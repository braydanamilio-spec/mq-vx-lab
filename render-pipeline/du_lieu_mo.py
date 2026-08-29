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
import threading
import time
import os
import urllib.parse
import urllib.request

UA = "MM0-Pipeline/1.0 (research; contact via youtube channel)"
TIMEOUT = 25


# ── KEY MIỄN PHÍ, ĐỌC TỪ MÔI TRƯỜNG ────────────────────────────────────────────────────────
# Hai key này đều free và đều CHỈ nới hạn mức, không mở thêm dữ liệu. Không có key thì mọi hàm
# vẫn chạy, chỉ là chạm trần sớm:
#   BLS_KEY       25 lượt/ngày -> 500      (đăng ký: data.bls.gov/registrationEngine)
#   DATA_GOV_KEY  30 lượt/giờ  -> 1.000    (api.data.gov — MỘT key dùng cho NASA + FEC + USDA)
# Đọc từ môi trường thay vì truyền tay ở từng chỗ gọi: thêm key sau này chỉ cần đặt biến, không
# phải sửa một dòng mã nào.
def key_bls() -> str:
    return os.environ.get("BLS_KEY", "").strip()


def key_data_gov() -> str:
    return os.environ.get("DATA_GOV_KEY", "").strip() or "DEMO_KEY"


# Lỗi TẠM THỜI: máy chủ đang quá tải hoặc chặn nhịp. Thử lại là qua. Khác hẳn 401/403/404 —
# những cái đó thử lại bao nhiêu lần cũng vậy, chỉ tốn thời gian của lane.
_TAM_THOI = ("503", "502", "504", "429", "timed out", "timeout", "reset by peer",
             "temporarily", "connection", "ssl")


# ── NHỊP GỌI TỐI THIỂU THEO TỪNG NGUỒN (28/8/2026) ─────────────────────────────────────────
# Ba nguồn có trần nhịp CÔNG BỐ RÕ, và cả ba đã cắn mình trong ngày:
#   • musicbrainz.org  — 1 lượt/giây. Gọi dày hơn thì trả 503, và `_goi` hiểu 503 là "nguồn hỏng"
#     nên kênh ONE HIT ra 0 video. Đo tay đúng URL ấy với nhịp giãn: 200 OK, dữ liệu đầy đủ.
#     Tức nguồn không hỏng bao giờ — mình tự làm nó từ chối mình.
#   • eutils.ncbi.nlm.nih.gov — 3 lượt/giây. Vượt thì NCBI CHẶN CẢ ĐỊA CHỈ MẠNG nhiều giờ, và
#     trả về một trang HTML "Access Denied" với mã 200. `json.loads` vấp trang đó rồi báo
#     "Expecting value: line 1 column 1" — đọc log thì tưởng mã phân tích hỏng, chứ không ai đoán
#     ra là mình bị cấm cửa. Đã dính thật hôm nay khi đo thử.
#   • wikimedia.org — không công bố số, nhưng 429 ngay khi gọi vài chục lượt liền.
#
# Hãm ở TẦNG CHUNG chứ không ở từng hàm: hàm mới thêm sau này được hưởng mà không phải nhớ, và
# đây đúng là chỗ duy nhất mọi lượt gọi đều đi qua.
_NHIP_NGUON = {
    "musicbrainz.org": 1.1,
    "eutils.ncbi.nlm.nih.gov": 0.4,
    "wikimedia.org": 0.25,
    "dog.ceo": 0.15,
}
_NHIP_LAN_CUOI: dict = {}
_NHIP_KHOA = threading.Lock()


def _cho_den_luot(host: str) -> None:
    """Chờ đủ nhịp tối thiểu của nguồn này trước khi gọi tiếp."""
    cho = 0.0
    for k, giay in _NHIP_NGUON.items():
        if not host.endswith(k):
            continue
        with _NHIP_KHOA:
            con = giay - (time.monotonic() - _NHIP_LAN_CUOI.get(k, 0.0))
            if con > 0:
                cho = con
            _NHIP_LAN_CUOI[k] = time.monotonic() + max(0.0, cho)
        break
    if cho > 0:
        time.sleep(cho)


def _goi(url: str, data: dict | None = None, tieu_de: dict | None = None, lan: int = 3):
    """Gọi một API mở. Trả dict/list, hỏng thì None — KHÔNG BAO GIỜ ném lên dây chuyền.

    25/8 — thêm THỬ LẠI CÓ GIÃN ở tầng chung. Khi 18 lane cùng gọi một nguồn, nguồn đó trả 503
    ngắt quãng và kênh rớt ngẫu nhiên mỗi phiên một cái khác (đo thật khi chạy 8 luồng song song:
    lần thì kênh đồ ăn rớt, lần thì kênh toà án). Vá ở đây thì mọi nguồn được hưởng, khỏi phải
    nhớ vá từng hàm."""
    import random as _rd
    import time as _tg
    h = {"User-Agent": UA, "Accept": "application/json"}
    h.update(tieu_de or {})
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        h["Content-Type"] = "application/json"
    host = url.split("/")[2] if "//" in url else ""
    cuoi = ""
    for i in range(max(1, lan)):
        try:
            _cho_den_luot(host)
            req = urllib.request.Request(url, data=body, headers=h)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                tho = r.read().decode("utf-8", "ignore")
            if tho.lstrip()[:1] not in ("{", "["):
                # Trang HTML trả về với mã 200 = nguồn đang TỪ CHỐI, không phải dữ liệu lạ.
                # Nói thẳng ra thay vì để `json.loads` ném một lỗi cú pháp khó hiểu.
                cuoi = ("nguồn trả về trang HTML thay vì JSON — nhiều khả năng đang CHẶN nhịp gọi"
                        if "blocked" in tho[:900].lower() or "denied" in tho[:900].lower()
                        else "nguồn trả về không phải JSON")
                break
            return json.loads(tho)
        except Exception as e:
            cuoi = str(e)
            if not any(t in cuoi.lower() for t in _TAM_THOI) or i == lan - 1:
                break
            _tg.sleep((1.6 ** i) + _rd.random())
    print(f"   ⚠️ dữ liệu mở hỏng ({host}): {cuoi[:80]}")
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


# ── CHUỖI THEO NGÀNH ────────────────────────────────────────────────────────────────────────
# Mã CES ghép theo khuôn: CES + 2 số ngành + 6 số 0 + đuôi. Đuôi `003` = lương giờ trung bình,
# `001` = số việc làm (nghìn người).
#
# 29/8 — VÌ SAO CẦN. Hai kênh hứa những thứ chuỗi TỔNG không chứng minh nổi:
#   SALARY TRUTH "nghề này thật sự trả bao nhiêu" -> đang vẽ TỔNG SỐ VIỆC LÀM phi nông nghiệp,
#       một con số 157.693,8 không phải lương của bất kỳ ai;
#   JOB DYING    "nghề đang biến mất"             -> đang vẽ TỈ LỆ THẤT NGHIỆP CHUNG, thứ đo
#       người không có việc chứ không đo việc mất đi.
# Chia theo ngành thì cả hai lời hứa đều có số thật đỡ: lương giờ chênh nhau hơn gấp đôi giữa
# ngành cao nhất và thấp nhất, còn chế tạo thì thiếu 4,5 triệu việc so với đỉnh năm 2001.
BLS_NGANH = {"Mining & logging": "10", "Construction": "20", "Manufacturing": "30",
             "Trade & transport": "40", "Information": "50", "Finance": "55",
             "Professional services": "60", "Education & health": "65",
             "Leisure & hospitality": "70", "Other services": "80"}


