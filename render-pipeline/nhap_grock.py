#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RÚT 10 KÊNH TỪ GÓI GROCK 2500 -> `kho_grock.json`  (1/9/2026)

Anh gửi thư mục `GROCK PROMPT 2500`: 10 tệp, mỗi tệp 2.500 prompt Kling cho MỘT kênh.
Ta không dùng Kling (không nằm trong đường chạy tự động) — dùng engine truyện tranh sẵn có,
đúng cách đã làm HOUSE RULES.

CẤU TRÚC MỘT PROMPT (khác gói cũ: thoại nằm trong VĂN XUÔI, không có dòng thời gian):

    0001 — Midnight Snack Busted
    GLOBAL CHARACTER LOCK: <5 dòng, mỗi dòng một vai>
    VISUAL LOCK / AUDIO LOCK
    SCENE AND DIALOGUE:
      Derek opens the fridge at 1 AM holding a massive sandwich. Derek whispers, "Just water."
      Amy appears behind him and says, "That sandwich has a name." Derek freezes.
    DIRECTOR LOCK: ...

Rút ra: câu MỞ (hình) · các lượt thoại có tên vai · câu CHỐT (hình, sau lời cuối).
Khớp đúng khuôn ba nhịp của HOUSE RULES: hai panel thoại + một panel lật giữ hình, tổng 6 giây.

