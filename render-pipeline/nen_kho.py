#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KHO NƠI CHỐN CHO 18 KÊNH — SOẠN MÔ TẢ, KHÔNG VẼ  (6/9/2026)

── VÌ SAO ───────────────────────────────────────────────────────────────────────────────────
Soi lưới 4 khung bản HOW LOUD: **3/4 khung cùng một cái bàn làm việc**. Không phải lỗi dựng —
`PHONG_KENH` chỉ khai nơi chốn cho ĐÚNG MỘT kênh (`dayinlife`, 4 phòng); 17 kênh còn lại rơi
về `_mac_dinh` và cả kênh sống bằng **hai** căn phòng.

Bộ nền comic đắt đúng một lần: vẽ xong thì tập thứ một nghìn vẫn dùng lại đúng ảnh ấy, chi phí
ảnh mỗi tập bằng 0. Nên số nơi chốn không bị hạn mức chặn — nó bị chặn bởi việc **chưa ai viết
ra danh sách**.

── VÌ SAO TÁCH KHỎI BƯỚC VẼ ─────────────────────────────────────────────────────────────────
Soạn mô tả gọi Groq; vẽ gọi Cloudflare và tiêu neuron thật. Trộn hai việc thì một lượt soạn
hỏng giữa chừng để lại nửa kho ảnh — và ảnh thì không sinh lại miễn phí. Soạn ra tệp, đọc tay,
rồi mới vẽ.

── AI ĐƯỢC LÀM GÌ Ở ĐÂY ─────────────────────────────────────────────────────────────────────
Khác hẳn `bang_mo_rong.py`: chỗ này **không có con số nào**, nên ranh giới "AI không bịa số"
không bị đụng tới. AI viết mô tả một CĂN PHÒNG, và mọi câu nó viết đều đi qua bốn cổng dưới.

── BỐN CỔNG ─────────────────────────────────────────────────────────────────────────────────
1. **không người**  — nền có người thì engine dán nhân vật vector lên một khung đã có người.
2. **không chữ**    — FLUX vẽ chữ ra ký tự loằng ngoằng, và người xem đọc ra "nghiệp dư" trong
                      nửa giây (§12.7). Cấm cả `sign`, `label`, `poster`, `menu`, `screen`.
3. **không viết nghịch** — FLUX không có negative prompt: `no clutter in the middle` đẻ ra đúng
                      cái đống ở giữa (`kiem_nen.CAM_NGHICH` đã trả giá cho bài học này).
4. **trùng**        — hai phòng cùng danh từ chính là một phòng.