def bls_theo_nganh(kieu: str, tu_nam: int, den_nam: int) -> dict:
    """{tên ngành: [{nam, thang, gia_tri}]}. `kieu` = "luong" (đô/giờ) hoặc "viec" (nghìn người).

    Đi qua `lay_bls` nên ăn FILE TĨNH trước — API v2 không key chỉ trả 10 năm một lượt, không đủ
    để tìm đỉnh lịch sử (đo thật: hỏi 2001-2025 thì nó cắt còn tới 2010, và "hiện nay" hoá ra là
    số của mười lăm năm trước — sai mà không báo lỗi).
    """
    duoi = "003" if kieu == "luong" else "001"
    ma = {t: f"CES{v}00000{duoi}" for t, v in BLS_NGANH.items()}
    d = lay_bls(list(ma.values()), tu_nam, den_nam)
    return {t: (d.get(m) or []) for t, m in ma.items()}


def chuoi_bls(ten: str, tu_nam: int, den_nam: int, key: str = "") -> list[dict]:
    """Chuỗi thời gian chính thức từ Cục Thống kê Lao động. Trả [{nam, thang, gia_tri}]."""
    ma = BLS_CHUOI.get(ten, ten)
    key = key or key_bls()
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


def nhieu_chuoi_bls(tens: list[str], tu_nam: int, den_nam: int, key: str = "") -> dict:
    """NHIỀU chuỗi BLS trong MỘT lượt gọi. Trả {ten: [{nam, thang, gia_tri}]}.

    TIẾT KIỆM QUOTA — lý do tồn tại: BLS không key chỉ cho 25 LƯỢT/NGÀY. Kênh dạng đua cột cần
    6-8 chuỗi để so nhau, gọi lẻ từng chuỗi là một video đã ăn 8 lượt, ba kênh là hết ngày.
    API v2 nhận cả danh sách `seriesid` trong một thân yêu cầu -> 8 chuỗi vẫn chỉ tốn 1 lượt."""
    ma_theo_ten = {t: BLS_CHUOI.get(t, t) for t in tens}
    key = key or key_bls()
    body = {"seriesid": list(dict.fromkeys(ma_theo_ten.values()))[:25],
            "startyear": str(tu_nam), "endyear": str(den_nam)}
    if key:
        body["registrationkey"] = key
    d = _goi("https://api.bls.gov/publicAPI/v2/timeseries/data/", body)
    theo_ma = {}
    try:
        for se in d["Results"]["series"]:
            diem = []
            for x in (se.get("data") or []):
                try:
                    diem.append({"nam": int(x["year"]), "thang": x.get("periodName", ""),
                                 "gia_tri": float(x["value"]),
                                 "nguon": "U.S. Bureau of Labor Statistics"})
                except Exception:
                    continue
            theo_ma[str(se.get("seriesID"))] = list(reversed(diem))
    except Exception:
        return {}
    return {t: theo_ma.get(ma, []) for t, ma in ma_theo_ten.items()}


# ── 3b. BLS QUA FILE TĨNH — CÙNG DỮ LIỆU, KHÔNG DÍNH HẠN MỨC 25 LƯỢT/NGÀY ───────────────────
# API BLS không key chỉ cho 25 lượt/NGÀY: 12 kênh ăn nguồn này thì hết veo sau một buổi. Nhưng
# BLS còn công bố CHÍNH DỮ LIỆU ẤY dạng file text ở download.bls.gov — không qua API, không đếm
# lượt, không cần key. Tải một lần rồi giữ trong bộ nhớ tiến trình: cả phiên render dùng chung.
_BLS_TEP: dict = {}
BLS_KHO = {"cu": "cu/cu.data.0.Current",       # chỉ số giá tiêu dùng — 7.936 chuỗi, 49MB,
                                               # tải một lần/tiến trình. Bản AllItems chỉ có
                                               # đúng "mọi mặt hàng" (101 chuỗi) -> thiếu hẳn
                                               # nhóm nhà ở/thực phẩm/xăng mà kênh cần.
           "ce": "ce/ce.data.0.AllCESSeries",  # việc làm & lương
           "ln": "ln/ln.data.1.AllData"}       # thất nghiệp (Current Population Survey)


def _bls_tai(kho: str) -> dict:
    """Tải một kho BLS dạng file, trả {series_id: [{nam, thang, gia_tri}]}. Hỏng thì trả rỗng."""
    if kho in _BLS_TEP:
        return _BLS_TEP[kho]
    duong = BLS_KHO.get(kho, kho)
    try:
        # download.bls.gov trả 403 với User-Agent chung chung. Chính sách của BLS: UA phải kèm
        # ĐỊA CHỈ LIÊN HỆ để họ báo được khi mình tải quá tay. Không phải chống bot.
        req = urllib.request.Request(
            f"https://download.bls.gov/pub/time.series/{duong}",
            headers={"User-Agent": "MM0-Pipeline/1.0 (adisondurham@gmail.com)",
                     "Accept": "text/plain,*/*"})
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read().decode("utf-8", "ignore")
    except Exception as e:
        print(f"   ⚠️ BLS file '{kho}' hỏng: {str(e)[:60]}")
        _BLS_TEP[kho] = {}
        return {}
    ra: dict = {}
    for dong in raw.split("\n")[1:]:
        c = dong.split("\t")
        if len(c) < 4:
            continue
        ma, nam, ky, gt = c[0].strip(), c[1].strip(), c[2].strip(), c[3].strip()
        if not ky.startswith("M") or ky == "M13":      # M13 = trung bình năm, bỏ để khỏi đếm hai lần
            continue
        try:
            ra.setdefault(ma, []).append({"nam": int(nam), "thang": f"M{ky[1:]}",
                                          "gia_tri": float(gt),
                                          "nguon": "U.S. Bureau of Labor Statistics"})
        except Exception:
            continue
    _BLS_TEP[kho] = ra
    print(f"   📚 BLS '{kho}': {len(ra):,} chuỗi (file tĩnh, không tốn lượt API)")
    return ra


def chuoi_bls_tep(ten: str, tu_nam: int = 0, den_nam: int = 0) -> list[dict]:
    """Một chuỗi BLS lấy TỪ FILE. Dùng thay `chuoi_bls` khi không có key."""
    ma = BLS_CHUOI.get(ten, ten)
    kho = "ce" if ma.startswith("CE") else ("ln" if ma.startswith("LN") else "cu")
    bang = _bls_tai(kho)
    # cu.data dùng cả bản đã hiệu chỉnh mùa (CUSR) lẫn chưa (CUUR) — nhận cái nào có
    diem = bang.get(ma) or bang.get(ma.replace("CUUR", "CUSR")) or bang.get(ma.replace("CUSR", "CUUR")) or []
    if tu_nam:
        diem = [x for x in diem if x["nam"] >= tu_nam]
    if den_nam:
        diem = [x for x in diem if x["nam"] <= den_nam]
    return sorted(diem, key=lambda z: (z["nam"], z["thang"]))


def nhieu_chuoi_bls_tep(tens: list[str], tu_nam: int = 0, den_nam: int = 0) -> dict:
    """Nhiều chuỗi từ file — không tốn một lượt API nào dù xin bao nhiêu chuỗi."""
    return {t: chuoi_bls_tep(t, tu_nam, den_nam) for t in tens}


