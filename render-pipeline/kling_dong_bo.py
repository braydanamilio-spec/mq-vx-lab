#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KLING ĐỒNG BỘ — anh tải clip từ Kling về, máy lo phần còn lại. (30/8/2026)

VIỆC CỦA TỆP NÀY
----------------
    anh thả video vào thư mục tập  →  máy chuẩn hoá khuôn hình  →  AI viết bài đăng cho ba nền
    tảng  →  đẩy vào Drive _QUEUE  →  khâu đăng của MM0-AutoPublisher lấy đi như 50 kênh kia.

VÌ SAO VIẾT BÀI ĐĂNG BA LẦN, KHÔNG DÙNG CHUNG MỘT BẢN
-----------------------------------------------------
`kling_lo.day_kho` cũ lấy tên tập làm title và logline làm description cho cả ba nền tảng. Bản ấy
không sai, nhưng nó bỏ qua một chuyện: ba nền tảng thưởng ba thứ khác nhau, và bài đăng dùng chung
thì thua ở cả ba.

    YouTube Shorts .. tiêu đề là câu hỏi tìm kiếm. Người ta gõ "husband thermostat fight", không
                      gõ "Thermostat Tangle Turnaround". Mô tả dài có tác dụng — nó là thứ YouTube
                      đọc để biết nên gợi ý video này cho ai.
    Facebook ....... không có ô tìm kiếm nào đáng kể. Thứ chạy được là câu đầu khiến người ta
                      DỪNG cuộn, và một câu mời bình luận — bình luận là tín hiệu phân phối mạnh
                      nhất ở đây. Hashtag gần như vô dụng, để nhiều chỉ làm bẩn bài.
    Instagram ...... caption ngắn, hashtag là kênh khám phá thật sự. 15-20 thẻ đúng chủ đề.

NGUYÊN TẮC AN TOÀN
------------------
Gán tệp vào tập là việc KHÔNG ĐẢO NGƯỢC được (chép/di chuyển tệp), nên chế độ hộp thư đến luôn IN
BẢNG DỰ KIẾN trước và chỉ làm thật khi có `--lam`. Đoán sai thứ tự mà cứ thế chạy thì mười tập
lắp nhầm mười video, và không có cách nào biết ngoài xem lại từng cái.
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KHO = os.path.join(HERE, "out", "kling")


def _chay(cmd, giay=900):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=giay)


def _tap_dir() -> list[str]:
    """Mọi thư mục tập đã sinh prompt, sắp theo kênh rồi số tập."""
    r = []
    if not os.path.isdir(KHO):
        return r
    for kenh in sorted(os.listdir(KHO)):
        tk = os.path.join(KHO, kenh)
        if not os.path.isdir(tk):
            continue
        for t in sorted(os.listdir(tk)):
            if os.path.isfile(os.path.join(tk, t, "tap.json")):
                r.append(os.path.join(tk, t))
    return r


def _clip(tm: str) -> list[str]:
    c = os.path.join(tm, "clips")
    if not os.path.isdir(c):
        return []
    return sorted(os.path.join(c, f) for f in os.listdir(c)
                  if f.lower().endswith((".mp4", ".mov", ".webm")) and not f.startswith("."))


