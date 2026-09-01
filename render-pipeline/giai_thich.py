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
    ("the Moon",                       238900,    "mat_trang"),
    ("the Sun",                      92960000,    "mat_troi"),
    ("Mars at its closest",          33900000,    "trai_dat"),
    ("all the way around the Earth",    24901,    "trai_dat"),
    ("New York to Los Angeles",          2445,    "xe"),
    ("the bottom of the Mariana Trench",  6.8,    "trai_dat"),
    ("the top of Mount Everest",          5.5,    "cay"),
    ("New York to London",               3459,    "may_bay"),
    ("the length of the Mississippi",    2340,    "trai_dat"),
    ("all the way around Saturn",       235298,   "trai_dat"),
]

CO_LON = [                                       # feet
    ("a blue whale",           98.0, "ft", "ca_voi"),
    ("a school bus",           36.0, "ft", "xe_buyt"),
    ("a giraffe",              18.0, "ft", "huou"),
    ("an adult human",          5.6, "ft", "nguoi"),
    ("a Boeing 747",          232.0, "ft", "may_bay"),
    ("the Statue of Liberty",  305.0, "ft", "nha"),
    ("a football field",      300.0, "ft", "cay"),
]

# ══ HẰNG SỐ CHO 8 KÊNH BỔ SUNG (1/9/2026) ═══════════════════════════════════════════════════
# Anh: *"phân tích nâng cấp cho a 8 channel phù hợp nữa để cho tròn 18 channel, đủ 18 luồng."*
#
# Chọn theo đúng hai tiêu chí đã đặt cho 10 kênh đầu, không nới lỏng:
#   1. MỌI CON SỐ PHẢI TÍNH RA ĐƯỢC, không tra. Kịch bản chạy không người canh; một con số tra
#      sai là mất kênh, và không ai biết cho tới khi có người bình luận.
#   2. KHÔNG TRÙNG NICHE với mười kênh đang có — trùng thì hai kênh cùng nhà tự ăn lượt xem
#      của nhau, và thuật toán YouTube coi chúng là một.
#
# Tám niche này phủ nốt những mảng viral ở Mỹ mà mười kênh đầu chưa chạm: xác suất · phí ẩn ·
# tổng đời người · âm thanh · khối lượng · dân số tức thời · nhiệt độ · thang cực nhỏ.
XAC_SUAT = [                                        # (việc, mẫu số 1-trên-N)
    ("winning the big lottery jackpot", 292_201_338, "tien"),
    ("being struck by lightning this year", 1_222_000, "lua"),
    ("bowling a perfect game as an amateur", 11_500, "hop"),
    ("being born on February 29th", 1_461, "dong_ho"),
    ("flipping ten heads in a row", 1_024, "tien"),
    ("two people sharing a birthday in a room of 23", 2, "nguoi"),
]
PHI_AN = [                                          # (thứ, giá, các phần %)
    ("a $6 coffee", 6.00, [("the beans", 6), ("the cup and lid", 4),
                           ("rent and power", 26), ("the person who made it", 24),
                           ("everything else", 40)]),
    ("a $15 cinema ticket", 15.00, [("the studio", 55), ("the cinema", 25),
                                    ("staff", 12), ("everything else", 8)]),
    ("a $30 delivered meal", 30.00, [("the food", 40), ("the restaurant", 18),
                                     ("the driver", 12), ("the app", 30)]),
    ("a $1200 phone", 1200.00, [("the parts", 38), ("assembly", 3),
                                ("research", 12), ("the shop", 12), ("the brand", 35)]),
]
DOI_NGUOI = [                                       # (việc, giờ mỗi ngày)
    ("sleeping", 8.0, "giuong"), ("looking at a phone", 4.5, "dien_thoai"),
    ("eating", 1.2, "hop"), ("commuting", 1.0, "xe"),
    ("waiting in lines", 0.3, "nguoi"), ("watching television", 2.8, "dien_thoai"),
]
# XẾP THEO SỨC HÚT, KHÔNG XẾP TĂNG DẦN. Tập 0 là tập đầu tiên người xem gặp trên kênh mới —
# xếp tăng dần thì nó rơi vào "HOW LOUD IS A WHISPER?", một tiêu đề không ai bấm vào.
AM_THANH = [                                        # (thứ, decibel)
    ("a jet at takeoff", 140, "may_bay"), ("a rock concert", 110, "lua"),
    ("a motorbike", 95, "xe"), ("a vacuum cleaner", 75, "hop"),
    ("normal talking", 60, "nguoi"), ("a whisper", 30, "nguoi"),
]
KHOI_LUONG = [                                      # (thứ, pound) — mạnh nhất trước
    ("a school bus", 24000, "xe_buyt"), ("a small car", 2900, "xe"),
    ("a grand piano", 990, "dan_piano"), ("an adult human", 180, "nguoi"),
    ("a car tyre", 25, "xe"), ("a housecat", 10, "meo"),
]
_KHOI_LUONG_CU = [
    ("a housecat", 10, "meo"), ("a car tyre", 25, "xe"),
    ("an adult human", 180, "nguoi"), ("a grand piano", 990, "dan_piano"),
    ("a small car", 2900, "xe_buyt"), ("a school bus", 24000, "xe"),
]
NHIET_DO = [                                        # (thứ, độ F) — mạnh nhất trước
    ("the surface of the Sun", 10000, "mat_troi"), ("lava", 2000, "lua"),
    ("a pizza oven", 800, "lua"), ("boiling water", 212, "lua"),
    ("a hot summer day in Phoenix", 115, "lua"), ("a comfortable room", 70, "nha"),
]
CUC_NHO = [                                         # (thứ, mét) — mạnh nhất trước
    ("a single atom", 1e-10, "nguyen_tu"), ("a virus", 1e-7, "vi_khuan"),
    ("a bacterium", 1e-6, "vi_khuan"), ("a red blood cell", 8e-6, "te_bao"),
    ("a human hair's width", 7e-5, "te_bao"), ("a grain of sand", 5e-4, "hop"),
]
_CUC_NHO_CU = [
    ("a grain of sand", 5e-4, "hop"), ("a human hair's width", 7e-5, "te_bao"),
    ("a red blood cell", 8e-6, "te_bao"), ("a bacterium", 1e-6, "vi_khuan"),
    ("a virus", 1e-7, "vi_khuan"), ("a single atom", 1e-10, "nguyen_tu"),
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
    # ── 8 kênh bổ sung. Màu chọn để KHÔNG trùng cặp nào ở trên: mỗi kênh phải nhận ra được
    # khi đứng cạnh mười bảy kênh kia trong danh sách đề xuất của YouTube.
    "odds":      {"nen": "#F1EDF5", "mau": "#6B3FA0", "phu": "#C9A227", "chu": "#241F2E"},
    "hiddenfee": {"nen": "#F0F2EE", "mau": "#2C6E49", "phu": "#B4522E", "chu": "#1F2620"},
    "yearsof":   {"nen": "#F5F1E8", "mau": "#A3542B", "phu": "#3E6E7C", "chu": "#2A2520"},
    "howloud":   {"nen": "#EDEEF2", "mau": "#C2352E", "phu": "#2F5D8A", "chu": "#20242B"},
    "whatweighs": {"nen": "#EFF0EC", "mau": "#4A5C2B", "phu": "#B4603A", "chu": "#22261E"},
    "rightnow":  {"nen": "#ECF1F4", "mau": "#1F7A8C", "phu": "#D97E36", "chu": "#1E272B"},
    "howhot":    {"nen": "#F6EFE6", "mau": "#C24E1E", "phu": "#3B5E7A", "chu": "#2B231C"},
    "smallest":  {"nen": "#EDEFF4", "mau": "#3A4E9B", "phu": "#8FA33E", "chu": "#1F2330"},
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
    # ── 8 kênh bổ sung cho tròn 18 luồng (1/9/2026) ───────────────────────────────────
    {"ma": "odds",       "ten": "THE ODDS OF THAT",     "mau": "#6B3FA0", "phu": "#C9A227", "sinh": "odds"},
    {"ma": "hiddenfee",  "ten": "WHAT IS INSIDE THE PRICE", "mau": "#2C6E49", "phu": "#B4522E", "sinh": "hiddenfee"},
    {"ma": "yearsof",    "ten": "YEARS OF YOUR LIFE",   "mau": "#A3542B", "phu": "#3E6E7C", "sinh": "yearsof"},
    {"ma": "howloud",    "ten": "HOW LOUD IS IT",       "mau": "#C2352E", "phu": "#2F5D8A", "sinh": "howloud"},
    {"ma": "whatweighs", "ten": "WHAT IT WEIGHS",       "mau": "#4A5C2B", "phu": "#B4603A", "sinh": "whatweighs"},
    {"ma": "rightnow",   "ten": "HOW MANY RIGHT NOW",   "mau": "#1F7A8C", "phu": "#D97E36", "sinh": "rightnow"},
    {"ma": "howhot",     "ten": "HOW HOT IS IT",        "mau": "#C24E1E", "phu": "#3B5E7A", "sinh": "howhot"},
    {"ma": "smallest",   "ten": "THE SMALLEST THING",   "mau": "#3A4E9B", "phu": "#8FA33E", "sinh": "smallest"},
]

