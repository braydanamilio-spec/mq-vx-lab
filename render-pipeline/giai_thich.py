#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PHIM GIẢI THÍCH — 10 kênh Mỹ, dựng từ số đo hai video tham chiếu.  (1/9/2026)

── VÌ SAO MỌI CON SỐ ĐỀU TÍNH BẰNG CODE ────────────────────────────────────────────────────
Kịch bản của hệ này do AI viết và chạy không người canh trên GitHub. Với kênh hài thì AI bịa
một chi tiết cũng chỉ là kém buồn cười. Với kênh GIẢI THÍCH thì AI bịa một con số là kênh chết:
người xem Mỹ soi rất kỹ, và YouTube phạt nặng nội dung sai.

Nên mười kênh này được chọn theo đúng một tiêu chí: **nội dung PHẢI tính ra được**, không phải
tra ra được. "Đi bộ lên Mặt Trăng mất bao lâu" là phép chia quãng đường cho vận tốc — hằng số
nào cũng tra được ở sách giáo khoa và không đổi. "Năm 1970 một ổ bánh mì giá bao nhiêu" thì
phải tra, và tra sai thì không ai biết cho tới lúc kênh bị gắn cờ.

Đây là lý do slate này KHÔNG có kênh tài chính cá nhân hoá và KHÔNG có kênh tư vấn pháp lý,
dù hai thứ ấy RPM cao nhất ($10-25 và $25-60 CPM). Sai một lần là mất kênh.

── NHỊP CẮT ────────────────────────────────────────────────────────────────────────────────
Đo trên hai video anh gửi: trung vị 2,1 giây, không cảnh nào quá 7 giây, ≈26 cắt/phút.
Điều này KHÔNG phải là việc của bộ dựng — nó là việc của bộ VIẾT. Nhịp cắt 2,1 giây có nghĩa
mỗi câu chỉ được dài 5-8 chữ. Viết câu dài rồi mong bộ dựng cắt nhanh là bất khả.
Cổng `kiem_nhip.py` đo lại điều đó trên danh sách nhịp, trước khi tốn một giây render nào.

