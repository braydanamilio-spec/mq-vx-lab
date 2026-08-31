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
    "giữa để trống":          [r"cent(?:er|re) of the frame (?:completely )?empty",
                               r"open space in the cent(?:er|re)",
                               r"leaving the cent(?:er|re)"],
}
# Tệp có dựng prompt vẽ nền
TEP = ["nen_cf.py", "kich_v2.py", "kich_hai.py"]


def main() -> int:
    thieu_tong = []
    for t in TEP:
        d = os.path.join(GOC, t)
        if not os.path.exists(d):
            continue
        s = io.open(d, encoding="utf-8", errors="ignore").read()
        # Chỉ xét tệp thật sự DỰNG prompt nền. Bộ lọc đầu chỉ tìm lời gọi API trực tiếp, nên
        # bỏ sót `kich_v2.py` và `kich_hai.py` — hai chỗ dựng prompt rồi đưa cho lớp khác gọi.
        # Đúng cái bẫy đã gặp mấy lần hôm nay: bộ lọc hẹp quá thì cổng im lặng bỏ qua đúng chỗ
        # cần soi, mà im lặng thì trông y hệt "không có vấn đề".
        if not re.search(r"_cf_flux_image|flux-1-schnell|fetch_image\(|GU_NEN|SAN_NEN|NEN_V3", s):
            continue
        thieu = [ten for ten, mau in MENH_LENH.items()
                 if not any(re.search(m, s, re.I) for m in mau)]
        dau = "✅" if not thieu else "❌"
        print(f"  {dau} {t:16s} " + ("đủ ba mệnh lệnh" if not thieu else "THIẾU: " + " · ".join(thieu)))
        if thieu:
            thieu_tong.append((t, thieu))

    if not thieu_tong:
        print("\n✅ mọi đường vẽ nền đều ép sàn, ngang tầm mắt, chừa giữa")
        return 0

    print("\n❌ có đường vẽ nền thiếu mệnh lệnh — nhân vật sẽ lơ lửng ở đó.")
    print("   Câu chuẩn (đang dùng trong `kich_hai.SAN_NEN`):")
    print('     "wide shot, camera at standing eye level, floor clearly visible across the')
    print('      lower third, open space in the centre of the frame"')
    print("   Đừng viết lại câu thứ hai — import `SAN_NEN` về dùng.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
