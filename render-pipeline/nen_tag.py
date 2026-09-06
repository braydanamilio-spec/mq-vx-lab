#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GẮN THẺ NƠI CHỐN ĐỂ NỀN KHỚP NỘI DUNG TẬP  (6/9/2026)

── VÌ SAO ───────────────────────────────────────────────────────────────────────────────────
Anh: *"ảnh generate ra e có chia theo từng group tag key phù hợp mỗi channel để khi lấy ảnh nó
tự động với nội dung kịch bản videos"*. Chưa có, và đo ra thì lệch rõ:

    HOW LOUD «a roaring crowd chant at a music festival» -> xưởng bảo trì · làn rải nhựa đường
    REAL COST «a $12 lunch every workday»                -> trạm bơm dầu diesel

Bộ chọn cũ là một BƯỚC NHẢY tất định — nó lo đúng một việc (đừng lặp phòng) và mù hoàn toàn
với nội dung. Đa dạng mà không liên quan thì vẫn là khung nói một đằng lời nói một nẻo (§17.5).

── VÌ SAO KHÔNG KHỚP BẰNG TỪ TRỰC TIẾP ──────────────────────────────────────────────────────
Kịch bản viết *"crowd chant at a music festival"*, nền viết *"a concert hall, speaker stacks
and a raised stage"*. Không một từ nào trùng. Khớp theo từ sẽ ra 0 gần như mọi lúc — đúng
§13.5: *đo CHUỖI khi thứ cần đo là NỘI DUNG*.

Cầu nối là **NHÓM CHỦ ĐỀ** — chính thứ đã sinh ra các nền ấy (`nen_kho.VUNG`, mỗi kênh 10
nhóm). Nhóm là một khái niệm, và cả nền lẫn kịch bản đều quy về nhóm được. Em đã không lưu
nhóm lúc sinh (đúng lỗi §15.12: viết ra một trường rồi vứt), nên ở đây suy lại từ chính chữ
của nền — và kiểm bằng cách đọc tay một mẫu.