# ── 3c. IMF: ĐÃ THỬ, BỊ CHẶN — đừng thử lại ────────────────────────────────────────────────
# datamapper API trả 403 với mọi User-Agent (kể cả giả trình duyệt). Phần so sánh quốc tế đã có
# World Bank (`chi_so_the_gioi`, 29.544 chỉ số, không key), nên không mất gì. Ghi lại để lần sau
# không mất công dò lại.

def lay_bls(tens: list[str], tu_nam: int, den_nam: int) -> dict:
    """ĐƯỜNG CHÍNH để lấy dữ liệu BLS. Ưu tiên FILE TĨNH, API chỉ là đường lùi.

    Vì sao đảo thứ tự so với lẽ thường (API trước, file sau): API không key chỉ 25 lượt/NGÀY, mà
    12 kênh cùng ăn nguồn này. File tĩnh là CÙNG một dữ liệu, do chính BLS công bố, không đếm
    lượt, không cần key. Nặng hơn (49MB lần đầu) nhưng chỉ tải một lần cho cả tiến trình."""
    ra = nhieu_chuoi_bls_tep(tens, tu_nam, den_nam)
    thieu = [t for t in tens if not ra.get(t)]
    if thieu:
        # File không có chuỗi đó (mã lạ, hoặc kho chưa tải được) -> mới đụng tới hạn mức API
        bu = nhieu_chuoi_bls(thieu, tu_nam, den_nam)
        for t, v in bu.items():
            if v:
                ra[t] = v
    return ra


# ── 3d. ZILLOW — giá nhà THẬT theo bang, 2000 -> nay, file tĩnh không key ───────────────────
# Nhóm kênh nhà ở không dùng được BLS theo BANG (BLS chỉ chia theo VÙNG). Zillow công bố chỉ số
# giá nhà từng bang từng tháng dạng CSV mở — đúng thứ cần, và cũng không đếm lượt.
_ZL: dict = {}


def gia_nha_zillow(muc: str = "State") -> list[dict]:
    """Chỉ số giá nhà theo bang. Trả [{ten, thang: {YYYY-MM-DD: giá}}] — giữ nguyên cả chuỗi."""
    if muc in _ZL:
        return _ZL[muc]
    u = (f"https://files.zillowstatic.com/research/public_csvs/zhvi/"
         f"{muc}_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv")
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "MM0-Pipeline/1.0 (adisondurham@gmail.com)"})
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read().decode("utf-8", "ignore")
    except Exception as e:
        print(f"   ⚠️ Zillow hỏng: {str(e)[:60]}")
        _ZL[muc] = []
        return []
    import csv as _csv
    import io as _io
    doc = list(_csv.reader(_io.StringIO(raw)))
    if len(doc) < 2:
        _ZL[muc] = []
        return []
    dau = doc[0]
    i_ten = dau.index("RegionName")
    ngays = [(i, c) for i, c in enumerate(dau) if len(c) == 10 and c[4] == "-"]
    ra = []
    for d in doc[1:]:
        if len(d) <= i_ten or not d[i_ten]:
            continue
        gia = {}
        for i, c in ngays:
            if i < len(d) and d[i]:
                try:
                    gia[c] = float(d[i])
                except Exception:
                    pass
        if gia:
            ra.append({"ten": d[i_ten], "gia": gia, "nguon": "Zillow Home Value Index"})
    _ZL[muc] = ra
    print(f"   🏠 Zillow {muc}: {len(ra)} vùng, {len(ngays)} tháng (file tĩnh, không key)")
    return ra


# ── 3e. OPEN FOOD FACTS — dinh dưỡng sản phẩm THẬT, không key, không hạn mức ────────────────
# USDA FoodData chỉ cho 30 lượt/GIỜ với DEMO_KEY: hai kênh đồ ăn là hết. Open Food Facts mở hoàn
# toàn, có nhãn hàng Mỹ thật (Dave's Killer Bread, Kirkland...) và cho lọc theo quốc gia.
# Lưu ý: chỉ endpoint `cgi/search.pl` dùng được — `api/v2/search` trả 503 dai dẳng.
def thanh_phan_off(mon: str, n: int = 8, nuoc: str = "united-states") -> list[dict]:
    """Dinh dưỡng sản phẩm thật. Trả [{ten, hieu, calo, duong, mo, muoi}] — sắp theo calo giảm."""
    # Lọc theo PHÂN LOẠI, không theo từ khoá: `search_terms="cereal"` xếp theo độ phổ biến nên trả
    # về cả khoai tây chiên, bảng ra lệch hẳn chủ đề. `mon` ở đây là mã category của Open Food
    # Facts (breakfast-cereals · pizzas · chips · candies …).
    q = {"action": "process", "json": "1", "page_size": str(max(1, min(50, n * 3))),
         "sort_by": "unique_scans_n",
         "tagtype_0": "countries", "tag_contains_0": "contains", "tag_0": nuoc,
         "tagtype_1": "categories", "tag_contains_1": "contains", "tag_1": mon}
    u = "https://world.openfoodfacts.org/cgi/search.pl?" + urllib.parse.urlencode(q)
    # 503 không phải hỏng hẳn mà là "đang quá tải" — 18 lane gọi cùng lúc là dính ngay. Thử lại
    # NGAY LẬP TỨC thì cũng 503; phải giãn dần. Đo thật: chạy 8 luồng song song, không giãn thì
    # một kênh rớt, có giãn thì đủ cả.
    import random as _rd
    import time as _tg
    d = None
    for _lan in range(4):
        d = _goi(u)
        if d:
            break
        _tg.sleep((1.5 ** _lan) + _rd.random())
    ra = []
    for x in ((d or {}).get("products") or []):
        nu = x.get("nutriments") or {}
        calo = nu.get("energy-kcal_100g")
        ten = " ".join(str(x.get("product_name") or "").split())
        if not calo or not ten:
            continue
        try:
            ra.append({"ten": ten[:60], "hieu": " ".join(str(x.get("brands") or "").split())[:34],
                       "calo": round(float(calo)),          # nguồn hay trả 116.666666666667
                       "duong": round(float(nu.get("sugars_100g") or 0), 1),
                       "mo": round(float(nu.get("fat_100g") or 0), 1),
                       "muoi": round(float(nu.get("salt_100g") or 0), 2),
                       "nguon": "Open Food Facts"})
        except Exception:
            continue
    return sorted(ra, key=lambda z: -z["calo"])[:n]


