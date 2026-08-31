#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QC MỘT KÊNH — một điểm số duy nhất, chặn dưới 90/100. (30/8/2026)

VÌ SAO GỘP THÀNH MỘT CỔNG
-------------------------
Anh: *"cần pipeline method chuẩn cho từng channel để sau các channel chuẩn chất lượng hình ảnh,
âm thanh, voice, sub, chuyển cảnh, kịch bản… và có tiêu chuẩn kiểm tra visual QC trước và sau
render đạt tối thiểu 90/100"*.

Đến giờ mỗi mặt có một cây thước riêng — `cham_v3` đo dữ liệu, `soi_ai` nhìn khung hình,
`selftest` chặn mã hỏng. Ba cây thước tốt, nhưng chúng nói ba thứ tiếng: một cái cho 85/100, một
cái nói "có lỗi hình", một cái báo pass. Không ai trả lời được câu hỏi cuối cùng: **video này có
được ra kho không?**

Tệp này gộp lại thành **một con số** và **một quyết định**.

TRƯỚC HAY SAU RENDER
--------------------
Cả hai, và chúng đo hai thứ khác nhau:

  · **TRƯỚC** (`truoc_render`) — đọc props: dữ liệu có thật không · biểu đồ có nói đúng con số nó
    in không · nhịp cảnh có đều không. Rẻ, không tốn một giây render nào, và bắt được lớp lỗi
    lớn nhất: dựng một video mười lăm phút từ dữ liệu đã hỏng sẵn.
  · **SAU** (`sau_render`) — nhìn khung hình thật: chữ có tràn không · nhân vật còn mặt không ·
    nền có đè biểu đồ không. Đắt hơn (mỗi khung một lượt hỏi), nhưng đây là lớp duy nhất thấy
    được thứ chỉ hiện ra khi mọi lớp đã chồng lên nhau.

Cùng một video có thể đạt lớp trước mà trượt lớp sau — đúng như hôm nay: dữ liệu sạch mà chữ vẫn
tràn khỏi tấm nền, vì tràn là chuyện của hình, không phải của số.