# ── CHUẨN HOÁ + GHÉP ────────────────────────────────────────────────────────────────────────
def dung_video(tm: str) -> str:
    """Ép clip về đúng khổ short rồi nối. Trả đường dẫn mp4, "" nếu chưa có clip nào.

    Kling trả về nhiều tỉ lệ/khung hình tuỳ lượt sinh và tuỳ phiên bản model. Nối thẳng thì hoặc
    ffmpeg từ chối, hoặc tệ hơn là nối được mà giật khung ở mỗi mối — bài học đã trả giá bên
    `kling_lo`. Ép hết về 1080x1920@30 rồi mới nối."""
    cs = _clip(tm)
    if not cs:
        return ""
    ra = os.path.join(tm, "video.mp4")
    if len(cs) == 1:
        r = _chay(["ffmpeg", "-y", "-loglevel", "error", "-i", cs[0], "-vf",
                   "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                   "fps=30,format=yuv420p",
                   "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                   "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", ra])
        return ra if r.returncode == 0 and os.path.exists(ra) else ""

    tam = os.path.join(tm, "_tam")
    os.makedirs(tam, exist_ok=True)
    ds = []
    for i, c in enumerate(cs, 1):
        o = os.path.join(tam, f"n{i:02d}.mp4")
        r = _chay(["ffmpeg", "-y", "-loglevel", "error", "-i", c, "-vf",
                   "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                   "fps=30,format=yuv420p",
                   "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                   "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", o])
        if r.returncode == 0 and os.path.exists(o):
            ds.append(o)
    if not ds:
        return ""
    lst = os.path.join(tam, "noi.txt")
    io.open(lst, "w", encoding="utf-8").write(
        "\n".join(f"file '{os.path.abspath(x)}'" for x in ds))
    r = _chay(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
               "-c", "copy", "-movflags", "+faststart", ra])
    shutil.rmtree(tam, ignore_errors=True)
    return ra if r.returncode == 0 and os.path.exists(ra) else ""


# ── AI VIẾT BÀI ĐĂNG ────────────────────────────────────────────────────────────────────────
SCHEMA_DANG = """Return ONLY JSON:
{
  "youtube": {
    "title": "under 60 characters, written the way a person would SEARCH for this, not the way a film is titled. Plain words. No colon, no clickbait punctuation.",
    "description": "2-3 short paragraphs. The FIRST LINE must be the on-screen hook moment itself, never a repeat of the title. Then what happens. Then one line about the channel. Written for a human, not stuffed with keywords.",
    "tags": ["8-12 lowercase search phrases people actually type"]
  },
  "facebook": {
    "text": "One scroll-stopping opening line, then two or three short lines, then one question that invites a reply. No hashtags in the body.",
    "hashtags": ["2-4 only"]
  },
  "instagram": {
    "caption": "Two short lines maximum. Punchy. One emoji at most.",
    "hashtags": ["15-20 lowercase tags, mix broad and specific, no spaces"]
  }
}"""


def viet_bai(tap: dict, kenh: str, keys=None) -> dict:
    """AI viết bài đăng RIÊNG cho từng nền tảng, vì ba nền tảng thưởng ba thứ khác nhau."""
    import content_brain as CB
    import kling_kenh as KK
    hs = KK.ho_so(kenh)
    tho = " ".join(f'{l.get("who")}: "{l.get("say")}"'
                   for l in (tap.get("lines") or []) if isinstance(l, dict) and l.get("say"))
    hoi = (
        f'A {tap.get("_giay", 8):g}-second animated comedy short from an American cartoon channel '
        f'called {hs["ten"]} ({hs["mo_ta"]}).\n\n'
        f'Episode: {tap.get("title")}\n'
        f'Opens on: {tap.get("hook")}\n'
        f'Dialogue: {tho}\n'
        f'Ends on: {tap.get("payoff")}\n\n'
        f'Write the posts. American English, the voice of someone who finds this funny and is '
        f'showing a friend — not a marketing department.\n'
        f'NEVER use the words kids, children, toddler, nursery, preschool or family-friendly '
        f'anywhere: they get the video classified as made-for-kids, which kills comments and '
        f'monetisation.\n\n{SCHEMA_DANG}')

    ho = KK._ho_key(keys) or [None]
    for i in range(min(len(ho), 12)):
        try:
            g = CB._genai(ho[i])
            m = g.GenerativeModel(CB.MODEL)
            t = getattr(m.generate_content(
                hoi, generation_config={"temperature": 0.9,
                                        "response_mime_type": "application/json"}), "text", "")
            d = CB._extract_json(t)
            if isinstance(d, dict) and d.get("youtube"):
                return d
        except Exception:
            continue
    # Không gọi được AI thì vẫn phải đăng được — bài mộc còn hơn video nằm kho.
    ten = str(tap.get("title") or "Untitled")
    return {"youtube": {"title": ten[:60], "description": str(tap.get("hook") or ""), "tags": []},
            "facebook": {"text": str(tap.get("hook") or ""), "hashtags": ["#shorts"]},
            "instagram": {"caption": ten, "hashtags": ["#animation", "#comedy", "#shorts"]},
            "_moc": True}


# Thẻ và từ khoá TUYỆT ĐỐI không được dùng. Đây không phải chuyện thẩm mỹ.
# Hoạt hình + chữ "kids/children/nursery" là đúng công thức để YouTube xếp video vào "made for
# kids": bình luận bị tắt, không lưu vào danh sách phát, không hiện thông báo, quảng cáo cá nhân
# hoá bị chặn — tức là mất gần hết doanh thu và gần hết đường phân phối. Một cái thẻ AI thêm cho
# đủ số đổi lấy chừng đó thì không đáng, nên chặn cứng ở đây thay vì tin AI nhớ.
CAM_THE = ("kid", "kids", "children", "child", "toddler", "nursery", "preschool", "baby",
           "cartoonforkids", "kidsanimation", "kidscartoon", "familyfriendly", "forkids")


def _sach(x: str) -> bool:
    t = re.sub(r"[^a-z]", "", str(x).lower())
    return not any(c in t for c in CAM_THE)


def _gon(b: dict, tap: dict) -> dict:
    """Ép bài đăng về đúng giới hạn thật của từng nền tảng.

    Đây là lưới an toàn, không phải trang trí: YouTube CẮT tiêu đề quá 100 ký tự giữa chừng, và
    Instagram từ chối bài quá 30 thẻ. Cả hai hỏng lặng lẽ — không có lỗi nào báo về."""
    yt = b.setdefault("youtube", {})
    yt["title"] = " ".join(str(yt.get("title") or tap.get("title") or "").split())[:95]
    yt["description"] = str(yt.get("description") or "").strip()
    yt["tags"] = [str(x).strip().lower() for x in (yt.get("tags") or []) if _sach(x)][:15]
    fb = b.setdefault("facebook", {})
    fb["text"] = str(fb.get("text") or "").strip()
    fb["hashtags"] = [_the(x) for x in (fb.get("hashtags") or []) if _sach(x)][:4]
    ig = b.setdefault("instagram", {})
    ig["caption"] = str(ig.get("caption") or "").strip()[:2100]
    ig["hashtags"] = [t for t in (_the(x) for x in (ig.get("hashtags") or []) if _sach(x)) if t][:25]
    return b


def _the(x: str) -> str:
    x = re.sub(r"[^0-9a-zA-Z]", "", str(x))
    return ("#" + x.lower()) if x else ""


# ── ẢNH BÌA ─────────────────────────────────────────────────────────────────────────────────
def lam_bia(tm: str, tap: dict, video: str) -> str:
    """Ảnh bìa 1280×720 cho một tập Kling. Trả đường dẫn, hoặc "" nếu hỏng.

    VÌ SAO PHẢI TỰ LÀM, KHÔNG ĐỂ DÂY CHUYỀN TỰ CẮT
    ----------------------------------------------
    `run_render._make_thumb()` cắt khung ở **62% thời lượng**. Với video dài của bộ phân tích
    thì đó là chỗ đẹp. Với short Kling thì đó là chỗ TỆ NHẤT: theo chính `nhip()`, cú lật của
    clip 5–6 giây bắt đầu từ 33–34%. Nên **mọi ảnh bìa của clip 5s và 6s đang lộ luôn câu chốt**
    — mà 5–6 giây chính là vùng ưu tiên vì Kling tính tiền theo lượt.

    Không có lỗi nào báo ra: ảnh vẫn đúng cỡ, vẫn lên YouTube, chỉ là nó kể trước cái kết.

    Bìa này lấy khung ở giữa NHỊP HOOK — đúng cái hình sai trái được thiết kế để chặn ngón tay
    người xem, và là hình duy nhất trong clip không tiết lộ gì.
    """
    try:
        from PIL import Image, ImageDraw, ImageFilter
        import kling_kenh as KK
        import brand_kling as BK
    except Exception:
        return ""
    try:
        kenh = tap.get("_kenh") or "HOUSE RULES"
        giay = float(tap.get("_giay") or 8)
        n = KK.nhip(giay)
        h = next((x for x in n if x[2] == "hook"), n[0])
        at = max(0.15, h[0] + (h[1] - h[0]) * 0.6)      # giữa nhịp hook

        tam = os.path.join(tm, "_bia_khung.jpg")
        vf = ("split[a][b];"
              "[a]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=20:2[bg];"
              "[b]scale=1280:720:force_original_aspect_ratio=decrease[fg];"
              "[bg][fg]overlay=(W-w)/2:(H-h)/2")
        _chay(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.2f}", "-i", video,
               "-frames:v", "1", "-filter_complex", vf, tam], 120)
        if not os.path.exists(tam):
            return ""

        im = Image.open(tam).convert("RGB")
        d = ImageDraw.Draw(im, "RGBA")
        W, H = im.size
        b = BK.BRAND.get(kenh)
        if b:
            c1 = BK._rgb(b["chinh"])
            # Dải thương hiệu mỏng dưới đáy + biểu tượng góc: đủ để nhận ra kênh ở cỡ nhỏ, không
            # đủ to để che hình. Dải tên kênh dưới MỌI khung là dấu hiệu nghiệp dư (luật 12.12) —
            # nhưng ở ảnh BÌA thì nhận diện kênh là việc chính đáng, khác với ở trong video.
            d.rectangle([0, H - 14, W, H], fill=c1)
            # Đĩa tối mờ SAU biểu tượng. Không có nó thì biểu tượng màu thương hiệu tàng hình
            # ngay khi khung hình tình cờ cùng tông — và với hai mươi kênh, sớm muộn sẽ có tập
            # rơi đúng vào tông ấy. Đĩa tối cũng là cách mọi hãng đặt logo lên hình bất kỳ.
            d.ellipse([W - 132, 12, W - 12, 132], fill=(0, 0, 0, 105))
            BK.bieu_tuong(d, b["bt"], W - 72, 72, 38, c1 + (255,), (0, 0, 0, 0), (0, 0, 0, 0))

        # Tiêu đề: chữ trắng + BÓNG MỀM, không viền trắng (luật 12.12 — không hãng phim nào
        # viền chữ). Đặt ở một phần ba dưới, nơi hình thường trống nhất.
        t = str(tap.get("title") or "").upper()
        if t:
            fo = BK._vua(d, t, int(W * .86), 92)
            tw, th = BK._rong(d, t, fo)
            x, y = (W - tw) // 2, int(H * .70)
            # BÓNG MỀM thật, bằng một lớp riêng đem làm mờ. Bản đầu vẽ ba bản chữ lệch nhau vài
            # điểm ảnh — ra một cái bóng CỨNG có bậc, đúng dấu hiệu nghiệp dư ở luật 12.12
            # ("đổ bóng cứng lệch"). Bóng mềm phải là bóng mờ, không phải bản sao dịch chỗ.
            bong = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(bong).text((x, y + 6), t, font=fo, fill=(0, 0, 0, 190))
            bong = bong.filter(ImageFilter.GaussianBlur(11))
            im.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), bong)
            d = ImageDraw.Draw(im, "RGBA")
            d.text((x, y), t, font=fo, fill=(252, 250, 246))

        dest = os.path.join(tm, "bia.jpg")
        im.save(dest, quality=88)
        os.remove(tam)
        return dest
    except Exception as e:
        print("   ⚠️ ảnh bìa lỗi:", str(e)[:70])
        return ""


