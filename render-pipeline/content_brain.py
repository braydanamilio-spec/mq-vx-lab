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
        ok3 = lambda m: not any(v in m for v in ("2.5", "2.0", "1.5", "1.0"))   # né 2.x/1.x (list_models có nhưng gọi 404 với user MỚI)
        flash = ([m for m in ms if "flash" in m and "lite" not in m and "preview" not in m and ok3(m)]
                 or [m for m in ms if "flash" in m and ok3(m)]
                 or [m for m in ms if "flash" in m and "lite" not in m and "preview" not in m]
                 or [m for m in ms if "flash" in m] or ms)
        pro = ([m for m in ms if "pro" in m and ok3(m)] or [m for m in ms if "pro" in m] or flash)
        cache = {"flash": flash[0] if flash else None, "pro": pro[0] if pro else None}
        _MODEL_CACHE[api_key] = cache
    return cache.get(prefer) or cache.get("flash")
MIN_SCORE = 90         # thang 100 — < 90 -> viết lại (chuẩn top USA)
MAX_TRIES = 3          # số vòng viết lại tối đa — PHẢI đạt >= MIN_SCORE, chưa đạt thì viết lại (không hạ chuẩn)

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


def test_key(api_key: str):
    """Health check 1 key -> trả (alive, reason).
    alive=True SỐNG · False CHẾT THẬT (sai/khoá) · None KHÔNG CHẮC (lỗi tạm -> giữ trạng thái cũ, không đánh chết oan).
    Có THỬ LẠI để chống báo-chết-oan do trục trặc mạng tạm trên CI."""
    import time
    # 429/quota = SỐNG nhưng hết quota tạm (message có 'consumer' nên PHẢI check TRƯỚC DEAD, tránh báo chết oan).
    RATE = ("429", "quota", "rate limit", "rate-limit", "resource_exhausted",
            "resource exhausted", "exhausted", "too many requests")
    DEAD = ("api key not valid", "api_key_invalid", "invalid api key",
            "permission_denied", "permission denied", "forbidden", "disabled", "not enabled",
            "has not been used", "unregistered", "suspended", "401", "403")
    last = ""
    for i in range(3):
        try:
            genai = _genai(api_key)
            list(genai.list_models())
            return True, "ok"
        except Exception as e:
            last = str(e); low = last.lower()
            if any(s in low for s in RATE):
                return True, "sống (đang bị giới hạn quota tạm — tự hồi khi quota reset)"
            if any(s in low for s in DEAD):
                return False, last[:150]          # lỗi xác thực THẬT -> chết chắc
            time.sleep(1.2 * (i + 1))             # lỗi tạm (timeout/503/mạng) -> nghỉ rồi thử lại
    return None, ("không chắc: " + last[:130])    # hết lần thử vẫn lỗi tạm -> KHÔNG kết luận chết


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
            # 403/project bị CHẶN/khoá quyền -> KEY (project) này hỏng, TỰ ĐỔI sang key khác (project khác), đừng giết cả kênh.
            if ("denied" in msg or "permission" in msg or "forbidden" in msg or "403" in msg
                    or "suspended" in msg or "has not been used" in msg
                    or "not enabled" in msg or "disabled" in msg):
                raise RateLimited(str(e))     # coi như key hỏng -> rotate + cooldown -> health-check sau đánh dấu chết
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

    # PHẢI đạt >= MIN_SCORE: chưa đạt sau MAX_TRIES -> BỎ chủ đề (thà bỏ còn hơn ra rác), KHÔNG hạ chuẩn.
    raise Exception(f"Sau {MAX_TRIES} vòng vẫn < {MIN_SCORE} (điểm cuối "
                    f"{(last or {}).get('self_score', {}).get('total', '?')}/100). Bỏ {seed!r}.")


PILLAR_SYS = ("You plan themed content for a TOP US data channel. Given a niche, propose DISTINCT, "
              "surprising, data-backed bar-chart-race sub-topics — each a different angle, US-relevant, "
              "with REAL public data available. No overlap between sub-topics. No sensitive/political-partisan topics.")


