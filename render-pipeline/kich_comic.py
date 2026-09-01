#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KỊCH COMIC — mười kênh hài dựng lại theo lối truyện tranh (31/8/2026)
════════════════════════════════════════════════════════════════════════════════════════════

Anh xem ba khung của bản hài cũ rồi bảo xoá đi làm lại. Ba khung ấy hỏng vì MỘT nguyên nhân
kiến trúc: bản cũ dán người vector lên ảnh AI. Chi tiết chẩn đoán nằm ở đầu `KichComic.tsx`.

Tệp này là nửa Python của bản mới. Nó CỐ Ý mỏng, và giữ nguyên bốn thứ đã tốt của bản cũ —
những thứ đã trả giá bằng nhiều vòng sửa và không dính dáng gì tới lỗi hình:

    · `KHO`            — bốn mươi mẩu thoại viết sẵn, đúng nhịp hài đối đáp Mỹ
    · `doc_hai_giong`  — mỗi lượt một giọng riêng, mốc thời gian ĐO từ WAV chứ không suy
    · `_hai_bong`      — bộ nhận dạng riêng của từng nhân vật, khoá theo kênh
    · `lam_thumb`      — ảnh bìa trích từ video đã dựng

Và bỏ đúng một thứ: `canh_nen_ai` cùng toàn bộ đường sinh ảnh nền. Nền nay do engine vẽ.
Bỏ nó lấy lại được ba thứ cùng lúc — hết lệch phong cách, hết nền không khớp thoại, và hết
phụ thuộc hạn mức ảnh của nhà cung cấp (một video comic không gọi API ảnh lần nào).

