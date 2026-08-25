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
BLS_CHUOI = {"cpi": "CUUR0000SA0",            # chỉ số giá tiêu dùng (mọi mặt hàng)
             "cpi_thucpham": "CUUR0000SAF1",   # thực phẩm
             "cpi_xang": "CUUR0000SETB01",     # xăng
             "cpi_nha": "CUUR0000SAH1",        # nhà ở
             "that_nghiep": "LNS14000000"}     # tỉ lệ thất nghiệp


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
