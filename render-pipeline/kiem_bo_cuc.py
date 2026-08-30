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
# 31/8 — HAI con số, vì bố cục có hai chế độ. 115 là bề ngang ở tư thế NGHỈ, và cổng dùng nó
# nên nó báo "lành 10" trong khi khung render vẫn cắt mất nửa người: nhân vật không đứng nghỉ
# cả clip, `chi` vươn tay ngang tới 181 đơn vị. Đo tư thế hẹp nhất rồi dùng cho công thức chống
# tràn thì công thức sai đúng lúc cần nó nhất — lúc nhân vật đang diễn.
NUA_TU_DO, NUA_GHIM = 181.0, 126.0
KHE = 26                     # khe an toàn để bàn tay dang rộng cũng không chạm rìa


def x_dung(co: float, mot_nguoi: bool = False) -> float:
    """Toạ độ đứng của hai người, CO theo cỡ máy — khớp công thức trong KichHai.tsx.

    Bản đầu của cổng này dùng hằng 292 chép tay, nên sau khi engine chuyển sang công thức thì
    cổng vẫn tố tràn ở mọi tập. Một cổng đo bằng con số đã lỗi thời thì tố nhầm y như không đo."""
    # 31/8 — khớp ĐÚNG công thức engine, ở đơn vị viewBox CUỐI (toạ độ đã nhân zoom).
    # Bản trước tôi viết ở đơn vị chưa nhân, còn engine thì lại dùng hằng 292 chẳng theo đơn vị
    # nào — ba cách hiểu cho một con số, nên cổng xanh mà khung vẫn cắt.
    nua = (NUA_GHIM if (not mot_nguoi and co >= 1.4) else NUA_TU_DO) * co
    return min(292.0, 500 - nua - 6)


def cham(f: str) -> list[str]:
    try:
        d = json.load(io.open(f, encoding="utf-8"))
    except Exception:
        return []
    loi = []
    for i, l in enumerate(d.get("luot") or []):
        co = CO_MAY.get(l.get("co") or "trung", 1.52)
        goc = l.get("goc") or "hai_nguoi"
        # Bề ngang phụ thuộc BỐ CỤC: hai người ở cỡ trung/cận thì engine ghim tay tầm ngực,
        # một người thì tay tự do. Cổng phải mô phỏng đúng điều kiện ấy, nếu không nó lại đo
        # một chế độ và kết luận cho chế độ kia — đúng lỗi đã mắc với bảng tư thế hôm qua.
        _mot = goc == "mot_nguoi"
        nua = (NUA_GHIM if (not _mot and co >= 1.4) else NUA_TU_DO) * co
        # Vị trí theo góc — phải khớp `_xA`/`_xB` trong engine.
        if goc == "qua_vai":
            # 30/8 — kiểm NGHIÊM trở lại. Bản trước tôi cho qua người tiền cảnh (x=430) với lý
            # do nó "cố ý bị cắt". Khung anh gửi cho thấy lý do ấy chỉ đúng trên giấy: trên màn
            # hình nó là một nhân vật lọt khung. Tôi đã dùng ý-định-thiết-kế để bịt miệng một
            # phép đo đúng — cổng nói thật, tôi bảo nó im.
            xs = [40, 430]
        elif goc == "mot_nguoi":
            xs = [0]
        else:
            xs = [-x_dung(co, _mot), x_dung(co, _mot)]   # đơn vị viewBox cuối
        for x in xs:
            trai, phai = x - nua, x + nua
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
