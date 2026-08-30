#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHẤM BỘ PHÂN TÍCH — cổng chất lượng cho 60 kênh dạng người-dẫn-và-biểu-đồ. (30/8/2026)

VÌ SAO CÓ TỆP NÀY
-----------------
Anh: *"xây pipeline rule chuẩn để nếu ok thì sau áp dụng cho các channel sau, theo mạch, đỡ sửa
đi sửa lại"*. Đúng chỗ đau: suốt hôm nay mỗi lỗi đều được tìm ra bằng cách **anh xem video rồi
chỉ ra**, và mỗi lần sửa xong lại lộ một lỗi khác ở kênh kế tiếp.

Mắt người không chạy được sáu mươi kênh mỗi đêm. Nên mọi thứ anh đã chỉ phải thành **một phép đo
chạy được bằng máy**, và phép đo ấy phải chặn TRƯỚC khi video ra kho.

MỖI TRỤC DƯỚI ĐÂY LÀ MỘT LỖI CÓ THẬT, ĐÃ TRẢ GIÁ
------------------------------------------------
    nhịp cảnh dồn ......... 2,8s · 0,5s · 0,3s rồi một cảnh 19,3s (luật 7bx)
    biểu đồ nói dối ....... cột "269.7K" vẽ thấp hơn cột "3,580"
    biểu đồ không có gì so  bốn cột chênh nhau 1,1 lần
    không có nền nào ...... `nenTheoCanh` rỗng hết, video chỉ có màu trơn
    mã nội bộ lọt ra ...... "Source: usda", lời dẫn đọc một câu tiếng Việt
    nhãn cắt cụt .......... "Häagen-Da…" — cắt đúng phần phân biệt các mục
    số dài chưa tách ...... một mốc 1,5 giây cho "14747", miệng mấp máy sai
    nhân vật lạc nghề ..... kênh nhãn thực phẩm mà người dẫn đeo ống nghe

NGUYÊN TẮC CỦA CÂY THƯỚC NÀY
----------------------------
Chỉ đo thứ **đo được chắc chắn**, và mỗi trục nêu rõ *tại sao* nó tồn tại. Một cây thước không
nói được vì sao nó đo thì lần sau người đọc sẽ nới ngưỡng cho qua — đó là cách mọi cổng chất
lượng chết.
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.abspath(__file__))


def _doc(f):
    try:
        return json.load(io.open(f, encoding="utf-8"))
    except Exception:
        return None