── SHORT CẮT RA TỪ LONG ────────────────────────────────────────────────────────────────────
Anh: *"mỗi long chọn ra tổng hợp 2-3 cái hay nhất dựng làm short."* Nên mỗi nhịp tự khai `dinh`.
Bộ cắt short lấy các dải nhịp đỉnh liền nhau, dùng lại đúng tiếng đã đọc — không sinh lại.
"""
import argparse
import io
import json
import os
import subprocess

GOC = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(os.path.dirname(GOC), "engine-remotion")
PUB = os.path.join(ENG, "public")

from kich_hai import doc_hai_giong, lam_thumb              # noqa: E402
from chuan_am import chuan                                  # noqa: E402

NHAC = ["music/mind_pad32.mp3", "music/km_ascending.mp3", "music/forecast.mp3",
        "music/inspired.mp3", "music/mindloop_pad.mp3", "music/broke_pad.mp3",
        "music/km_interloper.mp3", "music/carefree.mp3", "music/km_undaunted.mp3",
        "music/km_impact_andante.mp3"]

# ── HẰNG SỐ ĐỜI THẬT ────────────────────────────────────────────────────────────────────────
# Chỉ những hằng số tra được ở sách giáo khoa và không đổi theo năm. Không có giá cả, không có
# thuế suất, không có dân số — ba thứ đổi hằng năm và là chỗ mọi kênh giải thích chết vì sai.
DI_BO_KMH = 5.0            # tốc độ đi bộ người lớn
CHAY_KMH = 12.0
XE_KMH = 100.0
MAY_BAY_KMH = 900.0
AS_KMS = 299792.458        # tốc độ ánh sáng km/s

QUANG_DUONG = [
    ("the Moon",            384400,   "trai_dat"),
    ("the Sun",           149600000,  "trai_dat"),
    ("Mars at its closest", 54600000, "trai_dat"),
    ("around the Earth",    40075,    "trai_dat"),
    ("New York to Los Angeles", 3936, "xe"),
    ("the bottom of the Mariana Trench", 11,  "trai_dat"),
    ("the top of Mount Everest",         8.8, "cay"),
]

CO_LON = [
    ("a blue whale",        30.0, "m", "cay"),
    ("a school bus",        11.0, "m", "xe"),
    ("a giraffe",            5.5, "m", "cay"),
    ("an adult human",       1.7, "m", "nguoi"),
    ("a Boeing 747",        70.6, "m", "xe"),
    ("the Statue of Liberty", 93.0, "m", "nha"),
    ("Mount Everest",     8848.0, "m", "cay"),
]

THOI_QUEN = [
    ("a $6 coffee every morning",      6.00, 365, "coc"),
    ("a $15 streaming subscription",  15.00,  12, "dien_thoai"),
    ("a $12 lunch every workday",     12.00, 260, "hop"),
    ("a $4 energy drink daily",        4.00, 365, "coc"),
    ("a $90 phone plan",              90.00,  12, "dien_thoai"),
]


def _tien(v: float) -> str:
    """Số tiền viết theo lối người Mỹ đọc lướt: 1.2M, 47K, $940."""
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M".replace(".0M", "M")
    if v >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:,.0f}"


def _lau(gio: float) -> tuple:
    """Đổi số giờ thành (con số, đơn vị) mà tai người nghe ra được ngay.

    Không bao giờ nói "3.372.000 giờ" — con số ấy không gợi ra gì. Bộ não người đo thời gian
    bằng đơn vị nó SỐNG QUA: ngày, tháng, năm. Đây là bài học rút từ video tham chiếu: họ không
    đưa số tuyệt đối, họ đưa số ĐÃ QUY VỀ thứ người xem có sẵn trong đầu.

    ── VÌ SAO VIẾT LẠI (1/9, lần thứ ba) ────────────────────────────────────────────────────
    Soi khung bắt được "0 MINUTES" trên màn hình (ánh sáng tới Mặt Trăng, thật ra 1,3 giây).
    Tôi vá bằng cách thêm nhánh GIÂY. Chạy lại: rãnh Mariana ra "0 SECONDS" (thật ra 37 phần
    triệu giây). Cùng một lỗi, lùi xuống đúng một bậc — tức bản vá chỉ đẩy lỗi đi chứ không
    diệt nó. Đây đúng dấu hiệu "đang vá triệu chứng" mà CLAUDE.md mô tả: sửa vòng thứ hai mà
    vẫn cùng một họ lỗi.

    Gốc rễ: bảng nhánh cố định luôn có một đáy, và dưới đáy ấy mọi thứ làm tròn thành 0. Nên
    bỏ bảng nhánh, CHỌN ĐƠN VỊ theo nguyên tắc: lấy đơn vị lớn nhất mà con số vẫn ≥ 1.
    Không còn đáy thì không còn chỗ cho số 0 xuất hiện."""
    giay = gio * 3600
    BAC = [(1e-3, "milliseconds", 1000.0), (1.0, "seconds", 1.0), (60.0, "minutes", 1 / 60),
           (3600.0, "hours", 1 / 3600), (86400.0, "days", 1 / 86400),
           (2629800.0, "months", 1 / 2629800), (31557600.0, "years", 1 / 31557600),
           (3155760000.0, "centuries", 1 / 3155760000)]
    ten, he = BAC[0][1], BAC[0][2]
    for nguong, t2, h2 in BAC:
        if giay >= nguong:
            ten, he = t2, h2
    v = giay * he
    if v >= 100:
        chu = f"{v:,.0f}"
    elif v >= 10:
        chu = f"{v:.0f}"
    else:
        chu = f"{v:.1f}".rstrip("0").rstrip(".")
    if chu in ("0", "") or float(chu.replace(",", "")) < 0.05:
        # Không bao giờ để một con số hiện ra là 0. Thà nói "dưới một phần nghìn giây".
        return "under 1", "millisecond"
    return chu, (ten if not chu.startswith("1 ") and chu != "1" else ten.rstrip("s"))



# ══ MƯỜI KÊNH ═══════════════════════════════════════════════════════════════════════════════
# Chọn theo RPM Mỹ (tra 1/9/2026) NHÂN với độ an toàn về sự thật. Kênh RPM cao nhất mà rủi ro
# cao thì không lấy — xem đầu tệp.
KENH = [
    {"ma": "howlong",   "ten": "HOW LONG WOULD IT TAKE", "mau": "#D9622B", "phu": "#2F6E8A", "sinh": "howlong"},
    {"ma": "howbig",    "ten": "HOW BIG IS IT REALLY",   "mau": "#2F7D8A", "phu": "#C9552F", "sinh": "howbig"},
    {"ma": "realcost",  "ten": "THE REAL COST",          "mau": "#2E7D5B", "phu": "#B4523A", "sinh": "realcost"},
    {"ma": "howmuch",   "ten": "HOW MUCH IS A BILLION",  "mau": "#6B4A93", "phu": "#C98A2E", "sinh": "howmuch"},
    {"ma": "whatif",    "ten": "WHAT IF EVERYONE",       "mau": "#B4523A", "phu": "#2F7D8A", "sinh": "whatif"},
    {"ma": "survive",   "ten": "COULD YOU SURVIVE",      "mau": "#8A3F2E", "phu": "#4E7C4A", "sinh": "survive"},
    {"ma": "dayinlife", "ten": "A DAY IN THE LIFE OF",   "mau": "#9A6B34", "phu": "#3E6E8C", "sinh": "dayinlife"},
    {"ma": "wheregoes", "ten": "WHERE DOES IT GO",       "mau": "#3E7FB0", "phu": "#C9762F", "sinh": "wheregoes"},
    {"ma": "therules",  "ten": "THE RULES NOBODY READS", "mau": "#C9552F", "phu": "#4E7C4A", "sinh": "therules"},
    {"ma": "speedof",   "ten": "THE SPEED OF EVERYTHING","mau": "#2F6E8A", "phu": "#D9622B", "sinh": "speedof"},
]

VAI_KE = {"gioi": "nam", "tuoi": "trung", "toc": "bu", "mauToc": "#5A3E28",
          "ao": "#8A6A46", "quan": "#6E5A3E", "pk": [], "cao": 1.0, "ten": "narrator"}


# ── NƠI CHỐN ĐỌC RA TỪ CHÍNH LỜI KỂ ─────────────────────────────────────────────────────────
# Anh: *"nhớ vẽ đúng bối cảnh như lời thoại sub nha."*
# Bản đầu em đặt tay `noi="san_vuon"` cho gần hết các nhịp, nên lời nói về Mặt Trăng mà hình là
# cái sân sau có cây với thùng rác. Nay nơi chốn SUY RA TỪ LỜI, và câu nào trừu tượng (nói về
# con số, về vũ trụ, về ý niệm) thì KHÔNG dựng phòng ốc gì cả — dựng nền trơn.
# Nền trơn không phải là bỏ cuộc: một câu về tốc độ ánh sáng đặt trong phòng khách còn tệ hơn
# nhiều so với đặt trên nền phẳng, vì phòng khách nói một điều SAI về nội dung câu ấy.
NOI_TU_LOI = [
    ("bep",         r"\b(kitchen|coffee|cook\w*|eat|lunch|food|meal|fridge|cup|drink)\b"),
    ("phong_khach", r"\b(couch|sofa|living room|tv|home|house|sit\w*|watch\w*)\b"),
    ("duong",       r"\b(street|road|drive|car|walk\w* to work|commute|city|town|trip)\b"),
    ("san_vuon",    r"\b(outside|walk\w*|field|tree|garden|yard|ground|desert|ice age|winter)\b"),
    ("cua_hang",    r"\b(shop|store|buy|bought|purchase|subscription|bill)\b"),
    ("hanh_lang",   r"\b(hall\w*|corridor|door|office)\b"),
    ("giat",        r"\b(laundry|wash\w*|bin|recycl\w*|trash|throw away)\b"),
]


def _noi(loi: str) -> str:
    import re
    for ten, rx in NOI_TU_LOI:
        if re.search(rx, loi, re.I):
            return ten
    return ""          # rỗng = nền trơn, engine hiểu là "câu này trừu tượng"


def _n(khuon, loi, **kw):
    d = {"khuon": khuon, "loi": loi}
    d.update(kw)
    # Nơi chốn: nếu chỗ gọi không nói rõ thì đọc ra từ chính lời. Nói rõ thì tôn trọng —
    # nhưng vẫn phải là nơi hợp với câu, nên bên dưới có cổng `kiem_boi_canh.py` soát lại.
    if khuon in ("canh", "nhom", "kinh_lup") and not d.get("noi"):
        d["noi"] = _noi(loi)
    return d


# ── BỘ SINH TỪNG KÊNH ───────────────────────────────────────────────────────────────────────
# Mỗi bộ trả về (tiêu đề, hook, hook phụ, danh sách nhịp). Nhịp CHƯA có mốc thời gian — mốc do
# độ dài tiếng đọc quyết định, vì nhịp phải khớp lời chứ không phải lời phải khớp nhịp.

def sinh_howlong(i):
    """Bộ sinh MẪU — cả bảy quy tắc nối cảnh đều dùng ở đây, có chú thích tại chỗ.

    Bảy quy tắc rút ra khi cắt 24 cảnh LIÊN TIẾP của video tham chiếu (xem
    PHAN_TICH_GIAI_THICH.md mục 11). Lần soi đầu tôi lấy 25 khung rời rạc và chỉ rút được
    "bảy khuôn hình" — đó là TỪ VỰNG. Thứ làm nên phim là NGỮ PHÁP: cảnh nối cảnh thế nào."""
    ten, km, bt = QUANG_DUONG[i % len(QUANG_DUONG)]
    gio_b = km / DI_BO_KMH
    sb, ub = _lau(gio_b)
    sc, uc = _lau(km / XE_KMH)
    sm, um = _lau(km / MAY_BAY_KMH)
    sa, ua = _lau(km / AS_KMS / 3600)
    ngay = max(1, min(20, int(gio_b / 24)))
    return (f"Walking to {ten}",
            f"HOW LONG TO WALK TO {ten.upper()}?", f"{sb} {ub.upper()}",
            [
    # QUY TẮC G — con số đứng cạnh hình của CHÍNH VẬT ấy, không đứng trên biểu đồ.
    _n("chia_doi", "You walk. Light does not.",
       trai={"nhan": "you", "bt": "nguoi", "so": "5 km/h"},
       phai={"nhan": "light", "bt": "trai_dat", "so": "1.08 bn km/h"}, dinh=True),
    # QUY TẮC A — cảnh vẽ ĐÚNG mệnh đề. Câu nói về con số thì hình LÀ con số.
    _n("so_lieu", f"The distance to {ten}.", so=f"{km:,.0f}", don="kilometres", bt=bt, dinh=True),
    # QUY TẮC E — lời chuyển sang KHẲNG ĐỊNH thì hình chuyển sang THẺ CHỮ, bỏ hẳn minh hoạ.
    _n("the_chu", "Nobody has ever done this.", the="Nobody has|ever done this."),
    # QUY TẮC D — một mạch đi bộ; vệt dấu chân dài thêm qua từng cảnh.
    _n("canh", "So start walking.", noi="san_vuon", pose="lean", expr="neutral", ke_thua=0),
    _n("canh", "No breaks.", noi="san_vuon", pose="lean", expr="neutral", ke_thua=1),
    _n("canh", "No sleep.", noi="san_vuon", pose="lean", expr="annoyed", ke_thua=2),
    # QUY TẮC C — thời gian trôi vẽ bằng SỐ LƯỢNG. Người xem đếm, không đọc "hai tuần sau".
    _n("dem", "Days go by.", n=min(8, ngay), ngay=True, chu="", noi="san_vuon",
       pose="lean", expr="neutral", ke_thua=3),
    _n("dem", "And they keep going.", n=min(18, ngay * 2), ngay=True,
       chu="still walking", noi="san_vuon", pose="lean", expr="sad", ke_thua=5),
    _n("so_lieu", "You arrive.", so=sb, don=ub, chu=f"walking non-stop to {ten}",
       bt="nguoi", dinh=True),
    # QUY TẮC B — bộ cảnh SONG SONG: cùng bố cục, dải chữ cùng một chỗ, chỉ đổi nội dung.
    # QUY TẮC A + B cùng lúc: ba cảnh CÙNG bố cục (dải chữ một chỗ), nhưng mỗi cảnh phải vẽ
    # ĐÚNG chủ thể của mệnh đề. Bản trước cho cả ba là người đứng ngoài phố — "by car" mà không
    # có cái xe nào thì hình đang nói một điều khác lời.
    _n("so_lieu", "On foot.", so=sb, don=ub, bt="nguoi", dai_chu=f"WALK — {sb} {ub}"),
    _n("so_lieu", "By car.", so=sc, don=uc, bt="xe", dai_chu=f"CAR — {sc} {uc}"),
    _n("so_lieu", "By jet.", so=sm, don=um, bt="xe", dai_chu=f"JET — {sm} {um}"),
    _n("truc", "Light does it in this.",
       moc=[{"nhan": "walk", "phu": f"{sb} {ub}"}, {"nhan": "jet", "phu": f"{sm} {um}"},
            {"nhan": "light", "phu": f"{sa} {ua}"}], vt=1.0, dinh=True),
    _n("so_lieu", "Light wins.", so=sa, don=ua, bt="trai_dat", dinh=True),
    _n("the_chu", "So no. Do not walk.", the="So no.|Do not walk.", dinh=True),
            ])


def sinh_howbig(i):
    a = CO_LON[i % len(CO_LON)]
    b = CO_LON[(i + 3) % len(CO_LON)]
    lon, nho = (a, b) if a[1] >= b[1] else (b, a)
    lan = lon[1] / nho[1]
    xep = int(round(lan))
    return (f"{lon[0].title()} vs {nho[0]}",
            f"HOW BIG IS {lon[0].upper()} REALLY?", f"{lan:.0f}x BIGGER",
            [
    _n("chia_doi", "Two things. One question.",
       trai={"nhan": nho[0], "bt": nho[3], "so": f"{nho[1]:g} m"},
       phai={"nhan": lon[0], "bt": lon[3], "so": f"{lon[1]:g} m"}, dinh=True),
    _n("canh", "Numbers alone mean nothing.", noi="san_vuon", pose="shrug", expr="suspicious"),
    _n("so_lieu", "So here is the ratio.", so=f"{lan:.1f}x", don="bigger", bt=lon[3], dinh=True),
    _n("canh", f"Picture {nho[0]}.", noi="san_vuon", pose="present", expr="neutral"),
    _n("nhom", f"Now stack {xep} of them.", noi="san_vuon", n=min(5, max(2, xep // 4 + 2))),
    _n("so_lieu", "That is the other one.", so=f"{lon[1]:g}", don="metres", chu=lon[0], bt=lon[3], dinh=True),
    _n("truc", "On one scale, side by side.",
       moc=[{"nhan": "0"}, {"nhan": f"{nho[1]:g} m", "phu": nho[0]},
            {"nhan": f"{lon[1]:g} m", "phu": lon[0]}], vt=1.0),
    _n("the_chu", "Your brain was wrong.", the="Your brain|was wrong.", dinh=True),
            ])


def sinh_realcost(i):
    ten, gia, lan, bt = THOI_QUEN[i % len(THOI_QUEN)]
    nam = gia * lan
    m10 = sum(nam * (1.07 ** k) for k in range(10))
    m30 = sum(nam * (1.07 ** k) for k in range(30))
    return (f"The real cost of {ten}",
            f"WHAT {ten.upper()} REALLY COSTS", _tien(m30) + " OVER 30 YEARS",
            [
    _n("canh", "It feels like nothing.", noi="bep", pose="present", expr="happy"),
    _n("so_lieu", "One purchase.", so=_tien(gia), don="each time", bt=bt),
    _n("chia_doi", "But you do not buy it once.",
       trai={"nhan": "once", "bt": bt, "so": _tien(gia)},
       phai={"nhan": "one year", "bt": "tien", "so": _tien(nam)}, dinh=True),
    _n("so_lieu", "That is one year.", so=_tien(nam), don="per year", bt="tien", dinh=True),
    _n("canh", "Now leave it alone.", noi="phong_khach", pose="lookaway", expr="neutral"),
    _n("truc", "Ten years of the same habit.",
       moc=[{"nhan": "year 1", "phu": _tien(nam)}, {"nhan": "year 10", "phu": _tien(m10)}], vt=1.0),
    _n("so_lieu", "Invested instead, at seven percent.", so=_tien(m10), don="in 10 years",
       chu="assuming a 7% annual return", bt="tien", dinh=True),
    _n("canh", "Keep going.", noi="phong_khach", pose="point", expr="curious"),
    _n("so_lieu", "Thirty years.", so=_tien(m30), don="in 30 years",
       chu="same habit, same 7% assumption", bt="tien", dinh=True),
    _n("chia_doi", "The coffee, or the number.",
       trai={"nhan": "the habit", "bt": bt, "so": _tien(gia), "phu": "each time"},
       phai={"nhan": "30 years of it", "bt": "tien", "so": _tien(m30)}, dinh=True),
    _n("the_chu", "Nobody says stop. Just look.", the="Nobody says stop.|Just look.", dinh=True),
            ])


def sinh_howmuch(i):
    ds = [("seconds", 1), ("dollars a day", 86400), ("steps", 1), ("grains of rice", 1)]
    ten, _ = ds[i % len(ds)]
    gio = 1_000_000_000 / 3600
    s1, u1 = _lau(1_000_000 / 3600)
    s2, u2 = _lau(gio)
    return ("A million versus a billion",
            "A BILLION IS NOT A BIG MILLION", f"{s2} {u2.upper()}",
            [
    _n("chia_doi", "Two words. One letter apart.",
       trai={"nhan": "million", "bt": "tien", "so": "1,000,000"},
       phai={"nhan": "billion", "bt": "tien", "so": "1,000,000,000"}, dinh=True),
    _n("canh", "Your brain treats them the same.", noi="phong_khach", pose="shrug", expr="suspicious"),
    _n("so_lieu", "Count a million seconds.", so=s1, don=u1, bt="dong_ho", dinh=True),
    _n("canh", "That is a normal trip.", noi="duong", pose="lean", expr="neutral"),
    _n("so_lieu", "Now count a billion.", so=s2, don=u2, bt="dong_ho", dinh=True),
    _n("truc", "Same scale. Look again.",
       moc=[{"nhan": "million", "phu": f"{s1} {u1}"}, {"nhan": "billion", "phu": f"{s2} {u2}"}], vt=1.0),
    _n("the_chu", "One is a trip. One is a life.", the="One is a trip.|One is a life.", dinh=True),
            ])


def sinh_whatif(i):
    ds = [("everyone flushed at once", "hop"), ("everyone jumped at once", "trai_dat"),
          ("everyone stopped driving for a day", "xe"), ("everyone planted one tree", "cay")]
    ten, bt = ds[i % len(ds)]
    return (f"What if {ten}",
            f"WHAT IF {ten.upper()}?", "",
            [
    _n("canh", "One person does it.", noi="phong_khach", pose="present", expr="neutral"),
    _n("the_chu", "Nothing happens.", the="Nothing|happens."),
    _n("nhom", "Now ten people.", noi="duong", n=4, dai_chu="TEN"),
    _n("nhom", "Now a hundred.", noi="duong", n=5, dai_chu="A HUNDRED"),
    _n("so_lieu", "Now everyone.", so="8,000,000,000", don="people", bt=bt, dinh=True),
    _n("chia_doi", "One, against all of us.",
       trai={"nhan": "one", "bt": "nguoi", "so": "1"},
       phai={"nhan": "everyone", "bt": bt, "so": "8 bn"}, dinh=True),
    _n("the_chu", "Small things do not stay small.", the="Small things|do not stay small.", dinh=True),
            ])


def sinh_survive(i):
    ds = [("a day in the Ice Age", "san_vuon"), ("a week without fire", "san_vuon"),
          ("a night in the desert", "duong"), ("a winter without a shop", "san_vuon")]
    ten, noi = ds[i % len(ds)]
    return (f"Could you survive {ten}",
            f"COULD YOU SURVIVE {ten.upper()}?", "PROBABLY NOT",
            [
    _n("canh", "You. Dropped here.", noi=noi, pose="shock", expr="shock", dinh=True),
    _n("so_lieu", "You need this much.", so="2,000", don="calories a day", bt="lua"),
    _n("canh", "Nothing here has a label.", noi=noi, pose="lookaway", expr="suspicious"),
    _n("chia_doi", "What you know. What they knew.",
       trai={"nhan": "you", "bt": "dien_thoai", "so": "0 plants"},
       phai={"nhan": "them", "bt": "cay", "so": "200+"}, dinh=True),
    _n("the_chu", "That was not instinct.", the="That was|not instinct."),
    _n("canh", "It was training.", noi=noi, pose="present", expr="neutral"),
    _n("dem", "Count the days you last.", n=7, ngay=True, chu="one week", noi=noi,
       pose="lean", expr="sad"),
    _n("the_chu", "You would last a week.", the="You would|last a week.", dinh=True),
            ])


def sinh_dayinlife(i):
    ds = [("a Roman soldier", "duong"), ("a medieval baker", "bep"),
          ("a lighthouse keeper", "duong"), ("a night watchman", "hanh_lang")]
    ten, noi = ds[i % len(ds)]
    return (f"A day in the life of {ten}",
            f"A DAY IN THE LIFE OF {ten.upper()}", "",
            [
    _n("canh", "The day starts before light.", noi=noi, pose="lean", expr="sad", dinh=True),
    _n("truc", "The whole day, hour by hour.",
       moc=[{"nhan": "4am", "phu": "up"}, {"nhan": "noon", "phu": "work"},
            {"nhan": "8pm", "phu": "done"}], vt=0.0),
    _n("canh", "Up before light.", noi=noi, pose="lean", expr="sad", dai_chu="4 AM — UP"),
    _n("canh", "Working through noon.", noi=noi, pose="present", expr="neutral", dai_chu="NOON — WORK"),
    _n("canh", "Still going at dusk.", noi=noi, pose="lean", expr="sad", dai_chu="8 PM — STILL"),
    _n("so_lieu", "That is the daily distance.", so="30", don="kilometres", bt="nguoi", dinh=True),
    _n("chia_doi", "Their day, and yours.",
       trai={"nhan": "them", "bt": "nguoi", "so": "16 hours"},
       phai={"nhan": "you", "bt": "dien_thoai", "so": "8 hours"}, dinh=True),
    _n("dem", "Then they do it again.", n=14, ngay=True, chu="every day", noi=noi,
       pose="lean", expr="deadpan"),
    _n("the_chu", "Every day. For life.", the="Every day.|For life.", dinh=True),
            ])


def sinh_wheregoes(i):
    ds = [("the thing you put in recycling", "hop"), ("the return you sent back", "hop"),
          ("the water in your sink", "trai_dat"), ("the food you throw away", "hop")]
    ten, bt = ds[i % len(ds)]
    return (f"Where {ten} goes",
            f"WHERE DOES {ten.upper()} GO?", "",
            [
    _n("canh", "You put it in the bin.", noi="bep", pose="present", expr="neutral", dinh=True),
    _n("canh", "You stop thinking about it.", noi="bep", pose="lookaway", expr="deadpan"),
    _n("truc", "It has four more stops.",
       moc=[{"nhan": "bin"}, {"nhan": "truck"}, {"nhan": "sorting"}, {"nhan": "end"}], vt=0.0),
    _n("so_lieu", "Most of it stops here.", so="Step 3", don="sorting", bt=bt, dinh=True),
    _n("chia_doi", "What you think happens, and what does.",
       trai={"nhan": "you think", "bt": "trai_dat", "so": "reused"},
       phai={"nhan": "actually", "bt": bt, "so": "sorted, mostly"}, dinh=True),
    _n("the_chu", "Nobody told you. Now you know.", the="Nobody told you.|Now you know.", dinh=True),
            ])


def sinh_therules(i):
    ds = [("the rule about your own driveway", "duong"), ("the rule about your own mailbox", "duong"),
          ("the rule about your own front lawn", "san_vuon"), ("the rule about your own fence", "san_vuon")]
    ten, noi = ds[i % len(ds)]
    return (f"The rule about {ten}",
            f"THERE IS A RULE ABOUT {ten.upper()}", "",
            [
    _n("canh", "You own it. You paid for it.", noi=noi, pose="present", expr="happy", dinh=True),
    _n("canh", "There is still a rule.", noi=noi, pose="shock", expr="shock", dinh=True),
    _n("kinh_lup", "It is written right here.", noi=noi, nhan="the fine print", x=0.34, y=0.55),
    _n("chia_doi", "What you assumed, and what it says.",
       trai={"nhan": "you assumed", "bt": "nha", "so": "yours"},
       phai={"nhan": "the rule says", "bt": "giay", "so": "conditions"}, dinh=True),
    _n("the_chu", "Nobody reads it until it matters.", the="Nobody reads it|until it matters.", dinh=True),
            ])


def sinh_speedof(i):
    ds = [("a sneeze", 160), ("a falling raindrop", 32), ("a house cat", 48),
          ("the fastest human", 44), ("a commercial jet", 900)]
    ten, kmh = ds[i % len(ds)]
    lan = kmh / DI_BO_KMH
    return (f"The speed of {ten}",
            f"HOW FAST IS {ten.upper()}?", f"{kmh} KM/H",
            [
    _n("canh", "It happens too fast to see.", noi="phong_khach", pose="shock", expr="shock", dinh=True),
    _n("so_lieu", "So here is the number.", so=f"{kmh}", don="km/h", chu=ten, bt="nguoi", dinh=True),
    _n("chia_doi", "Next to you, walking.",
       trai={"nhan": "you walking", "bt": "nguoi", "so": f"{DI_BO_KMH:.0f} km/h"},
       phai={"nhan": ten, "bt": "xe", "so": f"{kmh} km/h"}, dinh=True),
    _n("so_lieu", "That is the multiple.", so=f"{lan:.0f}x", don="your walking speed", bt="nguoi", dinh=True),
    _n("truc", "On one line.",
       moc=[{"nhan": "walk", "phu": f"{DI_BO_KMH:.0f}"}, {"nhan": ten, "phu": f"{kmh}"},
            {"nhan": "jet", "phu": "900"}], vt=0.5),
    _n("the_chu", "You never had a chance.", the="You never|had a chance.", dinh=True),
            ])


BO_SINH = {"howlong": sinh_howlong, "howbig": sinh_howbig, "realcost": sinh_realcost,
           "howmuch": sinh_howmuch, "whatif": sinh_whatif, "survive": sinh_survive,
           "dayinlife": sinh_dayinlife, "wheregoes": sinh_wheregoes,
           "therules": sinh_therules, "speedof": sinh_speedof}


def mot_tap(ma: str, idx: int, doc: bool = True) -> str:
    k = next((x for x in KENH if x["ma"] == ma), None)
    if not k:
        print(f"❌ không có kênh {ma}")
        return ""
    tieu, hook, hook_phu, nhip = BO_SINH[k["sinh"]](idx)
    slug = f"{ma}_{idx:04d}"
    print(f"\n▶ {k['ten']} · {tieu}", flush=True)

    hat = sum(ord(c) for c in ma) + idx
    # Giọng kể: một người, trầm, chậm vừa. Phim giải thích không có đối thoại — mọi lời là
    # của người kể, nên `doc_hai_giong` chỉ dùng một giọng cho cả hai khe.
    ga = ("en-US-GuyNeural", "-4%", "-2Hz")
    cau = [(n["loi"], 0, "trung_tinh") for n in nhip]
    rel = f"v9_{slug}.mp3"
    try:
        dur, tu, moc = doc_hai_giong(cau, ga, ga, os.path.join(PUB, rel))
    except Exception as e:
        print(f"   ❌ giọng đọc hỏng: {str(e)[:110]}")
        return ""
    if not tu or len(moc) < len(nhip):
        print("   ❌ thiếu mốc — BỎ")
        return ""

    # Mốc nhịp lấy từ ĐỘ DÀI TIẾNG NÓI, không đặt cứng: câu ngắn thì cảnh ngắn. Đây chính là
    # cơ chế cho ra nhịp 2,1 giây — nó nằm ở khâu VIẾT (câu 5-8 chữ), không ở khâu dựng.
    for i, n in enumerate(nhip):
        n["s"] = round(moc[i][0], 3)
        n["e"] = round(moc[i + 1][0] if i + 1 < len(moc) else moc[i][1] + 0.55, 3)
    dai = round(nhip[-1]["e"] + 0.35, 2)

    props = {"nhip": nhip, "vai": [VAI_KE], "tu": tu, "voMp3": rel,
             "nhac": NHAC[hat % len(NHAC)], "nhacVol": 0.11,
             "tieuDe": k["ten"], "handle": "@" + ma + "usa",
             "mau": k["mau"], "mauPhu": k["phu"],
             "hook": hook, "hookPhu": hook_phu, "dai": dai, "doc": doc}
    pj = os.path.join(GOC, "out", f"v9_{slug}.json")
    os.makedirs(os.path.dirname(pj), exist_ok=True)
    io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))

    out = os.path.join(GOC, "out", f"v9_{slug}.mp4")
    comp = "GiaiThichDoc" if doc else "GiaiThich"
    r = subprocess.run(["npx", "remotion", "render", "src/index.ts", comp, out,
                        f"--props={pj}", "--gl=swiftshader", "--log=error", "--crf", "21"],
                       cwd=ENG, capture_output=True, text=True, timeout=3000)
    if r.returncode or not os.path.exists(out):
        print(f"   ❌ render hỏng: {(r.stderr or r.stdout or '')[-260:]}")
        return ""
    am = chuan(out)
    lam_thumb(out, tieu, k["ten"], k["mau"], os.path.join(GOC, "out", f"v9_{slug}.jpg"))

    d = [round(n["e"] - n["s"], 2) for n in nhip]
    d.sort()
    print(f"   ✅ {os.path.basename(out)} ({os.path.getsize(out)/1e6:.1f} MB · {dai:.1f}s · "
          f"{len(nhip)} nhịp · trung vị {d[len(d)//2]:.1f}s · dài nhất {d[-1]:.1f}s · {am})")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--tu", type=int, default=0)
    ap.add_argument("--so", type=int, default=1)
    ap.add_argument("--ngang", action="store_true", help="dựng bản 16:9 (long) thay vì 9:16")
    a = ap.parse_args()
    ds = [x.strip() for x in a.kenh.split(",") if x.strip()] or [k["ma"] for k in KENH]
    ra = [v for j, de in enumerate(ds) for i in range(a.so)
          if (v := mot_tap(de, a.tu + i + j, doc=not a.ngang))]
    print(f"\n✅ {len(ra)}/{len(ds) * a.so} video")
    return 0 if ra else 1


if __name__ == "__main__":
    raise SystemExit(main())