Ba mệnh lệnh bố cục (sàn liền mạch · ngang tầm mắt · đồ dồn hai mép) **KHÔNG viết ở đây**:
chúng nằm trong `kich_hai.SAN_NEN` và được `pilot_hai.ve_nen` ghép vào lúc vẽ. Một ràng buộc
chỉ được sống ở đúng một chỗ (§15.12).
"""
import argparse, io, json, os, re, subprocess, sys, time

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
os.environ.setdefault("GT_KHONG_CF", "1")
import giai_thich as G
import phim_canh as PC

MODEL = "openai/gpt-oss-120b"
RA = os.path.join(GOC, "nen_kho.json")

# ── VÙNG NƠI CHỐN CỦA TỪNG KÊNH ─────────────────────────────────────────────────────────────
# Mỗi kênh hỏi một câu hỏi khác nhau, nên nó SỐNG ở những nơi khác nhau. Cấp chung một danh
# sách nhóm cho cả 18 kênh là đúng lỗi đã trả giá ở `bang_mo_rong`: `DOI_NGUOI` nhận nhóm
# "space and the sky" rồi trả về 48/49 dòng vô nghĩa (§14.2 — đừng phát cho một thế giới cái
# nhịp nó không diễn được).
VUNG = {
 "howlong":    ("roads and highways", "airports and terminals", "train stations",
                "hiking trails and parks", "harbours and docks", "city streets",
                "deserts and open country", "bridges and overpasses",
                "bus depots and rest stops", "observatories and planetariums"),
 "howbig":     ("warehouses and hangars", "museums and galleries", "construction sites",
                "stadiums and arenas", "shipyards and dry docks", "quarries and mines",
                "zoos and aquariums", "cathedrals and grand halls",
                "car parks and lots", "open fields and plains"),
 "realcost":   ("home kitchens", "cafes and coffee shops", "supermarkets",
                "living rooms", "home offices", "bank and credit-union lobbies",
                "shopping malls", "petrol stations", "corner shops", "suburban porches"),
 "howmuch":    ("bank vaults and counting rooms", "office towers", "printing works",
                "warehouses of stacked crates", "trading floors", "libraries",
                "post-room and mail sorting halls", "vast car parks",
                "grain silos and elevators", "empty conference halls"),
 "whatif":     ("city squares", "motorway junctions", "power stations",
                "reservoirs and water works", "farm fields", "recycling plants",
                "subway platforms", "beaches and shorelines",
                "residential streets", "wind and solar farms"),
 "survive":    ("snowfields and glaciers", "deserts", "dense forests",
                "mountain ridges", "caves", "open ocean and rafts",
                "abandoned cabins", "swamps and wetlands",
                "high-altitude camps", "storm-hit coastlines"),
 "dayinlife":  ("hospital wards and corridors", "restaurant kitchens", "classrooms",
                "fire stations", "farms and barns", "workshops and garages",
                "newsrooms and studios", "warehouses and loading bays",
                "hotel lobbies and back rooms", "construction sites"),
 "wheregoes":  ("recycling plants", "landfills and transfer stations",
                "sewage and water treatment works", "sorting warehouses",
                "shipping ports", "scrapyards", "food processing plants",
                "power grids and substations", "post depots", "compost yards"),
 "therules":   ("courtrooms", "council chambers", "government office corridors",
                "airport security halls", "waiting rooms", "school offices",
                "library reading rooms", "police station front desks",
                "hospital admin offices", "corporate boardrooms"),
 "speedof":    ("race tracks", "airfields and runways", "railway lines",
                "velodromes and running tracks", "wind tunnels and test labs",
                "ski slopes", "open motorways", "rivers and rapids",
                "launch pads", "bowling alleys and arcades"),
 "odds":       ("casinos and card rooms", "bingo halls", "lottery kiosks",
                "sports betting lounges", "amusement arcades", "county fairs",
                "poker rooms", "racetrack stands", "board-game tables",
                "carnival midways"),
 "hiddenfee":  ("supermarket aisles", "restaurant dining rooms", "hotel receptions",
                "airline check-in halls", "car showrooms", "phone shops",
                "gym receptions", "cinema foyers", "repair workshops",
                "bank branch interiors"),
 "yearsof":    ("bedrooms", "commuter trains and buses", "office cubicles",
                "living rooms with a television", "queues and waiting areas",
                "gyms", "kitchens at mealtime", "bathrooms and hallways",
                "school corridors", "hospital waiting rooms"),
 "howloud":    ("workshops and machine rooms", "concert halls and clubs",
                "airport aprons", "construction sites", "stadium stands",
                "factory floors", "quiet libraries and studios",
                "forests and quiet countryside", "city intersections",
                "kitchens with appliances running"),
 "whatweighs": ("scrapyards and weighbridges", "farms and stockyards", "gyms",
                "docks and container yards", "removal vans and loading bays",
                "aircraft hangars", "quarries", "butchers and markets",
                "furniture warehouses", "museum storerooms"),
 "rightnow":   ("air traffic control rooms", "city rooftops at night",
                "server rooms and data centres", "hospital maternity wings",
                "crowded plazas", "supermarket checkouts", "call centres",
                "railway concourses", "ports with container ships",
                "stadium crowds"),
 "howhot":     ("kitchens and ovens", "foundries and forges", "deserts at noon",
                "volcano slopes and lava fields", "engine rooms",
                "glass and ceramic workshops", "boiler rooms", "saunas",
                "solar and power plants", "laboratories with furnaces"),
 "smallest":   ("laboratories with microscopes", "clean rooms",
                "electronics workbenches", "watchmaker and jeweller benches",
                "hospital pathology rooms", "seed and plant nurseries",
                "dental surgeries", "print and etching workshops",
                "textile mills", "pharmacies and dispensaries"),
}

LENH = """You write BACKGROUND descriptions for a flat 2D cartoon animated series.
Each one is a PLACE that the camera will look at. Two cartoon characters will later be drawn
standing in the middle of it, so the place must be somewhere two people could stand and talk.

Return ONE JSON array of strings and nothing else. Each string:
- 6 to 18 words, lowercase, starting with "a" or "an".
- Names the place, then two or three things along the walls or edges that belong there.
  Example shape: "a machine shop, lathes and tool racks along both side walls, high windows"
- Describe ONLY the place. NO people, NO animals, NO crowds, NO hands, NO silhouettes.
- NO writing of any kind: no signs, labels, posters, menus, screens, numbers or letters.
- Never write a sentence that says something is absent. Write only what IS there.
- Every one must be visibly DIFFERENT from the others: a different room, not the same room
  with a different adjective.

