#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CÂN ÂM LƯỢNG NHẠC NỀN — mỗi tệp một hệ số, không dùng chung một hằng (31/8/2026)

Anh: *"nhạc nền em chưa hề soi — 10 bản khác nhau nhưng chưa ai nghe thử xem có át giọng
không."*

Đo ra thì đúng là hỏng, và hỏng theo đúng họ lỗi đã trả giá nhiều lần: **một hằng phục vụ
hai thứ biến thiên độc lập**. Engine để `volume={0.16}` cho cả 10 tệp, trong khi độ to gốc của
chúng trải từ −12,1 đến −38,3 LUFS — chênh **26 dB**. Hệ quả: OFFICE (wallpaper.mp3, −12,1)
nhạc gần bằng giọng, còn DATING (km_reawakening.mp3, −38,3) coi như không có nhạc. Không có
lỗi nào được ném ra, nên nó sống sót qua mọi cổng.

Giọng edge-tts rất đều: −19,8 LUFS. Nhạc nền cho lời thoại nên nằm dưới giọng 16–18 dB — đủ
để có không khí, không đủ để tranh chỗ. Chọn mốc −37 LUFS.

    hệ số = 10 ^ ((MOC − đo được) / 20)

Ra `engine-remotion/public/music/am_luong.json`. Chạy lại khi thêm nhạc mới.
"""
import io
import json
import os
import re
import subprocess

GOC = os.path.dirname(os.path.abspath(__file__))
NHAC_DIR = os.path.join(GOC, "..", "engine-remotion", "public", "music")
RA = os.path.join(NHAC_DIR, "am_luong.json")

MOC = -37.0        # LUFS đích cho nhạc nền
GIONG = -19.8      # LUFS của giọng đọc, đo trên 6 tệp v4/v5
TRAN = 1.6         # không khuếch đại quá mức này


def do_lufs(d: str):
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", d, "-af", "ebur128=framelog=quiet",
         "-f", "null", "-"],
        capture_output=True, text=True)
    m = re.search(r"Integrated loudness[\s\S]{0,200}?I:\s*(-?[\d.]+)\s*LUFS", r.stderr)
    return float(m.group(1)) if m else None


def main() -> int:
    ra = {}
    for t in sorted(os.listdir(NHAC_DIR)):
        if not t.lower().endswith((".mp3", ".m4a", ".wav")):
            continue
        # Hiệu ứng tiếng không phải nhạc nền: chúng cần nghe RÕ đúng một nhịp, cân về mốc nền
        # là làm chúng biến mất. Để ngoài bảng cho khỏi ai lỡ tra nhầm.
        if t.startswith("sfx_"):
            continue
        L = do_lufs(os.path.join(NHAC_DIR, t))
        if L is None:
            print(f"  ⚠️ {t}: không đo được")
            continue
        hs = min(TRAN, round(10 ** ((MOC - L) / 20), 3))
        ra[t] = hs
        canh = "" if 0.05 <= hs <= 1.2 else "  (lệch xa mốc cũ 0.16)"
        print(f"  {t:24s} {L:7.1f} LUFS -> hệ số {hs:5.3f}{canh}")

    io.open(RA, "w", encoding="utf-8").write(json.dumps(ra, ensure_ascii=False, indent=1))
    print(f"\n  ✅ {len(ra)} tệp -> music/am_luong.json (mốc {MOC} LUFS, dưới giọng {GIONG - MOC:.0f} dB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