# ══ GU RIÊNG TỪNG NICHE ═════════════════════════════════════════════════════════════════════
# Anh: *"phải có một cái gu riêng cho từng niche, không bắt chước hoàn toàn nhau."*
#
# Đúng — nhưng có một mâu thuẫn phải nói rõ: sáng nay tôi CỐ Ý gộp cả mười kênh về một phong
# cách vẽ, vì trộn ảnh chụp với cartoon trong cùng một tập nhìn rất nghiệp dư (đo được: 30/74
# ảnh lệch phong cách). Nếu giờ cho mỗi kênh một chất vẽ khác thì rất dễ quay lại đúng chỗ ấy.
#
# Nên phân biệt ở những trục KHÔNG phá tính đồng nhất trong một tập:
#   · GIỌNG ĐỌC — trục mạnh nhất và rẻ nhất. Tai nhận ra kênh trước cả mắt, và giọng khác nhau
#     thì không cách nào nhầm hai kênh, dù hình có cùng chất vẽ.
#   · NHẠC NỀN cố định cho mỗi kênh, không xoay vòng — nhạc xoay vòng là thứ làm mười kênh
#     nghe như một xưởng.
#   · TỈ LỆ KHUÔN HÌNH — kênh tài chính nặng biểu đồ, kênh lịch sử nặng cảnh diễn, kênh so sánh
#     nặng khung chia đôi. Cùng bộ khuôn, khác hẳn nhịp điệu thị giác.
#   · SẮC THÁI CARTOON — vẫn phẳng, nhưng khác nét: viền dày / không viền / nét tay hơi run /
#     bảng màu hạn chế ba màu. Bốn thứ này đều nằm trong "cartoon phẳng" nên không kéo về ảnh thật.
#   · KIỂU CHỮ — hoa toàn phần / hoa đầu câu, và độ giãn chữ.
GU_RIENG = {
    # ══ GÁN THEO ĐỘ HỢP NICHE, KHÔNG GÁN VÒNG TRÒN ═══════════════════════════════════════
    # Anh: *"nhớ nhạc hay giọng đúng niche đúng channel phù hợp"* và *"lặp lại giọng vài
    # channel không sao, sao phù hợp là được."*
    #
    # Bản trước em gán bằng vòng tròn theo chỉ số — bảo đảm không trùng, nhưng BỎ QUA ĐỘ HỢP.
    # Giọng nhẹ vui cho kênh sinh tồn còn tệ hơn hai kênh trùng giọng: trùng thì người xem chỉ
    # thấy quen tai, lệch chất thì họ thấy kênh không đáng tin.
    #
    # ĐO KHO NHẠC TRƯỚC KHI GÁN, ra hai điều mà nhìn tên tệp không thấy:
    #   · các bản `_tram` là CÙNG MỘT BẢN, chỉ trầm hơn — chỉ có 15 bản khác nhau, không phải 20
    #   · ba bản rất ngắn: mindloop_pad 24s · mind_pad32 32s · broke_pad 44s. Dùng cho bản dài
    #     5 phút là lặp hơn mười vòng, nghe ra ngay là hàng rẻ. Nên chúng chỉ gán cho kênh mà
    #     bản ngắn là chính, và `_nhac_dai()` bên dưới đổi sang bản dài khi dựng long.
    #
    # Chất giọng gán theo niche: Christopher trầm khàn -> sinh tồn và khối lượng · Roger đo đắn
    # -> tiền bạc · Steffan giọng kể -> lịch sử · Andrew trẻ thân mật -> thí nghiệm tưởng tượng
    # · Brian dồn -> tốc độ và âm thanh · Aria rõ chuyên nghiệp -> dữ liệu · Michelle ấm -> đời
    # người · Jenny thân thiện -> đám đông · Emma sáng -> thang cực nhỏ.
    "howlong":    ("en-US-EricNeural",                "music/km_ascending.mp3",          "bold black outlines, playful"),
    "howbig":     ("en-US-AriaNeural",                "music/forecast.mp3",              "no outlines, clean geometric shapes, generous white space"),
    "realcost":   ("en-US-RogerNeural",               "music/mind_pad32.mp3",            "thin precise outlines, restrained three-colour palette, editorial"),
    "howmuch":    ("en-US-AriaNeural",                "music/km_reawakening.mp3",        "no outlines, soft rounded shapes, pastel accents"),
    "whatif":     ("en-US-AndrewNeural",              "music/carefree.mp3",              "bold outlines, exaggerated proportions, playful"),
    "survive":    ("en-US-ChristopherNeural",         "music/km_undaunted.mp3",          "rough hand-drawn outlines, muted earthy palette, gritty"),
    "dayinlife":  ("en-US-SteffanNeural",             "music/km_ossuary_rest.mp3",       "soft hand-drawn outlines, warm limited palette, storybook"),
    "wheregoes":  ("en-US-EricNeural",                "music/km_interloper.mp3",         "clean thin outlines, isometric-leaning shapes, tidy"),
    "therules":   ("en-US-GuyNeural",                 "music/broke_pad.mp3",             "bold outlines, flat suburban palette, deadpan"),
    "speedof":    ("en-US-BrianNeural",               "music/wallpaper.mp3",             "sharp outlines, motion lines, high-contrast palette"),
    "odds":       ("en-US-AndrewNeural",              "music/km_impact_andante.mp3",     "bold outlines, lucky-dip palette, playful chance motifs"),
    "hiddenfee":  ("en-US-RogerNeural",               "music/forecast_tram.mp3",         "thin outlines, ledger-like grid accents, editorial restraint"),
    "yearsof":    ("en-US-MichelleNeural",            "music/inspired.mp3",              "soft outlines, warm sepia-leaning palette, reflective"),
    "howloud":    ("en-US-BrianNeural",               "music/km_ascending_tram.mp3",     "sharp outlines, radiating sound-wave lines, high contrast"),
    "whatweighs": ("en-US-ChristopherNeural",         "music/km_long_note_four.mp3",     "heavy thick outlines, solid weighty shapes, low centre of gravity"),
    "rightnow":   ("en-US-JennyNeural",               "music/carefree_tram.mp3",         "no outlines, dense crowds of tiny simple shapes, bright"),
    "howhot":     ("en-US-GuyNeural",                 "music/km_ossuary_air.mp3",        "bold outlines, heat-shimmer texture, warm high contrast"),
    "smallest":   ("en-US-EmmaNeural",                "music/mindloop_pad.mp3",          "no outlines, soft rounded microscopic shapes, cool clinical palette"),
}