# ── 4. ARCHIVE.ORG — phim tư liệu công cộng ────────────────────────────────────────────────
def phim_tu_lieu(tu_khoa: str, n: int = 6) -> list[dict]:
    """Phim công cộng khớp từ khoá. Trả [{id, tieu_de, nam, link}] — tải về được, dùng thoải mái."""
    q = f'({tu_khoa}) AND mediatype:movies AND (licenseurl:*publicdomain* OR collection:prelinger)'
    # Phải xin ĐỦ trường. Bản cũ chỉ xin `identifier` nên `title` luôn rỗng và tiêu đề rơi về mã
    # lưu trữ ("205471_Home_Movie_010144") — đọc lên nghe như video lỗi.
    url = ("https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(
        [("q", q), ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "year"),
         ("fl[]", "description"), ("rows", max(1, min(30, n))), ("output", "json")]))
    d = _goi(url)
    ra = []
    for x in (((d or {}).get("response") or {}).get("docs") or []):
        i = x.get("identifier")
        if i:
            ra.append({"id": i, "tieu_de": " ".join(str(x.get("title") or i).split())[:90],
                       "mo_ta": " ".join(str(x.get("description") or "").split())[:200],
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
def dem_ho_so_sec(cum: str) -> int:
    """TỔNG SỐ hồ sơ SEC nhắc tới một cụm từ. Trả 0 nếu hỏng.

    29/8 — cùng bài học với `dem_ban_an`: đếm ĐỘ DÀI TRANG trả về là đo cái trần của API chứ
    không đo thực tế. Trường `hits.total.value` là con số thật.
    LƯU Ý CÓ THẬT: SEC chặn trần ở 10.000 — cụm phổ biến ("supply chain", "artificial
    intelligence") đều trả đúng 10000, tức đã CHẠM TRẦN chứ không phải bằng nhau. Nên chỉ dùng
    hàm này với những cụm đủ hẹp để nằm dưới trần; đo thử: Gatorade 3.318, Doritos 955,
    Cheerios 356, Tide 16 — dải rộng gấp hơn hai trăm lần, thừa để dựng một bảng đọc được."""
    k = str(cum or "").strip().lower()
    _cu = _nho_doc("sec:" + k)
    if _cu:
        return _cu
    d = _goi("https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode({"q": f'"{cum}"'}))
    try:
        n = int((((d or {}).get("hits") or {}).get("total") or {}).get("value") or 0)
    except Exception:
        n = 0
    if n:
        _nho_ghi("sec:" + k, n)
    return n


def tieu_hanh_tinh_jpl(lui: int = 3, toi: int = 7) -> list[dict]:
    """Vật thể sượt qua Trái Đất — nguồn JPL, KHÔNG CẦN KHOÁ. [{ten, cach_km, duong_kinh_m}].

    29/8 — VÌ SAO ĐỔI NGUỒN. `tieu_hanh_tinh` gọi `api.nasa.gov`, và cổng ấy dùng khoá DEMO khi
    không khai khoá riêng: 30 lượt/giờ cho TOÀN BỘ địa chỉ mạng. Đo suốt buổi hôm nay thì lượt
    nào cũng 429, nên hai kênh vũ trụ không ra được video nào.
    JPL SSD/CNEOS mở cùng dữ liệu ấy qua `ssd-api.jpl.nasa.gov/cad.api`, không khoá, không hạn
    mức gắt. Gọi thử: 14 vật thể trong mười ngày tới, đủ dựng bảng sáu cột.

    ĐƯỜNG KÍNH SUY TỪ ĐỘ SÁNG TUYỆT ĐỐI. Trường `diameter` chỉ có ở vài vật thể đã được đo kỹ;
    còn `h` (độ sáng tuyệt đối) thì vật thể nào cũng có. Công thức chuẩn của giới thiên văn:
        D(km) = 1329 / sqrt(suất phản xạ) × 10^(−H/5)
    Suất phản xạ lấy 0,14 — giá trị trung bình của tiểu hành tinh gần Trái Đất mà JPL vẫn dùng
    khi chưa đo được. Đây là ƯỚC LƯỢNG và tôi nói rõ nó là ước lượng, nhưng nó là ước lượng
    CHÍNH NGÀNH ẤY dùng, không phải con số tôi bịa ra cho đủ cột.
    """
    import datetime as _dt
    h0 = _dt.date.today()
    u = ("https://ssd-api.jpl.nasa.gov/cad.api?" + urllib.parse.urlencode({
        "date-min": (h0 - _dt.timedelta(days=max(0, lui))).isoformat(),
        "date-max": (h0 + _dt.timedelta(days=max(1, toi))).isoformat(),
        "dist-max": "0.05", "diameter": "true", "sort": "dist"}))
    d = _goi_toa(u) or {}
    fs = list(d.get("fields") or [])
    ra = []
    for hang in (d.get("data") or []):
        z = dict(zip(fs, hang))
        try:
            au = float(z.get("dist") or 0)
        except Exception:
            continue
        if au <= 0:
            continue
        dk = 0.0
        try:
            dk = float(z.get("diameter") or 0) * 1000.0        # JPL trả km
        except Exception:
            dk = 0.0
        if dk <= 0:
            try:
                H = float(z.get("h") or 0)
                if H:
                    dk = (1329.0 / (0.14 ** 0.5)) * (10 ** (-H / 5.0)) * 1000.0
            except Exception:
                dk = 0.0
        ra.append({"ten": str(z.get("des") or "").strip(),
                   "cach_km": au * 149_597_870.7,
                   "duong_kinh_m": round(dk),
                   "ngay": str(z.get("cd") or "")[:11],
                   "nguon": "NASA/JPL Center for Near-Earth Object Studies"})
    return ra


def ngan_hang_theo_bang(n: int = 1000) -> dict:
    """{tên bang: số ngân hàng ĐANG HOẠT ĐỘNG}. Nguồn FDIC BankFind, mở, không cần khoá.

    29/8 — thêm cho kênh BANK RUN. Trước đó kênh này mượn tạm chỉ số lương BLS vì chưa có hàm
    FDIC, và hậu quả là nó ra ĐÚNG một video với kênh FINE PRINT: cùng "$49.78 · Information".
    Mượn tạm một nguồn cho có số là cách chắc chắn nhất để hai kênh trùng nhau."""
    u = ("https://banks.data.fdic.gov/api/institutions?" + urllib.parse.urlencode(
        {"filters": "ACTIVE:1", "fields": "NAME,STNAME,ASSET",
         "limit": max(1, min(2000, n)), "format": "json"}))
    d = _goi(u)
    gom: dict = {}
    for x in ((d or {}).get("data") or []):
        b = str(((x or {}).get("data") or {}).get("STNAME") or "").strip()
        if b:
            gom[b] = gom.get(b, 0) + 1
    return gom


# ══════════════════════════════════════════════════════════════════════════════════════════
# SỔ NHỚ TRÊN ĐĨA cho các phép ĐẾM TỔNG
# ------------------------------------------------------------------------------------------
# 29/8 — CourtListener chặn 429 suốt nhiều giờ sau khi ba kênh luật cùng hỏi 18 lượt liên tiếp.
# Bộ nhớ trong tiến trình không cứu được: mỗi lượt render là một tiến trình mới, nên lần nào
# cũng hỏi lại từ đầu và lần nào cũng bị chặn.
#
# Nhưng những con số này GẦN NHƯ TĨNH: "breach of contract" có 494.200 bản án, mỗi ngày nhích
# vài chục — tức thay đổi khoảng 0,006%/ngày. Hỏi lại mỗi lượt render là trả giá bằng việc bị
# chặn để lấy một con số y hệt hôm qua.
# Nhớ ra ĐĨA, hạn 7 ngày. Nguồn chập thì dùng số đã nhớ thay vì bỏ lượt — và nói rõ trong log
# là đang dùng số cũ, không im lặng.
_SO_NHO = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".dem_nho.json")
_HAN_NHO = 7 * 86400
# 30/8 — KHOÁ TOÀ ĐƯỢC NHỚ LÂU HƠN HẲN. Tổng số bản án khớp một cụm từ là con số gần như TĨNH:
# nó nhích vài chục mỗi ngày trên nền hàng trăm nghìn, tức là dưới một phần vạn. Nhớ ba mươi ngày
# thì con số vẫn đúng tới chữ số có nghĩa thứ ba, mà số lượt gõ vào một nguồn chặn nhịp rất chặt
# giảm đi bốn lần. Đây là chỗ đánh đổi có lợi rõ ràng, không phải mẹo.
_HAN_TOA = 30 * 86400


def _nho_doc(khoa: str, qua_han: bool = False):
    """Đọc số đã nhớ. `qua_han=True` thì chấp nhận cả bản ghi đã hết hạn.

    30/8 — DÙNG SỐ CŨ CÒN HƠN KHÔNG CÓ SỐ. CourtListener chặn theo IP hàng giờ, và ba kênh luật
    thì mỗi video cần sáu, bảy lượt gọi. Khi nguồn đóng cửa, cách cũ là BỎ LƯỢT — kênh câm cả
    ngày. Nhưng tổng số bản án khớp một cụm từ là con số gần như TĨNH: nó nhích vài chục mỗi
    ngày trên nền hàng trăm nghìn. Một giá trị bốn mươi ngày tuổi vẫn đúng tới chữ số có nghĩa
    thứ ba — chính xác hơn nhiều so với việc không phát video nào.
    Đây là lối "dùng bản cũ khi nguồn lỗi", và nó chỉ đúng cho đại lượng biến đổi chậm; KHÔNG
    được áp cho bảng đọc-nhiều-hôm-nay hay giá cả, những thứ mà số cũ là số SAI.
    """
    try:
        import json as _j, time as _t
        d = _j.load(io.open(_SO_NHO, encoding="utf-8")) if os.path.exists(_SO_NHO) else {}
        x = d.get(khoa)
        han = _HAN_TOA if str(khoa or "").startswith("toa:") else _HAN_NHO
        if x and (qua_han or (_t.time() - float(x.get("luc", 0))) < han):
            return int(x.get("n") or 0)
    except Exception:
        pass
    return None


def _nho_ghi(khoa: str, n: int) -> None:
    try:
        import json as _j, time as _t
        d = _j.load(io.open(_SO_NHO, encoding="utf-8")) if os.path.exists(_SO_NHO) else {}
        d[khoa] = {"n": int(n), "luc": _t.time()}
        io.open(_SO_NHO, "w", encoding="utf-8").write(_j.dumps(d, ensure_ascii=False))
    except Exception:
        pass


_NHO_DEM: dict = {}          # cụm từ -> tổng số bản án, nhớ trong một tiến trình


def dem_ban_an(tu_khoa: str) -> int:
    """TỔNG SỐ bản án khớp một cụm từ. Trả 0 nếu hỏng.

    29/8 — `ban_an` trả về TỐI ĐA 20 bản ghi mỗi lượt (một trang API), nên đếm độ dài danh sách
    là đo cái trần chứ không đo thực tế: sáu cụm từ khác hẳn nhau đều ra đúng 20, biểu đồ phẳng
    lì. CourtListener có sẵn trường `count` trong cùng câu trả lời ấy — 1.579.237 bản án nhắc
    tới Tu chính án thứ nhất — và đó vừa là con số có dải thật, vừa là câu chuyện mạnh hơn hẳn.
    Không tốn thêm lượt gọi nào: cùng một truy vấn, chỉ là đọc thêm một trường."""
    # NHỚ TRONG TIẾN TRÌNH. Ba kênh luật cùng hỏi sáu cụm từ mỗi kênh = 18 lượt gọi liên tiếp,
    # và CourtListener chặn nhịp: đo thật ở lượt render demo, hai trong ba kênh bỏ lượt vì
    # "nguồn không trả đủ dữ liệu". Tổng số bản án khớp một cụm từ là con số gần như TĨNH —
    # nó nhích vài chục mỗi ngày trên nền hàng trăm nghìn — nên nhớ lại trong một phiên là
    # đúng, không phải mẹo. Cùng cách đã chữa cho bảng đọc nhiều của Wikipedia.
    k = str(tu_khoa or "").strip().lower()
    if k in _NHO_DEM:
        return _NHO_DEM[k]
    _cu = _nho_doc("toa:" + k)
    if _cu:
        _NHO_DEM[k] = _cu
        return _cu
    u = ("https://www.courtlistener.com/api/rest/v4/search/?"
         + urllib.parse.urlencode({"q": tu_khoa, "type": "o", "order_by": "dateFiled desc"}))
    d = _goi_toa(u) or {}
    try:
        n = int(d.get("count") or 0)
    except Exception:
        n = 0
    if n:                      # chỉ nhớ khi CÓ số; nhớ số 0 là biến một lượt chập thành cả phiên hỏng
        _NHO_DEM[k] = n
        _nho_ghi("toa:" + k, n)
        return n
    # Nguồn đóng cửa: lấy lại bản đã nhớ dù đã quá hạn, còn hơn để kênh câm cả ngày.
    cu = _nho_doc("toa:" + k, qua_han=True)
    if cu:
        print(f"   ↩️ toà chặn nhịp — dùng lại số đã nhớ cho {k!r}")
        _NHO_DEM[k] = cu
    return cu or 0


# ══════════════════════════════════════════════════════════════════════════════════════════
# NHỊP GỌI RIÊNG CHO COURTLISTENER
# ------------------------------------------------------------------------------------------
# 30/8 — Đo được: nguồn này trả 429 ngay từ lượt gọi THỨ HAI khi gọi liên tiếp, và ba kênh luật
# thì mỗi video cần sáu tới bảy lượt. Kết quả là ba kênh bỏ lượt gần như mọi hôm — hỏng lặng lẽ,
# vì "bỏ lượt" là hành vi ĐÚNG của dây chuyền nên không ai báo động.
#
# CourtListener chặn theo NHỊP chứ không theo tổng: giãn các lượt ra thì qua. Nên có một cái van
# riêng cho đúng máy chủ này — 4,5 giây giữa hai lượt. Sáu lượt mất chừng 27 giây, chấp nhận được
# cho một video, và đổi lại kênh chạy được thay vì câm.
#
# Van này KHÔNG đặt ở `_goi` chung: các nguồn khác (Wikipedia, World Bank, NASA) rộng rãi hơn
# nhiều, bắt chúng chờ 4,5 giây mỗi lượt là làm chậm cả bốn mươi bảy kênh còn lại để chiều ba kênh.
_LUC_TOA = [0.0]
_DA_CHAN = [False]      # nguồn đã đóng cửa trong phiên này thì thôi gõ nữa
_GIAN_TOA = 4.5


def _goi_toa(url: str):
    """Gọi CourtListener, tự giữ nhịp tối thiểu giữa hai lượt."""
    import time as _tg
    cho = _GIAN_TOA - (_tg.time() - _LUC_TOA[0])
    if cho > 0:
        _tg.sleep(cho)
    _LUC_TOA[0] = _tg.time()
    d = _goi(url)
    if d is None and not _DA_CHAN[0]:
        # Lượt đầu bị chặn: nghỉ hẳn 40 giây rồi thử lại MỘT lần. Nếu vẫn chặn thì đánh dấu cả
        # phiên là "nguồn đóng cửa" và thôi thử — gõ tiếp chỉ kéo dài thời gian bị chặn, mà mọi
        # lượt sau đã có đường lui là số đã nhớ.
        _tg.sleep(40)
        _LUC_TOA[0] = _tg.time()
        d = _goi(url)
        if d is None:
            _DA_CHAN[0] = True
            print("   ⛔ CourtListener đóng cửa phiên này — chuyển sang dùng số đã nhớ")
    return d


def dem_ban_an_theo_moc(tu_khoa: str, tu_nam: int = 0, den_nam: int = 0) -> int:
    """TỔNG SỐ bản án khớp một cụm từ, GIỚI HẠN trong một khoảng năm nộp đơn. Trả 0 nếu hỏng.

    30/8 — Bốn kênh của mình cùng ăn một nguồn CourtListener. Nếu cả bốn đều "đếm theo cụm từ"
    thì bốn kênh ra bốn cái biểu đồ giống hệt nhau, chỉ khác chữ trên nhãn — đúng thứ đã bị
    `selftest` chặn (COURT RECORD ~ COLD FILE). Trục THỜI GIAN là một câu chuyện khác hẳn từ
    cùng một nguồn: không phải "kiện về cái gì nhiều nhất" mà "toà bắt đầu nghe chuyện này từ
    bao giờ" — và đó mới là thứ đáng kể về một lý lẽ pháp lý.

    Không tốn kênh gọi mới: vẫn `search/?q=…&type=o`, chỉ thêm `filed_after`/`filed_before`, và
    vẫn đọc trường `count` có sẵn. Nhớ vào cùng kho đệm của `dem_ban_an` với khoá kèm mốc năm,
    nên một mốc đã hỏi rồi thì cả phiên không hỏi lại — quan trọng vì CourtListener chặn nhịp
    rất chặt (đo được HTTP 429 sau chừng mười tám lượt liên tiếp).
    """
    k = str(tu_khoa or "").strip().lower()
    if not k:
        return 0
    kho = f"{k}|{tu_nam}-{den_nam}"
    if kho in _NHO_DEM:
        return _NHO_DEM[kho]
    _cu = _nho_doc("toa:" + kho)
    if _cu:
        _NHO_DEM[kho] = _cu
        return _cu
    ts = {"q": tu_khoa, "type": "o", "order_by": "dateFiled desc"}
    if tu_nam:
        ts["filed_after"] = f"01/01/{int(tu_nam)}"
    if den_nam:
        ts["filed_before"] = f"12/31/{int(den_nam)}"
    d = _goi_toa("https://www.courtlistener.com/api/rest/v4/search/?" + urllib.parse.urlencode(ts)) or {}
    try:
        n = int(d.get("count") or 0)
    except Exception:
        n = 0
    if n:      # chỉ nhớ khi CÓ số — nhớ số 0 là biến một lượt chập thành cả phiên hỏng
        _NHO_DEM[kho] = n
        _nho_ghi("toa:" + kho, n)
        return n
    cu = _nho_doc("toa:" + kho, qua_han=True)
    if cu:
        _NHO_DEM[kho] = cu
    return cu or 0


def ban_an(tu_khoa: str, n: int = 6) -> list[dict]:
    """Bản án công khai khớp từ khoá. Trả [{ten_vu, toa, ngay, trich, link}]."""
    u = ("https://www.courtlistener.com/api/rest/v4/search/?"
         + urllib.parse.urlencode({"q": tu_khoa, "type": "o", "order_by": "dateFiled desc"}))
    d = _goi_toa(u)
    ra = []
    for x in ((d or {}).get("results") or [])[:n]:
        ra.append({"ten_vu": str(x.get("caseName") or "")[:90],
                   "toa": str(x.get("court") or "")[:70], "ngay": str(x.get("dateFiled") or ""),
                   "trich": str(x.get("snippet") or "")[:200],
                   "link": "https://www.courtlistener.com" + str(x.get("absolute_url") or ""),
                   "nguon": "CourtListener (Free Law Project)"})
    return ra


# ── 8. WORLD BANK — so sánh Mỹ với phần còn lại của thế giới ────────────────────────────────
# Mã của các dòng GỘP trong World Bank (vùng, nhóm thu nhập, nhóm nhân khẩu) — không phải quốc gia.
_GOP_WB = {
    "AFE", "AFW", "ARB", "CSS", "CEB", "EAR", "EAS", "EAP", "TEA", "EMU", "ECS", "ECA", "TEC",
    "EUU", "FCS", "HPC", "HIC", "IBD", "IBT", "IDB", "IDX", "IDA", "LTE", "LCN", "LAC", "TLA",
    "LDC", "LMY", "LIC", "LMC", "MEA", "MNA", "TMN", "MIC", "NAC", "INX", "OED", "OSS", "PSS",
    "PST", "PRE", "SST", "SAS", "TSA", "SSF", "SSA", "TSS", "UMC", "WLD",
}


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
        ma3 = str(x.get("countryiso3code") or "")
        # 28/8 — LỌC MÃ 3 KÝ TỰ LÀ CHƯA ĐỦ. Dòng gộp của World Bank cũng mang mã 3 ký tự: "PST"
        # = Post-demographic dividend, "EMU" = Euro area, "LMY" = Low & middle income. Đo thật:
        # bảng độ che phủ rừng lọt "Post-demographic" vào giữa Georgia và Nigeria — người xem đọc
        # ra một cái tên không phải quốc gia nằm trong bảng xếp hạng quốc gia, và cả bảng mất tin.
        if v is None or not c or len(ma3) != 3 or ma3 in _GOP_WB:
            continue
        ra.append({"nuoc": c, "gia_tri": float(v), "nam": nam,
                   "nguon": "World Bank Open Data"})
    return sorted(ra, key=lambda z: -z["gia_tri"])[:n]


# ── 9. USGS — động đất ─────────────────────────────────────────────────────────────────────
def dong_dat(do_lon: float = 6.0, tu_ngay: str = "2020-01-01", n: int = 10,
             trong_my: bool = False) -> list[dict]:
    """Trận động đất mạnh nhất trong khoảng. Trả [{noi, do_lon, ngay, sau_km}].

    `trong_my=True` giới hạn trong khung toạ độ nước Mỹ (gồm Alaska, Hawaii). Cần cho kênh dùng
    BẢN ĐỒ BANG MỸ: dữ liệu toàn cầu trả về Nga/Chile/Fiji thì bản đồ Mỹ không tô được ô nào."""
    than = {"format": "geojson", "minmagnitude": do_lon, "starttime": tu_ngay,
            "orderby": "magnitude", "limit": max(1, min(200, n))}
    if trong_my:
        than.update({"minlatitude": 18.0, "maxlatitude": 72.0,
                     "minlongitude": -180.0, "maxlongitude": -66.0})
    u = "https://earthquake.usgs.gov/fdsnws/event/1/query?" + urllib.parse.urlencode(than)
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
def tieu_hanh_tinh(tu_ngay: str, den_ngay: str = "", key: str = "", n: int = 10) -> list[dict]:
    """Vật thể sát Trái Đất trong khoảng ngày. Trả [{ten, duong_kinh_m, toc_do_kmh, cach_km}]."""
    u = ("https://api.nasa.gov/neo/rest/v1/feed?" + urllib.parse.urlencode(
        {"start_date": tu_ngay, "end_date": den_ngay or tu_ngay, "api_key": key or key_data_gov()}))
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
def tai_tro(ky: int = 2024, bang: str = "", key: str = "", n: int = 10) -> list[dict]:
    """Ứng viên gom tiền nhiều nhất một kỳ. Trả [{ten, dang, bang, thu, chi}].

    KEY: đăng ký free ở api.data.gov — MỘT key dùng được cho cả FEC lẫn NASA và nhiều API .gov
    khác (1.000 lượt/giờ). DEMO_KEY chỉ 30 lượt/giờ, đủ thử chứ không đủ chạy hằng ngày."""
    than = {"api_key": key or key_data_gov(), "sort": "-receipts", "per_page": str(max(1, min(50, n))),
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

_NHO_NGAY: dict = {}          # (năm, tháng, ngày) -> bảng đọc nhiều, nhớ trong một tiến trình


def bai_duoc_doc(nam: int, thang: int, ngay: int, n: int = 12) -> list[dict]:
    """Bài Wikipedia được đọc nhiều nhất một ngày. Trả [{ten, luot_doc, hang}].

    Đây là "nước Mỹ hôm qua quan tâm cái gì" — đo được, không phải đoán: người nổi tiếng, vụ án,
    phim mới, thảm hoạ. Một nguồn nuôi được nhiều niche cùng lúc mà không kênh nào đang khai thác.

    29/8 — NHỚ BẢNG TỪNG NGÀY TRONG MỘT TIẾN TRÌNH. Đo trên nhật ký phiên render thật:
        448 lượt  HTTP 429: Too Many Requests (wikimedia.org)
         76 lượt  HTTP 404
    Wikipedia chặn nhịp gọi, và hậu quả lan ra: UNSOLVED LOG bỏ 28 lượt, các kênh cùng nguồn
    cũng rớt theo. Chính tôi làm nặng thêm trong hôm nay — thêm phép thử toạ độ và nới cửa sổ
    quét lên 14 ngày, mỗi thứ nhân số lượt gọi lên vài lần.
    Nhưng phần lớn số lượt ấy là HỎI LẠI ĐÚNG THỨ VỪA HỎI: bốn kênh Wikipedia cùng lùi qua cùng
    một dải ngày, mỗi kênh lại hỏi lại bảng của từng ngày. Bảng đọc nhiều của một ngày đã qua là
    dữ liệu TĨNH — nó không đổi nữa — nên nhớ lại là đúng, không phải mẹo.
    Bảng đầy đủ (1.000 bài) nặng ~120KB; nhớ 20 ngày là ~2,4MB, không đáng kể."""
    _k = (int(nam), int(thang), int(ngay))
    if _k in _NHO_NGAY:
        return list(_NHO_NGAY[_k])[:max(1, n)]
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
    # Chỉ ghi nhớ khi thật sự có dữ liệu: nhớ một bảng RỖNG do nguồn chập là biến một sự cố
    # tạm thời thành một sự cố kéo dài hết cả tiến trình.
    if ra:
        _NHO_NGAY[_k] = list(ra)
        if len(_NHO_NGAY) > 40:
            _NHO_NGAY.pop(next(iter(_NHO_NGAY)))
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


def thanh_phan_mon(mon: str, n: int = 6, key: str = "") -> list[dict]:
    """Dinh dưỡng thật của một món (USDA FoodData Central). Trả [{ten, calo, duong, mo, muoi}].

    KEY free ở api.data.gov — cùng key dùng được cho NASA và FEC."""
    u = ("https://api.nal.usda.gov/fdc/v1/foods/search?" + urllib.parse.urlencode(
        {"query": mon, "pageSize": max(1, min(25, n)), "api_key": key or key_data_gov()}))
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


def _epmc(tu_khoa: str, n: int, chat: bool = True) -> list[dict]:
    """Europe PMC — cùng kho tài liệu với PubMed, mở, không cần khoá, không chặn nhịp gắt.

    Lọc theo TÊN BÀI (`TITLE:`), không lọc theo toàn văn. Đo thật khi lọc toàn văn: từ khoá
    "screen time" trả về bài "Cytoscape: a software environment…", "vitamin d" trả về "Gene set
    enrichment analysis…" — những bài nhiều trích dẫn nhất trong kho, chỉ tình cờ có chứa cụm từ
    ấy đâu đó. Với một kênh mà cả nội dung là "một nghiên cứu có thật về X" thì đó là NÓI SAI,
    không phải chọn bài kém.
    Sắp theo số trích dẫn: trong hàng chục nghìn bài cùng chủ đề, bài được trích dẫn nhiều nhất
    là bài đồng nghiệp trong ngành thật sự đọc — tiêu chí khách quan, không phải tôi chấm.
    """
    q = f'TITLE:"{tu_khoa}" AND SRC:MED' + (" AND HAS_ABSTRACT:Y" if chat else "")
    d = _goi("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
        {"query": q, "format": "json", "pageSize": max(1, min(20, n)), "sort": "CITED desc"}))
    ra = []
    for x in (((d or {}).get("resultList") or {}).get("result") or []):
        ma = str(x.get("pmid") or x.get("id") or "")
        if not ma:
            continue
        ra.append({"tieu_de": str(x.get("title") or "")[:180],
                   "tap_chi": str(x.get("journalTitle") or "")[:60],
                   "nam": str(x.get("pubYear") or "")[:4], "ma": ma,
                   "link": (f"https://pubmed.ncbi.nlm.nih.gov/{ma}/" if x.get("pmid")
                            else f"https://europepmc.org/article/{x.get('source') or 'MED'}/{ma}"),
                   "nguon": "Europe PMC"})
    return ra


def nghien_cuu(tu_khoa: str, n: int = 6) -> list[dict]:
    """Nghiên cứu y khoa thật. Europe PMC trước, PubMed làm đường lui.

    29/8 — ĐỔI NGUỒN CHÍNH VÌ PUBMED ĐANG CHẶN MÌNH. Gọi thử bốn từ khoá liên tiếp thì cả bốn
    nhận về trang HTML kèm mã 200 (`_goi` nhận ra và báo "nguồn đang CHẶN nhịp gọi"). NCBI cho
    3 lượt/giây khi không có khoá API, và một khi đã chặn thì chặn cả địa chỉ mạng một lúc lâu —
    nên kênh ONE STUDY là kênh DUY NHẤT trong 50 kênh không chấm được điểm, suốt mấy lượt chấm.
    Europe PMC phục vụ cùng kho tài liệu ấy, mở, không đòi khoá, và cho lọc theo TÊN BÀI — thứ
    PubMed không làm được sạch bằng.
    Giữ PubMed làm đường lui: hai nguồn cùng chết một lúc thì kênh bỏ lượt, chứ không bịa."""
    r = _epmc(tu_khoa, n) or _epmc(tu_khoa, n, chat=False)
    if r:
        return r
    return _nghien_cuu_pubmed(tu_khoa, n)


def _nghien_cuu_pubmed(tu_khoa: str, n: int = 6) -> list[dict]:
    """Đường lui: PubMed E-utilities. Trả [{tieu_de, tap_chi, nam, ma}]."""
    # 28/8 — `tool` là thứ NCBI YÊU CẦU trong hướng dẫn E-utilities: nó cho họ biết lượt gọi này
    # của ai để hãm đúng chỗ thay vì chặn cả địa chỉ mạng. Đã dính chặn thật hôm nay (trang
    # "Access Denied" trả về kèm mã 200, xem `_goi`), nên đây không phải phép lịch sự suông.
    # KHÔNG gửi kèm `email`: NCBI có nhận, nhưng đó là thư riêng của chủ kênh và việc đưa nó cho
    # một dịch vụ bên ngoài là quyết định của người chủ, không phải của mã.
    d = _goi("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "term": tu_khoa, "retmode": "json", "retmax": max(1, min(20, n)),
         "sort": "relevance", "tool": "MM0-DataVideo"}))
    ids = (((d or {}).get("esearchresult") or {}).get("idlist") or [])
    if not ids:
        return []
    s2 = _goi("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": ",".join(ids), "retmode": "json", "tool": "MM0-DataVideo"}))
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


