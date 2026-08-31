#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KỊCH COMIC — mười kênh hài dựng lại theo lối truyện tranh (31/8/2026)
════════════════════════════════════════════════════════════════════════════════════════════

Anh xem ba khung của bản hài cũ rồi bảo xoá đi làm lại. Ba khung ấy hỏng vì MỘT nguyên nhân
kiến trúc: bản cũ dán người vector lên ảnh AI. Chi tiết chẩn đoán nằm ở đầu `KichComic.tsx`.

Tệp này là nửa Python của bản mới. Nó CỐ Ý mỏng, và giữ nguyên bốn thứ đã tốt của bản cũ —
những thứ đã trả giá bằng nhiều vòng sửa và không dính dáng gì tới lỗi hình:

    · `KHO`            — bốn mươi mẩu thoại viết sẵn, đúng nhịp hài đối đáp Mỹ
    · `doc_hai_giong`  — mỗi lượt một giọng riêng, mốc thời gian ĐO từ WAV chứ không suy
    · `_hai_bong`      — bộ nhận dạng riêng của từng nhân vật, khoá theo kênh
    · `lam_thumb`      — ảnh bìa trích từ video đã dựng

Và bỏ đúng một thứ: `canh_nen_ai` cùng toàn bộ đường sinh ảnh nền. Nền nay do engine vẽ.
Bỏ nó lấy lại được ba thứ cùng lúc — hết lệch phong cách, hết nền không khớp thoại, và hết
phụ thuộc hạn mức ảnh của nhà cung cấp (một video comic không gọi API ảnh lần nào).

