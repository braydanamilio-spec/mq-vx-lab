#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ĐẨY BRAND KIT LÊN DASHBOARD (31/8/2026)

Anh: *"brandkit e nhớ đẩy lên đồng bộ web e nha — mm0-auto-publisher.web.app"*.

Dashboard đọc ảnh brand theo MỘT quy ước tên cố định, và bảng `_ART_V4` trong `index.html` là
thứ nói cho nó biết kênh nào có những ảnh gì:

    /brand/<TÊN_KÊNH_VIẾT_HOA>_<loại>_<kích thước>.png

Tám loại, và chúng KHÔNG phải tám biến thể của một ảnh — mỗi nền tảng cắt một kiểu:

    avatar_800          YouTube          hiển thị 98px
    cover_2560x1440     YouTube          vùng an toàn 1546×423 (mobile cắt TRÊN DƯỚI)
    watermark_150       YouTube          đè lên video, nền trong suốt
    fb_avatar_500       Facebook page    hiển thị 170px
    fb_cover_1640x624   Facebook page    mobile cắt HAI BÊN — ngược với YouTube
    ig_avatar_640       Instagram        hiển thị 110px
    ig_post_1080        Instagram        bài đăng vuông
    x_header_1500x500   X / Twitter      ảnh đại diện đè lên góc trái-dưới

Tệp này chỉ làm ba việc, và không việc nào được phép đoán: đổi tên theo quy ước · chép vào
`dashboard/brand/` · thêm mười kênh hài vào bảng `_ART_V4` mà KHÔNG đụng sáu mươi kênh đã có.
"""
import os
import io
import re
import json
import shutil
import argparse

from kich_hai import KENH, _ten_tep, GOC

WEB = os.path.join(GOC, "..", "MM0-AutoPublisher", "dashboard")
BRAND_WEB = os.path.join(WEB, "brand")
BRAND_MAY = os.path.join(GOC, "out", "brand")

# tên tệp của mình  ->  tên dashboard đòi
DOI_TEN = {
    "avatar":     "avatar_800",
    "banner":     "cover_2560x1440",
    "watermark":  "watermark_150",
    "cover_fb":   "fb_cover_1640x624",
    "x_header":   "x_header_1500x500",
    "fb_avatar_500": "fb_avatar_500",
    "ig_avatar_640": "ig_avatar_640",
    "ig_post_1080":  "ig_post_1080",
}
# `avatar_lon` là ảnh gốc để thu nhỏ ra ba cỡ kia, không tự lên web.


def _ten_web(k: dict) -> str:
    """TECHSUPPORT — dashboard dùng tên kênh viết hoa, bỏ khoảng trắng."""
    return k["ten"].replace(" ", "").upper()


def day_anh(chi_kenh=None) -> dict:
    os.makedirs(BRAND_WEB, exist_ok=True)
    ra = {}
    for k in KENH:
        if chi_kenh and k["ten"] not in chi_kenh:
            continue
        slug, ten = _ten_tep(k), _ten_web(k)
        co = {}
        for cua_minh, cua_web in DOI_TEN.items():
            ng = os.path.join(BRAND_MAY, f"{slug}_{cua_minh}.png")
            if not os.path.exists(ng):
                continue
            dich = os.path.join(BRAND_WEB, f"{ten}_{cua_web}.png")
            shutil.copy2(ng, dich)
            co[cua_web] = f"/brand/{ten}_{cua_web}.png?v=6"
        if co:
            ra[ten] = co
            print(f"   ✅ {k['ten']:19s} {len(co)}/8 ảnh")
        else:
            print(f"   ⏭ {k['ten']:19s} chưa dựng brand — chạy brand_comic.py trước")
    return ra


def cap_nhat_bang(moi: dict) -> bool:
    """Thêm các kênh mới vào `_ART_V4`, giữ nguyên phần đã có."""
    p = os.path.join(WEB, "index.html")
    s = io.open(p, encoding="utf-8").read()
    m = re.search(r"const _ART_V4 = (\{.*?\});", s, re.S)
    if not m:
        print("   ❌ không tìm thấy bảng _ART_V4 trong index.html")
        return False
    try:
        cu = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(f"   ❌ bảng _ART_V4 không đọc được: {e}")
        return False

    # Khoá dashboard dùng là tên rút gọn (`avatar`, `cover`, `fb_cover`…), không phải tên tệp.
    # Đọc một mục có sẵn để lấy đúng bộ khoá thay vì đoán — đoán sai thì ảnh không hiện mà
    # cũng chẳng báo lỗi gì.
    mau = next(iter(cu.values())) if cu else {}
    ANH_XA = {}
    for khoa, duong in mau.items():
        for _, cua_web in DOI_TEN.items():
            if f"_{cua_web}." in duong:
                ANH_XA[cua_web] = khoa
    them = 0
    for ten, co in moi.items():
        muc = {ANH_XA[k2]: v for k2, v in co.items() if k2 in ANH_XA}
        if not muc:
            continue
        if ten in cu and cu[ten] == muc:
            continue
        cu[ten] = muc
        them += 1
    if not them:
        print("   (bảng đã đúng, không cần đổi)")
        return True

    s2 = s[:m.start(1)] + json.dumps(cu, ensure_ascii=False) + s[m.end(1):]
    io.open(p, "w", encoding="utf-8").write(s2)
    print(f"   ✅ _ART_V4: thêm/cập nhật {them} kênh · tổng {len(cu)} kênh")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    a = ap.parse_args()
    loc = None
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        loc = {x["ten"] for x in KENH if x["ten"].replace(" ", "").upper() in vt}

    print("→ chép ảnh vào dashboard/brand/ …")
    moi = day_anh(loc)
    if not moi:
        print("⚠️ không có ảnh nào để đẩy")
        return 1
    print("\n→ cập nhật bảng _ART_V4 …")
    if not cap_nhat_bang(moi):
        return 2
    print("\n✅ xong. Bước cuối (cần anh chạy, vì nó đẩy lên mạng thật):")
    print("   cd MM0-AutoPublisher && firebase deploy --only hosting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
