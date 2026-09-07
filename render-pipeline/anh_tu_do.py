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

UA = {"User-Agent": "MM0-pipeline/1.0 (youtube explainer; contact via repo owner)"}
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
# Rác kỹ thuật của Wikipedia: biểu tượng, cờ, mũi tên tăng giảm, bản đồ SVG trống.
_RAC = re.compile(r"(icon|logo|flag|arrow|increase|decrease|symbol|commons-logo|"
                  r"edit-|ambox|question_book|wiki|padlock)", re.I)


def anh_cua(chu_the: str, toi_da: int = 8) -> list:
    """[{ten, url, giay_phep}] — CHỈ ảnh tự do, đã bỏ chân dung người và rác biểu tượng."""
    u = ("https://en.wikipedia.org/w/api.php?action=query&format=json&generator=images"
         f"&titles={urllib.parse.quote(chu_the)}&gimlimit=40&prop=imageinfo"
         "&iiprop=url|extmetadata&iiextmetadatafilter=License|LicenseShortName|"
         "UsageTerms|AttributionRequired|ImageDescription")
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
        if not url or not os.path.splitext(ten.lower())[1] in (".jpg", ".jpeg", ".png"):
            continue                      # bỏ svg/gif/ogg: engine dán ảnh bitmap
        if _RAC.search(ten) or _NGUOI.search(ten):
            continue
        mo = str((em.get("ImageDescription") or {}).get("value", ""))
        if _NGUOI.search(mo):
            continue
        if not _tu_do(em):
            continue
        ra.append({"ten": ten, "url": url,
                   "giay_phep": str((em.get("LicenseShortName") or {}).get("value", "?"))})
        if len(ra) >= toi_da:
            break
    return ra


def tai_ve(anh: dict) -> str:
    """Tải một ảnh về kho cục bộ. Trả đường dẫn, hoặc "" khi hỏng — KHÔNG ném lên trên."""
    try:
        os.makedirs(KHO, exist_ok=True)
        k = hashlib.sha1(anh["url"].encode("utf-8")).hexdigest()[:20]
        duoi = os.path.splitext(urllib.parse.urlparse(anh["url"]).path)[1].lower() or ".jpg"
        d = os.path.join(KHO, k + duoi)
        if os.path.exists(d) and os.path.getsize(d) > 4096:
            return d
        r = urllib.request.Request(anh["url"], headers=UA)
        b = urllib.request.urlopen(r, timeout=45).read()
        if len(b) < 4096:                 # ảnh quá nhỏ gần như luôn là biểu tượng
            return ""
        io.open(d, "wb").write(b)
        return d
    except Exception:
        return ""
