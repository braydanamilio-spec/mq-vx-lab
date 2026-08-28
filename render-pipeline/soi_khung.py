#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRÍCH KHUNG THÀNH BẢNG SOI — để đọc bằng MẮT nhiều kênh một lượt (29/8/2026).

VÌ SAO KHÔNG PHẢI LÀ MỘT BỘ CHẤM ĐIỂM
-------------------------------------
Bản đầu của tệp này chấm điểm bố cục bằng pixel: mật độ mực từng dải ngang (bắt chữ đè chữ), tỉ lệ
dải trống (bắt khung rỗng), tương phản chữ/nền (bắt chữ loá). Nghe hợp lý. Đo thật trên năm video
— gồm cả bản tôi đã soi bằng mắt và thấy sạch — thì:

    PRICE OF NOW (sạch)      dải đặc 42,7 · trống 33,3 · tương phản 6,6
    COST TO GO   (rỗng, xấu) dải đặc 40,8 · trống 66,7 · tương phản 3,1
    STEAM TRUTH  (sạch)      dải đặc 42,5 · trống 54,2 · tương phản 6,3

Cả ba phép đo cho cùng một dải số ở cả video tốt lẫn video hỏng. "Dải đặc" chỉ đang đo một hàng
cột bình thường của biểu đồ, không đo chữ chồng chữ. "Tương phản" lấy phân vị 97 so với trung vị,
mà trong một khung đầy cột màu thì phân vị 97 là một cái cột chứ không phải chữ.

Tôi đã dựng một cái thước cho ra cùng một số với mọi thứ nó đo — đúng thứ tôi phê bình cả phiên
này ở `cham_kenh.py` và ở phép đo "độ sáng trung bình" từng làm nền chói. Giữ nó lại thì nó thành
một cổng xanh vô nghĩa, tệ hơn không có cổng: nó dạy người đọc tin vào một con số rỗng.

Muốn đo thật thì phải khoanh được vùng CHỮ trước đã (nhận dạng chữ, hoặc engine tự khai toạ độ
từng khối ra một tệp kèm theo). Đó là việc đáng làm, nhưng là việc khác.

Trong lúc chưa có, thứ đã bắt được MỌI lỗi bố cục hôm nay là mắt người: tiêu đề ba mảnh, .XXX
trong bảng, "33 poi", đồng hồ "20260741", hook đè biểu đồ, nền chói — không lỗi nào bị máy bắt,
tất cả đều thấy ngay khi nhìn. Nên tệp này làm đúng một việc và làm cho tốt: gom nhiều khung của
nhiều kênh vào MỘT tấm ảnh, để nhìn 15 kênh mất công bằng nhìn một.

    python soi_khung.py --kenh SKYRIGHTNOW,STEAMTRUTH --khong-render
    python soi_khung.py --dang mapped,ranked,scaled,race,longshot,thennow
