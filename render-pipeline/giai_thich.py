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
# ══ ĐƠN VỊ MỸ, KHÔNG PHẢI ĐƠN VỊ QUỐC TẾ ════════════════════════════════════════════════════
# Anh: *"nhớ chuẩn phong cách USA từ nhân vật tới bối cảnh, nội dung."*
#
# Đây là lỗi NỘI DUNG chứ không phải lỗi hình, và nó nặng hơn mọi lỗi hình đã sửa hôm nay: cả
# mười kênh đang nói "384,400 kilometres", "5 km/h", "30 metres". Người xem Mỹ đọc câu ấy là
# biết ngay đây không phải kênh của họ — họ không có cảm giác về kilômét, đúng như người Việt
# không có cảm giác về dặm.
# Kênh giải thích sống bằng việc quy con số về thứ người xem CẢM ĐƯỢC. Dùng sai hệ đơn vị là
# phá hỏng đúng cái cơ chế ấy, ngay ở gốc.
DI_BO_MPH = 3.1            # tốc độ đi bộ người lớn (dặm/giờ)
CHAY_MPH = 7.5
XE_MPH = 60.0
MAY_BAY_MPH = 560.0
AS_MPS = 186282.0          # tốc độ ánh sáng, dặm mỗi giây

QUANG_DUONG = [                                  # dặm
    ("the Moon",                       238900,    "trai_dat"),
    ("the Sun",                      92960000,    "trai_dat"),
    ("Mars at its closest",          33900000,    "trai_dat"),
    ("all the way around the Earth",    24901,    "trai_dat"),
    ("New York to Los Angeles",          2445,    "xe"),
    ("the bottom of the Mariana Trench",  6.8,    "trai_dat"),
    ("the top of Mount Everest",          5.5,    "cay"),
]

