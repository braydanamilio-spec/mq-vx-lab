#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐO SỨC KHOẺ HỒ KHOÁ — bao nhiêu khoá THẬT SỰ gọi được. (30/8/2026)

VÌ SAO CẦN
----------
Anh: *"nhớ fix và sửa hệ thống lại cho a để ko lỗi liên quan tới việc dùng key gemini hay cf"*.

Hôm nay hệ chạy suốt ngày với **1 trên 68 khoá Gemini** mà không ai biết. Log chỉ nói `429`, và
`429` đọc ra như "hết hạn mức, mai chạy lại" — trong khi sự thật là hệ gọi đúng một model, model
ấy cạn, còn 39 model khác trên cùng khoá vẫn còn nguyên.

**Không ai biết vì không ai ĐẾM.** Cả dây chuyền có cơ chế xoay khoá, có cơ chế đổi model, có
cả cổng chặn bản hỏng — mà không có một phép đo nào trả lời câu hỏi đơn giản nhất: *lúc này ta
gọi được bao nhiêu khoá?*

Một con số không được đo thì không tồn tại. Hệ vẫn chạy, vẫn ra video, chỉ là chạy ở một phần
sáu mươi sáu năng lực — và mọi dấu hiệu đều đọc ra như bình thường.

CÁCH ĐO
-------
Lấy MẪU vài khoá mỗi nhà rồi suy ra tỉ lệ, không thử cả hồ: thử 248 khoá tốn 248 lượt gọi mỗi
lần chạy, mà mục đích ở đây là phát hiện SỤT, không phải điểm danh từng cái.
Ngưỡng báo động đặt thấp có chủ ý — dưới 40% mới kêu. Hồ khoá miễn phí luôn có một phần cạn theo
giờ; kêu ở mức 90% thì ngày nào cũng kêu, và một cổng kêu mỗi ngày là một cổng không ai đọc.
"""
from __future__ import annotations

import concurrent.futures as _cf
import io
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
MAU = 8              # số khoá thử mỗi nhà
NGUONG = 0.40        # dưới ngưỡng này thì coi là hồ khoá có vấn đề


def _ho() -> dict[str, list]:
    ds = []
    try:
        import the_he_2 as T2
        ds = [k.get("key") for k in (T2.keys_cuc_bo() or []) if k.get("key")]
    except Exception:
        pass
    ra: dict[str, list] = {"gemini": [], "groq": [], "cf": []}
    for k in ds:
        if str(k).startswith(("AQ.", "AIza")):
            ra["gemini"].append(k)
        elif str(k).startswith("gsk_"):
            ra["groq"].append(k)
        elif str(k).startswith("cf:"):
            ra["cf"].append(k)
    return ra


# Lý do hỏng của khoá đầu tiên mỗi nhà — để "0/8" không còn là một con số câm.
_VI_SAO: dict = {}


def _song(k) -> bool:
    """Thử MỘT khoá. Ghi lại lý do hỏng — `0/8` mà không có lý do thì không hành động được.

    ── VÌ SAO PHẢI GHI LÝ DO  (2/9/2026) ───────────────────────────────────────────────────
    Cổng này báo `cf 0/8 = 0%` kèm gợi ý *"kiểm model có còn mở không…"* — tức nó biết mình
    không biết, mà vẫn vứt bằng chứng đi bằng `except Exception: return False`.

    Và con số ấy nói SAI về mức độ: `_genai` phân nhánh `cf:` sang `_CfShim`, là mô hình **chữ**
    của Cloudflare. FLUX (vẽ ảnh) đi đường khác hẳn — `_cf_flux_image` — và log CI cùng ngày
    chứng minh nó CHẠY: `⛅ CF •••5032 hoạt động`, vẽ được ảnh thật, thậm chí trả cả lỗi NSFW.
    Nên "cf 0%" đọc ra là "khoá CF chết", trong khi sự thật là "mô hình CHỮ của CF không gọi
    được, mô hình ẢNH vẫn tốt".

    Một dòng đỏ vĩnh viễn và nói sai chuyện làm chìm lỗi thật nằm cạnh nó — đúng luật 13.2.
    """
    try:
        import content_brain as CB
        CB._genai(k).GenerativeModel(CB.MODEL).generate_content("Reply: OK")
        return True
    except Exception as e:
        nha = ("cf" if str(k).startswith("cf:")
               else "groq" if str(k).startswith("gsk_") else "gemini")
        _VI_SAO.setdefault(nha, f"{type(e).__name__}: {str(e)[:150]}")
        return False


def do(mau: int = MAU) -> dict:
    ho = _ho()
    kq = {}
    for ten, ds in ho.items():
        if not ds:
            kq[ten] = (0, 0, 0)
            continue
        # Lấy mẫu RẢI ĐỀU khắp hồ, không lấy mấy cái đầu: khoá đầu hồ hay là khoá cũ nhất, và
        # chúng cạn trước — lấy đầu hồ sẽ cho một bức tranh bi quan hơn sự thật.
        buoc = max(1, len(ds) // mau)
        lay = ds[::buoc][:mau]
        with _cf.ThreadPoolExecutor(min(6, len(lay))) as ex:
            s = sum(ex.map(_song, lay))
        kq[ten] = (s, len(lay), len(ds))
    return kq


def main() -> int:
    kq = do()
    print(f"  {'nhà':<9} {'mẫu sống':>10}  {'tỉ lệ':>6}  {'tổng khoá':>10}")
    xau = []
    for ten, (s, n, tong) in kq.items():
        ty = (s / n) if n else 0
        bi = "✅" if ty >= NGUONG else "❌"
        print(f"  {bi} {ten:<7} {s:>5}/{n:<4} {100*ty:>5.0f}%  {tong:>10}")
        if n and ty < NGUONG:
            xau.append(f"{ten}: chỉ {100*ty:.0f}% khoá gọi được trong mẫu {n} cái")
    if xau:
        print()
        for x in xau:
            print(f"  ❌ {x}")
            _n = x.split(":")[0]
            if _VI_SAO.get(_n):
                print(f"       lý do (khoá đầu hỏng): {_VI_SAO[_n]}")
        print("     → kiểm: model đang gọi có còn mở với khoá ấy không · hồ khoá có bị lọc "
              "nhầm định dạng không · nhà cung cấp có đổi tên model không")
        return 1
    print("\n  ✅ hồ khoá lành")
    return 0


if __name__ == "__main__":
    sys.exit(main())
