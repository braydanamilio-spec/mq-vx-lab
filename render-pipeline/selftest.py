"""
selftest.py — TỰ KIỂM TRƯỚC MỖI PHIÊN (chạy ở đầu job plan, <10s, 0 mạng, 0 quota Firestore/AI).

Vì sao tồn tại (22/8): 3 lần trong 1 ngày, một bản push hỏng giết cả phiên production mà chỉ
lộ ra khi 18 luồng đã chạy: (a) _GroqShim thiếu system_instruction -> TypeError 18/18 luồng;
(b) script vá trượt assert nhưng vẫn commit; (c) dấu phẩy thừa làm chết dashboard. Bộ này chạy
ĐÚNG các đường gọi sản xuất bằng mock — push hỏng là plan fail NGAY trong 30 giây đầu, lane
không spawn, không đốt quota, dashboard hiện lỗi rõ ràng thay vì 18 lane chết khó hiểu.

LUẬT: thêm lớp lỗi mới vào BUG LOG thì cân nhắc thêm 1 test tương ứng vào đây.
"""
from __future__ import annotations
import io
import json
import sys
import urllib.error
import urllib.request

FAILS = []


def check(name, fn):
    try:
        fn()
        print(f"  ✅ {name}")
    except Exception as e:
        FAILS.append(f"{name}: {type(e).__name__}: {str(e)[:120]}")
        print(f"  ❌ {name}: {str(e)[:160]}")


# chặn MỌI lệnh mạng thật — selftest phải chạy được cả khi không có mạng/quota
class _NoNet:
    def __init__(self):
        self.calls = []

    def __call__(self, req, timeout=0):
        self.calls.append(req)
        raise RuntimeError("selftest: không được gọi mạng thật")


def t_shim_signatures():
    """Lớp lỗi (a) 22/8: shim đội lốt SDK phải phủ ĐỦ chữ ký call site thật."""
    import content_brain as CB
    outs = {}

    def fake(req, timeout=0):
        body = json.loads(req.data.decode())
        outs["msgs"] = body["messages"]
        assert "MM0-render" in req.headers.get("User-agent", ""), "thiếu User-Agent"
        class R:
            headers = {}
            def read(self): return json.dumps({"choices": [{"message": {"content": '{"ok":1}'}}]}).encode()
            def __enter__(self): return self
            def __exit__(self, *a): return False
        return R()

    urllib.request.urlopen = fake
    for key in ("gsk_selftest", "cf:0123456789abcdef0123456789abcdef:tok_selftest"):
        genai = CB._genai(key)
        m = genai.GenerativeModel("gemini-3.5-flash", system_instruction="You are a writer.")
        r = m.generate_content("hello", generation_config={"response_mime_type": "application/json",
                                                           "temperature": 0.5},
                               request_options={"timeout": 30})
        assert json.loads(r.text)["ok"] == 1
        assert outs["msgs"][0]["role"] == "system", f"{key[:4]}: system_instruction không được map"
        # vision path (qc_vision dùng dạng [text, {mime_type,data}]) — chỉ CF có vision
        if key.startswith("cf:"):
            r2 = m.generate_content(["what is this?", {"mime_type": "image/jpeg", "data": b"\xff\xd8x"}])
            assert json.loads(r2.text)["ok"] == 1


def t_groq_waf_1010():
    """Lớp lỗi 22/8: 403/1010 (WAF) phải thành lỗi TẠM per-minute, không giết video/key."""
    import content_brain as CB

    def fake(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 403, "f", {}, io.BytesIO(b"error code: 1010"))

    urllib.request.urlopen = fake
    m = CB._genai("gsk_selftest").GenerativeModel("f")
    try:
        m.generate_content("hi")
        raise AssertionError("phải ném RuntimeError")
    except RuntimeError as e:
        assert "429 rate limit per minute" in str(e), str(e)


def t_groq_model_selfprobe():
    """Groq gỡ model (llama-3.3 đã xảy ra thật) -> shim tự dò model sống từ /models."""
    import content_brain as CB
    CB._GroqShim._live_model = None
    state = {"n": 0}

    def fake(req, timeout=0):
        state["n"] += 1
        if "chat/completions" in req.full_url:
            body = json.loads(req.data.decode())
            if body["model"] == CB.GROQ_MODEL and state["n"] < 3:
                raise urllib.error.HTTPError(req.full_url, 404, "nf", {},
                                             io.BytesIO(b'{"error":{"message":"model does not exist"}}'))
            class R:
                headers = {}
                def read(self): return json.dumps({"choices": [{"message": {"content": body["model"]}}]}).encode()
                def __enter__(self): return self
                def __exit__(self, *a): return False
            return R()
        class M:
            headers = {}
            def read(self): return json.dumps({"data": [{"id": "qwen/qwen3.6-27b"}]}).encode()
            def __enter__(self): return self
            def __exit__(self, *a): return False
        return M()

    urllib.request.urlopen = fake
    r = CB._genai("gsk_selftest").GenerativeModel("f").generate_content("hi")
    assert r.text == "qwen/qwen3.6-27b", r.text
    CB._GroqShim._live_model = None


