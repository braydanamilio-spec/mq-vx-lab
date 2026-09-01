#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG KHÔNG TRÙNG LẶP — mỗi kênh phải có đủ tập phân biệt, và long không được đụng short.

── VÌ SAO (1/9/2026) ───────────────────────────────────────────────────────────────────────
Anh: *"long và short cũng ko được trùng lặp nội dung, nội dung trên channel theo logic liền
mạch và ko lặp lại."* Đo trước khi sửa:

    18/18 kênh lặp nội dung y hệt trong vòng 1–21 tập; trung bình 6,9 tập phân biệt
    `howmuch` lặp ngay ở TẬP 1 — bộ sinh bỏ qua hẳn tham số `i`
    bản dài = các short nối lại (`bo(idx + c)`), nên nó vừa trùng short vừa TỰ LẶP 2–3 lần

Không lỗi nào báo. Kênh vẫn ra video mỗi ngày, chỉ là video thứ tám giống hệt video thứ hai.

── BA CÂU HỎI CỔNG ĐẶT ─────────────────────────────────────────────────────────────────────
  1. Kênh có đủ `TOI_THIEU` tập phân biệt không?  (dưới ngưỡng là lặp thấy được trong một tháng)
  2. Một bản dài có tự lặp chương không?
  3. Chương của bản dài có đụng nội dung short không?

Và một câu về dữ liệu nguồn: bảng nào có mục TRÙNG TÊN? Mục trùng không gây lỗi, nó chỉ lặng lẽ
thu hẹp không gian — bảng 33 mục có 2 mục trùng thì thực chất chỉ 31, và không ai biết.
"""
import collections
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
TOI_THIEU = 20          # tập phân biệt tối thiểu mỗi kênh
CHUONG = 10             # số chương của một bản dài sản xuất thật


def main() -> int:
    sys.path.insert(0, GOC)
    import giai_thich as G

    loi = 0

    # ── dữ liệu nguồn: mục trùng ────────────────────────────────────────────────────────
    tr = []
    for ten in dir(G):
        if not ten.isupper() or ten.startswith("_"):
            continue
        b = getattr(G, ten)
        if not isinstance(b, (list, tuple)) or not b or not isinstance(b[0], (list, tuple)):
            continue
        c = collections.Counter(x[0] for x in b)
        d = [k for k, n in c.items() if n > 1]
        if d:
            tr.append(f"{ten}({len(d)})")
    if tr:
        print(f"  ⚠ bảng có mục trùng: {', '.join(tr)} — không chặn (đã có `_khu` khử lúc chạy),")
        print("    nhưng nên dọn: mục trùng thu hẹp không gian nội dung mà không báo gì.")
    else:
        print("  ✅ không bảng dữ liệu nào có mục trùng tên")

    # ── ba câu hỏi chính ────────────────────────────────────────────────────────────────
    ns = []
    for k in G.KENH:
        ma = k["ma"]
        bo = G.BO_SINH[k["sinh"]]
        n = G.khong_gian(ma)
        ns.append(n)
        lg = [bo(G.vi_tri_long(ma, 0, c))[0] for c in range(CHUONG)]
        sh = {bo(G.vi_tri_short(ma, i))[0] for i in range(40)}
        tu_lap = len(lg) - len(set(lg))
        giao = len(set(lg) & sh)
        bao = []
        if n < TOI_THIEU:
            bao.append(f"chỉ {n} tập phân biệt (cần ≥ {TOI_THIEU})")
        if tu_lap:
            bao.append(f"bản dài tự lặp {tu_lap}/{CHUONG} chương")
        if giao:
            bao.append(f"{giao} chương trùng nội dung short")
        if bao:
            loi += 1
            print(f"  ❌ {ma:12s} " + " · ".join(bao))

    # ── LỜI KỂ CÓ ĐỔI GIỮA CÁC TẬP KHÔNG ────────────────────────────────────────────────
    # Nội dung khác nhau chưa đủ: nếu 100% câu chữ giống hệt và chỉ con số đổi thì người xem
    # hai tập vẫn nghe cùng một kịch bản. Đo lúc phát hiện: 127/130 câu (98%) cố định.
    # Đây là CẢNH BÁO, không chặn — nới nó cần viết biến thể cho từng câu của từng kênh, và một
    # cổng chặn ở mức chưa làm xong chỉ khiến người ta tắt cổng.
    tc = tl = 0
    for k in G.KENH:
        bo = G.BO_SINH[k["sinh"]]
        ds = [[x.get("loi", "") for x in bo(G.vi_tri_short(k["ma"], i))[3]] for i in range(6)]
        n = min(len(x) for x in ds)
        tc += sum(1 for j in range(n) if len({d[j] for d in ds}) == 1)
        tl += n
    pc = 100 * tc / max(1, tl)
    dau = "✅" if pc < 40 else "⚠"
    print(f"  {dau} lời kể cố định giữa các tập: {tc}/{tl} câu ({pc:.0f}%)"
          + ("" if pc < 40 else " — còn nhiều câu dùng lại nguyên văn"))

    if not loi:
        print(f"  ✅ 18/18 kênh: đủ tập phân biệt · bản dài không tự lặp · long không đụng short")
        print(f"     số tập phân biệt: trung bình {sum(ns)//len(ns)} · thấp nhất {min(ns)} · "
              f"cao nhất {max(ns)}")
        return 0
    print(f"\n❌ {loi} kênh còn lặp nội dung.")
    print("   Nới bằng cách THÊM DỮ LIỆU vào bảng của kênh ấy, hoặc đổi bộ sinh sang `_cap`")
    print("   (so sánh cặp) — `_cap` cho n·(n−1)/2 tập từ cùng n mục.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