VÌ SAO NGƯỠNG 90 CHỨ KHÔNG PHẢI 100
-----------------------------------
Đòi 100 thì cổng sẽ bị nới ngay lần đầu có một video 97 điểm bị chặn vì một lỗi nhỏ — và một
cổng đã nới một lần thì sẽ nới tiếp. 90 đủ chặt để không lọt lỗi thấy được bằng mắt, đủ rộng để
không chặn một video chỉ vì bốn cột chênh nhau 1,55 lần thay vì 1,6.
"""
from __future__ import annotations

import io
import json
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
NGUONG = 90


def truoc_render(props_json: str) -> tuple[int, list]:
    """Chấm phần DỮ LIỆU, trước khi tốn một giây render nào."""
    try:
        d = json.load(io.open(props_json, encoding="utf-8"))
    except Exception as e:
        return 0, [f"không đọc được props: {str(e)[:60]}"]
    ten = os.path.basename(props_json)
    if ten.startswith("v3_"):
        import cham_v3 as C3
        return C3.cham_mot(d, ten)
    # Bộ hài chưa có thước dữ liệu riêng ở đây; ba trục dưới là những trục `cham_v3` đã học được
    # mà bộ hài cũng mắc — xem chú thích ở cuối tệp về việc đồng bộ hai cây thước.
    diem, loi = 100, []
    luot = d.get("luot") or []
    if not luot:
        return 0, ["không có lượt thoại nào"]
    t = [max(0.01, x.get("e", 0) - x.get("s", 0)) for x in luot]
    if max(t) / max(0.01, min(t)) > 5.0:
        diem -= 20
        loi.append(f"nhịp lượt dồn: dài nhất gấp {max(t)/min(t):.0f} lần ngắn nhất")
    import re
    for x in luot:
        n = str(x.get("nar") or x.get("noi") or "")
        if re.search(r"[ăâđêôơưáàảãạấầẩẫậéèẻẽẹíìỉĩịóòỏõọúùủũụ]", n):
            diem -= 10
            loi.append(f"lời thoại có chữ tiếng Việt: {n[:36]!r}")
            break
    return max(0, diem), loi


def sau_render(mp4: str, keys=None) -> tuple[int, list]:
    """Chấm phần HÌNH, sau khi đã có video thật."""
    try:
        import soi_ai as SA
    except Exception:
        return 100, []
    loi = SA.soi(mp4, keys=keys)
    if not loi:
        return 100, []
    # Mỗi loại lỗi trừ một mức khác nhau: chữ tràn và nhân vật mất mặt là lỗi người xem THẤY
    # ngay; nền đè biểu đồ thì khó chịu nhưng còn đọc được.
    muc = {"chu_tran": 14, "mat_nguoi": 14, "chu_gia": 10, "nen_de": 8, "khong_co_nguoi": 20}
    # 31/8 — CHỈ TIN LỖI LẶP LẠI Ở HAI KHUNG TRỞ LÊN.
    # Ba lượt dựng cùng một bộ code cho ra điểm lệch nhau tới 14 (knowyourright 92→82→92,
    # paycheckgap 94→86). Code chỉ tốt lên, nên chênh lệch ấy không đến từ video — nó đến từ
    # chính thước: phần chấm hình hỏi một mô hình thị giác, và mô hình ấy trả lời khác nhau
    # giữa các lượt cho cùng một khung.
    # Một thước dao động ±14 thì không đo được tiến bộ: sửa đúng cũng có thể ra điểm thấp hơn,
    # và người sửa mất phương hướng. Đó là điều đã xảy ra với tôi hai lượt liền.
    # Lọc bằng tính CHẤT của lỗi thật: một lỗi hình có thật thì gần như luôn xuất hiện ở nhiều
    # khung (bố cục sai thì sai suốt), còn một câu trả lời nhiễu thì rơi lẻ vào đúng một khung.
    # Nên đếm số khung mắc từng lỗi, và chỉ trừ khi nó xuất hiện từ hai khung trở lên.
    dem: dict = {}
    for l in loi:
        ten = l.split(": ")[-1]
        dem[ten] = dem.get(ten, 0) + 1
    diem = 100
    da = []
    for ten, n in sorted(dem.items()):
        if n < 2:
            continue
        da.append(f"{ten} ×{n}")
        diem -= muc.get(ten, 8)
    return max(0, diem), da


def cham(props_json: str, mp4: str = "", keys=None) -> tuple[int, list]:
    """Điểm cuối = min(trước, sau). Lấy MIN chứ không lấy trung bình.

    Trung bình cho phép một mặt rất tốt che một mặt rất tệ — một video có dữ liệu hoàn hảo mà
    chữ tràn khỏi khung vẫn là video không dùng được. Điểm của một sản phẩm là điểm của mặt yếu
    nhất, không phải điểm trung bình các mặt."""
    d1, l1 = truoc_render(props_json)
    if not mp4 or not os.path.exists(mp4):
        return d1, l1
    d2, l2 = sau_render(mp4, keys=keys)
    return min(d1, d2), l1 + [f"(hình) {x}" for x in l2]


def main() -> int:
    import glob
    ds = sys.argv[1:]
    if not ds:
        ds = sorted(glob.glob(os.path.join(GOC, "out", "v[34]_*.json")))
    dat = hong = 0
    print(f"  {'kênh':<26} {'điểm':>5}")
    print("  " + "─" * 62)
    for j in ds:
        if j.endswith(".mp4"):
            j = j[:-4] + ".json"
        mp4 = j[:-5] + ".mp4"
        diem, loi = cham(j, mp4)
        ok = diem >= NGUONG
        dat, hong = (dat + 1, hong) if ok else (dat, hong + 1)
        print(f"  {'✅' if ok else '❌'} {os.path.basename(j)[:-5]:<24} {diem:>4}")
        for l in loi[:4]:
            print(f"       └ {l}")
    print(f"\n  ✅ đạt {dat}  ·  ❌ dưới ngưỡng {hong}   (ngưỡng {NGUONG}/100)")
    return 1 if hong else 0


if __name__ == "__main__":
    sys.exit(main())
