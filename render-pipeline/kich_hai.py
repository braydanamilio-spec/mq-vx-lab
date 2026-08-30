#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DỰNG PHIM HÀI HAI NHÂN VẬT — thế hệ 4, 10 kênh mới (29/8/2026).

Anh: "dạng videos hài hước phong cách usa, có đa dạng bối cảnh, và đa dạng nhân vật đối thoại
trong 1 videos… mỗi channel mang một phong cách riêng… kịch bản hay viral… short 15-45s-60s…
tận dụng hệ thống api gemini, cf để vẽ ảnh bối cảnh nền".

TÁCH HẲN khỏi 60 kênh đang có. Xem `YTUONG_V4.md` để biết vì sao chọn mười cặp nhân vật này.

    python kich_hai.py --nen          # vẽ + cache nền cho cả 10 kênh (chỉ chạy MỘT LẦN)
    python kich_hai.py --demo         # dựng 1 video cho mỗi kênh
    python kich_hai.py --kenh RENTPANIC

NỀN VẼ MỘT LẦN, DÙNG MÃI. Đo được hôm nay: "đã thử 151 key, tất cả hết hạn mức ảnh". Nếu mỗi
video vẽ nền mới thì bộ này chết đúng vào những ngày bận nhất. Nên nền cache theo KÊNH: 60 ảnh
cho cả bộ, và từ video thứ hai trở đi không tốn một lượt vẽ nào.
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(GOC, "..", "engine-remotion")
PUB = os.path.join(ENG, "public")
NEN = os.path.join(PUB, "v4nen")
sys.path.insert(0, GOC)