def plan_pillar(niche: str, n: int = 6, api_key: str = None, model_name: str = None, avoid: list = None) -> dict:
    """Lập 1 pillar cho video LONG: {pillar_title, hook, subtopics:[str x n]} — mỗi subtopic 1 race khác nhau.
    avoid: danh sách chủ đề ĐÃ dùng -> BẮT BUỘC tránh (chống trùng lặp / reused content)."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    avoid_txt = ""
    if avoid:
        avoid_txt = ("\nDO NOT repeat or closely resemble ANY of these already-used topics "
                     "(pick completely fresh angles): " + " | ".join(avoid[-60:]))
    prompt = (f'Niche: "{niche}". Propose {n} DISTINCT sub-topics for a US bar-chart-race compilation. '
              f'Return STRICT JSON: {{"pillar_title": str (<=40 chars, punchy), "hook": str (one shock line), '
              f'"subtopics": [str x {n}]}}. Each subtopic = short search-friendly phrase, real US data, different angle.'
              + avoid_txt)
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


# ─────────────────────────────────────────────────────────────────────────────
# KÊNH #1 GUESS — sinh bộ câu đố. Ép LOGIC tuyệt đối + ẢNH khớp đáp án 100% + SẠCH bản quyền.
GUESS_SYS = (
 "You are the head writer of a #1 US 'guess the...' viral shorts channel. You produce guessing quizzes "
 "that are addictive, factually PERFECT, and copyright-safe. Absolute rules you never break:\n"
 "1) LOGIC: each clue must uniquely identify EXACTLY ONE real answer — no other real answer can fit. "
 "If a clue could point to two things, it is WRONG. State the unique_reason for every round.\n"
 "2) FACTS: every clue and every stat must be TRUE, real, publicly-verifiable. Never invent numbers. "
 "Prefer round, well-known figures. If unsure of a number, use a safer widely-known fact instead.\n"
 "3) IMAGE MATCH: img_query must describe the ANSWER's own subject so a stock/CC search returns an image "
 "that clearly SHOWS the answer (e.g. a city -> its skyline; a landmark -> the landmark; a company -> its "
 "product/headquarters). The shown image must match the answer 100%.\n"
 "4) COPYRIGHT SAFE (public-domain only): for a LIVING or recently-deceased person, NEVER require their photo — "
 "the image is their CONTEXT (company product, HQ, city) and the answer is their NAME as text. BUT for a "
 "long-dead historical figure (scientist/inventor/artist/leader who died 70+ years ago, e.g. Einstein, Newton, "
 "Tesla, da Vinci, Lincoln), a public-domain portrait/painting exists, so img_query CAN be their name/portrait. "
 "Great categories: famous US/EU landmarks & cities, historical geniuses & scientists, historical events, iconic places.\n"
 "5) DIFFICULTY rises each round. No politics/partisan, no tragedy, no NSFW.\n"
 "6) NARRATION is spoken aloud: punchy, dramatic, guides the viewer to guess, builds suspense on the countdown, "
 "then a satisfying reveal. Natural spoken English, short sentences."
)

GUESS_SCHEMA = """Return STRICT JSON with EXACTLY these keys:
{
  "title": str,                 // internal title
  "category": str,              // e.g. "US cities", "US billionaires' empires", "US landmarks"
  "intro_vo": str,              // 1-2 spoken sentences hooking + telling them to guess before time runs out
  "rounds": [                   // 3 to 5 rounds, difficulty rising
    {
      "q": str,                 // on-screen question, <=5 words, e.g. "Guess this US city"
      "clue": str,              // on-screen clue, <=8 words, 2-3 facts joined by " · " that UNIQUELY fit the answer
      "answer": str,            // the answer shown as TEXT (UPPERCASE), <=22 chars
      "stat": str,              // one TRUE shock stat about the answer, <=26 chars, may end with 1 emoji
      "img_query": str,         // search phrase describing the ANSWER's subject (matches answer 100%, CC0-friendly)
      "vo_clue": str,           // spoken while tiles reveal + countdown: tease the clue, tell them to guess
      "vo_reveal": str,         // spoken at reveal: name the answer + the stat, dramatic
      "unique_reason": str      // WHY this clue fits ONLY this answer (proof of unique logic)
    }
  ],
  "outro_vo": str,              // spoken CTA: ask their score, follow for daily
  "title_yt": str,              // YouTube title, punchy, <=70 chars, include the hook (e.g. "99% FAIL")
  "description": str,           // 2-3 lines
  "hashtags": [str],            // 4-6, no spaces
  "tags": [str],                // 8-12 SEO tags
  "self_score": { "logic": int, "uniqueness": int, "image_match": int, "hook": int, "total": int }
}
Every round MUST be solvable from the clue alone by a knowledgeable US viewer, and MUST have exactly one correct answer."""


def _validate_guess(d: dict) -> list[str]:
    errs = []
    rounds = d.get("rounds") or []
    if not isinstance(rounds, list) or not (3 <= len(rounds) <= 5):
        errs.append("cần 3–5 rounds")
    for i, r in enumerate(rounds):
        for k in ("q", "clue", "answer", "stat", "img_query", "vo_clue", "vo_reveal", "unique_reason"):
            if not str((r or {}).get(k, "")).strip():
                errs.append(f"round {i+1} thiếu '{k}'")
    for k in ("intro_vo", "outro_vo", "title_yt", "category"):
        if not str(d.get(k, "")).strip():
            errs.append(f"thiếu '{k}'")
    return errs


def generate_guess(category: str, n_rounds: int = 3, api_key: str = None, model_name: str = None,
                   avoid: list = None) -> dict:
    """Sinh 1 bộ câu đố GUESS đạt chuẩn (logic + khớp ảnh + sạch bản quyền). Viết lại tới khi self_score>=MIN_SCORE.
    avoid: danh sách đáp án ĐÃ dùng -> tránh trùng."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    model = genai.GenerativeModel(mname, system_instruction=GUESS_SYS)
    resolved = False
    avoid_txt = ("\nDo NOT reuse any of these already-used answers: " + " | ".join(avoid[-80:])) if avoid else ""
    base = (f'Make a "Guess the {category}" quiz for US viewers with EXACTLY {n_rounds} rounds, difficulty rising.\n'
            f'{GUESS_SCHEMA}{avoid_txt}')
    feedback = ""; last = None
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base + (f"\n\nPrevious attempt rejected: {feedback}\nFix and raise the score." if feedback else "")
        try:
            resp = model.generate_content(prompt, generation_config={"temperature": 0.85, "response_mime_type": "application/json"})
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and not resolved:
                mn = _pick_model(genai, prefer, akey); resolved = True
                if mn and mn != mname:
                    mname = mn; model = genai.GenerativeModel(mn, system_instruction=GUESS_SYS); continue
            if ("429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg or "ratelimit" in msg
                    or "denied" in msg or "permission" in msg or "forbidden" in msg or "403" in msg
                    or "suspended" in msg or "has not been used" in msg or "not enabled" in msg or "disabled" in msg):
                raise RateLimited(str(e))
            raise
        try:
            d = _extract_json(resp.text)
        except Exception as e:
            feedback = f"JSON lỗi ({e}). Trả JSON hợp lệ đúng schema."; continue
        errs = _validate_guess(d)
        sc = d.get("self_score") or {}
        score = sc.get("total", 0)
        # ép logic & khớp ảnh: 2 tiêu chí này PHẢI cao, không chỉ nhìn total
        logic_ok = min(int(sc.get("logic", 0)), int(sc.get("uniqueness", 0)), int(sc.get("image_match", 0)))
        d["_attempt"] = attempt; last = d
        if errs:
            feedback = "Lỗi cấu trúc: " + "; ".join(errs[:6]); print(f"   ↻ guess vòng {attempt}: {feedback}"); continue
        if logic_ok < 95:
            feedback = (f"logic/uniqueness/image_match={logic_ok}/100 < 95. Mỗi clue PHẢI chỉ đúng 1 đáp án; "
                        f"stat phải THẬT; img_query phải khiến ảnh hiện ĐÚNG đáp án. Sửa round yếu.")
            print(f"   ↻ guess vòng {attempt}: {feedback}"); continue
        if score < MIN_SCORE:
            feedback = f"Điểm {score}/100 < {MIN_SCORE}. Hook mạnh hơn, clue thông minh hơn, reveal sốc hơn."
            print(f"   ↻ guess vòng {attempt}: điểm {score} — viết lại"); continue
        d["vtype"] = "guess"
        print(f"   ✅ GUESS đạt vòng {attempt}: total {score}, logic {logic_ok} — {d.get('title_yt')!r}")
        return d
    raise Exception(f"GUESS sau {MAX_TRIES} vòng chưa đạt (logic {logic_ok if last else '?'}). Bỏ {category!r}.")


