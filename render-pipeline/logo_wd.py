#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LOGO + ẢNH CHÍNH CỦA MỘT THỰC THỂ, TRA THẲNG TỪ WIKIDATA  (8/9/2026)

Anh: *"nói về facebook phải có logo facebook hay trụ sở… có api nào cho lấy ảnh thực tế chính
xác hay logo lên nền videos"*.

VÌ SAO KHÔNG TÌM THEO TỪ KHOÁ NỮA. `anh_tu_do` tìm ảnh theo TÊN rồi lọc — nó trả về ảnh "có
liên quan", không trả về "logo của đúng công ty ấy". Wikidata có thuộc tính riêng cho việc này:

    P154 = logo của tổ chức        P18 = ảnh chính của thực thể

Tra thuộc tính thì ra ĐÚNG MỘT TỆP, không phải một danh sách phải đoán.

BA CỔNG, và cả ba đều sinh ra từ một ca hỏng đo được:

1. NHẬN NHẦM THỰC THỂ. `wbsearchentities("Concorde")` trả `Q970075` = **ga tàu điện ngầm
   Concorde ở Paris**, không phải máy bay. Một logo lấy từ thực thể sai còn tệ hơn không có
   logo — đúng thứ anh gọi là *"râu ông nọ cắm cằm bà kia"* (§19.13). Nên phải soi phần mô tả
   của thực thể và loại những nghĩa rõ ràng không phải chủ thể (ga tàu, phim, bài hát, sách…).

2. GIẤY PHÉP. Tệp nằm trên Commons thì gần như luôn tự do, nhưng `P154` có thể trỏ tới tệp lưu
   CỤC BỘ ở Wikipedia theo diện "non-free logo". Nên vẫn phải hỏi `extmetadata` và chỉ nhận
   PD/CC0 — cùng luật mà `anh_tu_do` đã theo, không nới cho logo.

3. CỠ TỆP. Logo SVG phải kết xuất qua `iiurlwidth` (§19.12), và ảnh gốc trên Commons có thể
   hàng chục MB — hạ cỡ trước khi cất, như `anh_nara` đã làm.
