#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MỞ RỘNG BẢNG DỮ LIỆU CỦA BỘ GIẢI THÍCH  (6/9/2026)

── VÌ SAO TỆP NÀY TỒN TẠI ───────────────────────────────────────────────────────────────────
Đo `khong_gian()` cả 18 kênh: **826 chủ đề phân biệt cho cả bộ**, và `vi_tri_short` còn chia
đôi — nên short của `howlong` chỉ có **11** chủ đề. Kênh cạn nội dung ở tập ~13, không phải ở
tập thứ 1000. Nền đẹp, nhân vật đẹp, sản lượng cao đều vô nghĩa nếu tập 15 lặp tập 1.

Độ sâu của một kênh = **cỡ bảng dữ liệu nó rút**, không phải số kịch bản ai đó viết ra:

    kênh rút MỘT mục   (howlong, howloud, howhot…)  ->  độ sâu = n
    kênh rút MỘT CẶP   (whatweighs, smallest…)      ->  độ sâu = n(n−1)   (xem `_cap`)

22 mục cho 22 tập. **200 mục cho 200 tập — và 39.800 tập ở kênh rút cặp.**

── VÌ SAO KHÔNG ĐỂ AI VIẾT THẲNG CON SỐ ─────────────────────────────────────────────────────
Cả bộ giải thích được dựng trên đúng một luật: **mọi con số do Python tính từ hằng số có
nguồn, AI không bao giờ bịa ra một con số.** Đó là thứ tách kênh này khỏi hàng nghìn kênh
đọc-số-sai trên YouTube, và là thứ không lấy lại được sau khi mất.

Nên ở đây AI được giao đúng một việc: **đề cử TÊN của thứ đáng đo**. Con số nó kèm theo chỉ là
một ĐỀ NGHỊ, và phải sống sót qua bốn cổng dưới đây mới được vào bảng.

── BỐN CỔNG, VÀ VÌ SAO CỔNG THỨ TƯ MỚI LÀ CỔNG THẬT ─────────────────────────────────────────
1. **dạng**    — tên 2–7 chữ, mở bằng mạo từ, biểu tượng nằm trong 21 biểu tượng đang có.
2. **biên**    — giá trị nằm trong khoảng VẬT LÝ của thang ấy (dB không thể 1.100).
3. **trùng**   — danh từ chính chưa có trong bảng (không nhận "a chainsaw" hai lần).
4. **ĐỐI CHỨNG** — hỏi LẠI bằng một lượt gọi ĐỘC LẬP: khoá khác, `temperature 0`, và câu hỏi
   viết LẠNH ("what is the decibel level of X?") — không nhắc gì tới bảng, tới kênh, tới lượt
   hỏi trước. Chỉ giữ dòng nào hai lượt khớp nhau trong dung sai của thang.

Cổng 4 không biến AI thành nguồn. Nó chỉ loại **thứ AI bịa** — một con số bịa ra ở lượt một
gần như không bao giờ trùng với con số bịa ra ở lượt hai, trong khi một hằng số có thật thì
trùng. Đây là phép thử "hai nhân chứng kể cùng một chuyện", không phải phép thử đúng/sai.

Và vì thế **mọi dòng mới đều ghi lại xuất xứ** (`bang_nguon.json`: hai con số, độ lệch, model,
ngày). Không có dòng nào vào bảng mà không đọc lại được nó tới từ đâu — §13.1.

