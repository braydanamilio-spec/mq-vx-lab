"""
qc_vision.py — QC THẨM MỸ bằng Gemini Vision. Trích 1 still -> hỏi Gemini: có chồng chéo/xấu không?
Mảnh cuối để đảm bảo 100% khung hình đẹp trước khi đăng. Fail-OPEN (lỗi Vision -> KHÔNG chặn, giữ chạy).
"""
from __future__ import annotations
import os
import subprocess
import content_brain as CB

# BÁO HẾT QUOTA RA NGOÀI: các hàm dưới đây đều fail-open (nuốt lỗi, trả kết quả "cho qua") để một
# lỗi Vision không chặn cả dây chuyền. Nhưng nuốt luôn cả 429 thì caller KHÔNG BIẾT để đổi key ->
# lượt 20/8 ăn 1590 lỗi 429 mà cơ chế xoay key không chạy lần nào vì không nhận được tín hiệu.
# Caller nào cần biết thì gán qc_vision.on_quota = hàm_của_mình; ai không gán thì hành vi y như cũ.
on_quota = None


def _report_quota(err):
    if on_quota and any(x in str(err) for x in ("429", "quota", "exceeded", "RESOURCE_EXHAUSTED")):
        try:
            on_quota(err)
        except Exception:
            pass


def verify_image(path: str, subject: str, api_key: str = None, model_name: str = None):
    """Gemini Vision: ảnh này có RÕ RÀNG là `subject` không? (dùng cho GUESS — ép ảnh khớp đáp án 100%).
    Trả True (khớp) / False (KHÔNG khớp) / None (không kiểm được -> Vision lỗi/quota). None để caller fail-open."""
    try:
        genai = CB._genai(api_key)
        akey = api_key or os.environ.get("GEMINI_API_KEY", "")
        mn = model_name or CB._pick_model(genai, "flash", akey) or "gemini-3.5-flash"
        model = genai.GenerativeModel(mn)
        prompt = (f'Look at this photo. Does it CLEARLY and RECOGNIZABLY show: "{subject}"? '
                  f'Count it as a match ONLY if someone familiar with "{subject}" would confidently recognize it '
                  f'(e.g. an iconic skyline/landmark/subject actually visible). A generic, ambiguous, or unrelated '
                  f'photo (random construction, plain building, wrong place) is NOT a match. '
                  'ALSO set match=false if a LARGE watermark, logo, or a text caption bar covers a significant part '
                  'of the image (small unobtrusive credits are OK). '
                  'Return STRICT JSON only: {"match": true|false, "see": "<=6 words of what is shown"}')
        img = {"mime_type": "image/jpeg", "data": open(path, "rb").read()}
        resp = model.generate_content([prompt, img],
                                      generation_config={"response_mime_type": "application/json", "temperature": 0.0},
                                      request_options={"timeout": 30})   # cùng bug thiếu timeout như check_visual() — xem comment ở đó
        r = CB._extract_json(resp.text) or {}
        return bool(r.get("match"))
    except Exception as e:
        _report_quota(e)
        print(f"   ⚠️ verify_image lỗi (bỏ qua kiểm): {str(e)[:70]}")
        return None


def _stills(mp4: str, fracs=(0.4, 0.7)):
    """Trích VÀI khung ở các mốc ỔN ĐỊNH (giữa race), tránh intro/outro/chuyển cảnh."""
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nk=1:nw=1", mp4], capture_output=True, text=True).stdout.strip()
    try:
        d = float(dur)
    except ValueError:
        d = 10.0
    outs = []
    for i, fr in enumerate(fracs):
        at = max(1.0, d * fr)
        out = f"{mp4}.qc{i}.jpg"
        subprocess.run(["ffmpeg", "-y", "-ss", str(at), "-i", mp4, "-frames:v", "1",
                        "-vf", "scale=720:-1", out], capture_output=True)
        if os.path.exists(out):
            outs.append(out)
    return outs


