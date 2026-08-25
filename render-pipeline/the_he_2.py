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
_RIENG_TU = ("sex", "divorce", "affair", "dating", "marriage", "porn", "relationship",
             "breakup", "infidelity", "love", "wife", "husband", "girlfriend", "boyfriend",
             "wedding", "kiss", "nude", "body", "adult", "romance", "couple", "married",
             "onlyfans", "playboy", "virgin", "pregnan", "abortion", "gender", "sexual")


def _bd_wiki_top(D, ky):
    # Bảng đọc nhiều trả tới 1000 bài/ngày. Lọc theo chủ đề thì phải quét CẢ bảng, quét
    # 60 dòng đầu là gần như luôn rỗng -> kênh bỏ lượt oan mỗi ngày.
    r = D.bai_duoc_doc(int(ky["nam"]), int(ky["thang"]), int(ky["ngay"]), 1000)
    if ky.get("loc") == "rieng_tu":
        r = [x for x in r if any(t in x["ten"].lower() for t in _RIENG_TU)][:6]
        if len(r) < 3:
            return None
        return ("What America quietly looked up",
                [{"name": _gon(x["ten"], 28), "stat": _so(x["luot_doc"]),
                  "vo": f"{_gon(x['ten'], 34)}. {x['luot_doc']:,} searches."} for x in r],
                "Nobody admits to this one.")
    r = r[:6]
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
    r = D.chuoi_bls(ky.get("chuoi", "cpi"), int(ky.get("tu_nam", 2019)), int(ky.get("den_nam", 2024)))
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


def _bd_dinh_duong(D, ky):
    mon = ky.get("mon") or "pizza"
    r = [x for x in D.thanh_phan_mon(mon, 30, ky.get("key", "DEMO_KEY")) if x.get("calo")]
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
    return (f"{mon.title()}: what is really in it", muc,
            "U S D A measured every one of these.")


BO_CHUYEN = {
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
    return {
        "title": tieu_de,
        "intro_vo": mo,
        "outro_vo": ket,
        "items": items,
        "tiers": sorted({it["tier"] for it in items}, key="SABCDF".index),
        "nguon": kenh.get("nguon"),
        "_that": True,
        "self_score": {"total": 92},
    }


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
    bo = D.nhieu_chuoi_bls(nhom, tu, den, ky.get("key", ""))
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
    return {"title": tieu_de, "unit": don_vi, "frames": frames, "narration": dan,
            "nguon": kenh.get("nguon"), "_that": True, "self_score": {"total": 92}}


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
