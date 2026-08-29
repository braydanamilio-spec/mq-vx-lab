#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KÊNH THẾ HỆ 2 — dựng kịch bản THẲNG TỪ DỮ LIỆU, không footage (25/8/2026).

VÌ SAO CÓ FILE NÀY
------------------
55 kênh thế hệ 1 dùng chung công thức của hàng vạn kênh faceless: footage Pexels + chữ động +
giọng AI. Ai cũng lấy được cùng bộ footage nên không có gì để thuật toán ưu ái.

Thế hệ 2 đổi gốc: nội dung sinh từ BẢN GHI THẬT (25 nguồn mở đã gọi thử), hình vẽ bằng code.

BA CHẤT LIỆU (khai ở `chat_lieu` trong kenh_the_he_2.json)
  A — số liệu thật + đồ hoạ code. KHÔNG gọi AI một lần nào -> chạy được cả khi quota cạn sạch.
  B — ảnh AI theo style RIÊNG của kênh. Style cố định xuyên suốt là thứ đối thủ khó bắt chước:
      họ copy được ý tưởng, không copy được độ đều tay qua hàng trăm video.
  C — lai: số liệu làm xương, ảnh AI làm da.

RANH GIỚI KHÔNG ĐƯỢC VƯỢT: AI chỉ viết lời DẪN quanh con số CÓ SẴN. Nó không được nghĩ ra số.
Thiếu dữ liệu thì trả None và bỏ lượt — thà mất một video còn hơn mất uy tín cả kênh.

    python the_he_2.py --kenh STEAM_TRUTH --thu        # xem story, không render
"""
from __future__ import annotations

import datetime as _datetime
import io
import json
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
DS_KENH = os.path.join(GOC, "kenh_the_he_2.json")


def doc_kenh(ten: str | None = None) -> list[dict] | dict | None:
    ks = json.load(io.open(DS_KENH, encoding="utf-8"))
    if ten is None:
        return ks
    # 26/8 — SO SÁNH SAU KHI BỎ HẾT DẤU CÁCH Ở CẢ HAI VẾ.
    # `seed_the_he_2` lưu `name = ten.replace(" ", "")` -> Firestore có "WHATISINIT", còn ở đây so
    # với `ten` = "WHAT IS IN IT" (có dấu cách) và với `handle` = "whatisinitusa" (có đuôi usa).
    # Không vế nào khớp. Đo trên đúng 50 kênh: **33/50 tra không ra** -> `run_render` in "có cờ thế
    # hệ 2 nhưng không có trong kenh_the_he_2.json" rồi bỏ lượt => 33 lane ra 0 video cả đêm.
    # Bắt được lúc rà trước khi seed, chưa mất phiên nào.
    def _gon(x: str) -> str:
        return "".join(str(x or "").split()).replace("_", "").lstrip("@").upper()
    t = _gon(ten)
    for k in ks:
        if _gon(k["ten"]) == t or _gon(str(k["handle"]).lstrip("@")) == t:
            return k
    return None


def _tien(v: float) -> str:
    for chia, don in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(v) >= chia:
            return f"${v / chia:,.1f}{don}"
    return f"${v:,.0f}"


def _so(v: float) -> str:
    for chia, don in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(v) >= chia:
            return f"{v / chia:,.1f}{don}"
    # 28/8 — GIỮ MỘT CHỮ SỐ LẺ VỚI GIÁ TRỊ NHỎ.
    # Kênh MARRIAGE MATH ra sáu cột đề đúng một con số: 6, 6, 6, 6, 6, 6 — vì tỉ suất sinh của
    # sáu nước là 6.3 / 6.2 / 6.1 / 6.1 / 6.0 / 5.7 và `{:,.0f}` làm tròn hết về 6. Cột thì cao
    # thấp khác nhau mà nhãn thì giống nhau, nên người xem đọc ra "bảng này lỗi".
    # Làm tròn về hàng đơn vị chỉ vô hại khi con số đủ lớn để một đơn vị không đáng kể; dưới 100
    # thì phần lẻ CHÍNH LÀ thứ phân biệt. Số nguyên vẫn in ra nguyên (6.0 -> "6"), nên không có
    # chỗ nào đang đúng bị đổi.
    if abs(v) < 100 and abs(v - round(v)) >= 0.05:
        return f"{v:,.1f}"
    return f"{v:,.0f}"


# Tên nguồn HIỆN TRÊN MÀN HÌNH phải là tên cơ quan, không phải mã nội bộ. Cả điểm tin cậy của
# kênh nằm ở dòng này — "Source: bls" đọc như lỗi, "U.S. Bureau of Labor Statistics" là bằng chứng.
TEN_NGUON = {
    "usaspending": "USAspending.gov", "sec": "SEC EDGAR", "bls": "U.S. Bureau of Labor Statistics",
    "openfda": "openFDA · U.S. FDA", "nhtsa": "NHTSA", "court": "CourtListener",
    "worldbank": "World Bank Open Data",
    # 28/8 — thiếu dòng này nên hai kênh nhà đất in ra "Source: zillow" trên màn hình: chữ thường,
    # không viết hoa, đọc như một biến bị lộ chứ không như một nguồn. `ten_nguon` trả nguyên mã khi
    # không có bản dịch, nên lỗi kiểu này không kêu một tiếng nào — thấy được bằng mắt trên khung,
    # không thấy được trong log. Đã thêm chốt `t_moi_nguon_co_ten_that` để không tái phát.
    "zillow": "Zillow Home Value Index", "usgs": "U.S. Geological Survey", "nasa": "NASA CNEOS",
    "fec": "U.S. Federal Election Commission", "wikipedia": "Wikimedia pageviews",
    "mlb": "MLB StatsAPI", "nba": "NBA Stats", "steamspy": "SteamSpy", "tvmaze": "TVmaze",
    "musicbrainz": "MusicBrainz", "pubmed": "PubMed · U.S. NLM", "nws": "NOAA / National Weather Service",
    "opensky": "OpenSky Network", "epa": "U.S. EPA fueleconomy.gov", "dogceo": "Dog CEO API",
    "usda": "USDA FoodData Central", "archive": "Internet Archive",
}


def ten_nguon(ma: str) -> str:
    return TEN_NGUON.get(str(ma or "").lower(), str(ma or ""))


# ══════════════════════════════════════════════════════════════════════════════════════════
# CỔNG AN TOÀN NỘI DUNG — chạy trên MỌI kênh, MỌI dạng, không có ngoại lệ
# ------------------------------------------------------------------------------------------
# 26/8 — bài học suýt trả giá đắt: kênh WHAT THEY SEARCH lọc "chủ đề thầm kín" từ bảng đọc nhiều
# của Wikipedia, và ra một bảng gồm "Pornhub", "Sex", và "Teenage Sex and Death at…". Video kỹ
# thuật đạt hết mọi mốc QC — nhưng đăng lên là mất kênh, riêng cụm cuối (vị thành niên + tình
# dục) đủ để bị gỡ thẳng chứ không chỉ tắt kiếm tiền.
#
# Vì sao lỗi này KHÔNG thể để cho từng kênh tự lo: nguồn dữ liệu là bảng xếp hạng THẬT của thế
# giới thật, nên bất kỳ kênh nào lọc theo chủ đề cũng có ngày vớ phải mục như vậy. Cổng phải
# nằm ở chỗ mọi story đi qua.
_CAM = (
    # khiêu dâm / mại dâm
    "porn", "pornhub", "onlyfans", "xvideos", "xhamster", "nude", "naked", "nsfw", "hentai",
    "escort", "brothel", "prostitut", "strip club", "sex work", "sex tape", "erotic", "orgasm",
    "masturbat", "fetish", "bdsm", "incest", "playboy", "penthouse magazine",
    # trẻ vị thành niên — tuyệt đối không đứng cùng nội dung tình dục
    "child sex", "teenage sex", "teen sex", "underage", "child abuse", "csam", "grooming",
    "child porn", "minor sex", "statutory rape", "pedophil",
    # tấn công tình dục
    "rape", "sexual assault", "molest",
    # tự hại
    "suicide method", "how to kill", "self harm",
    # cực đoan
    "isis", "al-qaeda", "terror attack manual", "bomb making", "mass shooting livestream",
)
# Từ đứng riêng: chỉ chặn khi là TỪ ĐỘC LẬP, không chặn khi nằm trong từ khác
# ("Sussex" chứa "sex", "Essex" cũng vậy — chặn theo chuỗi con là xoá nhầm hàng loạt mục sạch).
_CAM_TU = ("sex", "sexual", "sexuality", "porn", "rape", "nude", "xxx", "erotica")


def an_toan(chu: str) -> bool:
    """True = dùng được. Lọc theo CỤM cho từ ghép, theo TỪ RIÊNG cho từ đơn."""
    import re as _re
    t = " ".join(str(chu or "").lower().split())
    if not t:
        return False
    if any(c in t for c in _CAM):
        return False
    return not any(_re.search(r"(?<![a-z])" + c + r"(?![a-z])", t) for c in _CAM_TU)


def loc_an_toan(ds: list, khoa=("name", "ten", "label", "tieu_de", "vo", "nar", "title")) -> list:
    """Bỏ mọi mục có chữ không an toàn ở bất kỳ trường chữ nào."""
    ra = []
    for x in ds or []:
        if isinstance(x, dict):
            if all(an_toan(str(x.get(k))) for k in khoa if x.get(k)):
                ra.append(x)
        elif an_toan(str(x)):
            ra.append(x)
    return ra


def _cau_neo(items: list) -> str:
    """Câu NEO SO SÁNH — cho con số một thước đo, thay vì để nó lơ lửng.

    27/8 — hai việc cùng lúc:
      • CHẤT LƯỢNG. "154K" tự nó không nói gì: người xem không biết nhiều hay ít. Kênh dữ liệu
        hạng nhất luôn neo con số vào một thứ khác — "gấp 3 lần hạng kế", "nhiều hơn cả năm
        hạng dưới cộng lại". Đây là thứ rẻ nhất mà nâng cảm giác nhiều nhất.
      • ĐỘ DÀI. Anh chốt long nên 5-10 phút. Đo được một chương ≈ 46,5 giây nên 6 chương ra
        4'39" — hụt sàn. Thêm chương thì ăn thêm đề tài (kho trung bình chỉ 9,8/kênh), còn thêm
        câu neo thì dài ra mà KHÔNG tốn đề tài nào. Chọn cách thứ hai.

    Chỉ neo khi CÓ CHÊNH LỆCH THẬT (đỉnh ≥ 1,5 lần hạng kế). Bảng san bằng mà vẫn nói "gấp
    nhiều lần" là nói sai — thà im."""
    xs = []
    for m in (items or []):
        if not isinstance(m, dict):
            continue
        v = _so_tu_chuoi(str(m.get("stat") or m.get("disp") or m.get("oddsDisp") or ""))
        if v > 0:
            xs.append((v, str(m.get("name") or m.get("label") or "")))
    if len(xs) < 3:
        return ""
    dinh, ten = xs[0]
    ke = xs[1][0]
    day = sum(v for v, _ in xs[1:])
    if ke <= 0 or dinh < ke * 1.5:
        return ""
    lan = dinh / ke
    if dinh > day:
        return (f"{ten} alone is bigger than every other one on this list combined.")
    return (f"{ten} is {lan:.1f} times the next one down."
            if lan < 10 else
            f"{ten} is more than {int(lan)} times the next one down.")


def _cong_an_toan(st: dict | None, ten_kenh: str = "") -> dict | None:
    """Cổng cuối: story nào còn chữ cấm thì cắt mục đó; cắt xong không đủ thì BỎ CẢ LƯỢT.

    Thà mất một video còn hơn mất một kênh."""
    if not st:
        return None
    # Neo TRƯỚC cổng an toàn để câu neo cũng bị soi chữ cấm như mọi câu khác.
    _neo = _cau_neo(st.get("items") or [])
    if _neo and _neo not in str(st.get("outro_vo") or ""):
        st["outro_vo"] = (str(st.get("outro_vo") or "").rstrip() + " " + _neo).strip()
    if not an_toan(st.get("title", "")):
        print(f"   🛡️ {ten_kenh}: tiêu đề không an toàn — BỎ LƯỢT")
        return None
    for khoa, toi_thieu in (("items", 3), ("data", 3), ("pairs", 3), ("scenes", 3)):
        if khoa in st:
            truoc = len(st[khoa] or [])
            st[khoa] = loc_an_toan(st[khoa])
            if truoc != len(st[khoa]):
                print(f"   🛡️ {ten_kenh}: cắt {truoc - len(st[khoa])} mục không an toàn")
            if len(st[khoa]) < toi_thieu:
                print(f"   🛡️ {ten_kenh}: còn {len(st[khoa])} mục sau khi lọc — BỎ LƯỢT")
                return None
    # 28/8 — CỔNG PHẢI ĐI QUA CẢ `frames`, CHỖ DẠNG ĐUA CẤT MỤC.
    # Anh gửi khung AMERICA LOOKED UP: một dòng trong bảng ghi **".XXX"**. `an_toan(".xxx")` vốn
    # trả False — danh sách chặn đã có từ "xxx" và luật ranh-giới-từ khớp đúng. Cổng KHÔNG hỏng;
    # nó chỉ chưa bao giờ được dẫn tới đó: vòng lọc ở trên đi qua items/data/pairs/scenes, mà
    # dạng `race` để mọi mục trong `frames[i].data`.
    # Đây là kiểu hỏng đắt nhất trong cả hệ: một cổng NHÌN THÌ CÓ, chạy thì không chạm tới dữ
    # liệu thật. Cùng họ với `DongNguon` được nhập mà không được vẽ, và `bien_cua` khai mà không
    # ai gửi. Với cổng an toàn nội dung thì cái giá không phải một video xấu, mà là cả một kênh.
    if st.get("frames"):
        _bo = 0
        _fr = []
        for fr in (st["frames"] or []):
            if not isinstance(fr, dict):
                continue
            _d = loc_an_toan(fr.get("data") or [])
            _bo += len(fr.get("data") or []) - len(_d)
            if len(_d) >= 3:
                _fr.append({**fr, "data": _d})
        if _bo:
            print(f"   🛡️ {ten_kenh}: cắt {_bo} ô không an toàn trong các khung đua")
        if len(_fr) < 4:
            print(f"   🛡️ {ten_kenh}: còn {len(_fr)} khung sau khi lọc — BỎ LƯỢT")
            return None
        st["frames"] = _fr
    for khoa in ("intro_vo", "outro_vo", "hook"):
        if st.get(khoa) and not an_toan(st[khoa]):
            st[khoa] = ""
    if st.get("narration"):
        st["narration"] = loc_an_toan(st["narration"])
        if len(st["narration"]) < 3:
            return None
    return st


def _gon(t: str, toi_da: int = 26) -> str:
    """Tên vừa thẻ: cắt theo TỪ, không cắt giữa chữ."""
    t = " ".join(str(t or "").split())
    if len(t) <= toi_da:
        return t
    tu = []
    for w in t.split():
        if len(" ".join(tu + [w])) > toi_da:
            break
        tu.append(w)
    # 27/8 — ĐỪNG ĐỂ CHỮ TREO LƠ LỬNG SAU KHI CẮT.
    # Đọc khung thật của AMERICA LOOKED UP: nhãn ra "SPIDER-MAN:" (treo dấu hai chấm của
    # "Spider-Man: Brand New Day") và "SOLAR ECLIPSE OF" (treo chữ "of"). Cả hai đều đọc như lỗi
    # phần mềm chứ không như một nhãn được chọn — mà đây là chữ nằm ngay cạnh con số, tức là chỗ
    # người xem nhìn nhiều nhất. Bỏ nốt từ nối cuối rồi gỡ dấu câu thừa: "Spider-Man" và
    # "Solar eclipse" vẫn nói đủ ý, mà trông như có người đặt.
    NOI = {"of", "and", "or", "the", "a", "an", "in", "on", "for", "to", "at", "by", "vs", "with"}
    while len(tu) > 1 and tu[-1].lower().strip(",;:-") in NOI:
        tu.pop()
    return (" ".join(tu).rstrip(" ,;:-–—") or t[:toi_da].rstrip(" ,;:-–—"))


# ══════════════════════════════════════════════════════════════════════════════════════════
# BỘ CHUYỂN ĐỔI: mỗi nguồn -> danh sách mục xếp hạng
# ------------------------------------------------------------------------------------------
# Mỗi hàm nhận tham số xoay vòng, trả (tieu_de, [{name, stat, vo}], cau_ket).
# Trả None = không đủ dữ liệu -> BỎ LƯỢT, tuyệt đối không bịa cho đủ.
# ══════════════════════════════════════════════════════════════════════════════════════════
def _bd_hop_dong(D, ky):
    nam = int(ky.get("nam", 2024))
    hd = D.hop_dong_lon(nam, 6, ky.get("de_tai", ""))
    if len(hd) < 3:
        return None
    tong = sum(x["tien"] for x in hd)
    ten = (ky.get("de_tai") or "federal").title()
    return (f"{ten} contracts: {_tien(tong)} in {nam}",
            [{"name": _gon(x["ten"]), "stat": _tien(x["tien"]),
              "vo": f"{_gon(x['ten'])}. {_tien(x['tien'])}."} for x in hd],
            "Every number is on USAspending dot gov.")


def _so_tu_chuoi(s: str) -> float:
    """Moi con so dau tien trong mot chuoi tu do ("approximately 12,480 cases" -> 12480).

    Truong `product_quantity` cua openFDA la van ban nguoi viet tay, muon kieu gi cung co:
    "1,234 cases", "approximately 500 lbs", "24 units/case; 120 cases". Lay so DAU TIEN va bo
    dau phay — du de xep hang, va khong bao gio bia them thu gi khong co trong nguon."""
    import re as _re
    m = _re.search(r"[\d][\d,\.]*", str(s or ""))
    if not m:
        return 0.0
    try:
        return float(m.group(0).replace(",", "").rstrip("."))
    except ValueError:
        return 0.0


def _ten_cty(t: str) -> str:
    """Ten cong ty doc duoc: bo duoi phap ly va menh de "dba".

    27/8 — xem khung that RECALL PLATE: mot the ghi "Silvestri Sweets Inc dba" — cat dung giua
    menh de, "dba" (doing business as) dung tro tren the nhu mot manh vun. Nguon openFDA ghi ten
    day du kieu "SILVESTRI SWEETS INC DBA HAMMOND'S CANDIES", ma cat cung 26 ky tu thi roi ngay
    giua. Cat theo CAU TRUC thay vi theo do dai: bo phan sau "dba" (ten thuong mai thi dai hon
    ma khong them thong tin), bo duoi Inc/LLC/Corp, roi moi cat neu van con dai."""
    import re as _re
    t = _re.sub(r"\s+", " ", str(t or "")).strip(" ,.")
    t = _re.split(r"\s+d[/.]?b[/.]?a\s+", t, flags=_re.I)[0]
    t = _re.sub(r"[,\s]+(inc|llc|l\.l\.c|corp|corporation|co|ltd|limited|plc|lp|llp|"
                r"company|holdings?|group)\.?$", "", t, flags=_re.I).strip(" ,.")
    return t or str(t)


def _gon_so(v: float) -> str:
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f}M".replace(".0M", "M")
    if v >= 1_000:
        return f"{v / 1_000:.1f}K".replace(".0K", "K")
    return f"{int(v):,}"


def _bd_thu_hoi(D, ky):
    """Thu hoi FDA -> bang xep hang.

    27/8 — XEM TAN MAT KHUNG HINH THAT (RECALL PLATE, frame 20/90/300) thi ba loi long ra, va
    khong loi nao la chuyen tham my:
      1. `stat` lay `classification` cua FDA ("Class I" -> "Cl.I"). Do la HANG PHAN LOAI, khong
         phai dai luong. Ket qua: CA SAU MUC cung mot gia tri -> bang "xep hang" khong xep gi ca,
         va so dan giua khung hook la chu "Cl.I" — nguoi xem khong hieu gi.
      2. `Renaissance Food Group` xuat hien BA LAN trong sau muc. Mot cong ty bi thu hoi nhieu lot
         thi nguon tra nhieu dong, nhung tren bang thi doc thanh "ba cong ty khac nhau trung ten".
      3. Bac S/A/B/C gan THEO VI TRI trong danh sach, ma nguon sap "moi nhat truoc" -> bac dang ma
         hoa DO GAN DAY chu khong phai do nang. Nguoi xem doc S la "dinh bang", hieu sai hoan toan.

    Sua: dai luong that la `product_quantity` (so luong bi thu hoi) — von da co san trong nguon ma
    khong ai dung. Gop cac lot cua cung mot cong ty, sap theo so luong giam dan, roi moi gan bac —
    luc do S moi that su la "nhieu nhat".
    Nguon khong du so luong thi KHONG bia: quay ve xep theo do nang cua FDA (Class I > II > III) va
    ghi ro "Class I" bang chu, khong nguy trang thanh con so."""
    kho = ky.get("kho", "thuc_pham")
    r = D.thu_hoi_fda(kho, 24, nam=int(ky.get("nam", 0)) or 0)   # lay rong hon vi con gop trung ten
    if len(r) < 3:
        return None
    nhan = {"thuc_pham": "Food", "thuoc": "Drug", "thiet_bi": "Device"}.get(kho, "Product")

    gop: dict = {}
    for x in r:
        ten = str(x.get("cong_ty") or "").strip()
        if not ten:
            continue
        g = gop.setdefault(ten, {"cong_ty": ten, "sl": 0.0, "lot": 0, "ly_do": "", "muc_do": ""})
        g["sl"] += _so_tu_chuoi(x.get("so_luong"))
        g["lot"] += 1
        if not g["ly_do"]:
            g["ly_do"] = str(x.get("ly_do") or "")
        if not g["muc_do"]:
            g["muc_do"] = str(x.get("muc_do") or "")
    ds = list(gop.values())
    if len(ds) < 3:
        return None

    co_so = [g for g in ds if g["sl"] > 0]
    if len(co_so) >= 3:
        co_so.sort(key=lambda g: -g["sl"])
        muc = [{"name": _gon(_ten_cty(g["cong_ty"])), "stat": _gon_so(g["sl"]),
                "vo": (f"{_gon(g['cong_ty'], 34)} pulled {_gon_so(g['sl'])}"
                       + (f" across {g['lot']} separate recalls" if g["lot"] > 1 else "")
                       + f". {g['ly_do'][:80]}")} for g in co_so[:6]]
        don_vi = "units"
    else:
        nang = {"Class I": 0, "Class II": 1, "Class III": 2}
        ds.sort(key=lambda g: (nang.get(g["muc_do"], 9), -g["lot"]))
        muc = [{"name": _gon(_ten_cty(g["cong_ty"])), "stat": g["muc_do"] or "Class ?",
                "vo": (f"{_gon(g['cong_ty'], 34)}, {g['muc_do'] or 'a recall'}"
                       + (f", {g['lot']} times" if g["lot"] > 1 else "")
                       + f". {g['ly_do'][:80]}")} for g in ds[:6]]
        don_vi = "severity"
    return (f"{nhan} recalls you probably missed", muc,
            "All of this is filed with the F D A.",
            f"{nhan} recalls, ranked by how much got pulled off the shelf." if don_vi == "units"
            else f"{nhan} recalls, ranked by how serious the F D A called them.")


def _ten_toa(t: str) -> str:
    """Ten toa rut gon ma VAN DUNG NGHIA.

    27/8 — `_gon(toa, 30)` cat cung 30 ky tu nen tren khung hien "Court of Appeals for the" va
    "Supreme Court of The Virgin": cat giua cum, nguoi xem doc khong ra toa nao. Ten toa My co
    cau truc co dinh, phan PHAN BIET nam o duoi ("...for the Ninth Circuit"), nen cat dau la cat
    dung thu can giu. Rut theo cau truc thay vi theo do dai."""
    import re as _re
    t = _re.sub(r"\s+", " ", str(t or "")).strip()
    if not t:
        return ""
    m = _re.search(r"for the (\w+) Circuit", t, _re.I)
    if m:
        return f"{m.group(1).title()} Circuit"
    m = _re.match(r"(?:Supreme Court|Court of Appeals?|District Court)\s+(?:of|for)\s+(?:the\s+)?(.+)", t, _re.I)
    if m:
        duoi = m.group(1).strip()
        loai = "Supreme" if t.lower().startswith("supreme") else "Appeals"
        return f"{duoi[:22]} {loai}" if len(duoi) <= 22 else f"{duoi[:22].rstrip()} {loai}"
    m = _re.match(r"(.+?)\s+(?:Supreme Court|Court of Appeals?)", t, _re.I)
    if m:
        return m.group(1).strip()[:26]
    return t[:26]


def _bd_ban_an(D, ky):
    """Vu kien -> bang xep hang theo TOA nao xu nhieu nhat.

    27/8 — bai soi 19 bo du lieu: bang cu cho `stat` = NAM NOP DON, va vi nguon sap "moi nhat
    truoc" nen ca sau muc deu ra "2026". Mot bang xep hang ma sau dong cung mot gia tri thi no
    khong xep hang gi ca — nguoi xem nhin 30 giay va khong biet duoc gi.
    Nguon CourtListener khong co truong nao la "do lon" cua mot vu kien. Nhung no co TOA. Lay
    rong ra roi DEM SO VU THEO TOA thi ra mot dai luong that: toa nao nghe loai kien nay nhieu
    nhat. Vua co so that, vua la mot cau chuyen dang xem hon danh sach ten vu roi rac."""
    tk = ky.get("tu_khoa", "consumer fraud")
    r = D.ban_an(tk, 120)               # rong hon: 60 dong trai deu ra 2-2-2-1-1-1, gan nhu phang
    if len(r) < 12:
        return None
    dem: dict = {}
    for x in r:
        toa = _ten_toa(str(x.get("toa") or ""))
        if not toa:
            continue
        g = dem.setdefault(toa, {"toa": toa, "n": 0, "vu": ""})
        g["n"] += 1
        if not g["vu"]:
            g["vu"] = str(x.get("ten_vu") or "")
    ds = sorted(dem.values(), key=lambda g: -g["n"])
    # Doi PHAN BO THAT, khong chi doi "co so". 2-2-2-1-1-1 ve mat ky thuat la mot bang xep hang,
    # nhung nhin tren man hinh thi sau cot cao bang nhau — nguoi xem khong thay thu hang nao ca.
    # Dinh bang phai it nhat gap doi day bang, va phai co it nhat 3 muc khac gia tri.
    # Doi dinh bang >= 3 va bang co it nhat 3 MUC KHAC GIA TRI. Ban dau con doi dinh >= 2x day
    # bang, nhung do la doi hoi sai: mot bang 5-4-3-2-2-1 la mot bang xep hang tot, ma 5 < 2x2
    # nen bi loai — kenh SUED FOR THIS ra 0 video vi dung dieu kien nay. Thu can la NHIN RA
    # THU HANG, khong phai mot khoang cach cu the.
    if len(ds) < 4 or ds[0]["n"] < 3 or len({g["n"] for g in ds[:6]}) < 3:
        print(f"   ⚠️ bản án '{tk}': không toà nào nổi trội (đỉnh {ds[0]['n'] if ds else 0}) — "
              f"BỎ LƯỢT thay vì dựng bảng sáu cột bằng nhau")
        return None
    return (f"Where people sue over {tk}",
            [{"name": g["toa"], "stat": f"{g['n']} cases",
              "vo": f"{g['toa']}: {g['n']} of them. Such as {_gon(g['vu'], 40)}."}
             for g in ds[:6]],
            "Court records are public. Look them up.",
            f"Courts that hear the most {tk} cases, counted from public dockets.")


# Bài mang tính riêng tư / tò mò thầm kín — dùng để tách kênh WHAT THEY SEARCH khỏi bảng chung.
# 26/8 — bản đầu gồm cả "porn", "nude", "onlyfans"… nên bảng ra toàn nội dung người lớn: đúng
# thứ làm mất kênh. Danh sách nay chỉ giữ chủ đề QUAN HỆ đời thường — vẫn là thứ người ta tra
# lặng lẽ, nhưng đăng được. Cổng `an_toan()` vẫn chặn lần hai phía sau.
_RIENG_TU = ("divorce", "dating", "marriage", "relationship", "breakup", "wedding",
             "engagement", "wife", "husband", "girlfriend", "boyfriend", "couple",
             "married", "romance", "prenup", "custody", "in-law", "long distance")


def _bd_wiki_top(D, ky):
    # Bảng đọc nhiều trả tới 1000 bài/ngày. Lọc theo chủ đề thì phải quét CẢ bảng, quét
    # 60 dòng đầu là gần như luôn rỗng -> kênh bỏ lượt oan mỗi ngày.
    # Và một ngày cụ thể có thể không có đủ bài thuộc chủ đề kênh -> lùi dần tối đa 10 ngày,
    # vẫn là bảng THẬT, chỉ của ngày khác (giống cách bộ phim kể đang làm).
    import datetime as _dt
    # 27/8 — LỆCH NGỮ NGHĨA GIỮA TRỤC XOAY VÀ HÀM ĐỌC.
    # Hàm này hiểu `ngay` là NGÀY TRONG THÁNG, còn `KHO_XOAY["ngay"]` là SỐ NGÀY LÙI LẠI
    # ([7, 14, 21, 30, 45, 60, 90, 120, 180, 270, 365, 545, 730]). Nên xoay tới 45 là dựng
    # `date(năm, tháng, 45)` -> ValueError, và mọi giá trị > 31 đều chết.
    # Đo thật: 3 kênh dùng nguồn này (AMERICA LOOKED UP, UNSOLVED LOG, REAL PLACE) chỉ có
    # 3/13 đề tài chạy được — đúng bằng số giá trị <= 31 trong kho.
    # Trục ĐÚNG cho một bảng "đọc nhiều nhất ngày X" là SỐ NGÀY LÙI, không phải ngày trong
    # tháng: nó luôn hợp lệ, luôn trỏ tới một ngày có thật, và tự trôi theo thời gian nên
    # kho không bao giờ cũ đi.
    if ky.get("lui") is not None:
        goc = _dt.date.today() - _dt.timedelta(days=int(ky["lui"]))
    else:
        goc = _dt.date(int(ky["nam"]), int(ky["thang"]), int(ky["ngay"]))
    if ky.get("loc") == "rieng_tu":
        r = []
        for lui in range(0, 10):
            d = goc - _dt.timedelta(days=lui)
            r = [x for x in D.bai_duoc_doc(d.year, d.month, d.day, 1000)
                 if any(t in x["ten"].lower() for t in _RIENG_TU)][:6]
            if len(r) >= 3:
                break
        if len(r) < 3:
            return None
        return ("What America quietly looked up",
                [{"name": _gon(x["ten"], 28), "stat": _so(x["luot_doc"]),
                  "vo": f"{_gon(x['ten'], 34)}. {x['luot_doc']:,} searches."} for x in r],
                "Nobody admits to this one.")
    r = D.bai_duoc_doc(goc.year, goc.month, goc.day, 1000)[:6]
    if len(r) < 3:
        return None
    return (f"What America read on {ky['thang']}/{ky['ngay']}",
            [{"name": _gon(x["ten"], 28), "stat": _so(x["luot_doc"]),
              "vo": f"{_gon(x['ten'], 34)}. {x['luot_doc']:,} people looked it up."} for x in r],
            "That is one single day of curiosity.")


def _bd_nba(D, ky):
    # Mặc định phải nằm ở BIẾN, không nằm rải trong lời gọi: trước đây title đọc lại
    # ky.get("mua", "") nên khi không truyền tham số, tiêu đề ra cụt "NBA points leaders, ".
    mua = ky.get("mua") or "2024-25"
    ma_ct = ky.get("chi_tieu") or "PTS"
    r = D.thong_ke_nba(mua, ma_ct, 6)
    if len(r) < 3:
        return None
    ct = {"PTS": "points", "REB": "rebounds", "AST": "assists"}.get(ma_ct, "")
    return (f"NBA {ct} leaders, {mua}",
            [{"name": _gon(x["ten"], 24), "stat": f"{x['gia_tri']:.1f}",
              "vo": f"{_gon(x['ten'], 30)}, {x['gia_tri']:.1f} {ct} a game."} for x in r],
            "Numbers straight from the league.")


def _so_huu(x) -> int:
    """Cận dưới của khoảng người sở hữu SteamSpy ("1,000,000–2,000,000" -> 1000000)."""
    v = str(x.get("so_huu") or "").replace(",", "").replace("..", "–")
    try:
        return int((v.split("–")[0] or "0").strip() or 0)
    except Exception:
        return 0


def _bd_steam(D, ky):
    """Game Steam — bốn góc nhìn trên CÙNG một bảng dữ liệu.

    28/8 — TRỤC XOAY `loc` TRƯỚC NAY CHỈ CÓ MỘT NHÁNH THẬT. Hàm này nhận `loc` nhưng chỉ xử lý
    `chet_yeu`; kênh STEAM TRUTH lại xoay qua bốn giá trị khác (`dong_nhat`, `tang_manh`,
    `dinh_cao`, `ban_chay`) và KHÔNG giá trị nào có nhánh — cả bốn rơi xuống cùng một đường mặc
    định, ra cùng một bảng, cùng một tiêu đề. Chống trùng coi cả bốn là đã làm ⇒ kênh câm sau một
    video, log ghi "hết kho đề tài".

    Và hai trong bốn giá trị ấy KHÔNG THỂ làm được: SteamSpy trả về tên, số người đang chơi, khoảng
    người sở hữu và giá — không có chuỗi thời gian, nên `tang_manh` (tăng mạnh nhất) và `dinh_cao`
    (đỉnh trong ngày) không có gì để tính. Viết nhánh cho chúng là mời một con số bịa vào bảng.
    Nên đổi kho trục sang bốn góc mà dữ liệu ĐỠ ĐƯỢC, mỗi góc một câu chuyện khác hẳn:
      dong_nhat  — đông người chơi nhất ngay lúc này
      ban_chay   — nhiều người sở hữu nhất
      mien_phi   — game miễn phí đang đông hơn game trả tiền
      dat_tien   — game đắt nhất mà vẫn có người chơi
      chet_yeu   — bán được hàng triệu bản mà không ai còn mở (góc ngược, kênh khác dùng)
    """
    r = D.game_steam(100)
    if len(r) < 6:
        return None
    loc = str(ky.get("loc") or "dong_nhat")

    def _bang(ds, nhan_so=None):
        return [{"name": _gon(x["ten"], 26), "stat": (nhan_so(x) if nhan_so else _so(x["dang_choi"])),
                 "vo": f"{_gon(x['ten'], 32)}. {x['dang_choi']:,} playing right now."} for x in ds]

    if loc == "chet_yeu":
        # Góc NGƯỢC LẠI: game bán được nhiều mà gần như không ai còn mở. Cùng một nguồn, hai kênh,
        # hai câu chuyện khác hẳn — đây là cách để hai kênh không giẫm chân nhau.
        ds = sorted([x for x in r if _so_huu(x) > 500000], key=lambda z: z["dang_choi"])[:6]
        if len(ds) < 3:
            return None
        return ("Games millions bought and nobody plays",
                [{"name": _gon(x["ten"], 26), "stat": _so(x["dang_choi"]),
                  "vo": f"{_gon(x['ten'], 32)}. Only {x['dang_choi']:,} still online."} for x in ds],
                "Owned by millions. Empty tonight.",
                "Millions own these games. Top of the board is the emptiest.")

    # BỐN LÁT: LỌC theo giá, nhưng luôn XẾP theo số người đang chơi.
    #
    # 28/8 — bản đầu của tôi xếp theo giá và theo số người sở hữu, và cả hai chết ngay lượt đo:
    # SteamSpy trả người sở hữu theo KHOẢNG THÔ ("100.000.000 – 200.000.000") nên sáu game đầu
    # bảng đều hiện "100.0M", còn giá thì sáu game đắt nhất đều đúng $59.99. Sáu dòng một con số
    # thì không phải bảng xếp hạng — cổng chất lượng chặn cả hai, đúng.
    # Số người ĐANG CHƠI thì mỗi game một khác, nên nó là đại lượng xếp hạng duy nhất mà nguồn
    # này đỡ nổi. Giá chỉ dùng để CẮT LÁT — và bốn lát ra bốn bảng khác hẳn nhau, vì game miễn phí
    # và game 60 đô gần như không bao giờ chung một bảng.
    _gia = lambda x: float(x.get("gia") or 0)
    LAT = {
        "mien_phi": (lambda x: _gia(x) <= 0, "Free games beating the ones people paid for",
                     "Nobody paid a cent for any of these."),
        "tra_tien": (lambda x: _gia(x) > 0, "Paid games people still open every night",
                     "Every one of these cost money. People still play them."),
        "dat_tien": (lambda x: _gia(x) >= 40, "Sixty-dollar games that kept their players",
                     "Full price, and the servers are still busy."),
        "re_tien": (lambda x: 0 < _gia(x) <= 10, "Cheap games pulling the biggest crowds",
                    "Ten dollars or less. Look at the numbers."),
    }
    if loc in LAT:
        _hop, _ten, _ket = LAT[loc]
        ds = sorted([x for x in r if _hop(x)], key=lambda z: -z["dang_choi"])[:6]
        if len(ds) < 3:
            return None
        return (_ten, _bang(ds), _ket)

    # ── NHÓM "MUA RỒI BỎ": cùng một nguồn, nhìn từ đầu kia ────────────────────────────────
    # 29/8 — khung thật GAME GRAVEYARD hiện ĐÚNG nội dung của STEAM TRUTH: Counter-Strike 1.0M,
    # PUBG 314.7K. Hai kênh, một video. Vì `kho_loc` của nó khai bốn giá trị (chet_yeu · tut_manh ·
    # vang_nhat · bo_hoang) mà hàm này chỉ có nhánh `chet_yeu`; ba giá trị kia rơi xuống nhánh
    # MẶC ĐỊNH — và nhánh mặc định chính là câu chuyện của kênh bên cạnh.
    # Đây là lỗi trùng nội dung giữa hai kênh, thứ chính sách "sản xuất hàng loạt" của YouTube
    # nhắm thẳng vào — nặng hơn hẳn một lỗi hiển thị.
    BO_HOANG = {
        "vang_nhat": (lambda x: _gia(x) > 0 and _so_huu(x) > 200000,
                      "Paid games with the emptiest servers",
                      "People bought them. Nobody logged in."),
        "bo_hoang":  (lambda x: _so_huu(x) > 2000000,
                      "The biggest games nobody opens",
                      "Two million owners. Look at tonight."),
        "dat_bo":    (lambda x: _gia(x) >= 40 and _so_huu(x) > 500000,
                      "Sixty-dollar games sitting empty",
                      "Full price, empty servers."),
    }
    if loc in BO_HOANG:
        _hop, _ten, _ket = BO_HOANG[loc]
        ds = sorted([x for x in r if _hop(x)], key=lambda z: z["dang_choi"])[:6]
        if len(ds) < 3:
            return None
        return (_ten,
                [{"name": _gon(x["ten"], 26), "stat": _so(x["dang_choi"]),
                  "vo": f"{_gon(x['ten'], 32)}. Only {x['dang_choi']:,} still online."} for x in ds],
                _ket)

    # KHÔNG có nhánh nào khớp -> BỎ LƯỢT, tuyệt đối không rơi về mặc định.
    # Rơi về mặc định nghĩa là kênh này nhả ra video của kênh khác, và không một dòng log nào báo.
    # Thà mất một lượt còn hơn hai kênh cùng đăng một video.
    if loc not in ("dong_nhat", ""):
        print(f"   ⚠️ game Steam: bộ lọc '{loc}' chưa có nhánh — BỎ LƯỢT "
              f"(không rơi về mặc định, tránh trùng nội dung với kênh khác)")
        return None

    ds = sorted(r, key=lambda z: -z["dang_choi"])[:6]
    return ("Games people actually play right now", _bang(ds),
            "Not sales. People actually online.")


