#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""XUẤT BỘ NHẬN DIỆN V4 — đủ cỡ YouTube / Facebook / Instagram / X, 0 quota (27/8/2026).

VÌ SAO CÓ TỆP NÀY THAY VÌ SỬA `xuat_brandkit.py`
------------------------------------------------
Bản cũ gọi composition `BrandKit2` và chỉ truyền đúng MỘT màu (`accent = palette.primary`), bỏ
qua cả bảng 5 màu, và không truyền `font`. Nên 50 kênh ra 50 ảnh cùng khuôn cùng phông — đúng
thứ đã bị bác. V4 truyền cả `palette` và `font`; `NhanV4.tsx` tự bốc bố cục/chất nền từ băm tên.

    python xuat_nhan_v4.py --mau 6        # 6 kênh trải đều, để soi trước
    python xuat_nhan_v4.py --tat-ca       # cả 50
    python xuat_nhan_v4.py --tat-ca --co avatar_800,cover_2560x1440
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

GOC = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(GOC, "..", "engine-remotion")
DS = os.path.join(GOC, "kenh_the_he_2.json")
RA = os.path.join(GOC, "..", "MM0-AutoPublisher", "dashboard", "brand")

# (khoá `kind` trong CO_BRAND của Root.tsx, hậu tố tên tệp)
# Cỡ theo đúng khuyến nghị từng nền tảng — xem BRAND_KIT.md mục 2:
#   YouTube  avatar 800×800 (cắt tròn, hiện 48px trên điện thoại) · cover 2560×1440 (an toàn 1546×423)
#   Facebook avatar 500×500 (cắt tròn)                            · cover 1640×624 (= 820×312 ×2)
#   Instagram avatar 640×640 (hiện 320)                           · bài vuông 1080×1080
#   X        header 1500×500
CO = [("avatar", "avatar_800"), ("banner", "cover_2560x1440"), ("watermark", "watermark_150"),
      ("fb_avatar", "fb_avatar_500"), ("fb_cover", "fb_cover_1640x624"),
      ("ig_avatar", "ig_avatar_640"), ("ig_post", "ig_post_1080"),
      ("x_header", "x_header_1500x500")]


def _ten_tep(k: dict) -> str:
    """Khoá tệp = tên kênh viết liền in hoa — TRÙNG với khoá kênh dùng khắp pipeline.

    Không dùng handle: handle có thể đổi (kênh bị trùng tay cầm thì phải thêm hậu tố), mà đổi
    handle không được làm chết mọi đường dẫn ảnh đã nhúng trong dashboard."""
    return str(k["ten"]).replace(" ", "").upper()


def mot_anh(k: dict, kind: str, hau_to: str, ban: int) -> tuple[str, str]:
    b = k.get("brand") or {}
    nen = _ten_tep(k)
    out = os.path.join(RA, f"{nen}_{hau_to}.png")
    props = json.dumps({
        "kind": kind, "name": b.get("name") or k["ten"], "tagline": b.get("tagline", ""),
        "handle": b.get("handle", ""), "motif": b.get("motif", "bars"),
        "font": b.get("font", ""), "palette": b.get("palette") or {},
    }, ensure_ascii=False)
    r = subprocess.run(["npx", "remotion", "still", "src/index.ts", "NhanKit", out,
                        f"--props={props}", "--log=error", "--gl=swiftshader"],
                       cwd=ENG, capture_output=True, text=True, timeout=420)
    if r.returncode or not os.path.exists(out):
        return "", f"{nen}/{hau_to}: {(r.stderr or r.stdout or '')[-200:]}"
    return out, ""


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tat-ca", action="store_true")
    ap.add_argument("--mau", type=int, default=0, help="lấy N kênh trải đều để soi trước")
    ap.add_argument("--co", default="", help="chỉ xuất các hậu tố này, cách nhau bằng dấu phẩy")
    ap.add_argument("--ban", type=int, default=4)
    ap.add_argument("--luong", type=int, default=4)
    a = ap.parse_args()

    ks = json.load(io.open(DS, encoding="utf-8"))
    ks = ks if isinstance(ks, list) else list(ks.values())
    if a.mau:
        buoc = max(1, len(ks) // a.mau)
        ks = ks[::buoc][:a.mau]
    elif not a.tat_ca:
        print("❌ cần --tat-ca hoặc --mau N")
        return 2
    co = CO if not a.co else [c for c in CO if c[1] in a.co.split(",")]
    os.makedirs(RA, exist_ok=True)

    viec = [(k, kind, ht) for k in ks for kind, ht in co]
    ok, loi = 0, []
    with ThreadPoolExecutor(max_workers=a.luong) as ex:
        fs = {ex.submit(mot_anh, k, kind, ht, a.ban): (k, ht) for k, kind, ht in viec}
        for i, f in enumerate(as_completed(fs), 1):
            p, e = f.result()
            if p:
                ok += 1
            else:
                loi.append(e)
            if i % 25 == 0 or i == len(viec):
                print(f"   … {i}/{len(viec)} ảnh · ok={ok} lỗi={len(loi)}", flush=True)
    for e in loi[:6]:
        print(f"   ❌ {e}")
    print(f"\n{'✅' if not loi else '⚠️'} {ok}/{len(viec)} ảnh · {len(ks)} kênh · {RA}")
    return 0 if not loi else 1


if __name__ == "__main__":
    sys.exit(main())
