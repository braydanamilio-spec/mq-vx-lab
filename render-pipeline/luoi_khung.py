#!/usr/bin/env python3
"""Ghép khung của NHIỀU video thành một tấm lưới để soi bằng mắt trong một lượt.

31/8 — Anh dặn kiểm QC visual THỰC cho cả bảy mươi kênh. Soi từng video một là bất khả: bảy
mươi video × ba khung là hai trăm mười tấm ảnh, và nhìn rời rạc thì không thấy được thứ quan
trọng nhất — sự KHÁC BIỆT giữa các kênh. Lỗi hệ thống (mọi kênh cùng một bố cục, cùng một
khoảng trống, cùng một chỗ bị cắt) chỉ hiện ra khi các khung nằm cạnh nhau.

Nên xếp lưới: mỗi kênh một ô, tên kênh ghi dưới. Một tấm nhìn được mười hai kênh, và bất
thường lộ ra ngay vì mắt so sánh giỏi hơn nhiều so với đọc số.
"""
import io, os, subprocess, sys, glob

GOC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(GOC, "out")


def khung(mp4: str, phan: float = 0.5, rong: int = 300) -> str:
    """Một khung ở vị trí `phan` (0..1) của video."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", mp4], capture_output=True, text=True)
        dai = float((r.stdout or "0").strip() or 0)
    except Exception:
        return ""
    if dai < 1:
        return ""
    d = os.path.join(OUT, "_luoi")
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, f"{os.path.splitext(os.path.basename(mp4))[0]}-{int(phan*100)}.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{dai*phan:.1f}", "-i", mp4,
                    "-frames:v", "1", "-vf", f"scale={rong}:-1", f], capture_output=True)
    return f if os.path.exists(f) else ""


def luoi(mp4s: list, ra: str, cot: int = 4, phan: float = 0.5, rong: int = 300) -> str:
    from PIL import Image, ImageDraw
    anh = []
    for m in mp4s:
        f = khung(m, phan, rong)
        if f:
            anh.append((os.path.splitext(os.path.basename(m))[0], Image.open(f)))
    if not anh:
        return ""
    w = max(i.width for _, i in anh)
    h = max(i.height for _, i in anh)
    NHAN = 22
    hang = (len(anh) + cot - 1) // cot
    canvas = Image.new("RGB", (cot * w, hang * (h + NHAN)), (16, 16, 20))
    d = ImageDraw.Draw(canvas)
    for i, (ten, im) in enumerate(anh):
        x, y = (i % cot) * w, (i // cot) * (h + NHAN)
        canvas.paste(im, (x, y))
        d.text((x + 6, y + h + 4), ten.replace("v3_", "").replace("v4_", ""), fill=(210, 210, 220))
    canvas.save(ra)
    return ra


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Ghép khung nhiều video thành lưới để soi.")
    ap.add_argument("--mau", default="v3_*.mp4", help="mẫu tên tệp trong out/")
    ap.add_argument("--ra", default="")
    ap.add_argument("--cot", type=int, default=4)
    ap.add_argument("--phan", type=float, default=0.5, help="vị trí khung, 0..1")
    ap.add_argument("--moi-nhat", type=int, default=0, help="chỉ lấy N video mới nhất")
    a = ap.parse_args()
    fs = sorted(glob.glob(os.path.join(OUT, a.mau)), key=os.path.getmtime)
    if a.moi_nhat:
        fs = fs[-a.moi_nhat:]
    ra = a.ra or os.path.join(OUT, "_luoi", f"luoi-{int(a.phan*100)}.png")
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    f = luoi(fs, ra, a.cot, a.phan)
    print(f"  {'✅ ' + f if f else '❌ không có video nào'}  ({len(fs)} video)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
