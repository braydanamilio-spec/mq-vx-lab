#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GHÉP DÒNG MỚI VÀO BẢNG THẬT CỦA `giai_thich.py`  (6/9/2026)

Tách khỏi `bang_mo_rong.py` có chủ ý: bộ kia GỌI MẠNG và có thể hỏng giữa chừng, bộ này SỬA
MÃ NGUỒN. Trộn hai việc ấy vào một lệnh là cách chắc chắn để một lượt gọi hỏng giữa chừng để
lại `giai_thich.py` sửa dở.

── BA ĐIỀU BỘ NÀY PHẢI LÀM ĐÚNG ─────────────────────────────────────────────────────────────
1. **Số cột (arity) khác nhau từng bảng.** `bang_mo_rong` chỉ sinh `(tên, số, biểu tượng)`, mà
   `QUANG_DUONG` có 5 cột và `CO_LON` có 4. Nối thẳng là gãy ngay lượt dựng đầu — nên mỗi bảng
   khai một hàm `_no()` biến 3 cột thành đúng số cột của nó.
2. **Khử trùng LẦN NỮA ở đây.** Bốn tiến trình chạy song song, mỗi tiến trình chỉ biết bảng gốc
   nên hai tiến trình có thể cùng đề cử một thứ. Bảng gốc `_khu` sẽ khử lúc chạy, nhưng để lọt
   vào tệp nguồn thì nó nằm đó mãi và làm mọi phép đếm nói dối.
3. **Chèn vào ĐÚNG chỗ đóng ngoặc của bảng**, đọc bằng `ast` chứ không bằng regex — regex trên
   mã nguồn là thứ tệp luật đã trả giá bốn lần trong một ngày (§17.15).
