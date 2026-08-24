#!/usr/bin/env python3
"""DỰNG LẠI SỔ ĐẾM TỪ SỐ JOB THẬT (24/8/2026).

Vì sao cần: sổ `render_stats` bị reset ngày 23/8 khi dọn kho làm lại. Sổ này là NGUỒN DUY NHẤT mà
`count_done()` dùng khi hệ đang chạy trên B2 (phiên khẩn) — vì B2 cố ý không chép lịch sử job. Sổ
trống thì phiên khẩn tưởng mọi kênh chưa làm gì và **làm dư video** so với chỉ tiêu.

Cách làm: đếm job THẬT ở B (`status=done` và có `drive_id`), gộp theo kênh + loại, rồi ghi đè:
  • `render_stats/{owner}`          -> {KÊNH: {l: số long, s: số short}}   (count_done đọc khi ở B2)
  • `render_stats/__pushed__{owner}` -> {total, ch_KÊNH}                    (dashboard đọc)

Đây là ghi ĐÈ có chủ ý (sổ đang sai), nên mặc định chạy thử; muốn ghi thật phải thêm --ghi.

    python rebuild_stats.py            # chỉ đếm và in ra
    python rebuild_stats.py --ghi      # ghi đè sổ
"""
from __future__ import annotations

import argparse
import os
import sys


def _client_b():
    from google.cloud import firestore
    from google.oauth2 import service_account
    pid = os.environ.get("FIREBASE_PROJECT_ID_B")
    sa = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_B")
    if not (pid and sa and os.path.exists(sa)):
        print("❌ thiếu FIREBASE_PROJECT_ID_B / GOOGLE_APPLICATION_CREDENTIALS_B")
        return None
    return firestore.Client(project=pid,
                            credentials=service_account.Credentials.from_service_account_file(sa))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ghi", action="store_true", help="ghi đè sổ thật (mặc định chỉ đếm)")
    ap.add_argument("--owner", default=os.environ.get("RENDER_OWNER", ""))
    a = ap.parse_args()
    if not a.owner:
        print("❌ thiếu RENDER_OWNER (UID chủ sở hữu)")
        return 1

    db = _client_b()
    if db is None:
        return 1

    theo_kenh: dict = {}
    tong = 0
    try:
        q = (db.collection("render_jobs")
               .where("owner", "==", a.owner).where("status", "==", "done"))
        for d in q.stream(timeout=60):
            x = d.to_dict() or {}
            if not (x.get("drive_id") or ""):
                continue                       # chỉ đếm video THẬT SỰ nằm trong kho
            ten = str(x.get("channel") or "").upper()
            if not ten:
                continue
            o = theo_kenh.setdefault(ten, {"l": 0, "s": 0})
            o["l" if x.get("type") == "long" else "s"] += 1
            tong += 1
    except Exception as e:
        print(f"❌ đọc render_jobs lỗi: {str(e)[:80]}")
        return 1

    print(f"📊 Đếm được {tong} video có file, trên {len(theo_kenh)} kênh")
    for ten, o in sorted(theo_kenh.items(), key=lambda kv: -(kv[1]['l'] + kv[1]['s']))[:8]:
        print(f"   {ten:<16} long {o['l']:>3} · short {o['s']:>3}")
    if not a.ghi:
        print("\n(chạy thử — thêm --ghi để ghi đè sổ thật)")
        return 0

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    db.collection("render_stats").document(a.owner).set({**theo_kenh, "at": now})
    db.collection("render_stats").document(f"__pushed__{a.owner}").set(
        {"total": tong, "at": now, **{f"ch_{k}": v["l"] + v["s"] for k, v in theo_kenh.items()}})
    print(f"\n✅ Đã dựng lại sổ: {tong} video · {len(theo_kenh)} kênh. Phiên khẩn (B2) giờ đếm đúng.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