# Bản DÀI không được dùng nhạc dưới 120 giây: lặp hơn mười vòng trong một tập là dấu hiệu rẻ
# tiền rõ nhất về mặt âm thanh. Đổi sang bản dài cùng chất.
NHAC_NGAN = {"music/mind_pad32.mp3", "music/mindloop_pad.mp3", "music/broke_pad.mp3",
             "music/broke_pad_tram.mp3"}
NHAC_DAI_THAY = {"music/mind_pad32.mp3": "music/km_ossuary_air.mp3",
                 "music/mindloop_pad.mp3": "music/km_reawakening.mp3",
                 "music/broke_pad.mp3": "music/km_interloper.mp3",
                 "music/broke_pad_tram.mp3": "music/km_interloper.mp3"}


# ══ ÂM LƯỢNG NHẠC NỀN ═══════════════════════════════════════════════════════════════════════
# Anh: *"có nên dùng nhạc nhẹ phù hợp không, có lại phản tác dụng?"*
#
# ĐO TRƯỚC KHI TRẢ LỜI, và số đo cho ra một câu trả lời khác hẳn câu hỏi:
#     bản trộn hoàn chỉnh      −14,0 LUFS
#     nhạc gốc                 −19,0 LUFS
#     nhạc sau `nhacVol 0.11`  −38,2 LUFS   -> thấp hơn bản trộn 24 dB
# 24 dB dưới lời nói là gần như biến mất trên loa điện thoại. Nên nhạc hiện KHÔNG phản tác
# dụng — nó đơn giản là KHÔNG NGHE THẤY. Câu hỏi đúng không phải "nhẹ hay không nhẹ" mà là
# "có ở đó hay không".
#
# VÀ GỐC RỄ LÀ LỖI TÔI VỪA GÂY LẠI. `_am_nhac()` trong `kich_comic.py` đã tồn tại từ trước,
# đọc hệ số RIÊNG TỪNG TỆP từ `music/am_luong.json` — dựng ra chính để chữa bệnh "một hằng
# dùng chung cho các tệp trải 26 dB". Tôi hardcode 0.11 ở đây, tức làm lại đúng cái lỗi đã
# được sửa một lần rồi. Họ lỗi "một hằng phục vụ hai thứ biến thiên độc lập", tái phạm.
#
# MỨC NỀN CỦA BỘ NÀY CAO HƠN BỘ HÀI, có lý do: hài sống bằng nhịp thoại và khoảng lặng, nhạc
# phải tránh đường. Phim giải thích cắt 2,1 giây một cảnh với câu 5-8 chữ, nên giữa các câu có
# rất nhiều khe ngắn — im lặng ở đó nghe ra là hụt hơi. Nhạc là thứ nối các khe ấy lại.
# Bảng `am_luong.json` chuẩn về −37 LUFS; nhân 1,58 (tức +4 dB) đưa nền về ~−33 LUFS.
BUOC_NHAC = 1.58


