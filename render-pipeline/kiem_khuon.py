#!/usr/bin/env python3
"""Cổng CHỐNG LẶP KHUÔN LỜI — đo cái YouTube thật sự nhìn vào.

31/8 — Anh hỏi cách làm template đa dạng để không vi phạm chính sách YouTube. Đo trước khi
thiết kế, và con số nói ngược lại trực giác: 52% câu trong 25 video dùng KHUÔN đã xuất hiện ở
video khác. Khuôn nặng nhất lặp 18 lần — "«tên» is straight from «nguồn», not from me".

Chính sách "inauthentic content" (YouTube làm rõ 16/7/2026) liệt kê đúng những thứ ấy:
  · "Similar or repetitive content with ... minimal variation"
  · "Videos where characters are put in the same situation over and over again with the same
     outcome"
  · "Image slideshows, TEMPLATED STORYLINES, or scrolling text with minimal or no narrative"
  · "AI-generated content made with generic or unoriginal templates giving the impression of
     mass production"
Còn thứ ĐƯỢC phép là "content that utilizes creative tools to assist in delivering a unique,
well-researched, or creative narrative".

Nên chỗ nguy hiểm KHÔNG nằm ở bố cục hình. Đổi nhân vật sang phải, đổi màu biểu đồ, đổi dáng
cột — tất cả đều không chạm tới điều chính sách nói. Nó nằm ở LỜI: cùng một câu chuyện kể lại
sáu mươi lần với con số khác.

Cách đo: bỏ mọi tên riêng và con số khỏi câu, phần còn lại là KHUÔN. Hai câu khác hẳn về dữ
liệu mà cùng khuôn thì với người xem — và với bộ máy xét duyệt — là một câu.
"""
import io, json, glob, os, re, sys, collections

# 31/8 — ĐO ĐỘ ĐA DẠNG, KHÔNG ĐO TỈ LỆ TRÙNG.
# Chỉ số đầu tiên tôi chọn — "bao nhiêu phần trăm câu dùng khuôn đã xuất hiện ở chỗ khác" — đo
# sai thứ cần đo. Sau khi thay bốn chuỗi cứng bằng sáu kiểu kể, khuôn lặp nặng nhất giảm từ 18
# lần xuống 3 lần, tức cải thiện sáu lần; nhưng tỉ lệ "câu trùng" lại TĂNG, vì nó đếm mọi khuôn
# xuất hiện từ hai lần trở lên như nhau — một khuôn dùng 2 lần và một khuôn dùng 18 lần bị tính
# ngang nhau. Chỉ số ấy không phân biệt được "hơi lặp" với "công thức".
# Hai con số nói đúng hơn:
#   · ĐỘ ĐA DẠNG = số khuôn khác nhau / số câu. Càng gần 1 càng ít lặp.
#   · KHUÔN NẶNG NHẤT = số lần dùng của khuôn phổ biến nhất. Đây mới là thứ người xem nhận ra,
#     và là thứ chính sách gọi là "characters put in the same situation over and over".
DA_DANG_TOI_THIEU = 0.50   # cứ hai câu phải có ít nhất một khuôn riêng
KHUON_TOI_DA = 3           # một khuôn dùng quá 3 lần trong kho là đã thành công thức


def khuon(cau: str) -> str:
    """Bỏ tên riêng và số, giữ lại bộ xương câu."""
    t = " ".join(str(cau or "").split())
    t = re.sub(r"\b[A-Z][a-zA-Z'&.\-]*\b", "«tên»", t)
    t = re.sub(r"[\d][\d.,]*\s?[KMB%]?", "«số»", t)
    return " ".join(t.split()).lower()


def doc_kho(thu_muc: str = "out") -> list:
    ra = []
    for f in sorted(glob.glob(os.path.join(thu_muc, "v3_*.json"))):
        try:
            d = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        for c in (d.get("canh") or []):
            t = " ".join(str(c.get("nar") or "").split())
            if t:
                ra.append((os.path.basename(f), t))
    return ra


def cham_tap(cau_moi: list, kho: list) -> list:
    """Chấm một tập SẮP dựng: câu nào dùng khuôn đã mòn trong kho thì phải viết lại."""
    dem = collections.Counter(khuon(t) for _, t in kho)
    loi = []
    for c in cau_moi:
        k = khuon(c)
        if len(k) < 12:
            continue
        if dem.get(k, 0) >= KHUON_TOI_DA:
            loi.append(f"khuôn đã dùng {dem[k]} lần trong kho: {c[:64]!r}")
    return loi


def main() -> int:
    kho = doc_kho()
    if not kho:
        print("  ⚠️ kho rỗng"); return 0
    dem = collections.Counter(khuon(t) for _, t in kho)
    tong = sum(dem.values())
    da_dang = len(dem) / max(1, tong)
    nang = dem.most_common(1)[0][1] if dem else 0
    print(f"\n  KHUÔN LỜI — {tong} câu trong {len({f for f, _ in kho})} video\n")
    for k, v in dem.most_common(6):
        if v > 1:
            print(f"   ×{v:3}  {k[:84]}")
    print(f"\n  độ đa dạng   {len(dem)}/{tong} = {da_dang:.0%}   (cần ≥ {DA_DANG_TOI_THIEU:.0%})")
    print(f"  khuôn nặng nhất  ×{nang}                (cần ≤ {KHUON_TOI_DA})")
    xau = []
    if da_dang < DA_DANG_TOI_THIEU:
        xau.append(f"độ đa dạng {da_dang:.0%} dưới ngưỡng")
    if nang > KHUON_TOI_DA:
        xau.append(f"một khuôn dùng {nang} lần — đã thành công thức")
    if xau:
        print(f"  ❌ {' · '.join(xau)}")
        print("     Đây là thứ chính sách gọi là 'templated storylines'. Cần thêm CÁCH KỂ, "
              "không phải thêm màu.")
        return 1
    print("  ✅ đạt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
