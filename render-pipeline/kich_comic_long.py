#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMIC BẢN DÀI 16:9 — chỗ kiếm tiền của mười kênh hài (31/8/2026)
════════════════════════════════════════════════════════════════════════════════════════════

Anh hỏi: *"loại này thì có ghép videos long hay sao để tối ưu kiếm tiền youtube sao cho vẫn
viral và hay và đảm bảo độ dài ko"*, rồi chốt: *"long thì phải 16:9 và dựng cho phù hợp 16:9"*.

── VÌ SAO PHẢI CÓ BẢN DÀI ────────────────────────────────────────────────────────────────
Tiền nằm ở video dài. Shorts chia doanh thu từ quỹ quảng cáo của Shorts Feed và RPM thấp hơn
long-form khoảng một bậc; long-form từ TÁM PHÚT trở lên mới bật được quảng cáo giữa video, và
đó là chỗ chênh lệch lớn nhất. Đường vào YPP cũng dễ hơn hẳn: 4.000 giờ xem — một video 10
phút giữ chân 40% chỉ cần chừng 60.000 lượt — so với 10 triệu lượt Shorts trong 90 ngày.

── VÌ SAO KHÔNG NỐI SHORT LẠI ────────────────────────────────────────────────────────────
Nối các short rời thành một video dài là compilation, và nó rơi thẳng vào chính sách nội dung
tái sử dụng / thiếu tính nguyên bản — đúng thứ anh vẫn lo. Một tập dài phải là MỘT TẬP PHIM:

  · có mạch — A đang cố làm xong MỘT việc, mỗi cảnh là một trở ngại mới trên đường ấy;
  · có mở, có thân, có kết — cảnh cuối gọi lại cảnh đầu (callback), thứ mà một chuỗi mẩu rời
    không bao giờ có;
  · có chương đặt tên, để người xem biết mình đang ở đâu trong mười phút.

Cùng nhân vật, cùng thế giới với bản short: Shorts kéo người xem về, bản dài giữ họ lại.

