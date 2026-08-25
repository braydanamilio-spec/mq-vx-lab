#!/usr/bin/env python3
"""DỮ LIỆU CHÍNH PHỦ MỸ MỞ — hào cạnh tranh không mua được bằng tiền (25/8/2026).

VẤN ĐỀ ANH ĐẶT RA
-----------------
55 kênh đang chạy đúng công thức mà hàng vạn kênh faceless khác dùng: footage Pexels + chữ động +
giọng AI. Ai cũng lấy được cùng bộ footage đó, nên không có gì để thuật toán ưu ái — sản lượng lớn
mà không khác biệt thì chỉ bị chôn nhanh hơn.

CÁI KHÔNG COPY ĐƯỢC
-------------------
Không phải footage đẹp hơn (ai cũng mua được), mà là **BẢN GHI GỐC hiện trên màn hình**: dòng hợp
đồng liên bang thật, con số trong hồ sơ SEC thật, chỉ số CPI thật. Ba thứ mà kênh stock-footage
không làm được:
  1. họ không có đường TỰ ĐỘNG lấy dữ liệu (API khó, phải viết riêng từng nguồn)
  2. khán giả Mỹ XÁC MINH được — hiện luôn nguồn, đây là thứ xây uy tín nhanh nhất
  3. dữ liệu TỰ CẬP NHẬT — không bao giờ hết đề tài, và mỗi tháng ra số mới

ĐÃ THỬ THẬT (25/8, gọi trực tiếp trước khi viết một dòng code nào):
  ✅ USASpending  — không cần key. Trả về hợp đồng thật: Humana $51,269,205,263 (Bộ Quốc phòng)
  ✅ SEC EDGAR    — không cần key (chỉ cần User-Agent). Apple: doanh thu 11 kỳ báo cáo
  ✅ BLS          — không cần key (25 lượt/ngày; key free lên 500). CPI 24 tháng
  ✅ Archive.org  — không cần key. Phim tư liệu công cộng
  ⚠️ Census       — trả 302, cần key free; ĐỂ LẠI, không chặn việc

MỌI HÀM Ở ĐÂY HỎNG THÌ TRẢ RỖNG, KHÔNG NÉM. Dữ liệu là gia vị, không được làm gãy dây chuyền.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

UA = "MM0-Pipeline/1.0 (research; contact via youtube channel)"
TIMEOUT = 25


def _goi(url: str, data: dict | None = None, tieu_de: dict | None = None):
    """Gọi một API mở. Trả dict/list, hỏng thì None — KHÔNG BAO GIỜ ném lên dây chuyền."""
    try:
        h = {"User-Agent": UA, "Accept": "application/json"}
        h.update(tieu_de or {})
        body = None
        if data is not None:
            body = json.dumps(data).encode()
            h["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=h)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except Exception as e:
        print(f"   ⚠️ dữ liệu mở hỏng ({url.split('/')[2]}): {str(e)[:70]}")
        return None


# ── 1. USASPENDING — mọi đồng tiền liên bang chi ra ─────────────────────────────────────────
def hop_dong_lon(nam: int, n: int = 8, tu_khoa: str = "") -> list[dict]:
    """Hợp đồng liên bang lớn nhất một năm. Trả [{ten, tien, co_quan, mo_ta}].

    Đây là thứ khán giả Mỹ đọc là giận/sốc ngay: tiền thuế của họ, tên công ty thật, con số thật.
    Không kênh stock-footage nào có đường lấy được cái này một cách tự động."""
    loc = {"award_type_codes": ["A", "B", "C", "D"],
           "time_period": [{"start_date": f"{nam}-01-01", "end_date": f"{nam}-12-31"}]}
    if tu_khoa:
        loc["keywords"] = [tu_khoa]
    d = _goi("https://api.usaspending.gov/api/v2/search/spending_by_award/",
             {"filters": loc,
              "fields": ["Award Amount", "Recipient Name", "Awarding Agency",
                         "Description", "Award Type"],
              "page": 1, "limit": max(1, min(50, n)), "sort": "Award Amount", "order": "desc"})
    ra = []
    for x in ((d or {}).get("results") or []):
        ra.append({"ten": str(x.get("Recipient Name") or "").title(),
                   "tien": float(x.get("Award Amount") or 0),
                   "co_quan": str(x.get("Awarding Agency") or ""),
                   "mo_ta": str(x.get("Description") or "")[:160],
                   "nguon": "USAspending.gov"})
    return ra


# ── 2. SEC EDGAR — số liệu trong hồ sơ công ty đại chúng ────────────────────────────────────
# CIK là mã cố định của công ty ở SEC (10 chữ số, đệm 0). Vài mã hay dùng để khỏi phải tra:
CIK = {"apple": "0000320193", "microsoft": "0000789019", "amazon": "0001018724",
       "tesla": "0001318605", "walmart": "0000104169", "coca-cola": "0000021344",
       "mcdonalds": "0000063908", "nike": "0000320187", "boeing": "0000012927",
       "ford": "0000037996", "disney": "0001744489", "netflix": "0001065280"}


def so_lieu_sec(cong_ty: str, chi_tieu: str = "Revenues", n: int = 6) -> list[dict]:
    """Chuỗi số liệu thật từ hồ sơ SEC. Trả [{ky, gia_tri, mau_don}] mới nhất trước.

    `chi_tieu` theo chuẩn US-GAAP: Revenues · NetIncomeLoss · Assets · Liabilities ·
    ResearchAndDevelopmentExpense · EmployeeRelatedLiabilitiesCurrent …"""
    cik = CIK.get(str(cong_ty).lower().strip()) or str(cong_ty).zfill(10)
    d = _goi(f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{chi_tieu}.json")
    if not d:
        return []
    don = (d.get("units") or {})
    khoa = "USD" if "USD" in don else (list(don) or [None])[0]
    if not khoa:
        return []
    # bỏ trùng kỳ (một kỳ có thể xuất hiện ở nhiều biểu mẫu), giữ bản mới nhất
    theo_ky = {}
    for x in don[khoa]:
        k = x.get("end")
        if k and (k not in theo_ky or str(x.get("filed", "")) > str(theo_ky[k].get("filed", ""))):
            theo_ky[k] = x
    ra = [{"ky": k, "gia_tri": float(v.get("val") or 0), "mau_don": str(v.get("form") or ""),
           "ten": d.get("entityName", ""), "nguon": "SEC EDGAR"}
          for k, v in sorted(theo_ky.items(), reverse=True)]
    return ra[:n]


# ── 3. BLS — chỉ số giá, việc làm, lương (số liệu chính thức) ───────────────────────────────
# Mã chuỗi hay dùng. Không cần key: 25 lượt/ngày — thừa cho một phiên render.
# 25/8 — nới từ 5 lên 13 chuỗi: 8 kênh thế hệ 2 cùng ăn nguồn BLS, mà chỉ có 5 chuỗi thì hai kênh
# buộc phải ra CÙNG một video. Mã dưới đây đã gọi thử, cả 13 đều trả dữ liệu.
BLS_CHUOI = {"cpi": "CUUR0000SA0",            # chỉ số giá tiêu dùng (mọi mặt hàng)
             "cpi_thucpham": "CUUR0000SAF1",   # thực phẩm
             "cpi_xang": "CUUR0000SETB01",     # xăng
             "cpi_nha": "CUUR0000SAH1",        # nhà ở
             "that_nghiep": "LNS14000000",     # tỉ lệ thất nghiệp
             "luong_gio": "CES0500000003",     # lương giờ trung bình, khối tư nhân
             "viec_lam": "CES0000000001",      # tổng việc làm phi nông nghiệp
             "cpi_yte": "CUUR0000SAM",         # chi phí y tế
             "cpi_giao_duc": "CUUR0000SAE1",   # giáo dục
             "cpi_di_lai": "CUUR0000SAT",      # đi lại
             "cpi_dien_nuoc": "CUUR0000SAH2",  # điện nước trong nhà
             "cpi_quan_ao": "CUUR0000SAA",     # quần áo
             "cpi_giai_tri": "CUUR0000SAR"}    # giải trí


def chuoi_bls(ten: str, tu_nam: int, den_nam: int, key: str = "") -> list[dict]:
    """Chuỗi thời gian chính thức từ Cục Thống kê Lao động. Trả [{nam, thang, gia_tri}]."""
    ma = BLS_CHUOI.get(ten, ten)
    body = {"seriesid": [ma], "startyear": str(tu_nam), "endyear": str(den_nam)}
    if key:
        body["registrationkey"] = key
    d = _goi("https://api.bls.gov/publicAPI/v2/timeseries/data/", body)
    try:
        diem = d["Results"]["series"][0]["data"]
    except Exception:
        return []
    ra = []
    for x in diem:
        try:
            ra.append({"nam": int(x["year"]), "thang": x.get("periodName", ""),
                       "gia_tri": float(x["value"]), "nguon": "U.S. Bureau of Labor Statistics"})
        except Exception:
            continue
    return list(reversed(ra))          # cũ -> mới, tiện vẽ biểu đồ


# ── 4. ARCHIVE.ORG — phim tư liệu công cộng ────────────────────────────────────────────────
def phim_tu_lieu(tu_khoa: str, n: int = 6) -> list[dict]:
    """Phim công cộng khớp từ khoá. Trả [{id, tieu_de, nam, link}] — tải về được, dùng thoải mái."""
    q = f'({tu_khoa}) AND mediatype:movies AND (licenseurl:*publicdomain* OR collection:prelinger)'
    url = ("https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(
        {"q": q, "fl[]": "identifier", "rows": max(1, min(30, n)), "output": "json"}))
    d = _goi(url)
    ra = []
    for x in (((d or {}).get("response") or {}).get("docs") or []):
        i = x.get("identifier")
        if i:
            ra.append({"id": i, "tieu_de": str(x.get("title") or i)[:90],
                       "nam": x.get("year", ""), "link": f"https://archive.org/details/{i}",
                       "nguon": "Internet Archive (public domain)"})
    return ra


# ── 5. openFDA — thu hồi thuốc / thực phẩm / sự cố thiết bị y tế ────────────────────────────
# Kho lớn nhất trong đám: 29.310 vụ thu hồi thực phẩm, 17.876 thuốc, 25,7 TRIỆU báo cáo thiết bị.
# Không cần key (240 lượt/phút). Đây là loại tin người Mỹ đọc là dừng lại: đồ họ đang ăn/uống.
FDA_KHO = {"thuc_pham": "food/enforcement", "thuoc": "drug/enforcement", "thiet_bi": "device/enforcement"}


def thu_hoi_fda(kho: str = "thuc_pham", n: int = 8, tu_khoa: str = "", nam: int = 0) -> list[dict]:
    """Vụ thu hồi thật. Trả [{cong_ty, ly_do, so_luong, bang, ngay, muc_do}] — mới nhất trước."""
    duong = FDA_KHO.get(kho, kho)
    tim = []
    if tu_khoa:
        tim.append(f'product_description:"{tu_khoa}"')
    if nam:
        tim.append(f"report_date:[{nam}0101+TO+{nam}1231]")
    q = "+AND+".join(tim) if tim else "classification:*"
    d = _goi(f"https://api.fda.gov/{duong}.json?search={q}&limit={max(1, min(50, n))}&sort=report_date:desc")
    ra = []
    for x in ((d or {}).get("results") or []):
        ra.append({"cong_ty": str(x.get("recalling_firm") or "")[:60],
                   "ly_do": str(x.get("reason_for_recall") or "")[:180],
                   "san_pham": str(x.get("product_description") or "")[:160],
                   "so_luong": str(x.get("product_quantity") or ""),
                   "bang": str(x.get("state") or ""), "ngay": str(x.get("report_date") or ""),
                   "muc_do": str(x.get("classification") or ""),
                   "nguon": "openFDA (U.S. Food & Drug Administration)"})
    return ra


# ── 6. NHTSA — triệu hồi xe + khiếu nại của chủ xe ──────────────────────────────────────────
def trieu_hoi_xe(hang: str, dong: str = "", nam: int = 2022) -> list[dict]:
    """Đợt triệu hồi thật của một dòng xe. Trả [{bo_phan, hau_qua, khac_phuc, so_xe}]."""
    u = ("https://api.nhtsa.gov/recalls/recallsByVehicle?"
         f"make={urllib.parse.quote(hang)}&model={urllib.parse.quote(dong or hang)}&modelYear={nam}")
    d = _goi(u)
    ra = []
    for x in ((d or {}).get("results") or []):
        ra.append({"bo_phan": str(x.get("Component") or "")[:80],
                   "hau_qua": str(x.get("Consequence") or "")[:200],
                   "khac_phuc": str(x.get("Remedy") or "")[:200],
                   "so_xe": str(x.get("PotentialNumberofUnitsAffected") or ""),
                   "hang": hang, "dong": dong, "nam": nam,
                   "nguon": "NHTSA (U.S. Dept. of Transportation)"})
    return ra


# ── 7. COURTLISTENER — bản án, vụ kiện ─────────────────────────────────────────────────────
def ban_an(tu_khoa: str, n: int = 6) -> list[dict]:
    """Bản án công khai khớp từ khoá. Trả [{ten_vu, toa, ngay, trich, link}]."""
    u = ("https://www.courtlistener.com/api/rest/v4/search/?"
         + urllib.parse.urlencode({"q": tu_khoa, "type": "o", "order_by": "dateFiled desc"}))
    d = _goi(u)
    ra = []
    for x in ((d or {}).get("results") or [])[:n]:
        ra.append({"ten_vu": str(x.get("caseName") or "")[:90],
                   "toa": str(x.get("court") or "")[:70], "ngay": str(x.get("dateFiled") or ""),
                   "trich": str(x.get("snippet") or "")[:200],
                   "link": "https://www.courtlistener.com" + str(x.get("absolute_url") or ""),
                   "nguon": "CourtListener (Free Law Project)"})
    return ra


# ── 8. WORLD BANK — so sánh Mỹ với phần còn lại của thế giới ────────────────────────────────
def chi_so_the_gioi(ma: str = "NY.GDP.PCAP.CD", nam: int = 2023, n: int = 12) -> list[dict]:
    """Xếp hạng quốc gia theo một chỉ số. Trả [{nuoc, gia_tri}] cao->thấp."""
    u = (f"https://api.worldbank.org/v2/country/all/indicator/{ma}?"
         + urllib.parse.urlencode({"format": "json", "date": str(nam), "per_page": "400"}))
    d = _goi(u)
    if not isinstance(d, list) or len(d) < 2:
        return []
    ra = []
    for x in (d[1] or []):
        v, c = x.get("value"), (x.get("country") or {}).get("value")
        # bỏ dòng gộp vùng ("World", "Euro area"…) — chỉ giữ QUỐC GIA có mã 3 ký tự thật
        if v is None or not c or len(str(x.get("countryiso3code") or "")) != 3:
            continue
        ra.append({"nuoc": c, "gia_tri": float(v), "nam": nam,
                   "nguon": "World Bank Open Data"})
    return sorted(ra, key=lambda z: -z["gia_tri"])[:n]


# ── 9. USGS — động đất ─────────────────────────────────────────────────────────────────────
def dong_dat(do_lon: float = 6.0, tu_ngay: str = "2020-01-01", n: int = 10) -> list[dict]:
    """Trận động đất mạnh nhất trong khoảng. Trả [{noi, do_lon, ngay, sau_km}]."""
    u = ("https://earthquake.usgs.gov/fdsnws/event/1/query?"
         + urllib.parse.urlencode({"format": "geojson", "minmagnitude": do_lon,
                                   "starttime": tu_ngay, "orderby": "magnitude",
                                   "limit": max(1, min(50, n))}))
    d = _goi(u)
    ra = []
    for x in ((d or {}).get("features") or []):
        pr = x.get("properties") or {}
        ge = (x.get("geometry") or {}).get("coordinates") or [0, 0, 0]
        ra.append({"noi": str(pr.get("place") or "")[:70], "do_lon": float(pr.get("mag") or 0),
                   "ngay": str(pr.get("time") or ""), "sau_km": round(float(ge[2] or 0), 1),
                   "nguon": "USGS (U.S. Geological Survey)"})
    return ra


# ── 10. WIKIMEDIA COMMONS — ẢNH THẬT, dùng thương mại được ──────────────────────────────────
def anh_commons(tu_khoa: str, rong: int = 900) -> dict | None:
    """Một ảnh THẬT trên Commons, ĐÃ LỌC giấy phép dùng thương mại. Trả {url, giay_phep, tac_gia}.

    Vì sao lọc chứ không lấy bừa: Commons có cả ảnh non-free (fair use). Dùng nhầm là dính bản
    quyền. Chỉ nhận CC / Public domain, và trả kèm tên giấy phép để ghi công trong mô tả."""
    u = ("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "format": "json", "generator": "search", "gsrsearch": tu_khoa,
         "gsrnamespace": "6", "gsrlimit": "6", "prop": "imageinfo",
         "iiprop": "url|extmetadata", "iiurlwidth": str(rong)}))
    d = _goi(u)
    for pg in (((d or {}).get("query") or {}).get("pages") or {}).values():
        ii = (pg.get("imageinfo") or [{}])[0]
        em = ii.get("extmetadata") or {}
        gp = str((em.get("LicenseShortName") or {}).get("value", ""))
        if str((em.get("NonFree") or {}).get("value", "0")) not in ("0", ""):
            continue
        if not any(k in gp for k in ("CC", "Public domain", "CC0")):
            continue
        return {"url": ii.get("thumburl") or ii.get("url"), "giay_phep": gp,
                "tac_gia": str((em.get("Artist") or {}).get("value", ""))[:120],
                "ten": str(pg.get("title") or ""), "nguon": "Wikimedia Commons"}
    return None


# ── 11. SEC FULL-TEXT — tìm CHỮ trong hồ sơ công ty (khác hẳn số liệu XBRL) ─────────────────
def tim_ho_so(tu_khoa: str, tu_ngay: str = "", n: int = 8) -> list[dict]:
    """Tìm nguyên văn trong hồ sơ SEC. Trả [{cong_ty, mau_don, ngay, link}].

    Đây là góc không ai làm tự động: công ty BUỘC phải khai rủi ro bằng chữ trong 10-K/8-K. Gõ
    "layoff", "data breach", "we may lose" là ra danh sách công ty tự khai — dẫn chứng cứng."""
    than = {"q": f'"{tu_khoa}"', "forms": "10-K,10-Q,8-K"}
    if tu_ngay:
        than["dateRange"] = "custom"; than["startdt"] = tu_ngay
    d = _goi("https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode(than))
    ra = []
    for x in ((((d or {}).get("hits") or {}).get("hits")) or [])[:n]:
        src = x.get("_source") or {}
        ten = (src.get("display_names") or [""])[0]
        ma = str(x.get("_id") or "")
        ra.append({"cong_ty": str(ten)[:70], "mau_don": str(src.get("form") or ""),
                   "ngay": str(src.get("file_date") or ""),
                   "link": f"https://www.sec.gov/Archives/edgar/data/{ma.replace(':', '/')}",
                   "nguon": "SEC EDGAR full-text search"})
    return ra


# ── 12. NASA — tiểu hành tinh bay sát Trái Đất ─────────────────────────────────────────────
def tieu_hanh_tinh(tu_ngay: str, den_ngay: str = "", key: str = "DEMO_KEY", n: int = 10) -> list[dict]:
    """Vật thể sát Trái Đất trong khoảng ngày. Trả [{ten, duong_kinh_m, toc_do_kmh, cach_km}]."""
    u = ("https://api.nasa.gov/neo/rest/v1/feed?" + urllib.parse.urlencode(
        {"start_date": tu_ngay, "end_date": den_ngay or tu_ngay, "api_key": key or "DEMO_KEY"}))
    d = _goi(u)
    ra = []
    for _ngay, ds in sorted(((d or {}).get("near_earth_objects") or {}).items()):
        for x in ds:
            dk = ((x.get("estimated_diameter") or {}).get("meters") or {})
            ca = (x.get("close_approach_data") or [{}])[0]
            ra.append({"ten": str(x.get("name") or "").strip("() "),
                       "duong_kinh_m": round(float(dk.get("estimated_diameter_max") or 0)),
                       "toc_do_kmh": round(float((ca.get("relative_velocity") or {}).get("kilometers_per_hour") or 0)),
                       "cach_km": round(float((ca.get("miss_distance") or {}).get("kilometers") or 0)),
                       "nguy_hiem": bool(x.get("is_potentially_hazardous_asteroid")),
                       "ngay": _ngay, "nguon": "NASA JPL / CNEOS"})
    return sorted(ra, key=lambda z: -z["duong_kinh_m"])[:n]


# ── 13. FEC — tiền vận động tranh cử ───────────────────────────────────────────────────────
def tai_tro(ky: int = 2024, bang: str = "", key: str = "DEMO_KEY", n: int = 10) -> list[dict]:
    """Ứng viên gom tiền nhiều nhất một kỳ. Trả [{ten, dang, bang, thu, chi}].

    KEY: đăng ký free ở api.data.gov — MỘT key dùng được cho cả FEC lẫn NASA và nhiều API .gov
    khác (1.000 lượt/giờ). DEMO_KEY chỉ 30 lượt/giờ, đủ thử chứ không đủ chạy hằng ngày."""
    than = {"api_key": key or "DEMO_KEY", "sort": "-receipts", "per_page": str(max(1, min(50, n))),
            "election_year": str(ky), "sort_hide_null": "true"}
    if bang:
        than["state"] = bang
    d = _goi("https://api.open.fec.gov/v1/candidates/totals/?" + urllib.parse.urlencode(than))
    ra = []
    for x in ((d or {}).get("results") or []):
        ra.append({"ten": str(x.get("name") or "")[:60], "dang": str(x.get("party") or ""),
                   "bang": str(x.get("state") or ""), "thu": float(x.get("receipts") or 0),
                   "chi": float(x.get("disbursements") or 0), "ky": ky,
                   "chuc": str(x.get("office_full") or ""),
                   "nguon": "U.S. Federal Election Commission"})
    return ra


# ══════════════════════════════════════════════════════════════════════════════════════════
# NGUỒN CHO NICHE GIẢI TRÍ / ĐỜI SỐNG (25/8)
# ------------------------------------------------------------------------------------------
# Bộ trên phủ mảng chính phủ - tài chính - pháp lý, nhưng niche viral ở Mỹ còn có đồ ăn, phim,
# game, thể thao, thú cưng… Không có số liệu cho những mảng đó thì kênh lại rơi về "AI bịa", đúng
# cái đang muốn tránh. Mười hai nguồn dưới đây đều đã gọi thật, đều KHÔNG cần key (trừ USDA dùng
# key free api.data.gov), và mỗi cái mở ra một mảng niche riêng.
# ══════════════════════════════════════════════════════════════════════════════════════════

def bai_duoc_doc(nam: int, thang: int, ngay: int, n: int = 12) -> list[dict]:
    """Bài Wikipedia được đọc nhiều nhất một ngày. Trả [{ten, luot_doc, hang}].

    Đây là "nước Mỹ hôm qua quan tâm cái gì" — đo được, không phải đoán: người nổi tiếng, vụ án,
    phim mới, thảm hoạ. Một nguồn nuôi được nhiều niche cùng lúc mà không kênh nào đang khai thác."""
    u = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/"
         f"{nam:04d}/{thang:02d}/{ngay:02d}")
    d = _goi(u)
    BO = {"Main_Page", "Special:Search", "Wikipedia:Featured_pictures"}
    ra = []
    for x in ((((d or {}).get("items") or [{}])[0]).get("articles") or []):
        ten = str(x.get("article") or "")
        if ten in BO or ten.startswith(("Special:", "Wikipedia:", "Portal:")):
            continue
        ra.append({"ten": ten.replace("_", " "), "luot_doc": int(x.get("views") or 0),
                   "hang": int(x.get("rank") or 0),
                   "link": f"https://en.wikipedia.org/wiki/{ten}",
                   "nguon": "Wikimedia pageviews"})
    return ra[:n]


def luot_doc_bai(ten_bai: str, tu: str, den: str) -> list[dict]:
    """Đường cong lượt đọc một bài theo ngày (tu/den dạng YYYYMMDD). Trả [{ngay, luot_doc}]."""
    t = urllib.parse.quote(str(ten_bai).replace(" ", "_"), safe="")
    u = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
         f"all-access/user/{t}/daily/{tu}/{den}")
    d = _goi(u)
    return [{"ngay": str(x.get("timestamp") or "")[:8], "luot_doc": int(x.get("views") or 0),
             "ten": ten_bai, "nguon": "Wikimedia pageviews"}
            for x in ((d or {}).get("items") or [])]


def thanh_phan_mon(mon: str, n: int = 6, key: str = "DEMO_KEY") -> list[dict]:
    """Dinh dưỡng thật của một món (USDA FoodData Central). Trả [{ten, calo, duong, mo, muoi}].

    KEY free ở api.data.gov — cùng key dùng được cho NASA và FEC."""
    u = ("https://api.nal.usda.gov/fdc/v1/foods/search?" + urllib.parse.urlencode(
        {"query": mon, "pageSize": max(1, min(25, n)), "api_key": key or "DEMO_KEY"}))
    d = _goi(u)
    LAY = {"Energy": "calo", "Sugars, total including NLEA": "duong",
           "Total lipid (fat)": "mo", "Sodium, Na": "muoi", "Protein": "dam"}
    ra = []
    for x in ((d or {}).get("foods") or []):
        r = {"ten": str(x.get("description") or "")[:70], "hieu": str(x.get("brandOwner") or "")[:40],
             "nguon": "USDA FoodData Central"}
        for nu in (x.get("foodNutrients") or []):
            k = LAY.get(str(nu.get("nutrientName") or ""))
            if k and k not in r:
                r[k] = float(nu.get("value") or 0)
        ra.append(r)
    return ra


def nghien_cuu(tu_khoa: str, n: int = 6) -> list[dict]:
    """Nghiên cứu y khoa thật (PubMed). Trả [{tieu_de, tap_chi, nam, ma}]."""
    d = _goi("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "term": tu_khoa, "retmode": "json", "retmax": max(1, min(20, n)),
         "sort": "relevance"}))
    ids = (((d or {}).get("esearchresult") or {}).get("idlist") or [])
    if not ids:
        return []
    s2 = _goi("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}))
    kq = ((s2 or {}).get("result") or {})
    ra = []
    for i in ids:
        x = kq.get(i) or {}
        if not x:
            continue
        ra.append({"tieu_de": str(x.get("title") or "")[:180], "tap_chi": str(x.get("source") or "")[:60],
                   "nam": str(x.get("pubdate") or "")[:4], "ma": i,
                   "link": f"https://pubmed.ncbi.nlm.nih.gov/{i}/",
                   "nguon": "PubMed (U.S. National Library of Medicine)"})
    return ra


def thong_ke_mlb(nam: int = 2025, n: int = 12) -> list[dict]:
    """Đội bóng chày + thành tích thật (MLB StatsAPI). Trả [{doi, thang, thua, ty_le}]."""
    d = _goi(f"https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season={nam}")
    ra = []
    for kh in ((d or {}).get("records") or []):
        for t in (kh.get("teamRecords") or []):
            ra.append({"doi": str((t.get("team") or {}).get("name") or ""),
                       "thang": int(t.get("wins") or 0), "thua": int(t.get("losses") or 0),
                       "ty_le": float(t.get("winningPercentage") or 0), "nam": nam,
                       "nguon": "MLB StatsAPI"})
    return sorted(ra, key=lambda z: -z["thang"])[:n]


def thong_ke_nba(mua: str = "2024-25", chi_tieu: str = "PTS", n: int = 12) -> list[dict]:
    """Cầu thủ dẫn đầu NBA theo một chỉ tiêu. Trả [{ten, doi, gia_tri}]."""
    u = ("https://stats.nba.com/stats/leagueleaders?" + urllib.parse.urlencode(
        {"LeagueID": "00", "PerMode": "PerGame", "Scope": "S", "Season": mua,
         "SeasonType": "Regular Season", "StatCategory": chi_tieu}))
    d = _goi(u, tieu_de={"Referer": "https://www.nba.com/", "Origin": "https://www.nba.com"})
    rs = ((d or {}).get("resultSet") or {})
    cot = [str(c) for c in (rs.get("headers") or [])]
    ra = []
    for h in (rs.get("rowSet") or [])[:n]:
        r = dict(zip(cot, h))
        ra.append({"ten": str(r.get("PLAYER") or ""), "doi": str(r.get("TEAM") or ""),
                   "gia_tri": float(r.get(chi_tieu) or 0), "chi_tieu": chi_tieu, "mua": mua,
                   "nguon": "NBA Stats"})
    return ra


def game_steam(n: int = 12) -> list[dict]:
    """Game Steam có người chơi thật 2 tuần qua. Trả [{ten, dang_choi, so_huu}] — cao->thấp.

    Khác hẳn "top game" báo chí: đây là SỐ NGƯỜI THẬT SỰ MỞ GAME, nên lộ ra game nổi tiếng mà
    không ai chơi, và game im lặng mà đông người."""
    d = _goi("https://steamspy.com/api.php?request=top100in2weeks")
    ra = []
    for _ma, x in (d or {}).items():
        if not isinstance(x, dict):
            continue
        ra.append({"ten": str(x.get("name") or "")[:60],
                   "dang_choi": int(x.get("ccu") or 0),
                   "so_huu": str(x.get("owners") or "").replace(" .. ", "–"),
                   "gia": (int(x.get("price") or 0) / 100.0),
                   "nguon": "SteamSpy"})
    return sorted(ra, key=lambda z: -z["dang_choi"])[:n]


def muc_tieu_thu(nam: int = 2024, hang: str = "Toyota", n: int = 12) -> list[dict]:
    """Mức tiêu thụ xăng CHÍNH THỨC do EPA đo. Trả [{xe, thanh_pho, xa_lo, ket_hop}].

    fueleconomy.gov mặc định trả XML và TỪ CHỐI `Accept: text/xml` bằng 406 — phải xin JSON."""
    def _js(u):
        return _goi(u, tieu_de={"Accept": "application/json"})

    def _ds(x):
        """API trả 1 phần tử thì là dict, nhiều phần tử mới là list — phải chuẩn hoá."""
        v = ((x or {}).get("menuItem")) or []
        return v if isinstance(v, list) else [v]

    ra = []
    for m in _ds(_js(f"https://www.fueleconomy.gov/ws/rest/vehicle/menu/model?year={nam}"
                     f"&make={urllib.parse.quote(hang)}"))[:n]:
        ten_m = str(m.get("value") or "")
        op = _ds(_js(f"https://www.fueleconomy.gov/ws/rest/vehicle/menu/options?year={nam}"
                     f"&make={urllib.parse.quote(hang)}&model={urllib.parse.quote(ten_m)}"))
        if not op:
            continue
        xe = _js(f"https://www.fueleconomy.gov/ws/rest/vehicle/{op[0].get('value')}")
        if not xe:
            continue
        ra.append({"xe": f"{hang} {ten_m}", "nam": nam,
                   "thanh_pho": float(xe.get("city08") or 0),
                   "xa_lo": float(xe.get("highway08") or 0),
                   "ket_hop": float(xe.get("comb08") or 0),
                   "nhien_lieu": str(xe.get("fuelType") or ""),
                   "chi_phi_nam": float(xe.get("fuelCost08") or 0),
                   "nguon": "U.S. EPA fueleconomy.gov"})
    return sorted(ra, key=lambda z: -z["ket_hop"])[:n]


def giong_cho(n: int = 12) -> list[dict]:
    """Danh sách giống chó + ảnh thật (Dog CEO). Trả [{giong, bien_the, anh}]."""
    d = _goi("https://dog.ceo/api/breeds/list/all")
    ra = []
    for g, bien in sorted(((d or {}).get("message") or {}).items()):
        a = _goi(f"https://dog.ceo/api/breed/{g}/images/random")
        ra.append({"giong": g.title(), "bien_the": [str(b).title() for b in (bien or [])],
                   "anh": str((a or {}).get("message") or ""), "nguon": "Dog CEO API"})
        if len(ra) >= n:
            break
    return ra


def phim_truyen(ten: str, n: int = 6) -> list[dict]:
    """Phim bộ thật (TVmaze). Trả [{ten, nam, dai, trang_thai, diem, the_loai}]."""
    d = _goi("https://api.tvmaze.com/search/shows?q=" + urllib.parse.quote(ten))
    ra = []
    for x in (d or [])[:n]:
        sh = x.get("show") or {}
        ra.append({"ten": str(sh.get("name") or ""),
                   "nam": str(sh.get("premiered") or "")[:4],
                   "dai": str((sh.get("network") or {}).get("name") or
                              (sh.get("webChannel") or {}).get("name") or ""),
                   "trang_thai": str(sh.get("status") or ""),
                   "diem": float(((sh.get("rating") or {}).get("average")) or 0),
                   "the_loai": list(sh.get("genres") or []),
                   "nguon": "TVmaze"})
    return ra


def ho_so_nhac(nghe_si: str, n: int = 8) -> list[dict]:
    """Hồ sơ nghệ sĩ / bản thu (MusicBrainz). Trả [{ten, loai, nuoc, bat_dau}]."""
    d = _goi("https://musicbrainz.org/ws/2/artist?" + urllib.parse.urlencode(
        {"query": nghe_si, "fmt": "json", "limit": max(1, min(25, n))}))
    ra = []
    for x in ((d or {}).get("artists") or []):
        sp = x.get("life-span") or {}
        ra.append({"ten": str(x.get("name") or ""), "loai": str(x.get("type") or ""),
                   "nuoc": str(x.get("country") or ""), "bat_dau": str(sp.get("begin") or ""),
                   "ket_thuc": str(sp.get("end") or ""),
                   "diem_khop": int(x.get("score") or 0),
                   "nguon": "MusicBrainz"})
    return ra


def canh_bao(bang: str = "CA", n: int = 10) -> list[dict]:
    """Cảnh báo thời tiết ĐANG BẬT của Sở Khí tượng Mỹ. Trả [{loai, muc, vung, den_khi}]."""
    d = _goi(f"https://api.weather.gov/alerts/active?area={urllib.parse.quote(bang)}")
    ra = []
    for x in ((d or {}).get("features") or [])[:n]:
        pr = x.get("properties") or {}
        ra.append({"loai": str(pr.get("event") or ""), "muc": str(pr.get("severity") or ""),
                   "gap": str(pr.get("urgency") or ""), "vung": str(pr.get("areaDesc") or "")[:90],
                   "den_khi": str(pr.get("ends") or pr.get("expires") or "")[:16],
                   "bang": bang, "nguon": "NOAA / National Weather Service"})
    return ra


def may_bay(lat1: float = 24, lon1: float = -125, lat2: float = 49, lon2: float = -66,
            n: int = 20) -> list[dict]:
    """Máy bay đang bay trong khung toạ độ (OpenSky). Trả [{hieu, nuoc, cao_m, toc_do_ms}]."""
    u = ("https://opensky-network.org/api/states/all?" + urllib.parse.urlencode(
        {"lamin": lat1, "lomin": lon1, "lamax": lat2, "lomax": lon2}))
    d = _goi(u)
    ra = []
    for st in ((d or {}).get("states") or []):
        try:
            ra.append({"hieu": str(st[1] or "").strip(), "nuoc": str(st[2] or ""),
                       "kinh_do": st[5], "vi_do": st[6],
                       "cao_m": float(st[7] or 0), "toc_do_ms": float(st[9] or 0),
                       "nguon": "OpenSky Network"})
        except Exception:
            continue
    return sorted(ra, key=lambda z: -z["cao_m"])[:n]


def tu_kiem() -> int:
    """Gọi thật cả bốn nguồn và in ra cái nhận được. Chạy trước khi tin bất cứ điều gì."""
    ok = 0
    hd = hop_dong_lon(2024, 3)
    print(f"USASpending : {len(hd)} hợp đồng" + (f" · lớn nhất ${hd[0]['tien']:,.0f} — {hd[0]['ten'][:34]}" if hd else ""))
    ok += bool(hd)
    sec = so_lieu_sec("apple", "Revenues", 3)
    print(f"SEC EDGAR   : {len(sec)} kỳ" + (f" · {sec[0]['ky']} = ${sec[0]['gia_tri']:,.0f}" if sec else ""))
    ok += bool(sec)
    bls = chuoi_bls("cpi_xang", 2023, 2024)
    print(f"BLS         : {len(bls)} điểm" + (f" · {bls[-1]['nam']}-{bls[-1]['thang']} = {bls[-1]['gia_tri']}" if bls else ""))
    ok += bool(bls)
    ar = phim_tu_lieu("factory america", 3)
    print(f"Archive.org : {len(ar)} phim" + (f" · {ar[0]['tieu_de'][:44]}" if ar else ""))
    ok += bool(ar)
    print(f"{'✅' if ok == 4 else '⚠️'} {ok}/4 nguồn trả dữ liệu thật")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(tu_kiem())
