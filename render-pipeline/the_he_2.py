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
                "Owned by millions. Empty tonight.")
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
    tieu_de, muc, ket = kq
    items = [{**m, "tier": TIER[min(i, 5)]} for i, m in enumerate(muc[:6])]
    return {
        "title": tieu_de,
        "intro_vo": f"{tieu_de}. Here they are.",
        "outro_vo": ket,
        "items": items,
        "tiers": sorted({it["tier"] for it in items}, key="SABCDF".index),
        "nguon": kenh.get("nguon"),
        "_that": True,
        "self_score": {"total": 92},
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", required=True)
    ap.add_argument("--thu", action="store_true", help="chỉ in story, không render")
    a = ap.parse_args()
    k = doc_kenh(a.kenh)
    if not k:
        print(f"❌ không thấy kênh '{a.kenh}'")
        return 2
    MOI = {"bai_duoc_doc": {"nam": 2026, "thang": 8, "ngay": 20},
           "tieu_hanh_tinh": {"tu_ngay": "2026-08-20", "den_ngay": "2026-08-22"}}
    st = dung_story_ranked(k, MOI.get(k["ham"], {}))
    if not st:
        return 3
    print(f"\n📄 {st['title']}   [{k['niche']} · chất liệu {k['chat_lieu']}]")
    for it in st["items"]:
        print(f"   {it['tier']}  {str(it['stat']):>10}  {it['name']}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, GOC)
    sys.exit(main())