# ─────────────────────────────────────────────────────────────────────────────
# KÊNH #2 MAPPED — sinh 1 metric + số liệu THẬT theo bang US + narration (choropleth).
MAPPED_SYS = (
 "You are the data lead of a #1 US 'mapped' viral channel that reveals a single US metric as an animated map. "
 "Absolute rules:\n"
 "1) DATA IS REAL: every state value must be a TRUE, publicly-verifiable figure (US Census, BLS, CDC, FBI UCR, "
 "IRS, etc.). Never invent numbers. Cite the source + year. If unsure of exact values, choose a metric you KNOW.\n"
 "2) Use OFFICIAL state names (e.g. 'California', 'New York', 'Massachusetts'). Provide 18-30 states incl. the "
 "clear TOP 3 and a few notable/low ones so the map reads well.\n"
 "3) LOGIC: the ranking must be correct and internally consistent (top values really are the highest).\n"
 "4) NO politics/partisan, no tragedy exploitation. Metric must be broadly interesting to US viewers.\n"
 "5) NARRATION spoken aloud: punchy hook, build tension as the map 'heats up', dramatic top-3 reveal, CTA. Short natural sentences."
)

MAPPED_SCHEMA = """Return STRICT JSON with EXACTLY these keys:
{
  "title": str,            // on-screen metric title, <=28 chars, e.g. "HIGHEST INCOME BY STATE"
  "unit": str,             // small subtitle, e.g. "median household income"
  "source": str,           // e.g. "US Census, 2023"
  "data": [                // 18-30 states with REAL values
    { "state": str, "value": number, "disp": str }   // disp = formatted, e.g. "$98,461" or "12.4"
  ],
  "top": [                 // exactly 3, ranked #1..#3 (must match the 3 highest in data)
    { "state": str, "disp": str, "vo": str }          // vo = one spoken dramatic line naming state + figure
  ],
  "intro_vo": str,         // hook + what the map shows
  "bloom_vo": str,         // spoken while the whole map colors in (the pattern/story)
  "outro_vo": str,         // CTA
  "title_yt": str,         // <=70 chars, punchy
  "description": str, "hashtags": [str], "tags": [str],
  "self_score": { "accuracy": int, "logic": int, "hook": int, "total": int }
}
Values must be real. 'top' must be the true top-3 of 'data'."""