── SỔ THẺ TÁCH RIÊNG, KHÔNG SỬA `nen_kho.json` ──────────────────────────────────────────────
Ảnh đặt tên theo CHỈ SỐ trong `nen_kho.json`. Đổi cấu trúc tệp ấy là mạo hiểm với 1.081 ảnh đã
vẽ. `nen_tag.json` là một bảng tra riêng, hỏng thì đường dựng rơi về bước nhảy cũ.
"""
import io, json, os, re, sys

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
os.environ.setdefault("GT_KHONG_CF", "1")
import nen_kho as NK

RA = os.path.join(GOC, "nen_tag.json")

# Từ khoá phụ cho mỗi nhóm: tên nhóm một mình quá hẹp ("workshops and machine rooms" không
# chứa chữ `forge`, `lathe`, `garage`). Danh sách này chỉ cần đủ để PHÂN NHÓM, không cần đủ
# để mô tả — sai nhóm một nền thì nó vẫn được dùng, chỉ là ở tập khác.
THEM = {
 "workshop": "forge lathe garage bay tool welding machine repair mechanic gear drum press mill",
 "concert": "concert club stage band music instrument speaker amplifier dance venue nightclub",
 "airport": "airport terminal runway hangar apron gate departure baggage aircraft plane",
 "construction": "construction site scaffold crane excavator concrete brick beam girder rubble",
 "stadium": "stadium arena bleacher stand court field track pitch gym locker",
 "factory": "factory floor plant assembly conveyor industrial warehouse foundry furnace kiln",
 "library": "library studio archive reading quiet booth recording bookshelf desk",
 "forest": "forest woodland meadow glade prairie riverbed lake marsh trail countryside grove",
 "street": "street intersection sidewalk crossing junction promenade plaza alley boulevard",
 "kitchen": "kitchen pantry diner cafe restaurant bakery counter oven stove fridge dining",
 "home": "living bedroom lounge parlour hallway porch attic basement apartment sofa",
 "office": "office cubicle boardroom conference reception corridor admin desk meeting",
 "shop": "supermarket aisle store shop market checkout showroom boutique mall stall",
 "hospital": "hospital ward clinic surgery pharmacy laboratory lab dispensary examination",
 "school": "classroom school lecture campus hall corridor auditorium",
 "transport": "train station platform bus depot subway tram ferry dock harbour port pier",
 "farm": "farm barn stable field orchard greenhouse silo stockyard nursery coop",
 "money": "bank vault counting teller casino bingo lottery betting poker trading",
 "space": "observatory planetarium launch control mission telescope rocket",
 "water": "beach shore coast ocean reservoir pool aquarium waterworks treatment",
 "cold": "glacier snowfield ice tundra freezer cold-storage arctic",
 "hot": "desert volcano lava sauna boiler engine-room forge foundry",
 "court": "courtroom chamber council police station tribunal registry",
 "waste": "recycling landfill scrapyard sorting compost sewage transfer",
}


def _tu(s):
    return set(re.findall(r"[a-z]+", (s or "").lower()))


_NHOM_TU = {k: set(v.split()) for k, v in THEM.items()}


_BO_NHOM = set("and the of a an in on at with".split())
_CACHE = {}


def _tu_nhom(ma: str):
    """Với mỗi nhóm của KÊNH ẤY: tập từ nhận diện = chữ trong tên nhóm + các mục `THEM` có
    khoá xuất hiện trong tên nhóm.

    ── VÌ SAO THEO KÊNH, KHÔNG THEO TỪ ĐIỂN CHUNG  (sửa lần 1, 6/9) ────────────────────────
    Bản đầu chấm mọi nền vào 24 nhóm chung và **37% nền không gán được**. Nhưng mọi nền đều
    SINH RA từ đúng một trong mười nhóm của kênh nó (`nen_kho.VUNG`) — nên hỏi "nền này thuộc
    nhóm nào TRONG MƯỜI NHÓM CỦA KÊNH" là một câu hỏi hẹp hơn hẳn và luôn có đáp án.
    Đây cũng là cách duy nhất giữ được tính ĐỐI XỨNG: kịch bản cũng chấm vào đúng mười nhóm
    ấy, nên hai bên nói cùng một ngôn ngữ.
    """
    if ma in _CACHE:
        return _CACHE[ma]
    r = []
    for g in (NK.VUNG.get(ma) or NK.VUNG["dayinlife"]):
        t = {w for w in _tu(g) if w not in _BO_NHOM}
        for k, v in _NHOM_TU.items():
            if k in g or (t & v):
                t |= v
        r.append((g, t))
    _CACHE[ma] = r
    return r


def nhom_cua(chu: str, ma: str = "") -> str:
    """Nhóm của một đoạn chữ, TRONG bộ nhóm của kênh `ma`. "" nếu không đủ bằng chứng —
    thà không gán còn hơn gán bừa (§13.12)."""
    t = _tu(chu)
    ds = _tu_nhom(ma) if ma else [(k, v) for k, v in _NHOM_TU.items()]
    diem = [(len(t & v), g) for g, v in ds]
    n, g = max(diem)
    return g if n >= 1 else ""


# ══ PHÂN NHÓM BẰNG MODEL  (sửa lần 2, 6/9/2026) ══════════════════════════════════════════════
# Hai lần khớp theo TỪ đều hỏng: từ điển chung -> 37% không gán được; tên nhóm của chính kênh ->
# **65%**. Không phải từ điển thiếu — mà vì nền viết *"a bleacher tier, steel railings"* còn nhóm
# tên là *"stadium stands"*: không một từ nào trùng, và mọi danh sách từ đủ rộng để bắt được nó
# sẽ đủ rộng để bắt nhầm thứ khác (§13.9 — danh sách ngoại lệ là danh sách vô hạn).
#
# Đây là việc PHÂN LOẠI THEO NGHĨA, đúng thứ model làm tốt. Và khác `bang_mo_rong`, ở đây
# **không có con số nào** — nên luật nền "AI không bao giờ cấp một con số" không bị đụng tới.
#
# Hai cổng, cả hai đều máy kiểm được: số phần tử trả về phải khớp số nền hỏi, và mọi chỉ số
# phải nằm trong 0..9. Sai một trong hai thì bỏ cả mẻ và hỏi lại — không nhận một phần.
LENH_NHOM = """You sort background descriptions into groups.

GROUPS (answer with the number):
{nhom}

