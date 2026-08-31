#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KIỂM MỘT KHUNG — dựng đúng 1 khung hình để bắt lỗi chỉ lộ lúc chạy. (30/8/2026)

VÌ SAO KHÔNG DÙNG CÁCH QUÉT MÃ
------------------------------
Lỗi `ReferenceError: Cannot access 'X' before initialization` đã nổ **năm lần** trong kho này,
và cả năm lần đều qua được `tsc` lẫn `esbuild` — mã hợp lệ về kiểu và cú pháp, chỉ sai THỨ TỰ.

Tôi viết một cổng quét mã bằng biểu thức chính quy để bắt nó. Nó báo **3.590 chỗ**, gần như toàn
phát hiện sai: tên biến ngắn khớp cả chữ trong chú thích tiếng Việt, trong chuỗi, trong tên khác
dài hơn. Biểu thức chính quy **không phân tích được phạm vi JavaScript** — muốn làm đúng phải có
một bộ phân tích thật, và viết bộ ấy để bắt một lớp lỗi thì đắt hơn giá trị nó mang lại.

Đây đúng luật 7ca tôi vừa ghi sáng nay: *cây thước mới viết chê nhầm nhiều hơn bắt đúng*. Và
lần này tôi mắc lại nó ngay trong ngày.

CÁCH ĐÚNG: DÙNG CHÍNH THỨ CHẠY THẬT
-----------------------------------
Remotion dựng được **một khung duy nhất**. TDZ nổ ở khung đầu tiên, nên một khung là đủ để bắt —
mất vài giây thay vì mười lăm phút của một lượt dựng đầy đủ, và **không có phát hiện sai nào**,
vì thứ kiểm chính là thứ sẽ chạy.

Bài học chung: khi một lớp lỗi chỉ lộ lúc chạy, đừng dựng công cụ đoán nó từ mã nguồn — hãy tìm
cách CHẠY THẬT nhưng rẻ.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(os.path.dirname(GOC), "engine-remotion")


def thu(comp: str, props: str) -> tuple[bool, str]:
    """Dựng 1 khung. Trả (lành, thông báo lỗi)."""
    ra = os.path.join(GOC, "out", "_khung1.png")
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    r = subprocess.run(
        # 31/8 — RENDER KHUNG GIỮA, KHÔNG PHẢI KHUNG 0.
        # Cổng này vừa bỏ lọt một ReferenceError chết người (`props is not defined` trong nhánh
        # vẽ biểu đồ) và vẫn báo xanh. Vì khung 0 là lúc bài mới mở: chưa có biểu đồ, chưa có
        # thẻ số, nhân vật vừa vào — tức phần lớn code vẽ CHƯA từng chạy.
        # Một cổng chống lỗi lúc chạy mà chỉ chạy một phần code thì nó bảo vệ đúng phần ấy.
        # Khung 300 (giây thứ 10) là lúc mọi lớp đã có mặt: biểu đồ, thẻ số, phụ đề, nhân vật.
        ["npx", "remotion", "still", "src/index.ts", comp, ra, "--frame=300",
         f"--props=./{os.path.relpath(props, ENG)}", "--gl=swiftshader", "--log=error"],
        cwd=ENG, capture_output=True, text=True, timeout=600)
    if r.returncode == 0:
        return True, ""
    loi = [l for l in (r.stderr or "").splitlines()
           if any(k in l for k in ("Error", "error", "Cannot", "undefined"))]
    return False, (loi[0].strip() if loi else (r.stderr or "")[-200:])


def main() -> int:
    # Lấy props THẬT đã dựng gần nhất cho mỗi composition — props thật mới đi qua đúng những
    # nhánh mã mà một props giả không chạm tới.
    cap = [("KichHai", "v4_"), ("KichV2", "v3_")]
    xau = 0
    for comp, tien in cap:
        ds = sorted(f for f in os.listdir(os.path.join(GOC, "out"))
                    if f.startswith(tien) and f.endswith(".json"))
        if not ds:
            print(f"  ⏭ {comp}: chưa có props nào trong out/ — bỏ qua")
            continue
        p = os.path.join(GOC, "out", ds[0])
        lanh, msg = thu(comp, p)
        print(f"  {'✅' if lanh else '❌'} {comp:<10} ({ds[0]})" + ("" if lanh else f"\n       └ {msg}"))
        xau += 0 if lanh else 1
    return 1 if xau else 0


if __name__ == "__main__":
    sys.exit(main())
