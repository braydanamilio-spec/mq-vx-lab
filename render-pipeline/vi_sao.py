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
    "therules":   ("vanished", ["Defunct airlines of the United States",
                                "United States federal legislation", "Corporate scandals"]),
    "realcost":   ("vanished", ["Defunct banks of the United States",
                                "Corporate scandals", "Defunct companies of the United States"]),
    "whatif":     ("unsolved", ["Cancelled spacecraft", "Abandoned projects",
                                "Cancelled aircraft projects"]),
    "survive":    ("unsolved", ["Maritime incidents", "Nuclear accidents and incidents",
                                "Aviation accidents and incidents in the United States"]),
    "speedof":    ("vanished", ["Defunct airlines of the United States",
                                "Defunct railroads", "Supersonic transport"]),
    "howbig":     ("vanished", ["Demolished buildings and structures in the United States",
                                "Megaprojects", "Defunct companies of the United States"]),
    "wheregoes":  ("unsolved", ["Superfund sites", "Waste management",
                                "Environmental disasters"]),
    "dayinlife":  ("unsolved", ["Medical controversies", "Withdrawn drugs",
                                "Health disasters"]),
    "odds":       ("unsolved", ["Nuclear accidents and incidents", "Fires in the United States",
                                "Maritime incidents"]),
    "hiddenfee":  ("vanished", ["Corporate scandals",
                                "Defunct financial services companies of the United States",
                                "Defunct banks of the United States"]),
    "yearsof":    ("vanished", ["Discontinued products", "Defunct computer companies of the United States",
                                "Defunct companies of the United States"]),
    "howloud":    ("vanished", ["Defunct record labels of the United States",
                                "Defunct radio stations in the United States",
                                "Discontinued products"]),
    "whatweighs": ("vanished", ["Defunct social networking services",
                                "Defunct manufacturing companies of the United States",
                                "Defunct railroads"]),
    "rightnow":   ("vanished", ["Defunct social networking services", "Defunct websites",
                                "Discontinued products"]),
    "howhot":     ("unsolved", ["Fires in the United States", "Power stations",
                                "Fires in the United States"]),
    "smallest":   ("vanished", ["Defunct computer companies of the United States",
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
    r"\b(?:massacre\w*|genocid\w*|atrocit\w*|holocaust\w*|lynch\w*|"
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


def hop_dinh_dang(chu_the: str, van: str = "") -> bool:
    """Chuyện này kể được bằng giọng một nhân vật hoạt hình vui vẻ không?

    Xét TÊN trước (rẻ), rồi vài trăm chữ đầu bài viết — phần mở đầu Wikipedia luôn nói ngay
    quy mô thương vong nếu có.
    """
    if _KHONG_HOP.search(chu_the or "") or _TEN_CAM.search(chu_the or ""):
        return False
    if van and _KHONG_HOP.search(van[:1200]):
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
    _ung = [(ct, kh, _sang.get(ct, SAN_NHAN_QUA))
            for ct, kh in H.tiep_tu(ma, _dat, khuons, so_luong=6)]
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
        try:
            v = C.luot_xem(_ct)
        except Exception:
            v = -1
        return _nq * (math.log10(max(v, 10)) if v >= 0 else 2.0)

    _ung.sort(key=lambda x: -_diem(x))
    try:
        _t = _ung[0]
        print(f"   🏅 chọn «{_t[0][:34]}» · {_t[2]} câu nhân quả · "
              f"{C.luot_xem(_t[0]):,} lượt xem/90 ngày")
    except Exception:
        pass
    for chu_the, khuon, _nq in _ung:
        try:
            _van = C.bai_viet(chu_the) or ""
        except Exception:
            _van = ""
        if not hop_dinh_dang(chu_the, _van):
            print(f"   ⏭ «{chu_the[:40]}»: có thương vong — không kể được bằng giọng này")
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
        DA_CHON[(ma, i)] = {"chu_the": chu_the.split(" (")[0],
                            "khuon": khuon,
                            "hinh_mau": C.hinh_mau(ho),
                            "r": r}          # giữ nguyên bộ nhịp để `bo_1_3` cắt short
        H.ghi(ma, chu_the, khuon)
        print(f"   🎯 «{chu_the}» × khuôn {khuons.index(khuon)} · {_nq} câu nhân quả")
        return r
    print(f"   ⚠ {ma}: không cặp nào trong 6 cặp đầu đủ tư liệu — dùng bộ sinh cũ")
    return None
