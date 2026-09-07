#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHỦ THỂ CÓ THẬT — lấy câu sự thật kiểm chứng được từ Wikipedia.  (7/9/2026)

── VÌ SAO CÓ TỆP NÀY ──────────────────────────────────────────────────────────────────────
Anh: *"18 channel hiện tại... hơi khô khan, đọc ko ra gì, ko phải cái người ta muốn coi"*.
Anh đúng, và cái khô là do THIẾT KẾ chứ không do dựng kém: mười tám kênh ấy đều là kênh
ĐO LƯỜNG — *bao to · bao ồn · bao nặng · bao lâu*. Không có câu chuyện nào trong "một sân
bóng dài bao nhiêu", nên không có lý do để ai ở lại.

Bốn tệp tiêu đề anh gửi (14.103 tiêu đề) nói ngược lại: **17% mở bằng một CÁI TÊN CÓ THẬT**,
12% là *"How X did Y"*. Chủ thể là một thứ đã xảy ra ngoài đời — Dolly, MH370, Concorde,
Theranos. Đó vừa là chỗ có câu chuyện, vừa là chỗ ý tưởng không bao giờ cạn.

── VÌ SAO KHÔNG DÙNG WIKIDATA ─────────────────────────────────────────────────────────────
Phản xạ đầu của em là Wikidata: có cấu trúc, dễ đọc máy. Đo thật trên 8 chủ thể thì nó cho
**~2 sự kiện có số mỗi chủ thể**, Segway cho 0 — trong khi một tập cần 10–20. Wikidata giữ
những gì ĐIỀN ĐƯỢC VÀO Ô; câu chuyện thì nằm ở THÂN BÀI. Đo lại trên thân bài: Concorde 38
câu có số, MH370 31, Theranos 23, Chernobyl 19.

── RANH GIỚI KHÔNG ĐƯỢC VƯỢT ──────────────────────────────────────────────────────────────
Mọi con số đi vào sản phẩm phải là chuỗi **trích nguyên văn** từ bài, và hàm `kiem()` đối
chiếu ngược lại nguồn trước khi cho qua. AI được phép DIỄN ĐẠT quanh con số; nó không bao
giờ được cấp một con số. Thiếu dữ liệu thì trả rỗng và bỏ lượt — thà mất một video còn hơn
mất uy tín cả kênh (chép đúng ranh giới của `the_he_2.py`).
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

UA = {"User-Agent": "MM0-pipeline/1.0 (youtube explainer; contact via repo owner)"}

# Đơn vị PHẢI có mặt thì con số mới "cảm được" — một năm trần (1996) không nói lên quy mô.
# Danh sách này cố ý HẸP: rộng ra thì nhặt cả số trang, số hiệu, số chú thích.
_DV = (r"%|percent|million|billion|trillion|thousand|km|kilometres?|miles?|kg|kilograms?|"
       r"pounds?|tons?|tonnes?|years?|months?|days?|hours?|minutes?|seconds?|people|"
       r"passengers?|crew|deaths?|dollars?|USD|feet|foot|metres?|meters?|degrees?")
_CAU = re.compile(r"[^.\n]*?\b\d[\d,\.]*\s*(?:" + _DV + r")\b[^.\n]*\.")
_SO = re.compile(r"\b\d[\d,\.]*\b")


def _goi(url: str, timeout: int = 25) -> dict:
    r = urllib.request.Request(url, headers=UA)          # §13.15: thiếu User-Agent -> CDN chặn 403
    return json.load(urllib.request.urlopen(r, timeout=timeout))


def bai_viet(ten: str) -> str:
    """Thân bài Wikipedia dạng chữ thuần. `redirects=1` là bắt buộc.

    Bản đầu của em thiếu nó và bốn trong tám chủ thể trả về CHUỖI RỖNG — em suýt kết luận
    "Wikipedia không có bài về Benjamin Franklin". Trang đổi hướng trả `pages` không có
    `extract`, và rỗng thì trông y hệt không tồn tại (§15.2).
    """
    u = ("https://en.wikipedia.org/w/api.php?action=query&format=json&redirects=1"
         f"&prop=extracts&explaintext=1&titles={urllib.parse.quote(ten)}")
    try:
        p = list((_goi(u).get("query") or {}).get("pages", {}).values())
        return (p[0].get("extract") or "") if p else ""
    except Exception:
        return ""


def cau_su_that(van: str, toi_da: int = 40) -> list[dict]:
    """Câu có SỐ KÈM ĐƠN VỊ, kèm chính con số để cổng đối chiếu ngược."""
    ra, thay = [], set()
    for c in _CAU.findall(van):
        c = " ".join(c.split())
        if not (34 < len(c) < 215) or c in thay:
            continue
        ds = [x for x in _SO.findall(c) if len(x) > 1 or x != "1"]
        if not ds:
            continue
        thay.add(c)
        ra.append({"cau": c, "so": ds[0], "moi_so": ds})
        if len(ra) >= toi_da:
            break
    return ra


def kiem(so: str, nguon: str) -> bool:
    """Con số này có THẬT nằm trong nguồn không.

    Cổng cuối trước khi một con số được phép lên màn hình. So trên chuỗi đã bỏ dấu phẩy để
    `239` khớp `239` lẫn `2,39` viết khác — nhưng KHÔNG nới hơn thế: nới nữa thì `39` khớp
    `1939` và cổng thành vô dụng.
    """
    if not so:
        return False
    g = so.replace(",", "")
    return g in nguon.replace(",", "")


