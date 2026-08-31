#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINH TẬP DÀI — MỘT VỤ VIỆC TRONG MỘT NGÀY (31/8/2026)
════════════════════════════════════════════════════════════════════════════════════════════

`kich_comic_long.py` hiện nối mẩu rời theo cửa sổ trượt. Nó cho ra một video chín phút, nhưng
về bản chất vẫn là compilation — và compilation rơi thẳng vào chính sách nội dung tái sử dụng
mà anh vẫn lo. Mười bốn mẩu không liên quan nhau, nối lại, thì vẫn là mười bốn mẩu không liên
quan nhau.

Thứ tách "video dài hợp lệ" khỏi "video dài bị gắn cờ" không phải độ dài, cũng không phải chất
lượng từng mẩu — mà là **có một mạch chạy suốt**. Tệp này sinh mạch ấy:

  1. ĐỀ CƯƠNG (một lượt gọi): A đang cố làm xong MỘT việc cụ thể trong một ngày. Mô hình nghĩ
     ra việc ấy, rồi liệt kê 10–14 trở ngại nối tiếp — mỗi trở ngại là hậu quả của cách A xử
     lý trở ngại trước, không phải một danh sách rời.
  2. CẢNH (ba tới bốn lượt gọi, mỗi lượt 4 cảnh): viết thoại cho từng trở ngại, có kèm bối
     cảnh chọn từ danh sách engine vẽ được.
  3. CALLBACK: cảnh cuối phải gọi lại cảnh đầu — thứ mà một chuỗi mẩu rời không bao giờ có.

Chia làm nhiều lượt gọi thay vì một lượt dài: một lượt sinh cả mười bốn cảnh thì mô hình quên
mất mạch ở giữa chừng và các cảnh cuối trôi thành mẩu rời — đúng thứ đang muốn tránh.
"""
import os
import io
import json
import time
import argparse

from kich_hai import KENH, GOC
from kich_comic import VAI
from sinh_kich_ban import _hoi_ai, _doc_json, _chuan_hoa

KHO_DAI = os.path.join(GOC, "kho_dai.json")


def _de_cuong(k: dict, keys, so_canh: int, cam: list) -> dict:
    va, vb = VAI[k["de"]]
    noi = []
    try:
        noi = json.load(io.open(os.path.join(GOC, "noi_chon.json"), encoding="utf-8")).get(k["de"], [])
    except Exception:
        pass
    tranh = ("\nEpisode premises already used — do not reuse:\n"
             + "\n".join(f"- {x}" for x in cam[-20:]) + "\n") if cam else ""
    hoi = f"""You are the writer of an American animated comedy series: {k['ten']}.

Characters (they never change):
  A = {va[5]}
  B = {vb[5]}
{tranh}
Plan ONE FULL EPISODE. Not a set of sketches — one continuous story across a single day.

The spine: A is trying to get ONE specific thing done. State it in a sentence. Then list
{so_canh} obstacles in order. Each obstacle must be a CONSEQUENCE of how A handled the previous
one — if the obstacles could be shuffled without anyone noticing, the episode is a compilation
and you have failed the task.

The last obstacle must call back to the first one, so the ending lands on something the
audience saw at the start.

Available locations (use only these exact labels):
{chr(10).join('- ' + x for x in noi)}

Return STRICT JSON:
{{"viec": "the one thing A is trying to get done",
  "tua": "episode title, 3-6 words",
  "canh": [{{"stt": 1, "tro_ngai": "one sentence", "noi": "exact label"}}, ...]}}"""
    return _doc_json(_hoi_ai(hoi, keys)) or {}


def _viet_canh(k: dict, keys, dc: dict, nhom: list) -> list:
    va, vb = VAI[k["de"]]
    ds = "\n".join(f"{c['stt']}. {c['tro_ngai']} (at {c.get('noi','')})" for c in nhom)
    hoi = f"""Series: {k['ten']}. A = {va[5]}, B = {vb[5]}.
Episode: A is trying to {dc.get('viec','')}.

Write the dialogue for these scenes, in order:
{ds}

For each scene: EXACTLY 6 lines, alternating A and B, starting with A. Every line under 12 words.
The humour comes from the situation and from both characters being consistent — never from puns,
and nobody is stupid.

Each scene must move the episode forward: by its last line, something has changed that makes the
NEXT obstacle inevitable. A scene that could be deleted without breaking the chain is a bad scene.

