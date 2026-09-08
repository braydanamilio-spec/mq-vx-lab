#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CỔNG PROMPT NỀN — ba mệnh lệnh bắt buộc, không được thiếu cái nào (31/8/2026)

Anh: *"cái ép sàn chiếm trọn phần ba dưới, đồ đạc dồn hai mép, giữa để trống đang hoạt động
tốt mà mấy bữa nay ko fix được — e đã làm được thì nên note lại đưa vào pepline methord rule
chuẩn để sau ko lỗi lặp lại"*.

Ba mệnh lệnh này chữa được lỗi "nhân vật lơ lửng" đã đeo bám cả bộ hài cũ lẫn 56 kênh phân
tích. Nhưng ghi vào tài liệu là chưa đủ — hôm nay đã có bằng chứng: `kich_hai.py` CÓ sẵn câu
`SAN_NEN` đúng như thế từ lâu, mà `kich_v2.py` chỉ lấy `GU_NEN` và bỏ qua nó, nên suốt thời
gian ấy nền 56 kênh phân tích chưa bao giờ được ép sàn — và không ai biết.

Cổng này quét mọi chỗ dựng prompt vẽ nền, kiểm đủ ba mệnh lệnh. Chạy trước mỗi lần dựng lô.
"""
import os
import re
import io

GOC = os.path.dirname(os.path.abspath(__file__))

# Ba mệnh lệnh, mỗi cái nhận nhiều cách diễn đạt (chúng được viết ở ba tệp khác nhau, bởi ba
# lần khác nhau — bắt đúng một chuỗi thì cổng sẽ tố oan ngay khi ai đó viết lại cho gọn hơn).
MENH_LENH = {
    "sàn chiếm phần ba dưới": [r"bottom third", r"lower third"],
    "máy ngang tầm mắt":      [r"standing eye level", r"eye[- ]level"],
    # ── CHỪA CHỖ CHO NGƯỜI: GIỮA hay MỘT BÊN, tuỳ engine đặt người ở đâu (8/9/2026) ──
    # Hai mệnh lệnh cũ ("giữa để trống" · "đồ dồn hai mép") sinh ra khi engine dán nhân vật
    # VECTOR vào GIỮA khung. Anh đã cho người dẫn đứng 1/3 và LỆCH HẲN MỘT BÊN, nên `pilot_hai`
    # nay chừa MỘT DẢI BÊN và để đồ đạc đứng tụ ở hai phần ba còn lại.
    #
    # Vì sao phải sửa CỔNG chứ không chỉ sửa prompt: cổng vẫn báo xanh sau khi em đổi prompt —
    # nó xanh vì `pilot_hai` còn `import SAN_NEN_VAT`, không phải vì prompt còn tuân luật. Một
    # cổng in ra "đồ dồn hai mép · giữa trống" cho đường vẽ đã bỏ hai điều ấy là cổng NÓI DỐI,
    # và lần sau nó sẽ không bắt được hồi quy thật (§12.8 — hỏng mà vẫn báo xanh).
    #
    # Điều CẦN canh không đổi: phải có MỘT vùng trống đủ rộng cho người đứng, và đồ đạc phải
    # tụ lại chứ không rải khắp khung. Chấp nhận cả hai cách diễn đạt.
    "chừa chỗ cho người":     [r"cent(?:er|re) of the frame (?:completely )?empty",
                               r"cent(?:er|re) of the frame is empty",
                               r"open space in the cent(?:er|re)",
                               r"leaving the cent(?:er|re)",
                               r"(?:left|right) third of the frame is open"],
    "đồ đạc tụ một phía":     [r"pushed (?:far )?to the (?:far )?left and (?:far )?right",
                               r"against the left and right edges",
                               r"at the (?:two |both )?side edges",
                               r"stand together in the (?:left|right) two thirds"],
}

# 1/9 — CẤM VIẾT NGHỊCH. FLUX không có negative prompt: mọi danh từ trong câu đều là thứ nó sẽ
# vẽ. `no furniture blocking the middle` vì thế đẻ ra đúng cái đồ chắn giữa khung mà nó định
# cấm — và che mất dải sàn. Cổng chặn luôn dạng câu này để không ai viết lại lần nữa.
CAM_NGHICH = [
    r"no furniture", r"nothing in the (?:middle|cent(?:er|re))", r"without any furniture",
    r"no objects in the cent(?:er|re)", r"empty of furniture",
    # 8/9/2026 — CẤM CHỮ BẰNG PHỦ ĐỊNH cũng là viết nghịch, và đắt hơn `no furniture`: chữ
    # loằng ngoằng trong khung là thứ người xem đọc ra "nghiệp dư" nhanh nhất (§13.20).
    r"no text", r"no letters", r"no signage", r"no words", r"without any text",
]
# Tệp có dựng prompt vẽ nền
# ── DANH SÁCH CHÉP TAY LÀ CỔNG CHE LỖI  (§13.2, và nó vừa che một lỗi thật) ─────────────────
# Ba tên trên là danh sách gõ tay, và `pilot_hai.py` — nơi dựng prompt nền cho CẢ 18 kênh của
# bộ mới — không có trong đó. Nên đuôi `"no text, no letters, no signage"` sống ở đấy nhiều
# ngày mà cổng chưa bao giờ soi tới, dù cổng sinh ra đúng để bắt loại câu ấy.
# Nay TỰ TÌM: mọi tệp .py khai `GU_NEN` hoặc `SAN_NEN`, cộng ba tên cũ để không mất phạm vi.
TEP = sorted({*["nen_cf.py", "kich_v2.py", "kich_hai.py"],
              *[f for f in os.listdir(os.path.dirname(os.path.abspath(__file__)))
                if f.endswith(".py")
                and re.search(r"^(GU_NEN|SAN_NEN)\w*\s*=",
                              io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f),
                                      encoding="utf-8", errors="ignore").read(), re.M)]})


def _doc_ma(s: str) -> str:
    """Trả về phần MÃ THẬT: bỏ chú thích, nối chuỗi ngắt dòng.

    1/9 — cổng vừa tố oan hai chỗ, và cả hai lần đều do chính nó quét chữ thô:
      · `kich_hai.py` bị báo "viết nghịch" vì trong CHÚ THÍCH tôi trích lại câu hỏng để giải
        thích vì sao nó hỏng. Cổng đọc lời kể về con dao thành con dao.
      · `kich_v2.py` bị báo thiếu "đồ đạc dồn hai mép" trong khi câu ấy có đủ — nhưng viết vắt
        qua hai dòng (`"…far left " "and far right edges…"`), nên giữa hai từ có dấu nháy và
        xuống dòng, biểu thức chính quy trượt.
    Cổng báo sai còn tệ hơn cổng im lặng: lần sau người ta sẽ tắt nó đi cho đỡ phiền."""
    s = re.sub(r"(?m)^\s*#.*$", "", s)                 # chú thích cả dòng
    s = re.sub(r'(?<!["\\])#(?![^\n"]*").*$', "", s, flags=re.M)   # chú thích cuối dòng
    s = re.sub(r'"\s*\n\s*"', "", s)                    # nối chuỗi ẩn ngắt dòng
    s = re.sub(r"'\s*\n\s*'", "", s)
    return s


def main() -> int:
    thieu_tong = []
    for t in TEP:
        d = os.path.join(GOC, t)
        if not os.path.exists(d):
            continue
        s = _doc_ma(io.open(d, encoding="utf-8", errors="ignore").read())
        # Chỉ xét tệp thật sự DỰNG prompt nền. Bộ lọc đầu chỉ tìm lời gọi API trực tiếp, nên
        # bỏ sót `kich_v2.py` và `kich_hai.py` — hai chỗ dựng prompt rồi đưa cho lớp khác gọi.
        # Đúng cái bẫy đã gặp mấy lần hôm nay: bộ lọc hẹp quá thì cổng im lặng bỏ qua đúng chỗ
        # cần soi, mà im lặng thì trông y hệt "không có vấn đề".
        if not re.search(r"_cf_flux_image|flux-1-schnell|fetch_image\(|GU_NEN|SAN_NEN|NEN_V3", s):
            continue
        # Tệp IMPORT `SAN_NEN` từ `kich_hai` là tệp làm ĐÚNG thứ cổng này khuyên ("đừng viết
        # lại"), nên không được tính là thiếu mệnh lệnh — bốn mệnh lệnh nằm trong hằng số nó
        # nhập về. Bản đầu của phạm vi mở rộng tố oan `pilot_hai.py` đúng vì lý do ấy, và cổng
        # bắt oan tệ hơn cổng không bắt (§13.8).
        _nhap = re.search(r"from\s+kich_hai\s+import[^\n]*SAN_NEN", s)
        thieu = [] if _nhap else [ten for ten, mau in MENH_LENH.items()
                                  if not any(re.search(m, s, re.I) for m in mau)]
        # Câu viết NGHỊCH tính là lỗi ngang với thiếu mệnh lệnh: nó không những không cấm được
        # gì, mà còn chủ động vẽ ra đúng thứ định cấm.
        nghich = sorted({re.search(c, s, re.I).group(0) for c in CAM_NGHICH if re.search(c, s, re.I)})
        dau = "✅" if not thieu and not nghich else "❌"
        cho = "đủ bốn mệnh lệnh" if not thieu else "THIẾU: " + " · ".join(thieu)
        if nghich:
            cho += ("  |  " if thieu else "") + "VIẾT NGHỊCH: " + " · ".join(nghich)
        print(f"  {dau} {t:16s} " + cho)
        if thieu or nghich:
            thieu_tong.append((t, thieu + [f"viết nghịch: {x}" for x in nghich]))

    if not thieu_tong:
        print("\n✅ mọi đường vẽ nền: sàn liền mạch · ngang tầm mắt · đồ tụ một phía · chừa chỗ cho người")
        return 0

    print("\n❌ có đường vẽ nền thiếu mệnh lệnh — nhân vật sẽ lơ lửng ở đó.")
    print("   Câu chuẩn (đang dùng trong `kich_hai.SAN_NEN`):")
    print('     "wide shot, camera at standing eye level, the ground plane fills the entire')
    print('      bottom third of the frame as one continuous unbroken surface running from the')
    print('      left edge to the right edge, all furniture and objects pushed far to the left')
    print('      and right edges, the centre of the frame is empty walkable floor"')
    print("   Đừng viết lại — import `SAN_NEN` từ `kich_hai` về dùng.")
    print("   Và đừng viết NGHỊCH (`no furniture…`): FLUX không có negative prompt, câu cấm")
    print("   biến thành lệnh vẽ. Mô tả thứ MUỐN thấy.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