def _am_nhac(nhac: str) -> float:
    """Hệ số âm lượng RIÊNG cho từng tệp nhạc, không dùng một hằng chung."""
    try:
        import json
        import os as _os
        p = _os.path.join(_os.path.dirname(GOC), "engine-remotion", "public",
                          "music", "am_luong.json")
        if _os.path.exists(p):
            b = json.load(io.open(p, encoding="utf-8"))
            h = float(b.get(_os.path.basename(nhac), 0.16))
            # TRẦN 2.0, KHÔNG PHẢI 1.0. Các hệ số trong `am_luong.json` là hệ số CHUẨN HOÁ:
            # tệp càng nhỏ tiếng thì hệ số càng CAO (cao nhất đo được 1.16). Kẹp ở 1.0 nghĩa là
            # cắt đúng phần bù của hai tệp nhỏ tiếng nhất — `howmuch` và `therules` chìm hơn 16
            # kênh kia, trong khi bảng hệ số sinh ra chính là để chúng ngang nhau. Một trần phục
            # vụ hai việc (chống giá trị rác · giữ chuẩn hoá) thì hỏng việc thứ hai.
            # Bộ hài dùng hệ số THÔ tới 1.16 và chạy thật nhiều tháng — Remotion nhận volume > 1.
            # Trần giữ lại chỉ để chặn một số rác, nên đặt trên đỉnh hợp lệ (1,16 × 1,58 = 1,83).
            return round(min(2.0, h * BUOC_NHAC), 3)
    except Exception as e:
        _am_nhac._loi = str(e)[:70]
    # Rơi tới đây là MỌI kênh dùng chung một hằng — đúng trạng thái đã làm nhạc chìm 24 dB dưới
    # lời và không có lỗi nào báo. Nên chỗ này phải kêu, dù chỉ một lần.
    if not getattr(_am_nhac, "_da_bao", False):
        _am_nhac._da_bao = True
        print(f"  ⚠ am_luong.json không đọc được ({getattr(_am_nhac, '_loi', 'không có tệp')})"
              f" — mọi kênh rơi về hằng 0.16")
    return 0.16


def _nhac(ma: str, long: bool) -> str:
    n = GU_RIENG.get(ma, ("", "music/forecast.mp3", ""))[1]
    return NHAC_DAI_THAY.get(n, n) if long and n in NHAC_NGAN else n



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


# ══ TÁM BỘ SINH BỔ SUNG ═════════════════════════════════════════════════════════════════════
def sinh_odds(i):
    ten, N, bt = XAC_SUAT[i % len(XAC_SUAT)]
    # Quy xác suất về thứ CẢM ĐƯỢC: bao nhiêu năm nếu thử mỗi ngày một lần. Con số "1 trên 292
    # triệu" không gợi ra gì; "mua mỗi ngày trong 800.000 năm" thì nhớ đời.
    nam = N / 365.25
    sn, un = _lau(nam * 365.25 * 24)
    return (f"The odds of {ten}", f"THE ODDS OF {ten.upper()}", f"1 IN {N:,}",
            [
    _n("so_lieu", "These are the real odds.", so=f"1 in {N:,}", don="", bt=bt, dinh=True,
       ve=_ve("one single lottery ticket lying alone on a plain surface",
              "sitting untouched, nothing else in frame", "", "a plain empty backdrop",
              "the ticket sharp and close", "bright cheerful palette")),
    _n("the_chu", "Numbers that big mean nothing.", the="Numbers that big|mean nothing."),
    _n("canh", "So try it once a day.", ve=_ve("one person putting a single ticket into a jar",
              "repeating an everyday routine", "patient, resigned",
              "a plain kitchen counter", "the jar filling slightly", "warm palette")),
    _n("so_lieu", "You would need this long.", so=sn, don=un, chu=f"trying once every day",
       bt="dong_ho", dinh=True,
       ve=_ve("an enormous calendar wall stretching past the top of the frame",
              "pages upon pages, no end visible", "",
              "a plain room dwarfed by the calendar", "one tiny figure at the base",
              "restrained palette")),
    _n("chart", "Next to things you fear.", don="1 in N",
       cot=[{"nhan": "lightning", "v": 1222000}, {"nhan": ten.split()[0][:9], "v": N}], dinh=True),
    _n("canh", "Somebody still wins.", dinh=True,
       ve=_ve("one small figure holding a ticket, arms half raised",
              "standing alone in an enormous empty stadium", "quietly stunned",
              "endless empty seats rising in every direction",
              "the figure tiny at the centre of the field", "bright palette")),
            ])


def sinh_hiddenfee(i):
    ten, gia, phan = PHI_AN[i % len(PHI_AN)]
    lon = max(phan, key=lambda x: x[1])
    return (f"What is inside {ten}", f"WHAT IS INSIDE {ten.upper()}", f"{lon[1]}% {lon[0].upper()}",
            [
    _n("so_lieu", "You pay this.", so=_tien(gia), don="", bt="tien", dinh=True,
       ve=_ve("one hand paying at a counter", "handing over payment", "ordinary, unthinking",
              "a plain shop counter", "the payment sharp and close", "muted editorial palette")),
    _n("the_chu", "Almost none of it goes where you think.",
       the="Almost none of it|goes where you think."),
    _n("chart", "Here is the split.", don="percent of the price",
       cot=[{"nhan": x[0].split()[-1][:9], "v": x[1]} for x in phan], dinh=True),
    _n("so_lieu", "The biggest slice.", so=f"{lon[1]}%", don=lon[0], bt="tien", dinh=True,
       ve=_ve("a large pie chart drawn flat on a plain wall, one slice much bigger",
              "one slice clearly dominating", "", "a clean plain wall",
              "nothing in the foreground", "muted editorial palette")),
    _n("chia_doi", "What you assumed, and what it is.",
       trai={"nhan": "you assumed", "bt": "hop", "so": "the product"},
       phai={"nhan": "actually", "bt": "tien", "so": lon[0]}, dinh=True),
    _n("canh", "Now you can see the price.", dinh=True,
       ve=_ve("the same everyday purchase sitting alone",
              "unchanged, but seen differently", "",
              "a plain surface, generous empty space", "a soft shadow beneath",
              "muted editorial palette")),
            ])


