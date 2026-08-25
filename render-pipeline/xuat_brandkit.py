#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""XUẤT 7 ASSET BRAND-KIT cho kênh thế hệ 2 — 0 quota, chỉ CPU (25/8/2026).

Cùng một thiết kế gốc (motif + bảng màu trong `kenh_the_he_2.json > brand`) render ra 7 cỡ đúng
chuẩn từng nền tảng, đặt tên theo `BRAND_KIT.md` mục 3 để khâu đăng tự nhận đúng file.

    python xuat_brandkit.py --kenh "GAME GRAVEYARD"     # 1 kênh
    python xuat_brandkit.py --tat-ca                    # cả 50 (nặng, nên chạy trên CI)
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(GOC, "..", "engine-remotion")
DS = os.path.join(GOC, "kenh_the_he_2.json")

# (khoá cỡ trong CO_BRAND của Root.tsx, hậu tố tên file theo BRAND_KIT.md)
ASSET = [("banner", "youtube_banner"), ("avatar", "youtube_avatar"), ("watermark", "watermark"),
         ("fb_cover", "fb_cover"), ("fb_avatar", "fb_avatar"), ("ig_avatar", "ig_avatar"),
         ("ig_story", "ig_story")]


def xuat_mot(k: dict, thu_muc: str, ban: int = 1) -> list[str]:
    b = k.get("brand") or {}
    if not b:
        print(f"   ⚠️ {k['ten']}: chưa sinh brand — chạy brandkit_the_he_2.py --sinh trước")
        return []
    ten_tep = k["handle"].lstrip("@").lower()
    d = os.path.join(thu_muc, ten_tep, "brand")
    os.makedirs(d, exist_ok=True)
    ra = []
    for kieu, hau_to in ASSET:
        out = os.path.join(d, f"{ten_tep}_{hau_to}_v{ban}.png")
        props = json.dumps({"kind": kieu, "name": b["name"], "tagline": b["tagline"],
                            "handle": b["handle"], "accent": b["palette"]["primary"],
                            "motif": b["motif"],
                            "layout": "left" if kieu in ("banner", "fb_cover") else "center"},
                           ensure_ascii=False)
        r = subprocess.run(["npx", "remotion", "still", "src/index.ts", "BrandKit2", out,
                            f"--props={props}", "--log=error"],
                           cwd=ENG, capture_output=True, text=True, timeout=300)
        if r.returncode or not os.path.exists(out):
            print(f"   ❌ {k['ten']} / {hau_to}: {(r.stderr or '')[-160:]}")
            continue
        ra.append(out)
    # bản mô tả/tag đi kèm — khâu đăng đọc thẳng file này
    js = os.path.join(d, f"{ten_tep}_brandkit.json")
    json.dump(b, io.open(js, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ra.append(js)
    return ra


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--tat-ca", action="store_true")
    ap.add_argument("--ra", default=os.path.join(GOC, "out", "brand"))
    a = ap.parse_args()
    ks = json.load(io.open(DS, encoding="utf-8"))
    chon = ks if a.tat_ca else [k for k in ks if k["ten"].upper() == a.kenh.upper()]
    if not chon:
        print("❌ không thấy kênh — dùng --kenh \"TÊN\" hoặc --tat-ca")
        return 2
    tong = 0
    for k in chon:
        f = xuat_mot(k, a.ra)
        tong += len(f)
        print(f"{'✅' if len(f) == 8 else '⚠️'} {k['ten']:20} {len(f)}/8 tệp · {k['brand']['motif']}")
    print(f"\n{tong} tệp trong {a.ra}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
