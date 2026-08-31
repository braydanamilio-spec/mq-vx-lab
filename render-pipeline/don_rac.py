#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DỌN RÁC TRONG public/ — quét theo THAM CHIẾU, không quét theo thư mục (31/8/2026)

Anh: *"thế dọn a nếu là tích tụ ko dùng nha."*

`engine-remotion/public` đang 104 GB, và toàn bộ nằm ngoài git (`.gitignore` có
`engine-remotion/public/**`), nên nó không ảnh hưởng gì tới hệ chạy trên GitHub — đó là rác
tích lại từ những lần dựng ở máy.

NHƯNG không được xoá theo thư mục. Ba lý do, xếp theo mức đắt:

  1. Trong đó có ẢNH AI đã tốn hạn mức để sinh. Xoá rồi sinh lại là trả tiền hai lần cho cùng
     một tấm ảnh.
  2. Nhạc nền (`music/`) nằm trong git và đang được cả bộ comic dùng — xoá là hỏng mọi video.
  3. `story/` và các thư mục `*_cine/` vẫn được `content_brain.py`, `run_render.py`,
     `nghiem_thu.py` đọc khi dựng 60 kênh phân tích.

Nên cách duy nhất đúng: lập danh sách tệp CÒN ĐƯỢC THAM CHIẾU (mọi `.json` props trong `out/`
và trong chính `public/` đều ghi tên tệp mà video cần), rồi coi phần còn lại là ứng viên — và
vẫn phải đủ CŨ mới xoá, phòng trường hợp một tiến trình đang dựng dở.

Mặc định chỉ LIỆT KÊ. Muốn xoá thật thì thêm `--xoa`.
"""
import os
import io
import re
import json
import time
import argparse

GOC = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(GOC, "..", "engine-remotion", "public")
OUT = os.path.join(GOC, "out")

# Không bao giờ đụng, bất kể tham chiếu: nhạc nằm trong git và cả bộ comic dùng; `img/` là ảnh
# dự phòng; `_canary` là mốc kiểm tra của hệ.
GIU = ("music/", "img/", "_canary", "fonts/")


def _tep_duoc_nhac(thu_muc: str) -> set:
    """Mọi tên tệp xuất hiện trong bất kỳ .json nào — đó là tệp còn có người dùng."""
    ra = set()
    for goc, _, ts in os.walk(thu_muc):
        for t in ts:
            if not t.endswith(".json"):
                continue
            try:
                noi_dung = io.open(os.path.join(goc, t), encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            # bắt mọi chuỗi trông như đường dẫn tệp media trong props
            for m in re.finditer(r'"([^"]+\.(?:mp3|mp4|jpg|jpeg|png|webp|svg))"', noi_dung):
                ra.add(m.group(1).lstrip("./"))
                ra.add(os.path.basename(m.group(1)))
    return ra


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xoa", action="store_true", help="xoá thật (mặc định chỉ liệt kê)")
    ap.add_argument("--ngay", type=int, default=14, help="chỉ xét tệp cũ hơn N ngày")
    a = ap.parse_args()

    if not os.path.isdir(PUB):
        print("❌ không thấy public/")
        return 2

    print("→ quét tham chiếu trong out/ và public/ …", flush=True)
    dung = _tep_duoc_nhac(OUT) | _tep_duoc_nhac(PUB)
    print(f"   {len(dung)} tên tệp còn được nhắc tới trong các props")

    nguong = time.time() - a.ngay * 86400
    rac, tong = [], 0
    for goc, _, ts in os.walk(PUB):
        for t in ts:
            d = os.path.join(goc, t)
            rel = os.path.relpath(d, PUB)
            if any(rel.startswith(g) for g in GIU):
                continue
            if t in dung or rel in dung:
                continue
            try:
                st = os.stat(d)
            except OSError:
                continue
            if st.st_mtime > nguong:            # còn mới -> có thể đang dựng dở
                continue
            rac.append((d, st.st_size))
            tong += st.st_size

    print(f"\n   ứng viên rác: {len(rac)} tệp · {tong/1e9:.1f} GB "
          f"(không tham chiếu, cũ hơn {a.ngay} ngày)")
    # bảng theo thư mục cấp 1, để nhìn ra ngay có gì bất thường trước khi xoá
    theo = {}
    for d, sz in rac:
        k = os.path.relpath(d, PUB).split(os.sep)[0]
        theo[k] = theo.get(k, [0, 0])
        theo[k][0] += 1
        theo[k][1] += sz
    for k, (n, sz) in sorted(theo.items(), key=lambda x: -x[1][1])[:14]:
        print(f"     {sz/1e9:6.2f} GB  {n:6d} tệp  {k[:56]}")

    # Ghi danh sách RA TỆP trước khi xoá, luôn luôn — kể cả khi chỉ liệt kê. Xoá 26 GB mà
    # không còn dấu vết đã xoá gì là thứ không sửa lại được; một tệp văn bản vài trăm KB thì
    # rẻ hơn nhiều so với việc phải đoán.
    nk = os.path.join(GOC, "out", "da_don.txt")
    os.makedirs(os.path.dirname(nk), exist_ok=True)
    with io.open(nk, "w", encoding="utf-8") as f:
        for d, sz in rac:
            f.write(f"{sz}\t{os.path.relpath(d, PUB)}\n")
    print(f"   danh sách ghi ở: out/da_don.txt")

    if not a.xoa:
        print("\n   (chỉ liệt kê — thêm --xoa để xoá thật)")
        return 0

    xong = 0
    for d, sz in rac:
        try:
            os.remove(d)
            xong += sz
        except OSError:
            pass
    print(f"\n✅ đã xoá {xong/1e9:.1f} GB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
