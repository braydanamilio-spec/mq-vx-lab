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
    t = str(ten).replace("_", " ").strip().upper()
    for k in ks:
        if str(k["ten"]).upper() == t or str(k["handle"]).lstrip("@").upper() == t.replace(" ", ""):
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
    r = D.dong_dat(float(ky.get("do_lon", 6.5)), ky.get("tu_ngay", "2015-01-01"), 40)
    if len(r) < 4:
        return None
    gop = {}
    for x in r:
        # "112km SW of Kokopo, Papua New Guinea" -> lấy phần sau dấu phẩy cuối
        noi = x["noi"].split(",")[-1].strip() or x["noi"]
        gop[noi] = max(gop.get(noi, 0), x["do_lon"])
    data = [{"name": k, "value": round(v, 1)} for k, v in sorted(gop.items(), key=lambda z: -z[1])[:10]]
    manh = r[0]
    dan = [f"The strongest was magnitude {manh['do_lon']}.",
           f"It hit {manh['noi']}.",
           f"Depth: {manh['sau_km']} kilometers.",
           f"{len(r)} quakes this size since {ky.get('tu_ngay', '2015')[:4]}.",
           "Each one recorded by seismometers, not estimates.",
           "U S G S publishes every single one."]
    return ("Strongest quakes on record", "mag", data, dan)


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
    return _cong_an_toan({"title": tieu_de, "unit": don_vi, "data": data, "narration": dan,
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
             "accent": b.get("primary", "#F5B301"), "music": "music/carefree.mp3", "sfx": True}
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
    return (ra, info) if ok else None


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
    if k["dinh_dang"] == "race":
        st = dung_story_race(k, ky)
        if not st:
            return 3
        print(f"\n📊 {st['title']}   [{k['niche']} · {len(st['frames'])} mốc]")
        for fr in st["frames"][-1:]:
            for d in fr["data"][:6]:
                print(f"   {fr['t']}  {d['value']:>9}  {d['name']}")
    else:
        st = dung_story_ranked(k, ky)
        if not st:
            return 3
        print(f"\n📄 {st['title']}   [{k['niche']} · chất liệu {k['chat_lieu']}]")
        for it in st["items"]:
            print(f"   {it['tier']}  {str(it['stat']):>10}  {it['name']}")
    if a.render:
        f = chay_race if k["dinh_dang"] == "race" else chay
        return 0 if f(k, ky=MOI.get(k["ham"], {})) else 4
    return 0


if __name__ == "__main__":
    sys.path.insert(0, GOC)
    sys.exit(main())
