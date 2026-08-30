#!/usr/bin/env python3
"""Cổng cử chỉ — bảng tư thế phải KHÁC BIỆT nhau và nằm trong giới hạn khớp người.

Sinh ra sau lượt hỏng 30/8. Khi tôi chia đôi mọi góc khuỷu để dập lỗi "tay khèo", cả mười cử
chỉ dẹt thành một tư thế: khoanh tay không khoanh, chống hông không chống, chỉ tay không chỉ.
Nhân vật vẫn "diễn", chỉ là diễn đúng một điệu suốt mười lăm giây.

Không cổng nào bắt được. Cổng nội dung chấm 100/100 vì nó đọc chữ và đo nhịp; hình thế nào nó
không biết. Chỉ có mắt nhìn bảng tư thế nền trơn mới thấy. Nên cổng này đo đúng thứ mắt đo:
khoảng cách giữa các tư thế.

Cách đo: dựng lại đúng phép của engine (P: SVG, y hướng XUỐNG), lấy toạ độ HAI BÀN TAY của mỗi
cử chỉ, rồi so từng cặp. Hai cử chỉ mà bàn tay chỉ lệch nhau vài chục đơn vị thì trên màn hình
là một. Ngưỡng 55 = khoảng mắt bắt đầu đọc ra "đã đổi tư thế" ở cỡ dọc 1080.

Kèm giới hạn giải phẫu: khuỷu người gập MỘT chiều, tối đa ~145°. Vượt ngưỡng là cẳng tay ưỡn
ngược — đúng cái anh gọi là "tay như què".
"""
import math, re, sys, io, itertools, pathlib

TSX = pathlib.Path(__file__).resolve().parents[0].parent / "engine-remotion/src/v4/DienVienHai.tsx"
DTAY, DCANG = 86.0, 80.0          # dài cánh tay / cẳng tay, đúng hằng trong engine
XA_TOI_THIEU = 55.0               # hai tư thế gần hơn mức này thì mắt đọc ra là một
KHUYU_TOI_DA = 145.0              # khớp khuỷu người gập tối đa

def doc_bang():
    s = TSX.read_text(encoding="utf-8")
    kh = s.index("const CU_CHI_HAI"); s = s[kh:s.index("};", kh)]
    ra = {}
    for m in re.finditer(r"^\s*(\w+):\s*\{\s*vaiT:\s*(-?[\d.]+),\s*khuyuT:\s*(-?[\d.]+),"
                         r"\s*vaiP:\s*(-?[\d.]+),\s*khuyuP:\s*(-?[\d.]+)", s, re.M):
        ra[m.group(1)] = tuple(float(m.group(i)) for i in range(2, 6))
    return ra

def ban_tay(g):
    """Toạ độ hai bàn tay, gốc ở giữa hai vai. Đúng phép P() của engine."""
    vT, kT, vP, kP = g
    out = []
    for x0, vai, khuyu in ((-26.0, vT, kT), (26.0, vP, kP)):
        ex = x0 + math.cos(math.radians(vai)) * DTAY
        ey = math.sin(math.radians(vai)) * DTAY
        out += [ex + math.cos(math.radians(vai + khuyu)) * DCANG,
                ey + math.sin(math.radians(vai + khuyu)) * DCANG]
    return out

def main():
    bang = doc_bang()
    if len(bang) < 8:
        print(f"  ❌ chỉ đọc được {len(bang)} cử chỉ — bảng đổi dạng, cổng mù"); return 1
    loi = []
    for ten, g in bang.items():
        for nhan, v in (("trái", g[1]), ("phải", g[3])):
            if abs(v) > KHUYU_TOI_DA:
                loi.append(f"{ten}: khuỷu {nhan} gập {abs(v):.0f}° > {KHUYU_TOI_DA:.0f}° — cẳng tay ưỡn ngược")
    for a, b in itertools.combinations(bang, 2):
        pa, pb = ban_tay(bang[a]), ban_tay(bang[b])
        d = math.dist(pa[:2], pb[:2]) + math.dist(pa[2:], pb[2:])
        if d < XA_TOI_THIEU:
            loi.append(f"{a} ≈ {b}: hai bàn tay chỉ lệch {d:.0f} đơn vị — trên màn hình là MỘT tư thế")
    print(f"\n  Cổng cử chỉ — {len(bang)} tư thế, {len(list(itertools.combinations(bang, 2)))} cặp\n")
    for l in loi: print(f"  ❌ {l}")
    if not loi:
        xa = min(math.dist(ban_tay(bang[a])[:2], ban_tay(bang[b])[:2])
                 + math.dist(ban_tay(bang[a])[2:], ban_tay(bang[b])[2:])
                 for a, b in itertools.combinations(bang, 2))
        print(f"  ✅ mọi cặp đều phân biệt được (gần nhất: {xa:.0f} ≥ {XA_TOI_THIEU:.0f})")
        print(f"  ✅ mọi khuỷu trong giới hạn khớp người (≤ {KHUYU_TOI_DA:.0f}°)")
    return 1 if loi else 0

if __name__ == "__main__":
    sys.exit(main())