def _bd_trieu_hoi(D, ky):
    """Trieu hoi xe -> dem so vu theo NHOM BO PHAN.

    27/8 — kenh CAR RECALL ra 0 video. API NHTSA van chay tot (11 ban ghi), nhung truong
    `so_xe` (so xe bi anh huong) RONG O CA 11 BAN GHI — endpoint nay khong tra con so do.
    Ban cu lay thang `so_xe` lam `stat`, khong co thi ghi "—": ca sau dong deu la dau gach,
    va cong "bang phai that su xep hang" chan lai. Chan la dung: sau dau gach thi bang khong
    noi len dieu gi.
    Dai luong CO THAT trong du lieu nay la SO VU theo tung he thong tren xe. "He thong dien:
    5 lan bi trieu hoi trong mot doi xe" la mot con so that, va la mot cau chuyen dang xem hon
    han mot danh sach ten bo phan.
    `bo_phan` cua NHTSA co dang "ELECTRICAL SYSTEM:12V BATTERY:CABLE" — lay phan TRUOC dau hai
    cham dau tien lam nhom, dung muc do nguoi xem hieu duoc."""
    # MOT DOI XE LA QUA MONG. Do that Ford F-150 2020: 11 ban ghi, gom lai chi ra 2x/2x/2x/1x/1x
    # — hai gia tri khac nhau, cong "bang phai that su xep hang" chan lai (dung).
    # Nhung cau hoi cua kenh khong phai "doi 2020 co gi" ma "dong xe nay hay hong cho nao" — va
    # cau do phai hoi NHIEU DOI moi tra loi duoc. Gom 5 doi lien nhau: du day de thay he thong
    # nao lap lai, va van la mot cau chuyen chat che ve DUNG mot dong xe.
    # 27/8 — TRỤC XOAY PHẢI LÀ CẶP (HÃNG, DÒNG), KHÔNG PHẢI HÃNG.
    # Đo thật: kênh CAR RECALL xoay `hang` qua 8 hãng nhưng giữ nguyên `dong = "f-150"`. API
    # NHTSA hỏi theo ĐÚNG một dòng xe, nên `toyota + f-150` không có gì cả — 7/8 giá trị xoay
    # ra rỗng. Kênh thực tế chỉ làm được ĐÚNG MỘT video (ford f-150) rồi câm.
    # Bỏ `dong` đi cũng không xong: API bắt buộc phải có dòng. Nên trục là một CẶP, viết liền
    # trong một chuỗi ("toyota camry") rồi tách ra ở đây.
    if ky.get("xe"):
        _p = str(ky["xe"]).strip().split(" ", 1)
        ky = {**ky, "hang": _p[0], "dong": (_p[1] if len(_p) > 1 else "")}
    nam0 = int(ky.get("nam", 2022))
    r = []
    for dn in range(nam0 - 4, nam0 + 1):
        try:
            r += D.trieu_hoi_xe(ky.get("hang", "ford"), ky.get("dong", ""), dn) or []
        except Exception:
            continue
    if len(r) < 6:
        return None
    dem: dict = {}
    for x in r:
        bp = str(x.get("bo_phan") or "").split(":")[0].strip().title()
        if not bp:
            continue
        g = dem.setdefault(bp, {"ten": bp, "n": 0, "hq": ""})
        g["n"] += 1
        if not g["hq"]:
            g["hq"] = str(x.get("hau_qua") or "")
    ds = sorted(dem.values(), key=lambda g: -g["n"])
    if len(ds) < 3:
        return None
    ten = f"{ky.get('hang', '').title()} {str(ky.get('dong', '')).upper()}".strip()
    return (f"{ten}: what keeps breaking ({nam0 - 4}-{nam0})",
            [{"name": _gon(g["ten"], 26), "stat": f"{g['n']}x",
              "vo": f"{_gon(g['ten'], 30)}, {g['n']} separate recalls. {g['hq'][:80]}"}
             for g in ds[:6]],
            "Every recall is on the N H T S A site.",
            f"{ten}, five model years: which systems got recalled most.")


def _bd_the_gioi(D, ky):
    r = D.chi_so_the_gioi(ky.get("ma", "NY.GDP.PCAP.CD"), int(ky.get("nam", 2023)), 6)
    if len(r) < 3:
        return None
    return (f"{ky.get('nhan') or 'World ranking'} {ky.get('nam', 2023)}",
            [{"name": _gon(x["nuoc"], 24), "stat": _so(x["gia_tri"]),
              "vo": f"{x['nuoc']}. {_so(x['gia_tri'])}."} for x in r],
            "World Bank open data. Check it yourself.")


def _bd_ho_so_sec(D, ky):
    """Ho so SEC -> bang xep hang theo cong ty nao NHAC nhieu nhat.

    27/8 — bang cu cho `stat` = MAU DON ("8-K"), tuc sau dong cung mot chu, va con mot cap ten
    trung. `_gon(x, 26)` lai cat giua ngoac: "Western Union CO (WU) (CIK" — nhin nhu du lieu hong.
    Dai luong that o day la SO LAN mot cong ty nhac cum tu do trong ho so cua chinh ho: cong ty
    viet "layoff" trong nam ho so khac han cong ty viet mot lan."""
    tk = ky.get("tu_khoa", "layoff")
    r = D.tim_ho_so(tk, n=60)
    if len(r) < 6:
        return None
    import re as _re
    dem: dict = {}
    for x in r:
        ten = str(x.get("cong_ty") or "")
        ten = _re.sub(r"\s*\((?:CIK)?[^)]*\)?\s*$", "", ten).strip(" ,(")   # bo duoi "(WU) (CIK…"
        if not ten:
            continue
        g = dem.setdefault(ten.upper(), {"ten": ten, "n": 0, "mau": set()})
        g["n"] += 1
        g["mau"].add(str(x.get("mau_don") or ""))
    ds = sorted(dem.values(), key=lambda g: -g["n"])
    if len(ds) < 3 or ds[0]["n"] < 2:
        return None
    return (f'Who keeps writing "{tk}" to the S E C',
            [{"name": _gon(g["ten"], 26), "stat": f"{g['n']}x",
              "vo": (f"{_gon(g['ten'], 32)} put it in writing {g['n']} times"
                     + (f", across their {', '.join(sorted(m for m in g['mau'] if m))}" if g["mau"] else "")
                     + ".")} for g in ds[:6]],
            "They filed it themselves. It is public.",
            f'Companies ranked by how many times they wrote "{tk}" in their own S E C filings.')


def _bd_thien_thach(D, ky):
    # 27/8 — `ky["tu_ngay"]` NGOẶC CỨNG giữa một hàng toàn `.get()` có mặc định. Kênh NEAR EARTH
    # xoay trục `den_ngay` (`kho_den_ngay` là danh sách NGÀY KẾT THÚC), còn `tu_ngay` KHÔNG BAO GIỜ
    # có trong `tham_so` — nên mọi lượt đều `KeyError: 'tu_ngay'`. Đo thật: lane NEAREARTH ném 7
    # traceback, ra 0 video, hai phiên liền.
    # API NEO của NASA giới hạn khoảng truy vấn 7 ngày, nên suy `tu_ngay` = `den_ngay` lùi 7 ngày
    # là vừa đúng ràng buộc của nguồn vừa đúng ý kênh (mỗi giá trị trục = một tuần khác nhau).
    from datetime import date as _d, timedelta as _td
    den = str(ky.get("den_ngay") or "").strip()
    tu = str(ky.get("tu_ngay") or "").strip()
    if not tu:
        try:
            tu = (_d.fromisoformat(den) - _td(days=7)).isoformat() if den else ""
        except ValueError:
            tu = ""
    if not tu:
        tu = (_d.today() - _td(days=7)).isoformat()
        den = den or _d.today().isoformat()
    r = D.tieu_hanh_tinh(tu, den or tu, ky.get("key", "DEMO_KEY"), 6)
    if len(r) < 3:
        return None
    return ("Rocks that just passed Earth",
            [{"name": _gon(x["ten"], 22), "stat": f"{x['duong_kinh_m']}m",
              "vo": f"{_gon(x['ten'], 26)}. {x['duong_kinh_m']} meters wide, "
                    f"{x['cach_km'] / 1000:,.0f} thousand kilometers away."} for x in r],
            "N A S A tracks every one of them.")


def _ten_giong_phang(D) -> list:
    """Mọi giống chó của Dog CEO dưới dạng tên phẳng: [(cách viết A, cách viết B)]. MỘT lượt gọi.

    KHÔNG dùng `D.giong_cho()` ở đây: hàm đó gọi thêm một lượt HTTP MỖI GIỐNG để lấy ảnh ngẫu
    nhiên. Với 165 giống thì đó là 165 lượt tuần tự — đo thật: quá 10 phút, chưa xong. Ảnh chỉ cần
    cho 6 con vào chung kết, nên lấy sau; danh sách tên thì một lượt là đủ.

    Dog CEO cất giống hai tầng ({'retriever': ['golden', ...]}) và KHÔNG nhất quán về thứ tự chữ:
    'retriever'/'golden' đọc là "golden retriever", nhưng 'australian'/'shepherd' đọc là
    "australian shepherd" — nhóm đứng trước. Nên trả cả hai thứ tự và để người gọi thử Wikipedia
    bằng cả hai; cãi nhau với quy ước của nguồn thì không bao giờ thắng, thử hai lần thì luôn đúng."""
    d = D._goi("https://dog.ceo/api/breeds/list/all")
    ra = []
    for g, bien in sorted(((d or {}).get("message") or {}).items()):
        g = str(g).strip().lower()
        bs = [str(b).strip().lower() for b in (bien or []) if str(b).strip()]
        if bs:
            ra += [(f"{b} {g}", f"{g} {b}") for b in bs]
        else:
            ra.append((g, g))
    return ra


def _anh_giong(D, ten: str) -> str:
    """Ảnh thật của một giống — chỉ gọi cho các mục ĐÃ vào bảng, không gọi cho cả 165 giống."""
    try:
        p = [x for x in str(ten).lower().split() if x]
        for duong in ("/".join(reversed(p)), "/".join(p)):
            a = D._goi(f"https://dog.ceo/api/breed/{duong}/images/random")
            if (a or {}).get("status") == "success":
                return str(a.get("message") or "")
    except Exception:
        pass
    return ""


def _bd_giong_cho(D, ky):
    """Giong cho -> xep theo LUOT NGUOI TRA WIKIPEDIA 30 ngay qua.

    27/8 — bang cu cho `stat` = so bien the cua giong, ma phan lon giong khong co bien the nao:
    bon trong sau dong hien dau gach "—", hai dong con lai "1 types". Do khong phai bang xep hang,
    do la mot danh sach ten cho.
    Nguon Dog CEO khong co bat ky con so nao — nen phai lay dai luong tu cho khac. Luot doc
    Wikipedia la thu do dung CAI MA NGUOI TA THAT SU QUAN TAM, mien phi, khong can key, va hop
    voi kenh hon han: "giong cho duoc tra nhieu nhat thang nay" la mot video co ly do de xem,
    con "danh sach sau giong cho" thi khong.

    28/8 — TRỤC XOAY `giong` TRƯỚC NAY LÀ MÃ CHẾT.
    Cấu hình kênh BREED FILE khai `"xoay": "giong"` với kho 8 nhóm, nhưng hàm này chưa từng đọc
    `ky`. Nó luôn lấy `giong_cho(24)` — tức 24 giống ĐẦU BẢNG CHỮ CÁI, lượt nào cũng đúng bấy
    nhiêu con — nên tám giá trị trục cho ra đúng MỘT bảng và đúng MỘT tiêu đề ("Borzoi: 25.7K").
    Chống trùng coi cả tám là đã làm ⇒ kênh đăng một video rồi câm hẳn, mà log chỉ ghi "hết kho
    đề tài" nên nhìn như kho cạn chứ không như mã chết.
    Nay `giong` chọn NHÓM giống (retriever · terrier · hound · spaniel …) và xếp hạng trong nhóm
    đó. Mỗi nhóm là một bảng khác hẳn, một tiêu đề khác hẳn, và câu hỏi cũng cụ thể hơn với người
    xem: "giống retriever nào người Mỹ tra nhiều nhất" đáng xem hơn "giống chó nào".
    """
    import datetime as _dt
    nhom = str(ky.get("giong") or "").strip().lower()
    den = _dt.date.today() - _dt.timedelta(days=2)      # Wikimedia tre ~1 ngay
    tu = den - _dt.timedelta(days=30)
    fmt = "%Y%m%d"

    def _luot(*ten_thu):
        """Lượt đọc 30 ngày, thử mấy cách viết tên — trả (tổng, tên đã dùng).

        28/8 — HAI ĐIỀU PHẢI ĐÚNG Ở ĐÂY, cả hai đều đã sai một lần:

        ① TÊN BÀI WIKIPEDIA PHÂN BIỆT HOA THƯỜNG. `luot_doc_bai` chỉ đổi khoảng trắng thành gạch
           dưới rồi ghép thẳng vào đường dẫn, nên "golden retriever" là 404 còn "Golden_Retriever"
           mới ra số. Bản đầu của tôi truyền tên chữ thường từ Dog CEO và nhận **404 cho toàn bộ
           16 giống** — kết luận sai thành "nhóm này không có dữ liệu".

        ② 429 KHÔNG PHẢI LÀ SỐ 0. Wikimedia chặn khi gọi dày, và `luot_doc_bai` trả `[]` cho cả
           hai trường hợp. Coi `[]` là "không ai đọc giống này" thì một cú chặn nhất thời lặng lẽ
           đá một giống ra khỏi bảng xếp hạng — bảng vẫn hiện ra bình thường, chỉ là sai. Nên giãn
           nhịp gọi và thử lại một lần trước khi kết luận là không có.
        """
        import time as _tg
        for bai in ten_thu:
            if not bai:
                continue
            dang = str(bai).title()
            for lan in range(2):
                try:
                    lo = D.luot_doc_bai(dang, tu.strftime(fmt), den.strftime(fmt))
                except Exception:
                    lo = []
                tong = sum(int(d.get("luot_doc") or 0) for d in (lo or []))
                if tong > 0:
                    return tong, dang
                # Giãn nhịp ĐỦ để không tự đâm vào 429, nhưng không hơn: hàm này gọi vài chục
                # lượt cho một video, nghỉ 1 giây mỗi lượt hụt là quá 3 phút — đo thật lần đầu
                # chạy quá 10 phút chưa xong. 0,3s là mức Wikimedia chịu được ở một luồng.
                _tg.sleep(0.3 if lan == 0 else 0.1)
        return 0, ""

    if nhom:
        ung = [x for x in _ten_giong_phang(D) if nhom in x[0] or nhom in x[1]]
        # Trần 14 ứng viên: nhóm `terrier` có 26 giống, mỗi giống thử tới 4 cách viết tên trên
        # Wikimedia = hơn 100 lượt gọi tuần tự cho MỘT video. Mười bốn con là quá đủ để chọn ra
        # sáu đứng đầu, mà vẫn nằm trong ngân sách thời gian của một lane.
        ung = ung[:12]
        if len(ung) < 4:
            # Nhóm quá nhỏ (shepherd chỉ 2, bulldog 3) thì KHÔNG dựng bảng 6 dòng từ 2 con rồi
            # gọi đó là xếp hạng. Trả None để lượt xoay đi tiếp sang nhóm khác — đúng cơ chế sẵn có.
            print(f"   ⚠️ giống chó: nhóm '{nhom}' chỉ có {len(ung)} giống — BỎ LƯỢT, xoay nhóm khác")
            return None
        ds = []
        for a, b in ung:
            tong, ten = _luot(a, b)
            if tong > 0:
                ds.append({"giong": ten.title(), "luot": tong})
            if len(ds) >= 12:
                break
        ds.sort(key=lambda g: -g["luot"])
        # BỎ DÒNG "KHỚP NHẦM BÀI". Tên của Dog CEO không phải tên bài Wikipedia: 'japanese spaniel'
        # thực ra là bài "Japanese Chin", nên tra thẳng ra một bài trùng tên nhưng khác nghĩa và
        # trả về 17 lượt. Đứng cạnh Cocker Spaniel 26.300 thì cột của nó mỏng bằng sợi chỉ — bảng
        # nhìn như lỗi render, mà thật ra là số đúng của một con chó khác.
        #
        # (Đã thử tra tên chuẩn bằng tìm kiếm Wikipedia và BỎ: nó trả 'golden retriever' ->
        #  "Labrador Retriever", 'japanese spaniel' -> "Tibetan spaniel". Gán số thật cho SAI con
        #  chó còn tệ hơn hẳn không tìm thấy bài — không tìm thấy thì mình biết mà bỏ, còn gán sai
        #  thì video vẫn ra và không ai phát hiện.)
        # Dưới 2% mức đầu bảng thì gần như chắc là khớp nhầm, không phải "ít người tra".
        if ds:
            _san = ds[0]["luot"] * 0.02
            ds = [g for g in ds if g["luot"] >= _san]
        if len(ds) < 4:
            print(f"   ⚠️ giống chó: nhóm '{nhom}' chỉ khớp được {len(ds)} bài Wikipedia — "
                  f"BỎ LƯỢT, xoay nhóm khác (không bịa số, không đoán tên)")
            return None
        top = ds[:6]
        for g in top:                       # ảnh chỉ lấy cho 6 mục thật sự lên hình
            g["anh"] = _anh_giong(D, g["giong"])
        return (f"{nhom.title()} breeds America looks up most",
                [{"name": g["giong"], "stat": _gon_so(float(g["luot"])),
                  "vo": f"{g['giong']}: {_gon_so(float(g['luot']))} lookups in thirty days.",
                  "img_url": g.get("anh")} for g in top],
                "Every number is Wikipedia's own public traffic log.",
                f"{nhom.title()} breeds, ranked by how many people quietly looked them up this month.")

    # ĐƯỜNG CHÍNH: xếp hạng TOÀN BỘ giống cấp một, xoay theo CỬA SỔ THỜI GIAN.
    #
    # 28/8 — vì sao không xoay theo nhóm giống (bản thử trước đó). Tên phụ của Dog CEO gần như
    # không bao giờ trùng tên bài Wikipedia: 'chesapeake retriever' thật ra là "Chesapeake Bay
    # Retriever", 'curly retriever' là "Curly-coated Retriever". Đo cả 8 nhóm trong cấu hình thì
    # chỉ `terrier` và `hound` gom đủ 4 bài khớp — hai đề tài cho cả một kênh là vẫn câm.
    # Còn tên CẤP MỘT thì sạch (Beagle, Borzoi, Dalmatian…) và đã chứng minh chạy từ trước.
    # Nên giữ tên cấp một, và lấy cái ĐỔI ĐƯỢC từ chỗ khác: cửa sổ đo. "Giống chó người Mỹ tra
    # nhiều nhất TUẦN QUA" và "… NĂM QUA" là hai bảng khác nhau, hai câu chuyện khác nhau, và
    # đều là số thật của Wikipedia.
    ngay = int(ky.get("lui") or 30)
    den = _dt.date.today() - _dt.timedelta(days=2)
    tu = den - _dt.timedelta(days=max(3, ngay))
    d = D._goi("https://dog.ceo/api/breeds/list/all")
    # Trần 50 giống: Dog CEO có ~98 tên cấp một, và mỗi tên tốn tới hai lượt gọi Wikimedia. Năm
    # mươi con là thừa sức chọn ra sáu đứng đầu, mà giữ được cả hàm trong khoảng một phút — phần
    # đuôi bảng chữ cái toàn giống hiếm, gần như không bao giờ lọt top 6.
    # Bảng cố định không làm video trùng nhau: thứ xoay ở kênh này là CỬA SỔ THỜI GIAN.
    ten_cap1 = sorted(str(g).strip() for g in ((d or {}).get("message") or {}))[:50]
    if len(ten_cap1) < 20:
        return None
    ds = []
    for g in ten_cap1:
        tong, ten = _luot(g)
        if tong > 0:
            ds.append({"giong": ten, "luot": tong})
    ds.sort(key=lambda g: -g["luot"])
    if len(ds) < 4:
        print("   ⚠️ giống chó: không lấy được lượt đọc Wikipedia — BỎ LƯỢT (không bịa số)")
        return None
    top = ds[:6]
    for g in top:                        # ảnh chỉ lấy cho 6 mục thật sự lên hình
        g["anh"] = _anh_giong(D, g["giong"])
    _ky = ("the past week" if ngay <= 9 else "the past month" if ngay <= 45
           else "the past year" if ngay >= 300 else f"the past {ngay} days")
    return (f"Dog breeds America looked up most in {_ky}",
            [{"name": g["giong"], "stat": _gon_so(float(g["luot"])),
              "vo": f"{g['giong']}: {_gon_so(float(g['luot']))} lookups in {_ky}.",
              "img_url": g.get("anh")} for g in top],
            "Every number is Wikipedia's own public traffic log.",
            f"Dog breeds ranked by how many people quietly looked them up in {_ky}.")


def _bd_phim(D, ky):
    tk = ky.get("tu_khoa") or "crime"
    r = D.phim_truyen(tk, 30)
    if ky.get("loc") == "da_huy":
        r = [x for x in r if str(x.get("trang_thai")) in ("Ended", "Canceled", "To Be Determined")]
        r = sorted(r, key=lambda z: -(z.get("diem") or 0))[:6]
        if len(r) < 3:
            return None
        return (f'Great "{tk}" shows that got cut',
                [{"name": _gon(x["ten"], 24), "stat": (f"{x['diem']:.1f}" if x["diem"] else x["nam"]),
                  "vo": f"{_gon(x['ten'], 30)}, rated {x['diem']}, {str(x['trang_thai']).lower()}."}
                 for x in r],
                "Good shows die young.")
    r = sorted(r, key=lambda z: -(z.get("diem") or 0))[:6]
    if len(r) < 3:
        return None
    return (f'Shows: "{tk}"',
            [{"name": _gon(x["ten"], 24), "stat": (f"{x['diem']:.1f}" if x["diem"] else x["nam"]),
              "vo": f"{_gon(x['ten'], 30)}, {x['nam']}, rated {x['diem']}."} for x in r],
            "Ratings from public listings.")


def _bd_bls(D, ky):
    r = D.lay_bls([ky.get("chuoi", "cpi")], int(ky.get("tu_nam", 2019)),
                  int(ky.get("den_nam", 2024))).get(ky.get("chuoi", "cpi")) or []
    if len(r) < 6:
        return None
    # gom theo năm -> mỗi năm một mục, số là mức trung bình năm
    theo_nam = {}
    for x in r:
        theo_nam.setdefault(x["nam"], []).append(x["gia_tri"])
    muc = [{"nam": n, "gt": sum(v) / len(v)} for n, v in sorted(theo_nam.items())][-6:]
    if len(muc) < 3:
        return None
    return (f"{ky.get('nhan') or 'Price index'} by year",
            [{"name": str(m["nam"]), "stat": f"{m['gt']:,.1f}",
              "vo": f"{m['nam']}. {m['gt']:,.1f}."} for m in reversed(muc)],
            "Bureau of Labor Statistics. Official numbers.")


def _ten_mon(x: dict, dai: int = 24) -> str:
    """Ghép hãng + tên sản phẩm thành một cái tên NGƯỜI ĐỌC ĐƯỢC.

    29/8 — khung thật CALORIE SHOCK: cột đầu bảng đề **"Nutella, Nutella"**. Bới dữ liệu thô thì
    Open Food Facts trả:
        hieu = "Nutella, Nutella biscuits"
        ten  = "Biscuits NUTELLA Biscuits Noisettes et Cacao x22 - 304g"
    Trường `brands` là một DANH SÁCH cách nhau bằng dấu phẩy, và nó hay lặp chính nó. Ghép thẳng
    rồi cắt 24 ký tự thì ra đúng "Nutella, Nutella" — nhìn như lỗi hiển thị.
    Còn tên sản phẩm thì mang cả khối lượng và quy cách ("x22 - 304g"), nhiều khi bằng tiếng Pháp
    hoặc tiếng Đức — đó là dữ liệu kho hàng, không phải tên để đọc trên màn hình.

    Ba việc, không đoán gì thêm: lấy HÃNG ĐẦU TIÊN, cắt phần quy cách khỏi tên, và bỏ hãng đi nếu
    tên đã nhắc tới nó rồi."""
    import re as _re
    hieu = " ".join(str(x.get("hieu") or "").split(",")[0].split())
    ten = " ".join(str(x.get("ten") or "").split())
    # Bỏ đuôi quy cách: "x22 - 304g" · "500 g" · "(2 x 125ml)" · "- 6 pack"
    ten = _re.sub(r"[\s,–-]*\(?\s*(?:x\s*\d+|\d+\s*(?:x|×)\s*\d+)?\s*"
                  r"\d*[.,]?\d*\s*(?:g|kg|ml|l|oz|lb|ct|pack|pk)\b\.?\)?\s*$",
                  "", ten, flags=_re.I).strip(" ,-–")
    ten = _re.sub(r"\s*[-–]\s*$", "", ten).strip()
    if not ten:
        ten, hieu = hieu, ""
    # Hãng đã nằm trong tên (dù khác kiểu chữ) thì không ghép thêm.
    if hieu and hieu.lower() not in ten.lower():
        ten = f"{hieu} {ten}"
    return _gon(ten.title(), dai)


def _tu_khoa_mon(mon: str) -> list:
    """Mã phân loại Open Food Facts -> các từ khoá phải thấy trong tên sản phẩm.

    "pizzas" -> ["pizza"] · "breakfast-cereals" -> ["breakfast", "cereal"] · "candies" -> ["candy"]
    Bỏ từ quá ngắn hoặc quá chung ("food", "snack") vì chúng khớp mọi thứ, tức là không lọc gì cả."""
    CHUNG = {"food", "foods", "product", "products", "meal", "meals", "snack", "snacks", "and"}
    ra = []
    for t in str(mon or "").lower().replace("_", "-").split("-"):
        if len(t) < 4 or t in CHUNG:
            continue
        # Số nhiều tiếng Anh không theo MỘT luật: candies->candy nhưng cookies->cookie; cheeses->
        # cheese nhưng fishes->fish. Đoán đúng một dạng là chắc chắn trượt một nửa số nhóm hàng —
        # bản đầu cho ra "cooky", không khớp sản phẩm nào tên Cookie, tức là lọc sạch cả bảng.
        # Nên sinh MỌI dạng có lý rồi khớp-nếu-trúng-một. Đây là lọc thô để loại bánh quy khỏi
        # bảng pizza, không phải phân tích hình thái — thừa một biến thể rẻ hơn hụt một biến thể.
        bien = {t}
        if t.endswith("ies"):
            bien |= {t[:-3] + "y", t[:-1]}
        if t.endswith("es") and len(t) > 5:
            bien.add(t[:-2])
        if t.endswith("s"):
            bien.add(t[:-1])
        ra += sorted(bien)
    return ra


def _mon_an(D, mon, n=30):
    """Dinh dưỡng: Open Food Facts TRƯỚC (mở, không hạn mức), USDA chỉ là đường lùi.

    USDA DEMO_KEY hết 30 lượt/giờ là hai kênh đồ ăn tắt tiếng — đã dính đúng vậy 25/8.

    28/8 — LỌC THEO TÊN, GIỜ MỚI LÀM THẬT. Chú thích cũ ở đây đã viết "lọc theo tên trước", nhưng
    đọc lại thì mã KHÔNG hề lọc, chỉ kiểm `calo` có giá trị. Ý định nằm trong chú thích còn lưới
    thì chưa bao giờ được dựng, nên không ai thấy nó thủng.
    Hậu quả có thật, xem khung của CALORIE SHOCK: tiêu đề "Frozen pizza, by calories" mà ba mục là
    Pauz Pauz, St Michel Palmier, Walker Shortbread - bánh quy, kèm biểu tượng pizza. Nó đến từ
    đường lùi USDA: `foods/search?query=pizzas` là tìm toàn văn, và nó trả về bất cứ thứ gì.
    Người xem không cần biết vì sao; họ chỉ thấy kênh này bịa số. Thà BỎ LƯỢT còn hơn."""
    tk = _tu_khoa_mon(mon)

    def _hop(x):
        if not x.get("calo"):
            return False
        if not tk:
            return True                             # không rút được từ khoá -> không lọc oan
        chu = (str(x.get("hieu") or "") + " " + str(x.get("ten") or "")).lower()
        return any(t in chu for t in tk)

    r = [x for x in D.thanh_phan_off(mon, n) if _hop(x)]
    if len(r) >= 3:
        return r
    return [x for x in D.thanh_phan_mon(mon, n) if _hop(x)]


def _bd_dinh_duong(D, ky):
    mon = ky.get("mon") or "pizza"
    r = _mon_an(D, mon)
    # USDA đặt cùng một `description` cho hàng chục sản phẩm khác hãng ("PIZZA" x 30). Lấy thẳng
    # là ra bảng 6 dòng y hệt nhau — nhìn như lỗi render. Ghép tên hãng để phân biệt, và bỏ trùng.
    thay, muc = set(), []
    for x in sorted(r, key=lambda z: -z["calo"]):
        ten = _ten_mon(x, 26)
        khoa = ten.lower()
        if not ten or khoa in thay:
            continue
        thay.add(khoa)
        muc.append({"name": ten, "stat": f"{x['calo']:.0f} cal",
                    "vo": f"{ten}. {x['calo']:.0f} calories per hundred grams."})
        if len(muc) >= 6:
            break
    if len(muc) < 3:
        return None
    return (f"{ky.get('nhan') or mon.replace('-', ' ').title()}: what is really in it", muc,
            "U S D A measured every one of these.")


def _bd_wiki_bai(D, ky):
    """Đo lượt đọc một DANH SÁCH BÀI CỐ ĐỊNH — dùng khi chủ đề kênh không tự lên bảng xếp hạng.

    26/8 — kênh quan hệ ban đầu lọc chủ đề từ bảng đọc-nhiều: đo thật 4 ngày liên tiếp, mỗi ngày
    991 bài mà khớp 0-1 bài, và bài khớp lại là tên ban nhạc ("My Chemical Romance"). Nguồn không
    sai, chỉ là hỏi sai câu. Hỏi ngược lại: những bài NÀY được đọc bao nhiêu? — vẫn số thật, và
    lần này đúng chủ đề kênh."""
    import datetime as _dt
    import concurrent.futures as _cf
    bai = ky.get("bai") or []
    if not bai:
        return None
    den = _dt.date(int(ky.get("nam", 2026)), int(ky.get("thang", 8)), int(ky.get("ngay", 20)))
    tu = (den - _dt.timedelta(days=29)).strftime("%Y%m%d")
    with _cf.ThreadPoolExecutor(6) as ex:
        ket = list(ex.map(lambda t: (t, D.luot_doc_bai(t, tu, den.strftime("%Y%m%d"))), bai))
    muc = []
    for ten, diem in ket:
        if not diem:
            continue
        tong = sum(x["luot_doc"] for x in diem)
        muc.append({"name": _gon(ten.replace("_", " "), 24), "stat": _so(tong),
                    "_v": tong,
                    "vo": f"{ten.replace('_', ' ')}. {tong:,} reads in thirty days."})
    if len(muc) < 3:
        return None
    muc = sorted(muc, key=lambda z: -z["_v"])[:6]
    for m in muc:
        m.pop("_v", None)
    return (ky.get("nhan") or "What America looks up",
            muc, "Thirty days of quiet curiosity, counted by Wikimedia.")


# 28/8 — PHỤ ĐỀ NÓI RÕ CON SỐ NGHĨA LÀ GÌ.
# Soi khung thật kênh FILINGS SAY (dạng `ranked`, 18/50 kênh dùng): thẻ ghi "7x", "5x", "4x" —
# đúng dữ liệu, nhưng người xem KHÔNG CÓ CÁCH NÀO biết 7x là gì. 7 lần nộp hồ sơ? 7 tỉ? gấp 7?
# Bảng xếp hạng mà không nói đang xếp theo gì thì chỉ là mấy con số xếp cạnh nhau.
# Cùng họ với lỗi thang "1 in 10,000" ở FAME CURVE: dữ liệu đúng, NHÃN không nói được nó là gì.
# Ghi một chỗ theo BỘ CHUYỂN ĐỔI (mỗi bộ biết mình đếm gì) thay vì sửa 15 bộ — thêm bộ thứ 16
# quên khai thì rơi về rỗng, mất phụ đề chứ không hiện phụ đề SAI.
PHU_DE_THEO_BO = {
    "tim_ho_so":      "by filings that mention it",
    "thu_hoi_fda":    "by recalls filed",
    "ban_an":         "by cases on the docket",
    "trieu_hoi_xe":   "by vehicles recalled",
    "hop_dong_lon":   "by contract dollars awarded",
    "bai_duoc_doc":   "by Wikipedia reads",
    "wiki_bai":       "by Wikipedia reads",
    "thong_ke_nba":   "per game, no adjustments",
    "game_steam":     "by players online",
    "chi_so_the_gioi": "by the World Bank's own figure",
    "tieu_hanh_tinh": "by miss distance from Earth",
    "giong_cho":      "by how often people look it up",
    "phim_truyen":    "by episodes that aired",
    "chuoi_bls":      "by the Bureau of Labor Statistics index",
    "thanh_phan_mon": "per serving, as labeled",
}

BO_CHUYEN = {
    "wiki_bai": _bd_wiki_bai,
    "hop_dong_lon": _bd_hop_dong, "thu_hoi_fda": _bd_thu_hoi, "ban_an": _bd_ban_an,
    "bai_duoc_doc": _bd_wiki_top, "thong_ke_nba": _bd_nba, "game_steam": _bd_steam,
    "trieu_hoi_xe": _bd_trieu_hoi, "chi_so_the_gioi": _bd_the_gioi, "tim_ho_so": _bd_ho_so_sec,
    "tieu_hanh_tinh": _bd_thien_thach, "giong_cho": _bd_giong_cho, "phim_truyen": _bd_phim,
    "chuoi_bls": _bd_bls, "thanh_phan_mon": _bd_dinh_duong,
}

TIER = ["S", "A", "A", "B", "B", "C"]


