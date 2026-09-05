#!/usr/bin/env python3
"""Nạp kho hình Canva vào engine: chép ảnh sang `public/`, sinh chỉ mục cho Python.

Kho gom từ Canva Elements (tác giả `zdeneksasek`, Canva Pro của anh). Toàn bộ là **nét mực
thuần** — đo được: 29/29 ảnh có tỉ lệ điểm-có-màu ≤ 0,12, độ sáng TB 0,03.

Vì sao điều đó quan trọng hơn nó nghe: ảnh nét mực **không mang màu riêng**, nên 18 kênh
dùng chung một kho mà mỗi kênh vẫn ra một tông — màu do bảng màu kênh cấp lúc dựng, không
do ảnh mang theo. Không kênh nào lệch tông được, vì không có tông nào để lệch.

Đó là lý do chọn họ nét mực làm nền tảng thay vì họ tô màu (`ghrzuzudu`): **màu là thứ mình
CẤP, không phải thứ mình phải HOÀ.**

── CỔNG MỘT HỌ NÉT ─────────────────────────────────────────────────────────────────────
    tỉ lệ điểm có màu ≤ 0,12  ->  họ "nét mực"
    tỉ lệ điểm có màu >  0,12  ->  họ "màu phẳng"
Một kênh chỉ được dùng MỘT họ. Trộn nét mực với mảng màu trong một khung là đúng lỗi đã
trả giá với unDraw (§12.10 — lệch phong cách là đòn bẩy lớn hơn hẳn màu sắc).
"""
import json, os, shutil, sys

GOC = os.path.join(os.path.dirname(__file__), "kho_canva")
PUB = os.path.join(os.path.dirname(__file__), "..", "engine-remotion", "public", "canva")
RA = os.path.join(os.path.dirname(__file__), "..", "engine-remotion", "src", "gt", "KhoCanva.ts")
NGUONG_MAU = 0.12


def main() -> int:
    kho = json.load(open(os.path.join(GOC, "_kho.json"), encoding="utf-8"))
    os.makedirs(PUB, exist_ok=True)
    ra, loai = [], []
    for h in kho:
        # Cổng một-họ-nét: ảnh có màu bị loại khỏi kho nét mực, không im lặng trộn vào.
        if h.get("ti_le_co_mau", 0) > NGUONG_MAU:
            loai.append(h["tep"]); continue
        if not h.get("tu"):
            loai.append(h["tep"]); continue      # không từ khoá thì không khớp được lời
        goc = os.path.join(GOC, h["tep"])
        shutil.copy(goc, os.path.join(PUB, h["tep"]))
        # Đọc cỡ từ CHÍNH TỆP, không tin trường trong json: lượt đo bảng màu đã ghi đè
        # `_kho.json` và làm rơi mất `rong`/`cao`. Tệp thì không nói dối (§13.7).
        from PIL import Image
        with Image.open(goc) as im:
            w, hh = im.size
        ra.append({"tep": h["tep"], "tu": h["tu"], "mo_ta": h["mo_ta"], "rong": w, "cao": hh})
    if len(ra) < 10:
        raise RuntimeError(f"chỉ {len(ra)} ảnh qua cổng — KHÔNG ghi đè kho cũ")
    with open(RA, "w", encoding="utf-8") as f:
        f.write("/* SINH TỰ ĐỘNG bởi `render-pipeline/tai_canva.py` — ĐỪNG SỬA TAY.\n"
                "   Nguồn: Canva Elements (tác giả zdeneksasek), tài khoản Canva Pro của anh.\n"
                "   Toàn bộ là NÉT MỰC thuần — engine tô bằng màu kênh, xem docstring. */\n")
        f.write("export type HinhCanva = { tep: string; tu: string[]; rong: number; cao: number };\n")
        f.write("export const KHO_CANVA: Record<string, HinhCanva> = ")
        f.write(json.dumps({h["tep"]: {"tep": h["tep"], "tu": h["tu"],
                                       "rong": h["rong"], "cao": h["cao"]} for h in ra},
                           ensure_ascii=False))
        f.write(";\n")
    print(f"   ✅ {len(ra)} ảnh vào kho · {len(loai)} loại · "
          f"{sum(os.path.getsize(os.path.join(PUB,h['tep'])) for h in ra)/1e6:.2f} MB")
    print(f"   từ khoá khác nhau: {len({w for h in ra for w in h['tu']})}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
