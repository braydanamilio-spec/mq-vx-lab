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


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _kc(a: str, b: str) -> float:
    """Khoảng cách màu có TRỌNG SỐ — xấp xỉ cách mắt người thấy, không phải Euclid trần.

    Mắt nhạy với xanh lá hơn hẳn với xanh dương, nên Euclid trên RGB nói hai màu xám và nâu
    khác nhau nhiều bằng hai màu lục khác nhau — sai đúng thứ đang cần đo."""
    (r1, g1, b1), (r2, g2, b2) = _rgb(a), _rgb(b)
    rm = (r1 + r2) / 2
    return ((2 + rm / 256) * (r1 - r2) ** 2 + 4 * (g1 - g2) ** 2
            + (2 + (255 - rm) / 256) * (b1 - b2) ** 2) ** 0.5


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
    # ── MÀU PHẢI CÁCH NHAU ĐỦ ĐỂ MẮT THẤY, KHÔNG CHỈ KHÁC CHUỖI  (soi khung 6/9/2026) ────
    # Bản cũ so `d["ao"] in dung` — phép so CHUỖI BẰNG NHAU. Nên `#3A3A3A` và `#2A2A2A` đi lọt:
    # khác nhau đúng 16/255 ở cả ba kênh màu, và cổng báo "không ai mặc trùng ai".
    # Soi khung `v11_howhot_0040`: Gus (#3A3A3A) và Tank (#2A2A2A) đứng cạnh nhau, CÙNG kiểu
    # tóc `trocs`, và người xem không phân biệt được ai đang nói — mà đuôi bong bóng chỉ về
    # người nói chính là thứ thay cho nhãn tên ở bộ này.
    #
    # Đo khoảng cách trên cả 18 kênh (270 cặp): trung vị 261, cặp tệ nhất 48. Hai đầu tách hẳn
    # nhau, nên sàn đặt được. Chọn 110: nó chữa 11 cặp tệ nhất và không đụng tới phần còn lại.
    #
    # Và một ràng buộc thứ hai: hai vai CÙNG KIỂU TÓC phải cách nhau xa hơn (160), vì lúc ấy
    # màu áo là dấu hiệu DUY NHẤT còn lại. `kieuToc` vốn cho phép trùng 2 người — đúng khi màu
    # đã tách, sai khi màu cũng gần. §17.2: một thứ chịu hai ràng buộc.
    SAN, SAN_TOC = 110.0, 160.0
    kho_mau = list(dict.fromkeys(MAU.values()))
    xong: list = []
    for d in tho:
        def _du(c, dd=d):
            for e in xong:
                s = SAN_TOC if e["kieuToc"] == dd["kieuToc"] else SAN
                if _kc(c, e["ao"]) < s:
                    return False
            return True
        if not _du(d["ao"]):
            # Không lấy "màu chưa ai dùng" (bản cũ) mà lấy màu XA NHẤT khỏi mọi màu đã dùng —
            # "chưa dùng" không bảo đảm nhìn ra khác, và đó đúng là cách lỗi này lọt qua.
            tot = max(kho_mau, key=lambda c: (_du(c), min((_kc(c, e["ao"]) for e in xong),
                                                          default=999)))
            d["ao"] = tot
        xong.append(d)
    return tho


def main():
    ra = {}
    for ma in GU.VAI:
        ra[ma] = mot_kenh(ma, GU.dan_vai_khai(ma))
    io.open(RA, "w", encoding="utf-8").write(json.dumps(ra, ensure_ascii=False, indent=1))
    import collections
    xau = 0
    for ma, ds in ra.items():
        import itertools
        gan = min((_kc(x["ao"], y["ao"]) for x, y in itertools.combinations(ds, 2)),
                  default=999)
        # Mỗi điều kiện in ĐÚNG lý do của nó. Bản đầu in khoảng cách màu cho MỌI ca trượt,
        # nên bốn kênh có màu hoàn toàn đạt (135–179 trên sàn 110) vẫn hiện ra như lỗi màu —
        # một dòng cảnh báo nói sai nguyên nhân dẫn người đọc đi sửa thứ không hỏng (§15.2).
        ao = collections.Counter(d["kieuAo"] for d in ds).most_common(1)[0]
        ly = []
        if gan < 110:
            ly.append(f"cặp áo gần nhất {gan:.0f} < sàn 110")
        if ao[1] > 2:
            ly.append(f"{ao[1]} người cùng kiểu áo '{ao[0]}'")
        if ly:
            xau += 1
            print(f"   ⚠ {ma}: " + " · ".join(ly))
    print(f"✅ {sum(len(v) for v in ra.values())} bộ đồ / {len(ra)} kênh · "
          f"{len(ra) - xau}/{len(ra)} kênh không ai mặc trùng ai")


if __name__ == "__main__":
    main()
