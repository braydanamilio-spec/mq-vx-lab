#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RÀ SOÁT CẢ KHO BẰNG CỔNG CHẤM CÚ CHỐT (31/8/2026)

`sinh_kich_ban.py --cham` chỉ chấm mẩu ĐANG sinh. Kho hiện có 221 mẩu, phần lớn được nhận vào
từ những mẻ trước khi cổng ấy tồn tại — nên nói "kịch bản đã qua cổng chấm" là nói quá: mới
có hai mẩu đi qua.

Tệp này chấm lại toàn bộ. KHÔNG xoá mẩu nào — chỉ ghi `diem_chot` vào từng mẩu, rồi
`kich_comic.py` bỏ qua mẩu dưới ngưỡng khi chọn. Xoá thì mất hẳn công sinh, mà một mẩu 5/10
vẫn có thể cứu được bằng cách viết lại câu cuối; đánh dấu thì giữ được đường lùi ấy.
"""
import os
import io
import json
import time
import argparse

from kich_hai import GOC
from sinh_kich_ban import cham_chot, KHO_TEP


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nguong", type=int, default=6)
    ap.add_argument("--lai", action="store_true", help="chấm lại cả mẩu đã có điểm")
    a = ap.parse_args()

    import the_he_2 as T2
    keys = T2.keys_cuc_bo() or None
    if not keys:
        print("❌ không có khoá AI")
        return 2

    kho = json.load(io.open(KHO_TEP, encoding="utf-8"))
    tong = sum(len(v) for v in kho["mau"].values())
    xong = yeu = bo = 0
    print(f"→ chấm {tong} mẩu, ngưỡng {a.nguong}/10 …", flush=True)

    for de, ds in kho["mau"].items():
        for i, m in enumerate(ds):
            if m.get("diem_chot") and not a.lai:
                bo += 1
                continue
            dat, diem, vs = cham_chot(m["loi"], keys, a.nguong)
            m["diem_chot"] = diem
            xong += 1
            if not dat:
                yeu += 1
                print(f"   ⚠️ {de}[{i}] {diem}/10 — {vs}", flush=True)
            # ghi sau MỖI mẩu: chấm 221 mẩu mất nửa tiếng, đứt giữa chừng mà mất hết thì
            # phải chạy lại từ đầu và tốn hạn mức lần nữa
            io.open(KHO_TEP, "w", encoding="utf-8").write(
                json.dumps(kho, ensure_ascii=False, indent=1))
            time.sleep(0.25)

    dat = sum(1 for ds in kho["mau"].values() for m in ds
              if (m.get("diem_chot") or 0) >= a.nguong)
    print(f"\n✅ chấm {xong} mẩu (bỏ qua {bo} đã có điểm) · {yeu} mẩu dưới ngưỡng")
    print(f"   kho dùng được: {dat}/{tong} mẩu ({dat/max(1,tong)*100:.0f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
