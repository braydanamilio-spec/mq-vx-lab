#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CỔNG GIÁ TRỊ TẠO HÌNH — pipeline gán kiểu nào thì engine phải nhận kiểu ấy (1/9/2026)

Bịa một giá trị engine không biết thì **không có lỗi nào được ném ra** — engine lặng lẽ rơi về
mặc định. Hậu quả đúng bằng việc không gán gì cả, mà nhìn code thì tưởng đã gán.

Đã dính hai lần trong một ngày:
  · `kich_kling.py` gán `kieuToc="dai"` cho mọi vai nữ của HOUSE RULES — `"dai"` không có
    trong kiểu `Kieu`, nên tóc nữ chưa bao giờ đúng như tôi tưởng, suốt từ hôm qua.
  · `kich_grock.py` bịa `cuoi`, `cong`, `boc`, `hoi_xoan` để làm mười kênh khác mặt nhau —
    tức bản vá chống "mười kênh giống hệt nhau" lại chính là bản vá không có tác dụng.

TypeScript không cứu được: props đi qua JSON, kiểu bị xoá lúc chạy.

Cổng đọc union type trong `v2/DienVien.tsx` rồi đối chiếu với mọi giá trị pipeline gán.
"""
import io
import os
import re

GOC = os.path.dirname(os.path.abspath(__file__))
DV = os.path.join(GOC, "..", "engine-remotion", "src", "v2", "DienVien.tsx")
PY_KIEM = ["kich_grock.py", "kich_kling.py", "kich_comic.py"]
TRUONG = ["kieuToc", "kieuMui", "kieuMat", "kieuMay", "rau", "mu"]


def main() -> int:
    if not os.path.exists(DV):
        print("⚠️ không thấy DienVien.tsx — bỏ qua")
        return 0
    tsx = io.open(DV, encoding="utf-8").read()
    hop_le = {}
    for t in TRUONG:
        m = re.search(rf"{t}\??:\s*((?:\"[a-z_]*\"\s*\|?\s*)+);", tsx)
        if m:
            hop_le[t] = set(re.findall(r'"([a-z_]*)"', m.group(1)))
    if not hop_le:
        print("⚠️ không đọc được kiểu — bỏ qua")
        return 0

    loi = []
    for f in PY_KIEM:
        d = os.path.join(GOC, f)
        if not os.path.exists(d):
            continue
        s = io.open(d, encoding="utf-8").read()
        for t, ok in hop_le.items():
            # bắt cả `"kieuToc": "x"` lẫn `kieuToc="x"` lẫn danh sách `_TOC = {... ["a","b"]}`
            for m in re.finditer(rf'"{t}"\s*:\s*"([a-z_]*)"', s):
                v = m.group(1)
                if v not in ok:
                    dong = s[:m.start()].count("\n") + 1
                    loi.append(f"{f}:{dong}  {t}=\"{v}\" — engine chỉ nhận: {', '.join(sorted(ok))}")
    # Danh sách hằng (_TOC/_MUI/_MAT/_MAY). Bản đầu của cổng này ngoạm 300 ký tự nên bốn
    # danh sách lẫn vào nhau và nó tố oan mọi giá trị — cổng tố oan thì người ta tắt cổng, nên
    # phải cắt ĐÚNG dấu ngoặc đóng của từng danh sách.
    for f in PY_KIEM:
        d = os.path.join(GOC, f)
        if not os.path.exists(d):
            continue
        s = io.open(d, encoding="utf-8").read()
        for ten, t in (("_TOC", "kieuToc"), ("_MUI", "kieuMui"), ("_MAT", "kieuMat"),
                       ("_MAY", "kieuMay")):
            m = re.search(rf"^{ten}\s*=\s*(\[[^\]]*\]|\{{[\s\S]*?\n\}})", s, re.M)
            if not m or t not in hop_le:
                continue
            for v in re.findall(r'"([a-z_]+)"', m.group(1)):
                if v in ("nam", "nu", "tre"):        # khoá của bảng, không phải giá trị
                    continue
                if v not in hop_le[t]:
                    loi.append(f"{f}  {ten} có \"{v}\" — engine chỉ nhận: "
                               f"{', '.join(sorted(hop_le[t]))}")

    if loi:
        print("❌ " + "\n❌ ".join(sorted(set(loi))))
        print("\n   Giá trị lạ KHÔNG gây lỗi — engine im lặng dùng mặc định. Đó là lý do phải "
              "có cổng này.")
        return 1
    print(f"  ✅ mọi giá trị tạo hình đều nằm trong kiểu của engine "
          f"({' · '.join(f'{k}:{len(v)}' for k, v in hop_le.items())})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