def check_visual(mp4: str, api_key: str = None, model_name: str = None, min_score: int = 55):
    """QC thẩm mỹ LƯỢNG THỨ: nhiều khung -> lấy điểm CAO NHẤT (1 khung chuyển cảnh xấu không giết cả video).
    Chỉ loại video THẬT SỰ hỏng (đen/vỡ/chồng nặng khắp nơi). Fail-OPEN khi lỗi Vision. Trả (ok, info)."""
    stills = _stills(mp4)
    if not stills:
        return True, {"note": "no-still-skip"}
    try:
        genai = CB._genai(api_key)
        akey = api_key or os.environ.get("GEMINI_API_KEY", "")
        mn = model_name or CB._pick_model(genai, "flash", akey) or "gemini-3.5-flash"
        model = genai.GenerativeModel(mn)
        prompt = ("This is ONE frame from a data-story video (dense labels/numbers are NORMAL). Rate visual quality 0-100. "
                  "CHECK and LIST in issues any of: (a) elements OVERLAPPING/OCCLUDING each other (caption over watermark, "
                  "label over label, image over text); (b) text/numbers CUT OFF at frame edges; (c) any image too SMALL/awkward "
                  "or OVERFLOWING the frame edges; (d) mostly black/empty. "
                  "Only give score <50 if GENUINELY broken (severe overlap everywhere, mostly black, major cutoff). "
                  "Clean, readable, well-sized = 80+. "
                  'Return STRICT JSON only: {"score": 0-100, "occluded": true|false, "issues": [str]}')
        scores, issues = [], []
        for st in stills:
            img = {"mime_type": "image/jpeg", "data": open(st, "rb").read()}
            # request_options timeout=30s: KHÔNG có timeout -> lệnh gọi Gemini Vision từng bị TREO VÔ THỜI
            # HẠN khi mạng/API chập chờn (mất mạng KHÔNG throw exception -> except bên dưới không bắt được),
            # kẹt job ở "qc" hàng giờ, gần hết cả 40 kênh cùng lúc bị treo (phát hiện 20/8). Có timeout ->
            # hết giờ tự throw TimeoutError -> except fail-open bên dưới bắt được, video qua QC bình thường.
            resp = model.generate_content([prompt, img],
                                          generation_config={"response_mime_type": "application/json", "temperature": 0.1},
                                          request_options={"timeout": 30})
            r = CB._extract_json(resp.text) or {}
            sc = float(r.get("score", 0) or 0)
            scores.append(sc)
            issues += (r.get("issues") or [])
            if sc >= min_score + 20:      # khung này đã RÕ ĐẸP -> khỏi soi thêm khung (TIẾT KIỆM token Gemini free)
                break
        if not scores:
            return True, {"note": "vision-empty-skip"}
    except Exception as e:
        _report_quota(e)
        return True, {"note": f"vision-skip: {str(e)[:80]}"}   # fail-open
    best = max(scores)
    return best >= min_score, {"score": round(best), "avg": round(sum(scores) / len(scores)), "frames": len(scores), "issues": issues[:4]}


def check_thumb(jpg: str, title: str = "", api_key: str = None, model_name: str = None,
                min_score: int = 60):
    """QC VISUAL RIÊNG CHO THUMBNAIL (ảnh tĩnh 1280x720) — trước đây CHỈ video được soi, thumbnail
    đẩy thẳng lên Drive không ai kiểm, nên lỗi chữ tràn/chồng/nền chán lọt hết ra ngoài.

    Soi đúng những lỗi CHẾT NGƯỜI của thumbnail:
      - chữ TRÀN/CẮT CỤT ở mép khung (lỗi đã gặp thật: hook lòi ra ngoài nền pill)
      - chữ ĐÈ NHAU / đè lên chủ thể chính của ảnh
      - chữ không đọc nổi (tương phản kém với nền)
      - nền trống trơn/đơn điệu (thiếu ảnh thật) -> khuyên đổi nền
    Trả (ok, info). Fail-OPEN khi Vision lỗi/hết quota (không chặn cả mẻ vì QC hỏng)."""
    if not os.path.exists(jpg):
        return True, {"note": "no-thumb-skip"}
    try:
        genai = CB._genai(api_key)
        akey = api_key or os.environ.get("GEMINI_API_KEY", "")
        mn = model_name or CB._pick_model(genai, "flash", akey) or "gemini-3.5-flash"
        model = genai.GenerativeModel(mn)
        prompt = (
            "This is a YouTube THUMBNAIL (1280x720). Judge it as a thumbnail, not as a photo.\n"
            "Score 0-100 and LIST every problem you actually see in `issues`:\n"
            "(a) any text CUT OFF or running past the frame edge;\n"
            "(b) text OVERLAPPING other text, or text spilling outside its colored button/pill background;\n"
            "(c) text hard to read (poor contrast against what is behind it);\n"
            "(d) the background is empty/plain/monotone with no real imagery;\n"
            "(e) the big number and the small label under it collide or touch.\n"
            + (f'The thumbnail is for a video titled: "{title}". Set topic_match=false if the background '
               "image clearly shows something unrelated to that title.\n" if title else "")
            + "Clean, fully-visible, readable text with real imagery behind it = 85+. "
            "Score below 60 ONLY if genuinely broken (text cut off, overlapping, or unreadable).\n"
            'Return STRICT JSON only: {"score": 0-100, "issues": [str], "topic_match": true|false}'
        )
        img = {"mime_type": "image/jpeg", "data": open(jpg, "rb").read()}
        resp = model.generate_content([prompt, img],
                                      generation_config={"response_mime_type": "application/json", "temperature": 0.1},
                                      request_options={"timeout": 30})
        r = CB._extract_json(resp.text) or {}
    except Exception as e:
        _report_quota(e)
        return True, {"note": f"vision-skip: {str(e)[:80]}"}   # fail-open
    sc = float(r.get("score", 0) or 0)
    info = {"score": round(sc), "issues": (r.get("issues") or [])[:4], "topic_match": r.get("topic_match")}
    return sc >= min_score, info