def dung_story_ranked(kenh: dict, ky: dict | None = None) -> dict | None:
    """Story dạng bảng hạng cho một kênh thế hệ 2. None = không đủ dữ liệu, BỎ LƯỢT."""
    import du_lieu_mo as D
    bo = BO_CHUYEN.get(kenh.get("ham"))
    if not bo:
        print(f"   ⚠️ chưa có bộ chuyển đổi cho '{kenh.get('ham')}' — bỏ lượt")
        return None
    # Tham số phải lấy từ CHÍNH KÊNH. Trước đây truyền chung theo nguồn nên PILL FACTS (thuốc) ra
    # tin thu hồi thực phẩm, còn SALARY TRUTH và DEGREE WORTH ra y hệt nhau — đúng cái trùng lặp
    # phải tránh. `ky` truyền vào chỉ để ghi đè khi thử tay.
    ts = dict(kenh.get("tham_so") or {})
    ts.update(ky or {})
    kq = bo(D, ts)
    if not kq:
        print(f"   ⚠️ {kenh.get('ten')}: nguồn không trả đủ dữ liệu — BỎ LƯỢT (không bịa)")
        return None
    # Bộ chuyển đổi được phép trả thêm LỜI MỞ riêng. Cần thiết cho các góc NGƯỢC: bảng hạng
    # mặc định đọc S là "đỉnh", nhưng kênh nghĩa địa game xếp S = vắng nhất — không nói rõ thì
    # người xem hiểu ngược hẳn ý video.
    tieu_de, muc, ket = kq[0], kq[1], kq[2]
    mo = kq[3] if len(kq) > 3 else f"{tieu_de}. Here they are."
    _phu = PHU_DE_THEO_BO.get(str(kenh.get("ham") or ""), "")
    muc = muc[:6]
    # ── CỔNG "BẢNG XẾP HẠNG PHẢI THẬT SỰ XẾP HẠNG" (27/8) ────────────────────────────────────
    # Soi 19 bộ chuyển dữ liệu thì BỐN bộ cho ra bảng mà mọi dòng CÙNG MỘT GIÁ TRỊ:
    #   thu_hoi   -> "Cl.I" ×6   (hạng phân loại FDA, không phải đại lượng)
    #   ban_an    -> "2026" ×6   (năm nộp đơn)
    #   ho_so_sec -> "8-K"  ×6   (mẫu đơn)
    #   giong_cho -> "—"    ×4   (giống không có biến thể)
    # Đây KHÔNG phải chuyện thẩm mỹ. Bảng xếp hạng mà sáu dòng bằng nhau thì người xem nhìn hết
    # 40 giây và không biết thêm được gì — đúng cảm giác "nhàm chán, rẻ tiền" mà anh nói.
    # Đã vá cả bốn, nhưng vá tay thì nguồn thứ 20 lại tái phạm. Chặn ngay tại cổng: bảng nào
    # không mang ít nhất 3 giá trị khác nhau thì BỎ LƯỢT, không dựng. Thà kênh ra ít video hơn
    # còn hơn ra video không nói gì.
    _sts = [str(m.get("stat", "")).strip() for m in muc]
    _kh = len({x for x in _sts if x})
    if len(muc) >= 3 and _kh < min(3, len(muc)):
        print(f"   🚫 {kenh.get('ten')}: bảng xếp hạng chỉ có {_kh} giá trị khác nhau trên "
              f"{len(muc)} mục ({_sts[:3]}) — KHÔNG xếp hạng được gì. BỎ LƯỢT.")
        return None
    _so = sum(1 for x in _sts if any(c.isdigit() for c in x))
    if len(muc) >= 3 and _so < len(muc) - 1:
        print(f"   🚫 {kenh.get('ten')}: {len(muc) - _so}/{len(muc)} mục KHÔNG có con số nào "
              f"({_sts[:3]}) — bảng không đo được gì. BỎ LƯỢT.")
        return None
    items = [{**m, "tier": TIER[min(i, 5)]} for i, m in enumerate(muc)]
    return _cong_an_toan({
        "title": tieu_de,
        "subtitle": _phu,          # xem `PHU_DE_THEO_BO`: nói rõ con số đang xếp theo gì
        "intro_vo": mo,
        "outro_vo": ket,
        "items": items,
        "tiers": sorted({it["tier"] for it in items}, key="SABCDF".index),
        "nguon": kenh.get("nguon"),
        "_that": True,
        "self_score": {"total": 92},
    }, kenh.get("ten", ""))


# ══════════════════════════════════════════════════════════════════════════════════════════
# DẠNG ĐUA CỘT — cần CHUỖI THỜI GIAN, khác hẳn bảng hạng (chỉ cần một lát cắt)
# ------------------------------------------------------------------------------------------
# Mỗi bộ trả (tieu_de, don_vi, frames, loi_dan). frames = [{t, data:[{name, value}]}], >= 4 mốc.
# Nguồn nào KHÔNG có chiều thời gian thì không làm được dạng này — khai `ranked` cho kênh đó
# thay vì bịa ra mốc thời gian giả.
# ══════════════════════════════════════════════════════════════════════════════════════════
def _dc_hop_dong(D, ky):
    """Nhà thầu liên bang đua nhau qua từng năm ngân sách."""
    den = int(ky.get("nam", 2024))
    frames, ten_thay = [], {}
    for nam in range(den - 5, den + 1):
        hd = D.hop_dong_lon(nam, 8, ky.get("de_tai", ""))
        if not hd:
            continue
        # 29/8 — GỘP THEO TÊN ĐÃ CHUẨN HOÁ, giống `_sk_hop_dong`. Khung thật SPACE INVOICE:
        # "Lockheed Martin 26K" và "Lockheed 9.5K" thành HAI hàng đua nhau — cùng một tập đoàn,
        # hai pháp nhân con. PENTAGON LEDGER cũng vậy với "Bae Systems" / "Bae Systems Land".
        # Trong biểu đồ ĐUA thì lỗi này nặng hơn ở bảng tĩnh: hai hàng của cùng một hãng vượt qua
        # nhau suốt video, và người xem đọc ra một cuộc đua không có thật.
        # Tôi đã vá dạng `scaled` sáng nay rồi quên dạng đua — cùng một lỗi, hai bộ dựng.
        gop = {}
        for x in hd:
            t = _ten_hang(x["ten"], 16)
            gop[t] = gop.get(t, 0) + x["tien"] / 1e6
            ten_thay[t] = True
        frames.append({"t": nam, "data": [{"name": k, "value": round(v, 1)}
                                          for k, v in sorted(gop.items(), key=lambda z: -z[1])[:7]]})
    if len(frames) < 4:
        return None
    nhan = (ky.get("de_tai") or "federal").title()
    dan = [f"Six years of {nhan.lower()} contracts.",
           "Same money, different names on the paperwork.",
           f"In {frames[0]['t']}, {frames[0]['data'][0]['name']} led.",
           f"By {frames[-1]['t']}, it was {frames[-1]['data'][0]['name']}.",
           "All of it filed on USAspending dot gov."]
    return (f"{nhan} contracts by year", "$M", frames, dan)


def _dc_bls(D, ky):
    """Nhiều nhóm giá đua nhau — MỘT lượt gọi cho tất cả chuỗi (BLS chỉ 25 lượt/ngày)."""
    nhom = ky.get("nhom") or ["cpi_thucpham", "cpi_xang", "cpi_nha", "cpi_yte", "cpi_di_lai", "cpi_giao_duc"]
    NHAN = {"cpi_thucpham": "Food", "cpi_xang": "Gas", "cpi_nha": "Housing", "cpi_yte": "Health",
            "cpi_di_lai": "Transport", "cpi_giao_duc": "Education", "cpi_dien_nuoc": "Utilities",
            "cpi_quan_ao": "Clothing", "cpi_giai_tri": "Recreation", "luong_gio": "Hourly pay"}
    tu, den = int(ky.get("tu_nam", 2015)), int(ky.get("den_nam", 2024))
    bo = D.lay_bls(nhom, tu, den)
    theo_nam = {}
    for ten, diem in bo.items():
        for x in diem:
            theo_nam.setdefault(x["nam"], {}).setdefault(ten, []).append(x["gia_tri"])
    frames = []
    for nam in sorted(theo_nam):
        data = [{"name": NHAN.get(t, t), "value": round(sum(v) / len(v), 1)}
                for t, v in theo_nam[nam].items() if v]
        if len(data) >= 3:
            frames.append({"t": nam, "data": sorted(data, key=lambda z: -z["value"])[:7]})
    if len(frames) < 4:
        return None
    d0, d1 = frames[0]["data"][0], frames[-1]["data"][0]
    dan = ["Watch what got expensive in America.",
           f"Back in {frames[0]['t']}, {d0['name'].lower()} sat on top.",
           f"Ten years later, {d1['name'].lower()} is still climbing.",
           "These are the official index numbers, not estimates.",
           "Bureau of Labor Statistics. Check any line yourself."]
    return ("Cost of living, by category", "idx", frames, dan)


def _dc_mlb(D, ky):
    """Các đội bóng chày đua thành tích qua nhiều mùa."""
    den = int(ky.get("nam", 2025))
    frames = []
    for nam in range(den - 5, den + 1):
        r = D.thong_ke_mlb(nam, 8)
        if len(r) >= 4:
            frames.append({"t": nam, "data": [{"name": _gon(x["doi"], 16), "value": x["thang"]}
                                              for x in r[:7]]})
    if len(frames) < 4:
        return None
    dan = ["Six seasons of baseball, side by side.",
           f"{frames[0]['data'][0]['name']} opened on top.",
           f"{frames[-1]['data'][0]['name']} finished there.",
           "Wins only. No opinions.",
           "Straight from the league's own stat feed."]
    return ("MLB wins by season", "W", frames, dan)


def _dc_wiki(D, ky):
    """Bài Wikipedia được đọc nhiều nhất đua nhau qua từng ngày."""
    import datetime as _dt
    # 27/8 — TRỤC `lui` (số ngày lùi) phải được HIỂU Ở MỌI BỘ DỰNG đọc bảng Wikipedia, không
    # chỉ ở `_bd_wiki_top`. Selftest bắt được: 3 kênh đi qua bộ dựng khác (`_pk_wiki` cho dạng
    # phim, `_dc_wiki` cho dạng đua) vốn không đọc `lui` -> chúng lặng lẽ dùng NGÀY MẶC ĐỊNH cho
    # cả 13 giá trị xoay. Bài kiểm tay của em bị lừa: thấy 13/13 "chạy được" mà thực chất là 13
    # lần cùng một ngày, tức 13 video trùng nhau — đúng lỗi SKY RIGHT NOW cũ.
    if ky.get("lui") is not None:
        goc = _dt.date.today() - _dt.timedelta(days=int(ky["lui"]))
    else:
        goc = _dt.date(int(ky.get("nam", 2026)), int(ky.get("thang", 8)), int(ky.get("ngay", 20)))
    _TH_G = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def _ngay_goc(d):
        """20260813 -> "Aug 13". Hỏng thì trả nguyên chuỗi, không ném."""
        t = str(d)
        try:
            return f"{_TH_G[int(t[4:6])]} {int(t[6:8])}"
        except Exception:
            return t

    dau = D.bai_duoc_doc(goc.year, goc.month, goc.day, 7)
    if len(dau) < 4:
        return None
    ten = [x["ten"] for x in dau]
    tu = (goc - _dt.timedelta(days=13)).strftime("%Y%m%d")
    den = goc.strftime("%Y%m%d")
    chuoi = {}
    for t in ten:
        chuoi[t] = {x["ngay"]: x["luot_doc"] for x in D.luot_doc_bai(t, tu, den)}
    ngays = sorted({d for v in chuoi.values() for d in v})
    frames = []
    for d in ngays:
        data = [{"name": _gon(t, 16), "value": round(chuoi[t].get(d, 0) / 1000.0, 1)}
                for t in ten if chuoi[t].get(d)]
        if len(data) >= 3:
            # 28/8 — ĐỒNG HỒ CỦA BIỂU ĐỒ ĐUA IN NGUYÊN MÃ NGÀY.
            # Anh gửi khung AMERICA LOOKED UP: góc phải trên hiện **"20260741"** cỡ chữ lớn nhất
            # khung hình. Đó là khoá ngày `YYYYMMDD` của Wikimedia, đưa thẳng vào chỗ đáng ra để
            # in NĂM. Với người xem thì đó là một dãy số vô nghĩa chiếm chỗ đẹp nhất màn hình —
            # và là dấu hiệu rõ nhất rằng video do máy nhả ra không ai xem lại.
            # Các bộ dựng đua khác truyền `nam` (một số nguyên bốn chữ số) nên đồng hồ đọc đúng;
            # riêng đường này đếm theo NGÀY nên phải tự đổi sang chữ người đọc được.
            frames.append({"t": _ngay_goc(d), "data": sorted(data, key=lambda z: -z["value"])[:7]})
    if len(frames) < 4:
        return None
    dan = ["Two weeks of what America actually read.",
           f"{frames[-1]['data'][0]['name']} ended on top.",
           "Every spike is a real day, a real story breaking.",
           "Nobody votes on this. People just click.",
           "Counts published by Wikimedia."]
    return ("Most-read on Wikipedia", "K reads", frames, dan)


def _dc_nba(D, ky):
    """Cầu thủ dẫn đầu đua nhau qua nhiều mùa giải."""
    ma = ky.get("chi_tieu") or "PTS"
    mua_cuoi = int(str(ky.get("mua", "2024-25")).split("-")[0])
    frames = []
    for y in range(mua_cuoi - 5, mua_cuoi + 1):
        r = D.thong_ke_nba(f"{y}-{str(y + 1)[-2:]}", ma, 8)
        if len(r) >= 4:
            frames.append({"t": y, "data": [{"name": _gon(x["ten"], 16), "value": x["gia_tri"]}
                                            for x in r[:7]]})
    if len(frames) < 4:
        return None
    nhan = {"PTS": "points", "AST": "assists", "REB": "rebounds"}.get(ma, ma.lower())
    # 28/8 — ĐƠN VỊ PHẢI LÀ MỘT TỪ VIẾT TẮT CÓ THẬT, KHÔNG PHẢI BA KÝ TỰ ĐẦU.
    # Xem props thật của COURT KINGS: `hookStat = "33 poi"`. Số dẫn to nhất khung hình, 0-3 giây
    # đầu, ghi một chữ không tồn tại trong tiếng Anh — vì đơn vị lấy bằng `nhan[:3]`, và
    # "points"[:3] ra "poi". Cắt chuỗi theo SỐ KÝ TỰ để lấy chữ viết tắt là đoán, và đoán sai ở
    # đúng chỗ đắt nhất. Bóng rổ vốn đã có sẵn ba chữ viết tắt ai cũng đọc được.
    vtat = {"points": "pts", "assists": "ast", "rebounds": "reb"}.get(nhan, ma.lower())
    dan = [f"Six seasons of {nhan} leaders.",
           f"{frames[0]['data'][0]['name']} started on top.",
           f"{frames[-1]['data'][0]['name']} is there now.",
           "Per game, no adjustments.",
           "Numbers from the league's own feed."]
    return (f"NBA {nhan} leaders", vtat, frames, dan)


def _dc_epa(D, ky):
    """Mức tiêu thụ xăng của các mẫu xe đổi qua từng đời."""
    hang = ky.get("hang") or "Toyota"
    den = int(ky.get("nam", 2024))
    # fueleconomy.gov cần 3 lượt cho MỖI mẫu xe (model -> options -> chi tiết). Sáu năm x bảy mẫu
    # là ~126 lượt nối đuôi nhau, chạy tuần tự thì quá hai phút và lane sẽ hết giờ. Các năm độc
    # lập nhau nên chạy song song, và giảm còn 5 mẫu/năm — đủ cho một khung đua cột.
    import concurrent.futures as _cf
    nams = list(range(den - 5, den + 1))
    with _cf.ThreadPoolExecutor(6) as ex:
        ket = list(ex.map(lambda n: (n, D.muc_tieu_thu(n, hang, 5)), nams))
    frames = []
    for nam, r in sorted(ket):
        if len(r) >= 4:
            frames.append({"t": nam, "data": [{"name": _gon(x["xe"].replace(hang, "").strip(), 16),
                                               "value": x["ket_hop"]} for x in r[:7]]})
    if len(frames) < 4:
        return None
    dan = [f"Six model years of {hang}.",
           "Same badge, very different numbers.",
           f"{frames[-1]['data'][0]['name']} leads the current lineup.",
           "Combined mileage, measured by the E P A.",
           "Not the ad. The lab test."]
    return (f"{hang}: miles per gallon", "mpg", frames, dan)


BO_DUA = {"hop_dong_lon": _dc_hop_dong, "chuoi_bls": _dc_bls, "thong_ke_mlb": _dc_mlb,
          "bai_duoc_doc": _dc_wiki, "thong_ke_nba": _dc_nba, "muc_tieu_thu": _dc_epa}


def _keo_dai(dan: list[str], frames: list[dict], don_vi: str) -> list[str]:
    """Thêm câu RÚT TỪ CHÍNH DỮ LIỆU cho đủ độ dài short (>=20s).

    QC chặn video dọc dưới 20 giây. Năm câu dẫn chỉ ra ~15s. Không kéo dài bằng câu đưa đẩy —
    tính thẳng từ frames: ai tăng mạnh nhất, khoảng cách đầu-cuối bao nhiêu. Vẫn là số có thật."""
    dau = {d["name"]: d["value"] for d in frames[0]["data"]}
    cuoi = {d["name"]: d["value"] for d in frames[-1]["data"]}
    chung = [t for t in cuoi if t in dau and dau[t]]
    them = []
    if chung:
        tang = max(chung, key=lambda t: (cuoi[t] - dau[t]) / dau[t])
        pc = (cuoi[tang] - dau[tang]) / dau[tang] * 100
        if pc >= 1:
            them.append(f"{tang} moved the most: up {pc:.0f} percent.")
    if len(frames[-1]["data"]) >= 2:
        a, b = frames[-1]["data"][0], frames[-1]["data"][1]
        if b["value"]:
            them.append(f"{a['name']} now sits {a['value'] / b['value']:.1f} times above {b['name']}.")
    them.append(f"{len(frames)} points on the chart. Every one of them filed, not guessed.")
    them.append("Save this before the next update changes it.")
    return dan + them


def dung_story_race(kenh: dict, ky: dict | None = None) -> dict | None:
    """Story dạng đua cột. None = nguồn không có chiều thời gian hoặc thiếu mốc -> BỎ LƯỢT."""
    import du_lieu_mo as D
    bo = BO_DUA.get(kenh.get("ham"))
    if not bo:
        print(f"   ⚠️ {kenh.get('ten')}: '{kenh.get('ham')}' chưa có bộ dựng đua cột — bỏ lượt")
        return None
    ts = dict(kenh.get("tham_so") or {})
    ts.update(ky or {})
    kq = bo(D, ts)
    if not kq:
        print(f"   ⚠️ {kenh.get('ten')}: không đủ mốc thời gian — BỎ LƯỢT (không bịa mốc)")
        return None
    tieu_de, don_vi, frames, dan = kq
    # 27/8 — SẮP MỌI KHUNG TẠI ĐÂY, KHÔNG TIN NGUỒN ĐÃ SẮP SẴN.
    #
    # Xem tận mắt khung hình thật của AMERICA LOOKED UP mới lòi ra: `BarChartRace.tsx` TỰ SẮP lúc
    # vẽ (dòng 51 và 59) — đúng vì `data` vào tay nó không có thứ tự bảo đảm. Nhưng phía Python thì
    # BA chỗ lại coi `data[0]` là kẻ dẫn đầu:
    #     `_so_noi_bat`  -> số dẫn của hook 0-3 giây
    #     `_keo_dai`     -> câu ĐỌC THÀNH TIẾNG "X now sits N times above Y"
    #     `_dc_nba`/`_dc_epa` -> câu "… started on top" / "… leads the current lineup"
    # Trong 6 bộ dựng đua chỉ `_dc_wiki` tự sắp; năm cái còn lại trông chờ NGUỒN trả về đúng thứ
    # tự — một giả định không ai bảo đảm và không ai kiểm. Hôm nào nguồn đổi thứ tự trả về là hook
    # nêu nhầm người, và lời đọc nêu nhầm tỉ lệ ("gấp 0.4 lần") — sai dữ liệu, không phải sai
    # thẩm mỹ, mà lại là loại sai không có gì báo động.
    # Vá từng chỗ thì lần sau thêm bộ dựng thứ bảy là lại sót. Sắp ở đây — đúng một cửa mà mọi
    # dạng đua đều phải qua — thì `data[0]` mang đúng nghĩa mà mọi người gọi vốn đã tưởng nó mang.
    for _fr in frames:
        _fr["data"] = sorted(_fr.get("data") or [], key=lambda z: -(z.get("value") or 0))
    dan = _keo_dai(dan, frames, don_vi)
    return _cong_an_toan({"title": tieu_de, "unit": don_vi, "frames": frames, "narration": dan,
                          "nguon": kenh.get("nguon"), "_that": True,
                          "self_score": {"total": 92}}, kenh.get("ten", ""))


# ══════════════════════════════════════════════════════════════════════════════════════════
# DẠNG PHIM KỂ — dùng cho niche mà bảng số không kể được (án, bí ẩn, nghiên cứu, tư liệu)
# ------------------------------------------------------------------------------------------
# Trả (tieu_de, cau_hook, [{nar, img_query}]). `img_query` là PROMPT VẼ, được ghép thêm `style_anh`
# của kênh ở dung_story_cinematic — đó là chỗ mỗi kênh giữ một gu hình riêng suốt đời.
# Lời kể lấy TỪ BẢN GHI: tên vụ, ngày, toà, trích đoạn. AI không tham gia ở đây.
# ══════════════════════════════════════════════════════════════════════════════════════════
# 29/8 — PROMPT VẼ KHÔNG ĐƯỢC GỌI TÊN THỨ CÓ MẶT CHỮ.
# Anh: "ko nên có chữ ở ảnh AI generate" — và chữ bịa trên một kênh hồ sơ công CHÍNH LÀ nội dung
# sai sự thật, không chỉ là chuyện xấu mã.
# Đã thử bốn vòng chỉnh lệnh cho máy vẽ: cấm ở đuôi prompt, cấm ở đầu prompt, bảo "mọi mặt giấy
# đều trống", bảo "vẽ chữ thành nét nguệch ngoạc". Khung vẫn lần lượt ra "COURTE OPITION",
# "NEW YORKE", "PUBLLTC RECORD", "ourt Opitric". Kết luận đo được sau bốn lần: mô hình khuếch tán
# KHÔNG có khái niệm "đừng vẽ", nó chỉ có khái niệm "vẽ cái gì" — hễ prompt gọi tên một tờ giấy
# thì nó dựng một mặt phẳng, và mặt phẳng nào cũng được nó điền chữ vào.
# Nên bỏ hẳn mặt phẳng ra khỏi khung: hồ sơ nhìn TỪ CẠNH, ngăn kéo kéo ra, gáy sách xếp hàng.
# Vẫn đúng chủ thể, người xem vẫn đọc ra ngay là hồ sơ toà — mà không còn chỗ nào để bịa chữ.
def _pk_ban_an(D, ky):
    r = D.ban_an(ky.get("tu_khoa", "wrongful death"), 4)
    if not r:
        return None
    v = r[0]
    nam = str(v["ngay"])[:4]
    trich = " ".join(str(v["trich"] or "").split())[:150]
    canh = [
        (f"This case is real. {_gon(v['ten_vu'], 60)}.", "empty american courtroom, morning light"),
        (f"Filed in {nam}.", "stack of closed manila folders tied with string, seen edge-on, deep shadow"),
        (f"The court: {_gon(v['toa'], 50)}.", "neoclassical courthouse columns seen from below against the sky"),
        (f"From the opinion: {trich}." if trich else "The opinion runs for pages.",
         "a wooden gavel resting on its block, shallow depth of field"),
        (f"There are {len(r)} more like it filed under the same words.",
         "long row of archive shelves, binder spines edge-on receding into shadow"),
        ("Every line of this is public record. Anyone can pull it.",
         "a brass filing cabinet drawer pulled open, folder tabs seen edge-on"),
    ]
    return (_gon(v["ten_vu"], 46), f"A {nam} case almost nobody read.", canh)


def _pk_wiki(D, ky):
    loc = ky.get("loc") or "" 
    # Mỗi bộ lọc có (nhận, LOẠI TRỪ). Không có vế loại trừ thì hai kênh lọc chồng nhau sẽ cùng
    # chọn đúng một bài — đo thật: UNSOLVED LOG và MISSING PIECE cùng ra "Disappearance of Marvin
    # Clark". Và "city" từng bắt nhầm "Manchester City F.C." vào kênh địa danh, nên bỏ hẳn từ đó.
    TU = {"bi_an":    (("mystery", "unsolved", "unexplained", "cryptid", "hoax", "conspiracy"),
                       ("missing", "disappear", "vanish")),
          "mat_tich": (("missing", "disappear", "vanish", "lost at sea"), ()),
          # Từ đơn bắt nhầm tên người ("Jessie Cave" là diễn viên, không phải hang). Chỉ nhận CỤM
          # chỉ địa danh, nơi chữ đứng sau mới xác định đó là một chỗ trên bản đồ.
          "dia_diem": ((" island", " mountains", " national park", " volcano", " canyon",
                        " desert", " glacier", "mount ", " peninsula", " archipelago",
                        " rainforest", " strait"), ("f.c.", "united", "album", "film", "song")),
          "ca_dem":   (("murder", "killing", "homicide", "night shift", "serial"), ("film", "song"))}
    cap = TU.get(loc)

    def _loc(ds):
        if not cap:
            return ds
        nhan, tru = cap
        return [x for x in ds
                if any(t in x["ten"].lower() for t in nhan)
                and not any(t in x["ten"].lower() for t in tru)]

    # Một ngày cụ thể có thể không có bài nào thuộc chủ đề kênh (kênh địa danh gặp ngày toàn tin
    # thể thao). Bỏ lượt là đúng nguyên tắc nhưng kênh sẽ trống liên miên. Lùi dần tối đa 10 ngày:
    # vẫn là bảng đọc THẬT, chỉ là của một ngày khác — không bịa gì thêm.
    import datetime as _dt
    # 27/8 — TRỤC `lui` (số ngày lùi) phải được HIỂU Ở MỌI BỘ DỰNG đọc bảng Wikipedia, không
    # chỉ ở `_bd_wiki_top`. Selftest bắt được: 3 kênh đi qua bộ dựng khác (`_pk_wiki` cho dạng
    # phim, `_dc_wiki` cho dạng đua) vốn không đọc `lui` -> chúng lặng lẽ dùng NGÀY MẶC ĐỊNH cho
    # cả 13 giá trị xoay. Bài kiểm tay của em bị lừa: thấy 13/13 "chạy được" mà thực chất là 13
    # lần cùng một ngày, tức 13 video trùng nhau — đúng lỗi SKY RIGHT NOW cũ.
    if ky.get("lui") is not None:
        goc = _dt.date.today() - _dt.timedelta(days=int(ky["lui"]))
    else:
        goc = _dt.date(int(ky.get("nam", 2026)), int(ky.get("thang", 8)), int(ky.get("ngay", 20)))
    r = []
    for lui in range(0, 10):
        d = goc - _dt.timedelta(days=lui)
        r = _loc(D.bai_duoc_doc(d.year, d.month, d.day, 1000))
        if r:
            break
    if not r:
        return None
    v = r[0]
    canh = [
        (f"On one single day, {v['luot_doc']:,} people looked up {v['ten']}.",
         "a phone lying face-down on a dark table, one hard light source, long shadow"),
        (f"It ranked number {v['hang']} across all of Wikipedia that day.",
         "a wall of monitors seen from BEHIND, cable bundles and glow spilling round the edges"),
        ("Nobody organised that. People just wanted to know.",
         "crowd of people walking, all looking down at phones"),
        (f"The second most read that day was {r[1]['ten']}." if len(r) > 1
         else "The rest of the list was ordinary news.",
         "rolled newspapers stacked and bound with twine, seen from the ends"),
        ("Curiosity leaves a trace. This is what it looks like counted.",
         "a single rising line traced through condensation on cold glass, no axes or ticks"),
        ("Wikimedia publishes these numbers every single day.",
         "server room corridor with blue indicator lights"),
    ]
    return (_gon(v["ten"], 46), f"{v['luot_doc']:,} people looked this up in one day.", canh)


def _pk_nghien_cuu(D, ky):
    r = D.nghien_cuu(ky.get("tu_khoa", "sleep"), 4)
    if not r:
        return None
    v = r[0]
    canh = [
        (f"A real study, published in {v['nam']}.", "a stack of medical journals on a desk"),
        (f"The title: {_gon(v['tieu_de'], 110)}.", "a microscope eyepiece and slide tray on a lab bench, shallow focus"),
        (f"It ran in {v['tap_chi']}.", "library shelf of bound medical journals"),
        ("Not a headline about a study. The study itself.",
         "a microscope and specimen jars under a desk lamp cone, night lab"),
        (f"There are {len(r)} more on the same question, all public.",
         "a monitor seen from behind, cool blue glow washing across an empty desk"),
        (f"Reference number {v['ma']} on PubMed. Go read it.",
         "a mechanical keyboard lit from one side, keys out of focus"),
    ]
    return (_gon(v["tieu_de"], 46), f"One real study on {ky.get('tu_khoa', 'this')}.", canh)


def _pk_nhac(D, ky):
    r = D.ho_so_nhac(ky.get("tu_khoa", "one hit wonder"), 4)
    r = [x for x in r if x.get("bat_dau")]
    if not r:
        return None
    v = r[0]
    canh = [
        (f"{v['ten']}. Started {v['bat_dau'][:4]}.", "turntable tonearm and needle in extreme close-up, record grooves catching the light"),
        (f"Type: {v['loai'] or 'artist'}. Country: {v['nuoc'] or 'unlisted'}.",
         "a worn leather suitcase with buckled straps, closed, travel stickers scraped off"),
        ((f"The record says it ended in {v['ket_thuc'][:4]}." if v.get("ket_thuc")
          else "The record has no end date."), "empty concert stage under one hard spotlight, smoke in the beam, cables coiled"),
        ("This is the catalogue entry, not the legend.",
         "a wooden card-index drawer pulled open, card edges seen from above, no faces visible"),
        ("MusicBrainz keeps it because somebody had to.",
         "a vinyl record sleeve seen edge-on, records fanned in a crate"),
        ("Every credit here can be checked in a minute.",
         "a mixing desk fader bank glowing in a dark studio"),
    ]
    return (_gon(v["ten"], 46), f"{v['ten']}, on paper.", canh)


def _pk_tu_lieu(D, ky):
    import re as _re
    r = D.phim_tu_lieu(ky.get("tu_khoa", "america 1950"), 20)
    # Archive.org nhiều mục chỉ có MÃ LƯU TRỮ làm tiêu đề ("205471_Home_Movie_010144"). Đọc lên
    # nghe như lỗi. Chỉ nhận tiêu đề người đọc được: ít nhất hai từ chữ cái thật.
    def _doc_duoc(t: str) -> bool:
        t = str(t or "").strip()
        # mã lưu trữ nhận ra ở hai dấu: dính gạch dưới, và không có khoảng trắng nào
        return (" " in t and "_" not in t and "#" not in t
                and len(_re.findall(r"[A-Za-z]{3,}", t)) >= 2
                and not _re.search(r"\d{5,}", t))

    r = [x for x in r if _doc_duoc(x.get("tieu_de"))]
    if not r:
        return None
    v = r[0]
    canh = [
        (f"This film belongs to nobody. {_gon(v['tieu_de'], 70)}.",
         "old film reel in a metal canister"),
        (f"Year on the record: {v['nam'] or 'unlisted'}.", "a mid-century wall clock with chipped paint, raking afternoon light"),
        ("Public domain means you can use it, sell it, cut it up.",
         "projector throwing light in a dusty room"),
        (f"There are {len(r)} more like it under the same search.",
         "shelves of film canisters in an archive"),
        ("Nobody is coming to take it down.",
         "empty archive reading room with warm light"),
        ("The Internet Archive keeps the copy.",
         "hard drives stacked in a preservation rack"),
    ]
    return (_gon(v["tieu_de"], 46), "A film that belongs to nobody.", canh)


BO_PHIM = {"ban_an": _pk_ban_an, "bai_duoc_doc": _pk_wiki, "nghien_cuu": _pk_nghien_cuu,
           "ho_so_nhac": _pk_nhac, "phim_tu_lieu": _pk_tu_lieu}


def dung_story_cinematic(kenh: dict, ky: dict | None = None) -> dict | None:
    """Story dạng phim kể. Ghép `style_anh` của kênh vào từng prompt vẽ."""
    import du_lieu_mo as D
    bo = BO_PHIM.get(kenh.get("ham"))
    if not bo:
        print(f"   ⚠️ {kenh.get('ten')}: '{kenh.get('ham')}' chưa có bộ dựng phim kể — bỏ lượt")
        return None
    ts = dict(kenh.get("tham_so") or {})
    ts.update(ky or {})
    kq = bo(D, ts)
    if not kq:
        print(f"   ⚠️ {kenh.get('ten')}: nguồn không trả dữ liệu — BỎ LƯỢT")
        return None
    tieu_de, hook, canh = kq
    # Gu vẽ phải là TIẾNG ANH — máy vẽ ảnh không đọc tiếng Việt và sẽ lặng lẽ rơi về mặc định
    # của nó (ảnh chụp người thật). Xem `gu_ve`.
    gu = gu_ve(kenh)
    scenes = [{"nar": nar, "img_query": (f"{q}, {gu}" if gu else q)} for nar, q in canh]
    return _cong_an_toan({"title": tieu_de, "hook": hook, "topic": kenh.get("niche", ""),
                          "scenes": scenes, "nguon": kenh.get("nguon"),
                          "thumb_hook": hook, "thumb_stat": "", "thumb_label": tieu_de[:30],
                          "_that": True, "self_score": {"total": 92}}, kenh.get("ten", ""))


# ══════════════════════════════════════════════════════════════════════════════════════════
# DẠNG SO KÍCH THƯỚC — mọi thứ quy về MỘT thang, để mắt thấy được chênh lệch
# ------------------------------------------------------------------------------------------
# Trả (tieu_de, don_vi, [{name, emoji, value, disp}], loi_ket). Giá trị phải CÙNG đơn vị, nếu
# không thì thanh dài ngắn chẳng nói lên gì.
# ══════════════════════════════════════════════════════════════════════════════════════════
def _sk_dinh_duong(D, ky):
    """So calo — LẤY TRẢI ĐỀU CẢ DẢI, không lấy 6 mục cao nhất.

    28/8 — xem khung thật CALORIE SHOCK: sáu cột cao gần bằng nhau, 599/534/529/526/525/517.
    Không sai số nào, nhưng một video tên là SCALED mà sáu cột nhìn như một thì chẳng nói được gì:
    người xem không rút ra được điều gì họ chưa biết. Gốc là phép chọn — sắp giảm dần rồi cắt 6 mục
    đầu thì bao giờ cũng ra sáu giá trị sát nhau, vì đó là sáu giá trị sát trần.
    Lấy trải đều từ cao nhất xuống thấp nhất thì cùng bấy nhiêu dữ liệu thật, cùng một nguồn, mà
    cột cao nhất gấp đôi ba cột thấp nhất — CÓ chuyện để kể. Mục #1 luôn giữ (nó là hook), phần
    còn lại chia đều khoảng cách trên danh sách đã sắp."""
    mon = ky.get("mon") or "pizza"
    r = _mon_an(D, mon)
    thay, sach = set(), []
    for x in sorted(r, key=lambda z: -z["calo"]):
        ten = _ten_mon(x, 24)
        if not ten or ten.lower() in thay:
            continue
        thay.add(ten.lower())
        sach.append({"name": ten, "emoji": "🍕", "value": round(x["calo"]),
                     "disp": f"{x['calo']:.0f} cal"})
    if len(sach) < 3:
        return None
    if len(sach) <= 6:
        muc = sach
    else:
        vt = sorted({0} | {round(i * (len(sach) - 1) / 5) for i in range(1, 6)})
        muc = [sach[i] for i in vt]
    return (f"{ky.get('nhan') or mon.replace('-', ' ').title()}, by calories", "cal", muc,
            "Per hundred grams, measured by the U S D A.")