Do not repeat any of these places, or anything with the same main noun:
{co}"""

# ── DỌN CÂU: ĐỌC TAY 18 MẪU BẮT ĐƯỢC BỐN LỖI  (6/9/2026) ────────────────────────────────────
# Bốn cổng ban đầu để lọt bốn thứ, và cả bốn đều không phải "sai nơi chốn" mà là sai CÂU CHỮ:
#   "an spice aisle"        -> mạo từ sai; máy sửa được (§13.12)
#   "alloy charts on the wall" -> `chart`/`diagram`/`map` là CHỮ dán tường, mà FLUX vẽ chữ ra
#                              ký tự loằng ngoằng — đúng thứ cổng `CHU` sinh ra để chặn, chỉ là
#                              danh sách thiếu mấy từ ấy
#   "wind‑mills", "stained‑glass" -> gạch nối U+2011, không phải ASCII
#   "an iPad lounge"        -> tên thương hiệu; vừa là tài sản của hãng, vừa làm FLUX vẽ một
#                              món đồ có logo
# Ba cái đầu máy sửa hoặc máy chặn được. Cái thứ tư chặn bằng cách nhận ra chữ viết HOA giữa
# câu — nơi chốn viết thường hết, nên chữ hoa lạc vào giữa câu gần như luôn là tên riêng.
_HIEU = re.compile(r"(?<! )\b[A-Z][a-zA-Z]{2,}\b|\b[a-z][A-Z]")


def don_cau(s):
    """Chuẩn hoá câu. Trả "" nghĩa là LOẠI."""
    s = (s.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
          .replace("\u2019", "'"))
    s = " ".join(s.split()).strip().rstrip(".")
    if _HIEU.search(s):
        return ""
    m = re.match(r"^(a|an)\s+(\S+)(.*)$", s, re.I)
    if m:
        s = ("an" if m.group(2)[:1].lower() in "aeiou" else "a") + " " + m.group(2) + m.group(3)
    return s


NGUOI = re.compile(r"\b(people|person|man|woman|men|women|child|children|kid|crowd|worker|"
                   r"staff|customer|figure|silhouette|hand|face|someone|anyone|shopper|"
                   r"patient|nurse|doctor|passenger|player|audience|visitor)s?\b", re.I)
CHU = re.compile(r"\b(sign|signage|label|poster|menu|banner|billboard|text|letter|word|"
                 r"number|logo|writing|screen|monitor|display|board|notice|chart|diagram|"
                 r"map|blueprint|plan|schedule|calendar|certificate|ticket|receipt|"
                 r"newspaper|book|magazine|whiteboard|chalkboard)s?\b", re.I)
NGHICH = re.compile(r"\b(no|without|not|empty of|free of|devoid)\b", re.I)
_BO = {"a", "an", "the", "of", "in", "on", "at", "with", "and"}


def _dau(s):
    tu = [w for w in re.findall(r"[a-z]+", s.lower()) if w not in _BO]
    return tu[0] if tu else s.lower()


def _goi(sys_p, user_p, khoa):
    body = {"model": MODEL, "temperature": 1.0, "max_tokens": 12000,
            "reasoning_effort": "low",
            "messages": [{"role": "system", "content": sys_p},
                         {"role": "user", "content": user_p}]}
    vi = []
    for j in range(min(12, len(khoa))):
        k = khoa[(int(time.time() * 1000) + j * 7919) % len(khoa)]
        p = subprocess.run(["curl", "-s", "--max-time", "180",
                            "-H", "Authorization: Bearer " + k,
                            "-H", "Content-Type: application/json",
                            "-H", "User-Agent: mm0-nen/1.0",
                            "-d", json.dumps(body),
                            "https://api.groq.com/openai/v1/chat/completions"],
                           capture_output=True, text=True)
        try:
            d = json.loads(p.stdout)
        except Exception:
            vi.append("không phải JSON"); continue
        if "error" in d:
            vi.append(str(d["error"].get("message", ""))[:50]); continue
        c = ((d.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        if c.strip():
            return c
        vi.append("content rỗng")
    print("      ⚠ Groq hỏng:", "; ".join(sorted(set(vi))[:3]))
    return ""


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
                    return [x for x in json.loads(t[i:j + 1]) if isinstance(x, str)]
                except Exception:
                    return []
    return []


def mot_kenh(ma, muc_tieu, khoa, da_co=None):
    """Bổ sung nơi chốn cho một kênh cho tới `muc_tieu`.

    ── VÌ SAO PHẢI NỐI, KHÔNG ĐƯỢC SINH LẠI  (6/9/2026) ────────────────────────────────────
    Ảnh nền đặt tên theo CHỈ SỐ: `comic_nen/howloud_042.webp` là mô tả thứ 42 của kênh ấy.
    Sinh lại danh sách từ đầu thì mô tả thứ 42 thành một căn phòng KHÁC, và 1.081 ảnh đã vẽ
    lệch hẳn khỏi mô tả sinh ra chúng. Không có lỗi nào báo — ảnh vẫn hiện, chỉ là sổ sách nói
    dối, và những phòng mới ở chỉ số cũ thì KHÔNG BAO GIỜ được vẽ (bộ vẽ thấy ảnh đã có nên bỏ
    qua). Đúng §15.11: hệ tất định + chỉ số tay = sinh trùng mà không có gì báo.

    Nên: nhận `da_co` là danh sách hiện có, giữ nguyên THỨ TỰ của nó, chỉ nối vào đuôi.
    """
    vung = VUNG.get(ma) or VUNG["dayinlife"]
    ra = list(da_co or [])
    co = {_dau(x) for x in ra}
    print(f"\n══ {ma}  {len(ra)} -> {muc_tieu} nơi chốn")
    lan = 0
    while len(ra) < muc_tieu and lan < len(vung) * 4:
        v = vung[lan % len(vung)]
        lan += 1
        sysp = LENH.format(co="  " + ", ".join(sorted(co)) if co else "  (none yet)")
        t = _goi(sysp, f"Write 14 background places for this area: {v}.", khoa)
        tho = _mang(t)
        if not tho:
            continue
        vi = {}
        for s in tho:
            s = don_cau(str(s))
            if not s:
                vi["tên riêng/thương hiệu"] = vi.get("tên riêng/thương hiệu", 0) + 1; continue
            w = len(s.split())
            if not (6 <= w <= 20) or not re.match(r"^(a|an)\b", s, re.I):
                vi["dạng câu"] = vi.get("dạng câu", 0) + 1; continue
            if NGUOI.search(s):
                vi["có người"] = vi.get("có người", 0) + 1; continue
            if CHU.search(s):
                vi["có chữ/biển"] = vi.get("có chữ/biển", 0) + 1; continue
            if NGHICH.search(s):
                vi["viết nghịch"] = vi.get("viết nghịch", 0) + 1; continue
            d = _dau(s)
            if d in co:
                vi["trùng"] = vi.get("trùng", 0) + 1; continue
            co.add(d)
            ra.append(s)
        print(f"   {v:<38} +{len([1 for s in tho]) and len(ra)}"
              f"  (loại: {' · '.join(f'{k} {v2}' for k, v2 in sorted(vi.items())) or 'không'})")
    return ra[:muc_tieu]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="", help="mã kênh, phẩy; rỗng = cả 18")
    ap.add_argument("--so", type=int, default=100, help="số nơi chốn mỗi kênh")
    # Mỗi tiến trình ghi một tệp RIÊNG rồi `gop_kho()` ghép lại. Bốn tiến trình cùng ghi
    # `nen_kho.json` thì tiến trình cuối xoá việc của ba tiến trình kia — mất lặng lẽ, vì tệp
    # còn lại vẫn hợp lệ. Em vừa mắc đúng lỗi này ở `bang_nguon.json` trong cùng buổi.
    ap.add_argument("--ra", default="")
    a = ap.parse_args()

    khoa = PC._khoa_groq()
    if not khoa:
        raise RuntimeError("không có khoá Groq")
    print(f"🔑 {len(khoa)} khoá Groq")

    ra = a.ra or RA
    kho = {}
    if os.path.exists(ra):
        kho = json.load(io.open(ra, encoding="utf-8"))
    ds = [x.strip() for x in a.kenh.split(",") if x.strip()] or [k["ma"] for k in G.KENH]
    # Nguồn của danh sách CŨ luôn là `nen_kho.json` (kho thật), kể cả khi ghi ra tệp riêng —
    # tệp riêng chỉ để bốn tiến trình không đè nhau, không phải một kho thứ hai.
    goc = {}
    if os.path.exists(RA):
        goc = json.load(io.open(RA, encoding="utf-8"))
    for ma in ds:
        kho[ma] = mot_kenh(ma, a.so, khoa, goc.get(ma) or kho.get(ma))
        io.open(ra, "w", encoding="utf-8").write(json.dumps(kho, ensure_ascii=False, indent=1))
    print(f"\n✅ {sum(len(v) for v in kho.values())} nơi chốn / {len(kho)} kênh -> {ra}")
    print("   ĐỌC TAY một mẫu trước khi vẽ — vẽ rồi thì neuron không lấy lại được.")


if __name__ == "__main__":
    main()
