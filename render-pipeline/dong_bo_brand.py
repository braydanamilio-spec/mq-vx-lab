#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐỒNG BỘ BRAND KIT LÊN DASHBOARD — chép ảnh + sinh `_ART_V4`.  (1/9/2026)

`brand_gt.py` sinh 7 tệp/kênh vào `render-pipeline/brand_gt/` với tên viết thường. Dashboard đọc
`/brand/<MÃ HOA>_<vai trò>_<kích thước>.png`. Hai bên chưa bao giờ được nối — nên 18 kênh mới có
đủ brand kit trên đĩa mà dashboard vẫn trống.

── ÁNH XẠ THEO KÍCH THƯỚC, KHÔNG THEO TÊN ──────────────────────────────────────────────────
Tên hai bên đặt khác nhau (`banner` vs `cover_2560x1440`), nên đoán theo tên là đoán. Đo bằng
PIL rồi khớp theo (rộng, cao) — sai kích thước thì dừng, không chép bừa.

── VÌ SAO SINH THÊM `fb_cover_820x312` ─────────────────────────────────────────────────────
Dashboard suy ra link tải Facebook bằng cách THAY CHUỖI trong tên tệp:

    b.art.cover.replace('_cover_2560x1440','_fb_cover_820x312')

Tệp ấy chưa từng được sinh ra, nên nút "⬇ Facebook 820×312" là link chết — và chết trong im
lặng, vì trình duyệt chỉ tải về một trang 404. Ở đây sinh thật (cắt giữa từ bản 2560×1440, vốn
đã chừa lề an toàn), và song song vá dashboard để đọc khoá `fb_cover` thay vì đoán từ tên.
"""
import io
import json
import os
import re
import shutil
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
NGUON = os.path.join(GOC, "brand_gt")
DICH = os.path.join(os.path.dirname(GOC), "MM0-AutoPublisher", "dashboard", "brand")
HTML = os.path.join(os.path.dirname(GOC), "MM0-AutoPublisher", "dashboard", "index.html")

# (kích thước đo được) -> (khoá trong _ART_V4, hậu tố tên tệp dashboard)
THEO_CO = {
    (800, 800):    ("avatar",    "avatar_800"),
    (1080, 1080):  ("ig_post",   "ig_post_1080"),
    (2560, 1440):  ("cover",     "cover_2560x1440"),
    (1640, 856):   ("fb_cover_lon", "fb_cover_1640x856"),
    (500, 500):    ("fb_avatar", "fb_avatar_500"),
    (640, 640):    ("ig_avatar", "ig_avatar_640"),
}


def main() -> int:
    sys.path.insert(0, GOC)
    import giai_thich as G
    from PIL import Image

    os.makedirs(DICH, exist_ok=True)
    ma = [k["ma"] for k in G.KENH]
    art, thieu, chep = {}, [], 0

    for m in ma:
        goi = {}
        for f in sorted(os.listdir(NGUON)):
            if not f.startswith(m + "_") or not f.endswith(".png"):
                continue
            p = os.path.join(NGUON, f)
            co = Image.open(p).size
            if co not in THEO_CO:
                continue                      # ảnh phụ (avatar_lon 1080 trùng ig_post — nhận cái đầu)
            khoa, hau = THEO_CO[co]
            if khoa in goi:
                continue
            ten = f"{m.upper()}_{hau}.png"
            shutil.copyfile(p, os.path.join(DICH, ten))
            goi[khoa] = f"/brand/{ten}?v=6"
            chep += 1

        # Bìa Facebook 820×312: CẮT GIỮA từ bản 2560×1440 rồi thu — không kéo giãn, vì kéo giãn
        # làm mặt nhân vật méo và đó là thứ đập vào mắt đầu tiên trên trang.
        big = os.path.join(DICH, f"{m.upper()}_cover_2560x1440.png")
        if os.path.exists(big):
            im = Image.open(big).convert("RGB")
            W, H = im.size
            ch = int(W * 312 / 820)           # chiều cao cần để đúng tỉ lệ 820:312
            y = (H - ch) // 2
            im.crop((0, y, W, y + ch)).resize((820, 312), Image.LANCZOS) \
              .save(os.path.join(DICH, f"{m.upper()}_fb_cover_820x312.png"))
            goi["fb_cover"] = f"/brand/{m.upper()}_fb_cover_820x312.png?v=6"
            chep += 1

        can = ("avatar", "cover", "fb_cover")
        v = [x for x in can if x not in goi]
        if v:
            thieu.append(f"{m}({','.join(v)})")
        art[m.upper()] = goi

    print(f"  chép {chep} tệp cho {len(ma)} kênh -> dashboard/brand/")
    if thieu:
        print(f"  ❌ thiếu ảnh bắt buộc: {', '.join(thieu)}")
        return 1
    print("  ✅ mọi kênh đủ avatar · cover · fb_cover")

    s = io.open(HTML, encoding="utf-8").read()
    moi = "    const _ART_V4 = " + json.dumps(art, ensure_ascii=False) + ";"
    s2 = re.sub(r"    const _ART_V4 = \{.*?\};", lambda _: moi, s, count=1, flags=re.S)
    if s2 == s:
        print("  ❌ không thay được _ART_V4 — DỪNG")
        return 1

    # Vá chỗ suy link bằng thay chuỗi: đọc khoá thật trước, chỉ đoán khi không có.
    cu = "${b.art.cover.replace('_cover_2560x1440','_fb_cover_820x312')}"
    if cu in s2:
        s2 = s2.replace(cu, "${b.art.fb_cover||b.art.cover}", 1)
        print("  ✅ bỏ phép suy link Facebook bằng thay chuỗi tên tệp")

    io.open(HTML, "w", encoding="utf-8").write(s2)
    print(f"  ✅ ghi _ART_V4 cho {len(art)} kênh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
