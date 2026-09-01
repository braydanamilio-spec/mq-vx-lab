#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG BIỂU TƯỢNG — mọi hình được GÁN phải có trong engine, và không hình nào gánh quá nhiều.

── VÌ SAO (1/9/2026) ───────────────────────────────────────────────────────────────────────
Hai lỗi cùng một ngày, cùng một gốc: **bộ hình được chốt TRƯỚC bảng nội dung**.

  · brand kit: 17 hình cho 18 kênh -> THE ODDS ra ngôi sao, YEARS ra giọt nước
  · bộ giải thích: 13 hình cho mọi bảng -> "a school bus" ra ô tô con, "a red blood cell" ra
    hình NGƯỜI, "a single atom" ra quả địa cầu, "a blue whale" ra cái cây

Không lỗi nào báo: hình vẫn vẽ ra, chỉ là nó nói sai chuyện. Và ngay khi đang sửa, tôi gán
`dan_piano` cho cây đàn mà quên vẽ hình ấy — nếu không kiểm thì nó lặng lẽ rơi về hình mặc định.

Cổng này hỏi hai câu:
  1. Hình nào được gán mà engine KHÔNG có?  (lỗi chặn — rơi về mặc định trong im lặng)
  2. Hình nào đang gánh quá nhiều nội dung khác nhau?  (cảnh báo — dấu hiệu bộ hình sắp hết chỗ)
"""
import collections
import io
import os
import re
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
TSX = os.path.join(os.path.dirname(GOC), "engine-remotion", "src", "gt", "Khuon.tsx")
TRAN_GANH = 8          # một hình gánh hơn 8 nội dung khác nhau là dấu hiệu thiếu hình


def _hinh_duoc_gan():
    """Mọi tên hình THẬT SỰ được gán — đọc từ chỗ KHAI, không đoán theo hình dạng chuỗi.

    Bản đầu của cổng này quét mọi ô chuỗi trong mọi bảng rồi ĐOÁN ô nào là tên hình (có gạch
    dưới? trùng tiền tố?). Đoán thì lúc bắt lúc không — tức một hàng rào giả, thứ còn nguy hơn
    không có hàng rào, vì nó làm người ta thôi đi tìm. Ở đây đọc đúng hai nơi hình được khai:
    đối số `bt=` / khoá `"bt":` trong mã, và CỘT CUỐI của các bảng hằng. Cả hai đều là mã hoặc
    vị trí cố định, nên không lẫn được với một chuỗi nội dung tiếng Anh.
    """
    src = io.open(os.path.join(GOC, "giai_thich.py"), encoding="utf-8").read()
    ra = collections.Counter()
    for m in re.finditer(r'(?:bt\s*=\s*|"bt"\s*:\s*)"([a-z_]+)"', src):
        ra[m.group(1)] += 1
    sys.path.insert(0, GOC)
    import giai_thich as G
    for ten in dir(G):
        if not ten.isupper():
            continue
        b = getattr(G, ten)
        if not isinstance(b, (list, tuple)) or not b or not isinstance(b[0], (list, tuple)):
            continue
        for row in b:
            x = row[-1]
            if isinstance(x, str) and re.fullmatch(r"[a-z][a-z_]{2,}", x):
                ra[x] += 1
    return ra


def main() -> int:
    co = set(re.findall(r'case "([a-z_]+)":', io.open(TSX, encoding="utf-8").read()))
    gan = _hinh_duoc_gan()
    print(f"  engine có {len(co)} hình · bảng dữ liệu gán {len(gan)} tên")

    thieu = sorted(k for k in gan if k not in co)
    if thieu:
        print(f"  ❌ gán {len(thieu)} hình mà engine KHÔNG có: {', '.join(thieu)}")
        print("     -> mỗi chỗ ấy rơi về hình mặc định, và không có lỗi nào báo")
        return 1
    print("  ✅ mọi hình được gán đều có trong engine")

    thua = sorted(c for c in co if c not in gan)
    if thua:
        print(f"  ℹ {len(thua)} hình engine có mà chưa dùng: {', '.join(thua[:8])}")

    qua = [(k, v) for k, v in gan.items() if v > TRAN_GANH]
    for k, v in sorted(qua, key=lambda x: -x[1]):
        print(f"  ⚠ `{k}` gánh {v} chỗ — gánh quá nhiều thì biểu tượng nói chung chung")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