def _validate_mapped(d: dict) -> list[str]:
    errs = []
    data = d.get("data") or []
    if not (10 <= len(data) <= 40):
        errs.append("data cần 10–40 bang")
    for i, r in enumerate(data):
        if not str((r or {}).get("state", "")).strip():
            errs.append(f"data[{i}] thiếu state")
        if not isinstance((r or {}).get("value"), (int, float)):
            errs.append(f"data[{i}] value không phải số")
    top = d.get("top") or []
    if len(top) != 3:
        errs.append("top cần đúng 3")
    for k in ("title", "unit", "source", "intro_vo", "bloom_vo", "outro_vo", "title_yt"):
        if not str(d.get(k, "")).strip():
            errs.append(f"thiếu '{k}'")
    return errs


def generate_mapped(niche: str, api_key: str = None, model_name: str = None, avoid: list = None) -> dict:
    """Sinh 1 câu chuyện MAPPED (metric + số liệu bang THẬT + narration). Viết lại tới khi accuracy&total đạt."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    model = genai.GenerativeModel(mname, system_instruction=MAPPED_SYS)
    resolved = False
    avoid_txt = ("\nAvoid metrics already used: " + " | ".join(avoid[-60:])) if avoid else ""
    base = (f'Pick ONE surprising US metric in the niche "{niche}" and map it by state.\n{MAPPED_SCHEMA}{avoid_txt}')
    feedback = ""; last = None
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base + (f"\n\nPrevious rejected: {feedback}\nFix and raise the score." if feedback else "")
        try:
            resp = model.generate_content(prompt, generation_config={"temperature": 0.8, "response_mime_type": "application/json"})
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and not resolved:
                mn = _pick_model(genai, prefer, akey); resolved = True
                if mn and mn != mname:
                    mname = mn; model = genai.GenerativeModel(mn, system_instruction=MAPPED_SYS); continue
            if ("429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg or "ratelimit" in msg
                    or "denied" in msg or "permission" in msg or "forbidden" in msg or "403" in msg
                    or "suspended" in msg or "has not been used" in msg or "not enabled" in msg or "disabled" in msg):
                raise RateLimited(str(e))
            raise
        try:
            d = _extract_json(resp.text)
        except Exception as e:
            feedback = f"JSON lỗi ({e})."; continue
        errs = _validate_mapped(d)
        sc = d.get("self_score") or {}
        score = sc.get("total", 0); acc = int(sc.get("accuracy", 0))
        d["_attempt"] = attempt; last = d
        if errs:
            feedback = "Lỗi cấu trúc: " + "; ".join(errs[:6]); print(f"   ↻ mapped vòng {attempt}: {feedback}"); continue
        if acc < 95:
            feedback = f"accuracy={acc}<95. Chỉ dùng metric có số liệu THẬT chắc chắn (Census/BLS/CDC/FBI). Đổi metric nếu không chắc số."
            print(f"   ↻ mapped vòng {attempt}: {feedback}"); continue
        if score < MIN_SCORE:
            feedback = f"Điểm {score}<{MIN_SCORE}. Hook mạnh hơn, reveal sốc hơn."; print(f"   ↻ mapped vòng {attempt}: điểm {score}"); continue
        d["vtype"] = "mapped"
        print(f"   ✅ MAPPED đạt vòng {attempt}: total {score}, acc {acc} — {d.get('title')!r}")
        return d
    raise Exception(f"MAPPED sau {MAX_TRIES} vòng chưa đạt. Bỏ {niche!r}.")


# ─────────────────────────────────────────────────────────────────────────────
# KÊNH #3 RANKED — sinh tier list S/A/B/C/D (xếp hạng có tiêu chí + số liệu thật).
RANKED_SYS = (
 "You are the host of a #1 US 'tier list' viral channel. You rank things into S/A/B/C/D tiers by a CLEAR, "
 "stated criterion. Absolute rules:\n"
 "1) CRITERION FIRST: state one objective criterion (e.g. 'by 2023 US sales', 'by average rating', 'by speed'). "
 "Tier placement must be CONSISTENT with it — the best by that criterion are S, worst are D. No contradictions.\n"
 "2) FACTS: every stat must be TRUE and verifiable. Never invent numbers. If unsure, pick a topic you know.\n"
 "3) 7-10 items total, spread across tiers, with a clear S tier (1-2 items). Use well-known US-relevant items.\n"
 "4) NO politics/partisan, no tragedy, no NSFW, no ranking real private people.\n"
 "5) ORDER items for a DRAMATIC reveal that ENDS on the S tier (reveal low tiers first, S last = climax).\n"
 "6) NARRATION spoken aloud: punchy hook, one spicy line per item as it drops into its tier, big S-tier payoff, CTA. Short natural sentences."
)

RANKED_SCHEMA = """Return STRICT JSON with EXACTLY these keys:
{
  "title": str,            // on-screen, <=24 chars, e.g. "FAST FOOD, RANKED"
  "subtitle": str,         // basis shown small, e.g. "by US sales"
  "criterion": str,        // the objective measure used
  "items": [               // 7-10, ORDERED for reveal (low tiers first, S tier LAST)
    { "name": str, "tier": "S"|"A"|"B"|"C"|"D", "stat": str, "vo": str }   // stat <=12 chars; vo = one spoken line
  ],
  "intro_vo": str,
  "outro_vo": str,
  "title_yt": str, "description": str, "hashtags": [str], "tags": [str],
  "self_score": { "accuracy": int, "logic": int, "hook": int, "total": int }
}
Tiers must be consistent with the criterion. The LAST items must be the S tier."""


def _validate_ranked(d: dict) -> list[str]:
    errs = []
    its = d.get("items") or []
    if not (5 <= len(its) <= 12):
        errs.append("items cần 5–12")
    tiers_ok = {"S", "A", "B", "C", "D", "F"}
    for i, it in enumerate(its):
        if not str((it or {}).get("name", "")).strip():
            errs.append(f"item[{i}] thiếu name")
        if str((it or {}).get("tier", "")).upper() not in tiers_ok:
            errs.append(f"item[{i}] tier lạ")
        if not str((it or {}).get("vo", "")).strip():
            errs.append(f"item[{i}] thiếu vo")
    if not any(str((it or {}).get("tier", "")).upper() == "S" for it in its):
        errs.append("cần ít nhất 1 item tier S")
    for k in ("title", "subtitle", "criterion", "intro_vo", "outro_vo", "title_yt"):
        if not str(d.get(k, "")).strip():
            errs.append(f"thiếu '{k}'")
    return errs


def generate_ranked(niche: str, api_key: str = None, model_name: str = None, avoid: list = None) -> dict:
    """Sinh 1 tier list RANKED (xếp hạng có tiêu chí + số liệu thật + narration). Viết lại tới khi đạt."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    model = genai.GenerativeModel(mname, system_instruction=RANKED_SYS)
    resolved = False
    avoid_txt = ("\nAvoid topics already used: " + " | ".join(avoid[-60:])) if avoid else ""
    base = (f'Make a tier list in the niche "{niche}".\n{RANKED_SCHEMA}{avoid_txt}')
    feedback = ""; last = None
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base + (f"\n\nPrevious rejected: {feedback}\nFix and raise the score." if feedback else "")
        try:
            resp = model.generate_content(prompt, generation_config={"temperature": 0.85, "response_mime_type": "application/json"})
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and not resolved:
                mn = _pick_model(genai, prefer, akey); resolved = True
                if mn and mn != mname:
                    mname = mn; model = genai.GenerativeModel(mn, system_instruction=RANKED_SYS); continue
            if ("429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg or "ratelimit" in msg
                    or "denied" in msg or "permission" in msg or "forbidden" in msg or "403" in msg
                    or "suspended" in msg or "has not been used" in msg or "not enabled" in msg or "disabled" in msg):
                raise RateLimited(str(e))
            raise
        try:
            d = _extract_json(resp.text)
        except Exception as e:
            feedback = f"JSON lỗi ({e})."; continue
        errs = _validate_ranked(d)
        sc = d.get("self_score") or {}
        score = sc.get("total", 0); lo = min(int(sc.get("accuracy", 0)), int(sc.get("logic", 0)))
        d["_attempt"] = attempt; last = d
        if errs:
            feedback = "Lỗi cấu trúc: " + "; ".join(errs[:6]); print(f"   ↻ ranked vòng {attempt}: {feedback}"); continue
        if lo < 95:
            feedback = f"accuracy/logic={lo}<95. Tiêu chí phải rõ, tier khớp tiêu chí, stat THẬT. Sửa item mâu thuẫn."
            print(f"   ↻ ranked vòng {attempt}: {feedback}"); continue
        if score < MIN_SCORE:
            feedback = f"Điểm {score}<{MIN_SCORE}. Hook mạnh hơn, S-tier payoff sốc hơn."; print(f"   ↻ ranked vòng {attempt}: điểm {score}"); continue
        d["vtype"] = "ranked"
        print(f"   ✅ RANKED đạt vòng {attempt}: total {score}, acc/logic {lo} — {d.get('title')!r}")
        return d
    raise Exception(f"RANKED sau {MAX_TRIES} vòng chưa đạt. Bỏ {niche!r}.")


