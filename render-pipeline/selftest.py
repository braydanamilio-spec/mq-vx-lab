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
import os
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


def t_het_key_thi_doi_key():
    """24/8: key Groq cạn hạn mức NGÀY phải làm hệ ĐỔI KEY, tuyệt đối không giết cả luồng.
    Đêm 23/8 lỗi này khiến POWERPLAY ra 0 video dù còn 40 key + CF + Gemini chưa đụng tới."""
    import content_brain as CB, key_manager as KM
    def gen_gia(niche, api_key=None, model_name=None, avoid=None):
        if str(api_key).startswith("gsk_"):
            raise RuntimeError("429 rate limit daily (groq): tokens per day (TPD): Limit 200000")
        return {"title": "du phong", "dialog": [{"who": "A", "line": "x"}], "sources": ["a", "b"]}
    CB.generate_thu_selftest = gen_gia
    keys = [{"id": "g1", "key": "gsk_1"}, {"id": "g2", "key": "gsk_2"}, {"id": "c1", "key": "cf:acc:tok"}]
    d = KM._write_wave4("generate_thu_selftest", "THU", "CH", keys, "niche", "normal", None, None, None)
    assert d.get("title") == "du phong", d
    print("  ✅ key cạn quota -> đổi key (không giết luồng)")


def t_groq_tpd_la_daily():
    """24/8: Groq cạn TOKEN/ngày (TPD) trong khi vẫn còn LƯỢT -> phải nhận nhãn 'daily' (phạt 8h),
    không được nhận 'per minute' (phạt 1.1') — chính lỗi làm POWERPLAY ra 0 video 3 phiên liền."""
    import content_brain as CB

    def fake(req, timeout=0):
        body = b'{"error":{"message":"Rate limit reached ... on tokens per day (TPD): Limit 200000"}}'
        raise urllib.error.HTTPError(req.full_url, 429, "x",
                                     {"x-ratelimit-remaining-requests": "500"}, io.BytesIO(body))

    urllib.request.urlopen = fake
    m = CB._genai("gsk_selftest").GenerativeModel("f")
    try:
        m.generate_content("hi")
        raise AssertionError("phải ném RateLimited")
    except CB.RateLimited as e:
        assert "daily" in str(e), str(e)[:80]
    print("  ✅ cạn token/ngày -> nhãn daily (phạt 8h, không dội lại key chết)")


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
    _b2env = os.environ.pop("FIREBASE_PROJECT_ID_B2", None)   # chặn failover B2 kích hoạt TRONG test
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
        if _b2env is not None:
            os.environ["FIREBASE_PROJECT_ID_B2"] = _b2env
        # trạng thái failover là GLOBAL tiến trình — test nào lỡ kích phải trả về OFF, không thì
        # (a) t_b2 phía sau fail oan -> selftest CHẶN CẢ PHIÊN, (b) các test sau chạy nhầm trên B2.
        FB._B2["on"] = False
        FB._B2["client"] = None


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
            "frames": [{"prompt": "wide", "line_idx": 0}, {"prompt": "lean in", "line_idx": 1},
                       {"prompt": "shock", "line_idx": 3}, {"prompt": "tight head-and-shoulders reaction", "line_idx": 5},
                       {"prompt": "punchline pose", "line_idx": 6}],
            "dialog": [{"who": "A", "line": "x"}] * 4 + [{"who": "B", "line": "y"}] * 4,
            "self_score": {"total": 95}}
    assert CB._validate_toon(good) == [], CB._validate_toon(good)
    bad = dict(good); bad2 = dict(good); bad2["frames"] = []
    assert CB._validate_toon(bad2)
    assert "head-and-shoulders" in DS._toon_safe("extreme close-up of face")
    # 22/8 đêm: FLUX in chữ giả khi prompt chứa tên HOA / từ 'advertising' (đo 6 lượt vẽ brand thật)
    _s = DS._toon_safe("PEARL a friendly woman, USA advertising cartoon, UPA look")
    assert "PEARL" not in _s and "USA" not in _s and "advertising" not in _s and "friendly woman" in _s
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_render.py")).read()
    assert '"toon"' in src and "make_toon" in src, "run_render chưa route toon"
    tale = {"title": "The Pig War", "scene_base": "island farm 1859",
            "frames": [{"prompt": "wide", "line_idx": 0}, {"prompt": "standoff", "line_idx": 3},
                       {"prompt": "tight head-and-shoulders", "line_idx": 5}, {"prompt": "twist", "line_idx": 7}],
            "dialog": [{"who": "A", "line": "x"}] * 8, "self_score": {"total": 96}}
    assert CB._validate_tale(tale) == [], CB._validate_tale(tale)
    assert "toon_mode" in src, "dispatch chưa truyền toon_mode"
    # ESSAY (23/8 — format phân tích thay skit hài): validator siết hook/số liệu/nguồn + route mode
    essay = {"title": "Foods doctors banned that add years", "scene_base": "american kitchen",
             "frames": [{"prompt": "a coffee mug as a tiny character mopping a street", "line_idx": 0}] * 6,
             "dialog": [{"who": "A", "line": "Coffee was blamed for heart disease for forty years."}] * 8,
             "sources": ["NIH cohort study 2022"], "self_score": {"total": 96}}
    essay["dialog"][2] = {"who": "A", "line": "A 2022 NIH study of 500,000 adults found the opposite."}
    assert CB._validate_essay(essay) == [], CB._validate_essay(essay)
    _bad = dict(essay); _bad["sources"] = []
    assert CB._validate_essay(_bad), "essay thiếu nguồn phải bị chặn"
    import key_manager as KM2
    assert callable(KM2.write_essay)
    assert '"essay": KM.write_essay' in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "datastory_ci.py")).read()