"""
import io
import json
import os
import re
import urllib.parse
import urllib.request

import chu_de as C

GOC = os.path.dirname(os.path.abspath(__file__))
KHO = os.path.join(GOC, "..", "engine-remotion", "public", "anh_pd")

# Nghĩa KHÔNG PHẢI chủ thể: gặp trong mô tả thực thể thì bỏ, vì nó là một Concorde khác.
_NGHIA_LAC = re.compile(
    r"\b(metro|underground|subway|railway station|street|square|bridge|film|movie|song|"
    r"album|novel|book|video game|band|album by|painting|sculpture|given name|surname|"
    r"municipality|commune|village|town in|river|mountain)\b", re.I)


def _goi(u: str) -> dict:
    C._cho_nhip()
    r = urllib.request.Request(u, headers=C.UA)
    return json.load(urllib.request.urlopen(r, timeout=25))


def _khong_dau(t: str) -> str:
    """Bỏ dấu trước khi so — mô tả Wikidata viết «Paris **Métro** station», regex viết `metro`.

    Lần chạy thử đầu tiên trượt đúng ca này: `Concorde` ra `Q970075` = ga tàu điện ngầm Paris,
    và bộ lọc không bắt vì chữ có dấu. Lần ấy thoát nhờ may — thực thể sai không có logo. Một
    thực thể sai CÓ logo thì đã lọt thẳng vào video (§19.13 — "râu ông nọ cắm cằm bà kia").
    """
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def thuc_the_qid(ten: str) -> tuple:
    """(qid, nhãn, mô tả) — hoặc (None, "", "") nếu không tìm được / nghĩa lạc."""
    u = ("https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json"
         "&language=en&limit=5&search=" + urllib.parse.quote(ten))
    for x in (_goi(u).get("search") or []):
        mo = str(x.get("description") or "")
        if _NGHIA_LAC.search(_khong_dau(mo)):
            continue                     # ga tàu Concorde, phim cùng tên… không phải chủ thể
        return x.get("id"), str(x.get("label") or ""), mo
    return None, "", ""


def ten_khac(ten: str) -> list:
    """[tên chính, các TÊN GỌI KHÁC] của thực thể — lấy từ nhãn + `aliases` của Wikidata.

    ── VÌ SAO CẦN  (anh chọn hướng này, 8/9/2026) ─────────────────────────────────────────
    Tầng Commons phải khớp CỤM LIỀN để khỏi nhận nhầm («Midway Pony Express station» cho chủ
    thể «Midway Express»). Nhưng khớp cụm cứng thì loại oan đúng những tấm hay nhất: đo trên
    «MetLife Building» mất hết ảnh **«Pan Am Building»** — mà đó chính là TÊN CŨ của cùng toà
    nhà ấy. Ảnh đúng bị loại vì tên đã đổi.

    Wikidata giữ sẵn danh sách ấy ở `aliases`, nên không phải đoán và không phải chép tay
    (§13.9: nắm quy luật sinh ra ngoại lệ, đừng liệt kê chúng). Hỏng thì trả về danh sách chỉ
    có tên gốc — không được làm đứng đường lấy ảnh (§13.3).
    """
    ra = [str(ten or "").strip()]
    try:
        qid, nhan, _mo = thuc_the_qid(ten)
        if not qid:
            return [x for x in ra if x]
        d = _goi("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json"
                 f"&props=labels|aliases&languages=en&ids={qid}")
        e = ((d.get("entities") or {}).get(qid) or {})
        lb = ((e.get("labels") or {}).get("en") or {}).get("value")
        if lb:
            ra.append(str(lb))
        for a in ((e.get("aliases") or {}).get("en") or []):
            v = str(a.get("value") or "").strip()
            if v:
                ra.append(v)
    except Exception:
        pass
    # khử trùng, giữ thứ tự, và bỏ tên quá ngắn (một chữ 3 ký tự khớp bừa)
    thay, sach = set(), []
    for x in ra:
        k = " ".join(x.lower().split())
        if len(k) >= 4 and k not in thay:
            thay.add(k)
            sach.append(x)
    return sach


def tep_logo(ten: str) -> tuple:
    """(tên tệp logo, tên tệp ảnh chính) trên Commons — chuỗi rỗng nếu không có."""
    qid, _, _ = thuc_the_qid(ten)
    if not qid:
        return "", ""
    d = _goi("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json"
             f"&ids={qid}&props=claims")
    cl = ((d.get("entities") or {}).get(qid) or {}).get("claims") or {}

    def lay(p):
        v = cl.get(p) or []
        try:
            return str(v[0]["mainsnak"]["datavalue"]["value"])
        except Exception:
            return ""
    return lay("P154"), lay("P18")


def anh_tu_tep(ten_tep: str, rong: int = 900) -> tuple:
    """(url ảnh đã kết xuất, tên giấy phép) — chỉ trả url khi giấy phép TỰ DO."""
    if not ten_tep:
        return "", ""
    u = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo"
         "&iiprop=url|extmetadata&iiextmetadatafilter=License|LicenseShortName|UsageTerms"
         f"&iiurlwidth={rong}&titles=" + urllib.parse.quote("File:" + ten_tep))
    p = list(((_goi(u).get("query") or {}).get("pages") or {}).values())
    if not p:
        return "", ""
    ii = (p[0].get("imageinfo") or [{}])[0]
    md = ii.get("extmetadata") or {}
    gp = str((md.get("LicenseShortName") or {}).get("value") or
             (md.get("License") or {}).get("value") or "")
    # CÙNG luật với `anh_tu_do`: chỉ PD/CC0. Không nới cho logo — `P154` có thể trỏ tệp lưu
    # cục bộ ở Wikipedia theo diện "non-free logo", và tệp ấy KHÔNG dùng được.
    tu_do = bool(re.search(r"\b(pd|public domain|cc0|cc[ -]?by)\b", gp, re.I))
    if not tu_do:
        return "", gp
    return str(ii.get("thumburl") or ii.get("url") or ""), gp


def tai_ve(url: str, ten_goi: str) -> str:
    """Tải về `public/anh_pd/` và trả ĐƯỜNG DẪN TƯƠNG ĐỐI mà engine phục vụ được.

    §19.12 đã trả giá hai lần ở đây, nên làm đúng cả hai:
      · đuôi tệp đọc từ TÊN TỆP chứ không từ URL — url Commons kết thúc bằng tham số truy vấn
        nên `url.endswith(".png")` trượt sạch;
      · phải copy vào `public` — engine chỉ phục vụ tệp dưới đó, không thì đường dẫn hợp lệ mà
        ảnh không hiện.
    """
    import hashlib
    if not url:
        return ""
    duoi = ".png"
    m = re.search(r"\.(png|jpe?g|webp|svg)(?:\?|$)", ten_goi + " " + url, re.I)
    if m:
        duoi = "." + m.group(1).lower().replace("jpeg", "jpg")
    if duoi == ".svg":
        duoi = ".png"                 # `iiurlwidth` đã kết xuất SVG -> PNG
    ten = hashlib.sha1((ten_goi + url).encode()).hexdigest()[:20] + duoi
    os.makedirs(KHO, exist_ok=True)
    ra = os.path.join(KHO, ten)
    if not os.path.exists(ra):
        C._cho_nhip()
        r = urllib.request.Request(url, headers=C.UA)
        b = urllib.request.urlopen(r, timeout=30).read()
        with open(ra, "wb") as f:
            f.write(b)
    return "anh_pd/" + ten


def logo_va_anh(chu_the: str) -> list:
    """[đường dẫn logo, đường dẫn ảnh chính] — rỗng nếu không có thứ nào TỰ DO."""
    try:
        lg, anh = tep_logo(chu_the)
    except Exception:
        return []
    # ── TÊN TỆP PHẢI MANG TÊN CHỦ THỂ  (8/9/2026) ───────────────────────────────────────
    # Bộ 153 («SNC-Lavalin affair») lấy về `File:Justin Trudeau 2019 (3x4 cropped).jpg` và
    # engine dùng nó làm NỀN TOÀN KHUNG: ảnh chụp mặt một chính khách đang sống, phủ kín
    # sau người dẫn vẽ. Anh khung thẻ nhỏ là "dẫn chứng"; một chân dung full-bleed thì không.
    #
    # Wikidata trả nó ĐÚNG luật của nó — mục về vụ việc khai P18 là ảnh người liên quan. Sai
    # là ở phía mình: §19.13 đã rút đúng luật *"ảnh phải mang tên THỰC THỂ"* nhưng chỉ áp cho
    # đường Wikimedia Commons, còn đường Wikidata này thì chưa (§6 — vá một nhánh, để nguyên
    # nhánh song song). Sổ `so_anh_nguon.json` dựng sáng nay là thứ cho phép truy ra trong
    # một phút: không có nó thì tên tệp chỉ là một chuỗi băm.
    _tu = {w for w in re.findall(r"[a-z]{3,}", (chu_the or "").lower())
           if w not in ("the", "and", "affair", "scandal", "case", "group", "company",
                        "corporation", "incorporated", "limited", "holdings", "inc", "ltd")}

    def _khop_ten(tep_ten: str) -> bool:
        if not _tu:
            return True
        t = (tep_ten or "").lower()
        return any(w in t for w in _tu)

    ra = []
    for tep in (lg, anh):               # LOGO ĐỨNG TRƯỚC: nhận ra nhanh nhất
        if not tep:
            continue
        if not _khop_ten(tep):
            print(f"   ⚠ bỏ «{str(tep)[:46]}» — tên tệp không mang tên «{chu_the[:28]}»")
            continue
        try:
            url, _gp = anh_tu_tep(tep)
            d = tai_ve(url, tep)
            if d:
                ra.append(d)
        except Exception:
            continue
    return ra