── ĐIỀU CHƯA ĐO ĐƯỢC, GHI RA THAY VÌ GIẤU ───────────────────────────────────────────────────
Hai lượt gọi cùng một họ model có thể cùng sai theo một cách (cùng dữ liệu huấn luyện). Cổng
này KHÔNG bắt được loại sai ấy. Nó bắt được thứ hay xảy ra hơn nhiều: bịa. Nên §13.20 vẫn phải
áp — **đọc tay một mẫu** trước khi nhận cả mẻ, và `--doc` in ra đúng mẫu để đọc.
"""
import argparse, io, json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

os.environ.setdefault("GT_KHONG_CF", "1")
GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
import giai_thich as G
import phim_canh as PC

MODEL = "openai/gpt-oss-120b"
BT_OK = {"ca_voi", "cay", "coc", "dien_thoai", "dong_ho", "giuong", "huou", "lua", "mat_trang",
         "mat_troi", "may_bay", "meo", "nguoi", "nguyen_tu", "nha", "te_bao", "tien",
         "trai_dat", "vi_khuan", "xe", "xe_buyt"}

# ══ ĐẶC TẢ TỪNG BẢNG ═════════════════════════════════════════════════════════════════════════
# `bien` là khoảng VẬT LÝ, không phải khoảng "đẹp": nó tồn tại để chặn thứ bịa, không phải để
# chọn thứ hay. `sai` là dung sai của cổng đối chứng, và mỗi con số dưới đây có lý do riêng —
# decibel là thang đo chuẩn hoá nên hai nguồn chênh nhau vài dB; còn xác suất thì mỗi nguồn
# một cách đếm, chênh nhau vài lần là bình thường, nên dung sai phải rộng hơn hẳn.
BANG = {
 "AM_THANH": dict(
    nhom=("the kitchen and household appliances", "power tools and workshops",
          "traffic, cars and motorbikes", "aircraft, trains and boats",
          "music, concerts and instruments", "animals and birds",
          "weather and natural sounds", "sport, crowds and stadiums",
          "the office, school and hospital", "guns, blasts and industry"),
    bt0="nguoi", don="decibels (dB SPL)", bien=(5, 200), sai=("nhan", 1.20), arity=3,
    mo="everyday and extreme things that make a measurable sound level",
    lanh="What is the typical sound level in decibels (dB SPL) of {x}?"),
 "NHIET_DO": dict(
    nhom=("cooking and the kitchen", "weather and climate", "the human body",
          "engines and machines", "space and the planets", "fire and industry",
          "ice, snow and the cold", "materials that melt or boil",
          "electronics and lighting", "extreme places on Earth"),
    bt0="lua", don="degrees Fahrenheit", bien=(-460, 30_000_000), sai=("nhan", 1.35), arity=3,
    mo="things with a well-known temperature, from the coldest to the hottest",
    lanh="What is the typical temperature of {x} in degrees Fahrenheit?"),
 "KHOI_LUONG": dict(
    nhom=("animals", "vehicles and machines", "furniture and appliances",
          "sports and gym equipment", "food and groceries", "tools and hardware",
          "musical instruments", "building materials", "spacecraft and aircraft",
          "everyday carried objects"),
    bt0="nguoi", don="pounds", bien=(0.000001, 500_000_000), sai=("nhan", 1.60), arity=3,
    mo="things with a well-known weight, from the very light to the enormous",
    lanh="What is the typical weight of {x} in pounds?"),
 "QUANG_DUONG": dict(
    nhom=("cities across the United States", "landmarks and monuments",
          "planets, moons and stars", "mountains, rivers and deserts",
          "famous roads, trails and bridges", "airports and flight routes",
          "stadiums, parks and campuses", "oceans and islands",
          "distances inside one town", "borders and coast-to-coast lines"),
    bt0="trai_dat", don="miles", bien=(0.1, 30_000_000_000), sai=("nhan", 1.12), arity=5,
    mo="named places and distances an American viewer would recognise",
    lanh="What is the distance to {x} in miles?"),
 "XAC_SUAT": dict(
    nhom=("lotteries and gambling", "weather and natural events", "health and medicine",
          "travel and accidents", "sport and competition", "birth and genetics",
          "everyday coincidences", "animals and insects", "crime and security",
          "card games and dice"),
    dang="dong_tu", bt0="tien", don="the denominator N of a 1-in-N chance", bien=(2, 100_000_000_000), sai=("nhan", 4.0),
    arity=3, mo="events with a published or calculable probability, written as -ing phrases",
    lanh="The odds of {x} are about 1 in how many? Give only the number N."),
 "DOI_NGUOI": dict(
    nhom=("the home", "work and the office", "commuting and errands",
          "screens, phones and media", "food and cooking", "exercise and health",
          "family and children", "chores and housework", "friends and socialising",
          "sleep and rest"),
    dang="dong_tu", bt0="dong_ho", don="hours per day an average American spends on it", bien=(0.02, 12), sai=("nhan", 1.9),
    arity=3, mo="ordinary daily activities, written as -ing phrases",
    lanh="How many hours per day does the average American spend {x}?"),
 "CUC_NHO": dict(
    bt0="nguyen_tu", don="metres (the object's size, in metres, as a decimal)",
    nhom=("atoms and subatomic particles", "molecules and chemistry",
          "viruses and bacteria", "human cells and blood", "dust, pollen and smoke",
          "insects and their parts", "electronics and chip features",
          "textiles, hair and paper", "seeds, grains and sand",
          "things just visible to the naked eye"),
    bien=(1e-15, 0.5), sai=("nhan", 2.0), arity=3,
    mo="very small things, from a single atom up to something you can just see",
    lanh="What is the typical size of {x} in metres?"),
 "CO_LON": dict(
    nhom=("buildings and towers", "ships, planes and vehicles",
          "bridges, dams and tunnels", "animals, living and extinct",
          "trees and plants", "sports fields and arenas",
          "machines and industrial equipment", "monuments and statues",
          "rockets and spacecraft", "natural formations"),
    bt0="nguoi", don="feet", bien=(1, 30_000), sai=("nhan", 1.30), arity=4,
    mo="large things with a well-known length or height",
    lanh="What is the typical length or height of {x} in feet?"),
}

def _bt(ten, mac_dinh):
    """Biểu tượng suy TỪ TÊN bằng chính bảng từ khoá engine đang dùng (`giai_thich._BT_TU`).

    ── VÌ SAO KHÔNG ĐỂ AI CHỌN  (đo ngày 6/9) ──────────────────────────────────────────────
    Mẻ đầu để AI chọn trong 21 biểu tượng và cổng chỉ kiểm "có nằm trong danh sách không".
    Đọc tay 18 dòng: **sấm sét -> `vi_khuan`, đồng hồ báo thức -> `te_bao`, tiếng chim ->
    `nguyen_tu`, bàn là hơi nước -> `huou`**. Mô hình bốc bừa từ một danh sách đóng, và cổng
    xanh vì nó chỉ được dạy kiểm tư cách thành viên — §13.11 đúng dạng: con số 0 lỗi nghĩa là
    cổng không hoạt động, không phải dữ liệu sạch.

    Đây là lỗi MÁY SỬA ĐƯỢC nên máy sửa, đừng tiêu một lượt gọi AI (§13.12). Và dùng lại đúng
    bảng engine đang dùng thì không đẻ ra nguồn sự thật thứ hai (§11 "đừng tạo nguồn thứ hai").
    """
    # RANH GIỚI TỪ, không phải chuỗi con. Thử ngược lần đầu bắt đúng hai ca của §15.3:
    # "cof**fee**" khớp `fee` -> `tien`, và "**house**cat" khớp `house` -> `nha`. Gốc từ ngắn
    # nằm lọt trong một từ dài hơn là cái bẫy đã trả giá ba lần trong một buổi ở bộ thiên nhiên.
    t = ten.lower()
    for bt, tu in G._BT_TU:
        if any(re.search(r"\b" + re.escape(w) + r"e?s?\b", t) for w in tu):
            return bt
    return mac_dinh


# ── DẠNG TÊN KHÔNG GIỐNG NHAU GIỮA CÁC BẢNG  (đo 6/9) ───────────────────────────────────────
# Bản đầu bắt MỌI bảng mở tên bằng "a/an/the". Kết quả: `DOI_NGUOI` nhận **0 dòng** — 14/14 bị
# cổng đối chứng loại. Không phải dữ liệu sai: bảng ấy vốn là **động từ dạng -ing**
# (`sleeping`, `looking at a phone`), nên câu hỏi lạnh *"how many hours does the average
# American spend a shower every morning?"* sai ngữ pháp, và lượt hai trả lời một câu khác.
# `XAC_SUAT` cùng bệnh (`winning the jackpot`, `being struck by lightning`).
#
# Đúng §12.5: một câu luật đúng ở ngữ cảnh nó sinh ra, sai ở ngữ cảnh mới. Dạng tên phải khai
# theo BẢNG, và nó phải khớp với câu hỏi đối chứng — hai thứ ấy là một quyết định, không phải hai.
DANG = {
 "mao_tu": dict(
    luat='- "ten" is 2 to 7 words and starts with "a", "an" or "the". '
         'Example shape: "a chainsaw at full throttle", "the surface of Venus".',
    kiem=r"^(a|an|the)\b"),
 "dong_tu": dict(
    luat='- "ten" is a 1-to-6-word activity phrase in the -ing form, with NO article in front. '
         'Example shape: "sleeping", "looking at a phone", "winning a state lottery".',
    kiem=r"^[a-z]+ing\b"),
}

# Mười vùng đời sống, xoay vòng — xem chú thích ở chỗ dùng.
NHOM = ("the home and kitchen", "work and the office", "streets and transport",
        "nature and weather", "music and entertainment", "sport and the gym",
        "medicine and the body", "construction and industry", "space and the sky",
        "animals and farms")

LENH = """You propose CANDIDATE ROWS for a reference table. You are NOT the source of truth —
every number you give is checked against an independent second lookup, and rows that disagree
are thrown away. So give only things you actually know a real figure for.

