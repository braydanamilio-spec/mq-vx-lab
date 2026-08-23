#!/usr/bin/env python3
"""DỌN BẢN GHI KHO TRÙNG TÊN (23/8/2026).

Triệu chứng: kho ADISONDURHAM lúc nào cũng báo `invalid_grant: Token has been expired or revoked`
dù bấm Kết nối lại rất nhiều lần. Nguyên nhân: project A có **hai doc** `connections` cho cùng một
kho (khác doc-id vì khác kiểu đặt tên qua các đời code), mỗi doc trỏ một folder khác nhau. Kết nối
lại chỉ ghi đè doc MỚI; doc CŨ nằm lại mãi với token đã bị Google thu hồi, và mọi vòng quét đều
vấp phải nó trước.

Cách làm — KHÔNG cần đọc project A (đang cạn quota đọc):
  1. Lấy danh sách kho từ bản gương `connections_mirror/__snap__` ở B2 (quota còn nguyên).
     Mỗi dòng có sẵn `id` = doc-id gốc bên A.
  2. Kho nào có ≥2 dòng cùng tên -> thử làm mới token từng dòng bằng Google OAuth (không đụng
     Firestore) để biết dòng nào SỐNG, dòng nào CHẾT.
  3. Xoá doc CHẾT ở A (lệnh ghi — A chỉ cạn ĐỌC nên xoá được) và xoá luôn dòng gương tương ứng.
     Chỉ xoá khi nhóm đó CÒN ÍT NHẤT MỘT dòng sống — không bao giờ xoá dòng cuối cùng.

    python fix_dup_connections.py --dry-run
    python fix_dup_connections.py
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.parse
import urllib.request


def _clients():
    from google.cloud import firestore
    from google.oauth2 import service_account
    out = {}
    for tag, pid_env, sa_env in (("A", "FIREBASE_PROJECT_ID", "GOOGLE_APPLICATION_CREDENTIALS"),
                                 ("B", "FIREBASE_PROJECT_ID_B", "GOOGLE_APPLICATION_CREDENTIALS_B"),
                                 ("B2", "FIREBASE_PROJECT_ID_B2", "GOOGLE_APPLICATION_CREDENTIALS_B")):
        pid, sa = os.environ.get(pid_env), os.environ.get(sa_env)
        if not (pid and sa and os.path.exists(sa)):
            continue
        try:
            out[tag] = firestore.Client(
                project=pid, credentials=service_account.Credentials.from_service_account_file(sa))
        except Exception as e:
            print(f"⚠️ không mở được {tag}: {str(e)[:60]}")
    return out


def _snapshot(cls) -> list[dict]:
    """Đọc danh sách kho từ gương — thử B2 trước (quota còn), rồi tới B."""
    for tag in ("B2", "B"):
        cl = cls.get(tag)
        if not cl:
            continue
        try:
            d = cl.collection("connections_mirror").document("__snap__").get()
            if d.exists:
                accs = (d.to_dict() or {}).get("accs") or []
                if accs:
                    print(f"📖 đọc gương ở {tag}: {len(accs)} dòng kho")
                    return accs
        except Exception as e:
            print(f"   ⚠️ gương {tag} hụt: {str(e)[:60]}")
    return []


def _token_alive(row: dict) -> bool:
    """Thử làm mới access token — chỉ gọi Google, không đụng Firestore."""
    try:
        body = urllib.parse.urlencode({
            "client_id": row.get("client_id", ""), "client_secret": row.get("client_secret", ""),
            "refresh_token": row.get("refresh_token", ""), "grant_type": "refresh_token"}).encode()
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body,
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status == 200
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    cls = _clients()
    rows = _snapshot(cls)
    if not rows:
        print("❌ không đọc được gương ở cả B2 lẫn B — dừng, không đoán mò.")
        return 1

    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(str(r.get("channel") or r.get("id") or "?").upper(), []).append(r)
    dups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"🔎 {len(rows)} dòng kho · {len(dups)} kho bị TRÙNG TÊN: {', '.join(dups) or '(không có)'}")
    if not dups:
        return 0

    killed = 0
    for name, rs in dups.items():
        alive, dead = [], []
        for r in rs:
            (alive if _token_alive(r) else dead).append(r)
        print(f"\n📦 {name}: {len(alive)} dòng SỐNG · {len(dead)} dòng CHẾT")
        for r in rs:
            print(f"   - id={r.get('id')} root={str(r.get('root'))[:12]}… "
                  f"{'SỐNG' if r in alive else 'CHẾT'}")
        if not alive:
            print("   ⏭ không có dòng nào sống -> KHÔNG xoá gì (tránh mất kho). Bấm Kết nối lại kho này.")
            continue
        for r in dead:
            if a.dry_run:
                print(f"   (chạy thử) sẽ xoá doc {r.get('id')}")
                continue
            for tag in ("A", "B", "B2"):
                cl = cls.get(tag)
                if not cl:
                    continue
                coll = "connections" if tag == "A" else "connections_mirror"
                try:
                    cl.collection(coll).document(str(r.get("id"))).delete()
                    print(f"   🗑 xoá {tag}/{coll}/{r.get('id')}")
                except Exception as e:
                    print(f"   ⚠️ xoá {tag} hụt: {str(e)[:60]}")
            killed += 1

    print(f"\n✅ Đã dọn {killed} bản ghi kho chết. Phiên render sau sẽ dựng lại gương sạch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