# ══════════════════════════════════════════════════════════════════════════════════════════
# MƯỜI KÊNH — mỗi kênh MỘT CẶP nhân vật, MỘT bộ nền, MỘT bảng giọng
# ------------------------------------------------------------------------------------------
# Hài Mỹ ăn khách không đến từ câu đùa mà từ KHOẢNG CÁCH giữa hai người: một bên tin vào điều
# hợp lý, một bên nói ra điều có thật. Nên mỗi kênh là một cặp cố định, và mọi tập đều là hai
# người ấy va nhau ở một chỗ khác.
#
# `nen` = ba prompt vẽ nền. CỐ Ý KHÔNG có chữ trong prompt (xem `_CAM_CHU` bên datastory_ci):
# máy vẽ thấy biển hiệu là bịa chữ, và chữ bịa trên nền thì không sửa được sau.
# ══════════════════════════════════════════════════════════════════════════════════════════
KENH = [
    {"ten": "RENT PANIC", "handle": "@rentpanicusa", "a": "nam_gay", "b": "bank",
     "mau": "#F3E3C6", "de": "rent",
     # ══ CỠ VẬT TRONG KHUNG — thêm 30/8 ═══════════════════════════════════════════════════
     # Anh gửi ảnh: một chậu cây và một bộ sofa TO HƠN CẢ NGƯỜI đứng cạnh. Đó không phải lỗi
     # nhân vật — quay về lối vẽ nào cũng không sửa được. Máy vẽ nhận "phòng khách" rồi trả về
     # một cú áp sát cái ghế, nên người bên cạnh trông như tí hon.
     # Câu cấm cũ đã có "wide shot at standing eye level", nhưng nó nói về GÓC MÁY chứ không
     # nói về CỠ VẬT: một cú wide-shot vẫn lấy trọn khung bằng một cái ghế nếu máy đứng sát nó.
     # Nên ràng thêm bằng hai thứ đo được: không vật nào chiếm quá một phần ba khung, và phải
     # thấy đường tường-gặp-sàn — có đường ấy thì mắt mới có thước để đọc kích thước.
     "nen": ["empty american apartment living room, bare walls, afternoon light, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "apartment building lobby with mailboxes along one wall, warm lamps, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "shared laundry room with washing machines along the back wall, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "apartment hallway with numbered doors receding, ceiling lights, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through"]},
    {"ten": "GYM LIES", "handle": "@gymliesusa", "a": "khoa_hoc", "b": "hang_xom",
     "mau": "#E3EEF6", "de": "gym",
     "nen": ["american gym floor with weight racks along the back wall, cool blue light, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             # Bản cũ ("smoothie bar counter") ra một biển quầy ghi "Smotte" — quầy hàng LÀ một mặt
             # biển hiệu, và máy vẽ thấy mặt phẳng là điền chữ. Góc duỗi cơ vẫn là phòng gym mà
             # không còn mặt nào để dán chữ.
             "gym stretching corner with foam rollers and yoga mats on the floor, plain painted wall behind, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "locker room with a bench and lockers along the back wall, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "empty spin studio with bikes pushed to the back wall, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through"]},
    {"ten": "AIRPORT HELL", "handle": "@airporthellusa", "a": "luat_tre", "b": "y_ta",
     "mau": "#E8EDF4", "de": "airport",
     "nen": ["airport check-in hall with queue barriers, tall windows, overcast light, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "airport departure gate lounge, planes outside the glass, dusk, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "baggage claim hall with a carousel along the back, fluorescent light, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "airport moving walkway corridor with tall windows, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through"]},
    {"ten": "CAR GUY", "handle": "@carguyusa", "a": "hang_xom", "b": "vien_phi",
     "mau": "#EEE6D8", "de": "car",
     "nen": ["auto repair garage bay with tool chests along the back wall, warm work light, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "american suburban driveway beside a parked car, morning, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "tyre shop floor with stacked tyres along the back wall, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "empty car dealership showroom floor, glass front, daylight, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through"]},
    {"ten": "OFFICE SMALL TALK", "handle": "@officesmalltalkusa", "a": "vien_phi", "b": "cong_to",
     "mau": "#EDF1F6", "de": "office",
     "nen": ["office meeting room with a long table pushed to the back, glass wall, daylight, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "office kitchenette with a counter along the back wall, warm light, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "open plan office floor with desks along the back, late afternoon, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "office corridor with a printer against the wall, ceiling lights, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through"]},
    {"ten": "DIET WARS", "handle": "@dietwarsusa", "a": "bank", "b": "hang_xom",
     "mau": "#F6EDDC", "de": "diet",
     "nen": ["american home kitchen with counters along the back wall, bright morning light, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "diner interior with red booths along the back wall, warm light, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "farmers market stall with crates of fruit along the back, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "backyard patio with a grill against the fence, afternoon, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through"]},
    {"ten": "TECH SUPPORT", "handle": "@techsupportusa", "a": "luat_tre", "b": "khoa_hoc",
     "mau": "#E9E6F4", "de": "tech",
     "nen": ["american living room with a sofa against the back wall, evening lamp light, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "call centre floor with cubicles along the back, cool light, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "home office corner with a desk against the wall, soft daylight, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "electronics repair shop counter along the back wall, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through"]},
    {"ten": "PARENT MODE", "handle": "@parentmodeusa", "a": "hang_xom", "b": "sao_dem",
     "mau": "#F4E9DC", "de": "parent",
     "nen": ["american family living room with a worn couch against the wall, afternoon light, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "suburban driveway beside a parked family car, morning, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "teenager bedroom with posters on the back wall, string lights, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "school pickup zone with a low wall and trees, afternoon, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through"]},
    {"ten": "NEIGHBOR WATCH", "handle": "@neighborwatchusa", "a": "hang_xom", "b": "cong_to",
     "mau": "#F7EFD8", "de": "neighbor",
     "nen": ["american suburban backyard with a white picket fence across the back, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "front porch of a suburban house, railing along the back, warm light, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "quiet suburban street with mailboxes along the kerb, morning haze, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "shared driveway between two suburban houses, afternoon, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through"]},
    {"ten": "DATING APP", "handle": "@datingappusa", "a": "sao_dem", "b": "luat_tre",
     "mau": "#F4E6EE", "de": "dating",
     # 30/8 — ĐỔI CÂU VẼ: bản cũ ("bedroom … unmade bed") bị chính bộ lọc của Cloudflare chặn là
     # NSFW, và hôm ấy Gemini vừa cạn nên không có chỗ lui — kênh mất hẳn một nền. Bối cảnh phòng
     # ngủ không cần cho chuyện hẹn hò: chỗ hai người bạn cùng phòng cãi nhau là PHÒNG KHÁCH.
     "nen": ["small apartment living room with a couch against the back wall, evening lamp, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "coffee shop interior with a counter along the back wall, window light, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "quiet residential street at night, parked cars under street lamps, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through",
             "rooftop terrace with a low wall and city skyline behind, dusk, wide shot, camera at standing eye level, floor clearly visible across the lower third and the line where floor meets the far wall visible, open space in the centre of the frame, camera standing back so no single object fills more than a third of the frame, furniture at normal size for a room a standing adult walks through"]},
]

# ══════════════════════════════════════════════════════════════════════════════════════════
# KHOÁ NHÂN VẬT — MỖI KÊNH MỘT CẶP CỐ ĐỊNH, CÓ TÊN, CÓ TÍNH CÁCH
# ------------------------------------------------------------------------------------------
# 30/8 — Học từ bộ 500 prompt anh gửi. Nó mở đầu MỌI tập bằng cùng một khối "CHARACTER LOCK":
# tên, tuổi, dáng người, tóc, áo, quần, giày, tính cách — rồi dặn "never redesign, recolor, age,
# or replace the characters".
#
# Đó chính là thứ bộ này thiếu ở tầng Ý NIỆM (không phải tầng mã): mười kênh đã có mười cặp khác
# nhau về màu áo và bóng dáng, nhưng KHÔNG AI CÓ TÊN. Nhân vật không tên thì mỗi tập là một người
# lạ, và kênh không tích luỹ được nhận diện nào — người xem không thể "hóng tập sau của ai".
#
# Bảng này là bản khai chính thức. Nó dùng cho ba việc, và đó là lý do nó đáng tồn tại:
#   1. VIẾT KỊCH BẢN cho ĐÚNG hai người ấy — người luôn tự tin dù sai, người luôn khô khan và
#      đúng — thay vì viết cho "nhân vật A" và "nhân vật B";
#   2. GIỌNG ĐỌC chọn theo tuổi và tính cách, không chọn theo kiểu vẽ;
#   3. MÔ TẢ KÊNH lúc đăng bài: giới thiệu được hai nhân vật là kênh có mặt mũi.
#
# `giong` ghi CHỮ KÝ giọng chứ không ghi mã giọng: mã giọng là việc của `GIONG` bên dưới, còn
# đây là mô tả để người đọc mã hiểu vì sao chọn mã ấy.
# ══ GIỚI TÍNH NHÂN VẬT — NGUỒN SỰ THẬT DUY NHẤT ═══════════════════════════════════════════
# 30/8 — Anh: *"nhiều khi a thấy con trai mà giọng nữ"*. Soi ra thì giọng không sai; HÌNH sai:
#   · Mrs. Vale, 54 tuổi, chủ nhà  → `"rau": "de"`   (râu dê)
#   · Coach Bree, huấn luyện viên  → `"rau": "quai"` (râu quai nón)
# Gốc rễ là BA BẢNG ĐỘC LẬP nói về cùng một người mà không bảng nào biết bảng kia:
#   `NHAN_VAT` (tên, tuổi, tính) · `_BONG` (dáng, râu, màu áo) · `GIONG_KENH` (giọng).
# `_BONG` được viết theo DÁNG NGƯỜI — cao thấp, gầy béo — nên lúc chọn râu cho "người thứ hai
# trông đô con hơn" thì không có gì nhắc rằng người thứ hai ấy tên là Mrs. Vale.
# Ba bảng thì phải có MỘT bảng cầm sự thật, và hai bảng kia suy từ nó. Bảng ấy là đây.
GIOI = {
    "rent":     ("nam", "nu"),  "gym":      ("nam", "nu"),
    "airport":  ("nam", "nu"),  "car":      ("nam", "nam"),
    "office":   ("nu",  "nam"), "diet":     ("nu",  "nam"),
    # Jae và Sam là tên TRUNG TÍNH, nên lúc viết bảng này tôi đoán giới của họ — và đoán ngược
    # với giọng đã chọn từ trước (Jae nhận giọng Eric nam, Sam nhận giọng Aria nữ). Anh nghe ra
    # ngay: "có clip nam nói tiếng nữ".
    # Sửa theo GIỌNG chứ không theo phỏng đoán của tôi: bảng giọng được chọn theo tuổi và tính
    # cách của từng người, có lý do rõ; còn giới thì tôi suy từ cái tên, mà tên trung tính thì
    # không suy được. Khi hai nguồn mâu thuẫn, tin nguồn có lý do.
    "tech":     ("nam", "nam"), "parent":   ("nam", "nu"),
    "neighbor": ("nam", "nu"),  "dating":   ("nam", "nam"),
}

NHAN_VAT = {
 "rent":     (("Danny", 29, "người thuê nhà, làm ca đêm, tin vào hợp đồng đã ký",
               "trẻ, hơi gấp gáp"),
              ("Mrs. Vale", 54, "chủ nhà, luôn tươi cười khi báo tin xấu",
               "ngọt, chậm rãi, không bao giờ mất bình tĩnh")),
 "gym":      (("Rick", 38, "hội viên năm thứ năm, chủ yếu ngồi trong xe",
               "trầm, thở dài"),
              ("Coach Bree", 31, "huấn luyện viên, nhiệt tình quá mức cần thiết",
               "cao, nhanh, hào hứng")),
 "airport":  (("Paul", 44, "khách bay công tác, đã lỡ ba chuyến trong tháng",
               "mệt mỏi, cố giữ lịch sự"),
              ("Agent Kim", 36, "nhân viên quầy, đọc quy định như đọc thời tiết",
               "đều đều, không lên xuống")),
 "car":      (("Wes", 33, "chủ xe, biết đúng một câu về động cơ",
               "hơi cao giọng khi lo"),
              ("Big Ray", 51, "thợ máy, báo giá theo từng phút",
               "trầm, chậm, chắc nịch")),
 "office":   (("Nina", 27, "nhân viên, đếm phút trong mọi cuộc họp",
               "gọn, khô"),
              ("Todd", 47, "sếp, tin rằng mọi thứ nên là một cuộc họp",
               "ấm, hào hứng, dài dòng")),
 "diet":     (("Marcy", 34, "tuần nào cũng bắt đầu một chế độ mới vào thứ Hai",
               "hăng hái đầu câu, xìu cuối câu"),
              ("Gus", 36, "bạn thân, ăn tất, không giấu giếm",
               "thấp, thủng thẳng, buồn cười")),
 "tech":     (("Hal", 61, "người dùng, gọi tổng đài như gọi cấp cứu",
               "chậm, hơi run"),
              ("Jae", 25, "tổng đài viên, thuộc lòng kịch bản trả lời",
               "trẻ, đều, lịch sự đến mức khó chịu")),
 "parent":   (("Dean", 46, "bố, đo mọi thứ bằng số giờ",
               "trầm, cụt"),
              ("Zoe", 16, "con gái, có lý lẽ cho mọi chuyện",
               "cao, nhanh, tự tin")),
 "neighbor": (("Earl", 58, "hàng xóm, biết mọi chuyện trong bán kính ba nhà",
               "thấp, tò mò, thân mật quá mức"),
              ("Priya", 34, "người mới dọn đến, chỉ muốn dỡ xong đồ",
               "rõ ràng, kiên nhẫn cạn dần")),
 "dating":   (("Owen", 30, "hồ sơ hẹn hò đẹp hơn đời thật một chút",
               "hào hứng, hay chống chế"),
              ("Sam", 30, "bạn cùng phòng, đọc hồ sơ ấy và không nể nang",
               "khô, thẳng, buồn cười")),
}


def ten_nv(de: str, ai: int) -> str:
    """Tên nhân vật A (0) hoặc B (1) của một kênh."""
    c = NHAN_VAT.get(de)
    return c[ai][0] if c else ("A" if ai == 0 else "B")


# ══════════════════════════════════════════════════════════════════════════════════════════
# KỊCH BẢN HÀI — mở · va · leo · chốt
# ------------------------------------------------------------------------------------------
# Mỗi kênh một kho tình huống. Cấu trúc giống nhau (đó là cấu trúc của mọi mẩu hài 30 giây),
# nhưng NỘI DUNG và GIỌNG khác hẳn, nên mười kênh không nghe giống nhau.
# Luật cứng, chốt bằng `cham_v4.py`: lượt thoại ≤ 14 từ · hai người nói xen kẽ · cú chốt ở cuối.
# ══════════════════════════════════════════════════════════════════════════════════════════
KHO = {
 "rent": [
   {"boi": 0, "loi": [
     ("They raised my rent four hundred dollars. For a hallway.", 0, "bat_ngo"),
     ("Yes. We repainted the hallway.", 1, "vui"),
     ("I do not live in the hallway.", 0, "tuc"),
     ("You walk through it. That is a premium.", 1, "tu_tin"),
     ("What if I take the stairs?", 0, "nghi_ngo"),
     ("Then we will need to talk about the stairs.", 1, "vui")
   ]},
   {"boi": 1, "loi": [
     ("Six packages vanished from a lobby with a camera.", 0, "tuc"),
     ("The lobby is not a secure area.", 1, "trung_tinh"),
     ("It has a lock and a camera.", 0, "nghi_ngo"),
     ("The camera is decorative.", 1, "vui"),
     ("Decorative.", 0, "bat_ngo"),
     ("It deters honest people. Those are the ones who matter.", 1, "tu_tin")
   ]},
   {"boi": 2, "loi": [
     ("The laundry room has been closed longer than my lease.", 0, "tuc"),
     ("We are waiting on a part.", 1, "trung_tinh"),
     ("For nine weeks?", 0, "bat_ngo"),
     ("It is a very specific part.", 1, "vui"),
     ("Which part?", 0, "nghi_ngo"),
     ("The one that makes it a laundry room.", 1, "vui")
   ]},
   {"boi": 3, "loi": [
     ("There is a man living in our hallway. With a couch.", 0, "so"),
     ("That is our new resident engagement program.", 1, "vui"),
     ("He has a couch out there.", 0, "bat_ngo"),
     ("He pays for the couch. Separately.", 1, "tu_tin"),
     ("You are charging him rent for a hallway.", 0, "tuc"),
     ("He is charging me. He got here first.", 1, "vui")
   ]},
 ],
 "gym": [
   {"boi": 0, "loi": [
     ("I have paid this gym nine hundred dollars to sit in my car.", 0, "tu_tin"),
     ("Four of those you sat in the car.", 1, "vui"),
     ("The car is in the parking lot. That counts.", 0, "nghi_ngo"),
     ("Then you have the strongest parking lot in town.", 1, "vui"),
     ("So nothing has changed at all.", 0, "buon"),
     ("Your car has lost weight. Very little gas.", 1, "vui")
   ]},
   {"boi": 1, "loi": [
     ("This smoothie costs fourteen dollars because the almonds were asleep.", 0, "bat_ngo"),
     ("It has activated almonds.", 1, "tu_tin"),
     ("What were the almonds doing before?", 0, "nghi_ngo"),
     ("Sleeping. We woke them up.", 1, "vui"),
     ("You woke up almonds for fourteen dollars.", 0, "tuc"),
     ("Twelve. Two dollars is for the waking.", 1, "vui")
   ]},
   {"boi": 2, "loi": [
     ("Somebody threw out my gym bag. It had been there since March.", 0, "tuc"),
     ("How long had it been in the locker?", 1, "trung_tinh"),
     ("Since March.", 0, "buon"),
     ("Then it was not a bag anymore.", 1, "vui"),
     ("It was a bag. It had my shoes in it.", 0, "nghi_ngo"),
     ("It had a civilization in it.", 1, "vui")
   ]},
   {"boi": 3, "loi": [
     ("I am the entire spin class. Again.", 0, "nghi_ngo"),
     ("That is because it is Tuesday at six.", 1, "trung_tinh"),
     ("You said Tuesday at six was peak hour.", 0, "tuc"),
     ("Peak for you. You are the peak.", 1, "vui"),
     ("So I am the entire class.", 0, "buon"),
     ("And the top of the leaderboard. Congratulations.", 1, "vui")
   ]},
 ],
 "airport": [
   {"boi": 0, "loi": [
     ("My flight left twenty minutes ago. I never left this counter.", 0, "so"),
     ("It did. Without you.", 1, "trung_tinh"),
     ("I have been standing at this counter for an hour.", 0, "tuc"),
     ("Then you were very close to it.", 1, "vui"),
     ("Can you put me on the next one?", 0, "nghi_ngo"),
     ("I can put you on a list about the next one.", 1, "tu_tin")
   ]},
   {"boi": 1, "loi": [
     ("They have moved our gate four times. The plane has not moved once.", 0, "tuc"),
     ("Third. One of those was a drill.", 1, "trung_tinh"),
     ("A gate change drill.", 0, "bat_ngo"),
     ("We practice. That is why we are so good at it.", 1, "vui"),
     ("Good at moving people for no reason.", 0, "tuc"),
     ("There is always a reason. It is just not yours.", 1, "vui")
   ]},
   {"boi": 2, "loi": [
     ("My bag came out of the plane wet. It was not raining.", 0, "bat_ngo"),
     ("Was it raining where you left from?", 1, "trung_tinh"),
     ("It was raining inside the plane?", 0, "nghi_ngo"),
     ("Planes are complicated.", 1, "vui"),
     ("What is in this bag is a laptop.", 0, "so"),
     ("Was. Was a laptop.", 1, "vui")
   ]},
   {"boi": 3, "loi": [
     ("This moving walkway has not moved since I landed.", 0, "tuc"),
     ("It is not broken. It is a floor now.", 1, "tu_tin"),
     ("It is a floor that used to move.", 0, "nghi_ngo"),
     ("Most floors used to be something.", 1, "vui"),
     ("That is not a real sentence.", 0, "bat_ngo"),
     ("Neither is your connection time.", 1, "vui")
   ]},
 ],
 "car": [
   {"boi": 0, "loi": [
     ("You said two hundred. This invoice says nine hundred.", 0, "nghi_ngo"),
     ("That was before I opened it.", 1, "trung_tinh"),
     ("What is it now?", 0, "so"),
     ("Two hundred. Per hour. Since I opened it.", 1, "vui"),
     ("Then close it.", 0, "tuc"),
     ("Closing is also labor.", 1, "vui")
   ]},
   {"boi": 1, "loi": [
     ("There is a bird living in my engine. You knew.", 0, "bat_ngo"),
     ("Yes. She has been there since spring.", 1, "trung_tinh"),
     ("You saw her and said nothing?", 0, "tuc"),
     ("She was not causing trouble. You were.", 1, "vui"),
     ("So what do we do now?", 0, "nghi_ngo"),
     ("We wait. Two more weeks and the eggs drive off.", 1, "vui")
   ]},
   {"boi": 2, "loi": [
     ("I asked for two tyres. You billed me for four.", 0, "tuc"),
     ("Correct. Four is how many the car has.", 1, "tu_tin"),
     ("I only asked for the front two.", 0, "nghi_ngo"),
     ("The back two felt left out.", 1, "vui"),
     ("Tyres do not have feelings.", 0, "bat_ngo"),
     ("Then why did two of them cost extra?", 1, "vui")
   ]},
   {"boi": 3, "loi": [
     ("This brand new car already has eleven miles on it.", 0, "nghi_ngo"),
     ("Someone had to drive it here.", 1, "trung_tinh"),
     ("From where? The factory is eleven miles away?", 0, "bat_ngo"),
     ("No. He took the long way around the lot.", 1, "vui"),
     ("Eleven miles around a parking lot.", 0, "tuc"),
     ("He was thinking about his life.", 1, "vui")
   ]},
 ],
 "office": [
   {"boi": 0, "loi": [
     ("We are fifty minutes into a meeting about the next meeting.", 0, "buon"),
     ("And we have covered a lot.", 1, "vui"),
     ("We have covered the agenda for the next meeting.", 0, "tuc"),
     ("That is the hardest part.", 1, "tu_tin"),
     ("This could have been an email.", 0, "nghi_ngo"),
     ("It was. Nobody read it. So here we are.", 1, "vui")
   ]},
   {"boi": 1, "loi": [
     ("Someone drank the coffee I bought. From the pot I filled.", 0, "tuc"),
     ("The pot is communal.", 1, "trung_tinh"),
     ("I bought the beans.", 0, "nghi_ngo"),
     ("Then the beans were communal too.", 1, "vui"),
     ("Nothing here is mine.", 0, "buon"),
     ("Your desk is yours. Until Friday.", 1, "vui")
   ]},
   {"boi": 2, "loi": [
     ("My desk is in the hallway. With a printer on it.", 0, "bat_ngo"),
     ("We are opening up the floor plan.", 1, "vui"),
     ("The hallway is not the floor plan.", 0, "tuc"),
     ("It is now. We call it the corridor of ideas.", 1, "tu_tin"),
     ("There is a printer on my keyboard.", 0, "nghi_ngo"),
     ("Then you are the printer team. Congratulations.", 1, "vui")
   ]},
   {"boi": 3, "loi": [
     ("The printer wants yellow ink. For a black and white page.", 0, "nghi_ngo"),
     ("Yes. For a black and white document.", 1, "trung_tinh"),
     ("Why does it need yellow for that?", 0, "bat_ngo"),
     ("It does not. It just wants yellow.", 1, "vui"),
     ("So we buy it yellow.", 0, "buon"),
     ("We buy it yellow. And it prints in November.", 1, "vui")
   ]},
 ],
 "diet": [
   {"boi": 0, "loi": [
     ("This is my fourth diet this month. It is the twelfth.", 0, "tu_tin"),
     ("That is what you said about the last Monday.", 1, "vui"),
     ("This one is different. No sugar at all.", 0, "tu_tin"),
     ("There is a birthday cake in your fridge.", 1, "nghi_ngo"),
     ("That is for the birthday.", 0, "buon"),
     ("Whose?", 1, "vui")
   ]},
   {"boi": 1, "loi": [
     ("I had one fry. The waiter offered to bring me my own.", 0, "tu_tin"),
     ("You ate the plate around the fry.", 1, "vui"),
     ("That is an exaggeration.", 0, "nghi_ngo"),
     ("The waiter asked if I wanted another one. For me.", 1, "vui"),
     ("Fine. I had a few.", 0, "buon"),
     ("You had a portion with a name and a table.", 1, "vui")
   ]},
   {"boi": 2, "loi": [
     ("This potato costs four dollars because it has a sticker.", 0, "tu_tin"),
     ("So is a potato in a normal store.", 1, "trung_tinh"),
     ("This one has a sticker.", 0, "nghi_ngo"),
     ("The sticker costs four dollars.", 1, "vui"),
     ("It is worth it for the peace of mind.", 0, "tu_tin"),
     ("You are buying a sticker and a small potato.", 1, "vui")
   ]},
   {"boi": 3, "loi": [
     ("I am meat only now. I cried at a burger advert last week.", 0, "tu_tin"),
     ("You cried at a hamburger commercial last week.", 1, "nghi_ngo"),
     ("That was about the family in it.", 0, "buon"),
     ("The family was eating hamburgers.", 1, "vui"),
     ("It is a lifestyle, not a phase.", 0, "tuc"),
     ("Every phase is a lifestyle for eight days.", 1, "vui")
   ]},
 ],
 "tech": [
   {"boi": 0, "loi": [
     ("My screen has been black since Tuesday. It is Friday.", 0, "buon"),
     ("Have you tried turning it off and on again?", 1, "trung_tinh"),
     ("It is already off. That is the problem.", 0, "tuc"),
     ("Then turn it on and off again.", 1, "tu_tin"),
     ("That is the same two things.", 0, "nghi_ngo"),
     ("In a different order. That is the fix.", 1, "vui")
   ]},
   {"boi": 1, "loi": [
     ("Forty minutes on hold to be told my call is important.", 0, "tuc"),
     ("Your call is very important to us.", 1, "vui"),
     ("Then why am I still on hold?", 0, "nghi_ngo"),
     ("Because it is important. We are savoring it.", 1, "vui"),
     ("Can I speak to a person?", 0, "buon"),
     ("You are. That is the sad part.", 1, "vui")
   ]},
   {"boi": 2, "loi": [
     ("The update deleted my files. Including the backup.", 0, "so"),
     ("Did you back them up?", 1, "trung_tinh"),
     ("The backup was a file.", 0, "buon"),
     ("Then it worked exactly as designed.", 1, "tu_tin"),
     ("What was the update even for?", 0, "tuc"),
     ("Improved file management.", 1, "vui")
   ]},
   {"boi": 3, "loi": [
     ("Ninety dollars. That was the price of you looking at it.", 0, "nghi_ngo"),
     ("That was the diagnostic.", 1, "trung_tinh"),
     ("The diagnostic was you looking at it.", 0, "tuc"),
     ("With trained eyes.", 1, "tu_tin"),
     ("What did the trained eyes find?", 0, "nghi_ngo"),
     ("That the screen is broken. Ninety dollars.", 1, "vui")
   ]},
 ],
 "parent": [
   {"boi": 0, "loi": [
     ("Six hours. That is how long that phone has been in your hand.", 0, "tuc"),
     ("I was doing homework on it.", 1, "trung_tinh"),
     ("What subject has that much scrolling?", 0, "nghi_ngo"),
     ("Research.", 1, "tu_tin"),
     ("Research on what?", 0, "nghi_ngo"),
     ("On whether I should do the homework.", 1, "vui")
   ]},
   {"boi": 1, "loi": [
     ("You have driven twice. The mirror is pointed at your face.", 0, "so"),
     ("And zero accidents. That is a perfect record.", 1, "tu_tin"),
     ("You have driven twice.", 0, "nghi_ngo"),
     ("Two for two. Nobody is doing better.", 1, "vui"),
     ("The mirror is pointed at your face.", 0, "tuc"),
     ("That is the most important thing behind me.", 1, "vui")
   ]},
   {"boi": 2, "loi": [
     ("There are eleven cups in this room. You know exactly where.", 0, "bat_ngo"),
     ("Eleven. Two are under the bed.", 1, "trung_tinh"),
     ("Why do you know that and not bring them down?", 0, "tuc"),
     ("Knowing and carrying are different jobs.", 1, "tu_tin"),
     ("Who does the carrying job?", 0, "nghi_ngo"),
     ("Historically? You.", 1, "vui")
   ]},
   {"boi": 3, "loi": [
     ("I have been parked here thirty minutes. In an orange car.", 0, "tuc"),
     ("I did not see you.", 1, "trung_tinh"),
     ("I am in a bright orange car.", 0, "nghi_ngo"),
     ("I was not looking for a car. I was looking for a ride.", 1, "vui"),
     ("Those are the same thing.", 0, "bat_ngo"),
     ("Not if I pretend I do not know you.", 1, "vui")
   ]},
 ],
 "neighbor": [
   {"boi": 0, "loi": [
     ("You have watched me carry forty boxes and offered nothing.", 0, "nghi_ngo"),
     ("Forty minutes. I took a break.", 1, "vui"),
     ("Do you want to help?", 0, "trung_tinh"),
     ("No. I want to know what is in the long one.", 1, "tu_tin"),
     ("It is a mirror.", 0, "buon"),
     ("That is what the last one said too.", 1, "vui")
   ]},
   {"boi": 1, "loi": [
     ("Your sprinkler has hit my porch every morning for a year.", 0, "tuc"),
     ("It hits a lot of things. It is a strong one.", 1, "tu_tin"),
     ("Can you turn it two inches to the left?", 0, "nghi_ngo"),
     ("Then it would hit the Hendersons.", 1, "trung_tinh"),
     ("So the Hendersons and I are the only options.", 0, "bat_ngo"),
     ("They complain less. So it is you.", 1, "vui")
   ]},
   {"boi": 2, "loi": [
     ("There is a camera on your house. Zoomed in on my mailbox.", 0, "tuc"),
     ("It faces the street. Your mailbox is on the street.", 1, "tu_tin"),
     ("It is zoomed in on the mailbox.", 0, "nghi_ngo"),
     ("The street is boring at that distance.", 1, "vui"),
     ("Take it down.", 0, "tuc"),
     ("I cannot. It is watching itself now.", 1, "vui")
   ]},
   {"boi": 3, "loi": [
     ("Your car is blocking two driveways. Mine is one of them.", 0, "tuc"),
     ("I know. That is the only way it fits.", 1, "trung_tinh"),
     ("Then it does not fit.", 0, "nghi_ngo"),
     ("It fits. Just not for you.", 1, "vui"),
     ("I cannot get out.", 0, "so"),
     ("Then you are not going anywhere. Neither am I. Neighbors.", 1, "vui")
   ]},
 ],
 "dating": [
   {"boi": 0, "loi": [
     ("My profile says I love hiking. I have hiked once. In 2019.", 0, "tu_tin"),
     ("You have been hiking once. In two thousand nineteen.", 1, "nghi_ngo"),
     ("It made a big impression.", 0, "trung_tinh"),
     ("You called it a walk with a hill problem.", 1, "vui"),
     ("That is still hiking.", 0, "tuc"),
     ("Then I am a sailor. I once stood on a boat.", 1, "vui")
   ]},
   {"boi": 1, "loi": [
     ("She asked what I do for fun. I said I enjoy experiences.", 0, "so"),
     ("What did you say?", 1, "nghi_ngo"),
     ("I said I enjoy experiences.", 0, "buon"),
     ("That is what a hostage says.", 1, "vui"),
     ("It was true though.", 0, "trung_tinh"),
     ("So is breathing. Do not lead with it.", 1, "vui")
   ]},
   {"boi": 2, "loi": [
     ("He was forty minutes late and told me time is a construct.", 0, "tuc"),
     ("Did he say why?", 1, "nghi_ngo"),
     ("He said time is a construct.", 0, "buon"),
     ("So is the bill. Did he pay it?", 1, "vui"),
     ("He said he would send it to me.", 0, "tuc"),
     ("Then the bill is a construct. He is not.", 1, "vui")
   ]},
   {"boi": 3, "loi": [
     ("I matched with someone four floors up. We have never met.", 0, "bat_ngo"),
     ("In this building?", 1, "nghi_ngo"),
     ("Yes. We have been chatting all week.", 0, "vui"),
     ("You could take the stairs.", 1, "trung_tinh"),
     ("That feels too fast.", 0, "so"),
     ("You have been dating an elevator ride.", 1, "vui")
   ]},
 ],
}

# ══════════════════════════════════════════════════════════════════════════════════════════
# CỬ CHỈ SUY TỪ CHÍNH CÂU THOẠI, KHÔNG XOAY VÒNG THEO CHỈ SỐ
# ------------------------------------------------------------------------------------------
# Bản cũ gán cử chỉ bằng `CU_CHI[i % 6]` — tức là câu nào ở vị trí 2 cũng chỉ tay, bất kể câu ấy
# nói gì. Kết quả là nhân vật chỉ tay khi đang đầu hàng và nhún vai khi đang gặng hỏi: tay nói
# một đằng, miệng nói một nẻo. Trong hoạt hình, tay là NỬA CỦA CÂU THOẠI — sai tay thì câu chết.
#
# Nay suy từ chính chữ: câu hỏi thì ngửa tay ra, con số thì đếm, phủ định thì khoanh tay, câu
# chốt thì mở rộng hai tay. Chỉ là mấy phép thử chuỗi, không cần mô hình nào — và nó đúng hơn
# hẳn phép chia lấy dư.
_HOI = ("what", "why", "how", "who", "when", "which", "can ", "do ", "did ", "is ", "are ")
_PHU = ("not", "no ", "never", "nothing", "cannot", "do not", "does not", "was not")

def cu_chi_cua(chu: str, i: int, cuoi: bool) -> str:
    t = " " + str(chu or "").lower().strip()
    if cuoi:
        return "mo_tay"                       # cú chốt: mở rộng tay, "đấy, xong"
    if "?" in t:
        return "chi" if t.strip().startswith(("what", "why", "who")) else "nhun_vai"
    if any(c.isdigit() for c in t) or any(w in t for w in (" one", " two", " four", " nine", " forty", " hundred")):
        return "dem"                          # có con số thì đếm ngón tay
    if any(w in t for w in _PHU):
        return "khoanh_tay"                   # phủ định: khép người lại
    if t.strip().startswith(("i think", "maybe", "then ", "so ")):
        return "suy_nghi"
    # Vòng xoay mặc định cũ có "mở tay" chiếm hai trên bốn chỗ, cộng với cú chốt và câu hỏi
    # cũng dùng nó — nên nó ra 20 lần trên mười tập, gần một phần ba tổng số lượt. Một cử chỉ
    # biên độ lớn dùng dày như thế thì thôi làm dấu nhấn và thành thói quen khua tay.
    # Vòng mới lấy toàn cử chỉ NHỎ, để dành "mở tay" cho đúng chỗ nó có nghĩa: cú chốt.
    return ["nghi", "dem", "chong_nanh", "chi", "ngan_ngam", "suy_nghi"][i % 6]

CU_CHI = ["mo_tay", "chi", "nhun_vai", "dem", "suy_nghi", "khoanh_tay"]
# 30/8 — HIỆU ỨNG ÂM DỒN VÀO CÚ CHỐT, KHÔNG RẢI ĐỀU.
# Bản cũ đặt pop ở lượt 1, whoosh ở lượt 3, ding ở lượt 5 — tức là cứ hai câu lại có một tiếng
# động, bất kể câu ấy có gì đáng nhấn. Trong hài, tiếng động RẢI ĐỀU làm loãng đúng thứ nó định
# nhấn: tai quen đi, và đến cú chốt thì tiếng động ấy chỉ còn là một tiếng nữa như mọi tiếng
# trước. Nhấn thì phải hiếm.
# Nên chỉ còn HAI: một tiếng nhẹ ở lượt VA (chỗ người xem cười lần đầu), và một tiếng ở CÚ CHỐT.
# `None` nghĩa là "gắn vào lượt cuối", tính lúc dựng vì số lượt mỗi kịch bản một khác.
SFX = {1: "sfx/pop.mp3"}
SFX_CHOT = "sfx/ding.mp3"


def canh_moi_luot_ai(k: dict, cau: list, keys) -> list:
    """Một cảnh nền cho MỖI LƯỢT thoại. Trả danh sách cùng độ dài `cau`, hoặc [].

    30/8 — Anh: *"bối cảnh cũng thế cần ai phân tích vẽ cho phù hợp"*. Bộ dữ liệu đã chạy một
    nền mỗi câu; bộ hài vẫn một nền cho cả tập, nên sáu lượt đối đáp diễn ra trong đúng một khung
    đứng yên — và trong hài, khung đứng yên hai mươi giây là chỗ khán giả lướt qua.
    Và MỌI cảnh phải là TOÀN CẢNH ở tầm mắt người đứng. Để mô hình tự do chọn góc thì nó trả về
    "close-up of engine block" hay "low angle looking into pistons" — vẽ ra là máy móc khổng lồ
    chiếm cả khung, mà nhân vật thì luôn được vẽ ở cỡ người, nên hai thứ lệch tỉ lệ và nhân vật
    hoá ra đứng tí hon giữa một cái pít-tông. Nền của phim hoạt hình có người đứng trước thì
    không bao giờ được là ảnh cận.

    Khác bộ dữ liệu ở một điểm: hài phải giữ LOGIC KHÔNG GIAN (luật 7x — hai người đang nói với
    nhau thì không dịch chuyển). Nên câu hỏi ép rõ: cùng MỘT địa điểm, chỉ đổi GÓC NHÌN và chi
    tiết tiền cảnh. Đổi khung mà không đổi chỗ — đúng cách một cảnh phim thật được dựng.
    """
    if not keys or not cau:
        return []
    try:
        import content_brain as CB
    except Exception:
        return []
    _nv = NHAN_VAT.get(k["de"])
    _ai = (f"A is {_nv[0][0]}, {_nv[0][2]}. B is {_nv[1][0]}, {_nv[1][2]}.\n" if _nv else "")
    ds = "\n".join(f"{i+1}. {'AB'[c[1]]}: {c[0]}" for i, c in enumerate(cau))
    hoi = (
        "You are the background artist for one short 2D cartoon comedy scene.\n"
        f"{_ai}Dialogue:\n{ds}\n\n"
        f"All lines happen in ONE single location. Return exactly {len(cau)} numbered lines: for "
        "line N, ONE short English phrase (max 12 words) describing the SAME place from a "
        "different angle or with different foreground detail that suits that line.\n"
        "Never move to another location. Vary the camera angle and props, not the place.\nEVERY scene must be a WIDE shot at standing eye level, showing a room or open space with the floor visible. Never a close-up, never a macro shot, never a low angle looking up at an object.\n\n"
        "Hard rules: no brand names, no proper nouns, no people, no text or signage, all "
        "packaging blank. Objects and places only.\n"
        "Format strictly as: 1. phrase\n2. phrase\n... nothing else."
    )
    import re as _re
    for kk in xoay_key(keys):
        try:
            g = CB._genai(kk if isinstance(kk, str) else kk.get("key"))
            m = g.GenerativeModel("gemini-2.5-flash")
            t = str(getattr(m.generate_content(hoi), "text", "") or "")
            ra = []
            for ln in t.splitlines():
                mm = _re.match(r"\s*(\d+)[.)]\s*(.+)", ln)
                if mm:
                    v = " ".join(mm.group(2).split()).strip().strip('"').rstrip(".")
                    if 6 <= len(v) <= 130:
                        ra.append(v)
            if len(ra) >= len(cau):
                return ra[:len(cau)]
        except Exception:
            continue
    return []


def ve_nen_moi_luot(k: dict, DS, canh_ds: list) -> list:
    """Vẽ một nền cho mỗi cảnh. Cache theo NỘI DUNG cảnh nên tập sau dùng lại được."""
    import hashlib as _hl
    os.makedirs(NEN, exist_ok=True)
    ra = []
    for canh in canh_ds:
        if not canh:
            ra.append("")
            continue
        rel = os.path.join("v4nen", f"c{_hl.md5(canh.encode('utf-8')).hexdigest()[:10]}.jpg")
        dest = os.path.join(PUB, rel)
        # 30/8 — anh soi ra chữ giả vẫn còn trên nền ("MATLE", "GYM", "PRICE") dù bộ dò chữ đã
        # nối vào sáng nay. Gốc rễ ở ngay dòng này: ảnh đã có trên đĩa thì trả về NGAY, không
        # qua bất kỳ phép kiểm nào. Gần mười một nghìn ảnh nền vẽ TRƯỚC khi có bộ dò, và tất cả
        # đi thẳng vào video mà không lần nào bị hỏi.
        # **Một cổng đặt sau bộ nhớ đệm thì nó chỉ gác những thứ chưa từng đi qua.**
        # Nay ảnh cache phải có DẤU ĐÃ KIỂM (`.ok` bên cạnh) mới được dùng thẳng; ảnh cũ không
        # có dấu thì bị dò một lần rồi ghi dấu — nên mỗi ảnh chỉ tốn một lượt hỏi, đúng một lần
        # trong đời nó.
        if os.path.exists(dest) and os.path.getsize(dest) > 20000:
            _dau = dest + ".ok"
            if not os.path.exists(_dau):
                if _co_chu(dest):
                    try:
                        os.remove(dest)
                    except OSError:
                        pass
                else:
                    io.open(_dau, "w").write("1")
        if os.path.exists(dest) and os.path.getsize(dest) > 20000:
            ra.append(rel)
            continue
        _them = CAM_CHU
        if any(x in canh.lower() for x in ("packet", "package", "box", "bottle", "carton",
                                           "label", "product", "shelf", "brand", "snack")):
            _them += ", all packaging completely blank and unbranded, no printed text"
        ok = None
        for _l in range(2):
            try:
                import datastory_ci as _DC
                _p = _DC._salt_prompt(f"{canh}{_them}, {SAN_NEN}, {GU_NEN}")
            except Exception:
                _p = f"{canh}{_them}, {SAN_NEN}, {GU_NEN}"
            try:
                ok = DS._generate_image_ai(_p, dest, None, style=GU_NEN)
            except Exception:
                ok = None
            if ok and os.path.exists(dest) and os.path.getsize(dest) > 20000:
                break
            ok = None
        if ok:
            try:
                DS.nang_sang_anh(dest); _keo_sang(dest)
                if _nen_hong(dest) or _co_chu(dest):
                    os.remove(dest); ok = None
                else:
                    io.open(dest + ".ok", "w").write("1")
            except Exception:
                pass
        ra.append(rel if (ok and os.path.exists(dest)) else "")
    print(f"      🎨 {sum(1 for x in ra if x)}/{len(ra)} nền theo lượt")
    return ra


def canh_nen_ai(k: dict, cau: list, keys) -> str:
    """Hỏi AI: mẩu hài này diễn ra ở đâu thì hợp nhất? Trả cụm mô tả, rỗng nếu hỏng.

    30/8 — Anh: *"10 channel hài cũng nên ứng dụng ai gọi để vẽ bối cảnh"*.
    Bộ này đang dùng bốn câu vẽ CỐ ĐỊNH mỗi kênh, gán theo chỉ số kịch bản. Nên tập nói về cái
    máy giặt hỏng và tập nói về gói hàng mất trộm cùng đứng trong đúng một cái sảnh chung cư.
    Bối cảnh phải là NƠI MẨU CHUYỆN NÀY XẢY RA, không phải nơi kênh này hay lui tới.
    Đưa nguyên lời thoại cho mô hình đọc — nó hiểu chuyện đang diễn ra ở đâu tốt hơn mọi bảng
    từ khoá tôi viết được.
    """
    if not keys:
        return ""
    try:
        import content_brain as CB
    except Exception:
        return ""
    thoai = " / ".join(str(c[0]) for c in cau[:6])
    # NGỮ CẢNH KÊNH PHẢI ĐI KÈM LỜI THOẠI.
    # Đo được: đưa mỗi lời thoại của CAR GUY ("That was before I opened it") thì AI hiểu là mở
    # thùng hàng và trả về "warehouse aisle beside an open shipping crate" — đọc đúng chữ nhưng
    # sai chuyện, vì lời thoại hài cố ý không nói ra bối cảnh (nói ra thì mất duyên).
    # Kèm nghề của hai nhân vật thì mô hình có đủ để hiểu "opened it" là mở nắp ca-pô.
    _nv = NHAN_VAT.get(k["de"])
    _ai = (f"Character A is {_nv[0][0]}, {_nv[0][2]}. Character B is {_nv[1][0]}, {_nv[1][2]}.\n"
           if _nv else "")
    hoi = (
        "You pick the background setting for one short 2D cartoon comedy scene.\n"
        f"{_ai}"
        f"Two characters talk. Dialogue: {thoai}\n\n"
        "Reply with ONE short English phrase (max 14 words) describing the exact physical place "
        "this conversation happens in. Be specific to the dialogue, not generic.\n"
        "Hard rules: no brand names, no proper nouns, no people in the scene, no text or signage, "
        "all packaging blank and unbranded. Describe a place and objects only.\n"
        "Reply with the phrase alone, nothing else."
    )
    for kk in xoay_key(keys):
        try:
            g = CB._genai(kk if isinstance(kk, str) else kk.get("key"))
            m = g.GenerativeModel("gemini-2.5-flash")
            t = " ".join(str(getattr(m.generate_content(hoi), "text", "") or "").split())[:130]
            t = t.strip().strip('"').strip("'").rstrip(".")
            if 8 <= len(t) <= 130:
                return t
        except Exception:
            continue
    return ""


def _ten_tep(k: dict) -> str:
    return k["ten"].replace(" ", "").lower()


# ══════════════════════════════════════════════════════════════════════════════════════════
# CÂU GU VẼ NỀN — MỘT CHỖ DUY NHẤT, DÙNG CHUNG CHO CẢ HAI BỘ
# ------------------------------------------------------------------------------------------
# 30/8 — Trước đây mỗi bộ tự viết một câu gu, và hai câu ấy trôi xa nhau: bộ hài được "classic
# American animated sitcoms" (ấm, giàu chi tiết), bộ dữ liệu bị "clean explainer animation, calm
# professional mood" (nhạt, ít chi tiết) vì tôi nghĩ kênh nghiêm túc thì nền phải điềm đạm hơn.
# Nghĩ thế là lẫn hai thứ: CHẤT của kênh nằm ở nội dung, ở nhạc, ở ký hiệu cảm xúc — KHÔNG nằm
# ở nét vẽ nền. Cùng một nét vẽ đẹp thì kênh nào cũng hưởng.
# Cố ý KHÔNG nhắc tên một bộ phim nào: "classic American animated sitcoms" là tên một DÒNG phim
# (đã có hàng chục sê-ri từ thập niên 1990), không phải tên một tác phẩm có bản quyền.
# Ép ảnh có SÀN ở một phần ba dưới khung — nếu không, ảnh chụp ngang tầm mặt bàn và nhân vật hoá
# ra đứng trên mặt bàn (luật 7aa).
SAN_NEN = ("wide shot, camera at standing eye level, floor clearly visible across the lower "
           "third, open space in the centre of the frame, no furniture blocking the middle")
# ══ CÂU CẤM CHỮ — MỘT BẢN DUY NHẤT CHO CẢ HAI BỘ ══════════════════════════════════════════
# 30/8 — anh gửi ảnh: "uabu", "5&iT", "CLARTUY" trên nền mười kênh hài. Câu cấm chữ ĐÃ có, nhưng
# nó tồn tại ở BA BẢN khác nhau trong hai tệp, và bản yếu nhất — thiếu hẳn "no shop signs, no
# window text" — lại là bản `kich_hai` đang chạy.
# Sáng nay tôi gộp hai bản bên `kich_v2` và tưởng đã xong. Bản thứ ba vẫn ngồi đây, vì tôi sửa
# tệp mình đang mở chứ không đi tìm mọi chỗ cùng dạng — đúng lỗi luật 7bf mô tả, tái phạm trong
# cùng một ngày. Nay chỉ còn MỘT hằng, và `kich_v2` mượn từ đây.
CAM_CHU = (", no signs on walls, no lettering anywhere in the scene, no shop signs, "
           "no window text, no posters, no framed text, no labels on furniture, "
           "no numbers, no writing of any kind, blank walls")
CAM_BAO_BI = (", all packaging completely blank and unbranded, plain white and solid colour "
              "surfaces, no labels, no printed text on any package")

GU_NEN = ("flat 2D cartoon background in the style of classic American animated sitcoms, "
          "bold clean outlines, simple flat colours, no people, no text, no signage, "
          "wide establishing shot, slightly stylised perspective")


def _keo_sang(tep: str, san_den: float = 0.05, san_sang: int = 96) -> None:
    """Kéo một ảnh nền ra khỏi vùng tối, đo trước khi kéo.

    Hai ngưỡng, vì hai kiểu tối khác nhau:
      * `san_den`  — tỉ lệ điểm gần như đen. `cham_v4` chặn ở 8%; đặt sàn 5% để còn chỗ cho lớp
        phủ mỏng mà Remotion đặt lên trên (lớp ấy tối thêm khoảng 2 điểm phần trăm).
      * `san_sang` — độ sáng trung bình. Một ảnh có thể không có điểm đen nào mà vẫn xám xịt.

    Dùng gamma chứ không cộng thẳng: cộng thẳng làm bệt vùng sáng (trời, cửa sổ) thành mảng
    trắng phẳng, còn gamma kéo vùng tối lên mà gần như không đụng vùng đã sáng.
    """
    try:
        from PIL import Image, ImageEnhance
    except ImportError:
        return
    im = Image.open(tep).convert("RGB")
    px = list(im.convert("L").resize((160, 160)).getdata())
    den = sum(1 for v in px if v < 40) / len(px)
    tb = sum(px) / len(px)
    if den <= san_den and tb >= san_sang:
        return
    g = 1.0
    for _ in range(6):
        if den <= san_den and tb >= san_sang:
            break
        g += 0.18
        # TRẦN 250, KHÔNG PHẢI 255. Gamma kéo vùng tối lên nhưng cũng đẩy vùng đã sáng chạm
        # trần, và một mảng 255 phẳng lì ở góc chính là thứ `_nen_hong` coi là ảnh đóng khung —
        # tức là phép nâng sáng tự tạo ra lỗi cho phép kiểm bắt. Đo được ở carguy_2: góc trần
        # phòng thành (248 · lệch chuẩn 0,3) sau khi nâng.
        thu = im.point([min(250, int(255 * ((x / 255.0) ** (1.0 / g)))) for x in range(256)] * 3)
        px = list(thu.convert("L").resize((160, 160)).getdata())
        den = sum(1 for v in px if v < 40) / len(px)
        tb = sum(px) / len(px)
        im = thu
    # gamma làm nhạt màu; trả lại độ đậm để nền không đọc ra là ảnh bạc phếch
    im = ImageEnhance.Color(im).enhance(1.0 + (g - 1.0) * 0.5)
    im.save(tep, quality=90)


def ve_nen(k: dict, DS, keys, canh_tap: str = "") -> list:
    """Vẽ + CACHE ba nền cho một kênh. Trả đường dẫn tương đối trong `public/`.

    Chỉ vẽ tệp CHƯA CÓ. Đây là lý do bộ này chạy được kể cả ngày kho key cạn: sau lượt đầu, mọi
    video đều dùng lại đúng ba ảnh ấy."""
    os.makedirs(NEN, exist_ok=True)
    ra = []
    # NỀN THEO CHÍNH MẨU CHUYỆN NÀY — vẽ một lần, cache theo nội dung. Đặt TRƯỚC các nền cố định
    # nên nó là nền được dùng (xem `dung_luot`: một tập một địa điểm).
    if canh_tap:
        import hashlib as _hl
        _kh = _hl.md5(canh_tap.encode("utf-8")).hexdigest()[:8]
        rel = os.path.join("v4nen", f"{_ten_tep(k)}_t{_kh}.jpg")
        dest = os.path.join(PUB, rel)
        # 30/8 — anh soi ra chữ giả vẫn còn trên nền ("MATLE", "GYM", "PRICE") dù bộ dò chữ đã
        # nối vào sáng nay. Gốc rễ ở ngay dòng này: ảnh đã có trên đĩa thì trả về NGAY, không
        # qua bất kỳ phép kiểm nào. Gần mười một nghìn ảnh nền vẽ TRƯỚC khi có bộ dò, và tất cả
        # đi thẳng vào video mà không lần nào bị hỏi.
        # **Một cổng đặt sau bộ nhớ đệm thì nó chỉ gác những thứ chưa từng đi qua.**
        # Nay ảnh cache phải có DẤU ĐÃ KIỂM (`.ok` bên cạnh) mới được dùng thẳng; ảnh cũ không
        # có dấu thì bị dò một lần rồi ghi dấu — nên mỗi ảnh chỉ tốn một lượt hỏi, đúng một lần
        # trong đời nó.
        if os.path.exists(dest) and os.path.getsize(dest) > 20000:
            _dau = dest + ".ok"
            if not os.path.exists(_dau):
                if _co_chu(dest):
                    try:
                        os.remove(dest)
                    except OSError:
                        pass
                else:
                    io.open(_dau, "w").write("1")
        if os.path.exists(dest) and os.path.getsize(dest) > 20000:
            ra.append(rel)
        else:
            _gu = GU_NEN
            _them = ("" if not any(x in canh_tap.lower() for x in
                                   ("packet", "package", "box", "bottle", "carton", "label",
                                    "product", "shelf", "shelves", "brand", "snack", "grocer"))
                     else ", all packaging completely blank and unbranded, no printed text")
            _ok = None
            for _l in range(2):
                try:
                    import datastory_ci as _DC
                    _p = _DC._salt_prompt(f"{canh_tap}{_them}, {SAN_NEN}, {_gu}")
                except Exception:
                    _p = f"{canh_tap}{_them}, {SAN_NEN}, {_gu}"
                try:
                    _ok = DS._generate_image_ai(_p, dest, None, style=_gu)
                except Exception:
                    _ok = None
                if _ok and os.path.exists(dest) and os.path.getsize(dest) > 20000:
                    break
                _ok = None
            if _ok:
                try:
                    DS.nang_sang_anh(dest); _keo_sang(dest)
                    if _nen_hong(dest) or _co_chu(dest):
                        os.remove(dest); _ok = None
                except Exception:
                    pass
            if _ok and os.path.exists(dest):
                print(f"      🎨 nền theo mẩu chuyện xong")
                ra.append(rel)

    for i, prompt in enumerate(k["nen"]):
        rel = os.path.join("v4nen", f"{_ten_tep(k)}_{i}.jpg")
        dest = os.path.join(PUB, rel)
        # 30/8 — anh soi ra chữ giả vẫn còn trên nền ("MATLE", "GYM", "PRICE") dù bộ dò chữ đã
        # nối vào sáng nay. Gốc rễ ở ngay dòng này: ảnh đã có trên đĩa thì trả về NGAY, không
        # qua bất kỳ phép kiểm nào. Gần mười một nghìn ảnh nền vẽ TRƯỚC khi có bộ dò, và tất cả
        # đi thẳng vào video mà không lần nào bị hỏi.
        # **Một cổng đặt sau bộ nhớ đệm thì nó chỉ gác những thứ chưa từng đi qua.**
        # Nay ảnh cache phải có DẤU ĐÃ KIỂM (`.ok` bên cạnh) mới được dùng thẳng; ảnh cũ không
        # có dấu thì bị dò một lần rồi ghi dấu — nên mỗi ảnh chỉ tốn một lượt hỏi, đúng một lần
        # trong đời nó.
        if os.path.exists(dest) and os.path.getsize(dest) > 20000:
            _dau = dest + ".ok"
            if not os.path.exists(_dau):
                if _co_chu(dest):
                    try:
                        os.remove(dest)
                    except OSError:
                        pass
                else:
                    io.open(_dau, "w").write("1")
        if os.path.exists(dest) and os.path.getsize(dest) > 20000:
            _xau = _nen_hong(dest) or (_co_chu(dest) and 'còn chữ trong ảnh')
            if not _xau:
                ra.append(rel)
                continue
            print(f"      ♻️ nền {i} bỏ và vẽ lại: {_xau}")
            os.remove(dest)
        gu = GU_NEN
        # 29/8 — GỌI THẲNG `_generate_image_ai`, KHÔNG QUA `fetch_image`.
        # `fetch_image` chỉ vẽ khi có tham số `ai_key` truyền vào (`if ai_key and ...`), nên gọi
        # nó với `ai_only=True` mà không kèm khoá thì nó lặng lẽ trả None — đúng cảnh vừa gặp:
        # 169 khoá vẽ nằm sẵn trong pool mà cả ba nền đều "không vẽ được".
        # `_generate_image_ai` tự lấy khoá từ pool đã nạp (`set_ai_pool`) và tự xoay khoá khi một
        # khoá cạn, nên nó mới là tầng đúng cho việc chỉ-vẽ-chứ-không-tìm-ảnh-thật.
        # 30/8 — THỬ LẠI BA LƯỢT.
        # Đo được: 2 trong 17 nền hụt (rentpanic_1, gymlies_2), và kênh thiếu nền thì tụt điểm
        # ở trục "đủ ba nền phân biệt". Một lượt vẽ hỏng gần như luôn là khoá vừa cạn hoặc mạng
        # chập — lượt sau `_generate_image_ai` tự xoay sang khoá khác nên thường qua ngay. Nền
        # là thứ CACHE VĨNH VIỄN, nên chịu tốn thêm vài lượt thử ở đây là rẻ nhất: hỏng một lần
        # là kênh ấy nhàm mãi mãi.
        ok = None
        for _lan in range(3):
            try:
                # 30/8 — DÙNG LẠI BỘ CHỐNG-BỊA-CHỮ CỦA `datastory_ci`, ĐỪNG TỰ VIẾT LẠI.
                # Khung DIET WARS đo được một biển hiệu ghi "FATET" — máy vẽ thấy "fast food
                # restaurant" là dựng ngay một mặt biển hướng vào ống kính rồi điền chữ bịa vào.
                # Câu "no text" trong `gu` KHÔNG cứu được: mô hình khuếch tán không có khái niệm
                # "đừng", chỉ có "vẽ cái gì" — chú thích ở `_bo_mat_chu` đã ghi rõ sau ba vòng thử.
                # Cách đã kiểm chứng là BỎ HẲN CHỖ CHỮ CÓ THỂ XUẤT HIỆN (nhìn từ cạnh, quay lưng),
                # và nó nằm sẵn trong `_salt_prompt`. Bộ này tự viết prompt riêng nên vòng ngoài
                # bỏ sót nó — đúng họ lỗi "đã chữa một lần rồi để lối khác chạy qua".
                try:
                    import datastory_ci as _DC
                    _p = _DC._salt_prompt(f"{prompt}, {gu}")
                except Exception:
                    _p = f"{prompt}, {gu}"
                ok = DS._generate_image_ai(_p, dest, None, style=gu)
            except Exception as e:
                print(f"      ⚠️ nền {i} lượt {_lan+1}: {str(e)[:56]}")
                ok = None
            if ok and os.path.exists(dest) and os.path.getsize(dest) > 20000:
                _xau = _nen_hong(dest) or (_co_chu(dest) and 'còn chữ trong ảnh')
                if not _xau:
                    break
                print(f"      ♻️ nền {i} lượt {_lan+1} không dùng được: {_xau}")
                os.remove(dest)
            ok = None
        if ok:
            # NÂNG SÁNG THEO SỐ ĐO, KHÔNG NÂNG MÙ.
            # Nền tối (ga-ra, phòng gọi) kéo tỉ lệ điểm gần-đen lên 13% — quá ngưỡng 8% của
            # `cham_v4`. Sửa ở ĐÂY chứ không sửa bằng bộ lọc trong Remotion, vì ảnh nền được
            # cache dùng lại cho mọi tập sau: nâng một lần thì mọi tập đều sáng.
            try:
                DS.nang_sang_anh(dest)
                _keo_sang(dest)
            except Exception:
                pass
            ra.append(rel)
            print(f"      🎨 nền {i} xong")
        else:
            print(f"      ⚠️ nền {i}: không vẽ được — cảnh này dùng màu nền trơn")
            ra.append("")
    return ra


# ══════════════════════════════════════════════════════════════════════════════════════════
# BÓNG DÁNG HAI NHÂN VẬT — MỖI KÊNH MỘT CẶP KHÁC
# ------------------------------------------------------------------------------------------
# 30/8 — Bản trước dùng ĐÚNG MỘT cặp ghi đè cho cả mười kênh (thấp-đậm-đeo-kính ↔ cao-gầy).
# Nó chữa được lỗi "hai người trong một cảnh giống nhau", nhưng đẻ ra lỗi to hơn: mười kênh
# giờ có mười cặp GIỐNG HỆT NHAU. Xem mười khung cạnh nhau thì đọc ra ngay là một khuôn tô
# lại — đúng thứ anh dặn tránh ("10 channel thì phong cách nhân vật… ko chung chung 1 template").
#
# Nên bảng này giữ nguyên nguyên tắc (trong MỘT cảnh, hai bóng phải tương phản) nhưng cho mỗi
# kênh một KIỂU tương phản riêng: chỗ thì chênh chiều cao, chỗ chênh bề ngang, chỗ chênh tuổi
# (mắt to / hàm bạnh), chỗ đảo vai — người đeo kính là người bên phải chứ không phải bên trái.
# Cặp nào cũng tương phản mạnh, nhưng không cặp nào lặp lại cặp khác.
_BONG = {
    # rent: chủ nhà cao lớn tươi cười ↔ người thuê nhỏ bé
    "rent":     ({"cao": .92, "beNgang": 1.06, "kinh": True,  "rau": "",     "matTo": 1.14, "cam": .1, "ao": "#C0392B", "quan": "#3A4B6C", "kieuMui": "moc", "kieuMat": "bau", "kieuMay": "manh", "tiLeDau": 1.02},
                 {"cao": 1.14, "beNgang": .94, "kinh": False, "rau": "",     "matTo": .92,  "cam": .9, "ao": "#EFC24B", "quan": "#544836", "kieuMui": "cu", "kieuMat": "hep", "kieuMay": "day", "tiLeDau": 0.94}),
    # gym: học viên mềm oặt ↔ huấn luyện viên vai u thịt bắp
    "gym":      ({"cao": .96, "beNgang": 1.28, "kinh": True,  "rau": "",     "matTo": 1.0,  "cam": .2, "ao": "#1E6B50", "quan": "#275A4E", "kieuMui": "quap", "kieuMat": "tron", "kieuMay": "ru", "tiLeDau": 0.96},
                 {"cao": 1.06, "beNgang": 1.02, "kinh": False, "rau": "",     "matTo": .9,  "cam": 1.0, "ao": "#F2B33C", "quan": "#5C481E", "kieuMui": "hat", "kieuMat": "tron", "kieuMay": "manh", "tiLeDau": 1.1}),
    # airport: khách bay bơ phờ ↔ nhân viên quầy thẳng đơ
    "airport":  ({"cao": 1.02, "beNgang": .88, "kinh": False, "rau": "ria",  "matTo": 1.08, "cam": .35, "ao": "#24486E", "quan": "#324E70", "kieuMui": "nhon", "kieuMat": "hep", "kieuMay": "xech", "tiLeDau": 0.98},
                 {"cao": .94,  "beNgang": 1.14, "kinh": True, "rau": "",     "matTo": .9,   "cam": .75, "ao": "#E3D2A2", "quan": "#5A4E33", "kieuMui": "moc", "kieuMat": "bau", "kieuMay": "manh", "tiLeDau": 0.96}),
    # car: chủ xe gọn gàng ↔ thợ máy đô con
    "car":      ({"cao": 1.10, "beNgang": .90, "kinh": True,  "rau": "",     "matTo": 1.05, "cam": .25, "ao": "#A8432A", "quan": "#5D4336", "kieuMui": "hat", "kieuMat": "bau", "kieuMay": "manh", "tiLeDau": 1.06},
                 {"cao": .90,  "beNgang": 1.30, "kinh": False, "rau": "quai", "matTo": .88, "cam": .95, "ao": "#79AEC8", "quan": "#34505F", "kieuMui": "cu", "kieuMat": "hep", "kieuMay": "day", "tiLeDau": 0.92}),
    # office: nhân viên trẻ ↔ sếp đứng tuổi
    "office":   ({"cao": 1.04, "beNgang": .92, "kinh": False, "rau": "",     "matTo": 1.20, "cam": .05, "ao": "#3B2E5A", "quan": "#4D3E79", "kieuMui": "moc", "kieuMat": "xech", "kieuMay": "xech", "tiLeDau": 1.0},
                 {"cao": .96,  "beNgang": 1.18, "kinh": True,  "rau": "de",  "matTo": .86,  "cam": .85, "ao": "#D9A441", "quan": "#5B4727", "kieuMui": "cu", "kieuMat": "bau", "kieuMay": "day", "tiLeDau": 0.95}),
    # diet: người ăn kiêng gầy khô ↔ bạn thân ăn tất
    "diet":     ({"cao": 1.08, "beNgang": .82, "kinh": False, "rau": "",     "matTo": 1.10, "cam": .15, "ao": "#1D7A5F", "quan": "#205D54", "kieuMui": "nhon", "kieuMat": "tron", "kieuMay": "manh", "tiLeDau": 1.04},
                 {"cao": .94,  "beNgang": 1.34, "kinh": True,  "rau": "ria", "matTo": .94,  "cam": .7, "ao": "#F0AE93", "quan": "#644036", "kieuMui": "cu", "kieuMat": "hep", "kieuMay": "ru", "tiLeDau": 0.93}),
    # tech: người dùng luống tuổi ↔ tổng đài viên trẻ măng
    "tech":     ({"cao": .93,  "beNgang": 1.20, "kinh": True,  "rau": "quai", "matTo": .88, "cam": .9, "ao": "#24486E", "quan": "#2E4F76", "kieuMui": "quap", "kieuMat": "hep", "kieuMay": "ru", "tiLeDau": 0.91},
                 {"cao": 1.10, "beNgang": .88,  "kinh": False, "rau": "",    "matTo": 1.22, "cam": .05, "ao": "#F2A33C", "quan": "#66441F", "kieuMui": "hat", "kieuMat": "tron", "kieuMay": "manh", "tiLeDau": 1.12}),
    # parent: bố to bè ↔ con tuổi teen cao lêu nghêu
    "parent":   ({"cao": .95,  "beNgang": 1.26, "kinh": True,  "rau": "de",  "matTo": .9,   "cam": .95, "ao": "#8E3B4E", "quan": "#653B4C", "kieuMui": "cu", "kieuMat": "bau", "kieuMay": "day", "tiLeDau": 0.93},
                 {"cao": 1.16, "beNgang": .80,  "kinh": False, "rau": "",    "matTo": 1.26, "cam": .0, "ao": "#83C4A2", "quan": "#355543", "kieuMui": "hat", "kieuMat": "tron", "kieuMay": "xech", "tiLeDau": 1.12}),
    # neighbor: hàng xóm lùn tròn ↔ người mới dọn đến cao gầy
    "neighbor": ({"cao": .90,  "beNgang": 1.22, "kinh": True,  "rau": "ria", "matTo": .94,  "cam": .85, "ao": "#E0725A", "quan": "#693E33", "kieuMui": "cu", "kieuMat": "xech", "kieuMay": "day", "tiLeDau": 0.94},
                 {"cao": 1.12, "beNgang": .86,  "kinh": False, "rau": "",    "matTo": 1.16, "cam": .10, "ao": "#33305C", "quan": "#454182", "kieuMui": "nhon", "kieuMat": "bau", "kieuMay": "xech", "tiLeDau": 1.0}),
    # dating: người dùng chỉn chu ↔ bạn cùng phòng luộm thuộm
    "dating":   ({"cao": 1.06, "beNgang": .94,  "kinh": False, "rau": "",    "matTo": 1.18, "cam": .2, "ao": "#D96A3C", "quan": "#6B3F28", "kieuMui": "moc", "kieuMat": "tron", "kieuMay": "manh", "tiLeDau": 1.05},
                 {"cao": .98,  "beNgang": 1.16, "kinh": True,  "rau": "quai", "matTo": .96, "cam": .6, "ao": "#35566E", "quan": "#335066", "kieuMui": "nhon", "kieuMat": "hep", "kieuMay": "xech", "tiLeDau": 0.97}),
}


def xoay_key(keys, toi_da: int = 14):
    """Sinh lần lượt khoá để thử, bắt đầu từ một chỗ KHÁC NHAU mỗi lần gọi.

    30/8 — anh gửi hai khung và nói nền chưa mờ, chưa liên quan. Đào tới cùng thì hoá ra video
    **không có ảnh nền nào**, và lý do là bốn hàm gọi mô hình đều viết `for kk in list(keys)[:3]`
    — thử đúng BA khoá đầu trong một hồ **295 khoá**.
    Ba khoá đầu hôm nay: một cạn hạn mức ngày, một bị thu hồi, một sống. Nhưng hàm bỏ cuộc
    trước khi tới khoá sống, nên toàn bộ khâu vẽ nền chết lặng.
    Repo đã có luật "key cạn quota thì ĐỔI KEY, đừng giết luồng" và cả một cổng selftest cho
    nó — mà bốn hàm này không hưởng, vì chúng tự viết vòng lặp riêng.
    Hai việc hàm này làm:
      · thử tới `toi_da` khoá thay vì ba;
      · mỗi lần gọi bắt đầu từ một VỊ TRÍ khác, nên vài khoá hỏng ở đầu hồ không chặn mãi mọi
        lời gọi — thứ khiến lỗi trên trông như "mô hình không trả lời" thay vì "khoá hỏng".
    """
    ds = [k if isinstance(k, str) else (k or {}).get("key") for k in (keys or [])]
    ds = [k for k in ds if k]
    if not ds:
        return
    xoay_key._i = (getattr(xoay_key, "_i", 0) + 1) % max(1, len(ds))
    for j in range(min(toi_da, len(ds))):
        yield ds[(xoay_key._i + j) % len(ds)]


def _co_chu(tep: str, keys=None) -> bool:
    """Ảnh này có chữ không? Trả True nếu CHẮC là có.

    30/8 — chú thích cũ ở `_nen_hong` tự nhận "chữ bịa thì không đo được nếu không có bộ nhận
    chữ". Câu ấy sai, và sai theo kiểu tốn kém nhất: **bộ nhận chữ nằm ngay trong nhà**. Đường
    vision đã chạy cho việc khác từ lâu. Tôi đã tự thuyết phục mình rằng không đo được, rồi ghi
    lý do ấy thành chú thích — nên lần sau đọc lại, chính tôi cũng tin.
    Anh nói đúng chỗ: *"1 là generate đúng, 2 là không nên có text"*. Lời cấm trong prompt là
    cách thứ nhất và nó có ngày trượt; cách thứ hai phải là ĐO RỒI LOẠI.

    HAI ĐIỀU ĐO ĐƯỢC KHI THỬ, và cả hai đổi hẳn cách viết hàm này:
      · **Không phải model vision nào cũng đọc được chữ.** Thử trên đúng khung có "COMPANT":
        `llava-1.5-7b` của CF trả NO — nó không đọc nổi cả dòng phụ đề trắng to giữa màn hình.
        Gemini trả YES ngay. Nên thứ tự hỏi phải theo ĐỘ TIN CẬY ĐỌC CHỮ, không theo độ sẵn có;
        hỏi một model không đọc được chữ thì câu trả lời "không có chữ" là vô nghĩa, mà tệ hơn
        nữa, nó đọc ra như một lời bảo đảm.
      · **Ảnh phải thu nhỏ.** Gửi nguyên tấm 1024px thì Groq từ chối thẳng ("reduce the length
        of the messages") — mất luôn 83 key khỏi cuộc chơi. Thu về 560px thì vừa đủ đọc chữ
        trên biển hiệu mà vẫn lọt cửa.
    """
    try:
        from PIL import Image
        import content_brain as CB
    except Exception:
        return False
    try:
        im = Image.open(tep).convert("RGB")
        if max(im.size) > 560:
            r = 560 / max(im.size)
            im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))))
        bo = io.BytesIO(); im.save(bo, "JPEG", quality=82); dl = bo.getvalue()
    except Exception:
        return False

    ho = keys or _co_chu._ho
    if not ho:
        try:
            import the_he_2 as T2
            ho = [k.get("key") for k in (T2.keys_cuc_bo() or []) if k.get("key")]
        except Exception:
            ho = []
        _co_chu._ho = ho
    # Xếp theo độ tin cậy ĐỌC CHỮ, không theo số lượng key sẵn có.
    xep = ([k for k in ho if str(k).startswith("AIza")][:2]
           + [k for k in ho if str(k).startswith("gsk_")][:3]
           + [k for k in ho if str(k).startswith("cf:")][:2])
    hoi = ("Does this image contain ANY readable letters, words, numbers or writing anywhere — "
           "on walls, signs, screens, packaging or posters? Answer exactly one word: YES or NO.")
    for k in xep:
        try:
            g = CB._genai(k)
            r = g.GenerativeModel(CB.MODEL).generate_content(
                [hoi, {"mime_type": "image/jpeg", "data": dl}])
            t = str(getattr(r, "text", "") or "").strip().upper()
            if t.startswith("YES"):
                return True
            if t.startswith("NO"):
                return False
        except Exception:
            continue
    return False        # dò không được thì cho qua — chặn nhầm nền lành tốn hơn để lọt một tấm


_co_chu._ho = []        # nhớ hồ key giữa các lần gọi, khỏi đọc lại tệp bảy lần mỗi video


def _nen_hong(tep: str) -> str:
    """Nền này có dùng được không. Trả lý do hỏng, hoặc "" nếu lành.

    30/8 — Soi mắt 29 nền thì bắt được hai tấm hỏng mà `_keo_sang` không thấy: một tấm bị máy vẽ
    đóng khung ô-van, bốn góc TRẮNG TINH (ảnh nền có góc trắng thì trên video thành bốn mảng
    trắng chói ở mép), và một tấm còn chữ bịa trên biển hiệu. Soi mắt không phải cách chạy được
    hằng đêm, nên phép đo phải nằm ở đây.

    Đo bốn góc gần trắng ở đây. Chữ bịa nay đo ở `_co_chu` bằng đường vision — xem chú thích ở
    hàm ấy về việc chú thích cũ chỗ này đã sai suốt một thời gian dài.
    """
    try:
        from PIL import Image
    except ImportError:
        return ""
    im = Image.open(tep).convert("L")
    w, h = im.size
    o = max(6, min(w, h) // 24)
    goc = [im.crop((0, 0, o, o)), im.crop((w - o, 0, w, o)),
           im.crop((0, h - o, o, h)), im.crop((w - o, h - o, w, h))]
    # Dấu hiệu của khung ô-van là góc TRẮNG VÀ PHẲNG: nền giấy máy vẽ chừa lại không có sắc độ
    # nào cả. Phải đo cả độ lệch chuẩn, không chỉ độ sáng — một góc trời sáng cũng đạt 248 nhưng
    # nó có chuyển sắc (lệch chuẩn hàng chục), còn giấy chừa thì lệch chuẩn dưới 3.
    # Ngưỡng là HAI góc, không phải một: ảnh đóng khung bao giờ cũng trắng nhiều góc, còn một
    # góc cháy sáng đơn lẻ là chuyện thường của ảnh lành (đo được ở carguy_2 — một góc trần).
    trang = 0
    for g in goc:
        px = list(g.getdata())
        tb = sum(px) / len(px)
        lech = (sum((x - tb) ** 2 for x in px) / len(px)) ** 0.5
        if tb >= 248 and lech < 3:
            trang += 1
    if trang >= 2:
        return "góc trắng phẳng — máy vẽ đóng khung ô-van, mép video sẽ loé trắng"
    return ""


def _hai_bong(k: dict) -> tuple:
    """(ghi đè cho người A, ghi đè cho người B) của một kênh."""
    a, b = _BONG.get(k["de"], _BONG["neighbor"])
    return dict(a), dict(b)


def doc_hai_giong(cau: list, ga: tuple, gb: tuple, mp3_dest: str) -> tuple:
    """Đọc TỪNG LƯỢT bằng giọng riêng rồi ghép thành một tệp. Trả (tổng giây, mốc từ, mốc lượt).

    ── VÌ SAO PHẢI TÁCH TỪNG LƯỢT (30/8/2026) ──────────────────────────────────────────
    Bản trước đọc CẢ ĐOẠN bằng đúng một giọng — giọng của nhân vật A. Nên trong một bộ phim
    HAI NGƯỜI ĐỐI THOẠI, tai người xem nghe ra đúng MỘT người tự nói với mình suốt hai mươi
    giây. Đó là lỗi nặng nhất còn lại của bộ này, và nó giết thẳng cái làm nên tiếng cười: hài
    hai người sống bằng KHOẢNG CÁCH giữa hai giọng — một bên tin điều hợp lý, một bên nói ra
    điều có thật, và tai phải nghe ra ngay hai chất người khác nhau.

    Ghi chú cũ ngại việc này vì "cộng dồn mốc thời gian sai một nhịp là khẩu hình lệch cả nửa
    video". Nỗi lo đúng, cách tránh cũng đơn giản: **đừng tin số thời lượng do bộ đọc trả về** —
    giải mã từng đoạn ra WAV rồi ĐO độ dài thật của tệp WAV. WAV không nén nên độ dài là số mẫu
    chia tần số lấy mẫu, chính xác tuyệt đối; còn mp3 thì bộ mã hoá chèn thêm mẫu đệm ở đầu mỗi
    tệp và chính chỗ đệm ấy mới là nguồn của trôi nhịp.

    Và tách từng lượt còn XOÁ LUÔN một bài toán khác: ranh giới lượt thoại không phải suy ra
    bằng cách đếm từ nữa (xem luật 7t mục 3-4) — mỗi lượt LÀ một đoạn tiếng riêng, nên mốc đầu
    và mốc cuối của nó là số đo, không phải phép suy.

    Khoảng lặng chèn giữa các lượt: 0,16 giây cho nhịp thoại thường, 0,55 giây trước CÚ CHỐT.
    Khoảng lặng trước cú chốt là thứ làm cú chốt nổ — trong hài, tiếng cười rơi vào chỗ trống.
    """
    import tempfile
    import tts_karaoke as TTS

    tam = tempfile.mkdtemp(prefix="v4giong_")
    wavs, moc, tu = [], [], []
    tong = 0.0

    def _lang(giay: float):
        nonlocal tong
        w = os.path.join(tam, f"s{len(wavs)}.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                        "-i", "anullsrc=r=24000:cl=mono", "-t", f"{giay:.3f}", w],
                       capture_output=True, timeout=120)
        if os.path.exists(w):
            wavs.append(w)
            tong += _giay_wav(w)

    # ══ NGỮ ĐIỆU: MỖI CÂU MỘT NHỊP, MỘT CAO ĐỘ ══════════════════════════════════════════
    # 30/8 — Anh: *"cần có ngữ điệu lên xuống giọng khi nói"*.
    # Bản trước gán ĐÚNG MỘT cặp (nhịp, cao độ) cho cả sáu câu của một người. Nên câu hỏi, câu
    # bực, câu chốt đều đọc bằng một giọng phẳng — và giọng phẳng giết hài nhanh hơn cả kịch bản
    # dở, vì tai nghe ra ngay là máy đọc.
    # edge-tts nhận `rate` và `pitch` cho MỖI lượt gọi, mà bộ này đã tách mỗi câu một lượt gọi
    # (luật 7ac) — nên chỉ việc đưa cảm xúc của câu vào đó. Không tốn thêm gì.
    #   · bực   -> nhanh hơn, cao hơn      · buồn  -> chậm hơn, trầm hơn
    #   · ngạc nhiên -> cao vọt, hơi chậm  · nghi ngờ -> chậm, trầm nhẹ (nhấn nhá)
    #   · tự tin -> chậm, trầm (chắc nịch) · vui   -> nhanh, cao
    # CÚ CHỐT luôn CHẬM LẠI một nấc: người kể chuyện hài nào cũng hạ nhịp ở câu cuối để câu ấy
    # rơi xuống có trọng lượng.
    _DIEU = {
        "tuc":       (+10, +8), "buon":     (-12, -8), "bat_ngo": (+2, +16),
        "nghi_ngo":  (-8,  -4), "tu_tin":   (-6,  -6), "vui":     (+8, +10),
        "so":        (+12, +14), "trung_tinh": (0, 0),
    }

    def _dieu(rate0: str, pitch0: str, cx: str, la_chot: bool) -> tuple:
        """Cộng độ lệch cảm xúc vào nhịp/cao độ gốc của nhân vật."""
        dr, dp = _DIEU.get(cx or "trung_tinh", (0, 0))
        if la_chot:
            dr -= 10          # câu chốt chậm lại để rơi có trọng lượng
        try:
            r0 = int(str(rate0).replace("%", "").replace("+", "") or 0)
            p0 = int(str(pitch0).replace("Hz", "").replace("+", "") or 0)
        except Exception:
            return rate0, pitch0
        r, pp = max(-40, min(40, r0 + dr)), max(-40, min(40, p0 + dp))
        return (f"{r:+d}%", f"{pp:+d}Hz")

    for i, (chu, ai, _cx) in enumerate(cau):
        if i:
            # 30/8 — Anh: *"đoạn cuối videos vẫn hơi bị kéo dài"*. Khoảng lặng trước cú chốt hạ
            # từ 0,55 xuống 0,34 giây: vẫn đủ tách câu chốt khỏi câu trước, mà không còn thành
            # một quãng trống nghe ra là phim bị treo.
            _lang(0.34 if i == len(cau) - 1 else 0.16)
        v, rate, pitch = ga if ai == 0 else gb
        rate, pitch = _dieu(rate, pitch, _cx, i == len(cau) - 1)
        m = os.path.join(tam, f"{i}.mp3")
        d, subs, _ = TTS.synth(chu, m, voice=v, rate=rate, pitch=pitch)
        if not subs:
            raise RuntimeError(f"lượt {i} không có mốc từ")
        w0 = os.path.join(tam, f"{i}.raw.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", m, "-ar", "24000", "-ac", "1", w0],
                       capture_output=True, timeout=300)
        w = os.path.join(tam, f"{i}.wav")
        # Cắt đệm im lặng của bộ đọc, và NHỚ đã cắt bao nhiêu ở đầu — mọi mốc từ của đoạn này
        # phải trừ đi đúng chừng ấy, không thì khẩu hình chạy trước tiếng.
        bo_dau = _cat_lang(w0, w)
        if not os.path.exists(w):
            w = w0
            bo_dau = 0.0
        dw = _giay_wav(w)
        if not dw:
            raise RuntimeError(f"lượt {i} giải mã hỏng")
        # ══ MỐC LƯỢT LẤY TỪ MỐC TỪ, KHÔNG LẤY TỪ BIÊN ĐOẠN TIẾNG ═══════════════════════
        # 30/8 — Bản đầu lấy `(tong, tong + dw)` tức là NGUYÊN BIÊN của đoạn WAV. Nhưng edge-tts
        # tự chèn một quãng im lặng ở ĐẦU và CUỐI mỗi đoạn nó đọc. Dò khoảng lặng thật trong tệp
        # ghép cho thấy rõ: khe giữa lượt 1 và lượt 2 mình khai là 3,91 → 4,07 (0,16 giây), còn
        # tiếng thật im từ 2,92 tới 4,35 (1,42 giây).
        # Hậu quả: thẻ phụ đề nằm lại gần MỘT GIÂY sau khi người ta nói xong, rồi thẻ tiếp theo
        # bật lên sớm gần ba phần mười giây trước khi người kia mở miệng. Cỡ máy cũng đổi lệch
        # theo. Không lỗi nào làm render hỏng, nên nó im lặng trôi qua mọi cổng kiểm.
        # Mốc TỪ thì chính xác — edge-tts trả đúng lúc từng từ phát ra. Nên lượt lấy mốc từ chính
        # từ đầu và từ cuối của nó, và khoảng lặng giữa hai lượt trở thành khoảng lặng THẬT.
        # (`KichHai` đã biết cách giữ nguyên lượt vừa kết thúc khi rơi vào khe — xem luật 7af.)
        t0 = tong + max(0.0, float(subs[0].get("t", 0)) - bo_dau)
        tc = tong + max(0.0, float(subs[-1].get("t", 0)) - bo_dau) + float(subs[-1].get("d", 0))
        moc.append((round(t0, 3), round(min(tc + 0.12, tong + dw), 3)))
        for x in subs:
            tu.append({"t": round(tong + max(0.0, float(x.get("t", 0)) - bo_dau), 3),
                       "d": round(float(x.get("d", 0)), 3),
                       "w": str(x.get("w", "")), "si": i})
        wavs.append(w)
        tong += dw

    lst = os.path.join(tam, "ds.txt")
    io.open(lst, "w", encoding="utf-8").write(
        "\n".join("file '" + w.replace("'", "'\\''") + "'" for w in wavs))
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                        "-i", lst, "-ar", "24000", "-ac", "1", "-b:a", "96k", mp3_dest],
                       capture_output=True, text=True, timeout=600)
    if r.returncode or not os.path.exists(mp3_dest):
        raise RuntimeError((r.stderr or "ghép tiếng hỏng")[-160:])
    return round(tong, 3), tu, moc


def _cat_lang(w_vao: str, w_ra: str) -> float:
    """Cắt im lặng ở ĐẦU và CUỐI một đoạn WAV. Trả số giây đã cắt ở đầu (để dời mốc từ).

    30/8 — Đo được: sau khi tách đọc từng lượt, khe im lặng THẬT giữa hai câu là 1,0–1,5 giây,
    trong khi khe mình cố ý chèn chỉ 0,16. Phần dôi ra là đệm của edge-tts ở hai đầu mỗi đoạn.
    Sáu khe như thế là **sáu giây im lặng trong một phim hai mươi giây** — gần một phần ba thời
    lượng không có gì xảy ra. Hài sống bằng nhịp chặt; rời rạc thế này thì mỗi câu đứng một mình
    và cú va giữa hai người không còn.
    Nên cắt sạch đệm rồi tự chèn đúng khe mình muốn. Giữ lại 0,05 giây ở đầu và 0,10 ở cuối để
    câu không bị xén mất phụ âm bật (p, t, k) — những âm ấy có phần đầu rất nhỏ, cắt sát là nghe
    ra "…ay" thay vì "play".
    """
    try:
        r = subprocess.run(["ffmpeg", "-v", "info", "-i", w_vao,
                            "-af", "silencedetect=n=-42dB:d=0.05", "-f", "null", "-"],
                           capture_output=True, text=True, timeout=180)
    except Exception:
        return 0.0
    tong = _giay_wav(w_vao)
    dau, cuoi = 0.0, tong
    kh, cur = [], None
    for ln in (r.stderr or "").splitlines():
        m = re.search(r"silence_start: (-?[\d.]+)", ln)
        if m:
            cur = float(m.group(1))
        m = re.search(r"silence_end: ([\d.]+)", ln)
        if m and cur is not None:
            kh.append((cur, float(m.group(1))))
            cur = None
    if cur is not None:                       # im lặng kéo tới hết tệp
        kh.append((cur, tong))
    for a, b in kh:
        if a <= 0.02:
            dau = max(dau, b)
        if b >= tong - 0.02:
            cuoi = min(cuoi, a)
    dau = max(0.0, dau - 0.05)
    cuoi = min(tong, cuoi + 0.10)
    if cuoi - dau < 0.25:                     # đo hỏng: giữ nguyên còn hơn cắt mất câu
        return 0.0
    r2 = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{dau:.3f}", "-to", f"{cuoi:.3f}",
                         "-i", w_vao, "-ar", "24000", "-ac", "1", w_ra],
                        capture_output=True, timeout=180)
    if r2.returncode or not os.path.exists(w_ra):
        return 0.0
    return dau


def _giay_wav(w: str) -> float:
    """Độ dài THẬT của một tệp WAV, đọc từ ffprobe. Dùng WAV chứ không dùng mp3 vì mp3 có mẫu
    đệm ở đầu mỗi tệp, và chính chỗ đệm ấy làm mốc thời gian trôi khi ghép nhiều đoạn."""
    try:
        return float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", w],
            capture_output=True, text=True, timeout=60).stdout.strip() or 0)
    except Exception:
        return 0.0


# ══════════════════════════════════════════════════════════════════════════════════════════
# THUMBNAIL — TRÍCH TỪ CHÍNH VIDEO, KHÔNG VẼ MỚI
# ------------------------------------------------------------------------------------------
# 30/8 — Cả bộ hài lẫn bộ dữ liệu đang xuất video mà KHÔNG có thumbnail, trong khi đường đăng bài
# cần nó. Vẽ thumbnail bằng AI thì tốn hạn mức, mà hạn mức là thứ đã đo được là cạn sạch vào
# những ngày bận nhất.
#
# Không cần vẽ mới: khung ĐẸP NHẤT của một video hài đã nằm sẵn trong chính video đó — khung cận
# cảnh lúc cú chốt, khi khuôn mặt chiếm gần bốn phần mười màn hình và nét mặt đang ở đỉnh. Trích
# đúng khung ấy rồi đặt câu hook lên trên là ra một thumbnail nói đúng nội dung, tốn 0 hạn mức và
# 0 giây chờ mạng.
#
# Chữ đặt Ở NỬA TRÊN, vì nửa dưới là chỗ mặt nhân vật. Và có nền tối mờ sau chữ: chữ trắng viền
# đen trên khung sáng vẫn khó đọc ở cỡ thumbnail trong danh sách đề xuất.
def lam_thumb(video: str, hook: str, ten_kenh: str, mau: str, dest: str) -> bool:
    """Trích khung cận cảnh của video rồi đặt chữ hook lên. Trả True nếu xong."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False
    try:
        dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
            capture_output=True, text=True, timeout=60).stdout.strip() or 0)
    except Exception:
        return False
    if not dur:
        return False
    tam = dest + ".raw.png"
    # LẤY KHUNG Ở NHỊP ĐUÔI, không lấy ở giữa lượt chốt.
    # Thử lần đầu lấy ở 0,80 của phim: khung ấy CÓ SẴN phụ đề của video, và tên kênh mình đặt
    # thêm ở đáy đè chồng lên đúng thẻ phụ đề — hai lớp chữ chồng nhau, không đọc được lớp nào.
    # Nhịp đuôi (2,2 giây sau câu chốt) không còn phụ đề nào, mà cỡ máy vẫn là cỡ CẬN và nét mặt
    # người nghe đang ở đỉnh phản ứng — đúng khung đẹp nhất của cả video.
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0.5, dur - 1.2):.2f}", "-i", video,
                    "-vframes", "1", tam], capture_output=True, timeout=120)
    if not os.path.exists(tam):
        return False
    im = Image.open(tam).convert("RGB")
    W, H = im.size
    d = ImageDraw.Draw(im, "RGBA")

    def phong(cs):
        for f in ("/System/Library/Fonts/Supplemental/Impact.ttf",
                  "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
            if os.path.exists(f):
                try:
                    return ImageFont.truetype(f, cs)
                except Exception:
                    pass
        return ImageFont.load_default()

    # Xuống dòng theo BỀ RỘNG THẬT, không theo số ký tự — hai chuỗi cùng số ký tự có thể rộng
    # khác nhau tới 40%, và chữ tràn mép là lỗi đã gặp nhiều lần ở bộ 50 kênh.
    cs = int(W * 0.093)
    ft = phong(cs)
    rong = int(W * 0.86)
    tu, dong, hien = str(hook or "").split(), [], ""
    for w in tu:
        thu = (hien + " " + w).strip()
        if d.textlength(thu, font=ft) <= rong:
            hien = thu
        else:
            if hien:
                dong.append(hien)
            hien = w
    if hien:
        dong.append(hien)
    dong = dong[:3]

    y = int(H * 0.10)
    cao = int(cs * 1.18)
    d.rectangle([0, y - int(cs * 0.5), W, y + cao * len(dong) + int(cs * 0.3)], fill=(12, 14, 20, 165))
    for ln in dong:
        w = d.textlength(ln, font=ft)
        x = (W - w) / 2
        d.text((x, y), ln, font=ft, fill="#FFFFFF", stroke_width=max(6, cs // 9), stroke_fill="#12131A")
        y += cao

    # DẢI NHẬN DIỆN KÊNH Ở ĐÁY.
    # Bản đầu chỉ viết tên kênh bằng chữ nhỏ mang màu kênh, đặt lên giữa áo nhân vật — chữ chìm
    # hẳn, không đọc được ở cỡ thumbnail trong danh sách đề xuất. Mà chỗ đó mới là việc của nó:
    # người xem phải nhận ra "à, kênh này" trước khi kịp đọc câu hook.
    # Nên nó thành một DẢI có nền màu kênh, chữ tương phản chọn theo độ sáng của chính màu ấy
    # (nền sáng thì chữ đen, nền tối thì chữ trắng) — cùng phép tính tương phản đã dùng cho áo.
    ft2 = phong(int(W * 0.058))
    w2 = d.textlength(ten_kenh, font=ft2)
    ch = int(W * 0.082)
    cy = int(H * 0.935)
    d.rectangle([(W - w2) / 2 - int(W * 0.045), cy - int(ch * 0.28),
                 (W + w2) / 2 + int(W * 0.045), cy + int(ch * 0.98)],
                fill=mau, outline="#12131A", width=6)
    _c = str(mau or "#CCCCCC").lstrip("#")
    _r, _g, _b = (int(_c[i:i + 2], 16) for i in (0, 2, 4)) if len(_c) == 6 else (200, 200, 200)
    chu = "#12131A" if (0.299 * _r + 0.587 * _g + 0.114 * _b) > 150 else "#FFFFFF"
    d.text(((W - w2) / 2, cy), ten_kenh, font=ft2, fill=chu)

    im.save(dest, quality=92)
    try:
        os.remove(tam)
    except Exception:
        pass
    return True


def dung_luot(k: dict, nen: list, vong: int = 0, nen_luot: list | None = None) -> tuple:
    """Trả (danh sách lượt thoại, lời đọc ghép). Kịch bản bốc theo `vong` để mỗi tập một chuyện.

    ── MỘT TẬP = MỘT ĐỊA ĐIỂM (30/8/2026) ──────────────────────────────────────────────
    Anh: *"bối cảnh phải liên quan lời nói hành động, ko phải đang ở trong nhà nhảy qua ra
    ngoài đường được, ko logic"*. Đây là lỗi nặng nhất của bản trước và tôi đã tự tạo ra nó:
    để tránh "nền lặp lại nhàm chán", tôi cho nền đổi theo nhịp kịch — nhưng hai người đang
    nói với nhau thì KHÔNG dịch chuyển tức thời sang chỗ khác giữa câu. Chữa một lỗi thẩm mỹ
    bằng cách đẻ ra một lỗi logic là đổi chác lỗ.

    Đường đúng: **nền đứng yên suốt tập**, và sự đa dạng đến từ hai chỗ khác:
      · TRONG một tập — đổi CỠ MÁY (toàn · trung · cận) và nhân vật XÊ DỊCH chỗ đứng;
      · GIỮA các tập — mỗi kịch bản gắn cứng với một địa điểm riêng (`boi`), nên bốn tập của
        một kênh diễn ra ở bốn nơi khác nhau và không tập nào trông giống tập nào.
    Kịch bản và địa điểm vì thế đi liền một cặp: chuyện phòng giặt xảy ra ở phòng giặt,
    chuyện lốp xe xảy ra ở tiệm lốp. Không còn chỗ nào để nhảy địa điểm.
    """
    kho = KHO[k["de"]]
    kb = kho[vong % len(kho)]
    cau = kb["loi"]
    # Nền của CẢ TẬP — chọn một lần, dùng cho mọi lượt.
    nen1 = nen[kb["boi"] % len(nen)] if nen else ""
    nenLuot = nen_luot or []
    luot, loi = [], []
    n = len(cau)
    for i, (chu, ai, cx) in enumerate(cau):
        cuoi = i == n - 1
        l = {"s": 0.0, "e": 0.0, "ai": ai, "nar": chu,
             "camXuc": cx,
             # CẢM XÚC NGƯỜI NGHE — nửa còn lại của trò đùa. Trong hài thoại, mặt người nghe
             # thường buồn cười hơn câu của người nói.
             # 30/8 — Ở CÚ CHỐT, NGƯỜI NGHE PHẢI SỮNG, KHÔNG ĐƯỢC CƯỜI.
             # Bảng xoay vòng `i % 6` đặt "vui" vào đúng lượt cuối của kịch bản sáu lượt, nên cả
             # mười kênh đều kết thúc bằng một khuôn mặt đang cười. Đó là ngược hẳn nguyên tắc:
             # NGƯỜI NGHE CƯỜI THÌ KHÁN GIẢ KHÔNG CƯỜI — nhân vật đã cười hộ mất rồi, và cú chốt
             # hoá ra chỉ là một câu vui vẻ. Cái làm người ta bật cười là mặt SỮNG NGƯỜI: hàm rơi,
             # mắt trợn, chưa kịp hiểu chuyện gì vừa xảy ra.
             "camXucKia": ("bat_ngo" if cuoi else
                           ["nghi_ngo", "bat_ngo", "trung_tinh", "tuc", "buon", "nghi_ngo"][i % 6]),
             "cuChi": cu_chi_cua(chu, i, cuoi),
             # CỠ MÁY LÀ CHỖ TẠO NHỊP, thay cho việc đổi nền. Mở bằng toàn cảnh cho người xem
             # đọc ra đang ở đâu, siết dần vào khi câu chuyện leo thang, và cú chốt đóng cận
             # nhất — vì cú chốt nằm ở NÉT MẶT, không ở lời.
             "co": "rong" if i == 0 else ("can" if (cuoi or i == n - 2) else "trung"),
             # Nền của LƯỢT NÀY; thiếu thì lui về nền cố định của kênh.
             "nen": (nenLuot[i] if i < len(nenLuot) and nenLuot[i] else nen1),
             "chot": cuoi}
        if cuoi:
            l["sfx"] = SFX_CHOT
        elif SFX.get(i):
            l["sfx"] = SFX[i]
        luot.append(l)
        loi.append(chu)
    return luot, " ".join(loi), cau


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--nen", action="store_true", help="chỉ vẽ + cache nền, không render")
    # Thumbnail trích từ video ĐÃ CÓ, nên tách được thành một lượt riêng: đổi cách làm thumbnail
    # thì không phải dựng lại mười video (mỗi lượt dựng mất chừng mười lăm phút).
    ap.add_argument("--thumb", action="store_true", help="chỉ làm thumbnail từ video đã dựng")
    ap.add_argument("--kenh", default="")
    ap.add_argument("--vong", type=int, default=0)
    a = ap.parse_args()

    import datastory_ci as DS
    import the_he_2 as T2
    import tts_karaoke as TTS

    chon = KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [x for x in KENH if x["ten"].replace(" ", "").upper() in vt]
    if not chon:
        print("❌ không khớp kênh nào")
        return 2

    keys = None
    try:
        keys = T2.keys_cuc_bo() or None
        if keys:
            DS.set_ai_pool(keys, "V4")
    except Exception:
        pass

    if a.thumb:
        n = 0
        for k in chon:
            mp4 = os.path.join(GOC, "out", f"v4_{_ten_tep(k)}.mp4")
            if not os.path.exists(mp4):
                print(f"   ⏭ {k['ten']}: chưa có video")
                continue
            hook = KHO[k["de"]][a.vong % len(KHO[k["de"]])]["loi"][0][0]
            th = os.path.join(GOC, "out", f"v4_{_ten_tep(k)}.jpg")
            if lam_thumb(mp4, hook, k["ten"], k["mau"], th):
                print(f"   🖼  {k['ten']}: {os.path.basename(th)}")
                n += 1
            else:
                print(f"   ❌ {k['ten']}: không làm được")
        print(f"\n✅ {n}/{len(chon)} thumbnail")
        return 0

    ra = []
    for k in chon:
        ten = k["ten"]
        print(f"\n▶ {ten}", flush=True)
        # Cảnh nền chọn theo CHÍNH mẩu chuyện của tập này, không theo bảng cố định của kênh.
        _kb0 = KHO[k["de"]][a.vong % len(KHO[k["de"]])]["loi"]
        # MỘT NỀN CHO MỖI LƯỢT, cùng một địa điểm chỉ đổi góc nhìn (giữ luật 7x).
        _canhDS = canh_moi_luot_ai(k, _kb0, keys)
        for _i4, _c4 in enumerate(_canhDS):
            print(f"   🧭 {_i4+1}. {_c4[:60]}")
        # ══ MỘT BỐI CẢNH CHO CẢ TẬP — 30/8, sau khi anh gửi ba phim ngắn tham khảo ═══════
        # Đo trên chính ba phim ấy: 11 giây / **KHÔNG một lần đổi cảnh**; phim dài 18 giây có ba
        # lần, mà cả ba chỉ là đổi CỠ MÁY trong cùng một phòng khách. Hình của họ đơn giản hơn
        # của mình, có chỗ còn thô hơn — mà xem vào là hiểu ngay và cười ngay.
        #
        # Lý do không nằm ở chất lượng vẽ: **họ giữ khung yên để người xem nghe được lời.**
        # Mình đổi khung mỗi lượt nên người xem không kịp bám vào đâu, và mỗi cảnh chỉ sống hai
        # ba giây thì cảnh nào cũng lộ ra là yếu. Đổi cảnh liên tục KHÔNG che được hình yếu —
        # nó phơi hình yếu ra sáu lần thay vì một.
        #
        # Đây đảo ngược yêu cầu trước của anh ("nói hết một câu thì đổi nền"). Yêu cầu ấy sinh
        # ra từ triệu chứng ĐÚNG — anh thấy tĩnh và chán — nhưng nguyên nhân thì khác: cái tĩnh
        # đến từ nhân vật diễn nhạt, không từ nền đứng yên. Ba phim kia có nền bất động suốt mà
        # không giây nào tĩnh, vì nhân vật diễn liên tục.
        # Nhịp thị giác từ nay do CỠ MÁY và DIỄN XUẤT gánh, không do đổi địa điểm.
        # Vẽ ĐÚNG MỘT nền rồi phát cho mọi lượt. Số lượt lấy từ `_canhDS` — danh sách cảnh mô
        # hình vừa trả — chứ không từ `luot`, vì `luot` mãi dòng dưới mới dựng xong.
        _nenMot = ve_nen_moi_luot(k, DS, _canhDS[:1]) if _canhDS else []
        nenLuot = ([_nenMot[0]] * max(1, len(_canhDS))) if (_nenMot and _nenMot[0]) else []
        # Nền cố định của kênh làm đường lui cho lượt nào mô hình không trả hoặc vẽ hỏng.
        nen = ve_nen(k, DS, keys, "") if (not nenLuot or not all(nenLuot)) else []
        if a.nen:
            continue
        luot, loi, kb_cau = dung_luot(k, nen, a.vong, nenLuot)

        # GIỌNG: hai nhân vật, hai chất giọng. Đây là thứ làm đối thoại nghe ra là hai người.
        # ══ GIỌNG CHỌN THEO NHÂN VẬT, KHÔNG THEO KIỂU VẼ ═══════════════════════════════
        # 30/8 — Bản trước tra giọng theo `k["a"]`/`k["b"]` tức là theo KIỂU VẼ (nam_gay, bank,
        # hang_xom…). Kiểu vẽ nói về tóc và màu áo, không nói gì về tuổi hay tính cách — nên
        # Mrs. Vale 54 tuổi và Coach Bree 31 tuổi có thể trúng cùng một giọng, còn Hal 61 tuổi
        # thì nói bằng giọng thanh niên.
        # Nay tra theo `NHAN_VAT` (luật 7ao): tuổi quyết cao độ, tính cách quyết nhịp.
        #   · nhiều tuổi hơn  -> cao độ thấp hơn, nhịp chậm hơn
        #   · "hào hứng/nhanh" -> nhịp nhanh, cao độ cao;  "khô/đều" -> nhịp chậm, cao độ phẳng
        GIONG_KENH = {
          # kênh:      (giọng A, rate, pitch),                    (giọng B, rate, pitch)
          "rent":     (("en-US-EricNeural",    "+14%", "+12Hz"), ("en-US-JennyNeural",   "-6%",  "-6Hz")),
          "gym":      (("en-US-SteffanNeural", "-8%",  "-14Hz"), ("en-US-AvaNeural",     "+16%", "+16Hz")),
          "airport":  (("en-US-GuyNeural",     "-2%",  "-6Hz"),  ("en-US-MichelleNeural","-10%", "-2Hz")),
          "car":      (("en-US-EricNeural",    "+10%", "+10Hz"), ("en-US-ChristopherNeural", "-12%", "-18Hz")),
          "office":   (("en-US-AriaNeural",    "+6%",  "+4Hz"),  ("en-US-BrianNeural",   "+2%",  "-8Hz")),
          "diet":     (("en-US-AvaNeural",     "+8%",  "+8Hz"),  ("en-US-SteffanNeural", "-10%", "-16Hz")),
          "tech":     (("en-US-ChristopherNeural", "-14%", "-16Hz"), ("en-US-EricNeural","+6%",  "+10Hz")),
          "parent":   (("en-US-GuyNeural",     "-8%",  "-16Hz"), ("en-US-AnaNeural",     "+18%", "+18Hz")),
          "neighbor": (("en-US-ChristopherNeural", "-6%", "-12Hz"), ("en-US-MichelleNeural", "+4%", "+4Hz")),
          "dating":   (("en-US-BrianNeural",   "+10%", "+8Hz"),  ("en-US-RogerNeural",   "-4%",  "-10Hz")),
        }
        # ══ BÓNG DÁNG RIÊNG — THỨ THAY CHO MÀU ÁO ═════════════════════════════════════
        # Anh: *"10 channel chưa có phong cách nhân vật riêng đặc trưng vẫn hơi na ná nhau"*.
        # Với nhân vật có khối thì lời than ấy đúng mà khó chữa: mười kênh dùng chung một khuôn
        # mặt, chỉ khác màu áo — mà màu áo là thứ mắt nhận ra SAU CÙNG, sau dáng và sau bóng.
        # Người que lật ngược bài toán: nó KHÔNG CÓ màu áo để dựa, nên buộc phải phân biệt bằng
        # đúng thứ mắt đọc trước — BÓNG DÁNG. Sáu trục dưới đây đều nhìn thấy được ở cỡ nhỏ và
        # ở một phần tư giây: tóc · mũ · kính · râu · cà vạt · dáng cao thấp.
        # Hai mươi người, hai mươi tổ hợp, không ai trùng ai.
        _NHAN_DANG = {
          #  kênh:     ( người A                                     , người B )
          "rent":     (dict(kieuToc="roi",       caVat=""),            dict(kieuToc="bui",  caVat="")),
          "gym":      (dict(kieuToc="ngan", kinh=True),                dict(kieuToc="duoi_ngua", mu="luoi_trai")),
          "airport":  (dict(kieuToc="hoi",  rau="ria"),                dict(kieuToc="bob",  caVat="#2E4A6B")),
          "car":      (dict(kieuToc="xoan"),                           dict(kieuToc="trocs", mu="luoi_trai", rau="quai")),
          "office":   (dict(kieuToc="duoi_ngua", kinh=True),           dict(kieuToc="hoi",  caVat="#7A2E2E")),
          "diet":     (dict(kieuToc="bob"),                            dict(kieuToc="xoan", rau="de")),
          "tech":     (dict(kieuToc="trocs", kinh=True, rau="quai"),   dict(kieuToc="ngan", caVat="#2F5B45")),
          "parent":   (dict(kieuToc="ngan", rau="de"),                 dict(kieuToc="duoi_ngua")),
          "neighbor": (dict(kieuToc="hoi",  rau="ria", kinh=True),     dict(kieuToc="bui")),
          "dating":   (dict(kieuToc="xoan", caVat="#5A3E7A"),          dict(kieuToc="roi",  kinh=True)),
        }
        # Nghề hiện lên người — anh dặn riêng cho bộ dữ liệu, nhưng bộ hài cũng cần: một huấn
        # luyện viên và một hội viên trông giống hệt nhau thì nửa trò đùa mất chỗ dựa.
        # Chỉ gán ở kênh mà nhân vật CÓ nghề rõ. Hai người bạn cãi nhau về ăn kiêng thì không có
        # đồng phục nào cả, và gán bừa một cái áo blouse cho họ là làm hỏng chứ không phải làm
        # rõ — phụ kiện chỉ có giá trị khi nó NÓI ĐÚNG một điều về người mang nó.
        _NGHE = {
          "rent":     ("", "the_deo"),      "gym":      ("", "khan_quang"),
          "airport":  ("", "the_deo"),      "car":      ("", "ao_blouse"),
          "office":   ("the_deo", "no_buom"), "tech":   ("", "the_deo"),
          "neighbor": ("", ""),            "diet":     ("", ""),
          "parent":   ("", ""),            "dating":   ("", ""),
        }
        for _b, _pk in zip(_BONG.get(k["de"], ({}, {})), _NGHE.get(k["de"], ("", ""))):
            if _pk:
                _b["phuKien"] = _pk
        for _b, _nd in zip(_BONG.get(k["de"], ({}, {})), _NHAN_DANG.get(k["de"], ({}, {}))):
            _b.update(_nd)

        # Ép hình theo bảng giới tính. Làm ở đây, một chỗ, thay vì đi sửa hai mươi dòng `_BONG`
        # — sửa tay thì lần thêm kênh thứ mười một lại quên, còn ép ở đây thì không quên được.
        for _b, _g in zip(_BONG.get(k["de"], ({}, {})), GIOI.get(k["de"], ("nam", "nam"))):
            # Truyền `gioi` xuống engine — nó quyết bề ngang vai, độ nở hông và cỡ đầu, tức là
            # những thứ đọc được từ xa. Trước đây bảng này chỉ dùng để XOÁ râu cho nhân vật nữ:
            # sửa được một lỗi thô, mà không giải được việc "nhìn là biết nam hay nữ".
            _b["gioi"] = _g
            if _g == "nu":
                _b["rau"] = ""
                # Nữ mà tóc ngắn kiểu nam là mất luôn dấu hiệu đọc-từ-xa mạnh nhất. Ép sang một
                # kiểu tóc dài nếu bảng chưa chọn kiểu nào thuộc nhóm nữ.
                if _b.get("kieuToc") not in ("duoi_ngua", "bui", "bob", "xoan"):
                    _b["kieuToc"] = "bob"
            else:
                _b.setdefault("kieuToc", "ngan")

        ga, gb = GIONG_KENH.get(k["de"], (("en-US-GuyNeural", "+4%", "+0Hz"),
                                          ("en-US-JennyNeural", "+2%", "+6Hz")))
        rel = f"v4_{_ten_tep(k)}.mp3"
        mp3 = os.path.join(PUB, rel)
        try:
            dur, tu, moc = doc_hai_giong(kb_cau, ga, gb, mp3)
        except Exception as e:
            print(f"   ❌ giọng đọc hỏng: {str(e)[:90]}")
            continue
        if not tu:
            print("   ❌ không có mốc từ — BỎ")
            continue

        # 30/8 — MỐC LƯỢT LÀ SỐ ĐO, KHÔNG CÒN LÀ PHÉP SUY.
        # Trước đây phải ghép mốc bằng cách đếm từ (luật 7t mục 3-4) vì cả đoạn chỉ có MỘT tệp
        # tiếng. Nay mỗi lượt là một đoạn tiếng riêng nên `doc_hai_giong` trả thẳng mốc đầu/cuối
        # của từng lượt — đo được, không đoán. Cả một họ lỗi (rớt đuôi câu, gán nhầm người nói)
        # biến mất theo.
        for i2, l in enumerate(luot):
            l["s"], l["e"] = moc[i2]
        if luot:
            # NHỊP ĐUÔI SAU CÚ CHỐT — sau câu chốt là một quãng không ai nói gì, chỉ còn nét mặt
            # người nghe. Trong hài, tiếng cười rơi vào đúng quãng ấy; cắt phim ngay ở từ cuối là
            # cắt mất chỗ khán giả cười.
            # ══ NHỊP ĐUÔI CỐ ĐỊNH 1,2 GIÂY — KHÔNG CO GIÃN NỮA ══════════════════════════
            # 30/8, sửa lần hai. Anh: *"đoạn cuối clip đang bị hơi dài ko có ý nghĩa, nhân vật
            # đứng yên"*. Đúng, và đây là lỗi TÔI TỰ TẠO RA: bản trước cho nhịp đuôi giãn tới
            # 5 giây để bù độ dài cho đủ "sàn 15 giây của short".
            #
            # Cái sàn ấy là thứ CHÍNH TÔI BỊA RA. YouTube Shorts không có độ dài tối thiểu; tôi
            # viết 15 giây vào `cham_v4` rồi sau đó kéo dài phim để chiều con số của chính mình.
            # Đó là **tối ưu cho cây thước thay vì cho người xem** — loại sai lầm tệ nhất, vì nó
            # làm sản phẩm xấu đi mà bảng điểm lại đẹp lên.
            #
            # Nhịp đuôi thật chỉ cần đủ cho cú giật mình chạy hết: 1,2 giây. Dài hơn là chết hình,
            # và trên Shorts (phát lặp vô hạn) thì mỗi vòng lặp khán giả phải ngồi qua đúng quãng
            # trống ấy trước khi được nghe lại câu mở.
            # Nhịp đuôi 1,2 → 0,85 giây. Anh: *"đoạn cuối videos vẫn hơi bị kéo dài"*. Cú giật
            # mình của người nghe nổ trong khoảng 0,6 giây đầu; phần còn lại chỉ là chờ. Trên
            # Shorts phát lặp vô hạn, mỗi phần mười giây thừa là mỗi vòng lặp khán giả phải ngồi
            # qua trước khi được nghe lại câu mở.
            luot[-1]["e"] = round(max(luot[-1]["e"], dur) + 0.85, 2)

        # 30/8 — ÉP HAI NGƯỜI KHÁC BÓNG DÁNG.
        # Mười kiểu gốc khác nhau ở tóc và màu áo, nhưng vài kiểu cùng đeo kính và cùng để ria:
        # khung đo được hai nhân vật đọc ra như anh em sinh đôi đổi màu áo. Trong phim hoạt hình
        # Mỹ, hai người trong một cảnh luôn tương phản ở BÓNG — một cao gầy một thấp đậm — vì
        # người xem nhận ra ai đang nói qua hình dáng trước cả khi nhìn mặt.
        tuyA, tuyB = _hai_bong(k)
        # ══ NHẠC NỀN — MỖI KÊNH MỘT BẢN, KHÔNG KÊNH NÀO CHUNG ═══════════════════════════
        # 30/8 — Bộ này đang phát ra video KHÔNG CÓ NHẠC: chỉ có hai giọng nói trên nền im lặng
        # tuyệt đối. Trong hài, khoảng lặng chỉ "nổ" nếu có gì đó để nó cắt vào; im lặng trên nền
        # im lặng thì không đọc ra là nhịp, chỉ đọc ra là thiếu tiếng. Đây là một phần của câu
        # anh hỏi: "sao hook hay viral người coi nhận ra được tiếng cười funny trong đó".
        # Nhạc lấy từ kho có sẵn trong `public/music` (không tốn hạn mức nào), mở rất nhỏ (0,07)
        # để không đè giọng, và MỖI KÊNH MỘT BẢN — hai kênh chung một bản nhạc là thứ `selftest`
        # của bộ 50 kênh đã chặn từ lâu, vì nghe giống nhau là dấu hiệu "sản xuất hàng loạt".
        NHAC = {"rent": "music/forecast.mp3", "gym": "music/km_undaunted.mp3",
                "airport": "music/mind_pad32.mp3", "car": "music/km_interloper.mp3",
                "office": "music/wallpaper.mp3", "diet": "music/carefree.mp3",
                "tech": "music/mindloop_pad.mp3", "parent": "music/inspired.mp3",
                "neighbor": "music/km_ascending.mp3", "dating": "music/km_reawakening.mp3"}
        # ══ ĐẠO CỤ — MỖI NGƯỜI MỘT VẬT, NÓI NGAY NHÂN VẬT LÀ AI ═════════════════════════
        # 30/8 — Clip anh gửi cho thấy trò đùa nằm ở HÀNH ĐỘNG: người bố lục ghế sofa rồi giơ
        # cái điều khiển lên. Không cần một câu thoại nào cũng hiểu. Bộ của mình thì hai người
        # đứng nói suông — mọi trò đùa dồn vào chữ, mà chữ thì phải ĐỌC mới hiểu, trong khi khán
        # giả lướt short quyết định ở hai giây đầu bằng MẮT.
        # Một cái cờ-lê trên tay thợ máy làm ba việc cùng lúc: nói ngay đây là thợ máy · cho tay
        # một việc để làm nên tay không buông thõng · và ở cú chốt là thứ để chìa ra.
        # Chỉ gán cho MỘT người mỗi kênh: hai người cùng cầm đồ thì khung rối và mất tương phản.
        # ══ BỎ HẲN ĐẠO CỤ — 30/8, lần anh nhắc THỨ HAI ═══════════════════════════════════
        # Lần đầu anh nói *"tay cầm vật gì đó có vẻ không hợp lắm"*, tôi thu hẹp lại: chỉ hiện ở
        # lượt mở và lượt chốt. Anh xem lại vẫn thấy: *"tay vẫn còn cầm đồ gì đó trên tay"*, kèm
        # ảnh chụp một bàn tay cầm cái gì đó màu cam-nâu không đọc ra được là vật gì.
        #
        # Ảnh ấy chỉ đúng ra gốc rễ, và gốc rễ không nằm ở CHỖ đạo cụ xuất hiện mà ở CHÍNH NÓ:
        # đạo cụ vẽ bằng vài hình vector đơn giản. Ở toàn cảnh nó bé nên qua được; ở cỡ CẬN nó
        # phóng to gấp đôi và lộ ra là một cục màu vô nghĩa nằm trong lòng bàn tay. Không có
        # ngưỡng "hiện ít hơn" nào cứu được điều đó — một hình vẽ không đọc được thì hiện một
        # giây cũng là một giây khán giả phải đoán.
        #
        # Vẽ đạo cụ đủ chi tiết để chịu được cỡ cận là một việc khác hẳn về quy mô, và nó không
        # nằm trong thứ anh đang cần. Bỏ hẳn thì tay được rảnh để diễn — mà cử chỉ tay mới là
        # thứ anh nhờ nâng cấp ngay từ đầu.
        # ══ ĐẠO CỤ QUAY LẠI, VÌ LÝ DO ĐÃ ĐỔI ═══════════════════════════════════════════
        # Bỏ hẳn đạo cụ hôm nay là đúng — với nhân vật CÓ KHỐI. Vật vẽ bằng vài hình vector đặc,
        # nằm trong một bàn tay có khối và có màu, ở cỡ cận phóng to thành cục màu không đọc ra
        # được là gì (anh chỉ hai lần).
        # Người que đổi hẳn điều kiện ấy: vật cũng vẽ bằng NÉT ĐEN như người, cùng một ngôn ngữ
        # hình, nên nó không còn cãi nhau với nhân vật. Đây không phải đổi ý — là cùng một
        # nguyên tắc ("đạo cụ phải cùng lối vẽ với nhân vật") cho ra kết luận khác khi lối vẽ
        # của nhân vật đã khác.
        # Vẫn giữ luật đã trả giá: chỉ hiện ở lượt MỞ và lượt CHỐT, không cầm suốt phim.
        VAT = {"rent": ("", "giay_to"), "gym": ("chai_nuoc", ""),
               "airport": ("ve_may_bay", ""), "car": ("", "co_le"),
               "office": ("coc", ""), "diet": ("", "banh"),
               "tech": ("", "coc"), "parent": ("", "dien_thoai"),
               "neighbor": ("", "ong_nhom"), "dating": ("dien_thoai", "")}
        _vA, _vB = VAT.get(k["de"], ("", ""))
        for _i3, _l3 in enumerate(luot):
            _hien = (_i3 == 0) or bool(_l3.get("chot"))
            _l3["vatA"] = _vA if _hien else ""
            _l3["vatB"] = _vB if _hien else ""
        props = {"luot": luot, "tu": tu, "voMp3": rel, "nhac": NHAC.get(k["de"], ""),
                 "kieuA": k["a"], "kieuB": k["b"], "kieuTuyA": tuyA, "kieuTuyB": tuyB,
                 "tieuDe": ten, "mucNen": k["mau"]}
        pj = os.path.join(GOC, "out", f"v4_{_ten_tep(k)}.json")
        os.makedirs(os.path.dirname(pj), exist_ok=True)
        io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))
        out = os.path.join(GOC, "out", f"v4_{_ten_tep(k)}.mp4")
        r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "KichHai", out,
                            f"--props={pj}", "--gl=swiftshader", "--log=error"],
                           cwd=ENG, capture_output=True, text=True, timeout=2400)
        if r.returncode or not os.path.exists(out):
            print(f"   ❌ render hỏng: {(r.stderr or r.stdout or '')[-190:]}")
            continue
        th = os.path.join(GOC, "out", f"v4_{_ten_tep(k)}.jpg")
        if lam_thumb(out, kb_cau[0][0] if kb_cau else ten, ten, k["mau"], th):
            print(f"   🖼  thumbnail: {os.path.basename(th)}")
        else:
            print("   ⚠️ không làm được thumbnail")
        print(f"   ✅ {ten}: {out}  ({os.path.getsize(out)/1e6:.1f} MB · {dur:.0f}s)")
        ra.append(out)

    print(f"\n{'✅' if ra else '⚠️'} {len(ra)}/{len(chon)} video")
    return 0 if ra or a.nen else 1


if __name__ == "__main__":
    sys.exit(main())
