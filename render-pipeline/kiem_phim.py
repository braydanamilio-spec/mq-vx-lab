#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG CỦA BỘ PHIM v10 — chạy TRƯỚC khi tốn một giây render nào.  (6/9/2026)

Bảy phép, và mỗi phép đều có BÀI THỬ NGƯỢC ở `t_thu_nguoc()`. §13.11: một cổng chỉ chạy trên
dữ liệu thật và báo "0 lỗi" thì con số ấy có hai nghĩa ngược nhau — "sạch" và "cổng chết".

    python3 kiem_phim.py            # chạy cả bảy phép + bài thử ngược
"""
import io
import json
import os
import re
import statistics
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
import phim_gu as GU          # noqa: E402
import phim_anh as A          # noqa: E402
import phim as P              # noqa: E402

ENG = os.path.join(os.path.dirname(GOC), "engine-remotion")


def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _sang(c):
    def f(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (f(x) for x in _hex(c))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def tuong_phan(a, b):
    x, y = _sang(a), _sang(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


# ══ 1. MÀU THƯƠNG HIỆU PHẢI ĐỌC ĐƯỢC TRÊN NỀN TỐI ═══════════════════════════════════════════
# §14.5: `chinh` là màu của DẤU HIỆU, không phải màu của bộ phim. Lớp dữ liệu vẽ `chinh` lên
# dải tối chân khung (`nen` + phủ đen), nên phép đo đúng là tương phản với `nen`, sàn 3,0.
def t_tuong_phan():
    loi = []
    for m, k in GU.KENH.items():
        for truong in ("chinh", "phu"):
            t = tuong_phan(k[truong], k["nen"])
            if t < 3.0:
                loi.append(f"{m}.{truong} {k[truong]} trên nền {k['nen']}: {t:.2f} < 3.0")
    return loi


# ══ 2. KHÔNG KÊNH NÀO TRÙNG BỘ NHẬN DIỆN HÌNH ═══════════════════════════════════════════════
# §14.1: thêm mười cái giống nhau không phải mở rộng. Bộ nhận diện = (kỹ thuật, bảng màu).
# Kỹ thuật trùng thì được — 18 kênh trên 6 kỹ thuật là bắt buộc trùng — nhưng CẢ CẶP thì không.
def t_khong_trung():
    thay, loi = {}, []
    for m, k in GU.KENH.items():
        khoa = (k["kt"], k["mau"])
        if khoa in thay:
            loi.append(f"{m} trùng bộ (kỹ thuật, bảng màu) với {thay[khoa]}")
        thay[khoa] = m
    for m, k in GU.KENH.items():
        for t in ("sang", "may", "the"):
            if len(k[t]) < 30:
                loi.append(f"{m}.{t} quá ngắn ({len(k[t])} ký tự) — mô hình sẽ bỏ qua")
    return loi


# ══ 3. NGÂN SÁCH PROMPT — ĐO VẬT THẬT, KHÔNG ƯỚC LƯỢNG ══════════════════════════════════════
# §15.13: bản ước lượng bằng công thức lệch 140 ký tự và tốn ba lượt cắt mò. `ca_xau_nhat()`
# ghép bằng CHÍNH `prompt_anh` với câu cảnh dài nhất mà lệnh hệ thống cho phép.
def t_ngan_sach():
    n, m = P.ca_xau_nhat()
    if n > A.KY_TU_MAX:
        return [f"prompt ca xấu nhất {n} ký tự (kênh {m}) > trần {A.KY_TU_MAX}"]
    return []


# ══ 4. CÂU AN TOÀN KHÔNG ĐƯỢC LÀ CÂU RỖNG ═══════════════════════════════════════════════════
# §15.20: cổng so A với B mà A và B cùng đọc MỘT nguồn thì nó chỉ chứng minh hai bên nhất
# quán. Ở đây kiểm NỘI DUNG: câu an toàn phải thật sự cấm chữ và thật sự đòi tràn khung.
def t_an_toan():
    t = GU.AN_TOAN.lower()
    loi = []
    for phai_co in ("no text", "no logos", "bleeds"):
        if phai_co not in t:
            loi.append(f"AN_TOAN thiếu ý {phai_co!r}")
    return loi


# ══ 5. LỚP DỮ LIỆU KHÔNG ĐƯỢC VẼ CẢNH ═══════════════════════════════════════════════════════
# Ràng buộc chính anh đặt ra: code chỉ vẽ chart và số liệu. Cổng đọc MÃ THẬT của `LopSo.tsx`
# (bỏ chú thích trước — §17.15, cổng đọc lời kể về con dao thành con dao) và bắt mọi thứ
# trông như vẽ cảnh: đường path SVG, hình người, phòng, cây.
CAM_VE = ("<path", "<circle", "<polygon", "<ellipse", "nguoi", "phong", "canh_ve", "NenPhong")


def t_lop_khong_ve_canh():
    p = os.path.join(ENG, "src", "phim", "LopSo.tsx")
    src = io.open(p, encoding="utf-8").read()
    ma = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    ma = re.sub(r"(?m)^\s*//.*$", "", ma)
    return [f"LopSo.tsx chứa {c!r} — lớp dữ liệu không được vẽ cảnh" for c in CAM_VE
            if c in ma]


# ══ 6. ENGINE KHÔNG CÒN ĐƯỜNG NÀO VẼ NỀN BẰNG CODE ══════════════════════════════════════════
# Nhịp không có ảnh phải MƯỢN ảnh nhịp bên cạnh, không được rơi về một khung vẽ tay. Đo bằng
# cách đọc mã `Phim.tsx`: nó chỉ được phép nhận nền qua `<Img>`.
def t_chi_anh():
    p = os.path.join(ENG, "src", "phim", "Phim.tsx")
    ma = re.sub(r"/\*.*?\*/", "", io.open(p, encoding="utf-8").read(), flags=re.S)
    ma = re.sub(r"(?m)^\s*//.*$", "", ma)
    loi = []
    if "<Img" not in ma:
        loi.append("Phim.tsx không có <Img> — nền không tới từ ảnh AI")
    for c in ("NenQue", "CanhVe", "NenPhong", "MoDun"):
        if c in ma:
            loi.append(f"Phim.tsx còn gọi {c} — đường vẽ nền bằng code chưa bị cắt")
    return loi


# ══ 7. NHỊP — ĐO TRÊN DANH SÁCH NHỊP, TRƯỚC KHI RENDER ══════════════════════════════════════
# §12.11: nhịp là việc của khâu viết. Ở bộ này nó là việc của `chia_nhip`, nên đo được mà
# không cần giọng đọc thật: dựng một dòng thời gian giả rồi chia.
def t_nhip():
    loi = []
    for tong, n in ((30.0, 12), (60.0, 20), (18.0, 9)):
        moc = [(tong * i / n, tong * (i + 1) / n - 0.1) for i in range(n)]
        tu = [{"t": tong * k / (n * 6), "d": 0.2, "w": "w"} for k in range(n * 6)]
        nhip = P.chia_nhip([{"loi": "x"} for _ in range(n)], moc, tu, tong)
        d = [x["e"] - x["s"] for x in nhip]
        if max(d) > P.TRAN_NHIP + 0.4:
            loi.append(f"nhịp dài nhất {max(d):.2f}s > trần {P.TRAN_NHIP}")
        if statistics.median(d) > 2.5:
            loi.append(f"trung vị {statistics.median(d):.2f}s > 2.5s")
    return loi


# ══ 8. `.tai.json` PHẢI KHỚP HỢP ĐỒNG CỦA `day_kho.py` ══════════════════════════════════════
# Bản đầu viết `youtube.tieu_de`, không có `loai`, và `dang_duoc` là DANH SÁCH — trong khi
# `day_kho` đọc `yt.get("title")`, `d.get("loai")`, và duyệt `dang_duoc` bằng `.items()`.
# Ba chỗ lệch, cả ba hỏng CÂM: video vẫn được nhặt và đẩy đi, chỉ là tiêu đề rỗng và không nền
# tảng nào bật. §10.3 — thiếu `.tai.json` đúng là có video mà không đăng được.
#
# Cổng đọc TRƯỜNG MÀ `day_kho.py` THẬT SỰ LẤY (quét mã của chính nó, bỏ chú thích trước —
# §17.15), rồi đối chiếu với một `.tai.json` sinh thật. Không chép tay danh sách trường: chép
# tay là cổng sẽ đúng hôm nay và sai vào ngày `day_kho` đổi (§13.2).
def t_hop_dong_tai():
    import phim_dang as PD
    p = os.path.join(GOC, "day_kho.py")
    if not os.path.exists(p):
        return ["không tìm thấy day_kho.py — không kiểm được hợp đồng"]
    # CHỈ QUÉT HÀM THẬT SỰ ĐỌC `.tai.json`, không quét cả tệp. Bản đầu quét cả tệp và bắt oan
    # ngay lượt chạy đầu: `d.get("channels")` ở một hàm khác đọc `channels.yaml`, chẳng liên
    # quan gì tới `.tai.json`. §13.8 — cổng bắt oan tệ hơn cổng không bắt, vì nó ép người ta
    # đi sửa thứ không hỏng và làm chìm dòng đỏ thật nằm cạnh.
    import ast
    cay = ast.parse(io.open(p, encoding="utf-8").read())
    ma = ""
    for nut in ast.walk(cay):
        if isinstance(nut, ast.FunctionDef) and '.tai.json' in ast.unparse(nut):
            ma += ast.unparse(nut) + "\n"
    if not ma:
        return ["không tìm thấy hàm nào của day_kho.py đọc .tai.json"]
    d = PD.viet_bai("realcost", "THE REAL COST", "the real cost of a $12 lunch",
                    "HOOK", "$295K OVER 30 YEARS", 17.0, False,
                    [{"cua": "One line.", "lop": {"k": "so", "so": "$295K", "don": "30 YEARS"}}])
    loi = []
    for truong in sorted(set(re.findall(r'd\.get\("(\w+)"', ma))):
        if truong not in d:
            loi.append(f"day_kho đọc d[{truong!r}] mà .tai.json không có")
    yt = d.get("youtube") or {}
    for truong in sorted(set(re.findall(r'yt\.get\("(\w+)"', ma))):
        if truong not in yt:
            loi.append(f"day_kho đọc youtube[{truong!r}] mà .tai.json không có")
    if not isinstance(d.get("dang_duoc"), dict):
        loi.append("dang_duoc phải là DICT — day_kho duyệt nó bằng .items()")
    if not (d["youtube"].get("title") or "").strip():
        loi.append("youtube.title rỗng — đăng lên sẽ không có tiêu đề")
    return loi


# ══ 9. KHÔNG ĐƯỢC MƯỢN ẢNH  ═══════════════════════════════════════════════════════════════
# Anh: *"ko lấy ảnh lung tung là giảm chất lượng videos rác."* Cơ chế mượn ảnh hàng xóm đã bị
# gỡ; cổng này canh để nó không quay lại — vì nó rất dễ quay lại: mỗi lần ai đó thấy "tập bị
# hoãn vì thiếu một ảnh" thì phản xạ đầu tiên là thêm một tầng đỡ.
def t_khong_muon_anh():
    import ast
    ma = ast.unparse(ast.parse(io.open(os.path.join(GOC, "phim.py"), encoding="utf-8").read()))
    loi = []
    if "ThieuAnh" not in ma:
        loi.append("phim.py không còn lớp ThieuAnh — sàn ảnh 100% đã bị gỡ")
    # Dấu vết của phép mượn: gán `anh` của nhịp này bằng `anh` của nhịp khác.
    if re.search(r"n\['anh'\]\s*=\s*cuoi|nhip\[-1\]\['anh'\]\s*=\s*nhip\[0\]", ma):
        loi.append("phim.py có gán ảnh nhịp này bằng ảnh nhịp khác — mượn ảnh đã quay lại")
    return loi


# ══ 10. KHỐI BỐ CỤC VÀ KHỐI PHONG CÁCH PHẢI NGẮN ══════════════════════════════════════════
# Ba lần trong một ngày em nới hai khối này ra và cả ba lần nội dung khung hình bị nuốt:
#   · tả nét hình que 90 chữ  -> 8/8 khung là hình que trần trên nền trắng
#   · thêm luật chừa đầu 45 chữ -> tập y tá ra làng Địa Trung Hải
#   · `sang`/`may` lẫn nội dung -> 8/8 khung cận mặt trong phòng khách
# Prompt có ngân sách chú ý, không chỉ có ngân sách ký tự: mỗi chữ thêm vào khối đứng TRƯỚC là
# một chữ bị pha loãng ở khối cảnh đứng SAU. Trần đặt ở mức của bản đang chạy tốt, cộng 15%.
def t_khoi_ngan():
    loi = []
    for ten, s, tran in (("BO_CUC_DOC", GU.BO_CUC_DOC, 200),
                         ("BO_CUC_NGANG", GU.BO_CUC_NGANG, 200),
                         ("GIAI_PHAU", GU.GIAI_PHAU, 320),
                         ("AN_TOAN", GU.AN_TOAN, 260)):
        if len(s) > tran:
            loi.append(f"{ten} dài {len(s)} ký tự > trần {tran} — sẽ nuốt khối cảnh")
    for m, t in GU.KY_THUAT.items():
        if len(t) > 1000:
            loi.append(f"KY_THUAT[{m!r}] dài {len(t)} > 1000 ký tự")
    return loi


PHEP = [("tương phản màu thương hiệu", t_tuong_phan),
        ("không kênh nào trùng nhận diện", t_khong_trung),
        ("ngân sách prompt", t_ngan_sach),
        ("câu an toàn có nội dung", t_an_toan),
        ("lớp dữ liệu không vẽ cảnh", t_lop_khong_ve_canh),
        ("engine chỉ nhận nền từ ảnh AI", t_chi_anh),
        ("nhịp 1,5–2,5 giây", t_nhip),
        (".tai.json khớp hợp đồng day_kho", t_hop_dong_tai),
        ("không mượn ảnh nhịp khác", t_khong_muon_anh),
        ("khối bố cục/phong cách không phình", t_khoi_ngan)]


def t_thu_nguoc() -> list:
    """PHÁ có chủ đích, rồi đòi cổng phải BẮT. Không có phép này thì "0 lỗi" vô nghĩa."""
    loi = []
    goc = dict(GU.KENH["howlong"])

    GU.KENH["howlong"]["chinh"] = "#141C24"          # gần như trùng nền
    if not t_tuong_phan():
        loi.append("cổng tương phản KHÔNG bắt được màu tối thui")
    GU.KENH["howlong"].update(goc)

    GU.KENH["howlong"]["kt"] = GU.KENH["survive"]["kt"]
    GU.KENH["howlong"]["mau"] = GU.KENH["survive"]["mau"]
    if not t_khong_trung():
        loi.append("cổng trùng nhận diện KHÔNG bắt được hai kênh giống hệt")
    GU.KENH["howlong"].update(goc)

    tran = A.KY_TU_MAX
    A.KY_TU_MAX = 200
    if not t_ngan_sach():
        loi.append("cổng ngân sách prompt KHÔNG bắt được prompt vượt trần")
    A.KY_TU_MAX = tran

    at = GU.AN_TOAN
    GU.AN_TOAN = "x"
    if not t_an_toan():
        loi.append("cổng câu an toàn KHÔNG bắt được câu rỗng")
    GU.AN_TOAN = at

    import phim_dang as PD
    goc_vb = PD.viet_bai
    PD.viet_bai = lambda *a, **k: {"youtube": {}, "dang_duoc": []}
    if not t_hop_dong_tai():
        loi.append("cổng hợp đồng .tai.json KHÔNG bắt được tệp thiếu trường")
    PD.viet_bai = goc_vb

    bc = GU.BO_CUC_DOC
    GU.BO_CUC_DOC = "x" * 400
    if not t_khoi_ngan():
        loi.append("cổng khối ngắn KHÔNG bắt được khối bố cục phình gấp đôi")
    GU.BO_CUC_DOC = bc

    tr = P.TRAN_NHIP
    P.TRAN_NHIP = 30.0
    if not t_nhip():
        loi.append("cổng nhịp KHÔNG bắt được cảnh dài 30 giây")
    P.TRAN_NHIP = tr
    return loi


def main() -> int:
    xau = 0
    for ten, f in PHEP:
        try:
            ds = f()
        except Exception as e:
            ds = [f"cổng nổ: {type(e).__name__}: {e}"]
        print(("   ✅ " if not ds else "   ❌ ") + ten)
        for d in ds:
            print("        ·", d)
        xau += len(ds)
    tn = t_thu_nguoc()
    print(("   ✅ " if not tn else "   ❌ ") + "bài thử ngược (cổng có bắt thật không)")
    for d in tn:
        print("        ·", d)
    xau += len(tn)
    print(("\n✅ SẠCH" if not xau else f"\n❌ {xau} lỗi"))
    return 0 if not xau else 1


if __name__ == "__main__":
    raise SystemExit(main())