def _sk_bls(D, ky):
    """So các nhóm chi phí trên CÙNG một thang chỉ số — một lượt gọi cho tất cả."""
    nhom = ky.get("nhom") or ["cpi_yte", "cpi_nha", "cpi_giao_duc", "cpi_thucpham", "cpi_di_lai", "cpi_quan_ao"]
    NHAN = {"cpi_yte": ("Health care", "🏥"), "cpi_nha": ("Housing", "🏠"),
            "cpi_giao_duc": ("Education", "🎓"), "cpi_thucpham": ("Food", "🛒"),
            "cpi_di_lai": ("Transport", "🚌"), "cpi_quan_ao": ("Clothing", "👕"),
            "cpi_xang": ("Gas", "⛽"), "luong_gio": ("Hourly pay", "💵"),
            "cpi_dien_nuoc": ("Utilities", "💡"), "cpi_giai_tri": ("Fun", "🎟️")}
    den = int(ky.get("den_nam", 2024))
    bo = D.lay_bls(nhom, den - 1, den)
    muc = []
    for t, diem in bo.items():
        if not diem:
            continue
        v = sum(x["gia_tri"] for x in diem[-12:]) / max(1, len(diem[-12:]))
        ten, em = NHAN.get(t, (t, "📊"))
        muc.append({"name": ten, "emoji": em, "value": round(v, 1), "disp": f"{v:,.0f}"})
    if len(muc) < 3:
        return None
    muc = sorted(muc, key=lambda z: -z["value"])[:6]
    # Tiêu đề phải theo NHÃN CỦA KÊNH. Để tiêu đề cứng thì hai kênh cùng nguồn ra y hệt nhau dù
    # tham số khác — đúng lỗi đã dính một lần với PAYCHECK GAP và HOUSE MATH.
    return (ky.get("nhan") or f"What costs the most in {den}", "idx", muc,
            "Same index, same base year. Bureau of Labor Statistics.")


def _sk_the_gioi(D, ky):
    """So chỉ số quốc gia — LẤY TRẢI ĐỀU CẢ BẢNG, không lấy 6 nước đứng đầu.

    28/8 — cùng một gốc với lỗi bảng calo: sáu nước đứng đầu một bảng thế giới bao giờ cũng sát
    trần nhau. Đo thật: WILD NUMBERS ra 94.5 / 92.1 / 91.2 / 90.4 / 90.1 / 87.1 (chênh 8%), và
    MARRIAGE MATH ra 6.3 / 6.2 / 6.1 / 6.1 / 6.0 / 5.7 (chênh 10%). Sáu cột cao gần bằng nhau
    trong một video mang tên SCALED — người xem không rút ra được gì họ chưa biết.
    Trải đều từ nước cao nhất xuống nước thấp nhất thì vẫn đúng bấy nhiêu dữ liệu, cùng một nguồn,
    mà độ che phủ rừng đi từ 94% xuống dưới 1%. ĐÓ mới là thứ đáng làm thành một video so kích cỡ.
    Nước #1 luôn giữ (nó là hook); năm mục còn lại chia đều vị trí trên bảng đã sắp."""
    r = D.chi_so_the_gioi(ky.get("ma", "NY.GDP.PCAP.CD"), int(ky.get("nam", 2023)), 200)
    if len(r) < 3:
        return None
    if len(r) > 6:
        vt = sorted({0} | {round(i * (len(r) - 1) / 5) for i in range(1, 6)})
        r = [r[i] for i in vt]
    muc = [{"name": _gon(x["nuoc"], 22), "emoji": "🌍", "value": round(x["gia_tri"], 1),
            "disp": _so(x["gia_tri"])} for x in r]
    return (f"{ky.get('nhan') or 'World ranking'} {ky.get('nam', 2023)}", "", muc,
            "World Bank open data.")


def _ten_hang(ten: str, dai: int = 22) -> str:
    """Tên nhà thầu đã CHUẨN HOÁ để gộp — bỏ đuôi pháp nhân và mạo từ.

    29/8 — sau khi gộp theo tên, bảng vẫn ra "Lockheed Martin" và "Lockheed Martin Corp" thành
    HAI dòng: cùng một hãng, hai cách nguồn ghi. USAspending chép nguyên tên pháp nhân trên hợp
    đồng, mà cùng một tập đoàn ký bằng nhiều pháp nhân con.
    Bỏ đuôi (Corp · Inc · LLC · Company · Ltd) và mạo từ đầu thì hai bản viết về một mối. Đây là
    chuẩn hoá TỐI THIỂU, cố ý không đi xa hơn: gộp "Boeing" với "Boeing Defence" nghe hợp lý
    nhưng là suy đoán, và suy đoán trên số liệu công là chỗ không được phép đoán."""
    import re as _re
    t = " ".join(str(ten or "").split())
    t = _re.sub(r"^(the)\s+", "", t, flags=_re.I)
    t = _re.sub(r"[,\s]+(corp(oration)?|inc|llc|l\.?l\.?c|co|company|ltd|limited|plc|"
                r"holdings?|group|systems?)\.?$", "", t, flags=_re.I)
    t = _re.sub(r"[,\s]+(corp(oration)?|inc|llc|co|company|ltd)\.?$", "", t, flags=_re.I)
    return _gon(t.strip(" ,.-") or str(ten or ""), dai)


def _sk_hop_dong(D, ky):
    """Hợp đồng liên bang lớn nhất — GỘP THEO NHÀ THẦU, không liệt từng hợp đồng.

    29/8 — khung thật WEAPON PRICE: bảng sáu dòng mà "The Boeing Company" xuất hiện hai lần,
    "Lockheed Martin" hai lần, "Northrop Grumman" hai lần. Vì nguồn trả về TỪNG HỢP ĐỒNG, còn
    bảng thì đọc như một bảng xếp hạng NHÀ THẦU — người xem thấy một cái tên lặp ba dòng và kết
    luận bảng bị lỗi, chứ không nghĩ "à, đây là ba hợp đồng khác nhau".
    Và nó sai cả về nghĩa: hai dòng Boeing 22,4B và 10,5B khiến Boeing trông NHỎ HƠN thực tế so
    với một nhà thầu chỉ có một hợp đồng lớn. Gộp lại thì thứ hạng mới đúng là thứ hạng.
    """
    nam = int(ky.get("nam", 2024))
    hd = D.hop_dong_lon(nam, 30, ky.get("de_tai", ""))
    if len(hd) < 3:
        return None
    gop: dict = {}
    for x in hd:
        t = _ten_hang(x["ten"])
        gop[t] = gop.get(t, 0.0) + float(x["tien"] or 0)
    xep = sorted(gop.items(), key=lambda z: -z[1])[:6]
    if len(xep) < 3:
        return None
    muc = [{"name": t, "emoji": "🧾", "value": round(v / 1e6, 1), "disp": _tien(v)}
           for t, v in xep]
    return (f"{(ky.get('de_tai') or 'federal').title()} contracts, {nam}", "$M", muc,
            "Filed on USAspending dot gov.")


BO_SO = {"thanh_phan_mon": _sk_dinh_duong, "chuoi_bls": _sk_bls,
         "chi_so_the_gioi": _sk_the_gioi, "hop_dong_lon": _sk_hop_dong}


def dung_story_scaled(kenh: dict, ky: dict | None = None) -> dict | None:
    """Story dạng so kích thước. None = thiếu dữ liệu -> BỎ LƯỢT."""
    import du_lieu_mo as D
    bo = BO_SO.get(kenh.get("ham"))
    if not bo:
        print(f"   ⚠️ {kenh.get('ten')}: '{kenh.get('ham')}' chưa có bộ so kích thước — bỏ lượt")
        return None
    ts = dict(kenh.get("tham_so") or {})
    ts.update(ky or {})
    kq = bo(D, ts)
    if not kq:
        print(f"   ⚠️ {kenh.get('ten')}: thiếu dữ liệu — BỎ LƯỢT")
        return None
    tieu_de, don_vi, muc, ket = kq
    for m in muc:
        m["vo"] = f"{m['name']}. {m['disp']}."
    return _cong_an_toan({"title": tieu_de, "unit": don_vi, "items": muc,
                          "intro_vo": f"{tieu_de}. Same scale, no tricks.",
                          "outro_vo": ket, "nguon": kenh.get("nguon"),
                          "_that": True, "self_score": {"total": 92}}, kenh.get("ten", ""))


# ══════════════════════════════════════════════════════════════════════════════════════════
# BA DẠNG CÒN LẠI: bản đồ · bậc thang · xưa & nay
# ══════════════════════════════════════════════════════════════════════════════════════════
# Mã bang Mỹ -> tên đầy đủ, để engine bản đồ tô đúng vùng.
BANG = {"AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
        "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
        "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
        "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
        "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
        "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
        "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
        "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
        "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"}


def _bd_canh_bao(D, ky):
    """Cảnh báo thời tiết ĐANG BẬT, đếm theo bang — bản đồ nóng lên đúng chỗ đang có chuyện."""
    # 26/8 — CHUẨN HOÁ VỀ MÃ 2 CHỮ. API của NWS chỉ nhận mã (`TX`), còn kho xoay của kênh
    # `ALERT NOW` chứa TÊN ĐẦY ĐỦ (`Texas`, `Oklahoma`…) vì trục `bangs` dùng chung với các kênh
    # khác vốn cần tên để hiển thị. Không bang nào khớp ⇒ `data` dưới 3 mục ⇒ trả None ⇒ kênh ra
    # 0 video, mà log chỉ ghi "nguồn thiếu dữ liệu" nên nhìn như nguồn chết chứ không như lệch
    # khuôn dữ liệu. (Em đã báo nhầm đúng chuyện này: gọi thẳng `D.canh_bao("CA")` thì nguồn trả
    # 10 bản ghi bình thường — hỏng nằm ở đây, không nằm ở nguồn.)
    _ma = {v.lower(): k for k, v in BANG.items()}
    bangs = [str(b).strip() for b in (ky.get("bangs") or [])] or \
            ["TX", "CA", "FL", "NY", "OK", "KS", "LA", "AZ", "CO", "MO"]
    bangs = [b if len(b) == 2 else _ma.get(b.lower(), b) for b in bangs]
    import concurrent.futures as _cf
    with _cf.ThreadPoolExecutor(6) as ex:
        ket = list(ex.map(lambda b: (b, D.canh_bao(b, 50)), bangs))
    data = [{"name": BANG.get(b, b), "value": len(r)} for b, r in ket if r]
    if len(data) < 3:
        return None
    data = sorted(data, key=lambda z: -z["value"])
    loai = {}
    for _b, r in ket:
        for x in r:
            loai[x["loai"]] = loai.get(x["loai"], 0) + 1
    hay = sorted(loai.items(), key=lambda z: -z[1])[:1]
    dan = ["These warnings are live right now.",
           f"{data[0]['name']} has the most: {data[0]['value']} active.",
           (f"Most common: {hay[0][0].lower()}." if hay else "Mixed warning types."),
           f"{sum(d['value'] for d in data)} warnings across {len(data)} states.",
           "Issued by the National Weather Service, not a forecast app.",
           "If your state is on here, go check it."]
    return ("Active weather warnings", "alerts", data, dan)


def _bd_dong_dat(D, ky):
    """Động đất TRONG NƯỚC MỸ, gom theo bang — vì engine vẽ bản đồ các bang Mỹ."""
    r = D.dong_dat(float(ky.get("do_lon", 4.5)), ky.get("tu_ngay", "2015-01-01"), 200, trong_my=True)
    if len(r) < 4:
        return None
    gop, dem = {}, {}
    for x in r:
        # "112km SW of Anchor Point, Alaska" -> phần sau dấu phẩy cuối là bang
        bang = x["noi"].split(",")[-1].strip()
        if bang not in BANG.values():
            continue
        gop[bang] = max(gop.get(bang, 0), x["do_lon"])
        dem[bang] = dem.get(bang, 0) + 1
    if len(gop) < 3:
        return None
    data = [{"name": k, "value": round(v, 1), "disp": f"M{v:.1f}"}
            for k, v in sorted(gop.items(), key=lambda z: -z[1])[:10]]
    manh = r[0]
    tong = sum(dem.values())
    dan = [f"The ground moved {tong} times in the United States.",
           f"The strongest was magnitude {manh['do_lon']}.",
           f"It hit {manh['noi']}.",
           f"That one was {manh['sau_km']} kilometers down.",
           f"{data[0]['name']} tops the list, {dem.get(data[0]['name'], 0)} quakes on its own.",
           f"{len(gop)} states felt something since {ky.get('tu_ngay', '2015')[:4]}.",
           "Every one of these was recorded by a seismometer, not estimated.",
           "U S G S publishes the whole catalogue, free.",
           "If your state is on this map, it has happened before."]
    return ("Where America shakes", "magnitude", data, dan)


# Khung toạ độ từng vùng của Mỹ — để kênh SKY RIGHT NOW có thứ mà xoay.
# 27/8 — đo thật: kênh này ra 18 video mà chỉ MỘT tiêu đề, vì `_bd_may_bay` hỏi ĐÚNG MỘT khung
# toạ độ cứng (cả nước Mỹ) nên lượt nào cũng là cùng một câu hỏi. Dữ liệu có đổi theo giờ thật,
# nhưng "bao nhiêu máy bay đang trên nước Mỹ" thì lần nào cũng là một câu chuyện.
# Hỏi theo VÙNG thì mỗi lượt là một câu trả lời khác hẳn, và câu hỏi cũng cụ thể hơn hẳn với
# người xem: "ngay lúc này có bao nhiêu máy bay trên bầu trời Texas".
VUNG_MY = {
    "the whole country": (24, -125, 49, -66),
    "California":        (32.5, -124.5, 42, -114),
    "Texas":             (25.8, -106.7, 36.5, -93.5),
    "Florida":           (24.4, -87.7, 31.1, -79.9),
    "New York":          (40.4, -79.8, 45.1, -71.8),
    "the Midwest":       (36.9, -97.5, 49.4, -80.5),
    "the Pacific Northwest": (41.9, -124.8, 49.1, -116.9),
    "the Northeast":     (38.8, -80.6, 47.5, -66.9),
    "the Deep South":    (29.0, -94.1, 36.6, -81.0),
    "the Mountain West": (31.3, -117.2, 49.0, -102.0),
}


def _bd_may_bay(D, ky):
    """Máy bay đang bay, gom theo BANG — bản đồ nhiệt của bầu trời Mỹ ngay lúc này.

    28/8 — bản cũ gom theo NƯỚC ĐĂNG KÝ ("United States: 192", "Canada: 5") rồi đưa thẳng vào
    `MappedShort`, mà composition đó khớp `d.state` với TÊN BANG. Không tên nào khớp, nên 51 bang
    đều rỗng và bản đồ ra một mảng navy phẳng — dạng "bản đồ" mà không map được gì. Xem `bang_my.py`.

    Khung hỏi được NỚI RỘNG 5 độ quanh vùng đang xoay. Hỏi khít khung California thì chỉ California
    có số, bản đồ còn đúng một mảng sáng lẻ loi, không so được với gì. Nới ra thì các bang lân cận
    cũng có số: California vẫn đậm nhất, nhưng giờ người xem THẤY nó đậm hơn bao nhiêu — đó mới là
    thứ một bản đồ nhiệt phải nói."""
    from bang_my import VANH, bang_cua
    _v = str(ky.get("vung") or "the whole country")
    _b = VUNG_MY.get(_v) or VUNG_MY["the whole country"]
    if _v == "the whole country":
        _v = "America"                              # "over the whole country" đọc như văn nói vụng
    # Nới CHỈ khi vùng là một bang đơn lẻ. Vùng nhiều bang (the Midwest, the Northeast) vốn đã
    # có sẵn nền so sánh trong chính khung của nó; nới thêm thì kéo bang ngoài vùng vào bảng và
    # lời dẫn đi nói "North Carolina has the busiest sky" trong một video tên là "the Midwest" —
    # đúng loại lỗi mất mạch lạc mà con số sống vừa được sửa xong.
    _NOI = 5.0 if _v in VANH else 0.0
    r = D.may_bay(max(21.0, _b[0] - _NOI), max(-171.0, _b[1] - _NOI),
                  min(50.0, _b[2] + _NOI), min(-65.0, _b[3] + _NOI), 600)
    if len(r) < 10:
        return None
    gop = {}
    for x in r:
        b = bang_cua(x.get("kinh_do"), x.get("vi_do"))
        if b:                                       # None = đang trên biển, không thuộc bang nào
            gop[b] = gop.get(b, 0) + 1
    if len(gop) < 4:
        return None                                 # quá ít bang -> bản đồ không có gì để đọc
    data = [{"name": k, "value": v, "disp": f"{v} planes"}
            for k, v in sorted(gop.items(), key=lambda z: -z[1])[:12]]

    # Con số lên tiêu đề phải là con số của CHÍNH VÙNG ĐANG NÓI, không phải của cả khung đã nới.
    tam = gop.get(_v, 0) if _v in VANH else sum(gop.values())
    if tam < 5:
        tam, _v = sum(gop.values()), "America"      # vùng quá vắng -> lùi về cả nước, nói thật thế
    cao = r[0]
    dan = [f"Right now there are {tam} aircraft over {_v}.",
           f"{data[0]['name']} has the busiest sky: {data[0]['value']} planes overhead.",
           f"The highest is {cao['hieu'] or 'unmarked'}, at {cao['cao_m']:,.0f} meters.",
           f"{len(gop)} states have something in the air this second.",
           "Nobody is hiding this. The transponders broadcast it.",
           "OpenSky just writes it all down.",
           "Look up. One of these is above you."]
    # TIÊU ĐỀ MANG CON SỐ SỐNG. Kênh này là kênh DUY NHẤT có `xoay: None` (nguồn sống, không xoay
    # trục), nên nó cũng không được `_gan_truc_vao_tieu_de` gắn hậu tố phân biệt như 49 kênh kia —
    # luật 7.en bỏ sót đúng trường hợp này. Với nguồn sống thì thứ phân biệt là CON SỐ ĐO ĐƯỢC ngay
    # lúc đó; nó vừa làm tên khác nhau, vừa là một hook thật.
    return (f"{tam} planes are over {_v} right now", "planes overhead", data, dan)


def _bd_gia_nha(D, ky):
    """Giá nhà từng bang — bản đồ nóng đúng chỗ đắt.

    28/8 — TRỤC XOAY `bangs` TRƯỚC NAY LÀ MÃ CHẾT. Kênh WHERE TO MOVE khai `"xoay": "bangs"` với
    kho 6 nhóm bang, nhưng hàm này chưa từng đọc `ky`: nó luôn hỏi cả 51 bang và luôn trả về
    Hawaii đứng đầu. Sáu giá trị trục ⇒ đúng MỘT tiêu đề ("Hawaii: $833,877 — Home price by
    state") ⇒ chống trùng coi cả sáu là đã làm ⇒ kênh đăng một video rồi câm hẳn.

    Nay nhóm bang được chọn quyết định bảng: mỗi nhóm là một cuộc so khác, một bang dẫn đầu khác,
    một tiêu đề khác. Bản đồ tô đúng nhóm đó, các bang ngoài nhóm để màu "không có dữ liệu" — chú
    giải thang màu đã ghi rõ ô "none", nên người xem đọc ra "ngoài phạm vi câu hỏi" chứ không đọc
    nhầm thành "rẻ nhất"."""
    r = D.gia_nha_zillow("State")
    if len(r) < 10:
        return None
    moi = []
    for x in r:
        ks = sorted(x["gia"])
        if ks:
            moi.append({"name": x["ten"], "value": round(x["gia"][ks[-1]]),
                        "disp": f"${x['gia'][ks[-1]]:,.0f}"})
    chon = [str(b).strip().lower() for b in (ky.get("bangs") or []) if str(b).strip()]
    if chon:
        loc = [m for m in moi if str(m["name"]).strip().lower() in chon]
        # Dưới 4 bang khớp thì bản đồ không còn gì để so — lùi về cả nước thay vì ra một video
        # chỉ có hai ô sáng.
        moi = loc if len(loc) >= 4 else moi
    if len(moi) < 4:
        return None
    moi = sorted(moi, key=lambda z: -z["value"])
    re_ = moi[-1]
    dan = [f"A typical home in {moi[0]['name']} is now {moi[0]['disp']}.",
           f"In {re_['name']} it is {re_['disp']}.",
           f"That is {moi[0]['value'] / max(1, re_['value']):.1f} times the price for the same idea of a house.",
           f"{len(moi)} states, all measured the same way.",
           "This is the Zillow index, updated every month.",
           "Your move might be worth more than your raise."]
    return ("Home price by state", "$", moi, dan)


BO_BAN_DO = {"canh_bao": _bd_canh_bao, "dong_dat": _bd_dong_dat, "may_bay": _bd_may_bay,
             "gia_nha_zillow": _bd_gia_nha}


def dung_story_mapped(kenh: dict, ky: dict | None = None) -> dict | None:
    import du_lieu_mo as D
    bo = BO_BAN_DO.get(kenh.get("ham"))
    if not bo:
        print(f"   ⚠️ {kenh.get('ten')}: '{kenh.get('ham')}' chưa có bộ bản đồ — bỏ lượt")
        return None
    ts = dict(kenh.get("tham_so") or {})
    ts.update(ky or {})
    kq = bo(D, ts)
    if not kq:
        print(f"   ⚠️ {kenh.get('ten')}: thiếu dữ liệu — BỎ LƯỢT")
        return None
    tieu_de, don_vi, data, dan = kq
    # MappedShort đọc khoá `state`, không phải `name` — và cần riêng 3 mục đầu để "bung" lần lượt.
    data = [{"state": d.get("state") or d.get("name"), "value": d["value"],
             "disp": d.get("disp") or _so(d["value"])} for d in data]
    top = [{"state": d["state"], "disp": d["disp"],
            "vo": f"{d['state']}. {d['disp']}."} for d in data[:3]]
    # build_mapped_props chỉ đọc intro/bloom/outro + 3 mục top — viết 9 câu mà nó dùng 3 thì video
    # ra 16 giây, dưới mốc 20 giây của QC. Gộp phần còn lại vào ba chặng đó.
    _c = [c for c in (dan or []) if c]
    mo = " ".join(_c[:3]) if _c else tieu_de
    giua = " ".join(_c[3:5]) if len(_c) > 3 else "Watch the map light up."
    ket = " ".join(_c[5:]) if len(_c) > 5 else (_c[-1] if _c else "")
    return _cong_an_toan({"title": tieu_de, "unit": don_vi, "data": data, "top": top,
                          "intro_vo": mo, "bloom_vo": giua, "outro_vo": ket,
                          "narration": _c,
                          "nguon": kenh.get("nguon"), "_that": True,
                          "self_score": {"total": 92}}, kenh.get("ten", ""))


