#!/usr/bin/env python3
"""SINH BỘ NHẬN DIỆN 5 KÊNH HOẠT HÌNH — đúng cỡ chuẩn từng nền tảng (25/8/2026).

Vì sao render bằng Remotion chứ không nhờ AI vẽ: bộ nhận diện phải dùng CHÍNH nhân vật trong video.
Nhờ AI vẽ lại là ra một con vật khác (đúng bệnh drift đã giết concept cũ) — khán giả thấy avatar
một kiểu, mở video ra một kiểu, mất tin ngay giây đầu. Lấy thẳng PNG rig thì khớp 100%, mãi mãi.

CỠ CHUẨN (và vì sao)
  • avatar   800×800    — YouTube/FB/IG đều nhận; hiện ra chỉ 98px nên mặt phải TO, không có chữ
  • banner   2560×1440  — nhưng vùng an toàn trên điện thoại chỉ 1546×423 GIỮA khung; chữ nằm ngoài
                          ô đó là bị cắt. MascotBrand đã ép chữ vào đúng ô này.
  • watermark 1024×1024 — dấu chìm góc video YouTube
  • fbcover  1640×624   — bìa trang Facebook (an toàn cho cả di động)
  • thumb    1280×720   — khung thumbnail mẫu, giữ bố cục cố định cho cả kênh

    python mascot_brand.py --kenh EAGLEBANDIT        # sinh đủ 5 cỡ
    python mascot_brand.py --tat-ca                  # cả 5 kênh
"""
from __future__ import annotations

import json
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))

# (composition, thư mục con, tên file) — tên file nói rõ cỡ để anh khỏi phải tra lại khi upload
BO_CO = [
    ("MascotAvatar",    "avatar_800x800.png"),
    ("MascotBanner",    "banner_youtube_2560x1440.png"),
    ("MascotWatermark", "watermark_1024x1024.png"),
    ("MascotFbCover",   "cover_facebook_1640x624.png"),
    ("MascotThumb",     "thumbnail_mau_1280x720.png"),
]


def _qc_anh(dest: str, comp: str, kenh: str, keys: list) -> tuple[bool, str]:
    """QC HÌNH cho một ảnh nhận diện — ĐO trước, SOI sau (25/8, anh dặn "kiểm visual QC trước sau").

    Hai tầng, rẻ trước đắt sau:
      1. ĐO BẰNG PIXEL (0 quota): ảnh không được là nền trơn (nhân vật không hiện / lỗi nạp PNG),
         và phải đủ màu. Đây là bẫy thật đã xảy ra với video: file có, mở ra toàn nền.
      2. SOI BẰNG VISION (chỉ khi tầng 1 qua): hỏi đúng câu "có đúng nhân vật không, chữ có bị cắt
         không". Vision hỏng/hết quota trả None -> KHÔNG chặn (fail-open), vì tầng 1 đã gác phần
         chết người rồi.
    """
    import datastory_ci as DS
    try:
        dark, sat, cols = DS.flat_bg_metrics(dest)
    except Exception as e:
        return True, f"không đo được ({str(e)[:40]}) — cho qua"
    # avatar/watermark là hình tròn nền đặc nên tối/màu ít là BÌNH THƯỜNG; banner/thumb thì không
    it_mau = 60 if comp in ("MascotAvatar", "MascotWatermark") else 140
    if cols < it_mau:
        return False, f"chỉ {cols} màu — nhân vật nhiều khả năng KHÔNG hiện (nền trơn)"
    if dark >= 96:
        return False, f"tối {dark:.0f}% — ảnh gần như đen"
    try:
        import qc_vision as QV
        v = QV.verify_image(dest, f"the {kenh} channel mascot artwork, characters clearly visible, "
                                  f"no cut-off text, no distorted faces",
                            api_key=(keys or [{}])[0].get("key", ""))
        if v is False:
            return False, "Vision chấm KHÔNG đạt (nhân vật/chữ hỏng)"
    except Exception:
        pass
    return True, f"{cols} màu · tối {dark:.0f}%"


def sinh(kenh: str) -> int:
    import datastory_ci as DS
    import mascot_cast as MC
    import mascot_rig as MR

    kenh = kenh.upper()
    cast = MC.cast_cua(kenh)
    if not cast:
        print(f"❌ {kenh}: chưa khai dàn nhân vật"); return 1
    if not MR.da_co_rig(kenh, cast):
        print(f"❌ {kenh}: chưa có rig — chạy mascot_pilot.py --rig {kenh} trước"); return 2

    cfg = json.load(open(os.path.join(GOC, "mascot_channels.json"), encoding="utf-8")).get(kenh) or {}
    props = {
        "channel": kenh,
        "hero": cast[0]["id"],
        "hero2": cast[1]["id"] if len(cast) > 1 else "",
        "display": cfg.get("display") or kenh,
        "tagline": cfg.get("tagline") or (cfg.get("style") or "")[:52],
        "handle": "@" + kenh.lower(),
        "accent": cfg.get("accent", "#E4562B"),
        "accent2": cfg.get("accent2", "#2E6FD9"),
    }
    ra_dir = os.path.join(DS.ENG, "public", "brand", kenh)
    os.makedirs(ra_dir, exist_ok=True)
    pf = os.path.join(DS.PUB, f"_brand_{kenh}.json")
    json.dump(props, open(pf, "w"), ensure_ascii=False)

    import firestore_bridge as FB
    keys = []
    try:
        keys = FB.read_keys(os.environ.get("OWNER_UID", ""))
    except Exception:
        pass
    n = 0
    for comp, ten in BO_CO:
        dest = os.path.join(ra_dir, ten)
        try:
            DS.run_render_cmd(
                ["npx", "remotion", "still", "src/index.ts", comp, dest,
                 f"--props=./{os.path.relpath(pf, DS.ENG)}", "--gl=swiftshader", "--log=error"],
                cwd=DS.ENG, timeout=600, label=f"brand:{comp}")
            if not (os.path.exists(dest) and os.path.getsize(dest) > 3000):
                print(f"   ⚠️ {kenh}/{ten}: file rỗng"); continue
            ok, vi_sao = _qc_anh(dest, comp, kenh, keys)
            if ok:
                print(f"   ✅ {kenh}/{ten} · {vi_sao}")
                n += 1
            else:
                # KHÔNG xoá — giữ để soi tận mắt (luật "hỏng thì giữ bằng chứng")
                hong = os.path.join(ra_dir, "_hong"); os.makedirs(hong, exist_ok=True)
                os.replace(dest, os.path.join(hong, ten))
                print(f"   ❌ {kenh}/{ten}: {vi_sao} — chuyển vào _hong/, KHÔNG dùng")
        except Exception as e:
            print(f"   ⚠️ {kenh}/{comp}: {str(e)[:80]}")
    print(f"{'✅' if n == len(BO_CO) else '⚠️'} {kenh}: {n}/{len(BO_CO)} ảnh nhận diện")
    return 0 if n else 3


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--tat-ca", action="store_true")
    a = ap.parse_args()
    import mascot_cast as MC
    ds = list(MC.CAST) if a.tat_ca else ([a.kenh.upper()] if a.kenh else [])
    if not ds:
        ap.print_help(); return 1
    loi = 0
    for k in ds:
        loi |= sinh(k)
    return loi


if __name__ == "__main__":
    sys.exit(main())