# ── ĐẨY KHO ─────────────────────────────────────────────────────────────────────────────────
def day_kho(tm: str, kenh_dang: str, video: str, bai: dict, tap: dict, bia: str = "") -> bool:
    """Đẩy vào Drive _QUEUE qua ĐÚNG cửa mà 50 kênh kia đi — khâu đăng không cần biết video này
    do Kling làm hay do Remotion làm."""
    sys.path.insert(0, HERE)
    import run_render as R
    yt = bai.get("youtube") or {}
    story = {
        "topic": tap.get("title"),
        "title": yt.get("title") or tap.get("title"),
        "description": yt.get("description") or "",
        "sources": [],
        # `enqueue_drive` ghi VÔ ĐIỀU KIỆN "Imagery: Pexels · Pixabay · Wikimedia · NASA…" khi
        # không có sổ ghi công. Với video Kling thì đó là MÔ TẢ SAI SỰ THẬT — không có tấm ảnh
        # Pexels nào trong đây, tất cả do Kling sinh. Chính đoạn mã ấy đã chép lại bài học y hệt
        # về việc ghi công Kevin MacLeod cho video không có nhạc: mô tả sai là điểm trừ khi
        # YouTube xét kênh, và ghi công một giấy phép mình không dùng thì chẳng được gì.
        "_credits": ["Animation generated with Kling AI"],
        "hashtags": (bai.get("instagram") or {}).get("hashtags") or ["#shorts"],
        # Bài riêng của FB/IG đi kèm để khâu đăng dùng đúng bản của nền tảng nó, thay vì lấy
        # bản YouTube dán sang cả ba chỗ.
        "posts": {k: bai.get(k) for k in ("youtube", "facebook", "instagram")},
    }
    # Ảnh bìa TỰ LÀM. Không truyền thì `run_render` lùi về `_make_thumb()` cắt ở 62% thời lượng
    # — đúng vào cú lật của clip 5–6 giây, tức bìa kể trước cái kết.
    if bia and os.path.exists(bia):
        story["_thumb"] = bia
    eq = R.enqueue_drive(kenh_dang, video, story, "short")
    return bool(eq and eq.get("id"))


