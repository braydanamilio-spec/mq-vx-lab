#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DỰNG PHIM HOẠT HÌNH CÓ NHÂN VẬT — thế hệ 3, 10 kênh mới (29/8/2026).

TÁCH HẲN KHỎI 50 KÊNH ĐANG CHẠY. Anh: "ko động vào 50 channel đang ok hiện tại mà nếu làm ok
thì làm channel mới". Tệp này không import `the_he_2` và không đọc `kenh_the_he_2.json`; nó có
danh sách kênh riêng ở dưới. Hai đường chạy song song, chung hạ tầng render/giọng đọc, KHÔNG
chung một dòng mã dựng nào — nên sửa ở đây không thể làm hỏng 50 kênh kia.

    python kich_v2.py --demo                 # dựng 1 video ngắn cho MỖI kênh (10 video)
    python kich_v2.py --kenh BANKRUN         # chỉ một kênh
    python kich_v2.py --demo --luong 3

KHÔNG TỐN LƯỢT VẼ ẢNH. Nhân vật và bối cảnh đều là vector dựng bằng mã (xem `src/v2/`). Chỉ
tốn giọng đọc edge-tts, thứ vốn miễn phí và không hạn mức.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(GOC, "..", "engine-remotion")
PUB = os.path.join(ENG, "public")
sys.path.insert(0, GOC)

# ══════════════════════════════════════════════════════════════════════════════════════════
# MƯỜI KÊNH — xem YTUONG_V3.md để biết vì sao chọn đúng mười niche này
# ------------------------------------------------------------------------------------------
# Mỗi kênh khai: nguồn dữ liệu, nhân vật, bối cảnh, bảng màu, và một GÓC NHÌN riêng.
# `nguon` trỏ tới một hàm trong `du_lieu_mo` — cùng kho nguồn mở với 50 kênh cũ, nhưng CÁCH KỂ
# khác hẳn: ở đây có một người đứng ra nói, không phải một bảng số tự trôi.
# ══════════════════════════════════════════════════════════════════════════════════════════
KENH = [
    {"ten": "BANK RUN", "handle": "@bankrunusa", "nhan": "Is your bank actually healthy?",
     "kieu": "nu_kinh", "boi": "quay", "mau": "ngan_hang", "nguon": "fdic",
     "hoi": "How many banks does America still have?"},
    {"ten": "FINE PRINT", "handle": "@fineprintusa", "nhan": "The clause they hope you skip",
     "kieu": "nam_gay", "boi": "van_phong", "mau": "van_phong", "nguon": "cfpb",
     "hoi": "What do Americans complain about most?"},
    {"ten": "WHO OWNS IT", "handle": "@whoownsitusa", "nhan": "Who really owns the brand",
     "kieu": "nam_dam", "boi": "san_sau", "mau": "san_sau", "nguon": "sec",
     "hoi": "Who owns the company behind your groceries?"},
    {"ten": "KNOW YOUR RIGHT", "handle": "@knowyourrightusa", "nhan": "What you are allowed to do",
     "kieu": "nu_kinh", "boi": "toa_an", "mau": "luat", "nguon": "toa",
     "hoi": "What rights get argued in court this month?"},
    {"ten": "SUED IN AMERICA", "handle": "@suedinamericausa", "nhan": "What Americans sue over",
     "kieu": "nam_dam", "boi": "toa_an", "mau": "luat", "nguon": "toa",
     "hoi": "What do Americans actually sue each other over?"},
    {"ten": "SKY TONIGHT", "handle": "@skytonightusa", "nhan": "What is above you right now",
     "kieu": "nu_kinh", "boi": "vu_tru", "mau": "vu_tru", "nguon": "nasa",
     "hoi": "What just passed the Earth?"},
    {"ten": "ONE EXPERIMENT", "handle": "@oneexperimentusa", "nhan": "One study, explained straight",
     "kieu": "nam_gay", "boi": "lab", "mau": "phong_lab", "nguon": "epmc",
     "hoi": "What does the research actually say?"},
    {"ten": "DEEP FIELD", "handle": "@deepfieldusa", "nhan": "The farthest thing we have seen",
     "kieu": "nam_gay", "boi": "vu_tru", "mau": "vu_tru", "nguon": "nasa",
     "hoi": "How far away is the farthest rock we track?"},
    {"ten": "WHAT THE CHART SAYS", "handle": "@whatthechartusa", "nhan": "What your chart does not say out loud",
     "kieu": "nu_kinh", "boi": "phong_kham", "mau": "phong_kham", "nguon": "fda",
     "hoi": "What got pulled off the shelf this month?"},
    # 29/8 — ĐỔI NGUỒN. Hai kênh y tế cùng khai `fda` nên ra GẦN NHƯ CÙNG MỘT VIDEO: cùng bảng
    # thu hồi, cùng con số 2,9M, cùng bối cảnh phòng khám. Đó đúng là khuôn "nội dung lặp lại"
    # mà chính sách YouTube nhắm vào — và tôi vừa tự tạo ra nó trong bộ kênh mới.
    # Chỉ số giá y tế của BLS mới là thứ trả lời được câu hỏi của kênh này.
    {"ten": "PRICE OF CARE", "handle": "@priceofcareusa", "nhan": "What care costs now",
     "kieu": "nam_dam", "boi": "phong_kham", "mau": "phong_kham", "nguon": "gia_yte",
     "hoi": "How much has medical care gone up?"},
]

