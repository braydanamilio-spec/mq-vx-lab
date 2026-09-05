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
import math
import os
import re
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

# ══ QUÃNG ĐƯỜNG — MỖI MỤC MANG THEO LOẠI NGỮ PHÁP CỦA NÓ  (4/9/2026) ═══════════════════════
# Bảng cũ chỉ có tên, và BỐN khuôn câu đều ghép `f"… {ten}"` như thể mọi mục cùng một loại.
# Chúng không cùng loại, và đo trên 22 mục thì **13 mục (59%)** ra câu sai:
#
#     "The distance to all the way around Saturn."      <- câu đọc
#     "Walking to all the way around Saturn"            <- TIÊU ĐỀ YOUTUBE
#     "HOW LONG TO WALK TO ALL THE WAY AROUND SATURN?"  <- chữ hook trên khung
#     "New York to Los Angeles hanging huge and pale in a deep open sky"   <- prompt gửi FLUX
#
# Câu cuối là nặng nhất: nó không sai ngữ pháp mà VÔ NGHĨA, và nó là thứ mô hình vẽ theo.
#
# §12.5 đúng từng chữ — một câu luật đúng trong ngữ cảnh sinh ra nó (bảng ban đầu 10 mục, hầu
# hết là điểm đến thiên thể), sai ở ngữ cảnh mới (nối thêm 12 mục gồm tuyến đường và quãng
# đường). Và §13.9: chữa bằng DANH SÁCH NGOẠI LỆ thì danh sách ấy vô hạn — mỗi mục thêm sau
# lại là một ngoại lệ mới. Nên loại ngữ pháp phải là MỘT TRƯỜNG của chính dữ liệu.
#
#   den    điểm đến   -> "to X"     · "Walking to the Moon"
#   tuyen  A đến B    -> "from X"   · "Walking from New York to Los Angeles"
#   vong   vòng quanh -> "X"        · "Walking all the way around Saturn"
#   vat    một chặng  -> "of X"     · "Walking the Appalachian Trail"
#
# Trường thứ năm `troi` là TÊN VẬT TREO TRÊN TRỜI, dùng cho câu tả cảnh. Rỗng thì cảnh dùng
# khuôn trung tính. Không suy ra từ `bt` vì `trai_dat` là biểu tượng quả cầu dùng chung — nó
# đứng cho cả Sao Hoả, Sao Thổ lẫn rãnh Mariana, nên suy từ nó là đoán.
#
# Hai mục được ĐỔI TÊN thay vì thêm ngoại lệ, vì tên cũ đã chứa sẵn một danh từ đo lường nên
# mọi khuôn câu đều ra chữ lặp ("The distance of the length of the Mississippi"):
#   "the length of the Mississippi"  -> "the Mississippi River"
#   "the height of a passenger jet"  -> "jet cruising altitude"
QUANG_DUONG = [                                  # dặm
    ("the Moon",                       238900,    "mat_trang", "den",   "the Moon"),
    ("the Sun",                      92960000,    "mat_troi",  "den",   "the Sun"),
    ("Mars at its closest",          33900000,    "trai_dat",  "den",   "Mars"),
    ("all the way around the Earth",    24901,    "trai_dat",  "vong",  "the Earth"),
    ("New York to Los Angeles",          2445,    "xe",        "tuyen", ""),
    ("the bottom of the Mariana Trench",  6.8,    "trai_dat",  "den",   ""),
    ("the top of Mount Everest",          5.5,    "trai_dat",  "den",   ""),
    ("New York to London",               3459,    "may_bay",   "tuyen", ""),
    ("the Mississippi River",            2340,    "trai_dat",  "vat",   ""),
    ("all the way around Saturn",      235298,    "trai_dat",  "vong",  "Saturn"),
    # ── NỐI THÊM 1/9 ────────────────────────────────────────────────────────────────────
    # Bảng cũ 10 mục, mà bộ sinh lấy `ds[i % n]` -> kênh lặp y hệt từ tập 10. Đo được cả 18
    # kênh lặp trong vòng 1-21 tập. Mọi khoảng cách bằng DẶM (§12.13: kênh Mỹ, đơn vị Mỹ).
    ("the International Space Station",   254,     "trai_dat", "den",   ""),
    ("Miami to Seattle",                 2734,     "may_bay",  "tuyen", ""),
    ("the edge of space",                  62,     "may_bay",  "den",   ""),
    ("a cross-country road trip",        3000,     "xe",       "vat",   ""),
    ("Chicago to Denver",                 920,     "xe",       "tuyen", ""),
    ("the Moon and back",              477800,     "mat_trang","den",   "the Moon"),
    ("a year of the average commute",    4700,     "xe",       "vat",   ""),
    ("the Appalachian Trail",            2190,     "cay",      "vat",   ""),
    ("Alaska to Florida",                4400,     "xe_buyt",  "tuyen", ""),
    ("jet cruising altitude",               7,     "may_bay",  "den",   ""),
    ("Boston to Miami",                  1500,     "xe",       "tuyen", ""),
    ("a marathon",                         26,     "nguoi",    "vat",   ""),
]

# Giới từ theo loại: (cho câu "Walking …" và chữ hook, cho câu "The distance …").
# Hai cột vì chúng KHÁC NHAU ở `vat`: "Walking the Appalachian Trail" nhưng "The distance OF
# the Appalachian Trail" — dùng chung một giới từ là ra một trong hai câu sai.
GIOI_TU = {"den":   ("to ",   "to "),
           "tuyen": ("from ", "from "),
           "vong":  ("",      ""),
           "vat":   ("",      "of ")}

CO_LON = [                                       # feet
    ("a blue whale",           98.0, "ft", "ca_voi"),
    ("a school bus",           36.0, "ft", "xe_buyt"),
    ("a giraffe",              18.0, "ft", "huou"),
    ("an adult human",          5.6, "ft", "nguoi"),
    ("a Boeing 747",          232.0, "ft", "may_bay"),
    ("the Statue of Liberty",  305.0, "ft", "nha"),
    ("a football field",      300.0, "ft", "nguoi"),
    # ── NỐI THÊM 1/9. Chiều cao/dài bằng FOOT. Cặp lấy bằng `_cap`.
    ("a ten-storey building",       110.0, "ft", "nha"),
    ("a grand piano",                 9.0, "ft", "dan_piano"),
    ("a refrigerator",                6.0, "ft", "hop"),
    ("a smartphone",                  0.5, "ft", "dien_thoai"),
    ("a housecat",                    1.5, "ft", "meo"),
    ("a passenger jet",             230.0, "ft", "may_bay"),
    ("the Empire State Building",  1454.0, "ft", "nha"),
    ("a redwood tree",              350.0, "ft", "cay"),
    ("a city bus",                   40.0, "ft", "xe_buyt"),
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
    # ── NỐI THÊM 1/9. Mẫu số là 1-trong-N, số thật.
    ("finding a four-leaf clover",           10000, "cay"),
    ("a hole in one",                        12500, "hop"),
    ("matching five numbers but not the ball", 11688054, "tien"),
    ("a shark attack in your lifetime",      3748067, "ca_voi"),
    ("becoming an astronaut after applying",  1500, "may_bay"),
    ("drawing the ace of spades",               52, "tien"),
    ("rolling snake eyes",                      36, "hop"),
    ("your flight being cancelled",             56, "may_bay"),
    # ── ĐỢT 2 (1/9). Mẫu số 1-trong-N.
    ("being dealt a royal flush",          649740, "tien"),
    ("getting a hole in your parachute",   750000, "may_bay"),
    ("guessing a stranger's PIN",           10000, "tien"),
    ("both of your coins landing edge-up",  36000000, "tien"),
    ("being audited this year",               220, "giay"),
    ("your luggage being lost",               158, "may_bay"),
    ("meeting someone with your birthday",    365, "dong_ho"),
    ("being left-handed",                      10, "nguoi"),
    ("having identical twins",                250, "nguoi"),
    ("a meteorite hitting your house",   182138880, "nha"),
    ("winning a coin toss five times",         32, "tien"),
    ("being born in a leap second",      31557600, "dong_ho"),
]
PHI_AN = [                                          # (thứ, giá, các phần %)
    ("a $6 coffee", 6.00, [("the beans", 6), ("the cup and lid", 4),
                           ("rent and power", 26), ("the person who made it", 24),
                           ("everything else", 40)]),
    ("a $15 movie ticket", 15.00, [("the studio", 55), ("the theater", 25),
                                    ("staff", 12), ("everything else", 8)]),
    ("a $30 delivered meal", 30.00, [("the food", 40), ("the restaurant", 18),
                                     ("the driver", 12), ("the app", 30)]),
    ("a $1200 phone", 1200.00, [("the parts", 38), ("assembly", 3),
                                ("research", 12), ("the shop", 12), ("the brand", 35)]),
    # ── NỐI THÊM 1/9. Bóc giá thành từng phần — phần trăm cộng lại đúng 100.
    ("a $12 fast-food meal", 12.0, [("the food", 30), ("packaging", 8), ("staff", 27),
                                     ("rent and power", 20), ("profit", 15)], ),
    ("a $4 bottle of water", 4.0, [("the water", 1), ("the bottle", 12), ("shipping", 22),
                                    ("the store's cut", 40), ("profit", 25)], ),
    ("a $60 pair of sneakers", 60.0, [("materials", 12), ("factory labor", 4),
                                       ("shipping", 8), ("marketing", 26),
                                       ("the retailer", 34), ("profit", 16)], ),
    ("a $25 movie ticket night", 25.0, [("the studio's cut", 50), ("the venue", 18),
                                         ("staff", 14), ("building costs", 12),
                                         ("profit", 6)], ),
    ("a $200 airline ticket", 200.0, [("fuel", 24), ("crew", 18), ("the aircraft", 16),
                                       ("airport fees", 15), ("taxes", 14),
                                       ("profit", 13)], ),
    ("a $8 pint of beer", 8.0, [("the beer", 11), ("the glass and tap", 5),
                                 ("staff", 30), ("rent", 34), ("profit", 20)], ),
    ("a $35 delivered pizza", 35.0, [("the pizza", 22), ("the driver", 14),
                                      ("the app's cut", 30), ("the restaurant", 24),
                                      ("profit", 10)], ),
    # ── ĐỢT 2 (1/9): n = 12 nên bản dài 10 chương chỉ có 6 mục để dùng -> tự lặp 4 lần.
    ("a $30 concert ticket", 30.0, [("the artist", 24), ("the venue", 20),
                                     ("the promoter", 18), ("service fees", 26),
                                     ("taxes", 12)]),
    ("a $5 cup of coffee at a chain", 5.0, [("the beans", 5), ("milk and cup", 9),
                                             ("staff", 28), ("rent", 32),
                                             ("head office", 14), ("profit", 12)]),
    ("a $90 pair of jeans", 90.0, [("cotton", 8), ("sewing", 5), ("shipping", 7),
                                    ("brand and marketing", 28), ("the shop", 36),
                                    ("profit", 16)]),
    ("a $15 streaming month", 15.0, [("content licensing", 55), ("servers", 12),
                                      ("payment fees", 4), ("marketing", 17),
                                      ("profit", 12)]),
    ("a $2,000 laptop", 2000.0, [("the parts", 45), ("assembly", 4), ("research", 13),
                                  ("marketing", 10), ("the retailer", 15),
                                  ("profit", 13)]),
    ("a $70 hotel night", 70.0, [("staff", 26), ("the building", 30), ("utilities", 11),
                                  ("booking site's cut", 18), ("profit", 15)]),
    ("a $9 bag of chips", 9.0, [("potatoes", 6), ("oil and seasoning", 5),
                                 ("the bag", 8), ("shipping", 12),
                                 ("the store", 45), ("profit", 24)]),
    ("a $45 video game", 45.0, [("development", 30), ("the platform's cut", 30),
                                 ("marketing", 20), ("the publisher", 12),
                                 ("profit", 8)]),
    ("a $600 flight", 600.0, [("fuel", 22), ("crew", 17), ("aircraft costs", 18),
                              ("airport and taxes", 28), ("profit", 15)]),
    ("a $18 cocktail", 18.0, [("the spirits", 12), ("mixers and ice", 4),
                              ("staff", 29), ("rent", 35), ("profit", 20)]),
    ("a $250 pair of running shoes", 250.0, [("materials", 9), ("factory labor", 3),
                                         ("shipping", 5), ("athlete endorsement", 12),
                                         ("marketing", 20), ("the retailer", 35),
                                         ("profit", 16)]),
    ("a $40 phone case", 40.0, [("plastic and rubber", 4), ("molding", 3),
                                 ("shipping", 6), ("brand licence", 22),
                                 ("the shop", 45), ("profit", 20)]),
]
DOI_NGUOI = [                                       # (việc, giờ mỗi ngày)
    ("sleeping", 8.0, "giuong"), ("looking at a phone", 4.5, "dien_thoai"),
    ("eating", 1.2, "hop"), ("commuting", 1.0, "xe"),
    ("waiting in lines", 0.3, "nguoi"), ("watching television", 2.8, "hop"),
    # ── NỐI THÊM 1/9. Giờ mỗi ngày trung bình của người Mỹ.
    ("doing housework",              1.8, "nha"),
    ("cooking",                      0.9, "lua"),
    ("scrolling social media",       2.4, "dien_thoai"),
    ("sitting in meetings",          1.1, "giay"),
    ("shopping",                     0.6, "tien"),
    ("caring for family",            1.5, "nguoi"),
    ("exercising",                   0.3, "nguoi"),
    ("reading",                      0.3, "giay"),
    # ── ĐỢT 2 (1/9). Giờ mỗi ngày, trung bình người Mỹ trưởng thành.
    ("waiting on hold",              0.08, "dien_thoai"),
    ("looking for things you lost",  0.15, "nha"),
    ("brushing your teeth",          0.06, "coc"),
    ("showering",                    0.20, "nha"),
    ("getting dressed",              0.15, "nguoi"),
    ("sitting in traffic",           0.45, "xe"),
    ("checking email",               0.90, "giay"),
    ("watching commercials",             0.60, "dien_thoai"),
    ("on video calls",               0.70, "dien_thoai"),
    ("doing laundry",                0.35, "hop"),
    ("walking the dog",              0.30, "nguoi"),
    ("paying bills",                 0.10, "tien"),
    ("standing in an elevator",           0.04, "nha"),
    ("scrolling before sleep",       0.55, "giuong"),
]
# XẾP THEO SỨC HÚT, KHÔNG XẾP TĂNG DẦN. Tập 0 là tập đầu tiên người xem gặp trên kênh mới —
# xếp tăng dần thì nó rơi vào "HOW LOUD IS A WHISPER?", một tiêu đề không ai bấm vào.
AM_THANH = [                                        # (thứ, decibel)
    ("a jet at takeoff", 140, "may_bay"), ("a rock concert", 110, "lua"),
    ("a motorbike", 95, "xe"), ("a vacuum cleaner", 75, "hop"),
    ("normal talking", 60, "nguoi"), ("a whisper", 30, "nguoi"),
    # ── NỐI THÊM 1/9. Decibel là thang LOG — chính điều làm kênh này đáng xem.
    ("a chainsaw",                      110,  "cay"),
    ("a subway train arriving",         100,  "xe_buyt"),
    ("a lawn mower",                     90,  "hop"),
    ("city traffic from the sidewalk",   85,  "xe"),
    ("a dishwasher",                     60,  "hop"),
    ("a quiet library",                  40,  "giay"),
    ("a bedroom at night",               30,  "giuong"),
    ("a firework overhead",             150,  "lua"),
    ("a gunshot",                       165,  "lua"),
    ("an ambulance siren up close",     120,  "xe"),
    ("a crying baby",                   110,  "nguoi"),
    ("a hair dryer",                     90,  "hop"),
    # ── ĐỢT 2 (1/9): cần n ≥ 24 để nửa dành cho bản dài đủ 10 chương mà không tự lặp.
    ("a whisper at arm's length",        20,  "nguoi"),
    ("rustling leaves",                  25,  "cay"),
    ("a ticking clock",                  35,  "dong_ho"),
    ("rain on a window",                 45,  "nha"),
    ("an office at work",                55,  "giay"),
    ("a washing machine spinning",       70,  "hop"),
    ("a busy restaurant",                80,  "hop"),
    ("a rock concert front row",        115,  "nguoi"),
    ("a jackhammer",                    100,  "hop"),
    ("thunder directly overhead",       120,  "lua"),
    ("a balloon popping by your ear",   157,  "hop"),
    ("a car horn at ten feet",          110,  "xe"),
    ("a school cafeteria at lunch",      85,  "nguoi"),
]
KHOI_LUONG = [                                      # (thứ, pound) — mạnh nhất trước
    ("a school bus", 24000, "xe_buyt"), ("a small car", 2900, "xe"),
    ("a grand piano", 990, "dan_piano"), ("an adult human", 180, "nguoi"),
    ("a car tire", 25, "xe"), ("a housecat", 10, "meo"),
    # ── NỐI THÊM 1/9. Cân nặng bằng POUND. Cặp lấy bằng `_cap` nên n mục cho n(n−1)/2 tập.
    ("a bull elephant",         12000,  "ca_voi"),
    ("a full moving truck",     26000,  "xe_buyt"),
    ("a blue whale",           300000,  "ca_voi"),
    ("a vending machine",         800,  "hop"),
    ("a refrigerator",            250,  "hop"),
    ("a large dog",                90,  "nguoi"),
    ("a bowling ball",             16,  "hop"),
    ("a gallon of water",           8,  "coc"),
    ("a laptop",                    3,  "dien_thoai"),
    ("a smartphone",                0.4,  "dien_thoai"),
    ("a sheet of paper",         0.01,  "giay"),
    ("a city bus, full",        33000,  "xe_buyt"),
    ("a pickup truck",           5500,  "xe"),
    ("a horse",                  1100,  "nguoi"),
    ("a washing machine",         200,  "hop"),
    ("a bag of groceries",         12,  "hop"),
]
_KHOI_LUONG_CU = [
    ("a housecat", 10, "meo"), ("a car tire", 25, "xe"),
    ("an adult human", 180, "nguoi"), ("a grand piano", 990, "dan_piano"),
    ("a small car", 2900, "xe_buyt"), ("a school bus", 24000, "xe"),
]
NHIET_DO = [                                        # (thứ, độ F) — mạnh nhất trước
    ("the surface of the Sun", 10000, "mat_troi"), ("lava", 2000, "lua"),
    ("a pizza oven", 800, "lua"), ("boiling water", 212, "lua"),
    ("a hot summer day in Phoenix", 115, "lua"), ("a comfortable room", 70, "nha"),
    # ── NỐI THÊM 1/9. Độ F, vì kênh Mỹ (§12.13).
    ("a candle flame",                  1800,  "lua"),
    ("a car engine running",             210,  "xe"),
    ("the inside of a parked car",       140,  "xe"),
    ("a fever",                          102,  "nguoi"),
    ("a refrigerator",                    37,  "hop"),
    ("a home freezer",                     0,  "hop"),
    ("the coldest day recorded in Alaska", -80, "nha"),
    ("the surface of Mars at night",    -100,  "trai_dat"),
    ("liquid nitrogen",                 -320,  "nguyen_tu"),
    ("the Moon at night",               -280,  "mat_trang"),
    # ── ĐỢT 2 (1/9).
    ("a cup of fresh coffee",           160,  "coc"),
    ("a hot shower",                    105,  "nha"),
    ("body temperature",                 98,  "nguoi"),
    ("a warm spring day",                72,  "mat_troi"),
    ("the inside of a fridge door",      40,  "hop"),
    ("a snowy morning",                  28,  "nha"),
    ("dry ice",                         -109, "hop"),
    ("the top of Mount Everest",        -30,  "trai_dat"),
    ("a wood stove burning",            1100, "lua"),
    ("molten steel",                    2500, "lua"),
    ("a lightning bolt",               50000, "lua"),
    ("the core of the Earth",          10800, "trai_dat"),
    ("deep space",                      -455, "nguyen_tu"),
    ("a laptop under load",             120,  "dien_thoai"),
]
CUC_NHO = [                                         # (thứ, mét) — mạnh nhất trước
    ("a single atom", 1e-10, "nguyen_tu"), ("a virus", 1e-7, "vi_khuan"),
    ("a bacterium", 1e-6, "vi_khuan"), ("a red blood cell", 8e-6, "te_bao"),
    ("a human hair's width", 7e-5, "te_bao"), ("a grain of sand", 5e-4, "hop"),
    # ── NỐI THÊM 1/9. Kích thước tính bằng MÉT rồi quy ra đơn vị người Mỹ cảm được.
    ("a water molecule",        2.8e-10,"nguyen_tu"),
    ("a dust mite",             3e-4,   "vi_khuan"),
    ("a sheet of paper",        1e-4,   "giay"),
    ("a smartphone transistor", 5e-9,   "dien_thoai"),
    ("a speck of pollen",       2.5e-5, "cay"),
    ("a snowflake",             3e-3,   "nguyen_tu"),
    ("a credit card's thickness", 7.6e-4, "tien"),
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
    # ── NỐI THÊM 1/9. Thói quen nhỏ, giá thật ở Mỹ, số lần/năm.
    ("a $14 lunch every workday",         14.0, 250, "hop"),
    ("a $60 tank of gas each week",       60.0,  52, "xe"),
    ("a $30 streaming bundle",            30.0,  12, "dien_thoai"),
    ("a $9 sandwich every workday",        9.0, 250, "hop"),
    ("a $120 gym membership",            120.0,  12, "nguoi"),
    ("a $25 rideshare twice a week",      25.0, 104, "xe"),
    ("a $3 bottle of water daily",         3.0, 365, "coc"),
    ("a $50 grocery delivery fee monthly", 50.0, 12, "xe"),
    ("a $8 parking charge each workday",   8.0, 250, "xe"),
    ("a $200 cable package",             200.0,  12, "nha"),
    ("a $5 pastry every morning",          5.0, 365, "coc"),
    # ── ĐỢT 2 (1/9).
    ("a $7 smoothie three times a week",   7.0, 156, "coc"),
    ("a $45 haircut monthly",             45.0,  12, "nguoi"),
    ("a $2 lottery ticket daily",          2.0, 365, "tien"),
    ("a $19 cloud storage plan",          19.0,  12, "dien_thoai"),
    ("a $75 dinner out weekly",           75.0,  52, "hop"),
    ("a $6 car wash twice a month",        6.0,  24, "xe"),
    ("a $130 phone upgrade yearly",      130.0,   1, "dien_thoai"),
    ("a $11 movie ticket monthly",       11.0,  12, "giay"),
    ("a $40 tank of gas weekly",          40.0,  52, "xe"),
    ("a $16 delivery fee twice a week",   16.0, 104, "xe"),
    ("a $3 snack every afternoon",         3.0, 365, "hop"),
    ("a $22 music and video bundle",      22.0,  12, "dien_thoai"),
]


def _tien(v: float) -> str:
    """Số tiền viết theo lối người Mỹ đọc lướt: 1.2M, 47K, $940."""
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M".replace(".0M", "M")
    if v >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:,.0f}"


# ── CẤP PHÁT SỐ TẬP: SHORT VÀ LONG KHÔNG BAO GIỜ ĐỤNG NHAU  (1/9/2026) ──────────────────────
# Anh: *"long và short cũng ko được trùng lặp nội dung."* Trước bản này chúng trùng HOÀN TOÀN:
# `sinh_long` gọi `bo(idx + c)`, tức chương c của bản dài CHÍNH LÀ short tập c. Và vì chu kỳ nội
# dung chỉ 4–6, một bản dài 10 chương còn **tự lặp chính nó 2–3 lần trong cùng một video**.
#
# ── BẢN VÁ ĐẦU SAI, GHI LẠI ĐỂ KHÔNG LÀM LẠI ───────────────────────────────────────────────
# Tôi chia dãy CHỈ SỐ: short lấy số chẵn, long lấy số lẻ. Nghe hợp lý, đo ra 10/10 chương bản
# dài vẫn trùng short. Vì bộ sinh lấy `ds[i % n]`, mà với n lẻ thì tập các số chẵn chia dư n
# PHỦ TRỌN mọi dư — y hệt tập các số lẻ. Chia chỉ số không chia được KHÔNG GIAN.
#
# ── CÁCH ĐÚNG: chia chính không gian nội dung ──────────────────────────────────────────────
# Đo `n` = số tập phân biệt thật của kênh (đi tới khi lặp), rồi cắt đôi: short dùng nửa đầu,
# long dùng nửa sau. Hai nửa rời nhau theo định nghĩa.
# Đo bằng cách gọi bộ sinh — tất định, cho cùng kết quả ở máy và trên runner, không cần sổ ghi
# (trên Actions không trạng thái nào sống qua hai lượt chạy).
_KG = {}


def khong_gian(ma: str) -> int:
    """Số tập PHÂN BIỆT của một kênh. Đo một lần rồi nhớ."""
    if ma in _KG:
        return _KG[ma]
    k = next((x for x in KENH if x["ma"] == ma), None)
    bo = BO_SINH.get(k["sinh"]) if k else None
    if not bo:
        return 1
    # ĐO THEO TIÊU ĐỀ, không theo chữ ký đầy đủ. Chữ ký gồm cả lời kể, mà lời kể nay có biến
    # thể xoay theo `i` (xem `_loi`) — nên chữ ký phồng lên tới bội chung của hai chu kỳ, trong
    # khi CHỦ ĐỀ vẫn lặp theo chu kỳ cũ. Chia đôi một con số phồng thì hai nửa vẫn trỏ về cùng
    # tập chủ đề, và đó chính là lỗi vừa đo được: 4 kênh có 10/10 chương bản dài trùng short.
    # Với người xem, "cùng một tập" nghĩa là cùng CHỦ ĐỀ — nên đó mới là thứ phải chia.
    thay, n = set(), 0
    for i in range(600):
        t = bo(i)[0]
        if t in thay:
            break
        thay.add(t)
        n += 1
    _KG[ma] = max(1, n)
    return _KG[ma]