# ─────────────────────────────────────────────────────────────────────────────
# KÊNH #4 SCALED — sinh so sánh KÍCH THƯỚC vật lý thật (emoji đúng tỉ lệ).
SCALED_SYS = (
 "You are the creator of a #1 US 'size comparison' viral channel. You compare the REAL physical size of things "
 "drawn to scale. Absolute rules:\n"
 "1) REAL MEASUREMENTS: every value is a TRUE physical measurement of ONE dimension (length OR height OR "
 "diameter) in ONE consistent unit for all items. Never invent numbers. State the dimension in subtitle.\n"
 "2) Each item MUST have a single representative EMOJI that clearly depicts it (🐋 🚌 🗽 🏢 🦕 🌍 etc.).\n"
 "3) 4-6 items, ORDERED SMALLEST→LARGEST (largest last = climax). Keep the size ratio within ~200x so every "
 "item is still visible; include a familiar reference (human/bus) when helpful.\n"
 "4) NO politics, no tragedy, no NSFW. Broadly fascinating to US viewers.\n"
 "5) NARRATION spoken aloud: punchy hook, one vivid line per item as it appears, jaw-drop on the biggest, CTA. Short natural sentences."
)

SCALED_SCHEMA = """Return STRICT JSON with EXACTLY these keys:
{
  "title": str,            // <=26 chars, e.g. "HOW BIG IS A BLUE WHALE?"
  "subtitle": str,         // the dimension + unit, e.g. "length compared (meters)"
  "unit": str,             // e.g. "m"
  "items": [               // 4-6, ORDERED smallest -> largest
    { "name": str, "emoji": str, "value": number, "disp": str, "vo": str }   // value = real, same unit; disp e.g. "30 m"
  ],
  "intro_vo": str,
  "outro_vo": str,
  "title_yt": str, "description": str, "hashtags": [str], "tags": [str],
  "self_score": { "accuracy": int, "logic": int, "hook": int, "total": int }
}
Values must be real, same unit, ascending. Each item needs a fitting emoji."""


