#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHẤM HÌNH BẰNG THỊ GIÁC — ghép nhiều khung vào MỘT tấm, gọi Gemini một lần.  (1/9/2026)

Anh: *"xây rule chấm tự động như trước em làm được mà, dùng gemini hay tiêu chuẩn đầu vào để
chấm, ghép nhiều ảnh vào 1 tấm để check chấm."*

── VÌ SAO GHÉP THÀNH MỘT TẤM, KHÔNG GỬI TỪNG KHUNG ─────────────────────────────────────────
Không phải để tiết kiệm lượt gọi (dù có tiết kiệm). Lý do thật: **lỗi nặng nhất của bộ này là
lỗi GIỮA CÁC KHUNG, không phải trong một khung.** Mười lăm ảnh mỗi ảnh một chất vẽ — soi từng
tấm thì tấm nào cũng ổn, ghép lại mới thấy hỏng. Gửi từng khung là hỏi sai câu hỏi.

Đây đúng bài học đã ghi ở CLAUDE.md 12.11: lần đầu tôi soi 25 khung RỜI RẠC và chỉ rút được
"bảy khuôn hình"; cắt 24 cảnh LIÊN TIẾP mới thấy ngữ pháp. Cổng cũng vậy.

── QUAN HỆ VỚI `kiem_hinh.py` ──────────────────────────────────────────────────────────────
Hai cổng làm hai việc khác nhau, không thay nhau:
  · `kiem_hinh.py` đo thứ TÍNH ĐƯỢC — nhịp cắt, tương phản WCAG, LUFS, tỉ lệ khung. Chính xác
    tuyệt đối, chạy không cần mạng, và là cổng CÓ QUYỀN CHẶN.
  · `cham_hinh.py` (tệp này) hỏi thứ KHÔNG tính được — nhìn có ra một bộ phim không, có chỗ
    nào chồng chéo không, có đọc ra "nghiệp dư" không. Nó **cố vấn**, không chặn.

Không cho model chặn vì hai lẽ: nó không tái lập (cùng ảnh, hai lần hỏi ra hai điểm khác nhau),
và khi mạng hỏng thì cả đường chạy dừng. Một cổng chặn phải là cổng tất định.

── THANG ĐIỂM ĐƯA CHO MODEL ────────────────────────────────────────────────────────────────
Hỏi "ảnh này đẹp không" thì nhận về một con số vô nghĩa. Nên hỏi SÁU câu cụ thể, mỗi câu có
tiêu chí kiểm được, và bắt trả JSON để không phải đoán ý.
"""
import argparse
import io
import json
import os
import re
import subprocess
import tempfile

GOC = os.path.dirname(os.path.abspath(__file__))

RUBRIC = """You are reviewing a frame grid from ONE episode of a US explainer video channel.
The grid shows 9 frames sampled evenly across the episode, left to right, top to bottom.

Score each item 0-100 and reply with ONLY a JSON object, no prose:

