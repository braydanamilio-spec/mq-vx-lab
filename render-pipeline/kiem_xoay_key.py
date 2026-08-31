#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CỔNG XOAY KHOÁ — chặn lỗi "tưởng hết quota" tái diễn, kể cả trong GitHub Actions (31/8/2026)

Anh: *"qua cũng bị lỗi thế sao nay vẫn bị, cần fix đúng rule ko lặp lại"*. Luật đã ghi từ hôm
qua mà hôm nay lặp lại — vì luật nằm trong tài liệu, không có gì trong CODE chặn.

Cổng này quét mã nguồn tìm ba dấu hiệu của lỗi ấy. Chạy trước mỗi lần dựng lô, và chạy trong
workflow trước khi gọi bất kỳ API nào.
"""
import os
import re
import io
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
BO_QUA = {"xoay_key.py", "kiem_xoay_key.py", "datastory_ci.py", "content_brain.py", "the_he_2.py"}

# 1. Thông điệp KHẲNG ĐỊNH cạn quota mà không kèm bằng chứng đã thử hết khoá
# 31/8, thu hẹp lần hai. Lượt trước còn tố oan `run_render.py` — vòng `for k in all_keys` ở đó
# là vòng KIỂM TRA SỨC KHOẺ khoá, không phải vòng gọi ảnh; và hai dòng `firestore_bridge.py`
# nói về Firestore cạn hạn mức, một chuyện có thật.
#
# Bài học lặp lại lần thứ hai trong ngày: một cổng chỉ đáng tin khi nó bắt ĐÚNG cái mẫu đã có
# bằng chứng, không bắt mọi thứ trông giống. Ở đây bằng chứng là: thông điệp nói CF/neuron cạn
# NGÀY, và vòng lặp khoá có gọi hàm sinh ảnh bên trong.
KHANG_DINH = re.compile(
    r'["\'][^"\']*(?:cf|cloudflare|neuron)[^"\']*(?:hết|cạn)[^"\']*(?:ngày|quota|hạn mức)'
    r'|["\'][^"\']*(?:hết|cạn)\s*(?:neuron)[^"\']*(?:trong\s*)?ngày', re.I)
# 2. Vòng lặp khoá tự viết CÓ GỌI SINH ẢNH bên trong (thay vì dùng đường chung)
TU_VIET = re.compile(r'for\s+\w+\s+in\s+\w*keys?\w*\s*:', re.I)
GOI_ANH = re.compile(r'_cf_flux_image|flux-1-schnell')


def main() -> int:
    # 31/8 — lượt chạy đầu của cổng này tố oan hai chỗ trong `firestore_bridge.py`: chúng nói
    # về Firestore cạn hạn mức, một chuyện có thật và đo được, không liên quan tới Cloudflare.
    # Đúng cái bẫy đã ghi ở mục 7E — cổng tự viết mà không thu hẹp thì sinh ra lời tố oan, và
    # lời tố oan làm người ta thôi tin cả cái cổng.
    # Thu hẹp: chỉ xét tệp thật sự đụng tới khoá ẢNH Cloudflare.
    loi = []
    for t in sorted(os.listdir(GOC)):
        if not t.endswith(".py") or t in BO_QUA:
            continue
        d = io.open(os.path.join(GOC, t), encoding="utf-8", errors="ignore").read()
        if not ("cf:" in d or "flux" in d.lower() or "_cf_flux_image" in d):
            continue
        for i, dong in enumerate(d.split("\n"), 1):
            if dong.lstrip().startswith("#"):
                continue
            if KHANG_DINH.search(dong):
                loi.append((t, i, "khẳng định cạn quota trong thông điệp", dong.strip()[:70]))
            if TU_VIET.search(dong) and "goi_xoay" not in d:
                # chỉ tính là lỗi nếu TRONG vòng lặp ấy có gọi hàm sinh ảnh
                than = "\n".join(d.split("\n")[i:i + 14])
                if GOI_ANH.search(than):
                    loi.append((t, i, "tự viết vòng lặp khoá quanh lệnh sinh ảnh", dong.strip()[:70]))

    if not loi:
        print("✅ xoay khoá: không chỗ nào tự viết vòng lặp hay khẳng định cạn quota")
        return 0
    print(f"❌ {len(loi)} chỗ có nguy cơ lặp lại lỗi 'tưởng hết quota':")
    for t, i, vs, d in loi:
        print(f"   {t}:{i}  {vs}\n      {d}")
    print("\n   Sửa: dùng `from xoay_key import goi_xoay, bao_cao, CanThat`.")
    print("   Chỉ được nói 'cạn' khi goi_xoay ném CanThat — tức MỌI khoá đều trả mã 4006.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