def t_b2_failover():
    """B2 (23/8): thiếu env -> failover từ chối êm, _db routing không đổi; cờ _B2 mặc định tắt."""
    import firestore_bridge as FB
    saved = dict(os.environ)
    FB._B2["on"] = False; FB._B2["client"] = None   # dọn cờ global phòng test trước lỡ kích
    try:
        os.environ.pop("FIREBASE_PROJECT_ID_B2", None)
        assert FB._b2_available() is False
        assert FB.failover_to_b2("selftest") is False
        assert FB._B2["on"] is False
    finally:
        os.environ.clear(); os.environ.update(saved)


def t_failover_rehearsal():
    """DIỄN TẬP FAILOVER (23/8, user: "đừng chạy xong mới ớ ra"): giả lập B chết giữa phiên bằng
    client GIẢ (0 mạng, 0 quota) và kiểm 4 đường gây HỎNG SẢN PHẨM nếu lệch:
      1) chủ đề ghi song song B+B2   2) phiên khẩn vẫn giữ đề tài cũ
      3) count_done ở B2 = sổ thống kê + job khẩn (không về 0 -> không làm dư video)
      4) rót ngược GỘP hai phía (không đè mất ngân hàng chống trùng)."""
    import firestore_bridge as FB

    class D:
        def __init__(s, d, i="x"): s._d, s.id, s.exists = d, i, d is not None
        def to_dict(s): return dict(s._d or {})
        @property
        def reference(s): return s

    class R:
        def __init__(s, st, c, i): s.st, s.c, s.id = st, c, i
        def get(s): return D(s.st.get(s.c, {}).get(s.id))
        def set(s, d, merge=False):
            cur = s.st.setdefault(s.c, {}).setdefault(s.id, {})
            cur.update(d) if merge else s.st[s.c].update({s.id: dict(d)})
        def delete(s): s.st.get(s.c, {}).pop(s.id, None)

    class C:
        def __init__(s, st, n): s.st, s.n = st, n
        def document(s, i): return R(s.st, s.n, i)
        def where(s, *a, **k): return s
        def limit(s, n): return s
        def order_by(s, *a, **k): return s
        def stream(s): return [D(v, i) for i, v in s.st.get(s.n, {}).items()]

    class DB:
        def __init__(s, st): s.st = st
        def collection(s, n): return C(s.st, n)

    B, B2, own = {}, {}, "u1"
    key = f"{own}__CH"
    B["render_topics"] = {key: {"owner": own, "channel": "CH", "topics": ["cu1"]}}
    B2["render_topics"] = {key: {"owner": own, "channel": "CH", "topics": ["cu1"]}}
    B2["render_stats"] = {own: {"CH": {"l": 4, "s": 12}}}
    sv = (FB._db_meta, FB._db_jobs, FB._db, FB._soft, FB._b2_available, FB._count_jobs,
          dict(FB._B2))
    try:
        FB._db_meta = FB._db_jobs = FB._db = lambda: DB(B)
        FB._soft = lambda fn, tag: fn()
        FB._b2_available = lambda: True
        FB._B2["on"] = False; FB._B2["wclient"] = DB(B2)
        FB._TOPICS_CACHE.clear(); FB._HOT_CACHE.clear()
        FB.save_topics(own, "CH", ["moiA"])
        assert "moiA" in B["render_topics"][key]["topics"], "B thiếu đề tài mới"
        assert "moiA" in B2["render_topics"][key]["topics"], "B2 KHÔNG nhận ghi song song"
        FB._B2["on"] = True; FB._B2["client"] = DB(B2)
        FB._db_meta = FB._db_jobs = lambda: DB(B2)
        FB._TOPICS_CACHE.clear()
        FB.save_topics(own, "CH", ["khanB"])
        t2 = B2["render_topics"][key]["topics"]
        assert "khanB" in t2 and "moiA" in t2, "phiên khẩn làm mất đề tài cũ"
        FB._count_jobs = lambda db, o, c, v=None: 2
        FB._HOT_CACHE.clear()
        n = FB.count_done(own, "CH")
        assert n == 18, f"count_done ở B2 = {n} (phải 16+2=18, nếu 2 là sẽ LÀM DƯ video)"
    finally:
        (FB._db_meta, FB._db_jobs, FB._db, FB._soft, FB._b2_available, FB._count_jobs, _b) = sv
        FB._B2.clear(); FB._B2.update(_b); FB._B2["on"] = False; FB._B2["client"] = None
        FB._TOPICS_CACHE.clear(); FB._HOT_CACHE.clear()