def sinh_yearsof(i):
    ten, gio, bt = DOI_NGUOI[i % len(DOI_NGUOI)]
    tong = gio * 365.25 * 79          # tuổi thọ trung bình Mỹ ~79
    sn, un = _lau(tong)
    return (f"Years of your life spent {ten}", f"HOW LONG YOU SPEND {ten.upper()}", f"{sn} {un.upper()}",
            [
    _n("canh", "It is a few hours a day.", ve=_ve(f"one person {ten}",
              "doing it casually, as always", "unremarkable", "a plain everyday setting",
              "flat ground", "bright palette")),
    _n("so_lieu", "That is today.", so=f"{gio:g}", don="hours a day", bt=bt),
    _n("the_chu", "Now add up a whole life.", the="Now add up|a whole life."),
    _n("dem", "Day after day after day.", n=18, ngay=True, chu="every single day", ve=_ve(
        "the same person repeating the same action", "over and over", "worn by repetition",
        "the same plain setting unchanged", "flat ground", "muted palette")),
    _n("so_lieu", "Across seventy-nine years.", so=sn, don=un, chu=f"spent {ten}",
       bt=bt, dinh=True,
       ve=_ve("an enormous hourglass towering over a small figure",
              "sand piled high at the bottom", "the figure looking up",
              "a plain backdrop", "the figure tiny at the base", "restrained palette")),
    _n("chia_doi", "Against one whole life.",
       trai={"nhan": ten, "bt": bt, "so": f"{sn} {un}"},
       phai={"nhan": "a whole life", "bt": "nguoi", "so": "79 years"}, dinh=True),
    _n("canh", "Nobody adds it up.", dinh=True,
       ve=_ve("one person standing still, looking at their own hands",
              "having just realised something", "quiet, thoughtful",
              "a plain calm room", "flat floor", "warm muted palette")),
            ])


def sinh_howloud(i):
    ten, db, bt = AM_THANH[i % len(AM_THANH)]
    lan = 10 ** ((db - 60) / 10.0)
    return (f"How loud is {ten}", f"HOW LOUD IS {ten.upper()}", f"{db} DECIBELS",
            [
    _n("so_lieu", "Here is the number.", so=f"{db}", don="decibels", chu=ten, bt=bt, dinh=True,
       ve=_ve(f"{ten} shown clearly, sound waves radiating outward",
              "loud, waves rippling out", "", "a plain backdrop",
              "the source sharp and central", "high-contrast palette")),
    _n("the_chu", "Decibels do not add up the way you think.",
       the="Decibels do not add up|the way you think."),
    _n("chia_doi", "Ten more is ten times more.",
       trai={"nhan": "normal talking", "bt": "nguoi", "so": "60 dB"},
       phai={"nhan": ten, "bt": bt, "so": f"{db} dB"}, dinh=True),
    _n("so_lieu", "So this is the real gap.", so=f"{lan:,.0f}x", don="the energy of talking",
       bt=bt, dinh=True),
    _n("chart", "On one scale.", don="decibels",
       cot=[{"nhan": "whisper", "v": 30}, {"nhan": "talking", "v": 60},
            {"nhan": ten.split()[-1][:9], "v": db}], dinh=True),
    _n("canh", "Your ears do the maths for you.", dinh=True,
       ve=_ve("one person covering their ears", "flinching away from a loud source",
              "wincing", "a plain backdrop", "sound waves in the near foreground",
              "high-contrast palette")),
            ])


def sinh_whatweighs(i):
    a = KHOI_LUONG[i % len(KHOI_LUONG)]
    b = KHOI_LUONG[(i + 3) % len(KHOI_LUONG)]
    lon, nho = (a, b) if a[1] >= b[1] else (b, a)
    lan = lon[1] / nho[1]
    return (f"{lon[0].title()} vs {nho[0]}", f"HOW HEAVY IS {lon[0].upper()}", f"{lon[1]:,} POUNDS",
            [
    _n("chia_doi", "Two things. One scale.",
       trai={"nhan": nho[0], "bt": nho[2], "so": f"{nho[1]:,} lb"},
       phai={"nhan": lon[0], "bt": lon[2], "so": f"{lon[1]:,} lb"}, dinh=True),
    _n("the_chu", "Weight is the sense we are worst at.",
       the="Weight is the sense|we are worst at."),
    _n("so_lieu", "That is the multiple.", so=f"{lan:,.0f}x", don="heavier", bt=lon[2], dinh=True,
       ve=_ve(f"{lon[0]} resting on one side of an enormous balance scale",
              f"{nho[0]} piled high on the other side", "",
              "a plain backdrop, the scale filling the frame",
              "flat ground beneath the scale", "bright palette")),
    _n("chart", "On one scale.", don="pounds",
       cot=[{"nhan": nho[0].split()[-1][:9], "v": nho[1]},
            {"nhan": lon[0].split()[-1][:9], "v": lon[1]}], dinh=True),
    _n("canh", "You guessed wrong. Everyone does.", dinh=True,
       ve=_ve("one person straining to lift something far too heavy",
              "heaving with both arms, feet planted", "red-faced, struggling",
              "a plain backdrop", "the object barely off the ground", "bright palette")),
            ])