def vi_tri_short(ma: str, idx: int) -> int:
    """Chỉ số nội dung cho short tập `idx` — luôn nằm ở NỬA ĐẦU không gian."""
    n = khong_gian(ma)
    nua = max(1, n // 2)
    return idx % nua


def vi_tri_long(ma: str, idx: int, chuong: int) -> int:
    """Chỉ số nội dung cho chương `chuong` của bản dài — ƯU TIÊN nửa sau, tràn sang nửa đầu khi hết.

    ── VÌ SAO ĐỔI  (3/9/2026) ─────────────────────────────────────────────────────────────
    Bản cũ khoá cứng ở nửa sau (`nua + (… % con)`), để bản dài và bản ngắn không đụng chủ đề
    nhau. Ý định đúng, nhưng nó đặt một TRẦN mà không ai đo: bảng 24 mục thì bản dài chỉ dùng
    được 12, tức tối đa 12 chương.

    Đo thời lượng thật cả 18 kênh: **2,4 – 5,0 phút**, và ngay cả khi xin hết trần cũng chỉ
    3,4 – 5,0 phút cho 15/18 kênh. Mốc YouTube cho phép quảng cáo GIỮA video là **8 phút** — bộ
    comic đã làm 8–11 phút đúng vì lý do ấy (§11), bộ giải thích thì chưa ai đo.

    Nay quay vòng trên TOÀN bảng nhưng vẫn BẮT ĐẦU ở nửa sau. Với `chuong < con` kết quả y hệt
    bản cũ — nên mọi tập đã dựng vẫn ra đúng nội dung cũ. Chỉ khi cần nhiều chương hơn nửa bảng
    thì nó mới mượn sang nửa đầu.

    Đánh đổi nói rõ: chương thứ 13 trở đi CÓ THỂ trùng chủ đề với một bản ngắn của cùng kênh.
    Chấp nhận được, vì bản dài vốn là bản TỔNG HỢP nhiều câu hỏi — người xem bản dài gặp lại một
    câu hỏi đã xem ở short thì đó là ôn lại, không phải lặp. Còn video 3 phút thì mất hẳn một
    dòng doanh thu.
    """
    n = khong_gian(ma)
    nua = max(1, n // 2)
    return (nua + idx * 40 + chuong) % max(1, n)


# ══ BIẾN THỂ LỜI KỂ  (1/9/2026) ═════════════════════════════════════════════════════════════
# Anh: *"ko lặp lại nhàm chán."* Đo được: **127/130 câu (98%) GIỐNG HỆT nhau ở mọi tập** của
# cùng một kênh — chỉ con số và tên vật đổi. Người xem hai tập nghe gần như cùng một kịch bản,
# và đó là dạng lặp người ta nhận ra nhanh nhất, nhanh hơn cả lặp hình.
#
# Phần lớn những câu ấy là câu NỐI theo vai trò ("Here is the number." · "So this is the real
# gap.") chứ không phải câu mang nội dung riêng của kênh. Nên: một kho câu nối theo VAI TRÒ,
# dùng chung cho mọi kênh, xoay theo số tập. Câu mang nội dung riêng thì vẫn viết tại chỗ.
#
# Vì sao xoay theo `i` chứ không ngẫu nhiên: tất định — cùng một tập luôn ra cùng một lời, ở máy
# và trên runner như nhau. Ngẫu nhiên thì hai lần dựng cùng một tập ra hai video khác nhau, và
# mọi cổng so sánh trước/sau đều mất nghĩa.
# ── HỒ CÂU NỐI: 5 -> 8 CÂU MỖI VAI  (3/9/2026) ─────────────────────────────────────────────
# Cổng `kiem_khuon` (sau khi sửa để đếm theo VIDEO) bắt: "Set one against the other." dùng ở
# **4 kênh khác nhau** — howloud · howhot · howbig · whatweighs.
#
# Nhưng đó là SỐ HỌC, không phải lỗi cơ chế: hồ 5 câu chia cho 18 kênh thì trung bình 3,6
# kênh/câu, nên trần 3 của cổng CHẶT HƠN mức hồ cho phép. `_lech_kenh` đã lệch pha đúng — nó
# không thể tạo ra sự khác biệt mà hồ không có.
#
# Nới HỒ chứ không nới CỔNG: 8 câu -> trần lý thuyết ceil(18/8) = 3, vừa khít yêu cầu.
# Cùng bài học với `BIEN_THE` 3 -> 6 sáng nay: **cơ chế chạy đúng, hồ quá nhỏ so với số lần rút**
# — không có gì hỏng để sửa, chỉ có một con số cần lớn hơn.
LOI_MAU = {
    "mo": ["Here is the number.", "Start with the number.", "This is where it starts.",
           "Look at this first.", "One number, to begin.",
           "Begin with the figure.", "The number first.", "Here is where it opens."],
    "so": ["Here is the number.", "That is the figure.", "This is what it comes to.",
           "The number lands here.", "Here is what it actually is.",
           "That is the total.", "Here is the count.", "This is the answer."],
    # TRUNG TÍNH VỀ MIỀN. "That is the real distance" nghe hay, nhưng kênh duy nhất dùng vai
    # `gap` là `howloud` — đo DECIBEL. Soi khung ra "100,000x — THE REAL DISTANCE" trên một kênh
    # âm thanh. Câu nối dùng chung thì không được mang danh từ của một miền cụ thể (khoảng cách,
    # cân nặng, tiền); nó phải nói về QUAN HỆ giữa hai số, thứ đúng ở mọi kênh.
    "gap": ["So this is the real gap.", "That is the true difference.", "Here is the real gap.",
            "The difference is this big.", "That is what separates them.",
           "That is how far apart they are.", "Here is the distance between them.", "The gap is that wide."],
    "so_sanh": ["Put them side by side.", "Line them up.", "Now compare them.",
                "Set one against the other.", "Two things, one scale.",
           "Hold them next to each other.", "One beside the other.", "See them together."],
    "bat_ngo": ["That is not what most people guess.", "Almost nobody guesses this.",
                "Most people are far off.", "The guess is usually wrong.",
                "It rarely feels like that.",
           "Nobody sees that coming.", "That is not the number people expect.", "It catches everyone out."],
    "chot": ["Now you know.", "That is the whole answer.", "That is the number to keep.",
             "Remember that one.", "That is what it really is.",
           "That is the figure to keep.", "Hold on to that one.", "That is the takeaway."],
    # ── BA CÂU KHUNG CỦA FORMAT  (3/9/2026) ────────────────────────────────────────────
    # Ba câu này viết cứng trong `sinh_long`, nên **cả 18 kênh cùng nói y hệt** — đo được ×18
    # mỗi câu. Câu "vao" là câu THỨ HAI người xem nghe trong mọi video của mọi kênh.
    #
    # Chúng là khung chung của format, không phải nội dung riêng kênh (§13.4: cắt phần tay nghề
    # chung ra trước khi đo). Nhưng khung chung nói y hệt nhau ở 18 kênh thì đọc ra một xưởng,
    # và đó chính là trục "kịch bản" chính sách nêu tên. Cho chúng đi qua `_loi` để lệch pha
    # theo kênh — cùng cơ chế, không thêm gì mới.
    "vao": ["We are going to answer it properly.", "Let us do this properly.",
            "So let us actually work it out.", "Here is the honest version.",
            "Let us put a real number on it.", "Time to do the arithmetic.",
            "So we measured it.", "Let us settle this."],
    "tong": ["Here they all are, side by side.", "All of them on one scale.",
             "Every one of them, together.", "The whole set at once.",
             "Now all of them together.", "Here is the full picture.",
             "All of it on one chart.", "Everything, lined up."],
    "ket": ["That is the whole picture.", "That is all of it.",
            "Now you have seen the whole thing.", "That is the full answer.",
            "And that is the shape of it.", "That is everything.",
            "So now you know the whole of it.", "That is where it lands."],
    "than": ["Your brain does not work in these numbers.",
             "We are bad at numbers this size.",
             "Nothing in daily life prepares you for this.",
             "The scale does not fit in your head.",
             "This is where intuition gives up.",
           "Your head has no scale for this.", "Numbers this size stop meaning anything.", "Intuition has nothing to offer here."],
}


# Kênh đang được dựng — `_loi` đọc để lệch pha câu nối. Đặt ở `kich_ban` và `sinh_long`, hai
# chỗ duy nhất gọi bộ sinh. Xem chú thích trong `_loi`.
_MA_HIEN = ""


def _lech_kenh(ma: str) -> int:
    """Băm mã kênh ra một số nguyên ỔN ĐỊNH.

    KHÔNG dùng `hash()` của Python: nó đổi theo từng lần chạy vì `PYTHONHASHSEED` ngẫu nhiên,
    nên máy anh và runner sẽ cho hai lịch khác nhau — cùng một tập dựng lại ra lời khác. Đã trả
    giá cho đúng chuyện này ở bộ Kling (§13.13).
    """
    n = 0
    for c in str(ma or ""):
        n = (n * 31 + ord(c)) % 100003
    return n


def _loi(vai: str, i: int, rieng: str = "") -> str:
    """Câu nối theo VAI TRÒ, xoay theo số tập VÀ theo kênh.

    ── VÌ SAO PHẢI LỆCH THEO KÊNH  (3/9/2026) ─────────────────────────────────────────────
    Cổng `kiem_khuon` đo trên 21 video của nhiều kênh: câu "Put them side by side." xuất hiện
    **7 lần**, "We are going to answer it properly." 5 lần. Không phải một kênh lặp — mà là BẢY
    KÊNH KHÁC NHAU cùng đọc một câu, vì `ds[i % len(ds)]` chỉ nhìn chỉ số chương. Hai kênh dựng
    chương thứ 3 thì cùng lấy câu thứ 3.

    Đây đúng trục *"kịch bản"* mà chính sách YouTube nêu tên (§13.17): các kênh dùng chung một
    bộ câu nối thì đọc ra một xưởng. Và nó là thứ đo được, không phải cảm giác.

    Lệch pha bằng băm mã kênh: cùng một hồ 5 câu nhưng mỗi kênh bắt đầu ở một chỗ khác, nên
    xác suất hai kênh trùng câu ở cùng chỉ số giảm năm lần. Tất định nên dựng lại vẫn ra đúng
    lời cũ.
    """
    if rieng:
        return rieng
    ds = LOI_MAU.get(vai)
    if not ds:
        return ""
    return ds[(i + _lech_kenh(_MA_HIEN)) % len(ds)]


def _khu(ds: list) -> list:
    """Bỏ mục TRÙNG TÊN, giữ mục xuất hiện trước.

    Một mục trùng không gây lỗi nào — nó chỉ lặng lẽ **thu hẹp không gian nội dung**: bảng 16
    mục có 2 mục trùng thì kênh lặp lại sau 14 tập chứ không phải 16, và không ai biết. Đo được
    hôm nay: sau khi nối thêm dữ liệu, 26 mục trùng lọt vào 8 bảng, và `speedof` lặp ở tập 5
    thay vì tập 16.

    Khử ở đây là lưới AN TOÀN, không phải chỗ sửa: cổng `kiem_trung.py` vẫn báo để dữ liệu được
    dọn cho sạch. Giấu lỗi soạn dữ liệu là cách để nó quay lại.
    """
    ra, thay = [], set()
    for x in ds:
        k = x[0] if isinstance(x, (list, tuple)) and x else x
        if k in thay:
            continue
        thay.add(k)
        ra.append(x)
    return ra


def _hoa(t: str) -> str:
    """Viết hoa ĐÚNG CHỮ CÁI ĐẦU, giữ nguyên phần sau.

    Bốn kênh so sánh dùng `lon[0].title()` cho vế đầu và để nguyên vế sau, nên tiêu đề ra
    không đối xứng: *"A School Bus vs a giraffe"* · *"A Red Blood Cell vs a bacterium"*.
    Hai vế cùng vai mà một vế Title Case, một vế chữ thường — người xem đọc ra ngay là chữ
    do máy ghép, và 14 kênh còn lại đều đang dùng câu thường (*"The real cost of a $6
    coffee"* · *"How loud is a jet at takeoff"*).

    Không dùng `.capitalize()`: nó HẠ chữ hoa ở phần sau, nên *"New York to London"* thành
    *"New york to london"*. Không dùng `.title()`: nó nâng mọi từ, kể cả mạo từ.
    """
    return (t[:1].upper() + t[1:]) if t else t


def _lay(ds: list, i: int):
    """Mục thứ `i` của bảng, sau khi đã khử trùng. Chu kỳ = số mục PHÂN BIỆT."""
    d = _khu(ds)
    return d[i % len(d)]


def _cap(ds: list, i: int) -> tuple:
    """Cặp (a, b) KHÁC NHAU, đi hết n·(n−1) tổ hợp rồi mới lặp.

    ── VÌ SAO (1/9/2026) ───────────────────────────────────────────────────────────────────
    Ba bộ sinh so sánh hai vật lấy cặp bằng `ds[i % n]` và `ds[(i+3) % n]`. Bước nhảy CỐ ĐỊNH
    nghĩa là cặp thứ i luôn là (i, i+3), nên chu kỳ chỉ bằng **n** — với `KHOI_LUONG` n=6 thì
    tập 6 giống hệt tập 0, dù sáu vật ấy tạo được 30 cặp khác nhau. Đo được: 18/18 kênh lặp
    nội dung trong vòng 3–10 tập, `howmuch` lặp ngay ở tập 1.

    Ở đây bước nhảy TĂNG DẦN theo vòng: đi hết một vòng bước 1, rồi vòng bước 2, ... Cách này
    phủ trọn n·(n−1) cặp có thứ tự mà không cần nhớ gì giữa các lần gọi — quan trọng, vì trên
    Actions không có trạng thái nào sống qua hai lượt chạy.
    """
    ds = _khu(ds)
    n = len(ds)
    if n < 2:
        return ds[0], ds[0]
    vong = (i // n) % (n - 1) + 1          # bước nhảy 1..n-1, không bao giờ 0 (a != b)
    a = i % n
    return ds[a], ds[(a + vong) % n]


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
# ── GÓC MÀU TRẢI ĐỀU VÒNG TRÒN  (4/9/2026) ────────────────────────────────────────────────
# Đo bảng cũ: **8/18 kênh chen trong dải 3°–31°** (cam/đỏ) trong khi cả cung 267°–360° bỏ
# trống, và năm cặp cách nhau **≤2°** — tức mắt đọc ra cùng một màu. Khoảng cách trung bình
# lại đúng 20°, bằng mức lý tưởng: con số trung bình che mất HÌNH DẠNG của phân bố.
#
# Nay 18 góc cách nhau ≥17°, gán theo NGHĨA kênh: nhiệt/báo động ở cung đỏ, tiền ở cung lục,
# tốc độ/quy mô ở cung lam, may rủi/giả định ở cung tím.
#
# ── HAI PHÉP CHỈNH KHÔNG BỎ ĐƯỢC ─────────────────────────────────────────────────────────
# 1. GIỮ ĐỘ CHÓI, KHÔNG GIỮ S/V. Bản đầu em xoay góc màu mà giữ nguyên bão hoà và độ sáng —
#    độ chói lệch từ 3,4 lần lên **4,7 lần**, `yearsof` vàng-lục chói 0,309 so với trung vị
#    0,128. Trên nền kem nó nhợt đi và chữ trắng đè lên hụt tương phản. Cùng S,V ở hai góc
#    màu khác nhau KHÔNG cho cùng độ sáng cảm nhận. Nay dò nhị phân trên V để khớp đúng độ
#    chói cũ của từng kênh.
# 2. TRẦN BÃO HOÀ RIÊNG CUNG HỒNG/TÍM. Cùng một S đọc rất khác nhau: 0,78 ở cam là đất nung
#    ấm, ở magenta là đèn neon — `howlong` ra `#F8317A` chói mắt. Cung 265–350 hạ trần 0,58.
#
# Kết quả đo: chói 0,070–0,235 (3,4×, bằng bảng cũ) · tương phản chữ trắng thấp nhất 3,68:1
# (đạt AA cho chữ lớn, và `chuHopNen` vẫn tự đổi màu chữ theo nền).
MAU_KENH = {
    "howlong":  {"nen": "#F4EDE0", "mau": "#D75A88", "phu": "#2F6E8A", "chu": "#2E2A24"},
    "howbig":   {"nen": "#EEF1F3", "mau": "#216E83", "phu": "#C9552F", "chu": "#22282B"},
    "realcost": {"nen": "#F2F0EA", "mau": "#1E6C45", "phu": "#8A5A2E", "chu": "#232622"},
    "howmuch":  {"nen": "#EEF0F4", "mau": "#573C85", "phu": "#C98A2E", "chu": "#232336"},
    "whatif":   {"nen": "#F5F0E6", "mau": "#B04A8E", "phu": "#2F7D8A", "chu": "#2B2622"},
    "survive":  {"nen": "#E8E9E6", "mau": "#6B5124", "phu": "#4E6B54", "chu": "#232522"},
    "dayinlife":{"nen": "#F0E7D6", "mau": "#6E6C2A", "phu": "#3E6E8C", "chu": "#2A241B"},
    "wheregoes":{"nen": "#EDF0F2", "mau": "#405FD8", "phu": "#C9762F", "chu": "#212629"},
    "therules": {"nen": "#EFF1EA", "mau": "#BC4FBC", "phu": "#4E7C4A", "chu": "#252722"},
    "speedof":  {"nen": "#EAF0F5", "mau": "#245E99", "phu": "#D9622B", "chu": "#1F272E"},
    # ── 8 kênh bổ sung. Màu chọn để KHÔNG trùng cặp nào ở trên: mỗi kênh phải nhận ra được
    # khi đứng cạnh mười bảy kênh kia trong danh sách đề xuất của YouTube.
    "odds":      {"nen": "#F1EDF5", "mau": "#753D92", "phu": "#C9A227", "chu": "#241F2E"},
    "hiddenfee": {"nen": "#F0F2EE", "mau": "#2C6F2F", "phu": "#B4522E", "chu": "#1F2620"},
    "yearsof":   {"nen": "#F5F1E8", "mau": "#59721E", "phu": "#3E6E7C", "chu": "#2A2520"},
    "howloud":   {"nen": "#EDEEF2", "mau": "#C52F3B", "phu": "#2F5D8A", "chu": "#20242B"},
    "whatweighs": {"nen": "#EFF0EC", "mau": "#3F5E2C", "phu": "#B4603A", "chu": "#22261E"},
    "rightnow":  {"nen": "#ECF1F4", "mau": "#1C7D75", "phu": "#D97E36", "chu": "#1E272B"},
    "howhot":    {"nen": "#F6EFE6", "mau": "#BC5326", "phu": "#3B5E7A", "chu": "#2B231C"},
    "smallest":  {"nen": "#EDEFF4", "mau": "#4C43B2", "phu": "#8FA33E", "chu": "#1F2330"},
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
    "realcost":   ("en-US-RogerNeural",               "music/mind_pad32.mp3",            "thin precise outlines, restrained three-color palette, editorial"),
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
    # ── GẮN VẬT VẼ BẰNG CODE  (3/9/2026) ───────────────────────────────────────────────────
    # `_bt_canh` viết xong từ hôm qua và **chưa bao giờ được gọi** — nên trường `bt` không hề
    # tồn tại trong nhịp `canh`, và engine rơi vào nhánh "không có gì để vẽ". Soi lưới bản dài
    # SURVIVE: 3/6 khung chỉ có tường, sàn và một dòng phụ đề.
    #
    # Đây đúng luật 13.1 ở dạng nặng nhất: cơ chế đã có sẵn, thiếu đúng một thứ GỌI nó. Suốt
    # hai vòng sửa tôi đi chỉnh độ mờ và bóng đổ của một hình chưa từng được vẽ.
    #
    # Gắn ở `_n` vì đây là chỗ hẹp duy nhất mọi nhịp cảnh đi qua — hơn sáu mươi chỗ gọi ở mười
    # tám bộ sinh đều dùng nó. Chỗ gọi nói rõ `bt` thì tôn trọng, y như `noi`.
    # `kinh_lup` cũng cần: khi cạn hồ ảnh CF thì ống kính không có gì để phóng và engine vẽ ra
    # một ĐĨA TRẮNG to bằng một phần ba khung (soi khung THE RULES bản dọc). Biểu tượng làm
    # tầng dự phòng — kính lúp phóng to một vật vẫn đúng nghĩa "nhìn kỹ vào chi tiết".
    if khuon in ("canh", "kinh_lup") and not d.get("bt"):
        d["bt"] = _bt_canh(loi, d.get("ve", ""))
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
    ten, km, bt, kieu, troi = _lay(QUANG_DUONG, i)
    # `gt_de` cho tiêu đề và chữ hook, `gt_kc` cho câu đọc — xem `GIOI_TU`, hai cột khác nhau.
    gt_de, gt_kc = GIOI_TU.get(kieu, ("to ", "to "))
    gio_b = km / DI_BO_MPH
    sb, ub = _lau(gio_b)
    sc, uc = _lau(km / XE_MPH)
    sm, um = _lau(km / MAY_BAY_MPH)
    sa, ua = _lau(km / AS_MPS / 3600)
    ngay = max(1, min(20, int(gio_b / 24)))
    return (f"Walking {gt_de}{ten}",
            f"HOW LONG TO WALK {gt_de.upper()}{ten.upper()}?", f"{sb} {ub.upper()}",
            [
    _n("chia_doi", "You walk. Light does not.",
       trai={"nhan": "you", "bt": "nguoi", "so": "3 mph"},
       phai={"nhan": "light", "bt": "trai_dat", "so": "670 mn mph"}, dinh=True),
    _n("so_lieu", f"The distance {gt_kc}{ten}.", so=f"{km:,.0f}", don="miles", bt=bt, dinh=True,
       ve=_ve(f"a tiny lone human figure standing alone on a vast empty plain, simple worn clothing",
              "head tilted back, gazing up at the sky", "small and awed against the emptiness",
              # CHỈ TẢ VẬT TRÊN TRỜI KHI CÓ VẬT TRÊN TRỜI. Bản trước nhét thẳng `ten` vào,
              # nên FLUX nhận "New York to Los Angeles hanging huge and pale in a deep open
              # sky" — không sai ngữ pháp, chỉ vô nghĩa, và mô hình vẽ theo đúng thứ vô nghĩa
              # ấy. §15.2: mọi danh từ viết ra đều có thể hiện trong khung.
              (f"{troi} hanging huge and pale in a deep open sky, low flat horizon line"
               if troi else "a long empty road running straight to a far flat horizon"),
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
    # `canh`, KHÔNG `so_lieu`.  (3/9/2026)
    # Nhịp này và nhịp "On foot." ngay sau đó cùng hiện **8.8** — hai khối số liền nhau nói
    # đúng một con số, và người xem thấy màn hình đứng yên qua hai nhịp. Con số đã được nói ở
    # nhịp trước rồi; chỗ này là CÚ ĐẾN NƠI, tức một khoảnh khắc, không phải một số liệu.
    # Đổi sang cảnh thì vừa hết trùng số vừa đúng nghĩa — và prompt ảnh vốn đã viết cho một
    # cảnh ("arms raised in triumph"), nên chính khuôn cũ mới là chỗ sai.
    _n("canh", "You arrive.", dinh=True, tam_trang="ngay",
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
    _n("canh", _loi("chot", i, "So no. Do not walk." if i % 3 == 0 else ""), dinh=True, tam_trang="ngay",
       ve=_ve("a lone figure standing beside a parked car, one hand on the roof",
              "having just given up on walking, looking at the horizon",
              "wry, self-aware, half-smiling",
              "the same endless plain, the destination tiny and far away in the sky",
              "the car door open, footprints ending right at the wheel",
              "warm late light from the left, long shadow")),
            ])


def sinh_howbig(i):
    a, b = _cap(CO_LON, i)
    lon, nho = (a, b) if a[1] >= b[1] else (b, a)
    lan = lon[1] / nho[1]
    xep = int(round(lan))
    return (f"{_hoa(lon[0])} vs {nho[0]}",
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
    _n("chart", _loi("so_sanh", i), don="feet",
       cot=[{"nhan": _nhan(nho[0]), "v": nho[1]},
            {"nhan": _nhan(lon[0]), "v": lon[1]}], dinh=True),
    _n("canh", "Your brain was wrong.", dinh=True,
       ve=_ve("a simplified human silhouette standing very small",
              "looking up at an enormous object towering over the whole frame",
              "stunned, tiny by comparison",
              "a plain pale backdrop, the object filling most of the height",
              "the silhouette at the very bottom for scale",
              "even soft light, restrained muted palette")),
            ])


def sinh_realcost(i):
    ten, gia, lan, bt = _lay(THOI_QUEN, i)
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


# ── MỐC SỐ LỚN CHO `howmuch` (1/9) ──────────────────────────────────────────────────────────
# Bộ sinh cũ BỎ QUA HẲN `i`: mọi tập ra đúng một video "A million versus a billion". Đo được
# n = 1, tức kênh này chưa bao giờ có tập thứ hai. Đây là dạng nặng nhất của lỗi lặp — không
# phải lặp sau vài tập, mà lặp ngay từ tập một, và không có lỗi nào báo.
#   (tên nhỏ, số nhỏ, tên lớn, số lớn, đơn vị đếm, hình)
MOC_LON = [
    ("a million",        1e6,  "a billion",     1e9,  "seconds",     "tien"),
    ("a billion",        1e9,  "a trillion",    1e12, "seconds",     "tien"),
    ("a thousand",       1e3,  "a million",     1e6,  "seconds",     "tien"),
    ("a million dollars", 1e6, "a billion dollars", 1e9, "dollars",  "tien"),
    ("a million steps",  1e6,  "a billion steps", 1e9, "steps",      "nguoi"),
    ("a thousand days",  1e3,  "a million days", 1e6, "days",        "dong_ho"),
    ("a million grains", 1e6,  "a billion grains", 1e9, "grains",    "hop"),
    ("a million people", 1e6,  "a billion people", 1e9, "people",    "nguoi"),
    ("a million miles",  1e6,  "a billion miles", 1e9, "miles",      "may_bay"),
    ("a million words",  1e6,  "a billion words", 1e9, "words",      "giay"),
    ("a thousand hours", 1e3,  "a million hours", 1e6, "hours",      "dong_ho"),
    ("a million drops",  1e6,  "a trillion drops", 1e12, "drops",    "coc"),
    ("a million cells",  1e6,  "a trillion cells", 1e12, "cells",    "te_bao"),
    ("a billion stars",  1e9,  "a trillion stars", 1e12, "stars",    "mat_troi"),
    ("a thousand dollars", 1e3, "a billion dollars", 1e9, "dollars", "tien"),
    ("a million minutes", 1e6, "a billion minutes", 1e9, "minutes",  "dong_ho"),
    ("a million pages",  1e6,  "a billion pages", 1e9, "pages",      "giay"),
    ("a million heartbeats", 1e6, "a billion heartbeats", 1e9, "heartbeats", "nguoi"),
    ("a million atoms",  1e6,  "a trillion atoms", 1e12, "atoms",    "nguyen_tu"),
    ("a thousand miles", 1e3,  "a million miles", 1e6, "miles",      "xe"),
    ("a million bytes",  1e6,  "a trillion bytes", 1e12, "bytes",    "dien_thoai"),
    ("a million breaths", 1e6, "a billion breaths", 1e9, "breaths",  "nguoi"),
    ("a million raindrops", 1e6, "a billion raindrops", 1e9, "raindrops", "coc"),
    ("a thousand seconds", 1e3, "a billion seconds", 1e9, "seconds", "dong_ho"),
]


def sinh_howmuch(i):
    nho, vn, lon, vl, don, bt = _lay(MOC_LON, i)
    s1, u1 = _lau(vn / 3600)
    s2, u2 = _lau(vl / 3600)
    return (f"{_hoa(nho)} versus {lon}",
            f"{lon.upper()} IS NOT A BIG {nho.upper().replace('A ', '')}", f"{s2} {u2.upper()}",
            [
    _n("chia_doi", "Two words. One letter apart.",
       trai={"nhan": "million", "bt": "tien", "so": "1,000,000"},
       phai={"nhan": "billion", "bt": "tien", "so": "1,000,000,000"}, dinh=True),
    _n("canh", _loi("than", i),
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
          ("everyone planted one tree", "cay", "a huge open field newly filled with young saplings"),
          # ── NỐI THÊM 1/9: bốn mục -> lặp từ tập 4.
          ("everyone turned on a light at once", "nha", "a whole city block lit at the same instant seen from a hill"),
          ("everyone shouted at once", "nguoi", "a dense crowd in a public square all with mouths open"),
          ("nobody threw anything away for a week", "hop", "a street corner stacked high with neat sealed boxes"),
          ("everyone worked from home", "dien_thoai", "an empty office tower at midday, every desk bare"),
          ("everyone drank only tap water", "coc", "a long row of glasses filling from a single tap"),
          ("everyone walked to work", "nguoi", "a wide road filled with people walking, no vehicles"),
          ("everyone kept their phone for ten years", "dien_thoai", "an orderly shelf of well-used identical phones"),
          ("everyone slept eight hours", "giuong", "a quiet neighbourhood at night, every window dark"),
          ("everyone grew one vegetable", "cay", "rows of small pots on balconies across a whole street"),
          ("everyone stopped flying for a year", "may_bay", "a large airport apron with parked aircraft and no movement"),
          ("everyone read one book a month", "giay", "a park bench row where every person holds an open book"),
          ("everyone got a dog", "meo", "a wide sidewalk with a person and a dog every few steps"),
          # ── ĐỢT 2 (1/9).
          ("everyone stopped eating meat for a month", "hop", "a supermarket aisle of produce with empty meat cases"),
          ("everyone took the bus for a week", "xe_buyt", "a long line of full buses on an otherwise empty road"),
          ("nobody used plastic for a day", "hop", "a market stall with only paper and cloth wrapping"),
          ("everyone paid in cash", "tien", "a long shop queue with open wallets and notes"),
          ("everyone turned the heat down two degrees", "nha", "a street of houses with people in thick jumpers indoors"),
          ("everyone recycled everything correctly", "hop", "a sorting yard with perfectly separated clean bales"),
          ("nobody drove alone", "xe", "a highway of cars each visibly full of people"),
          ("everyone learned one language", "giay", "a park where every bench holds a person with a phrasebook"),
          ("everyone donated one dollar", "tien", "an enormous heap of single notes in an open hall"),
          ("everyone planted a garden", "cay", "back yards along a street all turned into vegetable beds"),
          ("everyone slept in complete darkness", "giuong", "an aerial view of a neighbourhood with no lit windows"),
          ("everyone wrote one letter", "giay", "a post office counter with towering trays of envelopes")]
    ten, bt, canh = _lay(ds, i)
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
          ("a winter without a shop", "a snowbound valley with no buildings in sight"),
          # ── NỐI THÊM 1/9.
          ("a week in the open ocean", "an endless flat sea under a pale empty sky"),
          ("a night on a mountain top", "a bare rocky summit above the clouds at dusk"),
          ("three days without water", "a cracked dry lakebed stretching to the horizon"),
          ("a winter in a cabin with no power", "a snowed-in wooden cabin, no lights, deep drifts"),
          ("a day in a rainforest alone", "dense green rainforest, thick undergrowth, no path"),
          ("a week on a deserted island", "a small sandy island with a few palms and open sea"),
          ("a night in a swamp", "a dark still swamp with dead trees and low mist"),
          ("a day on the salt flats", "a blinding white salt plain under a hard noon sun"),
          ("a month with no supermarket", "an empty small-town street with shuttered shopfronts"),
          ("a night in a cave", "a wide dark cave mouth with faint light from outside"),
          ("a day in a sandstorm", "a desert road vanishing into a wall of blowing sand"),
          # ── ĐỢT 2 (1/9).
          ("a week in the Arctic", "a flat expanse of pack ice under a low pale sun"),
          ("a day on an active volcano", "a black ash slope with steam venting from cracks"),
          ("a night in the Everglades", "still dark water between mangrove roots at night"),
          ("a week without electricity in winter", "a dark suburban street under deep snow"),
          ("three days in Death Valley", "a shimmering salt basin under a hard white sky"),
          ("a night in a blizzard", "a wall of driving snow with a fence barely visible"),
          ("a day adrift in a life raft", "a small orange raft alone on a wide calm ocean"),
          ("a week in a desert canyon", "sheer red canyon walls with a dry streambed below"),
          ("a night on a frozen lake", "a vast flat sheet of ice under a clear starry sky"),
          ("a day in a dust bowl storm", "a farmhouse half-buried under drifting brown dust"),
          ("a week above the treeline", "bare grey rock and lichen under a hard blue sky")]
    ten, canh = _lay(ds, i)
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
           "one warm lantern light against deep blue darkness, hard pool of light on the stones"),
          # ── NỐI THÊM 1/9.
          ("a lighthouse keeper",
           "a stone lighthouse on a rocky headland at dawn, grey sea stretching out behind",
           "a heavy wool coat and a brass oil can",
           "cold blue dawn light from the low right, long thin shadows"),
          ("a night-shift nurse",
           "a quiet hospital corridor at 3am, closed doors receding into the distance",
           "pale scrubs and a clipboard",
           "flat green-white ceiling light, almost no shadow"),
          ("a long-haul trucker",
           "a wide empty interstate at night, headlights on a straight road to the horizon",
           "a padded jacket and a paper log book",
           "hard white headlight glow from ahead, deep black beyond"),
          ("a wheat farmer at harvest",
           "a vast ripe wheat field under a huge open sky, a combine far off",
           "worn denim and heavy gloves",
           "warm gold late-afternoon light from the left"),
          ("a subway train operator",
           "a lit underground platform seen from the front of a train, tiled walls curving away",
           "a uniform jacket and a worn key ring",
           "hard fluorescent light, sharp reflections on tile"),
          ("a firefighter on shift",
           "an open fire station bay at dusk, a red engine and polished concrete floor",
           "heavy turnout gear and a helmet under one arm",
           "warm orange bay light against blue evening outside"),
          ("a fishing-boat deckhand",
           "an open deck of a small boat on a grey choppy sea, nets piled at the stern",
           "oilskins and heavy rubber boots",
           "flat overcast light with no shadows"),
          ("a hotel night porter",
           "an empty hotel lobby after midnight, polished floor and a single lit desk",
           "a plain uniform waistcoat and a brass luggage trolley",
           "warm pooled lamplight, dark corners"),
          ("a warehouse picker",
           "an enormous warehouse aisle of identical shelving running out of sight",
           "a hi-vis vest and a hand scanner",
           "even overhead light, faint shadows straight down"),
          ("an air traffic controller",
           "a glass tower cabin above a runway at dusk, wide view over the airfield",
           "a headset and a plain shirt",
           "dim interior with cool screen glow from below"),
          # ── ĐỢT 2 (1/9).
          ("a Victorian factory child",
           "a long dim spinning-mill floor, rows of machines vanishing into haze",
           "a plain smock and bare feet",
           "weak grey daylight from high windows on the left"),
          ("an Apollo mission controller",
           "a 1960s control room of identical consoles, a large screen at the far end",
           "a short-sleeved shirt, tie and headset",
           "even fluorescent light, faint green glow from screens"),
          ("a medieval scribe",
           "a stone monastery scriptorium, high narrow windows, sloped writing desks",
           "a heavy robe, a quill and an inkpot",
           "cool light from a tall window on the right, deep shadow behind"),
          ("a 1920s switchboard operator",
           "a wall of cable jacks running the length of a narrow room",
           "a plain blouse and a headset",
           "flat warm bulb light overhead"),
          ("a Gold Rush prospector",
           "a shallow river in a wide valley, tents on the far bank",
           "muddy boots, a wide pan and a shovel",
           "hard midday sun straight down, short black shadows"),
          ("a lighthouse builder",
           "a half-built stone tower on a wave-lashed rock, open sea beyond",
           "rope, a chisel and a heavy leather harness",
           "flat stormy light, no direct sun"),
          ("an Antarctic researcher",
           "a small red hut on an endless white plain under a low sun",
           "a heavy parka and goggles",
           "low blinding sun from the horizon, very long blue shadows"),
          ("a 1950s telephone linesman",
           "a straight country road with wooden poles running to the horizon",
           "a tool belt and climbing spikes",
           "clear afternoon light from the left"),
          ("a submarine sonar operator",
           "a cramped steel compartment of dials and pipes, no windows",
           "a plain uniform and heavy headphones",
           "dim red light, hard shadows"),
          ("a rail yard signalman",
           "a raised signal box over a fan of converging tracks at dusk",
           "a waistcoat and a row of long levers",
           "warm lamp light inside against blue dusk outside")]
    ten, canh, do, sang = _lay(ds, i)
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
               "standing at a suburban curb waiting for collection", "",
               "a quiet residential street, simplified houses receding, parked car far off",
               "the bin large and sharp, curb stones and a few leaves close to camera",
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
               "flat indoor light, slightly desaturated palette")),
          # ── NỐI THÊM 1/9.
          ("your recycling", "hop", "a sorting facility with conveyor belts of mixed material"),
          ("your old phone", "dien_thoai", "a warehouse of stacked electronics awaiting processing"),
          ("your tap water", "coc", "a treatment plant with large open circular tanks"),
          ("your online return", "hop", "a huge warehouse aisle of returned parcels"),
          ("your used cooking oil", "coc", "a collection yard with sealed drums lined up"),
          ("your old car", "xe", "a scrapyard with crushed vehicles stacked in rows"),
          ("your junk mail", "giay", "a mail sorting hall with bins of unopened envelopes"),
          ("your worn-out clothes", "hop", "a bale yard of compressed textile bundles"),
          ("your food scraps", "hop", "an open composting site with long dark windrows"),
          ("your dead batteries", "hop", "a hazardous-waste bay with labelled containers"),
          ("your package before it arrives", "hop", "a night distribution hub with parcels on belts"),
          # ── ĐỢT 2 (1/9).
          ("your old mattress", "hop", "a yard of stacked mattresses awaiting shredding"),
          ("your bank transfer", "tien", "a server hall of identical racks with cable trays"),
          ("your rubbish on collection day", "xe", "a transfer station with a tipping floor of mixed waste"),
          ("your holiday photos", "dien_thoai", "a data centre aisle with rows of blinking drives"),
          ("your old tires", "xe", "a stacked yard of worn tires in long rows"),
          ("your prescription bottle", "hop", "a pharmacy return bin with sorted containers"),
          ("your paper receipt", "giay", "a shredding facility with bales of paper strips"),
          ("your leftover paint", "hop", "a hazardous collection depot with labelled tins"),
          ("your old textbooks", "giay", "a warehouse of palletised books under plastic wrap"),
          ("your worn-out running shoes", "nguoi", "a grinding line turning shoes into rubber crumb"),
          ("your washing machine water", "coc", "an underground pipe junction with flowing channels"),
          ("your unwanted gift", "hop", "a liquidation warehouse of mixed unopened boxes")]
    ten, bt, canh = _lay(ds, i)
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
              "moving slowly along the curb, arm extended toward a bin", "",
              "a quiet suburban street, simplified houses and trees receding",
              "the curb and bins passing close to camera",
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
           _ve("a clean empty concrete driveway", "running from the curb up to a closed garage", "",
               "a plain two-storey American suburban house, neighbouring roofs beyond",
               "the driveway surface filling the lower third, a curb edge close to camera",
               "warm mid-morning light from the left, bright friendly muted palette")),
          ("your own mailbox",
           _ve("a plain curbside mailbox on a wooden post", "standing closed at the edge of the lawn", "",
               "a quiet suburban home set back behind a neat lawn, trees beyond",
               "the mailbox large and sharp, grass and curb close to camera",
               "warm morning light from the right, bright muted palette")),
          ("your own front lawn",
           _ve("a neat mown green front lawn", "stretching flat from curb to porch", "",
               "a simple suburban house front, low hedge, sky above",
               "cut grass texture filling the lower third",
               "bright midday light, saturated fresh green, friendly palette")),
          ("your own fence",
           _ve("a plain wooden boundary fence", "running straight between two yards", "",
               "two simplified suburban houses on either side, sky above",
               "fence boards large and sharp at the left, grass at the base",
               "warm afternoon light from the right, muted palette")),
          # ── NỐI THÊM 1/9.
          ("the gym membership you cannot cancel", "a gym reception desk with a long printed contract"),
          ("the airline ticket small print", "an airport gate desk with a dense printed page"),
          ("the software you agreed to", "a laptop screen showing an endless scrolling agreement"),
          ("the rental car extras", "a car rental counter with a stack of forms"),
          ("the phone contract clause", "a phone shop counter with a folded multi-page document"),
          ("the concert ticket resale rule", "a venue entrance with a printed notice board"),
          ("the free trial that renews", "a kitchen table with an unopened bank statement"),
          ("the warranty that expires early", "a repair shop counter with a small printed card"),
          ("the parking sign nobody reads", "a city curb with a dense stack of parking signs"),
          ("the hotel resort fee", "a hotel front desk with an itemised printed bill"),
          # ── ĐỢT 2 (1/9).
          ("the deposit you will not get back", "an empty rental flat with a clipboard on the counter"),
          ("the overdraft fee schedule", "a bank counter with a dense printed fee sheet"),
          ("the ticket you cannot refund", "a train station window with a printed notice"),
          ("the insurance exclusion list", "a desk with an open policy booklet under a lamp"),
          ("the subscription that auto-renews", "a laptop on a kitchen table showing a renewal notice"),
          ("the delivery guarantee that is not one", "a doorstep with a printed card left behind"),
          ("the return window nobody notices", "a shop counter with a receipt and a wall sign"),
          ("the roaming charge nobody mentions", "an airport lounge with a phone showing a bill alert"),
          ("the fine print on the coupon", "a supermarket checkout with a long printed voucher"),
          ("the clause about arbitration", "an office table with a thick contract and a pen"),
          ("the fee for paying by card", "a small shop counter with a handwritten notice")]
    ten, canh = _lay(ds, i)
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
               "bright hard sunlight from above left, clean cool palette")),
          # ── NỐI THÊM 1/9.
          ("a sneeze", 160, "a close view of a person mid-sneeze, motion lines"),
          ("a commercial jet", 900, "a passenger jet cruising above a flat cloud layer"),
          ("a cheetah at full sprint", 112, "a cheetah stretched flat in mid-stride on open ground"),
          ("a falling raindrop", 32, "a single large raindrop against a grey sky"),
          ("a major-league fastball", 160, "a baseball leaving a pitcher's hand, motion blur behind"),
          ("a passenger train", 130, "a long train crossing an open plain"),
          ("the space station orbiting", 27600, "a station silhouette against the curve of Earth"),
          ("a housefly", 7, "a housefly hovering close to a plain surface"),
          ("a person walking", 5, "a person walking along an empty pavement"),
          ("a rifle bullet", 3500, "a stylised bullet crossing an empty frame at speed"),
          ("sound at sea level", 1235, "an expanding ring of pressure lines over flat ground"),
          ("the Earth around the Sun", 107000, "the Earth as a small disc on a wide curved path"),
          # ── ĐỢT 2 (1/9): cần n ≥ 24.
          ("a sprinting human", 37, "a runner at full stride on an empty track"),
          ("a city bus", 50, "a bus moving along an empty avenue"),
          ("a hurricane gust", 250, "bent palm trees under a dark sky"),
          ("a bullet train", 320, "a sleek train blurred against a flat landscape"),
          ("a diving falcon", 390, "a falcon folded into a steep dive against open sky"),
          ("a tennis serve", 260, "a tennis ball leaving a racket, motion streak behind"),
          ("light through glass", 200000000, "a thin bright beam crossing a dark frame"),
          ("a helicopter", 260, "a helicopter low over open ground"),
          ("an elevator", 22, "an elevator shaft seen from below with cables"),
          ("a garden snail", 0.05, "a snail on a wide plain surface"),
          ("the Moon around the Earth", 3680, "a small moon on a wide curved path"),
          ("a paper plane", 25, "a paper plane gliding across an empty room")]
    ten, kmh, canh = _lay(ds, i)
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
    _n("chart", _loi("so_sanh", i), don="mph",
       cot=[{"nhan": "walk", "v": 3}, {"nhan": _nhan(_danh_tu(ten)), "v": kmh},
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
    ten, N, bt = _lay(XAC_SUAT, i)
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
    # `don` là NHÃN HIỆN RA, không phải chỗ ghi công thức. "1 in N" lên màn hình nguyên văn
    # là "1 IN N" — soi khung ODDS thấy ngay ở đầu biểu đồ. Chuỗi mẫu lọt ra sản phẩm.
    _n("chart", "Next to things you fear.", don="1 in this many",
       # Mốc so sánh phải khác chính mục của chương — khi bộ lịch phát trúng chương "lightning"
       # thì hai cột bằng nhau và trục phẳng lì. Cùng gốc với `_moc_khac` ở `chia_doi`.
       cot=[_moc_khac([{"nhan": "lightning", "v": 1222000, "so": 1222000},
                       {"nhan": "a shark bite", "v": 3748067, "so": 3748067}], N),
            {"nhan": _nhan(ten.split()[0]), "v": N}], dinh=True),
    _n("canh", "Somebody still wins.", dinh=True,
       ve=_ve("one small figure holding a ticket, arms half raised",
              "standing alone in an enormous empty stadium", "quietly stunned",
              "endless empty seats rising in every direction",
              "the figure tiny at the centre of the field", "bright palette")),
            ])


