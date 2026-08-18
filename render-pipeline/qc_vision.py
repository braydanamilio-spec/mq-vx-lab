"""
qc_vision.py — QC THẨM MỸ bằng Gemini Vision. Trích 1 still -> hỏi Gemini: có chồng chéo/xấu không?
Mảnh cuối để đảm bảo 100% khung hình đẹp trước khi đăng. Fail-OPEN (lỗi Vision -> KHÔNG chặn, giữ chạy).
"""
from __future__ import annotations
import os
import subprocess
import content_brain as CB


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
                  'Return STRICT JSON only: {"match": true|false, "see": "<=6 words of what is shown"}')
        img = {"mime_type": "image/jpeg", "data": open(path, "rb").read()}
        resp = model.generate_content([prompt, img],
                                      generation_config={"response_mime_type": "application/json", "temperature": 0.0})
        r = CB._extract_json(resp.text) or {}
        return bool(r.get("match"))
    except Exception as e:
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
            resp = model.generate_content([prompt, img],
                                          generation_config={"response_mime_type": "application/json", "temperature": 0.1})
            r = CB._extract_json(resp.text) or {}
            sc = float(r.get("score", 0) or 0)
            scores.append(sc)
            issues += (r.get("issues") or [])
            if sc >= min_score + 20:      # khung này đã RÕ ĐẸP -> khỏi soi thêm khung (TIẾT KIỆM token Gemini free)
                break
        if not scores:
            return True, {"note": "vision-empty-skip"}
    except Exception as e:
        return True, {"note": f"vision-skip: {str(e)[:80]}"}   # fail-open
    best = max(scores)
    return best >= min_score, {"score": round(best), "avg": round(sum(scores) / len(scores)), "frames": len(scores), "issues": issues[:4]}
