#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QUY MỘT ĐIỂM (kinh độ, vĩ độ) VỀ ĐÚNG TÊN BANG MỸ (28/8/2026).

VÌ SAO CÓ TỆP NÀY
-----------------
Soi khung thật của SKY RIGHT NOW: bản đồ là một mảng navy phẳng, KHÔNG bang nào sáng lên, trong
khi tiêu đề nói "200 planes are over California right now". Bới ra thì `_bd_may_bay` gom máy bay
theo NƯỚC ĐĂNG KÝ ("United States: 192", "Canada: 5"), còn `MappedShort.tsx` khớp `d.state` với
TÊN BANG MỸ. Không tên nào khớp -> mọi bang rỗng -> bản đồ đen. Một video dạng "bản đồ" mà không
map được gì — và cổng chấm điểm không bắt được, vì dữ liệu vẫn "hợp lệ", chỉ là sai loại.

OpenSky VỐN trả `kinh_do`/`vi_do` từng chiếc. Dữ liệu để vẽ đúng vẫn luôn ở đó, chỉ là bị vứt.

VÌ SAO ĐA GIÁC CHỨ KHÔNG PHẢI KHUNG CHỮ NHẬT
--------------------------------------------
Bản đầu dùng khung chữ nhật từng bang, chọn bang có tâm gần nhất khi nhiều khung cùng phủ. Đo thử
thì Manhattan (-73.9, 40.7) ra **New Jersey** — khung NJ nhỏ hơn nên tâm gần hơn, dù điểm nằm hẳn
trong New York. Sai ở đúng vùng đông máy bay nhất nước Mỹ thì cả bản đồ sai theo.
Nên dùng đa giác thật + phép đếm giao điểm. Khung chữ nhật vẫn giữ, nhưng chỉ để LỌC NHANH.

Đa giác sinh thẳng từ `engine-remotion/public/geo/states-10m.json` — ĐÚNG tệp composition dùng để
vẽ — nên tên bang khớp tuyệt đối, không có chuyện "D.C." với "District of Columbia". Đã giản lược
Douglas-Peucker ở ngưỡng 0.02° (~2km): thừa chính xác cho việc quy điểm, mà gọn còn 145KB.
"""
from __future__ import annotations

import io
import json
import os

_GOC = os.path.dirname(os.path.abspath(__file__))

# {tên bang: [vành ngoài, ...]} — bang có nhiều đảo thì nhiều vành.
VANH: dict = json.load(io.open(os.path.join(_GOC, "bang_my.json"), encoding="utf-8"))

# Khung bao mỗi vành, dựng sẵn một lần: [(tên, tây, nam, đông, bắc, vành)]
_KHUNG = []
for _ten, _vs in VANH.items():
    for _v in _vs:
        _xs = [p[0] for p in _v]
        _ys = [p[1] for p in _v]
        _KHUNG.append((_ten, min(_xs), min(_ys), max(_xs), max(_ys), _v))


def _trong_vanh(x: float, y: float, vanh: list) -> bool:
    """Phép đếm giao điểm (ray casting) — bắn tia ngang sang phải, lẻ lần cắt = ở trong."""
    trong = False
    n = len(vanh)
    j = n - 1
    for i in range(n):
        xi, yi = vanh[i]
        xj, yj = vanh[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            trong = not trong
        j = i
    return trong


def bang_cua(kinh_do, vi_do):
    """Tên bang chứa điểm này — hoặc None nếu điểm không nằm trên đất Mỹ.

    Trả None là CÂU TRẢ LỜI ĐÚNG cho máy bay trên vịnh Mexico hay Đại Tây Dương, không phải lỗi.
    Người gọi bỏ qua chúng: một bản đồ 'máy bay trên bang nào' không có chỗ cho máy bay ngoài khơi,
    và gán bừa cho bang gần nhất là bịa số liệu."""
    try:
        x, y = float(kinh_do), float(vi_do)
    except (TypeError, ValueError):
        return None
    for ten, t, n, d, b, vanh in _KHUNG:
        if t <= x <= d and n <= y <= b and _trong_vanh(x, y, vanh):
            return ten
    return None
