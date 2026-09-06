#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NỚI BẢNG CHỮ CỦA BỘ GIẢI THÍCH — bảng KHÔNG có con số  (6/9/2026)

── VÌ SAO TÁCH KHỎI `bang_mo_rong.py` ───────────────────────────────────────────────────────
Bộ kia xoay quanh MỘT bài toán: AI đề cử tên, con số phải sống sót qua một lượt đối chứng độc
lập. Bảy bảng ở đây **không có con số nào** — chúng là chủ đề và mô tả cảnh. Không có gì để
đối chứng, và cổng đối chứng chạy trên chúng chỉ tốn lượt gọi mà không chứng minh gì.
Hai bản chất khác nhau thì hai lệnh khác nhau (§10 — hai bộ, hai xưởng, đừng trộn).

── VÌ SAO CÁC BẢNG NÀY CẦN NỚI ──────────────────────────────────────────────────────────────
Đo ngày 6/9: bảy kênh cạn chủ đề ở tập 11–15, và cả bảy đều vì danh sách nằm TRONG hàm sinh
nên không bộ nới nào nhìn thấy. Không kênh nào cạn vì thế giới hết thứ để nói — cùng niche ấy,
`howloud` đi từ 31 lên 278 mục chỉ bằng cách nới bảng. Đây là lỗi PIPELINE, không phải lỗi
niche, và câu hỏi "có phải đổi kênh không" trả lời được bằng đúng số đo ấy.

── BỐN CỔNG (không có cổng đối chứng, vì không có số để đối chứng) ───────────────────────────
1. **dạng**   — mỗi trường đúng khuôn của bảng ấy (số chữ, cách mở đầu).
2. **không người / không chữ** ở mô tả cảnh — cùng lý do như kho nền: FLUX vẽ chữ ra ký tự
   loằng ngoằng, và nhân vật vector sẽ được dán lên khung.
3. **không viết nghịch** — FLUX không có negative prompt, `no clutter` đẻ ra đúng cái clutter.
4. **trùng** — danh từ chính chưa có trong bảng.