── CÁCH DỰNG ─────────────────────────────────────────────────────────────────────────────
Engine `KichComic` viết sẵn hai nhánh bố cục. Khung dọc vẽ cả người (bong bóng trên đầu, nền
lấp khoảng giữa); khung ngang cắt ngang hông cho mặt to — vì khung ngang không có chiều cao để
chứa cả người mà vẫn đọc được nét mặt. Bản dài dùng nhánh thứ hai qua composition
`KichComicWide` (1920×1080). Không phải viết lại engine, chỉ đổi khung.
"""
import os
import io
import json
import argparse
import subprocess

from kich_hai import (KENH, KHO, cu_chi_cua, doc_hai_giong, _ten_tep, lam_thumb,
                      _hai_bong, GOC, ENG, PUB)
from kich_comic import GIONG_KENH, NHAC, MAU_CHINH, MAU_PHU, NET_KENH

# Mục tiêu độ dài: qua ngưỡng tám phút để bật được quảng cáo giữa video, và dừng quanh mười một
# phút — dài hơn nữa thì tỉ lệ xem hết tụt nhanh với thể loại hài ngắn nối chương.
GIAY_TOI_THIEU = 8 * 60 + 20
GIAY_TOI_DA = 11 * 60


def _kho_day(k: dict) -> list:
    """Toàn bộ mẩu của một kênh: viết tay trước (mẫu giọng chuẩn), rồi kho sinh bằng AI."""
    ra = [{"loi": list(m["loi"])} for m in KHO[k["de"]]]
    tep = os.path.join(GOC, "kho_comic.json")
    if os.path.exists(tep):
        try:
            k2 = json.load(io.open(tep, encoding="utf-8"))
            for m in k2.get("mau", {}).get(k["de"], []):
                ra.append({"loi": [tuple(c) for c in m["loi"]], "nhan": m.get("tinh_huong", "")})
        except Exception as e:
            print(f"   ⚠️ kho sinh không đọc được: {str(e)[:70]}")
    return ra


def dung_tap_dai(k: dict, so_tap: int) -> tuple:
    """Trả (danh sách cảnh, danh sách câu, tên chương).

    ── ƯU TIÊN KHO TẬP DÀI, KHÔNG NỐI MẨU RỜI ────────────────────────────────────────────
    31/8 — Bản trước nối mẩu short theo cửa sổ trượt. Nó cho ra video chín phút, nhưng mười bốn
    mẩu không liên quan nhau nối lại thì vẫn là mười bốn mẩu không liên quan nhau — tức là
    compilation, đúng thứ chính sách nội dung tái sử dụng nhắm tới.

    `sinh_tap_dai.py` sinh TẬP có mạch: một việc A cố làm xong, mỗi cảnh là hậu quả của cách A
    xử lý cảnh trước, cảnh cuối gọi lại cảnh đầu. Kho ấy đứng trước; chỉ khi kênh chưa có tập
    nào thì mới lùi về cách nối mẩu — và khi lùi thì NÓI RA, để không ai tưởng đang có mạch.
    """
    tep = os.path.join(GOC, "kho_dai.json")
    if os.path.exists(tep):
        try:
            kd = json.load(io.open(tep, encoding="utf-8")).get(k["de"], [])
        except Exception as e:
            print(f"   ⚠️ kho tập dài không đọc được: {str(e)[:60]}")
            kd = []
        if kd:
            t = kd[so_tap % len(kd)]
            cau, chuong, chon = [], [], []
            for c in t["canh"]:
                chuong.append((c.get("tro_ngai") or "")[:58])
                chon.append(c)
                for x in c["loi"]:
                    cau.append(tuple(x))
            print(f"   📖 tập có mạch: {t.get('tua','')} — {t.get('viec','')[:56]}")
            return chon, cau, chuong

    print("   ⚠️ kênh chưa có tập dài nào — lùi về NỐI MẨU RỜI (đây là compilation, "
          "chạy sinh_tap_dai.py để có tập thật)")
    kho = _kho_day(k)
    if len(kho) < 6:
        return [], [], []
    n_can = min(len(kho), 16)
    bat_dau = (so_tap * n_can) % len(kho)
    chon = [kho[(bat_dau + i) % len(kho)] for i in range(n_can)]
    cau, chuong = [], []
    for i, m in enumerate(chon):
        chuong.append(m.get("nhan") or f"Part {i + 1}")
        for c in m["loi"]:
            cau.append(tuple(c))
    return chon, cau, chuong


def mot_kenh_dai(k: dict, so_tap: int) -> str:
    ten = k["ten"]
    slug = _ten_tep(k)
    print(f"\n▶ {ten} — bản dài", flush=True)

    chon, cau, chuong = dung_tap_dai(k, so_tap)
    if not cau:
        print("   ⏭ kho chưa đủ mẩu cho một tập dài (cần ≥ 6). Chạy sinh_kich_ban.py trước.")
        return ""
    print(f"   {len(chon)} mẩu · {len(cau)} lượt thoại", flush=True)

    ga, gb = GIONG_KENH.get(k["de"], (("en-US-GuyNeural", "+4%", "+0Hz"),
                                      ("en-US-JennyNeural", "+2%", "+6Hz")))
    rel = f"v5L_{slug}.mp3"
    try:
        dur, tu, moc = doc_hai_giong(cau, ga, gb, os.path.join(PUB, rel))
    except Exception as e:
        print(f"   ❌ giọng đọc hỏng: {str(e)[:110]}")
        return ""
    if not tu:
        print("   ❌ không có mốc từ — BỎ")
        return ""
    print(f"   ⏱  {dur/60:.1f} phút", flush=True)
    if dur < GIAY_TOI_THIEU:
        print(f"   ⚠️ NGẮN HƠN NGƯỠNG QUẢNG CÁO GIỮA VIDEO ({GIAY_TOI_THIEU/60:.1f} phút) — "
              f"sinh thêm mẩu rồi dựng lại thì mới bật được mid-roll")

    n = len(cau)
    luot = []
    for i, (chu, ai, cx) in enumerate(cau):
        cuoi_mau = (i + 1 == n) or (i + 1 < n and cau[i + 1][1] == 0 and ai == 1
                                    and (i + 1) % 6 == 0)
        luot.append({
            "s": moc[i][0], "e": moc[i][1], "ai": ai, "nar": chu, "camXuc": cx,
            "camXucKia": ("bat_ngo" if cuoi_mau else
                          ["nghi_ngo", "bat_ngo", "trung_tinh", "tuc", "buon", "nghi_ngo"][i % 6]),
            "cuChi": cu_chi_cua(chu, i, cuoi_mau),
            "chot": i + 1 == n,          # chỉ cảnh CUỐI TẬP mới là cú chốt lớn
        })

    tuyA, tuyB = _hai_bong(k)
    nk = NET_KENH.get(k["de"], dict(net=7, cham=9, bo=26, tile=0.60))
    props = {
        "luot": luot, "tu": tu, "voMp3": rel, "nhac": NHAC.get(k["de"], ""),
        "kieuA": k["a"], "kieuB": k["b"], "kieuTuyA": tuyA, "kieuTuyB": tuyB,
        "tieuDe": ten, "handle": k.get("handle", ""), "kenh": slug,
        "mau": MAU_CHINH.get(k["de"], "#E4572E"), "mauPhu": MAU_PHU.get(k["de"], "#1F7AE0"),
        "netMuc": nk["net"], "cham": nk["cham"], "boGoc": nk["bo"], "tiLe": nk["tile"],
        "soTap": so_tap,
    }
    pj = os.path.join(GOC, "out", f"v5L_{slug}.json")
    os.makedirs(os.path.dirname(pj), exist_ok=True)
    io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))

    out = os.path.join(GOC, "out", f"v5L_{slug}.mp4")
    r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "KichComicWide", out,
                        f"--props={pj}", "--gl=swiftshader", "--log=error"],
                       cwd=ENG, capture_output=True, text=True, timeout=9000)
    if r.returncode or not os.path.exists(out):
        print(f"   ❌ render hỏng: {(r.stderr or r.stdout or '')[-200:]}")
        return ""

    th = os.path.join(GOC, "out", f"v5L_{slug}.jpg")
    lam_thumb(out, cau[0][0] if cau else ten, ten, k["mau"], th)
    print(f"   ✅ {ten}: {os.path.basename(out)} "
          f"({os.path.getsize(out)/1e6:.0f} MB · {dur/60:.1f} phút · {len(luot)} cảnh)")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--vong", type=int, default=0)
    a = ap.parse_args()

    chon = KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [x for x in KENH if x["ten"].replace(" ", "").upper() in vt]
    if not chon:
        print("❌ không khớp kênh nào")
        return 2

    ra = [v for v in (mot_kenh_dai(k, a.vong) for k in chon) if v]
    print(f"\n{'✅' if ra else '⚠️'} {len(ra)}/{len(chon)} tập dài")
    return 0 if ra else 1


if __name__ == "__main__":
    raise SystemExit(main())
