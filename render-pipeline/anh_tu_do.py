#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ẢNH TỰ DO TỪ WIKIMEDIA — chỉ Public domain và CC0, không gì khác.  (7/9/2026)

── VÌ SAO CHỈ HAI LOẠI GIẤY PHÉP ─────────────────────────────────────────────────────────
Đo giấy phép ảnh của hai chủ thể thật qua API Wikipedia:

    Kodak     20 ảnh -> 10 tự do (8 Public domain + 2 CC0), còn lại CC BY-SA
    Concorde  20 ảnh ->  3 tự do (Public domain),           còn lại CC BY-SA · GFDL

`CC BY-SA` chiếm phần lớn, và nó đòi **tác phẩm phái sinh dùng cùng giấy phép** — tức video
cũng phải mở theo CC BY-SA. Không hợp với kênh kiếm tiền. `CC BY` thì phải hiện chữ ghi công
trên khung, làm bẩn hình và dễ quên. Nên cổng chỉ nhận **Public domain** và **CC0**: hai loại
duy nhất không đòi gì cả.

Một điểm hợp ngách: chủ thể càng CŨ thì ảnh tự do càng nhiều (bản quyền hết hạn). Kodak —
công ty 1888 — có 10; Concorde 1969 chỉ có 3. Đúng ngách "vì sao thứ này biến mất".

── ĐÂY LÀ TẦNG BỔ SUNG, KHÔNG PHẢI TẦNG THIẾT YẾU ────────────────────────────────────────
Hỏng, thiếu ảnh, hay mạng chết thì tập vẫn dựng được bằng nền vẽ code — đúng nguyên tắc bốn
tầng ở §7: tầng cuối không gọi API nên không bao giờ hỏng. Mọi hàm ở đây trả rỗng khi hỏng,
không bao giờ ném lên trên.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import urllib.parse
import urllib.request

# ── USER-AGENT PHẢI CÓ LIÊN HỆ THẬT — ĐÂY LÀ GỐC CỦA MỌI 429 ĐÊM NAY  (8/9/2026) ──
# Chính sách User-Agent của Wikimedia đòi định danh công cụ KÈM một địa chỉ liên hệ.
# Chuỗi cũ ghi "contact via repo owner" — nghe như có liên hệ mà KHÔNG PHẢI liên hệ,
# nên Wikimedia coi ta là bot ẩn danh và bóp cổ ngay. Đo tách bạch bằng `curl`:
#     UA cũ ("contact via repo owner")      -> HTTP 429
#     không UA                              -> HTTP 429
#     UA có URL repo                        -> HTTP 200  (wikipedia · wikidata · commons)
#
# Đây là §13.15 ở mức đắt nhất của cả đêm: em kết luận "Wikipedia đang chặn vì mình gọi
# nhiều", rồi dựng đồng hồ dùng chung, nới nhịp tự động, rút theo thời gian, lùi 6/12/24
# — cả một bộ máy để đi vòng qua một vấn đề mà nguyên nhân là MỘT DÒNG HEADER. Hai bộ
# 142 và 144 mất trắng vì nó, và hồ đề tài đọc về 0 ký tự suốt nhiều giờ.
# (Bộ máy nhịp vẫn giữ: nó đúng và cần khi thật sự bị giới hạn — chỉ là nó không phải
#  thứ đang hỏng.)
#
# KHÔNG đưa email cá nhân của anh vào header gửi bên thứ ba: đo được URL repo là ĐỦ.
UA = {"User-Agent": "MM0-pipeline/1.0 (+https://github.com/braydanamilio-spec/mq-vx-lab)"}
GOC = os.path.dirname(os.path.abspath(__file__))
KHO = os.path.join(GOC, "anh_pd")

# Cổng CỨNG. Chuỗi phải khớp SAU KHI hạ chữ thường và bỏ dấu chấm — Wikipedia viết cùng một
# giấy phép bằng nhiều cách ("CC0", "CC-Zero", "Public domain", "PD-US").
_TU_DO = ("public domain", "cc0", "cc-zero", "pd-us", "pd-old", "no restrictions")
# Không nhận dù có chữ "public domain" ở đâu đó: các biến thể này KÈM điều kiện.
_CAM = ("share", "attribution required", "by-sa", "by-nc", "gfdl", "fair use", "non-free")


