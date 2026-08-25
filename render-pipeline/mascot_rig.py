#!/usr/bin/env python3
"""RIG NHÂN VẬT — vẽ MỘT LẦN, dùng cho MỌI video của kênh (25/8/2026).

VÌ SAO PHẢI CÓ (bệnh đã giết concept mascot hồi 22/8)
-----------------------------------------------------
Cách cũ: mỗi cảnh gọi FLUX vẽ lại cả nhân vật lẫn bối cảnh, ghì bằng "style lock" trong prompt.
Style lock chỉ giữ được ~80%: soi hai khung liền nhau của CÙNG cặp đại bàng + gấu mèo thì tỉ lệ
đầu, độ dày nét, kính râm, cái ly đều lệch — khán giả thấy ngay "không phải một nhân vật".
Đó là lý do concept bị xếp lại, KHÔNG phải vì fps hay vì chi phí.

CÁCH CHỮA (chuẩn phim cutout — South Park, Rick & Morty đều vậy)
-----------------------------------------------------------------
Nhân vật được vẽ ĐÚNG MỘT LẦN cho cả kênh, thành một BỘ TƯ THẾ (pose set) tách nền trong suốt.
Từ đó về sau video chỉ còn: nền (1-3 ảnh/skit) + các lớp nhân vật ĐÃ CÓ SẴN, và Remotion điều
khiển từng lớp theo từng khung ở 30fps (nhún, nghiêng, phóng, nhép mồm theo biên độ tiếng).

Được cả ba thứ vốn xung khắc:
  • KHÔNG DRIFT   — không vẽ lại thì không có gì để lệch;
  • 30 FPS THẬT   — chuyển động do máy tính nội suy từng khung, không phải ảnh tĩnh đổi nhịp;
  • ~0 QUOTA/VIDEO— FLUX chỉ tốn lúc dựng rig (một lần/kênh), sau đó mỗi video chỉ vẽ nền.

TÁCH NỀN
--------
Bắt FLUX vẽ trên nền phẳng một màu hiếm (xanh chroma #00B140) rồi tự tách bằng PIL: pixel gần
màu khoá -> alpha 0, có viền mềm 2px để không răng cưa. Không cần rembg/AI, chạy CPU tức thì.

DÙNG
----
    python mascot_rig.py --kenh EAGLEBANDIT          # dựng rig (bỏ qua tư thế đã có)
    python mascot_rig.py --kenh EAGLEBANDIT --lam-lai  # vẽ lại từ đầu
"""
from __future__ import annotations

import io
import json
import os
import sys

# Màu khoá: xanh chroma phim trường. Chọn màu HIẾM trong tranh hoạt hình Mỹ (da/cờ/gỗ đều xa nó)
# để không ăn nhầm vào nhân vật.
KEY_RGB = (0, 177, 64)
NGUONG = 88            # khoảng cách màu tối đa còn coi là nền (0-441)
VIEN_MEM = 2           # px làm mềm mép, tránh răng cưa khi phóng to

# Bộ tư thế tối thiểu cho một nhân vật biết diễn. `talk_open`/`talk_closed` là cặp nhép mồm;
# các tư thế còn lại đổi theo nhịp kịch bản.
TU_THE = {
    "idle":        "standing relaxed, neutral friendly expression, mouth closed, arms at sides",
    "talk_closed": "standing, talking, mouth closed, mid-sentence expression, one hand gesturing",
    "talk_open":   "standing, talking, mouth open wide mid-word, same pose and same outfit, one hand gesturing",
    "react":       "surprised reaction, eyes wide, eyebrows up, mouth open, both hands raised",
    "smug":        "smug confident smirk, arms crossed, eyes half closed, leaning slightly back",
    "point":       "pointing forward at the viewer with one hand, explaining, mouth open",
}

# Câu đuôi ép FLUX vào đúng khuôn rig: một nhân vật, toàn thân, nền phẳng, không chữ.
DUOI = ("full body, head to toe, centered, facing viewer, single character alone, "
        "flat solid pure green background color #00B140, no shadow on background, "
        "no text, no letters, no signs, no watermark, no logo, no border")


