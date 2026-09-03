#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BRAND KIT MƯỜI KÊNH THIÊN NHIÊN — vẽ bằng code, không gọi API ảnh  (2/9/2026)

Dùng lại phần TAY NGHỀ của `brand_kling.py` thay vì chép: cách vẽ avatar theo khung tròn nội
tiếp, cổng bóng ngoài ở 48px, cổng chữ lọt đường cắt tròn, cổng tương phản biểu tượng/nền — cả
bốn đều đã trả giá để có (luật 14.4 và 14.5). Đây là tay nghề dùng chung, không phải bản sắc
của bộ hài, nên dùng lại là ĐÚNG.

Thứ KHÔNG dùng lại: bảng màu, biểu tượng, khẩu hiệu. Đó mới là bản sắc.
"""
from __future__ import annotations

import os

import brand_kling as BK
from PIL import Image, ImageDraw

GOC = os.path.dirname(os.path.abspath(__file__))
RA = os.path.join(GOC, "out", "brand_tn")

# Màu CHÍNH là màu của DẤU HIỆU, không phải bảng màu của phim (luật 14.5). Mọi cặp dưới đây đã
# đi qua `BK.kiem_tuong_phan` với sàn 3,0.
BRAND = {
    "ICE BEAR":     dict(chinh="#8FC7E8", phu="#F2F5F7", nen="#16202A", bt="bear",
                         khau_hieu="IT WAITS LONGER THAN YOU CAN"),
    "THE POD":      dict(chinh="#F5F7FA", phu="#2FA8C7", nen="#0E1418", bt="fin",
                         khau_hieu="THEY ALL TURN AT ONCE"),
    "BLUE GIANT":   dict(chinh="#3FB6D9", phu="#EAF6FA", nen="#0A1A2E", bt="fluke",
                         khau_hieu="IT IS STILL PASSING"),
    "PENGUIN ROAD": dict(chinh="#F2C230", phu="#F2F2F2", nen="#151A20", bt="penguin",
                         khau_hieu="THE LINE NEVER STOPS"),
    "TUSK":         dict(chinh="#E8DCC0", phu="#3FB6A8", nen="#0D2430", bt="tusk",
                         khau_hieu="IT IS REAL"),
    "SEAL ROCK":    dict(chinh="#6FD1A8", phu="#F0F4F2", nen="#161C1A", bt="wave",
                         khau_hieu="THE WATER DECIDES"),
    "DEEP DARK":    dict(chinh="#4FE0D0", phu="#9B6FE0", nen="#05070C", bt="jelly",
                         khau_hieu="IT MAKES ITS OWN LIGHT"),
    "NIGHT EYES":   dict(chinh="#D9C46B", phu="#7E8FA8", nen="#0C0F16", bt="eye",
                         khau_hieu="SOMETHING IS LOOKING BACK"),
    "FIRST LIGHT":  dict(chinh="#F2B57A", phu="#8FBF6B", nen="#1C1712", bt="hoof",
                         khau_hieu="THE FIRST HOUR"),
    "STORM COAST":  dict(chinh="#E8EDF2", phu="#5A8FC7", nen="#141A1F", bt="gale",
                         khau_hieu="IT STANDS IN IT"),
    "ICE AGE":      dict(chinh="#D9A05B", phu="#E8E4DA", nen="#1E1A16", bt="mammoth",
                         khau_hieu="IT WAS REALLY HERE"),
    "DEEP TIME":    dict(chinh="#8FC46B", phu="#D9C9A3", nen="#12180F", bt="track",
                         khau_hieu="AN ANIMAL, NOT A MONSTER"),
    "REEF WALL":    dict(chinh="#FF8A4C", phu="#3FD0E0", nen="#07202E", bt="manta",
                         khau_hieu="NOTHING HERE MOVES LIKE AN ANIMAL"),
    "GHOST MOUNTAIN": dict(chinh="#CFD8E0", phu="#8A9BA8", nen="#1A1E22", bt="paw",
                           khau_hieu="YOU WERE LOOKING RIGHT AT IT"),
}


def bieu_tuong(d: ImageDraw.ImageDraw, ten: str, cx: int, cy: int, r: int, c1, c2, c_nen=None):
    """Mười biểu tượng riêng. Hình phải đọc được ở 48px — cỡ thật trong danh sách đăng ký — nên
    mỗi cái là MỘT khối đặc có bóng ngoài riêng, không phải một bản vẽ nhiều nét mảnh."""
    c_nen = c_nen if c_nen is not None else c2
    import math as _m
    if ten == "bear":                         # đầu gấu — tròn lớn + hai tai tròn + mõm
        for dx in (-.62, .62):
            d.ellipse([cx + r * dx - r * .30, cy - r * .82, cx + r * dx + r * .30, cy - r * .22],
                      fill=c1)
        d.ellipse([cx - r * .74, cy - r * .58, cx + r * .74, cy + r * .78], fill=c1)
        d.ellipse([cx - r * .30, cy + r * .10, cx + r * .30, cy + r * .62], fill=c_nen)
    elif ten == "fin":                        # vây lưng cá voi sát thủ. Bản đầu là tam giác
        # đặt trên một thanh ngang, và ở 48px nó đọc thành NGỌN NÚI. Vây nhận ra được là nhờ mép
        # sau CONG và đỉnh lệch về phía sau — không phải nhờ nó nhọn.
        d.polygon([(cx - r * .30, cy + r * .52), (cx - r * .34, cy - r * .10),
                   (cx - r * .16, cy - r * .70), (cx + r * .10, cy - r * .90),
                   (cx + r * .02, cy - r * .48), (cx + r * .12, cy + r * .10),
                   (cx + r * .40, cy + r * .52)], fill=c1)
        d.rounded_rectangle([cx - r * .92, cy + r * .62, cx + r * .92, cy + r * .84],
                            radius=r * .11, fill=c1)
    elif ten == "fluke":                      # đuôi cá voi. Bản đầu hai cánh chụm thành chữ Y;
        # bản hai thêm cuống đứng và nó đọc thành CON BƯỚM. Đuôi thật không có cuống trong khung
        # hình — chỉ có hai thuỳ RỘNG, THẤP, xoè ngang, với một khấc chữ V sâu ở giữa.
        d.polygon([(cx - r * .98, cy - r * .40), (cx - r * .34, cy + r * .02),
                   (cx, cy + r * .52), (cx + r * .34, cy + r * .02),
                   (cx + r * .98, cy - r * .40), (cx + r * .50, cy + r * .46),
                   (cx, cy + r * .16), (cx - r * .50, cy + r * .46)], fill=c1)
    elif ten == "penguin":                    # chim cánh cụt NHÌN NGHIÊNG. Bản đầu vẽ chính
        # diện và ở 48px nó đọc thành một cái ổ khoá: thân với đầu dính làm một khối. Bóng nghiêng
        # có mỏ và chân chìa ra nên đọc được ngay.
        d.ellipse([cx - r * .48, cy - r * .30, cx + r * .44, cy + r * .74], fill=c1)
        d.ellipse([cx - r * .40, cy - r * .82, cx + r * .16, cy - r * .18], fill=c1)
        d.polygon([(cx + r * .10, cy - r * .58), (cx + r * .78, cy - r * .44),
                   (cx + r * .10, cy - r * .30)], fill=c1)
        d.polygon([(cx - r * .10, cy + r * .74), (cx + r * .62, cy + r * .74),
                   (cx + r * .62, cy + r * .92), (cx - r * .10, cy + r * .92)], fill=c1)
        d.ellipse([cx - r * .28, cy - r * .72, cx - r * .10, cy - r * .50], fill=c_nen)
    elif ten == "tusk":                       # ngà xoắn — thanh chéo dày + ba khấc
        a = _m.radians(-38)
        ux, uy = _m.cos(a), _m.sin(a)
        d.polygon([(cx - ux * r * .86 + uy * r * .20, cy - uy * r * .86 - ux * r * .20),
                   (cx - ux * r * .86 - uy * r * .20, cy - uy * r * .86 + ux * r * .20),
                   (cx + ux * r * .92, cy + uy * r * .92)], fill=c1)
        for t in (-.30, .06, .42):
            px, py = cx + ux * r * t, cy + uy * r * t
            d.line([(px - uy * r * .22, py + ux * r * .22), (px + uy * r * .22, py - ux * r * .22)],
                   fill=c_nen, width=max(2, int(r * .10)))
    elif ten == "wave":                       # sóng vỗ. Bản đầu là nửa vòng tròn trên một
        # thanh ngang, đọc thành MẶT TRỜI MỌC. Sóng nhận ra được nhờ CÁI CUỘN: một vòng dày cuộn
        # vào trong với một khoảng rỗng ở lõi, và cái môi chìa ra phía trước.
        d.ellipse([cx - r * .86, cy - r * .78, cx + r * .46, cy + r * .54], fill=c1)
        d.ellipse([cx - r * .52, cy - r * .44, cx + r * .20, cy + r * .28], fill=c_nen)
        d.polygon([(cx + r * .18, cy - r * .70), (cx + r * .96, cy - r * .18),
                   (cx + r * .34, cy - r * .04)], fill=c1)
        d.rounded_rectangle([cx - r * .96, cy + r * .58, cx + r * .96, cy + r * .82],
                            radius=r * .12, fill=c1)
    elif ten == "jelly":                      # sứa — vòm + ba tua
        d.pieslice([cx - r * .72, cy - r * .80, cx + r * .72, cy + r * .28], 180, 360, fill=c1)
        d.rectangle([cx - r * .72, cy - r * .28, cx + r * .72, cy - r * .10], fill=c1)
        for dx in (-.44, 0, .44):
            d.rounded_rectangle([cx + r * dx - r * .11, cy - r * .10,
                                 cx + r * dx + r * .11, cy + r * (.86 - abs(dx) * .5)],
                                radius=r * .09, fill=c1)
    elif ten == "eye":                        # mắt trong đêm — hình quả hạnh + con ngươi dọc
        d.polygon([(cx - r * .92, cy), (cx, cy - r * .58), (cx + r * .92, cy),
                   (cx, cy + r * .58)], fill=c1)
        d.ellipse([cx - r * .20, cy - r * .46, cx + r * .20, cy + r * .46], fill=c_nen)
    elif ten == "hoof":                        # dấu chân móng chẻ. Hai bản trước đọc thành lá,
        # vì cả hai mép đều cong. Dấu móng thật có mép TRONG gần như thẳng đứng (chỗ hai móng áp
        # nhau) và mép NGOÀI cong — chính sự bất đối xứng ấy làm nó đọc ra là móng.
        for sx in (-1, 1):
            d.polygon([(cx + sx * r * .10, cy - r * .70), (cx + sx * r * .46, cy - r * .52),
                       (cx + sx * r * .60, cy + r * .02), (cx + sx * r * .40, cy + r * .78),
                       (cx + sx * r * .18, cy + r * .86), (cx + sx * r * .10, cy + r * .30)],
                      fill=c1)
    elif ten == "gale":                        # gió giật — ba nét ngang cong dài ngắn khác nhau
        for i, (y, w) in enumerate(((-.46, .96), (0.0, .74), (.46, .88))):
            d.rounded_rectangle([cx - r * w, cy + r * y - r * .13, cx + r * w * .62,
                                 cy + r * y + r * .13], radius=r * .13, fill=c1)
            d.arc([cx + r * w * .30, cy + r * y - r * .34, cx + r * w * .92, cy + r * y + r * .34],
                  270, 90, fill=c1, width=max(2, int(r * .26)))
    elif ten == "mammoth":                     # voi ma mút.
        # Hai bản trước hỏng vì vẽ ngà bằng `arc` (rời khỏi thân ở 48px), rồi bằng đa giác THẲNG
        # song song xuống dưới (đọc thành ba cái chân — con nhện). Thứ tách ma mút khỏi mọi con
        # vật khác là CẶP NGÀ CONG VÀO NHAU thành một cái nôi, tip chỉ lên. Nên vẽ đúng nó: hai
        # cung DÀY, sinh điểm dọc theo cung rồi đổ đầy — không dùng nét, và không dùng đường thẳng.
        import math as _m
        d.ellipse([cx - r * .46, cy - r * .92, cx + r * .46, cy - r * .06], fill=c1)
        d.polygon([(cx - r * .15, cy - r * .20), (cx + r * .15, cy - r * .20),
                   (cx + r * .09, cy + r * .40), (cx - r * .09, cy + r * .40)], fill=c1)
        for sx in (-1, 1):
            ngoai, trong = [], []
            for k in range(13):
                a = _m.radians(-72 + k * 13)          # quét từ dưới lên, cong vào trong
                ngoai.append((cx + sx * (r * .30 + r * .62 * _m.cos(a)), cy + r * .34 - r * .62 * _m.sin(a)))
                trong.append((cx + sx * (r * .30 + r * .40 * _m.cos(a)), cy + r * .34 - r * .40 * _m.sin(a)))
            d.polygon(ngoai + trong[::-1], fill=c1)
    elif ten == "track":                       # dấu chân ba ngón của theropod.
        # Bản đầu: ngón toè rộng từ một đệm tròn to -> quả cầu lông. Bản hai: ngón CHỤM vào một
        # điểm dưới -> mũi tên. Dấu chân thật: ba ngón HẸP, TÁCH RỜI nhau, mọc LÊN từ một đệm
        # nhỏ ở dưới, ngón giữa dài hơn hẳn — tách rời mới là chỗ mắt đọc ra "ba ngón".
        import math as _m

        def _ngon(goc, dai, day):
            a = _m.radians(goc)
            ux, uy = _m.sin(a), -_m.cos(a)
            x0, y0 = cx + ux * r * .22, cy + r * .46 + uy * r * .22
            x1, y1 = cx + ux * r * dai, cy + r * .46 + uy * r * dai
            px, py = -uy * r * day, ux * r * day
            d.polygon([(x0 + px, y0 + py), (x1 + px * .28, y1 + py * .28),
                       (x1 - px * .28, y1 - py * .28), (x0 - px, y0 - py)], fill=c1)
        _ngon(-46, 1.02, .15)
        _ngon(0, 1.24, .16)
        _ngon(46, 1.02, .15)
        d.ellipse([cx - r * .24, cy + r * .38, cx + r * .24, cy + r * .90], fill=c1)
    elif ten == "manta":                       # cá đuối manta nhìn từ trên. Bản đầu để hai vây
        # đầu dài quá -> đọc thành RÂU côn trùng. Vây đầu thật ngắn và cụp; thứ nhận ra manta là
        # ĐÔI CÁNH RỘNG CONG NGƯỢC RA SAU, nên cánh phải cong chứ không phải hình thoi nhọn.
        d.polygon([(cx, cy - r * .40),
                   (cx + r * .46, cy - r * .34), (cx + r * .96, cy + r * .06),
                   (cx + r * .62, cy + r * .16), (cx + r * .30, cy + r * .44),
                   (cx, cy + r * .34),
                   (cx - r * .30, cy + r * .44), (cx - r * .62, cy + r * .16),
                   (cx - r * .96, cy + r * .06), (cx - r * .46, cy - r * .34)], fill=c1)
        for sx in (-1, 1):
            d.polygon([(cx + sx * r * .30, cy - r * .38), (cx + sx * r * .34, cy - r * .70),
                       (cx + sx * r * .14, cy - r * .66), (cx + sx * r * .10, cy - r * .36)],
                      fill=c1)
        d.polygon([(cx - r * .08, cy + r * .30), (cx + r * .08, cy + r * .30),
                   (cx + r * .03, cy + r * .94), (cx - r * .03, cy + r * .94)], fill=c1)
    elif ten == "paw":                         # dấu chân mèo lớn — đệm TO ở dưới, bốn ngón TRÒN
        # ở trên. Khác hẳn `track` (ba ngón nhọn của chim) ở chỗ tròn và ở số lượng.
        d.ellipse([cx - r * .50, cy + r * .04, cx + r * .50, cy + r * .86], fill=c1)
        for dx, dy, rr in ((-.62, -.30, .23), (-.22, -.60, .25), (.22, -.60, .25), (.62, -.30, .23)):
            d.ellipse([cx + r * dx - r * rr, cy + r * dy - r * rr,
                       cx + r * dx + r * rr, cy + r * dy + r * rr], fill=c1)
    else:
        d.ellipse([cx - r * .7, cy - r * .7, cx + r * .7, cy + r * .7], fill=c1)


# ── BA CỔNG: mượn nguyên phép đo của `brand_kling`, chỉ đổi bảng dữ liệu ───────────────────
def _voi_bang(f):
    """Chạy một cổng của `brand_kling` trên BRAND và biểu tượng của bộ này.

    Không chép lại phép đo. Ba cổng ấy đã trả giá để có (14.4, 14.5) và chúng đo TAY NGHỀ —
    thứ hai bộ dùng chung. Chép lại là tạo nguồn sự thật thứ hai, thứ luật 13.5 đã cấm.
    """
    g_brand, g_bt = BK.BRAND, BK.bieu_tuong
    try:
        BK.BRAND, BK.bieu_tuong = BRAND, bieu_tuong
        return f()
    finally:
        BK.BRAND, BK.bieu_tuong = g_brand, g_bt


def kiem_bong(nguong: float = 0.72) -> list:
    return _voi_bang(lambda: BK.kiem_bong(nguong))


def kiem_tron(nguong: int = 40) -> list:
    return _voi_bang(lambda: BK.kiem_tron(nguong))


def kiem_tuong_phan(san: float = 3.0) -> list:
    return _voi_bang(lambda: BK.kiem_tuong_phan(san))


def avatar(ten: str, so: int, W: int = 1080):
    return _voi_bang(lambda: BK.avatar(ten, so, W))


def xuat(dich: str = RA) -> int:
    os.makedirs(dich, exist_ok=True)
    n = 0
    for i, ten in enumerate(BRAND, 1):
        slug = ten.lower().replace(" ", "-")
        for co, W in (("avatar", 1080), ("avatar_yt", 800)):
            avatar(ten, i, W).save(os.path.join(dich, f"{i:02d}-{slug}_{co}.png"))
            n += 1
    return n


def xuat_web(dich: str) -> tuple:
    """Ảnh xem trước cho dashboard — WebP nhỏ, vì đây là thứ tải mỗi lần mở trang.

    Bài học đã ghi trong chính `index.html`: brand kit đầy đủ mà đặt lên trang thì sáu lượt mở
    là hết hạn mức Hosting 360 MB/ngày của gói free — brand kit làm sập chính cái dashboard nó
    nằm trong. Nên trang chỉ nhận bản 320px; tệp đem đăng kênh vẫn nằm ở out/brand_tn.
    """
    os.makedirs(dich, exist_ok=True)
    n = tong = 0
    for i, ten in enumerate(BRAND, 1):
        slug = ten.lower().replace(" ", "-")
        f = os.path.join(dich, f"{i:02d}-{slug}_avatar.webp")
        im = avatar(ten, i, 1080).resize((320, 320))
        im.save(f, "WEBP", quality=82, method=6)
        n += 1
        tong += os.path.getsize(f)
    return n, tong


if __name__ == "__main__":
    print("  bóng ngoài 48px :", kiem_bong() or "✅ không cặp nào trùng")
    print("  chữ lọt vòng cắt:", kiem_tron() or "✅ không kênh nào bị cắt")
    print("  tương phản ≥ 3.0:", kiem_tuong_phan() or "✅ mọi biểu tượng đọc được")
    print(f"  ✅ {xuat()} ảnh → {RA}")
    _n, _b = xuat_web(os.path.join(GOC, "..", "MM0-AutoPublisher", "dashboard", "brand_tn"))
    print(f"  ✅ {_n} ảnh xem trước · {_b / 1024:.0f} KB → dashboard/brand_tn")
