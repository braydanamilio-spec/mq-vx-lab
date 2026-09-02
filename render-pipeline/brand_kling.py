#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BRAND KIT MƯỜI KÊNH KLING — ảnh đại diện · ảnh bìa · hình chìm  (1/9/2026)

Vẽ HOÀN TOÀN BẰNG CODE, không gọi AI, không cần Remotion. Ba lý do:

  1. Mười kênh Kling không có nhân vật vector trong engine (Kling tự vẽ người), nên không thể
     dùng lại `BrandComic.tsx` — nó dựng brand kit từ chính dàn nhân vật vector của bộ hài.
  2. Ảnh sinh bằng AI cho brand kit là chỗ tệ nhất để dùng AI: logo phải GIỐNG HỆT nhau qua
     mọi lần dựng, mà AI thì mỗi lần một khác. Avatar đổi sau mỗi lần chạy là mất nhận diện.
  3. Free 100% và chạy được trên GitHub Actions y như ở máy anh (luật 8).

Bảng màu KHÔNG chọn lại theo cảm tính — lấy đúng từ câu `style` đã viết cho từng niche trong
`kling_kenh.py`. Nếu chọn riêng ở đây thì brand kit và video thành hai bảng màu khác nhau trên
cùng một kênh, và người xem đọc ra ngay dù không gọi được tên.

Ra `out/brand_kling/`:
    NN-<slug>_avatar.png      1080×1080  — Facebook page · Instagram
    NN-<slug>_avatar_yt.png    800×800   — YouTube
    NN-<slug>_banner.png      2560×1440  — ảnh bìa kênh YouTube (an toàn 1546×423 ở giữa)
    NN-<slug>_cover_fb.png    1640×624   — ảnh bìa fanpage Facebook
    NN-<slug>_watermark.png    300×300   — hình chìm, nền trong suốt
