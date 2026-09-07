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

import ho_chu_de as H
import khung_hoi as K

# Kênh -> (lời hứa, các gốc hạng mục cấp chủ thể).
# Mới nối MỘT kênh: §4 nói pilot một kênh, anh duyệt, rồi mới nhân ra mười. Mười bảy kênh
# còn lại thêm vào đây, mỗi kênh một lời hứa và bộ gốc riêng.
KENH_HUA = {
    "therules": ("vanished", ["Defunct companies of the United States",
                              "Discontinued products"]),
}

# `(mã, số tập)` -> {chu_the, khuon, hinh_mau}. `pilot_hai` đọc bảng này.
DA_CHON: dict = {}


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
    _dat = set(H.co_chuyen(gocs, san=SAN_NHAN_QUA, them=6))
    _sang = H._doc_sang()
    _ung = []
    for chu_the, khuon in H.tiep(ma, gocs, khuons, so_luong=40):
        if chu_the not in _dat:
            continue
        _ung.append((chu_the, khuon, _sang.get(chu_the, SAN_NHAN_QUA)))
        if len(_ung) >= 6:
            break
    if not _ung:
        print(f"   ⚠ {ma}: không chủ thể nào trong 10 cặp đầu đủ chuyện — dùng bộ sinh cũ")
        return None
    # Trong số ĐÃ qua cổng chuyện: nhiều câu nhân quả trước, đó mới là thứ quyết định tập hay.
    _ung.sort(key=lambda x: -x[2])
    for chu_the, khuon, _nq in _ung:
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
                            "hinh_mau": C.hinh_mau(ho)}
        H.ghi(ma, chu_the, khuon)
        print(f"   🎯 «{chu_the}» × khuôn {khuons.index(khuon)} · {_nq} câu nhân quả")
        return r
    print(f"   ⚠ {ma}: không cặp nào trong 6 cặp đầu đủ tư liệu — dùng bộ sinh cũ")
    return None
