"""
content_brain.py — BỘ NÃO viết kịch bản "Data-Story điện ảnh" (USA).

Thực thi BRAIN_RULES.md: ép Gemini viết theo khuôn, TỰ CHẤM ĐIỂM, trượt thì viết lại.
Đầu ra = 1 JSON chuẩn nuôi cả:
  - RENDER   (race.frames  + narration)   -> Remotion
  - ĐĂNG BÀI (title/description/hashtags/tags) -> enqueue.py

Chạy:
    export GEMINI_API_KEY=...          # tạo free ở aistudio.google.com
    python content_brain.py --type short --seed "US billionaire wealth" --out story.json

Không có key -> in hướng dẫn, không crash pipeline.
"""
from __future__ import annotations
import argparse
import json
import os
import sys

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")  # Google đã lên 3.x (2.5 bỏ với key mới). Auto-dò nếu 404.
_MODEL_CACHE = {}   # key -> {"flash":..., "pro":...}  (dò 1 lần/key)


def _pick_model(genai, prefer="flash", api_key=""):
    """Tự chọn model KHẢ DỤNG cho key này (mỗi key có bộ model khác nhau) -> chống 404."""
    cache = _MODEL_CACHE.get(api_key)
    if not cache:
        bad = ("image", "tts", "robotics", "embedding", "lyria", "computer-use", "deep-research", "nano", "vision")
        try:
            ms = [m.name.replace("models/", "") for m in genai.list_models()
                  if "generateContent" in m.supported_generation_methods]
        except Exception:
            ms = []
        ms = [m for m in ms if not any(b in m for b in bad)]
        flash = ([m for m in ms if "flash" in m and "lite" not in m and "preview" not in m]
                 or [m for m in ms if "flash" in m] or ms)
        pro = ([m for m in ms if "pro" in m] or flash)
        cache = {"flash": flash[0] if flash else None, "pro": pro[0] if pro else None}
        _MODEL_CACHE[api_key] = cache
    return cache.get(prefer) or cache.get("flash")
MIN_SCORE = 90         # thang 100 — < 90 -> viết lại (chuẩn top USA)
MAX_TRIES = 3          # số vòng viết lại tối đa

# --------------------------------------------------------------------------- #
#  SYSTEM PROMPT — đóng khuôn chất lượng (bản rút gọn của BRAIN_RULES.md)
# --------------------------------------------------------------------------- #
_GENERIC_SYSTEM = """You write short, punchy, factual US data-story scripts for a faceless channel.
Return strict JSON per the requested schema. Keep it accurate and engaging."""
# BÍ KÍP thật: nạp từ GitHub Secret GEMINI_SYSTEM_PROMPT (không hardcode -> public không lộ).
SYSTEM = os.environ.get("GEMINI_SYSTEM_PROMPT") or _GENERIC_SYSTEM

# JSON schema mô tả cho model (nhúng vào prompt để ép đúng cấu trúc)
SCHEMA_HINT = """Return JSON with EXACTLY these keys:
{
  "topic": str,                       // chủ đề ngắn gọn
  "title": str,                       // tiêu đề YouTube (<=70 ký tự, hút, không clickbait rẻ tiền)
  "description": str,                 // mô tả 2-4 câu + để trống dòng cuối cho CTA/nguồn
  "hashtags": [str],                  // 3-5 hashtag mạnh, có dấu #
  "tags": [str],                      // 5-12 keyword SEO (không #)
  "hook": str,                        // câu HOOK 3s đầu (reveal cốt lõi/sốc, đứng riêng, ĐỌC lên)
  "hook_title": str,                  // 2-4 TỪ IN HOA cho màn hook lớn, dùng \\n xuống dòng (vd "WHO RULES\\nAMERICA?")
  "hook_stat": str,                   // con số SỐC ngắn hiện to màu vàng (vd "39M", "8.2%", "$1.2T")
  "hook_caption": str,                // 1 dòng ngắn dưới số (vd "California leads — for now")
  "twist": str,                       // 1 câu mô tả cú lật cuối
  "sources": [str],                   // nguồn dữ liệu thật đã dùng
  "narration": [                      // SHORT: 5-7 dòng | LONG: 12-16 dòng. Mỗi dòng 1 CÂU NGẮN (~8-14 từ).
     { "text": str,                   // SHORT tổng giọng phải < 55 giây -> câu ngắn gọn, không lê thê.
       "visual": { "query": str } }   // 2-5 TỪ KHOÁ CỤ THỂ để TÌM ẢNH THẬT (địa danh/vật/cảnh), KHÔNG phải câu mô tả.
  ],                                   // VD tốt: "us dollar bills", "wall street building", "texas oil field", "empty classroom"
  "race": {
     "title_label": str,              // nhãn góc (vd "US State Population")
     "unit": str,                     // đơn vị (vd "million")
     "frames": [                      // >=4 mốc thời gian, mỗi mốc 4-7 mục
        {"t": number, "data": [ {"name": str, "value": number} ] }
     ]
  },
  "self_score": {                     // thang 100, tự chấm KHẮT
     "hook":0-20, "surprise":0-20, "pace_no_repeat":0-15, "accuracy":0-15,
     "natural_us_voice":0-15, "memorability":0-10, "visual_variety":0-5, "total":0-100
  }
}
Every narration line MUST have a distinct 'visual' (adjacent lines must differ) so the video never looks repetitive."""