Biểu tượng do MÁY suy từ tên (`bang_mo_rong._bt`), không để AI chọn: đo ngày 6/9 thấy AI bốc
bừa từ danh sách đóng — sấm sét -> `vi_khuan`, đồng hồ báo thức -> `te_bao`.
"""
import argparse, io, json, os, re, sys, time

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
os.environ.setdefault("GT_KHONG_CF", "1")
import giai_thich as G
import phim_canh as PC
import bang_mo_rong as BM

MODEL = "openai/gpt-oss-120b"

# ── ĐẶC TẢ TỪNG BẢNG ═══════════════════════════════════════════════════════════════════════
# `truong` mô tả từng cột cho AI. `ve` = cột nào phải bọc `_ve(...)` khi ghi ra mã nguồn.
BANG = {
 "MOI_NGUOI": dict(
   kenh="whatif", bt=1, ve=None, cuoi=True,
   mo="things that would happen if every person on Earth did one ordinary thing at once",
   truong=[("viec", 'the event, 3 to 7 words, always starting "everyone". '
                    'Example shape: "everyone flushed at once"'),
           ("canh", "one flat-cartoon scene showing that moment from a distance, "
                    "12 to 22 words, a place and what fills it")]),
 "SONG_SOT": dict(
   kenh="survive", bt=None, ve=None,
   mo="hard situations a modern person would struggle to live through",
   truong=[("de", 'the challenge, 3 to 7 words, starting "a". '
                  'Example shape: "a week without fire"'),
           ("canh", "one flat-cartoon landscape for it, 10 to 20 words, empty of people")]),
 "DI_DAU": dict(
   kenh="wheregoes", bt=1, ve=2, cuoi=False,
   mo="everyday things people throw away or send off, whose journey afterwards is worth seeing",
   truong=[("vat", 'the thing, 3 to 7 words, starting "the". '
                   'Example shape: "the thing you put in recycling"')],
   ve_truong=[("chu", "the object itself, 5 to 12 words"),
              ("lam", "where it sits or what is happening to it, 5 to 12 words"),
              ("cam", "leave this an empty string"),
              ("xa", "the place behind it, 6 to 14 words"),
              ("gan", "what is on the ground right in front, 5 to 12 words"),
              ("sang", "the light and the colour mood, 5 to 12 words, no camera words")]),
 "LUAT_NGAM": dict(
   kenh="therules", bt=None, ve=1, cuoi=False,
   mo="ordinary places and objects that are quietly governed by a rule almost nobody has read",
   truong=[("noi", 'the place or thing, 2 to 6 words, starting "a", "an", "the" or "your". '
                   'Example shape: "your own driveway"')],
   ve_truong=[("chu", "the place itself, 5 to 12 words"),
              ("lam", "how it sits in the frame, 5 to 12 words"),
              ("cam", "leave this an empty string"),
              ("xa", "what is behind it, 6 to 14 words"),
              ("gan", "what is on the ground in front, 5 to 12 words"),
              ("sang", "the light and colour mood, 5 to 12 words, no camera words")]),
 # ── VÌ SAO HAI BẢNG NÀY KHÔNG CẦN CỔNG ĐỐI CHỨNG  (đo 6/9/2026) ────────────────────────────
 # Em từng gộp bốn kênh "tiền/khảo sát" lại và nói cả bốn cần bảng số công bố. Đọc lại dữ liệu
 # thì hai trong bốn KHÔNG hề khẳng định điều gì về thế giới:
 #   THOI_QUEN — giá nằm TRONG TÊN: *"a $6 coffee every morning"*. Video không nói "cà phê giá
 #     6 đô"; nó nói "GIẢ SỬ bạn mua một ly 6 đô mỗi sáng" rồi tính lãi kép. Con số là TIỀN ĐỀ,
 #     không phải khẳng định — không có gì để đối chứng, và bắt nó qua cổng đối chứng là hỏi
 #     thế giới một câu mà video không hề đặt ra.
 #   MOC_LON  — "một triệu so với một tỉ" là toán thuần tuý. Không có sự kiện nào cả.
 # Cái phải giữ ở đây là NHẤT QUÁN NỘI BỘ: số trong tên phải bằng đúng cột số. Lệch một chữ là
 # màn hình nói một đằng, lời nói một nẻo — thứ tệ hơn một con số sai nguồn.
 "THOI_QUEN": dict(
   kenh="realcost", bt=3, ve=None, cuoi=True, so=1, khop_ten=True,
   so_don="dollars", so_bien=(0.5, 500), so_sai=None,
   nhom=("coffee, tea and drinks", "lunch and takeaway", "subscriptions and apps",
         "transport and parking", "snacks and convenience stores", "phone and internet",
         "gym, hobbies and classes", "cigarettes, vapes and lottery",
         "delivery fees and tips", "small household buys"),
   mo="everyday spending habits an American repeats, each written with its price inside the name",
   truong=[("viec", 'the habit WITH its price inside, 4 to 8 words, starting "a". '
                    'Example shape: "a $6 coffee every morning", "a $15 streaming subscription"'),
           ("gia", "just the dollar amount from that name, a plain number, no $ and no commas"),
           ("lan", "how many times a year it happens: 365 daily, 260 workdays, 52 weekly, "
                   "12 monthly, 4 quarterly")]),
 "MOC_LON": dict(
   kenh="howmuch", bt=5, ve=None, cuoi=True, cot_ten=4,   # bản sắc = ĐƠN VỊ, xem `_ic`
   nhom=("time", "money", "distance", "counting objects", "food and drink",
         "steps and movement", "paper and writing", "data and files",
         "people and crowds", "nature and small things"),
   mo="units where the gap between a million and a billion of them becomes shocking",
   truong=[("nho", 'the smaller amount in words, 2 to 3 words. Example: "a million"'),
           ("nho_v", "that amount as a plain number, no commas"),
           ("lon", 'the bigger amount in words, 2 to 3 words. Example: "a billion"'),
           ("lon_v", "that amount as a plain number, no commas"),
           ("don", "the unit being counted, 1 to 3 words. Example: \"seconds\", \"dollar bills\"")]),
 "TOC_DO": dict(
   kenh="speedof", bt=None, ve=2, cuoi=False, so=1,
   # Bảng DUY NHẤT ở đây có con số, nên nó phải qua **cổng đối chứng** của `bang_mo_rong`:
   # tốc độ là hằng số vật lý, hỏi lại bằng một lượt gọi độc lập thì con số thật trùng, con số
   # bịa thì không. Không có ngoại lệ cho "chỉ một cột số" — luật nền là AI không bao giờ cấp
   # một con số cho sản phẩm giao đi.
   so_don="miles per hour",
   so_bien=(0.0001, 700_000_000), so_sai=("nhan", 1.35),
   so_lanh="How fast is {x}, in miles per hour? Give only the number.",
   mo="things whose speed a US viewer can feel, from the very slow to the extremely fast",
   truong=[("vat", 'the thing, 2 to 6 words, starting "a", "an" or "the". '
                   'Example shape: "a sneeze", "the fastest lift in a skyscraper"'),
           ("mph", "its speed in miles per hour, a plain number, no units and no commas")],
   ve_truong=[("chu", "the thing itself in motion, 5 to 12 words"),
              ("lam", "the exact instant of that motion, 5 to 12 words"),
              ("cam", "leave this an empty string"),
              ("xa", "the place behind it, 6 to 14 words"),
              ("gan", "what is in front along the ground, 5 to 12 words"),
              ("sang", "the light and colour mood, 5 to 12 words, no camera words")]),
 "MOT_NGAY": dict(
   kenh="dayinlife", bt=None, ve=None,
   mo="jobs and roles from history and from today whose working day is worth seeing",
   truong=[("ai", 'the person, 2 to 5 words, starting "a" or "an". '
                  'Example shape: "a Roman soldier", "an air traffic controller"'),
           ("canh", "their workplace as a flat-cartoon scene, 12 to 22 words, no people in it"),
           ("do", "what they wear and carry, 6 to 14 words"),
           ("sang", "the light in that place, 6 to 14 words, no camera or lens words")]),
}

# Nhóm chủ đề xoay vòng. Không có nó thì tới mẻ thứ hai mô hình quay lại đúng cái hồ nó vừa
# múc — đo được ở `bang_mo_rong`: 48/50 dòng trùng, và trần thật của một bảng là trần của LỜI
# HỎI chứ không phải của thế giới.
NHOM = {
 "TOC_DO": ("animals on land", "birds and things that fly", "fish and sea creatures",
            "cars, bikes and trains", "aircraft and rockets", "sport and human bodies",
            "weather and natural forces", "machines and tools",
            "things inside the human body", "space and the planets"),
 "DI_DAU": ("recycling and rubbish", "water and drains", "post and parcels",
            "food waste and compost", "old electronics", "clothes and textiles",
            "cars and scrap metal", "batteries and chemicals", "paper and packaging",
            "sewage and treatment"),
 "LUAT_NGAM": ("the home and garden", "driving and parking", "shops and receipts",
               "work and contracts", "renting and property", "food and hygiene",
               "money and banking", "travel and airports", "internet and data",
               "public space and noise"),
 "SONG_SOT": ("extreme cold and ice", "deserts and heat", "open water and the sea",
              "forests and jungle", "mountains and high altitude", "caves and the underground",
              "historical eras before machines", "storms and natural disasters",
              "isolation with no people", "life with one resource missing"),
 "MOI_NGUOI": ("water and plumbing", "electricity and the grid", "roads and vehicles",
               "food and farming", "money and banking", "phones and the internet",
               "rubbish and recycling", "walking, jumping and crowds",
               "sound and shouting", "sleep and daily routine"),
 "MOT_NGAY": ("the ancient world", "the middle ages", "medicine and hospitals",
              "transport and travel", "food and restaurants", "emergency services",
              "science and laboratories", "entertainment and sport",
              "trades and workshops", "farming, sea and sky"),
}

LENH = """You write rows for a reference table used by an animated explainer channel.

