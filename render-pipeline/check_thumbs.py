"""
check_thumbs.py — TỰ KIỂM THUMBNAIL, KHÔNG TỐN TOKEN CLAUDE.

Vì sao có file này: mỗi lần muốn biết "thumbnail đã đẹp chưa" mà phải nhờ Claude render rồi soi
từng ảnh thì tốn token và chậm. Script này làm đúng việc đó bằng máy: dựng ảnh mẫu cho MỌI kênh,
tự bắt lỗi bằng thước đo (không cần AI), và tuỳ chọn chấm bằng Gemini Vision (free tier).

Chạy:
    python3 check_thumbs.py                 # dựng + kiểm bằng thước đo (KHÔNG gọi API, free 100%)
    python3 check_thumbs.py --vision        # + chấm chất lượng bằng Gemini Vision
    python3 check_thumbs.py --open          # mở bảng ảnh tổng hợp để tự nhìn
    python3 check_thumbs.py --stress        # thêm các ca chữ dài xấu nhất (test tràn/chồng chữ)

Đầu ra: out_thumbcheck/SHEET.jpg (bảng ảnh tổng) + báo cáo PASS/FAIL từng kênh ở terminal.

THƯỚC ĐO TỰ ĐỘNG (không cần AI, bắt đúng các lỗi đã từng gặp thật):
  - chữ TRÀN mép: quét cột pixel sát 4 mép, nếu có nét chữ sáng chạm mép -> FAIL
  - ảnh TRỐNG/đơn điệu: độ lệch chuẩn quá thấp -> FAIL (nền phẳng chán)
  - ảnh QUÁ TỐI: sáng trung bình quá thấp -> FAIL
  - TRÙNG MÀU giữa các kênh: 2 kênh cùng màu số liệu -> CẢNH BÁO (rủi ro "nội dung hàng loạt")
"""
from __future__ import annotations
import os
import sys
import json
import argparse
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(os.path.dirname(ROOT), "engine-remotion")
PUB = os.path.join(ENG, "public")
OUT = os.path.join(ROOT, "out_thumbcheck")

# Mẫu thật cho từng nhóm kênh (số liệu/nhãn/hook lấy đúng kiểu dữ liệu engine đó sinh ra).
SAMPLES = [
    # (kênh, accent, accent2, tiêu đề, stat, nhãn, hook)
    ("DATARACE",     "#F5B301", "#22D3EE", "Medical Debt By State",      "1 IN 4",  "ADULTS IN MEDICAL DEBT", "WHICH STATE?"),
    ("STATEWARS",    "#E4562B", "#FFD93D", "The Great State Shift",      "-75,000", "PEOPLE LEFT IN A YEAR",  "NOT CALIFORNIA?"),
    ("MONEYMOVES",   "#2FA84F", "#7CF6C0", "Cost Of Growing Old",        "$104K",   "A YEAR TO GROW OLD",     "CAN YOU AFFORD IT?"),
    ("POWERPLAY",    "#22D3EE", "#F5B301", "Who Owns Retail",            "1 IN 3",  "DOLLARS SPENT HERE",     "WHO OWNS IT?"),
    ("GRIDIRON",     "#FB923C", "#4ADE80", "The Record Contract",        "$450M",   "GUARANTEED MONEY",       "WORTH IT?"),
    ("SCREENKINGS",  "#EC4899", "#38BDF8", "The Box Office Disaster",    "$200M",   "LOST IN ONE WEEKEND",    "WHAT KILLED IT?"),
    ("PAYCHECK",     "#2DD4BF", "#FB7185", "Jobs At 3 AM",               "16M",     "WORK THE NIGHT SHIFT",   "WHAT DO THEY EARN?"),
    ("BODYUSA",      "#7C5CFF", "#5EEAD4", "The Pill Illusion",          "$60B",    "SPENT ON SUPPLEMENTS",   "DO THEY WORK?"),
    ("RIDEUSA",      "#38BDF8", "#FACC15", "Dead Car Brands",            "2.1M",    "SOLD BEFORE THEY DIED",  "REMEMBER THEM?"),
    ("EATSUSA",      "#A3E635", "#F97316", "Sugar In Milkshakes",        "128g",    "SUGAR IN ONE CUP",       "THAT'S 32 SPOONS"),
    ("MAPPEDUSA",    "#059669", "#FDBA74", "Highest Income By State",    "$98,461", "MARYLAND",               "HIGHEST INCOME BY STATE"),
    ("RANKEDUSA",    "#D946EF", "#67E8F9", "Fast Food Ranked",           "$53.1B",  "MCDONALD'S",             "FAST FOOD, RANKED"),
    ("SCALEDUSA",    "#0284C7", "#FDE68A", "How Big Is A Blue Whale",    "30 m",    "BLUE WHALE",             "HOW BIG REALLY?"),
    ("THENNOWUSA",   "#9333EA", "#86EFAC", "Cost Of Living Then vs Now", "+108%",   "GALLON OF GAS",          "$1.51 → $3.14"),
    ("SWARMUSA",     "#0D9488", "#F0ABFC", "How Many Fit",               "92,542",  "ROSE BOWL",              "HOW MANY FIT?"),
    ("PULSEUSA",     "#EA580C", "#FCA5A5", "How Loud",                   "180 dB",  "ROCKET LAUNCH",          "HOW LOUD?"),
    ("CLOCKWORKUSA", "#C2410C", "#FCD34D", "Earth's History",            "1.7 SECONDS", "ALL HUMAN HISTORY",  "24 HOURS = 4.5 BILLION YEARS"),
    ("LONGSHOTUSA",  "#4F46E5", "#A5B4FC", "What Are The Odds",          "1 in 292,201,338", "POWERBALL",     "WHAT ARE THE ODDS?"),
    ("GUESSUSA",     "#84CC16", "#FDE047", "Can You Name This City?",    "",        "",                       ""),
]

