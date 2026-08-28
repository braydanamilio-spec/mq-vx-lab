#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KLING TỰ ĐỘNG A-Z — một lệnh: nghĩ ý tưởng -> bảng chụp -> sinh clip -> ghép -> đẩy kho -> đăng.

CÔNG TẮC DUY NHẤT (28/8/2026)
-----------------------------
    CÓ  KLING_ACCESS_KEY/SECRET  ->  chạy hết, người không phải làm gì
    CHƯA có                      ->  làm tới bảng chụp rồi DỪNG, in ra việc anh cần làm tay
Cùng một lệnh, cùng một đường. Ngày anh mua key thì chỉ thêm hai biến môi trường — không sửa
một dòng nào, không dựng lại gì.

VÌ SAO VIẾT THÀNH MỘT LỆNH THAY VÌ NHIỀU BƯỚC RỜI
--------------------------------------------------
Nhiều bước rời thì mỗi lần chạy phải nhớ thứ tự, và quên một bước là hỏng im lặng (đã thấy đúng
kiểu đó tối nay: video ghép xong nhưng không ai đẩy kho). Một lệnh thì thứ tự nằm trong mã, và
mỗi bước hỏng đều có tiếng.

TIỀN
----
`kling_api` đã có phanh theo NGÀY. Lệnh này thêm phanh theo LƯỢT CHẠY (`--so`), vì hai thứ chặn
hai chuyện khác nhau: trần ngày chặn tổng chi, trần lượt chặn một lệnh chạy hoang.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
KHO = os.path.join(GOC, "out", "kling")

# Mồi ý tưởng — KHÔNG phải kịch bản, chỉ là hạt để model nở ra gag. Cố ý chọn bối cảnh Mỹ đời
# thường vì đó là nơi Kling vẽ chắc tay nhất, và cũng là nơi khán giả Mỹ nhận ra ngay.
MOI = [
    "a dog running the night shift at a convenience store",
    "a raccoon doing a full grocery run at 3am",
    "a cat operating a suburban drive-thru window",
    "a goose refusing to leave a gym parking lot",
    "an office chair that follows people down the hallway",
    "a lawnmower that mows only at the neighbor's house",
    "a vending machine that gives back more than you paid",
    "a pigeon supervising a construction site",
    "a laundromat dryer that returns clothes from another decade",
    "a squirrel running a valet stand outside a diner",
    "a robot vacuum that keeps escaping the house",
    "a deer casually using an ATM at dawn",
]


def _slug(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(t or "").lower()).strip("-")[:48] or "kling"


def _da_lam() -> list:
    """Ý tưởng đã dùng — đọc từ chính các thư mục việc, không cần sổ riêng.

    Sổ riêng là thứ phải giữ đồng bộ với thực tế, và mọi sổ như thế đều lệch sau vài tuần. Thư mục
    việc CHÍNH LÀ thực tế."""
    if not os.path.isdir(KHO):
        return []
    ra = []
    for x in os.listdir(KHO):
        js = os.path.join(KHO, x, "shots.json")
        if os.path.exists(js):
            try:
                ra.append(json.load(io.open(js, encoding="utf-8")).get("title") or x)
            except Exception:
                ra.append(x)
    return ra


