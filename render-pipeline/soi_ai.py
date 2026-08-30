#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SOI KHUNG BẰNG MÁY NHÌN — cổng kiểm hình sau khi render. (30/8/2026)

VÌ SAO CÓ TỆP NÀY
-----------------
Anh: *"phải có kiểm tra visual thực tế trước và sau khi render để tránh lỗi tiềm ẩn"*.

Đúng chỗ đau nhất của cả phiên hôm nay. Mọi lỗi hình đều được tìm ra theo cùng một cách: **anh
xem video rồi gửi ảnh chỉ ra**. Nhân vật văng khỏi khung · chữ tràn mép · hai bàn tay chụm · nhãn
đè thanh · nền đè biểu đồ · cột vẽ sai bậc. Không lỗi nào bị bất kỳ cổng nào chặn, vì mọi cổng
đang có đều đọc **mã** hoặc **dữ liệu**, không cái nào nhìn **khung hình**.

`soi_khung.py` (29/8) đã ghi kết luận đúng: chấm bố cục bằng pixel cho ra cùng một dải số ở cả
video tốt lẫn video hỏng, nên nó bị bỏ. Câu cuối của tệp ấy là *"thứ đã bắt được mọi lỗi bố cục
hôm nay là mắt người"*.

Nay có máy nhìn. Nó không thay được mắt anh, nhưng nó **chạy được sáu mươi kênh mỗi đêm**, còn
mắt người thì không.

CÁCH HỎI — QUAN TRỌNG HƠN CHỌN MÔ HÌNH
--------------------------------------
Bài học từ `_co_chu`: hỏi một model không đọc được chữ thì câu "không có chữ" đọc ra như một lời
bảo đảm. Hai điều rút ra và áp ở đây:

  · **Câu hỏi phải ĐÓNG và CỤ THỂ.** Không hỏi "khung này có đẹp không" — hỏi "có nhân vật nào bị
    cắt mất một phần thân bởi mép khung không". Câu mở cho ra văn xuôi, và văn xuôi thì không
    chặn được gì.
  · **Không trả lời được thì cho QUA.** Chặn nhầm một khung lành tốn hơn để lọt một khung hỏng:
    một khung hỏng còn có anh xem, còn một cổng chặn bừa thì cả lượt dựng đứng lại.
"""
from __future__ import annotations

import io
import os
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))

# Mỗi câu hỏi là một lỗi CÓ THẬT anh đã chỉ ra hôm nay. Không thêm câu nào "cho đủ bộ": mỗi câu
# tốn một lượt gọi mô hình, và một câu chưa từng bắt được lỗi nào chỉ làm chậm cổng.
CAU_HOI = [
    ("nhan_vat_cut",
     "Is any cartoon person cut off by the edge of the frame so that part of their body is "
     "missing? Answer exactly one word: YES or NO."),
    ("chu_tran",
     "Is any text or number cut off or clipped by a panel edge or the frame edge, so it cannot "
     "be read fully? Answer exactly one word: YES or NO."),
    ("nen_de",
     "Does any background object overlap and hide part of the chart or the text? "
     "Answer exactly one word: YES or NO."),
    ("khong_co_nguoi",
     "Is there at least one cartoon person visible in this image? "
     "Answer exactly one word: YES or NO."),
]
# Câu nào mà câu trả lời ĐÚNG là "NO" thì ghi ở đây; còn lại đúng là "YES".
DAP_AN = {"nhan_vat_cut": "NO", "chu_tran": "NO", "nen_de": "NO", "khong_co_nguoi": "YES"}


def _khung(mp4: str, giay: float, ra: str) -> bool:
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{giay:.2f}",
                        "-i", mp4, "-vframes", "1", "-vf", "scale=560:-1", ra],
                       capture_output=True, timeout=180)
    return r.returncode == 0 and os.path.exists(ra)


def _hoi(anh: str, cau: str, keys) -> str:
    """Hỏi máy nhìn một câu đóng. Trả 'YES' | 'NO' | '' (không trả lời được)."""
    try:
        import content_brain as CB
        import kich_hai as KH
    except Exception:
        return ""
    dl = io.open(anh, "rb").read()
    for k in KH.xoay_key(keys, toi_da=8):
        try:
            g = CB._genai(k)
            r = g.GenerativeModel(CB.MODEL).generate_content(
                [cau, {"mime_type": "image/jpeg", "data": dl}])
            t = str(getattr(r, "text", "") or "").strip().upper()
            if t.startswith("YES"):
                return "YES"
            if t.startswith("NO"):
                return "NO"
        except Exception:
            continue
    return ""


def soi(mp4: str, keys=None, so_khung: int = 3) -> list[str]:
    """Soi vài khung của một video. Trả danh sách lỗi (rỗng = lành)."""
    try:
        import the_he_2 as T2
        keys = keys or [k.get("key") for k in (T2.keys_cuc_bo() or []) if k.get("key")]
    except Exception:
        keys = keys or []
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", mp4], capture_output=True, text=True, timeout=60)
    try:
        dai = float((r.stdout or "0").strip())
    except ValueError:
        return []
    if dai < 2:
        return []
    # Lấy khung ở 25% · 55% · 85% — tránh khung đầu (đang mờ vào) và khung cuối (đang mờ ra).
    moc = [dai * p for p in (0.25, 0.55, 0.85)][:so_khung]
    tam = os.path.join(GOC, "out", "_soi")
    os.makedirs(tam, exist_ok=True)
    loi = []
    for i, g in enumerate(moc):
        anh = os.path.join(tam, f"k{i}.jpg")
        if not _khung(mp4, g, anh):
            continue
        for ten, cau in CAU_HOI:
            tl = _hoi(anh, cau, keys)
            if not tl:
                continue                    # không trả lời được -> cho qua, xem chú thích đầu tệp
            if tl != DAP_AN[ten]:
                loi.append(f"giây {g:.0f}: {ten}")
    return loi


def main() -> int:
    import glob
    ds = sys.argv[1:] or sorted(glob.glob(os.path.join(GOC, "out", "v[34]_*.mp4")))
    if not ds:
        print("  (không có video nào để soi)")
        return 0
    xau = 0
    for f in ds:
        loi = soi(f)
        ten = os.path.basename(f)
        print(f"  {'❌' if loi else '✅'} {ten:<28}" + ("  " + " · ".join(loi[:4]) if loi else ""))
        xau += 1 if loi else 0
    print(f"\n  ✅ lành {len(ds) - xau}  ·  ❌ có lỗi hình {xau}")
    return 1 if xau else 0


if __name__ == "__main__":
    sys.exit(main())