# Ca CHỮ XẤU NHẤT có thể xảy ra thật từ Gemini (test tràn/chồng/cắt cụt).
STRESS = [
    ("STRESS-statdai",  "#2FA84F", "#7CF6C0", "X", "$1,284,000,000",
     "IN UNPAID MEDICAL BILLS EVERY SINGLE YEAR", "WHO ACTUALLY ENDS UP PAYING FOR ALL OF THIS?"),
    ("STRESS-tieudedai", "#E4562B", "#FFD93D",
     "The State Americans Are Fleeing The Fastest And It Is Definitely Not California Anymore", "", "", ""),
    ("STRESS-1tu",      "#22D3EE", "#F5B301", "MEGAEXTRAORDINARYUNBELIEVABLE", "", "", ""),
    ("STRESS-hookdai",  "#7C5CFF", "#5EEAD4", "X", "60", "BILLION",
     "AND NOBODY IN THE ENTIRE INDUSTRY WANTS TO TALK ABOUT WHY THAT IS"),
    ("STRESS-rong",     "#A3E635", "#F97316", "", "", "", ""),
]


def render(rows):
    os.makedirs(OUT, exist_ok=True)
    made = []
    for name, a, a2, big, stat, lab, hook in rows:
        props = {"big": big, "kicker": name, "accent": a, "accent2": a2,
                 "stat": stat, "statLabel": lab, "hook": hook}
        pf = os.path.join(PUB, f"_chk_{name}.json")
        json.dump(props, open(pf, "w"))
        dst = os.path.join(OUT, f"{name}.jpg")
        try:
            subprocess.run(["npx", "remotion", "still", "src/index.ts", "DocThumb", dst,
                            f"--props=./{os.path.relpath(pf, ENG)}", "--log=error"],
                           cwd=ENG, check=True, timeout=180)
            made.append((name, dst, a2))
        except Exception as e:
            print(f"  ❌ {name}: render lỗi {str(e)[:70]}")
        finally:
            try:
                os.remove(pf)
            except Exception:
                pass
    return made


