#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MƯỜI KÊNH NGƯỜI QUE 15 GIÂY — một pipeline, mười gia đình Mỹ  (1/9/2026)

Anh: *"kiểu người que phong cách chuẩn usa cử chỉ biểu cảm mượt mà, bối cảnh đúng như kịch bản"*.

Gói 15 giây cho mỗi tập BỐN NHỊP, mỗi nhịp một hành động kèm một câu thoại. Đó là thứ engine
truyện tranh không dùng được (nó chỉ có tám tư thế tay tĩnh) mà bộ khung `StickAnim` dùng được
hết: hành động -> tư thế, và lớp `live()` lo phần mượt.

BA ÁNH XẠ, mỗi cái đọc từ chính chữ trong kịch bản chứ không bịa:
  hành động -> TƯ THẾ   ("walks in" -> lean · "points" -> point · "shrugs" -> shrug …)
  lời thoại -> BIỂU CẢM (dấu hỏi -> curious · dấu than -> shock · "sorry" -> sad …)
  lời thoại -> BỐI CẢNH (bếp/nhà -> home · cửa hàng -> store · công viên -> park …)
"""
import argparse
import io
import json
import os
import re
import subprocess

from kich_hai import doc_hai_giong, lam_thumb, GOC, ENG, PUB
from kich_comic import GIONG_VAI, _am_nhac
from chuan_am import chuan

KHO = os.path.join(GOC, "kho_15s.json")

# ── ÁNH XẠ HÀNH ĐỘNG -> TƯ THẾ ────────────────────────────────────────────────────────────
# `StickAnim.POSES`: idle · present · point · shrug · shock · lean · lookaway
TU_THE = [
    (r"\b(point|points|pointing|holds up|shows|hands)\b", "point"),
    (r"\b(walk|walks|enters|appears|comes in|steps)\b", "lean"),
    (r"\b(shrug|shrugs|doesn'?t know|no idea)\b", "shrug"),
    (r"\b(gasp|gasps|shocked|freezes|jumps|drops|stares)\b", "shock"),
    (r"\b(turns away|looks away|ignores|walks by|sighs)\b", "lookaway"),
    (r"\b(holding|carrying|presents|offers|lifts|raises)\b", "present"),
]
CAM_XUC = [
    (r"\?", "curious"), (r"!", "shock"),
    (r"\b(sorry|sad|nothing|never|fail)\b", "sad"),
    (r"\b(great|love|perfect|yes|amazing|nice)\b", "happy"),
    (r"\b(sure|really|right|suspicious|hmm)\b", "suspicious"),
    (r"\b(no|stop|again|seriously|why)\b", "annoyed"),
]
# `SceneBG` có: office · home · street · bank · store · city · park · hospital · lab · gym · room · clean
BOI_CANH = [
    (r"\b(kitchen|fridge|couch|living room|bedroom|garage|laundry|home|house|dinner|breakfast)\b", "home"),
    (r"\b(store|shop|grocery|checkout|aisle|cart|mall|register)\b", "store"),
    (r"\b(office|desk|meeting|work|boss|email|zoom)\b", "office"),
    (r"\b(street|sidewalk|neighbou?r|driveway|car|road|mailbox)\b", "street"),
    (r"\b(park|yard|lawn|outside|garden|bench|walk the dog)\b", "park"),
    (r"\b(doctor|hospital|clinic|nurse|sick|medicine|shot)\b", "hospital"),
    (r"\b(gym|workout|treadmill|weights|exercise)\b", "gym"),
    (r"\b(bank|money|rent|bill|paycheck|loan)\b", "bank"),
    (r"\b(school|class|homework|teacher|test)\b", "room"),
]


def _khop(bang, van: str, mac_dinh: str) -> str:
    v = van.lower()
    for mau, ra in bang:
        if re.search(mau, v):
            return ra
    return mac_dinh


# ── TẠO HÌNH ──────────────────────────────────────────────────────────────────────────────
DA = ["#F6C89A", "#EFC49A", "#D9A878", "#B98A5E", "#8E6240", "#6E4A30"]
TOC = ["#3A2A22", "#2E2018", "#6B4A2A", "#1E1A18", "#8A7A5C", "#B9B2A6"]


def _vai(ten: str, v: dict, i: int) -> dict:
    b = sum(ord(c) * (j + 3) for j, c in enumerate(ten))
    tre = v["tuoi"] in ("tre_con", "tre")
    gia = v["tuoi"] == "gia"
    return {
        "ten": ten,
        # Da và tóc xoay theo băm TÊN VAI: mười gia đình Mỹ đa sắc tộc, và gói tả rõ điều đó —
        # dùng một tông da cho tất cả là làm hỏng đúng thứ khiến bộ này khác biệt.
        "skin": DA[b % len(DA)],
        "hair": "#C9C6C0" if gia else TOC[(b // 5) % len(TOC)],
        "shirt": v["ao"], "pants": v["quan"],
        "hoodie": bool(re.search(r"hoodie|sweatshirt", v.get("mo", ""))),
        "cap": "#D9793C" if re.search(r"\bcap\b|hat", v.get("mo", "")) else None,
        "glasses": bool(re.search(r"glasses|specs", v.get("mo", ""))) or gia,
        # Chiều cao theo tuổi thật — anh đã dặn: con thấp hơn mẹ, ông thấp hơn bố.
        "scale": 0.74 if v["tuoi"] == "tre_con" else 0.88 if v["tuoi"] == "tre"
                 else 0.95 if gia else 1.0,
    }


def _giong(v: dict, i: int) -> tuple:
    ds = GIONG_VAI.get((("tre" if v["tuoi"] == "tre_con" else v["gioi"]), v["tuoi"])) \
        or GIONG_VAI[("nam", "trung")]
    return ds[i % len(ds)]


NHAC = ["music/carefree.mp3", "music/km_undaunted.mp3", "music/forecast.mp3",
        "music/inspired.mp3", "music/km_ascending.mp3", "music/broke_pad.mp3",
        "music/km_interloper.mp3", "music/mind_pad32.mp3", "music/mindloop_pad.mp3",
        "music/km_impact_andante.mp3"]


def mot_tap(de: str, idx: int) -> str:
    kho = json.load(io.open(KHO, encoding="utf-8"))
    if de not in kho:
        print(f"❌ không có kênh {de}")
        return ""
    k = kho[de]
    tap = k["tap"]
    t = tap[idx % len(tap)]
    hat = sum(ord(c) for c in de)
    slug = f"{de}_{idx:04d}"
    print(f"\n▶ {k['ten']} · {t['ten'][:44]}", flush=True)

    nguoi = [n for n, v in k["dan"].items() if not v["thu"]]
    # Hai vai CHÍNH của tập: hai người nói nhiều nhất trong bốn nhịp.
    dem = {}
    for n in t["nhip"]:
        for _c, ai in n["loi"]:
            if ai in nguoi:
                dem[ai] = dem.get(ai, 0) + 1
    thu_tu = sorted(dem, key=lambda x: -dem[x]) or nguoi[:2]
    vA = thu_tu[0]
    vB = next((x for x in thu_tu[1:] if x != vA), next((x for x in nguoi if x != vA), vA))

    cau, ghi = [], []
    for n in t["nhip"]:
        for c, ai in n["loi"]:
            cau.append((c, 0 if ai == vA else 1, "trung_tinh"))
            ghi.append((n, c, ai))
    if len(cau) < 2:
        print("   ⏭ dưới hai lượt thoại — bỏ")
        return ""

    ga, gb = _giong(k["dan"][vA], hat), _giong(k["dan"][vB], hat + 3)
    rel = f"v8_{slug}.mp3"
    try:
        dur, tu, moc = doc_hai_giong(cau, ga, gb, os.path.join(PUB, rel))
    except Exception as e:
        print(f"   ❌ giọng đọc hỏng: {str(e)[:110]}")
        return ""
    if not tu:
        print("   ❌ không có mốc từ — BỎ")
        return ""

    # 1/9 — DÁNG PHẢI ĐỔI THEO NHỊP. Soi khung bốn nhịp ra bốn hình giống hệt nhau: `_khop`
    # dò `hanh` không thấy mẫu nào thì lặng lẽ trả "present", mà `hanh` của một tập thường viết
    # na ná nhau -> cả bốn nhịp cùng "present". Đúng họ lỗi "rơi về mặc định trong im lặng":
    # không có lỗi nào báo, chỉ có video nhạt.
    # Ba tầng, tầng sau chỉ dùng khi tầng trước KHÔNG khớp thật:
    #   1. hành động của nhịp   2. lời thoại của nhịp   3. xoay vòng theo số thứ tự nhịp
    # Tầng 3 không "đoán bừa" — nó chỉ bảo đảm hai nhịp liền nhau không trùng bóng dáng.
    VONG = ["present", "point", "lean", "shrug", "lookaway"]
    def _dang(n, c, i):
        d = _khop(TU_THE, n["hanh"], "")
        if not d:
            d = _khop(TU_THE, c, "")
        return d or VONG[i % len(VONG)]

    nhip = []
    truoc = ""
    for i, (n, c, ai) in enumerate(ghi):
        van = f"{n['hanh']} {c}"
        nhip.append({
            "s": moc[i][0], "e": moc[i][1] + (0.25 if i == len(ghi) - 1 else 0.02),
            "bg": _khop(BOI_CANH, van, "home"),
            "hanh": n["hanh"][:90],
            "ai": 0 if ai == vA else 1,
            "nar": c,
            "pose": (lambda d: d if d != truoc else VONG[(VONG.index(d) + 2) % len(VONG)]
                     if d in VONG else d)(_dang(n, c, i)),
            "expr": _khop(CAM_XUC, c, "neutral"),
            "hai": True,
        })
        truoc = nhip[-1]["pose"]

    props = {
        "nhip": nhip, "tu": tu, "voMp3": rel, "nhac": NHAC[hat % len(NHAC)],
        "nhacVol": _am_nhac(NHAC[hat % len(NHAC)]),
        "vaiA": _vai(vA, k["dan"][vA], 0), "vaiB": _vai(vB, k["dan"][vB], 1),
        "tieuDe": k["ten"].upper(), "handle": "@" + de + "usa",
        "mau": "#E0533D", "mauPhu": "#2F7D6B",
        "hook": (cau[0][0].rstrip("?.!").upper())[:34],
    }
    pj = os.path.join(GOC, "out", f"v8_{slug}.json")
    os.makedirs(os.path.dirname(pj), exist_ok=True)
    io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))

    out = os.path.join(GOC, "out", f"v8_{slug}.mp4")
    r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "KichQue", out,
                        f"--props={pj}", "--gl=swiftshader", "--log=error", "--crf", "21"],
                       cwd=ENG, capture_output=True, text=True, timeout=2400)
    if r.returncode or not os.path.exists(out):
        print(f"   ❌ render hỏng: {(r.stderr or r.stdout or '')[-240:]}")
        return ""

    lam_thumb(out, t["ten"], k["ten"], "#E0533D", os.path.join(GOC, "out", f"v8_{slug}.jpg"))
    am = chuan(out)
    print(f"   ✅ {os.path.basename(out)} ({os.path.getsize(out)/1e6:.1f} MB · {dur:.1f}s · "
          f"{len(nhip)} nhịp{' · ' + am if am else ''})")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--tu", type=int, default=0)
    ap.add_argument("--so", type=int, default=1)
    a = ap.parse_args()
    kho = json.load(io.open(KHO, encoding="utf-8"))
    ds = [x.strip() for x in a.kenh.split(",") if x.strip()] or list(kho)
    ra = [v for de in ds for i in range(a.so) if (v := mot_tap(de, a.tu + i))]
    print(f"\n✅ {len(ra)}/{len(ds) * a.so} video")
    return 0 if ra else 1


if __name__ == "__main__":
    raise SystemExit(main())