def _tach_nen(duong: str) -> bool:
    """Biến nền xanh khoá thành trong suốt, ghi đè chính file (.png). True nếu tách được."""
    try:
        from PIL import Image
    except Exception as e:
        print(f"   ⚠️ thiếu Pillow ({e}) — không tách nền được")
        return False
    try:
        im = Image.open(duong).convert("RGBA")
        px = im.load()
        W, H = im.size
        kr, kg, kb = KEY_RGB
        nen = 0
        for y in range(H):
            for x in range(W):
                r, g, b, a = px[x, y]
                d = abs(r - kr) + abs(g - kg) + abs(b - kb)
                if d <= NGUONG:
                    px[x, y] = (r, g, b, 0)
                    nen += 1
                elif d <= NGUONG + 60:            # vành đai: mờ dần cho mép mượt
                    px[x, y] = (r, g, b, int(a * (d - NGUONG) / 60))
        # Nền phải chiếm phần đáng kể — dưới 12% nghĩa là FLUX không vẽ nền phẳng, rig sẽ hỏng.
        ty = nen / max(1, W * H)
        if ty < 0.12:
            print(f"   ⚠️ chỉ {ty*100:.0f}% khung là nền khoá — FLUX không vẽ nền phẳng, bỏ tư thế này")
            return False
        if VIEN_MEM:
            from PIL import ImageFilter
            alpha = im.split()[3].filter(ImageFilter.GaussianBlur(VIEN_MEM))
            im.putalpha(alpha)
        im.save(duong, "PNG")
        return True
    except Exception as e:
        print(f"   ⚠️ tách nền hỏng: {str(e)[:70]}")
        return False


def _cat_khung(duong: str) -> None:
    """Cắt sát nhân vật (bỏ viền trong suốt thừa) -> Remotion canh vị trí chuẩn, khỏi đoán lề."""
    try:
        from PIL import Image
        im = Image.open(duong)
        bb = im.getbbox()
        if bb:
            im.crop(bb).save(duong, "PNG")
    except Exception:
        pass


def dung_rig(kenh: str, nhan_vat: dict, keys: list, lam_lai: bool = False) -> dict:
    """Dựng bộ tư thế cho MỘT nhân vật. Trả {ten_tu_the: đường dẫn} những cái dựng được.

    `nhan_vat` = {"id": "BALD", "mo_ta": "...", "style": "..."}.
    Đã có file thì BỎ QUA (rig là tài sản một lần — vẽ lại chỉ tổ tạo ra drift mới)."""
    import datastory_ci as DS
    goc = os.path.join(DS.ENG, "public", "mascots", str(kenh).upper(), str(nhan_vat["id"]).upper())
    os.makedirs(goc, exist_ok=True)
    ra = {}
    for ten, tu_the in TU_THE.items():
        dest = os.path.join(goc, f"{ten}.png")
        if os.path.exists(dest) and os.path.getsize(dest) > 5000 and not lam_lai:
            ra[ten] = dest
            continue
        prompt = f"{nhan_vat['mo_ta']}, {tu_the}, {DUOI}"
        tam = dest + ".raw.png"
        try:
            ok = DS._generate_image_ai(prompt, tam, (keys or [{}])[0].get("key", ""),
                                       style=nhan_vat.get("style") or "")
        except Exception as e:
            print(f"   ⚠️ {nhan_vat['id']}/{ten}: vẽ hỏng ({str(e)[:60]})")
            ok = False
        if not ok or not os.path.exists(tam):
            continue
        os.replace(tam, dest)
        if _tach_nen(dest):
            _cat_khung(dest)
            ra[ten] = dest
            print(f"   ✅ {kenh}/{nhan_vat['id']}/{ten}")
        else:
            os.remove(dest)
    return ra


def rig_kenh(kenh: str, cast: list, keys: list, lam_lai: bool = False) -> dict:
    """Dựng rig cho cả dàn nhân vật của kênh. Trả {id_nhan_vat: {tư_thế: path}}."""
    ra = {}
    for nv in cast:
        ra[str(nv["id"]).upper()] = dung_rig(kenh, nv, keys, lam_lai)
    thieu = [k for k, v in ra.items() if len(v) < 3]
    if thieu:
        print(f"   ⚠️ {kenh}: nhân vật {thieu} chưa đủ 3 tư thế — kênh CHƯA sẵn sàng diễn")
    return ra


