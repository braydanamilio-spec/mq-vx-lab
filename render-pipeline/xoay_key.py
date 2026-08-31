#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XOAY KHOÁ — MỘT ĐƯỜNG DUY NHẤT, CHẶN LỖI "TƯỞNG HẾT QUOTA" (31/8/2026)
════════════════════════════════════════════════════════════════════════════════════════════

Anh: *"qua cũng bị lỗi thế sao nay vẫn bị, cần fix đúng rule ko lặp lại nha"* và *"fix cả auto
trên pipeline sau này tự động trên github"*.

Anh nói đúng chỗ đau: luật đã ghi trong PIPELINE_RULES từ hôm qua, mà hôm nay tôi lặp lại y
nguyên — vì luật chỉ nằm trong tài liệu, không có gì trong CODE chặn nó.

── LỖI GỐC ───────────────────────────────────────────────────────────────────────────────
Cloudflare trả HTTP 429 cho HAI chuyện khác hẳn nhau:
    · hết neuron trong ngày (mã 4006)  — thật sự phải chờ;
    · gọi quá nhanh, giới hạn theo phút — chỉ cần nghỉ một nhịp.
Thông điệp lỗi cũ ghi cứng "hết neuron CF trong ngày" cho cả hai. Tôi đọc log, thấy dòng ấy,
rồi báo với anh rằng phải chờ hôm sau — trong khi 94 tài khoản CF mới dùng 52 ảnh trên trần
khoảng 16.000 ảnh/ngày, và ảnh NGAY SAU đó vẫn sinh thành công.

── BA THỨ TỆP NÀY BẢO ĐẢM ────────────────────────────────────────────────────────────────
  1. XOAY TỪ VỊ TRÍ KHÁC NHAU. Luôn bắt đầu từ khoá đầu danh sách nghĩa là mỗi lần gọi đều
     đâm vào đúng khoá vừa cạn, và mỗi lần đâm vẫn TRỪ hạn mức của nhà cung cấp.
  2. NGHỈ KHI GẶP RATE-LIMIT. 429 không kèm mã 4006 thì nghỉ một nhịp rồi đi tiếp; không coi
     là hỏng.
  3. CHỈ ĐƯỢC KẾT LUẬN "CẠN" KHI ĐÃ THỬ HẾT. Và khi ấy vẫn phải nói rõ đã thử bao nhiêu khoá,
     bao nhiêu cái báo 4006 — con số ấy là thứ phân biệt "cạn thật" với "gọi quá nhanh".

Mọi chỗ gọi ảnh CF đều phải đi qua đây, kể cả trong GitHub Actions.
"""
import os
import time
import random


class CanThat(Exception):
    """Cạn hạn mức THẬT: mọi khoá đều trả mã 4006 (hết neuron ngày)."""


def loc_cf(keys) -> list:
    ra = []
    for k in keys or []:
        s = k if isinstance(k, str) else (k.get("key", "") if isinstance(k, dict) else "")
        if s.startswith("cf:"):
            ra.append(s)
    return ra


def goi_xoay(keys, ham, hat: int = 0, nghi_ratelimit: float = 1.2, giua_lan: float = 0.25):
    """Gọi `ham(khoa)` lần lượt qua các khoá cho tới khi một khoá trả về giá trị "thật".

    `ham` trả về giá trị falsy (hoặc ném lỗi) thì thử khoá tiếp theo.
    Ném `CanThat` chỉ khi MỌI khoá đều báo mã 4006 — tức cạn thật, không phải gọi nhanh.
    """
    cf = loc_cf(keys)
    if not cf:
        return None, {"da_thu": 0, "cf": 0, "ly_do": "không có khoá CF nào"}

    # Điểm bắt đầu đổi theo `hat` — mỗi ảnh/mỗi lần gọi vào một chỗ khác trong vòng khoá.
    dau = (hat * 7919 + random.randint(0, 97)) % len(cf)
    so_4006 = so_429 = so_khac = 0

    for i in range(len(cf)):
        k = cf[(dau + i) % len(cf)]
        try:
            r = ham(k)
            if r:
                return r, {"da_thu": i + 1, "cf": len(cf), "4006": so_4006, "429": so_429}
            so_khac += 1
        except Exception as e:
            t = str(e)
            if "4006" in t or "neuron" in t.lower():
                so_4006 += 1
            elif "429" in t:
                so_429 += 1
                time.sleep(nghi_ratelimit)     # rate-limit theo phút: nghỉ rồi đi tiếp
            else:
                so_khac += 1
        time.sleep(giua_lan)

    tk = {"da_thu": len(cf), "cf": len(cf), "4006": so_4006, "429": so_429, "khac": so_khac}
    if so_4006 >= len(cf):
        raise CanThat(f"cả {len(cf)} khoá CF đều hết neuron ngày (4006)")
    return None, tk


def bao_cao(tk: dict) -> str:
    """Câu báo cáo TRUNG THỰC — không được nói 'hết quota' khi chưa thử hết."""
    if not tk or not tk.get("cf"):
        return "không có khoá CF"
    if tk.get("da_thu", 0) < tk["cf"]:
        return f"xong sau {tk['da_thu']}/{tk['cf']} khoá"
    return (f"thử hết {tk['cf']} khoá · {tk.get('4006', 0)} cạn ngày · "
            f"{tk.get('429', 0)} rate-limit · {tk.get('khac', 0)} lỗi khác")