CO_LON = [                                       # feet
    ("a blue whale",           98.0, "ft", "cay"),
    ("a school bus",           36.0, "ft", "xe"),
    ("a giraffe",              18.0, "ft", "cay"),
    ("an adult human",          5.6, "ft", "nguoi"),
    ("a Boeing 747",          232.0, "ft", "xe"),
    ("the Statue of Liberty",  305.0, "ft", "nha"),
    ("a football field",      300.0, "ft", "cay"),
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
# ══ TÔNG MÀU RIÊNG TỪNG NICHE ═══════════════════════════════════════════════════════════════
# Anh: *"xây dựng tông màu cho niche, phong cách dựng ảnh sao cho đẹp chuẩn USA như một channel
# top 1 hàng đầu thế giới."*
#
# Mười kênh dùng chung một nền kem `#F3EEE4` là sai — không phải sai thẩm mỹ mà sai CHỨC NĂNG.
# Bảng màu là thứ người xem nhận ra kênh TRƯỚC KHI đọc chữ đầu tiên; dùng chung một bảng thì
# mười kênh trông như mười tập của cùng một kênh, và không kênh nào xây được nhận diện.
#
# Chọn theo niche, không theo sở thích:
#   · tài chính / dữ liệu -> trắng ngà lạnh + xanh trầm: đọc ra "đáng tin", đúng thứ quyết
#     định RPM ở niche này (người xem tin thì mới xem hết, mới có quảng cáo giữa video)
#   · lịch sử -> giấy cũ ngả vàng + nâu đất
#   · sinh tồn -> xám đá lạnh + gỉ sắt
#   · khoa học vui -> cát ấm + cam cháy, tông duy nhất được phép tươi
# `nen` là nền trơn (khuôn chia đôi, trục, thẻ chữ, và cảnh trừu tượng không có ảnh).
MAU_KENH = {
    "howlong":  {"nen": "#F4EDE0", "mau": "#D9622B", "phu": "#2F6E8A", "chu": "#2E2A24"},
    "howbig":   {"nen": "#EEF1F3", "mau": "#1F6F7A", "phu": "#C9552F", "chu": "#22282B"},
    "realcost": {"nen": "#F2F0EA", "mau": "#1E6B4E", "phu": "#8A5A2E", "chu": "#232622"},
    "howmuch":  {"nen": "#EEF0F4", "mau": "#43418F", "phu": "#C98A2E", "chu": "#232336"},
    "whatif":   {"nen": "#F5F0E6", "mau": "#B4523A", "phu": "#2F7D8A", "chu": "#2B2622"},
    "survive":  {"nen": "#E8E9E6", "mau": "#8A3F2E", "phu": "#4E6B54", "chu": "#232522"},
    "dayinlife":{"nen": "#F0E7D6", "mau": "#8A6134", "phu": "#3E6E8C", "chu": "#2A241B"},
    "wheregoes":{"nen": "#EDF0F2", "mau": "#2F6E9E", "phu": "#C9762F", "chu": "#212629"},
    "therules": {"nen": "#EFF1EA", "mau": "#C0603A", "phu": "#4E7C4A", "chu": "#252722"},
    "speedof":  {"nen": "#EAF0F5", "mau": "#21618C", "phu": "#D9622B", "chu": "#1F272E"},
}

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


# ══ GHÉP PROMPT ẢNH CHI TIẾT ════════════════════════════════════════════════════════════════
# Anh: *"thế phải viết prompt tạo ảnh dài hơn, chi tiết, phù hợp với bối cảnh videos để ra được
# đúng như ý."*
#
# Anh đúng. Bản đầu em viết `ve="a lone figure walking across a wide empty plain"` — mười hai
# chữ. FLUX điền phần còn lại bằng thứ nó hay vẽ nhất, nên ra cảnh chung chung và đôi khi lạc
# hẳn (nhịp nói đi bộ ban đêm ngoài sa mạc ra một phòng khách có tủ kệ).
#
# Mô hình khuếch tán không "hiểu" cảnh; nó khớp mô tả. Chỗ nào mình không tả thì nó tự chọn,
# và nó chọn theo thứ phổ biến trong dữ liệu huấn luyện — tức là chọn cái trung bình, đúng thứ
# làm ảnh trông nhạt. Nên mỗi prompt phải nói đủ SÁU tầng:
#
#   1. CHỦ THỂ  — ai/cái gì, mặc gì, ở tư thế nào
#   2. HÀNH ĐỘNG— đang làm gì, hướng nào
#   3. BIỂU CẢM — nét mặt và dáng người (anh dặn "vẽ đúng bối cảnh biểu cảm")
#   4. MÔI TRƯỜNG — ba lớp xa/giữa/gần, đúng thứ hai video tham chiếu làm
#   5. ÁNH SÁNG — hướng, độ gắt, bảng màu
#   6. MÁY QUAY — cỡ cảnh và độ cao
#
# Viết tay đủ sáu tầng cho 250 nhịp thì không ai làm nổi, nên hàm này ghép — người viết nhịp
# chỉ cần nói phần RIÊNG của nhịp ấy, phần chung do đây lo.
def _ve(chu: str, lam: str = "", cam: str = "", xa: str = "", gan: str = "",
        sang: str = "", may: str = "wide shot at standing eye level") -> str:
    """Ghép sáu tầng thành một prompt dài. Tầng nào bỏ trống thì bỏ hẳn khỏi câu — thà thiếu
    còn hơn điền bừa một mô tả sai, vì mô tả sai thì mô hình vẽ đúng cái sai ấy."""
    # 1/9 — BỎ NHÃN KIỂU ẢNH CHỤP.
    # Bản trước ghép "background: …", "foreground: …" rồi một câu ánh sáng ("warm light from the
    # left, long soft shadows"). Đó là cách người ta tả một BỨC ẢNH, và mô hình đọc xong thì vẽ
    # ra một bức ảnh — đo được: những nhịp có câu ánh sáng cho độ phẳng thấp nhất cả tập.
    # Tranh vẽ phẳng không có "tiền cảnh/hậu cảnh" theo nghĩa quang học, cũng không có đổ bóng
    # mềm. Nó có: cái gì ở đâu trong khung, và màu gì.
    p = [chu]
    if lam:
        p.append(lam)
    if cam:
        p.append(cam)
    if xa:
        p.append(f"behind them {xa}")
    if gan:
        p.append(f"near the bottom of the frame {gan}")
    # `sang` giữ lại NHƯNG chỉ lấy phần bảng màu, bỏ phần hướng sáng và đổ bóng.
    if sang:
        gon = [c.strip() for c in sang.split(",")
               if "palette" in c or "colour" in c or "color" in c]
        if gon:
            p.append(", ".join(gon))
    p.append(may)
    return ", ".join(x for x in p if x)


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
    """Bộ sinh MẪU — bảy quy tắc nối cảnh, và mỗi nhịp cảnh viết kèm PROMPT ẢNH.

    Anh: *"khi viết kịch bản thì sẽ viết cả prompt tạo ảnh bối cảnh, nhân vật tĩnh mô phỏng kèm
    luôn sao cho khớp đúng là được, ko cần vector chuyển động."*
    Nên trường `ve` đứng ngay cạnh `loi`: người viết nhịp là người biết nhịp ấy đang nói gì,
    nên cũng là người duy nhất viết đúng được prompt cho nó. Tách hai việc ra hai chỗ là cách
    chắc chắn để hình lệch lời — đúng cái đã xảy ra khi tôi để `noi` cho một bảng regex đoán."""
    ten, km, bt = QUANG_DUONG[i % len(QUANG_DUONG)]
    gio_b = km / DI_BO_MPH
    sb, ub = _lau(gio_b)
    sc, uc = _lau(km / XE_MPH)
    sm, um = _lau(km / MAY_BAY_MPH)
    sa, ua = _lau(km / AS_MPS / 3600)
    ngay = max(1, min(20, int(gio_b / 24)))
    return (f"Walking to {ten}",
            f"HOW LONG TO WALK TO {ten.upper()}?", f"{sb} {ub.upper()}",
            [
    _n("chia_doi", "You walk. Light does not.",
       trai={"nhan": "you", "bt": "nguoi", "so": "3 mph"},
       phai={"nhan": "light", "bt": "trai_dat", "so": "670 mn mph"}, dinh=True),
    _n("so_lieu", f"The distance to {ten}.", so=f"{km:,.0f}", don="miles", bt=bt, dinh=True,
       ve=_ve(f"a tiny lone human figure standing alone on a vast empty plain, simple worn clothing",
              "head tilted back, gazing up at the sky", "small and awed against the emptiness",
              f"{ten} hanging huge and pale in a deep open sky, low flat horizon line",
              "cracked dry earth with a few scattered pebbles",
              "clear cool daylight from high behind, long soft shadow stretching toward camera"),
       tam_trang="ngay"),
    _n("the_chu", "Nobody has ever done this.", the="Nobody has|ever done this."),
    _n("canh", "So start walking.", ke_thua=0, tam_trang="ngay",
       ve=_ve("a lone adult figure in plain simple clothing, mid-stride",
              "setting off walking to the right, first steps of a journey",
              "determined, chin up, arms swinging",
              "an endless flat plain, low pale hills far away, wide open sky",
              "a fresh line of footprints pressed into dry sand, a few dry tufts of grass",
              "warm morning sun from the left, long soft shadows")),
    _n("canh", "No breaks.", ke_thua=1, tam_trang="ngay",
       ve=_ve("the same lone adult figure in plain simple clothing, seen from the side",
              "still walking to the right at a steady pace",
              "beginning to tire, shoulders lower, head down slightly",
              "the same endless plain, the horizon completely empty ahead",
              "a much longer trail of footprints receding behind, small stones",
              "harsh midday sun directly overhead, short hard shadow, bleached warm palette")),
    _n("canh", "No sleep.", ke_thua=2, tam_trang="dem",
       ve=_ve("the same lone adult figure, small in the frame",
              "still walking to the right, slow heavy steps",
              "exhausted, head down, arms hanging",
              "the same open plain at night, a huge field of stars, faint moonlit horizon",
              "cool blue sand, the footprint trail catching pale moonlight",
              "deep blue night, single cool moonlight source from above right")),
    _n("dem", "Days go by.", n=min(8, ngay), ngay=True, tam_trang="ngay",
       ve=_ve("a lone adult figure far away, small in the frame",
              "walking steadily onward to the right",
              "worn down but still moving",
              "the same plain seen from further back, hills unchanged on the horizon",
              "an extremely long curving trail of footprints filling the lower third",
              "warm afternoon light from behind, dust haze")),
    _n("dem", "And they keep going.", n=min(18, ngay * 2), ngay=True, chu="still walking",
       tam_trang="kho",
       ve=_ve("an exhausted lone adult figure, clothing worn and dusty",
              "trudging forward with great effort",
              "head hanging, dragging feet, defeated but continuing",
              "a grey overcast plain, the footprint trail vanishing to the far horizon behind",
              "cracked pale ground, wind-blown dust",
              "cold flat overcast light, desaturated grey-brown palette")),
    _n("so_lieu", "You arrive.", so=sb, don=ub, chu=f"walking non-stop to {ten}",
       bt="nguoi", dinh=True, tam_trang="ngay",
       ve=_ve("a small weary human figure with arms raised in triumph",
              "standing still at the end of a very long walk",
              "worn out but joyful, head thrown back",
              f"{ten} filling the upper half of the frame, close and enormous",
              "the last footprints ending right at the figure's feet",
              "warm golden light from the left, celebratory palette")),
    _n("so_lieu", "On foot.", so=sb, don=ub, bt="nguoi", dai_chu=f"WALK — {sb} {ub}",
       ve=_ve("a single adult person seen in clean side profile, plain simple clothing",
              "walking steadily to the right, mid-stride",
              "neutral, everyday",
              "a completely plain pale backdrop with a single horizon line, nothing else",
              "a simple flat ground strip",
              "even soft studio lighting, no drama, clean flat colours")),
    _n("so_lieu", "By car.", so=sc, don=uc, bt="xe", dai_chu=f"CAR — {sc} {uc}",
       ve=_ve("a simple ordinary family car in clean side profile",
              "driving to the right, wheels turning, slight motion lines",
              "",
              "a completely plain pale backdrop with a single horizon line, nothing else",
              "a simple flat road strip",
              "even soft studio lighting, clean flat colours")),
    _n("so_lieu", "By jet.", so=sm, don=um, bt="may_bay", dai_chu=f"JET — {sm} {um}",
       ve=_ve("a simple passenger jet aircraft in clean side profile",
              "flying to the right, thin vapour trail behind",
              "",
              "an empty pale blue sky with one thin cloud band far below",
              "nothing in the foreground, open air",
              "bright even daylight, clean flat colours")),
    _n("chart", "Side by side.", don="time to arrive",
       cot=[{"nhan": "walk", "v": round(gio_b)}, {"nhan": "car", "v": round(km / XE_MPH)},
            {"nhan": "jet", "v": round(km / MAY_BAY_MPH)}], dinh=True),
    _n("so_lieu", "Light wins.", so=sa, don=ua, bt="trai_dat", dinh=True,
       ve=_ve("a single bright beam of light streaking horizontally across the frame",
              "travelling at extreme speed to the right, long luminous trail",
              "",
              "deep black space scattered with small stars, a pale distant world at the right edge",
              "the beam's glow lighting nothing but itself",
              "high contrast, cold white light against deep blue-black, dramatic")),
    # Anh: *"cuối videos bỏ cái kéo dài mấy giây nhàm chán text cuối videos."*
    # Đúng: một tấm thẻ chữ giữ 3 giây ở cú chốt là chỗ người xem thoát. Cú chốt phải là HÌNH
    # mạnh nhất của cả tập, câu chốt để phụ đề nói. Video tham chiếu cũng vậy — họ đóng bằng
    # cảnh, không đóng bằng bảng chữ.
    _n("canh", "So no. Do not walk.", dinh=True, tam_trang="ngay",
       ve=_ve("a lone figure standing beside a parked car, one hand on the roof",
              "having just given up on walking, looking at the horizon",
              "wry, self-aware, half-smiling",
              "the same endless plain, the destination tiny and far away in the sky",
              "the car door open, footprints ending right at the wheel",
              "warm late light from the left, long shadow")),
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
       trai={"nhan": nho[0], "bt": nho[3], "so": f"{nho[1]:g} ft"},
       phai={"nhan": lon[0], "bt": lon[3], "so": f"{lon[1]:g} ft"}, dinh=True),
    _n("canh", "Numbers alone mean nothing.",
       ve=_ve("a single simplified human silhouette beside an enormous blank measuring rule",
              "looking up at the rule, one hand raised uncertainly", "puzzled, head tilted",
              "a clean pale studio wall with a faint horizon line", "a plain flat floor strip",
              "even soft light, restrained muted palette")),
    _n("so_lieu", "So here is the ratio.", so=f"{lan:.1f}x", don="bigger", bt=lon[3], dinh=True,
       ve=_ve(f"{nho[0]} and {lon[0]} standing side by side on the same flat ground",
              "both seen in clean side profile at true relative scale", "",
              "a plain pale backdrop with one faint horizon line, nothing else",
              "a simple continuous flat ground strip running edge to edge",
              "even soft daylight, restrained muted palette, clear separation between shapes")),
    _n("canh", f"Picture {nho[0]}.", ve=_ve(f"{nho[0]} alone, centred, clean side profile", "standing still", "",
              "a plain pale backdrop with a single faint horizon line",
              "a simple flat ground strip", "even soft daylight, muted palette")),
    _n("canh", f"Now stack {xep} of them.",
       ve=_ve(f"many identical copies of {nho[0]} stacked into one tall neat column",
              "piled precisely one on top of another, reaching high up the frame",
              "orderly and slightly absurd",
              "a plain pale backdrop, the column rising past the top edge",
              "a simple flat ground strip at the base",
              "even soft daylight, muted palette")),
    _n("so_lieu", "That is the other one.", so=f"{lon[1]:g}", don="feet", chu=lon[0],
       bt=lon[3], dinh=True, ve=_ve(f"{lon[0]} alone, filling most of the frame, clean side profile",
              "standing still, overwhelming in size", "",
              "a plain pale backdrop with a single faint horizon line",
              "a simple flat ground strip, a tiny human silhouette for scale at the far left",
              "even soft daylight, muted palette, strong sense of scale")),
    _n("chart", "On one scale.", don="feet",
       cot=[{"nhan": nho[0].replace("a ", "")[:9], "v": nho[1]},
            {"nhan": lon[0].replace("a ", "").replace("the ", "")[:9], "v": lon[1]}], dinh=True),
    _n("canh", "Your brain was wrong.", dinh=True,
       ve=_ve("a simplified human silhouette standing very small",
              "looking up at an enormous object towering over the whole frame",
              "stunned, tiny by comparison",
              "a plain pale backdrop, the object filling most of the height",
              "the silhouette at the very bottom for scale",
              "even soft light, restrained muted palette")),
            ])


