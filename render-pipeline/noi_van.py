#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NỐI DÒNG MỚI VÀO BẢNG CHỮ CỦA `giai_thich.py`  (6/9/2026)

Tách khỏi `noi_bang.py` vì hai bảng khác bản chất ở đúng một chỗ quyết định: bảng SỐ sắp lại
theo giá trị giảm dần (vừa đúng quy ước "mạnh nhất trước", vừa trộn các nhóm chủ đề vào nhau);
bảng CHỮ không có cột giá trị để sắp, nên phải trộn bằng cách khác — nếu không thì hai chục tập
liên tiếp cùng rơi vào một nhóm chủ đề, đúng lỗi đã đo ở HOW LOUD tập 40–51 (mười hai tập liền
toàn dụng cụ điện).

Cách trộn ở đây: **xen kẽ theo bước nguyên tố cùng nhau với số dòng mới**. Dòng mới sinh ra
theo nhóm (30 dòng một nhóm), nên đi bước lớn là mỗi lần nhảy sang một nhóm khác hẳn. Cùng cơ
chế `_cap` dùng cho cặp dữ liệu và bộ chọn nền dùng cho nơi chốn.

Thứ tự dòng CŨ giữ nguyên tuyệt đối: không có ảnh nào gắn theo chỉ số ở các bảng này, nhưng
`vi_tri_short`/`vi_tri_long` chia đôi không gian theo chỉ số — đổi thứ tự cũ là đổi tập nào
thuộc bản ngắn, tập nào thuộc bản dài, tức đổi nội dung của những tập đã đăng.
"""
import ast, glob, io, json, os, re, sys

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
os.environ.setdefault("GT_KHONG_CF", "1")
import giai_thich as G
import bang_van as BV

TEP = os.path.join(GOC, "giai_thich.py")


def _cuoi_bang(src, ten):
    """Vị trí dấu `]` đóng bảng, lấy từ AST — không regex trên mã nguồn (§17.15)."""
    t = ast.parse(src)
    for n in t.body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) \
           and n.targets[0].id == ten and isinstance(n.value, (ast.List, ast.Tuple)):
            dong = src.splitlines(keepends=True)
            return sum(len(x) for x in dong[:n.value.end_lineno - 1]) + n.value.end_col_offset - 1
    raise RuntimeError(f"không tìm thấy bảng {ten}")


def _tron(ds):
    """Xen kẽ để hai dòng liền nhau không cùng nhóm chủ đề."""
    n = len(ds)
    if n < 4:
        return ds
    b = next((x for x in (37, 31, 29, 23, 19, 17, 13, 11, 7) if n % x), 1)
    return [ds[(i * b) % n] for i in range(n)]


def _viet(r) -> str:
    """Một dòng bảng thành mã nguồn. Phần tử `["_VE", …]` thành lời gọi `_ve(...)` THẬT.

    Vì sao không tự ghép chuỗi cảnh ở bộ sinh: `_ve` là nơi DUY NHẤT biết cách ghép sáu tầng,
    và cách ghép ấy đã đổi một lần (bỏ nhãn "background:"/"foreground:" kiểu ảnh chụp — chúng
    làm mô hình vẽ ra ẢNH CHỤP thay vì tranh phẳng, §12.6). Ghép sẵn thành chuỗi là đóng băng
    cách ghép của hôm nay vào dữ liệu, và lần sửa `_ve` sau sẽ không chạm tới được.
    """
    ra = []
    for x in r:
        if isinstance(x, (list, tuple)) and x and x[0] == "_VE":
            ra.append("_ve(" + ", ".join(repr(str(y)) for y in x[1:]) + ")")
        else:
            ra.append(repr(x))
    return "(" + ", ".join(ra) + ")"


def main():
    kho = {}
    for p in sorted(glob.glob(os.path.join(GOC, "bang_van_*.json"))):
        for b, ds in json.load(io.open(p, encoding="utf-8")).items():
            kho.setdefault(b, []).extend(tuple(x) for x in ds)

    src = io.open(TEP, encoding="utf-8").read()
    dem = {}
    for b in sorted(kho, key=lambda x: -_cuoi_bang(src, x)):   # chèn từ CUỐI lên
        dt = BV.BANG[b]
        cu = list(getattr(G, b))
        cuoi = dt.get("cuoi", False)
        co = {BV._dau_thuc(r[0], cuoi) for r in cu}
        moi = []
        for r in kho[b]:
            d = BV._dau_thuc(r[0], cuoi)
            if d in co:
                continue
            co.add(d)
            moi.append(r)
        if not moi:
            dem[b] = (len(cu), len(cu)); continue
        moi = _tron(moi)
        khoi = (f"\n    # ── NỐI THÊM 6/9/2026 · {len(moi)} mục qua bốn cổng của `bang_van.py`\n"
                f"    #    (dạng · không người · không chữ · không viết nghịch · không trùng).\n"
                f"    #    Bảng này KHÔNG có con số nào, nên không có gì để đối chứng và cũng\n"
                f"    #    không đụng tới luật nền 'AI không bao giờ cấp một con số'.\n")
        for r in moi:
            khoi += "    " + _viet(r) + ",\n"
        vt = _cuoi_bang(src, b)
        # ── DẤU PHẨY CỦA MỤC CUỐI  (đo 6/9/2026) ─────────────────────────────────────────
        # `_cuoi_bang` trả về vị trí NGAY TRƯỚC dấu `]`. Nếu mục cuối của bảng cũ không có dấu
        # phẩy treo thì khối mới dính thẳng vào nó: `("a", "b")\n    ("c", "d"),` — Python đọc
        # ra một LỜI GỌI HÀM, và nổ `TypeError: 'tuple' object is not callable` ngay lúc import.
        # Cú pháp vẫn hợp lệ nên `ast.parse` báo xanh; chỉ `import` mới nổ. Đây đúng §12.2 lật
        # ngược: **phân tích cú pháp xanh không có nghĩa là chạy được**.
        # Bảng số thoát nạn vì chúng tình cờ đều có dấu phẩy treo — tức nó là một quả mìn đang
        # chờ bảng đầu tiên không có.
        _tr = src[:vt].rstrip()
        if not _tr.endswith(","):
            src = _tr + ",\n" + src[vt:]
            vt = len(_tr) + 2
        src = src[:vt] + khoi + src[vt:]
        dem[b] = (len(cu), len(cu) + len(moi))

    io.open(TEP, "w", encoding="utf-8").write(src)
    for b, (a, c) in sorted(dem.items()):
        print(f"  {b:<14} {a:>4} -> {c:>4} mục  ({'+' + str(c - a) if c > a else 'không đổi'})")


if __name__ == "__main__":
    main()