class RateLimited(Exception):
    """Key hết quota/bị rate-limit -> tầng trên đổi key khác."""


def _genai(api_key=None):
    try:
        import google.generativeai as genai
    except ImportError:
        raise SystemExit("❌ Thiếu thư viện. Cài: pip install google-generativeai")
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit(
            "❌ Chưa có GEMINI_API_KEY.\n"
            "   Tạo FREE tại https://aistudio.google.com/apikey rồi:\n"
            "   export GEMINI_API_KEY=xxx   (hoặc thêm vào GitHub Secrets)"
        )
    genai.configure(api_key=key)
    return genai


def _extract_json(text: str) -> dict:
    """Model đôi khi bọc ```json ... ``` -> bóc ra."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    return json.loads(t.strip())


def _validate(story: dict, vtype: str) -> list[str]:
    """Kiểm cứng cấu trúc + luật đếm được. Trả list lỗi (rỗng = đạt)."""
    errs = []
    for k in ("title", "description", "narration", "race", "self_score"):
        if not story.get(k):
            errs.append(f"thiếu '{k}'")
    race = story.get("race") or {}
    frames = race.get("frames") or []
    if len(frames) < 4:
        errs.append("race.frames < 4 mốc")
    for i, fr in enumerate(frames):
        if not fr.get("data"):
            errs.append(f"frame[{i}] rỗng data")
        for d in fr.get("data", []):
            if "name" not in d or not isinstance(d.get("value"), (int, float)):
                errs.append(f"frame[{i}] item sai name/value")
                break
    title = story.get("title", "")
    if len(title) > 80:
        errs.append("title quá dài (>80)")
    if not story.get("hook"):
        errs.append("thiếu 'hook' (câu 3s đầu)")
    # mỗi narration phải có visual; visual liền kề KHÔNG được trùng (chống lặp/nhàm)
    narr = story.get("narration", [])
    prev_q = None
    for i, s in enumerate(narr):
        vis = s.get("visual") or {}
        q = (vis.get("query") or "").strip().lower()
        if not q:
            errs.append(f"narration[{i}] thiếu visual.query")
        elif q == prev_q:
            errs.append(f"narration[{i}] visual trùng đoạn trước (gây lặp)")
        prev_q = q
    # điểm phải theo thang 100
    if (story.get("self_score") or {}).get("total", 0) > 100:
        errs.append("self_score.total sai thang (>100)")
    # cấm cụm sáo AI
    banned = ["let's dive in", "in today's video", "you won't believe",
              "buckle up", "results may surprise you"]
    blob = (title + " " + story.get("description", "") + " " + story.get("hook", "") + " " +
            " ".join(s.get("text", "") for s in narr)).lower()
    for b in banned:
        if b in blob:
            errs.append(f"dính cụm sáo AI: '{b}'")
    return errs


def generate(seed: str, vtype: str = "short", api_key: str = None, model_name: str = None) -> dict:
    """Sinh 1 data-story đạt chuẩn. Vòng lặp viết-lại tới khi >= MIN_SCORE hoặc hết lượt.
    api_key/model_name: cho phép key_manager truyền key + model theo từng kênh (bám key, đổi khi limit)."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    model = genai.GenerativeModel(mname, system_instruction=SYSTEM)
    resolved = False

    dur = "a SHORT (<60 seconds, vertical)" if vtype == "short" else "a LONG (>=8 minutes, horizontal)"
    base = (f"Create {dur} cinematic data-story for a US audience.\n"
            f"Seed idea / niche: {seed!r}\n\n{SCHEMA_HINT}")

    feedback = ""
    last = None
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base + (f"\n\nPrevious attempt was rejected: {feedback}\nFix it and raise the score." if feedback else "")
        try:
            resp = model.generate_content(
                prompt,
                generation_config={"temperature": 0.9, "response_mime_type": "application/json"},
            )
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and not resolved:
                mn = _pick_model(genai, prefer, akey)      # tự chọn model khả dụng cho key này
                resolved = True
                if mn and mn != mname:
                    print(f"   ↻ model 404 → tự chọn {mn}")
                    mname = mn; model = genai.GenerativeModel(mn, system_instruction=SYSTEM)
                    continue
            if "429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg or "ratelimit" in msg:
                raise RateLimited(str(e))     # tầng trên đổi sang key khác
            raise
        try:
            story = _extract_json(resp.text)
        except Exception as e:
            feedback = f"JSON parse lỗi ({e}). Trả JSON hợp lệ đúng schema."
            continue

        errs = _validate(story, vtype)
        score = (story.get("self_score") or {}).get("total", 0)
        story["_attempt"] = attempt
        last = story

        if errs:
            feedback = "Lỗi cấu trúc: " + "; ".join(errs)
            print(f"   ↻ vòng {attempt}: {feedback}")
            continue
        if score < MIN_SCORE:
            feedback = f"Điểm tự chấm {score}/100 < {MIN_SCORE}. Viết lại hay hơn (hook reveal mạnh hơn, twist sắc hơn, bớt lặp)."
            print(f"   ↻ vòng {attempt}: điểm {score}/100 — viết lại")
            continue

        story["vtype"] = vtype
        print(f"   ✅ đạt vòng {attempt}: {score}/100 — {story['title']!r}")
        return story

    raise SystemExit(f"❌ Sau {MAX_TRIES} vòng vẫn chưa đạt chuẩn (điểm cuối "
                     f"{(last or {}).get('self_score', {}).get('total', '?')}/100). "
                     f"Bỏ chủ đề {seed!r} — chọn chủ đề khác. (Đúng tinh thần: thà bỏ còn hơn ra rác.)")