def _bt_luot_doc(D, ky):
    """Bậc thang: một cái tên leo lên rồi rơi xuống, đo bằng lượt đọc từng ngày."""
    import datetime as _dt
    # 27/8 — cùng lệch ngữ nghĩa với `_bd_wiki_top`: kênh FAME CURVE xoay trục `thang` với kho
    # [1..12], nhưng ở đây `thang` ghép vào một NGÀY CỤ THỂ (`nam`/`thang`/`ngay`). Tháng nào
    # nằm ở tương lai so với hôm nay thì Wikipedia chưa có bảng -> hỏng. Đo được: 2/12 chạy.
    # Trục đúng là SỐ NGÀY LÙI: luôn trỏ tới một ngày có thật, và tự trôi theo thời gian.
    if ky.get("lui") is not None:
        goc = _dt.date.today() - _dt.timedelta(days=int(ky["lui"]))
    else:
        goc = _dt.date(int(ky.get("nam", 2026)), int(ky.get("thang", 8)), int(ky.get("ngay", 20)))
    top = D.bai_duoc_doc(goc.year, goc.month, goc.day, 12)
    if not top:
        return None
    v = top[0]
    tu = (goc - _dt.timedelta(days=29)).strftime("%Y%m%d")
    diem = D.luot_doc_bai(v["ten"], tu, goc.strftime("%Y%m%d"))
    if len(diem) < 8:
        return None
    diem = sorted(diem, key=lambda z: z["luot_doc"])
    buoc = [diem[0]] + diem[len(diem) // 4::max(1, len(diem) // 5)][:5]
    import math
    # 28/8 — BA THỨ SAI CÙNG LÚC Ở ĐÂY, thấy trên khung hình thật kênh FAME CURVE:
    #   • lời đọc ra "07 slash 03" — không người Mỹ nào đọc ngày kiểu đó;
    #   • nhãn "07/23" trên màn hình cũng vậy;
    #   • và nặng nhất: thang bên cạnh ghi "1 in 10,000" trong khi con số là LƯỢT ĐỌC.
    #     Khuôn `longshot` vốn là thang XÁC SUẤT ("1 phần triệu"); đổ dữ liệu ĐẾM vào đó thì mọi
    #     nhãn thang đều vô nghĩa — người xem đọc "63.4K" cạnh "1 in 10,000" và không hiểu gì.
    # Nên nguồn phải KHAI RÕ nó đếm cái gì; phần vẽ đọc khai báo đó mà đặt nhãn thang cho đúng.
    _TH = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    def _ngay_dep(ng):
        try:
            return f"{_TH[int(ng[4:6])]} {int(ng[6:8])}"
        except Exception:
            return str(ng)
    muc = [{"label": _ngay_dep(x["ngay"]), "emoji": "📈",
            "oddsDisp": _so(x["luot_doc"]),
            "logValue": round(math.log10(max(10, x["luot_doc"])), 3),
            "vo": f"{_ngay_dep(x['ngay'])}. {x['luot_doc']:,} reads."}
           for x in buoc[:6]]
    if len(muc) < 4:
        return None
    dan = [f"{v['ten']}, one month of attention.", "From nobody looking, to everybody looking."]
    # `rung_kieu` đi kèm story -> props -> composition: thang ghi "10K reads" thay vì "1 in 10,000".
    return (f"{_gon(v['ten'], 34)}: the spike", muc, dan, {"rung_kieu": "dem", "rung_don_vi": "reads"})


def _bt_bls(D, ky):
    """Bậc thang: một chỉ số leo qua từng năm."""
    import math
    ten = ky.get("chuoi", "that_nghiep")
    diem = D.lay_bls([ten], int(ky.get("tu_nam", 2015)), int(ky.get("den_nam", 2024))).get(ten) or []
    if len(diem) < 24:
        return None
    theo_nam = {}
    for x in diem:
        theo_nam.setdefault(x["nam"], []).append(x["gia_tri"])
    nams = sorted(theo_nam)[-6:]
    # 27/8 — DẠNG LONGSHOT LÀ THANG LOG CỦA TỈ LỆ CƯỢC ("1 trên N"), có bậc EVERYDAY / 1 trên 10 /
    # 1 trên 100… Nhét thẳng phần trăm vào đó là sai đơn vị: xem khung thật kênh JOB DYING thì
    # 5,4 · 3,7 · 8,1 · 3,6 đều rơi vào log10 ≈ 0,56-0,91, tức CÙNG MỘT BẬC — sáu con số chen nhau
    # quanh một vòng tròn nhỏ, không đọc ra thứ tự lẫn ý nghĩa.
    # Phần trăm CHUYỂN ĐƯỢC sang đúng ngôn ngữ của dạng này: 5,4% nghĩa là 1 trong 18 người. Vừa
    # đúng đơn vị mà bậc thang đang đo, vừa là cách nói mạnh hơn hẳn với người xem — "1 trong 12
    # người Mỹ đi làm" đọng lại lâu hơn "8,1 phần trăm".
    la_pt = "%" in str(ky.get("don_vi", "")) or ten in ("that_nghiep",) or bool(ky.get("phan_tram"))
    muc = []
    for n in nams:
        v = sum(theo_nam[n]) / len(theo_nam[n])
        if la_pt and v > 0:
            cu = max(1.0, 100.0 / v)                    # 5,4% -> 1 trên 18,5
            muc.append({"label": str(n), "emoji": "📉", "oddsDisp": f"1 in {cu:,.0f}",
                        "logValue": round(math.log10(cu), 3),
                        "vo": f"{n}. One in {cu:,.0f}."})
        else:
            muc.append({"label": str(n), "emoji": "📉", "oddsDisp": f"{v:,.1f}",
                        "logValue": round(math.log10(max(1.0, v)), 3),
                        "vo": f"{n}. {v:,.1f}."})
    if len(muc) < 4:
        return None
    nhan = ky.get("nhan") or "Index"
    return (f"{nhan} by year", muc,
            [f"{nhan}, six years in a row." if not la_pt
             else f"{nhan}: how many people it actually was, year by year.",
             "Bureau of Labor Statistics. Not a forecast."])


def _bt_nhac(D, ky):
    """Bậc thang: nghệ sĩ và độ dài sự nghiệp trên giấy tờ."""
    import math, datetime as _dt
    r = [x for x in D.ho_so_nhac(ky.get("tu_khoa", "one hit wonder"), 20) if x.get("bat_dau")]
    if len(r) < 4:
        return None
    nay = _dt.date.today().year
    muc = []
    for x in r:
        try:
            d0 = int(str(x["bat_dau"])[:4])
        except Exception:
            continue
        d1 = int(str(x.get("ket_thuc") or nay)[:4]) if str(x.get("ket_thuc") or "")[:4].isdigit() else nay
        nam = max(1, d1 - d0)
        muc.append({"label": _gon(x["ten"], 18), "emoji": "🎵", "oddsDisp": f"{nam}y",
                    "logValue": round(math.log10(max(1, nam)), 3),
                    "vo": f"{_gon(x['ten'], 26)}. {nam} years on the record."})
        if len(muc) >= 6:
            break
    if len(muc) < 4:
        return None
    return ("How long they lasted", muc,
            ["Careers, measured in years on paper.", "MusicBrainz keeps the dates."])


BO_THANG = {"luot_doc_bai": _bt_luot_doc, "chuoi_bls": _bt_bls, "ho_so_nhac": _bt_nhac}


def dung_story_longshot(kenh: dict, ky: dict | None = None) -> dict | None:
    import du_lieu_mo as D
    bo = BO_THANG.get(kenh.get("ham"))
    if not bo:
        print(f"   ⚠️ {kenh.get('ten')}: '{kenh.get('ham')}' chưa có bộ bậc thang — bỏ lượt")
        return None
    ts = dict(kenh.get("tham_so") or {})
    ts.update(ky or {})
    kq = bo(D, ts)
    if not kq:
        return None
    # 28/8 — bộ dựng CÓ THỂ trả thêm gói cấu hình thang (4 phần tử). Nhận cả hai dạng để không
    # phải sửa 6 bộ dựng còn lại — cái nào chưa cần thì vẫn trả 3 phần tử như cũ.
    tieu_de, muc, dan = kq[0], kq[1], kq[2]
    _them = kq[3] if len(kq) > 3 and isinstance(kq[3], dict) else {}
    return _cong_an_toan({"title": tieu_de, "items": muc, **_them,
                          "intro_vo": dan[0], "outro_vo": dan[-1] if len(dan) > 1 else "",
                          "nguon": kenh.get("nguon"), "_that": True,
                          "self_score": {"total": 92}}, kenh.get("ten", ""))


def _xn_bls(D, ky):
    """Xưa & nay: cùng một chỉ số, cách nhau nhiều năm."""
    nhom = ky.get("nhom") or [ky.get("chuoi", "cpi_nha")]
    NHAN = {"cpi_nha": "Housing", "cpi_thucpham": "Food", "cpi_xang": "Gas", "cpi_yte": "Health care",
            "cpi_giao_duc": "Education", "luong_gio": "Hourly pay", "cpi_di_lai": "Transport"}
    tu, den = int(ky.get("tu_nam", 2005)), int(ky.get("den_nam", 2024))
    bo = D.lay_bls(nhom, tu, den)
    cap = []
    for t, diem in bo.items():
        if len(diem) < 12:
            continue
        d0 = [x for x in diem if x["nam"] == diem[0]["nam"]]
        d1 = [x for x in diem if x["nam"] == diem[-1]["nam"]]
        if not d0 or not d1:
            continue
        v0 = sum(x["gia_tri"] for x in d0) / len(d0)
        v1 = sum(x["gia_tri"] for x in d1) / len(d1)
        cap.append({"label": NHAN.get(t, t), "thenYear": str(diem[0]["nam"]),
                    "thenVal": f"{v0:,.0f}", "nowYear": str(diem[-1]["nam"]),
                    "nowVal": f"{v1:,.0f}", "change": f"+{(v1 - v0) / v0 * 100:.0f}%",
                    "vo": f"{NHAN.get(t, t)}. From {v0:,.0f} to {v1:,.0f}."})
    if len(cap) < 3:
        return None
    return (ky.get("nhan") or "Then and now", cap,
            ["Same measure, twenty years apart.", "Bureau of Labor Statistics. Look it up."])


def _xn_gia_nha(D, ky):
    """Giá nhà một bang: đầu những năm 2000 so với bây giờ."""
    r = D.gia_nha_zillow("State")
    if len(r) < 6:
        return None
    chon = ky.get("bangs") or ["California", "Texas", "Florida", "New York", "Ohio", "Idaho"]
    cap = []
    for x in r:
        if x["ten"] not in chon:
            continue
        ks = sorted(x["gia"])
        if len(ks) < 60:
            continue
        v0, v1 = x["gia"][ks[0]], x["gia"][ks[-1]]
        cap.append({"label": x["ten"], "thenYear": ks[0][:4], "thenVal": f"${v0:,.0f}",
                    "nowYear": ks[-1][:4], "nowVal": f"${v1:,.0f}",
                    "change": f"+{(v1 - v0) / v0 * 100:.0f}%",
                    "vo": f"{x['ten']}. From {v0:,.0f} to {v1:,.0f} dollars."})
    if len(cap) < 3:
        return None
    return ("Same house, different decade", cap,
            ["What a home cost then, and what it costs now.",
             "Zillow index, same measure both years."])


def _xn_tu_lieu(D, ky):
    """Xưa & nay bằng phim tư liệu: cùng chủ đề, hai mốc thời gian trong kho lưu trữ."""
    r = D.phim_tu_lieu(ky.get("tu_khoa", "city street"), 30)
    co_nam = [x for x in r if str(x.get("nam") or "")[:4].isdigit()]
    if len(co_nam) < 6:
        return None
    co_nam.sort(key=lambda z: int(str(z["nam"])[:4]))
    n = len(co_nam) // 2
    cu, moi = co_nam[:n], co_nam[n:]
    cap = []
    for a, b in zip(cu[:4], moi[:4]):
        cap.append({"label": _gon(a["tieu_de"], 18), "thenYear": str(a["nam"])[:4],
                    "thenVal": _gon(a["tieu_de"], 16), "nowYear": str(b["nam"])[:4],
                    "nowVal": _gon(b["tieu_de"], 16), "change": "",
                    "vo": f"{str(a['nam'])[:4]}, then {str(b['nam'])[:4]}."})
    if len(cap) < 3:
        return None
    return ("The same subject, decades apart", cap,
            ["Two eras of the same thing, both on film.",
             "Public domain. Nobody owns either one."])


BO_XUA_NAY = {"chuoi_bls": _xn_bls, "gia_nha_zillow": _xn_gia_nha, "phim_tu_lieu": _xn_tu_lieu}


def dung_story_thennow(kenh: dict, ky: dict | None = None) -> dict | None:
    import du_lieu_mo as D
    bo = BO_XUA_NAY.get(kenh.get("ham"))
    if not bo:
        print(f"   ⚠️ {kenh.get('ten')}: '{kenh.get('ham')}' chưa có bộ xưa&nay — bỏ lượt")
        return None
    ts = dict(kenh.get("tham_so") or {})
    ts.update(ky or {})
    kq = bo(D, ts)
    if not kq:
        return None
    tieu_de, cap, dan = kq
    return _cong_an_toan({"title": tieu_de, "pairs": cap, "intro_vo": dan[0], "outro_vo": dan[-1],
                          "nguon": kenh.get("nguon"), "_that": True,
                          "self_score": {"total": 92}}, kenh.get("ten", ""))


def chay(kenh: dict, ra: str = "", ky: dict | None = None) -> tuple[str, dict] | None:
    """Dựng story -> thu giọng -> render. Trả (đường dẫn, thông tin QC). None = bỏ lượt."""
    import datastory_ci as DS
    st = dung_story_ranked(kenh, ky)
    if not st:
        return None
    sl = DS.slug(kenh["handle"].lstrip("@"))
    sdir = os.path.join(DS.PUB, "narration", "_th2_" + sl)
    os.makedirs(sdir, exist_ok=True)
    props = DS.build_ranked_props(st, sdir, handle=kenh["handle"])
    pf = os.path.join(DS.PUB, f"_th2_{sl}.json")
    json.dump(props, io.open(pf, "w", encoding="utf-8"), ensure_ascii=False)
    ra = os.path.abspath(ra or os.path.join(GOC, "out", f"th2_{sl}.mp4"))
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    DS.run_render_cmd(["npx", "remotion", "render", "src/index.ts", "RankedShort", ra,
                       f"--props=./{os.path.relpath(pf, DS.ENG)}", "--gl=swiftshader", "--jpeg-quality=100", "--crf=15",
                       "--concurrency=2", "--log=error"],
                      cwd=DS.ENG, timeout=2400, label=f"RankedShort({kenh['ten']})")
    ok, info = DS.qc(ra)
    print(f"{'✅' if ok else '❌'} {kenh['ten']} · {info}")
    if ok:
        lam_thumb(kenh, st, ra)
    return (ra, info) if ok else None


def dung_props_race(kenh: dict, ky: dict | None = None, st_san: dict | None = None,
                    ky_hieu: str = ""):
    """Đua cột: dựng frames -> thu giọng từng câu -> ghép track + băng chữ -> render RaceShort."""
    import datastory_ci as DS
    st = st_san or dung_story_race(kenh, ky)
    if not st:
        return None
    sl = DS.slug(kenh["handle"].lstrip("@")) + (f"_{ky_hieu}" if ky_hieu else "")
    sdir = os.path.join(DS.PUB, "narration", "_th2r_" + sl)
    os.makedirs(sdir, exist_ok=True)
    doan, subs, cum = [], [], 0.0
    for i, cau in enumerate(st["narration"]):
        m = os.path.join(sdir, f"n{i}.mp3")
        _, sb, _ = DS.TK.synth(cau, m)
        for w in sb:
            w["t"] = round(w["t"] + cum, 3)
        subs += sb
        cum += DS._dur(m) or 0
        doan.append(m)
    track = os.path.join(sdir, "track.mp3")
    DS._concat(doan, track)
    n = len(st["frames"])
    # Nhịp cột bám ĐỘ DÀI GIỌNG THẬT: đặt cứng thì hoặc cột chạy xong còn giọng, hoặc ngược lại.
    spf = max(1.2, min(6.0, (cum * 0.92) / max(1, n - 1)))
    b = (kenh.get("brand") or {}).get("palette") or {}
    props = {"frames": st["frames"], "secondsPerFrame": round(spf, 3),
             "durationSec": round(cum + 1.4, 2), "topN": 7,
             "title": st["title"][:40], "unit": st["unit"][:6],
             "handle": kenh["handle"], "source": ten_nguon(st.get("nguon", "")),
             "audio": os.path.relpath(track, DS.PUB), "subs": subs,
             "accent": b.get("primary", "#F5B301"),
             # 27/8 — nhạc nền RIÊNG của kênh. Trước đây viết cứng `carefree.mp3` nên 50 kênh
             # dùng chung đúng một bản, dù kho có 14 bản dùng được. Đó là dấu vân tay "cùng một
             # chủ" phiên bản âm thanh — khó thấy hơn dấu trên hình vì người ta không "nhìn"
             # nhạc, nhưng nghe hai kênh mà cùng một vòng nhạc thì nhận ra ngay.
             "music": (kenh.get("brand") or {}).get("nhac") or "music/carefree.mp3", "sfx": True,
             # 26/8 — phông riêng của kênh. Thiếu khoá này thì RaceShort rơi về Poppins và 7 kênh
             # dạng đua lại chung một khuôn chữ, dù JSON đã gán phông khác nhau cho từng kênh.
             "font": (kenh.get("brand") or {}).get("font", ""),
             **({"hookStat": _so_noi_bat(st)["stat"],
                 "hookLabel": _so_noi_bat(st).get("name", ""),
                 "hookLine": _cau_hoi_mo(kenh, st)} if _so_noi_bat(st).get("stat") else {})}
    return props, st, sl


def chay_race(kenh: dict, ra: str = "", ky: dict | None = None,
              st_san: dict | None = None, ky_hieu: str = "",
              keys: list | None = None) -> tuple[str, dict] | None:
    """Đua cột: dựng props -> render RaceShort (9:16). Long 16:9 đi qua `Gen2Long`."""
    import datastory_ci as DS
    _dp = dung_props_race(kenh, ky, st_san, ky_hieu)
    if not _dp:
        return None
    props, st, sl = _dp
    _ly_do = DS.xac_minh_mo_dau(props, "RaceShort")
    if _ly_do:
        print(f"   ⚠️ {kenh.get('ten')}: mở đầu {_ly_do} — BỎ LƯỢT TRƯỚC render")
        return None
    pf = os.path.join(DS.PUB, f"_th2r_{sl}.json")
    json.dump(props, io.open(pf, "w", encoding="utf-8"), ensure_ascii=False)
    ra = os.path.abspath(ra or os.path.join(GOC, "out", f"th2r_{sl}.mp4"))
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    DS.run_render_cmd(["npx", "remotion", "render", "src/index.ts", "RaceShort", ra,
                       f"--props=./{os.path.relpath(pf, DS.ENG)}", "--gl=swiftshader", "--jpeg-quality=100", "--crf=15",
                       "--concurrency=2", "--log=error"],
                      cwd=DS.ENG, timeout=2400, label=f"RaceShort({kenh['ten']})")
    ok, info = DS.qc(ra)
    print(f"{'✅' if ok else '❌'} {kenh['ten']} · {info}")
    if ok:
        chuan_am(ra)          # đưa về -14 LUFS trước mọi khâu sau (xem `chuan_am`)
        _hok, _htin = qc_hook_sau_render(ra, kenh.get("ten", ""), keys)
        if isinstance(info, dict):
            info.update(_htin)
        if not _hok:
            return None
        lam_thumb(kenh, st, ra)
    if isinstance(info, dict):
        info["_props_obj"] = props
    return (ra, info) if ok else None


# Mỗi dạng: (composition Remotion, hàm dựng props trong datastory_ci)
DUONG_RA = {
    "ranked":    ("RankedShort", "build_ranked_props"),
    "race":      ("RaceShort", None),               # có đường riêng: chay_race
    "scaled":    ("ScaledShort", "build_scaled_props"),
    "mapped":    ("MappedShort", "build_mapped_props"),
    "longshot":  ("LongshotShort", "build_longshot_props"),
    "thennow":   ("ThenNowShort", "build_thennow_props"),
    "cinematic": ("CinematicShort", None),          # có đường riêng: build_doc_props (cần ảnh AI)
}

# ── BỐ CỤC RIÊNG THEO KÊNH (29/8/2026) ─────────────────────────────────────────────────────
# Anh soi ba kênh `ranked` cạnh nhau: "vẫn còn rẻ tiền, channel nào cũng làm được". Đúng — 18/50
# kênh dùng chung bảng tier S/A/B/C thẻ màu. `bien_cua` có 27 biến thể nhưng chúng chỉ đổi vị trí
# nhãn, kiểu viền, hoạ tiết nền; bộ khung thì một, nên ba kênh đọc ra là một kênh đổi filter.
# Vừa là chuyện thẩm mỹ, vừa là rủi ro lớn nhất còn lại với chính sách "nội dung sản xuất hàng
# loạt" của YouTube — thứ quyết định bật được kiếm tiền hay không.
#
# Cách chữa không phải thêm biến thể màu mà là VIẾT THÊM BỐ CỤC THẬT. Ba bố cục cho 18 kênh, chia
# đều 6/6/6, gán CỐ ĐỊNH theo tên kênh: một kênh phải giữ một bộ mặt, đổi bố cục giữa các video là
# tự phá nhận diện của chính nó.
#
#   RankedShort      bảng tier S/A/B/C — hợp kênh có thứ hạng rõ ràng, nhiều mục
#   RankedEditorial  một mục một màn hình, số thứ hạng khổng lồ — hợp kênh ít mục, cần sức nặng
#   VectorChart      cột ngang nền giấy, đồ hoạ báo dữ liệu — hợp kênh tiền/giá/số liệu khô
BO_CUC_KENH = {
    # Bảng tier: kênh có nhiều mục và thứ hạng là chuyện chính.
    "STEAMTRUTH": "RankedShort", "GAMEGRAVEYARD": "RankedShort", "BREEDFILE": "RankedShort",
    "SHOWNUMBERS": "RankedShort", "GONETOOSOON": "RankedShort", "WHATTHEYSEARCH": "RankedShort",
    # Biên tập: ít mục, mỗi mục đáng một màn hình riêng.
    "PILLFACTS": "RankedEditorial", "RECALLPLATE": "RankedEditorial",
    "CARRECALL": "RankedEditorial", "SUEDFORTHIS": "RankedEditorial",
    "NEAREARTH": "RankedEditorial", "PAIDVSPLAYED": "RankedEditorial",
    # Đồ hoạ vector nền giấy: kênh tiền, lương, giá, hồ sơ doanh nghiệp — số liệu khô cần đọc rõ.
    "SALARYTRUTH": "VectorChart", "DEGREEWORTH": "VectorChart", "COSTTOGO": "VectorChart",
    "FILINGSSAY": "VectorChart", "QUIETLAYOFFS": "VectorChart", "WHATISINIT": "VectorChart",
    # 29/8 — SÁU KÊNH `scaled` CHUYỂN HẲN SANG VECTOR, BỎ ẢNH AI.
    # Chúng vốn vẽ một ảnh AI cho MỖI mục (`_ve_vat`) để làm chóp trên đầu cột. Ba lý do bỏ:
    #   • chữ bịa — ảnh nào có mặt phẳng là có chữ giả, và đó là nội dung sai sự thật;
    #   • hạn mức — mỗi video tốn 6 lượt vẽ, mà hôm nay 169 key Gemini đã cạn sạch;
    #   • chúng CÓ SỐ LIỆU THẬT, nên cột tỉ lệ nói được nhiều hơn hẳn một cái ảnh minh hoạ.
    # Ảnh AI giữ lại cho dạng phim kể, nơi cần không khí chứ không cần đo đạc.
    "CALORIESHOCK": "VectorChart", "HOUSEMATH": "VectorChart", "PAYCHECKGAP": "VectorChart",
    "WEAPONPRICE": "VectorChart", "WILDNUMBERS": "VectorChart", "MARRIAGEMATH": "VectorChart",
}


def bo_cuc_cua(kenh: dict, dang: str) -> str:
    """Composition thật sự dùng cho kênh này. Không khai riêng thì dùng mặc định của dạng."""
    if dang not in ("ranked", "scaled"):
        return (DUONG_RA.get(dang) or ("", ""))[0]
    mac = "RankedShort" if dang == "ranked" else "ScaledShort"
    return BO_CUC_KENH.get(str(kenh.get("ten") or "").replace(" ", "").upper(), mac)


DUNG_STORY = {}      # nạp ở cuối file, sau khi mọi hàm đã định nghĩa


# ── GU VẼ: TIẾNG VIỆT TRONG CẤU HÌNH, TIẾNG ANH KHI GỬI ĐI VẼ (29/8/2026) ──────────────────
# Anh: "sao lại render ảnh kiểu người thật này, ko hợp — a muốn ảnh mà AI vẽ tốt: vũ trụ, khoa
# học, viễn tưởng…". Đúng cả về thẩm mỹ lẫn kỹ thuật, và gốc của nó là một lỗi cụ thể:
#
#   `_cf_flux_image` ghép prompt là  f"A {style} of: {prompt}"
#   mà `style` lấy thẳng từ `kenh["style_anh"]` — VIẾT BẰNG TIẾNG VIỆT.
#
# Nên prompt thật gửi lên FLUX là "A phác thảo phòng xử, than chì of: a stack of court files".
# Máy vẽ không đọc được phần tiếng Việt, bỏ qua nó, và rơi về mặc định của nó: ẢNH CHỤP NGƯỜI
# THẬT. Suốt thời gian qua mười kênh đều khai gu riêng (than chì · khắc gỗ · vector · sơn dầu) và
# KHÔNG kênh nào nhận được gu của mình — lại đúng họ lỗi "khai ra rồi không ai đọc" của
# `voice_tone`, `brand.font`, `palette.bg`, `tham_so.xoay`.
#
# Và ảnh người thật là thứ máy vẽ dở nhất: tay thừa ngón, mặt méo, chữ sai chính tả ("PUBLIC
# RECCORDS"). Còn nét vẽ, khắc gỗ, vector, vũ trụ, ảnh vĩ mô thì nó làm rất tốt — vì ở đó không có
# một "bản gốc đúng" nào để mắt người đem ra so.
GU_VE_EN = {
    "minh hoạ giải phẫu nét mảnh":
        "clean line-art anatomical illustration, thin ink strokes on warm paper, "
        "medical textbook plate, muted ochre accents",
    "phác thảo phòng xử, than chì":
        "graphite courtroom reportage sketch, loose charcoal linework on toned paper, "
        "smudged shading, no colour except a single warm accent",
    "ảnh tài liệu ố yellow": "",
    "ảnh tài liệu ố vàng":
        "macro photograph of an aged archival document, yellowed paper fibres, "
        "typewriter era, raking light, shallow depth of field, objects only",
    "tranh khắc gỗ đen trắng":
        "black and white woodcut engraving, bold carved lines, cross-hatching, "
        "vintage broadsheet illustration",
    "ảnh sương mù đơn sắc":
        "monochrome fog landscape, heavy atmosphere, long lens, desaturated, "
        "empty scene, architectural silhouettes",
    "bìa đĩa vector":
        "flat vector album-cover artwork, bold geometric shapes, limited palette, "
        "screenprint texture, mid-century poster feel",
    "ảnh đêm tương phản mạnh":
        "high contrast night scene, deep shadows with hard rim light, wet asphalt, "
        "empty architecture, cinematic anamorphic flare",
    "tranh sơn dầu tối màu":
        "dark oil painting, thick impasto brushwork, chiaroscuro lighting, "
        "moody interior, old-master palette",
    "khung phim xước":
        "scratched 16mm film frame, heavy grain, halation and dust, "
        "faded archival footage still, warm bleach-bypass grade",
    "tranh minh hoạ phiên toà":
        "editorial ink illustration, fine cross-hatching, civic architecture, "
        "restrained two-colour palette, broadsheet op-ed style",
    "ảnh món ăn chụp trên cao":
        "overhead food photograph, single dish centred on a plain surface, "
        "soft diffused light, styled flat lay",
    # 18 gu còn lại. Dịch HẾT, không để kênh nào rơi về mặc định của máy vẽ — mặc định đó là
    # ảnh chụp người thật, đúng thứ anh bác.
    "ảnh sản phẩm sạch, nền giấy gói":
        "clean product still life on kraft paper, single object, soft box lighting, "
        "packaging-design look",
    "chân dung vận động viên phẳng":
        "flat vector sports portrait, bold shapes and hard edges, two-tone palette, "
        "silkscreen poster",
    "chân dung nét đơn sắc":
        "monochrome line portrait, single continuous ink stroke, minimal, high contrast",
    "poster giả lập phong cách in lụa":
        "silkscreen propaganda-style poster, three flat inks, halftone dots, bold composition",
    "ảnh màn hình tối, chữ neon":
        "dark terminal screen glow, neon monospaced glyph shapes, scanlines, close macro, "
        "abstract interface",
    "ảnh sân khấu hạt phim":
        "empty stage under a single spotlight, heavy film grain, deep blacks, "
        "smoke in the beam, no performers",
    "pixel art u tối":
        "dark pixel art scene, limited 16-colour palette, chunky pixels, dithering, "
        "retro game still",
    "xe cắt lớp isometric":
        "isometric technical cutaway of a vehicle, exploded mechanical parts, "
        "blueprint-style line rendering",
    "tranh màu nước":
        "loose watercolour painting, wet-on-wet bleeds, soft edges, generous white paper",
    "tranh khắc tự nhiên học":
        "vintage natural-history engraving, fine stipple and hatching, "
        "scientific plate on cream paper",
    "bưu thiếp cũ":
        "faded vintage postcard, muted printed colours, halftone texture, deckled border",
    "bản đồ radar phát sáng":
        "glowing radar sweep display, phosphor green traces on dark grid, "
        "atmospheric scanlines, abstract data map",
    "biểu tượng phẳng ấm màu":
        "flat icon-style illustration, warm limited palette, rounded geometry, "
        "generous negative space",
    "ảnh màn hình đêm":
        "night-time screen glow in a dark room, cool blue light on surfaces, "
        "objects only, shallow focus",
    "mặt cắt nhà isometric":
        "isometric architectural cutaway of a house, clean line rendering, "
        "muted pastel fills, doll-house view",
    "ảnh ghép hai thời":
        "split-frame diptych of the same place in two eras, left aged and sepia, "
        "right clean and modern, architectural subject",
    "kỹ thuật hoạ bản vẽ xanh":
        "technical blueprint drawing, white lines on deep cyan, dimension lines and callouts, "
        "drafting-table look",
}

# Dán vào MỌI prompt vẽ. Hai câu, hai lý do khác nhau:
#   • cấm mặt/tay người thật — đó là chỗ máy vẽ hỏng rõ nhất và mắt người bắt được ngay;
#   • đẩy về phía tranh/đồ hoạ — đúng hướng anh chọn, và cũng là phía máy vẽ mạnh.
# 29/8 — CẤM SUÔNG KHÔNG ĂN, PHẢI CHO NÓ VẼ THỨ KHÁC.
# Sau hai vòng siết lệnh cấm ("no text" ở đuôi, rồi ở đầu prompt), khung vẫn ra "Publlic Records"
# (ba chữ L) và một tờ lịch đề "Fetemisary". Mô hình khuếch tán xử lý phủ định rất kém: bảo nó
# "đừng vẽ chữ" thì từ "chữ" vẫn kích hoạt đúng vùng đặc trưng đó.
# Cách ăn hơn hẳn là RA LỆNH KHẲNG ĐỊNH — mô tả mặt phẳng TRỐNG như một chi tiết muốn có. Nó
# không phải kìm mình lại nữa, nó có sẵn thứ để vẽ vào chỗ đó.
# Và chữ bịa đắt nhất đúng ở kênh hồ sơ/lưu trữ, nơi cả uy tín nằm ở chỗ "giấy tờ có thật".
# 29/8 — VÒNG BA CỦA BÀI TOÁN CHỮ BỊA, và lần này mới đúng gốc.
# Vòng 1 cấm ở đuôi prompt, vòng 2 cấm ở đầu prompt, vòng 3 bảo "mọi mặt giấy đều trống". Cả ba
# đều hụt, và khung mới nhất còn tệ hơn: "COURTE OPITION", "NEW YORKE", cả trang toàn chữ vô nghĩa.
#
# Lý do vòng 3 hụt: chủ thể của kênh CHÍNH LÀ tài liệu ("stack of legal case files", "hands opening
# a public records"). Bảo máy vẽ một tờ giấy mà "hoàn toàn trống" là hai mệnh lệnh chỏi nhau, và
# nó chọn cái cụ thể hơn — vẽ giấy có chữ.
#
# Cách ra khỏi bế tắc: đừng bảo nó BỎ chữ, hãy bảo nó vẽ chữ THÀNH THỨ KHÁC. "Nét nguệch ngoạc
# trừu tượng" là một thứ hình cụ thể, máy vẽ được, và trong một bức ký hoạ thì nó ĐÚNG — hoạ sĩ
# ký hoạ phiên toà cũng vẽ chữ thành nét lượn chứ không chép từng chữ.
# Người xem đọc ra "đây là một trang tài liệu" mà không đọc ra một lỗi chính tả nào.
GU_CAM = ("no photorealistic human faces, no hands in frame, no crowds of people, "
          "illustrative rather than photographic, "
          "any writing or signage drawn only as abstract wavy squiggle lines, "
          "never legible letters or words, no readable text anywhere")

# NÉT CHÌ CHO NHÓM NHÂN VẬT (anh chọn 29/8: "người nổi tiếng, vĩ nhân, người thành công, công ty
# đế chế gia tộc lớn — vẽ kiểu nét chì sẽ hợp hơn, khác lạ hơn footage free").
# Vì sao đúng cả về kỹ thuật: chân dung ẢNH CHỤP là chỗ máy vẽ hỏng rõ nhất — mắt người có sẵn
# một bản gốc để so, nên lệch một chút là thấy ngay "giả". Chân dung NÉT CHÌ thì không có bản gốc
# nào để so: người xem đọc nó như một bức vẽ, và máy vẽ nét chì rất tốt.
# Và nó giải luôn bài toán nhận diện: mọi kênh khác đang xài footage kho giống nhau; một kênh
# toàn tranh chì thì nhìn phát ra ngay là của mình.
# BA GU VẼ ANH CHỌN (29/8): NÉT CHÌ NGHỆ THUẬT · CHIBI · VINTAGE.
# Bản trước đã bỏ được ảnh người thật, nhưng anh xem lại vẫn nói "hơi giống thật" — đúng: cụm
# "detailed / high contrast / portrait drawing" kéo máy vẽ về phía RENDER CHI TIẾT, tức vẫn là
# một bức ảnh chỉ khoác lớp chì. Muốn ra tranh thì phải nói bằng ngôn ngữ của tranh: nét tay, giấy
# phác, tỉ lệ cách điệu, mực in lệch màu — và phải NÓI THẲNG "không phải ảnh chụp", vì đó là thứ
# mô hình mặc định trả về khi không bị cấm.
#
# Ba gu chứ không một: mười kênh dùng chung một nét vẽ thì lại thành "cùng một lò" — đúng thứ vừa
# tốn công xoá khỏi ảnh đại diện và bố cục. Chia theo NICHE, thứ cố định của kênh.
# BA GU VẼ ANH CHỌN (29/8): NÉT CHÌ NGHỆ THUẬT · CHIBI · VINTAGE — neo vào ĐÚNG BA TRƯỜNG PHÁI
# NGƯỜI MỸ NHẬN RA NGAY, vì khán giả đích là Mỹ.
#
# Bản trước đã bỏ được ảnh người thật, nhưng anh xem lại vẫn nói "hơi giống thật" — đúng: cụm
# "detailed / high contrast / portrait drawing" kéo máy vẽ về phía RENDER CHI TIẾT, tức vẫn là một
# bức ảnh chỉ khoác lớp chì. Muốn ra tranh thì phải nói bằng ngôn ngữ của tranh (nét tay, giấy
# phác, mực in lệch màu) và phải NÓI THẲNG "không phải ảnh chụp" — đó là thứ mô hình mặc định trả
# về khi không bị cấm.
#
# Và gọi tên trường phái CÓ THẬT thay vì tả suông: mô hình được huấn luyện trên chú thích của
# hàng triệu bức tranh, nên "New Yorker style editorial illustration" dẫn nó tới đúng chỗ, còn
# "vẽ đẹp nghệ thuật" thì không dẫn tới đâu cả.
#
# Ba gu chứ không một: mười kênh dùng chung một nét vẽ thì lại thành "cùng một lò" — đúng thứ vừa
# tốn công xoá khỏi ảnh đại diện và bố cục. Chia theo NICHE, thứ cố định của kênh.

# Ký hoạ biên tập Mỹ: gu của phác thảo phiên toà trên bản tin và tranh minh hoạ The New Yorker.
GU_NET_CHI = (
    "New Yorker style editorial pencil illustration, expressive loose graphite strokes, visible "
    "construction lines and eraser smudges on rough sketchbook paper, stylised proportions, "
    "generous white space, unfinished edges, American courtroom-sketch tradition — "
    "NOT a photograph, not photorealistic, not 3d render")

# Hoạt hình Mỹ hiện đại: đường viền dày, màu phẳng — gu của Cartoon Network / explainer trên YouTube.
GU_CHIBI = (
    "cute chibi cartoon illustration in modern American animation style, oversized head and tiny "
    "body, thick clean outlines, flat cel shading, bold saturated palette, playful sticker art, "
    "Cartoon Network energy — NOT a photograph, not photorealistic, not 3d render")

# Quảng cáo Mỹ giữa thế kỷ: áp phích WPA, bìa Saturday Evening Post, in lụa lệch màu.
GU_VINTAGE = (
    "mid-century American advertising lithograph, 1950s Saturday Evening Post and WPA poster "
    "style, aged paper with foxing, slightly misregistered ink layers, limited three-colour "
    "palette, halftone dot texture — NOT a photograph, not photorealistic, not 3d render")

# Vũ trụ / khoa học / viễn tưởng: đây là chỗ máy vẽ MẠNH NHẤT — không có bản gốc nào để mắt người
# đem ra so, nên nó tha hồ đẹp mà không sợ "trông giả". Ngược hẳn với chân dung ảnh chụp.
# Gọi tên đúng trường phái người Mỹ biết: bìa tiểu thuyết viễn tưởng thập niên 70-80, tranh vũ trụ
# kiểu Bonestell, ảnh giả lập của NASA.
GU_VU_TRU = (
    "retro sci-fi book cover art, 1970s space illustration in the tradition of Chesley Bonestell "
    "and NASA concept paintings, luminous nebula gradients, vast scale with a tiny silhouette for "
    "reference, airbrushed glow, deep starfield — NOT a photograph, not photorealistic")

# Bản vẽ khoa học: giải phẫu, địa chấn, khí tượng — thứ cần trông CHÍNH XÁC chứ không cần đẹp
# kiểu tranh. Gu bản khắc giáo khoa Mỹ: nét mảnh, chú thích gọn, giấy kem.
GU_KHOA_HOC = (
    "vintage scientific plate illustration, fine engraved linework and stipple shading, "
    "cream textured paper, restrained ochre and slate accents, museum specimen board, "
    "American textbook diagram tradition — NOT a photograph, not photorealistic")

# ── GÁN GU THEO TỪNG KÊNH (29/8) ───────────────────────────────────────────────────────────
# Anh: "ko kiểu râu ông nọ cắm cằm bà kia". Đúng, và bản gán theo NICHE làm đúng chuyện đó:
#   QUIET LAYOFFS (sa thải, đọc hồ sơ SEC)  -> tranh vũ trụ, vì niche ghi "Công nghệ & AI"
#   FILINGS SAY   (hồ sơ SEC)               -> tranh vũ trụ, cùng lý do
#   PILL FACTS    (thu hồi thuốc)           -> chibi dễ thương, vì niche ghi "Sức khoẻ & gym"
#   COST TO GO    (nước giàu nhất)          -> tranh vũ trụ, vì niche ghi "Du lịch"
# Niche là nhãn PHÂN LOẠI KHO, không phải mô tả nội dung: "Du lịch" gom cả giá vé lẫn máy bay đang
# bay, "Sức khoẻ" gom cả nghiên cứu y khoa lẫn thuốc bị thu hồi. Suy gu từ nhãn kho là suy từ một
# thứ không mang thông tin cần.
# Nên gán TỪNG KÊNH. Năm mươi dòng là đọc được, và mỗi dòng nói rõ kênh đó KỂ chuyện gì.
GU_THEO_KENH = {
    # Ký hoạ biên tập — người, tiền, tội phạm, luật, nghề: chuyện nghiêm túc về con người.
    "AMERICA LOOKED UP": "chi", "FAME CURVE": "chi", "COLD FILE": "chi", "COURT RECORD": "chi",
    "SUED FOR THIS": "chi", "YOUR RIGHTS CASE": "chi", "MISSING PIECE": "chi",
    "UNSOLVED LOG": "chi", "NIGHT SHIFT": "chi", "REAL PLACE": "chi", "PAYCHECK GAP": "chi",
    "PRICE OF NOW": "chi", "RENT REALITY": "chi", "HOUSE MATH": "chi", "WHERE TO MOVE": "chi",
    "JOB DYING": "chi", "SALARY TRUTH": "chi", "QUIET LAYOFFS": "chi", "DEGREE WORTH": "chi",
    "FILINGS SAY": "chi", "COST TO GO": "chi", "PILL FACTS": "chi", "MARRIAGE MATH": "chi",
    # Áp phích Mỹ giữa thế kỷ — lịch sử, nhạc, phim, xe, quân sự, hàng không, thể thao.
    "ARCHIVE REEL": "vin", "THEN AND NOW": "vin", "ONE HIT": "vin", "SONG FILE": "vin",
    "GONE TOO SOON": "vin", "SHOW NUMBERS": "vin", "CAR RECALL": "vin", "MPG TRUTH": "vin",
    "PENTAGON LEDGER": "vin", "WEAPON PRICE": "vin", "SKY RIGHT NOW": "vin",
    "COURT KINGS": "vin", "DIAMOND NUMBERS": "vin", "PAID VS PLAYED": "vin",
    # Hoạt hình — đồ ăn, thú cưng, game, chuyện nhẹ.
    "BREED FILE": "chibi", "WILD NUMBERS": "chibi", "CALORIE SHOCK": "chibi",
    "RECALL PLATE": "chibi", "WHAT IS IN IT": "chibi", "GAME GRAVEYARD": "chibi",
    "STEAM TRUTH": "chibi", "WHAT THEY SEARCH": "chibi",
    # Vũ trụ — chỗ máy vẽ mạnh nhất, để dành cho kênh thật sự nói về vũ trụ.
    "NEAR EARTH": "vutru", "SPACE INVOICE": "vutru",
    # Bản vẽ khoa học — địa chấn, khí tượng, y khoa.
    "QUAKE LOG": "khoahoc", "ALERT NOW": "khoahoc", "ONE STUDY": "khoahoc",
}
_GU_MA = {"chi": None, "vin": None, "chibi": None, "vutru": None, "khoahoc": None}

# Đường lui theo NICHE cho kênh THÊM SAU mà chưa kịp gán tay.

# Mọi niche của 50 kênh đều phải rơi vào một nhóm: kênh không thuộc nhóm nào sẽ nhận gu cũ (tả một
# bức ẢNH) và lại ra ảnh giống thật — đúng thứ đang đi sửa.
NICHE_NET_CHI = ("người nổi tiếng", "vĩ nhân", "doanh nhân", "kinh doanh", "công ty",
                 "tiểu sử", "thành công", "gia tộc", "tội phạm", "luật", "bí ẩn",
                 "kinh dị", "rùng rợn", "tiền", "tài chính")
NICHE_VINTAGE = ("lịch sử", "nhạc", "phim", "văn hoá", "quân sự", "nhà ở", "xe")
NICHE_VU_TRU = ("vũ trụ", "không gian", "thiên văn", "khoa học", "công nghệ", "viễn tưởng",
                "thời tiết", "địa chất", "du lịch")
NICHE_CHIBI = ("thú cưng", "động vật", "đồ ăn", "đồ uống", "quan hệ", "hẹn hò", "game",
               "thể thao", "sức khoẻ", "gym", "giáo dục")


def gu_ve(kenh: dict) -> str:
    """Gu vẽ TIẾNG ANH cho một kênh — thứ thật sự gửi lên máy vẽ ảnh.

    Không dịch được thì trả về chuỗi cấm; thà để máy vẽ tự chọn bố cục còn hơn nhét cho nó một
    câu tiếng Việt mà nó chắc chắn bỏ qua (và bỏ qua thì nó vẽ ảnh người thật, xem trên)."""
    tho = str((kenh.get("brand") or {}).get("style_anh") or kenh.get("style_anh") or "").strip()
    niche = str(kenh.get("niche") or "").lower()
    # Ba gu cách điệu ĐÈ LÊN gu khai trong cấu hình. Gu cũ tả một bức ẢNH ("ảnh tài liệu ố vàng",
    # "ảnh đêm tương phản mạnh") nên dù dịch sang tiếng Anh vẫn kéo máy vẽ về phía ảnh chụp.
    # BẢNG GÁN TAY ĐỨNG TRƯỚC MỌI SUY LUẬN — xem `GU_THEO_KENH`.
    _bang = {"chi": GU_NET_CHI, "vin": GU_VINTAGE, "chibi": GU_CHIBI,
             "vutru": GU_VU_TRU, "khoahoc": GU_KHOA_HOC}
    _ma = GU_THEO_KENH.get(str(kenh.get("ten") or "").strip().upper())
    if _ma and _ma in _bang:
        return f"{_bang[_ma]}, {GU_CAM}"
    # Đường lui theo niche cho kênh thêm sau mà chưa kịp gán tay.
    for nhom, gu in ((NICHE_VU_TRU, GU_VU_TRU), (NICHE_NET_CHI, GU_NET_CHI),
                     (NICHE_VINTAGE, GU_VINTAGE), (NICHE_CHIBI, GU_CHIBI)):
        if any(t in niche for t in nhom):
            return f"{gu}, {GU_CAM}"
    en = GU_VE_EN.get(tho.lower()) or GU_VE_EN.get(tho) or ""
    return f"{en}, {GU_CAM}" if en else f"{GU_NET_CHI}, {GU_CAM}"


def dung_props_phim(kenh: dict, ky: dict | None = None, keys: list | None = None,
                    st_san: dict | None = None, ky_hieu: str = ""):
    """Dựng props phim kể + kiểm mở đầu, KHÔNG render. Trả (props, story, slug) hoặc None.

    Dạng phim kể: mỗi cảnh MỘT ảnh AI vẽ theo `style_anh` của kênh.

    Khác 6 dạng kia ở chỗ CẦN KEY vẽ ảnh. `build_doc_props(..., ai_only=True)` đã có sẵn chế độ
    100% ảnh AI với gu riêng — dùng lại, khỏi viết engine mới.
    Không có key thì trả None chứ không render ra video toàn khung trắng."""
    import datastory_ci as DS
    st = st_san or dung_story_cinematic(kenh, ky)
    if not st:
        return None
    # 27/8 — ĐÂY LÀ CHỖ 10 KÊNH PHIM RA 0 VIDEO SUỐT PHIÊN 12:14.
    #
    # `chay_chung` gọi hàm này mà KHÔNG truyền `keys` (thiếu đúng một tham số), nên `keys` luôn
    # rỗng, `api` lùi về biến môi trường `GEMINI_API_KEY` — biến đó không được đặt trong lane vì
    # lane lấy key từ HỒ. Kết quả: `api` rỗng -> bỏ lượt, 30 lần trong một phiên, và CẢ NHÓM
    # cinematic (10/50 kênh = 20% hệ) không ra nổi một video nào.
    # Chiều nay tôi đã đổ cho con key chết. Key chết là thật, nhưng nó chỉ là lớp thứ hai — lớp
    # thứ nhất là dòng gọi thiếu tham số, và nếu không sửa thì vá key chết cũng vô ích.
    #
    # Đồng thời: lấy `keys[0]` là sai về nguyên tắc. Một key duy nhất cho cả lượt vẽ nghĩa là key
    # đó cạn hoặc chết thì cả video hỏng, trong khi hồ có hàng trăm key. `_vision_key` chọn key
    # còn sống theo đúng thứ tự ưu tiên đã có, và `set_ai_pool` bên dưới lo phần xoay vòng.
    keys = keys or []
    if keys:
        DS.set_ai_pool(keys, kenh["ten"])
    api = ""
    if keys:
        try:
            api = DS._vision_key(keys) or ""
        except Exception:
            api = (keys[0].get("key") or "") if keys else ""
    api = api or os.environ.get("GEMINI_API_KEY", "") or ""
    if not api:
        print(f"   ⚠️ {kenh.get('ten')}: dạng phim kể cần key vẽ ảnh — bỏ lượt "
              f"(nhận {len(keys)} key, không key nào dùng được cho vẽ/soi ảnh)")
        return None
    b = (kenh.get("brand") or {}).get("palette") or {}
    props = DS.build_doc_props(st, kenh["ten"], api_key=api,
                               accent=b.get("primary", "#22D3EE"),
                               accent2=b.get("accent", "#F5B301"),
                               font=(kenh.get("brand") or {}).get("font", ""),
                               handle=kenh["handle"],
                               ai_style=gu_ve(kenh), ai_only=True,
                               prefix="th2_")
    # Cùng lớp chặn "nền trơn" như ba đường Cinematic bên datastory_ci: đo trên KHUNG THẬT,
    # không đoán qua mô hình lớp phủ. Kênh chất liệu B/C vẽ ảnh bằng AI nên càng dễ ra khung tối
    # đều màu — đúng thứ QC loại sau khi đã tốn cả lượt vẽ lẫn lượt render.
    _that = DS.xac_minh_mo_dau(props, "CinematicShort", dark_ok=False)
    if _that:
        print(f"   ⚠️ {kenh['ten']}: mở đầu {_that} — bỏ lượt TRƯỚC render")
        return None
    sl = DS.slug(kenh["handle"].lstrip("@")) + (f"_{ky_hieu}" if ky_hieu else "")
    return props, st, sl


def keys_cuc_bo() -> list:
    """Hồ key cho lúc chạy TAY TRÊN MÁY — đọc từ `.keys.local` (đã cho vào .gitignore).

    29/8 — vì sao cần. Dạng `cinematic` (10/50 kênh) bắt buộc phải có key vẽ ảnh, nên trên máy
    không key thì nó bỏ lượt và KHÔNG cách nào soi được khung của nó bằng mắt — trong khi soi bằng
    mắt là thứ duy nhất bắt được lỗi bố cục (bộ đo pixel đã chứng minh vô dụng). Kết quả: 10 kênh
    sửa mù, vá xong không biết đúng hay sai.
    Trên CI thì key tới từ hồ Firestore; ở máy thì không có creds. Nên mở một lối riêng chỉ dùng
    khi chạy tay, và nó phải KHÔNG BAO GIỜ lọt vào git.

    Định dạng: mỗi dòng một key, bỏ qua dòng trống và dòng bắt đầu bằng `#`.
        AIza...                (Gemini)
        cf:<account_id>:<token>  (Cloudflare Workers AI — FLUX vẽ ảnh)
    Không có tệp thì trả rỗng và mọi thứ chạy y như trước."""
    ra = []
    for nguon in (os.path.join(GOC, ".keys.local"),
                  os.environ.get("MM0_KEYS_FILE") or ""):
        if not (nguon and os.path.exists(nguon)):
            continue
        for d in io.open(nguon, encoding="utf-8").read().splitlines():
            d = d.strip()
            if d and not d.startswith("#"):
                ra.append({"id": f"local{len(ra)}", "key": d})
        break
    tho = (os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY") or "").strip()
    for k in tho.split(","):
        if len(k.strip()) > 20:
            ra.append({"id": f"env{len(ra)}", "key": k.strip()})
    return ra


def chay_phim(kenh: dict, ra: str = "", ky: dict | None = None, keys: list | None = None,
              st_san: dict | None = None, ky_hieu: str = "") -> tuple[str, dict] | None:
    """Phim kể (ảnh AI): dựng props -> render CinematicShort (9:16)."""
    import datastory_ci as DS
    _dp = dung_props_phim(kenh, ky, keys, st_san, ky_hieu)
    if not _dp:
        return None
    props, st, sl = _dp
    pf = os.path.join(DS.PUB, f"_th2_phim_{sl}.json")
    json.dump(props, io.open(pf, "w", encoding="utf-8"), ensure_ascii=False)
    ra = os.path.abspath(ra or os.path.join(GOC, "out", f"th2_phim_{sl}.mp4"))
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    DS.run_render_cmd(["npx", "remotion", "render", "src/index.ts", "CinematicShort", ra,
                       f"--props=./{os.path.relpath(pf, DS.ENG)}", "--gl=swiftshader", "--jpeg-quality=100", "--crf=15",
                       "--concurrency=2", "--log=error"],
                      cwd=DS.ENG, timeout=2400, label=f"CinematicShort({kenh['ten']})")
    ok, info = DS.qc(ra)
    print(f"{'✅' if ok else '❌'} {kenh['ten']} [phim kể] · {info}")
    if ok:
        chuan_am(ra)          # đưa về -14 LUFS trước mọi khâu sau (xem `chuan_am`)
        _hok, _htin = qc_hook_sau_render(ra, kenh.get("ten", ""), keys)
        if isinstance(info, dict):
            info.update(_htin)
        if not _hok:
            return None
        lam_thumb(kenh, st, ra, "CinematicShort", pf)
    if isinstance(info, dict):
        info["_props_obj"] = props
    return (ra, info) if ok else None



# ══════════════════════════════════════════════════════════════════════════════════════════
# XOAY VÒNG ĐỀ TÀI (26/8/2026) — THỨ QUYẾT ĐỊNH KÊNH SỐNG HAY CHẾT
#
# Cả 50 kênh đều có trường `tham_so.xoay` ghi rõ trục xoay ("mon" / "nam" / "tu_khoa" / …), nhưng
# rà lại thì **KHÔNG DÒNG MÃ NÀO ĐỌC NÓ**. Tham số lấy nguyên từ `tham_so` cố định, `ky` thì luôn
# None. Nghĩa là mỗi kênh làm ĐÚNG MỘT câu chuyện rồi lặp lại mãi: cùng loại ngũ cốc, cùng từ khoá,
# cùng năm. 50 kênh × một video lặp = kênh chết ngay, và YouTube tính là nội dung trùng lặp.
# Cùng họ với `voice_tone` và `brand.font`: khai ra rồi để đó.
#
# Cơ chế: mỗi trục có một KHO giá trị. Mỗi lượt duyệt kho theo thứ tự, dựng thử story, và BỎ QUA
# giá trị nào cho ra tiêu đề đã có trong `avoid` (danh sách video kênh đã làm — `run_render` vốn
# tính sẵn cho các kênh đời 1 qua `_avoid_for`). Hết kho mà vẫn trùng thì mới bỏ lượt.
# ══════════════════════════════════════════════════════════════════════════════════════════

_NAM_NAY = _datetime.date.today().year

# Kho cho từng trục. Giá trị phải là thứ NGUỒN THẬT chấp nhận — đây không phải chỗ bịa cho có.
_BANG_50 = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
            "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
            "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
            "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
            "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
            "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island",
            "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia",
            "Washington", "West Virginia", "Wisconsin", "Wyoming"]

# 26/8 — KHO NÀY TỪNG PHỦ ĐÚNG 17/50 KÊNH. Đo thật:
#     tu_khoa 13 kênh · tu_nam 6 · bangs 3 · mua 2 · loc 2 · hang 2 · thang/giong/tu_ngay/den_ngay 4
#     -> tất cả đều `kho KHÔNG CÓ giá trị`
# Kênh không có kho thì `_dung_story_xoay` chỉ còn ĐÚNG MỘT lượt thử; làm xong video đầu là tiêu đề
# vào `avoid` và mọi lượt sau BỎ LƯỢT — tức 33/50 kênh câm vĩnh viễn sau một video. Chốt selftest
# lúc đó vẫn xanh vì nó chỉ kiểm "có khai trục xoay" và "trục có được đọc", KHÔNG kiểm kho rỗng.
#
# Và một lỗi lệch tên kinh điển: kho khai `"bang"`, kênh dùng trục `"bangs"` — lệch một chữ `s`,
# 3 kênh mất sạch kho, không có gì báo. Cùng họ với `doc_kenh` (33/50 tra không ra) và với việc
# radar đọc khoá `name` trong khi nguồn trả `giong`/`ten`.
KHO_XOAY: dict[str, list] = {
    # Nhóm hàng của Open Food Facts (đã kiểm bằng gọi thật, xem du_lieu_mo.thanh_phan_off)
    "mon": ["breakfast-cereals", "pizzas", "sodas", "chocolates", "crisps", "biscuits",
            "energy-drinks", "ice-creams", "breads", "cheeses", "yogurts", "sauces",
            "peanut-butters", "cereals", "frozen-foods", "snacks", "juices", "coffees",
            "chips", "candies", "meats", "fishes"],
    # Năm: nới từ 6 lên 16. Sáu năm × 6 chương = đúng MỘT bộ rồi cạn — nguyên nhân trực tiếp khiến
    # 10 kênh trục `nam` chỉ làm được một bộ. Các nguồn (openFDA, USAspending, BLS) đều có dữ liệu
    # sâu hơn 6 năm rất nhiều; radar `kiem_chung` sẽ loại năm nào thật sự không có số.
    "nam": [_NAM_NAY - i for i in range(1, 17)],
    "tu_nam": [_NAM_NAY - i for i in range(1, 17)],
    # Cửa sổ ngày lùi về trước
    "ngay": [7, 14, 21, 30, 45, 60, 90, 120, 180, 270, 365, 545, 730],
    "tu_ngay": [7, 14, 30, 60, 90, 180, 365, 730],
    "den_ngay": [0, 7, 14, 30, 60, 90],
    "thang": list(range(1, 13)),
    # Mùa giải thể thao
    "mua": [f"{n}-{str(n + 1)[-2:]}" for n in range(2010, _NAM_NAY)],
    # Hãng xe (NHTSA)
    "hang": ["Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "Jeep", "Hyundai", "Kia", "Subaru",
             "BMW", "Mercedes-Benz", "Volkswagen", "Tesla", "Ram", "GMC", "Dodge", "Mazda",
             "Lexus", "Audi", "Volvo"],
    "bang": list(_BANG_50),
    "bangs": list(_BANG_50),
}


def _chuan_truc(truc: str) -> str:
    """Chuẩn hoá tên trục trước khi tra kho — chịu được số nhiều/số ít và dấu gạch.

    26/8 — kho khai `"bang"`, ba kênh khai trục `"bangs"`. Lệch một chữ `s` mà mất sạch kho, và
    không có gì báo vì `dict.get` trả None rất lịch sự. Đây là lần thứ ba trong ngày cùng một lớp
    lỗi "hai bên dùng khuôn tên khác nhau", nên chặn ở đây một lần cho xong."""
    t = str(truc or "").strip().lower().replace("-", "_")
    if t in KHO_XOAY:
        return t
    for bien in (t.rstrip("s"), t + "s"):
        if bien in KHO_XOAY:
            return bien
    return t


def _kho_xoay_cua(kenh: dict) -> tuple[str, list]:
    """(tên trục, kho giá trị) cho một kênh. Kho rỗng = kênh này không xoay được."""
    ts = kenh.get("tham_so") or {}
    truc = str(ts.get("xoay") or "").strip()
    if not truc:
        return "", []
    # Kênh tự mang kho riêng thì ưu tiên — chính xác hơn kho chung.
    rieng = ts.get("kho_" + truc)
    if isinstance(rieng, list) and rieng:
        return truc, list(rieng)
    return truc, list(KHO_XOAY.get(_chuan_truc(truc)) or [])


# `run_render._avoid_for` CẮT mọi mục trong sổ tránh-trùng xuống 60 ký tự (để prompt khỏi phình).
# Nên phép so ở đây cũng PHẢI cắt bên kia đúng bấy nhiêu — nếu không, hai bên so hai độ dài khác
# nhau và không bao giờ khớp.
_DAI_SO = 60


def _tieu_de_da_lam(tieu_de: str, avoid) -> bool:
    """Tiêu đề này đã ra lò chưa. So sau khi bỏ dấu câu để "X in 2024" và "X In 2024." là một.

    27/8 — SO PHẢI CÙNG ĐỘ DÀI, và đây là chỗ bản vá tiêu đề của tôi tự phá chính nó.
    `_avoid_for` cắt mọi mục xuống 60 ký tự. Trước đây tiêu đề là khuôn ngắn ("Most-read on
    Wikipedia — Aug 24, 2026" = 41 ký tự) nên cắt không đụng gì và phép so vẫn đúng.
    Từ khi tiêu đề dẫn bằng chủ thể, nó dài ra:
        "Shelley Fabares: 466K — Most-read on Wikipedia — Aug 24, 2026"  (61 ký tự)
    Sổ giữ bản ĐÃ CẮT, hàm này so bản ĐẦY ĐỦ -> không bao giờ khớp -> hệ tin là chưa từng làm ->
    đo thật: **9 long y hệt nhau** trên AMERICALOOKEDUP, 6 trên GAME GRAVEYARD, trong MỘT phiên.
    Đúng thứ bản vá sinh ra để diệt, và nó tự tạo ra vì làm tiêu đề dài hơn.
    Bài học: đổi HÌNH DẠNG một giá trị thì phải soi mọi nơi so sánh giá trị đó — cắt chuỗi là một
    phép so ẩn."""
    import re as _r
    g = lambda x: _r.sub(r"[^a-z0-9 ]", "", str(x or "")[:_DAI_SO].lower()).strip()
    t = g(tieu_de)
    return bool(t) and any(g(a) == t for a in (avoid or []))


_BIEN_MAP: dict = {}


def bien_cua(kenh: dict) -> int:
    """Chỉ số BIẾN THỂ BỐ CỤC của một kênh — thứ tự của nó trong nhóm CÙNG `dinh_dang`.

    26/8 — anh chỉ ra: 50 kênh mà chỉ có 7 `dinh_dang`, riêng `ranked` dùng lại 18 lần. Màu chính
    50/50 khác nhau, giọng 50/50 khác nhau, nhưng khán giả nhận ra "cùng một lò" qua BỐ CỤC chứ
    không qua mã màu — nên 18 kênh vẫn nhìn như một.

    Không viết 18 bố cục. `Bien.tsx` tách bố cục thành ba công tắc độc lập (vị trí nhãn × kiểu thẻ
    × hoạ tiết nền) = 27 tổ hợp; hàm này chỉ việc phát cho mỗi kênh một số khác nhau trong nhóm.
    Đánh theo THỨ TỰ trong `kenh_the_he_2.json` nên cố định: bố cục của một kênh không được đổi
    giữa các video, vì nhận diện kênh phải ổn định — đó là toàn bộ mục đích."""
    global _BIEN_MAP
    if not _BIEN_MAP:
        try:
            ds = json.load(io.open(os.path.join(GOC, "kenh_the_he_2.json"), encoding="utf-8"))
            ds = ds if isinstance(ds, list) else list(ds.values())
            dem: dict = {}
            for k in ds:
                d = str(k.get("dinh_dang") or "")
                _BIEN_MAP[str(k.get("handle") or "")] = dem.get(d, 0)
                dem[d] = dem.get(d, 0) + 1
        except Exception:
            _BIEN_MAP = {"_": 0}
    return int(_BIEN_MAP.get(str(kenh.get("handle") or ""), 0))


def _ve_vat(kenh: dict, props: dict, keys: list | None, ky_hieu: str = "") -> int:
    """Vẽ HÌNH THẬT cho từng vật trong dạng `scaled` — thay emoji.

    27/8 — anh nói thẳng: emoji làm đồ hoạ dữ liệu là "rẻ tiền". Đúng, và còn hai lý do kỹ thuật
    nữa: emoji hiện khác nhau tuỳ nền tảng, và nó gần vuông nên từng ép chiều cao cột phải bằng
    bề ngang (xem `hs` trong ScaledShort) — chính chỗ từng xoá sạch tỉ lệ.
    Anh có 87 key Cloudflare = ~15.100 ảnh FLUX miễn phí mỗi ngày. Một video dạng này cần 6 ảnh.
    Kho đó đang bỏ không trong khi mình vẽ bằng emoji.

    Gọi qua `DS.fetch_image(ai_only=True)`: bỏ hẳn kho ảnh chụp sẵn, đi thẳng vào vẽ — CF FLUX
    trước, Gemini sau (xem `_ai_candidates`). Vẽ theo `style_anh` riêng của kênh nên 6 kênh dạng
    `scaled` không ra cùng một gu.
    FAIL-OPEN: vẽ hụt thì giữ nguyên emoji, video vẫn ra. Đây là lớp làm ĐẸP HƠN, không được
    thành chỗ chết mới."""
    import datastory_ci as DS
    items = props.get("items") or []
    if not items:
        return 0
    if keys:
        try:
            DS.set_ai_pool(keys, kenh.get("ten", ""))
        except Exception:
            pass
    style = gu_ve(kenh)          # TIẾNG ANH, xem `gu_ve` — trước đây gửi thẳng chuỗi tiếng Việt
    sl = DS.slug(kenh["handle"].lstrip("@")) + (f"_{ky_hieu}" if ky_hieu else "")
    thu = os.path.join(DS.PUB, "img", "th2v_" + sl)
    os.makedirs(thu, exist_ok=True)
    n = 0
    for i, it in enumerate(items[:6]):
        ten = str(it.get("name") or "").strip()
        if not ten:
            continue
        dest = os.path.join(thu, f"{i}.jpg")
        try:
            if os.path.exists(dest) or DS.fetch_image(ten, dest, ai_only=True, ai_style=style,
                                                      ai_prompt=f"{ten}, {style}" if style else ten):
                it["img"] = os.path.relpath(dest, DS.PUB)
                n += 1
        except BaseException as e:
            if isinstance(e, KeyboardInterrupt):
                raise
            print(f"      ⚠️ không vẽ được `{ten[:24]}` ({str(e)[:40]}) — giữ emoji")
    if n:
        print(f"   🎨 {kenh.get('ten')}: vẽ {n}/{len(items[:6])} hình thật (Cloudflare FLUX), thay emoji")
    return n


def dung_props(kenh: dict, st: dict, dang: str, ten_props: str, ky_hieu: str = "",
               keys: list | None = None):
    """Dựng props + ghi tệp props, KHÔNG render. Trả (props, đường_tệp_props, slug).

    26/8 — tách ra khỏi `chay_chung` vì LONG khổ ngang cần props của NHIỀU chương hơn số short:
    long ghép `so_chuong` chương, còn short chỉ dựng `so_short` cái. Trước đây hai việc dính liền
    nên muốn có props của một chương là buộc phải render nguyên một short cho nó — vừa phí, vừa ép
    số chương của long bằng đúng số short (long 3 chương ≈ 2 phút).

    Anh nói rõ: short KHÔNG phải cắt từ long ra, mà viết + dựng lại riêng cho 9:16 có hook. Nên
    long và short dùng CHUNG kịch bản (story + tiếng nói) nhưng đi hai đường render khác nhau."""
    import datastory_ci as DS
    # 26/8 — `ky_hieu` là thứ BẮT BUỘC khi long ghép nhiều chương. Cả thư mục tiếng nói lẫn tệp
    # props trước đây đặt tên theo KÊNH (`_th2_{dang}_{slug}`), không theo chương — hợp lý khi mỗi
    # chương dựng xong render ngay rồi vứt. Nhưng long cần props của MỌI chương cùng lúc: giữ tên
    # cũ thì chương 2 ghi đè chương 1, và long sẽ ghép 6 bản sao của chương cuối, mỗi bản mang
    # tiếng nói của chương khác. Đây đúng dạng lỗi không có gì đỏ để thấy — video vẫn ra, vẫn dài,
    # chỉ là nội dung sai.
    sl = DS.slug(kenh["handle"].lstrip("@")) + (f"_{ky_hieu}" if ky_hieu else "")
    sdir = os.path.join(DS.PUB, "narration", f"_th2_{dang}_" + sl)
    os.makedirs(sdir, exist_ok=True)
    props = getattr(DS, ten_props)(st, sdir, handle=kenh["handle"])
    br = kenh.get("brand") or {}
    b = br.get("palette") or {}
    if b.get("primary"):
        props["accent"] = b["primary"]
        props.setdefault("color", b["primary"])
    # PHÔNG RIÊNG TỪNG KÊNH (26/8). Không có dòng này thì `brand.font` chỉ là chữ nằm trong JSON:
    # engine mặc định Poppins, và 50 kênh lại dùng chung một khuôn chữ — đúng cái bẫy `voice_tone`
    # (ghi vào brand kit từ đầu mà không hàm nào đọc, nên suốt thời gian qua vô tác dụng).
    if br.get("font"):
        props["font"] = br["font"]
    # BIẾN THỂ BỐ CỤC. Thiếu dòng này thì `Bien.tsx` chỉ là mã chết và 18 kênh `ranked` vẫn chung
    # một khuôn — đúng cái bẫy "khai ra rồi không ai gửi" đã vấp với `voice_tone`, `brand.font`,
    # `palette.bg` và `tham_so.xoay`. Lần này chốt luôn: t_bien_bo_cuc_khong_trung.
    props["bien"] = bien_cua(kenh)
    # Chỉ vẽ ảnh vật thể khi bố cục THẬT SỰ hiển thị ảnh. Bố cục vector không có chỗ cho ảnh,
    # nên vẽ là ném thẳng 6 lượt hạn mức vào thùng rác — và mỗi lượt vẽ là một cơ hội bịa chữ.
    if dang == "scaled" and bo_cuc_cua(kenh, dang) == "ScaledShort":
        _ve_vat(kenh, props, keys, ky_hieu)
    # 27/8 — DÒNG NGUỒN cho MỌI dạng, không chỉ dạng đua.
    # Soi 6 dạng: 4 dạng không in một chữ nào về nguồn dữ liệu. Mất hai thứ cùng lúc — lòng tin
    # của người xem ("số này ở đâu ra?"), và bằng chứng trước chính sách "nội dung sản xuất hàng
    # loạt" của YouTube. Trong khi dữ liệu của mình VỐN là dữ liệu công khai tra được, tức là một
    # lợi thế đang bị bỏ không. Chỉ cần truyền xuống; `DongNguon` lo phần hiển thị kín đáo.
    if st.get("nguon") and not props.get("source"):
        props["source"] = ten_nguon(st.get("nguon", ""))
    # NHẠC NỀN RIÊNG cho MỌI dạng (27/8). `datastory_ci` đặt mặc định một bản chung; ghi đè ở đây
    # để mỗi kênh một vòng nhạc. Xem `brandkit_the_he_2.chia_hinh`: 14 bản chia đều 50 kênh.
    _nhac = _nhac_co_that((kenh.get("brand") or {}).get("nhac"), kenh.get("ten", ""))
    if _nhac:
        props["music"] = _nhac
    # NỀN RIÊNG TỪNG KÊNH (26/8). Nền chiếm gần hết khung hình; để nó viết cứng trong composition
    # nghĩa là 18 kênh dạng `ranked` dùng CHUNG một nền — khán giả nhìn là thấy cùng một lò, dù
    # accent đã riêng. `palette.bg/primary/secondary` có sẵn 38/50/50 giá trị khác nhau mà chưa
    # ai đọc — đây là lần thứ NĂM cùng bệnh "khai ra rồi để đó".
    if b.get("primary"):
        props["bg"] = b["primary"]
    if b.get("secondary"):
        props["bg2"] = b["secondary"]
    # HOOK 0-3 GIÂY. `Bookend` nhận `hookStat/hookLabel/hookLine` nhưng nếu Python không gửi thì
    # nó lặng lẽ dùng bản mở đầu cũ (handle + tiêu đề) — đúng bẫy "khai ra rồi không ai gửi" đã
    # gặp 5 lần đêm nay, lần này ở chính mã em vừa viết. Dùng lại đúng số liệu của thumbnail để
    # bìa và 3 giây đầu nói CÙNG một con số — người bấm vào vì con số nào thì thấy ngay con số đó.
    _d = _so_noi_bat(st)
    if _d.get("stat"):
        props["hookStat"] = _d["stat"]
        props["hookLabel"] = _d.get("name", "")
        props["hookLine"] = _cau_hoi_mo(kenh, st)
    # 26/8 — QC VISUAL TRƯỚC RENDER, CHO MỌI DẠNG. `xac_minh_mo_dau` vốn TỔNG QUÁT (nhận tên
    # composition bất kỳ) nhưng suốt thời gian qua chỉ được gọi cho `CinematicShort` — tức 40/50
    # kênh render thẳng, hỏng rồi mới biết, mà một lượt render là vài phút CPU.
    # Đo thật trước khi nối, để khỏi chặn oan: khung mở đầu RankedShort = 57,0% điểm tối · 966 màu;
    # ngưỡng chặn là ≥75% tối VÀ <900 màu ⇒ còn dư 18 điểm an toàn, chỉ khung THẬT SỰ đen và trơn
    # mới bị loại. Dạng dữ liệu không có `scenes` nên không có đường cứu bằng ảnh sáng hơn — bị
    # chặn là bỏ lượt, đúng ý: thà mất một đề tài còn hơn mất một lượt render.
    comp0 = (DUONG_RA.get(dang) or ("", ""))[0]
    if comp0:
        _ly_do = DS.xac_minh_mo_dau(props, comp0)
        if _ly_do:
            print(f"   ⚠️ {kenh.get('ten')}: mở đầu {_ly_do} — BỎ LƯỢT TRƯỚC render")
            return None
    pf = os.path.join(DS.PUB, f"_th2_{dang}_{sl}.json")
    json.dump(props, io.open(pf, "w", encoding="utf-8"), ensure_ascii=False)
    return props, pf, sl


def chuan_am(duong: str, dich_lufs: float = -14.0) -> bool:
    """Đưa âm lượng video về chuẩn phát của YouTube (-14 LUFS).

    27/8 — ĐO ĐƯỢC, và đây là lỗi im lặng nhất trong cả hệ: video ra lò ở **-20,5 LUFS**.
    YouTube chuẩn hoá mọi video về -14 LUFS, nhưng nó CHỈ HẠ CHỨ KHÔNG NÂNG. Nghĩa là bản của
    mình phát ra nhỏ hơn hẳn 6,5 LU so với mọi video nằm cạnh nó trong bảng đề xuất — người xem
    phải vặn to, hoặc lướt qua. Không có cảnh báo nào, không có lỗi nào; chỉ là thua.

    Dùng KHUẾCH ĐẠI TĨNH + GIỚI HẠN ĐỈNH, cố ý không dùng `loudnorm` một lượt:
      • dải động đo được đã hẹp sẵn (LRA 2,2 LU); `loudnorm` còn nén động nữa thì giọng bẹp hẳn,
        mất hết nhấn nhá — đổi một lỗi lấy một lỗi khác.
      • khuếch đại tĩnh giữ nguyên tương quan giọng/nhạc/hiệu ứng đã dựng trong Remotion.
      • `alimiter` chỉ chặn đỉnh vượt ngưỡng, không đụng phần còn lại.

    Video KHÔNG có tiếng, hoặc ffmpeg hụt -> trả False và GIỮ NGUYÊN bản gốc. Âm lượng chưa
    chuẩn thì vẫn là một video xem được; hỏng tệp thì mất trắng."""
    import subprocess as _sp
    import re as _re
    if not duong or not os.path.exists(duong):
        return False
    try:
        r = _sp.run(["ffmpeg", "-hide_banner", "-nostats", "-i", duong,
                     "-af", "ebur128", "-f", "null", "-"],
                    capture_output=True, text=True, timeout=300)
        # PHẢI lấy chỉ số TỔNG KẾT, không lấy `I:` đầu tiên gặp được.
        # `ebur128` in một dòng `I:` cho MỖI KHUNG trong lúc chạy; khung đầu là im lặng nên nó ra
        # -70 LUFS. Bản đầu của hàm này dùng `search` -> vớ đúng con số đó -> tính ra phải bù
        # +56 dB và suýt cho nổ toàn bộ âm thanh. Chỉ số thật nằm trong khối "Summary" ở CUỐI.
        _tom = (r.stderr or "").rsplit("Summary:", 1)
        _vung = _tom[-1] if len(_tom) > 1 else (r.stderr or "")
        m = _re.search(r"I:\s*(-?[\d.]+)\s*LUFS", _vung)
        if not m:
            _tat = _re.findall(r"I:\s*(-?[\d.]+)\s*LUFS", r.stderr or "")
            if not _tat:
                return False
            m = None
            cu = float(_tat[-1])
        else:
            cu = float(m.group(1))
        if cu <= -60:                     # không có tiếng -> đừng khuếch đại nhiễu nền lên
            return False
        bu = dich_lufs - cu
        if abs(bu) < 0.7:                 # đã sát chuẩn, đụng vào chỉ tốn một lượt nén lại
            return True
        tam = duong + ".am.mp4"
        r2 = _sp.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", duong,
                      "-af", f"volume={bu:.2f}dB,alimiter=limit=0.97",
                      "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", tam],
                     capture_output=True, text=True, timeout=900)
        if r2.returncode or not os.path.exists(tam) or os.path.getsize(tam) < 10000:
            if os.path.exists(tam):
                os.remove(tam)
            return False
        os.replace(tam, duong)
        print(f"   🔊 âm lượng: {cu:.1f} -> {dich_lufs:.0f} LUFS (bù {bu:+.1f} dB) — chuẩn phát YouTube")
        return True
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        print(f"   ⚠️ không chuẩn được âm lượng ({str(e)[:50]}) — giữ nguyên bản gốc")
        return False


