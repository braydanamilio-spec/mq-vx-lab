#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dựng THỬ một tập kênh "vì sao" qua ĐÚNG đường mà `pilot_hai` chạy.

Không viết đường dựng thứ hai: đăng ký bộ sinh mới vào `giai_thich.BO_SINH` rồi gọi
`pilot_hai.mot_tap` như thường. Nhờ vậy tập thử đi qua TOÀN BỘ dây chuyền thật — vai chuyên
gia, ngữ điệu, luân phiên, cổng số bịa, trang phục, kho nền, ảnh bìa — và cái gì hỏng thì
hỏng ở đúng chỗ nó sẽ hỏng khi chạy thật (§15.10).
"""
import sys

import chu_de as C
import giai_thich as G
import khung_hoi as K

CHU_THE = sys.argv[1] if len(sys.argv) > 1 else "Kodak"
KENH = sys.argv[2] if len(sys.argv) > 2 else "therules"
I_KHUON = int(sys.argv[3]) if len(sys.argv) > 3 else 2

_kn = K.KHUNG["vanished"]
_ho = C.ho_so(CHU_THE)
_r = K.nhip_tu_khuon(_kn["khuon"][I_KHUON], CHU_THE.split(" (")[0], _ho,
                     G._n, G._ve, _kn["tu_khoa"])
if not _r:
    print(f"   ⏭ {CHU_THE}: không đủ tư liệu đúng chủ đề -> BỎ CẶP (đúng hành vi)")
    raise SystemExit(1)

G.BO_SINH[KENH] = lambda i, _r=_r: _r
print(f"   ▶ {_r[0]}")

import pilot_hai as P                                   # noqa: E402  (sau khi đã đăng ký)
P.MOT_GIONG = True          # MỘT chuyên gia nói liên tục, hình đổi theo lời
P.DAO_CU_TAP = C.hinh_mau(_ho)      # hình mẫu suy từ chủ thể, dùng cho cả tập
print(f"   🎨 hình mẫu: {P.DAO_CU_TAP or '(không nhận ra)'}")
raise SystemExit(0 if P.mot_tap(KENH, 4, False) else 1)
