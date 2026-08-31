#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CỔNG ÂM THANH — mỗi tệp nhạc phải có hệ số riêng, và bóng phải vẽ cho MỌI cảnh (31/8/2026)

Hai lỗi ở mục 22 của PIPELINE_RULES đều vô hình với mọi cổng đang có, vì không cái nào làm
render thất bại. Cổng này bắt đúng hai thứ ấy ở tầng mã nguồn:

  1. Mọi tệp trong bảng `NHAC` phải có số đo trong `music/am_luong.json`. Thiếu thì tệp ấy rơi
     về hằng 0.16 — tức là quay lại đúng lỗi cũ, lặng lẽ.
  2. `BongNguoi` phải được gọi NGOÀI nhánh `doiNguoi`. Bóng thuộc về người, không thuộc về số
     lượng người trong khung.
"""
import io
import json
import os
import re

GOC = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(GOC, "..", "engine-remotion", "public")
ENG = os.path.join(GOC, "..", "engine-remotion", "src", "comic", "KichComic.tsx")


def main() -> int:
    loi = []

    # ── 1. nhạc ──────────────────────────────────────────────────────────────────────────
    try:
        bang = json.load(io.open(os.path.join(PUB, "music", "am_luong.json"), encoding="utf-8"))
    except Exception:
        bang = {}
    s = io.open(os.path.join(GOC, "kich_comic.py"), encoding="utf-8").read()
    m = re.search(r"^NHAC\s*=\s*\{(.*?)\}", s, re.S | re.M)
    tep = re.findall(r'"(music/[^"]+)"', m.group(1)) if m else []
    thieu = [t for t in tep if os.path.basename(t) not in bang]
    if thieu:
        loi.append("thiếu số đo âm lượng: " + " · ".join(thieu) + "  (chạy `python3 can_nhac.py`)")
    else:
        hs = [bang[os.path.basename(t)] for t in tep]
        print(f"  ✅ {len(tep)} tệp nhạc đều có hệ số riêng "
              f"({min(hs):.3f} .. {max(hs):.3f} — hằng cũ dùng chung 0.16 cho tất cả)")

    # ── 2. bóng ──────────────────────────────────────────────────────────────────────────
    e = io.open(ENG, encoding="utf-8").read()
    goi = re.findall(r"^\s*(\{doiNguoi \? )?<BongNguoi", e, re.M)
    if not goi:
        loi.append("engine không gọi `BongNguoi` — nhân vật sẽ không có bóng")
    elif all(g for g in goi):
        loi.append("mọi lời gọi `BongNguoi` đều nằm trong nhánh `doiNguoi` — "
                   "cảnh một người sẽ không có bóng (mục 22.1)")
    else:
        print(f"  ✅ bóng vẽ cho cả cảnh một người ({len(goi)} lời gọi, "
              f"{sum(1 for g in goi if not g)} nằm ngoài nhánh `doiNguoi`)")

    # ── 3. mốc phát của nền tảng ─────────────────────────────────────────────────────────
    # YouTube/FB/IG chuẩn hoá về −14 LUFS và chỉ HẠ chứ không nâng. Cả BA đường dựng phải gọi
    # `chuan()` — đây chính là chỗ dễ tái phạm họ lỗi "vá một nhánh, để nguyên nhánh song song",
    # vì ba tệp này không dùng chung hàm dựng nào.
    thieu_chuan = [t for t in ("kich_comic.py", "kich_comic_long.py", "kich_v2.py")
                   if "chuan(out)" not in io.open(os.path.join(GOC, t), encoding="utf-8").read()]
    if thieu_chuan:
        loi.append("chưa chuẩn âm đầu ra: " + " · ".join(thieu_chuan) + "  (gọi `chuan(out)`)")
    else:
        print("  ✅ cả 3 đường dựng đều đưa âm lượng về −14 LUFS")

    if loi:
        print("\n❌ " + "\n❌ ".join(loi))
        return 1
    print("\n✅ âm lượng và bóng đều đúng luật")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