_NHO_TOA_DO: dict = {}          # tiêu đề -> có toạ độ hay không, nhớ trong một tiến trình


def noi_co_that(tieu_de: list[str]) -> set:
    """Trong danh sách tiêu đề Wikipedia, bài nào là MỘT CHỖ CÓ THẬT TRÊN BẢN ĐỒ.

    Phép thử: bài đó có TOẠ ĐỘ hay không. Wikipedia gắn toạ độ cho mọi bài về một địa điểm, và
    không gắn cho phim, bài hát, người.

    VÌ SAO KHÔNG DÒ CHỮ TRONG TIÊU ĐỀ NỮA
    -------------------------------------
    Bản cũ nhận bài có cụm " island", " canyon", " volcano"… rồi loại bỏ bài có "film"/"song".
    Khung thật kênh REAL PLACE: "Muppet Treasure Island" — khớp " island", không chứa chữ "film"
    nào trong tên, nên lọt thẳng vào một video có nhãn "nơi có thật, chuyện có thật". Danh sách
    chữ cấm kiểu này không bao giờ đủ: phim nào cũng có thể đặt tên theo một địa danh.
    Và nó còn CHẶT quá ở chiều ngược lại — mười hai cụm từ bỏ sót gần hết địa danh thật (thị
    trấn, công viên, hồ, đèo), nên kênh phải lùi ngày liên miên mới có bài.

    Toạ độ giải cả hai chiều cùng lúc, bằng chính dữ liệu của Wikipedia chứ không bằng phỏng đoán
    của mình. Đo thật trên bảng đọc nhiều nhất ngày 26/8: Dollywood, Neatsville (Kentucky),
    Pittman Center (Tennessee) đều có toạ độ; toàn bộ phim, ca sĩ, danh sách bài hát đều không.

    Gọi theo lô 50 tiêu đề — đúng trần một lần gọi của API Wikipedia.
    """
    import urllib.parse as _up
    ra = set()
    # NHỚ TRONG TIẾN TRÌNH. Bộ dựng lùi tối đa 10 ngày để tìm được một chỗ có thật, và bảng đọc
    # nhiều của hai ngày liền kề trùng nhau tới quá nửa — không nhớ thì cùng một tiêu đề bị hỏi
    # lại cả chục lần. Đo thật: chấm 50 kênh 6 luồng làm Wikipedia trả 429 hàng loạt, và phần lớn
    # lượt gọi ấy là hỏi lại thứ vừa hỏi xong.
    ds = [t for t in tieu_de if t]
    chua = [t for t in ds if t not in _NHO_TOA_DO]
    ra = {t for t in ds if _NHO_TOA_DO.get(t)}
    for i in range(0, len(chua), 50):
        lo = chua[i:i + 50]
        d = _goi("https://en.wikipedia.org/w/api.php?" + _up.urlencode(
            {"action": "query", "format": "json", "prop": "coordinates", "titles": "|".join(lo)}))
        if d is None:
            continue                       # nguồn chập -> ĐỪNG ghi nhớ "không có toạ độ"
        for p in (((d or {}).get("query") or {}).get("pages") or {}).values():
            t = str(p.get("title") or "")
            co = bool(p.get("coordinates"))
            _NHO_TOA_DO[t] = co
            if co:
                ra.add(t)
        for t in lo:                       # tiêu đề API không trả về = chắc chắn không có toạ độ
            _NHO_TOA_DO.setdefault(t, False)
    return ra


