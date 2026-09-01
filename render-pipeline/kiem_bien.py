#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CỔNG BIẾN MÔI TRƯỜNG — workflow khai biến nào thì phải có mã ĐỌC biến ấy (1/9/2026)

Ba workflow render đều khai `CF_KEYS: ${{ secrets.CF_KEYS }}` và `GEMINI_KEYS: ...`. Nhìn vào
thì tưởng đã có đường lấy khoá dự phòng, không phụ thuộc Firestore. Sự thật: **không dòng mã
nào đọc hai biến ấy**, và secret cũng chưa từng tồn tại.

Hậu quả kéo dài nhiều tuần: trên CI khoá AI chỉ đến từ hồ Firestore, nên Firestore cạn lượt
đọc là cả nhà máy đứng — mà mỗi lần chẩn lại nhìn thấy dòng `CF_KEYS` trong workflow rồi kết
luận "đường dự phòng có rồi, chắc lỗi chỗ khác".

**Hàng rào giả nguy hơn không có hàng rào: nó làm người ta thôi đi tìm.**

Cổng này đối chiếu biến workflow khai với biến mã thật sự đọc.
"""
import io
import os
import re

GOC = os.path.dirname(os.path.abspath(__file__))
WF = os.path.join(GOC, "..", ".github", "workflows")

# Biến do runner/hành động dựng sẵn hoặc thư viện ngoài đọc — không phải mã của mình.
BO_QUA = {
    "GOOGLE_APPLICATION_CREDENTIALS", "GITHUB_TOKEN", "GH_TOKEN", "PYTHONUNBUFFERED",
    "NODE_OPTIONS", "CI", "TZ", "LANG", "PATH", "HOME", "REMOTION_", "AWS_",
}


def main() -> int:
    ma = ""
    for t in os.listdir(GOC):
        if t.endswith(".py"):
            ma += io.open(os.path.join(GOC, t), encoding="utf-8", errors="ignore").read()

    loi = []
    for w in sorted(os.listdir(WF)):
        if not w.endswith((".yml", ".yaml")):
            continue
        y = io.open(os.path.join(WF, w), encoding="utf-8").read()
        if not re.search(r"python (kich_\w+|duyet_lo|chuan_bi_nen)", y):
            continue          # chỉ soi workflow RENDER
        khai = set(re.findall(r"^\s{6,}([A-Z][A-Z0-9_]{2,}):\s*\$\{\{\s*secrets\.", y, re.M))
        thua = sorted(x for x in khai
                      if not any(x.startswith(b) or x == b for b in BO_QUA)
                      and f'"{x}"' not in ma and f"'{x}'" not in ma)
        if thua:
            loi.append(f"{w}: khai {' · '.join(thua)} nhưng KHÔNG mã nào đọc — hàng rào giả")
        else:
            print(f"  ✅ {w:28s} {len(khai)} biến, đều có mã đọc")

    if loi:
        print("\n❌ " + "\n❌ ".join(loi))
        return 1
    print("\n✅ mọi biến workflow khai đều có mã đọc thật")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
