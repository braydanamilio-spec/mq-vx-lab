#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BỘ THIÊN NHIÊN — ĐƯA CLIP VỀ THÀNH VIDEO ĐĂNG ĐƯỢC  (2/9/2026)

VÌ SAO CÓ TỆP NÀY
-----------------
`thien_nhien.py` dừng ở PROMPT. Sau khi anh dán vào Kling và tải clip về thì **không có gì đưa
nó đi tiếp** — `kling_dong_bo.py` import cứng `kling_kenh` (engine hài) nên đưa clip thiên nhiên
vào là nổ ngay ở dòng đầu:

    KK.ho_so("ICE BEAR")  ->  RuntimeError: chưa có kênh 'ICE BEAR'

Đây là lỗ hổng lớn nhất còn lại của bộ thứ năm: một dây chuyền kết thúc ở nửa đường trông y hệt
một dây chuyền hoàn chỉnh, cho tới lúc anh có clip trong tay.

BA CHỖ KHÁC HẲN BỘ HÀI, và cả ba đều là lý do không dùng chung tệp
------------------------------------------------------------------
1. **Ảnh bìa lấy ở 66%**, không phải 62% và cũng không phải nhịp hook. Prompt của bộ này viết
   rõ *"the movement resolves about two thirds through"* — nên hai phần ba CHÍNH LÀ đỉnh của
   hành động. Ở bộ hài, 62% rơi đúng vào cú lật và làm lộ cái kết (luật 13.27); ở đây không có
   cú lật nào để lộ, chỉ có một khoảnh khắc đẹp nhất, và nó nằm ở đúng chỗ ấy.
2. **Bài đăng viết bằng CODE, không gọi AI.** Bộ hài cần AI vì tiêu đề phải bắt được cú đùa. Ở
   đây tiêu đề là *loài + hành vi + nơi chốn* — ba thứ đã nằm sẵn trong `tap.json`. Gọi AI cho
   việc này là tiêu một lượt gọi và một chỗ trong hạn mức để lấy về thứ đã có.
3. **Bắt buộc ghi rõ là cảnh dựng bằng AI.** Đây là ràng buộc cứng số một của ngách này (§15.6):
   trình bày cảnh AI như tư liệu động vật thật vừa là khai man vừa là dạng bị gỡ nhanh nhất.
   `_KHAI_BAO` đi vào mô tả của cả ba nền tảng, và `kiem()` chặn nếu thiếu.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
KHO = os.path.join(GOC, "out", "thien_nhien")

# Câu khai báo. Ngắn, đứng ĐẦU mô tả, không giấu xuống cuối — giấu xuống cuối thì về mặt chính
# sách vẫn tính là có, nhưng về mặt người xem thì đó là giấu, và người xem mới là bên phát hiện.
_KHAI_BAO = "Animated with AI. This is not documentary footage of a real animal."

# Ảnh bìa: hai phần ba clip. Xem docstring — con số này KHÁC bộ hài một cách có chủ đích.
BIA_TAI = 0.66


def _chay(cmd, giay=900):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=giay)


def _tap_dir() -> list[str]:
    """Mọi thư mục tập đã sinh prompt, cũ trước mới sau."""
    ra = []
    for slug in sorted(os.listdir(KHO)) if os.path.isdir(KHO) else []:
        d = os.path.join(KHO, slug)
        if not os.path.isdir(d):
            continue
        ra += [os.path.join(d, x) for x in sorted(os.listdir(d))
               if os.path.isdir(os.path.join(d, x))]
    return ra


def _clip(tm: str) -> list[str]:
    c = os.path.join(tm, "clips")
    if not os.path.isdir(c):
        return []
    return [os.path.join(c, x) for x in sorted(os.listdir(c))
            if x.lower().endswith((".mp4", ".mov", ".webm"))]


