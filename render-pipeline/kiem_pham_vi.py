#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG DỰNG + PHẠM VI — chạy CẢ HAI bộ kiểm, vì mỗi bên bắt thứ bên kia bỏ sót.  (1/9/2026)

── HAI BÀI HỌC NGƯỢC CHIỀU NHAU, CÙNG MỘT NGÀY ─────────────────────────────────────────────
CLAUDE.md §12.2 ghi: *`tsc --noEmit` xanh KHÔNG có nghĩa build được* — chú thích JSX đặt giữa
các thuộc tính làm `esbuild` chết trong khi `tsc` báo xanh. Từ đó tôi dùng `esbuild` làm cổng.

Chiều ngược lại cũng đúng, và hôm nay trả giá hai lần trong một phiên:
    ReferenceError  _samMau is not defined     (khai dưới chỗ dùng — vùng chết thời gian)
    ReferenceError  mauNhan is not defined     (khai trong component KHÁC với chỗ dùng)
Cả hai lần `esbuild` báo xanh, vì nó gói mã chứ không phân tích PHẠM VI. Cả hai lần chỉ vỡ ra
khi render thật — tức sau khi đã tốn một lượt dựng, và trên Actions thì tốn cả lượt chạy.

`tsc` bắt cả hai ngay: `error TS2304: Cannot find name 'mauNhan'`.

**Kết luận: không bộ nào một mình là cổng đủ.** `esbuild` canh cú pháp mà bộ dựng thật dùng;
`tsc` canh phạm vi và kiểu. Chạy cả hai tốn thêm vài giây và cắt hẳn một họ lỗi chỉ lộ ra lúc
render.
"""
import os
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(os.path.dirname(GOC), "engine-remotion")
THU_MUC = ["src/gt", "src/que"]          # bộ giải thích + bộ người que

TSC = ["--noEmit", "--jsx", "react-jsx", "--esModuleInterop", "--skipLibCheck",
       "--target", "es2020", "--moduleResolution", "bundler", "--module", "esnext"]


def _tep() -> list:
    ra = []
    for t in THU_MUC:
        d = os.path.join(ENG, t)
        if os.path.isdir(d):
            ra += [os.path.join(t, f) for f in sorted(os.listdir(d)) if f.endswith(".tsx")]
    return ra


def main() -> int:
    ds = _tep()
    if not ds:
        print("  ⏭ không có tệp .tsx nào để kiểm")
        return 0
    loi = 0

    # 1. esbuild — CÚ PHÁP mà bộ dựng thật (Remotion) dùng.
    r = subprocess.run(["npx", "esbuild", *ds, "--loader:.tsx=tsx",
                        "--outdir=" + os.path.join("/tmp", "_kpv"), "--log-level=error"],
                       cwd=ENG, capture_output=True, text=True)
    if r.returncode != 0:
        print("  ❌ esbuild:")
        print("     " + (r.stderr or "").strip()[:600].replace("\n", "\n     "))
        loi += 1
    else:
        print(f"  ✅ esbuild   {len(ds)} tệp — cú pháp bộ dựng thật nhận")

    # 2. tsc — PHẠM VI và KIỂU. Thứ esbuild không nhìn.
    tsc = os.path.join(ENG, "node_modules", ".bin", "tsc")
    if not os.path.exists(tsc):
        print("  ⚠ chưa cài typescript cục bộ — bỏ qua phần PHẠM VI (chạy `npm i -D typescript`)")
        print("    Không chặn ở đây, vì thiếu công cụ không phải lỗi của mã.")
        return 1 if loi else 0
    r2 = subprocess.run([tsc, *TSC, *ds], cwd=ENG, capture_output=True, text=True)
    ra = [l for l in (r2.stdout or "").splitlines()
          if "error TS" in l and any(l.startswith(t) for t in THU_MUC)]
    # Chỉ chặn ở lỗi PHẠM VI/tên (TS2304/TS2552/TS2448) — đó là họ lỗi đã thật sự làm chết render.
    # Lỗi kiểu khác để CẢNH BÁO: siết hết ngay sẽ đỏ vì các tệp cũ, và một cổng đỏ vĩnh viễn thì
    # người ta thôi đọc nó.
    chan = [l for l in ra if any(m in l for m in ("TS2304", "TS2552", "TS2448", "TS2454"))]
    if chan:
        print(f"  ❌ tsc — {len(chan)} lỗi PHẠM VI (biến dùng mà không thấy khai):")
        for l in chan[:6]:
            print("     " + l.strip()[:150])
        loi += 1
    else:
        print(f"  ✅ tsc       {len(ds)} tệp — không có biến nào dùng ngoài phạm vi")
        if ra:
            print(f"  ℹ {len(ra)} cảnh báo kiểu khác (không chặn)")
    return 1 if loi else 0


if __name__ == "__main__":
    raise SystemExit(main())
