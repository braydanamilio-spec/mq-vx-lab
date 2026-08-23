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
    if str(api_key).startswith("gsk_") or type(genai).__name__ == "_GroqShim":
        return GROQ_MODEL
    if str(api_key).startswith("cf:") or type(genai).__name__ == "_CfShim":
        return CF_TEXT_MODEL
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
# TIMEOUT cho MỌI lệnh gọi Gemini viết kịch bản. 20/8 — nguyên nhân gốc khiến 30 kênh mới CHƯA TỪNG
# có 1 video thành công nào: generate_content() KHÔNG timeout -> mạng/API chập chờn là TREO VĨNH VIỄN
# (không throw nên except/retry bên dưới vô dụng), job đứng ở "writing"/"qc" tới khi bị giết sau 6h.
# 45/72 job của kênh mới chết đúng kiểu này. Kênh cũ (data-race) đi đường khác nên thoát. 180s = dư cho
# bản nháp dài nhất, vẫn cắt sớm hơn nhiều so với timeout workflow (350').
GEN_OPTS = {"timeout": 180}
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


# 22/8: Groq ĐÃ GỠ llama-3.3-70b-versatile (test thật qua dashboard: HTTP 404 "does not exist").
# Mặc định mới = openai/gpt-oss-120b (test 200 OK, JSON chuẩn). Groq gỡ/thay model khá thường xuyên
# -> _GroqShim tự dò model SỐNG từ /models khi gặp 404 (danh sách ưu tiên bên dưới), khỏi chết lần nữa.
# UA tử tế cho mọi lệnh gọi REST qua urllib: api.groq.com/api.cloudflare.com đều nấp sau WAF
# Cloudflare — UA "Python-urllib" mặc định thi thoảng dính chặn chữ ký bot (403 error code 1010,
# EMPIREUSA 22/8). UA rõ danh tính + kiểu trình duyệt là hết bị soi.
UA = "Mozilla/5.0 (compatible; MM0-render/1.0; +https://mm0-auto-publisher.web.app)"

GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
_GROQ_PREF = [GROQ_MODEL, "openai/gpt-oss-120b", "qwen/qwen3.6-27b", "groq/compound-mini", "openai/gpt-oss-20b"]

# Cloudflare Workers AI (22/8): key dạng "cf:<account_id>:<api_token>" — 10K neuron free/ngày/tài
# khoản (reset 00:00Z). SỐ THẬT tự tính từ giá niêm yết (22/8 — số "2K ảnh" của trang thứ 3 SAI ~12 lần):
# ≈ ~174 ảnh FLUX 1024²/4 bước (58n/ảnh) HOẶC ~60 bài viết ngắn gpt-oss-120b (~166n/bài). Vai trò: VẼ ẢNH
# (FLUX schnell, ưu tiên TRƯỚC Gemini) + VISION fallback (sau Gemini) + viết chữ CHÓT BẢNG
# (sau Groq và Gemini — để dành neuron cho ảnh, thứ chỉ CF và Gemini làm được).
CF_TEXT_MODEL = os.environ.get("CF_TEXT_MODEL", "@cf/openai/gpt-oss-120b")
CF_VISION_MODEL = os.environ.get("CF_VISION_MODEL", "@cf/meta/llama-3.2-11b-vision-instruct")
# CF cũng gỡ/đổi model như Groq -> danh sách ưu tiên cho tự-dò khi 404/400 model-không-tồn-tại
_CF_PREF = [CF_TEXT_MODEL, "@cf/openai/gpt-oss-120b", "@cf/openai/gpt-oss-20b",
            "@cf/meta/llama-3.3-70b-instruct-fp8-fast", "@cf/qwen/qwen2.5-coder-32b-instruct"]


def _cf_parse(key):
    p = str(key).split(":", 2)
    return (p[1], p[2]) if len(p) == 3 and p[1] and p[2] else ("", "")


