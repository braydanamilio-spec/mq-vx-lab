#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LẤY KEY VỀ MÁY ĐỂ CHẠY TAY — dùng chính phiên đăng nhập Firebase sẵn có (29/8/2026).

VÌ SAO CẦN
----------
Dạng `cinematic` (10/50 kênh) bắt buộc phải có key vẽ ảnh. Trên CI thì key tới từ hồ Firestore
qua service account; trên máy thì không có creds nào, nên `dung_props_phim` bỏ lượt và KHÔNG cách
nào soi khung của 10 kênh đó bằng mắt. Mà soi bằng mắt là thứ DUY NHẤT bắt được lỗi bố cục — bộ
đo pixel đã chứng minh cho ra cùng một dải số với video tốt lẫn video hỏng. Không có key thì 10
kênh phải sửa mù: vá xong không biết đúng hay sai.

Máy này đã đăng nhập `firebase` bằng tài khoản chủ dự án, tức quyền đọc vốn đã có sẵn — chỉ thiếu
một đường ống. Script này là đường ống đó.

KEY KHÔNG BAO GIỜ ĐƯỢC IN RA
----------------------------
Chỉ ghi thẳng vào `.keys.local` (đã nằm trong .gitignore) và báo lại SỐ LƯỢNG cùng vài ký tự đầu.
Một khoá API in ra màn hình là một khoá đã rò: nó nằm lại trong log, trong lịch sử phiên, trong
bản chép màn hình. Đường ống này không có lý do gì phải nhìn thấy giá trị khoá.

    python lay_key_cuc_bo.py                 # đọc project mặc định
    python lay_key_cuc_bo.py --project mm0-shard-b
"""
from __future__ import annotations

import io
import json
import os
import sys
import urllib.parse
import urllib.request

GOC = os.path.dirname(os.path.abspath(__file__))
RA = os.path.join(GOC, ".keys.local")

# Khoá OAuth của chính công cụ `firebase` (mã nguồn mở, công khai trong repo firebase-tools).
# Đây KHÔNG phải bí mật của anh — nó chỉ để đổi refresh token của phiên đăng nhập sẵn có lấy
# access token. Không có refresh token ấy thì hai giá trị này chẳng mở được gì.
FB_CLIENT_ID = "563584335869-fgrhgmd47bqnekij5i8b5pr03ho849e6.apps.googleusercontent.com"
FB_CLIENT_SECRET = "j9iVZfS8kkCEFUPaAeJV0sAi"
CAU_HINH = os.path.expanduser("~/.config/configstore/firebase-tools.json")


def _refresh_token() -> str:
    if not os.path.exists(CAU_HINH):
        raise SystemExit("❌ chưa đăng nhập `firebase` trên máy này — chạy `firebase login` trước")
    d = json.load(io.open(CAU_HINH, encoding="utf-8"))
    t = ((d.get("tokens") or {}).get("refresh_token")
         or ((d.get("user") or {}).get("tokens") or {}).get("refresh_token"))
    if not t:
        raise SystemExit("❌ không thấy refresh token trong cấu hình firebase-tools")
    return t


def _access_token() -> str:
    than = urllib.parse.urlencode({
        "client_id": FB_CLIENT_ID, "client_secret": FB_CLIENT_SECRET,
        "refresh_token": _refresh_token(), "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=than,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())["access_token"]


def _doc(proj: str, col: str, tok: str) -> list:
    """Đọc TRỌN collection — theo `nextPageToken` cho tới hết.

    ── VÌ SAO  (đo 6/9/2026) ───────────────────────────────────────────────────────────────
    Bản cũ gọi `?pageSize=300` rồi lấy `documents` và dừng. Dashboard đếm **363 khoá**, nên
    mọi bản ghi sau cái thứ 300 **chưa bao giờ về máy** — và không có lỗi nào báo: HTTP 200,
    JSON hợp lệ, danh sách đầy đủ về mặt cú pháp.
    Triệu chứng nhìn từ ngoài là "hồ khoá ít hơn dashboard", và em đã đi đổ cho ba thứ khác
    (Cloudflare không cho xem lại token · khoá nằm ở shard khác · khoá nằm trong localStorage)
    trước khi nhìn vào chính lời gọi.

    Đúng §15.1: **phép CẮT đặt trước phép LỌC**. Và đúng §15.2: một danh sách trả về không kèm
    "còn nữa hay hết rồi" thì nó có hai nghĩa ngược nhau, mà mã chỉ đọc một nghĩa.
    """
    ra, tok_trang = [], ""
    while True:
        u = (f"https://firestore.googleapis.com/v1/projects/{proj}/databases/(default)/documents/"
             f"{col}?pageSize=300" + (f"&pageToken={tok_trang}" if tok_trang else ""))
        req = urllib.request.Request(u, headers={"Authorization": f"Bearer {tok}"})
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode()) or {}
        ra += d.get("documents") or []
        tok_trang = d.get("nextPageToken") or ""
        if not tok_trang:
            return ra


def _gia_tri(f: dict):
    """Bóc một trường Firestore REST về giá trị Python (chỉ các kiểu bảng key dùng)."""
    for k in ("stringValue", "integerValue", "doubleValue", "booleanValue"):
        if k in f:
            return f[k]
    return None


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=os.environ.get("FIREBASE_PROJECT_ID") or "mm0-auto-publisher")
    ap.add_argument("--collection", default="gemini_keys")
    a = ap.parse_args()

    tok = _access_token()
    try:
        docs = _doc(a.project, a.collection, tok)
    except Exception as e:
        print(f"❌ không đọc được `{a.collection}` ở project {a.project}: {str(e)[:120]}")
        print("   Thử project khác: --project mm0-shard-b   (SHARD_KEYS=1 thì bảng key nằm ở B)")
        return 3

    keys, nghi = [], 0
    for d in docs:
        f = d.get("fields") or {}
        k = _gia_tri(f.get("key") or {}) or _gia_tri(f.get("api_key") or {})
        if not k or len(str(k)) < 20:
            continue
        # Bỏ key đang bị phạt/tắt: lấy về cũng không dùng được, chỉ tổ làm lượt vẽ hụt.
        if (not os.environ.get("LAY_TAT_CA")) and \
           str(_gia_tri(f.get("status") or {}) or "").lower() in ("dead", "disabled", "off"):
            nghi += 1
            continue
        keys.append(str(k))

    if not keys:
        print(f"⚠️ đọc được {len(docs)} bản ghi nhưng không rút ra key nào dùng được")
        return 4

    io.open(RA, "w", encoding="utf-8").write(
        "# Hồ key CHẠY TAY trên máy — .gitignore đã chặn tệp này.\n"
        "# Sinh bởi lay_key_cuc_bo.py; xoá đi lúc nào cũng được.\n"
        + "\n".join(keys) + "\n")
    os.chmod(RA, 0o600)

    # CHỈ báo số lượng và loại. Không in giá trị khoá — xem ghi chú đầu tệp.
    from collections import Counter
    loai = Counter("Cloudflare" if k.startswith("cf:") else
                   "Gemini" if k.startswith("AIza") else "khác" for k in keys)
    print(f"✅ {len(keys)} key -> {RA}  (quyền 600)"
          + (f" · bỏ {nghi} key đang tắt" if nghi else ""))
    for t, n in loai.most_common():
        print(f"     {n:>4} × {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