# ── HỘP THƯ ĐẾN ─────────────────────────────────────────────────────────────────────────────
def hop_thu(thu_muc: str, lam: bool = False) -> int:
    """Gán video mới tải về cho các tập chưa có clip, theo THỨ TỰ THỜI GIAN tệp.

    Luôn in bảng dự kiến trước. Chép tệp là việc không đảo ngược được, và nếu thứ tự đoán sai thì
    mười tập lắp nhầm mười video mà không có cách nào biết ngoài mở từng cái ra xem."""
    if not os.path.isdir(thu_muc):
        print(f"❌ không thấy thư mục {thu_muc}")
        return 1
    moi = sorted((os.path.join(thu_muc, f) for f in os.listdir(thu_muc)
                  if f.lower().endswith((".mp4", ".mov", ".webm")) and not f.startswith(".")),
                 key=lambda p: os.path.getmtime(p))
    trong = [t for t in _tap_dir() if not _clip(t)]
    if not moi:
        print(f"   (không có video nào trong {thu_muc})")
        return 0
    if not trong:
        print("   (mọi tập đã có clip — không còn chỗ trống để gán)")
        return 0

    n = min(len(moi), len(trong))
    print(f"\n  {len(moi)} video mới · {len(trong)} tập còn trống → ghép được {n}\n")
    for i in range(n):
        print(f"    {os.path.basename(moi[i])[:46]:<48} →  {os.path.basename(trong[i])}")
    if len(moi) > n:
        print(f"\n    ⚠️ {len(moi) - n} video thừa, chưa có tập để gán (sinh thêm prompt trước)")
    if len(trong) > n:
        print(f"\n    ⏸️ {len(trong) - n} tập vẫn chờ clip")

    if not lam:
        print("\n  Đúng thứ tự thì chạy lại kèm --lam. Sai thì thả tay vào đúng thư mục "
              "clips/ của từng tập.")
        return 0
    for i in range(n):
        d = os.path.join(trong[i], "clips")
        os.makedirs(d, exist_ok=True)
        shutil.copy2(moi[i], os.path.join(d, "scene-01" + os.path.splitext(moi[i])[1]))
    print(f"\n   ✅ đã gán {n} video (bản gốc giữ nguyên chỗ cũ)")
    return 0


