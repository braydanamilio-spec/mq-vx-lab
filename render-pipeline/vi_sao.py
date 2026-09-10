#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NỐI ENGINE "VÌ SAO" VÀO ĐƯỜNG SẢN XUẤT.  (7/9/2026)

── VÌ SAO CẦN TỆP NÀY ────────────────────────────────────────────────────────────────────
Cả ngày hôm nay dựng: chủ thể có thật · khuôn hỏi · cổng số bịa · một giọng · ảnh thật ·
nền theo chủ thể. Và **không thứ nào chạm vào đường sản xuất**: đường thật là

    render_comic_18.yml  ->  pilot_hai.mot_tap  ->  giai_thich.BO_SINH[ma]  ->  bộ sinh ĐO LƯỜNG cũ

còn engine "vì sao" chỉ với tới được qua `_thu_vanished.py`, một tệp THỬ nhận chủ thể từ
dòng lệnh. Tệp này là mắt xích còn thiếu: nó biến `(kênh, số tập)` thành một tập hoàn chỉnh,
đúng hình dạng `BO_SINH` trả, KHÔNG cần ai gõ tên chủ thể.

── BA THỨ MỘT TẬP CẦN, VÀ CHÚNG Ở BA CHỖ KHÁC NHAU ──────────────────────────────────────
    chủ thể      `ho_chu_de.tiep`   — cây hạng mục Wikipedia, không cạn
    khuôn hỏi    `khung_hoi.KHUNG`  — lời hứa của kênh × ~24 cách hỏi
    nhịp         `khung_hoi.nhip_tu_khuon`