def cham_mot(d: dict, ten: str) -> tuple[int, list]:
    """Chấm một tập. Trả (điểm 0-100, danh sách lỗi)."""
    diem, loi = 100, []
    canh = d.get("canh") or []
    tu = d.get("tu") or []

    # ── 20đ · NHỊP CẢNH (luật 7bx) ────────────────────────────────────────────────────────
    # Cảnh dài nhất không được gấp quá ~3,5 lần cảnh ngắn nhất. Vượt số ấy nghĩa là mốc thời
    # gian tính sai ở đâu đó — chưa lần nào là do kịch bản.
    if canh:
        t = [max(0.01, c.get("e", 0) - c.get("s", 0)) for c in canh]
        ty = max(t) / max(0.01, min(t))
        # Ngưỡng nới từ 3,5 lên 5. Đo lại trên mười ba tập: tỉ lệ 4 xuất hiện ở những tập có
        # một câu mở dài và một câu chốt ngắn — đó là nhịp kể bình thường, không phải lỗi. Chỉ
        # từ 5 lần trở lên mới là dấu hiệu mốc thời gian tính sai.
        if ty > 5.0:
            diem -= 20
            loi.append(f"nhịp cảnh dồn: dài nhất gấp {ty:.0f} lần ngắn nhất "
                       f"({min(t):.1f}s → {max(t):.1f}s) — mốc thời gian tính sai")

    # ── 25đ · BIỂU ĐỒ CÓ NÓI ĐÚNG CON SỐ NÓ IN RA KHÔNG ───────────────────────────────────
    # Trục nặng điểm nhất, vì đây là trục duy nhất mà sai thì kênh MẤT UY TÍN chứ không chỉ
    # xấu: cột "269.7K" từng được vẽ thấp hơn cột "3,580".
    cot = next((c.get("cot") for c in canh if c.get("cot")), None)
    if cot:
        # Bản đầu của trục này đo "cột sau phải thấp hơn cột trước" và tố ONE EXPERIMENT ba lần.
        # Soi ra thì cột của kênh ấy vốn KHÔNG sắp xếp giảm dần (37, 33, 13, 14, 26, 21) — thứ
        # tự là do nguồn, không phải lỗi. **Thước sai, không phải video sai.**
        # Một cây thước kêu oan thì lần sau người đọc bỏ qua cả những lần nó kêu đúng, nên phép
        # đo dựng trên một giả định chưa kiểm còn tệ hơn không có phép đo nào.
        # Thứ đo được CHẮC CHẮN là quan hệ giữa CHỮ HIỆN và GIÁ TRỊ VẼ của cùng một cột:
        for c in cot:
            h, g = str(c.get("hien") or ""), float(c.get("gt") or 0)
            # Chỉ chữ HOA mới là bậc. "1.1M km" là triệu; "443 m" là MÉT — đường kính một
            # tiểu hành tinh bên DEEP FIELD, và thước bản đầu tố nó là "mất hậu tố triệu".
            # Chữ thường ở đây gần như luôn là đơn vị đo (m, kg, km), không phải bậc.
            if re.search(r"\d\s*[KMB]\b", h) and g < 1000:
                diem -= 25
                loi.append(f"{h!r} nhưng giá trị vẽ chỉ {g:g} — mất hậu tố nghìn/triệu, "
                           f"cột sẽ vẽ sai bậc")
                break
        # Và giữa hai cột: cột nào CHỮ HIỆN lớn hơn mà GIÁ TRỊ VẼ nhỏ hơn thì chắc chắn sai,
        # bất kể thứ tự sắp xếp.
        def _bac(h):
            m = re.search(r"([\d.]+)\s*([KkMmBb])?", str(h).replace(",", ""))
            if not m:
                return None
            try:
                v = float(m.group(1))
            except ValueError:
                return None
            return v * {"k": 1e3, "m": 1e6, "b": 1e9}.get((m.group(2) or "").lower(), 1)
        for a in cot:
            for b in cot:
                ba, bb = _bac(a.get("hien")), _bac(b.get("hien"))
                if ba is None or bb is None:
                    continue
                if ba > bb * 1.05 and float(a.get("gt") or 0) < float(b.get("gt") or 0):
                    diem -= 25
                    loi.append(f"BIỂU ĐỒ NÓI NGƯỢC: {a.get('hien')} vẽ thấp hơn {b.get('hien')}")
                    break
            else:
                continue
            break

    # ── 15đ · BIỂU ĐỒ CÓ GÌ ĐỂ SO KHÔNG ───────────────────────────────────────────────────
    if cot and len(cot) >= 3:
        g = [float(c.get("gt") or 0) for c in cot[:4]]
        if min(g) > 0 and max(g) / min(g) < 1.6:
            diem -= 15
            loi.append(f"bốn cột chênh nhau {max(g)/min(g):.1f} lần — mắt không thấy chênh lệch, "
                       f"biểu đồ thành hàng rào")
    if cot is not None and len(cot) < 3:
        diem -= 15
        loi.append(f"chỉ {len(cot)} cột — dưới ba thì không có gì để so")

    # ── 15đ · CÓ NỀN KHÔNG ────────────────────────────────────────────────────────────────
    # Từng có tập ra lò với `nenTheoCanh` rỗng hết mà không một dòng cảnh báo nào.
    nen = [x for x in (d.get("nenTheoCanh") or []) if x]
    if not nen and not (d.get("nenAnh") or ""):
        diem -= 15
        loi.append("KHÔNG có ảnh nền nào — video chỉ có màu trơn phía sau")
    elif canh and len(nen) < max(1, len(canh) - 2):
        diem -= 6
        loi.append(f"chỉ {len(nen)}/{len(canh)} cảnh có nền")

    # ── 10đ · MÃ NỘI BỘ LỌT RA MÀN HÌNH HOẶC RA LOA (luật 7t · 7by) ────────────────────────
    ngu = str(d.get("nguon") or "")
    if ngu and ngu.islower() and " " not in ngu:
        diem -= 5
        loi.append(f"nguồn hiện dạng mã nội bộ {ngu!r} — phải là tên cơ quan")
    loi_viet = [c.get("nar", "") for c in canh
                if re.search(r"[ăâđêôơưĂÂĐÊÔƠƯáàảãạấầẩẫậéèẻẽẹíìỉĩịóòỏõọúùủũụ]", c.get("nar", ""))]
    if loi_viet:
        diem -= 10
        loi.append(f"lời dẫn có chữ tiếng Việt: {loi_viet[0][:40]!r}")

    # ── 10đ · SỐ DÀI ĐÃ TÁCH THÀNH TỪNG TỪ CHƯA (luật miệng-lệch-phụ-đề) ──────────────────
    dai = [w for w in tu if float(w.get("d") or 0) > 0.9 and re.fullmatch(r"[\d,.]+[A-Za-z%]*",
                                                                          str(w.get("w") or ""))]
    if dai:
        diem -= 10
        loi.append(f"mốc {dai[0].get('w')!r} dài {float(dai[0]['d']):.1f}s chưa tách — "
                   f"phụ đề đứng im còn miệng mấp máy theo chữ số")

    # ── 5đ · NHÃN CỘT ĐỌC ĐƯỢC ────────────────────────────────────────────────────────────
    if cot:
        # ONE EXPERIMENT lộ ra một dạng hỏng nặng hơn cắt-cụt-cuối: nhãn là MẢNH CÂU bị chặt
        # giữa chừng — "Sleep Quali", "of sleep-di", "the a". Nguồn trả về một đoạn văn chứ
        # không phải tên mục, và không khâu nào bắt được.
        # Ba dấu hiệu, cả ba đo được: quá dài · quá ngắn · bắt đầu bằng một từ nối (một tên mục
        # không bao giờ mở đầu bằng "of", "the", "and").
        _NOI = ("of", "the", "and", "for", "with", "in", "on", "to", "a", "an", "by")
        xau = [c.get("nhan") for c in cot
               if len(str(c.get("nhan") or "")) > 22 or "…" in str(c.get("nhan") or "")
               or len(str(c.get("nhan") or "").strip()) < 4
               # Từ nối phải VIẾT THƯỜNG mới là dấu hiệu câu bị chặt. "A New Life Herbs" mở đầu
               # bằng "A" hoa — đó là tên một công ty, và thước bản đầu tố nó là mảnh câu.
               or (str(c.get("nhan") or "").strip().split()[:1] and
                   str(c.get("nhan")).strip().split()[0] in _NOI)
               or re.search(r"[^\x00-\x7F]", str(c.get("nhan") or ""))]
        if xau:
            diem -= 12
            loi.append(f"nhãn không phải tên mục mà là mảnh câu bị chặt: "
                       f"{', '.join(repr(x) for x in xau[:3])}")

    return max(0, diem), loi


