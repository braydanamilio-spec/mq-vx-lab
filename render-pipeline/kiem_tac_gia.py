#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG MỘT TÁC GIẢ — kho hình phải toàn của CÙNG một hoạ sĩ.

── VÌ SAO  (5/9/2026) ────────────────────────────────────────────────────────────────────
Anh nói từ sớm: *"nó bị nhảy sang của người khác rồi kia nhớ là nhất quán chuẩn nha"*.
Em vá bằng cách bấm cẩn thận hơn — tức bằng sự chú ý, không bằng cơ chế. Đo hôm nay:

    kho 118 hình  ->  18 của Zdenek Sasek  ·  100 của hoạ sĩ KHÁC

85% kho sai tác giả. Và không có gì báo, vì mọi hình đều là "hình que đen trắng" nên
nhìn lướt thì giống nhau. Đây là gốc thật của lời chê *"xấu, không nhất quán"* — trộn
nét của mười hoạ sĩ thì không bản vá bố cục nào cứu được.

Lý do panel Canva trộn: bấm một tile thì Canva chèn hình VÀ nhét dải "Magic
recommendations" vào giữa lưới; ngay cả trang tác giả cũng xen hình người khác. Nên
"đang ở panel tác giả" KHÔNG phải bằng chứng về tác giả.

── BẰNG CHỨNG CỨNG ────────────────────────────────────────────────────────────────────
`danh_muc_canva.json` là 4.317 id + tiêu đề quét từ trang tác giả công khai
`canva.com/p/id/BAD5p5eXihY/`. Một hình là của ông ấy KHI VÀ CHỈ KHI id của nó nằm
trong danh mục đó. Không đoán theo nét vẽ, không tin panel.

Ở lúc thu hoạch thì so bằng ID (chắc chắn tuyệt đối). Với kho đã có mà chỉ còn tiêu đề
thì so bằng tập từ — lỏng hơn, nên ngưỡng đặt cao và mọi ca dưới ngưỡng đều IN RA để
đọc tay, không tự xoá (§13.8: cổng bắt oan tệ hơn cổng không bắt).

    python3 kiem_tac_gia.py                 # soi kho_canva
    python3 kiem_tac_gia.py --kho <thư mục>
"""
from __future__ import annotations
import argparse, json, os, re, sys

GOC = os.path.dirname(os.path.abspath(__file__))
DANH_MUC = os.path.join(GOC, "danh_muc_canva.json")
NGUONG = 0.75


def _tu(s: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", (s or "").lower()))


def doc_danh_muc() -> list[set[str]]:
    if not os.path.exists(DANH_MUC):
        sys.exit(f"❌ thiếu {DANH_MUC} — chạy lượt quét trang tác giả trước.")
    return [_tu(x.get("ten", "")) for x in json.load(open(DANH_MUC, encoding="utf-8"))]


def soi(thu_muc: str) -> int:
    so = os.path.join(thu_muc, "_kho.json")
    if not os.path.exists(so):
        sys.exit(f"❌ thiếu {so}")
    kho = json.load(open(so, encoding="utf-8"))
    dm = doc_danh_muc()
    dung, ngo = [], []
    for k in kho:
        # id là bằng chứng cứng; có id thì dùng id, không có thì mới so tiêu đề
        ma = k.get("id") or k.get("canva_id")
        if ma:
            (dung if any(ma == x.get("id") for x in
                         json.load(open(DANH_MUC, encoding="utf-8"))) else ngo).append((1.0, ma))
            continue
        t = _tu(k.get("mo_ta") or k.get("ten") or "")
        if not t:
            ngo.append((0.0, k.get("tep", "?")))
            continue
        diem = max((len(t & o) / max(len(t | o), 1) for o in dm), default=0.0)
        (dung if diem >= NGUONG else ngo).append((round(diem, 2),
                                                  (k.get("mo_ta") or k.get("tep") or "?")))
    # Mọi con số kèm MẪU SỐ (§15.2)
    print(f"📊 {thu_muc}: {len(kho)} hình · {len(dung)} đúng tác giả · {len(ngo)} NGỜ")
    if ngo:
        print(f"   {len(ngo)} hình dưới ngưỡng {NGUONG} — ĐỌC TAY, cổng không tự xoá:")
        for d, t in sorted(ngo)[:15]:
            print(f"     {d:4}  {str(t)[:70]}")
        if len(ngo) > 15:
            print(f"     … còn {len(ngo)-15} hình nữa")
    return len(ngo)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--kho", default=os.path.join(GOC, "kho_canva"))
    p.add_argument("--chan", action="store_true",
                   help="thoát khác 0 khi còn hình ngờ (dùng làm cổng trong workflow)")
    a = p.parse_args()
    n = soi(a.kho)
    if a.chan and n:
        sys.exit(f"❌ còn {n} hình chưa chứng minh được tác giả")


if __name__ == "__main__":
    main()