def _validate_scaled(d: dict) -> list[str]:
    errs = []
    its = d.get("items") or []
    if not (3 <= len(its) <= 7):
        errs.append("items cần 3–7")
    vals = []
    for i, it in enumerate(its):
        if not str((it or {}).get("name", "")).strip():
            errs.append(f"item[{i}] thiếu name")
        if not str((it or {}).get("emoji", "")).strip():
            errs.append(f"item[{i}] thiếu emoji")
        if not isinstance((it or {}).get("value"), (int, float)):
            errs.append(f"item[{i}] value không phải số")
        else:
            vals.append(it["value"])
        if not str((it or {}).get("vo", "")).strip():
            errs.append(f"item[{i}] thiếu vo")
    if vals and vals != sorted(vals):
        errs.append("items phải xếp NHỎ→LỚN")
    for k in ("title", "subtitle", "intro_vo", "outro_vo", "title_yt"):
        if not str(d.get(k, "")).strip():
            errs.append(f"thiếu '{k}'")
    return errs


def generate_scaled(niche: str, api_key: str = None, model_name: str = None, avoid: list = None) -> dict:
    """Sinh 1 so sánh kích thước SCALED (đo thật + emoji + narration). Viết lại tới khi đạt."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    model = genai.GenerativeModel(mname, system_instruction=SCALED_SYS)
    resolved = False
    avoid_txt = ("\nAvoid topics already used: " + " | ".join(avoid[-60:])) if avoid else ""
    base = (f'Make a size comparison in the niche "{niche}".\n{SCALED_SCHEMA}{avoid_txt}')
    feedback = ""; last = None
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base + (f"\n\nPrevious rejected: {feedback}\nFix and raise the score." if feedback else "")
        try:
            resp = model.generate_content(prompt, generation_config={"temperature": 0.85, "response_mime_type": "application/json"})
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and not resolved:
                mn = _pick_model(genai, prefer, akey); resolved = True
                if mn and mn != mname:
                    mname = mn; model = genai.GenerativeModel(mn, system_instruction=SCALED_SYS); continue
            if ("429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg or "ratelimit" in msg
                    or "denied" in msg or "permission" in msg or "forbidden" in msg or "403" in msg
                    or "suspended" in msg or "has not been used" in msg or "not enabled" in msg or "disabled" in msg):
                raise RateLimited(str(e))
            raise
        try:
            d = _extract_json(resp.text)
        except Exception as e:
            feedback = f"JSON lỗi ({e})."; continue
        errs = _validate_scaled(d)
        sc = d.get("self_score") or {}
        score = sc.get("total", 0); acc = int(sc.get("accuracy", 0))
        d["_attempt"] = attempt; last = d
        if errs:
            feedback = "Lỗi cấu trúc: " + "; ".join(errs[:6]); print(f"   ↻ scaled vòng {attempt}: {feedback}"); continue
        if acc < 95:
            feedback = f"accuracy={acc}<95. Chỉ dùng số đo THẬT (cùng đơn vị). Đổi item nếu không chắc số."
            print(f"   ↻ scaled vòng {attempt}: {feedback}"); continue
        if score < MIN_SCORE:
            feedback = f"Điểm {score}<{MIN_SCORE}. Hook mạnh hơn, cú chốt to nhất sốc hơn."; print(f"   ↻ scaled vòng {attempt}: điểm {score}"); continue
        d["vtype"] = "scaled"
        print(f"   ✅ SCALED đạt vòng {attempt}: total {score}, acc {acc} — {d.get('title')!r}")
        return d
    raise Exception(f"SCALED sau {MAX_TRIES} vòng chưa đạt. Bỏ {niche!r}.")


# ─────────────────────────────────────────────────────────────────────────────
# KÊNH #5 THEN×NOW — sinh so sánh XƯA/NAY (giá trị thật + mức biến đổi).
THENNOW_SYS = (
 "You are the creator of a #1 US 'then vs now' nostalgia channel. Each pair shows how ONE thing changed from a "
 "past year to now, with REAL numbers. Absolute rules:\n"
 "1) REAL VALUES: thenVal (past) and nowVal (present) are TRUE, verifiable figures for the SAME thing in the SAME "
 "unit. Never invent. The change (×N or +N%) must match the numbers.\n"
 "2) One clear THEME across all pairs (e.g. 'cost of living 1970 vs today', 'tech then vs now').\n"
 "3) 2-4 pairs. Use round, recognizable figures. thenYear/nowYear are real years.\n"
 "4) NO politics/partisan, no tragedy, no NSFW. Nostalgic + jaw-dropping for US viewers.\n"
 "5) NARRATION spoken aloud: hook, one punchy line per pair contrasting then vs now, CTA. Short natural sentences."
)

THENNOW_SCHEMA = """Return STRICT JSON with EXACTLY these keys:
{
  "title": str,            // <=28 chars, e.g. "COST OF LIVING: THEN vs NOW"
  "theme": str,            // the common thread
  "pairs": [               // 2-4
    { "label": str, "thenYear": str, "thenVal": str, "nowYear": str, "nowVal": str, "change": str, "vo": str }
    // change = "×10" or "+880%"; vo = one spoken line
  ],
  "intro_vo": str,
  "outro_vo": str,
  "title_yt": str, "description": str, "hashtags": [str], "tags": [str],
  "self_score": { "accuracy": int, "logic": int, "hook": int, "total": int }
}
Values must be real and the change must match them."""


def _validate_thennow(d: dict) -> list[str]:
    errs = []
    ps = d.get("pairs") or []
    if not (2 <= len(ps) <= 4):
        errs.append("pairs cần 2–4")
    for i, p in enumerate(ps):
        for k in ("label", "thenYear", "thenVal", "nowYear", "nowVal", "vo"):
            if not str((p or {}).get(k, "")).strip():
                errs.append(f"pair[{i}] thiếu '{k}'")
    for k in ("title", "theme", "intro_vo", "outro_vo", "title_yt"):
        if not str(d.get(k, "")).strip():
            errs.append(f"thiếu '{k}'")
    return errs


def generate_thennow(niche: str, api_key: str = None, model_name: str = None, avoid: list = None) -> dict:
    """Sinh 1 so sánh XƯA/NAY (giá trị thật + biến đổi + narration). Viết lại tới khi đạt."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    model = genai.GenerativeModel(mname, system_instruction=THENNOW_SYS)
    resolved = False
    avoid_txt = ("\nAvoid themes already used: " + " | ".join(avoid[-60:])) if avoid else ""
    base = (f'Make a then-vs-now comparison in the niche "{niche}".\n{THENNOW_SCHEMA}{avoid_txt}')
    feedback = ""; last = None
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base + (f"\n\nPrevious rejected: {feedback}\nFix and raise the score." if feedback else "")
        try:
            resp = model.generate_content(prompt, generation_config={"temperature": 0.85, "response_mime_type": "application/json"})
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and not resolved:
                mn = _pick_model(genai, prefer, akey); resolved = True
                if mn and mn != mname:
                    mname = mn; model = genai.GenerativeModel(mn, system_instruction=THENNOW_SYS); continue
            if ("429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg or "ratelimit" in msg
                    or "denied" in msg or "permission" in msg or "forbidden" in msg or "403" in msg
                    or "suspended" in msg or "has not been used" in msg or "not enabled" in msg or "disabled" in msg):
                raise RateLimited(str(e))
            raise
        try:
            d = _extract_json(resp.text)
        except Exception as e:
            feedback = f"JSON lỗi ({e})."; continue
        errs = _validate_thennow(d)
        sc = d.get("self_score") or {}
        score = sc.get("total", 0); acc = int(sc.get("accuracy", 0))
        d["_attempt"] = attempt; last = d
        if errs:
            feedback = "Lỗi cấu trúc: " + "; ".join(errs[:6]); print(f"   ↻ thennow vòng {attempt}: {feedback}"); continue
        if acc < 95:
            feedback = f"accuracy={acc}<95. thenVal/nowVal phải THẬT cùng đơn vị, change khớp số. Đổi cặp nếu không chắc."
            print(f"   ↻ thennow vòng {attempt}: {feedback}"); continue
        if score < MIN_SCORE:
            feedback = f"Điểm {score}<{MIN_SCORE}. Hook mạnh hơn, tương phản xưa/nay sốc hơn."; print(f"   ↻ thennow vòng {attempt}: điểm {score}"); continue
        d["vtype"] = "thennow"
        print(f"   ✅ THENNOW đạt vòng {attempt}: total {score}, acc {acc} — {d.get('title')!r}")
        return d
    raise Exception(f"THENNOW sau {MAX_TRIES} vòng chưa đạt. Bỏ {niche!r}.")


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
