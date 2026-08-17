"""
qc_vision.py — QC THẨM MỸ bằng Gemini Vision. Trích 1 still -> hỏi Gemini: có chồng chéo/xấu không?
Mảnh cuối để đảm bảo 100% khung hình đẹp trước khi đăng. Fail-OPEN (lỗi Vision -> KHÔNG chặn, giữ chạy).
"""
from __future__ import annotations
import os
import subprocess
import content_brain as CB


def _still(mp4: str, frac: float = 0.5):
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nk=1:nw=1", mp4], capture_output=True, text=True).stdout.strip()
    try:
        at = max(1.0, float(dur) * frac)
    except ValueError:
        at = 3.0
    out = mp4 + ".qc.jpg"
    subprocess.run(["ffmpeg", "-y", "-ss", str(at), "-i", mp4, "-frames:v", "1",
                    "-vf", "scale=720:-1", out], capture_output=True)
    return out if os.path.exists(out) else None


def check_visual(mp4: str, api_key: str = None, model_name: str = None, min_score: int = 85):
    """Trả (ok, info). ok=False nếu chồng chéo hoặc điểm < min_score."""
    still = _still(mp4)
    if not still:
        return True, {"note": "no-still-skip"}
    try:
        genai = CB._genai(api_key)
        akey = api_key or os.environ.get("GEMINI_API_KEY", "")
        mn = model_name or CB._pick_model(genai, "flash", akey) or "gemini-3.5-flash"
        model = genai.GenerativeModel(mn)
        img = {"mime_type": "image/jpeg", "data": open(still, "rb").read()}
        prompt = ("This is one frame from a data bar-chart-race video. Rate its visual quality 0-100. "
                  "Give a LOW score if ANY: text or numbers overlap each other, text/numbers cut off at "
                  "frame edges, unreadable or low contrast, frame is mostly black/empty, or it looks broken. "
                  "High score = clean, readable, professional, nothing overlapping. "
                  'Return STRICT JSON only: {"score": 0-100, "overlap": true|false, "issues": [str]}')
        resp = model.generate_content([prompt, img],
                                      generation_config={"response_mime_type": "application/json", "temperature": 0.1})
        r = CB._extract_json(resp.text)
    except Exception as e:
        return True, {"note": f"vision-skip: {str(e)[:80]}"}   # fail-open
    ok = (r.get("score", 0) >= min_score) and not r.get("overlap")
    return ok, r