def sinh_realcost(i):
    ten, gia, lan, bt = THOI_QUEN[i % len(THOI_QUEN)]
    nam = gia * lan
    m10 = sum(nam * (1.07 ** k) for k in range(10))
    m30 = sum(nam * (1.07 ** k) for k in range(30))
    return (f"The real cost of {ten}",
            f"WHAT {ten.upper()} REALLY COSTS", _tien(m30) + " OVER 30 YEARS",
            [
    _n("canh", "It feels like nothing.", tam_trang="ngay",
       ve=_ve("one hand holding a plain takeaway coffee cup, close in the frame",
              "raised casually, as if about to drink", "relaxed, unthinking, ordinary",
              "a softly blurred city sidewalk with simplified building shapes",
              "the cup crisp and sharp, everything behind it soft",
              "warm bright morning light from the left, cheerful muted palette")),
    _n("so_lieu", "One purchase.", so=_tien(gia), don="each time", bt=bt,
       ve=_ve("one single small everyday purchase sitting alone",
              "placed dead centre on an empty clean surface", "",
              "a plain pale wall, completely empty, generous negative space",
              "a clean unmarked tabletop with a soft contact shadow",
              "soft even overhead light, restrained muted palette")),
    _n("chia_doi", "But you do not buy it once.",
       trai={"nhan": "once", "bt": bt, "so": _tien(gia)},
       phai={"nhan": "one year", "bt": "tien", "so": _tien(nam)}, dinh=True),
    _n("so_lieu", "That is one year.", so=f"{nam:,.0f}", don="dollars a year", bt="tien", dinh=True,
       ve=_ve("a tall neat stack of plain unmarked banknotes",
              "stacked squarely in the centre of an empty desk", "",
              "a plain pale wall, nothing else in the room",
              "an empty clean desktop with a soft shadow under the stack",
              "soft overhead light from above front, restrained muted palette")),
    _n("canh", "Now leave it alone.",
       ve=_ve("a closed glass jar filled with coins, sitting untouched",
              "resting on a windowsill, undisturbed for a long time", "still and quiet",
              "a calm simple interior, a plain window with soft daylight beyond",
              "a dusty windowsill, a faint ring where the jar has always sat",
              "soft cool daylight from the window, calm muted palette")),
    _n("chart", "Ten years of the same habit.", don="dollars",
       cot=[{"nhan": "year 1", "v": round(nam)}, {"nhan": "year 5", "v": round(sum(nam * 1.07 ** k for k in range(5)))},
            {"nhan": "year 10", "v": round(m10)}], dinh=True),
    _n("so_lieu", "Invested instead.", so=f"{m10:,.0f}", don="dollars in 10 years",
       chu="assuming a 7% annual return", bt="tien", dinh=True,
       ve=_ve("a large simple rising line chart with one bold upward arrow",
              "climbing steeply from lower left to upper right", "",
              "a clean plain office wall, generous empty space around the chart",
              "a bare desk edge at the very bottom of the frame",
              "even soft daylight, restrained muted palette, business-magazine look")),
    _n("canh", "Keep going.",
       ve=_ve("a wall calendar with many loose pages caught mid-turn",
              "pages flying off the calendar and drifting through the air", "",
              "a quiet plain room, one bare wall, nothing else",
              "a few fallen pages settling on the floor",
              "soft daylight from the left, calm muted palette")),
    _n("so_lieu", "Thirty years.", so=f"{m30:,.0f}", don="dollars in 30 years",
       chu="same habit, same 7% assumption", bt="tien", dinh=True,
       ve=_ve("an enormous tower of plain unmarked banknotes",
              "rising far past the top of the frame",
              "a tiny simplified human silhouette at its base, dwarfed",
              "a plain pale backdrop, nothing else competing",
              "a clean floor with the tower's long shadow",
              "dramatic side light from the left, restrained muted palette")),
    _n("chia_doi", "The habit, or the number.",
       trai={"nhan": "the habit", "bt": bt, "so": _tien(gia), "phu": "each time"},
       phai={"nhan": "30 years", "bt": "tien", "so": _tien(m30)}, dinh=True),
    _n("canh", "Nobody says stop. Just look.", dinh=True,
       ve=_ve("one hand holding a plain takeaway cup, held out toward the camera",
              "offering it, as if asking a question",
              "calm, unjudging",
              "a softly blurred tall stack of banknotes far behind, out of focus",
              "the cup crisp and close, everything else soft",
              "soft even daylight, restrained muted palette")),
            ])