# ── BỐI CẢNH NHIỀU LỚP (multiplane camera — nguyên lý phim 2D từ 1937) ──────────────────────
# Nền phẳng zoom vào thì mắt biết ngay là ảnh tĩnh. Tách nền thành các lớp SÂU rồi cho chúng
# trượt ở tốc độ khác nhau thì não đọc ra chiều sâu — đó là toàn bộ bí quyết "bối cảnh sống"
# của phim hoạt hình 2D, và nó là hình học thuần tuý: 0 quota, 0 AI, chỉ tốn vài phép nhân/khung.
# Lớp `sky` phủ kín khung nên KHÔNG tách nền; các lớp còn lại tách để nhìn xuyên qua.
DUOI_NEN = ("wide establishing shot, no people, no characters, no animals, "
            "flat solid pure green background color #00B140 behind everything, "
            "no text, no letters, no signs, no watermark, no logo")


def dung_san_khau(kenh: str, ten: str, lop_list: list, keys: list, lam_lai: bool = False) -> dict:
    """Vẽ các lớp sâu của MỘT sân khấu. Trả {tên_lớp: đường dẫn}. Đã có thì bỏ qua."""
    import datastory_ci as DS
    goc = os.path.join(DS.ENG, "public", "stages", str(kenh).upper(), str(ten))
    os.makedirs(goc, exist_ok=True)
    ra = {}
    for lp in lop_list:
        ten_lop = lp["lop"]
        dest = os.path.join(goc, f"{ten_lop}.png")
        if os.path.exists(dest) and os.path.getsize(dest) > 5000 and not lam_lai:
            ra[ten_lop] = dest
            continue
        # lớp nền dưới cùng phủ kín khung -> KHÔNG ép nền xanh, KHÔNG tách
        la_sky = ten_lop == "sky"
        duoi = ("wide flat background plate, no people, no characters, no text, no letters, "
                "no watermark") if la_sky else DUOI_NEN
        tam = dest + ".raw.png"
        try:
            ok = DS._generate_image_ai(f"{lp['mo_ta']}, {duoi}", tam,
                                       (keys or [{}])[0].get("key", ""),
                                       style=lp.get("style") or "")
        except Exception as e:
            print(f"   ⚠️ {kenh}/{ten}/{ten_lop}: vẽ hỏng ({str(e)[:60]})")
            ok = False
        if not ok or not os.path.exists(tam):
            continue
        os.replace(tam, dest)
        if la_sky or _tach_nen(dest):
            ra[ten_lop] = dest
            print(f"   ✅ nền {kenh}/{ten}/{ten_lop}")
        else:
            os.remove(dest)
    return ra


def da_co_san_khau(kenh: str, ten: str) -> bool:
    """Sân khấu dùng được chưa? Cần ÍT NHẤT sky + 1 lớp nữa (không thì hết chiều sâu)."""
    import datastory_ci as DS
    goc = os.path.join(DS.ENG, "public", "stages", str(kenh).upper(), str(ten))
    if not os.path.isdir(goc):
        return False
    co = {f[:-4] for f in os.listdir(goc) if f.endswith(".png")}
    return "sky" in co and len(co) >= 2


def da_co_rig(kenh: str, cast: list) -> bool:
    """Rig đủ dùng chưa? (mỗi nhân vật ≥3 tư thế, trong đó BẮT BUỘC có cặp nhép mồm)"""
    import datastory_ci as DS
    for nv in cast:
        goc = os.path.join(DS.ENG, "public", "mascots", str(kenh).upper(), str(nv["id"]).upper())
        if not os.path.isdir(goc):
            return False
        co = {f[:-4] for f in os.listdir(goc) if f.endswith(".png")}
        if len(co) < 3 or not {"talk_open", "talk_closed"} <= co:
            return False
    return True


def _main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", required=True)
    ap.add_argument("--lam-lai", action="store_true")
    a = ap.parse_args()
    import firestore_bridge as FB
    import mascot_cast as MC
    cast = MC.CAST.get(a.kenh.upper())
    if not cast:
        print(f"❌ chưa khai báo dàn nhân vật cho {a.kenh} (xem mascot_cast.py)")
        return 1
    keys = FB.read_keys(os.environ.get("OWNER_UID", ""))
    ra = rig_kenh(a.kenh.upper(), cast, keys, a.lam_lai)
    nen = {}
    for ten in MC.ten_san_khau(a.kenh.upper()):
        nen[ten] = sorted(dung_san_khau(a.kenh.upper(), ten,
                                        MC.san_khau_cua(a.kenh.upper(), ten), keys, a.lam_lai))
    print(json.dumps({"nhan_vat": {k: sorted(v) for k, v in ra.items()}, "san_khau": nen},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
