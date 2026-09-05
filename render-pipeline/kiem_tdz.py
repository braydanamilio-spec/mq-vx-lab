#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG VÙNG CHẾT TẠM THỜI — `const` bị dùng TRƯỚC khi khai báo.  (3/9/2026)

── VÌ SAO CẦN CỔNG NÀY ─────────────────────────────────────────────────────────────────────
Thêm hai bố cục cho `Chart`, chèn khối mới vào GIỮA hai khai báo, và khối ấy dùng `bo` — một
`const` khai báo ở phía DƯỚI. JavaScript có *vùng chết tạm thời*: đọc một `const` trước dòng
khai báo ném `ReferenceError` **lúc chạy**, không phải lúc dịch.

`npx esbuild` xanh. `npx tsc --noEmit` cũng sẽ xanh. Chỉ có lúc RENDER một tập mà biểu đồ rơi
đúng vào kiểu 1 hoặc 2 thì nó mới nổ — tức lỗi ẩn sau một nhánh dữ liệu, đúng thứ §5 đã ghi:
*"cổng render một khung không chứng minh được gì ngoài khung ấy"*.

Đây là biến thể của §12.2 (*`tsc --noEmit` xanh KHÔNG có nghĩa là build được*), lần này ngược
lại: **build được không có nghĩa là chạy được**.

── PHẠM VI ─────────────────────────────────────────────────────────────────────────────────
Chỉ soi thân các component `export const X: React.FC` trong `engine-remotion/src/gt` và `v2`,
vì đó là nơi có những hàm dài hàng trăm dòng với hàng chục `const` — chỗ duy nhất lỗi này thực
sự xảy ra được. Hàm ngắn thì mắt bắt ngay.

