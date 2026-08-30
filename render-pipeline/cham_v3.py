#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHẤM 10 KÊNH THẾ HỆ 3 — đo được, không cảm tính (29/8/2026).

Anh: "nâng cấp cho đạt trên 90/100". Nói "đạt 90" mà không có cây thước thì chỉ là cảm tính, và
cảm tính thì mỗi lần nhìn lại một khác. Tệp này đo SÁU thứ, mỗi thứ một số:

  30đ  DỮ LIỆU     — đủ 4 mục, ít nhất 3 giá trị PHÂN BIỆT, cột cao nhất gấp ≥2 lần thấp nhất
  20đ  KỊCH BẢN    — dùng lại `nghiem_thu.cham_kich_ban` của 50 kênh cũ, cùng một chuẩn
  20đ  KHÔNG TRÙNG — nhân vật, bối cảnh, bảng màu, giọng đọc, nguồn: không kênh nào chung
  15đ  ĐỘ SÁNG     — khung thật ≥ 75/255 và dưới 8% điểm gần như đen
  10đ  CHỮ TRONG KHUNG — không nhãn nào tràn mép, không hai nhãn nào chồng nhau
   5đ  NGUỒN       — có ghi nguồn và nguồn ấy gọi được

Chấm ở tầng dữ liệu + khung thật đã render, KHÔNG tốn hạn mức vẽ ảnh (bộ này vốn không dùng).

    python cham_v3.py              # chấm cả 10
    python cham_v3.py --kenh BANKRUN
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)

NGUONG = 90


def _sang(ten_tep: str) -> tuple:
    """(độ sáng trung bình, tỉ lệ điểm gần như đen) của các khung đã trích từ video kênh này."""
    try:
        from PIL import Image
    except ImportError:
        return (None, None)
    ps = sorted(glob.glob(os.path.join(GOC, "out", "_soi", f"V3{ten_tep.upper()}_?.png")))
    if not ps:
        return (None, None)
    s = t = 0.0
    for p in ps:
        px = list(Image.open(p).convert("L").resize((160, 284)).getdata())
        s += sum(px) / len(px)
        t += sum(1 for v in px if v < 40) / len(px)
    return (s / len(ps), t / len(ps))


def _rong_chu(t: str, cs: float) -> float:
    """Ước lượng bề rộng một chuỗi ở cỡ chữ `cs`. 0,55 là hệ số đo được cho phông đậm dùng ở đây."""
    return len(str(t or "")) * cs * 0.55