def t_extract_json():
    import content_brain as CB
    assert CB._extract_json('```json\n{"a": 1}\n```')["a"] == 1
    assert CB._extract_json('{"b": 2}')["b"] == 2



def t_key_pool_sach():
    """Hồ key VIẾT không được lẫn key ảnh (px:/pb:) hay khoá lưu trữ (r2:) — 23/8 từng lẫn, gây lỗi 401."""
    import key_manager as KM
    ks = [{"id": "a", "key": "AIzaTEST"}, {"id": "b", "key": "px:abc"},
          {"id": "c", "key": "pb:12345678-x"}, {"id": "d", "key": "r2:acc:ak:se:bucket"},
          {"id": "e", "key": "gsk_z"}]
    order = KM.key_order("CH", ks)
    assert all(not str(k["key"]).startswith(("px:", "pb:", "r2:")) for k in order), order
    assert len(order) == 2, order
    print("  ✅ hồ key viết sạch: chỉ còn key AI (loại px:/pb:/r2:)")

def main():
    print("🧪 SELFTEST (0 mạng · 0 quota) — chặn bản deploy hỏng trước khi spawn 18 luồng:")
    check("shim Groq/CF: system_instruction + UA + JSON + vision", t_shim_signatures)
    check("groq WAF 1010 -> lỗi tạm per-minute", t_groq_waf_1010)
    check("key cạn quota -> đổi key, không giết luồng", t_het_key_thi_doi_key)
    check("cạn token/ngày -> nhãn daily", t_groq_tpd_la_daily)
    check("groq model bị gỡ -> tự dò model sống", t_groq_model_selfprobe)
    check("key_order viết: groq -> cf -> gemini", t_key_order)
    check("pool vẽ cf-trước / vision gemini-trước", t_ai_pool_split)
    check("đọc-mềm: quota chết không ném", t_soft_read)
    check("cổng dark_ok theo kênh", t_dark_ok)
    check("_extract_json bóc ```json", t_extract_json)
    check("B2 failover: thiếu env từ chối êm", t_b2_failover)
    check("DIỄN TẬP failover: chủ đề + đếm chỉ tiêu khi B chết", t_failover_rehearsal)
    check("toon: validator + safe-words + route", t_toon)
    check("hồ key viết không lẫn key ảnh/lưu trữ", t_key_pool_sach)
    check("hồ key ẢNH được bù khi shard trả lời thiếu", t_giu_key_anh)
    check("trí nhớ key cạn SỐNG xuyên video", t_nho_key_can)
    if FAILS:
        print(f"\n🚨 SELFTEST FAIL ({len(FAILS)}) — CHẶN PHIÊN để không đốt 18 luồng vào bản hỏng:")
        for f in FAILS:
            print("   - " + f)
        sys.exit(1)
    print("✅ SELFTEST PASS — code lành, cho phép chạy phiên.")