"""
import ast, io, json, os, re, sys, glob

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
os.environ.setdefault("GT_KHONG_CF", "1")
import giai_thich as G

TEP = os.path.join(GOC, "giai_thich.py")

# ══ BA LỖI ĐỌC TAY BẮT ĐƯỢC, VÀ CHỖ CHỮA  (6/9/2026) ════════════════════════════════════════
# Đọc 24 dòng của hai bảng đầu (§13.20). Cả ba lỗi đều lọt qua bốn cổng của `bang_mo_rong` vì
# chúng không phải lỗi CON SỐ — con số đúng cả — mà là lỗi CÂU CHỮ và lỗi BIỂU TƯỢNG.
#
# 1. **"a electric scooter"** — mạo từ sai trước nguyên âm. Máy sửa được (§13.12).
# 2. **"a 4‑by‑8 sheet of OSB panel"** — gạch nối U+2011 (không phải ASCII) và một từ viết tắt
#    kỹ thuật. Chuẩn hoá gạch nối; loại dòng có từ viết tắt vì nó phá đúng luật "thứ người xem
#    ĐÃ có cảm giác".
# 3. **"a voyage from Salt Lake City to Provo"** — nặng nhất. `QUANG_DUONG` có trường `kieu`
#    (`den` · `vong` · `tuyen`) quyết định CÂU DẪN. Em mặc định `den` cho mọi dòng mới, nên câu
#    ra là *"how long to walk to a voyage from Salt Lake City to Provo"* — vô nghĩa. Tuyến A→B
#    phải là `tuyen`, và tên phải viết đúng khuôn bảng gốc dùng: **"New York to Los Angeles"**,
#    không kèm mạo từ và không kèm một danh từ đồng nghĩa do mô hình bịa ra (passage · voyage ·
#    expedition · span). Đây đúng §14.16: *mọi ràng buộc sẽ được thoả bằng cách rẻ nhất câu chữ
#    cho phép* — em xin "quãng đường", mô hình trả về "một chuyến đi", và cả hai đều đúng chữ.

_BO = {"a", "an", "the"}
_VIET_TAT = re.compile(r"\b[A-Z]{2,}\b")     # OSB · HVAC · CNC — jargon, không phải đời thường
_TUYEN = re.compile(r"^(?:an?|the)\s+\w+\s+(?:from|between)\s+(.+?)\s+(?:to|and)\s+(.+)$", re.I)
_TUYEN2 = re.compile(r"^(?:an?|the)\s+(.+?)\s+to\s+(.+)$", re.I)


def don_ten(ten):
    """Chuẩn hoá câu chữ. Trả về "" nghĩa là LOẠI dòng."""
    ten = (ten.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
              .replace("\u2019", "'").strip())
    if _VIET_TAT.search(ten):
        return ""
    # "a electric scooter" -> "an electric scooter"; "an bison" -> "a bison"
    m = re.match(r"^(a|an)\s+(\S+)(.*)$", ten, re.I)
    if m:
        dung = "an" if m.group(2)[:1].lower() in "aeiou" else "a"
        ten = dung + " " + m.group(2) + m.group(3)
    return ten


def tuyen(ten):
    """Nhận ra tuyến A→B và trả về tên theo ĐÚNG khuôn bảng gốc, hoặc None."""
    for m in (_TUYEN.match(ten), _TUYEN2.match(ten)):
        if m:
            a, b = m.group(1).strip(), m.group(2).strip()
            if 1 <= len(a.split()) <= 4 and 1 <= len(b.split()) <= 4:
                return f"{a} to {b}"
    return None


# ── BIỂU TƯỢNG: LỚP BỔ SUNG  (đo 6/9) ───────────────────────────────────────────────────────
# Đọc 12 dòng `KHOI_LUONG`: **10/12 rơi về `nguoi`** — bảng từ khoá của engine không có chữ nào
# cho đồ nghề, đồ gỗ, dụng cụ thể thao. Một biểu tượng người đứng cạnh mọi con số cân nặng thì
# lớp biểu tượng hết làm được việc của nó.
# Lớp này để RIÊNG ở đây, KHÔNG sửa `giai_thich._BT_TU`: bảng ấy là nguồn sự thật của engine và
# đang được dùng ở chỗ khác — sửa nó là đổi hình của những tập đã dựng (§11 "đừng tạo nguồn thứ
# hai", và §12.5 "câu luật đúng ở ngữ cảnh nó sinh ra").
_BT_THEM = (
    ("xe",        ("scooter", "bike", "bicycle", "van", "motorcycle", "wagon", "trailer",
                   "tractor", "forklift", "ambulance", "taxi", "cart")),
    ("may_bay",   ("helicopter", "rocket", "drone", "glider", "satellite", "shuttle")),
    ("ca_voi",    ("dolphin", "orca", "seal", "squid", "tuna", "boat", "ship", "ferry",
                   "kayak", "canoe", "submarine", "anchor")),
    ("huou",      ("bison", "moose", "horse", "cow", "bull", "deer", "bear", "lion",
                   "rhino", "hippo", "camel", "zebra", "gorilla", "ostrich")),
    ("meo",       ("puppy", "kitten", "rabbit", "hamster", "parrot", "goat", "sheep")),
    ("nha",       ("bookshelf", "sofa", "couch", "mattress", "dresser", "cabinet", "table",
                   "chair", "desk", "door", "window", "fridge", "washer", "oven", "stove",
                   "furniture", "toolbox", "wrench", "hammer", "drill", "ladder", "brick",
                   "shed", "fence", "pipe", "tile", "panel", "beam", "sheet")),
    ("nguyen_tu", ("proton", "electron", "neutron", "quark", "photon", "ion", "grain",
                   "nanometre", "nanometer", "transistor")),
    ("te_bao",    ("neuron", "platelet", "chromosome", "dna", "protein", "enzyme", "ribosome")),
    ("vi_khuan",  ("spore", "pollen", "yeast", "mite", "amoeba")),
    ("cay",       ("seed", "leaf", "branch", "log", "sequoia", "oak", "pine", "bamboo")),
    ("lua",       ("furnace", "kiln", "torch", "blast", "lava", "magma", "ember", "coal",
                   "welding", "plasma")),
    ("coc",       ("bottle", "mug", "kettle", "jug", "can", "pot", "pan", "teapot")),
    ("dong_ho",   ("stopwatch", "timer", "calendar", "watch")),
    ("dien_thoai", ("laptop", "tablet", "monitor", "console", "camera", "headphone")),
    ("nguoi",     ("dumbbell", "barbell", "kettlebell", "treadmill", "stroller", "backpack",
                   "helmet", "boot", "shoe", "jacket", "suitcase", "ball")),
)


def bt_lai(ten, cu):
    """Tính lại biểu tượng: bảng engine trước (nguồn sự thật), rồi lớp bổ sung, rồi giữ cũ."""
    t = ten.lower()
    for bt, tu in list(G._BT_TU) + list(_BT_THEM):
        if any(re.search(r"\b" + re.escape(w) + r"e?s?\b", t) for w in tu):
            return bt
    return cu


def _ngan(ten):
    """Tên NGẮN để đặt cạnh con số. `QUANG_DUONG` dùng nó làm nhãn, nên phải bỏ mạo từ."""
    t = ten.split()
    return " ".join(t[1:]) if t and t[0].lower() in _BO else ten


NO = {
    # ("the Moon", 238900, "mat_trang", "den", "the Moon") — `den`/`vong`/`tuyen` là KIỂU câu.
    # Dòng mới mặc định `den` ("đi tới X"): đó là kiểu duy nhất đúng với MỌI nơi chốn, còn
    # `vong` (đi vòng quanh) và `tuyen` (tuyến A→B) chỉ đúng với một số mục và đoán sai thì
    # câu dẫn vô nghĩa. Đoán bừa còn tệ hơn không đoán (§13.12).
    "QUANG_DUONG": lambda t, s, b: ((lambda x: (x, s, b, "tuyen", "") if x else
                                      (t, s, b, "den", _ngan(t)))(tuyen(t))),
    "CO_LON":      lambda t, s, b: (t, s, "ft", b),
}


def _no(bang, r):
    return NO.get(bang, lambda t, s, b: (t, s, b))(*r)


def _dau(ten):
    tu = [w for w in re.findall(r"[a-z]+", ten.lower())
          if w not in {"a", "an", "the", "at", "of", "in", "on", "to", "from", "one",
                       "single", "full", "its"}]
    return tu[0] if tu else ten.lower()


def _cuoi_bang(src, ten):
    """Vị trí ký tự của dấu `]` đóng bảng — lấy từ AST, không từ regex."""
    t = ast.parse(src)
    for n in t.body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) \
           and n.targets[0].id == ten and isinstance(n.value, (ast.List, ast.Tuple)):
            # `end_col_offset` trỏ NGAY SAU dấu đóng; lùi một ký tự để chèn vào TRONG bảng.
            dong = src.splitlines(keepends=True)
            vt = sum(len(x) for x in dong[:n.value.end_lineno - 1]) + n.value.end_col_offset
            return vt - 1
    raise RuntimeError(f"không tìm thấy bảng {ten}")


def main():
    kho, dem = {}, {}
    for p in sorted(glob.glob(os.path.join(GOC, "bang_moi*.json"))):
        for b, ds in json.load(io.open(p, encoding="utf-8")).items():
            kho.setdefault(b, []).extend(ds)

    src = io.open(TEP, encoding="utf-8").read()
    goc_len = len(src)
    for b in sorted(kho, key=lambda x: -_cuoi_bang(src, x)):   # chèn từ CUỐI lên, giữ vị trí
        cu = list(getattr(G, b))
        co = {_dau(r[0]) for r in cu}
        moi, bo = [], 0
        for t, so, bt in kho[b]:
            t = don_ten(t)
            if not t:
                bo += 1; continue
            d = _dau(t)
            if d in co:
                continue
            co.add(d)
            moi.append(_no(b, (t, so, bt_lai(t, bt))))
        if bo:
            print(f"   ⚠ {b}: loại {bo} dòng vì từ viết tắt kỹ thuật")
        # ── THỨ TỰ DÒNG MỚI LÀ THỨ TỰ NGƯỜI XEM GẶP CHÚNG ──────────────────────────────
        # `_lay` lấy `ds[i % n]`, nên thứ tự trong tệp CHÍNH LÀ lịch phát. Dòng mới sinh theo
        # NHÓM CHỦ ĐỀ nên nối thẳng cho ra 12 tập liên tiếp toàn dụng cụ điện — đo được ở
        # HOW LOUD tập 40–51. Không có lỗi nào báo: mỗi tập đều đúng, chỉ là người đăng ký
        # xem mười hai tập giống nhau.
        # Sắp theo GIÁ TRỊ giảm dần: vừa đúng quy ước bảng gốc ghi sẵn ("mạnh nhất trước"),
        # vừa trộn các nhóm vào nhau, vì độ to của một cái máy khoan và của một con vật không
        # đi theo nhóm nào cả.
        moi.sort(key=lambda r: -abs(r[1]))
        # ── SỐ NGUYÊN PHẢI Ở LẠI LÀ SỐ NGUYÊN  (đo 6/9) ────────────────────────────────
        # AI trả về JSON nên `111` về tới đây là `111.0` (float). Bộ sinh ghép thẳng
        # `f"{db}"`, và màn hình hiện **"111.0 DECIBELS"** — đo được 324 nhịp của 4 kênh.
        # Không cổng nào bắt: con số đúng, kiểu dữ liệu hợp lệ, chỉ có mắt người đọc ra là
        # sai. Bảng gốc viết `("a jet at takeoff", 140, ...)` — số nguyên. Giữ đúng kiểu ấy
        # ngay ở chỗ ghi, thay vì đi sửa mọi chỗ ĐỌC nó (bốn bộ sinh, và bộ thứ năm mai sau).
        moi = [tuple(int(x) if isinstance(x, float) and x.is_integer() and abs(x) >= 1
                     else x for x in r) for r in moi]
        if not moi:
            dem[b] = (len(cu), len(cu)); continue
        khoi = (f"\n    # ── NỐI THÊM 6/9/2026 · {len(moi)} mục, mỗi mục qua bốn cổng của\n"
                f"    #    `bang_mo_rong.py`; xuất xứ ở `bang_nguon_*.json`. Con số là ĐỀ NGHỊ\n"
                f"    #    của AI đã sống sót qua một lượt ĐỐI CHỨNG độc lập, không phải hằng\n"
                f"    #    số tra từ sách — nên nếu một mục nào bị người xem bắt sai, sửa THẲNG\n"
                f"    #    ở đây và giữ nguyên cơ chế.\n")
        for r in moi:
            khoi += "    " + repr(r) + ",\n"
        vt = _cuoi_bang(src, b)
        src = src[:vt] + khoi + src[vt:]
        dem[b] = (len(cu), len(cu) + len(moi))

    io.open(TEP, "w", encoding="utf-8").write(src)
    print(f"giai_thich.py  {goc_len:,} -> {len(src):,} ký tự\n")
    for b, (a, c) in sorted(dem.items()):
        print(f"  {b:<14} {a:>4} -> {c:>4} mục   ({'+' + str(c - a) if c > a else 'không đổi'})")


if __name__ == "__main__":
    main()
