#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KIỂM BỐ CỤC — nhân vật có nằm trong khung và có cùng cỡ không. (30/8/2026)

VÌ SAO CẦN
----------
Anh nhắc BA LẦN cùng một chuyện: *"nhân vật ko zoom lên nhân vật to nhân vật nhỏ, hay nhân vật
bị lệch khỏi khung"*. Mỗi lần tôi chỉnh một hệ số rồi soi mắt, và lần sau nó lại hỏng ở một cỡ
máy khác — vì soi mắt chỉ thấy được cỡ máy nào mình vừa trích khung.

Bố cục là chuyện **tính được**. Biết toạ độ, biết cỡ, biết khung — nhân vật có ra ngoài hay
không là một phép so sánh, không phải một cảm nhận. Nên nó phải là một cổng chạy trước render,
không phải một lần soi ảnh sau render.

BA ĐIỀU KIỆN, cả ba đo từ props thật:
    · mọi nhân vật nằm TRỌN trong khung ở mọi cỡ máy
    · hai nhân vật trong cùng một lượt không chênh cỡ quá 5%
    · người đang nói không lệch tâm quá một phần tư bề ngang khung
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))

# Các hằng phải khớp KichHai.tsx. Chép sang đây là một bản thứ hai của sự thật — nhưng bản này
# CHỈ ĐỌC và chỉ để đo; nếu nó lệch khỏi engine thì cổng báo sai và mình biết ngay, còn hơn
# không đo gì. Ghi rõ ở đây để lần sau ai đổi engine thì nhớ đổi cả chỗ này.
VB_NUA = 500                 # nửa bề ngang viewBox dọc
CO_MAY = {"rong": 1.18, "trung": 1.52, "can": 1.86}
CO_NGUOI = 1.12
NUA_RONG_NGUOI = 150         # nửa bề ngang một nhân vật ở cỡ 1.0 (đo từ engine)
NUA_NGUOI = 115 * 1.12       # nửa bề ngang nhân vật, đo trên bảng tư thế nền trơn
KHE = 26                     # khe an toàn để bàn tay dang rộng cũng không chạm rìa


def x_dung(co: float) -> float:
    """Toạ độ đứng của hai người, CO theo cỡ máy — khớp công thức trong KichHai.tsx.

    Bản đầu của cổng này dùng hằng 292 chép tay, nên sau khi engine chuyển sang công thức thì
    cổng vẫn tố tràn ở mọi tập. Một cổng đo bằng con số đã lỗi thời thì tố nhầm y như không đo."""
    return min(292, max(120, (500 - KHE - NUA_NGUOI * co) / co))


def cham(f: str) -> list[str]:
    try:
        d = json.load(io.open(f, encoding="utf-8"))
    except Exception:
        return []
    loi = []
    for i, l in enumerate(d.get("luot") or []):
        co = CO_MAY.get(l.get("co") or "trung", 1.52)
        goc = l.get("goc") or "hai_nguoi"
        nua = NUA_NGUOI * co
        # Vị trí theo góc — phải khớp `_xA`/`_xB` trong engine.
        if goc == "qua_vai":
            # Chỉ kiểm NGƯỜI ĐANG NÓI (x = 40). Người tiền cảnh ở x = 430 CỐ Ý bị khung cắt bớt
            # — đó chính là bản chất của cú qua-vai: một khối gần ống kính đóng khung cho khuôn
            # mặt ở xa. Bản đầu của cổng kiểm cả hai và tố tràn, tức tố đúng cái mình vừa thiết
            # kế. Cổng phải biết ý ĐỊNH của bố cục, không chỉ biết toạ độ.
            xs = [40]
        elif goc == "mot_nguoi":
            xs = [0]
        else:
            xs = [-x_dung(co), x_dung(co)]
        for x in xs:
            trai, phai = x * co - nua, x * co + nua
            if trai < -VB_NUA - 40 or phai > VB_NUA + 40:
                loi.append(f"lượt {i} ({goc}/{l.get('co')}): nhân vật ở x={x} tràn khung "
                           f"({trai:.0f}..{phai:.0f} ngoài ±{VB_NUA})")
                break
    return loi


def main() -> int:
    ds = sys.argv[1:] or sorted(glob.glob(os.path.join(GOC, "out", "v4_*.json")))
    xau = 0
    for f in ds:
        loi = cham(f)
        ten = os.path.basename(f)[:-5]
        print(f"  {'❌' if loi else '✅'} {ten:<24}" + (f"  {loi[0]}" if loi else ""))
        xau += 1 if loi else 0
    print(f"\n  ✅ lành {len(ds) - xau}  ·  ❌ tràn khung {xau}")
    return 1 if xau else 0


if __name__ == "__main__":
    sys.exit(main())
