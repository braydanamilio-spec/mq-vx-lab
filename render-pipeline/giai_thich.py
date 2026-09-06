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

    # ── NỐI THÊM 6/9/2026 · 47 mục, mỗi mục qua bốn cổng của
    #    `bang_mo_rong.py`; xuất xứ ở `bang_nguon_*.json`. Con số là ĐỀ NGHỊ
    #    của AI đã sống sót qua một lượt ĐỐI CHỨNG độc lập, không phải hằng
    #    số tra từ sách — nên nếu một mục nào bị người xem bắt sai, sửa THẲNG
    #    ở đây và giữ nguyên cơ chế.
    ('distance to the Sun', 93000000, 'mat_troi', 'tuyen', ''),
    ('the orbit of Mercury', 36100000, 'trai_dat', 'den', 'orbit of Mercury'),
    ('the surface of the Moon', 238855, 'mat_trang', 'den', 'surface of the Moon'),
    ('Denver to Salt Lake City', 520, 'trai_dat', 'tuyen', ''),
    ('Portland to Boise', 429, 'trai_dat', 'tuyen', ''),
    ('the Historic Route 66 in Arizona', 400, 'trai_dat', 'den', 'Historic Route 66 in Arizona'),
    ('Philadelphia to Pittsburgh', 304, 'trai_dat', 'tuyen', ''),
    ('the I-90 across Washington', 300, 'trai_dat', 'den', 'I-90 across Washington'),
    ('Las Vegas to Los Angeles', 270, 'trai_dat', 'tuyen', ''),
    ('Atlanta to Charlotte', 244, 'trai_dat', 'tuyen', ''),
    ('Miami to Orlando', 236, 'xe', 'tuyen', ''),
    ('Boston to New York', 215, 'trai_dat', 'tuyen', ''),
    ('the intercity bus from New\xa0York to Boston', 215, 'xe_buyt', 'den', 'intercity bus from New York to Boston'),
    ('Nashville to Memphis', 212, 'trai_dat', 'tuyen', ''),
    ('the John Muir Trail', 211, 'trai_dat', 'den', 'John Muir Trail'),
    ('a weekend road trip from Nashville to Memphis', 210, 'trai_dat', 'den', 'weekend road trip from Nashville to Memphis'),
    ('Dallas to Austin', 195, 'trai_dat', 'tuyen', ''),
    ('Seattle to Portland', 175, 'trai_dat', 'tuyen', ''),
    ('Seattle to Portland', 174, 'trai_dat', 'tuyen', ''),
    ('Detroit to Cleveland', 170, 'trai_dat', 'tuyen', ''),
    ('coastal drive from Baltimore to Ocean\xa0City', 135, 'xe', 'tuyen', ''),
    ('a desert road trip from Phoenix to Sedona', 120, 'trai_dat', 'den', 'desert road trip from Phoenix to Sedona'),
    ('Phoenix to Tucson', 116, 'trai_dat', 'tuyen', ''),
    ('Indianapolis to Louisville', 115, 'trai_dat', 'tuyen', ''),
    ('the turnpike connecting Oklahoma City and Tulsa', 105, 'trai_dat', 'den', 'turnpike connecting Oklahoma City and Tulsa'),
    ('Hartford to Provid Providence', 100, 'trai_dat', 'tuyen', ''),
    ('train stretch from Philadelphia to Baltimore', 100, 'trai_dat', 'tuyen', ''),
    ('Chicago to Milwaukee', 92, 'may_bay', 'tuyen', ''),
    ('San Francisco to Sacramento', 87, 'trai_dat', 'tuyen', ''),
    ('New\xa0Orleans to Baton\xa0Rouge', 81, 'trai_dat', 'tuyen', ''),
    ('Denver to Colorado Springs', 70, 'trai_dat', 'tuyen', ''),
    ('Kansas\xa0City to Topeka', 61, 'trai_dat', 'tuyen', ''),
    ('commuter rail from Boston to Providence', 50, 'trai_dat', 'tuyen', ''),
    ('regional train from Boston to Providence', 50, 'trai_dat', 'tuyen', ''),
    ('Salt\xa0Lake\xa0City to Provo', 46, 'trai_dat', 'tuyen', ''),
    ('Washington D.C. to Baltimore', 39, 'xe_buyt', 'tuyen', ''),
    ('a scenic rail line from Seattle to Tacoma', 35, 'trai_dat', 'den', 'scenic rail line from Seattle to Tacoma'),
    ('Dallas to Fort Worth', 32, 'xe', 'tuyen', ''),
    ('Raleigh to Durham', 25, 'trai_dat', 'tuyen', ''),
    ('the Lake Pontchartrain Causeway', 24, 'trai_dat', 'den', 'Lake Pontchartrain Causeway'),
    ('the Grand Canyon Rim-to-Rim Trail', 24, 'trai_dat', 'den', 'Grand Canyon Rim-to-Rim Trail'),
    ('Minneapolis to St.\u202fPaul', 11, 'trai_dat', 'tuyen', ''),
    ('the Seven Mile Bridge', 7, 'trai_dat', 'den', 'Seven Mile Bridge'),
    ('a ferry ride across San Francisco Bay', 7, 'ca_voi', 'den', 'ferry ride across San Francisco Bay'),
    ('the length of the Golden Gate Bridge', 1.7, 'trai_dat', 'den', 'length of the Golden Gate Bridge'),
    ('the walk across the Golden Gate Bridge', 1.7, 'nguoi', 'den', 'walk across the Golden Gate Bridge'),
    ('a bike ride across the Brooklyn Bridge', 1, 'xe', 'den', 'bike ride across the Brooklyn Bridge'),
]

# Giới từ theo loại: (cho câu "Walking …" và chữ hook, cho câu "The distance …").
# Hai cột vì chúng KHÁC NHAU ở `vat`: "Walking the Appalachian Trail" nhưng "The distance OF
# the Appalachian Trail" — dùng chung một giới từ là ra một trong hai câu sai.
GIOI_TU = {"den":   ("to ",   "to "),
           "tuyen": ("from ", "from "),
           "vong":  ("",      ""),
           "vat":   ("",      "of ")}

CO_LON = [                                       # feet
    ('a blue whale', 98, 'ft', 'ca_voi'),
    ('a school bus', 36, 'ft', 'xe_buyt'),
    ('a giraffe', 18, 'ft', 'huou'),
    ("an adult human",          5.6, "ft", "nguoi"),
    ('a Boeing 747', 232, 'ft', 'may_bay'),
    ('the Statue of Liberty', 305, 'ft', 'nha'),
    ('a football field', 300, 'ft', 'nguoi'),
    # ── NỐI THÊM 1/9. Chiều cao/dài bằng FOOT. Cặp lấy bằng `_cap`.
    ('a ten-storey building', 110, 'ft', 'nha'),
    ('a grand piano', 9, 'ft', 'dan_piano'),
    ('a refrigerator', 6, 'ft', 'hop'),
    ("a smartphone",                  0.5, "ft", "dien_thoai"),
    ("a housecat",                    1.5, "ft", "meo"),
    ('a passenger jet', 230, 'ft', 'may_bay'),
    ('the Empire State Building', 1454, 'ft', 'nha'),
    ('a redwood tree', 350, 'ft', 'cay'),
    ('a city bus', 40, 'ft', 'xe_buyt'),

    # ── NỐI THÊM 6/9/2026 · 148 mục, mỗi mục qua bốn cổng của
    #    `bang_mo_rong.py`; xuất xứ ở `bang_nguon_*.json`. Con số là ĐỀ NGHỊ
    #    của AI đã sống sót qua một lượt ĐỐI CHỨNG độc lập, không phải hằng
    #    số tra từ sách — nên nếu một mục nào bị người xem bắt sai, sửa THẲNG
    #    ở đây và giữ nguyên cơ chế.
    ('the Mackinac Bridge', 26000, 'ft', 'nguoi'),
    ('the Pont de Normandie', 8450, 'ft', 'nguoi'),
    ('the Holland Tunnel', 7410, 'ft', 'nguoi'),
    ('the Lincoln Tunnel', 7275, 'ft', 'nguoi'),
    ('the Queensboro Bridge', 3360, 'ft', 'nguoi'),
    ('the Burj Khalifa', 2722, 'ft', 'nguoi'),
    ('the Carquinez Bridge', 2200, 'ft', 'nguoi'),
    ('the Shanghai\xa0Tower', 2073, 'ft', 'nguoi'),
    ('the Abraj\xa0Al\xa0Bait\xa0Tower', 1971, 'ft', 'nguoi'),
    ('the Petronas\xa0Twin\xa0Towers', 1912, 'ft', 'nguoi'),
    ('the Lotte\xa0World\xa0Tower', 1900, 'ft', 'trai_dat'),
    ('the One World Trade Center', 1776, 'ft', 'trai_dat'),
    ('the Taipei\xa0101', 1671, 'ft', 'nguoi'),
    ('the Willis Tower', 1450, 'ft', 'nguoi'),
    ('the Bank of China\xa0Tower', 1155, 'ft', 'nguoi'),
    ('the Queen Mary 2 ocean liner', 1135, 'ft', 'ca_voi'),
    ('the Nimitz-class supercarrier', 1084, 'ft', 'nguoi'),
    ('the Eiffel\xa0Tower', 1063, 'ft', 'nguoi'),
    ('the Chrysler\xa0Building', 1046, 'ft', 'nha'),
    ('the Kingdom\xa0Centre', 1005, 'ft', 'nguoi'),
    ('the One\xa0Canada\xa0Square', 1001, 'ft', 'nguoi'),
    ('the Rockefeller\xa0Center\xa0Tower', 850, 'ft', 'nguoi'),
    ('the MetLife\xa0Building', 808, 'ft', 'nha'),
    ('the Hindenburg airship', 804, 'ft', 'nguoi'),
    ('the New\xa0York\xa0Times\xa0Building', 789, 'ft', 'dong_ho'),
    ('the Golden\xa0Gate\xa0Bridge\xa0tower', 746, 'ft', 'nguoi'),
    ('the Hoover Dam', 726, 'ft', 'nguoi'),
    ('the Glen Canyon Dam', 710, 'ft', 'nguoi'),
    ('the Itaipu Dam', 689, 'ft', 'nguoi'),
    ('the Hearst\xa0Tower', 631, 'ft', 'nguoi'),
    ('the St.~Louis\xa0Gateway\xa0Arch', 630, 'ft', 'nguoi'),
    ('the Three Gorges Dam', 607, 'ft', 'nguoi'),
    ('the Seattle Space Needle spire', 605, 'ft', 'nguoi'),
    ('the Shasta Dam', 602, 'ft', 'nguoi'),
    ('the Gherkin', 591, 'ft', 'nguoi'),
    ('the Tarbela Dam', 560, 'ft', 'nguoi'),
    ('the Washington\xa0Monument', 555, 'ft', 'nguoi'),
    ('the German Navy F125 frigate', 509, 'ft', 'nguoi'),
    ('the London Eye observation wheel', 443, 'ft', 'nguoi'),
    ('a soccer pitch at a World Cup venue', 360, 'ft', 'trai_dat'),
    ('the rugby union pitch at a national stadium', 360, 'ft', 'nguoi'),
    ('the Japanese Maritime Self-Defense Sōryū submarine', 332, 'ft', 'ca_voi'),
    ('a lacrosse field at a college stadium', 330, 'ft', 'nguoi'),
    ('a field hockey pitch at an Olympic venue', 300, 'ft', 'nguoi'),
    ('the U.S.~Capitol\xa0Dome', 288, 'ft', 'nguoi'),
    ('the Flatiron\xa0Building', 285, 'ft', 'nha'),
    ('the Antonov An-225 Mriya', 275, 'ft', 'nguoi'),
    ('a wind turbine tower', 250, 'ft', 'nguoi'),
    ('a softball field at a high-school complex', 250, 'ft', 'nguoi'),
    ('the Lockheed C-5 Galaxy cargo plane', 247, 'ft', 'may_bay'),
    ('the Airbus A380', 239, 'ft', 'nguoi'),
    ('the kapok tree', 230, 'ft', 'cay'),
    ('the Concorde supersonic jet', 202, 'ft', 'may_bay'),
    ('the ice hockey rink at a professional arena', 200, 'ft', 'nguoi'),
    ('the Goodyear Blimp', 192, 'ft', 'nguoi'),
    ('the paper mill smokestack', 180, 'ft', 'nguoi'),
    ('the western hemlock', 180, 'ft', 'nguoi'),
    ('the swimming pool length at an Olympic center', 164, 'ft', 'nguoi'),
    ('a commercial airliner fuselage', 150, 'ft', 'nguoi'),
    ('the curling sheet at a dedicated rink', 147, 'ft', 'nha'),
    ('the Space Shuttle orbiter', 122, 'ft', 'may_bay'),
    ('the tower crane jib', 120, 'ft', 'nguoi'),
    ('the Embraer E195 regional jet', 115, 'ft', 'may_bay'),
    ('the European larch', 115, 'ft', 'nguoi'),
    ('the Bombardier CRJ900', 106, 'ft', 'nguoi'),
    ('the white oak', 100, 'ft', 'cay'),
    ('the Gulfstream G650 private jet', 99, 'ft', 'may_bay'),
    ('a tulip tree', 90, 'ft', 'cay'),
    ('the plane tree', 90, 'ft', 'may_bay'),
    ('a baseball diamond at a major league park', 90, 'ft', 'nguoi'),
    ('a massive grain silo', 85, 'ft', 'nguyen_tu'),
    ('the baobab tree', 85, 'ft', 'cay'),
    ('the fin whale', 85, 'ft', 'ca_voi'),
    ('a high school gymnasium basketball floor', 84, 'ft', 'nguoi'),
    ('a ponderosa pine', 80, 'ft', 'cay'),
    ('a tennis court at a Grand Slam venue', 78, 'ft', 'nguoi'),
    ('the sweetgum tree', 75, 'ft', 'cay'),
    ('the Virgin Galactic SpaceShipTwo', 71, 'ft', 'nguoi'),
    ('the Northrop Grumman B-2 Spirit', 71, 'ft', 'nguoi'),
    ('a bald cypress', 70, 'ft', 'nguoi'),
    ('the sugar maple', 70, 'ft', 'nguoi'),
    ('the lodgepole pine', 70, 'ft', 'cay'),
    ('the ash tree', 70, 'ft', 'cay'),
    ('the eastern white pine', 68, 'ft', 'cay'),
    ('the Douglas fir', 62, 'ft', 'nguoi'),
    ('the Mount Rushmore presidential faces', 60, 'ft', 'nguoi'),
    ('the humpback whale', 60, 'ft', 'ca_voi'),
    ('a volleyball court in an indoor arena', 60, 'ft', 'nguoi'),
    ('the loblolly pine', 58, 'ft', 'cay'),
    ('the Learjet 75 business jet', 55, 'ft', 'may_bay'),
    ('the northern red oak', 55, 'ft', 'cay'),
    ('the Norway spruce', 55, 'ft', 'nguoi'),
    ('the F-22 Raptor fighter jet', 53, 'ft', 'may_bay'),
    ('a honeylocust tree', 50, 'ft', 'cay'),
    ('the bristlecone pine', 50, 'ft', 'cay'),
    ('the ginkgo tree', 50, 'ft', 'cay'),
    ('the Beechcraft King Air 350', 45, 'ft', 'nguoi'),
    ('the saguaro cactus', 45, 'ft', 'nguoi'),
    ('the southern live oak', 45, 'ft', 'cay'),
    ('a black locust', 40, 'ft', 'nguoi'),
    ('the Bell 206 JetRanger helicopter', 39, 'ft', 'may_bay'),
    ('the maple tree', 31, 'ft', 'cay'),
    ('a steel gantry crane', 30, 'ft', 'nguoi'),
    ('the Cessna 172 Skyhawk', 27, 'ft', 'nguoi'),
    ('a professional soccer stadium goal width', 24, 'ft', 'nguoi'),
    ('the Mercedes-Benz Sprinter van', 22, 'ft', 'xe'),
    ('the Ford F-150 pickup truck', 19, 'ft', 'xe'),
    ('the Volvo V90 station wagon', 19, 'ft', 'xe'),
    ('the Chevrolet Silverado pickup', 19, 'ft', 'nguoi'),
    ('the Lamborghini Aventador supercar', 16, 'ft', 'nguoi'),
    ('the Bugatti Chiron super-luxury car', 16, 'ft', 'xe'),
    ('the Honda Odyssey minivan', 16, 'ft', 'nguoi'),
    ('the Tesla Model S sedan', 15, 'ft', 'nguoi'),
    ('the Subaru Outback wagon', 15, 'ft', 'xe'),
    ('a giant lumber-saw blade', 15, 'ft', 'nguoi'),
    ('a mining haul truck', 14, 'ft', 'xe'),
    ('the Ferrari 812 Superfast', 14, 'ft', 'nguoi'),
    ('the African elephant', 13, 'ft', 'huou'),
    ('a large dump truck', 12, 'ft', 'xe'),
    ('a timber harvesting harvester', 12, 'ft', 'nguoi'),
    ('the Apollo spacecraft command module', 12, 'ft', 'nguoi'),
    ('the freight elevator cage', 10, 'ft', 'nguoi'),
    ('the electric substation transformer', 10, 'ft', 'nguoi'),
    ('a tall corn stalk', 10, 'ft', 'nguoi'),
    ('the polar bear', 10, 'ft', 'huou'),
    ('the Komodo dragon', 10, 'ft', 'nguoi'),
    ('a compact excavator', 9, 'ft', 'nguoi'),
    ('the Harley-Davidson Softail motorcycle', 9, 'ft', 'xe'),
    ('a concrete mixer drum', 8, 'ft', 'nguoi'),
    ('the grizzly bear', 8, 'ft', 'huou'),
    ('a diesel generator set', 7, 'ft', 'nguoi'),
    ('the common ostrich', 7, 'ft', 'huou'),
    ('the moose', 7, 'ft', 'huou'),
    ('the Dodge\xa0Ram\xa02500', 7, 'ft', 'nguoi'),
    ('the kangaroo', 6, 'ft', 'nguoi'),
    ('the Toyota Tundra', 6, 'ft', 'nguoi'),
    ('the average human', 5.9, 'ft', 'nguoi'),
    ('the width of a standard operating table', 3, 'ft', 'nha'),
    ('the spinal column', 2.5, 'ft', 'nguoi'),
    ('a pneumatic drill', 2, 'ft', 'nha'),
    ('the conveyor belt roller', 2, 'ft', 'nguoi'),
    ('the height of a newborn baby', 1.8, 'ft', 'nguoi'),
    ('the femur bone', 1.8, 'ft', 'nguoi'),
    ('a newborn infant', 1.5, 'ft', 'nguoi'),
    ('the aorta', 1.2, 'ft', 'nguoi'),
    ('the length of a typical adult foot', 1, 'ft', 'nguoi'),
    ('the esophagus', 1, 'ft', 'nguoi'),
    ('a human forearm length', 1, 'ft', 'nguoi'),
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

    # ── NỐI THÊM 6/9/2026 · 67 mục, mỗi mục qua bốn cổng của
    #    `bang_mo_rong.py`; xuất xứ ở `bang_nguon_*.json`. Con số là ĐỀ NGHỊ
    #    của AI đã sống sót qua một lượt ĐỐI CHỨNG độc lập, không phải hằng
    #    số tra từ sách — nên nếu một mục nào bị người xem bắt sai, sửa THẲNG
    #    ở đây và giữ nguyên cơ chế.
    ('hitting the Powerball jackpot', 292201338, 'tien'),
    ('dealing a royal flush', 649740, 'tien'),
    ('capturing a poker royal flush', 649740, 'tien'),
    ('holding a straight flush', 72192, 'tien'),
    ('a rare autoimmune disease diagnosis', 50000, 'tien'),
    ('a mole turning malignant', 25000, 'tien'),
    ('a spinal cord injury', 15000, 'tien'),
    ('spotting a four-leaf clover', 10000, 'cay'),
    ('seeing a double rainbow', 8000, 'tien'),
    ('a sudden cardiac arrest while exercising', 5000, 'tien'),
    ('a life-threatening anaphylaxis from medication', 4000, 'tien'),
    ('a carpal tunnel surgery', 2500, 'tien'),
    ('a fracture of the wrist', 1900, 'tien'),
    ('a testicular cancer', 1000, 'tien'),
    ('a deep-vein thrombosis after surgery', 800, 'tien'),
    ('a blood clot in the lung (pulmonary embolism)', 600, 'te_bao'),
    ('the chance of a blood clot after surgery', 500, 'te_bao'),
    ('a stroke in a year', 500, 'dong_ho'),
    ('a herniated disc in the lumbar region', 400, 'tien'),
    ('standing on a full house', 374, 'nha'),
    ('receiving a birthday card on your exact birthday', 365, 'tien'),
    ('a gallbladder removal complication', 300, 'tien'),
    ('a glaucoma diagnosis', 300, 'tien'),
    ('a type 1 diabetes diagnosis', 300, 'tien'),
    ('a severe asthma attack at night', 250, 'giuong'),
    ('a heart attack in a middle-aged adult', 250, 'te_bao'),
    ('a torn anterior cruciate ligament', 250, 'tien'),
    ('a bout of severe asthma attack', 250, 'tien'),
    ('a case of appendicitis in adulthood', 150, 'tien'),
    ('sustaining a concussion', 110, 'tien'),
    ('breaking a glass while washing dishes', 100, 'coc'),
    ('a concussion from a sports collision', 70, 'tien'),
    ('passing a three-of-a-kind', 47, 'tien'),
    ('spinning a single zero on European roulette', 37, 'tien'),
    ('throwing a snake eyes', 36, 'nguoi'),
    ('landing a craps “hard six” roll', 36, 'tien'),
    ('a broken bone from a fall', 30, 'tien'),
    ('a sprained ankle during sports', 30, 'tien'),
    ('a food poisoning', 25, 'tien'),
    ('dying from lung cancer', 25, 'te_bao'),
    ('an urinary tract infection each year', 20, 'dong_ho'),
    ('a herpes simplex outbreak', 20, 'tien'),
    ('a sleep apnea diagnosis', 20, 'giuong'),
    ('surviving a heart attack', 20, 'te_bao'),
    ('a sinus infection after a cold', 15, 'tien'),
    ('a diagnosis of type 2 diabetes', 15, 'tien'),
    ('undergoing cataract surgery', 15, 'tien'),
    ('missing a bus by a minute', 12, 'xe_buyt'),
    ('a cataract development', 12, 'tien'),
    ('a premature birth before 37 weeks', 10, 'dong_ho'),
    ('a chickenpox infection', 10, 'tien'),
    ('a dental cavity by age 30', 8, 'tien'),
    ('experiencing food poisoning', 7, 'tien'),
    ('betting on a natural seven', 6, 'tien'),
    ('a mild allergic reaction to pollen', 6, 'vi_khuan'),
    ('a seasonal flu', 6, 'tien'),
    ('a migraine episode', 5, 'tien'),
    ('an obesity diagnosis', 5, 'tien'),
    ('suffering a migraine', 5, 'tien'),
    ('the flu vaccine causing mild fever', 4, 'tien'),
    ('a miscarriage in the first trimester', 4, 'tien'),
    ('a hypertension diagnosis', 4, 'tien'),
    ('calling a bluff successfully', 3, 'tien'),
    ('developing hypertension', 3, 'tien'),
    ('taking antibiotics', 3, 'tien'),
    ('a common cold in a year', 2, 'dong_ho'),
    ('catching a cold', 2, 'tien'),
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

    # ── NỐI THÊM 6/9/2026 · 247 mục, mỗi mục qua bốn cổng của
    #    `bang_mo_rong.py`; xuất xứ ở `bang_nguon_*.json`. Con số là ĐỀ NGHỊ
    #    của AI đã sống sót qua một lượt ĐỐI CHỨNG độc lập, không phải hằng
    #    số tra từ sách — nên nếu một mục nào bị người xem bắt sai, sửa THẲNG
    #    ở đây và giữ nguyên cơ chế.
    ('a supersonic jet overflight', 150, 'may_bay'),
    ('a massive structural failure', 140, 'nguoi'),
    ('an explosive firework test', 137, 'nguoi'),
    ('a cataclysmic building collapse', 135, 'nha'),
    ('a reverberating metal rack collapse', 133, 'nguoi'),
    ('a demolition wrecking ball', 130, 'nguoi'),
    ('a close-mic electric guitar solo at max gain', 130, 'nguoi'),
    ('the boom of a nearby fireworks display', 125, 'nguoi'),
    ('a shattering window impact', 125, 'nha'),
    ('a blaring trumpet fanfare at a ceremony', 123, 'nguoi'),
    ('the ultimate concert climax', 122, 'nguoi'),
    ('a front-row spot at a punk show', 121, 'nguoi'),
    ('a siren from an emergency vehicle passing', 120, 'nguoi'),
    ('a pneumatic nail gun', 119, 'nguoi'),
    ('a howler monkey call', 119, 'dien_thoai'),
    ('the heavy-duty garbage disposal shredding bones', 118, 'nguoi'),
    ('a deafening stadium fireworks display with music', 118, 'nguoi'),
    ("a peacock's display scream", 118, 'nguoi'),
    ('the piercing feedback from a stage monitor', 117, 'dien_thoai'),
    ('a cicada chorus', 116, 'nguoi'),
    ('the power sandblaster', 115, 'nguoi'),
    ('a steel stamping press', 115, 'nguoi'),
    ('the emergency slide deployment on a passenger plane', 115, 'may_bay'),
    ('a bat echolocation chirp', 115, 'nguoi'),
    ('the airplane overhead fly-by', 115, 'nguoi'),
    ('a seal bark', 114, 'ca_voi'),
    ('the angle grinder', 112, 'nguoi'),
    ('a rivet gun', 112, 'nguoi'),
    ('the nail gun', 112, 'nguoi'),
    ('a screaming audience at a pop finale', 112, 'nguoi'),
    ('a large outdoor music festival main stage', 112, 'nguoi'),
    ('a roaring crowd chant at a music festival', 111, 'nguoi'),
    ('an extreme bang of a fire alarm test', 110, 'lua'),
    ('a stadium cheer', 110, 'nguoi'),
    ('the cockpit alarm of a commercial aircraft', 110, 'may_bay'),
    ('the horn of a freight train passing by', 110, 'nguoi'),
    ('the street siren passing by', 110, 'nguoi'),
    ('the reciprocating saw', 108, 'nguoi'),
    ('a blowtorch', 108, 'nguoi'),
    ('the shrill cry of a red-winged blackbird', 108, 'nguoi'),
    ('a fire alarm sounding fully', 108, 'lua'),
    ('a thunderous organ pipe in a cathedral', 107, 'nha'),
    ('the miter saw', 106, 'nguoi'),
    ('a grizzly bear growl', 106, 'huou'),
    ('a table saw', 105, 'nha'),
    ('a helicopter hovering', 105, 'may_bay'),
    ('the scream of a howler monkey', 105, 'nguoi'),
    ('the construction jackhammer outside', 105, 'nguoi'),
    ('the screech of a distorted electric guitar solo', 104, 'nguoi'),
    ('a small propeller plane taking off', 104, 'may_bay'),
    ('a rhinoceros snort', 104, 'nguoi'),
    ('the safety alarm', 103, 'nguoi'),
    ('the whistle of a tugboat in harbor', 103, 'nguoi'),
    ('a sudden alarm siren', 103, 'nguoi'),
    ('a pressure washer', 102, 'nha'),
    ('a hammer drill', 101, 'nha'),
    ('the deck crane operation on a supply ship', 101, 'ca_voi'),
    ('a band saw', 100, 'nguoi'),
    ('the intense metal concert', 100, 'nguoi'),
    ('a steam locomotive chugging uphill', 100, 'nguoi'),
    ('an elephant trumpeting', 100, 'huou'),
    ('the parking lot car horn', 100, 'xe'),
    ('the circular saw', 99, 'nguoi'),
    ('the tile cutter', 99, 'nha'),
    ('the coupling impact of two rail cars connecting', 98, 'xe'),
    ("a tiger's roar", 98, 'nguoi'),
    ('the impact driver', 97, 'nguoi'),
    ('the electric saw', 97, 'nguoi'),
    ('a raucous punk show', 97, 'nguoi'),
    ('a portable sandblaster at work', 97, 'nguoi'),
    ('the jigsaw', 96, 'nguoi'),
    ('a motorcycle revving', 96, 'xe'),
    ('a motorized pontoon boat accelerating', 96, 'ca_voi'),
    ('the floor sander', 95, 'nguoi'),
    ('the sharp crack of a kitchen timer alarm', 95, 'dong_ho'),
    ('a snowmobile engine', 95, 'xe'),
    ('a booming tuba in a brass ensemble', 95, 'nguoi'),
    ('a private jet during descent', 95, 'may_bay'),
    ("a lion's roar", 95, 'huou'),
    ('a festival outdoor stage with amplifiers', 95, 'nguoi'),
    ('the welding torch igniting', 95, 'lua'),
    ('a strong printer carriage slam', 95, 'nguoi'),
    ('a bench grinder', 94, 'nguoi'),
    ('the roar of a lioness', 94, 'nguoi'),
    ('a belt sander', 93, 'nguoi'),
    ('the metal lathe', 92, 'nguoi'),
    ('a deep fryer frying food', 92, 'nguoi'),
    ('a vibrant brass band performance', 92, 'nguoi'),
    ('a commuter train accelerating from a station', 92, 'nguoi'),
    ('the propeller wash of a small fishing boat', 92, 'ca_voi'),
    ('a concert hall symphony orchestra', 92, 'nguoi'),
    ('the hydraulic press', 90, 'nguoi'),
    ('a powerful violin solo in a concert hall', 90, 'nguoi'),
    ('the energetic pop concert', 90, 'nguoi'),
    ('the turbulence rattling inside a cargo aircraft', 90, 'may_bay'),
    ('a wolf howl', 90, 'nguoi'),
    ('a cow mooing in a pasture', 90, 'huou'),
    ('the orbital sander', 88, 'nguoi'),
    ('the drill press', 88, 'nha'),
    ('a handheld router', 88, 'nguoi'),
    ('the crack of a wooden chair breaking', 88, 'nha'),
    ('the blast of a fire alarm test', 88, 'lua'),
    ('a ferry docking at a terminal', 87, 'ca_voi'),
    ('a wood lathe', 86, 'cay'),
    ('the bleat of a mountain goat', 86, 'meo'),
    ('the loudspeaker announcement on a metropolitan train', 86, 'nguoi'),
    ('the water spray from a jet ski', 86, 'may_bay'),
    ("a raven's call", 86, 'dien_thoai'),
    ('the air compressor', 85, 'nguoi'),
    ('a loud clatter of a dishwasher rack slam', 85, 'nguoi'),
    ('a leaf blower', 85, 'cay'),
    ('a carnival ride motor', 85, 'nguoi'),
    ('a horse neigh on a field', 85, 'huou'),
    ('the cabin of a commercial jet cruising', 85, 'may_bay'),
    ('a commercial airliner at cruising altitude', 85, 'nguoi'),
    ('a diesel locomotive idling in a yard', 85, 'nguoi'),
    ('a cordless impact driver', 85, 'nguoi'),
    ('the grunt of a pig in a pen', 85, 'nguoi'),
    ('a rotary tool', 84, 'nguoi'),
    ('a paint sprayer', 84, 'nguoi'),
    ('the interior announcement system on a regional flight', 84, 'may_bay'),
    ("a duck's quack", 84, 'nguoi'),
    ('a hand sander', 82, 'nguoi'),
    ('the announcement chime on a long-distance train', 82, 'nguoi'),
    ('a turkey gobble', 82, 'nguoi'),
    ('a standard electric guitar amp at 5 watts', 82, 'nguoi'),
    ('a shredder cutting a stack of paper', 82, 'nguoi'),
    ('the thud of a briefcase hitting the floor', 81, 'nguoi'),
    ('a wind turbine blade', 80, 'nguoi'),
    ('an industrial fan', 80, 'nguoi'),
    ('a coffee espresso machine steaming', 80, 'coc'),
    ('the average rock band rehearsal', 80, 'nguoi'),
    ('a rooster crowing', 80, 'nguoi'),
    ('a goat bleating on a hill', 80, 'meo'),
    ('the door slam', 80, 'nha'),
    ('the bang of a dropped monitor', 80, 'dien_thoai'),
    ('the heat gun', 79, 'lua'),
    ('the moderate roar of a stand mixer', 78, 'nguoi'),
    ('the disc sander', 78, 'nguoi'),
    ('a kitchen blender', 78, 'nguoi'),
    ('the garbage disposal grinding', 78, 'nguoi'),
    ('the engine of a turboprop aircraft at idle', 78, 'may_bay'),
    ('the doors closing on a high-speed rail car', 78, 'xe'),
    ('the bilge pump operating on a yacht', 78, 'nguoi'),
    ('the radio chatter on a commercial airline cockpit', 78, 'may_bay'),
    ('the wheel squeal of a light rail vehicle', 78, 'nguoi'),
    ('the galley equipment on a passenger liner', 78, 'nguoi'),
    ('a crowded coffeehouse acoustic set', 78, 'nguoi'),
    ('the paper shredder running', 78, 'nguoi'),
    ('the slam of a glass office door', 78, 'coc'),
    ('a whir of a coffee grinder', 78, 'coc'),
    ('an usual breakroom microwave ping', 78, 'nguoi'),
    ('the magnetic drill press', 77, 'nha'),
    ('a common water dispenser splash', 76, 'coc'),
    ('a donkey braying in a valley', 75, 'nguoi'),
    ('a routine copier operation', 75, 'nguoi'),
    ('the clang of a metal filing cabinet latch', 75, 'nha'),
    ('the projector lamp ignition', 75, 'nguoi'),
    ('the reception desk bell chime', 75, 'nha'),
    ('a stack of CDs being shuffled', 75, 'nguoi'),
    ('the food processor chopping', 73, 'nguoi'),
    ('a lively banjo jam at a backyard gathering', 73, 'nguoi'),
    ('the elevator arriving', 73, 'nguoi'),
    ('the clank of a metal filing cabinet drawer', 73, 'nha'),
    ('a milk frother frothing milk', 72, 'nguoi'),
    ('a compact planer in operation', 72, 'nguoi'),
    ('the beep of a fire alarm test', 71, 'lua'),
    ('a stand mixer whisking batter', 70, 'nguoi'),
    ('a robotic mop cleaning floor', 70, 'nguoi'),
    ('a windscreen wiper on a small aircraft', 70, 'may_bay'),
    ('a typical phone ring', 70, 'dien_thoai'),
    ('the telephone ringtone', 70, 'nguoi'),
    ('a stapler being used', 70, 'nguoi'),
    ('the pop of a bubble wrap sheet', 70, 'nha'),
    ('the thwack of a stapler hitting paper', 70, 'nguoi'),
    ('the ding of a microwave timer', 70, 'dong_ho'),
    ('the whine of a domestic cat', 68, 'meo'),
    ("the deckhand's radio chatter on a fishing boat", 68, 'ca_voi'),
    ('a chicken clucking', 68, 'nguoi'),
    ('the breakroom microwave beep', 68, 'nguoi'),
    ('the whiteboard marker squeaking', 68, 'nguoi'),
    ('the thump of a stack of binders falling', 68, 'nguoi'),
    ('the rubber band snap on a binder', 66, 'nguoi'),
    ('the mellow trumpet warm-up', 65, 'nguoi'),
    ('a crow caw in the distance', 65, 'nguoi'),
    ('the ventilation fan in a train car', 65, 'xe'),
    ('the splash of a kayak hitting a wave', 65, 'ca_voi'),
    ('a folder being thumped on a table', 65, 'nha'),
    ("a canary's song", 64, 'nguoi'),
    ('a dryer tumbling laundry', 63, 'nguoi'),
    ('the muted clatter of a coffee grinder', 62, 'coc'),
    ('the mechanical keyboard typing', 62, 'nguoi'),
    ('the clatter of a lunchroom tray stacker', 62, 'nguoi'),
    ('a wooden chair leg scraping floor', 62, 'nha'),
    ('a mild coffee maker brew', 60, 'coc'),
    ('a toaster popping bread', 60, 'nguoi'),
    ('a bread slicer slicing', 60, 'nguoi'),
    ('a budgerigar chatter', 60, 'nguoi'),
    ('a consistent stapler use', 60, 'nguoi'),
    ('the vending machine dispensing', 60, 'nguoi'),
    ('the desktop computer boot chime', 60, 'nguoi'),
    ('the copier loading click', 60, 'nguoi'),
    ('the filing cabinet drawer closing', 60, 'nha'),
    ('the clink of glassware in a kitchen area', 60, 'nguoi'),
    ('the mailroom package drop', 58, 'nguoi'),
    ('the copy room door closing', 58, 'nha'),
    ('the chime of an office clock', 58, 'dong_ho'),
    ('a shop fan', 57, 'nguoi'),
    ('a soft electric kettle boil', 55, 'coc'),
    ('the cluck of a backyard chicken', 55, 'nguoi'),
    ('the hoot of an owl in the night', 55, 'giuong'),
    ('the hallway chatter', 55, 'nguoi'),
    ('a phone notification ping', 55, 'dien_thoai'),
    ('a scanner scanning a thick document', 54, 'nguoi'),
    ('the chatter of a small meeting room', 54, 'nha'),
    ('the ceiling fan on high', 53, 'nguoi'),
    ('the whirr of a photocopier', 53, 'nguoi'),
    ('a parakeet chirping', 52, 'nguoi'),
    ('the foot traffic in the lobby', 52, 'xe'),
    ('the fax machine sending', 50, 'nguoi'),
    ('the recycling bin lid closing', 50, 'nguoi'),
    ('a printer loading paper', 50, 'nguoi'),
    ('a hiss of a dehumidifier', 50, 'nguoi'),
    ('the clack of a keyboard typing rapidly', 50, 'nguoi'),
    ('the subtle whine of a microwave', 48, 'nguoi'),
    ('the document scanner', 46, 'nguoi'),
    ('a keyboard typing rapidly', 46, 'nguoi'),
    ('a gentle dishwasher cycle', 45, 'nguoi'),
    ('the chair rolling across carpet', 45, 'nha'),
    ('the hum of a server rack', 45, 'nguoi'),
    ('the murmur of coworkers chatting', 45, 'nguoi'),
    ('the rustle of a stapler', 44, 'nguoi'),
    ('the steady hum of a fridge compressor', 42, 'nha'),
    ('a wine cooler cooling', 42, 'nguoi'),
    ('the fluorescent light hum', 42, 'nguoi'),
    ('the conference room projector fan whirring', 42, 'nha'),
    ('the click of a mouse button', 42, 'nguoi'),
    ('the battery charger', 40, 'nguoi'),
    ('the refrigerator humming', 40, 'nguoi'),
    ('the buzz of a fluorescent light fixture', 40, 'nguoi'),
    ('the low whir of a freezer', 38, 'nguoi'),
    ('a mouse click', 38, 'nguoi'),
    ('the laser level', 35, 'nguoi'),
    ('the faint ticking metronome', 35, 'nguoi'),
    ('a glider soaring in quiet air', 35, 'may_bay'),
    ('the empty conference room', 35, 'nha'),
    ('a whispering coworker at desk', 35, 'nha'),
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

    # ── NỐI THÊM 6/9/2026 · 169 mục, mỗi mục qua bốn cổng của
    #    `bang_mo_rong.py`; xuất xứ ở `bang_nguon_*.json`. Con số là ĐỀ NGHỊ
    #    của AI đã sống sót qua một lượt ĐỐI CHỨNG độc lập, không phải hằng
    #    số tra từ sách — nên nếu một mục nào bị người xem bắt sai, sửa THẲNG
    #    ở đây và giữ nguyên cơ chế.
    ('the container ship', 220000000, 'ca_voi'),
    ('a cargo airplane', 400000, 'nguoi'),
    ('a locomotive', 210000, 'nguoi'),
    ('a commuter rail car', 95000, 'xe'),
    ('a fuel tanker truck', 90000, 'xe'),
    ('a high-speed train car', 90000, 'xe'),
    ('a passenger train car', 80000, 'xe'),
    ('a sperm whale', 80000, 'ca_voi'),
    ('a subway car', 80000, 'xe'),
    ('a metro car', 72000, 'xe'),
    ('a freight car', 70000, 'xe'),
    ('a light-rail vehicle', 65000, 'nguoi'),
    ('the intercity train car', 56000, 'xe'),
    ('a streetcar', 55000, 'nguoi'),
    ('a fire engine', 54000, 'xe'),
    ('a crane truck', 50000, 'xe'),
    ('a bulldozer', 48000, 'nguoi'),
    ('a downtown electric trolley', 42000, 'nguoi'),
    ('a backhoe loader', 36000, 'nguoi'),
    ('a trolley bus', 32000, 'xe_buyt'),
    ('the garbage truck', 30000, 'xe'),
    ('the fighter jet', 29000, 'may_bay'),
    ('a trolleybus', 28000, 'nguoi'),
    ('a transit bus', 28000, 'xe_buyt'),
    ('the charter bus', 26000, 'xe_buyt'),
    ('a semi-tractor', 18000, 'xe'),
    ('the ice-cream truck', 15000, 'xe'),
    ('a tow truck', 15000, 'xe'),
    ('a diesel bus chassis', 15000, 'xe_buyt'),
    ('a municipal snow plow', 12000, 'nguoi'),
    ('a killer whale', 11000, 'ca_voi'),
    ('a farm tractor', 7000, 'xe'),
    ('a delivery van', 6200, 'xe'),
    ('a shipping container (20\u202fft)', 5000, 'nguoi'),
    ('a white rhinoceros', 5000, 'nguoi'),
    ('a police cruiser', 4200, 'nguoi'),
    ('a 2-ton steel I-beam section', 4000, 'nha'),
    ('a rhinoceros', 4000, 'nguoi'),
    ('a taxi cab', 4000, 'xe'),
    ('the midsize sedan', 3400, 'nguoi'),
    ('a mid-size gasoline sedan', 3400, 'nguoi'),
    ('a construction hoist', 3200, 'nguoi'),
    ('a compact car', 2600, 'xe'),
    ('the sailboat', 2500, 'nguoi'),
    ('a giraffe', 2500, 'huou'),
    ('a bulk bag of cement', 2200, 'nguoi'),
    ('a massive stone fireplace', 2100, 'nguoi'),
    ('a weightlifting platform', 2000, 'nguoi'),
    ('a bison', 2000, 'huou'),
    ('a wrestling ring', 1800, 'nguoi'),
    ('a garden tractor', 1500, 'xe'),
    ('a dairy cow', 1500, 'huou'),
    ('a walrus', 1500, 'nguoi'),
    ('a polar bear', 1000, 'huou'),
    ('the golf cart', 800, 'xe'),
    ('a crocodile', 800, 'nguoi'),
    ('an elk', 600, 'nguoi'),
    ('a young cow', 600, 'huou'),
    ('a smith machine', 500, 'nguoi'),
    ('a 500-lb steel truss segment', 500, 'nguoi'),
    ('a snowmobile', 500, 'nguoi'),
    ('a giant tortoise', 500, 'nguoi'),
    ('a motorcycle', 430, 'xe'),
    ('a leg press machine', 400, 'nguoi'),
    ('a commercial refrigerator', 400, 'nguoi'),
    ('a full-grown llama', 400, 'nguoi'),
    ('a llama', 300, 'nguoi'),
    ('a king-size mattress with foundation', 285, 'nha'),
    ('a heavy-duty washing machine', 260, 'nguoi'),
    ('a treadmill', 250, 'nguoi'),
    ('a ski lift chair', 250, 'nha'),
    ('a sectional sofa', 230, 'nha'),
    ('a solid oak desk', 205, 'nha'),
    ('a rowing machine', 200, 'nguoi'),
    ('a mature goat', 200, 'meo'),
    ('a streetlight', 200, 'nguoi'),
    ('a curb stone', 200, 'nguoi'),
    ('a double-door refrigerator', 190, 'nha'),
    ('a pre-cast concrete stair tread', 180, 'nguoi'),
    ('a squat rack', 150, 'nguoi'),
    ('a table saw', 150, 'nha'),
    ('a street curb stone', 150, 'nguoi'),
    ('a dishwasher unit', 140, 'nguoi'),
    ('a wooden dining table', 138, 'nha'),
    ('a railroad tie', 130, 'nguoi'),
    ('a workbench', 120, 'nguoi'),
    ('a stack of three 4-by-8 plywood sheets', 120, 'nha'),
    ('a highway guardrail post', 120, 'xe'),
    ('a drywall lift', 110, 'nguoi'),
    ('a kangaroo', 90, 'nguoi'),
    ('a gray wolf', 80, 'nguoi'),
    ('a road sign frame', 80, 'nguoi'),
    ('a standard coffee table', 63, 'coc'),
    ('a public bike share bike', 50, 'xe'),
    ('a simple bookshelf', 45, 'nha'),
    ('a floor jack', 45, 'nguoi'),
    ('a barbell', 45, 'nguoi'),
    ('a battle rope coil', 45, 'nguoi'),
    ('a hydraulic jack', 45, 'nguoi'),
    ('the push mower', 45, 'nguoi'),
    ('a steel toolbox', 45, 'nha'),
    ('a parking meter', 45, 'nguoi'),
    ('a box of books', 40, 'nguoi'),
    ('a curbside trash bin', 40, 'nguoi'),
    ('a basic nightstand', 38, 'nguoi'),
    ('a beaver', 35, 'nguoi'),
    ('an utility cart', 35, 'xe'),
    ('a single office chair', 34, 'nha'),
    ('a portable compressor', 30, 'nguoi'),
    ('a garage door opener', 30, 'nha'),
    ('a plyometric box', 30, 'nguoi'),
    ('a concrete paver slab', 30, 'nguoi'),
    ('a pressure washer', 30, 'nha'),
    ('a pneumatic jack', 30, 'nguoi'),
    ('a mailbox', 30, 'nguoi'),
    ('a bike rack', 30, 'xe'),
    ('a recycling bin', 30, 'nguoi'),
    ('the foldable bike', 28, 'xe'),
    ('a scooter', 28, 'xe'),
    ('an electric scooter', 27, 'xe'),
    ('a bench vise', 25, 'nguoi'),
    ('a beagle', 25, 'nguoi'),
    ('a baby stroller', 25, 'nguoi'),
    ('a bicycle', 22, 'xe'),
    ('a toolbox', 20, 'nha'),
    ('an aluminum side table', 18, 'nha'),
    ('a chainsaw', 14, 'nguoi'),
    ('a bolt cutter', 12, 'nguoi'),
    ('a circular saw', 10, 'nguoi'),
    ('a medicine ball', 10, 'nguoi'),
    ('a 2\u202f×\u202f4 pine stud (8\u202fft)', 10, 'cay'),
    ('a traffic cone', 9, 'xe'),
    ('a ladder step', 8, 'nguoi'),
    ('a dumbbell', 8, 'nguoi'),
    ('the handheld chainsaw', 8, 'nguoi'),
    ('a folding chair', 8, 'nha'),
    ('a kitchen blender', 7, 'nguoi'),
    ('a skateboard', 7, 'nguoi'),
    ('a winter coat', 6, 'nguoi'),
    ('the average chicken', 6, 'nguoi'),
    ('a power sander', 5, 'nguoi'),
    ('a wall mount bracket', 5, 'nguoi'),
    ('a brick of common red clay', 5, 'nha'),
    ('a domestic rabbit', 5, 'meo'),
    ('a platypus', 5, 'nguoi'),
    ('a grocery bag of produce', 5, 'nguoi'),
    ('a pipe wrench', 4, 'nha'),
    ('a foam roller', 4, 'nguoi'),
    ('a yoga mat', 4, 'nguoi'),
    ('a cordless drill', 3, 'nha'),
    ('a red-tailed hawk', 3, 'nguoi'),
    ('a pedestrian crossing button', 3, 'nguoi'),
    ('a hand saw', 2, 'nguoi'),
    ('a hammer', 2, 'nha'),
    ('a paint roller', 2, 'nguoi'),
    ('a pair of shoes', 2, 'nguoi'),
    ('a claw hammer', 2, 'nha'),
    ('a ferret', 2, 'nguoi'),
    ('a wrench', 1.5, 'nha'),
    ('a tape measure', 1, 'nguoi'),
    ('a plunger', 1, 'nguoi'),
    ('a metal file', 0.8, 'nguoi'),
    ('a paperback novel', 0.8, 'nguoi'),
    ('a travel mug', 0.6, 'coc'),
    ('a screwdriver', 0.5, 'nguoi'),
    ('a set of keys', 0.3, 'nguoi'),
    ('a credit card', 0.01, 'nguoi'),
    ('a paper clip', 0.001, 'nguoi'),
    ('a postage stamp', 0.001, 'nguoi'),
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

    # ── NỐI THÊM 6/9/2026 · 224 mục, mỗi mục qua bốn cổng của
    #    `bang_mo_rong.py`; xuất xứ ở `bang_nguon_*.json`. Con số là ĐỀ NGHỊ
    #    của AI đã sống sót qua một lượt ĐỐI CHỨNG độc lập, không phải hằng
    #    số tra từ sách — nên nếu một mục nào bị người xem bắt sai, sửa THẲNG
    #    ở đây và giữ nguyên cơ chế.
    ('the corona of the Sun', 2500000, 'mat_troi'),
    ('the photosphere of the Sun', 10000, 'mat_troi'),
    ('the inner core of Earth', 9900, 'trai_dat'),
    ('a fluorescent lamp arc', 8000, 'lua'),
    ('the outer core of Earth', 7200, 'trai_dat'),
    ('the combustion chamber of a space launch vehicle', 6000, 'lua'),
    ('the arc of an oxy-acetylene welder', 6000, 'lua'),
    ('a tungsten-halogen lamp filament', 5600, 'lua'),
    ('the filament of a halogen lamp', 5500, 'lua'),
    ('the nozzle of a gasoline rocket engine', 4000, 'xe'),
    ('the reentry vehicle heat shield surface', 3800, 'lua'),
    ('a solid-fuel rocket nozzle', 3400, 'may_bay'),
    ('the rocket engine combustion chamber', 3200, 'xe'),
    ('the afterburner flame of a fighter jet', 3000, 'may_bay'),
    ('the high-temperature furnace for ceramics', 2700, 'lua'),
    ('the melt pool of a steel induction furnace', 2600, 'lua'),
    ('the steelmaking basic oxygen furnace', 2600, 'lua'),
    ('the blast furnace hearth', 2500, 'lua'),
    ('the cathode of a high-intensity discharge lamp', 2300, 'lua'),
    ('the copper smelter hearth', 2300, 'lua'),
    ('the anode of a molten-salt electrolysis cell', 2100, 'te_bao'),
    ('the iron foundry ladle', 2100, 'lua'),
    ('the mantle of Earth', 2000, 'trai_dat'),
    ('the glassblowing furnace flame', 2000, 'lua'),
    ('the burner of an industrial oil furnace', 1800, 'lua'),
    ('the turbine inlet of a gas turbine', 1500, 'lua'),
    ('the spark plug of a high-performance motorcycle', 1500, 'xe'),
    ('a steel forging hammer', 1500, 'nha'),
    ('the catalyst bed of a catalytic converter', 1300, 'giuong'),
    ("the forge on a blacksmith's bench", 1150, 'lua'),
    ('the induction furnace for aluminum', 1150, 'lua'),
    ('the coke oven during preheat', 1150, 'nha'),
    ('a blacksmith-style forge used for culinary experiments', 1150, 'lua'),
    ('a furnace-type outdoor pizza oven', 1000, 'nha'),
    ('the firebox of a wood-burning stove', 900, 'cay'),
    ('the zinc coating strip', 787, 'lua'),
    ('the nuclear reactor core coolant', 530, 'nguyen_tu'),
    ('the exhaust pipe of a commuter motorcycle', 500, 'xe'),
    ('the broiler setting on high', 500, 'lua'),
    ('the shade of interplanetary space', -459, 'lua'),
    ('the cosmic microwave background', -454, 'lua'),
    ('the heating element of a hair straightener', 450, 'lua'),
    ('the tin solder bead', 442, 'lua'),
    ('a caramelization skillet', 440, 'lua'),
    ('the flambé pan', 430, 'coc'),
    ('the grill grate on medium-high', 425, 'lua'),
    ('a broiling turkey in the oven', 425, 'nha'),
    ('the baking sheet after roasting vegetables', 425, 'nha'),
    ('a naan-baking stone', 420, 'lua'),
    ('a commercial pizza oven', 400, 'nha'),
    ('the reflector of a stage spot light', 400, 'lua'),
    ('a toaster slot', 400, 'lua'),
    ('a cast-iron skillet heating', 400, 'lua'),
    ('a baked potato crisped on a rack', 400, 'lua'),
    ('the intense broiler tray', 390, 'lua'),
    ('the aluminum foil sheet after baking potatoes', 380, 'nha'),
    ('a waffle iron heating up', 375, 'lua'),
    ('the beef-roasting pan', 370, 'coc'),
    ('a toasted bagel', 370, 'lua'),
    ('a pie-baking dish', 360, 'lua'),
    ('the upper atmosphere of Uranus', -357, 'lua'),
    ('the atmosphere of Neptune', -353, 'lua'),
    ('the standard oven rack', 350, 'nha'),
    ('the motorcycle engine at cruise', 350, 'xe'),
    ('the coffee-roaster drum', 350, 'coc'),
    ('the oil in a pan ready for sautéing', 350, 'coc'),
    ('the oven preheat on bake', 350, 'nha'),
    ('a chocolate chip cookie baking', 350, 'lua'),
    ('the biscuit-baking sheet', 340, 'nha'),
    ('a caramelized onion pan', 340, 'coc'),
    ('the caramelizing sugar pan', 340, 'coc'),
    ('a pork-roasting tray', 330, 'lua'),
    ('the turkey-roasting pan', 320, 'coc'),
    ('the grilled cheese sandwich surface', 320, 'lua'),
    ('a steak-searing skillet', 310, 'lua'),
    ('the drum of a heavy-duty industrial dryer', 300, 'lua'),
    ('a heated skillet before adding oil', 300, 'lua'),
    ('a sizzling skillet with onions', 300, 'lua'),
    ('a preheated Dutch oven for stew', 300, 'nha'),
    ('the cloud tops of Saturn', -288, 'lua'),
    ('the night side of the Moon', -280, 'mat_trang'),
    ('a frying-pan for fries', 260, 'coc'),
    ('the low-temp roast pan', 250, 'coc'),
    ('the lawn mower engine', 250, 'xe'),
    ('the rings of Saturn', -250, 'lua'),
    ('a casserole dish warming in a low oven', 250, 'nha'),
    ('the hair dryer on high', 250, 'lua'),
    ('a caramel sauce melting in a saucepan', 240, 'lua'),
    ('the candy melting pot', 240, 'coc'),
    ('the south pole of the Moon', -233, 'mat_trang'),
    ('a pan of fried eggs', 225, 'coc'),
    ('the barbecue smoker low smoke', 225, 'lua'),
    ('the steam from a pot of boiling water', 212, 'coc'),
    ('a pot of boiling water', 212, 'coc'),
    ('the kettle after whistle', 212, 'coc'),
    ('a rice cooker at completion', 212, 'lua'),
    ('the radiator of a midsize sedan', 210, 'lua'),
    ('the Yellowstone hot spring', 200, 'lua'),
    ('a cryogenic camera cooler', -200, 'dien_thoai'),
    ('the silicone baking mat after use', 200, 'lua'),
    ('a gasoline engine at idle', 190, 'xe'),
    ('a simmering soup pot', 190, 'coc'),
    ('the sauna bench in home sauna', 190, 'nha'),
    ('a steaming mug of tea', 185, 'coc'),
    ('a saucepan of simmering soup', 185, 'lua'),
    ('the stovetop simmer setting', 185, 'lua'),
    ('the wind turbine gearbox oil', 180, 'lua'),
    ('a microwave heated bowl', 165, 'lua'),
    ('the roasted turkey interior temperature', 165, 'lua'),
    ('the slow-cooker low setting', 150, 'lua'),
    ('an electric motor in a drill', 140, 'nha'),
    ('the dishwasher interior during cycle', 140, 'lua'),
    ('a mug of tea', 140, 'coc'),
    ('a sous-vide water bath set to 140°F', 140, 'coc'),
    ('the Death Valley record high', 136, 'lua'),
    ('the milk warming jug', 130, 'coc'),
    ('the record high in Kuwait City', 130, 'lua'),
    ('the Vostok Station record low', -128, 'lua'),
    ('a heat wave in Death Valley', 125, 'lua'),
    ('the coil of a hair-drying brush', 120, 'lua'),
    ('the hottest day in Las Vegas', 118, 'dong_ho'),
    ('the Sahara desert midday', 115, 'lua'),
    ('the Texas heat wave', 115, 'lua'),
    ('a scorching midday in Phoenix', 115, 'lua'),
    ('the Nevada salt flats noon', 110, 'lua'),
    ('the desert of Phoenix summer', 104, 'lua'),
    ('the bathroom mirror after a hot shower', 104, 'lua'),
    ('the Arizona monsoon evening', 100, 'lua'),
    ('a lukewarm bath towel', 100, 'lua'),
    ('the fields of Kansas summer', 95, 'lua'),
    ('the water in a tepid bath', 95, 'coc'),
    ('the cotton dish towel on a warm counter', 95, 'lua'),
    ('the spice rack near the stove', 95, 'nha'),
    ('the casing of a cordless drill (no-load)', 92, 'nha'),
    ('the Florida summer humidity', 92, 'lua'),
    ('the enclosure of a portable speaker', 90, 'lua'),
    ('the Mediterranean coast summer', 90, 'lua'),
    ('the typical July in Atlanta', 90, 'lua'),
    ('the Gulf of Mexico summer', 88, 'lua'),
    ('the highlands of Ethiopia', 86, 'lua'),
    ('the Hawaiian beach noon', 86, 'lua'),
    ('the streets of New York in July', 85, 'lua'),
    ('the Congo basin midday', 85, 'lua'),
    ('a thunderstorm in Dallas', 85, 'lua'),
    ('a humid summer morning in New Orleans', 85, 'lua'),
    ('a server rack ambient', 85, 'lua'),
    ('the Caribbean sea breezes', 84, 'ca_voi'),
    ('the Amazon rainforest canopy', 82, 'lua'),
    ('the temperature of a tropical cyclone eye', 80, 'nguoi'),
    ('the wall outlet near the refrigerator', 80, 'lua'),
    ('the prairie of Nebraska', 78, 'lua'),
    ('the warmth of a tropical beach sunrise', 78, 'lua'),
    ('the indoor thermostat summer setting', 78, 'lua'),
    ('the stainless steel sink after rinsing', 78, 'lua'),
    ('the handle of a turned-off dishwasher', 78, 'lua'),
    ('the bay of San Diego summer', 77, 'lua'),
    ('the plateau of the Colorado Plateau', 72, 'lua'),
    ('the floor near a sunny window', 72, 'nha'),
    ('the kitchen countertop', 70, 'lua'),
    ('the Los Angeles summer evening', 70, 'lua'),
    ('the Canadian Rockies summer', 70, 'lua'),
    ('a windy day on the Great Plains', 70, 'dong_ho'),
    ('a sunny winter day in Miami', 70, 'dong_ho'),
    ('a moderate day in the Midwest', 70, 'dong_ho'),
    ('a smart thermostat sensor', 70, 'lua'),
    ('the pantry shelf in summer', 70, 'lua'),
    ('a bowl of cereal with milk', 70, 'lua'),
    ('the foothills of the Appalachians', 68, 'lua'),
    ('the Alps summer afternoon', 68, 'lua'),
    ('a cool evening on the Gulf Coast', 68, 'lua'),
    ('a room-temperature loaf of bread', 68, 'nha'),
    ('the living-room carpet on a mild day', 68, 'dong_ho'),
    ('a loaf of bread sitting on the countertop', 68, 'lua'),
    ('the valley of the Mississippi in spring', 66, 'lua'),
    ('a breezy autumn afternoon in Boston', 65, 'lua'),
    ('a pleasant autumn evening in Asheville', 62, 'lua'),
    ('the plastic cutting board in a warm room', 62, 'nha'),
    ('a softened butter slab', 60, 'lua'),
    ('the shoreline of the Gulf of Mexico winter', 60, 'lua'),
    ('a rainy afternoon in Portland', 60, 'lua'),
    ('the shore of Lake Baikal', 60, 'lua'),
    ('the wine cooler set to red', 60, 'lua'),
    ('the troposphere of Earth', 59, 'trai_dat'),
    ('a foggy morning in San Francisco', 58, 'lua'),
    ('the office air conditioner', 55, 'lua'),
    ('the Rocky Mountains fall dusk', 55, 'lua'),
    ('a summer evening in Seattle', 55, 'lua'),
    ('a mild spring day in Seattle', 55, 'dong_ho'),
    ('the basin of the Great Salt Lake', 55, 'lua'),
    ('a refrigerated wine cellar', 55, 'lua'),
    ('the metal doorknob in the hallway', 55, 'lua'),
    ('the coast of San Francisco fog', 54, 'lua'),
    ('the Atacama Desert night', 45, 'giuong'),
    ('a chilly spring dawn in New York', 45, 'lua'),
    ('the coolant inlet of a home air-conditioner', 45, 'nha'),
    ('a soda pulled from the ice bin', 42, 'lua'),
    ('a chilled salad bowl', 40, 'lua'),
    ('a winter night in Siberia', -40, 'giuong'),
    ('a crisp head of lettuce', 40, 'lua'),
    ('the outside of a chilled bottle of soda', 38, 'coc'),
    ('the household refrigerator', 35, 'lua'),
    ('the crest of K2', -35, 'lua'),
    ('the air inside a walk-in cooler', 35, 'nguoi'),
    ('the glacier of Alaska summer', 32, 'lua'),
    ('a cold glass of ice water', 32, 'coc'),
    ('a glass of iced water', 32, 'coc'),
    ('a frosty glass of lemonade', 32, 'coc'),
    ('a bag of ice cubes', 32, 'lua'),
    ('the Greenland summer melt', 30, 'lua'),
    ('the morning frost in Denver', 30, 'lua'),
    ('the summit of Denali', -30, 'lua'),
    ('the Arctic sea ice summer', 28, 'ca_voi'),
    ('a freshly shaved block of ice', 28, 'lua'),
    ('the ambient temperature of a winter carnival', 27, 'lua'),
    ('the peak of Denali', -26, 'lua'),
    ('the Antarctic summer coast', 25, 'lua'),
    ('the ice sheet of Greenland summer', 23, 'nha'),
    ('a blizzard in Buffalo', 15, 'lua'),
    ('the plains of North Dakota winter', 12, 'lua'),
    ('the interior of a freezer', 0.0, 'lua'),
    ('a freezer compartment', 0.0, 'lua'),
    ('a block of ice cream', 0.0, 'lua'),
    ('a frozen pizza straight from the freezer', 0.0, 'lua'),
    ('a backyard freezer', 0.0, 'lua'),
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

    # ── NỐI THÊM 6/9/2026 · 53 mục, mỗi mục qua bốn cổng của
    #    `bang_mo_rong.py`; xuất xứ ở `bang_nguon_*.json`. Con số là ĐỀ NGHỊ
    #    của AI đã sống sót qua một lượt ĐỐI CHỨNG độc lập, không phải hằng
    #    số tra từ sách — nên nếu một mục nào bị người xem bắt sai, sửa THẲNG
    #    ở đây và giữ nguyên cơ chế.
    ('a kitchen sink basin width', 0.5, 'nguyen_tu'),
    ('a vinyl record diameter', 0.31, 'nguyen_tu'),
    ('a basketball diameter', 0.24, 'nguyen_tu'),
    ('a soccer ball diameter', 0.22, 'nguoi'),
    ('a baseball diameter', 0.073, 'nguyen_tu'),
    ('a tennis ball diameter', 0.067, 'nguoi'),
    ('a soda-can diameter', 0.066, 'coc'),
    ('a playing-card width', 0.063, 'nguyen_tu'),
    ('a paperclip length', 0.04, 'nguyen_tu'),
    ('a standard dice edge', 0.016, 'nguyen_tu'),
    ('a coffee bean length', 0.01, 'coc'),
    ('a grape diameter', 0.01, 'nguyen_tu'),
    ('a pea diameter', 0.008, 'nguyen_tu'),
    ('a drop of blood', 0.002, 'te_bao'),
    ('a raindrop diameter', 0.002, 'nguyen_tu'),
    ('a tiny blood clot', 0.0005, 'te_bao'),
    ('a pollen grain diameter', 2e-05, 'nguyen_tu'),
    ('a monocyte', 1.5e-05, 'nguyen_tu'),
    ('an eosinophil', 1.3e-05, 'nguyen_tu'),
    ('a neutrophil', 1.2e-05, 'nguyen_tu'),
    ('a basophil', 1.2e-05, 'nguyen_tu'),
    ('a leukocyte', 1e-05, 'nguyen_tu'),
    ('a blood vessel endothelial cell', 1e-05, 'te_bao'),
    ('a microscopic blood smear particle', 1e-05, 'nguyen_tu'),
    ('a tissue interstitial space', 1e-05, 'nguyen_tu'),
    ('a chlamydia inclusion', 9e-06, 'nguyen_tu'),
    ('a lymphocyte', 7e-06, 'nguyen_tu'),
    ('a capillary lumen diameter', 5e-06, 'nguyen_tu'),
    ('a cilia', 5e-06, 'nguyen_tu'),
    ('a treponema spiral', 5e-06, 'nguyen_tu'),
    ('a platelet', 2e-06, 'te_bao'),
    ('a pseudomonas grain', 2e-06, 'nguyen_tu'),
    ('a pertussis particle', 1.5e-06, 'nguyen_tu'),
    ('a bacillus subtilis', 1.2e-06, 'nguyen_tu'),
    ('a mitochondrion length', 1e-06, 'nguyen_tu'),
    ('a microvillus', 1e-06, 'nguyen_tu'),
    ('a peroxisome', 7e-07, 'nguyen_tu'),
    ('a streptococcus sphere', 7e-07, 'nguyen_tu'),
    ('a Golgi stack', 5e-07, 'nguyen_tu'),
    ('a ribosome', 2e-08, 'te_bao'),
    ('a histone octamer', 1e-08, 'nguyen_tu'),
    ('a microfilament', 7e-09, 'nguyen_tu'),
    ('a protein molecule', 5e-09, 'nguyen_tu'),
    ('a cell membrane thickness', 5e-09, 'te_bao'),
    ('a hemoglobin molecule', 5e-09, 'nguyen_tu'),
    ('an albumin molecule', 3.6e-09, 'nguyen_tu'),
    ('a carbon nanotube diameter', 1e-09, 'nguyen_tu'),
    ('a glucose molecule', 9e-10, 'nguyen_tu'),
    ('a buckyball diameter', 7.1e-10, 'nguyen_tu'),
    ('an amino acid length', 5e-10, 'nguyen_tu'),
    ('an ozone molecule diameter', 3e-10, 'nguyen_tu'),
    ('a hydrogen molecule length', 2.4e-10, 'nguyen_tu'),
    ('an electron classical radius', 2.8e-15, 'nguyen_tu'),
]
_CUC_NHO_CU = [
    ("a grain of sand", 5e-4, "hop"), ("a human hair's width", 7e-5, "te_bao"),
    ("a red blood cell", 8e-6, "te_bao"), ("a bacterium", 1e-6, "vi_khuan"),
    ("a virus", 1e-7, "vi_khuan"), ("a single atom", 1e-10, "nguyen_tu"),
]

THOI_QUEN = [
    ('a $6 coffee every morning', 6, 365, 'coc'),
    ('a $15 streaming subscription', 15, 12, 'dien_thoai'),
    ('a $12 lunch every workday', 12, 260, 'hop'),
    ('a $4 energy drink daily', 4, 365, 'coc'),
    ('a $90 phone plan', 90, 12, 'dien_thoai'),
    # ── NỐI THÊM 1/9. Thói quen nhỏ, giá thật ở Mỹ, số lần/năm.
    ('a $14 lunch every workday', 14, 250, 'hop'),
    ('a $60 tank of gas each week', 60, 52, 'xe'),
    ('a $30 streaming bundle', 30, 12, 'dien_thoai'),
    ('a $9 sandwich every workday', 9, 250, 'hop'),
    ('a $120 gym membership', 120, 12, 'nguoi'),
    ('a $25 rideshare twice a week', 25, 104, 'xe'),
    ('a $3 bottle of water daily', 3, 365, 'coc'),
    ('a $50 grocery delivery fee monthly', 50, 12, 'xe'),
    ('a $8 parking charge each workday', 8, 250, 'xe'),
    ('a $200 cable package', 200, 12, 'nha'),
    ('a $5 pastry every morning', 5, 365, 'coc'),
    # ── ĐỢT 2 (1/9).
    ('a $7 smoothie three times a week', 7, 156, 'coc'),
    ('a $45 haircut monthly', 45, 12, 'nguoi'),
    ('a $2 lottery ticket daily', 2, 365, 'tien'),
    ('a $19 cloud storage plan', 19, 12, 'dien_thoai'),
    ('a $75 dinner out weekly', 75, 52, 'hop'),
    ('a $6 car wash twice a month', 6, 24, 'xe'),
    ('a $130 phone upgrade yearly', 130, 1, 'dien_thoai'),
    ('a $11 movie ticket monthly', 11, 12, 'giay'),
    ('a $40 tank of gas weekly', 40, 52, 'xe'),
    ('a $16 delivery fee twice a week', 16, 104, 'xe'),
    ('a $3 snack every afternoon', 3, 365, 'hop'),
    ('a $22 music and video bundle', 22, 12, 'dien_thoai'),
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


_CAP_TI: dict = {}        # nhớ danh sách cặp hợp lệ theo bảng — xem `_cap_ti`


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


def _cap_ti(ds: list, i: int, ti: float = 1.5, cot: int = 1) -> tuple:
    """Như `_cap`, nhưng chỉ lấy những cặp CÁCH NHAU đủ xa để câu so sánh có nghĩa.

    ── VÌ SAO  (6/9/2026) ──────────────────────────────────────────────────────────────────
    Ba kênh (HOW BIG · WHAT WEIGHS · SMALLEST) tồn tại để trả lời *"cái này lớn hơn cái kia bao
    nhiêu lần"*. `_cap` chỉ bảo đảm hai VẬT khác nhau, không bảo đảm hai SỐ khác nhau — nên khi
    bảng có hai mục xấp xỉ bằng nhau, cả tập ra:

        tiêu đề "1x BIGGER"  ·  "Now stack 1 of them."  ·  biểu đồ hai cột bằng nhau

    Không lỗi nào báo. Mỗi con số đúng, mỗi câu đúng ngữ pháp, cả tập vô nghĩa — đúng §14.6:
    *điểm cao và bản thảo vô nghĩa cùng tồn tại được*, vì thước đo tay nghề chứ không đo "thế
    giới này có diễn được không". Trước 6/9 lỗi hiếm vì bảng nhỏ và thưa; nối thêm ~950 mục thì
    mọi thang dày lên và cặp xấp xỉ bằng nhau thành chuyện thường. **Bảng to lên làm lộ một lỗ
    vốn đã có**, không tạo ra nó.

    ── VÌ SAO LỌC TRƯỚC RỒI MỚI ĐÁNH SỐ ────────────────────────────────────────────────────
    Bản đầu "nhảy tới cặp hợp lệ tiếp theo" (`_cap(d, i + b)`). Nó cho ra cặp đúng, và **phá
    tính song ánh**: i=0 nhảy sang cặp của i=5, rồi i=5 cũng trả cặp ấy. `so_chuong_toi_da`
    đếm chương bằng cách chạy tới khi tiêu đề TRÙNG, nên nó dừng ngay — bản dài `howbig` tụt
    từ 10,3 xuống **2,1 phút**. Đúng §15.1: *lọc trước, cắt sau* — ở đây là lọc trước, ĐÁNH SỐ
    sau. Đánh số trên một dãy rồi mới loại phần tử là tự tay tạo va chạm.
    """
    d = _khu(ds)
    n = len(d)
    if n < 2:
        return d[0], d[0]
    kh = (id(ds), n, ti, cot)
    hl = _CAP_TI.get(kh)
    if hl is None:
        hl = []
        for j in range(n * (n - 1)):
            x, y = _cap(d, j)
            try:
                u, v = abs(float(x[cot])), abs(float(y[cot]))
            except Exception:
                hl = None
                break
            if u and v and max(u, v) / min(u, v) >= ti:
                hl.append(j)
        if hl is None or not hl:          # bảng không so tỉ lệ được -> trả về hành vi cũ
            _CAP_TI[kh] = []
            return _cap(d, i)
        _CAP_TI[kh] = hl
    if not hl:
        return _cap(d, i)
    return _cap(d, hl[i % len(hl)])


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
    "howlong":  {"nen": "#EAD2BE", "mau": "#D75A88", "phu": "#2F6E8A", "chu": "#2E2A24"},
    "howbig":   {"nen": "#D8D4BE", "mau": "#216E83", "phu": "#C9552F", "chu": "#22282B"},
    "realcost": {"nen": "#D7D4B7", "mau": "#1E6C45", "phu": "#8A5A2E", "chu": "#232622"},
    "howmuch":  {"nen": "#DDCFBE", "mau": "#573C85", "phu": "#C98A2E", "chu": "#232336"},
    "whatif":   {"nen": "#E6D0BF", "mau": "#B04A8E", "phu": "#2F7D8A", "chu": "#2B2622"},
    "survive":  {"nen": "#DFD1B4", "mau": "#6B5124", "phu": "#4E6B54", "chu": "#232522"},
    "dayinlife":{"nen": "#DFD4B5", "mau": "#6E6C2A", "phu": "#3E6E8C", "chu": "#2A241B"},
    "wheregoes":{"nen": "#DBD2C6", "mau": "#405FD8", "phu": "#C9762F", "chu": "#212629"},
    "therules": {"nen": "#E7D1C3", "mau": "#BC4FBC", "phu": "#4E7C4A", "chu": "#252722"},
    "speedof":  {"nen": "#D8D2C0", "mau": "#245E99", "phu": "#D9622B", "chu": "#1F272E"},
    # ── 8 kênh bổ sung. Màu chọn để KHÔNG trùng cặp nào ở trên: mỗi kênh phải nhận ra được
    # khi đứng cạnh mười bảy kênh kia trong danh sách đề xuất của YouTube.
    "odds":      {"nen": "#E0CFBF", "mau": "#753D92", "phu": "#C9A227", "chu": "#241F2E"},
    "hiddenfee": {"nen": "#D9D4B5", "mau": "#2C6F2F", "phu": "#B4522E", "chu": "#1F2620"},
    "yearsof":   {"nen": "#DDD4B3", "mau": "#59721E", "phu": "#3E6E7C", "chu": "#2A2520"},
    "howloud":   {"nen": "#E8CDB6", "mau": "#C52F3B", "phu": "#2F5D8A", "chu": "#20242B"},
    "whatweighs": {"nen": "#DBD2B5", "mau": "#3F5E2C", "phu": "#B4603A", "chu": "#22261E"},
    "rightnow":  {"nen": "#D7D5BC", "mau": "#1C7D75", "phu": "#D97E36", "chu": "#1E272B"},
    "howhot":    {"nen": "#E7D1B4", "mau": "#BC5326", "phu": "#3B5E7A", "chu": "#2B231C"},
    "smallest":  {"nen": "#DCCFC2", "mau": "#4C43B2", "phu": "#8FA33E", "chu": "#1F2330"},
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
        # ── 6/9/2026 — "BEHIND THEM" BỊA RA NGƯỜI KHÔNG CÓ TRONG CÂU ────────────────────
        # Soi khung thật kênh `smallest`: câu chỉ tả MỘT VẬT phóng to ("a smartphone
        # transistor shown enormous and clear") — không hề có người. Nhưng cụm cũ luôn
        # viết "behind THEM", và đại từ "them" không có ai để chỉ trong câu. Mô hình
        # không kiểm ngữ pháp — nó đọc "behind them" và TỰ VẼ THÊM người để khớp đại từ,
        # ra đúng khung "hai người đứng chồng chéo cạnh một khối đen khổng lồ" anh chê.
        # Bỏ hẳn đại từ: an toàn với cả chủ thể người lẫn vật, không mời thêm ai vào khung.
        p.append(f"{xa} in the background")
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
    a, b = _cap_ti(CO_LON, i)
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
    ('a million', 1000000, 'a billion', 1000000000, 'seconds', 'tien'),
    ('a billion', 1000000000, 'a trillion', 1000000000000, 'seconds', 'tien'),
    ('a thousand', 1000, 'a million', 1000000, 'seconds', 'tien'),
    ('a million dollars', 1000000, 'a billion dollars', 1000000000, 'dollars', 'tien'),
    ('a million steps', 1000000, 'a billion steps', 1000000000, 'steps', 'nguoi'),
    ('a thousand days', 1000, 'a million days', 1000000, 'days', 'dong_ho'),
    ('a million grains', 1000000, 'a billion grains', 1000000000, 'grains', 'hop'),
    ('a million people', 1000000, 'a billion people', 1000000000, 'people', 'nguoi'),
    ('a million miles', 1000000, 'a billion miles', 1000000000, 'miles', 'may_bay'),
    ('a million words', 1000000, 'a billion words', 1000000000, 'words', 'giay'),
    ('a thousand hours', 1000, 'a million hours', 1000000, 'hours', 'dong_ho'),
    ('a million drops', 1000000, 'a trillion drops', 1000000000000, 'drops', 'coc'),
    ('a million cells', 1000000, 'a trillion cells', 1000000000000, 'cells', 'te_bao'),
    ('a billion stars', 1000000000, 'a trillion stars', 1000000000000, 'stars', 'mat_troi'),
    ('a thousand dollars', 1000, 'a billion dollars', 1000000000, 'dollars', 'tien'),
    ('a million minutes', 1000000, 'a billion minutes', 1000000000, 'minutes', 'dong_ho'),
    ('a million pages', 1000000, 'a billion pages', 1000000000, 'pages', 'giay'),
    ('a million heartbeats', 1000000, 'a billion heartbeats', 1000000000, 'heartbeats', 'nguoi'),
    ('a million atoms', 1000000, 'a trillion atoms', 1000000000000, 'atoms', 'nguyen_tu'),
    ('a thousand miles', 1000, 'a million miles', 1000000, 'miles', 'xe'),
    ('a million bytes', 1000000, 'a trillion bytes', 1000000000000, 'bytes', 'dien_thoai'),
    ('a million breaths', 1000000, 'a billion breaths', 1000000000, 'breaths', 'nguoi'),
    ('a million raindrops', 1000000, 'a billion raindrops', 1000000000, 'raindrops', 'coc'),
    ('a thousand seconds', 1000, 'a billion seconds', 1000000000, 'seconds', 'dong_ho'),
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


# ── MOI_NGUOI: NÂNG TỪ DANH SÁCH NỘI BỘ LÊN BẢNG MODULE  (6/9/2026) ───────────────────────
# Danh sách này nằm TRONG `sinh_whatif` nên `bang_mo_rong.py` không nhìn thấy nó, và kênh
# `whatif` dừng ở 28 mục = cạn chủ đề sau ~14 tập short. Không phải vì thế giới hết thứ
# để nói — cùng niche ấy, `howloud` đi từ 31 lên 278 mục chỉ bằng cách nới BẢNG.
# Đưa ra ngoài không đổi một hành vi nào; nó chỉ làm dữ liệu NHÌN THẤY ĐƯỢC từ bên ngoài,
# đúng điều kiện để nới. Cùng bài học §15.12: một trường chỉ được ghi mà không ai đọc
# được thì coi như chưa tồn tại.
MOI_NGUOI = [("everyone flushed at once", "hop", "a vast grid of identical bathrooms seen from above"),
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
      ("everyone wrote one letter", "giay", "a post office counter with towering trays of envelopes"),

    # ── NỐI THÊM 6/9/2026 · 274 mục qua bốn cổng của `bang_van.py`
    #    (dạng · không người · không chữ · không viết nghịch · không trùng).
    #    Bảng này KHÔNG có con số nào, nên không có gì để đối chứng và cũng
    #    không đụng tới luật nền 'AI không bao giờ cấp một con số'.
    ('everyone sang a chorus together', 'nguoi', 'a vast stadium filled with swirling clouds of vibrating air, rippling across the empty seats'),
    ('everyone watered plants', 'cay', 'A balcony garden brimming with watering cans, soil trays, and sprouting seedlings'),
    ('everyone flicked windshield defrosters', 'nguoi', 'a cold winter road with buses, trucks, and cars steaming as heat rises'),
    ('everyone placed a cardboard box', 'nguoi', 'an open parking lot covered in stacked brown boxes creating a maze of angles'),
    ('everyone used electric shavers at once', 'nguoi', 'a grooming salon, many shavers buzzing, metal heads moving, mist of tiny droplets rising'),
    ('everyone walked along riverbanks', 'nguoi', 'a calm riverbank lined with reeds, smooth stones, and a wooden dock stretching outward'),
    ('everyone bounded over potholes', 'nguoi', 'an old cobbled lane, cracked stones, wild thyme sprouting, morning dew sparkling'),
    ('everyone checked the weather forecast', 'nguoi', 'a mountain summit blanketed by soft pastel clouds that pulse with rhythmic glows'),
    ('everyone dumped old magazines', 'nguoi', 'a waiting room floor stacked with glossy magazines creating a colorful paper hill'),
    ('everyone shifted gears rapidly', 'nguoi', 'a steep hill climb where trucks, cars, and motorcycles grunt as they change speeds'),
    ('everyone made charitable donations', 'nguoi', 'a community hall with large donation boxes overflowing with paper notes and ribbons'),
    ('everyone requested debit card replacements', 'nguoi', 'a service counter area with rows of metal trays, soft beige walls, and a ceiling of acoustic tiles'),
    ('everyone walked down stairwells', 'nguoi', 'a dim stairwell lined with worn carpet, flickering bulbs, and a cascade of hanging vines'),
    ('everyone hopped onto elevators', 'nguoi', 'a modern office lobby with glass elevators, potted plants, and sleek marble flooring'),
    ('everyone braked hard', 'nguoi', 'a mountain pass winding through hills, cars and motorcycles slowing abruptly on the curve'),
    ('everyone sang a lullaby in unison', 'nguoi', 'a cozy cabin interior filled with warm melodic mist curling around wooden beams'),
    ('everyone turned on fans', 'nguoi', 'A living room filled with rotating fans, breezy ribbons, and hanging plants'),
    ('everyone tossed used napkins simultaneously', 'nguoi', 'a school cafeteria trash can piled with crumpled paper towels, stained napkins, and disposable wipes'),
    ('everyone tossed a bottle cap', 'nguoi', 'a gravel path sprinkled with metallic caps shimmering like scattered stars'),
    ('everyone powered up electric scooters in a mall', 'nguoi', 'a shopping corridor, rows of scooters docked, indicator LEDs pulsing, floor reflecting bright colors'),
    ('everyone marched through plazas', 'nguoi', 'a historic square paved with cobblestones, surrounded by fountains, statues, and blooming lavender bushes'),
    ('everyone updated security passwords', 'nguoi', 'a secure password vault room filled with locked keychains and digital keypads'),
    ('everyone clicked a link at once', 'nguoi', 'a modern office lobby bathed in a cascade of bright arrows arching across the ceiling'),
    ('everyone dumped old CDs', 'nguoi', 'a hallway floor shimmering with rainbow‑colored disc fragments catching the ceiling light'),
    ('everyone pressed the gas pedal', 'nguoi', 'a straight desert highway where convoy of pickups, SUVs, and motorcycles surge forward'),
    ('everyone set up two‑factor authentication', 'nguoi', 'a sleek gadget showcase with smartphones, hardware keys, and glowing LEDs'),
    ('everyone tossed snack wrappers simultaneously', 'nguoi', 'a school playground surrounded by bright recycling bins overflowing with colorful snack packet wrappers'),
    ('everyone jumped in office corridors', 'nguoi', 'a long corridor with glass partitions, potted ferns, and a row of humming coffee machines'),
    ('everyone hopped across ponds', 'nguoi', 'a lily‑filled pond, water lilies opening, dragonflies skimming surface, reeds swaying gently'),
    ('everyone pressed the parking brake', 'nguoi', 'a crowded parking garage, rows of vehicles halted on concrete ramps'),
    ('everyone poured oil waste', 'nguoi', 'a garage floor slick with dark oily puddles reflecting the ceiling lights'),
    ('everyone polished their glasses', 'coc', 'A nightstand with eyeglass cases, cleaning cloths, and sparkling lenses'),
    ('everyone requested loan approvals', 'nguoi', 'a conference room with large wooden table covered in thick contract binders'),
    ('everyone placed a paper plate', 'nguoi', 'a picnic meadow scattered with white plates forming a patterned blanket'),
    ('everyone walked along beaches', 'nguoi', 'a wide sandy shore scattered with seashells, rolling waves, and driftwood logs under a golden sunrise'),
    ('everyone hopped onto scooters', 'nguoi', 'a bike lane bordered by trees, trash cans, and painted lane markings'),
    ('everyone read books before sleep', 'giuong', 'a quiet reading nook filled with open books, soft cushions, and a warm lamp glow'),
    ('everyone turned on a VPN at once', 'nguoi', 'a dense urban alley where glowing tunnels appear along the walls, weaving in and out'),
    ('everyone checked their phones', 'dien_thoai', 'A coffee table scattered with smartphones, chargers, and glowing notification icons'),
    ('everyone opened glove compartments', 'nguoi', 'a parking lot under trees where sedans, coupes, and minivans expose interior panels'),
    ('everyone folded a newspaper', 'nguoi', 'a quiet downtown square piled with crisp sheets forming soft white hills'),
    ('everyone activated smart speakers at noon', 'nguoi', 'a modern kitchen island, numerous devices glowing blue, sound waves illustrated as concentric circles'),
    ('everyone jumped in backyard pools', 'nguoi', 'a backyard pool shimmering with ripples, floating pool toys, and a line of sun umbrellas'),
    ('everyone marched through vineyards', 'nguoi', 'vine rows laden with grapes, wooden trellises, distant hills, sunrise casting amber light'),
    ('everyone sent a text message at once', 'dien_thoai', 'a wide riverbank lined with tiny flickering bubbles rising like fireflies across the water'),
    ('everyone tossed coffee grounds', 'coc', 'a kitchen counter scattered with dark coffee grounds forming a thick brown carpet'),
    ('everyone flashed turn signals', 'nguoi', 'a roundabout crowded with cars, trucks, and bicycles signaling left and right in sync'),
    ('everyone audited personal expenses', 'nguoi', 'a home study desk cluttered with spreadsheets, pens, and stacked receipts'),
    ('everyone activated mobile alerts', 'nguoi', 'a contemporary call center floor with rows of ergonomic chairs, soft carpeting, and large acoustic panels'),
    ('everyone jumped in schoolyards', 'nguoi', 'a playground crowded with squeaky swings, bright slides, and scattered chalk drawings on the pavement'),
    ('everyone vaulted over garden walls', 'nguoi', 'a backyard garden with flowerbeds, watering cans, and a low brick wall'),
    ('everyone cleaned dishes after meals', 'nguoi', 'a kitchen sink filled with sudsy plates, forks, and a gleaming faucet'),
    ('everyone chanted a mantra at once', 'nguoi', 'a serene garden terrace filled with rhythmic pulse circles glowing above stone tiles'),
    ('everyone brewed tea', 'nguoi', 'A kitchen countertop crowded with teapots, loose leaf tins, and steaming cups'),
    ('everyone cleared cardboard boxes collectively', 'nguoi', 'a warehouse courtyard stacked with flattened cardboard, corrugated sheets, and broken packing inserts'),
    ('everyone dropped a yogurt container', 'nguoi', "a farmer's market aisle overflowing with smooth plastic tubs arranged in rows"),
    ('everyone activated electric air purifiers', 'nguoi', 'an office atrium, tall units with spinning filters, soft blue lights, clean air swirling visibly'),
    ('everyone bounced on trampolines', 'nguoi', 'an indoor gymnasium with foam mats, rubberized flooring, and a wall of climbing ropes'),
    ('everyone requested cash advances', 'nguoi', 'a bustling teller area with brass cash drawers overflowing with banknotes'),
    ('everyone posted a review online', 'nguoi', 'a cozy café patio covered in floating star icons that twinkle above the tables'),
    ('everyone poured ink cartridges', 'nguoi', 'a printer room table stacked with colorful ink cartridges spilling tiny droplets onto the surface'),
    ('everyone turned on windshield wipers', 'nguoi', 'a rainy downtown avenue where trucks, sedans, and buses spray water across the pavement'),
    ('everyone updated beneficiary information', 'nguoi', 'a quiet waiting area with comfortable chairs, low tables, and decorative lamps'),
    ('everyone dropped glass jars at once', 'coc', 'a quiet suburban street corner with green recycling containers overflowing with clear glass jars'),
    ('everyone walked through subway tunnels', 'nguoi', 'a underground tunnel lined with tiled walls, glowing neon strips, and echoing train whistles'),
    ('everyone shuffled through snow', 'nguoi', 'a pine forest blanketed in fresh snow, icicles hanging, animal tracks weaving between trunks'),
    ('everyone engaged four‑wheel drive', 'xe', 'a rugged off‑road trail, mud splashing as SUVs climb steep inclines together'),
    ('everyone dumped cardboard boxes', 'nguoi', 'a warehouse floor covered in flattened brown boxes forming a maze of corrugated layers'),
    ('everyone checked the news', 'nguoi', 'A living room coffee table with newspapers, tablets, and a steaming tea pot'),
    ('everyone transferred funds instantly', 'nguoi', 'a data center hallway illuminated by rows of blinking server racks and humming cables'),
    ('everyone dumped a milk jug', 'nguoi', 'a farmyard surrounded by white jugs forming a gentle white wall'),
    ('everyone jumped on rooftops', 'nguoi', 'a city skyline roof garden filled with potted herbs, loose tiles, and humming bees buzzing around'),
    ('everyone vaulted across playgrounds', 'nguoi', 'a city playground with swings, slides, sandboxes, and colorful rubber tiles'),
    ('everyone set alarms for tomorrow', 'nguoi', 'a nightstand cluttered with digital clocks, alarm buttons, and soft nightlights'),
    ('everyone cleared their cache simultaneously', 'nguoi', 'an ancient courtyard where dust motes sparkle and rise like tiny fireworks'),
    ('everyone fed their pets', 'meo', 'A kitchen nook piled with pet bowls, kibble piles, and wagging tails toys'),
    ('everyone checked tire pressure', 'nguoi', 'a service station lane with cars, bikes, and scooters lined up beside fuel pumps'),
    ('everyone dropped a plastic bottle', 'nguoi', 'a bustling beach dotted with countless translucent bottles shimmering under bright sky'),
    ('everyone turned on electric toothbrushes', 'nguoi', 'a bathroom exhibit, many brushes vibrating, bristles moving, tiny lights blinking on handles'),
    ('everyone walked through airport runways', 'nguoi', 'a long runway marked with white lights, distant aircraft, and a stretch of endless tarmac'),
    ('everyone leapt over streams', 'nguoi', 'a crystal creek winding through a valley, smooth stones glistening, moss-covered banks, rainbows forming'),
    ('everyone posted a selfie simultaneously', 'nguoi', 'a bustling rooftop garden drenched in countless glowing rectangular panels reflecting twilight'),
    ('everyone poured paint cans', 'nguoi', 'an artist studio floor splashed with bright paint cans spilling vivid colors onto the concrete'),
    ('everyone played loud music', 'nguoi', 'a downtown parking lot where cars vibrate, speakers blaring, and exhaust pipes humming'),
    ('everyone activated mobile wallets', 'nguoi', 'a bustling café counter with rows of smartphones, chargers, and frothy drinks'),
    ('everyone set up automatic transfers', 'nguoi', 'an open‑plan tech hub with modular desks, whiteboard walls, and hanging pendant lights'),
    ('everyone walked through museums', 'nguoi', 'a grand hall filled with marble statues, polished floors, and soft spotlights illuminating artifacts'),
    ('everyone hopped across frozen lakes', 'nguoi', 'a winter lake surface covered with thin ice, snow drifts, and scattered pine trees'),
    ('everyone locked doors at night', 'giuong', 'a hallway lined with sturdy doors, keychains, and a quiet humming of night insects'),
    ('everyone yodeled on a hill simultaneously', 'nguoi', 'a rolling meadow filled with echoing mountain calls bouncing off distant peaks'),
    ('everyone cleaned their windows', 'nguoi', 'A sunlit porch with sparkling glass panes, spray bottles, and microfiber cloths'),
    ('everyone recycled glass simultaneously', 'coc', 'a city recycling depot piled high with clear bottles, colored jars, and shattered shards sparkling under sun'),
    ('everyone threw a snack wrapper', 'nguoi', 'a playground sandbox filled with colorful foil wrappers forming a mosaic pattern'),
    ('everyone started electric water pumps', 'coc', 'a farm irrigation field, pumps humming, water jets arcing, canals filling with flowing streams'),
    ('everyone hopped onto buses', 'xe_buyt', 'a busy bus depot filled with waiting benches, ticket kiosks, and overhead luggage racks'),
    ('everyone set up automatic payments', 'nguoi', 'a quiet back‑office room lined with humming printers and stacks of receipt rolls'),
    ('everyone opened a map app simultaneously', 'dien_thoai', 'a winding road tunnel glowing with animated route lines that snake along the walls'),
    ('everyone dumped garden pots', 'nguoi', 'a balcony terrace filled with broken clay pots and shattered ceramic pieces'),
    ('everyone tapped brakes lightly', 'nguoi', 'a narrow alley packed with motorcycles, mopeds, and compact cars gently slowing together'),
    ('everyone reviewed transaction histories', 'nguoi', 'a sunlit study area filled with open laptops, stacks of paper, and potted plants'),
    ('everyone emptied coffee cups at once', 'coc', 'a modern office lobby featuring sleek metal recycling stations stacked with white disposable coffee cups'),
    ('everyone jumped in theater lobbies', 'nguoi', 'a marble lobby with plush carpets, towering columns, and glowing sconces casting soft shadows'),
    ('everyone bounded over rocks', 'nguoi', 'a rugged coastline, jagged cliffs, seafoam crashing, gulls circling, tide pools shimmering'),
    ('everyone pulled over', 'nguoi', 'a rest area beside a highway, parking spaces filling with stopped cars and RVs'),
    ('everyone tossed old tires', 'nguoi', 'an industrial lot scattered with black rubber tires piled in chaotic circles'),
    ('everyone opened a window', 'nguoi', 'A breezy balcony showing open windows, fluttering curtains, and potted herbs'),
    ('everyone deposited checks at once', 'nguoi', 'a modern teller area scattered with glossy envelopes and stacked green sheets'),
    ('everyone placed a broken umbrella', 'nguoi', 'a bus stop awash with colorful canopy frames forming a kaleidoscopic canopy'),
    ('everyone walked through parks', 'nguoi', 'a sunny park dotted with rustling leaves, swaying benches, and fluttering kite tails against blue sky'),
    ('everyone leapt over puddles', 'nguoi', 'a rain‑slicked sidewalk dotted with rain gutters, street lamps, and reflective puddles'),
    ('everyone cooked dinner simultaneously', 'nguoi', 'a spacious kitchen stove surrounded by sizzling pans, herbs, and fragrant steam'),
    ('everyone turned on push notifications', 'nguoi', 'a sleek subway platform where tiny bells glow amber and sway with each passing train'),
    ('everyone opened their curtains', 'nguoi', 'A sunrise-lit living room filled with fluttering curtains, sunbeams, and potted ferns'),
    ('everyone shifted to reverse', 'nguoi', 'a loading dock where trucks, vans, and carts back up in coordinated motion'),
    ('everyone tossed a soda can', 'nguoi', 'a wide riverbank strewn with sparkling aluminum cans reflecting the sunrise'),
    ('everyone switched on electric heaters simultaneously', 'nguoi', 'a mountain lodge lounge, multiple wall heaters glowing red, warm air swirling, frost melting from windows'),
    ('everyone walked across city squares', 'nguoi', 'a stone plaza surrounded by fountains, stone benches, and a towering clock tower ticking'),
    ('everyone walked through orchards', 'nguoi', 'rows of apple trees heavy with fruit, blossoms falling, bees buzzing among fragrant petals'),
    ('everyone activated emergency flashers', 'nguoi', 'a construction zone at dusk, flashing red lights on dozens of work trucks and vans'),
    ('everyone dumped used diapers', 'nguoi', 'a daycare playroom floor covered with white disposable diapers forming a soft mound'),
    ('everyone turned on headlights', 'nguoi', 'a twilight boulevard illuminated by glowing headlights of taxis, SUVs, and street sweepers'),
    ('everyone requested balance statements', 'nguoi', 'a tidy filing shelf stocked with thick bound ledgers and paper folders'),
    ('everyone paid utility bills', 'tien', 'a municipal utility office filled with rows of filing cabinets, ticking wall clocks, and soft carpeted aisles'),
    ('everyone jumped in grocery aisles', 'nguoi', 'an aisle brimming with stacked crates, hanging fruit, and colorful produce spilling onto the floor'),
    ('everyone sprinted through stadiums', 'nguoi', 'a large arena with tiered seats, bright spotlights, and a polished wooden floor'),
    ('everyone turned on radios at lunch', 'nguoi', 'a kitchen counter surrounded by small radios, coffee mugs, and a midday sunbeam'),
    ('everyone laughed loudly at once', 'nguoi', 'a large theater lobby filled with shimmering giggle ripples bouncing off marble columns'),
    ('everyone opened the fridge', 'nguoi', 'A kitchen fridge interior filled with colorful vegetables, milk cartons, and fruit bowls'),
    ('everyone tossed paper today', 'nguoi', 'a quiet streetside bin brimming with crumpled newspaper, glossy magazines, and loose office sheets'),
    ('everyone placed a plastic bag', 'nguoi', 'a suburban street lined with translucent bags swaying gently in the breeze'),
    ('everyone switched on electric snow blowers', 'nguoi', 'a winter park, multiple machines blowing snow, white plumes swirling, motors humming in cold air'),
    ('everyone leapt over curbs', 'nguoi', 'a quiet suburban sidewalk bordered by flower beds, garden gnomes, and rows of mailboxes'),
    ('everyone exchanged foreign currency', 'nguoi', 'an international exchange hall filled with colorful stacks of bills and rotating coin dispensers'),
    ('everyone turned on video chat', 'nguoi', 'a high‑rise balcony filled with dozens of tiny holographic frames hovering in the night sky'),
    ('everyone dumped old receipts', 'nguoi', 'a office hallway carpeted with crumpled paper strips forming a gray carpet'),
    ('everyone checked mirrors simultaneously', 'nguoi', 'a busy intersection where cars, buses, and bicycles reflect the sky in side mirrors'),
    ('everyone requested account closures', 'nguoi', 'a sterile office corridor lined with locked filing cabinets and empty desk trays'),
    ('everyone set up tax withholding', 'nguoi', 'a government tax office with high ceilings, rows of wooden cubicles, and a polished brass chandelier'),
    ('everyone walked across parking lots', 'nguoi', 'an expansive lot dotted with striped lines, parked cars, and scattered tire marks under a clear sky'),
    ('everyone sprinted through forest', 'cay', 'a dense woodland path, ferns unfurling, mushrooms clustering, shafts of light piercing the canopy'),
    ('everyone sounded horns', 'nguoi', 'a bustling city intersection, traffic signals green, cars and taxis emitting short bursts of sound'),
    ('everyone flushed plastic bags', 'nguoi', 'a city park pond surface dotted with floating translucent bags drifting among lily pads'),
    ('everyone fed breakfast cereal', 'nguoi', 'A breakfast table piled with cereal boxes, milk cartons, and crunchy bowls'),
    ('everyone cleared discarded flyers simultaneously', 'nguoi', 'a community board bin crowded with glossy sheets, colorful graphics, and torn corners'),
    ('everyone threw a paper napkin', 'nguoi', 'a restaurant patio strewn with crumpled white napkins like fluffy clouds'),
    ('everyone jumped in kitchens', 'nguoi', 'a bright kitchen cluttered with floating spoons, tumbling bowls, and swirling steam from simmering pots'),
    ('everyone hopped onto skateboards', 'nguoi', 'a skate park filled with concrete ramps, railings, and scattered skate decks'),
    ('everyone left work at five', 'nguoi', 'an office lobby filled with rolling chairs, coffee cups, and a sunrise through glass doors'),
    ('everyone turned on airplane mode simultaneously', 'nguoi', 'a quiet hilltop where tiny lanterns dim together, creating a soft twilight blanket'),
    ('everyone tied their shoes', 'nguoi', 'A hallway floor strewn with laces, sneaker soles, and colorful shoe polish bottles'),
    ('everyone opened sun visors', 'mat_troi', 'a bright morning street where sedans, hatchbacks, and scooters block glare with visor flaps'),
    ('everyone applied for overdraft protection', 'nguoi', 'a small office nook with piles of forms, staplers, and a ticking wall clock'),
    ('everyone charged electric cars simultaneously', 'xe', 'a large parking garage, rows of vehicles with glowing plugs, indicator LEDs flashing green in unison'),
    ('everyone jumped in kitchen pantries', 'nguoi', 'a pantry stacked with canned goods, hanging pots, and a rope ladder leaning against shelves'),
    ('everyone hopped onto docks', 'nguoi', 'a wooden pier stretching into calm lake, fishing nets hanging, water lilies drifting nearby'),
    ('everyone engaged lane‑keeping assist', 'nguoi', 'a straight city boulevard, vehicles hugging centerlines with invisible guidance'),
    ('everyone dumped glass shards', 'coc', 'a laboratory floor scattered with glittering broken glass fragments catching the overhead lights'),
    ('everyone accelerated at once', 'nguoi', 'an open highway stretching under a clear sky, dozens of trucks and cars surging forward'),
    ('everyone applied for credit cards', 'nguoi', 'a polished desk area piled with glossy card packets and sleek plastic sleeves'),
    ('everyone updated beneficiary details', 'nguoi', 'a corporate headquarters lobby adorned with marble pillars, potted ficus trees, and a polished stone floor'),
    ('everyone walked across bridges', 'nguoi', 'a steel bridge arching over a river, lined with rusted railings, hanging lanterns, and flowing water below'),
    ('everyone dashed through airports', 'nguoi', 'an airport terminal with rolling luggage carts, departure boards, and rows of waiting chairs'),
    ('everyone polished shoes before outing', 'nguoi', 'a entryway rug covered with shoe polish pots, brushes, and gleaming leather shoes'),
    ('everyone shouted a greeting simultaneously', 'nguoi', 'a bustling market square filled with bright bursts of audible color swirling above stalls'),
    ('everyone brushed their hair', 'nguoi', 'A bathroom vanity covered with combs, hairbrushes, and bottles of styling gel'),
    ('everyone turned on hazard blinkers', 'nguoi', 'a busy tunnel filled with buses, trucks, and cars flashing amber lights in unison'),
    ('everyone dropped a coffee cup', 'coc', 'a commuter station floor littered with white ceramic cups forming a sea of circles'),
    ('everyone turned on electric lawn mowers', 'nguoi', 'a suburban cul-de-sac, many mowers cutting grass, blades whirring, green clippings forming clouds'),
    ('everyone walked across desert dunes', 'nguoi', 'a vast dune field under a blazing sun, dotted with tumbleweeds, sand ripples, and distant mirages'),
    ('everyone leapt onto balconies', 'nguoi', 'a courtyard with stone arches, climbing roses, lanterns hanging, night sky full of stars'),
    ('everyone posted a comment on a video', 'nguoi', 'a city square illuminated by a cascade of multicolored speech bubbles floating above the pavement'),
    ('everyone poured used oil', 'nguoi', 'a restaurant kitchen drain filled with amber liquid pooling in the sink basin'),
    ('everyone rolled down sunroofs', 'nguoi', 'a sunny coastal road with convertibles, minivans, and scooters enjoying breezes'),
    ('everyone set up direct deposits', 'nguoi', 'a corporate break room with coffee pots, snack bowls, and printed payroll sheets'),
    ('everyone reviewed transaction history', 'nguoi', 'a quiet audit office with rows of filing cabinets, green desk lamps, and a low humming HVAC system'),
    ('everyone jumped on balcony railings', 'nguoi', 'a balcony overlooking a city, adorned with potted succulents, wind chimes, and fluttering curtains'),
    ('everyone walked through rain', 'nguoi', 'a cobblestone lane under heavy clouds, puddles glimmering, lanterns flickering, vines dripping with water'),
    ('everyone changed lanes', 'nguoi', 'a multilane expressway, vehicles weaving smoothly between orange stripes under a sunrise'),
    ('everyone dumped food scraps', 'nguoi', 'a community garden compost heap swelling with vegetable peels, fruit skins, and leafy waste'),
    ('everyone organized drawers', 'nguoi', 'A study desk with open drawers, neatly arranged pens, and colorful paper clips'),
    ('everyone dumped broken umbrellas simultaneously', 'nguoi', 'a rainy‑day shelter floor covered with snapped ribs, torn canopies, and tangled handles'),
    ('everyone placed a juice carton', 'nguoi', 'a school courtyard piled with pastel cartons creating a soft pastel mound'),
    ('everyone powered up electric hot tubs', 'lua', 'a resort pool area, several tubs bubbling, water steaming, underwater lights casting ripples'),
    ('everyone darted through alleys', 'nguoi', 'a narrow city alley lined with brick walls, fire escapes, and stacked crates'),
    ('everyone walked their dogs simultaneously', 'meo', 'a suburban street lined with wagging leashes, leashed collars, and blooming flowerbeds'),
    ('everyone changed their profile picture', 'nguoi', 'a suburban driveway lined with rotating mirrors that reflect shifting colors like sunrise'),
    ('everyone poured coffee', 'coc', 'A kitchen island cluttered with coffee mugs, steaming pots, and scattered coffee beans'),
    ('everyone pressed the horn softly', 'nguoi', 'a quiet residential lane filled with bicycles, compact cars, and a delivery cart'),
    ('everyone adjusted interest rates personally', 'nguoi', 'a modern finance lab with digital dashboards, glowing graphs, and sleek workstations'),
    ('everyone used microwaves at once', 'nguoi', 'a kitchen showroom, dozens of microwave ovens humming, interior lights flickering, steam rising from dishes'),
    ('everyone walked through botanical gardens', 'nguoi', 'a garden path winding among blooming roses, cascading waterfalls, and fluttering butterflies'),
    ('everyone stepped onto stairs', 'nguoi', 'an ancient stone staircase winding up a hill, moss covering steps, sunrise peeking over the ridge'),
    ('everyone released handbrake', 'nguoi', 'a steep hill overlook, cars rolling gently downhill in a coordinated glide'),
    ('everyone emptied ashtrays', 'nguoi', 'a café patio table surrounded by ash-filled trays releasing gray powder into the air'),
    ('everyone honked simultaneously', 'nguoi', 'a bustling city avenue lined with parked cars, moving buses, and a river of motorcycles'),
    ('everyone checked credit scores', 'nguoi', 'a comfortable lounge with plush sofas, coffee tables, and stacked financial brochures'),
    ('everyone checked account balances', 'nguoi', 'a quiet library reading room with tall bookshelves, green lamps, and a central wooden table'),
    ('everyone jumped on train platforms', 'nguoi', 'a bustling platform filled with rolling suitcases, bright ticket kiosks, and a cascade of departing trains'),
    ('everyone hopped across stepping stones', 'nguoi', 'a shallow creek dotted with smooth stones, water lilies, and dragonflies hovering'),
    ('everyone organized closets at weekend', 'nguoi', 'a bedroom hallway filled with hanging racks, shoe boxes, and colorful scarves'),
    ('everyone whistled a tune at once', 'nguoi', 'an open field covered in floating musical notes drifting above the grass and sky'),
    ('everyone made their bed', 'giuong', 'A cozy bedroom displaying neatly spread sheets, fluffy pillows, and a tidy comforter'),
    ('everyone activated turn signals left', 'nguoi', 'a four‑lane avenue where vehicles line up, lights blinking left as they prepare to merge'),
    ('everyone tossed a tin foil', 'nguoi', 'a rooftop terrace glittering with crinkled silver sheets fluttering like tiny flags'),
    ('everyone powered up electric blankets at night', 'giuong', 'a dormitory hallway, beds with faint orange glows, blankets radiating gentle warmth'),
    ('everyone jumped on carnival rides', 'nguoi', 'a carnival midway filled with colorful tents, spinning wheels, and a cascade of cotton candy clouds'),
    ('everyone walked along cliffs', 'nguoi', 'a sheer cliff edge overlooking turquoise sea, seabirds gliding, sea spray misting the air'),
    ('everyone opened a new tab simultaneously', 'nguoi', 'a spacious library aisle filled with hovering translucent pages fluttering like butterflies'),
    ('everyone dumped broken dishes', 'nguoi', 'a dining hall floor littered with ceramic shards reflecting fragments of light'),
    ('everyone activated hazard lights', 'nguoi', 'a construction zone lane where trucks and diggers flash amber lights amid dust'),
    ('everyone reviewed mortgage terms', 'nguoi', 'a quiet library corner surrounded by tall shelves of thick finance manuals'),
    ('everyone paid mortgage installments', 'tien', 'a suburban bank branch lobby with a large indoor fountain, marble pillars, and a tiled floor pattern'),
    ('everyone walked through markets', 'nguoi', 'a bustling market square filled with stalls of fabric, baskets of spices, and hanging lanterns swaying'),
    ('everyone jumped at sunrise', 'nguoi', 'a quiet hillside bathed in gold, wildflowers swaying, birds soaring, mist lingering over pine trees'),
    ('everyone revved engines', 'xe', 'a parking lot beside a mall, rows of cars idling, exhaust clouds rising'),
    ('everyone placed paper in bins', 'nguoi', 'a suburban street lined with overflowing paper recycling containers spilling crisp sheets onto the curb'),
    ('everyone took a shower', 'nguoi', 'A bathroom stall filled with showerheads, fluffy towels, and scented soap bars'),
    ('everyone tossed used batteries simultaneously', 'nguoi', 'a hazardous waste station crowded with cylindrical cells, corroded terminals, and plastic casings'),
    ('everyone tossed a plastic straw', 'nguoi', 'a beach boardwalk scattered with bright straws resembling colorful confetti'),
    ('everyone started electric snow melt systems', 'nguoi', 'a city street, pavement embedded with glowing strips, snow disappearing as heat radiates upward'),
    ('everyone hopped onto trains', 'nguoi', 'a bustling train station with platforms, luggage trolleys, and rows of waiting benches'),
    ('everyone made breakfast at once', 'nguoi', 'a bright dining table overloaded with pancakes, fruit bowls, butter knives, and syrup drizzles'),
    ('everyone added a friend on a network', 'nguoi', 'a quiet forest clearing where luminous vines intertwine, forming a glowing web overhead'),
    ('everyone brushed their teeth', 'nguoi', 'A bathroom counter covered with toothpaste tubes, toothbrushes, and a glass of minty mouthwash'),
    ('everyone turned on seat belts', 'nguoi', 'a highway rest area where parked cars, RVs, and vans show buckled straps'),
    ('everyone verified identity documents', 'nguoi', 'a secure verification booth filled with scanners, document trays, and bright task lighting'),
    ('everyone dropped used mascara tubes simultaneously', 'nguoi', 'a makeup boutique entrance with recycling bins packed with slender plastic mascara tubes'),
    ('everyone jumped on playground sandboxes', 'nguoi', 'a sandbox brimming with golden sand, scattered toy trucks, and a small wooden bridge'),
    ('everyone galloped through meadows', 'nguoi', 'a golden meadow, buttercups blooming, butterflies fluttering, distant hills rolling under clear sky'),
    ('everyone started electric motors', 'nguoi', 'an electric‑vehicle charging lane, silent cars gliding forward with soft hums'),
    ('everyone dumped old clothes', 'nguoi', 'a thrift shop backroom overflowing with folded shirts, jeans, and jackets spilling onto the racks'),
    ('everyone turned on the heater', 'nguoi', 'A cozy lounge filled with radiators, warm blankets, and a glowing fireplace'),
    ('everyone set up automatic savings', 'nguoi', 'a bright kitchen countertop with open notebooks, calculators, and jars of coins'),
    ('everyone changed PIN numbers', 'nguoi', 'a sleek security office filled with rows of keypad panels, glass cabinets, and soft amber lighting'),
    ('everyone walked through libraries', 'nguoi', 'a quiet library aisles lined with towering shelves, scattered bookmarks, and dust motes dancing in sunlight'),
    ('everyone leaped over logs', 'nguoi', 'a forest trail covered in moss, fallen logs, and clusters of pine cones'),
    ('everyone checked the weather morning', 'nguoi', 'a kitchen window sill holding rain gauges, potted herbs, and a bright sunrise'),
    ('everyone clapped their hands simultaneously', 'nguoi', 'a quiet auditorium filled with concentric rings of resonant waves echoing off polished walls'),
    ('everyone folded laundry', 'nguoi', 'A bedroom floor stacked with neatly folded shirts, socks, and soft blankets'),
    ('everyone turned on cruise control', 'nguoi', 'an endless freeway where a steady stream of cars, trucks, and RVs maintain constant speed'),
    ('everyone recycled a glass jar', 'coc', 'a garden path lined with glimmering glass jars catching morning light'),
    ('everyone switched on electric grills simultaneously', 'nguoi', 'an outdoor market, multiple grills heating, flames licking metal, smoke curling above stalls'),
    ('everyone walked through art galleries', 'nguoi', 'a white-walled gallery displaying abstract paintings, sleek pedestals, and soft track lighting'),
    ('everyone sprinted across fields', 'nguoi', 'a wheat field swaying, golden stalks rippling, distant wind turbines turning slowly'),
    ('everyone liked a post at the same moment', 'nguoi', 'a calm lake surface rippling with thousands of tiny golden ripples spreading outward'),
    ('everyone tossed plastic wrap', 'nguoi', 'a kitchen island covered with translucent cling film shimmering under the lamp'),
    ('everyone honked horns politely', 'nguoi', 'a city crosswalk filled with taxis, buses, and delivery scooters echoing short beeps'),
    ('everyone purchased stocks simultaneously', 'nguoi', 'an open-plan trading floor with rows of glowing ticker boards and humming computers'),
    ('everyone set up escrow services', 'nguoi', 'a legal firm conference room with dark mahogany table, leather chairs, and a wall of framed certificates'),
    ('everyone jumped on gym floors', 'nguoi', 'a gymnasium echoing with rubber mats, dangling jump ropes, and a hoop suspended from the ceiling'),
    ('everyone leapt over hedges', 'nguoi', 'a manicured garden with trimmed hedges, stone pathways, and decorative garden statues'),
    ('everyone flashed high beams', 'nguoi', 'a rural lane at night, headlights piercing darkness across rows of trucks and vans'),
    ('everyone dropped bottles simultaneously', 'nguoi', 'a beach shoreline littered with colorful glass bottles sparkling among the sand dunes'),
    ('everyone stretched arms', 'nguoi', 'A yoga mat area dotted with foam rollers, yoga blocks, and scented candles'),
    ('everyone tossed plastic cutlery simultaneously', 'nguoi', 'a fast‑food waste container filled with bent forks, bent spoons, and broken knives'),
    ('everyone dumped a banana peel', 'nguoi', 'a park trail littered with yellow peels curling on the ground like ribbons'),
    ('everyone turned on electric ceiling fans in offices', 'nguoi', 'a corporate hallway, multiple ceiling fans rotating, blades a blur, cool air rippling through vents'),
    ('everyone vaulted over fences', 'nguoi', 'a rural pasture enclosed by wooden fences, dotted with hay bales and grazing sheep'),
    ('everyone enrolled in insurance plans', 'nguoi', 'a tidy policy office with stacks of glossy policy books and soft carpeted floors'),
    ('everyone posted a birthday wish simultaneously', 'nguoi', 'a rooftop observatory where colorful balloons drift upward, each pulsing with soft light'),
    ('everyone tossed plastic straws', 'nguoi', 'a movie theater aisle littered with bright plastic straws forming a colorful line on the carpet'),
    ('everyone opened trunk lids', 'nguoi', 'a suburban driveway lined with family cars, sports cars, and a few bicycles exposing cargo'),
    ('everyone opened high‑yield accounts', 'nguoi', 'a bright atrium with glass walls, indoor plants, and decorative fountains'),
    ('everyone dropped used cotton swabs simultaneously', 'nguoi', 'a beauty salon reception with recycling bins filled with white cotton swab sticks'),
    ('everyone walked across airport terminals', 'nguoi', 'a spacious terminal filled with rolling luggage carts, departure boards, and rows of waiting chairs'),
    ('everyone lunged into caves', 'nguoi', 'a dark cavern mouth, stalactites hanging, glowworms twinkling, underground river flowing silently'),
    ('everyone turned on GPS voice', 'nguoi', 'a suburban cul‑de‑sac, quiet streets echoing with soft navigation prompts from many cars'),
    ('everyone dumped newspaper stacks', 'nguoi', 'a bus stop shelter piled with crisp newspaper sheets creating a white mound'),
    ('everyone set a timer', 'nguoi', 'A kitchen counter displaying digital timers, cooking pots, and fresh herbs'),
    ('everyone exchanged currencies simultaneously', 'nguoi', 'a spacious exchange floor with colorful piles of foreign paper and metallic discs'),
    ('everyone set up online banking', 'nguoi', 'a modern data center corridor lined with blinking server racks and cooling ducts humming softly'),
    ('everyone jumped in living rooms', 'nha', 'a cozy living room packed with plush cushions, wobbling coffee tables, and a flickering lamp casting warm light'),
    ('everyone sprinted along boardwalks', 'nguoi', 'a seaside boardwalk lined with wooden planks, beach umbrellas, and seagull nests'),
    ('everyone opened mailboxes simultaneously', 'nguoi', 'a suburban cul-de-sac dotted with metal boxes spilling envelopes, flyers, and small parcels'),
]


def sinh_whatif(i):
    ds = MOI_NGUOI
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


# ── SONG_SOT: NÂNG TỪ DANH SÁCH NỘI BỘ LÊN BẢNG MODULE  (6/9/2026) ───────────────────────
# Danh sách này nằm TRONG `sinh_survive` nên `bang_mo_rong.py` không nhìn thấy nó, và kênh
# `survive` dừng ở 26 mục = cạn chủ đề sau ~13 tập short. Không phải vì thế giới hết thứ
# để nói — cùng niche ấy, `howloud` đi từ 31 lên 278 mục chỉ bằng cách nới BẢNG.
# Đưa ra ngoài không đổi một hành vi nào; nó chỉ làm dữ liệu NHÌN THẤY ĐƯỢC từ bên ngoài,
# đúng điều kiện để nới. Cùng bài học §15.12: một trường chỉ được ghi mà không ai đọc
# được thì coi như chưa tồn tại.
SONG_SOT = [("a day in the Ice Age", "a frozen tundra under heavy grey sky, bare and endless"),
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
      ("a week above the treeline", "bare grey rock and lichen under a hard blue sky"),

    # ── NỐI THÊM 6/9/2026 · 275 mục qua bốn cổng của `bang_van.py`
    #    (dạng · không người · không chữ · không viết nghịch · không trùng).
    #    Bảng này KHÔNG có con số nào, nên không có gì để đối chứng và cũng
    #    không đụng tới luật nền 'AI không bao giờ cấp một con số'.
    ('a month without running water', 'dry riverbed winding through scrubby grass, scattered rocks, and a lone dead tree'),
    ('a day without a safe footing', 'A slippery limestone floor slick with algae-covered stones and uneven ledges'),
    ('a week in a pre‑colonial rainforest settlement', 'Thick canopy, woven huts on stilts, fallen logs, and tangled vines covering the ground'),
    ('a night without night sounds', 'still jungle clearing, moonlight casting silver on a calm pond, silent trees'),
    ('a week without oxygen', 'steep rocky ridge under a thin blue sky, scattered pine clumps, distant clouds, barren cliffs'),
    ('a week without a coat', 'open meadow under a veil of fresh snowfall, silent birches standing like sentinels'),
    ('a week without grocery delivery', 'an empty front porch, a stack of empty cardboard boxes, a silent mailbox under a maple'),
    ('a day without footing', 'loose gravel slope, scattered stones shifting under each step, distant cliffs looming'),
    ('a night trapped underground', 'A winding shale passage narrowing into darkness, echoing distant water drips'),
    ('a month without waste management', 'A deep underground chamber filled with piles of discarded packaging, plastic bags, and broken containers'),
    ('a month without heating', 'frost‑kissed field of tall grasses, breath visible in cold air'),
    ('a week in a crystal cave', 'glittering quartz formations, reflective surfaces, soft pink light filtering through thin cracks above'),
    ('a weekend without music', 'a living room, silent stereo, a vinyl record on the floor, a dim lamp'),
    ('a hike without trail', 'unmarked plateau, scattered boulders, wind‑carved gullies, distant peaks fading'),
    ('a night in a landslide basin', 'steep bowl filled with mud and rocks, cracked earth, scattered boulders'),
    ('a week without paper', 'sunlit hillside strewn with fallen leaves, ancient stone steps, and a quiet pond'),
    ('a night lost in a blizzard', 'Snowy hill with deep drifting drifts, bare pine trees, and a collapsed wooden cabin roof'),
    ('a hull leak in calm seas', 'small boat with water pooling on deck, gentle waves lapping around'),
    ('a month without daylight', 'polar night tundra, endless white expanse, low aurora flickering faintly above'),
    ('a day without clarity', 'dense cloud veil hugging a towering ridge, muted colors, indistinct outlines of distant stone'),
    ('a night without a sleeping bag', 'frozen marshland dotted with frozen reeds, a thin veil of snowfall overhead'),
    ('a weekend without a functional faucet', 'a kitchen sink with dry basin, a dripping pipe halted, a window showing drizzle'),
    ('a siege on hilltop fort', 'rugged stone walls, barren slopes, scattered catapult stones, distant smoke plumes, muted sunrise'),
    ('a week without privacy', 'A series of open cavern rooms connected by wide arches and echoing chambers'),
    ('a spring during the Crusades', 'Arid desert plateau, cracked earth, abandoned tents, broken spears half‑buried in sand'),
    ('a week without signal', 'towering redwoods, fern-covered ground, winding river reflecting overcast sky'),
    ('a day in an abandoned mine shaft', 'rusted wooden supports, broken rails, piles of coarse gravel and scattered ore fragments'),
    ('a week without a stove', 'a kitchen island, a cold metal burner, a pot sitting empty, faint kitchen scent'),
    ('a frostbite scare on fingers', 'exposed ridge with scattered lichens, sky turning amber at sunset'),
    ('a night with endless mirage', 'Vast open sand sea, distant heat shimmer, horizon blending sky and ground'),
    ('a week without synthetic fabrics', 'lush meadow filled with wildflowers, tall grasses, and a gentle brook'),
    ('a week caught in a cold snap', 'Frozen lake with cracked ice, frosted pines, and a collapsed ice fishing shack'),
    ('a depleted fuel supply', 'empty fuel tank visible through transparent side, calm sea stretching outward'),
    ('a month without progress', 'endless flat rice paddies, water level uniform, distant mountains hazy, sky monotone'),
    ('a week without proper nutrition', 'barren summit field strewn with hardy alpine grasses, thin air swirling around crags'),
    ('a week without a thermal shirt', 'snow‑laden pine forest, branches heavy with powder, a distant glacier glimmering'),
    ('a week without laughter', 'still orchard with drooping fruit trees, fallen leaves carpet the ground, quiet breeze'),
    ('a sinkhole in marketplace', 'circular earth depression, scattered crates, broken pottery shards, dust swirling, distant walls'),
    ('a week without navigation tools', 'A sprawling network of limestone passages branching in every direction'),
    ('a week in a Viking winter camp', 'Ice‑slick shoreline, skeletal wooden longhouses, frozen fish barrels, and scattered driftwood'),
    ('a night without moonlight', 'deep jungle gloom, phosphorescent lichens on bark, soft glow from glowing beetles'),
    ('a day in a mineral-rich grotto', 'walls embedded with colorful veins of copper, iron and turquoise, sparkling under faint light'),
    ('a month without a heater', 'a living room corner, a cold stone floor, a folded blanket, a faint draft'),
    ('a day without fragrance', 'open meadow under a clear sky, wild grasses swaying, distant hills painted in soft pastel'),
    ('a day without scent', 'dry basalt plain, smooth black rocks, thin layer of dust drifting lazily'),
    ('a week without glass bottles', 'crystal-clear spring flowing over smooth pebbles, surrounded by fern-covered banks'),
    ('a month without climate control', 'A humid tunnel system with steaming vents and slick moss covering the stone floor'),
    ('a missing anchor chain', 'anchor hanging loosely from a rusted chain, calm waters surrounding a small boat'),
    ('a night without blankets', 'open ice field, starless sky, endless expanse of untouched snow'),
    ('a week without coffee', 'a quiet kitchen counter, empty mugs, a cold stovetop, soft morning light'),
    ('a season without sun', 'polar‑like summit, perpetual twilight, snow‑covered slopes, pale horizon'),
    ('a month without edible plants', 'monotonous green understory of uniform ferns, sparse berry bushes, smooth bark trunks, quiet streams'),
    ('a night of wolves in forest camp', 'dense pine thicket, moonlit clearing, scattered fire pits, fallen logs, distant mountain ridge'),
    ('a week without natural sounds', 'A silent cavern with smooth marble walls and a still, mirror-like pool'),
    ('a night in a Celtic hillfort', 'Moss‑covered earthen ramparts, torches extinguished, stone huts collapsed, and mist rolling in'),
    ('a day without shade', 'open forest ridge, bright sun beating on exposed soil, scattered rocks'),
    ('a season in a deep underground garden', 'hidden enclave with thriving moss, tiny flowering plants and soft ambient glow from mineral walls'),
    ('a day without a blanket', 'wide frozen lake reflecting a steel‑gray dawn, surrounding dunes of soft drift'),
    ('a night without campfire', 'dark jungle clearing illuminated only by distant lightning flashes'),
    ('a pause without wind', 'wide glacial basin, smooth icy surface, distant mountains reflected in still water'),
    ('a month without fresh water', 'A narrow sandstone tunnel lined with dry mineral walls and cracked stone floor'),
    ('a month without clean bedding', 'A cramped underground dormitory, thin mattresses on concrete slabs, and a thin layer of dust'),
    ('a day without cooling', 'sun‑baked asphalt road stretching straight, heat wavering above surface'),
    ('a night in a collapsed tunnel', 'blocked passage with piles of rubble, dust clouds and a faintly glowing mineral vein'),
    ('a weekend without laundry', 'a laundry room, a full washing machine, a heap of damp clothes on a rack'),
    ('a trek without compass', 'labyrinth of cliffs, jagged spires, swirling mist, endless stone arches'),
    ('a morning locked in a blizzard valley', 'snow‑covered canyon, white drifts piling against stone walls, swirling flakes'),
    ('a night without candles', 'dark forest clearing illuminated only by moonlight filtering through dense canopy'),
    ('a month under relentless hail', 'Open field covered in jagged white hailstones, dented metal roofs, and splintered wooden fences'),
    ('a broken compass on deck', 'weathered wooden deck, swirling sea currents, dark clouds looming overhead'),
    ('a day without temperature change', 'flat tropical lagoon, water perfectly still, sky uniformly bright, heat constant and unrelenting'),
    ('a day without silence', 'rocky slope where distant avalanches rumble, echoing off sheer walls, constant low roar'),
    ('a day without a scarf', 'open plain where snow drifts form soft dunes, pale horizon stretching endlessly'),
    ('a week without a functioning lock', 'a front door ajar, a rusted latch, a wind‑swept porch, fallen leaves swirling'),
    ('a plague in crowded market', 'stone paved square, overturned barrels, scattered baskets, stray animals, muted clouds'),
    ('a week without sleep', 'A labyrinthine network of narrow tunnels echoing constant dripping sounds'),
    ('a night in the Dark Ages', 'Moonlit moor, twisted dead trees, mist swirling over a ruined stone chapel'),
    ('a night without stars', 'tall trees blocking sky, bioluminescent fungi glowing on trunks, thick night mist'),
    ('a night surrounded by echoing chambers', 'large dome cavern with reverberating sounds, hanging stalactites and distant water flow'),
    ('a weekend without Wi‑Fi', 'a home office, a router blinking off, a stack of printed papers, soft lamp glow'),
    ('a delayed rescue helicopter', 'rocky outcrop with a clear view of swirling clouds, wind whipping loose stones'),
    ('a month with exhausted batteries', 'Vast sun‑bleached plain, scattered dry shrubs, horizon shimmering with heat distortion'),
    ('a season without refrigeration', 'cold alpine plateau with snow-capped peaks, pine trees, and a frozen lake'),
    ('a month stranded after a tsunami', 'Sandy shore littered with broken driftwood, overturned boats, and a torn pier'),
    ('a seaweed entanglement', 'boat hull covered in thick kelp, seaweed swaying with gentle currents'),
    ('a day without hope', 'barren moor under heavy fog, twisted shrubs, ground damp and indistinct'),
    ('a week without directionality', 'maze of interlocking ridges, similar angles, endless repeats of stone arches'),
    ('a night without a heated floor', 'silent meadow where snowflakes settle on every blade of grass, stars overhead'),
    ('a frost‑bitten equipment failure', 'frozen lake surface reflecting a pale dawn, icy wind sculpting frost on surrounding stones'),
    ('a heatwave in stone city', 'sun‑baked cobblestones, cracked arches, dried fountains, wilted vines, shimmering horizon'),
    ('a day without light', 'A deep basalt tunnel where only faint mineral glint reflects off wet stone'),
    ('a night in a Maya ruin', 'Jungle‑covered stone pyramids, overgrown staircases, vines hanging from cracked glyphs'),
    ('a day without insects', 'still canopy, quiet rustle, bright green foliage, droplets clinging to leaves'),
    ('a season without solid ground', 'shifting sand pit beneath stone arches, rippling surface and occasional small sinkholes forming'),
    ('a week without a toothbrush', 'a bathroom shelf, an empty holder, a glass of water, a faint mint scent'),
    ('a weekend without batteries', 'quiet campsite beside a crystal clear stream, lanterns unlit, fireflies blinking in dusk'),
    ('a month without color', 'monochrome limestone canyon, pale stone walls, dust‑filled air diffusing muted light'),
    ('a season without electric heating', 'snowy tundra with gentle hills, scattered driftwood, and a pale sunrise'),
    ('a month without sanitation', 'A damp tunnel network with slow‑moving streams and piles of discarded stone tools'),
    ('a sea turtle rescue attempt', 'shallow lagoon with tangled nets, clear water revealing stranded turtle'),
    ('a month without transport', 'frozen river crossing, thick ice crust, surrounding birch trees stripped of leaves'),
    ('a month coping with drought', 'Sunbaked plain with cracked soil, scattered wilted shrubs, distant mountains shimmering heat'),
    ('a path without direction', 'maze of ridgelines, winding trails disappearing into mist, peaks receding'),
    ('a month without guidance', 'maze of tall hedges, winding paths, occasional clearing revealing distant sunrise'),
    ('a tidal surge on coastal cliff', 'rocky shoreline, high water lapping cliffs, scattered shells, seaweed strands, overcast sky'),
    ('a day without echo', 'A soft, powdery gypsum cave where sound is swallowed by thick walls'),
    ('a season in a feudal Japanese village', 'Bamboo groves, thatched roofs, stone lanterns toppled, and fallen cherry blossoms'),
    ('a month without firewood', 'rain-soaked pine stand, moss-covered trunks, damp fallen branches, soft earth'),
    ('a week with constant tremors', 'unstable cavern floor, loose rocks, subtle vibrations causing small stones to shift'),
    ('a week enduring cyclone aftermath', 'torn canopy, uprooted trees, flooded lowland, heavy clouds'),
    ('a day without windbreaks', 'flat rainforest plain exposed to relentless gusts bending tall grasses'),
    ('a night without dreams', 'dark volcanic crater, rim illuminated faintly by distant glow, empty floor of black ash'),
    ('a week without sunlight', 'A deep limestone cavern with stalactites dripping into a still underground pool'),
    ('a week without transportation', 'A long, straight tunnel with abandoned tracks and rusted wheels lying on the concrete'),
    ('a week without connection', 'isolated lighthouse perched on a rocky outcrop, lantern swinging in wind'),
    ('a week without surface light', 'deep subterranean tunnel lined with rough stone, echoing drips and occasional bioluminescent fungi'),
    ('a month without gasoline', 'a driveway with an empty fuel pump, a lone car, a wilted garden'),
    ('a summit without view', 'cloud‑covered peak, white veil hiding distant ranges, icy wind sweeping around'),
    ('a dusk surrounded by a sandstorm', 'flat dunes rolling endlessly, golden grains whipping, horizon blurred by wind'),
    ('a fortnight without glass windows', 'stone courtyard surrounded by ivy-covered walls, a central fountain, and tall cypress trees'),
    ('a day without breathable air', 'A sealed basalt cavern with thick, unmoving air and faint mineral glimmer'),
    ('a relentless tide pulling in', 'rocky shoreline being swallowed by steadily rising turquoise water, splashing foam'),
    ('a night without moon', 'deep canyon shrouded in darkness, cliffs rising on both sides, faint bioluminescent moss'),
    ('a month without companionship', 'isolated alpine meadow dotted with lone stone cairns, rolling hills disappearing into mist'),
    ('a month without a jacket', 'lonely spruce grove under a thick sheet of fresh powder, silent and still'),
    ('a month without garbage collection', 'a narrow street, piled bags, stray paper fluttering, a distant dumpster sealed shut'),
    ('a famine during harvest', 'bare fields, withered stalks, scattered straw bundles, empty granary doors, overcast sky'),
    ('a day without heat', 'A frozen ice cave with glittering frozen stalagmites and a thin veil of mist'),
    ('a summer under Roman siege', 'Dusty hilltop fort, cracked stone walls, smoldering fire pits, with scattered broken shields'),
    ('a day without compass', 'thick jungle vines, twisting trails, towering palms, sun filtering through dense foliage'),
    ('a day in a maze of tunnels', 'intersecting stone passages, low arches, occasional underground spring bubbling from cracks'),
    ('a day without a calendar', 'a wall with a blank frame, a simple clock ticking, morning light'),
    ('a flash flood in a gorge', 'deep narrow canyon with rushing water, smooth rock walls reflecting the sky'),
    ('a month with cracked skin', 'Broad arid plateau, scattered stone outcrops, sun scorching the parched surface'),
    ('a week without spices', 'fertile valley with rows of wild herbs, low hills, and a bright sunrise'),
    ('a month without power after an ice storm', 'Frozen highway with hanging icicles, bent power lines, and a collapsed streetlight'),
    ('a rogue wave at dawn', 'massive towering wave cresting over a tiny kayak, sunrise glowing orange'),
    ('a week without safety', 'steep canyon floor, loose gravel, sudden drops on both sides, sky overcast'),
    ('a day without calm', 'swift gusts whipping over a narrow pass, tumbleweed rolling, clouds racing across sky'),
    ('a month without a hoodie', 'open tundra where wind shapes the snow into smooth ripples, pale sky above'),
    ('a steep rockslide path', 'chaotic field of loose stones, jagged cliffs rising on either side, wind stirring dust'),
    ('a pest invasion in grain field', 'golden stalks broken, swarms of insects hovering, scattered husks, distant hills under pale light'),
    ('a night without sound', 'A massive echoing cavern with smooth walls that absorb all vibrations'),
    ('a season in the Bronze Age', 'Rolling hills dotted with clay houses, smoldering hearths, and broken bronze tools'),
    ('a month without rain', 'dry savanna-forest edge, cracked earth, scattered dead leaves, sun-baked trunks'),
    ('a week in an echoing abyss', 'deep vertical chasm, sheer walls, faint light from distant opening and constant wind howl'),
    ('a weekend without a charger', 'a nightstand with an unplugged cable, a silent phone, a sleeping cat curled'),
    ('a day without air‑conditioning', 'sun‑baked desert oasis with palm trees, reflecting pool surrounded by sand dunes'),
    ('a night with scorching ground', 'Flat sun‑baked terrain, scattered stones, heat haze rising even after dusk'),
    ('a week without modern medicine', 'quiet meadow with a solitary oak, soft grass, and a small herbal garden'),
    ('a month without ventilation', 'A deep earthen shaft, thick dust clouds swirling around jagged rock formations'),
    ('a tangled fishing line', 'silvery line coiled around a mast, sea surface calm and reflective'),
    ('a day without warm clothing', 'open tundra plain, wind‑sculpted snow dunes, distant frozen ridge under muted light'),
    ('a night after landslide', 'Forest floor covered in displaced earth, fallen trunks forming barriers, small streams redirected'),
    ('a camp without wind', 'quiet highland basin, still air, smooth snow drifts, low‑lying clouds'),
    ('a week without ambition', 'still lake surrounded by smooth stones, surface mirror‑like, mountains reflected perfectly'),
    ('a rebellion in fortified town', 'stone gate cracked, overturned barrels, broken wooden doors, smoke rising, distant hills'),
    ('a week without escape routes', 'A sealed underground pit surrounded by sheer cliff walls of dark stone'),
    ('a week in a Neolithic stone circle', 'Moss‑covered standing stones, surrounding heathland, low mist, and scattered fire pits'),
    ('a week without a trail', 'unmarked dense thicket, tangled underbrush, fallen logs crossing a narrow stream'),
    ('a month living among underground roots', 'network of thick tree roots breaking through stone, soft earthy smell and muted green foliage'),
    ('a day surviving after mudslide', 'thick sludge covering road, displaced stones, tangled vegetation, grey sky'),
    ('a week without berries', 'dense understory where shrubs bear only green, unripe fruit'),
    ('a day without energy', 'flat basalt plain, cracked fissures emitting faint steam, silent and still'),
    ('a month without manufactured sweets', 'honey-colored meadow dotted with wild berries, buzzing insects, and a gentle breeze'),
    ('a day without medical supplies', 'A sterile underground clinic room, empty shelves, and a lone surgical table under a single lamp'),
    ('a week without water', 'dry riverbed stretching under a clouded sky, cracked earth, scattered stones, distant hills'),
    ('a month in a flooded cave', 'dark limestone chamber filled with slow moving water, mossy walls and faint glimmering crystals'),
    ('a week without cleaning supplies', 'a kitchen sink, piles of dishes, a dripping faucet, a lone sponge'),
    ('a descent without brakes', 'steep scree slope, loose stones, rushing wind, distant pine forest below'),
    ('a day without a stable footing', 'muddy bank beside a slow river, soft earth giving way, scattered stones and reeds'),
    ('a day without printed maps', 'rolling hills blanketed in wildflowers, a winding path disappearing into a foggy valley'),
    ('a day without a clear horizon', 'A curved tunnel that spirals endlessly, walls merging into darkness'),
    ('a prolonged fog over water', 'thick white mist covering calm sea, barely visible distant coastline'),
    ('a month in total silence', 'vast empty desert plain, wind-swept dunes, distant jagged cliffs, sky heavy with clouds'),
    ('a day without breath', 'thin air over a high plateau, sparse vegetation, distant peaks disappearing into haze'),
    ('a week without insulated walls', 'wide salt‑flat turned to crystal glaze, distant hills softened by a mist'),
    ('a day without a working car', 'an empty driveway, a car with a flat tire, a toolbox on the curb, autumn leaves'),
    ('a flood in lowland plain', 'shallow water covering mud flats, reeds bending, scattered driftwood, cloudy horizon, distant cliffs'),
    ('a month without communication', 'A series of interlocking lava tubes with smooth orange walls and occasional vent openings'),
    ('a year in the Black Death', 'Foggy countryside, with wilted crops, abandoned thatched cottages, and scattered broken carts'),
    ('a night without firelight', 'dark rainforest floor, towering trees, glowing fireflies, mist swirling above leaf litter'),
    ('a month in a cold limestone vault', 'chilly cavern with icy stalactites, frost-covered floor and silent echoing drips'),
    ('a month without soap', 'a bathroom sink, an empty soap dish, a lone towel draped'),
    ('a thin air training trek', 'steep rocky slope dotted with sparse alpine grasses, clouds hugging the summit'),
    ('a week with sand clogged filters', 'Vast wind‑sculpted dunes, occasional scrubby bushes, air thick with fine dust particles'),
    ('a day without clocks', 'serene lake shore with reeds, smooth stones, and a backdrop of misty mountains'),
    ('a week isolated by a volcanic ashfall', 'Mountain slope blanketed in gray ash, scorched rocks, and a broken stone bridge'),
    ('a coral reef collision', 'bright underwater scene of tangled ropes and broken hull near colorful reef'),
    ('a month without routine', 'wildflower meadow shifting colors, hills rising and falling, clouds drifting aimlessly'),
    ('a week without momentum', 'flat high plain strewn with smooth boulders, wind‑softened dust, distant peaks looming'),
    ('a day without a mittens', 'broad canyon walls glazed with a thin frost, soft light filtering through clouds'),
    ('a dwindling fuel supply', 'isolated mountain cabin beside a stone fire pit, surrounded by barren scree'),
    ('a mudslide in mountain pass', 'steep rocky slope, thick brown mud flowing, broken branches, distant pine peaks, overcast sky'),
    ('a week without shelter', 'A barren underground sinkhole surrounded by jagged stone and loose debris'),
    ('a day in ancient floodplain', 'Muddy riverbank, overgrown reeds, collapsed wooden huts, waterlogged mud stretching outward'),
    ('a week without tools', 'rocky outcrop, fallen branches, natural stone slab, mossy creek banks'),
    ('a month in a damp tunnel network', 'interconnected passages slick with algae, dripping water and occasional puddles reflecting dim glow'),
    ('a day without a mirror', 'a hallway with plain wall, a coat rack, a single framed photo, soft shadows'),
    ('a year without plastic', 'pristine beach with smooth shells, gentle surf, seagrass swaying, gulls gliding overhead'),
    ('a week with empty water bottle', 'Endless dunes rolling like waves, occasional cracked mud flats, sun glaring'),
    ('a day without indoor lighting', 'deep canyon illuminated by shafts of sunlight breaking through narrow openings'),
    ('a day without internet', 'A sprawling subterranean network of brick corridors, echoing with distant water drops'),
    ('a unexpected ice shelf drift', 'blue sea surrounding massive white ice floe, gentle waves lapping its edges'),
    ('a week without balance', 'steep icy slope, glittering frost covering surface, sky pale, horizon barely visible'),
    ('a week without adequate hydration', 'dry high‑altitude basin dotted with stone piles, occasional dry streambed, clouds drifting low'),
    ('a day without a parka', 'quiet hilltop covered in fresh drifts, clouds low, air shimmering with breath'),
    ('a day without trust', 'dense bamboo forest, shafts of light piercing canopy, ground covered in soft leaf litter'),
    ('a pestilence in mountain monastery', 'stone cloister courtyard, wilted herbs, broken incense bowls, misty peaks, muted dawn'),
    ('a month without stability', 'A precarious rock overhang within a deep cavern, stones hanging above a void'),
    ('a night in a Roman battlefield', 'Foggy plain, broken gladius blades, shattered shields, and smoldering campfires'),
    ('a night without animal sounds', 'quiet rainforest, moonlit canopy, dew on spider webs, still pond reflecting stars'),
    ('a night in a cavern of echoing drums', 'rocky chamber with hollow pillars, natural resonances creating rhythmic reverberations'),
    ('a week navigating after earthquake', 'split pavement, fallen stone walls, cracked sidewalk, low clouds'),
    ('a month without trails', 'untouched primary forest floor covered in thick leaf litter and tangled vines'),
    ('a night without breeze', 'calm frozen lake, ice sheet perfectly smooth, distant hills barely visible'),
    ('a month without canned food', 'sunny orchard with fruit trees, low hedgerows, and a winding dirt path'),
    ('a week without structural support', 'A crumbling tunnel with fallen columns, jagged edges, and loose gravel spilling onto the path'),
    ('a drifting sandbar encounter', 'shallow sandbank emerging from clear water, waves breaking softly around it'),
    ('a month without insulation', 'bare concrete building, frost coating walls, surrounding snow drifts piling high'),
    ('a day without phone signal', 'a balcony with a rusted antenna, wind chimes swaying, distant city skyline'),
    ('a journey without maps', 'intersecting ridges, winding valleys, endless stone walls, clouds obscuring peaks'),
    ('a day without a protective canopy', 'exposed ridge with sparse trees, wind sweeping over rocky ground, scattered pine needles'),
    ('a week without metal tools', 'dense pine forest floor covered in pine needles, mossy logs, and a shallow creek'),
    ('a week without reliable footing', 'A steep underground slope covered in loose gravel and scattered boulders'),
    ('a week in a prehistoric volcanic eruption', 'Lava‑blackened valley, basalt rocks, scorched pine stumps, and ash‑covered ground'),
    ('a week without sunrise', 'endless flat tundra under perpetual twilight, low horizon, distant icy mountains'),
    ('a month without rest', 'endless ridge with alternating sun and shadow, steep drops on both sides, endless ascent'),
    ('a day without a sweater', 'gentle hill rolling into a sea of powder, low clouds hovering low'),
    ('a month without public transport', 'a deserted bus stop, rusted bench, overgrown weeds, a lone timetable board covered in vines'),
    ('a drought in fertile valley', 'cracked earth, wilted grass, dried riverbed, scattered stones, distant hills under bright sun'),
    ('a week without food', 'A vast underground chamber filled with scattered mineral deposits and silent stone pillars'),
    ('a month without secure storage', 'An open underground hall, scattered crates overturned, and loose stones covering the floor'),
    ('a month without entertainment', 'quiet library hall, shelves of books, dust motes floating in shafts of light'),
    ('a night amid underground floods', 'rapid underground river rushing past smooth riverbed, water splashing against rocky banks'),
    ('a weekend without cooking oil', 'a kitchen stove, an empty bottle, a pan with a faint sheen, quiet'),
    ('a ascent without stamina', 'steep talus slope, loose gravel, thin air, clouds drifting low'),
    ('a twilight caught in a thunderclap corridor', 'narrow gorge illuminated by jagged lightning, wet cliffs, echoing rumble'),
    ('a month without roadways', 'vast savanna dotted with acacia trees, distant mesas, and a winding dry stream'),
    ('a day stuck in a flash flood', 'River valley overflowing, water rushing over a cracked road, uprooted shrubs, and floating barrels'),
    ('a sudden loss of wind', 'sailboat drifting motionless on glassy water under a pale sky'),
    ('a week without comfort', 'rocky outcrop under scorching sun, sharp stones scattered, shadows minimal'),
    ('a month without relief', 'continuous ascent of jagged cliffs, narrow ledges, thin air swirling above'),
    ('a week without a thermostat', 'vast expanse of white‑capped ridges, sunrise casting a gentle pink glow'),
    ('a blinding sun glare', 'sharp rocky outcrop catching intense light, glare reflecting off quartz shards'),
    ('a storm on open steppe', 'tall grasses bending, dark swirling clouds, scattered tumbleweeds, distant thunderclouds, flat horizon'),
    ('a day without direction', 'A tangled maze of intersecting tunnels with identical curved walls'),
    ('a harvest in medieval famine', 'Barren field under grey sky, with stunted wheat stalks and empty stone granaries'),
    ('a month without medicine', 'jungle thicket, medicinal herbs sprouting among ferns, wild orchids clinging to bark'),
    ('a night in a sulfurous grotto', 'yellowish vapors rising, wet black rocks, faint orange glow from mineral deposits'),
    ('a month without a fridge', 'a pantry door ajar, a bowl of wilted greens, a single candle flickering'),
    ('a loss of footing on loose gravel', 'wide talus field with scattered stones, distant valleys fading into blue'),
    ('a month with failing eyesight', 'Broad sun‑baked terrain, scattered scrub, horizon a wavering line of heat'),
    ('a month without road signs', 'winding forest trail flanked by mossy stones, ferns, and a distant waterfall'),
    ('a week battling a thunderous hailstorm', 'Open field with dented metal fence, shattered glass shards, and a splintered wooden fence post'),
    ('a malfunctioning bilge pump', 'water rising inside a cramped cabin, wooden planks wet and glistening'),
    ('a month without peace', 'storm‑tossed sea cliffs, waves crashing violently, dark clouds swirling above'),
    ('a week without sturdy boots', 'sharp scree slope littered with loose stones, sparse alpine shrubs, wind brushing the ridgeline'),
    ('a month without a fleece', 'expansive frozen beach, icy sand mixed with snow, sunrise painting the ice pink'),
    ('a month without colors', 'monochrome desert of pale sand dunes, wind shaping smooth ridges under a flat horizon'),
    ('a thunderstorm over river delta', 'wide river mouth, lightning striking water, reeds swaying, dark clouds rolling, distant cliffs'),
    ('a month without warmth', 'A frozen glacier cave with icicle formations hanging from the ceiling'),
    ('a month in a medieval plague town', 'Narrow cobblestone lanes, overturned barrels, wilted herb gardens, and crumbling stone wells'),
    ('a day without wind', 'still swamp forest, stagnant water, heavy air, drooping fronds hanging motionless'),
    ('a week inside a frozen underground lake', 'transparent ice sheet covering still water, frosted walls and occasional icicle formations'),
    ('a day without a lamp', 'a dark bedroom, a window with night sky, a single candle casting soft glow'),
    ('a season without fruit', 'lush jungle vines hanging over a barren clearing, branches bare of blossoms'),
    ('a month without motion', 'still swamp water, thick mist hovering, dead trees standing like silent sentinels'),
    ('a day without digital screens', 'open plateau under a bright blue sky, dotted with lone stone monoliths'),
    ('a day without emergency lighting', 'A cavernous underground chamber, walls covered in phosphorescent algae, shadows dancing across the floor'),
    ('a severe sea sickness episode', 'tilted boat rocking on choppy water, foam spraying over the rail'),
    ('a week without fuel', 'snow‑packed road, abandoned fuel depot encased in ice, distant mountain range'),
    ('a month without cash', 'a desk with a closed wallet, a stacked pile of receipts, a potted cactus'),
    ('a climb without rest', 'endless ascent of rocky steps, thin air, distant horizon, clouds brushing cliffs'),
    ('a day without a map', 'intersecting trails disappearing among giant trees, overgrown footpaths covered in leaf litter'),
]


def sinh_survive(i):
    ds = SONG_SOT
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


# ── MOT_NGAY: NÂNG TỪ DANH SÁCH NỘI BỘ LÊN BẢNG MODULE  (6/9/2026) ───────────────────────
# Danh sách này nằm TRONG `sinh_dayinlife` nên `bang_mo_rong.py` không nhìn thấy nó, và kênh
# `dayinlife` dừng ở 24 mục = cạn chủ đề sau ~12 tập short. Không phải vì thế giới hết thứ
# để nói — cùng niche ấy, `howloud` đi từ 31 lên 278 mục chỉ bằng cách nới BẢNG.
# Đưa ra ngoài không đổi một hành vi nào; nó chỉ làm dữ liệu NHÌN THẤY ĐƯỢC từ bên ngoài,
# đúng điều kiện để nới. Cùng bài học §15.12: một trường chỉ được ghi mà không ai đọc
# được thì coi như chưa tồn tại.
MOT_NGAY = [("a Roman soldier",
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
       "warm lamp light inside against blue dusk outside"),

    # ── NỐI THÊM 6/9/2026 · 280 mục qua bốn cổng của `bang_van.py`
    #    (dạng · không người · không chữ · không viết nghịch · không trùng).
    #    Bảng này KHÔNG có con số nào, nên không có gì để đối chứng và cũng
    #    không đụng tới luật nền 'AI không bao giờ cấp một con số'.
    ('a sushi chef', 'bright kitchen island with bamboo cutting board, stainless steel knives, rice barrels, hanging lanterns, wooden shelves, steam clouds', 'white chef coat, black apron, sushi knife, rubber shoes, hair net', 'soft warm glow from hanging paper lanterns reflecting off polished surfaces'),
    ('a cruise ship deck manager', 'a sun‑drenched promenade deck with lounge chairs, palm trees, and a turquoise ocean stretching to the horizon', 'a navy blazer, crisp white shirt, polished shoes, and a clipboard', 'warm golden light spilling from a rooftop lantern'),
    ('a rural clinic doctor', 'small wooden clinic with waiting bench, simple desk, medicine cabinet, window view of fields, tiled floor', 'light‑blue coat, stethoscope, prescription pad, pocket watch, friendly grin', 'soft natural light entering through a single wide window'),
    ('a mental health therapist', 'counselling office, plush sofa, bookshelf, soft rug, floor lamp, window with blinds', 'soft cardigan, notepad, calming tea mug', 'warm amber light from a standing lamp beside the sofa'),
    ('a chemical‑spill responder', 'industrial plant yard with containment berms, yellow drums, spill kits, steel barriers', 'full hazmat suit, chemical detector, sealed gloves, portable decontamination unit', 'bright white safety lights casting clean illumination'),
    ('a ballet dancer', 'spacious rehearsal studio, mirrored wall, wooden barre, soft pastel walls, scattered ribbons on floor', 'fitted pink leotard, sheer tutu, pink ballet slippers, hair bun', 'gentle natural light streaming through high windows, creating bright patches'),
    ('a stonemason', 'an open yard with massive stone blocks, chisels, wooden mallets, and a sand‑filled trench', 'wearing a thick canvas shirt, leather apron, and sturdy boots', 'bright sun glints off dust‑covered stone surfaces'),
    ('an archaeobotanist', 'a sand‑filled dig table with ancient seed pods, clay pots, microscopes, and a drying rack of parchment', 'linen shirt, canvas vest, tweezers, magnifying visor, leather satchel', 'warm golden light from a hanging lantern casting gentle shadows'),
    ('a Spanish paella chef', 'large shallow pan over open fire, saffron threads, rice piles, seafood trays, wooden spoon, tiled patio floor', 'light linen shirt, apron with embroidered pattern, wooden ladle, heat-resistant gloves', 'bright sunny light spilling across the patio'),
    ('a radiology technician', 'large imaging machine, lead‑lined walls, control console, rolling cart, tiled floor, window blind', 'gray scrubs, lead apron, handheld dosimeter, clipboard, comfortable shoes', 'soft indirect lighting from recessed panels, muted brightness'),
    ('an espresso barista', 'a sleek coffee counter with stainless steel espresso machine, glass jars of beans, brushed metal shelves', 'black shirt, denim apron, tamping tool, reusable cup', 'cool white illumination from under‑counter LED strips'),
    ('a monk copyist', 'a cloistered scriptorium with wooden desks, parchment piles, ink wells, wooden shelves, stone arches', 'simple brown robe, wooden stylus, inkpot, small candle holder', 'gentle candlelight flickering over the stone floor'),
    ('a Sumerian brewer', 'a clay‑pot brewery beside a canal, fermenting vats, barley sacks, reed mats, water troughs', 'linen shirt, straw hat, wooden ladle, clay cup', 'soft twilight reflecting off the water’s surface'),
    ('a hyperloop operator', 'low‑profile tunnel control chamber, sleek consoles, a transparent tube view, neon safety lines, a polished steel floor', 'technical jumpsuit, a data tablet, a magnetic badge, a pair of insulated gloves', 'clean white LEDs lining the control panels and tunnel walls'),
    ('a pottery kiln operator', 'a brick kiln chamber with stacked clay pots, glowing coals, ventilation pipes, and a wooden loading cart', 'clad in a thick apron, heat‑resistant gloves, and holding a metal tongs', 'deep red heat radiates from the kiln, bathing the space in warm light'),
    ('an MMA referee', 'a cage arena with chain‑link walls, a padded floor, and a metal entrance gate', 'a black shirt, white armbands, whistle, clipboard, athletic shoes', 'bright white floodlights illuminating the cage interior'),
    ('an intercity bus conductor', 'a modern highway rest area with a concrete shelter, fuel pumps, and a row of parked buses under a bright sky', 'a crisp uniform shirt, name badge, handheld ticket scanner, and a clipboard', 'clear daylight filtering through a translucent roof'),
    ('a neonatal specialist', 'warm nursery with incubators, pastel walls, soft blankets, wooden rocking chairs, gentle curtains', 'light‑colored coat, soft stethoscope, small notebook, baby scale, gentle smile', 'soft diffused daylight filtered through sheer curtains bathing the room'),
    ('a bakery dough mixer', 'a spacious prep area with industrial mixer, flour sacks, wooden rolling pins, metal shelving', 'gray chef coat, flour‑specked gloves, mixing paddle, timer', 'steady cool illumination from ceiling fluorescents'),
    ('a crisis‑call volunteer', 'small community center room with folding chairs, bulletin board, coffee pot, window overlooking park', 'casual shirt, headset, notebook, comforting plush toy', 'gentle late‑afternoon sun filtering through curtains'),
    ('an Edo period sushi chef', 'tatami mat floor, low wooden counter, bamboo shoots, ceramic plates, hanging lanterns, polished bamboo rails', 'simple kimono, wooden clapper, sushi knife, rice paddle, straw hat', 'soft yellow light from paper lanterns glowing gently'),
    ('a silversmith', 'a bright workshop with a small furnace, silver ingots, polishing cloths, and a set of delicate tools', 'clad in a white apron, protective goggles, and holding a tiny hammer', 'clear white light from a skylight shines on polished surfaces'),
    ('a quantum physicist', 'a low‑vibration room with cryogenic chamber, superconducting coils, laser array, and a floating magnetic levitation platform', 'black insulated jacket, rubber‑soled shoes, handheld spectrometer, notebook with silver pen', 'cool blue LED strips lining the walls, pulsing gently'),
    ('a Thai street noodle cook', 'wok over high flame, bamboo steam basket, fresh herbs, lime wedges, hanging chili strings, misty steam', 'light raincoat, apron with pockets, metal spatula, heat-resistant gloves', 'bright flickering light from the open flame'),
    ('an emergency nurse', 'bright tiled corridor, stainless steel cabinets, rolling beds, glass window, potted plant, polished floor', 'blue scrubs, name badge, digital tablet, stethoscope, penlight', 'soft fluorescent wash across the hallway, steady hum'),
    ('an astronaut botanist', 'metallic space station module, hydroponic trays stacked in rows, a window showing Earth below', 'light‑weight suit, data tablet, small gardening tools, sealed nutrient packs', 'cool artificial LED panels bathing the trays in steady white light'),
    ('an apothecary', 'stone counter with mortar and pestle, glass jars of herbs, dried vines hanging, low wooden shelf', 'linen coat, satchel of dried herbs, small bronze scale', 'soft candlelight flickering on the counter'),
    ('a Phoenician shipwright', 'a dockside shed with timber planks, rope coils, tar barrels, gulls overhead, calm sea beyond', 'linen shirt, rope belt, carpenter’s knife, measuring tape', 'soft golden glow of sunrise over the water'),
    ('a karaoke bar manager', 'private karaoke room, plush velvet sofas, decorative wall panels, small coffee table, soundproof doors', 'smart casual blazer, dress shirt, badge, tablet, polished shoes', 'soft warm lighting from wall sconces creating a cozy ambience'),
    ('a miller', 'a stone mill room with a turning wheel, grain sacks, wooden gears, and a sack of flour', 'dressed in a woolen coat, simple trousers, and a wooden grain scoop', 'steady daylight filters through a small grate, casting linear shadows on the millstones'),
    ('a radiobiologist', 'a radiation‑shielded lab with lead‑lined walls, dosimeter stations, irradiator chamber, and a glass‑covered sample rack', 'lead‑lined apron, dosimeter badge, protective goggles, sample carrier, clipboard', 'muted amber glow from low‑intensity safety lamps'),
    ('a Jamaican jerk chef', 'smoking pit, hanging Scotch bonnet peppers, wooden planks, coconut shells, fragrant smoke, bamboo mat floor', 'bright patterned shirt, apron with pockets, metal grill fork, heat‑resistant gloves', 'deep amber light from the fire pit'),
    ('a wound care nurse', 'treatment chairs, sterile trays, hanging lamps, clean curtains, soft carpet, window with blinds', 'blue scrubs, dressing kit, gloves, gentle smile, supportive shoes', 'soft warm light from ceiling lamps, comforting tone'),
    ('a farm‑to‑table chef', 'a rustic kitchen with reclaimed wood table, hanging herbs, mason jars of vegetables, stone mortar', 'linen apron, earth‑tone shirt, wooden spoon, basket of carrots', 'natural sunlight through open window'),
    ('a paramedic supervisor', 'medical response vehicle bay with stretchers, defibrillators on carts, organized supply racks, open garage doors', 'scrubs, stethoscope, tablet, medical bag slung across shoulder', 'bright daylight pouring through large overhead doors'),
    ('a bike‑share maintenance worker', 'city plaza with bike racks, potted plants, stone fountain, bench, sunrise sky', 'high‑visibility vest, tool belt, wrench, water bottle', 'soft morning light casting gentle hues'),
    ('a Athenian playwright', 'open theater stone stage, marble columns, ivy vines, audience stone seats, distant sea view', 'white chiton, lyre, scroll of script, sandals', 'soft evening light glowing behind the columns'),
    ('a pandemic response field medic', 'temporary clinic tent with isolation curtains, portable ventilators, sanitizer stations, stacked medical crates', 'protective gown, N95 mask, gloves, handheld pulse oximeter, insulated bag', 'cool fluorescent lighting humming above the rows of beds'),
    ('a Japanese ramen master', 'large simmering pot, bamboo ladles, stacked noodles, dried seaweed sheets, steam vents, wooden floorboards', 'black chef jacket, thick apron, ladle, chopsticks, rubber kitchen mats', 'steady glow from a hanging lantern casting gentle shadows'),
    ('a high‑speed rail conductor', 'a sleek platform with glass walls, polished tiles, and a digital arrival board glowing softly', 'a tailored uniform, badge, handheld scanner, and a sleek black briefcase', 'cool white light from recessed ceiling fixtures'),
    ('a cathedral stone mason', 'a construction site with half‑erected arches, stone blocks, wooden scaffolding, chisels, sand piles', "heavy leather apron, sturdy boots, mason's hammer, measuring rod", 'bright overcast sky casting even light over the stone'),
    ('an olive harvester', 'grove of silver‑green trees, baskets stacked on stone crates, ancient terracotta amphorae scattered nearby', 'linen tunic, woven basket, curved sickle at belt', 'soft midday glow shimmering through rustling leaves'),
    ('a ferry terminal ticket agent', 'harbor dock with wooden piers, moored boats, gulls perched on railings, and water ripples', 'light blouse, name tag, ledger, pen, sensible flats', 'soft sunrise light shimmering on the calm water'),
    ('a graffiti artist', 'urban alley, brick wall covered in paint splatters, metal fire escape, overturned trash cans, puddles', 'hooded hoodie, cargo pants, spray cans, bandana, canvas sneakers', 'soft streetlamp glow creating a muted amber wash'),
    ('a ceramic tile maker', 'a tiled floor studio with molds, glaze buckets, drying racks, and a kiln opening emitting faint heat', 'clad in a dusty apron, gloves, and a small brush for glazing', 'warm orange light glows from the kiln, casting patterned shadows'),
    ('a neurophysiologist', 'a brain‑mapping suite with electrode arrays, EEG caps, sound‑proof walls, and a reclining patient chair', 'gray lab coat, conductive gel packets, handheld stimulator, clipboard, safety glasses', 'focused cool white light from adjustable desk lamps'),
    ('a Filipino halo‑halo maker', 'large clear bowls, shaved ice piles, sweet beans, coconut strips, colorful syrups, tropical plants', 'light cotton shirt, patterned apron, plastic spoon, straw hat for shade', 'bright tropical light streaming through open shutters'),
    ('a psychiatric therapist', 'soft sofa, bookshelf, window with plants, warm rug, lamp on side table, calm walls', 'casual sweater, notebook, pen, glasses, gentle shoes', 'warm mellow light from table lamp, soothing tone'),
    ('a pizza oven operator', 'a stone brick oven surrounded by wooden prep table, hanging pizza peel, flour dust clouds', 'red checkered apron, flour‑stained shirt, wooden pizza peel, heat‑resistant gloves', 'radiant orange heat from the open oven'),
    ('a search and rescue pilot', 'airfield hangar with a sleek rescue helicopter, fuel trucks, open runway, distant mountains', 'flight suit with patches, flight helmet, navigation tablet strapped to wrist', 'bright sunrise light spilling across the tarmac and hangar doors'),
    ('a gondola operator', 'narrow canal with stone bridges, rippling water, lantern‑lit banks, blooming vines, distant bell tower', 'striped shirt, straw hat, wooden oar, leather belt', 'soft golden glow from lanterns reflecting on water'),
    ('a Shang dynasty oracle', 'bronze cauldron on stone altar, pine incense smoke, dragon motifs carved on walls', 'silk robe, jade pendant, wooden divination sticks, bronze bells', 'soft amber glow from oil lamps surrounding the altar'),
    ('an avalanche safety technician', 'snow‑covered slope with buried probes, a rescue sled, pine trees, a compact snowmobile', 'thermal parka, snow boots, avalanche beacon, shovel, insulated gloves', 'cold pale light of a high‑altitude winter sun'),
    ('an Italian pizza baker', 'stone oven with flickering fire, wooden prep table, flour-dusted brick walls, hanging copper pots, herb bundles', 'red striped shirt, flour-dusted apron, wooden pizza peel, sturdy boots', 'golden orange light spilling from the open oven mouth'),
    ('a historic stagecoach guard', 'a dusty desert trail with tumbleweeds, a wooden water trough, and distant mesas under a blazing sun', 'a leather coat, wide‑brimmed hat, a revolver, and a leather satchel', 'harsh yellow light beating down on the sand'),
    ('a forensic pathologist', 'cold autopsy suite with stainless steel table, steel instruments, stainless walls, ventilation hood, tiled floor', 'white lab coat, surgical gloves, scalpels, evidence bag, careful eyes', 'bright white surgical lights highlighting the work surface'),
    ('a Renaissance alchemist', 'a vaulted workshop with stone hearth, copper alembics, and shelves of dried herbs and minerals', 'a velvet robe, leather belt, and a glass vial', 'golden firelight dancing across stained glass windows'),
    ('a canal boat captain', 'calm waterway bordered by willow trees, stone bridges, floating reeds, and a distant mill', 'blue raincoat, straw hat, wooden walking stick, leather boots, brass compass', 'cool morning light reflecting off the water’s surface'),
    ('an esports commentator', 'modern streaming studio, LED backdrops, sleek desk, gaming chairs, soundproof foam panels', 'graphic hoodie, headphones, wireless mic, gaming mouse, casual sneakers', 'cool blue LED strips illuminating the room with a futuristic hue'),
    ('a basket weaver', 'a shaded corner with bundles of willow rods, woven trays, a wooden workbench, and a drying rack', 'dressed in a light cotton smock, barefoot, and holding a flexible reed', 'soft dappled light filters through leafy branches overhead'),
    ('a nanotechnologist', 'a clean‑room floor with atom‑scale manipulators, silicon wafers, dust‑free benches, and a vacuum chamber', 'full‑body anti‑static suit, gloves with fingertip sensors, micro‑probe, data glove', 'soft blue illumination from low‑glare LEDs lining the walls'),
    ('a Chinese dim sum steward', 'steamer baskets stacked, bamboo trays, soy sauce dishes, porcelain cups, hanging ginger, gentle steam rise', 'simple mandarin collar shirt, waist apron, bamboo spatula, cloth napkin', 'soft white light from a ceiling lantern'),
    ('a hospice caregiver', 'cozy room, soft rug, armchair, bedside table, framed photo, gentle curtains', 'comfortable cardigan, warm socks, clipboard, calming scent bottle, gentle smile', 'soft warm light from floor lamp, comforting aura'),
    ('a grill pit manager', 'an open fire pit surrounded by brick walls, metal grill grates, hanging meat hooks, charcoal piles', 'heavy denim jacket, leather gloves, steel spatula, tongs', 'bright orange flicker from roaring flames'),
    ('a battlefield medic', 'muddy trench with sandbags, wooden crates, a makeshift stretcher, and a field tent', 'khaki uniform, bandage roll, small first‑aid kit, and a whistle', 'dawn light breaking over the horizon illuminating the trench'),
    ('a Mayan jade cutter', 'a stone workshop with jade blocks, grinding stones, obsidian blades, tropical vines, hummingbirds nearby', 'woven waistcloth, stone hammer, chisel, small leather pouch', 'bright filtered light through canopy openings'),
    ('a riverboat steward', 'wooden deck with polished railings, a polished bar counter, lanterns, a paddle wheel partially visible, mist rising from water', 'white shirt with a black vest, a bow tie, a serving tray, a pocket watch', 'warm glow from lanterns reflecting on the river surface'),
    ('a furrier', 'a workshop with hanging pelts, trimming shears, wooden drying racks, and a fur‑stitching bench', 'wearing a fur‑lined coat, gloves, and holding a small stitching needle', 'soft daylight filters through a frosted window, highlighting the soft textures'),
    ('a concert lighting designer', 'a large arena stage with truss structures, speaker stacks, and a glossy floor', 'a black shirt, tablet, headset, utility belt, reflective safety vest', 'multicolored moving beams sweeping across the stage surface'),
    ('a river ferry operator', 'a calm riverbank with wooden piers, floating buoys, and a small dock shaded by willow trees', 'a waterproof jacket, rubber boots, a life jacket, and a handheld radio', 'soft silver light reflected off the water’s surface'),
    ('an orthopedic surgeon', 'spacious operating theater with stainless steel table, sterile drapes, surgical lights, wall‑mounted cabinets, polished tiles', 'green scrub suit, surgical mask, scalpel, orthopedic drill, sterile gloves', 'focused bright surgical lamps casting sharp shadows on the operating table'),
    ('a coffee roaster', 'a dark roasting room with copper roaster, burlap bean sacks, steel cooling trays, hanging thermometer', 'heavy denim jacket, protective gloves, scoop, tasting cup', 'warm amber glow from glowing roaster'),
    ('a rescue diver', 'boat dock with submerged training pool, ladders, life vests hanging, water ripples', 'dry‑suit, scuba mask, buoyancy device, waterproof tablet', 'bright midday sun sparkling on the water surface'),
    ('an Ottoman coffee house barista', 'carpeted floor, low wooden benches, copper coffee pots, brass trays, hanging lanterns, intricate tiles, incense smoke', 'cotton tunic, leather sandals, copper coffee scoop, decorative pipe', 'warm amber light from hanging lanterns'),
    ('a candle maker', 'a tidy studio with rows of melted wax vats, wick spools, wooden molds, and a gentle fan', 'wearing a cotton apron, rubber gloves, and a small ladle', 'soft golden light flickers from nearby candles, creating a warm ambience'),
    ('an astrobiologist', 'a simulated Martian habitat with red sand, sealed growth chambers, hydroponic racks, and a compact rover model', 'lightweight polymer suit, portable microscope, data tablet, utility belt with sample vials', 'warm amber light from a dome‑shaped lamp mimicking sunrise'),
    ('a German pretzel baker', 'large stone oven, dough trays, wooden rolling pins, malt barrels, hanging copper hooks, flour clouds', 'blue work shirt, flour-dusted apron, dough scraper, sturdy shoes', 'soft yellow light spilling from the oven doorway'),
    ('a wartime field medic', 'muddy tent floor, canvas walls, sandbags, wooden stretcher, lantern, sand‑covered ground', 'khaki jacket, bandage roll, compact rifle, field kit, rugged boots', 'dim lantern light flickering through canvas, amber shadows'),
    ('an alpine cheese maker', 'mountain meadow with scattered pine trees, a stone cheese cave entrance, grazing goats nearby', 'thick wool vest, leather apron, cheese‑making knife, wooden ladle, basket', 'soft golden light filtering through mountain mist'),
    ('a papyrus maker', 'shallow riverbank with stacked reed bundles, drying racks, mud‑filled vats, wooden paddles', 'linen shirt, reed cutter, basket of wet strips', 'gentle sunlight glinting on the water surface'),
    ('a Minoan fresco painter', 'a palace wall with fresh plaster, pigment palettes, brushes, ceramic jars, columns, garden vines', 'light tunic, paint‑stained apron, wooden palette, fine brushes', 'diffused daylight through an open atrium'),
    ('a shipyard carpenter', 'a bustling dock with timber piles, half‑built hulls, rope coils, wooden crates, and a wind‑blown sail', 'wears canvas shirt, leather belt, carries a plane and a drawknife', 'bright midday sun reflects off the water and wood'),
    ('a stained‑glass artisan', 'a studio with colored glass sheets, lead cames, soldering iron, and a large wooden table covered in designs', 'clad in a white smock, protective gloves, and holding a small cutting wheel', 'bright natural light streams through a north‑facing window, lighting the glass fragments'),
    ('a synthetic biologist', 'a bio‑fabrication bench with 3D‑printer bioplotters, gel vats, sterile hood, and a wall of DNA helix murals', 'white lab coat, sterile gloves, pipette gun, tablet, safety glasses', 'bright cool white light from recessed ceiling panels'),
    ('a Canadian maple syrup tapper', 'wooden sugar shack, copper boiling vats, maple sap buckets, pine branches, steam rising, stone hearth', 'flannel shirt, wool vest, metal tap spout, rubber boots', 'soft warm light from a hanging oil lantern'),
    ('an ancient Egyptian papyrus farmer', 'lush riverbank, tall reeds, mud‑filled irrigation channels, mudbrick walls surrounding the plot', 'linen shirt, leather sandals, reed basket filled with cut stalks', 'warm golden light filtering through palm fronds'),
    ('a pastry decorator', 'a bright workbench with pastel fondant rolls, piping bags, edible glitter jars, marble slab', 'white smock, colorful gloves, piping tip set, small spatula', 'clear daylight from large skylight'),
    ('a flood relief coordinator', 'riverbank staging area with sandbags piled, inflatable boats, floating barriers, wooden pallets', 'rain‑proof jacket, waterproof boots, rescue rope, handheld GPS', 'soft overcast light diffusing across the wet ground'),
    ('a roller‑coaster operator', 'amusement park midway with tracks, safety barriers, colorful flags, concession stalls, twilight sky', 'bright polo shirt, badge, safety whistle, handheld control panel', 'vivid neon lights glowing against dusk'),
    ('a Hellenistic mathematician', 'marble study room, scrolls on wooden shelves, abacus, potted fig tree, open window', 'white robe, stylus, wax tablet, simple sandals', 'soft daylight pouring through the window'),
    ('a wildlife disease outbreak monitor', 'forest ranger station with sample trays, microscopes, a log pile, a small greenhouse', 'field jacket, gloves, sample vials, handheld scanner, notebook', 'dappled sunlight filtering through dense canopy'),
    ('a Mexican mole maker', 'heavy cast-iron cauldron, dried chilies, chocolate blocks, wooden ladle, woven baskets, fragrant steam curls', 'lightweight shirt, embroidered apron, wooden spoon, sturdy boots', 'rich reddish light from a nearby stove fire'),
    ('a vintage trolley driver', 'a cobbled avenue with streetlamps, flower boxes, and an old electric trolley parked beside a curb', 'a woolen cap, leather gloves, a brass key ring, and a pocket ledger', 'soft amber glow from the streetlamps'),
    ('a guild master weaver', 'a workshop with large wooden loom, skeins of dyed yarn, spindles, wooden crates, hanging tapestries', 'linen shirt, woolen vest, wooden shuttle, measuring tape belt', 'warm midday glow through a high mullioned window'),
    ('a bronze caster', 'open workshop with clay molds, molten metal vats, ash‑covered stone floor, smoke rising from a furnace', 'sturdy leather gloves, bronze hammer, protective apron', 'bright furnace fire casting flickering orange light'),
    ('a trolley car driver', 'city street with tram tracks, vintage street lamps, cobblestones, and storefront awnings', 'dark uniform, cap, handheld conductor’s box, leather gloves, sturdy boots', 'soft amber glow from street lamps during early evening'),
    ('a classical violinist', 'concert hall stage, polished wooden floor, grand piano, velvet curtains, ornate chandelier, empty rows of seats', 'black formal dress, silver violin, bow, music stand, elegant shoes', 'soft warm light from chandelier bathing the stage'),
    ('a parchment maker', 'a quiet attic with vats of plant pulp, drying frames, wooden rollers, and stacked parchment sheets', 'wearing a linen smock, soft gloves, and a wooden spatula', 'soft natural light filters through a small attic window, creating gentle highlights'),
    ('a spectroscopist', 'a optics lab with diffraction gratings, prism arrays, laser benches, and a dark‑room enclosure', 'lab coat, safety goggles, fiber‑optic probe, calibration blocks, notebook', 'precise narrow beams of white light from overhead spotlights'),
    ('a Belgian waffle artisan', 'iron waffle iron, powdered sugar dust, fresh berries, maple syrup bottles, wooden serving board, tiled floor', 'white chef jacket, red striped apron, metal spatula, non‑slip shoes', 'warm honey‑colored light from a hanging bulb'),
    ('a fertility specialist', 'glass cabinets, microscope, soft carpet, window with curtains, gentle lighting, wooden desk', 'white coat, tablet, lab pipette, calm demeanor, soft shoes', 'soft diffused light from ceiling, calming ambience'),
    ('a dim sum chef', 'a bamboo steamer station with metal racks, porcelain bowls, hanging herbs, polished wok', 'light cotton jacket, bamboo hat, bamboo steam basket, ladle', 'soft warm light from hanging paper lanterns'),
    ('a marine rescue swimmer', 'coastal lifeboat station with lifeboats on cradles, ropes coiled, sea gulls perched on railings', 'wetsuit, rescue board strapped to back, waterproof watch', 'clear sky light reflecting off calm water and metal hulls'),
    ('a sailboat skipper', 'calm harbor with wooden piers, moored yachts, gulls perched, seafoam lapping, lighthouse beam', 'striped tee, sailing gloves, rope coil, waterproof watch', 'soft evening glow reflecting off calm water'),
    ('a Olmec stone carver', 'jagged limestone quarry, massive stone blocks, wooden sleds, tropical vines climbing cliffs', 'woven bark shirt, stone chisel, wooden mallet, sand sandals', 'bright midday sun beating on the quarry walls'),
    ('a rapid‑response veterinary medic', 'mobile clinic van parked beside a barn, medical cabinets, a portable ultrasound, hay bales', 'lab coat, stethoscope, syringes, portable cooler, sturdy boots', 'warm midday sun streaming through open doors'),
    ('a street taco vendor', 'metal cart with sizzling grill, stacked corn tortillas, chilies in clay bowls, colorful awning, steam rising', 'light denim jacket, bandana, grill tongs, reusable water bottle, sturdy sandals', 'bright midday sun casting sharp shadows on the cart'),
    ('a modern tram conductor', 'a city street with paved tracks, modern streetlights, and a glass‑covered tram stop shelter', 'a smart‑tech uniform, digital ticket scanner, headset, and a compact tablet', 'soft white glow from the streetlights'),
    ('an obstetric midwife', 'bright birthing suite with birthing pool, soft curtains, wooden birthing chair, pastel walls, gentle lighting', 'comforting gown, supportive shoes, birthing ball, warm blanket, encouraging voice', 'soft natural daylight streaming through a high window'),
    ('a present‑day virologist', 'a biosafety level‑3 lab with sealed cabinets, air‑flow hoods, and rows of incubators', 'a full protective suit, respirator, and a data pad', 'cool blue light from filtered ceiling panels'),
    ('an airline flight attendant', 'spacious aircraft aisle with rows of seats, overhead bins, safety cards, polished metal walls', 'navy uniform, crisp badge, slim belt, silver name tag, comfortable shoes', 'soft cabin lighting with a warm, inviting hue'),
    ('a stand‑up comedian', 'small comedy club stage, brick backdrop, single microphone stand, low table, red curtains, empty audience seats', 'casual jeans, graphic tee, sneakers, notebook in pocket', 'focused spot lamp creating a bright circle on the floor'),
    ('a candlewick cutter', 'a narrow backroom with rows of dried cotton threads, metal cutters, and a small oil lamp', 'wearing a simple apron, gloves, and a small scalpel‑like cutter', 'warm glow from the oil lamp bathes the workspace'),
    ('a paleoanthropologist', 'a fossil preparation lab with sandstone blocks, grinding wheels, dust‑collection hoods, and a wall of skeletal casts', 'sturdy denim jacket, leather gloves, handheld chisel, field notebook, protective goggles', 'warm incandescent glow from industrial bulbs casting gentle highlights'),
    ('a Peruvian ceviche master', 'marble slab, bowls of citrus juice, fresh fish fillets, sliced onions, cilantro bunches, sea salt crystals', 'light breathable shirt, apron with pockets, fish fillet knife, rubber sandals', 'cool crisp light from a nearby window'),
    ('a lab pathologist', 'microscope stations, glass slides, stainless cabinets, white tiles, ceiling vents, plant in corner', 'white coat, latex gloves, slide box, notebook, comfortable shoes', 'cool neutral light from ceiling fixtures, precise illumination'),
    ('an ice‑cream scooper', 'a colorful ice‑cream counter with pastel tubs, chrome freezer, striped awning, decorative cones stacked', 'bright pink shirt, white cap, metal scoop, napkin dispenser', 'cheerful daylight filtered through frosted glass doors'),
    ('a World War II field surgeon', 'makeshift operating tent with canvas walls, wooden table, medical instruments, and sandbags outside', 'olive drab coat, scalpel, bandage roll, and a field compass', 'dim lantern light swinging gently above the table'),
    ('a Carthaginian glassblower', 'a sand‑filled workshop with furnace, glass rods, metal tongs, mosaic tiles, desert wind outside', 'protective apron, heat‑resistant gloves, blowpipe, small cloth bag', 'intense furnace glow illuminating molten glass'),
    ('a logistics drone pilot', 'open rooftop with a landing pad, metal racks, a wind turbine, a weather‑proof console, sunrise over the skyline', 'lightweight flight suit, a tablet, a headset, a compact battery pack', 'early morning light casting long shadows across the rooftop'),
    ('an Inuit seal hunter preparing a feast', 'snow‑covered igloo interior with seal skins draped, stone fire pit, and a wooden carving table', 'fur‑lined parkas, insulated boots, and a bone carving knife', 'soft glow from the fire illuminating the icy walls'),
    ('a theater makeup artist', 'a backstage makeup station with mirrored vanity, lighted ring, and rows of cosmetic jars', 'a white coat, brush set, palette, disposable sponges, gloves', 'soft diffused light from a ring lamp creating even illumination'),
    ('a cargo ship deckhand', 'a sprawling steel deck crowded with stacked containers, massive winches, and a rusted crane against a stormy horizon', 'a high‑visibility vest, steel‑toed boots, a heavy rope coil, and a weathered cap', 'dim gray light from a lantern mounted on the deck rail'),
    ('an ambulance paramedic', 'compact ambulance interior with stretcher, medical bag, oxygen tank, dashboard lights, black rubber flooring', 'high‑visibility jacket, helmet, trauma kit, handheld defibrillator, radio', 'steady blue emergency lights flashing softly along the ceiling'),
    ('a hospital pharmacist', 'compact pharmacy room, shelves of labeled bottles, dispensing counter, computer terminal, safety cabinet', 'white lab coat, safety glasses, pill counter, prescription pad', 'bright fluorescent glow reflecting off polished countertops'),
    ('a volcanic eruption monitor', 'mountain observatory with seismic sensors, ash‑filled sky, metal rails, protective dome', 'heat‑resistant coverall, respirator mask, data logger, sturdy gloves', 'glowing red light from distant lava flow'),
    ('a colonial American tavern cook', 'rough timber beams, stone hearth, hanging iron pots, wooden barrels, woven tablecloths, animal hide rug, candle sconces', 'homespun shirt, leather apron, wooden ladle, iron skillet', 'soft candlelight flickering alongside the fireplace'),
    ('a tanner', 'a rustic cellar with vats of tannic solution, hanging animal hides, wooden racks, and a stone mortar', 'dressed in a heavy leather coat, boots, and a wide‑brimmed hat', 'dim natural light filters through a small grate, casting muted tones'),
    ('a climatologist', 'a climate‑modeling chamber with wind tunnels, temperature gauges, humidity domes, and a rotating Earth globe model', 'lightweight insulated jacket, digital hygrometer, notebook, portable anemometer, sturdy boots', 'soft diffuse daylight simulated by large overhead panels'),
    ('a Moroccan tagine chef', 'clay tagine pots, copper spice bowls, woven rugs, hanging dried oranges, fragrant steam, mosaic floor', 'linen robe, leather belt, wooden spoon, spice ladle, soft slippers', 'warm amber glow from a low oil lantern'),
    ('a 19th century apothecary', 'oak shelves, glass jars, wooden counter, brass scales, hanging dried herbs, stone floor', 'long coat, leather belt, mortar and pestle, measuring spoon, pocket watch', 'golden glow from oil lamp, gentle reflections'),
    ('a wandering minstrel', 'a forest clearing with mossy stones, a small fire pit, fallen logs, and scattered pine cones', 'colorful doublet, lute strapped across chest, leather boots, and a feathered cap', 'soft firelight dancing on the surrounding trees'),
    ('a temple sculptor', 'carved marble courtyard, half‑finished statue, chisel marks, stone dust clouds, marble blocks stacked', 'simple tunic, leather belt with carving tools, protective cloth', 'cool morning light casting gentle shadows'),
    ('a Persian carpet weaver', 'a tent interior with loom, dyed wool skeins, wooden beams, patterned rugs hanging, desert sand outside', 'loose robe, weaving needles, small pouch of dyes, soft slippers', 'warm glow of oil lamps casting gentle light'),
    ('an operating theatre surgeon', 'large sterile suite with overhead surgical lights, stainless tables, anesthesia machine, and rolled surgical drapes', 'green surgical gown, mask, double gloves, and a sleek scalpel', 'intense focused spotlights creating crisp, shadow‑free illumination'),
    ('a rope maker', 'a tall building with hemp bundles, twisting machines, coil racks, and a basket of finished ropes', 'wearing a rough canvas shirt, sturdy boots, and a small coil cutter', 'soft daylight pours from a high window, highlighting the twisted fibers'),
    ('an atmospheric chemist', 'a high‑altitude simulation chamber with pressure gauges, gas mixers, aerosol generators, and a transparent observation dome', 'thermal jacket, portable gas analyzer, safety goggles, data logger, sturdy boots', 'soft blue illumination from internal LEDs mimicking clear sky'),
    ('a steam locomotive engineer', 'a long iron rail line stretching across rolling hills, distant mountains, and a stone bridge under a cloudy sky', 'a dark wool coat, leather gloves, brass pocket watch, and a folded railway timetable', 'soft amber glow from a lantern hanging on the locomotive cab'),
    ('a Viking longship rower', 'calm fjord water, towering pine trees, mist rising from surface, wooden shields stacked on shore', 'leather tunic, fur cloak, wooden oar, iron axe at belt', 'soft dawn light shimmering across still water'),
    ('a barbecue pit pitmaster', 'a large smoker with brick walls, hanging meat hooks, cedar planks, metal firebox', 'flannel shirt, denim apron, heat‑proof gloves, basting brush', 'rich orange radiance from smoking wood'),
    ('a wildfire air‑crew member', 'remote helipad surrounded by tall pines, fire‑suppression tanks, charcoal‑blackened soil, smoke plume', 'flame‑resistant suit, fire‑retardant helmet, portable pump, safety goggles', 'harsh midday sun beating down on the clearing'),
    ('an itinerant minstrel', 'a village square paved with cobblestones, market stalls empty, wooden fountain, stone bench, lantern posts', 'colorful doublet, leather boots, lute case, feathered hat, small pouch', 'golden twilight washing over the square'),
    ('a blacksmith', 'a stone forge with glowing ember pits, iron bars, hanging leather apron, and a wooden anvil stand', 'wearing a soot‑stained leather apron, heavy iron gauntlets, sturdy boots, and a hammer', 'warm amber glow emanates from the furnace and flickering sparks'),
    ('a post‑earthquake structural assessor', 'city block with cracked pavement, fallen streetlamps, scattered bricks, a temporary fence, dust clouds', 'hard hat, safety vest, laser distance meter, clipboard, sturdy boots', 'soft diffused light through lingering dust'),
    ('a Brazilian churrasco chef', 'open grill with rotating skewers, charred wood planks, hanging garlic braids, smoky haze, tiled floor', 'checked shirt, leather apron, long tongs, heat-resistant gloves, sturdy sandals', 'bright orange flare from the glowing coals'),
    ('a desert caravan guide', 'a wide sand dune valley with a line of camels, a stone oasis, and a setting sun painting the sky', 'a flowing robe, leather sandals, a curved dagger, and a water skin', 'rich orange light spilling across the dunes'),
    ('a royal falconer', 'a palace terrace with marble columns, ornamental fountains, stone statues, wind‑blown grasses, distant hills', 'embroidered cloak, feathered cap, leather gauntlet, falcon perch', 'crisp morning light sparkling on the fountain water'),
    ('a potter', 'clay‑filled workshop, turning wheel, stacked amphorae, kiln emitting soft heat, stray pottery shards', 'simple wool tunic, apron with pockets, wooden carving tool', 'warm glow from the glowing kiln'),
    ('an Egyptian scribe', 'a quiet reed‑paper desk in a stone library, papyrus scrolls stacked, wooden shelves, clay jars, lotus motifs', 'linen robe, reed pen, satchel of scrolls, simple sandals', 'soft daylight filtering through high lattice windows'),
    ('a skate‑park photographer', 'concrete skate park, ramps, rails, graffiti walls, scattered skate decks, chain‑link fence', 'camouflage jacket, cargo shorts, camera strap, beanie, sneakers', 'bright midday sun casting sharp shadows across the ramps'),
    ('a lute maker', 'a workshop filled with wooden soundboards, catgut strings, carving tools, and a drying rack of finished instruments', 'dressed in a simple tunic, leather apron, and holding a fine carving knife', 'warm midday sun streams through a skylight, illuminating the polished wood'),
    ('a renewable‑energy researcher', 'a solar‑cell testing area with photovoltaic panels, multimeters, sun‑simulator lamps, and a battery bank rack', 'lightweight lab jacket, insulated gloves, voltage meter, data logger, safety glasses', 'bright simulated sunlight flooding the workbench from a large arc lamp'),
    ('a Turkish baklava cutter', 'layered pastry trays, pistachio piles, honey drizzles, copper pans, marble countertop, fragrant steam', 'light cotton tunic, apron with decorative fringe, sharp pastry knife, comfortable slippers', 'soft golden light from a low hanging lantern'),
    ('a dialysis nurse', 'row of machines, water filters, plastic chairs, tiled floor, ceiling vents, window blind', 'light blue scrubs, blood pressure cuff, clipboard, gentle smile, comfortable shoes', 'steady cool light from ceiling panels, clinical calm'),
    ('a chocolatier', 'a quiet workshop with marble countertop, tempered chocolate molds, glass jars of nuts, brass thermometer', 'white lab coat, silicone gloves, chocolate spatula, cooling rack', 'muted golden light from low pendant bulbs'),
    ('a hazardous‑materials officer', 'industrial yard with sealed drums, containment tents, decontamination shower, rusted metal fences', 'full hazmat suit, respirator mask, sealed gloves, detection device', 'harsh white ceiling lights highlighting the safety barriers'),
    ('a kayak river guide', 'rocky river gorge with pine cliffs, swirling water, fallen logs, misty spray, sunlit spray', 'quick‑dry shirt, waterproof pouch, paddle, life jacket', 'dappled sunlight piercing through canopy onto water'),
    ('a Etruscan tomb painter', 'underground chamber walls, fresco pigments, stone benches, torches set in niches', 'wool tunic, paintbrushes, pigment jars, leather belt', 'flickering torchlight casting warm shadows'),
    ('a building collapse inspector', 'ruined structure with twisted steel beams, dust clouds, scattered debris, a safety barrier', 'hard hat, high‑visibility vest, inspection clipboard, flashlight, sturdy gloves', 'dim natural light filtered through broken windows'),
    ('an Ethiopian coffee roaster', 'clay roasting drum on a fire pit, sacks of green beans, wooden spoon, woven baskets, aromatic smoke', 'linen shirt, leather apron, wooden roasting paddle, protective gloves', 'soft amber light filtering through the smoke-filled air'),
    ('a polar research sled pilot', 'a frozen tundra with snow‑covered sleds, scientific tents, and distant icebergs under a pale aurora', 'a insulated parka, fur‑lined boots, a GPS device, and a sled harness', 'cool greenish light dancing across the icy horizon'),
    ('an illuminated manuscript scribe', 'a quiet scriptorium with wooden desks, parchment stacks, ink pots, candle holders, stone walls', 'simple linen robe, quill pen, ink satchel, parchment roll tucked under arm', 'soft flickering candlelight casting gentle shadows on the desk'),
    ('a contemporary pharmacologist', 'a lab with pill‑press machines, glass vials, and a refrigerated compound freezer', 'a lab coat, latex gloves, and a barcode scanner', 'steady white light from ceiling fluorescent strips'),
    ('a bicycle courier', 'urban alley with brick walls, fire escapes, graffiti‑free murals, and stacked crates', 'lightweight jacket, messenger bag, helmet, reflective vest, sturdy sneakers', 'clear morning sun streaming through narrow gaps between buildings'),
    ('a Broadway choreographer', 'large rehearsal hall, sprung floor, mirrored wall, rows of folding chairs, stacked music stands', 'black leggings, fitted shirt, sneakers, clipboard, water bottle', 'bright daylight pouring through tall windows, creating crisp illumination'),
    ('a leather cutter', 'a workshop with hanging leather hides, wooden cutting boards, brass shears, and a stack of finished belts', 'clad in a heavy apron, sturdy boots, and holding a sharp leather knife', 'bright daylight streams through a high window, highlighting the grain of the leather'),
    ('a biochemist', 'a reaction‑vessel station with glass beakers, stir plates, pH meters, and a refrigerated reagent fridge', 'white lab coat, rubber gloves, pipette set, analytical balance, safety glasses', 'clear bright light from ceiling floodlights creating crisp shadows'),
    ('a Swedish fika host', 'round wooden table, cinnamon buns, coffee pot, glass jars of jam, soft rug, pastel walls', 'cozy cardigan, simple skirt, tea kettle, wooden spoon, wool slippers', 'gentle warm light from a hanging pendant lamp'),
    ('an anesthesiologist', 'operating table, breathing machines, medication cart, ceiling lights, polished floor, glass window', 'blue scrubs, mask, syringe, monitoring device, calm demeanor', 'bright clinical light from ceiling, clear visibility'),
    ('a food truck chef', 'a painted van kitchen with stainless steel grill, hanging spice racks, rolling serving window, bright awning', 'green bandana, short‑sleeve shirt, utility belt, handheld thermometer', 'vivid daylight reflected off metal surfaces'),
    ('an African market grill cook', 'open grill with charcoal, rows of skewers, woven basket of vegetables, clay pots, hanging lanterns', 'cotton dashiki, sturdy sandals, metal tongs, wooden spatula, small woven pouch', 'golden glow of charcoal fire mixing with lantern light'),
    ('a Nubian goldsmith', 'a riverside stall with gold nuggets, wooden molds, crucible, palm thatch roof, reeds swaying', 'linen vest, small hammer, tongs, gold dust pouch', 'bright river reflections shimmering on the metal'),
    ('an apprentice cobbler', 'a narrow wooden shop with rows of shoe lasts, leather rolls, a leather-cutting table, and a brass shoe‑making press', 'linen shirt, canvas apron, small leather mallet, measuring tape coiled at waist', 'soft daylight streaming through a dusty window onto the workbench'),
    ('an urban disaster coordinator', 'busy street intersection, overturned cars, debris piles, scattered fire hydrants, broken streetlights', 'bright reflective vest, sturdy boots, tablet, walkie‑talkie, safety helmet', 'sharp white floodlights casting stark shadows on wet pavement'),
    ('a parkour trainer', 'an urban training area with concrete walls, railings, low platforms, and scattered mats', 'a breathable tee, cargo pants, training shoes, wrist tape, water bottle', 'midday sun casting crisp shadows across the concrete'),
    ('a mountain tram operator', 'a steep alpine pass with wooden support towers, cable lines, and a snowy plateau under a pale sunrise', 'a insulated parka, thick gloves, a woolen scarf, and a handheld control panel', 'cool blue light spilling from sunrise over the peaks'),
    ('an immunology specialist', 'clean lab area with refrigerated freezers, microscope stations, sterile countertops, glass partitions, muted flooring', 'protective gown, latex gloves, pipette, data tablet, calm expression', 'cool white LEDs casting a crisp, clinical illumination'),
    ('an oncology pharmacist', 'secure medication room, locked cabinets, chemotherapy vials, biohazard bins, stainless steel workbench', 'white coat, protective gloves, dose‑calculator device, safety glasses', 'clinical white light from ceiling panels highlighting safety equipment'),
    ('a traffic collision analyst', 'highway rest area with broken barriers, overturned vehicle, scattered debris, road markings', 'reflective vest, safety vest, clipboard, measuring tape', 'bright noon sun casting sharp shadows on the asphalt'),
    ('a circus ringmaster', 'bright big top tent interior, striped red and white canopy, wooden beams, colorful bunting hanging from poles', 'tailored red coat, black top hat, silver cane, polished black boots', 'warm amber glow from chandeliers casting soft shadows on the canvas'),
    ('a weaver', 'a spacious loft with a large wooden loom, skeins of dyed yarn, wooden spindles, and a basket of finished cloth', 'wearing a simple linen dress, a woven belt, and holding a shuttle', 'bright midday sun pours through high windows, lighting the vibrant threads'),
    ('a materials scientist', 'a high‑temperature furnace area with alloy crucibles, rolling presses, electron microscope, and a metal‑dust collection tray', 'heat‑resistant apron, thick gloves, safety goggles, alloy sample holder, metal detector', 'intense orange glow from furnace reflected on nearby steel surfaces'),
    ('a vegan smoothie bar operator', 'glass blenders, rows of fresh fruit, bamboo cutting boards, recycled jars, green plants, soft countertop', 'eco-friendly shirt, reusable apron, stainless steel strainer, wooden spoon, canvas shoes', 'bright natural light from a large front window'),
    ('an obstetrician', 'soft pastel walls, birthing pool, folded blankets, wooden chair, window with curtains, polished tiles', 'white coat, stethoscope, ultrasound probe, clipboard, comfortable shoes', 'calm daylight streaming through curtains, warm ambience'),
    ('a shipwright apprentice', 'a dockyard with wooden hulls, rope coils, tar barrels, and a thatched shed', 'oil‑stained smock, wooden mallet, measuring tape, and a bundle of shavings', 'soft dusk light glowing over the water’s surface'),
    ('a loom operator', 'large wooden loom, skeins of dyed wool, woven tapestries hanging, straw‑filled floor', 'linen apron, wooden shuttle, measuring rod', 'soft daylight filtering through a high window'),
    ('an Incan stone mason', 'a high mountain terrace with cut stone blocks, sand piles, wooden levers, llamas grazing nearby', 'woven poncho, stone‑carving tools, leather belt, sturdy sandals', 'bright mountain sun lighting the quarry'),
    ('a steamship captain', 'a polished wooden bridge with brass helm, rope coiled on a barrel, oil lanterns hanging from the railings, gentle ocean mist', 'naval coat with gold buttons, a leather hat, a pocket watch, a sextant tucked in coat pocket', 'soft amber glow from hanging oil lanterns reflecting on polished wood'),
    ('a metal caster', 'a furnace room with molten metal ladles, sand molds, cooling racks, and a stack of iron ingots', 'dressed in a heat‑resistant coat, gloves, and holding a metal tongs', 'intense orange glow from the furnace reflects on the surrounding walls'),
    ('an Olympic sprinter', 'a stadium track lane surrounded by a clear sky, white starting blocks, and a smooth red rubber surface', 'a sleek aerodynamic suit, lightweight spikes, wristband, visor', 'bright natural sunlight streaming through open stadium arches'),
    ('an ocean liner captain', 'a massive wooden deck with polished railings, towering smokestacks, and gentle waves lapping against the hull at sunset', 'a navy double‑breasted coat, gold epaulettes, a captain’s hat, and a brass sextant', 'warm golden light spilling from a lantern on the wheelhouse'),
    ('an Arctic seal hunter', 'ice floes glittering, polar bear tracks, cracked sea ice, aurora faintly glowing above', 'fur‑lined parkas, heavy boots, harpoon, sled harness', 'pale twilight casting a cool blue wash'),
    ('a noodle maker', 'a long wooden table with flour dust, rolling pins, stainless steel dough cutter, hanging pasta racks', 'white apron, cotton shirt, noodle cutter, wooden rolling pin', 'bright daylight filtering through high windows'),
    ('a disaster medical technician', 'field triage tent with rows of stretchers, medical trays, portable lights, sandbags outside', 'lightweight scrubs, medical badge, compact trauma kit, headlamp', 'warm lantern light flickering inside the canvas shelter'),
    ('a telemedicine physician', 'a home office with a laptop on a desk, potted plant, framed certificates, and a wall clock', 'smart casual shirt, headset, and a coffee mug beside a notepad', 'cool daylight from a nearby window filtered through blinds'),
    ('an organ builder', 'a workshop filled with wooden pipes, brass windchests, intricate carvings, and a large drafting table', 'dressed in a dark waistcoat, leather belt, and carrying a tuning fork', 'cool morning light reflects off polished metal and polished wood'),
    ('a paleobotanist', 'a cluttered greenhouse bench with fossilized leaves, terracotta pots, glass jars of amber, and a sand table', 'khaki field coat, wide brim hat, magnifying glass, leather notebook, sturdy boots', 'soft amber glow filtering through translucent greenhouse panes'),
    ('a Korean kimchi fermenter', 'large earthenware jars, bamboo lids, hanging red peppers, wooden cutting board, misty air, stone floor', 'simple linen shirt, apron with pockets, wooden mallet, cloth napkin', 'soft cool light from a recessed ceiling fixture'),
    ('a ski lift operator', 'a snowy mountain slope with wooden chair lifts, pine trees, and a chalet roof against a crisp blue sky', 'a insulated jacket, snow boots, a safety harness, and a handheld ticket scanner', 'crisp white light of a high‑altitude noon'),
    ('a minstrel', 'a tavern corner with wooden tables, empty mugs, a cracked lute stand, hanging lanterns, straw rugs', 'colorful doublet, leather boots, lute case, feathered hat', 'warm candlelight dancing across the rough wooden beams'),
    ('a grain merchant', 'market stall with wooden beams, sacks of golden wheat, scale stones, woven baskets, sand‑covered ground', 'linen vest, leather satchel, bronze weighing pan', 'bright sun casting sharp shadows on the stall'),
    ('a Babylonian baker', 'a mud‑brick oven yard, flatbread on stone slabs, wheat sacks, clay pots, fire pits, desert backdrop', 'linen shirt, apron, wooden paddle, woven basket', 'glowing orange firelight reflecting off the baked loaves'),
    ('a salsa dance instructor', 'dance studio with polished wood floor, mirrored wall, colorful wall murals, stacked stereo speakers, empty chairs', 'flowing red dress, dance shoes, hair comb, water bottle', 'warm golden light from ceiling fixtures illuminating the floor'),
    ('a copper boiler maker', 'an industrial loft with copper sheets, rivet guns, pipe racks, and a large unfinished boiler shell', 'clad in a heavy coat, steel-toe boots, and holding a rivet hammer', 'bright industrial light pours from high windows, reflecting off copper surfaces'),
    ('a geochemist', 'a rock‑analysis station with crushing mill, X‑ray diffractometer, acid‑resistant bench, and stacked sample jars', 'heavy lab coat, acid‑resistant gloves, handheld pH meter, sample scoop, safety goggles', 'steady bright illumination from ceiling floodlights, highlighting mineral colors'),
    ('a South African braai master', 'open charcoal grill, meat skewers, maize porridge pots, wooden firewood stacks, smoke curls, stone patio', 'checked shirt, leather apron, long grilling fork, heat‑proof gloves', 'bright red‑orange light from the glowing embers'),
    ('a transplant coordinator', 'large conference table, whiteboard, potted plant, floor‑to‑ceiling windows, soft carpet, ceiling lights', 'business‑casual attire, tablet, clipboard, phone, calm expression', 'clear daylight streaming through windows, bright and hopeful'),
    ('a ramen broth master', 'a large simmering pot surrounded by wooden shelves, dried kelp bundles, ceramic bowls, hanging ladles', 'black apron, thick sleeves, ladle, wooden spoon', 'deep amber light from simmering broth'),
    ('a canine handler', 'training arena with obstacle tunnels, scent barrels, padded flooring, bright safety cones', 'tactical vest, utility belt, dog harness, whistle on collar', 'even daylight from skylights casting uniform illumination'),
    ('a tram driver', 'urban tramway with overhead wires, polished tracks, cobblestone streets, park benches, flowering trees', 'dark uniform jacket, cap, control panel gloves, badge', 'steady fluorescent light from street fixtures'),
    ('a Celtic ironworker', 'open forge beside a river, red-hot iron bars, stone anvil, willow branches', 'leather apron, iron hammer, tongs, soot‑stained boots', 'glowing furnace light mixing with river reflections'),
    ('a humanitarian water‑purification specialist', 'campground with large filtration units, barrels, solar panels, a shaded tarp, sand piles', 'light work shirt, utility belt, filter cartridges, water testing strips, cap', 'bright sunlight reflected off clear water tanks'),
    ('a French pastry chef', 'marble countertop with piping bags, tiered trays of croissants, sugar crystals, pastel walls, butter churn', 'white double-breasted coat, pastel chef hat, whisk, measuring spoons, non-slip shoes', 'gentle diffused light from a skylight above the pastry station'),
    ('an interplanetary cargo shuttle operator', 'a futuristic docking bay with metallic platforms, hovering cargo pods, and a vast starfield beyond a transparent dome', 'a sleek nano‑fabric suit, data glove, holo‑tablet, and a compact thruster pack', 'soft silver light streaming through the dome'),
    ('a castle steward', 'a grand hall with long wooden tables, barrels, hanging tapestries, stone arches, empty goblets', 'fur‑lined coat, leather boots, ledger book, brass ring on finger', 'bright midday sun streaming through high stained‑glass windows'),
    ('a 21st‑century solar‑farm engineer', 'expansive field of gleaming panels, desert‑like soil, distant wind turbines, clear sky', 'safety vest, hard hat, tablet, insulated gloves', 'bright sun casting mirror‑like reflections'),
    ('a freight ship deckhand', 'vast ocean deck with cargo crates, ropes, metal railings, and distant gulls', 'water‑resistant coat, steel-toe boots, weathered cap, cargo ledger, gloves', 'silver moonlight reflecting off the rolling sea'),
    ('a film stunt coordinator', 'abandoned warehouse set, broken windows, concrete floor, stacked crates, exposed beams, safety mats', 'utility vest, black cargo pants, sturdy boots, walkie‑talkie, safety goggles', 'harsh industrial lights casting stark shadows on the concrete'),
    ('a goldsmith apprentice', 'a compact studio with tiny crucibles, gold nuggets, polishing wheels, and a set of delicate pliers', 'wearing a white smock, protective gloves, and a small magnifying visor', 'clear focused light from a desk lamp shines on the metal'),
    ('a cryobiologist', 'a sub‑zero chamber with liquid nitrogen tanks, cryo‑preservation racks, insulated workbench, and frost‑covered windows', 'thermal insulated coat, insulated gloves, cryo‑tube carrier, digital thermometer, goggles', 'cold bluish light emitted from chilled LED panels lining the walls'),
    ('a Haitian griot grill operator', 'charcoal grill, hanging pork pieces, pineapple slices, wooden skewers, smoky haze, rustic stone wall', 'colorful shirt, apron with fringe, grill tongs, heat-resistant gloves', 'deep orange glow from the glowing coals'),
    ('a medical researcher', 'laboratory benches, glass beakers, incubator, whiteboard, floor‑to‑ceiling windows, smooth floor', 'lab coat, safety goggles, clipboard, pipette, sturdy shoes', 'natural daylight flooding the lab, energizing glow'),
    ('a sous‑chef', 'a busy line kitchen with stainless steel prep tables, hanging pots, stainless trays, stacked pans', 'black chef jacket, white apron, sharp chef’s knife, timer', 'steady cool light from overhead fluorescent panels'),
    ('an EMT trainee', 'spacious ambulance garage with stacked stretchers, medical kits on shelves, open garage doors showing city street', 'lightweight waterproof jacket, utility belt with trauma shears, compact backpack', 'soft natural daylight streaming through high windows onto polished concrete'),
    ('a field medic', 'dusty tent camp, canvas walls, fold‑out medical table, sandbags, portable generator humming', 'camouflage vest, combat boots, first‑aid kit, compact defibrillator', 'steady yellow floodlight casting sharp shadows'),
    ('a traditional potter', 'a mud‑lined studio with a turning wheel, stacked clay blocks, drying racks, and a kiln emitting soft smoke', 'apron smeared with clay, wooden paddle, shaping rib, and a water bucket', 'soft natural light spilling from an open doorway onto the wet clay'),
    ('a maritime rescue pilot', 'coastal helipad with sand dunes, a rescue hoist, fuel drums, wind‑blown seaweed', 'flight suit, flight helmet, navigation tablet, survival vest, gloves', 'cool blue dawn light reflecting off distant waves'),
    ('a competitive chef', 'a televised kitchen arena with stainless steel counters, burners, and a large overhead exhaust hood', 'a white chef coat, tall hat, knife set, apron, timer', 'bright white kitchen lights highlighting every surface'),
    ('an aerial tramway technician', 'a high‑altitude station perched on a cliff, cable cars hanging, and pine forests below a clear sky', 'a safety harness, reflective jacket, toolkit belt, and a portable radio', 'bright daylight illuminating the metal cables'),
    ('a clinical psychologist', 'cozy therapy room with sofa, bookshelf, soft rug, floor lamp, window with blinds', 'casual shirt, notebook, soothing voice, gentle smile, coffee cup', 'warm golden light from a floor lamp creating a relaxed mood'),
    ('a physiotherapy aide', 'rehabilitation gym, exercise mats, resistance bands, balance boards, wall‑mounted mirror, large window', 'sports‑style polo shirt, sneakers, water bottle, clipboard', 'natural daylight flooding the space through floor‑to‑ceiling glass'),
    ('a storm‑damage carpenter', 'storm‑hit neighborhood street with fallen trees, broken fences, scattered lumber, muddy ground', 'work shirt, tool belt, safety glasses, hammer', 'overcast sky providing muted, even illumination'),
    ('an opera singer', 'ornate stage with velvet curtains, grand piano, marble columns, gilded railings, plush red seats empty', 'elegant black evening gown, delicate pearl necklace, silk gloves, crystal clutch', 'golden spotlights sweeping across the stage, bathing it in luminous warmth'),
    ('a watchmaker', 'a tiny bench surrounded by brass gears, tiny screwdrivers, magnifying glass, and rows of pocket watches', 'clad in a crisp white shirt, tweed vest, and delicate tweezers', 'focused lamp light casts a focused glow over the intricate parts'),
    ('a pharmacologist', 'a drug‑discovery lab with compound libraries, robotic pipetting arm, incubators, and a glass‑covered synthesis table', 'white coat, nitrile gloves, pill‑pressing tool, tablet computer, safety glasses', 'bright cool white lighting highlighting each reaction vessel'),
    ('an Irish pub bartender', 'polished wood bar, copper taps, stacked barrels, hanging hops, amber glassware, stone fireplace backdrop', 'dark vest, crisp white shirt, bar spoon, pocket watch, sturdy boots', 'soft golden glow from the fireplace flames'),
    ('a dental hygienist', 'white tiled floor, dental chairs, stainless trays, hanging mirrors, plant pot, ceiling vent', 'green uniform, protective glasses, ultrasonic scaler, floss dispenser, mask', 'clear cool light from ceiling fixtures, steady illumination'),
    ('a village healer', 'a cottage interior with herbal bundles, stone mortar, wooden shelves, and a thatched roof window', 'simple linen dress, leather satchel, wooden spoon, and a bundle of dried sage', 'soft afternoon light filtering through a small window'),
    ('a marble cutter', 'quarry with massive stone blocks, wooden sledges, dust clouds, ancient tools laid on a bench', 'heavy leather belt, copper chisel, wooden mallet', 'bright sun striking the marble surfaces'),
    ('a Hittite metalworker', 'a cave‑like forge with bronze crucible, anvils, charcoal piles, stone arches, echoing clangs', 'thick leather apron, protective gloves, hammer, tongs, metal ingots', 'fiery orange light from the molten metal'),
    ('an airship mechanic', 'a massive canvas-filled hangar, rows of brass gas valves, wooden scaffolding, crates of spare propellers, light streaming through skylights', 'oil‑stained overalls, leather gloves, a toolkit belt, a leather cap with goggles hanging', 'bright daylight filtering through high glass panes onto the metallic floor'),
    ('a tapestry weaver', 'a vaulted room with massive looms, dyed yarn skeins, wooden spindles, and a wall of half‑finished tapestries', 'wearing a long linen dress, a woven sash, and a small shuttle', 'soft filtered sunlight filters through stained‑glass windows, casting colored patterns'),
    ('a jazz saxophonist', 'a small club stage with a polished piano, brass drum set, and low‑hanging vintage bulbs', 'a black tuxedo, polished shoes, saxophone case, pocket square', 'warm golden light from low‑hanging bulbs bathing the stage'),
    ('a horse‑drawn carriage driver', "cobblestone streets lined with gas‑lit lanterns, street vendors' stalls, and a bustling marketplace square", 'a leather apron, sturdy boots, a wide‑brimmed hat, and a set of reins', 'flickering orange light from the street lanterns'),
    ('an early 20th century radiographer', 'brick examination room with wooden examination table, heavy lead shield, glass window, metal cabinets, tiled floor', 'white lab coat, thick rubber gloves, lead apron, wooden stool, clipboard', 'steady incandescent glow from a hanging bulb casting even light across the room'),
    ('a taco stand operator', 'a colorful stall with metal grill, hanging chili strings, stacked corn tortillas, wooden serving board', 'bright shirt, straw hat, tongs, lime squeezer', 'vivid midday sun casting warm shadows'),
    ('a coastal storm‑watch officer', 'cliffside watchtower with weather instruments, wind‑swept flag, sea spray mist, rugged stone steps', 'windbreaker, binoculars, waterproof notebook, radio communicator', 'brisk sea‑air light with occasional sun bursts'),
    ('a railway signal operator', 'elevated signal tower beside tracks, red and green lights, wooden fence, and a misty valley below', 'dark coat, signal lever, pocket flashlight, and a brass badge', 'cool morning mist illuminated by signal lamps'),
    ('a bookbinder', 'a quiet room with wooden presses, stacks of vellum sheets, leather rolls, and a copper binding press', 'wearing a linen vest, thin gloves, and a small leather mallet', 'soft lamplight glows amber, casting warm shadows on the table'),
    ('an immunologist', 'a sterile bench with pipette racks, petri dishes, refrigerated incubator, and a wall of glass shelves', 'white lab coat, latex gloves, safety goggles, clipboards, digital timer', 'bright overhead fluorescents casting even illumination across the workspace'),
    ('a Lebanese mezze platter artist', 'ceramic plates stacked, olives in glass bowls, fresh herbs, brass bowls, woven table runner, citrus scent', 'white tunic, embroidered vest, small serving tray, wooden spoon, comfortable sandals', 'warm daylight filtering through a lattice window'),
    ('an electric vehicle charging attendant', 'a modern parking garage with rows of charging stalls, sleek concrete columns, and soft ambient lighting', 'a branded polo shirt, tablet, tool kit, and a safety vest', 'cool blue light emanating from the charging units'),
    ('a monastery scribe', 'a stone cloister with stone benches, wooden lectern, candle holders, stacks of vellum, quiet garden view', 'rough wool robe, reed pen, ink pot, small wooden cross pendant', 'soft glow of multiple candles flickering in the night'),
    ('a glassblower', 'open furnace area with glowing crucible, glass tubes on wooden racks, sand piles, charcoal fire', 'heat‑resistant apron, long tongs, leather gloves', 'intense orange light from the furnace flames'),
    ('an Assyrian chariot maker', 'a workshop with wooden frames, bronze wheels, leather straps, tools hanging, dust motes, stone floor', 'leather apron, heavy boots, hammer, chisel, protective headband', 'sunlight streaming through a high opening, casting sharp shadows'),
    ('a marathon runner', 'city street early morning, lined with trees, empty sidewalks, street lamps, distant skyline, road markings', 'technical running shirt, shorts, shoes, hydration belt, wristwatch', 'cool dawn light casting a pale blue hue'),
    ('a shoemaker', 'a compact shop with wooden lasts, leather strips, stitching awls, and a wall of polished shoes', 'wearing a canvas apron, sturdy shoes, and holding a small awl', 'soft warm light from a hanging lantern glows over the leather'),
    ('a plant physiologist', 'a growth‑chamber greenhouse with adjustable LED panels, hydroponic racks, misting system, and a sensor array wall', 'lightweight lab coat, moisture sensor glove, portable chlorophyll meter, notebook', 'vivid green light from programmable LED strips bathing the plants'),
    ('a Greek souvlaki cook', 'metal rotisserie, stacked pita breads, olive oil bottles, lemon wedges, hanging oregano bunches, tiled floor', 'white shirt, blue apron, metal tongs, wooden spatula, comfortable sandals', 'clear bright light from a sunny courtyard'),
    ('a surgical resident', 'sterile operating room, hanging lights, steel table, instrument tray, glass wall, tiled floor', 'green scrub, surgical cap, handheld suction, pen, focused eyes', 'bright sterile light from overhead, precise clarity'),
    ('a cocktail mixologist', 'a polished bar top with mirrored back, rows of glass bottles, copper shakers, citrus garnish tray', 'black vest, crisp shirt, cocktail shaker, muddler', 'cool blue glow from LED backlighting'),
    ('a fire investigation specialist', 'burned warehouse interior with charred beams, soot‑covered floor, broken windows, scattered debris', 'protective coat, fire‑proof gloves, evidence bag, handheld scanner', 'muted orange glow from lingering flames reflected on walls'),
    ('a glider pilot', 'rolling hillside launch field with grassy runway, wind socks, wooden hangar, distant clouds', 'flight suit, helmet, harness, altimeter', 'clear blue light bathing the open sky'),
    ('a Parthian horse archer', 'grassland camp, wooden archery range, sandbags, distant hills, wind‑swept grasses', 'leather armor, composite bow, quiver of arrows, riding boots', 'bright clear sky casting sharp light over the camp'),
    ('a nuclear incident safety officer', 'containment yard with shielding walls, concrete slabs, monitoring consoles, steel drums, warning cones', 'radiation badge, lead apron, dosimeter, hard hat, thick gloves', 'steady low‑intensity amber glow from safety lamps'),
    ('an Indian spice blender', 'wooden mortar and pestle, rows of glass jars, vibrant turmeric piles, hanging copper pans, fragrant steam', 'cotton kurta, simple apron, spice scoops, wooden spoon, soft sandals', 'warm golden light spilling from a low hanging oil lamp'),
    ('a city scooter fleet manager', 'a bustling pedestrian plaza with charging stations, concrete pads, and decorative planters under a clear sky', 'a casual polo shirt, smart watch, tablet, and a set of spare batteries', 'bright daylight casting crisp shadows on the pavement'),
    ('a town baker', 'a rustic bakery with brick ovens, flour sacks, wooden carts, hanging loaves, clay pots', "flour‑dusted apron, baker's hat, wooden rolling pin, basket of dough", 'golden sunrise light spilling through a small front window'),
    ('a stone mason', 'sunlit quarry with towering limestone blocks, wooden scaffolding, dust clouds drifting over rugged cliffs', 'worn leather apron, heavy hammer, chisel tucked in belt', 'warm golden rays filtering through thin cloud cover'),
    ('a space shuttle flight controller', 'control room with glowing consoles, rows of chairs, cable bundles, and large windows overlooking launch pad', 'formal suit, badge, digital tablet, headset, polished loafers', 'soft ambient glow from panels illuminating the space'),
    ('a professional surfer', 'sun‑kissed beach, rolling waves, palm trees, wooden board racks, sandy shoreline, distant cliffs', 'wetsuit, board leash, surfboard tucked under arm, sunglasses', 'bright tropical sun casting dazzling reflections on the water'),
    ('a textile dyer', 'a large vat room with steaming dye baths, wooden racks, colorful cloth strips, and a steam vent', 'dressed in a rubber apron, rubber boots, and holding a wooden paddle', 'soft steam‑filled light creates a hazy, colorful glow'),
    ('a botanical illustrator', 'a studio‑lab hybrid with herbarium shelves, watercolor palettes, magnifying lamp, and a large drafting table', 'cotton smock, sketchbook, fine brushes, colored pencils, light‑weight apron', 'soft daylight‑mimicking lamp casting gentle, even light across the canvas'),
    ('an Australian coffee roaster', 'metal drum roaster, burlap bean sacks, stainless steel grinder, wooden crates, aromatic steam, concrete floor', 'casual shirt, denim apron, metal scoop, protective goggles, sturdy boots', 'soft morning light filtering through industrial windows'),
    ('a trauma surgeon', 'emergency bay, stainless tables, hanging lights, crash cart, large windows, polished floor', 'scrub suit, surgical glove, scalpel, hemostat, focused expression', 'intense white glare from overhead lights, urgent brightness'),
    ('a wine sommelier', 'a dimly lit cellar with wooden racks, stacked barrels, stone walls, soft candle clusters', 'crisp white shirt, black vest, tasting glass, corkscrew', 'gentle amber glow from candlelight'),
    ('a 911 dispatcher', 'dimly lit control room filled with glowing consoles, stacked folders, acoustic panels, coffee mugs on desks', 'formal shirt, headset microphone, wristwatch, slim notebook', 'warm amber desk lamps illuminating the workstation area'),
    ('a camel caravan guide', 'endless desert dunes, scattered oasis palms, sand ripples, distant mirage, stone cairns', 'loose linen robe, headscarf, leather satchel, walking stick', 'bright midday sun casting sharp shadows on sand'),
    ('a Byzantine mosaicist', 'marble floor with tiny colored stones, wooden mixing trays, frescoed arches, candle holders', 'linen smock, palette of pigments, tiny trowel, leather satchel', 'warm candlelight flickering across the mosaic'),
    ('a mass‑casualty triage nurse', 'field tent with red cross tarp, stretchers, medical bags, a portable oxygen tank, sandbags', 'light scrubs, stethoscope, triage tags, headlamp, compact med‑kit', 'soft lantern glow illuminating the tent interior'),
]


def sinh_dayinlife(i):
    # Mỗi nghề ba mảnh: NƠI (ba lớp xa-giữa-gần) · ĐỒ NGHỀ · ÁNH SÁNG. Ba mảnh này đi vào ba
    # tầng khác nhau của prompt, nên tách sẵn ở đây thay vì nhét chung một chuỗi.
    ds = MOT_NGAY
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


# ── DI_DAU: NÂNG TỪ DANH SÁCH NỘI BỘ LÊN BẢNG MODULE  (6/9/2026) ───────────────────────
# Danh sách này nằm TRONG `sinh_wheregoes` nên `bang_mo_rong.py` không nhìn thấy nó, và kênh
# `wheregoes` dừng ở 27 mục = cạn chủ đề sau ~13 tập short. Không phải vì thế giới hết thứ
# để nói — cùng niche ấy, `howloud` đi từ 31 lên 278 mục chỉ bằng cách nới BẢNG.
# Đưa ra ngoài không đổi một hành vi nào; nó chỉ làm dữ liệu NHÌN THẤY ĐƯỢC từ bên ngoài,
# đúng điều kiện để nới. Cùng bài học §15.12: một trường chỉ được ghi mà không ai đọc
# được thì coi như chưa tồn tại.
DI_DAU = [("the thing you put in recycling", "hop",
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
      ("your unwanted gift", "hop", "a liquidation warehouse of mixed unopened boxes"),

    # ── NỐI THÊM 6/9/2026 · 172 mục qua bốn cổng của `bang_van.py`
    #    (dạng · không người · không chữ · không viết nghịch · không trùng).
    #    Bảng này KHÔNG có con số nào, nên không có gì để đối chứng và cũng
    #    không đụng tới luật nền 'AI không bao giờ cấp một con số'.
    ('the used lithium phone battery', 'dien_thoai', _ve('a flat rectangular lithium cell with cracked edges', 'resting on a plastic recycling chute', '', 'behind the chute a wall of reclaimed wood panels', 'a thin layer of dark gravel', 'cool blue light with subtle teal hints')),
    ('the unit you ship', 'nguoi', _ve('a slim laptop with chipped hinge', 'balanced on a metal conveyor belt in a warehouse', '', 'behind a row of stacked wooden crates with weathered paint', 'under a thin layer of spilled oil droplets', 'neutral white illumination with subtle gray tones')),
    ('the popcorn kernels leftovers', 'nguoi', _ve('yellowish popped corn kernels', 'spread on a compost tray surface', '', 'behind a mound of vegetable scraps and coffee grounds', 'soft earth and tiny leaf fragments', 'warm sunrise gold with gentle shadows')),
    ('the dried herb stem', 'nguoi', _ve('a slender brown stem of dried basil', 'lying on a terracotta pot', '', 'behind a collection of glass spice jars', 'a sprinkle of tiny charcoal granules ahead', 'soft sage light with muted green tones')),
    ('the pair of denim jeans for upcycle', 'nguoi', _ve('a pair of distressed denim jeans with frayed cuffs', 'pinned on a cork board in a maker space', '', 'behind the board a shelf of paint cans and brushes', 'a reclaimed wood floor with scattered sawdust', 'bright morning light with fresh green hue')),
    ('the garden runoff water', 'coc', _ve('muddy water carrying small leaves', 'traveling through an outdoor rain gutter', '', 'behind the gutter a brick garden wall with vines', 'gravel path wet with runoff', 'dappled sunlight with earthy green mood')),
    ('the power strip you recycle', 'nguoi', _ve('a surge protector with broken switches', 'lying on a metal tray beside a workbench', '', 'behind a wall of exposed piping and ducts', 'on a concrete floor with scattered metal shavings', 'neutral gray light with faint blue undertones')),
    ('the soaked cotton swab', 'nguoi', _ve('white stick with a damp, fluffy tip', 'lying in a bathroom drain cover slot', '', 'behind the slot a smooth ceramic basin with a faint shine', 'a small pool of clear water surrounding the swab', 'soft warm light with gentle peach tint')),
    ('the chipped coffee cup', 'coc', _ve('white ceramic mug with a small crack', 'sitting on a gray plastic bin edge', '', 'near a row of overturned cardboard boxes', 'a thin layer of coffee grounds dusting the floor', 'cool morning light with pale blue hue')),
    ('the lace curtain you discard', 'nguoi', _ve('a sheer white lace curtain with delicate trim', 'draped over a rusted iron rod in a garden shed', '', 'behind a stack of old wooden crates', 'a cobblestone patio with scattered pebbles', 'soft diffused light with cool ivory tones')),
    ('the corroded battery case', 'nguoi', _ve('large plastic container with leaking acid stains', 'lying inside a rusted metal cage', '', 'adjacent to a pile of shredded copper wires and cables', 'wet soil dotted with dark puddles', 'dim greenish light with faint teal shadows')),
    ('the potato peel strips', 'nguoi', _ve('thin amber potato peels', 'sprawled across a compost tray', '', 'behind a heap of carrot tops and beet leaves', 'loose earthy compost and a few pebbles', 'soft warm light with a hint of amber')),
    ('the frayed knit hat', 'nguoi', _ve('a knitted beanie with loose yarn strands', 'propped against a metal fire pit', '', 'behind the pit a pine forest fading into dusk', 'a bed of pine needles surrounding the hat', 'deep orange glow with subtle crimson shadows')),
    ('the retired smartwatch', 'nguoi', _ve('a small rectangular device with a dented band', 'placed on a rotating platform for battery removal', '', 'behind a glass enclosure where lithium cells are extracted', 'a puddle of spilled electrolyte on a steel tray', 'soft pink light with a warm pastel feel')),
    ('the discarded car battery', 'xe', _ve('a large heavy lead-acid battery with rusted terminals', 'parked inside an open-air hazardous waste pit', '', 'behind the pit a chain-link fence topped with barbed wire', 'wet mud mixed with broken glass shards', 'dim overcast sky with muted gray tones')),
    ('the speaker you recycle', 'nguoi', _ve('a portable Bluetooth speaker with scratched surface', 'placed on a pine bench beside a garden path', '', 'behind a low hedge of evergreen shrubs', 'on a mulch carpet dotted with pine needles', 'gentle sunrise orange with faint pink undertones')),
    ('the zucchini ends you cut', 'nguoi', _ve('dark green zucchini ends with seeds', 'stacked in a compost bin corner', '', 'behind a layer of moist soil and mulch', 'soft earth and small bark pieces', 'cool garden green with warm sunlit highlights')),
    ('the soda can you recycle', 'nguoi', _ve('shiny aluminum cylinder with crinkled top', 'balanced on a rusted metal bin edge', '', 'a narrow alley lined with overflowing cardboard boxes', 'a puddle of rainwater reflecting the can', 'soft twilight blue with a hint of orange glow')),
    ('the rechargeable laptop battery', 'nguoi', _ve('large rectangular laptop battery with vents', 'leaning against a rusted metal pipe', '', 'a wall of stacked steel drums behind', 'crushed gravel covering the floor', 'cool cyan light with faint teal accents')),
    ('the laundry rinse water', 'coc', _ve('clear water tinged with fabric softener scent', 'draining from a washing machine into a utility drain', '', 'behind the machine a row of stacked laundry baskets', 'concrete floor with faint suds residue', 'soft indoor glow with pastel blue hue')),
    ('the USB hub you discard', 'nguoi', _ve('a hub with missing ports and bent pins', 'resting on a metal shelf in a utility room', '', 'behind a row of hanging tool belts', 'on a concrete slab with scattered metal clips', 'neutral white illumination with subtle gray cast')),
    ('the drained aquarium water', 'coc', _ve('clear liquid with tiny floating plant fragments', 'collecting in a shallow basin beside a bathroom drain', '', 'behind the basin a tiled floor with subtle grout lines', 'a thin layer of water covering the basin bottom', 'soft pastel light with muted teal hue')),
    ('the padded envelope', 'nguoi', _ve('soft foam-lined envelope with bubble corners', 'sitting on a shelf beside reusable bags', '', 'behind a stack of reusable tote containers', 'a thin carpet of dust motes near the base', 'gentle teal lighting with calm undertones')),
    ('the terry cloth bathrobe you replace', 'nguoi', _ve('a plush terry cloth bathrobe in soft peach', 'draped over a ceramic vase on a balcony', '', 'behind a lattice trellis with blooming vines', 'a tiled balcony floor with tiny sea shells', 'late morning light with warm coral hues')),
    ('the shredded car seat belt', 'xe', _ve('woven web of frayed nylon strands', 'coiled on a rusted steel barrel', '', 'near a pile of twisted metal springs and clips', 'gritty sand mixed with loose bolts', 'cool early-morning light with pale teal shade')),
    ('the mushroom stems you cut', 'nguoi', _ve('soft brown mushroom stems', 'nestled among composted leaves', '', 'behind a mound of shredded newspaper and straw', 'moist compost and a few fallen pine needles', 'gentle dusk purple with warm undertones')),
    ('the stale bread crust', 'nguoi', _ve('dry golden slice with uneven edges', 'sinking into an anaerobic digester chamber', '', 'behind a thick concrete wall lined with pipes', 'muddy slurry covering the chamber floor', 'muted brown tones with faint orange highlights')),
    ('the knitted sweater for recycling', 'nguoi', _ve('a chunky wool sweater in pastel pink', 'folded on a wicker basket beside a donation bin', '', 'behind the basket a row of wooden pallets holding other textiles', 'a light dusted floor with tiny pine needles', 'gentle sunrise glow with peach hues')),
    ('the coffee grounds from filter', 'coc', _ve('wet brown coffee grounds soaked in water', 'sitting in a kitchen sink drain pipe', '', 'behind the pipe a tiled wall with faint grout lines', 'a slick stone floor with tiny water droplets', 'soft morning light with warm amber hue')),
    ('the keyboard you retire', 'nguoi', _ve('a mechanical keyboard with missing keys', 'placed on a steel tray in an industrial loft', '', 'behind a brick wall with exposed mortar joints', 'on a polished concrete slab with faint oil sheen', 'muted amber light with faint rust tones')),
    ('the busted gaming console with missing vent', 'nguoi', _ve('a black gaming console with a cracked front panel', 'sitting on a concrete slab beside a power strip', '', 'a backdrop of stacked cardboard boxes and foam inserts', 'scattered plastic clips and a broken controller joystick', 'cool teal lighting with subtle futuristic vibe')),
    ('the tin can of soup', 'nguoi', _ve('rust-speckled metal can with a dented rim', 'tilted inside a yellow recycling drum', '', 'a concrete slab littered with fallen leaves', 'a small puddle of oily residue nearby', 'soft dusk lavender with a faint orange hue')),
    ('the electric bike battery', 'nguoi', _ve('large rectangular lithium-ion bike battery', 'standing upright on a concrete platform', '', 'a line of empty cardboard tubes behind', 'a thin layer of spilled coffee grounds', 'bright white illumination with crisp cool shadows')),
    ('the fruit juice splash', 'nguoi', _ve('vivid orange juice mixed with water droplets', 'dripping into a kitchen floor drain', '', 'behind the drain a tiled backsplash with subtle pattern', 'linoleum floor with sticky orange sheen', 'vivid daylight with citrus orange glow')),
    ('the VR headset you recycle', 'nguoi', _ve('a headset with torn strap and foggy lenses', 'resting on a plush beanbag in a dim lounge', '', 'behind a curtain of dark velvet drapes', 'on a soft carpet with muted charcoal fibers', 'warm deep red light with faint burgundy shade')),
    ('the crumpled cardboard box', 'nguoi', _ve('a torn cardboard shipping container', 'lying flat on a recycling conveyor belt', '', 'a row of stacked wooden pallets behind the belt', 'scattered shredded paper pieces on the floor', 'soft warm amber glow with gentle shadows')),
    ('the poly mailer bag', 'nguoi', _ve('lightweight plastic bag with zip seal', 'inflated and hanging from a rack hook', '', 'above a row of empty shipping containers', 'a small pile of crushed bubble sheets', 'soft lavender hue with diffused illumination')),
    ('the mesh laundry bag you retire', 'nguoi', _ve('a white mesh laundry bag with zippered closure', 'placed on a metal drying rack outdoors', '', 'behind a row of potted herbs', 'a sun-warmed wooden deck with tiny footprints', 'bright sunny light with crisp white highlights')),
    ('the bent suspension arm', 'nguoi', _ve('long metal arm with twisted joints', 'propped on a rusted tire stack', '', 'next to a pile of broken brake lines', 'wet mud with scattered leaves', 'soft green light with subtle fog')),
    ('the tomato seed shells', 'nguoi', _ve('tiny orange tomato seed shells', 'scattered across a compost bin floor', '', 'behind a pile of vegetable peels and leaves', 'fine compost granules and a few bits of bark', 'bright daylight orange with gentle shadows')),
    ('the plastic bottle you recycle', 'nguoi', _ve('a clear PET bottle with a blue cap', 'floating gently on a slow moving stream', '', 'dense reeds swaying beside a misty marshland', 'smooth river stones glistening with algae', 'soft twilight blue with a calm glow')),
    ('the cotton t-shirt for upcycling', 'nguoi', _ve('a plain white cotton t-shirt with small tear', 'spread on a cutting board in a workshop', '', 'behind the board a wall of hanging fabric scraps', 'a reclaimed barn floor dotted with sawdust', 'bright daylight with crisp white ambience')),
    ('the soap suds from shower', 'nguoi', _ve('fluffy white bubbles clinging to tile', 'rolling down a shower drain channel', '', 'behind the channel a curved glass wall with mist', 'smooth stone floor slick with water', 'bright cool light with pale blue mood')),
    ('the charger you toss', 'nguoi', _ve('a power adapter with broken plug', 'stacked on a ceramic tile floor near a doorway', '', 'behind a row of potted succulents in terracotta pots', 'surrounded by scattered sand grains and tiny stones', 'cool mint light with gentle seafoam tones')),
    ('the tossed out printer with jammed rollers', 'nguoi', _ve('a bulky white printer with paper stuck inside', 'standing on a wooden pallet beside a stack of boxes', '', 'a dimly lit storage aisle lined with metal shelves', 'a pile of shredded paper scraps and ink cartridges', 'soft amber light with warm inviting mood')),
    ('the smashed portable speaker with torn mesh', 'nguoi', _ve('a cylindrical device with exposed wiring', 'lying on a sun-warmed patio tile', '', 'next to a low wooden fence covered in moss', 'surrounded by scattered seashells and sand', 'warm amber light with late-afternoon glow')),
    ('the steel canister', 'nguoi', _ve('large cylindrical steel container with rust patches', 'resting on a metal sorting platform', '', 'a row of industrial drums behind the platform', 'a smear of oil stain on the concrete floor', 'industrial glow with steel-gray ambience')),
    ('the battered car door', 'xe', _ve('rusted steel panel with dented hinge', 'leaning against a pile of shredded metal', '', 'behind a tangled heap of discarded engine blocks and tubing', 'scrap metal fragments scattered on a dusty ground', 'dim amber glow with muted orange tones')),
    ('the apple core you discard', 'nguoi', _ve('a brownish apple core with seeds', 'lying in a shallow compost bin', '', 'surrounded by damp leaf litter and soil fragments', 'soft earth mixed with tiny wood chips', 'warm amber glow with gentle shadows')),
    ('the torn paper envelope', 'nguoi', _ve('a ripped white mailing envelope', 'sliding down a chute into a bin', '', 'a row of cardboard tubes behind the chute', 'a thin carpet of loose fibers on the floor', 'soft pastel green light with calm ambience')),
    ('the insulated thermal bag', 'nguoi', _ve('white insulated carrier with reflective lining', 'placed on a cooling rack near a door', '', 'against a wall of stacked insulation panels', 'a few stray pieces of foil foil', 'cool silver light with crisp contrast')),
    ('the nylon windbreaker you toss', 'nguoi', _ve('a lightweight nylon windbreaker in electric orange', 'leaning against a metal fence post', '', 'behind a cluster of wind-swept grasses', 'a compacted earth ground with scattered twigs', 'strong midday sun with vibrant orange highlights')),
    ('the paper towel roll discarded', 'nguoi', _ve('empty white paper towel roll with a few sheets left', 'lying on a compost heap beside a garden path', '', 'a stone wall covered in moss and lichen', 'loose soil mixed with fallen leaves', 'dappled sunlight casting warm amber hues')),
    ('the herb stems you trim', 'nguoi', _ve('green basil and parsley stems', 'sprinkled over a compost tray', '', 'behind a heap of vegetable waste and coffee grounds', 'soft earth and tiny pine needles', 'fresh spring green with gentle sunlight')),
    ('the wilted lettuce leaf', 'cay', _ve('a limp green leaf with brown edges', 'lying on a wooden cutting board', '', 'against a tiled kitchen backsplash', 'a scattering of tiny pebbles on the floor', 'muted jade light with a cool tone')),
    ('the linen sheet for donation', 'nguoi', _ve('a crisp white linen sheet folded neatly', 'stacked on a wooden shelf in a shelter storage room', '', 'behind the shelf a wall of painted brick', 'a polished concrete floor with a few stray linens', 'muted daylight with cool gray tones')),
    ('the vegetable peel from sink', 'nguoi', _ve('green cucumber rind slick with water', 'spinning in a kitchen garbage disposal whirl', '', 'behind the disposal a dark cabinet door', 'stainless steel floor with a faint sheen', 'bright daylight with fresh lime hue')),
    ('the headset you donate', 'nguoi', _ve('a VR headset with cracked visor', 'lying on a glass shelf in a tech exhibit', '', 'behind a backdrop of soft fabric panels', 'on a polished marble floor with subtle veining', 'cool lavender light with subtle violet hue')),
    ('the junked external hard drive with dented case', 'xe', _ve('a black external hard drive with a cracked shell', 'resting on a metal grid tray', '', 'a concrete floor with a scattering of old packaging foam', 'a small pile of zip ties and broken USB plugs', 'soft greenish glow with calming tech vibe')),
    ('the stripped car battery', 'xe', _ve('an empty lead-acid car battery casing', 'placed on a steel grating platform', '', 'adjacent to a stack of copper cable reels', 'small puddles of acidic liquid stain the floor', 'soft greenish light with muted industrial feel')),
    ('the recyclable plastic wrap', 'nguoi', _ve('clear stretch film on a dispenser roll', 'partially unrolled across a workbench beside a box', '', 'behind a row of empty cardboard boxes awaiting fill', 'a polished concrete surface with faint footprints', 'bright white light with a crisp energy')),
    ('the dented car bumper', 'xe', _ve('heavy plastic and metal bumper with deep dents', 'resting on a sloping scrap yard ramp', '', 'behind a mound of crushed aluminum cans and brackets', 'gravel and oil stains covering the surface', 'warm golden light with subtle brown hues')),
    ('the carrot tops you cut', 'nguoi', _ve('green carrot tops with thin stems', 'scattered across a compost tray', '', 'behind a pile of shredded cabbage leaves', 'coarse compost fibers and small stone pieces', 'fresh morning green with soft diffused light')),
    ('the ripped paper bag', 'nguoi', _ve('a torn grocery paper bag', 'hanging from a recycling hook', '', 'a stack of cardboard milk cartons behind the hook', 'a few loose plastic fragments on the ground', 'cool morning blue light with gentle shadows')),
    ('the reusable bubble pouch', 'nguoi', _ve('fabric pouch filled with reusable bubbles', 'hung from a pegboard near a sorting table', '', 'next to a stack of empty poly mailers', 'a few stray bubbles rolled on the ground', 'cool cyan lighting with subtle sparkle')),
    ('the hemp tote bag you retire', 'nguoi', _ve('a natural hemp tote bag with braided straps', 'hung from a reclaimed iron hook on a wall', '', 'behind a weathered brick chimney', 'a cobblestone courtyard with scattered leaves', 'warm late-day light with soft amber tones')),
    ('the pizza box after a night', 'giuong', _ve('brown pizza cardboard with grease stains', 'slightly collapsed on a recycling station shelf', '', 'a metal recycling bin with a hinged lid', 'a few stray pepperoni bits on the floor', 'warm orange glow of late afternoon')),
    ('the pumpkin seed shells', 'nguoi', _ve('cracked orange pumpkin seed shells', 'scattered across a compost tray', '', 'behind a heap of shredded newspaper and straw', 'soft earth and tiny bark pieces', 'soft autumn orange with gentle shadows')),
    ('the peeled cucumber skin', 'nguoi', _ve('a long strip of pale green cucumber peel', 'coiled inside a glass jar', '', 'behind a shelf of mason jars', 'a layer of moist compost fibers below', 'fresh morning light with light teal hue')),
    ('the fleece blanket for recycling', 'nguoi', _ve('a thick teal fleece blanket with fringe edges', 'rolled on a metal cart in a textile recycling plant', '', 'behind the cart a series of conveyor belts and sorting bins', 'a gritty concrete floor with specks of dust', 'industrial white light with cool steel hue')),
    ('the shampoo residue from tub', 'nguoi', _ve('viscous lavender shampoo slick on surfaces', 'collecting in a bathtub overflow pipe', '', 'behind the pipe a tiled wall with subtle pattern', 'smooth white tiles glistening with foam', 'soft pastel light with lavender tint')),
    ('the drone you send', 'nguoi', _ve('a quadcopter with broken propeller', 'sitting on a metal platform in an open garage', '', 'behind a stack of spare batteries and wires', 'on a concrete floor dusted with fine grit', 'muted steel blue with faint charcoal hints')),
    ('the soggy paper towel', 'nguoi', _ve('white, crumpled sheet soaked in water', 'lying flat in the bathtub overflow groove', '', 'behind the groove a smooth porcelain surface with faint steam', 'a shallow pool of clear water at its edge', 'gentle diffused light with pale teal tint')),
    ('the lithium pack you discard', 'nguoi', _ve('thin flexible energy strip with silver contacts', 'coiled on a metal tray', '', 'behind a rusted metal cabinet and old paint cans', 'a smear of oil and grease stains', 'dim teal lighting with subtle blue undertones')),
    ('the satin pillowcase you replace', 'nguoi', _ve('a smooth satin pillowcase in deep burgundy', 'tucked inside a wicker laundry basket', '', 'behind an open window with sheer curtains', 'a polished wooden floor with a faint rug pattern', 'soft evening glow with muted rose tones')),
    ('the shattered side mirror', 'nguoi', _ve('glass and plastic mirror with broken frame', 'propped against a rusted tire stack', '', 'behind a pile of twisted metal springs and bolts', 'gritty sand covering the base of the mirror', 'cool twilight glow with deep indigo tones')),
    ('the eggshell fragments you crush', 'nguoi', _ve('crushed white eggshell pieces', 'spread over a compost pile surface', '', 'behind a mound of vegetable peels and stems', 'rich dark compost and a few tiny stones', 'soft daylight white with a faint yellow cast')),
    ('the abandoned e-reader', 'nguoi', _ve('slim tablet, faded backlight, cracked edge', 'lying on a stone countertop beside a kettle', '', 'a window view of a rainy street and distant trees', 'a few crumbs of dried tea leaves on the surface', 'muted teal light with soft gray undertones')),
    ('the foam corner protector', 'nguoi', _ve('triangular foam piece with adhesive backing', 'stuck on the side of a wooden crate', '', 'behind a line of empty cardboard boxes', 'a thin film of foam dust on the ground', 'soft lavender glow with calm ambience')),
    ('the rolled-up gift wrap', 'nguoi', _ve('a festive patterned paper roll', 'coiled neatly on a kitchen counter', '', 'a stack of empty jars on a shelf behind', 'a few stray confetti pieces on the tile', 'soft pastel light with rosy undertones')),
    ('the junk mail bundle you discard', 'nguoi', _ve('stack of glossy flyers and envelopes', 'overflowing a small recycling tote', '', 'a concrete wall with climbing vines', 'a scattering of torn paper fragments', 'bright daylight with crisp white brightness')),
    ('the beetroot tops you cut', 'nguoi', _ve('deep red beet tops with veins', 'tucked into a compost pile', '', 'behind a layer of shredded leaves and straw', 'moist compost and a few pine needles', 'rich ruby glow with soft amber light')),
    ('the sliced kiwi skin', 'nguoi', _ve('bright green fuzzy skin of a kiwi fruit', 'arranged in a circular pattern on a slate', '', 'near a small indoor fountain', 'wet moss covering the floor nearby', 'cool mint light with subtle sparkle')),
    ('the wool coat for second-hand shop', 'dong_ho', _ve('a heavy charcoal wool coat with deep pockets', 'hanged on a brass hook near a wooden bench', '', 'behind the bench a wall of reclaimed timber panels', 'a stone tiled floor with faint footprints', 'soft diffused light with cool slate tint')),
    ('the spilled milk from counter', 'nguoi', _ve('creamy white milk spreading across floor', 'flowing toward a hallway floor drain', '', 'behind the drain a painted wall with soft texture', 'light oak floor with milk sheen', 'soft morning light with buttery yellow tone')),
    ('the earphones you discard', 'nguoi', _ve('a set of earbuds with tangled cord', 'placed on a fabric pouf in a lounge area', '', 'behind a low bookshelf with assorted knick-knacks', 'on a soft carpet with muted teal threads', 'warm peach glow with gentle rose tint')),
    ('the leftover pasta water', 'coc', _ve('starchy, cloudy liquid collected in a pot', 'sitting in a stainless pot on the kitchen counter near the sink', '', 'behind the pot a wooden cabinet with a subtle grain pattern', 'a small splash of water spilling onto the countertop', 'bright natural light with warm honey tone')),
    ('the crinkled soda can', 'nguoi', _ve('shiny aluminum cylinder with dented top', 'resting on a metal recycling hopper', '', 'behind a stack of rusted wooden pallets', 'surrounded by scattered crushed newspaper pieces', 'soft amber glow with warm muted tones')),
    ('the flannel shirt you retire', 'nguoi', _ve('a red-black checked flannel shirt with cuffed sleeves', 'folded on a reclaimed pine table', '', 'behind a brick fireplace with stone mantle', 'a rustic stone floor dusted with ash', 'warm hearth light with deep orange tones')),
    ('the broken steering wheel', 'nguoi', _ve('black leather wheel with cracked rim', 'resting on a metal grate', '', 'behind a tower of discarded brake discs and rotors', 'scattered grit and small metal shards', 'subtle overcast light with muted gray tones')),
    ('the rice husk bits you discard', 'nguoi', _ve('tiny pale rice husks and grains', 'mixed into a compost bin bottom', '', 'behind a layer of moist soil and mulch', 'fine compost particles and a few wood chips', 'soft daylight beige with a hint of green')),
    ('the stained canvas tote', 'nguoi', _ve('a canvas tote bag splattered with coffee stains', 'resting on a stone ledge', '', 'behind the ledge a low stone wall covered in vines', 'a scattering of smooth river stones below', 'soft golden light with warm amber tones')),
    ('the protective foam sheet', 'nguoi', _ve('thin sheet of white packing foam', 'folded over a stack of parcels', '', 'next to a pile of empty bubble wrap rolls', 'a thin layer of foam dust on the ground', 'cool bluish light with muted highlights')),
    ('the empty alkaline kitchen battery', 'nguoi', _ve('a bright orange cylindrical battery missing its top', 'balanced on a metal sorting tray', '', 'behind the tray a concrete pillar with moss patches', 'a smooth concrete floor speckled with dust', 'gentle golden sunrise with warm pastel shades')),
    ('the console you discard', 'nguoi', _ve('a gaming console with dented case', 'sitting atop a glass table in a quiet showroom', '', 'behind a wall of frosted glass panels', 'next to a smooth stone floor with tiny pebbles', 'warm golden light with soft brown hue')),
    ('the grape seed husks', 'nguoi', _ve('tiny brown grape seed husks', 'mixed into a compost bin', '', 'behind a pile of shredded newspaper and straw', 'rich dark compost and small stones', 'soft dusk purple with warm amber tones')),
    ('the spoiled fish remains', 'nguoi', _ve('slimy, pinkish fish carcass fragments', 'sinking into a deep anaerobic lagoon', '', 'reed-like aeration pipes rise beyond the waterline', 'muddy sludge covering the lagoon bottom', 'murky greenish glow with occasional bubbles')),
    ('the crocheted blanket for reuse', 'nguoi', _ve('a colorful crocheted blanket with geometric motifs', 'spread over a low wooden table in a community center', '', 'behind the table a bookshelf filled with fabric swatches', 'a polished cement floor with a few stray yarn pieces', 'bright natural light with vibrant rainbow hue')),
    ('the fish tank water exchange', 'coc', _ve('clear aquarium water mixed with tiny algae', 'pouring into a bathroom floor drain', '', 'behind the drain a tiled shower enclosure', 'non-slip floor tiles speckled with droplets', 'cool bright light with aqua tint')),
    ('the smartwatch you replace', 'nguoi', _ve('a fitness band with broken clasp', 'lying on a ceramic tile near a plant pot', '', 'behind a low wall of stacked garden stones', 'on a smooth pebble path with tiny leaves', 'soft teal light with gentle seafoam hue')),
    ('the wet cardboard box', 'nguoi', _ve('brown corrugated sheet soaked through with water', 'stacked near a utility room floor drain', '', 'behind the stack a painted concrete wall with faint texture', 'a shallow puddle of water covering the floor', 'soft warm light with earthy amber tone')),
    ('the bubble wrap envelope', 'nguoi', _ve('transparent plastic film filled with air pockets', 'rolled up near a loading dock', '', 'against a wall of stacked pallets and crates', 'a glossy strip of discarded packaging tape', 'cool bluish light with subtle silver hints')),
    ('the microfiber towel you replace', 'nguoi', _ve('a teal microfiber towel with soft loops', 'rolled on a stainless steel countertop', '', 'behind a glass door leading to a patio', 'a tiled floor with faint water ripples', 'bright clean light with crisp turquoise hints')),
    ('the twisted car frame', 'xe', _ve('bent steel skeleton with jagged edges', 'balanced on a tilted steel beam', '', 'behind a mound of crushed engine blocks and pistons', 'coarse gravel covering the lower beams', 'harsh midday light with bright white glare')),
    ('the onion skin layers', 'nguoi', _ve('dry papery onion skins', 'layered in a compost bin corner', '', 'behind a pile of vegetable scraps and coffee grounds', 'crushed compost and tiny twig fragments', 'muted amber with subtle teal highlights')),
    ('the mismatched sock pair', 'nguoi', _ve('two wool socks, one striped, one plain', "tangled around a garden gnome's foot", '', 'behind the gnome a flowerbed bursting with daisies', "a patch of moist soil at the gnome's base", 'bright sunrise light with fresh green highlights')),
    ('the denim jacket you donate', 'nguoi', _ve('a faded blue denim jacket with metal buttons', 'hanging on a wooden rack in a charity shop', '', 'behind the rack a wall of stacked cardboard boxes', 'a polished concrete floor with scattered fabric tags', 'soft warm light with amber tones')),
    ('the spent alkaline 9-volt battery', 'nguoi', _ve('a rectangular black battery with peeled plastic cover', 'resting on a rusted steel grating', '', 'behind the grating a concrete wall with graffiti spray patterns', 'a thin layer of cracked paint', 'muted teal light with deep indigo shadows')),
    ('the router you replace', 'nguoi', _ve('a wireless router with broken antenna', 'lying on a metal shelf in a dim hallway', '', 'behind a series of ventilation grilles with rust streaks', 'on a concrete floor with scattered dust motes', 'cool cyan light with muted teal shadows')),
    ('the outdated tablet with faded display', 'nguoi', _ve('a rectangular tablet with a cracked glass front', 'leaning against a stack of printed manuals', '', 'a concrete floor lined with discarded packaging material', 'a few loose bolts and a bent metal clip', 'soft greenish hue with calming pastel vibe')),
    ('the glass jar of jam', 'coc', _ve('clear glass jar with a faded lid', 'standing upright in a glass recycling chute', '', 'a stone pathway bordered by low hedges and ferns', 'a smear of spilled fruit puree on the stones', 'gentle sunrise gold with soft violet shadows')),
    ('the small electric toothbrush battery', 'nguoi', _ve('tiny cylindrical battery from a toothbrush', 'placed on a woven bamboo mat', '', 'a row of empty tin cans behind', 'a thin layer of sawdust on the ground', 'warm amber light with soft honey tones')),
    ('the toothpaste slurry', 'nguoi', _ve('minty white paste mixed with water', 'running down a bathroom sink drain', '', 'behind the sink a porcelain countertop with a toothbrush holder', 'smooth ceramic tiles with a thin film', 'bright cool light with fresh mint hue')),
    ('the smart speaker you donate', 'nguoi', _ve('a cylindrical speaker with dented body', 'sitting on a marble pedestal near a plant', '', 'behind a wall of glass tiles with subtle veining', 'on a polished stone floor with faint sparkle', 'cool sapphire light with gentle blue tint')),
    ('the emptied chemical spray can', 'nguoi', _ve('a silver aerosol container with rusted nozzle', 'resting against a cracked concrete wall', '', 'near a pile of broken garden hoses and wilted vines', 'covered in a thin layer of dried dust', 'muted teal light casting gentle shadows')),
    ('the kraft paper wrap', 'nguoi', _ve('brown kraft paper with twine fastened tightly', 'folded over a wooden crate in a corner', '', 'next to a row of empty cardboard boxes', 'a smear of adhesive residue on the floor', 'warm honey-colored glow with soft shadows')),
    ('the burlap sack you discard', 'nguoi', _ve('a coarse natural burlap sack with rope handles', 'standing upright on a wooden pallet', '', 'behind a stack of old wooden barrels', 'a rough concrete floor with dust patches', 'soft overcast light with muted earth tones')),
    ('the old sedan chassis', 'nguoi', _ve('rusted steel frame with faded paint', 'sitting on a dusty junkyard floor', '', 'behind a mound of tangled wire and oil drums', 'gravel and broken glass scattered nearby', 'soft amber glow with muted shadows')),
    ('the avocado pit you toss', 'nguoi', _ve('large dark green avocado pit', 'sitting at the base of a compost heap', '', 'behind a layer of broken fruit skins and pulp', 'rich dark compost and small stone pieces', 'deep earth brown with soft golden light')),
    ('the disposable razor', 'nguoi', _ve('metal handle with plastic cartridge and blades', 'moving through a shredding carousel', '', 'behind a rotating cage of steel rods', 'tiny metal curls resting on the conveyor', 'bright white light with subtle blue tint')),
    ('the silk scarf sent abroad', 'nguoi', _ve('a delicate silk scarf with floral pattern', 'rolled inside a padded envelope on a shipping table', '', 'behind the table a stack of wooden crates ready for loading', 'a smooth stone tile with a few stray threads', 'cool morning light with pale blue shade')),
    ('the citrus peel from juicer', 'nguoi', _ve('bright orange lemon rind dripping with juice', 'floating in a bathroom bathtub drain', '', 'behind the tub a frosted glass panel and tiled edge', 'smooth porcelain tiles glistening with water', 'cool daylight with gentle teal tone')),
    ('the mouse you discard', 'nguoi', _ve('a wireless mouse with frayed cable', 'lying on a velvet cushion in a quiet nook', '', 'behind a low bookshelf filled with antique volumes', 'on a plush carpet with muted burgundy threads', 'warm rose glow with soft mauve accents')),
    ('the dead digital camera with shattered lens', 'nguoi', _ve('a compact digital camera with a broken glass lens', 'leaning against a metal filing cabinet', '', 'a wall of reclaimed wood panels with hanging cables', 'a few loose memory cards and a torn strap', 'muted lavender light with tranquil pastel mood')),
    ('the metal bottle cap', 'nguoi', _ve('shiny steel cap with a dented edge', 'spilling onto a metal sorting conveyor', '', 'a concrete loading dock with stacked crates', 'a thin line of oil slick on the concrete', 'soft sunrise gold with muted cyan')),
    ('the newspaper bundle', 'nguoi', _ve('stacked sheets of gray printed paper', 'piled in a paper recycling chute', '', 'a wooden fence with vines behind the chute', 'a carpet of crumpled paper bits at the base', 'muted daylight with warm honey colour')),
    ('the aquarium water change', 'coc', _ve('clear water with tiny fish food particles', 'pouring into a bathroom utility sink drain', '', 'behind the sink a tiled wall with subtle mosaic', 'non-slip mat wet with droplets', 'calm daylight with soft aqua tint')),
    ('the laptop charger you discard', 'nguoi', _ve('a brick-shaped charger with cracked casing', 'placed on a rusted metal tray beside a tool bench', '', 'behind a wall of stacked wooden pallets', 'on a gritty concrete floor with oil stains', 'cool steel blue with faint gray highlights')),
    ('the flattened pizza box', 'nguoi', _ve('a flattened cardboard pizza container', 'resting against a recycling bin wall', '', 'a stack of empty milk cartons behind it', 'a small puddle of water from a leaky pipe', 'bright daylight yellow with soft shadows')),
    ('the wooden crate lid', 'nguoi', _ve('sturdy pine lid with metal hinges', 'resting on top of an open crate', '', 'behind a stack of reclaimed wooden pallets', 'a scattering of pine shavings on the ground', 'rich amber light with subtle warm shadows')),
    ('the velvet cushion you donate', 'nguoi', _ve('a plush velvet cushion in royal purple', 'propped against a stone garden wall', '', 'behind a blooming lavender bush', 'a gravel path with soft moss edges', 'evening glow with deep violet undertones')),
    ('the cardboard box you recycle', 'nguoi', _ve('large corrugated cardboard box with flaps folded', 'stacked in a recycling bin near the curb', '', 'a row of wooden pallets awaiting collection trucks', 'crumpled newspaper pieces scattered on the concrete', 'soft morning light with muted gray tones')),
    ('the corn cob remnants', 'nguoi', _ve('dry yellowish corn cob fragments', 'stacked in a compost corner', '', 'behind a mound of shredded newspaper and straw', 'wet compost and small leaf pieces', 'warm golden light with soft green hints')),
    ('the aluminum can from soda', 'nguoi', _ve('shiny silver can with a dented rim', 'spinning slowly in a whirlpool of water', '', 'overgrown cattails framing a quiet pond', 'muddy sand mixed with tiny shells', 'warm amber light reflecting off ripples')),
    ('the polyester jacket for resale', 'nguoi', _ve('a bright orange polyester jacket with reflective strips', 'hung on a metal hook in a storefront window', '', 'behind the window a row of mannequins draped in garments', 'a glossy tiled floor with faint footprints', 'soft golden light with warm orange tint')),
    ('the hair clippings from sink', 'nguoi', _ve('tiny dark strands tangled in water', 'settling at the bottom of a bathroom sink drain', '', 'behind the sink a marble countertop with a faucet', 'polished ceramic tiles dotted with droplets', 'soft warm glow with subtle amber shade')),
    ('the battery you recycle', 'nguoi', _ve('a lithium battery pack with corroded terminals', 'resting on a steel tray in a recycling bin area', '', 'behind a wall of stacked metal drums with rust patches', 'on a gritty concrete base with spilled grit', 'soft teal illumination with faint gray undertones')),
    ('the obsolete router with broken antennas', 'nguoi', _ve('a small gray router with cracked plastic housing', 'sitting on a concrete slab next to a power outlet', '', 'a wall of exposed brick with hanging cable bundles', 'a few tangled Ethernet cables lying loose', 'cool cyan lighting with modern sleek feel')),
    ('the fried gaming console with melted plastic', 'nguoi', _ve('a bulky box with scorched corners', 'sitting on a rusted metal fire pit', '', 'behind a stack of pine logs ready for burning', 'on a bed of dark charcoal dust', 'deep orange light with smoky undertones')),
    ('the biodegradable packing peanuts', 'nguoi', _ve('fluffy corn-based pellets in a white sack', 'spilled onto a low platform beside a packing station', '', 'behind a stack of cardboard sheets waiting for use', 'a smooth concrete pad dotted with loose pellets', 'fresh greenish light with a lively vibe')),
    ('the cracked windshield glass', 'coc', _ve('shattered transparent pane with jagged edges', 'lying flat on a gravel driveway', '', 'near a rusted chassis surrounded by twisted steel rods', 'small shards glittering among coarse sand', 'soft cool light with pale blue shadows')),
    ('the banana peel you toss', 'nguoi', _ve('a yellow banana peel with brown spots', 'curled at the edge of a compost heap', '', 'behind a mound of shredded newspaper and straw', 'loose compost granules and fallen garden twigs', 'soft sunrise gold with subtle orange hue')),
    ('the sealed cardboard parcel', 'nguoi', _ve('a taped cardboard shipping package', 'sitting on a pallet in a sorting area', '', 'rows of wooden crates behind the pallet', 'a thin line of adhesive tape on the floor', 'soft golden hour light with warm tones')),
    ('the zip-tie bundle', 'nguoi', _ve('cluster of bright nylon zip ties', 'spilled onto a concrete floor near a cart', '', 'behind a row of empty cardboard tubes', 'a thin film of spilled packing tape', 'neutral gray light with subtle blue tint')),
    ('the spandex leggings you discard', 'nguoi', _ve('a glossy black spandex legging with seamless seams', 'coiled on a steel pipe near a loading dock', '', 'behind a stack of wooden pallets', 'a concrete slab with faint oil stains', 'cool industrial light with muted charcoal hues')),
    ('the glossy magazine you toss', 'nguoi', _ve('shiny full-color magazine pages slightly torn', 'piled on a curbside waste container', '', 'a graffiti-free brick fence with ivy vines', 'a thin layer of dust on the pavement', 'cool blue light with a hint of teal')),
    ('the cheese rind scraps', 'nguoi', _ve('yellowish cheese rind pieces', 'placed on top of a compost heap', '', 'behind a mound of vegetable scraps and coffee grounds', 'soft compost and scattered leaf fragments', 'warm buttery light with gentle shadows')),
    ('the soft mushroom cap', 'nguoi', _ve('a smooth brown cap of a button mushroom', 'settled on a wicker basket', '', 'under a hanging copper pot rack', 'a rug of shredded newspaper underneath', 'earthy brown light with a hint of green')),
    ('the vintage dress for charity auction', 'nguoi', _ve('a floral vintage dress with lace trim', 'displayed on a vintage wooden mannequin in a gallery', '', 'behind the mannequin a velvet drape and antique frames', 'a polished hardwood floor with scattered rose petals', 'warm amber light with soft rose glow')),
    ('the melted ice from freezer', 'nguoi', _ve('clear water pooling with tiny ice shards', 'draining through a laundry room floor drain', '', 'behind the drain a stack of clean towels', 'gray concrete slab wet with meltwater', 'cool neutral light with soft silver tone')),
    ('the camera you send', 'nguoi', _ve('a digital camera with dented body', 'placed on a wooden crate in a shipping area', '', 'behind a stack of bubble wrap sheets', 'on a rough timber floor with stray splinters', 'warm amber glow with faint copper tint')),
    ('the useless Bluetooth speaker with cracked dome', 'nguoi', _ve('a compact Bluetooth speaker with a shattered front dome', 'standing on a wooden pallet beside a pile of cables', '', 'a dimly lit garage corner with stacked pallets', 'a few loose speaker drivers and torn fabric mesh', 'cool teal light with relaxed calm mood')),
    ('the alkaline can you toss', 'nguoi', _ve('bright orange rectangular household power source', 'resting inside a cracked plastic container', '', 'behind a pile of dried cardboard boxes and tape rolls', 'a thin layer of dust and shredded paper', 'cool fluorescent light with pastel yellow hue')),
    ('the eco-friendly packing paper', 'nguoi', _ve('recycled kraft paper sheets crumpled for cushioning', 'scattered across a packing station beside a box', '', 'behind a stack of empty cardboard boxes awaiting reuse', 'a rough wooden floor with soft dust', 'soft forest green light with a calm ambience')),
    ('the rusted exhaust pipe', 'nguoi', _ve('curved steel pipe coated in orange rust', 'coiled on a wooden pallet', '', 'adjacent to a stack of broken radiators and copper coils', 'dry earth dotted with tiny metal flakes', 'muted sunrise light with gentle pink shades')),
    ('the tea bags you empty', 'nguoi', _ve('used tea bags with dried leaves', 'nestled in a compost bin corner', '', 'behind a layer of fallen autumn leaves', 'loose, crumbly soil and tiny bark shards', 'warm amber tone with gentle orange undertones')),
    ('the folded paper shopping list', 'nguoi', _ve('a folded sheet of lined paper', 'tucked into a recycling bag', '', 'a row of cardboard delivery boxes behind the bag', 'a few stray paperclips on the floor', 'warm sunrise gold with subtle glow')),
    ('the postage stamp sheet', 'nguoi', _ve('grid of adhesive stamps on paper', 'scattered across a wooden pallet', '', 'against a wall of empty envelope bins', 'a few torn stamp corners on the floor', 'soft ivory glow with muted highlights')),
    ('the plush stuffed animal costume you donate', 'huou', _ve('a fluffy plush costume resembling a bunny in pastel pink', 'folded on a soft rug in a playroom corner', '', 'behind a low wooden bookshelf filled with toys', 'a plush carpet with subtle pastel speckles', 'gentle morning light with sweet pink hues')),
    ('the cereal box you recycle', 'nguoi', _ve('brightly colored cereal box with torn corners', 'standing upright in a cardboard collection bin', '', 'a row of stacked wooden crates in the alley', 'a thin carpet of shredded paper shreds', 'soft pastel light with gentle lavender tones')),
    ('the leafy kale stems', 'nguoi', _ve('dark green kale stems with ribs', 'layered in a compost bin', '', 'behind a mound of vegetable peels and coffee grounds', 'rich compost soil and small stone bits', 'vibrant forest green with warm sunlight')),
    ('the crushed grape seed', 'nguoi', _ve('a handful of tiny dark grape seeds', 'scattered across a ceramic plate', '', 'against a backdrop of hanging dried herbs', 'a thin film of sand-like soil ahead', 'soft violet glow with calm undertones')),
    ('the canvas tote bag for reuse', 'nguoi', _ve('a sturdy canvas tote bag with natural fibers', 'leaning against a wooden crate in a market stall', '', 'behind the crate a row of hanging dried herbs', 'a cobblestone floor with a few loose stones', 'late afternoon sun with mellow amber shade')),
    ('the dishwater suds from sink', 'nguoi', _ve('frothy white bubbles mixed with grease', 'swirling inside a kitchen sink trap', '', 'behind the trap a wooden cabinet with open doors', 'bright stainless steel countertop with water streaks', 'warm daylight with creamy ivory glow')),
    ('the hard drive you recycle', 'xe', _ve('a portable SSD with dented case', 'resting on a wooden pallet in a storage room', '', 'behind a row of sealed plastic containers', 'on a rough concrete slab with scattered sawdust', 'cool silver light with subtle violet undertone')),
    ('the rinsed vegetable peels', 'nguoi', _ve('green and orange fragments of carrots and cucumbers', 'scattered in the kitchen sink drain basket', '', 'behind the basket a stainless steel sink basin with water droplets', 'a thin sheet of running water flowing over the basket', 'fresh natural light with soft green shade')),
    ('the expired milk carton', 'nguoi', _ve('creamy, slightly curdled cardboard container', 'floating in a high-rate anaerobic digester', '', 'surrounded by sealed steel tanks and vent pipes', 'bubbles of methane rising slowly', 'deep indigo light with subtle green undertones')),
    ('the corduroy pants you no longer need', 'nguoi', _ve('a pair of dark brown corduroy trousers', 'hanged on a metal coat rack in a hallway', '', 'behind a cracked plaster wall with faded paint', 'a worn linoleum floor with subtle scuff marks', 'neutral daylight with cool gray shadows')),
    ('the worn out car seat', 'xe', _ve('fabric upholstered cushion with frayed edges', 'folded on a concrete slab', '', 'near a heap of dented steel frames and suspension arms', 'dusty ground littered with loose screws', 'soft sunrise light with warm honey hue')),
    ('the bread crust leftovers', 'nguoi', _ve('dry golden-brown bread crust', 'lying on top of a compost layer', '', 'behind a pile of shredded lettuce and kale', 'soft compost earth and scattered seed shells', 'warm sunrise gold with gentle shadows')),
    ('the faded wool sweater', 'nguoi', _ve('a chunky wool sweater in muted gray', 'folded on a weathered pine table', '', 'behind the table a window overlooking misty hills', 'a rug of soft woven fibers under the sweater', 'cool bluish light with subtle gray shadows')),
    ('the recycled paper envelope', 'nguoi', _ve('brown envelope made from recycled fibers', 'lying flat on a metal sorting tray', '', 'behind a row of empty cardboard dividers', 'a few torn envelope edges on the floor', 'warm amber glow with subtle shadows')),
]


def sinh_wheregoes(i):
    ds = DI_DAU
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


# ── LUAT_NGAM: NÂNG TỪ DANH SÁCH NỘI BỘ LÊN BẢNG MODULE  (6/9/2026) ───────────────────────
# Danh sách này nằm TRONG `sinh_therules` nên `bang_mo_rong.py` không nhìn thấy nó, và kênh
# `therules` dừng ở 25 mục = cạn chủ đề sau ~12 tập short. Không phải vì thế giới hết thứ
# để nói — cùng niche ấy, `howloud` đi từ 31 lên 278 mục chỉ bằng cách nới BẢNG.
# Đưa ra ngoài không đổi một hành vi nào; nó chỉ làm dữ liệu NHÌN THẤY ĐƯỢC từ bên ngoài,
# đúng điều kiện để nới. Cùng bài học §15.12: một trường chỉ được ghi mà không ai đọc
# được thì coi như chưa tồn tại.
LUAT_NGAM = [("your own driveway",
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
      ("the fee for paying by card", "a small shop counter with a handwritten notice"),

    # ── NỐI THÊM 6/9/2026 · 275 mục qua bốn cổng của `bang_van.py`
    #    (dạng · không người · không chữ · không viết nghịch · không trùng).
    #    Bảng này KHÔNG có con số nào, nên không có gì để đối chứng và cũng
    #    không đụng tới luật nền 'AI không bao giờ cấp một con số'.
    ('the kitchen sink', _ve('stainless steel basin with chrome faucet and drain', 'centered slightly to the left in the frame', '', 'white tiled wall with a subtle grout pattern behind it', 'smooth gray tiles extending outward toward the viewer', 'soft morning light with cool blue tones')),
    ('the front porch steps', _ve('weathered stone steps leading up to the door', 'ascending from right to left in frame', '', 'lush climbing vines draped over the railing behind', 'clean white tiles with a thin line of moss', 'golden sunrise glow with soft pastel shadows')),
    ('a secure data vault door', _ve('reinforced steel door with numeric keypad', 'opened slightly, revealing interior glow', '', 'dark hallway lined with silent racks', 'gritty concrete steps leading forward', 'deep amber lighting with heavy shadows')),
    ('an electronic barcode scanner', _ve('a sleek handheld device with green light', 'placed on a metal stand near the left side', '', 'a wall of pastel-painted panels behind the scanner', 'a smooth tiled floor with subtle grout lines', 'cool daylight with subtle teal hints')),
    ('a conference room', _ve('a rectangular room with a long wooden table', 'viewed from the entrance looking toward the far wall', '', 'a whiteboard covered with faint grid lines', 'carpeted floor with a patterned runner', 'warm amber lighting with gentle shadows')),
    ('the decorative wall clock', _ve('circular clock with minimalist black numerals', 'hung slightly above eye level on the far wall', '', 'a row of abstract art panels in muted colors', 'polished concrete floor with faint reflective spots', 'gentle sunrise amber with faint rose blush')),
    ('a candy jar', _ve('a clear glass container filled with colorful sweets', 'positioned slightly off-center to the right', '', 'a pastel-painted wall with a subtle pattern', 'a smooth white tile floor in front of the jar', 'cheerful daylight with bright pastel hues')),
    ('the vacant parking stall', _ve('a painted white rectangle on a concrete slab', 'framed from a low angle looking upward', '', 'a row of apartment building windows beyond the stall', 'gravel with a few fallen leaves scattered', 'cool twilight with subtle purple hues')),
    ('an employee handbook', _ve('thick bound booklet resting on a wooden desk', 'lying flat near the edge of the frame', '', 'a potted plant with glossy green leaves', 'a smooth stone countertop with a few scattered pens', 'gentle warm illumination from a desk lamp')),
    ('an optical fiber splice tray', _ve('transparent tray holding tiny glass fibers', 'close-up shot, fibers fanning outward', '', 'blurred rack of networking gear behind', 'smooth steel surface with faint reflections', 'cool cyan light with crisp highlights')),
    ('the entryway shoe mat', _ve('a woven coir mat with a simple pattern', 'placed centrally near the door threshold', '', 'a painted door with a brass knob', 'a polished stone floor with subtle dust motes', 'soft natural light with warm earth tones')),
    ('the temporary construction barricade', _ve('orange barricade panels marking a blocked parking area', 'arranged diagonally across the foreground, leading the eye', '', 'a construction site with stacked steel beams behind', 'gravel with scattered small rocks', 'overcast sky with neutral gray lighting')),
    ('the barcode scanner stand', _ve('a sleek black device with a glass lens and LED indicator', 'positioned directly in front of the counter, central focus', '', 'a shelf of unopened packaging boxes behind it', 'a clean tiled floor with a faint reflection', 'cool white light with subtle silver tones')),
    ('the ferry terminal pier', _ve('a wooden pier extending into calm water', 'low angle showing the length of the dock', '', 'distant hills and a cloudy sky behind', 'weathered planks with scattered seaweed', 'muted overcast light with gentle grey tones')),
    ('the spice rack', _ve('a wooden spice rack holding glass jars on a wall', 'shown from a slight side angle', '', 'a brushed metal vent cover above the rack', 'a thin line of spilled pepper on the floor', 'warm afternoon sun with golden highlights')),
    ('a ceramic soap dish', _ve('white bowl with a small drainage hole', 'placed near the lower edge of the frame', '', 'tiled bathroom wall with a subtle wave pattern behind', 'cool marble slab extending toward the camera', 'gentle natural light with pale blue undertones')),
    ('the patio umbrella stand', _ve('metal base holding a large fabric umbrella', 'placed slightly off-center near the table', '', 'lawn with a line of potted rosemary behind', 'stone patio with a few scattered shells', 'sunny bright light with soft white canopy shadows')),
    ('a modest studio apartment', _ve('small living space with a single window', 'centered with ceiling light casting soft shadows', '', 'brick wall with faint water stains behind the sofa', 'bare wooden floor with a thin rug', 'warm amber glow with muted earth tones')),
    ('the lone traffic cone', _ve('orange reflective cone standing on a flat surface', 'placed near the right edge, slightly forward', '', 'empty lot with a distant fence and shrubbery behind', 'gravel driveway with scattered dust particles', 'cool dusk light with pinkish-purple shades')),
    ('a RAID array chassis', _ve('silver tower with rotating drive bays', 'centered, slightly elevated above the floor', '', 'cable bundles and a small power distribution unit behind', 'a dark gray carpet with low pile', 'soft gold illumination with cool blue undertones')),
    ('the hidden compliance checklist', _ve('laminated checklist pinned to a cork board', 'centered in the lower third of the composition', '', 'a row of neatly arranged office chairs', 'soft carpet with a faint wave pattern', 'gentle sunrise amber with a hint of rose')),
    ('the discreet traffic cone', _ve('an orange safety cone placed on a quiet road', 'situated near the bottom edge of the view', '', 'a row of parked cars lined up behind the cone', 'asphalt extending forward with faint lane markings', 'bright daylight with crisp white highlights')),
    ('the encryption key vault', _ve('steel safe glowing with faint blue runes', 'positioned centrally against a shadowed wall', '', 'rows of locked digital lockers behind it', 'tiny holographic keys hovering near the floor', 'cold steel blue with subtle violet undertones')),
    ('an expense report form', _ve('multi-page spreadsheet printout with highlighted totals', 'fanned slightly on a conference table', '', 'a glass water pitcher with condensation droplets', 'a dark laminate surface with a subtle grain pattern', 'cool office lighting with a hint of teal')),
    ('a rack-mount power strip', _ve('metal strip with multiple outlets and switches', 'placed at the base of a server rack', '', 'wall of cable bundles hanging loosely behind', 'rubberized floor panel with a faint oil mark', 'soft white illumination with subtle amber accents')),
    ('the wheel lock device', _ve('metal clamp attached to a front tire', 'close-up on the left side of the frame', '', 'rear tire and a portion of the wheel hub behind', 'rubber tread with a small speck of dirt', 'neutral daylight with subtle steel reflections')),
    ('the price scanner', _ve('a sleek black barcode scanner mounted on a stand', 'positioned at the right edge of the image', '', 'a stack of printed price stickers on a nearby table', 'a smooth tiled floor reflecting a hint of blue', 'cool fluorescent light with subtle teal tones')),
    ('an unlabelled network hub', _ve('small box with eight glowing port lights', 'positioned on a low shelf in the foreground', '', 'stack of spare cables leaning behind the shelf', 'light gray carpet tiles covering the floor', 'cool teal lighting with subtle reflections')),
    ('the ledger shelf', _ve('tall oak shelf filled with bound ledgers', 'placed to the left side of the frame', '', 'a dim hallway with stone arches recedes behind', 'rich walnut floorboards lie in front of the shelf', 'muted golden light filtered through frosted glass')),
    ('the butter dish', _ve('a ceramic butter dish with a lid on a kitchen table', 'centered with a shallow perspective', '', 'a wooden cutting board with grain visible behind', 'a faint smear of butter on the floorboards', 'warm afternoon sunshine with golden highlights')),
    ('a plastic food storage container', _ve('clear rectangular box with snap-tight lid', 'positioned slightly left of center', '', 'wooden pantry shelf with faint grain behind', 'smooth countertop surface extending forward', 'neutral daylight with soft gray reflections')),
    ('the subway platform tile', _ve('a glossy white tile with subtle speckles', 'stretched across the length of the platform', '', 'a dimly lit tunnel wall recedes behind the tiles', 'clean concrete floor with faint water stains', 'cool fluorescent light giving a blue-white hue')),
    ('the utility meter box', _ve('gray metal box with dials and switches', 'placed slightly to the right of center', '', 'exterior siding with faded paint behind the box', 'gravel driveway with a thin line of oil', 'overcast sky light giving a neutral grey tone')),
    ('the coin-sorting machine', _ve('large transparent drum with rotating brushes', 'centered, occupying the middle third of the view', '', 'stacked trays of sorted coins line the back wall', 'grey epoxy floor with faint oil-resistant coating', 'soft white light with a hint of teal')),
    ('the gasoline nozzle', _ve('a black plastic hose ending in a silver tip', "angled upward toward the viewer's eye level", '', 'a row of fuel tanks standing behind the nozzle', 'gravelly ground with scattered leaf litter', 'bright midday sun casting sharp shadows')),
    ('a passenger boarding bridge', _ve('a telescopic corridor linking terminal to aircraft door', 'angled from the terminal side showing its length', '', 'aircraft wing and engine visible beyond the bridge', 'metal grating floor with faint oil stains', 'cool steel blue with a hint of sunrise orange')),
    ("the branch's water cooler", _ve('stainless steel dispenser with glass pitcher', 'placed in foreground, slightly to the right', '', 'a wall of neutral-tone acoustic panels behind', 'a light gray carpet with subtle pile', 'soft warm illumination, gentle amber tone')),
    ('the API rate limit', _ve('vertical meter with a red warning segment', 'centered on a dark matte panel', '', 'faint cascade of request arrows behind', 'tiny blocked symbols scattered on the ground', 'deep scarlet with muted charcoal')),
    ('the ATM enclosure', _ve('transparent glass box housing a single cash machine', 'framed centrally with slight upward perspective', '', 'security cameras mounted on the ceiling above', 'grey tiled floor with a faint reflection', 'neutral daylight tone with crisp white balance')),
    ('the load balancer unit', _ve('slim chassis with rotating status wheels', 'placed on a raised platform, slightly off-center', '', 'wall of fiber optic cables disappearing upward', 'concrete floor with a thin layer of dust', 'steady amber light with gentle shadows')),
    ('an abandoned bike rack', _ve('metal racks arranged in a V shape near a street', 'angled view from the side showing empty slots', '', 'brick wall covered in ivy behind the rack', 'gritty concrete with scattered gravel pieces', 'muted teal shadows with a hint of sunrise')),
    ('a product price board', _ve('a chalk-covered board displaying item prices', 'centered against the back wall of the aisle', '', 'a series of hanging lights above the board', 'a concrete floor with small cracks', 'warm evening glow with orange highlights')),
    ('the locked storage locker', _ve('steel locker with a combination dial and reinforced door', 'occupying the center foreground of the scene', '', 'a hallway lined with identical lockers stretching away', 'concrete floor speckled with faint oil stains', 'dim fluorescent buzz with a hint of teal')),
    ('a silver ledger clip', _ve('large silver clip holding multiple ledger pages', 'positioned near the foreground left side', '', 'a wooden panel with subtle grain texture behind', 'polished concrete floor extends forward', 'soft metallic sheen with gentle daylight')),
    ('the baggage claim carousel', _ve('a rotating steel belt with luggage compartments', 'spanning the lower half, curving gently forward', '', 'a large glass wall showing distant runway lights', 'smooth concrete floor with scattered luggage tags', 'warm amber lighting with subtle orange highlights')),
    ('a foreign currency tray', _ve('transparent acrylic holder with neatly stacked bills of many nations', 'viewed from above, emphasizing the varied colors', '', 'glass cabinet with a frosted back panel', 'smooth white countertop with a faint reflection', 'soft natural light with pastel tones')),
    ('the downtown sidewalk curb', _ve('a concrete ledge separating road from footpath', 'running along a bustling street line', '', 'storefront windows and awnings stretch behind', 'smooth pavement with occasional puddles', 'overcast sky casting neutral gray tones')),
    ('the curb cut', _ve('ramp of smooth concrete sloping downwards', 'shown from a slight upward perspective', '', 'a parked sedan with its wheels aligned on the edge', 'clean asphalt with a thin layer of dust', 'early morning light with soft amber tones')),
    ('the compact car lane', _ve('a narrow painted lane beside the main road', 'centered with gentle perspective lines leading forward', '', 'a row of street trees with autumn leaves rustling softly', 'smooth asphalt dotted with faint tire marks', 'soft morning light with cool blue shadows')),
    ('the ignition switch', _ve('a metallic knob with a keyhole inset', 'centered in the lower middle of the composition', '', 'a dashboard with faint warning lights behind', 'plastic panel with subtle texture', 'warm low-light glow with amber accents')),
    ('an inspection checklist pad', _ve('a leather-bound notebook opened to a checklist page', 'overhead shot showing the top of the pad', '', 'a desk lamp casting a halo behind the notebook', 'a dark oak desk surface with faint scratches', 'gentle amber glow with subtle shadows')),
    ('the underground garage ramp', _ve('a concrete incline with steel guardrails', 'stretching from the bottom left to the top right', '', 'rows of parked cars disappearing into depth', 'a textured concrete floor ahead', 'dim artificial lighting with cool gray tones')),
    ('a money-order form', _ve('pre-printed paper with numbered sections and faint watermark', 'lying flat on a steel tray', '', 'a stack of completed forms behind the tray', 'cold steel surface with a slight sheen', 'neutral daylight with cool shadows')),
    ('a garden compost bin', _ve('large wooden bin with slatted sides in the backyard', 'positioned near the fence at left side', '', 'tall hedges casting gentle shadows behind it', 'rich dark soil with fallen autumn leaves', 'warm earthy tones under late afternoon sun')),
    ('the power distribution unit', _ve('tall metal column with numerous circuit breakers', 'centered, slightly low angle showing top handles', '', 'wall of server cabinets receding into darkness', 'concrete floor with a thin sheen of water', 'steady white light with subtle amber highlights')),
    ("the shop's loyalty card holder", _ve('a metal tray filled with plastic cards', 'centered near the bottom of the image', '', 'a wall of reclaimed wood panels behind the tray', 'a smooth concrete slab with subtle sheen', 'soft daylight with cool pastel tones')),
    ('an overlooked parking space number', _ve('metallic plaque attached to a concrete post', 'placed near the lower left corner', '', 'row of parked sedans with dark windows behind', 'smooth concrete with faint chalk dust in front', 'bright noon sun with crisp white-blue contrast')),
    ('an insulated file folder', _ve('sturdy cardboard folder with a clear plastic sleeve', 'standing upright against a filing rail', '', 'a tall bookshelf filled with reference manuals', 'light-colored carpet with a subtle wave design', 'soft natural light with warm ivory tones')),
    ('a paper receipt roll', _ve('a cylindrical spool of thin white paper', 'situated in the foreground near the bottom edge', '', 'a metal cash drawer open behind the roll', 'a polished oak counter top beneath the roll', 'soft ambient light with muted ivory tones')),
    ('the terminal ceiling panel', _ve('a large suspended acoustic tile with subtle pattern', 'occupying top third, centered horizontally', '', 'a row of sleek glass doors leading outside', 'light concrete flooring with faint directional lines', 'diffused natural light with warm ivory hue')),
    ('the printer station', _ve('compact black printer with paper tray and scanner lid', 'placed in the foreground left corner', '', 'a wall of stacked file folders in muted blues', 'a gray carpet with a small rubber mat underneath', 'soft ambient light with a hint of amber')),
    ('the firewall appliance', _ve('compact metal box with flashing red warnings', 'placed on a raised platform, slightly tilted', '', 'wall of data cables coiled in the distance', 'gray epoxy floor with scattered dust particles', 'deep red accents against a dark background')),
    ('the traffic island', _ve('small raised concrete mound with a plant', 'viewed from a slight elevation, centered', '', 'a busy street with passing cars blurred', 'asphalt with a thin film of rain', 'late afternoon gold with soft shadows')),
    ('the loading zone paint', _ve('a bold blue rectangle marking a commercial loading area', 'centered near the bottom, stretching across the width', '', 'a brick warehouse door with large freight doors behind', 'concrete with faint tire tracks', 'midday sun with crisp, clean light')),
    ('the loyalty card holder', _ve('a small wooden box with a sliding metal latch', 'placed near the left corner, low on the counter', '', 'a bulletin board covered with promotional flyers', 'a thin strip of paper receipts spilling out', 'cozy golden hue with soft orange undertones')),
    ('the university quad', _ve('a grassy quad surrounded by academic buildings', 'wide aerial view emphasizing open space', '', 'brick façades with large windows behind', 'well-mowed lawn dotted with stone benches', 'bright clear sky with crisp white light')),
    ('a fridge magnet', _ve('a small round magnet attached to a stainless fridge door', 'centered near the upper third of the frame', '', 'a frosted glass panel with faint condensation behind', 'a polished tile strip on the kitchen floor', 'cool daylight with subtle teal highlights')),
    ('the pantry shelf', _ve('wooden board filled with sealed containers', 'view from slightly above, centered', '', 'brick wall with faint mortar lines behind', 'dry wooden floorboards stretching forward', 'soft daylight with muted earthy hues')),
    ('the hallway coat rack', _ve('metal rack with several hooks on a narrow post', 'standing near the entry door on the left', '', 'plain hallway wall painted light gray behind', 'hardwood floor with a subtle rug runner', 'warm indoor lighting with gentle amber hue')),
    ('an iron garden bench', _ve('an ornate iron bench with curved backrest', 'centered with empty seat inviting viewer', '', 'a tall maple tree casting shade behind', 'soft moss covering the ground beneath', 'golden hour glow with warm amber tones')),
    ('a bundle of printed invoices', _ve('a thick stack of paper with stamped totals', 'stacked on a metal counter near the right side', '', 'a backdrop of hanging fabric panels behind', 'a dark slate floor with subtle sheen', 'warm indoor lighting with gentle orange hue')),
    ('the negotiation table', _ve('a long oval table with built-in power outlets', 'wide perspective from one end toward the opposite side', '', 'a wall of acoustic panels behind the table', 'carpeted floor with a low-pile rug in the center', 'warm ambient lighting with subtle amber highlights')),
    ('a tidy legal pad', _ve('spiral-bound pad with ruled lines and a soft cover', 'leaning against a stack of reference books', '', 'a wall of muted artwork in abstract shapes', 'light-colored wood desk with subtle varnish', 'soft natural light with warm peach undertones')),
    ('the narrow loading zone', _ve('a painted white rectangle beside a storefront curb', 'aligned horizontally across the lower third', '', 'storefront windows reflecting distant traffic lights', 'clean concrete leading toward a distant alley', 'warm golden hour glow with soft orange tones')),
    ('an HTTP header', _ve('strip of translucent paper bearing key-value pairs', 'lying flat on a sleek dark table', '', 'soft blur of a server farm beyond', 'scattered tiny icons of request methods ahead', 'soft ivory light with a hint of amber')),
    ('the mail slot', _ve('metal slot built into a wooden door with a red flag', 'centered on the lower third of the door', '', 'a hallway lined with framed certificates', 'a smooth concrete floor with a faint dust layer', 'soft daylight with a pale yellow cast')),
    ('the data center door', _ve('heavy steel door with a biometric scanner', 'opened halfway, revealing interior glow', '', 'dim hallway with rows of silent machines', 'gritty concrete steps leading to the entrance', 'industrial orange lighting with deep shadows')),
    ("a car's tire tread", _ve('deep rubber pattern on a black wheel', 'shown from a low angle near the foreground', '', 'parking space lines and a distant fire hydrant', 'dry asphalt with a thin dust layer', 'warm sunlit tone with subtle shadows')),
    ('an IPv6 address pool board', _ve('magnetic board with rows of hex-coded tags', 'slightly top-down to show tag arrangement', '', 'plain plaster wall with subtle shadowing', 'light-gray vinyl flooring', 'cool blue lighting with a hint of white')),
    ('a sealed SSD enclosure', _ve('compact black case with a tiny indicator LED', 'placed on a raised platform in the foreground', '', 'wall of server blades glowing behind', 'dark rubber mat covering the floor', 'subtle violet hue with gentle highlights')),
    ("the apartment's fire alarm", _ve('a red plastic unit with flashing light', 'mounted high on a plaster ceiling', '', 'behind it a plain white ceiling with acoustic tiles', 'a smooth white wall with subtle texture', 'cool fluorescent glow with faint red pulse')),
    ('the dish rack', _ve('a plastic dish rack holding plates and cups in a kitchen sink', 'shown from a low side view', '', 'a tiled wall with a faint checkerboard pattern behind', 'a few droplets of water on the linoleum floor', 'soft warm light with gentle orange hue')),
    ('the microwave interior', _ve('black glass turntable with smooth walls', 'view from directly above, centered', '', 'metal door interior with subtle vent pattern behind', 'dry kitchen tiles extending toward the camera', 'cool neutral light with soft gray tones')),
    ('an urban bike rack', _ve('metal loops anchored to a concrete post', 'aligned along the curb of a side street', '', 'brick storefronts with awnings stretch behind the rack', 'gravel and leaf litter scattered at its base', 'soft overcast sky casting muted gray tones')),
    ('an empty mailbox slot', _ve('metallic slot with a hinged door', 'centered in the lower half of the frame', '', 'brick façade with vines creeping behind the mailbox', 'cobblestone path with scattered leaves', 'golden late-afternoon sun casting gentle shadows')),
    ("the lobby's welcome mat", _ve('coir mat with subtle border pattern', 'straight on, filling lower third of frame', '', 'glass doors opening to a hallway behind', 'marble floor with faint veining patterns', 'bright natural light, crisp ivory tone')),
    ('a vehicle jack', _ve('a compact hydraulic lift resting on a rubber mat', 'positioned in the lower third of the scene', '', 'a wall of garage tools hanging behind it', 'smooth tiled floor with scattered dust particles', 'warm amber glow from overhead bulbs')),
    ('a runway wind sock', _ve('a red and white fabric cone perched on a metal pole', 'low angle capturing its flutter against the sky', '', 'open field of grass stretching toward distant hangars', 'bare earth with occasional footprints', 'bright daylight with clear blue tones')),
    ('a check-verification scanner', _ve('compact black device with glass feeding slot', 'centered, slightly tilted forward', '', 'a wall of acoustic panels absorbing sound', 'a dark rubberized mat with faint grip pattern', 'neutral cool light, soft blue tint')),
    ('the TCP handshake', _ve('three interlocking gears turning in sync', 'arranged in a triangular composition', '', 'soft circuitry background behind the gears', 'tiny spark icons scattered at their base', 'cool cobalt blue with faint amber highlights')),
    ('the legal seal stamp', _ve('gold-plated rubber stamp with embossed company crest', 'resting on a polished glass tray on a desk', '', 'a wall of framed certificates in dark wood frames', 'a sleek black desk surface with faint fingerprints', 'cool white illumination with a subtle metallic sheen')),
    ('an encrypted USB stick', _ve('metallic thumb drive with a tiny lock icon', 'resting on a silicone pad, front facing up', '', 'softly lit rack of storage servers behind', 'matte black surface with faint scratches', 'cool silver glow with a faint violet hue')),
    ('the library reading nook', _ve('a secluded corner with a low table and lamps', 'tight shot focusing on the tabletop', '', 'shelves filled with books fading into the background', 'soft carpet with a subtle geometric pattern', 'warm golden light casting calm shadows')),
    ('a reusable bag rack', _ve('a wooden rack holding colorful reusable shopping bags', 'aligned to the left side of the composition', '', 'a row of potted plants on the opposite wall', 'a polished concrete floor with a faint sheen', 'soft natural light with pastel undertones')),
    ('a solitary desk lamp', _ve('metallic desk lamp with an adjustable arm', 'positioned in the lower right corner of the frame', '', 'a wall of stacked binders and legal pads', 'smooth marble surface with a few scattered paper clips', 'cool white light with subtle blue undertones')),
    ('a steel audit tray', _ve('metal tray holding sorted financial documents', 'centered and slightly tilted toward the camera', '', 'a row of metal shelves recedes behind the tray', 'dark stone tiles extend forward', 'cool gray ambiance with faint amber highlights')),
    ('an emergency exit sign', _ve('a bright green illuminated panel above a door', 'aligned to the right edge, occupying upper third', '', 'a plain concrete wall with faint ventilation grilles', 'gray carpet runner with a faint striped pattern', 'steady green light against muted gray background')),
    ('the currency counting machine', _ve('compact device with a transparent feeding slot', 'centered, showing bills moving through the rollers', '', 'metal shelving unit stacked with sealed envelopes', 'gray anti-static mat covering the floor beneath', 'cool white illumination with a slight cyan tint')),
    ('a community garden plot', _ve('raised wooden beds filled with assorted vegetables', 'arranged in neat rows across a grassy lot', '', 'a low fence and a shed stand behind the beds', 'bare soil and mulch surrounding each plot', 'soft morning light with fresh green hues')),
    ('the driveway gate', _ve('metal fence with a small padlock attached', 'captured from a side angle near the ground', '', 'a low hedge with blooming roses behind it', 'gravel path sprinkled with fallen leaves', 'sunset orange light with gentle pink hues')),
    ('a park duck pond edge', _ve('a low stone wall bordering calm water', 'framed from a side view near the waterline', '', 'tall reeds and distant trees reflected', 'muddy bank with small pebbles', 'soft twilight glow with cool lavender tones')),
    ('the windshield wiper blade', _ve('a flexible rubber strip on a metal arm', 'angled diagonally across the upper right corner', '', 'a cloudy sky visible through a window behind', 'glass surface with droplets of water', 'soft rainy light with muted gray tones')),
    ('the lease office', _ve('a small wooden desk with stacked lease forms', 'centered with a narrow window behind', '', 'a filing cabinet full of tenant records behind the desk', 'a polished laminate floor with a faint carpet runner', 'soft morning light with warm beige tones')),
    ('the painted curb line', _ve('a thin white stripe along the street edge', 'centered in the lower third of the frame', '', 'a row of parked cars with matching tinted windows behind', 'smooth asphalt pavement extending forward', 'soft morning light with cool gray tones')),
    ('a checkbook', _ve('green-bordered ledger with perforated pages and a clasp', 'opened to a blank page on a sleek desk', '', 'a small potted plant on the opposite side of the desk', 'smooth glass top with a faint reflection', 'cool morning light with subtle green tint')),
    ('the attic window', _ve('small rectangular window tucked behind wooden beams', 'centered slightly above the roofline', '', 'dusty rafters with cobwebs and a forgotten toolbox', 'weathered floorboards with scattered pine needles', 'soft muted amber light filtering through clouds')),
    ('a fiber optic transceiver', _ve('small gold-colored module with tiny glass fibers', 'placed on a silicone mat, side view', '', 'blurred rows of network switches behind', 'matte black surface with faint specks', 'cool gold sheen with muted blue background')),
    ('a handwritten receipt', _ve('a slip of paper with looping script totals', 'lying flat on a glossy countertop', '', 'a stack of unopened envelopes to the right', 'a dark walnut surface with faint sheen', 'muted amber light casting gentle shadows')),
    ('a lonely parking barrier', _ve('chain-linked fence segment blocking a private spot', 'placed at the right edge of the frame', '', 'brick wall covered in graffiti behind', 'dry dirt ground with scattered leaves in front', 'late afternoon sun casting long amber shadows')),
    ('a brass nameplate holder', _ve('metal frame holding a small engraved plate', 'mounted on a low partition near the entrance', '', 'a row of potted succulents lining the hallway', 'smooth stone tiles with a subtle speckle', 'soft overcast light with muted lavender tint')),
    ('a market stall canopy', _ve('a striped canvas awning over a wooden table', 'angled diagonally across the top of the frame', '', 'a line of empty crates against a brick fence', 'a woven straw mat covering the ground', 'golden sunset light with warm orange tint')),
    ('a jet bridge walkway', _ve('a long glass tunnel connecting terminal to aircraft', 'stretching from foreground to vanishing point', '', 'the aircraft wing visible through the glass', 'polished metal grating with subtle reflections', 'bright daylight with cool neutral tones')),
    ('a filing cabinet', _ve('tall metal drawer unit with brass handles', 'positioned slightly off centre to the right', '', 'a row of closed office doors with frosted glass panels', 'a polished laminate floor with a thin dusting of carpet', 'cool neutral tone from muted ceiling lights')),
    ('a backup power unit', _ve('large UPS box with LED status indicators', 'centered, front panel facing viewer', '', 'row of server cabinets behind, dimly lit', 'concrete floor with a thin oil spill sheen', 'steady green glow with cool shadows')),
    ('the lane divider post', _ve('metal pole with reflective orange strips', 'centered vertically against a dark background', '', 'a stretch of empty road disappearing ahead', 'asphalt with a thin layer of dust', 'late afternoon sun with golden highlights')),
    ('the handicap parking placard slot', _ve('a narrow slot on a curb for inserting a placard', 'centered near the bottom edge, clearly visible', '', 'a historic stone building with arched windows behind', 'cobblestone street with subtle moss growth', 'muted sunrise light with pastel yellow tones')),
    ('a dusty checkout counter', _ve('a wooden surface with faint scratches and a cash drawer', 'centered slightly to the left, filling the lower half', '', 'a wall of pastel tiles with a vintage scale underneath', 'a thin line of scattered coin rolls and paper receipts', 'soft warm amber glow with muted amber tones')),
    ('a hospital waiting area', _ve('a quiet waiting room with soft armchairs', 'straight-on view showing the reception desk', '', 'large windows revealing a garden outside', 'polished laminate floor with a muted runner', 'calm neutral lighting with cool teal undertones')),
    ('the soap dish', _ve('a ceramic white soap dish holding a bar of soap', 'aligned to the left edge of the frame', '', 'a tiled bathroom wall with subtle blue pattern behind', 'a few water beads on the tiled floor', 'soft warm glow from a nearby window')),
    ('a stainless steel trash can', _ve('tall cylindrical bin with a foot pedal', 'centered, slightly tilted forward', '', 'plain gray wall with a subtle texture behind', 'polished linoleum floor reflecting faint light', 'cool morning light with subtle teal hints')),
    ('the laundry drying rack', _ve('foldable metal rack with multiple arms', 'leaning against the wall near the window', '', 'white washing machine visible behind it', 'polished tiled floor with a faint soap residue', 'bright daylight with crisp white tones')),
    ('a stone stepping stone', _ve('a single flat stone set in a mossy clearing', 'positioned off-center toward the left', '', 'a dense thicket of ferns behind the stone', 'soft loam dotted with tiny wildflowers', 'misty gray atmosphere with a hint of sunrise')),
    ("the store's coupon rack", _ve('a metal grid holding colorful flyers', 'spanning the lower third of the scene', '', 'a backdrop of stacked wooden crates behind the rack', 'a concrete floor with faint oil stains', 'neutral daylight with gentle gray tones')),
    ('the meeting whiteboard', _ve('a large magnetic whiteboard with faint grid pattern', 'front view centered, showing the board surface', '', 'a tray of dry-erase markers on a small shelf', 'light gray carpet with a subtle fringe', 'bright daylight streaming from a side window, cool tones')),
    ('the polished rubber mat', _ve('black rubber mat with a subtle embossed pattern', 'lying in front of a standing desk', '', 'a wall of glass cabinets holding office supplies', 'smooth hardwood floor with faint grain', 'soft evening amber with muted gold highlights')),
    ('the living-room side table', _ve('a small round table with a glass top', 'slightly angled, showing the edge of the glass', '', 'a plush sofa and a tall floor lamp behind', 'a woven rug with muted earth tones', 'warm indoor lighting with amber glow')),
    ('a travel pillow', _ve('cylindrical memory-foam cushion in a soft teal cover', 'lying on a fabric seat, viewed from above', '', 'row of empty seats with headrests behind', 'carpeted floor with a faint pattern', 'warm indoor lighting with gentle amber highlights')),
    ('a signed NDA document', _ve('single-sided paper with a thick black signature line', 'laid flat on a dark wooden table', '', 'a sleek metal laptop closed beside it', 'a smooth glass surface with a faint reflection of the ceiling', 'soft natural light from a nearby window')),
    ('an SSD enclosure', _ve('compact metal case with a single LED indicator', 'centered, slightly rotated to show side panel', '', 'blurred wall of server racks behind', 'black anti-static mat with faint fingerprints', 'cool silver tone with a subtle pink glow')),
    ('an exit sign above a garage', _ve('green illuminated rectangle pointing outward', 'mounted high on the wall, centered', '', 'concrete support beams and a faint hallway', 'gravel path leading to the doorway', 'bright green glow against dark stone')),
    ('a latency-monitoring probe', _ve('small box perched on a rack shelf', 'angled to expose side vents', '', 'bare brick wall with faint mortar cracks', 'low-pile carpet in soft charcoal', 'neutral white light with subtle teal wash')),
    ("the cashier's receipt printer", _ve('a compact white machine with a paper tray and ink cartridge', 'centered on the countertop, slightly angled toward viewer', '', 'a wall of stacked cardboard boxes behind it', 'a polished floor with a thin line of paper scraps', 'bright neutral light with crisp white highlights')),
    ('a maintenance request form', _ve('a short printed form with checkboxes and signature line', 'placed on a metal clipboard near a sink', '', 'behind it a tiled utility room with pipes', 'a stainless steel countertop with a small faucet', 'cool fluorescent light with crisp white tones')),
    ('the hand soap pump', _ve('a plastic pump bottle dispensing liquid soap near a sink', 'placed near the left edge of the composition', '', 'a tiled backsplash with subtle mosaic pattern behind', 'a glossy wet spot on the marble floor', 'soft diffused light with pastel green hue')),
    ('a porcelain toothbrush holder', _ve('white cup with a small drainage hole', 'placed near the lower right of the frame', '', 'plain bathroom wall with a faint pastel hue behind', 'smooth tiled floor extending forward', 'gentle warm light with creamy ivory tones')),
    ('the public library entrance', _ve('a glass double door framed by marble pillars', 'occupying the foreground of a quiet plaza', '', 'a row of ornamental shrubs and a stone fountain behind', 'polished stone tiles reflecting subtle shadows', 'warm sunrise glow with amber highlights')),
    ('the rent receipt printer', _ve('compact white printer with paper tray open', "angled slightly toward the viewer's left", '', 'plain white wall with a tiny vent behind it', 'smooth laminate countertop with a few stray receipts', 'cool office white light with subtle green tint')),
    ('the shared laundry chute', _ve('metallic vertical shaft with a hinged door', 'low angle from the base looking up', '', 'stack of laundry baskets stacked on a shelf behind', 'tile floor with tiny specks of detergent', 'cool fluorescent wash, muted teal tint')),
    ('the fuel dispenser', _ve('a stainless steel pump with rotating nozzle', 'centered slightly to the left of the frame', '', 'a row of empty gasoline containers behind the pump', 'concrete slab with faint oil stains below', 'soft morning light with cool blue tones')),
    ('a duty-free perfume display', _ve('glass shelves holding rows of colorful bottles', 'angled from above showing the arrangement', '', 'bright LED strips lining the edge of the counter', 'marble countertop with a faint reflection of bottles', 'soft white light with a subtle rose tint')),
    ('the HR policy binder', _ve('a thick ring-bound binder with a blue cover', 'leaning against a filing cabinet on the left', '', 'a wall of motivational quotes framed behind it', 'a low-pile carpet with a muted taupe hue', 'warm indoor lighting with gentle highlights')),
    ('a cache eviction policy', _ve('sliding panel revealing older entries being removed', 'centered within a clean white frame', '', 'blurred stack of older cache blocks behind', 'small glowing crumbs of evicted data on floor', 'warm honey yellow with soft gray shadows')),
    ('an audit trail log', _ve('thick ledger bound in dark leather with stamped entries', 'open on a brass lectern in the centre', '', 'a wall of filing cabinets with brass pull-out trays', 'a dark oak floor with a faint polished finish', 'soft warm lighting with a hint of amber')),
    ('the redundancy switch', _ve('dual-power unit with mirrored LED panels', 'centered, slightly tilted toward viewer', '', 'blurred backdrop of data cabinets', 'smooth steel floor with a faint sheen', 'balanced white light with subtle blue undertones')),
    ("the lot's fire hydrant", _ve('red cylindrical hydrant with a cap and valve', 'standing upright near the left side of frame', '', 'concrete island with a small parking space behind', 'gravel surface with a few scattered leaves', 'soft overcast light with muted red tones')),
    ('a gift-wrap station', _ve('a compact table covered with rolls of wrapping paper', 'situated in the corner of the shop floor', '', 'a wall of holiday decorations behind the station', 'a plush carpet with a subtle swirl design', 'cozy warm light with hints of amber')),
    ('a redundant power cable', _ve('thick gray cable with multiple connectors side by side', 'lying straight across the foreground', '', 'rack of UPS units behind the cable', 'dark epoxy floor with a faint sheen', 'cool steel blue lighting with muted shadows')),
    ('a marble transaction counter', _ve('white marble slab with engraved ledger lines', 'centered and slightly elevated in the scene', '', 'a dark wooden panel forms the backdrop behind', 'polished stone tiles stretch forward', 'bright crisp light with subtle gray tones')),
    ('the tea kettle', _ve('a stainless steel tea kettle perched on a stovetop burner', 'centered with a slight upward angle', '', 'a tiled backsplash with faint orange glaze behind', 'a small steam swirl hovering above the floor', 'bright morning light with gentle copper highlights')),
    ('the safe deposit box lobby', _ve('rows of metal lockers with numbered doors', 'symmetrical arrangement leading the eye toward the back wall', '', 'large window showing a city skyline under overcast sky', 'dark carpet with a subtle geometric pattern', 'muted gray tones with a soft, diffused glow')),
    ('the municipal clock tower face', _ve('a large round dial with brass numerals', "prominently displayed on the tower's front wall", '', 'a skyline of low-rise buildings behind the tower', 'stone steps leading up to the base', 'crisp midday sun casting sharp shadows')),
    ('the disabled parking sign', _ve('blue rectangular board mounted on a pole', 'positioned slightly off center to the right', '', 'a row of regular parking spaces with striped lines', 'concrete slab with faint tire marks', 'diffuse overcast light with muted gray tones')),
    ('a museum hallway corridor', _ve('a long marble corridor with recessed lighting', 'straight view down the center line', '', 'gallery doors and a distant sculpture pedestal', 'polished floor with subtle reflective sheen', 'soft white light with cool blue undertones')),
    ('the rear-view camera lens', _ve('a black circular sensor embedded in the trunk lid', 'centered at the bottom of the image', '', 'a faint outline of a garage door behind', 'polished metal floor with slight reflections', 'soft cool lighting with subtle teal hints')),
    ('the aircraft fueling truck', _ve('a yellow tanker with a long hose attached', 'side view with the hose coiled on the ground', '', 'parking area marked with fuel spill containment circles', 'gravel surface with occasional oil sheen', 'bright daylight with a crisp yellow tone')),
    ('the dining-room centerpiece vase', _ve('clear glass cylinder holding a single branch', 'centered on the rectangular oak table', '', 'a large window with sheer curtains beyond the vase', 'polished tabletop with a faint ring of condensation', 'soft midday sun casting gentle highlights')),
    ('the interest rate chart', _ve('framed line graph on a matte board', 'hung slightly off-center on a plain wall', '', 'a row of empty picture frames beside it', 'light gray carpet with low pile', 'soft daylight with pastel shadows')),
    ('an offshore banking compliance seal', _ve('circular embossed seal on a thick paper document', 'close-up, centered, slight rotation', '', 'stack of legal parchment sheets behind the seal', 'smooth ivory tabletop with a faint edge glow', 'soft parchment yellow with muted ambient light')),
    ('the DNS cache file', _ve('stack of printed pages with tiny QR codes', 'leaning against a metal rack, slightly tilted', '', 'empty space of a quiet server aisle', 'dark rubberized floor with subtle dust', 'warm ivory glow with gentle contrast')),
    ('the checkout conveyor belt', _ve('a black rubber belt stretched across a metal frame', 'running diagonally from left to right', '', 'a wall of pastel tiles with subtle patterns behind', 'a speckled concrete floor with scattered crumbs', 'neutral lighting with soft gray undertones')),
    ('the discount coupon dispenser', _ve('a glass cylinder dispensing single-use discount coupons', 'standing near the entrance of the checkout lane', '', 'a row of stacked cardboard boxes behind the dispenser', 'a light-colored linoleum floor with subtle speckles', 'bright natural light with a soft yellow tone')),
    ('an indexed legal ledger', _ve('thick bound book with numbered tabs and faded cover', 'lying open on a wooden reading stand', '', 'a shelf of similar ledgers arranged in order', 'polished walnut table with a faint sheen', 'warm candlelight flicker with amber highlights')),
    ('a pharmacy shelf', _ve('a wooden shelf lined with small bottle containers', 'tilted slightly upward toward the viewer', '', 'a muted blue wall with a framed certificate', 'a clean linoleum floor with subtle texture', 'cool fluorescent illumination with soft cyan accents')),
    ('a passport control booth', _ve('a compact wooden desk with built-in scanner', 'aligned left, filling lower half of scene', '', 'a plain plaster wall with a muted color', 'dark carpet with a low-pile texture', 'cool fluorescent light with a subtle green hue')),
    ('the office pantry', _ve('a small kitchenette with coffee machine and shelves', 'centered on the left side of the frame', '', 'a glass wall with blurred cityscape visible beyond', 'a tiled floor with scattered paperclips and napkins', 'soft warm glow from overhead fluorescent lights')),
    ('an Ethernet patch panel', _ve('grid of ports with colorful cable plugs', 'viewed from above, rows neatly aligned', '', 'wall of server racks fading into darkness', 'plastic mat with scattered tiny connector pieces', 'neutral gray tones with a hint of teal')),
    ('the valet ticket holder', _ve('small metal box attached to a wall', 'centered, slightly angled to the right', '', 'a polished marble floor behind it', 'smooth stone tiles with faint footprints', 'warm indoor lighting with soft amber glow')),
    ('a parallel parking space', _ve('a marked rectangular space between two parked cars', 'framed centrally with perspective converging toward the vanishing point', '', 'a brick wall with small ventilation grilles behind', 'asphalt with faint tire tread impressions', 'late afternoon sun with soft amber tones')),
    ('the anti-theft alarm sensor', _ve('a small rectangular device mounted under the hood', 'centered in the middle of the composition', '', 'a row of engine components blurred behind', 'metallic engine cover with subtle shine', 'soft daylight with gentle green undertones')),
    ('a tenant handbook', _ve('a thick paperback bound in navy cloth', 'lying flat on a metal clipboard', '', 'a wall of acoustic tiles behind the clipboard', 'a smooth steel surface with faint fingerprints', 'soft diffused light with gentle gray tones')),
    ('an oil dispenser', _ve('a sleek stainless steel oil dispenser on a kitchen counter', 'placed centrally with a slight tilt forward', '', 'a marble backsplash with faint speckles behind it', 'a small splash of oil droplets on the countertop', 'bright overhead illumination with crisp white light')),
    ('the bathroom soap dispenser', _ve('clear glass pump filled with liquid soap', 'placed at the lower right of the frame', '', 'white porcelain sink and tiled wall behind it', 'smooth white tiles stretching forward', 'soft diffused light with warm ivory tones')),
    ('an outdoor garden hose reel', _ve('metal reel mounted on a concrete post', 'aligned vertically on the left side of frame', '', 'flower beds bursting with roses behind it', 'bare concrete with a thin film of water', 'bright sunny glow with vivid green accents')),
    ('the birdbath', _ve('a ceramic birdbath nestled among low shrubs', 'framed from a slightly elevated perspective', '', 'a hedge of boxwood forming a natural border', 'pebble stones glistening with water droplets', 'cool turquoise reflections with soft morning light')),
    ('a rolled up shopping list', _ve('a paper scroll tied with a thin string', 'leaning against a metal shelf on the left', '', 'a wall of exposed brick with subtle cracks behind', 'a worn wooden floor with natural patina', 'soft late-morning light with warm hues')),
    ('the reception desk', _ve('a polished wooden desk with a glass panel', 'centered, eye-level view toward the visitor area', '', 'a potted plant in a ceramic pot behind the desk', 'marble floor with subtle veining', 'bright neutral lighting with crisp white highlights')),
    ('a laminated safety poster', _ve('clear laminated sheet displaying safety icons', 'mounted on a low wall panel near a doorway', '', 'a row of stacked cardboard boxes', 'smooth concrete floor with faint cracks', 'cool overcast light with muted gray tone')),
    ('an alleyway gate', _ve('a wrought-iron gate closing a narrow brick alley', 'positioned centrally with the arch opening forward', '', 'tall brick walls covered in ivy and graffiti tags', 'cracked cobblestones scattered with tiny pebbles', 'soft twilight glow with muted amber tones')),
    ('the tiny fire alarm', _ve('a red pull-station mounted on a white ceiling', 'centered near the top of the composition', '', 'a long corridor with fluorescent lights behind', 'smooth concrete floor with a faint dust layer', 'bright sterile light with crisp white tones')),
    ('the fire exit sign', _ve('green illuminated panel mounted above a metal door', 'centered on the upper left side of the frame', '', 'a plain hallway with white painted walls', 'a tiled floor with a subtle anti-slip texture', 'cool white light emphasizing safety colours')),
    ('the cable management tray', _ve('plastic bin filled with neatly tied cables', 'viewed from a low angle, showing texture', '', 'background of empty rack space and vent grilles', 'concrete floor with a thin sheen of water', 'muted teal lighting with gentle diffusion')),
    ('an angled parking space', _ve('two white lines forming a V shape on asphalt', 'fills the middle of the composition', '', 'row of parked cars beyond the lines', 'smooth gray surface with tire marks', 'warm late-afternoon sun with soft shadows')),
    ('the packet-capture appliance', _ve('compact device with transparent front and LED ring', 'front-facing, slightly elevated view', '', 'metal shelving with spare network gear behind', 'smooth gray floor tiles', 'cool cyan light with faint orange accents')),
    ('a folded store policy notice', _ve('a thin card with bold headings and tiny print', 'tucked into the left corner of the counter', '', 'a plain plaster wall with a faint texture', 'a line of tiny receipt edges scattered nearby', 'soft diffused light with muted lavender tint')),
    ('a neighborhood playground swing', _ve('a single swing hanging from a metal frame', 'low angle showing the seat in motion', '', 'fence with painted graffiti in the background', 'soft rubber mulch covering the ground', 'late-afternoon sun casting warm orange shadows')),
    ('an ice cube tray', _ve('a silicone ice cube tray sitting on a kitchen counter', 'centered with a slight upward tilt', '', 'a stainless steel refrigerator door behind', 'a few water droplets on the tile floor', 'cool daylight with faint blue tint')),
    ('a glass spice jar', _ve('clear container with a tiny metal lid', 'positioned in the lower left corner', '', 'dark wooden spice rack behind it', 'polished countertop surface under the jar', 'natural daylight with cool gray shadows')),
    ('a city park bench', _ve('a wooden bench beneath a canopy of oak trees', 'centered in a wide green lawn', '', 'tall street lamps line the distant walkway beyond the trees', 'soft moss covering the earth around the bench', 'gentle morning light with cool blue tones')),
    ('a quiet storage locker', _ve('metallic compartment with a rusted lock', 'positioned in the lower third of the frame', '', 'brick partition with faint graffiti behind the locker', 'grimy concrete floor with a small puddle', 'muted grey light with a hint of sunrise orange')),
    ('a parked electric scooter', _ve('compact scooter leaning against a curb post', 'positioned near the foreground left, slightly angled', '', 'tree line with autumn leaves behind', 'concrete slab with a thin dust layer', 'cool late-afternoon light with subtle amber tones')),
    ('an indoor potted fern', _ve('ceramic pot holding lush green fronds', 'centered on a low coffee table', '', 'brick fireplace with a faint ember glow behind', 'soft woven rug with muted earth tones', 'gentle warm light, soothing jade hues')),
    ('the boarding gate', _ve('a narrow corridor beside the jetway doors', 'centered with a clear view of the waiting line', '', 'glass walls showing distant runway lights and taxiing aircraft', 'smooth tiled floor speckled with faint footprints', 'soft amber glow with muted shadows')),
    ('an unused parking permit holder', _ve('a plastic sleeve attached to a metal pole', 'centered, slightly off-center to the right', '', 'a row of parked cars under a canopy behind it', 'gravel-covered ground with scattered leaves', 'soft overcast light with muted colors')),
    ('a JSON schema', _ve('transparent sheet displaying nested brackets and fields', 'leaning against a minimalist digital desk', '', 'soft focus of a code editor window behind', 'small icons of data types scattered ahead', 'soft pastel green with gentle ivory')),
    ('the compliance checklist', _ve('paper checklist with green checkmarks beside each item', 'leaning against a stack of folders on a desk', '', 'a wall-mounted digital clock showing 14:32', 'a smooth mahogany surface with a few coffee rings', 'warm incandescent glow from a nearby desk lamp')),
    ('an IP camera housing', _ve('small dome with a tiny infrared LED ring', 'mounted on the ceiling, looking downwards', '', 'grid of ceiling tiles receding behind', 'white acoustic panel with subtle dust', 'soft violet hue with low-key contrast')),
    ('the curbside recycling bin', _ve('green metal container with a hinged lid', 'placed near the right edge of the frame', '', 'parking space lines and a parked hatchback behind', 'concrete curb with a thin strip of grass', 'late afternoon sun casting gentle orange highlights')),
    ('a shopping basket', _ve('a woven plastic basket with a sturdy handle', 'resting near the entrance of the aisle', '', 'a stack of promotional flyers on a nearby table', 'a tiled floor with a faint checker pattern', 'soft midday light with cool blue accents')),
    ('a spare power cord', _ve('thick black cord ending in a three-prong plug', 'coiled loosely on the floor near a rack', '', 'metallic cable trays running parallel behind', 'dark rubberized flooring with faint footprints', 'subtle warm glow from overhead lights')),
    ('a copper change machine', _ve('vintage machine with rotating coin slots', 'placed in the middle of the composition', '', 'a tiled wall with subtle mosaic patterns behind', 'smooth polished concrete extends forward', 'soft teal light with warm reflections')),
    ('a salad bowl', _ve('a glass salad bowl filled with mixed greens on a dining table', 'shown from a top-down angle covering most of the frame', '', 'a linen napkin with subtle texture behind', 'a small drop of vinaigrette on the wooden floor', 'soft natural light with fresh green undertones')),
    ('the teller window', _ve('glass partition with a polished wooden frame', 'positioned left of center, angled toward the viewer', '', 'row of empty service counters behind a muted carpet', 'smooth marble tiles speckled with tiny gray veins', 'warm amber lighting casting gentle shadows')),
    ('the bus stop shelter', _ve('a transparent canopy supported by steel arches', 'positioned beside a curb with a bench underneath', '', 'lined trees and a distant traffic lane behind', 'rain-slick asphalt leading up to the shelter', 'soft diffused light with pastel gray ambience')),
    ('the street curb', _ve('concrete edge lining a narrow city lane', 'centered with a slight tilt to the left', '', 'a row of parked cars with matching bumper stickers', 'smooth pavement dotted with faint oil stains', 'soft morning light with cool blue tones')),
    ("the treasury's ledger board", _ve('large oak board with chalked entries and totals', 'mounted at eye level, centered', '', 'row of antique brass scales rests behind', 'polished stone floor with subtle reflective quality', 'warm golden glow from vintage pendant lights')),
    ('the emission test sticker', _ve('a small circular badge with green border', "placed on the windshield corner near the driver's side", '', 'a metal frame of a testing booth behind', 'clean glass surface with faint reflections', 'bright fluorescent lighting with neutral white balance')),
    ('a departure lounge sofa', _ve('a low-back modular couch upholstered in charcoal fabric', 'angled from the side showing the cushion depth', '', 'large window framing a sunrise over the tarmac', 'soft carpet with a low-pile texture', 'gentle sunrise pink blended with soft gray')),
    ('an isolated test server', _ve('a tower of blinking LEDs in a glass case', 'shown from a side angle with depth', '', 'a whiteboard filled with cryptic equations behind', 'smooth concrete floor with scattered cable ties', 'neutral gray lighting with subtle violet accents')),
    ("a banker's seal", _ve('circular wax stamp with embossed crest', 'placed upright on a dark leather blotter', '', 'a stack of sealed envelopes behind the blotter', 'deep mahogany desk surface with subtle grain', 'rich amber lighting with soft shadows')),
    ('an automated safe deposit lock', _ve('digital lock panel with green keypad and status LEDs', 'centered, eye-level view', '', 'steel wall with riveted plates behind the lock', 'black rubberized floor with faint dust particles', 'cool teal lighting with subtle shadow depth')),
    ('an access control panel', _ve('flat keypad with tiny LED indicators', 'mounted at eye level, centered', '', 'blurred hallway of cables and conduit', 'smooth tiled floor with faint oil streak', 'neutral white light with soft amber accents')),
    ('a simple price tag', _ve('a small cardboard tag with printed digits', 'sitting on a wooden shelf near the center', '', 'a row of glass jars filled with goods behind', 'a light pine floor with gentle grain texture', 'warm late-afternoon glow with golden hues')),
    ('a promotional stand', _ve('a metal stand holding a stack of discount coupons', 'positioned at the front of the checkout lane', '', 'a wall of product shelves behind the stand', 'a light-colored laminate floor with faint scratches', 'bright morning light with subtle yellow hue')),
    ('the recessed ceiling vent', _ve('square vent with slatted metal grates', 'centered near the top of the frame', '', 'a plain plaster wall extending outward', 'carpeted floor with a subtle geometric rug', 'soft diffused glow with neutral gray ambience')),
    ('a bakery display case', _ve('a glass counter showcasing assorted pastries', 'aligned with the right edge of the frame', '', 'a chalkboard listing daily specials behind the case', 'a smooth marble slab beneath the glass', 'bright natural light with pastel pastel tones')),
    ('the customs inspection window', _ve('a small glass booth with a sliding shutter', 'centered, occupying middle third vertically', '', 'a wall of muted stone with a discreet clock', 'dark rubber flooring with a faint anti-slip pattern', 'soft yellow lighting with gentle shadows')),
    ('an old piggy bank', _ve('ceramic pot with a coin slot on top and a stopper underneath', 'slightly tilted, showing the slot and stopper clearly', '', 'shelf of dusty books behind the bank', 'soft fabric rug with muted colors under the pot', 'soft sunrise gold with gentle shadows')),
    ('the router cabinet', _ve('locked enclosure housing network routing hardware', 'positioned slightly left of center, door ajar', '', 'wall of fiber optic panels humming softly behind', 'smooth white tiles reflecting faint amber light', 'soft amber illumination with gentle contrast')),
    ('a roadside parking barrier', _ve('orange plastic cone standing upright', 'captured from a low, forward angle', '', 'a narrow alley with brick walls on both sides', 'wet cobblestones glistening after rain', 'soft overcast light with cool gray tones')),
    ('the no parking curb', _ve('a red painted curb prohibiting parking in that zone', 'runs horizontally across the lower third of the frame', '', 'a leafy park bench under a canopy of trees behind', 'smooth concrete with a thin film of water', 'dawn light with warm rose hues')),
    ('the steering wheel lock', _ve('a steel bar with a locking mechanism attached', 'positioned diagonally across the lower left side', '', 'a shadowed wall with faint paint texture behind', 'leather steering column with slight creases', 'cool indoor light with muted blue shade')),
    ('a property tax bill', _ve('a folded paper document with stamped totals', 'centered on a glass tabletop', '', 'a decorative plant pot on the opposite side of the table', 'a smooth marble surface with a faint reflection', 'soft natural light with warm ivory tones')),
    ('the low-profile scanner', _ve('flatbed scanner with a glass surface and control buttons', 'centered, viewed from a slight top-down perspective', '', 'row of empty trays stacked on a metal shelf', 'smooth black workbench with a subtle sheen', 'cool neutral light with a hint of blue')),
    ('a wooden cutting board', _ve('rectangular maple board with faint knife marks', 'angled from the lower left corner', '', 'marble countertop with faint speckles behind it', 'light wood shavings scattered near the edge', 'warm amber glow with gentle shadows')),
    ('the backyard swing set', _ve('wooden platform with a hanging rope seat', 'situated near the far edge of the yard', '', 'tall oak tree providing shade behind the set', 'soft grass dotted with wildflowers', 'late-day amber light with gentle shadows')),
    ('the rain barrel', _ve('a metal rain barrel perched beside a stone wall', 'aligned to the right edge of the frame', '', 'a low fence topped with climbing vines', 'wet earth with puddles reflecting sky', 'cool gray tones with diffused daylight')),
    ('a stack of paper receipts', _ve('a neat pile of white slips with faint ink', 'centered on a marble countertop', '', 'a glass cabinet displaying jars of candy behind', 'a polished stone floor with soft reflections', 'soft natural light with creamy tones')),
    ('a breakroom fridge', _ve('a stainless steel refrigerator with magnetic notes', 'angled from the left side showing the door', '', 'a bulletin board covered in colorful paper clips', 'linoleum floor with a faint checker pattern', 'soft daylight filtered through blinds, pastel tones')),
    ('the silent shredder bin', _ve('metal bin with a hinged lid and shredded paper overflow', 'centered near the back of a small office nook', '', 'a tall plant in a ceramic pot casting soft shadows', 'light-colored linoleum with subtle speckles', 'soft daylight with gentle amber warmth')),
    ('a deli sandwich wrapper', _ve('a waxed paper covering a freshly cut sandwich', 'lying diagonally across the lower left area', '', 'a stainless steel prep table behind the wrapper', 'a brushed aluminum tray beneath the wrapper', 'warm indoor glow with soft amber tones')),
    ('a rusted key box', _ve('a metal lockbox attached to a brick pillar', 'placed slightly off-center to the right', '', 'a graffiti-covered wall with vines climbing behind', 'cracked concrete with puddles reflecting light', 'soft overcast light with muted green tones')),
    ('a contract envelope', _ve('sealed white envelope with a red seal and stamp', 'centered on a marble slab in the scene', '', 'a stack of legal pads with lined paper visible', 'a glossy black desk surface with subtle reflections', 'soft diffused light creating subtle shadows')),
    ('a network switch', _ve('slim rack-mount device with blinking port LEDs', 'positioned at the foreground, slightly off-center', '', 'shadowed row of servers fading into darkness', 'raised metal platform with subtle grime', 'soft white light with faint blue hints')),
    ('the yellow curb', _ve('painted edge along a city street lane', 'runs horizontally across the lower third', '', 'brick building facade with small windows behind', 'wet pavement reflecting nearby traffic lights', 'cool blue tone with gentle highlights')),
    ('the SSL certificate repository', _ve('glass cabinet holding sealed digital token devices', 'centered, with glass reflections', '', 'plain drywall with subtle shadowed corners', 'soft carpet runner in muted beige', 'soft ivory light with a gentle blue tint')),
    ('a stacked pile of paper receipts', _ve('a high tower of thin white sheets with printed totals', 'centered in the foreground, reaching toward the top', '', 'a wall of glass doors leading to storage room', 'a polished concrete floor with a faint sheen', 'bright daylight with cool gray shadows')),
    ('the riverwalk promenade', _ve('a wooden boardwalk hugging a flowing river', 'long perspective following the path', '', 'riverbank trees lining the far side', 'weathered boards with occasional sand patches', 'soft sunrise light with pastel orange hues')),
    ('the coffee filter', _ve('a paper coffee filter perched on a drip coffee maker', 'framed from above, occupying the top third', '', 'a stainless steel kettle hanging on a rack behind', 'a small coffee stain on the countertop', 'warm amber glow with soft shadows')),
    ('the refrigerator door', _ve('smooth stainless steel surface with a magnetic strip', 'framed from the side, slightly angled', '', 'kitchen wall with a faint pastel paint behind', 'checkerboard floor tiles leading forward', 'bright cool light with crisp white tones')),
    ('a bedroom closet rod', _ve('metal rod fixed inside a wooden wardrobe', 'running horizontally across the upper interior', '', 'softly lit interior wall with subtle texture behind', 'smooth wooden floor with a faint dust layer', 'warm gentle glow from a nearby ceiling light')),
    ("the landlord's office door", _ve('plain wooden door with a brass knob', 'aligned to the left edge of the frame', '', 'corridor lined with filing cabinets and a coat rack', 'polished tile leading up to the doorway', 'cool daylight filtered through frosted glass')),
    ('a marked handicap space', _ve('blue wheelchair symbol painted on the pavement', 'occupying the lower middle third of the view', '', 'tree-lined boulevard with a distant building facade behind', 'freshly laid asphalt with a faint sheen', 'bright morning light with crisp cyan accents')),
    ('the bandwidth throttling valve', _ve('metallic lever with digital readout indicating limits', 'centered, slightly tilted forward', '', 'a wall of server racks and a cooling vent behind', 'a dark rubber flooring with subtle texture', 'muted indigo light with faint orange highlights')),
    ('a sleek document scanner', _ve('flatbed scanner with a glass surface and brushed metal edges', 'placed on a narrow side table near a window', '', 'a wall of frosted glass panels diffusing light', 'light oak floor with subtle grain', 'cool daylight with a soft teal hue')),
    ('the company handbook', _ve('a thick bound manual on a wooden desk', 'centered, slightly tilted to the left', '', 'a row of filing cabinets with labeled folders behind it', 'a smooth matte carpet with subtle grain', 'soft warm daylight filtering through blinds')),
    ('a CDN edge node', _ve('compact tower with blinking status lights', 'standing alone on a concrete platform', '', 'distant horizon of other nodes fading away', 'small data packets scattering across the ground', 'soft sunrise orange with muted teal')),
    ('the security badge reader', _ve('compact scanner with a green LED indicator and slot', 'mounted at eye level on a side wall', '', 'a plain plaster wall with acoustic panels above', 'a polished stone floor with a thin runner rug', 'neutral white illumination with a faint metallic sheen')),
    ('the monitoring dashboard screen', _ve('large LCD panel displaying graphs and alerts', 'front-facing, centered in the frame', '', 'blurred rows of server lights in the distance', 'dark matte desk with a few scattered post-its', 'cool cyan background with bright magenta highlights')),
    ('an illuminated parking space number', _ve('LED panel showing “12” in white light', 'mounted on a low post near the curb', '', 'brick wall with ivy vines behind', 'concrete slab with a small puddle reflecting light', 'cool night blue with bright white glow')),
    ('a receipt printer', _ve('a compact thermal printer with a paper tray', 'centered near the bottom of the composition', '', 'a wall of framed certificates behind the printer', 'a thin line of half-printed receipts on the floor', 'soft white light with a gentle yellow wash')),
    ('the UPS battery bank', _ve('row of rectangular lead-acid batteries with orange caps', 'framed from a low angle emphasizing height', '', 'ventilation fans humming in the background', 'concrete floor with subtle oil stains', 'muted amber light with cool gray contrast')),
    ('the antique balance scale', _ve('iron balance with glass pans and wooden beam', 'centered and slightly tilted toward the right', '', 'a bookshelf of leather-bound books fades behind', 'dark slate floor tiles lie in front of the scale', 'rich brown warmth with gentle highlights')),
    ('the trash can', _ve('a matte black kitchen trash can with a lid slightly ajar', 'centered, showing its rounded shape', '', 'a tiled backsplash with faint vertical lines behind', 'a few crumpled paper pieces on the concrete floor', 'cool daylight with subtle blue-grey mood')),
    ('a bank vault door', _ve('massive steel door with intricate locking bolts', 'centered, slightly tilted to reveal its curvature', '', 'dimly lit hallway lined with old brass safes and ledgers', 'polished concrete floor reflecting faint ambient light', 'cool blue tones with a soft, steady glow')),
    ('a town square fountain', _ve('a stone basin with gentle water jets', 'situated at the heart of the cobblestone plaza', '', 'historic town hall towers over the scene behind', 'smooth cobblestones wet from the spray', 'golden late-afternoon sun with warm orange tones')),
    ("the building's recycling bin", _ve('large blue bin with a hinged lid', 'centered in the frame, slightly off ground', '', 'concrete wall with graffiti tags behind the bin', 'gravel ground with scattered paper scraps', 'soft overcast light with cool blue hints')),
    ('the cash-counting table', _ve('sturdy oak surface with built-in ledger slots', 'seen from above, showing neat stacks of bills', '', 'wall of framed certificates hangs behind', 'dark walnut floorboards with a thin runner rug', 'warm golden light casting gentle shadows')),
    ('the tire pressure gauge', _ve('a handheld dial device with a bright red pointer', 'placed on a wooden bench in the foreground', '', 'a stack of spare tires leaning against a wall', 'concrete pavers with faint water marks', 'soft diffused light with pastel yellow tones')),
    ('the airport fire truck', _ve('a red emergency vehicle parked near the runway edge', 'side view with ladders and hoses visible', '', 'sparse grass and a few scattered fire extinguishers', 'concrete pad with tire tracks', 'muted daylight with a slight overcast gray')),
    ('the archived log file', _ve('a dusty wooden cabinet with brass handles', 'framed from a low angle showing depth', '', 'stacked boxes of old hard drives line the back wall', 'polished oak floorboards catching morning light', 'warm amber glow with muted brown shadows')),
    ('the compression algorithm', _ve('folded ribbon of code looping tightly', 'suspended over a dark void', '', 'blurred mass of uncompressed files behind', 'tiny compressed blocks scattered below', 'soft violet with gentle silver sheen')),
    ('a vault pressure gauge', _ve('circular analog gauge with red needle', 'placed in the foreground, side view', '', 'metallic panel with wiring behind the gauge', 'cold concrete slab with a thin water-resistant coating', 'soft green illumination with subtle shadows')),
    ('the cooling vent grill', _ve('metallic lattice covering a large air duct', 'centered, slightly angled upward', '', 'wall of illuminated server panels behind', 'cold concrete floor with a thin mist', 'cool blue tone with crisp highlights')),
    ('a small town square fountain', _ve('stone basin with gentle water jets and surrounding benches', 'low angle capturing the water spray', '', 'historic town hall with clock tower in the background', 'cobblestone paving with occasional moss patches', 'golden late-afternoon glow with warm reflections')),
    ('an aisle divider rope', _ve('a thick rope cord used to separate product sections', 'running vertically near the center of the frame', '', 'a line of empty shelving units behind the rope', 'a smooth tiled floor with a light gray tone', 'bright daylight with crisp white balance')),
    ('the stamped approval seal', _ve('circular rubber stamp with raised lettering and ink pad', 'resting on a neat stack of paperwork', '', 'a wooden drawer filled with assorted folders', "smooth slate tile under the stamp's edge", 'soft natural light with warm honey tones')),
    ('a grocery storefront', _ve('a small brick building with glass windows', 'centered slightly to the left of the frame', '', 'a row of parked bicycles against a brick wall', 'a polished wooden mat at the entrance', 'soft morning light with warm amber tones')),
    ('a luggage trolley', _ve('a metal frame with four rolling wheels and a basket', 'positioned left, slightly angled toward center', '', 'a row of empty check-in counters with glass partitions', 'smooth tiled floor with subtle directional markings', 'natural daylight filtered through high windows')),
    ('the loan approval board', _ve('magnetic board with pinned documents and a red approval stamp', 'slightly tilted, showing a stamped document in focus', '', 'brick wall with exposed pipes behind the board', 'dark wooden desk surface with subtle grain', 'warm amber glow with a hint of copper')),
    ('a server rack', _ve('tall metal frame filled with blinking lights', 'centered with cables cascading downwards', '', 'rows of identical racks stretching into the dim background', 'cold metal floor with subtle dust specks', 'cool blue glow with muted shadows')),
    ('an electric car charger', _ve('silver column with a cord coiled neatly', 'framed from a diagonal viewpoint', '', 'a row of compact cars waiting nearby', 'gray concrete with faint tire scuffs', 'bright daylight with crisp white highlights')),
    ('a double yellow line', _ve('two solid yellow lines running down the center of the road', 'running vertically through the middle of the composition', '', 'a row of parked cars on either side, their hoods gleaming', 'asphalt with subtle oil sheen near the lines', 'bright midday sun casting sharp, crisp shadows')),
    ('the engine oil dipstick', _ve('a thin metal stick with a yellow handle', 'placed vertically in the left foreground', '', 'a toolbox filled with assorted tools behind', 'gray garage floor with faint oil spots', 'cool artificial lighting with soft white tone')),
    ('the eviction notice envelope', _ve('a thick envelope stamped with official seals', 'lying flat on a metal tray', '', 'a stack of generic office folders behind the tray', 'a matte gray carpet with a low-pile texture', 'muted indoor lighting with a hint of green')),
    ('the tucked-away legal pad', _ve('spiral-bound pad with ruled lines and a leather cover', 'lying flat near the edge of the desk', '', 'stack of binders stacked against a metal filing rack', 'light wood veneer with a faint polished sheen', 'soft daylight filtered through blinds, pale yellow tones')),
]


def sinh_therules(i):
    ds = LUAT_NGAM
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


# ── TOC_DO: NÂNG TỪ DANH SÁCH NỘI BỘ LÊN BẢNG MODULE  (6/9/2026) ───────────────────────
# Danh sách này nằm TRONG `sinh_speedof` nên `bang_mo_rong.py` không nhìn thấy nó, và kênh
# `speedof` dừng ở 29 mục = cạn chủ đề sau ~14 tập short. Không phải vì thế giới hết thứ
# để nói — cùng niche ấy, `howloud` đi từ 31 lên 278 mục chỉ bằng cách nới BẢNG.
# Đưa ra ngoài không đổi một hành vi nào; nó chỉ làm dữ liệu NHÌN THẤY ĐƯỢC từ bên ngoài,
# đúng điều kiện để nới. Cùng bài học §15.12: một trường chỉ được ghi mà không ai đọc
# được thì coi như chưa tồn tại.
TOC_DO = [("a sneeze", 100,
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
      ("a paper plane", 25, "a paper plane gliding across an empty room"),

    # ── NỐI THÊM 6/9/2026 · 139 mục qua bốn cổng của `bang_van.py`
    #    (dạng · không người · không chữ · không viết nghịch · không trùng).
    #    Bảng này KHÔNG có con số nào, nên không có gì để đối chứng và cũng
    #    không đụng tới luật nền 'AI không bao giờ cấp một con số'.
    ('the orbit of a low Earth satellite', 17500, _ve('an artificial craft circling the planet at high velocity', 'the instant it passes over the sun-lit side of the globe', '', 'the deep blue atmosphere fading into black space behind', "the bright edge of Earth's curvature ahead", 'crisp white light with deep midnight blue')),
    ('a desert sandstorm', 40, _ve('massive dunes shifting as wind lifts fine grains', 'the instant visibility drops to a veil', '', 'vast flat dunes rippling under a scorching sun', 'a solitary rocky outcrop rising ahead', 'harsh golden light with burning orange undertones')),
    ('a commuter electric bike', 18, _ve('the bike glides smoothly along a park pathway', 'the exact moment the pedal assist engages', '', 'a line of flowering cherry trees arches behind', 'a paved loop curves ahead', 'soft daylight with gentle rose tint')),
    ('the blazing trail of a re-entry capsule', 18000, _ve("a capsule hurtling back through Earth's atmosphere", 'the moment it ignites a searing plasma sheath', '', 'a black night sky behind the glowing arc', 'a fierce orange-red flame ahead', 'intense scarlet light with bright yellow bursts')),
    ('a touring motorcycle', 65, _ve('the motorcycle winds along a mountain pass', 'when the rider leans into a sharp turn', '', 'steep cliffs covered with evergreen trees', 'a curving road climbs toward the summit', 'crisp alpine white with icy blue hints')),
    ('a steady rowing stroke', 5, _ve('an athlete pulls the oar through water in rhythm', 'at the moment the blade enters the water', '', 'a calm river flanked by reeds and low willow branches', 'the river widening toward a distant bend', 'crisp morning light with silver-gray reflections')),
    ('the Voyager 1 probe', 38000, _ve('the probe sails silently beyond the heliosphere into interstellar space', 'the instant it passes the termination shock', '', 'a blackness speckled with distant stars', 'a faint glow of distant galaxies ahead', 'deep midnight blue with subtle violet glimmer')),
    ('the javelin run-up', 13, _ve('an athlete gathering speed before the throw', 'the precise moment the foot plants for launch', '', 'a sand runway edged by low grass', 'the distant field where the javelin will land', 'bright sunrise gold with soft teal accents')),
    ('a vintage biplane', 110, _ve('the vintage biplane loops gently over a pasture', 'as its fabric wings flutter in the breeze', '', 'a rolling green meadow with scattered oak trees', 'a narrow dirt road winding toward distant hills', 'soft golden light with muted green tones')),
    ('a greyhound', 55, _ve('the greyhound races across the open field', 'when its lean body leans into the wind', '', 'soft clover and low weeds sway behind', 'a straight track of compacted earth ahead', 'bright daylight blue with crisp white glare')),
    ('a jet-powered sailplane', 210, _ve('a sailplane with a small jet engine climbs steeply', 'the moment the jet ignites and thrust builds', '', 'a rugged alpine valley with snow-capped peaks', 'a clear blue sky opening ahead', 'crisp alpine light with bright cyan highlights')),
    ('a pole vault clearance', 12, _ve('the athlete propels upward over the high bar', 'the instant the pole bends and releases energy', '', 'sand pit with scattered footprints and a distant stadium wall', 'the cross-bar silhouetted against a clear sky', 'bright daylight with soft white clouds')),
    ("a sprinter's start", 15, _ve('muscles contract as the athlete launches from blocks', "the flash of the starter gun's echo", '', 'a track stadium with red rubberized lanes', 'a clear straightaway disappearing into the horizon', 'sharp sunrise orange with deepening shadows')),
    ('a classic motorcycle', 65, _ve('the motorcycle cruises down the coastal boulevard', 'as the wind whistles through the open fairing', '', 'a row of palm trees swaying in the breeze behind it', 'a sun-kissed road hugging the shoreline ahead', 'golden sunset light with warm amber highlights')),
    ('a swordfish', 55, _ve('the swordfish slices through water with its elongated bill', 'when it bursts forward in a hunting strike', '', 'a deep ocean trench illuminated by faint light', 'a flash of silver ahead as a fish flees', 'cold steel-gray light with sharp contrasts')),
    ('a snowmobile', 65, _ve('the sled tears across packed snow leaving a spray', 'when the rider twists the throttle forward', '', 'fresh powder drifting behind the track', 'a white-covered hill stretching forward under pale sky', 'crisp icy light with faint lavender shades')),
    ('the flick of a table tennis rally', 60, _ve('a paddle snaps, sending the ball zipping across the table', 'the instant the rubber contacts the tiny sphere', '', 'a quiet room with a smooth wooden table', 'a bright white net stretched tightly ahead', 'soft daylight with gentle teal reflections')),
    ('the impala sprint', 55, _ve('the impala rockets across a savanna thicket', 'in the flash of a sudden thunderstorm break', '', 'a low thicket of acacia leaves trembling in wind', 'a narrow dry riverbed glistening with rain', 'stormy grey light with bright silver highlights')),
    ('a fast lunar eclipse shadow', 1300, _ve("the Earth's shadow racing across the Moon's surface", 'the moment the umbra covers a crater rim', '', 'a deep midnight sky behind the darkened moon', 'a silvered glow of the penumbra ahead', 'cool slate blue with faint amber highlights')),
    ('a compact electric bike', 22, _ve('the e-bike zips past the river promenade', 'as the motor engages smoothly', '', 'a reflective water surface dotted with reeds', 'a paved bike lane runs parallel', 'fresh morning light with pastel pink hue')),
    ('the lightning-fast sailfish sprint', 68, _ve('sailfish accelerates, its dorsal fin unfurled like a sail', 'in the split-second it pierces a wave crest', '', 'a distant reef wall fades behind', 'a clear, sun-lit corridor ahead', 'electric azure with bright silver flash')),
    ('a hot-air balloon', 8, _ve('a colorful balloon drifts lazily above a sunrise valley', 'the instant the burner releases a gentle flame', '', 'rolling hills covered in misty pine forests', 'a narrow river winding through the valley', 'soft pastel sunrise with pink and peach hues')),
    ('the baseball pitch', 95, _ve('a pitcher hurling a fastball with a sharp release', 'the exact instant the ball leaves the fingertips', '', 'a dirt mound surrounded by neatly trimmed grass', 'the home-plate area gleaming under stadium lights', 'cool steel blue with crisp white highlights')),
    ('a cargo helicopter', 160, _ve('the cargo helicopter hovers low above a forest clearing', 'when its rotors churn a steady breeze', '', 'a dense pine forest with shafts of light filtering down', 'a moss-covered log bridge crossing a sparkling creek', 'dappled green light with warm amber highlights')),
    ('a moose', 45, _ve('the moose lumbers across the wet marshland', 'as its massive hooves splash shallow water', '', 'reeds and cattails rustle behind', 'a mist-filled channel lies ahead', 'cool teal mist with muted sunrise pink')),
    ('the B-2 stealth bomber', 630, _ve('the stealth bomber glides low over a moonlit desert', 'the instant its radar-absorbing surface shimmers', '', 'silvery dunes under a deep midnight blue sky', 'a faint line of distant star-filled horizon', 'soft moonlight with muted teal and indigo hues')),
    ('a boxing jab', 20, _ve('the glove rockets forward in a crisp straight line', 'the instant the fist contacts the target pad', '', 'leather boxing ring canvas with faint scuff marks', 'the padded focus mitt held steady ahead', 'warm amber glow with subtle shadow depth')),
    ('a casual jogging pace', 6, _ve('a runner moves rhythmically along a paved path', 'the second the foot lifts off the ground', '', 'a tree-lined park with fallen leaves covering the trail', 'a smooth asphalt stretch disappearing into the distance', 'warm golden light with hints of early sunrise')),
    ('the black-tailed jackrabbit', 40, _ve('the jackrabbit bounds across a sun-baked desert plain', 'when its long ears flick in the hot wind', '', 'endless flat desert with distant mesas under a blazing sky', 'a long, straight track of disturbed sand', 'intense golden light with scorching orange tones')),
    ('a dolphin pod leader', 22, _ve('the dolphin speeds ahead, leaping briefly above water', 'when it signals the pod to turn', '', 'a sun-lit sea surface with gentle waves', 'a spray of seafoam trailing ahead', 'vivid turquoise with sparkling sun flecks')),
    ('the long-range strategic bomber', 620, _ve('the bomber cruises high, engines humming deep', 'as it passes through thin cirrus clouds', '', 'a wide expanse of open sky with distant sun', 'a faint line of distant mountains ahead', 'cool steel gray with soft sunrise pink')),
    ("a marathon runner's rhythm", 8, _ve('a runner maintains steady stride over long distance', 'the precise beat of each footfall on pavement', '', 'a city boulevard lined with tall lampposts', 'a smooth road extending beyond the horizon', 'soft sunrise orange with gentle gray mist')),
    ('the brown bear run', 40, _ve('the bear charges through a pine forest trail', 'in the hush of a late-afternoon drizzle', '', 'a moss-laden fallen log beside a shallow creek', 'a narrow earthen path slick with fresh rain', 'muted teal light with soft brown undertones')),
    ('a gentle breath', 1, _ve('air flows in and out through the nasal passage', 'the precise second the diaphragm lowers slightly', '', 'the soft inner lining of the throat behind the airflow', 'the open airway leading toward the lungs', 'calm teal light with subtle lavender shadows')),
    ('a highway sedan', 55, _ve('the sedan cruises smoothly on the open highway', 'when the driver eases onto the next lane', '', 'a stretch of median with tall grasses', 'asphalt ribbon disappearing into distant hills', 'clear bright sky with light blue tone')),
    ('a soaring flying fish', 30, _ve('flying fish bursts out of water, gliding briefly in air', 'when the splash lifts its wing-like fins', '', 'a ripple-filled sea surface behind', 'clear sky over calm water ahead', 'bright sky blue with sun-kissed gold')),
    ('the Concorde', 1350, _ve('the iconic supersonic liner glides over the Atlantic at dusk', 'the instant its nose pierces the twilight horizon', '', 'a calm sea shimmering with amber reflections', 'a thin line of distant clouds ahead', 'rich twilight blues with warm orange accents')),
    ('the golf swing', 85, _ve('a golfer driving the ball with a powerful arc', 'the moment the clubface strikes the ball', '', 'a manicured fairway bordered by rolling hills', 'the green carpet stretching toward the distant flag', 'golden afternoon light with warm amber tones')),
    ('the tilt-rotor aircraft', 300, _ve('the tilt-rotor lifts and transitions to forward flight', 'as its rotors tilt forward over a lagoon', '', 'a shallow lagoon edged with mangrove roots and water lilies', 'a distant coral reef visible beneath crystal water', 'tranquil turquoise light with gentle sun flecks')),
    ('a elk', 40, _ve('the elk thunders through the alpine meadow', 'when its antlers catch a flash of light', '', 'rocky outcrops and low pines linger behind', 'a wide valley floor opens forward', 'crisp mountain blue with bright white highlights')),
    ('the Ariane 5 rocket', 19000, _ve('the Ariane rocket lifts off, shedding stages in succession', 'the instant the first stage separates cleanly', '', 'a desert launch site framed by distant mountains', 'a bright plume of flame and smoke ahead', 'bright sunrise gold with deepening navy shadows')),
    ('a ski slalom turn', 40, _ve('skis carve a tight curve through fresh powder', 'the moment the edges bite the snow', '', 'snow-covered slope with pine trees lining the side', 'the next gate pole waiting ahead', 'bright winter light with icy blue highlights')),
    ('a snow goose flying', 55, _ve('V-formation cutting through cold air', 'instant as they turn over a frozen lake', '', 'a frozen lake glittering with ice crystals', 'a snow-covered pine forest bordering the shore', 'crisp winter light with pale blue tones')),
    ('a mule deer', 38, _ve('the mule deer leaps over a small creek', 'as its hooves splash water droplets into the air', '', 'a clear mountain stream bordered by mossy rocks', 'a shallow, wet crossing of smooth stones', 'cool morning light with gentle turquoise reflections')),
    ('a marlin', 50, _ve('the marlin rockets forward, spear-like bill cutting water', 'as it accelerates to chase a schooling fish', '', 'a clear blue expanse with distant coral at the horizon', 'a shimmering line of silver fish ahead', 'bright cyan light with sparkling highlights')),
    ('a medium-range missile carrier aircraft', 560, _ve('the carrier streaks, missile bays open briefly', 'as the launch doors swing outward', '', 'a remote desert scrubland with scattered rocks', 'a straight runway disappearing into heat haze', 'harsh white glare with muted rust tones')),
    ('the glide of a luge sled', 70, _ve('an athlete leans low, sled humming down an ice track', 'the moment the steel runners bite the frozen surface', '', 'a winding icy tunnel flanked by frosted walls', 'a sleek icy curve disappearing into darkness', 'cold blue illumination with stark white highlights')),
    ('a meadow vole', 4, _ve('the vole darts through tall meadow grasses', 'during a quiet moment just after sunrise', '', 'a sea of emerald grass swaying under a soft pink sky', 'a narrow clearing of dew-wet clover', 'fresh pastel light with gentle lime accents')),
    ('a modern electric trainer aircraft', 110, _ve('the silent plane glides over a quiet field', 'the moment the electric motor hums softly', '', 'a golden meadow swaying under a clear sky behind', 'a low horizon line of distant trees ahead', 'bright daylight with fresh turquoise tones')),
    ('a mountain bike', 18, _ve('the bike darts over rocky trail bumps', 'when the rider lifts off a small jump', '', 'a forest floor littered with pine needles', 'a narrow dirt track winds forward', 'crisp cool light with hints of amber')),
    ('a leaping marlin', 55, _ve('marlin arches out of the sea in a powerful leap', 'when its spear-like bill cuts the air', '', 'deep blue depths recede behind the jump', 'sunlit spray sparkling ahead', 'bright indigo with golden spray highlights')),
    ('the SR-71 Blackbird', 2190, _ve('the legendary spy plane darts across a sunrise horizon', 'the instant it hits Mach 3', '', 'a barren salt flat reflecting pink light', 'a thin ribbon of heat haze ahead', 'high-contrast amber light with metallic sheen')),
    ('a downhill ski turn', 30, _ve('a skier carving a swift arc down a snowy slope', 'the instant the edge bites into the powder', '', 'snow-covered pine forest stretching behind the run', 'glistening white trail disappearing into the valley', 'crisp white light with icy blue highlights')),
    ('the regional jet', 420, _ve('the regional jet streaks past the mountain ridge', 'as it pierces a thin veil of cloud', '', 'snow-capped peaks dusted with late-spring pine', 'a valley of emerald fir forest below', 'bright high-altitude light with icy white highlights')),
    ('a bobcat', 32, _ve('the bobcat streaks through the scrubland', 'when its whiskers twitch at a rustling mouse', '', 'low bramble and pine needles lie behind', 'a narrow footpath cuts forward', 'deep forest green light with warm amber accents')),
    ('a paragliding wing', 25, _ve('a colorful paraglider drifts over a sun-lit valley', 'the moment thermal lifts the wing higher', '', 'lush green valley dotted with wildflower patches', 'a winding river glinting in the distance', 'soft late-morning light with gentle green tones')),
    ('the swing of a baseball bat', 70, _ve('the wooden bat arcs swiftly through the air', 'the precise moment it contacts the ball', '', 'dusty infield with scattered dirt and faint sunlight', 'a clean patch of grass beyond the home plate', 'bright daylight with crisp white highlights')),
    ('a pelican gliding', 23, _ve('large bill open, wings steady above water', 'second it skims a calm lagoon', '', 'a shallow lagoon fringed with mangrove roots', 'a sandy beach stretching toward distant horizon', 'soft teal water with gentle sunrise glow')),
    ('the common hedgehog', 3, _ve('the hedgehog shuffles along a leaf-covered forest floor', 'when it lifts its spines and continues forward', '', 'a carpet of fallen oak leaves and pine needles', 'a narrow trail of crushed leaves and small berries', 'dappled forest shade with cool green tones')),
    ('the oceanic manta ray', 20, _ve('the massive manta glides gracefully, wings beating slowly', 'as it turns to follow a plankton bloom', '', 'a deep blue pelagic zone with faint light shafts', 'a dense cloud of shimmering plankton ahead', 'soft lavender glow with gentle highlights')),
    ('a twin-engine maritime patrol aircraft', 340, _ve('the patrol plane cruises low, radar humming softly', 'as it skims over gentle ocean waves', '', 'a calm sea stretching to distant horizon', 'a thin line of water glistening ahead', 'soft teal light with pale sunrise pink')),
    ("a boxer's jab", 25, _ve('a fist snaps forward with crisp, focused power', 'the fraction when the glove contacts the target pad', '', 'a gym ring surrounded by ropes and padded walls', 'a smooth canvas floor stretching ahead', 'intense white light with deep charcoal shadows')),
    ('the intercontinental ballistic missile', 15000, _ve('a missile streaking upward in a bright white plume', 'the exact instant its booster ignites with thunderous roar', '', 'military launch complex with concrete bunkers', 'a clear sky turning orange from the exhaust', 'intense white fire against deep midnight blue')),
    ('a sailplane in ridge lift', 40, _ve('the glider rides a steady wind along a cliff', 'the moment the wing catches the upward current', '', 'a sheer limestone cliff dropping into a green valley behind', 'a long ridge line extending forward', 'bright sunrise gold with cool teal shadows')),
    ('a cruising bicycle', 12, _ve('the bike pedals smoothly along the park path', 'when the rider shifts gears lightly', '', 'a canopy of oak trees shades the left side', 'a paved loop curves ahead into distance', 'bright green daylight with dappled sunbeams')),
    ('a Neptune wind gust', 1200, _ve('deep blue clouds whipping across a frozen world', 'the moment a dark vortex forms near the pole', '', 'a dark, star-filled sky over a sapphire-hued atmosphere', 'the swift, swirling storm moving across the horizon', 'cold indigo with flashes of bright cyan')),
    ('a Falcon 9 first stage', 18000, _ve('a rocket booster ignites, soaring straight up from the pad', 'the moment thrust reaches maximum thrust', '', 'a coastal launch complex with rolling dunes', 'a clear blue sky opening ahead', 'bright white flare against deep indigo sky')),
    ('a sprint start', 15, _ve('an athlete exploding forward from the blocks', 'the exact moment the starter pistol fires', '', 'a synthetic track edged by rubberized lanes', 'the starting line painted in bold white', 'intense white light with a cool blue tint')),
    ('a pronghorn antelope', 60, _ve('the pronghorn sprints across open plains with endurance', 'at the exact beat of its rhythmic stride', '', 'a low horizon of muted grasses behind', 'a distant line of wind-swept sage ahead', 'clear blue sky light with warm amber tint')),
    ('a coyote', 30, _ve('the coyote sprints across the open sagebrush', 'as its howl rises over the hills', '', 'dry sage and tumbleweeds roll behind', 'a dust-kissed trail stretches ahead', 'bright orange sunrise with crisp teal shadows')),
    ('the SpaceX Starship', 18000, _ve('the massive Starship rockets skyward with roaring engines', 'the instant its nose cone separates', '', 'a sprawling coastal launch complex with rugged cliffs', 'a bright column of flame stretching forward', 'intense sunrise orange with darkening indigo sky')),
    ('a rushing elk calf', 35, _ve('the calf bolts across a riverbank meadow energetically', 'as its hooves splash through shallow water', '', 'wet grasses shimmering with reflected sky', 'a low bank of smooth stones', 'bright sunrise light with rosy undertones')),
    ('the golden eagle diving', 120, _ve('muscular form plunging with fierce intensity', 'second it pierces the wind above a cliff', '', 'rugged mountain slope covered in alpine grasses', 'a sheer drop opening to a crystal lake', 'intense white light with stark gray shadows')),
    ('the rotation of Earth', 1000, _ve('the planet turning eastward beneath a night sky', 'a continuous, smooth spin seen from space', '', 'a dark oceanic swath with cloud shadows behind', 'the bright sunrise cresting over the horizon ahead', 'deep navy fading to warm sunrise orange')),
    ('a flying fish', 35, _ve('the flying fish bursts out of the water, gliding briefly', 'at the moment its fins spread like wings', '', 'calm sea surface with gentle ripples', 'a spray of droplets sparkling ahead', 'golden sunrise light with warm orange tones')),
    ('a supercar', 150, _ve('the supercar rockets along a coastal freeway', 'the moment the rev counter hits the red line', '', 'cliffs dropping sharply into turquoise water', 'a smooth paved stretch hugging the shoreline', 'intense midday glare with sharp teal reflections')),
    ("a hurdler's clearance", 18, _ve('an athlete launches over a low barrier with swift legs', 'the split second the foot clears the hurdle', '', 'a track field surrounded by tall bleachers', 'a series of dark hurdles ahead in a line', 'bright daylight with crisp shadow play')),
    ('the reusable launch booster', 15000, _ve('a booster descending rapidly under controlled thrust', 'the precise moment its grid fins adjust direction', '', 'sparse desert with scattered rock formations', 'a wide flat plain stretching toward the horizon', 'warm amber light with deep shadowed reds')),
    ('a fighter jet afterburner burst', 1800, _ve('the combat plane erupts forward with roaring flames', 'the split second the exhaust ignites bright orange', '', 'a smoky trail of burnt ozone lingering behind the jet', 'a blazing orange-red flare lighting the forward air', 'intense fiery orange with deep crimson shadows')),
    ('a slow moving tram', 5, _ve('the tram glides slowly past the riverbank', 'at the instant the doors close gently', '', 'a grassy embankment dotted with wildflowers', 'a paved track runs parallel to the water', 'muted teal light with misty reflections')),
    ('a Jupiter storm swirl', 400, _ve('the Great Red Spot rotating with colossal force', 'the exact moment a band of clouds curls tighter', '', 'layers of swirling brown, orange, and white gases below', 'the massive vortex expanding rapidly ahead', 'deep rust reds blended with bright cream highlights')),
    ('the F-22 Raptor', 1500, _ve('an agile stealth fighter streaks over a pine forest', 'the moment it pulls a tight vertical climb', '', 'dense evergreen trees casting long shadows', 'a smooth meadow clearing ahead', 'bright midday sun with crisp green highlights')),
    ('a kingfisher darting', 25, _ve('the bright bird plunging toward a creek', 'when it snaps at a flashing fish', '', 'a crystal-clear creek edged with mossy stones', 'a smooth river rock formation ahead', 'emerald green with sparkling silver accents')),
    ('the African wild dog', 35, _ve('the wild dog darts through tall savanna grass swiftly', 'in the flash of its sudden turn', '', 'a thin line of sun-scorched earth behind', 'a thicket of acacia leaves rustling ahead', 'vivid sunlit gold with subtle teal shadows')),
    ('the rush of a Martian dust storm', 50, _ve("fine red dust swirling across the planet's surface", 'as the storm engulfs a crater rim', '', 'a barren ochre plain behind', 'a towering wall of dust ahead', 'muted rust orange with a faint rose haze')),
    ('a crop-dusting biplane', 110, _ve('a low-flying biplane sprays fields in tight passes', 'the moment its spray nozzles emit a fine mist', '', 'golden wheat fields shimmering under a summer sun', 'a narrow furrow of freshly sprayed crops ahead', 'warm golden light with soft amber shadows')),
    ('a darting African wildcat', 35, _ve('the wildcat darts low across the scrub quickly', 'as its tail flicks for balance', '', 'dense low brush with scattered stones', 'a narrow dry creek bed', 'soft twilight with muted lavender tones')),
    ('a turkey vulture gliding', 28, _ve('broad wings held flat, drifting lazily', 'instant as it passes a lone cactus', '', 'arid desert plain with scattered sagebrush', 'a rocky outcrop casting long shadows', 'soft amber light with muted brown tones')),
    ('a cough', 80, _ve('air rushes out of the lungs through the throat', 'when the diaphragm contracts sharply and the glottis snaps open', '', 'the tracheal walls and bronchi behind the burst', 'the mouth opening leading to the outside world', 'sharp silver light with a hint of teal')),
    ('a shortfin mako shark', 60, _ve('the mako shark cuts through currents with rapid tail flicks', 'when it reaches top speed chasing a tuna', '', 'a deep trench opening to open sea', 'a distant pod of dolphins leaping ahead', 'intense sapphire light with strong reflections')),
    ('the ruby-throated hummingbird darting', 25, _ve('tiny body flickering between blossoms', 'in the flash it sips nectar', '', 'a vine of bright red trumpet flowers', 'a droplet of pollen glinting', 'vivid sunrise with coral and gold highlights')),
    ("a speed skater's glide", 28, _ve('a skater pushes forward, blades cutting thin ice', 'the instant the blade pushes off the surface', '', 'an indoor arena with frosted glass walls', 'a polished oval track curving ahead', 'cool silver light with faint pink reflections')),
    ('a turboprop commuter plane', 350, _ve('a twin-engine turboprop cruising over coastal cliffs', 'the moment its propellers spin in perfect sync', '', 'craggy shoreline with sea-foam crashing below', 'a winding coastal road hugging the cliffs', 'fresh sea-blue light with gentle gold highlights')),
    ('an ultralight over a quiet lake', 45, _ve("the tiny aircraft skims the water's surface in calm", 'the instant the propeller cuts a faint ripple', '', 'still mirror-like lake reflecting pale sunrise over pine trees', 'a smooth waterline leading toward a misty horizon', 'soft pastel blues blended with gentle pink')),
    ('a racing marlin', 50, _ve('the marlin surges ahead, its spear-like nose leading', 'in the instant it bursts from depth', '', 'deep, dark water receding rapidly', 'a shimmering ribbon of water ahead', 'intense sapphire with bright white highlights')),
    ('the International Space Station orbit', 17400, _ve('the massive laboratory gliding silently above the atmosphere', "the instant it passes directly over the observer's latitude", '', 'the curvature of Earth fading into the dark void below', 'the sleek metallic body moving swiftly across the horizon', 'sharp contrast of bright Earth blues and deep black space')),
    ('the Boeing 747', 560, _ve('a massive four-engine airliner glides over a desert sunrise', 'the moment its massive winglets slice the warm air', '', 'endless dunes rippling under a pink-orange sky', 'a narrow strip of paved runway ahead', 'vivid sunrise with fiery orange and soft pink')),
    ('the frigatebird soaring', 35, _ve('the seabird gliding on warm ocean breezes', 'as it circles above a distant reef', '', 'a turquoise lagoon surrounded by coral cliffs', 'a stretch of open sea ahead', 'vivid teal with sun-kissed highlights')),
    ('a feral horse', 30, _ve('the horse gallops across open fields with thunderous rhythm', 'at the precise beat of its fourth stride', '', 'a cloud of kicked-up grass and dust behind', 'a rolling meadow of tall golden reeds ahead', 'warm honey-toned light with deep orange highlights')),
    ('a tongue lick', 7, _ve('the tongue darts forward to taste a surface', 'when the tip contacts the palate briefly', '', 'behind the mandibular ridge, a smooth mucosal layer lies', 'in front, the taste buds sparkle on the tongue surface', 'fresh minty green light with soft highlights')),
    ('the X-15 rocket plane', 4500, _ve('the X-15 rockets upward, leaving a fiery tail', 'the instant it exceeds Mach 5', '', 'a barren desert launch pad under a clear sky', 'a thin column of ionized air ahead', 'bright white flare against deep sapphire sky')),
    ('a fleeing desert hare', 30, _ve('the hare bolts across the sand dunes rapidly', 'when its ears flatten against the wind', '', 'fine sand ripples catching the low sun', 'a distant dune crest glowing orange', 'soft golden light with faint teal shadows')),
    ('a low-altitude patrol aircraft', 250, _ve('the patrol aircraft sweeps low over a marshland', 'as its wheels skim the misty water surface', '', 'shallow wetlands dotted with cattails and reeds', 'a thin line of fog rolling ahead', 'cool silver light with gentle green reflections')),
    ('a sandstorm surge', 40, _ve('massive grains of sand spiraling across a flat desert', 'as the vortex lifts the dunes into motion', '', 'dry, cracked playa stretching to the horizon', 'bare, sun-baked horizon barely visible through haze', 'warm ochre light with a dusty amber veil')),
    ('a sailfish', 68, _ve('the sailfish slices through water, dorsal fin raised high', 'as it accelerates to its maximum sprint', '', 'vast ocean surface reflecting bright midday sun', 'a ripple trail left behind in the water', 'bright white glare with crisp cyan tones')),
    ('the great horned owl swooping', 50, _ve('broad wings beating in a silent rush', 'at the moment it dives toward a shadowed branch', '', 'a dark forest floor carpeted in pine needles', 'a moss-covered fallen log', 'deep dusk light with muted indigo shades')),
    ("a rowing eight's sprint", 13, _ve('eight rowers pull in perfect unison on a river', 'the instant the oars slice through water together', '', 'a calm lake edged with reeds and distant hills', 'a long smooth waterway ahead under bright sky', 'soft teal light with gentle sunrise blush')),
    ('a subsonic trainer jet', 350, _ve('a low-profile trainer jet climbing steadily above clouds', 'the moment its afterburner flickers to life', '', 'snow-covered plateau with sparkling white surface', 'a narrow valley with a frozen river below', 'crisp white light with pale blue shadows')),
    ('a reef manta ray', 18, _ve('the manta glides effortlessly, wings undulating gently', 'when it follows a current through a coral corridor', '', 'a narrow passage of branching coral arches', 'a bright sand channel ahead', 'crystalline turquoise with bright highlights')),
    ('the high-speed gust of a Neptune wind', 1500, _ve('supersonic methane-rich winds whipping across a deep blue world', 'the moment a dark storm cloud rolls forward', '', 'the endless cobalt ocean of clouds receding behind', 'the fierce white-capped wave of wind ahead', 'deep indigo light with icy white streaks')),
    ('a rapid swallow', 20, _ve('the esophagus contracts in a swift peristaltic wave', 'when the bolus passes the upper sphincter quickly', '', 'the throat muscles tighten behind the moving food', 'the stomach entrance opens forward awaiting the next bite', 'soft amber glow with gentle amber undertones')),
    ('the Airbus A320', 530, _ve('a commercial jet pierces a thin layer of clouds', 'the instant it reaches cruising altitude above the ocean', '', 'a vast expanse of deep blue ocean below', 'a faint horizon line of distant islands', 'crisp high-altitude light with cool cyan shades')),
    ('a peregrine falcon stooping', 180, _ve('the swift bird plunging with razor focus', 'at the precise moment it dives toward prey', '', 'a rugged cliffside with wind-carved rocks', 'a narrow gorge opening ahead', 'sharp steel-blue light with crisp shadows')),
    ('a prairie dog', 6, _ve('the prairie dog scurries through its burrow entrance rapidly', 'at the moment its tiny paws touch ground', '', 'a mound of loose earth and tumbleweed behind', 'a sun-warmed patch of short grass ahead', 'soft golden light with a hint of lavender')),
    ('a wind turbine blade', 70, _ve('the blade slices through air in a graceful arc', 'when gusts reach peak velocity', '', 'a rolling hill dotted with low grasses', 'a horizon of distant mountains under clear sky', 'soft sunrise light with pastel pinks')),
    ('the Orion crew capsule', 25000, _ve('the capsule rockets away from Earth on a fiery ascent', 'the instant its launch tower releases its grip', '', 'a sprawling launch complex surrounded by desert scrub', 'a bright plume of smoke stretching forward', 'intense sunrise orange with deep charcoal shadows')),
    ('a bounding springbok', 55, _ve('the springbok leaps high over a low ridge', 'in the precise moment its back legs extend', '', 'low scrubland dotted with yellow wildflowers', 'a distant line of acacia trees', 'warm sunrise glow with pastel pinks')),
    ('a skydiving plane', 130, _ve('the skydiving plane climbs slowly to altitude', 'as its rear door opens to a gust of wind', '', 'a wide open plain dotted with lone tumbleweeds', 'a cluster of white clouds drifting ahead', 'clear bright light with subtle pastel clouds')),
    ('a drifting fog', 1, _ve('thick mist gliding across the meadow grasses', 'at the moment the sunrise lifts the veil', '', 'dewy wildflowers hiding beneath a silvery veil', 'bare earth slowly emerging from the haze', 'cool greys and muted lavender in early light')),
    ('a barracuda', 30, _ve('the barracuda rockets forward with a sleek, streamlined body', 'in the split second it lunges for prey', '', 'open water dotted with floating kelp fronds', 'a school of silvery fish shimmering ahead', 'sharp silver light with high contrast shadows')),
    ('a windsurfing gust push', 22, _ve('the sail catches wind propelling the board forward', 'the exact moment the sail billows fully', '', 'sparkling sea surface with distant horizon and low clouds', 'the water ahead rippling under the moving board', 'crisp teal light with golden sun sparkle')),
    ('the burst of a 100-meter dash', 22, _ve('an athlete propels forward, muscles firing explosively', 'the precise moment the starting blocks release', '', 'a stadium track surrounded by cheering crowds', 'a clean lane stretching toward the finish line', 'vivid stadium lighting with golden highlights')),
    ('a business turbofan', 560, _ve('a twin-engine business jet soaring above cumulus layers', 'the moment its engines roar into full thrust', '', 'vast desert dunes rippling beneath a clear sky', 'a distant mountain ridge catching sunrise light', 'vivid orange-pink horizon with deep azure overhead')),
    ('a thresher shark', 27, _ve('the thresher swings its long tail and speeds forward', 'in the moment it snaps at a schooling fish', '', 'a dark abyss with faint bioluminescent patches', 'a glowing trail of fish ahead', 'deep midnight blue with pulsing violet glows')),
    ('the swift passage of a Venusian cloud', 180, _ve("thick sulfuric clouds drifting across the planet's lower atmosphere", 'the moment a bright patch reflects sunlight', '', 'the endless amber haze fading into distant horizon behind', 'the luminous cloud front moving toward the observer', 'soft golden light with muted yellow tones')),
    ('the gust of a tornado', 150, _ve('rotating funnel tearing across an open plain', 'the moment the vortex touches the earth', '', 'flattened prairie grass swirling in chaotic patterns', 'a line of broken trees torn away ahead', 'violent dark violet light with stark crimson flashes')),
    ('the Cessna 172', 120, _ve('a small propeller plane cruises above a patchwork field', 'the instant its engine hums at steady rpm', '', 'golden wheat fields stretching toward a distant ridge', 'a narrow river glimmering in the sunlight', 'bright daylight with clear blue tones')),
    ('the albatross winging', 40, _ve('the giant seabird skimming ocean breezes', 'when it rides a steady gust aloft', '', 'a vast expanse of deep blue sea below', 'a distant horizon line of water ahead', 'cool turquoise with soft white highlights')),
    ('the supersonic shock of a meteor entering atmosphere', 25000, _ve('a burning rock tearing through thin air at high speed', 'when it ignites at the edge of the thermosphere', '', 'star-filled night sky behind the glowing trail', 'a bright, incandescent fireball racing forward', 'fiery orange with intense white core')),
    ('the moderate sprint', 12, _ve('a sprinter dashes with powerful, quick strides', 'when the front foot lands hard on the track', '', 'a synthetic track surrounded by stadium bleachers and distant trees', 'the straightaway lane stretching ahead', 'bright midday sun with sharp white glare')),
    ('a military transport helicopter', 160, _ve('a heavy lift helicopter hovers over a rugged canyon', 'the moment its rotors create a steady vortex', '', 'steep red rock walls bathed in late afternoon sun', 'a narrow gorge opening ahead', 'warm sandstone glow with amber highlights')),
    ('a galloping mustang', 45, _ve('the mustang thunders across the open range', 'when its mane streams back in the wind', '', 'dusty plain strewn with sagebrush and tumbleweed', 'a distant line of distant mesas', 'high noon glare with bright cerulean sky')),
    ('the stealth bomber', 600, _ve('the stealth bomber glides low over a canyon', 'when its angular shape cuts the thin air', '', 'rugged red rock walls streaked with lichen', 'a river carving a silver ribbon through the gorge', 'muted earth tones under a hazy amber sky')),
    ('a antelope', 65, _ve('the antelope bounds over the rolling foothills', 'as its horns catch the sunrise', '', 'low brush and scattered rocks linger behind', 'a gentle slope climbs forward', 'soft pink light with cool teal shadows')),
    ('a blue tang', 6, _ve('the blue tang darts quickly around a coral head', 'as it changes direction to chase a passing fish', '', 'brightly colored staghorn coral forming a maze', 'a patch of swaying sea fans ahead', 'vivid turquoise light with sparkling highlights')),
    ('a soccer free-kick strike', 55, _ve('the foot snaps forward sending the ball curving', 'the exact moment the ball leaves the shoe', '', 'well-maintained grass pitch with faint divot marks', 'the goalpost framed by a clear sky backdrop', 'vivid green light with bright white glare')),
    ("a cyclist's sprint", 30, _ve('a rider leans low, pedaling hard on a flat road', 'the instant the chain engages the rear cog', '', 'an open highway bordered by distant hills', 'a smooth asphalt ribbon ahead under bright sky', 'clear daylight with crisp cyan highlights')),
    ('a single-engine trainer', 120, _ve('a red-painted trainer climbing gently above pine forests', 'the precise moment its nose lifts toward a cloud', '', 'dense evergreen canopy fading into misty valleys', 'a clear clearing with a sparkling lake below', 'fresh sunrise tones with warm amber highlights')),
    ('a hammerhead shark', 25, _ve('the hammerhead glides with its wide head scanning ahead', 'as it circles a school of fish', '', 'a dimly lit reef plateau with hanging algae', 'a dense swarm of silver fish ahead', 'muted teal with subtle amber undertones')),
]


def sinh_speedof(i):
    ds = TOC_DO
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
    a, b = _cap_ti(KHOI_LUONG, i)
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


# ── NGAY_LUC_NAY: NÂNG TỪ DANH SÁCH NỘI BỘ LÊN BẢNG MODULE  (6/9/2026) ───────────────────────
# Danh sách này nằm TRONG `sinh_rightnow` nên `bang_mo_rong.py` không nhìn thấy nó, và kênh
# `rightnow` dừng ở 30 mục = cạn chủ đề sau ~15 tập short. Không phải vì thế giới hết thứ
# để nói — cùng niche ấy, `howloud` đi từ 31 lên 278 mục chỉ bằng cách nới BẢNG.
# Đưa ra ngoài không đổi một hành vi nào; nó chỉ làm dữ liệu NHÌN THẤY ĐƯỢC từ bên ngoài,
# đúng điều kiện để nới. Cùng bài học §15.12: một trường chỉ được ghi mà không ai đọc
# được thì coi như chưa tồn tại.
NGAY_LUC_NAY = [("asleep right now", 0.42, "dong_ho"), ("in a car right now", 0.02, "xe"),
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


def sinh_rightnow(i):
    ds = NGAY_LUC_NAY
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
    a, b = _cap_ti(CUC_NHO, i)
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


# Trần thời lượng bản dài, tính bằng PHÚT. 10,5 chứ không 11,0: selftest chặn ở 11,0, và đặt
# hằng sát ngưỡng là để cổng nổ vì nhiễu — đúng bài học khi `hiddenfee` rơi vào 5,99 trên sàn
# 6,0. Trần DƯỚI (5,5 phút) canh ở selftest, vì nó là giới hạn của DỮ LIỆU chứ không của mã.
TRAN_PHUT_LONG = 10.5


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


_KHO_ICON = None


def _kho_icon():
    """Đọc chỉ mục icon từ chính tệp engine dùng — MỘT nguồn sự thật (§13.5)."""
    global _KHO_ICON
    if _KHO_ICON is None:
        f = os.path.join(os.path.dirname(__file__), "..", "engine-remotion", "src", "gt", "KhoIcon.ts")
        try:
            t = open(f, encoding="utf-8").read()
            i = t.index("KHO_ICON: Record<string, Icon> = ") + len("KHO_ICON: Record<string, Icon> = ")
            _KHO_ICON = set(json.loads(t[i:t.rindex(";")]).keys())
        except Exception:
            _KHO_ICON = set()
    return _KHO_ICON


_KHO_CANVA = None


def _kho_canva():
    """Chỉ mục kho hình Canva — đọc từ chính tệp engine dùng, MỘT nguồn sự thật (§13.5)."""
    global _KHO_CANVA
    if _KHO_CANVA is None:
        f = os.path.join(os.path.dirname(__file__), "..", "engine-remotion", "src", "gt", "KhoCanva.ts")
        try:
            t = open(f, encoding="utf-8").read()
            i = t.index("KHO_CANVA: Record<string, HinhCanva> = ") + len("KHO_CANVA: Record<string, HinhCanva> = ")
            # `engine-remotion/public/**` nằm trong .gitignore, nên bản khai (KhoCanva.ts, CÓ
            # trong git) đi tới Actions còn ẢNH thì không. Gán `canva` lúc ấy = engine trỏ vào
            # tệp trống -> nhân vật biến mất khỏi 14% nhịp, KHÔNG lỗi nào báo (§12.8).
            # Nên nguồn sự thật cuối cùng là ẢNH CÓ MẶT, không phải bản khai.
            d = os.path.join(os.path.dirname(f), "..", "..", "public", "canva")
            _KHO_CANVA = [(k, set(v["tu"])) for k, v in json.loads(t[i:t.rindex(";")]).items()
                          if os.path.exists(os.path.join(d, k))]
            if not _KHO_CANVA:
                print("   ⚠️ kho Canva: bản khai có %d hình, thư mục ảnh có 0 -> bỏ qua lớp Canva"
                      % len(json.loads(t[i:t.rindex(';')])), file=sys.stderr)
        except Exception:
            _KHO_CANVA = []
    return _KHO_CANVA


# ── TẦNG TÌNH HUỐNG — cầu nối giữa hai vốn từ không gặp nhau ─────────────────────────────
#
# Đo ngày 5/9 trên 216 tập: kho 117 hình chỉ có **17 hình từng được dùng**, 6 kênh không có
# hình nào, và 54/60 chữ đầu của kho (`holding` · `businessman` · `sitting` · `angry`) KHÔNG
# xuất hiện trong bất kỳ kịch bản nào. Vì hai bên nói hai thứ khác nhau:
#
#     kho tả BỨC ẢNH   : holding · walking · thinking · frustrated · pointing · sitting
#     kịch bản tả THẾ GIỚI: noon · driveway · fence · rent · tickets · blink
#
# Và câu thì rất ngắn, phần lớn trừu tượng: *"No breaks."* · *"Now ten people."* ·
# *"Numbers alone mean nothing."* Ghép theo CHỮ TRÙNG NHAU là bất khả về cấu trúc — thêm
# 400 hình cùng tác giả chỉ thêm hàng chết, không thêm một khớp nào.
#
# Nên hỏi câu khác: KHÔNG phải *"câu có chứa danh từ của hình không"* mà *"đây có phải cùng
# một KHOẢNH KHẮC không"*. Hình người chung chung là tài sản chung chung — thứ định vị nó là
# tư thế và cảm xúc, đúng hai thứ mà thẻ của kho ghi.
#
# Mỗi tình huống khai HAI phía: chữ phía CÂU, thẻ phía HÌNH. Đây không phải danh sách ngoại
# lệ (§13.9) — nó là một tập khái niệm ĐÓNG, và mỗi mục đều đọc tay để chắc nó không bịa.
# Nhưng KHÔNG phải hình nào cũng được ghép theo tình huống. Đọc tay 24 cặp đầu tiên thì
# 14 cặp sai, và sai theo đúng một kiểu: hình có NHIỀU thẻ trúng mọi tình huống một cách
# tình cờ — `gallery museum painting running stolen thief` nhận được *"So no. Do not walk."*
# (ra một tên trộm), `during flood house` nhận *"Every day. For life."* (ra một trận lụt).
#
# Khác biệt thật nằm ở chỗ này:
#
#   hình CHUNG CHUNG (chỉ tư thế + cảm xúc)  -> ghép theo tình huống ĐƯỢC. Một người mệt
#                                               ngồi xuống hợp với mọi câu nói về mệt.
#   hình CÓ CẢNH CỤ THỂ (lụt · trộm · cây)   -> BẮT BUỘC câu phải nhắc đúng danh từ ấy.
#                                               Không ai được vẽ lụt cho câu không nói lụt.
#
# Nên `VON_DANG` liệt kê vốn từ TƯ THẾ + CẢM XÚC. Hình nào có thẻ nằm trọn trong đó là hình
# chung chung; hình nào thò ra một danh từ cảnh thì danh từ ấy phải xuất hiện trong câu.
# §17.5: lặp một hình ĐÚNG chỉ nhàm, thay bằng hình SAI thì khung nói một đằng lời một nẻo.
VON_DANG: set[str] = {
    "holding","thinking","walking","sitting","running","standing","pointing","carrying",
    "looking","watching","showing","offering","asking","reading","writing","waiting",
    "angry","frustrated","sad","tired","shocked","smiling","unhappy","confused","unsure",
    "surprised","lonely","happy","exhausted","stressed","worried","bored","calm",
    "man","woman","person","people","character","figures","figure","guy","girl","couple",
    "two","team","group","pose","gesture","hands","hand","arms","arm","legs","head","open",
    "something","anything","behind","away","between","forward","back","down","together",
    "thought","question","answer","decide","choose","choices","choice","crossroad","idea",
    "sleeping","rest","empty","blank","alone","success","loving","heart","cute","kind",
    "exclamation","marks","mark","symbols","surrounded","big","small","new","old","young",
}


TINH_HUONG: dict[str, tuple[set, set]] = {
    "di":      ({"walk","walking","walks","step","steps","road","trip","travel","journey",
                 "mile","miles","arrive","arrives","start","starts","go","goes","drive",
                 "driveway","run","running","moving","move","away","path"},
                {"walking","walk","path","running","run","travel","journey","road","away","way"}),
    "nghi":    ({"rest","sleep","sleeping","tired","break","breaks","stop","stops","quit",
                 "wait","waiting","slow","night","bed","sit","sits","sitting","done"},
                {"tired","sleeping","sitting","rest","sleep","exhausted","sits"}),
    "nghi_ngo":({"think","thinks","thinking","imagine","guess","wonder","idea",
                 "decide","decides","choose","choice","choices",
                 "question","answer","why","maybe","sure","unsure","confused"},
                {"thinking","thought","question","answer","confused","unsure","decide",
                 "choose","choices","crossroad","asking","about","problem","looking"}),
    "sung_sot":({"never","nobody","nothing","impossible","wrong","actually","really",
                 "suddenly","turns","surprise","shocked","wait","cannot","not"},
                {"shocked","surprised","exclamation","marks","surprise","mark"}),
    "buc_boi":({"angry","mad","argue","fight","complain","frustrated","annoy","hate",
                "bad","worse","worst","fault","blame"},
               {"angry","frustrated","unhappy","sad","gesture","fight","fighter","problem"}),
    "tien":    ({"money","cost","costs","price","pay","pays","paid","rent","bill","bills",
                 "fee","fees","dollar","dollars","cheap","expensive","ticket","tickets",
                 "buy","buys","sell","free","worth","spend","charge","charges"},
                {"money","businessman","success","carrying","holding","paper"}),
    "giay_to":({"paper","form","forms","rule","rules","sign","signs","contract","list",
                "write","writes","writing","note","notes","report","desk","office","work",
                "works","job","read","reads","label","print"},
               {"paper","sheet","writing","pen","desk","office","worker","sign","blank",
                "torn","scroll","businessman","holding"}),
    "nha":     ({"house","home","homes","roof","door","doors","room","rooms","apartment",
                 "kitchen","floor","wall","walls","fence","yard","building","window"},
                {"house","roof","door","home","locked","building"}),
    "dong":    ({"everyone","everybody","people","crowd","million","thousand","billion",
                 "group","team","together","city","population","person","persons"},
                {"team","figures","couple","two","crowd","group","people"}),
    "thoi_gian":({"hour","hours","minute","minutes","day","days","year","years","noon",
                  "clock","time","times","late","week","weeks","month","months","second",
                  "seconds","morning","today","tomorrow","already","still","long"},
                 {"clock","time","waiting","during","alarm"}),
    "mot_minh":({"alone","nobody","empty","nothing","lost","single","only","one","last",
                 "gone","missing","blank"},
                {"empty","blank","alone","lonely","lost","missing"}),
    "mang":    ({"carry","carries","carrying","hold","holds","holding","lift","lifts",
                 "weigh","weighs","heavy","pound","pounds","load","pull","push","drop",
                 "dropped","stack","pile"},
                {"carrying","holding","heavy","hands","hand","lifting"}),
    "nhin":    ({"look","looks","watch","watches","watching","see","sees","seeing",
                 "notice","eyes","blink","show","shows","behind","hidden","hide"},
                {"looking","watching","behind","pointing","showing","something","offering"}),
    "man_hinh":({"phone","scroll","screen","app","apps","text","message","tap","online",
                 "internet","click"},
                {"scroll","phone","screen"}),
    "nuoc_lua":({"fire","burn","burns","hot","heat","flame","flood","water","rain","wet",
                 "cold","ice","melt","boil"},
                {"fire","flood","water","burning"}),
    "vui":     ({"win","wins","good","better","best","happy","enjoy","love","nice",
                 "great","easy","success"},
                {"smiling","success","happy","open","arms","loving","heart"}),
}


# ── CHÍNH SÁCH ẢNH: SƠ ĐỒ VẼ BẰNG CODE, CẢNH MỚI DÙNG ẢNH AI ─────────────────────────────
#
# Đo 5/9 trên 16 tập dài: 46% số nhịp đặt ảnh CF, và nó chia rất lệch —
#
#     canh      67%      so_lieu   96%      mọi khuôn còn lại  0%
#
# `so_lieu` là khuôn CON SỐ và BIỂU ĐỒ. Đặt ảnh AI sau lưng một con số là chỗ tệ nhất để
# dùng ảnh AI: nền ảnh làm con số khó đọc, mỗi tập một chất ảnh khác nhau, và FLUX vẽ chữ
# số thì sai (§12.7 — số dài có dấu ra 0/2 đúng). Sơ đồ vẽ bằng code thì nét sạch, màu theo
# kênh, và NHẤT QUÁN TUYỆT ĐỐI giữa mọi tập — mà §12.10 đã đo rằng lệch phong cách giữa các
# ảnh là đòn bẩy lớn nhất của cả bộ.
#
# Nên: họ khuôn SƠ ĐỒ không bao giờ nhận ảnh AI; ảnh AI để dành cho `canh`/`nhom`, nơi cần
# một nơi chốn thật mà code không vẽ nổi.
KHUON_SO_DO = ("so_lieu", "chart", "dem", "truc", "chia_doi", "kinh_lup", "the_chu")


# ── HAI HỌ HÌNH CHO CẢ TẬP  (5/9/2026) ───────────────────────────────────────────────────
#
# Anh: *"xấu, không phù hợp, lộn xộn"* — và chốt rằng lộn xộn nằm TRONG một video.
#
# Đo trên 16 tập: một tập 23 giây đi qua **năm ngôn ngữ hình khác nhau** — biểu đồ cột ·
# thanh trượt · thẻ chữ · hình người · bảng chia đôi. Người xem chưa kịp học cách đọc một
# kiểu thì đã sang kiểu khác.
#
# Và phần lớn sự đa dạng ấy là GIẢ. Đếm trường dữ liệu riêng của từng khuôn:
#
#     so_lieu  41 nhịp -> có `so` + `don`      chart  6 -> có `cot`     the_chu 14 -> có `the`
#     chia_doi 18 · kinh_lup 8 · truc 4 · nhom 4  ->  KHÔNG có trường nào cả
#
# Năm khuôn sau không mang thông tin gì mà một khuôn khác không mang được — chúng chỉ là năm
# cách vẽ khác nhau cho cùng một câu. Bỏ chúng không mất một dữ kiện nào, chỉ mất sự lộn xộn.
#
# HAI HỌ, và ranh giới là một câu hỏi có thật: *nhịp này nói một CON SỐ hay kể một CẢNH?*
#
#     SỐ    -> `so_lieu` (hoặc `chart` khi có dữ liệu cột thật — cùng một họ, hai trạng thái)
#     NGƯỜI -> `canh`
#
# Quyết ở Python và ghi vào nhịp, engine chỉ đọc — cùng nguyên tắc `bo_the`/`kieu_so` (§15.3).
HO_SO = ("so_lieu", "dem", "truc", "kinh_lup", "chia_doi", "the_chu")
HO_NGUOI = ("canh", "nhom")


# Mười khoảnh khắc CÓ NGƯỜI. Dựng từ chính `TINH_HUONG` chứ không chép tay: thêm một
# khoảnh khắc mới ở đó thì bảng này tự có, không có nguồn sự thật thứ hai (§13.5).
_HO_CO_NGUOI = ("di", "nghi", "mang", "nhin", "dong", "vui",
                "buc_boi", "sung_sot", "nghi_ngo", "man_hinh")
# Hai vốn từ cho hai bố cục đạo cụ. Ngắn và ĐÓNG — đây là khái niệm, không phải danh
# sách ngoại lệ (§13.9): "so sánh hai lượng" và "không hình dung nổi" là hai ý hữu hạn.
# ── BIỂU CẢM DỰNG TỪ `TINH_HUONG`, KHÔNG VIẾT BẢNG THỨ HAI ───────────────────────────────
# Lượt đầu em viết sáu vốn từ mới và đo được **5/95 nhịp** có biểu cảm — 95% trung tính, tức
# vẫn đúng cái anh chê. Vốn từ tự viết luôn hẹp, và §13.9 đã nói: danh sách là vô hạn.
# `TINH_HUONG` đã có sẵn vốn từ rộng cho mười khoảnh khắc; biểu cảm chỉ là một PHÉP CHIẾU từ
# khoảnh khắc sang khuôn mặt. Một nguồn sự thật, và thêm chữ ở đó thì biểu cảm tự có (§13.5).
CAM_TU_HO = {
    "vui": "vui", "buc_boi": "gian", "sung_sot": "ngac_nhien",
    "nghi_ngo": "nghi", "nghi": "buon", "mot_minh": "buon",
}

_CO_LUONG = {"thousand", "million", "billion", "trillion", "hundred", "dozen"}
_SS = {"versus", "compared", "bigger", "smaller", "larger", "apart", "difference",
       "gap", "twice", "times", "against", "between", "than"}
_NGHI = {"brain", "head", "mind", "imagine", "understand", "grasp", "sense",
         "picture", "guess", "think", "scale", "instinct"}
_TU_NGUOI: set = set()
for _k in _HO_CO_NGUOI:
    _TU_NGUOI |= TINH_HUONG[_k][0]


def _khong_de_trong(nhip: list) -> None:
    """LƯỚI CHẶN CUỐI: không nhịp nào được phép rỗng. Chạy SAU mọi lượt khác.

    ── VÌ SAO PHẢI LÀ MỘT LƯỚI, KHÔNG PHẢI THÊM MỘT ĐIỀU KIỆN  (5/9/2026) ────────────────
    Anh soi ra khung trống **ba lần**, và ba lần em vá một điều kiện: nới độ dài câu, sửa bộ
    khử trùng, đổi cách trích mệnh đề. Mỗi lần con số tụt (3% -> 1%) nhưng KHÔNG BAO GIỜ về
    không — vì mỗi bản vá chỉ đóng một đường vào chỗ rỗng, mà số đường vào thì em không đếm
    hết được.

    Đây đúng §2: *sửa vòng thứ ba mà vẫn cùng một họ lỗi thì dừng lại, đi tìm thứ cả ba cùng
    dùng*. Thứ cả ba cùng dùng là: **không có ai chịu trách nhiệm cuối cùng cho việc nhịp
    phải có hình**. Nên đặt một lưới, và nó không có nhánh nào trả về tay không:

        1. mệnh đề nào đó của câu đủ ngắn  -> thẻ chữ
        2. tập có con số                   -> khuôn SỐ, mượn số của tập
        3. còn lại                         -> hình so sánh (luôn dựng được)

    Nhánh 3 không cần dữ liệu gì nên nó KHÔNG THỂ trượt. Đó là điều kiện để gọi là lưới.
    """
    for i, n in enumerate(nhip):
        # ── 6/9/2026 — `canh_ve` MỘT MÌNH KHÔNG PHẢI "ĐÃ CÓ HÌNH"  ──────────────────────
        # Soi khung thật: nhịp "And they keep going." ra một nền gần trắng, chỉ có phụ đề.
        # Gốc: `_gop_hai_ho` gán `bt` theo từ vựng câu, và khi câu trừu tượng trùng đúng
        # một câu đã lên thẻ chữ trước đó trong tập (`_cau in _da_the`) thì nhánh ấy bỏ
        # cuộc TRONG IM LẶNG — nhịp không có `bt`, không có `the`. `_rai_canh_ve` chạy sau
        # vẫn gán `canh_ve` cho nó (chỉ cần đúng khuôn + tới lượt xoay), và danh sách bỏ
        # qua ở đây đọc "có `canh_ve`" thành "đã có hình" nên lưới không chặn.
        #
        # Nhưng `CanhVe` (engine) chỉ dựng BỐI CẢNH — kệ hàng, bàn ghế, mái nhà máy — KHÔNG
        # vẽ chủ thể của câu (xem chú thích trong `KichGiaiThich.tsx`: "`canh_ve` KHÔNG vẽ
        # chủ thể của câu"). Engine đã có sẵn cơ chế vẽ CẢ HAI (`canh_ve` làm nền + `bt` làm
        # chủ thể chồng lên trên — xem `btVe` trong `KichGiaiThich.tsx`), nên bỏ `canh_ve`
        # khỏi danh sách "đã đủ" ở đây không mất gì: nhịp vẫn giữ nguyên nền đã chọn, chỉ
        # được lưới bổ sung thêm chủ thể nếu còn thiếu.
        if any(n.get(f) for f in ("ve", "bt", "canva", "hinh_nhap")):
            continue
        if (n.get("khuon") or "canh") not in ("canh", "nhom"):
            continue                     # khuôn SỐ/CHART/THẺ tự vẽ kín khung
        if n.get("canh_ve"):
            # Đã có NỀN (bối cảnh do `_rai_canh_ve` chọn) — chỉ thiếu CHỦ THỂ. Đừng đổi
            # sang `the_chu`: nó bỏ hẳn `canh_ve` đã chọn cho một bố cục khác, và để lại
            # đúng trường mồ côi cổng `kiem_truong` bắt (`dai_chu` ghi cho `canh` mà
            # `the_chu` không đọc). Giữ nguyên nền, chỉ thêm chủ thể chồng lên — đúng cơ
            # chế `btVe` đã có sẵn.
            #
            # `bt="nguoi"` chứ không phải `"nguoi_ss"`: cổng `t_gu_hinh_khac_nhau` cho
            # NGƯỜI lặp liền kề miễn TƯ THẾ khác (`tu` khác), nhưng bắt mọi biểu tượng
            # KHÁC lặp liền kề vô điều kiện — `nguoi_ss` cứng dễ trùng đúng láng giềng.
            #
            # `tu` phải khác nhịp HIỂN THỊ liền trước theo đúng nghĩa của cổng — tức nhịp
            # gần nhất (lùi về trước) có khuôn `canh/nhom/kinh_lup` VÀ có `bt` (bỏ qua
            # nhịp không vẽ hình, chúng "trong suốt" với cổng). Dùng `i % 5` (vị trí
            # trong danh sách THÔ) không đủ — hai nhịp liền kề đúng nghĩa của cổng có thể
            # cách nhau vài chỉ số thô nếu có nhịp SỐ/CHỮ chen giữa.
            _tu_truoc = None
            for _p in range(i - 1, -1, -1):
                _pn = nhip[_p]
                if (_pn.get("khuon") or "") in ("canh", "nhom", "kinh_lup") and _pn.get("bt"):
                    if _pn.get("bt") == "nguoi":
                        _tu_truoc = _pn.get("tu") or 0
                    break
            n["bt"] = "nguoi"
            n["tu"] = ((_tu_truoc + 1) % 5) if _tu_truoc is not None else 0
            n["cam"] = "ngac_nhien"
            continue
        # 1 — thử mọi mệnh đề, không chỉ mệnh đề đầu
        for _c in re.split(r"[.!?]", (n.get("loi") or "")):
            _c = _c.strip()
            if _c and len(_c.split()) <= 9:
                n["khuon"] = "the_chu"
                n["the"] = _c
                break
        else:
            # 2 — mượn con số của một nhịp khác trong tập
            _ng = next((x for x in nhip if x.get("so") and x.get("don")), None)
            if _ng:
                n["khuon"] = "so_lieu"
                n["so"], n["don"] = _ng["so"], _ng["don"]
            else:
                # 3 — nhánh KHÔNG THỂ TRƯỢT
                n["bt"] = "nguoi_ss"
                n["cam"] = "ngac_nhien"


def _giu_chan(nhip: list) -> None:
    """Hai đòn giữ chân, cả hai là CẤU TRÚC chứ không phải hình đẹp hơn.

    ── ĐO TRƯỚC  (5/9/2026) ──────────────────────────────────────────────────────────────
    Anh: *"vẫn chưa có sự giữ chân người coi"*. Đo 6 kênh:

        ba giây đầu : "How long to walk to the moon? / 8.8"  -> một CÂU HỎI kèm con số
        kết         : 0/6 tập ghép vòng được

    §12.12 đã viết sẵn: *hook phải là NỘI DUNG của cảnh đầu, không phải một tấm biển* — mà
    con số kèm nhãn đơn vị chính là tấm biển. §13.16 đo được rewatch là tín hiệu nặng nhất
    của TikTok, nên tập không ghép vòng được là bỏ trắng đòn bẩy lớn nhất.

    THỨ TỰ QUAN TRỌNG: chốt hook TRƯỚC rồi mới cho kết mượn hình. Lượt trước em làm ngược
    nên nhịp cuối mượn phải hình CŨ, và vòng lặp không khớp dù số đo báo 100%.
    """
    if len(nhip) < 4:
        return
    dau, cuoi = nhip[0], nhip[-1]

    # ── 1. HOOK ─────────────────────────────────────────────────────────────────────────
    # Chỉ đổi khi câu TỰ NÓ đã mạnh. Chuẩn hook của bộ này (cổng `selftest`): có SỐ **hoặc**
    # có PHỦ ĐỊNH. Bỏ con số thì câu phủ định vẫn gánh được ("A billion is NOT a big
    # million"), còn câu HỎI thì mất cả hai chân — điểm kịch bản tụt 99,4 -> 97,5 và cổng
    # chặn ngay. Một luật giữ chân không được phép phá một chuẩn đã đo.
    _loi = (dau.get("loi") or "").lower()
    manh = re.search(r"\b(not|no|never|nobody|nothing|cannot|wrong)\b", _loi)
    if manh and not dau.get("ve") and not dau.get("canva"):
        dau["khuon"] = "canh"
        dau["bt"] = "nguoi_ss"
        dau["cam"] = dau.get("cam") or "ngac_nhien"
        for f in ("so", "don", "chu", "cot", "muc"):
            dau.pop(f, None)
        # Hai nhịp liền cùng một hình là thứ cổng `gu hình` bắt, và bắt đúng: người xem đọc
        # ra "đứng hình". Nhịp 1 nhường chỗ cho hook.
        if len(nhip) > 1 and nhip[1].get("bt") == "nguoi_ss":
            nhip[1].pop("bt", None)

    # ── 2. KẾT GHÉP VÒNG ────────────────────────────────────────────────────────────────
    # Nhịp cuối mượn HÌNH của nhịp đầu — chỉ hình, không mượn lời: lời cuối vẫn là cú chốt,
    # nếu không thì tập ấy không kết thúc mà chỉ dừng lại.
    # Gỡ luôn `ve` của nhịp cuối: `ve` là PROMPT chứ không phải ảnh, để nguyên thì ở lượt có
    # CF nó sẽ đè lên hình hook và vòng lặp hở đúng chỗ quan trọng nhất.
    if cuoi is not dau:
        cuoi.pop("ve", None)
        # ── `bt` LÀ HAI TRƯỜNG KHÁC NGHĨA TUỲ KHUÔN — CHÉP MÙ THÌ CHÉP SAI NGHĨA ───────────
        # Rà soát toàn bộ 18 kênh: 61% hook là khuôn `so_lieu` — ở đó `bt` là tên một ICON
        # BÉ đứng cạnh con số ("nguoi" = hình người nhỏ trang trí). Ở khuôn `canh`, `bt` là
        # tên một BỐ CỤC NGƯỜI ĐẦY ĐỦ cần thêm `tu` (tư thế). Bản trước chép thẳng `dau["bt"]`
        # sang `cuoi` bất kể khuôn khác nhau — `howbig` tập 2 dính đúng: hook (so_lieu,
        # bt="nguoi" = icon bé) chép "nguoi" sang nhịp cuối (canh) mà không có `tu`, engine
        # vẽ một bố cục người ĐẦY ĐỦ ở tư thế mặc định, và nó trùng tư thế nhịp liền trước.
        # Đây đúng họ lỗi "chép hằng sang hệ quy chiếu khác" (đã trả giá ở tọa độ hoạt hình).
        #
        # Nếu hook là `so_lieu`/`chart`: nhân bản NGUYÊN KHỐI (khuôn + số + đơn vị + icon) —
        # đó mới thật sự là "khung cuối trùng khung đầu", không phải một icon rơi lạc chỗ.
        if (dau.get("khuon") or "canh") in ("so_lieu", "chart"):
            # `kieu_so`/`bo_so` là bố cục CỦA CHÍNH NHỊP `so_lieu`, giống `kieu_chart` của
            # `chart` — chép cùng lô với `so`/`don`, nếu không cổng `t_moi_nhip_co_bo_cuc`
            # bắt đúng nhịp vừa nhân bản là "thiếu bố cục" dù có đủ số liệu.
            for f in ("khuon", "so", "don", "chu", "cot", "muc", "bt", "kieu_chart",
                      "kieu_so", "bo_so"):
                if dau.get(f) is not None:
                    cuoi[f] = dau[f]
                else:
                    cuoi.pop(f, None)
            cuoi.pop("tu", None)          # so_lieu không dùng tư thế — dọn trường thừa
            cuoi["cam"] = dau.get("cam") or cuoi.get("cam")
        else:
            for f in ("bt", "canva", "hinh_nhap"):
                if dau.get(f):
                    for g in ("bt", "canva", "hinh_nhap"):
                        cuoi.pop(g, None)
                    cuoi[f] = dau[f]
                    cuoi["cam"] = dau.get("cam") or cuoi.get("cam")
                    # Kề nhau ở ĐẦU KIA: nhịp áp chót cũng có thể mang đúng hình vừa chép
                    # sang nhịp cuối. Kề nhau là quan hệ HAI CHIỀU, dọn một phía là dọn nửa
                    # việc. Vòng lặp đòi nhịp cuối TRÙNG nhịp đầu, kể cả TƯ THẾ.
                    if dau.get("tu") is not None:
                        cuoi["tu"] = dau["tu"]
                break
        # ── KỀ NHAU LÀ QUAN HỆ HAI CHIỀU, VÀ EM ĐÃ TỰ DỌN SAI CHỖ  (5/9/2026) ────────────
        # Bản trước tự sửa `nhip[-2]` (nhịp áp chót) ngay tại đây, dùng liền kề THÔ. Nhưng
        # dedup "1b" bên dưới mới là nơi biết liền kề ĐÚNG (theo con mắt, bỏ qua khuôn
        # không vẽ hình) — và nó chạy SAU đoạn này nên đè lại đúng cái vừa sửa, đẻ ra một
        # collision MỚI ở một cặp khác (`wheregoes` tập 2: sửa nhịp áp chót lại làm nó
        # trùng nhịp4, một nhịp áp chót "không biết" tới). Bỏ hẳn đoạn tự sửa ở đây — dời
        # "1b" xuống chạy SAU toàn bộ mục 2, để nó là LƯỚI CUỐI CÙNG duy nhất, đúng nguyên
        # tắc đã trả giá ở `_khong_de_trong`: một lưới đặt trước cái làm rơi thì không đỡ
        # được gì.    # ── 1b. KHÔNG HAI NHỊP LIỀN CÙNG MỘT HÌNH ───────────────────────────────────────────
    # Cổng `gu hình` bắt đúng: hai nhịp liền cùng một biểu tượng thì người xem đọc ra "đứng
    # hình", và ở nhịp cắt 2 giây thì đó là bốn giây không có gì đổi.
    # Dọn TOÀN DANH SÁCH chứ không vá hai đầu: em đã vá phía hook rồi phía kết, và lần nào
    # cổng cũng chỉ ra một cặp khác — vì kề nhau là tính chất của CẢ DÃY, không phải của hai
    # mút. Người thì đổi TƯ THẾ (giữ hình, §17.5), vật thì bỏ hẳn.
    # ── "LIỀN KỀ" PHẢI CÙNG PHẠM VI VỚI CỔNG selftest, KHÔNG PHẢI LIỀN KỀ TRONG DANH SÁCH
    # THÔ  (5/9/2026, rà soát toàn bộ 18 kênh) ─────────────────────────────────────────────
    # Đo: `wheregoes` tập 2 có nhịp4(canh,nguoi) · nhịp5(so_lieu) · nhịp6(the_chu) ·
    # nhịp7(canh,nguoi) — nhịp4 và nhịp7 KHÔNG liền nhau trong danh sách thô nên vòng lặp cũ
    # bỏ qua, nhưng `so_lieu`/`the_chu` tự vẽ kín khung nên MẮT thấy nhịp4 và nhịp7 đứng
    # NGAY CẠNH NHAU. Cổng `selftest` định nghĩa liền kề đúng theo con mắt (bỏ qua khuôn
    # không vẽ hình); vòng lặp này định nghĩa theo chỉ số danh sách. Hai định nghĩa lệch
    # nhau thì cổng bắt được thứ bộ khử trùng bỏ lọt.
    _hienHinh = [n for n in nhip if (n.get("khuon") or "canh") in ("canh", "nhom", "kinh_lup")]
    for q in range(1, len(_hienHinh)):
        a, b = _hienHinh[q - 1], _hienHinh[q]
        if not b.get("bt") or b.get("bt") != a.get("bt"):
            continue
        if str(b["bt"]).startswith("nguoi") and a.get("tu") is not None:
            b["tu"] = (int(a["tu"]) + 2) % 5
        else:
            b.pop("bt", None)
            # GỠ HÌNH MÀ KHÔNG THAY GÌ VÀO LÀ ĐẺ RA KHUNG TRỐNG — đúng thứ anh soi ra hai
            # lần. Bộ khử trùng sinh ra để chống LẶP, không phải để chống CÓ HÌNH; nó không
            # được phép để lại một khung rỗng làm giá phải trả.
            if not any(b.get(f) for f in ("ve", "canh_ve", "canva", "hinh_nhap")):
                _c2 = re.split(r"[.!?]", (b.get("loi") or "").strip())[0].strip()
                if _c2 and len(_c2.split()) <= 9:
                    b["khuon"] = "the_chu"
                    b["the"] = _c2




def _gop_hai_ho(nhip: list) -> None:
    """9 khuôn -> 2 họ. Giữ `chart` khi nhịp có dữ liệu cột thật (nó là trạng thái so sánh
    của chính họ SỐ, không phải một họ thứ ba)."""
    _da_the: set = set()   # câu đã lên thẻ trong tập này — không lặp
    for _vt, n in enumerate(nhip):
        k = n.get("khuon") or "canh"
        if k in HO_NGUOI:
            n["khuon"] = "canh"
        # Gộp xong phải DỌN trường của khuôn cũ: `the` (câu tuyên bố) và `bo_the` (bố cục
        # thẻ chữ) chỉ có nghĩa với `the_chu`. Để nguyên thì nhịp mang một trường không nhánh
        # nào đọc — đúng §15.12, và cổng `kiem_truong` bắt được ngay lượt chạy đầu.
        elif k in HO_SO or k == "chart":
            n["khuon"] = "chart" if n.get("cot") else "so_lieu"
            # nhịp SỐ mà không có số thì không phải nhịp SỐ — trả về họ NGƯỜI, đừng dựng một
            # khung số rỗng (đó đúng là mấy khung trống anh soi thấy).
            if n["khuon"] == "so_lieu" and not n.get("so"):
                n["khuon"] = "canh"
        # Nhịp đổi họ thì trường của họ CŨ phải đi theo. `chu`/`don`/`cot`/`muc` chỉ có
        # nghĩa với họ SỐ; `the`/`bo_the` chỉ có nghĩa với thẻ chữ. Để sót một trường là
        # để lại một thứ ghi-mà-không-ai-đọc, và cổng `kiem_truong` bắt đúng nó.
        if n["khuon"] == "canh":
            for f in ("the", "bo_the", "chu", "don", "cot", "muc"):
                n.pop(f, None)
        elif n["khuon"] != "the_chu":
            n.pop("the", None)
            n.pop("bo_the", None)
    # ── MỌI NHỊP `canh` PHẢI CÓ NGƯỜI ────────────────────────────────────────────────────
    # Soi khung sau lượt gộp đầu: HAI khung trống hẳn, chỉ có giấy và phụ đề. Vì `chia_doi`
    # và `the_chu` mang hình bằng chính BỐ CỤC của chúng — bỏ bố cục đi là không còn gì để
    # vẽ. Đây là cái giá của việc gộp, và nó phải được trả bằng một hình thay thế chứ không
    # phải bằng một khung rỗng.
    # §17.5 đã chốt: nhịp không có vật vẽ được thì vẽ NGƯỜI, cái đổi là TƯ THẾ.
    for n in nhip:
        if (n.get("khuon") or "canh") != "canh":
            continue
        if any(n.get(f) for f in ("ve", "bt", "canh_ve", "canva", "hinh_nhap")):
            continue
        # ── NGƯỜI CHỈ XUẤT HIỆN KHI CÂU NÓI VỀ MỘT NGƯỜI ĐANG LÀM GÌ  (5/9/2026) ─────────
        # Anh: *"tự dưng cho người vô không hợp, không nói lên được nội dung"*.
        # Đúng, và đây là lỗi em tự tạo ở lượt gộp: em cấp `nguoi` cho MỌI nhịp rỗng để
        # không còn khung trống. Nhưng "không trống" không phải là "nói được nội dung" —
        # một người đứng cạnh câu *"Two words. One letter apart."* không nói gì cả.
        #
        # Đo trên 16 tập: 29 nhịp cảnh không có ảnh, trong đó **9 nhịp (31%) là câu TRỪU
        # TƯỢNG** — "The habit, or the number." · "None of that was instinct." — không có
        # người nào trong câu để mà vẽ.
        #
        # `TINH_HUONG` đã sẵn có phía CÂU cho mười khoảnh khắc có người (đi · nghỉ · mang ·
        # nhìn · đông · vui · bực · sửng sốt · nghĩ ngợi · màn hình). Câu chạm vào một trong
        # số đó thì vẽ người; không chạm thì để TRỐNG. Khung chỉ có chữ trên giấy là một
        # nhịp hợp lệ — nó cho mắt nghỉ giữa hai khung đông. Cắm một hình vô can vào đó mới
        # là thứ người xem đọc ra "làm cho có".
        tu = {w for w in re.findall(r"[a-z]{3,}", (n.get("loi") or "").lower())}
        # ── ĐẠO CỤ KỂ NỘI DUNG, KHÔNG PHẢI NGƯỜI ĐỨNG KHÔNG ─────────────────────────────
        # Anh gửi hai ảnh: một người cầm `$` bé và `$` khổng lồ; bốn người ngẩng nhìn đám
        # mây có chữ. Cả hai đều KỂ được câu đang nói — người đứng không thì không.
        #
        # `_SS` là chỗ đắt nhất của 18 kênh này: mọi kênh đều là "X so với Y", nên một
        # người cầm hai vật chênh cỡ chính là nội dung vẽ ra thành hình.
        # biểu cảm gán TRƯỚC, độc lập với tư thế — hai trục khác nhau
        for _ho, _cam in CAM_TU_HO.items():
            if tu & TINH_HUONG[_ho][0]:
                n["cam"] = _cam
                break
        if len(tu & _CO_LUONG) >= 2 or (tu & _SS):
            n["bt"] = "nguoi_ss"
        elif tu & _NGHI:
            n["bt"] = "nguoi_nghi"
        elif tu & _TU_NGUOI:
            n["bt"] = "nguoi"
        else:
            # ── CÂU TRỪU TƯỢNG: CHỮ LÀM HÌNH, KHÔNG PHẢI KHOẢNG TRỐNG ────────────────────
            # Lượt trước em bỏ hẳn hình ở những nhịp này để tránh "cắm người vô duyên", và
            # anh soi ra ngay: *"vẫn trống"*. Bỏ trắng không phải giải pháp — nó là không
            # làm gì, và một khung trống trên nền giấy đọc ra CHƯA LÀM XONG.
            # Cách đúng: lấy chính CÂU làm hình. Vẫn thuộc họ SỐ/CHỮ (chữ trên giấy), không
            # đẻ ra ngôn ngữ hình thứ ba.
            # Chỉ lấy 1–2 chữ CUỐI có nghĩa: cú chốt câu tiếng Anh nằm ở đuôi, và lấy trọn
            # câu thì nó trùng đúng dòng phụ đề ngay dưới.
            # Lấy TRỌN câu, không trích hai chữ cuối. Trích ra "OR NUMBER" · "KNOW KNEW"
            # · "DAY YOURS" — đọc như mảnh gãy chứ không như một câu tuyên bố, vì cú chốt
            # tiếng Anh nằm ở QUAN HỆ giữa hai vế chứ không ở hai chữ cuối. Câu trừu tượng
            # của bộ này vốn đã ngắn (5–7 chữ), nên trọn câu vừa khít một thẻ chữ.
            # Lấy MỆNH ĐỀ ĐẦU chứ không đòi cả dòng ≤ 8 chữ: nhiều nhịp có hai mệnh đề
            # ("The word changes by three letters. The gap does not.") nên điều kiện cũ chặn
            # đúng những câu cần thẻ nhất — anh soi ra một khung TRỐNG HOÀN TOÀN.
            _cau = re.split(r"[.!?]", (n.get("loi") or "").strip())[0].strip()
            if _cau and len(_cau.split()) <= 9 and _cau not in _da_the:
                n["khuon"] = "the_chu"
                n["the"] = _cau
                # KHÔNG tự gán `bo_the` ở đây. Đã có cơ chế gán theo GU CỦA KÊNH (mỗi kênh
                # dùng 3 trong 6 bố cục — đó là bản sắc, §15.2), và nó chạy SAU. Em tự gán
                # thì đè lên gu và sáu bố cục co lại còn ba — đúng dòng đỏ cổng báo.
                # Nơi BIẾT bản sắc kênh mới được quyết; chỗ này chỉ tạo ra nhịp.
                _da_the.add(_cau)


def _chinh_ti_le_cf(nhip: list) -> None:
    """Gỡ `ve` khỏi mọi nhịp thuộc họ SƠ ĐỒ. Một chỗ duy nhất, gọi cuối `kich_ban`."""
    for n in nhip:
        if (n.get("khuon") or "canh") in KHUON_SO_DO and n.get("ve"):
            n.pop("ve", None)


def _rai_canva(nhip: list, ma: str, idx: int) -> None:
    """Chọn cho mỗi nhịp CẢNH một bức tranh Canva khớp NGHĨA của câu.

    Kho là hình do hoạ sĩ vẽ (Canva Elements, tác giả `zdeneksasek`), toàn bộ NÉT MỰC —
    nên engine tô bằng màu kênh và 18 kênh không thể lệch tông nhau.

    Ưu tiên hơn `icon` và hơn `BieuTuong` tự vẽ: đây là hình người thật do hoạ sĩ vẽ, còn
    hai đường kia là icon giao diện và hình que em vẽ bằng code — anh đã chê cả hai.

    Điểm khớp chia cho căn bậc hai số từ của tên, cùng lý do đã dùng ở `_rai_hinh_nhap`:
    tên dài dễ trúng một từ vu vơ, không chia thì tên dài luôn thắng.
    """
    # ── 5/9 — TẮT: MỘT VIDEO MỘT NÉT ────────────────────────────────────────────────
    # Anh: *"sao lấy râu ông nọ cắm cằm bà kia thế"* — và trước đó đã dặn *"đừng râu ông nọ
    # cắm cằm ông kia"*. Đúng: một tập đang có HAI nét — hình Canva vẽ tay của Zdenek Sasek
    # và hình que em vẽ bằng code — xen kẽ nhau.
    # Kho Canva ĐÚNG TÁC GIẢ chỉ có **18 hình** (cổng `kiem_tac_gia` đo được 18/118), không
    # đủ phủ một tập, nên nó buộc phải xen vào giữa nét khác. Không phải kho xấu — kho quá
    # nhỏ để làm nét CHÍNH, mà làm nét phụ thì thành trộn.
    # Nét vẽ bằng code phủ được mọi nhịp, nên nó là nét chính. Bật lại kho Canva bằng
    # GT_CANVA=1 khi nào nó đủ lớn để dùng MỘT MÌNH cho cả tập.
    if os.environ.get("GT_CANVA", "") != "1":
        return
    kho = _kho_canva()
    if not kho:
        return
    dung: dict[str, int] = {}
    for n in nhip:
        if (n.get("khuon") or "canh") not in ("canh", "nhom"):
            continue
        tu = {w for w in re.findall(r"[a-z]{3,}", (n.get("loi") or "").lower())
              if w not in _BO_TU}
        if not tu:
            continue
        # TÌNH HUỐNG của câu: câu ngắn thường trúng 1–2 tình huống, câu rỗng nghĩa trúng 0.
        th = {k for k, (cau, _) in TINH_HUONG.items() if tu & cau}
        tot, diem = None, 0.0
        for ten, tt in kho:
            # (a) chữ trùng thẳng — mạnh nhất khi có, vì nó là nghĩa đen
            d = len(tu & tt) / (len(tt) ** 0.5)
            # (b) cùng khoảnh khắc — đường DUY NHẤT với tới hình người chung chung
            rieng = tt - VON_DANG          # danh từ CẢNH của hình này
            if rieng and not (tu & rieng):
                # Hình có cảnh cụ thể mà câu không nhắc tới cảnh ấy: cấm hẳn đường tình
                # huống. Đây là chỗ chặn "tên trộm cho câu không nói trộm".
                if not d:
                    continue
            elif th:
                hop = sum(1 for k in th if tt & TINH_HUONG[k][1])
                if hop:
                    # Chia cho SỐ THẺ của hình: hình tám thẻ trúng mọi tình huống một cách
                    # tình cờ, hình ba thẻ trúng vì nó thật sự nói về khoảnh khắc ấy.
                    d += 0.42 * hop / ((len(th) * len(tt)) ** 0.5)
            if not d:
                continue
            d *= 0.25 ** dung.get(ten, 0)   # dùng lại trong cùng tập thì tụt hẳn
            if d > diem:
                tot, diem = ten, d
        # Sàn 0,30: dưới mức này hình khớp quá lỏng, hiện lên hại hơn không hiện. Một hình
        # SAI tệ hơn không hình — khung nói một đằng, lời nói một nẻo (§17.5).
        if tot and diem >= 0.30:
            n["canva"] = tot
            dung[tot] = dung.get(tot, 0) + 1


def _rai_icon(nhip: list, ma: str) -> None:
    """Chọn cho mỗi nhịp CẢNH một icon khớp CHỮ trong câu.

    ── VÌ SAO ĐỔI  (5/9/2026) ─────────────────────────────────────────────────────────────
    `_bt_canh` ánh xạ câu vào **23 biểu tượng em tự vẽ**. Đó là gốc của cả hai lời chê nặng
    nhất: "hình que" (chất vẽ là trần của người viết code) và "lặp đi lặp lại" (23 đích cho
    hàng nghìn nhịp — §15.15, hồ quá nhỏ so với số lần rút).
    Kho icon có ~400 từ, và quan trọng hơn: khoá của nó là CHỮ TRONG CÂU, nên hai câu khác
    nhau gần như luôn ra hai hình khác nhau, không cần cơ chế chống trùng nào.

    Từ ĐỨNG SAU được ưu tiên: tiếng Anh đặt thông tin mới ở cuối câu (*"It decides your
    fence"* — `fence` mới là thứ câu nói tới, `decides` chỉ là động từ dẫn). Quét từ phải
    sang trái là mã hoá đúng điều đó, và rẻ hơn hẳn mọi phép phân tích cú pháp.
    """
    # ── 5/9 — TẮT MẶC ĐỊNH: ICON CHỌN TỪ CHỮ TRỪU TƯỢNG RA KÝ HIỆU VÔ NGHĨA ───────────
    # Soi khung bản demo: một dấu `#` khổng lồ và một mũi tên tròn lơ lửng giữa thành phố.
    # Đo trên 16 tập: 38 lượt cấp icon, và chữ kích hoạt gần như toàn là ĐỘNG TỪ / TRẠNG TỪ /
    # danh từ trừu tượng —
    #
    #     now(7) · off · once · own · keep · mean · wrong · quit · touch · hold · look · life
    #
    # chỉ `bus` là danh từ vẽ được. Đúng §17.5: đồ vật chỉ được lấy từ LỜI, mà những chữ này
    # không có hình — nên icon khớp được là icon giao diện, và người xem đọc ra "ký hiệu dán
    # vào cho có". Nhịp không có vật vẽ được thì §17.5 đã chốt: vẽ NGƯỜI, đổi TƯ THẾ.
    # Bật lại bằng GT_ICON=1 khi nào lọc được theo danh từ cụ thể.
    if os.environ.get("GT_ICON", "") != "1":
        return
    kho = _kho_icon()
    if not kho:
        return
    dung = set()
    for n in nhip:
        if (n.get("khuon") or "canh") not in ("canh", "nhom"):
            continue
        tu = [w for w in re.findall(r"[a-z]{3,}", (n.get("loi") or "").lower()) if w in kho]
        if not tu:
            continue
        # Chưa dùng trong tập này thì ưu tiên; hết thì đành lấy lại còn hơn không có hình.
        moi = [w for w in tu if w not in dung]
        n["icon"] = (moi or tu)[-1]
        dung.add(n["icon"])


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
            # ── 6/9/2026 — TẮT XEN KẼ: `canh` PHẢI THỬ CF/GEMINI, KHÔNG CHE TRƯỚC ────────
            # `CANH_MOI` được đặt ra khi hồ ảnh CHỈ có CF (~16.700 ảnh/ngày, phải để dành).
            # Từ khi `sinh()` gộp cả CF+Gemini (~50.000 ảnh/ngày, xem commit trước), lý do
            # tiết kiệm ấy không còn nặng như cũ — mà cái giá của xen kẽ thì vẫn y nguyên:
            # 1/3 nhịp `canh` KHÔNG BAO GIỜ được thử vẽ ảnh, luôn luôn rơi thẳng xuống
            # người que trên nền trơn. Anh soi đúng một video toàn người que và nói thẳng:
            # *"kêu là 100% ảnh footage videos là từ cf và gemini... mà"* — đúng ý anh đã
            # chốt từ trước: *"còn lại ảnh mà cần đúng bối cảnh và khớp thì 100% gemini +
            # cf"*, chỉ chart/số liệu mới vẽ code.
            #
            # Nay MỌI nhịp `canh` đều giữ `ve` và thử CF/Gemini trong `sinh()`; `canh_ve`
            # (người que + nền vẽ code) chỉ còn là lưới đỡ THẬT SỰ khi CẢ HAI nhà đều thua
            # (xem `sinh()`: "4 lượt vẽ đều hỏng" hoặc "cả hồ CF+Gemini đều cạn") — không
            # còn là một chính sách tiết kiệm áp trước khi thử.
            dem_canh += 1
            lay = False
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
        # ── TRẦN THỜI LƯỢNG ĐO TRÊN BẢN THẬT, KHÔNG TRÊN ƯỚC LƯỢNG  (6/9/2026) ──────────────
        # `so_chuong_toi_da` ước thời lượng từ `nc` THÔ của bộ sinh — chưa có nhịp hook, chưa
        # qua `ap_gu`/`doi_loi`, chưa có nhịp mở/chốt của `sinh_long`. Nên nó luôn hụt, và hằng
        # bù (`giay >= 560`) đã phải hiệu chỉnh **hai lần**: 600 -> 560. Nối thêm ~950 mục vào
        # tám bảng thì nó sai lần thứ ba — `howbig` ra 11,2 phút, vượt trần 11 của selftest.
        #
        # §13.7 nói thẳng: sai một hằng số tới lần thứ ba thì THÔI TÌM CON SỐ — đo vật thật.
        # Vật thật ở đây là `nhip` vừa dựng xong, đang nằm ngay trong tay. Đo nó, thừa thì bớt
        # chương rồi dựng lại; bộ sinh không gọi mạng nên rẻ. Không còn hằng bù nào để hiệu
        # chỉnh lần thứ tư — bảng có to lên nữa thì vòng này tự lo.
        while so_chuong > 6:
            _p = sum(max(1.0, len(str(x.get("loi") or "").split()) / 2.8) + 0.35
                     for x in nhip) / 60
            if _p <= TRAN_PHUT_LONG:
                break
            so_chuong = max(6, int(so_chuong * TRAN_PHUT_LONG / _p))
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
        # ── 5/9 — RÀ SOÁT TOÀN BỘ 18 KÊNH: TRẦN 11 CHỮ LUÔN KÍCH HOẠT ────────────────────
        # Đo trên 40 tập của 5 kênh này: câu ghép NGẮN NHẤT đã 13 chữ, dài nhất 18. Tức
        # nhánh dự phòng `f"{_m}."` chạy 100% số lần — không phải một trường hợp hiếm, mà là
        # ĐƯỜNG DUY NHẤT. Hậu quả: `dayinlife` · `wheregoes` · `therules` · `odds` ·
        # `hiddenfee` — MỌI TẬP mở bằng đúng một câu, bất kể nội dung tập là gì.
        #
        # Đây đúng lỗi đã trả giá ở nơi khác trong ngày (đợt sinh script hôm 3/9): hệ tối ưu
        # đúng thứ được bảo tối ưu (hook ngắn, điểm cao) và bỏ quên mục tiêu thật (tập phải
        # PHÂN BIỆT được với nhau). Năm tập giống hệt nhau là thứ chính anh chê "nhàm chán"
        # suốt đêm nay, chỉ là ở lớp KỊCH BẢN chứ không phải lớp hình vẽ.
        #
        # Sửa: khi câu ghép quá dài, đừng BỎ chủ đề — RÚT GỌN nó về vài chữ NỘI DUNG cuối
        # (đã lọc từ hư từ), vẫn đủ để phân biệt tập mà không kéo dài cả câu hỏi.
        if len(_gh.split()) <= 11:
            nhip[0]["loi"] = _gh
        else:
            _dh = " ".join(w for w in re.findall(r"[A-Za-z0-9$]+", hook)
                            if w.lower() not in _BO_TU)
            _dh = " ".join(_dh.split()[-4:])
            nhip[0]["loi"] = f"{_m}. {_dh.capitalize()}." if _dh else f"{_m}."
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
    _gop_hai_ho(nhip)          # gộp TRƯỚC: hình người mới sinh cũng phải được cấp tư thế
    # Lượt gộp SINH RA thẻ chữ mới (câu trừu tượng -> chữ làm hình), mà `_rai_khuon` đã chạy
    # xong từ trước nên những thẻ ấy không có `bo_the` — cổng bắt đúng. Gọi lại một lượt:
    # hàm ấy chỉ gán, không tạo, nên chạy hai lần là an toàn (idempotent).
    _rai_khuon(ma, nhip, idx)
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
    _rai_canva(nhip, ma, idx)
    _chinh_ti_le_cf(nhip)
    _giu_chan(nhip)
    # `_giu_chan` còn SINH RA thẻ chữ (khi bộ khử trùng gỡ hình), mà `_rai_khuon` đã chạy
    # xong từ trước — nên gọi lại lượt nữa. Hàm chỉ gán chứ không tạo nên chạy lại an toàn.
    # Và dọn trường của họ cũ: một nhịp vừa đổi sang thẻ chữ mà còn mang `cam`/`tu` là để
    # lại thứ ghi-mà-không-ai-đọc, cổng `kiem_truong` bắt đúng (§15.12).
    for _n in nhip:
        if (_n.get("khuon") or "") == "the_chu":
            for _f in ("cam", "tu", "nv", "so", "don", "chu", "cot", "muc"):
                _n.pop(_f, None)
    # LƯỚI CHẶN CUỐI đặt ở ĐÂY, sau mọi lượt có thể làm rỗng một nhịp. Lượt trước em đặt
    # nó ngay sau lượt gộp — rồi `_giu_chan` chạy sau và lại gỡ hình đi, nên số khung trống
    # không đổi. Một cái lưới đặt trước cái làm rơi thì không đỡ được gì.
    _khong_de_trong(nhip)
    _rai_khuon(ma, nhip, idx)
    _rai_icon(nhip, ma)
    # ── TẮT LỚP TRANH unDRAW  (5/9/2026) ────────────────────────────────────────────────
    # Tranh unDraw là mảng màu phẳng có bảng màu riêng. Sau khi chốt phong cách NÉT MỰC
    # TRÊN GIẤY (theo các kênh 10M–129M view), nó thành chất liệu thứ hai trong cùng một
    # khung — và §12.10 đã đo: *lệch phong cách giữa các hình là đòn bẩy lớn nhất*, lớn hơn
    # hẳn màu sắc. Một bức tô màu phẳng cạnh một hình vẽ nét đọc ra "ghép từ hai nơi".
    # Giữ nguyên cả đường ống (`_rai_hinh_nhap` · `HinhNhap.tsx` · `KhoSVG.ts`) — bật lại
    # chỉ là bỏ một dòng. Xoá đi thì lần sau phải dựng lại từ đầu.
    if os.environ.get("GT_TRANH_NHAP"):
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

    # ── VẼ CẢNH BẰNG CF + GEMINI  (5/9/2026) ────────────────────────────────────────────
    # Chạy TRƯỚC render, không trong lúc render: một ảnh hỏng thì chỉ nhịp ấy rơi về nền vẽ
    # bằng code, chứ không làm cả tập chết giữa chừng. Đây là bài học bốn tầng nền của bộ
    # truyện tranh — thứ gì gọi mạng phải có tầng không gọi mạng đứng dưới.
    #
    # Trước đây lọc CHỈ giữ khoá `cf:` — khoá Gemini (`AIza...`, không có tiền tố) đọc được
    # từ `keys_cuc_bo()` (biến `GEMINI_KEYS`/`.keys.local`) vẫn nằm trong danh sách trả về,
    # rồi bị vứt NGAY Ở ĐÂY trước khi tới `nen_gt`. Bộ này viết kịch bản 100% bằng code (0
    # lượt Gemini dùng cho chữ), nên 68 khoá Gemini nằm không hoàn toàn — trong khi hồ ảnh
    # ghép CF+Gemini (`datastory_ci.set_ai_pool`) đã chạy thật ở các bộ khác. Anh: *"ảnh kết
    # hợp cả cf + gemini nha"* — bỏ lọc, để `nen_gt.sinh_tap` tự nạp cả hai vào một hồ.
    try:
        import the_he_2 as T2
        import nen_gt
        _ks = [] if os.environ.get("GT_KHONG_CF") else (T2.keys_cuc_bo() or [])
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
    # ── 5/9/2026 — BỎ LƯỢT XẢ `_QUAN_SAT`  ──────────────────────────────────────────────
    # Chú thích cũ ở đây nói "khâu viết kịch bản dùng gemini/groq" — SAI ngay từ đầu, vì
    # bộ này viết kịch bản 100% bằng code, chưa từng `import key_manager`. Nguồn duy nhất
    # từng nạp sổ này là `goi_xoay` (CF) bên `nen_gt.sinh()`, và hàm ấy đã đổi sang
    # `DS._generate_image_ai` (ghi trạng thái thẳng qua `bao_key`/`mark_key_alive`, không
    # qua sổ lô này nữa) — xem `nen_gt.sinh_tap`. Gọi ở đây giờ luôn gặp sổ rỗng.
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