def qc_hook_sau_render(duong: str, ten_kenh: str = "", keys: list | None = None) -> tuple:
    """QC THỊ GIÁC SAU RENDER, chấm riêng khung hook. Trả (cho_qua, thông_tin).

    26/8 — vì sao cần dù đã có QC kỹ thuật và QC-trước-render. Đo trên một video thật hôm nay:
      • QC kỹ thuật (độ dài · có tiếng · khung hình · mức âm) — CHO QUA cả 4 lỗi thị giác;
      • QC-trước-render (đo % điểm tối) — CHO QUA 4/6 lỗi, nó chỉ bắt được khung gần đen;
      • bốn lỗi còn lại chỉ MẮT thấy: emoji đè lên số dẫn, số dẫn cùng màu nền, nút câu hỏi chữ
        tối trên nền tối, vạch trục xuyên qua chữ.
    Khi 50 kênh chạy tự động thì không ai ngồi nhìn từng video, nên phần "chỉ mắt thấy" phải có
    máy nhìn hộ.

    FAIL-OPEN: không có khoá, Vision lỗi, hết hạn mức — đều CHO QUA. Một cổng QC tự chặn dây
    chuyền khi chính nó hỏng thì tệ hơn là không có cổng."""
    # 27/8 — CỔNG NÀY CHƯA BAO GIỜ CHẠY, VÀ KHÔNG AI BIẾT.
    #
    # Soi cả 186 video của phiên 12:14: KHÔNG có một dòng `🖼️ … hook …đ` nào. Nghĩa là cổng chấm
    # khung mở đầu — thứ được viết ra để bắt bốn lỗi "chỉ mắt thấy" (emoji đè số, số trùng màu
    # nền, chữ tối trên nền tối, vạch trục xuyên chữ) — fail-open suốt, cho qua tất.
    # Gốc: `check_hook` lấy khoá từ biến môi trường `GEMINI_API_KEY`, mà lane render lấy key từ
    # HỒ chứ không đặt biến đó. Không khoá -> ném -> lưới fail-open nuốt -> trả True, KHÔNG in gì.
    # Một cổng chất lượng tắt trong im lặng còn tệ hơn không có cổng: hệ báo "đã kiểm" ở mọi video,
    # và mình tin vào một lớp bảo vệ không tồn tại.
    _k = ""
    try:
        import datastory_ci as _DS
        _k = _DS._vision_key(keys) if keys else ""
    except Exception:
        _k = ""
    try:
        import qc_vision as QV
        ok, tin = QV.check_hook(duong, api_key=_k or None)
    except BaseException as e:
        # Lưới thứ hai, cùng lý do như trong `check_hook`: `SystemExit` không phải `Exception`.
        # Hai lưới vì cổng QC tuyệt đối không được phép giết dây chuyền — thà bỏ qua kiểm.
        if isinstance(e, KeyboardInterrupt):
            raise
        # NÓI RA khi bỏ qua. Vẫn fail-open (cổng QC không được giết dây chuyền), nhưng im lặng thì
        # không phân biệt được "đã kiểm, đạt" với "không kiểm được" — mà hai thứ đó khác hẳn nhau.
        print(f"   ⏭️ {ten_kenh}: KHÔNG chấm được hook ({str(e)[:70]}) — cho qua, "
              f"video này CHƯA được soi khung mở đầu")
        return True, {"note": f"hook-qc-skip: {str(e)[:60]}"}
    if not ok:
        print(f"   🖼️ {ten_kenh}: HOOK trượt QC thị giác — {tin.get('hook_score')}đ · "
              f"{'; '.join(tin.get('issues') or [])[:110]}")
    elif tin.get("hook_score"):
        print(f"   🖼️ {ten_kenh}: hook {tin['hook_score']}đ")
    return ok, tin


def chay_chung(kenh: dict, ra: str = "", ky: dict | None = None,
               avoid: list | None = None, st_san: dict | None = None,
               ky_hieu: str = "", keys: list | None = None) -> tuple[str, dict] | None:
    """Dựng + render cho MỌI dạng. Trả (đường dẫn, QC) hoặc None nếu bỏ lượt.

    `avoid` = tiêu đề các video kênh này ĐÃ làm. Thiếu nó thì kênh lặp lại đúng một câu chuyện
    mãi mãi — xem khối XOAY VÒNG ĐỀ TÀI ở trên."""
    import datastory_ci as DS
    dang = kenh.get("dinh_dang")
    # 26/8 — PHẢI CHUYỂN TIẾP `st_san`/`ky_hieu`. Thiếu thì `chay_bo` chọn chương xong, hai
    # đường riêng này lại TỰ CHỌN LẠI chuyện khác, và mọi chương ghi đè nhau vì cùng slug —
    # đúng hai cái bẫy đã vá cho 5 dạng kia, chỉ khác chỗ.
    if dang == "race":
        return chay_race(kenh, ra, ky, st_san=st_san, ky_hieu=ky_hieu, keys=keys)
    if dang == "cinematic":
        return chay_phim(kenh, ra, ky, keys=keys, st_san=st_san, ky_hieu=ky_hieu)
    comp, ten_props = DUONG_RA.get(dang, (None, None))
    if not comp or not ten_props:
        print(f"   ⚠️ {kenh.get('ten')}: dạng '{dang}' chưa có đường render chung")
        return None
    # Bố cục riêng của kênh (xem `BO_CUC_KENH`). Ba composition dùng CHUNG một bộ props, nên đổi
    # composition không phải đổi dữ liệu — đúng chỗ để tách bộ mặt mà không đụng đường dựng.
    comp = bo_cuc_cua(kenh, dang)
    # `st_san` = chương ĐÃ CHỌN sẵn (dùng khi dựng BỘ). 26/8 — bản đầu của `chay_bo` chọn chương
    # rồi vẫn gọi `chay_chung` để nó TỰ CHỌN LẠI: hai bên chọn độc lập nên video render ra không
    # phải chương đã ghi sổ, và `avoid` lệch một nhịp khiến chương 2 trùng chương 1 rồi cả bộ
    # dừng ở 1 chương. Đo thật: long 38,3s = đúng một short, không phải ba.
    st = st_san or _dung_story_xoay(dang, kenh, ky, avoid)
    if not st:
        return None
    _dp = dung_props(kenh, st, dang, ten_props, ky_hieu, keys)
    if not _dp:
        return None
    props, pf, sl = _dp
    ra = os.path.abspath(ra or os.path.join(GOC, "out", f"th2_{dang}_{sl}.mp4"))
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    DS.run_render_cmd(["npx", "remotion", "render", "src/index.ts", comp, ra,
                       f"--props=./{os.path.relpath(pf, DS.ENG)}", "--gl=swiftshader", "--jpeg-quality=100", "--crf=15",
                       "--concurrency=2", "--log=error"],
                      cwd=DS.ENG, timeout=2400, label=f"{comp}({kenh['ten']})")
    ok, info = DS.qc(ra)
    print(f"{'✅' if ok else '❌'} {kenh['ten']} [{dang}] · {info}")
    if ok:
        chuan_am(ra)          # đưa về -14 LUFS trước mọi khâu sau (xem `chuan_am`)
        _hok, _htin = qc_hook_sau_render(ra, kenh.get("ten", ""), keys)
        if isinstance(info, dict):
            info.update(_htin)
        if not _hok:
            return None                  # hook hỏng = video hỏng, đừng đẩy lên kho
        lam_thumb(kenh, st, ra, comp, pf)
    # Gửi kèm props để `chay_bo` ghép long mà KHÔNG phải dựng lại (dựng lại = gọi TTS lần nữa,
    # ra tệp tiếng khác, long lệch tiếng khỏi short cùng chương).
    if isinstance(info, dict):
        info["_props_obj"] = props
    return (ra, info) if ok else None



# Mã trục xoay -> chữ cho NGƯỜI XEM. Chỉ liệt kê mã không phải tiếng Anh; mã vốn đã là tiếng Anh
# (retriever, caffeine, harbor…) tự đi qua lưới viết hoa bên dưới.
# Nhãn phải nói ĐÚNG lát dữ liệu, không phải dịch từ điển: "chet_yeu" của GAME GRAVEYARD là game
# ra mắt rồi chết ngay, nên "Dead on arrival" đúng hơn "Died young".
_NHAN_TRUC = {
    # 28/8 — bốn mã lọc mới của STEAM TRUTH. Bản dịch cố ý CHỌN CHỮ ĐÃ CÓ SẴN trong tiêu đề của
    # chính lát đó ("Free games beating…", "Cheap games pulling…"). `_gan_truc_vao_tieu_de` bỏ qua
    # khi giá trị đã nằm trong tiêu đề, nên không lát nào bị bồi thêm một cái đuôi thừa — mà chốt
    # kiểm vẫn có bản dịch để đối chiếu, và mã nội bộ vẫn không có đường nào lọt lên màn hình.
    "mien_phi":  "Free",
    "tra_tien":  "Paid",
    "dat_tien":  "Sixty-dollar",
    "re_tien":   "Cheap",
    "ban_chay":  "Best sellers",
    "dinh_cao":  "Peak players",
    "dong_nhat":  "Most played",
    "tang_manh": "Biggest gainers",
    "chet_yeu":  "Dead on arrival",
    "vang_nhat_": "Emptiest",          # giữ khoá cũ khỏi vỡ nếu còn chỗ nào tra
    "dat_bo":    "Sixty-dollar",       # trùng chữ đã có trong tiêu đề -> không bị bồi đuôi
    "tut_manh":  "Biggest drops",
    "vang_nhat": "Emptiest servers",
    "bo_hoang":  "Abandoned",
}


_NHAC_CO = None


def _nhac_co_that(duong: str, ten_kenh: str = "") -> str:
    """Chỉ trả bản nhạc CÓ THẬT trong gói render; thiếu thì lùi về bản có, không để render chết.

    27/8 — đây là thứ giết nhiều video nhất trong phiên 15:30, và nó không hề trông giống lỗi:
        Error while downloading .../music/km_long_note_four.mp3: 404
        -> `npx remotion render` thoát khác 0 -> "bộ gen-2 lỗi" -> mất cả long lẫn 3 short.
    Nguyên nhân: `.gitignore` chặn `engine-remotion/public/**`, nên chỉ 6/18 bản nhạc từng được
    thêm ép vào git. Máy làm việc có đủ 18 -> chạy thử ở nhà thì đẹp; CI chỉ có 6 -> **29/50 kênh**
    được gán một bản không tồn tại và hỏng ngay từ lệnh render.
    Đây là lớp lỗi "chạy được ở máy tôi": không sai một dòng mã nào, sai ở chỗ TÀI SẢN không đi
    cùng mã.
    Một bản nhạc thiếu không đáng để mất một video 7 phút đã dựng xong. Lùi về bản có thật —
    chọn theo băm tên kênh nên vẫn rải đều, và kênh nào cũng có nhạc.
    """
    import os as _o
    global _NHAC_CO
    kho = _o.path.join(GOC, "..", "engine-remotion", "public", "music")
    if _NHAC_CO is None:
        try:
            _NHAC_CO = sorted(f for f in _o.listdir(kho) if f.endswith(".mp3") and not f.startswith("sfx_"))
        except Exception:
            _NHAC_CO = []
    if not duong:
        return ""
    ten = _o.path.basename(str(duong))
    if _o.path.exists(_o.path.join(kho, ten)):
        return duong
    if not _NHAC_CO:
        print(f"   ⚠️ {ten_kenh}: kho nhạc rỗng — bỏ nhạc nền (video vẫn ra, chỉ không có nhạc)")
        return ""
    import hashlib as _h
    thay = _NHAC_CO[int(_h.md5(str(ten_kenh).encode()).hexdigest(), 16) % len(_NHAC_CO)]
    print(f"   🎵 {ten_kenh}: thiếu `{ten}` trong gói render — dùng `{thay}` thay thế")
    return "music/" + thay