def sinh_howmuch(i):
    s1, u1 = _lau(1_000_000 / 3600)
    s2, u2 = _lau(1_000_000_000 / 3600)
    return ("A million versus a billion",
            "A BILLION IS NOT A BIG MILLION", f"{s2} {u2.upper()}",
            [
    _n("chia_doi", "Two words. One letter apart.",
       trai={"nhan": "million", "bt": "tien", "so": "1,000,000"},
       phai={"nhan": "billion", "bt": "tien", "so": "1,000,000,000"}, dinh=True),
    _n("canh", "Your brain treats them the same.",
       ve=_ve("a simplified human silhouette standing between two identical blank boxes",
              "shrugging, both palms turned up", "genuinely unable to tell them apart",
              "a plain pale wall, the two boxes exactly the same size",
              "a clean floor strip", "even soft light, restrained muted palette")),
    _n("so_lieu", "Count a million seconds.", so=s1, don=u1, bt="dong_ho", dinh=True,
       ve=_ve("one large plain clock face with blank unmarked dial",
              "hands frozen, hanging alone", "",
              "an empty pale wall, generous negative space all around",
              "nothing in the foreground", "soft even light, restrained muted palette")),
    _n("canh", "That is a normal trip.",
       ve=_ve("a small packed suitcase standing upright",
              "waiting by a closed door, handle up", "patient, about to leave",
              "a calm plain hallway with one simple door",
              "a clean floor with a soft shadow under the case",
              "soft daylight from the side, calm muted palette")),
    _n("so_lieu", "Now count a billion.", so=s2, don=u2, bt="dong_ho", dinh=True,
       ve=_ve("an enormous clock face with a blank unmarked dial",
              "filling almost the entire frame",
              "a tiny simplified human silhouette standing at its base, overwhelmed",
              "a plain pale backdrop, nothing else",
              "a clean floor strip at the very bottom",
              "dramatic light from the upper left, restrained muted palette")),
    _n("chart", "Same scale. Look again.", don="seconds",
       cot=[{"nhan": "million", "v": 1000000}, {"nhan": "billion", "v": 1000000000}], dinh=True),
    _n("canh", "One is a trip. One is a life.", dinh=True,
       ve=_ve("a small suitcase and an entire lifetime of belongings side by side",
              "the suitcase tiny, the pile of belongings enormous",
              "",
              "a plain pale wall, generous empty space",
              "both objects sharp on a clean floor, a soft shadow under each",
              "soft even light, restrained muted palette")),
            ])