class _GroqShim:
    """Groq (OpenAI-compatible) đội lốt giao diện google.generativeai — nhờ vậy TOÀN BỘ luồng viết
    (generate_doc/plan_pillar/audit + vòng chấm điểm + validator) chạy Groq mà KHÔNG sửa dòng nào.

    Nhận diện tự động: key Groq bắt đầu bằng 'gsk_' (Gemini là 'AIza'). Cùng nằm chung collection
    gemini_keys -> đồng bộ A→B, xoay vòng, cooldown, đếm request... thừa hưởng nguyên xi.
    Lỗi 429 của Groq được ném lại thành chuỗi chứa '429'/'rate limit' -> các tầng trên (RateLimited,
    cool_key, key_order) xử lý y như key Gemini bị giới hạn. Groq KHÔNG có vision/vẽ ảnh — các pool
    ảnh/Vision đã lọc bỏ gsk_ ở datastory_ci."""

    _limits_printed = set()   # in hạn mức THẬT (Groq tự khai trong header) 1 lần/key/tiến trình

    def __init__(self, key):
        self._key = key

    def _print_limits(self, headers):
        tag = self._key[-4:]
        if tag in _GroqShim._limits_printed:
            return
        rpd = headers.get("x-ratelimit-limit-requests")
        left = headers.get("x-ratelimit-remaining-requests")
        tpm = headers.get("x-ratelimit-limit-tokens")
        if rpd:
            _GroqShim._limits_printed.add(tag)
            print(f"   ⚡ Groq •••{tag} — hạn mức CHÍNH THỨC (tự khai trong header): "
                  f"{rpd} req/ngày · còn {left} · {tpm or '?'} token/phút")

    _live_model = None        # model Groq đã xác nhận SỐNG (chia sẻ toàn tiến trình)

    def GenerativeModel(self, model_name, system_instruction=None, **kw):
        # 22/8: PHẢI nhận system_instruction — plan_pillar/generate_doc đều truyền; thiếu là
        # TypeError giết cả 18 luồng ngay phiên ĐẦU TIÊN Groq vào trận (07:07Z, sau khi key
        # Groq được hợp nhất vào pool). Map thành message role=system chuẩn OpenAI.
        self._model = _GroqShim._live_model or GROQ_MODEL   # tên gemini-* được map sang model Groq
        self._sys = system_instruction
        return self

    def _resolve_live_model(self) -> str:
        """Gặp 404 model-đã-gỡ -> hỏi /models rồi chọn model SỐNG theo danh sách ưu tiên."""
        import urllib.request
        req = urllib.request.Request("https://api.groq.com/openai/v1/models",
                                     headers={"Authorization": f"Bearer {self._key}", "User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            ids = {m.get("id") for m in (json.load(r).get("data") or [])}
        for want in _GROQ_PREF:
            if want in ids:
                _GroqShim._live_model = want
                print(f"   ⚡ Groq: model '{self._model}' đã bị gỡ -> tự chuyển sang '{want}' (còn sống).")
                return want
        raise RuntimeError(f"groq: không còn model nào trong danh sách ưu tiên ({sorted(ids)[:6]}...)")

    def configure(self, **kw):
        pass

    def list_models(self):
        # PING THẬT endpoint models — health-check (test_key) đi qua đây; trả tĩnh thì key Groq bị
        # thu hồi vẫn "sống ảo". Lỗi 401/403 nổi lên -> test_key map DEAD; 429 -> map SỐNG-tạm y Gemini.
        import urllib.request, urllib.error
        req = urllib.request.Request("https://api.groq.com/openai/v1/models",
                                     headers={"Authorization": f"Bearer {self._key}", "User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                self._print_limits(r.headers)
                json.load(r)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"groq HTTP {e.code}: {'invalid api key' if e.code in (401, 403) else 'rate limit' if e.code == 429 else ''}")
        return [type("M", (), {"name": "models/" + GROQ_MODEL, "supported_generation_methods": ["generateContent"]})()]

    def generate_content(self, prompt, generation_config=None, request_options=None):
        import urllib.request, urllib.error
        gc = generation_config or {}
        msgs = ([{"role": "system", "content": self._sys}] if getattr(self, "_sys", None) else [])
        msgs.append({"role": "user", "content": prompt if isinstance(prompt, str) else str(prompt)})
        # max_tokens 3600 chứ KHÔNG 8192 (GỐC RỄ 413 — đo 14:0xZ 22/8): Groq cộng max_tokens vào
        # "Requested" khi so trần TPM 8000/request -> khai 8192 là MỌI lệnh đều 413 bất kể prompt
        # ngắn hay dài. 3600 đủ rộng cho JSON dài nhất của mình (~2.5K token) mà input+max luôn <8K.
        body = {"model": self._model,
                "messages": msgs,
                "temperature": gc.get("temperature", 0.9),
                "max_tokens": 3600}
        if gc.get("response_mime_type") == "application/json":
            body["response_format"] = {"type": "json_object"}
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self._key}", "Content-Type": "application/json", "User-Agent": UA})
        timeout = (request_options or {}).get("timeout", 120)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                self._print_limits(r.headers)
                out = json.load(r)
        except urllib.error.HTTPError as e:
            detail = ""
            try: detail = e.read().decode()[:200]
            except Exception: pass
            if e.code == 404 and "not exist" in detail.lower():
                # model bị Groq gỡ (đã xảy ra thật với llama-3.3 ngày 22/8) -> dò model sống, thử lại 1 lần
                self._model = self._resolve_live_model()
                body["model"] = self._model
                req2 = urllib.request.Request(
                    "https://api.groq.com/openai/v1/chat/completions",
                    data=json.dumps(body).encode(),
                    headers={"Authorization": f"Bearer {self._key}", "Content-Type": "application/json", "User-Agent": UA})
                with urllib.request.urlopen(req2, timeout=timeout) as r:
                    self._print_limits(r.headers)
                    out = json.load(r)
                txt = ((out.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
                return type("R", (), {"text": txt})()
            if e.code == 403 and "1010" in detail:
                # WAF Cloudflare của Groq chặn chữ ký bot (lẻ tẻ theo IP runner) -> lỗi TẠM per-minute:
                # key nghỉ 1.1' + thử key kế, KHÔNG đánh trượt video, KHÔNG giết key.
                raise RuntimeError(f"429 rate limit per minute (groq WAF 1010): {detail[:80]}")
            if e.code == 429:
                # PHÂN LOẠI bằng chính header Groq: còn request trong ngày -> đây là nghẽn THEO PHÚT
                # (RPM/TPM) -> gắn chữ 'per minute' để _cool cho nghỉ 1.1' thay vì phạt oan 20'.
                try:
                    left = int(e.headers.get("x-ratelimit-remaining-requests") or 0)
                except Exception:
                    left = 0
                kind = "per minute" if left > 0 else "daily"
                raise RuntimeError(f"429 rate limit {kind} (groq): {detail}")
            raise RuntimeError(f"groq HTTP {e.code}: {detail}")
        txt = ((out.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        return type("R", (), {"text": txt})()


class _CfShim:
    """Cloudflare Workers AI đội lốt google.generativeai (cùng chiêu _GroqShim). Key 'cf:acc:token'.
    KHÁC Groq: nhận CẢ ẢNH trong generate_content ([text, {"mime_type","data"}]) -> toàn bộ
    qc_vision (verify_image/verify_grid/check_visual) dùng key CF mà không sửa dòng nào; ô mồi
    (decoy) sẵn có tự loại giám khảo CF nếu nó chấm ẩu."""

    _limits_printed = set()

    def __init__(self, key):
        self._key = key
        self._acc, self._tok = _cf_parse(key)

    _live_model = None    # model CF text đã xác nhận SỐNG (chia sẻ toàn tiến trình, như _GroqShim)

    def GenerativeModel(self, model_name, system_instruction=None, **kw):
        self._model = _CfShim._live_model or CF_TEXT_MODEL
        self._sys = system_instruction     # cùng lớp lỗi TypeError như _GroqShim (xem trên)
        return self

    def _resolve_live_model(self) -> str:
        """CF gỡ model text -> hỏi /ai/models/search rồi chọn theo _CF_PREF (bài học llama-3.3 Groq)."""
        import urllib.request
        req = urllib.request.Request(
            f"https://api.cloudflare.com/client/v4/accounts/{self._acc}/ai/models/search?per_page=100",
            headers=self._hdr())
        with urllib.request.urlopen(req, timeout=20) as r:
            ids = {m.get("name") for m in ((json.load(r).get("result")) or [])}
        for want in _CF_PREF:
            if want in ids:
                _CfShim._live_model = want
                print(f"   ⛅ CF: model '{self._model}' đã bị gỡ -> tự chuyển sang '{want}' (còn sống).")
                return want
        raise RuntimeError("cloudflare: không còn model text nào trong danh sách ưu tiên")

    def configure(self, **kw):
        pass

    def _hdr(self):
        return {"Authorization": f"Bearer {self._tok}", "Content-Type": "application/json", "User-Agent": UA}

    def list_models(self):
        # PING THẬT (health-check): token/account sai -> 401/403 nổi lên -> map DEAD y như Groq.
        import urllib.request, urllib.error
        req = urllib.request.Request(
            f"https://api.cloudflare.com/client/v4/accounts/{self._acc}/ai/models/search?per_page=1",
            headers=self._hdr())
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                json.load(r)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"cloudflare HTTP {e.code}: {'invalid api key' if e.code in (400, 401, 403) else 'rate limit' if e.code == 429 else ''}")
        return [type("M", (), {"name": "models/" + CF_TEXT_MODEL, "supported_generation_methods": ["generateContent"]})()]

    def generate_content(self, prompt, generation_config=None, request_options=None):
        import urllib.request, urllib.error, base64
        gc = generation_config or {}
        timeout = (request_options or {}).get("timeout", 120)
        text = prompt if isinstance(prompt, str) else ""
        img = None
        if isinstance(prompt, (list, tuple)):               # dạng qc_vision: [prompt, {"mime_type","data"}]
            for p in prompt:
                if isinstance(p, str):
                    text += p
                elif isinstance(p, dict) and p.get("data"):
                    img = p
        if img is not None:
            content = [{"type": "text", "text": text},
                       {"type": "image_url", "image_url": {"url": "data:" + img.get("mime_type", "image/jpeg")
                        + ";base64," + base64.b64encode(img["data"]).decode()}}]
            body = {"model": CF_VISION_MODEL, "messages": [{"role": "user", "content": content}],
                    "temperature": 0.0, "max_tokens": 1024}   # vision KHÔNG gửi response_format (model vision hay từ chối) — _extract_json tự bóc
        else:
            msgs = ([{"role": "system", "content": self._sys}] if getattr(self, "_sys", None) else [])
            msgs.append({"role": "user", "content": text or str(prompt)})
            body = {"model": getattr(self, "_model", CF_TEXT_MODEL),
                    "messages": msgs,
                    "temperature": gc.get("temperature", 0.9), "max_tokens": 8192}
            if gc.get("response_mime_type") == "application/json":
                body["response_format"] = {"type": "json_object"}
        req = urllib.request.Request(
            f"https://api.cloudflare.com/client/v4/accounts/{self._acc}/ai/v1/chat/completions",
            data=json.dumps(body).encode(), headers=self._hdr())
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.load(r)
        except urllib.error.HTTPError as e:
            detail = ""
            try: detail = e.read().decode()[:200]
            except Exception: pass
            low = detail.lower()
            if e.code in (400, 404) and ("no such model" in low or "does not exist" in low or "invalid model" in low or "not found" in low):
                # CF gỡ model (bài học llama-3.3 bên Groq) -> dò model sống rồi thử lại 1 lần
                self._model = self._resolve_live_model()
                body["model"] = self._model
                req2 = urllib.request.Request(
                    f"https://api.cloudflare.com/client/v4/accounts/{self._acc}/ai/v1/chat/completions",
                    data=json.dumps(body).encode(), headers=self._hdr())
                with urllib.request.urlopen(req2, timeout=timeout) as r:
                    out = json.load(r)
                txt2 = ((out.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
                return type("R", (), {"text": txt2})()
            if e.code == 429 or "4006" in detail or "neuron" in low:
                # 4006 = hết 10K neuron free trong ngày -> để chuỗi chứa '429' cho cool_key/key_order xử như Gemini/Groq
                raise RuntimeError(f"429 rate limit daily (cloudflare): {detail}")
            raise RuntimeError(f"cloudflare HTTP {e.code}: {detail}")
        txt = ((out.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        if not _CfShim._limits_printed and self._tok:
            _CfShim._limits_printed.add(self._tok[-4:])
            print(f"   ⛅ CF •••{self._tok[-4:]} hoạt động (free 10K neuron/ngày ≈ ~174 ảnh FLUX hoặc ~60 bài viết).")
        return type("R", (), {"text": txt})()


def _genai(api_key=None):
    key0 = api_key or os.environ.get("GEMINI_API_KEY", "")
    if str(key0).startswith("cf:"):
        return _CfShim(key0)
    if str(key0).startswith("gsk_"):
        return _GroqShim(key0)
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
                request_options=GEN_OPTS,
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
    if str(akey).startswith(("gsk_", "cf:")) and avoid:
        avoid = avoid[-35:]   # nhà 8K-token/request (Groq TPM 8000, đo thật 22/8: request 9069 bị 413) -> cắt danh sách tránh-trùng cho vừa
    avoid_txt = ""
    if avoid:
        avoid_txt = ("\nDO NOT repeat or closely resemble ANY of these already-used topics "
                     "(pick completely fresh angles): " + " | ".join(avoid[-60:]))
    # ĐẤU LOẠI CHỦ ĐỀ (22/8, nâng chất lượng theo user): key Groq/CF dư lượt -> sinh 3 phương án
    # pillar trong 1 lệnh + 1 lệnh giám khảo chấm chọn (curiosity gap / stakes / độ mới) thay vì
    # lấy ý tưởng đầu tiên. Key Gemini (đạn hiếm) giữ 1 lệnh như cũ. Giám khảo lỗi -> phương án 1.
    multi = str(akey).startswith(("gsk_", "cf:"))
    if multi:
        prompt = (f'Niche: "{niche}". Propose 3 ALTERNATIVE pillar plans for a US compilation video, each with a '
                  f'DIFFERENT angle (e.g. money-shock vs hidden-history vs everyday-mystery). Return STRICT JSON: '
                  f'{{"plans": [{{"pillar_title": str (<=40 chars, punchy), "hook": str (one shock line), '
                  f'"subtopics": [str x {n}]}} x 3]}}. Each subtopic = short search-friendly phrase, real US data, '
                  'different angle within its plan.' + avoid_txt)
    else:
        prompt = (f'Niche: "{niche}". Propose {n} DISTINCT sub-topics for a US bar-chart-race compilation. '
                  f'Return STRICT JSON: {{"pillar_title": str (<=40 chars, punchy), "hook": str (one shock line), '
                  f'"subtopics": [str x {n}]}}. Each subtopic = short search-friendly phrase, real US data, different angle.'
                  + avoid_txt)
    for _try in range(2):
        try:
            model = genai.GenerativeModel(mname, system_instruction=PILLAR_SYS)
            resp = model.generate_content(prompt, generation_config={"temperature": 0.95, "response_mime_type": "application/json"}, request_options=GEN_OPTS)
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
    if multi:
        plans = [p for p in (d.get("plans") or []) if p.get("subtopics")][:3]
        if len(plans) >= 2:
            try:
                jm = genai.GenerativeModel(mname, system_instruction=PILLAR_SYS)
                jp = ("You are a ruthless YouTube strategist. Pick the ONE plan a US audience is MOST likely "
                      "to click AND finish. Judge: curiosity gap, emotional stakes, freshness (generic = lose). "
                      'Return STRICT JSON: {"winner": 0|1|2, "why": "<=12 words"}.\nPlans:\n'
                      + json.dumps(plans, ensure_ascii=False))
                jr = jm.generate_content(jp, generation_config={"temperature": 0.0, "response_mime_type": "application/json"},
                                         request_options=GEN_OPTS)
                w = _extract_json(jr.text) or {}
                wi = int(w.get("winner", 0)) % len(plans)
                d = plans[wi]
                print(f"   🏆 Đấu loại chủ đề: chọn phương án {wi + 1}/3 — {str(w.get('why', ''))[:60]}")
            except Exception:
                d = plans[0]           # giám khảo lỗi/hết lượt -> phương án 1, không chặn sản xuất
        elif plans:
            d = plans[0]
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
  // MỖI mục chấm ĐỘC LẬP thang 0-100 (KHÔNG phải điểm thành phần cộng vào total).
  //   accuracy = % câu/số liệu KIỂM CHỨNG ĐƯỢC; toàn bộ đều thật -> 100.
  "self_score": { "logic":0-100, "uniqueness":0-100, "image_match":0-100, "hook":0-100, "total":0-100 }
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
            resp = model.generate_content(prompt, generation_config={"temperature": 0.85, "response_mime_type": "application/json"}, request_options=GEN_OPTS)
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
  // MỖI mục chấm ĐỘC LẬP thang 0-100 (KHÔNG phải điểm thành phần cộng vào total).
  //   accuracy = % câu/số liệu KIỂM CHỨNG ĐƯỢC; toàn bộ đều thật -> 100.
  "self_score": { "accuracy":0-100, "logic":0-100, "hook":0-100, "total":0-100 }
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
            resp = model.generate_content(prompt, generation_config={"temperature": 0.8, "response_mime_type": "application/json"}, request_options=GEN_OPTS)
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
  // MỖI mục chấm ĐỘC LẬP thang 0-100 (KHÔNG phải điểm thành phần cộng vào total).
  //   accuracy = % câu/số liệu KIỂM CHỨNG ĐƯỢC; toàn bộ đều thật -> 100.
  "self_score": { "accuracy":0-100, "logic":0-100, "hook":0-100, "total":0-100 }
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
            resp = model.generate_content(prompt, generation_config={"temperature": 0.85, "response_mime_type": "application/json"}, request_options=GEN_OPTS)
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
  // MỖI mục chấm ĐỘC LẬP thang 0-100 (KHÔNG phải điểm thành phần cộng vào total).
  //   accuracy = % câu/số liệu KIỂM CHỨNG ĐƯỢC; toàn bộ đều thật -> 100.
  "self_score": { "accuracy":0-100, "logic":0-100, "hook":0-100, "total":0-100 }
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
            resp = model.generate_content(prompt, generation_config={"temperature": 0.85, "response_mime_type": "application/json"}, request_options=GEN_OPTS)
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
  // MỖI mục chấm ĐỘC LẬP thang 0-100 (KHÔNG phải điểm thành phần cộng vào total).
  //   accuracy = % câu/số liệu KIỂM CHỨNG ĐƯỢC; toàn bộ đều thật -> 100.
  "self_score": { "accuracy":0-100, "logic":0-100, "hook":0-100, "total":0-100 }
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
            resp = model.generate_content(prompt, generation_config={"temperature": 0.85, "response_mime_type": "application/json"}, request_options=GEN_OPTS)
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


# ─────────────────────────────────────────────────────────────────────────────
# WAVE 2 — kênh KỂ CHUYỆN/TÀI LIỆU (Cosmos/Deep/Why/Empire/Unsolved). Dùng chung engine Cinematic.
DOC_SYS = (
 "You are the head writer of a #1 US cinematic documentary shorts channel. You write tight, factual, "
 "awe-inducing narration that hooks in 2 seconds and never lets go. Absolute rules:\n"
 "1) FACTS ONLY: everything stated must be TRUE and publicly verifiable. Never invent. If unsure, pick a safer true fact.\n"
 "2) HOOK hard: first line is a jaw-dropping question or shocking fact — no throat-clearing, no setup. Build tension "
 "scene to scene by withholding the full picture, then END ON A TWIST: a final fact/reveal that RECONTEXTUALIZES "
 "everything before it (not just 'more info' — a genuine turn). Make the viewer feel they HAVE to rewatch scene 1.\n"
 "3) Each scene has ONE spoken sentence (natural spoken English, vivid, concise) + an img_query describing a "
 "REAL visual that a CC0/public-domain stock/Wikimedia/NASA search will return (matches the sentence).\n"
 "4) COPYRIGHT SAFE: img_query must be describable by public-domain imagery (space=NASA, ocean=NOAA, nature/CC0). "
 "For a person, the visual is their CONTEXT (place/work), never a copyrighted portrait unless long-dead (public domain).\n"
 "5) NO politics/partisan, NO real tragedy/victims, no NSFW, no medical/financial advice.\n"
 "6) Tone = the given style. 6-9 scenes total for a ~45-70s short."
)

# SPECULATIVE (Wave 5 — FUTUREUSA/UNSEENUSA): KHÁC DOC_SYS ở đúng 1 chỗ quan trọng — rule #4 ở trên bắt img_query
# phải tìm được ảnh CC0 THẬT, mâu thuẫn trực tiếp với kênh speculative (ảnh do AI vẽ 100%, ai_only=True bên
# fetch_image() -> không bao giờ tìm Openverse). Không dùng chung DOC_SYS cho 2 kênh này -> Gemini sẽ tự bó hẹp
# img_query về cảnh "tìm được ảnh thật", làm content mất chất tưởng tượng/lý thuyết. Rule accuracy vẫn giữ NGHIÊM
# (niche riêng của từng kênh tự quy định rõ cái gì phải bám khoa học thật, cái gì được suy đoán).
DOC_SYS_SPECULATIVE = (
 "You are the head writer of a #1 US visionary/speculative documentary shorts channel. You write tight, "
 "awe-inducing narration that hooks in 2 seconds and never lets go. Absolute rules:\n"
 "1) Follow the niche's own STRICT grounding rules exactly — some speculative content must stay grounded in "
 "real science/trends even though the IMAGERY is imagined; others are pure creative speculation. Obey whatever "
 "the niche text specifies.\n"
 "2) HOOK hard: first line is a jaw-dropping question or vivid imagined scene — no throat-clearing, no setup. Build "
 "tension scene to scene, then END ON A TWIST: a final fact/reveal that RECONTEXTUALIZES everything before it. Make "
 "the abstract/invisible feel concrete and awe-inspiring, the way the best science-visualization channels do.\n"
 "3) Each scene has ONE spoken sentence (natural spoken English, vivid, concise) + an img_query describing the "
 "IMAGINED/THEORETICAL visual for an AI artist to paint — it does NOT need to be a real photographable scene, "
 "describe it vividly and specifically like a concept-art brief (no need for CC0/stock-photo-findable imagery).\n"
 "4) Use clearly speculative framing language wherever the niche requires it ('could', 'might', 'imagine', "
 "'scientists believe', 'one vision of') — never state speculation as settled fact.\n"
 "5) NO politics/partisan, NO real tragedy/victims, no NSFW, no medical/financial advice.\n"
 "6) Tone = the given style. 6-9 scenes total for a ~45-70s short."
)

DOC_SCHEMA = """Return STRICT JSON with EXACTLY these keys:
{
  "title": str,            // punchy on-screen title, <=32 chars
  "hook": str,             // spoken opening line (the shock)
  "scenes": [              // 6-9 scenes, in order
    { "nar": str,          // ONE spoken sentence
      "img_query": str,    // real visual, CC0/PD-friendly, matches the sentence
      "title": str }       // OPTIONAL chapter word shown big ("" if none)
  ],
  "outro": str,            // spoken closing + soft CTA (follow for more)
  "title_yt": str, "description": str, "hashtags": [str], "tags": [str],
  // ── THUMBNAIL (điểm nhấn của video, để vẽ ảnh bìa gây tò mò) ──
  "thumb_stat": str,       // THE single most shocking REAL number in this video, formatted SHORT for a
                           // thumbnail: "$4.7B", "92%", "1 IN 6", "40,000x". <=8 chars. Must be a number
                           // that actually appears in the narration above. "" if the video has no number.
  "thumb_label": str,      // <=20 chars, what that number IS: "OF US TAP WATER", "PER SECOND"
  "thumb_hook": str,       // <=22 chars, an OPEN QUESTION or doubt that creates curiosity — do NOT answer
                           // it in the thumbnail: "IS YOURS ON THE LIST?", "WHY?", "NOBODY NOTICED"
  "sources": [str],        // 2-4 REAL public sources backing the specific numbers/claims used above,
                           // e.g. "FBI Uniform Crime Report 2023", "NOAA NCEI Billion-Dollar Disasters",
                           // "US Census Bureau ACS 2022". Name the ORGANISATION + dataset/report + year.
                           // NEVER invent a source. If a claim has no real source you can name, REPLACE
                           // that claim with one you can source.
  // MỖI mục chấm ĐỘC LẬP thang 0-100 (KHÔNG phải điểm thành phần cộng vào total).
  //   accuracy = % câu/số liệu KIỂM CHỨNG ĐƯỢC; toàn bộ đều thật -> 100.
  "self_score": { "accuracy":0-100, "hook":0-100, "flow":0-100, "total":0-100 }
}
Every fact must be true. img_query must be findable in public-domain/CC0 imagery."""


def _validate_doc(d: dict) -> list[str]:
    errs = []
    sc = d.get("scenes") or []
    if not (5 <= len(sc) <= 12):
        errs.append("scenes cần 5–12")
    for i, s in enumerate(sc):
        if not str((s or {}).get("nar", "")).strip():
            errs.append(f"scene[{i}] thiếu nar")
        if not str((s or {}).get("img_query", "")).strip():
            errs.append(f"scene[{i}] thiếu img_query")
    for k in ("title", "hook", "title_yt"):
        if not str(d.get(k, "")).strip():
            errs.append(f"thiếu '{k}'")
    return errs


AUDIT_SYS = (
 "You are an independent fact-checker and YouTube monetization-policy reviewer. You did NOT write this script "
 "and you have NO stake in it passing. Be skeptical and strict — your job is to CATCH problems, not to be nice.\n"
 "Check EVERY spoken line for:\n"
 "(a) FALSE or unverifiable factual claims — a specific number, date, ranking, record, or named case that is wrong, "
 "made up, or that you cannot confirm from well-known public knowledge. Confidently-worded invented stats are the "
 "single most common failure — flag them.\n"
 "(b) YouTube advertiser-friendly risk: real tragedy/victims described in detail, graphic violence/crime detail, "
 "partisan politics, medical/financial advice, adult themes, hateful or demeaning framing about any group.\n"
 "(c) Claims stated as settled fact that are actually contested/speculative without hedging language.\n"
 "Judge the SCRIPT AS WRITTEN. Ignore how cinematic or engaging it is — that is not your job."
)
AUDIT_SCHEMA = """Return STRICT JSON only:
{
  "verdict": "pass" | "fix",
  "risk": "none" | "low" | "high",          // advertiser-friendliness risk
  "problems": [str]                          // each: quote the exact problem line + say WHY (<=25 words). [] if none.
}"""


def audit_doc(d: dict, api_key: str = None, model_name: str = None) -> tuple[bool, list]:
    """LỚP KIỂM CHỨNG ĐỘC LẬP (khác self_score): self_score do CHÍNH model vừa viết tự chấm -> một fact bịa
    nhưng viết tự tin vẫn tự cho 92+ điểm (điểm yếu cố hữu, không thể tự sửa bằng prompt chặt hơn). Ở đây gọi
    1 lệnh Gemini RIÊNG, system prompt của người soi (không biết/không dính dáng gì tới bản nháp) -> bắt được
    fact sai + rủi ro chính sách kiếm tiền YouTube mà tự-chấm bỏ lọt.
    CHỈ chạy 1 lần cho bản ĐÃ QUA self_score (không phải mỗi vòng viết lại) -> tốn tối đa 1 call/video.
    FAIL-OPEN: lỗi/hết quota/timeout -> trả (True, []) cho qua, KHÔNG chặn pipeline (giống qc_vision)."""
    lines = [d.get("hook") or ""] + [s.get("nar") or "" for s in (d.get("scenes") or [])] + [d.get("outro") or ""]
    body = "\n".join(f"- {ln}" for ln in lines if ln)
    if not body:
        return True, []
    try:
        genai = _genai(api_key)
        mn = model_name or MODEL
        model = genai.GenerativeModel(mn, system_instruction=AUDIT_SYS)
        resp = model.generate_content(
            f"Script lines:\n{body}\n\n{AUDIT_SCHEMA}",
            generation_config={"temperature": 0.0, "response_mime_type": "application/json"},
            request_options={"timeout": 45})   # LUÔN đặt timeout — xem bài học treo Gemini Vision 20/8 ở qc_vision.py
        r = _extract_json(resp.text) or {}
    except Exception as e:
        print(f"   ⚠️ audit bỏ qua (fail-open): {str(e)[:70]}")
        return True, []
    probs = [p for p in (r.get("problems") or []) if isinstance(p, str)][:6]
    ok = (r.get("verdict") != "fix") and (r.get("risk") != "high")
    return ok, probs


def generate_doc(niche: str, style: str = "awe, cinematic", api_key: str = None,
                 model_name: str = None, avoid: list = None, speculative: bool = False,
                 audit: bool = True) -> dict:
    """Sinh 1 kịch bản TÀI LIỆU (narration + img_query mỗi cảnh) cho engine Cinematic. Viết lại tới khi đạt.
    speculative=True (Wave 5): img_query mô tả cảnh TƯỞNG TƯỢNG cho AI vẽ — KHÔNG bó buộc phải tìm được ảnh
    CC0 thật (khác DOC_SYS mặc định)."""
    sysp = DOC_SYS_SPECULATIVE if speculative else DOC_SYS
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    model = genai.GenerativeModel(mname, system_instruction=sysp)
    resolved = False
    avoid_txt = ("\nAvoid topics already used: " + " | ".join(avoid[-60:])) if avoid else ""
    base = (f'Niche: "{niche}". Tone/style: {style}. Write ONE cinematic documentary short.\n{DOC_SCHEMA}{avoid_txt}')
    feedback = ""; last = None; audits = 0
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base + (f"\n\nPrevious rejected: {feedback}\nFix and raise the score." if feedback else "")
        try:
            resp = model.generate_content(prompt, generation_config={"temperature": 0.9, "response_mime_type": "application/json"}, request_options=GEN_OPTS)
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and not resolved:
                mn = _pick_model(genai, prefer, akey); resolved = True
                if mn and mn != mname:
                    mname = mn; model = genai.GenerativeModel(mn, system_instruction=sysp); continue
            if ("429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg or "ratelimit" in msg
                    or "denied" in msg or "permission" in msg or "forbidden" in msg or "403" in msg
                    or "suspended" in msg or "has not been used" in msg or "not enabled" in msg or "disabled" in msg):
                raise RateLimited(str(e))
            raise
        try:
            d = _extract_json(resp.text)
        except Exception as e:
            feedback = f"JSON lỗi ({e})."; continue
        errs = _validate_doc(d)
        sc = d.get("self_score") or {}
        score = sc.get("total", 0); acc = int(sc.get("accuracy", 0))
        d["_attempt"] = attempt; last = d
        if errs:
            feedback = "Lỗi cấu trúc: " + "; ".join(errs[:6]); print(f"   ↻ doc vòng {attempt}: {feedback}"); continue
        if acc < 92:
            feedback = f"accuracy={acc}<92. Chỉ nêu SỰ THẬT kiểm chứng được. Sửa câu sai/bịa."
            print(f"   ↻ doc vòng {attempt}: {feedback}"); continue
        if score < MIN_SCORE:
            feedback = f"Điểm {score}<{MIN_SCORE}. Hook mạnh hơn, mạch cuốn hơn."; print(f"   ↻ doc vòng {attempt}: điểm {score}"); continue
        # ĐÃ QUA TỰ-CHẤM -> soi lại bằng LỚP ĐỘC LẬP (bắt fact bịa tự tin + rủi ro chính sách kiếm tiền).
        # Tối đa 2 lượt soi/video: soi mãi mà vẫn vướng thì nhận bản cuối (fail-open) — tránh đốt quota vô hạn.
        # audit=False (phần 2-3 của pillar): 3 phần cùng người viết + cùng luật + cùng gia đình chủ
        # đề — soi ĐỘC LẬP phần 1 là đủ đại diện; tiết kiệm 2 gọi Gemini/cụm (20 gọi/key/ngày rất đắt).
        if audit and audits < 2:
            audits += 1
            a_ok, a_probs = audit_doc(d, api_key=api_key, model_name=model_name)
            if not a_ok and a_probs:
                feedback = ("Người kiểm chứng ĐỘC LẬP bác bỏ (SỬA ĐÚNG các câu này, thay bằng sự thật kiểm chứng "
                            "được / bỏ hẳn nếu vướng chính sách quảng cáo): " + " | ".join(a_probs))
                print(f"   ↻ doc vòng {attempt}: audit bác — {a_probs[0][:90]}"); continue
            if a_probs:
                print(f"   ⚠️ audit ghi chú (vẫn cho qua): {a_probs[0][:80]}")
        d["vtype"] = "doc"
        print(f"   ✅ DOC đạt vòng {attempt}: total {score}, acc {acc} — {d.get('title')!r}")
        return d
    raise Exception(f"DOC sau {MAX_TRIES} vòng chưa đạt. Bỏ {niche!r}.")


# ─────────────────────────────────────────────────────────────────────────────
# WAVE 4 — 4 engine mới: SWARM (mật độ hạt), PULSE (gauge cường độ), CLOCKWORK (nén thời gian), LONGSHOT (xác suất).
SWARM_SYS = (
 "You are the creator of a #1 US channel that visualizes REAL crowd/quantity numbers as a satisfying particle swarm. "
 "Absolute rules:\n"
 "1) REAL COUNTS ONLY: every number is a true, verifiable real-world quantity (stadium capacity, population, biology "
 "counts, natural phenomena counts). Never invent.\n"
 "2) NEUTRAL CONTEXTS ONLY: stadiums, cities, nature, biology, everyday objects. NEVER protests/crowds-as-political-event, "
 "never disaster crowds, never sensitive gatherings.\n"
 "3) 3-5 items, each a DIFFERENT kind of quantity (don't repeat the same category of number twice in one video).\n"
 "4) shape must be exactly one of: stadium, city, person, circle, grid — pick whichever best matches the item's context.\n"
 "5) NARRATION spoken aloud: hook, one punchy line per item, CTA. Short natural sentences."
)
SWARM_SCHEMA = """Return STRICT JSON with EXACTLY these keys:
{
  "title": str,            // <=26 chars, e.g. "HOW MANY FIT?"
  "items": [               // 3-5
    { "label": str, "count": number, "countDisp": str, "shape": "stadium"|"city"|"person"|"circle"|"grid", "emoji": str, "vo": str }
    // countDisp = pretty formatted real number, e.g. "82,500"
  ],
  "intro_vo": str,
  "outro_vo": str,
  "title_yt": str, "description": str, "hashtags": [str], "tags": [str],
  // MỖI mục chấm ĐỘC LẬP thang 0-100 (KHÔNG phải điểm thành phần cộng vào total).
  //   accuracy = % câu/số liệu KIỂM CHỨNG ĐƯỢC; toàn bộ đều thật -> 100.
  "self_score": { "accuracy":0-100, "logic":0-100, "hook":0-100, "total":0-100 }
}
Counts must be real numbers. shape must be exactly one of the 5 listed."""


def _validate_swarm(d: dict) -> list[str]:
    errs = []
    its = d.get("items") or []
    if not (3 <= len(its) <= 6):
        errs.append("items cần 3–6")
    shapes = {"stadium", "city", "person", "circle", "grid"}
    for i, it in enumerate(its):
        if not str((it or {}).get("label", "")).strip():
            errs.append(f"item[{i}] thiếu label")
        if not isinstance((it or {}).get("count"), (int, float)):
            errs.append(f"item[{i}] count không phải số")
        if str((it or {}).get("shape", "")) not in shapes:
            errs.append(f"item[{i}] shape lạ")
        if not str((it or {}).get("vo", "")).strip():
            errs.append(f"item[{i}] thiếu vo")
    for k in ("title", "intro_vo", "outro_vo", "title_yt"):
        if not str(d.get(k, "")).strip():
            errs.append(f"thiếu '{k}'")
    return errs


def generate_swarm(niche: str, api_key: str = None, model_name: str = None, avoid: list = None) -> dict:
    """Sinh 1 kịch bản SWARM (mật độ/số lượng thật + narration). Viết lại tới khi đạt."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    model = genai.GenerativeModel(mname, system_instruction=SWARM_SYS)
    resolved = False
    avoid_txt = ("\nAvoid topics already used: " + " | ".join(avoid[-60:])) if avoid else ""
    base = (f'Make a crowd/quantity visualization in the niche "{niche}".\n{SWARM_SCHEMA}{avoid_txt}')
    feedback = ""; last = None
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base + (f"\n\nPrevious rejected: {feedback}\nFix and raise the score." if feedback else "")
        try:
            resp = model.generate_content(prompt, generation_config={"temperature": 0.85, "response_mime_type": "application/json"}, request_options=GEN_OPTS)
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and not resolved:
                mn = _pick_model(genai, prefer, akey); resolved = True
                if mn and mn != mname:
                    mname = mn; model = genai.GenerativeModel(mn, system_instruction=SWARM_SYS); continue
            if ("429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg or "ratelimit" in msg
                    or "denied" in msg or "permission" in msg or "forbidden" in msg or "403" in msg
                    or "suspended" in msg or "has not been used" in msg or "not enabled" in msg or "disabled" in msg):
                raise RateLimited(str(e))
            raise
        try:
            d = _extract_json(resp.text)
        except Exception as e:
            feedback = f"JSON lỗi ({e})."; continue
        errs = _validate_swarm(d)
        sc = d.get("self_score") or {}
        score = sc.get("total", 0); acc = int(sc.get("accuracy", 0))
        d["_attempt"] = attempt; last = d
        if errs:
            feedback = "Lỗi cấu trúc: " + "; ".join(errs[:6]); print(f"   ↻ swarm vòng {attempt}: {feedback}"); continue
        if acc < 95:
            feedback = f"accuracy={acc}<95. Chỉ dùng số lượng THẬT. Đổi item nếu không chắc số."
            print(f"   ↻ swarm vòng {attempt}: {feedback}"); continue
        if score < MIN_SCORE:
            feedback = f"Điểm {score}<{MIN_SCORE}. Hook mạnh hơn, số cuối gây sốc hơn."; print(f"   ↻ swarm vòng {attempt}: điểm {score}"); continue
        d["vtype"] = "swarm"
        print(f"   ✅ SWARM đạt vòng {attempt}: total {score}, acc {acc} — {d.get('title')!r}")
        return d
    raise Exception(f"SWARM sau {MAX_TRIES} vòng chưa đạt. Bỏ {niche!r}.")


PULSE_SYS = (
 "You are the creator of a #1 US channel comparing REAL sensory intensities (loudness dB, brightness lux, heat °F, "
 "g-force, radiation, etc) on a dramatic analog gauge. Absolute rules:\n"
 "1) REAL MEASURED VALUES ONLY, all in the SAME unit for one video (never mix dB with °F in one video). Never invent.\n"
 "2) Pick ONE unit/dimension per video (loudness OR heat OR g-force OR brightness...) — vary which dimension across "
 "different videos on this channel, but stay consistent WITHIN one video.\n"
 "3) 3-5 items ascending intensity, the LAST one should be genuinely extreme (mark extreme=true only for truly "
 "dangerous/record-breaking values).\n"
 "4) NO politics, no NSFW, no real injury/death imagery — describe the physical intensity, not harm to a specific person.\n"
 "5) NARRATION spoken aloud: hook, one punchy line per item, CTA. Short natural sentences."
)
PULSE_SCHEMA = """Return STRICT JSON with EXACTLY these keys:
{
  "title": str,            // <=26 chars, e.g. "HOW LOUD?"
  "unit": str,              // e.g. "dB"
  "maxScale": number,       // the gauge's max value (a bit above the largest item's value)
  "items": [                // 3-5, ASCENDING value
    { "label": str, "emoji": str, "value": number, "disp": str, "extreme": bool, "vo": str }
    // disp = pretty display e.g. "180 dB"; extreme=true ONLY for the genuinely record/dangerous item(s)
  ],
  "intro_vo": str,
  "outro_vo": str,
  "title_yt": str, "description": str, "hashtags": [str], "tags": [str],
  // MỖI mục chấm ĐỘC LẬP thang 0-100 (KHÔNG phải điểm thành phần cộng vào total).
  //   accuracy = % câu/số liệu KIỂM CHỨNG ĐƯỢC; toàn bộ đều thật -> 100.
  "self_score": { "accuracy":0-100, "logic":0-100, "hook":0-100, "total":0-100 }
}
Values must be real, same unit, ascending."""


def _validate_pulse(d: dict) -> list[str]:
    errs = []
    its = d.get("items") or []
    if not (3 <= len(its) <= 6):
        errs.append("items cần 3–6")
    if not isinstance(d.get("maxScale"), (int, float)):
        errs.append("thiếu maxScale số")
    vals = []
    for i, it in enumerate(its):
        if not str((it or {}).get("label", "")).strip():
            errs.append(f"item[{i}] thiếu label")
        if not isinstance((it or {}).get("value"), (int, float)):
            errs.append(f"item[{i}] value không phải số")
        else:
            vals.append(it["value"])
        if not str((it or {}).get("vo", "")).strip():
            errs.append(f"item[{i}] thiếu vo")
    if vals and vals != sorted(vals):
        errs.append("items phải xếp TĂNG DẦN")
    for k in ("title", "unit", "intro_vo", "outro_vo", "title_yt"):
        if not str(d.get(k, "")).strip():
            errs.append(f"thiếu '{k}'")
    return errs


def generate_pulse(niche: str, api_key: str = None, model_name: str = None, avoid: list = None) -> dict:
    """Sinh 1 kịch bản PULSE (cường độ giác quan thật + narration). Viết lại tới khi đạt."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    model = genai.GenerativeModel(mname, system_instruction=PULSE_SYS)
    resolved = False
    avoid_txt = ("\nAvoid units/topics already used: " + " | ".join(avoid[-60:])) if avoid else ""
    base = (f'Make an intensity-gauge comparison in the niche "{niche}".\n{PULSE_SCHEMA}{avoid_txt}')
    feedback = ""; last = None
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base + (f"\n\nPrevious rejected: {feedback}\nFix and raise the score." if feedback else "")
        try:
            resp = model.generate_content(prompt, generation_config={"temperature": 0.85, "response_mime_type": "application/json"}, request_options=GEN_OPTS)
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and not resolved:
                mn = _pick_model(genai, prefer, akey); resolved = True
                if mn and mn != mname:
                    mname = mn; model = genai.GenerativeModel(mn, system_instruction=PULSE_SYS); continue
            if ("429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg or "ratelimit" in msg
                    or "denied" in msg or "permission" in msg or "forbidden" in msg or "403" in msg
                    or "suspended" in msg or "has not been used" in msg or "not enabled" in msg or "disabled" in msg):
                raise RateLimited(str(e))
            raise
        try:
            d = _extract_json(resp.text)
        except Exception as e:
            feedback = f"JSON lỗi ({e})."; continue
        errs = _validate_pulse(d)
        sc = d.get("self_score") or {}
        score = sc.get("total", 0); acc = int(sc.get("accuracy", 0))
        d["_attempt"] = attempt; last = d
        if errs:
            feedback = "Lỗi cấu trúc: " + "; ".join(errs[:6]); print(f"   ↻ pulse vòng {attempt}: {feedback}"); continue
        if acc < 95:
            feedback = f"accuracy={acc}<95. Chỉ dùng số đo THẬT, cùng đơn vị. Đổi item nếu không chắc số."
            print(f"   ↻ pulse vòng {attempt}: {feedback}"); continue
        if score < MIN_SCORE:
            feedback = f"Điểm {score}<{MIN_SCORE}. Hook mạnh hơn, item cuối cực đoan hơn."; print(f"   ↻ pulse vòng {attempt}: điểm {score}"); continue
        d["vtype"] = "pulse"
        print(f"   ✅ PULSE đạt vòng {attempt}: total {score}, acc {acc} — {d.get('title')!r}")
        return d
    raise Exception(f"PULSE sau {MAX_TRIES} vòng chưa đạt. Bỏ {niche!r}.")


CLOCKWORK_SYS = (
 "You are the creator of a #1 US channel that compresses HUGE real timespans onto a single scale (a clock/timeline) "
 "to reveal a shocking true perspective. Absolute rules:\n"
 "1) REAL TIMESPANS ONLY: the total scale and every waypoint position are TRUE, verifiable durations/dates. Never invent.\n"
 "2) atPercent (0-100) is the waypoint's REAL proportional position within the total compressed scale — compute it "
 "correctly from the real numbers (do the math).\n"
 "3) The hero event must be a GENUINELY tiny/recent sliver relative to the whole scale (a real 'you won't believe how "
 "little time this actually is' fact) with atPercent very close to 100.\n"
 "4) 3-5 waypoints plus the hero. NO politics, no tragedy, no NSFW.\n"
 "5) NARRATION spoken aloud: hook, one punchy line per waypoint, big reveal line for hero, CTA."
)
CLOCKWORK_SCHEMA = """Return STRICT JSON with EXACTLY these keys:
{
  "title": str,             // <=26 chars, e.g. "EARTH'S HISTORY"
  "scaleLabel": str,        // e.g. "24 HOURS = 4.5 BILLION YEARS"
  "waypoints": [             // 3-5, ORDERED by atPercent ascending
    { "label": str, "atPercent": number, "vo": str }
  ],
  "hero": { "label": str, "atPercent": number, "realValue": str, "vo": str },
  // realValue = the shocking real duration to display big, e.g. "1.7 SECONDS"
  "intro_vo": str,
  "outro_vo": str,
  "title_yt": str, "description": str, "hashtags": [str], "tags": [str],
  // MỖI mục chấm ĐỘC LẬP thang 0-100 (KHÔNG phải điểm thành phần cộng vào total).
  //   accuracy = % câu/số liệu KIỂM CHỨNG ĐƯỢC; toàn bộ đều thật -> 100.
  "self_score": { "accuracy":0-100, "logic":0-100, "hook":0-100, "total":0-100 }
}
atPercent values must be mathematically correct real proportions."""


def _validate_clockwork(d: dict) -> list[str]:
    errs = []
    wps = d.get("waypoints") or []
    if not (3 <= len(wps) <= 6):
        errs.append("waypoints cần 3–6")
    pcts = []
    for i, w in enumerate(wps):
        if not str((w or {}).get("label", "")).strip():
            errs.append(f"waypoint[{i}] thiếu label")
        if not isinstance((w or {}).get("atPercent"), (int, float)):
            errs.append(f"waypoint[{i}] atPercent không phải số")
        else:
            pcts.append(w["atPercent"])
    if pcts and pcts != sorted(pcts):
        errs.append("waypoints phải xếp atPercent TĂNG DẦN")
    hero = d.get("hero") or {}
    for k in ("label", "atPercent", "realValue", "vo"):
        if not str(hero.get(k, "")).strip() and not isinstance(hero.get(k), (int, float)):
            errs.append(f"hero thiếu '{k}'")
    for k in ("title", "scaleLabel", "intro_vo", "outro_vo", "title_yt"):
        if not str(d.get(k, "")).strip():
            errs.append(f"thiếu '{k}'")
    return errs


def generate_clockwork(niche: str, api_key: str = None, model_name: str = None, avoid: list = None) -> dict:
    """Sinh 1 kịch bản CLOCKWORK (nén thời gian thật + narration). Viết lại tới khi đạt."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    model = genai.GenerativeModel(mname, system_instruction=CLOCKWORK_SYS)
    resolved = False
    avoid_txt = ("\nAvoid topics already used: " + " | ".join(avoid[-60:])) if avoid else ""
    base = (f'Make a time-compression reveal in the niche "{niche}".\n{CLOCKWORK_SCHEMA}{avoid_txt}')
    feedback = ""; last = None
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base + (f"\n\nPrevious rejected: {feedback}\nFix and raise the score." if feedback else "")
        try:
            resp = model.generate_content(prompt, generation_config={"temperature": 0.85, "response_mime_type": "application/json"}, request_options=GEN_OPTS)
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and not resolved:
                mn = _pick_model(genai, prefer, akey); resolved = True
                if mn and mn != mname:
                    mname = mn; model = genai.GenerativeModel(mn, system_instruction=CLOCKWORK_SYS); continue
            if ("429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg or "ratelimit" in msg
                    or "denied" in msg or "permission" in msg or "forbidden" in msg or "403" in msg
                    or "suspended" in msg or "has not been used" in msg or "not enabled" in msg or "disabled" in msg):
                raise RateLimited(str(e))
            raise
        try:
            d = _extract_json(resp.text)
        except Exception as e:
            feedback = f"JSON lỗi ({e})."; continue
        errs = _validate_clockwork(d)
        sc = d.get("self_score") or {}
        score = sc.get("total", 0); acc = int(sc.get("accuracy", 0))
        d["_attempt"] = attempt; last = d
        if errs:
            feedback = "Lỗi cấu trúc: " + "; ".join(errs[:6]); print(f"   ↻ clockwork vòng {attempt}: {feedback}"); continue
        if acc < 95:
            feedback = f"accuracy={acc}<95. atPercent phải tính ĐÚNG từ số liệu thật. Đổi ví dụ nếu không chắc số."
            print(f"   ↻ clockwork vòng {attempt}: {feedback}"); continue
        if score < MIN_SCORE:
            feedback = f"Điểm {score}<{MIN_SCORE}. Hook mạnh hơn, hero reveal sốc hơn."; print(f"   ↻ clockwork vòng {attempt}: điểm {score}"); continue
        d["vtype"] = "clockwork"
        print(f"   ✅ CLOCKWORK đạt vòng {attempt}: total {score}, acc {acc} — {d.get('title')!r}")
        return d
    raise Exception(f"CLOCKWORK sau {MAX_TRIES} vòng chưa đạt. Bỏ {niche!r}.")


LONGSHOT_SYS = (
 "You are the creator of a #1 US channel revealing REAL probability/odds of everyday and rare events, climbing a "
 "log-scale ladder. Absolute rules:\n"
 "1) REAL, SOURCED ODDS ONLY: every probability is a true, verifiable published figure (lottery odds, actuarial/CDC/"
 "NOAA/NHTSA-style published statistics, sports/game odds). Never invent a number.\n"
 "2) logValue = log10(the odds denominator) — e.g. odds of 1-in-100 -> logValue=2; 1-in-1,000,000 -> logValue=6. "
 "Compute it correctly from oddsDisp.\n"
 "3) 3-5 items, ORDERED least-rare to MOST-rare (ascending logValue), ending on a genuinely jaw-dropping real longshot.\n"
 "4) NO politics, no medical-diagnosis framing, no gambling encouragement — describe real statistical odds only, never advise betting.\n"
 "5) NARRATION spoken aloud: hook, one punchy line per item, big reveal line for the final longshot, CTA."
)
LONGSHOT_SCHEMA = """Return STRICT JSON with EXACTLY these keys:
{
  "title": str,             // <=26 chars, e.g. "WHAT ARE THE ODDS?"
  "items": [                 // 3-5, ORDERED logValue ASCENDING (common -> rare)
    { "label": str, "emoji": str, "oddsDisp": str, "logValue": number, "vo": str }
    // oddsDisp = "1 in 292,201,338" style; logValue = log10 of that denominator
  ],
  "intro_vo": str,
  "outro_vo": str,
  "title_yt": str, "description": str, "hashtags": [str], "tags": [str],
  // MỖI mục chấm ĐỘC LẬP thang 0-100 (KHÔNG phải điểm thành phần cộng vào total).
  //   accuracy = % câu/số liệu KIỂM CHỨNG ĐƯỢC; toàn bộ đều thật -> 100.
  "self_score": { "accuracy":0-100, "logic":0-100, "hook":0-100, "total":0-100 }
}
Odds must be real and sourced; logValue must match oddsDisp's denominator."""


def _validate_longshot(d: dict) -> list[str]:
    errs = []
    its = d.get("items") or []
    if not (3 <= len(its) <= 6):
        errs.append("items cần 3–6")
    logs = []
    for i, it in enumerate(its):
        if not str((it or {}).get("label", "")).strip():
            errs.append(f"item[{i}] thiếu label")
        if not str((it or {}).get("oddsDisp", "")).strip():
            errs.append(f"item[{i}] thiếu oddsDisp")
        if not isinstance((it or {}).get("logValue"), (int, float)):
            errs.append(f"item[{i}] logValue không phải số")
        else:
            logs.append(it["logValue"])
        if not str((it or {}).get("vo", "")).strip():
            errs.append(f"item[{i}] thiếu vo")
    if logs and logs != sorted(logs):
        errs.append("items phải xếp logValue TĂNG DẦN (thường -> hiếm)")
    for k in ("title", "intro_vo", "outro_vo", "title_yt"):
        if not str(d.get(k, "")).strip():
            errs.append(f"thiếu '{k}'")
    return errs


def generate_longshot(niche: str, api_key: str = None, model_name: str = None, avoid: list = None) -> dict:
    """Sinh 1 kịch bản LONGSHOT (xác suất thật + narration). Viết lại tới khi đạt."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    model = genai.GenerativeModel(mname, system_instruction=LONGSHOT_SYS)
    resolved = False
    avoid_txt = ("\nAvoid topics already used: " + " | ".join(avoid[-60:])) if avoid else ""
    base = (f'Make a real-odds ladder in the niche "{niche}".\n{LONGSHOT_SCHEMA}{avoid_txt}')
    feedback = ""; last = None
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base + (f"\n\nPrevious rejected: {feedback}\nFix and raise the score." if feedback else "")
        try:
            resp = model.generate_content(prompt, generation_config={"temperature": 0.85, "response_mime_type": "application/json"}, request_options=GEN_OPTS)
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and not resolved:
                mn = _pick_model(genai, prefer, akey); resolved = True
                if mn and mn != mname:
                    mname = mn; model = genai.GenerativeModel(mn, system_instruction=LONGSHOT_SYS); continue
            if ("429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg or "ratelimit" in msg
                    or "denied" in msg or "permission" in msg or "forbidden" in msg or "403" in msg
                    or "suspended" in msg or "has not been used" in msg or "not enabled" in msg or "disabled" in msg):
                raise RateLimited(str(e))
            raise
        try:
            d = _extract_json(resp.text)
        except Exception as e:
            feedback = f"JSON lỗi ({e})."; continue
        errs = _validate_longshot(d)
        sc = d.get("self_score") or {}
        score = sc.get("total", 0); acc = int(sc.get("accuracy", 0))
        d["_attempt"] = attempt; last = d
        if errs:
            feedback = "Lỗi cấu trúc: " + "; ".join(errs[:6]); print(f"   ↻ longshot vòng {attempt}: {feedback}"); continue
        if acc < 95:
            feedback = f"accuracy={acc}<95. Chỉ dùng xác suất THẬT có nguồn. Đổi item nếu không chắc số."
            print(f"   ↻ longshot vòng {attempt}: {feedback}"); continue
        if score < MIN_SCORE:
            feedback = f"Điểm {score}<{MIN_SCORE}. Hook mạnh hơn, longshot cuối sốc hơn."; print(f"   ↻ longshot vòng {attempt}: điểm {score}"); continue
        d["vtype"] = "longshot"
        print(f"   ✅ LONGSHOT đạt vòng {attempt}: total {score}, acc {acc} — {d.get('title')!r}")
        return d
    raise Exception(f"LONGSHOT sau {MAX_TRIES} vòng chưa đạt. Bỏ {niche!r}.")


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


# ─────────────────────────────────────────────────────────────────────────────
# TOON (22/8) — skit hài 2 nhân vật cố định, 3-5 khung FLUX + thoại. Dùng chung 2 kênh
# (BALD & BANDIT / HANKTOWN) — nhân vật + style lấy từ cấu hình kênh, KHÔNG hardcode ở đây.
TOON_SYS = (
 "You are the head writer of a #1 US comedy shorts channel using two FIXED cartoon characters. "
 "You write tight 18-30 second dialogue skits. Absolute rules:\n"
 "1) STRUCTURE: setup in line 1-2, escalation, then ONE hard punchline at the end. 6-9 lines total, "
 "each line under 14 words, spoken natural American English. Alternate speakers A/B. 7-10 lines total.\n"
 "2) CHARACTERS stay in the personalities given by the user prompt. Never rename them.\n"
 "3) FRAMES: describe 5-8 keyframes of ONE consistent scene (a new frame every 1-2 dialogue lines "
 "so the video cuts every 2-3 seconds): frame 1 = wide establishing, middle = "
 "emotion/pose changes, one frame = tight head-and-shoulders reaction shot (never say 'close-up of face'), "
 "final = punchline reaction. Each frame_prompt describes ONLY what changes (pose/expression/prop), "
 "no camera jargon, no text or signs in the scene.\n"
 "4) CLEAN: no politics, no slurs, no NSFW, no real brand names or celebrities. Family-safe irony is the tone.\n"
 "5) HOOK: the title is a VIRAL curiosity hook under 8 words in US shorts style (unexpected conflict, "
 "a challenge, or a relatable pain — e.g. 'The HOA fine', 'Why is gas $9?'); line 1 must hook within 2 "
 "seconds — start mid-conflict, never with greetings.\n"
 'Return STRICT JSON: {"title": str, "scene_base": str (one sentence, the constant setting), '
 '"frames": [{"prompt": str, "line_idx": int}], "dialog": [{"who": "A"|"B", "line": str}], '
 '"self_score": {"funny": 0-100, "hook": 0-100, "clean": 0-100, "total": 0-100}}'
)


def _validate_toon(d: dict) -> list:
    errs = []
    if not (d.get("title") or "").strip(): errs.append("thiếu title")
    if not (d.get("scene_base") or "").strip(): errs.append("thiếu scene_base")
    fr = d.get("frames") or []
    if not (4 <= len(fr) <= 9): errs.append(f"frames={len(fr)} (cần 5-8)")
    dl = d.get("dialog") or []
    if not (5 <= len(dl) <= 11): errs.append(f"dialog={len(dl)} câu (cần 7-10)")
    for i, l in enumerate(dl):
        if l.get("who") not in ("A", "B"): errs.append(f"dialog[{i}].who phải A/B")
        if len((l.get("line") or "").split()) > 18: errs.append(f"dialog[{i}] quá dài")
    for i, f in enumerate(fr):
        if not (f.get("prompt") or "").strip(): errs.append(f"frames[{i}] thiếu prompt")
        li = f.get("line_idx")
        if not isinstance(li, int) or not (0 <= li < max(1, len(dl))): errs.append(f"frames[{i}].line_idx sai")
    return errs


def generate_toon(niche: str, api_key: str = None, model_name: str = None, avoid: list = None) -> dict:
    """Sinh 1 skit TOON. `niche` = mô tả kênh + 2 nhân vật (từ config kênh). Viết lại tới khi đạt."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    if str(akey).startswith(("gsk_", "cf:")) and avoid:
        avoid = avoid[-30:]                     # nhà 8K token/request
    model = genai.GenerativeModel(mname, system_instruction=TOON_SYS)
    resolved = False
    avoid_txt = ("\nDo NOT reuse these premises: " + " | ".join(avoid[-40:])) if avoid else ""
    base = (f"Channel + characters: {niche}.\nWrite ONE new skit. Fresh everyday-America premise."
            + avoid_txt)
    feedback = ""; last = None
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base + (f"\n\nPrevious rejected: {feedback}\nFix it." if feedback else "")
        try:
            resp = model.generate_content(prompt, generation_config={"temperature": 0.95, "response_mime_type": "application/json"}, request_options=GEN_OPTS)
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and not resolved:
                mn = _pick_model(genai, prefer, akey); resolved = True
                if mn and mn != mname:
                    mname = mn; model = genai.GenerativeModel(mn, system_instruction=TOON_SYS); continue
            if ("429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg or "ratelimit" in msg
                    or "denied" in msg or "permission" in msg or "forbidden" in msg or "403" in msg
                    or "suspended" in msg or "has not been used" in msg or "not enabled" in msg or "disabled" in msg):
                raise RateLimited(str(e))
            raise
        try:
            d = _extract_json(resp.text)
        except Exception as e:
            feedback = f"invalid JSON ({e})"; continue
        errs = _validate_toon(d)
        sc = d.get("self_score") or {}
        score = int(sc.get("total", 0) or 0)
        d["_attempt"] = attempt; last = d
        if errs:
            feedback = "structure: " + "; ".join(errs[:6]); print(f"   ↻ toon vòng {attempt}: {feedback}"); continue
        if score < 95:
            feedback = f"total={score}<95 — punchline sắc hơn, hook giật hơn, thoại đời hơn."; print(f"   ↻ toon vòng {attempt}: điểm {score}"); continue
        print(f"   ✅ TOON đạt vòng {attempt}: total {score} — '{d.get('title')}'")
        return d
    if last: return last
    raise RuntimeError("toon: không sinh được kịch bản")


# ── TOON chế độ STORY (22/8 đêm) — narrator kể chuyện, stickman minh họa (TRUETALES/DUMBHISTORY/EXPLAINUSA)
TALE_SYS = (
 "You are the head writer of a #1 US narrated-story shorts channel (stick-figure illustrations). "
 "You write tight 25-40 second narrated stories. Absolute rules:\n"
 "1) HOOK: title is a VIRAL curiosity hook under 8 words (conflict/irony/absurd-but-true); sentence 1 "
 "drops the listener MID-DRAMA within 2 seconds — never begin with greetings or setup fluff.\n"
 "2) STRUCTURE: 7-11 narration sentences, each under 16 words, spoken natural American English; "
 "escalate stakes; END with a twist or dry punchline. Speaker is always the single narrator 'A'.\n"
 "3) FRAMES: 6-9 keyframes illustrating the beats (a new frame every 1-2 sentences so the video cuts every 2-3 seconds): frame 1 = establishing the scene, middle = the "
 "escalations, one tight head-and-shoulders reaction, final = the twist. Each frame_prompt describes "
 "only what is shown (pose/prop/scene), no camera jargon, no text or signs.\n"
 "4) TRUTHFUL & CLEAN: if the channel is factual (history/explainer) every fact must be real and "
 "verifiable — never invent; for everyday-life stories keep them fictional-but-relatable, no politics, "
 "no real brands or celebrities, family-safe.\n"
 'Return STRICT JSON: {"title": str, "scene_base": str, "frames": [{"prompt": str, "line_idx": int}], '
 '"dialog": [{"who": "A", "line": str}], "self_score": {"funny": 0-100, "hook": 0-100, "clean": 0-100, "total": 0-100}}'
)


ESSAY_SYS = (
 "You are the head writer of a #1 US explainer shorts channel — the kind people SAVE and SHARE "
 "because a belief they held got flipped. You write 30-45 second narrated visual essays. Rules:\n"
 "1) HOOK (make-or-break): title is a curiosity gap under 8 words promising a reversal. Sentence 1 "
 "must be a PUNCH under 9 words that names the stake or the number — e.g. 'Four foods your doctor "
 "was wrong about.' Never open with a greeting, a definition, or 'today we will talk about'. "
 "Sentence 2 raises the tension before any explanation begins.\n"
 "2) STRUCTURE: a LIST of 4-6 items, each item = 1-2 narration sentences: name the thing everyone "
 "believes, then the real mechanism in plain words with ONE concrete number or study finding. "
 "7-10 sentences total, each UNDER 13 WORDS (short lines read faster and fit one subtitle "
 "chunk), natural American English. Close with a one-line "
 "takeaway the viewer can repeat to a friend.\n"
 "3) FRAMES: 6-9 keyframes. Each frame_prompt is a VISUAL METAPHOR of that item, not a literal "
 "illustration — the thing personified, scaled absurdly, or in a place it does not belong (a mug of "
 "beer as a tiny character mopping a street, a brain hiding under a desk, salt crystals as guards). "
 "Describe only what is shown (subject/pose/props/setting), no camera jargon, no text or signs.\n"
 "3b) AMERICAN FINGERPRINT (mandatory in EVERY frame): the scene must read as the United States at "
 "a glance. Set it in a recognisably American place — suburban clapboard house with a porch and "
 "white picket fence, a diner booth, a big-box store aisle, an ER waiting room, a gas station at "
 "night, a school gym, an interstate, a strip mall parking lot — and include at least one everyday "
 "American object: a curbside mailbox with a red flag, a red plastic party cup, a yellow school bus, "
 "a paper coffee cup, a long receipt, a pill bottle, a pickup truck, a fire hydrant, a folding lawn "
 "chair, a stop sign shape. Any people are ordinary Americans of mixed ages and ethnicities in "
 "everyday US clothing (hoodie, scrubs, work polo, baseball cap) — never generic anonymous figures, "
 "never other countries' streets, uniforms or signage. Keep the fingerprint as a PROP or SETTING, "
 "not as a flag draped over everything: subtle, lived-in, never political.\n"
 "4) MONETIZATION-SAFE (YouTube YPP): the video must be ORIGINAL commentary that ADDS analysis — never a plain list read from one article; no shocking/graphic wording, no clickbait the video does not deliver, no health claims phrased as advice ('you should', 'cures'), no medical/financial instructions; state uncertainty when evidence is mixed.\n"
 "5) TRUTHFUL: every claim must be REAL and verifiable (peer-reviewed nutrition/medicine/economics/"
 "history). Never invent studies or numbers. No medical advice, no politics, no real brands or "
 "celebrities, family-safe. US-centric framing (US prices, US habits, US institutions).\n"
 'Return STRICT JSON: {"title": str, "scene_base": str, "frames": [{"prompt": str, "line_idx": int}], '
 '"dialog": [{"who": "A", "line": str}], "sources": [str], '
 '"self_score": {"surprise": 0-100, "hook": 0-100, "clean": 0-100, "total": 0-100}}'
)


def _validate_essay(d: dict) -> list:
    """Essay = bài phân tích lật-ngược-niềm-tin (23/8, thay format skit hài): siết HOOK + độ thật.
    Khác tale: bắt buộc có 'sources' (dẫn nguồn thật) và câu chốt phải là takeaway, không phải punchline."""
    errs = []
    if not (d.get("title") or "").strip():
        errs.append("thiếu title")
    if len((d.get("title") or "").split()) > 11:
        errs.append("title quá dài (hook phải <9 từ)")
    if not (d.get("scene_base") or "").strip():
        errs.append("thiếu scene_base")
    fr = d.get("frames") or []
    if not (5 <= len(fr) <= 10):
        errs.append(f"frames={len(fr)} (cần 6-9)")
    dl = d.get("dialog") or []
    if not (6 <= len(dl) <= 12):
        errs.append(f"narration={len(dl)} câu (cần 7-10)")
    for i, l in enumerate(dl):
        if (l.get("who") or "A") != "A":
            errs.append(f"câu {i}: essay chỉ 1 giọng kể 'A'")
        # 23/8 (user: "sub hơi dài, video bị dài"): trần 13 từ -> mỗi câu vừa 2-3 cụm phụ đề,
        # đọc kịp trên điện thoại; câu đầu siết chặt hơn nữa vì nó QUYẾT ĐỊNH giữ chân 2 giây đầu.
        _n = len((l.get("line") or "").split())
        if _n > 15:
            errs.append(f"câu {i} quá dài ({_n} từ, trần 13)")
    if dl and len((dl[0].get("line") or "").split()) > 11:
        errs.append("câu MỞ ĐẦU quá dài — hook phải dưới 9 từ")
    if not any(any(ch.isdigit() for ch in (l.get("line") or "")) for l in dl):
        errs.append("thiếu SỐ LIỆU cụ thể (essay phải có ít nhất 1 con số thật)")
    if len([s for s in (d.get("sources") or []) if str(s).strip()]) < 1:
        errs.append("thiếu sources (bắt buộc dẫn nguồn thật)")
    for i, f in enumerate(fr):
        if not (f.get("prompt") or "").strip():
            errs.append(f"frames[{i}] thiếu prompt")
        li = f.get("line_idx")
        if not isinstance(li, int) or not (0 <= li < max(1, len(dl))):
            errs.append(f"frames[{i}].line_idx sai")
    return errs


def _validate_tale(d: dict) -> list:
    errs = []
    if not (d.get("title") or "").strip(): errs.append("thiếu title")
    if not (d.get("scene_base") or "").strip(): errs.append("thiếu scene_base")
    fr = d.get("frames") or []
    if not (4 <= len(fr) <= 10): errs.append(f"frames={len(fr)} (cần 6-9)")
    dl = d.get("dialog") or []
    if not (6 <= len(dl) <= 12): errs.append(f"narration={len(dl)} câu (cần 7-11)")
    for i, l in enumerate(dl):
        if len((l.get("line") or "").split()) > 20: errs.append(f"câu {i} quá dài")
    for i, f in enumerate(fr):
        if not (f.get("prompt") or "").strip(): errs.append(f"frames[{i}] thiếu prompt")
        li = f.get("line_idx")
        if not isinstance(li, int) or not (0 <= li < max(1, len(dl))): errs.append(f"frames[{i}].line_idx sai")
    return errs


def generate_tale(niche: str, api_key: str = None, model_name: str = None, avoid: list = None) -> dict:
    """Sinh 1 chuyện narrator (mode story) — cùng khuôn generate_toon, sys/validator riêng."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    if str(akey).startswith(("gsk_", "cf:")) and avoid:
        avoid = avoid[-30:]
    model = genai.GenerativeModel(mname, system_instruction=TALE_SYS)
    resolved = False
    avoid_txt = ("\nDo NOT reuse these premises: " + " | ".join(avoid[-40:])) if avoid else ""
    base = (f"Channel: {niche}.\nWrite ONE new narrated story. Every speaker is 'A'." + avoid_txt)
    feedback = ""; last = None
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base + (f"\n\nPrevious rejected: {feedback}\nFix it." if feedback else "")
        try:
            resp = model.generate_content(prompt, generation_config={"temperature": 0.95, "response_mime_type": "application/json"}, request_options=GEN_OPTS)
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and not resolved:
                mn = _pick_model(genai, prefer, akey); resolved = True
                if mn and mn != mname:
                    mname = mn; model = genai.GenerativeModel(mn, system_instruction=TALE_SYS); continue
            if ("429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg or "ratelimit" in msg
                    or "denied" in msg or "permission" in msg or "forbidden" in msg or "403" in msg
                    or "suspended" in msg or "has not been used" in msg or "not enabled" in msg or "disabled" in msg):
                raise RateLimited(str(e))
            raise
        try:
            d = _extract_json(resp.text)
        except Exception as e:
            feedback = f"invalid JSON ({e})"; continue
        for l in (d.get("dialog") or []):
            l["who"] = "A"                       # narrator duy nhất
        errs = _validate_tale(d)
        sc = d.get("self_score") or {}
        score = int(sc.get("total", 0) or 0)
        d["_attempt"] = attempt; last = d
        if errs:
            feedback = "structure: " + "; ".join(errs[:6]); print(f"   ↻ tale vòng {attempt}: {feedback}"); continue
        if score < 95:
            feedback = f"total={score}<95 — twist sắc hơn, hook giật hơn."; print(f"   ↻ tale vòng {attempt}: điểm {score}"); continue
        print(f"   ✅ TALE đạt vòng {attempt}: total {score} — '{d.get('title')}'")
        return d
    if last: return last
    raise RuntimeError("tale: không sinh được chuyện")

def generate_essay(niche: str, api_key: str = None, model_name: str = None, avoid: list = None) -> dict:
    """Sinh 1 BÀI PHÂN TÍCH (mode essay, 23/8) — lật ngược niềm tin + ẩn dụ hình ảnh; khuôn chung."""
    genai = _genai(api_key)
    akey = api_key or os.environ.get("GEMINI_API_KEY", "")
    prefer = "pro" if (model_name and "pro" in model_name) else "flash"
    mname = model_name or MODEL
    if str(akey).startswith(("gsk_", "cf:")) and avoid:
        avoid = avoid[-30:]
    model = genai.GenerativeModel(mname, system_instruction=ESSAY_SYS)
    resolved = False
    avoid_txt = ("\nDo NOT reuse these premises: " + " | ".join(avoid[-40:])) if avoid else ""
    base = (f"Channel: {niche}.\nWrite ONE new visual essay that flips a belief. Every speaker is 'A'. Include real sources." + avoid_txt)
    feedback = ""; last = None
    for attempt in range(1, MAX_TRIES + 1):
        prompt = base + (f"\n\nPrevious rejected: {feedback}\nFix it." if feedback else "")
        try:
            resp = model.generate_content(prompt, generation_config={"temperature": 0.95, "response_mime_type": "application/json"}, request_options=GEN_OPTS)
        except Exception as e:
            msg = str(e).lower()
            if ("404" in msg or "not found" in msg or "no longer available" in msg) and not resolved:
                mn = _pick_model(genai, prefer, akey); resolved = True
                if mn and mn != mname:
                    mname = mn; model = genai.GenerativeModel(mn, system_instruction=ESSAY_SYS); continue
            if ("429" in msg or "quota" in msg or "resource_exhausted" in msg or "rate limit" in msg or "ratelimit" in msg
                    or "denied" in msg or "permission" in msg or "forbidden" in msg or "403" in msg
                    or "suspended" in msg or "has not been used" in msg or "not enabled" in msg or "disabled" in msg):
                raise RateLimited(str(e))
            raise
        try:
            d = _extract_json(resp.text)
        except Exception as e:
            feedback = f"invalid JSON ({e})"; continue
        for l in (d.get("dialog") or []):
            l["who"] = "A"                       # narrator duy nhất
        errs = _validate_essay(d)
        sc = d.get("self_score") or {}
        score = int(sc.get("total", 0) or 0)
        d["_attempt"] = attempt; last = d
        if errs:
            feedback = "structure: " + "; ".join(errs[:6]); print(f"   ↻ tale vòng {attempt}: {feedback}"); continue
        if score < 95:
            feedback = f"total={score}<95 — twist sắc hơn, hook giật hơn."; print(f"   ↻ tale vòng {attempt}: điểm {score}"); continue
        print(f"   ✅ TALE đạt vòng {attempt}: total {score} — '{d.get('title')}'")
        return d
    if last: return last
    raise RuntimeError("tale: không sinh được chuyện")

# ── SOI LẠI KỊCH BẢN 1 LƯỢT TRƯỚC KHI RENDER (23/8, theo yêu cầu) ─────────────────────────────
# Bài viết xong vẫn có thể: câu dài lê thê, 2 khung tả CÙNG một cảnh (=> ảnh trùng), thiếu số thật,
# hoặc trùng ý với video cũ của chính kênh. Bước này là 1 lượt gọi AI đóng vai BIÊN TẬP KHÓ TÍNH:
# sửa tại chỗ rồi trả về đúng khuôn JSON cũ. Hỏng thì trả nguyên bản (không bao giờ chặn render).
REVIEW_SYS = (
    "You are a ruthless script editor for a US YouTube channel. You receive ONE script as JSON.\n"
    "Return the SAME JSON schema, corrected in place. Never add or remove keys. Rules:\n"
    "1) Every spoken line <= 13 words. Split or cut anything longer. Plain American English.\n"
    "2) First line must hook in under 9 words. If it does not, rewrite it.\n"
    "3) No two lines may repeat the same idea. Delete filler, keep the story moving.\n"
    "4) Every visual/frame description must show a DIFFERENT subject, place and camera angle.\n"
    "   If two frames would produce a similar photo, rewrite the later one entirely.\n"
    "5) At least 3 concrete real numbers stay in the script, each tied to its source.\n"
    "6) Do not invent facts. Keep every existing source. Monetization-safe: no gore, no slurs,\n"
    "   no medical/financial advice, no real person accused of anything.\n"
    "Return JSON only."
)


def review_script(d: dict, niche: str = "", api_key: str = None, model_name: str = None,
                  avoid: list = None) -> dict:
    """Trả về kịch bản đã soi/sửa. Mọi lỗi -> trả nguyên bản (không chặn render)."""
    try:
        genai = _genai(api_key)
        model = genai.GenerativeModel(model_name or MODEL, system_instruction=REVIEW_SYS)
        av = ("\nAlready used by this channel, must NOT be repeated: " + " | ".join((avoid or [])[-25:])) if avoid else ""
        resp = model.generate_content(
            f"Channel: {niche}.{av}\n\nSCRIPT:\n" + json.dumps(d, ensure_ascii=False),
            generation_config={"temperature": 0.4, "response_mime_type": "application/json"},
            request_options=GEN_OPTS)
        out = _extract_json(resp.text)
        if not isinstance(out, dict) or not (out.get("dialog") or []):
            return d
        for l in (out.get("dialog") or []):
            l["who"] = l.get("who") or "A"
        for k in ("self_score", "sources", "_attempt"):
            if k in d and k not in out:
                out[k] = d[k]
        n_fix = sum(1 for a, b in zip(d.get("dialog") or [], out.get("dialog") or [])
                    if (a.get("line") or "") != (b.get("line") or ""))
        print(f"   🔎 soi kịch bản: sửa {n_fix}/{len(out.get('dialog') or [])} câu")
        return out
    except Exception as e:
        print(f"   🔎 soi kịch bản bỏ qua ({str(e)[:60]})")
        return d