def ho_so(ten: str) -> dict:
    """{ten, van, cau[]} — rỗng khi không đủ sự thật, và KHÔNG đoán bù."""
    van = bai_viet(ten)
    cs = cau_su_that(van)
    return {"ten": ten, "van": van, "cau": cs, "du": len(cs) >= 8}


# ══════════════════════════════════════════════════════════════════════════════════════════
# CỔNG KIỂM MỆNH ĐỀ — thứ chặn "Theranos worked"
# ══════════════════════════════════════════════════════════════════════════════════════════
# ── VÌ SAO KIỂM SỐ LÀ KHÔNG ĐỦ  (đo 7/9/2026) ─────────────────────────────────────────────
# Ghép hook bằng khuôn trên sự thật đã trích, ba câu đầu tiên máy sinh ra:
#
#     "They built it. 60,000 of them are left."   -> 60.000 là CHI PHÍ chương trình Concorde,
#                                                    không phải số máy bay còn lại
#     "Theranos worked. That was the problem."    -> Theranos KHÔNG hoạt động; đó là cả vụ án
#     "What Chernobyl disaster looked like in..." -> vỡ ngữ pháp
#
# Và `kiem()` cho CẢ BA đi qua, vì `60,000` có thật trong bài. Cái sai không nằm ở con số mà
# ở MỆNH ĐỀ gắn vào con số — một chuỗi chữ số đúng có thể mang một câu hoàn toàn bịa.
#
# Ở kênh đo lường, số do Python tính nên không ai gán nghĩa sai được: sai nhất là NHÀM. Ở kênh
# câu chuyện, "Theranos worked" là một khẳng định sai về một vụ án hình sự có thật — không
# phải lỗi thẩm mỹ mà là rủi ro mất kênh. Nên cổng phải đổi đại lượng: từ "con số có trong
# nguồn không" sang "CÂU NÀY có nói quá điều nguồn nói không".
#
# ── BA PHÉP, VÀ VÌ SAO ĐỦ BA ──────────────────────────────────────────────────────────────
#   1. SỐ phải nằm trong ĐÚNG CÂU NGUỒN, không phải trong cả bài. Đây là chỗ "60,000" chết:
#      nó có trong bài, không có trong câu nói về số máy bay còn lại.
#   2. TỪ NỘI DUNG phải bắt rễ ở câu nguồn. Một câu diễn đạt lại được phép đổi cách nói,
#      không được phép mang vào một khái niệm nguồn không có. "worked" chết ở đây.
#   3. PHỦ ĐỊNH phải cùng chiều. Nguồn nói "not approved" mà câu nói "approved" là lật nghĩa
#      trong khi mọi từ đều bắt rễ — phép 2 một mình không bắt được.
#
# Cổng này CHẶT CÓ CHỦ Ý: nó thà chặn một câu diễn đạt hay còn hơn cho qua một câu sai. Đó là
# đánh đổi đúng chiều ở ngách này, và ngược hẳn với ngách hài (§13.8) nơi bắt oan mới là hại.
_DUNG = {
    "the","a","an","of","in","on","at","to","for","and","or","but","is","are","was","were",
    "be","been","it","its","this","that","these","those","as","by","with","from","into",
    "than","then","so","not","no","only","just","about","over","under","more","less","most",
    "least","after","before","when","while","how","what","why","who","which","many","much",
    "one","two","first","last","new","old","still","now","even","also","all","would","could",
    "did","does","do","has","have","had","will","can","may","they","their","them","you","your",
}
_PHU_DINH = re.compile(r"\b(not|never|no|nobody|nothing|none|failed|denied|without|n['’]t)\b", re.I)


def _goc_tu(c: str) -> set:
    """Từ nội dung, đã bỏ đuôi biến hình thô để 'passengers' khớp 'passenger'."""
    ts = re.findall(r"[a-z]+", (c or "").lower())
    ra = set()
    for t in ts:
        if t in _DUNG or len(t) < 3:
            continue
        for d in ("ing", "ed", "es", "s"):
            if len(t) > 4 and t.endswith(d):
                t = t[: -len(d)]
                break
        ra.add(t)
    return ra


def kiem_menh_de(cau_ra: str, cau_nguon: str, san: float = 0.6) -> tuple[bool, str]:
    """(đạt, lý do). `cau_ra` không được khẳng định nhiều hơn `cau_nguon`."""
    if not cau_ra or not cau_nguon:
        return False, "thiếu câu nguồn — không truy ngược được"
    for s in _SO.findall(cau_ra):
        if len(s) > 1 and not kiem(s, cau_nguon):
            return False, f"số «{s}» không có trong CÂU NGUỒN (có thể có ở chỗ khác trong bài)"
    tr, ng = _goc_tu(cau_ra), _goc_tu(cau_nguon)
    if tr:
        la = tr - ng
        if len(tr - la) / len(tr) < san:
            return False, f"từ không bắt rễ ở nguồn: {', '.join(sorted(la)[:4])}"
    if bool(_PHU_DINH.search(cau_ra)) != bool(_PHU_DINH.search(cau_nguon)):
        return False, "lật chiều phủ định so với nguồn"
    return True, "đạt"