def sinh_rightnow(i):
    ds = [("asleep right now", 0.42, "dong_ho"), ("in a car right now", 0.02, "xe"),
          ("eating right now", 0.06, "hop"), ("having a birthday today", 1 / 365.25, "nguoi")]
    ten, ti, bt = ds[i % len(ds)]
    n = int(8_000_000_000 * ti)
    # Quy về đơn vị tai người nghe ra: "3360 MILLION" không ai đọc, "3.4 BILLION" thì đọc ngay.
    gon = (f"{n/1e9:.1f} BILLION".replace(".0 ", " ") if n >= 1e9
           else f"{n/1e6:.0f} MILLION" if n >= 1e6 else f"{n:,}")
    return (f"How many people are {ten}", f"HOW MANY PEOPLE ARE {ten.upper()}", gon,
            [
    _n("canh", "Right now, while you watch this.", dinh=True,
       ve=_ve("one person alone, mid-ordinary-moment", "caught in a normal instant", "neutral",
              "a plain everyday setting", "flat ground", "bright palette")),
    _n("so_lieu", "This many people are too.", so=f"{n:,}", don="people", bt=bt, dinh=True,
       ve=_ve("an immense crowd stretching to the horizon in every direction",
              "all of them still, all at once", "",
              "an enormous open plain filled with people", "the front row sharp",
              "bright palette")),
    _n("chia_doi", "You, and all of them.",
       trai={"nhan": "you", "bt": "nguoi", "so": "1"},
       phai={"nhan": "them", "bt": bt, "so": f"{n/1e6:.0f} mn"}, dinh=True),
    _n("the_chu", "Nothing you do is only yours.",
       the="Nothing you do|is only yours.", dinh=True),
    _n("canh", "That is the whole point.", dinh=True,
       ve=_ve("one person standing at the front of an enormous crowd",
              "turning to look back at all of them", "quietly amazed",
              "the crowd filling the entire background", "the person sharp and close",
              "bright palette")),
            ])


def sinh_howhot(i):
    ten, f, bt = NHIET_DO[i % len(NHIET_DO)]
    c = (f - 32) * 5 / 9
    return (f"How hot is {ten}", f"HOW HOT IS {ten.upper()}", f"{f:,}°F",
            [
    _n("so_lieu", "Here is the number.", so=f"{f:,}", don="degrees fahrenheit", chu=ten,
       bt=bt, dinh=True,
       ve=_ve(f"{ten} shown clearly, heat shimmering above it",
              "radiating heat", "", "a plain backdrop", "the source sharp and central",
              "warm high-contrast palette")),
    _n("chia_doi", "Next to a warm room.",
       trai={"nhan": "a warm room", "bt": "nha", "so": "70°F"},
       phai={"nhan": ten, "bt": bt, "so": f"{f:,}°F"}, dinh=True),
    _n("the_chu", "Your body has a very narrow window.",
       the="Your body has|a very narrow window."),
    _n("so_lieu", "Outside it, minutes matter.", so=f"{c:,.0f}", don="degrees celsius",
       chu="the same temperature, other scale", bt=bt),
    _n("chart", "On one scale.", don="degrees fahrenheit",
       cot=[{"nhan": "room", "v": 70}, {"nhan": "boiling", "v": 212},
            {"nhan": ten.split()[-1][:9], "v": f}], dinh=True),
    _n("canh", "We live in a very thin band.", dinh=True,
       ve=_ve("one small figure standing between an icy side and a burning side",
              "arms out, balancing between the two", "wary",
              "half the background frozen blue, half glowing orange",
              "the dividing line running under the figure", "high-contrast palette")),
            ])


def sinh_smallest(i):
    a = CUC_NHO[i % len(CUC_NHO)]
    b = CUC_NHO[(i + 2) % len(CUC_NHO)]
    lon, nho = (a, b) if a[1] >= b[1] else (b, a)
    lan = lon[1] / nho[1]
    return (f"{lon[0].title()} vs {nho[0]}", f"HOW SMALL IS {nho[0].upper()}",
            f"{lan:,.0f}x SMALLER",
            [
    _n("canh", "Start with something you can see.", dinh=True,
       ve=_ve(f"{lon[0]} shown enormous and clear, filling the frame",
              "magnified far beyond life size", "", "a plain backdrop",
              "the object sharp and central", "clean cool palette")),
    _n("so_lieu", "Now go smaller.", so=f"{lan:,.0f}x", don="smaller", bt="trai_dat", dinh=True,
       ve=_ve(f"{nho[0]} shown as a tiny speck beside {lon[0]}",
              "almost invisible next to it", "", "a plain backdrop",
              "both objects on the same flat line", "clean cool palette")),
    _n("the_chu", "Your eyes stop long before this.",
       the="Your eyes stop|long before this."),
    _n("chia_doi", "Both, at true scale.",
       trai={"nhan": lon[0], "bt": "hop", "so": f"{lon[1]:.0e} m"},
       phai={"nhan": nho[0], "bt": "cay", "so": f"{nho[1]:.0e} m"}, dinh=True),
    _n("canh", "Everything you are is built from that.", dinh=True,
       ve=_ve("one person's outline filled with countless tiny dots",
              "standing still, made visibly of small parts", "calm",
              "a plain dark backdrop", "the dots sharp near the edge of the figure",
              "clean cool palette")),
            ])


BO_SINH = {"howlong": sinh_howlong, "howbig": sinh_howbig, "realcost": sinh_realcost,
           "howmuch": sinh_howmuch, "whatif": sinh_whatif, "survive": sinh_survive,
           "dayinlife": sinh_dayinlife, "wheregoes": sinh_wheregoes,
           "therules": sinh_therules, "speedof": sinh_speedof,
           "odds": sinh_odds, "hiddenfee": sinh_hiddenfee, "yearsof": sinh_yearsof,
           "howloud": sinh_howloud, "whatweighs": sinh_whatweighs, "rightnow": sinh_rightnow,
           "howhot": sinh_howhot, "smallest": sinh_smallest}


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
    "odds":       "You will not win this.",
    "hiddenfee":  "You are not paying for the thing.",
    "yearsof":    "It is a few hours a day.",
    "howloud":    "Your ears round it off.",
    "whatweighs": "You guessed wrong.",
    "rightnow":   "You are never doing it alone.",
    "howhot":     "Your body has a narrow window.",
    "smallest":   "Your eyes give up long before this.",
}


