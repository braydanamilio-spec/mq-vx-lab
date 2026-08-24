#!/usr/bin/env python3
"""QUY ƯỚC ĐẶT TÊN FILE — MỘT NGUỒN DUY NHẤT (24/8/2026).

    KENH__YYYYMMDD__SERI__VAI__tieu-de-khong-dau
    DEFENSEUSA__20260824__ab3xk9__L__The-750B-Question-Nobody-Asks
    DEFENSEUSA__20260824__ab3xk9__S1__Part-1-Where-The-Money-Goes

Ô `SERI` là **mã job của video LONG**: long và 3 short đẻ ra từ nó dùng CHUNG một mã, nên nhìn tên
file là biết ngay chúng thuộc một chùm — cần cho khâu đăng (short phải kéo người về đúng long của
nó). Video cũ không có mã đó thì **bỏ hẳn ô SERI** (4 đoạn thay vì 5); tuyệt đối không bịa một mã
ngẫu nhiên, vì mã bịa trông y như mã thật mà lại nhóm sai.

Thumbnail / sidecar / phụ đề luôn = tên video + đuôi riêng, nên chỉ cần một hàm này là cả bốn khớp.

Để trong file riêng vì `run_render.py` (lúc render) và `doi_ten_kho.py` (lúc sửa tên file cũ) đều
cần — hai bản chép tay sẽ lệch nhau vào một ngày nào đó.
"""
from __future__ import annotations

import re
from datetime import datetime as _dt, timezone as _tz

VAI = re.compile(r"^(L|S\d*)$", re.I)
TRAN = 96          # Drive cho tên dài hơn, nhưng dài quá thì cột tên trên dashboard vỡ


def lat(x: str, n: int = 0) -> str:
    """Bỏ dấu/ký tự lạ -> chỉ còn chữ, số và gạch nối."""
    r = re.sub(r"[^A-Za-z0-9]+", "-", str(x or "")).strip("-")
    return r[:n] if n else r


def ten_file(channel: str, story: dict, vtype: str, seri: str = "", bo: str = "",
             ngay: str = "") -> str:
    """Xem chú thích đầu file. Tiêu đề bị CẮT còn 46 ký tự nên hai bài khác nhau vẫn có thể ra
    cùng một tên — 24/8 tối, chạy thử bắt được ca thật:
        'Which state pays the most for electricity in 2026 really'
        'Which state pays the most for electricity in 2026 truly'
    -> cùng ra `GUESSUSA__20260824__S__Which-state-pays-the-most-for-electricity-in-2`.
    Trên Drive thành hai file TRÙNG TÊN trong một thư mục, và `find_junk` loại 2 sẽ bỏ cái cũ vào
    thùng rác — **xoá mất một video thật**. Sidecar/thumbnail cũng lấy tên theo gốc này nên còn bị
    móc chéo sang nhau.
    Nên: hễ tiêu đề BỊ CẮT thì gắn thêm 4 ký tự băm của tiêu đề ĐẦY ĐỦ. Tên đủ dài thì không gắn gì
    (giữ tên sạch), vì lúc đó trùng tên nghĩa là trùng đúng nội dung."""
    _goc = str((story or {}).get("title") or (story or {}).get("topic") or vtype)
    tieu_de = lat(_goc, 46)
    if len(lat(_goc)) > 46:
        import hashlib as _h
        tieu_de += "-" + _h.sha1(_goc.encode("utf-8")).hexdigest()[:4]
    phan = [lat(channel), ngay or _dt.now(_tz.utc).strftime("%Y%m%d")]
    if seri:
        phan.append(lat(seri, 6).lower())
    phan.append(bo or ("L" if vtype == "long" else "S"))
    phan.append(tieu_de)
    return "__".join(p for p in phan if p)[:TRAN]


def doc_vai(ten: str) -> str:
    """long/short suy từ tên file — DÒ ô vai trò chứ không lấy theo vị trí cố định.

    Tên có SERI dài 5 đoạn, không SERI dài 4; lấy cứng `p[3]` là đọc nhầm nửa số file. Tên đời cũ
    (`KENH__tieu-de`) thì không có ô nào cả -> đoán theo chữ 'long', còn lại coi là short (short
    chiếm đa số nên đoán sai ít hơn)."""
    for p in str(ten or "").split("__"):
        if VAI.match(p):
            return "l" if p.upper() == "L" else "s"
    return "l" if "long" in str(ten or "").lower() else "s"


def da_chuan(ten: str) -> bool:
    """Tên đã theo quy ước chưa (có ô ngày 8 số và ô vai trò)."""
    p = str(ten or "").rsplit(".", 1)[0].split("__")
    return len(p) >= 4 and bool(re.fullmatch(r"\d{8}", p[1] or "")) and any(VAI.match(x) for x in p)