def dung_video(tm: str) -> str:
    """Ép clip về đúng khổ short 1080x1920@30. Một tập = MỘT clip, nên không có khâu nối.

    Vẫn phải ép khổ: Kling trả về nhiều tỉ lệ và nhiều khung hình tuỳ lượt sinh, và một tệp
    9:16 "gần đúng" vẫn làm YouTube xếp nó thành video ngang có viền đen.
    """
    cs = _clip(tm)
    if not cs:
        return ""
    if len(cs) > 1:
        print(f"   ⚠️ {os.path.basename(tm)}: có {len(cs)} clip, bộ này mỗi tập MỘT clip — "
              f"dùng clip đầu, mấy cái sau bỏ qua")
    ra = os.path.join(tm, "video.mp4")
    # NÂNG CỠ LÊN 2160×3840 TRƯỚC KHI UPLOAD — và gọi đúng tên: đây là NÂNG CỠ, không phải 4K
    # gốc. Viết "4K" vào prompt không làm Kling xuất 4K; độ phân giải là thiết lập sinh, không
    # phải một chữ.
    #
    # Nhưng đòn bẩy này CÓ THẬT và nằm ở phía YouTube: nó cấp codec và bitrate cao hơn hẳn cho
    # tệp ≥1440p (VP9/AV1 thay vì H.264 ở bậc thấp). Cùng một khung hình, bản nâng cỡ giữ được
    # nhiều chi tiết hơn sau khi YouTube nén lại — mà chi tiết chính là thứ ngách này bán.
    #
    # `lanczos` chứ không phải bicubic mặc định: ở tỉ lệ 2× nó giữ nét lông và bọt nước, thứ
    # bicubic làm nhoè. Và `crf 18` vì bản nâng cỡ phải nuôi bộ nén của YouTube, không phải để
    # xem trực tiếp.
    r = _chay(["ffmpeg", "-y", "-loglevel", "error", "-i", cs[0], "-vf",
               "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
               "scale=2160:3840:flags=lanczos,fps=30,format=yuv420p",
               "-c:v", "libx264", "-crf", "18", "-preset", "slow",
               "-an", "-movflags", "+faststart", ra])
    return ra if r.returncode == 0 and os.path.exists(ra) else ""


# ── BÀI ĐĂNG — viết bằng CODE, không gọi AI ────────────────────────────────────────────────
def _hoa(t: str) -> str:
    return t[:1].upper() + t[1:] if t else t


def viet_bai(tap: dict) -> dict:
    """Tiêu đề · mô tả · thẻ cho ba nền tảng, dựng từ chính `tap.json`.

    Không gọi AI: mọi thành phần của một tiêu đề tốt ở ngách này (loài · hành vi · nơi chốn) đã
    nằm sẵn trong tập. Gọi AI ở đây là tiêu một lượt và một chỗ trong hạn mức để lấy về thứ mình
    đang cầm — và còn thêm một chỗ nữa để hỏng khi hết quota.
    """
    import thien_nhien as TN
    kenh = tap["kenh"]
    hs = TN.ho_so(kenh)
    loai, hv = tap["loai"], tap["hanh_vi"]
    noi = hs["the_gioi"].split(":")[0].strip()

    # Tiêu đề viết theo cách người ta GÕ TÌM, không theo cách đặt tên một bộ phim.
    tieu_de = f"{_hoa(loai)} {hv}"
    if len(tieu_de) > 58:
        tieu_de = f"{_hoa(loai)} {hv.split(',')[0]}"
    if len(tieu_de) > 58:
        # Cắt theo RANH GIỚI TỪ. Cắt thẳng ở ký tự thứ 58 cho ra "...breathing hole in t" —
        # một tiêu đề cụt giữa chữ đọc ra là lỗi máy ngay trong nửa giây, đúng dạng dấu hiệu
        # nghiệp dư ở luật 12.12.
        tieu_de = tieu_de[:58].rsplit(" ", 1)[0]
    tieu_de = tieu_de.rstrip(" ,;—-")

    mo_ta = (
        f"{_KHAI_BAO}\n\n"
        f"{_hoa(loai)} — {hv}. {noi}.\n\n"
        f"{hs['mo_ta']}\n\n"
        f"{hs['hook']}"
    )
    the = ([re.sub(r"[^a-z0-9]", "", w) for w in loai.lower().split()]
           + [re.sub(r"[^a-z0-9]", "", w) for w in kenh.lower().split()]
           + ["wildlife", "nature", "animals", "aiart", "aianimation", "shorts"])
    the = [t for i, t in enumerate(dict.fromkeys(the)) if t and len(t) > 2][:12]
    return {
        "youtube": {"title": tieu_de, "description": mo_ta, "tags": the},
        "facebook": {"text": f"{_hoa(loai)} — {hv}.\n\n{_KHAI_BAO}",
                     "hashtags": ["#" + t for t in the[:4]]},
        "instagram": {"caption": f"{_hoa(loai)} — {hv}.\n{_KHAI_BAO}",
                      "hashtags": ["#" + t for t in the]},
    }


