#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SIÊU DỮ LIỆU CHO 18 KÊNH GIẢI THÍCH — tiêu đề/mô tả/thẻ cho ba nền tảng.  (1/9/2026)

`giai_thich.py` sinh `.mp4` + `.jpg` + `.json`. Thiếu `.tai.json` là **có video mà không đăng
được** — đúng điều luật §10.3 đã ghi, và là trạng thái của bộ này cho tới hôm nay.

── VÌ SAO KHÔNG GỌI AI VIẾT TIÊU ĐỀ ────────────────────────────────────────────────────────
Nội dung bộ này là SỰ THẬT TÍNH ĐƯỢC: mỗi tập có sẵn con số, đơn vị và câu chốt trong `.json`.
Tiêu đề hay nhất của thể loại này chính là câu hỏi mà con số trả lời — thứ đã nằm sẵn trong dữ
liệu. Gọi AI để viết lại nó là thêm một chỗ hỏng (hạn mức, mạng, kiểm duyệt) để đổi lấy một câu
kém chính xác hơn. Nên: dựng thẳng từ dữ liệu, chạy được cả khi mọi khoá đều cạn.

── BA BỘ CHỮ, KHÔNG PHẢI MỘT BỘ DÙNG BA NƠI ───────────────────────────────────────────────
YouTube đọc tiêu đề như câu hỏi tìm kiếm; Facebook đọc dòng đầu như một lời kể; Instagram đọc
thẻ. Dán một bộ chữ vào cả ba là cách chắc chắn để không nơi nào hợp.

── `dang_duoc` PHẢI TÍNH, KHÔNG ĐƯỢC MẶC ĐỊNH TRUE ─────────────────────────────────────────
Reels Instagram chặn video quá 90 giây. Bản dài 9 phút đăng lên đó là một lượt hỏng lặng lẽ —
API nhận, rồi bỏ. Nên tính bằng ĐỘ DÀI THẬT đọc từ tệp, và ghi rõ lý do vào `khong_dang_vi`.
"""
import argparse
import glob
import io
import json
import os
import subprocess

GOC = os.path.dirname(os.path.abspath(__file__))
RA = os.path.join(GOC, "out")
IG_TOI_DA = 90.0            # giây — trần Reels


def _dai(mp4: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", mp4], capture_output=True, text=True)
    try:
        return round(float(r.stdout.strip()), 1)
    except Exception:
        return 0.0


def _cau_hoi(p: dict, ten: str) -> str:
    """Câu hỏi mà tập này trả lời — lấy từ nhịp có con số ĐẦU TIÊN, vì đó là câu chốt."""
    for n in p.get("nhip", []):
        if n.get("so") and n.get("don"):
            return f"{n['so']} {n['don']}".strip()
    return ten


def _lam(mp4: str) -> dict:
    p = json.load(io.open(mp4.replace(".mp4", ".json"), encoding="utf-8"))
    ten = str(p.get("tieuDe") or "").strip()
    handle = str(p.get("handle") or "").strip()
    # MÃ KÊNH lấy từ TÊN TỆP, không suy từ tên hiển thị. `day_kho.py` trước đó suy mã bằng cách
    # bỏ dấu cách trong tên hiển thị: "HOW MUCH IS A BILLION" -> "HOWMUCHISABILLION", trong khi
    # `channels.yaml` dùng mã ngắn "HOWMUCH". Kết quả: 0/68 video vào được hàng đợi đăng, và bước
    # ấy vẫn trả về 0 (xanh). Ghi mã ra đây thì không khâu nào phải đoán nữa.
    ma = os.path.basename(mp4)[3:].split("_")[0].upper()
    slug = os.path.basename(mp4)[3:].replace(".mp4", "")
    long = "_long" in mp4
    giay = _dai(mp4)
    loi = [str(n.get("loi") or "").strip() for n in p.get("nhip", []) if n.get("loi")]
    chot = _cau_hoi(p, ten)

    # Tiêu đề YouTube: TÊN KÊNH đứng trước làm câu hỏi, con số đứng sau làm lời hứa. Short thêm
    # `#shorts` vì YouTube phân loại bằng thẻ ấy, không bằng tỉ lệ khung.
    tieu_yt = f"{ten}? {chot}" + ("" if long else " #shorts")
    # Facebook: dòng đầu là câu hook, không phải tên kênh — bảng tin cắt sau ~80 ký tự.
    tieu_fb = loi[0] if loi else ten
    the = [w.lower() for w in ten.split() if len(w) > 2][:4]
    ht = " ".join("#" + w for w in the) + " #explained #usa" + ("" if long else " #shorts")

    mo_ta = "\n\n".join([
        " ".join(loi[:3]),
        " ".join(loi[3:8]) if len(loi) > 3 else "",
        f"New episodes on {handle} — {ten.lower()}, answered with real numbers.",
    ]).strip()

    # dang_duoc TÍNH bằng độ dài thật, và ghi lý do khi từ chối.
    ig_ok = giay <= IG_TOI_DA
    vi = {} if ig_ok else {"instagram": f"Reels chặn quá {IG_TOI_DA:.0f}s (tập này {giay:.0f}s)"}

    return {
        "ma": ma,
        "video": os.path.basename(mp4),
        "thumbnail": os.path.basename(mp4).replace(".mp4", ".jpg"),
        "kenh": ten, "handle": handle, "slug": slug,
        "loai": "long" if long else "short",
        "giay": giay, "khung_hinh": "16:9" if long else "9:16",
        "dang_duoc": {"youtube": True, "facebook": True, "instagram": ig_ok},
        "khong_dang_vi": vi,
        "youtube":   {"title": tieu_yt[:100], "description": mo_ta, "tags": the + ["explained", "facts"]},
        "facebook":  {"title": tieu_fb[:120], "description": mo_ta + "\n\n" + ht},
        "instagram": {"title": (loi[0] if loi else ten)[:120], "description": (loi[0] if loi else ten) + "\n\n" + ht},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tep", nargs="*")
    a = ap.parse_args()
    ds = a.tep or sorted(glob.glob(os.path.join(RA, "v9_*.mp4")))
    n = 0
    for mp4 in ds:
        if not os.path.exists(mp4.replace(".mp4", ".json")):
            print(f"  ⚠ {os.path.basename(mp4)}: không có .json, bỏ qua")
            continue
        d = _lam(mp4)
        p = mp4.replace(".mp4", ".tai.json")
        io.open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1))
        kh = ",".join(k for k, v in d["dang_duoc"].items() if v)
        print(f"  ✅ {os.path.basename(p):32s} {d['loai']:5s} {d['giay']:6.1f}s -> {kh}")
        n += 1
    print(f"\n✅ {n} tệp .tai.json")
    return 0 if n else 1


if __name__ == "__main__":
    raise SystemExit(main())