def sinh_whatif(i):
    ds = [("everyone flushed at once", "hop", "a vast grid of identical bathrooms seen from above"),
          ("everyone jumped at once", "trai_dat", "an enormous crowd of people mid-jump on open ground"),
          ("everyone stopped driving", "xe", "a completely empty multi-lane highway at midday"),
          ("everyone planted one tree", "cay", "a huge open field newly filled with young saplings")]
    ten, bt, canh = ds[i % len(ds)]
    return (f"What if {ten}",
            f"WHAT IF {ten.upper()}?", "",
            [
    _n("canh", "One person does it.", ve=_ve("one single ordinary person alone in the frame",
              "performing one small everyday action", "casual, unremarkable",
              "a plain simple setting, mostly empty",
              "a clean floor strip", "flat even daylight, bright friendly palette")),
    _n("the_chu", "Nothing happens.", the="Nothing|happens."),
    _n("nhom", "Now ten people.", dai_chu="TEN", ve=_ve("exactly ten ordinary people standing together in a loose group",
              "all doing the same small action at the same moment",
              "casual, unaware of each other",
              "flat open ground stretching to a low horizon, wide sky",
              "short grass and a few small stones",
              "flat even daylight, bright friendly palette")),
    _n("nhom", "Now a hundred.", dai_chu="A HUNDRED",
       ve=_ve("about a hundred small simplified people filling a public square",
              "all doing the same small action together", "a busy uniform crowd",
              "a wide open square seen from a high angle, plain paving",
              "the front row of the crowd larger and clearer",
              "flat even daylight, bright friendly palette")),
    _n("so_lieu", "Now everyone.", so="8,000,000,000", don="people", bt=bt, dinh=True, ve=canh),
    _n("chia_doi", "One, against all of us.",
       trai={"nhan": "one", "bt": "nguoi", "so": "1"},
       phai={"nhan": "everyone", "bt": bt, "so": "8 bn"}, dinh=True),
    _n("canh", "Small things do not stay small.", dinh=True,
       ve=_ve("one single ordinary person standing alone in the foreground",
              "turning to look back at an enormous crowd stretching to the horizon",
              "realising the scale of it",
              "an immense crowd filling the entire background to the horizon",
              "the single person sharp and close, the crowd soft behind",
              "flat even daylight, bright friendly palette")),
            ])


def sinh_survive(i):
    ds = [("a day in the Ice Age", "a frozen tundra under heavy grey sky, bare and endless"),
          ("a week without fire", "a cold dark forest clearing at dusk, no light source"),
          ("a night in the desert", "a vast cold desert at night under a huge starfield"),
          ("a winter without a shop", "a snowbound valley with no buildings in sight")]
    ten, canh = ds[i % len(ds)]
    return (f"Could you survive {ten}",
            f"COULD YOU SURVIVE {ten.upper()}?", "PROBABLY NOT",
            [
    _n("canh", "You. Dropped here.", tam_trang="lanh", dinh=True,
       ve=f"a lone modern person in ordinary clothes standing in {canh}, small in the frame"),
    _n("so_lieu", "You need this much.", so="2,000", don="calories a day", bt="lua",
       ve=_ve("a small meagre pile of raw wild roots and berries",
              "gathered together on bare frozen ground", "",
              "a bleak empty landscape blurred behind, low grey horizon",
              "frost-hardened soil, a few dry twigs, the food sharp and close",
              "cold flat overcast light, heavily desaturated palette")),
    _n("canh", "Nothing here has a label.", tam_trang="lanh",
       ve=_ve("several unfamiliar wild plants and exposed roots",
              "growing low and tangled out of frozen ground", "",
              "a bleak cold landscape blurred far behind",
              "frost on the leaves, cracked icy soil filling the lower frame",
              "cold overcast light, desaturated blue-grey palette")),
    _n("chia_doi", "What you know. What they knew.",
       trai={"nhan": "you", "bt": "dien_thoai", "so": "0 plants"},
       phai={"nhan": "them", "bt": "cay", "so": "200+"}, dinh=True),
    _n("the_chu", "That was not instinct.", the="That was|not instinct."),
    _n("canh", "It was training.", tam_trang="dem",
       ve=_ve("an older adult and a child sitting close beside a small fire",
              "the adult pointing at something on the ground, teaching",
              "patient and attentive, both faces lit warm",
              "the dark mouth of a shelter behind them, deep night beyond",
              "the small fire and a scatter of stones in the near foreground",
              "warm firelight from below front against deep cold blue night")),
    _n("dem", "Count the days you last.", n=7, ngay=True, chu="one week", tam_trang="lanh",
       ve=_ve("a lone weakening figure huddled small against a large rock",
              "curled tight, arms wrapped around knees, sheltering from wind",
              "failing, hollow-eyed, barely holding on",
              "an open frozen waste, wind-driven snow streaking across a grey sky",
              "the rock's rough edge and drifted snow in the near foreground",
              "cold flat light, heavily desaturated blue-grey palette")),
    _n("canh", "You would last a week.", dinh=True, tam_trang="lanh",
       ve=_ve("a single set of footprints in snow ending abruptly",
              "the trail simply stopping in open ground, nobody in frame",
              "",
              "an empty frozen waste under heavy grey sky, no shelter anywhere",
              "the last two footprints sharp and close in the lower frame",
              "cold flat overcast light, heavily desaturated palette")),
            ])


