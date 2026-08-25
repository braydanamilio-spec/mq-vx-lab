#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐĂNG KÝ 50 KÊNH THẾ HỆ 2 vào render_channels (26/8/2026).

MẶC ĐỊNH LÀ DRY-RUN. Phải `--that` mới ghi thật — đăng ký kênh là thứ 18 lane sẽ đọc và bắt đầu
render ngay phiên sau, nên không để lỡ tay.

Kênh mới vào ở trạng thái TẮT (`paused: True`) trừ khi `--bat`: bật 50 kênh trong khi 55 kênh cũ
còn đang chạy là 105 kênh chen nhau trên 18 lane, không kênh nào ra hồn.

    python seed_the_he_2.py                 # xem sẽ tạo gì
    python seed_the_he_2.py --that          # tạo, để TẮT
    python seed_the_he_2.py --that --bat    # tạo và bật
"""
from __future__ import annotations

import io
import json
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(GOC, "kenh_the_he_2.json")
TARGET = ["short_target", "long_target", "n_shorts", "make_long", "tier", "cap_gb"]


def _db():
    from google.cloud import firestore
    from google.oauth2 import service_account
    key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_B") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    prj = os.environ.get("FIREBASE_PROJECT_ID_B") or os.environ.get("FIREBASE_PROJECT_ID")
    if not key or not os.path.exists(key):
        sys.exit("❌ Chưa có GOOGLE_APPLICATION_CREDENTIALS_B — chạy trên máy có khoá dịch vụ.")
    return firestore.Client(project=prj, credentials=service_account.Credentials.from_service_account_file(key))


def main() -> int:
    that = "--that" in sys.argv
    bat = "--bat" in sys.argv
    ks = json.load(io.open(DS, encoding="utf-8"))
    if not that:
        print(f"🔍 DRY-RUN — sẽ đăng ký {len(ks)} kênh, trạng thái "
              f"{'BẬT' if bat else 'TẮT (chờ bật tay)'}\n")
        for k in ks:
            b = k.get("brand") or {}
            print(f"  ➕ {k['ten']:18} {k['handle']:20} {k['dinh_dang']:9} "
                  f"{(b.get('palette') or {}).get('primary', '-'):8} {k['niche'][:22]}")
        print(f"\n(chưa ghi gì cả. Thêm --that để ghi thật)")
        return 0
    db = _db()
    hien = list(db.collection("render_channels").stream())
    if not hien:
        sys.exit("❌ render_channels rỗng — không lấy được mẫu cấu hình.")
    mau = [d.to_dict() or {} for d in hien]
    owner = os.environ.get("OWNER_UID") or next((t.get("owner") for t in mau if t.get("owner")), "")
    if not owner:
        sys.exit("❌ Không có owner. Đặt OWNER_UID.")
    co = {(t.get("name") or "") for t in mau}
    dich = {k: mau[0].get(k) for k in TARGET if mau[0].get(k) is not None}
    tao = bo = 0
    for k in ks:
        ten = k["ten"].replace(" ", "")
        if ten in co:
            print(f"  ⏭  {ten:18} đã có -> bỏ qua"); bo += 1; continue
        b = k.get("brand") or {}
        pal = b.get("palette") or {}
        doc = {"owner": owner, "name": ten, "the_he": 2, "paused": not bat,
               "type": "short", "make_long": False, "long_target": 0, "n_shorts": 3,
               **dich,
               "format": k["dinh_dang"], "accent": pal.get("primary", "#22D3EE"),
               "accent2": pal.get("accent", "#F5B301"),
               "handle": k["handle"], "niche": k["goc_nhin"], "brand": b}
        db.collection("render_channels").document(f"{owner}__{ten}").set(doc, merge=True)
        print(f"  ➕ {ten:18} [{k['dinh_dang']}] {'BẬT' if bat else 'tắt'}")
        tao += 1
    print(f"\n✅ tạo {tao} kênh, bỏ qua {bo}. Trạng thái: {'ĐANG CHẠY' if bat else 'TẮT — bật ở dashboard'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
