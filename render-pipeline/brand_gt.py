#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BRAND KIT — 10 kênh giải thích. Đủ cỡ cho YouTube · Facebook · Instagram.  (1/9/2026)

Anh: *"brandkit — có đủ profile, banner đủ size cho youtube, fb, insta."*

── CỠ ẢNH, VÀ VÌ SAO ĐÚNG NHỮNG CỠ NÀY ─────────────────────────────────────────────────────
    <ma>_avatar.png       800×800    YouTube ảnh đại diện kênh
    <ma>_avatar_lon.png  1080×1080   Facebook Trang + Instagram (hai nơi này nén xuống nhưng
                                     nhận bản lớn, đưa bản 800 lên là mờ ở màn hình Retina)
    <ma>_banner.png      2560×1440   YouTube ảnh bìa kênh
    <ma>_cover.png       1640×856    Facebook ảnh bìa Trang
    <ma>_post.png        1080×1080   Instagram bài ghim đầu trang
    <ma>_fb_500.png       500×500    bản thu nhỏ, một số chỗ của FB đòi ≤512
    <ma>_ig_640.png       640×640    bản thu nhỏ cho Instagram

VÙNG AN TOÀN là thứ quyết định, không phải kích thước. Banner YouTube 2560×1440 nhưng trên
điện thoại chỉ hiện **1546×423 ở giữa** — mọi thứ ngoài vùng ấy bị cắt sạch. Ảnh bìa Facebook
thì bị chính ảnh đại diện của Trang đè lên góc dưới trái, nên chữ phải dồn sang phải.
Làm banner đẹp mà không tôn trọng hai điều đó thì trên điện thoại chỉ còn một mảng màu.