def mot_video(y_tuong: str, kenh: str, tranh: list) -> str:
    """Làm TRỌN một video từ một ý tưởng. Trả trạng thái: 'day' | 'cho_clip' | 'hong'."""
    import kling_studio as KS
    import kling_lo as KL

    # 1) BẢNG CHỤP — luôn làm được, không cần key Kling.
    try:
        d = KS.sinh(y_tuong, avoid=tranh)
    except Exception as e:
        print(f"   ❌ bảng chụp hỏng: {str(e)[:110]}")
        return "hong"
    slug = _slug(d.get("title") or y_tuong)
    tm = os.path.join(KHO, slug)
    os.makedirs(os.path.join(tm, "clips"), exist_ok=True)
    io.open(os.path.join(tm, "shots.json"), "w", encoding="utf-8").write(
        json.dumps(d, ensure_ascii=False, indent=2))
    io.open(os.path.join(tm, "BANG_CHUP.md"), "w", encoding="utf-8").write(KS.bang_chup(d))
    try:
        import firestore_bridge as FB
        FB.save_kling_shots(os.environ.get("OWNER_UID") or "THU", slug, d)
    except Exception:
        pass                    # lên dashboard là tiện ích, không phải điều kiện để chạy tiếp

    # 2) SINH CLIP — chỗ duy nhất cần key. Không có key thì dừng ở đây, có tiếng.
    import kling_api as KA
    if not KA.co_api():
        print(f"   ⏸️ {slug}: xong bảng chụp ({len(d.get('scenes') or [])} cảnh). "
              f"CHƯA có KLING_ACCESS_KEY -> anh dán prompt vào Kling rồi thả clip vào:")
        print(f"      {os.path.join(tm, 'clips')}/scene-01.mp4 …")
        return "cho_clip"
    ra, con = KA.sinh_clip(tm)
    print(f"   🎬 {slug}: sinh {ra} clip · còn thiếu {con}")
    if con:
        return "cho_clip"

    # 3) GHÉP + 4) ĐẨY KHO — dùng đúng đường ray của 50 kênh kia.
    v = KL.ghep(tm)
    if not v:
        return "hong"
    if not kenh:
        print(f"   ✅ {slug}: ghép xong (chưa đẩy kho — thiếu --kenh)")
        return "cho_clip"
    if KL.day_kho(tm, kenh, v):
        io.open(os.path.join(tm, ".da_day"), "w").write("1")
        print(f"   📤 {slug}: đã vào kho — khâu đăng tự lấy như 50 kênh kia")
        return "day"
    print(f"   ⚠️ {slug}: ghép xong nhưng đẩy kho hụt — giữ file, chạy lại sau")
    return "hong"


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Kling A-Z: ý tưởng -> video -> kho -> đăng")
    ap.add_argument("--so", type=int, default=1, help="số video mỗi lượt chạy (phanh chống chạy hoang)")
    ap.add_argument("--kenh", default=os.environ.get("KLING_KENH") or "",
                    help="mã kênh trong channels.yaml để đẩy kho + đăng")
    ap.add_argument("--y-tuong", default="", help="ép một ý tưởng cụ thể thay vì bốc từ kho mồi")
    a = ap.parse_args()

    import kling_api as KA
    print(f"🎞️ KLING A-Z · {'CÓ' if KA.co_api() else 'CHƯA CÓ'} key API · "
          f"{'chạy hết' if KA.co_api() else 'dừng ở bảng chụp'}")

    # DỌN VIỆC CŨ TRƯỚC KHI NHẬN VIỆC MỚI. Anh có thể đã thả clip vào từ hôm qua — đẩy nốt cái
    # đó đáng giá hơn hẳn việc đẻ thêm bảng chụp mới rồi để cả hai treo.
    import kling_lo as KL
    if os.path.isdir(KHO):
        for x in sorted(os.listdir(KHO)):
            tm = os.path.join(KHO, x)
            if not os.path.isdir(tm) or os.path.exists(os.path.join(tm, ".da_day")):
                continue
            du, _, _ = KL.kiem_du(tm)
            if du:
                v = KL.ghep(tm)
                if v and a.kenh and KL.day_kho(tm, a.kenh, v):
                    io.open(os.path.join(tm, ".da_day"), "w").write("1")
                    print(f"   📤 {x}: việc cũ đã đủ clip -> đã vào kho")

    tranh = _da_lam()
    moi = [a.y_tuong] if a.y_tuong else [m for m in MOI if _slug(m) not in
                                         {_slug(t) for t in tranh}] or MOI
    dem = {"day": 0, "cho_clip": 0, "hong": 0}
    for i in range(max(1, a.so)):
        if i >= len(moi):
            break
        yt = moi[i]
        print(f"\n── [{i + 1}/{a.so}] {yt}")
        dem[mot_video(yt, a.kenh, tranh)] += 1
        tranh = _da_lam()
    print(f"\n📊 {dem['day']} đã vào kho · {dem['cho_clip']} chờ clip · {dem['hong']} hỏng")
    return 0


if __name__ == "__main__":
    sys.exit(main())