def kiem_bai(bai: dict) -> list[str]:
    """Cổng: câu khai báo AI phải có mặt ở CẢ BA nền tảng, và tiêu đề phải trong giới hạn.

    Thử ngược được: bỏ câu khai báo khỏi một nền tảng thì cổng phải kêu. Một cổng chỉ chạy chiều
    thuận là một cổng chưa biết có hoạt động không (luật 13.11).
    """
    e = []
    for nen, khoa in (("youtube", "description"), ("facebook", "text"), ("instagram", "caption")):
        if _KHAI_BAO not in (bai.get(nen) or {}).get(khoa, ""):
            e.append(f"{nen}: thiếu câu khai báo cảnh dựng bằng AI — đây là ràng buộc cứng của "
                     f"ngách này, không phải tuỳ chọn")
    t = (bai.get("youtube") or {}).get("title", "")
    if not t:
        e.append("youtube: thiếu tiêu đề")
    elif len(t) > 60:
        e.append(f"youtube: tiêu đề {len(t)} ký tự, quá 60 — YouTube cắt đuôi trên điện thoại")
    return e


def lam_bia(tm: str, video: str) -> str:
    """Ảnh bìa: khung ở 66% clip — đỉnh hành động theo đúng nhịp mà prompt đặt hàng.

    Cố ý KHÁC bộ hài. Ở đó `_make_thumb` cắt 62% và rơi trúng cú lật của clip 5–6 giây, tức bìa
    kể trước cái kết (luật 13.27). Ở đây không có cú lật nào để lộ: prompt yêu cầu *"the movement
    resolves about two thirds through"*, nên hai phần ba là khoảnh khắc đẹp nhất chứ không phải
    khoảnh khắc phải giấu. Cùng một cơ chế, hai con số, hai lý do — và lý do mới là thứ phải ghi.
    """
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    import brand_tn as BT
    import thien_nhien as TN
    tap = json.load(io.open(os.path.join(tm, "tap.json"), encoding="utf-8"))
    kenh = tap["kenh"]
    giay = float(tap.get("giay") or 8)
    at = max(0.2, giay * BIA_TAI)
    tam = os.path.join(tm, "_bia.jpg")
    vf = ("split[a][b];"
          "[a]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=20:2[bg];"
          "[b]scale=1280:720:force_original_aspect_ratio=decrease[fg];"
          "[bg][fg]overlay=(W-w)/2:(H-h)/2")
    r = _chay(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{at:.2f}", "-i", video,
               "-frames:v", "1", "-filter_complex", vf, tam], 120)
    if r.returncode != 0 or not os.path.exists(tam):
        return ""
    b = BT.BRAND[kenh]
    im = Image.open(tam).convert("RGB")
    W, H = im.size
    d = ImageDraw.Draw(im)
    c1 = tuple(int(b["chinh"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    # Đĩa tối sau biểu tượng: khung hình thiên nhiên đủ mọi tông, và sớm muộn sẽ có tập trùng
    # tông với màu kênh — lúc ấy biểu tượng biến mất. Đây là lỗi đã trả giá ở bìa bộ hài (13.27).
    d.ellipse([W - 132, 12, W - 12, 132], fill=(0, 0, 0, 105))
    BT.bieu_tuong(d, b["bt"], W - 72, 72, 38, c1, (0, 0, 0), (0, 0, 0))
    try:
        fo = ImageFont.truetype("/System/Library/Fonts/Supplemental/Impact.ttf", 74)
    except Exception:
        fo = ImageFont.load_default()
    t = TN.ho_so(kenh)["ten"]
    w = d.textbbox((0, 0), t, font=fo)[2]
    x, y = 48, H - 132
    # Bóng MỀM thật: một lớp riêng đem làm mờ, không phải ba bản chữ lệch chỗ (dấu hiệu nghiệp
    # dư đã liệt kê ở 12.12 và đã vi phạm một lần rồi).
    bong = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(bong).text((x, y + 6), t, font=fo, fill=(0, 0, 0, 190))
    im.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), bong.filter(ImageFilter.GaussianBlur(11)))
    ImageDraw.Draw(im).text((x, y), t, font=fo, fill=(255, 255, 255))
    ra = os.path.join(tm, "bia.jpg")
    im.save(ra, quality=90)
    os.remove(tam)
    return ra


def day_kho(tm: str, kenh_dang: str, video: str, bai: dict, tap: dict, bia: str = "") -> bool:
    """Đẩy vào Drive _QUEUE qua ĐÚNG cửa mà mọi bộ khác đi — khâu đăng không cần biết video này
    do Kling làm hay do Remotion làm."""
    sys.path.insert(0, GOC)
    import run_render as R
    yt = bai.get("youtube") or {}
    story = {
        "topic": yt.get("title"),
        "title": yt.get("title"),
        "description": yt.get("description") or "",
        "sources": [],
        # `enqueue_drive` ghi VÔ ĐIỀU KIỆN "Imagery: Pexels · Pixabay · Wikimedia · NASA…" khi
        # không có sổ ghi công. Với video này đó là MÔ TẢ SAI SỰ THẬT — và ở ngách động vật, mô
        # tả sai nguồn hình là đúng thứ khiến kênh bị soi.
        "_credits": ["Animated with Kling AI — not real wildlife footage"],
        "hashtags": (bai.get("instagram") or {}).get("hashtags") or ["#shorts"],
        "posts": {k: bai.get(k) for k in ("youtube", "facebook", "instagram")},
    }
    if bia and os.path.exists(bia):
        story["_thumb"] = bia
    eq = R.enqueue_drive(kenh_dang, video, story, "short")
    return bool(eq and eq.get("id"))


def mot_tap(tm: str, kenh_dang: str = "", day: bool = False) -> str:
    """Một tập: clip -> video -> bài -> bìa -> (tuỳ chọn) đẩy kho. Trả đường dẫn video."""
    tapf = os.path.join(tm, "tap.json")
    if not os.path.exists(tapf):
        print(f"   ⚠️ {tm}: thiếu tap.json"); return ""
    tap = json.load(io.open(tapf, encoding="utf-8"))
    v = dung_video(tm)
    if not v:
        print(f"   ⏭️ {os.path.basename(os.path.dirname(tm))}/{os.path.basename(tm)}: "
              f"chưa có clip trong clips/"); return ""
    bai = viet_bai(tap)
    e = kiem_bai(bai)
    if e:
        # Không đẩy một bài thiếu khai báo. Hỏng ở đây là hỏng ở chỗ ĐẮT NHẤT — kênh bị soi.
        raise RuntimeError("bài đăng chưa đạt:\n  - " + "\n  - ".join(e))
    json.dump(bai, io.open(os.path.join(tm, "bai.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    bia = lam_bia(tm, v)
    if day:
        ok = day_kho(tm, kenh_dang or tap["kenh"], v, bai, tap, bia)
        print(f"   {'✅ đã đẩy kho' if ok else '❌ đẩy kho HỎNG'}: {tap['kenh']} #{tap['so']}")
        if not ok:
            raise RuntimeError("đẩy kho hỏng — lượt này phải tính là HỎNG, không được nuốt "
                               "(luật 13.3: `|| true` ở mắt xích cuối làm hỏng mà vẫn báo xanh)")
    else:
        print(f"   ✅ {tap['kenh']} #{tap['so']} → {os.path.basename(v)}"
              f"{' + bìa' if bia else ''}")
    return v


def main() -> int:
    ap = argparse.ArgumentParser(description="Đưa clip Kling của bộ thiên nhiên thành video đăng.")
    ap.add_argument("--tap", help="đường dẫn một thư mục tập; bỏ trống = mọi tập có clip")
    ap.add_argument("--kenh-dang", default="", help="tên kênh ở khâu đăng")
    ap.add_argument("--day", action="store_true", help="đẩy vào Drive _QUEUE")
    a = ap.parse_args()
    ds = [a.tap] if a.tap else _tap_dir()
    if not ds:
        print(f"   (chưa có tập nào — chạy thien_nhien.py trước)"); return 1
    n = 0
    for tm in ds:
        if mot_tap(tm, a.kenh_dang, a.day):
            n += 1
    print(f"\n  {n}/{len(ds)} tập có clip và đã dựng xong")
    return 0 if n else 1


if __name__ == "__main__":
    raise SystemExit(main())