Return ONE JSON array and nothing else. Each element:
  {{"ten": "<short English name>", "so": <number>}}

Rules:
{dang}
- "so" is the value in {don}. A plain number. No units, no commas, no ranges, no text.
- Spread the values ACROSS THE WHOLE RANGE, not clustered at one end.
- Every item must be something a US viewer already has a feeling for. No obscure lab equipment.
- Do NOT repeat any of these, or anything with the same head noun:
{co}"""


def _goi(sys_p, user_p, khoa, nhiet=0.9, tra=3):
    """Một lượt gọi Groq. Trả về text, hoặc "" kèm lý do in ra — không nuốt im lặng (§15.2)."""
    body = {"model": MODEL, "temperature": nhiet, "max_tokens": 12000,
            "reasoning_effort": "low",
            "messages": [{"role": "system", "content": sys_p},
                         {"role": "user", "content": user_p}]}
    vi = []
    for j in range(min(tra * 4, len(khoa))):
        k = khoa[(int(time.time() * 1000) + j * 7919) % len(khoa)]
        p = subprocess.run(["curl", "-s", "--max-time", "180",
                            "-H", "Authorization: Bearer " + k,
                            "-H", "Content-Type: application/json",
                            "-H", "User-Agent: mm0-bang/1.0",
                            "-d", json.dumps(body),
                            "https://api.groq.com/openai/v1/chat/completions"],
                           capture_output=True, text=True)
        try:
            d = json.loads(p.stdout)
        except Exception:
            vi.append("không phải JSON"); continue
        if "error" in d:
            vi.append(str(d["error"].get("message", ""))[:60]); continue
        c = ((d.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        if c.strip():
            return c
        vi.append("content rỗng")
    print("      ⚠ Groq hỏng:", "; ".join(sorted(set(vi))[:3]))
    return ""


def _json_mang(t):
    """Lấy mảng JSON đầu tiên trong một câu trả lời có thể lẫn chữ."""
    i = t.find("[")
    if i < 0:
        return []
    sau = 0
    for j in range(i, len(t)):
        if t[j] == "[":
            sau += 1
        elif t[j] == "]":
            sau -= 1
            if sau == 0:
                try:
                    return json.loads(t[i:j + 1])
                except Exception:
                    return []
    return []


_BO = {"a", "an", "the", "at", "of", "in", "on", "to", "from", "one", "single", "full", "its"}


def _dau(ten):
    """Danh từ CHÍNH của một tên — dùng để chống trùng. `_dau` phải bỏ mạo từ và giới từ, nếu
    không thì "a chainsaw" và "a chainsaw at full throttle" đọc ra hai thứ khác nhau."""
    tu = [w for w in re.findall(r"[a-z]+", ten.lower()) if w not in _BO]
    return tu[0] if tu else ten.lower()


def _lech(a, b, sai):
    """True nếu hai con số KHỚP trong dung sai. `nhan` = tỉ số, dùng cho mọi thang log."""
    kieu, nguong = sai
    if a is None or b is None:
        return False
    if kieu == "nhan":
        if a == 0 or b == 0:
            return a == b
        if (a < 0) != (b < 0):
            return False
        r = abs(a) / abs(b)
        return (1 / nguong) <= r <= nguong
    return abs(a - b) <= nguong


def _so_tu(t):
    m = re.search(r"-?\d[\d,]*(?:\.\d+)?(?:\s*[eE]-?\d+)?", t.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(0).replace(" ", ""))
    except Exception:
        return None


def doi_chung(ten_ds, cau, khoa):
    """Cổng 4. Hỏi LẠI từng tên bằng một lượt gọi độc lập, `temperature 0`, câu hỏi LẠNH —
    không nhắc bảng, không nhắc kênh, không nhắc con số vừa nhận. Chạy song song."""
    sysp = ("Answer with ONE number and nothing else. No units, no words, no commas. "
            "If you do not know a real figure, answer exactly: UNKNOWN")

    def mot(x):
        t = _goi(sysp, cau.format(x=x), khoa, nhiet=0.0, tra=2)
        return None if "UNKNOWN" in t.upper() else _so_tu(t)

    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(mot, ten_ds))


def mot_bang(ten_bang, muc_tieu, khoa, mo_moi=48):
    dt = BANG[ten_bang]
    cu = list(getattr(G, ten_bang))
    co_dau = {_dau(r[0]) for r in cu}
    them, nguon = [], []
    print(f"\n══ {ten_bang}  {len(cu)} -> {muc_tieu} mục")

    while len(cu) + len(them) < muc_tieu:
        thieu = muc_tieu - len(cu) - len(them)
        n = min(mo_moi, thieu + 12)          # xin dư, vì cổng sẽ loại bớt
        dg = DANG[dt.get("dang", "mao_tu")]
        sysp = LENH.format(don=dt["don"], dang=dg["luat"],
                           co="  " + ", ".join(sorted(co_dau)))
        # Xin theo NHÓM CHỦ ĐỀ, xoay vòng. Mẻ trước không chia nhóm thì tới mẻ thứ tám có
        # 48/50 dòng trùng danh từ chính — mô hình quay lại đúng cái hồ nó vừa múc. Nhóm là
        # cách rẻ nhất ép nó sang một vùng khác của trí nhớ; không nhóm thì trần thật của một
        # bảng chỉ khoảng 120 mục, và trần ấy là trần của LỜI HỎI, không phải của thế giới.
        # Nhóm phải HỢP với bảng. Bản đầu dùng chung một danh sách mười nhóm cho mọi bảng, và
        # `DOI_NGUOI` (hoạt động thường ngày) rơi vào nhóm *"space and the sky"* -> 48/49 dòng
        # sai dạng, vì không có "hoạt động thường ngày trong vũ trụ" nào để kể. Cùng §14.2 của
        # bộ Kling: **bộ lịch phát cho một kênh nhịp mà thế giới ấy không diễn được** — chữa
        # bằng cách đừng phát nhịp ấy, không phải bằng cách dặn thêm.
        _nh = dt.get("nhom") or NHOM
        nh = _nh[(len(cu) + len(them)) % len(_nh)]
        t = _goi(sysp, f"Give {n} rows: {dt['mo']}. Draw them from this area of life: {nh}.",
                 khoa)
        tho = _json_mang(t)
        if not tho:
            print("      ⛔ không nhận được dòng nào — dừng bảng này"); break

        # ── cổng 1·2·3 (máy, không tốn lượt gọi) ────────────────────────────────────────────
        qua, vi = [], {}
        for r in tho:
            if not isinstance(r, dict):
                vi["không phải object"] = vi.get("không phải object", 0) + 1; continue
            ten = str(r.get("ten") or "").strip()
            try:
                so = float(r.get("so"))
            except Exception:
                vi["số không đọc được"] = vi.get("số không đọc được", 0) + 1; continue
            # Thiếu mạo từ là lỗi máy sửa được — thêm "a"/"an" thay vì vứt cả dòng (§13.12).
            if dt.get("dang", "mao_tu") == "mao_tu" and ten[:1].islower() \
               and not re.match(r"^(a|an|the)\b", ten, re.I):
                ten = ("an " if ten[:1] in "aeiou" else "a ") + ten
            w = len(ten.split())
            it = 1 if dt.get("dang") == "dong_tu" else 2
            if not (it <= w <= 8) or not re.match(dg["kiem"], ten, re.I):
                vi["dạng tên"] = vi.get("dạng tên", 0) + 1; continue
            bt = _bt(ten, dt["bt0"])
            if not (dt["bien"][0] <= so <= dt["bien"][1]):
                vi["ngoài biên vật lý"] = vi.get("ngoài biên vật lý", 0) + 1; continue
            d = _dau(ten)
            if d in co_dau:
                vi["trùng danh từ chính"] = vi.get("trùng danh từ chính", 0) + 1; continue
            co_dau.add(d)
            qua.append((ten, so, bt))

        # ── cổng 4: đối chứng ────────────────────────────────────────────────────────────────
        hai = doi_chung([x[0] for x in qua], dt["lanh"], khoa) if qua else []
        an = 0
        for (ten, so, bt), so2 in zip(qua, hai):
            if not _lech(so, so2, dt["sai"]):
                an += 1
                vi["đối chứng lệch"] = vi.get("đối chứng lệch", 0) + 1
                co_dau.discard(_dau(ten))
                continue
            them.append((ten, so, bt))
            nguon.append({"bang": ten_bang, "ten": ten, "so": so, "doi_chung": so2,
                          "ti_so": round(so / so2, 3) if so2 else None,
                          "model": MODEL, "ngay": time.strftime("%Y-%m-%d")})
        print(f"   xin {len(tho)} · qua cổng máy {len(qua)} · đối chứng loại {an}"
              f" · NHẬN {len(qua) - an}  (tổng {len(cu) + len(them)})")
        if vi:
            print("      loại vì:", " · ".join(f"{k} {v}" for k, v in sorted(vi.items())))
        if len(qua) - an == 0:
            print("      ⛔ một mẻ không nhận được dòng nào — dừng, đừng đốt thêm lượt gọi")
            break
    return them, nguon


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bang", default="", help="tên bảng, cách nhau bởi dấu phẩy; rỗng = tất cả")
    ap.add_argument("--den", type=int, default=200, help="số mục mục tiêu")
    ap.add_argument("--ra", default=os.path.join(GOC, "bang_moi.json"))
    a = ap.parse_args()

    khoa = PC._khoa_groq()
    if not khoa:
        raise RuntimeError("không có khoá Groq — đặt GROQ_KEYS hoặc .keys.local")
    print(f"🔑 {len(khoa)} khoá Groq · model {MODEL}")

    ds = [x.strip() for x in a.bang.split(",") if x.strip()] or list(BANG)
    ket, nguon = {}, []
    for b in ds:
        t, n = mot_bang(b, a.den, khoa)
        ket[b] = t
        nguon += n
    io.open(a.ra, "w", encoding="utf-8").write(json.dumps(ket, ensure_ascii=False, indent=1))
    # Tên sổ xuất xứ đi THEO tệp kết quả: bốn tiến trình chạy song song mà cùng ghi một
    # `bang_nguon.json` thì tiến trình cuối xoá xuất xứ của ba tiến trình kia — và mất lặng lẽ,
    # vì mỗi tệp đọc lên vẫn hợp lệ. Đúng họ §15.2: bằng chứng bị ném đi trước khi ai kịp đọc.
    io.open(a.ra.replace("bang_moi", "bang_nguon"), "w", encoding="utf-8").write(
        json.dumps(nguon, ensure_ascii=False, indent=1))
    print(f"\n✅ ghi {sum(len(v) for v in ket.values())} dòng mới -> {a.ra}")
    print("   xuất xứ từng dòng -> bang_nguon.json")
    print("   ĐỌC TAY một mẫu trước khi nối vào giai_thich.py (§13.20).")


if __name__ == "__main__":
    main()
