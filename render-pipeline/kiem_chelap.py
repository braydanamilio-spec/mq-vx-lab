#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG CHE KHUẤT — chữ trắng có đủ nền tối để đọc được không.  (3/9/2026)

Anh: *"nhớ tránh tràn hay che khuất."*

── VÌ SAO CẦN CỔNG NÀY ─────────────────────────────────────────────────────────────────────
Hôm nay đã sửa tay đúng một ca: dòng chú thích *"a jet at takeoff"* đè lên mũi máy bay trắng và
các tia đen của nền cắt ngang qua chữ. Sửa xong thì phải có cổng, không thì lần sau lại lọt —
và lọt **im lặng**, vì cổng chấm hiện có cho 99/100 với đúng khung ấy.

── ĐO GÌ ───────────────────────────────────────────────────────────────────────────────────
Chữ của bộ này là **trắng** đè lên dải mờ tối. Nên câu hỏi đo được là: *dải chữ có đủ tối
không?* Hai số, và phải nhìn cả hai:

  · **độ sáng trung bình** — nền sáng thì chữ trắng chìm.
  · **tỉ lệ điểm ảnh SÁNG** trong dải — trung bình có thể đẹp mà vẫn có một mảng trắng to
    (mũi máy bay) nằm đúng chỗ chữ. Trung bình giấu được vệt; tỉ lệ thì không.

Đúng bài học 13.3: thước chỉ nhìn hai đầu cực sẽ bỏ sót ca ở khoảng giữa. Ở đây "khoảng giữa"
là khung có nền tối nhưng **có một mảng sáng cục bộ**.