CHẠY TỰ ĐỘNG TRÊN GITHUB: mọi thứ ở đây chỉ cần `edge-tts` + `remotion`, không cần khoá ảnh,
không cần Claude Code. Cùng một lệnh chạy được ở máy anh và trong Actions.
"""
import os
import io
import json
import argparse
import subprocess

from kich_hai import (KENH, KHO, cu_chi_cua, doc_hai_giong, _ten_tep, lam_thumb,
                      _hai_bong, GOC, ENG, PUB)

# Giọng đọc — chép nguyên từ bản cũ. Mỗi kênh một cặp giọng khác nhau; hai kênh chung một cặp
# là dấu hiệu sản xuất hàng loạt mà bộ kiểm tra của 50 kênh đã chặn từ lâu.
GIONG_KENH = {
    "rent":     (("en-US-EricNeural", "+14%", "+12Hz"), ("en-US-JennyNeural", "-6%", "-6Hz")),
    "gym":      (("en-US-SteffanNeural", "-8%", "-14Hz"), ("en-US-AvaNeural", "+16%", "+16Hz")),
    "airport":  (("en-US-GuyNeural", "-2%", "-6Hz"), ("en-US-MichelleNeural", "-10%", "-2Hz")),
    "car":      (("en-US-EricNeural", "+10%", "+10Hz"), ("en-US-ChristopherNeural", "-12%", "-18Hz")),
    "office":   (("en-US-AriaNeural", "+6%", "+4Hz"), ("en-US-BrianNeural", "+2%", "-8Hz")),
    "diet":     (("en-US-AvaNeural", "+8%", "+8Hz"), ("en-US-SteffanNeural", "-10%", "-16Hz")),
    "tech":     (("en-US-ChristopherNeural", "-14%", "-16Hz"), ("en-US-EricNeural", "+6%", "+10Hz")),
    "parent":   (("en-US-GuyNeural", "-8%", "-16Hz"), ("en-US-AnaNeural", "+18%", "+18Hz")),
    "neighbor": (("en-US-ChristopherNeural", "-6%", "-12Hz"), ("en-US-MichelleNeural", "+4%", "+4Hz")),
    "dating":   (("en-US-BrianNeural", "+10%", "+8Hz"), ("en-US-RogerNeural", "-4%", "-10Hz")),
}

NHAC = {"rent": "music/forecast.mp3", "gym": "music/km_undaunted.mp3",
        "airport": "music/mind_pad32.mp3", "car": "music/km_interloper.mp3",
        "office": "music/wallpaper.mp3", "diet": "music/carefree.mp3",
        "tech": "music/mindloop_pad.mp3", "parent": "music/inspired.mp3",
        "neighbor": "music/km_ascending.mp3", "dating": "music/km_reawakening.mp3"}

# ══ HAI MÀU CỦA MỖI KÊNH ═══════════════════════════════════════════════════════════════
# 31/8 — `k["mau"]` KHÔNG PHẢI MÀU THƯƠNG HIỆU.
# Bản đầu của tệp này truyền thẳng `k["mau"]` xuống engine làm màu nhấn. Khung ra có tên kênh
# đọc được mà handle thì biến mất, và cả trang nhợt như ảnh phơi nắng. Lý do: `k["mau"]` của
# TECH SUPPORT là `#E9E6F4` — một màu tím trắng, vì trong bản cũ nó là MÀU NỀN DỰ PHÒNG
# (`mucNen`), thứ để lót sau nhân vật khi ảnh AI chưa tải xong. Dùng một màu nền làm màu chữ
# thì chữ nằm trên giấy trắng và không ai thấy.
#
# Đây là họ lỗi "mượn một giá trị cho việc nó không sinh ra để làm". Không có cách sửa nào ở
# chỗ dùng — phải có bảng riêng, và bảng ấy là đây. Mỗi kênh HAI màu ăn nhau (một ấm một
# lạnh), không kênh nào trùng kênh nào: một trang truyện tranh chịu được đúng hai màu mạnh.
MAU_CHINH = {"rent": "#E4572E", "gym": "#0FA36B", "airport": "#D64545", "car": "#2D6CDF",
             "office": "#7A5AF8", "diet": "#12A594", "tech": "#1F7AE0", "parent": "#EF6C3B",
             "neighbor": "#0E9F6E", "dating": "#E0367A"}
MAU_PHU = {"rent": "#1F7AE0", "gym": "#F2994A", "airport": "#2A9D8F", "car": "#F4A522",
           "office": "#10B981", "diet": "#EC4899", "tech": "#F97316", "parent": "#3B82F6",
           "neighbor": "#B45309", "dating": "#8B5CF6"}


def dung_luot_comic(k: dict, vong: int) -> tuple:
    """Trả (danh sách lượt, danh sách câu thô). Mỏng hơn `dung_luot` của bản cũ đúng một cột:

    KHÔNG CÒN `goc` VÀ `co`.

    Bản cũ ghi sẵn cỡ máy và góc máy vào từng lượt, rồi engine đọc theo. Đó là nguồn của lỗi
    nặng nhất anh nhìn thấy — lượt ghi "hai_nguoi" mà khung ra chỉ có một người — vì kịch bản
    không biết khung rộng bao nhiêu pixel, nên nó KHÔNG ĐỦ THÔNG TIN để quyết định việc ấy.
    Nay panel tự đo mình rồi tự chọn: đủ chỗ thì hai người, không đủ thì cận một người.
    Kịch bản chỉ còn nói thứ nó thật sự biết — ai nói câu gì, với cảm xúc nào.
    """
    kho = KHO[k["de"]]
    kb = kho[vong % len(kho)]
    cau = kb["loi"]
    n = len(cau)
    luot = []
    for i, (chu, ai, cx) in enumerate(cau):
        cuoi = i == n - 1
        luot.append({
            "s": 0.0, "e": 0.0, "ai": ai, "nar": chu, "camXuc": cx,
            # Ở cú chốt người nghe phải SỮNG, không được cười: nhân vật cười hộ rồi thì khán
            # giả không cười nữa. (Luật này của bản cũ đúng, giữ nguyên.)
            "camXucKia": ("bat_ngo" if cuoi else
                          ["nghi_ngo", "bat_ngo", "trung_tinh", "tuc", "buon", "nghi_ngo"][i % 6]),
            "cuChi": cu_chi_cua(chu, i, cuoi),
            "chot": cuoi,
        })
    return luot, cau


def mot_kenh(k: dict, vong: int) -> str:
    """Dựng một video comic. Trả đường tệp, hoặc "" nếu hỏng."""
    ten = k["ten"]
    slug = _ten_tep(k)
    print(f"\n▶ {ten}", flush=True)

    luot, cau = dung_luot_comic(k, vong)
    ga, gb = GIONG_KENH.get(k["de"], (("en-US-GuyNeural", "+4%", "+0Hz"),
                                      ("en-US-JennyNeural", "+2%", "+6Hz")))
    rel = f"v5_{slug}.mp3"
    mp3 = os.path.join(PUB, rel)
    try:
        dur, tu, moc = doc_hai_giong(cau, ga, gb, mp3)
    except Exception as e:
        print(f"   ❌ giọng đọc hỏng: {str(e)[:110]}")
        return ""
    if not tu:
        print("   ❌ không có mốc từ — BỎ")
        return ""

    for i, l in enumerate(luot):
        l["s"], l["e"] = moc[i]

    tuyA, tuyB = _hai_bong(k)
    props = {
        "luot": luot, "tu": tu, "voMp3": rel, "nhac": NHAC.get(k["de"], ""),
        "kieuA": k["a"], "kieuB": k["b"], "kieuTuyA": tuyA, "kieuTuyB": tuyB,
        "tieuDe": ten, "handle": k.get("handle", ""), "kenh": slug,
        "mau": MAU_CHINH.get(k["de"], "#E4572E"), "mauPhu": MAU_PHU.get(k["de"], "#1F7AE0"),
    }
    pj = os.path.join(GOC, "out", f"v5_{slug}.json")
    os.makedirs(os.path.dirname(pj), exist_ok=True)
    io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))

    out = os.path.join(GOC, "out", f"v5_{slug}.mp4")
    r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "KichComic", out,
                        f"--props={pj}", "--gl=swiftshader", "--log=error"],
                       cwd=ENG, capture_output=True, text=True, timeout=2400)
    if r.returncode or not os.path.exists(out):
        print(f"   ❌ render hỏng: {(r.stderr or r.stdout or '')[-200:]}")
        return ""

    th = os.path.join(GOC, "out", f"v5_{slug}.jpg")
    if lam_thumb(out, cau[0][0] if cau else ten, ten, k["mau"], th):
        print(f"   🖼  thumbnail: {os.path.basename(th)}")
    print(f"   ✅ {ten}: {os.path.basename(out)}  "
          f"({os.path.getsize(out) / 1e6:.1f} MB · {dur:.0f}s · {len(luot)} panel)")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="", help="lọc theo tên kênh, cách nhau bằng dấu phẩy")
    ap.add_argument("--vong", type=int, default=0, help="số tập — bốc mẩu thoại thứ mấy trong kho")
    a = ap.parse_args()

    chon = KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [x for x in KENH if x["ten"].replace(" ", "").upper() in vt]
    if not chon:
        print("❌ không khớp kênh nào")
        return 2

    ra = [v for v in (mot_kenh(k, a.vong) for k in chon) if v]
    print(f"\n{'✅' if ra else '⚠️'} {len(ra)}/{len(chon)} video comic")
    return 0 if ra else 1


if __name__ == "__main__":
    raise SystemExit(main())