For each numbered background below, answer which group it belongs to.
Return ONE JSON array of integers, same length and order as the list. Nothing else."""


def _phan_ai(ma, ds, nhom, khoa, lo=40):
    """Trả danh sách chỉ số nhóm cho `ds`, hoặc [] nếu không lấy được."""
    import phim_canh as C
    ra = []
    for i in range(0, len(ds), lo):
        mieng = ds[i:i + lo]
        sysp = LENH_NHOM.format(nhom="\n".join(f"{j}. {g}" for j, g in enumerate(nhom)))
        u = "\n".join(f"{k}. {t}" for k, t in enumerate(mieng))
        # Thử lại tối đa 3 lần: mẻ hỏng ở đây không phải lỗi dữ liệu mà là một câu trả lời
        # lệch định dạng — thử lại gần như luôn ăn, và bỏ mẻ thì 40 nền mất nhóm vĩnh viễn.
        v = []
        for _ in range(3):
            t = C._goi(sysp, u, khoa)
            try:
                w = json.loads(t[t.index("["):t.rindex("]") + 1])
            except Exception:
                w = []
            if len(w) == len(mieng) and all(isinstance(x, int) and 0 <= x < len(nhom)
                                            for x in w):
                v = w
                break
        if not v:
            print(f"      ⚠ {ma} mẻ {i//lo}: 3 lần đều lệch định dạng — bỏ mẻ")
            ra += [None] * len(mieng)
            continue
        ra += v
    return ra


SO_TAP = os.path.join(GOC, "nen_tag_tap.json")


def nhom_tap(ma: str, chu: str, khoa=None) -> str:
    """Nhóm nơi chốn HỢP với nội dung một tập. Có nhớ đệm nên mỗi chủ đề chỉ hỏi một lần.

    ── VÌ SAO PHẢI HỎI MODEL Ở CẢ HAI PHÍA  (đo 6/9/2026) ──────────────────────────────────
    Gắn thẻ cho NỀN bằng model xong, em vẫn chấm phía TẬP bằng phép khớp từ — và 3/4 tập thử
    ra "không chấm được". Hiển nhiên khi nhìn lại: *"How hot is the corona of the Sun"* không
    chứa từ nào trong *"space and the planets"*. Cùng đúng một lý do đã làm phép khớp từ hỏng
    ở phía nền; sửa một phía rồi dừng là đúng họ lỗi *vá một nhánh, để nguyên nhánh song song*
    (§6 CLAUDE.md).

    Hai phía phải nói CÙNG một ngôn ngữ: cùng bộ mười nhóm, cùng cách chấm.

    Nhớ đệm theo (kênh, chủ đề) — một kênh chỉ có vài trăm chủ đề, nên sau vài ngày chạy thì
    hàm này gần như không bao giờ gọi mạng nữa.
    """
    try:
        so = json.load(io.open(SO_TAP, encoding="utf-8"))
    except Exception:
        so = {}
    kh = ma + "|" + " ".join(chu.lower().split())[:120]
    if kh in so:
        return so[kh]
    nhom = list(NK.VUNG.get(ma) or NK.VUNG["dayinlife"])
    try:
        import phim_canh as C
        khoa = khoa or C._khoa_groq()
        sysp = ("Answer with ONE integer and nothing else — the number of the group where this "
                "episode would most naturally be filmed.\n\nGROUPS:\n"
                + "\n".join(f"{i}. {g}" for i, g in enumerate(nhom)))
        t = C._goi(sysp, chu[:600], khoa)
        v = int(re.search(r"\d+", t).group(0))
        r = nhom[v] if 0 <= v < len(nhom) else ""
    except Exception:
        r = ""
    so[kh] = r
    try:
        io.open(SO_TAP, "w", encoding="utf-8").write(json.dumps(so, ensure_ascii=False, indent=0))
    except Exception:
        pass
    return r


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--ai", action="store_true", help="phân nhóm bằng model (chính xác hơn hẳn)")
    ap.add_argument("--kenh", default="")
    a = ap.parse_args()
    kho = json.load(io.open(os.path.join(GOC, "nen_kho.json"), encoding="utf-8"))
    if a.ai:
        import phim_canh as C
        khoa = C._khoa_groq()
        cu = {}
        if os.path.exists(RA):
            cu = json.load(io.open(RA, encoding="utf-8"))
        ds_k = [x for x in (a.kenh.split(",") if a.kenh else sorted(kho)) if x in kho]
        for ma in ds_k:
            nhom = list(NK.VUNG.get(ma) or NK.VUNG["dayinlife"])
            ds = kho[ma]
            v = _phan_ai(ma, ds, nhom, khoa)
            n = 0
            for i, x in enumerate(v):
                if x is not None:
                    cu[f"{ma}_{i:03d}"] = nhom[x]; n += 1
            print(f"   {ma:<12} {n}/{len(ds)} nền có nhóm")
            io.open(RA, "w", encoding="utf-8").write(json.dumps(cu, ensure_ascii=False, indent=0))
        import collections
        c = collections.Counter(v for v in cu.values() if v)
        print(f"\n✅ {sum(1 for v in cu.values() if v)}/{len(cu)} nền có nhóm · "
              f"{len(c)} nhóm khác nhau -> {RA}")
        return
    the, thieu = {}, 0
    for ma, ds in kho.items():
        for i, s in enumerate(ds):
            n = nhom_cua(s, ma)
            if not n:
                thieu += 1
            the[f"{ma}_{i:03d}"] = n
    io.open(RA, "w", encoding="utf-8").write(json.dumps(the, ensure_ascii=False, indent=0))
    import collections
    c = collections.Counter(v for v in the.values() if v)
    print(f"gắn thẻ {len(the)} nền · {thieu} nền không gán được nhóm "
          f"({thieu*100//max(1,len(the))}%)")
    print("  nhóm nhiều nhất:", ", ".join(f"{k}:{v}" for k, v in c.most_common(8)))
    print(f"  -> {RA}")


if __name__ == "__main__":
    main()
