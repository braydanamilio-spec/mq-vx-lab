#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RÚT 10 KÊNH TỪ GÓI 15 GIÂY -> `kho_15s.json`  (1/9/2026)

Anh gửi `GROCK PROMPT VIDEOS 15S`: 10 tệp × 2.500 prompt. Khác hẳn gói 6 giây trước đó —
gói này có **dòng thời gian bốn nhịp**, mỗi nhịp một hành động kèm một câu thoại:

    0-3s:   Derek stands in the kitchen holding a smoking pan.
            Derek: "I made breakfast!"
    3-7s:   Sara walks in, waves the smoke away.
            Sara: "That's not breakfast. That's a fire drill."
    7-11s:  Max appears and takes a photo.
            Max: "This is going on the family group chat."
    11-15s: Nana Bea walks by without stopping: "I've seen worse... from him."

Bốn nhịp × 4 giây = 15 giây, đúng độ dài anh muốn. Và mỗi nhịp có HÀNH ĐỘNG riêng — đó là thứ
engine người que dùng được mà engine truyện tranh thì không: `StickAnim` có bảy tư thế cộng lớp
`live()` chạy trên chín khớp, nên "walks in", "takes a photo", "walks by" diễn được.

Rút ra: dàn vai (tên · tuổi · giới · màu áo quần) · bốn nhịp (giây · hành động · ai nói · lời).
"""
import io
import json
import os
import re

GOC = os.path.dirname(os.path.abspath(__file__))
NGUON = os.path.expanduser("~/Downloads/GROCK PROMPT VIDEOS 15S")
RA = os.path.join(GOC, "kho_15s.json")

MAU = {
    "gray": "#8C9095", "grey": "#8C9095", "blue": "#3A5C93", "light blue": "#7FA8D4",
    "navy": "#22375C", "red": "#C4453A", "green": "#3E8F5E", "light green": "#7FBF8F",
    "teal": "#2F7D8A", "yellow": "#E8B93C", "orange": "#D9793C", "purple": "#6B4A93",
    "lavender": "#9B87C4", "pink": "#D98BA6", "coral": "#E0715E", "white": "#F1EEE7",
    "black": "#2A2A2E", "brown": "#7A5638", "khaki": "#C2A778", "beige": "#D8C7A9",
    "cream": "#EDE3CE", "maroon": "#7B3B3B", "olive": "#6E7A46", "mint": "#8FC4A8",
    # 1/9 — "dark jeans" và "light cardigan" rất hay gặp trong gói. Trước đây "dark" không nằm
    # trong bảng nên rơi về màu dự phòng băm từ tên: quần bò sẫm ra đỏ gạch, nhìn hệt đùi trần.
    # Đây không phải màu thật mà là ĐỘ SÁNG, nhưng đoán một sắc trung tính vẫn đúng hơn nhiều
    # so với bốc một màu ngẫu nhiên.
    "dark": "#2F3540", "light": "#DDE3E8", "dark blue": "#22375C", "light gray": "#C3C8CD",
    "dark gray": "#4A5058", "dark grey": "#4A5058", "light grey": "#C3C8CD",
    "plaid": "#9C5346", "floral": "#D98BA6", "denim blue": "#4A6A96",
    "blonde": "#D9B978", "gold": "#C9A24B", "silver": "#B9BDC2", "denim": "#4A6A96",
}
_TREN = r"(t-shirt|shirt|top|sweater|hoodie|cardigan|polo|blouse|jacket|vest|sweatshirt|dress)"
_DUOI = r"(jeans|pants|shorts|leggings|skirt|trousers|slacks)"


# ══ NÉT RIÊNG TỪNG VAI — GÓI ĐÃ VIẾT SẴN, CHỈ VIỆC ĐỌC ═══════════════════════════════════
# 1/9 — anh gửi ảnh ba người que trên sa mạc: cùng một ngôn ngữ nét, nhưng người tóc dài xoã,
# người tóc bù, người hói; người đeo giỏ, người bế con, người cầm giáo. Rồi: *"nhân vật ko phải
# giống hết, đa nhân vật và đa dạng, có nét đặc trưng."*
#
# Mà bản khoá nhân vật của gói ĐÃ tả từng nét ấy cho từng vai — "short curly gray hair, purple
# glasses, floral blouse", "long black hair in a sleek ponytail", "messy spiky brown hair".
# Tôi chỉ đang đọc lấy hai màu áo/quần rồi vứt phần còn lại. Nên mười kênh × năm vai = năm mươi
# người khác nhau trên giấy, ra hình thành một người lặp lại năm mươi lần.
KIEU_TOC = [
    ("troc",      r"\b(bald|shaved head|no hair)\b"),
    ("duoi_ngua", r"\bponytail|pony tail|high bun|top knot\b"),
    ("bum",       r"\b(bun|updo|braid|braids|wrapped in a bun)\b"),
    ("xoan",      r"\b(curly|curls|afro|coily|kinky)\b"),
    ("bu",        r"\b(messy|spiky|shaggy|unkempt|tousled)\b"),
    ("song",      r"\b(wavy|waves)\b"),
    ("dai",       r"\b(long hair|long [a-z]+ hair|shoulder-length|shoulder length|past her shoulders)\b"),
    ("ngan",      r"\b(short|buzz|cropped|neatly combed|crew cut)\b"),
]
MAU_TOC = {"black": "#241F1D", "dark brown": "#3B2A20", "brown": "#5A3E28", "auburn": "#7A3B23",
           "red": "#9C4A2A", "blonde": "#D9B978", "blond": "#D9B978", "gray": "#9AA0A6",
           "grey": "#9AA0A6", "silver": "#C3C8CD", "white": "#E8E6E2", "ginger": "#C06A34"}


def _toc(mo: str) -> tuple:
    """(kiểu, màu). Kiểu dò theo THỨ TỰ CỤ THỂ TRƯỚC: "long black hair in a sleek ponytail" phải
    ra `duoi_ngua` chứ không phải `dai` — đuôi ngựa là nét nhận dạng, "dài" thì ai cũng có."""
    kieu = next((k for k, rx in KIEU_TOC if re.search(rx, mo, re.I)), "ngan")
    mau = ""
    m = re.search(r"([a-z]+(?:\s+[a-z]+)?)\s+hair", mo)
    if m:
        for tu in (m.group(1), *reversed(m.group(1).split())):
            if tu in MAU_TOC:
                mau = MAU_TOC[tu]; break
    return kieu, mau or "#3B2A20"


# Phụ kiện: mỗi cái là một nét vẽ RIÊNG, đủ để nhận ra vai từ xa mà không cần nhìn mặt.
PHU_KIEN = [
    ("kinh",   r"\bglasses|spectacles|eyeglasses\b"),
    ("rau",    r"\bmustache|moustache|beard|goatee\b"),
    ("mu",     r"\b(cap|baseball hat|beanie|hat)\b"),
    ("khan",   r"\b(shawl|scarf|headscarf|hijab|dupatta)\b"),
    ("day_deo", r"\bsuspenders|braces\b"),
    ("tap_de", r"\bapron\b"),
    ("hoodie", r"\bhoodie|sweatshirt\b"),
    ("vay",    r"\b(dress|skirt)\b"),
]


def _mau(mo: str, dau: str) -> str:
    """Màu của món đồ: quét NGƯỢC vài chữ đứng trước tên món, lấy màu gần nhất.

    1/9 — bản trước bắt đúng hai chữ liền trước bằng `([a-z]+(\\s+[a-z]+)?)`. Gặp "light blue
    button-up shirt" thì dấu gạch nối cắt cụm: `[a-z]+` chỉ với tới chữ "up", không phải màu,
    và hàm trả rỗng -> rơi về xám mặc định. Ba trong năm vai của kênh NGUYEN dính lỗi này, nên
    cả nhà mặc xám giống hệt nhau — đúng cái anh nói "nhân vật giống hết".

    Nay tách chữ bằng mọi ký tự không phải chữ cái (gạch nối, dấu phẩy đều là ranh giới) rồi
    dò ngược tối đa bốn chữ. Thử cụm hai chữ trước ("light blue"), vì "light" một mình không
    phải màu mà "light blue" thì phải."""
    for m in re.finditer(dau, mo):
        tu = re.findall(r"[a-z]+", mo[max(0, m.start() - 40):m.start()])[-4:]
        for i in range(len(tu) - 1, -1, -1):
            doi = " ".join(tu[i - 1:i + 1]) if i else ""
            if doi in MAU:
                return MAU[doi]
            if tu[i] in MAU:
                return MAU[tu[i]]
    return ""


def _mau_rieng(ten: str, lech: int) -> str:
    """Màu dự phòng RIÊNG cho từng vai, khi gói không ghi màu ("soft floral blouse").

    Không dùng chung một mã xám: hai vai cùng rơi về dự phòng là hai vai mặc y hệt nhau, và ở
    nét que thì màu áo gánh phần lớn việc phân biệt. Băm từ tên nên cùng một vai luôn ra cùng
    một màu qua mọi tập — nhất quán là điều kiện của "khoá nhân vật" mà gói đòi."""
    bang = ["#4E7C9E", "#B4614B", "#5E8C5A", "#8E6FA8", "#C08A3E", "#3F7F78",
            "#A8556E", "#6C7A8C", "#7A6A4E", "#8C4F4F"]
    return bang[(sum(ord(c) for c in ten) + lech) % len(bang)]


# ══ NƠI CHỐN — ĐỌC TỪ KỊCH BẢN, KHÔNG ĐOÁN ═══════════════════════════════════════════════
# 1/9 — anh: *"bối cảnh phải đúng, thay đổi đúng như trong prompt kịch bản 15s."*
#
# Trước đây `kich_que.py` dò nơi chốn bằng regex trên 11 cảnh có sẵn của `SceneBG`
# (home/office/street/bank/store/city/park/hospital/lab/gym). Đếm trong gói thật:
#   couch 1863 · kitchen 1149 · living room 700 · laundry 700 · hallway 313 · school 301
#   bedroom 200 · yard 50 · street 50 · store 50 · bathroom 50
# Bốn nơi hay gặp nhất — kitchen, laundry, hallway, bedroom — KHÔNG CÓ trong 11 cảnh ấy, nên
# chúng rơi hết về "home". Đó là vì sao mọi tập đều diễn ở một phòng khách.
#
# Và nơi chốn thuộc về CẢ TẬP, không thuộc từng nhịp: gói viết "Tyler stands in the kitchen"
# ở nhịp đầu rồi ba nhịp sau là người khác bước vào CÙNG căn bếp ấy. Dò lại từng nhịp thì ba
# nhịp sau không thấy từ khoá nào và nhảy về mặc định — nền nhấp nháy giữa các nhịp.
NOI = [
    ("bep",        r"\b(kitchen|stove|oven|pan|fridge|refrigerator|counter|dishes|sink|cooking|burn\w*|microwave)\b"),
    ("giat",       r"\b(laundry|washer|dryer|washing machine|hamper|folding|socks)\b"),
    ("tam",        r"\b(bathroom|shower|toilet|mirror|towel|toothbrush)\b"),
    ("phong_ngu",  r"\b(bedroom|bed|pillow|blanket|alarm clock|closet)\b"),
    ("hanh_lang",  r"\b(hallway|hall|corridor|stairs|staircase|landing)\b"),
    ("truong",     r"\b(school|classroom|locker|teacher|homework desk|principal)\b"),
    ("cua_hang",   r"\b(store|grocery|aisle|checkout|cart|shopping)\b"),
    ("san_vuon",   r"\b(backyard|yard|garden|lawn|fence|grill|patio|porch)\b"),
    ("duong",      r"\b(street|sidewalk|driveway|mailbox|car|garage)\b"),
    ("an",         r"\b(dining|dinner table|dining table|at the table)\b"),
    ("phong_khach", r"\b(couch|sofa|living room|tv|television|remote|coffee table|rug)\b"),
]


def _noi(van: str) -> str:
    """Nơi chốn của CẢ TẬP: đếm phiếu trên toàn văn bản tập, lấy nơi nhiều phiếu nhất.

    Đếm phiếu chứ không lấy nơi khớp đầu tiên: một tập nói "kitchen" một lần rồi "couch" ba
    lần thì nó diễn ở phòng khách, dù bếp xuất hiện trước. Hoà phiếu thì thứ tự trong `NOI`
    quyết định — nơi cụ thể (bếp, phòng giặt) đứng trước nơi chung (phòng khách)."""
    d = [(sum(1 for _ in re.finditer(rx, van, re.I)), -i, ten) for i, (ten, rx) in enumerate(NOI)]
    n, _, ten = max(d)
    return ten if n else "phong_khach"


def _dan(than: str) -> dict:
    m = re.search(r"CHARACTER LOCK[^\n]*\n([\s\S]+?)\nKeep exact", than)
    if not m:
        return {}
    ra = {}
    for d in m.group(1).splitlines():
        mm = re.match(r"([A-Z][\w ]*?):\s*(.+)", d.strip())
        if not mm:
            continue
        ten, mo = mm.group(1).strip(), mm.group(2).lower()
        gt = re.search(r"(\d{1,2})-year-old", mo)
        so = int(gt.group(1)) if gt else 0
        tuoi = ("tre_con" if so and so <= 12 else "tre" if so and so <= 19
                else "gia" if (so >= 60 or "elderly" in mo) else "trung")
        gioi = "nam"
        if re.search(r"\b(woman|female|girl|mom|mother|grandma|nana|nani|dadi|abuela|gigi|ba noi|she|her)\b", mo):
            gioi = "nu"
        elif re.search(r"\b(blouse|dress|skirt|shawl|cardigan)\b", mo):
            gioi = "nu"
        # thú cưng: không tuổi VÀ không mặc gì
        thu = (not gt and "elderly" not in mo and not re.search(_TREN + "|" + _DUOI, mo))
        kieu_toc, mau_toc = _toc(mo)
        # CHIỀU CAO theo tuổi thật, không theo cảm giác. Bảng tăng trưởng: bé 9 tuổi ~135cm,
        # thiếu niên 15 ~168, người lớn ~172, người già co lại ~165. Chia cho 172 ra hệ số.
        # Trước đây mọi vai cùng một cỡ nên con cao bằng bố — lỗi đã ghi ở CLAUDE.md cho bộ
        # truyện tranh, nay tái diễn nguyên si ở bộ người que vì tôi không mang bài học sang.
        cao = (0.78 if so and so <= 10 else 0.86 if so and so <= 13 else
               0.94 if so and so <= 17 else 0.96 if gioi == "nu" else 1.0)
        if tuoi == "gia":
            cao *= 0.96
        ra[ten] = {"tuoi": tuoi, "gioi": gioi, "so_tuoi": so, "thu": thu,
                   # Thú cưng không mặc áo, nên màu của nó nằm rải trong câu ("chubby orange
                   # cat", "small gray-and-white dog"). Dò cả câu thay vì dò trước tên món đồ.
                   "ao": (next((MAU[w] for w in re.findall(r"[a-z]+", mo) if w in MAU), "#C58A4A")
                          if thu else _mau(mo, _TREN) or _mau_rieng(ten, 0)),
                   "quan": _mau(mo, _DUOI) or _mau_rieng(ten, 5),
                   "toc": kieu_toc, "mau_toc": mau_toc, "cao": round(cao, 3),
                   "pk": [k for k, rx in PHU_KIEN if re.search(rx, mo, re.I)],
                   "mo": mo[:160]}
    return ra


def main() -> int:
    if not os.path.isdir(NGUON):
        print(f"❌ không thấy {NGUON}")
        return 1
    kho = {}
    for t in sorted(os.listdir(NGUON)):
        if not t.endswith(".txt"):
            continue
        s = io.open(os.path.join(NGUON, t), encoding="utf-8", errors="ignore").read()
        m = re.search(r"NEW CHANNEL: (.+)|CHANNEL: (.+)", s)
        ten = (m.group(1) or m.group(2)).strip() if m else t[:24]
        de = re.sub(r"[^a-z0-9]", "", ten.lower())[:14] or t[:10]
        khoi = re.split(r"\n(\d{4}) — ", s)[1:]
        cap = list(zip(khoi[0::2], khoi[1::2]))
        if not cap:
            continue
        # DÀN VAI NẰM Ở ĐẦU TỆP, không nằm trong prompt. Bản đầu đọc từ `cap[0][1]` (thân
        # prompt 0001) nên `dan` rỗng, và vì lượt thoại chỉ được nhận khi `ai in dan`, cả
        # 25.000 prompt đều bị loại — ra 0 tập mà không lỗi nào báo.
        dan = _dan(s)
        vai = sorted(dan, key=len, reverse=True)
        tap = []
        for so, than in cap:
            mk = re.search(r"SCENE AND DIALOGUE[^\n]*\n([\s\S]+?)\n\s*DIRECTOR NOTE", than)
            if not mk:
                continue
            nhip = []
            for mm in re.finditer(r"(\d+)-(\d+)s:\s*([^\n]+)((?:\n(?!\d+-\d+s:|DIRECTOR)[^\n]+)*)",
                                  mk.group(1)):
                khoi_van = (mm.group(3) + "\n" + (mm.group(4) or "")).strip()
                # lời thoại: `Ten: "..."` ở bất kỳ đâu trong nhịp
                # AI NÓI = TÊN VAI CUỐI CÙNG xuất hiện TRƯỚC dấu nháy, không phải chữ ngay
                # trước dấu hai chấm. Nhịp thứ tư thường viết kiểu:
                #   "Nana Bea walks by without stopping: 'I've seen worse... from him.'"
                # -> chữ ngay trước dấu hai chấm là "stopping", nên bản đầu gán nhầm rồi loại
                # cả câu. Mất trọn nhịp CHỐT của mỗi tập — mà nhịp chốt là chỗ buồn cười nhất.
                loi = []
                for q in re.finditer(r'"([^"]+)"', khoi_van):
                    truoc = khoi_van[:q.start()]
                    ai = ""
                    vt = -1
                    for v in dan:
                        i = truoc.rfind(v)
                        if i > vt:
                            vt, ai = i, v
                    if ai:
                        loi.append([q.group(1).replace("\u2019", "'"), ai])
                hanh = re.sub(r'[A-Z][\w ]*?:\s*"[^"]+"', "", khoi_van)
                hanh = " ".join(hanh.split())[:140]
                # AI CÓ MẶT trong nhịp: người đang nói + mọi tên vai được nhắc trong hành
                # động. Gói viết rõ ai bước vào ("Megan waves the smoke away", "Papa Earl
                # walks past") — cả nhà đứng trong một căn bếp, không phải mỗi nhịp một người
                # đứng một mình. Bản trước vẽ đúng MỘT người mỗi nhịp nên mất hẳn cái vui của
                # phản ứng dây chuyền, thứ mà toàn bộ gói được viết ra để tạo.
                co = []
                for v in dan:
                    if v in khoi_van and v not in co:
                        co.append(v)
                for _c, ai in loi:
                    if ai not in co:
                        co.append(ai)
                nhip.append({"s": int(mm.group(1)), "e": int(mm.group(2)),
                             "hanh": hanh, "loi": loi, "co_mat": co})
            if len(nhip) >= 3 and sum(len(n["loi"]) for n in nhip) >= 2:
                # DÀN CỦA TẬP = hợp của mọi người xuất hiện ở bốn nhịp. Mỗi nhịp gói chỉ GỌI
                # TÊN một người — người đang diễn — nhưng cả nhà vẫn đứng trong căn phòng ấy
                # suốt mười lăm giây; nhịp sau người kia phản ứng ngay là bằng chứng. Dựng
                # đúng một người mỗi nhịp thì mất hẳn phản ứng dây chuyền.
                # Giữ thứ tự xuất hiện: người mở màn đứng chỗ tốt nhất.
                vt = []
                for x in nhip:
                    for a in x["co_mat"]:
                        if a not in vt:
                            vt.append(a)
                tap.append({"so": int(so), "ten": than.split("\n")[0].strip(),
                            "noi": _noi(mk.group(1)), "vai": vt[:4], "nhip": nhip})
        kho[de] = {"ten": ten, "dan": dan, "tap": tap}
        n_loi = sum(len(n["loi"]) for x in tap for n in x["nhip"])
        print(f"  {ten[:26]:28s} {len(tap):5d} tập · {n_loi} lượt thoại · "
              f"dàn {len([1 for v in dan.values() if not v['thu']])} người + "
              f"{len([1 for v in dan.values() if v['thu']])} thú")

    io.open(RA, "w", encoding="utf-8").write(json.dumps(kho, ensure_ascii=False))
    print(f"\n  ✅ {len(kho)} kênh · {sum(len(v['tap']) for v in kho.values())} tập -> kho_15s.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