CHẠY TỰ ĐỘNG TRÊN GITHUB: mọi thứ ở đây chỉ cần `edge-tts` + `remotion`, không cần khoá ảnh,
không cần Claude Code. Cùng một lệnh chạy được ở máy anh và trong Actions.
"""
import os
import io
import json
import argparse
import subprocess
from chuan_am import chuan   # đưa âm lượng về mốc −14 LUFS của nền tảng

from kich_hai import (KENH, KHO, cu_chi_cua, doc_hai_giong, _ten_tep, lam_thumb,
                      _hai_bong, GOC, ENG, PUB)

# Giọng đọc — chép nguyên từ bản cũ. Mỗi kênh một cặp giọng khác nhau; hai kênh chung một cặp
# là dấu hiệu sản xuất hàng loạt mà bộ kiểm tra của 50 kênh đã chặn từ lâu.
GIONG_KENH = {
    "rent":     (("en-US-EricNeural", "+14%", "+12Hz"), ("en-US-JennyNeural", "-6%", "-6Hz")),
    "gym":      (("en-US-SteffanNeural", "-8%", "-14Hz"), ("en-US-AvaNeural", "+16%", "+16Hz")),
    "airport":  (("en-US-GuyNeural", "-2%", "-6Hz"), ("en-US-MichelleNeural", "-10%", "-2Hz")),
    "car":      (("en-US-EricNeural", "+10%", "+10Hz"), ("en-US-ChristopherNeural", "-12%", "-18Hz")),
    "office":   (("en-US-AriaNeural", "+6%", "+4Hz"), ("en-US-BrianNeural", "+2%", "-8Hz")),
    "diet":     (("en-US-AvaNeural", "+8%", "+8Hz"), ("en-US-SteffanNeural", "-10%", "-16Hz")),
    "tech":     (("en-US-ChristopherNeural", "-14%", "-16Hz"), ("en-US-EricNeural", "+6%", "+10Hz")),
    "parent":   (("en-US-GuyNeural", "-8%", "-16Hz"), ("en-US-AnaNeural", "+18%", "+18Hz")),
    "neighbor": (("en-US-ChristopherNeural", "-6%", "-12Hz"), ("en-US-MichelleNeural", "+4%", "+4Hz")),
    "dating":   (("en-US-BrianNeural", "+10%", "+8Hz"), ("en-US-RogerNeural", "-4%", "-10Hz")),
}

NHAC = {"rent": "music/forecast.mp3", "gym": "music/km_undaunted.mp3",
        "airport": "music/mind_pad32.mp3", "car": "music/km_interloper.mp3",
        "office": "music/wallpaper.mp3", "diet": "music/carefree.mp3",
        "tech": "music/mindloop_pad.mp3", "parent": "music/inspired.mp3",
        "neighbor": "music/km_ascending.mp3", "dating": "music/km_reawakening.mp3"}

# ══ HAI MÀU CỦA MỖI KÊNH ═══════════════════════════════════════════════════════════════
# 31/8 — `k["mau"]` KHÔNG PHẢI MÀU THƯƠNG HIỆU.
# Bản đầu của tệp này truyền thẳng `k["mau"]` xuống engine làm màu nhấn. Khung ra có tên kênh
# đọc được mà handle thì biến mất, và cả trang nhợt như ảnh phơi nắng. Lý do: `k["mau"]` của
# TECH SUPPORT là `#E9E6F4` — một màu tím trắng, vì trong bản cũ nó là MÀU NỀN DỰ PHÒNG
# (`mucNen`), thứ để lót sau nhân vật khi ảnh AI chưa tải xong. Dùng một màu nền làm màu chữ
# thì chữ nằm trên giấy trắng và không ai thấy.
#
# Đây là họ lỗi "mượn một giá trị cho việc nó không sinh ra để làm". Không có cách sửa nào ở
# chỗ dùng — phải có bảng riêng, và bảng ấy là đây. Mỗi kênh HAI màu ăn nhau (một ấm một
# lạnh), không kênh nào trùng kênh nào: một trang truyện tranh chịu được đúng hai màu mạnh.
MAU_CHINH = {"rent": "#E4572E", "gym": "#0FA36B", "airport": "#D64545", "car": "#2D6CDF",
             "office": "#7A5AF8", "diet": "#12A594", "tech": "#1F7AE0", "parent": "#EF6C3B",
             "neighbor": "#0E9F6E", "dating": "#E0367A"}
MAU_PHU = {"rent": "#1F7AE0", "gym": "#F2994A", "airport": "#2A9D8F", "car": "#F4A522",
           "office": "#10B981", "diet": "#EC4899", "tech": "#F97316", "parent": "#3B82F6",
           "neighbor": "#B45309", "dating": "#8B5CF6"}

# ══ NÉT RIÊNG CỦA TỪNG KÊNH ════════════════════════════════════════════════════════════
# Anh: *"sao cho 10 channel có nét riêng và phong cách riêng, và chuẩn USA"*.
# Đổi màu là chưa đủ — mười kênh cùng độ dày nét, cùng cỡ chấm halftone, cùng bo góc bong bóng
# thì vẫn đọc ra là MỘT xưởng vẽ tô mười bảng màu. Bốn trục dưới đây đổi CHẤT của nét, và mắt
# đọc chất trước khi kịp đọc màu:
#
#   net   — viền mực: 5 mảnh sạch (đời sống, hiện đại) .. 10 thô mạnh (báo biếm hoạ)
#   cham  — halftone: 7 mịn (in đẹp) .. 14 thô (báo giấy rẻ, kiểu tranh Lichtenstein)
#   bo    — bong bóng: 6 vuông đanh (gắt gỏng) .. 34 tròn hiền (nhẹ nhàng)
#   tile  — người cao bao nhiêu phần khung: 0.54 (thấy nhiều bối cảnh) .. 0.68 (áp sát, dồn nén)
#
# Mỗi kênh một tổ hợp, chọn theo CHẤT của chuyện chứ không bốc ngẫu nhiên: chuyện tiền nong thì
# nét gắt, chuyện hẹn hò thì nét mềm, chuyện hàng xóm rình nhau thì thô như tranh biếm.
# Ba trục BỐ CỤC riêng cho mỗi kênh — khác với bốn trục nét vẽ ở dưới. Anh: *"kiểu videos làm
# cũng thế"*: mười kênh cùng đặt bong bóng trên đầu, cùng khung vuông, cùng kêu "BOOM!" thì dù
# nét và màu khác nhau, mắt vẫn đọc ra một xưởng. Bốn kênh dùng lối bong bóng-DƯỚI (kiểu manga
# dịch): người ở nửa trên, lời ở đáy — một bố cục khác hẳn, không phải một biến thể.
BO_CUC_KENH = {
    "rent":     dict(duoi=False, bo=0,  no="BOOM!"),
    "gym":      dict(duoi=True,  bo=18, no="OOF!"),
    "airport":  dict(duoi=False, bo=6,  no="WELP!"),
    "car":      dict(duoi=True,  bo=0,  no="CLUNK!"),
    "office":   dict(duoi=False, bo=26, no="YIKES!"),
    "diet":     dict(duoi=True,  bo=22, no="NOPE!"),
    "tech":     dict(duoi=False, bo=10, no="BEEP!"),
    "parent":   dict(duoi=False, bo=24, no="WHAM!"),
    "neighbor": dict(duoi=True,  bo=4,  no="AH-HA!"),
    "dating":   dict(duoi=False, bo=28, no="OUCH!"),
}

# 31/8 — TỈ LỆ NGƯỜI HẠ XUỐNG ĐỂ BỐI CẢNH CÓ CHỖ.
# Anh nói ba lần "chưa nhận ra được bối cảnh gì", và sau khi sửa xong thước đo, vị trí, lớp —
# vẫn chưa rõ. Đo mới thấy ràng buộc thật: ở tỉ lệ 0,60 thì hai người chiếm 52% bề ngang và
# chỉ chừa 35% chiều cao phía trên đầu. Vật chủ đạo đặt đâu cũng bị che, và phần nền thấy được
# quá ít để đọc ra chỗ nào.
#
# Đây là ĐÁNH ĐỔI, không phải bản vá: mặt nhỏ đi khoảng một phần năm ở cảnh hai người, đổi lấy
# một nền đọc được. Cảnh CẬN (một người) vẫn giữ mặt to như cũ — nhịp rộng/cận vì thế còn rõ
# hơn trước, vì hai cỡ cảnh nay chênh nhau nhiều hơn.
NET_KENH = {
    "rent":     dict(net=9,  cham=13, bo=8,  tile=0.48),   # tiền nhà: gắt, thô, dồn nén
    "gym":      dict(net=7,  cham=8,  bo=20, tile=0.51),   # phòng tập: khoẻ, sát mặt
    "airport":  dict(net=6,  cham=10, bo=14, tile=0.44),   # sân bay: rộng, thấy nhiều bối cảnh
    "car":      dict(net=10, cham=14, bo=6,  tile=0.47),   # gara: thô nhất, vuông nhất
    "office":   dict(net=5,  cham=7,  bo=30, tile=0.45),   # văn phòng: mảnh, mịn, hiền
    "diet":     dict(net=6,  cham=9,  bo=34, tile=0.5),   # ăn kiêng: tròn trịa, gần
    "tech":     dict(net=7,  cham=11, bo=12, tile=0.47),   # kỹ thuật: vuông vắn vừa phải
    "parent":   dict(net=8,  cham=8,  bo=28, tile=0.49),   # làm cha mẹ: dày ấm, tròn
    "neighbor": dict(net=9,  cham=14, bo=10, tile=0.44),   # hàng xóm: biếm hoạ, thô, lùi xa
    "dating":   dict(net=5,  cham=7,  bo=32, tile=0.51),   # hẹn hò: mảnh mềm, sát mặt
}


# ══ VAI, QUAN HỆ, CHIỀU CAO, GIỌNG — MỘT BẢNG DUY NHẤT ═══════════════════════════════
# 31/8 — Anh: *"giọng nào nam thì lồng nam, nữ lồng nữ, con nhỏ lồng con nhỏ, ông già lồng
# giọng ông"* và *"con đứng với mẹ thì con phải thấp hơn mẹ, vợ đứng với chồng thì vợ thường
# thấp hơn chồng — nhớ logic nha e"*.
#
# Cả hai việc đều hỏng vì cùng một lý do: **giới và tuổi của nhân vật chưa từng được ghi vào
# dữ liệu.** Chúng chỉ nằm trong lời chú thích tiếng Việt phía trên mỗi kiểu vẽ ("nữ giao dịch
# viên", "thẩm phán về hưu"). Bộ chọn giọng không đọc được chú thích, nên giọng gán theo KÊNH
# rồi trượt khỏi nhân vật; bảng `_BONG` ghi đè chiều cao và râu cũng theo kênh, độc lập với
# giới — thành ra có nữ cựu công tố đeo râu dê, và ở PARENT MODE thì đứa con cao hơn bố.
#
# Bảng này là nguồn sự thật DUY NHẤT cho ba thứ đi liền nhau: ai là ai · cao thấp thế nào ·
# giọng nào. Tách chúng ra ba chỗ là cách chắc chắn để chúng lại mâu thuẫn lần nữa.
#
# Chiều cao lấy mốc nam trưởng thành = 1.00. Nữ trưởng thành 0.92–0.95, ông bà hơi còng 0.96–
# 0.99, trẻ con 0.62–0.70. Đây là quan hệ THẬT giữa hai người trong cùng khung, nên khán giả
# đọc ra quan hệ trước khi nghe câu đầu tiên.
VAI = {
    # 31/8 — VAI CÓ HAI TÊN: một tiếng Việt để tôi đọc, một tiếng Anh để HIỆN RA.
    # Bản đầu chỉ có tên tiếng Việt, và nó lọt thẳng vào tiêu đề YouTube: "When Khách Gọi Hỗ
    # Trợ Meets Nhân Viên Hỗ Trợ". Chú thích dành cho người viết code và nhãn dành cho người
    # xem là hai thứ khác nhau — trộn chung thì sớm muộn cũng rò ra mặt trước.
    #            A: (kiểu vẽ, giới, tuổi, cao, vai trò VN, vai trò EN)     B: (…)
    "rent":     (("luat_tre",  "nam", "tre",     0.97, "người thuê", "the tenant"),
                 ("cong_to",   "nu",  "trung",   0.94, "chủ nhà", "the landlord")),
    "gym":      (("khoa_hoc",  "nu",  "trung",   0.93, "học viên", "the member"),
                 ("hang_xom",  "nam", "trung",   1.06, "huấn luyện viên", "the trainer")),
    "airport":  (("vien_phi",  "nam", "trung",   1.02, "khách bay", "the passenger"),
                 ("y_ta",      "nu",  "trung",   0.93, "nhân viên quầy", "the gate agent")),
    "car":      (("bank",      "nu",  "trung",   0.93, "chủ xe", "the car owner"),
                 ("tham_phan", "nam", "gia",     1.04, "thợ máy già", "the old mechanic")),
    "office":   (("sao_dem",   "nu",  "tre",     0.94, "nhân viên trẻ", "the new hire"),
                 ("vu_tru_gia","nam", "gia",     1.01, "sếp đứng tuổi", "the boss")),
    "diet":     (("cong_to",   "nu",  "trung",   0.94, "người ăn kiêng", "the dieter"),
                 ("hang_xom",  "nam", "trung",   1.05, "bạn cùng nhà", "the roommate")),
    "tech":     (("hang_xom",  "nam", "trung",   1.03, "khách gọi hỗ trợ", "the caller"),
                 ("sao_dem",   "nu",  "tre",     0.92, "nhân viên hỗ trợ", "tech support")),
    # PARENT MODE là chỗ anh nêu đích danh: con phải thấp hơn mẹ. 0.66 so với 1.00 — chênh
    # đúng cỡ một đứa trẻ đứng cạnh người lớn, nhìn một giây là ra quan hệ.
    # 31/8 — Anh: *"này có phải là con nít đang vẽ lỗi ko, ko thấy cổ và thân người đầu quá to"*.
    # Đúng, và tôi đo được: đứa trẻ ra 1,2 "đầu" (đầu chiếm hơn nửa người) trong khi người lớn
    # là 4 đầu. Nguyên nhân: BA hệ số nhân chồng lên nhau mà tôi chỉ nhìn từng cái một —
    #   cao 0,66 ở bảng này  ×  0,74 mà engine nhân cho giới "tre"  = thân chỉ còn 0,49
    #   tiLeDau 1,22          ×  1,34 mà engine cũng nhân cho "tre" = đầu to gấp 1,63
    # Thân co lại còn đầu phình ra, hai chiều ngược nhau nên sai số nhân đôi.
    # Số dưới đây tính NGƯỢC từ mục tiêu: trẻ con hoạt hình đúng tỉ lệ là 3 đầu (đầu to hơn
    # người lớn theo tỉ lệ, nhưng không nuốt cả thân), sau khi đã tính cả hệ số của engine.
    "parent":   (("bank",      "nu",  "trung",   1.00, "mẹ", "mom"),
                 ("luat_tre",  "tre", "tre_con", 0.89, "con nhỏ", "the kid")),
    "neighbor": (("vu_tru_gia","nam", "gia",     0.99, "ông hàng xóm", "the neighbor"),
                 ("y_ta",      "nu",  "trung",   0.94, "hàng xóm nữ", "the woman next door")),
    # Vợ chồng — ví dụ thứ hai anh nêu. Vợ thấp hơn chồng, và cả hai cùng lứa.
    "dating":   (("luat_tre",  "nam", "tre",     1.04, "chồng", "the husband"),
                 ("sao_dem",   "nu",  "tre",     0.95, "vợ", "the wife")),
}

# Giọng chọn theo (giới, tuổi) của CHÍNH nhân vật, không theo kênh. Mỗi ô nhiều giọng để mười
# kênh không dùng lại một giọng — hai kênh chung một giọng là dấu hiệu sản xuất hàng loạt.
# 31/8 — CHỈ DÙNG GIỌNG CÓ THẬT. Bản đầu của bảng này ghi `DavisNeural` và `NancyNeural` —
# hai giọng KHÔNG tồn tại trong edge-tts. Triệu chứng không phải "tên giọng sai" mà là "TTS trả
# về rỗng", nên nhìn log thì tưởng hỏng mạng hoặc hỏng khoá. Danh sách thật của en-US chỉ có
# 13 giọng; dưới đây lấy đúng trong số ấy.
#   nam: Andrew Brian Christopher Eric Guy Roger Steffan
#   nữ:  Aria Ava Emma Jenny Michelle
#   trẻ em: Ana  (giọng trẻ con thật duy nhất — dùng đúng chỗ của nó)
GIONG_VAI = {
    ("nam", "tre"):    [("en-US-BrianNeural", "+8%", "+6Hz"), ("en-US-AndrewNeural", "+10%", "+8Hz")],
    ("nam", "trung"):  [("en-US-GuyNeural", "+2%", "-2Hz"), ("en-US-ChristopherNeural", "-4%", "-8Hz"),
                        ("en-US-EricNeural", "+4%", "+2Hz")],
    # Ông già: chậm hẳn và trầm hẳn. Hai trục cùng lúc mới ra tuổi; chỉ hạ cao độ thì nghe ra
    # là người trẻ đang giả giọng.
    ("nam", "gia"):    [("en-US-SteffanNeural", "-16%", "-22Hz"), ("en-US-RogerNeural", "-14%", "-18Hz")],
    ("nu", "tre"):     [("en-US-AvaNeural", "+12%", "+14Hz"), ("en-US-JennyNeural", "+8%", "+10Hz")],
    ("nu", "trung"):   [("en-US-AriaNeural", "+2%", "+2Hz"), ("en-US-MichelleNeural", "-4%", "-2Hz"),
                        ("en-US-EmmaNeural", "0%", "+4Hz")],
    ("nu", "gia"):     [("en-US-EmmaNeural", "-14%", "-12Hz")],
    ("tre", "tre_con"): [("en-US-AnaNeural", "+14%", "+24Hz")],
}

# Tóc phải hợp giới, nếu không thì mọi thứ khác đều vô nghĩa: một nhân vật nữ để tóc "ngắn nam"
# và đeo râu thì người xem đọc ra là nam, bất kể dữ liệu ghi gì.
# Lối vẽ của từng kênh — trục thứ tám tách mười kênh ra. Chia 4/3/3 và gán theo CHẤT của kênh:
# chuyện đời thường nhẹ nhàng thì nét mảnh, chuyện gắt gỏng thì nét dày, chuyện công sở khô
# khan thì hình khối góc cạnh.
LOI_VE_KENH = {
    "rent": "goc_canh", "gym": "mat_to", "airport": "goc_canh", "car": "mat_to",
    "office": "goc_canh", "diet": "net_manh", "tech": "mat_to", "parent": "mat_to",
    "neighbor": "net_manh", "dating": "net_manh",
}

TOC_HOP = {("nu", "tre"): "duoi_ngua", ("nu", "trung"): "bui", ("nu", "gia"): "bob",
           ("nam", "tre"): "re_ngoi", ("nam", "trung"): "ngan", ("nam", "gia"): "hoi",
           ("tre", "tre_con"): "roi"}


# ── SỐ ĐO ĐỌC TỪ ĐĨA, ĐƯA SANG ENGINE BẰNG PROPS ────────────────────────────────────────────
# Hai bảng dưới được tính MỘT LẦN bằng `huong_sang.py` / `can_nhac.py`; engine chỉ nhận con số.
# Không để engine tự đọc tệp: bước render trên Actions chỉ được chạm `staticFile`, và đo lại ở
# mỗi lượt render là tốn công cho một con số không bao giờ đổi.

def _bang(ten: str) -> dict:
    d = os.path.join(GOC, "..", "engine-remotion", "public", ten)
    try:
        return json.load(io.open(d, encoding="utf-8"))
    except Exception:
        return {}


def _sang_cua(anh: str):
    """Hướng sáng của ảnh nền đang dùng -> bóng nhân vật đổ cùng chiều với ảnh."""
    if not anh:
        return None
    return _bang("comic_nen/huong_sang.json").get(os.path.splitext(os.path.basename(anh))[0])


def _am_nhac(nhac: str) -> float:
    """Hệ số âm lượng riêng của tệp nhạc này.

    Mốc cũ là một hằng 0.16 dùng chung cho 10 tệp trải 26 dB — nên OFFICE nhạc gần bằng giọng
    còn DATING coi như câm. Không có số đo thì trả 0.16, giữ nguyên hành vi cũ.
    """
    if not nhac:
        return 0.16
    return float(_bang("music/am_luong.json").get(os.path.basename(nhac), 0.16))


def kho_cua_kenh(k: dict) -> list:
    """Kho mẩu của một kênh: viết tay TRƯỚC, sinh mới nối sau.

    Tách thành hàm để bước CHUẨN BỊ NỀN hỏi được đúng mẩu mà bước dựng sẽ dùng. Nếu hai bên tự
    tính riêng thì sớm muộn chúng lệch nhau, và triệu chứng là nền sinh cho nơi A trong khi
    thoại diễn ra ở nơi B — sai mà không có lỗi nào báo.
    """
    kho = list(KHO[k["de"]])
    try:
        _kt = os.path.join(GOC, "kho_comic.json")
        if os.path.exists(_kt):
            _k2 = json.load(io.open(_kt, encoding="utf-8"))
            for _m in _k2.get("mau", {}).get(k["de"], []):
                kho.append({"boi": 0, "loi": [tuple(c) for c in _m["loi"]],
                            "noi": _m.get("noi", ""), "hook": _m.get("hook", "")})
    except Exception as e:
        # Không nuốt: kho hỏng mà lặng lẽ bỏ qua thì hệ âm thầm quay về vòng lặp bốn mẩu, và
        # triệu chứng duy nhất là "sao dạo này video giống nhau thế".
        print(f"   ⚠️ kho sinh không đọc được, chỉ dùng kho viết tay: {str(e)[:70]}")
    return kho


def mau_cua_tap(k: dict, vong: int) -> tuple:
    """(mẩu, câu thoại) của tập `vong` — dùng chung cho bước chuẩn bị nền và bước dựng."""
    kho = kho_cua_kenh(k)
    kb = kho[vong % len(kho)]
    return kb, kb["loi"]


def noi_va_nen(k: dict, kb: dict, cau: list, vong: int) -> tuple:
    """Nơi chốn của mẩu này -> (chỉ số nơi, đường dẫn ảnh nền). Nguồn DUY NHẤT cho cả ngắn+dài.

    Thứ tự có ý nghĩa và đã từng đặt sai: nơi chốn phải chốt TRƯỚC khi chọn nền. Bản cũ tính
    `_NOI_IDX` mười mấy dòng SAU chỗ dùng nó, nên nhánh chọn nền theo nơi chết hẳn và cả 86/306
    mẩu có nhãn nơi đều rơi về "mượn nền theo số tập". Python không báo gì vì biến đã có sẵn
    giá trị -1 (mục 22.5).

    Ba tầng, theo thứ tự tin cậy giảm dần:
      1. nhãn `noi` của mẩu, nếu khớp danh sách nơi của kênh;
      2. SUY TỪ LỜI THOẠI — câu nào nhắc "server", "front desk", "closet" thì nơi chốn nằm ngay
         trong câu. Dò từ khoá, không gọi mô hình. Tầng này cứu 105/213 mẩu không có nhãn;
      3. mượn nền của một nơi khác CÙNG KÊNH — mười nơi của một kênh thuộc cùng thế giới nên
         nền mượn vẫn khớp ngữ cảnh, hơn hẳn rơi về nền vector và mất chiều sâu.
    """
    idx = -1
    try:
        ds_noi = json.load(io.open(os.path.join(GOC, "noi_chon.json"), encoding="utf-8"))
    except Exception as e:
        print(f"   ⚠️ không đọc được noi_chon.json: {str(e)[:60]}")
        ds_noi = {}
    ten = [x.lower() for x in ds_noi.get(k["de"], [])]
    nhan = (kb.get("noi") or "").strip().lower()
    if nhan and nhan in ten:
        idx = ten.index(nhan)
    elif ten:
        loi = " ".join(str(c[0]) for c in cau).lower()
        diem = []
        for i, t in enumerate(ten):
            tu = [w for w in t.replace("'s", "").split()
                  if len(w) > 3 and w not in ("the", "a", "an", "some")]
            diem.append((sum(1 for w in tu if w in loi), -i))
        tot = max(diem)
        if tot[0] > 0:
            idx = -tot[1]

    anh = ""
    # TẦNG 0 — NỀN RIÊNG CỦA TẬP NÀY. 1/9, anh: *"tạo cho đa dạng, ko dùng lại, mà tạo cho đúng
    # bối cảnh channel, videos"* + *"key api free dư sức mà"*. Dùng lại một ảnh cho mọi tập là
    # tự tay làm kênh nhàm; 97 khoá CF cho ~16.300 ảnh/ngày nên sinh mới mỗi tập là rẻ.
    # Ảnh của tập do bước CHUẨN BỊ sinh trước (`chuan_bi_nen.py --vong N`), nên bước render vẫn
    # không gọi API lần nào. Không có thì rơi xuống kho 110 ảnh chuẩn — lớp đỡ, không phải lớp
    # chính.
    if idx >= 0:
        rieng = f"comic_nen/{_ten_tep(k)}_{idx:02d}_t{vong:03d}.jpg"
        if os.path.exists(os.path.join(PUB, rieng)):
            return idx, rieng
    try:
        nc = json.load(io.open(os.path.join(GOC, "nen_cf.json"), encoding="utf-8"))
        ds = nc.get(_ten_tep(k), {})
        if idx >= 0:
            anh = ds.get(str(idx), "")
        if not anh and ds:
            khoa = sorted(ds.keys(), key=lambda x: int(x))
            anh = ds[khoa[vong % len(khoa)]]
    except Exception:
        pass
    return idx, anh


def vai_va_giong(k: dict) -> tuple:
    """Trả (kiểuA, kiểuB, ghi_đè_A, ghi_đè_B, giọngA, giọngB) — nhất quán giới · tuổi · cao · giọng."""
    de = k["de"]
    va, vb = VAI[de]
    hs = sum(ord(c) for c in de)
    ra = []
    for i, (kieu, gioi, tuoi, cao, _vt, _en) in enumerate((va, vb)):
        ds = GIONG_VAI[(gioi, tuoi)]
        giong = ds[(hs + i * 3) % len(ds)]
        ghi = {
            "gioi": gioi, "tuoi": tuoi, "cao": cao,
            "loiVe": LOI_VE_KENH.get(de, "mat_to"),
            "kieuToc": TOC_HOP[(gioi, tuoi)],
            # Râu chỉ có ở nam đã trưởng thành. Bảng `_BONG` cũ gán râu theo kênh nên có cả nữ
            # công tố râu dê — một chi tiết đủ để người xem thôi tin vào cả nhân vật.
            "rau": ("" if gioi != "nam" or tuoi == "tre_con"
                    else ["", "ria", "quai", "de"][(hs + i) % 4]),
            # Trẻ con: đầu to hơn, mắt to hơn — hai thứ đọc ra "trẻ con" nhanh hơn cả chiều cao.
            **({"tiLeDau": 0.65, "matTo": 1.3, "beNgang": 0.94} if tuoi == "tre_con" else {}),
        }
        ra.append((kieu, ghi, giong))
    return ra[0][0], ra[1][0], ra[0][1], ra[1][1], ra[0][2], ra[1][2]


def dung_luot_comic(k: dict, vong: int) -> tuple:
    """Trả (danh sách lượt, danh sách câu thô). Mỏng hơn `dung_luot` của bản cũ đúng một cột:

    KHÔNG CÒN `goc` VÀ `co`.

    Bản cũ ghi sẵn cỡ máy và góc máy vào từng lượt, rồi engine đọc theo. Đó là nguồn của lỗi
    nặng nhất anh nhìn thấy — lượt ghi "hai_nguoi" mà khung ra chỉ có một người — vì kịch bản
    không biết khung rộng bao nhiêu pixel, nên nó KHÔNG ĐỦ THÔNG TIN để quyết định việc ấy.
    Nay panel tự đo mình rồi tự chọn: đủ chỗ thì hai người, không đủ thì cận một người.
    Kịch bản chỉ còn nói thứ nó thật sự biết — ai nói câu gì, với cảm xúc nào.
    """
    # ── NGUỒN MẨU: KHO VIẾT TAY + KHO SINH BẰNG AI ────────────────────────────────────
    # Anh: *"mỗi channel làm hàng nghìn videos đảm bảo đa dạng, ko lặp lại hay cùng 1 motip"*.
    # Bốn mẩu viết tay cho mỗi kênh nghĩa là tập thứ năm quay lại mẩu thứ nhất. `sinh_kich_ban.py`
    # sinh thêm bằng chính bộ khoá AI của hệ, có cổng chống trùng khuôn câu; kho ấy nối vào đây.
    kho = kho_cua_kenh(k)
    kb = kho[vong % len(kho)]
    cau = kb["loi"]
    # Nhãn nơi chốn -> chỉ số trong danh sách engine vẽ được. Mẩu viết tay không có nhãn, nên
    # trả -1 và engine tự chọn theo số tập như trước — không mẩu nào bị bỏ lại.
    globals()["_NOI_IDX"] = -1
    # Bốn mươi mẩu viết tay không có thẻ hook (chúng có trước khi hook tồn tại). Dựng một thẻ
    # từ chính câu MỞ: rút gọn còn 6 từ, viết hoa. Không hay bằng hook viết riêng, nhưng vẫn
    # hơn hẳn không có gì — và không mẩu nào bị bỏ lại phía sau.
    _hk = (kb.get("hook") or "").strip()
    # Mẩu viết tay lấy hook từ `hook_tay.json` (sinh một lần bằng AI). Chỉ số của chúng trùng
    # với thứ tự trong `KHO`, vì kho viết tay luôn đứng TRƯỚC trong danh sách nguồn.
    if not _hk:
        _i = vong % len(kho)
        if _i < len(KHO[k["de"]]):
            try:
                _ht = json.load(io.open(os.path.join(GOC, "hook_tay.json"), encoding="utf-8"))
                _hk = _ht.get(f"{k['de']}|{_i}", "")
            except Exception:
                pass
    if not _hk and cau:
        _hk = " ".join(str(cau[0][0]).replace(".", "").split()[:6]).upper()
    globals()["_HOOK"] = _hk
    # Nơi chốn + nền: MỘT nguồn duy nhất, dùng chung với bản dài. Bản dài dựng props riêng nên
    # nếu để hai chỗ tự tính, chúng sẽ lệch nhau — đúng cái bẫy "vá một nhánh, để nguyên nhánh
    # song song" đã ghi ở mục 22.1.
    globals()["_NOI_IDX"], globals()["_ANH_NEN"] = noi_va_nen(k, kb, cau, vong)
    n = len(cau)
    luot = []
    for i, (chu, ai, cx) in enumerate(cau):
        cuoi = i == n - 1
        luot.append({
            "s": 0.0, "e": 0.0, "ai": ai, "nar": chu, "camXuc": cx,
            # Ở cú chốt người nghe phải SỮNG, không được cười: nhân vật cười hộ rồi thì khán
            # giả không cười nữa. (Luật này của bản cũ đúng, giữ nguyên.)
            "camXucKia": ("bat_ngo" if cuoi else
                          ["nghi_ngo", "bat_ngo", "trung_tinh", "tuc", "buon", "nghi_ngo"][i % 6]),
            "cuChi": cu_chi_cua(chu, i, cuoi),
            "chot": cuoi,
        })
    return luot, cau


def mot_kenh(k: dict, vong: int) -> str:
    """Dựng một video comic. Trả đường tệp, hoặc "" nếu hỏng."""
    ten = k["ten"]
    slug = _ten_tep(k)
    print(f"\n▶ {ten}", flush=True)

    luot, cau = dung_luot_comic(k, vong)
    kieuA, kieuB, ghiA, ghiB, ga, gb = vai_va_giong(k)
    rel = f"v5_{slug}.mp3"
    mp3 = os.path.join(PUB, rel)
    try:
        dur, tu, moc = doc_hai_giong(cau, ga, gb, mp3)
    except Exception as e:
        print(f"   ❌ giọng đọc hỏng: {str(e)[:110]}")
        return ""
    if not tu:
        print("   ❌ không có mốc từ — BỎ")
        return ""

    for i, l in enumerate(luot):
        l["s"], l["e"] = moc[i]

    # Nét mặt và màu áo vẫn lấy từ `_hai_bong` (chúng làm mười kênh khác nhau), nhưng giới,
    # tuổi, chiều cao, tóc và râu thì bảng VAI nói lời cuối — nếu không, hai nguồn lại mâu thuẫn.
    tuyA, tuyB = _hai_bong(k)
    tuyA.update(ghiA); tuyB.update(ghiB)
    props = {
        "luot": luot, "tu": tu, "voMp3": rel, "nhac": NHAC.get(k["de"], ""),
        "kieuA": kieuA, "kieuB": kieuB, "kieuTuyA": tuyA, "kieuTuyB": tuyB,
        "tieuDe": ten, "handle": k.get("handle", ""), "kenh": slug,
        "mau": MAU_CHINH.get(k["de"], "#E4572E"), "mauPhu": MAU_PHU.get(k["de"], "#1F7AE0"),
    }
    _nk = NET_KENH.get(k["de"], dict(net=7, cham=9, bo=26, tile=0.60))
    _bc = BO_CUC_KENH.get(k["de"], dict(duoi=False, bo=0, no="BOOM!"))
    props.update(netMuc=_nk["net"], cham=_nk["cham"], boGoc=_nk["bo"], tiLe=_nk["tile"],
                 soTap=vong, bongDuoi=_bc["duoi"], boKhung=_bc["bo"], chuNo=_bc["no"],
                 noiIdx=globals().get("_NOI_IDX", -1), hook=globals().get("_HOOK", ""),
                 anhNen=globals().get("_ANH_NEN", ""),
                 sang=_sang_cua(globals().get("_ANH_NEN", "")),
                 nhacVol=_am_nhac(NHAC.get(k["de"], "")))
    pj = os.path.join(GOC, "out", f"v5_{slug}.json")
    os.makedirs(os.path.dirname(pj), exist_ok=True)
    io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))

    out = os.path.join(GOC, "out", f"v5_{slug}.mp4")
    r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "KichComic", out,
                        f"--props={pj}", "--gl=swiftshader", "--log=error"],
                       cwd=ENG, capture_output=True, text=True, timeout=2400)
    if r.returncode or not os.path.exists(out):
        print(f"   ❌ render hỏng: {(r.stderr or r.stdout or '')[-200:]}")
        return ""

    th = os.path.join(GOC, "out", f"v5_{slug}.jpg")
    if lam_thumb(out, cau[0][0] if cau else ten, ten, k["mau"], th):
        print(f"   🖼  thumbnail: {os.path.basename(th)}")
    # YouTube/FB/IG chuẩn hoá về −14 LUFS và chỉ HẠ chứ không nâng — video nhỏ hơn mốc thì
    # phát ra yếu hơn mọi thứ quanh nó trong feed. Đánh bóng ở bước cuối, nuốt mọi lỗi.
    _am = chuan(out)
    print(f"   ✅ {ten}: {os.path.basename(out)}  "
          f"({os.path.getsize(out) / 1e6:.1f} MB · {dur:.0f}s · {len(luot)} panel"
          f"{' · ' + _am if _am else ''})")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="", help="lọc theo tên kênh, cách nhau bằng dấu phẩy")
    ap.add_argument("--vong", type=int, default=0, help="số tập — bốc mẩu thoại thứ mấy trong kho")
    a = ap.parse_args()

    chon = KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [x for x in KENH if x["ten"].replace(" ", "").upper() in vt]
    if not chon:
        print("❌ không khớp kênh nào")
        return 2

    ra = [v for v in (mot_kenh(k, a.vong) for k in chon) if v]
    print(f"\n{'✅' if ra else '⚠️'} {len(ra)}/{len(chon)} video comic")
    return 0 if ra else 1


if __name__ == "__main__":
    raise SystemExit(main())
