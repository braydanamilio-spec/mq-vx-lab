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
    return f"{v:,.0f}"


# Tên nguồn HIỆN TRÊN MÀN HÌNH phải là tên cơ quan, không phải mã nội bộ. Cả điểm tin cậy của
# kênh nằm ở dòng này — "Source: bls" đọc như lỗi, "U.S. Bureau of Labor Statistics" là bằng chứng.
TEN_NGUON = {
    "usaspending": "USAspending.gov", "sec": "SEC EDGAR", "bls": "U.S. Bureau of Labor Statistics",
    "openfda": "openFDA · U.S. FDA", "nhtsa": "NHTSA", "court": "CourtListener",
    "worldbank": "World Bank Open Data", "usgs": "U.S. Geological Survey", "nasa": "NASA CNEOS",
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


def _cong_an_toan(st: dict | None, ten_kenh: str = "") -> dict | None:
    """Cổng cuối: story nào còn chữ cấm thì cắt mục đó; cắt xong không đủ thì BỎ CẢ LƯỢT.

    Thà mất một video còn hơn mất một kênh."""
    if not st:
        return None
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
    return " ".join(tu) or t[:toi_da]


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


def _bd_thu_hoi(D, ky):
    kho = ky.get("kho", "thuc_pham")
    r = D.thu_hoi_fda(kho, 6, nam=int(ky.get("nam", 0)) or 0)
    if len(r) < 3:
        return None
    nhan = {"thuc_pham": "Food", "thuoc": "Drug", "thiet_bi": "Device"}.get(kho, "Product")
    return (f"{nhan} recalls you probably missed",
            [{"name": _gon(x["cong_ty"]), "stat": (x["muc_do"] or "").replace("Class ", "Cl."),
              "vo": f"{_gon(x['cong_ty'], 34)}. {x['ly_do'][:90]}"} for x in r],
            "All of this is filed with the F D A.")


def _bd_ban_an(D, ky):
    r = D.ban_an(ky.get("tu_khoa", "consumer fraud"), 6)
    if len(r) < 3:
        return None
    return (f"Sued over {ky.get('tu_khoa', 'this')}",
            [{"name": _gon(x["ten_vu"], 30), "stat": str(x["ngay"])[:4],
              "vo": f"{_gon(x['ten_vu'], 40)}, filed {str(x['ngay'])[:4]}."} for x in r],
            "Court records are public. Look them up.")


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


def _bd_steam(D, ky):
    r = D.game_steam(60)
    if len(r) < 6:
        return None
    if ky.get("loc") == "chet_yeu":
        # Góc NGƯỢC LẠI: game bán được nhiều mà gần như không ai còn mở. Cùng một nguồn, hai kênh,
        # hai câu chuyện khác hẳn — đây là cách để hai kênh không giẫm chân nhau.
        def _chu(x):
            v = str(x.get("so_huu") or "").replace(",", "")
            try:
                return int(v.split("–")[0] or 0)
            except Exception:
                return 0
        r = sorted([x for x in r if _chu(x) > 500000], key=lambda z: z["dang_choi"])[:6]
        if len(r) < 3:
            return None
        return ("Games millions bought and nobody plays",
                [{"name": _gon(x["ten"], 26), "stat": _so(x["dang_choi"]),
                  "vo": f"{_gon(x['ten'], 32)}. Only {x['dang_choi']:,} still online."} for x in r],
                "Owned by millions. Empty tonight.",
                "Millions own these games. Top of the board is the emptiest.")
    r = r[:6]
    return ("Games people actually play right now",
            [{"name": _gon(x["ten"], 26), "stat": _so(x["dang_choi"]),
              "vo": f"{_gon(x['ten'], 32)}. {x['dang_choi']:,} playing right now."} for x in r],
            "Not sales. People actually online.")


def _bd_trieu_hoi(D, ky):
    r = D.trieu_hoi_xe(ky.get("hang", "ford"), ky.get("dong", ""), int(ky.get("nam", 2022)))
    if len(r) < 3:
        return None
    ten = f"{ky.get('hang', '').title()} {ky.get('dong', '')}".strip()
    return (f"{ten} {ky.get('nam', '')}: what got recalled",
            [{"name": _gon(x["bo_phan"], 26), "stat": (x["so_xe"] or "—"),
              "vo": f"{_gon(x['bo_phan'], 30)}. {x['hau_qua'][:90]}"} for x in r[:6]],
            "Every recall is on the N H T S A site.")


def _bd_the_gioi(D, ky):
    r = D.chi_so_the_gioi(ky.get("ma", "NY.GDP.PCAP.CD"), int(ky.get("nam", 2023)), 6)
    if len(r) < 3:
        return None
    return (f"{ky.get('nhan', 'World ranking')} {ky.get('nam', 2023)}",
            [{"name": _gon(x["nuoc"], 24), "stat": _so(x["gia_tri"]),
              "vo": f"{x['nuoc']}. {_so(x['gia_tri'])}."} for x in r],
            "World Bank open data. Check it yourself.")


def _bd_ho_so_sec(D, ky):
    r = D.tim_ho_so(ky.get("tu_khoa", "layoff"), n=6)
    if len(r) < 3:
        return None
    return (f'Companies that wrote "{ky.get("tu_khoa", "")}" in their filings',
            [{"name": _gon(x["cong_ty"], 26), "stat": x["mau_don"],
              "vo": f"{_gon(x['cong_ty'], 32)}, in their {x['mau_don']}."} for x in r],
            "They filed it themselves. It is public.")


def _bd_thien_thach(D, ky):
    r = D.tieu_hanh_tinh(ky["tu_ngay"], ky.get("den_ngay", ""), ky.get("key", "DEMO_KEY"), 6)
    if len(r) < 3:
        return None
    return ("Rocks that just passed Earth",
            [{"name": _gon(x["ten"], 22), "stat": f"{x['duong_kinh_m']}m",
              "vo": f"{_gon(x['ten'], 26)}. {x['duong_kinh_m']} meters wide, "
                    f"{x['cach_km'] / 1000:,.0f} thousand kilometers away."} for x in r],
            "N A S A tracks every one of them.")


def _bd_giong_cho(D, ky):
    r = D.giong_cho(6)
    if len(r) < 3:
        return None
    return ("Dog breeds, one file each",
            [{"name": x["giong"], "stat": f"{len(x['bien_the'])} types" if x["bien_the"] else "—",
              "vo": f"{x['giong']}.", "img_url": x.get("anh")} for x in r],
            "Which one is yours?")


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
    return (f"{ky.get('nhan', 'Price index')} by year",
            [{"name": str(m["nam"]), "stat": f"{m['gt']:,.1f}",
              "vo": f"{m['nam']}. {m['gt']:,.1f}."} for m in reversed(muc)],
            "Bureau of Labor Statistics. Official numbers.")


def _mon_an(D, mon, n=30):
    """Dinh dưỡng: Open Food Facts TRƯỚC (mở, không hạn mức), USDA chỉ là đường lùi.

    USDA DEMO_KEY hết 30 lượt/giờ là hai kênh đồ ăn tắt tiếng — đã dính đúng vậy 25/8."""
    # Open Food Facts xếp theo ĐỘ PHỔ BIẾN nên "cereal" vẫn trả về khoai tây chiên. Tiêu đề nói
    # một đằng mà bảng liệt kê một nẻo thì video mất tin cậy ngay giây đầu — lọc theo tên trước.
    r = [x for x in D.thanh_phan_off(mon, n) if x.get("calo")]
    if len(r) >= 3:
        return r
    return [x for x in D.thanh_phan_mon(mon, n) if x.get("calo")]


def _bd_dinh_duong(D, ky):
    mon = ky.get("mon") or "pizza"
    r = _mon_an(D, mon)
    # USDA đặt cùng một `description` cho hàng chục sản phẩm khác hãng ("PIZZA" x 30). Lấy thẳng
    # là ra bảng 6 dòng y hệt nhau — nhìn như lỗi render. Ghép tên hãng để phân biệt, và bỏ trùng.
    thay, muc = set(), []
    for x in sorted(r, key=lambda z: -z["calo"]):
        ten = " ".join(f"{x.get('hieu') or ''} {x['ten']}".split()).title()
        khoa = ten.lower()
        if khoa in thay:
            continue
        thay.add(khoa)
        muc.append({"name": _gon(ten, 26), "stat": f"{x['calo']:.0f} cal",
                    "vo": f"{_gon(ten, 34)}. {x['calo']:.0f} calories per hundred grams."})
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
    items = [{**m, "tier": TIER[min(i, 5)]} for i, m in enumerate(muc[:6])]
    return _cong_an_toan({
        "title": tieu_de,
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
        gop = {}
        for x in hd:
            t = _gon(x["ten"], 16)
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
    goc = _dt.date(int(ky.get("nam", 2026)), int(ky.get("thang", 8)), int(ky.get("ngay", 20)))
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
            frames.append({"t": int(d), "data": sorted(data, key=lambda z: -z["value"])[:7]})
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
    dan = [f"Six seasons of {nhan} leaders.",
           f"{frames[0]['data'][0]['name']} started on top.",
           f"{frames[-1]['data'][0]['name']} is there now.",
           "Per game, no adjustments.",
           "Numbers from the league's own feed."]
    return (f"NBA {nhan} leaders", nhan[:3], frames, dan)


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
def _pk_ban_an(D, ky):
    r = D.ban_an(ky.get("tu_khoa", "wrongful death"), 4)
    if not r:
        return None
    v = r[0]
    nam = str(v["ngay"])[:4]
    trich = " ".join(str(v["trich"] or "").split())[:150]
    canh = [
        (f"This case is real. {_gon(v['ten_vu'], 60)}.", "empty american courtroom, morning light"),
        (f"Filed in {nam}.", "stack of legal case files on a desk"),
        (f"The court: {_gon(v['toa'], 50)}.", "exterior of a US federal courthouse"),
        (f"From the opinion: {trich}." if trich else "The opinion runs for pages.",
         "close up of a printed court opinion page"),
        (f"There are {len(r)} more like it filed under the same words.",
         "long row of archive shelves with case binders"),
        ("Every line of this is public record. Anyone can pull it.",
         "hands opening a public records folder"),
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
         "a lit phone screen alone in a dark room"),
        (f"It ranked number {v['hang']} across all of Wikipedia that day.",
         "a wall of glowing screens showing traffic graphs"),
        ("Nobody organised that. People just wanted to know.",
         "crowd of people walking, all looking down at phones"),
        (f"The second most read that day was {r[1]['ten']}." if len(r) > 1
         else "The rest of the list was ordinary news.",
         "newspaper front pages spread on a table"),
        ("Curiosity leaves a trace. This is what it looks like counted.",
         "a rising line chart drawn on frosted glass"),
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
        (f"The title: {_gon(v['tieu_de'], 110)}.", "close up of an academic paper abstract"),
        (f"It ran in {v['tap_chi']}.", "library shelf of bound medical journals"),
        ("Not a headline about a study. The study itself.",
         "researcher reading a paper under a desk lamp"),
        (f"There are {len(r)} more on the same question, all public.",
         "search results page on a clean monitor"),
        (f"Reference number {v['ma']} on PubMed. Go read it.",
         "hands typing an ID into a search field"),
    ]
    return (_gon(v["tieu_de"], 46), f"One real study on {ky.get('tu_khoa', 'this')}.", canh)


def _pk_nhac(D, ky):
    r = D.ho_so_nhac(ky.get("tu_khoa", "one hit wonder"), 4)
    r = [x for x in r if x.get("bat_dau")]
    if not r:
        return None
    v = r[0]
    canh = [
        (f"{v['ten']}. Started {v['bat_dau'][:4]}.", "vintage vinyl record on a turntable"),
        (f"Type: {v['loai'] or 'artist'}. Country: {v['nuoc'] or 'unlisted'}.",
         "old passport and tour paperwork on a table"),
        ((f"The record says it ended in {v['ket_thuc'][:4]}." if v.get("ket_thuc")
          else "The record has no end date."), "empty concert stage with one spotlight"),
        ("This is the catalogue entry, not the legend.",
         "index card drawer in a music archive"),
        ("MusicBrainz keeps it because somebody had to.",
         "close up of handwritten liner notes"),
        ("Every credit here can be checked in a minute.",
         "screen showing a music database entry"),
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
        (f"Year on the record: {v['nam'] or 'unlisted'}.", "faded calendar page from mid century"),
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
    gu = str(kenh.get("style_anh") or "").strip()
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
    mon = ky.get("mon") or "pizza"
    r = _mon_an(D, mon)
    thay, muc = set(), []
    for x in sorted(r, key=lambda z: -z["calo"]):
        ten = " ".join(f"{x.get('hieu') or ''} {x['ten']}".split()).title()
        if ten.lower() in thay:
            continue
        thay.add(ten.lower())
        muc.append({"name": _gon(ten, 24), "emoji": "🍕", "value": round(x["calo"]),
                    "disp": f"{x['calo']:.0f} cal"})
        if len(muc) >= 6:
            break
    if len(muc) < 3:
        return None
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
    r = D.chi_so_the_gioi(ky.get("ma", "NY.GDP.PCAP.CD"), int(ky.get("nam", 2023)), 6)
    if len(r) < 3:
        return None
    muc = [{"name": _gon(x["nuoc"], 22), "emoji": "🌍", "value": round(x["gia_tri"], 1),
            "disp": _so(x["gia_tri"])} for x in r]
    return (f"{ky.get('nhan', 'World ranking')} {ky.get('nam', 2023)}", "", muc,
            "World Bank open data.")


def _sk_hop_dong(D, ky):
    nam = int(ky.get("nam", 2024))
    hd = D.hop_dong_lon(nam, 6, ky.get("de_tai", ""))
    if len(hd) < 3:
        return None
    muc = [{"name": _gon(x["ten"], 22), "emoji": "🧾", "value": round(x["tien"] / 1e6, 1),
            "disp": _tien(x["tien"])} for x in hd]
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
    bangs = ky.get("bangs") or ["TX", "CA", "FL", "NY", "OK", "KS", "LA", "AZ", "CO", "MO"]
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


def _bd_may_bay(D, ky):
    r = D.may_bay(24, -125, 49, -66, 200)
    if len(r) < 10:
        return None
    gop = {}
    for x in r:
        gop[x["nuoc"] or "Unknown"] = gop.get(x["nuoc"] or "Unknown", 0) + 1
    data = [{"name": k, "value": v} for k, v in sorted(gop.items(), key=lambda z: -z[1])[:10]]
    cao = r[0]
    dan = [f"Right now there are {len(r)} aircraft over the United States.",
           f"The highest is {cao['hieu'] or 'unmarked'}, at {cao['cao_m']:,.0f} meters.",
           f"Registered in {data[0]['name']}: {data[0]['value']} of them.",
           "Nobody is hiding this. The transponders broadcast it.",
           "OpenSky just writes it all down.",
           "Look up. One of these is above you."]
    return ("Who is flying over America", "planes", data, dan)


def _bd_gia_nha(D, ky):
    """Giá nhà từng bang — bản đồ nóng đúng chỗ đắt."""
    r = D.gia_nha_zillow("State")
    if len(r) < 10:
        return None
    moi = []
    for x in r:
        ks = sorted(x["gia"])
        if ks:
            moi.append({"name": x["ten"], "value": round(x["gia"][ks[-1]]),
                        "disp": f"${x['gia'][ks[-1]]:,.0f}"})
    if len(moi) < 10:
        return None
    moi = sorted(moi, key=lambda z: -z["value"])
    re_ = sorted(moi, key=lambda z: z["value"])[0]
    dan = [f"A typical home in {moi[0]['name']} is now {moi[0]['disp']}.",
           f"In {re_['name']} it is {re_['disp']}.",
           f"That is {moi[0]['value'] / max(1, re_['value']):.1f} times the price for the same idea of a house.",
           f"Fifty one states and territories, all measured the same way.",
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
    muc = [{"label": f"{x['ngay'][4:6]}/{x['ngay'][6:8]}", "emoji": "📈",
            "oddsDisp": _so(x["luot_doc"]),
            "logValue": round(math.log10(max(10, x["luot_doc"])), 3),
            "vo": f"{x['ngay'][4:6]} slash {x['ngay'][6:8]}. {x['luot_doc']:,} reads."}
           for x in buoc[:6]]
    if len(muc) < 4:
        return None
    dan = [f"{v['ten']}, one month of attention.", "From nobody looking, to everybody looking."]
    return (f"{_gon(v['ten'], 34)}: the spike", muc, dan)


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
    muc = []
    for n in nams:
        v = sum(theo_nam[n]) / len(theo_nam[n])
        muc.append({"label": str(n), "emoji": "📉", "oddsDisp": f"{v:,.1f}",
                    "logValue": round(math.log10(max(1.0, v)), 3),
                    "vo": f"{n}. {v:,.1f}."})
    if len(muc) < 4:
        return None
    nhan = ky.get("nhan") or "Index"
    return (f"{nhan} by year", muc,
            [f"{nhan}, six years in a row.", "Bureau of Labor Statistics. Not a forecast."])


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
    tieu_de, muc, dan = kq
    return _cong_an_toan({"title": tieu_de, "items": muc,
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
                       f"--props=./{os.path.relpath(pf, DS.ENG)}", "--gl=swiftshader",
                       "--concurrency=2", "--log=error"],
                      cwd=DS.ENG, timeout=2400, label=f"RankedShort({kenh['ten']})")
    ok, info = DS.qc(ra)
    print(f"{'✅' if ok else '❌'} {kenh['ten']} · {info}")
    if ok:
        lam_thumb(kenh, st, ra)
    return (ra, info) if ok else None


def chay_race(kenh: dict, ra: str = "", ky: dict | None = None) -> tuple[str, dict] | None:
    """Đua cột: dựng frames -> thu giọng từng câu -> ghép track + băng chữ -> render RaceShort."""
    import datastory_ci as DS
    st = dung_story_race(kenh, ky)
    if not st:
        return None
    sl = DS.slug(kenh["handle"].lstrip("@"))
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
             "accent": b.get("primary", "#F5B301"), "music": "music/carefree.mp3", "sfx": True,
             # 26/8 — phông riêng của kênh. Thiếu khoá này thì RaceShort rơi về Poppins và 7 kênh
             # dạng đua lại chung một khuôn chữ, dù JSON đã gán phông khác nhau cho từng kênh.
             "font": (kenh.get("brand") or {}).get("font", ""),
             **({"hookStat": _so_noi_bat(st)["stat"],
                 "hookLabel": _so_noi_bat(st).get("name", ""),
                 "hookLine": _cau_hoi_mo(kenh, st)} if _so_noi_bat(st).get("stat") else {})}
    pf = os.path.join(DS.PUB, f"_th2r_{sl}.json")
    json.dump(props, io.open(pf, "w", encoding="utf-8"), ensure_ascii=False)
    ra = os.path.abspath(ra or os.path.join(GOC, "out", f"th2r_{sl}.mp4"))
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    DS.run_render_cmd(["npx", "remotion", "render", "src/index.ts", "RaceShort", ra,
                       f"--props=./{os.path.relpath(pf, DS.ENG)}", "--gl=swiftshader",
                       "--concurrency=2", "--log=error"],
                      cwd=DS.ENG, timeout=2400, label=f"RaceShort({kenh['ten']})")
    ok, info = DS.qc(ra)
    print(f"{'✅' if ok else '❌'} {kenh['ten']} · {info}")
    if ok:
        lam_thumb(kenh, st, ra)
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
DUNG_STORY = {}      # nạp ở cuối file, sau khi mọi hàm đã định nghĩa


def chay_phim(kenh: dict, ra: str = "", ky: dict | None = None,
              keys=None) -> tuple[str, dict] | None:
    """Dạng phim kể: mỗi cảnh MỘT ảnh AI vẽ theo `style_anh` của kênh.

    Khác 6 dạng kia ở chỗ CẦN KEY vẽ ảnh. `build_doc_props(..., ai_only=True)` đã có sẵn chế độ
    100% ảnh AI với gu riêng — dùng lại, khỏi viết engine mới.
    Không có key thì trả None chứ không render ra video toàn khung trắng."""
    import datastory_ci as DS
    st = dung_story_cinematic(kenh, ky)
    if not st:
        return None
    keys = keys or []
    api = (keys[0].get("key") if keys else os.environ.get("GEMINI_API_KEY", "")) or ""
    if not api:
        print(f"   ⚠️ {kenh.get('ten')}: dạng phim kể cần key vẽ ảnh — bỏ lượt "
              f"(6 dạng còn lại không cần)")
        return None
    if keys:
        DS.set_ai_pool(keys, kenh["ten"])
    b = (kenh.get("brand") or {}).get("palette") or {}
    props = DS.build_doc_props(st, kenh["ten"], api_key=api,
                               accent=b.get("primary", "#22D3EE"),
                               accent2=b.get("accent", "#F5B301"),
                               font=(kenh.get("brand") or {}).get("font", ""),
                               handle=kenh["handle"],
                               ai_style=kenh.get("style_anh") or None, ai_only=True,
                               prefix="th2_")
    # Cùng lớp chặn "nền trơn" như ba đường Cinematic bên datastory_ci: đo trên KHUNG THẬT,
    # không đoán qua mô hình lớp phủ. Kênh chất liệu B/C vẽ ảnh bằng AI nên càng dễ ra khung tối
    # đều màu — đúng thứ QC loại sau khi đã tốn cả lượt vẽ lẫn lượt render.
    _that = DS.xac_minh_mo_dau(props, "CinematicShort", dark_ok=False)
    if _that:
        print(f"   ⚠️ {kenh['ten']}: mở đầu {_that} — bỏ lượt TRƯỚC render")
        return None
    sl = DS.slug(kenh["handle"].lstrip("@"))
    pf = os.path.join(DS.PUB, f"_th2_phim_{sl}.json")
    json.dump(props, io.open(pf, "w", encoding="utf-8"), ensure_ascii=False)
    ra = os.path.abspath(ra or os.path.join(GOC, "out", f"th2_phim_{sl}.mp4"))
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    DS.run_render_cmd(["npx", "remotion", "render", "src/index.ts", "CinematicShort", ra,
                       f"--props=./{os.path.relpath(pf, DS.ENG)}", "--gl=swiftshader",
                       "--concurrency=2", "--log=error"],
                      cwd=DS.ENG, timeout=2400, label=f"CinematicShort({kenh['ten']})")
    ok, info = DS.qc(ra)
    print(f"{'✅' if ok else '❌'} {kenh['ten']} [phim kể] · {info}")
    if ok:
        lam_thumb(kenh, st, ra, "CinematicShort", pf)
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
KHO_XOAY: dict[str, list] = {
    # Nhóm hàng của Open Food Facts (đã kiểm bằng gọi thật, xem du_lieu_mo.thanh_phan_off)
    "mon": ["breakfast-cereals", "pizzas", "sodas", "chocolates", "crisps", "biscuits",
            "energy-drinks", "ice-creams", "breads", "cheeses", "yogurts", "sauces"],
    # Năm ngân sách/thống kê: lùi dần, mỗi năm là một bộ số khác hẳn
    "nam": [_NAM_NAY - 1, _NAM_NAY - 2, _NAM_NAY - 3, _NAM_NAY - 4, _NAM_NAY - 5, _NAM_NAY - 6],
    # Cửa sổ ngày (số ngày lùi về trước) cho nguồn theo thời gian: thu hồi, thiên thạch, hồ sơ
    "ngay": [7, 14, 30, 60, 90, 180],
    "bang": ["California", "Texas", "Florida", "New York", "Pennsylvania", "Illinois",
             "Ohio", "Georgia", "North Carolina", "Michigan", "Arizona", "Washington"],
}


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
    return truc, list(KHO_XOAY.get(truc) or [])


def _tieu_de_da_lam(tieu_de: str, avoid) -> bool:
    """Tiêu đề này đã ra lò chưa. So sau khi bỏ dấu câu để "X in 2024" và "X In 2024." là một."""
    import re as _r
    g = lambda x: _r.sub(r"[^a-z0-9 ]", "", str(x or "").lower()).strip()
    t = g(tieu_de)
    return bool(t) and any(g(a) == t for a in (avoid or []))


def chay_chung(kenh: dict, ra: str = "", ky: dict | None = None,
               avoid: list | None = None) -> tuple[str, dict] | None:
    """Dựng + render cho MỌI dạng. Trả (đường dẫn, QC) hoặc None nếu bỏ lượt.

    `avoid` = tiêu đề các video kênh này ĐÃ làm. Thiếu nó thì kênh lặp lại đúng một câu chuyện
    mãi mãi — xem khối XOAY VÒNG ĐỀ TÀI ở trên."""
    import datastory_ci as DS
    dang = kenh.get("dinh_dang")
    if dang == "race":
        return chay_race(kenh, ra, ky)
    if dang == "cinematic":
        return chay_phim(kenh, ra, ky)
    comp, ten_props = DUONG_RA.get(dang, (None, None))
    if not comp or not ten_props:
        print(f"   ⚠️ {kenh.get('ten')}: dạng '{dang}' chưa có đường render chung")
        return None
    st = _dung_story_xoay(dang, kenh, ky, avoid)
    if not st:
        return None
    sl = DS.slug(kenh["handle"].lstrip("@"))
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
    pf = os.path.join(DS.PUB, f"_th2_{dang}_{sl}.json")
    json.dump(props, io.open(pf, "w", encoding="utf-8"), ensure_ascii=False)
    ra = os.path.abspath(ra or os.path.join(GOC, "out", f"th2_{dang}_{sl}.mp4"))
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    DS.run_render_cmd(["npx", "remotion", "render", "src/index.ts", comp, ra,
                       f"--props=./{os.path.relpath(pf, DS.ENG)}", "--gl=swiftshader",
                       "--concurrency=2", "--log=error"],
                      cwd=DS.ENG, timeout=2400, label=f"{comp}({kenh['ten']})")
    ok, info = DS.qc(ra)
    print(f"{'✅' if ok else '❌'} {kenh['ten']} [{dang}] · {info}")
    if ok:
        lam_thumb(kenh, st, ra, comp, pf)
    return (ra, info) if ok else None



def _dung_story_xoay(dang: str, kenh: dict, ky: dict | None, avoid: list | None) -> dict | None:
    """Dựng story, XOAY qua kho đề tài cho tới khi ra một chuyện CHƯA LÀM.

    Trục xoay đầu tiên thử luôn tham số gốc của kênh (giữ đúng ý thiết kế), rồi mới đi kho."""
    dung = DUNG_STORY.get(dang)
    if not dung:
        return None
    truc, kho = _kho_xoay_cua(kenh)
    thu = [dict(ky or {})]                       # lượt 0: đúng tham số gốc
    if truc and kho:
        thu += [{**(ky or {}), truc: v} for v in kho]
    da_thay = None
    for i, t in enumerate(thu):
        st = dung(kenh, t)
        if not st:
            continue
        da_thay = da_thay or st
        if not _tieu_de_da_lam(st.get("title"), avoid):
            if i:
                print(f"   ♻️ {kenh.get('ten')}: đề tài gốc đã làm rồi — xoay `{truc}` sang "
                      f"`{t.get(truc)}` ({i}/{len(thu) - 1})")
            return st
    if da_thay:
        print(f"   ⚠️ {kenh.get('ten')}: hết kho `{truc or 'không có trục'}` mà đề tài nào cũng "
              f"đã làm rồi — BỎ LƯỢT, không đăng trùng.")
    return None



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
        for k in ks:
            v = (d or {}).get(k)
            if v not in (None, "", 0):
                return v
        return ""
    it = st.get("items") or []
    if it:
        return {"stat": str(_g(it[0], "stat", "disp", "oddsDisp")),
                "name": str(_g(it[0], "name", "label", "state"))}
    fr = st.get("frames") or []
    if fr:
        d = (fr[-1].get("data") or [{}])[0]
        v = d.get("value")
        so = f"{v:,.0f}" if isinstance(v, (int, float)) else str(v or "")
        don = str(st.get("unit") or "")
        return {"stat": (so + (" " + don if don and len(don) <= 6 else "")).strip(),
                "name": str(d.get("name") or "")}
    da = st.get("data") or []
    if da:
        return {"stat": str(_g(da[0], "disp", "value")), "name": str(_g(da[0], "state", "name"))}
    pa = st.get("pairs") or []
    if pa:
        return {"stat": str(_g(pa[-1], "nowVal", "nowDisp")),
                "name": str(_g(pa[-1], "label", "name", "nowYear"))}
    h = st.get("hook") or {}
    if h:
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



def chay_bo(kenh: dict, ra_long: str = "", avoid: list | None = None,
            so_short: int = 3) -> tuple[str, list] | None:
    """MỘT BỘ = 1 LONG + `so_short` SHORT, short là CÁC CHƯƠNG CỦA CHÍNH LONG ĐÓ.

    26/8 — anh nêu yêu cầu này nhiều lần, và mỗi lần em lại đi làm việc khác. Ghi rõ ở đây để
    không phải nói lại:
      • tỉ lệ 1 long : 3 short;
      • 3 short **cắt từ long ra**, dựng lại theo khổ dọc cho hợp nền tảng — không phải 3 video
        rời rạc về 3 chủ đề khác nhau;
      • đánh số để khâu đăng đăng từ nhỏ tới lớn, và short LUÔN đi kèm long của nó.

    Cách làm: xoay kho đề tài lấy `so_short` chương KHÁC NHAU nhưng CÙNG một mạch (cùng kênh, cùng
    nguồn) -> render mỗi chương thành một short hoàn chỉnh -> **nối các chương lại thành long**.
    Nối chứ không render riêng bản dài: như vậy short đúng nghĩa là một đoạn của long, khớp 100%,
    và không tốn thêm một lượt gọi AI nào.

    Trả `(đường_long, [(đường_short, story), ...])`, hoặc None nếu không đủ dữ liệu."""
    import datastory_ci as DS
    ten = kenh.get("ten", "?")
    dang = kenh.get("dinh_dang")
    da = list(avoid or [])
    chuong = []
    for i in range(max(1, so_short)):
        st = _dung_story_xoay(dang, kenh, None, da)
        if not st:
            break
        da.append(st.get("title") or "")
        sl = DS.slug(kenh["handle"].lstrip("@")) + f"_c{i + 1}"
        ra_s = os.path.abspath(os.path.join(GOC, "out", f"th2bo_{sl}.mp4"))
        kq = chay_chung(kenh, ra=ra_s, avoid=da[:-1])
        if not kq:
            print(f"   ⚠️ {ten}: chương {i + 1} không dựng được — bỏ chương này")
            continue
        chuong.append((kq[0], st))
    if not chuong:
        print(f"   ⚠️ {ten}: không dựng được chương nào — BỎ LƯỢT")
        return None
    if len(chuong) < so_short:
        print(f"   ⚠️ {ten}: chỉ dựng được {len(chuong)}/{so_short} chương "
              f"(kho đề tài cạn hoặc nguồn thiếu) — vẫn ra bộ, long ngắn hơn.")
    ra_long = os.path.abspath(ra_long or os.path.join(
        GOC, "out", f"th2long_{DS.slug(kenh['handle'].lstrip('@'))}.mp4"))
    if not _noi_video([c[0] for c in chuong], ra_long):
        return None
    print(f"   🎬 {ten}: BỘ = 1 long ({len(chuong)} chương) + {len(chuong)} short")
    return ra_long, chuong


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
        return 0 if chay_chung(k, ky=MOI.get(k["ham"], {})) else 4
    return 0


DUNG_STORY.update({"ranked": dung_story_ranked, "race": dung_story_race,
                   "cinematic": dung_story_cinematic, "scaled": dung_story_scaled,
                   "mapped": dung_story_mapped, "longshot": dung_story_longshot,
                   "thennow": dung_story_thennow})


if __name__ == "__main__":
    sys.path.insert(0, GOC)
    sys.exit(main())
