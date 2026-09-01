#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CỔNG 18+2 — tổng job render không bao giờ được vượt 18 (1/9/2026)

Anh: *"bữa kêu là chỉ chạy 18 luồng còn 2 luồng để điều phối mà sao ko ghi rule vào"*.

Trần đồng thời của tài khoản Free là **20 job cho CẢ tài khoản**, không phải cho mỗi workflow.
Hai luồng cuối phải để trống cho các workflow ĐIỀU PHỐI: `publish.yml` (mỗi 30 phút),
`publish_social.yml`, `health_guardian.yml`, `thumb_requests.yml`. Chúng bị xếp hàng thì
dashboard đứng hình và video dựng xong không được đăng — tức cả dây chuyền tắc ở khâu cuối.

Luật này từng chỉ nằm trong đầu, nên khi thêm workflow comic 10 luồng và chạy cùng lúc với 18
luồng phân tích thì thành 28 job. Luật không có cơ chế thì không phải luật.

Cổng kiểm hai điều:
  1. mỗi workflow render có `max-parallel` ≤ 18;
  2. các workflow render dùng CHUNG một `concurrency group` — có thế thì hai xưởng mới không
     bao giờ chạy chồng nhau, và tổng job render mới bị chặn ở 18.
"""
import io
import os
import re

GOC = os.path.dirname(os.path.abspath(__file__))
WF = os.path.join(GOC, "..", ".github", "workflows")
TRAN = 18          # 20 của tài khoản, chừa 2 cho điều phối


def main() -> int:
    loi, thay = [], []
    nhom = {}
    for t in sorted(os.listdir(WF)):
        if not t.endswith((".yml", ".yaml")):
            continue
        s = io.open(os.path.join(WF, t), encoding="utf-8").read()
        # workflow RENDER = có gọi một pipeline dựng video
        if not re.search(r"python (kich_\w+|duyet_lo)\.py", s):
            continue
        mp = re.search(r"max-parallel:\s*(\d+)", s)
        n = int(mp.group(1)) if mp else 1
        g = re.search(r"concurrency:.*?group:\s*([\w-]+)", s, re.S)
        g = g.group(1) if g else "(không có)"
        thay.append((t, n, g))
        nhom.setdefault(g, []).append(t)
        if n > TRAN:
            loi.append(f"{t}: max-parallel {n} > {TRAN} — chiếm hết luồng điều phối")

    for t, n, g in thay:
        print(f"  {t:28s} max-parallel={n:<3d} group={g}")

    if len(nhom) > 1:
        loi.append("các xưởng render KHÔNG dùng chung concurrency group: "
                   + " · ".join(f"{g}({len(v)})" for g, v in nhom.items())
                   + " — hai xưởng chạy chồng là vượt trần 20 job")

    if loi:
        print("\n❌ " + "\n❌ ".join(loi))
        return 1
    tong = max((n for _t, n, _g in thay), default=0)
    print(f"\n✅ luật 18+2: tối đa {tong} job render cùng lúc, chừa {20 - tong} cho điều phối")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
