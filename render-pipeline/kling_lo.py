#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KLING LÒ — ghép clip Kling thành video hoàn chỉnh rồi ĐẨY THẲNG vào đường ray sẵn có.

VỊ TRÍ TRONG HỆ (28/8/2026)
---------------------------
    kling_studio.py  ->  BẢNG CHỤP (prompt cho từng cảnh)
    [anh dán vào Kling, tải clip về, thả vào thư mục]      <- chỗ duy nhất cần người
    kling_lo.py      ->  ghép + chữ + nhạc + chuẩn âm + QC + đẩy kho
    (đường ray cũ)   ->  Drive _QUEUE -> workflow đăng -> YouTube/Facebook

CHỖ CẮM DUY NHẤT
----------------
Hôm nay clip do người thả vào. Ngày anh mua API Kling, cái duy nhất đổi là AI TẢI CLIP VỀ ĐÚNG
THƯ MỤC ĐÓ — mọi thứ từ `kling_lo` trở đi giữ nguyên. Cố ý thiết kế vậy: cả dây chuyền không được
phụ thuộc vào việc clip từ đâu ra.

VÌ SAO GHÉP BẰNG FFMPEG CHỨ KHÔNG QUA REMOTION
----------------------------------------------
Clip Kling ĐÃ LÀ video thành phẩm. Cho nó chạy qua Remotion là mã hoá lại lần nữa — mất chất
lượng ở đúng thứ anh vừa trả tiền để có. ffmpeg ghép ở tầng luồng, chữ vẽ chồng một lần duy nhất.
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
KHO = os.path.join(GOC, "out", "kling")


def _chay(cmd, giay=900):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=giay)


def _do(duong: str) -> dict:
    """Số đo thật của một tệp video — không đoán theo tên."""
    r = _chay(["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-show_entries", "stream=width,height,duration",
               "-show_entries", "format=duration", "-of", "json", duong], 60)
    try:
        j = json.loads(r.stdout or "{}")
        st = (j.get("streams") or [{}])[0]
        d = float(st.get("duration") or (j.get("format") or {}).get("duration") or 0)
        return {"w": int(st.get("width") or 0), "h": int(st.get("height") or 0), "giay": d}
    except Exception:
        return {"w": 0, "h": 0, "giay": 0.0}


def kiem_du(thu_muc: str) -> tuple[bool, list, list]:
    """Đủ clip chưa. Trả (đủ?, danh sách tệp theo thứ tự, danh sách cảnh còn thiếu).

    ĐỦ HAY KHÔNG LÀ CÂU HỎI QUAN TRỌNG NHẤT Ở ĐÂY. Thiếu một cảnh giữa chừng thì gag gãy — mà
    video vẫn ra, vẫn đẩy kho, vẫn đăng. Hỏng kiểu đó không có gì báo động, nên phải chặn TRƯỚC
    khi ghép chứ không phải sửa sau."""
    js = os.path.join(thu_muc, "shots.json")
    if not os.path.exists(js):
        return False, [], ["thiếu shots.json"]
    d = json.load(io.open(js, encoding="utf-8"))
    canh = [s for s in (d.get("scenes") or []) if isinstance(s, dict)]
    clipdir = os.path.join(thu_muc, "clips")
    tep, thieu = [], []
    for s in canh:
        n = int(s.get("n") or 0)
        found = ""
        for ext in (".mp4", ".mov", ".webm", ".m4v"):
            p = os.path.join(clipdir, f"scene-{n:02d}{ext}")
            if os.path.exists(p) and os.path.getsize(p) > 10000:
                found = p
                break
        if found:
            tep.append((n, found, s))
        else:
            thieu.append(f"scene-{n:02d}")
    return (not thieu and len(tep) == len(canh)), tep, thieu


_CO_CHU = None