def sinh_dayinlife(i):
    # Mỗi nghề ba mảnh: NƠI (ba lớp xa-giữa-gần) · ĐỒ NGHỀ · ÁNH SÁNG. Ba mảnh này đi vào ba
    # tầng khác nhau của prompt, nên tách sẵn ở đây thay vì nhét chung một chuỗi.
    ds = [("a Roman soldier",
           "a Roman military camp at first light, rows of leather tents, a stone road running out to distant hills",
           "worn leather armour, a heavy pack and a spear",
           "pale cold dawn light from the low left, long blue shadows"),
          ("a medieval baker",
           "a low stone bakery with a wide wood-fired oven, flour dust in the air, a shuttered window",
           "a flour-dusted apron and a long wooden peel",
           "warm orange oven glow from the right against cold blue pre-dawn"),
          ("a lighthouse keeper",
           "a lone stone lighthouse on a rocky headland, grey sea and low cloud behind",
           "a heavy oilskin coat and a brass lamp",
           "flat grey overcast light, desaturated sea-green palette"),
          ("a night watchman",
           "a narrow old town street at night, shuttered houses leaning close, cobblestones",
           "a long coat and a single swinging lantern",
           "one warm lantern light against deep blue darkness, hard pool of light on the stones")]
    ten, canh, do, sang = ds[i % len(ds)]
    return (f"A day in the life of {ten}",
            f"A DAY IN THE LIFE OF {ten.upper()}", "",
            [
    _n("canh", "The day starts before light.", dinh=True, tam_trang="dem",
       ve=_ve(f"{ten} alone, {do}", "rising stiffly in the dark, still half asleep",
              "heavy-lidded, reluctant, resigned", canh,
              "the edge of a rough bed and cold floor close to camera", sang)),
    _n("canh", "Up before light.", dai_chu="4 AM — UP", tam_trang="dem",
       ve=_ve(f"{ten}, {do}", "pulling on worn clothing piece by piece",
              "moving on habit, eyes barely open", canh,
              "clothing and tools laid out ready in the near foreground", sang)),
    _n("canh", "Working through noon.", dai_chu="NOON — WORK", tam_trang="ngay",
       ve=_ve(f"{ten}, {do}", "deep in hard physical work, both hands busy",
              "concentrating, sweating, jaw set", canh,
              "the work itself large and clear in the near foreground",
              "harsh bright midday sun from overhead, short hard shadows, warm palette")),
    _n("canh", "Still going at dusk.", dai_chu="8 PM — STILL", tam_trang="kho",
       ve=_ve(f"{ten}, {do}", "still working as the light drains away",
              "exhausted, shoulders down, moving slowly", canh,
              "long shadows stretching across the near foreground",
              "low orange evening light from the right, cooling grey sky")),
    _n("so_lieu", "That is the daily distance.", so="19", don="miles", bt="nguoi", dinh=True,
       ve=_ve(f"{ten} small and distant, {do}", "walking a long worn path away from camera",
              "steady, head down", canh,
              "the worn path filling the lower third, footprints in the dust", sang)),
    _n("chia_doi", "Their day, and yours.",
       trai={"nhan": "them", "bt": "nguoi", "so": "16 hours"},
       phai={"nhan": "you", "bt": "dien_thoai", "so": "8 hours"}, dinh=True),
    _n("dem", "Then they do it again.", n=14, ngay=True, chu="every day", tam_trang="kho",
       ve=_ve(f"{ten}, {do}", "starting the exact same routine over again",
              "tired but steady, expression blank with habit", canh,
              "the same tools back in the same place", sang)),
    _n("canh", "Every day. For life.", dinh=True, tam_trang="dem",
       ve=_ve(f"{ten}, {do}", "walking away from camera into the dark, back turned",
              "worn down but still going", canh,
              "the worn path receding into darkness in the lower frame", sang)),
            ])


def sinh_wheregoes(i):
    ds = [("the thing you put in recycling", "hop",
           _ve("a plain blue recycling bin with its lid open",
               "standing at a suburban kerb waiting for collection", "",
               "a quiet residential street, simplified houses receding, parked car far off",
               "the bin large and sharp, kerb stones and a few leaves close to camera",
               "cool early morning light from the left, soft muted palette")),
          ("the return you sent back", "hop",
           _ve("a sealed cardboard return parcel with plain unmarked tape",
               "sitting alone on a doorstep, waiting for pickup", "",
               "a simple front door and porch, blurred garden beyond",
               "the parcel sharp and close, doormat texture in front",
               "soft flat daylight, restrained muted palette")),
          ("the water in your sink", "trai_dat",
           _ve("a stainless kitchen sink with water swirling into the drain",
               "the last of the water spiralling away", "",
               "a clean modern kitchen, simplified cabinets softly blurred",
               "the drain and swirling water sharp and close in the lower frame",
               "cool daylight from a window at the left, clean muted palette")),
          ("the food you throw away", "hop",
           _ve("an open kitchen bin holding untouched leftover food",
               "lid propped open, food still on the plate inside", "",
               "a plain kitchen corner, simplified cupboards behind",
               "the bin opening and its contents sharp and close",
               "flat indoor light, slightly desaturated palette"))]
    ten, bt, canh = ds[i % len(ds)]
    return (f"Where {ten} goes",
            f"WHERE DOES {ten.upper()} GO?", "",
            [
    _n("canh", "You put it in the bin.", dinh=True, ve=canh),
    _n("canh", "You stop thinking about it.",
       ve=_ve("a closed bin lid, shut tight", "nothing moving, nobody present", "",
              "a completely tidy empty room, everything put away",
              "the closed lid sharp and central, clean floor beneath",
              "flat even indoor light, quiet muted palette")),
    _n("truc", "It has four more stops.",
       moc=[{"nhan": "bin"}, {"nhan": "truck"}, {"nhan": "sorting"}, {"nhan": "end"}], vt=0.0),
    _n("canh", "First the truck.", ve=_ve("a large plain collection truck, side profile",
              "moving slowly along the kerb, arm extended toward a bin", "",
              "a quiet suburban street, simplified houses and trees receding",
              "the kerb and bins passing close to camera",
              "cool early morning light from the left, muted palette")),
    _n("canh", "Then the sorting line.",
       ve=_ve("a long industrial conveyor belt carrying mixed material",
              "the belt running steadily away into the depth of the frame", "",
              "a large plain sorting hall, high roof beams, machinery simplified",
              "the near end of the belt and its contents sharp and close",
              "cold overhead industrial light, desaturated grey-blue palette")),
    _n("so_lieu", "Most of it stops here.", so="Step 3", don="sorting", bt=bt, dinh=True,
       ve=_ve("tall separated piles of sorted material filling a warehouse",
              "piles rising high, walkways between them", "",
              "a huge plain sorting facility, far wall barely visible",
              "one pile close and sharp, a tiny human silhouette for scale",
              "cold overhead industrial light, desaturated palette")),
    _n("chia_doi", "What you think happens, and what does.",
       trai={"nhan": "you think", "bt": "trai_dat", "so": "reused"},
       phai={"nhan": "actually", "bt": bt, "so": "sorted"}, dinh=True),
    _n("canh", "Nobody told you. Now you know.", dinh=True,
       ve=_ve("a single small object sitting on top of an enormous sorted pile",
              "resting at the very top, unremarkable among thousands",
              "",
              "a vast sorting facility interior stretching far back",
              "the small object sharp and close at the top of the pile",
              "cold overhead industrial light, desaturated palette")),
            ])