def _gan_truc_vao_tieu_de(tieu_de: str, truc: str, val) -> str:
    """Nhét GIÁ TRỊ TRỤC XOAY vào tiêu đề, nếu nó chưa có mặt ở đó.

    26/8 — đo thật trên RECALL PLATE (openFDA): xoay `nam` 2025→2020 cho ra SÁU bộ dữ liệu khác
    nhau nhưng `title` y hệt `"Food recalls you probably missed"` cả sáu lần. Khâu chống trùng so
    bằng tiêu đề nên coi cả sáu là "đã làm rồi" ⇒ bộ 1 long + 3 short co lại còn 1 chương, và
    nguy hơn: kênh đăng đúng MỘT video rồi câm vĩnh viễn, log chỉ ghi "hết kho đề tài" nên nhìn
    như kho cạn chứ không như lỗi.

    Xoay trục mà tiêu đề không đổi thì bản thân nó cũng đã sai với người xem: hai video khác năm
    mà cùng một tên là trùng lặp trên trang kênh. Nên chữa ở tiêu đề là chữa cả hai chuyện."""
    t = str(tieu_de or "").strip()
    if not t or not truc or val in (None, ""):
        return t
    # 27/8 — GIÁ TRỊ TRỤC CÓ THỂ LÀ MỘT DANH SÁCH.
    # Xem khung thật kênh WHERE TO MOVE: trên màn hình in nguyên văn
    #     Home price by state — ['Florida', 'New York', 'Pennsylvania', 'Illinois', 'Ohio', 'Georgia']
    # Đây là lỗi của hàm này: trục `bangs` mang một list, `str(val)` cho ra `repr` của Python và
    # nó đi thẳng lên tiêu đề video. Người xem nhìn thấy dấu ngoặc vuông và dấu nháy — trông như
    # phần mềm hỏng, và nó phá luôn tiêu đề của cả kênh.
    # Danh sách thì gọi tên hai phần tử đầu rồi đếm phần còn lại: vừa đọc được, vừa vẫn phân biệt
    # được các lượt xoay khác nhau (điều mà hàm này sinh ra để làm).
    if isinstance(val, (list, tuple, set)):
        xs = [str(x).strip() for x in val if str(x).strip()]
        if not xs:
            return t
        v = xs[0] if len(xs) == 1 else (f"{xs[0]} vs {xs[1]}" if len(xs) == 2
                                        else f"{xs[0]}, {xs[1]} and {len(xs) - 2} more")
    else:
        v = str(val)
    # So bằng ĐUÔI tên trục: đo thật 50 kênh thấy trục năm/ngày xuất hiện dưới nhiều tên
    # (`nam`, `tu_nam`, `ngay`, `tu_ngay`). Khớp cứng "nam"/"ngay" thì 4 kênh ra tiêu đề kiểu
    # "… — 2024" thay vì "… (2024)" — vẫn phân biệt được nhưng đọc như lỗi máy.
    if truc == "lui":
        # 27/8 — trục `lui` là SỐ NGÀY LÙI. Ghép trần vào tiêu đề thì ra "— 3", "— 30": vô nghĩa
        # với người xem, và tệ hơn là KHÔNG PHÂN BIỆT ĐƯỢC nếu nguồn trả cùng một nhan đề chung
        # (đo thật: AMERICA LOOKED UP ra "Most-read on Wikipedia" cho cả ngày lùi 3 lẫn lùi 30).
        # Đổi thành NGÀY THẬT: vừa đọc được, vừa là khoá chống trùng đúng nghĩa.
        import datetime as _dt2
        try:
            _n = _dt2.date.today() - _dt2.timedelta(days=int(val))
            _nh = _n.strftime("%b %-d, %Y")
        except Exception:
            return t
        return t if _nh in t else f"{t} — {_nh}"
    if truc.endswith("ngay"):
        # 27/8 — trục đuôi "ngay" mang HAI loại giá trị khác hẳn nhau, mà bản cũ gộp làm một:
        #   • SỐ ngày  (`ngay = 7`)          -> "… — last 7 days"        ✔
        #   • MỘT NGÀY (`den_ngay` = ISO)    -> "… — last 2026-08-20 days"  ✘ vô nghĩa
        # Kênh NEAR EARTH xoay đúng trục `den_ngay`, nên mọi tiêu đề của nó đều dính câu đó.
        import re as _re
        if _re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            return t if v in t else f"{t} — week ending {v}"
        return t if f"{v} day" in t.lower() else f"{t} — last {v} days"
    # 27/8 — MÃ NỘI BỘ KHÔNG BAO GIỜ ĐƯỢC LÊN TIÊU ĐỀ.
    #
    # Đọc tiêu đề thật của GAME GRAVEYARD trong phiên 12:14:
    #     "Games people actually play right now — tut_manh"
    #     "Games millions bought and nobody plays — chet_yeu"
    # `tut_manh` / `chet_yeu` là giá trị trục xoay — mã tiếng Việt viết cho MÌNH đọc, không phải
    # cho khán giả Mỹ. Nhánh cuối `f"{t} — {v}"` ném thẳng nó lên tiêu đề video.
    # Người xem Mỹ nhìn thấy một chuỗi gạch dưới không đọc được là biết ngay video do máy đẻ ra —
    # và đó là ấn tượng đầu tiên, ngay trên trang kênh, trước cả khi họ bấm vào.
    # Cùng họ với lỗi `— ['Florida', 'New York', ...]` vá hôm qua: cả hai đều là DỮ LIỆU NỘI BỘ
    # rò ra mặt tiền, chỉ khác kiểu.
    #
    # Chữa hai tầng, vì hai tầng chặn hai chuyện khác nhau:
    #   1. bảng dịch cho các mã đang dùng -> tiêu đề vừa đọc được vừa NÓI ĐÚNG lát dữ liệu;
    #   2. lưới chung cho mã thêm sau -> gạch dưới thành khoảng trắng, viết hoa; còn dấu tiếng
    #      Việt thì THÀ BỎ HẲN còn hơn để lọt, vì một tiêu đề kém phân biệt vẫn hơn một tiêu đề
    #      lộ ruột gan hệ thống.
    # LUẬT: giá trị CÓ GẠCH DƯỚI là mã nội bộ (`tut_manh`, `chet_yeu`) — chưa có bản dịch thì
    # KHÔNG được lên tiêu đề. Bỏ gạch dưới rồi thả lên ("Tut manh") không cứu được gì: với người
    # xem Mỹ nó vẫn là rác, chỉ là rác không còn dấu hiệu để chốt kiểm bắt. Thà tiêu đề kém phân
    # biệt còn hơn tiêu đề lộ ruột gan hệ thống.
    # Giá trị MỘT TỪ (retriever, caffeine, harbor) vốn đã là tiếng Anh -> đi thẳng, chỉ hoa chữ đầu.
    _tho = v
    v = _NHAN_TRUC.get(v.lower(), v)
    if v is _tho and "_" in _tho:
        return t
    # So sau khi CHUẨN HOÁ gạch nối/gạch dưới: giá trị trục là slug của nguồn ("ice-creams"),
    # còn tiêu đề viết chữ người đọc ("Ice Creams"). So thô thì hai bên không khớp và hậu tố bị
    # dán thêm — ra "Ice Creams: what is really in it — Ice-creams", lặp đúng một chữ hai lần.
    _sosanh = lambda x: " ".join(str(x).lower().replace("-", " ").replace("_", " ").split())
    if _sosanh(v) in _sosanh(t):
        return t
    if any(ord(c) > 127 for c in v):
        return t                                   # thà không phân biệt còn hơn lộ mã
    # Chỉ hoa CHỮ ĐẦU. Hoa từng từ thì ra "Dead On Arrival" / "Florida, New York And 1 More" —
    # tiếng Anh không viết hoa giới từ và liên từ giữa câu, và sai chỗ đó đọc ra ngay là máy làm.
    v = " ".join(v.replace("_", " ").split())
    v = (v[:1].upper() + v[1:]) if v else v
    return f"{t} ({v})" if truc.endswith("nam") else f"{t} — {v}"


def _tieu_de_tu_du_lieu(st: dict, kenh: dict) -> str:
    """Dựng tiêu đề TỪ CHÍNH CHỦ THỂ ĐỨNG ĐẦU BẢNG, thay cho khuôn cố định + ngày.

    27/8 — đọc 11 tiêu đề thật của AMERICA LOOKED UP trong một phiên:
        Most-read on Wikipedia — Aug 24, 2026
        Most-read on Wikipedia — Aug 19, 2026
        Most-read on Wikipedia — Aug 12, 2026
        Most-read on Wikipedia — Dec 30, 2025
    Mười một video chỉ khác nhau con số ngày. Hai cái hỏng cùng lúc:
      • với NGƯỜI XEM: trang kênh trông như một cỗ máy nhả hàng loạt, và không tiêu đề nào nói cho
        họ biết bên trong có gì đáng xem — cái duy nhất phân biệt lại là thứ họ không quan tâm;
      • với YOUTUBE: đây đúng khuôn "nội dung lặp lại, sản xuất hàng loạt" bị hạn chế phân phối.

    Gốc: khuôn tiêu đề mô tả CÁCH LÀM ("most-read on Wikipedia") chứ không mô tả NỘI DUNG. Mà nội
    dung thì mỗi lượt một khác — chỉ là không ai đưa nó lên tiêu đề.

    Nên lấy chính thứ đứng đầu bảng làm chủ ngữ. Mười một lượt là mười một cái tên khác nhau, nên
    hết trùng MỘT CÁCH TỰ NHIÊN — không phải nhờ dán thêm hậu tố cho khác đi. Và người xem đọc
    tiêu đề là biết ngay bên trong nói về ai.

    Khuôn CỐ ĐỊNH THEO KÊNH (băm từ tên kênh) chứ không đổi theo từng video: một kênh nên có một
    giọng nhất quán. Đổi khuôn mỗi video chỉ là biến hoá bề mặt, mà lại làm kênh trông thiếu chủ đích.

    Trả "" khi không dựng được — lúc đó đường lui (khuôn + ngày) vẫn còn nguyên."""
    # Lớp lưới thứ hai: đây là hàm LÀM ĐẸP TIÊU ĐỀ. Nó không được phép giết một video đã dựng
    # xong vì một hình dạng dữ liệu lạ. Hỏng thì trả "" và rơi về khuôn cũ — mất một tiêu đề hay,
    # giữ được cả bộ video.
    try:
        d = _so_noi_bat(st or {})
    except Exception as e:
        print(f"   ⚠️ {kenh.get('ten', '?')}: không dựng được tiêu đề theo dữ liệu ({str(e)[:60]}) "
              f"— dùng khuôn cũ")
        return ""
    ten = " ".join(str(d.get("name") or "").split())
    so = " ".join(str(d.get("stat") or "").split())
    khung = " ".join(str((st or {}).get("title") or "").split())
    if len(ten) < 2 or not khung:
        return ""
    # Chủ thể cũng phải là chữ cho người đọc — cùng luật với `_gan_truc_vao_tieu_de`. Tên lấy từ
    # nguồn nên gần như luôn sạch, nhưng "gần như" không phải là một bảo đảm.
    if "_" in ten or any(ord(c) > 127 for c in ten):
        return ""
    # 28/8 — CHỦ THỂ PHẢI LÀ MỘT CÁI TÊN, KHÔNG PHẢI MỘT CÂU.
    # `_so_noi_bat` lấy `hook` khi story không có bảng mục (đúng với dạng cinematic), mà `hook` là
    # một câu dẫn. Kết quả đo thật trên ba kênh hồ sơ toà:
    #     "A 2026 case almost nobody read. — Ex Parte Randy Louis Dupree v. the State"
    #     "A 2026 case almost nobody read. — United States v. William Boylston"
    #     "A 2026 case almost nobody read. — Order on Motion - Aldin Associates Ltd."
    # Ba kênh KHÁC NHAU mở đầu bằng ĐÚNG một câu. Hàm này sinh ra để diệt tiêu đề hàng loạt, mà
    # đang tự dựng thêm một khuôn hàng loạt mới — và nó còn đẩy cái tên thật (thứ duy nhất phân
    # biệt) ra sau, đúng chỗ YouTube cắt.
    # Tên riêng thì ngắn, không có dấu chấm cuối, không mở đầu bằng mạo từ.
    if ten.endswith(".") or len(ten.split()) > 5 or ten.split()[0].lower() in ("a", "an", "the"):
        return ""
    # 28/8 — CHỦ THỂ KHÔNG ĐƯỢC LÀ MỘT CÁI MỐC THỜI GIAN.
    # Anh gửi khung FAME CURVE:
    #     "07/08: 25.7K — Spider-Man: Brand New Day: the spike — Aug 6, 2026"
    # Ba mảnh, mở đầu bằng "07/08" — đó là NHÃN TRỤC NGANG của biểu đồ, không phải chủ thể. Dạng
    # `longshot` để nhãn ở khoá `label`, mà với kênh này `label` là ngày; `_so_noi_bat` đọc đúng
    # khoá ấy và trả về một cái ngày làm "tên".
    # Hậu quả nặng gấp đôi bình thường: tên thật (Spider-Man) bị đẩy xuống giữa, đúng chỗ YouTube
    # cắt, nên trên trang tìm kiếm người xem chỉ đọc được "07/08: 25.7K".
    # Ngày tháng thì không bao giờ là chủ ngữ của một câu tiêu đề.
    # NGOẠI LỆ: một NĂM đứng riêng vẫn là chủ thể hợp lệ. "2024: 299.7 — Education cost by year"
    # đọc trôi và nói đúng thứ nó nói; cái hỏng là mốc NGÀY ("07/08", "Aug 6"), vì ngày là toạ độ
    # trên trục chứ không phải nhân vật của câu chuyện.
    import re as _re
    _t = ten.strip()
    _la_nam = bool(_re.fullmatch(r"(?:19|20)\d{2}", _t))
    if not _la_nam and (
            _re.fullmatch(r"[\d\s/.,:-]+", _t)
            or _re.match(r"^(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\.?\s+\d",
                         _t, _re.I)
            or len([c for c in _t if c.isalpha()]) < 3):
        return ""
    # Tên đã nằm sẵn trong khung thì ghép vào chỉ tổ lặp chữ ("Spider-Man — Spider-Man: the spike").
    if ten.lower() in khung.lower():
        return ""
    # 28/8 — KHUNG ĐÃ CÓ SỐ THÌ KHÔNG ĐƯỢC GẮN SỐ THỨ HAI.
    # Khung thật của SKY RIGHT NOW là "200 planes are over California right now" (nguồn sống nên
    # con số nằm sẵn trong tên). Ghép tiếp chủ thể + số ra:
    #     "United States: 192 — 200 planes are over California right now"
    # Hai con số khác nhau đứng cạnh nhau trong một tiêu đề, không con nào giải thích con nào —
    # người xem đọc xong không biết 192 là gì, 200 là gì, và tưởng mình đọc nhầm. Đây là lỗi NẶNG
    # hơn tiêu đề trùng: trùng thì nhàm, còn cái này thì SAI.
    # Khung có số nghĩa là nó ĐÃ tự phân biệt và đã có hook — không cần bồi thêm.
    _khung_co_so = any(c.isdigit() for c in khung)
    import hashlib as _h
    kieu = int(_h.md5(str(kenh.get("ten") or "").encode()).hexdigest(), 16) % 2
    if so and not _khung_co_so:
        t = f"{ten}: {so} — {khung}" if kieu == 0 else f"{khung} — {ten}, {so}"
    elif _khung_co_so:
        return ""                                  # khung tự đứng được, giữ nguyên
    else:
        t = f"{ten} — {khung}"
    # YouTube cắt tiêu đề quanh mốc 60-70 ký tự trong kết quả tìm; 95 là trần an toàn để phần
    # QUAN TRỌNG NHẤT (chủ thể + số, đứng đầu) không bao giờ bị cắt mất.
    return t[:95].rstrip(" —-,:")


def _van_tay_du_lieu(st: dict) -> frozenset:
    """Dấu vân tay theo DỮ LIỆU, không theo tiêu đề.

    26/8 — `quality_gate.too_similar` (dùng cho gen-1) so bằng tiêu đề, và đo thật thì nó GIẾT 5/6
    chương của một bộ: sáu tiêu đề chỉ khác nhau con số năm, mà dấu vân tay bỏ chữ số ⇒ trùng 1.00.
    Nối thẳng vào là phá đúng cơ chế xoay vòng.

    Với gen-2 thì tiêu đề GIỐNG NHAU là ĐÚNG THIẾT KẾ — một khuôn, nhiều lát dữ liệu. Thứ phải khác
    nhau là DỮ LIỆU. Nên vân tay lấy từ tên các mục, và trùng nghĩa là "cùng một bảng số", không
    phải "cùng một cách đặt tên"."""
    ten = []
    for khoa in ("items", "data", "pairs"):
        for x in (st.get(khoa) or [])[:12]:
            if isinstance(x, dict):
                v = x.get("name") or x.get("label") or x.get("state") or x.get("ten") or ""
                if v:
                    ten.append(str(v).strip().lower())
    for fr in (st.get("frames") or [])[:3]:
        for x in (fr.get("data") or [])[:8]:
            if isinstance(x, dict) and x.get("name"):
                ten.append(str(x["name"]).strip().lower())
    return frozenset(ten)


def _trung_du_lieu(st: dict, da: list, tran: float = 0.8) -> float:
    """Mức trùng cao nhất giữa dữ liệu của `st` và các chương đã nhận. 0 = mới hoàn toàn."""
    a = _van_tay_du_lieu(st)
    if len(a) < 3:
        return 0.0                      # quá ít mục để kết luận -> không chặn oan
    cao = 0.0
    for b in da:
        if not b:
            continue
        chung = len(a & b)
        cao = max(cao, chung / max(1, len(a | b)))
    return round(cao, 2)


def cong_chat_luong(st: dict, kenh: dict) -> list:
    """CỔNG CHẤT LƯỢNG KỊCH BẢN cho gen-2. Trả list lỗi (rỗng = đạt).

    KHÔNG dùng `quality_gate.money_safe` nguyên bản: nó đòi `sources >= 2`, chuẩn hợp lý cho bài do
    AI viết (cần đối chứng), nhưng gen-2 dựng từ MỘT nguồn gốc có thẩm quyền — openFDA chính là cơ
    quan công bố, không phải nguồn thứ cấp. Đo thật: yêu cầu đó loại 100% story gen-2.

    Giữ lại hai phép kiểm thật sự có ý nghĩa (có số, không có câu chữ rủi ro chính sách) và thêm ba
    phép hợp với gen-2."""
    import quality_gate as Q
    loi = []
    chu = " ".join(str(v) for v in st.values() if isinstance(v, str))
    if not st.get("nguon"):
        loi.append("không ghi nguồn dữ liệu")
    if not any(c.isdigit() for c in chu):
        loi.append("không có con số nào — video dữ liệu mà không có số thì không có gì để xem")
    import re as _r
    xau = _r.findall(r"\b(guaranteed returns?|get rich|cure[sd]? cancer|miracle cure|buy now|"
                     r"click here|100% profit|risk[- ]free money)\b", chu, _r.I)
    if xau:
        loi.append("câu chữ rủi ro chính sách: " + ", ".join(sorted(set(x.lower() for x in xau))[:3]))
    n = sum(len(st.get(k) or []) for k in ("items", "data", "pairs", "frames"))
    if n < 3:
        loi.append(f"chỉ {n} mục dữ liệu — quá mỏng để dựng")
    return loi


_NHU_CAU_DEM: dict = {}      # (kênh, trục) -> thứ tự đã xếp; đo một lần rồi dùng lại cả phiên


def _goc_doc(v) -> str:
    """Giá trị trục ở dạng ĐỌC ĐƯỢC cho log — danh sách thì gọi tên, không in `repr` Python.

    27/8 — log thật in ra `đầu bảng ['Texas', 'Oklahoma', 'Kansas', ...]`. Dấu ngoặc vuông và dấu
    nháy là cú pháp của Python, không phải thứ để người đọc log nhìn; và nó khiến em tưởng chính
    truy vấn cũng dùng chuỗi đó (không phải). Log nói sai làm mất thời gian đúng bằng lỗi thật."""
    if isinstance(v, (list, tuple)):
        xs = [str(x) for x in v if str(x).strip()]
        return xs[0] + (f" +{len(xs) - 1}" if len(xs) > 1 else "") if xs else ""
    return str(v)


def _xep_theo_nhu_cau(kenh: dict, truc: str, kho: list) -> list:
    """Xếp kho đề tài theo NHU CẦU THẬT của người xem, cao nhất lên trước.

    27/8 — anh hỏi đúng chỗ đau: "kịch bản dựa trên phân tích trending hay chỉ làm theo dữ liệu
    kho sẵn, có khi nào làm ra mà chủ đề không còn ai quan tâm?"
    Đo thì đúng là vế sau: `radar_dethai.py` đã viết xong từ hôm trước nhưng KHÔNG MỘT CHỖ NÀO
    trong đường chạy gọi nó — chỉ selftest import. Kho đề tài được duyệt theo THỨ TỰ KHAI TRONG
    JSON, tức thứ tự em gõ tay, hoàn toàn không liên quan tới việc có ai tìm hay không.
    Hậu quả cụ thể: kênh CAR RECALL luôn bắt đầu bằng `ford` vì `ford` đứng đầu danh sách, chứ
    không phải vì tháng này người ta đang tra về Ford.

    Tín hiệu dùng: GỢI Ý TÌM KIẾM CỦA YOUTUBE (`radar_dethai.diem_nhu_cau`). Đây là thứ tốt nhất
    lấy được miễn phí và không cần khoá — nó nói thẳng người ta đang gõ gì vào ô tìm kiếm. Và nó
    hỏi theo GÓC của kênh chứ không hỏi danh từ trần: đo thật cho thấy "peanut butter recall" ra
    8 gợi ý còn "breakfast cereal recall" ra 0 — tức người ta tìm thu hồi bơ đậu phộng, không ai
    tìm thu hồi ngũ cốc ăn sáng. Hỏi trần thì cả hai đều ra 10 gợi ý, phẳng lì, vô dụng.

    FAIL-OPEN tuyệt đối: radar hỏng, mạng chặn, hết giờ — trả nguyên thứ tự cũ. Đây là lớp làm
    CHO TỐT HƠN, không được phép trở thành chỗ chết mới.
    """
    try:
        kh = (str(kenh.get("ten", "")), str(truc))
        if kh in _NHU_CAU_DEM:
            return _NHU_CAU_DEM[kh]
        import radar_dethai as R
        goc = R.goc_kenh(kenh) or ""
        niche_tu = R._tu(kenh.get("niche", "")) | R._tu(kenh.get("goc_nhin", ""))
        cham = []
        for i, v in enumerate(kho):
            # 27/8 — TRỤC DANH SÁCH: HỎI PHẦN TỬ ĐẦU, ĐỪNG HỎI CẢ CHUỖI GHÉP.
            # Bản cũ ghép cả danh sách thành một câu rồi đem đi hỏi gợi ý tìm kiếm:
            #     "Texas, Oklahoma, Kansas, Nebraska, Iowa, Missouri"
            # Không một người dùng nào gõ câu đó vào ô tìm kiếm, nên YouTube trả về gần như không
            # gì — điểm nhận được là NHIỄU, mà nhiễu thì còn tệ hơn không đo: nó xếp lại thứ tự
            # kho bằng một con số vô nghĩa và trông y như đã đo thật.
            # Phần tử đầu là thứ đại diện được và CÓ người tìm ("Texas") -> điểm nói đúng nhu cầu
            # của cụm đó. Đo bằng một tín hiệu thật còn hơn đo bằng sáu tín hiệu trộn thành vô nghĩa.
            cum = str(v[0]) if (isinstance(v, (list, tuple)) and v) else str(v)
            # Kho đề tài lưu dạng SLUG cho khớp API nguồn (`breakfast-cereals`, `cpi_nha`). Hỏi
            # gợi ý bằng slug thì không bao giờ ra kết quả — không ai gõ dấu gạch vào ô tìm kiếm.
            # Đo được: 22 đề tài của WHAT IS IN IT đều ra điểm 0 cho tới khi bỏ dấu gạch.
            cum = cum.replace("-", " ").replace("_", " ").strip()
            # Trục là NĂM/NGÀY thì gợi ý tìm kiếm không nói được gì (không ai gõ "2019" vào ô
            # tìm kiếm để tìm chủ đề) -> giữ nguyên thứ tự, khỏi tốn lượt gọi mạng.
            if cum.strip().isdigit() or "-" in cum[:5]:
                return kho
            try:
                d, _ = R.diem_nhu_cau(cum, niche_tu, goc)
            except Exception:
                d = 0.0
            cham.append((-float(d or 0), i, v))
        cham.sort()
        ra = [v for _, _, v in cham]
        top = cham[0]
        if -top[0] > 0:
            print(f"   🎯 {kenh.get('ten')}: xếp {len(ra)} đề tài theo NHU CẦU THẬT "
                  f"(đầu bảng `{_goc_doc(ra[0])}`, điểm {-top[0]:.1f}) — không phải theo thứ tự khai.")
        _NHU_CAU_DEM[kh] = ra
        return ra
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        print(f"   ⚠️ không đo được nhu cầu ({str(e)[:60]}) — giữ thứ tự kho như cũ")
        return kho


def _cat_cau_dai(cau: str, tran: int = 20) -> list:   # cùng ngưỡng với nghiem_thu.TRAN_TU
    """Tách một câu quá dài thành hai, CẮT Ở RANH GIỚI MỆNH ĐỀ chứ không cắt theo số từ.

    29/8 — chấm 50 kênh thì 16 kênh còn hỏng vì đúng một lỗi: một câu 19-23 từ. Với giọng đọc
    ~2,5 từ/giây thì 22 từ là gần 9 giây cho MỘT câu — trên feed dọc, ngón tay đã lướt từ lâu.
    Cắt theo số từ thì câu vỡ giữa chừng ("Only 1,240 people still" / "play it tonight"), nghe còn
    tệ hơn câu dài. Dấu phẩy và các liên từ chính là chỗ tác giả đã đánh dấu sẵn ranh giới ý —
    cắt ở đó thì hai câu đều đứng được một mình.
    Không tìm được chỗ cắt hợp lý thì TRẢ NGUYÊN: thà một câu dài còn hơn hai mảnh vụn."""
    import re as _re
    t = " ".join(str(cau or "").split())
    if len(t.split()) <= tran:
        return [t] if t else []
    # Ưu tiên: dấu phẩy/chấm phẩy -> liên từ. Chọn chỗ gần GIỮA câu nhất để hai nửa cân nhau.
    ung = [m.end() for m in _re.finditer(r",\s|;\s", t)]
    ung += [m.start() for m in _re.finditer(r"\s(?:and|but|while|because|so that|which)\s", t)]
    if not ung:
        return [t]
    giua = len(t) / 2
    cat = min(ung, key=lambda i: abs(i - giua))
    a, b = t[:cat].strip(" ,;"), t[cat:].strip(" ,;")
    if len(a.split()) < 4 or len(b.split()) < 4:
        return [t]                       # cắt ra một mảnh quá ngắn -> không cắt còn hơn
    a = a if a.endswith((".", "!", "?")) else a + "."
    b = (b[:1].upper() + b[1:]) if b else b
    b = b if b.endswith((".", "!", "?")) else b + "."
    return [a, b]


def hoan_kich_ban(st: dict, kenh: dict) -> dict:
    """Đảm bảo CÂU ĐẦU của lời đọc là một HOOK, không phải một câu mô tả.

    29/8 — thêm phép chấm kịch bản rồi đo lại 50 kênh: **40 kênh mở đầu bằng câu mô tả**.
        "Six seasons of points leaders."
        "Frozen pizza, by calories. Same scale, no tricks."
        "Dog breeds ranked by how many people quietly looked them up this month."
    Không câu nào sai. Nhưng không câu nào cho người xem một LÝ DO để ở lại giây thứ hai — chúng
    giới thiệu chủ đề, đúng cách viết của video giảng bài dài, sai hẳn với feed dọc nơi ngón tay
    đã sẵn sàng lướt. Và bảng điểm cũ chấm cả 40 kênh này 100/100, vì nó chưa từng chạm tới lời đọc.

    Cách chữa KHÔNG phải viết lại 25 bộ dựng: con số gây choáng vốn đã nằm sẵn trong dữ liệu, chỉ
    là nó bị chôn ở câu thứ ba. Đưa nó lên trước, giữ nguyên câu mô tả làm câu thứ hai — người xem
    nhận con số trước, rồi mới nhận bối cảnh. Đó đúng là trật tự của mọi short giữ được chân người.

    Khuôn hook CỐ ĐỊNH THEO KÊNH (băm từ tên): một kênh nên có một giọng mở nhất quán, còn 50 kênh
    thì không được mở giống nhau."""
    try:
        # MỖI DẠNG CẤT LỜI MỞ Ở MỘT KHOÁ KHÁC. Bản đầu của hàm này chỉ đọc `narration` và vá
        # xong vẫn còn 33 kênh hỏng y nguyên — vì `ranked`/`scaled`/`longshot`/`thennow` để câu
        # mở ở `intro_vo`, còn `cinematic` để ở `scenes[0].nar`. Sửa một khoá rồi tưởng xong là
        # đúng cách vá theo triệu chứng: cùng một lỗi, sáu chỗ, vá một chỗ.
        if st.get("narration"):
            kho, lay = "narration", lambda: [str(x).strip() for x in st["narration"] if str(x).strip()]
        elif str(st.get("intro_vo") or "").strip():
            kho, lay = "intro_vo", lambda: [str(st["intro_vo"]).strip()]
        elif (st.get("scenes") or [{}])[0].get("nar"):
            kho, lay = "scenes", lambda: [str(st["scenes"][0].get("nar") or "").strip()]
        else:
            return st
        dan = lay()
        if not dan:
            return st
        dau = dan[0]
        # Đã có số hoặc đã là câu hỏi -> tự nó đã hook, không đụng vào.
        if any(c.isdigit() for c in dau) or dau.rstrip().endswith("?"):
            return st
        d = _so_noi_bat(st or {})
        so = " ".join(str(d.get("stat") or "").split())
        ten = " ".join(str(d.get("name") or "").split())
        if not so or not any(c.isdigit() for c in so):
            return st
        # Chủ thể phải là chữ đọc được — cùng luật với tiêu đề (xem `_tieu_de_tu_du_lieu`).
        if "_" in ten or any(ord(c) > 127 for c in ten) or len(ten) < 2:
            ten = ""
        import hashlib as _h
        kieu = int(_h.md5(str(kenh.get("ten") or "").encode()).hexdigest(), 16) % 3
        if ten:
            hook = (f"{so}. That is {ten}." if kieu == 0
                    else f"{ten}: {so}." if kieu == 1
                    else f"Start with this: {so}, {ten}.")
        else:
            hook = f"{so}. That is where this starts."
        if hook.strip().lower() == dau.strip().lower():
            return st
        if kho == "narration":
            st["narration"] = [hook] + dan
        elif kho == "intro_vo":
            st["intro_vo"] = f"{hook} {dau}".strip()
        else:
            st["scenes"][0] = {**st["scenes"][0], "nar": f"{hook} {dau}".strip()}
        return _cat_moi_cau_dai(st)
    except Exception:
        return st          # lớp làm ĐẸP, không được phép giết một video đã dựng xong


def _cat_moi_cau_dai(st: dict) -> dict:
    """Chạy `_cat_cau_dai` lên MỌI chỗ chứa lời đọc của mọi dạng."""
    try:
        if st.get("narration"):
            ra = []
            for d in st["narration"]:
                ra += _cat_cau_dai(d)
            st["narration"] = ra
        for k in ("intro_vo", "outro_vo"):
            if str(st.get(k) or "").strip():
                st[k] = " ".join(_cat_cau_dai(st[k]))
        for kho in ("items", "data", "pairs"):
            for m in (st.get(kho) or []):
                if isinstance(m, dict) and str(m.get("vo") or "").strip():
                    m["vo"] = " ".join(_cat_cau_dai(m["vo"]))
        for m in (st.get("scenes") or []):
            if isinstance(m, dict) and str(m.get("nar") or "").strip():
                m["nar"] = " ".join(_cat_cau_dai(m["nar"]))
    except Exception:
        pass
    return st


def hoan_tieu_de(st: dict, kenh: dict, truc: str, t: dict, avoid) -> dict:
    """Hoàn thiện tiêu đề của một story: gắn giá trị trục, rồi ưu tiên tiêu đề dựng từ dữ liệu.

    28/8 — TÁCH RA THÀNH HÀM VÌ BỘ CHẤM ĐO NHẦM TẦNG.
    `cham_kenh.py` gọi thẳng `DUNG_STORY[dang](kenh, t)` để so tiêu đề giữa hai giá trị trục, và
    kết luận 23 kênh "tiêu đề không đổi khi xoay trục". Sai: đường chạy thật còn đi qua hai lớp
    sửa tiêu đề NỮA, cả hai nằm trong `_dung_story_xoay`. Bộ chấm đo một đường mà máy đi một đường
    khác — đúng họ lỗi đã gây ra mọi hỏng hóc tuần này (chống trùng so chuỗi A, video mang chuỗi B).
    Nay chỉ còn MỘT bản mã dựng tiêu đề, và cả hai bên đều gọi nó. Muốn đo lệch cũng không lệch được.

    28/8 — GIỮ TIÊU ĐỀ GỐC TRƯỚC KHI GẮN TRỤC.
    Đo trên 600 video, kênh DIAMOND NUMBERS ra:
        "Dodgers: 98 W — MLB wins by season (2025) — Brewers, 97 W (2025)"
    MỘT tiêu đề gọi tên HAI đội khác nhau. Vì `_tieu_de_tu_du_lieu` đọc `st["title"]` SAU khi
    `_gan_truc_vao_tieu_de` đã nhét một chủ thể vào đuôi, rồi nó nhét chủ thể của mình vào đầu —
    hai lớp chồng lên nhau, và người xem đọc ra hai kẻ dẫn đầu mâu thuẫn.
    """
    _goc = str(st.get("title") or "")
    if truc:
        st["title"] = _gan_truc_vao_tieu_de(st.get("title"), truc, t.get(truc))
    # Ưu tiên tiêu đề dựng từ dữ liệu (xem `_tieu_de_tu_du_lieu`), nhưng CHỈ KHI nó chắc chắn chưa
    # từng dùng. Thứ tự này quan trọng: khuôn-cộng-trục ở trên vẫn là đường lui bảo đảm phân biệt
    # được mọi lượt xoay, nên nếu tiêu đề theo dữ liệu trùng (hai ngày cùng một chủ thể đứng đầu —
    # chuyện có thật với bảng đọc nhiều Wikipedia) thì rơi về nó, không kẹt.
    # Dựng từ KHUNG GỐC, không dựng chồng lên bản đã bị gắn thêm.
    _td = _tieu_de_tu_du_lieu({**st, "title": _goc}, kenh)
    if _td and not _tieu_de_da_lam(_td, avoid):
        # 28/8 — PHẢI GẮN LẠI GIÁ TRỊ TRỤC VÀO BẢN DỰNG-TỪ-DỮ-LIỆU.
        # Đo bằng cách dựng story hai lượt với hai giá trị trục khác nhau: 11 kênh ra ĐÚNG MỘT
        # tiêu đề cho cả hai lượt. Ví dụ DEGREE WORTH, trục `tu_nam` đổi 2015 <-> mặc định:
        #     "2024: 299.7 — Education cost by year"     (cả hai lượt)
        # Vì `_td` dựng từ KHUNG GỐC (`_goc`) — đúng, để khỏi chồng hai chủ thể — nhưng rồi nó
        # thay thẳng `st["title"]`, ném luôn hậu tố trục mà dòng trên vừa gắn. Mà hậu tố trục
        # CHÍNH LÀ thứ phân biệt các lượt xoay khi chủ thể đứng đầu bảng không đổi (năm nào thì
        # 2024 cũng là năm học đắt nhất).
        # NHƯNG CHỈ GẮN LẠI VỚI TRỤC THỜI GIAN. Bản đầu gắn lại cho mọi trục và lập tức tái phạm
        # đúng lỗi hai-chủ-thể vừa vá, đo thật ở RENT REALITY:
        #     "Same house, different decade — Idaho, $481,825 — California, Texas and 4 more"
        # Hai đuôi: một chủ thể do dữ liệu chọn, một danh sách phạm vi truy vấn.
        # Lý do phải gắn lại chỉ đúng với trục thời gian: đổi cửa sổ thời gian mà CHỦ THỂ ĐỨNG ĐẦU
        # thường vẫn thế (năm nào 2024 cũng là năm học đắt nhất), nên không có mốc thời gian thì
        # hai lượt trùng tên. Trục nội dung (`mon`, `giong`, `bangs`) thì đổi trục là đổi hẳn dữ
        # liệu, chủ thể tự khác đi — gắn thêm chỉ là bồi một đuôi thừa.
        _truc_tg = bool(truc) and (truc.endswith(("nam", "ngay")) or truc in ("lui", "mua"))
        st["title"] = _gan_truc_vao_tieu_de(_td, truc, t.get(truc)) if _truc_tg else _td
    # Ghi lại GIÁ TRỊ TRỤC vào story để bài nghiệm thu so được "tiêu đề có khớp nội dung không".
    if truc:
        st["_truc_gia_tri"] = t.get(truc)
    return hoan_kich_ban(st, kenh)


