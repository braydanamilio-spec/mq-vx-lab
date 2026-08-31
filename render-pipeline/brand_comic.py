#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BRAND KIT BỘ HÀI — ảnh đại diện · ảnh bìa kênh · hình chìm (31/8/2026)

Anh: *"e nhớ design lại brandkit cho a nha"*. Bộ cũ dựng theo phong cách `KichHai` (nhân vật
đứng trên ảnh nền AI) nên không còn khớp thứ gì trên kênh nữa.

Ba cỡ ra ba tệp cho mỗi kênh, đặt ở `out/brand/`:
    <slug>_avatar.png     800×800    — YouTube, Facebook, Instagram dùng chung
    <slug>_banner.png     2560×1440  — ảnh bìa kênh YouTube (vùng an toàn 1546×423 ở giữa)
    <slug>_watermark.png  150×150    — hình chìm đè lên video, nền trong suốt

Khẩu hiệu mỗi kênh viết tay ở đây chứ không sinh máy: nó là câu duy nhất người xem đọc trên
trang kênh trước khi quyết định bấm đăng ký, nên không đáng để một khuôn mẫu quyết định hộ.
"""
import os
import io
import json
import argparse
import subprocess

from kich_hai import KENH, _ten_tep, _hai_bong, GOC, ENG
from kich_comic import MAU_CHINH, MAU_PHU, vai_va_giong

KHAU_HIEU = {
    "rent":     "THE RENT IS NEVER THE PROBLEM",
    "gym":      "NOBODY SKIPPED LEG DAY. NOBODY.",
    "airport":  "YOUR FLIGHT IS ON TIME. PROBABLY.",
    "car":      "IT WAS MAKING THAT NOISE BEFORE",
    "office":   "JUST CIRCLING BACK ON THAT",
    "diet":     "IT DOESN'T COUNT IF NOBODY SEES",
    "tech":     "HAVE YOU TRIED TURNING IT OFF?",
    "parent":   "FIVE MORE MINUTES. EVERY TIME.",
    "neighbor": "SOMEBODY HAS TO SAY SOMETHING",
    "dating":   "THE PROFILE WAS MOSTLY TRUE",
}

# Ai lên avatar, với vẻ mặt gì. Xếp mười ô 48px cạnh nhau thì chỉ còn TÓC · BIỂU CẢM · MÀU là
# đọc được — nên ba thứ ấy phải khác nhau rõ giữa các kênh, còn lại (áo, kính, râu) là chi tiết
# chỉ thấy khi bấm vào trang kênh.
AVATAR_VAI = {
    "rent":     ("A", "nghi_ngo"),   # người thuê đang nghi ngờ
    "gym":      ("B", "tu_tin"),     # huấn luyện viên tự tin
    "airport":  ("A", "buon"),       # khách bay rã rời
    "car":      ("B", "vui"),        # thợ máy già cười khà
    # OFFICE lấy nhân vật A: vai B của kênh này dùng chung kiểu vẽ `vu_tru_gia` với vai A của
    # NEIGHBOR WATCH, nên hai avatar ra hai ông tóc bạc gần như giống hệt. Mười kiểu vẽ chia cho
    # hai mươi vai thì trùng là chuyện phải xảy ra — chỗ nào trùng thì đổi ở AVATAR, không đổi
    # ở VAI (vai đã khớp với giọng và chiều cao, sửa ở đó là kéo theo cả dây).
    "office":   ("A", "nghi_ngo"),   # nhân viên trẻ nhướng mày
    "diet":     ("A", "so"),         # người ăn kiêng hoảng
    "tech":     ("B", "vui"),        # nhân viên hỗ trợ tươi quá mức
    "parent":   ("B", "bat_ngo"),    # đứa nhỏ trợn mắt
    "neighbor": ("A", "tuc"),        # ông hàng xóm cáu
    "dating":   ("A", "vui"),        # anh chồng cười toe
}

CO = {"avatar": ("ComicAvatar", "avatar"), "banner": ("ComicBanner", "banner"),
      "watermark": ("ComicWatermark", "watermark")}


def mot_kenh(k: dict, chi: str = "") -> int:
    slug = _ten_tep(k)
    thu = os.path.join(GOC, "out", "brand")
    os.makedirs(thu, exist_ok=True)

    kieuA, kieuB, ghiA, ghiB, _ga, _gb = vai_va_giong(k)
    tuyA, tuyB = _hai_bong(k)
    tuyA.update(ghiA); tuyB.update(ghiB)
    goc = {
        "kieuA": kieuA, "kieuB": kieuB, "kieuTuyA": tuyA, "kieuTuyB": tuyB,
        "tieuDe": k["ten"], "handle": k.get("handle", ""),
        "khau": KHAU_HIEU.get(k["de"], "NEW EPISODE EVERY DAY"),
        "mau": MAU_CHINH.get(k["de"], "#E4572E"), "mauPhu": MAU_PHU.get(k["de"], "#1F7AE0"),
    }
    # Khuôn dựng riêng cho mỗi kênh — anh: *"tránh họ nhìn vào biết cùng 1 người làm"*.
    # Lấy theo THỨ TỰ kênh chứ không theo băm: băm có thể cho hai kênh cạnh nhau cùng số, mà
    # hai kênh cạnh nhau trong danh sách lại chính là hai kênh hay bị đem ra so nhất.
    goc["boCuc"] = [x["de"] for x in KENH].index(k["de"])
    _ai, _cx = AVATAR_VAI.get(k["de"], ("A", "vui"))
    goc["dungB"] = (_ai == "B")
    goc["camXuc"] = _cx

    n = 0
    for ten, (comp, kind) in CO.items():
        if chi and chi != ten:
            continue
        dest = os.path.join(thu, f"{slug}_{ten}.png")
        pj = dest + ".props.json"
        io.open(pj, "w", encoding="utf-8").write(json.dumps({**goc, "kind": kind}, ensure_ascii=False))
        r = subprocess.run(["npx", "remotion", "still", "src/index.ts", comp, dest,
                            f"--props={pj}", "--gl=swiftshader", "--log=error"],
                           cwd=ENG, capture_output=True, text=True, timeout=900)
        try:
            os.remove(pj)
        except OSError:
            pass
        if r.returncode or not os.path.exists(dest):
            print(f"   ❌ {ten}: {(r.stderr or r.stdout or '')[-140:]}")
            continue
        n += 1
    print(f"   ✅ {k['ten']:19s} {n}/{len(CO) if not chi else 1} ảnh")
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--chi", default="", choices=["", "avatar", "banner", "watermark"])
    a = ap.parse_args()
    chon = KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [x for x in KENH if x["ten"].replace(" ", "").upper() in vt]
    tong = sum(mot_kenh(k, a.chi) for k in chon)
    print(f"\n{'✅' if tong else '⚠️'} {tong} ảnh brand cho {len(chon)} kênh → out/brand/")
    return 0 if tong else 1


if __name__ == "__main__":
    raise SystemExit(main())