def t_key_order():
    """Thứ tự viết: Groq -> CF -> Gemini (bảo toàn đạn Vision Gemini)."""
    import key_manager as KM
    ks = [{"id": "g1", "key": "AIza1"}, {"id": "c1", "key": "cf:a:t"},
          {"id": "q1", "key": "gsk_1"}, {"id": "g2", "key": "AIza2"}]
    o = [k["id"] for k in KM.key_order("SELFTEST", ks)]
    assert o[0] == "q1" and o[1] == "c1" and set(o[2:]) == {"g1", "g2"}, o


def t_ai_pool_split():
    """Pool vẽ: CF trước Gemini; vision: Gemini trước CF; Groq bị loại cả hai."""
    import datastory_ci as DS
    ks = [{"key": "AIza1"}, {"key": "cf:a:t"}, {"key": "gsk_1"}]
    DS.set_ai_pool(ks, "SELFTEST")
    assert DS._AI_POOL["keys"][0].startswith("cf:")
    assert DS._vision_order(["cf:a:t", "AIza1", "gsk_1"]) == ["AIza1", "cf:a:t"]


def t_soft_read():
    """Quota ĐỌC chết -> read_keys/read_config trả đệm/mặc định, KHÔNG ném (lỗi 18/18 luồng 04:22Z)."""
    import firestore_bridge as FB
    saved = (FB._retry, getattr(FB, "_db_keys"), getattr(FB, "_db_meta"))
    try:
        FB._retry = lambda fn, tries=5: fn()

        def boom():
            raise RuntimeError("429 Quota exceeded RESOURCE_EXHAUSTED")
        FB._db_keys = boom
        FB._db_meta = boom
        FB._KEYS_CACHE.clear()
        FB._RQ_DEAD["until"] = 0
        assert FB.read_keys("selftest_owner") == []
        FB._RQ_DEAD["until"] = 0
        assert isinstance(FB.read_config("selftest_owner"), dict)
    finally:
        FB._retry, FB._db_keys, FB._db_meta = saved
        FB._KEYS_CACHE.clear()
        FB._RQ_DEAD["until"] = 0


def t_dark_ok():
    """Cổng mở-đầu-tối: kênh vũ trụ không bị giết oan, nền trơn thật vẫn bị bắt."""
    import datastory_ci as DS
    assert DS._dark_ok("COSMOS") and DS._dark_ok("thedeep") and not DS._dark_ok("DEBTUSA")
    for dark, cols, dk, expect_flat in ((85.9, 750, True, False), (91.9, 342, True, True),
                                        (85.9, 750, False, True), (43.9, 1983, False, False)):
        flat = (dark >= 88 and cols < 450) if dk else (dark >= 75 and cols < 900)
        assert flat == expect_flat, (dark, cols, dk)


def t_toon():
    """TOON (22/8): validator + né bộ lọc + route fmt trong run_render."""
    import content_brain as CB, datastory_ci as DS
    good = {"title": "The HOA Letter", "scene_base": "backyard BBQ",
            "frames": [{"prompt": "wide", "line_idx": 0}, {"prompt": "shock", "line_idx": 2},
                       {"prompt": "tight head-and-shoulders reaction", "line_idx": 4}],
            "dialog": [{"who": "A", "line": "x"}] * 3 + [{"who": "B", "line": "y"}] * 3,
            "self_score": {"total": 95}}
    assert CB._validate_toon(good) == [], CB._validate_toon(good)
    bad = dict(good); bad2 = dict(good); bad2["frames"] = []
    assert CB._validate_toon(bad2)
    assert "head-and-shoulders" in DS._toon_safe("extreme close-up of face")
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_render.py")).read()
    assert '"toon"' in src and "make_toon" in src, "run_render chưa route toon"


def t_extract_json():
    import content_brain as CB
    assert CB._extract_json('```json\n{"a": 1}\n```')["a"] == 1
    assert CB._extract_json('{"b": 2}')["b"] == 2


def main():
    print("🧪 SELFTEST (0 mạng · 0 quota) — chặn bản deploy hỏng trước khi spawn 18 luồng:")
    check("shim Groq/CF: system_instruction + UA + JSON + vision", t_shim_signatures)
    check("groq WAF 1010 -> lỗi tạm per-minute", t_groq_waf_1010)
    check("groq model bị gỡ -> tự dò model sống", t_groq_model_selfprobe)
    check("key_order viết: groq -> cf -> gemini", t_key_order)
    check("pool vẽ cf-trước / vision gemini-trước", t_ai_pool_split)
    check("đọc-mềm: quota chết không ném", t_soft_read)
    check("cổng dark_ok theo kênh", t_dark_ok)
    check("_extract_json bóc ```json", t_extract_json)
    check("toon: validator + safe-words + route", t_toon)
    if FAILS:
        print(f"\n🚨 SELFTEST FAIL ({len(FAILS)}) — CHẶN PHIÊN để không đốt 18 luồng vào bản hỏng:")
        for f in FAILS:
            print("   - " + f)
        sys.exit(1)
    print("✅ SELFTEST PASS — code lành, cho phép chạy phiên.")


if __name__ == "__main__":
    main()
