#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHUẨN ÂM ĐẦU RA — đưa mọi video về mốc phát của nền tảng (31/8/2026)

YouTube chuẩn hoá mọi video về **−14 LUFS**: to hơn thì nó hạ xuống, NHỎ HƠN THÌ NÓ ĐỂ NGUYÊN.
Video của ta đo được −20,9 LUFS — thấp hơn mốc 7 dB, nên khi phát trong feed nó nhỏ hơn hẳn
mọi video xung quanh. Người xem không phân tích được vì sao, họ chỉ thấy video này "yếu hơn"
và lướt qua. Đây là khoảng cách đo được mà kênh chuyên nghiệp không bao giờ có, và nó không
tốn gì để đóng.

Facebook và Instagram cũng chuẩn hoá quanh −14 LUFS, nên một mốc dùng chung cho cả ba nền tảng
`dang_duoc` của `sieu_du_lieu.py`.

Dùng `loudnorm` HAI LƯỢT của ffmpeg: lượt một đo, lượt hai sửa theo số đo. Một lượt cũng chạy
được nhưng nó phải đoán khi vừa đọc vừa sửa, và với video ngắn có đoạn lặng thì đoán sai khá
xa. Video được COPY nguyên (`-c:v copy`), chỉ mã hoá lại tiếng — nên nhanh và không mất chất
hình.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile

MOC = -14.0      # LUFS — mốc chuẩn hoá của YouTube / Facebook / Instagram
DINH = -1.5   # 1/9: đặt -1.0 thì đo lại ra -0.7 dBTP (loudnorm không đạt trần tuyệt đối
              # trên mọi nội dung). Hạ xuống -1.5 để bản ra thật sự nằm dưới -1.      # dBTP — YouTube khuyến nghị đỉnh thật dưới −1 để không vỡ tiếng khi nén lại
DAI = 11.0       # LRA


def _do(d: str):
    """Lượt một: đo. Trả None nếu ffmpeg không in ra JSON (tệp hỏng, không có tiếng…)."""
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", d,
         "-af", f"loudnorm=I={MOC}:TP={DINH}:LRA={DAI}:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True)
    m = re.search(r"\{[^{}]*input_i[\s\S]*?\}", r.stderr)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def chuan(d: str) -> str:
    """Chuẩn hoá âm lượng tệp mp4 TẠI CHỖ. Trả về mô tả ngắn để in ra, hoặc "" nếu bỏ qua.

    Mọi lỗi đều nuốt và trả "": bước này là ĐÁNH BÓNG, không phải điều kiện để có video. Một
    tệp chưa chuẩn âm vẫn hơn hẳn một lượt render hỏng ở phút chót — nhất là trên Actions, nơi
    hỏng ở đây nghĩa là mất cả lượt.
    """
    if not os.path.exists(d):
        return ""
    do = _do(d)
    if not do:
        return ""
    try:
        truoc = float(do["input_i"])
    except Exception:
        return ""
    if truoc > 0 or truoc < -60:          # tệp câm hoặc số đo vô nghĩa
        return ""

    tam = tempfile.mktemp(suffix=".mp4", dir=os.path.dirname(d) or ".")
    loc = (f"loudnorm=I={MOC}:TP={DINH}:LRA={DAI}"
           f":measured_I={do['input_i']}:measured_TP={do['input_tp']}"
           f":measured_LRA={do['input_lra']}:measured_thresh={do['input_thresh']}"
           f":offset={do.get('target_offset', 0)}:linear=true"
           # TRẦN CỨNG SAU LOUDNORM. `TP=` của `loudnorm` là mục tiêu MỀM: đặt −1.0 đo ra −0.7,
           # đặt −1.5 vẫn đo ra −0.7…−0.9 trên 9/14 tệp. Nâng con số ấy nữa chỉ làm bản trộn
           # nhỏ đi mà đỉnh vẫn vượt — vì loudnorm bù bằng khuếch đại tuyến tính, không cắt đỉnh.
           # `alimiter` cắt thật — nhưng PHẢI `level=disabled`: mặc định nó tự NÂNG mức lên chạm
           # trần sau khi cắt, và bản thử đầu ra −12,5 LUFS / −0,1 dBTP, tệ hơn trước. 0.84 ≈ −1.5 dBFS, chừa chỗ cho đỉnh giữa hai mẫu (inter-sample)
           # mà phép đo true-peak tính tới còn phép đo mẫu thì không.
           ",alimiter=level_in=1:level_out=1:limit=0.84:attack=5:release=50:level=disabled")
    r = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-nostats", "-loglevel", "error", "-i", d,
         "-c:v", "copy", "-af", loc, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
         tam], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(tam) or os.path.getsize(tam) < 1000:
        if os.path.exists(tam):
            os.remove(tam)
        return ""

    # GIẢI MÃ THỬ TRƯỚC KHI THAY THẾ. 31/8 — năm tệp ra hỏng luồng hình (NAL lỗi) mà bước này
    # vẫn thản nhiên đè lên bản gốc: `returncode == 0` và kích thước hợp lý KHÔNG chứng minh
    # tệp giải mã được. Một bước ĐÁNH BÓNG mà làm hỏng bản gốc thì tệ hơn hẳn không có nó —
    # nên phải tự chứng minh sản phẩm của mình dùng được rồi mới đụng vào tệp thật.
    kt = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-v", "error", "-xerror",
         "-i", tam, "-f", "null", "-"],
        capture_output=True, text=True)
    if kt.returncode != 0 or "Invalid NAL" in kt.stderr or "Error splitting" in kt.stderr:
        os.remove(tam)
        return "âm: BỎ QUA (bản chuẩn hoá giải mã lỗi, giữ bản gốc)"

    shutil.move(tam, d)
    return f"âm: {truoc:.1f} -> {MOC:.0f} LUFS"


if __name__ == "__main__":
    import sys
    for d in sys.argv[1:]:
        print(f"  {os.path.basename(d)}: {chuan(d) or 'bỏ qua'}")