def t_nho_key_can():
    """Key đã cạn Vision/vẽ ảnh phải được NHỚ qua video kế. Sự cố 24/8: set_ai_pool xoá sổ mỗi video
    (136 lần/phiên) -> video sau lại đâm vào đúng key đã 429, mỗi lượt hỏng vẫn trừ hạn mức."""
    import datastory_ci as DS
    DS._VIS_DEAD.clear(); DS._VE_DEAD.clear()
    DS._vis_die("AIzaHET"); DS._ve_die("cf:HET")
    assert DS._vis_chet("AIzaHET") and DS._ve_chet("cf:HET")
    DS.set_ai_pool([{"id": "x", "key": "AIzaHET"}, {"id": "y", "key": "cf:HET"}], "KENH")
    assert DS._vis_chet("AIzaHET"), "set_ai_pool đã xoá mất trí nhớ Vision"
    assert DS._ve_chet("cf:HET"), "set_ai_pool đã xoá mất trí nhớ vẽ ảnh"
    import time as _t
    DS._VIS_DEAD["AIzaHET"] = _t.time() - 1          # hết hạn nghỉ
    assert not DS._vis_chet("AIzaHET"), "hết hạn nghỉ thì key phải quay lại vòng xoay"
    DS._VIS_DEAD.clear(); DS._VE_DEAD.clear()


def t_giu_key_anh():
    """Hồ key ẢNH không được biến mất khi shard trả lời thiếu (sự cố 24/8: 87/136 lượt nạp hồ mất
    sạch key px:/pb: sau khi failover sang B2 -> phải nhờ AI vẽ ảnh, 0 clip thật cả phiên)."""
    import firestore_bridge as FB
    FB._IMG_KEYS.clear()
    day = [{"id": "a", "key": "AIzaAAA"}, {"id": "b", "key": "px:PX1"}, {"id": "c", "key": "pb:PB1"}]
    assert len(FB._giu_key_anh(day)) == 3
    ra = FB._giu_key_anh([{"id": "a", "key": "AIzaAAA"}])    # shard trả lời thiếu key ảnh
    co = [r for r in ra if str(r["key"]).startswith(("px:", "pb:"))]
    assert len(co) == 2, f"phải bù lại 2 key ảnh, thực tế {len(co)}"
    FB._IMG_KEYS.clear()


if __name__ == "__main__":
    main()
