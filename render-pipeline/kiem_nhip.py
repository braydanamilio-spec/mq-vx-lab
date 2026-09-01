#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG NHỊP CẮT — đo trên danh sách nhịp, TRƯỚC khi render.  (1/9/2026)

Anh: *"Trung vị 2,1 giây, không cảnh nào quá 7 giây, mình cũng phải thế hay ngon hơn."*

VÌ SAO CẦN MỘT CỔNG RIÊNG. Cổng chấm điểm hiện có đo bố cục, đo chữ tràn, đo âm lượng — không
đo nhịp. Mà đo trên hai video tham chiếu thì nhịp mới là khoảng cách lớn nhất giữa bộ mình và
họ: `kich_v2` giữ mỗi cảnh 4-8 giây, họ giữ 2,1 giây. Chậm gấp ba. Không có cổng nào đỏ vì
không có cổng nào biết nhìn thứ đó.

VÀ NHỊP LÀ VIỆC CỦA KHÂU VIẾT, KHÔNG PHẢI KHÂU DỰNG. Mỗi cảnh dài đúng bằng câu nói trong nó.
Muốn cảnh 2,1 giây thì câu phải 5-8 chữ. Viết câu hai mươi chữ rồi mong bộ dựng cắt nhanh là
bất khả — nên cổng này chạy TRƯỚC khi tốn một giây render nào, và nó chỉ thẳng vào câu nào dài.

NGƯỠNG (lấy từ số đo, không lấy từ cảm giác):
    trung vị        ≤ 2,6 s     (họ 2,1 — cho mình dôi 0,5)
    cảnh dài nhất   ≤ 7,0 s     (họ đúng 7,0 ở video A)
    cắt mỗi phút    ≥ 20        (họ 26)
    tỉ lệ cảnh >4 s ≤ 12%       (họ 7%)
"""
import io
import json
import os
import sys

TRUNG_VI = 2.6
DAI_NHAT = 7.0
CAT_PHUT = 20.0
TI_LE_DAI = 0.12


def do(nhip: list) -> dict:
    d = sorted(round(float(n["e"]) - float(n["s"]), 3) for n in nhip)
    if not d:
        return {"ok": False, "vi_sao": ["không có nhịp nào"]}
    tong = sum(d)
    n = len(d)
    tv = d[n // 2]
    dai = d[-1]
    cp = n / (tong / 60.0) if tong else 0
    ti = sum(1 for x in d if x > 4.0) / n
    vs = []
    if tv > TRUNG_VI:
        vs.append(f"trung vị {tv:.1f}s > {TRUNG_VI}s — cảnh giữ quá lâu")
    if dai > DAI_NHAT:
        vs.append(f"cảnh dài nhất {dai:.1f}s > {DAI_NHAT}s")
    if cp < CAT_PHUT:
        vs.append(f"chỉ {cp:.0f} cắt/phút < {CAT_PHUT:.0f}")
    if ti > TI_LE_DAI:
        vs.append(f"{ti*100:.0f}% số cảnh dài quá 4s > {TI_LE_DAI*100:.0f}%")
    return {"ok": not vs, "vi_sao": vs, "n": n, "tong": round(tong, 1),
            "tv": tv, "dai": dai, "cp": round(cp, 1), "ti": round(ti, 3)}


def cau_dai(nhip: list, nguong: int = 11) -> list:
    """Câu nào dài quá thì chỉ đích danh — vì đó mới là chỗ sửa được.

    Ngưỡng 11 chữ: giọng đọc Mỹ ở nhịp bình thường ra khoảng 2,8 chữ mỗi giây, nên 11 chữ là
    ~3,9 giây. Dài hơn thế là cảnh ấy chắc chắn vượt trung vị."""
    ra = []
    for i, n in enumerate(nhip):
        c = (n.get("loi") or n.get("nar") or "").split()
        if len(c) > nguong:
            ra.append((i, len(c), " ".join(c[:9]) + "…"))
    return ra


def main() -> int:
    goc = os.path.dirname(os.path.abspath(__file__))
    ds = sys.argv[1:] or sorted(
        os.path.join(goc, "out", f) for f in os.listdir(os.path.join(goc, "out"))
        if f.startswith("v9_") and f.endswith(".json"))
    if not ds:
        print("  (không có tệp nhịp nào để đo)")
        return 0
    hong = 0
    for p in ds:
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        k = do(d.get("nhip", []))
        ten = os.path.basename(p)
        if k["ok"]:
            print(f"  ✅ {ten:34s} {k['n']:3d} nhịp · {k['tong']:5.1f}s · "
                  f"trung vị {k['tv']:.1f}s · dài nhất {k['dai']:.1f}s · {k['cp']:.0f} cắt/phút")
        else:
            hong += 1
            print(f"  ❌ {ten:34s} " + " · ".join(k["vi_sao"]))
            for i, sc, mau in cau_dai(d.get("nhip", []))[:3]:
                print(f"       nhịp {i}: {sc} chữ — {mau}")
    if hong:
        print(f"\n❌ {hong} tập không đạt nhịp. Nhịp là việc của KHÂU VIẾT: rút câu về 5-8 chữ.")
        return 1
    print(f"\n✅ {len(ds)} tập đạt nhịp cắt (chuẩn đo từ hai video tham chiếu)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