def sinh_hiddenfee(i):
    ten, gia, phan = _lay(PHI_AN, i)
    lon = max(phan, key=lambda x: x[1])
    return (f"What is inside {ten}", f"WHAT IS INSIDE {ten.upper()}", f"{lon[1]}% {lon[0].upper()}",
            [
    _n("so_lieu", "You pay this.", so=_tien(gia), don="", bt="tien", dinh=True,
       ve=_ve("one hand paying at a counter", "handing over payment", "ordinary, unthinking",
              "a plain shop counter", "the payment sharp and close", "muted editorial palette")),
    _n("the_chu", "Almost none of it goes where you think.",
       the="Almost none of it|goes where you think."),
    _n("chart", "Here is the split.", don="percent of the price",
       cot=[{"nhan": _nhan(x[0].split()[-1]), "v": x[1]} for x in phan], dinh=True),
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
    ten, gio, bt = _lay(DOI_NGUOI, i)
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
    ten, db, bt = _lay(AM_THANH, i)
    lan = 10 ** ((db - 60) / 10.0)
    return (f"How loud is {ten}", f"HOW LOUD IS {ten.upper()}", f"{db} DECIBELS",
            [
    _n("so_lieu", _loi("so", i), so=f"{db}", don="decibels", chu=ten, bt=bt, dinh=True,
       ve=_ve(f"{ten} shown clearly, sound waves radiating outward",
              "loud, waves rippling out", "", "a plain backdrop",
              "the source sharp and central", "high-contrast palette")),
    _n("the_chu", "Decibels do not add up the way you think.",
       the="Decibels do not add up|the way you think."),
    _n("chia_doi", "Ten more is ten times more.",
       trai=_moc_khac([{"nhan": "normal talking", "bt": "nguoi", "so": "60 dB"},
                       {"nhan": "a whisper", "bt": "nguoi", "so": "30 dB"}], f"{db} dB"),
       phai={"nhan": ten, "bt": bt, "so": f"{db} dB"}, dinh=True),
    _n("so_lieu", _loi("gap", i), so=f"{lan:,.0f}x", don="the energy of talking",
       bt=bt, dinh=True),
    _n("chart", _loi("so_sanh", i), don="decibels",
       cot=[{"nhan": "whisper", "v": 30}, {"nhan": "talking", "v": 60},
            {"nhan": _nhan(_danh_tu(ten)), "v": db}], dinh=True),
    _n("canh", "Your ears do the maths for you.", dinh=True,
       ve=_ve("one person covering their ears", "flinching away from a loud source",
              "wincing", "a plain backdrop", "sound waves in the near foreground",
              "high-contrast palette")),
            ])


def sinh_whatweighs(i):
    a, b = _cap(KHOI_LUONG, i)
    lon, nho = (a, b) if a[1] >= b[1] else (b, a)
    lan = lon[1] / nho[1]
    return (f"{_hoa(lon[0])} vs {nho[0]}", f"HOW HEAVY IS {lon[0].upper()}", f"{lon[1]:,} POUNDS",
            [
    _n("chia_doi", _loi("so_sanh", i),
       trai={"nhan": nho[0], "bt": nho[2], "so": f"{nho[1]:,} lb"},
       phai={"nhan": lon[0], "bt": lon[2], "so": f"{lon[1]:,} lb"}, dinh=True),
    _n("the_chu", "Weight is the sense we are worst at.",
       the="Weight is the sense|we are worst at."),
    _n("so_lieu", "That is the multiple.", so=f"{lan:,.0f}x", don="heavier", bt=lon[2], dinh=True,
       ve=_ve(f"{lon[0]} resting on one side of an enormous balance scale",
              f"{nho[0]} piled high on the other side", "",
              "a plain backdrop, the scale filling the frame",
              "flat ground beneath the scale", "bright palette")),
    # `i + 3`, KHÔNG phải `i`.  (3/9/2026)
    # Chương này gọi `_loi("so_sanh", i)` HAI lần — một cho nhịp so sánh, một cho nhịp biểu đồ.
    # Cùng vai + cùng chỉ số = **cùng một câu**, và hai nhịp ấy cách nhau ba nhịp (~7 giây), nên
    # người xem nghe đúng một câu hai lần trong bảy giây. Soi bản dài WHATWEIGHS: 12 lần như thế
    # trong một tập, khoảng cách gần nhất 6,0 giây.
    # Không cổng nào bắt: `kiem_khuon` đo khuôn CÂU trên toàn tập, `cham_kich_ban` đo lặp SỐ.
    # Lệch 3 vì hồ `LOI_MAU` có 5 câu — lệch 1 hay 2 vẫn có thể đụng câu của chương kế bên.
    _n("chart", _loi("so_sanh", i + 3), don="pounds",
       cot=[{"nhan": _nhan(nho[0].split()[-1]), "v": nho[1]},
            {"nhan": _nhan(lon[0].split()[-1]), "v": lon[1]}], dinh=True),
    _n("canh", "You guessed wrong. Everyone does.", dinh=True,
       ve=_ve("one person straining to lift something far too heavy",
              "heaving with both arms, feet planted", "red-faced, struggling",
              "a plain backdrop", "the object barely off the ground", "bright palette")),
            ])


def sinh_rightnow(i):
    ds = [("asleep right now", 0.42, "dong_ho"), ("in a car right now", 0.02, "xe"),
          ("eating right now", 0.06, "hop"), ("having a birthday today", 1 / 365.25, "nguoi"),
          ("at work right now", 0.19, "nha"), ("on a phone right now", 0.31, "dien_thoai"),
          ("in school right now", 0.08, "giay"), ("watching something right now", 0.14, "dien_thoai"),
          ("driving right now", 0.015, "xe"), ("cooking right now", 0.05, "lua"),
          ("on a plane right now", 0.00016, "may_bay"), ("being born this minute", 0.0000032, "nguoi"),
          ("waiting in a queue right now", 0.03, "nguoi"), ("in a hospital right now", 0.004, "nha"),
          ("exercising right now", 0.02, "nguoi"), ("shopping right now", 0.04, "tien"),
          ("reading right now", 0.01, "giay"), ("listening to music right now", 0.11, "dien_thoai"),
          ("in a meeting right now", 0.03, "giay"), ("on a train right now", 0.006, "xe_buyt"),
          ("brushing their teeth right now", 0.004, "coc"), ("in a queue at a shop right now", 0.02, "tien"),
          ("laughing right now", 0.05, "nguoi"), ("crying right now", 0.01, "nguoi"),
          ("getting married today", 0.00012, "nguoi"), ("taking a photo right now", 0.03, "dien_thoai"),
          ("on hold right now", 0.002, "dien_thoai"), ("in the air right now", 0.00016, "may_bay"),
          ("having surgery right now", 0.0005, "nha"), ("starting a new job today", 0.0004, "giay")]
    ten, ti, bt = _lay(ds, i)
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
    ten, f, bt = _lay(NHIET_DO, i)
    c = (f - 32) * 5 / 9
    return (f"How hot is {ten}", f"HOW HOT IS {ten.upper()}", f"{f:,}°F",
            [
    _n("so_lieu", _loi("so", i), so=f"{f:,}", don="degrees fahrenheit", chu=ten,
       bt=bt, dinh=True,
       ve=_ve(f"{ten} shown clearly, heat shimmering above it",
              "radiating heat", "", "a plain backdrop", "the source sharp and central",
              "warm high-contrast palette")),
    _n("chia_doi", "Next to a warm room.",
       trai=_moc_khac([{"nhan": "a warm room", "bt": "nha", "so": "70°F"},
                       {"nhan": "a fridge", "bt": "hop", "so": "38°F"}], f"{f:,}°F"),
       phai={"nhan": ten, "bt": bt, "so": f"{f:,}°F"}, dinh=True),
    _n("the_chu", "Your body has a very narrow window.",
       the="Your body has|a very narrow window."),
    # ── BỎ NHỊP ĐỘ C  (4/9/2026) ───────────────────────────────────────────────────────
    # Nhịp này hiện "DEGREES CELSIUS" tràn màn hình trên một kênh MỸ — đúng thứ §12.13 cấm:
    # người xem Mỹ đọc độ C là biết ngay không phải kênh của mình. Và nó là nhịp DUY NHẤT
    # trong cả tệp dùng hệ mét, tức một ngoại lệ lọt qua chứ không phải một quyết định.
    #
    # Không đổi sang °F rồi giữ nguyên câu: "cùng nhiệt độ, thang khác" chỉ có nghĩa khi thang
    # kia là thang người xem dùng. Kênh này sống bằng việc quy con số về thứ CẢM ĐƯỢC, nên thay
    # bằng khoảng cách tới THÂN NHIỆT — mốc duy nhất ai cũng mang sẵn trong người.
    _n("so_lieu", "Outside it, minutes matter.", so=f"{abs(f - 98.6):,.0f}",
       don="degrees from your body", chu="how far this is from 98.6°F", bt=bt),
    _n("chart", _loi("so_sanh", i), don="degrees fahrenheit",
       cot=[{"nhan": "room", "v": 70}, {"nhan": "boiling", "v": 212},
            {"nhan": _nhan(_danh_tu(ten)), "v": f}], dinh=True),
    _n("canh", "We live in a very thin band.", dinh=True,
       ve=_ve("one small figure standing between an icy side and a burning side",
              "arms out, balancing between the two", "wary",
              "half the background frozen blue, half glowing orange",
              "the dividing line running under the figure", "high-contrast palette")),
            ])


def sinh_smallest(i):
    a, b = _cap(CUC_NHO, i)
    lon, nho = (a, b) if a[1] >= b[1] else (b, a)
    lan = lon[1] / nho[1]
    return (f"{_hoa(lon[0])} vs {nho[0]}", f"HOW SMALL IS {nho[0].upper()}",
            f"{lan:,.0f}x SMALLER",
            [
    _n("canh", "Start with something you can see.", dinh=True,
       ve=_ve(f"{lon[0]} shown enormous and clear, filling the frame",
              "magnified far beyond life size", "", "a plain backdrop",
              "the object sharp and central", "clean cool palette")),
    _n("so_lieu", "Now go smaller.", so=f"{lan:,.0f}x", don="smaller", bt=nho[2], dinh=True,
       ve=_ve(f"{nho[0]} shown as a tiny speck beside {lon[0]}",
              "almost invisible next to it", "", "a plain backdrop",
              "both objects on the same flat line", "clean cool palette")),
    _n("the_chu", "Your eyes stop long before this.",
       the="Your eyes stop|long before this."),
    # ── BỎ MÉT VÀ KÝ HIỆU KHOA HỌC  (4/9/2026) ────────────────────────────────────────
    # Nhịp này hiện `5e-04 m` — vừa hệ MÉT trên kênh Mỹ, vừa ký hiệu khoa học mà người xem phổ
    # thông không đọc được. Chú thích của bảng `CUC_NHO` hứa "quy ra đơn vị người Mỹ cảm được"
    # và chưa bao giờ được nối.
    #
    # Và dùng ICON THẬT của bảng thay vì ghim cứng `hop`/`cay`: bảng đã có `nguyen_tu` ·
    # `te_bao` · `vi_khuan` cho từng mục mà KHÔNG chỗ nào đọc — nên nguyên tử hiện ra một CÁI
    # CÂY, hồng cầu hiện ra một cái hộp. Đúng họ lỗi §16.6.
    _n("chia_doi", "Both, at true scale.",
       trai={"nhan": lon[0], "bt": lon[2], "so": _be(lon[1])},
       phai={"nhan": nho[0], "bt": nho[2], "so": _be(nho[1])}, dinh=True),
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
# ══ NGỮ PHÁP RIÊNG TỪNG KÊNH + BIẾN THIÊN THEO TẬP  (1/9/2026) ══════════════════════════════
# Anh: *"style template method xây nội dung 18 channel có gu riêng."*
#
# ── ĐO TRƯỚC KHI THIẾT KẾ ─────────────────────────────────────────────────────────────────
# 18/18 kênh có chuỗi khuôn hình KHÁC NHAU (tốt), nhưng mỗi kênh chỉ có **một** chuỗi duy nhất
# dùng cho MỌI tập: đo 5 tập liên tiếp của cả 18 kênh ra đúng 1,0 chuỗi phân biệt. Người xem hai
# tập liền thấy y hệt một khuôn dựng, dù nội dung đã khác.
#
# ── VÌ SAO KHÔNG ĐẢO THỨ TỰ NHỊP ──────────────────────────────────────────────────────────
# Quy tắc A của bộ này (PHAN_TICH_GIAI_THICH.md): *mỗi cảnh vẽ đúng mệnh đề đang nói*. Lời của
# nhịp được viết cho ĐÚNG vị trí ấy, nên đảo thứ tự là phá vỡ khớp hình–lời — đúng cái làm nên
# chất lượng của thể loại này. Biến thiên phải nằm ở chỗ KHÔNG đụng vào khớp ấy.
#
# ── BA TRỤC BIẾN THIÊN AN TOÀN ────────────────────────────────────────────────────────────
#   `dem`      con số nhỏ kể bằng ĐẾM VẬT thay vì hiện số — cùng nghĩa, khác hẳn thị giác
#   `dai_chu`  thêm dải chữ giữ nguyên một chỗ qua mấy nhịp (quy tắc B: mệnh đề song song)
#   `ke_thua`  đánh dấu mạch cảnh liên tiếp (quy tắc D: cảnh sau kế thừa cảnh trước)
# Cả ba đổi CÁCH KỂ mà không đổi điều đang kể.
GU_KENH = {
    # ma -> (các trục được phép dùng, số biến thể xoay vòng)
    "howlong":   (("dem", "ke_thua"), 3),
    "howbig":    (("dai_chu",), 2),
    "realcost":  (("dem", "dai_chu"), 3),
    "howmuch":   (("dem",), 2),
    "whatif":    (("dai_chu", "ke_thua"), 3),
    "survive":   (("ke_thua",), 2),
    "dayinlife": (("ke_thua", "dai_chu"), 3),
    "wheregoes": (("ke_thua",), 3),
    "therules":  (("dai_chu",), 2),
    "speedof":   (("dem",), 2),
    "odds":      (("dem", "dai_chu"), 3),
    "hiddenfee": (("dai_chu",), 2),
    "yearsof":   (("dem", "ke_thua"), 3),
    "howloud":   (("dai_chu",), 2),
    "whatweighs":(("dem",), 2),
    "rightnow":  (("dem", "dai_chu"), 3),
    "howhot":    (("dai_chu",), 2),
    "smallest":  (("dem",), 2),
}


# ══ BIẾN THỂ CHO LỜI KỂ RIÊNG CỦA TỪNG KÊNH  (1/9/2026) ═════════════════════════════════════
# `LOI_MAU` ở trên chỉ phủ được câu NỐI dùng chung. Đo lại sau bản ấy: vẫn 116/130 câu (89%)
# dùng lại nguyên văn ở mọi tập — và những câu ấy chính là GIỌNG của kênh ("You walk. Light does
# not." · "Nobody says stop. Just look."), nên không thể thay bằng câu nối chung chung.
#
# Bảng này viết 2 cách nói khác cho từng câu, giữ nguyên nghĩa và nhịp. Xoay theo số tập, tất
# định — cùng một tập luôn ra cùng lời, ở máy và trên runner như nhau.
#
# Đặt ở MỘT bảng thay vì sửa 18 bộ sinh: sửa trong hàm thì mỗi lần thêm biến thể phải mở 18 chỗ,
# và đó là cách một bảng thứ hai lặng lẽ mọc ra rồi lệch khỏi bảng đầu.
BIEN_THE = {
    # ── howlong ────────────────────────────────────────────────────────────────────────────
    "You walk. Light does not.": ["Light does not walk. You do.", "You are on foot. Light is not."],
    "Nobody has ever done this.": ["No one has ever tried it.", "This has never been done."],
    "So start walking.": ["So set off.", "So begin the walk."],
    "No breaks.": ["No stopping.", "No rest."],
    "No sleep.": ["No sleeping.", "Not once."],
    "Days go by.": ["The days pass.", "Day after day."],
    "And they keep going.": ["And they do not stop.", "And still more."],
    "You arrive.": ["You get there.", "You finally arrive."],
    "On foot.": ["Walking.", "By foot."],
    "By car.": ["Driving.", "In a car."],
    "By jet.": ["Flying.", "On a plane."],
    "Side by side.": ["All three together.", "Lined up."],
    "Light wins.": ["Light gets there first.", "Light is already done."],
    # ── howbig ─────────────────────────────────────────────────────────────────────────────
    "Two things. One question.": ["Two objects. One question.", "Here are two of them."],
    "Numbers alone mean nothing.": ["A number on its own tells you nothing.",
                                    "Numbers need something to sit next to."],
    "So here is the ratio.": ["So here is how they compare.", "Here is the multiple."],
    "That is the other one.": ["And here is the second.", "Now the other."],
    "Your brain was wrong.": ["Your guess was off.", "That is not what you pictured."],
    # ── realcost ───────────────────────────────────────────────────────────────────────────
    "It feels like nothing.": ["It barely registers.", "It seems too small to matter."],
    "One purchase.": ["Just the one.", "A single buy."],
    "But you do not buy it once.": ["But it is not a one-off.", "But you keep buying it."],
    "That is one year.": ["One year in.", "After twelve months."],
    "Now leave it alone.": ["Now do not touch it.", "Now let it sit."],
    "Ten years of the same habit.": ["Ten years, same habit.", "A decade of the same thing."],
    "Invested instead.": ["Put to work instead.", "Saved instead."],
    "Keep going.": ["Carry on.", "And on."],
    "Thirty years.": ["Three decades.", "Thirty years in."],
    "The habit, or the number.": ["The habit against the number.", "One or the other."],
    "Nobody says stop. Just look.": ["Nobody is telling you to stop. Just look.",
                                     "This is not advice. It is arithmetic."],
    # ── howmuch ────────────────────────────────────────────────────────────────────────────
    "Two words. One letter apart.": ["Two words, one letter apart.", "One letter between them."],
    "Count a million seconds.": ["Start counting to a million.", "Count out a million."],
    "That is a normal trip.": ["That is a holiday.", "That is a couple of weeks."],
    "Now count a billion.": ["Now go to a billion.", "Now the bigger one."],
    "Same scale. Look again.": ["Same axis. Look again.", "Put them on one scale."],
    "One is a trip. One is a life.": ["One is a holiday. One is a lifetime.",
                                      "One you could do. One you could not."],
    # ── whatif ─────────────────────────────────────────────────────────────────────────────
    "One person does it.": ["Start with one person.", "Just one person does it."],
    "Nothing happens.": ["Nothing at all.", "No effect."],
    "Now ten people.": ["Now make it ten.", "Ten people."],
    "Now a hundred.": ["Now a hundred of them.", "A hundred."],
    "Now everyone.": ["Now all of us.", "Everyone at once."],
    "One, against all of us.": ["One person against everyone.", "One, then all."],
    "Small things do not stay small.": ["Small does not stay small.",
                                        "Scale changes what a small thing is."],
    # ── survive ────────────────────────────────────────────────────────────────────────────
    "You. Dropped here.": ["You, put here.", "Here you are."],
    "You need this much.": ["This is what you need.", "Here is the requirement."],
    "Nothing here has a label.": ["Nothing here comes labelled.", "No labels out here."],
    "What you know. What they knew.": ["What you know against what they knew.",
                                       "Your knowledge, and theirs."],
    "That was not instinct.": ["None of that was instinct.", "Instinct had nothing to do with it."],
    "It was training.": ["It was learned.", "It was taught."],
    "Count the days you last.": ["Count how long you last.", "Count the days."],
    "You would last a week.": ["A week, at best.", "About a week."],
    # ── dayinlife ──────────────────────────────────────────────────────────────────────────
    "The day starts before light.": ["The day begins before dawn.", "It starts in the dark."],
    "Up before light.": ["Awake before dawn.", "Up in the dark."],
    "Working through noon.": ["Still at it by midday.", "Straight through noon."],
    "Still going at dusk.": ["Still working at dusk.", "And still going as it gets dark."],
    "That is the daily distance.": ["That is one day's distance.", "That is a single day."],
    "Their day, and yours.": ["Their day against yours.", "Put your day next to theirs."],
    "Then they do it again.": ["Then it starts over.", "And then again tomorrow."],
    "Every day. For life.": ["Every day, for a lifetime.", "Day after day, for good."],
    # ── wheregoes ──────────────────────────────────────────────────────────────────────────
    "You put it in the bin.": ["It goes in the bin.", "You drop it in the bin."],
    "You stop thinking about it.": ["And you forget it.", "That is where your part ends."],
    "It has four more stops.": ["It has four stops to go.", "Four more stops ahead."],
    "First the truck.": ["The truck comes first.", "First stop: the truck."],
    "Then the sorting line.": ["Then it hits the sorting line.", "Next: the sorting line."],
    "Most of it stops here.": ["Most of it goes no further.", "This is where most of it ends."],
    "What you think happens, and what does.": ["What you assume, against what happens.",
                                               "The story you have, and the real one."],
    "Nobody told you. Now you know.": ["Nobody ever explained it. Now you know.",
                                       "No one tells you this part."],
    # ── therules ───────────────────────────────────────────────────────────────────────────
    "You own it. You paid for it.": ["You paid for it. It is yours.", "You bought it outright."],
    "There is still a rule.": ["There is a rule anyway.", "And still there is a rule."],
    "It is written right here.": ["It is written down, right here.", "Here it is, in writing."],
    "What you assumed, and what it says.": ["Your assumption, and the actual wording.",
                                            "What you thought against what it says."],
    "Then the letter arrives.": ["Then a letter turns up.", "And then the letter comes."],
    "Nobody reads it until it matters.": ["Nobody reads it until it costs them.",
                                          "It gets read only when it is too late."],
    # ── speedof ────────────────────────────────────────────────────────────────────────────
    "It happens too fast to see.": ["Too fast for your eyes.", "It is over before you see it."],
    "So here is the number.": ["Here is the actual speed.", "So here is what it is."],
    "Next to you, walking.": ["Next to a person walking.", "Put a walker beside it."],
    "That is the multiple.": ["That is the gap.", "That is how many times over."],
    "You never had a chance.": ["You were never close.", "Not even close."],
    # ── odds ───────────────────────────────────────────────────────────────────────────────
    "These are the real odds.": ["Here are the actual odds.", "These are the true odds."],
    "Numbers that big mean nothing.": ["A number that big does not land.",
                                       "Your head cannot hold a number like that."],
    "So try it once a day.": ["So try every single day.", "So do it daily."],
    "You would need this long.": ["This is how long it would take.", "That is the wait."],
    "Next to things you fear.": ["Beside the things you actually worry about.",
                                 "Next to what you are already afraid of."],
    "Somebody still wins.": ["And yet somebody wins.", "Someone does win."],
    # ── hiddenfee ──────────────────────────────────────────────────────────────────────────
    "You pay this.": ["This is what you pay.", "Here is the price."],
    "Almost none of it goes where you think.": ["Hardly any of it goes where you assume.",
                                                "Almost none of it lands where you expect."],
    "Here is the split.": ["Here is where it goes.", "This is the breakdown."],
    "The biggest slice.": ["The largest share.", "Here is the biggest piece."],
    "What you assumed, and what it is.": ["Your assumption against the real split.",
                                          "What you pictured, and what it is."],
    "Now you can see the price.": ["Now the price makes sense.", "Now you can read the price."],
    # ── yearsof ────────────────────────────────────────────────────────────────────────────
    "It is a few hours a day.": ["A few hours a day.", "Only a few hours each day."],
    "That is today.": ["That is one day.", "That is just today."],
    "Now add up a whole life.": ["Now add up a lifetime.", "Now total a whole life."],
    "Day after day after day.": ["Day after day.", "Every day, without a gap."],
    "Across seventy-nine years.": ["Over seventy-nine years.", "Across a full lifetime."],
    "Against one whole life.": ["Set against a whole life.", "Next to a whole lifetime."],
    "Nobody adds it up.": ["Nobody ever totals it.", "No one adds this up."],
    # ── howloud ────────────────────────────────────────────────────────────────────────────
    "Decibels do not add up the way you think.": ["Decibels do not add the way you expect.",
                                                  "The decibel scale is not what it looks like."],
    "Ten more is ten times more.": ["Ten more decibels is ten times the energy.",
                                    "Add ten, multiply by ten."],
    "Your ears do the maths for you.": ["Your ears hide the maths from you.",
                                        "Your ears compress all of it."],
    # ── whatweighs ─────────────────────────────────────────────────────────────────────────
    "Weight is the sense we are worst at.": ["Weight is the one we judge worst.",
                                             "We are worse at weight than anything."],
    "You guessed wrong. Everyone does.": ["You were wrong. So is everyone.",
                                          "Your guess was off, like everyone's."],
    # ── rightnow ───────────────────────────────────────────────────────────────────────────
    "Right now, while you watch this.": ["Right now, as you watch.", "At this exact moment."],
    "This many people are too.": ["This many others are doing it too.",
                                  "So are this many people."],
    "You, and all of them.": ["You and everyone else.", "You, plus all of them."],
    "Nothing you do is only yours.": ["Nothing you do is yours alone.",
                                      "Whatever you are doing, you are not alone in it."],
    "That is the whole point.": ["That is the point.", "That is the whole idea."],
    # ── howhot ─────────────────────────────────────────────────────────────────────────────
    "Next to a warm room.": ["Next to a comfortable room.", "Beside room temperature."],
    "Your body has a very narrow window.": ["Your body works in a very narrow band.",
                                            "The range your body survives is tiny."],
    "Outside it, minutes matter.": ["Outside that band, minutes count.",
                                    "Step outside it and minutes matter."],
    "We live in a very thin band.": ["We live inside a very thin band.",
                                     "Our whole range is that narrow."],
    # ── smallest ───────────────────────────────────────────────────────────────────────────
    "Start with something you can see.": ["Start with something visible.",
                                          "Begin with something your eyes can catch."],
    "Now go smaller.": ["Now smaller.", "Now go further down."],
    "Your eyes stop long before this.": ["Your eyes gave up long before this.",
                                         "Your eyes stopped a long way back."],
    "Both, at true scale.": ["Both of them, to scale.", "Side by side, at true scale."],
    "Everything you are is built from that.": ["All of you is built from that.",
                                               "Everything you are starts there."],
}


# ── BA BIẾN THỂ NỮA CHO MỖI CÂU: 3 -> 6 LỰA CHỌN  (3/9/2026) ────────────────────────────────
# Anh: *"nó cứ lặp đi lặp lại cùng 1 motip hoài"* — và soi bản dài thì lời còn lặp nặng hơn hình.
#
# Đo trên cả 18 kênh, bản dài 10 chương: **40–58% số câu là LẶP NGUYÊN VĂN**. Kênh ODDS có câu
# xuất hiện đúng 4 lần trong một tập.
#
# Gốc là số học, không phải thiếu cơ chế: `doi_loi` chọn `ds[idx % len(ds)]` với `ds` gồm câu
# gốc + 2 biến thể = **3 lựa chọn**, và nó được gọi với `idx + c` cho từng chương. Mười chương
# chia cho ba lựa chọn thì mỗi biến thể phải dùng 3–4 lần. Cơ chế chạy đúng; cái sai là HỒ quá
# nhỏ so với số lần rút.
#
# Nâng lên 6 lựa chọn thì 10 chương chia cho 6 — mỗi biến thể ~1,7 lần, và ba câu liền nhau
# không còn giống nhau. Đây là cách rẻ nhất: không đụng cơ chế, không thêm lượt gọi AI nào.
#
# Giọng giữ nguyên: câu ngắn, khẳng định, tiếng Anh Mỹ, 2–7 chữ. Câu dài hơn thì cảnh phải giữ
# lâu hơn, và §12.11 đã đo rằng nhịp cắt là việc của khâu VIẾT.
BIEN_THE_THEM = {

"You walk. Light does not.": ("Light travels. You walk.", "One of you is walking.", "Light does not take steps."),
"Nobody has ever done this.": ("Nobody has made this trip.", "It has never been attempted.", "No record of anyone doing it."),
"So start walking.": ("So take the first step.", "So get moving.", "Start walking, then."),
"No breaks.": ("No breaks at all.", "Never stopping.", "Straight through."),
"No sleep.": ("No sleep either.", "Awake the whole way.", "Zero sleep."),
"Days go by.": ("Days keep passing.", "The days add up.", "Time keeps moving."),
"And they keep going.": ("And it continues.", "And there are more.", "And more after that."),
"You arrive.": ("You make it.", "The walk ends.", "You are there."),
"On foot.": ("Walking it.", "Step by step.", "On your own two feet."),
"By car.": ("Behind the wheel.", "In a car instead.", "On the road."),
"By jet.": ("On a jet.", "By air.", "In a plane instead."),
"Side by side.": ("All of them at once.", "Together on one scale.", "Compared directly."),
"Light wins.": ("Light finishes first.", "Light has already arrived.", "Not close."),
"Two things. One question.": ("Two objects, one scale.", "Two of them, side by side.", "A pair to compare."),
"Numbers alone mean nothing.": ("A number by itself is empty.", "Numbers need a comparison.", "On its own, it means nothing."),
"So here is the ratio.": ("So this is the difference.", "Here is how much bigger.", "That is the gap."),
"That is the other one.": ("Here is the second.", "And that is the other.", "The other one, for scale."),
"Your brain was wrong.": ("Your instinct missed it.", "That is not what you expected.", "Your estimate was off."),
"It feels like nothing.": ("It feels harmless.", "It hardly feels like spending.", "It does not feel like much."),
"One purchase.": ("One item.", "A single purchase.", "One transaction."),
"But you do not buy it once.": ("But it repeats.", "But it is every day.", "But once is not how it works."),
"That is one year.": ("That is twelve months.", "One year of it.", "A single year."),
"Now leave it alone.": ("Now leave it there.", "Now do nothing with it.", "Now just wait."),
"Ten years of the same habit.": ("Ten years, unchanged.", "The same habit for ten years.", "Ten years of exactly this."),
"Invested instead.": ("Invested, not spent.", "Sent somewhere else.", "Kept working for you."),
"Keep going.": ("Keep it running.", "Give it longer.", "Now stretch it out."),
"Thirty years.": ("Thirty years of it.", "Three decades in.", "Now thirty years."),
"The habit, or the number.": ("The habit against that number.", "One of the two.", "Habit on one side, number on the other."),
"Nobody says stop. Just look.": ("No one is telling you to quit.", "This is arithmetic, not advice.", "Just look at the number."),
"Two words. One letter apart.": ("One letter separates them.", "Almost the same word.", "A single letter apart."),
"Count a million seconds.": ("Count to a million.", "A million seconds, counted.", "Start at one, go to a million."),
"That is a normal trip.": ("That is a short break.", "About two weeks.", "A normal vacation."),
"Now count a billion.": ("Now a billion.", "Now the larger one.", "Same count, bigger number."),
"Same scale. Look again.": ("One scale for both.", "Now look again.", "Same axis, both numbers."),
"One is a trip. One is a life.": ("One is a vacation. One is a lifetime.", "One fits in a year. One does not.", "One you could sit through. One you could not."),
"One person does it.": ("It starts with one.", "One person, alone.", "A single person does it."),
"Nothing happens.": ("Nothing changes.", "No difference at all.", "Nothing moves."),
"Now ten people.": ("Now ten of them.", "Add nine more.", "Ten at once."),
"Now a hundred.": ("Now one hundred.", "A hundred at once.", "Ten times more."),
"Now everyone.": ("Now all of them.", "Everyone, together.", "All eight billion."),
"One, against all of us.": ("One against everyone.", "From one to all.", "One person, then every person."),
"Small things do not stay small.": ("Small does not stay small at scale.", "Scale changes everything.", "Multiply it and it is not small."),
"You. Dropped here.": ("You, out here.", "Here you are, alone.", "You land here."),
"You need this much.": ("This is the minimum.", "That is what it takes.", "Here is what you need."),
"Nothing here has a label.": ("Nothing is marked.", "There are no instructions.", "No signs, no labels."),
"What you know. What they knew.": ("Yours against theirs.", "Two sets of knowledge.", "What you have, and what they had."),
"That was not instinct.": ("Instinct did not do that.", "That was not born in.", "Nobody is born knowing it."),
"It was training.": ("It was practice.", "Someone taught them.", "Years of learning."),
"Count the days you last.": ("Count how many days.", "Count them off.", "How many days do you get."),
"You would last a week.": ("Roughly a week.", "A week is the answer.", "Seven days, give or take."),
"The day starts before light.": ("It begins in the dark.", "Before sunrise.", "The day opens before dawn."),
"Up before light.": ("Awake before sunrise.", "On your feet in the dark.", "Up while it is still dark."),
"Working through noon.": ("Still going at midday.", "No break at noon.", "Right through the middle of the day."),
"Still going at dusk.": ("Still at it after sunset.", "And still going when the light goes.", "Working past dark."),
"That is the daily distance.": ("That is one day of it.", "That is a single day's work.", "One day, measured."),
"Their day, and yours.": ("Theirs next to yours.", "Two days, compared.", "Your day against theirs."),
"Then they do it again.": ("And again the next day.", "Then it repeats.", "Tomorrow, the same."),
"Every day. For life.": ("Every day, for good.", "For the rest of it.", "No end to it."),
"You put it in the bin.": ("It goes in the recycling.", "You throw it in.", "Into the bin it goes."),
"You stop thinking about it.": ("And that is the last you think of it.", "Then you forget it.", "Your part is over."),
"It has four more stops.": ("There are four stops left.", "Four more places to go.", "The trip is not over."),
"First the truck.": ("The truck first.", "It starts with the truck.", "Stop one: the truck."),
"Then the sorting line.": ("Next, the sorting line.", "Then it gets sorted.", "Stop two: sorting."),
"Most of it stops here.": ("This is the end for most of it.", "Most never goes further.", "Most of it ends right here."),
"What you think happens, and what does.": ("Your version, and the real one.", "What you pictured, and what happens.", "Two versions of the same trip."),
"Nobody told you. Now you know.": ("No one explains this part.", "Now you have seen it.", "Nobody mentions this."),
"You own it. You paid for it.": ("It is yours. You paid.", "You bought it.", "Paid for, and yours."),
"There is still a rule.": ("A rule applies anyway.", "There is a rule regardless.", "It is still covered by a rule."),
"It is written right here.": ("Here it is, written.", "It is in the text.", "Right there in writing."),
"What you assumed, and what it says.": ("Your assumption against the wording.", "What you believed, and what is written.", "Two readings of the same thing."),

"Then the letter arrives.": ("Then a letter shows up.", "Until the letter comes.", "Then something arrives in the mail."),
"Nobody reads it until it matters.": ("Nobody reads it until they have to.", "It sits unread until it counts.", "You read it the day it matters."),
"It happens too fast to see.": ("Too fast for your eyes.", "It is over before you see it.", "You cannot see it happen."),
"So here is the number.": ("So this is the speed.", "Here is what it actually is.", "This is the figure."),
"Next to you, walking.": ("Next to a person walking.", "Against walking pace.", "Compared to you on foot."),
"That is the multiple.": ("That is how many times over.", "That is the factor.", "That is the gap between them."),
"You never had a chance.": ("You were never going to.", "It was never close.", "There was no contest."),
"These are the real odds.": ("Here are the actual odds.", "This is what it really is.", "The true number."),
"Numbers that big mean nothing.": ("A number that size is meaningless.", "Too big to picture.", "Your brain cannot hold that number."),
"So try it once a day.": ("So do it every day.", "One try, every day.", "Once a day, every day."),
"You would need this long.": ("This is how long it takes.", "That is the wait.", "Here is how long."),
"Next to things you fear.": ("Against the things that scare you.", "Compared to what you worry about.", "Next to your actual fears."),
"Somebody still wins.": ("Someone does win.", "And yet someone wins.", "It happens to somebody."),
"You pay this.": ("This is what you hand over.", "Here is what you pay.", "That is the price on the label."),
"Almost none of it goes where you think.": ("Very little goes where you assume.", "Almost none of it lands there.", "Hardly any of it goes there."),
"Here is the split.": ("This is where it goes.", "Here is the breakdown.", "The split looks like this."),
"The biggest slice.": ("The largest share.", "Most of it.", "The biggest piece by far."),
"What you assumed, and what it is.": ("Your guess against the real split.", "What you pictured, and the truth.", "Assumption versus reality."),
"Now you can see the price.": ("Now the real price is visible.", "Now you know what you paid for.", "That is the actual cost."),
"It is a few hours a day.": ("Only a few hours daily.", "A couple of hours a day.", "Just hours, each day."),
"That is today.": ("That is one day.", "That is a single day of it.", "Today alone."),
"Now add up a whole life.": ("Now stretch it across a lifetime.", "Now do the whole life.", "Add up every year."),
"Day after day after day.": ("Every single day.", "Repeated for decades.", "Over and over."),
"Across seventy-nine years.": ("Over a full lifetime.", "Across the whole life.", "Seventy-nine years of it."),
"Against one whole life.": ("Against a lifetime.", "Compared to a life.", "Next to everything you get."),
"Nobody adds it up.": ("Nobody ever totals it.", "No one does this sum.", "The total goes uncounted."),
"Decibels do not add up the way you think.": ("Decibels do not work like normal numbers.", "The scale is not what you assume.", "Adding decibels is not adding."),
"Ten more is ten times more.": ("Add ten, multiply by ten.", "Ten more decibels is ten times the energy.", "Ten up means ten times."),
"Your ears do the maths for you.": ("Your ears compress it.", "Your ears hide the scale.", "Your ears round it off."),
"Weight is the sense we are worst at.": ("We judge weight worst of all.", "Weight is where our guesses fail.", "Nothing fools us like weight."),
"You guessed wrong. Everyone does.": ("Almost nobody gets this right.", "Your guess was off. So is everyone's.", "Everyone misses this one."),
"Right now, while you watch this.": ("At this exact moment.", "While this is playing.", "Right now, as you watch."),
"This many people are too.": ("So are this many others.", "This many, at the same time.", "And this many people with you."),
"You, and all of them.": ("You are one of them.", "You, plus everyone else.", "All of you at once."),
"Nothing you do is only yours.": ("You are never doing it alone.", "Nothing here is only yours.", "Millions are doing it with you."),
"That is the whole point.": ("That is the point.", "That is what this shows.", "That is the takeaway."),
"Next to a warm room.": ("Against room temperature.", "Compared to a warm room.", "Next to where you are sitting."),
"Your body has a very narrow window.": ("Your body works in a narrow band.", "The safe range is tiny.", "You survive in a thin slice of it."),
"Outside it, minutes matter.": ("Past that, minutes count.", "Outside that range, time is short.", "Beyond it, you have minutes."),
"We live in a very thin band.": ("Our range is a sliver.", "We only work in a narrow strip.", "That thin band is all we get."),
"Start with something you can see.": ("Begin with something visible.", "Start where your eyes still work.", "Start with something in view."),
"Now go smaller.": ("Now smaller again.", "Keep shrinking it.", "Now down another step."),
"Your eyes stop long before this.": ("Your eyes gave up long ago.", "This is far past what you can see.", "Sight ended well before here."),
"Both, at true scale.": ("Both on the real scale.", "Side by side, honestly scaled.", "True scale, both of them."),
"Everything you are is built from that.": ("You are made of these.", "All of it starts there.", "That is what you are built from.")
}

for _k, _v in BIEN_THE_THEM.items():
    if _k in BIEN_THE:
        BIEN_THE[_k] = tuple(BIEN_THE[_k]) + tuple(_v)


def doi_loi(nhip: list, idx: int) -> list:
    """Thay lời kể bằng biến thể của tập `idx`. Câu không có trong bảng thì giữ nguyên.

    Xoay theo `idx` chứ không ngẫu nhiên: tất định, nên dựng lại cùng một tập luôn ra cùng lời —
    ở máy và trên runner như nhau. Ngẫu nhiên thì mọi phép so sánh trước/sau đều mất nghĩa.
    """
    for n in nhip:
        l = (n.get("loi") or "").strip()
        bt = BIEN_THE.get(l)
        if not bt:
            continue
        ds = [l] + list(bt)
        n["loi"] = ds[idx % len(ds)]
    return nhip


def _cau_hook(hook: str, lui: str) -> str:
    """Lời của nhịp hook, viết lại từ `hook` của chính tập ấy.

    Giữ ĐÚNG DẤU CÂU: `hook` là chuỗi viết hoa dùng cho tiêu đề ("COULD YOU SURVIVE A DAY IN THE
    ICE AGE"), nhưng nó là một CÂU HỎI — thêm dấu chấm vào là đọc sai ngữ điệu, và giọng máy đọc
    câu hỏi khác câu kể. Nhận biết bằng từ để hỏi ở đầu câu."""
    h = hook.strip().rstrip("?.").strip()
    if not h:
        return lui
    dau = h.split()[0].lower() if h.split() else ""
    hoi = dau in ("how", "what", "why", "could", "can", "would", "will", "is", "are", "do", "does", "where", "who")
    return h.capitalize() + ("?" if hoi else ".")


def ap_gu(ma: str, idx: int, nhip: list) -> list:
    """Áp ngữ pháp riêng của kênh, biến thể xoay theo số tập. Trả về CHÍNH danh sách đã sửa."""
    truc, so_bt = GU_KENH.get(ma, ((), 1))
    if not truc or not nhip:
        return nhip
    bt = idx % so_bt
    if bt == 0:
        return nhip                       # biến thể 0 = giữ nguyên chuỗi gốc của kênh

    if "dem" in truc:
        # Số nhỏ (2..12) kể bằng ĐẾM VẬT. Chỉ đổi MỘT nhịp, và chỉ khi con số đếm được —
        # "8,000 centuries" mà vẽ 8000 vật thì thành một mảng nhiễu, không thành ý.
        for n in nhip:
            if n.get("khuon") != "so_lieu":
                continue
            t = str(n.get("so") or "").replace(",", "")
            if t.isdigit() and 2 <= int(t) <= 12:
                n["khuon"] = "dem"
                n["n"] = int(t)
                n["ngay"] = "day" in str(n.get("don", "")).lower()
                break

    if "dai_chu" in truc:
        # Dải chữ GIỮ NGUYÊN qua các nhịp giữa — quy tắc B: mệnh đề song song thì khung hình
        # song song, và dải chữ là xương sống giữ chúng lại với nhau.
        giua = [n for n in nhip[1:-1] if n.get("khuon") in ("canh", "so_lieu")]
        if len(giua) >= 2:
            d = (giua[0].get("chu") or giua[0].get("don") or "").strip()
            if d:
                for n in giua[:3]:
                    n["dai_chu"] = d.upper()[:34]

    if "ke_thua" in truc:
        # Đánh số mạch cảnh liên tiếp: cảnh thứ mấy trong một chuỗi. Engine dùng nó để cảnh sau
        # mang dấu vết cảnh trước (vệt chân dài dần) thay vì mỗi cảnh một thế giới rời rạc.
        d = 0
        for n in nhip:
            if n.get("khuon") == "canh":
                d += 1
                n["ke_thua"] = d
            else:
                d = 0
    return nhip


def so_chuong_toi_da(ma: str, tran: int = 40) -> int:
    """Số chương LỚN NHẤT mà kênh này còn ra chủ đề khác nhau.

    ── VÌ SAO CẦN  (3/9/2026) ─────────────────────────────────────────────────────────────
    Workflow gọi `--chuong 10` cho mọi kênh. Đo thời lượng thật của cả 18 kênh: **2,4 – 5,0
    phút**, không kênh nào chạm mốc **8 phút** — mốc YouTube cho phép chèn quảng cáo GIỮA video.
    Bộ comic đã làm 8–11 phút đúng vì lý do ấy (§11); bộ giải thích thì chưa ai đo.

    Nhưng không thể nâng đồng loạt: bảng dữ liệu mỗi kênh một cỡ (13–33 mục), và `vi_tri_long`
    quay vòng khi hết mục — nâng quá trần thì chương sau lặp lại chủ đề chương trước, tức đổi
    một lỗi (video ngắn) lấy một lỗi nặng hơn (video lặp).

    Nên ĐO thay vì đoán: chạy bộ sinh cho tới khi tiêu đề trùng, lấy số chương ngay trước đó.
    Rẻ — bộ sinh không gọi mạng, không đọc tiếng, không vẽ ảnh.
    """
    bo = BO_SINH.get(next((k["sinh"] for k in KENH if k["ma"] == ma), ""), None)
    if not bo:
        return 10
    da, giay = [], 0.0
    for c in range(tran):
        try:
            t, _h, _hp, nc = bo(vi_tri_long(ma, 0, c))
        except Exception:
            break
        if t in da:
            break
        da.append(t)
        # Ước thời lượng ngay tại đây: giọng đọc Mỹ ~2,8 chữ/giây (cùng con số `kiem_nhip` dùng),
        # cộng 0,35s khoảng nghỉ mỗi nhịp. Cộng thêm thẻ chương của chương ấy.
        giay += sum(max(1.0, len(str(x.get("loi") or "").split()) / 2.8) + 0.35 for x in nc) + 2.2
        # ── TRẦN THỜI LƯỢNG, KHÔNG CHỈ TRẦN NỘI DUNG  (3/9/2026) ──────────────────────────
        # Bỏ khoá nửa bảng thì HOW BIG ra 12,7 phút và HOW LONG 11,7. Vượt mốc 8 phút là tốt,
        # nhưng §10.1 dặn đo TRẦN THỜI GIAN: bản dài 9 phút mất ~50 phút dựng trên runner, nên
        # 12,7 phút là ~70 phút — và job có trần 330 phút cho NHIỀU vòng.
        # Dừng ở ~10 phút: trên mốc quảng cáo giữa video một khoảng an toàn, mà vẫn còn chỗ cho
        # bốn năm vòng dựng mỗi lượt chạy. Dài hơn nữa đổi số lượng lấy độ dài, không đáng.
        # 520 chứ không 600: ước lượng ở đây đọc `nc` THÔ từ bộ sinh, chưa có nhịp hook, chưa
        # qua `ap_gu`/`doi_loi` (biến thể dài ngắn khác nhau) và chưa có nhịp mở/chốt của
        # `sinh_long`. Đo thực tế: đặt 600 thì bản giao ra 11,2 phút. Chênh ~12%, và cách chữa
        # đúng là hiệu chỉnh HẰNG theo số đo thật, không phải tin vào mô hình (§13.7).
        # 560, hiệu chỉnh lần hai. 520 cho ra 5,99–9,79 phút và `hiddenfee` rơi đúng SÀN 6
        # phút của cổng — sát ngưỡng thì một thay đổi nhỏ ở lời (thêm ba câu khung vào `LOI_MAU`)
        # cũng đủ đẩy nó xuống dưới. Đặt hằng sát ngưỡng là để cổng nổ vì nhiễu.
        # Đây là lần thứ hai hằng này phải hiệu chỉnh theo SỐ ĐO chứ không theo mô hình (§13.7).
        if giay >= 560:
            break
    return max(6, len(da))


def sinh_long(ma: str, idx: int, so_chuong: int = 10):
    k = next(x for x in KENH if x["ma"] == ma)
    bo = BO_SINH[k["sinh"]]
    global _MA_HIEN
    _MA_HIEN = ma            # `_loi` đọc để lệch pha câu nối theo kênh
    nhip, muc = [], []

    # ── MỞ ĐẦU ──────────────────────────────────────────────────────────────────────────
    tieu0, hook0, hp0, _n0 = bo(vi_tri_long(ma, idx, 0))
    nhip.append(_n("the_chu", HOOK_LOI.get(ma, "Here is the question."),
                   the=HOOK_LOI.get(ma, "").replace(". ", ".|"), dinh=True))
    nhip.append(_n("canh", _loi("vao", idx), dinh=True,
                   ve=_ve("one simple cartoon figure standing alone at the centre",
                          "looking straight ahead, about to begin",
                          "calm and curious",
                          "a plain open background with a single horizon line",
                          "flat empty ground", "bright cheerful palette")))

    # ── CÁC CHƯƠNG ──────────────────────────────────────────────────────────────────────
    _phat_the = 0          # đếm LƯỢT PHÁT thẻ tuyên bố — xem chú thích trong vòng lặp
    for c in range(so_chuong):
        tieu, _h, _hp, nc = bo(vi_tri_long(ma, idx, c))
        nc = doi_loi(ap_gu(ma, idx + c, nc), idx + c)   # mỗi chương một biến thể
        if not nc:
            continue
        muc.append((len(nhip), tieu))
        # thẻ chương: dùng chính khuôn thẻ chữ, nhưng NGẮN — nó là mốc, không phải nội dung
        nhip.append(_n("the_chu", tieu + ".", the=f"{c+1}.|{tieu}"))
        # ── THẺ TUYÊN BỐ PHÁT THƯA RA  (3/9/2026) ────────────────────────────────────────
        # Mỗi bộ sinh phát một thẻ chữ mang LUẬN ĐỀ của kênh ("Decibels do not add up the way
        # you think.") trong MỖI chương. Với bản dài 31 chương thì người xem đọc lại nó 31 lần
        # trong bảy phút — đo được 63 thẻ chữ mà chỉ 33 nội dung khác nhau.
        #
        # `_dong_bo_the` đã kéo nó theo 6 biến thể của `doi_loi`, nhưng 31 chương chia cho 6
        # biến thể vẫn là 5 lần mỗi câu. Đây là sàn số học — không sửa được bằng cách thêm biến
        # thể, chỉ sửa được bằng cách phát THƯA.
        #
        # Luận đề là thứ nói MỘT LẦN rồi để người xem mang theo cả tập; nhắc lại mỗi chương làm
        # nó mất trọng lượng. Giữ ở chương 1 và cứ ba chương một lần — vừa đủ để người vào giữa
        # video vẫn bắt được, vừa không thành điệp khúc.
        #
        # Nhận ra thẻ tuyên bố bằng cách loại trừ: thẻ CHƯƠNG có dòng đầu là số (`"3.|Tiêu đề"`).
        def _la_the_chuong(x):
            return str(x.get("the") or "").split("|")[0].rstrip(".").strip().isdigit()

        if c % 3 != 0:
            nc = [x for x in nc
                  if (x.get("khuon") or "") != "the_chu" or _la_the_chuong(x)]
        else:
            # ── BIẾN THỂ THEO LƯỢT PHÁT, KHÔNG THEO SỐ CHƯƠNG  (3/9/2026) ────────────────
            # `doi_loi` chọn biến thể bằng `(idx + c) % 6`. Sau khi lọc, thẻ tuyên bố chỉ phát ở
            # các chương c ≡ 0 (mod 3) — nên chỉ số biến thể cũng chỉ nhận các giá trị ≡ 0 hoặc
            # 3 (mod 6): **2 trong 6 biến thể được dùng, bốn cái còn lại không bao giờ**.
            # `gcd(3, 6) = 3` — đúng cái bẫy modulo đã trả giá ở bộ Kling (§13.13).
            # Đánh số theo LƯỢT PHÁT thì mọi biến thể đều tới lượt.
            for x in nc:
                if (x.get("khuon") or "") == "the_chu" and not _la_the_chuong(x):
                    _ho = _ho_cau().get(str(x.get("loi") or "").strip())
                    if _ho:
                        x["loi"] = _ho[(idx + _phat_the) % len(_ho)]
            _phat_the += 1
        nhip.extend(nc)

    # ── TỔNG HỢP ────────────────────────────────────────────────────────────────────────
    # Chỉ bản dài mới làm được: đặt cả mười chương cạnh nhau trên một trục. Đây là lý do người
    # xem ngồi hết 8 phút thay vì xem một bản ngắn.
    # Nhãn chương tính MỘT LƯỢT cho cả loạt, không tính lẻ từng chương: phép chống thoái
    # hoá trong `_nhan_chuong` so các tiêu đề VỚI NHAU, nên nó cần cả loạt mới quyết được
    # (một tiêu đề đứng một mình không cho biết đâu là khung chung).
    _tieu, _hook = [], []
    for c in range(min(so_chuong, 6)):
        t2, _h2, hp2, _n2 = bo(vi_tri_long(ma, idx, c))
        _tieu.append(t2)
        _hook.append(_so_hook(hp2))
    ten_ch = _nhan_chuong(_tieu)
    cot = [{"nhan": nh, "v": v} for nh, v in zip(ten_ch, _hook) if v is not None]
    # ── BIỂU ĐỒ CHỈ VẼ KHI CÓ SỐ THẬT  (3/9/2026) ──────────────────────────────────────────
    # Bản đầu cạo số bằng `"".join(ch for ch in hp2.split()[0] if ch.isdigit())`. Đo trên cả 18
    # kênh: **5 kênh** (whatif · survive · dayinlife · wheregoes · therules) không có một con số
    # nào trong hook phụ — chúng trả lời ĐỊNH TÍNH ("PROBABLY NOT", hoặc rỗng). Nên nhịp tổng
    # hợp của chúng ra bốn cột `0.0`, và soi khung thì đó là một trục trống có bốn cái nhãn.
    #
    # Không có gì báo lỗi: `float("") or 0` chạy êm, biểu đồ vẫn dựng, video vẫn ra.
    #
    # Không cạo mạnh hơn để chữa — năm kênh ấy THẬT SỰ không có đại lượng để so. Thứ đúng là
    # đổi sang thẻ chữ liệt kê các chương: vẫn là nhịp tổng hợp, và nói thật.
    # Mọi cột bằng nhau cũng là biểu đồ vô nghĩa — trục phẳng lì thì không so được gì. Đây là
    # trạng thái THỨ HAI của cùng một lỗi, và nó không lộ ra ở phép kiểm "có số hay không".
    if len(cot) >= 2 and len({round(c["v"], 6) for c in cot}) >= 2:
        nhip.append(_n("chart", _loi("tong", idx), don="compared", cot=cot, dinh=True))
    elif len(ten_ch) >= 2:
        # Danh sách chương đi vào `the`, KHÔNG vào `chu`.  (4/9/2026)
        # Bản vá §15.13 hôm qua ghi `chu=` — nhưng `TheChu` vẽ `N.the || N.loi` và chưa bao
        # giờ đọc `chu`, nên thứ người xem thấy vẫn chỉ là câu dẫn *"Here they all are, side
        # by side."* cạnh một khung trống: một câu trỏ tới cái không có ở đó. Bản vá đi được
        # đúng nửa đường và không có gì báo (§16.6 — trường được GHI mà không ai ĐỌC).
        # Hai vế ngăn bằng `|` vì `TheChu` xuống dòng ở đó; bốn nhãn một dòng thì chữ bé lại.
        # Khử trùng trước khi lấy bốn: "air traffic controller" và "Apollo mission
        # controller" cùng rút ra `controller`, và một danh sách bốn mục trùng hai thì
        # người xem đọc ra lỗi chứ không đọc ra bốn chương.
        _l, _thay = [], set()
        for x in ten_ch:
            _kx = (x or "").lower()          # KHÔNG đặt tên `k`: `k` là hồ sơ kênh ở phạm vi này
            if x and _kx not in _thay:
                _thay.add(_kx); _l.append(x)
            if len(_l) == 4:
                break
        nhip.append(_n("the_chu", _loi("tong", idx), dinh=True,
                       the=(" · ".join(_l[:2]) + "|" + " · ".join(_l[2:])) if len(_l) > 2
                           else " · ".join(_l)))
    nhip.append(_n("canh", _loi("ket", idx), dinh=True,
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
# ══ CHỌN BA CHƯƠNG HAY NHẤT CỦA BẢN DÀI  (4/9/2026) ════════════════════════════════════════
# Anh: *"không phải cắt, mà lấy từ long rồi dựng lại lấy ra 3 short HAY NHẤT, HOOK NHẤT"*.
#
# Khác nhau thật sự: cắt chương 1·2·3 là lấy theo THỨ TỰ, và thứ tự trong bản dài được xếp
# theo mạch kể chứ không theo sức hút. Đo trên bản dài thật: chương dài từ 6,5 đến 15,5 nhịp
# (10–25 giây) — tức chọn sai chương là ra một short 10 giây trong khi ngay cạnh có chương 25
# giây mạnh hơn.
#
# ── NĂM TRỤC CHẤM, TẤT CẢ ĐO ĐƯỢC, KHÔNG GỌI AI ────────────────────────────────────────────
# Không dùng AI chấm: bộ giải thích sinh kịch bản bằng Python tất định và không tiêu token nào
# (§17.12) — thêm một lượt gọi AI cho mỗi chương là phá đúng tính chất ấy.
#
#   1. CON SỐ CÀNG LỚN CÀNG CHOÁNG   log10 của số lớn nhất trong chương
#   2. HOOK Ở CÂU ĐẦU                phủ định · thu nhỏ kỳ vọng · nói thẳng với người xem
#   3. ĐỘ DÀI ĐÚNG BĂNG 18–22 GIÂY   11–14 nhịp; phạt cả quá ngắn LẪN quá dài
#   4. CÓ NHỊP ĐỐI CHIẾU             `chia_doi` · `chart` · `truc` — so sánh đóng đinh con số
#   5. CÓ HÌNH ĐỂ NHÌN               nhịp có ảnh hoặc biểu tượng, không phải toàn chữ
#
# Trục 3 là trục dễ làm sai nhất: phạt MỘT CHIỀU (chỉ phạt ngắn) thì bộ chọn dồn hết về chương
# dài nhất, và ba short thành ba đoạn 25 giây — vượt băng anh chốt. Phải phạt cả hai phía.
_HOOK = re.compile(r"\b(no|not|never|none|nothing|nobody|cannot|hardly|barely|only|just|"
                   r"every|everyone|all|most|more than|you|your)\b", re.I)


def _cham_chuong(nhip: list) -> float:
    """Điểm sức hút của một chương. Càng cao càng đáng làm short."""
    if not nhip:
        return -1.0
    d = 0.0
    # 1. con số lớn nhất
    lon = 0.0
    for n in nhip:
        v = re.sub(r"[^0-9.]", "", str(n.get("so") or ""))
        try:
            lon = max(lon, float(v))
        except Exception:
            pass
    d += min(30.0, math.log10(lon + 1) * 4.5)
    # 2. hook ở câu đầu
    if _HOOK.search(str(nhip[0].get("loi") or "")):
        d += 18.0
    if str(nhip[0].get("so") or "").strip():
        d += 10.0
    # 3. độ dài đúng băng — phạt HAI CHIỀU
    d += max(0.0, 22.0 - abs(len(nhip) - 12) * 3.0)
    # 4. có nhịp đối chiếu
    if any((n.get("khuon") or "") in ("chia_doi", "chart", "truc") for n in nhip):
        d += 14.0
    # 5. có hình để nhìn
    co = sum(1 for n in nhip if n.get("ve") or n.get("bt") or n.get("nenAnh"))
    d += min(16.0, co / max(1, len(nhip)) * 16.0)
    return d


def chuong_hay(ma: str, idx: int, so_chuong: int, lay: int = 3) -> list:
    """Chỉ số của `lay` chương hay nhất trong bản dài, đã KHỬ TRÙNG chủ thể.

    Khử trùng chủ thể là ràng buộc thứ sáu và nó không nằm trong `_cham_chuong` được, vì nó
    là quan hệ GIỮA các chương đã chọn chứ không phải tính chất của một chương. Ba short cùng
    nói về một vật thì dù mỗi cái đều mạnh, người xem vẫn thấy ba lần một chuyện.
    """
    try:
        _, _, _, _, nhip, muc = kich_ban(ma, idx, True, so_chuong)
    except Exception:
        return []
    if not muc:
        return []
    diem = []
    for c in range(len(muc)):
        d0 = muc[c][0]
        d1 = muc[c + 1][0] if c + 1 < len(muc) else len(nhip)
        diem.append((_cham_chuong(nhip[d0:d1]), c, str(muc[c][1] or "")))
    diem.sort(reverse=True)
    ra, thay = [], set()
    for _, c, ten in diem:
        # chủ thể = danh từ chính của tên chương; hai chương cùng danh từ thì lấy cái điểm cao
        khoa = _nhan(_danh_tu(_bo_so_thu_tu(ten))) if ten else str(c)
        if khoa in thay:
            continue
        thay.add(khoa)
        ra.append(c)
        if len(ra) >= lay:
            break
    return ra


def short_tu_long(ma: str, idx: int, chuong: int, so_chuong: int = 10) -> str:
    """Short 9:16 CẮT RA từ chương `chuong` của bản dài `idx` — dùng lại ảnh của bản dài.

    ── VÌ SAO VIẾT LẠI  (4/9/2026) ─────────────────────────────────────────────────────────
    Anh: *"1 long 3 short, mà 3 short là tận dụng từ long ra, nhặt hook hay ra dựng lại"*.
    Bản cũ có đúng cái TÊN ấy và làm việc khác: `mot_tap(ma, idx + chuong, long=False)` —
    tức dựng một tập short MỚI ở chỉ số lệch, không liên quan gì tới bản dài.

    Đo trên 36 bộ thật: một bộ (1 long + 3 short) tốn 25,8 ảnh CF, trong đó 6,1 ảnh là của ba
    short và **0 ảnh dùng lại được của long**. Chạy 24/7 thì đó là 3.566 ảnh/ngày vẽ thừa —
    21 điểm phần trăm hạn mức — cộng với việc short mất đúng lợi thế "nhặt khoảnh khắc mạnh
    nhất của bản dài ra".

    Docstring nói một đằng, mã làm một nẻo, và không có gì báo. Cùng họ §15.25.

    ── CÁCH LÀM ────────────────────────────────────────────────────────────────────────────
    Đọc `out/v9_<ma>_<idx>_long.json` — tệp props mà chính lượt dựng bản dài đã ghi, và nó
    mang `nhip` ĐÃ CÓ `nenAnh`. Cắt lấy đoạn nhịp của chương, giữ nguyên `nenAnh`, dựng lại
    ở khung dọc. Engine đặt ảnh bằng `objectFit: cover` nên ảnh 16:9 vào khung 9:16 tự cắt
    giữa — mà prompt vốn đã dặn chủ thể ở giữa khung, nên phần bị cắt là hai mép trống.
    Không có tệp ấy (chưa dựng bản dài) thì trả "" và nói rõ, KHÔNG lặng lẽ dựng một short
    rời: dựng nhầm một tập không ai đặt hàng còn tệ hơn không dựng.
    """
    # ── DÙNG BẢN DÀI THẬT SỰ CÓ TRÊN ĐĨA, KHÔNG TÍNH LẠI CHỈ SỐ  (4/9/2026) ─────────────
    # Chạy thật đầu-cuối và hỏng ngay: bản dài dựng ở tập **0002** (`tap_ke` đếm tập kế
    # tiếp), còn `--short-tu-long` gọi `_goc(de)` và đi tìm tập **0003**. Hai đường tính chỉ
    # số độc lập cho một câu hỏi duy nhất — "bản dài nào" — nên chúng lệch nhau ngay lượt
    # đầu, và thông điệp *"chưa có bản dài 3"* đọc ra như thiếu dữ liệu chứ không như lệch
    # chỉ số.
    # Chữa bằng cách hỏi ĐĨA thay vì tính lại: bản dài vừa dựng là tệp props MỚI NHẤT của
    # kênh. §13.15 — dùng chính vật thật, đừng mô hình hoá lại nó.
    pj = os.path.join(GOC, "out", f"v9_{ma}_{idx:04d}_long.json")
    if not os.path.exists(pj):
        import glob as _g
        _ds = sorted(_g.glob(os.path.join(GOC, "out", f"v9_{ma}_*_long.json")),
                     key=os.path.getmtime, reverse=True)
        if _ds:
            pj = _ds[0]
            try:
                idx = int(os.path.basename(pj).split("_")[2])
            except Exception:
                pass
            print(f"   ⓘ {ma}: dùng bản dài mới nhất {os.path.basename(pj)}")
    if not os.path.exists(pj):
        print(f"   ⓘ {ma}: chưa có bản dài {idx} (thiếu {os.path.basename(pj)}) — "
              f"bỏ qua short cắt-từ-long. Dựng bản dài trước.")
        return ""
    try:
        nhip_dai = (json.loads(io.open(pj, encoding="utf-8").read()) or {}).get("nhip") or []
    except Exception as e:
        print(f"   ⚠ đọc {os.path.basename(pj)} hỏng ({str(e)[:60]}) — bỏ qua")
        return ""
    k, tieu, hook, hook_phu, _n, muc = kich_ban(ma, idx, True, so_chuong)
    if not k or not muc:
        return ""
    if chuong >= len(muc):
        print(f"   ⓘ {ma}: bản dài chỉ có {len(muc)} chương, không có chương {chuong}")
        return ""
    dau = muc[chuong][0]
    cuoi = muc[chuong + 1][0] if chuong + 1 < len(muc) else len(nhip_dai)
    # ── GỘP THÊM CHƯƠNG KẾ CHO ĐỦ BĂNG 18–22 GIÂY  (4/9/2026) ──────────────────────────
    # Anh chốt short 18–22 giây = 11–14 nhịp (1,62 giây/nhịp đo thật). Nhưng bản dài dựng với
    # `--chuong 40` bị kẹp còn 21–28 chương, nên mỗi chương chỉ 6,5–8 nhịp ≈ 10–13 giây ở phần
    # lớn kênh. Chọn "chương hay nhất" không cứu được độ dài — nó chọn trong một hồ toàn chương
    # ngắn.
    # Gộp thêm chương LIỀN KỀ chứ không lấy chương xa: hai chương cạnh nhau nối tiếp một mạch
    # kể, nên ghép lại vẫn đọc trôi. Ghép hai chương rời rạc thì short thành hai mẩu không liên
    # quan — dài đúng băng mà mất mạch, đổi một lỗi lấy một lỗi.
    # Trần 14 nhịp: dừng ngay khi ĐỦ, không gộp tiếp. Không có trần thì một chương dài sẵn cộng
    # thêm chương kế sẽ vọt lên 30 giây, vượt băng ở phía kia.
    while cuoi - dau < 11 and chuong + 1 < len(muc):
        chuong += 1
        ke = muc[chuong + 1][0] if chuong + 1 < len(muc) else len(nhip_dai)
        # Trần 16 chứ không 14: khi chương hiện tại còn DƯỚI băng, một short 26 giây tốt
        # hơn một short 13 giây. Trần 14 làm phép gộp từ chối những cặp 8+8, và đo được 11/50
        # short kẹt dưới 15 giây vì đúng lý do ấy — chốt chặn đúng hướng mà đặt quá chặt thì
        # nó chặn luôn thứ nó sinh ra để cứu.
        if ke - dau > 16:
            break
        cuoi = ke
    # Hết chương phía sau thì GỘP LÙI. Chương CUỐI của bản dài không có gì để tiến tới, nên
    # nếu chỉ gộp một chiều thì nó mãi mãi ra short 10 giây — đo được 22/50 short rơi ngoài
    # băng, phần lớn vì lý do ấy. Đúng họ lỗi §6: vá một chiều, để nguyên chiều song song.
    _c = chuong
    while cuoi - dau < 11 and _c > 0:
        _c -= 1
        truoc = muc[_c][0]
        if cuoi - truoc > 16:
            break
        dau = truoc
    lat = [dict(x) for x in nhip_dai[dau:cuoi]]
    if not lat:
        return ""
    # ── HOOK PHẢI LÀ CỦA CHÍNH CHƯƠNG ẤY ────────────────────────────────────────────────
    # Bê nguyên hook của bản dài sang thì ba short của một bản dài mở đầu giống hệt nhau —
    # đúng thứ anh phê về lặp mô-típ. Tên chương là câu ngắn nhất mô tả đúng nội dung đoạn
    # vừa cắt, nên nó là hook tự nhiên của short này.
    ten_chuong = muc[chuong][1]
    _cf = sum(1 for x in lat if x.get("nenAnh"))
    print(f"   ✂ cắt chương {chuong + 1}/{len(muc)} của bản dài {idx}: {len(lat)} nhịp · "
          f"{_cf} ảnh DÙNG LẠI của bản dài (0 lượt CF mới)")
    # TIÊU ĐỀ = CHÍNH TÊN CHƯƠNG. Nối `tieu` của bản dài vào ra chuỗi ba tầng gạch ngang
    # ("How Loud Is It — 3 answers — How loud is a vacuum cleaner") — vừa dài quá mức YouTube
    # hiển thị, vừa lặp tên kênh vốn đã nằm ngay cạnh video. Tên chương tự nó đã là một câu
    # hỏi trọn vẹn và cụ thể hơn tiêu đề bản dài, tức đúng thứ một short cần.
    return mot_tap(ma, idx, doc=True, long=False,
                   san=(ten_chuong or tieu, ten_chuong or hook, hook_phu, lat,
                        f"_c{chuong + 1}"))


# ── BIỂU TƯỢNG DỰ PHÒNG CHO KHUÔN `canh`  (2/9/2026) ────────────────────────────────────────
# Anh gửi khung hình toàn nền trơn. Đo: `canh` có **30 nhịp, 0 nhịp có biểu tượng** — vì thiết
# kế giả định luôn có ảnh AI. Hôm CF còn neuron thì 29/30 có ảnh nên không ai thấy; hôm cạn thì
# cả 30 rơi xuống gradient rỗng. Đúng luật §7: *tầng cuối không gọi mạng thì không bao giờ hỏng*
# — mà `canh` thiếu đúng tầng ấy.
#
# KHÔNG dùng `NenQue`: nó chỉ có 10 nơi chốn sinh hoạt (bếp · phòng khách · sân vườn) lấy từ bộ
# truyện tranh. Đặt bếp sau một câu về động cơ phản lực là đúng lỗi §12.5, và chú thích trong
# engine đã cảnh báo: *"nền ấy nói một điều SAI về nội dung câu, tệ hơn hẳn nền trống"*.
#
# Nên vẽ **chính vật đang nói tới**, lấy từ lời của nhịp. Bảng dưới chỉ chứa những từ mà biểu
# tượng tương ứng CÓ THẬT trong engine (`kiem_hinhve.py` canh chuyện đó).
#
# **Không khớp thì để TRỐNG.** Đoán bừa một biểu tượng sai còn tệ hơn nền trơn: nền trơn không
# nói gì, biểu tượng sai nói một điều SAI. Cùng luật với `don_drive_kenh`: không biết thì đừng ghi.
_BT_TU = (
    ("may_bay",   ("jet", "plane", "aircraft", "flight", "airline", "takeoff")),
    ("xe_buyt",   ("bus", "transit", "commute")),
    ("xe",        ("car", "drive", "driving", "truck", "traffic", "engine", "highway")),
    ("trai_dat",  ("earth", "planet", "world", "globe", "orbit", "equator")),
    ("mat_trang", ("moon", "lunar")),
    ("mat_troi",  ("sun", "solar", "sunlight", "daylight")),
    ("tien",      ("dollar", "money", "cost", "price", "salary", "wage", "paid", "rent", "fee")),
    ("dong_ho",   ("hour", "minute", "second", "clock", "time", "day", "week", "year")),
    ("nha",       ("house", "home", "building", "apartment", "roof", "room")),
    ("nguyen_tu", ("atom", "molecule", "particle", "nuclear")),
    ("te_bao",    ("cell", "blood", "body", "heart", "brain", "lung")),
    ("vi_khuan",  ("bacteria", "germ", "virus", "microbe")),
    ("ca_voi",    ("whale", "ocean", "sea", "shark")),
    ("huou",      ("giraffe", "animal", "elephant")),
    ("meo",       ("cat", "dog", "pet")),
    ("cay",       ("tree", "forest", "wood", "leaf", "plant")),
    ("lua",       ("fire", "burn", "flame", "heat", "hot")),
    ("coc",       ("cup", "coffee", "water", "drink", "glass")),
    ("giuong",    ("bed", "sleep", "asleep", "night")),
    ("dien_thoai", ("phone", "screen", "app", "text", "call")),
    ("nguoi",     ("you", "person", "people", "human", "walk", "step", "hand", "ear", "eye")),
)


# ── GU HÌNH RIÊNG TỪNG KÊNH  (3/9/2026) ─────────────────────────────────────────────────────
# Anh: *"các channel nên có gu style chất nha e"* và *"nó cứ lặp đi lặp lại cùng 1 motip hoài"*.
#
# Đo trên 18 kênh × 4 tập: **41/196 nhịp cảnh dùng lại đúng biểu tượng của nhịp ngay trước**, và
# mỗi kênh bị MỘT biểu tượng chiếm sóng (`dayinlife` ra cái đồng hồ 8 lần, `howmuch` ra hình
# người 11 lần). Soi lưới DAY IN LIFE: 3/9 khung là cùng một cái đồng hồ trong cùng một căn
# phòng. Người xem không đọc ra "kênh về thời gian", họ đọc ra "video bị lỗi".
#
# Gốc: `_bt_canh` không khớp từ nào thì trả `nguoi`, và khớp thì trả đúng một biểu tượng cho mọi
# lần gặp từ ấy. Không có tầng nào biết tới NHỊP TRƯỚC, nên không có gì ngăn lặp.
#
# Bảng này làm hai việc cùng lúc:
#   1. cho mỗi kênh một BỘ TỪ VỰNG HÌNH riêng — phần tử đầu là biểu tượng chữ ký của kênh
#   2. cho `_rai_hinh` chỗ để chọn khi phải tránh lặp, thay vì chọn bừa
#
# Các bộ cố ý ÍT GIAO NHAU: đây chính là trục "cảnh" mà chính sách YouTube nêu tên (§13.17), và
# nó là thứ đo được — không phải cảm giác.
GU_HINH = {
    "howlong":    ("nguoi", "may_bay", "dong_ho", "xe", "trai_dat"),
    "howbig":     ("ca_voi", "xe_buyt", "nha", "huou", "nguoi"),
    "realcost":   ("tien", "coc", "nha", "giay", "dien_thoai"),
    "howmuch":    ("hop", "tien", "coc", "giay", "nguoi"),
    "whatif":     ("trai_dat", "mat_troi", "lua", "mat_trang", "nguoi"),
    "survive":    ("lua", "cay", "mat_trang", "hop", "nguoi"),
    "dayinlife":  ("dong_ho", "giuong", "coc", "giay", "nguoi"),
    "wheregoes":  ("hop", "xe", "nha", "giay", "cay"),
    "therules":   ("giay", "nha", "dong_ho", "hop", "nguoi"),
    "speedof":    ("may_bay", "xe", "nguyen_tu", "mat_troi", "trai_dat"),
    "odds":       ("giay", "tien", "dong_ho", "lua", "nguoi"),
    "hiddenfee":  ("tien", "giay", "dien_thoai", "xe", "hop"),
    "yearsof":    ("cay", "mat_trang", "giuong", "coc", "nguoi"),
    "howloud":    ("dan_piano", "xe", "may_bay", "hop", "nguoi"),
    "whatweighs": ("ca_voi", "xe", "huou", "hop", "nguoi"),
    "rightnow":   ("trai_dat", "dien_thoai", "dong_ho", "xe_buyt", "nguoi"),
    "howhot":     ("lua", "mat_troi", "coc", "nha", "hop"),
    "smallest":   ("te_bao", "vi_khuan", "nguyen_tu", "meo", "nguoi"),
}


# ── GU BỐ CỤC RIÊNG TỪNG KÊNH  (3/9/2026) ───────────────────────────────────────────────────
# Anh: *"nhớ tận dụng dùng cho từng channel 1 sau này nha và cơ chế lưu thông minh để ko chồng
# chéo, lẫn lộn hay lỗi"* · *"các channel nên có gu style chất"*.
#
# `TheChu` có sáu bố cục. Nếu mọi kênh đều rút từ cả sáu thì có ĐA DẠNG nhưng không có BẢN SẮC —
# xem hai video của hai kênh khác nhau vẫn thấy cùng một bộ bài. Nên mỗi kênh chỉ dùng BA, và
# ba ấy chọn theo tính cách kênh:
#
#     0 tràn màu, chữ giữa      — mạnh nhất, dùng cho kênh gây sốc
#     1 số khổng lồ làm nền     — tạp chí, dùng cho kênh về con số
#     2 dải màu giữa khung      — giữ được bối cảnh, nhẹ nhàng
#     3 nền sáng, luật màu dày  — nhẹ nhất, kênh giải thích điềm đạm
#     4 nêm chéo                — phá nhịp, kênh có tiết tấu nhanh
#     5 đĩa số bên trái         — "chương sách", kênh kể theo trình tự
#
# ── VÌ SAO LƯU VÀO NHỊP, KHÔNG SUY RA Ở ENGINE ─────────────────────────────────────────────
# Bản trước engine tự tính `bo = hat + round(N.s * 3)`. Nghĩa là chỗ CHỌN bố cục nằm ở engine
# còn chỗ biết BẢN SẮC KÊNH nằm ở Python — hai nơi, và không nơi nào thấy được nơi kia. Đúng
# họ lỗi "hai nguồn sự thật cho một thứ" (§13.5): sửa bảng gu ở Python mà engine vẫn dựng theo
# công thức cũ, không có lỗi nào báo.
#
# Nay Python quyết định và GHI vào `nhip["bo_the"]`. Engine chỉ đọc. Con số ấy nằm trong tệp
# `.json` của tập nên dựng lại tập cũ ra đúng hình cũ — không có chuyện cùng một kịch bản ra
# hai bố cục ở hai lần dựng.
GU_KHUON = {
    "howlong":    (2, 5, 3),   "howbig":     (0, 1, 4),
    "realcost":   (1, 0, 3),   "howmuch":    (1, 2, 5),
    "whatif":     (4, 0, 2),   "survive":    (0, 4, 1),
    "dayinlife":  (5, 2, 3),   "wheregoes":  (3, 5, 0),
    "therules":   (3, 2, 1),   "speedof":    (4, 1, 0),
    "odds":       (1, 4, 5),   "hiddenfee":  (0, 3, 1),
    "yearsof":    (5, 3, 2),   "howloud":    (0, 2, 4),
    "whatweighs": (1, 5, 4),   "rightnow":   (4, 3, 0),
    "howhot":     (0, 1, 2),   "smallest":   (2, 4, 5),
}


# Khuôn SO SÁNH có ba bố cục (xem `ChiaDoi` trong Khuon.tsx). Mỗi kênh dùng HAI — cùng lý do
# với `GU_KHUON`: đủ đa dạng trong một video, vẫn nhận ra được kênh.
#   0 hai cột + vạch đứt · 1 trên/dưới (nhãn dài thoải mái) · 2 theo TỈ LỆ (chênh lệch thành
#   thứ nhìn thấy được). Bố cục 2 tự rơi về 0 khi hai vế không có số đọc được — cấp một bố cục
#   cho dữ liệu không đỡ nổi nó là cách chắc chắn để ra khung vô nghĩa.
GU_SS = {
    "howlong":    (0, 1), "howbig":     (2, 0), "realcost":   (2, 1), "howmuch":    (2, 0),
    "whatif":     (1, 0), "survive":    (0, 1), "dayinlife":  (1, 0), "wheregoes":  (1, 2),
    "therules":   (1, 0), "speedof":    (2, 1), "odds":       (2, 0), "hiddenfee":  (0, 2),
    "yearsof":    (1, 2), "howloud":    (0, 2), "whatweighs": (2, 1), "rightnow":   (0, 1),
    "howhot":     (2, 0), "smallest":   (2, 1),
}


# Khuôn SỐ LIỆU có bốn bố cục (xem `SoLieu` trong Khuon.tsx). Nó chiếm **29% tổng số nhịp** —
# nhiều thứ hai sau `canh` — nên đây là chỗ đa dạng đáng giá nhất trong cả bộ.
#   0 giữa · 1 canh trái · 2 dải màu · 3 số làm nền
# Mỗi kênh dùng HAI, chọn theo tính cách: kênh về tiền và về con số lớn hợp kiểu 0/2 (con số là
# nhân vật chính); kênh kể chuyện hợp kiểu 1/3 (hình là nhân vật chính).
# ══ DẤU ẤN KÊNH — KHAI RIÊNG, KHÔNG CHỌN TỪ HỒ CHUNG  (4/9/2026) ═══════════════════════════
# Anh: *"mỗi channel có nét riêng để người xem nhớ tới style mỗi channel"*.
#
# Đo hồ sơ hình hiện tại giữa 153 cặp kênh: trung bình trùng 0,39, và cặp tệ nhất — `whatif`
# với `survive` — trùng **79%**. Nguyên nhân là SỐ HỌC chứ không phải thiết kế:
#
#     trục `ss`    có 3 lựa chọn, mỗi kênh dùng 2
#     trục `chart` có 3 lựa chọn, mỗi kênh dùng 2
#     trục `so`    có 4 lựa chọn, mỗi kênh dùng 2
#
# Chọn 2 trong 3 cho 18 kênh thì trùng là BẮT BUỘC. §15.15 đã ghi đúng hình dạng này: *cơ chế
# chạy đúng, hồ quá nhỏ so với số lần rút* — không có gì hỏng để mà sửa, chỉ có một con số cần
# lớn hơn. Nhưng ở đây nới hồ không giải được, vì bản sắc mà CHỌN TỪ hồ chung thì hai kênh
# vẫn có thể rút trúng nhau. Bản sắc phải là thứ **khai riêng**, duy nhất theo thiết kế.
#
# Hai trục, đặt vào hai thứ ĐÃ hiện trong mọi khung nên không thêm món đồ nào:
#   `san` 0-4  cách vẽ ĐƯỜNG CHÂN TRỜI (liền · đôi · đứt · tan một bên · chấm)
#   `so`  0-3  nét quanh CON SỐ        (không · gạch dưới · ngoặc vuông · vạch nhấn lệch)
# 5 × 4 = 20 tổ hợp cho 18 kênh, mỗi kênh một tổ hợp không đụng ai — `selftest` canh điều đó.
#
# Gán theo CHẤT kênh, không gán vòng tròn: kênh số liệu lấy nét kỹ thuật (đứt, ngoặc vuông),
# kênh kể chuyện đời thường lấy nét mềm (chấm, không dấu), kênh dứt khoát lấy nét đậm.
# ══ ĐÃ THỬ VÀ BỎ: CHẤT GIẤY VẼ TAY  (4/9/2026) ════════════════════════════════════════════
# Anh chốt kiểu "chì + màu" sau khi soi bốn biến thể chuyển ảnh bằng Python. Em dựng thử một
# lớp chất giấy (sợi giấy dọc + ố giấy) ở LỚP HOÀN THIỆN của engine — đặt ở đó vì phép chuyển
# nét chì bằng Python chỉ chạm được ảnh CF, còn cảnh vẽ bằng code dựng bằng SVG trong trình
# duyệt; áp riêng cho ảnh CF là làm hai loại khung lệch chất trong cùng một tập.
#
# ĐO RỒI BỎ. Dựng thật ba kênh rồi so A/B ở CỠ THẬT (không ở lưới thu nhỏ — lưới 290px làm em
# đọc nhầm là "bạc màu", trong khi khung đầy đủ hoàn toàn sạch):
#     bão hoà trước 0,099 -> sau 0,092   · gần như không đổi
#     tăng cường độ 3 lần -> VẪN không đọc ra chất giấy
# Nhiễu SVG ở độ phân giải video, đi qua nén H.264, thì tan hết. Một hiệu ứng không ai nhìn
# thấy mà vẫn tốn thời gian dựng là GÁNH NẶNG, không phải tính năng — nên gỡ, không giữ lại
# "cho có".
#
# Và bài học đắt hơn: thứ làm nên vẻ "chì + màu" trong ảnh mẫu là HAI việc khác — khử bão hoà
# xuống ~0,5 và nhấn nét. Lớp giấy không làm việc nào trong hai việc ấy, tức em đã cài SAI
# CÁCH cho đúng yêu cầu. Khử bão hoà thì lại đụng trục bản sắc màu vừa dựng (18 góc cách nhau
# ≥17°), nên nếu làm thì phải làm ở tầng khác và đánh đổi phải nói rõ trước.
# Ghi ra đây để phiên sau không đi làm lại đúng cái vừa bị bác (§13.22).


DAU_AN = {
    "howlong":    (0, 1), "howbig":     (1, 0), "realcost":   (2, 2), "howmuch":    (3, 1),
    "whatif":     (4, 0), "survive":    (3, 3), "dayinlife":  (4, 2), "wheregoes":  (0, 3),
    "therules":   (2, 0), "speedof":    (3, 2), "odds":       (2, 1), "hiddenfee":  (1, 2),
    "yearsof":    (4, 1), "howloud":    (0, 2), "whatweighs": (1, 1), "rightnow":   (2, 3),
    "howhot":     (1, 3), "smallest":   (4, 3),
}


# ── BA TRONG SÁU, KHÔNG PHẢI HAI TRONG BỐN  (nới 4/9/2026) ────────────────────────────────
# `so_lieu` chiếm 31% tổng số nhịp — khuôn nhiều nhất, nên mỗi lựa chọn thêm ở đây đổi nhiều
# khung hơn bất cứ trục nào khác. Engine nay có SÁU bố cục (thêm "hình trên số dưới" và "khối
# góc" — hai bố cục đảo hẳn trọng tâm khung, không phải đổi cỡ trong cùng một sơ đồ).
#
# Mỗi kênh dùng BA: tổ hợp so_lieu của một kênh đi từ 2×3 = 6 lên 3×3 = 9 (+50%), mà ba trên
# sáu vẫn đủ hẹp để hai kênh không đọc ra cùng một bộ bài (§15.2 — đa dạng và bản sắc là hai
# trục, phải giải cùng lúc).
# Bộ ba chọn sao cho hai kênh bất kỳ KHÔNG trùng cả ba: `selftest` canh điều đó.
GU_SO = {
    "howlong":     (0, 1, 2), "howbig":      (0, 3, 4), "realcost":    (1, 3, 5), "howmuch":     (0, 1, 3),
    "whatif":      (0, 3, 5), "survive":     (1, 4, 5), "dayinlife":   (0, 1, 4), "wheregoes":   (0, 4, 5),
    "therules":    (2, 3, 4), "speedof":     (0, 1, 5), "odds":        (1, 2, 3), "hiddenfee":   (2, 3, 5),
    "yearsof":     (0, 2, 3), "howloud":     (1, 2, 4), "whatweighs":  (2, 4, 5), "rightnow":    (0, 2, 4),
    "howhot":      (1, 2, 5), "smallest":    (3, 4, 5),
}


# Khuôn BIỂU ĐỒ có ba bố cục (xem `Chart` trong Khuon.tsx). Nó chỉ chiếm 7% số nhịp nhưng đứng
# ở vị trí đắt nhất — nhịp CHỐT, chỗ người xem thấy toàn cảnh sau khi đã nghe từng phần.
#   0 cột đứng · 1 cột ngang (nhãn dài thoải mái) · 2 chấm–gậy (đọc nhanh ở khung điện thoại)
# Engine tự ép về kiểu 1 khi nhãn quá dài cho cột đứng: bố cục phục vụ dữ liệu, không ngược lại.
GU_CHART = {
    "howlong":    (1, 0), "howbig":     (0, 2), "realcost":   (0, 1), "howmuch":    (2, 0),
    "whatif":     (1, 2), "survive":    (2, 1), "dayinlife":  (1, 2), "wheregoes":  (1, 0),
    "therules":   (2, 1), "speedof":    (0, 2), "odds":       (1, 2), "hiddenfee":  (2, 0),
    "yearsof":    (0, 1), "howloud":    (0, 2), "whatweighs": (2, 1), "rightnow":   (1, 0),
    "howhot":     (0, 1), "smallest":   (2, 0),
}


# Khoảng cách tối thiểu giữa hai lần đọc CÙNG MỘT CÂU, tính bằng số nhịp. 12 nhịp ≈ 25 giây ở
# nhịp cắt trung vị 1,7s — dưới mức ấy tai nhận ra ngay là lặp; trên mức ấy nó đọc ra như một
# câu dẫn quen thuộc của kênh, tức là bản sắc chứ không phải lỗi.
GAN_NHAT = 12

_HO_CAU = None


def _ho_cau() -> dict:
    """Bản đồ NGƯỢC: mỗi câu -> cả họ biến thể của nó (gồm câu gốc).

    Sau khi `doi_loi` thay câu, thứ nằm trong nhịp là một BIẾN THỂ, không phải khoá của
    `BIEN_THE`. Muốn đổi nó sang biến thể khác thì phải tra ngược được về họ.
    """
    global _HO_CAU
    if _HO_CAU is None:
        _HO_CAU = {}
        for goc, bt in BIEN_THE.items():
            ho = [goc] + list(bt)
            for c in ho:
                _HO_CAU[c] = ho
    return _HO_CAU


def _dong_bo_the(nhip: list) -> list:
    """Thẻ chữ phải hiện ĐÚNG câu mà lời đọc nói.  (3/9/2026)

    ── ĐO LÚC PHÁT HIỆN ───────────────────────────────────────────────────────────────────
    Soi lưới bản dài HOW LOUD (31 chương): **31/63 thẻ chữ hiện đúng một câu** —
    *"Decibels do not add up the way you think."* — và khung 1, 3, 7 trong chín khung lấy mẫu
    đều là nó. Bố cục thẻ đã đổi theo `GU_KHUON`, nhưng CHỮ thì không.

    Gốc: bộ sinh khai `_n("the_chu", <lời>, the=<chữ hiện>)` — **hai trường viết tay riêng**.
    `doi_loi` xoay `loi` theo từng chương (6 biến thể) nhưng `the` ghi cứng nên nó đứng yên.
    Người xem ĐỌC `the`, nên họ đọc lại đúng một câu 31 lần trong bảy phút.

    Chữa: khi `the` và `loi` thuộc CÙNG một họ biến thể — tức chúng vốn là một câu, chỉ khác dấu
    ngắt dòng — thì dựng lại `the` từ `loi`. Nhờ đó `the` tự thừa hưởng mọi biến thể mà `doi_loi`
    và `_tranh_lap_gan` đã chọn, không cần cơ chế thứ hai.

    KHÔNG đụng thẻ có số chương (`"3.|Tiêu đề"`): đó là hai dòng nội dung KHÁC nhau, không phải
    một câu bị ngắt. Nhận ra bằng dòng đầu là một chữ số.
    """
    ho = _ho_cau()
    for n in nhip:
        if (n.get("khuon") or "") != "the_chu":
            continue
        t = str(n.get("the") or "").strip()
        l = str(n.get("loi") or "").strip()
        if not t or not l:
            continue
        if t.split("|")[0].rstrip(".").strip().isdigit():
            continue                       # thẻ chương: số + tiêu đề, để nguyên
        phang = t.replace("|", " ").split()
        if phang == l.split():
            continue                       # đã khớp
        hoT = ho.get(" ".join(phang))
        if hoT and l in hoT:
            n["the"] = _ngat_the(l)        # cùng họ -> dựng lại từ lời đọc
    return nhip


def _ngat_the(cau: str) -> str:
    """Chèn dấu `|` (ngắt dòng của thẻ chữ) vào giữa câu, ở ranh giới TỪ.

    Thẻ chữ khai `the="Decibels do not add up|the way you think."` — cùng câu với `loi`, chỉ
    thêm một dấu ngắt. Khi bộ khử lặp đổi `loi` sang biến thể khác thì `the` phải dựng lại từ
    câu mới, nếu không hai trường nói hai câu khác nhau.
    """
    tu = str(cau or "").split()
    if len(tu) < 4:
        return str(cau or "")
    k = (len(tu) + 1) // 2
    return " ".join(tu[:k]) + "|" + " ".join(tu[k:])


def _tranh_lap_gan(nhip: list, ma: str = "") -> list:
    """Không đọc lại CÙNG MỘT CÂU trong vòng `GAN_NHAT` nhịp.  (3/9/2026)

    ── VÌ SAO CẦN  ────────────────────────────────────────────────────────────────────────
    Soi bản dài ODDS: bốn cảnh lặp vòng và lời lặp nguyên văn. Đo trên 18 kênh, bản dài 10
    chương: **7/18 kênh có câu đọc lại trong vòng 30 giây**, gần nhất là 6 giây.

    Nguyên nhân khác nhau ở từng kênh — cùng vai gọi hai lần trong một chương, tiêu đề chương
    trùng lời một nhịp, hồ `LOI_MAU` chỉ 5 câu cho 10 chương. Đuổi từng cái thì sửa được hôm nay
    và tái diễn khi thêm kênh mới.

    Nên chữa ở TẦNG CHUNG, sau khi mọi nhịp đã ghép xong: quét một lượt, câu nào lặp gần thì đổi
    sang một biến thể khác trong CÙNG HỌ mà chưa dùng gần đây. Đây là lỗi **máy sửa được** — hại
    của nó là tai nghe thấy lặp, không phải hình hỏng — nên nó thuộc về `don()`, không thuộc về
    một cổng chặn (§13.23, ba nấc).

    Không đổi được (câu không có họ biến thể) thì GIỮ NGUYÊN và để cổng báo. Đoán bừa một câu
    khác nghĩa còn tệ hơn lặp.
    """
    # ── HOOK KHÔNG ĐƯỢC TRÙNG THẺ CHƯƠNG ĐẦU  (3/9/2026) ───────────────────────────────
    # Bản dài: nhịp hook đọc TIÊU ĐỀ TẬP, rồi thẻ chương 1 đọc lại đúng câu ấy 7 giây sau —
    # vì chương đầu của bản dài chính là chủ đề của hook. Soi ODDS thấy rõ.
    #
    # Chữa ở HOOK chứ không ở thẻ chương: thẻ chương phải nói tên chương (đó là việc của nó),
    # còn hook thì có sẵn một câu mạnh hơn tiêu đề — chính `HOOK_LOI`, câu mâu thuẫn. Đổi ở đây
    # vừa hết trùng vừa làm ba giây đầu mạnh lên (§13.16: thứ chặn ngón tay là điều SAI TRÁI
    # sẵn, không phải một cái tên).
    if ma and len(nhip) > 1:
        _h = str(nhip[0].get("loi") or "").strip()
        _m = (HOOK_LOI.get(ma) or "").strip()
        if _h and _m and _h != _m:
            for _x in nhip[1:GAN_NHAT]:
                if str(_x.get("loi") or "").strip() == _h:
                    nhip[0]["loi"] = _m
                    break
    ho = _ho_cau()
    lan_cuoi = {}
    for j, n in enumerate(nhip):
        l = str(n.get("loi") or "").strip()
        if not l:
            continue
        if j - lan_cuoi.get(l, -999) >= GAN_NHAT:
            lan_cuoi[l] = j
            continue
        thay = ""
        for c in ho.get(l, []):
            if c != l and j - lan_cuoi.get(c, -999) >= GAN_NHAT:
                thay = c
                break
        if thay:
            n["loi"] = thay
            lan_cuoi[thay] = j
        else:
            lan_cuoi[l] = j
    return _dong_bo_the(nhip)


def _rai_chart(ma: str, nhip: list, idx: int = 0) -> list:
    """Gán bố cục cho từng nhịp biểu đồ, xoay trong hai bố cục của kênh."""
    bo = GU_CHART.get(ma) or (0, 1)
    d = 0
    for n in nhip:
        if (n.get("khuon") or "") != "chart":
            continue
        n["kieu_chart"] = bo[(idx + d) % len(bo)]
        d += 1
    return nhip


def _rai_so(ma: str, nhip: list, idx: int = 0) -> list:
    """Gán bố cục cho từng nhịp số liệu, xoay trong hai bố cục của kênh.

    Nhịp HOOK (nhịp 0) luôn lấy bố cục ĐẦU của kênh, không xoay: ba giây đầu là chỗ người xem
    nhận ra kênh, nên nó phải giống nhau qua mọi tập. Đa dạng ở đây đổi lấy nhận diện — sai
    chiều.
    """
    bo = GU_SO.get(ma) or (0, 1)
    d = 0
    for j, n in enumerate(nhip):
        if (n.get("khuon") or "") != "so_lieu":
            continue
        n["kieu_so"] = bo[0] if j == 0 else bo[(idx + d) % len(bo)]
        # Trục bố cục THỨ HAI của `SoLieu`: cỡ và chỗ đặt khối số. Engine từng tự tính bằng
        # `hat % 3` — tức một quyết định nằm ngoài mọi bảng gu, và sửa `GU_SO` không chạm tới
        # được. Nay Python quyết cả hai trục, engine chỉ đọc (§15.3).
        n["bo_so"] = (idx + d) % 3
        d += 1
    return nhip


def _rai_ss(ma: str, nhip: list, idx: int = 0) -> list:
    """Gán bố cục cho từng nhịp so sánh, xoay trong hai bố cục của kênh."""
    bo = GU_SS.get(ma) or (0, 1)
    d = 0
    for n in nhip:
        if (n.get("khuon") or "") != "chia_doi":
            continue
        n["bo_ss"] = bo[(idx + d) % len(bo)]
        d += 1
    return nhip


def _rai_truc(ma: str, nhip: list, idx: int = 0) -> list:
    """Một số tập vẽ phép so sánh bằng TRỤC thay vì bằng biểu đồ cột.

    ── VÌ SAO  (4/9/2026) ──────────────────────────────────────────────────────────────────
    Đo phân bố khuôn trên 18 kênh × 6 tập = 840 nhịp:

        canh 35,7% · so_lieu 29,2% · chia_doi 12,9% · the_chu 7,9% · chart 7,1%
        dem 4,4% · nhom 1,4% · truc 0,7% · kinh_lup 0,7%

    Hai khuôn gánh 65%, ba khuôn cộng lại 2,8%. `truc` và `kinh_lup` có tên trong bảng mà
    thực tế gần như không tồn tại — 6 nhịp trên 840. Đó chính là lời anh chê từ đầu: *"cứ
    lặp đi lặp lại cùng một mô-típ"*.

    Không đổi nhãn được: `Truc` cần `moc` (dãy mốc có thứ tự) chứ không đọc `cot`. Nhưng
    nhịp `chart` ĐÃ MANG đúng dữ liệu ấy — một dãy (tên, giá trị) đã sắp. Cùng một phép so
    sánh, hai cách vẽ: cột thì so DIỆN TÍCH, trục thì so VỊ TRÍ. Nên đây không phải một khuôn
    mới cần nội dung mới, mà là một cách đọc khác của nội dung đang có.

    Xoay theo TẬP, không theo nhịp: một tập chỉ có một hai nhịp `chart`, đổi trong tập thì
    người xem không thấy gì; đổi giữa các tập mới là thứ họ cảm được (§14.9 — đa dạng phải
    nằm ở chỗ người xem NHÌN THẤY, và thứ họ thấy là hai tập liền nhau).
    """
    if idx % 2 == 0:
        return nhip                      # tập chẵn giữ biểu đồ cột
    for n in nhip:
        if (n.get("khuon") or "") != "chart":
            continue
        cot = n.get("cot") or []
        # ── KHỬ TRÙNG TRƯỚC, RỒI MỚI ĐẾM  (soi khung 4/9) ──────────────────────────────
        # Trục `speedof` hiện **"jet 560" HAI LẦN** trên cùng một trục. Bản đầu dựng `moc`
        # thẳng từ `cot` mà không khử trùng, trong khi `cot` ĐƯỢC PHÉP có hai mục cùng tên:
        # biểu đồ cột vẽ hai cột cạnh nhau nên mắt vẫn phân biệt, còn trục thì hai mốc trùng
        # rơi đúng một chỗ và đọc ra là lỗi. Cùng dữ liệu, hai cách vẽ, hai ràng buộc khác
        # nhau — và bản chuyển đổi chỉ mang theo ràng buộc của bên nguồn.
        # Khử theo CẶP (nhãn, giá trị), không theo nhãn: hai mốc cùng tên khác giá trị là dữ
        # liệu thật và phải giữ.
        thay, sach = set(), []
        for c in cot:
            k = (str(c.get("nhan") or "").strip().lower(), _bac_gon(c.get("v")))
            if k in thay:
                continue
            thay.add(k)
            sach.append(c)
        # ── BA MỐC, KHÔNG PHẢI HAI ────────────────────────────────────────────────────────
        # Trần cũ là hai. Soi khung `howbig` và `odds`: trục hai mốc ra một đường dọc với một
        # nhãn ở đỉnh, một ở đáy và khoảng trống chiếm **hai phần ba khung** — đúng chỗ anh
        # chê "khung trống, không toát lên được ý". Hai điểm không dựng được cảm giác THANG
        # ĐO; và `chia_doi` nói đúng nội dung ấy mà kín khung hơn hẳn, nên bỏ qua ở đây là
        # đổi lấy một khuôn tốt hơn, không phải mất một khuôn.
        if len(sach) < 3:
            continue
        cot = sach
        # Trục đọc từ NHỎ tới LỚN. Biểu đồ cột không cần sắp (mắt so chiều cao), trục thì có:
        # mốc để lộn xộn trên một đường thẳng là mất đúng thứ trục sinh ra để nói.
        sap = sorted(cot, key=lambda c: abs(float(c.get("v") or 0)))
        n["khuon"] = "truc"
        n["moc"] = [{"nhan": str(c.get("nhan") or ""), "phu": _bac_gon(c.get("v"))}
                    for c in sap]
        n["vt"] = len(sap) - 1           # mốc lớn nhất là mốc đang nói tới
        n.pop("cot", None)
    return nhip


def _bac_gon(v) -> str:
    """Số rút gọn cho nhãn mốc: 24000 -> 24K. Nhãn trục ngắn thì mắt đọc được cả dãy."""
    try:
        x = abs(float(v))
    except (TypeError, ValueError):
        return ""
    for m, k in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if x >= m:
            return f"{x / m:.1f}".rstrip("0").rstrip(".") + k
    return f"{x:.0f}" if x >= 10 else f"{x:.1f}".rstrip("0").rstrip(".")


_SO_NGUYEN = re.compile(r"^\s*([0-9]{1,2})\s*$")


def _rai_dem(ma: str, nhip: list, idx: int = 0) -> list:
    """Số NHỎ thì cho người xem ĐẾM, đừng bắt họ đọc.

    §12.11 quy tắc C: *thời gian trôi vẽ bằng SỐ LƯỢNG biểu tượng để người xem ĐẾM, không đọc
    "hai tuần sau"*. Khuôn `dem` dựng ra đúng cho việc ấy và đang dùng 4,4%, trong khi `so_lieu`
    gánh 29,2% — trong đó có những nhịp mà con số là **một số nguyên nhỏ**, tức đúng loại đếm
    được bằng mắt.

    Chỉ đổi khi số từ 3 đến 20: dưới ba thì không thành một lượng để đếm, trên hai mươi thì mắt
    thôi đếm và chuyển sang ước lượng — mất đúng thứ khuôn này sinh ra để làm (chính chú thích
    của `Dem` trong engine đã ghi giới hạn ấy).

    Một nhịp mỗi tập, xoay theo `idx` để hai tập liền nhau không đổi cùng một chỗ.
    """
    ung = [n for n in nhip
           if (n.get("khuon") or "") == "so_lieu" and not n.get("nenAnh")
           and _SO_NGUYEN.match(str(n.get("so") or ""))
           and 3 <= int(_SO_NGUYEN.match(str(n.get("so"))).group(1)) <= 20]
    if not ung:
        return nhip
    n = ung[idx % len(ung)]
    n["khuon"] = "dem"
    n["n"] = int(_SO_NGUYEN.match(str(n["so"])).group(1))
    return nhip


def _rai_kinh_lup(ma: str, nhip: list, idx: int = 0) -> list:
    """Thỉnh thoảng SOI GẦN một cảnh thay vì chỉ nhìn toàn cảnh.

    `kinh_lup` dùng 6/840 nhịp — có tên trong bảng mà gần như không tồn tại. Nó không cần nội
    dung mới: nhịp `canh` CÓ ẢNH đã đủ mọi thứ, chỉ thiếu điểm soi.

    Đặt điểm soi vào GIỮA-TRÊN khung, nơi chủ thể đứng — chú thích của `KinhLup` trong engine
    ghi lại một lần nó "phóng to chỗ trống" vì điểm soi để tuỳ tiện. Không đặt nhãn: nhãn phải
    gọi đúng tên thứ được soi, mà ta chỉ biết mã biểu tượng tiếng Việt — đặt bừa một chữ còn
    tệ hơn không có chữ.

    Một nhịp mỗi ba tập: soi gần là một nhấn mạnh, dùng dày thì hết là nhấn mạnh.
    """
    if idx % 3 != 1:
        return nhip
    # LỌC THEO `ve`, KHÔNG THEO `nenAnh`. Ảnh chỉ tồn tại SAU khi `nen_gt.sinh_tap` chạy,
    # còn hàm này chạy lúc sinh kịch bản — lọc theo `nenAnh` thì điều kiện không bao giờ
    # đúng và khuôn này đứng nguyên 0,7%. Bản đầu của em mắc đúng thế, và số đo là thứ
    # duy nhất phát hiện ra: sau khi thêm, tỉ lệ `kinh_lup` KHÔNG đổi một chút nào.
    # `ve` là lời hứa sẽ có ảnh; hứa không thành thì `KinhLup` soi biểu tượng `bt` — mọi
    # nhịp `canh` đều có `bt`, nên không có đường nào dẫn tới ống kính rỗng.
    ung = [n for n in nhip
           if (n.get("khuon") or "") == "canh" and n.get("ve") and not n.get("canh_ve")]
    if not ung:
        return nhip
    n = ung[len(ung) // 2]               # nhịp giữa mạch, không phải mở đầu hay kết
    n["khuon"] = "kinh_lup"
    n["x"] = 0.50
    n["y"] = 0.42
    return nhip


def _rai_khuon(ma: str, nhip: list, idx: int = 0) -> list:
    """Gán bố cục thẻ chữ cho từng nhịp, xoay trong BA bố cục của kênh.

    Xoay theo thứ tự xuất hiện chứ không theo mốc thời gian: một bản dài có mười thẻ chương, và
    chúng phải lần lượt đổi bố cục. Cộng `idx` để hai TẬP của cùng kênh không mở đầu bằng cùng
    một bố cục — thiếu nó thì tập nào cũng "thẻ mở kiểu 5, chương 1 kiểu 2, chương 2 kiểu 3".
    """
    bo = GU_KHUON.get(ma) or (0, 2, 3)
    d = 0
    for n in nhip:
        if (n.get("khuon") or "") != "the_chu":
            continue
        n["bo_the"] = bo[(idx + d) % len(bo)]
        d += 1
    return nhip


# ══ TƯ THẾ NHÂN VẬT — CHỌN THEO CHÍNH CÂU  (4/9/2026) ══════════════════════════════════════
# Năm tư thế trong `BieuTuong` (xem chú thích ở đó). Chọn ở đây chứ không ở engine, vì engine
# không đọc được lời — §15.3: nơi CHỌN và nơi biết nội dung phải là một, rồi TRUYỀN KẾT QUẢ.
#
# Ưu tiên NGHĨA trước, xoay vòng sau: câu có động từ chỉ hành động thì tư thế phải nói đúng
# hành động ấy; câu không có thì mới xoay theo chỉ số nhịp để hai nhịp liền nhau khác nhau.
# Làm ngược lại (xoay trước, khớp nghĩa sau) thì được đa dạng mà mất nghĩa — đúng lỗi vừa sửa
# ở `_rai_hinh`.
TU_THE = (
    (1, ("look", "see", "notice", "number", "count", "many", "much", "big", "more",
         "that is", "here is", "this is")),                      # chỉ tay lên
    (2, ("tired", "quit", "still", "again", "every day", "no end", "wait", "long",
         "hard", "work", "past dark", "keep")),                   # mệt, buông tay
    (3, ("why", "how", "what if", "would you", "could you", "who", "?",
         "nobody", "no one", "never")),                           # dang tay, thắc mắc
    (4, ("walk", "walking", "go", "goes", "went", "run", "move", "start", "leave",
         "arrive", "take", "give", "hand")),                      # bước đi, đưa tay
)


def _tu_the(loi: str, j: int) -> int:
    """Tư thế cho một nhịp có nhân vật. 0 = đứng trung tính."""
    t = f" {str(loi or '').lower()} "
    for tu, khoa in TU_THE:
        for w in khoa:
            if w in t:
                return tu
    return (j % 4) + 1 if j else 0      # nhịp hook giữ tư thế trung tính


# ══ SHORT PHẢI ĐỦ Ý — HAI NHỊP THÊM CHO KÊNH MỎNG  (4/9/2026) ══════════════════════════════
# Anh: *"làm short phải đủ ý, không làm quá ngắn, và phải hook hay"*.
#
# Đo 18 kênh: **10 kênh ra short dưới 12 giây**, tám kênh đúng 6 nhịp ≈ 10 giây. Sáu nhịp vẫn
# là một vòng trọn vẹn (hook → khẳng định → dựng → số → so sánh → chốt) nhưng NÉN: người xem
# nhận con số mà không kịp CẢM nó, và không có gì để mang đi.
#
# Hai nhịp thiếu, và cả hai đều là thứ ngách này sống bằng:
#   · QUY ĐỔI — con số về thứ người xem cảm được (§12.13). "1 trong 292 triệu" không cảm được;
#     "mua mỗi ngày, tám nghìn năm" thì cảm được.
#   · HỆ QUẢ — nó đổi gì cho người xem. Không có nhịp này thì short kết thúc ở một dữ kiện,
#     và dữ kiện không giữ chân ai.
#
# ── VÌ SAO VIẾT TAY TỪNG KÊNH, KHÔNG SINH TỰ ĐỘNG ─────────────────────────────────────────
# Một phép ghép tự động chỉ dùng được thứ có trong nhịp (con số, đơn vị), và nó sẽ đẻ ra câu
# đúng ngữ pháp mà rỗng nghĩa — tức ĐỘN cho dài, đúng cái anh dặn tránh. Mỗi kênh nói một
# chuyện khác nhau nên câu quy đổi và câu hệ quả phải khác nhau. Hai câu mỗi kênh là ít, và
# chúng là NỘI DUNG chứ không phải khuôn.
#
# ── VÌ SAO CHÈN TRƯỚC NHỊP CHỐT ───────────────────────────────────────────────────────────
# Nhịp cuối là câu đóng; nối thêm vào sau nó là đóng hai lần. Chèn ở vị trí -1 giữ nguyên cú
# chốt mà vẫn kéo dài phần thân.
THEM_NHIP: dict[str, tuple[str, str, str]] = {
    # BA câu cho mỗi kênh, theo đúng ba vai:
    #   [0] QUY ĐỔI  — con số về thứ người xem CẢM được (§12.13)
    #   [1] ĐỜI SỐNG — nó chạm vào ngày thường của người xem ở đâu
    #   [2] HỆ QUẢ   — nó đổi gì; câu này phải MANG ĐI ĐƯỢC, không phải một dữ kiện nữa
    # Viết tay từng kênh: ghép tự động chỉ dùng được con số trong nhịp, và sẽ ra câu đúng ngữ
    # pháp mà rỗng nghĩa — tức ĐỘN cho dài, đúng cái phải tránh.
    "odds":       ("Every day for eight thousand years.",
                   "A whole life of tickets is one blink of that.",
                   "The ticket is the price of the daydream."),
    "howloud":    ("Three steps back halves it.",
                   "Your commute sits above the safe line most days.",
                   "Distance is the only free protection."),
    "therules":   ("The line is on a map you never saw.",
                   "It decides your fence, your trees, your driveway.",
                   "Ask before you build, not after."),
    "hiddenfee":  ("Under a tenth of it is the thing itself.",
                   "The rest is rent, wages, cards and waste.",
                   "You are paying for the trip, not the cup."),
    "howhot":     ("Hot enough to boil it away in a second.",
                   "Nothing you own would arrive as a solid.",
                   "Heat that high stops being a temperature."),
    "rightnow":   ("More than the country you live in.",
                   "All of it happening while you hold this phone.",
                   "You are never the only one awake."),
    "smallest":   ("Line up a billion and you reach a finger.",
                   "Everything you touch is mostly this and space.",
                   "Scale is where intuition quits."),
    "whatweighs": ("It would take a hundred people to lift.",
                   "You carry a version of this every grocery run.",
                   "Weight is not size, and never was."),
    "speedof":    ("Blink and it has already passed you.",
                   "Every drive home is a slow version of this.",
                   "Your eyes were never fast enough."),
    "whatif":     ("One person changes nothing measurable.",
                   "Ten thousand doing it is a different number.",
                   "Everyone is the only unit that moves it."),
    "dayinlife":  ("Sixteen hours before the light came back.",
                   "No weekend, no notice, no way out of it.",
                   "The job was the whole life, not part of it."),
    "howmuch":    ("A million seconds is eleven days.",
                   "A billion is thirty-one years of them.",
                   "The word changes by three letters. The gap does not."),
    "wheregoes":  ("Most of it never becomes what you pictured.",
                   "The bin is a sorting problem, not an ending.",
                   "Where it goes depends on what you did first."),
    "yearsof":    ("That is years you will not get a second time.",
                   "It happens in minutes you never noticed spending.",
                   "Small daily numbers are the only ones that compound."),
    "howbig":     ("Stand it up and it clears the tree line.",
                   "You have walked past something this size and not looked.",
                   "Size stops registering once it leaves human scale."),
    "survive":    ("The first night is the one that decides it.",
                   "No fire, no shelter, no second attempt.",
                   "Preparation is the whole of the answer."),
}
# ── HIỆU CHỈNH SAU KHI ĐO CLIP THẬT  (4/9/2026) ───────────────────────────────────────────
# Đặt 11 nhịp vì đo được 1,62 giây/nhịp trên các clip dựng TRƯỚC khi thêm nhịp. Dựng lại 6
# clip sau khi thêm: **2,21 giây/nhịp** — lệch 37%, và 11 nhịp ra 23–26 giây, vượt băng
# 18–22 anh chốt.
# Gốc: hằng cũ đo trên bộ nhịp CŨ. Nhịp em thêm (quy đổi · đời sống · đối chiếu · hệ quả) có
# câu dài hơn nhịp trung bình, nên chính việc thêm nhịp làm đổi luôn cái hằng số dùng để tính
# số nhịp cần thêm. §13.6 — hằng số sống lâu hơn ngữ cảnh sinh ra nó; đổi một hàm thì phải đi
# soát mọi hằng số hàm ấy từng nuôi.
# 18 ÷ 2,21 ≈ 8. Sàn 8, và băng thật là 8–10 nhịp.
SAN_NHIP = 9          # 9 nhịp × 2,21 giây đo lại ≈ 20 giây, giữa băng 18–22 — xem `t_short_du_y_va_hook`


# ══ HAI NHỊP ĐỔI THEO TẬP — LẤY TỪ CHÍNH BẢNG DỮ LIỆU CỦA KÊNH  (4/9/2026) ═════════════════
# Anh chốt short 18–22 giây, tức ≥11 nhịp (1,62 giây/nhịp đo thật). Ba nhịp viết tay đưa được
# lên 9. Hai nhịp cuối KHÔNG được viết cố định nữa, và đây là lý do đo được:
#
#   tỉ lệ câu GIỐNG HỆT giữa 4 tập của cùng một kênh, hiện tại : 30%  (therules/odds 44%)
#   nếu thêm 2 nhịp hằng số nữa (5/11 nhịp là hằng)            : ~48%
#
# Gần một nửa mỗi tập giống hệt tập trước là đúng thứ luật YouTube nhắm tới — *"các video của
# CHÍNH BẠN giống hệt nhau"* (§13.18). Làm dài bằng cách lặp là đổi một vấn đề lấy một vấn đề
# nặng hơn.
#
# Nên hai nhịp cuối lấy MỘT MỤC KHÁC trong chính bảng của kênh — mục ấy đổi theo `idx`, nên
# câu đổi theo tập mà vẫn là dữ liệu thật, không phải câu độn. `_cap()` đã đi hết n·(n−1) tổ
# hợp nên hai mục không bao giờ trùng nhau và chuỗi không lặp sớm.
BANG_KENH: dict[str, tuple] = {
    #  kênh        bảng          đơn vị hiện ra          mẫu câu đối chiếu
    "odds":       ("XAC_SUAT",  "1 in {v:,}",  "Next to {t}."),
    "howloud":    ("AM_THANH",  "{v} dB",      "Now put {t} beside it."),
    "whatweighs": ("KHOI_LUONG","{v:,} lb",    "Against {t}."),
    "howhot":     ("NHIET_DO",  "{v:,}°F",     "Now {t}."),
    "smallest":   ("CUC_NHO",   "",            "Beside {t}."),
    "howbig":     ("CO_LON",    "{v:,.0f} ft", "Next to {t}."),
    "yearsof":    ("DOI_NGUOI", "{v} hrs/day", "And {t}."),
    "howlong":    ("QUANG_DUONG","{v:,} mi",   "Or {t}."),
    "hiddenfee":  ("PHI_AN",    "${v:,.0f}",   "Same story with {t}."),
    "realcost":   ("THOI_QUEN", "${v:,.0f}",   "Or {t}."),
}


def _hai_nhip_du_lieu(ma: str, idx: int, bt: str) -> list:
    """Hai nhịp đối chiếu lấy từ bảng của kênh — ĐỔI THEO TẬP, không phải câu cố định."""
    cau = BANG_KENH.get(ma)
    if not cau:
        # ── KÊNH KHÔNG CÓ BẢNG MÔ-ĐUN: LẤY CHỦ THỂ CỦA MỘT TẬP KHÁC  (4/9/2026) ────────
        # Tám kênh (`rightnow`, `therules`, `speedof`, `whatif`, `dayinlife`, `wheregoes`,
        # `survive`, `howmuch`) giữ danh sách nội dung CỤC BỘ trong hàm sinh, không phải bảng
        # mô-đun — nên `BANG_KENH` với tới không được. Nâng chúng lên mô-đun là tám lượt sửa
        # cơ học vào tám hàm, mỗi lượt một cơ hội gãy.
        # Không cần: chính hàm sinh đã trả về TIÊU ĐỀ của mỗi tập, và tiêu đề là tên chủ thể
        # của tập ấy. Lấy tiêu đề của một tập KHÁC làm vế đối chiếu cho ra đúng thứ bảng dữ
        # liệu cho — một chủ thể thật của kênh, đổi theo `idx`.
        # Lấy TÊN chứ không lấy cả nhịp: bê nguyên một nhịp sang thì tập này chứa một câu mà
        # tập kia cũng có, tức tự đẩy tỉ lệ trùng lên — đúng cái đang tránh.
        try:
            khac = BO_SINH[ma](idx + 7)[0]
        except Exception:
            return []
        khac = re.sub(r"^(The |A |An |How |What |Where |Could you |Years of )", "", str(khac)).strip()
        # ── PHẢI LÀ CỤM DANH TỪ, KHÔNG PHẢI MỆNH ĐỀ  (soi khung 4/9) ──────────────────
        # Khung RIGHT NOW ra câu vỡ: *"Now put many people are in the air right now beside
        # it."* — tiêu đề của kênh ấy là một MỆNH ĐỀ ("how many people are in the air right
        # now"), và cắt tiền tố xong vẫn còn nguyên động từ.
        # Khuôn câu `"Now put {x} beside it"` chỉ nhận một cụm danh từ. Thà BỎ nhịp còn hơn
        # ghép ra một câu sai: nhịp thiếu chỉ làm short ngắn hơn một chút, câu sai thì người
        # xem đọc ra máy viết.
        if (len(khac.split()) > 6
                or re.search(r"\b(is|are|was|were|do|does|did|goes|go|comes|come|"
                             r"takes|take|will|would|can|could)\b", khac, re.I)):
            return []
        if not khac:
            return []
        return [
            _n("so_lieu", f"Now put {khac} beside it.", so="", don="", bt=bt, dinh=True),
            # Khuôn TỰ VẼ, không mượn biểu tượng: mượn thì hai nhịp liền nhau cùng hình,
            # và `_rai_hinh` cố ý giữ hình trùng thay vì gán hình sai nên không ai dọn hộ.
            _n("the_chu", "Same scale, different thing.",
               the="Same scale,|different thing."),
        ]
    ten_bang, khuon_so, khuon_cau = cau
    bang = globals().get(ten_bang) or []
    if len(bang) < 4:
        return []
    # Lấy mục CÁCH XA mục chính của tập này, để hai con số đủ khác nhau mà đáng so.
    a, b = _cap(bang, idx + 7)
    ten, gt = str(b[0]), b[1]
    try:
        so = khuon_so.format(v=gt) if khuon_so else ""
    except Exception:
        so = ""
    return [
        _n("so_lieu", khuon_cau.format(t=ten), so=so, don="", bt=bt, dinh=True),
        _n("the_chu", "Same scale, different thing.",
           the="Same scale,|different thing."),
    ]


def _day_du_y(ma: str, nhip: list, idx: int = 0) -> list:
    """Chèn nhịp quy đổi + hệ quả cho kênh mỏng. Không đụng kênh đã đủ dài."""
    them = THEM_NHIP.get(ma)
    if not them or len(nhip) >= SAN_NHIP or len(nhip) < 3:
        return nhip
    quy, doi, he = them
    # Mượn biểu tượng của nhịp áp chót để hai nhịp mới thuộc về cùng một cảnh, không nhảy
    # sang một thế giới khác ngay trước cú chốt.
    bt = next((n.get("bt") for n in reversed(nhip[:-1]) if n.get("bt")), "nguoi")
    # ── THÊM ĐÚNG SỐ CÒN THIẾU, KHÔNG THÊM ĐỦ BỘ  (4/9/2026) ───────────────────────────
    # Bản trước luôn chèn cả năm nhịp, nên kênh thiếu 2 cũng nhận 5 và vọt lên 24 giây — vượt
    # băng 18–22 ở phía kia. Chốt chặn đúng hướng mà không đếm thì nó bắn quá đích.
    # Xếp theo GIÁ TRỊ giảm dần, rồi cắt: quy đổi (con số về thứ cảm được, §12.13) > hệ quả
    # (thứ mang đi được) > đối chiếu dữ liệu (đổi theo tập) > câu đời sống. Thiếu một nhịp thì
    # nhịp ấy phải là nhịp đáng nhất, không phải nhịp đầu danh sách.
    can = max(0, SAN_NHIP - len(nhip))
    moi = [
        _n("so_lieu", quy, so=(nhip[0].get("so") or ""), don=(nhip[0].get("don") or ""),
           bt=bt, dinh=True),
        # Hình lấy từ CHÍNH câu này, không mượn của nhịp trước. Mượn thì hai nhịp liền
        # nhau cùng hình, và `_rai_hinh` cố ý GIỮ hình trùng thay vì gán một hình sai
        # (đúng luật "lặp một hình đúng còn hơn thay bằng hình sai") — nên trùng ở đây
        # không ai dọn hộ. Câu không khớp danh từ nào thì ra `nguoi`, mà `nguoi` được
        # phép lặp vì nó phân biệt bằng TƯ THẾ.
        _n("canh", doi, bt=_bt_canh(doi)),
    ]
    # Hai nhịp dữ liệu chèn GIỮA phần viết tay và câu hệ quả: chúng là bằng chứng, và bằng
    # chứng phải đứng trước kết luận.
    moi.append(_n("the_chu", he, the=he.replace(". ", ".|")))
    moi += _hai_nhip_du_lieu(ma, idx, bt)
    # `moi` đang xếp: quy đổi · đời sống · hệ quả · hai nhịp dữ liệu. Cắt theo nhu cầu, nhưng
    # LUÔN giữ câu hệ quả — short kết ở một dữ kiện thì không ai mang đi được gì.
    if can < len(moi):
        giu = moi[:max(1, can)]
        _he = moi[2]
        if _he not in giu:
            giu = giu[:-1] + [_he] if len(giu) > 1 else [_he]
        moi = giu
    return nhip[:-1] + moi + nhip[-1:]


def _rai_tu_the(nhip: list, ma_kenh: str = "") -> list:
    """Gán `tu` cho mọi nhịp vẽ nhân vật, và không để hai nhịp liền nhau trùng tư thế."""
    # PHẠM VI PHẢI KHỚP CHỖ NHÂN VẬT THẬT SỰ ĐƯỢC VẼ TOÀN KHUNG: `canh` · `nhom` ·
    # `kinh_lup`. Bản đầu xét mọi nhịp có `bt="nguoi"`, kể cả `so_lieu` — mà `so_lieu` vẽ
    # biểu tượng nhỏ trong khối số, không vẽ nhân vật. Hậu quả: một nhịp `so_lieu` xen giữa
    # hai nhịp `canh` làm đứt mạch so sánh, nên hai nhịp `canh` liền nhau (thứ người xem
    # THẬT SỰ thấy nối nhau) vẫn lọt tư thế trùng. Cổng bắt được đúng hai ca ấy.
    # Đây là lỗi lệch phạm vi mà chú thích trong chính cổng đã cảnh báo — lần này hàm lệch,
    # không phải cổng lệch.
    truoc = -1
    dem_ng = 0
    for j, n in enumerate(nhip):
        # CHỈ so giữa những nhịp THẬT SỰ vẽ nhân vật toàn khung, và KHÔNG cắt mạch ở nhịp
        # không vẽ gì. Hai bản trước đều sai một đầu:
        #   · xét mọi `bt="nguoi"` -> tính cả `so_lieu` (vẽ biểu tượng nhỏ trong khối số,
        #     không vẽ nhân vật), nên hai nhịp `canh` liền nhau vẫn lọt tư thế trùng;
        #   · cắt mạch ở nhịp không phải người -> hai nhịp `nhom` KHÔNG CÓ hình xen giữa
        #     làm mạch reset, và người xem vẫn thấy hai nhân vật cùng tư thế nối nhau.
        # Định nghĩa đúng là *nhịp có vẽ nhân vật*, và nhịp không vẽ gì thì trong suốt.
        if (n.get("khuon") or "") not in ("canh", "nhom", "kinh_lup"):
            continue
        if (n.get("bt") or "") != "nguoi":
            continue
        t = _tu_the(n.get("loi") or "", j)
        if t == truoc:
            # Trùng thì lệch một bậc trong năm tư thế. Khác với chuyện đổi BIỂU TƯỢNG: đổi
            # tư thế không đổi thứ đang được vẽ, nên nó không bao giờ làm sai nghĩa câu.
            t = (t + 1) % 5
        n["tu"] = t
        # ── DÀN NHÂN VẬT, KHÔNG PHẢI MỘT NGƯỜI  (4/9/2026) ──────────────────────────────
        # Anh: *"lặp đi lặp lại 1 nhân vật, nhàm chán, không ra đâu cả"*. Tư thế thôi chưa
        # đủ — bốn ảnh anh gửi có nhiều người KHÁC NHAU (tóc bù, tóc tết bím, có râu), cùng
        # một khuôn mặt trắng nhưng khác tóc khác áo.
        # Đổi theo NHỊP, không theo tập: người xem so hai khung liền nhau, không so hai tập
        # (§14.9). Lệch pha theo kênh để hai kênh không ra cùng thứ tự dàn diễn viên.
        # ĐẾM THEO NHỊP NGƯỜI, không theo chỉ số nhịp bất kỳ. Dùng `j` thì hai nhịp người
        # cách nhau 2 nhịp, nên `% 4` chỉ ra HAI giá trị trong một tập — soi bốn khung
        # `therules` thấy cả bốn cùng một áo. Dàn bốn người thành hai người, và cơ chế vẫn
        # "chạy đúng" nên không có gì báo.
        n["nv"] = (dem_ng + _lech_kenh(ma_kenh)) % 4 if ma_kenh else dem_ng % 4
        dem_ng += 1
        truoc = t
    return nhip


def _rai_hinh(ma: str, nhip: list, idx: int = 0) -> list:
    """Không nhịp cảnh nào dùng lại biểu tượng của nhịp ngay trước.

    Chỉ đụng vào nhịp bị TRÙNG — biểu tượng khớp đúng từ ("a jet" -> máy bay) luôn được giữ, vì
    hình đúng nghĩa quan trọng hơn hình đa dạng. Chỉ khi hai nhịp liền nhau ra cùng một hình
    thì nhịp sau mới đổi sang biểu tượng khác trong bộ của kênh.

    `idx` xoay điểm bắt đầu nên hai TẬP của cùng một kênh cũng không rơi vào cùng một chuỗi
    thay thế — không có nó thì tập nào cũng "đồng hồ, giường, đồng hồ, giường".
    """
    bo = GU_HINH.get(ma) or ("nguoi", "nha", "dong_ho", "hop", "giay")
    truoc = ""
    for j, n in enumerate(nhip):
        if (n.get("khuon") or "") not in ("canh", "kinh_lup"):
            continue
        b = n.get("bt") or ""
        # ── NGƯỜI ĐƯỢC PHÉP LẶP  (4/9/2026) ─────────────────────────────────────────────
        # Sau khi buộc đồ vật phải lấy từ LỜI, `nguoi` chiếm 64% nhịp `canh` — vì phần lớn
        # câu không chứa danh từ vẽ được. Cho phép chống-trùng đổi những nhịp ấy đi thì nó
        # lại nhặt đồ vật trong phông nền, tức kéo đúng lỗi vừa sửa quay lại.
        # Bốn ảnh anh gửi đều có người ở MỌI khung, và cái đổi giữa khung này với khung kia
        # là TƯ THẾ và BIỂU CẢM, không phải đổi người thành cái đồng hồ. Nhân vật lặp lại là
        # DÀN DIỄN VIÊN của chương trình, không phải một lỗi lặp.
        if b == "nguoi":
            truoc = b
            continue
        if b and b == truoc:
            # ── HÌNH KHỚP THỨ HAI CỦA CHÍNH CÂU ẤY, TRƯỚC ĐÃ  (4/9/2026) ─────────────
            # Bản cũ nhảy thẳng sang bộ hình của kênh, tức đổi lấy đa dạng bằng cách bỏ
            # hẳn nghĩa — soi khung ra ngôi nhà cho câu nói về đêm tối. Nay hỏi lại chính
            # câu xem nó còn khớp hình nào khác không.
            c = next((x for x in _bt_canh_ds(n.get("loi", ""), n.get("ve", ""))
                      if x != truoc), "")
            if not c:
                # Câu không còn hình nào khớp. GIỮ NGUYÊN hình trùng thay vì mượn một hình
                # của kênh: lặp một hình ĐÚNG thì chỉ nhàm, còn thay bằng một hình SAI thì
                # khung nói một đằng lời nói một nẻo — lỗi nặng hơn hẳn, và đúng thứ tự ưu
                # tiên mà docstring của hàm này vẫn luôn khai.
                c = b
            b = c
            n["bt"] = b
        truoc = b
    return nhip


def _moc_khac(cac, so):
    """Mốc so sánh phải KHÁC mục đang nói tới.  (3/9/2026)

    `chia_doi` đặt mục của chương cạnh một mốc quen thuộc để người xem có cảm giác về con số.
    Mốc ấy ghi cứng trong bộ sinh — và bảng dữ liệu của chính kênh ấy CŨNG chứa mốc đó. Nên khi
    bộ lịch phát trúng chương *"a normal conversation"*, nhịp so sánh ra:

        NORMAL TALKING  60 dB   |   A NORMAL CONVERSATION  60 dB

    Hai vế bằng nhau thì nhịp so sánh không so gì cả — nhưng nó vẫn dựng, vẫn đúng cỡ, vẫn có
    lời đọc. Đo trên 18 kênh × 6 tập: 2/108 nhịp `chia_doi` rơi vào trạng thái này. Hiếm, và
    khi xảy ra thì hỏng trọn một nhịp giữa video.

    Nhận `cac` là danh sách mốc xếp theo thứ tự ưu tiên, trả mốc đầu tiên có giá trị khác `so`.
    """
    for m in cac:
        if str(m.get("so", "")).strip() != str(so or "").strip():
            return m
    return cac[-1]


# Đầu ngữ ĐO LƯỜNG: khi cụm bắt đầu bằng một trong những từ này rồi tới "of", chủ thể nằm SAU
# giới từ, không nằm trước. Xem chú thích trong `_danh_tu`.
_DAU_NGU = ("odds", "chance", "chances", "risk", "cost", "price", "number", "amount",
            "value", "share", "rate", "level", "size", "weight", "speed", "length",
            "height", "surface", "depth", "total")

_GIOI = ("at", "of", "in", "on", "from", "with", "for", "by", "to", "up", "over", "near")


TOC_M = 7.0e-5          # bề ngang sợi tóc người, mét — mốc nhỏ nhất người ta còn NHÌN THẤY


def _be(m: float) -> str:
    """Quy một chiều dài (mét) sang cách nói người Mỹ CẢM ĐƯỢC.  (4/9/2026)

    Trên 1/1000 inch thì nói bằng inch. Nhỏ hơn thì inch cũng vô nghĩa, nên nói bằng SỐ LẦN so
    với bề ngang SỢI TÓC — thứ nhỏ nhất mắt thường còn thấy, nên nó là mốc duy nhất người xem
    có sẵn trong đầu. `5e-04 m` không gợi ra gì; "1/70 sợi tóc" thì gợi ra ngay.
    """
    if m <= 0:
        return ""
    inch = m / 0.0254
    if inch >= 1:
        return f"{inch:,.0f} in"
    if inch >= 0.01:
        return f"{inch:.2f} in"
    lan = TOC_M / m
    if lan < 1:
        return f"{1/lan:,.0f} hairs wide"
    if lan < 2:
        return "about a hair wide"
    return f"1/{lan:,.0f} of a hair"


def _bo_so_thu_tu(s: str) -> str:
    import re as _re
    return _re.sub(r"^\s*\d+[.)]\s*", "", str(s or "").strip())


def _cat_khung(tieu: list[str]) -> list[str]:
    """Bỏ phần KHUNG dùng chung của các tiêu đề chương, giữ phần khác nhau."""
    ds = [_bo_so_thu_tu(t).split() for t in tieu if _bo_so_thu_tu(t)]
    if len(ds) < 3:
        return [" ".join(x) for x in ds]

    def _chung(lay):
        n = 0
        while n < min(len(x) for x in ds) - 1:
            if len({lay(x, n).lower() for x in ds}) != 1:
                break
            n += 1
        return n

    dau = _chung(lambda x, n: x[n])
    cuoi = _chung(lambda x, n: x[-1 - n])
    return [" ".join(x[dau: len(x) - cuoi] or x[dau:] or x) for x in ds]


def _nhan_chuong(tieu: list[str]) -> list[str]:
    """Nhãn ngắn cho từng chương — dùng cho cột biểu đồ tổng hợp và thẻ liệt kê.

    Vì sao không chỉ gọi `_danh_tu`  (4/9/2026)
    ────────────────────────────────────────────
    §15.21 đã chữa một lần cho ODDS và REAL COST bằng danh sách `_DAU_NGU` chép tay. Đo
    lại cả 18 kênh thì bốn kênh vẫn thoái hoá, và tệ hơn hẳn mức ấy:

        HOW LONG    10 chương -> nhãn `Walking` ×10      YEARS OF  -> `Years` ×10
        DAY IN LIFE 10 chương -> nhãn `day`     ×10      WHERE GOES-> `goes`  ×8

    Tức biểu đồ tổng hợp — nhịp bán cả bản dài — có mười cột mang **một chữ**. Thêm bốn
    đầu ngữ nữa vào `_DAU_NGU` chỉ hoãn lỗi tới kênh thứ mười chín (§13.9: nhận ra quy
    luật sinh ra ngoại lệ, đừng liệt kê chúng).

    Quy luật ấy đo được, không cần đoán ngữ pháp: mỗi kênh có một KHUNG CÂU cố định
    (*"A day in the life of…"*, *"Where your … goes"*), và thứ phân biệt các chương là
    đúng phần KHÁC NHAU giữa chúng. Cắt phần chung ở hai đầu là xong.

    Nhưng cắt cho MỌI kênh thì sai chiều — đo được ODDS `flight -> cancelled`,
    `parachute -> hole`, vì cắt khung lấy mất chữ `of` mà `_DAU_NGU` cần. Nên chỉ cắt khi
    nhãn hiện tại THOÁI HOÁ (một chữ dùng cho quá nửa số chương) **và** cắt xong thật sự
    ra nhiều nhãn riêng hơn. Đo trên 18 kênh: bật cho 4 kênh, tắt cho 14 — và cả bốn đều
    đọc tay thấy khá lên rõ (§13.23: đo bằng kết quả cuối, không bằng số ca bắt được).
    """
    goc = [_nhan(_danh_tu(_bo_so_thu_tu(t))) for t in tieu]
    if len(goc) < 3 or len(set(goc)) * 2 >= len(goc):
        return goc
    moi = [_nhan(_danh_tu(x)) for x in _cat_khung(tieu)]
    return moi if len(set(moi)) > len(set(goc)) else goc


# ══════════════════════════════════════════════════════════════════════════════════════════
# XEN KẼ ẢNH CF VỚI CẢNH VẼ BẰNG CODE                                        (4/9/2026)
# ══════════════════════════════════════════════════════════════════════════════════════════
# ĐO ĐƯỢC TRƯỚC KHI SỬA: 18 kênh, tập 0, short + long = 1.640 nhịp, trong đó **999 nhịp
# (60%) đặt một ảnh Cloudflare**. Riêng khuôn `canh` là 586/586 — một trăm phần trăm. Một
# tập HOW LONG tiêu **134 ảnh**; 18 kênh một vòng là 2.412 ảnh. §16.5 đã đo hồ CF cạn sạch
# ở 14.900 ảnh. Nên ở mức "vài nghìn video mỗi ngày" thì đây là một BỨC TƯỜNG, không phải
# một nút thắt nới ra được — và không lời khuyên tối ưu nào đổi được điều đó.
#
# HAI CÂU HỎI, VÀ CHỈ CÂU THỨ HAI MỚI DẪN TỚI LỜI GIẢI
#   sai : "làm sao gọi CF rẻ hơn?"      -> tiết kiệm vài chục phần trăm, tường vẫn ở đó
#   đúng: "nhịp nào KHÔNG CẦN ảnh CF?"  -> đo được, và câu trả lời là phần lớn
#
# HAI LOẠI NHỊP KHÔNG CẦN ẢNH CF
#
#   1. NHỊP CÓ ĐỒ HOẠ PHỦ KHUNG (`so_lieu` · `dem` · `nhom` · `kinh_lup`) — 413 nhịp.
#      Ở những nhịp này thứ mang nghĩa là con số, lưới biểu tượng, vòng kính lúp; nền chỉ
#      là BỐI CẢNH. Trả tiền một ảnh AI để rồi đè 70% diện tích nó bằng một thẻ số là mua
#      thứ không ai nhìn. Và có bằng chứng trực tiếp: cổng `kiem_chelap` sinh ra chính vì
#      chữ trắng đè lên ảnh sáng ở đúng khuôn `so_lieu`.
#
#   2. CỨ BA NHỊP `canh` THÌ MỘT nhịp vẽ bằng code — 195 nhịp.
#      Đây KHÔNG phải mẹo hạ hạn mức. Bộ luật nối cảnh của chính bộ này (§12.11) nói cảnh
#      sau kế thừa cảnh trước và mệnh đề song song thì khung hình song song; một nhịp
#      "đặt lại bối cảnh" xen giữa các nhịp tả chủ thể là NHỊP DỰNG PHIM, và nó có tác
#      dụng ngay cả khi hạn mức CF vô hạn.
#
# CÒN LẠI THÌ CF VẼ — đúng chỗ nó hơn hẳn: một chủ thể CỤ THỂ đang làm một việc CỤ THỂ.
# Mười nơi chốn trong `CanhVe.tsx` vẽ được NƠI CHỐN, không vẽ được "một người thợ xây hải
# đăng năm 1890". Ranh giới đặt đúng ở đó.
#
# KẾT QUẢ ĐO LẠI: 391/1.640 = **24%** (trước: 60%). Một tập HOW LONG còn ~33 ảnh.
#
# VÀ NÓ PHẢI TẤT ĐỊNH: `hat` + chỉ số nhịp, không dùng `random`, để dựng lại một tập cũ ra
# đúng cảnh cũ. Cùng lý do §13.13 cấm `hash()` của Python ở chỗ này.

# Mỗi kênh dùng 3–4 nơi chốn HỢP THẾ GIỚI của nó, không dùng cả mười.
# Đây là cùng cơ chế `mo_cam` của bộ Kling (§14.2): bộ lịch không được phát cho một kênh
# thứ mà thế giới ấy không diễn được. Kênh nói về hoá đơn khách sạn thì không có sa mạc;
# kênh sinh tồn thì không có văn phòng.
# ══ NƠI CHỐN CỦA TỪNG KÊNH — NĂM, KHÔNG PHẢI BA  (nới 4/9/2026) ════════════════════════════
# Đo: mỗi kênh khai ĐÚNG BA nơi và dùng trung bình 2,9 — tức phép xoay chạy tốt, trần nằm ở
# BẢNG. Trong khi `CanhVe` vẽ được MƯỜI cảnh: kho · nha_may · van_phong · pho · duong · dong
# · bien · bang · sa_mac · troi. Ba trên mười là bỏ phí bảy cảnh đã dựng xong.
#
# Đây đúng dạng §15.15: *cơ chế chạy đúng, hồ quá nhỏ so với số lần rút* — không có gì hỏng
# để sửa, chỉ có một con số cần lớn hơn. Năm nơi cho gần gấp đôi độ đa dạng bối cảnh trong
# MỘT kênh mà không phải vẽ thêm cảnh nào.
#
# RÀNG BUỘC KHÔNG ĐƯỢC PHÁ: chỉ thêm nơi mà THẾ GIỚI kênh ấy diễn được. `survive` (băng, sa
# mạc, đồng hoang) không thể nhận `van_phong`; `smallest` không thể nhận `nha_may`. §14.2 đã
# trả giá đúng chuyện này ở bộ thiên nhiên — bộ lịch phát cho DOG PARK một nhịp "khói bốc lên"
# trong khi công viên chó ngoài trời không có gì bốc khói được, và không cổng nào bắt vì cổng
# đo tay nghề chứ không đo vật lý của thế giới.
#
# Nên mỗi kênh nới theo ĐÚNG chất của nó, không nới đều:
#   · kênh đời thường/tiền bạc  -> thêm nơi người ta thật sự đi qua trong ngày
#   · kênh khoảng cách/tốc độ   -> thêm địa hình rộng
#   · kênh cực đoan (nhiệt, sinh tồn) -> chỉ thêm nơi cực đoan
NOI_KENH: dict[str, tuple[str, ...]] = {
    # khoảng cách · đi bộ: mọi địa hình đi qua được
    "howlong":    ("duong", "dong", "pho", "sa_mac", "bien"),
    # so sánh KÍCH THƯỚC: cần nơi có vật to để đối chiếu
    "howbig":     ("bien", "troi", "pho", "nha_may", "sa_mac"),
    # tiền bạc đời thường: nơi người ta tiêu tiền và kiếm tiền
    "realcost":   ("van_phong", "pho", "nha_may", "kho", "duong"),
    # thang con số: nơi có SỐ LƯỢNG lớn nhìn thấy được
    "howmuch":    ("kho", "van_phong", "nha_may", "pho", "troi"),
    # "nếu ai cũng…": nơi đông người
    "whatif":     ("pho", "dong", "duong", "bien", "van_phong"),
    # sinh tồn: CHỈ nơi khắc nghiệt — không thêm nơi có mái che
    "survive":    ("bang", "sa_mac", "dong", "bien", "troi"),
    # một ngày của nghề xưa: nơi làm việc
    "dayinlife":  ("kho", "nha_may", "van_phong", "dong", "pho"),
    # đồ vật đi đâu: theo đường vận chuyển
    "wheregoes":  ("kho", "nha_may", "bien", "duong", "pho"),
    # luật về tài sản: nơi có ranh giới sở hữu
    "therules":   ("van_phong", "pho", "duong", "dong", "kho"),
    # tốc độ: nơi có thứ di chuyển nhanh
    "speedof":    ("duong", "troi", "bien", "pho", "sa_mac"),
    # xác suất: nơi đời thường, việc thường
    "odds":       ("van_phong", "pho", "dong", "duong", "kho"),
    # bên trong một cái giá: chuỗi cung ứng
    "hiddenfee":  ("van_phong", "pho", "kho", "nha_may", "duong"),
    # số năm của đời người: nơi người ta sống qua
    "yearsof":    ("van_phong", "pho", "dong", "duong", "kho"),
    # độ ồn: nơi ồn và nơi tĩnh, cần cả hai để so
    "howloud":    ("pho", "nha_may", "kho", "duong", "dong"),
    # khối lượng: nơi có vật nặng
    "whatweighs": ("kho", "bien", "nha_may", "duong", "pho"),
    # ngay lúc này có bao nhiêu người: nơi đông và nơi vắng
    "rightnow":   ("pho", "duong", "troi", "dong", "van_phong"),
    # nhiệt độ: CHỈ nơi cực đoan + nơi có nguồn nhiệt
    "howhot":     ("sa_mac", "nha_may", "bang", "troi", "bien"),
    # thang cực nhỏ: nơi trừu tượng, không đồ đạc lớn tranh chỗ
    "smallest":   ("troi", "bien", "van_phong", "dong", "bang"),
}

# Khuôn có đồ hoạ phủ khung — nền chỉ là bối cảnh, không cần ảnh AI.
#
# Chia làm HAI nhóm, và ranh giới là *"khung này là một CẢNH hay một SƠ ĐỒ?"*:
#   · `so_lieu` · `nhom`  -> một cảnh có con số đặt lên. Nơi chốn giúp câu chuyện.
#   · `dem` · `kinh_lup`  -> một SƠ ĐỒ. Lưới biểu tượng đếm hoặc vòng kính lúp đã chiếm
#     gần hết khung, và một nơi chốn phía sau chỉ làm nhiễu — soi khung DAY IN LIFE thấy
#     sáu mặt trời xếp lưới đè lên rèm văn phòng, hai lớp cùng đòi mắt người xem.
# Nhóm sau vẫn KHÔNG gọi CF (vẫn bỏ `ve`), nhưng nhận nền phẳng `NenPhong` thay vì cảnh.
KHUON_PHU = ("so_lieu", "nhom")
KHUON_SO_DO = ("dem", "kinh_lup")

# ── KHUÔN TỰ VẼ ĐỒ HOẠ THÌ KHÔNG NHẬN *CẢNH VẼ CODE*  (5/9/2026) ────────────────────────
# Anh soi khung THE RULES nhịp 5: một khối số liệu và một nhân vật đứng trước **cả một cảnh
# kho đầy tủ**. Ba bức tranh trong một khung.
#
# `so_lieu` nằm trong `KHUON_PHU` nên nó luôn được cấp nền — và điều đó ĐÚNG cho nền ẢNH:
# ảnh CF là bề mặt mềm, `SoLieu` đã có sẵn dải chuyển tối phủ lên (`tren_anh`) nên con số
# vẫn đọc được và bức ảnh vẫn làm nền. Nhưng `canh_ve` là bề mặt **nét mực đen, mảng màu
# đặc** — không có dải nào phủ lên nó, và mọi vật trong cảnh đều tranh chỗ với khối số.
#
# Đúng §12.5 lần nữa: *"khuôn này được cấp nền"* là một luật đúng ở ngữ cảnh nền ảnh, và sai
# khi đem sang ngữ cảnh nền vẽ. Hai loại nền không thay thế nhau được chỉ vì cùng nằm phía
# sau.
#
# Phản xạ đầu của em là DÌM cảnh xuống sau chủ thể bằng một cái đĩa mờ. Đó là vá triệu
# chứng: nó không bỏ bức tranh thứ ba đi, nó chỉ làm mờ bức ấy — và ảnh tham chiếu anh gửi
# (cậu bé + chồng báo) đẹp vì **một khung một bức tranh**, không phải vì nó dìm khéo.
#
# Nên: khuôn nào tự vẽ đồ hoạ của nó thì nền phía sau phải là mặt phẳng trung tính.
# `the_chu` KHÔNG có trong danh sách, và đó là một quyết định, không phải sót:
# anh soi khung "The word changes by three letters" và nói *"đừng làm kiểu chữ trên nền
# không này rất xấu và chán"*. Đúng — nhưng gốc không nằm ở thẻ chữ, nó nằm ở CÁI PHÍA SAU.
# `TheChu` phủ một tấm màu 0,80 chứ không phải 1,00, và chú thích tại chỗ ghi rõ vì sao:
# *"chỉ cần hạ độ đục là cảnh hiện mờ trở lại, khung không còn rỗng"*. Lý do ấy đúng — với
# điều kiện có một cảnh để hiện. Đưa `the_chu` vào danh sách này là cắt mất đúng cái cảnh
# ấy, nên tấm màu phủ lên một bức tường trơn và đọc ra mảng màu đặc. §12.5 một lần nữa:
# tấm phủ mờ là giải pháp đúng cho ngữ cảnh có cảnh, và vô nghĩa ở ngữ cảnh không có.
# Thẻ chữ khác các khuôn còn lại ở một chỗ quyết định: nó KHÔNG vẽ sơ đồ, nên nó không
# tranh chỗ với cảnh — và nó đã mang sẵn tấm phủ làm nền đọc chữ.
KHUON_TU_VE = ("so_lieu", "dem", "kinh_lup", "chart", "truc", "chia_doi")

# Cứ N nhịp `canh` thì một nhịp vẽ bằng code. 3 cho ra 24% CF; đổi số này là đổi thẳng
# tỉ lệ, nên nó là NÚT VẶN duy nhất của chính sách — đừng rải điều kiện ra nhiều chỗ.
CANH_MOI = 3

# ── CHỦ THỂ × NƠI CHỐN: HỎI CẶP, KHÔNG CHỈ HỎI TỪNG TRỤC  (4/9/2026) ═══════════════════════
# Bộ lịch chọn NƠI CHỐN theo kênh (`NOI_KENH`) và CHỦ THỂ theo nội dung câu (`bt`) — hai trục
# độc lập, không trục nào hỏi trục kia. Soi 15 nhịp vẽ code đã dựng thì ra hai cặp vô nghĩa:
#
#     duong × giuong    một cái giường đặt giữa lòng đường
#     pho   × trai_dat  quả Địa Cầu đứng trên vỉa hè
#
# 2/15 — ít, nhưng khi xảy ra thì HỎNG CẢ KHUNG, và nó không tốn một lượt gọi AI nào để chữa
# nên nó thuộc nấc `don()`: máy sửa được thì máy sửa (§13.23).
#
# KHÔNG liệt kê cặp cấm — danh sách cặp là danh sách vô hạn (§13.9). Hai cặp trên sinh ra từ
# đúng một quy luật: **quy mô**. Vật thiên văn không đứng trên mặt sàn ở cỡ người; đồ đạc
# trong nhà không nằm ngoài trời. Hai lớp đóng, không phải một bảng mở.
_BT_THIEN_VAN = {"trai_dat", "mat_trang", "mat_troi"}
_BT_TRONG_NHA = {"giuong", "dan_piano"}
_NOI_TRONG_NHA = {"kho", "van_phong", "nha_may"}


def _hop_noi(bt: str, noi: str) -> bool:
    """Chủ thể `bt` có đứng được ở nơi chốn `noi` không."""
    if bt in _BT_THIEN_VAN:
        return False                      # không mặt sàn nào hợp — để nền phẳng lo
    if bt in _BT_TRONG_NHA:
        return noi in _NOI_TRONG_NHA
    return True


# ══ ĐẠO CỤ NÓI RA CON SỐ  (4/9/2026) ═══════════════════════════════════════════════════════
# Anh: *"vẫn không toát lên được ý truyền đạt."* So với mấy ảnh anh gửi thì đây là khác biệt
# sâu nhất, và nó không nằm ở nét vẽ:
#
#     ảnh mẫu   : một người ngồi bàn, CHỒNG GIẤY cao, ĐỒNG HỒ TƯỜNG chỉ 5:01
#     bản của ta: "a night-shift nurse walking away from camera, back turned"
#
# Ảnh mẫu nói ra ý mà không cần lời: cái đồng hồ chỉ 5 giờ chiều cạnh chồng giấy chưa vơi
# CHÍNH LÀ mệnh đề "vẫn còn ngồi đây". Bản của ta chỉ có một tư thế, nên lời phải gánh hết —
# và người xem không đọc phụ đề trong nửa giây đầu.
#
# Cơ chế: mỗi nhịp cảnh mang một ĐẠO CỤ đo được đại lượng đang nói. Con số đã nằm sẵn trong
# nhịp (`so`/`don`) — chưa ai đưa nó vào câu cảnh.
#
# Ánh xạ theo ĐẠI LƯỢNG, không theo từng chuỗi đơn vị: `don` có ~30 dạng chữ ("dollars a
# year", "dollars in 30 years"…) nhưng chỉ quy về chừng mười đại lượng. Bắt theo đại lượng
# thì đơn vị viết kiểu gì cũng trúng, và thêm kênh mới không phải thêm dòng.
DAO_CU: tuple = (
    # Mỗi đại lượng vài ĐẠO CỤ khác nhau, xoay theo chỉ số nhịp. Một tập bốn cảnh mà cả bốn
    # cùng "a roadside distance sign" thì đạo cụ lại thành một kiểu đơn điệu mới — đúng cái
    # bệnh vừa chữa ở tầng khuôn hình, chỉ ở tầng đồ vật.
    (("century", "centuries", "year", "decade"),
     ("a wall calendar with most pages torn off", "a stack of dated ledgers",
      "a tree stump with its growth rings showing")),
    (("day",),
     ("a row of torn-off calendar pages pinned up", "a line of chalk tally marks on a wall")),
    (("hour", "time to arrive"),
     ("a round wall clock", "a wristwatch held up close", "an hourglass on a shelf")),
    (("second", "minute"),
     ("a stopwatch held in one hand", "a kitchen timer mid-count")),
    (("mph", "speed"),
     ("a car speedometer dial", "a roadside speed display board")),
    (("mile", "feet", "foot", "distance"),
     ("a roadside distance sign", "a folding tape measure pulled out",
      "a worn pair of boots beside a trail marker")),
    (("decibel", "loud", "energy of"),
     ("a handheld sound level meter", "a pair of ear defenders on a hook")),
    (("pound", "heavier", "weigh"),
     ("a floor scale with a round dial", "a hanging luggage scale")),
    (("fahrenheit", "degree"),
     ("a wall thermometer", "a car dashboard temperature readout")),
    (("dollar", "price", "cost", "fee"),
     ("a long paper receipt curling off a till", "a stack of banknotes under a clip",
      "a bank statement pinned to a fridge")),
    (("calorie",),
     ("a printed label on a food packet", "a lunch tray with the meal laid out")),
    (("people", "population"),
     ("a dense crowd of small identical figures", "a full stadium seen from the stands")),
)


def _dao_cu(don: str, i: int = 0) -> str:
    """Đạo cụ đo được đại lượng của `don`. Không khớp thì trả rỗng — thà không có đạo cụ còn
    hơn có một đạo cụ nói sai đại lượng (tỉ lệ, phần trăm, "1 in N" không có vật đo nào)."""
    d = str(don or "").lower()
    # ── ĐẠI LƯỢNG NẰM Ở TỪ ĐẦU  (đo lại sau khi thử) ──────────────────────────────────
    # Quét chuỗi con trên CẢ câu cho ra hai ánh xạ sai: "dollars in 30 years" trúng "year"
    # -> ra tấm lịch (nó nói về TIỀN), và "hours a day" trúng "day" -> cũng ra lịch (nó nói
    # về GIỜ). Trong mọi dạng `don` của dự án, đại lượng luôn là TỪ ĐẦU và phần sau chỉ là
    # bổ ngữ ("… a year", "… in 30 years", "… a day"). Nên soi từ đầu trước, hết mới soi cả
    # câu — không thêm ngoại lệ nào, chỉ đọc đúng chỗ.
    dau = d.split()[0] if d.split() else ""
    for tu, vat in DAO_CU:
        if any(t in dau for t in tu):
            return vat[i % len(vat)]
    for tu, vat in DAO_CU:
        if any(t in d for t in tu):
            return vat[i % len(vat)]
    return ""


# Số NGẮN thì cho mô hình vẽ lên đạo cụ; số dài thì tuyệt đối không.
# §12.7 đã đo: chuỗi <= 4 ký tự không dấu đúng 5/6 lần, còn "238,900" sai 2/2 — ra "23 8,900"
# và "238.900". Người xem đọc ra "máy làm" trong nửa giây.
_SO_NGAN = re.compile(r"^[0-9]{1,4}$")


def _gan_dao_cu(nhip: list) -> None:
    """Gắn đạo cụ vào TIỀN CẢNH của mỗi nhịp cảnh có con số.

    Đơn vị lấy của chính nhịp, không có thì lấy của nhịp số liệu gần nhất phía trước — đó là
    con số mà cảnh này đang minh hoạ."""
    don_gan, so_gan, _k = "", "", 0
    for n in nhip:
        if n.get("don"):
            don_gan, so_gan = str(n["don"]), str(n.get("so") or "")
        ve = n.get("ve")
        if not ve or n.get("canh_ve"):
            continue
        vat = _dao_cu(n.get("don") or don_gan, _k)
        _k += 1
        if not vat:
            continue
        so = str(n.get("so") or so_gan).strip()
        doc = f" reading {so}" if _SO_NGAN.match(so) else ""
        # Chèn vào TRƯỚC câu máy quay (câu cuối của `_ve`) để nó nằm ở tiền cảnh, không bị
        # đẩy ra sau chỗ cắt.
        n["ve"] = ve + f", in the foreground {vat}{doc}"


_KHO_TU = None


def _kho_hinh_nhap():
    """Đọc chỉ mục kho hình từ chính tệp engine dùng — MỘT nguồn sự thật.

    Không chép danh sách sang Python: `KhoSVG.ts` do `tai_svg.py` sinh ra và sẽ đổi mỗi lần
    chạy lại. Giữ một bản sao ở đây là dựng nguồn thứ hai, và nó sẽ lệch đúng vào lúc không
    ai nhìn (§13.5 — bốn nguồn sự thật cho một danh sách kênh, đã trả giá).
    """
    global _KHO_TU
    if _KHO_TU is None:
        f = os.path.join(os.path.dirname(__file__), "..", "engine-remotion", "src", "gt", "KhoSVG.ts")
        try:
            t = open(f, encoding="utf-8").read()
            i = t.index("KHO_SVG: HinhSVG[] = ") + len("KHO_SVG: HinhSVG[] = ")
            j = t.index(";\nexport const CHI_SO", i)
            _KHO_TU = [(h["ten"], set(h["tu"])) for h in json.loads(t[i:j])]
        except Exception:
            _KHO_TU = []
    return _KHO_TU


_BO_TU = {"the", "and", "for", "you", "your", "that", "this", "with", "from", "are", "was",
          "not", "but", "all", "one", "out", "get", "got", "its", "has", "had", "who", "why",
          "how", "what", "when", "where", "them", "they", "does", "did", "will", "can"}


def _rai_hinh_nhap(nhip: list, ma: str, idx: int) -> None:
    """Chọn cho mỗi nhịp CẢNH một bức tranh khớp NGHĨA của câu đang nói.

    ── VÌ SAO ĐỔI CÁCH LÀM  (5/9/2026) ────────────────────────────────────────────────────
    Anh soi ba vòng liền: *"vẫn xấu lơ lửng và lặp đi lặp lại quá nhiều, đổi cách làm mới"*.
    Anh đúng ở cả ba, và cả ba chảy ra từ MỘT chỗ: em đang **dán một bức tranh vào trong một
    bức tranh khác**.

      · LƠ LỬNG — hình unDraw mang theo mặt đất của chính nó ở ~0,55·H, sàn của mình ở
        0,72·H. Nhân vật đứng trên đất của bức tranh, cái bóng của mình nằm tách phía dưới.
        Không hằng số nào chữa được, vì mỗi hình có một mặt đất ở một độ cao khác nhau.
      · LẶP — bảng chép tay ánh xạ BIỂU TƯỢNG -> HÌNH, mà biểu tượng chỉ có 23 giá trị và
        `nguoi` chiếm 54% số nhịp. Hai hình cho hơn một nửa số khung.
      · SAI NGHĨA — cùng một người hiện cho mọi câu, vì `nguoi` là vai trung tính.

    Nên: ánh xạ CÂU -> HÌNH (1.362 đích thay vì 19), và hình nhập chiếm TRỌN khung — không
    còn sàn thứ hai để mà lệch. Một khung một bức tranh, đúng luật đã rút sáng nay.

    Điểm khớp = số từ chung giữa lời và tên hình, chia cho căn bậc hai số từ của tên: tên dài
    dễ trúng một từ vu vơ, không chia thì `a-better-world` thắng mọi câu có chữ `world`.
    """
    kho = _kho_hinh_nhap()
    if not kho:
        return
    dung = set()
    for i, n in enumerate(nhip):
        if (n.get("khuon") or "canh") not in ("canh", "nhom"):
            continue
        tu = {w for w in re.findall(r"[a-z]{3,}", (n.get("loi") or "").lower())
              if w not in _BO_TU}
        if not tu:
            continue
        tot, diem = None, 0.0
        for ten, tt in kho:
            c = len(tu & tt)
            if not c:
                continue
            d = c / (len(tt) ** 0.5)
            # KHÔNG dùng lại hình đã dùng trong CHÍNH tập này. Kho 300 hình mà một tập chỉ
            # 9–16 nhịp, nên ràng buộc này gần như không bao giờ ép phải lấy hình kém hơn —
            # mà nó chặn đứng đúng cái lặp anh chê.
            if ten in dung:
                d *= 0.25
            if d > diem:
                tot, diem = ten, d
        # Sàn: dưới mức này thì hình khớp quá lỏng, hiện lên còn hại hơn không hiện —
        # một bức tranh sai nghĩa chiếm trọn khung là chỗ người xem đọc ra "máy làm".
        if tot and diem >= 0.30:
            n["hinh_nhap"] = tot
            dung.add(tot)


def _rai_canh_ve(nhip: list, ma: str, hat: int) -> None:
    """Gán `canh_ve` (tên nơi chốn) cho nhịp sẽ vẽ bằng code, và bỏ `ve` của nhịp ấy.

    Bỏ `ve` là phần quan trọng: `nen_gt.sinh_tap` quyết định gọi CF bằng chính trường ấy,
    nên để lại `ve` là vẫn tốn một lượt gọi rồi vứt kết quả đi — tức "sửa" mà không tiết
    kiệm gì, và không có gì báo.
    """
    noi = NOI_KENH.get(ma) or ("dong", "pho", "van_phong")
    dem_canh = 0
    for i, n in enumerate(nhip):
        kh = n.get("khuon") or ""
        if kh in KHUON_SO_DO:
            # Sơ đồ: bỏ ảnh CF, KHÔNG gán nơi chốn -> engine rơi về nền phẳng `NenPhong`.
            n.pop("ve", None)
            continue
        if kh in KHUON_TU_VE:
            # Tự vẽ đồ hoạ: GIỮ `ve` (ảnh CF là bề mặt mềm, đã có dải chuyển tối phủ lên)
            # nhưng KHÔNG bao giờ gán `canh_ve`. Hai loại nền không thay thế nhau được —
            # xem chú thích ở `KHUON_TU_VE`. Bỏ `ve` ở đây là cắt mất đúng cái nền ĐẸP để
            # tránh cái nền XẤU, tức chữa bằng cách bỏ cả hai.
            continue
        lay = False
        if kh in KHUON_PHU:
            lay = True
        elif kh == "the_chu":
            # Thẻ chữ LUÔN có cảnh phía sau — xem chú thích ở `KHUON_TU_VE`. Không đi qua
            # nhánh `CANH_MOI` (cấp cho một phần ba nhịp `canh`) vì thẻ chữ không cạnh
            # tranh hạn mức CF: nó không bao giờ đặt ảnh, nên cảnh vẽ code là lớp DUY NHẤT
            # nó có. Cấp một phần ba tức để hai phần ba thẻ chữ nằm trên tường trơn — đúng
            # cái anh vừa chê.
            lay = True
        elif kh == "canh":
            dem_canh += 1
            lay = (dem_canh % CANH_MOI == 0)
        if not lay:
            continue
        # Lọc nơi chốn theo chủ thể của CHÍNH nhịp này, rồi mới xoay. Xoay trước lọc sau là
        # lại rơi đúng bẫy §15.1 (cắt trước lọc sau) ở một hình dạng khác.
        _bt = str(n.get("bt") or "")
        # Thẻ chữ không có `bt`, nên phép lọc theo chủ thể không nói gì về nó — mọi nơi
        # chốn đều hợp. Không có dòng này thì `_hop` rỗng và thẻ chữ lại rơi về tường trơn,
        # tức bản sửa trên không có hiệu lực (§6: sửa một mắt, quên mắt kế bên).
        _hop = list(noi) if kh == "the_chu" else [x for x in noi if _hop_noi(_bt, x)]
        if not _hop:
            # KHÔNG có nơi nào hợp -> bỏ hẳn `canh_ve`, để nhịp rơi về nền phẳng `NenPhong`.
            # Nền phẳng là một mặt sàn trung tính: nó không nói gì SAI về nội dung câu, còn
            # một nơi chốn sai thì nói. Và không quay về `noi` đầy đủ — quay về danh sách gốc
            # là vô hiệu hoá chính phép lọc vừa làm (§14.2).
            n.pop("ve", None)
            continue
        n["canh_ve"] = _hop[(hat + i) % len(_hop)]
        # ── HẠT RIÊNG CHO TỪNG NHỊP  (4/9/2026, sau khi SOI KHUNG) ──────────────────────
        # `CanhVe` sinh đường bao lởm chởm và vị trí vật từ một hạt. Bản đầu truyền `hat`
        # của TẬP, nên mọi nhịp `duong` trong một tập ra **đúng cùng một con đường** — và
        # một tập 16 nhịp có tới ba nhịp `duong`. Đó chính là lời anh chê từ đầu: *"cứ lặp
        # đi lặp lại cùng 1 motip hoài"*, chỉ là ở một tầng khác.
        #
        # Số đo đẹp che mất nó: mười nơi chốn được dùng đều, và "mười nơi dùng đều" KHÔNG
        # phải thứ người xem cảm được — thứ họ cảm được là "hai cảnh trong một tập có
        # trông khác nhau không" (§14.9, đã trả giá đúng chỗ này ở bộ Kling).
        n["canh_hat"] = (hat + i * 7919) % 100000
        n.pop("ve", None)


def _danh_tu(s: str) -> str:
    """Danh từ chính của một cụm — dùng làm NHÃN cột và nhãn vế so sánh.  (3/9/2026)

    Bản đầu lấy `s.split()[-1]`. Soi lưới HOW LOUD: cột của chương *"How loud is a whisper at
    arm's length"* mang nhãn **`length`**, và cột *"a normal conversation"* bị `_nhan` cắt cụt
    thành **`conversatio`**. Người xem đọc trục ra "length" thì không biết cột ấy nói về cái gì.

    Từ cuối chỉ đúng khi cụm không có bổ ngữ. Có giới từ thì phần mang nghĩa nằm TRƯỚC nó:
        "a whisper at arm's length" -> whisper        "a jet at takeoff" -> jet
        "a normal conversation"     -> conversation   "a hair dryer"     -> dryer
    """
    import re as _re
    t = _re.sub(r"^(a|an|the)\s+", "", str(s or "").strip(), flags=_re.I).split()
    for j, w in enumerate(t):
        if w.lower() in _GIOI and j > 0:
            # ── ĐẦU NGỮ CHUNG THÌ LẤY PHẦN SAU "OF"  (3/9/2026) ──────────────────────────
            # "The odds of rolling snake eyes" cắt ở "of" cho ra **`odds`**, và cả sáu chương
            # của kênh ODDS đều bắt đầu bằng "The odds of…" nên biểu đồ tổng hợp ra SÁU CỘT
            # cùng nhãn `odds`. Soi khung thấy ngay: một trục sáu nhãn giống hệt nhau.
            # Cùng lỗi ở REAL COST ("The real cost of…" -> `cost`).
            #
            # `odds` · `cost` · `chance` là ĐẦU NGỮ ĐO LƯỜNG, không phải chủ thể — chủ thể nằm
            # sau "of". Đây là chỗ luật "danh từ chính nằm TRƯỚC giới từ" không còn đúng, và
            # nhận ra được bằng chính danh sách đầu ngữ ấy.
            if t[:j] and t[j - 1].lower() in _DAU_NGU and w.lower() == "of":
                sau = [x for x in t[j + 1:]
                       if x.lower() not in ("a", "an", "the", "your", "my", "its", "their")]
                # Bỏ đuôi động từ (-ing/-ed) từ phải sang: "your flight being cancelled" ->
                # `flight`; "rolling snake eyes" giữ nguyên vì `eyes` không phải đuôi động từ.
                while len(sau) > 1 and _re.search(r"(ing|ed)$", sau[-1], _re.I):
                    sau = sau[:-1]
                if sau:
                    return " ".join(sau[-2:]) if len(" ".join(sau[-2:])) <= 15 else sau[-1]
            t = t[:j]
            break
    return t[-1] if t else str(s or "")


_HE = {"k": 1e3, "m": 1e6, "bn": 1e9, "b": 1e9, "tn": 1e12}


def _so_hook(hp: str):
    """Số thật trong một hook phụ, hoặc None nếu câu ấy không có đại lượng nào.

    Bản đầu chỉ lấy chữ số của TỪ ĐẦU TIÊN. Ba chỗ hỏng, cả ba chỉ thấy khi đọc dữ liệu thật:
      · `$227K OVER 30 YEARS` -> 227, còn chương khác `$1.2M` -> 1.2 — hai cột cạnh nhau lệch
        nhau một nghìn lần mà trục vẫn vẽ như thường
      · `-320°F` -> 320, mất dấu âm, nên chương lạnh nhất thành chương nóng nhất
      · `PROBABLY NOT` -> "" -> 0.0, một cột trống không ai biết là trống

    Trả None (không phải 0) khi không có số, để chỗ gọi phân biệt được *"giá trị bằng không"*
    với *"không có giá trị"* — hai thứ này lẫn vào nhau chính là gốc của bốn cột 0 ở trên.
    """
    import re as _re
    t = str(hp or "")
    # `1 IN 36` — đại lượng là 36, không phải 1. Kênh ODDS viết mọi hook phụ theo khuôn ấy, nên
    # cạo từ trái sang cho ra bốn cột đều bằng 1: một biểu đồ phẳng lì mà không có lỗi nào báo.
    _o = _re.search(r"\b1\s+in\s+([\d][\d,\.]*)", t, _re.I)
    if _o:
        t = _o.group(1)
    # `(?![A-Za-z])` — hệ số phải đứng ở BIÊN TỪ. Thiếu nó thì chữ M của `11 MONTHS` thành hệ
    # số triệu và cột ấy cao gấp một triệu lần các cột kia. Đúng họ lỗi "một danh sách chuỗi con
    # không bắt được ngôn ngữ" (13.20).
    #
    # Dấu chặn phải nằm TRONG nhóm hệ số, không nằm sau cả cụm: đặt sau cụm thì `700,000x` bị
    # regex lùi lại thành `700,00` để né chữ `x`, và trả về 70.000 — sai một bậc mười mà vẫn là
    # một con số trông hợp lý. Đây là kiểu hỏng tệ nhất của regex: nó không thất bại, nó lùi.
    m = _re.search(r"(-?)\s*\$?\s*([\d][\d,\.]*)\s*(?:([kK]|[mM]|[bB][nN]?|[tT][nN])(?![A-Za-z]))?", t)
    if not m:
        return None
    try:
        v = float(m.group(2).replace(",", ""))
    except ValueError:
        return None
    v *= _HE.get((m.group(3) or "").lower(), 1.0)
    return -v if m.group(1) else v


def _bt_canh_ds(loi: str, ve: str = "") -> list:
    """MỌI biểu tượng khớp câu, xếp hạng — khớp trong LỜI trước, trong câu tả cảnh sau.

    ── VÌ SAO CẦN DANH SÁCH  (4/9/2026) ────────────────────────────────────────────────
    `_bt_canh` trả đúng một hình. Khi hai nhịp liền nhau ra cùng hình, `_rai_hinh` đổi nhịp
    sau sang **một hình bất kỳ trong bộ của kênh** — chọn thuần cho đa dạng, không xét
    nghĩa. Soi khung: câu *"Up while it is still dark"* (cảnh: người gác đêm, áo choàng
    dài, đèn lồng) nhận một NGÔI NHÀ; *"Now just wait"* (cảnh: lọ thuỷ tinh đựng xu) nhận
    một MẶT TRỜI. Đó đúng là lời anh phê *"chưa thể hiện được cái nói"*.
    Chú thích của chính `_rai_hinh` viết *"hình đúng nghĩa quan trọng hơn hình đa dạng"* —
    rồi làm ngược lại ở đúng nhánh trùng. Có danh sách thì nhịp sau lấy được hình khớp
    THỨ HAI của chính câu ấy: vừa khác hình trước, vừa vẫn đúng nghĩa.

    ── VÌ SAO LỜI TRƯỚC, CẢNH SAU ──────────────────────────────────────────────────────
    `ve` tả trọn bối cảnh nên đầy danh từ của PHÔNG NỀN. Gộp hai nguồn vào một chuỗi thì
    hình được chọn theo cái đứng trong nền chứ không theo cái câu đang nói. Cùng bài học
    §15.3: đo một phép nối là đo một văn bản không ai viết ra.
    """
    ra = []
    for nguon in (str(loi or ""), str(ve or "")):
        t = f" {nguon} ".lower()
        for bt, tu in _BT_TU:
            if bt in ra:
                continue
            for w in tu:
                if f" {w} " in t or f" {w}s " in t or f" {w}." in t or f" {w}," in t:
                    ra.append(bt)
                    break
    return ra


def _bt_canh(loi: str, ve: str = "") -> str:
    """Biểu tượng cho một nhịp `canh` — ưu tiên khớp trong LỜI, rồi mới tới câu tả cảnh.

    Bản trước nối `loi` và `ve` thành MỘT chuỗi rồi quét. Nhưng `ve` tả trọn bối cảnh nên
    đầy danh từ của phông nền, và chúng thắng ngay khi bảng `_BT_TU` xếp chúng lên trước:
    câu *"Up while it is still dark."* với cảnh *"a night watchman … moving out of a small
    room"* nhận một NGÔI NHÀ, vì `ve` có chữ "room". Khung nói một đằng, lời nói một nẻo —
    đúng lời anh phê *"chưa thể hiện được cái nói"*.
    Xem `_bt_canh_ds`: quét hai nguồn RIÊNG, lời trước.
    """
    # ── ĐỒ VẬT CHỈ LẤY TỪ LỜI. CÂU TẢ CẢNH KHÔNG ĐƯỢC ĐƯA VÀO ĐỒ VẬT MỚI  (4/9/2026) ──────
    # Đo trên nhịp thật: câu *"Up while it is still dark."* khớp **không danh từ nào** trong
    # bảng, nên nó rơi xuống `ve` — và `ve` tả *"a night watchman … a narrow old town street
    # at night, shuttered houses"*. Chữ "house" của PHÔNG NỀN thắng, và khung hiện một ngôi
    # nhà cho một câu nói về bóng tối.
    #
    # Bốn ảnh anh gửi xử lý đúng ca này bằng NHÂN VẬT ĐANG DIỄN — người trở dậy trong tối,
    # tay cầm đèn lồng — chứ không bằng một đồ vật. Câu không có danh từ vẽ được thì thứ diễn
    # đạt nó là hành động của người, không phải một món đồ nhặt trong nền.
    #
    # Nên `ve` chỉ còn được dùng để CHỌN GIỮA các ứng viên (xem `_rai_hinh` nhánh trùng), chứ
    # không được đưa vào ứng viên đầu tiên. Đúng thứ tự ưu tiên mà đoạn dưới vẫn luôn khai:
    # *đồ vật phải khớp từ mới vẽ; NGƯỜI là mặc định an toàn.*
    ds = _bt_canh_ds(loi, "")
    if ds:
        return ds[0]
    # ── KHÔNG KHỚP TỪ NÀO -> VẼ NGƯỜI  (3/9/2026) ──────────────────────────────────────────
    # Bản đầu trả "" với lý do *"không biết ≠ đoán bừa"*. Lý do ấy đúng với ĐỒ VẬT: gắn một cái
    # ô tô vào câu nói về vũ trụ là nói một điều SAI, tệ hơn nền trống.
    #
    # Nhưng NGƯỜI thì khác hẳn về bản chất. Soi sáu ảnh tham chiếu anh gửi: **cả sáu đều có
    # người** — người ngồi cạnh lửa, người ở bàn làm việc, người đổi hàng ngoài chợ. Người là
    # thứ mọi cảnh giải thích đều có quyền có, vì lời kể luôn nói VỚI ai đó hoặc VỀ ai đó. Nó
    # không khẳng định điều gì sai về nội dung câu.
    #
    # Đo hậu quả của việc trả "": bản dài SURVIVE có 3/6 khung soi ra **trống trơn người** —
    # chỉ căn phòng và một dòng phụ đề. Một khung không có ai đứng trong đó thì không phải cảnh,
    # nó là tấm nền.
    #
    # Nên: đồ vật vẫn phải khớp từ mới vẽ; còn NGƯỜI là mặc định an toàn.
    return "nguoi"


# ── NHÃN CỘT: CẮT THEO TỪ, KHÔNG CẮT GIỮA CHỮ  (3/9/2026) ───────────────────────────────────
# Anh soi khung HOW BIG: nhãn biểu đồ hiện **"school bu"** và **"blue whal"** — cụt ngang giữa
# chữ, đọc ra như lỗi phần mềm.
#
# Gốc: `[:9]` rải ở **9 chỗ** trong tệp này. Con số 9 chọn để nhãn không tràn cột — đúng mục
# đích, sai cách: nó cắt theo KÝ TỰ nên rơi vào giữa một từ. "school bus" 10 ký tự chỉ thừa 1,
# mà thành "school bu".
#
# Cắt theo TỪ: giữ nguyên nếu vừa, không thì bỏ bớt từ đầu (thường là mạo từ / bổ ngữ) và giữ
# từ CUỐI — vì từ cuối mới là danh từ chính ("bus", "whale"). Không bao giờ để lại một từ cụt.
def _nhan(t: str, toi_da: int = 11) -> str:
    t = str(t or "").replace("a ", "", 1).replace("the ", "", 1).strip()
    if len(t) <= toi_da:
        return t
    tu = t.split()
    while len(tu) > 1 and len(" ".join(tu)) > toi_da:
        tu.pop(0)                 # bỏ từ ĐẦU, giữ danh từ chính ở cuối
    con = " ".join(tu)
    # MỘT TỪ ĐƠN THÌ KHÔNG CẮT.  (3/9/2026)
    # Bản trước cắt cứng ở `toi_da`, nên nhãn cột `conversation` (12 ký tự) hiện ra là
    # **`conversatio`** — soi lưới HOW LOUD thấy ngay. Một nhãn cụt đọc ra "lỗi phần mềm", tệ
    # hơn hẳn một nhãn dài hơn ba ký tự so với dự tính.
    #
    # Cắt chỉ có nghĩa khi còn RANH GIỚI để cắt. Nhiều từ thì bỏ bớt từ (vòng lặp trên đã làm);
    # một từ thì giữ nguyên — chỗ vẽ nhãn tự co cỡ chữ được, mà chữ cụt thì không cứu được.
    # Chốt chặn 22 ký tự để một chuỗi bất thường không phá bố cục.
    if len(con) <= toi_da or " " not in con:
        return con[:22]
    return con[:toi_da]


def kich_ban(ma: str, idx: int, long: bool = False, so_chuong: int = 10):
    """Danh sách nhịp HOÀN CHỈNH của một tập — gồm cả nhịp hook và ba lượt rải bố cục.

    ── VÌ SAO TÁCH RA  (3/9/2026) ──────────────────────────────────────────────────────────
    `cham_kich_ban.py` cần đúng danh sách mà `mot_tap` sắp dựng. Bản đầu của thước gọi thẳng
    `BO_SINH[ma](i)` cho tiện — và chấm SAI: nhịp hook được chèn ở `mot_tap`, sau khi bộ sinh
    đã trả về, nên thước thấy 17/18 kênh "hook không có số" trong khi hook thật luôn có số.

    Một phép đo đọc từ nguồn khác nguồn mà sản phẩm dùng thì nó đo một sản phẩm không tồn tại.
    Đúng luật 13.15 (*bài kiểm phải gọi bằng đúng đường mà mã thật gọi*) và đúng điều anh dặn
    hôm nay: *"cơ chế lưu thông minh để ko chồng chéo, lẫn lộn hay lỗi"*.

    Trả `(k, tiêu đề, hook, hook phụ, nhịp, mục lục)`. Không đọc tiếng, không vẽ ảnh, không
    dựng — nên gọi được từ cổng và từ thước mà không tốn một lượt API nào.
    """
    k = next((x for x in KENH if x["ma"] == ma), None)
    if not k:
        print(f"❌ không có kênh {ma}")
        return ""
    muc = []
    if long:
        # Kẹp theo trần THẬT của kênh — xem `so_chuong_toi_da`. Chỗ gọi xin bao nhiêu cũng
        # được; vượt trần thì chương sau lặp chủ đề chương trước, đổi một lỗi lấy một lỗi nặng
        # hơn. Kẹp ở đây chứ không ở workflow: workflow không biết bảng dữ liệu kênh nào lớn.
        _tran = so_chuong_toi_da(ma)
        if so_chuong > _tran:
            print(f"   ⓘ {ma}: xin {so_chuong} chương, kho chỉ đủ {_tran} — dựng {_tran}")
            so_chuong = _tran
        tieu, hook, hook_phu, nhip, muc = sinh_long(ma, idx, so_chuong)
    else:
        # Short lấy vị trí CHẴN, bản dài lấy vị trí LẺ — xem `vi_tri_short`/`vi_tri_long`.
        global _MA_HIEN
        _MA_HIEN = ma        # xem `_loi`
        tieu, hook, hook_phu, nhip = BO_SINH[k["sinh"]](vi_tri_short(ma, idx))
        # Ngữ pháp riêng của kênh, biến thể xoay theo số tập — xem `GU_KENH`.
        nhip = doi_loi(ap_gu(ma, idx, nhip), idx)
        # Cấp biểu tượng dự phòng cho `canh` — xem `_bt_canh`. Chỉ cấp khi nhịp CHƯA có, nên
        # không bao giờ đè lên biểu tượng đã chọn tay trong khuôn kịch bản.
        # ── `nhom` VÀ `kinh_lup` CŨNG CẦN BIỂU TƯỢNG DỰ PHÒNG  (4/9/2026) ─────────────
        # Bản trước chỉ cấp cho `canh`. Nhưng `nhom` vẽ một dải chữ trên nền, và `kinh_lup`
        # vẽ một vòng tròn — cả hai RỖNG nếu không có gì để soi. Cổng `kiem_hinh` vừa được
        # sửa để nhìn thấy chúng, và nó bắt 12 nhịp `nhom` trống trên 840 nhịp: đúng khung
        # WHAT IF "Now one hundred" — hàng cây với một nhãn, không có ai.
        # Ba khuôn cùng một nhu cầu, và bản vá cũ chỉ chạm một — §6, vá một nhánh để nguyên
        # nhánh song song.
        for _x in nhip:
            if (_x.get("khuon") or "") in ("canh", "nhom", "kinh_lup") and not _x.get("bt"):
                _b = _bt_canh(_x.get("loi") or "", _x.get("ve") or "")
                if _b:
                    _x["bt"] = _b
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
        # Khuôn `chia_doi` giấu hình trong `trai`/`phai`, không để ở cấp trên — nên phép lấy
        # `n.get("bt")` trả rỗng và nhịp hook thành khung trống (cổng KHUNG TRỐNG bắt được ở
        # `howmuch`). Nhìn vào cả hai nửa trước khi bỏ cuộc.
        def _hinh(n):
            return (n.get("bt") or (n.get("trai") or {}).get("bt")
                    or (n.get("phai") or {}).get("bt") or "")
        _bt = _hinh(_dau) or next((_hinh(n) for n in nhip[:3] if _hinh(n)), "")
        # LỜI HOOK PHẢI BÁM TẬP, không phải câu cố định của kênh.
        # `HOOK_LOI[ma]` là một câu viết sẵn cho mỗi kênh. Soi hai tập liền của `howmuch`: tập 2
        # nói về TRILLION vs BILLION mà lời vẫn đọc "A billion is not a big million" — sai nghĩa,
        # và trên màn hình còn đá nhau với dòng chú thích (vốn lấy từ tập). Bộ sinh đã trả sẵn
        # `hook` riêng cho từng tập; dùng nó, `HOOK_LOI` chỉ còn là đường lui.
        _hl = _cau_hook(hook, HOOK_LOI[ma])
        nhip.insert(0, {
            "khuon": "so_lieu", "loi": _hl, "dinh": True,
            "so": (hook_phu.split()[0] if hook_phu else ""),
            "don": (" ".join(hook_phu.split()[1:]) if hook_phu else ""),
            # BỎ CHÚ THÍCH KHI NÓ TRÙNG LỜI ĐỌC.
            # Từ khi lời hook bám tập (`_cau_hook`), cả `loi` lẫn `chu` cùng dựng từ `hook` —
            # nên màn hình hiện ĐÚNG MỘT CÂU HAI LẦN: một dòng chú thích nhỏ giữa khung và một
            # dòng phụ đề to ở đáy. Soi khung `realcost` thấy rõ. Phụ đề đã nói câu ấy rồi;
            # chú thích lặp lại chỉ chiếm chỗ và làm khung rối.
            "chu": "" if _cau_hook(hook, "").lower() == _hl.lower()
                   else hook.rstrip("?").title() + "?",
            **({"ve": _ve} if _ve else {}), **({"bt": _bt} if _bt else {}),
        })
    elif HOOK_LOI.get(ma) and nhip:
        # ── NHÁNH KHÔNG CÓ SỐ: MÂU THUẪN ĐỨNG TRƯỚC  (3/9/2026) ────────────────────────────
        # Nhánh trên (`if`) là hook kiểu khối số — con số chiếm một phần năm chiều cao khung và
        # tự nó là cái móc giữ chân. Nhánh này KHÔNG có số: bốn kênh trả lời định tính (whatif ·
        # dayinlife · wheregoes · therules) mở đầu bằng một câu hỏi trơn, tức ba giây đầu không
        # có gì để người xem ở lại. Số đo công bố (§13.16): quyết định lướt xảy ra trong ~400ms.
        #
        # `HOOK_LOI` của đúng bốn kênh ấy đã là những câu mạnh — *"You would quit by noon."* ·
        # *"You think it gets reused."* — và `_cau_hook` đang VỨT chúng đi để lấy câu hỏi tiêu đề.
        # Một câu hay viết sẵn mà không bao giờ được dùng thì cũng như chưa viết.
        #
        # ĐÃ THỬ SỬA TRONG `_cau_hook` và SAI: hàm ấy không thấy trường `so`, nên nó nối thêm
        # mâu thuẫn vào cả những kênh vốn đã có số — hook dài quá 8 chữ và điểm trung bình
        # TỤT 96,9 -> 94,7. Đúng luật 13.23: đo bằng ĐIỂM CUỐI, không bằng số lỗi sửa được.
        # Sửa ở đây thì phạm vi chính xác bằng đúng tập hợp cần sửa.
        _m = HOOK_LOI[ma].strip().rstrip(".")
        _c = _cau_hook(hook, HOOK_LOI[ma])
        _gh = f"{_m}. {_c}"
        # Trần 11 chữ ~ 4 giây đọc. Quá dài thì lấy MỖI mâu thuẫn: thà mất chủ đề ở giây đầu
        # còn hơn mất người xem ở giây đầu — chủ đề còn cả tập để nói.
        nhip[0]["loi"] = _gh if len(_gh.split()) <= 11 else f"{_m}."
        nhip[0]["dinh"] = True
    # ── RẢI BỐ CỤC — SAU KHI ĐÃ CHÈN HOOK  (3/9/2026) ──────────────────────────────────────
    # Một chỗ hẹp duy nhất cho CẢ short và long; đặt trong từng nhánh là hai chỗ để lệch nhau.
    #
    # Và phải đặt SAU khối hook, không trước. Nhịp hook được `insert(0, …)` ở ngay trên, nên nếu
    # rải trước thì nhịp quan trọng NHẤT của cả tập — ba giây đầu — là nhịp duy nhất không có bố
    # cục, và engine rơi về mặc định. Đo được: `kieu_so=None` ở 30/30 nhịp hook.
    #
    # Đây là lần thứ HAI trong ngày cùng một lỗi thứ tự (lần đầu: `_bt_canh` gắn ở `_n` nên hook
    # không có `bt`). Quy luật rút ra: **mọi lượt rải phải chạy sau MỌI lượt chèn nhịp**, vì nhịp
    # chèn sau không đi qua thứ đã chạy trước.
    # CHÈN TRƯỚC MỌI LƯỢT RẢI (§15.19). Chèn sau thì nhịp mới không được gán bố cục —
    # cổng `t_moi_nhip_co_bo_cuc` bắt đúng chuyện ấy ngay lượt chạy đầu: nhịp `the_chu`
    # vừa thêm thiếu `bo_the`, và engine sẽ lặng lẽ dùng bố cục mặc định.
    nhip = _day_du_y(ma, nhip, idx)
    # KHỬ TRÙNG HÌNH SAU KHI CHÈN, không trước. `_day_du_y` mượn biểu tượng của nhịp áp
    # chót cho ba nhịp mới, nên chèn xong là có hai ba nhịp liền cùng hình — cổng
    # `t_gu_hinh_khac_nhau` bắt đúng chuyện ấy ngay lượt chạy đầu.
    # §15.19 lần thứ ba trong ngày: MỌI lượt rải phải chạy SAU mọi lượt chèn nhịp.
    nhip = _rai_hinh(ma, nhip, idx)
    nhip = _rai_khuon(ma, nhip, idx)
    nhip = _rai_truc(ma, nhip, idx)
    nhip = _rai_dem(ma, nhip, idx)
    nhip = _rai_kinh_lup(ma, nhip, idx)
    # SAU MỌI LƯỢT CHÈN, xem §15.19 — lượt RẢI phải chạy sau lượt CHÈN, nếu không thì
    # nhịp hook (chèn ở `insert(0, …)`) không bao giờ được gán.
    nhip = _rai_tu_the(nhip, ma)
    # DẤU ẤN KÊNH — ghi vào MỌI nhịp. Python quyết, engine chỉ đọc (§15.3): engine không
    # biết mã kênh, và tính lại ở đó là tạo nguồn sự thật thứ hai.
    _da = DAU_AN.get(ma, (0, 0))
    for _n in nhip:
        _n["dau_an"], _n["dau_an_so"] = _da
    nhip = _rai_ss(ma, nhip, idx)
    nhip = _rai_so(ma, nhip, idx)
    nhip = _rai_chart(ma, nhip, idx)
    # Khử lặp gần — chạy SAU mọi lượt rải và sau khối hook, vì nó đọc thứ tự cuối cùng.
    nhip = _tranh_lap_gan(nhip, ma)
    # Xen kẽ ảnh CF với cảnh vẽ bằng code — cũng phải chạy SAU mọi lượt chèn, vì nó đếm
    # nhịp `canh` theo THỨ TỰ CUỐI CÙNG. Xem khối `NOI_KENH` để biết vì sao và tỉ lệ bao nhiêu.
    # ĐẠO CỤ TRƯỚC, RẢI CẢNH CODE SAU. `_rai_canh_ve` bỏ `ve` của những nhịp nó nhận, nên
    # chạy sau nó là gắn đạo cụ vào một trường sắp bị xoá — công cốc và không ai thấy.
    # Cùng họ §15.19: mọi lượt RẢI phải chạy sau mọi lượt CHÈN, và ngược lại ở đây là mọi
    # lượt SỬA `ve` phải chạy trước lượt XOÁ `ve`.
    _gan_dao_cu(nhip)
    _rai_canh_ve(nhip, ma, _lech_kenh(ma) + idx * 7919)
    # SAU `_rai_canh_ve`: nhịp nào nhận được tranh nhập thì bỏ luôn cảnh vẽ code của nó —
    # hai cảnh trong một khung là đúng thứ vừa đi sửa.
    _rai_hinh_nhap(nhip, ma, idx)
    for _n in nhip:
        if _n.get("hinh_nhap"):
            _n.pop("canh_ve", None)
            _n.pop("ve", None)

    return k, tieu, hook, hook_phu, nhip, muc


TAP_SO = os.path.join(GOC, "out", "so_tap_gt.json")


def tap_ke(ma: str) -> int:
    """Số tập kế tiếp CHƯA dựng của kênh `ma`.

    ── VÌ SAO PHẢI CÓ HÀM NÀY  (4/9/2026) ──────────────────────────────────────────────────
    `--tu` mặc định 0 và workflow không truyền nó:

        python giai_thich.py --kenh "$MA" --long --ngang --chuong 40     -> idx 0
        python giai_thich.py --kenh "$MA" --so 4                         -> idx 0,1,2,3

    Cả hai nằm TRONG một vòng `while` chạy tới hết ngân sách 285 phút, và workflow nổ 5 mốc
    cron mỗi ngày. Bộ sinh thì TẤT ĐỊNH theo `(kênh, idx)`. Nên mỗi vòng, mỗi lượt, mỗi ngày
    đều dựng lại **đúng năm tập ấy**, ghi đè lên đúng năm tên tệp ấy, rồi đẩy lên kho.

    Chú thích của chính workflow hứa *"~25 video mỗi luồng mỗi lượt, ×18 luồng ≈ 450
    video/lượt"*. Con số video thì đúng; số video KHÁC NHAU là 5 mỗi kênh, phần còn lại là
    bản sao. Và một kênh đăng cùng một tập nhiều lần mỗi ngày là đúng thứ chính sách
    "inauthentic content" của YouTube nêu tên (§13.17) — nặng hơn hẳn chuyện tốn công dựng.

    Không có gì báo, vì về mặt kỹ thuật không có gì hỏng — đúng họ lỗi §15.11 của bộ thiên
    nhiên (*tất định + số thứ tự bằng tay = sinh trùng*), lần này ở bộ giải thích.

    ── SỔ ĐẶT Ở ĐÂU ────────────────────────────────────────────────────────────────────────
    Hai nguồn, lấy số LỚN HƠN:
      1. tệp sổ `out/so_tap_gt.json` — sống qua nhiều lượt trên cùng một máy;
      2. quét chính `out/v9_<ma>_NNNN.mp4` — đúng khi sổ bị xoá mà video còn đó.
    Runner GitHub thì khởi tạo trắng mỗi lượt, nên đường CHÍNH ở đó là biến môi trường
    `GT_TAP_GOC` (workflow đặt từ `github.run_number`, xem `render_giai_thich_18.yml`) —
    một con số tăng đều, không tốn hạn mức, và không đụng Firestore.
    """
    goc = 0
    try:
        goc = int(os.environ.get("GT_TAP_GOC", "0") or 0)
    except ValueError:
        goc = 0
    n = goc
    try:
        with io.open(TAP_SO, encoding="utf-8") as f:
            n = max(n, int(json.load(f).get(ma, 0)))
    except Exception:
        pass
    try:
        rx = re.compile(rf"^v9_{re.escape(ma)}_(\d{{4}})(_long)?\.mp4$")
        for t in os.listdir(os.path.join(GOC, "out")):
            m = rx.match(t)
            if m:
                n = max(n, int(m.group(1)) + 1)
    except Exception:
        pass
    return n


def ghi_tap(ma: str, idx: int) -> None:
    """Ghi vào sổ rằng tập `idx` của kênh `ma` đã dựng. Hỏng thì im — sổ chỉ là một trong
    hai nguồn, và nguồn kia (quét `out/`) vẫn đứng."""
    try:
        d = {}
        try:
            with io.open(TAP_SO, encoding="utf-8") as f:
                d = json.load(f) or {}
        except Exception:
            d = {}
        if int(d.get(ma, 0)) <= idx:
            d[ma] = idx + 1
            os.makedirs(os.path.dirname(TAP_SO), exist_ok=True)
            with io.open(TAP_SO, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False)
    except Exception:
        pass


def mot_tap(ma: str, idx: int, doc: bool = True, long: bool = False,
            so_chuong: int = 10, san=None) -> str:
    """Dựng một tập. `san` = (tiêu đề, hook, hook phụ, nhịp, hậu tố slug) đã chuẩn bị sẵn.

    `san` cho phép dựng một tập từ kịch bản CẮT RA từ tập khác — xem `short_tu_long`. Nhịp
    truyền vào đã mang sẵn `nenAnh`, nên bước vẽ ảnh bị bỏ qua hoàn toàn và tập ấy tốn 0 lượt
    CF. Không đi đường này thì "short cắt từ long" chỉ là tên gọi.
    """
    if san:
        k = next((x for x in KENH if x["ma"] == ma), None)
        tieu, hook, hook_phu, nhip, _hau = san
        muc = []
    else:
        k, tieu, hook, hook_phu, nhip, muc = kich_ban(ma, idx, long, so_chuong)
        _hau = ""
    if not k:
        return ""
    slug = f"{ma}_{idx:04d}" + ("_long" if long else "") + _hau
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
        _ks = [] if os.environ.get("GT_KHONG_CF") else [
               k for k in (T2.keys_cuc_bo() or [])
               if str(k if isinstance(k, str) else k.get("key", "")).startswith("cf:")]
        if _ks:
            _mk = MAU_KENH.get(ma, {})
            # ĐÃ CÓ ẢNH SẴN THÌ KHÔNG GỌI CF. Nhịp cắt ra từ bản dài mang theo `nenAnh` của
            # bản dài; gọi lại `sinh_tap` sẽ vẽ ảnh MỚI cho cùng cảnh ấy — vừa tốn hạn mức vừa
            # làm short khác hình với long, tức mất đúng lợi thế của việc cắt ra.
            # CẮT TỪ BẢN DÀI THÌ TUYỆT ĐỐI KHÔNG GỌI CF. Đo lượt thử: bản dài vẽ hụt 1/3
            # cảnh (cạn hạn mức), và short cắt ra lại đi vẽ bù đúng cảnh ấy — tức "0 lượt CF
            # mới" chỉ đúng khi bản dài may mắn vẽ đủ. Một short ăn theo mà lại tự đặt hàng
            # CF thì nó không còn là bản cắt ra nữa, và cái trần hạn mức tính theo bộ 1:3
            # cũng sai theo. Cảnh thiếu ảnh rơi về lớp vẽ bằng code, y như mọi nhịp khác.
            _na = 0 if (san or all((not x.get("ve")) or x.get("nenAnh") for x in nhip)) \
                  else nen_gt.sinh_tap(ma, idx, nhip, _ks, doc=doc,
                                  mau_chu=_mk.get("chu", ""), mau_nen=_mk.get("nen", ""))
            # Mẫu số chỉ đếm nhịp THẬT SỰ đặt hàng CF. Nhịp `canh_ve` vẽ bằng code là
            # nhịp đã có hình, không phải nhịp thiếu hình — đếm chúng vào đây thì dòng
            # "vẽ 39/134 cảnh" sẽ đọc ra như một lượt hỏng nặng ngay hôm đầu bật xen kẽ.
            # ── ẢNH KHÔNG RA THÌ RƠI VỀ CẢNH VẼ CODE, KHÔNG RƠI VỀ PHÒNG TRỐNG  (4/9/2026)
            # Một nhịp đặt ảnh CF mà không có ảnh (hồ cạn · 4 lượt vẽ đều trượt cổng · quá
            # tối) trước đây rơi xuống `NenPhong` — một căn phòng trơn không nói gì về nội
            # dung câu. Nay nó nhận đúng nơi chốn của kênh, tức vẫn là một CẢNH.
            #
            # Đây là mắt xích làm cả dây chuyền tự chạy được: hồ CF cạn giữa chừng thì
            # phần còn lại của tập không xấu đi thành phòng trống, nó chỉ chuyển sang lớp
            # vẽ code — lớp không gọi mạng nên không bao giờ hỏng theo (§7, bốn tầng nền).
            _cn = sum(1 for x in nhip if x.get("ve"))
            _cv = sum(1 for x in nhip if x.get("canh_ve"))
            # NÓI RÕ VÌ SAO THIẾU, KHÔNG CHỈ NÓI THIẾU BAO NHIÊU  (2/9/2026)
            # "vẽ 6/42" một mình không hành động được: 36 cảnh thiếu vì cạn hạn mức thì phải đi
            # thêm khoá CF; vì prompt bị chặn NSFW thì phải sửa chữ; vì bốn lượt vẽ đều hỏng thì
            # phải xem mạng hay mô hình. Ba nguyên nhân, ba việc khác hẳn nhau — mà con số gộp
            # lại không phân biệt được cái nào, nên nó dẫn người đọc đi sai hướng.
            _ly = []
            for _t, _n in (("cạn hạn mức", "_can"), ("4 lượt đều hỏng", "_het")):
                _v = getattr(nen_gt.sinh, _n, 0)
                if _v:
                    _ly.append(f"{_t} {_v}")
            # ── KẾT VÒNG VỀ HÌNH MỞ ĐẦU  (3/9/2026) ──────────────────────────────────────
            # Anh: *"mở đầu kết thúc nhàm chán tẻ nhạt."* Trích ba khung cuối của tập mẫu: cùng
            # một hình, người đứng yên, rồi video hết một cách lửng lơ — không có cú đóng.
            #
            # Luật 13.16 của chính dự án đã chỉ ra đòn bẩy, và nó là đòn bẩy DUY NHẤT ở đây
            # không tốn thêm một lượt gọi API nào: *"rewatch là tín hiệu nặng nhất của TikTok →
            # kết ghép vòng được"*. Cho cảnh cuối dùng LẠI hình của cảnh mở đầu thì khi video
            # tự phát lại, khung cuối và khung đầu nối liền — mắt không thấy chỗ nối, và lượt
            # xem thứ hai bắt đầu trước khi người ta kịp quyết định lướt đi.
            #
            # Ba điều kiện, thiếu một là KHÔNG làm — vòng ghép sai còn tệ hơn không ghép:
            #   · cảnh cuối phải CHƯA có ảnh riêng (không cướp hình của nó);
            #   · cảnh đầu phải CÓ ảnh (không thì chẳng có gì để vòng về);
            #   · phải có ít nhất 4 nhịp (tập quá ngắn thì đầu và cuối kề nhau, ghép vòng chỉ
            #     làm nó trông như một ảnh lặp hai lần).
            if len(nhip) >= 4:
                _dau = next((x for x in nhip if x.get("nenAnh")), None)
                _cuoi = nhip[-1]
                # `not _cuoi.get("canh_ve")`: nhịp cuối vẽ bằng code thì nó ĐÃ có hình.
                # Gán `nenAnh` đè lên nó là xoá mất cảnh vẽ code — và engine ưu tiên
                # `nenAnh` nên sẽ không có lỗi nào báo, chỉ là mất một cảnh.
                if (_dau is not None and not _cuoi.get("nenAnh")
                        and not _cuoi.get("canh_ve") and _dau is not _cuoi):
                    _cuoi["nenAnh"] = _dau["nenAnh"]
                    print("   ↩ kết vòng: cảnh cuối dùng lại hình mở đầu (ghép liền khi phát lại)")

            print(f"   🎨 vẽ {_na}/{_cn} cảnh bằng CF · {_cv} cảnh vẽ bằng code"
                  + ("" if _na == _cn else "  (số còn lại dùng nền vẽ bằng code"
                     + (" — " + " · ".join(_ly) if _ly else "") + ")"))
        else:
            print("   ⚠ không có khoá CF — toàn bộ dùng nền vẽ bằng code")
    except Exception as e:
        print(f"   ⚠ vẽ cảnh hỏng ({str(e)[:70]}) — dùng nền vẽ bằng code")

    # ── LƯỚI AN TOÀN PHẢI Ở NGOÀI CÁI NÓ ĐỠ  (5/9/2026) ─────────────────────────────────
    # Vòng gán cảnh dự phòng này trước đây nằm BÊN TRONG `if _ks:` — tức nó chỉ chạy khi hồ
    # khoá CF không rỗng. Ba nhánh thoát khác (hồ rỗng · `--khong-cf` · khối vẽ ném lỗi) đều
    # bỏ qua nó, và cả ba đều IN RA rằng "toàn bộ dùng nền vẽ bằng code" — một câu nói dối:
    # không nhịp nào được gán `canh_ve`, nên engine rơi xuống `NenPhong`, một bức tường trơn.
    #
    # Đo trên clip demo `--khong-cf`: 5 nhịp `canh`, chỉ **1** có cảnh, 4 khung còn lại là
    # tường trắng có một cái bóng. Đúng họ lỗi §12.8 — hỏng mà vẫn báo xanh, và ở đây câu báo
    # còn mô tả chính xác điều đáng lẽ phải xảy ra.
    #
    # Một lưới an toàn đặt bên trong nhánh thành công thì nó không phải lưới an toàn.
    _noi = NOI_KENH.get(ma) or ("dong", "pho", "van_phong")
    _hut = 0
    for _j, _x in enumerate(nhip):
        # `KHUON_TU_VE`: khuôn tự vẽ đồ hoạ thì KHÔNG nhận cảnh vẽ — xem chú thích ở chỗ
        # khai báo. Đây là chỗ gán `canh_ve` THỨ HAI trong tệp, và bản sửa lúc đầu chỉ chạm
        # vào chỗ thứ nhất; thiếu dòng này thì `so_lieu` lại có cả một cảnh kho sau lưng
        # ngay khi hồ CF cạn (§6 — vá một nhánh, để nguyên nhánh song song).
        if (_x.get("khuon") or "") in KHUON_TU_VE or not _x.get("ve") or _x.get("nenAnh"):
            continue
        _bt = str(_x.get("bt") or "")
        _hop = [x for x in _noi if _hop_noi(_bt, x)] or list(_noi)
        _x["canh_ve"] = _hop[(_lech_kenh(ma) + _j) % len(_hop)]
        _x["canh_hat"] = (_lech_kenh(ma) + _j * 7919) % 100000
        _hut += 1
    if _hut:
        print(f"   ↩ {_hut} nhịp không có ảnh CF -> dùng cảnh vẽ bằng code")

    # Mốc nhịp lấy từ ĐỘ DÀI TIẾNG NÓI, không đặt cứng: câu ngắn thì cảnh ngắn. Đây chính là
    # cơ chế cho ra nhịp 2,1 giây — nó nằm ở khâu VIẾT (câu 5-8 chữ), không ở khâu dựng.
    for i, n in enumerate(nhip):
        n["s"] = round(moc[i][0], 3)
        n["e"] = round(moc[i + 1][0] if i + 1 < len(moc) else moc[i][1] + 0.55, 3)
    dai = round(nhip[-1]["e"] + 0.35, 2)

    mk = MAU_KENH.get(ma, {"nen": "#F3EEE4", "mau": k["mau"], "phu": k["phu"], "chu": "#2C2722"})
    # `ma` sang engine để nó chọn PHÔNG CHỮ của kênh (xem `gt/Chu.tsx`). Không suy từ
    # `tieuDe` ở engine: tiêu đề đổi theo tập, mã kênh thì không.
    props = {"ma": ma, "nhip": nhip, "tu": tu, "voMp3": rel,
             "nhac": _nhac(ma, long), "nhacVol": _am_nhac(_nhac(ma, long)),
             # HẠT GIỐNG THEO TẬP. Trước bản này `hat` được TÍNH ở trên rồi bỏ đó — engine
             # không bao giờ nhận, nên mọi tập của một kênh dựng y hệt nhau. Cùng họ lỗi
             # "tính rồi không dùng" đã vấp ở `mauChu`.
             "hat": hat,
             "tieuDe": k["ten"],
        # HOOK CỦA CHÍNH TẬP — `sieu_gt.py` dùng làm tiêu đề YouTube.  (3/9/2026)
        # Trước bản này `sieu_gt` ghép `f"{tên kênh}? {con số}"`. Nhưng 7/18 tên kênh KHÔNG phải
        # câu hỏi ("A DAY IN THE LIFE OF" · "THE RULES NOBODY READS" · "YEARS OF YOUR LIFE"),
        # nên tiêu đề ra **"A DAY IN THE LIFE OF? 19 miles"** — thiếu chủ thể, dấu hỏi lửng.
        # Hook của tập vốn đã là một tiêu đề đúng ngữ pháp VÀ cụ thể hơn cho tìm kiếm
        # ("A DAY IN THE LIFE OF A ROMAN SOLDIER"), nên nó là thứ đúng để dùng — chỉ là props
        # chưa bao giờ mang nó sang.
        "hookTap": hook, "handle": "@" + ma + "usa",
             "mau": mk["mau"], "mauPhu": mk["phu"],
             "nenTrang": mk["nen"], "chuTrang": mk["chu"],
             "dai": dai, "doc": doc}
    _ = (hook, hook_phu)   # thẻ hook đã bỏ theo yêu cầu; giữ biến để bộ sinh không phải sửa
    # Xả sổ sức khoẻ khoá của CẢ BA NHÀ (cf ở `nen_gt`, gemini/groq ở `key_manager`) — đặt ở đây
    # vì khâu VIẾT KỊCH BẢN dùng gemini/groq mà không đi qua `sinh_tap`, nên nếu chỉ xả trong ấy
    # thì 173 khoá của hai nhà kia vẫn không bao giờ được ghi.
    try:
        import xoay_key as _XK
        _XK.ghi_trang_thai(os.environ.get("OWNER_UID", ""))
    except Exception:
        pass
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
    # ── ẢNH BÌA LẤY NHỊP ĐỈNH, KHÔNG LẤY GẦN CUỐI  (3/9/2026) ────────────────────────────
    # `lam_thumb` mặc định trích khung ở **1,2 giây trước khi hết video** — đúng cho bộ comic
    # (cú chốt nằm ở cuối) và SAI cho bộ giải thích: nhịp cuối là cảnh đóng, còn khung đáng làm
    # bìa là nhịp có CON SỐ lớn giữa khung.
    #
    # Trường `dinh` đánh dấu đúng những nhịp ấy — 87 chỗ trong mã đặt `dinh=True`, và **không ai
    # đọc nó**. Đúng họ lỗi §15.12: viết ra một trường rồi không bao giờ đọc, im lặng cả hai phía.
    # Nay nó làm việc nó sinh ra để làm.
    #
    # Ưu tiên nhịp đỉnh CÓ SỐ (`so_lieu`/`chia_doi`) vì con số là thứ bán được cú click; không
    # có thì lấy nhịp đỉnh nào cũng được; không có nữa thì rơi về hành vi cũ.
    _dinh = [n for n in nhip if n.get("dinh") and n.get("s") is not None]
    _uu = [n for n in _dinh if (n.get("khuon") or "") in ("so_lieu", "chia_doi")] or _dinh
    _moc = 0.0
    if _uu:
        _n0 = _uu[len(_uu) // 2]          # nhịp đỉnh ở GIỮA tập: đã vào mạch, chưa lộ kết
        _moc = float(_n0["s"]) + (float(_n0["e"]) - float(_n0["s"])) * 0.62
    lam_thumb(out, tieu, k["ten"], k["mau"], os.path.join(GOC, "out", f"v9_{slug}.jpg"),
              giay=_moc)

    d = [round(n["e"] - n["s"], 2) for n in nhip]
    d.sort()
    print(f"   ✅ {os.path.basename(out)} ({os.path.getsize(out)/1e6:.1f} MB · {dai:.1f}s · "
          f"{len(nhip)} nhịp · trung vị {d[len(d)//2]:.1f}s · dài nhất {d[-1]:.1f}s · {am})")
    # Ghi sổ CHỈ khi video đã thành tệp. Ghi ở đầu hàm là đánh dấu "xong" cho một tập còn có
    # thể hỏng giữa chừng, và lượt sau sẽ nhảy qua nó — mất tập mà không ai biết.
    ghi_tap(ma, idx)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    # `--tu` là TUỲ CHỌN ÉP, không phải mặc định 0. Xem `tap_ke()`: mặc định 0 cộng với bộ
    # sinh tất định là công thức sinh trùng, và nó không báo gì cả.
    ap.add_argument("--tu", type=int, default=-1,
                    help="ép số tập bắt đầu; bỏ trống thì máy tự đếm tập kế tiếp (tap_ke)")
    ap.add_argument("--so", type=int, default=1)
    ap.add_argument("--ngang", action="store_true", help="dựng bản 16:9 thay vì 9:16")
    # ── SOI LỚP VECTOR PHẢI CHỦ ĐỘNG ĐƯỢC  (5/9/2026) ──────────────────────────────────
    # Anh chê năm khung "chồng chéo, nghiệp dư", và em mất một vòng mới biết cả năm đều là
    # LỚP DỰ PHÒNG — hồ CF cạn nên không nhịp nào có ảnh. Tức lớp ấy quyết định phần lớn
    # những gì anh thật sự nhìn thấy, mà cách duy nhất để soi nó là **chờ hồ cạn**.
    # Một lớp chỉ kiểm được khi hạ tầng hỏng là một lớp không được kiểm.
    ap.add_argument("--khong-cf", action="store_true",
                    help="dựng 100%% bằng đồ hoạ code, không gọi CF (để soi lớp dự phòng)")
    ap.add_argument("--long", action="store_true", help="bản dài (chương theo dòng dữ liệu)")
    # Anh: *"long demo e dựng ngắn a coi là được, nào vào dựng thật thì scale lên."*
    # Đúng: cấu trúc bản dài (mở đầu -> thẻ chương -> các chương -> biểu đồ tổng hợp -> chốt)
    # kiểm được với 3 chương y như với 10, mà tốn 1/3 số ảnh. Vào sản xuất chỉ đổi con số này.
    ap.add_argument("--chuong", type=int, default=10, help="số chương của bản dài (demo: 3)")
    ap.add_argument("--short-tu-long", type=int, default=-1, metavar="N",
                    help="dựng N short 9:16 từ kịch bản N chương đầu của bản dài")
    a = ap.parse_args()
    if a.khong_cf:
        # Truyền qua biến môi trường chứ không qua tham số hàm: đường sinh ảnh nằm sâu bốn
        # tầng gọi, và nhét thêm một tham số vào cả bốn là bốn chỗ để quên một chỗ.
        os.environ["GT_KHONG_CF"] = "1"
        print("   🎨 chế độ KHÔNG CF — mọi hình vẽ bằng code")
    # ── BẢN DÀI LUÔN LÀ 16:9  (2/9/2026) ────────────────────────────────────────────────────
    # Anh gửi khung hình: bản dài ra **9:16 dọc**, hai mép đen, chữ tràn.
    #
    # Gốc rễ: `--long` và `--ngang` là HAI cờ ĐỘC LẬP, và `doc=not a.ngang`. Nên gọi
    # `--long --chuong 10` mà quên `--ngang` là dựng nội dung dài bằng composition DỌC
    # (`GiaiThichDoc`) — đúng cú pháp, chạy trót lọt, không một dòng lỗi nào. Workflow đã gọi
    # thiếu như thế suốt.
    #
    # Sửa ở GỐC chứ không vá workflow: bản dài là chỗ bật quảng cáo giữa video trên YouTube,
    # nó **không có** phiên bản dọc. Một cờ mà mọi người gọi đều phải nhớ kèm cờ thứ hai thì
    # sớm muộn có người quên — nên để mặc định tự đúng, và chỉ ai thật sự muốn dọc mới phải nói.
    #
    # Cùng họ lỗi "một kích thước chịu hai ràng buộc mà công thức chỉ mã hoá một" (§6): ở đây
    # `doc` bị quyết định bởi MỘT cờ, trong khi nó phụ thuộc CẢ `--long`.
    if a.long and not a.ngang:
        a.ngang = True
        print("   ↔ bản dài -> ép 16:9 (bản dài không có phiên bản dọc)")
    ds = [x.strip() for x in a.kenh.split(",") if x.strip()] or [k["ma"] for k in KENH]

    # SỐ TẬP TÍNH RIÊNG CHO TỪNG KÊNH. Bản cũ dùng `a.tu + i + j` — một mốc chung cộng chỉ số
    # kênh trong danh sách, nên hai kênh không bao giờ ở cùng một chỗ trong lịch của CHÍNH
    # chúng, và `j` làm kênh thứ hai bắt đầu ở tập 1 dù nó chưa có tập 0. Mỗi kênh có lịch
    # riêng thì mỗi kênh phải đếm riêng.
    def _goc(de: str) -> int:
        return a.tu if a.tu >= 0 else tap_ke(de)

    if a.short_tu_long > 0:
        # BA CHƯƠNG HAY NHẤT, không phải ba chương ĐẦU. Thứ tự trong bản dài xếp theo mạch
        # kể chứ không theo sức hút, và chương dài từ 6,5 đến 15,5 nhịp — lấy theo thứ tự là
        # bỏ qua chương mạnh hơn nằm ngay cạnh. Xem `chuong_hay`.
        ra = []
        for de in ds:
            g = _goc(de)
            for c in (chuong_hay(de, g, a.chuong, a.short_tu_long)
                      or list(range(a.short_tu_long))):
                v = short_tu_long(de, g, c, a.chuong)
                if v:
                    ra.append(v)
    else:
        ra = []
        for de in ds:
            g = _goc(de)
            if a.tu < 0:
                print(f"   📓 {de}: tập kế tiếp = {g}")
            for i in range(a.so):
                v = mot_tap(de, g + i, doc=not a.ngang, long=a.long, so_chuong=a.chuong)
                if v:
                    ra.append(v)
    print(f"\n✅ {len(ra)}/{len(ds) * a.so} video")
    return 0 if ra else 1


if __name__ == "__main__":
    raise SystemExit(main())