def _goi(u: str, timeout: int = 30) -> dict:
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout))


def _tu_do(em: dict) -> bool:
    """Ảnh này có thật sự dùng được không.

    Đọc CẢ BA trường, không chỉ một: `LicenseShortName` là chữ hiển thị, `UsageTerms` mới là
    câu điều kiện, và `AttributionRequired` là cờ riêng. Một ảnh ghi "Public domain" ở tên
    ngắn mà `UsageTerms` nói "share alike" thì KHÔNG dùng được — đọc một trường là đủ để
    lọt đúng loại nguy hiểm nhất.
    """
    v = " ".join(str((em.get(k) or {}).get("value", "")) for k in
                 ("LicenseShortName", "License", "UsageTerms")).lower()
    v = v.replace(".", " ")
    if any(c in v for c in _CAM):
        return False
    if str((em.get("AttributionRequired") or {}).get("value", "")).lower() in ("true", "yes"):
        return False
    return any(t in v for t in _TU_DO)


# Ảnh PD vẫn có thể là CHÂN DUNG NGƯỜI. Ảnh một cái máy ảnh cổ thì vô tư; ảnh một người còn
# sống là chuyện quyền hình ảnh cá nhân, khác hẳn bản quyền. Bộ lọc này thô và cố ý NGHIÊNG
# VỀ PHÍA BỎ: thà mất một ảnh còn hơn đưa mặt một người thật lên kênh.
_NGUOI = re.compile(r"\b(portrait|headshot|selfie|posing|actor|actress|singer|player|"
                    r"ceo|president|founder|speaking at|interview)\b", re.I)
# ── DẤU CẮT CHÂN DUNG CỦA COMMONS  (8/9/2026) ──────────────────────────────────────────
# Bộ 153 («SNC-Lavalin affair») lấy về `File:Justin Trudeau 2019 (3x4 cropped).jpg` và engine
# dùng nó làm NỀN TOÀN KHUNG: mặt một chính khách đang sống phủ kín sau người dẫn vẽ. Anh
# khung thẻ nhỏ là "dẫn chứng"; một chân dung full-bleed thì không còn là dẫn chứng.
#
# `_NGUOI` ở trên là một DANH SÁCH TỪ và tên tệp ấy không chứa từ nào trong đó — §13.20 lần
# nữa. Còn cổng tên-chủ-thể (§19.13) tha vì ảnh NẰM ĐÚNG hạng mục «SNC-Lavalin affair»: ông
# ấy là nhân vật trung tâm của vụ việc, nên hạng mục khớp thật.
#
# Quy luật sinh ra ngoại lệ nằm ở chỗ khác và nó hẹp, chính xác: Commons đặt tên bản cắt
# chân dung bằng TỈ LỆ — `(3x4 cropped)` · `(4x3 cropped)` · `(1x1 cropped)`. Không ảnh
# CẢNH nào mang dấu ấy, vì cắt theo tỉ lệ chỉ có nghĩa với một khuôn mặt.
_CAT_CHAN_DUNG = re.compile(r"\(\s*\d\s*[x×]\s*\d[^)]{0,12}crop", re.I)
# Rác kỹ thuật của Wikipedia: biểu tượng, cờ, mũi tên tăng giảm, bản đồ SVG trống.
# `logo` ĐÃ BỊ BỎ khỏi danh sách này (7/9/2026). Anh: *"mấy hình ảnh logo … liên quan KODAK
# … cho vào khi nói"* — và đo ra 5 logo Kodak Public domain đang bị chặn bởi chính chữ ấy.
# Rác của Wikipedia (`Commons-logo`) vẫn bị chặn bằng tên riêng của nó, còn logo của chủ thể
# thì để `_dung_chu_the` quyết: tên tệp phải mang tên chủ thể (§19.13). Một chữ chặn cả rác
# lẫn thứ mình cần là một chữ không dùng làm cổng được (§13.22).
_RAC = re.compile(r"(icon|flag|arrow|increase|decrease|symbol|commons-logo|"
                  r"edit-|ambox|question_book|wiki|padlock)", re.I)