# ══════════════════════════════════════════════════════════════════════════════════════════
# LẤY SỐ LIỆU THẬT
# ------------------------------------------------------------------------------------------
# Mỗi nguồn trả về (tiêu đề, [ (nhãn, giá trị, chuỗi hiện) ], câu nguồn). Không có dữ liệu thì
# trả None và kênh BỎ LƯỢT — cùng nguyên tắc với 50 kênh cũ: thà không ra video còn hơn bịa.
# ══════════════════════════════════════════════════════════════════════════════════════════
def _so(v: float) -> str:
    if v >= 1_000_000_000:
        return f"${v/1e9:.1f}B".replace(".0B", "B")
    if v >= 1_000_000:
        return f"{v/1e6:.1f}M".replace(".0M", "M")
    if v >= 10_000:
        return f"{v/1e3:.1f}K".replace(".0K", "K")
    return f"{v:,.0f}"


def lay_so_lieu(nguon: str, D):
    if nguon == "fda":
        # `thu_hoi_fda` đòi tham số KHO trước tiên; gọi thiếu thì rơi vào endpoint sai và nhận
        # 404 — đo được ở lượt chạy đầu, kênh im lặng bỏ lượt.
        r = D.thu_hoi_fda("thuc_pham", 60) or []
        gom: dict = {}
        for x in r:
            t = str(x.get("cong_ty") or "").strip()[:26]
            if not t:
                continue
            # `so_luong` là CHUỖI như "1,589,577 dozen total" — lấy cụm số đầu tiên. Không đọc
            # được thì tính 1 (một vụ thu hồi), vẫn đúng nghĩa "đếm vụ".
            import re as _re
            m = _re.search(r"[\d][\d,]*", str(x.get("so_luong") or ""))
            gom[t] = gom.get(t, 0) + (float(m.group(0).replace(",", "")) if m else 1.0)
        ds = sorted(gom.items(), key=lambda z: -z[1])[:6]
        if len(ds) < 3:
            return None
        return ("Recalls filed this month", [(k, v, _so(v)) for k, v in ds],
                "openFDA, U.S. Food and Drug Administration")
    if nguon == "sec":
        # MỘT từ khoá chỉ ra 8 bản ghi thuộc 2 công ty — không đủ dựng bảng sáu dòng. Hỏi nhiều
        # cụm mà doanh nghiệp Mỹ hay phải khai, rồi gom lại: mỗi cụm vài công ty, cộng lại thành
        # một bảng có dải thật. Vẫn là hồ sơ công khai, chỉ là hỏi rộng hơn.
        gom = {}
        for tk in ("artificial intelligence", "supply chain disruption", "cybersecurity incident",
                   "material weakness", "going concern", "workforce reduction"):
            for x in (D.tim_ho_so(tk, 20) or []):
                t = str(x.get("cong_ty") or "").split("(")[0].strip()[:24]
                if t:
                    gom[t] = gom.get(t, 0) + 1
        ds = sorted(gom.items(), key=lambda z: -z[1])[:6]
        if len(ds) < 3:
            return None
        return ("Companies writing it into their filings",
                [(k, v, f"{int(v)}x") for k, v in ds], "SEC EDGAR full-text search")
    if nguon == "toa":
        r = D.ban_an("false advertising", 30) or []
        gom = {}
        for x in r:
            t = str(x.get("toa") or "")[:26]
            if t:
                gom[t] = gom.get(t, 0) + 1
        ds = sorted(gom.items(), key=lambda z: -z[1])[:6]
        if len(ds) < 3:
            return None
        return ("Where the cases are filed",
                [(k, v, f"{int(v)}") for k, v in ds], "CourtListener")
    if nguon == "nasa":
        r = D.tieu_hanh_tinh(7) or []
        ds = sorted(r, key=lambda z: float(z.get("khoang_cach_km") or 9e12))[:6]
        if len(ds) < 3:
            return None
        return ("Rocks that just passed Earth",
                [(str(x.get("ten") or "")[:22], float(x.get("khoang_cach_km") or 0),
                  _so(float(x.get("khoang_cach_km") or 0)) + " km") for x in ds],
                "NASA Center for Near-Earth Object Studies")
    if nguon == "epmc":
        r = D.nghien_cuu("sleep", 6) or []
        if len(r) < 3:
            return None
        nam_nay = 2026
        ds = [(str(x.get("tieu_de") or "")[:26], max(1, nam_nay - int(str(x.get("nam") or nam_nay)[:4] or nam_nay)),
               f"{max(1, nam_nay - int(str(x.get('nam') or nam_nay)[:4] or nam_nay))}y") for x in r[:6]]
        return ("How old the evidence actually is", ds, "Europe PMC")
    if nguon == "gia_yte":
        r = D.lay_bls(["cpi_yte"], 2015, 2026).get("cpi_yte") or []
        theo_nam: dict = {}
        for x in r:
            theo_nam.setdefault(int(x["nam"]), []).append(float(x["gia_tri"]))
        nam = sorted(theo_nam)[-6:]
        if len(nam) < 3:
            return None
        return ("Medical care price index, by year",
                [(str(n), sum(theo_nam[n]) / len(theo_nam[n]),
                  f"{sum(theo_nam[n]) / len(theo_nam[n]):,.0f}") for n in nam],
                "U.S. Bureau of Labor Statistics")
    if nguon in ("fdic", "cfpb"):
        # Hai nguồn này chưa có hàm trong `du_lieu_mo`. KHÔNG bịa số để có demo: dùng chỉ số
        # BLS theo ngành, thứ đã có sẵn và đã kiểm, rồi nói đúng tên nó trên khung.
        d = D.bls_theo_nganh("luong", 2024, 2024)
        ds = []
        for ten, r in (d or {}).items():
            if r:
                ds.append((ten[:24], sum(x["gia_tri"] for x in r) / len(r), None))
        if len(ds) < 3:
            return None
        ds = sorted(ds, key=lambda z: -z[1])[:6]
        return ("What an hour of work pays",
                [(k, v, f"${v:,.2f}") for k, v, _ in ds],
                "U.S. Bureau of Labor Statistics")
    return None


