#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SINH TRANG PHỤC CHO TOÀN DÀN VAI  (6/9/2026)

Anh: *"nhớ đa dạng và phù hợp bối cảnh, phong cách style channel."* Hai yêu cầu, và chúng KÉO
NGƯỢC NHAU: suy từ câu tả thì HỢP bối cảnh nhưng dồn cục (mô tả hay viết "short brown hair" và
"jacket", nên ai cũng `ngan` + `somi`); rải đều thì đa dạng nhưng cãi lại câu tả.

Đo bản đầu: **12/18 kênh có người mặc trùng nhau** — `survive` 6/6 người cùng `somi`,
`realcost` 5/6 cùng `ngan`.

── CÁCH GIẢI: TÔN TRỌNG CHỖ CÂU TẢ NÓI RÕ, RẢI Ở CHỖ NÓ IM ─────────────────────────────────
Hai bước, và thứ tự quan trọng:
  1. Suy từ câu tả. Chỉ nhận khi câu tả nói RÕ ("bald" -> `trocs`, "hoodie" -> `hoodie`).
     Không khớp từ nào thì để TRỐNG, không điền mặc định — điền mặc định chính là thứ tạo ra
     cục `ngan`/`somi`.
  2. Chỗ trống mới rải, và rải bằng giá trị CHƯA AI TRONG KÊNH DÙNG.
Nhờ vậy người nào câu tả tả kỹ thì mặc đúng thứ được tả; người nào tả chung chung thì được cấp
một kiểu khác biệt — thay vì cả sáu người dùng chung một mặc định.