def co_ve_chu() -> bool:
    """Bản ffmpeg này có vẽ được chữ không (`drawtext` cần libfreetype).

    28/8 — đo thật: ffmpeg trên máy làm việc KHÔNG có `drawtext`, ffmpeg trên CI thì thường có.
    Nếu cứ dùng thẳng thì máy nào thiếu là hỏng CẢ VIDEO, chỉ vì thiếu một dòng chữ — cùng lớp
    lỗi với bản nhạc 404 hôm qua: một tài sản/năng lực phụ giết cả thành phẩm.
    Nên hỏi trước, thiếu thì bỏ chữ và NÓI RA, chứ không im lặng và cũng không chết."""
    global _CO_CHU
    if _CO_CHU is None:
        try:
            r = _chay(["ffmpeg", "-hide_banner", "-filters"], 30)
            _CO_CHU = " drawtext " in (r.stdout or "")
        except Exception:
            _CO_CHU = False
        if not _CO_CHU:
            print("   ⚠️ ffmpeg ở máy này KHÔNG có `drawtext` — video vẫn ra nhưng KHÔNG CÓ CHỮ "
                  "(mất hook chữ + phụ đề cảnh). Cài ffmpeg có libfreetype để có chữ.")
    return _CO_CHU


def _thoat(t: str) -> str:
    """Thoát chuỗi cho drawtext của ffmpeg — dấu nháy và hai chấm là hai thứ hay làm gãy lệnh."""
    return str(t or "").replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'")


def ghep(thu_muc: str, ra: str = "") -> str:
    """Ghép clip + chữ + nhạc + chuẩn âm. Trả đường dẫn mp4, hoặc "" nếu chưa đủ điều kiện."""
    du, tep, thieu = kiem_du(thu_muc)
    if not du:
        print(f"   ⏸️ {os.path.basename(thu_muc)}: chưa đủ clip — còn thiếu {', '.join(thieu[:6])}")
        return ""
    d = json.load(io.open(os.path.join(thu_muc, "shots.json"), encoding="utf-8"))
    ra = ra or os.path.join(thu_muc, "video.mp4")

    # 1) CHUẨN HOÁ TỪNG CLIP VỀ CÙNG KHUÔN trước khi nối.
    # Kling trả về nhiều tỉ lệ/khung hình khác nhau tuỳ lượt sinh; nối thẳng thì ffmpeg hoặc từ
    # chối, hoặc tệ hơn là nối được mà video giật khung ở mỗi mối. Ép hết về 1080x1920@30 (dọc,
    # đúng khổ short) rồi mới nối.
    tam = os.path.join(thu_muc, "_tam")
    os.makedirs(tam, exist_ok=True)
    ds = []
    for n, p, s in tep:
        o = os.path.join(tam, f"n{n:02d}.mp4")
        cap = _thoat(s.get("caption") or "") if co_ve_chu() else ""
        vf = ("scale=1080:1920:force_original_aspect_ratio=increase,"
              "crop=1080:1920,fps=30,format=yuv420p")
        if cap:
            # Chữ đặt ở 78% chiều cao: dưới vùng mắt nhìn chủ thể, trên vùng UI của YouTube Shorts.
            vf += (f",drawtext=text='{cap}':fontcolor=white:fontsize=54:box=1:boxcolor=black@0.45:"
                   f"boxborderw=18:x=(w-text_w)/2:y=h*0.78")
        r = _chay(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-vf", vf,
                   "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                   "-an", o])
        if r.returncode or not os.path.exists(o):
            print(f"   ❌ cảnh {n}: chuẩn hoá hỏng — {(r.stderr or '')[-140:]}")
            return ""
        ds.append(o)

    # 2) NỐI. Dùng concat demuxer (không mã hoá lại) vì mọi clip đã cùng khuôn ở bước trên.
    lst = os.path.join(tam, "ds.txt")
    io.open(lst, "w", encoding="utf-8").write(
        "".join(f"file '{os.path.abspath(x)}'\n" for x in ds))
    noi = os.path.join(tam, "noi.mp4")
    r = _chay(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
               "-i", lst, "-c", "copy", noi])
    if r.returncode or not os.path.exists(noi):
        print(f"   ❌ nối hỏng — {(r.stderr or '')[-140:]}")
        return ""

    # 3) CHỮ HOOK 1,5 GIÂY ĐẦU — thứ quyết định người xem ở lại hay lướt.
    hook = _thoat(d.get("hook_line") or "") if co_ve_chu() else ""
    nen = os.path.join(GOC, "..", "engine-remotion", "public",
                       "music", d.get("music") or "km_ascending.mp3")
    tmp2 = os.path.join(tam, "hook.mp4")
    vf2 = (f"drawtext=text='{hook}':fontcolor=white:fontsize=76:box=1:boxcolor=black@0.55:"
           f"boxborderw=24:x=(w-text_w)/2:y=h*0.13:enable='lt(t,1.6)'") if hook else "null"
    r = _chay(["ffmpeg", "-y", "-loglevel", "error", "-i", noi, "-vf", vf2,
               "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-an", tmp2])
    if r.returncode or not os.path.exists(tmp2):
        tmp2 = noi                       # chữ hook hỏng thì thà mất chữ còn hơn mất video

    # 4) NHẠC NỀN — dùng chung lưới an toàn với 50 kênh kia (thiếu tệp thì lùi, không giết video).
    try:
        import the_he_2 as T
        nh = T._nhac_co_that("music/" + os.path.basename(nen), "KLING")
    except Exception:
        nh = ""
    if nh:
        mp3 = os.path.join(GOC, "..", "engine-remotion", "public", nh)
        r = _chay(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp2, "-stream_loop", "-1",
                   "-i", mp3, "-shortest", "-c:v", "copy",
                   "-filter:a", "volume=0.16", "-c:a", "aac", "-b:a", "160k", ra])
        if r.returncode or not os.path.exists(ra):
            print("   ⚠️ ghép nhạc hỏng — giữ bản không nhạc")
            _chay(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp2, "-c", "copy", ra])
    else:
        _chay(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp2, "-c", "copy", ra])

    # 5) CHUẨN ÂM về -14 LUFS — cùng mức với 50 kênh kia, để người xem không phải chỉnh loa.
    try:
        import the_he_2 as T
        T.chuan_am(ra)
    except Exception as e:
        print(f"   ⚠️ chuẩn âm bỏ qua ({str(e)[:50]})")

    m = _do(ra)
    print(f"   ✅ ghép xong: {m['giay']:.1f}s · {m['w']}x{m['h']} · "
          f"{os.path.getsize(ra) / 1e6:.1f} MB · {len(ds)} cảnh")
    return ra