PILLAR_SYS = ("You plan themed content for a TOP US data channel. Given a niche, propose DISTINCT, "
              "surprising, data-backed bar-chart-race sub-topics — each a different angle, US-relevant, "
              "with REAL public data available. No overlap between sub-topics. No sensitive/political-partisan topics.")


def plan_pillar(niche: str, n: int = 6, api_key: str = None, model_name: str = None) -> dict:
    """Lập 1 pillar cho video LONG: {pillar_title, hook, subtopics:[str x n]} — mỗi subtopic 1 race khác nhau."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    prompt = (f'Niche: "{niche}". Propose {n} DISTINCT sub-topics for a US bar-chart-race compilation. '
              f'Return STRICT JSON: {{"pillar_title": str (<=40 chars, punchy), "hook": str (one shock line), '
              f'"subtopics": [str x {n}]}}. Each subtopic = short search-friendly phrase, real US data, different angle.')
    for _try in range(2):
        try:
            model = genai.GenerativeModel(mname, system_instruction=PILLAR_SYS)
            resp = model.generate_content(prompt, generation_config={"temperature": 0.95, "response_mime_type": "application/json"})
            break
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and _try == 0:
                mn = _pick_model(genai, prefer, akey)
                if mn: mname = mn; continue
            if "429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg:
                raise RateLimited(str(e))
            raise
    d = _extract_json(resp.text)
    d["subtopics"] = [s for s in (d.get("subtopics") or []) if s][:n]
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", dest="vtype", choices=["long", "short"], default="short")
    ap.add_argument("--seed", required=True, help="Chủ đề/niche gợi ý cho Gemini")
    ap.add_argument("--out", default="story.json", help="File JSON đầu ra")
    a = ap.parse_args()
    story = generate(a.seed, a.vtype)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)
    print(f"💾 Đã ghi {a.out}")


if __name__ == "__main__":
    main()