"""
from __future__ import annotations

import glob
import io
import json
import os
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)

# Ba mốc: sau mở đầu · giữa thân · gần cuối. Soi một khung là gần như chắc chắn bỏ sót — đã tự
# vấp: khung t=14 của một video trông sạch, khung t=28 của CHÍNH nó có hai bản tiêu đề chồng nhau.
MOC = (0.30, 0.62, 0.88)
RA = os.path.join(GOC, "out", "_soi")


def _thoi_luong(mp4: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "json", mp4], capture_output=True, text=True, timeout=60)
    try:
        return float(json.loads(r.stdout or "{}").get("format", {}).get("duration") or 0)
    except Exception:
        return 0.0


def trich(mp4: str, nhan: str) -> list:
    """Ba khung của một video, đã ghi nhãn tên kênh + mốc giây lên góc."""
    dur = _thoi_luong(mp4)
    if dur < 5:
        return []
    os.makedirs(RA, exist_ok=True)
    ra = []
    for i, m in enumerate(MOC):
        p = os.path.join(RA, f"{nhan}_{i}.png")
        # Thu nhỏ còn 1/3 để một tấm bảng chứa được nhiều kênh mà vẫn đọc được chữ tiêu đề.
        r = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{dur * m:.2f}", "-i", mp4,
             "-frames:v", "1", "-vf",
             f"scale=360:-1,drawtext=text='{nhan} {dur * m:.0f}s':x=6:y=6:fontsize=15:"
             f"fontcolor=yellow:box=1:boxcolor=black@0.75:boxborderw=4",
             p], capture_output=True, timeout=120)
        if r.returncode != 0:   # máy thiếu libfreetype -> trích trần, không nhãn
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{dur * m:.2f}", "-i", mp4,
                            "-frames:v", "1", "-vf", "scale=360:-1", p],
                           capture_output=True, timeout=120)
        if os.path.exists(p):
            ra.append(p)
    return ra


def ghep(anhs: list, ra: str, cot: int = 6) -> bool:
    """Xếp mọi khung thành MỘT tấm lưới. Đây là toàn bộ giá trị của tệp: nhìn 15 kênh mất công
    bằng nhìn một."""
    if not anhs:
        return False
    from PIL import Image
    ims = [Image.open(x).convert("RGB") for x in anhs]
    w = max(i.width for i in ims)
    h = max(i.height for i in ims)
    hang = (len(ims) + cot - 1) // cot
    bang = Image.new("RGB", (w * min(cot, len(ims)), h * hang), (16, 16, 20))
    for k, im in enumerate(ims):
        bang.paste(im, ((k % cot) * w, (k // cot) * h))
    bang.save(ra)
    return True


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--dang", default="", help="mapped,ranked,... — mỗi dạng một kênh mẫu")
    ap.add_argument("--khong-render", dest="kr", action="store_true")
    ap.add_argument("--ra", default=os.path.join(RA, "bang_soi.png"))
    a = ap.parse_args()

    import the_he_2 as T
    ks = json.load(io.open(os.path.join(GOC, "kenh_the_he_2.json"), encoding="utf-8"))
    ks = ks if isinstance(ks, list) else list(ks.values())
    chon = []
    if a.kenh:
        can = {x.strip().upper() for x in a.kenh.split(",") if x.strip()}
        chon = [k for k in ks if str(k["ten"]).replace(" ", "").upper() in can]
    elif a.dang:
        for d in [x.strip() for x in a.dang.split(",") if x.strip()]:
            m = next((k for k in ks if k.get("dinh_dang") == d), None)
            if m:
                chon.append(m)
    if not chon:
        print("❌ cần --kenh hoặc --dang")
        return 2

    anhs = []
    for k in chon:
        ten = str(k["ten"])
        nhan = ten.replace(" ", "")[:14]
        mp4 = None
        if not a.kr:
            print(f"▶ render {ten} [{k['dinh_dang']}] …", flush=True)
            try:
                r = T.chay_chung(k, ky=dict(k.get("tham_so") or {}))
            except Exception as ex:
                print(f"   ❌ render ném {type(ex).__name__}: {str(ex)[:80]}")
                continue
            if not r:
                print("   ⚠️ không ra tệp (nguồn chập hoặc bị cổng chặn)")
                continue
            mp4 = r[0] if isinstance(r, (tuple, list)) else r
        else:
            dang = k["dinh_dang"]
            mau = "th2r_*" if dang == "race" else f"th2_{dang}_*"
            g = sorted(glob.glob(os.path.join(GOC, "out", mau)), key=os.path.getmtime)
            g = [x for x in g if x.endswith(".mp4")
                 and nhan.lower()[:9] in os.path.basename(x).lower()]
            mp4 = g[-1] if g else None
        if not (mp4 and os.path.exists(mp4)):
            print(f"   ⚠️ {ten}: không có tệp để soi")
            continue
        got = trich(mp4, nhan)
        anhs += got
        print(f"   ✓ {ten}: {len(got)} khung")

    if not ghep(anhs, a.ra, cot=len(MOC)):
        print("❌ không trích được khung nào")
        return 1
    print(f"\n🖼  {a.ra}  ({len(anhs)} khung · {len(anhs) // len(MOC)} kênh)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