def measure(path):
    """Thước đo tự động — KHÔNG gọi API. Trả danh sách lỗi (rỗng = đạt)."""
    from PIL import Image, ImageStat
    im = Image.open(path).convert("L")
    w, h = im.size
    px = im.load()
    bad = []
    # 1. chữ chạm mép -> tràn khung. Chỉ tính pixel RẤT sáng (nét chữ trắng/màu), bỏ nền sáng.
    M = 4
    for side, pts in (("trái",  [(x, y) for x in range(M) for y in range(h)]),
                      ("phải",  [(w - 1 - x, y) for x in range(M) for y in range(h)]),
                      ("trên",  [(x, y) for y in range(M) for x in range(w)]),
                      ("dưới",  [(x, h - 1 - y) for y in range(M) for x in range(w)])):
        hot = sum(1 for x, y in pts if px[x, y] > 205)
        if hot > (h if side in ("trái", "phải") else w) * 0.06:
            bad.append(f"chữ chạm mép {side}")
    st = ImageStat.Stat(im)
    if st.stddev[0] < 26:
        bad.append(f"ảnh phẳng/đơn điệu (lệch chuẩn {st.stddev[0]:.0f})")
    if st.mean[0] < 18:
        bad.append(f"ảnh quá tối (sáng TB {st.mean[0]:.0f})")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vision", action="store_true", help="chấm thêm bằng Gemini Vision")
    ap.add_argument("--stress", action="store_true", help="thêm ca chữ dài xấu nhất")
    ap.add_argument("--open", action="store_true", help="mở bảng ảnh tổng hợp")
    a = ap.parse_args()

    rows = SAMPLES + (STRESS if a.stress else [])
    print(f"🖼️  Dựng {len(rows)} thumbnail mẫu…")
    made = render(rows)

    vkey = None
    if a.vision:
        sys.path.insert(0, ROOT)
        vkey = os.environ.get("GEMINI_API_KEY")
        if not vkey:
            try:
                import firestore_bridge as FB
                ks = FB.read_keys(os.environ.get("OWNER_UID"))
                vkey = ks[0].get("key") if ks else None
            except Exception:
                pass
        print("   Vision:", "BẬT" if vkey else "TẮT (không có key)")

    fails, colors = 0, {}
    print(f"\n{'kênh':<16}{'thước đo':<10}{'Vision':<9}lỗi")
    for name, path, a2 in made:
        bad = measure(path)
        colors.setdefault(a2, []).append(name)
        vtxt = "-"
        if vkey:
            try:
                import qc_vision as QV
                ok, info = QV.check_thumb(path, api_key=vkey)
                vtxt = f"{info.get('score', '?')}"
                if not ok:
                    bad += (info.get("issues") or [])[:2]
            except Exception as e:
                vtxt = "lỗi"
        status = "ĐẠT" if not bad else "LỖI"
        if bad:
            fails += 1
        print(f"{name:<16}{status:<10}{vtxt:<9}{'; '.join(bad)[:70]}")

    dup = {c: n for c, n in colors.items() if len(n) > 1}
    if dup:
        print("\n⚠️  TRÙNG MÀU SỐ LIỆU (rủi ro nhìn như hàng loạt):")
        for c, n in dup.items():
            print(f"   {c}: {', '.join(n)}")

    # bảng ảnh tổng hợp
    try:
        from PIL import Image
        cols, cw, ch, pad = 3, 420, 236, 6
        rowsn = (len(made) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cw + pad * (cols + 1), rowsn * ch + pad * (rowsn + 1)), (17, 17, 17))
        for i, (name, path, _) in enumerate(made):
            sheet.paste(Image.open(path).resize((cw, ch)),
                        (pad + (i % cols) * (cw + pad), pad + (i // cols) * (ch + pad)))
        sp = os.path.join(OUT, "SHEET.jpg")
        sheet.save(sp, quality=88)
        print(f"\n📄 Bảng ảnh tổng: {sp}")
        if a.open:
            subprocess.run(["open", sp], check=False)
    except Exception as e:
        print("   ⚠️ không dựng được bảng ảnh:", str(e)[:60])

    print(f"\n{'✅ TẤT CẢ ĐẠT' if not fails else f'❌ {fails}/{len(made)} ảnh có lỗi'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