# ══ BẢN DÀI: MỘT CHƯƠNG CHO MỖI DÒNG DỮ LIỆU ════════════════════════════════════════════════
# Bản dài 7-10 phút cần ~200 nhịp ở nhịp cắt 2,1 giây. Không nhờ AI viết 200 nhịp: kênh này
# sống bằng "mọi con số tính ra được", mà AI viết 200 nhịp là 200 chỗ để bịa.
#
# Cách làm giữ được điều ấy: bản dài = NỐI CÁC CHƯƠNG, mỗi chương là một dòng trong bảng dữ
# liệu, và mỗi chương dùng lại đúng bộ sinh của bản ngắn. Mười dòng -> mười chương -> ~200 nhịp,
# và mọi con số vẫn là phép tính, không phải phép tra.
#
# Thêm ba thứ chỉ bản dài mới có:
#   · MỞ ĐẦU đặt câu hỏi chung và hứa hẹn (giữ chân 30 giây đầu)
#   · THẺ CHƯƠNG giữa các chương — người xem biết mình đang ở đâu, và đây cũng là mốc để đặt
#     chương trong phần mô tả YouTube (thứ hai video tham chiếu KHÔNG có)
#   · TỔNG HỢP cuối: một biểu đồ so tất cả các chương, thứ chỉ bản dài làm được
def sinh_long(ma: str, idx: int, so_chuong: int = 10):
    k = next(x for x in KENH if x["ma"] == ma)
    bo = BO_SINH[k["sinh"]]
    nhip, muc = [], []

    # ── MỞ ĐẦU ──────────────────────────────────────────────────────────────────────────
    tieu0, hook0, hp0, _n0 = bo(idx)
    nhip.append(_n("the_chu", HOOK_LOI.get(ma, "Here is the question."),
                   the=HOOK_LOI.get(ma, "").replace(". ", ".|"), dinh=True))
    nhip.append(_n("canh", "We are going to answer it properly.", dinh=True,
                   ve=_ve("one simple cartoon figure standing alone at the centre",
                          "looking straight ahead, about to begin",
                          "calm and curious",
                          "a plain open background with a single horizon line",
                          "flat empty ground", "bright cheerful palette")))

    # ── CÁC CHƯƠNG ──────────────────────────────────────────────────────────────────────
    for c in range(so_chuong):
        tieu, _h, _hp, nc = bo(idx + c)
        if not nc:
            continue
        muc.append((len(nhip), tieu))
        # thẻ chương: dùng chính khuôn thẻ chữ, nhưng NGẮN — nó là mốc, không phải nội dung
        nhip.append(_n("the_chu", tieu + ".", the=f"{c+1}.|{tieu}"))
        nhip.extend(nc)

    # ── TỔNG HỢP ────────────────────────────────────────────────────────────────────────
    # Chỉ bản dài mới làm được: đặt cả mười chương cạnh nhau trên một trục. Đây là lý do người
    # xem ngồi hết 8 phút thay vì xem một bản ngắn.
    cot = []
    for c in range(min(so_chuong, 6)):
        t2, _h2, hp2, _n2 = bo(idx + c)
        v = "".join(ch for ch in (hp2.split()[0] if hp2 else "0") if ch.isdigit() or ch == ".")
        try:
            cot.append({"nhan": t2.split()[-1][:9], "v": float(v or 0)})
        except ValueError:
            pass
    if len(cot) >= 2:
        nhip.append(_n("chart", "Here they all are, side by side.", don="compared", cot=cot, dinh=True))
    nhip.append(_n("canh", "That is the whole picture.", dinh=True,
                   ve=_ve("one simple cartoon figure seen from behind, small in the frame",
                          "looking out over a wide open view",
                          "quietly satisfied",
                          "a broad open landscape stretching to a distant horizon",
                          "flat ground in the lower part of the frame",
                          "warm bright palette")))
    return (f"{k['ten'].title()} — {so_chuong} answers", hook0, hp0, nhip, muc)


# ══ SHORT DỰNG LẠI TỪ KỊCH BẢN CỦA LONG — KHÔNG CẮT VIDEO ═══════════════════════════════════
# Anh: *"short không phải cắt long ra, mà là chỉ lấy KỊCH BẢN từ long ra rồi dựng lại sao cho
# hook đúng tỉ lệ, tránh lỗi che khuất hay không đúng định dạng."*
#
# Anh đúng, và điều này bác kế hoạch trước của em (cắt theo cờ `dinh`). Cắt video thì short
# thừa hưởng NGUYÊN bố cục của bản ngang: chữ số đặt theo ngân sách chiều cao 1080, dải chữ
# đặt theo khung rộng. Đem khung ấy nhét vào 1080×1920 thì hoặc phải cắt hai mép (mất chữ),
# hoặc phải thêm viền đen (sai định dạng Shorts). Cả hai đều hỏng, và hỏng theo cách không sửa
# được ở khâu cắt.
#
# Dựng lại từ kịch bản thì mỗi tỉ lệ có bố cục riêng, hook riêng, và ảnh nền sinh ĐÚNG hướng
# khung (`_ten()` đã mang hậu tố `_d`/`_n` từ trước).
#
# Quan hệ giữa hai bản: CHƯƠNG k của bản dài = tập ngắn thứ (idx + k). Cùng một bộ sinh, cùng
# một dữ liệu, cùng những con số — chỉ khác khuôn hình và nhịp. Nên không có nguy cơ hai bản
# nói khác nhau, thứ sẽ xảy ra nếu viết hai kịch bản riêng.
def short_tu_long(ma: str, idx: int, chuong: int) -> str:
    """Dựng bản short 9:16 từ ĐÚNG kịch bản của chương `chuong` trong bản dài `idx`."""
    return mot_tap(ma, idx + chuong, doc=True, long=False)