# ── MỘT TẬP TRỌN VẸN ────────────────────────────────────────────────────────────────────────
def mot_tap(tm: str, kenh_dang: str = "", keys=None) -> str:
    """clip → video → bài đăng → kho. Trả 'day' | 'xong' | 'cho' | 'hong'."""
    tap = json.load(io.open(os.path.join(tm, "tap.json"), encoding="utf-8"))
    ten = os.path.basename(tm)
    if os.path.exists(os.path.join(tm, ".da_day")):
        return "day"
    if not _clip(tm):
        return "cho"

    v = os.path.join(tm, "video.mp4")
    if not os.path.exists(v):
        v = dung_video(tm)
        if not v:
            print(f"   ❌ {ten}: dựng video hỏng")
            return "hong"

    bp = os.path.join(tm, "bai_dang.json")
    if os.path.exists(bp):
        bai = json.load(io.open(bp, encoding="utf-8"))
    else:
        bai = _gon(viet_bai(tap, tap.get("_kenh") or "HOUSE RULES", keys), tap)
        io.open(bp, "w", encoding="utf-8").write(json.dumps(bai, ensure_ascii=False, indent=2))
    moc = " (bài mộc — AI không gọi được)" if bai.get("_moc") else ""
    print(f"   📝 {ten}: {(bai.get('youtube') or {}).get('title')!r}{moc}")

    if not kenh_dang:
        print(f"      ✅ video + bài đăng + ảnh bìa xong (chưa đẩy kho — thiếu --kenh-dang)")
        return "xong"
    bia = os.path.join(tm, "bia.jpg")
    if not os.path.exists(bia):
        bia = lam_bia(tm, tap, v)
    if bia:
        print(f"      🖼  ảnh bìa: khung ở nhịp hook (không lộ cú lật)")

    if day_kho(tm, kenh_dang, v, bai, tap, bia):
        io.open(os.path.join(tm, ".da_day"), "w").write("1")
        print(f"      📤 đã vào kho — khâu đăng tự lấy như 50 kênh kia")
        return "day"
    print(f"      ⚠️ đẩy kho hụt — giữ file, chạy lại sau")
    return "hong"


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Đồng bộ video Kling tải về vào kênh.")
    ap.add_argument("--hop", default="", help="thư mục chứa video mới tải (vd ~/Downloads)")
    ap.add_argument("--lam", action="store_true", help="thực hiện thật, không chỉ xem trước")
    ap.add_argument("--kenh-dang", default="", help="mã kênh bên khâu đăng; bỏ trống = không đẩy kho")
    a = ap.parse_args()

    if a.hop:
        return hop_thu(os.path.expanduser(a.hop), a.lam)

    ts = _tap_dir()
    if not ts:
        print("   (chưa có tập nào — chạy kling_kenh.py trước)")
        return 0
    dem = {"day": 0, "xong": 0, "cho": 0, "hong": 0}
    for t in ts:
        dem[mot_tap(t, a.kenh_dang)] += 1
    print(f"\n  📤 vào kho {dem['day']}  ·  ✅ xong tại chỗ {dem['xong']}  ·  "
          f"⏸️ chờ clip {dem['cho']}  ·  ❌ hỏng {dem['hong']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