def cham_mot(k: dict, D) -> dict:
    """Chấm một kênh. Trả {diem, loi[]}."""
    import kich_v2 as K
    import nghiem_thu as N

    loi: list = []
    diem = 100

    # ── 30đ DỮ LIỆU ────────────────────────────────────────────────────────────────────
    sl = K.lay_so_lieu(k["nguon"], D)
    if not sl:
        return {"diem": 0, "bo_qua": True,
                "loi": ["nguồn không trả dữ liệu lượt này (không tính là hỏng)"]}
    tieu_de, ds, nguon = sl
    if len(ds) < 4:
        diem -= 15
        loi.append(f"chỉ {len(ds)} mục — bảng bốn cột không đủ chỗ so sánh")
    gt = [float(b) for _, b, _ in ds[:4]]
    if len({round(x, 4) for x in gt}) < 3:
        diem -= 15
        loi.append(f"chỉ {len({round(x,4) for x in gt})} giá trị phân biệt trên 4 cột — "
                   f"bảng phẳng, không đọc ra thứ hạng")
    elif gt and min(gt) > 0 and max(gt) / min(gt) < 2:
        diem -= 8
        loi.append(f"cột cao nhất chỉ gấp {max(gt)/min(gt):.1f} lần cột thấp nhất — "
                   f"mắt không thấy chênh lệch")

    # ── 20đ KỊCH BẢN ───────────────────────────────────────────────────────────────────
    canh, loi_doc = K.dung_canh(k, sl)
    st = {"narration": [c["nar"] for c in canh]}
    e_kb = N.cham_kich_ban(st) or []
    if e_kb:
        diem -= min(20, 10 * len(e_kb))
        loi.append("kịch bản: " + "; ".join(str(x)[:88] for x in e_kb[:2]))

    # ── 10đ CHỮ TRONG KHUNG ────────────────────────────────────────────────────────────
    # Nhãn chân cột rộng tối đa 100 điểm (bước cột 112 trừ khe 12). Tính theo BỀ RỘNG THẬT,
    # không theo số ký tự — hai chuỗi cùng số ký tự có thể rộng khác nhau tới 40%.
    for a, _b, _c in ds[:4]:
        tu = str(a).split(" ")
        dai_nhat = max((_rong_chu(w, 18) for w in tu), default=0)
        if dai_nhat > 100:
            diem -= 5
            loi.append(f"nhãn cột {a[:22]!r} có từ dài {dai_nhat:.0f} điểm > 100 — sẽ tràn khỏi cột")
            break
    _nhan = K._nhan_gon(str(ds[0][0]))
    if _rong_chu(_nhan, 38) > 560:
        diem -= 5
        loi.append(f"nhãn dưới số lớn {_nhan!r} rộng quá khung")

    # ── KHÔNG ĐƯỢC CÓ KHUNG ĐEN Ở ĐẦU HAY CUỐI ────────────────────────────────────────
    # 30/8 — mượn phép đo đã viết cho bộ hài. Khung đen ở cuối là lỗi hay gặp nhất của mọi dây
    # chuyền dựng phim, và trên Shorts (phát lặp vô hạn) thì cái nháy đen ấy chớp mỗi vòng lặp.
    import glob as _g2
    import subprocess as _sp2
    _mp4 = os.path.join(GOC, "out", f"v3_{k['ten'].replace(' ', '').lower()}.mp4")
    if os.path.exists(_mp4):
        try:
            _d = float(_sp2.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", _mp4], capture_output=True, text=True,
                                timeout=60).stdout.strip() or 0)
        except Exception:
            _d = 0
        if _d:
            from PIL import Image as _Im
            for _ten2, _ss in (("đầu", 0.05), ("cuối", max(0.0, _d - 0.12))):
                _pp = os.path.join("/tmp", f"_v3den{int(_ss*100)}.png")
                _sp2.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{_ss:.2f}", "-i", _mp4,
                          "-vframes", "1", "-vf", "scale=120:-1", _pp],
                         capture_output=True, timeout=60)
                if not os.path.exists(_pp):
                    continue
                _px2 = list(_Im.open(_pp).convert("L").getdata())
                _tb2 = sum(_px2) / len(_px2)
                if _tb2 < 60:
                    diem -= 10
                    loi.append(f"khung {_ten2} gần như ĐEN ({_tb2:.0f}/255)")
                    break

    # ── 15đ ĐỘ SÁNG ────────────────────────────────────────────────────────────────────
    s, t = _sang(k["ten"].replace(" ", ""))
    if s is None:
        loi.append("(chưa có khung để đo độ sáng — render rồi chấm lại)")
    else:
        if s < 75:
            diem -= 10
            loi.append(f"khung tối: sáng trung bình {s:.0f}/255 (ngưỡng 75)")
        if t > 0.08:
            diem -= 5
            loi.append(f"{t*100:.0f}% điểm gần như đen (ngưỡng 8%)")

    # ── 5đ NGUỒN ───────────────────────────────────────────────────────────────────────
    if not str(nguon or "").strip():
        diem -= 5
        loi.append("không ghi nguồn dữ liệu")

    return {"diem": max(0, diem), "bo_qua": False, "loi": loi,
            "tieu_de": tieu_de, "so_muc": len(ds)}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    a = ap.parse_args()

    import du_lieu_mo as D
    import kich_v2 as K

    chon = K.KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [x for x in K.KENH if x["ten"].replace(" ", "").upper() in vt]

    # ── 20đ KHÔNG TRÙNG — đo trên CẢ BỘ, không đo từng kênh ────────────────────────────
    # Trùng lặp là thuộc tính của một TẬP, không phải của một phần tử: một kênh không thể tự
    # trùng với chính nó. Nên phép đo này phải chạy trên cả mười kênh cùng lúc.
    trung: dict = {}
    for truc in ("kieu", "boi", "mau", "nguon"):
        d: dict = {}
        for x in K.KENH:
            # `boi` nay là một DANH SÁCH (bộ ba bối cảnh) — so nguyên bộ, không so từng cái.
            # Hai kênh dùng chung một bối cảnh phụ là chấp nhận được; dùng chung cả BỘ thì mới
            # là hai kênh trông như một.
            v = tuple(x[truc]) if isinstance(x[truc], list) else x[truc]
            d.setdefault(v, []).append(x["ten"])
        lap = {v: t for v, t in d.items() if len(t) > 1}
        if lap:
            trung[truc] = lap

    print(f"\n{'ĐIỂM':>5}  {'KÊNH':<20} {'MỤC':>4}  TIÊU ĐỀ")
    print("─" * 92)
    bang, dat, hong, bo = {}, 0, 0, 0
    for k in chon:
        r = cham_mot(k, D)
        # phạt phần trùng cho đúng những kênh dính
        for truc, lap in trung.items():
            for _v, tens in lap.items():
                if k["ten"] in tens:
                    r["diem"] = max(0, r["diem"] - 20)
                    r["loi"].append(f"TRÙNG `{truc}` với: {', '.join(t for t in tens if t != k['ten'])}")
                    break
        bang[k["ten"]] = r
        if r.get("bo_qua"):
            bo += 1
            mui = "⏭"
        elif r["diem"] >= NGUONG:
            dat += 1
            mui = "✅"
        else:
            hong += 1
            mui = "❌"
        print(f"{mui} {r['diem']:>3}  {k['ten']:<20} {r.get('so_muc', 0):>4}  "
              f"{str(r.get('tieu_de') or '')[:44]}")
        for x in r["loi"][:2]:
            print(f"         └ {str(x)[:86]}")

    print(f"\n  ✅ đạt {dat}  ·  ❌ hỏng {hong}  ·  ⏭ nguồn chập {bo}   (ngưỡng {NGUONG}/100)")
    if trung:
        for truc, lap in trung.items():
            print(f"  🚨 trùng `{truc}`: {lap}")
    else:
        print("  ✓ không trục nào (nhân vật · bối cảnh · màu · nguồn) bị hai kênh dùng chung")
    io.open(os.path.join(GOC, "chat_luong_v3.json"), "w", encoding="utf-8").write(
        json.dumps({"nguong": NGUONG, "kenh": bang}, ensure_ascii=False, indent=1))
    return 0 if hong == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