def mot_tap(ma: str, idx: int, doc: bool = True, long: bool = False,
            so_chuong: int = 10) -> str:
    k = next((x for x in KENH if x["ma"] == ma), None)
    if not k:
        print(f"❌ không có kênh {ma}")
        return ""
    muc = []
    if long:
        tieu, hook, hook_phu, nhip, muc = sinh_long(ma, idx, so_chuong)
    else:
        tieu, hook, hook_phu, nhip = BO_SINH[k["sinh"]](idx)
    # Nhịp 0 = HOOK. Chèn ở đây chứ không viết vào từng bộ sinh: hook là quy tắc chung của cả
    # bộ phim, không phải nội dung riêng của một kênh — viết mười chỗ là mười chỗ để lệch nhau.
    # CHỈ chèn khung số liệu khi THẬT SỰ CÓ SỐ. Bốn kênh (whatif · dayinlife · wheregoes ·
    # therules) không có con số tiêu đề, và chèn bừa thì ra một khung số liệu RỖNG — chữ số
    # trống, không biểu tượng, chỉ còn dòng chú thích lơ lửng giữa nền trơn. Khung rỗng ở nhịp
    # mở đầu còn tệ hơn không có hook: ba giây đầu là ba giây quyết định.
    # Không có số thì hook nằm ở LỜI, đặt lên chính nhịp đầu vốn đã có ảnh.
    if HOOK_LOI.get(ma) and nhip and hook_phu.strip() and nhip[0].get("khuon") != "so_lieu":
        # 1/9 (lần 2) — NHỊP HOOK PHẢI CÓ GÌ ĐỂ NHÌN.
        # Chốt chặn ở trên chỉ hỏi "có SỐ không", nên nó cho qua một thẻ số đặt giữa nền trơn:
        # soi khung đầu của `howmuch` thì 60% khung là màu xám trống, con số lơ lửng trên cùng.
        # Đó đúng là "tấm biển tiêu đề" mà luật §12.12 cấm — *hook phải là NỘI DUNG của cảnh đầu*.
        #
        # Cho nó thừa hưởng hình của nhịp gần nhất: ưu tiên `bt` (vẽ bằng code, miễn phí, không
        # bao giờ hỏng), rồi mới tới `ve` (ảnh AI, tốn một lượt gọi và có thể trượt).
        # Lấy hình của NHỊP ĐẦU, không lấy hình đầu tiên tìm thấy trong cả tập.
        # Bản trước quét cả danh sách tìm `bt` nào cũng được: với `survive` tập 0 (Kỷ Băng Hà)
        # nó vớ phải ngọn lửa của nhịp "a week without fire" ở tận cuối — hook mở đầu bằng một
        # biểu tượng nói SAI chủ đề tập. Nhịp đầu thì theo cấu trúc luôn nói đúng chuyện đang kể.
        # Khai CẢ HAI: `ve` cho ảnh thật, `bt` làm tầng dự phòng khi ảnh trượt (engine tự bỏ `bt`
        # khi đã có ảnh, nên không bao giờ vẽ đè).
        _dau = nhip[0]
        _ve = _dau.get("ve") or ""
        _bt = _dau.get("bt") or next((n.get("bt") for n in nhip[:2] if n.get("bt")), "")
        nhip.insert(0, {
            "khuon": "so_lieu", "loi": HOOK_LOI[ma], "dinh": True,
            "so": (hook_phu.split()[0] if hook_phu else ""),
            "don": (" ".join(hook_phu.split()[1:]) if hook_phu else ""),
            "chu": hook.rstrip("?").title() + "?",
            **({"ve": _ve} if _ve else {}), **({"bt": _bt} if _bt else {}),
        })
    elif HOOK_LOI.get(ma) and nhip:
        nhip[0]["loi"] = HOOK_LOI[ma]
        nhip[0]["dinh"] = True
    slug = f"{ma}_{idx:04d}" + ("_long" if long else "")
    print(f"\n▶ {k['ten']} · {tieu}", flush=True)

    hat = sum(ord(c) for c in ma) + idx
    # Giọng kể: một người, trầm, chậm vừa. Phim giải thích không có đối thoại — mọi lời là
    # của người kể, nên `doc_hai_giong` chỉ dùng một giọng cho cả hai khe.
    gr = GU_RIENG.get(ma, ("en-US-GuyNeural", NHAC[0], ""))
    # Nhịp và cao độ cũng lệch theo kênh: cùng một giọng máy mà khác tốc độ đã đủ để tai
    # tách ra hai người kể. Băm từ mã kênh nên cố định qua mọi tập.
    _h = sum(ord(c) for c in ma)
    ga = (gr[0], f"{-8 + _h % 9}%", f"{-4 + _h % 7}Hz")
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
             "nhac": _nhac(ma, long), "nhacVol": _am_nhac(_nhac(ma, long)),
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
        # 1/9 — IN LỖI PHẢI LỌC, KHÔNG CẮT ĐUÔI.
        # Bản trước lấy 260 ký tự CUỐI stderr. Remotion in cảnh báo phông ở cuối, nên lỗi thật
        # bị đẩy ra ngoài cửa sổ và tôi đọc được đúng câu cảnh báo vô hại. Hai lần trong ngày
        # cách in lỗi của chính mình giấu mất nguyên nhân.
        _e = (r.stderr or r.stdout or "")
        _dong = [d for d in _e.splitlines()
                 if any(t in d for t in ("Error", "error:", "Cannot", "undefined is not",
                                         "TypeError", "ReferenceError", "failed", "Expected"))]
        print("   ❌ render hỏng:")
        for d in (_dong[:4] or _e.splitlines()[-4:]):
            print(f"      {d.strip()[:190]}")
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
    ap.add_argument("--ngang", action="store_true", help="dựng bản 16:9 thay vì 9:16")
    ap.add_argument("--long", action="store_true", help="bản dài (chương theo dòng dữ liệu)")
    # Anh: *"long demo e dựng ngắn a coi là được, nào vào dựng thật thì scale lên."*
    # Đúng: cấu trúc bản dài (mở đầu -> thẻ chương -> các chương -> biểu đồ tổng hợp -> chốt)
    # kiểm được với 3 chương y như với 10, mà tốn 1/3 số ảnh. Vào sản xuất chỉ đổi con số này.
    ap.add_argument("--chuong", type=int, default=10, help="số chương của bản dài (demo: 3)")
    ap.add_argument("--short-tu-long", type=int, default=-1, metavar="N",
                    help="dựng N short 9:16 từ kịch bản N chương đầu của bản dài")
    a = ap.parse_args()
    ds = [x.strip() for x in a.kenh.split(",") if x.strip()] or [k["ma"] for k in KENH]
    if a.short_tu_long > 0:
        ra = [v for de in ds for c in range(a.short_tu_long)
              if (v := short_tu_long(de, a.tu, c))]
    else:
        ra = [v for j, de in enumerate(ds) for i in range(a.so)
              if (v := mot_tap(de, a.tu + i + j, doc=not a.ngang, long=a.long,
                               so_chuong=a.chuong))]
    print(f"\n✅ {len(ra)}/{len(ds) * a.so} video")
    return 0 if ra else 1


if __name__ == "__main__":
    raise SystemExit(main())