def _dung_story_xoay(dang: str, kenh: dict, ky: dict | None, avoid: list | None) -> dict | None:
    """Dựng story, XOAY qua kho đề tài cho tới khi ra một chuyện CHƯA LÀM.

    Trục xoay đầu tiên thử luôn tham số gốc của kênh (giữ đúng ý thiết kế), rồi mới đi kho."""
    dung = DUNG_STORY.get(dang)
    if not dung:
        return None
    truc, kho = _kho_xoay_cua(kenh)
    # 26/8 — BỎ "lượt 0 trần" khi kênh có kho xoay. Trước đây lượt 0 chạy tham số gốc (không nêu
    # rõ giá trị trục) nên tiêu đề của nó KHÔNG mang trục, còn các lượt sau thì có. Hai dạng tiêu
    # đề cho cùng một bộ dữ liệu ⇒ chống trùng so không khớp ⇒ đăng lại đúng nội dung đã đăng.
    # Kho xoay đã chứa sẵn giá trị mặc định của kênh nên bỏ lượt 0 không mất đề tài nào.
    if truc and kho:
        kho = _xep_theo_nhu_cau(kenh, truc, kho)
    # 28/8 — XOAY TRỤC THÌ PHẢI BỎ NHÃN TĨNH GẮN VỚI TRỤC ĐÓ.
    #
    # Soi clip thật kênh WHAT IS IN IT: tiêu đề ghi "Breakfast cereal: what is really in it" mà
    # các mục bên trong là KEM (Amul Fruit 'N' Nut, Häagen-Dazs Vanilla). Vì cấu hình kênh có
    #     {"mon": "breakfast-cereals", "nhan": "Breakfast cereal", "xoay": "mon"}
    # `mon` xoay sang `ice-creams` nhưng `nhan` ĐỨNG YÊN — nên tiêu đề nói dối nội dung.
    # Đây là loại sai tệ nhất trong cả hệ: không phải xấu, không phải thiếu, mà là NÓI SAI. Người
    # xem bấm vào vì tưởng một đằng rồi thấy một nẻo, và họ không quay lại.
    # 12/50 kênh có nhãn tĩnh kèm trục xoay, tức 12 kênh cùng dính.
    # Nhãn tĩnh chỉ đúng cho giá trị GỐC; xoay đi thì để bộ dựng tự đặt tên theo giá trị mới.
    _goc_truc = (ky or {}).get(truc) if truc else None
    def _mot(v):
        t = {**(ky or {}), truc: v}
        if "nhan" in t and str(v) != str(_goc_truc):
            # 29/8 — ĐẶT None, KHÔNG XOÁ KHOÁ. Bản vá 28/8 dùng `t.pop("nhan")` và nó KHÔNG chạy:
            # mọi `dung_story_*` đều mở đầu bằng
            #     ts = dict(kenh.get("tham_so") or {});  ts.update(ky or {})
            # tức dựng lại tham số TỪ CẤU HÌNH KÊNH rồi mới chồng `ky` lên. Khoá đã xoá thì không
            # có gì để chồng, nên `nhan` tĩnh trong cấu hình sống lại nguyên vẹn ở tầng dưới.
            # Đo thật trên khung vừa render: tiêu đề ra "Breakfast cereal: what is really in it —
            # Ice-creams" — khung nói ngũ cốc, dữ liệu là KEM, đúng cái lỗi bản vá kia sinh ra để
            # diệt. Tôi đã tưởng nó xong suốt một ngày.
            # `None` thì `update` GHI ĐÈ được, và mọi bộ dựng đều viết `ky.get("nhan") or <mặc
            # định>` nên None rơi đúng vào đường lui.
            t["nhan"] = None
        return t
    thu = [_mot(v) for v in kho] if (truc and kho) else [dict(ky or {})]
    da_thay = None
    hong = 0            # số lần NGUỒN không trả dữ liệu (khác hẳn "đề tài đã làm rồi")
    for i, t in enumerate(thu):
        st = dung(kenh, t)
        if not st:
            hong += 1
            continue
        st = hoan_tieu_de(st, kenh, truc, t, avoid)
        da_thay = da_thay or st
        if not _tieu_de_da_lam(st.get("title"), avoid):
            if i:
                print(f"   ♻️ {kenh.get('ten')}: đề tài gốc đã làm rồi — xoay `{truc}` sang "
                      f"`{t.get(truc)}` ({i}/{len(thu) - 1})")
            return st
    # 26/8 — PHÂN BIỆT HAI NGUYÊN NHÂN. Bản đầu in "hết kho, đề tài nào cũng đã làm rồi" cho MỌI
    # trường hợp không ra story. Nhưng có hai chuyện hoàn toàn khác nhau:
    #   • kho đề tài cạn thật  -> chờ kênh đăng bớt, hoặc nới kho;
    #   • NGUỒN đang chết      -> chẳng liên quan gì tới kho, lát nữa thử lại là được.
    # Đo thật: Open Food Facts trả 503 bốn lần liên tiếp, mà log vẫn báo "hết kho" ⇒ em đi truy
    # nhầm sang cơ chế xoay vòng mất một lượt. Thông báo sai nguyên nhân đắt ngang một lỗi thật.
    if hong >= max(2, len(thu) - 1):
        print(f"   ⚠️ {kenh.get('ten')}: NGUỒN không trả dữ liệu ({hong}/{len(thu)} lượt hỏng) — "
              f"BỎ LƯỢT. Không phải cạn kho đề tài; thử lại phiên sau.")
    elif da_thay:
        print(f"   ⚠️ {kenh.get('ten')}: hết kho `{truc or 'không có trục'}` mà đề tài nào cũng "
              f"đã làm rồi — BỎ LƯỢT, không đăng trùng.")
    else:
        print(f"   ⚠️ {kenh.get('ten')}: không dựng được story nào ({hong} lượt nguồn hỏng) — BỎ LƯỢT.")
    return None



def _dinh_don_vi(so: str, don: str) -> str:
    """Dán đơn vị vào số sao cho ĐỘ LỚN không bao giờ mất (xem chú thích trong `_so_noi_bat`).

        525 + "K reads" -> "525K"      (giữ K, bỏ chữ mô tả)
        525 + "$M"      -> "$525M"     (tiền tệ đứng trước, độ lớn đứng sau)
        29  + "mpg"     -> "29 mpg"    (đơn vị ngắn thì để nguyên)
    """
    don = str(don or "").strip()
    if not don:
        return so
    if don.startswith("$"):
        return "$" + so + don[1:].strip()          # "$M" -> $525M ; "$" -> $525
    dau = don.split()[0]
    if dau in ("K", "M", "B", "T"):
        return so + dau                            # "K reads" -> 525K
    if len(don) <= 6:
        return f"{so} {don}"
    return so


def _so_noi_bat(st: dict) -> dict:
    """Rút SỐ LIỆU NỔI BẬT + nhãn của nó, ĐÚNG THEO TỪNG DẠNG STORY.

    26/8 — render thử 5 video rồi xem 5 ảnh bìa cạnh nhau: chỉ **1/5** có số (`567 cal`), bốn cái
    còn lại rơi về bố cục tiêu đề (`AMMUNITION CONTRACTS BY YEAR`) — mô tả đúng nhưng không có số,
    không có câu hỏi mở, tức không phải thứ khiến người ta bấm.

    Gốc: bản đầu chỉ đọc `st["items"][0]["stat"]`, mà mỗi dạng để dữ liệu ở khoá KHÁC:
        ranked/scaled/longshot -> items[].stat | disp | oddsDisp
        race                   -> frames[-1].data[0].value
        mapped                 -> data[].disp | value
        thennow                -> pairs[].nowVal
        cinematic              -> hook.stat
    Không khớp khoá thì `stat` rỗng ⇒ `DocThumb` tự lùi về bố cục tiêu đề. Cùng lớp lỗi "hai bên
    dùng khuôn khác nhau" đã gặp ở `doc_kenh` (33/50 tra không ra)."""
    def _g(d, *ks):
        if not isinstance(d, dict):
            return ""                       # mục có thể là chuỗi/số — xem chú thích ở nhánh `hook`
        for k in ks:
            v = (d or {}).get(k)
            if v not in (None, "", 0):
                return v
        return ""
    # 26/8 — SỐ DẪN PHẢI CÓ CHỮ SỐ. Xem tận mắt khung giây thứ 1 của long RECALL PLATE: số dẫn
    # to đùng giữa màn hình là `Cl.I` — đó là HẠNG thu hồi của FDA, không phải con số. Hook 0-3
    # giây mà không có số thì mất đúng cái tác dụng nó sinh ra để làm. Không có mục nào mang số
    # thì lấy CHÍNH SỐ MỤC (`12 recalls`) — luôn là một con số thật, luôn đúng.
    it = st.get("items") or []
    if it:
        for m in it:
            v = str(_g(m, "stat", "disp", "oddsDisp"))
            if any(c.isdigit() for c in v):
                return {"stat": v, "name": str(_g(m, "name", "label", "state"))}
        # Nhãn phải nói đúng thứ đang được ĐẾM. Đo khung hook thật: số dẫn ra `6` (số mục) mà nhãn
        # lại là `WEGMANS FOOD MARKETS, INC.` — người xem đọc thành "6 Wegmans", vô nghĩa. Có
        # `unit` thì dùng, không có thì để TRỐNG và nhường câu hỏi mở phía dưới làm nhiệm vụ —
        # số trần kèm câu hỏi vẫn là một hook đúng, còn số kèm nhãn sai thì không.
        return {"stat": str(len(it)), "name": str(st.get("unit") or "")}
    fr = st.get("frames") or []
    if fr:
        _cuoi = fr[-1] if isinstance(fr[-1], dict) else {}
        _ds = [x for x in (_cuoi.get("data") or []) if isinstance(x, dict)]
        if not _ds:
            return {}                       # khung rỗng / mục không phải dict -> không có số dẫn
        d = _ds[0]
        v = d.get("value")
        so = f"{v:,.0f}" if isinstance(v, (int, float)) else str(v or "")
        don = str(st.get("unit") or "")
        # 27/8 — ĐƠN VỊ DÀI THÌ RÚT GỌN, KHÔNG PHẢI VỨT ĐI.
        #
        # Luật cũ `len(don) <= 6` im lặng ném cả đơn vị. Xem khung hook thật của AMERICA LOOKED UP:
        # dạng này đo bằng NGHÌN lượt (`luot_doc / 1000`) với `unit = "K reads"` — dài 7 ký tự, nên
        # rơi đúng vào nhánh vứt. Hook in trần **525** trong khi ý nghĩa là **525K lượt đọc**, còn
        # thanh ngay phía sau ghi "22.8K READ". Người xem đọc hai con số cùng khung, không thể hiểu
        # nổi, và kết luận hợp lý nhất của họ là hệ bịa số — mất niềm tin vì một luật cắt chuỗi.
        # Chữ chỉ ĐỘ LỚN (K/M/B) là phần KHÔNG ĐƯỢC PHÉP mất: thiếu nó thì con số sai đi một nghìn
        # lần. Phần chữ mô tả phía sau ("reads") thì mất được — thanh bên dưới đã nói rồi.
        return {"stat": _dinh_don_vi(so, don), "name": str(d.get("name") or "")}
    da = st.get("data") or []
    if da:
        return {"stat": str(_g(da[0], "disp", "value")), "name": str(_g(da[0], "state", "name"))}
    pa = st.get("pairs") or []
    if pa:
        return {"stat": str(_g(pa[-1], "nowVal", "nowDisp")),
                "name": str(_g(pa[-1], "label", "name", "nowYear"))}
    h = st.get("hook") or {}
    # 27/8 — HOOK CÓ THỂ LÀ CHUỖI, KHÔNG PHẢI LÚC NÀO CŨNG LÀ DICT.
    # Kênh dạng phim đặt `hook` là một câu văn. Mã cũ gọi thẳng `h.get(...)` -> AttributeError:
    # 'str' object has no attribute 'get' -> giết cả bộ.
    # Trước chiều nay lỗi này nấp được vì `_so_noi_bat` chỉ chạy ở đường ẢNH BÌA; từ lúc tôi nối
    # nó vào khâu đặt tiêu đề thì nó chạy cho MỌI story, và lôi ngay dạng dữ liệu nó chưa gặp.
    # Bài học: nối một hàm cũ vào đường chạy mới nghĩa là cho nó ăn tập dữ liệu MỚI — phải soi lại
    # mọi giả định về hình dạng dữ liệu, không phải chỉ soi hàm gọi.
    if isinstance(h, str):
        return {"stat": "", "name": h.strip()}
    if isinstance(h, dict) and h:
        return {"stat": str(h.get("stat") or ""), "name": str(h.get("label") or "")}
    return {}



# Câu hỏi mở theo NHÓM NICHE — không trả lời trong ảnh, để người xem phải bấm vào.
# 26/8 — trước đây `hook` gần như luôn rỗng vì chỉ có dạng phim kể mới đặt `thumb_hook`,
# nên 4/5 ảnh bìa không có câu hỏi nào. Câu hỏi phải hợp CHỦ ĐỀ, không phải một câu chung chung
# dán cho cả 50 kênh — dán chung thì lại thành "nhìn là biết cùng một lò".
_HOI = {
    "Đồ ăn & đồ uống":      "IS YOURS ON THE LIST?",
    "Tiền cá nhân":         "HOW FAR BEHIND ARE YOU?",
    "Tội phạm có thật":     "WHY DID NOBODY ASK?",
    "Thể thao":             "GUESS WHO IS #1?",
    "Sức khoẻ & gym":       "DOES THIS APPLY TO YOU?",
    "Bí ẩn chưa lời giải":  "WHERE DID THEY GO?",
    "Người nổi tiếng":      "WHAT HAPPENED NEXT?",
    "Phim & truyền hình":   "DID YOURS SURVIVE?",
    "Nhạc":                 "REMEMBER THIS ONE?",
    "Game":                 "IS YOUR GAME HERE?",
    "Xe":                   "IS YOUR CAR ON IT?",
    "Thú cưng & động vật":  "IS THIS YOUR BREED?",
    "Du lịch":              "WOULD YOU GO?",
    "Công nghệ & AI":       "WHO IS REALLY WINNING?",
    "Kinh dị & rùng rợn":   "WOULD YOU STAY?",
    "Quan hệ & hẹn hò":     "SOUND FAMILIAR?",
    "Nghề nghiệp":          "IS YOUR JOB SAFE?",
    "Nhà ở":                "CAN YOU STILL AFFORD IT?",
    "Lịch sử":              "WHY WAS THIS FORGOTTEN?",
    "Vũ trụ":               "HOW CLOSE DID IT GET?",
    "Thời tiết & thảm hoạ": "IS YOUR STATE ON IT?",
    "Quân sự":              "WHERE DID IT GO?",
    "Luật & quyền công dân": "DO YOU KNOW YOUR RIGHTS?",
    "Giáo dục":             "WAS IT WORTH IT?",
}


def _cau_hoi_mo(kenh: dict, st: dict) -> str:
    """Câu hỏi mở cho ảnh bìa. Story tự đặt thì tôn trọng; không thì lấy theo nhóm chủ đề."""
    rieng = str(st.get("thumb_hook") or st.get("hook") or "").strip()
    if rieng and not isinstance(st.get("hook"), dict):
        return rieng
    return _HOI.get(str(kenh.get("niche") or ""), "HOW BAD IS IT?")


def lam_thumb(kenh: dict, st: dict, ra: str, comp: str = "", pf: str = "") -> str:
    """Ảnh bìa cho video thế hệ 2.

    26/8 — TRƯỚC KHI CÓ HÀM NÀY, NHÁNH THẾ HỆ 2 KHÔNG LÀM THUMBNAIL. `chay_chung` render xong là
    `return` thẳng, còn `run_render` cũng `return` ngay sau khi gọi nó — nên cả 50 kênh mới sẽ
    xuất bản mà không có ảnh bìa nào. Bắt được lúc rà đường đi của `mau`/`font`, trước khi seed.

    Số liệu lấy từ CHÍNH story vừa dựng (mục #1), không nhờ AI nghĩ thêm: thumbnail phải nói đúng
    thứ video nói, nếu không là câu view sai sự thật."""
    # 26/8 — THIẾU DÒNG NÀY LÀ MỌI VIDEO GEN-2 KHÔNG CÓ ẢNH BÌA. `chay_chung` có
    # `import datastory_ci as DS` nhưng đó là tên CỤC BỘ trong hàm đó, không phải của mô-đun;
    # `lam_thumb` là hàm riêng nên `DS` không tồn tại ⇒ `NameError`, và except ngay dưới nuốt nó
    # thành một dòng cảnh báo. Render thật tại máy mới lộ ra: video ra đúng 38,3s -23,2 dB,
    # chỉ có mỗi dòng `⚠️ thumbnail ... lỗi: name 'DS' is not defined`.
    # Chốt `t_gen2_phai_lam_thumbnail` KHÔNG bắt được: nó kiểm hình dạng mã (có gọi lam_thumb,
    # có truyền mau/font), mà lỗi này chỉ hiện lúc CHẠY.
    import datastory_ci as DS
    b = kenh.get("brand") or {}
    pal = b.get("palette") or {}
    dau = _so_noi_bat(st)
    try:
        return DS.doc_thumb(
            kenh.get("ten") or "", ra,
            big=st.get("title") or kenh.get("ten") or "",
            stat=str(dau.get("stat") or st.get("thumb_stat") or "").strip(),
            stat_label=str(dau.get("name") or st.get("thumb_label") or "").strip(),
            hook=_cau_hoi_mo(kenh, st),
            accent=pal.get("primary", "#22D3EE"), accent2=pal.get("accent", "#F5B301"),
            comp_id=comp, props_path=pf, uu_tien_khung=False,
            mau=b.get("mau", "trai"), font=b.get("font", "")) or ""
    except Exception as e:
        print(f"   ⚠️ thumbnail {kenh.get('ten')} lỗi: {str(e)[:70]}")
        return ""



def _gop_story(sts: list, truc: str = "", tran: int = 6) -> dict:
    """Gộp NHIỀU chương thành MỘT story, để một short gói trọn 2-3 chương.

    26/8 — anh nói rõ: "1 long làm ra khoảng 3 short, còn có thể gộp 2-3 chương thành 1 short sao
    cho phù hợp, thành 1 clip short hoàn hảo". Nên short KHÔNG phải một chương lẻ, cũng không phải
    một đoạn cắt của long: nó là một bản riêng, gói phần đắt nhất của mấy chương liền kề.

    Hai điều phải giữ, nếu không gộp lại thành phá:
      • **CÓ TRẦN.** Nối thẳng 2 chương `ranked` là 12 mục vào một bảng tier khổ dọc — tràn khung,
        đúng thứ anh dặn tránh. Nên lấy XEN KẼ mỗi chương một mục cho tới `tran`: hai chương đều
        có mặt, và mục đầu (mục đắt nhất) của cả hai chắc chắn được chọn.
      • **TIÊU ĐỀ PHẢI NÓI ĐÚNG PHẠM VI.** Gộp 2024 với 2025 mà tiêu đề vẫn ghi "(2025)" là nói
        sai với người xem, lại làm hỏng khoá chống trùng. Ghép thành "(2024-2025)".

    Lời dẫn (`intro_vo`/`outro_vo`) lấy của chương đầu; `build_*_props` sẽ đọc kịch bản GỘP để sinh
    tiếng nói mới, nên short có một mạch kể riêng chứ không phải hai đoạn dán vào nhau."""
    sts = [x for x in sts if x]
    if not sts:
        return {}
    if len(sts) == 1:
        return sts[0]
    goc = dict(sts[0])
    for khoa in ("items", "pairs", "data", "frames", "scenes"):
        cac = [x.get(khoa) for x in sts if isinstance(x.get(khoa), list) and x.get(khoa)]
        if not cac:
            continue
        # trần theo khoá: `data` của `mapped` là 51 bang (bản đồ vẽ hết), không được cắt còn 6
        t = 51 if khoa == "data" else tran
        # 27/8 — XEN KẼ MÀ KHÔNG LỌC TRÙNG THÌ RA HAI THẺ GIỐNG HỆT NHAU CẠNH NHAU.
        # Anh gửi khung PAYCHECK GAP (2000-2012): "Health care 564" hiện hai lần, "Housing 401"
        # hiện hai lần. Dữ liệu gốc của từng chương KHÔNG trùng (đo rồi: 6 mục khác nhau) — trùng
        # đẻ ra ở đúng vòng lặp này. Kênh xoay trục `tu_nam`, mà bộ chỉ số BLS (nhà ở, y tế, thực
        # phẩm…) thì năm nào cũng gồm ĐÚNG những hạng mục đó. Xen kẽ chương 2000 với chương 2012
        # là ghép hai danh sách có chung tên hạng mục -> mỗi tên xuất hiện hai lần.
        # Người xem thấy hai thẻ y hệt nhau nằm cạnh nhau: đọc ra như video lỗi, và một nửa chỗ
        # trên khung bị phí cho thông tin đã nói rồi.
        # Lọc theo KHOÁ NHẬN DẠNG của từng mục (tên/nhãn/bang), giữ bản gặp trước — tức bản của
        # chương sớm hơn, đúng thứ tự xen kẽ vốn có.
        def _khoa(x):
            if not isinstance(x, dict):
                return str(x)
            for k in ("name", "label", "state", "ten", "giong"):
                if x.get(k):
                    return str(x[k]).strip().lower()
            return str(sorted(x.items()))[:80]
        ra, i, da = [], 0, set()
        while len(ra) < t and any(i < len(c) for c in cac):
            for c in cac:
                if i < len(c) and len(ra) < t:
                    kx = _khoa(c[i])
                    if kx not in da:
                        da.add(kx)
                        ra.append(c[i])
            i += 1
        goc[khoa] = ra
    # phạm vi trục: rút các giá trị đã nhét vào tiêu đề từng chương rồi ghép đầu-cuối
    import re as _re
    vals = []
    for x in sts:
        m = _re.search(r"\(([^)]+)\)\s*$", str(x.get("title") or ""))
        if m and m.group(1) not in vals:
            vals.append(m.group(1))
    tg = _re.sub(r"\s*\([^)]*\)\s*$", "", str(goc.get("title") or "")).strip()
    if len(vals) >= 2:
        goc["title"] = f"{tg} ({min(vals)}-{max(vals)})"
    elif vals:
        goc["title"] = f"{tg} ({vals[0]})"
    return goc


def _chia_nhom(xs: list, n: int) -> list:
    """Chia `xs` thành đúng `n` nhóm liền kề, chia đều nhất có thể (6 chương/3 short = 2-2-2)."""
    n = max(1, min(n, len(xs)))
    co = len(xs) // n
    du = len(xs) % n
    ra, i = [], 0
    for k in range(n):
        d = co + (1 if k < du else 0)
        ra.append(xs[i:i + d]); i += d
    return ra


def _props_chuong(kenh: dict, st: dict, dang: str, kh: str, keys: list | None):
    """Dựng props cho MỘT chương, đúng đường của từng dạng. Trả props hoặc None."""
    if dang == "race":
        r = dung_props_race(kenh, None, st, kh)
    elif dang == "cinematic":
        r = dung_props_phim(kenh, None, keys, st, kh)
    else:
        comp, ten_props = DUONG_RA.get(dang, (None, None))
        if not ten_props:
            return None
        r = dung_props(kenh, st, dang, ten_props, kh, keys)
    return r[0] if r else None


def chay_bo(kenh: dict, ra_long: str = "", avoid: list | None = None,
            so_short: int = 3, so_chuong: int = 6,
            keys: list | None = None) -> tuple[str, list] | None:
    """MỘT BỘ = 1 LONG 16:9 (nhiều chương) + `so_short` SHORT 9:16, mỗi short GỘP 2-3 chương.

    26/8 — ghi lại nguyên văn hai lần anh phải nhắc, để không làm sai lần thứ ba:

      > long 16:9 chuẩn, short "cắt" ý là lấy **kịch bản** thôi — còn phải viết và design render
      > làm lại cho chuẩn 9:16, hook đẹp. Không phải cắt ra là xong.

      > 1 long làm ra khoảng 3 short, còn có thể **gộp 2-3 chương thành 1 short** sao cho phù hợp,
      > thành 1 clip short hoàn hảo.

    Nên luồng là: dựng `so_chuong` chương -> LONG ghép đủ cả `so_chuong` -> chia chương thành
    `so_short` nhóm liền kề, mỗi nhóm GỘP lại thành một story rồi render một short riêng. Short vì
    thế có kịch bản riêng, tiếng nói riêng, hook riêng — không phải một đoạn của long, cũng không
    phải một chương lẻ trơ trọi.

    Trả `(đường_long, [(đường_short, story), ...])`, hoặc None nếu không đủ dữ liệu."""
    import datastory_ci as DS
    ten = kenh.get("ten", "?")
    dang = kenh.get("dinh_dang")
    if dang not in DUNG_STORY:
        print(f"   ⚠️ {ten}: dạng '{dang}' chưa có đường dựng bộ")
        return None
    truc, _ = _kho_xoay_cua(kenh)
    da = list(avoid or [])
    chuong, kho_st = [], []
    for i in range(max(1, so_chuong)):
        st = _dung_story_xoay(dang, kenh, None, da)
        if not st:
            break
        da.append(st.get("title") or "")
        pr = _props_chuong(kenh, st, dang, f"c{i + 1}", keys)
        if not pr:
            print(f"   ⚠️ {ten}: chương {i + 1} không dựng được props — bỏ chương")
            continue
        chuong.append({"dang": dang, "props": pr})
        kho_st.append(st)
    if not chuong:
        print(f"   ⚠️ {ten}: không dựng được chương nào — BỎ LƯỢT")
        return None

    # ── LONG 16:9 ───────────────────────────────────────────────────────────────────────────
    br = kenh.get("brand") or {}
    pal = br.get("palette") or {}
    slk = DS.slug(kenh["handle"].lstrip("@"))
    goi = {"chuong": chuong, "handle": kenh["handle"], "font": br.get("font", ""),
           "accent": pal.get("primary", "#7C5CFF")}
    pf = os.path.join(DS.PUB, f"_th2long_{slk}.json")
    json.dump(goi, io.open(pf, "w", encoding="utf-8"), ensure_ascii=False)
    # ── KIỂM TRÙNG TRƯỚC KHI RENDER (28/8) ────────────────────────────────────────────────
    #
    # Anh chỉ ra: "sao không check đạt chuẩn rồi mới làm, chứ làm xong rồi dọn thì tốn công".
    # Đúng. Bản vá đầu của tôi kiểm SAU `_gop_story` — mà chỗ đó nằm sau khi long VÀ tất cả short
    # đã render xong. Bắt được trùng ở đó thì vẫn đốt trọn công rồi mới vứt: mỗi bộ là một lượt
    # render long 5-7 phút cộng 3 short, cộng giọng đọc, cộng ảnh.
    #
    # Tiêu đề cuối cùng do `_gop_story` quyết, mà `_gop_story` chỉ cần `kho_st` — thứ đã có SẴN ở
    # đây, trước khi render một khung hình nào. Nên kiểm được ngay bây giờ.
    # Nguyên tắc: kiểm ở chỗ SỚM NHẤT mà câu trả lời đã xác định, không phải ở chỗ tiện viết.
    _tl_truoc = str((_gop_story(kho_st, truc, tran=6) or {}).get("title") or "")
    if _tl_truoc and _tieu_de_da_lam(_tl_truoc, avoid):
        print(f"   ♻️ {ten}: bộ này sẽ ra tiêu đề ĐÃ LÀM RỒI ({_tl_truoc[:54]}) — "
              f"BỎ TRƯỚC KHI RENDER, không đốt công")
        return None
    ra_long = os.path.abspath(ra_long or os.path.join(GOC, "out", f"th2long_{slk}.mp4"))
    os.makedirs(os.path.dirname(ra_long), exist_ok=True)
    DS.run_render_cmd(["npx", "remotion", "render", "src/index.ts", "Gen2Long", ra_long,
                       f"--props=./{os.path.relpath(pf, DS.ENG)}", "--gl=swiftshader", "--jpeg-quality=100", "--crf=15",
                       "--concurrency=2", "--log=error"],
                      cwd=DS.ENG, timeout=5400, label=f"Gen2Long({ten})")
    ok, info = DS.qc(ra_long)
    print(f"{'✅' if ok else '❌'} {ten} LONG 16:9 ({len(chuong)} chương) · {info}")
    if not ok:
        return None
    # Long cũng phải qua cổng hook: khung mở đầu của long là thứ quyết định lượt xem trên trang chủ.
    chuan_am(ra_long)
    if not qc_hook_sau_render(ra_long, ten, keys)[0]:
        return None

    # ── SHORT 9:16, mỗi cái gộp 2-3 chương ──────────────────────────────────────────────────
    shorts = []
    for gi, nhom in enumerate(_chia_nhom(kho_st, so_short), 1):
        st_g = _gop_story(nhom, truc)
        if not st_g:
            continue
        ra_s = os.path.abspath(os.path.join(GOC, "out", f"th2bo_{slk}_s{gi}.mp4"))
        kq = chay_chung(kenh, ra=ra_s, st_san=st_g, ky_hieu=f"s{gi}", keys=keys)
        if not kq:
            print(f"   ⚠️ {ten}: short {gi} (gộp {len(nhom)} chương) không dựng được")
            continue
        shorts.append((kq[0], st_g))
    if not shorts:
        print(f"   ⚠️ {ten}: có long nhưng KHÔNG ra short nào")
        return None
    # 26/8 — TIÊU ĐỀ LONG PHẢI PHỦ CẢ BỘ. `_gen2_bo` vốn lấy `chuong[0][1]` làm tiêu đề long, tức
    # story của SHORT ĐẦU TIÊN. Từ lúc short gộp 2 chương, short đầu chỉ phủ chương 1-2 — nên long
    # trải 6 chương `2020-2025` lại mang tên `(2024-2025)`. Sai một phần ba sự thật, và người xem
    # bấm vào vì tên đó sẽ thấy nội dung khác. Gộp TOÀN BỘ chương để lấy đúng phạm vi.
    st_long = _gop_story(kho_st, truc, tran=6)
    # ── CHỐNG TRÙNG PHẢI KIỂM ĐÚNG CHUỖI SẼ ĐI RA (28/8) ──────────────────────────────────
    #
    # ĐÂY LÀ GỐC CỦA 334/600 VIDEO HỎNG HÔM NAY.
    # `_gop_story` VIẾT LẠI tiêu đề của long sau khi gộp chương:
    #     goc["title"] = f"{tg} ({min(vals)}-{max(vals)})"   -> "MLB wins by season (2022-2025)"
    # Nghĩa là tiêu đề CUỐI CÙNG khác hẳn tiêu đề mà `_story_xoay` đã đem đi kiểm trùng. Bộ chống
    # trùng kiểm một chuỗi, video mang một chuỗi khác — kiểm xong vô nghĩa. Hai bộ khác nhau phủ
    # cùng một dải năm sẽ ra tiêu đề y hệt, và không có gì chặn.
    # Đo được: DIAMOND NUMBERS 32 video, một tiêu đề lặp 9 lần, TRONG CÙNG MỘT LANE.
    #
    # Bài học: chống trùng phải kiểm ĐÚNG CHUỖI SẼ ĐI RA, ở CHỖ CUỐI CÙNG nó được quyết định.
    # Kiểm sớm rồi để khâu sau đổi đi thì lớp bảo vệ chỉ còn là hình thức.
    # Lưới THỨ HAI. Lưới thứ nhất nằm trước khi render (xem `_tl_truoc`) và bắt gần hết. Giữ lưới
    # này cho trường hợp `_gop_story` ra kết quả khác sau khi vài chương bị loại giữa chừng —
    # hiếm, nhưng khi xảy ra thì thà vứt một bộ còn hơn đăng trùng.
    _tl = str((st_long or {}).get("title") or "")
    if _tl and _tieu_de_da_lam(_tl, avoid):
        # Đã làm rồi. Phân biệt bằng thứ CÓ THẬT trong dữ liệu — kẻ dẫn đầu — chứ không đánh số.
        _them = _tieu_de_tu_du_lieu(st_long, kenh)
        st_long["title"] = _them if (_them and not _tieu_de_da_lam(_them, avoid)) else ""
        if not st_long["title"]:
            print(f"   ♻️ {ten}: long trùng đề tài đã làm ({_tl[:52]}) — BỎ BỘ, không đăng trùng")
            return None
        print(f"   ♻️ {ten}: long trùng sau khi gộp — đổi tiêu đề thành {st_long['title'][:56]!r}")
    print(f"   🎬 {ten}: BỘ = 1 long 16:9 ({len(chuong)} chương) + {len(shorts)} short 9:16 "
          f"(mỗi short gộp ~{max(1, len(chuong) // max(1, len(shorts)))} chương)")
    print(f"      long: {st_long.get('title')}")
    return ra_long, shorts, st_long


def _noi_video(cac_tep: list, ra: str) -> bool:
    """Nối các chương thành long. Dùng `-c copy` để KHÔNG mã hoá lại — nhanh, và quan trọng hơn:
    khung hình của short và của long GIỐNG NHAU TỪNG PIXEL, đúng nghĩa 'short cắt từ long'."""
    import subprocess, tempfile
    if not cac_tep:
        return False
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        for t in cac_tep:
            fh.write("file '" + os.path.abspath(t).replace("'", "'\\''") + "'\n")
        ds = fh.name
    try:
        r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", ds,
                            "-c", "copy", ra], capture_output=True, timeout=600)
        if r.returncode != 0 or not os.path.exists(ra):
            # `-c copy` kén: các chương phải cùng bộ mã hoá. Chúng đều ra từ cùng một lệnh render
            # nên bình thường là khớp; lệch thì mã hoá lại, chậm hơn nhưng không mất bộ.
            print("   ⚠️ nối nhanh hỏng — mã hoá lại")
            r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", ds,
                                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                                "-c:a", "aac", ra], capture_output=True, timeout=1800)
        return os.path.exists(ra) and os.path.getsize(ra) > 0
    finally:
        try: os.unlink(ds)
        except Exception: pass


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", required=True)
    ap.add_argument("--thu", action="store_true", help="chỉ in story, không render")
    ap.add_argument("--render", action="store_true", help="dựng thành video thật")
    a = ap.parse_args()
    k = doc_kenh(a.kenh)
    if not k:
        print(f"❌ không thấy kênh '{a.kenh}'")
        return 2
    MOI = {"bai_duoc_doc": {"nam": 2026, "thang": 8, "ngay": 20},
           "tieu_hanh_tinh": {"tu_ngay": "2026-08-20", "den_ngay": "2026-08-22"}}
    ky = MOI.get(k["ham"], {})
    st = DUNG_STORY[k["dinh_dang"]](k, ky)
    if not st:
        return 3
    print(f"\n📄 {st['title']}   [{k['niche']} · {k['dinh_dang']} · chất liệu {k['chat_lieu']}]")
    if st.get("frames"):
        for d in st["frames"][-1]["data"][:6]:
            print(f"   {st['frames'][-1]['t']}  {d['value']:>9}  {d['name']}")
    for m in (st.get("items") or st.get("data") or st.get("pairs") or st.get("scenes") or [])[:6]:
        nhan = m.get("name") or m.get("state") or m.get("label") or m.get("nar", "")
        so = m.get("stat") or m.get("disp") or m.get("oddsDisp") or m.get("nowVal") or ""
        print(f"   {str(so):>10}  {str(nhan)[:56]}")
    if a.render:
        return 0 if chay_chung(k, ky=MOI.get(k["ham"], {}), keys=keys_cuc_bo() or None) else 4
    return 0


DUNG_STORY.update({"ranked": dung_story_ranked, "race": dung_story_race,
                   "cinematic": dung_story_cinematic, "scaled": dung_story_scaled,
                   "mapped": dung_story_mapped, "longshot": dung_story_longshot,
                   "thennow": dung_story_thennow})


if __name__ == "__main__":
    sys.path.insert(0, GOC)
    sys.exit(main())
