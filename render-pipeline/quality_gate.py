#!/usr/bin/env python3
"""CỔNG CHẤT LƯỢNG DÙNG CHUNG (23/8/2026) — chuẩn bị cho kênh hàng nghìn video.

Ba việc, đặt chung một chỗ để mọi format (12 loại) và mọi kênh cùng được áp:

1. CHỐNG TRÙNG THEO Ý NGHĨA — sổ chủ đề cũ so khớp CHUỖI và chỉ nhớ 80 mục: tới video thứ 300 là
   vô dụng, mà "Rent in 2025 vs 2015" với "How US rent doubled since 2015" thì chuỗi khác nhau
   hoàn toàn dù cùng một bài. Nay mỗi tiêu đề rút thành BỘ TỪ KHOÁ; bài mới trùng ≥55% từ khoá với
   bất kỳ bài cũ nào là bị loại. Nhớ được vài nghìn mục mà vẫn gọn trong 1 doc.

2. MẠCH KÊNH (series/pillar) — thay vì mỗi video một chủ đề rời rạc, người viết tự gắn nhãn "trụ
   nội dung" cho bài; hệ đếm và ép chọn trụ ĐANG ÍT NHẤT. Kênh có mạch, người xem hết tập này sang
   tập khác, YouTube đọc được chủ đề kênh — đúng thứ vòng xét kiếm tiền nhìn vào.

3. CHUẨN KIẾM TIỀN — chặn trước khi tốn công render: phải có nguồn thật, phải có số liệu, không
   được rơi vào nhóm nội dung dễ bị đánh "tái sử dụng/hàng loạt".

KHÔNG gọi API ngoài, không nhúng model — chạy bằng phép so từ khoá, free 100%.
"""
from __future__ import annotations

import re

# từ quá phổ biến, giữ lại chỉ làm nhiễu phép so
_STOP = {
    "the", "a", "an", "and", "or", "of", "in", "on", "at", "to", "for", "from", "by", "with", "is",
    "are", "was", "were", "be", "been", "this", "that", "these", "those", "it", "its", "as", "how",
    "why", "what", "when", "where", "who", "you", "your", "we", "our", "us", "they", "their", "не",
    "vs", "than", "then", "now", "new", "real", "truth", "about", "into", "over", "under", "most",
    "more", "less", "just", "only", "every", "each", "one", "two", "three", "us", "usa", "american",
    "america", "united", "states",
}
SIM_LIMIT = 0.5           # trùng ≥50% từ khoá của bài NGẮN hơn = coi như cùng bài
MIN_WORDS = 4             # dưới 4 từ khoá thì tín hiệu quá yếu, không dám kết luận
MEMORY = 4000             # nhớ 4000 bài gần nhất mỗi kênh


def fingerprint(text: str) -> list[str]:
    """Tiêu đề -> bộ từ khoá đã chuẩn hoá (bỏ dấu câu, số lẻ, từ phổ biến)."""
    words = re.findall(r"[a-zA-Z][a-zA-Z\-']{2,}", str(text or "").lower())
    out = []
    for w in words:
        w = w.strip("-'")
        if len(w) < 3 or w in _STOP:
            continue
        if w.endswith("ies") and len(w) > 4:
            w = w[:-3] + "y"
        elif w.endswith("es") and len(w) > 4:
            w = w[:-2]
        elif w.endswith("s") and len(w) > 3:
            w = w[:-1]
        if w not in out:
            out.append(w)
    return out[:12]


def similarity(a: list[str], b: list[str]) -> float:
    """Tỉ lệ chồng lấn giữa 2 bộ từ khoá.

    Dùng OVERLAP (chia cho bộ NHỎ hơn) chứ không phải Jaccard: hai tiêu đề cùng nội dung nhưng một
    cái dài một cái ngắn — "Rent 2025 vs 2015" và "How US rent doubled since 2015 in 40 cities" —
    Jaccard cho ra ~0.2 (bỏ lọt), overlap cho ra đúng mức trùng thật."""
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / float(min(len(sa), len(sb)))


def too_similar(title: str, seen: list[list[str]]) -> tuple[bool, float, list[str]]:
    """Bài mới có trùng ý với bài cũ nào không. Trả (có/không, mức trùng cao nhất, bộ từ khoá trùng)."""
    fp = fingerprint(title)
    if len(fp) < MIN_WORDS:
        return False, 0.0, []
    worst, worst_fp = 0.0, []
    for old in seen:
        s = similarity(fp, old)
        if s > worst:
            worst, worst_fp = s, old
    return worst >= SIM_LIMIT, round(worst, 2), worst_fp


def pillar_hint(counts: dict, k: int = 3) -> str:
    """Câu nhắc người viết chọn trụ nội dung ĐANG ÍT tập nhất (giữ mạch kênh cân bằng)."""
    if not counts:
        return ""
    ranked = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]))
    thieu = [f"{n} ({c} tập)" for n, c in ranked[:k]]
    thua = [n for n, c in sorted(counts.items(), key=lambda kv: -kv[1])[:2]]
    return ("\nSERIES BALANCE — this channel already runs these pillars. Choose one of the LEAST "
            "covered and write the next episode in it: " + ", ".join(thieu) +
            (". Avoid the over-used pillars: " + ", ".join(thua) if thua else "") +
            ". Also return a short \"pillar\" field (2-3 words) naming the pillar you chose.")


def money_safe(story: dict) -> list[str]:
    """Chuẩn kiếm tiền YouTube — trả list lỗi (rỗng = đạt). Chặn TRƯỚC khi tốn công render."""
    errs = []
    if not isinstance(story, dict):
        return ["kịch bản rỗng"]
    text = " ".join(str(v) for v in story.values() if isinstance(v, str))
    if len(story.get("sources") or []) < 2:
        errs.append("cần ≥2 nguồn thật (YouTube xét 'nội dung tái sử dụng' nhìn vào đây)")
    if not re.search(r"\d", text):
        errs.append("không có con số nào — bài phân tích phải neo bằng dữ liệu")
    xau = re.findall(r"\b(guaranteed returns?|get rich|cure[sd]? cancer|miracle cure|"
                     r"buy now|click here|subscribe or|100% profit|risk[- ]free money)\b", text, re.I)
    if xau:
        errs.append("câu chữ rủi ro chính sách: " + ", ".join(sorted(set(x.lower() for x in xau))[:3]))
    return errs