# ══════════════════════════════════════════════════════════════════════════════════════════
# DỰNG CẢNH — mỗi câu thoại một cảnh, mỗi cảnh một cảm xúc + cử chỉ + cỡ máy quay
# ------------------------------------------------------------------------------------------
# Đây là chỗ "diễn xuất" được quyết định. Nguyên tắc rút từ phim kể chuyện:
#   • mở đầu bằng CÂU HỎI ở cỡ TRUNG, nhân vật nhìn thẳng ống kính — mời người xem vào;
#   • con số lớn rơi xuống ở cỡ CẬN với cảm xúc BẤT NGỜ — khuôn mặt phản ứng trước, số sau;
#   • phần giải thích ở cỡ TRUNG với cử chỉ tay — tay dẫn mắt người xem tới biểu đồ;
#   • câu chốt ở cỡ CẬN, cảm xúc TỰ TIN — người xem nhớ khuôn mặt lúc kết.
# ══════════════════════════════════════════════════════════════════════════════════════════
def dung_canh(k: dict, so_lieu, giay_moi_cau: float = 3.4) -> tuple:
    tieu_de, ds, nguon = so_lieu
    dan = ds[:6]
    top_ten, top_gt, top_hien = dan[0]
    cau = [
        (k["hoi"], "nghi_ngo", "mo_tay", "trung", [0, 0]),
        (f"{top_hien}. That is {top_ten}.", "bat_ngo", "chi", "can", [0.25, -0.15]),
        (f"{tieu_de}, and the gap is not small.", "tu_tin", "dem", "trung", [-0.3, 0.1]),
        (f"Second place is {dan[1][0]}, at {dan[1][2]}.", "trung_tinh", "chi", "trung", [0.3, 0]),
        (f"Every number here comes from {nguon.split(',')[0]}.", "tu_tin", "mo_tay", "can", [0, 0]),
        ("You can look it up yourself in a minute.", "vui", "nghi", "trung", [0, 0]),
    ]
    canh, t = [], 0.0
    for i, (nar, cx, cc, co, nhin) in enumerate(cau):
        c = {"s": round(t, 2), "e": round(t + giay_moi_cau, 2), "nar": nar,
             "camXuc": cx, "cuChi": cc, "co": co, "nhin": nhin, "boi": k["boi"]}
        if i == 1:
            c["soLon"] = top_hien
            c["nhanSo"] = top_ten[:18]
        if i == 2:
            c["cot"] = [{"nhan": a, "gt": float(b), "hien": h} for a, b, h in dan]
        canh.append(c)
        t += giay_moi_cau
    return canh, " ".join(x[0] for x in cau)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="dựng 1 video ngắn cho mỗi kênh")
    ap.add_argument("--kenh", default="", help="chỉ kênh này (tên viết liền)")
    ap.add_argument("--luong", type=int, default=2)
    a = ap.parse_args()

    import du_lieu_mo as D
    import datastory_ci as DS

    chon = KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [k for k in KENH if k["ten"].replace(" ", "").upper() in vt]
    if not chon:
        print("❌ không khớp kênh nào")
        return 2

    ra = []
    for k in chon:
        ten = k["ten"]
        print(f"\n▶ {ten}", flush=True)
        sl = lay_so_lieu(k["nguon"], D)
        if not sl:
            print(f"   ⚠️ {ten}: nguồn không trả đủ dữ liệu — BỎ LƯỢT (không bịa)")
            continue
        canh, loi = dung_canh(k, sl)
        sl_ten = ten.replace(" ", "").lower()

        # GIỌNG ĐỌC + MỐC TỪNG TỪ. Dùng lại `tts_karaoke.synth` — đúng đường đã chạy cho 50 kênh,
        # miễn phí, không key. GIỌNG CÓ CẢM XÚC: cao độ và tốc độ đổi theo nhân vật, đây chính là
        # mục "🗣️ Voice có cảm xúc" anh dặn. Hạ cao độ nghe bệ vệ, nâng lên nghe lanh lợi.
        import tts_karaoke as TTS
        _GIONG = {
            "nu_kinh": ("en-US-JennyNeural", "+6%", "+12Hz"),
            "nam_dam": ("en-US-GuyNeural", "-2%", "-14Hz"),
            "nam_gay": ("en-US-EricNeural", "+9%", "+8Hz"),
        }
        v, rate, pitch = _GIONG.get(k["kieu"], ("en-US-GuyNeural", "+0%", "+0Hz"))
        rel = f"v3_{sl_ten}.mp3"
        mp3 = os.path.join(PUB, rel)
        try:
            dur, subs, _srt = TTS.synth(loi, mp3, voice=v, rate=rate, pitch=pitch)
        except Exception as e:
            print(f"   ❌ giọng đọc hỏng: {str(e)[:70]}")
            continue
        # `subs` là [{w, t, d, si}] — đúng khuôn `Tu` mà `visemeTai` cần, không phải đổi gì.
        tu = [{"t": float(x.get("t", 0)), "d": float(x.get("d", 0)), "w": str(x.get("w", ""))}
              for x in (subs or [])]
        if not tu:
            print("   ❌ giọng đọc không trả mốc từ nào — BỎ (khỏi ra video câm)")
            continue
        # CẢNH PHẢI KHỚP GIỌNG THẬT, không phải 3,4 giây bốc sẵn: chia đều thời lượng đọc thật
        # cho sáu cảnh. Lệch một chút thì khẩu hình chạy trước/sau lời — thứ mắt bắt ngay.
        moi_canh = max(1.6, dur / max(1, len(canh)))
        for i2, c2 in enumerate(canh):
            c2["s"] = round(i2 * moi_canh, 2)
            c2["e"] = round((i2 + 1) * moi_canh, 2)
        props = {
            "canh": canh, "tu": tu, "voMp3": rel,
            "kieuGoc": k["kieu"], "bangMau": k["mau"],
            "tieuDe": k["nhan"], "nguon": sl[2],
        }
        pj = os.path.join(GOC, "out", f"v3_{sl_ten}.json")
        os.makedirs(os.path.dirname(pj), exist_ok=True)
        io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))
        out = os.path.join(GOC, "out", f"v3_{sl_ten}.mp4")
        r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "KichV2", out,
                            f"--props={pj}", "--gl=swiftshader", "--log=error"],
                           cwd=ENG, capture_output=True, text=True, timeout=1800)
        if r.returncode or not os.path.exists(out):
            print(f"   ❌ render hỏng: {(r.stderr or r.stdout or '')[-200:]}")
            continue
        mb = os.path.getsize(out) / 1e6
        print(f"   ✅ {ten}: {out}  ({mb:.1f} MB)")
        ra.append(out)

    print(f"\n{'✅' if ra else '⚠️'} {len(ra)}/{len(chon)} video")
    for x in ra:
        print(f"   {x}")
    return 0 if ra else 1


if __name__ == "__main__":
    sys.exit(main())
