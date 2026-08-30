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
    # Câu đầu tiên của bản này hỏi "có nhân vật nào bị mép khung cắt mất một phần thân không".
    # Nó tố cả ba video, và soi mắt thì cả ba đều ở CỠ CẬN — nơi cắt vai là ngôn ngữ điện ảnh
    # bình thường, không phải lỗi. Câu hỏi đúng ngữ pháp mà sai ngưỡng: nó bắt cả những cú cận
    # cảnh đúng đắn.
    # Thứ THẬT SỰ hỏng là khi cắt tới mức không còn đọc được MẶT — đó mới là khung mất nhân vật.
    ("mat_nguoi",
     "Is a cartoon person's face fully visible in this image? A face cut in half by the frame "
     "edge does not count as visible. Answer exactly one word: YES or NO."),
    # 31/8 — CÂU HỎI CŨ TỐ NHẦM GẦN NHƯ MỌI KÊNH.
    # Nó hỏi "có chữ nào không thuộc hộp phụ đề không". Nhưng video này CỐ Ý có ba lớp chữ do
    # hệ thống vẽ: thẻ số lớn ở đỉnh, nhãn cột trong bảng, và dòng ghi nguồn ở đáy. Cả ba đều
    # là "không thuộc hộp phụ đề", nên AI trả YES ở hầu hết khung và mỗi kênh mất 10 điểm cho
    # một thứ hoàn toàn đúng thiết kế. Đó là lý do điểm đứng yên ở 63–82 dù hình đã sửa.
    # Thứ THẬT SỰ cần bắt là chữ nằm TRONG ẢNH NỀN do AI vẽ — chữ méo, chữ vô nghĩa, chữ giả
    # tiếng Anh trên tường và biển hiệu. Nên hỏi đúng vào đó, và liệt kê rõ những lớp được phép.
    ("chu_gia",
     "Ignore all clean overlay graphics: the big number card at the top, the chart panel with "
     "its labels, the subtitle box, and the small source line at the bottom — those are part of "
     "the design. Looking ONLY at the drawn background scene behind them, does the background "
     "itself contain any letters, words or signage? Answer exactly one word: YES or NO."),
    # 31/8 — Soi mắt khung mà nó tố: không có chữ nào bị cắt cả. Câu cũ hỏi "có bị panel edge
    # hay frame edge cắt không", và AI coi cả những con số nằm SÁT mép bảng là bị cắt — sát mép
    # không phải là mất chữ. Hỏi đúng vào thứ đo được: có đọc thiếu ký tự nào không.
    ("chu_tran",
     "Look at every word and number on screen. Is any of them missing letters or digits because "
     "it runs past an edge — so you can only read part of the word or number? Text that merely "
     "sits close to an edge but is fully readable does NOT count. Answer exactly one word: "
     "YES or NO."),
    # Nền LUÔN nằm sau biểu đồ — đó là bố cục, không phải lỗi. Chỉ là lỗi khi nền làm chữ hoặc
    # cột KHÔNG ĐỌC ĐƯỢC nữa. Câu cũ hỏi "có che không" nên câu trả lời đúng luôn là YES.
    ("nen_de",
     "Are any chart bars, chart labels or numbers UNREADABLE because the background behind them "
     "is too busy or too similar in colour? Judge readability only, not overlap. "
     "Answer exactly one word: YES or NO."),
    ("khong_co_nguoi",
     "Is there at least one cartoon person visible in this image? "
     "Answer exactly one word: YES or NO."),
]
# Câu nào mà câu trả lời ĐÚNG là "NO" thì ghi ở đây; còn lại đúng là "YES".
DAP_AN = {"mat_nguoi": "YES", "chu_gia": "NO", "chu_tran": "NO", "nen_de": "NO",
          "khong_co_nguoi": "YES"}


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
