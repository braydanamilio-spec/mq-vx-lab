#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINH THẺ HOOK CHO 40 MẨU VIẾT TAY (31/8/2026)

Bốn mươi mẩu thoại viết tay có trước khi thẻ hook tồn tại, nên chúng không có trường `hook`.
Bản dự phòng — lấy sáu từ đầu của câu mở — cho ra một tấm thẻ LẶP LẠI đúng câu người xem đang
nghe, tức là không hook gì cả: nó không tạo câu hỏi nào, chỉ chiếm chỗ.

Sinh một lần cho cả bốn mươi mẩu, lưu vào `hook_tay.json`. Từ đó `kich_comic.py` đọc theo cặp
(chủ đề, số thứ tự mẩu).
"""
import os
import io
import json
import time

from kich_hai import KENH, KHO, GOC
from sinh_kich_ban import _hoi_ai, _doc_json

TEP = os.path.join(GOC, "hook_tay.json")


def main() -> int:
    import the_he_2 as T2
    keys = T2.keys_cuc_bo() or None
    if not keys:
        print("❌ không có khoá AI")
        return 2

    kho = {}
    if os.path.exists(TEP):
        kho = json.load(io.open(TEP, encoding="utf-8"))

    tong = moi = 0
    for k in KENH:
        de = k["de"]
        for i, mau in enumerate(KHO[de]):
            tong += 1
            khoa = f"{de}|{i}"
            if kho.get(khoa):
                continue
            thoai = "\n".join(f"{'AB'[c[1]]}: {c[0]}" for c in mau["loi"])
            hoi = (
                "Here is a short two-person comedy scene:\n\n" + thoai + "\n\n"
                "Write a HOOK CARD for it: 4 to 7 words, ALL CAPITALS, shown on screen for the "
                "first two seconds.\n"
                "- State the SITUATION, never the punchline. If it gives away the joke, nobody "
                "watches on.\n"
                "- It must create one specific question in the viewer's head.\n"
                "- No question marks, no emoji, no channel name, no quotation marks.\n"
                'Return STRICT JSON only: {"hook": "YOUR HOOK HERE"}'
            )
            t = _hoi_ai(hoi, keys)
            d = _doc_json(t) or {}
            hk = " ".join(str(d.get("hook", "")).split()).upper().strip('"')
            # Cùng cổng như bên `sinh_kich_ban`: đúng độ dài, và KHÔNG được trùng câu chốt.
            chot = set(mau["loi"][-1][0].lower().replace(".", "").split())
            if not (3 <= len(hk.split()) <= 8) or len(chot & set(hk.lower().split())) >= 3:
                print(f"   ↺ {de}[{i}] hook không đạt: {hk[:40]}")
                continue
            kho[khoa] = hk
            moi += 1
            print(f"   ✅ {de}[{i}] {hk}")
            io.open(TEP, "w", encoding="utf-8").write(json.dumps(kho, ensure_ascii=False, indent=1))
            time.sleep(0.3)

    print(f"\n✅ {len(kho)}/{tong} mẩu viết tay đã có thẻ hook (thêm {moi} lượt này)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