{"dong_bo": 0-100,   // do all 9 frames look like ONE authored series? same drawing style,
                     //   same character design, same colour world? A mix of photo-real and
                     //   cartoon, or a different-looking character, scores below 50.
 "che_khuat": 0-100, // is any text, number or chart overlapping a subject's face or body,
                     //   or running off the edge? Fully clear = 100.
 "doc_duoc": 0-100,  // is every piece of on-screen text easy to read at phone size?
 "bo_cuc": 0-100,    // is each frame composed with a clear focal point and calm margins?
 "chuyen_nghiep": 0-100, // does this look like a top US channel, or like an amateur template?
                     //   Cheap tells: outlined text, hard drop shadows, watermark bars,
                     //   clip-art icons sitting on top of illustrations, cluttered frames.
 "usa": 0-100,       // does the setting, clothing and styling read as United States?
 "loi": ["short specific defect", "..."]   // at most 4, each naming the frame number
}"""


def luoi(mp4: str, n: int = 9, rong: int = 1400) -> str:
    """Ghép `n` khung rải đều thành MỘT tấm lưới 3×3. Trả đường dẫn, hoặc "" nếu hỏng."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=duration,width,height", "-of", "json", mp4],
                       capture_output=True, text=True)
    try:
        st = json.loads(r.stdout)["streams"][0]
        dai = float(st.get("duration", 0))
        W, H = int(st["width"]), int(st["height"])
    except Exception:
        return ""
    if dai <= 0:
        return ""
    try:
        from PIL import Image
    except Exception:
        return ""

    tam = tempfile.mkdtemp(prefix="luoi_")
    o_w = rong // 3
    o_h = int(o_w * H / W)
    lu = Image.new("RGB", (o_w * 3, o_h * 3), "white")
    dem = 0
    for i in range(n):
        t = dai * (i + 0.5) / n
        p = os.path.join(tam, f"{i}.png")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", mp4,
                        "-frames:v", "1", "-vf", f"scale={o_w}:{o_h}", p], capture_output=True)
        if os.path.exists(p):
            lu.paste(Image.open(p).convert("RGB"), ((i % 3) * o_w, (i // 3) * o_h))
            dem += 1
    if dem < 4:
        return ""
    # Đánh số từng ô để model chỉ được ĐÍCH DANH khung nào hỏng — không có số thì nó chỉ nói
    # chung chung, và lời phê chung chung thì không sửa được gì.
    try:
        from PIL import ImageDraw
        d = ImageDraw.Draw(lu)
        for i in range(9):
            x, y = (i % 3) * o_w + 8, (i // 3) * o_h + 6
            d.rectangle([x, y, x + 34, y + 30], fill="#111111")
            d.text((x + 12, y + 8), str(i + 1), fill="#FFFFFF")
    except Exception:
        pass
    out = os.path.join(tam, "luoi.jpg")
    lu.save(out, "JPEG", quality=88)
    return out


def cham(mp4: str, keys=None) -> tuple:
    """Chấm một video. Trả (điểm 0-100, [lỗi], đường dẫn lưới) — (None, [], luoi) nếu không hỏi được."""
    lu = luoi(mp4)
    if not lu:
        return None, ["không ghép được lưới khung"], ""
    try:
        import content_brain as CB
        import the_he_2 as T2
    except Exception:
        return None, ["không nạp được đường thị giác"], lu

    ks = keys or [(k if isinstance(k, str) else k.get("key", ""))
                  for k in (T2.keys_cuc_bo() or [])]
    ks = [k for k in ks if k and not k.startswith(("cf:", "px:", "pb:"))]
    dl = io.open(lu, "rb").read()

    for k in ks[:8]:
        try:
            g = CB._genai(k)
            r = g.GenerativeModel(CB.MODEL).generate_content(
                [RUBRIC, {"mime_type": "image/jpeg", "data": dl}])
            t = str(getattr(r, "text", "") or "")
            m = re.search(r"\{[\s\S]*\}", t)
            if not m:
                continue
            j = json.loads(m.group(0))
            muc = ["dong_bo", "che_khuat", "doc_duoc", "bo_cuc", "chuyen_nghiep", "usa"]
            # Trọng số: đồng bộ và che khuất nặng nhất, vì đó là hai lỗi đã thật sự xảy ra và
            # là hai lỗi người xem thấy trong nửa giây.
            w = {"dong_bo": 0.28, "che_khuat": 0.22, "doc_duoc": 0.16,
                 "bo_cuc": 0.12, "chuyen_nghiep": 0.14, "usa": 0.08}
            diem = sum(float(j.get(x, 0)) * w[x] for x in muc)
            loi = [str(x)[:130] for x in (j.get("loi") or [])][:4]
            chi = " · ".join(f"{x}:{int(float(j.get(x,0)))}" for x in muc)
            return round(diem), [chi] + loi, lu
        except Exception:
            continue
    return None, ["mọi khoá đều không trả lời được"], lu


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tep", nargs="*")
    ap.add_argument("--nguong", type=int, default=90)
    a = ap.parse_args()
    ds = a.tep or sorted(os.path.join(GOC, "out", f)
                         for f in os.listdir(os.path.join(GOC, "out"))
                         if f.startswith("v9_") and f.endswith(".mp4"))
    duoi = 0
    for mp4 in ds:
        d, bao, lu = cham(mp4)
        ten = os.path.basename(mp4)
        if d is None:
            print(f"  ⚠  {ten:34s} không chấm được: {bao[0] if bao else '?'}")
            continue
        dau = "✅" if d >= a.nguong else "❌"
        print(f"  {dau} {ten:34s} {d}/100")
        for x in bao:
            print(f"        · {x}")
        if lu:
            print(f"        lưới: {lu}")
        if d < a.nguong:
            duoi += 1
    if duoi:
        print(f"\n⚠ {duoi} tệp dưới {a.nguong}. Đây là điểm CỐ VẤN — cổng chặn là `kiem_hinh.py`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
