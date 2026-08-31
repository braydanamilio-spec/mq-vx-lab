#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CỔNG MẶT SÀN — chặn đúng lỗi "đồ vật lơ lửng" tái diễn (31/8/2026)

Anh: *"cần có rule gì đó để ko cảnh nào lỗi."* Rule là: trong cả bộ engine comic chỉ được có
MỘT hằng mặt sàn (`SAN` trong `NoiChon.tsx`), và không tệp nào được tự viết một con số sàn
riêng. Ba lần trước đồ vật lơ lửng đều vì ba chỗ đặt ba số khác nhau — mà mỗi số đọc riêng ra
thì đều "trông hợp lý".

Cổng này grep tìm số sàn viết tay còn sót. Chạy trước mỗi lần dựng lô.
"""
import os
import re
import io
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
THU = os.path.join(GOC, "..", "engine-remotion", "src", "comic")
# 31/8 — bản đầu của cổng này tố oan ngay lượt chạy thứ nhất: nó bắt `vungChu.h * 0.86` (một
# phép tính CỠ CHỮ) và gọi đó là mức sàn. Đúng cái bẫy đã ghi ở mục 7E — cổng tự viết mà không
# thu hẹp thì sinh ra tám lời tố oan.
#
# Thu hẹp hai bước: `h` phải đứng RIÊNG (không phải `vungChu.h`, `AT.h`), và hệ số phải trong
# 0,90–0,99 — dải mà chỉ mặt sàn mới dùng tới.
NGHI = re.compile(r"(?<![.\w])h\s*\*\s*(0\.9[0-9])")


def main() -> int:
    xau = []
    for t in sorted(os.listdir(THU)):
        if not t.endswith(".tsx"):
            continue
        for i, dong in enumerate(io.open(os.path.join(THU, t), encoding="utf-8"), 1):
            if "SAN" in dong:                 # dùng hằng chung thì hợp lệ
                continue
            m = NGHI.search(dong)
            if m:
                xau.append((t, i, m.group(1), dong.strip()[:74]))

    if not xau:
        print("✅ mặt sàn: mọi vị trí đều dùng hằng SAN chung")
        return 0
    print(f"❌ {len(xau)} chỗ tự đặt mức sàn riêng — đây là nguồn của lỗi 'đồ vật lơ lửng':")
    for t, i, v, d in xau:
        print(f"   {t}:{i}  h*{v}   {d}")
    print("\n   Sửa: import { SAN } from './NoiChon' rồi dùng h * SAN.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