Bỏ qua chuỗi và chú thích: `bo` trong một câu chú thích tiếng Việt không phải một lượt dùng.
"""
import io
import os
import re
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
NGUON = [os.path.join(os.path.dirname(GOC), "engine-remotion", "src", "gt"),
         os.path.join(os.path.dirname(GOC), "engine-remotion", "src", "v2")]

# Tên quá ngắn hay quá phổ biến thì phép quét theo từ sẽ nhận vơ; bỏ chúng đi còn hơn tố oan.
BO_QUA_TEN = {"i", "j", "k", "x", "y", "w", "h", "n", "p", "q", "s", "t", "d", "e", "f", "g"}


def _go_chu_thich(t: str) -> str:
    """Thay chú thích và chuỗi bằng khoảng trắng, GIỮ NGUYÊN độ dài để chỉ số không lệch."""
    ra = list(t)
    i, n = 0, len(t)
    while i < n:
        hai = t[i:i + 2]
        if hai == "/*":
            j = t.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for z in range(i, j):
                if ra[z] != "\n":
                    ra[z] = " "
            i = j
            continue
        if hai == "//":
            j = t.find("\n", i)
            j = n if j < 0 else j
            for z in range(i, j):
                ra[z] = " "
            i = j
            continue
        if t[i] in "\"'`":
            dau = t[i]
            j = i + 1
            while j < n and t[j] != dau:
                j += 2 if t[j] == "\\" else 1
            j = min(n, j + 1)
            for z in range(i, j):
                if ra[z] != "\n":
                    ra[z] = " "
            i = j
            continue
        i += 1
    return "".join(ra)


def soi_mot(duong: str) -> list:
    goc = io.open(duong, encoding="utf-8").read()
    t = _go_chu_thich(goc)
    loi = []
    for m in re.finditer(r"^export const (\w+): React\.FC", t, re.M):
        dau = m.start()
        ket = t.find("\n};", dau)
        ket = len(t) if ket < 0 else ket
        than = t[dau:ket]
        for kb in re.finditer(r"^  const (\w+)\s*=", than, re.M):
            ten = kb.group(1)
            if ten in BO_QUA_TEN:
                continue
            # ── HAI LUẬT CHỐNG BẮT OAN  (đọc tay hai ca đầu tiên cổng bắt được) ────────────
            # Lần chạy đầu cổng tố hai chỗ, và ĐỌC TAY thì cả hai đều là mã đúng:
            #   · `Khuon.tsx <Chart>` dùng `b` trong `cot.reduce((a, b) => …)` — `b` ở đó là
            #     THAM SỐ LAMBDA che tên, không phải `const b` của thân component.
            #   · `BrandGT.tsx <BrandGT>` khai `cs` HAI LẦN, trong hai hàm con khác nhau; chỗ
            #     dùng ở giữa trỏ tới khai báo thứ nhất, không phải thứ hai.
            # Cổng bắt oan còn tệ hơn cổng không bắt (§13.8) — nó dạy người ta bỏ qua báo động.
            # Nên: tên khai báo nhiều lần thì KHÔNG phán (mơ hồ, cần phân tích phạm vi thật), và
            # bỏ mọi danh sách tham số `( … ) =>` ra khỏi phần văn bản đem soi.
            if len(re.findall(r"^\s*const " + re.escape(ten) + r"\s*=", than, re.M)) > 1:
                continue
            truoc = than[:kb.start()]
            than_dau = truoc.find("=> {")
            if than_dau >= 0:
                truoc = " " * (than_dau + 4) + truoc[than_dau + 4:]
            # Che tên bằng THAM SỐ LAMBDA: `cot.reduce((a, b) => Math.abs(b.v) …)` — chữ `b`
            # trong THÂN lambda cũng trỏ tới tham số, không chỉ chữ `b` trong danh sách tham số.
            # Blank mỗi danh sách tham số là chưa đủ; muốn phán đúng phải phân tích phạm vi thật.
            # Nên áp cùng nguyên tắc với trường hợp khai báo hai lần: MƠ HỒ THÌ KHÔNG PHÁN.
            # Bỏ sót một ca còn hơn tố oan một ca — cổng này chỉ có giá trị khi mọi dòng đỏ của
            # nó đều là lỗi thật.
            if re.search(r"\(\s*(?:\w+\s*,\s*)*" + re.escape(ten) + r"\s*(?:,[^)]*)?\)\s*=>", truoc):
                continue
            # ── `.ten` LÀ THUỘC TÍNH, KHÔNG PHẢI BIẾN  (5/9/2026) ──────────────────
            # Cổng tố oan `const ruot = h.ruot...` trong `HinhNhap.tsx`: `h.ruot` là truy
            # cập thuộc tính của một object khác, hoàn toàn hợp lệ ở trước dòng khai báo.
            # `\b` không phân biệt được hai thứ ấy vì dấu chấm cũng là ranh giới từ.
            # Cùng lý do phải chữa chứ không bỏ qua: một dòng đỏ giả không phiền, nó CHE —
            # lỗi thật nằm cạnh nó sẽ bị đọc lướt qua (§13.8, đã trả giá 3 lần).
            # Cũng loại luôn `{ ten: ... }` (khoá của object) và `ten:` trong kiểu.
            _sach = re.sub(r"\.\s*" + re.escape(ten) + r"\b", "", truoc)
            _sach = re.sub(r"\b" + re.escape(ten) + r"\s*:", "", _sach)
            if re.search(r"\b" + re.escape(ten) + r"\b", _sach):
                dong = goc[:dau + kb.start()].count("\n") + 1
                loi.append((os.path.basename(duong), m.group(1), ten, dong))
    return loi


def main() -> int:
    loi = []
    for thu in NGUON:
        if not os.path.isdir(thu):
            continue
        for t in sorted(os.listdir(thu)):
            if t.endswith(".tsx"):
                loi += soi_mot(os.path.join(thu, t))
    if loi:
        print(f"❌ {len(loi)} chỗ dùng `const` TRƯỚC khi khai báo (vùng chết tạm thời):")
        for tep, comp, ten, dong in loi[:12]:
            print(f"   {tep}:{dong}  <{comp}>  dùng `{ten}` trước dòng khai báo")
        print("\n   JavaScript ném ReferenceError LÚC CHẠY, còn esbuild và tsc đều xanh.")
        print("   Nâng dòng khai báo lên trước chỗ dùng đầu tiên.")
        return 1
    print("✅ không có `const` nào bị dùng trước khai báo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