"""
import argparse
import json
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from kling_kenh import KENH, _slug, ho_so

HERE = os.path.dirname(os.path.abspath(__file__))
RA = os.path.join(HERE, "out", "brand_kling")

# ── BẢN SẮC TỪNG KÊNH ───────────────────────────────────────────────────────────────────────
# `chinh` là màu người xem nhớ; `phu` chỉ để nhấn một chi tiết; `nen` là nền tối để chữ trắng
# nổi ở cỡ 48px (kích thước avatar thật trong danh sách đăng ký của YouTube).
BRAND = {
    "BREAK ROOM":   dict(chinh="#1F8A8A", phu="#E8E2D4", nen="#2B2B28", bt="cup",
                         khau_hieu="JUST CIRCLING BACK ON THAT"),
    "DINER SHIFT":  dict(chinh="#E0533D", phu="#F2A93B", nen="#14213D", bt="mug",
                         khau_hieu="WE CLOSE WHEN WE CLOSE"),
    "GYM FLOOR":    dict(chinh="#F2C230", phu="#2E6BE6", nen="#23262B", bt="plate",
                         khau_hieu="THAT IS NOT WHAT THAT MACHINE IS FOR"),
    "DORM 204":     dict(chinh="#7B4FE0", phu="#3FD07A", nen="#1B1B2A", bt="bowl",
                         khau_hieu="SOMEBODY WILL WASH IT EVENTUALLY"),
    "GARAGE HOURS": dict(chinh="#E8722B", phu="#4E7FA8", nen="#221E1B", bt="wrench",
                         khau_hieu="IT WAS MAKING THAT NOISE BEFORE"),
    "FENCE LINE":   dict(chinh="#3E8F5E", phu="#E4E9EC", nen="#1E2A22", bt="fence",
                         khau_hieu="JUST BEING NEIGHBORLY"),
    "FRONT DESK":   dict(chinh="#4FB3A6", phu="#F0F4F3", nen="#1C2A2C", bt="clip",
                         khau_hieu="AND YOUR DATE OF BIRTH AGAIN"),
    "ROAD TRIP":    dict(chinh="#E3A21C", phu="#5AA6D6", nen="#1D2430", bt="road",
                         khau_hieu="WE ARE NOT STOPPING AGAIN"),
    "PET HOUSE":    dict(chinh="#F08A3C", phu="#59C2C9", nen="#241E1A", bt="paw",
                         khau_hieu="HE KNOWS WHAT HE DID"),
    "HOUSE RULES":  dict(chinh="#E0533D", phu="#2F7D6B", nen="#26221C", bt="roof",
                         khau_hieu="THE FRIDGE WAS MAKING A NOISE"),
    # ── MƯỜI KÊNH MỚI (1/9) ────────────────────────────────────────────────────────────────
    # Màu lấy đúng từ câu `style` của từng kênh trong `kling_kenh.py`, không chọn lại. Biểu
    # tượng chọn theo SILHOUETTE khác nhau — ở 48px chỉ hình dáng ngoài là đọc được, nên hai
    # kênh có cùng bóng ngoài là hai kênh trông giống nhau dù màu khác.
    "NIGHT SHIFT":    dict(chinh="#E23B2E", phu="#5FB6E8", nen="#101318", bt="pump",
                           khau_hieu="OPEN. ALWAYS. UNFORTUNATELY."),
    "OPEN HOUSE":     dict(chinh="#1E9B94", phu="#EDE7DC", nen="#2A2723", bt="sign",
                           khau_hieu="COZY MEANS SMALL"),
    "AISLE SIX":      dict(chinh="#3E9B4F", phu="#F2C230", nen="#1C221D", bt="cart",
                           khau_hieu="IT RANG UP WRONG"),
    "PARENT PICKUP":  dict(chinh="#F2B01E", phu="#E8621F", nen="#232A2E", bt="cone",
                           khau_hieu="YOU ARE IN ZONE THREE"),
    "MOVING DAY":     dict(chinh="#E8722B", phu="#9C8B78", nen="#221F1C", bt="box",
                           khau_hieu="IT CAME IN THIS WAY"),
    "THE SALON":      dict(chinh="#E0338C", phu="#F2F0EC", nen="#1A1A1D", bt="scissors",
                           khau_hieu="JUST A LITTLE OFF THE BACK"),
    "TAILGATE":       dict(chinh="#E85A1F", phu="#3E7BC4", nen="#22262B", bt="flag",
                           khau_hieu="WE PARK HERE. WE HAVE ALWAYS PARKED HERE."),
    "BAGGAGE CLAIM":  dict(chinh="#4E86D6", phu="#F28E1C", nen="#1B1F26", bt="suitcase",
                           khau_hieu="IT IS ON THE NEXT ONE"),
    "THE CAMPGROUND": dict(chinh="#3F8A4E", phu="#F2A03B", nen="#151E17", bt="tent",
                           khau_hieu="THE RANGER DID SAY"),
    "THE LAUNDROMAT": dict(chinh="#F2D024", phu="#4FB3C9", nen="#1D1E20", bt="washer",
                           khau_hieu="THAT ONE EATS QUARTERS"),
    "QUEST BOARD":  dict(chinh="#D9A441", phu="#8C2F39", nen="#241C18", bt="sword",
                         khau_hieu="THAT POSTING IS SPOKEN FOR"),
    "ORBIT SHIFT":  dict(chinh="#5BD1E6", phu="#F26B21", nen="#191C21", bt="sat",
                         khau_hieu="IT IS NOT COMING BACK"),
    "THE HAUNTING": dict(chinh="#9AA9C7", phu="#C77DA6", nen="#1F1D26", bt="ghost",
                         khau_hieu="SHE THINKS IT IS THE PIPES"),
    "DOG PARK":     dict(chinh="#8FBF3F", phu="#C8792E", nen="#20241A", bt="bone",
                         khau_hieu="I WAS HERE FIRST"),
    "SALOON 1884":  dict(chinh="#B5651D", phu="#EDD9B0", nen="#2A211A", bt="boot",
                         khau_hieu="IT IS IN THE LEDGER"),
    "DISPATCH":     dict(chinh="#6E7CF0", phu="#FFC24B", nen="#12161F", bt="headset",
                         khau_hieu="STAY ON THE LINE WITH ME"),
    "ENGINE 12":    dict(chinh="#E63946", phu="#F5D547", nen="#1A1D22", bt="hydrant",
                         khau_hieu="WHOSE IS THIS IN THE FRIDGE"),
    "SMALL CLAIMS": dict(chinh="#C8A24A", phu="#7B2233", nen="#20191A", bt="gavel",
                         khau_hieu="MARK IT AS EXHIBIT A"),
    "COUNTY FAIR":  dict(chinh="#F0C230", phu="#B33A3A", nen="#1E2118", bt="ribbon",
                         khau_hieu="THAT IS NOT IN THE RULEBOOK"),
    "THE CRUISE":   dict(chinh="#0FA3B1", phu="#F5E6C8", nen="#14212B", bt="anchor",
                         khau_hieu="THAT TOWEL WAS THERE AT SIX"),
}


def _rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ── FONT ────────────────────────────────────────────────────────────────────────────────────
# Dây chuyền chạy ở HAI nơi: máy anh (macOS) và GitHub Actions (Ubuntu). Danh sách chỉ có font
# macOS thì trên Actions rơi về `load_default()` — một font bitmap tí xíu, và brand kit ra chữ
# vỡ mà không có lỗi nào. Nên phải có đường Linux, và phải BÁO khi không tìm được font thật.
_FONT = [
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]
_da_bao = {"x": False}


def font(cs: int):
    for f in _FONT:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, cs)
            except Exception:
                pass
    if not _da_bao["x"]:
        print("⚠️  không tìm được font đậm nào — chữ sẽ vỡ. Cài fonts-dejavu trên Linux.")
        _da_bao["x"] = True
    return ImageFont.load_default()


def _rong(d, t, f):
    a = d.textbbox((0, 0), t, font=f)
    return a[2] - a[0], a[3] - a[1]


def _vua(d, t, tran_rong, cs_dau, cs_min=12):
    """Cỡ chữ lớn nhất mà chuỗi này còn lọt bề rộng. Đo BỀ RỘNG THẬT, không đếm ký tự — hai
    chuỗi cùng số ký tự rộng khác nhau, và đó là cách chữ tràn ra khỏi khung mà không ai thấy."""
    cs = cs_dau
    while cs > cs_min:
        f = font(cs)
        if _rong(d, t, f)[0] <= tran_rong:
            return f
        cs -= 2
    return font(cs_min)


# ── BIỂU TƯỢNG — vẽ bằng hình khối, đọc được ở 48px ─────────────────────────────────────────
# Mười ô 48px xếp cạnh nhau thì chỉ SILHOUETTE là đọc được. Nên mỗi biểu tượng phải khác nhau
# về HÌNH DÁNG NGOÀI, không phải về chi tiết bên trong: tròn · vuông · chữ nhật đứng · tam giác.
def bieu_tuong(d: ImageDraw.ImageDraw, ten: str, cx: int, cy: int, r: int, c1, c2,
               c_nen_bt=None):
    c_nen_bt = c_nen_bt if c_nen_bt is not None else c2
    """Vẽ biểu tượng của kênh, tâm (cx,cy), bán kính r."""
    if ten == "cup":                         # cốc giấy — hình thang đứng
        d.polygon([(cx - r * .52, cy - r * .62), (cx + r * .52, cy - r * .62),
                   (cx + r * .34, cy + r * .70), (cx - r * .34, cy + r * .70)], fill=c1)
        d.rectangle([cx - r * .58, cy - r * .74, cx + r * .58, cy - r * .50], fill=c2)
    elif ten == "mug":                       # cốc có quai. Quai vẽ bằng `arc` mảnh thì ở 48px
        # biến mất và cốc đọc thành một hình chữ nhật — phải là hai vòng tròn lồng nhau, dày.
        d.ellipse([cx + r * .04, cy - r * .40, cx + r * .86, cy + r * .42], fill=c1)
        d.ellipse([cx + r * .22, cy - r * .22, cx + r * .68, cy + r * .24], fill=c_nen_bt)
        d.rounded_rectangle([cx - r * .70, cy - r * .58, cx + r * .20, cy + r * .70],
                            radius=r * .14, fill=c1)
        d.rectangle([cx - r * .70, cy - r * .58, cx + r * .20, cy - r * .34], fill=c2)
    elif ten == "plate":                     # đĩa tạ — tròn có lỗ
        d.ellipse([cx - r * .72, cy - r * .72, cx + r * .72, cy + r * .72], fill=c1)
        d.ellipse([cx - r * .22, cy - r * .22, cx + r * .22, cy + r * .22], fill=c2)
    elif ten == "bowl":                       # bát có vành — nửa tròn cộng một vành nhô hai bên,
        # nếu không thì nó chỉ là một nửa hình tròn và đọc thành bất cứ thứ gì.
        d.pieslice([cx - r * .70, cy - r * .62, cx + r * .70, cy + r * .78], 0, 180, fill=c1)
        d.rounded_rectangle([cx - r * .86, cy - r * .22, cx + r * .86, cy + r * .02],
                            radius=r * .12, fill=c1)
        d.ellipse([cx - r * .30, cy + r * .16, cx + r * .30, cy + r * .44], fill=c_nen_bt)
    elif ten == "wrench":                     # cờ lê. Bản đầu vẽ đầu KÍN nên đọc thành chìa
        # khoá. Cờ lê nhận ra được là nhờ cái MIỆNG HỞ hình chữ C — phải khoét thật.
        d.line([(cx - r * .58, cy + r * .58), (cx + r * .30, cy - r * .30)], fill=c1,
               width=int(r * .34))
        d.ellipse([cx + r * .10, cy - r * .78, cx + r * .84, cy - r * .04], fill=c1)
        d.ellipse([cx + r * .28, cy - r * .60, cx + r * .66, cy - r * .22], fill=c_nen_bt)
        d.polygon([(cx + r * .40, cy - r * .82), (cx + r * .88, cy - r * .82),
                   (cx + r * .88, cy - r * .40), (cx + r * .47, cy - r * .40)], fill=c_nen_bt)
        d.line([(cx - r * .58, cy + r * .58), (cx - r * .34, cy + r * .34)], fill=c1,
               width=int(r * .44))
    elif ten == "fence":                      # hàng rào — ba cọc nhọn
        for i, dx in enumerate((-r * .56, 0, r * .56)):
            d.polygon([(cx + dx - r * .17, cy + r * .70), (cx + dx - r * .17, cy - r * .30),
                       (cx + dx, cy - r * .60), (cx + dx + r * .17, cy - r * .30),
                       (cx + dx + r * .17, cy + r * .70)], fill=c1)
        d.rectangle([cx - r * .80, cy + r * .02, cx + r * .80, cy + r * .20], fill=c2)
    elif ten == "clip":                       # bảng kẹp — chữ nhật đứng có kẹp trên
        d.rounded_rectangle([cx - r * .56, cy - r * .58, cx + r * .56, cy + r * .74],
                            radius=r * .10, fill=c1)
        d.rounded_rectangle([cx - r * .24, cy - r * .78, cx + r * .24, cy - r * .44],
                            radius=r * .09, fill=c2)
    elif ten == "road":                       # con đường — hình thang + vạch kẻ
        d.polygon([(cx - r * .30, cy - r * .70), (cx + r * .30, cy - r * .70),
                   (cx + r * .80, cy + r * .74), (cx - r * .80, cy + r * .74)], fill=c1)
        for i, (y0, y1, w) in enumerate(((-.52, -.28, .05), (-.12, .20, .07), (.38, .70, .10))):
            d.rectangle([cx - r * w, cy + r * y0, cx + r * w, cy + r * y1], fill=c2)
    elif ten == "paw":                        # dấu chân — đệm lớn + bốn ngón
        d.ellipse([cx - r * .46, cy - r * .06, cx + r * .46, cy + r * .70], fill=c1)
        for dx, dy, rr in ((-.56, -.42, .20), (-.20, -.62, .21), (.20, -.62, .21), (.56, -.42, .20)):
            d.ellipse([cx + r * dx - r * rr, cy + r * dy - r * rr,
                       cx + r * dx + r * rr, cy + r * dy + r * rr], fill=c1)
    elif ten == "house":                      # mái nhà — tam giác trên khối vuông
        d.polygon([(cx, cy - r * .76), (cx + r * .82, cy - r * .04), (cx - r * .82, cy - r * .04)],
                  fill=c1)
        d.rectangle([cx - r * .54, cy - r * .04, cx + r * .54, cy + r * .72], fill=c1)
        d.rectangle([cx - r * .16, cy + r * .22, cx + r * .16, cy + r * .72], fill=c2)
    elif ten == "roof":                       # mái nhà — tam giác trên khối vuông (HOUSE RULES)
        d.polygon([(cx, cy - r * .76), (cx + r * .82, cy - r * .04), (cx - r * .82, cy - r * .04)], fill=c1)
        d.rectangle([cx - r * .54, cy - r * .04, cx + r * .54, cy + r * .72], fill=c1)
        d.rectangle([cx - r * .16, cy + r * .22, cx + r * .16, cy + r * .72], fill=c_nen_bt)
    elif ten == "cart":                       # xe đẩy siêu thị — hình thang nghiêng + hai bánh
        d.polygon([(cx - r * .66, cy - r * .34), (cx + r * .74, cy - r * .34),
                   (cx + r * .50, cy + r * .30), (cx - r * .44, cy + r * .30)], fill=c1)
        d.line([(cx - r * .82, cy - r * .62), (cx - r * .60, cy - r * .34)], fill=c1, width=int(r * .17))
        for dx in (-.30, .34):
            d.ellipse([cx + r * dx - r * .15, cy + r * .44, cx + r * dx + r * .15, cy + r * .74], fill=c1)
    elif ten == "cone":                       # cọc tiêu — tam giác trên đế bẹt
        d.polygon([(cx, cy - r * .78), (cx + r * .42, cy + r * .50), (cx - r * .42, cy + r * .50)], fill=c1)
        d.rectangle([cx - r * .26, cy - r * .22, cx + r * .26, cy - r * .02], fill=c_nen_bt)
        d.rounded_rectangle([cx - r * .78, cy + r * .50, cx + r * .78, cy + r * .74], radius=r * .10, fill=c1)
    elif ten == "pump":                       # trụ bơm xăng — chữ nhật đứng cao có vòi bên
        d.rounded_rectangle([cx - r * .44, cy - r * .74, cx + r * .30, cy + r * .74],
                            radius=r * .10, fill=c1)
        d.rectangle([cx - r * .30, cy - r * .58, cx + r * .16, cy - r * .22], fill=c_nen_bt)
        d.line([(cx + r * .30, cy - r * .10), (cx + r * .74, cy - r * .10)], fill=c1, width=int(r * .15))
        d.rectangle([cx + r * .62, cy - r * .40, cx + r * .84, cy + r * .04], fill=c1)
    elif ten == "sign":                       # biển bán nhà — bảng chữ nhật treo trên hai cọc
        d.rectangle([cx - r * .62, cy + r * .10, cx - r * .48, cy + r * .80], fill=c1)
        d.rectangle([cx + r * .48, cy + r * .10, cx + r * .62, cy + r * .80], fill=c1)
        d.rounded_rectangle([cx - r * .80, cy - r * .62, cx + r * .80, cy + r * .18],
                            radius=r * .10, fill=c1)
        d.rectangle([cx - r * .56, cy - r * .42, cx + r * .56, cy - r * .28], fill=c_nen_bt)
        d.rectangle([cx - r * .56, cy - r * .14, cx + r * .20, cy - r * .02], fill=c_nen_bt)
    elif ten == "box":                        # thùng carton. Bản đầu vẽ hai nắp mở hai bên và
        # một dải băng dính giữa — ở 48px cả ba nét ấy gộp lại thành HAI THANH DỌC, không ai
        # đọc ra cái thùng. Bóng ngoài phải là một khối vuông ĐẶC, chi tiết khoét vào bên trong.
        d.rectangle([cx - r * .74, cy - r * .56, cx + r * .74, cy + r * .72], fill=c1)
        d.rectangle([cx - r * .74, cy - r * .56, cx + r * .74, cy - r * .28], fill=c_nen_bt)
        d.rectangle([cx - r * .74, cy - r * .50, cx - r * .10, cy - r * .34], fill=c1)
        d.rectangle([cx + r * .10, cy - r * .50, cx + r * .74, cy - r * .34], fill=c1)
        d.rectangle([cx - r * .12, cy - r * .28, cx + r * .12, cy + r * .72], fill=c_nen_bt)
    elif ten == "scissors":                   # kéo — hai lưỡi chéo và hai vòng tay cầm
        d.line([(cx - r * .52, cy - r * .62), (cx + r * .34, cy + r * .34)], fill=c1, width=int(r * .19))
        d.line([(cx + r * .52, cy - r * .62), (cx - r * .34, cy + r * .34)], fill=c1, width=int(r * .19))
        for dx in (-.40, .40):
            d.ellipse([cx + r * dx - r * .26, cy + r * .30, cx + r * dx + r * .26, cy + r * .82], fill=c1)
            d.ellipse([cx + r * dx - r * .13, cy + r * .43, cx + r * dx + r * .13, cy + r * .69], fill=c_nen_bt)
    elif ten == "flag":                       # cờ cổ vũ — tam giác bay trên cán đứng
        d.rectangle([cx - r * .60, cy - r * .78, cx - r * .44, cy + r * .78], fill=c1)
        d.polygon([(cx - r * .44, cy - r * .72), (cx + r * .80, cy - r * .34),
                   (cx - r * .44, cy + r * .04)], fill=c1)
    elif ten == "suitcase":                   # vali — chữ nhật nằm có quai trên
        d.rounded_rectangle([cx - r * .72, cy - r * .30, cx + r * .72, cy + r * .66],
                            radius=r * .12, fill=c1)
        d.arc([cx - r * .30, cy - r * .74, cx + r * .30, cy - r * .10], 180, 360, fill=c1, width=int(r * .15))
        d.rectangle([cx - r * .72, cy + r * .10, cx + r * .72, cy + r * .26], fill=c_nen_bt)
    elif ten == "tent":                       # lều — tam giác có cửa hình chữ A
        d.polygon([(cx, cy - r * .74), (cx + r * .84, cy + r * .62), (cx - r * .84, cy + r * .62)], fill=c1)
        d.polygon([(cx, cy - r * .22), (cx + r * .26, cy + r * .62), (cx - r * .26, cy + r * .62)],
                  fill=c_nen_bt)
    elif ten == "washer":                     # máy giặt — vuông có cửa tròn lớn
        d.rounded_rectangle([cx - r * .70, cy - r * .70, cx + r * .70, cy + r * .74],
                            radius=r * .10, fill=c1)
        d.ellipse([cx - r * .40, cy - r * .26, cx + r * .40, cy + r * .54], fill=c_nen_bt)
        d.rectangle([cx - r * .58, cy - r * .58, cx - r * .18, cy - r * .44], fill=c_nen_bt)
    elif ten == "sword":                      # kiếm — lưỡi DÀI chiếm hai phần ba chiều cao,
        # chắn ngang hẹp hơn lưỡi là dài, chuôi có núm nhô RA (không khoét vào, khoét thì mất).
        d.polygon([(cx, cy - r * .96), (cx + r * .20, cy - r * .60), (cx + r * .20, cy + r * .18),
                   (cx - r * .20, cy + r * .18), (cx - r * .20, cy - r * .60)], fill=c1)
        d.rounded_rectangle([cx - r * .66, cy + r * .18, cx + r * .66, cy + r * .38],
                            radius=r * .08, fill=c1)
        d.rectangle([cx - r * .13, cy + r * .38, cx + r * .13, cy + r * .74], fill=c1)
        d.ellipse([cx - r * .26, cy + r * .66, cx + r * .26, cy + r * .96], fill=c1)
    elif ten == "sat":                        # vệ tinh — thân hẹp, hai tấm pin TÁCH HẲN ra bằng
        # một quãng nền. Bản đầu để panel dính vào thân nên ở 48px nó đọc thành một cục tạ.
        d.rounded_rectangle([cx - r * .22, cy - r * .44, cx + r * .22, cy + r * .44],
                            radius=r * .07, fill=c1)
        for sx in (-1, 1):
            _a, _b = sorted((cx + sx * r * .22, cx + sx * r * .46))
            d.rectangle([_a, cy - r * .06, _b, cy + r * .06], fill=c1)          # cần nối mảnh
            _a, _b = sorted((cx + sx * r * .46, cx + sx * r * .96))
            d.rectangle([_a, cy - r * .40, _b, cy + r * .40], fill=c1)          # tấm pin
            d.rectangle([_a, cy - r * .05, _b, cy + r * .05], fill=c_nen_bt)    # rãnh giữa tấm
        d.rectangle([cx - r * .05, cy - r * .78, cx + r * .05, cy - r * .44], fill=c1)
        d.ellipse([cx - r * .17, cy - r * .98, cx + r * .17, cy - r * .66], fill=c1)
    elif ten == "ghost":                      # ma — vòm trên + ba múi dưới, hai mắt khoét
        d.pieslice([cx - r * .62, cy - r * .84, cx + r * .62, cy + r * .40], 180, 360, fill=c1)
        d.rectangle([cx - r * .62, cy - r * .22, cx + r * .62, cy + r * .42], fill=c1)
        for dx in (-.41, 0, .41):
            d.pieslice([cx + r * dx - r * .21, cy + r * .20, cx + r * dx + r * .21, cy + r * .64],
                       0, 180, fill=c1)
        for dx in (-.22, .22):
            d.ellipse([cx + r * dx - r * .12, cy - r * .38, cx + r * dx + r * .12, cy - r * .08],
                      fill=c_nen_bt)
    elif ten == "bone":                       # khúc xương — thân ngang + hai cặp bướu hai đầu
        d.rounded_rectangle([cx - r * .58, cy - r * .17, cx + r * .58, cy + r * .17],
                            radius=r * .10, fill=c1)
        for sx in (-1, 1):
            for sy in (-1, 1):
                d.ellipse([cx + sx * r * .62 - r * .27, cy + sy * r * .27 - r * .27,
                           cx + sx * r * .62 + r * .27, cy + sy * r * .27 + r * .27], fill=c1)
    elif ten == "boot":                        # ủng cao bồi — ống đứng + mũi chìa + gót
        d.polygon([(cx - r * .40, cy - r * .82), (cx + r * .16, cy - r * .82),
                   (cx + r * .16, cy + r * .22), (cx - r * .40, cy + r * .22)], fill=c1)
        d.polygon([(cx - r * .40, cy + r * .22), (cx + r * .16, cy + r * .22),
                   (cx + r * .84, cy + r * .46), (cx + r * .84, cy + r * .64),
                   (cx - r * .40, cy + r * .64)], fill=c1)
        d.rectangle([cx - r * .40, cy + r * .64, cx - r * .04, cy + r * .90], fill=c1)
        d.rectangle([cx - r * .40, cy - r * .48, cx + r * .16, cy - r * .32], fill=c2)
    elif ten == "headset":                     # tai nghe — vành cung dày + hai chụp tai
        d.arc([cx - r * .70, cy - r * .78, cx + r * .70, cy + r * .34], 180, 360,
              fill=c1, width=int(max(2, r * .20)))
        for sx in (-1, 1):
            d.rounded_rectangle([cx + sx * r * .70 - r * .21, cy - r * .30,
                                 cx + sx * r * .70 + r * .21, cy + r * .34],
                                radius=r * .10, fill=c1)
        d.rounded_rectangle([cx - r * .04, cy + r * .18, cx + r * .58, cy + r * .32],
                            radius=r * .07, fill=c2)
    elif ten == "hydrant":                     # trụ nước cứu hoả — thân + nắp chóp + hai vòi bên
        d.ellipse([cx - r * .28, cy - r * .92, cx + r * .28, cy - r * .56], fill=c1)
        d.rectangle([cx - r * .10, cy - r * .70, cx + r * .10, cy - r * .52], fill=c1)
        d.rounded_rectangle([cx - r * .34, cy - r * .56, cx + r * .34, cy + r * .58],
                            radius=r * .14, fill=c1)
        for sx in (-1, 1):
            d.rounded_rectangle([cx + sx * r * .58 - r * .22, cy - r * .28,
                                 cx + sx * r * .58 + r * .22, cy + r * .02],
                                radius=r * .07, fill=c1)
        d.rectangle([cx - r * .62, cy + r * .58, cx + r * .62, cy + r * .82], fill=c1)
        d.rectangle([cx - r * .34, cy - r * .22, cx + r * .34, cy - r * .06], fill=c2)
    elif ten == "gavel":                       # búa toà. Vẽ THẲNG ĐỨNG thì ở 48px nó đọc thành
        # chữ I hoặc quả tạ — đã thử hai lần. Búa toà chỉ nhận ra được khi ĐẦU BÚA NGHIÊNG và
        # cán đâm chéo xuống: đó là hình người ta thực sự nhớ.
        import math as _m
        a = _m.radians(-32)
        ux, uy = _m.cos(a), _m.sin(a)          # trục đầu búa
        vx, vy = -uy, ux                       # trục cán, vuông góc
        hx, hy = cx - r * .16, cy - r * .40    # tâm đầu búa
        L, T = r * .56, r * .25                # nửa dài · nửa dày của đầu búa
        d.polygon([(hx + ux * L + vx * T, hy + uy * L + vy * T),
                   (hx + ux * L - vx * T, hy + uy * L - vy * T),
                   (hx - ux * L - vx * T, hy - uy * L - vy * T),
                   (hx - ux * L + vx * T, hy - uy * L + vy * T)], fill=c1)
        d.line([(hx, hy), (hx + vx * r * 1.06, hy + vy * r * 1.06)],
               fill=c1, width=int(max(2, r * .21)))
        d.rounded_rectangle([cx - r * .86, cy + r * .62, cx + r * .34, cy + r * .92],
                            radius=r * .10, fill=c1)
    elif ten == "ribbon":                      # ruy băng giải — hoa thị tròn + hai dải đuôi
        d.polygon([(cx - r * .36, cy + r * .12), (cx - r * .10, cy + r * .12),
                   (cx - r * .16, cy + r * .92), (cx - r * .46, cy + r * .62)], fill=c1)
        d.polygon([(cx + r * .36, cy + r * .12), (cx + r * .10, cy + r * .12),
                   (cx + r * .16, cy + r * .92), (cx + r * .46, cy + r * .62)], fill=c1)
        for a in range(0, 360, 45):
            import math as _m
            ax, ay = cx + r * .46 * _m.cos(_m.radians(a)), cy - r * .22 + r * .46 * _m.sin(_m.radians(a))
            d.ellipse([ax - r * .21, ay - r * .21, ax + r * .21, ay + r * .21], fill=c1)
        d.ellipse([cx - r * .40, cy - r * .62, cx + r * .40, cy + r * .18], fill=c1)
        d.ellipse([cx - r * .17, cy - r * .39, cx + r * .17, cy - r * .05], fill=c_nen_bt)
    elif ten == "anchor":                      # mỏ neo — khuyên + thân + ngang + hai càng cong
        d.ellipse([cx - r * .21, cy - r * .90, cx + r * .21, cy - r * .48], fill=c1)
        d.ellipse([cx - r * .10, cy - r * .79, cx + r * .10, cy - r * .59], fill=c_nen_bt)
        d.rectangle([cx - r * .11, cy - r * .62, cx + r * .11, cy + r * .72], fill=c1)
        d.rounded_rectangle([cx - r * .52, cy - r * .40, cx + r * .52, cy - r * .24],
                            radius=r * .06, fill=c1)
        d.arc([cx - r * .82, cy - r * .06, cx + r * .82, cy + r * .86], 0, 180,
              fill=c1, width=int(max(2, r * .19)))
        for sx in (-1, 1):
            d.polygon([(cx + sx * r * .82, cy + r * .26), (cx + sx * r * .58, cy + r * .48),
                       (cx + sx * r * .94, cy + r * .54)], fill=c1)
    else:
        d.ellipse([cx - r * .7, cy - r * .7, cx + r * .7, cy + r * .7], fill=c1)



def _sang(h: str) -> float:
    """Độ sáng tương đối WCAG của một mã màu."""
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def kiem_tuong_phan(san: float = 3.0) -> list:
    """Kênh nào có biểu tượng không đủ tương phản với nền của chính nó.

    2/9 — Mười kênh mới lần đầu dùng màu KHÔNG KHÍ của bộ phim làm màu dấu hiệu: đỏ huy hiệu
    cho sảnh hội mạo hiểm, đỏ tiết cho phòng xử. Đúng cho một khung phim, sai cho một hình
    tròn 48 điểm ảnh trong danh sách đăng ký — SMALL CLAIMS đo được 1,74 và QUEST BOARD 2,06,
    thấp hơn mọi kênh đang có. Nhìn lưới avatar thì thấy ngay: hai biểu tượng ấy gần như biến
    mất.

    Cùng họ lỗi với `k["mau"]` ở luật số 6 và với biểu tượng tàng hình trên ảnh bìa (13.27):
    *mượn một giá trị cho việc nó không sinh ra để làm*. `chinh` là màu của DẤU HIỆU, không
    phải màu của bộ phim; nếu chúng phải khác nhau thì để bảng màu phim ở `phu`.

    Sàn 3,0 lấy từ số đo thật: hai mươi kênh đầu nằm trong khoảng 2,61–10,98. Sàn đặt ngay
    trên đuôi dưới ấy, nên nó bắt được cái mới mà không tự nhận là đã sửa cái cũ.
    """
    e = []
    for t, b in BRAND.items():
        la, lb = _sang(b["chinh"]), _sang(b["nen"])
        hi, lo = max(la, lb), min(la, lb)
        g = (hi + .05) / (lo + .05)
        if g < san:
            e.append((round(g, 2), t, b["chinh"], b["nen"]))
    return sorted(e)


def kiem_tron(nguong: int = 40) -> list:
    """Kênh nào có CHỮ hoặc SỐ trên avatar rơi ra ngoài đường tròn nền tảng sẽ cắt.

    2/9 — Không thay được bằng mắt: nới mép từ 0,965 xuống 0,90 mà lưới nhìn *y hệt*, vì cỡ
    chữ đang bị chặn bởi CHIỀU CAO dải chứ không bởi bề ngang, nên trần ngang mới không hề
    ràng buộc. Đúng luật §1: khi con số và con mắt bất đồng thì đo pixel.

    Cách đo: dựng avatar, lấy mọi pixel NGOÀI đường tròn nội tiếp, đếm pixel nào mang màu nền
    (`nen`) trong khi nằm trong DẢI MÀU đáy — vì trong dải, màu nền chỉ xuất hiện ở nét chữ.
    Cùng phép ấy cho huy hiệu số ở nửa trên.
    """
    from PIL import Image
    ra = []
    for t, b in BRAND.items():
        im = avatar(t, 1, 400).convert("RGB")
        W = 400
        R = W / 2
        cn = _rgb(b["nen"])
        px = im.load()
        day = int(W * .30)
        ngoai = 0
        for y in range(W):
            dy = y - R
            for x in range(W):
                dx = x - R
                if dx * dx + dy * dy <= R * R:
                    continue
                if y < W - day:              # nửa trên: chỉ quan tâm huy hiệu số
                    continue
                r, g, bl = px[x, y]
                if abs(r - cn[0]) + abs(g - cn[1]) + abs(bl - cn[2]) < 60:
                    ngoai += 1
        if ngoai > nguong:
            ra.append((ngoai, t))
    return sorted(ra, reverse=True)

def _hat(im: Image.Image, muc: float = 5.0) -> Image.Image:
    """Hạt nhiễu rất nhẹ phủ toàn khung. Không phải trang trí: nó phủ lên CẢ nền phẳng lẫn khối
    màu nên hai thứ khác bản chất mới chung một bề mặt — thiếu nó thì hình trông như file SVG,
    và "trông như SVG" là một trong những dấu hiệu nghiệp dư đọc ra trong nửa giây (mục 12.12)."""
    import random
    random.seed(7)
    W, H = im.size
    n = Image.new("L", (W // 3, H // 3))
    n.putdata([random.randint(0, 255) for _ in range(n.width * n.height)])
    n = n.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.6))
    return Image.blend(im, Image.composite(Image.new("RGB", (W, H), (255, 255, 255)),
                                           Image.new("RGB", (W, H), (0, 0, 0)), n),
                       muc / 255.0 * 3)


def _vien(im: Image.Image, muc: float = 0.30) -> Image.Image:
    """Vignette — tối bốn góc. Cùng lý do với hạt: nó buộc mọi thứ trong khung chịu chung một
    nguồn sáng, nên các khối màu thôi trông như dán rời lên nền."""
    W, H = im.size
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([-W * .28, -H * .28, W * 1.28, H * 1.28], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(min(W, H) * .12))
    toi = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(im, Image.blend(im, toi, muc), m)


# ── DỰNG TỪNG CỠ ────────────────────────────────────────────────────────────────────────────
def avatar(ten: str, so: int, W: int = 1080) -> Image.Image:
    """Bố cục: biểu tượng lớn ở trên, DẢI MÀU đặc ở dưới mang tên kênh, số trong vòng an toàn.

    Bản đầu vẽ một vòng tròn viền rồi đặt cả biểu tượng lẫn tên BÊN TRONG. Soi lưới mười avatar
    thì thấy ba lỗi mà cổng số không bắt được cái nào:
      · huy hiệu số đè thẳng lên dòng chữ thứ hai — "ROOM" thành "R⓵OM", 10/10 kênh
      · tên kênh dài tràn qua vòng tròn rồi bị mép ảnh cắt ("GARAGE HOURS", "HOUSE RULES")
      · nét vòng tròn cắt ngang chữ
    Gốc chung: vòng tròn ăn mất bề ngang, mà tôi lại giới hạn chữ theo bề ngang KHUNG VUÔNG
    (0,80·W) chứ không theo đường kính TRONG của vòng. Ba lỗi, một nguyên nhân.

    2/9 — VÀ CÙNG MỘT LỖI ẤY LẦN THỨ HAI, vì bản vá trên chỉ bỏ vòng tròn TÔI VẼ. YouTube,
    Facebook và Instagram đều tự cắt avatar thành hình tròn; bỏ vòng tròn của mình không làm
    vòng tròn của họ biến mất. Ghép lưới rồi vẽ đè đường cắt tròn lên thì thấy:
      · dải tên bị cắt ngang GIỮA dòng chữ — 30/30 kênh
      · huy hiệu số ở góc nằm HOÀN TOÀN ngoài đường tròn, tức không bao giờ hiện ra
    Nên khung an toàn không phải hình vuông W×W mà là ĐƯỜNG TRÒN NỘI TIẾP. Bề ngang cho phép
    ở mỗi độ cao là dây cung tại độ cao ấy, không phải một hằng số:  nửa dây = √(R² − d²).
    Dải màu vẫn tràn hết bề ngang (bị cắt cong trông vẫn đúng) — chỉ CHỮ và SỐ phải vào trong.
    """
    b = BRAND[ten]
    c_nen, c1, c2 = _rgb(b["nen"]), _rgb(b["chinh"]), _rgb(b["phu"])
    im = Image.new("RGB", (W, W), c_nen)
    d = ImageDraw.Draw(im)
    R = W / 2

    def _day_cung(y: float, le: float = 0.90) -> int:
        """Bề ngang dùng được của đường tròn nội tiếp tại độ cao `y`, chừa một mép nhỏ."""
        dd = abs(y - R)
        return int(2 * (R * R - dd * dd) ** .5 * le) if dd < R else 0

    day = int(W * .30)                      # dải màu đáy — vẫn tràn hết bề ngang
    d.rectangle([0, W - day, W, W], fill=c1)
    bieu_tuong(d, b["bt"], W // 2, int((W - day) * .50), int(W * .215), c1, c_nen)

    # Khối chữ neo theo ĐÁY của nó, không căn giữa dải: chỗ hẹp nhất là dòng dưới cùng, nên
    # đáy khối là thứ quyết định cỡ chữ. Căn giữa dải thì dòng dưới luôn thò ra ngoài cung.
    y_day = int(W * .875)                   # đáy khối chữ
    tran = _day_cung(y_day)
    f1 = _vua(d, ten, tran, int(day * .46))
    if _rong(d, ten, f1)[0] <= tran and len(ten) <= 12:
        dong = [ten]
    else:
        tu = ten.split()
        dong = [tu[0], " ".join(tu[1:])] if len(tu) > 1 else [ten]
    fs = [_vua(d, t, tran, int(day * (.46 if len(dong) == 1 else .34))) for t in dong]
    hs = [_rong(d, t, fo)[1] for t, fo in zip(dong, fs)]
    khe = int(day * .06)
    tong = sum(hs) + khe * (len(dong) - 1)
    y = y_day - tong
    for t, fo, h in zip(dong, fs, hs):
        w, _ = _rong(d, t, fo)
        d.text(((W - w) // 2, y), t, font=fo, fill=c_nen)
        y += h + khe

    # Số: kéo vào trong đường tròn. Ở góc khung vuông nó cách tâm 0,57·W — ngoài bán kính 0,5·W,
    # nên bản cũ vẽ một huy hiệu mà không nền tảng nào hiển thị.
    r = int(W * .052)
    cxn, cyn = int(W * .245), int(W * .205)
    d.ellipse([cxn - r, cyn - r, cxn + r, cyn + r], fill=c1)
    fn = font(int(r * 1.15))
    sn = f"{so:02d}"
    wn, hn = _rong(d, sn, fn)
    d.text((cxn - wn // 2, cyn - hn // 2 - int(r * .16)), sn, font=fn, fill=c_nen)
    return _vien(_hat(im), 0.22)

def banner(ten: str, so: int, W: int = 2560, H: int = 1440) -> Image.Image:
    """Ảnh bìa YouTube. Chữ phải nằm trong ô an toàn 1546×423 GIỮA khung — ngoài ô đó thì mobile
    cắt mất, và đó là chỗ phần lớn người xem nhìn thấy kênh lần đầu."""
    b = BRAND[ten]
    c_nen, c1, c2 = _rgb(b["nen"]), _rgb(b["chinh"]), _rgb(b["phu"])
    im = Image.new("RGB", (W, H), c_nen)
    d = ImageDraw.Draw(im)

    # Dải chéo màu thương hiệu chạy hết khung: phần ngoài ô an toàn KHÔNG được mang thông tin,
    # nhưng cũng không nên trống — nó là thứ lấp đầy màn hình desktop.
    for i in range(-2, 14):
        x = i * (W // 12)
        d.polygon([(x, H), (x + W // 26, H), (x + W // 26 + H // 3, 0), (x + H // 3, 0)],
                  fill=tuple(min(255, int(v * (1.06 if i % 2 else .94))) for v in c_nen))

    ax, ay = (W - 1546) // 2, (H - 423) // 2
    bieu_tuong(d, b["bt"], ax + 190, ay + 212, 132, c1, c_nen)

    f = _vua(d, ten, 1546 - 400, 168)
    _, h = _rong(d, ten, f)
    d.text((ax + 372, ay + 212 - h - 22), ten, font=f, fill=(250, 248, 244))

    kh = b["khau_hieu"]
    fk = _vua(d, kh, 1546 - 400, 60)
    d.text((ax + 372, ay + 212 + 26), kh, font=fk, fill=c1)

    d.rectangle([ax + 372, ay + 212 + 8, ax + 372 + 210, ay + 212 + 15], fill=c2)
    return _vien(_hat(im), 0.34)


def cover_fb(ten: str, so: int) -> Image.Image:
    """Ảnh bìa fanpage. KHÔNG co giãn từ banner YouTube: Facebook cắt HAI BÊN trên mobile còn
    YouTube cắt TRÊN DƯỚI, nên một ảnh dùng chung thì luôn có một bên mất chữ."""
    W, H = 1640, 624
    b = BRAND[ten]
    c_nen, c1, c2 = _rgb(b["nen"]), _rgb(b["chinh"]), _rgb(b["phu"])
    im = Image.new("RGB", (W, H), c_nen)
    d = ImageDraw.Draw(im)
    d.rectangle([0, H - 14, W, H], fill=c1)
    bieu_tuong(d, b["bt"], int(W * .50), int(H * .34), 104, c1, c_nen)
    f = _vua(d, ten, int(W * .74), 104)
    w, h = _rong(d, ten, f)
    d.text(((W - w) // 2, int(H * .52)), ten, font=f, fill=(250, 248, 244))
    fk = _vua(d, b["khau_hieu"], int(W * .74), 40)
    wk, _ = _rong(d, b["khau_hieu"], fk)
    d.text(((W - wk) // 2, int(H * .52) + h + 22), b["khau_hieu"], font=fk, fill=c1)
    return _vien(_hat(im), 0.30)


def watermark(ten: str, W: int = 300) -> Image.Image:
    """Hình chìm đè lên video — nền TRONG SUỐT và mờ. Dải tên kênh dưới mọi khung là dấu hiệu
    nghiệp dư số một (mục 12.12); một biểu tượng nhạt ở góc thì không."""
    b = BRAND[ten]
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c1 = _rgb(b["chinh"]) + (215,)
    d.ellipse([6, 6, W - 6, W - 6], outline=c1, width=int(W * .075))
    bieu_tuong(d, b["bt"], W // 2, W // 2, int(W * .30), c1, (0, 0, 0, 0))
    return im


CO = {"avatar": (avatar, 1080), "avatar_yt": (avatar, 800),
      "banner": (banner, None), "cover_fb": (cover_fb, None), "watermark": (watermark, 300)}


# ── CỔNG: CHỮ CÓ TRÀN KHÔNG, CÓ ĐÈ BIỂU TƯỢNG KHÔNG ─────────────────────────────────────────
def kiem(im: Image.Image, ten: str, cỡ: str) -> list:
    """Ba phép đo bắt đúng loại lỗi mà nhìn từng ảnh một không thấy.

    Banner DIET WARS của bộ hài từng ra khung có tên kênh đè thẳng lên nhân vật, và chỉ phát
    hiện khi anh gửi ảnh lại — vì nhìn riêng thì mỗi cái vẫn "có chữ, có hình"."""
    e = []
    W, H = im.size
    px = im.convert("RGB").load()
    # 1 · viền ngoài phải sạch: chữ chạm mép là chữ sẽ bị cắt trên mọi nền tảng
    bien = max(2, int(min(W, H) * .012))
    nen = px[3, 3]
    for x in range(0, W, max(1, W // 200)):
        for y in (bien, H - bien - 1):
            if sum(abs(a - b) for a, b in zip(px[x, y], nen)) > 210:
                e.append(f"{cỡ}: có nét sáng sát mép trên/dưới ({x},{y}) — sẽ bị cắt")
                break
        if e:
            break
    # 2 · không được là ảnh phẳng lì một màu (dấu hiệu hàm vẽ hỏng mà không báo lỗi)
    mau = {px[x, y] for x in range(0, W, max(1, W // 40)) for y in range(0, H, max(1, H // 40))}
    if len(mau) < 6:
        e.append(f"{cỡ}: chỉ {len(mau)} màu — gần như ảnh trống, có thể hàm vẽ hỏng")
    return e


def mot_kenh(ten: str, so: int, thu: str) -> int:
    n = 0
    sl = _slug(ten)
    for cỡ, (fn, w) in CO.items():
        im = fn(ten, so) if fn is not watermark else fn(ten)
        if w and im.size[0] != w:
            im = im.resize((w, w), Image.LANCZOS)
        loi = kiem(im, ten, cỡ) if cỡ != "watermark" else []
        if loi:
            print("   ⚠️ " + " · ".join(loi))
        f = os.path.join(thu, f"{so:02d}-{sl}_{cỡ}.png")
        im.save(f)
        n += 1
    return n


# ── BẢN XEM TRƯỚC CHO WEB ───────────────────────────────────────────────────────────────────
# PNG đầy đủ nặng 53 MB cho mười kênh (banner 2,3 MB/tệp). Đẩy chỗ ấy lên Firebase Hosting thì
# **sáu lượt mở trang là hết hạn mức 360 MB/ngày** của gói free — tức brand kit làm sập chính
# cái dashboard nó nằm trong.
#
# Lý do PNG phồng: lớp hạt nhiễu biến mảng màu phẳng thành nhiễu từng điểm ảnh, và PNG nén theo
# vùng đồng màu nên mất sạch lợi thế. Đó là cái giá của lớp hoàn thiện — đáng trả ở tệp đem đăng
# kênh, KHÔNG đáng trả ở ảnh xem trước 320px.
#
# Nên tách hai đường, và tách theo CÔNG DỤNG chứ không theo kích thước:
#   · PNG đầy đủ  -> ở lại máy / Drive, để tải lên YouTube và Facebook (họ cần đúng cỡ, nét)
#   · WebP nhỏ    -> lên web, chỉ để anh NHÌN. 320px avatar = 5 KB, 640px banner = 8 KB.
# Cả mười kênh gói lại còn ~130 KB, tức 0,04% hạn mức ngày thay vì 15%.
def xuat_web(nguon: str, dich: str) -> tuple:
    import glob
    os.makedirs(dich, exist_ok=True)
    RONG = {"avatar": 320, "banner": 640, "cover_fb": 560, "watermark": 96}
    n, tong = 0, 0
    for f in sorted(glob.glob(os.path.join(nguon, "*.png"))):
        ten = os.path.basename(f)[:-4]
        co = ten.rsplit("_", 1)[-1]
        if co not in RONG:                      # avatar_yt chỉ là bản thu nhỏ của avatar
            continue
        im = Image.open(f)
        w = RONG[co]
        im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
        d = os.path.join(dich, ten + ".webp")
        im.save(d, format="WEBP", quality=82, method=6)
        tong += os.path.getsize(d) / 1024
        n += 1
    # mục lục để web không phải đoán tên tệp
    io_json = os.path.join(dich, "index.json")
    with open(io_json, "w", encoding="utf-8") as fh:
        json.dump({"kenh": [{"so": list(KENH).index(t) + 1, "ten": t, "slug": _slug(t),
                             "mau": BRAND[t]["chinh"], "nen": BRAND[t]["nen"],
                             "khau_hieu": BRAND[t]["khau_hieu"]}
                            for t in KENH if t in BRAND],
                   "co": list(RONG)}, fh, ensure_ascii=False)
    return n, tong


def main() -> int:
    ap = argparse.ArgumentParser(description="Brand kit 10 kênh Kling — vẽ bằng code, không AI")
    ap.add_argument("--kenh", default="", help="chỉ một kênh (tên đầy đủ)")
    ap.add_argument("--ra", default=RA)
    ap.add_argument("--web", default="", metavar="THƯ_MỤC",
                    help="xuất thêm bản XEM TRƯỚC nhẹ (WebP) cho dashboard")
    a = ap.parse_args()
    os.makedirs(a.ra, exist_ok=True)
    chon = [a.kenh.upper()] if a.kenh else list(KENH)
    tong = 0
    for i, ten in enumerate(chon, 1):
        if ten not in BRAND:
            print(f"⚠️ chưa có bản sắc cho {ten!r}")
            continue
        so = list(KENH).index(ten) + 1
        n = mot_kenh(ten, so, a.ra)
        tong += n
        print(f"  {so:02d} · {ten:14s} {n} ảnh")
    print(f"\n{'✅' if tong else '⚠️'} {tong} ảnh brand cho {len(chon)} kênh → {a.ra}")
    if a.web:
        n, kb = xuat_web(a.ra, a.web)
        print(f"✅ {n} ảnh xem trước (WebP) · {kb:.0f} KB → {a.web}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ══ CỔNG VA CHẠM BÓNG NGOÀI ═══════════════════════════════════════════════════════════════
# 1/9 — Soi lưới hai mươi avatar bằng mắt thì thấy ngay NIGHT SHIFT dùng đúng cái cốc của
# BREAK ROOM và OPEN HOUSE gần trùng mái nhà của HOUSE RULES. Nhưng "soi bằng mắt" không dùng
# lại được: kênh thứ hai mươi mốt sẽ va chạm với một trong hai mươi kênh kia và không ai nhớ hết.
#
# Ở 48px — cỡ avatar thật trong danh sách đăng ký — **chỉ BÓNG NGOÀI là đọc được**, màu chỉ giúp
# phân biệt sau khi hình đã khác. Nên phép đo đúng là: vẽ riêng biểu tượng trên nền trống, hạ
# xuống 48px, nhị phân hoá, rồi so hai mặt nạ. Hai kênh trùng bóng là hai kênh trông giống nhau
# dù bảng màu khác hẳn.
def _mask(bt: str, N: int = 48):
    im = Image.new("L", (N * 4, N * 4), 0)
    d = ImageDraw.Draw(im)
    bieu_tuong(d, bt, N * 2, N * 2, int(N * 1.3), 255, 0, 0)
    im = im.resize((N, N), Image.LANCZOS)
    return [1 if p > 96 else 0 for p in im.getdata()]


def kiem_bong(nguong: float = 0.72) -> list:
    """Cặp biểu tượng nào có bóng ngoài trùng nhau quá `nguong` (Jaccard trên mặt nạ 48px)."""
    import itertools
    m = {t: _mask(b["bt"]) for t, b in BRAND.items()}
    e = []
    for a, b in itertools.combinations(m, 2):
        x, y = m[a], m[b]
        chung = sum(1 for i, j in zip(x, y) if i and j)
        hop = sum(1 for i, j in zip(x, y) if i or j)
        g = chung / max(1, hop)
        if g > nguong:
            e.append((round(g, 2), a, b, BRAND[a]["bt"], BRAND[b]["bt"]))
    return sorted(e, reverse=True)