`BO_SINH[ma](i)` chỉ trả về NHỊP, trong khi `pilot_hai` còn cần biết CHỦ THỂ (để tải ảnh
thật và vẽ nền theo chủ thể) và HÌNH MẪU. Không nhét chúng vào một biến toàn cục — biến
toàn cục thì tập sau đọc phải chủ thể của tập trước khi có gì hỏng giữa chừng. Ghi vào một
bảng khoá theo `(mã, số tập)`, và `pilot_hai` tra đúng cặp nó đang dựng.
"""
from __future__ import annotations

import re

import ho_chu_de as H
import khung_hoi as K

# Kênh -> (lời hứa, các gốc hạng mục cấp chủ thể).
# Mới nối MỘT kênh: §4 nói pilot một kênh, anh duyệt, rồi mới nhân ra mười. Mười bảy kênh
# còn lại thêm vào đây, mỗi kênh một lời hứa và bộ gốc riêng.
KENH_HUA = {
    # Đã KIỂM từng tên bằng API (7/9/2026). Bốn tên hoá ra RỖNG THẬT — khác hẳn "đọc hỏng" —
    # nên đã thay: `Defunct retailers of the US` · `Industrial disasters` · `Obsolete
    # technologies` · `Defunct automobile manufacturers of the US`.
    # Lần đo ĐẦU báo 25/30 tên hỏng, và em suýt loại nhầm cả `Shipwrecks` (125) lẫn
    # `Power stations` (32): bắn 30 lệnh liên tiếp thì Wikipedia chặn nhịp, và mã -1 (đọc
    # hỏng) bị trình bày cạnh số 0 (rỗng thật) như thể cùng một nghĩa (§15.2).
    # Mỗi kênh BA gốc hạng mục, cố ý dư: một tên viết sai hay một hạng mục bị đổi tên trên
    # Wikipedia thì kênh vẫn còn hai gốc kia mà chạy, thay vì chết câm. `duyet` in cảnh báo
    # riêng cho gốc ra 0 nên vẫn biết cái nào hỏng (§15.2 — số 0 phải có mẫu số).
    #
    # Gốc chọn theo NGHỀ của chuyên gia cố định từng kênh, để chủ thể và người dẫn cùng một
    # thế giới: Attorney Brooks nói về hãng bay sập và luật liên bang, Dr Imani nói về nhà
    # máy điện và hoả hoạn. Người dẫn đúng nghề là nửa của việc "nhìn ra một người".
    # ── 9/9: ĐỔI GỐC THEO ĐỘ PHỦ ẢNH, ĐO CHỨ KHÔNG ĐOÁN ────────────────────────────────
    # Anh chốt phương án A (chỉ kể chủ thể có tư liệu) và muốn đề tài viral Mỹ. Đo sổ ảnh
    # 1.010 chủ thể rồi đếm chủ thể giàu ảnh theo từng gốc:
    #     Superfund sites                    26 giàu ảnh /   439   ← tốt nhất, 6%
    #     Nuclear accidents and incidents     5 /   287
    #     Fires in the United States          5 /   748
    #     Defunct companies of the US         1 / 3.757          ← gốc cũ, gần như trắng
    #     Defunct airlines of the US          0 /   757          ← gốc cũ của therules
    # Lý do Superfund giàu ảnh không phải nó nổi tiếng mà là **EPA chụp và công bố**: tác
    # phẩm của cơ quan liên bang Mỹ mặc nhiên thuộc phạm vi công cộng. Cùng lý do với Edwards
    # AFB (20 ảnh), Hanford Site (16), Fernald (18) trong top sổ ảnh.
    # Và nó đúng là đề tài viral ở Mỹ: ô nhiễm độc hại, doanh nghiệp gây hại, kiện tụng —
    # khớp lời hứa `vanished` mà không cần đổi giọng kênh.
    # Giữ `Corporate scandals` làm gốc thứ hai (cùng thế giới của Attorney Brooks), bỏ
    # `Defunct airlines` vì đo được 0/757 chủ thể giàu ảnh.
    "therules":   ("downfall", ["Superfund sites", "Corporate scandals",
                                "Defunct companies of the United States"]),
    "realcost":   ("downfall", ["Defunct banks of the United States",
                                "Corporate scandals", "Defunct companies of the United States"]),
    "whatif":     ("unsolved", ["Cancelled spacecraft",
                                "Abandoned military projects of the United States",
                                "Cancelled aircraft projects"]),
    # ── ĐỔI GỐC ÍT THƯƠNG VONG  (rà 10/9/2026) ──────────────────────────────────────────
    # Ba gốc cũ (Maritime/Nuclear/Aviation incidents) gần như TOÀN chủ thể có thương vong, nên
    # cổng `hop_dinh_dang` (giọng nhẹ không kể thảm hoạ chết người) loại gần hết — đo được
    # `vi_sao.sinh("survive")` bỏ qua hàng chục chủ thể liên tiếp, chọn mất >20 phút (các kênh
    # khác ~2 phút). Ba gốc mới hợp lời hứa "unsolved" HƠN (bí ẩn, chưa ai trả lời) mà ít
    # thương vong hàng loạt: người mất tích được tìm thấy · biến mất không giải thích · trò lừa.
    # Bí ẩn/mất-tích cũng đầy án mạng ("Murder of Milly Dowler" trong "Formerly missing
    # people"), vẫn vướng cổng thương vong. Nay ba gốc THẬT SỰ ít chết người mà vẫn "unsolved"
    # (chưa ai trả lời): trò lừa · phát minh biến mất · sinh vật bí ẩn.
    "survive":    ("unsolved", ["Hoaxes", "Lost inventions", "Cryptids"]),
    "speedof":    ("vanished", ["Defunct airlines of the United States",
                                "Defunct railroads", "Cancelled aircraft projects"]),
    "howbig":     ("vanished", ["Demolished buildings and structures in the United States",
                                "Megaprojects", "Defunct companies of the United States"]),
    "wheregoes":  ("unsolved", ["Superfund sites", "Waste management",
                                "Environmental disasters"]),
    "dayinlife":  ("unsolved", ["Medical controversies", "Withdrawn drugs",
                                "Health disasters"]),
    "odds":       ("unsolved", ["Nuclear accidents and incidents", "Fires in the United States",
                                "Maritime incidents"]),
    "hiddenfee":  ("downfall", ["Corporate scandals",
                                "Defunct financial services companies of the United States",
                                "Defunct banks of the United States"]),
    "yearsof":    ("boom", ["Discontinued products", "Defunct computer companies of the United States",
                                "Defunct companies of the United States"]),
    "howloud":    ("vanished", ["Defunct record labels of the United States",
                                "Defunct radio stations in the United States",
                                "Discontinued products"]),
    "whatweighs": ("vanished", ["Defunct social networking services",
                                "Defunct manufacturing companies of the United States",
                                "Defunct railroads"]),
    "rightnow":   ("boom", ["Defunct social networking services", "Defunct websites",
                                "Discontinued products"]),
    "howhot":     ("unsolved", ["Fires in the United States", "Power stations",
                                "Nuclear accidents and incidents"]),
    "smallest":   ("boom", ["Defunct computer companies of the United States",
                                "Defunct telecommunications companies of the United States",
                                "Discontinued products"]),
    "howlong":    ("unsolved", ["Shipwrecks", "Defunct railroads", "Maritime incidents"]),
    "howmuch":    ("vanished", ["Defunct banks of the United States", "Hyperinflation",
                                "Defunct department stores of the United States"]),
}

# `(mã, số tập)` -> {chu_the, khuon, hinh_mau}. `pilot_hai` đọc bảng này.
DA_CHON: dict = {}


# ── CHỦ THỂ KHÔNG HỢP VỚI ĐỊNH DẠNG  (soi khung 8/9/2026) ───────────────────────────────────
# Lượt dựng thật chọn trúng **"1971 Iraq poison grain disaster"** — một vụ ngộ độc hàng loạt
# chết hàng trăm người — và người dẫn là nhân vật hoạt hình ĐANG CƯỜI. Không cổng nào bắt, vì
# mọi cổng đang đo tay nghề viết và độ đầy tư liệu, không đo **chuyện này có kể được bằng
# giọng ấy không**.
#
# Đây không phải chuyện thẩm mỹ. Một kênh hoạt hình vui vẻ kể chuyện người chết hàng loạt thì
# vừa phản cảm với người xem Mỹ, vừa là dạng bị gỡ và bị tắt kiếm tiền nhanh nhất.
#
# Hồ đề tài lấy từ chính những hạng mục ấy (`Maritime incidents`, `Nuclear accidents`,
# `Fires in the United States`…) nên nó sẽ còn trúng nữa — phải chặn ở khâu CHỌN, không phải
# dặn khâu viết (§14.12: ràng buộc tuyệt đối thì làm cho nó không thể vi phạm).
#
# Danh sách này cố ý HẸP và chỉ nhắm thứ có NGƯỜI CHẾT. Tai nạn không chết người, công ty phá
# sản, sản phẩm khai tử — vẫn nhận, vì đó đúng là ngách "vì sao nó biến mất".
# ── CỔNG GIỌNG: BIỂU THỨC ĐỌC LÊN RẤT CHẮC MÀ BẮT ĐƯỢC 1/16  (8/9/2026) ─────────────────
# Bản đầu viết `\b(massacre|atrocit|terror|casualt|hijack|...)\b`. Nửa danh sách là GỐC TỪ
# định để khớp mọi hậu tố (`atrocit` -> atrocities), nhưng `\b` đóng ở cuối chặn đúng điều
# đó: sau `atrocit` là `i`, không phải ranh giới từ. Nửa còn lại chỉ khớp dạng SỐ ÍT.
#
# Đo trên 16 chủ thể bạo lực rõ ràng: **1/16 bị chặn**. Lọt cả «September 11 attacks»,
# «Munich massacres», «Terrorism in Italy» — và lọt đúng chủ thể mà bộ 125 đã dựng thành
# video: «1973 Rome airport attacks and hijacking» (34 người chết), vì `hijack` không khớp
# `hijacking`. Anh đã bắt lỗi này một lần rồi với «1971 Iraq poison grain disaster».
#
# Cùng họ §15.3, chiều ngược lại: ở đó `\w*` sau gốc NGẮN nuốt nhầm; ở đây `\b` sau gốc
# DÀI không nuốt gì. Nên gốc dài và riêng cho bạo lực thì mở `\w*`, gốc mơ hồ thì liệt kê
# đúng dạng thật (§15.3 nguyên văn).
#
# VÀ CHI PHÍ HAI PHÍA KHÔNG BẰNG NHAU — đây là chỗ cổng này khác mọi cổng khác trong repo.
# §13.8 dạy "cổng bắt oan tệ hơn cổng không bắt", đúng khi bắt oan tiêu một vòng gọi AI.
# Ở đây bắt oan tiêu MỘT CHỦ THỂ trong hồ 3.112 cái mà chỉ cần 17 — gần như bằng 0. Bỏ lọt
# thì ra một video có người dẫn hoạt hình tươi cười kể chuyện 34 người chết. Nên cổng này
# CỐ Ý nghiêng về phía chặn, và đó là một quyết định, không phải một sự cẩu thả.
_KHONG_HOP = re.compile(
    # gốc dài, chỉ dùng cho bạo lực -> mở hậu tố
    # `lynch\w*` -> dạng THẬT: nó từng bắt «Merrill **Lynch**» trong bài Lehman Brothers, tức
    # một HỌ NGƯỜI. §15.3 nguyên văn: gốc từ ngắn cộng `\w*` là cái bẫy, phải liệt kê dạng thật.
    r"\b(?:massacre\w*|genocid\w*|atrocit\w*|holocaust\w*|lynching\w*|lynched|lynch\s+mob\w*|"
    r"murder\w*|homicid\w*|manslaughter|assassinat\w*|"
    r"terror\w*|hijack\w*|hostage\w*|kidnap\w*|"
    r"casualt\w*|fatalit\w*|massacr\w*|"
    # `outbreak` · `illness` · `disease` thiếu ở bản trước, và bộ 141 đã dựng
    # «2019–2020 vaping lung illness outbreak» (68 người chết) thành 4 clip vì thế.
    # Cùng họ với `hijack` trượt `hijacking`: danh sách nêu vài chữ của MỘT khái niệm
    # rồi tưởng đã phủ hết khái niệm ấy (§13.20 — một danh sách chuỗi con không bắt
    # được ngôn ngữ).
    r"famine\w*|epidemic\w*|pandemic\w*|plague\w*|outbreak\w*|"
    r"illness\w*|disease\w*|infection\w*|hospitali[sz]\w*|"
    # `contaminat*` · `toxic*` · `exposure to` ĐÃ BỎ (9/9/2026): ba chữ này có trong MỌI bài
    # Superfund — vì Superfund LÀ chương trình dọn ô nhiễm — nên cổng chặn trọn một họ đề tài,
    # đúng cái họ vừa được chọn vì giàu ảnh nhất (26 chủ thể ≥8 ảnh / 439).
    # Ô nhiễm là chuyện doanh nghiệp và pháp lý, KỂ ĐƯỢC. Thứ không kể được là THƯƠNG VONG, và
    # hai luật SỐ ở `hop_dinh_dang` canh đúng nó: bỏ ba chữ này ra, «Firestone and Ford» vẫn bị
    # chặn vì *"killed 238 people"*. §13.8 — cổng bắt oan tệ hơn cổng không bắt.
    r"overdose\w*|contaminat\w*|toxic\w*|exposure\s+to\w*|"
    r"traffick\w*|slaver\w*|torture\w*|execution\w*|"
    # gốc MƠ HỒ -> liệt kê đúng dạng ("shoot" còn nghĩa quay phim, "bomb" còn nghĩa thất bại,
    # "abuse" còn nghĩa lạm dụng quyền, "attack" còn nghĩa cạnh tranh)
    r"bombing|bombings|bombed|bombard\w*|"
    r"shooting|shootings|gunman|gunmen|"
    r"suicide|suicides|poisoning|poisonings|"
    r"death\s+toll|mass\s+grave\w*|"
    r"(?:sexual|child|physical|domestic)\s+abuse\w*|"
    r"terrorist\s+attack\w*|armed\s+attack\w*|air\s+attack\w*)\b", re.I)

# TÊN chủ thể được soi CHẶT HƠN phần thân bài: trong một tiêu đề, "attack" và "disaster" gần
# như luôn nghĩa đen, còn trong văn xuôi chúng là ẩn dụ kinh doanh thường gặp ("attacked the
# low-cost market"). Một biểu thức cho hai loại chuỗi là chỗ §12.5 đã trả giá nhiều lần.
_TEN_CAM = re.compile(r"\b(?:attack\w*|disaster\w*|crash\w*|derailment\w*|"
                      r"sinking|shipwreck\w*|explosion\w*|fire\s+of\s+\d{4})\b", re.I)


_KHONG_HOP_VAN = re.compile(
    _KHONG_HOP.pattern.replace("contaminat\\w*|", "").replace("toxic\\w*|", "")
                      .replace("exposure\\s+to\\w*|", ""), re.I)


def hop_dinh_dang(chu_the: str, van: str = "") -> bool:
    """Chuyện này kể được bằng giọng một nhân vật hoạt hình vui vẻ không?

    Xét TÊN trước (rẻ), rồi vài trăm chữ đầu bài viết — phần mở đầu Wikipedia luôn nói ngay
    quy mô thương vong nếu có.
    """
    if _KHONG_HOP.search(chu_the or "") or _TEN_CAM.search(chu_the or ""):
        return False
    # ── TÊN XÉT CHẶT, THÂN BÀI XÉT NHẸ HƠN  (9/9/2026) ─────────────────────────────────
    # Bỏ `contaminat*` khỏi cả hai chỗ thì «Contaminated blood scandal» lọt — vụ máu nhiễm
    # bệnh, hàng nghìn người chết. Cổng selftest bắt đúng, và nó đúng.
    # Nhưng giữ ở cả hai chỗ thì mọi bài Superfund bị chặn, vì thân bài nào cũng có chữ ấy.
    # Phân biệt nằm ở CHỖ chữ xuất hiện: tên bài gọi thẳng "Contaminated blood" nghĩa là câu
    # chuyện LÀ về nhiễm độc người; thân bài nhắc "contamination" chỉ là bối cảnh của một bãi
    # thải. Nên TÊN xét bằng danh sách đầy đủ, THÂN BÀI xét bằng danh sách đã bỏ ba chữ môi
    # trường — và hai luật SỐ phía dưới vẫn canh thương vong thật ở thân bài.
    if van and _KHONG_HOP_VAN.search(van[:1200]):
        return False
    # Con số thương vong ở phần mở đầu: "killed 47", "459 died", "death toll of 6,000".
    if van and re.search(r"\b(kill(?:ed|ing)|died|dead|perished)\b[^.]{0,40}\d",
                         van[:1200], re.I):
        return False
    # Số đứng TRƯỚC động từ — dạng phổ biến nhất và bản đầu bỏ sót: *"a runway collision in
    # which **10 people died**"* lọt qua vì biểu thức đòi chữ số đứng SAU. Một cổng chỉ bắt
    # một trật tự từ là cổng chỉ bắt một nửa (§13.9: nhận ra quy luật, đừng liệt kê ví dụ).
    if van and re.search(r"\b\d[\d,]*\s+(?:\w+\s+){0,3}?(?:were\s+|was\s+)?"
                         r"(?:killed|died|dead|perished|injured|wounded)\b",
                         van[:1200], re.I):
        return False
    return True


def co_vi_sao(ma: str) -> bool:
    return ma in KENH_HUA


def sinh(ma: str, i: int):
    """(tiêu đề, hook, hook phụ, nhịp) cho tập thứ `i` của kênh `ma` — hoặc None.

    Trả None khi không dựng được (hết chủ thể · chủ thể thiếu tư liệu · mạng hỏng). Người
    gọi rơi về bộ sinh cũ, nên một lượt mạng xấu KHÔNG làm mất một tập — §7, tầng dưới cùng
    không bao giờ gọi mạng.
    """
    import chu_de as C
    import giai_thich as G
    if ma not in KENH_HUA:
        return None
    hua, gocs = KENH_HUA[ma]
    kn = K.KHUNG.get(hua)
    if not kn:
        return None
    khuons = kn["khuon"]
    # Lấy vài cặp: chủ thể đầu có thể thiếu tư liệu, và cổng tư liệu là cổng ĐẮT nên chỉ
    # chạy khi sắp dùng — quét 2.000 chủ thể mà kiểm cả 2.000 là trả tiền cho 1.990 tập
    # chưa làm.
    # ── CỔNG CHUYỆN TRƯỚC, ĐỘ PHỦ ẢNH CHỈ LÀ TIÊU CHÍ PHỤ  (anh bắt được, 7/9/2026) ──────
    # Em đo ra 6/11 chủ thể có đủ ảnh tự do nên tốn 0 hạn mức CF, rồi định xếp hồ đề tài theo
    # ĐỘ PHỦ ẢNH cho rẻ. Anh hỏi lại *"như thế có đúng bối cảnh khớp kịch bản … và vẫn đảm bảo
    # ra videos hay hook chứ"* — và anh đúng:
    #
    #     Polaroid   14 ảnh tự do   ·   0 câu nhân quả   -> ảnh đẹp, KHÔNG có chuyện
    #     Periscope  ít ảnh          ·   5 câu nhân quả   -> kịch bản tụt thành nhật ký phiên bản
    #
    # Tập Periscope dựng thật đã ra đúng thế: *"On 12 August 2015 … Then on 26 May 2015 …"*,
    # mốc thời gian còn đi lùi. Tối ưu một RÀNG BUỘC (hạn mức ảnh) mà biến nó thành TIÊU CHÍ
    # CHỌN nội dung là tối ưu đúng thứ dễ đo và hỏng đúng thứ người xem tới xem.
    #
    # Nên: lọc bằng CHUYỆN trước, rồi trong số đã qua cổng mới ưu tiên chủ thể nhiều ảnh.
    SAN_NHAN_QUA = 8          # Kodak/Concorde/Zeppelin/Pan Am = 30 · Periscope = 5 (trượt)
    # Lấy từ hồ ĐÃ SÀNG. Bản đầu thử 10 chủ thể rồi loại 7 ở NGAY lúc dựng — đo thật ở lượt
    # chạy tối nay: 7/7 bị loại, 7 vòng gọi mạng cho một tập rồi vẫn phải rơi về bộ sinh cũ.
    # `co_chuyen` đệm kết quả đã đo và sàng thêm vài chủ thể mỗi lượt, nên chi phí tỉ lệ với
    # PHẦN MỚI chứ không với kích thước hồ (§18.8).
    _dat = H.co_chuyen(gocs, san=SAN_NHAN_QUA, them=6)
    _sang = H._doc_sang()
    # Bốc cặp TỪ HỒ ĐÃ SÀNG, không từ cả hồ: bản trước bốc 40 cặp trên 757 chủ thể rồi lọc
    # lấy cái nào đã qua cổng — với 4 chủ thể đạt thì 40 cặp ấy gần như không bao giờ trúng,
    # nên `vi_sao` báo "không chủ thể nào đủ chuyện" và rơi về bộ sinh cũ DÙ hồ đã có hàng
    # tốt. Cổng lọc đúng, phép bốc sai nguồn (§15.1: bốc trước lọc sau).
    # ── BỐC RỘNG RỒI MỚI LỌC  (đo bộ 210 · 211, 9/9/2026) ─────────────────────────────
    # `so_luong=6` là cái trần THẬT làm mọi tập gần đây trắng ảnh — không phải trần `[:60]`
    # ở lượt xếp theo sổ ảnh phía dưới (em đã chẩn đoán nhầm chỗ ấy trước, và đo lại thì
    # `_ung` chỉ có ĐÚNG 6 phần tử nên trần 60 chưa bao giờ chạm tới).
    # Sổ có 51 chủ thể ≥8 ảnh trên 1.795 đã qua cổng chuyện — bốc 6 cặp ngẫu nhiên thì xác
    # suất trúng một trong số ấy là ~3%. Đo hai lượt liền: 0/6 và 0/6.
    # `tiep_tu` là phép số học trên danh sách đã đệm, KHÔNG gọi mạng — bốc 120 cặp tốn đúng
    # bằng bốc 6. §15.1: bốc trước lọc sau, và tập cần giữ chỉ chiếm 3% hồ.
    _ung = [(ct, kh, _sang.get(ct, SAN_NHAN_QUA))
            for ct, kh in H.tiep_tu(ma, _dat, khuons, so_luong=120)]
    # Cắt bằng SỔ ẢNH trước khi hỏi lượt xem: sổ đọc đĩa (miễn phí), `luot_xem` gọi mạng cho
    # chủ thể chưa đệm. Xếp theo ảnh ở đây KHÔNG vi phạm §19.19 — mọi ứng viên trong `_ung`
    # đều ĐÃ qua cổng chuyện, nên đây đúng là "tiêu chí phụ giữa những chủ thể đã qua cổng".
    if len(_ung) > 40:
        _sd0 = {x[0]: H.so_anh_da_do(x[0]) for x in _ung}
        if any(v > 0 for v in _sd0.values()):
            _ung.sort(key=lambda x: -_sd0.get(x[0], -1))
        _ung = _ung[:40]
    if not _ung:
        print(f"   ⚠ {ma}: không chủ thể nào trong 10 cặp đầu đủ chuyện — dùng bộ sinh cũ")
        return None
    # ── XẾP HẠNG: ĐỦ CHUYỆN TRƯỚC, RỒI ĐẾN DỄ HÌNH DUNG  (anh, 8/9/2026) ────────────────
    # Anh: *"kịch bản phải nói về cái người dùng dễ nhớ dễ hình dung — một công ty lớn, một
    # sự kiện tầm cỡ thế giới… nhìn là hình dung ra ngay"*. Hồ duyệt cây hạng mục nên nó ra
    # `Alaska International Air` (143 lượt xem/90 ngày) thay vì `Facebook` (1.784.660).
    #
    # THỨ TỰ HAI TIÊU CHÍ LÀ CÓ CHỦ Ý, và §19.19 đã trả giá để biết: xếp theo độ phủ tư liệu
    # trước thì Polaroid lên đầu hồ với 14 ảnh đẹp và **0 câu nhân quả**. Chuyện phải đứng
    # trước; độ nhận biết chỉ là tiêu chí PHỤ giữa những chủ thể ĐÃ qua cổng chuyện.
    #
    # Gộp bằng cách nhân, không bằng cách thay: điểm = số câu nhân quả × log(lượt xem). Nhân
    # thì một chủ thể vô danh nhưng cực giàu chuyện vẫn thắng một cái tên lớn mà rỗng chuyện.
    # `luot_xem` trả -1 khi không hỏi được — coi như trung tính, không đẩy lên cũng không dìm.
    import math

    def _diem(x):
        _ct, _kh, _nq = x
        v = _lx(_ct)
        return _nq * (math.log10(max(v, 10)) if v >= 0 else 2.0)

    # ── SÀN NHẬN BIẾT: NHÂN THÌ SỐ CÂU DÌM CHẾT ĐỘ NHẬN BIẾT  (anh, 8/9/2026) ──────────
    # Anh: *"ảnh thực tế vẫn quá ít"* · *"phải render cái gì người dùng nhìn cái nhận ra
    # ngay"*. Truy ra cả hai về cùng một gốc: CHỌN CHỦ THỂ.
    #
    # Đo 28 chủ thể đã dùng: **6/28 có dưới 1.000 lượt xem/90 ngày** — «Charter One Airlines»
    # 53 lượt, «Alaska International Air» 143, «Boston-Maine Airways» 189. Dưới 1.000 lượt là
    # ~11 lượt/ngày, tức gần như không ai tra. Và đúng những chủ thể ấy KHÔNG CÓ ảnh tự do:
    # Charter One cho 1 tấm, trong khi Kodak cho 18 và MetLife 7.
    #
    # Phép nhân là chỗ hỏng: `log10` nén chênh lệch 6.000 lần (53 vs 327.667) xuống còn 3,2
    # lần, còn số câu nhân quả biến thiên tới 8 lần — nên một hãng bay vô danh giàu chuyện
    # luôn thắng một cái tên ai cũng biết. Chú thích ngay trên còn ghi đó là chủ ý; đo xong
    # thì thấy chủ ý ấy sai với thứ anh cần.
    #
    # Sàn chứ không phải hệ số: dưới ngưỡng thì LOẠI, trên ngưỡng thì vẫn xếp bằng công thức
    # cũ. Và HỎNG MỀM — lọc sạch trơn thì trả lại danh sách đầy đủ, vì "không chủ thể nào đủ
    # nổi tiếng" không được phép biến thành "không dựng được tập nào" (§13.3).
    # ĐO HỎNG (-1) KHÔNG ĐƯỢC TÍNH LÀ NỔI TIẾNG. Bản đầu của em ánh xạ -1 -> 10^9, tức biến
    # "không đo được" thành "nổi tiếng nhất có thể" — đúng §15.2 ở dạng tệ nhất, vì nó không
    # chỉ mất thông tin mà còn ĐẨY LÊN ĐẦU thứ mình không kiểm chứng được. Nay -1 trượt sàn;
    # nhánh hỏng mềm ngay dưới vẫn giữ nguyên nên hồ không bao giờ cạn vì chuyện này.
    # Và gọi MỘT lần rồi dùng lại — bản đầu gọi `luot_xem` hai lần cho mỗi ứng viên.
    # ── SÀN LÀ ƯU TIÊN XẾP HẠNG, KHÔNG PHẢI PHÉP CẮT  (sửa lần hai, 8/9/2026) ──────────
    # Bản đầu cắt cứng mọi chủ thể dưới 1.000 lượt. Đo ngay lượt sau: hồ chỉ còn một ứng viên
    # qua sàn, mà nó có 8 câu nhân quả — dưới cổng chuyện — nên hệ BỎ cả bộ và không dựng gì.
    # Tức em chữa "chọn chủ thể vô danh" bằng cách làm đứng hẳn dây chuyền: một cái sàn cứng
    # đặt trước một cái cổng khác thì hai cái cùng chặn, và không cái nào biết cái kia.
    #
    # Nay xếp hạng hai tầng: qua sàn thì đứng TRƯỚC, và trong mỗi tầng vẫn xếp bằng công thức
    # cũ. Chủ thể nổi tiếng luôn được chọn khi nó đủ chuyện; chỉ khi KHÔNG có cái nào vừa nổi
    # vừa đủ chuyện thì mới rơi xuống tầng dưới — thay vì không dựng gì cả. `luot_xem` trả -1
    # (không đo được) nằm tầng dưới, không được coi là nổi tiếng (§15.2).
    _SAN_NHAN_BIET = 1000

    # TRA LƯỢT XEM ĐÚNG MỘT LẦN MỖI ỨNG VIÊN. `_tang` và `_diem` đều cần con số ấy, và cả hai
    # nằm trong khoá sắp xếp — nên bản đầu gọi `luot_xem` HAI lần cho mỗi chủ thể. Có đệm đĩa
    # thì lượt sau rẻ, nhưng lượt ĐẦU của mỗi chủ thể là một vòng mạng, và §19.20 đã đo rằng
    # chính nhịp gọi dồn dập là thứ đẻ ra 429. Gom lại một lần và dùng chung.
    _xem: dict = {}

    def _lx(ct):
        if ct not in _xem:
            try:
                _xem[ct] = C.luot_xem(ct)
            except Exception:
                _xem[ct] = -1
        return _xem[ct]

    def _tang(x):
        return 1 if (_lx(x[0]) or 0) >= _SAN_NHAN_BIET else 0

    _qua = sum(_tang(x) for x in _ung)
    if _qua and _qua < len(_ung):
        print(f"   🔎 {_qua}/{len(_ung)} chủ thể đạt ≥{_SAN_NHAN_BIET:,} lượt xem/90 ngày "
              f"— ưu tiên nhóm ấy, phần còn lại vẫn giữ làm dự phòng")
    _ung.sort(key=lambda x: (-_tang(x), -_diem(x)))

    # ── TẦNG THỨ BA: CHỦ THỂ PHẢI CÓ ẢNH TƯ LIỆU  (anh chốt, 8/9/2026) ─────────────────
    # Anh: nền chỉ được là ảnh thật, và *"tất cả videos đều có ảnh thật chứ"*. Đo 14 bộ đã
    # dựng: số ảnh đi theo độ nhận biết gần như tuyến tính — Kodak (87.057 lượt) 12 ảnh, South
    # Sea Company (35.493) 5 ảnh, Charter One Airlines (53 lượt) ĐÚNG MỘT.
    #
    # Nên siết ở khâu CHỌN CHỦ THỂ, và siết bằng CHÍNH THỨ MÌNH CẦN — số ảnh — chứ không bằng
    # một thứ thay thế. Lượt xem chỉ tương quan; số ảnh là điều kiện thật.
    #
    # Chỉ hỏi 6 ứng viên ĐẦU (đã qua hai tầng trên) để bó nhịp gọi Wikimedia, và `so_anh_co`
    # đệm ra đĩa nên 18 kênh dùng chung một sổ — chúng rút từ CÙNG hai họ hạng mục.
    #
    # Và ƯU TIÊN, không CẮT: một sàn cứng đặt trước cổng chuyện đã làm đứng dây chuyền hai
    # lượt liền sáng nay (157, 158 đều "chưa có chủ thể đủ chuyện — BỎ bộ này"). Không có ứng
    # viên nào đủ ảnh thì vẫn dựng bằng ứng viên tốt nhất, chỉ là tập ấy nhiều nền trống hơn.
    # ── SÀN THẬT, KHÔNG CÒN LÀ ƯU TIÊN  (anh: *"tìm cách fix nha e"*, 9/9/2026) ──────────
    # Bản trước để 3 và chỉ ĐẨY LÊN ĐẦU, không cắt — vì một sàn cứng từng làm đứng dây chuyền
    # hai lượt liền (bundle 157, 158). Nhưng đo lại thì nỗi lo ấy đặt sai chỗ:
    #
    #   chủ thể qua cổng chuyện          1.752
    #   trong đó có ≥10 ảnh  (đo 6/20)     ~525  × 24 khuôn = 12.600 bộ/kênh
    #
    # 12.600 bộ mỗi kênh là dư sức nuôi nhiều năm. Cắt xuống 30% hồ KHÔNG làm đứng gì cả —
    # thứ làm đứng bundle 157/158 là sàn cứng đặt TRƯỚC cổng chuyện rồi lọc sạch trơn, không
    # phải bản thân việc cắt.
    #
    # Nên bất biến thật không phải "đừng bao giờ cắt" mà là **"đừng bao giờ trả về rỗng"**.
    # Còn ứng viên đủ ảnh thì DÙNG RIÊNG chúng; không còn ai thì giữ nguyên cả danh sách.
    #
    # 8 chứ không phải 10: một tập dài 12 nhịp, 8 ảnh phủ 2/3 số nhịp, phần còn lại để nền
    # TRỐNG — anh đã chốt *"nền 100% ảnh thật liên quan… hay nền trống"* và *"ko ưu tiên dựng
    # ảnh cf mới"*, nên chỗ thiếu là chỗ trống, không phải chỗ để AI vẽ bù.
    # ── XẾP TRƯỚC BẰNG SỔ ẢNH ĐÃ ĐO  (anh chốt phương án A, 9/9/2026) ────────────────
    # `ho_chu_de.sang_anh()` đo sẵn số ảnh của từng chủ thể và đệm ra đĩa, nên phép xếp này
    # KHÔNG tốn một lượt mạng nào. Đo 1.010 chủ thể: 46 có ≥8 ảnh, và top danh sách nói rõ
    # loại nào giàu ảnh — cơ sở chính phủ Mỹ và thảm hoạ lịch sử Mỹ:
    #   Edwards AFB 20 · Savannah River Plant 20 · Orion 20 · động đất SF 1906 20 ·
    #   Hanford Site 16 · cháy Boston 1872 17 · cháy USS Forrestal 1967 14
    # Lý do không phải nổi tiếng mà là AI CHỤP: tác phẩm của cơ quan liên bang Mỹ mặc nhiên
    # thuộc phạm vi công cộng. Đo được A-ha 114.892 lượt xem mà chỉ 1 ảnh, còn Langley
    # Research Center 8.832 lượt thì 12 ảnh — nên lượt xem KHÔNG dùng làm thước (đã bác).
    #
    # Xếp trước bằng sổ, rồi vòng chọn vẫn đo lại bằng `nap_anh_that` trước khi dựng: sổ là
    # CẬN TRÊN (chưa qua bộ lọc tải về), không phải con số cuối (§13.15).
    # ── HỎI SỔ CHO MỌI ỨNG VIÊN, KHÔNG CHỈ 60 TÊN ĐẦU  (bộ 210, 9/9/2026) ────────────
    # `_ung[:60]` là §15.1 nguyên xi: cắt trước, lọc sau. Sổ có 51 chủ thể ≥8 ảnh trên 1.752
    # đã đo, nhưng chủ thể nào không rơi vào 60 tên đầu thì KHÔNG BAO GIỜ được xếp lên — và
    # thứ tự 60 tên ấy do điểm nhân quả quyết, không liên quan gì tới ảnh. Đo bộ 210: 0/6 ứng
    # viên có ≥8 ảnh, tập ra 1/12 nhịp có ảnh thật, 11 nhịp nền trơn — đúng thứ anh chê.
    # Cái trần ấy sinh ra vì `so_anh_da_do` nạp lại cả tệp mỗi lượt hỏi; nay nó có bộ nhớ nên
    # hỏi hết danh sách tốn đúng một lượt đọc đĩa.
    try:
        _sd = {x[0]: H.so_anh_da_do(x[0]) for x in _ung}
        if any(v > 0 for v in _sd.values()):
            _ung.sort(key=lambda x: -_sd.get(x[0], -1))
            _giau = sum(1 for v in _sd.values() if v >= 8)
            print(f"   📒 sổ ảnh: {_giau}/{len(_sd)} ứng viên có ≥8 ảnh — xếp lên trước")
    except Exception:
        pass

    _SAN_ANH = 8
    _dau = _ung[:6]
    if len(_dau) > 1:
        _anh = {}
        for _x in _dau:
            try:
                _anh[_x[0]] = C.so_anh_co(_x[0])
            except Exception:
                _anh[_x[0]] = -1
        _du_anh = [x for x in _dau if _anh.get(x[0], -1) >= _SAN_ANH]
        if _du_anh:
            # ── ĐÃ THỬ CẮT THẬT, VÀ NÓ LÀM ĐỨNG DÂY CHUYỀN NGAY LƯỢT ĐẦU  (9/9/2026) ──────
            # Em đổi tầng này thành SÀN CỨNG sau khi đo hồ: 1.752 chủ thể qua cổng chuyện,
            # ~525 đủ ảnh, × 24 khuôn = 12.600 bộ/kênh — "cắt 70% hồ vẫn dư nhiều năm".
            # Phép tính ấy ĐÚNG và KHÔNG LIÊN QUAN. Chạy thật, tập 180:
            #     🖼 1/6 ứng viên đầu có ≥8 ảnh — CHỈ dựng nhóm ấy
            #     🏅 «Superfund» -> ⏭ có thương vong, không kể được bằng giọng này
            #     ⏭ tập 180: chưa có chủ thể đủ chuyện — BỎ bộ này
            # Sàn cắt 6 xuống 1, rồi một cổng PHÍA SAU loại nốt cái duy nhất. Kích thước hồ
            # không cứu được, vì thứ quyết định là HAO HỤT Ở CÁC CỔNG SAU chứ không phải số
            # ứng viên còn lại ở cổng này.
            #
            # Bất biến đúng vì thế KHÔNG phải "tầng này trả về khác rỗng" — mà là **mỗi cổng
            # phải để lại đủ ứng viên cho mọi cổng đứng sau nó**. Không đo được bằng cách nhìn
            # riêng một cổng, nên cách an toàn là ƯU TIÊN chứ đừng CẮT: xếp nhóm đủ ảnh lên
            # đầu, giữ phần còn lại làm dự phòng.
            #
            # Cổng `t_uu_tien_chu_the_co_anh` bản cũ canh đúng chuyện này và em đã tự nới nó
            # ra để bản sửa của mình đi qua. Đó mới là lỗi thật của lượt này (§13.8 ngược:
            # không phải cổng bắt oan, mà là em gỡ cổng đang bắt đúng).
            _bo = len(_dau) - len(_du_anh)
            if _bo:
                print(f"   🖼 {len(_du_anh)}/{len(_dau)} ứng viên đầu có ≥{_SAN_ANH} ảnh tư "
                      f"liệu — ưu tiên nhóm ấy, phần còn lại giữ làm dự phòng")
            _ung = _du_anh + [x for x in _ung if x not in _du_anh]
        else:
            # Hỏng mềm: hồ mỏng hoặc lượt hỏi ảnh hụt thì vẫn dựng bằng danh sách đầy đủ.
            # Đây là nhánh giữ cho dây chuyền không đứng, và nó phải luôn tồn tại.
            print(f"   ⚠ không ứng viên nào có ≥{_SAN_ANH} ảnh tư liệu — vẫn dựng bằng cả "
                  f"danh sách, tập sẽ nhiều nền trống hơn")

    try:
        _t = _ung[0]
        # KHÔNG cắt tên ở đây: dòng này là dòng CHẨN ĐOÁN. Bản cũ cắt 34 ký tự và biến
        # «Bricks & Minifigs–Reckless Ben controversy» thành một chuỗi trông như rác,
        # khiến em kết luận nhầm là hồ có bản ghi hỏng và suýt đi sửa thứ không hỏng.
        print(f"   🏅 chọn «{_t[0]}» · {_t[2]} câu nhân quả · "
              f"{C.luot_xem(_t[0]):,} lượt xem/90 ngày")
    except Exception:
        pass
    # ── KIỂM ẢNH TRONG VÒNG CHỌN, KHÔNG LỌC TRƯỚC  (9/9/2026) ─────────────────────────
    # Hai cách đã thử và đều sai:
    #   · lọc TRƯỚC vòng (sàn cứng) -> cắt 6 ứng viên xuống 1, cổng "có thương vong" phía sau
    #     loại nốt, cả bộ 180 bị bỏ. Một cổng không biết cổng sau nó sẽ loại bao nhiêu.
    #   · chỉ ƯU TIÊN -> dây chuyền chạy, nhưng bộ 180 chọn «Firepower International» với
    #     ĐÚNG 0 ảnh thật, tức vẫn ra một tập toàn nền trống.
    # Cách đúng là hỏi ảnh Ở TRONG vòng, sau khi ứng viên đã qua MỌI cổng khác: ai có ảnh thì
    # nhận ngay; ai không có thì GIỮ LÀM DỰ BỊ rồi thử ứng viên kế. Hết ứng viên mà chưa ai
    # có ảnh thì dùng bản dự bị — dây chuyền không bao giờ đứng, và cũng không bao giờ chọn
    # một chủ thể trắng ảnh khi còn chủ thể khác có.
    # `so_anh_co` đệm ra đĩa nên phép hỏi này gần như miễn phí ở lượt thứ hai trở đi.
    _du_bi = None

    def _nhan(chu_the, khuon, _nq, r):
        DA_CHON[(ma, i)] = {"chu_the": chu_the.split(" (")[0], "khuon": khuon,
                            "hinh_mau": C.hinh_mau(C.ho_so(chu_the)), "r": r}
        H.ghi(ma, chu_the, khuon)
        return r

    for chu_the, khuon, _nq in _ung:
        try:
            _van = C.bai_viet(chu_the) or ""
        except Exception:
            _van = ""
        if not hop_dinh_dang(chu_the, _van):
            print(f"   ⏭ «{chu_the[:40]}»: có thương vong — không kể được bằng giọng này")
            continue
        # ── KHUÔN ĐÒI TIỀN MÀ KỊCH BẢN KHÔNG CÓ TIỀN  (bộ 214, 9/9/2026) ──────────────
        # Hook đọc *"How much money died with Savannah River Plant, eighty dollars?"* trong
        # khi kịch bản không có một con số tiền nào — mô hình mượn "eighty" của
        # *"up to eighty PERCENT"* rồi gắn sang **dollars**. §19.4: nó bịa vì ta để lại chỗ
        # trống. Bỏ CẶP chứ không bỏ chủ thể: cùng chủ thể ấy vẫn dựng được bằng 21 khuôn
        # khác, nên đây là bộ lọc trên một trục, không phải mất một chủ thể (§15.7).
        if K.khuon_doi_tien(khuon) and not K.co_so_tien(_van):
            print(f"   ⏭ «{chu_the[:34]}» × khuôn hỏi TIỀN: kịch bản không có con số "
                  f"tiền nào — bỏ cặp, không để mô hình bịa")
            continue
        try:
            ho = C.ho_so(chu_the)
        except Exception:
            continue
        if not ho:
            continue
        try:
            r = K.nhip_tu_khuon(khuon, chu_the.split(" (")[0], ho, G._n, G._ve,
                                kn.get("tu_khoa", ()))
        except Exception as e:
            print(f"   ⚠ «{chu_the[:34]}» dựng nhịp hỏng: {str(e)[:44]}")
            continue
        if not r:
            continue                     # không đủ tư liệu đúng chủ đề -> BỎ CẶP, đúng hành vi
        # ── ĐẾM ẢNH BẰNG ĐÚNG ĐƯỜNG SẢN PHẨM ĐI  (đo bộ 181, 9/9/2026) ────────────────
        # Bản trước hỏi `C.so_anh_co`, và nó báo «Liberty Express Airlines» có 2 ảnh nên vòng
        # chọn nhận. Dựng ra thì `nap_anh_that` trả về **0** và cả 12 nhịp nền trống.
        # `so_anh_co` đếm ỨNG VIÊN từ `anh_cua`; `nap_anh_that` còn phải TẢI VỀ rồi qua thêm
        # bộ lọc chân dung, sàn cỡ, chặn logo và khử trùng — 2 ứng viên rụng sạch.
        # §13.15: phép đo phải đi qua ĐÚNG đường mà mã thật đi, nếu không nó đo một sản phẩm
        # không tồn tại. Nên gọi thẳng `nap_anh_that`.
        # Không lãng phí: ảnh tải về vào chung kho `anh_pd/` và lượt dựng sau dùng lại ngay;
        # chi phí thật chỉ là ảnh của những ứng viên bị loại. Xin 8 thôi — đủ để trả lời câu
        # "có ảnh không", không cần xin trọn 32 cho một ứng viên chưa chắc được chọn.
        try:
            import pilot_hai as _PH          # nhập muộn: `pilot_hai` nhập `vi_sao` ở tầng trên
            _sa = len(_PH.nap_anh_that(chu_the, toi_da=8) or [])
        except Exception:
            _sa = -1                       # hỏi hụt: coi như CHƯA BIẾT, không coi như 0
        # ── NHẬN NGAY KHI ĐỦ GIÀU, CÒN LẠI GIỮ BẢN GIÀU NHẤT  (đo bộ 182, 9/9/2026) ────
        # Bản trước chỉ bỏ qua chủ thể có ĐÚNG 0 ảnh, nên nó nhận ngay «Mountain West
        # Airlines» với 2 ảnh -> 2/11 nhịp có nền, còn KÉM HƠN bộ 171 (4/12).
        # Có bản dự bị rồi thì không còn lý do dễ dãi: duyệt hết ứng viên, nhận NGAY ai đủ
        # `_SAN_ANH`, còn không thì cuối vòng lấy người GIÀU ẢNH NHẤT đã gặp.
        # Không bao giờ đứng (luôn còn bản giàu nhất), và không bao giờ bỏ một chủ thể giàu
        # ảnh để lấy một chủ thể nghèo chỉ vì nó đứng trước.
        if _sa < _SAN_ANH:
            if _du_bi is None or _sa > _du_bi[4]:
                _du_bi = (chu_the, khuon, _nq, r, _sa)
            print(f"   ⏭ «{chu_the[:34]}»: {max(0, _sa)} ảnh (< {_SAN_ANH}) — giữ dự bị, "
                  f"thử ứng viên kế")
            continue
        DA_CHON[(ma, i)] = {"chu_the": chu_the.split(" (")[0],
                            "khuon": khuon,
                            "hinh_mau": C.hinh_mau(ho),
                            "r": r}          # giữ nguyên bộ nhịp để `bo_1_3` cắt short
        H.ghi(ma, chu_the, khuon)
        print(f"   🎯 «{chu_the}» × khuôn {khuons.index(khuon)} · {_nq} câu nhân quả"
              + (f" · {_sa} ảnh thật" if _sa > 0 else ""))
        return r
    if _du_bi:
        # Không ai có ảnh. Vẫn dựng — bỏ cả bộ còn tệ hơn một tập nhiều nền trống, và đó
        # đúng là thứ đã làm đứng bundle 157/158/180.
        _ct, _kh, _nq2, _r, _sa2 = _du_bi
        print(f"   ⚠ không ứng viên nào đạt {_SAN_ANH} ảnh — dựng bằng «{_ct[:30]}» "
              f"({max(0, _sa2)} ảnh), tập sẽ nhiều nền trống")
        return _nhan(_ct, _kh, _nq2, _r)
    print(f"   ⚠ {ma}: không cặp nào trong 6 cặp đầu đủ tư liệu — dùng bộ sinh cũ")
    return None