def nhac_theo_the(the: str, n: int = 20, phai_ket_thuc: bool = False) -> list[dict]:
    """Nghệ sĩ Mỹ THEO THẺ THỂ LOẠI (MusicBrainz). Trả cùng khuôn `ho_so_nhac`, thêm `the`.

    VÌ SAO KHÔNG DÙNG `ho_so_nhac` CHO VIỆC NÀY
    -------------------------------------------
    `ho_so_nhac` là tra THEO TÊN. Đưa vào một cụm thể loại thì MusicBrainz đem cụm ấy khớp với
    TÊN nghệ sĩ — nên "viral song" trả về các ban tên "Viral", "Viral Load", "Viral Millennium",
    rồi video gọi họ là nghệ sĩ một-bản-hit. Đo thật trên khung đã render của ONE HIT: đúng ba
    cái tên đó nằm cạnh Ella Fitzgerald. Không phải video xấu — video NÓI SAI, mà nói sai là thứ
    chính sách YouTube phạt nặng nhất và người xem không tha thứ.

    Kênh hồ sơ bài hát dính cùng một gốc mà còn đau hơn: nó lấy KẾT QUẢ ĐẦU TIÊN làm nhân vật
    chính của cả video, nên từ khoá "Grammy Award" hay "Billboard Hot 100" biến thành "nghệ sĩ"
    được dựng nguyên một phim chân dung.

    MusicBrainz có sẵn đường đúng: truy vấn theo THẺ (`tag:`) kèm nước và loại. Thẻ do người
    đóng góp gắn nên chỉ phủ các tên có tiếng — đúng thứ cần, vì kênh Mỹ kể về nghệ sĩ người xem
    đã nghe qua. Đo thật `tag:"new wave" AND country:US AND type:group`: 161 kết quả, đầu bảng là
    Hall & Oates, ZZ Top, Blondie, Talking Heads — tên thật, ngày tháng thật.

    `phai_ket_thuc` = chỉ lấy nghệ sĩ đã có ngày KẾT THÚC trên hồ sơ. Cần cho kênh đo "trụ được
    bao lâu": ban còn hoạt động thì quãng đời chưa chốt, đem xếp chung với ban đã tan là so một
    số đã xong với một số đang chạy.
    """
    d = _goi("https://musicbrainz.org/ws/2/artist?" + urllib.parse.urlencode(
        {"query": f'tag:"{the}" AND country:US', "fmt": "json",
         "limit": max(1, min(100, n * 4))}))
    ra = []
    for x in ((d or {}).get("artists") or []):
        # Điểm khớp thấp = MusicBrainz đoán mò. Loại "Group"/"Person" = gạt bỏ nhãn đĩa và
        # nhân vật hư cấu, những thứ không kể được thành chuyện người.
        if int(x.get("score") or 0) < 70 or str(x.get("type") or "") not in ("Group", "Person"):
            continue
        sp = x.get("life-span") or {}
        bd, kt = str(sp.get("begin") or ""), str(sp.get("end") or "")
        if not bd[:4].isdigit() or (phai_ket_thuc and not kt[:4].isdigit()):
            continue
        ra.append({"ten": str(x.get("name") or ""), "loai": str(x.get("type") or ""),
                   "nuoc": str(x.get("country") or ""), "bat_dau": bd, "ket_thuc": kt,
                   "diem_khop": int(x.get("score") or 0), "the": the,
                   "nguon": "MusicBrainz"})
        if len(ra) >= n:
            break
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