def sinh_therules(i):
    ds = [("your own driveway",
           _ve("a clean empty concrete driveway", "running from the kerb up to a closed garage", "",
               "a plain two-storey American suburban house, neighbouring roofs beyond",
               "the driveway surface filling the lower third, a kerb edge close to camera",
               "warm mid-morning light from the left, bright friendly muted palette")),
          ("your own mailbox",
           _ve("a plain kerbside mailbox on a wooden post", "standing closed at the edge of the lawn", "",
               "a quiet suburban home set back behind a neat lawn, trees beyond",
               "the mailbox large and sharp, grass and kerb close to camera",
               "warm morning light from the right, bright muted palette")),
          ("your own front lawn",
           _ve("a neat mown green front lawn", "stretching flat from kerb to porch", "",
               "a simple suburban house front, low hedge, sky above",
               "cut grass texture filling the lower third",
               "bright midday light, saturated fresh green, friendly palette")),
          ("your own fence",
           _ve("a plain wooden boundary fence", "running straight between two yards", "",
               "two simplified suburban houses on either side, sky above",
               "fence boards large and sharp at the left, grass at the base",
               "warm afternoon light from the right, muted palette"))]
    ten, canh = ds[i % len(ds)]
    return (f"The rule about {ten}",
            f"THERE IS A RULE ABOUT {ten.upper()}", "",
            [
    _n("canh", "You own it. You paid for it.", dinh=True, tam_trang="ngay", ve=canh),
    _n("canh", "There is still a rule.", tam_trang="ngay",
       ve=f"{canh}, a small blank white notice board planted upright in the ground near the centre, "
          "the board completely blank and unmarked"),
    _n("kinh_lup", "It is written right here.", nhan="the fine print", x=0.34, y=0.55,
       ve=_ve("a thick document lying open, pages completely blank and unmarked",
              "spread flat, one page half turned", "",
              "a plain wooden table, nothing else on it, softly blurred room behind",
              "the open pages sharp and close, paper texture visible",
              "soft overhead light, restrained muted palette")),
    _n("chia_doi", "What you assumed, and what it says.",
       trai={"nhan": "you assumed", "bt": "nha", "so": "yours"},
       phai={"nhan": "the rule", "bt": "giay", "so": "conditions"}, dinh=True),
    _n("canh", "Then the letter arrives.", tam_trang="kho",
       ve=_ve("a single plain white envelope, completely unmarked",
              "sitting alone inside an open mailbox", "quietly ominous",
              "a suburban front lawn softly blurred behind, grey overcast sky",
              "the mailbox mouth and envelope sharp and close",
              "flat cold overcast light, desaturated palette")),
    _n("canh", "Nobody reads it until it matters.", dinh=True, tam_trang="kho",
       ve=_ve("a thick unread document lying face down on a kitchen counter",
              "untouched, a thin layer of dust on it",
              "",
              "a plain suburban kitchen softly blurred behind",
              "the document sharp and close, its edges curling",
              "flat cold morning light, desaturated palette")),
            ])


def sinh_speedof(i):
    ds = [("a sneeze", 100,
           _ve("a person caught at the exact instant of a sneeze",
               "head snapping forward, sharp motion lines bursting outward",
               "eyes screwed shut, whole body braced",
               "a plain simple interior, everything else still and blurred",
               "the burst of motion lines large and sharp across the frame",
               "flat even light, bright friendly palette")),
          ("a falling raindrop", 20,
           _ve("one single raindrop, elongated by speed",
               "falling straight down through the frame, faint motion streak behind", "",
               "a flat grey sky with soft cloud banding, no ground visible",
               "the drop crisp and close, a few smaller drops soft behind",
               "cool diffuse overcast light, cool muted palette")),
          ("a house cat", 30,
           _ve("a domestic cat at full sprint, body stretched flat",
               "running hard to the right, sharp motion lines trailing behind",
               "ears flat, eyes wide and fixed ahead",
               "a simple green lawn with a low fence and blurred garden beyond",
               "grass blades bending in the cat's wake, close to camera",
               "bright afternoon light from the left, saturated friendly palette")),
          ("the fastest human", 27,
           _ve("a sprinter at absolute top speed, both feet off the ground",
               "driving to the right, arms pumping, motion lines behind",
               "face locked in total effort",
               "a running track with lane lines converging, blurred stadium beyond",
               "the near lane line and track texture sharp at the bottom",
               "bright stadium daylight, high saturation, energetic palette")),
          ("a commercial jet", 560,
           _ve("a passenger jet in clean side profile, cruising",
               "flying to the right, thin vapour trail stretching behind", "",
               "a deep blue high-altitude sky, a flat cloud deck far below",
               "nothing near the camera, open air",
               "bright hard sunlight from above left, clean cool palette"))]
    ten, kmh, canh = ds[i % len(ds)]
    lan = kmh / DI_BO_MPH
    # Biểu tượng phải là HÌNH CỦA CHÍNH VẬT đang đo (quy tắc G). Bản trước gán cứng "xe" cho
    # mọi chủ thể, nên nhịp nói "a commercial jet" mà hình ra ô tô.
    bt_ten = ("may_bay" if "jet" in ten else "nguoi" if ("human" in ten or "sneeze" in ten)
              else "cay" if "raindrop" in ten else "nguoi")
    return (f"The speed of {ten}",
            f"HOW FAST IS {ten.upper()}?", f"{kmh} MPH",
            [
    _n("canh", "It happens too fast to see.", dinh=True, ve=canh),
    _n("so_lieu", "So here is the number.", so=f"{kmh}", don="mph", chu=ten, bt="nguoi",
       dinh=True, ve=canh),
    _n("chia_doi", "Next to you, walking.",
       trai={"nhan": "you walking", "bt": "nguoi", "so": "3 mph"},
       phai={"nhan": ten, "bt": bt_ten, "so": f"{kmh} mph"}, dinh=True),
    _n("so_lieu", "That is the multiple.", so=f"{lan:.0f}x", don="your walking speed", bt="nguoi",
       ve=_ve("one ordinary person walking calmly at normal pace",
              "walking to the right while a heavily blurred fast shape streaks past behind",
              "unbothered, unaware",
              "a plain pale backdrop with a single horizon line",
              "the walking figure sharp, the streak smeared across the frame",
              "even soft light, restrained palette")),
    _n("chart", "On one scale.", don="mph",
       cot=[{"nhan": "walk", "v": 3}, {"nhan": ten.split()[-1][:9], "v": kmh},
            {"nhan": "jet", "v": 560}], dinh=True),
    _n("canh", "You never had a chance.", dinh=True,
       ve=_ve("one ordinary person standing still, seen from behind",
              "watching a blurred streak vanish into the far distance",
              "small and left behind",
              "an empty road running straight to a flat horizon",
              "the person sharp and close, the streak smeared far ahead",
              "even soft light, restrained palette")),
            ])


BO_SINH = {"howlong": sinh_howlong, "howbig": sinh_howbig, "realcost": sinh_realcost,
           "howmuch": sinh_howmuch, "whatif": sinh_whatif, "survive": sinh_survive,
           "dayinlife": sinh_dayinlife, "wheregoes": sinh_wheregoes,
           "therules": sinh_therules, "speedof": sinh_speedof}