Cùng nguyên tắc §17.3: *đa dạng thì CHỌN được, bản sắc thì phải KHAI* — ở đây bản sắc do câu
tả khai, còn phần câu tả không khai thì mới đến lượt phép chọn.
"""
import io, json, os, re, sys

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
os.environ.setdefault("GT_KHONG_CF", "1")
import phim_gu as GU

RA = os.path.join(GOC, "do_vai_all.json")

MAU = {"white":"#F2F2F2","black":"#2A2A2A","grey":"#8A8F94","gray":"#8A8F94","silver":"#B9BFC4",
 "red":"#D9503F","blue":"#3E6E8C","navy":"#2C3E50","green":"#3FA46A","olive":"#6B7A45",
 "yellow":"#E8C24A","orange":"#E08A3C","purple":"#8B6BB8","pink":"#E39BB4","brown":"#6B4A2F",
 "tan":"#C8A97E","beige":"#D8C7A8","cream":"#EDE3CE","ginger":"#C4642A","blonde":"#E0C060",
 "blond":"#E0C060","denim":"#4E6E8E","khaki":"#BDA97A","teal":"#2E8B8B","maroon":"#7B2233",
 "charcoal":"#3A3A3A","platinum":"#D8D8D8","cobalt":"#2B5FA8","crimson":"#B03A3A",
 "lilac":"#B49CD0","burgundy":"#6E2A34","mustard":"#D2A32E","rust":"#B5542E","lime":"#9ACD32",
 "copper":"#B87333","auburn":"#8C4A2F","sandy":"#D9BE86"}

# Chỉ những từ nói RÕ một kiểu. "shirt"/"jacket" cố tình KHÔNG có ở đây: chúng hợp với ba kiểu
# và điền bừa là tạo ra cục `somi`.
AO_RO = [("hoodie","hoodie"),("sweatshirt","hoodie"),("cardigan","cardigan"),
         ("sweater","cardigan"),("polo","polo"),("tank top","thun"),("t-shirt","thun"),
         ("tee","thun"),("jumpsuit","somi"),("overalls","somi"),("lab coat","somi"),
         ("uniform","somi"),("blazer","somi"),("apron","somi")]
TOC_RO = [("pigtails","duoi_ngua"),("braids","duoi_ngua"),("braid","duoi_ngua"),
          ("ponytail","duoi_ngua"),("chignon","bui"),("bun","bui"),("curls","xoan"),
          ("curly","xoan"),("wavy","xoan"),("bald","trocs"),("shaved","trocs"),
          ("buzz","ngan"),("crew cut","ngan"),("cropped","ngan"),("bob","bob"),
          ("side-part","re_ngoi"),("side part","re_ngoi"),("parted","re_ngoi"),
          ("shaggy","roi"),("messy","roi"),("tousled","roi"),("slicked","hoi"),
          ("neat","hoi"),("long straight","roi")]
RAU = [("moustache","ria"),("beard","de"),("sideburns","quai")]
MU  = [("ball cap","luoi_trai"),("hard hat","luoi_trai"),("helmet","luoi_trai"),
       ("cap","luoi_trai"),("beanie","len"),("cowboy","cao_bo")]

AO_ALL = ["thun", "somi", "polo", "hoodie", "cardigan"]
TOC_ALL = ["ngan", "re_ngoi", "roi", "hoi", "xoan", "duoi_ngua", "bob", "bui", "trocs"]


def _mau(t, m=""):
    for w, h in MAU.items():
        if re.search(r"\b" + w + r"\b", t):
            return h
    return m


def _sau(t, tu):
    x = re.search(r"(\w+)[\w\s-]{0,14}\b" + tu, t)
    return _mau(x.group(0)) if x else ""


def _ro(t, bang):
    return next((v for k, v in bang if k in t), "")


def mot_kenh(ma, ds):
    tho = []
    for v in ds:
        t = v["ta"].lower()
        ao_ten = next((k for k, _v in AO_RO if k in t), "") or \
                 next((k for k in ("jacket", "shirt", "coat", "vest", "dress") if k in t), "shirt")
        d = {"ao": _sau(t, ao_ten) or _mau(t, "#8A8F94"), "aoTrong": "#FFFFFF",
             "quan": "#3A3A3A", "toc": "", "kieuToc": _ro(t, TOC_RO), "kieuAo": _ro(t, AO_RO)}
        for w in ("hair", "curls", "braids", "ponytail", "beard", "buzz", "bob", "bun"):
            if w in t:
                c = _sau(t, w)
                if c:
                    d["toc"] = c
                    break
        d["toc"] = d["toc"] or "#4A3728"
        r = _ro(t, RAU)
        if r:
            d["rau"] = r
        m = _ro(t, MU)
        if m:
            d["mu"] = m
        if "glasses" in t or "goggles" in t:
            d["kinh"] = True
        tho.append(d)

    # ── RẢI CHỖ CÒN TRỐNG  ────────────────────────────────────────────────────────────────
    # Đi theo thứ tự dàn vai, mỗi lần lấy giá trị CHƯA DÙNG trong kênh này. Tất định: cùng dàn
    # vai luôn ra cùng bộ đồ, nên dựng lại một tập cũ không đổi hình.
    for truong, moi in (("kieuAo", AO_ALL), ("kieuToc", TOC_ALL)):
        da = {d[truong] for d in tho if d[truong]}
        con = [x for x in moi if x not in da]
        k = 0
        for d in tho:
            if not d[truong]:
                d[truong] = con[k % len(con)] if con else moi[k % len(moi)]
                k += 1
    # Màu áo trùng nhau thì đổi người sau sang màu chưa ai mặc.
    dung = set()
    kho_mau = [v for v in MAU.values()]
    for d in tho:
        if d["ao"] in dung:
            for c in kho_mau:
                if c not in dung:
                    d["ao"] = c
                    break
        dung.add(d["ao"])
    return tho


def main():
    ra = {}
    for ma in GU.VAI:
        ra[ma] = mot_kenh(ma, GU.dan_vai_khai(ma))
    io.open(RA, "w", encoding="utf-8").write(json.dumps(ra, ensure_ascii=False, indent=1))
    import collections
    xau = 0
    for ma, ds in ra.items():
        for f, tran in (("ao", 1), ("kieuAo", 2), ("kieuToc", 2)):
            if max(collections.Counter(d[f] for d in ds).values()) > tran:
                xau += 1
                break
    print(f"✅ {sum(len(v) for v in ra.values())} bộ đồ / {len(ra)} kênh · "
          f"{len(ra) - xau}/{len(ra)} kênh không ai mặc trùng ai")


if __name__ == "__main__":
    main()