def anh_cua(chu_the: str, toi_da: int = 8) -> list:
    """[{ten, url, giay_phep}] — CHỈ ảnh tự do, đã bỏ chân dung người và rác biểu tượng."""
    u = ("https://en.wikipedia.org/w/api.php?action=query&format=json&generator=images"
         f"&titles={urllib.parse.quote(chu_the)}&gimlimit=40&prop=imageinfo"
         "&iiprop=url|extmetadata&iiurlwidth=1000"
         "&iiextmetadatafilter=License|LicenseShortName|"
         "UsageTerms|AttributionRequired|ImageDescription|Categories|ObjectName")
    try:
        d = _goi(u)
    except Exception:
        return []
    ra = []
    for p in (d.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        em = ii.get("extmetadata") or {}
        ten = str(p.get("title") or "")
        url = str(ii.get("url") or "")
        # Đuôi tệp phải đọc từ TÊN TỆP, không từ URL: URL Wikimedia kết thúc bằng tham số
        # truy vấn ("...?width=800&...original"), nên `url.endswith(".jpg")` trượt SẠCH — bộ
        # lọc trả 0 ảnh cho mọi chủ thể trong khi cổng giấy phép vẫn nói `TỰ DO? True`.
        # Cổng đúng, phép kiểm cạnh nó sai, và triệu chứng giống hệt "không có ảnh nào".
        # ── SVG ĐƯỢC NHẬN QUA BẢN PNG DO WIKIMEDIA DỰNG  (7/9/2026) ──────────────────
        # Engine dán ảnh bitmap nên bản đầu loại thẳng `.svg`. Nhưng logo của công ty gần như
        # LUÔN là SVG, và đó đúng là thứ hợp nhất với một tập nói về công ty ấy. Wikimedia tự
        # dựng PNG khi mình xin `iiurlwidth` — hỏi API lấy `thumburl`, đừng tự ghép đường
        # `/thumb/` (ghép tay trả `HTTP 400 Use thumbnail sizes listed on…`, §13.8).
        _duoi = os.path.splitext(ten.lower())[1]
        _mark = False
        if _duoi == ".svg":
            _th = str(ii.get("thumburl") or "")
            if not _th:
                continue
            url, _mark = _th, True
        elif _duoi not in (".jpg", ".jpeg", ".png"):
            continue                      # gif/ogg/pdf: không dán được
        if _RAC.search(ten) or _NGUOI.search(ten) or _CAT_CHAN_DUNG.search(ten):
            continue
        mo = str((em.get("ImageDescription") or {}).get("value", ""))
        if _NGUOI.search(mo):
            continue
        if not _tu_do(em):
            continue
        cat = str((em.get("Categories") or {}).get("value", ""))
        ten_ob = str((em.get("ObjectName") or {}).get("value", ""))
        ra.append({"ten": ten, "url": url, "cat": cat, "ob": ten_ob, "mark": _mark,
                   "giay_phep": str((em.get("LicenseShortName") or {}).get("value", "?"))})
    return _dung_chu_the(ra, chu_the)[:toi_da]


def _dung_chu_the(ds: list, chu_the: str) -> list:
    """Giữ ảnh NÓI VỀ chính chủ thể; bỏ ảnh chỉ đứng cạnh nó trong bài.

    ── VÌ SAO KHÔNG LIỆT KÊ TỪ  (7/9/2026) ───────────────────────────────────────────────
    `GeorgeEastman2.jpg` lọt qua bộ lọc chân dung vì tên tệp là một TÊN NGƯỜI — không chứa
    `portrait`, `headshot` hay bất kỳ từ nào trong danh sách. Thêm "GeorgeEastman" vào danh
    sách thì mai `Akio Morita` (Betamax) lại lọt: danh sách ngoại lệ là danh sách vô hạn
    (§13.9). Phải tìm LUẬT sinh ra ngoại lệ.

    Đo trên 4 chủ thể thì luật ấy nằm sẵn trong `Categories` của Wikimedia:

        Eastman Kodak HQ 1900   -> `... | Kodak | Featured pictures of New York ...`
        GeorgeEastman2          -> `Retouched pictures | PD-Bain | George Eastman | ...`

    Ảnh CỦA chủ thể được xếp vào hạng mục mang tên chủ thể; ảnh của một người/vật liên quan
    thì xếp theo tên NGƯỜI/VẬT ấy. Đó là câu hỏi "hình này nói về ai", đúng thứ cần hỏi.

    Nới một lần sau khi đọc tay các ca bị loại: *"Two women holding a sign … Take a Kodak
    with you"* là quảng cáo Kodak 1917 THẬT nhưng hạng mục chỉ ghi `Autochromes; Fashion in
    1917`. Tên tệp thì có chữ Kodak. Nên xét cả TÊN và ObjectName — vẫn loại `GeorgeEastman2`
    (tên không có "kodak") và `Lockheed L-2000 mockup` khi hỏi về Concorde (một máy bay KHÁC,
    đúng thứ anh gọi là "râu ông nọ cắm cằm bà kia").

    Lọc sạch trơn thì TRẢ NGUYÊN danh sách: "không ảnh nào đúng chủ thể" và "phép lọc của tôi
    không với tới" trông giống hệt nhau, và bỏ hết luôn là hướng sai (§15.6).
    """
    kho = [k for k in re.split(r"[^a-z0-9]+", chu_the.split(" (")[0].lower())
           if len(k) > 2 and k not in ("the", "and", "for")]
    if not kho:
        return ds
    giu = [a for a in ds
           if any(k in (a["cat"] + " " + a["ten"] + " " + a["ob"]).lower() for k in kho)]
    return giu or ds


def _the_logo(d: str) -> str:
    """Dựng logo thành TẤM DỌC có nền, thay vì để nó bị `objectFit: cover` cắt méo.

    ── VÌ SAO KHÔNG DÁN THẲNG  (7/9/2026) ────────────────────────────────────────────────
    Logo là một dấu hiệu PHẲNG, nền trong suốt, tỉ lệ thường rất ngang (5:1). Panel là khung
    DỌC 1080×1920 và engine đặt ảnh bằng `objectFit: cover` — dán thẳng thì nó phóng theo
    chiều ngang tới khi lấp đủ chiều cao, tức cắt mất hai đầu chữ và phóng to gấp mấy lần.
    Cùng phép tính đã đo ở §18.13, chỉ khác là ở đây tỉ lệ còn lệch hơn nhiều.

    Nên đóng khung nó: nền sáng đúng khổ dọc, logo đặt giữa, chiếm 62% bề ngang. Đó là cách
    một tấm thẻ hiệu bài được dựng, và nó đọc ra "đây là công ty đang nói tới" trong nửa giây.
    """
    try:
        from PIL import Image
    except Exception:
        return d
    try:
        lg = Image.open(d).convert("RGBA")
        W, H = 768, 1344
        nen = Image.new("RGB", (W, H), "#F2EFE9")
        r = min(W * 0.62 / lg.width, H * 0.30 / lg.height)
        lg = lg.resize((max(1, int(lg.width * r)), max(1, int(lg.height * r))), Image.LANCZOS)
        nen.paste(lg, ((W - lg.width) // 2, (H - lg.height) // 2), lg)
        moi = os.path.splitext(d)[0] + "_the.jpg"
        nen.save(moi, "JPEG", quality=90, optimize=True)
        return moi
    except Exception as e:
        print(f"   ⚠ dựng thẻ logo hỏng ({str(e)[:40]}) — dùng ảnh gốc")
        return d


def tai_ve(anh: dict) -> str:
    """Tải một ảnh về kho cục bộ. Trả đường dẫn, hoặc "" khi hỏng — KHÔNG ném lên trên."""
    try:
        os.makedirs(KHO, exist_ok=True)
        k = hashlib.sha1(anh["url"].encode("utf-8")).hexdigest()[:20]
        duoi = os.path.splitext(urllib.parse.urlparse(anh["url"]).path)[1].lower() or ".jpg"
        d = os.path.join(KHO, k + duoi)
        if os.path.exists(d) and os.path.getsize(d) > 4096:
            return _the_logo(d) if anh.get("mark") else d
        r = urllib.request.Request(anh["url"], headers=UA)
        b = urllib.request.urlopen(r, timeout=45).read()
        if len(b) < 4096:                 # ảnh quá nhỏ gần như luôn là biểu tượng
            return ""
        io.open(d, "wb").write(b)
        return _the_logo(d) if anh.get("mark") else d
    except Exception:
        return ""