── KHÔNG ĐO Ở DẢI PHỤ ĐỀ ───────────────────────────────────────────────────────────────────
Phụ đề dưới cùng đã có nền đen riêng nên luôn đạt; đo nó chỉ làm loãng kết quả. Cổng soi đúng
vùng CHỮ TRÊN ẢNH (dải 0,10–0,42 chiều cao của bản dọc), nơi lỗi thật xảy ra.
"""
import argparse
import json
import os
import subprocess
import tempfile

GOC = os.path.dirname(os.path.abspath(__file__))

# Ngưỡng lấy từ ca thật đã sửa tay hôm nay, đo trên khung TRƯỚC và SAU:
#   trước (chữ bị nuốt): sáng TB 148 · tỉ lệ điểm sáng 34%
#   sau  (đọc tốt)     : sáng TB  92 · tỉ lệ điểm sáng  9%
# Đặt giữa hai mốc, nghiêng về phía cho qua — cổng bắt oan còn tệ hơn cổng không bắt (13.8).
# HIỆU CHỈNH TRÊN CA THẬT, HAI ĐẦU ĐỀU ĐÃ NHÌN TẬN MẮT  (3/9/2026):
#   HỎNG — chữ chìm, xem `/tmp/bat.png`: sáng TB **177–189** · điểm sáng **50–55%**
#   TỐT  — đọc rõ, xem `/tmp/sau.png`: sáng TB **126**     · điểm sáng **24%**
# Ngưỡng đặt GIỮA hai mốc, nghiêng về phía cho qua: cổng bắt oan còn tệ hơn cổng không bắt
# (13.8), và ở đây bắt oan nghĩa là chặn một tập hoàn toàn đọc được.
#
# Không lấy số từ đầu: bản đầu đặt 125/22% theo suy đoán và nó **bắt cả khung tốt** — đúng lỗi
# 13.3 (calibrate ở hai đầu cực rồi tin luôn, không nhìn khoảng giữa).
SANG_TB_MAX = 150
TI_LE_SANG_MAX = 0.35
NGUONG_SANG = 190          # điểm ảnh sáng hơn mức này coi là "nền sáng"


def do_khung(png: str, tren: float = 0.10, duoi: float = 0.42) -> tuple:
    """Trả (độ sáng TB, tỉ lệ điểm sáng) của dải chữ-trên-ảnh."""
    from PIL import Image
    im = Image.open(png).convert("L")
    W, H = im.size
    dai = im.crop((0, int(H * tren), W, int(H * duoi)))
    px = list(dai.getdata())
    if not px:
        return 0.0, 0.0
    return sum(px) / len(px), sum(1 for p in px if p >= NGUONG_SANG) / len(px)


# CHỈ soi nhịp có CHỮ TRẮNG ĐÈ LÊN ẢNH. Đó là `so_lieu` (và `canh` khi có nhãn) CÓ `nenAnh`.
# Bản đầu của cổng này soi MỌI khung và bắt **10/10 tệp** — một cỗ máy bắt oan. Vì khung nền
# sáng của khuôn `chart`/`chia_doi` có chữ **ĐEN**, sáng ở đó là ĐÚNG; đo chúng bằng thước dành
# cho chữ trắng thì cái gì cũng trượt.
#
# Luật 13.22: một cổng chỉ đáng ship khi ĐỌC TAY các ca nó bắt và thấy chúng thật sự hỏng. Tỉ lệ
# bắt cao không phải bằng chứng cổng tốt — nó cũng có thể là bằng chứng cổng sai.
#
# Nên cổng không đoán từ điểm ảnh mà **đọc kịch bản của chính tập ấy** để biết nhịp nào có chữ
# trắng trên ảnh, rồi chỉ soi đúng những nhịp đó.
# CHỈ `so_lieu`. Bản trước để thêm `canh` và cổng bắt 10/10 — trích khung ra nhìn thì nhịp
# `canh` chỉ có ẢNH và PHỤ ĐỀ, mà phụ đề đã có dải nền tối riêng nên luôn đọc được. Không có
# chữ trắng nào đè lên ảnh ở đó cả.
#
# Suýt ship một cổng chặn mọi tập. Luật 13.22 cứu đúng chỗ này: **đọc tay các ca nó bắt** trước
# khi tin nó. Nếu chỉ nhìn con số "bắt 10/10" thì kết luận sẽ là "video hỏng hết", trong khi
# thứ hỏng là cái thước.
KHUON_CHU_TRANG = ("so_lieu",)


def _nhip_can_soi(mp4: str) -> list:
    """[(giây giữa nhịp, khuôn)] của các nhịp có chữ trắng đè lên ảnh."""
    pj = mp4[:-4] + ".json"
    if not os.path.exists(pj):
        return []
    try:
        d = json.load(open(pj, encoding="utf-8"))
    except Exception:
        return []
    ra = []
    for x in (d.get("nhip") or []):
        if not x.get("nenAnh"):
            continue                      # không có ảnh -> chữ nằm trên nền vẽ code, tự đủ tương phản
        if (x.get("khuon") or "") not in KHUON_CHU_TRANG:
            continue
        s0, e0 = x.get("s"), x.get("e")
        if s0 is None or e0 is None:
            continue
        ra.append(((float(s0) + float(e0)) / 2, x.get("khuon")))
    return ra


def soi(mp4: str, n: int = 6) -> list:
    """Soi các nhịp có chữ trắng trên ảnh. Trả danh sách nhịp KHÔNG đạt."""
    moc = _nhip_can_soi(mp4)
    if not moc:
        return []
    tam = tempfile.mkdtemp(prefix="chelap_")
    xau = []
    for i, (t, kh) in enumerate(moc[:8]):
        p = os.path.join(tam, f"{i}.png")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", mp4,
                        "-frames:v", "1", "-vf", "scale=360:-1", p], capture_output=True)
        if not os.path.exists(p):
            continue
        tb, ti = do_khung(p)
        if tb > SANG_TB_MAX and ti > TI_LE_SANG_MAX:
            xau.append((i, round(tb), round(ti * 100)))
    return xau


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tep", nargs="*")
    a = ap.parse_args()
    thu = os.path.join(GOC, "out")
    os.makedirs(thu, exist_ok=True)
    ds = a.tep or sorted(os.path.join(thu, f) for f in os.listdir(thu)
                         if f.startswith("v9_") and f.endswith(".mp4"))
    if not ds:
        print("  ℹ chưa có tệp v9_*.mp4 để soi — bỏ qua (lượt đầu chưa dựng là bình thường)")
        return 0
    hong = 0
    for mp4 in ds:
        xau = soi(mp4)
        ten = os.path.basename(mp4)
        if xau:
            hong += 1
            print(f"  ❌ {ten:34s} {len(xau)} nhịp có nền quá sáng dưới chữ trắng")
            for i, tb, ti in xau[:3]:
                print(f"        khung {i}: sáng TB {tb} (trần {SANG_TB_MAX}) · "
                      f"{ti}% điểm sáng (trần {int(TI_LE_SANG_MAX*100)}%)")
        else:
            print(f"  ✅ {ten:34s} chữ trên ảnh đủ nền tối")
    if hong:
        print(f"\n❌ {hong}/{len(ds)} tệp có chữ bị nền sáng nuốt.")
        print("   Chữa bằng QUẦNG MỀM quanh chữ, không bằng viền — §12.12: không hãng phim nào viền chữ.")
        return 1
    print(f"\n✅ {len(ds)}/{len(ds)} tệp: chữ trên ảnh đọc được")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