── VẼ BẰNG CODE, KHÔNG GỌI API ─────────────────────────────────────────────────────────────
Avatar và banner mang TÊN KÊNH. Đo hôm nay: FLUX viết chuỗi ngắn đúng 5/6 lần. Với một khung
phim thoáng qua thì chấp nhận được; với ảnh đứng vĩnh viễn trên trang kênh thì một lần sai là
hỏng thương hiệu, và không ai phát hiện cho tới khi có người nhắn hỏi.
"""
import argparse
import io
import json
import os
import subprocess

GOC = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(os.path.dirname(GOC), "engine-remotion")
RA = os.path.join(GOC, "brand_gt")

from giai_thich import KENH, MAU_KENH                        # noqa: E402

# Biểu tượng nhận diện + từ ngắn cho avatar. Ở 48px chỉ còn đọc được hình khối và 1-2 từ, nên
# từ ngắn phải là từ MANG NGHĨA NHẤT của tên kênh, không phải từ đầu tiên.
# ── MÔ TẢ THƯƠNG HIỆU: khẩu hiệu tiếng Anh + thẻ · dùng cho dashboard, bìa kênh và bài đăng ──
# Đặt ở ĐÂY chứ không ở dashboard, vì `brand_gt.py` đã là nơi giữ nhận diện (biểu tượng + từ
# avatar trong `NHAN`). Gõ tay lần nữa vào `index.html` là tạo nguồn sự thật thứ tư cho danh
# sách kênh — và bốn nguồn thì hôm nay đã lệch nhau hai chiều rồi.
#   ma -> (khẩu hiệu hiện dưới tên kênh, chuỗi thẻ)
MO_TA = {
    "howlong":   ("Every journey, in real time",        "#howlong #timescale #distance #explained"),
    "howbig":    ("Scale you can actually picture",     "#howbig #scale #sizecomparison #explained"),
    "realcost":  ("The price after the price",          "#realcost #truecost #money #explained"),
    "howmuch":   ("Big numbers, made human",            "#howmuch #billion #bignumbers #perspective"),
    "whatif":    ("One change, all the math",           "#whatif #hypothetical #thoughtexperiment"),
    "survive":   ("The numbers say no",                 "#survive #survival #extremes #explained"),
    "dayinlife": ("Twenty-four hours, counted",         "#dayinthelife #dailynumbers #routine"),
    "wheregoes": ("Follow it all the way down",         "#wheredoesitgo #supplychain #hiddensystems"),
    "therules":  ("The fine print, read out loud",      "#finePrint #therules #knowyourrights"),
    "speedof":   ("Everything, ranked by speed",        "#speedof #howfast #physics #explained"),
    "odds":      ("What the chances really are",        "#odds #probability #chances #explained"),
    "hiddenfee": ("Where your money actually goes",     "#hiddenfees #pricebreakdown #money"),
    "yearsof":   ("What you spend your life on",        "#yearsofyourlife #timespent #lifemath"),
    "howloud":   ("Decibels you can feel",              "#howloud #decibels #sound #explained"),
    "whatweighs":("Heavier than you think",             "#whatitweighs #howheavy #comparison"),
    "rightnow":  ("Happening while you watch",          "#rightnow #livenumbers #happeningnow"),
    "howhot":    ("The degrees that matter",            "#howhot #temperature #heat #explained"),
    "smallest":  ("Too small to imagine, measured",     "#smallest #tiny #microscopic #explained"),
}

NHAN = {
    # 18 biểu tượng KHÁC NHAU HOÀN TOÀN. Ở 48px — cỡ avatar thật trong danh sách đề xuất —
    # hình khối là thứ duy nhất còn phân biệt được; trùng hình là hai kênh trông như một.
    "howlong":    ("dong_ho",          "HOW LONG"),
    "howbig":     ("trai_dat",          "HOW BIG"),
    "realcost":   ("tien",          "REAL COST"),
    "howmuch":    ("hat",          "A BILLION"),
    "whatif":     ("nguoi",          "WHAT IF"),
    "survive":    ("cay",          "SURVIVE"),
    "dayinlife":  ("cua",          "A DAY"),
    "wheregoes":  ("hop",          "WHERE"),
    "therules":   ("khoa",          "THE RULES"),
    "speedof":    ("may_bay",          "HOW FAST"),
    "odds":       ("sao",          "THE ODDS"),
    "hiddenfee":  ("banh_rang",          "INSIDE"),
    "yearsof":    ("giot",          "YEARS"),
    "howloud":    ("song",          "HOW LOUD"),
    "whatweighs": ("nui",          "WEIGHS"),
    "rightnow":   ("mui_ten",          "RIGHT NOW"),
    "howhot":     ("nhiet",          "HOW HOT"),
    "smallest":   ("lua",          "SMALLEST"),
}


CO = [("GTAvatar", "avatar"), ("GTAvatarLon", "avatar_lon"), ("GTBanner", "banner"),
      ("GTCover", "cover"), ("GTPost", "post")]
THU_NHO = {"fb_500": ("avatar_lon", 500), "ig_640": ("avatar_lon", 640)}


def mot_kenh(k: dict) -> int:
    ma = k["ma"]
    mk = MAU_KENH.get(ma, {})
    bieu, ngan = NHAN.get(ma, ("nguoi", ma.upper()))
    props = {"ten": k["ten"], "ngan": ngan, "bieu": bieu,
             "mau": mk.get("mau", k["mau"]), "phu": mk.get("phu", k["phu"]),
             "nen": mk.get("nen", "#F3EEE4"), "chu": mk.get("chu", "#2C2722")}
    os.makedirs(RA, exist_ok=True)
    pj = os.path.join(RA, f"_{ma}.json")
    io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))

    n = 0
    for comp, ten in CO:
        out = os.path.join(RA, f"{ma}_{ten}.png")
        r = subprocess.run(["npx", "remotion", "still", "src/index.ts", comp, out,
                            f"--props={pj}", "--gl=swiftshader", "--log=error"],
                           cwd=ENG, capture_output=True, text=True, timeout=900)
        if r.returncode or not os.path.exists(out):
            loi = [d for d in (r.stderr or "").splitlines()
                   if any(t in d for t in ("Error", "error:", "Cannot", "Expected"))]
            print(f"   ❌ {ten}: {(loi[:1] or ['?'])[0][:120]}")
            continue
        n += 1

    # Bản thu nhỏ: một số chỗ của FB/IG từ chối tệp lớn. Thu bằng PIL cho sắc, không để nền
    # tảng tự thu — thu ở phía nền tảng luôn ra mềm hơn.
    try:
        from PIL import Image
        for ten, (goc, cx) in THU_NHO.items():
            g = os.path.join(RA, f"{ma}_{goc}.png")
            if os.path.exists(g):
                Image.open(g).convert("RGB").resize((cx, cx), Image.LANCZOS) \
                     .save(os.path.join(RA, f"{ma}_{ten}.png"))
                n += 1
    except Exception:
        pass
    print(f"   ✅ {k['ten']:26s} {n}/7 tệp")
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    a = ap.parse_args()
    ds = [x.strip() for x in a.kenh.split(",") if x.strip()]
    ks = [k for k in KENH if not ds or k["ma"] in ds]
    tong = sum(mot_kenh(k) for k in ks)
    print(f"\n✅ {tong} tệp brand cho {len(ks)} kênh -> {RA}")
    return 0 if tong else 1


if __name__ == "__main__":
    raise SystemExit(main())
