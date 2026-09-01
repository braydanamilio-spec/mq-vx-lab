#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CỔNG GIAO HÀNG — mỗi video dựng ra phải đi được tới khâu đăng (1/9/2026)

Anh: *"fix tất cả lần sao cho thông minh"*. Thông minh ở đây không phải sửa nhiều chỗ, mà là
tìm chỗ nào một video **dựng xong rồi nằm lại**.

Tìm ra một chỗ như thế: **bản dài**. `v3L_bankrun.mp4` và `v5L_techsupport.mp4` dựng xong mà
không có `.tai.json`, nên `day_kho.py` bỏ qua — bản dài chính là chỗ bật quảng cáo giữa video,
tức nguồn tiền chính, và nó không bao giờ tới được khâu đăng.

Vì sao lọt: workflow CÓ gọi `sieu_du_lieu --long`, nhưng bản thân pipeline dài thì không. Ai
chạy tay là ra video câm. Nay bước sinh chữ dính liền bước dựng, và cổng này canh kết quả.

Kiểm hai điều, đo trên TỆP THẬT chứ không đọc mã:
  1. mọi `.mp4` trong `out/` đều có `.tai.json` đi kèm;
  2. mọi pipeline dựng ra mp4 đều có gọi sinh chữ đăng — bắt được trước cả khi có tệp.
"""
import glob
import io
import os
import re

GOC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(GOC, "out")
# tệp dựng mp4 -> có phải sinh chữ đăng không (bản nháp/thử thì không bắt)
PIPELINE = ["kich_comic.py", "kich_comic_long.py", "kich_v2.py", "kich_v2_long.py"]


def main() -> int:
    loi = []

    # ── 1. tệp thật ──────────────────────────────────────────────────────────────────────
    # Soi ĐÚNG những tiền tố `day_kho.py` thật sự đẩy — đọc thẳng từ nó, không viết lại danh
    # sách. Bản đầu quét `v*.mp4` nên tố cả `v4_*` (engine hài CŨ đã bị v5 thay thế, không nằm
    # trong đường giao hàng nào). Cổng tố oan thì người ta tắt cổng.
    mau = ["v3_*.mp4", "v3L_*.mp4", "v5_*.mp4", "v5L_*.mp4"]
    try:
        dk = io.open(os.path.join(GOC, "day_kho.py"), encoding="utf-8").read()
        m = re.search(r'--mau",\s*default="([^"]+)"', dk)
        if m:
            mau = [x.strip() for x in m.group(1).split(",")]
    except Exception:
        pass
    ds = [f for m2 in mau for f in glob.glob(os.path.join(OUT, m2))]
    thieu = []
    for f in sorted(ds):
        if not os.path.exists(f[:-4] + ".tai.json"):
            thieu.append(os.path.basename(f))
    if thieu:
        loi.append(f"{len(thieu)} video KHÔNG có chữ đăng -> `day_kho.py` sẽ bỏ qua, chúng nằm "
                   f"lại vĩnh viễn: {', '.join(thieu[:6])}" + ("…" if len(thieu) > 6 else ""))
    else:
        print(f"  ✅ {len(ds)}/{len(ds)} video trong đường giao hàng đều có chữ đăng "
              f"({' '.join(mau)})")

    # ── 2. mã nguồn ──────────────────────────────────────────────────────────────────────
    for t in PIPELINE:
        p = os.path.join(GOC, t)
        if not os.path.exists(p):
            continue
        s = io.open(p, encoding="utf-8").read()
        if "sieu_du_lieu" not in s:
            loi.append(f"{t}: dựng ra mp4 mà không gọi sinh chữ đăng — video sẽ không đăng được")
        else:
            print(f"  ✅ {t:22s} có gọi sinh chữ đăng")

    if loi:
        print("\n❌ " + "\n❌ ".join(loi))
        return 1
    print("\n✅ mọi video dựng ra đều đi được tới khâu đăng")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