def main() -> int:
    fs = sorted(glob.glob(os.path.join(GOC, "out", "v3_*.json")))
    if not fs:
        print("  (chưa có tập nào trong out/)")
        return 0
    print(f"  {'kênh':<22} {'điểm':>5}  {'cảnh':>5} {'cột':>4} {'nền':>4}")
    print("  " + "─" * 78)
    dat = hong = 0
    for f in fs:
        d = _doc(f)
        if not d:
            continue
        ten = os.path.basename(f)[3:-5].upper()
        diem, loi = cham_mot(d, ten)
        canh = d.get("canh") or []
        cot = next((c.get("cot") for c in canh if c.get("cot")), None) or []
        nen = len([x for x in (d.get("nenTheoCanh") or []) if x])
        bi = "✅" if diem >= 85 else "❌"
        dat, hong = (dat + 1, hong) if diem >= 85 else (dat, hong + 1)
        print(f"  {bi} {ten:<20} {diem:>4}  {len(canh):>5} {len(cot):>4} {nen:>4}")
        for l in loi:
            print(f"       └ {l}")
    print(f"\n  ✅ đạt {dat}  ·  ❌ chưa đạt {hong}   (ngưỡng 85/100)")
    return 1 if hong else 0


if __name__ == "__main__":
    sys.exit(main())