def day_kho(thu_muc: str, kenh: str, video: str) -> bool:
    """Đẩy vào Drive _QUEUE qua ĐÚNG cửa mà 50 kênh kia đi — để khâu đăng không cần biết
    video này do Kling làm hay do Remotion làm."""
    d = json.load(io.open(os.path.join(thu_muc, "shots.json"), encoding="utf-8"))
    sys.path.insert(0, GOC)
    import run_render as R
    story = {
        "topic": d.get("title"), "title": d.get("title"),
        "description": (d.get("logline") or ""),
        "sources": ["Generated with Kling AI"],
        "hashtags": ["#shorts", "#comedy"],
    }
    eq = R.enqueue_drive(kenh, video, story, "short")
    return bool(eq and eq.get("id"))


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Ghép clip Kling và đẩy kho")
    ap.add_argument("--kenh", default="", help="mã kênh trong channels.yaml (bỏ trống = chỉ ghép)")
    ap.add_argument("--thu-muc", default="", help="một thư mục cụ thể (bỏ trống = quét cả kho)")
    a = ap.parse_args()
    ds = [a.thu_muc] if a.thu_muc else [
        os.path.join(KHO, x) for x in sorted(os.listdir(KHO))] if os.path.isdir(KHO) else []
    ds = [x for x in ds if os.path.isdir(x)]
    if not ds:
        print(f"   (chưa có việc nào trong {KHO})")
        return 0
    xong = cho = 0
    for t in ds:
        ten = os.path.basename(t)
        if os.path.exists(os.path.join(t, ".da_day")):
            continue                     # đã đẩy rồi -> bỏ qua, khỏi đăng trùng
        v = ghep(t)
        if not v:
            cho += 1
            continue
        if a.kenh:
            if day_kho(t, a.kenh, v):
                io.open(os.path.join(t, ".da_day"), "w").write("1")
                print(f"   📤 {ten}: đã vào kho, khâu đăng sẽ tự lấy")
                xong += 1
            else:
                print(f"   ⚠️ {ten}: ghép xong nhưng đẩy kho hụt — giữ file, chạy lại sau")
        else:
            xong += 1
    print(f"\n📊 {xong} video xong · {cho} việc còn chờ clip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