Return ONE JSON array and nothing else. Each element is an object with exactly these keys:
{khoa}

Rules for every row:
{luat}
- Scene fields describe a PLACE ONLY. No people, no crowds, no hands, no silhouettes.
- Scene fields contain NO writing: no signs, labels, posters, screens, numbers or letters.
- Never write that something is absent. Write only what IS there.
- Every row must be clearly DIFFERENT from the others and from this list:
{co}"""

# ── DANH TỪ CHÍNH: BỎ ĐƠN VỊ THỜI GIAN TRƯỚC  (đo 6/9/2026) ─────────────────────────────────
# `BM._dau` lấy từ-không-phải-hư-từ ĐẦU TIÊN. Với bảng này thì tựa viết là *"a day in the Ice
# Age"* · *"a week without fire"* · *"a night in the desert"* — nên nó trả về `day`, `week`,
# `night`, và **31/32 dòng mới bị chấm là trùng** trong khi cả 31 là nơi chốn khác nhau.
# Cùng họ §15.21: *đầu ngữ ĐO LƯỜNG — chủ thể nằm SAU giới từ*. Ở đó là `odds of X`, ở đây là
# `a day in X`. Bỏ đơn vị thời gian rồi mới lấy danh từ chính.
# Cùng bẫy, lần thứ hai trong một buổi: `MOI_NGUOI` bắt mọi tựa mở bằng "everyone", nên danh
# từ chính của CẢ BẢNG là `everyone` và mẻ nào cũng 29/31 "trùng". Quy luật chung: **từ mà
# ĐỀ BÀI BẮT PHẢI CÓ thì không mang bản sắc** — nó là khuôn, không phải nội dung. Nhận ra quy
# luật sinh ra ngoại lệ, đừng liệt kê từng ngoại lệ (§13.9).
_THOI = {"day", "week", "night", "month", "year", "hour", "minute", "morning", "evening",
         "afternoon", "season", "weekend", "decade", "moment",
         "everyone", "everybody", "everything", "world", "people"}


_KHUON = {"a", "an", "the", "of", "in", "on", "at", "with", "and", "to", "from", "one",
          "single", "full", "its", "without", "once", "same", "time", "simultaneously",
          "all", "every", "their", "his", "her"}


def _dau_thuc(s: str, cuoi: bool = False) -> str:
    """Từ mang BẢN SẮC của một dòng.

    `cuoi=True` lấy từ CUỐI thay vì từ đầu. Vì sao cần cả hai (đo 6/9): `SONG_SOT` viết
    *"a week without fire"* — bản sắc ở từ đầu sau khi bỏ đơn vị thời gian (`fire`). `MOI_NGUOI`
    viết *"everyone turned on a light at once"* — bản sắc ở **tân ngữ** (`light`), còn động từ
    thì *"turned on a light"* và *"turned off the tap"* cùng cho `turned`, và cả bảng đọc ra
    trùng nhau: đo được 28/32 dòng bị loại oan mẻ nào cũng vậy.
    Không có một phép lấy nào đúng cho mọi bảng — khuôn câu khác nhau thì chỗ đặt bản sắc khác
    nhau. Nên nó là một lựa chọn KHAI trong đặc tả bảng, không phải một hằng số chung."""
    tu = [w for w in re.findall(r"[a-z]+", s.lower())
          if w not in _KHUON and w not in _THOI]
    if not tu:
        return BM._dau(s)
    return tu[-1] if cuoi else tu[0]


def _don(x: str) -> str:
    """Chuẩn hoá một trường. Gạch nối U+2011 và nháy cong lọt vào mã nguồn thì đọc lên vẫn
    bình thường mà `grep`/so chuỗi thì trượt — đã bắt được ở kho nền, và lại lọt vào đây
    (`a mass‑casualty triage nurse`). Sửa ở CHỖ GHI, đừng đi sửa mọi chỗ đọc."""
    x = (x.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
          .replace("\u2019", "'").replace("\u2018", "'"))
    return " ".join(x.split()).strip().rstrip(".")


NGUOI = re.compile(r"\b(people|person|man|woman|men|women|child|children|kid|worker|staff|"
                   r"customer|figure|silhouette|hand|face|someone|passenger|player)s?\b", re.I)
CHU = re.compile(r"\b(sign|signage|label|poster|banner|billboard|text|letter|word|number|"
                 r"logo|writing|screen|monitor|display|notice|chart|map|menu)s?\b", re.I)
NGHICH = re.compile(r"\b(no|without|not|empty of|free of|devoid)\b", re.I)


def _mang(t):
    i = t.find("[")
    if i < 0:
        return []
    d = 0
    for j in range(i, len(t)):
        if t[j] == "[":
            d += 1
        elif t[j] == "]":
            d -= 1
            if d == 0:
                try:
                    return [x for x in json.loads(t[i:j + 1]) if isinstance(x, dict)]
                except Exception:
                    return []
    return []


def mot_bang(ten, muc_tieu, khoa, mo_moi=30):
    dt = BANG[ten]
    cu = list(getattr(G, ten))
    _c = dt.get("cuoi", False)
    # ── CỘT MANG BẢN SẮC KHÔNG PHẢI LÚC NÀO CŨNG LÀ CỘT ĐẦU  (đo 6/9/2026) ────────────────
    # `MOC_LON` viết ('a million', 1e6, 'a billion', 1e9, 'seconds', 'tien'). Cột đầu là ĐỘ LỚN
    # — mọi dòng đều "a million"/"a thousand", nên khử trùng theo nó loại 31/31 dòng mới.
    # Bản sắc ở đây là ĐƠN VỊ ĐƯỢC ĐẾM ("seconds" · "dollar bills") — thứ người xem thấy khác
    # nhau giữa hai tập. Cùng quy luật đã trả giá bốn lần hôm nay (*từ mà khuôn câu bắt phải có
    # thì không mang bản sắc*), chỉ khác là ở đây nó chiếm nguyên một CỘT.
    _ic = dt.get("cot_ten", 0)
    co = {_dau_thuc(str(r[_ic]), _c) for r in cu}
    them = []
    print(f"\n══ {ten} ({dt['kenh']})  {len(cu)} -> {muc_tieu} mục")
    # Hai ngân sách KHÁC BẢN CHẤT, hai bộ đếm (§14.8): `lan` đếm mẻ đã xin, `hong` đếm lượt
    # gọi hỏng liên tiếp. Bản đầu dừng cả bảng ngay khi MỘT lượt gọi trả rỗng — mà lượt gọi
    # hỏng là chuyện mạng, không phải bằng chứng rằng bảng đã hết chỗ để nới.
    lan = hong = 0
    while len(cu) + len(them) < muc_tieu and lan < 60 and hong < 4:
        lan += 1
        _tr = list(dt["truong"]) + list(dt.get("ve_truong") or [])
        khoas = "\n".join(f'  "{k}": {m}' for k, m in _tr)
        luat = "\n".join(f"- {m}" for _k, m in _tr)
        sysp = LENH.format(khoa=khoas, luat=luat, co="  " + ", ".join(sorted(co)))
        # Nhóm khai TRONG đặc tả bảng đứng trước bảng toàn cục — bảng mới thì khai tại chỗ,
        # không phải sửa hai nơi. Thiếu cả hai thì `KeyError`, và đó là điều ĐÚNG: một bảng
        # không có nhóm chủ đề sẽ lặp ngay từ mẻ thứ hai (đo được 48/50 dòng trùng).
        _nh = dt.get("nhom") or NHOM[ten]
        nh = _nh[(len(cu) + len(them)) % len(_nh)]
        t = PC._goi(sysp, f"Give {mo_moi} rows: {dt['mo']}. "
                          f"Draw them all from this area: {nh}.", khoa)
        tho = _mang(t)
        if not tho:
            hong += 1
            print(f"      ↻ lượt gọi hỏng ({hong}/4) — thử nhóm khác"); continue
        hong = 0
        vi, nhan = {}, 0
        for r in tho:
            gt = [_don(str(r.get(k) or "")) for k, _m in dt["truong"]]
            vt = [_don(str(r.get(k) or "")) for k, _m in (dt.get("ve_truong") or [])]
            # Trường `cam` (biểu cảm) được phép rỗng — cảnh không có người thì không có biểu cảm.
            if dt.get("ve_truong") and not all(v for k, v in zip(
                    [x[0] for x in dt["ve_truong"]], vt) if k != "cam"):
                vi["thiếu trường cảnh"] = vi.get("thiếu trường cảnh", 0) + 1; continue
            if not all(gt):
                vi["thiếu trường"] = vi.get("thiếu trường", 0) + 1; continue
            canh = " ".join(str(x) for x in gt[1:]) + " " + " ".join(vt)
            if NGUOI.search(canh):
                vi["có người"] = vi.get("có người", 0) + 1; continue
            if CHU.search(canh):
                vi["có chữ/biển"] = vi.get("có chữ/biển", 0) + 1; continue
            if NGHICH.search(canh):
                vi["viết nghịch"] = vi.get("viết nghịch", 0) + 1; continue
            if dt.get("khop_ten"):
                # Số trong tên phải BẰNG cột số. Không phải chuyện thẩm mỹ: bộ sinh in tên ra
                # tiêu đề và in cột số ra bảng, nên lệch nhau là màn hình cãi lời nói.
                import re as _re
                _t = _re.search(r"\$\s*([\d.,]+)", gt[0])
                _c = _re.sub(r"[^\d.]", "", str(gt[dt["so"]]) or "")
                if not _t or _t.group(1).replace(",", "") != _c:
                    vi["số trong tên lệch cột số"] = vi.get("số trong tên lệch cột số", 0) + 1
                    continue
            if dt.get("so") is not None:
                try:
                    _v = float(re.sub(r"[^\d.\-]", "", gt[dt["so"]]) or 0)
                except Exception:
                    _v = 0.0
                if not (dt["so_bien"][0] <= _v <= dt["so_bien"][1]):
                    vi["ngoài biên vật lý"] = vi.get("ngoài biên vật lý", 0) + 1; continue
                # Ghi ra SỐ, không phải chuỗi. Bộ sinh `sinh_speedof` chia thẳng `kmh /
                # DI_BO_MPH`, nên một chuỗi làm nó nổ `TypeError` ngay lúc `khong_gian()` chạy —
                # tức lỗi hiện ở một hàm cách đó ba tầng và không nhắc gì tới bảng. Kiểu dữ
                # liệu là một phần của hợp đồng bảng, y như số cột (§16.6).
                gt[dt["so"]] = int(_v) if float(_v).is_integer() else _v
            w = len(gt[0].split())
            if not (2 <= w <= 8):
                vi["dạng tên"] = vi.get("dạng tên", 0) + 1; continue
            d = _dau_thuc(str(gt[_ic]), _c)
            if d in co:
                vi["trùng"] = vi.get("trùng", 0) + 1; continue
            co.add(d)
            if dt["bt"] is not None:
                gt.insert(dt["bt"], BM._bt(gt[0], "nguoi"))
            if dt.get("ve") is not None:
                # Ghi ra dưới dạng ĐÁNH DẤU, `noi_van` sẽ đổi thành lời gọi `_ve(...)` thật.
                # Không tự ghép chuỗi ở đây: `_ve` là nơi DUY NHẤT biết cách ghép sáu tầng, và
                # nó đã đổi cách ghép một lần (bỏ nhãn "background:" kiểu ảnh chụp, §12.6).
                gt.insert(dt["ve"], ["_VE"] + vt)
            them.append(tuple(gt)); nhan += 1
        # ── CỔNG ĐỐI CHỨNG, chỉ cho bảng CÓ CỘT SỐ ────────────────────────────────────
        # Chạy sau vòng lọc để hỏi một lượt cho cả mẻ (song song), thay vì một lượt mỗi dòng.
        # Có cột SỐ không có nghĩa là phải đối chứng. `THOI_QUEN` có cột giá, nhưng giá ấy là
        # TIỀN ĐỀ video tự nêu ("giả sử một ly 6 đô"), không phải khẳng định về thế giới — hỏi
        # thế giới một câu mà video không đặt ra thì câu trả lời không dùng vào đâu được.
        # Điều kiện đúng là "bảng có khai CÂU HỎI LẠNH không", không phải "có cột số không".
        if dt.get("so_lanh") and them:
            _moi = them[len(them) - nhan:]
            hai = BM.doi_chung([r[0] for r in _moi], dt["so_lanh"], khoa)
            giu, an = [], 0
            for r, s2 in zip(_moi, hai):
                try:
                    v = float(re.sub(r"[^\d.\-]", "", str(r[dt["so"]])) or 0)
                except Exception:
                    v = 0.0
                if BM._lech(v, s2, dt["so_sai"]):
                    giu.append(r)
                else:
                    an += 1
                    co.discard(_dau_thuc(r[0], _c))
            them = them[:len(them) - nhan] + giu
            nhan = len(giu)
            if an:
                print(f"      đối chứng loại {an} dòng (số không khớp lượt hỏi độc lập)")
        print(f"   xin {len(tho)} · NHẬN {nhan}  (tổng {len(cu)+len(them)})"
              + (f"  [loại: {' · '.join(f'{k} {v}' for k,v in sorted(vi.items()))}]" if vi else ""))
        if nhan == 0:
            hong += 1
            if hong >= 4:
                print("      ⛔ bốn mẻ liền không nhận được gì — bảng đã tới hạn"); break
    return them


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bang", default="")
    ap.add_argument("--den", type=int, default=300)
    ap.add_argument("--ra", default=os.path.join(GOC, "bang_van_moi.json"))
    a = ap.parse_args()
    khoa = PC._khoa_groq()
    if not khoa:
        raise RuntimeError("không có khoá Groq")
    print(f"🔑 {len(khoa)} khoá Groq · model {MODEL}")
    ds = [x.strip() for x in a.bang.split(",") if x.strip()] or list(BANG)
    ket = {}
    for b in ds:
        ket[b] = mot_bang(b, a.den, khoa)
        io.open(a.ra, "w", encoding="utf-8").write(json.dumps(ket, ensure_ascii=False, indent=1))
    print(f"\n✅ {sum(len(v) for v in ket.values())} dòng mới -> {a.ra}")
    print("   ĐỌC TAY một mẫu trước khi nối (§13.20).")


if __name__ == "__main__":
    main()