**Chỉ khớp tên vai lấy từ CHARACTER LOCK.** Bản dò đầu bắt bừa mọi từ viết hoa đứng trước dấu
nháy, nên ra cả "Hey", "You", "The" như thể chúng là nhân vật — và mỗi cái như thế là một tập
có vai không tồn tại.
"""
import io
import json
import os
import re

GOC = os.path.dirname(os.path.abspath(__file__))
NGUON = os.path.expanduser("~/Downloads/GROCK PROMPT 2500")
RA = os.path.join(GOC, "kho_grock.json")

# tệp -> (mã kênh, tên hiện ra, người hay phi nhân)
KENH = {
    "2500_NewChannel_ModernFamily": ("modernfam", "HOUSE OF FOUR", "nguoi"),
    "2500_Channel3_KevinLaura":     ("kevinlaura", "TWO KIDS ONE HOUSE", "nguoi"),
    "2500_Channel4_MarcusSofia":    ("marcussofia", "THE LOUD HOUSE RULES", "nguoi"),
    "2500_Channel5_EthanMaya":      ("ethanmaya", "GRANDMA KNOWS", "nguoi"),
    "2500_Channel6_ChrisAngela":    ("chrisangela", "TEEN VS DAD", "nguoi"),
    "2500_Kling_6s_Funny_USA":      ("houserules", "HOUSE RULES", "nguoi"),
    "2500_Channel7_Anthropomorphic": ("thurung", "CRITTER HOUSE", "thu"),
    "2500_Channel8_MonsterFamily":  ("quaivat", "MONSTER CHORES", "quai"),
    "2500_Channel9_RobotFamily":    ("robot", "UNIT FAMILY", "robot"),
    "2500_Channel10_AlienFamily":   ("alien", "PLANET PARENTS", "alien"),
}

# Bảng màu: gói mô tả quần áo bằng CHỮ ("gray t-shirt, blue jeans"), engine cần MÃ HEX. Chọn
# tông hơi trầm và hơi ngả pastel để hợp nét mực dày của engine — màu bão hoà cao đặt cạnh viền
# đen 7px sẽ chói và làm mặt nhân vật chìm đi.
MAU = {
    "gray": "#8C9095", "grey": "#8C9095", "blue": "#3A5C93", "light-blue": "#7FA8D4",
    "navy": "#22375C", "red": "#C4453A", "green": "#3E8F5E", "teal": "#2F7D8A",
    "yellow": "#E8B93C", "orange": "#D9793C", "purple": "#6B4A93", "lavender": "#9B87C4",
    "pink": "#D98BA6", "coral": "#E0715E", "white": "#F1EEE7", "black": "#2A2A2E",
    "brown": "#7A5638", "khaki": "#C2A778", "silver": "#B9BDC2", "gold": "#C9A24B",
    "golden": "#C9A24B", "denim": "#4A6A96", "cream": "#EDE3CE", "dark": "#3A3D42",
    "beige": "#D8C7A9", "maroon": "#7B3B3B", "olive": "#6E7A46", "mint": "#8FC4A8",
}
# thứ mặc trên thân · dưới thân — để biết màu nào là áo, màu nào là quần
_TREN = r"(t-shirt|shirt|top|sweater|hoodie|cardigan|polo|blouse|jacket|vest|sweatshirt|shawl|dress)"
_DUOI = r"(jeans|pants|shorts|leggings|skirt|trousers|slacks)"


def _mau_cua(mo: str, dau: str) -> str:
    """Màu của món đồ (áo hoặc quần) đọc từ câu mô tả vai."""
    for m in re.finditer(rf"([a-z-]+(?:\s+[a-z-]+)?)\s+{dau}", mo):
        for tu in reversed(m.group(1).split()):
            if tu in MAU:
                return MAU[tu]
    return ""


# gợi ý giới/tuổi từ chính dòng mô tả vai
_TUOI = [(r"\b(\d{1,2})-year-old\b", None), (r"\belderly\b", "gia"), (r"\badult\b", "trung")]


def _vai_tu_lock(than: str) -> dict:
    """Đọc khối CHARACTER LOCK -> {tên: {gioi, tuoi, cao, ao, quan, toc}}."""
    m = re.search(r"GLOBAL CHARACTER LOCK[^\n]*\n([\s\S]+?)\nKeep exact", than)
    if not m:
        return {}
    ra = {}
    for d in m.group(1).splitlines():
        d = d.strip()
        mm = re.match(r"([A-Z][\w-]*):\s*(.+)", d)
        if not mm:
            continue
        ten, mo = mm.group(1), mm.group(2).lower()
        # tuổi
        tuoi, so = "trung", 0
        gt = re.search(r"(\d{1,2})-year-old", mo)
        if gt:
            so = int(gt.group(1))
            tuoi = "tre_con" if so <= 12 else ("tre" if so <= 19 else "trung")
        elif "elderly" in mo:
            tuoi = "gia"
        # GIỚI — đọc từ mô tả, và khi mô tả KHÔNG nói thì đọc từ TÊN.
        # 1/9: `Nana` (bà cú, CRITTER HOUSE) mô tả là "elderly anthropomorphic owl… floral shawl
        # over a light blouse" — không có một từ chỉ giới nào, nên bản đầu xếp vào "nam" và bà
        # sẽ được lồng giọng ông. Anh đã dặn riêng chuyện này: *"bà giọng bà"*. Váy/khăn/áo
        # blouse là chỉ dấu, và tên gọi trong nhà (nana, grandma, mama) là chỉ dấu chắc hơn nữa.
        gioi = "nam"
        if re.search(r"\b(woman|female|girl|mom|mother|grandma|granny|wife|sister|daughter|aunt|she|her)\b", mo):
            gioi = "nu"
        elif re.search(r"\b(blouse|dress|skirt|shawl|cardigan)\b", mo):
            gioi = "nu"
        elif ten.lower() in ("nana", "granny", "gran", "mama", "mimi", "abuela", "vexa", "circuit", "luna", "mira"):
            gioi = "nu"

        # THÚ CƯNG — không phải vai diễn. Chó/mèo của gia đình không có tuổi, không mặc quần áo,
        # và engine không vẽ được chúng. Xếp nhầm chúng thành người lớn thì một tập có chó nói
        # sẽ dựng ra một người đàn ông lạ đứng trong bếp.
        # Kênh CRITTER HOUSE thì MỌI vai đều là thú, nên chỉ loại khi vai vừa không có tuổi vừa
        # không mặc gì.
        la_thu = (not gt and "elderly" not in mo
                  and not re.search(_TREN + "|" + _DUOI, mo))
        if tuoi == "tre_con":
            gioi_ve = "tre"
        else:
            gioi_ve = gioi
        # chiều cao theo QUAN HỆ THẬT trong nhà — anh đã dặn: con thấp hơn mẹ, vợ thường thấp
        # hơn chồng. Suy từ tuổi chứ không bịa.
        cao = ({"tre_con": 0.70 if so and so <= 9 else 0.78, "tre": 0.90,
                "gia": 0.95, "trung": 1.00}[tuoi])
        if tuoi == "trung" and gioi == "nu":
            cao = 0.94
        ra[ten] = {"gioi": gioi_ve, "gioiThat": gioi, "tuoi": tuoi, "cao": cao, "thu": la_thu,
                   "so_tuoi": so,
                   "ao": _mau_cua(mo, _TREN) or "#8C9095",
                   "quan": _mau_cua(mo, _DUOI) or "#3A3D42",
                   "mo": mo[:150]}
    return ra


def main() -> int:
    if not os.path.isdir(NGUON):
        print(f"❌ không thấy {NGUON}")
        return 1
    kho = {}
    for t in sorted(os.listdir(NGUON)):
        if not t.endswith(".txt"):
            continue
        # KHỚP THEO TIỀN TỐ, không cắt đuôi. Mười tệp đặt tên không cùng khuôn:
        # `..._Channel3_KevinLaura_6s_Prompts.txt` và `..._Kling_6s_Funny_USA_Prompts.txt` —
        # cắt `_6s_Prompts.txt` thì trượt cái sau, cắt `_Prompts.txt` thì trượt cái trước. Hai
        # lần sửa đều bỏ SÓT một tệp mà không báo gì, vì `continue` im lặng.
        goc = next((k for k in KENH if t.startswith(k)), "")
        if not goc:
            print(f"  ⏭ bỏ qua {t} (chưa khai trong bảng KENH)")
            continue
        de, ten_kenh, loai = KENH[goc]
        s = io.open(os.path.join(NGUON, t), encoding="utf-8", errors="ignore").read()
        khoi = re.split(r"\n(\d{4}) — ", s)[1:]
        cap = list(zip(khoi[0::2], khoi[1::2]))
        if not cap:
            continue

        dan = _vai_tu_lock(cap[0][1])
        ten_vai = sorted(dan.keys(), key=len, reverse=True)   # tên dài trước, tránh khớp lồng
        tap = []
        for so, than in cap:
            m = re.search(r"SCENE AND DIALOGUE:\s*\n(.+)", than)
            if not m:
                continue
            canh = m.group(1).strip()
            # chỉ nhận lượt thoại có tên vai THẬT
            thoai = []
            for mm in re.finditer(r'"([^"]+)"', canh):
                truoc = canh[max(0, mm.start() - 90):mm.start()]
                ai = next((v for v in ten_vai if re.search(rf"\b{re.escape(v)}\b", truoc)), "")
                if ai:
                    thoai.append([mm.group(1).replace("’", "'"), ai])
            if not thoai:
                continue
            # câu CHỐT = phần văn xuôi sau dấu nháy cuối cùng (hành động, không lời)
            cuoi = canh[canh.rfind('"') + 1:].strip(" .,") or ""
            tap.append({"so": int(so), "ten": than.split("\n")[0].strip(),
                        "hook": canh[:canh.find('"')].strip()[:120],
                        "loi": thoai[:3], "lat": cuoi[:110]})
        kho[de] = {"ten": ten_kenh, "loai": loai, "dan": dan, "tap": tap}
        n2 = sum(1 for x in tap if len(x["loi"]) >= 2)
        print(f"  {ten_kenh:22s} {len(tap):5d} tập ({n2} có ≥2 thoại) · dàn {len(dan)}: "
              f"{', '.join(list(dan)[:5])}")

    io.open(RA, "w", encoding="utf-8").write(json.dumps(kho, ensure_ascii=False))
    print(f"\n  ✅ {len(kho)} kênh · {sum(len(v['tap']) for v in kho.values())} tập -> kho_grock.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