# ══ HOOK: MỘT KHẲNG ĐỊNH TẠO KHOẢNG TRỐNG ═══════════════════════════════════════════════════
# Anh: *"nhớ vẽ đẹp và sát kịch bản, viết kịch bản cho hay sâu sắc, chất lượng, mang lại giá trị
# cao, hook."*
#
# Nhịp mở đầu cũ của cả mười kênh đều là CÂU DẪN NHẬP, không phải hook: "It feels like nothing."
# · "One person does it." · "Two things. One question." Chúng mô tả, và mô tả thì không tạo lý
# do để xem tiếp.
#
# Video tham chiếu mở bằng một KHẲNG ĐỊNH TẠO KHOẢNG TRỐNG — tấm thẻ "Not the fastest. Not even
# close." Người xem lập tức muốn biết "không nhanh nhất thì là gì", và khoảng trống ấy giữ họ.
#
# Và vì đã bỏ thẻ tiêu đề đầu video, nhịp 0 phải gánh thêm việc thứ hai: NÓI RA CHỦ ĐỀ. Nên nó
# là khuôn `so_lieu` — con số trả lời đặt ngay trước mặt, câu hỏi làm chú thích dưới. Đáp án
# trước, rồi cả tập đi chứng minh. Kiểu này giữ chân tốt hơn kiểu giấu đáp án tới cuối, vì người
# lướt không chờ tới cuối.
HOOK_LOI = {
    "howlong":  "Nobody has ever done this.",
    "howbig":   "Your brain gets this wrong.",
    "realcost": "It feels like nothing. It is not.",
    "howmuch":  "A billion is not a big million.",
    "whatif":   "One person changes nothing.",
    "survive":  "You would not last.",
    "dayinlife": "You would quit by noon.",
    "wheregoes": "You think it gets reused.",
    "therules": "You own it. Sort of.",
    "speedof":  "You never stood a chance.",
}


def mot_tap(ma: str, idx: int, doc: bool = True) -> str:
    k = next((x for x in KENH if x["ma"] == ma), None)
    if not k:
        print(f"❌ không có kênh {ma}")
        return ""
    tieu, hook, hook_phu, nhip = BO_SINH[k["sinh"]](idx)
    # Nhịp 0 = HOOK. Chèn ở đây chứ không viết vào từng bộ sinh: hook là quy tắc chung của cả
    # bộ phim, không phải nội dung riêng của một kênh — viết mười chỗ là mười chỗ để lệch nhau.
    # CHỈ chèn khung số liệu khi THẬT SỰ CÓ SỐ. Bốn kênh (whatif · dayinlife · wheregoes ·
    # therules) không có con số tiêu đề, và chèn bừa thì ra một khung số liệu RỖNG — chữ số
    # trống, không biểu tượng, chỉ còn dòng chú thích lơ lửng giữa nền trơn. Khung rỗng ở nhịp
    # mở đầu còn tệ hơn không có hook: ba giây đầu là ba giây quyết định.
    # Không có số thì hook nằm ở LỜI, đặt lên chính nhịp đầu vốn đã có ảnh.
    if HOOK_LOI.get(ma) and nhip and hook_phu.strip() and nhip[0].get("khuon") != "so_lieu":
        nhip.insert(0, {
            "khuon": "so_lieu", "loi": HOOK_LOI[ma], "dinh": True,
            "so": (hook_phu.split()[0] if hook_phu else ""),
            "don": (" ".join(hook_phu.split()[1:]) if hook_phu else ""),
            "chu": hook.rstrip("?").title() + "?",
        })
    elif HOOK_LOI.get(ma) and nhip:
        nhip[0]["loi"] = HOOK_LOI[ma]
        nhip[0]["dinh"] = True
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

    # ── VẼ CẢNH BẰNG CF ─────────────────────────────────────────────────────────────────
    # Chạy TRƯỚC render, không trong lúc render: một ảnh hỏng thì chỉ nhịp ấy rơi về nền vẽ
    # bằng code, chứ không làm cả tập chết giữa chừng. Đây là bài học bốn tầng nền của bộ
    # truyện tranh — thứ gì gọi mạng phải có tầng không gọi mạng đứng dưới.
    try:
        import the_he_2 as T2
        import nen_gt
        _ks = [k for k in (T2.keys_cuc_bo() or [])
               if str(k if isinstance(k, str) else k.get("key", "")).startswith("cf:")]
        if _ks:
            _mk = MAU_KENH.get(ma, {})
            _na = nen_gt.sinh_tap(ma, idx, nhip, _ks, doc=doc,
                                  mau_chu=_mk.get("chu", ""), mau_nen=_mk.get("nen", ""))
            _cn = sum(1 for x in nhip if x.get("ve"))
            print(f"   🎨 vẽ {_na}/{_cn} cảnh bằng CF"
                  + ("" if _na == _cn else "  (số còn lại dùng nền vẽ bằng code)"))
        else:
            print("   ⚠ không có khoá CF — toàn bộ dùng nền vẽ bằng code")
    except Exception as e:
        print(f"   ⚠ vẽ cảnh hỏng ({str(e)[:70]}) — dùng nền vẽ bằng code")

    # Mốc nhịp lấy từ ĐỘ DÀI TIẾNG NÓI, không đặt cứng: câu ngắn thì cảnh ngắn. Đây chính là
    # cơ chế cho ra nhịp 2,1 giây — nó nằm ở khâu VIẾT (câu 5-8 chữ), không ở khâu dựng.
    for i, n in enumerate(nhip):
        n["s"] = round(moc[i][0], 3)
        n["e"] = round(moc[i + 1][0] if i + 1 < len(moc) else moc[i][1] + 0.55, 3)
    dai = round(nhip[-1]["e"] + 0.35, 2)

    mk = MAU_KENH.get(ma, {"nen": "#F3EEE4", "mau": k["mau"], "phu": k["phu"], "chu": "#2C2722"})
    props = {"nhip": nhip, "tu": tu, "voMp3": rel,
             "nhac": NHAC[hat % len(NHAC)], "nhacVol": 0.11,
             "tieuDe": k["ten"], "handle": "@" + ma + "usa",
             "mau": mk["mau"], "mauPhu": mk["phu"],
             "nenTrang": mk["nen"], "chuTrang": mk["chu"],
             "dai": dai, "doc": doc}
    _ = (hook, hook_phu)   # thẻ hook đã bỏ theo yêu cầu; giữ biến để bộ sinh không phải sửa
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