Use only plain ASCII.

Return STRICT JSON:
{{"canh": [{{"stt": 1,
             "loi": [["line", 0, "emotion"], ["line", 1, "emotion"], ...]}}, ...]}}
emotion is one of: trung_tinh, vui, buon, so, tuc, bat_ngo, nghi_ngo, tu_tin."""
    d = _doc_json(_hoi_ai(hoi, keys)) or {}
    return d.get("canh", []) or []


def sinh_tap(k: dict, keys, so_canh: int = 12) -> dict:
    kho = {}
    if os.path.exists(KHO_DAI):
        kho = json.load(io.open(KHO_DAI, encoding="utf-8"))
    cam = [t.get("viec", "") for t in kho.get(k["de"], [])]

    print(f"   → đề cương ({so_canh} cảnh) …", flush=True)
    dc = _de_cuong(k, keys, so_canh, cam)
    if not dc.get("canh"):
        print("   ❌ không dựng được đề cương")
        return {}
    print(f"     việc: {dc.get('viec','')[:70]}")

    SACH = {"‘": "'", "’": "'", "“": '"', "”": '"',
            "‑": "-", "–": "-", "—": "-", "…": "...", " ": " "}
    canh_ra = []
    for i in range(0, len(dc["canh"]), 4):
        nhom = dc["canh"][i:i + 4]
        print(f"   → thoại cảnh {nhom[0]['stt']}–{nhom[-1]['stt']} …", flush=True)
        for c in _viet_canh(k, keys, dc, nhom):
            loi = []
            for x in c.get("loi", []):
                if not (isinstance(x, list) and len(x) >= 3):
                    continue
                chu = str(x[0])
                for a_, b_ in SACH.items():
                    chu = chu.replace(a_, b_)
                chu = " ".join(chu.split()).strip()
                if 4 <= len(chu) <= 96 and chu.isascii():
                    loi.append([chu, 1 if int(x[1]) else 0, str(x[2])])
            if len(loi) < 4:
                continue
            g = next((y for y in dc["canh"] if y["stt"] == c.get("stt")), {})
            canh_ra.append({"stt": c.get("stt"), "loi": loi, "noi": g.get("noi", ""),
                            "tro_ngai": g.get("tro_ngai", "")})
        time.sleep(0.4)

    if len(canh_ra) < max(6, so_canh // 2):
        print(f"   ❌ chỉ viết được {len(canh_ra)}/{so_canh} cảnh — bỏ tập này")
        return {}
    return {"viec": dc.get("viec", ""), "tua": dc.get("tua", ""), "canh": canh_ra}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--so", type=int, default=1, help="số TẬP dài cần sinh cho mỗi kênh")
    # 28 cảnh × 6 lượt × 3,1 giây ≈ 8,7 phút — vừa qua ngưỡng bật quảng cáo giữa video (8
    # phút). 12 cảnh × 4,3 lượt chỉ ra 2,7 phút, tức chưa tới một phần ba chỗ cần.
    ap.add_argument("--canh", type=int, default=28)
    a = ap.parse_args()

    import the_he_2 as T2
    keys = T2.keys_cuc_bo() or None
    if not keys:
        print("❌ không có khoá AI")
        return 2

    chon = KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [x for x in KENH if x["ten"].replace(" ", "").upper() in vt]

    kho = {}
    if os.path.exists(KHO_DAI):
        kho = json.load(io.open(KHO_DAI, encoding="utf-8"))
    moi = 0
    for k in chon:
        print(f"\n▶ {k['ten']}", flush=True)
        for _ in range(a.so):
            t = sinh_tap(k, keys, a.canh)
            if not t:
                continue
            kho.setdefault(k["de"], []).append(t)
            moi += 1
            n_luot = sum(len(c["loi"]) for c in t["canh"])
            print(f"   ✅ {t.get('tua','')} · {len(t['canh'])} cảnh · {n_luot} lượt "
                  f"(~{n_luot * 3.1 / 60:.1f} phút)")
            io.open(KHO_DAI, "w", encoding="utf-8").write(
                json.dumps(kho, ensure_ascii=False, indent=1))

    print(f"\n{'✅' if moi else '⚠️'} thêm {moi} tập dài · kho "
          f"{sum(len(v) for v in kho.values())} tập")
    return 0 if moi else 1


if __name__ == "__main__":
    raise SystemExit(main())
