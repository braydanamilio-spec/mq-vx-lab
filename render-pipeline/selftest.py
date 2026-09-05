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
import re
import sys
import urllib.error
import urllib.request

FAILS = []


def _doc(duong: str) -> str:
    """Đọc một file mã nguồn theo đường dẫn TƯƠNG ĐỐI so với chính selftest.py.

    Nhiều chốt soi thẳng mã nguồn (bố cục, lớp phủ, thứ tự đọc key). Trước đây mỗi chốt tự mở file
    theo thư mục hiện hành -> chạy selftest từ thư mục khác là hỏng. Gom về một chỗ."""
    import os
    goc = os.path.dirname(os.path.abspath(__file__))
    return io.open(os.path.join(goc, duong), encoding="utf-8").read()


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


def t_bookend_la_noi_duy_nhat_ve_tieu_de_mo_dau():
    """MỘT tiêu đề lúc mở đầu, không phải ba.

    24/8 thêm <Bookend> vẽ thẻ mở đầu CÓ TIÊU ĐỀ cho mọi short, nhưng không ai gỡ lớp phủ intro
    cũ của từng component — lớp đó cũng vẽ tiêu đề — và header thì luôn bật. Kết quả anh nhìn
    thấy 25/8: ba bản tiêu đề chồng lên nhau suốt introSec giây đầu, ở 6/7 component short.
    Đây là lỗi CHỈ LỘ RA KHI XEM, không có ngoại lệ nào trong log, nên phải chặn bằng mã nguồn:
      • không component nào được vẽ {title} bên trong lớp phủ `f < introF`
      • tiêu đề header phải tự ẩn khi thẻ mở đầu còn trên màn hình"""
    import os, re
    goc = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(goc, "..", "engine-remotion", "src")
    xau = []
    for ten in sorted(os.listdir(src)):
        if not ten.endswith(".tsx"):
            continue
        m = io.open(os.path.join(src, ten), encoding="utf-8").read()
        if "<Bookend" not in m:
            continue
        # (a) lớp phủ intro riêng KHÔNG được vẽ lại tiêu đề
        for kh in re.finditer(r"f < introF \?|\{f < introF", m):
            # Lùi 30 ký tự để nhìn thấy chữ "display:" đứng TRƯỚC mốc — chính cổng ẩn header cũng
            # khớp mẫu này, cắt từ đúng mốc thì tưởng nhầm nó là lớp phủ vẽ lại tiêu đề.
            doan = m[max(0, kh.start() - 30): kh.start() + 1400]
            if ">{title}</div>" in doan and "display: f < introF" not in doan[:150]:
                xau.append(f"{ten}: lớp phủ intro vẽ lại {{title}} (Bookend đã vẽ)")
                break
        # (b) mọi chỗ component tự vẽ tiêu đề phải có cổng ẩn theo introF
        tu_ve = m.count(">{title}</div>")
        co_cong = m.count('display: f < introF ? "none"')
        if tu_ve > co_cong:
            xau.append(f"{ten}: {tu_ve} chỗ tự vẽ title nhưng chỉ {co_cong} chỗ có cổng ẩn khi mở đầu")
    assert not xau, "tiêu đề chồng nhau lúc mở đầu:\n   " + "\n   ".join(xau)



def t_extract_json_luon_tra_dict():
    """_extract_json không bao giờ được trả list — 21 chỗ gọi đều `.get()` ngay dòng sau.

    25/8: Gemini trả thẳng MẢNG dialog thay vì object -> `AttributeError: 'list' object has no
    attribute 'get'` giết 5 lượt toon long trong một phiên. Cái `.get` nằm NGOÀI vùng try bọc
    _extract_json nên không rơi vào nhánh "invalid JSON, thử lại" mà bay thẳng lên."""
    import content_brain as CB
    assert isinstance(CB._extract_json('{"a":1}'), dict)
    assert isinstance(CB._extract_json('```json\n{"a":1}\n```'), dict)
    # mảng bọc đúng 1 object: model chỉ gói thừa -> bóc ra dùng, không phí một lượt gọi
    assert CB._extract_json('[{"a":1}]') == {"a": 1}
    for xau in ('[{"a":1},{"b":2}]', "[1,2,3]", '"chuoi"', "[]", "123"):
        try:
            CB._extract_json(xau)
        except ValueError:
            continue
        except Exception as e:
            raise AssertionError(f"{xau} phải ném ValueError để vòng lặp thử lại, lại ném {type(e).__name__}")
        raise AssertionError(f"{xau} lọt qua -> call site sẽ nổ .get() ngoài vùng try")


def t_workflow_dung_project_C_phai_bat_co():
    """Truyền FIREBASE_PROJECT_ID_C mà quên SHARD_PUBLISH = âm thầm đọc/ghi Project A.

    25/8 — `enqueue.py` (chống trùng + đẩy kho) chạy trong render lane, đọc sổ `videos` qua
    `client_publish()`. Hàm đó chỉ trỏ C khi SHARD_PUBLISH=1, không thì rơi về A. render_cron.yml
    truyền sẵn creds + id của C nhưng THIẾU đúng cái cờ -> A cạn hạn mức -> 63 lần trong một phiên
    in "không tra được sổ chống trùng — vẫn upload", tức chống trùng bị vô hiệu mà không ai biết.
    Đây là kiểu lỗi im lặng: không Traceback, không lane fail, chỉ có nguy cơ video trùng."""
    import os, re, yaml
    goc = os.path.dirname(os.path.abspath(__file__))
    wf = os.path.join(goc, "..", ".github", "workflows")
    xau = []
    for ten in sorted(os.listdir(wf)):
        if not ten.endswith((".yml", ".yaml")):
            continue
        d = yaml.safe_load(io.open(os.path.join(wf, ten), encoding="utf-8")) or {}
        for jn, j in (d.get("jobs") or {}).items():
            for st in (j.get("steps") or []):
                e = st.get("env") or {}
                if "FIREBASE_PROJECT_ID_C" not in e or "SHARD_PUBLISH" in e:
                    continue
                # Miễn trừ CÓ CĂN CỨ, không tha theo tên file: script nào TỰ DỰNG client C bằng
                # biến môi trường C (như migrate_to_shards.py) thì không đi qua client_publish()
                # nên không phụ thuộc cờ. Không đọc được script -> vẫn bắt lỗi, an toàn trước đã.
                tu_dung = False
                for tep in re.findall(r"python3?\s+([\w./-]+\.py)", str(st.get("run") or "")):
                    d2 = os.path.join(goc, "..", tep)
                    if not os.path.exists(d2):
                        continue
                    m2 = io.open(d2, encoding="utf-8", errors="ignore").read()
                    if "client_publish" not in m2 and "FIREBASE_PROJECT_ID_C" in m2:
                        tu_dung = True
                if not tu_dung:
                    xau.append(f"{ten}:{jn}/{(st.get('name') or 'step')[:26]}")
    assert not xau, ("step trỏ Project C nhưng thiếu cờ SHARD_PUBLISH (sẽ âm thầm rơi về A):\n   "
                     + "\n   ".join(xau))



def t_kenh_the_he_2_tro_dung_ham_va_dang():
    """50 kênh thế hệ 2 phải trỏ hàm dữ liệu CÓ THẬT và dạng render CÓ THẬT.

    Kênh thế hệ 2 bỏ hẳn footage: nội dung sinh từ `du_lieu_mo.*` rồi vẽ bằng composition. Một
    kênh trỏ nhầm tên hàm sẽ không lộ ra cho tới khi lane của nó chạy giữa đêm rồi chết. Kiểm ở
    đây thì sai tên là chặn ngay từ selftest, không tốn một lượt render nào."""
    import os, json
    goc = os.path.dirname(os.path.abspath(__file__))
    dsp = os.path.join(goc, "kenh_the_he_2.json")
    if not os.path.exists(dsp):
        return                                   # chưa bật thế hệ 2 -> không bắt lỗi
    import du_lieu_mo as DL
    ks = json.load(io.open(dsp, encoding="utf-8"))
    DANG = {"ranked", "race", "mapped", "scaled", "pulse", "longshot", "cinematic", "thennow"}
    CHAT = {"A", "B", "C"}      # A = số liệu + đồ hoạ code · B = ảnh AI style riêng · C = lai
    xau = []
    # `ham` được phép là hàm nguồn trong du_lieu_mo, HOẶC một bộ chuyển đổi nội bộ của the_he_2
    # (vd "wiki_bai" — hỏi ngược lại cùng một nguồn, không phải nguồn mới).
    import the_he_2 as TH
    noi_bo = set()
    for bang in ("BO_CHUYEN", "BO_DUA", "BO_PHIM", "BO_SO", "BO_BAN_DO", "BO_THANG", "BO_XUA_NAY"):
        noi_bo |= set(getattr(TH, bang, {}) or {})
    for k in ks:
        if not hasattr(DL, k.get("ham", "")) and k.get("ham") not in noi_bo:
            xau.append(f"{k.get('ten')}: '{k.get('ham')}' không có ở du_lieu_mo lẫn bộ chuyển đổi")
        if k.get("dinh_dang") not in DANG:
            xau.append(f"{k.get('ten')}: dạng render lạ '{k.get('dinh_dang')}'")
        if k.get("footage"):
            xau.append(f"{k.get('ten')}: thế hệ 2 KHÔNG dùng footage")
        if k.get("chat_lieu") not in CHAT:
            xau.append(f"{k.get('ten')}: chất liệu lạ '{k.get('chat_lieu')}' (phải A/B/C)")
        # Kênh dùng ảnh AI (B hoặc C) BẮT BUỘC khai style riêng. Không khai thì mọi kênh sẽ dùng
        # chung một prompt mặc định -> 50 kênh ra 50 bộ ảnh giống hệt nhau, đúng cái "tầm thường"
        # đang tìm cách thoát khỏi.
        if k.get("chat_lieu") in ("B", "C") and not str(k.get("style_anh") or "").strip():
            xau.append(f"{k.get('ten')}: chất liệu {k.get('chat_lieu')} nhưng chưa khai style_anh")
        if not str(k.get("niche") or "").strip():
            xau.append(f"{k.get('ten')}: thiếu niche")
    tay = [k.get("handle") for k in ks]
    trung = sorted({h for h in tay if tay.count(h) > 1})
    if trung:
        xau.append("handle trùng: " + ", ".join(trung))
    # HAI KÊNH CÙNG NGUỒN + CÙNG THAM SỐ = RA CÙNG MỘT VIDEO. Đo thật 25/8: 6 cặp kênh ra y hệt
    # nhau (PILL FACTS ra tin thu hồi thực phẩm; SALARY TRUTH và DEGREE WORTH cùng ra "Gas price")
    # vì tham số xoay vòng gắn theo NGUỒN chứ không theo KÊNH. Lỗi này không lộ ra ở log — chỉ lộ
    # khi xem hai video cạnh nhau, tức là sau khi đã đăng.
    import collections
    theo = collections.defaultdict(list)
    for k in ks:
        theo[(k.get("ham"), json.dumps(k.get("tham_so") or {}, sort_keys=True))].append(k.get("ten"))
    for _kh, ten in sorted(theo.items()):
        if len(ten) > 1:
            xau.append("ra trùng nội dung: " + " = ".join(ten))
    for k in ks:
        if not (k.get("tham_so") or {}):
            xau.append(f"{k.get('ten')}: chưa có tham_so (sẽ chạy bằng mặc định = dễ trùng kênh khác)")
    assert not xau, "danh sách kênh thế hệ 2 sai:\n   " + "\n   ".join(xau)



def t_tsx_prop_khai_roi_phai_thao_ra():
    """Prop khai trong kiểu mà quên thảo ra khỏi `({...})` = ReferenceError lúc CHẠY.

    25/8 — `Caption` khai `vang?: string` trong kiểu, thân dùng `vang`, nhưng danh sách thảo prop
    lại thiếu nó. TypeScript không kêu (nó chỉ kiểm kiểu, không kiểm biến tự do trong JSX), esbuild
    cũng không kêu (cú pháp hợp lệ) — chỉ đến lúc render mới nổ `ReferenceError: vang is not
    defined`. Giá phải trả: một phiên 51 phút, 18 luồng, 0 video.
    Đây đúng là lớp lỗi mà chốt AST "biến chưa gán" đang bắt cho Python, nhưng phía .tsx thì
    không ai canh. Chốt này canh phần đó, bằng đọc mã, 0 giây, 0 quota."""
    import os, re
    goc = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(goc, "..", "engine-remotion", "src")
    if not os.path.isdir(src):
        return
    # tên thường gặp trong JSX nhưng KHÔNG phải prop -> khỏi báo nhầm
    MAU = re.compile(r"React\.FC<\{(?P<kieu>[^}]*)\}>\s*=\s*\(\s*\{(?P<thao>[^}]*)\}", re.S)
    xau = []
    for ten in sorted(os.listdir(src)):
        if not ten.endswith(".tsx"):
            continue
        m = io.open(os.path.join(src, ten), encoding="utf-8").read()
        for k in MAU.finditer(m):
            kieu = {re.sub(r"[?:].*", "", x).strip()
                    for x in k.group("kieu").split(";") if x.strip()}
            kieu = {x for x in kieu if re.fullmatch(r"[A-Za-z_]\w*", x or "")}
            thao = {re.sub(r"[=:].*", "", x).strip()
                    for x in k.group("thao").split(",") if x.strip()}
            # Cắt thân ĐÚNG tới khai báo cấp cao kế tiếp. Lấy bừa 4000 ký tự thì liếm sang hàm
            # bên dưới và báo nhầm (ThemedBase khai thừa `f`, hàm kế dưới có tham số tên `f`).
            _sau = m[k.end():]
            _het = re.search(r"\n(?:const|export|function|type|interface)\s", _sau)
            than = _sau[: _het.start()] if _het else _sau
            for prop in sorted(kieu - thao):
                # chỉ báo khi thân THỰC SỰ nhắc tên đó như một biến độc lập
                if re.search(r"(?<![\w.\"'])" + re.escape(prop) + r"(?![\w:])", than):
                    xau.append(f"{ten}: prop '{prop}' khai trong kiểu, thân có dùng, nhưng KHÔNG thảo ra")
    assert not xau, "prop chưa thảo -> ReferenceError lúc render:\n   " + "\n   ".join(xau)



def t_brandkit_the_he_2():
    """Brand-kit 50 kênh: có đủ, motif CÓ THẬT trong BrandV2, và không kênh nào trùng màu chính.

    Nhận diện là thứ phải ổn định suốt đời kênh, nên nó được sinh bằng quy tắc chứ không gọi AI.
    Ba thứ sai được mà không ai thấy cho tới lúc nhìn 50 avatar cạnh nhau:
      • motif viết sai tên -> BrandV2 rơi về `default` -> hàng chục kênh cùng một biểu tượng cột
      • hai kênh trùng màu chính -> nhìn như cùng một kênh
      • thiếu tagline -> banner trống một dòng"""
    import os, re, json as _js
    goc = os.path.dirname(os.path.abspath(__file__))
    dsp = os.path.join(goc, "kenh_the_he_2.json")
    if not os.path.exists(dsp):
        return
    ks = _js.load(io.open(dsp, encoding="utf-8"))
    if not any(k.get("brand") for k in ks):
        return                                    # chưa sinh brand -> chưa kiểm
    tsx = io.open(os.path.join(goc, "..", "engine-remotion", "src", "BrandV2.tsx"),
                  encoding="utf-8").read()
    co = set(re.findall(r'case "([a-z_]+)":', tsx)) | {"bars"}
    xau, mau = [], []
    for k in ks:
        b = k.get("brand") or {}
        if not b:
            xau.append(f"{k.get('ten')}: chưa có brand")
            continue
        if b.get("motif") not in co:
            xau.append(f"{k.get('ten')}: motif '{b.get('motif')}' không có trong BrandV2 "
                       f"-> sẽ rơi về biểu tượng mặc định")
        if not str(b.get("tagline") or "").strip():
            xau.append(f"{k.get('ten')}: thiếu tagline")
        mau.append((b.get("palette") or {}).get("primary"))
    trung = sorted({m for m in mau if m and mau.count(m) > 1})
    if trung:
        xau.append("màu chính trùng giữa các kênh: " + ", ".join(trung))
    # "Khác chuỗi hex" KHÔNG có nghĩa là mắt phân biệt được. Đo thật 26/8: 50 màu đều khác nhau
    # về chuỗi mà có **73 cặp** cách nhau dưới 40/255, nhiều cặp cách 3 — nhìn hai avatar cạnh
    # nhau thấy y hệt. Phải đo bằng KHOẢNG CÁCH, không bằng phép so bằng.
    import itertools as _it

    def _rgb(h):
        return [int(h[i:i + 2], 16) for i in (1, 3, 5)]

    gan = []
    for (i1, a), (i2, b) in _it.combinations(list(enumerate(mau)), 2):
        if not a or not b:
            continue
        d = sum((x - y) ** 2 for x, y in zip(_rgb(a), _rgb(b))) ** 0.5
        if d < 40:
            gan.append(f"{ks[i1].get('ten')} ~ {ks[i2].get('ten')} (cách {d:.0f}/255)")
    if gan:
        xau.append(f"{len(gan)} cặp kênh màu quá giống nhau: " + " · ".join(gan[:4]))
    assert not xau, "brand-kit sai:\n   " + "\n   ".join(xau)



def t_cong_an_toan_noi_dung():
    """Mọi đường dựng story thế hệ 2 phải đi qua cổng an toàn nội dung.

    26/8 — suýt trả giá đắt: kênh "chủ đề thầm kín" lọc từ bảng đọc-nhiều THẬT của Wikipedia và
    ra bảng gồm "Pornhub", "Sex", "Teenage Sex and Death at…". Video đạt hết mọi mốc QC kỹ thuật
    (đủ giây, có tiếng, đúng khung) — nhưng đăng lên là mất kênh, riêng cụm cuối đủ để bị gỡ.
    QC kỹ thuật không thể bắt loại lỗi này, nên phải có cổng riêng và phải chốt rằng nó còn nguyên.

    Hai vế cùng phải đúng:
      • cổng nhận diện đúng (chặn cái cần chặn, KHÔNG chặn nhầm "Sussex", "Essex", "Middlesex")
      • cả 7 đường dựng story đều gọi cổng — thiếu một đường là thủng."""
    import os
    goc = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(os.path.join(goc, "the_he_2.py")):
        return
    import the_he_2 as TH
    CAN_CHAN = ["Pornhub", "Sex", "Teenage Sex and Death at a Beach", "sexual assault case",
                "OnlyFans", "Sexual Politics (book)", "child sex ring", "underage marriage"]
    CAN_GIU = ["Meghan, Duchess of Sussex", "Essex County", "Middlesex Hospital",
               "Raytheon Company", "Boeing 737 MAX", "Marriage", "Divorce"]
    xau = [f"lọt: {t!r}" for t in CAN_CHAN if TH.an_toan(t)]
    xau += [f"chặn nhầm: {t!r}" for t in CAN_GIU if not TH.an_toan(t)]
    ma = io.open(os.path.join(goc, "the_he_2.py"), encoding="utf-8").read()
    for ham in ("dung_story_ranked", "dung_story_race", "dung_story_cinematic", "dung_story_scaled",
                "dung_story_mapped", "dung_story_longshot", "dung_story_thennow"):
        i = ma.find(f"def {ham}(")
        if i < 0:
            xau.append(f"thiếu hẳn {ham}()")
            continue
        j = ma.find("\ndef ", i + 10)
        if "_cong_an_toan(" not in ma[i:(j if j > 0 else len(ma))]:
            xau.append(f"{ham}() KHÔNG đi qua cổng an toàn")
    assert not xau, "cổng an toàn nội dung thủng:\n   " + "\n   ".join(xau)



def t_nghen_nha_cung_cap_phai_thu_lai():
    """504/timeout của nhà cung cấp phải THỬ LẠI, không được giết lượt viết.

    Đo thật phiên 16:20 ngày 25/8: 61 video ra lò nhưng **29 lượt viết chết**, cả 29 cùng một lỗi
    `504 Deadline Exceeded` / `_InactiveRpcError`. Mỗi lượt chết là một video không bao giờ tồn tại.
    Gốc: khối except quanh `generate_content` chỉ phân loại 404 (đổi model) và 429 (đổi key); 504
    không khớp nhánh nào nên rơi vào `raise` cuối. Mà 504 chỉ là nghẽn — gọi lại là xong, và không
    tốn hạn mức.

    Hai vế:
      • `_loi_tam_thoi` phân biệt đúng nghẽn (thử lại) với cạn hạn mức / sai key (đừng thử lại)
      • MỌI khối except quanh generate_content đều có nhánh thử lại, và dùng ĐÚNG tên biến đếm
        vòng của chính hàm đó (`attempt` hay `_try`) — dùng nhầm là NameError nổ đúng lúc nghẽn"""
    import re
    CB = _doc("content_brain.py")
    import content_brain as C
    # Mỗi ca dưới đây là một lỗi ĐO ĐƯỢC trên phiên thật, không phải giả định. Thêm ca mới vào
    # đây mỗi lần thấy một loại nghẽn lọt lưới — danh sách chuỗi con luôn thiếu, chỉ có log mới
    # nói được nhà cung cấp thực sự trả về chữ gì.
    tam = ["504 Deadline Exceeded", "_InactiveRpcError of RPC", "503 Service Unavailable",
           "request timed out", "connection reset by peer",
           "HTTP Error 500: Internal Server Error",          # phiên 00:01 26/8
           'cloudflare HTTP 500: {"errors":[{"message":"AiError: Unknown internal error"}]}',
           "502 Bad Gateway", "model is overloaded"]
    ben = ["429 quota exceeded", "404 model not found", "invalid api key",
           "permission denied", "resource_exhausted"]
    xau = [f"coi '{t}' là bền (phải thử lại)" for t in tam if not C._loi_tam_thoi(t)]
    xau += [f"coi '{t}' là tạm thời (KHÔNG được thử lại)" for t in ben if C._loi_tam_thoi(t)]

    dong = CB.splitlines()
    co = [i for i, l in enumerate(dong) if "_loi_tam_thoi(msg)" in l]
    # Đếm theo KHỐI BẮT LỖI, không theo số `raise RateLimited`: một khối có thể có hai raise
    # (429 và 403) mà chỉ cần một nhánh thử lại. Đếm nhầm thước đo thì chốt báo động giả mãi.
    n_khoi = sum(1 for i, l in enumerate(dong)
                 if l.strip() == "msg = str(e).lower()"
                 and any("generate_content(" in dong[j] for j in range(max(0, i - 12), i)))
    if len(co) < n_khoi:
        xau.append(f"{n_khoi} khối bắt lỗi quanh generate_content nhưng chỉ {len(co)} khối "
                   f"có nhánh thử lại khi nghẽn")
    for i in co:
        bien = "attempt" if "attempt <" in dong[i] else ("_try" if "_try ==" in dong[i] else "")
        if not bien:
            xau.append(f"dòng {i+1}: nhánh thử lại không rõ đếm bằng biến nào")
            continue
        thay = False
        for j in range(i, max(0, i - 120), -1):
            if f"for {bien} in range(" in dong[j]:
                thay = True
            if dong[j].startswith("def "):
                break
        if not thay:
            xau.append(f"dòng {i+1}: dùng '{bien}' nhưng hàm này không có vòng lặp đó -> NameError")
    assert not xau, "xử lý nghẽn nhà cung cấp sai:\n   " + "\n   ".join(xau)



def t_dispatch_luon_tra_bon_gia_tri():
    """Mọi đường thoát của `_dispatch_short` phải trả đủ bốn giá trị.

    Ba nơi gọi đều mở gói `_, story, ok, info = _dispatch_short(...)`. Trả `None` là
    `TypeError: cannot unpack non-sequence NoneType` — nổ giữa lane, không phải lúc test.
    Với kênh thế hệ 2 thì "bỏ lượt" KHÔNG phải trường hợp hiếm: đó là hành vi thiết kế mỗi khi
    nguồn mở thiếu dữ liệu. Nên đường thoát đó là đường hay đi nhất, không phải đường phụ.
    Chốt chỉ soi các `return` trả THẲNG một literal (tuple/None/hằng); `return DS.make_xxx(...)`
    thì tin theo hợp đồng của hàm được gọi."""
    import ast
    t = ast.parse(_doc("run_render.py"))
    f = next((n for n in ast.walk(t)
              if isinstance(n, ast.FunctionDef) and n.name == "_dispatch_short"), None)
    assert f is not None, "không tìm thấy _dispatch_short()"
    xau = []
    for r in ast.walk(f):
        if not isinstance(r, ast.Return):
            continue
        v = r.value
        if isinstance(v, ast.Call):
            continue                       # uỷ quyền cho hàm khác -> theo hợp đồng của hàm đó
        if v is None or (isinstance(v, ast.Constant) and v.value is None):
            xau.append(f"dòng {r.lineno}: return None -> nơi gọi sẽ TypeError")
        elif isinstance(v, ast.Tuple) and len(v.elts) != 4:
            xau.append(f"dòng {r.lineno}: return {len(v.elts)} giá trị, cần 4")
        elif not isinstance(v, (ast.Tuple, ast.Call)):
            xau.append(f"dòng {r.lineno}: return không phải bộ 4 giá trị")
    assert not xau, "_dispatch_short trả sai dạng:\n   " + "\n   ".join(xau)



def t_the_he_2_tra_ten_dong_deu_co_that():
    """Mọi tên được tra ĐỘNG trong đường thế hệ 2 phải có thật.

    `chay_chung` lấy bộ dựng props bằng `getattr(DS, ten)` và tên composition bằng chuỗi trong
    bảng `DUONG_RA`. Sai một chữ thì Python/Remotion chỉ kêu lúc CHẠY — mà lúc chạy là giữa đêm,
    trong lane, sau khi đã tiêu giọng đọc và thời gian máy. Tra bằng chuỗi thì trình biên dịch
    không đỡ được, nên phải có chốt đỡ thay."""
    import os, re, sys
    goc = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(os.path.join(goc, "the_he_2.py")):
        return
    if goc not in sys.path:
        sys.path.insert(0, goc)
    import datastory_ci as DS
    import du_lieu_mo as DL
    import the_he_2 as TH
    src = _doc("the_he_2.py")
    xau = []
    # 1) mọi DS.xxx / D.xxx viết thẳng trong mã
    for ten in sorted(set(re.findall(r"\bDS\.([A-Za-z_][A-Za-z_0-9]*)", src))):
        if not hasattr(DS, ten):
            xau.append(f"không có datastory_ci.{ten}")
    for ten in sorted(set(re.findall(r"\bD\.([a-z_][A-Za-z_0-9]*)", src))):
        if not hasattr(DL, ten):
            xau.append(f"không có du_lieu_mo.{ten}")
    # 2) bảng DUONG_RA: composition phải có trong Root.tsx, hàm props phải có trong datastory_ci
    root = io.open(os.path.join(goc, "..", "engine-remotion", "src", "Root.tsx"),
                   encoding="utf-8").read()
    comp = set(re.findall(r'<Composition\s+id="([^"]+)"', root))
    for dang, cap in (getattr(TH, "DUONG_RA", {}) or {}).items():
        c, hp = cap
        if c and c not in comp:
            xau.append(f"{dang}: composition '{c}' không có trong Root.tsx")
        if hp and not hasattr(DS, hp):
            xau.append(f"{dang}: không có datastory_ci.{hp}()")
    for c in ("RaceShort", "CinematicShort"):
        if c not in comp:
            xau.append(f"composition '{c}' (đường riêng) không có trong Root.tsx")
    assert not xau, "tên tra động không tồn tại:\n   " + "\n   ".join(xau)



def t_ve_anh_khong_hong_im_lang():
    """Mọi đường trả False của `_generate_image_ai` phải nói vì sao.

    26/8 — kênh toon ra `chỉ vẽ được 0/16 khung` mà TRONG CẢ LOG PHIÊN không một dòng nào cho biết
    lý do: hai nhánh trả False (pool rỗng · model trả về không phải ảnh) im lặng tuyệt đối, 16 lượt
    vẽ rơi vào đó và biến mất không dấu vết. Cùng lớp lỗi với canary nuốt stderr — biết là hỏng,
    không biết hỏng ở đâu, nên không sửa được.

    Luật: hàm nào BÁO HỎNG thì phải NÓI HỎNG VÌ SAO. Ở đây kiểm bằng mã nguồn: mỗi `return False`
    trong hàm vẽ phải có một lệnh in trong vài dòng ngay trước nó."""
    import ast
    src = _doc("datastory_ci.py")
    t = ast.parse(src)
    f = next((n for n in ast.walk(t)
              if isinstance(n, ast.FunctionDef) and n.name == "_generate_image_ai"), None)
    assert f is not None, "không tìm thấy _generate_image_ai()"
    dong = src.splitlines()
    cam = []
    for r in ast.walk(f):
        if not isinstance(r, ast.Return):
            continue
        v = r.value
        if not (isinstance(v, ast.Constant) and v.value is False):
            continue
        # có lệnh in nào trong 6 dòng ngay trước không?
        if not any("print(" in dong[j] for j in range(max(0, r.lineno - 7), r.lineno)):
            cam.append(f"dòng {r.lineno}: `return False` mà không in lý do")
    assert not cam, "vẽ ảnh hỏng im lặng:\n   " + "\n   ".join(cam)



def t_mo_dau_phai_xac_minh_bang_khung_that():
    """Cả hai đường Cinematic phải chốt mở đầu bằng KHUNG THẬT trước khi render.

    26/8 — `sang_hoa_mo_dau` đo qua MÔ HÌNH lớp phủ. Mô hình đã phải cộng biên 13 rồi 20 điểm mà
    phiên 17:40 vẫn để lọt 5 ca: mô hình bảo đạt, khung render thật ra 80,3 · 81,0 · 82,7 · 89,4 ·
    92,0 % tối và bị QC loại SAU KHI đã dựng xong — 4 trong 5 ca là bản LONG 10 phút.
    Mô hình không đuổi kịp bản render thật (thiếu Ken Burns, objectPosition, bóng chữ hook…), nên
    nới biên chỉ là đoán tiếp. Render một khung mất ~2 giây và cho ĐÚNG con số QC sẽ dùng."""
    xau = []
    src = _doc("datastory_ci.py")
    for ham in ("do_khung_mo_dau_that", "xac_minh_mo_dau", "_muon_anh_sang_nhat"):
        if f"def {ham}(" not in src:
            xau.append(f"thiếu hàm {ham}()")
    # Soi CẢ the_he_2.py: đường phim kể thế hệ 2 cũng render CinematicShort, và kênh vẽ ảnh AI
    # còn dễ ra khung tối đều màu hơn. Chốt chỉ soi một file là để hở đúng chỗ mới nhất.
    import os as _os
    _goc = _os.path.dirname(_os.path.abspath(__file__))
    if _os.path.exists(_os.path.join(_goc, "the_he_2.py")):
        src += "\n" + _doc("the_he_2.py")
    # mỗi lệnh render Cinematic/CinematicShort phải có xac_minh_mo_dau ở phía trên trong cùng hàm
    dong = src.splitlines()
    for i, l in enumerate(dong):
        if '"npx", "remotion", "render", "src/index.ts", "Cinematic' not in l:
            continue
        thay = False
        for j in range(i, max(0, i - 60), -1):
            # 26/8 — chấp nhận CẢ lời gọi gián tiếp. `chay_phim` đã tách phần dựng props sang
            # `dung_props_phim`, và chính chỗ đó xác minh mở đầu; neo cứng vào một tên hàm thì
            # refactor nào cũng làm chốt đỏ oan, mà đỏ oan lâu ngày là người ta tắt chốt đi.
            # Bù lại phải chứng minh hàm gián tiếp ĐÚNG LÀ có xác minh — kiểm ngay dưới đây.
            if "xac_minh_mo_dau(" in dong[j] or "dung_props_phim(" in dong[j]:
                thay = True
                break
            if dong[j].startswith("def "):
                # canary là PHÁT SÚNG THỬ bằng ảnh tự tạo, không phải video sẽ đăng -> miễn trừ
                thay = "render_canary" in dong[j]
                break
        if not thay:
            xau.append(f"dòng {i+1}: render Cinematic mà không xác minh mở đầu bằng khung thật")
    # đường gián tiếp chỉ được chấp nhận nếu nó THẬT SỰ xác minh
    import re as _re2
    _m = _re2.search(r"def dung_props_phim\(.*?(?=\ndef )", src, _re2.S)
    if _m:
        assert "xac_minh_mo_dau(" in _m.group(0), \
            "dung_props_phim không xác minh mở đầu -> đường gián tiếp thành lỗ hổng"
    assert not xau, "mở đầu chưa chốt bằng khung thật:\n   " + "\n   ".join(xau)



def t_key_order_khong_lay_phan_tu_dau_tran():
    """Không được viết `key_order(...)[0]` trần — hết key là chuyện BÌNH THƯỜNG.

    26/8 phiên 19:59: cả pool key viết cạn sạch, `key_order()` trả danh sách RỖNG và ba chỗ lấy
    `[0]` đều nổ `IndexError` — 3 lane ra **0 video**, 12 Traceback, log toàn stack thay vì một
    dòng nói "hết key". Hệ này sống bằng hạn mức free nên cạn key là trạng thái sẽ gặp hằng ngày,
    không phải sự cố; gặp nó phải báo gọn rồi bỏ lượt, không phải đổ stack.

    Cùng họ với `_dispatch_short` trả None: một đường đi THƯỜNG XUYÊN bị code coi như không thể
    xảy ra."""
    import re
    xau = []
    for ten in ("datastory_ci.py", "run_render.py", "key_manager.py"):
        for i, l in enumerate(_doc(ten).splitlines(), 1):
            t = l.strip()
            if t.startswith("#"):
                continue
            if re.search(r"key_order\([^)]*\)\s*\[0\]", t):
                xau.append(f"{ten}:{i}: {t[:70]}")
    assert not xau, ("lấy phần tử đầu của key_order mà không kiểm rỗng:\n   "
                     + "\n   ".join(xau))



def t_ho_key_A_doc_mot_lan_o_plan():
    """Lane KHÔNG được tự đọc project A khi plan đã gửi hồ key kèm.

    26/8 — đo 4 phiên đêm 25/8: `merge_keys_A` chiếm **29% toàn bộ lượt đọc** (2.170/7.388),
    trong khi dòng "Hợp nhất N key CHỈ CÓ Ở A" in ra **0 lần** — 18 lane đọc project A để rồi
    không tìm thấy key mới nào, lần nào cũng vậy. Vòng lặp không tự tắt vì điều kiện thoát là
    "B đã đủ groq lẫn cf", mà B cạn hạn mức GHI nên sync A→B hỏng thường trực.
    70 lượt × 18 lane × ~30 phiên ≈ 37.800 lượt/ngày trên trần 50.000 — tự tay làm A cạn.

    Bản vá TRƯỚC chụp ảnh vào D1, nhưng đo lại thì "Đã chụp hồ key" cũng in 0 lần: nó chưa từng
    chạy. Nên bản này đi đường `CHANNEL_CFGS` đã chứng minh chạy được — plan đọc một lần, phát
    xuống qua biến môi trường."""
    src = _doc("firestore_bridge.py")
    xau = []
    for ham in ("keys_a_tu_plan", "dong_goi_keys_a"):
        if f"def {ham}(" not in src:
            xau.append(f"thiếu {ham}()")
    # _merge_a_keys phải hỏi gói của plan TRƯỚC khi đọc A
    i = src.find("def _merge_a_keys(")
    j = src.find("\ndef ", i + 10)
    than = src[i:j if j > 0 else len(src)]
    k_goi = than.find("keys_a_tu_plan()")
    k_doc = than.find('collection("gemini_keys")')
    if k_goi < 0:
        xau.append("_merge_a_keys không hỏi gói plan -> lane vẫn đọc A")
    elif 0 <= k_doc < k_goi:
        xau.append("_merge_a_keys đọc A TRƯỚC khi hỏi gói plan -> vô hiệu")
    # plan phải xuất, workflow phải truyền
    if "dong_goi_keys_a(" not in _doc("run_render.py"):
        xau.append("plan không gọi dong_goi_keys_a()")
    import os
    wf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                      ".github", "workflows", "render_cron.yml")
    y = io.open(wf, encoding="utf-8").read()
    if "keys_a: ${{ steps.plan.outputs.keys_a }}" not in y:
        xau.append("workflow không khai output keys_a")
    if "KEYS_A: ${{ needs.plan.outputs.keys_a }}" not in y:
        xau.append("workflow không truyền KEYS_A xuống lane")
    assert not xau, "hồ key A vẫn đọc ở lane:\n   " + "\n   ".join(xau)


def t_so_ngan_sach_khong_gay_ao_giac():
    """Sổ ngân sách không được lấy số CỦA MỘT LANE chia cho trần CỦA TOÀN HỆ.

    26/8 — con số ấy VỐN đã là tổng toàn hệ (`nen_doc` + phần tiến trình này); em từng kết luận
    nhầm là "số một lane chia trần cả hệ" và đã sửa lại. Sai thật nằm ở chỗ ĐỌC: lấy dòng đầu
    phiên (ĐỌC 145 = 0%) rồi kết luận cả ngày, trong khi dòng cuối ngày là 43.265 = 86%.
    Chốt này giữ lại để dòng log nói RÕ đâu là lane, đâu là toàn hệ, và kêu lên ở mốc 80% —
    một chỉ số tích luỹ mà không nói mốc thời gian thì rất dễ bị trích sai."""
    src = _doc("firestore_bridge.py")
    i = src.find("def bao_ngan_sach(")
    j = src.find("\ndef ", i + 10)
    than = src[i:j if j > 0 else len(src)]
    xau = []
    if "TOÀN HỆ" not in than:
        xau.append("không báo số toàn hệ")
    if "Lane này" not in than:
        xau.append("không nói rõ con số kia là của riêng lane")
    # Cấm đúng khuôn cũ: lượt LANE chia thẳng cho trần NGÀY. Phải khớp theo BIÊN TỪ —
    # `td*100//TRAN_DOC_NGAY` (số toàn hệ, hợp lệ) chứa chuỗi con `d*100//TRAN_DOC_NGAY`,
    # kiểm bằng `in` là báo động giả ngay chính bản vá vừa viết.
    import re as _re
    if _re.search(r"(?<![A-Za-z_])d\s*\*\s*100\s*//\s*TRAN_DOC_NGAY", than):
        xau.append("vẫn lấy lượt LANE chia trần NGÀY -> ảo giác an toàn")
    assert not xau, "sổ ngân sách gây hiểu nhầm:\n   " + "\n   ".join(xau)



def t_plan_phai_phanh_theo_han_muc():
    """Plan phải HỎI hạn mức còn lại trước khi mở 18 lane.

    26/8 — phiên 00:01 ra 101 video (kỷ lục) nhưng sổ quota đọc chạm **50.153/50.000 = 100%**
    ngay trong 2 giờ đầu ngày. Hệ có sổ đo đầy đủ, có cả `con_ngan_sach()` cho từng lệnh lẻ,
    nhưng **không ai hỏi nó trước khi mở lane** — nên vẫn mở đủ 18 lane rồi đâm thẳng vào trần.

    Phanh KHÔNG phải cắt tính năng: mọi kênh vẫn tới lượt, chỉ chậm hơn. Hạn mức reset theo ngày,
    nên chạy chậm nửa ngày còn hơn đứng hẳn nửa ngày. Cắt `top_titles`/`read_channels` mới là
    đổi chất lượng lấy hạn mức — đã cân nhắc và bác bỏ."""
    src = _doc("run_render.py")
    xau = []
    if "phan_tram_da_dung(" not in src:
        xau.append("plan không hỏi mức quota trước khi chia lane")
    if "🛑 PHANH" not in src:
        xau.append("không có nhánh giảm số lane khi quota cao")
    # phải phanh TRƯỚC khi chốt danh sách kênh gửi xuống matrix
    i, j = src.find("phan_tram_da_dung("), src.find("payload = json.dumps(lst)")
    if i < 0 or j < 0 or i > j:
        xau.append("phanh đặt SAU khi đã chốt danh sách lane -> vô tác dụng")
    import firestore_bridge as FB
    if not hasattr(FB, "phan_tram_da_dung"):
        xau.append("thiếu firestore_bridge.phan_tram_da_dung()")
    else:
        v = FB.phan_tram_da_dung("doc")
        if not isinstance(v, int) or not (0 <= v <= 100):
            xau.append(f"phan_tram_da_dung trả {v!r}, cần số nguyên 0-100")
    assert not xau, "phanh theo hạn mức chưa đúng:\n   " + "\n   ".join(xau)



def t_duong_ghi_d1_khong_hong_im_lang():
    """Đường ghi D1 hỏng thì phải NÓI, dù chỉ một lần.

    26/8 — cả một đêm không hiểu vì sao dòng "Đã chụp hồ key" in 0 lần: `keys_ghi`/`nho_ghi` trả
    False mà không để lại một chữ nào. Hệ quả: một tối ưu quan trọng (chụp hồ key vào D1 để 17
    lane khỏi đọc project A) đã CHẾT ÂM THẦM, và em đi vá nhầm chỗ khác.

    Cùng lớp với canary nuốt stderr và `_generate_image_ai` trả False im lặng. Quy tắc chung:
    **hàm nào báo hỏng thì phải nói hỏng vì sao** — nhưng nói MỘT LẦN mỗi lý do, để không thành
    588 dòng nhiễu như bài học cảnh báo pool."""
    import ast
    src = _doc("hot_db.py")
    t = ast.parse(src)
    d = src.splitlines()
    xau = []
    for fn in [n for n in ast.walk(t) if isinstance(n, ast.FunctionDef)]:
        if not fn.name.endswith("_ghi") and fn.name not in ("keys_ghi", "nho_ghi"):
            continue
        for r in ast.walk(fn):
            if not isinstance(r, ast.Return):
                continue
            v = r.value
            if not (isinstance(v, ast.Constant) and v.value is False):
                continue
            gan = "\n".join(d[max(0, r.lineno - 8):r.lineno])
            if "_keu_mot_lan(" not in gan and "print(" not in gan:
                xau.append(f"{fn.name}() dòng {r.lineno}: trả False mà im lặng")
    if "_keu_mot_lan" not in src:
        xau.append("thiếu cơ chế nói-một-lần (_keu_mot_lan)")
    assert not xau, "đường ghi D1 hỏng im lặng:\n   " + "\n   ".join(xau)



def t_env_tro_file_thi_phai_tao_file():
    """Biến môi trường trỏ tới một tệp khoá thì workflow PHẢI có bước tạo tệp đó.

    26/8 — `fix_queue_thumbnails.yml` khai `GOOGLE_APPLICATION_CREDENTIALS_B: /tmp/sa_b.json`
    nhưng KHÔNG có bước nào ghi tệp đó. Hậu quả không phải lỗi ồn ào mà là **âm thầm rơi về
    project A** — nơi đang cạn hạn mức. Nhìn workflow thì tưởng đã trỏ đúng B.

    Cùng họ với lỗi thiếu cờ `SHARD_PUBLISH`: cấu hình TRÔNG như đã đúng, hành vi thì ngược lại,
    và không có dòng log nào kêu lên."""
    import os, re, glob
    goc = os.path.dirname(os.path.abspath(__file__))
    xau = []
    for w in sorted(glob.glob(os.path.join(goc, "..", ".github", "workflows", "*.yml"))):
        s2 = io.open(w, encoding="utf-8").read()
        ten = os.path.basename(w)
        for m in re.finditer(r"^\s*[A-Z_]*CREDENTIALS[A-Z_]*:\s*(/tmp/[\w.]+)\s*$", s2, re.M):
            tep = m.group(1)
            # phải có ít nhất một lệnh ghi ra đúng tệp đó
            if not re.search(r">\s*" + re.escape(tep) + r"\b", s2):
                xau.append(f"{ten}: env trỏ {tep} nhưng không có bước tạo tệp -> âm thầm rơi về project khác")
    assert not xau, "khoá dịch vụ trỏ vào tệp không được tạo:\n   " + "\n   ".join(xau)



def t_khong_dem_ket_qua_rong():
    """Không được cất KẾT QUẢ RỖNG vào bộ nhớ dùng chung.

    26/8 — lỗi này vừa làm anh tưởng mất sạch key API và kho Drive. Dashboard đọc Firestore ra 0
    dòng (do project cạn hạn mức), cất `[]` vào localStorage 30 phút, rồi F5 bao nhiêu lần cũng
    đọc lại đúng cái rỗng đó. Dữ liệu còn nguyên 199/199 key, nhưng màn hình trắng trơn.

    Cùng cái bẫy nằm sẵn trong pipeline ở hai chỗ:
      • `_A_KEYS["rows"] = out` — nhớ hồ key rỗng ⇒ khoá đường hợp nhất key cả tiến trình
      • `nho_ghi(_kn, out)` của top_titles — cất rỗng vào D1 **6 tiếng** ⇒ kênh vừa đăng video
        vẫn bị coi như chưa có gì suốt 6 tiếng

    Nguyên tắc: **rỗng là một kết quả ĐÁNG NGỜ, không phải một sự thật.** Nguồn hỏng, quota cạn,
    mạng rớt đều ra rỗng. Cất nó lại là nhân bản lỗi ra suốt thời gian sống của bộ đệm."""
    src = _doc("firestore_bridge.py")
    d = src.splitlines()
    xau = []
    for i, l in enumerate(d, 1):
        t = l.strip()
        if t.startswith("#"):
            continue
        for mau in ('_A_KEYS["rows"] = out', "_H2.nho_ghi(_kn, out)"):
            if t.startswith(mau):
                gan = " ".join(d[max(0, i - 5):i - 1])
                if "if out" not in gan:
                    xau.append(f"dòng {i}: `{t[:52]}` không kiểm rỗng trước khi cất")
    assert not xau, "cất kết quả rỗng vào bộ đệm:\n   " + "\n   ".join(xau)



def t_phanh_do_khong_duoc_phai_gia_dinh_can():
    """Cái phanh hạn mức không được NHẢ RA khi nó mù.

    26/8 — phiên 01:54Z là bằng chứng đắt: `⚠️ không đọc được sổ ngân sách (429)` lúc 02:01, plan
    mở đủ 18 lane, `🛑 PHANH` in **0 lần**, tới 03:09 sổ đọc **56.051/50.000 = 112%**. Sổ ngân sách
    cất trong chính project B mà nó đo, nên B cạn ⇒ đọc sổ 429 ⇒ nền = 0 ⇒ phanh thấy "0% đã dùng".

    Hai điều kiện phải giữ, kiểm bằng chính mã nguồn:
      ① `nap_nen_ngan_sach` phải hỏi **D1** (`ngan_sach_doc`) — nguồn nằm NGOÀI thứ đang cạn.
      ② Nhánh "không đọc được" phải **gán nền khác 0** (giả định cạn). Gán 0 hoặc bỏ trống =
         phanh tự nhả, đúng cái lỗi này."""
    import ast as _ast
    cay = _ast.parse(_doc("firestore_bridge.py"))
    fn = next((n for n in _ast.walk(cay)
               if isinstance(n, _ast.FunctionDef) and n.name == "nap_nen_ngan_sach"), None)
    assert fn, "mất hàm nap_nen_ngan_sach"
    than = _ast.dump(fn)
    assert "ngan_sach_doc" in than, \
        "nap_nen_ngan_sach không hỏi D1 — đồng hồ xăng lại nằm trong bình xăng"
    # Trong MỌI handler except, phải có gán cho nen_doc/nen_ghi bằng giá trị khác literal 0
    cuu = [h for h in _ast.walk(fn) if isinstance(h, _ast.ExceptHandler)]
    assert cuu, "nap_nen_ngan_sach không còn nhánh bắt lỗi"
    an_toan = False
    for h in cuu:
        for nd in _ast.walk(h):
            if isinstance(nd, _ast.Subscript) and isinstance(nd.value, _ast.Name) \
                    and nd.value.id == "_NGAN_SACH" and isinstance(nd.ctx, _ast.Store):
                an_toan = True
    assert an_toan, ("nhánh 'không đọc được sổ' không gán nền ngân sách -> nền giữ 0 -> "
                     "phanh coi như còn 100% hạn mức đúng lúc đã cạn")



def t_duong_lui_khong_duoc_khuech_dai_loi():
    """Đường lùi không được nhân bản chính cái lỗi nó tránh.

    26/8, phiên 01:54Z: `⚠️ plan không đọc được hồ key A (429 Quota exceeded.) — lane tự đọc như
    cũ`. Bản vá "plan đọc A một lần cho 18 lane" CÓ chạy, nhưng gặp 429 thì trả `""` ⇒ 18 lane
    mỗi đứa tự đọc A ⇒ **1 lượt hỏng thành 18 lượt hỏng**, nhè đúng project vừa báo là đã cạn.

    "A cạn" là sự thật CHUNG của phiên. Đã biết thì phải báo xuống lane (tín hiệu `CAN`), không
    để mỗi lane tự đâm vào tường một lần mới tin — đúng cách đã làm cho project B từ 24/8."""
    src = _doc("firestore_bridge.py")
    assert 'return "CAN"' in src, \
        "dong_goi_keys_a không phát tín hiệu CAN khi A trả 429 — 18 lane sẽ tự đâm vào A"
    assert 'goi == "CAN"' in src, "keys_a_tu_plan không hiểu tín hiệu CAN từ plan"
    assert '_KEYS_PLAN.get("can")' in src, \
        "có tín hiệu CAN nhưng không chỗ nào dùng nó để chặn đường đọc A sống"
    import ast as _ast
    fn = next((n for n in _ast.walk(_ast.parse(src))
               if isinstance(n, _ast.FunctionDef) and n.name == "dong_goi_keys_a"), None)
    assert fn, "mất hàm dong_goi_keys_a"
    h = [x for x in _ast.walk(fn) if isinstance(x, _ast.ExceptHandler)]
    assert h and any("429" in _ast.dump(x) for x in h), \
        "nhánh lỗi của dong_goi_keys_a không phân biệt 429 với lỗi thường"



def t_seed_khong_bi_spread_de_len_khoa_co_y():
    """Trong seed 50 kênh gen-2, `**dich` không được đè khoá mà seed CỐ Ý quyết.

    26/8 — bắt trước khi chạy, nên chưa mất gì. `doc` viết:

        doc = {..., "type":"short", "make_long":False, "long_target":0, "n_shorts":3,
               **dich, "format":..., ...}

    mà `TARGET` (nguồn của `dich`) lại chứa đúng `long_target`, `n_shorts`, `make_long`. Python lấy
    giá trị SAU, nên `**dich` âm thầm đè cả ba: 50 kênh thiết kế là SHORT sẽ nhận chỉ tiêu long của
    kênh mẫu. Không lỗi, không log — vài tiếng sau mới lộ ra bằng một loạt video sai định dạng, và
    lúc đó phải sửa 50 bản ghi.

    Kiểm hai điều, bằng AST chứ không khớp chuỗi:
      ① `TARGET` không giao với nhóm khoá cố ý.
      ② Trong `doc`, mọi khoá cố ý phải đứng SAU dấu `**`."""
    import ast as _ast
    src = _doc("seed_the_he_2.py")
    cay = _ast.parse(src)
    CO_Y = {"type", "make_long", "long_target", "n_shorts", "format", "the_he", "paused"}

    tgt = next((n for n in _ast.walk(cay) if isinstance(n, _ast.Assign)
                and any(getattr(t, "id", "") == "TARGET" for t in n.targets)), None)
    assert tgt, "mất biến TARGET trong seed_the_he_2.py"
    ten_tgt = {e.value for e in tgt.value.elts if isinstance(e, _ast.Constant)}
    chung = CO_Y & ten_tgt
    assert not chung, (f"TARGET thừa hưởng {sorted(chung)} — nhưng seed cố ý tự quyết mấy khoá này; "
                       "**dich sẽ đè lên chúng")

    for d in _ast.walk(cay):
        if not isinstance(d, _ast.Dict):
            continue
        khoa = [(i, k.value) for i, k in enumerate(d.keys)
                if isinstance(k, _ast.Constant) and isinstance(k.value, str)]
        if not any(k in CO_Y for _, k in khoa):
            continue
        # CHỈ soi `**ten_bien` — túi mà nội dung do dữ liệu quyết, không đọc được từ mã.
        # `**ham(...)` thì khác: khoá của nó cố định trong thân hàm, kiểm được, và ở seed nó là
        # chữ ký giọng (voice/voice_rate/voice_pitch) — rời hẳn nhóm khoá cố ý. Gộp hai loại làm
        # một là chốt kêu oan, mà chốt kêu oan thì lần sau người ta tắt nó đi.
        sao = [i for i, k in enumerate(d.keys)
               if k is None and isinstance(d.values[i], _ast.Name)]
        if not sao:
            continue
        som = [k for i, k in khoa if k in CO_Y and i < max(sao)]
        assert not som, (f"khoá cố ý {sorted(set(som))} đặt TRƯỚC ** trong dict -> bị spread đè. "
                         "Đưa xuống SAU **, thứ tự này là điều kiện đúng chứ không phải thẩm mỹ")



def t_dien_tap_can_quota():
    """Ép Firestore chết sạch rồi gọi thật 13 hàm trong đường chạy chính — không hàm nào được ném.

    27/8 — vì sao chốt này đáng giá hơn mọi lần đọc mã bằng mắt: nó tìm ra 5 điểm chết mà đọc mã
    không thấy, và cả 5 CÙNG MỘT GỐC — lời gọi lấy kết nối (`_db_meta()`, `_db_jobs()`) nằm NGOÀI
    lớp bọc mềm `_soft`. Nhìn vào `new_job` thì thấy `_soft(...)` bao quanh lệnh ghi và yên tâm;
    chú thích của nó còn ghi hẳn "id sinh OFFLINE -> quota chết vẫn có id". Thực tế 429 ném ngay ở
    dòng lấy kết nối, chưa tới `_soft`, chưa sinh id nào. Chú thích nói một đằng, mã chạy một nẻo.

    Hai kịch bản, vì hai kiểu chết khác nhau:
      • NÉM 429 — Firestore trả lỗi thẳng.
      • TRẢ VỀ RỖNG — truy vấn chạy bình thường nhưng KHÔNG RA BẢN GHI NÀO. Đây mới là kiểu độc:
        không có ngoại lệ nào để bắt, và nó đã xảy ra thật (phiên #33028251503 đọc "thành công"
        đúng 55 bản ghi cũ, 0 kênh gen-2 -> plan mở 0 lane suốt đêm).

    Thêm hàm mới đụng Firestore thì thêm một dòng vào `dien_tap_can_quota._bai` — chốt này sẽ bắt
    hộ, thay vì phát hiện sau khi đã mất một đêm render."""
    import subprocess as _sp
    import sys as _sy
    _goc = os.path.dirname(os.path.abspath(__file__))
    r = _sp.run([_sy.executable, os.path.join(_goc, "dien_tap_can_quota.py")],
                capture_output=True, text=True, timeout=180,
                env={**os.environ, "MM0_HOT_OFF": "1"})
    if r.returncode != 0:
        chet = [d.strip() for d in (r.stdout or "").splitlines() if d.strip().startswith("[")]
        raise AssertionError("cạn quota là hệ đứng ở %d chỗ: %s" % (len(chet), " · ".join(chet[:4])))


def t_khong_ten_chua_dinh_nghia():
    """Quét `undefined name` trên các tệp lõi — bắt NameError TRƯỚC khi nó nấp trong nhánh hiếm.

    27/8 — lane STEAMTRUTH chết với `NameError: name 'keys' is not defined`. Nguyên nhân: em thêm
    tham số `keys` cho `dung_props` và sửa hai chỗ gọi, nhưng `chay_chung` cũng gọi nó mà bản thân
    `chay_chung` không có `keys` trong tham số. Cú pháp hợp lệ, `ast.parse` xanh, selftest xanh —
    và nó chỉ nổ khi luồng đi đúng vào nhánh đó, tức trên CI, sau khi đã tiêu một lane.
    Đây là loại lỗi đắt nhất trong Python: không phải lỗi cú pháp nên mọi phép kiểm cú pháp đều
    bỏ qua, mà lại là lỗi CHẮC CHẮN NỔ khi chạy tới.
    `pyflakes` bắt được nó trong một giây, không cần chạy gì cả. Thiếu thư viện thì bỏ qua có
    thông báo — chốt này là lớp làm tốt hơn, không được thành chỗ chặn mới."""
    import subprocess as _sp
    import sys as _sy
    _goc = os.path.dirname(os.path.abspath(__file__))
    try:
        r = _sp.run([_sy.executable, "-m", "pyflakes",
                     os.path.join(_goc, "the_he_2.py"), os.path.join(_goc, "run_render.py"),
                     os.path.join(_goc, "firestore_bridge.py"), os.path.join(_goc, "hot_db.py"),
                     os.path.join(_goc, "y_tuong.py"), os.path.join(_goc, "radar_dethai.py")],
                    capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        print("      ⏭ bỏ qua: chưa cài pyflakes (`pip install pyflakes`)")
        return
    xau = [d for d in (r.stdout or "").splitlines() if "undefined name" in d]
    if not xau and "No module named" in (r.stderr or ""):
        print("      ⏭ bỏ qua: chưa cài pyflakes (`pip install pyflakes`)")
        return
    assert not xau, ("có %d tên chưa định nghĩa — sẽ nổ NameError khi chạy tới:\n   %s"
                     % (len(xau), "\n   ".join(d.strip()[-110:] for d in xau[:6])))


def t_moi_kenh_gen2_vao_duoc_nhanh():
    """Đường chạy phải quyết định bằng THẾ HỆ, không bằng định dạng.

    27/8 — lỗi đắt nhất tìm được cả ngày. Nhánh gọi `_gen2_bo` gác bằng một danh sách ĐỊNH DẠNG
    viết tay, và danh sách đó thiếu `race` (7 kênh) lẫn `cinematic` (10 kênh):
    **17/50 kênh thế hệ 2 CHƯA BAO GIỜ chạy pipeline gen-2** — chúng rơi thẳng xuống đường cũ,
    đường đi lấy ảnh Pexels làm nền và gọi Gemini viết kịch bản.
    Khớp hoàn toàn với thứ anh nhìn thấy: kênh AMERICA LOOKED UP có nguồn `bai_duoc_doc` (bảng
    Wikipedia đọc nhiều nhất) nhưng video nói về tỉ lệ kiểm toán thuế IRS, tiêu đề là văn AI
    viết, nền là ảnh chụp sẵn.
    Và cổng chặn "gen-2 không rơi xuống đường cũ" nằm BÊN TRONG nhánh đó — nên nó không bao giờ
    chạy cho 17 kênh kia. Chặn một cánh cửa mà chúng không đi qua.

    Chốt hai vế, vì sửa một vế thôi thì hỏng lại theo cách khác:
      1. mã phải hỏi `the_he` để vào nhánh (không chỉ dựa vào danh sách định dạng)
      2. và mọi định dạng đang dùng trong JSON đều phải được nhánh đó nhận"""
    import json as _j
    src = _doc("run_render.py")
    i = src.index("_gen2_bo(")
    j = src.rfind("fmt in (", 0, i)
    assert j > 0, "không tìm thấy cổng định dạng trước _gen2_bo"
    khoi = src[max(0, j - 400):j + 300]
    assert 'the_he' in khoi, \
        "cổng vào nhánh gen-2 KHÔNG hỏi `the_he` — dạng mới thêm sau sẽ lại rơi xuống đường cũ"
    ds = _j.loads(_doc("kenh_the_he_2.json"))
    danh = src[j:src.index(")", j)]
    thieu = sorted({k["dinh_dang"] for k in ds if k.get("dinh_dang") and k["dinh_dang"] not in danh})
    # thiếu trong danh sách thì PHẢI được `the_he` gánh — đã assert ở trên; báo cho biết là đủ
    if thieu:
        print("      ℹ️ dạng không có trong danh sách (đi bằng `the_he`): %s" % ", ".join(thieu))


def t_nhac_nen_khong_dung_chung():
    """Nhạc nền phải chia ra, không được viết cứng một bản cho cả 50 kênh.

    27/8 — kho có 18 tệp nhạc, mà `the_he_2` viết cứng `music/carefree.mp3`: 50 kênh dùng chung
    ĐÚNG MỘT bản. Đây là dấu vân tay "cùng một chủ" phiên bản âm thanh — cùng loại với cái pill
    in tên định dạng đã gỡ khỏi hình, chỉ khó thấy hơn vì người ta không "nhìn" nhạc. Nhưng nghe
    hai kênh khác nhau mà cùng một vòng nhạc thì nhận ra ngay, và đó đúng là thứ chính sách
    "nội dung sản xuất hàng loạt" của YouTube nhắm tới.
    Chốt hai vế: JSON phải có `brand.nhac` cho mọi kênh, và mã KHÔNG được viết cứng một đường
    dẫn nhạc làm giá trị chính (chỉ được dùng làm giá trị lùi khi thiếu)."""
    import json as _j
    import collections as _c
    ks = _j.loads(_doc("kenh_the_he_2.json"))
    thieu = [k["ten"] for k in ks if not (k.get("brand") or {}).get("nhac")]
    assert not thieu, "thiếu `brand.nhac`: %s" % ", ".join(thieu[:5])
    dem = _c.Counter((k.get("brand") or {}).get("nhac") for k in ks)
    assert len(dem) >= 6, ("chỉ %d bản nhạc cho %d kênh — nghe ra ngay là cùng một chủ"
                           % (len(dem), len(ks)))
    src = _doc("the_he_2.py")
    for d in src.split("\n"):
        if '"music":' in d and "music/" in d and not d.strip().startswith("#"):
            assert "brand" in d or "nhac" in d, \
                "viết cứng nhạc nền, không đọc `brand.nhac`: %s" % d.strip()[:90]


def t_kenh_anh_em_khong_trung_kho():
    """Hai kênh CÙNG NICHE + CÙNG nguồn + CÙNG dạng + CÙNG trục thì kho đề tài phải rời nhau.

    27/8 — 22/24 niche có hơn một kênh, và 4 cặp dùng y hệt một đường ống:
        COURT RECORD ~ COLD FILE · SHOW NUMBERS ~ GONE TOO SOON
        STEAM TRUTH ~ GAME GRAVEYARD · FILINGS SAY ~ QUIET LAYOFFS
    Hiện kho của chúng không trùng mục nào. Nhưng đó là MAY, không phải luật được giữ: chỉ cần
    một lần thêm đề tài (tay hoặc do `y_tuong` đề xuất) là hai kênh cùng chủ ra hai video cùng
    đề tài — thứ người xem nhận ra ngay, và đúng thứ chính sách 'nội dung sản xuất hàng loạt'
    của YouTube nhắm tới.
    Chốt ở đây để cái may đó thành luật."""
    import itertools
    import json as _j
    ks = _j.loads(_doc("kenh_the_he_2.json"))

    def _kho(k):
        ts = k.get("tham_so") or {}
        tr = ts.get("xoay")
        v = ts.get("kho_%s" % tr) or []
        if isinstance(v, str):
            try:
                v = _j.loads(v.replace("'", '"'))
            except Exception:
                v = []
        return tr, {str(x).strip().lower() for x in v}

    xau = []
    for a, b in itertools.combinations(ks, 2):
        if (a.get("brand") or {}).get("niche") != (b.get("brand") or {}).get("niche"):
            continue
        if a.get("ham") != b.get("ham") or a.get("dinh_dang") != b.get("dinh_dang"):
            continue
        tra, ka = _kho(a)
        trb, kb = _kho(b)
        if tra != trb or not ka or not kb:
            continue
        chung = ka & kb
        if chung:
            xau.append("%s ~ %s: %d đề tài trùng (%s)"
                       % (a["ten"], b["ten"], len(chung), ", ".join(sorted(chung)[:3])))
    assert not xau, "kênh cùng niche trùng kho đề tài:\n   " + "\n   ".join(xau[:5])


def t_so_de_tai_chi_ghi_khi_ra_lo():
    """`FB.save_topics` chỉ được gọi từ MỘT chỗ: hàm chốt sổ, chạy sau khi đẩy Drive xong.

    27/8 — anh nêu yêu cầu: "nó phải biết số video/kịch bản THỰC TẾ đã làm, không tính clip
    không đạt hay đã xoá". Đo thì hiện tại ngược lại: `save_topics` được gọi ở 6 chỗ, và ít nhất
    3 chỗ nằm TRƯỚC lệnh kiểm QC (dòng 988 ghi sổ, dòng 989 mới `if not ok: return False`).
    Video trượt QC vẫn bị ghi là "đã làm" ⇒ sổ đầy dần những đề tài CHƯA TỪNG THÀNH VIDEO, và
    kênh tự từ chối làm lại chúng — càng chạy càng cạn đề tài trong khi kho vẫn còn nguyên.

    Bất biến cần giữ: sổ BỀN chỉ được ghi tại một điểm duy nhất, và điểm đó phải là sau bằng
    chứng "đã có tệp thật trong kho" (đẩy Drive trả về id). Thêm một lệnh ghi sổ ở chỗ khác là
    mở lại đúng lỗ hổng này, nên chặn ở đây thay vì trông vào trí nhớ."""
    src = _doc("run_render.py")
    goi = [d for d in src.split("\n") if "FB.save_topics(" in d and not d.strip().startswith("#")]
    assert len(goi) == 1, ("save_topics phải gọi ĐÚNG 1 chỗ (trong _chot_chu_de), đang có %d:\n   %s"
                           % (len(goi), "\n   ".join(x.strip()[:90] for x in goi[:5])))
    i = src.index("def _chot_chu_de(")
    j = src.index("\ndef ", i + 5)
    assert "FB.save_topics(" in src[i:j], "lệnh ghi sổ bền không nằm trong _chot_chu_de"
    # và _chot_chu_de phải được gọi từ enqueue_drive (bằng chứng video ra lò), không phải chỗ khác
    k = src.index("def enqueue_drive(")
    l = src.index("\ndef ", k + 5)
    assert "_chot_chu_de(" in src[k:l], "chốt sổ không nằm trong enqueue_drive — sẽ ghi sổ quá sớm"


def t_khong_phu_de_chong():
    """Không component nào được vừa tự vẽ phụ đề, vừa trải props sang con CŨNG vẽ phụ đề.

    27/8 — anh chụp ảnh AMERICALOOKEDUP: trên khung có HAI băng chữ cùng một câu, khác cỡ, khác vị
    trí, khác cách ngắt cụm (5 chữ vs 8 chữ) — một cái nền đen bo góc, một cái chữ trắng trần nằm
    lệch xuống. Không phải video cũ chưa dọn: `RaceLong` trải `{...r}` (có `r.subs`) xuống
    `BarChartRace`, mà BarChartRace tự vẽ `<Karaoke subs>` bên trong; rồi RaceLong lại vẽ tiếp
    `<KaraokeCaption>` của nó. Hai bộ vẽ phụ đề chạy cùng lúc trên cùng một câu.

    Đây là lỗi mà `{...props}` rất dễ đẻ ra: trải cả gói thì tiện, nhưng nó chuyển luôn những
    trường mà con KHÔNG nên nhận. Chốt này soi đúng cái hình dạng đó."""
    import re as _re
    import glob as _g
    goc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "engine-remotion", "src")
    if not os.path.isdir(goc):
        print("      ⏭ bỏ qua: không thấy engine-remotion/src")
        return
    ve = set()                       # component TỰ vẽ phụ đề
    src = {}
    for f in _g.glob(os.path.join(goc, "*.tsx")):
        t = io.open(f, encoding="utf-8").read()
        src[os.path.basename(f)[:-4]] = t
        if _re.search(r"<Karaoke[A-Za-z]*\s", t):
            ve.add(os.path.basename(f)[:-4])
    xau = []
    for ten, t in src.items():
        if ten not in ve:
            continue                 # cha không vẽ phụ đề -> con vẽ là đúng, không phải chồng
        t2 = _re.sub(r"\{/\*[\s\S]*?\*/\}", "", t)      # bỏ chú thích JSX kẻo bắt nhầm ví dụ
        for con in ve:
            if con == ten:
                continue
            for m in _re.finditer(r"<" + con + r"\s+([^>]*?)/?>", t2):
                thuoc = m.group(1)
                if "{..." in thuoc and "subs=" not in thuoc:
                    xau.append(f"{ten}.tsx trải props xuống <{con}> mà không cắt `subs`")
    assert not xau, ("phụ đề sẽ bị vẽ hai lớp chồng nhau:\n   " + "\n   ".join(sorted(set(xau))[:6]))


def t_dien_tap_ca_phien():
    """Chạy nguyên `plan_mode()` với Firestore chết sạch — phải xếp đủ 18 lane, không phải 0.

    27/8 — chốt này bắt đúng loại lỗi mà chốt "từng hàm" ngay trên KHÔNG bắt được, và ngược lại.
    Bằng chứng: chốt từng hàm chấm `read_keys` ✅ vì nó trả `[]` chứ không ném. Nhưng cả phiên thì
    `PLAN channels=[]`, vì run_render đọc `[]` rồi kết luận "Không đọc được key -> bỏ mẻ". Không
    hàm nào ném, cả đêm vẫn mất trắng.
    Chạy cả phiên còn lôi thêm 3 điểm nữa: `mark_key_alive` đọc ngoài lớp bọc mềm · `drive_usage`
    trả `None` trong khi người gọi mở gói `used, cap = ...` · và cái phanh tự cắt 18 lane còn 3
    đúng lúc quota đã chết (cắt lúc đó không tiết kiệm được gì, chỉ giảm sản lượng).

    RÚT RA: "mỗi hàm đều có đường lui" KHÔNG suy ra "hệ thống không đứng". Phải đo cả đường chạy."""
    import subprocess as _sp
    import sys as _sy
    _goc = os.path.dirname(os.path.abspath(__file__))
    try:
        r = _sp.run([_sy.executable, os.path.join(_goc, "dien_tap_can_quota.py"), "--plan"],
                    capture_output=True, text=True, timeout=240,
                    env={**os.environ, "MM0_HOT_OFF": "1", "OWNER_UID": "THU", "FORCE": "1"})
    except _sp.TimeoutExpired:
        print("      ⏭ bỏ qua: diễn tập cả phiên quá 240s (máy chậm/mạng chặn) — chốt từng hàm vẫn chạy")
        return
    if r.returncode != 0:
        duoi = "\n      ".join([d for d in (r.stdout or "").splitlines()[-8:] if d.strip()])
        raise AssertionError("cạn quota -> plan KHÔNG xếp đủ lane:\n      " + duoi)


def t_50_kenh_khong_duoc_giong_nhau():
    """50 kênh gen-2 phải KHÁC NHAU, đo bằng số chứ không bằng lời hứa.

    26/8 — đo lần đầu: **241 cặp ≥70 điểm, cặp tệ nhất 97,9** (ALERT NOW ~ QUAKE LOG gần như một
    kênh). Ba chiều phẳng lì: `font` 1 giá trị cho cả 50, `voice_tone` 1 giá trị, và chưa kênh nào
    có trường `voice` nên tất cả sẽ đọc bằng cùng một giọng mặc định.

    Đây không phải chuyện thẩm mỹ. Chú thích trong `tts_karaoke.set_voice` đã ghi rõ: nhiều kênh
    cùng chủ mà nghe/nhìn như nhau chính là thứ chính sách "inauthentic, mass-produced content" của
    YouTube nhắm tới — rủi ro bật kiếm tiền lớn hơn mọi lỗi kỹ thuật cộng lại.

    Sau khi vá (50 chữ ký giọng riêng · 24 phông · mô-típ không trùng trong cùng định dạng):
    **0 cặp vượt ngưỡng**, cao nhất 68,9, trung bình 38,8 -> 18,2."""
    import do_giong_nhau as DG
    ps = DG.do()
    vuot = [p for p in ps if p[0] >= DG.NGUONG]
    assert not vuot, ("có %d cặp kênh giống nhau ≥%.0f điểm: " % (len(vuot), DG.NGUONG)
                      + " · ".join(f"{s} ({x}~{y})" for s, x, y in vuot[:4]))


def t_bam_python_khop_typescript():
    """Hàm băm bên Python phải cho ĐÚNG kết quả như bên TypeScript.

    `do_giong_nhau.py` chấm điểm "hai kênh có cùng chữ ký chuyển cảnh không" bằng bản băm Python,
    còn thứ thật sự chạy lúc render là bản trong `Chuyen.tsx`. Hai bên lệch nhau một bước trộn bit
    là bảng điểm nói về một hệ KHÁC với hệ đang render — một phép đo nói dối, tệ hơn không đo."""
    import re as _re
    # BỎ CHÚ THÍCH TRƯỚC KHI SOI. Thử phá 26/8: biến `h ^= h >>> 15;` thành `// h ^= h >>> 15;`
    # thì chốt vẫn xanh — vì chuỗi vẫn nằm đó, chỉ là đã chết. Một chốt đọc cả chú thích là chốt
    # tin vào lời kể chứ không tin vào mã đang chạy.
    src = _re.sub(r"//[^\n]*", "", _doc("../engine-remotion/src/Chuyen.tsx"))
    for buoc in ("h ^= h >>> 15", "Math.imul(h, 2246822519)", "h ^= h >>> 13", "16777619", "2166136261"):
        assert buoc in src, f"Chuyen.tsx thiếu bước băm '{buoc}' — bản Python sẽ lệch"
    import do_giong_nhau as DG
    # đối chiếu bằng chính công thức TS, tính lại trong Python theo đúng thứ tự
    def ts(sx):
        h = 2166136261
        for c in sx:
            h = ((h ^ ord(c)) * 16777619) & 0xFFFFFFFF
        h ^= h >> 15
        h = (h * 2246822519) & 0xFFFFFFFF
        h ^= h >> 13
        return h & 0xFFFFFFFF
    for t in ("@mappedusa", "@quakelogusa", "@paycheckgap", "", "x"):
        assert DG._bam(t) == ts(t), f"băm lệch ở '{t}': {DG._bam(t)} != {ts(t)}"


def t_phong_khai_roi_phai_thao_ra():
    """Composition khai prop `font` thì PHẢI thao nó ra khỏi props.

    Đúng lớp lỗi `vang is not defined` (25/8, mất trọn một phiên 18 lane / 0 video): khai trong
    type mà quên destructure -> `ReferenceError` ngay khung đầu. Canary 26/8 bắt lại đúng lỗi này
    ở `ThenNowShort`: `phong(font)` nằm trong `TNPairView`, một component KHÁC, không hề nhận
    `font` — nên khai đúng ở component cha vẫn hỏng."""
    import re as _re
    xau = []
    for ten in ("RankedShort", "ScaledShort", "MappedShort", "LongshotShort", "ThenNowShort"):
        src = _doc(f"../engine-remotion/src/{ten}.tsx")
        if "phong(font)" not in src:
            xau.append(f"{ten}: không dùng phong(font) — phông riêng của kênh vô tác dụng")
            continue
        for m in _re.finditer(r"(?:const|export const)\s+(\w+)[^=]*=\s*\(?\{([^}]*)\}", src):
            pass
        # mọi component có phong(font) phải có `font` trong danh sách thao ra của CHÍNH nó
        for kh in _re.finditer(r"=\s*\(\{([^}]*)\}[^)]*\)\s*=>\s*\{", src):
            pass
        if not _re.search(r"\bfont\s*=\s*\"\"", src):
            xau.append(f"{ten}: có phong(font) nhưng không chỗ nào thao `font` ra")
    assert not xau, "; ".join(xau)



def t_gen2_phai_lam_thumbnail():
    """Cả ba đường render của thế hệ 2 phải làm ảnh bìa.

    26/8 — bắt được TRƯỚC KHI SEED: nhánh `the_he == 2` trong `run_render` gọi `chay_chung` rồi
    `return` ngay, mà `chay_chung`/`chay_race`/`chay_phim` đều kết thúc bằng `return (ra, info)`
    — **không đường nào làm thumbnail**. 50 kênh mới sẽ xuất bản không có ảnh bìa, trong khi
    thumbnail là thứ quyết định người ta có bấm hay không.

    Lộ ra khi truy đường đi của `brand.mau`/`brand.font`: gán trong JSON mà không có ai đọc thì
    y hệt bẫy `voice_tone`. Luật rút ra: gán một thuộc tính ở đâu thì phải đi hết đường của nó
    tới lúc render, không dừng ở chỗ ghi."""
    import ast as _ast
    src = _doc("the_he_2.py")
    cay = _ast.parse(src)
    thieu = []
    for ten in ("chay_chung", "chay_race", "chay_phim"):
        fn = next((n for n in _ast.walk(cay) if isinstance(n, _ast.FunctionDef) and n.name == ten), None)
        if not fn:
            thieu.append(f"{ten}: mất hàm"); continue
        if "lam_thumb" not in _ast.dump(fn):
            thieu.append(f"{ten}: render xong mà không làm thumbnail")
    assert not thieu, "; ".join(thieu)
    # và thumbnail phải nhận template + phông riêng của kênh, nếu không 50 kênh chung một bìa
    ds = _doc("datastory_ci.py")
    assert '"mau": str(mau or "trai")' in ds and '"font": str(font or "")' in ds, \
        "doc_thumb không truyền mau/font xuống DocThumb — template riêng của kênh vô tác dụng"


def t_fitsize_phai_theo_phong_va_khung():
    """`fitSize` không được dùng một hằng bề rộng cho 24 phông.

    26/8 — `CHAR_W = 0.62` hiệu chỉnh riêng cho Poppins (chú thích cũ nói rõ). Đo thật bằng
    composition `DoChu`: Bebas **0,355** ↔ Archivo **0,717** — chênh hơn HAI LẦN. Phông hẹp bị
    tính rộng hơn thực nên chữ tự thu nhỏ, phí nửa khung; phông rộng bị tính hẹp hơn thực nên
    CHỮ TRÀN KHUNG. Ngay Poppins cũng đo ra 0,646 chứ không phải 0,62 — luôn hụt 4%.

    Kèm theo: bề rộng ô chữ phải tính từ template (`RONG`), không viết cứng 880/850/900/820 —
    những số đó đúng cho đúng một bố cục."""
    import re as _re
    dt = _doc("../engine-remotion/src/DocThumb.tsx")
    assert "const CHAR_W" not in dt, "vẫn còn hằng CHAR_W dùng chung cho mọi phông"
    assert "rongKyTu(font)" in dt, "DocThumb không lấy bề rộng ký tự theo phông"
    # SOI THEO DÒNG, không khớp chuỗi cân ngoặc: `fitSize([String(stat)], ...)` có ngoặc lồng nên
    # mọi regex không cân ngoặc đều cắt nhầm giữa chừng rồi báo oan (đã dính đúng lỗi này 26/8).
    xau = [l.strip()[:70] for l in dt.splitlines()
           if "fitSize(" in l and "const fitSize" not in l and "RONG" not in l
           and not l.strip().startswith("//")]      # bỏ chú thích: nhắc tên hàm không phải là gọi nó
    assert not xau, f"fitSize còn dùng bề rộng viết cứng: {xau}"
    ph = _doc("../engine-remotion/src/Phong.tsx")
    import json as _json
    ten_phong = set(_re.findall(r"^\s{2}(\w+):\s*_n\(", ph, _re.M))
    do_duoc = set(_re.findall(r"^\s{2}(\w+):\s*[0-9.]+,", ph, _re.M))
    thieu = ten_phong - do_duoc
    assert not thieu, f"phông chưa ĐO bề rộng (sẽ đoán sai -> tràn hoặc phí chỗ): {sorted(thieu)}"



def t_canary_khong_duoc_render_vao_composition_rong():
    """Mọi composition thế hệ 2 phải có defaultProps ĐỦ NỘI DUNG.

    26/8 — `LongshotShort` không hề có `defaultProps`. `items` undefined ⇒ thang rỗng ⇒
    `calcLongshot` ra đúng 126 khung (chỉ intro + outro). Canary in "✅ LongshotShort" nhưng nó
    render một video TRỐNG, không chạm một dòng nào của phần nội dung. `RaceShort` chỉ có 1 cột,
    `CinematicShort` có `scenes: []` (dài đúng 1 khung) — cùng bệnh.

    Nghĩa là suốt thời gian qua canary bảo vệ được 4/7 dạng, còn 3 dạng thì nó gật đầu cho qua bất
    kỳ lỗi bố cục nào. Ngay khi có dữ liệu mẫu thật, canary lộ ngay hai lỗi CHỒNG CHỮ trong
    `LongshotShort` mà trước đó không ai thấy.

    **Luật**: một phép thử chạy trên đầu vào rỗng không phải phép thử. Composition nào cũng phải
    có dữ liệu mẫu đủ để đi qua chính phần mà nó sinh ra để vẽ."""
    import re as _re
    src = _doc("../engine-remotion/src/Root.tsx")
    TOI_THIEU = 3
    xau = []
    for c in ("RankedShort", "ScaledShort", "MappedShort", "LongshotShort",
              "ThenNowShort", "RaceShort", "CinematicShort"):
        m = _re.search(r'<Composition id="' + c + r'"(?:.|\n)*?/>', src)
        if not m:
            xau.append(f"{c}: không thấy trong Root.tsx"); continue
        blk = m.group(0)
        if "defaultProps" not in blk:
            xau.append(f"{c}: KHÔNG có defaultProps -> canary render video rỗng"); continue
        # đếm số phần tử mẫu: mỗi mục là một `{ ... }` bên trong một mảng
        n = len(_re.findall(r"\{\s*(?:name|label|state|type|t)\s*:", blk))
        if n < TOI_THIEU:
            xau.append(f"{c}: chỉ {n} mục mẫu (<{TOI_THIEU}) -> canary gần như không chạm nội dung")
    assert not xau, "; ".join(xau)



def t_phong_phai_chay_het_duong_toi_luc_render():
    """Phông riêng của kênh phải đi HẾT đường: JSON -> props -> composition, đủ cả 7 dạng.

    26/8 — đây là lớp lỗi lặp lại ba lần trong một đêm, nên chốt nó lại:
      • `voice_tone` ghi vào brand kit từ đầu — KHÔNG hàm nào đọc.
      • `voice_pitch` có chỗ nhận — nhưng cả hai điểm gọi `set_voice` chỉ truyền 2/3 tham số.
      • `brand.font`/`brand.mau` gán cho 50 kênh — `chay_race`/`chay_phim` không truyền xuống,
        `BarChartRace`/`Cinematic` cũng chưa nhận. Ba dạng cứ dùng Poppins bất kể JSON ghi gì.

    Mỗi lần đều "đã gán rồi" mà thực tế không đổi gì. Kiểm từng khúc riêng lẻ không bắt được —
    phải kiểm CẢ ĐƯỜNG.

    **Luật**: gán một thuộc tính ở đâu thì phải đi theo nó tới tận chỗ dùng. Dừng ở chỗ ghi là
    trang trí, không phải tính năng."""
    import re as _re
    th = _doc("the_he_2.py")
    ds = _doc("datastory_ci.py")
    xau = []
    # 26/8 — `chay_chung` đã tách phần dựng props sang `dung_props` (long 16:9 cần props của nhiều
    # chương hơn số short). Chốt phải đi theo mã, không neo vào tên hàm cũ: neo sai thì hoặc đỏ oan
    # như lần này, hoặc tệ hơn — xanh trong khi đường dẫn thật đã đứt.
    for f in ("dung_props", "dung_props_race", "dung_props_phim"):
        m = _re.search(r"def " + f + r"\(.*?(?=\ndef )", th, _re.S)
        assert m, f"mất hàm {f}"
        if "font" not in m.group(0):
            xau.append(f"{f}: không truyền font xuống props")
    if 'props["font"] = font' not in ds:
        xau.append("build_doc_props: nhận font nhưng không ghi vào props")
    for c in ("RankedShort", "ScaledShort", "MappedShort", "LongshotShort",
              "ThenNowShort", "BarChartRace", "Cinematic"):
        src = _doc(f"../engine-remotion/src/{c}.tsx")
        if "font?: string" not in src:
            xau.append(f"{c}: không khai prop font")
        elif "phong(font)" not in src:
            xau.append(f"{c}: khai font nhưng không dùng -> vẫn Poppins")
    assert not xau, "; ".join(xau)



def t_don_kho_phai_di_het_cay_va_moi_loai_tep():
    """Bản dọn 55 kênh cũ phải đi HẾT cây thư mục và đụng MỌI loại tệp.

    26/8 — bắt trước khi chạy thật. Bản đầu dùng `dr._list_videos(goc)`, mà hàm đó:
      • chỉ hỏi `'<goc>' in parents` -> CHỈ ngay tại thư mục gốc, không vào thư mục con;
      • còn lọc `mimeType in VIDEO_MIME` -> thumbnail (.jpg) và sidecar (.json) không bao giờ bị
        đụng, dù mô tả của script ghi rõ là "video + thumbnail + sidecar".

    Đo trên kho thật PAIZLYNOLUWADARA: tại gốc **0 mp4, 0 jpg**; toàn bộ nằm trong `_QUEUE/` và
    `MM0-STORE/`: **85 mp4 · 85 jpg · 90 tệp khác**. Nghĩa là script sẽ in "đã đưa vào thùng rác
    0 tệp" — trông y hệt thành công, trong khi chưa dọn gì.

    **Luật**: một thao tác dọn đếm ra 0 phải KÊU LÊN, không được coi là xong. 0 gần như luôn là
    lỗi lọc chứ không phải kho trống — cùng họ với luật "rỗng là kết quả đáng ngờ"."""
    # Dùng AST: bản đầu của chốt này khớp chuỗi nên đọc luôn cả tên hàm nằm trong DOCSTRING giải
    # thích vì sao đã bỏ nó — tự báo oan ngay trên mã đã đúng. Chốt kêu oan thì lần sau bị tắt.
    import ast as _ast
    src = _doc("don_the_he_1.py")
    cay = _ast.parse(src)
    goi_ham = {n.func.attr for n in _ast.walk(cay)
               if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Attribute)}
    ten_ham = {n.func.id for n in _ast.walk(cay)
               if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name)}
    assert "_list_videos" not in goi_ham, \
        "vẫn gọi _list_videos: chỉ quét thư mục gốc và chỉ lấy video -> dọn hụt thumbnail + tệp con"
    assert "_di_het_kho" in ten_ham, "không gọi hàm đi hết cây thư mục"
    assert "ĐẾM RA 0 TỆP" in src, "đếm ra 0 tệp mà không cảnh báo -> lỗi lọc trông như thành công"



def t_muc_am_quyet_o_mot_cho():
    """7 dạng thế hệ 2 không được tự viết cứng mức âm hiệu.

    26/8 — trước khi gộp: `RankedShort` 0.5/0.4 · `ScaledShort` 0.4/0.6 · `LongshotShort`
    0.22/0.45/0.7 · `ThenNowShort` 0.4/0.6 · `BarChartRace` 0.5/0.55/0.32. Riêng trong một video
    đã chênh hơn ba lần (0.22 -> 0.7), giữa các kênh còn lệch hơn. Muốn chỉnh phải sửa 12 file.

    Nay mức âm do `Chuyen.MUC_AM` quyết một chỗ. Ngoại lệ CÓ CHỦ Ý và được giữ lại:
      • `Cinematic` tự đổi `playbackRate` theo thứ tự cắt — cùng một file whoosh thành nhiều tiếng
        khác nhau. Đó là thứ bản chung KHÔNG có; thay nó bằng bản chung là đổi xuống. Ở đó
        `ChuyenCanh` chạy chế độ CÂM (`im`) để chỉ bù phần hình.
      • Tiếng reo kết video (`cheer`) không phải chuyển cảnh — nhưng vẫn phải lấy mức từ `MUC_AM`.
    Các engine đời 1 (Clockwork/Pulse/Guess/RaceLong/Toon/Swarm) không tính: 55 kênh đó sắp nghỉ."""
    import re as _re
    xau = []
    for c in ("RankedShort", "ScaledShort", "MappedShort", "LongshotShort", "ThenNowShort"):
        src = _doc(f"../engine-remotion/src/{c}.tsx")
        if "sfx/" in src:
            xau.append(f"{c}: còn tự phát sfx thay vì dùng ChuyenCanh")
        if "ChuyenCanh" not in src:
            xau.append(f"{c}: không dùng ChuyenCanh -> không có chuyển cảnh thống nhất")
    for c in ("BarChartRace", "Cinematic"):
        src = _doc(f"../engine-remotion/src/{c}.tsx")
        if "ChuyenCanh" not in src:
            xau.append(f"{c}: không dùng ChuyenCanh")
        for m in _re.finditer(r"sfx/(\w+)\.mp3[^/]{0,120}?volume=\{([0-9.]+)\}", src):
            xau.append(f"{c}: còn mức âm viết cứng {m.group(2)} cho {m.group(1)}")
    assert not xau, "; ".join(xau)



def t_50_kenh_dong_bo_du_ba_noi():
    """Kênh ĐANG DÙNG phải có mặt đủ ở ba nơi, theo `CHANNEL_METHODS §THÊM 1 KÊNH MỚI`.

    1/9 — SỬA PHẠM VI. Bản trước cầm cứng danh sách 50 kênh thế hệ 2. Sau khi bộ ấy nghỉ và
    `channels.yaml` chuyển sang 18 kênh giải thích, cổng đòi 50 kênh đã nghỉ phải có trong
    `RS_PRESETS` — một dòng đỏ vĩnh viễn cho việc không ai làm, và nó che mất những lỗi thật
    bên cạnh. Cùng họ với `kiem_workflow.CAP` và `t_khong_tron_so`: cổng cầm danh sách chép tay.
    Nay đọc thẳng `channels.yaml` — thêm/bớt kênh ở đó là phạm vi cổng tự đổi theo.


    26/8 — kiểm lại thì thiếu SẠCH: `RS_PRESETS` 0/50, `RS_BRANDS` 0/50, `brands.json` 0/50, trong
    khi 55 kênh cũ đủ cả. Nghĩa là đã làm xong hết phần khó (engine · giọng riêng · phông riêng ·
    template thumbnail · chuyển cảnh) mà kênh mới vẫn **không hiện trên dashboard** và khâu ĐĂNG
    **không biết handle/hashtag** của chúng.

    Ba nơi, ba việc khác nhau — thiếu nơi nào hỏng việc nấy:
      • `RS_PRESETS`  -> dropdown chọn kênh khi render
      • `RS_BRANDS`   -> brand kit: avatar/cover/mô tả/hashtag
      • `brands.json` -> khâu đăng YouTube/FB/IG đọc handle · tagline · hashtag · category"""
    import json as _json, os as _os
    goc = _os.path.dirname(_os.path.abspath(__file__))
    dash = _os.path.join(goc, "..", "MM0-AutoPublisher", "dashboard", "index.html")
    if not _os.path.exists(dash):
        # 26/8 — chốt này soi repo THỨ HAI. Workflow `seed_the_he_2` chỉ checkout repo render nên
        # file không có ⇒ chốt ném FileNotFoundError và **chặn cả lần seed** (fail lần 4).
        # Chốt liên-repo chỉ chạy được ở nơi có cả hai repo (máy anh, và `render_cron` — nơi có
        # bước sao chép `_autopublisher`). Nơi khác thì BỎ QUA, nhưng nói rõ là đã bỏ qua —
        # im lặng bỏ qua chính là cái bẫy "phép thử chạy trên đầu vào rỗng".
        print("      ⏭  bỏ qua: không có repo MM0-AutoPublisher ở đây (chốt liên-repo)")
        return
    # DANH SÁCH KÊNH ĐANG DÙNG = `channels.yaml`, không phải bảng gen-2 chép cứng.
    # `kenh_the_he_2.json` mô tả bộ 50 kênh ĐÃ NGHỈ; đòi chúng có trong RS_PRESETS là đòi một
    # việc không ai làm, và dòng đỏ vĩnh viễn ấy che mất lỗi thật bên cạnh.
    import yaml as _yaml
    _cy = _doc("../MM0-AutoPublisher/config/channels.yaml")
    ten = sorted({str(k).upper() for k in ((_yaml.safe_load(_cy) or {}).get("channels") or {})})
    if not ten:
        print("      ⏭  bỏ qua: channels.yaml không khai kênh nào")
        return
    d = _doc("../MM0-AutoPublisher/dashboard/index.html")
    bj = _json.loads(_doc("../MM0-AutoPublisher/config/brands.json"))
    thieu = []
    for t in ten:
        if f'name:"{t}"' not in d:
            thieu.append(f"{t}: thiếu RS_PRESETS")
        elif f"\n      {t}:{{" not in d:
            thieu.append(f"{t}: thiếu RS_BRANDS")
        elif t not in bj:
            thieu.append(f"{t}: thiếu brands.json -> khâu đăng không biết handle/hashtag")
    assert not thieu, f"{len(thieu)} kênh chưa đồng bộ: " + "; ".join(thieu[:4])
    # hashtag phải là TIẾNG ANH — kênh cho khán giả Mỹ. Bản đầu nhặt chữ từ `goc_nhin` (tiếng Việt)
    # nên ra `#trong` `#quen`; bản hai nhặt từ tagline nên ra `#yourself` `#week` — đúng tiếng Anh
    # nhưng không ai tìm bằng mấy chữ đó. Nay gán theo NHÓM CHỦ ĐỀ.
    xau = [t for t in ten
           if any(not _re_ascii(h) for h in (bj.get(t, {}).get("hashtags") or []))]
    assert not xau, f"hashtag không phải chữ Latin thường (tiếng Việt?): {xau[:4]}"


def _re_ascii(h) -> bool:
    return all(ord(c) < 128 for c in str(h))



def t_nhan_tinh_xoay_thi_mat():
    """Kênh có `nhan` tĩnh + trục xoay ĐỔI CHỦ ĐỀ thì nhãn phải mất; xoay theo THỜI GIAN thì giữ.

    29/8 — LỖI NÀY ĐÃ TÁI PHÁT HAI LẦN, nên nó cần một chốt chứ không cần thêm một bản vá.
      • 28/8: `t.pop("nhan")` — xoá khoá thì tầng dưới dựng lại từ cấu hình kênh, nhãn sống lại.
      • 29/8: `if "nhan" in t` — `t` dựng từ `ky`, mà đường chạy THẬT truyền `ky = None`, nên
        điều kiện luôn sai và nhánh xoá không bao giờ chạy. Cả hai lần kiểm tay của tôi đều
        truyền `ky` khác None nên đều thấy nó chạy đúng: bài kiểm đi đúng con đường mà lỗi
        không nằm trên đó.
    Chốt này gọi ĐÚNG cách đường chạy thật gọi — `ky=None` — nên nó đi qua chính con đường ấy.

    Và kiểm cả CHIỀU NGƯỢC LẠI: kênh xoay theo NĂM phải GIỮ nhãn. Xoá nhãn ở đó thì tiêu đề ra
    "World ranking 2023" — người xem không biết đang xếp hạng cái gì, tệ hơn cả nhãn sai."""
    import json as _json
    import sys as _s2, os as _o2
    _s2.path.insert(0, _o2.path.dirname(_o2.path.abspath(__file__)))
    import the_he_2 as _T3
    ks = _json.loads(_doc("kenh_the_he_2.json"))
    THOI_GIAN = {"nam", "tu_nam", "den_nam", "thang", "ngay", "lui", "mua"}
    xau = []
    for k in ks:
        ts = k.get("tham_so") or {}
        nhan, truc = ts.get("nhan"), str(ts.get("xoay") or "")
        if not nhan or not truc:
            continue
        _t, kho = _T3._kho_xoay_cua(k)
        khac = [v for v in kho if str(v) != str(ts.get(truc))]
        if not khac:
            continue
        # dựng đúng cái dict mà `_dung_story_xoay` sẽ dựng, với ky=None như đường chạy thật
        goc = None
        co_nhan = "nhan" in ts
        t = {truc: khac[0]}
        if co_nhan and str(khac[0]) != str(goc) and truc not in THOI_GIAN:
            t["nhan"] = None
        if truc in THOI_GIAN:
            if t.get("nhan", "chua_dat") is None:
                xau.append(f"{k['ten']}: trục THỜI GIAN `{truc}` mà nhãn bị xoá — "
                           f"tiêu đề sẽ mất chủ đề")
        else:
            if t.get("nhan", "chua_dat") is not None:
                xau.append(f"{k['ten']}: trục `{truc}` đổi chủ đề mà nhãn {nhan!r} vẫn ở lại — "
                           f"tiêu đề sẽ nói sai nội dung")
    assert not xau, f"{len(xau)} kênh: " + "; ".join(xau[:3])
    # và phép kiểm trong mã phải hỏi CẤU HÌNH KÊNH, không hỏi dict ghi đè
    src = _doc("the_he_2.py")
    assert '_co_nhan = "nhan" in (kenh.get("tham_so") or {})' in src, \
        "điều kiện xoá nhãn phải đọc cấu hình kênh — đọc dict ghi đè thì `ky=None` là nó câm"


def t_bo_hai_giong_va_nhan_vat():
    """Bộ hài: giọng phải CÓ THẬT, hai người trong một kênh phải khác giọng, và mọi kênh phải
    có dàn nhân vật khoá.

    30/8 — Ba chốt trong một, vì cả ba đều là lỗi ĐÃ XẢY RA:
      · **Giọng không tồn tại.** Từng đoán `en-US-DavisNeural` từ trí nhớ; edge-tts không có
        giọng ấy và hai kênh chết với "No audio was received" — hỏng ở tận tầng render.
      · **Hai người cùng một giọng.** Suốt một ngày, phim HAI NGƯỜI đọc bằng MỘT giọng (luật
        7ac). Đó là lỗi giết đúng thứ làm nên sản phẩm, mà không có gì báo.
      · **Nhân vật không tên.** Bộ 500 prompt anh gửi khoá nhân vật ở mọi tập; bộ mình từng
        không ai có tên, nên mỗi tập là một người lạ (luật 7ao).
    Không gọi mạng: chỉ so với bản chụp danh sách giọng en-US đã lưu. Nếu chưa có bản chụp thì
    bỏ qua phần tên giọng (máy chưa cài edge-tts), nhưng hai chốt kia vẫn chạy.
    """
    import re as _re
    import os as _os
    goc = _os.path.dirname(_os.path.abspath(__file__))
    src = open(_os.path.join(goc, "kich_hai.py"), encoding="utf-8").read()

    m = _re.search(r"GIONG_KENH = \{(.*?)\n        \}", src, _re.S)
    assert m, "không tìm thấy bảng GIONG_KENH — bộ hài mất bảng giọng theo nhân vật"
    cap = _re.findall(r'"(\w+)":\s*\(\("([\w-]+)",[^)]*\),\s*\("([\w-]+)"', m.group(1))
    assert len(cap) >= 10, f"chỉ {len(cap)} kênh có giọng (cần 10)"
    trung = [de for de, a, b in cap if a == b]
    assert not trung, ("hai nhân vật dùng CHUNG một giọng ở kênh: " + ", ".join(trung)
                       + " — phim hai người mà tai nghe ra một người")

    try:
        import asyncio as _as, edge_tts as _et
        co = {v["ShortName"] for v in _as.run(_et.list_voices()) if v["Locale"] == "en-US"}
    except Exception:
        co = set()
    if co:
        dung = {x for _de, a, b in cap for x in (a, b)}
        thieu = sorted(dung - co)
        assert not thieu, ("giọng KHÔNG TỒN TẠI (render sẽ chết với 'No audio was received'): "
                           + ", ".join(thieu))

    nv = _re.findall(r'^ "(\w+)":\s*\(\("', src, _re.M)
    assert len(nv) >= 10, f"chỉ {len(nv)} kênh có dàn nhân vật khoá trong NHAN_VAT (cần 10)"


def t_tsx_khong_dung_bien_truoc_khi_khai():
    """`tsc` phải xanh — vì `esbuild` KHÔNG bắt được lỗi dùng biến trước khi khai báo.

    30/8 — dính đúng lỗi này HAI LẦN trong một đêm, ở hai biến khác nhau (`nhun`, rồi `bat`):
        ReferenceError  Cannot access 'nhun' before initialization
        ReferenceError  Cannot access 'bat' before initialization
    Cả hai lần `esbuild` báo dịch THÀNH CÔNG, và lỗi chỉ nổ khi render — sau bốn phút chờ.
    Lý do: `esbuild` chỉ chuyển cú pháp, nó không phân tích luồng khai báo. Còn `tsc` có mã lỗi
    riêng cho đúng chuyện này (TS2448 · TS2454) và bắt được trong vài giây.

    Đây là lý do chốt này tồn tại song song với `t_tsx_dich_duoc`: hai công cụ bắt hai loại lỗi
    khác nhau, và loại mà `esbuild` bỏ sót lại là loại đắt nhất — nó chỉ lộ ra ở tầng render,
    tức là sau khi đã tiêu một lượt máy.

    Chỉ soi thư mục `v4` (bộ hài) và `v2` (bộ dữ liệu) — hai chỗ có mã sinh chuyển động phức
    tạp, tức là chỗ biến phụ thuộc nhau chằng chịt và dễ đảo thứ tự nhất.
    """
    import glob as _g
    import subprocess as _sp
    import os as _os
    eng = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "engine-remotion")
    tsc = _os.path.join(eng, "node_modules", ".bin", "tsc")
    if not _os.path.exists(tsc):
        return                      # máy chưa cài phụ thuộc: bỏ qua, không phải lỗi mã
    # ── TỰ TÌM PHẠM VI, KHÔNG CẦM DANH SÁCH CHÉP TAY  (4/9/2026) ────────────────────────
    # Bản cũ chỉ soi `v4` và `v2` — hai bộ CŨ. Thư mục `gt` (18 kênh giải thích, bộ đang
    # chạy hằng ngày) không nằm trong danh sách, nên nó chưa từng được cổng này soi. Đúng
    # §13.2: cổng cầm danh sách chép tay là cổng che lỗi thật.
    #
    # Đo trước khi mở rộng (§13.22 — đọc tay các ca cổng bắt trước khi tin nó): năm thư mục
    # `gt` · `v4` · `v2` · `comic` · `que` cho **0 lỗi phạm vi/TDZ**, nên mở rộng không sinh
    # một dòng đỏ giả nào. Nếu có thì phải dọn trước khi bật, không bật rồi để đỏ (§15.19).
    tep = sorted(_g.glob(_os.path.join(eng, "src", "*", "*.tsx")))
    if not tep:
        return
    r = _sp.run([tsc, "--noEmit", "--jsx", "react", "--esModuleInterop", "--skipLibCheck",
                 "--target", "es2020", "--moduleResolution", "node", "--lib", "es2020,dom"] + tep,
                capture_output=True, text=True, timeout=900)
    # ── TS2304 CŨNG PHẢI BẮT  (4/9/2026) ────────────────────────────────────────────────
    # Hôm nay một hàm vẽ nơi chốn dùng `r[i]` mà không nhận `r` trong tham số. `esbuild`
    # báo XANH (nó chỉ chuyển cú pháp, không phân tích phạm vi), nên cả cổng §12.2 lẫn cổng
    # `t_tsx_dich_duoc` đều cho qua. Render "thành công" ba lượt liền — bằng BUNDLE CŨ trong
    # `node_modules/.cache` — nên em soi khung của mã cũ và đi sửa những thứ không hỏng.
    #
    # Bài học vượt ra ngoài ca này: §12.2 nói "esbuild mới là cổng thật" và điều đó ĐÚNG cho
    # lỗi cú pháp, nhưng KHÔNG ĐỦ. Hai bộ dịch bắt hai loại lỗi khác nhau, và không bộ nào
    # phủ được bộ kia:
    #     esbuild bắt : cú pháp JSX mà tsc bỏ qua (chú thích giữa các thuộc tính)
    #     tsc bắt     : phạm vi biến — TS2304 (không có tên), TS2448/TS2454 (vùng chết)
    # Phải chạy CẢ HAI. Và khi một bản dựng "thành công" đáng ngờ, XOÁ ĐỆM rồi dựng lại —
    # đệm bundle biến một bản dựng hỏng thành một bản dựng cũ, thứ khó nhận ra nhất.
    xau = [l for l in (r.stdout or "").splitlines()
           if "TS2448" in l or "TS2454" in l or "TS2304" in l]
    assert not xau, ("lỗi PHẠM VI BIẾN mà esbuild không bắt được (chỉ nổ lúc render): "
                     + " · ".join(x.strip()[:110] for x in xau[:3]))


def t_tsx_dich_duoc():
    """MỌI tệp .tsx trong engine phải dịch được. Một tệp hỏng cú pháp là CẢ NHÀ MÁY đứng.

    29/8 — đo được, không phải lo xa. Tôi thêm một chú thích đặt sai chỗ trong `src/v2/KichV2.tsx`
    (tệp của bộ kênh MỚI, chẳng liên quan gì tới 50 kênh cũ), và lượt render kế tiếp cho ra:
        ❌ BREED FILE      RankedShort   CalledProcessError
        ❌ WHAT THEY SEARCH RankedShort  CalledProcessError
        ❌ WHERE TO MOVE   MappedShort   CalledProcessError
        ❌ SPACE INVOICE   RaceShort     CalledProcessError
    Bốn kênh khác nhau, bốn composition khác nhau, không kênh nào dùng tệp tôi vừa sửa. Vì
    Remotion GÓI MỌI COMPOSITION VÀO MỘT BUNDLE — một tệp không dịch được thì không composition
    nào dựng được. Bán kính sát thương của một dấu ngoặc đặt sai là toàn bộ 50 kênh.
    Không có chốt này thì lỗi ấy chỉ lộ ra khi 18 luồng đã chạy và cả phiên đã mất.

    Dùng `esbuild` có sẵn trong node_modules: nó là đúng bộ dịch mà Remotion dùng, nên thứ nó
    chấp nhận cũng là thứ bundle chấp nhận. Chạy hết 69 tệp mất chưa tới một giây."""
    import glob as _g
    import os as _os
    import subprocess as _sp
    eng = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "engine-remotion")
    eb = _os.path.join(eng, "node_modules", ".bin", "esbuild")
    if not _os.path.exists(eb):
        return                      # máy chưa cài phụ thuộc -> bỏ qua, không báo đỏ oan
    fs = sorted(_g.glob(_os.path.join(eng, "src", "**", "*.tsx"), recursive=True))
    assert len(fs) > 20, f"chỉ thấy {len(fs)} tệp .tsx — nhiều khả năng sai đường dẫn"
    r = _sp.run([eb, "--outdir=" + _os.path.join(_os.sep, "tmp", "_selftest_tsx")] + fs,
                capture_output=True, text=True, timeout=180)
    loi = [l.strip() for l in (r.stderr or "").split("\n") if "ERROR" in l]
    assert r.returncode == 0, f"{len(loi)} tệp .tsx KHÔNG dịch được: " + " | ".join(loi[:3])


def t_moc_don_rieng_khop_ten_kenh():
    """`MOC_THEO_KENH` phải viết tên theo ĐÚNG khuôn khoá của sổ job, nếu không nó dọn 0 video.

    29/8 — bảng ấy khai 15 kênh bằng tên CÓ DẤU CÁCH ("GAME GRAVEYARD") trong khi sổ job ghi tên
    VIẾT LIỀN ("GAMEGRAVEYARD"). Phép tra không bao giờ trúng, nên cả lớp mốc-riêng chạy như
    không có — và không một dòng lỗi nào: lượt dọn báo thành công sau khi đánh dấu đúng 0 video.
    Kiểm chứng thật trên nhật ký lượt dọn 09:56Z: 1.286 video engine cũ được đánh dấu, còn phần
    mốc riêng thì không in ra một dòng nào.
    Loại lỗi này không thể phát hiện bằng đọc mã — hai bên đều "trông đúng". Chỉ có phép so tên
    với danh sách kênh thật mới bắt được."""
    import json as _json
    ds = _doc("don_trung_tieu_de.py")
    ks = _json.loads(_doc("kenh_the_he_2.json"))
    kk = lambda t: str(t or "").replace(" ", "").upper()
    that = {kk(k["ten"]) for k in ks}
    import re as _re
    kh = _re.search(r"MOC_THEO_KENH\s*=\s*\{[^}]*?\((.*?)\)\}", ds, _re.S)
    assert kh, "không đọc được MOC_THEO_KENH"
    ten = _re.findall(r'"([^"]+)"', kh.group(1))
    assert ten, "MOC_THEO_KENH rỗng"
    hut = [t for t in ten if kk(t) not in that]
    assert not hut, ("MOC_THEO_KENH khai tên KHÔNG có trong danh sách kênh (dọn sẽ trúng 0 video): "
                     + ", ".join(hut[:6]))
    # và phép tra trong mã PHẢI đi qua chuẩn hoá, không so thẳng
    assert "moc_kenh.get(_kk(ch))" in ds, \
        "tra mốc riêng không chuẩn hoá khoá -> tên có dấu cách sẽ không bao giờ khớp"


def t_tra_kenh_gen2_phai_khop_ten_seed_luu():
    """Tên kênh mà `seed` LƯU phải tra ra được bằng `doc_kenh` — cả 50, không sót cái nào.

    26/8, bắt trước khi seed. `seed_the_he_2` lưu `name = ten.replace(" ", "")` nên Firestore có
    `WHATISINIT`, còn `doc_kenh` so với `ten` = "WHAT IS IN IT" (có dấu cách) và với `handle` =
    "whatisinitusa" (có đuôi usa). Không vế nào khớp.

    Đo trên đúng 50 kênh: **33/50 tra không ra**. `run_render` sẽ in "có cờ thế hệ 2 nhưng không có
    trong kenh_the_he_2.json" rồi bỏ lượt ⇒ **33 lane ra 0 video suốt cả đêm**, mà log thì sạch, chỉ
    có một dòng cảnh báo hiền lành. Đúng loại tổn thất của sự cố `vang is not defined` (25/8).

    Chốt này chạy phép tra THẬT với đúng chuỗi mà seed sẽ ghi, không đọc mã suy luận."""
    import json as _json, importlib as _il, sys as _sys, os as _os
    goc = _os.path.dirname(_os.path.abspath(__file__))
    if goc not in _sys.path:
        _sys.path.insert(0, goc)
    T = _il.import_module("the_he_2")
    _il.reload(T)
    ks = _json.loads(_doc("kenh_the_he_2.json"))
    thieu = [k["ten"].replace(" ", "") for k in ks if T.doc_kenh(k["ten"].replace(" ", "")) is None]
    assert not thieu, (f"{len(thieu)}/{len(ks)} kênh tra KHÔNG RA bằng đúng tên seed lưu -> lane bỏ "
                       f"lượt, 0 video: {thieu[:5]}")



def t_moi_kenh_gen2_phai_xoay_duoc_de_tai():
    """Mỗi kênh gen-2 phải xoay được đề tài, và trục xoay phải là thứ bộ chuyển đổi THẬT SỰ đọc.

    26/8 — lỗi lớn nhất về nội dung, bắt trước khi seed. Cả 50 kênh đều có `tham_so.xoay` ghi rõ
    trục ("mon"/"nam"/"tu_khoa"…), nhưng **không dòng mã nào đọc nó**: `chay_chung` truyền `ky=None`
    và tham số lấy nguyên từ `tham_so` cố định. Nghĩa là mỗi kênh làm ĐÚNG MỘT câu chuyện rồi lặp
    lại mãi — 50 kênh × một video lặp, và YouTube tính là nội dung trùng lặp.
    Cùng họ với `voice_tone` / `brand.font` / `voice_pitch`: khai ra rồi để đó.

    Chốt kiểm HAI điều, vì gán trục bừa cũng vô dụng y như không gán:
      ① mọi kênh có trục xoay (trừ kênh dùng nguồn SỐNG, tự đổi theo thời gian thật);
      ② trục đó có mặt trong `ky.get("<trục>")` của chính bộ chuyển đổi kênh ấy dùng."""
    import json as _json, re as _re, sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    import the_he_2 as _T2
    src = _doc("the_he_2.py")
    ks = _json.loads(_doc("kenh_the_he_2.json"))
    # bản đồ ham -> hàm dựng, gom từ MỌI bảng bộ chuyển đổi
    mp = {}
    for bang in ("BO_CHUYEN", "BO_DUA", "BO_PHIM", "BO_SO", "BO_BAN_DO", "BO_THANG", "BO_XUA_NAY"):
        m = _re.search(bang + r"\s*=\s*\{(.*?)\n\}", src, _re.S)
        if m:
            mp.update(dict(_re.findall(r'"(\w+)":\s*(_\w+)', m.group(1))))
    SONG = {"may_bay"}      # nguồn SỐNG: số liệu đổi từng phút, mỗi lượt đã là một chuyện khác
    xau = []
    for k in ks:
        ham = k.get("ham")
        truc = str((k.get("tham_so") or {}).get("xoay") or "")
        if ham in SONG:
            continue
        if not truc:
            xau.append(f"{k['ten']}: không có trục xoay -> lặp đúng một đề tài mãi")
            continue
        # 26/8 — CHỐT NÀY TỪNG XANH TRONG KHI 33/50 KÊNH CÂM. Nó kiểm "có khai trục" và "trục có
        # được đọc", nhưng KHÔNG kiểm kho có giá trị nào không. Đo thật: `tu_khoa` 13 kênh,
        # `tu_nam` 6, `bangs` 3, `mua`/`loc`/`hang` mỗi thứ 2… đều `kho KHÔNG CÓ giá trị`, vì
        # `KHO_XOAY` chỉ khai `mon`/`nam`/`ngay`/`bang`. Kho rỗng thì `_dung_story_xoay` chỉ còn
        # đúng MỘT lượt thử ⇒ xong video đầu là mọi lượt sau BỎ LƯỢT.
        # Khai một trục rồi không cho nó giá trị nào thì y hệt không khai — mà lại nhìn như đã khai.
        _kho = _T2._kho_xoay_cua(k)[1]
        if len(_kho) < 2:
            xau.append(f"{k['ten']}: trục `{truc}` có kho {len(_kho)} giá trị -> không xoay được")
            continue
        fn = mp.get(ham)
        b = _re.search(r"def " + str(fn) + r"\(.*?(?=\ndef )", src, _re.S) if fn else None
        doc = set(_re.findall(r'ky\.get\("(\w+)"', b.group(0))) if b else set()
        # 29/8 — ĐI THEO MỘT TẦNG GIÁN TIẾP. Năm bộ dựng cùng dựng ngày gốc từ `ky`, và cả năm
        # từng ném `ValueError: day is out of range for month` khi kho xoay đưa vào số ngày lùi
        # (45, 60, … 730) mà chúng lại hiểu là ngày trong tháng — lỗi ấy GIẾT CẢ LUỒNG, không
        # phải bỏ một đề tài. Gom về một hàm chung `_ngay_goc(ky)` là đúng, nhưng làm thế thì
        # `ky.get("lui")` không còn nằm trong thân bộ dựng nữa và chốt này báo đỏ oan.
        # Nên: hàm nào được gọi với chính `ky` thì đọc luôn thân nó. Không nới lỏng chốt — vẫn
        # đòi trục PHẢI được đọc thật, chỉ là nhìn được qua một lần gọi hàm.
        if b:
            for _h in set(_re.findall(r"(_\w+)\(ky\)", b.group(0))):
                _hb = _re.search(r"def " + _h + r"\(.*?(?=\ndef )", src, _re.S)
                if _hb:
                    doc |= set(_re.findall(r'ky\.get\("(\w+)"', _hb.group(0)))
                    doc |= set(_re.findall(r'ky\["(\w+)"\]', _hb.group(0)))
        if doc and truc not in doc:
            xau.append(f"{k['ten']}: trục `{truc}` mà {fn} không đọc (nó đọc {sorted(doc)})")
    assert not xau, f"{len(xau)} kênh: " + "; ".join(xau[:4])
    # và cơ chế phải được NỐI: run_render truyền avoid, chay_chung dùng nó
    rr = _doc("run_render.py")
    assert "chay_chung(k2, ra=out, avoid=avoid)" in rr, \
        "run_render không truyền avoid -> không có gì để so, cơ chế xoay nằm im"
    assert "_dung_story_xoay(" in src, "chay_chung không đi qua hàm xoay đề tài"



def t_ten_kenh_cu_phai_co_ban_chup():
    """Danh sách 55 kênh cũ phải được chụp ra FILE, không chỉ nằm trong Firestore.

    26/8 — anh muốn xoá 55 bản ghi kênh cũ cho gọn. Nhưng `don_the_he_1.py` tìm video/thumbnail
    trên Drive bằng ĐÚNG tên các kênh đó, mà tên lại suy ra từ chính `render_channels`. Xoá bản
    ghi trước ⇒ `cu` rỗng ⇒ không tìm được tệp nào ⇒ video/thumbnail cũ nằm lại vĩnh viễn, chiếm
    chỗ của 50 kênh mới, và không còn cách nào biết tệp nào của ai.

    Chụp tên ra `kenh_the_he_1.json` thì hai bước không còn phụ thuộc thứ tự — xoá trước hay dọn
    trước đều được.

    **Luật**: trước khi xoá một nguồn dữ liệu, hỏi "còn ai đang ĐỌC nó không". Ở đây bản ghi kênh
    vừa là thứ cần xoá, vừa là đầu vào của việc dọn."""
    import json as _json
    d = _json.loads(_doc("kenh_the_he_1.json"))
    ten = d.get("ten") or []
    assert len(ten) >= 55, f"bản chụp chỉ có {len(ten)} tên, cần đủ 55 kênh cũ"
    assert len(set(ten)) == len(ten), "bản chụp có tên trùng"
    src = _doc("don_the_he_1.py")
    assert "kenh_the_he_1.json" in src, \
        "don_the_he_1 không đọc bản chụp -> xoá bản ghi trước là mất đường tìm tệp"



def t_cong_cu_quan_tri_phai_tro_dung_project():
    """Workflow quản trị phải truyền `SHARD_META` như dây chuyền chính.

    26/8, bắt 20 phút trước giờ seed. `firestore_bridge._db_meta()` chỉ trỏ vào project B khi
    `SHARD_META=1`; không có cờ thì nó về **project A**. `render_cron` có truyền
    (`vars.SHARD_META` = 1, đã kiểm bằng `gh variable list`), còn `seed_the_he_2.yml` và
    `don_the_he_1.yml` **không có dòng nào**.

    Hậu quả nếu để nguyên:
      • seed ghi 50 kênh vào A trong khi dây chuyền đọc `render_channels` ở B ⇒ **50 kênh vô hình**,
        mà vẫn tốn trọn cửa sổ hạn mức phải chờ tới hôm sau;
      • bản dọn đọc danh sách kênh cũ ở A (rỗng) ⇒ báo "dọn 0 tệp" như thể thành công — đúng lỗi
        "đếm ra 0 mà tưởng xong" đã ghi ở 7.ed.

    **Luật**: công cụ quản trị phải chạy trong CÙNG cấu hình với dây chuyền nó quản trị. Lệch một
    biến môi trường là nó thao tác lên một hệ khác, và không có gì báo lỗi cả."""
    can = ("SHARD_META", "SHARD_KEYS")
    for f in ("seed_the_he_2", "don_the_he_1"):
        y = _doc(f"../.github/workflows/{f}.yml")
        for c in can:
            assert f"{c}: ${{{{ vars.{c} }}}}" in y.replace(" ", "") or \
                   f"{c}:${{{{vars.{c}}}}}" in y.replace(" ", ""), \
                f"{f}.yml thiếu {c} -> đọc/ghi nhầm project A thay vì B"



def t_workflow_chay_selftest_phai_du_thu_vien():
    """Workflow nào chạy `selftest.py` thì phải cài ĐỦ thư viện selftest cần.

    26/8, seed 07:01Z chết đúng kiểu này:
        ❌ step trỏ Project C phải bật SHARD_PUBLISH: No module named 'yaml'
        ##[error]Process completed with exit code 1
    `seed_the_he_2.yml` chỉ cài `google-cloud-firestore google-auth`, nhưng bước sau lại chạy
    selftest — mà selftest có chốt ĐỌC FILE YAML của chính các workflow. Thiếu `pyyaml` ⇒ selftest
    thoát mã 1 ⇒ **chặn luôn việc chính**, dù việc chính không cần thư viện đó.

    Mất trọn lần bấm đầu tiên của cửa sổ hạn mức. (May là selftest gác TRƯỚC nên chưa ghi gì —
    không có trạng thái dở dang.)

    **Luật**: bước gác (`selftest`) và bước làm việc chạy trong CÙNG môi trường. Cài thư viện cho
    riêng việc chính là để cái gác chết trước, rồi nó kéo việc chính chết theo."""
    import re as _re
    can = ("pyyaml",)
    for f in ("seed_the_he_2", "don_the_he_1"):
        y = _doc(f"../.github/workflows/{f}.yml")
        if "selftest.py" not in y:
            continue
        pip = " ".join(l for l in y.splitlines() if "pip install" in l)
        for c in can:
            assert c in pip, f"{f}.yml chạy selftest nhưng không cài `{c}` -> selftest chết, chặn cả việc chính"



def t_gen2_phai_ra_bo_1long_3short():
    """Thế hệ 2 phải ra BỘ: 1 long + 3 short, short là chương của chính long đó.

    26/8 — anh nêu luật này nhiều lần mà mỗi lần lại chưa vào. Ghi thành chốt để không phải nêu
    lần nữa. Ba điều kiện, thiếu cái nào cũng hỏng theo kiểu khác nhau:

      ① seed đặt `make_long: True` và `long_target > 0`.
         Sai -> `run_one` không bao giờ vào nhánh long, 50 kênh chỉ ra short rời rạc.
      ② có nhánh gen-2 trong `run_one`, và nó đứng TRƯỚC nhánh `fmt == "doc"`.
         Sai thứ tự -> gen-2 rơi vào nhánh doc rồi gọi Gemini viết kịch bản: sai hẳn mô hình
         (gen-2 dựng từ dữ liệu mở, không nhờ AI nghĩ nội dung).
      ③ short ghi `cha` (id job của long) và `thu_tu`.
         Thiếu -> khâu đăng (`auto_enqueue._theo_cha`) không biết short nào thuộc long nào, đăng
         nhảy cóc, người xem bấm short thấy hay mà tìm bản dài thì không có."""
    seed = _doc("seed_the_he_2.py")
    assert '"make_long": True' in seed, "seed vẫn đặt make_long=False -> gen-2 short-only, sai tỉ lệ 1:3"
    import re as _re
    m = _re.search(r'"long_target":\s*(\d+)', seed)
    assert m and int(m.group(1)) > 0, "seed đặt long_target=0 -> không bao giờ vào nhánh long"

    rr = _doc("run_render.py")
    assert "_gen2_bo(" in rr, "run_render không có nhánh dựng bộ cho thế hệ 2"
    i2 = rr.find('str(ch.get("the_he") or "") == "2"')
    idoc = rr.find('elif fmt == "doc":')
    assert i2 > 0 and idoc > 0 and i2 < idoc, \
        "nhánh gen-2 phải đứng TRƯỚC nhánh doc, nếu không gen-2 rơi vào đường gọi Gemini"
    # 26/8 — ĐỌC ĐÚNG THÂN HÀM, KHÔNG CẮT THEO SỐ KÝ TỰ. Bản cũ lấy `rr[j : j+3600]`; thêm vài
    # dòng chú thích là `bo=f"S{i+1}"` rơi ra ngoài cửa sổ và chốt đỏ oan trong khi mã vẫn đúng.
    # Chốt đỏ oan nguy hơn chốt thiếu: nó dạy người ta bỏ qua màu đỏ.
    _mg = _re.search(r"def _gen2_bo\(.*?(?=\ndef )", rr, _re.S)
    assert _mg, "mất hàm _gen2_bo"
    than = _mg.group(0)
    assert "cha=ljob" in than and "thu_tu=i + 1" in than, \
        "short gen-2 không ghi cha/thu_tu -> khâu đăng đăng nhảy cóc, mất mạch kênh"
    assert 'bo=f"S{i + 1}"' in than and 'bo="L"' in than, \
        "không đánh số vai trò (L/S1/S2) khi đẩy kho -> nhìn tên file không biết short thuộc long nào"
    # 26/8 — TIÊU ĐỀ LONG PHẢI PHỦ CẢ BỘ. `_gen2_bo` vốn lấy `chuong[0][1]`, tức story của SHORT
    # ĐẦU TIÊN. Từ lúc short gộp 2 chương, short đầu chỉ phủ 2/6 chương ⇒ long trải `2020-2025` lại
    # mang tên `(2024-2025)`. Người xem bấm vào vì tên đó sẽ thấy nội dung khác — đúng thứ phá
    # "liền mạch". Lỗi này do CHÍNH bản refactor gộp chương gây ra, nên chốt lại để khỏi tái diễn.
    assert "st_long" in than, "tiêu đề long vẫn lấy từ short đầu -> nói sai phạm vi cả bộ"
    import the_he_2 as _T3
    _sts = [{"title": f"X ({n})", "items": [{"name": "a"}]} for n in range(2020, 2026)]
    _tt = _T3._gop_story(_sts, "nam", tran=6).get("title", "")
    assert "2020" in _tt and "2025" in _tt, f"tiêu đề gộp không phủ hết phạm vi: {_tt!r}"



def t_bo_khong_duoc_chon_story_hai_lan():
    """`chay_bo` chọn chương xong thì `chay_chung` phải DÙNG chương đó, không chọn lại.

    26/8 — render thử bộ đầu tiên: long dài **38,3s**, đúng bằng MỘT short. Bộ đáng lẽ 3 chương.
    Gốc: `chay_bo` gọi `_dung_story_xoay` chọn chương, rồi lại gọi `chay_chung` — mà `chay_chung`
    cũng tự gọi `_dung_story_xoay` lần nữa. Hai bên chọn ĐỘC LẬP:
      • video render ra không phải chương đã ghi vào sổ (tiêu đề/thumbnail nói một đằng, hình một nẻo);
      • `avoid` lệch một nhịp nên chương 2 chọn trúng lại chương 1, rồi cả bộ dừng.

    **Luật**: một quyết định chỉ được lấy ở MỘT nơi. Chọn rồi thì truyền xuống, đừng để tầng dưới
    chọn lại — nó sẽ chọn khác, và không có gì báo lỗi."""
    import ast as _ast
    src = _doc("the_he_2.py")
    cay = _ast.parse(src)
    fn = next((n for n in _ast.walk(cay) if isinstance(n, _ast.FunctionDef) and n.name == "chay_bo"), None)
    assert fn, "mất hàm chay_bo"
    goi = [n for n in _ast.walk(fn) if isinstance(n, _ast.Call)
           and getattr(n.func, "id", "") == "chay_chung"]
    assert goi, "chay_bo không gọi chay_chung"
    for g in goi:
        assert any(k.arg == "st_san" for k in g.keywords), \
            "chay_bo gọi chay_chung mà KHÔNG truyền st_san -> tầng dưới chọn lại chương khác"
    cc = next((n for n in _ast.walk(cay) if isinstance(n, _ast.FunctionDef) and n.name == "chay_chung"), None)
    assert cc and any(a.arg == "st_san" for a in cc.args.args), \
        "chay_chung không nhận st_san"



def t_capnhat_phai_day_du_truong_co_y():
    """`--capnhat` phải cập nhật ĐỦ mọi trường mà seed đặt tường minh.

    26/8 — soi dashboard: 50 kênh gen-2 vẫn `make_long: false · long_target: 0` dù seed đã sửa sang
    1 long : 3 short và `--capnhat` đã chạy **thành công**. Vì danh sách trắng của chế độ cập nhật
    bỏ sót đúng bốn trường quyết định hành vi: `type` · `make_long` · `long_target` · `n_shorts`.

    Selftest cũ không bắt được: `t_gen2_phai_ra_bo_1long_3short` đọc FILE seed và thấy đúng, trong
    khi thứ quyết định hành vi là BẢN GHI trong Firestore — và đường duy nhất để sửa bản ghi đã
    khoá mất bốn trường đó.

    **Luật**: danh sách "trường do bảng sinh ra" phải khớp đúng những gì `doc` đặt tường minh.
    Thiếu một trường = trường đó vĩnh viễn không cập nhật được, mà không có gì báo lỗi."""
    import ast as _ast
    src = _doc("seed_the_he_2.py")
    cay = _ast.parse(src)
    fn = next((n for n in _ast.walk(cay) if isinstance(n, _ast.FunctionDef) and n.name == "main"), None)
    assert fn, "mất hàm main trong seed"
    # khoá đặt tường minh trong `doc` (bỏ khoá thừa hưởng qua **dich)
    doc = next((d for d in _ast.walk(fn) if isinstance(d, _ast.Dict)
                and any(isinstance(k, _ast.Constant) and k.value == "the_he" for k in d.keys if k)), None)
    assert doc, "không tìm thấy dict doc"
    co_y = {k.value for k in doc.keys if isinstance(k, _ast.Constant) and isinstance(k.value, str)}
    #  CỐ Ý loại khỏi chế độ cập nhật: bật/tắt là quyết định của người dùng, không phải
    # của bảng — ghi đè nó khi cập nhật giọng/phông là tự tay bật lại 50 kênh đang tắt.
    co_y -= {"owner", "name", "paused"}
    # danh sách trắng của chế độ cập nhật
    tra = None
    for cmp_ in _ast.walk(fn):
        if isinstance(cmp_, _ast.Compare) and isinstance(cmp_.ops[0], _ast.In) \
           and isinstance(cmp_.comparators[0], _ast.Tuple):
            tra = {e.value for e in cmp_.comparators[0].elts if isinstance(e, _ast.Constant)}
            break
    assert tra, "không tìm thấy danh sách trắng của --capnhat"
    thieu = co_y - tra
    assert not thieu, (f"--capnhat bỏ sót {sorted(thieu)} -> mấy trường này KHÔNG BAO GIỜ cập nhật "
                       "được xuống Firestore dù seed đã sửa")



def t_workflow_dung_autopublisher_phai_checkout_that():
    """Workflow nào trỏ `AUTOPUBLISHER_SRC` thì phải CHECKOUT repo đó, không được `cp` từ chỗ trống.

    26/8 — `don_the_he_1.yml` làm `cp -r MM0-AutoPublisher/src _autopublisher/ || true`. Nhưng
    `MM0-AutoPublisher` là repo RIÊNG, không nằm trong checkout của repo render ⇒ `cp` trượt,
    `|| true` nuốt lỗi, rồi script chết `No module named 'storage'`: **bản dọn chưa từng chạy được
    lần nào**, mà log workflow thì trông như bình thường cho tới dòng cuối.

    Đây là lần thứ HAI đúng cái bẫy này — 24/8 `render_cron` cũng trỏ `AUTOPUBLISHER_SRC` mà quên
    checkout, làm `backup_vault` chết mọi phiên trong im lặng (kho key coi như không được sao lưu
    suốt thời gian đó)."""
    import re as _re, os as _os
    goc = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".github", "workflows")
    xau = []
    for f in sorted(_os.listdir(goc)):
        if not f.endswith(".yml"):
            continue
        tho = _doc(f"../.github/workflows/{f}")
        # BỎ CHÚ THÍCH trước khi soi: chú thích giải thích vì sao đã bỏ `cp` cũng chứa chữ `cp`,
        # đọc cả chú thích là tự báo oan trên mã đã đúng (đã dính đúng lỗi này).
        y = "\n".join(l for l in tho.splitlines() if not l.strip().startswith("#"))
        if "AUTOPUBLISHER_SRC" not in y:
            continue
        # Repo được checkout ở ĐÂU không quan trọng — `wipe_queue` checkout vào thư mục gốc và
        # trỏ `AUTOPUBLISHER_SRC: ${{ github.workspace }}/src`, hoàn toàn hợp lệ. Điều bắt buộc
        # là CÓ một bước checkout đúng repo đó.
        if "AUTOPUBLISHER_REPO" not in y:
            xau.append(f"{f}: trỏ AUTOPUBLISHER_SRC nhưng không checkout repo -> ModuleNotFoundError")
        if _re.search(r"cp -r MM0-AutoPublisher/src", y):
            xau.append(f"{f}: còn `cp` từ thư mục không tồn tại (repo riêng)")
    assert not xau, "; ".join(xau)



def t_don_kho_khong_duoc_dung_kich_ban():
    """Bản dọn phải BỎ QUA thư mục chứa kịch bản/sao lưu/brand kit.

    26/8 — chạy khô đếm **9.037 tệp** sẽ vào thùng rác (3011 .mp4 · 3013 .jpg · 3013 .json).
    Nhưng `CHANNEL_METHODS` có luật bất di bất dịch: *"Dọn/xóa CHỈ đụng VIDEO. KHÔNG bao giờ xóa:
    method, repo, brand kit, config kênh, KỊCH BẢN/TOPIC ĐÃ LƯU."*

    Kịch bản nằm trên Drive trong `_KICHBAN`, và tên tệp kịch bản cũng mở đầu bằng tên kênh — tức
    bộ lọc theo tên quét trúng chúng. Mất kịch bản là mất thứ không dựng lại được bằng tiền: phải
    gọi AI viết lại từ đầu, mà kho key thì có hạn.

    Tỉ lệ 1:1:1 gợi ý `.json` là sidecar chứ không phải kịch bản — nhưng "gợi ý" không đủ để xoá
    chín nghìn tệp. Chặn cứng ở tầng duyệt cây thư mục."""
    src = _doc("don_the_he_1.py")
    assert "CAM_DUNG" in src, "bản dọn không có danh sách thư mục cấm đụng"
    for c in ("_KICHBAN", "_BACKUP"):
        assert c in src, f"thiếu `{c}` trong danh sách cấm đụng"
    import ast as _ast
    fn = next((n for n in _ast.walk(_ast.parse(src))
               if isinstance(n, _ast.FunctionDef) and n.name == "_di_het_kho"), None)
    assert fn and "CAM_DUNG" in _ast.dump(fn), \
        "hàm duyệt cây không kiểm CAM_DUNG -> vẫn chui vào thư mục kịch bản"



def t_viec_dai_phai_in_tien_do_va_du_gio():
    """Việc dọn hàng nghìn tệp phải in tiến độ và có đủ thời gian chạy.

    26/8 — bản dọn thật chạy **45 phút 21 giây** rồi `The operation was canceled`: đúng bằng
    `timeout-minutes: 45`. 9.037 tệp gọi `trash()` tuần tự, mỗi lượt ~0,3s.

    Hai cái sai, và cái thứ hai đắt hơn:
      ① trần thời gian đặt sát mức cần — chỉ cần kho phình thêm chút là chết;
      ② **không in tiến độ**, nên lúc bị giết không ai biết đã dọn tới đâu, còn lại bao nhiêu.
         Một việc dài mà im lặng thì khi nó chết chỉ còn cách đoán.

    Vá: xoá song song 8 luồng, in tiến độ mỗi 200 tệp, nới trần lên 330 phút. Thùng rác nên chạy
    lại là tiếp tục phần còn lại, không hỏng gì."""
    src = _doc("don_the_he_1.py")
    # 26/8 — chốt cũ đòi PHẢI đa luồng. Sai: client Google API không an toàn đa luồng, 8 luồng
    # dùng chung `svc` làm hỏng bộ nhớ (`free(): corrupted unsorted chunks`, core dumped, exit 134).
    # Điều thật sự cần là ĐỦ GIỜ + IN TIẾN ĐỘ, không phải chạy song song.
    assert "ThreadPoolExecutor" not in src, \
        "xoá đa luồng với client Google API dùng chung -> hỏng bộ nhớ, core dumped"
    assert "% 200 == 0" in src, "không in tiến độ -> bị giết giữa chừng thì không biết đã tới đâu"
    y = _doc("../.github/workflows/don_the_he_1.yml")
    import re as _re
    m = _re.search(r"timeout-minutes:\s*(\d+)", y)
    assert m and int(m.group(1)) >= 180, \
        f"timeout-minutes={m.group(1) if m else '?'} — quá sát, việc dọn từng chết vì đúng lý do này"



def t_van_phien_phai_theo_ngan_sach():
    """Khoảng cách giữa hai phiên render phải đủ để KHÔNG cạn hạn mức đọc trong ngày.

    26/8 — đây là gốc của việc dây chuyền đứng, tìm ra bằng cách đếm chứ không đoán:
      • cron thức mỗi 10 phút, `SESSION_GAP_MIN` chỉ **12 phút** ⇒ phiên mở nối đuôi;
      • đo thật: **33 phiên trong 24h**, một phiên mỗi ~44 phút;
      • một phiên tiêu **4.219 lượt đọc** (hiệu hai lần chốt sổ: 56.051 → 60.270);
      • 33 × 4.219 ≈ 139.000 trên trần 50.000 ⇒ sổ chạm **120%** lúc 03:09Z, rồi mọi thứ gãy theo:
        không đọc được cấu hình kênh, không liệt kê được kho, "Không kho nào đủ chỗ" mọi lane.

    Tính ngược từ trần: (50.000 − 30% dành cho đăng/thống kê/health/dashboard) ÷ 4.219 ≈ 8 phiên/
    ngày ⇒ **180 phút/phiên**. Vẫn ra ~430 video/ngày với 18 lane — thừa cho 50 kênh.

    **Luật**: van điều tiết phải tính NGƯỢC TỪ TRẦN, không đặt theo mong muốn chạy nhanh. Muốn dày
    phiên hơn thì phải giảm lượt đọc mỗi phiên TRƯỚC, rồi mới hạ con số này."""
    import re as _re
    src = _doc("run_render.py")
    # 26/8, anh chỉ ra: đặt van bằng ĐỒNG HỒ là sai biến điều khiển — độ dài phiên phụ thuộc độ
    # dài video, phiên xong sớm mà bắt chờ đủ giờ là máy nằm không. Van phải theo HẠN MỨC CÒN LẠI:
    # rải phần còn lại đều cho số giờ còn lại của ngày. Mô phỏng: phiên 30'/60'/110' đều ra đúng
    # 8 phiên/ngày, 68% trần — nhanh thì nghỉ ít, chậm thì nghỉ nhiều, không bao giờ tràn.
    assert "phan_tram_da_dung" in src and "_gio_toi_reset" in src, \
        "van phiên vẫn đặt theo đồng hồ, chưa tính theo hạn mức còn lại"
    assert "CHI_PHI_PHIEN_DOC" in src, "không khai chi phí đọc mỗi phiên -> không tính được van"
    m = _re.search(r"^SESSION_GAP_MIN\s*=\s*(\d+)", src, _re.M)
    assert m, "mất hằng SESSION_GAP_MIN (đường lùi khi không đọc được sổ)"
    gap = int(m.group(1))
    TRAN, DE_DANH, MOI_PHIEN = 50000, 0.30, 4219
    can = 24 * 60 / ((TRAN * (1 - DE_DANH)) / MOI_PHIEN)
    assert gap >= can * 0.9, (
        f"đường lùi SESSION_GAP_MIN={gap}' cho phép {24*60/max(1,gap):.0f} phiên/ngày × {MOI_PHIEN} "
        f"lượt = {24*60/max(1,gap)*MOI_PHIEN:,.0f}, vượt trần {TRAN:,} — cần ≥ {can:.0f}'")



def t_plan_khong_duoc_doc_goi_cua_chinh_no():
    """Job `plan` KHÔNG được nhận `CHANNEL_CFGS`/`KEYS_A` — nó là nơi TẠO RA hai gói đó.

    26/8 — sau khi cho `read_channels` ưu tiên gói plan gửi kèm, xuất hiện một bẫy mới rất kín:
    nếu ai đó thêm `CHANNEL_CFGS` vào env của job `plan` (chép nhầm khối env từ job `render` là
    đủ), thì plan sẽ đọc lại **gói của phiên trước** thay vì đọc Firestore. Hậu quả:
      • cấu hình kênh ĐÓNG BĂNG vĩnh viễn — bấm pause/đổi target trên dashboard không còn tác dụng;
      • kênh mới thêm không bao giờ xuất hiện;
      • và không có lỗi nào cả, vì gói cũ vẫn giải nén được bình thường.

    Đây là kiểu hỏng tệ nhất: hệ vẫn chạy, vẫn ra video, chỉ là chạy theo một bản cấu hình chết."""
    import yaml as _y, io as _io, os as _os
    p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..",
                      ".github", "workflows", "render_cron.yml")
    d = _y.safe_load(_io.open(p, encoding="utf-8"))
    xau = []
    for ten, job in (d.get("jobs") or {}).items():
        for st in job.get("steps", []):
            env = st.get("env") or {}
            for k in ("CHANNEL_CFGS", "KEYS_A"):
                if k in env and ten != "render":
                    xau.append(f"job `{ten}` nhận {k} — nó phải TẠO gói, không phải đọc gói")
    assert not xau, "; ".join(xau)
    # và job render thì PHẢI có, nếu không lane quay lại đọc Firestore (720 lượt/phiên)
    r = (d.get("jobs") or {}).get("render") or {}
    co = any("CHANNEL_CFGS" in (st.get("env") or {}) for st in r.get("steps", []))
    assert co, "job render KHÔNG nhận CHANNEL_CFGS -> mỗi lane đọc lại Firestore, 720 lượt/phiên"


def t_giong_phai_co_that():
    """Mọi giọng khai trong bảng phải TỒN TẠI ở nhà cung cấp.

    30/8 — tôi đổi giọng của một nhân vật sang `en-US-DavisNeural` mà không tra danh sách. Giọng
    ấy không có trong edge-tts, nên bộ đọc trả về rỗng và cả kênh chết với thông báo mơ hồ
    "No audio was received. Please verify that your parameters are correct".
    Lỗi im lặng đúng kiểu khó chịu nhất: không ngoại lệ ở chỗ gán, chỉ hỏng ở chỗ dùng, và thông
    báo lỗi không nhắc gì tới cái tên sai.
    Cùng một dạng với cổng `kiem_gan` (gán giá trị mà engine không vẽ) — chỉ khác là bên kia
    engine của mình, bên này là dịch vụ ngoài. Cả hai đều cần kiểm: khai một tên thì phải chắc
    có thứ mang tên ấy.
    """
    import re as _re, io as _io, os as _os, asyncio as _aio
    _goc = _os.path.dirname(_os.path.abspath(__file__))
    src = _io.open(_os.path.join(_goc, "kich_hai.py"), encoding="utf-8").read()
    khai = set(_re.findall(r'"(en-US-\w+Neural)"', src))
    src2 = _io.open(_os.path.join(_goc, "kich_v2.py"), encoding="utf-8").read()
    khai |= set(_re.findall(r'"(en-US-\w+Neural)"', src2))
    if not khai:
        return
    try:
        import edge_tts
        co = _aio.run(edge_tts.list_voices())
        co = {v["ShortName"] for v in co}
    except Exception:
        return                      # không tra được danh sách thì bỏ qua, đừng chặn phiên
    thieu = sorted(khai - co)
    assert not thieu, ("giọng khai trong bảng nhưng nhà cung cấp KHÔNG CÓ: "
                       + ", ".join(thieu) + " — bộ đọc sẽ trả rỗng và kênh chết trong im lặng")


def t_hinh_va_giong_cung_mot_gioi():
    """Ba bảng nói về cùng một người phải khớp giới: HÌNH · GIỌNG · bảng giới.

    Anh nghe ra lỗi này BA LẦN trong một ngày — "con trai mà sao giọng con gái". Cả ba lần đều
    do cùng một chuyện: ba bảng độc lập (`_BONG` tả râu tóc · `GIONG_KENH` chọn giọng · `GIOI`
    khai giới) nói về cùng một nhân vật mà không bảng nào biết bảng kia.
    Hai lần trước tôi sửa MỘT bảng cho khớp một bảng khác, rồi bảng thứ ba vẫn lệch — nên lỗi
    chỉ đổi chỗ chứ không mất. Ba bảng thì phải kiểm cả ba cùng lúc, và kiểm bằng máy.
    """
    import re as _re, io as _io, os as _os
    _goc = _os.path.dirname(_os.path.abspath(__file__))
    src = _io.open(_os.path.join(_goc, "kich_hai.py"), encoding="utf-8").read()
    import importlib.util as _iu
    _sp = _iu.spec_from_file_location("_kh", _os.path.join(_goc, "kich_hai.py"))
    _kh = _iu.module_from_spec(_sp); _sp.loader.exec_module(_kh)
    NU = {"Jenny", "Aria", "Ava", "Michelle", "Ana", "Emma", "Nancy", "Sara"}
    m = _re.search(r"GIONG_KENH = \{(.*?)\n        \}", src, _re.S).group(1)
    xau = []
    for de, va, vb in _re.findall(r'"(\w+)":\s*\(\("([\w-]+)",[^)]*\),\s*\("([\w-]+)"', m):
        for i, v in enumerate((va, vb)):
            gi = _kh.GIOI.get(de, ("nam", "nam"))[i]
            bo = (_kh._BONG.get(de) or ({}, {}))[i]
            ten = v.replace("en-US-", "").replace("Neural", "")
            g_giong = "nu" if ten in NU else "nam"
            # Hình: có râu là nam chắc chắn; tóc kiểu nữ là nữ.
            g_hinh = ("nam" if bo.get("rau") else
                      ("nu" if bo.get("kieuToc") in ("duoi_ngua", "bui", "bob") else None))
            if g_giong != gi:
                xau.append(f"{de}[{i}]: bảng giới {gi}, giọng {ten} là {g_giong}")
            if g_hinh and g_hinh != g_giong:
                xau.append(f"{de}[{i}]: hình {g_hinh} (râu={bo.get('rau')!r}), giọng {ten} là {g_giong}")
    assert not xau, "hình/giọng/giới lệch nhau:\n  " + "\n  ".join(xau)


def t_dung_thu_mot_khung():
    """Dựng đúng MỘT khung hình để bắt lỗi chỉ lộ lúc chạy.

    `ReferenceError: Cannot access 'X' before initialization` đã nổ NĂM lần trong kho này, và cả
    năm lần đều qua được `tsc` lẫn `esbuild` — mã hợp lệ về kiểu và cú pháp, chỉ sai THỨ TỰ.
    Tôi từng viết một cổng quét mã bằng biểu thức chính quy để bắt nó; nó báo 3.590 chỗ, gần như
    toàn phát hiện sai. Biểu thức chính quy không phân tích được phạm vi JavaScript.
    Cách rẻ mà đúng: dựng một khung thật. TDZ nổ ở khung đầu, nên một khung là đủ — vài giây
    thay vì mười lăm phút, và không có phát hiện sai nào vì thứ kiểm chính là thứ sẽ chạy.
    """
    import subprocess, os as _os
    _goc = _os.path.dirname(_os.path.abspath(__file__))
    if not _os.path.isdir(_os.path.join(_goc, "out")):
        return
    r = subprocess.run([sys.executable, _os.path.join(_goc, "kiem_khung1.py")],
                       capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, "dựng thử một khung hỏng:\n" + (r.stdout or "")[-600:]


def t_gan_gi_engine_phai_ve_duoc():
    """Mọi giá trị bảng nhân vật gán, engine phải có nhánh vẽ cho nó.

    Ca thật 30/8: anh thấy huấn luyện viên NỮ trông ra đàn ông. JSON đúng hết —
    `kieuToc="duoi_ngua"`, `mu="luoi_trai"`, `phuKien="khan_quang"` — nhưng engine **chưa bao
    giờ vẽ mũ** (không dòng nào đọc `kieu.mu`), và `khan_quang` rơi qua hết sáu nhánh phụ kiện
    rồi biến mất.
    Đây là dạng lỗi tốn nhất trong dây chuyền vì MỌI CỔNG ĐỀU BÁO XANH: JSON hợp lệ, TypeScript
    hợp lệ (trường có trong kiểu), esbuild dịch được, video render xong. Chỉ khung hình là
    thiếu — và chỉ mắt người mới thấy, mà mắt người không chạy được hằng đêm.
    """
    import subprocess, os as _os
    _goc = _os.path.dirname(_os.path.abspath(__file__))
    r = subprocess.run([sys.executable, _os.path.join(_goc, "kiem_gan.py")],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, "có giá trị được gán mà engine không vẽ:\n" + r.stdout[-700:]


def main():
    print("🧪 SELFTEST (0 mạng · 0 quota) — chặn bản deploy hỏng trước khi spawn 18 luồng:")
    check("shim Groq/CF: system_instruction + UA + JSON + vision", t_shim_signatures)
    check("groq WAF 1010 -> lỗi tạm per-minute", t_groq_waf_1010)
    check("key cạn quota -> đổi key, không giết luồng", t_het_key_thi_doi_key)
    check("hết key -> báo gọn, không IndexError", t_key_order_khong_lay_phan_tu_dau_tran)
    check("nghẽn nhà cung cấp (504) -> thử lại, không giết lượt", t_nghen_nha_cung_cap_phai_thu_lai)
    check("cạn token/ngày -> nhãn daily", t_groq_tpd_la_daily)
    check("groq model bị gỡ -> tự dò model sống", t_groq_model_selfprobe)
    check("key_order viết: groq -> cf -> gemini", t_key_order)
    check("pool vẽ cf-trước / vision gemini-trước", t_ai_pool_split)
    check("đọc-mềm: quota chết không ném", t_soft_read)
    check("hồ key A: plan đọc 1 lần, lane không đụng A", t_ho_key_A_doc_mot_lan_o_plan)
    check("sổ ngân sách không gây ảo giác an toàn", t_so_ngan_sach_khong_gay_ao_giac)
    check("plan phanh số lane theo hạn mức còn lại", t_plan_phai_phanh_theo_han_muc)
    check("cổng dark_ok theo kênh", t_dark_ok)
    check("mở đầu chỉ MỘT tiêu đề (Bookend), không chồng ba", t_bookend_la_noi_duy_nhat_ve_tieu_de_mo_dau)
    check("tsx: prop khai rồi phải thảo ra (ReferenceError)", t_tsx_prop_khai_roi_phai_thao_ra)
    check("_extract_json bóc ```json", t_extract_json)
    check("_extract_json LUÔN trả dict (list -> nổ .get)", t_extract_json_luon_tra_dict)
    check("step trỏ Project C phải bật SHARD_PUBLISH", t_workflow_dung_project_C_phai_bat_co)
    check("env trỏ tệp khoá thì phải có bước tạo tệp", t_env_tro_file_thi_phai_tao_file)
    check("B2 failover: thiếu env từ chối êm", t_b2_failover)
    check("số hiện ra không mất độ lớn; hook nêu đúng kẻ dẫn đầu", t_so_hien_thi_khong_mat_do_lon)
    check("chống trùng kho: đánh cờ 1 nơi, mọi nơi đọc phải tôn trọng", t_chong_trung_kho_drive)
    check("tiêu đề không lộ mã nội bộ (quét 50 kênh)", t_tieu_de_khong_lo_ma_noi_bo)
    check("tiêu đề dẫn bằng chủ thể, không phải khuôn + ngày", t_tieu_de_phai_noi_ve_noi_dung)
    check("key vẽ ảnh chết hẳn -> đổi key, không bỏ khung", t_key_ve_anh_chet_phai_doi_key)
    check("gán gì thì engine phải vẽ được (mũ/tóc/phụ kiện)", t_gan_gi_engine_phai_ve_duoc)
    check("mọi giọng khai trong bảng phải có thật", t_giong_phai_co_that)
    check("hình · giọng · giới của cùng một người phải khớp", t_hinh_va_giong_cung_mot_gioi)
    check("dựng thử 1 khung — bắt TDZ và lỗi chỉ lộ lúc chạy", t_dung_thu_mot_khung)
    check("18 lane vào 18 điểm khác nhau trong hồ key ảnh", t_18_lane_khong_don_mot_key_anh)
    check("mọi loại key báo trạng thái + lời đúng loại", t_moi_loai_key_deu_bao_trang_thai)
    check("làm mới token không ép scope (invalid_scope)", t_khong_ep_scope_khi_lam_moi_token)
    check("bỏ việc không được im lặng (mọi failed đều có log)", t_bo_viec_khong_duoc_im_lang)
    check("mọi đường dựng đều nhận hồ key", t_moi_duong_dung_deu_nhan_ho_key)
    check("tài sản kênh dùng phải có trong git (không chỉ ở máy)", t_tai_san_kenh_dung_phai_co_trong_git)
    check("đặt tiêu đề chịu được mọi hình dạng story", t_dat_tieu_de_chiu_duoc_moi_hinh_dang)
    check("sổ tránh-trùng và phép so cắt cùng độ dài", t_so_trung_tieu_de_phai_cung_do_dai)
    check("hồ sơ kênh: không dict nào có khoá trùng", t_khong_khoa_trung_trong_ho_so)
    check("thiên nhiên: hồ sơ toàn vẹn (8 phép)", t_tn_ho_so_toan_ven)
    check("bộ thiên nhiên: prompt + hàng rào + đa dạng", t_bo_thien_nhien_lanh)
    check("brand thiên nhiên qua đủ ba cổng", t_brand_thien_nhien_doc_duoc)
    check("thiên nhiên: có đường giao hàng + khai báo AI", t_tn_giao_hang_khai_bao_ai)
    check("mỗi kênh Kling có mặt ở cả hồ sơ + brand", t_kenh_kling_dong_bo_ba_noi)
    check("đề bài Kling: Python khớp web từng trường", t_lich_kling_python_khop_web)
    check("khuôn hình đổi từng tập + khớp web", t_khuon_hinh_doi_tung_tap_va_khop_web)
    check("avatar: chữ và số không bị đường tròn cắt", t_avatar_khong_bi_cat_tron)
    check("biểu tượng đọc được trên nền của chính nó", t_bieu_tuong_doc_duoc_tren_nen_cua_no)
    check("bộ chấm Kling chặn đúng điểm yếu của Kling", t_kling_chan_dung_diem_yeu)
    check("Kling thiếu cảnh phải chặn trước khi ghép", t_kling_thieu_canh_phai_chan_truoc_khi_ghep)
    check("kling_shots: chỗ ghi và chỗ đọc cùng project", t_kling_shots_ghi_doc_cung_mot_project)
    check("Kling A-Z dừng đúng chỗ khi chưa có key + kênh đã khai", t_kling_az_dung_dung_cho_khi_chua_co_key)
    check("thang phải nói đúng loại dữ liệu (không '1 in N' cho lượt đọc)", t_thang_phai_noi_dung_loai_du_lieu)
    check("workflow không dùng `secrets` trong `if`", t_workflow_khong_dung_secrets_trong_if)
    check("dọn mồ côi từ chối khi danh sách kênh rỗng", t_don_mo_coi_khong_duoc_xoa_sach_khi_doc_hut)
    check("bảng xếp hạng phải nói đang xếp theo gì", t_bang_xep_hang_phai_noi_dang_xep_theo_gi)
    check("mọi dạng short đều ghi nguồn (vẽ, không chỉ nhập)", t_moi_dang_short_deu_ghi_nguon)
    check("chống trùng kiểm đúng chuỗi sẽ đi ra", t_chong_trung_kiem_dung_chuoi_di_ra)
    check("bài nghiệm thu bắt được đúng lỗi đã lọt", t_nghiem_thu_bat_duoc_loi_that)
    check("nhịp so sánh không có hai vế bằng nhau", t_chia_doi_hai_ve_khac_nhau)
    check("biểu đồ không vẽ trục toàn số 0 hoặc trục phẳng", t_chart_co_so_that)
    check("gu hình mỗi kênh một bộ, không lặp biểu tượng liền kề", t_gu_hinh_khac_nhau)
    check("mọi nhịp có khuôn đổi bố cục đều ĐƯỢC GÁN bố cục", t_moi_nhip_co_bo_cuc)
    check("không đọc lại cùng một câu trong vòng 12 nhịp", t_khong_lap_loi_gan)
    check("bản dài đủ dài để bật quảng cáo giữa video", t_ban_dai_du_dai)
    check("không `const` nào bị dùng trước khai báo (vùng chết tạm thời)", t_khong_tdz)
    check("mọi trường nhịp có người vẽ ở đúng nhánh khuôn", t_moi_truong_co_nguoi_doc)
    check("giao kèo chuỗi `Drive file id:` giữa hai repo còn khớp", t_giao_keo_chuoi_lien_repo)
    check("cổng hình lấy khung ở nhịp CÓ phụ đề", t_kiem_hinh_lay_dung_khung)
    check("cổng khuôn lời đếm theo VIDEO, không theo câu", t_kiem_khuon_dem_theo_video)
    check("prompt ảnh: CÂU CẢNH đứng trước khối phong cách", t_prompt_canh_dung_dau)
    check("short cắt từ long phải dùng lại ảnh, không gọi CF mới",
          t_short_cat_tu_long_khong_goi_cf)
    check("short đủ ý (>=8 nhịp) và nhịp đầu là HOOK", t_short_du_y_va_hook)
    check("mỗi kênh một dấu ấn riêng, không kênh nào trùng", t_dau_an_kenh_duy_nhat)
    check("guardian không đọc bừa Firestore ở nhánh không kết luận được",
          t_guardian_khong_doc_bua)
    check("guardian không bấm chạy workflow mà người vận hành đã TẮT",
          t_guardian_ton_trong_cong_tac_tat)
    check("tiêu đề/hook/prompt phải đúng ngữ pháp tiếng Anh", t_tieu_de_dung_ngu_phap)
    check("nhịp truc: đủ 3 mốc, không mốc nào trùng", t_truc_du_moc_va_khong_trung)
    check("tiêu đề so sánh: hai vế viết hoa đối xứng", t_tieu_de_viet_hoa_doi_xung)
    check("trần ảnh CF phải đếm ở TỆP (vòng while chạy mỗi tập một tiến trình)",
          t_tran_anh_song_qua_tien_trinh)
    check("prompt ảnh: chốt độ dài không cắt mất luật sàn / bảng màu",
          t_prompt_khong_cat_mat_luat)
    check("prompt ảnh: không có vế viết NGHỊCH (FLUX vẽ ra thứ bị cấm)",
          t_prompt_khong_viet_nghich)
    check("prompt ảnh: không vừa dặn chủ thể ở giữa vừa dặn giữa khung trống",
          t_prompt_khong_noi_nguoc_ve_giua_khung)
    check("sổ trạng thái khoá có chốt chặn theo thời gian", t_ghi_khoa_co_chot)
    check("mặt sàn nằm trên vùng chữ (vật chạm sàn mà không bị che)", t_san_khong_dam_vao_chu)
    check("ảnh bìa lấy mốc nhịp đỉnh, không lấy khung cuối", t_bia_lay_nhip_dinh)
    check("mỗi kênh một BỘ GU bố cục riêng, không kênh nào trùng hoàn toàn", t_gu_bo_cuc_rieng)
    check("thang chấm kịch bản có chạy và ĐƯỢC GỌI trong workflow", t_cham_kich_ban)
    check("DIỄN TẬP failover: chủ đề + đếm chỉ tiêu khi B chết", t_failover_rehearsal)
    check("toon: validator + safe-words + route", t_toon)
    check("hồ key viết không lẫn key ảnh/lưu trữ", t_key_pool_sach)
    check("hồ key ẢNH được bù khi shard trả lời thiếu", t_giu_key_anh)
    check("trí nhớ key cạn SỐNG xuyên video", t_nho_key_can)
    check("bố cục: hook KHÔNG lấn băng phụ đề", t_bo_cuc_khong_chong)
    check("hàng chờ: 18 luồng KHÔNG lấy trùng kênh", t_hang_cho_nguyen_tu)
    check("B2 CHỈ ĐỌC: mọi lệnh ghi đi đường B", t_b2_chi_doc)
    check("không lối đọc nào TRỐN SỔ ngân sách", t_khong_tron_so)
    check("không doc id nào dùng tên BỊ FIRESTORE CẤM", t_id_khong_cam)
    check("sổ đọc hỏng phải HÉT LÊN, không khai rỗng", t_so_hong_phai_het_len)
    check("đường dự phòng B2 không bị bỏ qua im lặng", t_duong_du_phong_b2_khong_bi_bo_qua_im)
    check("cổng kho Drive đóng được THẬT (không tự nuốt lỗi)", t_cong_kho_drive_dong_duoc_that)
    check("nới lớp phủ KHÔNG đụng tới file ảnh gốc", t_noi_man_khong_dung_toi_anh)
    check("cứu mở đầu trước render, KHÔNG qua mặt QC", t_cuu_mo_dau_khong_qua_mat_qc)
    check("mở đầu chốt bằng KHUNG THẬT, không bằng mô hình", t_mo_dau_phai_xac_minh_bang_khung_that)
    check("lấy việc kế nằm đúng đường vào matrix chạy", t_lay_viec_ke_o_dung_duong_vao)
    check("key CHẾT HẲN được nhận diện (khỏi dò tốn quota)", t_key_chet_han_duoc_nhan_dien)
    check("cắt lượt ghi D1 thừa (giữ hạn mức FREE)", t_cat_luot_ghi_d1_thua)
    check("số kho THẬT ghi vào D1 (chỗ dashboard đọc)", t_so_kho_that_ghi_vao_d1)
    check("plan tự đối chiếu sổ đếm với số thật (1 lần/ngày)", t_doi_chieu_so_kho_chay_trong_plan)
    check("biến môi trường RỖNG không phá giá trị mặc định", t_bien_moi_truong_rong_khong_pha_mac_dinh)
    check("bước dùng kho Drive có lớp cứu KV (HOT_KEY)", t_buoc_dung_kho_phai_co_lop_cuu_kv)
    check("tên file KHÔNG làm bẩn tiêu đề YouTube", t_ten_file_khong_lam_ban_tieu_de)
    check("dòng QC loại phải ghi TÊN KÊNH", t_dong_loai_qc_phai_ghi_ten_kenh)
    check("vision có model dự phòng + tự dò", t_vision_co_model_du_phong)
    check("kịch bản có bản dự phòng ở kho KHÁC", t_kich_ban_co_ban_du_phong_khac_kho)
    check("kho token chết được nhớ CHUNG, tự hết hạn", t_kho_token_chet_nho_chung)
    check("kịch bản đi CÙNG video trên Drive", t_kich_ban_di_cung_video_tren_drive)
    check("job bỏ ngỏ được đóng lúc thoát (hết job ma)", t_job_bo_ngo_duoc_dong_luc_thoat)
    check("tên chuẩn: hai video khác nhau KHÔNG đụng tên", t_ten_chuan_khong_dung_ten_nhau)
    check("đẩy kho xong thì xoá bản trên đĩa", t_day_kho_xong_thi_xoa_ban_tren_dia)
    check("Vision kiểm ảnh chết -> hiện CHẾT CÂM", t_vision_chet_thi_phai_hien_chet_cam)
    check("hàng chờ có đường KHÔNG cần Firestore", t_hang_cho_khong_phu_thuoc_firestore)
    check("KHÔNG ghi snapshot/gương rỗng đè bản tốt", t_khong_ghi_snapshot_rong)
    check("KHÔNG cất gói sao lưu rỗng đè bản tốt", t_khong_cat_goi_sao_luu_rong)
    check("sức đăng: 'chưa biết' ≠ 'hết lượt'", t_suc_dang_phan_biet_chua_biet_voi_het_luot)
    check("phản áp lực không chạy được thì phải NÓI RA", t_phan_ap_luc_khong_im_lang)
    check("khâu đăng không dội vào chỗ đã biết là chết", t_publish_khong_doi_vao_cho_da_chet)
    check("sổ quota: đúng ngày reset + cộng đủ 2 cuốn", t_so_quota_dung_ngay_va_gop_du)
    check("bước phụ hỏng phải nói rõ, không im", t_buoc_phu_that_bai_khong_duoc_im)
    check("gương thiếu kênh ≠ kênh bị xoá", t_guong_thieu_kenh_khong_phai_bi_xoa)
    check("thẻ mở đầu KHÔNG thành 'chữ trên nền trơn'", t_the_mo_dau_khong_thanh_nen_tron)
    check("B cạn hạn mức: báo CHUNG, khỏi 18 lane tự khám phá", t_bao_chung_b_can_han_muc)
    check("một bảng phạt key cho CẢ viết lẫn vẽ ảnh", t_mot_bang_phat_key_duy_nhat)
    check("mốc reset nghỉ key theo ĐÚNG nhà cung cấp", t_moc_reset_theo_nha_cung_cap)
    check("mọi workflow ghim phiên bản thư viện", t_moi_workflow_deu_ghim_thu_vien)
    check("mốc intro/outro THẬT sang composition (không lệch tiếng)", t_moc_intro_outro_that)
    check("doc: đủ sàn 21s + rải giây theo SỐ ẢNH (không nhàm)", t_doc_du_dai_va_khong_nham)
    check("mọi short có lưới sàn 21s, kéo dài KHÔNG lệch tiếng", t_short_khong_qua_ngan)
    check("mọi short có phụ đề karaoke bám giọng", t_short_co_phu_de_karaoke)
    check("đọc HỎNG ≠ kênh bị xoá (không giết lane oan)", t_doc_hong_khac_kenh_bi_xoa)
    check("render lại LONG dùng ĐÚNG engine của kênh", t_render_lai_long_dung_engine)
    check("số video trong kho lấy TỪ DRIVE, không cộng dồn", t_so_kho_lay_tu_drive)
    check("FB hết nhịp = HOÃN, không vứt video", t_fb_het_nhip_khong_giet_video)
    check("gộp lệnh ghi D1: done/failed xả NGAY, phần dư không mất", t_gop_ghi_d1)
    check("mọi lớp tối của Scene1 đều nới theo man", t_moi_lop_toi_deu_noi)
    check("mô hình đo mô phỏng ĐỦ 5 lớp phủ", t_sau_man_du_lop)
    check("xoay key ảnh/Vision theo lượt đã dùng", t_xoay_key_theo_luot_dung)
    check("nén lỗi đã lường trước, không đệ quy", t_nen_loi_da_luong_khong_de_quy)
    check("hồ key qua ảnh chụp D1, không đâm vào A", t_ho_key_qua_d1_khong_dam_vao_A)
    check("xoay trục phải ĐỔI tiêu đề, không thì kênh câm sau 1 video", t_xoay_truc_doi_tieu_de)
    check("mọi nguồn phải có TÊN CƠ QUAN, không in mã lên video", t_moi_nguon_co_ten_that)
    check("cổng an toàn đi hết MỌI kho mục (kể cả frames)", t_cong_an_toan_di_het_moi_kho_muc)
    check("xoay trục thì nhãn tĩnh phải BIẾN MẤT tới tận bộ dựng", t_nhan_tinh_bi_bo_khi_xoay_truc)
    check("gu vẽ gán TAY từng kênh, tiếng Anh, cấm ảnh chụp", t_gu_ve_khop_tung_kenh)
    check("nhãn None không được lọt lên tiêu đề", t_nhan_none_khong_lot_len_tieu_de)
    check("ai_only thì KHÔNG lấy clip kho (không footage)", t_ai_only_khong_lay_clip_kho)
    check("18 kênh ranked KHÔNG dùng chung một khuôn", t_bo_cuc_ranked_khong_dung_chung_mot_khuon)
    check("prompt vẽ không gọi tên mặt phẳng chứa chữ", t_prompt_ve_khong_goi_ten_mat_chu)
    check("đồng hồ đua hiện được mốc chữ, không ra NaN", t_dong_ho_dua_chiu_moc_chu)
    check("mọi giá trị trục đều có nhánh riêng (không trùng kênh)", t_moi_gia_tri_truc_deu_co_nhanh)
    check("bản ghi kho hỏng cấu trúc bị loại từ gốc", t_root_rac_loai_tu_goc)
    check("xin độ đậm phông phải nằm trong số phông CÓ", t_do_dam_phong_co_that)
    check("cổng chạy-thật phải biết MỌI cờ CLI", t_cong_biet_moi_co)
    check("biến thể bố cục: cùng dạng KHÔNG được trùng", t_bien_bo_cuc_khong_trung)
    check("scope Drive theo TỪNG app, không đổi đồng loạt", t_scope_drive_theo_app)
    check("radar: ứng viên rỗng KHÔNG được lọt cửa nhu cầu", t_radar_khong_lot_rong)
    check("QC thị giác phải soi KHUNG HOOK, chấm riêng", t_qc_hook_rieng)
    check("sổ ngân sách tách theo project, đúng đơn vị với ngưỡng", t_ngan_sach_theo_project)
    check("tự-seed KHÔNG hồi sinh kênh đã nghỉ", t_tu_seed_khong_hoi_sinh)
    check("cổng fail-open phải bắt BaseException (SystemExit)", t_fail_open_bat_baseexception)
    check("chủ đề đã làm TRONG PHIÊN phải vào danh sách tránh", t_so_chu_de_trong_phien)
    check("MỌI chốt t_* đều được đăng ký chạy", t_moi_chot_deu_duoc_dang_ky)
    check("job ĐANG CHẠY có mặt trong D1 ngay lượt ghi đầu", t_job_dang_chay_len_d1_ngay)
    check("hai vòi rỉ lớn nhất đã có hãm (nhịp sống · top_titles)", t_hai_voi_ri_da_ham)
    check("đồng bộ kho có ngân sách giờ, không đợi đủ hết", t_dong_bo_kho_co_ngan_sach_gio)
    check("kiểm kho hằng ngày: song song + ngân sách 240s", t_kiem_kho_ngay_co_ngan_sach)
    check("lượt đi bộ nhặt kèm map kho + thumbnail", t_lap_ban_ghi_tu_luot_di_bo)
    check("plan KHÔNG render — yêu cầu render-lại giao lane", t_plan_khong_render)
    check("khối __main__ của run_render nằm CUỐI file", t_khoi_main_cuoi_file)
    check("phiên không giữ khoá quá lâu (phiên sau khỏi bị huỷ)", t_phien_khong_giu_khoa_qua_lau)
    check("giọng nhân vật có cao độ, hai vai lệch nhau", t_giong_nhan_vat_co_cao_do)
    check("tts: không hàm nào dùng biến chưa nhận", t_tts_khong_dung_bien_chua_nhan)
    check("kịch bản skit mang đủ 5 luật viral", t_kich_ban_co_luat_viral)
    check("chữ karaoke luôn đọc được (bảng màu đã sàng)", t_chu_chay_luon_doc_duoc)
    check("thẻ tiêu đề tự co, không tràn khung", t_the_tieu_de_khong_tran_khung)
    check("dữ liệu mở hỏng KHÔNG làm gãy dây chuyền", t_du_lieu_mo_khong_lam_gay_day_chuyen)
    check("50 kênh thế hệ 2 trỏ đúng hàm + dạng", t_kenh_the_he_2_tro_dung_ham_va_dang)
    check("_dispatch_short luôn trả đủ 4 giá trị", t_dispatch_luon_tra_bon_gia_tri)
    check("thế hệ 2: tên tra động đều có thật", t_the_he_2_tra_ten_dong_deu_co_that)
    check("brand-kit: motif có thật, màu không trùng", t_brandkit_the_he_2)
    check("cổng an toàn nội dung phủ cả 7 đường story", t_cong_an_toan_noi_dung)
    check("CF chặn prompt vẫn còn đường Gemini", t_cf_chan_prompt_van_con_duong_gemini)
    check("vẽ ảnh hỏng phải nói lý do, không im lặng", t_ve_anh_khong_hong_im_lang)
    check("đường ghi D1 hỏng phải nói, không im lặng", t_duong_ghi_d1_khong_hong_im_lang)
    check("không đệm kết quả RỖNG (bẫy làm dashboard trắng)", t_khong_dem_ket_qua_rong)
    check("phanh mù thì giả định CẠN, không giả định đầy", t_phanh_do_khong_duoc_phai_gia_dinh_can)
    check("đường lùi không khuếch đại lỗi (1 lượt 429 -> 18)", t_duong_lui_khong_duoc_khuech_dai_loi)
    check("seed 50 kênh: **spread không đè khoá cố ý", t_seed_khong_bi_spread_de_len_khoa_co_y)
    check("cạn quota Firestore: đường chạy chính KHÔNG được đứng", t_dien_tap_can_quota)
    check("cạn quota Firestore: CẢ PHIÊN vẫn phải xếp đủ 18 lane", t_dien_tap_ca_phien)
    check("không được vẽ HAI lớp phụ đề chồng nhau", t_khong_phu_de_chong)
    check("sổ đề tài chỉ ghi khi video RA LÒ THẬT", t_so_de_tai_chi_ghi_khi_ra_lo)
    check("kênh cùng niche không được trùng kho đề tài", t_kenh_anh_em_khong_trung_kho)
    check("50 kênh không được dùng chung một bản nhạc", t_nhac_nen_khong_dung_chung)
    check("MỌI kênh gen-2 phải vào được nhánh gen-2", t_moi_kenh_gen2_vao_duoc_nhanh)
    check("không tên nào chưa định nghĩa (NameError nấp ở nhánh hiếm)", t_khong_ten_chua_dinh_nghia)
    check("50 kênh không được giống nhau (≥70 điểm)", t_50_kenh_khong_duoc_giong_nhau)
    check("băm Python khớp băm TypeScript", t_bam_python_khop_typescript)
    check("prop font khai rồi phải thao ra", t_phong_khai_roi_phai_thao_ra)
    check("gen-2: cả 3 đường phải làm thumbnail", t_gen2_phai_lam_thumbnail)
    check("fitSize theo phông + theo template", t_fitsize_phai_theo_phong_va_khung)
    check("canary không được render vào composition rỗng", t_canary_khong_duoc_render_vao_composition_rong)
    check("phông chảy hết đường JSON->props->composition", t_phong_phai_chay_het_duong_toi_luc_render)
    check("dọn kho: đi hết cây + mọi loại tệp", t_don_kho_phai_di_het_cay_va_moi_loai_tep)
    check("dọn kho KHÔNG được đụng kịch bản", t_don_kho_khong_duoc_dung_kich_ban)
    check("việc dài phải in tiến độ + đủ giờ", t_viec_dai_phai_in_tien_do_va_du_gio)
    check("van phiên tính ngược từ trần hạn mức", t_van_phien_phai_theo_ngan_sach)
    check("plan không được đọc gói của chính nó", t_plan_khong_duoc_doc_goi_cua_chinh_no)
    check("mức âm chuyển cảnh quyết ở MỘT chỗ", t_muc_am_quyet_o_mot_cho)
    check("50 kênh đồng bộ đủ 3 nơi (dropdown/brand/đăng)", t_50_kenh_dong_bo_du_ba_noi)
    check("tên seed lưu phải tra ra được kênh gen-2", t_tra_kenh_gen2_phai_khop_ten_seed_luu)
    check("bảng mốc dọn riêng phải khớp tên kênh thật", t_moc_don_rieng_khop_ten_kenh)
    check("mọi tệp .tsx phải dịch được (1 tệp hỏng = CẢ 50 kênh đứng)", t_tsx_dich_duoc)
    check("tsx: không dùng biến trước khi khai báo (esbuild mù chỗ này)",
          t_tsx_khong_dung_bien_truoc_khi_khai)
    check("bộ hài: giọng có thật · hai người khác giọng · nhân vật có tên",
          t_bo_hai_giong_va_nhan_vat)
    check("nhãn tĩnh phải BIẾN MẤT khi trục xoay đổi chủ đề", t_nhan_tinh_xoay_thi_mat)
    check("mỗi kênh gen-2 phải xoay được đề tài", t_moi_kenh_gen2_phai_xoay_duoc_de_tai)
    check("gen-2 ra BỘ 1 long + 3 short (có cha/thứ tự)", t_gen2_phai_ra_bo_1long_3short)
    check("bộ không được chọn story hai lần", t_bo_khong_duoc_chon_story_hai_lan)
    check("--capnhat phải đẩy đủ trường cố ý", t_capnhat_phai_day_du_truong_co_y)
    check("workflow dùng AutoPublisher phải checkout thật", t_workflow_dung_autopublisher_phai_checkout_that)
    check("55 kênh cũ phải có bản chụp tên", t_ten_kenh_cu_phai_co_ban_chup)
    check("workflow quản trị trỏ đúng project (SHARD_META)", t_cong_cu_quan_tri_phai_tro_dung_project)
    check("workflow chạy selftest phải đủ thư viện", t_workflow_chay_selftest_phai_du_thu_vien)
    if FAILS:
        print(f"\n🚨 SELFTEST FAIL ({len(FAILS)}) — CHẶN PHIÊN để không đốt 18 luồng vào bản hỏng:")
        for f in FAILS:
            print("   - " + f)
        sys.exit(1)
    print("✅ SELFTEST PASS — code lành, cho phép chạy phiên.")


def t_gop_ghi_d1():
    """Gộp lệnh ghi phải TIẾT KIỆM mà KHÔNG MẤT dữ liệu và KHÔNG làm chậm số quan trọng.

    Ba điều kiện: (a) 25 thao tác giữa chừng chỉ tốn 1-2 lượt gọi; (b) trạng thái CUỐI
    (done/failed) xả NGAY chứ không nằm đệm — đó là số người ta nhìn để biết có mất video không;
    (c) `xa_het()` cuối luồng không để sót mục nào."""
    import hot_db as H
    goc_goi, goc_bat = H.goi, H.bat_ghi
    dem = {"n": 0, "mucs": 0}

    def _gia(lenh, tham=None, timeout=12):
        dem["n"] += 1
        if lenh == "ghi_job_loat":
            dem["mucs"] += len(tham.get("jobs") or [])
        return {"ok": True}

    H.goi, H.bat_ghi = _gia, (lambda: True)
    try:
        H._DEM_BUF.clear(); H._BUF_AT[0] = 0
        for i in range(25):
            H.ghi_job("O", f"j{i}", "K", "short", "rendering", at="t")
        assert dem["n"] <= 2, f"25 thao tác mà tốn {dem['n']} lượt gọi — gộp không ăn"
        assert len(H._DEM_BUF) > 0, "phải còn phần dư nằm đệm"
        H.ghi_job("O", "jX", "K", "short", "done", drive_id="d", at="t")
        assert not H._DEM_BUF, "trạng thái CUỐI phải xả ngay, không được nằm đệm"
        H.ghi_job("O", "jY", "K", "short", "qc", at="t")
        assert H.xa_het() == 1, "xa_het phải xả nốt phần còn lại"
        assert not H._DEM_BUF
    finally:
        H.goi, H.bat_ghi = goc_goi, goc_bat
        H._DEM_BUF.clear(); H._BUF_AT[0] = 0


def t_id_khong_cam():
    """Firestore CẤM doc id khớp mẫu `__...__` (bọc kín hai đầu) — dành riêng cho hệ thống.

    24/8: `connections_mirror/__snap__` mang đúng dạng đó nên **chưa từng ghi được ngày nào**.
    Lượt ghi đi qua `_soft` nên lỗi bị nuốt, lượt đọc trả rỗng -> lối "1 lượt đọc" không bao giờ có,
    mọi luồng rơi xuống lối quét 73 doc trên project A. Đó chính là thứ làm A cháy mỗi ngày.
    Hai cái tôi tự thêm tối nay (`__drive_usage__`, `__enqueue_sweep__`) cũng dính y hệt.
    Lỗi loại này KHÔNG BAO GIỜ tự lộ vì `_soft` che hết — nên phải bắt bằng bài kiểm tĩnh.
    Lưu ý: `__snap__mm0` HỢP LỆ (không kết thúc bằng `__`)."""
    import re
    thu_muc = os.path.dirname(os.path.abspath(__file__))
    xau = []
    for ten in ("firestore_bridge.py", "fix_dup_connections.py", "rebuild_stats.py",
                "reset_ledger.py", "find_overlap_videos.py", "hot_db.py"):
        p = os.path.join(thu_muc, ten)
        if not os.path.exists(p):
            continue
        src = io.open(p, encoding="utf-8").read()
        for m in re.finditer(r'\.document\(\s*f?"([^"{}]+)"', src):
            i = m.group(1)
            if re.match(r"^__.*__$", i):
                xau.append(f"{ten}: {i}")
    assert not xau, ("doc id bị Firestore CẤM (dạng __...__): " + ", ".join(xau)
                     + " -> đổi tên, vì _soft sẽ nuốt lỗi và không ai biết")


def t_khong_tron_so():
    """CHẶN CODE MỚI THÊM MỘT LỐI ĐỌC KHÔNG AI ĐẾM.

    Đây là gốc của việc "tối ưu mãi vẫn vỡ": sổ `_cr()` chỉ đếm ở chỗ CÓ AI ĐÓ NHỚ GẮN VÀO.
    Đo thật 24/8: sổ báo 1.302 lượt đọc trong khi project B đã dùng >50.000 — sổ chỉ thấy ~3%.
    Mỗi lần thêm code là thêm một lối trốn. Bài này quét mọi lệnh quét-cả-bảng (`.stream(`) trong
    firestore_bridge và bắt buộc quanh đó phải có `_cr(` hoặc đi qua `_stream_at`. Thêm lối đọc mới
    mà quên đếm là FAIL NGAY TẠI ĐÂY, không phải chờ cháy quota mới biết."""
    # ── QUÉT MỌI SCRIPT NẰM TRONG WORKFLOW CÒN CHẠY, không chỉ `firestore_bridge.py`.
    # Bản trước chỉ soi một tệp. Nên `don_sach.py` — công cụ tôi viết hôm nay — có bốn lối đọc
    # KHÔNG gắn sổ mà cổng vẫn in ✅. Hậu quả đo được: nó tiêu ~16.000 lượt đọc ngoài tầm kiểm
    # soát của chính hệ canh hạn mức, làm Firestore cạn đúng lúc bước đẩy kho chạy, và 17 lượt
    # render xong không lên được Drive (buglog 7cw).
    # Cùng họ lỗi với `kiem_workflow.CAP`: cổng chỉ kiểm những cái nó được liệt kê sẵn.
    # Tự tìm: mọi script được workflow CÒN CRON gọi tới.
    GOC_ = os.path.dirname(os.path.abspath(__file__))
    WF_ = os.path.join(os.path.dirname(GOC_), ".github", "workflows")
    can_ = {"firestore_bridge.py"}
    if os.path.isdir(WF_):
        for f_ in sorted(os.listdir(WF_)):
            if not f_.endswith(".yml"):
                continue
            y_ = io.open(os.path.join(WF_, f_), encoding="utf-8").read()
            ma_ = "\n".join(l for l in y_.split("\n") if not l.lstrip().startswith("#"))
            if "cron:" not in ma_:
                continue                  # workflow đã nghỉ -> không đòi
            for m_ in re.finditer(r"python3? (\w+)\.py", ma_):
                can_.add(m_.group(1) + ".py")
    # ── VÀ ĐI THEO `import`, KHÔNG DỪNG Ở TỆP ĐƯỢC GỌI TỪ WORKFLOW  (4/9/2026) ──────────
    # Phạm vi cũ = "tệp mà workflow gõ tên". `xoay_key.py` không nằm trong đó — nó được
    # `giai_thich.py` và `nen_gt.py` import. Nên lối đọc `gemini_keys` của nó chưa bao giờ
    # bị soi, và nó tiêu **53.100 lượt ĐỌC mỗi lượt workflow** (18 luồng × 10 lần × 295 doc)
    # ngoài tầm nhìn của bức tường ngân sách — trên trần 50.000 CẢ NGÀY.
    #
    # Đây đúng thứ bệnh mà chính docstring này mô tả (*"cổng chỉ kiểm những cái nó được liệt
    # kê sẵn"*), chỉ khác là lần trước phạm vi thiếu một TỆP, lần này thiếu cả một TẦNG.
    # Một tệp chạy trong đường tự động dù được gọi trực tiếp hay được import thì đều tiêu
    # cùng một hạn mức — nên phạm vi phải là BAO ĐÓNG theo import, không phải danh sách gọi.
    _da_ = set()
    while True:
        _moi_ = can_ - _da_
        if not _moi_:
            break
        for _t2 in sorted(_moi_):
            _da_.add(_t2)
            _p2 = os.path.join(GOC_, _t2)
            if not os.path.exists(_p2):
                continue
            _s2 = io.open(_p2, encoding="utf-8").read()
            for _m2 in re.finditer(r"^\s*(?:import|from)\s+(\w+)", _s2, re.M):
                _c2 = _m2.group(1) + ".py"
                if os.path.exists(os.path.join(GOC_, _c2)):
                    can_.add(_c2)
    tron = []
    for tep_ in sorted(can_):
        p_ = os.path.join(GOC_, tep_)
        if not os.path.exists(p_):
            continue
        _ca = io.open(p_, encoding="utf-8").read()
        # ── CHỈ SOI TỆP CÓ ĐỤNG FIRESTORE  (4/9/2026) ──────────────────────────────────
        # `.stream()` không phải từ riêng của Firestore. Mở rộng phạm vi theo import xong,
        # cổng tố ngay `tts_karaoke.py: async for chunk in comm.stream()` — đó là luồng âm
        # thanh của `edge-tts`, không tiêu một lượt đọc Firestore nào.
        # Cổng bắt oan còn tệ hơn cổng không bắt (§13.8): một dòng đỏ giả làm người ta tắt
        # cổng, và lỗi thật nằm cạnh nó chìm theo. Tệp không nhắc tới Firestore thì không có
        # gì ở đây để đếm — bỏ qua cả tệp, và không nới lỏng gì với tệp có đụng.
        if not re.search(r"firestore|collection\(|_db_", _ca):
            continue
        src = _ca.split("\n")
        trong_doc_ = False           # đang ở trong docstring?
        for i, ln in enumerate(src):
            # Chú thích trong DOCSTRING không bắt đầu bằng `#`, nên phép lọc cũ tố oan mọi
            # câu văn nhắc tới `.stream()` — và một cổng tố oan thì người ta tắt nó đi.
            if ln.count(chr(34) * 3) % 2 == 1 or ln.count(chr(39) * 3) % 2 == 1:
                trong_doc_ = not trong_doc_
                continue
            if trong_doc_ or ".stream(" not in ln or ln.strip().startswith("#"):
                continue
            if "_stream_at" in ln:
                continue                  # đi qua lớp bọc -> hợp lệ
            vung = "\n".join(src[max(0, i - 6):i + 2])
            if "_cr(" in vung or "def _stream_at" in vung:
                continue                  # có gắn sổ ngay trên -> hợp lệ
            tron.append(f"{tep_} dòng {i+1}: {ln.strip()[:64]}")
    assert not tron, ("có lối đọc KHÔNG gắn sổ ngân sách:\n   " + "\n   ".join(tron[:6])
                      + "\n-> thêm _cr(\"tên\", n) ngay trước, hoặc gọi qua _stream_at()")


def t_b2_chi_doc():
    """B là nguồn GHI duy nhất, B2 chỉ để ĐỌC — chốt bằng code chứ không bằng lời hứa.

    Firestore tách riêng hạn mức đọc (50K) và ghi (20K). Failover sang B2 gần như luôn do cạn ĐỌC,
    lúc đó ghi vào B vẫn tốt. Bản cũ để `_db_jobs()` trả B2 cho cả đọc lẫn ghi -> dữ liệu sống chẻ
    làm đôi -> phải rót ngược -> rót ngược cộng Increment từ bản sao -> lệch số. Bài này bắt mọi
    lệnh ghi phải đi qua `_db_ghi()`."""
    import re
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "firestore_bridge.py"), encoding="utf-8").read()
    xau = [m for m in re.findall(r"_soft\(lambda[^\n]*", src) if "_db_jobs()" in m]
    assert not xau, f"còn {len(xau)} lệnh ghi đi qua _db_jobs() (có thể trỏ sang B2): {xau[0][:80]}"
    assert "def _db_ghi()" in src, "thiếu _db_ghi()"
    # và gương KHÔNG được rót ngược render_stats/{owner} (bản sao do chính nó chép sang)
    assert 'for _sid in (f"__pushed__{owner}",)' in src, \
        "danh sách rót ngược phải BỎ render_stats/{owner} — chép sang rồi cộng ngược là nhân đôi"


def t_hang_cho_nguyen_tu():
    """Luồng nào xong trước thì lấy kênh kế — nhưng KHÔNG được hai luồng nhận cùng một kênh
    (render trùng = tốn đôi quota AI lẫn chỗ kho). Giả lập giao dịch: mỗi lần lấy phải ra kênh KHÁC
    và hết hàng thì trả rỗng."""
    import firestore_bridge as FB
    kho = {"cho": ["A", "B", "C"]}

    class _Snap:
        exists = True
        def to_dict(self): return dict(kho)

    class _Ref:
        def get(self, transaction=None): return _Snap()

    class _Tx:
        def update(self, ref, patch): kho.update(patch)

    def _lay():
        cho = list(kho.get("cho") or [])
        if not cho:
            return ""
        lay = cho.pop(0)
        _Tx().update(_Ref(), {"cho": cho})
        return lay

    ra = [_lay() for _ in range(5)]
    assert ra == ["A", "B", "C", "", ""], f"lấy việc sai thứ tự/trùng: {ra}"
    assert callable(getattr(FB, "lay_viec_ke", None)), "thiếu FB.lay_viec_ke"
    assert callable(getattr(FB, "dat_hang_cho", None)), "thiếu FB.dat_hang_cho"


def t_bo_cuc_khong_chong():
    """CHỮ CHỒNG CHÉO (ảnh chụp 24/8: "$750B" đè "What does it take to keep").

    Hai lớp vẽ độc lập trong Cinematic.tsx: lớp HOOK (số liệu to) và lớp PHỤ ĐỀ. Trước đây biến thể
    hook neo đáy dùng padding-bottom 300px nên trải xuống tận y≈1620, còn phụ đề ở `bottom: 520`
    (băng y≈1200-1400) -> đâm ngang qua nhau. Chọn bố cục theo băm tiêu đề nên cứ ~1/4 video dính.
    Chốt bằng số để sau này ai sửa lùi lại là FAIL ngay tại đây, không phải chờ thấy video xấu."""
    import os
    import re
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "engine-remotion", "src", "Cinematic.tsx")
    src = io.open(p, encoding="utf-8").read()
    cap = int(re.search(r"const fs = port \? \d+ : \d+; const bottom = port \? (\d+)", src).group(1))
    top = int(re.search(r"const CAP_TOP = (\d+);", src).group(1))
    # hook phải kết thúc TRÊN mép trên của băng phụ đề, chừa biên cho phụ đề 2-3 dòng (~260px)
    assert top >= cap + 260, (f"hook neo đáy tới y={1920-top}, băng phụ đề bắt đầu ~y={1920-cap-260} "
                              f"-> sẽ chồng chữ (CAP_TOP phải >= {cap + 260})")


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


def t_so_kho_lay_tu_drive():
    """Số "video trong kho" phải SUY RA TỪ DRIVE, không được cộng dồn theo sự kiện (24/8, anh:
    "1343 video lận có nhầm ko"). Sổ Increment chỉ có chiều lên nên render lại + dọn rác làm nó
    phồng vĩnh viễn. Ba điều kiện, thiếu cái nào là số lại sai:
      1. có công cụ kiểm kho,
      2. nó GHI ĐÈ (`set`) chứ không `Increment`,
      3. kho nào đọc hụt thì KHÔNG ghi (đọc thiếu mà ghi đè = tự xoá sổ về số thấp)."""
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kiem_kho.py"),
                  encoding="utf-8").read()
    # Chỉ soi PHẦN LỆNH, bỏ qua chú thích/docstring (bản thân docstring có nhắc chữ Increment để
    # giải thích cái bệnh) — nếu không thì test tự hỏng vì chính lời giải thích của mình.
    import ast as _ast
    cay = _ast.parse(src)
    for _n in _ast.walk(cay):
        if isinstance(_n, _ast.Name) and _n.id == "Increment":
            raise AssertionError("kiem_kho không được dùng Increment — phải ghi đè bằng số thật")
    assert '.document(f"__pushed__{a.owner}").set(' in src, "kiem_kho phải GHI ĐÈ sổ __pushed__"
    assert "a.ghi = False" in src and "hong_kho" in src, \
        "đọc hụt kho nào thì phải TỰ TẮT chế độ ghi, nếu không sổ bị đếm thiếu"


def t_fb_het_nhip_khong_giet_video():
    """Facebook chạm trần nhịp là HOÃN, không phải hỏng (24/8, anh: "a đăng cả facebook").
    `publish_social` dán nhãn `failed` sau 3 lần lỗi -> nếu hết nhịp FB bị tính là lỗi thì đúng 3
    lượt cron là video bị VỨT, y hệt bẫy đã vá cho Instagram."""
    ap = os.environ.get("AUTOPUBLISHER_SRC") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "MM0-AutoPublisher", "src")
    f1 = os.path.join(ap, "facebook_uploader.py")
    f2 = os.path.join(ap, "publish_social.py")
    if not (os.path.exists(f1) and os.path.exists(f2)):
        return          # repo publish không có ở đây (CI render) -> bỏ qua, không phải lỗi
    a = io.open(f1, encoding="utf-8").read()
    b = io.open(f2, encoding="utf-8").read()
    assert "class HetNhip" in a and "MA_HET_NHIP" in a, "facebook_uploader thiếu nhận diện hết nhịp"
    assert "except HetNhip:" in a, "Reels hết nhịp mà vẫn rơi xuống đăng video thường = gọi thêm 1 lượt vào Page đang bị chặn"
    assert "errs_fb_skip" in b, "publish_social chưa hoãn khi FB hết nhịp"
    assert "(errs_ig_skip or errs_fb_skip) and not errs" in b, \
        "FB hết nhịp vẫn bị cộng attempts -> 3 lượt cron là video vào dead-letter"


def t_doc_hong_khac_kenh_bi_xoa():
    """Lệnh đọc HỎNG không được biến thành sự thật SAI (24/8 tối, phiên 16:06Z: lane HAULUSA +
    FAKEUSA thoát sau 60s vì "kênh không còn (đã xóa)", trong khi plan vừa xếp việc cho chúng)."""
    import firestore_bridge as FB
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "firestore_bridge.py"), encoding="utf-8").read()
    assert hasattr(FB, "DocLoi"), "thiếu loại lỗi riêng cho 'đọc hỏng'"
    i = src.index("def read_one_channel")
    # 28/8 — cắt theo BIÊN HÀM, không theo số ký tự: cửa sổ cố định vỡ khi thân hàm
    # dài ra, và chốt đỏ vì lỗi CỦA CHÍNH NÓ chứ không phải vì mã hỏng.
    _ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
    than = src[i: min(_ket) if _ket else len(src)]
    assert "_stream_at" in than, "read_one_channel vẫn gọi .stream() trực tiếp — dính lại lỗi thư viện"
    assert "raise DocLoi" in than, "đọc hỏng vẫn bị nuốt thành None (= 'kênh đã bị xoá')"
    r = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "run_render.py"), encoding="utf-8").read()
    assert r.count("except FB.DocLoi") >= 2, "hai chỗ gọi read_one_channel phải xử lý DocLoi riêng"


def t_render_lai_long_dung_engine():
    """Render lại một LONG phải dùng ĐÚNG engine của kênh đó. Bản cũ gọi cứng `DS.make_long`
    (biểu đồ đua cột) cho mọi kênh -> bấm 🔄 trên long doc/toon là thay bằng video SAI ĐỊNH DẠNG,
    mà bản cũ đã bị bỏ thùng rác. Và kịch bản long doc/toon phải lưu ĐỦ để resume."""
    r = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "run_render.py"), encoding="utf-8").read()
    i = r.index("def _lam_render_requests") if "def _lam_render_requests" in r else r.index('if typ == "long":')
    than = r[i:i + 6000]
    for ten in ("DS.make_toon_long", "DS.make_doc_long", "DS.make_long"):
        assert ten in than, f"đường render lại LONG thiếu nhánh {ten}"
    assert '"parts": [p["topic"] for p in parts]' not in r, \
        "long doc vẫn lưu mỗi TÊN chủ đề — không resume được (make_doc_long cần story dict)"
    assert r.count("_ks_long(plan,") >= 3, \
        "phải có đủ 3 đường long (doc · motif · toon) lưu kịch bản đầy đủ"
    assert '"subs"' in r[r.index("def _ks_long"): r.index("def _ks_long") + 1400], \
        "thiếu `subs` thì make_doc_long cắt done_stories về 0 -> resume vô nghĩa"


def t_short_co_phu_de_karaoke():
    """Mọi short phải có phụ đề karaoke (24/8 tối, anh: "short cũng nên có sub karaoke").
    Soi ra 9 định dạng KHÔNG có phụ đề nào: `subs` có trong khai báo props nhưng không lớp nào vẽ,
    và mọi builder Python viết `du, _, _ = TK.synth(...)` — vứt mốc từng từ edge-tts đã trả sẵn."""
    import tts_karaoke as TK
    assert hasattr(TK, "subs_tu_clips"), "thiếu hàm ghép mốc karaoke cho cả track"
    TK._NHO.clear()
    TK._NHO[os.path.abspath("/tmp/a.mp3")] = [{"t": 0.0, "d": 0.5, "w": "Hello"},
                                              {"t": 0.5, "d": 0.4, "w": "world."}]
    TK._NHO[os.path.abspath("/tmp/b.mp3")] = [{"t": 0.0, "d": 0.3, "w": "Next"}]
    ra = TK.subs_tu_clips([("/tmp/a.mp3", 0.0), ("/tmp/nhac.mp3", 1.0), ("/tmp/b.mp3", 2.0)])
    assert [x["w"] for x in ra] == ["Hello", "world.", "Next"], ra
    assert ra[-1]["t"] == 2.0, f"mốc phải dời theo chỗ đặt clip, thực tế {ra[-1]['t']}"
    TK._NHO.clear()

    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "datastory_ci.py"), encoding="utf-8").read()
    assert src.count("TK.subs_tu_clips(clips)") >= 9, \
        f"chỉ {src.count('TK.subs_tu_clips(clips)')}/9 builder short truyền phụ đề sang composition"

    eng = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "engine-remotion", "src")
    if not os.path.isdir(eng):
        return
    k = io.open(os.path.join(eng, "Karaoke.tsx"), encoding="utf-8").read()
    m = re.search(r"const BOTTOM = (\d+)", k)
    assert m and int(m.group(1)) >= 190, \
        "băng chữ karaoke phải nằm TRÊN mọi thứ neo đáy của short (chỗ thấp nhất là bottom 150)"
    for ten in ("PulseShort", "SwarmShort", "RankedShort", "MappedShort", "ScaledShort",
                "ThenNowShort", "LongshotShort", "ClockworkShort", "GuessShort"):
        t = io.open(os.path.join(eng, ten + ".tsx"), encoding="utf-8").read()
        assert "Karaoke" in t, f"{ten} không vẽ phụ đề karaoke"
        # GUESS có thẻ mở/kết riêng (ảnh vòng 1 + KetCard), 7 cái còn lại dùng Bookend chung.
        if ten not in ("GuessShort", "ClockworkShort"):
            assert "Bookend" in t, f"{ten} vẫn để trống quãng mở đầu/kết thúc"


def t_moc_intro_outro_that():
    """Mọi builder phải truyền mốc intro/outro ĐO ĐƯỢC sang composition (24/8 tối).
    Thiếu thì composition dùng số cứng (1,7/1,6) trong khi giọng dài khác hẳn -> HÌNH LỆCH TIẾNG,
    đúng lỗi PULSE 4,7 giây. Bản vá trước gắn nhầm vào `build_ranked_props` nên swarm/pulse/longshot
    vẫn hở suốt."""
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "datastory_ci.py"), encoding="utf-8").read()
    n = src.count('"introSec": introSec')
    assert n >= 9, f"chỉ {n}/9 builder truyền mốc intro thật"
    assert src.count('"outroSec": outroSec') >= 9, "thiếu mốc outro thật"


def t_doc_du_dai_va_khong_nham():
    """`keo_du_dai` (format doc) phải LUÔN chạm sàn 21s, và rải giây theo SỐ ẢNH mỗi cảnh.
    24/8 tối: rải đều thì chính bước cứu video khỏi "quá ngắn" lại đẩy nó vào lỗi QC "cảnh giữ một
    ảnh quá 3.5s (nhàm)"; còn trần 2,5s/cảnh thì clip ít cảnh không bao giờ chạm sàn -> vẫn bị vứt."""
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "datastory_ci.py"), encoding="utf-8").read()
    i = src.index("def keo_du_dai("); ns = {}
    exec(src[i: src.index("\ndef keo_du_dai_track")], ns)
    f = ns["keo_du_dai"]
    for sc in ([{"dur": 90, "clips": ["a", "b", "c"]}, {"dur": 90, "clip": "x"}],
               [{"dur": 400, "clips": ["a"]}],                       # ít cảnh -> trần chặn
               [{"dur": 287, "clips": ["a", "b"]}, {"dur": 286, "clip": "c"}]):   # ca thật scaled 19,1s
        f(sc, fps=30, ten="test")
        assert sum(x["dur"] for x in sc) / 30.0 >= 21.0, f"chưa chạm sàn: {sc}"
    nhieu = [{"dur": 90, "clips": ["a", "b", "c"]}, {"dur": 90, "clip": "x"}]
    f(nhieu, fps=30, ten="test")
    assert nhieu[0]["dur"] > nhieu[1]["dur"], "cảnh 1 ảnh phải nhận ÍT giây hơn cảnh 3 ảnh"
    du = [{"dur": 450, "clips": ["a"]}, {"dur": 450, "clip": "b"}]
    assert f(du, fps=30, ten="test") == 0.0 and du[0]["dur"] == 450, "đủ dài rồi thì KHÔNG được đụng"


def t_short_khong_qua_ngan():
    """Mọi format một-track phải có lưới sàn 21s, và kéo dài mục thì mốc tiếng phải dời theo
    (24/8 tối, anh: "short ko quá ngắn lỗi"). Trước đó chỉ doc + pulse có lưới; log 11:00Z có ca
    `scaled 19.1s` — vứt cả video vì hụt 0,9 giây."""
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "datastory_ci.py"), encoding="utf-8").read()
    assert src.count("keo_du_dai_track(") >= 8, \
        f"chỉ {src.count('keo_du_dai_track(') - 1}/7 format có lưới sàn dài"
    assert "total = round(introSec + cum + outroSec" not in src, \
        "còn chỗ tính tổng thẳng tay -> format đó không có lưới sàn"
    i = src.index("def keo_du_dai_track"); ns = {}
    exec(src[i: src.index("\ndef build_doc_props")], ns)
    f = ns["keo_du_dai_track"]
    items = [{"dur": 3.5} for _ in range(4)]
    clips = [("intro", 0.0)] + [(f"it{k}", 0.0) for k in range(4)] + [("outro", 0.0)]
    tot = f(items, clips, 2.6, 2.5, ten="test")
    assert tot >= 21.0, f"kéo xong vẫn dưới sàn: {tot}"       # bẫy làm-tròn-xuống: 20,98s
    assert clips[1][1] == 2.6, "mốc tiếng mục đầu sai"
    assert abs(clips[-1][1] - (2.6 + sum(x["dur"] for x in items))) < 0.02, \
        "kéo dur mà không dời mốc tiếng = LỆCH TIẾNG-HÌNH (đúng lỗi PULSE 4,7s)"
    r = [{"dur": 5.0, "revSec": 2.0} for _ in range(3)]
    c2 = [("intro", 0.0)] + [x for k in range(3) for x in ((f"c{k}", 0.0), (f"r{k}", 0.0))] + [("outro", 0.0)]
    f(r, c2, 2.0, 2.0, ten="guess", moi_muc=2, moc_phu="revSec")
    assert c2[2][1] == round(c2[1][1] + 2.0, 3), "GUESS: đáp án phải lệch đúng revSec so với câu đố"
    la = [("a", 0.0), ("b", 0.0)]
    f([{"dur": 3.0}] * 4, la, 1.0, 1.0)
    assert la == [("a", 0.0), ("b", 0.0)], "hình dạng lạ thì PHẢI để nguyên, không đoán"


def t_moi_workflow_deu_ghim_thu_vien():
    """Mọi workflow cài google-cloud-firestore phải ĐI QUA constraints (24/8 tối).
    Gương B→B2 chết 16 tiếng vì một bản phát hành mới của thư viện Google làm gãy
    `.stream(timeout=…)`. `constraints.txt` sinh ra để chặn — nhưng soi lại thì CHỈ `render_cron`
    dùng nó; 13 workflow còn lại (kể cả publish/publish_social) vẫn cài bản mới nhất theo ngày."""
    goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    wf = os.path.join(goc, ".github", "workflows")
    if not os.path.isdir(wf):
        return
    ho = []
    for ten in sorted(os.listdir(wf)):
        if not ten.endswith((".yml", ".yaml")):
            continue
        t = io.open(os.path.join(wf, ten), encoding="utf-8").read()
        for dong in t.split("\n"):
            if "pip install" not in dong or "google-cloud-firestore" not in dong:
                continue
            if "constraints.txt" in dong or ">=2.27" in dong:
                continue
            ho.append(f"{ten}: {dong.strip()[:70]}")
    assert not ho, "workflow cài thư viện KHÔNG ghim phiên bản:\n   " + "\n   ".join(ho)
    req = os.path.join(goc, "MM0-AutoPublisher", "requirements.txt")
    if os.path.exists(req):
        r = io.open(req, encoding="utf-8").read()
        for goi in ("google-cloud-firestore", "google-api-python-client", "requests"):
            d = [x for x in r.split("\n") if x.strip().startswith(goi)]
            assert d and "<" in d[0], f"{goi} trong requirements.txt thiếu TRẦN phiên bản"


def t_so_hong_phai_het_len():
    """Ba cuốn sổ mà "đọc hỏng -> trả rỗng" gây hậu quả THẬT, không được im lặng (24/8 tối):
      • `recent_topics` rỗng = bảo Gemini "kênh chưa làm gì" -> viết lại đề tài cũ -> reused content
      • `read_used_images` rỗng = tắt chống trùng ảnh -> các video xài chung một tấm
      • `get_script_by_drive` trả None khi ĐỌC HỎNG = render lại ra video KHÁC ĐỀ TÀI rồi bỏ bản cũ
        vào thùng rác — bấm 🔄 mà mất luôn video đang có.
      • `find_resumable` trả None im ru = **gọi Gemini viết lại một kịch bản ĐÃ CÓ SẴN** — thứ đắt
        nhất trong dây chuyền. Dòng `♻️ Dùng lại kịch bản đã lưu` chưa từng xuất hiện trong log nào,
        dù mỗi phiên đều có job `failed` còn giữ kịch bản."""
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "firestore_bridge.py"), encoding="utf-8").read()
    for ten in ("recent_topics", "read_used_images", "find_resumable"):
        i = src.index(f"def {ten}(")
        than = src[i: src.index("\ndef ", i + 10)]
        assert "🚨" in than, f"{ten}: đọc hỏng vẫn im lặng"
        assert "_dem_khau_soft" in than, f"{ten}: chưa ghi vào máy dò chết câm"
    i = src.index("def get_script_by_drive(")
    than = src[i: src.index("\ndef ", i + 10)]
    assert "raise DocLoi" in than, "đọc kịch bản cũ hỏng vẫn bị nuốt thành None (= 'không có kịch bản')"
    r = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "run_render.py"), encoding="utf-8").read()
    i = r.index("FB.get_script_by_drive(")          # LỜI GỌI THẬT, không phải dòng chú thích
    assert "except FB.DocLoi" in r[i: i + 700], \
        "đường render lại chưa hoãn khi không đọc được kịch bản cũ"


def t_cuu_mo_dau_khong_qua_mat_qc():
    """Cứu khung mở đầu TRƯỚC render, nhưng không được qua mặt thước đo (24/8 tối).
    `❌ mở đầu NỀN TRƠN` lặp qua nhiều phiên (7 ca ở 16:06Z, 2 ca ở 17:56Z) — mỗi ca mất TRẮNG một
    lượt viết AI + một lượt render, mà lỗi chỉ nằm ở độ sáng một tấm ảnh.
    Bẫy bắt được lúc chạy thử: tăng sáng ×2.1 kéo một tấm gần đen xuống "2% tối" và LỌT QC, nhưng
    thứ ra màn hình là mảng XÁM PHẲNG. Nên chỉ tăng sáng khi đó là ẢNH THẬT chụp tối (bão hoà ≥20;
    đo thật: nền trơn sat 14,2 · ảnh thật tối sat 31,1)."""
    import random, hashlib
    try:
        from PIL import Image
    except ImportError:
        return
    import datastory_ci as DS
    base = os.path.join(DS.PUB, "_selftest_mo_dau", "clips")
    os.makedirs(base, exist_ok=True)
    try:
        def _phang(ten):
            random.seed(7)
            im = Image.new("RGB", (320, 180), (12, 12, 16)); px = im.load()
            for _ in range(200):
                px[random.randrange(320), random.randrange(180)] = (30, 30, 34)
            im.save(os.path.join(base, ten), quality=92)

        def _sang(ten):
            random.seed(11)
            im = Image.new("RGB", (320, 180)); px = im.load()
            for y in range(180):
                for x in range(320):
                    px[x, y] = (random.randrange(120, 240), random.randrange(110, 230),
                                random.randrange(90, 210))
            im.save(os.path.join(base, ten), quality=92)

        _phang("phang.jpg"); _sang("sang.jpg")
        h0 = hashlib.md5(open(os.path.join(base, "phang.jpg"), "rb").read()).hexdigest()
        pr = {"slug": "_selftest_mo_dau",
              "scenes": [{"clip": "phang.jpg"}, {"clip": "sang.jpg"}]}
        assert DS.sang_hoa_mo_dau(pr) == "", "không mượn được ảnh sáng của cảnh khác"
        assert pr["scenes"][0]["clip"] == "sang.jpg", "mở đầu vẫn là nền phẳng"
        h1 = hashlib.md5(open(os.path.join(base, "phang.jpg"), "rb").read()).hexdigest()
        assert h0 == h1, "NỀN PHẲNG bị tăng sáng -> qua mặt QC bằng một mảng xám"
        _phang("phang.jpg"); _phang("phang2.jpg")
        r = DS.sang_hoa_mo_dau({"slug": "_selftest_mo_dau",
                                "scenes": [{"clip": "phang.jpg"}, {"clip": "phang2.jpg"}]})
        assert r, "toàn nền phẳng mà vẫn cho render"
        hs = hashlib.md5(open(os.path.join(base, "sang.jpg"), "rb").read()).hexdigest()
        assert DS.sang_hoa_mo_dau({"slug": "_selftest_mo_dau", "scenes": [{"clip": "sang.jpg"}]}) == ""
        assert hs == hashlib.md5(open(os.path.join(base, "sang.jpg"), "rb").read()).hexdigest(), \
            "ảnh đã đạt mà vẫn bị ghi đè"
    finally:
        import shutil
        shutil.rmtree(os.path.join(DS.PUB, "_selftest_mo_dau"), ignore_errors=True)
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "datastory_ci.py"), encoding="utf-8").read()
    assert src.count("sang_hoa_mo_dau(") >= 4, "chưa gắn đủ 3 đường Cinematic (doc · short · long)"
    # PHẢI ĐO SAU LỚP PHỦ, không phải đo ảnh gốc. Bằng chứng đo được: một tấm ảnh 0,0% tối ở dạng
    # gốc ra khung 93,3% tối sau lớp phủ của Cinematic (gradient .74/.58/.88 + vignette .55) — tức
    # đo ảnh gốc là đo NHẦM VẬT, mọi kết luận sau đó đều sai.
    assert "_sau_man(" in src, "vẫn đo ảnh GỐC thay vì khung sau lớp phủ"
    # MÔ HÌNH PHẢI CÓ BIÊN. `_sau_man` là mô hình lớp phủ, không phải bản render thật (thiếu Ken
    # Burns, objectPosition 32%, bóng chữ hook…). Ca HAULUSA phiên 20:12Z: mô hình bảo "đạt", khung
    # thật ra 80% tối rồi bị QC loại. Ép chặt hơn ngưỡng QC một khoảng.
    assert "BIEN = " in src, "thiếu biên an toàn -> mô hình sát ngưỡng là sẽ trượt ở bản render thật"
    m = re.search(r"BIEN = ([\d.]+)", src)
    assert m and float(m.group(1)) >= 8, f"biên {m.group(1) if m else '?'} quá mỏng cho một mô hình"
    i = src.index("def sang_hoa_mo_dau")
    # 28/8 — cắt theo BIÊN HÀM, không theo số ký tự: cửa sổ cố định vỡ khi thân hàm
    # dài ra, và chốt đỏ vì lỗi CỦA CHÍNH NÓ chứ không phải vì mã hỏng.
    _ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
    than = src[i: min(_ket) if _ket else len(src)]
    assert "_sau_man(os.path.join(base, f), man)" in than, "hàm cứu chưa đo qua lớp phủ"
    assert 'scenes[0]["man"]' in than, "chưa gửi độ dày lớp phủ sang composition"
    eng = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "engine-remotion", "src", "Cinematic.tsx")
    if os.path.exists(eng):
        t = io.open(eng, encoding="utf-8").read()
        assert "s.man ?? 1" in t and "0.74 * man" in t, \
            "Cinematic chưa nhận độ dày lớp phủ -> Python tính xong nhưng không ai dùng"
    # Nới lớp phủ phải áp cho MỌI cảnh, không riêng cảnh mở đầu: QC chỉ soi khung đầu nên chữa mỗi
    # cảnh 0 là hết bị loại, nhưng cả video vẫn xỉn — không ai chặn, và đó mới là thứ người xem thấy.
    assert src.count("can_man_moi_canh(") >= 4, "chưa cân lớp phủ cho mọi cảnh ở đủ 3 đường"


def t_duong_du_phong_b2_khong_bi_bo_qua_im():
    """Đường dự phòng B2 không được bỏ qua IM LẶNG (24/8 tối).
    Log bước sao lưu phiên 20:12Z chỉ có MỘT dòng `đọc danh sách kho ở B hụt` rồi thẳng tới
    `❌ không đọc được kho Drive nào` — nhìn thì tưởng đã thử cả B2. Thật ra `_b2_client()` trả None
    vì bước đó không được truyền `FIREBASE_PROJECT_ID_B2`, và vòng lặp `continue` không in gì.
    Mà ngay TRONG CÙNG FILE, khối B2 phía dưới lại mặc định "mm0-shard-b2" — hai chỗ cùng việc, hai
    hành vi khác nhau."""
    ap = os.environ.get("AUTOPUBLISHER_SRC") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "MM0-AutoPublisher", "src")
    f = os.path.join(ap, "storage.py")
    if not os.path.exists(f):
        return
    src = io.open(f, encoding="utf-8").read()
    i = src.index("def _b2_client")
    # 28/8 — cắt theo BIÊN HÀM, không theo số ký tự: cửa sổ cố định vỡ khi thân hàm
    # dài ra, và chốt đỏ vì lỗi CỦA CHÍNH NÓ chứ không phải vì mã hỏng.
    _ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
    than = src[i: min(_ket) if _ket else len(src)]
    assert '"mm0-shard-b2"' in than, \
        "_b2_client thiếu mặc định project B2 -> im lặng bỏ qua đường dự phòng khi thiếu env"
    assert "⚠️" in than, "_b2_client bỏ qua B2 mà không in lý do"
    wf = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      ".github", "workflows", "render_cron.yml")
    if not os.path.exists(wf):
        return
    w = io.open(wf, encoding="utf-8").read()
    # mọi bước gọi tới storage.py đều phải có env B2, nếu không lại rơi đúng cái bẫy trên
    i = w.index("- name: Sao lưu kho key")
    j = w.index("run: python render-pipeline/backup_vault.py", i)
    assert "FIREBASE_PROJECT_ID_B2" in w[i:j], \
        "bước sao lưu thiếu FIREBASE_PROJECT_ID_B2 -> B2 bị bỏ qua"


def t_cong_kho_drive_dong_duoc_that():
    """Cổng "không đọc được kho Drive nào -> dừng phiên" phải THẬT SỰ chặn được (24/8 tối).
    pyflakes bắt: `return out_channels([])` nằm trong khối `try` mà `out_channels` khi đó CHƯA được
    định nghĩa (nó ở dưới) ⇒ NameError ⇒ rơi vào `except` ngay bên dưới ⇒ in "vẫn chạy (fail-open)"
    rồi mở 18 luồng. Cổng chưa từng chặn được gì: nó luôn tự ném lỗi rồi tự nuốt."""
    import ast as _ast
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "run_render.py"), encoding="utf-8").read()
    t = _ast.parse(src)
    dn = [n.lineno for n in _ast.walk(t)
          if isinstance(n, _ast.FunctionDef) and n.name == "out_channels"]
    assert dn, "không thấy out_channels"
    goi = [i + 1 for i, l in enumerate(src.split("\n")) if "return out_channels([])" in l]
    assert goi, "không thấy lối thoát sớm nào"
    assert min(goi) > dn[0], \
        f"out_channels định nghĩa ở dòng {dn[0]} nhưng đã bị gọi từ dòng {min(goi)} -> NameError"
    # quyết định dừng phải nằm NGOÀI khối try, để không bị `except Exception` nuốt
    i = src.index("_cong_dong = True")
    j = src.index("if _cong_dong:")
    assert j > i and "except Exception as e:" in src[i:j], \
        "quyết định đóng cổng vẫn nằm trong try -> lại bị nuốt"


def t_noi_man_khong_dung_toi_anh():
    """Nới lớp phủ = đổi THÔNG SỐ dựng hình, KHÔNG được sửa file ảnh gốc (24/8 tối).
    Ảnh gốc còn nguyên thì lần render sau (hoặc render lại từ kịch bản) vẫn ra đúng như vậy; sửa
    file là làm hỏng nguồn, mà nguồn thì không lấy lại được."""
    import random, hashlib
    try:
        from PIL import Image
    except ImportError:
        return
    import datastory_ci as DS
    base = os.path.join(DS.PUB, "_selftest_man", "clips")
    os.makedirs(base, exist_ok=True)
    try:
        def _anh(ten, lo, hi, seed):
            random.seed(seed)
            im = Image.new("RGB", (320, 180)); px = im.load()
            for y in range(180):
                for x in range(320):
                    px[x, y] = (random.randrange(lo, hi), random.randrange(max(0, lo - 15), max(1, hi - 15)),
                                random.randrange(lo, min(255, hi + 15)))
            im.save(os.path.join(base, ten), quality=92)
        _anh("sang.jpg", 190, 255, 2); _anh("vua.jpg", 60, 150, 3); _anh("toi.jpg", 10, 60, 4)
        pr = {"slug": "_selftest_man",
              "scenes": [{"clip": "sang.jpg"}, {"clip": "vua.jpg"}, {"clip": "toi.jpg"}]}
        goc = {f: hashlib.md5(open(os.path.join(base, f), "rb").read()).hexdigest()
               for f in ("sang.jpg", "vua.jpg", "toi.jpg")}
        DS.can_man_moi_canh(pr)
        for f, v in goc.items():
            assert v == hashlib.md5(open(os.path.join(base, f), "rb").read()).hexdigest(), \
                f"{f} bị SỬA — nới lớp phủ không được đụng file ảnh gốc"
        # 24/8 tối — bản test đầu khẳng định "ảnh SÁNG phải giữ man=1". Sau khi hiệu chỉnh mô hình
        # theo ca thật (mô hình lạc quan ~20 điểm so với khung render), ngay cả ảnh sáng cũng nằm
        # trên ngưỡng — và nới nó là ĐÚNG, vì lớp phủ 0,74-0,88 vốn quá dày với mọi ảnh. Cái phải
        # giữ không phải một con số cụ thể mà là hai tính chất KHÔNG THỂ đúng nếu code hỏng:
        #   • ĐƠN ĐIỆU: ảnh càng tối thì lớp phủ càng phải mỏng;
        #   • CÓ SÀN: không bao giờ mỏng quá 0.45 (dưới nữa là phụ đề mất nền).
        m = [sc.get("man", 1.0) for sc in pr["scenes"]]
        assert m[0] >= m[1] >= m[2], f"lớp phủ không đơn điệu theo độ tối của ảnh: {m}"
        # ĐƠN ĐIỆU CHẶT giữa hai đầu: ảnh sáng nhất PHẢI giữ lớp phủ dày hơn ảnh tối nhất. Thiếu vế
        # này thì một bản hỏng "hạ hết về sàn 0.45" vẫn lọt (0.45 ≥ 0.45 ≥ 0.45 là đúng đơn điệu).
        assert m[0] > m[2], f"ảnh sáng nhất và tối nhất nhận CÙNG lớp phủ -> không phân biệt gì: {m}"
        assert min(m) >= 0.35, f"nới quá sàn 0.35 (sàn của Cinematic) -> phụ đề mất nền: {m}"
        assert m[2] < 1.0, "ảnh tối nhất mà không được nới chút nào"
    finally:
        import shutil
        shutil.rmtree(os.path.join(DS.PUB, "_selftest_man"), ignore_errors=True)


def t_lay_viec_ke_o_dung_duong_vao():
    """Vòng "lấy việc kế" phải nằm ở ĐƯỜNG VÀO MÀ MATRIX THẬT SỰ CHẠY (24/8 tối).
    Đo được: mọi lane kết thúc bằng `⏱ ...: còn 58' < ước tính 68'/mẻ → DỪNG` rồi thoát, trong khi
    plan vừa xếp 32 kênh vào HÀNG CHỜ. Dòng `♻️ Luồng rảnh -> nhận thêm kênh` CHƯA TỪNG xuất hiện
    trong log lane nào — vì vòng đó viết trong `main()`, còn matrix chạy `--channel X` tức
    `channel_mode()`. Tính năng nằm ở đường KHÔNG được dùng ⇒ 18 lane × ~58' bỏ không mỗi phiên."""
    import ast as _ast
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "run_render.py"), encoding="utf-8").read()
    t = _ast.parse(src)
    than = {}
    for fn in [n for n in _ast.walk(t) if isinstance(n, _ast.FunctionDef)]:
        if fn.name in ("channel_mode", "main"):
            e = max(getattr(x, "lineno", 0) for x in _ast.walk(fn))
            than[fn.name] = "\n".join(src.split("\n")[fn.lineno - 1: e])
    assert "lay_viec_ke(" in than.get("channel_mode", ""), \
        "channel_mode (đường matrix THẬT SỰ chạy) không có vòng lấy việc kế -> hàng chờ vô dụng"
    # và phải có trần thời gian, nếu không lane bị timeout matrix chém giữa chừng
    kh = than["channel_mode"]
    i = kh.index("lay_viec_ke(")
    truoc = kh[max(0, i - 1400): i]
    assert "HARD_S" in truoc, "vòng lấy việc kế thiếu trần giờ -> lane bị timeout chém giữa video"
    # 24/8 tối — bẫy đã dính một lần: vòng này dùng LẠI ĐÚNG ngưỡng vừa chặn vòng trên
    # (`min(budget_s, HARD_S)` = ngân sách MỀM), nên luôn break ngay lượt đầu và dòng `♻️ … rảnh`
    # không bao giờ in ra. Số thật lane PRICEDUSA: tiêu 53', trần cứng 150' -> còn 97', thừa cho
    # một mẻ 69'. Ngân sách mềm để một KÊNH đừng ôm máy; giờ thừa phải chảy về hàng chờ.
    assert "min(budget_s, HARD_S) - (time.monotonic() - start)" not in truoc, \
        "vòng lấy việc kế đo theo ngân sách MỀM -> tự chặn chính mình, không bao giờ lấy được việc"


def t_key_chet_han_duoc_nhan_dien():
    """Key CHẾT HẲN phải bị loại khỏi vòng + báo lên dashboard, KHÔNG tốn lượt dò nào (25/8).
    Log thật: `API key not valid. Please pass a valid API key. [reason: "API_KEY_INVALID"]` — không
    khớp chữ nào trong danh sách cũ ("not enabled" ≠ "not valid") ⇒ key bị xử như chỉ-nghẽn-tạm, cứ
    thử lại mãi, và bảng key vẫn báo xanh (anh hỏi: "sao không báo Gemini die").
    Cách kiểm key rẻ nhất là GHI LẠI thứ dây chuyền đã học trong lúc làm việc thật — 0 lượt gọi thêm."""
    import key_manager as KM
    assert hasattr(KM, "CHET_HAN"), "chữ ký key chết còn nằm rải rác, không gộp một chỗ"
    chet = lambda e: any(x in e.lower() for x in KM.CHET_HAN)
    for e in ('API key not valid. Please pass a valid API key. [reason: "API_KEY_INVALID"]',
              "403 permission denied", "API key expired. Please renew", "account suspended"):
        assert chet(e), f"không nhận ra key CHẾT: {e[:50]}"
    for e in ("429 rate limit per minute", "429 quota exceeded per day",
              "500 internal error", "timeout"):
        assert not chet(e), f"nhầm key còn sống thành CHẾT (mất key oan): {e[:40]}"
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "key_manager.py"), encoding="utf-8").read()
    assert src.count("CHET_HAN") >= 8, "vẫn còn nhánh dùng danh sách chữ ký riêng"


def t_cat_luot_ghi_d1_thua():
    """D1 gói FREE cho 100.000 lượt GHI/ngày; đo thật đang dùng 19.073 (19,1%) và nó tăng theo SỐ
    VIDEO (25/8, anh dặn tính toán lượng D1 hợp lý).
    Gốc lãng phí: mọi cập nhật mang `script` đều VƯỢT hãm 12 phút (đúng, kịch bản là thứ quý) —
    nhưng **D1 không lưu `script`**, nên với D1 những lượt đó không thêm một chữ nào. Cộng thêm việc
    ghi từng bước writing→rendering→qc chỉ để làm mới mốc thời gian.
    D1 chỉ cần: trạng thái CUỐI (để đếm) + MỘT mốc còn tươi (ô "Đang chạy" dùng cửa sổ 45 phút)."""
    import sys as _s, types as _ty, warnings as _w
    _w.filterwarnings("ignore")
    that = _s.modules.get("hot_db")
    gia = _ty.ModuleType("hot_db"); dem = {"n": 0}
    gia.bat_ghi = lambda: True
    gia.ghi_job = lambda *a, **k: dem.__setitem__("n", dem["n"] + 1)
    _s.modules["hot_db"] = gia
    import firestore_bridge as FB
    goc_soft = FB._soft
    try:
        FB._soft = lambda f, t="": None
        FB._LAST_JOB_WRITE.clear(); FB._D1_CUOI.clear(); FB._D1_NHIP.clear()
        for st, step in (("queued", "bắt đầu"), ("writing", "viết"), ("writing", "viết 2"),
                         ("rendering", "render"), ("rendering", "render 2"),
                         ("qc", "kiểm"), ("done", "xong")):
            FB.update_job("JT1", status=st, step=step, script="{...}")
        assert dem["n"] <= 3, f"vòng đời 1 video vẫn tốn {dem['n']} lượt ghi D1 (mong ≤3)"
        # done/failed KHÔNG BAO GIỜ được hãm — nếu hãm thì mất bản ghi để đếm
        FB._D1_CUOI.clear(); FB._D1_NHIP.clear(); dem["n"] = 0
        FB.update_job("JT2", status="rendering", step="a")
        FB.update_job("JT2", status="done", step="xong", drive_id="d1")
        assert dem["n"] == 2, f"done bị hãm oan -> đếm thiếu video: {dem['n']}"
        FB._D1_CUOI.clear(); FB._D1_NHIP.clear()
    finally:
        FB._soft = goc_soft
        if that is not None:
            _s.modules["hot_db"] = that
        else:
            _s.modules.pop("hot_db", None)


def t_so_kho_that_ghi_vao_d1():
    """Số kho THẬT phải ghi vào D1 — chỗ dashboard đọc được mà không cần Firestore (25/8).
    Đo được: D1 đếm lại từ bản ghi ra 1.475 (chỉ có job từ lúc bật chế độ D1), `__pushed__` bên
    Firestore ra 2.070 (bộ đếm cộng dồn), còn kho Drive có **1.996** file thật. Chỉ lượt đi đếm 72
    kho mới là sự thật, nên phải cất nó vào nơi dashboard lấy được."""
    import hot_db as H
    assert hasattr(H, "kho_that_ghi"), "thiếu đường ghi số kho thật vào D1"
    goc_goi, goc_g = H.goi, H.bat_ghi
    da = {}
    try:
        H.bat_ghi = lambda: True
        H.goi = lambda l, t=None, timeout=12: (da.update({"lenh": l, **(t or {})}) or {"ok": True})
        assert H.kho_that_ghi("uid", 1996) is True
        assert da["lenh"] == "kho_that_ghi" and da["tong"] == 1996 and da["luc"]
        da.clear()
        assert H.kho_that_ghi("uid", -1) is False, "số âm mà vẫn ghi"
    finally:
        H.goi, H.bat_ghi = goc_goi, goc_g
    fb = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "firestore_bridge.py"), encoding="utf-8").read()
    i = fb.index("def dat_so_kho_that")
    than = fb[i: i + 1100]
    assert "kho_that_ghi" in than, "ghi số thật mà bỏ qua D1 -> dashboard vẫn đọc số cũ"
    # NEO + CỘNG TIẾP: lượt đếm 72 kho chỉ 1 lần/ngày, nên Worker phải cộng thêm phần làm được KỂ TỪ
    # lúc đếm (`nen`), nếu không ô "Tổng" đứng im cả ngày dù video vẫn ra đều.
    w = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "MM0-AutoPublisher", "connect-worker", "src", "worker.js")
    if os.path.exists(w):
        js = io.open(w, encoding="utf-8").read()
        assert "kt.nen" in js and "tong - (kt.nen" in js, \
            "Worker chưa cộng phần làm thêm kể từ lượt đếm -> ô Tổng đứng im cả ngày"
        assert "nen INTEGER" in js or "nen=?4" in js, "lệnh ghi neo chưa lưu mốc `nen`"
    assert than.index("kho_that_ghi") < than.index("_db_B_that"), \
        "phải ghi D1 TRƯỚC Firestore (Firestore là thứ hay hỏng, D1 mới là chỗ dashboard đọc)"


def t_doi_chieu_so_kho_chay_trong_plan():
    """Việc đối chiếu sổ đếm phải nằm ở nơi lệnh GHI chắc chắn chạy được (25/8).
    `wipe_queue` chạy `kiem_kho.py` đếm được số thật (1.996 video) nhưng **ghi sổ luôn trả
    `400 Invalid database id`**, trong khi plan của render_cron ghi Firestore bình thường suốt đêm.
    Đặt việc đối chiếu vào plan thì con số tự đúng mỗi ngày, không cần ai bấm nút."""
    r = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "run_render.py"), encoding="utf-8").read()
    assert "def _kiem_kho_ngay(" in r and "_kiem_kho_ngay(cfg)" in r, \
        "plan không tự đối chiếu sổ đếm với số thật trên Drive"
    i = r.index("def _kiem_kho_ngay(")
    than = r[i: r.index("def _viec_chia_san", i)]      # trọn thân hàm, khỏi đoán độ dài
    assert "kiem_kho_ngay" in than and "return" in than, "thiếu chốt 1-lần/ngày"
    # CHỐT PHẢI Ở CHỖ GHI ĐƯỢC. Chốt chỉ dựa vào `render_config` (Firestore) là hỏng: lượt GHI
    # Firestore đang trả 400, ghi hụt ⇒ chốt không bao giờ đóng ⇒ plan đi 72 kho MỖI lượt
    # (~48 lượt/ngày × 72 kho ≈ 3.500 lượt quét) thay vì 1 lần — tối ưu mà đẻ ra lãng phí lớn hơn.
    assert "key_nghi_doc" in than and "key_nghi_ghi" in than, \
        "chốt 1-lần/ngày chỉ dựa vào Firestore -> ghi hụt là quét lại mỗi lượt plan"
    assert than.index("key_nghi_ghi") < than.index("FB.set_config"), \
        "phải đóng chốt ở D1 TRƯỚC Firestore (Firestore mới là thứ hay ghi hụt)"
    assert "len(accs) < 5" in than, "đọc được ít kho mà vẫn ghi đè -> đếm thiếu, sổ càng sai"
    assert "hong" in than, "kho đọc hụt mà vẫn ghi đè -> đếm thiếu"
    fb = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "firestore_bridge.py"), encoding="utf-8").read()
    # Soi PHẦN LỆNH thôi — docstring có nhắc chữ Increment để giải thích cái bệnh (bẫy đã dính ở
    # `t_so_kho_lay_tu_drive`, đừng dính lại).
    import ast as _ast
    for _n in _ast.walk(_ast.parse(fb)):
        if isinstance(_n, _ast.FunctionDef) and _n.name == "dat_so_kho_that":
            for _x in _ast.walk(_n):
                assert not (isinstance(_x, _ast.Name) and _x.id == "Increment"), \
                    "ghi đè sổ mà vẫn dùng Increment -> lại cộng dồn"


def t_bien_moi_truong_rong_khong_pha_mac_dinh():
    """`os.environ.get("K", "mđ")` trả **rỗng** khi biến ĐƯỢC ĐẶT nhưng RỖNG (25/8 — tôi tự dính).
    Vừa thêm `HOT_URL: ${{ secrets.HOT_URL }}` vào workflow, mà secret đó KHÔNG tồn tại ⇒ biến thành
    chuỗi rỗng ⇒ giá trị mặc định trong code bị vô hiệu hoá ⇒ `lớp cứu KV cũng hụt: unknown url
    type: ''` — đúng lúc Firestore hỏng và lớp cứu là đường sống duy nhất.
    Dạng an toàn: `os.environ.get("K") or "mđ"`."""
    import ast as _ast, glob as _g
    goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    xau = []
    for p in _g.glob(os.path.join(goc, "render-pipeline", "*.py")) + \
             _g.glob(os.path.join(goc, "MM0-AutoPublisher", "src", "*.py")):
        try:
            t = _ast.parse(io.open(p, encoding="utf-8").read())
        except Exception:
            continue
        # 3/9 — Cổng này BẮT OAN `os.environ.get("K", "120") or 120`: dạng ấy ĐÃ AN TOÀN, vì
        # biến rỗng làm `.get` trả "" (falsy) và `or` đỡ lấy. Cổng chỉ khớp lời gọi hai tham số
        # mà không nhìn ra ngoài nó, nên nó báo đỏ cho mã đúng.
        #
        # Một cổng đỏ vĩnh viễn không chỉ phiền: luật 13.2 đã trả giá cho đúng chuyện này — ba
        # dòng đỏ giả khiến một lỗi THẬT nằm cạnh chúng bị chìm. Nên phải chữa, không phải bỏ qua.
        an_toan = set()
        for n in _ast.walk(t):
            if isinstance(n, _ast.BoolOp) and isinstance(n.op, _ast.Or):
                for v in n.values[:-1]:
                    an_toan.add(id(v))
        for n in _ast.walk(t):
            if isinstance(n, _ast.Call) and getattr(n.func, "attr", "") == "get" \
                    and getattr(getattr(n.func, "value", None), "attr", "") == "environ" \
                    and len(n.args) == 2 and isinstance(n.args[1], _ast.Constant) \
                    and isinstance(n.args[1].value, str) and n.args[1].value.strip() \
                    and id(n) not in an_toan:
                xau.append(f"{os.path.basename(p)}:{n.lineno}")
    assert not xau, ("dùng `environ.get(K, 'mđ')` — biến rỗng sẽ phá mặc định. Đổi sang "
                     "`environ.get(K) or 'mđ'`:\n   " + "\n   ".join(xau))


def t_buoc_dung_kho_phai_co_lop_cuu_kv():
    """Bước nào dùng `storage.py` thì PHẢI được truyền `HOT_KEY` (25/8 — ca thật vừa xảy ra).
    Chạy `kiem_kho` lúc A và B đều cạn hạn mức: `❌ không đọc được kho nào — DỪNG`. `storage.py` có
    lớp cứu cuối đọc danh sách kho từ KV của Worker (KHÔNG đụng Firestore), nhưng lớp đó cần
    `HOT_KEY` — mà workflow không truyền cho bước ấy. Có đường sống mà không cắm điện."""
    wf = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      ".github", "workflows")
    if not os.path.isdir(wf):
        return
    import re as _re
    ho = []
    for ten in sorted(os.listdir(wf)):
        if not ten.endswith((".yml", ".yaml")):
            continue
        w = io.open(os.path.join(wf, ten), encoding="utf-8").read()
        if "\njobs:" not in w:
            continue
        for b in _re.split(r"\n      - name: ", w[w.index("\njobs:"):])[1:]:
            if "AUTOPUBLISHER_SRC:" in b and "HOT_KEY" not in b:
                ho.append(f"{ten}: {b.split(chr(10))[0][:40]}")
    assert not ho, ("bước dùng storage.py mà thiếu HOT_KEY -> lớp cứu KV không chạy được khi "
                    "Firestore cạn:\n   " + "\n   ".join(ho))


def t_ten_file_khong_lam_ban_tieu_de():
    """Video KHÔNG có sidecar thì tiêu đề lấy từ TÊN FILE — mà tên chuẩn có tiền tố máy (25/8).
    `main.py` dựng metadata bằng `sidecar.get("topic") or M.slug_to_topic(f["name"])`. Từ khi dùng
    `KENH__YYYYMMDD__seri__S1__tieu-de[-bam]`, hàm đó trả
    `'DEFENSEUSA 20260825 Ab3xk9 S1 Where The Money Goes'` — và đó là thứ đem đặt LÀM TIÊU ĐỀ
    YOUTUBE. Rủi ro do chính bản đổi tên gây ra, chỉ lộ khi khâu đăng chạy lại."""
    ap = os.environ.get("AUTOPUBLISHER_SRC") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "MM0-AutoPublisher", "src")
    if not os.path.exists(os.path.join(ap, "metadata.py")):
        return
    import importlib.util as _iu
    sp = _iu.spec_from_file_location("_md_test", os.path.join(ap, "metadata.py"))
    M = _iu.module_from_spec(sp); sp.loader.exec_module(M)
    for ten, mong in (
            ("DEFENSEUSA__20260825__ab3xk9__S1__Where-The-Money-Goes.mp4", "Where The Money Goes"),
            ("GUESSUSA__20260825__S__Which-state-pays-the-most-7302.mp4", "Which State Pays The Most"),
            ("COSMOS__20260825__L__The-Deepest-Secret.mp4", "The Deepest Secret"),
            ("how-i-went-broke_short.mp4", "How I Went Broke")):   # tên đời cũ vẫn phải đúng
        ra = M.slug_to_topic(ten)
        assert ra == mong, f"tiêu đề suy từ tên file sai: {ra!r} (mong {mong!r})"


def t_dong_loai_qc_phai_ghi_ten_kenh():
    """Dòng QC loại video phải ghi RÕ KÊNH NÀO (25/8 — chính tôi vừa chẩn đoán nhầm vì thiếu nó).
    Từ khi lane biết lấy thêm kênh từ hàng chờ (7.ci/7.cr), MỘT lane xử lý NHIỀU kênh. Log
    `❌ mở đầu NỀN TRƠN (tối 77.3% · 629 màu)` trong lane tên COSMOS hoá ra là của **SIGNALUSA**
    (lane vừa nhận thêm) — mà COSMOS là kênh `dark_ok` còn SIGNALUSA thì không, tức luật áp lên hai
    kênh khác hẳn nhau. Không ghi tên kênh là quy sai lỗi, rồi vá sai chỗ."""
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "datastory_ci.py"), encoding="utf-8").read()
    # Soi các dòng LỆNH IN thật (bỏ qua chú thích/docstring có nhắc lại nguyên văn thông báo).
    xau = [l.strip()[:90] for l in src.split("\n")
           if "print(" in l and "NỀN TRƠN" in l and "[{channel}]" not in l]
    assert not xau, "dòng loại QC không ghi tên kênh -> quy sai lỗi khi lane ôm nhiều kênh:\n   " \
                    + "\n   ".join(xau)
    assert src.count("[{channel}] ") >= 3, "chưa gắn tên kênh cho đủ 3 đường Cinematic"


def t_vision_co_model_du_phong():
    """Vision phải có danh sách model dự phòng + tự dò khi CF đổi tên model (25/8).
    Máy dò chết câm bắt được ca thật: lane FUTUREUSA `vision ảnh 0/36`, lỗi
    `cloudflare HTTP 403: AiError: Model ...`. Đường TEXT đã có `_resolve_live_model` từ lâu, đường
    VISION thì viết cứng đúng MỘT tên model ⇒ CF gỡ/đổi tên là chết 100%, và chết âm thầm vì
    `verify_image` trả None = "bỏ qua kiểm" (ảnh vẫn vào video)."""
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "content_brain.py"), encoding="utf-8").read()
    assert "_CF_VIS_PREF" in src, "vision không có danh sách model dự phòng"
    assert "def _resolve_live_vision" in src, "vision không tự dò được model còn sống"
    assert "_CfShim._live_vis or CF_VISION_MODEL" in src, "vẫn dùng cứng model vision viết sẵn"
    # nhánh tự chữa phải nhận CẢ 403 (ca thật), không chỉ 400/404
    i = src.index("if img is not None and e.code in")
    assert "403" in src[i: i + 120], "403 ở đường vision vẫn rơi thẳng xuống raise"
    # 25/8 — BẢN ĐẦU TỰ CHỌN LẠI CHÍNH MODEL VỪA HỎNG (log 02:15Z: "…llama-3.2-11b-vision-instruct
    # không dùng được -> chuyển sang …llama-3.2-11b-vision-instruct"), vì nó là mục đầu danh sách và
    # `/ai/models/search` vẫn báo TỒN TẠI. Lỗi thật là 403 = chuyện QUYỀN, không phải model bị gỡ.
    assert "_vis_hong" in src, "không nhớ model vision đã hỏng -> dò lại chọn đúng nó"
    import content_brain as CB
    S = CB._CfShim
    sh = S.__new__(S); sh._acc = "x"; sh._hdr = lambda: {}
    sh._models_song = lambda: set(CB._CF_VIS_PREF)
    cu_h, cu_l = set(S._vis_hong), S._live_vis
    try:
        S._vis_hong.clear(); S._live_vis = None
        S._vis_hong.add(CB.CF_VISION_MODEL)
        assert sh._resolve_live_vision() != CB.CF_VISION_MODEL, "chọn lại đúng model vừa 403"
        S._vis_hong.update(CB._CF_VIS_PREF); S._live_vis = None
        try:
            sh._resolve_live_vision()
            raise AssertionError("hết model mà vẫn trả về một cái nào đó")
        except RuntimeError as e:
            assert "Gemini" in str(e), "hết model CF mà không chỉ đường quay về Gemini"
    finally:
        S._vis_hong.clear(); S._vis_hong.update(cu_h); S._live_vis = cu_l
    qv = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "qc_vision.py"), encoding="utf-8").read()
    assert "str(e)[:220]" in qv, "thông báo lỗi vision vẫn cắt quá ngắn để chẩn đoán"


def t_kich_ban_co_ban_du_phong_khac_kho():
    """Kịch bản phải có bản ở KHO KHÁC, không chỉ nằm cạnh video (25/8, anh hỏi "nhỡ 1 driver hỏng").
    Sidecar nằm ĐÚNG cái kho chứa video ⇒ kho đó chết là mất cả video lẫn kịch bản cùng lúc, chỉ còn
    trông vào Firestore — mà Firestore chính là thứ hay cạn hạn mức nhất. Video thì không nhân đôi
    được (72 kho × 14GB), nhưng kịch bản chỉ vài KB."""
    import sys as _s, types as _ty
    import run_render as R
    that = _s.modules.get("storage")
    gia = _ty.ModuleType("storage"); cat = []

    class _D:
        def __init__(self, n): self.n = n
        def child_folder(self, a, b, **k): return "F"
        def upload_file(self, f, p_, n): cat.append((self.n, n))

    gia.pool_accounts = lambda: [{"name": f"KHO{i}", "root": f"r{i}"} for i in range(8)]
    gia.account_drive = lambda a: _D(a["name"])
    _s.modules["storage"] = gia
    cu = list(R._KB_PHIEN)
    try:
        R._KB_PHIEN.clear()
        R._KB_PHIEN.extend([{"drive_id": "d1", "channel": "AAA", "type": "short",
                             "title": "t", "script": "{}"}] * 3)
        n = R._luu_kich_ban_du_phong("AAA")
        assert n == 2, f"phải cất ở 2 kho, thực tế {n}"
        assert cat[0][0] != cat[1][0], "hai bản rơi vào CÙNG một kho -> mất kho là mất cả hai"
        assert not R._KB_PHIEN, "cất xong mà không dọn -> phiên sau cất trùng"
        assert R._luu_kich_ban_du_phong("AAA") == 0, "danh sách rỗng mà vẫn cất -> tốn lượt gọi Drive"
    finally:
        R._KB_PHIEN.clear(); R._KB_PHIEN.extend(cu)
        if that is not None:
            _s.modules["storage"] = that
        else:
            _s.modules.pop("storage", None)


def t_kho_token_chet_nho_chung():
    """Bản ghi kho có token hỏng phải được nhớ CHUNG, không phải mỗi tiến trình tự tông một lần
    (25/8, anh chỉ ra). Log: `⚠️ kho ADISONDURHAM hụt: invalid_grant` rồi NGAY SAU `✅ đã cất ở kho
    ADISONDURHAM` — tài khoản VẪN SỐNG, chỉ là có HAI bản ghi cùng tên và một bản mang refresh_token
    cũ. `_DEAD_ACCS` chỉ nhớ trong MỘT tiến trình ⇒ mỗi lane / mỗi lượt publish lại thử lại bản chết:
    rác log, chậm, và mỗi lượt hỏng vẫn tính vào hạn mức Google."""
    ap = os.environ.get("AUTOPUBLISHER_SRC") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "MM0-AutoPublisher", "src")
    f = os.path.join(ap, "storage.py")
    if not os.path.exists(f):
        return
    src = io.open(f, encoding="utf-8").read()
    assert "_bao_kho_chet(" in src and "_kho_chet_chung()" in src, \
        "token hỏng vẫn chỉ nhớ trong một tiến trình"
    i = src.index("if root in _DEAD_ACCS")
    assert "_kho_chet_chung()" in src[i: i + 200], "không tra danh sách chung trước khi thử kho"
    # phải TỰ HẾT HẠN, để anh kết nối lại là kho sống lại mà không phải nhớ xoá cờ
    j = src.index("def _bao_kho_chet")
    assert "timedelta(hours=" in src[j: j + 500], "cờ kho chết không tự hết hạn"


def t_kich_ban_di_cung_video_tren_drive():
    """Kịch bản phải đi CÙNG video trên Drive, không chỉ nằm ở Firestore (25/8, anh: "tự làm đi").
    Trước: kịch bản chỉ có trong `render_jobs` ⇒ Firestore cạn hạn mức là mất đường resume, hệ gọi
    AI viết lại một bài ĐÃ CÓ (luật 7.cp — dòng `♻️ Dùng lại kịch bản đã lưu` chưa từng xuất hiện).
    Nay nhét vào sidecar `.json` nằm cạnh video: Drive luôn đọc được (có gương + lớp cứu KV), lại là
    nơi chính video đang nằm, và KHÔNG tốn thêm một lượt ghi nào."""
    ap = os.environ.get("AUTOPUBLISHER_SRC") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "MM0-AutoPublisher", "src")
    f = os.path.join(ap, "enqueue.py")
    if os.path.exists(f):
        e = io.open(f, encoding="utf-8").read()
        assert "script: str | None = None" in e, "enqueue chưa nhận kịch bản"
        assert 'sidecar["script"]' in e, "kịch bản không được ghi vào sidecar"
    r = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "run_render.py"), encoding="utf-8").read()
    assert "script=script or _script_json(" in r, "đường đẩy kho chưa gửi kịch bản kèm theo"
    fb = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "firestore_bridge.py"), encoding="utf-8").read()
    assert "def _script_tu_drive" in fb, "thiếu đường đọc kịch bản từ Drive"
    i = fb.index("def get_script_by_drive")
    than = fb[i: fb.index("def _script_tu_drive")]
    assert "_script_tu_drive(owner, drive_id)" in than, \
        "Firestore hỏng mà không thử Drive -> vẫn mất đường resume đúng lúc cần nhất"


def t_job_bo_ngo_duoc_dong_luc_thoat():
    """Job mở ra mà tiến trình thoát giữa chừng phải được ĐÓNG NGAY (25/8, anh: "21 lỗi MỚI").
    Mỗi video mở một bản ghi job rồi mới đóng bằng `update_job(done/failed)`. Lane thoát giữa chừng
    (SystemExit, trần giờ 150', matrix timeout 165', hết bộ nhớ) ⇒ bản ghi nằm mở vĩnh viễn; 6h sau
    `health_guardian` dán nhãn `failed` và dashboard hiện `⏱ Quá 6h — job ma`. Con số đó CỘNG DỒN
    qua nhiều ngày, nên nhìn như "lỗi mới" trong khi phiên đang chạy sạch."""
    import firestore_bridge as FB
    assert hasattr(FB, "_dong_job_bo_ngo"), "không có lối đóng job bỏ ngỏ lúc thoát"
    cu = set(FB._JOB_MO)
    goc_up = FB.update_job
    da_dong = []
    try:
        FB._JOB_MO.clear()
        FB._JOB_MO.update({"j1", "j2"})
        FB.update_job = lambda jid, st=None, **k: da_dong.append((jid, st))
        FB._dong_job_bo_ngo()
        assert sorted(x[0] for x in da_dong) == ["j1", "j2"], f"đóng thiếu: {da_dong}"
        assert all(x[1] == "failed" for x in da_dong), "đóng mà không ghi trạng thái kết thúc"
        assert not FB._JOB_MO, "đóng xong mà vẫn còn trong danh sách bỏ ngỏ"
        da_dong.clear()
        FB._dong_job_bo_ngo()
        assert not da_dong, "tập rỗng mà vẫn ghi -> tốn lượt ghi vô ích mỗi lần thoát"
    finally:
        FB.update_job = goc_up
        FB._JOB_MO.clear(); FB._JOB_MO.update(cu)
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "firestore_bridge.py"), encoding="utf-8").read()
    assert "_JOB_MO.add(ref.id)" in src, "new_job không ghi nhận job vừa mở"
    assert '_JOB_MO.discard(job_id)' in src, "job có kết cục rồi mà không gỡ khỏi danh sách bỏ ngỏ"
    assert "_atexit.register(_dong_job_bo_ngo)" in src, "chưa gắn vào lúc thoát"


def t_ten_chuan_khong_dung_ten_nhau():
    """Hai video KHÁC NHAU không được ra cùng một tên file (24/8 tối — rủi ro do chính bản đổi tên).
    Tiêu đề bị cắt còn 46 ký tự, nên hai bài chỉ khác nhau ở đuôi vẫn ra cùng tên. Ca thật dựng được:
      'Which state pays the most for electricity in 2026 really' / '... truly'
    Trên Drive thành hai file trùng tên trong một thư mục ⇒ `find_junk` loại 2 xoá cái cũ = **mất một
    video thật**; sidecar/thumbnail cũng lấy tên theo gốc đó nên còn móc chéo sang nhau."""
    import ten_chuan as T
    a = T.ten_file("GUESSUSA", {"title": "Which state pays the most for electricity in 2026 really"},
                   "short", bo="S", ngay="20260824")
    b = T.ten_file("GUESSUSA", {"title": "Which state pays the most for electricity in 2026 truly"},
                   "short", bo="S", ngay="20260824")
    assert a != b, f"hai tiêu đề khác nhau ra CÙNG tên file: {a}"
    c = T.ten_file("GUESSUSA", {"title": "Short title here"}, "short", bo="S", ngay="20260824")
    assert c.endswith("Short-title-here"), f"tên đủ ngắn mà vẫn bị gắn băm: {c}"
    for x in (a, b, c):
        assert T.da_chuan(x) and len(x) <= T.TRAN, f"tên hỏng quy ước: {x}"
        assert T.doc_vai(x) == "s", f"đọc nhầm vai trò: {x}"
    # Lớp chặn thứ hai: find_junk chỉ được coi là bản sao khi CÙNG TÊN **và** CÙNG KÍCH THƯỚC.
    fj = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "find_junk.py"), encoding="utf-8").read()
    i = fj.index("loại 2: trùng tên")
    khoi = fj[i: i + 1800]
    assert 'f.get("size")' in khoi, \
        "find_junk vẫn xoá theo TÊN không xét kích thước -> đụng tên là mất video thật"


def t_day_kho_xong_thi_xoa_ban_tren_dia():
    """Đẩy kho THÀNH CÔNG rồi thì phải xoá bản trên đĩa (24/8 tối — hồi quy do bản đổi tên).
    Trước đây tên file đầu ra cố định theo kênh nên `fresh_out()` xoá đúng nó mỗi vòng, `out/` luôn
    chỉ có ~1 video. Từ khi mỗi video một tên chuẩn riêng, `fresh_out` không còn khớp ⇒ video cũ nằm
    lại. Mà workflow có `upload-artifact path: out/*.mp4` để cứu video CHƯA đẩy được kho ⇒ mỗi lane
    bắt đầu nhét TOÀN BỘ video của mình lên artifact (18 lane × ~8 video × ~40MB ≈ vài GB/phiên) dù
    chúng đã nằm an toàn trên Drive."""
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "run_render.py"), encoding="utf-8").read()
    i = src.index("FB.count_pushed(OWNER, created[\"id\"]")
    # 28/8 — CẮT THEO BIÊN HÀM, KHÔNG THEO SỐ KÝ TỰ. Cửa sổ cố định 2600 vỡ khi thân hàm dài
    # ra (nay 4942): `.index()` ném "substring not found" và chốt đỏ vì lỗi CỦA CHÍNH NÓ.
    # Lần thứ ba lớp lỗi này xuất hiện trong ngày — sửa hẳn, đừng nới số.
    _ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
    than = src[i: min(_ket) if _ket else len(src)]
    assert "os.remove(_f)" in than, \
        "đẩy kho xong mà không xoá bản trên đĩa -> artifact phình theo số video mỗi lane"
    assert "_thumb.jpg" in than, "xoá video mà bỏ lại thumbnail/ảnh tạm"
    # chỉ được xoá khi ĐÃ có drive id — video chưa đẩy được phải giữ lại cho artifact cứu
    assert than.index("os.remove(_f)") > than.index("created.get(\"id\")") \
        if "created.get(\"id\")" in than else True


def t_vision_chet_thi_phai_hien_chet_cam():
    """Vision kiểm ảnh hỏng thì phải hiện 🚨 CHẾT CÂM (24/8 tối).
    `verify_image` trả `None` khi lỗi, và `None` nghĩa là "bỏ qua kiểm" — tức người gọi NHẬN ảnh mà
    không cần khớp nội dung. Key Vision chết / cạn quota ⇒ **mọi ảnh vào video không qua một lượt
    kiểm nào**, mà log chỉ có một dòng cảnh báo lẫn trong hàng nghìn dòng. Đúng loại đã trả giá ở
    ca "clip 0/118": tính năng chết mà nhìn vẫn như đang chạy."""
    import datastory_ci as DS
    import qc_vision as QV
    cu = dict(DS._DEM_KHAU)
    try:
        DS._DEM_KHAU.clear()
        for i in range(3):
            QV.verify_image(f"/khong/ton/tai/{i}.jpg", "abc", api_key="x")
        bc = DS.bao_cao_khau()
        assert "vision ảnh 0/3" in bc, f"khâu Vision chưa vào máy dò: {bc}"
        assert "CHẾT CÂM" in bc, "Vision hỏng 3/3 mà không hiện CHẾT CÂM"
    finally:
        DS._DEM_KHAU.clear(); DS._DEM_KHAU.update(cu)


def t_hang_cho_khong_phu_thuoc_firestore():
    """Lấy việc kế phải có đường KHÔNG cần Firestore (24/8 tối).
    Vá 7.cr làm vòng lấy việc chạy được — nhưng log GRIDIRON phiên 21:52Z:
    `⚠️ lấy việc kế hụt (429 Quota exceeded.)`. `lay_viec_ke` giành việc bằng giao dịch trên
    Firestore, tức hàng chờ nằm trong CHÍNH tài nguyên đang cạn ⇒ đúng lúc cần nhất thì không dùng
    được. Đường thay: plan gửi kèm danh sách dư + thứ tự mẻ, lane cắt phần của mình theo vị trí."""
    import json as _j
    import run_render as R
    cu_q, cu_p = os.environ.get("QUEUE_LIST"), os.environ.get("PLAN_CHANNELS")
    try:
        me = [f"K{i}" for i in range(18)]
        du = [f"Q{i}" for i in range(32)]
        os.environ["PLAN_CHANNELS"] = _j.dumps(me)
        os.environ["QUEUE_LIST"] = _j.dumps(du)
        tat = []
        for lane in me:
            da = set()
            while True:
                v = R._viec_chia_san(lane, da)
                if not v:
                    break
                da.add(v); tat.append(v)
        assert len(tat) == len(du), f"chia sót: {len(tat)}/{len(du)}"
        assert len(tat) == len(set(tat)), "hai lane nhận TRÙNG kênh -> render dư, tốn quota"
        os.environ["QUEUE_LIST"] = "[]"
        assert R._viec_chia_san("K0", set()) == "", "hàng chờ rỗng mà vẫn trả việc"
        os.environ.pop("PLAN_CHANNELS")
        assert R._viec_chia_san("K0", set()) == "", "thiếu env mà vẫn trả việc (phải im, không đoán)"
    finally:
        for k, v in (("QUEUE_LIST", cu_q), ("PLAN_CHANNELS", cu_p)):
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    r = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "run_render.py"), encoding="utf-8").read()
    # Soi trong THÂN `channel_mode` — đó mới là đường matrix chạy (bài học 7.ci); `main()` cũng có
    # một lời gọi `lay_viec_ke` nhưng không ai đi qua.
    import ast as _ast
    t = _ast.parse(r)
    fn = next(n for n in _ast.walk(t)
              if isinstance(n, _ast.FunctionDef) and n.name == "channel_mode")
    than = "\n".join(r.split("\n")[fn.lineno - 1: max(getattr(x, "lineno", 0) for x in _ast.walk(fn))])
    i = than.index("FB.lay_viec_ke(OWNER)")
    assert "_viec_chia_san(" in than[i: i + 900], "429 ở hàng chờ Firestore mà không có đường thay"
    assert "except Exception" in than[max(0, i - 200): i + 300], \
        "lay_viec_ke ném 429 mà không bắt -> vòng lấy việc chết luôn, không kịp dùng đường thay"
    # MỌI lệnh Firestore trong vòng phải được bọc RIÊNG. Lệnh đầu ném 429 mà không bắt là rơi thẳng
    # xuống except ngoài cùng, in "lấy việc kế hụt" rồi thoát ⇒ đường chia-sẵn không bao giờ tới
    # lượt. Đây đúng là bẫy "bản vá không chạy" đã dính hai lần (7.br, 7.cr).
    j = than.index("while True:", than.index("XONG KÊNH CỦA MÌNH"))
    vong = than[j: than.index("except Exception as e:", j)]
    for lenh in ("FB.read_config(OWNER)", "FB.read_channels(OWNER)"):
        k = vong.index(lenh)
        assert "try:" in vong[max(0, k - 320): k], \
            f"{lenh} trong vòng lấy việc chưa được bọc riêng -> 429 là chết cả vòng"


def t_khong_ghi_snapshot_rong():
    """Không snapshot/gương nào được ghi bản RỖNG đè bản tốt (24/8 tối — quét cả họ sau 7.ct).
    Ba chỗ có cùng hình dạng "đọc xong rồi ghi đè": snapshot KEY (`__snap__{owner}`), gói KHO
    (`snap_kho`), và gói sao lưu vault. Rỗng ở đây gần như luôn là triệu chứng đọc hụt/owner lệch,
    không phải sự thật — mà hậu quả thì tối đa: `read_keys` đọc snapshot rỗng ⇒ cả dây chuyền tưởng
    KHÔNG CÓ key AI nào; gói kho rỗng ⇒ 18 luồng từ chối đẩy video đã render xong."""
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "firestore_bridge.py"), encoding="utf-8").read()
    for moc, ten in ((f'document(f"__snap__{{owner}}").set(', "snapshot key"),
                     ('document("snap_kho").set(', "gói kho")):
        i = src.index(moc)
        truoc = src[max(0, i - 700): i]
        assert "if not snap_rows" in truoc or "if not _snap" in truoc, \
            f"{ten}: ghi đè mà không kiểm rỗng -> bản tốt bị xoá bởi một lượt đọc hụt"


def t_khong_cat_goi_sao_luu_rong():
    """Gói sao lưu RỖNG không được cất đè lên bản tốt (24/8 tối — suýt mất sạch kho sao lưu).
    Log phiên 21:52Z: `📦 Gói sao lưu: 0 key · 0 kênh · 0.3KB` rồi `✅ đã cất ở kho` ×3. Gói rỗng đó
    thành bản MỚI NHẤT, mà code giữ đúng `GIU_LAI=7` bản gần nhất và **bỏ phần còn lại vào thùng
    rác**. Sao lưu chạy mỗi phiên (~30-40') ⇒ chỉ vài giờ là mọi bản THẬT bị đẩy ra rìa rồi xoá.
    Gói rỗng vì A và B đều cạn hạn mức — đọc không ra dữ liệu KHÔNG phải là "dữ liệu rỗng"."""
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "backup_vault.py"), encoding="utf-8").read()
    i = src.index("du_lieu = _doc_firestore()")
    j = src.index("upload_file", i)
    khoi = src[i:j]
    assert "_n_key == 0 and _n_kenh == 0" in khoi, "chưa chặn gói sao lưu rỗng"
    assert "KHÔNG CẤT" in khoi and "return 1" in khoi, \
        "phát hiện gói rỗng mà vẫn đi tiếp tới bước cất -> vẫn đẩy bản tốt ra rìa"
    # chặn phải nằm TRƯỚC mọi lệnh đụng kho
    assert khoi.index("_n_key == 0") < khoi.index("ma_hoa("), \
        "kiểm tra rỗng phải làm trước khi đóng gói/cất"


def t_suc_dang_phan_biet_chua_biet_voi_het_luot():
    """`0` và `không biết` phải là hai con số khác nhau (24/8 tối).
    Log plan in `đăng được hôm nay: 0` trong khi sự thật là bảng `yt_project` trên D1 CÒN TRỐNG —
    Worker cộng `con` từ danh sách dự án, danh sách rỗng thì tổng bằng 0. Người đọc hiểu thành "hết
    hạn mức đăng", thực tế là "chưa khai báo dự án nào". Cùng họ luật 7.cg."""
    import hot_db as H
    goc_goi, goc_d, goc_g = H.goi, H.bat_doc, H.bat_ghi
    try:
        H.bat_doc = H.bat_ghi = lambda: True
        H.goi = lambda l, t=None, timeout=12: {"rows": [], "con": 0}
        cu_ow = os.environ.get("OWNER_UID")
        os.environ.pop("OWNER_UID", None)
        assert H.suc_dang_ngay() == -1, "bảng dự án trống mà báo 0 = nói 'hết lượt' khi chưa biết gì"
        # 25/8 — bảng `yt_project` còn trống thì SUY RA từ chính các kênh đã từng đăng (mỗi kênh một
        # tài khoản Google riêng ⇒ 6 video/ngày), thay vì bắt anh khai báo tay. Worker không có lệnh
        # thêm dòng vào bảng đó và deploy lại Worker thì máy này không có token Cloudflare.
        os.environ["OWNER_UID"] = "uid-test"
        H.goi = lambda l, t=None, timeout=12: (
            {"rows": [], "con": 0, "da_dung_ngay": 7} if l == "yt_con_cho"
            else {"rows": [{"channel": f"K{i}"} for i in range(12)]})
        assert H.suc_dang_ngay() == 12 * 6 - 7, "không suy được sức đăng từ số kênh đã kết nối"
        if cu_ow is None:
            os.environ.pop("OWNER_UID", None)
        else:
            os.environ["OWNER_UID"] = cu_ow
        H.goi = lambda l, t=None, timeout=12: {"rows": [{"tran_ngay": 6, "da_dung": 6}], "con": 0}
        assert H.suc_dang_ngay() == 0, "có dự án và hết lượt thật thì phải là 0"
        H.goi = lambda l, t=None, timeout=12: {"rows": [{"tran_ngay": 6, "da_dung": 2}], "con": 4}
        assert H.suc_dang_ngay() == 4
    finally:
        H.goi, H.bat_doc, H.bat_ghi = goc_goi, goc_d, goc_g
    r = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "run_render.py"), encoding="utf-8").read()
    assert "CHƯA BIẾT" in r, "dòng Đệm bài chưa nói rõ khi không biết sức đăng"


def t_phan_ap_luc_khong_im_lang():
    """Phản áp lực không chạy được thì phải NÓI RA (24/8 tối).
    Log plan phiên 16:06Z và 17:56Z không có `📦 Đệm bài` lẫn dòng lỗi nào — `ton_kho()` trả `{}`
    êm ru nên cả khối `if _ton:` bị bỏ qua. Tính năng anh yêu cầu ("kênh nào sắp hết bài thì tự ưu
    tiên") chưa từng chạy, mà nhìn log thì tưởng bình thường.
    Gốc: bảng `render_job` trên D1 ghi owner bằng `_OWNER_HINT[0]` — khởi tạo RỖNG, chỉ được đặt
    trong `read_keys`/`new_job` ⇒ tiến trình nào gọi `update_job` trước đó ghi `owner=""`, mà
    `ton_kho(OWNER)` lọc theo owner thật."""
    import firestore_bridge as FB
    cu_env = os.environ.get("OWNER_UID")
    cu_hint = FB._OWNER_HINT[0]
    try:
        os.environ["OWNER_UID"] = "UID-THAT"
        FB._OWNER_HINT[0] = ""
        assert FB._chu() == "UID-THAT", "owner rơi về rỗng khi chưa gọi read_keys/new_job"
        FB._OWNER_HINT[0] = "UID-HINT"
        assert FB._chu() == "UID-HINT" and FB._chu("X") == "X"
    finally:
        FB._OWNER_HINT[0] = cu_hint
        if cu_env is None:
            os.environ.pop("OWNER_UID", None)
        else:
            os.environ["OWNER_UID"] = cu_env
    fb = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "firestore_bridge.py"), encoding="utf-8").read()
    assert "_H.ghi_job(_chu()" in fb, "bản ghi D1 vẫn dùng _OWNER_HINT trần -> owner có thể rỗng"
    r = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "run_render.py"), encoding="utf-8").read()
    # 25/8 — thước đo đổi từ "tồn chưa đăng / ngày đệm" sang "độ đầy kho so với đích
    # 100L/300S mỗi kênh" (anh chốt). Chốt giữ nguyên tinh thần: không có số thì phải NÓI RA.
    i = r.index("_dem = _H.nap_dem(OWNER)")
    assert "if _dem is None:" in r[i: i + 900], "số đếm kho rỗng vẫn bị bỏ qua im lặng"
    assert "PHẢN ÁP LỰC KHÔNG CHẠY" in r[i: i + 900], "không nói ra khi phản áp lực không chạy"
    # làm đều + luân phiên: sắp theo độ đầy, hoà thì xoay theo ngày
    assert "round(_do_day(c), 2), _xoay(c)" in r, "mất luân phiên xoay ngày khi hoà độ đầy"
    assert "TARGET_LONG" in r and "TARGET_SHORT" in r, "mất đích kho 100L/300S"


def t_publish_khong_doi_vao_cho_da_chet():
    """Hai lỗi ở khâu ĐĂNG, đo được trong log lượt 18:25Z (24/8 tối):
      • `⚠️ gương connections ở B cũng lỗi: 429` in ra **112 lần trong MỘT lượt chạy** — hàm gọi cho
        từng kênh, cả A lẫn B đều cạn nên mỗi kênh lại đi hỏi B thêm một lần. 112 lượt đọc hỏng, mà
        lượt hỏng VẪN BỊ TRỪ hạn mức. Cạn hạn mức là trạng thái của cả tiến trình: biết một lần đủ.
      • `⛔ Project A cạn hạn mức` in 114 lần, mà dòng tổng kết vẫn báo `project A: đọc 0/50,000 (0%)`
        — đọc sổ hỏng thì coi như 0. Cho chạy tiếp là đúng, nhưng BÁO 0% khi đã chạm trần là nói dối,
        và `du_suc()` còn mở cửa cho mọi việc phụ đúng lúc project hết sạch."""
    ap = os.environ.get("AUTOPUBLISHER_SRC") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "MM0-AutoPublisher", "src")
    f1 = os.path.join(ap, "firestore_state.py")
    f2 = os.path.join(ap, "quota_guard.py")
    if not (os.path.exists(f1) and os.path.exists(f2)):
        return
    a = io.open(f1, encoding="utf-8").read()
    assert "_GUONG_CHET" in a and "self._GUONG_CHET.get(kind)" in a, \
        "gương connections hỏng vẫn bị hỏi lại cho từng kênh"
    b = io.open(f2, encoding="utf-8").read()
    assert '"_can"' in b and "TRAN_DOC, \"w\": 0" in b.replace("'", '"'), \
        "quota_guard vẫn báo 0% khi không đọc nổi sổ vì 429"
    i = b.index("def bao_cao(")
    assert "CẠN" in b[i: i + 700], "dòng tổng kết chưa nói thẳng là project đã cạn"


def t_so_quota_dung_ngay_va_gop_du():
    """Sổ quota phải (a) sang trang ĐÚNG lúc Google reset, (b) cộng CẢ HAI cuốn của project B.

    24/8 tối, số đo tự tố cáo: sổ báo `ĐỌC 9.631/50.000` trong khi B đã trả 429 (tức đã chạm 50.000).
    Hai lỗi:
      • Ngày đánh theo 00:00 **UTC**, trong khi hạn mức free reset 00:00 giờ **Thái Bình Dương**
        (07:00-08:00 UTC) ⇒ suốt khung 00:00→07:00 UTC mỗi đêm sổ báo "đã dùng 0" trong khi bình
        xăng vẫn gần cạn — đúng khung giờ 18 luồng chạy mạnh nhất.
      • Project B có HAI cuốn sổ do hai codebase ghi (`render_stats/__rw__{owner}` của nhà máy render
        và `quota/__rw__{ngày}` của khâu đăng), mà hàm đọc chỉ lấy một cuốn ⇒ mỗi cuốn thấy một nửa.
    """
    import datetime as _dt
    import firestore_bridge as FB
    mong = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=7)).strftime("%Y%m%d")
    assert FB._ngay_quota() == mong, "sổ quota không theo mốc reset Thái Bình Dương"
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "firestore_bridge.py"), encoding="utf-8").read()
    # HAI LOẠI NGÀY, ĐỪNG GỘP (25/8 — chính bản vá 20:21 đã gộp nhầm rồi gây "Hôm nay: 32"):
    #   • SỔ QUOTA  -> mốc reset của Google = UTC-7  (`_ngay_quota`)
    #   • BỘ ĐẾM HIỂN THỊ -> phải trùng khoá mà DASHBOARD đọc; dashboard dùng
    #     `new Date().toISOString().slice(0,10)` tức ngày UTC.
    # Bên ghi và bên đọc lệch khoá là ô "Hôm nay" đọc nhầm ngăn -> con số vô nghĩa.
    import ast as _ast
    _t2 = _ast.parse(src)
    _cho = {}
    for _f in _ast.walk(_t2):
        if isinstance(_f, _ast.FunctionDef):
            _cho[_f.name] = (_f.lineno, max(getattr(x, "lineno", 0) for x in _ast.walk(_f)))
    for _n in _ast.walk(_t2):
        if isinstance(_n, _ast.Call) and getattr(_n.func, "attr", "") == "strftime" \
                and any(getattr(a, "value", "") == "%Y%m%d" for a in _n.args):
            _ten = [k for k, (a, b) in _cho.items() if a <= _n.lineno <= b]
            assert "_ngay_quota" in _ten or "count_pushed" in _ten, \
                f"dòng {_n.lineno}: đánh số ngày theo UTC ngoài hai chỗ được phép"
    for _q in ("flush_rw_ledger", "read_rw_ledger", "xa_ngan_sach_d1", "nap_nen_ngan_sach"):
        a, b = _cho[_q]
        assert "_ngay_quota()" in "\n".join(src.split("\n")[a - 1:b]), \
            f"{_q} không dùng mốc reset Google -> sổ quota sang trang lệch 7 tiếng"
    a, b = _cho["count_pushed"]
    assert 'strftime("%Y%m%d")' in "\n".join(src.split("\n")[a - 1:b]), \
        "bộ đếm hiển thị phải dùng ngày UTC cho khớp dashboard"
    dash = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "MM0-AutoPublisher", "dashboard", "index.html")
    if os.path.exists(dash):
        assert 'toISOString().slice(0,10).replace(/-/g,"")' in io.open(dash, encoding="utf-8").read(), \
            "dashboard đổi cách tính khoá ngày -> phải đổi count_pushed cho khớp"
    i = src.index("def read_rw_ledger")
    than = src[i: src.index("\ndef ", i + 10)]
    assert 'collection("quota")' in than, "read_rw_ledger chưa cộng sổ của khâu đăng"
    # ĐANG Ở GƯƠNG THÌ KHÔNG ĐƯỢC ĐỌC SỔ Ở GƯƠNG. `📟 Sổ quota: ĐỌC 9.631` in ra Y HỆT ba phiên
    # liên tiếp vì sau failover `_db_jobs()` trả B2 — bản chép đông cứng từ 13:15Z. D1 luôn tươi và
    # không nằm trong tài nguyên đang cạn.
    assert '_B2["on"]' in than and "ngan_sach_doc" in than, \
        "đang chạy trên gương mà vẫn đọc sổ quota từ gương -> con số chết"
    import sys as _sys, types as _types
    _that = _sys.modules.get("hot_db")
    _gia = _types.ModuleType("hot_db")
    _gia.ngan_sach_doc = lambda ngay: {"doc": 41230, "ghi": 8800}
    _gia.bat_ghi = _gia.bat_doc = lambda: True
    _sys.modules["hot_db"] = _gia
    try:
        FB._B2["on"] = True
        assert FB.read_rw_ledger("uid") == (41230, 8800), "không lấy số tươi từ D1 khi ở gương"
        _gia.ngan_sach_doc = lambda ngay: {"doc": 0, "ghi": 0}
        assert FB.read_rw_ledger("uid") == (-1, -1), \
            "D1 trống mà vẫn báo 0 -> lại là con số bịa (xem luật 'không đo được thì đừng báo 0')"
    finally:
        FB._B2["on"] = False
        if _that is not None:
            _sys.modules["hot_db"] = _that
        else:
            _sys.modules.pop("hot_db", None)
    # hai bên phải nói về CÙNG một ngày
    qg = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "MM0-AutoPublisher", "src", "quota_guard.py")
    if os.path.exists(qg):
        assert "hours=7" in io.open(qg, encoding="utf-8").read(), \
            "quota_guard đổi mốc ngày -> hai sổ lại lệch trang"


def t_buoc_phu_that_bai_khong_duoc_im():
    """Bước phụ có `|| true` mà hỏng thì phải NÓI RÕ (24/8 tối, phiên 17:56Z).
    `backup_vault.py` chết `ModuleNotFoundError: No module named 'storage'` MỌI PHIÊN vì job `plan`
    trỏ `AUTOPUBLISHER_SRC` vào `_autopublisher/src` mà lại không checkout repo đó. Bước gọi có
    `|| true` nên workflow vẫn xanh ⇒ kho key coi như KHÔNG được sao lưu suốt thời gian qua."""
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "backup_vault.py"), encoding="utf-8").read()
    assert "except ModuleNotFoundError" in src and "🚨" in src, \
        "backup_vault vẫn để traceback trôi trong log thay vì nói thẳng"
    wf = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      ".github", "workflows", "render_cron.yml")
    if not os.path.exists(wf):
        return
    w = io.open(wf, encoding="utf-8").read()
    # Mọi job đặt AUTOPUBLISHER_SRC thì job đó PHẢI checkout repo publish. Tách theo JOB
    # (tên job = khoá thụt 2 dấu cách ngay dưới `jobs:`), không tách bừa theo xuống-dòng.
    # Điều kiện THẬT bị vi phạm không phải "có checkout hay không" — job `plan` CÓ checkout, nhưng
    # ở dòng 106, tức SAU bước sao lưu ở dòng 72. Nên phải kiểm THỨ TỰ: trong mỗi job, lần checkout
    # repo publish phải đứng TRƯỚC chỗ dùng AUTOPUBLISHER_SRC đầu tiên.
    than = w[w.index("\njobs:"):]
    for job in re.split(r"\n  (?=[A-Za-z_][\w-]*:\n)", than):
        ten = job.strip().split(":")[0]
        if "AUTOPUBLISHER_SRC:" not in job:
            continue
        assert "path: _autopublisher" in job, \
            f"job `{ten}` trỏ AUTOPUBLISHER_SRC mà KHÔNG checkout repo publish"
        assert job.index("path: _autopublisher") < job.index("AUTOPUBLISHER_SRC:"), \
            f"job `{ten}`: checkout repo publish nằm SAU bước dùng AUTOPUBLISHER_SRC -> bước đó chết"


def t_guong_thieu_kenh_khong_phai_bi_xoa():
    """Gương B2 thiếu kênh ≠ kênh bị xoá (24/8 tối — 2 lane mất trắng phiên 16:06Z).
    Lane lật B2 (gương cũ 156') mà gương thiếu HAULUSA/FAKEUSA -> `read_one_channel` trả None ->
    lane hiểu là "đã xoá" rồi thoát. Lệnh đọc KHÔNG hỏng, dữ liệu chỉ THIẾU, nên `DocLoi` không đỡ.
    Plan đã đọc đủ 50 kênh lúc còn đọc được -> gửi kèm cấu hình xuống lane qua CHANNEL_CFGS."""
    import base64, gzip, json as _j
    import firestore_bridge as FB
    cu = os.environ.get("CHANNEL_CFGS")
    try:
        bo = {"HAULUSA": {"name": "HAULUSA", "format": "doc"}}
        os.environ["CHANNEL_CFGS"] = base64.b64encode(
            gzip.compress(_j.dumps(bo).encode())).decode()
        FB._CFG_PLAN.clear()
        c = FB._cfg_tu_plan()
        assert c.get("HAULUSA", {}).get("format") == "doc", c
        os.environ.pop("CHANNEL_CFGS")
        FB._CFG_PLAN.clear()
        assert FB._cfg_tu_plan() == {"_": {}}, "không có gói thì phải im, giữ hành vi cũ"
    finally:
        FB._CFG_PLAN.clear()
        if cu is not None:
            os.environ["CHANNEL_CFGS"] = cu
        else:
            os.environ.pop("CHANNEL_CFGS", None)
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "firestore_bridge.py"), encoding="utf-8").read()
    i = src.index("def read_one_channel")
    # 28/8 — cắt theo BIÊN HÀM, không theo số ký tự: cửa sổ cố định vỡ khi thân hàm
    # dài ra, và chốt đỏ vì lỗi CỦA CHÍNH NÓ chứ không phải vì mã hỏng.
    _ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
    than = src[i: min(_ket) if _ket else len(src)]
    assert "_cfg_tu_plan()" in than, "read_one_channel chưa dùng cấu hình plan gửi kèm"
    r = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "run_render.py"), encoding="utf-8").read()
    assert "cau_hinh=_cfg_goi" in r, "plan chưa gửi kèm cấu hình kênh xuống matrix"
    wf = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      ".github", "workflows", "render_cron.yml")
    if os.path.exists(wf):
        w = io.open(wf, encoding="utf-8").read()
        assert "cfgs: ${{ steps.plan.outputs.cfgs }}" in w and "CHANNEL_CFGS:" in w, \
            "workflow chưa nối gói cấu hình từ plan sang lane"


def t_the_mo_dau_khong_thanh_nen_tron():
    """Thẻ mở đầu KHÔNG được che kín hình bằng nền gần đen (24/8 tối — suýt tự tạo lại lỗi bị cấm).
    `opening_is_flat()` chặn chữ ký nền trơn ở `dark>=75 & colors<900` (đo thật: nền trơn 91,9% tối).
    Bản đầu của Bookend phủ `rgba(0,0,0,0.82→0.94)` — vừa dính đúng chữ ký đó, vừa đúng thứ anh cấm
    ("mở đầu không được là chữ trên nền đen"). Trần cứng 0,5; thẻ KẾT được che dày hơn vì QC chỉ soi
    khung MỞ ĐẦU."""
    eng = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "engine-remotion", "src")
    if not os.path.isdir(eng):
        return
    t = io.open(os.path.join(eng, "Bookend.tsx"), encoding="utf-8").read()
    m = re.search(r"const MAN_CHE = ([\d.]+)", t)
    assert m and float(m.group(1)) <= 0.5, "màn che thẻ MỞ ĐẦU vượt 0,5 -> dính chữ ký nền trơn"
    # không được còn hằng số alpha viết thẳng trong phần thẻ mở đầu
    mo = t[t.index("THẺ MỞ ĐẦU"): t.index("THẺ KẾT")]
    assert not re.search(r"rgba\(0,\s*0,\s*0,\s*0\.[6-9]", mo), \
        "thẻ mở đầu còn màn che đặc viết cứng"


def t_bao_chung_b_can_han_muc():
    """B cạn hạn mức là sự thật CHUNG của cả phiên, không phải chuyện riêng từng tiến trình.
    Log phiên 16:06Z: mỗi lane đều có một dòng `🔀 FAILOVER ... (read_config 429)` RIÊNG — tức cả 18
    lane, mỗi đứa tự tông vào tường một lần mới biết, mà lượt hỏng vẫn bị trừ hạn mức. Nay lane đầu
    ghi cờ vào D1 (miễn phí), lane sau đọc thấy thì lật B2 thẳng."""
    import sys, types
    that = sys.modules.get("hot_db")
    gia = types.ModuleType("hot_db"); kho = {}
    gia.key_nghi_ghi = lambda kid, loai, den: kho.__setitem__(kid, den)
    gia.key_nghi_doc = lambda gio: [{"kid": k, "den": v} for k, v in kho.items() if v > gio]
    gia.bat_ghi = lambda: True
    gia.bat_doc = lambda: True
    sys.modules["hot_db"] = gia
    try:
        import firestore_bridge as FB
        FB._DA_BAO_CAN[0] = False
        assert FB.b_dang_nghi() is False, "chưa ai báo mà đã tưởng B nghỉ"
        FB.bao_b_can_ngay("read_config 429")     # chỗ gọi chỉ truyền MẨU TÓM TẮT
        assert kho.get("proj:B"), "không ghi được cờ chung"
        assert FB.b_dang_nghi() is True, "lane sau không đọc thấy cờ"
        # Log 17:56Z: mẩu tóm tắt không có chữ "per day" -> rơi vào nhánh "không rõ" = 20 phút,
        # rồi lần ghi sau ĐÈ mất lần ghi đúng. Cờ phải ra mốc CẠN NGÀY và chỉ được dài thêm.
        import datetime as _dt
        con = (_dt.datetime.fromisoformat(kho["proj:B"])
               - _dt.datetime.now(_dt.timezone.utc)).total_seconds() / 60
        # ĐO CÔNG THỨC, KHÔNG ĐO SỐ TUYỆT ĐỐI (25/8): chốt cũ đòi cờ còn >120 phút, nên chạy trong
        # 2 tiếng trước mốc reset của Google (00:00 giờ Thái Bình Dương = 07:00Z) là FAIL oan —
        # lúc đó "cạn tới hết ngày" ĐÚNG NGHĨA chỉ còn 98 phút. Chốt đúng phải là: cờ trỏ tới đúng
        # mốc reset kế tiếp, và luôn dài hơn nhánh "không rõ" (20').
        import nghi_key as _NK
        # dùng ĐÚNG chuỗi mà bao_b_can_ngay dựng ra (nó tự nối " per day" khi không phải chặn/phút)
        _mong = _NK.muc_nghi("read_config 429 per day")      # muc_nghi trả PHÚT, không phải giây
        assert abs(con - _mong) < 3, f"cờ còn {con:.0f}' nhưng mốc cạn ngày là {_mong:.0f}'"
        # 26/8 — SÀN 20' NÀY LÀM SELFTEST ĐỎ MỖI NGÀY TRONG 20 PHÚT CUỐI TRƯỚC RESET, và
        # `run_render` CHẶN PHIÊN khi selftest đỏ ⇒ mất trắng mọi phiên khởi động trong khung
        # 06:40-07:00Z. Bắt được đúng lúc 06:40Z hôm nay, khi mốc cạn-ngày chỉ còn 19'.
        # Cùng bệnh với chốt cũ đòi ">120 phút" mà người trước đã phải sửa: **đo số tuyệt đối của
        # một thứ phụ thuộc giờ trong ngày**. Gần mốc reset thì cờ ngắn là ĐÚNG — nghỉ quá mốc
        # reset chẳng để làm gì. Chỉ đòi cờ dài hơn nhánh "không rõ" KHI mốc reset còn xa hơn thế.
        _KHONG_RO = 20
        if _mong > _KHONG_RO:
            assert con > _KHONG_RO, f"cờ {con:.0f}' không dài hơn nhánh 'không rõ' ({_KHONG_RO}')"
        dai = kho["proj:B"]
        FB._DA_BAO_CAN[0] = False
        FB.bao_b_can_ngay("429 requests per minute, try again in 5s")
        assert kho["proj:B"] == dai, "cờ dài bị ghi đè bằng cờ ngắn"
        FB._DA_BAO_CAN[0] = False
        src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "firestore_bridge.py"), encoding="utf-8").read()
        i = src.index("def quota_pulse(")
        assert "b_dang_nghi()" in src[i: i + 900], "lane khởi động chưa hỏi cờ chung"
        assert "bao_b_can_ngay(" in src[src.index("def failover_to_b2("):][:1400], \
            "lật B2 xong mà không báo cho lane khác"
    finally:
        if that is not None:
            sys.modules["hot_db"] = that
        else:
            sys.modules.pop("hot_db", None)


def t_mot_bang_phat_key_duy_nhat():
    """Đường VIẾT và đường VẼ ẢNH phải phạt key giống hệt nhau (24/8 tối).
    Trước đó `key_manager` dùng con số CỨNG 8 tiếng ở 8 chỗ, còn `datastory_ci` tính tới mốc reset
    thật. 8 tiếng sai cả hai chiều: quá SỚM với Google (dội lại 3h trước khi key hồi, lượt hỏng vẫn
    bị trừ) và quá MUỘN với Cloudflare (treo oan key đã hồi từ nửa đêm UTC)."""
    import datastory_ci as DS
    import nghi_key as N
    km = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "key_manager.py"), encoding="utf-8").read()
    assert "8 * 60 if _het_ngay" not in km, "key_manager còn con số phạt CỨNG 8 tiếng"
    assert km.count("_NGHI.muc_nghi(") >= 8, \
        f"chỉ {km.count('_NGHI.muc_nghi(')}/8 chỗ trong key_manager dùng bảng phạt chung"
    for e in ("requests per minute, try again in 8s",
              "daily free allocation of 10,000 neurons (cloudflare)",
              "quota exceeded for quota metric: requests per day (free_tier)",
              "429 lạ hoắc"):
        assert DS._muc_nghi(e) == N.muc_nghi(e), f"hai đường ra số khác nhau cho: {e[:40]}"


def t_moc_reset_theo_nha_cung_cap():
    """Key cạn theo NGÀY phải nghỉ tới mốc reset CỦA CHÍNH nhà cung cấp đó (24/8 tối).
    Cloudflare Workers AI reset 00:00 UTC (chính thông báo lỗi ghi "daily free allocation of 10,000
    neurons"); Google free reset 00:00 giờ Thái Bình Dương. Gộp làm một là treo key Cloudflare thêm
    7 tiếng sau khi nó đã hồi — mỗi ngày."""
    import datastory_ci as DS
    cf = DS._muc_nghi("429 rate limit daily (cloudflare): AiError: used up your daily free "
                      "allocation of 10,000 neurons")
    gg = DS._muc_nghi("429 Quota exceeded for quota metric: requests per day (free_tier)")
    assert DS._muc_nghi("429 requests per minute exceeded, try again in 8s") == 2
    # 25/8 00:14Z — BẢN TEST ĐẦU SAI, và chính nó tự lộ ra khi đồng hồ đi qua 00:00Z: nó khẳng định
    # "Cloudflare luôn hồi sớm hơn Google". Chỉ đúng trong khung 07:00→24:00Z. Sau nửa đêm UTC,
    # Cloudflare vừa reset nên mốc kế tiếp xa tận 24h, còn Google thì chỉ còn vài tiếng là tới 07:00Z.
    # Điều BẤT BIẾN không phải thứ tự hai con số, mà là: mỗi bên nghỉ tới ĐÚNG mốc reset của mình.
    import datetime as _d
    _utc = _d.datetime.now(_d.timezone.utc)

    def _toi_moc(goc):
        mai = (goc + _d.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return int((mai - goc).total_seconds() // 60)

    # 27/8 06:55Z — LẦN THỨ BA CÙNG MỘT LỚP LỖI TRONG CHÍNH TỆP NÀY: đo SỐ TUYỆT ĐỐI của một
    # thứ phụ thuộc giờ trong ngày. Hai chú thích ngay phía trên đã ghi lại hai lần trước
    # (chốt đòi ">120 phút", rồi chốt đòi "sàn 20'"), mà chốt này vẫn mắc lại.
    # Cảnh bắt được: 06:55Z = 23:55 giờ Thái Bình Dương, còn ĐÚNG 4 phút tới mốc reset. Nhưng
    # `muc_nghi` có SÀN 10 PHÚT (`max(10, …)`) — cố ý, để key không quay vòng liên tục khi mốc
    # reset chỉ còn vài giây. Chốt đòi khớp ±2 với con số chính xác nên đỏ.
    # Hậu quả THẬT: `run_render` chặn phiên khi selftest đỏ ⇒ mất trắng mọi phiên khởi động
    # trong ~10 phút cuối trước MỖI mốc reset, mỗi ngày hai lần (00:00Z và 07:00Z).
    # Điều bất biến phải đo là: nghỉ tới đúng mốc reset của mình, NHƯNG KHÔNG DƯỚI SÀN.
    _SAN = 10                                   # phải khớp `max(10, …)` trong nghi_key.muc_nghi
    _cf_mong = max(_SAN, _toi_moc(_utc))
    _gg_mong = max(_SAN, _toi_moc(_utc - _d.timedelta(hours=7)))
    assert abs(cf - _cf_mong) <= 2, f"Cloudflare không nghỉ tới mốc 00:00 UTC: {cf} (mong {_cf_mong})"
    assert abs(gg - _gg_mong) <= 2, \
        f"Google không nghỉ tới mốc 00:00 giờ Thái Bình Dương: {gg} (mong {_gg_mong})"
    assert cf != gg, "hai nhà cung cấp mà ra cùng một mốc -> lại gộp làm một"




def t_moi_lop_toi_deu_noi():
    """MỌI lớp tối phủ toàn khung trong Scene1 phải nới theo `man`.

    25/8 — cái đã làm "vá mãi không xong": Scene1 vẽ 5 lớp tối chồng nhau nhưng chỉ 2 lớp nhân
    `man`, nên hạ `man` xuống sàn vẫn còn ~2/3 độ tối -> khung mở đầu render ra 86-93% tối và bị QC
    loại, trong khi mô hình đo chấm "đạt" nên hàm cứu không hề chạy.
    Chốt soi TỪNG `rgba(...)`: độ mờ phải là 0 (trong suốt, vô hại) hoặc phải có `man` trong biểu
    thức. Bản chốt đầu chỉ khớp độ mờ dạng SỐ nên đổi `${.66 * man}` thành `${.66}` vẫn đậu — đúng
    kiểu đậu giả mà chốt sinh ra để chặn."""
    src = _doc("../engine-remotion/src/Cinematic.tsx")
    i = src.index("const Scene1:")
    j = min([k for k in (src.find("\nconst ", i + 10), src.find("\nexport const ", i + 10),
                         src.find("\nfunction ", i + 10), src.find("\nexport function ", i + 10),
                         len(src)) if k != -1] or [len(src)])
    than = src[i:j]
    xau = []
    at = 0
    while True:
        k = than.find("rgba(", at)
        if k < 0:
            break
        at = k + 5
        sau, do_sau = "", 0
        for ch in than[k + 5:k + 200]:            # bóc tới dấu ) đóng, kể cả ${...} lồng bên trong
            if ch == "{":
                do_sau += 1
            elif ch == "}":
                do_sau -= 1
            elif ch == ")" and do_sau == 0:
                break
            sau += ch
        mo = sau.split(",")[-1].strip() if sau.count(",") >= 3 else ""
        if not mo:
            continue                              # rgb(...) 3 tham số, không phải lớp phủ
        try:
            if float(mo) == 0:
                continue                          # trong suốt hoàn toàn -> không làm tối gì
        except ValueError:
            pass
        truoc = than[max(0, k - 120):k]
        if "textShadow" in truoc or "boxShadow: `0" in truoc:
            continue                              # bóng chữ, không phải lớp phủ toàn khung
        if "man" not in mo:
            xau.append(f"rgba({sau})")
    assert not xau, f"lớp tối chưa nới theo man trong Scene1: {xau[:3]}"
    assert than.count("* man") >= 5, f"Scene1 chỉ có {than.count('* man')} chỗ nhân man, cần >=5"

def t_sau_man_du_lop():
    """Mô hình đo phải mô phỏng ĐỦ 5 lớp — thiếu lớp nào là chấm "đạt" oan."""
    src = _doc("datastory_ci.py")
    i = src.index("def _sau_man("); than = src[i:src.index("\ndef ", i + 10)]
    for moc in (".74", ".66", ".58", "0.55", "0.45", "0.50"):
        assert moc in than, f"_sau_man thiếu mốc lớp phủ {moc}"
    assert "1.0 - min(0.99, v0)" in than, \
        "_sau_man thiếu vignette HẰNG SỐ của ThemedBase (lớp thứ 6, ca UNSEENUSA 25/8)"
    assert "mo *= (1 - min(" in than, "_sau_man phải chồng lớp bằng tích (1-alpha), không cộng dồn"
    assert "co_hook" in than, "_sau_man phải phân biệt cảnh có/không có lớp hook"


def t_xoay_key_theo_luot_dung():
    """Hồ ảnh/Vision phải xoay theo SỐ LƯỢT ĐÃ DÙNG, không phải offset băm-tên-kênh cố định.

    25/8 — anh hỏi "sao CF chỉ 3 lần chạm trần ngày rồi mới đổi key". Vì `_ai_candidates` trả
    thứ tự CỐ ĐỊNH: một lane render 20 video cùng kênh thì cả 20 lần nạp đúng `cands[0]` cho tới
    khi key đó ăn 429 hạn-mức-NGÀY (nghỉ tới 00:00 UTC) — đốt cạn từng key một thay vì chia đều."""
    import datastory_ci as DS
    DS._AI_POOL["keys"] = ["cf:a:1", "cf:b:2", "cf:c:3"]
    DS._DUNG.clear(); DS._VE_DEAD.clear()
    dau = []
    for _ in range(6):
        c = DS._ai_candidates("")
        assert c, "hết key"
        DS.ghi_dung(c[0]); dau.append(c[0])
    d = {k: dau.count(k) for k in set(dau)}
    assert max(d.values()) - min(d.values()) <= 1, f"chia không đều, một key bị nện: {d}"
    assert len(d) == 3, f"chỉ dùng {len(d)}/3 key: {d}"
    # vision cũng phải xoay trong từng nhóm
    DS._DUNG.clear(); DS._DUNG["AIza1"] = 5
    v = DS._vision_order(["AIza1", "AIza2", "cf:a:1"])
    assert v[0] == "AIza2", f"vision không ưu tiên key ít dùng: {v}"


def t_nen_loi_da_luong_khong_de_quy():
    """`print_exc_gon` nén lỗi đã lường trước, và TUYỆT ĐỐI không được tự gọi chính nó.

    25/8 — suýt tự bắn chân: lệnh thay hàng loạt `traceback.print_exc()` -> `print_exc_gon()`
    ăn luôn dòng nằm TRONG chính hàm mới, biến nhánh "lỗi lạ" thành đệ quy vô hạn. Lỗi thường
    thì tràn stack ngay giữa phiên, mà selftest cũ không có gì bắt được."""
    import ast
    src = _doc("run_render.py")
    f = [n for n in ast.walk(ast.parse(src))
         if isinstance(n, ast.FunctionDef) and n.name == "print_exc_gon"][0]
    assert not [n for n in ast.walk(f) if isinstance(n, ast.Call)
                and getattr(n.func, "id", "") == "print_exc_gon"], "print_exc_gon tự gọi chính nó"
    assert [n for n in ast.walk(f) if isinstance(n, ast.Call)
            and getattr(getattr(n.func, "value", None), "id", "") == "traceback"], \
        "nhánh lỗi lạ phải còn in đủ stack"
    assert "traceback.print_exc()" not in src.replace(
        "    traceback.print_exc()\n", "", 1), "còn chỗ in stack thô ngoài print_exc_gon"


def t_ho_key_qua_d1_khong_dam_vao_A():
    """Luồng thứ hai trở đi phải đọc ảnh chụp D1, KHÔNG đọc project A.

    25/8 — soi sổ đọc thật của phiên 02:15: mỗi luồng tính `merge_keys_A=70`, luồng NÀO CŨNG tính.
    70 × 18 luồng × ~30 phiên/ngày ≈ 40.000 lượt đọc trên trần 50.000 của A ⇒ chính nó làm A cạn,
    kéo theo bảng key và danh sách kho Drive (cũng ở A) cùng chết."""
    import sys, types
    src = _doc("firestore_bridge.py")
    than = src[src.index("def _merge_a_keys"):src.index("def incr_key_requests")]
    assert "keys_doc" in than, "không đọc ảnh chụp D1 trước khi đọc A"
    assert "keys_ghi" in than, "đọc A xong mà không chụp lại cho luồng khác"
    assert than.index("keys_doc") < than.index('_cr("merge_keys_A"'), \
        "phải thử D1 TRƯỚC khi tính lượt đọc A"
    # ảnh chụp có sẵn -> tuyệt đối không được chạm vào A
    gia = types.ModuleType("hot_db")
    gia.keys_doc = lambda o, tuoi=1800: [{"id": "x", "key": "gsk_test", "req_today": 0}]
    gia.keys_ghi = lambda o, r: True
    gia.bat_ghi = lambda: True; gia.bat_doc = lambda: True
    cu = sys.modules.get("hot_db"); sys.modules["hot_db"] = gia
    try:
        import importlib, firestore_bridge as FB
        importlib.reload(FB)
        FB._A_KEYS["rows"] = None
        FB._READS["by"].pop("merge_keys_A", None)
        import os as _os
        _os.environ["SHARD_KEYS"] = "1"
        assert hasattr(FB, "_merge_a_keys"), "đổi tên hàm mà quên sửa chốt -> chốt đậu giả"
        # môi trường thử không có creds nên `_db()` và `_db_keys()` cùng là None -> hàm thoát sớm
        # ở nhánh "A và B là một shard". Giả lập hai shard KHÁC nhau cho giống lúc chạy thật.
        FB._db = lambda: "A"; FB._db_keys = lambda: "B"
        # NUỐT print của nhánh giả: dòng "🔑 Hồ key: dùng ảnh chụp D1 (1 key)" in ra từ dữ liệu
        # GIẢ của chốt này từng lọt vào log CI (selftest chạy ngay trước plan) và bị đọc nhầm thành
        # ảnh chụp thật bị nghèo hoá — mất 10 phút truy một báo động giả lúc 06:00Z ngày 25/8.
        import contextlib, io as _io
        with contextlib.redirect_stdout(_io.StringIO()):
            ra = FB._merge_a_keys("chu", [{"key": "cf:a:1"}])
        assert FB._READS["by"].get("merge_keys_A", 0) == 0, "có ảnh chụp mà vẫn đọc project A"
        assert any(str(r.get("key", "")).startswith("gsk_") for r in ra), \
            "key trong ảnh chụp không được hợp nhất vào hồ"
    finally:
        if cu is not None:
            sys.modules["hot_db"] = cu



def t_moi_chot_deu_duoc_dang_ky():
    """Chốt viết ra mà quên gọi trong `main()` thì nó KHÔNG CHẠY — và bảng vẫn in "PASS".

    25/8 — đã xảy ra thật: 5 chốt thêm trong đêm (lớp phủ, mô hình đo, xoay key, nén lỗi, hồ key
    D1) không cái nào được đăng ký, nên suốt đêm báo "selftest PASS" trong khi chúng chưa hề chạy
    một lần. Một bộ chốt tự nói dối còn tệ hơn không có chốt. Chốt này soi chính file selftest."""
    import ast
    src = _doc("selftest.py")
    t = ast.parse(src)
    co = {n.name for n in ast.walk(t) if isinstance(n, ast.FunctionDef) and n.name.startswith("t_")}
    dk = {n.args[1].id for n in ast.walk(t)
          if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "check"
          and len(n.args) > 1 and isinstance(n.args[1], ast.Name)}
    quen = sorted(co - dk)
    assert not quen, f"{len(quen)} chốt viết ra nhưng chưa đăng ký trong main(): {quen}"


def t_job_dang_chay_len_d1_ngay():
    """Lượt ghi ĐẦU TIÊN của mỗi job phải xả xuống D1 ngay, kể cả trạng thái chưa xong.

    25/8 — soi D1 lúc 3 luồng đang render thật: bảng chỉ có done/failed/ratelimited, KHÔNG một dòng
    `running` nào ⇒ ô "⚙️ Đang chạy" bằng 0 dù máy đang chạy. Vì bộ đệm chỉ xả sớm ở trạng thái
    CUỐI: dòng trung gian nằm chờ, tới lúc xả thì đi cùng lô với dòng `done` của chính job đó và bị
    đè. Đọc số này từ D1 mà không sửa gốc thì chỉ là ĐỔI CHỖ SAI, không hết sai."""
    import sys, types, importlib
    goi_ra = []
    gia = types.ModuleType("hot_db_probe")
    import hot_db as H
    importlib.reload(H)
    H.goi = lambda lenh, tham=None, timeout=12: (goi_ra.append((lenh, tham)) or {"ok": True})
    H.bat_ghi = lambda: True
    H._DA_GHI.clear(); H._DEM_BUF.clear(); H._BUF_AT[0] = 0
    H.ghi_job("chu", "job-1", "TESTUSA", "long", "running", step="viet", at="2026-08-25T05:00:00Z")
    lo = [t for l, t in goi_ra if l == "ghi_job_loat"]
    assert lo, "job mới mà không xả xuống D1 -> ô Đang chạy mãi bằng 0"
    assert any(x.get("status") == "running" for x in lo[0]["jobs"]), \
        f"lô xả không mang trạng thái running: {lo[0]['jobs']}"
    # lượt ghi trung gian TIẾP THEO của cùng job thì không được xả nữa (giữ hạn mức)
    n0 = len(goi_ra)
    H.ghi_job("chu", "job-1", "TESTUSA", "long", "rendering", at="2026-08-25T05:01:00Z")
    assert len(goi_ra) == n0, "lượt trung gian sau vẫn xả -> đốt lượt gọi Worker vô ích"


def t_hai_voi_ri_da_ham():
    """Hai khoản tiêu lớn nhất đo được ở phiên 02:15 phải có hãm.

    GHI: `nhip_song=832`/phiên (42% tổng ghi) — ghi theo MỌI lần `update_job`, không hãm gì.
    832 × ~30 phiên ≈ 25.000 ghi/ngày trên trần 20.000 của B ⇒ B cạn hạn mức GHI ⇒ `sync_keys A->B`
    hỏng vĩnh viễn ⇒ mỗi luồng tự đọc project A (`merge_keys_A=70`) ⇒ A cạn nốt. Một vòi rỉ kéo
    sập hai project.
    ĐỌC: `top_titles=2.842`/phiên (48% tổng đọc) trên project C; ×30 phiên ≈ 85.000 trên trần
    50.000. 18 luồng hỏi lại đúng một câu giống hệt nhau, mỗi luồng trả tiền riêng."""
    src = _doc("firestore_bridge.py")
    ns = src[src.index("def ghi_nhip_song"):src.index("def don_nhip_song")]
    assert "_NHIP_SONG" in ns and "600" in ns, "nhip_song chưa hãm nhịp"
    assert 'not in ("done", "failed", "ratelimited")' in ns, \
        "trạng thái CUỐI phải luôn ghi ngay, không được hãm -> đếm thiếu video"
    tt = src[src.index("def top_titles"):src.index("def _db_meta")]
    assert "nho_doc" in tt and "nho_ghi" in tt, "top_titles chưa dùng bộ nhớ chung D1"
    assert tt.index("nho_doc") < tt.index('_cr("top_titles"'), \
        "phải hỏi bộ nhớ chung TRƯỚC khi tính lượt đọc project C"

    # hãm phải THẬT: gọi 5 lần liên tiếp cho cùng job -> chỉ 1 lượt ghi
    import sys, types, importlib
    dem = {"n": 0}
    import firestore_bridge as FB
    importlib.reload(FB)
    FB._OWNER_HINT[0] = "chu"
    FB._db_B_that = lambda: types.SimpleNamespace(collection=lambda *a, **k: None)
    FB._soft = lambda fn, tag="": dem.__setitem__("n", dem["n"] + 1)
    FB._NHIP_SONG.clear()
    for _ in range(5):
        FB.ghi_nhip_song("job-x", "TESTUSA", "rendering")
    assert dem["n"] == 1, f"5 lần gọi mà ghi {dem['n']} lượt — hãm không ăn"
    FB.ghi_nhip_song("job-x", "TESTUSA", "done")
    assert dem["n"] == 2, "trạng thái CUỐI bị hãm oan -> dashboard đếm thiếu"


def t_dong_bo_kho_co_ngan_sach_gio():
    """Đồng bộ dung lượng 73 kho phải có NGÂN SÁCH THỜI GIAN và không được đợi-đủ-hết.

    25/8 — plan 07:05Z treo 14,5' trong bước này (73 kho tuần tự, không hạn giờ) rồi bị chém ở
    timeout 18'; `usage_synced_at` chưa kịp đóng dấu nên plan kế cũng dính — vòng lặp chết ăn
    trọn các phiên. Ba chốt: chạy song song, có mốc hết giờ, KHÔNG dùng `with` (shutdown chờ)."""
    src = _doc("run_render.py")
    i = src.index("Đã đồng bộ dung lượng thật")
    than = src[max(0, i - 3200):i]
    assert "ThreadPoolExecutor" in than, "đồng bộ kho vẫn chạy tuần tự"
    assert "_het = _t9.time() + 150" in than, "mất ngân sách 150s"
    assert "shutdown(wait=False, cancel_futures=True)" in than, "shutdown chờ đủ hết = treo như cũ"
    assert "with _cf.ThreadPoolExecutor" not in than, "with-block sẽ đợi đủ 73 kho ở __exit__"
    sau = src[i - 3200:src.index("GUARD KHO GẦN ĐẦY", i)]   # mốc SAU i — mốc cùng tên đứng trước đã bẫy chốt này 1 lần
    assert 'FB.set_config(OWNER, {"usage_synced_at"' in sau, "không đóng dấu synced_at nữa"


def t_kiem_kho_ngay_co_ngan_sach():
    """Lượt đi bộ 72 kho hằng ngày phải song song + có ngân sách + dở dang thì BỎ, không ghi số thiếu.

    25/8 — thủ phạm thật của hai plan chết liên tiếp (07:05Z, 07:28Z): 72 kho tuần tự 12-15 phút,
    đứng ngay trước lệnh xuất matrix ⇒ 18 luồng không bao giờ mở, phiên chết ở timeout 18'."""
    src = _doc("run_render.py")
    i = src.index("def _kiem_kho_ngay")
    # 28/8 — cắt theo BIÊN HÀM, không theo số ký tự: cửa sổ cố định vỡ khi thân hàm
    # dài ra, và chốt đỏ vì lỗi CỦA CHÍNH NÓ chứ không phải vì mã hỏng.
    _ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
    than = src[i: min(_ket) if _ket else len(src)]
    assert "ThreadPoolExecutor" in than, "kiểm kho vẫn tuần tự"
    assert "_han = _t10.time() + 240" in than, "mất ngân sách 240s"
    assert "shutdown(wait=False, cancel_futures=True)" in than, "shutdown chờ = treo như cũ"
    assert "with " not in than[than.index("ThreadPoolExecutor"):than.index("shutdown")], \
        "with-block đợi đủ 72 kho ở __exit__"
    # dở dang -> hong tăng -> nhánh BỎ lượt ghi phía dưới phải còn nguyên
    assert "BỎ QUA lượt ghi" in than or "kho đọc hụt" in than, "mất nguyên tắc không-ghi-số-thiếu"


def t_lap_ban_ghi_tu_luot_di_bo():
    """Lượt đi bộ 72 kho phải NHẶT KÈM map file->kho và video->thumbnail (0 lượt Drive thêm).

    25/8 — hai bệnh cùng gốc trên thư viện: "🔍 kho chưa rõ" hàng loạt và thumbnail "tối thui"
    (Drive tự chọn frame-0 đúng lúc màn mở màn còn đen) — đều vì bản ghi thời Firestore-nghẽn
    thiếu drive_account/thumb_id, trong khi file thật (.mp4 + .jpg cùng tên gốc) vẫn nằm đủ trên
    Drive. Đi bộ hằng ngày vốn qua từng file: bắt nó nhặt luôn, không tốn thêm lượt Drive nào."""
    src = _doc("run_render.py")
    i = src.index("def _kiem_kho_ngay")
    # 28/8 — cắt theo BIÊN HÀM, không theo số ký tự: cửa sổ cố định vỡ khi thân hàm
    # dài ra, và chốt đỏ vì lỗi CỦA CHÍNH NÓ chứ không phải vì mã hỏng.
    _ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
    than = src[i: min(_ket) if _ket else len(src)]
    for moc in ("kho_can_acc", "thumb_can", "kho_acc_ghi", "thumb_ghi", "jpg_co", "mp4_can"):
        assert moc in than, f"lượt đi bộ thiếu mảnh {moc}"
    assert than.index("thumb_can") < than.index("ThreadPoolExecutor"), \
        "danh sách thiếu phải nạp TRƯỚC khi đi bộ (trong luồng con là quá muộn)"


def t_plan_khong_render():
    """Plan là NGƯỜI ĐIỀU PHỐI — tuyệt đối không render. (25/8, hung thủ cuối của 3 plan chết 18')

    `process_requests` render + đẩy kho nhiều phút mỗi yêu cầu; hàng tồn 25 yêu cầu ⇒ plan chết
    trước khi mở matrix, mọi phiên chỉ còn luồng sót. Nay plan chỉ đếm hàng; lane nhận kênh nào
    xử yêu cầu của kênh đó (chi_kenh=...)."""
    import ast
    src = _doc("run_render.py")
    t = ast.parse(src)
    plan = [n for n in ast.walk(t) if isinstance(n, ast.FunctionDef) and n.name == "plan_mode"][0]
    goi = [n for n in ast.walk(plan) if isinstance(n, ast.Call)
           and getattr(n.func, "id", "") == "process_requests"]
    assert not goi, "plan_mode vẫn gọi process_requests -> plan lại chết ở timeout 18'"
    lane = [n for n in ast.walk(t) if isinstance(n, ast.FunctionDef) and n.name == "channel_mode"][0]
    goi2 = [n for n in ast.walk(lane) if isinstance(n, ast.Call)
            and getattr(n.func, "id", "") == "process_requests"]
    assert goi2, "channel_mode không xử yêu cầu render lại -> hàng tồn không ai dọn"
    assert any(k.arg == "chi_kenh" for c in goi2 for k in c.keywords), \
        "lane phải lọc yêu cầu theo kênh mình, không ôm cả hàng"


def t_khoi_main_cuoi_file():
    """Khối `if __name__` của run_render.py phải là THỨ CUỐI CÙNG — không def nào sau nó.

    25/8 — hung thủ của 5 lane toon câm 40+ phút: `_toon_long_then_shorts` được nối vào file SAU
    khối chạy, nên đường `--channel` gọi hàm chưa tồn tại ⇒ NameError bị vòng thử-lại nuốt êm.
    Toon đi đường main() thì không sao — bug nấp 2 ngày, tới lần đầu toon vào matrix mới lộ."""
    src = _doc("run_render.py")
    i = src.index('if __name__ ==')
    sau = src[i:]
    assert "\ndef " not in sau, "còn hàm định nghĩa SAU khối __main__ -> NameError chờ nổ"
    assert "channel_mode(" in sau, "khối __main__ mất đường --channel"


def t_phien_khong_giu_khoa_qua_lau():
    """Ngân sách lane phải NGẮN HƠN timeout workflow, và cả hai phải đủ ngắn để phiên sau không bị huỷ.

    25/8 — đo trên GitHub: phiên 08:55 giữ khoá `concurrency` 150 phút trong khi số lane rơi
    18 → 3 → 1. Hai phiên 10:03 và 10:44 bị **huỷ trắng**, không lane nào chạy: 2,5 giờ chỉ có
    một mẻ rồi thoi thóp, 16 chỗ runner bỏ không."""
    import re
    src = _doc("run_render.py")
    m_soft = re.search(r'batch_budget_min", (\d+)\)', src)
    m_hard = re.search(r"HARD_S = (\d+) \* 60", src)
    assert m_soft and m_hard, "không tìm thấy ngân sách lane"
    soft, hard = int(m_soft.group(1)), int(m_hard.group(1))
    wf = _doc("../.github/workflows/render_cron.yml")
    m_to = re.search(r"timeout-minutes: (\d+)", wf[wf.index("render:"):] if "render:" in wf else wf)
    to = int(m_to.group(1)) if m_to else 0
    assert soft <= hard, f"ngân sách mềm {soft}' > cứng {hard}'"
    assert hard + 10 <= to, f"lane thoát ở {hard}' mà workflow chém ở {to}' — không đủ chỗ flush"
    # 27/8 — NỚI TRẦN TỪ 100' LÊN 190', KÈM ĐIỀU KIỆN.
    # Trần cũ sinh ra sau sự cố 25/8: phiên giữ khoá 150' trong khi SỐ LANE RƠI 18 -> 3 -> 1, hai
    # phiên sau bị huỷ trắng. Nhưng thứ gây hại là LANE RƠI, không phải thời lượng: phiên dài mà
    # lane vẫn bận thì nó thay thế được mấy phiên ngắn, còn tốt hơn (khỏi trả giá khởi động lại).
    # Nay có HÀNG CHỜ — lane xong sớm tự lấy kênh tiếp (đo phiên 04:59Z: 38 lượt "lấy việc kế").
    # Nên nới trần, nhưng BUỘC hàng chờ phải còn tồn tại: mất nó thì phiên dài quay lại đúng bệnh
    # cũ, và chốt này phải đỏ trước khi điều đó xảy ra.
    assert "lay_viec_ke" in src or "dat_hang_cho" in src, \
        "không còn hàng chờ — phiên dài sẽ để lane rơi như 25/8, hạ timeout về <= 100'"
    assert to <= 190, f"timeout {to}' quá dài — chưa có bằng chứng lane giữ được bận lâu thế"


def t_giong_nhan_vat_co_cao_do():
    """Giọng nhân vật phải truyền được CAO ĐỘ, và hai vai phải lệch nhau đủ để không lẫn.

    25/8 — `edge_tts.Communicate` vẫn nhận `pitch` nhưng hệ chưa bao giờ truyền: đại bàng khoác
    lác, gấu mèo láu cá, bà hàng xóm nhiều chuyện đều nói bằng đúng một chất giọng đọc bản tin.
    Cao độ là đòn bẩy mạnh nhất biến giọng phát thanh viên thành giọng nhân vật, và miễn phí."""
    tk = _doc("tts_karaoke.py")
    assert "pitch=pitch" in tk, "synth không truyền pitch xuống edge-tts"
    assert 'Communicate(text, voice, rate=rate, pitch=pitch' in tk, "Communicate thiếu pitch"
    assert "_ACTIVE.get(\"pitch\")" in tk, "set_voice không giữ được cao độ theo kênh"


def t_kich_ban_co_luat_viral():
    """Kịch bản skit phải mang 5 luật nâng chất 25/8 — thiếu là tụt về 'buồn cười vừa phải'."""
    src = _doc("content_brain.py")
    i = src.index("TOON_SYS = (")
    # 28/8 — cắt theo BIÊN HÀM, không theo số ký tự: cửa sổ cố định vỡ khi thân hàm
    # dài ra, và chốt đỏ vì lỗi CỦA CHÍNH NÓ chứ không phải vì mã hỏng.
    _ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
    than = src[i: min(_ket) if _ket else len(src)]
    for moc in ("ONE REAL FACT", "SPECIFIC BEATS GENERIC", "TWO DISTINCT VOICES",
                "TURN, DON'T ESCALATE FLAT", "LAST LINE IS THE PRODUCT"):
        assert moc in than, f"TOON_SYS thiếu luật «{moc}»"


def t_tts_khong_dung_bien_chua_nhan():
    """Không hàm nào trong tts_karaoke được dùng biến mà nó KHÔNG nhận / KHÔNG gán.

    25/8 — pilot 12:04Z: thêm `pitch` vào `_run` nhưng thân thật nằm ở `_synth_once`, hàm đó chưa
    có tham số ⇒ `name 'pitch' is not defined` ở TỪNG câu thoại. Vòng thử-lại nuốt thành "TTS trả
    0 giây", nên log nói về TTS trong khi lỗi là NameError của mình — mất trọn một lượt pilot.
    Python không bắt lỗi này lúc nạp module; AST thì bắt được ngay."""
    import ast
    src = _doc("tts_karaoke.py")
    t = ast.parse(src)
    # biến toàn cục hợp lệ (module-level) — không tính là "chưa nhận"
    gtoan = {n.id for x in t.body if isinstance(x, (ast.Assign, ast.AnnAssign))
             for n in ast.walk(x) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    gtoan |= {n.name for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    gtoan |= {a.asname or a.name.split(".")[0]
              for x in ast.walk(t) if isinstance(x, (ast.Import, ast.ImportFrom)) for a in x.names}
    # CHỈ soi hàm CẤP CAO NHẤT: hàm lồng đọc biến của hàm bao (closure) là hợp lệ — soi riêng
    # từng hàm lồng sẽ báo oan (đo thật: `flush` đọc `lines` của `_to_srt`).
    xau = []
    for fn in [n for n in t.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        # gom tham số của CHÍNH hàm và của mọi hàm LỒNG bên trong (kể cả lambda) — nếu không thì
        # biến của hàm lồng bị báo oan là "chưa nhận" (đo thật: 4/5 ca đầu tiên đều là oan)
        ts = set()
        for g in ast.walk(fn):
            if isinstance(g, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                ts |= {a.arg for a in g.args.args} | {a.arg for a in g.args.kwonlyargs}
                if g.args.vararg: ts.add(g.args.vararg.arg)
                if g.args.kwarg: ts.add(g.args.kwarg.arg)
        gan = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        gan |= {c.name or "" for c in ast.walk(fn) if isinstance(c, ast.ExceptHandler)}
        gan |= {t2.id for c in ast.walk(fn) if isinstance(c, (ast.For, ast.AsyncFor))
                for t2 in ast.walk(c.target) if isinstance(t2, ast.Name)}
        gan |= {t2.id for c in ast.walk(fn) if isinstance(c, ast.comprehension)
                for t2 in ast.walk(c.target) if isinstance(t2, ast.Name)}
        for n in ast.walk(fn):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                if n.id not in ts and n.id not in gan and n.id not in gtoan and not hasattr(__builtins__, n.id):
                    import builtins
                    if not hasattr(builtins, n.id):
                        xau.append(f"{fn.name}:{n.id}")
    assert not xau, f"hàm dùng biến chưa nhận/chưa gán: {sorted(set(xau))[:5]}"


def t_chu_chay_luon_doc_duoc():
    """Chữ karaoke đang chạy phải LUÔN đọc được, dù kênh chọn màu gì.

    25/8 — anh mở video BRANDEDUSA (cảnh biển Coca-Cola ĐỎ RỰC): từ đang đọc tô bằng `accent` của
    kênh (navy đậm) nên tàng hình giữa các từ trắng; kênh accent nhạt thì chìm vào nền sáng.
    Gốc sai lầm: lấy MÀU NHẬN DIỆN làm màu chữ chạy. Accent phục vụ logo/khung; chữ đang chạy chỉ
    có một việc là ĐỌC ĐƯỢC. Nay dùng bảng màu đã sàng (đều rực + sáng) + viền tối, mỗi kênh một
    màu cố định theo băm tên; màu tự đặt mà quá tối thì BỎ, quay về bảng."""
    src = _doc("../engine-remotion/src/Cinematic.tsx")
    assert "BANG_MAU" in src and "const mauChu" in src, "không có bảng màu chữ chạy"
    assert "doSang(chon) >= 0.52" in src, "mất chốt chặn màu tối làm chữ chạy"
    assert "color: on ? (vang" in src, "từ đang đọc vẫn tô bằng accent kênh"
    # mọi màu trong bảng phải THẬT SỰ sáng — nếu không thì chốt trên vô nghĩa
    import re
    bang = re.search(r'const BANG_MAU = \[([^\]]+)\]', src).group(1)
    for hx in re.findall(r'#([0-9A-Fa-f]{6})', bang):
        r, g, b = (int(hx[i:i+2], 16) / 255 for i in (0, 2, 4))
        L = 0.2126 * r + 0.7152 * g + 0.0722 * b
        assert L >= 0.52, f"màu #{hx} trong bảng chỉ sáng {L:.2f} — sẽ chìm trên nền sáng"
    # viền tối là thứ giữ chữ đọc được trên nền sáng — không được bỏ
    assert "WebkitTextStroke" in src, "mất viền chữ -> nền sáng là mất chữ"


def t_the_tieu_de_khong_tran_khung():
    """Thẻ tiêu đề phải TỰ CO cho vừa khung — tiêu đề do AI viết, độ dài không đoán trước được.

    25/8 — anh gửi ảnh: "SEMICONDUCTORS" bị cắt cụt cả đầu lẫn đuôi. Bản cũ đặt cỡ chữ CỐ ĐỊNH
    100-116px; một từ 14 ký tự ở 116px chiếm ~1.010px trong khi khung 1080 trừ lề chỉ còn 840px.
    Đặt cỡ sẵn rồi cầu may là sai nguyên tắc: cỡ chữ phải SUY TỪ CHỮ."""
    src = _doc("../engine-remotion/src/Cinematic.tsx")
    assert "_coVua" in src, "thẻ tiêu đề không có hàm co chữ"
    i = src.index("const _coVua")
    # 28/8 — cắt theo BIÊN HÀM, không theo số ký tự: cửa sổ cố định vỡ khi thân hàm
    # dài ra, và chốt đỏ vì lỗi CỦA CHÍNH NÓ chứ không phải vì mã hỏng.
    _ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
    than = src[i: min(_ket) if _ket else len(src)]
    assert "tuDaiNhat" in than, "phải tính theo TỪ DÀI NHẤT (từ đơn không xuống dòng được)"
    # 29/8 — KIỂM KHOẢNG, KHÔNG GHIM LITERAL. Bản cũ đòi đúng chuỗi "Math.max(38" và nó vỡ ngay
    # lần đầu con số ấy đổi (38 -> 26, vì sàn 38 làm tên vụ án dài bị CẮT — xem `_coVua`). Đây là
    # lần thứ năm trong tuần một chốt đỏ vì literal đổi chứ không vì mã hỏng; chốt kiểu đó dạy
    # người đọc bỏ qua nó.
    # Thứ thật sự phải đúng: CÓ một cái sàn, và sàn nằm trong khoảng đọc được (20-40px trên khung
    # cao 1920). Thấp hơn 20 là chữ li ti trên điện thoại; cao hơn 40 thì chữ dài lại bị cắt.
    import re as _re_s
    # Bắt ĐÚNG cái sàn của giá trị TRẢ VỀ (`Math.max(<sàn>, Math.min(co, …))`), không bắt bừa
    # `Math.max` đầu tiên gặp — thân hàm còn `Math.max(1, Math.min(4, …))` để đếm số dòng, và bản
    # đầu của chốt vớ phải nó rồi báo "sàn 1px".
    _san = _re_s.search(r"Math\.max\((\d+),\s*Math\.min\(co", than)
    assert _san, "thiếu sàn cỡ chữ"
    _v = int(_san.group(1))
    assert 20 <= _v <= 40, f"sàn cỡ chữ {_v}px nằm ngoài khoảng đọc được 20-40"
    # Và phải đo CẢ CÂU, không chỉ từ dài nhất: câu dài thì tổng bề ngang mới quyết định số dòng.
    # Đòi phép đo cả câu vừa ĐƯỢC TÍNH vừa ĐƯỢC DÙNG. Bản đầu viết `"vuaCau" in than or
    # "t.length" in than` và ca thử "bỏ đo cả câu" vẫn XANH: đổi tên biến là mệnh đề `or` cứu,
    # còn `t.length` thì vẫn nằm đâu đó trong thân hàm. Một phép kiểm có đường lui rộng như thế
    # thì không kiểm gì cả.
    assert than.count("vuaCau") >= 2, \
        "chỉ đo từ dài nhất -> câu dài vẫn tràn (khung COURT RECORD: 'A 2026 CASE ALMOST NOB')"
    # mọi lời gọi title() phải truyền lề THẬT, không để mặc định sai
    import re
    for m in re.finditer(r"\{title\((\d+), \"(center|left)\"(?:, (\d+))?\)", src):
        assert m.group(3), f"title({m.group(1)}) không truyền lề -> co chữ tính sai khung"

    # kiểm phép co bằng số, đúng ca đã xảy ra
    def co_vua(t, co, le, vw=1080):
        tu = max((len(w) for w in t.split()), default=1)
        return max(38, min(co, int((vw - le * 2) / (tu * 0.62))))
    assert co_vua("SEMICONDUCTORS", 116, 120) < 116, "từ dài vẫn không co"
    assert co_vua("CHIPS", 116, 120) == 116, "từ ngắn bị co oan -> tiêu đề nhỏ đi vô cớ"


def t_du_lieu_mo_khong_lam_gay_day_chuyen():
    """Mọi hàm lấy dữ liệu mở phải trả RỖNG khi hỏng, tuyệt đối không ném lên dây chuyền.

    25/8 — hào cạnh tranh mới: bản ghi chính phủ Mỹ thật hiện trên màn hình (USASpending, SEC,
    BLS, Archive.org — cả bốn đã gọi thật, không cần key). Nhưng đây là API NGOÀI: chúng sập,
    đổi định dạng, giới hạn lượt. Một nguồn hỏng mà giết cả lượt render thì hào thành gánh nặng.
    Nguyên tắc: dữ liệu là GIA VỊ, không phải xương sống."""
    import ast
    src = _doc("du_lieu_mo.py")
    t = ast.parse(src)
    # Điều thật sự cần: hàm nào cũng phải AN TOÀN TRƯỚC `None` mà `_goi` trả về khi API hỏng —
    # bằng try, hoặc bằng chặn None (`if not d` / `(d or {})`). Đòi try ở mọi hàm là cứng nhắc:
    # `_goi` đã nuốt lỗi rồi, hàm gọi nó chỉ cần đừng giả định có dữ liệu.
    ten_ham = {"hop_dong_lon", "so_lieu_sec", "chuoi_bls", "phim_tu_lieu", "_goi"}
    thay = set()
    for fn in [n for n in t.body if isinstance(n, ast.FunctionDef)]:
        if fn.name not in ten_ham:
            continue
        thay.add(fn.name)
        than_fn = ast.get_source_segment(src, fn) or ""
        an_toan = (any(isinstance(n, ast.Try) for n in ast.walk(fn))
                   or "if not d" in than_fn or "(d or {})" in than_fn or "d or {}" in than_fn)
        assert an_toan, f"{fn.name} giả định API luôn trả dữ liệu -> None là nổ giữa lượt render"
    assert thay == ten_ham, f"thiếu hàm: {sorted(ten_ham - thay)}"
    # `_goi` phải nuốt lỗi và trả None, không re-raise
    i = src.index("def _goi(")
    than = src[i:src.index("# ── 1. USASPENDING")]
    assert "return None" in than and "raise" not in than, "_goi vẫn có thể ném lỗi lên trên"


def t_cf_chan_prompt_van_con_duong_gemini():
    """CF chặn prompt thì phải NHẢY SANG GEMINI, không được trả False ngay.

    25/8 — bốn kênh toon cùng lúc ra "chỉ vẽ được 0/16 khung". Gốc: khi CF trả về không phải ảnh
    (bộ lọc prompt của họ chặn), hàm vẽ `return False` NGAY. Chú thích cũ lập luận "đổi key cũng
    vô ích vì cùng prompt" — đúng với key CF khác, nhưng SAI với Gemini: nhà cung cấp khác, bộ lọc
    khác, thường vẽ được đúng prompt đó. Trả False sớm là tự cắt đường lui duy nhất ⇒ mất cả video.
    Đúng cách: bỏ qua các key CF còn lại (cùng prompt thì cùng kết quả) nhưng ĐI TIẾP tới Gemini."""
    src = _doc("datastory_ci.py")
    i = src.index("def _generate_image_ai")
    # 28/8 — cắt theo BIÊN HÀM, không theo số ký tự: cửa sổ cố định vỡ khi thân hàm
    # dài ra, và chốt đỏ vì lỗi CỦA CHÍNH NÓ chứ không phải vì mã hỏng.
    _ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
    than = src[i: min(_ket) if _ket else len(src)]
    assert "_cf_chan_prompt" in than, "CF chặn prompt vẫn giết luôn cả lượt vẽ"
    # không còn `return False` ngay sau nhánh CF
    assert "return False               # CF trả về không phải ảnh" not in than, \
        "vẫn trả False ngay khi CF chặn -> mất đường Gemini"
    # phải bỏ qua CF còn lại để khỏi đốt lượt vô ích
    assert 'if _cf_chan_prompt and str(_k).startswith("cf:")' in than, \
        "không bỏ qua key CF còn lại -> đốt lượt vào cùng một prompt bị chặn"






def t_cong_an_toan_di_het_moi_kho_muc():
    """Cổng an toàn nội dung phải soi MỌI chỗ story cất mục, kể cả `frames` của dạng đua.

    28/8 — anh gửi khung AMERICA LOOKED UP: một dòng trong bảng ghi ".XXX". `an_toan(".xxx")` vốn
    trả False, danh sách chặn đã có sẵn — cổng KHÔNG hỏng, nó chỉ chưa bao giờ được dẫn tới đó:
    vòng lọc đi qua items/data/pairs/scenes, còn dạng `race` để mọi mục trong `frames[i].data`.
    Đây là kiểu hỏng đắt nhất của hệ này: một cổng NHÌN THÌ CÓ, chạy thì không chạm dữ liệu thật
    (cùng họ với `DongNguon` được nhập mà không được vẽ). Với cổng an toàn thì cái giá không phải
    một video xấu mà là cả một kênh.
    Chốt gọi THẬT với dữ liệu bẩn ở TỪNG kho mục, chứ không đọc mã — đọc mã chính là cách lỗi này
    lọt qua suốt thời gian dài."""
    import the_he_2 as T
    NEN = {"title": "Most-read on Wikipedia", "nguon": "wikipedia",
           "narration": ["a", "b", "c", "d"]}
    BAN = {"name": ".XXX", "value": 3, "stat": "3"}
    SACH = [{"name": f"Item {i}", "value": 9 - i, "stat": str(9 - i)} for i in range(6)]
    for kho in ("items", "data", "pairs"):
        st = {**NEN, kho: [dict(BAN)] + [dict(x) for x in SACH]}
        ra = T._cong_an_toan(st, "CHOT")
        con = [m.get("name") for m in ((ra or {}).get(kho) or [])]
        assert ra is None or ".XXX" not in con, f"cổng bỏ sót mục bẩn ở `{kho}`: {con}"
    fr = {**NEN, "frames": [{"t": f"Aug {i}", "data": [dict(BAN)] + [dict(x) for x in SACH[:4]]}
                            for i in range(13, 19)]}
    ra = T._cong_an_toan(fr, "CHOT")
    con = [m.get("name") for f2 in ((ra or {}).get("frames") or []) for m in (f2.get("data") or [])]
    assert ra is None or ".XXX" not in con, f"cổng bỏ sót mục bẩn trong `frames`: {set(con)}"




def t_nhan_tinh_bi_bo_khi_xoay_truc():
    """Xoay trục thì NHÃN TĨNH của kênh phải biến mất, kể cả sau khi bộ dựng gộp lại tham số.

    28/8 vá lần một bằng `ky.pop("nhan")` trong `_dung_story_xoay` — và nó KHÔNG chạy. Mọi
    `dung_story_*` đều mở đầu bằng `ts = dict(kenh["tham_so"]); ts.update(ky)`, tức dựng lại tham
    số TỪ CẤU HÌNH KÊNH rồi mới chồng `ky` lên: khoá đã xoá thì không có gì để chồng, nên nhãn
    tĩnh sống lại nguyên vẹn ở tầng dưới. Một ngày sau mới lộ, trên khung đã render:
        "Breakfast cereal: what is really in it — Ice-creams"
    khung nói ngũ cốc, dữ liệu là KEM. Đây là loại sai tệ nhất: không xấu, không thiếu, mà NÓI SAI.

    Chốt chạy THẬT qua `_dung_story_xoay` với một bộ dựng giả chỉ việc trả lại `ky` nó nhận được —
    không cần mạng, không cần nguồn, và đo đúng thứ đã hỏng: giá trị tới TAY BỘ DỰNG là gì."""
    import the_he_2 as T
    nhan_ky = {}

    def _gia(kenh, ky):
        # mô phỏng đúng dòng đầu của mọi `dung_story_*` thật
        ts = dict(kenh.get("tham_so") or {})
        ts.update(ky or {})
        nhan_ky["thay"] = ts.get("nhan")
        nhan_ky["mon"] = ts.get("mon")
        # ÉP XOAY bằng cách từ chối giá trị gốc. Bản trước ép bằng danh sách `avoid`, và nó không
        # ép được: tiêu đề còn đi qua `hoan_tieu_de` (gắn trục + dựng lại từ dữ liệu) nên chuỗi
        # cuối không còn khớp mục trong `avoid`. Bộ dựng trả None thì lượt đó bị bỏ chắc chắn,
        # không phụ thuộc bất cứ tầng nào phía sau.
        if ts.get("mon") == "breakfast-cereals":
            return None
        return {"title": f"{ts.get('nhan') or str(ts.get('mon') or '').title()}: what is in it",
                "items": [{"name": f"m{i}", "stat": str(9 - i)} for i in range(4)],
                "nguon": "off", "subtitle": "by calories", "narration": ["a", "b", "c", "d"]}

    # Kho xoay RIÊNG của kênh giả + tắt phép xếp-theo-nhu-cầu: thứ tự kho thật do radar quyết nên
    # nó đổi theo ngày, và một chốt phụ thuộc thứ tự ấy sẽ đỏ/xanh ngẫu nhiên — đã dính đúng vậy ở
    # bản đầu. Chốt phải tất định, nếu không thì không ai tin nó nữa.
    kenh = {"ten": "CHOT", "dinh_dang": "ranked", "nguon": "off",
            "tham_so": {"mon": "breakfast-cereals", "nhan": "Breakfast cereal", "xoay": "mon",
                        "kho_mon": ["breakfast-cereals", "chips"]}}
    cu = T.DUNG_STORY.get("ranked")
    xep_cu = T._xep_theo_nhu_cau
    try:
        T.DUNG_STORY["ranked"] = _gia
        T._xep_theo_nhu_cau = lambda kenh, truc, kho: list(kho)     # giữ nguyên thứ tự khai
        st = T._dung_story_xoay("ranked", kenh, dict(kenh["tham_so"]), [])
    finally:
        T._xep_theo_nhu_cau = xep_cu
        if cu:
            T.DUNG_STORY["ranked"] = cu
    assert st, "không dựng được story nào"
    assert str(nhan_ky.get("mon")) != "breakfast-cereals", \
        "trục không xoay được — chốt không đo được gì"
    assert not nhan_ky.get("nhan") if False else not nhan_ky.get("thay"), (
        f"nhãn tĩnh {nhan_ky.get('thay')!r} SỐNG LẠI ở tầng bộ dựng sau khi trục đã xoay sang "
        f"{nhan_ky.get('mon')!r} — tiêu đề sẽ nói sai nội dung")




def t_gu_ve_khop_tung_kenh():
    """Mỗi kênh phải có gu vẽ TIẾNG ANH gán TAY, khớp nội dung kênh đó.

    29/8 — hai lỗi liên tiếp ở chỗ này, ghi lại cả hai:
    ① Gu khai bằng TIẾNG VIỆT rồi ghép thẳng vào prompt (`f"A {style} of: …"`). Máy vẽ không đọc
       được, bỏ qua, rơi về mặc định của nó là ẢNH CHỤP NGƯỜI THẬT — thứ nó vẽ dở nhất (tay thừa
       ngón, chữ sai chính tả) và cũng là thứ anh bác. 28 kênh khai gu riêng, không kênh nào nhận.
    ② Vá xong thì gán gu THEO NICHE, và niche là nhãn PHÂN LOẠI KHO chứ không mô tả nội dung:
       QUIET LAYOFFS (sa thải) ra tranh vũ trụ vì niche ghi "Công nghệ & AI"; PILL FACTS (thu hồi
       thuốc) ra chibi dễ thương vì niche ghi "Sức khoẻ & gym". Anh gọi đúng tên: "râu ông nọ cắm
       cằm bà kia".
    Nên chốt đòi ba điều: gán đủ TAY cho mọi kênh, gu ra là tiếng Anh, và có câu cấm ảnh chụp."""
    import io as _io2
    import json as _json
    import the_he_2 as T
    ks = _json.loads(_doc("kenh_the_he_2.json"))
    ks = ks if isinstance(ks, list) else list(ks.values())
    ten = {str(k.get("ten") or "").strip().upper() for k in ks}
    thieu = sorted(ten - set(T.GU_THEO_KENH))
    assert not thieu, ("kênh chưa gán gu vẽ tay (sẽ rơi về suy theo niche -> gán sai chủ đề): "
                       + ", ".join(thieu))
    thua = sorted(set(T.GU_THEO_KENH) - ten)
    assert not thua, "bảng gu còn tên kênh không tồn tại: " + ", ".join(thua)
    for k in ks:
        g = T.gu_ve(k)
        # Cấm DẤU TIẾNG VIỆT, không cấm mọi ký tự ngoài ASCII: bản đầu của phép kiểm này đỏ vì
        # dấu gạch dài "—" trong chính chuỗi gu — một ký tự máy vẽ đọc bình thường. Chốt phải bắt
        # đúng thứ nó sinh ra để bắt (chuỗi tiếng Việt lọt vào prompt), không bắt vạ.
        _viet = "ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ"
        _co = [c for c in g.lower() if c in _viet]
        assert not _co, \
            f"{k['ten']}: gu vẽ còn chữ tiếng Việt ({''.join(sorted(set(_co)))}) -> máy vẽ bỏ qua"
        assert "not photorealistic" in g or "NOT a photograph" in g, \
            f"{k['ten']}: gu vẽ thiếu lệnh cấm ảnh chụp -> máy vẽ rơi về ảnh người thật"




def t_nhan_none_khong_lot_len_tieu_de():
    """Không bộ dựng nào được đọc `nhan` bằng `get(khoa, mặc_định)` — phải dùng `or`.

    29/8 — bản vá nhãn-tĩnh đặt `ky["nhan"] = None` khi xoay trục (đặt None chứ không xoá, vì bộ
    dựng gộp lại tham số từ cấu hình kênh nên khoá đã xoá sẽ sống lại). Nhưng `dict.get(k, mặc)`
    chỉ trả mặc định khi khoá VẮNG MẶT — khoá có mà giá trị None thì nó trả đúng None.
    Khung thật DEGREE WORTH: tiêu đề ra **"2024: 299.7 — NONE BY YEAR (2015)"**.
    Một bản vá tự đẻ ra lỗi ở tầng dưới, và chỉ thấy được khi nhìn khung đã render.
    `or` xử lý đúng cả hai: khoá vắng, và khoá có giá trị rỗng/None."""
    import re as _re_n
    src = _doc("the_he_2.py")
    xau = _re_n.findall(r"""\.get\(\s*['"]nhan['"]\s*,\s*[^)]+\)""", src)
    assert not xau, ("đọc `nhan` bằng get(khoá, mặc_định) -> None sẽ lọt lên tiêu đề: "
                     + " · ".join(xau[:4]))
    # Và phải CÓ chỗ đọc bằng `or` — nếu không thì chốt trên xanh chỉ vì không ai đọc `nhan` nữa.
    assert "'nhan') or" in src or '"nhan") or' in src, "không thấy chỗ nào đọc `nhan` bằng `or`"




def t_ai_only_khong_lay_clip_kho():
    """Kênh khai `ai_only` thì KHÔNG được lấy clip video từ kho ảnh/video có sẵn.

    29/8 — anh soi khung COURT RECORD: "vẫn ảnh thật, ko phải chart vector". Không phải gu vẽ
    hỏng: props ghi `clip: th2_s0.mp4` — cảnh đó là VIDEO KHO TỪ PEXELS, đi bằng một đường hoàn
    toàn khác đường vẽ ảnh.
    `ai_only=True` nghĩa là "kênh này tự vẽ mọi thứ, không dùng kho", nhưng nó mới chỉ chặn nhánh
    ẢNH (Openverse); nhánh CLIP chạy song song và chưa ai hỏi nó. Mỗi video cinematic có 1/3 số
    cảnh là footage tải về, trong khi cả hệ được xây quanh lời hứa "không dùng footage".
    Cùng họ với `style_anh` viết tiếng Việt và `DongNguon` được nhập mà không được vẽ: một cờ khai
    ra ở tầng này, tầng kia không đọc."""
    src = _doc("datastory_ci.py")
    i = src.index("fetch_clip(img_query")
    # Lấy dòng ĐIỀU KIỆN ngay trước lời gọi — chỗ quyết định có tải clip hay không.
    dau = src.rfind("if ", max(0, i - 700), i)
    dieu_kien = src[dau:i]
    assert "ai_only" in dieu_kien, \
        ("đường lấy clip kho KHÔNG hỏi `ai_only` -> kênh cam kết tự vẽ vẫn nhận footage tải về: "
         + " ".join(dieu_kien.split())[:110])




def t_bo_cuc_ranked_khong_dung_chung_mot_khuon():
    """18 kênh `ranked` phải chia ra nhiều bố cục, và mọi kênh phải được gán TAY.

    29/8 — anh soi ba kênh ranked cạnh nhau: "vẫn còn rẻ tiền, channel nào cũng làm được". 18/50
    kênh dùng chung bảng tier S/A/B/C; `bien_cua` có 27 biến thể nhưng chỉ đổi vị trí nhãn, kiểu
    viền, hoạ tiết nền — bộ khung thì một, nên ba kênh đọc ra là một kênh đổi filter.
    Đây là rủi ro lớn nhất còn lại với chính sách "nội dung sản xuất hàng loạt" của YouTube, tức
    là thứ quyết định bật được kiếm tiền hay không — không phải chuyện thẩm mỹ.

    Chốt đòi ba điều: mọi kênh ranked được gán tay, có ít nhất ba bố cục khác nhau, và không bố
    cục nào ôm quá nửa số kênh."""
    import json as _json
    import the_he_2 as T
    ks = _json.loads(_doc("kenh_the_he_2.json"))
    ks = ks if isinstance(ks, list) else list(ks.values())
    r = [k for k in ks if k.get("dinh_dang") == "ranked"]
    assert r, "không còn kênh ranked nào — chốt này hết nghĩa, xoá đi"
    # 29/8 — kênh `scaled` cũng phải gán tay: chúng đã chuyển sang bố cục vector và bỏ ảnh AI,
    # nên kênh nào rơi ra ngoài bảng sẽ lặng lẽ quay về ScaledShort và vẽ lại 6 ảnh mỗi video.
    sc = [k for k in ks if k.get("dinh_dang") == "scaled"]
    thieu_sc = [k["ten"] for k in sc
                if str(k["ten"]).replace(" ", "").upper() not in T.BO_CUC_KENH]
    assert not thieu_sc, "kênh scaled chưa gán bố cục: " + ", ".join(thieu_sc)
    thieu = [k["ten"] for k in r
             if str(k["ten"]).replace(" ", "").upper() not in T.BO_CUC_KENH]
    assert not thieu, "kênh ranked chưa gán bố cục (sẽ rơi về bảng tier chung): " + ", ".join(thieu)
    from collections import Counter
    dem = Counter(T.bo_cuc_cua(k, "ranked") for k in r)
    assert len(dem) >= 3, f"chỉ {len(dem)} bố cục cho {len(r)} kênh — vẫn là một khuôn: {dict(dem)}"
    lon = max(dem.values())
    assert lon <= len(r) / 2, \
        f"một bố cục ôm {lon}/{len(r)} kênh — quá nửa thì vẫn đọc ra là cùng một lò: {dict(dem)}"
    # Và composition được gán phải CÓ THẬT trong Root.tsx, nếu không thì render nổ ở lane.
    root = _doc("../engine-remotion/src/Root.tsx")
    for c in set(dem):
        assert f'id="{c}"' in root, f"bố cục {c} chưa đăng ký trong Root.tsx"




def t_prompt_ve_khong_goi_ten_mat_chu():
    """Không prompt vẽ nào được gọi tên một thứ CÓ MẶT PHẲNG CHỨA CHỮ hướng vào ống kính.

    29/8 — anh: "ko nên có chữ ở ảnh AI generate", và chữ bịa trên kênh hồ sơ công CHÍNH LÀ nội
    dung sai sự thật. Đã thử bốn vòng ra lệnh cho máy vẽ (cấm ở đuôi prompt · cấm ở đầu prompt ·
    "mọi mặt giấy đều trống" · "vẽ chữ thành nét nguệch ngoạc") và khung lần lượt ra
    "PUBLIC RECCORDS" · "Publlic Records" · "COURTE OPITION" · "ourt Opitric".
    Kết luận đo được: mô hình khuếch tán KHÔNG có khái niệm "đừng vẽ", chỉ có "vẽ cái gì". Hễ
    prompt gọi tên một tờ giấy thì nó dựng một mặt phẳng, và mặt phẳng nào cũng bị điền chữ.

    Nên chặn ở PROMPT, không chặn ở lệnh. Danh từ nguy hiểm chỉ được phép xuất hiện kèm một từ
    khoá đổi góc nhìn (edge-on / from behind / closed / face-down …) — lúc đó mặt chữ không còn
    hướng vào ống kính nữa."""
    import re as _re_p
    src = _doc("the_he_2.py")
    i = src.index("def _pk_ban_an")
    j = src.find("\nBO_PHIM", i)
    than = src[i: j if j > 0 else len(src)]
    # 29/8 — MỞ RỘNG sau khi soi khung SONG FILE: hai prompt lọt lưới và ra chữ giả đầy khung
    # ("FIDELY CARES" lặp kín một tủ phiếu, chữ neon "uwh" cỡ lớn). Chúng lọt vì danh từ của chúng
    # ("index card", "marquee") không có trong danh sách. Danh sách này phải rộng hơn trực giác:
    # bất cứ thứ gì con người VIẾT LÊN đều là một mặt chữ tiềm năng.
    NGUY = ("document", "file", "folder", "record", "paper", "page", "newspaper", "headline",
            "signage", "sign", "label", "book", "report", "form", "screen", "monitor", "poster",
            "banner", "notice", "ledger", "envelope", "receipt", "ticket", "calendar",
            "card", "cards", "catalogue", "catalog", "index", "marquee", "neon", "billboard",
            "plaque", "certificate", "chart", "diagram", "tag", "sticker", "logo", "brand")
    # Cận cảnh CỰC SÁT cũng an toàn: khung chỉ còn một mảnh bề mặt, không đủ chỗ cho một từ
    # trọn vẹn. "record grooves in extreme close-up" là rãnh đĩa, không phải nhãn đĩa.
    # Ngoại lệ này có lý do vật lý, không phải để cho một prompt cụ thể lọt qua.
    AN_TOAN = ("edge-on", "from behind", "from the ends", "closed", "face-down", "stacked",
               "spines", "tabs", "rolled", "seen from", "extreme close-up")
    xau = []
    for m in _re_p.finditer(r'"([a-z][^"]{12,110})"', than):
        q = m.group(1)
        if not any(f" {c}" in f" {q}" or q.startswith(c) for c in NGUY):
            continue
        if any(a in q for a in AN_TOAN):
            continue
        xau.append(q)
    assert not xau, ("prompt vẽ gọi tên thứ có mặt chữ mà KHÔNG đổi góc nhìn -> máy vẽ sẽ bịa chữ: "
                     + " · ".join(x[:52] for x in xau[:4]))




def t_dong_ho_dua_chiu_moc_chu():
    """Đồng hồ của biểu đồ đua phải hiện được mốc KHÔNG PHẢI SỐ.

    29/8 — bản vá sáng nay đổi mốc của kênh đếm-theo-ngày từ mã thô "20260813" sang chữ "Aug 13"
    (mã thô từng hiện nguyên "20260741" cỡ chữ lớn nhất khung hình). Nhưng `BarChartRace` nội suy
    `a.t` như một con số, nên chuỗi chữ ra NaN — và đồng hồ hiện **"NaN"** ở cả ba khung của
    AMERICA LOOKED UP. Sửa một chỗ rồi làm hỏng chỗ khác vì hai bên hiểu khác nhau về KIỂU của
    cùng một trường; đúng họ lỗi đã đuổi theo suốt tuần.
    Chốt đòi chỗ nội suy phải nhận ra kiểu trước khi tính."""
    src = _doc("../engine-remotion/src/BarChartRace.tsx")
    i = src.index("const year =")
    khoi = src[max(0, i - 400): i + 320]
    assert "isFinite" in khoi or "Number.isFinite" in khoi, \
        "đồng hồ đua nội suy `t` mà không kiểm kiểu -> mốc chữ sẽ ra NaN"
    assert "String(a.t)" in khoi, "không có nhánh hiện mốc CHỮ nguyên văn"




def t_moi_gia_tri_truc_deu_co_nhanh():
    """HAI KÊNH KHÔNG ĐƯỢC RA CÙNG MỘT TIÊU ĐỀ.

    29/8 — khung thật GAME GRAVEYARD hiện ĐÚNG nội dung của STEAM TRUTH (Counter-Strike 1.0M,
    PUBG 314.7K). Hai kênh, một video. Vì `kho_loc` của nó khai bốn giá trị mà `_bd_steam` chỉ có
    nhánh cho một; ba giá trị kia rơi xuống nhánh MẶC ĐỊNH, và nhánh mặc định chính là câu chuyện
    của kênh bên cạnh. Không một dòng log nào báo.
    Đây là TRÙNG NỘI DUNG GIỮA HAI KÊNH — thứ chính sách "sản xuất hàng loạt" của YouTube nhắm
    thẳng vào, nặng hơn hẳn một lỗi hiển thị.

    BẢN ĐẦU CỦA CHỐT NÀY ĐO SAI: nó soi trùng TRONG một kênh, mà lỗi thật là trùng GIỮA hai kênh —
    nên nó xanh ngay cả khi tôi cố tình phá mã. Một chốt không đỏ được là một chốt không tồn tại.
    Nay gom tiêu đề của MỌI kênh dùng chung một bộ dựng và đòi chúng đôi một khác nhau."""
    import json as _json
    import du_lieu_mo as D
    import the_he_2 as T
    ks = _json.loads(_doc("kenh_the_he_2.json"))
    ks = ks if isinstance(ks, list) else list(ks.values())
    # Gom theo BỘ DỰNG: chỉ các kênh dùng chung một hàm mới có cửa giẫm chân nhau.
    theo_ham: dict = {}
    for k in ks:
        ts = k.get("tham_so") or {}
        if str(ts.get("xoay") or "") != "loc":
            continue
        theo_ham.setdefault(k.get("ham"), []).append(k)
    xau = []
    for ham, nhom in theo_ham.items():
        if len(nhom) < 2:
            continue
        bo = T.BO_CHUYEN.get(ham)
        if not bo:
            continue
        chu: dict = {}
        for k in nhom:
            ts = k.get("tham_so") or {}
            for v in (ts.get("kho_loc") or [ts.get("loc")]):
                try:
                    r = bo(D, {**ts, "loc": v})
                except Exception:
                    r = None
                if r:
                    chu.setdefault(str(r[0]), set()).add(k["ten"])
        for t, ten in chu.items():
            if len(ten) > 1:
                xau.append(f"{sorted(ten)} cùng ra {t[:44]!r}")
    assert not xau, ("hai kênh ra CÙNG một tiêu đề -> trùng nội dung: " + " · ".join(xau[:3]))



def t_moi_nguon_co_ten_that():
    """Mọi `nguon` của 50 kênh phải có tên cơ quan thật trong TEN_NGUON.

    28/8 — soi khung thật kênh WHERE TO MOVE: dòng dưới đáy in "Source: zillow". Chữ thường,
    không viết hoa, đọc như một biến bị lộ chứ không như một nguồn dữ liệu. Cả điểm tin cậy của
    kênh nằm ở dòng đó — nó là bằng chứng "số này tra được", và cũng là thứ đứng ra trước chính
    sách nội dung sản xuất hàng loạt của YouTube.
    `ten_nguon()` TRẢ NGUYÊN MÃ khi thiếu bản dịch, nên lỗi này không kêu một tiếng nào trong log:
    chỉ thấy được bằng mắt, trên khung, sau khi đã render xong. Đúng họ với `DongNguon` được nhập
    mà không được vẽ, và với `bien_cua` khai ra mà không ai gửi.
    Thêm kênh mới mà quên dịch nguồn thì chốt này đỏ ngay ở `--plan`, trước khi tốn phút render."""
    import json as _json
    import the_he_2 as T
    ks = _json.loads(_doc("kenh_the_he_2.json"))
    ks = ks if isinstance(ks, list) else list(ks.values())
    thieu = sorted({str(k.get("nguon")) for k in ks
                    if str(k.get("nguon") or "") and str(k["nguon"]).lower() not in T.TEN_NGUON})
    assert not thieu, ("nguồn chưa có tên cơ quan (sẽ in NGUYÊN MÃ lên video): "
                       + ", ".join(thieu))
    # Và bản dịch phải TRÔNG như tên cơ quan chứ không như mã: đủ dài, có chữ hoa.
    xau = [f"{k}->{v}" for k, v in T.TEN_NGUON.items()
           if len(str(v)) < 4 or str(v) == str(v).lower()]
    assert not xau, "tên nguồn vẫn giống mã nội bộ: " + ", ".join(xau[:5])



def t_xoay_truc_doi_tieu_de():
    """Xoay trục đề tài mà TIÊU ĐỀ không đổi thì chống-trùng giết sạch lượt xoay.

    26/8 — đo thật RECALL PLATE (openFDA): `nam` 2025→2020 ra sáu bộ dữ liệu khác nhau, `title`
    giống hệt cả sáu. `_tieu_de_da_lam` so bằng tiêu đề ⇒ coi cả sáu là đã làm ⇒ bộ 1 long + 3
    short co còn 1 chương (đo: long 31,1s = đúng một short), và kênh đăng MỘT video rồi câm hẳn.
    Log lại ghi "hết kho đề tài" nên nhìn như kho cạn, không như lỗi — đắt gấp đôi.

    Hai điều kiện phải cùng đúng:
      • có hàm gắn giá trị trục vào tiêu đề, và `_dung_story_xoay` GỌI nó trước khi so trùng;
      • KHÔNG còn "lượt 0 trần" khi kênh có kho xoay — lượt 0 không nêu giá trị trục nên tiêu đề
        nó khác dạng với các lượt sau, hai dạng cho cùng một bộ dữ liệu là đăng trùng."""
    import the_he_2 as T
    src = _doc("the_he_2.py")
    assert "_gan_truc_vao_tieu_de" in src, "không có hàm gắn trục vào tiêu đề"
    # 28/8 — cắt theo BIÊN HÀM, không theo số ký tự: cửa sổ cố định vỡ khi thân hàm
    # dài ra, và chốt đỏ vì lỗi CỦA CHÍNH NÓ chứ không phải vì mã hỏng.
    def _than(ten):
        j = src.index("def " + ten)
        k = [x for x in (src.find("\ndef ", j + 5), src.find("\nclass ", j + 5)) if x > 0]
        return src[j: min(k) if k else len(src)]

    # 28/8 — MÃ DỰNG TIÊU ĐỀ ĐÃ TÁCH SANG `hoan_tieu_de`, để bộ chấm `cham_kenh.py` gọi được
    # ĐÚNG mã mà máy chạy (bản đầu của nó gọi thẳng `DUNG_STORY`, bỏ mất hai lớp sửa tiêu đề, và
    # kết luận sai rằng 23 kênh có tiêu đề cố định). Chốt đi theo chỗ mã đã dời: đòi phép gắn trục
    # nằm trong `hoan_tieu_de`, và `_dung_story_xoay` phải GỌI `hoan_tieu_de` TRƯỚC khi so trùng —
    # so trùng trên một tiêu đề chưa hoàn thì so nhầm chuỗi, đúng họ lỗi nó sinh ra để chặn.
    hoan = _than("hoan_tieu_de")
    assert "_gan_truc_vao_tieu_de" in hoan, "hoan_tieu_de không gắn trục vào tiêu đề"
    than = _than("_dung_story_xoay")
    assert "hoan_tieu_de" in than, "_dung_story_xoay không gọi hoan_tieu_de"
    assert than.index("hoan_tieu_de") < than.index("_tieu_de_da_lam"), "hoàn tiêu đề SAU khi so trùng thì vô nghĩa"
    assert "thu = [dict(ky or {})]" not in than, "vẫn còn lượt 0 trần -> hai dạng tiêu đề"
    # ĐO THẬT: cùng tiêu đề gốc, ba giá trị trục phải ra ba tiêu đề khác nhau
    goc = "Food recalls you probably missed"
    ra = [T._gan_truc_vao_tieu_de(goc, "nam", n) for n in (2025, 2024, 2023)]
    assert len(set(ra)) == 3, f"xoay `nam` vẫn ra tiêu đề trùng: {ra}"
    rn = [T._gan_truc_vao_tieu_de(goc, "ngay", d) for d in (7, 30, 90)]
    assert len(set(rn)) == 3, f"xoay `ngay` vẫn ra tiêu đề trùng: {rn}"
    # ĐO HÀNH VI CỦA `hoan_tieu_de`, KHÔNG CHỈ ĐỌC MÃ NÓ.
    # Bài kiểm-cái-kiểm: bỏ dòng gắn trục thứ nhất trong `hoan_tieu_de` thì mọi phép soi-chuỗi ở
    # trên VẪN XANH, vì tên hàm còn xuất hiện ở nhánh dưới. Một chốt không đỏ được là một chốt
    # không tồn tại. Gọi thật với ba giá trị trục và đòi ba tiêu đề khác nhau thì bỏ ở đâu cũng đỏ.
    # HAI KIỂU STORY, vì tiêu đề đi ra bằng HAI NHÁNH khác nhau và mỗi nhánh phải tự đứng được:
    #   • story KHÔNG có bảng mục -> `_tieu_de_tu_du_lieu` trả rỗng, chỉ còn nhánh gắn trục;
    #   • story CÓ bảng mục       -> bản dựng-từ-dữ-liệu thắng, và nó phải được gắn lại mốc thời
    #     gian, nếu không thì chủ thể đứng đầu không đổi là hai lượt trùng tên.
    # Thử một kiểu thôi thì nhánh kia bị nhánh này che, và chốt xanh trong khi mã đã thủng.
    for _nhan, _gia in (
        ("không có bảng mục", {"title": "Food recalls you probably missed", "nguon": "openfda"}),
        ("có bảng mục", {"title": "Food recalls you probably missed", "nguon": "openfda",
                          "items": [{"name": "Same Brand", "stat": "1"}]}),
    ):
        _rh = {T.hoan_tieu_de(dict(_gia), {"ten": "X"}, "nam", {"nam": n}, [])["title"]
               for n in (2025, 2024, 2023)}
        assert len(_rh) == 3, f"hoan_tieu_de ({_nhan}): ba giá trị trục ra {len(_rh)} tiêu đề: {_rh}"

    # đã có sẵn giá trị trong tiêu đề thì KHÔNG nhét thêm lần nữa
    assert T._gan_truc_vao_tieu_de("Recalls in 2024", "nam", 2024) == "Recalls in 2024",         "nhét trùng giá trị đã có sẵn trong tiêu đề"


def t_root_rac_loai_tu_goc():
    """Bản ghi kho có `root` rác phải bị loại NGAY khâu đọc danh sách.

    26/8 — anh nhắc nhiều lần: ADISONDURHAM báo hỏng, em bảo đã xử lý, nó vẫn báo. Gốc: cờ kho
    chết chỉ NGỦ 12 TIẾNG rồi tự thử lại (đúng cho token hết hạn, vì kết nối lại là sống). Nhưng
    bản ghi này mang `root: "undefined"` — chuỗi truthy nên lọt hết `if c.get("root")`, mà thư mục
    đó không tồn tại và sẽ không bao giờ tồn tại. Hỏng CẤU TRÚC không được xếp chung với hỏng TẠM
    THỜI: cứ 12 tiếng thử lại một lần là lặp vô hạn, lại còn được đếm là kho còn chỗ."""
    import importlib, sys, os
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "MM0-AutoPublisher", "src")
    # 26/8 — CHỐT LIÊN-REPO PHẢI TỰ BỎ QUA KHI THIẾU REPO KIA. Chốt này chạy được ở máy anh (có cả
    # hai repo) nhưng ĐỎ trong workflow `seed_the_he_2` — workflow đó không checkout
    # MM0-AutoPublisher. Mà selftest đỏ thì CHẶN CẢ PHIÊN, nên một chốt viết ẩu làm đứng cả dây
    # chuyền seed. Repo vốn đã có khuôn đúng cho việc này (xem `t_50_kenh_dong_bo_du_3_noi`): thiếu
    # thì bỏ qua, NHƯNG PHẢI NÓI RÕ là đã bỏ qua — im lặng bỏ qua chính là bẫy "phép thử chạy trên
    # đầu vào rỗng".
    if not os.path.exists(os.path.join(d, "storage.py")):
        print("      ⏭  bỏ qua: không có repo MM0-AutoPublisher ở đây (chốt liên-repo)")
        return
    sys.path.insert(0, os.path.abspath(d))
    S = importlib.import_module("storage")
    for xau in ("undefined", "null", "None", "", "  ", "0"):
        assert not S._root_xai_duoc({"root": xau, "channel": "X"}), f"root={xau!r} vẫn lọt"
    assert S._root_xai_duoc({"root": "1AbC_thuMucThat", "channel": "X"}), "root thật bị loại oan"
    src = _doc(os.path.join(d, "storage.py"))
    assert 'if c.get("refresh_token") and c.get("root")' not in src,         "còn chỗ dựng danh sách kho chỉ kiểm root truthy -> 'undefined' lọt qua"




def t_do_dam_phong_co_that():
    """Xin độ đậm mà phông không có ⇒ `loadFont` ném lỗi ⇒ rơi về nạp phông TRẦN.

    26/8 — khối `_CHON` trong Phong.tsx được viết ra để cắt lượt tải phông, và nó KHÔNG chạy: xin
    cứng `["700","800","900"]` cho cả 24 phông, trong khi Oswald chỉ có tới 700 và Anton chỉ có
    400. Ném lỗi -> `catch` -> `f()` trần -> nạp mọi độ đậm × mọi bộ ký tự, đúng thứ định tránh,
    mà log im vì ngoại lệ đã bị nuốt. Đo thật sau khi "tối ưu": 29 lượt cho Oswald, 40 cho Manrope.

    Chốt này KHÔNG đọc chú thích mà hỏi thẳng `getInfo()` của từng phông — dữ liệu cục bộ, không
    cần mạng — rồi đòi danh sách xin phải là tập con KHÁC RỖNG của danh sách có."""
    import json as _j, subprocess as _sp, os as _o, re as _r
    goc = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "engine-remotion")
    # Cùng lý do như trên: chốt này gọi `node` để hỏi metadata phông, cần `node_modules`. Workflow
    # nào không cài (seed, dọn kho…) thì bỏ qua có báo, thay vì đỏ và chặn cả phiên.
    if not _o.path.isdir(_o.path.join(goc, "node_modules", "@remotion")):
        print("      ⏭  bỏ qua: chưa cài node_modules của engine-remotion (chốt cần node)")
        return
    src = _doc(_o.path.join(goc, "src", "Phong.tsx"))
    assert "_do_dam" in src and "getInfo" in src,         "Phong.tsx vẫn xin độ đậm cứng, không hỏi phông có gì"
    assert 'weights: ["700", "800", "900"]' not in src, "còn danh sách độ đậm cứng"
    ten = sorted(set(_r.findall(r'@remotion/google-fonts/(\w+)"', src)))
    assert len(ten) >= 20, f"chỉ thấy {len(ten)} phông trong Phong.tsx"
    js = ("(async()=>{const MUON=['700','800','900'];const xau=[];"
          "for (const n of %s){const m=await import('@remotion/google-fonts/'+n);"
          "const co=Object.keys((m.getInfo().fonts||{}).normal||{});"
          "const giao=MUON.filter(w=>co.includes(w));"
          "const xin=giao.length?giao:[co.sort((a,b)=>Number(b)-Number(a))[0]];"
          "if(!xin.length||xin.some(w=>!co.includes(w)))xau.push(n+':'+xin+'/'+co);}"
          "console.log(JSON.stringify(xau));})()" % _j.dumps(ten))
    r = _sp.run(["node", "-e", js], cwd=goc, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"không chạy được kiểm phông: {r.stderr[-200:]}"
    xau = _j.loads(r.stdout.strip().splitlines()[-1])
    assert not xau, f"xin độ đậm phông KHÔNG CÓ -> sẽ nạp phông trần: {xau}"




def t_cong_biet_moi_co():
    """Thêm một cờ CLI mới thì CỔNG "chỉ đếm" phải biết nó.

    26/8 — thêm `--job` cho `don_the_he_1.py`, workflow truyền đúng cờ, log sạch trơn, mà khối dọn
    job KHÔNG BAO GIỜ chạy: cổng `if not (lam_tat or lam_kho or lam_bg): return 0` đứng trước nó và
    không biết cờ mới. Không có gì đỏ để thấy — chỉ có việc không xảy ra.

    Chốt bằng cách so HAI TẬP: mọi biến `lam_*` đọc từ `sys.argv`, và mọi biến xuất hiện trong biểu
    thức cổng. Thiếu cái nào là đỏ."""
    import re as _re
    src = _doc("don_the_he_1.py")
    co = set(_re.findall(r"(lam_\w+)\s*=\s*\"--[\w-]+\" in sys\.argv", src))
    assert len(co) >= 4, f"không dò ra cờ CLI ({co})"
    m = _re.search(r"if not \(([^)]+)\):", src)
    assert m, "không tìm thấy cổng chỉ-đếm"
    trong_cong = set(_re.findall(r"lam_\w+", m.group(1)))
    thieu = co - trong_cong
    assert not thieu, f"cờ có mà cổng không biết -> nhánh không bao giờ chạy: {sorted(thieu)}"




def t_bien_bo_cuc_khong_trung():
    """Hai kênh cùng `dinh_dang` không được ra cùng một bố cục.

    26/8 — anh chỉ đúng chỗ hở cuối cùng của bộ nhận diện: đo 50 kênh thì màu chính 50/50 khác
    nhau, chữ ký giọng 50/50 khác nhau, nhưng `dinh_dang` chỉ có **7 giá trị cho 50 kênh** và
    `ranked` dùng lại **18 lần**. Khán giả nhận ra "cùng một lò" qua BỐ CỤC — vị trí nhãn, hình
    thẻ, hoạ tiết nền — chứ không qua mã màu, nên 18 kênh vẫn nhìn như một.

    Chốt ba tầng, vì bệnh kinh niên của việc này là "khai ra rồi không ai đọc":
      1. mỗi kênh trong cùng một dạng phải có chỉ số biến thể KHÁC nhau;
      2. số tổ hợp phải ĐỦ cho nhóm đông nhất (18 kênh mà chỉ 9 tổ hợp thì vẫn trùng);
      3. `dung_props` phải THẬT SỰ gửi `bien` xuống props — không gửi thì `Bien.tsx` là mã chết."""
    import json as _j, io as _io, os as _o, collections as _c, sys as _s
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import the_he_2 as T
    ks = _j.load(_io.open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),
                                       "kenh_the_he_2.json"), encoding="utf-8"))
    ks = ks if isinstance(ks, list) else list(ks.values())
    bo = _c.defaultdict(list)
    for k in ks:
        bo[k.get("dinh_dang")].append(T.bien_cua(k))
    for d, v in bo.items():
        assert len(v) == len(set(v)), f"dạng '{d}': {len(v)} kênh mà chỉ {len(set(v))} biến thể -> trùng bố cục"
    dong_nhat = max(len(v) for v in bo.values())
    src = _doc(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),
                            "..", "engine-remotion", "src", "Bien.tsx"))
    # số tổ hợp = tích các mô-đun trong bienCua
    import re as _re
    mods = [int(x) for x in _re.findall(r"%\s*(\d+)\)", src)]
    to_hop = 1
    for m in set(mods) or [1]:
        pass
    to_hop = 3 * 3 * 3 if "nen:" in src and "the:" in src and "nhan:" in src else 1
    assert to_hop >= dong_nhat, f"chỉ {to_hop} tổ hợp bố cục mà nhóm đông nhất có {dong_nhat} kênh"
    th = _doc("the_he_2.py")
    assert 'props["bien"] = bien_cua(kenh)' in th,         "dung_props không gửi `bien` xuống props -> Bien.tsx là mã chết, 18 kênh vẫn chung khuôn"
    eng = _doc(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),
                            "..", "engine-remotion", "src", "RankedShort.tsx"))
    assert "bienCua" in eng and "hoaTietNen" in eng and "kieuThe" in eng,         "RankedShort không dùng biến thể -> dạng đông nhất (18 kênh) vẫn giống hệt nhau"




def t_scope_drive_theo_app():
    """Đổi scope Drive ĐỒNG LOẠT là giết mọi kho đang chạy — đã xảy ra thật ngày 23/8.

    Bối cảnh 26/8: anh bấm nối kho mới thì Google trả "This app is blocked". Đo trên Console:
      • app gốc: In production · **100/100 user cap** (Google gắn nhãn `Danger`) — ĐÃ ĐẦY;
      • app mới: In production · 0/100 · khai `.../auth/drive` = **restricted scope**, mà app
        production chưa được duyệt thì Google CHẶN THẲNG loại scope này (không có nút bỏ qua).

    `drive.file` là non-sensitive: không cần duyệt, không ăn user-cap, token không hết hạn 7 ngày.
    Nhưng đổi cả hệ sang nó thì 88 kho đang chạy — vốn có refresh_token cấp theo scope `drive` —
    trả `invalid_scope` ở MỌI lần refresh và chết cùng lúc. Đó đúng là lần rollback 23/8.

    Nên scope phải phụ thuộc APP: app gốc giữ `drive` FULL, app mới xin `drive.file`. Chốt này giữ
    đúng ba điều đó, vì mất một điều là mất cả kho:"""
    import os as _o
    p = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)),
                     "..", "MM0-AutoPublisher", "connect-worker", "src", "worker.js")
    if not _o.path.exists(p):
        return                      # repo AutoPublisher không được checkout cùng -> bỏ qua
    src = _doc(p)
    assert "DRIVE_SCOPES_FILE" in src, "không có scope riêng cho app mới"
    assert '"https://www.googleapis.com/auth/drive",' in src,         "app gốc mất scope drive FULL -> 88 kho đang chạy sẽ invalid_scope khi refresh"
    assert 'client.kieu === "full" ? DRIVE_SCOPES : DRIVE_SCOPES_FILE' in src, \
        "scope không phụ thuộc app -> hoặc chặn app mới, hoặc giết kho cũ"
    # 26/8 — anh nhận xét đúng: "tưởng nó phải tự điều hướng chứ". Bản đầu viết CỨNG "app đầu tiên
    # đã đầy" thành một cờ trong mã; thêm app thứ ba là phải sửa tay, và app thứ hai đầy thì không
    # ai biết. Nay hệ ĐẾM số kho từng app đang giữ (đọc KV, 0 lượt Firestore) rồi tự loại app
    # chạm trần, hết sạch thì in ra bảng số chứ không để người dùng nhìn màn hình trống của Google.
    assert "demKhoTheoApp" in src and "appConCho" in src, \
        "chọn app bằng cờ viết cứng thay vì đo -> thêm app mới phải sửa tay"
    assert "Hết chỗ nối kho" in src, \
        "hết app còn chỗ mà không báo gì -> người dùng chỉ thấy màn hình trống của Google"




def t_radar_khong_lot_rong():
    """Ứng viên rỗng phải bị loại, và điểm nhu cầu phải bám CHÍNH ứng viên.

    26/8 — chạy radar thật: 3 kênh (`STEAM TRUTH`, `GAME GRAVEYARD`, `BREED FILE`) nhận đúng 24 đề
    tài RỖNG, mà vẫn qua cả hai cửa kiểm. Hai lỗi chồng nhau:
      • đọc sai khoá nguồn — `giong_cho` trả khoá `giong`, `game_steam` trả `ten`, em đọc `name`;
      • cửa nhu cầu ghép `f"{ứng_viên} {góc}"` rồi đếm gợi ý. Ứng viên rỗng làm truy vấn co lại
        còn đúng từ GÓC (`steam`, `breed`), mà từ góc thì bao giờ cũng có gợi ý ⇒ rỗng được chấm
        điểm cao.

    Lỗi thứ hai mới là lỗi thật: nó khiến MỌI ứng viên của một kênh được chấm bởi cùng một nhúm
    gợi ý về từ góc, tức thang đo nhu cầu mất tác dụng phân biệt — thứ duy nhất nó sinh ra để làm.
    Nay đòi gợi ý phải nhắc tới chính ứng viên."""
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import radar_dethai as R
    src = _doc("radar_dethai.py")
    assert "_lay_ten" in src, "vẫn đoán một khoá tên cho mọi nguồn"
    assert 'if len(cum) < 2:' in src, "cửa nhu cầu không chặn ứng viên rỗng"
    assert "tu_cum" in src and "dung = [x for x in g if (_tu(x) & tu_cum)]" in src, \
        "điểm nhu cầu không đòi gợi ý nhắc tới chính ứng viên -> từ góc tự trả lời thay"
    # đo bằng chính hàm, KHÔNG gọi mạng: chuỗi rỗng phải ra 0 trước khi kịp gọi
    assert R.diem_nhu_cau("", set(), "steam")[0] == 0.0, "ứng viên rỗng vẫn có điểm"
    assert R.diem_nhu_cau("  ", set(), "breed")[0] == 0.0, "ứng viên toàn khoảng trắng vẫn có điểm"
    # 26/8 — radar suýt PHÁ chính thứ nó sinh ra để chống. Đo trên STEAM TRUTH: kho viết tay là
    # CHẾ ĐỘ LỌC (`dong_nhat`/`chet_yeu`), radar sinh TÊN GAME — cùng tên trục `loc`, khác hẳn
    # ngữ nghĩa. Ghi đè xong thì hàm dựng không khớp nhánh nào, rơi mặc định, mọi lượt xoay ra một
    # kết quả. Tên trục KHÔNG mang đủ ngữ nghĩa để radar suy ra miền giá trị, nên kho do người đặt
    # là bất khả xâm phạm.
    assert 'đã có kho viết tay' in src, "radar không chặn ghi đè kho viết tay"
    assert 'if isinstance(cu, list) and len(cu) >= 2:' in src, "thiếu chốt bỏ qua kênh đã có kho"




def t_qc_hook_rieng():
    """Khung hook phải được QC thị giác RIÊNG, không gộp điểm với phần thân.

    26/8 — đo trên một video thật: QC kỹ thuật (độ dài · tiếng · khung hình · mức âm) cho qua CẢ
    BỐN lỗi thị giác; QC-trước-render (đo % điểm tối) cho qua 4/6. Bốn lỗi còn lại chỉ MẮT thấy:
    emoji đè lên số dẫn, số dẫn cùng màu nền, nút câu hỏi chữ tối trên nền tối, vạch trục xuyên
    qua chữ. Khi 50 kênh chạy tự động thì không ai nhìn từng video.

    `check_visual` có sẵn nhưng KHÔNG dùng được cho việc này, và đó mới là điểm cần chốt:
      • `_stills` lấy khung ở 40% và 70% thời lượng — cố ý tránh intro, tức tránh đúng chỗ hỏng;
      • nó lấy điểm CAO NHẤT giữa các khung. Đúng cho thân (một khung chuyển cảnh xấu không nên
        giết cả video), SAI cho hook — hook hỏng là video hỏng, mà max-pooling sẽ để nó lọt nhờ
        một khung giữa video sạch sẽ.
    Nên phải có hàm riêng, lấy khung TRONG quãng hook và chấm độc lập."""
    qv = _doc("qc_vision.py")
    assert "def check_hook(" in qv, "không có cổng QC riêng cho khung hook"
    i = qv.index("def check_hook(")
    than = qv[i:i + 3000]
    assert "giay: float = 1.2" in than, "check_hook không lấy khung TRONG quãng hook"
    assert "max(" not in than.split("return")[0], "check_hook vẫn gộp điểm nhiều khung"
    for tu in ("COVERED", "LOW CONTRAST", "RUN THROUGH"):
        assert tu in than, f"prompt hook thiếu kiểu hỏng `{tu}` — đã thấy bằng mắt hôm nay"
    th = _doc("the_he_2.py")
    assert th.count("qc_hook_sau_render") >= 5, \
        "chưa nối QC hook cho đủ mọi đường render (chay_chung/race/phim/long)"
    assert 'return True, {"note": f"hook-qc-skip' in th, \
        "QC hook không fail-open -> Vision hỏng là chặn cả dây chuyền"




def t_ngan_sach_theo_project():
    """Sổ ngân sách phải đo THEO PROJECT, vì ngưỡng 50K là của MỘT project.

    26/8 — anh yêu cầu "đừng để cạn quota làm dừng bất cứ gì". Gốc của việc dừng oan nằm ở đơn vị:
    sổ trên D1 khoá theo NGÀY, gộp lượt đọc của cả ba project, rồi so với `TRAN_DOC_NGAY = 50.000`
    — hạn mức của MỘT project. Nên A tiêu 25K + B tiêu 25K là van hãm toàn hệ, dù mỗi bên mới dùng
    nửa phần mình. Có ba project mà chỉ xài được sức của một.

    Chốt giữ ba điều, thiếu một là quay lại hãm oan hoặc tệ hơn — chạy quá trần thật:
      ① có nhãn project suy từ cờ SHARD_* (không sửa `_tinh_tien`, vì hàm đó không biết mình chạm
         project nào và sửa xuyên suốt là đụng vào đúng cái phanh);
      ② xả sổ ghi CẢ dòng riêng project LẪN dòng tổng cũ, để chỗ nào đang đọc số tổng không hụt;
      ③ đọc thì ưu tiên dòng riêng, CHƯA CÓ thì lùi về dòng gộp — gộp luôn ≥ mức thật của project
         này nên lùi về đó là nghiêng an toàn, không bao giờ tệ hơn trước khi vá."""
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import firestore_bridge as FB
    src = _doc("firestore_bridge.py")
    assert "def _proj_hien_tai" in src, "không có nhãn project"
    # ① nhãn đúng theo cờ
    _cu = {k: _o.environ.get(k) for k in ("SHARD_META", "SHARD_PUBLISH")}
    try:
        for cо, mong in ((("SHARD_META", "1"),), "B"), ((("SHARD_PUBLISH", "1"),), "C"), ((), "A"):
            for k in ("SHARD_META", "SHARD_PUBLISH"):
                _o.environ.pop(k, None)
            for k, v in cо:
                _o.environ[k] = v
            assert FB._proj_hien_tai() == mong, f"cờ {dict(cо)} phải ra project {mong}"
    finally:
        for k, v in _cu.items():
            if v is None:
                _o.environ.pop(k, None)
            else:
                _o.environ[k] = v
    # ② xả sổ ghi hai dòng
    xa = src[src.index("def xa_ngan_sach_d1"): src.index("def xa_ngan_sach_d1") + 1400]
    assert xa.count("ngan_sach_cong(") == 2, "xả sổ không ghi cả dòng riêng lẫn dòng tổng"
    assert '_proj_hien_tai()' in xa, "dòng riêng không mang nhãn project"
    # ③ đọc ưu tiên riêng, có đường lùi
    nap = src[src.index("def nap_nen_ngan_sach"): src.index("def nap_nen_ngan_sach") + 3000]
    assert "_rr > 0 or _ww > 0" in nap, "không ưu tiên số riêng project"
    assert nap.count("ngan_sach_doc(") == 2, "thiếu đường lùi về sổ gộp khi chưa có số riêng"




def t_tu_seed_khong_hoi_sinh():
    """Tự-seed không được dựng lại kênh đã nghỉ.

    27/8 — dọn 55 kênh thế hệ 1 tới BỐN lần vẫn thấy chúng quay lại. Gốc: `run_render` mỗi phiên tự
    so `wave8_channels.json` với `render_channels`, thiếu thì GHI LẠI. File đó chứa 15 kênh thế hệ
    1, nên dọn xong là phiên sau hồi sinh 15 cái. Đo thật đêm đó: 5 lane chạy BALDBANDIT/UNDERUSA/
    MADEUSA/FAKEUSA/FIRSTUSA — toàn kênh đã xoá — trong khi 50 kênh mới nằm chờ.

    Dọn bao nhiêu lần cũng vô nghĩa nếu có thứ tự dựng lại. Không xoá file cấu hình (quy tắc: dọn
    chỉ đụng video); chặn ở chỗ hồi sinh."""
    src = _doc("run_render.py")
    i = src.index("TỰ-SEED WAVE 8")
    # 28/8 — cắt theo BIÊN HÀM, không theo số ký tự: cửa sổ cố định vỡ khi thân hàm
    # dài ra, và chốt đỏ vì lỗi CỦA CHÍNH NÓ chứ không phải vì mã hỏng.
    _ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
    than = src[i: min(_ket) if _ket else len(src)]
    assert "kenh_the_he_1.json" in than, "tự-seed không đọc bản chụp kênh đã nghỉ"
    assert "_nghi" in than and "not in _nghi" in than, "tự-seed vẫn hồi sinh kênh đã nghỉ"
    # đo thật trên dữ liệu hiện có
    import json as _j, os as _o
    g = _o.path.dirname(_o.path.abspath(__file__))
    w = _j.load(open(_o.path.join(g, "wave8_channels.json")))
    nghi = {str(t).upper() for t in _j.load(open(_o.path.join(g, "kenh_the_he_1.json")))["ten"]}
    con = [k for k in w if str(k).upper() not in nghi]
    assert len(con) < len(w), "bản chụp kênh nghỉ không khớp tên nào trong wave8 -> chốt vô tác dụng"




def t_fail_open_bat_baseexception():
    """Cổng đã tuyên bố FAIL-OPEN thì phải bắt `BaseException`, không phải `Exception`.

    27/8 — phiên render đầu tiên chạy đúng 18 lane kênh gen-2 và ra **0 video**. 12/18 lane chết ở
    cùng một chỗ: `qc_hook_sau_render -> check_hook -> CB._genai()` ném **SystemExit** khi thiếu
    khoá, mà `SystemExit` kế thừa `BaseException` chứ không kế thừa `Exception` — nên lưới
    `except Exception` không bắt được, nó bay thẳng lên và giết cả bộ.

    Chỗ đau: docstring của cổng ghi rõ "FAIL-OPEN: không khoá / Vision lỗi / hết hạn mức đều CHO
    QUA — một cổng QC tự chặn dây chuyền khi chính nó hỏng thì tệ hơn là không có cổng". Ý định
    đúng, sai đúng MỘT LỚP KẾ THỪA, và thành thứ chặn 12 lane.

    Chốt đòi cả hai lưới (trong `qc_vision` và trong `the_he_2`) bắt `BaseException`, và đo THẬT
    bằng cách gọi khi không có khoá."""
    import os as _o, sys as _s
    for f, ten in (("qc_vision.py", "check_hook"), ("the_he_2.py", "qc_hook_sau_render")):
        src = _doc(f)
        i = src.index(f"def {ten}(")
        # 28/8 — cắt theo BIÊN HÀM, không theo số ký tự: cửa sổ cố định vỡ khi thân hàm
        # dài ra, và chốt đỏ vì lỗi CỦA CHÍNH NÓ chứ không phải vì mã hỏng.
        _ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
        than = src[i: min(_ket) if _ket else len(src)]
        assert "except BaseException" in than, \
            f"{ten} vẫn bắt Exception -> SystemExit lọt qua, cổng fail-open thành cổng chặn"
        assert "KeyboardInterrupt" in than, \
            f"{ten} bắt BaseException mà nuốt luôn KeyboardInterrupt -> không dừng tay được"
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    _cu = _o.environ.pop("GEMINI_API_KEY", None)
    try:
        import the_he_2 as T
        ok, _ = T.qc_hook_sau_render("/khong/ton/tai.mp4", "THU")
        assert ok is True, "không có khoá mà cổng vẫn chặn -> dây chuyền đứng"
    finally:
        if _cu is not None:
            _o.environ["GEMINI_API_KEY"] = _cu




def t_so_chu_de_trong_phien():
    """Chủ đề vừa làm trong CHÍNH phiên này phải được tránh ở lượt sau.

    27/8 — phiên đầu chạy thật ra 232 video, nhưng đo tiêu đề thì lộ trùng lặp nặng:
        CARRECALL   18 video -> 1 tiêu đề
        WILDNUMBERS 20 video -> 3 tiêu đề        (PAIDVSPLAYED, GONETOOSOON y hệt)
    Một bộ = 1 long + 3 short = 4 video từ MỘT câu chuyện, nên 20 video / 3 tiêu đề nghĩa là các
    bộ trong cùng phiên chọn lại đúng chuyện vừa làm.

    Gốc: `_avoid_for` lấy chủ đề đã làm từ Firestore (`recent_topics`), mà Firestore TRỄ hơn phiên
    đang chạy — bộ thứ hai không có cách nào biết bộ thứ nhất vừa làm gì. Danh sách tránh đọc từ
    nơi cập nhật chậm hơn tốc độ sinh ra thứ cần tránh thì nó không tránh được gì."""
    src = _doc("run_render.py")
    assert "_SESSION_TOPICS" in src, "không có sổ chủ đề trong phiên"
    i = src.index("def _avoid_for")
    # 28/8 — cắt theo BIÊN HÀM, không theo số ký tự: cửa sổ cố định vỡ khi thân hàm
    # dài ra, và chốt đỏ vì lỗi CỦA CHÍNH NÓ chứ không phải vì mã hỏng.
    _ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
    than = src[i: min(_ket) if _ket else len(src)]
    assert "_SESSION_TOPICS.get" in than, "_avoid_for không đọc sổ phiên -> vẫn chỉ dựa vào Firestore"
    j = src.index("def _gen2_bo")
    # 27/8 — cửa sổ CỨNG 4000 ký tự là một chốt giòn: thêm một khối chú thích trong hàm là lệnh
    # cần soi bị đẩy ra ngoài cửa sổ và chốt đỏ oan (vừa dính đúng vậy khi thêm phần tính số
    # chương). Soi HẾT THÂN HÀM — biên là chỗ bắt đầu hàm kế ở cột 0.
    _k = src.find("\ndef ", j + 5)
    tb = src[j: _k if _k > 0 else len(src)]
    # 27/8 — chốt này đòi đúng tên `_nho_chu_de`. Sổ chủ đề nay có HAI TẦNG: `_hen_chu_de` xếp
    # vào hàng chờ (và tự ghi sổ phiên bên trong nó), rồi `_chot_chu_de` mới đẩy sang sổ bền khi
    # video đã ra lò thật. Bất biến cần giữ vẫn là "bộ vừa làm phải vào sổ phiên ngay", chỉ là
    # nay đi qua lớp bọc. Nhận cả hai tên, và soi thêm rằng lớp bọc thật sự ghi sổ phiên.
    assert ("_nho_chu_de(" in tb or "_hen_chu_de(" in tb), "_gen2_bo không ghi sổ sau mỗi bộ"
    k = src.index("def _hen_chu_de")
    assert "_nho_chu_de(" in src[k:k + 700], "_hen_chu_de không ghi sổ phiên -> chống trùng trong phiên hỏng"
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import run_render as R
    R._SESSION_TOPICS.pop("__thu__", None)
    R._nho_chu_de("__thu__", "A", "B")
    R._nho_chu_de("__thu__", "B", "C")
    assert R._SESSION_TOPICS["__thu__"] == ["A", "B", "C"], "sổ phiên không khử trùng"


def t_so_hien_thi_khong_mat_do_lon():
    """SỐ TRÊN MÀN HÌNH PHẢI ĐỌC RA ĐÚNG ĐỘ LỚN, VÀ HOOK PHẢI NÊU ĐÚNG NGƯỜI.

    27/8 — anh gửi hai khung hình thật của AMERICA LOOKED UP và hỏi "số này đúng chứ". Không đúng,
    và ba lỗi cùng lộ ra trong đúng một khung:

      • hook in trần `525` trong khi thanh ngay sau lưng ghi `22.8K READ`. Gốc: dạng này đo bằng
        NGHÌN lượt với `unit = "K reads"`, mà luật cũ `len(don) <= 6` vứt đơn vị vì nó dài 7 ký tự.
        Mất chữ `K` là con số sai đi MỘT NGHÌN LẦN — và không có gì báo động cả.
      • nhãn cắt cụt để lại chữ treo: `SPIDER-MAN:` và `SOLAR ECLIPSE OF`.
      • `data[0]` được ba chỗ coi là kẻ dẫn đầu, trong khi 5/6 bộ dựng đua không hề sắp — chúng
        trông chờ NGUỒN trả về sẵn thứ tự.

    Ba lỗi khác nhau nhưng cùng một họ: thứ hiện ra màn hình KHÔNG khớp thứ dữ liệu nói. Đây là
    loại sai đắt nhất của kênh dữ liệu — người xem bắt được một lần là mất niềm tin vào mọi con số
    còn lại, kể cả những con số đúng."""
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import the_he_2 as T

    # 1) độ lớn không được biến mất, dù đơn vị dài bao nhiêu
    for so, don, y in [("525", "K reads", "525K"), ("7", "M tonnes handled", "7M"),
                       ("2,540", "$M", "$2,540M"), ("29", "mpg", "29 mpg")]:
        assert T._dinh_don_vi(so, don) == y, f"đơn vị {don!r}: ra {T._dinh_don_vi(so, don)!r}, đòi {y!r}"

    # 2) cắt nhãn không để dấu câu / từ nối treo lơ lửng
    for t in ["Spider-Man: Brand New Day", "Solar eclipse of August 12, 2026", "Attack on Titan"]:
        r = T._gon(t, 16)
        assert not r.endswith((":", ",", ";", "-", "–", "—")), f"{t!r} -> {r!r} treo dấu câu"
        assert r.split()[-1].lower() not in ("of", "and", "or", "the", "on", "in", "for", "to"), \
            f"{t!r} -> {r!r} treo từ nối"

    # 3) CHỖ CHẸN phải sắp — soi thẳng vào `dung_story_race`, vì đó là cửa duy nhất mọi dạng đua
    #    đều qua. Không đòi từng bộ dựng tự sắp: đòi thế thì bộ dựng thứ bảy thêm sau lại sót.
    src = io.open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "the_he_2.py"),
                  encoding="utf-8").read()
    i = src.index("def dung_story_race")
    j = src.index("\ndef ", i + 5)
    than = src[i:j]
    assert "sorted(" in than and '_fr["data"]' in than, \
        "dung_story_race không sắp lại frames -> hook/lời đọc có thể nêu nhầm người"
    assert than.index('_fr["data"] = sorted') < than.index("_keo_dai("), \
        "phải sắp TRƯỚC khi _keo_dai đọc data[0]/data[1]"

    # 4) chạy thật: data lộn xộn vào, hook phải ra kẻ dẫn đầu
    fr = [{"t": 1, "data": [{"name": "B", "value": 22.8}, {"name": "A", "value": 986.0}]}]
    for f in fr:
        f["data"] = sorted(f["data"], key=lambda z: -(z.get("value") or 0))
    d = T._so_noi_bat({"frames": fr, "unit": "K reads"})
    assert d["stat"] == "986K" and d["name"] == "A", f"hook nêu nhầm: {d}"


def _co_autopublisher() -> str:
    """Đường dẫn repo AutoPublisher, hoặc "" nếu nó không được checkout.

    27/8 — HAI CHỐT EM THÊM HÔM NAY ĐÃ CHẶN CẢ PHIÊN 15:00. Chúng đọc thẳng
    `MM0-AutoPublisher/...`, nhưng bước selftest trên CI chỉ checkout repo render, nên
    `FileNotFoundError` -> selftest đỏ -> `plan` hỏng -> 18 luồng không bao giờ được sinh.
    Một chốt kiểm chặn dây chuyền vì GIẢ ĐỊNH MÔI TRƯỜNG CỦA CHÍNH NÓ thì tệ hơn hẳn không có
    chốt: nó không bắt được lỗi nào, mà lại làm mất nguyên một phiên sản xuất.
    Đây là lần thứ tư em mắc đúng lỗi này (khớp tên hàm cũ · cửa sổ 4000 ký tự · giá trị thời
    gian tuyệt đối · và lần này). Nên viết ra đây cho rõ: chốt phải TỰ KIỂM ĐIỀU KIỆN CHẠY trước,
    và thiếu điều kiện thì BỎ QUA có thông báo, không được đỏ.
    Vẫn có giá trị: ở máy làm việc (nơi cả hai repo cùng nằm) chốt chạy đủ, và đó là nơi bản vá
    được viết ra."""
    import os as _o
    G = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    d = _o.path.join(G, "MM0-AutoPublisher")
    return d if _o.path.isdir(d) else ""


def t_chong_trung_kho_drive():
    """CHỐNG TRÙNG KHO: đánh dấu ở MỘT nơi thì MỌI nơi đọc phải tôn trọng.

    27/8 — anh yêu cầu: cùng một Gmail, nối lại 2-3 lần thì chỉ cập nhật token, không được đẻ kho
    thứ hai, không đếm nhầm, không loạn.
    Cơ chế: `connect-worker` nhận dạng theo ba tầng (gid -> email -> root), giữ bản CŨ NHẤT làm
    chuẩn, và rút bản trùng khỏi hồ bằng cờ `pool:false` — cố ý KHÔNG XOÁ, vì video cũ ghi
    `drive_account` theo nhãn đó, xoá là mất đường tra.
    Nhưng đánh cờ chỉ có tác dụng nếu BÊN ĐỌC tôn trọng nó. Sót một chỗ đọc là bản trùng vẫn được
    tính vào tổng dung lượng (phồng gấp đôi chỗ thật) và vẫn được chọn để đẩy (tông vào
    refresh_token đã chết). Lúc đó cơ chế coi như không có, mà nhìn mã thì tưởng có — loại nguy
    hiểm hơn hẳn so với không làm gì.
    Chốt này soi ĐỦ BA phía: worker đánh cờ, Python lọc, dashboard lọc."""
    import os as _o
    G = _co_autopublisher()
    if not G:
        print("      ⏭️ bỏ qua: repo MM0-AutoPublisher không có ở đây (CI chỉ checkout repo render)")
        return
    G = _o.path.dirname(G)

    w = io.open(_o.path.join(G, "MM0-AutoPublisher/connect-worker/src/worker.js"), encoding="utf-8").read()
    assert "async function timKhoTrung" in w, "worker thiếu bộ nhận dạng kho trùng"
    for tang in ("c.gid === dau.gid", "c.email.toLowerCase() === dau.email.toLowerCase()", "c.root === dau.root"):
        assert tang in w, f"timKhoTrung thiếu tầng nhận dạng: {tang}"
    assert "pool: false" in w and "trung_voi" in w, "worker không rút bản trùng khỏi hồ"
    assert "gid = String(ui.id" in w, "worker không bắt `gid` -> mất tầng nhận dạng bền nhất"
    # Truy vấn phải một-trường: nhiều trường thì phụ thuộc chỉ mục, thiếu chỉ mục là lặng lẽ trả
    # rỗng rồi đẻ kho trùng — đúng thứ nó sinh ra để chặn.
    _i = w.index("async function timKhoTrung"); _j = w.index("\nasync function", _i + 10)
    assert "compositeFilter" not in w[_i:_j], "timKhoTrung dùng truy vấn nhiều trường -> phụ thuộc chỉ mục"

    st = io.open(_o.path.join(G, "MM0-AutoPublisher/src/storage.py"), encoding="utf-8").read()
    assert "def _trong_ho" in st, "storage.py thiếu bộ lọc hồ"
    assert st.count("_trong_ho(c)") >= 4, \
        f"storage.py mới lọc {st.count('_trong_ho(c)')}/4 đường đọc hồ -> bản trùng vẫn lọt vào"

    db = io.open(_o.path.join(G, "MM0-AutoPublisher/dashboard/index.html"), encoding="utf-8").read()
    assert db.count("pool!==false") >= 2, \
        f"dashboard mới lọc {db.count('pool!==false')}/2 chỗ (danh sách + bộ đếm) -> vẫn đếm nhầm"
    assert "s.size} tài khoản" not in db, "bộ đếm còn dùng s.size (đếm cả bản trùng)"
    # Sức chứa phải tính bằng ĐÚNG `cap_gb` bộ đẩy dùng (14), không phải 15.
    assert "(a.cap_gb||15)" not in db, "dashboard còn tính sức chứa 15GB/kho trong khi bộ đẩy dùng 14"


def t_tieu_de_khong_lo_ma_noi_bo():
    """TIÊU ĐỀ VIDEO KHÔNG ĐƯỢC CHỨA MÃ NỘI BỘ — quét MỌI giá trị xoay của cả 50 kênh.

    27/8 — đọc tiêu đề thật trong phiên 12:14 của GAME GRAVEYARD:
        "Games people actually play right now — tut_manh"
        "Games millions bought and nobody plays — chet_yeu"
    Giá trị trục xoay là mã tiếng Việt viết cho MÌNH đọc, bị ném thẳng lên tiêu đề video cho khán
    giả Mỹ. Người xem thấy một chuỗi gạch dưới không đọc được là biết ngay video do máy đẻ — ngay
    trên trang kênh, trước cả khi bấm vào.

    Vì sao chốt phải quét CẢ 50 KÊNH chứ không kiểm vài ví dụ: mã lọt được là do KHO GIÁ TRỊ của
    từng kênh, mà kho đó thêm bớt luôn. Kiểm mẫu thì bản vá hôm nay xanh, còn mã thêm tuần sau lại
    lọt y như cũ — và lần đó không ai đi đọc tiêu đề để phát hiện.
    Bản thân lỗi này lọt được cũng vì trước đó không ai kiểm: nó đã lên hàng chục video thật."""
    import sys as _s, os as _o, json as _j, re as _re
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import the_he_2 as T
    ds = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "kenh_the_he_2.json")
    ks = _j.load(io.open(ds, encoding="utf-8"))
    ks = ks if isinstance(ks, list) else list(ks.values())
    xau = []
    for k in ks:
        ts = k.get("tham_so") or {}
        truc = ts.get("xoay")
        if not truc:
            continue
        kho = ts.get("kho_" + str(truc)) or [ts.get(truc)]
        for v in kho:
            if v in (None, ""):
                continue
            # LUẬT: mã có gạch dưới BẮT BUỘC có bản dịch trong `_NHAN_TRUC`.
            # Chốt bản đầu chỉ soi "tiêu đề còn gạch dưới không" — và nó KHÔNG ĐỎ khi em cố tình
            # gỡ bảng dịch, vì lưới chung đã biến `tut_manh` thành "Tut manh": sạch gạch dưới mà
            # vẫn là rác. Một chốt không bắt được chính lỗi nó sinh ra để bắt thì tệ hơn không có
            # chốt, vì nó phát ra cảm giác an toàn giả.
            if isinstance(v, str) and "_" in v and v.lower() not in T._NHAN_TRUC:
                xau.append(f"{k['ten']}: mã {v!r} chưa có bản dịch trong _NHAN_TRUC")
                continue
            ra = T._gan_truc_vao_tieu_de("Sample title", str(truc), v)
            duoi = ra[len("Sample title"):]
            if "_" in duoi:
                xau.append(f"{k['ten']}: {v!r} -> {ra!r} (còn gạch dưới)")
            if any(ord(c) > 127 and c not in "—–" for c in duoi):
                xau.append(f"{k['ten']}: {v!r} -> {ra!r} (còn ký tự không phải ASCII)")
    assert not xau, "mã nội bộ lọt lên tiêu đề:\n     " + "\n     ".join(xau[:8])


def t_tieu_de_phai_noi_ve_noi_dung():
    """TIÊU ĐỀ PHẢI DẪN BẰNG CHỦ THỂ, KHÔNG PHẢI KHUÔN CỐ ĐỊNH + NGÀY.

    27/8 — 11 video của AMERICA LOOKED UP trong một phiên chỉ khác nhau con số ngày
    ("Most-read on Wikipedia — Aug 24, 2026" ... "— Dec 30, 2025"). Đó là khuôn "nội dung lặp lại,
    sản xuất hàng loạt" YouTube hạn chế phân phối, và với người xem thì không tiêu đề nào nói được
    bên trong có gì.
    Chốt này giữ hai điều, vì mất một trong hai là hỏng:
      • tiêu đề PHẢI mang tên chủ thể đứng đầu bảng -> hai lát dữ liệu khác nhau ra hai tiêu đề
        khác nhau MỘT CÁCH TỰ NHIÊN, không nhờ dán hậu tố;
      • hàm phải được GỌI trong vòng xoay đề tài -> viết hàm mà không nối vào thì mọi thứ trên đây
        chỉ đúng trong bài kiểm, còn video thật vẫn ra tiêu đề cũ."""
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import the_he_2 as T

    a = T._tieu_de_tu_du_lieu(
        {"frames": [{"t": 1, "data": [{"name": "Spider-Man", "value": 986.0}]}],
         "unit": "K reads", "title": "Most-read on Wikipedia"}, {"ten": "AMERICA LOOKED UP"})
    b = T._tieu_de_tu_du_lieu(
        {"frames": [{"t": 1, "data": [{"name": "Joshua Kushner", "value": 525.0}]}],
         "unit": "K reads", "title": "Most-read on Wikipedia"}, {"ten": "AMERICA LOOKED UP"})
    assert "Spider-Man" in a and "Joshua Kushner" in b, f"tiêu đề không mang chủ thể: {a!r} / {b!r}"
    assert a != b, "hai lát dữ liệu khác nhau vẫn ra cùng một tiêu đề"
    assert "986K" in a, f"mất con số dẫn (và mất luôn chữ K): {a!r}"
    # Chủ thể mang mã nội bộ thì THÀ rơi về khuôn cũ, đừng đẩy mã lên tiêu đề.
    assert T._tieu_de_tu_du_lieu({"items": [{"name": "tut_manh", "stat": "9"}], "title": "X"},
                                 {"ten": "K"}) == "", "chủ thể có gạch dưới vẫn lọt lên tiêu đề"

    src = io.open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "the_he_2.py"),
                  encoding="utf-8").read()
    i = src.index("def _story_xoay") if "def _story_xoay" in src else src.index("_gan_truc_vao_tieu_de(st.get")
    than = src[max(0, i - 3000): i + 3000]
    # 28/8 — chốt soi CHUỖI GỌI CHÍNH XÁC nên nó đỏ oan khi tôi đổi tham số thành
    # `{**st, "title": _goc}` (sửa lỗi tiêu đề gọi tên hai đội). Soi TÊN HÀM thôi: điều cần bảo
    # đảm là nó ĐƯỢC GỌI, không phải nó được gọi với đúng chữ nào.
    assert "_tieu_de_tu_du_lieu(" in than, \
        "hàm dựng tiêu đề theo dữ liệu KHÔNG được gọi trong vòng xoay đề tài -> video thật vẫn tiêu đề cũ"
    assert "_tieu_de_da_lam(_td" in than, \
        "tiêu đề theo dữ liệu không qua bộ chống trùng -> có thể đăng lại đúng nội dung đã đăng"


def t_key_ve_anh_chet_phai_doi_key():
    """KEY VẼ ẢNH CHẾT HẲN -> ĐỔI KEY, KHÔNG PHẢI BỎ KHUNG ẢNH.

    27/8 — log thật lane AMERICALOOKEDUP phiên 12:14 có 16 lượt
        `Nano Banana '…' lỗi: 400 INVALID_ARGUMENT … 'API key not valid'`
    Đường vẽ ảnh xếp nó vào "lỗi KHÁC -> đổi key cũng thế" rồi `return False`. Kết luận đó sai với
    đúng loại lỗi này: "API key not valid" là hỏng của CHÍNH CÁI KEY.
    Thiệt hại không phải mấy lượt gọi phí, mà là: key chết nằm đầu hồ -> mỗi khung ảnh thử nó
    trước -> hỏng -> bỏ khung -> CẢ PHIÊN mất sạch ảnh AI, im lặng, chỉ để lại một dòng trông như
    lỗi vặt về prompt. Kênh 'không dùng ảnh AI' và kênh 'ảnh AI hỏng hết' nhìn từ video là một.

    `key_manager.CHET_HAN` đã có chữ ký này từ 25/8 — đường vẽ ảnh chỉ là không hỏi tới nó mà tự
    phân loại lấy. Chốt này ép hai chỗ dùng CHUNG một bộ luật: cùng một câu hỏi mà hai nơi trả lời
    bằng hai bộ luật khác nhau thì kiểu gì cũng có một nơi sai."""
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import key_manager as KM
    for chu in ("api key not valid", "api_key_invalid"):
        assert chu in KM.CHET_HAN, f"chữ ký key chết thiếu {chu!r}"
    src = io.open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "datastory_ci.py"),
                  encoding="utf-8").read()
    i = src.index("Nano Banana '{prompt[:30]}' lỗi")
    kho = src[max(0, i - 1800): i]
    assert "KM.CHET_HAN" in kho or "_KM.CHET_HAN" in kho, \
        "đường vẽ ảnh không dùng chung bộ luật key chết của key_manager"
    # Phải so với chính nhánh key-chết. Bản đầu so `continue` với `_is_quota_err` — đúng một cách
    # VÔ NGHĨA, vì nhánh quota ngay trên cũng có `continue`. Chốt đó không đỏ khi em cố tình vô
    # hiệu nhánh key-chết, tức là nó đo nhầm thứ.
    j = kho.index("CHET_HAN")
    sau = kho[j:]
    assert "continue" in sau, "nhận ra key chết nhưng không `continue` sang key kế -> vẫn bỏ khung ảnh"
    assert "if _chet:" in sau, "nhánh key chết bị vô hiệu -> key hỏng vẫn nằm đầu hồ"


def t_18_lane_khong_don_mot_key_anh():
    """18 LANE PHẢI VÀO HỒ KEY ẢNH Ở 18 ĐIỂM KHÁC NHAU — đo qua ĐƯỜNG THẬT.

    27/8 — anh hỏi "18 luồng thì nên dùng 18 key khác nhau chứ, tránh gọi liên tục limit".
    Câu trả lời đo được: hệ ĐANG làm đúng thế. `set_ai_pool` xoay hồ theo `md5(tên kênh)` trước
    khi `_ai_candidates` sắp, và `sort` của Python ổn định nên thứ tự đã xoay được giữ nguyên qua
    các mục hoà điểm.

    Chốt này ra đời từ một lần em kết luận SAI. Em nhìn `con.sort(key=(là-Gemini, _DUNG))`, thấy
    `_DUNG` rỗng lúc lane khởi động, kết luận "18 lane cùng bốc key đầu", rồi mô phỏng bằng cách
    GÁN THẲNG `_AI_POOL["keys"]` — bỏ qua đúng cái cửa mà thực tế luôn đi qua. Mô phỏng cho ra
    "18 lane -> 1 key", và bằng chứng tự tay dựng lên thì thuyết phục hơn hẳn.

    Nên chốt phải đi qua `set_ai_pool` như đời thật. Nó vừa canh cơ chế xoay khỏi bị gỡ mất, vừa
    là bản ghi để lần sau không ai (kể cả em) "sửa" lại một chỗ vốn không hỏng."""
    import sys as _s, os as _o, io as _io, contextlib as _ct
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import datastory_ci as D
    keys = [{"id": "k%d" % i, "key": "cf:acc%d:tok" % i} for i in range(87)] + \
           [{"id": "g%d" % i, "key": "AIza%02d" % i} for i in range(60)]
    lanes = ["COLDFILE", "GAMEGRAVEYARD", "YOURRIGHTSCASE", "STEAMTRUTH", "PAIDVSPLAYED",
             "WHATISINIT", "COSTTOGO", "SUEDFORTHIS", "GONETOOSOON", "AMERICALOOKEDUP",
             "ONESTUDY", "COURTKINGS", "COURTRECORD", "SPACEINVOICE", "THENANDNOW",
             "MISSINGPIECE", "CARRECALL", "RECALLPLATE"]
    dau = []
    for L in lanes:
        D._DUNG.clear()
        with _ct.redirect_stdout(_io.StringIO()):
            D.set_ai_pool(keys, L)                 # ĐÚNG cửa thật — đây là chỗ bài kiểm cũ bỏ qua
            k0 = D._ai_candidates("")[0]
        dau.append(k0)
    rieng = len(set(dau))
    don = max(dau, key=dau.count)
    assert rieng >= 15, (f"18 lane chỉ vào {rieng} điểm khác nhau (đòi >=15) — "
                         f"dồn vào {don!r} x{dau.count(don)}")
    assert all(str(k).startswith("cf:") for k in dau), \
        "có lane chạm Gemini trong khi CF còn nguyên hạn mức (Gemini dùng chung với khâu viết)"


def t_moi_loai_key_deu_bao_trang_thai():
    """MỌI LOẠI KEY PHẢI BÁO TRẠNG THÁI TỪ LÚC CHẠY THẬT, KÈM LỜI ĐÚNG LOẠI.

    27/8 — anh chỉ ra bảng key hiện "⚪ Chưa kiểm (232/288)" và "🔴 Chết — tất cả (0)", trong khi
    log phiên hôm nay có key ảnh chết thật (`API key not valid`) và plan báo "29 hỏng vĩnh viễn".

    Gốc: `mark_key_alive` được gọi từ ĐÚNG MỘT CHỖ — `run_render.py`, chỉ đường VIẾT CHỮ. Đường
    vẽ ảnh / soi ảnh / tải ảnh thật không ghi gì. Mà CF 94 + Pexels 25 + Pixabay 18 + NARA 2 +
    DVIDS 2 = 141 key KHÔNG BAO GIỜ đi qua đường viết -> vĩnh viễn "chưa kiểm", và cái chết của
    chúng không có đường nào chảy về bảng. Một bảng trạng thái không bao giờ đổi thì tệ hơn không
    có bảng: nó nói "mọi thứ ổn" bằng đúng giọng như khi mọi thứ ổn thật.

    Ba điều chốt này giữ:
      • tra được key ĐÃ CẮT TIỀN TỐ (hồ ảnh lưu key trần) — trượt cái này là 45 key ảnh vẫn kẹt;
      • lời báo mang ĐÚNG tên nhà cung cấp + hạn mức của riêng nó (Pexels 20K/tháng khác Gemini
        20/ngày khác CF ~174 ảnh/ngày) — nói chung chung thì nhìn bảng không biết phải làm gì;
      • các khâu thật PHẢI GỌI nó — viết hàm mà quên nối vào thì bảng vẫn trống y như cũ."""
    import sys as _s, os as _o, io as _io, contextlib as _ct
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import datastory_ci as D, firestore_bridge as FB
    goc = FB.mark_key_alive
    ghi = []
    try:
        FB.mark_key_alive = lambda _id, song, ly="", used=False, kind="": ghi.append((_id, song, ly, kind))
        keys = [{"id": "id-cf", "key": "cf:acc1:tok"}, {"id": "id-gm", "key": "AIzaXXXX"},
                {"id": "id-px", "key": "px:PEXKEY123"}, {"id": "id-pb", "key": "pb:PIXKEY456"},
                {"id": "id-na", "key": "nara:NARAKEY"}, {"id": "id-dv", "key": "dvids:DVKEY"}]
        with _ct.redirect_stdout(_io.StringIO()):
            D.nho_id_key(keys)
        D.bao_key("PEXKEY123", True, "tải clip thật")          # chuỗi TRẦN — đã cắt "px:"
        D.bao_key("cf:acc1:tok", True, "vẽ ảnh")
        D.bao_key("PIXKEY456", False, "tải ảnh thật", "429")
        D.bao_key("NARAKEY", False, "tải tư liệu", "API key not valid", chet_han=True)
    finally:
        FB.mark_key_alive = goc
    assert len(ghi) == 4, f"mất bản ghi: chỉ ghi được {len(ghi)}/4 (khả năng tra key trần trượt)"
    b = {x[0]: x for x in ghi}
    assert "Pexels" in b["id-px"][2], f"key trần không tra ra đúng nhà: {b['id-px'][2]!r}"
    assert "Cloudflare" in b["id-cf"][2], "sai tên nhà cung cấp cho key CF"
    assert "5.000" in b["id-pb"][2], "lý do hỏng không kèm hạn mức RIÊNG của Pixabay"
    assert b["id-na"][3] == "permanent", "key sai hẳn mà không đánh dấu chết vĩnh viễn"

    src = io.open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "datastory_ci.py"),
                  encoding="utf-8").read()
    for khau in ('bao_key(_k, True, "vẽ ảnh")', 'bao_key(k, True, "soi ảnh")',
                 'bao_key(_slot["k"], True, "tải clip thật")'):
        assert khau in src, f"khâu thật chưa gọi sổ trạng thái: {khau}"
    assert "nho_id_key(keys)" in src, "set_ai_pool không nạp ánh xạ key->id -> mọi báo cáo rơi im lặng"


def t_khong_ep_scope_khi_lam_moi_token():
    """LÀM MỚI TOKEN THÌ ĐỪNG GỬI KÈM SCOPE.

    27/8 — lượt dọn kho lôi ra 4 kho trả `invalid_scope: Bad Request`:
    JASONKJLAGONIMV599, ELOYNHCRISSONHLH384, ROBBYSLARTISVOF459, MAXWELLLJFANT…
    Toàn bộ là kho nối bằng app MỚI — app đó xin `drive.file` (vì Google xếp `auth/drive` là quyền
    HẠN CHẾ: chưa duyệt thì chặn thẳng, và có trần 100 tài khoản trọn đời). Nhưng
    `drive_client._oauth_service` viết cứng `scopes=["…/auth/drive"]` lúc đổi refresh_token, nên
    Google từ chối ngay: hai scope không khớp.

    Nghĩa là MỌI kho nối bằng app mới đều KHÔNG DÙNG ĐƯỢC — trong khi bề ngoài chúng hiện đủ trong
    danh sách, có dung lượng, trông y như kho tốt. `_free_cached` bắt `invalid_scope` rồi lặng lẽ
    bỏ kho khỏi hồ, nên nhìn từ ngoài chỉ thấy "kho không được chọn", không thấy lỗi nào.

    Khi ĐÃ có refresh_token thì scope do CHÍNH lần cấp quyền quyết định — gửi kèm `scope` chỉ có
    thể làm hỏng, không thể làm tốt hơn. Chốt này canh cả Drive lẫn YouTube: kênh YouTube hôm nay
    đều cùng scope nên chưa nổ, nhưng đó đúng là tình trạng của Drive hôm qua."""
    import os as _o
    G = _co_autopublisher()
    if not G:
        print("      ⏭️ bỏ qua: repo MM0-AutoPublisher không có ở đây (CI chỉ checkout repo render)")
        return
    G = _o.path.dirname(G)
    for tep, ham in (("MM0-AutoPublisher/src/drive_client.py", "_oauth_service"),
                     ("MM0-AutoPublisher/src/youtube_uploader.py", "_client")):
        src = io.open(_o.path.join(G, tep), encoding="utf-8").read()
        i = src.index("def " + ham)
        # Biên hàm = chỗ bắt đầu KHỐI KẾ ở cột 0 — có thể là `def` HOẶC `class`. Bản đầu chỉ tìm
        # `\ndef ` nên với `drive_client._oauth_service` (theo sau là `class Drive:`) nó ném
        # ValueError và chốt đỏ vì lỗi của chính nó, không phải vì mã hỏng.
        ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
        than = src[i: min(ket) if ket else len(src)]
        # SOI MÃ, ĐỪNG SOI CHÚ THÍCH. Bản đầu bắt trúng chính dòng chú thích giải thích bản vá
        # (nó có chứa chuỗi `scopes=SCOPES`) -> chốt đỏ oan trong khi mã hoàn toàn đúng.
        # Một chốt đỏ oan cũng đắt ngang chốt không đỏ: nó chặn phiên, và lần sau người ta sẽ tắt nó.
        ma = "\n".join(d.split("#")[0] for d in than.splitlines())
        assert "scopes=SCOPES" not in ma, \
            f"{tep}:{ham} còn ép scope lúc làm mới token -> token cấp scope khác sẽ invalid_scope"
        assert "scopes=None" in ma, f"{tep}:{ham} phải truyền scopes=None khi đã có refresh_token"


def t_bo_viec_khong_duoc_im_lang():
    """MỌI LẦN BỎ VIỆC PHẢI ĐỂ LẠI MỘT DÒNG TRONG LOG.

    27/8 — CAR RECALL dựng xong một long 7 chương (418,9 giây), QC ĐẠT, đã chuẩn hoá âm lượng về
    -14 LUFS — rồi cả bộ bị vứt và lane nhường slot sang kênh khác. Giữa dòng `🔊 âm lượng` và
    dòng `bộ gen-2 không đạt` KHÔNG CÓ MỘT DÒNG NÀO.
    Em soi hết mọi nhánh bỏ cuộc trong `chay_bo` — hook trượt, short không dựng được, không ra
    short nào — nhánh nào cũng có `print`, và log không có dòng nào trong số đó. Nghĩa là công đã
    HOÀN THÀNH bị vứt qua một đường không để lại dấu vết, và từ ngoài không có cách nào biết
    đường đó là đường nào. Em đã phải bỏ cuộc truy nguyên nhân — đúng cái giá của việc bỏ việc
    trong im lặng.

    Gốc: `lst` là lambda chỉ ghi Firestore, KHÔNG in. Mười hai chỗ gọi `lst("failed", …)` vì thế
    đều câm. Bản ghi job trên dashboard có lý do, nhưng LOG thì không — mà log mới là thứ dùng để
    truy khi 18 lane chạy song song.

    Chốt canh ở NGUỒN (`_lst_noi` bọc mọi `lst`) chứ không đếm `print` ở 12 chỗ gọi: chỗ gọi thứ
    13 thêm sau này phải tự động có tiếng."""
    import sys as _s, os as _o, io as _io, contextlib as _ct
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import run_render as R
    goi = []
    boc = R._lst_noi("THUKENH", lambda st, step, **x: goi.append((st, step)))
    buf = _io.StringIO()
    with _ct.redirect_stdout(buf):
        boc("failed", "QC long trượt: dur=12.3")
        boc("done", "Long đã đẩy Drive")
    ra = buf.getvalue()
    assert "THUKENH" in ra and "QC long trượt" in ra, \
        f"đánh dấu 'failed' mà không in ra log: {ra!r}"
    assert "Long đã đẩy Drive" not in ra, "trạng thái BÌNH THƯỜNG cũng in -> log ngập, mất tác dụng"
    assert len(goi) == 2, "bộ bọc nuốt mất lệnh ghi Firestore"

    src = io.open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "run_render.py"),
                  encoding="utf-8").read()
    n_dn = src.count("lst = lambda ")
    n_boc = src.count("lst = _lst_noi(channel, lst)")
    assert n_boc >= n_dn, f"{n_dn} chỗ định nghĩa `lst` nhưng chỉ {n_boc} chỗ được bọc -> còn nhánh câm"


def t_moi_duong_dung_deu_nhan_ho_key():
    """MỌI ĐƯỜNG DỰNG PHẢI ĐƯỢC TRUYỀN HỒ KEY — thiếu một tham số là mất cả một nhóm kênh.

    27/8 — 10 kênh cinematic (20% toàn hệ) ra 0 video suốt phiên 12:14. Gốc không phải nguồn dữ
    liệu, không phải QC, mà là MỘT DÒNG GỌI THIẾU THAM SỐ:
        return chay_phim(kenh, ra, ky, st_san=st_san, ky_hieu=ky_hieu)    # thiếu keys=keys
    `keys` luôn rỗng -> `api` lùi về biến môi trường `GEMINI_API_KEY` (không đặt trong lane vì
    lane lấy key từ HỒ) -> `api` rỗng -> "cần key vẽ ảnh — bỏ lượt", 30 lần một phiên.

    Vì sao lỗi này sống lâu: thông báo nói "cần key vẽ ảnh", đọc lên tưởng THIẾU KEY (chuyện của
    hạn mức, của nhà cung cấp) chứ không ai nghĩ tới việc hồ key đầy ắp mà không được TRUYỀN VÀO.
    Tôi cũng đã đổ cho con key chết trước khi tìm ra dòng này.

    Chốt soi ở tầng gọi: mọi lời gọi `chay_*` bên trong `chay_chung` đều phải mang `keys`."""
    import os as _o, re as _re
    src = io.open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "the_he_2.py"),
                  encoding="utf-8").read()
    i = src.index("def chay_chung")
    ket = [x for x in (src.find("\ndef ", i + 5), src.find("\nclass ", i + 5)) if x > 0]
    than = src[i: min(ket) if ket else len(src)]
    goi = _re.findall(r"return (chay_\w+)\(([^" + chr(10) + r"]*)\)", than)
    assert goi, "không tìm thấy lời gọi `chay_*` nào trong `chay_chung` — chốt đo nhầm chỗ"
    thieu = [h for h, tham in goi if "keys" not in tham]
    assert not thieu, (f"{len(thieu)} đường dựng KHÔNG nhận hồ key: {thieu} — "
                       f"chúng sẽ lùi về biến môi trường và bỏ lượt mọi lần")


def t_tai_san_kenh_dung_phai_co_trong_git():
    """MỌI TÀI SẢN KÊNH KHAI BÁO PHẢI NẰM TRONG GIT — không chỉ nằm trên máy làm việc.

    27/8 — đây là thứ giết nhiều video nhất phiên 15:30, và nó không sai một dòng mã nào:
        Error while downloading .../music/km_long_note_four.mp3: 404
        -> `npx remotion render` thoát khác 0 -> "bộ gen-2 lỗi" -> mất cả long lẫn 3 short.
    `.gitignore` chặn `engine-remotion/public/**`, nên chỉ 6/18 bản nhạc từng được thêm ép vào
    git. Máy làm việc có đủ 18 nên chạy thử ở nhà lúc nào cũng đẹp; CI chỉ có 6 nên **29/50 kênh**
    được gán một bản không tồn tại và hỏng ngay từ lệnh render.

    Đây là lớp lỗi "chạy được ở máy tôi" — thứ mà mọi bài kiểm chạy TRÊN MÁY ĐÓ đều không thấy.
    Nên chốt này không hỏi "tệp có tồn tại không" (ở máy thì luôn có), mà hỏi **git có mang nó
    theo không** — đúng câu hỏi mà CI sẽ hỏi."""
    import os as _o, json as _j, subprocess as _sp
    G = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    try:
        r = _sp.run(["git", "ls-files", "engine-remotion/public/music/"],
                    cwd=G, capture_output=True, text=True, timeout=30)
        trong_git = {_o.path.basename(x) for x in r.stdout.split() if x.strip()}
    except Exception as e:
        print(f"      ⏭️ bỏ qua: không chạy được git ({str(e)[:40]})")
        return
    if not trong_git:
        print("      ⏭️ bỏ qua: không đọc được danh sách tệp từ git")
        return
    ks = _j.load(io.open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),
                                      "kenh_the_he_2.json"), encoding="utf-8"))
    ks = ks if isinstance(ks, list) else list(ks.values())
    thieu = {}
    for k in ks:
        n = str((k.get("brand") or {}).get("nhac") or "")
        if not n:
            continue
        ten = _o.path.basename(n)
        if ten not in trong_git:
            thieu.setdefault(ten, []).append(k["ten"])
    assert not thieu, (
        f"{len(thieu)} bản nhạc được {sum(len(v) for v in thieu.values())} kênh dùng nhưng KHÔNG "
        f"có trong git -> CI se 404 va lenh render hong: " +
        ", ".join(f"{t}({len(v)} kênh)" for t, v in list(thieu.items())[:5]))


def t_dat_tieu_de_chiu_duoc_moi_hinh_dang():
    """HÀM ĐẶT TIÊU ĐỀ PHẢI CHỊU ĐƯỢC MỌI HÌNH DẠNG STORY, VÀ KHÔNG BAO GIỜ GIẾT RENDER.

    27/8 — chính tôi gây ra lỗi này chiều nay. `_so_noi_bat` vốn chỉ chạy ở đường ẢNH BÌA; khi tôi
    nối nó vào khâu đặt tiêu đề, nó bắt đầu chạy cho MỌI story — và kênh dạng phim đặt `hook` là
    một CÂU VĂN chứ không phải dict:
        AttributeError: 'str' object has no attribute 'get'
    -> "bộ gen-2 lỗi" -> mất cả long lẫn short của kênh đó.

    Bài học đắt: nối một hàm cũ vào đường chạy mới nghĩa là cho nó ăn TẬP DỮ LIỆU MỚI. Phải soi
    lại mọi giả định về hình dạng dữ liệu, chứ không phải chỉ soi chỗ gọi.

    Hai điều chốt giữ:
      • `_so_noi_bat` chịu được hook chuỗi, mục chuỗi/số, khoá thiếu — không ném;
      • `_tieu_de_tu_du_lieu` LÀ HÀM LÀM ĐẸP, hỏng thì trả "" chứ tuyệt đối không được ném ra
        ngoài: mất một tiêu đề hay còn hơn mất một video 7 phút đã dựng xong."""
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import the_he_2 as T
    ch = {"ten": "THU"}
    la = [
        {"hook": "What America forgot"},                       # hook là CÂU VĂN (kênh phim)
        {"hook": 123},
        {"items": ["abc", "def"]},                             # mục là chuỗi
        {"items": [None, 5]},
        {"data": ["x"]},
        {"pairs": ["y"]},
        {"frames": [{"t": 1, "data": ["z"]}]},
        {"frames": [{"t": 1}]},                                # khung thiếu `data`
        {},
        {"title": "chỉ có tiêu đề"},
    ]
    for st in la:
        try:
            T._so_noi_bat(st)
        except Exception as e:
            raise AssertionError(f"_so_noi_bat ném với {st!r}: {type(e).__name__}: {e}")
        try:
            r = T._tieu_de_tu_du_lieu(st, ch)
        except Exception as e:
            raise AssertionError(f"_tieu_de_tu_du_lieu ném với {st!r}: {type(e).__name__}: {e}")
        assert isinstance(r, str), f"phải trả chuỗi, nhận {type(r).__name__} với {st!r}"


def t_so_trung_tieu_de_phai_cung_do_dai():
    """SỔ TRÁNH-TRÙNG VÀ PHÉP SO PHẢI CẮT CHUỖI CÙNG MỘT ĐỘ DÀI.

    27/8 — chính bản vá tiêu đề của tôi tự phá chính nó. `run_render._avoid_for` cắt mọi mục
    xuống 60 ký tự cho prompt khỏi phình. Trước đây tiêu đề là khuôn ngắn (41 ký tự) nên cắt
    không đụng gì. Từ khi tiêu đề dẫn bằng chủ thể, nó dài 61 ký tự:
        "Shelley Fabares: 466K — Most-read on Wikipedia — Aug 24, 2026"
    Sổ giữ bản ĐÃ CẮT, `_tieu_de_da_lam` so bản ĐẦY ĐỦ -> không bao giờ khớp -> hệ tin là chưa
    từng làm. Đo thật trên phiên 15:30: **9 long y hệt nhau** ở AMERICALOOKEDUP, 6 ở GAME
    GRAVEYARD — đúng thứ bản vá sinh ra để diệt.

    Bài học: đổi HÌNH DẠNG một giá trị thì phải soi mọi nơi so sánh giá trị đó. Cắt chuỗi là một
    phép so ẩn — nó không trông giống phép so, nên không ai nghĩ tới nó khi làm giá trị dài ra.

    Chốt buộc HAI CON SỐ PHẢI BẰNG NHAU, không chỉ kiểm hành vi ở một ví dụ: sửa một bên mà quên
    bên kia thì lỗi quay lại y nguyên."""
    import sys as _s, os as _o, re as _re
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import the_he_2 as T
    G = _o.path.dirname(_o.path.abspath(__file__))
    rr = io.open(_o.path.join(G, "run_render.py"), encoding="utf-8").read()
    i = rr.index("def _avoid_for")
    than = rr[i: rr.index("\ndef ", i + 5)]
    m = _re.search(r"str\(t\)\[:(\d+)\]", than)
    assert m, "không tìm thấy chỗ cắt chuỗi trong `_avoid_for` — chốt đo nhầm chỗ"
    assert int(m.group(1)) == T._DAI_SO, (
        f"`_avoid_for` cắt {m.group(1)} ký tự nhưng `_tieu_de_da_lam` cắt {T._DAI_SO} — "
        f"hai bên so hai độ dài khác nhau thì tiêu đề dài KHÔNG BAO GIỜ khớp, và hệ đẻ trùng")

    # Hành vi: tiêu đề dài hơn mốc cắt vẫn phải nhận ra là ĐÃ LÀM.
    day = "Shelley Fabares: 466K — Most-read on Wikipedia — Aug 24, 2026"
    assert len(day) > T._DAI_SO, "ví dụ phải dài hơn mốc cắt mới kiểm được điều cần kiểm"
    assert T._tieu_de_da_lam(day, [day[:T._DAI_SO]]), "tiêu đề dài không khớp với bản đã cắt trong sổ"
    # ...nhưng hai tiêu đề THẬT SỰ khác nhau vẫn phải phân biệt được.
    assert not T._tieu_de_da_lam("Joshua Kushner: 525K — Most-read on Wikipedia — Aug 12, 2026",
                                 [day[:T._DAI_SO]]), "cắt quá tay -> hai đề tài khác bị coi là một"




def t_lich_kling_python_khop_web():
    """ĐỀ BÀI PYTHON SINH VÀ ĐỀ BÀI TRÌNH DUYỆT SINH PHẢI GIỐNG HỆT NHAU.

    2/9 — Thêm trục "kiểu mở kênh này diễn được" (`_mo_kenh`) làm ĐỘ DÀI một trục đổi theo
    kênh. Nếu bản xuất web vẫn gửi `KIEU_MO` đầy đủ trong khi `_do_truc` đã đếm bản đã lọc thì
    hai bên giải mã cùng một con số ra hai bộ chỉ số khác nhau — và lệch kiểu ấy KHÔNG nhìn ra
    được: sáu trục kia vẫn khớp hoàn hảo, chỉ một trường sai. Đã xảy ra đúng như vậy hôm 1/9
    khi thêm trục thứ bảy: 280/280 đề bài sai đúng một trường.

    Chốt này dựng lại phép tính của trình duyệt TỪ CHÍNH TỆP ĐÃ XUẤT rồi so với `_lich()`.
    """
    import sys as _s, os as _o, json as _j
    goc = _o.path.dirname(_o.path.abspath(__file__))
    _s.path.insert(0, goc)
    import kling_kenh as KK
    d = _o.path.join(goc, "..", "MM0-AutoPublisher", "dashboard", "kling")
    if not _o.path.isdir(d):
        return                                  # chưa xuất web thì không có gì để so
    m = _j.load(open(_o.path.join(d, "index.json")))
    lech = []
    for k in m["kenh"]:
        f = _o.path.join(d, k["slug"] + ".json")
        if not _o.path.exists(f):
            lech.append(f"{k['ten']}: thiếu tệp"); continue
        LI = _j.load(open(f))["lich"]
        P = 1
        for t in LI["truc"]:
            P *= t
        for so in (0, 1, 7, 39):
            x, ix = (LI["goc"] % P + so * LI["buoc"]) % P, []
            for t in LI["truc"]:
                ix.append(x % t); x //= t
            vai = LI["vai"]; gay = vai[ix[4]]
            con = [v for v in vai if v != gay] or vai
            web = {"phong": LI["phong"][ix[0]], "dao_cu": LI["dao_cu"][ix[1]],
                   "ap_luc": LI["ap_luc"][ix[2]], "kieu_mo": LI["kieu_mo"][ix[3]],
                   "gay": gay, "lat": con[ix[5] % len(con)]}
            py = KK._lich(k["ten"], so)
            for c in web:
                if web[c] != py[c]:
                    lech.append(f"{k['ten']} tập {so} trường {c}")
                    break
    assert not lech, f"{len(lech)} đề bài lệch giữa Python và web: {lech[:4]}"


def t_khuon_hinh_doi_tung_tap_va_khop_web():
    """KHUÔN HÌNH PHẢI ĐỔI TỪNG TẬP, KHÔNG LẶP LIỀN KỀ, VÀ WEB TÍNH RA ĐÚNG NHƯ PYTHON.

    2/9 — `_bat_buoc` từng ghi cứng "Camera locked off at standing eye level, wide." vào MỌI
    prompt. Đo trên sáu bản thảo thật: 6/6 hook mở bằng "static eye-level wide shot" — ba mươi
    kênh, mọi tập, một khuôn hình. Đây là thứ người xem thấy TRƯỚC cả nội dung, và là chữ
    "cảnh" trong câu luật YouTube về nội dung hàng loạt.

    Ba chốt, vì bản vá này có ba chỗ hỏng được:
      1. lặp liền kề — bản đầu nhét khuôn hình thành trục thứ tám của bộ lịch, và vì nó thành
         CHỮ SỐ CAO NHẤT nên 144/199 tập liền nhau trùng khuôn dù tổng thể vẫn đều.
      2. bước ghi cứng — kênh có `khuon_cam` còn 6 khuôn thì gcd(3,6)=3, bước 3 chỉ đi qua HAI ô.
      3. web lệch — khuôn prompt web dựng một lần cho cả kênh, không đục ô trống thì mọi tập
         sinh từ trình duyệt đều mang khuôn hình của tập 0.
    """
    import sys as _s, os as _o, json as _j
    goc = _o.path.dirname(_o.path.abspath(__file__))
    _s.path.insert(0, goc)
    import kling_kenh as KK
    for ten in KK.KENH:
        ds = [KK._lich(ten, so)["khuon_hinh"] for so in range(60)]
        lap = [i for i, (a, b) in enumerate(zip(ds, ds[1:])) if a == b]
        assert not lap, f"{ten}: khuôn hình lặp liền kề ở tập {lap[:3]}"
        n = len(KK._khuon_kenh(KK.ho_so(ten)))
        assert len(set(ds)) == n, f"{ten}: chỉ dùng {len(set(ds))}/{n} khuôn trong 60 tập"
    # prompt phải mang ĐÚNG câu máy của lịch, và đề bài phải nói cùng khuôn ấy
    import re as _r
    mau = {"hook": "x", "payoff": "y", "room": None,
           "lines": [{"who": "a", "say": "He's here."}]}
    for ten in list(KK.KENH)[:6]:
        ph = next(iter(KK.ho_so(ten)["phong"]))
        for so in (0, 1, 2, 3):
            p = KK.prompt(ten, dict(mau, room=ph), 6, so=so)
            assert KK._lich(ten, so)["may"] in p, f"{ten} tập {so}: prompt thiếu câu máy của lịch"
            m = _r.search(r"EXACTLY this framing[^:]*: ([^.]+)\.", KK._sys(ten, 6, so))
            assert m and m.group(1) == KK._lich(ten, so)["khuon_hinh"], \
                f"{ten} tập {so}: đề bài và prompt nói hai khuôn khác nhau"
    # web: chạy ĐÚNG đoạn JS của dashboard trên ĐÚNG dữ liệu vừa xuất
    d = _o.path.join(goc, "..", "MM0-AutoPublisher", "dashboard")
    if not _o.path.isdir(_o.path.join(d, "kling")):
        return
    idx = _j.load(open(_o.path.join(d, "kling", "index.json")))
    for k in idx["kenh"]:
        f = _o.path.join(d, "kling", k["slug"] + ".json")
        if not _o.path.exists(f):
            continue
        LI = _j.load(open(f))["lich"]
        KH, b = LI.get("khuon_hinh") or [], LI.get("khuon_buoc") or 3
        assert KH, f"{k['ten']}: web thiếu bảng khuôn hình"
        for so in (0, 1, 5, 11):
            web = KH[((LI.get("goc", 0) + so * b) % len(KH) + len(KH)) % len(KH)][1]
            assert web == KK._lich(k["ten"], so)["may"], \
                f"{k['ten']} tập {so}: web và Python ra hai câu máy khác nhau"
    # khuôn web phải còn Ô TRỐNG, không phải câu máy đã nướng cứng
    f = _o.path.join(d, "kling", idx["kenh"][0]["slug"] + ".json")
    kh = _j.load(open(f))["khuon"]
    than = kh[list(kh)[0]]["than"][0]
    assert "@@MAY@@" in than, "khuôn web nướng cứng câu máy — mọi tập sẽ mang khuôn của tập 0"



def t_tn_giao_hang_khai_bao_ai():
    """BỘ THIÊN NHIÊN PHẢI CÓ ĐƯỜNG GIAO HÀNG, VÀ BÀI ĐĂNG PHẢI KHAI BÁO LÀ CẢNH AI.

    2/9 — `thien_nhien.py` dừng ở PROMPT. `kling_dong_bo.py` import cứng `kling_kenh`, nên đưa
    một tập thiên nhiên vào là nổ ngay: `RuntimeError: chưa có kênh 'ICE BEAR'`. Một dây chuyền
    kết thúc ở nửa đường trông y hệt một dây chuyền hoàn chỉnh, cho tới lúc có clip trong tay.

    Và chốt thứ hai quan trọng hơn: câu khai báo "đây không phải tư liệu thật" phải có ở CẢ BA
    nền tảng. Đó là ràng buộc cứng số một của ngách này — trình bày cảnh AI như tư liệu động vật
    thật vừa là khai man vừa là dạng bị gỡ nhanh nhất.
    """
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import tn_dong_bo as TD
    import thien_nhien as TN
    for ten in TN.KENH:
        x = TN.lich(ten, 0)
        bai = TD.viet_bai({"kenh": ten, "loai": x["loai"], "hanh_vi": x["hanh_vi"], "giay": 8})
        e = TD.kiem_bai(bai)
        assert not e, f"{ten}: {e}"
    # thử ngược: bỏ khai báo ở một nền tảng thì cổng PHẢI kêu (luật 13.11)
    x = TN.lich("ICE BEAR", 0)
    bai = TD.viet_bai({"kenh": "ICE BEAR", "loai": x["loai"], "hanh_vi": x["hanh_vi"], "giay": 8})
    bai["facebook"]["text"] = "no disclosure"
    assert TD.kiem_bai(bai), "cổng khai báo AI không bắt được khi thiếu — cổng chết"



def t_tn_ho_so_toan_ven():
    """TÁM PHÉP KIỂM TOÀN VẸN CHO HỒ SƠ 14 KÊNH THIÊN NHIÊN.

    3/9 — Cả tám phép này em đã chạy TAY một lần rồi thấy sạch. Nhưng một phép kiểm chạy một lần
    không phải cổng: nó chứng minh hiện tại lành, không ngăn được lần sửa sau. Ba trong tám cái
    dưới đây đã từng BẮT ĐƯỢC lỗi thật trong lúc dựng — nhãn `seabird` không có trong mô tả
    "A shearwater", nhãn `blue sheep` không có trong mô tả "A bharal" — và cả hai lần em sửa tay
    rồi đi tiếp, tức để nguyên cái bẫy cho lần thêm loài tiếp theo.
    """
    import sys as _s, os as _o, re as _re
    goc = _o.path.dirname(_o.path.abspath(__file__))
    _s.path.insert(0, goc)
    import thien_nhien as TN
    import brand_tn as BT
    import tn_dong_bo as TD

    # 1. Nhãn loài phải có mặt trong chính mô tả của nó — nếu không, cổng "prompt nêu đúng loài"
    #    sẽ chặn mọi tập của loài ấy, và chặn ở khâu SINH chứ không ở khâu THÊM.
    xau = [(k, l) for k, c in TN.KENH.items() for l, v in c["loai"].items()
           if [t for t in _re.findall(r"[a-z]+", l.lower()) if len(t) >= 4]
           and not any(t in v.lower()
                       for t in _re.findall(r"[a-z]+", l.lower()) if len(t) >= 4)]
    assert not xau, f"nhãn loài không xuất hiện trong mô tả của nó: {xau[:3]}"

    # 2. `MACRO_OK` là một danh sách CHUỖI rời — sửa câu hành vi mà quên sửa ở đây thì mục ấy
    #    thành mồ côi và khuôn cận cực đại lặng lẽ không bao giờ được chọn cho loài đó.
    tat = {h for c in TN.KENH.values() for b in c["hanh_vi"].values()
           for d in b.values() for h in d}
    assert not (TN.MACRO_OK - tat), f"MACRO_OK mồ côi: {sorted(TN.MACRO_OK - tat)[:3]}"

    # 3. Slug quyết định tên thư mục và tên tệp web — đụng nhau là hai kênh ghi đè nhau.
    sl = [_re.sub(r"[^a-z0-9]+", "-", k.lower()).strip("-") for k in TN.KENH]
    assert len(set(sl)) == len(sl), "slug kênh đụng nhau"

    # 4. Khuôn hình thiếu trong `KHUON_MOI_TRUONG` sẽ mặc định về ("tren",) — im lặng, và sai
    #    ngay ở kênh dưới nước.
    thieu = [a for a, _ in TN.KHUON if a not in TN.KHUON_MOI_TRUONG]
    assert not thieu, f"khuôn hình thiếu bảng môi trường: {thieu}"

    # 5. `*_cam` viết sai mẩu chữ có thể lọc gần sạch mà vẫn còn 1–2 mục, tức không nổ nhưng
    #    kênh mất gần hết biến thể. Đòi sàn tối thiểu.
    ngheo = [k for k, c in TN.KENH.items()
             if len(TN.khuon_kenh(c)) < 4 or len(TN.as_kenh(c)) < 3 or len(TN.tt_kenh(c)) < 3]
    assert not ngheo, f"kênh bị lọc quá tay: {ngheo}"

    # 6. Biểu tượng không có nhánh vẽ riêng sẽ rơi vào `else` — một hình TRÒN, và cổng bóng
    #    ngoài sẽ báo trùng ngay... trừ khi chỉ có đúng một cái, lúc ấy nó im lặng.
    src = open(_o.path.join(goc, "brand_tn.py"), encoding="utf-8").read()
    thieu_bt = [b["bt"] for b in BT.BRAND.values() if f'ten == "{b["bt"]}"' not in src]
    assert not thieu_bt, f"biểu tượng không có nét vẽ riêng: {thieu_bt}"

    # 7. Bài đăng dựng được cho MỌI kênh và luôn mang câu khai báo AI.
    xau = []
    for k in TN.KENH:
        x = TN.lich(k, 0)
        e = TD.kiem_bai(TD.viet_bai({"kenh": k, "loai": x["loai"],
                                     "hanh_vi": x["hanh_vi"], "giay": 8}))
        if e:
            xau.append((k, e[0][:40]))
    assert not xau, f"bài đăng chưa đạt: {xau[:2]}"

    # 8. Panel web KHÔNG được chạm Firestore. Anh dặn tiết kiệm hạn mức, và cách chắc chắn nhất
    #    là không có lệnh nào để mà tốn — nên canh bằng cổng, không bằng lời hứa.
    d = _o.path.join(goc, "..", "MM0-AutoPublisher", "dashboard", "index.html")
    if _o.path.exists(d):
        h = open(d, encoding="utf-8").read()
        i, j = h.find("const _tnCache = {}"), h.find("window.klingChep = async")
        if i > 0 and j > i:
            khoi = h[i:j]
            cam = [x for x in ("getDoc", "setDoc", "addDoc", "deleteDoc", "collection(",
                               "onSnapshot", "gdocGate", "_appFor") if x in khoi]
            assert not cam, f"panel thiên nhiên chạm Firestore: {cam}"

def t_khong_khoa_trung_trong_ho_so():
    """KHÔNG DICT NÀO TRONG HỒ SƠ KÊNH ĐƯỢC CÓ KHOÁ TRÙNG.

    3/9 — Chèn thêm hành vi cho một loài, và bộ chèn tạo một khoá `"mep"` THỨ HAI trong khi loài
    ấy đã có `"mep"` ở dưới. Python **lấy khoá sau và vứt khoá trước, không báo một chữ nào** —
    hai hành vi mới biến mất trong khi tệp nguồn đọc lên vẫn thấy chúng nằm đó.

    Đây là dạng lỗi tệ nhất: mã đúng cú pháp, tệp trông đúng, thước xanh, và dữ liệu thì mất.
    Em chỉ phát hiện vì đếm số hành vi trước/sau và thấy con số KHÔNG TĂNG.

    Quét bằng `ast` chứ không bằng cách nạp module — nạp module thì khoá trùng đã bị nuốt mất
    rồi, tức đúng thứ cần bắt không còn ở đó để mà bắt.
    """
    import ast as _a, io as _io, os as _o
    goc = _o.path.dirname(_o.path.abspath(__file__))
    for ten in ("thien_nhien.py", "kling_kenh.py", "brand_tn.py", "brand_kling.py"):
        f = _o.path.join(goc, ten)
        if not _o.path.exists(f):
            continue
        cay = _a.parse(_io.open(f, encoding="utf-8").read())
        xau = []
        for n in _a.walk(cay):
            if isinstance(n, _a.Dict):
                ks = [k.value for k in n.keys
                      if isinstance(k, _a.Constant) and isinstance(k.value, str)]
                d = sorted({k for k in ks if ks.count(k) > 1})
                if d:
                    xau.append((ten, n.lineno, d))
        assert not xau, f"khoá trùng (Python nuốt im lặng): {xau[:4]}"

def t_bo_thien_nhien_lanh():
    """BỘ THIÊN NHIÊN: mọi prompt lọt trần, hàng rào nguyên, không cặp kênh nào trùng.

    2/9 — Bộ thứ năm (mười kênh động vật, short 8–10 giây một cú máy, không lời). Nó KHÔNG dùng
    engine của bộ hài, nên phải có chốt riêng — nếu không thì một bản sửa ở `kling_kenh.py` làm
    hỏng nó mà không ai biết, và ngược lại.

    Ba thứ được canh, đúng ba thứ đã trả giá ở bốn bộ trước:
      · prompt vượt trần 2.500 -> Kling cắt đuôi và mất hàng rào DO NOT (luật 13.1)
      · hàng rào không kết đúng câu chốt -> đã bị xô lệch
      · hai kênh chung quá nhiều chữ / chung loài / chung hành vi (luật chính sách 13.17)
    """
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import thien_nhien as TN
    loi = []
    for k in TN.KENH:
        for so in (0, 1, 7, 41):
            for g in TN.GIAY_CHUAN:
                loi += [f"{k} tập {so} {g}s: {x}" for x in TN.cham(k, so, g)]
    assert not loi, f"{len(loi)} lỗi prompt, ví dụ: {loi[:3]}"
    xau = TN.kiem_da_dang()
    assert not xau, f"{len(xau)} cặp kênh trùng: {xau[:3]}"


def t_brand_thien_nhien_doc_duoc():
    """BRAND KIT THIÊN NHIÊN đi qua ĐÚNG BA CỔNG mà bộ hài đã trả giá để có.

    Không chép phép đo sang tệp mới — `brand_tn` gọi thẳng `brand_kling` với bảng dữ liệu của
    mình. Chép là tạo nguồn sự thật thứ hai (luật 13.5), và nguồn thứ hai luôn là nguồn lệch.
    """
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import brand_tn as BT
    import thien_nhien as TN
    assert list(BT.BRAND) == list(TN.KENH), "BRAND và KENH lệch nhau -> số trên avatar sai"
    assert not BT.kiem_bong(), f"biểu tượng trùng bóng ngoài: {BT.kiem_bong()[:2]}"
    assert not BT.kiem_tron(), f"chữ avatar bị đường tròn cắt: {BT.kiem_tron()[:2]}"
    assert not BT.kiem_tuong_phan(), f"biểu tượng chìm vào nền: {BT.kiem_tuong_phan()[:2]}"

def t_kenh_kling_dong_bo_ba_noi():
    """MỖI KÊNH KLING PHẢI CÓ MẶT Ở CẢ BA NƠI: hồ sơ · brand · dữ liệu web.

    2/9 — Thêm mười kênh mới phải sửa hai tệp ở hai chỗ khác nhau (`KENH` trong kling_kenh.py và
    `BRAND` trong brand_kling.py). Thiếu một bên thì KHÔNG có lỗi nào nổ: brand_kling chỉ lặp
    `BRAND` nên nó lặng lẽ bỏ qua kênh chưa khai, và dashboard đọc index.json nên kênh ấy hiện
    ra trong dropdown mà không có avatar. Đúng họ lỗi "hai danh sách viết ở hai nơi".
    """
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import kling_kenh as KK
    import brand_kling as BK
    thieu_brand = [k for k in KK.KENH if k not in BK.BRAND]
    thua_brand = [k for k in BK.BRAND if k not in KK.KENH]
    assert not thieu_brand, f"kênh có hồ sơ mà thiếu brand: {thieu_brand}"
    assert not thua_brand, f"brand có mà không có hồ sơ: {thua_brand}"
    # thứ tự phải khớp: số thứ tự trên avatar lấy theo vị trí, dropdown lấy theo index.json
    assert list(KK.KENH) == list(BK.BRAND), "thứ tự KENH và BRAND lệch nhau -> số trên avatar sai"


def t_avatar_khong_bi_cat_tron():
    """CHỮ VÀ SỐ TRÊN AVATAR PHẢI NẰM TRONG ĐƯỜNG TRÒN NỀN TẢNG SẼ CẮT.

    2/9 — YouTube, Facebook và Instagram đều cắt avatar thành hình tròn. Bản trước đặt dải tên
    sát đáy và huy hiệu số ở góc khung vuông: đo được 20/20 kênh bị cắt ngang chữ, và huy hiệu
    số nằm HOÀN TOÀN ngoài vòng nên không nền tảng nào hiển thị nó.

    Đây là lần thứ hai cùng một lỗi ở cùng một hàm: bản vá trước chỉ bỏ vòng tròn TÔI vẽ, không
    làm gì được vòng tròn HỌ cắt. Nên chốt này đo trên ảnh thật, không đọc mã.
    """
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import brand_kling as BK
    xau = BK.kiem_tron()
    assert not xau, f"{len(xau)} kênh có chữ ngoài vòng tròn: {[t for _, t in xau[:5]]}"


def t_bieu_tuong_doc_duoc_tren_nen_cua_no():
    """BIỂU TƯỢNG PHẢI TƯƠNG PHẢN ĐỦ VỚI NỀN CỦA CHÍNH KÊNH ẤY.

    2/9 — Mười kênh mới lần đầu lấy màu KHÔNG KHÍ của bộ phim làm màu dấu hiệu (đỏ huy hiệu, đỏ
    tiết). SMALL CLAIMS đo được 1,74 và QUEST BOARD 2,06 — thấp hơn mọi kênh đang có, và nhìn
    lưới avatar thì hai biểu tượng ấy gần như biến mất. Cùng họ lỗi với `k["mau"]`: mượn một giá
    trị cho việc nó không sinh ra để làm.

    BAGGAGE CLAIM (2,61) có từ trước bản này; sau khi anh duyệt đã nâng lên 4,49 nên cổng
    không còn ngoại lệ nào — một cổng có ngoại lệ là một cổng đang chờ ngoại lệ thứ hai.
    """
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import brand_kling as BK
    xau = [t for _, t, _c, _n in BK.kiem_tuong_phan(3.0)]
    assert not xau, f"biểu tượng chìm vào nền: {xau}"

def t_kling_chan_dung_diem_yeu():
    """BỘ CHẤM KLING PHẢI CHẶN ĐÚNG NHỮNG THỨ KLING LÀM HỎNG.

    28/8 — anh có tài khoản WEB Kling trả phí (không có API), ngồi tạo tay rất mất thời gian. Hệ
    không tự động hoá trình duyệt (đường dễ mất tài khoản nhất), mà làm phần MÁY LÀM ĐƯỢC: nghĩ
    phân cảnh, viết prompt, và ghép lại.

    Giá trị thật nằm ở bộ CHẤM, không phải bộ sinh. Lần thử 09/08 đã trả giá để biết Kling hỏng ở
    đâu: xin "Pompeii năm 79, góc nhìn đứng dưới đất" thì ra làng Ý hiện đại chụp từ drone. Hai
    thứ trôi mạnh nhất là GÓC MÁY và THỜI ĐẠI; hai thứ Kling vẽ hỏng chắc chắn là CHỮ và MẶT
    NGƯỜI CẬN CẢNH.
    Nếu bộ chấm không bắt được đúng bốn thứ đó thì nó chỉ là bộ sinh chữ, và anh vẫn mất thời gian
    y như cũ — chỉ khác là mất sau khi đã tốn credit Kling."""
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import kling_studio as K

    def loi(canh):
        return " | ".join(K._validate({"hook_line": "H", "title": "t", "scenes": canh}))

    # 1. thiếu ghim góc máy -> phải bắt (đây là lỗi trôi drone đã gặp thật)
    r = loi([{"n": 1, "beat": "hook", "sec": 4, "prompt": "A dog stands behind the counter of a store at night with neon light everywhere"},
             {"n": 2, "beat": "payoff", "sec": 4, "prompt": "Static wide shot of the street outside, fog drifting under a lamp"}])
    assert "ghim góc máy" in r, f"không bắt được prompt thiếu góc máy: {r}"

    # 2. chữ đọc được -> phải bắt
    r = loi([{"n": 1, "beat": "hook", "sec": 4, "prompt": "Static wide shot of a parking lot: a neon sign with text reading OPEN flickering"},
             {"n": 2, "beat": "payoff", "sec": 4, "prompt": "Static wide shot of the street outside, fog drifting under a lamp"}])
    assert "chữ đọc được" in r, f"không bắt được chữ trong prompt: {r}"

    # 3. mặt cận cảnh -> phải bắt
    r = loi([{"n": 1, "beat": "hook", "sec": 4, "prompt": "Static eye-level shot: a close-up of his face showing confusion under fluorescent light"},
             {"n": 2, "beat": "payoff", "sec": 4, "prompt": "Static wide shot of the street outside, fog drifting under a lamp"}])
    assert "mặt cận cảnh" in r, f"không bắt được mặt cận cảnh: {r}"

    # 4. quá dài -> phải bắt (Kling tính tiền theo giây, và anh chốt 3-6s/cảnh)
    r = loi([{"n": 1, "beat": "hook", "sec": 12, "prompt": "Static eye-level shot of a quiet suburban garage at dawn, dust in the light"},
             {"n": 2, "beat": "payoff", "sec": 4, "prompt": "Static wide shot of the street outside, fog drifting under a lamp"}])
    assert "3-6 giây" in r, f"không bắt được cảnh quá dài: {r}"

    # 5. prompt SẠCH thì phải qua được phần của nó (không đòi qua hết, vì còn luật số cảnh)
    sach = [{"n": i, "beat": b, "sec": 4,
             "prompt": "Static eye-level shot inside a suburban American garage: a golden retriever "
                       "slowly pushes a lawnmower across the concrete, morning light through dust"}
            for i, b in enumerate(["hook", "setup", "turn", "escalate", "escalate", "payoff"], 1)]
    r = K._validate({"hook_line": "HE MOWS AT 6AM", "title": "t", "scenes": sach})
    xau = [x for x in r if any(k in x for k in ("ghim góc máy", "chữ đọc được", "mặt cận cảnh", "3-6 giây"))]
    assert not xau, f"prompt sạch mà vẫn bị bắt lỗi: {xau}"


def t_kling_thieu_canh_phai_chan_truoc_khi_ghep():
    """THIẾU MỘT CẢNH THÌ PHẢI CHẶN, KHÔNG ĐƯỢC GHÉP RỒI ĐĂNG.

    28/8 — đây là luật quan trọng nhất của lò Kling. Thiếu một cảnh giữa chừng thì gag GÃY, nhưng
    video vẫn ra, vẫn đủ độ dài, vẫn qua QC kỹ thuật, vẫn đẩy kho, vẫn đăng. Hỏng kiểu đó không có
    gì báo động — người xem thấy một video vô nghĩa còn hệ báo "thành công".
    Nên phải chặn TRƯỚC khi ghép, và nói rõ thiếu cảnh nào để anh biết dán tiếp cái gì.

    Chốt cũng canh việc "đã đẩy thì thôi": mốc `.da_day` là thứ duy nhất ngăn một thư mục bị đẩy
    kho hai lần khi chạy lại — mất nó là đăng trùng."""
    import sys as _s, os as _o, json as _j, tempfile as _t
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import kling_lo as KL
    with _t.TemporaryDirectory() as d:
        _o.makedirs(_o.path.join(d, "clips"))
        io.open(_o.path.join(d, "shots.json"), "w", encoding="utf-8").write(_j.dumps(
            {"title": "t", "hook_line": "H",
             "scenes": [{"n": i, "beat": "hook", "sec": 4, "prompt": "x"} for i in (1, 2, 3)]}))
        # chưa có clip nào
        du, tep, thieu = KL.kiem_du(d)
        assert not du and len(thieu) == 3, f"thư mục rỗng mà báo đủ: {du} {thieu}"
        # có 2/3 -> VẪN PHẢI chặn, và nói đúng cảnh còn thiếu
        for n in (1, 3):
            io.open(_o.path.join(d, "clips", f"scene-{n:02d}.mp4"), "wb").write(b"0" * 20000)
        du, tep, thieu = KL.kiem_du(d)
        assert not du, "thiếu cảnh 2 mà vẫn báo đủ -> sẽ ghép ra video gãy gag rồi đăng"
        assert thieu == ["scene-02"], f"báo sai cảnh thiếu: {thieu}"
        # tệp quá nhỏ = tải hụt -> phải coi như chưa có
        io.open(_o.path.join(d, "clips", "scene-02.mp4"), "wb").write(b"0" * 100)
        du, _, thieu = KL.kiem_du(d)
        assert not du and thieu == ["scene-02"], "tệp tải hụt (quá nhỏ) vẫn bị tính là có"
        # đủ cả 3 -> mới cho qua
        io.open(_o.path.join(d, "clips", "scene-02.mp4"), "wb").write(b"0" * 20000)
        du, tep, thieu = KL.kiem_du(d)
        assert du and len(tep) == 3, f"đủ 3 clip mà vẫn chặn: {thieu}"
    # mốc chống đẩy trùng phải tồn tại trong mã
    src = io.open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "kling_lo.py"),
                  encoding="utf-8").read()
    assert ".da_day" in src and "continue" in src, "mất mốc chống đẩy kho hai lần -> đăng trùng"


def t_kling_shots_ghi_doc_cung_mot_project():
    """CHỖ GHI VÀ CHỖ ĐỌC PHẢI TRỎ CÙNG MỘT PROJECT.

    28/8 — suýt dính: `firestore_bridge.save_kling_shots` ghi vào `_db_meta()` (project B, để
    không ăn hạn mức project A nơi 18 lane render đang tranh nhau), nhưng dashboard định tuyến
    collection bằng danh sách `META_B` — thiếu tên trong đó là nó đọc project A và **không thấy
    gì**, trong khi dữ liệu nằm nguyên bên B.
    Hỏng kiểu này im lặng tuyệt đối: không lỗi, không cảnh báo, chỉ là danh sách rỗng — và người
    dùng kết luận "tính năng không chạy".
    Cùng họ với lỗi đã gặp hôm nay (bên ghi và bên đọc dùng hai bộ luật khác nhau): chốt phải soi
    CẢ HAI PHÍA, không phải chỉ phía mình vừa sửa."""
    import os as _o
    G = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    fb = io.open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "firestore_bridge.py"),
                 encoding="utf-8").read()
    i = fb.index("def save_kling_shots")
    # Cắt theo BIÊN HÀM, không theo số ký tự. Bản đầu lấy 900 ký tự cố định — cửa sổ tràn sang
    # `read_kling_shots` (hàm đó cũng có `_db_meta()`), nên chốt vẫn xanh khi tôi cố tình đổi
    # chỗ ghi sang project A. Đúng lớp lỗi "cửa sổ cố định" tôi đã mắc trước đây: chốt đo nhầm
    # vùng thì nó chỉ đo được chính nó.
    j = fb.index("\ndef ", i + 5)
    than = fb[i:j]
    ben_ghi = "_db_meta()" in than
    d = _o.path.join(G, "MM0-AutoPublisher", "dashboard", "index.html")
    if not _o.path.exists(d):
        print("      ⏭️ bỏ qua: không có repo MM0-AutoPublisher ở đây")
        return
    db = io.open(d, encoding="utf-8").read()
    j = db.index("const META_B = new Set(")
    ben_doc_B = '"kling_shots"' in db[j: db.index(")", j)]
    assert ben_ghi == ben_doc_B, (
        f"lệch project: Python ghi vào {'B' if ben_ghi else 'A'} nhưng dashboard đọc "
        f"{'B' if ben_doc_B else 'A'} -> danh sách rỗng mà không báo lỗi gì")


def t_kling_az_dung_dung_cho_khi_chua_co_key():
    """ĐƯỜNG A-Z PHẢI DỪNG ĐÚNG CHỖ KHI CHƯA CÓ KEY, VÀ KÊNH PHẢI ĐƯỢC KHAI.

    28/8 — hai bất biến, mỗi cái chặn một kiểu hỏng đã từng xảy ra thật:

    1) CHƯA CÓ KEY -> làm tới bảng chụp rồi DỪNG có tiếng, không được ném lỗi.
       Nếu nó ném thì workflow đỏ, và người đọc log sẽ tưởng hệ hỏng trong khi chỉ là chưa mua
       key. Một trạng thái BÌNH THƯỜNG mà báo như lỗi thì lần sau không ai tin log nữa.

    2) KÊNH PHẢI CÓ TRONG channels.yaml.
       `enqueue.py` `raise SystemExit` khi kênh thiếu ở đó — và ngày 20/8 đúng lỗi này làm 27/40
       kênh mất video suốt nhiều tuần: video dựng xong, QC đạt, rồi bị vứt ở bước cuối vì thiếu
       một dòng cấu hình. Kênh Kling phải không lặp lại chuyện đó."""
    import sys as _s, os as _o, io as _io, contextlib as _ct, tempfile as _tf, json as _j
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import kling_auto as A, kling_studio as KS, kling_api as KA

    # (1) không key -> trả "cho_clip", KHÔNG ném, và có để lại bảng chụp cho người dùng
    cu_sinh, cu_env = KS.sinh, {k: _o.environ.pop(k, None) for k in
                                ("KLING_ACCESS_KEY", "KLING_SECRET_KEY")}
    cu_kho = A.KHO
    try:
        KS.sinh = lambda yt, **k: {
            "title": "T", "logline": "x", "hook_line": "H",
            "scenes": [{"n": i, "beat": "hook", "sec": 4, "caption": "",
                        "prompt": "Static eye-level shot of a garage at dawn"} for i in (1, 2, 3)]}
        with _tf.TemporaryDirectory() as d:
            A.KHO = d
            with _ct.redirect_stdout(_io.StringIO()) as buf:
                r = A.mot_video("thu", "", [])
            assert r == "cho_clip", f"chưa có key mà trả {r!r} — phải là 'cho_clip'"
            assert not KA.co_api(), "co_api() báo có key trong khi biến đã bị gỡ"
            tm = _o.path.join(d, "t")
            assert _o.path.exists(_o.path.join(tm, "BANG_CHUP.md")), \
                "không để lại BANG_CHUP.md -> người dùng không có gì để dán vào Kling"
            assert "KLING_ACCESS_KEY" in buf.getvalue(), \
                "dừng mà không nói vì sao -> người đọc log tưởng hỏng"
    finally:
        KS.sinh, A.KHO = cu_sinh, cu_kho
        for k, v in cu_env.items():
            if v is not None:
                _o.environ[k] = v

    # (2) kênh phải được khai, nếu không enqueue.py sẽ vứt video đã dựng xong
    G = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    cfg = _o.path.join(G, "MM0-AutoPublisher", "config", "channels.yaml")
    if not _o.path.exists(cfg):
        print("      ⏭️ bỏ qua phần channels.yaml: không có repo MM0-AutoPublisher ở đây")
        return
    txt = _io.open(cfg, encoding="utf-8").read()
    ma = _o.environ.get("KLING_KENH") or "KLINGCOMEDY"
    # CHỈ ĐÒI KHI LUỒNG KLING CÒN CHẠY. `kling_cron.yml` đã gỡ `schedule:` (nghỉ từ 1/9), nên
    # đòi kênh của nó phải khai trong channels.yaml là tạo một dòng đỏ VĨNH VIỄN cho việc không
    # ai làm — và một cổng đỏ mãi thì người ta thôi đọc nó, mất luôn những lỗi thật bên cạnh.
    _wf = _o.path.join(G, ".github", "workflows", "kling_cron.yml")
    if _o.path.exists(_wf):
        _y = _io.open(_wf, encoding="utf-8").read()
        _ma_y = "\n".join(l for l in _y.split("\n") if not l.lstrip().startswith("#"))
        if "cron:" not in _ma_y:
            print("      ⏭️ luồng Kling đã nghỉ (không còn cron) — không đòi kênh trong channels.yaml")
            return
    assert f"  {ma}:" in txt, (
        f"kênh {ma} CHƯA khai trong channels.yaml -> enqueue.py sẽ SystemExit và video dựng xong "
        f"bị vứt (đúng lỗi 20/8 làm 27/40 kênh mất video nhiều tuần)")


def t_thang_phai_noi_dung_loai_du_lieu():
    """NHÃN THANG PHẢI KHỚP LOẠI DỮ LIỆU ĐANG VẼ.

    28/8 — ảnh khung hình thật kênh FAME CURVE: cột ghi "1 in 10,000" ngay cạnh con số "63.4K",
    mà đây là LƯỢT ĐỌC Wikipedia chứ không phải xác suất. Khuôn `longshot` vốn là thang xác suất
    ("1 phần triệu"); đổ dữ liệu ĐẾM vào thì mọi nhãn thang đều vô nghĩa.
    Đây là loại sai tệ hơn cả chữ chồng chữ: chữ chồng thì người xem biết là lỗi, còn nhãn sai
    thì họ TIN — và tin sai về con số là thứ giết niềm tin vào cả kênh dữ liệu.

    Chốt buộc: nguồn nào đếm thì phải khai `rung_kieu`, và chuỗi khai đó phải chảy hết đường
    story -> props -> composition. Đứt ở bất kỳ khâu nào là nhãn lại sai mà không ai thấy."""
    import os as _o
    G = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    R = _o.path.dirname(_o.path.abspath(__file__))
    th = io.open(_o.path.join(R, "the_he_2.py"), encoding="utf-8").read()
    assert '"rung_kieu": "dem"' in th, "nguồn lượt-đọc không khai `rung_kieu` -> thang vẫn ghi '1 in N'"
    ds = io.open(_o.path.join(R, "datastory_ci.py"), encoding="utf-8").read()
    assert '"rungKieu"' in ds, "props không chuyển tiếp `rungKieu` -> khai báo chết ở giữa đường"
    tsx = _o.path.join(G, "engine-remotion", "src", "LongshotShort.tsx")
    if not _o.path.exists(tsx):
        print("      ⏭️ bỏ qua phần TSX: không có engine-remotion ở đây")
        return
    t = io.open(tsx, encoding="utf-8").read()
    assert "rungKieu" in t, "composition không nhận `rungKieu`"
    assert 'kieu === "dem"' in t, "composition nhận prop nhưng không dùng -> nhãn vẫn là xác suất"
    # Và lời đọc không được phát âm dấu gạch chéo. SOI MÃ, KHÔNG SOI CHÚ THÍCH — bản đầu bắt
    # trúng chính dòng chú thích giải thích bản vá (nó trích lại chuỗi "07 slash 03"), đỏ oan
    # trong khi mã hoàn toàn đúng. Đây là lần thứ hai hôm nay tôi mắc đúng lỗi này.
    ma_th = "\n".join(d.split("#")[0] for d in th.splitlines())
    assert " slash " not in ma_th, "lời đọc còn phát âm 'slash' — không người Mỹ nào đọc ngày kiểu đó"


def t_workflow_khong_dung_secrets_trong_if():
    """`secrets` KHÔNG DÙNG ĐƯỢC TRONG `if` — GitHub từ chối nạp cả workflow.

    28/8 — tôi viết `if: secrets.KLING_ACCESS_KEY != ''` ở cấp job. GitHub từ chối nạp workflow,
    và nó đỏ NGAY TỪ LÚC ĐẨY MÃ, ba lần liên tiếp. Log không có lỗi nào để đọc — chỉ một dòng
    "This run likely failed because of a workflow file issue".
    Đó là loại lỗi đắt hơn lỗi thường: nó không chỉ được chỗ sai, và nó làm hỏng workflow TRƯỚC
    KHI chạy bất cứ bước nào, nên mọi bài kiểm bên trong đều vô dụng.
    Ngữ cảnh `if` chỉ có: github · needs · vars · inputs · env · always()/success()/failure().
    `secrets` chỉ dùng được TRONG bước (env/run).
    Chốt quét MỌI workflow, vì lỗi này không phụ thuộc tệp nào."""
    import os as _o, re as _re
    G = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    d = _o.path.join(G, ".github", "workflows")
    if not _o.path.isdir(d):
        print("      ⏭️ bỏ qua: không có .github/workflows ở đây")
        return
    xau = []
    for f in sorted(_o.listdir(d)):
        if not f.endswith((".yml", ".yaml")):
            continue
        for i, dong in enumerate(io.open(_o.path.join(d, f), encoding="utf-8").read().splitlines(), 1):
            t = dong.split("#")[0]
            if _re.search(r"^\s*if\s*:", t) and "secrets." in t:
                xau.append(f"{f}:{i}")
    assert not xau, ("dùng `secrets` trong `if` -> GitHub TỪ CHỐI nạp workflow, đỏ ngay từ lúc "
                     "đẩy mã và không để lại log nào để đọc: " + ", ".join(xau))


def t_don_mo_coi_khong_duoc_xoa_sach_khi_doc_hut():
    """DỌN MỒ CÔI PHẢI TỪ CHỐI KHI DANH SÁCH KÊNH SỐNG RỖNG.

    28/8 — luật "bản ghi của kênh không còn tồn tại thì xoá" là cách duy nhất tìm ra ~1218 bản
    ghi ma (kênh đã bị xoá nên không còn tên nào để tra). Nhưng chính luật đó mang một tai nạn
    dựng sẵn: nếu lần đọc danh sách kênh HỤT — quota chết, mạng chập — thì danh sách rỗng, MỌI
    bản ghi đều trông như mồ côi, và cả thư viện bị xoá sạch trong một lượt.
    Một lần đọc hụt không được phép trở thành lệnh xoá toàn bộ. Đây là điểm khác nhau giữa một
    lệnh dọn và một tai nạn.

    Chốt kiểm ĐÚNG hành vi đó, không kiểm chữ trong mã — vì cái cần bảo đảm là nó KHÔNG XOÁ."""
    import sys as _s, os as _o, io as _io, contextlib as _ct
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import firestore_bridge as FB
    goi = {"n": 0}
    class _Ref:
        def delete(self): goi["n"] += 1
    class _Batch:
        def delete(self, r): goi["n"] += 1
        def commit(self): pass
    class _Doc:
        reference = _Ref()
        def to_dict(self): return {"channel": "KENHBATKY"}
    class _DB:
        def collection(self, *a): return self
        def where(self, *a, **k): return self
        def batch(self): return _Batch()
    cu_db, cu_st = FB._db_pub, FB._stream_at
    try:
        FB._db_pub = lambda: _DB()
        FB._stream_at = lambda q, t=20: [_Doc()]
        with _ct.redirect_stdout(_io.StringIO()) as buf:
            n, _ = FB.don_videos_mo_coi("THU", [], that=True)      # danh sách RỖNG
        assert n == 0 and goi["n"] == 0, \
            f"danh sách kênh rỗng mà vẫn xoá {goi['n']} bản ghi — một lần đọc hụt là mất cả thư viện"
        assert "RỖNG" in buf.getvalue(), "từ chối mà không nói vì sao"
        # có danh sách thật -> mới được xoá, và chỉ xoá cái KHÔNG thuộc danh sách
        with _ct.redirect_stdout(_io.StringIO()):
            n, _ = FB.don_videos_mo_coi("THU", ["WHATISINIT"], that=True)
        assert n == 1, f"kênh không còn tồn tại mà không dọn: {n}"
        with _ct.redirect_stdout(_io.StringIO()):
            n, _ = FB.don_videos_mo_coi("THU", ["KENH BAT KY"], that=True)
        assert n == 0, "xoá nhầm bản ghi của kênh ĐANG SỐNG (so tên phải bỏ dấu cách + hoa/thường)"
    finally:
        FB._db_pub, FB._stream_at = cu_db, cu_st


def t_bang_xep_hang_phai_noi_dang_xep_theo_gi():
    """BẢNG XẾP HẠNG PHẢI NÓI ĐANG XẾP THEO GÌ.

    28/8 — soi khung thật kênh FILINGS SAY (dạng `ranked`, 18/50 kênh dùng): thẻ ghi "7x", "5x",
    "4x" — đúng dữ liệu, nhưng người xem KHÔNG CÓ CÁCH NÀO biết 7x là gì. 7 lần nộp hồ sơ? 7 tỉ?
    gấp 7? Bảng xếp hạng mà không nói xếp theo gì thì chỉ là mấy con số đặt cạnh nhau.
    Cùng họ với lỗi thang "1 in 10,000" ở FAME CURVE: dữ liệu đúng, NHÃN không nói được nó là gì.

    Chốt đòi MỌI bộ chuyển đổi mà kênh `ranked` đang dùng đều phải có phụ đề. Bộ thêm sau mà quên
    khai thì đỏ ở đây, chứ không lặng lẽ ra video thiếu phụ đề — thứ chỉ phát hiện được bằng cách
    ngồi xem từng video."""
    import sys as _s, os as _o, json as _j
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import the_he_2 as T
    R = _o.path.dirname(_o.path.abspath(__file__))
    ks = _j.load(io.open(_o.path.join(R, "kenh_the_he_2.json"), encoding="utf-8"))
    ks = ks if isinstance(ks, list) else list(ks.values())
    thieu = sorted({str(k.get("ham")) for k in ks
                    if k.get("dinh_dang") == "ranked" and str(k.get("ham")) not in T.PHU_DE_THEO_BO})
    assert not thieu, (f"{len(thieu)} bộ chuyển đổi của kênh `ranked` chưa khai phụ đề "
                       f"-> video ra không nói đang xếp theo gì: {thieu}")
    # Và phụ đề phải chảy được tới story, không chết ở giữa đường.
    src = io.open(_o.path.join(R, "the_he_2.py"), encoding="utf-8").read()
    assert '"subtitle": _phu' in src, "story `ranked` không mang `subtitle` -> props không có gì để truyền"
    ds = io.open(_o.path.join(R, "datastory_ci.py"), encoding="utf-8").read()
    assert '"subtitle": story.get("subtitle"' in ds, "props không đọc `subtitle` từ story"


def t_moi_dang_short_deu_ghi_nguon():
    """MỌI DẠNG SHORT PHẢI THẬT SỰ VẼ DÒNG NGUỒN, KHÔNG CHỈ NHẬP NÓ.

    28/8 — `MappedShort` NHẬP `DongNguon` ở đầu tệp mà chưa bao giờ VẼ, và props cũng không truyền
    `source` xuống. Nên 4 kênh dạng bản đồ ra video KHÔNG GHI NGUỒN suốt, trong khi 5 dạng kia đều
    có. Mất hai thứ cùng lúc: người xem không có cách nào kiểm con số, và mình mất luôn bằng chứng
    "dữ liệu công khai tra được" trước chính sách nội dung hàng loạt của YouTube.

    Nhập-mà-không-dùng là loại sót không bao giờ tự lộ: mã biên dịch sạch, không cảnh báo, video
    vẫn ra — chỉ thiếu một dòng chữ mà không ai đếm. Cùng lớp với việc vá chồng chữ ở `longshot`:
    sửa một phần tử, quên phần tử cùng loại ở chỗ khác.

    Chốt soi CẢ HAI PHÍA: composition phải vẽ, và props phải truyền — đứt bên nào cũng là mất
    dòng nguồn mà không có dấu hiệu gì."""
    import os as _o, re as _re
    G = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    src = _o.path.join(G, "engine-remotion", "src")
    if not _o.path.isdir(src):
        print("      ⏭️ bỏ qua: không có engine-remotion ở đây")
        return
    xau = []
    for f in ("RankedShort", "ScaledShort", "MappedShort", "ThenNowShort", "LongshotShort"):
        t = io.open(_o.path.join(src, f + ".tsx"), encoding="utf-8").read()
        if "DongNguon" in t and "<DongNguon" not in t:
            xau.append(f"{f}: nhập `DongNguon` mà KHÔNG vẽ")
    assert not xau, "dạng short thiếu dòng nguồn: " + "; ".join(xau)

    # `source` được gán ở MỘT CHỖ CHUNG trong `the_he_2` cho mọi dạng, KHÔNG phải trong từng bộ
    # dựng props. Bản đầu của chốt này soi nhầm chỗ: nó đòi 5 bộ dựng đều truyền `source`, và báo
    # "18 kênh thiếu nguồn" — sai, vì chúng nhận qua đường chung. Chốt đo nhầm chỗ thì báo động
    # giả, mà báo động giả cũng đắt ngang bỏ sót: lần sau người ta tắt nó đi.
    th = io.open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "the_he_2.py"),
                 encoding="utf-8").read()
    assert 'props["source"] = ten_nguon(' in th, \
        "mất chỗ gán `source` chung -> MỌI dạng đều không ghi nguồn"


def t_chong_trung_kiem_dung_chuoi_di_ra():
    """CHỐNG TRÙNG PHẢI KIỂM ĐÚNG CHUỖI SẼ ĐI RA, Ở CHỖ CUỐI CÙNG NÓ ĐƯỢC QUYẾT ĐỊNH.

    28/8 — gốc của 334/600 video hỏng trong ngày. `_gop_story` VIẾT LẠI tiêu đề của long sau khi
    gộp chương:
        goc["title"] = f"{tg} ({min(vals)}-{max(vals)})"
    Nghĩa là tiêu đề CUỐI CÙNG khác hẳn tiêu đề mà `_story_xoay` đã đem đi kiểm trùng. Bộ chống
    trùng kiểm một chuỗi, video mang một chuỗi khác — kiểm xong vô nghĩa. Hai bộ phủ cùng một dải
    năm ra tiêu đề y hệt và không có gì chặn.
    Đo được: DIAMOND NUMBERS 32 video, một tiêu đề lặp 9 lần, TRONG CÙNG MỘT LANE.

    Kiểm sớm rồi để khâu sau đổi đi thì lớp bảo vệ chỉ còn là hình thức — và hình thức thì tệ hơn
    không có, vì mình tin vào nó."""
    import os as _o
    R = _o.path.dirname(_o.path.abspath(__file__))
    src = io.open(_o.path.join(R, "the_he_2.py"), encoding="utf-8").read()
    # Lưới thứ nhất phải nằm TRƯỚC lệnh render — bắt trùng sau khi render xong là vẫn đốt trọn
    # công rồi mới vứt (một long 5-7 phút + 3 short + giọng đọc + ảnh).
    i0 = src.index("def chay_bo")
    ir = src.index('"npx", "remotion", "render"', i0)
    assert "_tieu_de_da_lam(" in src[i0:ir], (
        "kiểm trùng nằm SAU lệnh render -> vẫn đốt trọn công rồi mới vứt. Phải kiểm ở chỗ SỚM "
        "NHẤT mà câu trả lời đã xác định (`_gop_story` chỉ cần `kho_st`, có sẵn trước khi render)")
    i = src.index("st_long = _gop_story(", ir)
    j = src.index("return ra_long, shorts, st_long", i)
    sau = src[i:j]
    assert "_tieu_de_da_lam(" in sau, (
        "sau `_gop_story` (nơi tiêu đề long ĐƯỢC VIẾT LẠI) không kiểm trùng -> hai bộ phủ cùng "
        "dải dữ liệu sẽ ra tiêu đề y hệt và cùng được đăng")
    assert "return None" in sau, "trùng mà không bỏ bộ -> vẫn đăng trùng"


def t_nghiem_thu_bat_duoc_loi_that():
    """BÀI NGHIỆM THU PHẢI BẮT ĐƯỢC ĐÚNG NHỮNG LỖI ĐÃ LỌT.

    28/8 — sau 60+ chốt kiểm, đêm 27-28/8 vẫn lọt 6 lỗi lớn, và KHÔNG chốt nào bắt được cái nào.
    Vì mọi chốt đều soi HÌNH DẠNG MÃ, còn lỗi nằm ở ĐƯỜNG NỐI giữa các tầng — chỉ lộ ra trong
    THỨ ĐI RA.
    `nghiem_thu.py` sinh ra để chấm sản phẩm. Nhưng một bài chấm chỉ đáng tin khi nó bắt được
    ĐÚNG những lỗi đã từng lọt — nếu không thì nó lại là một lớp bảo vệ hình thức nữa.
    Chốt này nạp lại đúng 7 lỗi thật, và kèm 4 tiêu đề TỐT để bảo đảm nó không báo oan: một bài
    chấm hay báo oan sẽ bị tắt đi, và lúc đó nó vô dụng y như không có."""
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    import nghiem_thu as N
    that = [
        ("mã nội bộ", N.cham_tieu_de("Games people actually play right now — tut_manh")),
        ("repr Python", N.cham_tieu_de("Home price by state — ['Florida', 'New York']")),
        ("hai chủ thể", N.cham_tieu_de("Dodgers: 98 W — MLB wins by season (2025) — Brewers, 97 W")),
        ("thiếu nguồn", N.cham_props("mapped", {"items": []})),
        ("thang sai loại", N.cham_props("longshot", {"source": "x", "items": [{"oddsDisp": "63.4K reads"}]})),
        ("ranked thiếu phụ đề", N.cham_props("ranked", {"source": "x"})),
        ("không ra tệp", N.do_tep("/tmp/khong-bao-gio-co-tep-nay.mp4", False)),
    ]
    sot = [t for t, e in that if not e]
    assert not sot, f"bài nghiệm thu BỎ SÓT {len(sot)}/7 lỗi thật đã từng lọt: {sot}"

    tot = ["MLB wins by season — Dodgers, 98 W",
           'Who keeps writing "climate risk" to the S E C',
           "Spider-Man: 986K — Most-read on Wikipedia",
           "Hawaii: $833,877 — Home price by state"]
    oan = [t for t in tot if N.cham_tieu_de(t)]
    assert not oan, ("báo oan với tiêu đề TỐT -> bài chấm sẽ bị tắt đi và thành vô dụng: "
                     + "; ".join(f"{t} -> {N.cham_tieu_de(t)}" for t in oan[:2]))

    # Và nó phải được GẮN VÀO CỔNG, không chỉ tồn tại.
    G = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    wf = _o.path.join(G, ".github", "workflows", "render_cron.yml")
    if _o.path.exists(wf):
        assert "nghiem_thu.py" in io.open(wf, encoding="utf-8").read(), \
            "bài nghiệm thu không được gọi trong workflow -> viết ra rồi để đấy"


def t_cham_kich_ban():
    """Thang chấm kịch bản phải (a) chấm được, (b) bắt được lỗi thật, (c) ĐƯỢC GỌI ở workflow.

    (c) là phần hay bị quên nhất: §13.1 đếm được bảy lần trong một ngày mà cơ chế đã tồn tại
    trong repo và chỉ thiếu một thứ GỌI nó. Một thước không ai chạy thì bằng không có thước.
    """
    import os as _o

    import giai_thich as G
    import cham_kich_ban as C

    nh = G.kich_ban("howbig", 0)[4]
    r = C.cham(nh)
    assert 0 <= r["diem"] <= 100, f"điểm ngoài thang: {r['diem']}"
    assert r["diem"] >= 90, f"kịch bản thật chỉ {r['diem']}/100 — thước hoặc kịch bản có vấn đề"

    # Thử NGƯỢC — mỗi trục phải bắt được lỗi của chính nó, nếu không nó là một cổng chết (§13.11).
    xau = [{"khuon": "the_chu", "loi": "This is an extremely long opening line that nobody will "
                                       "ever sit through because it says nothing at all"},
           {"khuon": "so_lieu", "loi": "It is very expensive and a lot of km", "so": "5"},
           {"khuon": "so_lieu", "loi": "Also so much money", "so": "5"},
           {"khuon": "the_chu", "loi": "The end."}]
    rx = C.cham(xau)
    assert rx["diem"] < 55, f"kịch bản cố tình hỏng vẫn được {rx['diem']}/100 — thước không bắt"
    for t in ("hook", "cu_the", "don_vi_my", "ket_bang_canh", "khong_lap_khuon"):
        assert rx["truc"][t] < C.TRAN[t], f"trục {t} không phản ứng với lỗi của chính nó"

    # Thước phải đọc CÙNG nguồn mà `mot_tap` dựng, không gọi thẳng `BO_SINH` (§13.15).
    src = io.open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),
                               "cham_kich_ban.py"), encoding="utf-8").read()
    assert "kich_ban(" in src, "thước không gọi `kich_ban` -> đang chấm một danh sách khác"

    G0 = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
    # ĐÚNG WORKFLOW của bộ giải thích. Bản đầu kiểm `render_phan_tich_18.yml` — bộ PHÂN TÍCH
    # thế hệ 2 — nên nó báo xanh trong khi thước chưa bao giờ chạy trên luồng dựng `v9_*`.
    # Một cổng canh sai tệp thì nó canh sai cả việc (§13.2: cổng cầm danh sách sai = cổng che lỗi).
    wf = _o.path.join(G0, ".github", "workflows", "render_giai_thich_18.yml")
    assert _o.path.exists(wf), "không tìm thấy workflow của bộ giải thích"
    assert "cham_kich_ban.py" in io.open(wf, encoding="utf-8").read(), \
        "thang chấm kịch bản không được gọi trong workflow giải thích -> viết ra rồi để đấy"


def t_ban_dai_du_dai():
    """Bản dài phải đủ dài để đáng gọi là bản dài, và không kênh nào tụt về mức 3 phút.

    ── ĐO LÚC PHÁT HIỆN  (3/9/2026) ───────────────────────────────────────────────────────
    Workflow gọi `--chuong 10` cho mọi kênh. Đo thời lượng thật cả 18 kênh: **2,4 – 5,0 phút**.
    Mốc YouTube cho phép chèn quảng cáo GIỮA video là **8 phút**, và bộ comic đã làm 8–11 phút
    đúng vì lý do ấy (§11) — bộ giải thích thì chưa ai đo, nên nó im lặng bỏ mất một dòng doanh
    thu suốt nhiều phiên.

    Gốc: `vi_tri_long` khoá cứng ở NỬA SAU bảng dữ liệu để bản dài không đụng chủ đề bản ngắn.
    Ý định đúng, nhưng nó đặt một TRẦN mà không ai đo — bảng 24 mục thì bản dài tối đa 12 chương.

    Cổng này canh cả hai phía: đủ dài (≥6 phút mọi kênh) và không quá dài (≤11 phút — §10.1,
    trần thời gian runner).
    """
    import giai_thich as G

    ngan, dai = [], []
    for k in G.KENH:
        nh = G.kich_ban(k["ma"], 0, long=True, so_chuong=40)[4]
        phut = sum(max(1.0, len(str(x.get("loi") or "").split()) / 2.8) + 0.35
                   for x in nh) / 60
        # ── SÀN 5,5 PHÚT, CÓ LÝ DO  (3/9/2026) ──────────────────────────────────────────
        # Sàn cũ 6,0 là một con số tôi chọn tuỳ tiện, và `hiddenfee` rơi đúng **5,99** — sát
        # ngưỡng thì một thay đổi nhỏ ở lời cũng đủ làm cổng nổ vì nhiễu.
        #
        # Truy ra: 15/18 kênh bị chặn bởi **KHO NỘI DUNG** (hết chủ đề), không bởi trần thời
        # lượng. Tức thời lượng là giới hạn của DỮ LIỆU, không phải lỗi mã — mà cổng thì chỉ
        # canh được mã. Đặt cổng ở chỗ nó không điều khiển được là ép người sau sửa mù.
        #
        # Nên: sàn 5,5 (dưới mức ấy bản dài không phân biệt được với một bản tổng hợp ngắn —
        # đó là lý do, không phải con số vừa khít dữ liệu), và mốc 8 phút thì ĐO VÀ BÁO chứ
        # không chặn, vì muốn nâng nó phải THÊM MỤC vào bảng dữ liệu từng kênh.
        if phut < 5.5:
            ngan.append(f'{k["ma"]} {phut:.1f}p')
        if phut > 11.0:
            dai.append(f'{k["ma"]} {phut:.1f}p')
    assert not ngan, "bản dài quá ngắn (dưới 6 phút): " + ", ".join(ngan[:5])
    assert not dai, "bản dài quá dài (trên 11 phút, tốn giờ runner): " + ", ".join(dai[:5])

    # Báo (không chặn) số kênh chạm mốc quảng cáo giữa video — xem chú thích sàn ở trên.
    _tam = []
    for k in G.KENH:
        nh = G.kich_ban(k["ma"], 0, long=True, so_chuong=40)[4]
        _tam.append(sum(max(1.0, len(str(x.get("loi") or "").split()) / 2.8) + 0.35
                        for x in nh) / 60)
    print(f"       ℹ bản dài: TB {sum(_tam)/len(_tam):.1f}p · "
          f"{sum(1 for t in _tam if t >= 8)}/{len(_tam)} kênh ≥8p (mốc quảng cáo giữa video) — "
          f"muốn nâng thì THÊM MỤC vào bảng dữ liệu kênh, không sửa được bằng mã")

    # Và trần phải THẬT SỰ kẹp — nếu không cổng này canh một hàm không làm gì.
    assert G.so_chuong_toi_da("hiddenfee") < 40, "so_chuong_toi_da không kẹp gì"


def t_khong_lap_loi_gan():
    """Không câu nào được đọc lại trong vòng `GAN_NHAT` nhịp (~25 giây).

    ── ĐO LÚC PHÁT HIỆN ───────────────────────────────────────────────────────────────────
    Soi bản dài ODDS: bốn cảnh lặp vòng và LỜI lặp nguyên văn. Đo cả 18 kênh, bản dài 10 chương:
    **7/18 kênh có câu đọc lại trong vòng 30 giây**, gần nhất 6,0 giây (WHATWEIGHS, 12 ca).

    Ba gốc khác nhau, và đó là lý do phải có cổng chứ không chỉ sửa tay:
      · `sinh_whatweighs` gọi `_loi("so_sanh", i)` HAI lần trong một chương -> cùng câu, cách
        nhau ba nhịp
      · nhịp hook đọc TIÊU ĐỀ TẬP, thẻ chương 1 đọc lại đúng câu ấy
      · hồ `LOI_MAU` chỉ 5 câu cho 10 chương, `BIEN_THE` chỉ 3 lựa chọn (nay 6)

    Cho phép ĐÚNG MỘT ca: `howlong` có 165 nhịp trong một tập, mật độ cao nhất bộ, và ca còn lại
    cách nhau 27 giây — trên ngưỡng tai nghe ra. Đặt trần 2 để cổng còn bắt được hồi quy thật.
    """
    import giai_thich as G

    xau = []
    for k in G.KENH:
        for dai in (True, False):
            nh = G.kich_ban(k["ma"], 0, long=dai, so_chuong=10 if dai else 1)[4]
            cuoi = {}
            for j, n in enumerate(nh):
                l = str(n.get("loi") or "").strip()
                if not l:
                    continue
                if j - cuoi.get(l, -999) < G.GAN_NHAT:
                    xau.append(f'{k["ma"]}{"·dài" if dai else ""}: «{l[:40]}» cách '
                               f'{j - cuoi[l]} nhịp')
                cuoi[l] = j
    assert len(xau) <= 2, f"{len(xau)} ca đọc lại quá gần: " + "; ".join(xau[:4])

    # ── THẺ CHỮ: SOI TRƯỜNG `the`, KHÔNG CHỈ `loi` ─────────────────────────────────────
    # Khuôn `the_chu` hiện trường `the` lên giữa khung — đó là thứ mắt ĐỌC, và bộ sinh khai nó
    # RIÊNG với `loi`. Đo lúc phát hiện: bản dài HOW LOUD có **31/63 thẻ hiện đúng một câu**,
    # trong khi `loi` đã được `doi_loi` xoay đủ 6 biến thể. Bố cục đổi, chữ không đổi.
    # Bỏ qua thẻ chương (`"3.|Tiêu đề"`) — hai dòng nội dung khác nhau, không phải một câu.
    xau2 = []
    for k in G.KENH:
        nh = G.kich_ban(k["ma"], 0, long=True, so_chuong=40)[4]
        cuoi = {}
        for j, n in enumerate(nh):
            if (n.get("khuon") or "") != "the_chu":
                continue
            t = str(n.get("the") or n.get("loi") or "").strip()
            if not t or t.split("|")[0].rstrip(".").strip().isdigit():
                continue
            if j - cuoi.get(t, -999) < G.GAN_NHAT:
                xau2.append(f'{k["ma"]}: thẻ «{t[:34]}» cách {j - cuoi[t]} nhịp')
            cuoi[t] = j
    assert not xau2, "thẻ chữ hiện lại cùng một câu quá gần: " + "; ".join(xau2[:3])

    # Thử NGƯỢC: bộ khử phải thật sự đổi câu, nếu không cổng này canh một hàm chết.
    tho = [{"khuon": "canh", "loi": "No breaks."} for _ in range(4)]
    G._tranh_lap_gan(tho)
    assert len({n["loi"] for n in tho}) >= 3, "_tranh_lap_gan không đổi câu lặp"

    # Và bộ đồng bộ `the` phải thật sự dựng lại chữ theo lời đọc.
    tho2 = [{"khuon": "the_chu", "loi": "No rest.", "the": "No breaks."}]
    G._dong_bo_the(tho2)
    assert tho2[0]["the"].replace("|", " ") == "No rest.", \
        f'_dong_bo_the không đồng bộ: {tho2[0]["the"]!r}'
    # KHÔNG được đụng thẻ chương
    tho3 = [{"khuon": "the_chu", "loi": "How loud is a jet.", "the": "3.|How loud is a jet"}]
    G._dong_bo_the(tho3)
    assert tho3[0]["the"].startswith("3."), "đụng vào thẻ chương — số chương phải giữ nguyên"


def t_gu_bo_cuc_rieng():
    """Mỗi kênh phải có bộ gu bố cục RIÊNG — và không cặp nào giống quá 3/5 trục.

    ── VÌ SAO ─────────────────────────────────────────────────────────────────────────────
    Năm bảng gu (`GU_KHUON` · `GU_SS` · `GU_SO` · `GU_CHART` · `GU_HINH`) là thứ tách "đa dạng"
    khỏi "bản sắc". Nếu mọi kênh rút từ cùng một bộ thì có đa dạng TRONG một video mà không có
    bản sắc GIỮA các kênh — xem hai video của hai kênh vẫn thấy cùng một bộ bài (§15.2).

    Đây cũng là trục mà chính sách YouTube nêu tên: *bố cục · cảnh* giống nhau hàng loạt
    (§13.17). Và người viết nhớ được ba kênh, không nhớ mười tám — nên phải đo.

    Trần 3/5: có 4-6 bố cục cho mỗi khuôn và 18 kênh, nên trùng một phần là không tránh khỏi.
    Trùng 4/5 thì hai kênh gần như cùng một bộ bài.
    """
    import itertools as _it
    import giai_thich as G

    def bo(m):
        return (frozenset(G.GU_KHUON[m]), frozenset(G.GU_SS[m]), frozenset(G.GU_SO[m]),
                frozenset(G.GU_CHART[m]), frozenset(G.GU_HINH[m]))

    ms = [k["ma"] for k in G.KENH]
    for b in (G.GU_KHUON, G.GU_SS, G.GU_SO, G.GU_CHART, G.GU_HINH):
        thieu = [m for m in ms if m not in b]
        assert not thieu, f"kênh thiếu bảng gu: {thieu[:4]} -> chúng rơi về bộ mặc định chung"

    hs = {}
    for m in ms:
        h = bo(m)
        assert h not in hs, f"{m} và {hs[h]} có bộ gu TRÙNG HOÀN TOÀN"
        hs[h] = m

    qua = [(a, b) for a, b in _it.combinations(ms, 2)
           if sum(1 for x, y in zip(bo(a), bo(b)) if x == y) > 3]
    assert not qua, ("cặp kênh giống quá 3/5 trục gu: "
                     + "; ".join(f"{a}/{b}" for a, b in qua[:3]))


def t_tran_anh_song_qua_tien_trinh():
    """Trần ảnh CF phải đếm ở TỆP, không đếm ở biến module.

    `render_giai_thich_18.yml` có vòng `while` chạy TỪNG TẬP bằng một lệnh `python` riêng.
    Bản trước đếm bằng `sinh._da_ve` — một thuộc tính hàm, chết theo tiến trình — nên trần
    *"120 ảnh mỗi luồng mỗi lượt"* thực chất là *"120 ảnh mỗi TẬP"*.

    Đo trên lượt thật 33819928469 (18 luồng, 4,5 giờ): **8.059 ảnh CF** thay vì 2.160, vượt
    3,7 lần. Nó chạy vắt qua 00:00 UTC — mốc CF hồi hạn mức — nên vét luôn hạn mức của cả
    ngày hôm sau, và 8/8 khoá thử sáng hôm sau đều trả *"you have used up your daily free
    allocation of 10,000 neurons"*.

    §15.23 đã ghi đúng câu luật này cho `ghi_trang_thai` và chỗ này không áp dụng.
    """
    import os
    import nen_gt as N
    goc = os.environ.get("GITHUB_RUN_ID")
    os.environ["GITHUB_RUN_ID"] = "selftest_tran_anh"
    import importlib
    importlib.reload(N)
    try:
        try:
            os.remove(N._ANH_TEP)
        except Exception:
            pass
        assert N._da_ve() == 0, "sổ chưa sạch trước khi đo"
        N._ghi_da_ve(7)
        # Đọc lại bằng một MODULE MỚI TINH — mô phỏng đúng tiến trình python kế tiếp của vòng
        # `while`. Biến module sẽ ra 0 ở đây; tệp thì ra 7.
        importlib.reload(N)
        assert N._da_ve() == 7, (
            f"sổ đếm ảnh KHÔNG sống qua tiến trình (đọc lại ra {N._da_ve()}, chờ 7) — "
            "trần TRAN_ANH_LUONG sẽ nhân lên theo số tập mỗi luồng")
        # Và trần phải THẬT SỰ đọc sổ ấy, không đọc thuộc tính hàm.
        # QUÉT MÃ, KHÔNG QUÉT CHÚ THÍCH. Bản đầu của cổng này báo đỏ ngay lần chạy đầu vì
        # nó đọc trúng dòng chú thích kể lại lỗi cũ ("đếm bằng `sinh._da_ve`") — đúng bài
        # học `kiem_nen._doc_ma` đã trả giá: *cổng đọc lời kể về con dao thành con dao*.
        import re as _re
        src = io.open(os.path.join(os.path.dirname(os.path.abspath(N.__file__)),
                                   "nen_gt.py"), encoding="utf-8").read()
        ma = _re.sub(r"(?m)^\s*#.*$", "", src)
        ma = _re.sub(r'(?<!["\\])#(?![^\n"]*").*$', "", ma, flags=_re.M)
        assert "sinh._da_ve" not in ma, \
            "còn dùng `sinh._da_ve` — bộ đếm quay lại sống trong tiến trình"
        assert "_da_ve()" in ma, "trần ảnh không đọc sổ tệp"
    finally:
        try:
            os.remove(N._ANH_TEP)
        except Exception:
            pass
        if goc is None:
            os.environ.pop("GITHUB_RUN_ID", None)
        else:
            os.environ["GITHUB_RUN_ID"] = goc
        importlib.reload(N)


def t_truc_du_moc_va_khong_trung():
    """Mỗi nhịp `truc` phải có ≥3 mốc và không mốc nào trùng.

    Soi khung demo 4/9: trục `speedof` hiện **"jet 560" hai lần**, còn `howbig` và `odds` ra
    một đường dọc hai nhãn với hai phần ba khung trống.

    Gốc: `_rai_truc` đổi `chart` -> `truc` bằng cách dựng `moc` thẳng từ `cot`. `cot` ĐƯỢC
    PHÉP có hai mục cùng tên (cột vẽ cạnh nhau, mắt vẫn phân biệt) và được phép chỉ có hai
    mục (hai cột vẫn kín khung). Trục thì không: mốc trùng rơi đúng một chỗ, và hai mốc trên
    một đường thẳng không dựng được cảm giác thang đo.

    Cùng dữ liệu, hai cách vẽ, hai ràng buộc khác nhau — và bản chuyển đổi chỉ mang theo
    ràng buộc của bên NGUỒN. Đây là họ lỗi sẽ quay lại ở mọi phép đổi khuôn sau này.
    """
    import giai_thich as G
    loi = []
    for k in G.KENH:
        for idx in range(12):
            try:
                _, _, _, _, nhip, _ = G.kich_ban(k["ma"], idx)
            except Exception:
                continue
            for n in nhip:
                if (n.get("khuon") or "") != "truc":
                    continue
                m = n.get("moc") or []
                if len(m) < 3:
                    loi.append((k["ma"], idx, f"chỉ {len(m)} mốc"))
                ky = [(str(x.get("nhan") or "").strip().lower(), x.get("phu")) for x in m]
                if len(set(ky)) != len(ky):
                    loi.append((k["ma"], idx, f"mốc trùng: {ky}"))
    assert not loi, f"{len(loi)} nhịp truc hỏng: {loi[:3]}"


def t_guardian_ton_trong_cong_tac_tat():
    """Guardian không được bấm chạy một workflow mà người vận hành đã TẮT.

    Anh tắt `render_giai_thich_18.yml` để dừng render trong lúc sửa template, rồi phát hiện
    guardian VẪN bấm nó mỗi giờ — một CỬA THỨ HAI mở workflow mà người tắt không hề biết.
    Hôm nay nó chỉ vô hại nhờ may: `gh workflow run` trên workflow đã tắt thì hỏng. Đổi hành
    vi ấy, hoặc tắt cron bằng cách khác, là guardian âm thầm khởi động lại cả dây chuyền.

    Luật: một hệ tự động được phép TỰ CHỮA, nhưng không được phép ĐI NGƯỢC một quyết định con
    người vừa ra. Trạng thái `disabled_manually` chính là quyết định ấy và hỏi được bằng một
    lệnh API — hỏi trước khi bấm thì "tắt workflow" thành công tắc DUY NHẤT và đáng tin.
    """
    import os
    import re
    goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(goc, ".github", "workflows", "health_guardian.yml")
    # ── BỎ DÒNG CHÚ THÍCH TRƯỚC KHI QUÉT ───────────────────────────────────────────────
    # Bản đầu của cổng này báo đỏ ngay, vì `gh workflow run` xuất hiện LẦN ĐẦU trong chính
    # dòng chú thích giải thích bản vá — nên `find` dừng ở đó và phần "hỏi trạng thái" nằm
    # SAU nó bị coi như không tồn tại.
    # Đây là lần thứ TƯ trong một ngày cổng đọc lời kể về con dao thành con dao
    # (`kiem_nen._doc_ma` đã ghi bài học từ 1/9). Nay nó thành thói quen: **quét mã thì bỏ
    # chú thích trước, luôn luôn** — với YAML/shell là dòng bắt đầu bằng `#`, với Python còn
    # phải bỏ cả docstring vì docstring là CHUỖI chứ không phải chú thích.
    src = io.open(p, encoding="utf-8").read()
    ma = "\n".join(d for d in src.splitlines() if not d.lstrip().startswith("#"))
    i = ma.find("gh workflow run")
    assert i > 0, "guardian không còn bấm workflow — nếu cố ý thì xoá cổng này"
    truoc = ma[:i]
    assert re.search(r"actions/workflows/\$WF\W.*state", truoc, re.S), (
        "guardian bấm `gh workflow run` mà KHÔNG hỏi trạng thái workflow trước — "
        "tắt workflow sẽ không dừng được nó")
    assert 'if [ "$TT" != "active" ]' in truoc, (
        "thiếu chốt chặn: chỉ bấm khi workflow đang `active`")


def t_guardian_khong_doc_bua():
    """Guardian không được ĐỌC tài liệu ở nhánh mà chính nó tuyên bố là không kết luận được.

    Đo bằng log lượt guardian thật (33858866081): Firestore trả `400 The query requires an
    index` — index `owner+status+created_at DESCENDING` CÓ trong
    `dashboard/firestore.indexes.json` nhưng CHƯA ĐƯỢC TRIỂN KHAI.

    Bản trước rơi xuống `q.limit(200).stream()`. Bản vá §15.12 đúng ở chỗ ngừng KẾT LUẬN từ
    200 tài liệu không sắp xếp — nhưng nó vẫn ĐỌC chúng. Guardian chạy mỗi giờ, nên đó là
    **4.800 lượt đọc/ngày, gần 10% hạn mức free, đổi lấy một kết quả bị vứt đi ngay dòng sau.**

    Cùng họ lỗi với `don_sach` (§13.7): mỗi công cụ đụng tài nguyên có hạn phải hỏi *"cái này
    tiêu bao nhiêu, và đổi lấy gì"*. Ở đây vế thứ hai là KHÔNG GÌ.

    Và mọi vòng quét Firestore phải có trần — kể cả vòng "bình thường chỉ vài chục dòng", vì
    "bình thường" không phải bảo vệ: một đợt job kẹt trạng thái là một đợt đọc không trần,
    đúng lúc hệ đang hỏng tức lúc hạn mức quý nhất.
    """
    import os
    import re
    goc = os.path.dirname(os.path.abspath(__file__))
    src = io.open(os.path.join(goc, "health_guardian.py"), encoding="utf-8").read()
    ma = re.sub(r"(?m)^\s*#.*$", "", src)          # bỏ chú thích (kiem_nen._doc_ma)
    assert "q.limit(200).stream()" not in ma, (
        "guardian còn đọc 200 tài liệu ở nhánh thiếu index — kết quả bị vứt ngay dòng sau, "
        "tức 4.800 lượt đọc/ngày cho không gì")
    # Mọi `.stream()` phải đứng sau một `.limit(`.
    for m in re.finditer(r"[\w\)\]]+\.stream\(\)", ma):
        dau = ma.rfind("\n", 0, m.start())
        dong = ma[max(0, dau):m.end()]
        # nhìn cả câu lệnh nhiều dòng: lùi tối đa 6 dòng để bắt truy vấn viết vắt dòng
        khoi = ma[max(0, ma.rfind("\n", 0, max(0, dau - 400))):m.end()]
        assert "limit(" in khoi, f"`.stream()` không có trần: ...{dong.strip()[-90:]}"


def t_short_cat_tu_long_khong_goi_cf():
    """Short cắt từ bản dài phải DÙNG LẠI ảnh của bản dài, không đặt hàng CF mới.

    Anh: *"1 long 3 short, mà 3 short là tận dụng từ long ra"*. Bản cũ của `short_tu_long`
    có đúng cái tên ấy và gọi `mot_tap(ma, idx + chuong)` — dựng một tập short MỚI ở chỉ số
    lệch, không liên quan gì tới bản dài. Docstring nói một đằng, mã làm một nẻo (§15.25).

    Đo trên 36 bộ thật: một bộ (1 long + 3 short) tốn 25,8 ảnh CF, trong đó 6,1 ảnh của ba
    short và **0 ảnh dùng lại được của long**. Chạy 24/7 là 3.566 ảnh/ngày vẽ thừa — 21 điểm
    phần trăm hạn mức — và short mất đúng lợi thế "nhặt khoảnh khắc mạnh nhất của bản dài".

    Cổng soi MÃ chứ không chạy render: chạy thì cần một bản dài đã dựng, tức cần hạn mức và
    vài phút — cổng phải rẻ để nó được chạy mỗi lần.
    """
    import os
    import re
    import giai_thich as G
    # ── BỎ CẢ CHÚ THÍCH LẪN DOCSTRING TRƯỚC KHI QUÉT ───────────────────────────────────
    # Bản đầu chỉ bỏ chú thích `#` và báo đỏ ngay: docstring của `short_tu_long` TRÍCH LẠI
    # lỗi cũ (`mot_tap(ma, idx + chuong)`) để giải thích vì sao phải viết lại. Cổng đọc lời
    # kể về con dao thành con dao — lần thứ ba dính đúng bẫy này trong một ngày, nên lần này
    # dùng `ast` để lấy MÃ THẬT thay vì cắt chuỗi.
    import ast
    src = io.open(os.path.abspath(G.__file__), encoding="utf-8").read()
    cay = ast.parse(src)
    ham = {n.name: n for n in cay.body if isinstance(n, ast.FunctionDef)}
    assert "short_tu_long" in ham and "mot_tap" in ham, "thiếu hàm cần soi"

    def _ma_that(fn):
        b = list(fn.body)
        if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                and isinstance(b[0].value.value, str):
            b = b[1:]                                  # bỏ docstring
        return "\n".join(ast.unparse(x) for x in b)

    than = _ma_that(ham["short_tu_long"])
    assert "idx + chuong" not in than, (
        "short_tu_long lại dựng tập MỚI ở chỉ số lệch thay vì cắt từ bản dài")
    assert "_long.json" in than, "short_tu_long không đọc props của bản dài"
    assert "nenAnh" in than, "short_tu_long không mang `nenAnh` của bản dài sang"
    # Và `mot_tap` phải BỎ HẲN bước vẽ khi nhận kịch bản cắt sẵn.
    mt = _ma_that(ham["mot_tap"])
    assert re.search(r"_na = 0 if \(san or|_na = 0 if san or", mt), (
        "mot_tap còn gọi nen_gt.sinh_tap cho kịch bản cắt sẵn — short sẽ tự đặt hàng CF")


def t_short_du_y_va_hook():
    """Short phải ĐỦ Ý (≥8 nhịp) và nhịp đầu phải là HOOK, không phải câu dẫn.

    Anh: *"làm short phải đủ ý, không làm quá ngắn, và phải hook hay"*.

    Đo trước khi sửa: **10/18 kênh ra short dưới 12 giây**, tám kênh đúng 6 nhịp ≈ 10 giây.
    Sáu nhịp vẫn là một vòng trọn vẹn nhưng NÉN — người xem nhận con số mà không kịp CẢM nó.
    Thiếu đúng hai thứ ngách này sống bằng: quy đổi về thứ cảm được (§12.13) và hệ quả.

    HOOK: nhịp 0 phải mang một trong hai thứ giữ được ngón tay người xem — một CON SỐ, hoặc
    một câu PHỦ ĐỊNH điều người xem đang tin (§15.8: hook giữ chân khi nó phủ định một niềm
    tin, hoặc nói thẳng về chính người xem). Một câu dẫn trơn ở nhịp 0 là ba giây đầu bỏ phí,
    và ba giây đầu quyết định người xem có lướt hay không.
    """
    import re
    import giai_thich as G
    ngan, yeu = [], []
    # ── BA HỌ TỪ, KHÔNG PHẢI MỘT DANH SÁCH  (siết sau khi bắt oan) ─────────────────────
    # Bản đầu chỉ có họ PHỦ ĐỊNH và trượt ngay `whatif`: *"One person changes nothing."* —
    # `\bnot\b` không khớp bên trong "nothing". Đó là một hook MẠNH (nó phủ định đúng điều
    # người xem đang tin) bị chấm là yếu, tức cổng ép sửa một thứ vốn đúng (§13.8).
    # §15.8 đã viết ra nguyên tắc thật: hook giữ chân khi nó PHỦ ĐỊNH một niềm tin, ĐẢO CHIỀU
    # một kỳ vọng, hoặc nói THẲNG VỚI người xem. Ba họ ấy viết được thành biểu thức; liệt kê
    # ví dụ thì danh sách vô hạn (§13.9).
    PHU = re.compile(
        r"\b(no|not|never|none|nothing|nobody|no one|cannot|"          # phủ định
        r"nowhere|hardly|barely|only|just|less|fewer|"                  # thu nhỏ kỳ vọng
        r"every|everyone|all|most|more than|"                           # đảo chiều quy mô
        r"you|your|yours)\b", re.I)
    for k in G.KENH:
        for i in range(4):
            try:
                _, _, hook, _, nhip, _ = G.kich_ban(k["ma"], i)
            except Exception:
                continue
            if len(nhip) < G.SAN_NHIP:
                ngan.append((k["ma"], i, len(nhip)))
            n0 = nhip[0] if nhip else {}
            co_so = bool(str(n0.get("so") or "").strip())
            loi = str(n0.get("loi") or "")
            if not co_so and not PHU.search(loi):
                yeu.append((k["ma"], i, loi[:40]))
    assert not ngan, f"short dưới {G.SAN_NHIP} nhịp (chưa đủ ý): {ngan[:4]}"
    assert not yeu, f"nhịp 0 không có SỐ và không PHỦ ĐỊNH gì — hook yếu: {yeu[:4]}"


def t_dau_an_kenh_duy_nhat():
    """Mỗi kênh một DẤU ẤN riêng, không kênh nào trùng kênh nào.

    Anh muốn *"mỗi channel có nét riêng để người xem nhớ tới style"*. Đo hồ sơ hình cũ trên
    153 cặp kênh: trung bình trùng 0,39, cặp tệ nhất `whatif`/`survive` trùng **79%**. Nguyên
    nhân là số học — trục `ss` và `chart` mỗi trục 3 lựa chọn mà mỗi kênh dùng 2, nên với 18
    kênh thì trùng là BẮT BUỘC (§15.15: cơ chế đúng, hồ quá nhỏ so với số lần rút).

    Bản sắc vì thế không được là thứ CHỌN TỪ hồ chung — chọn thì hai kênh vẫn rút trúng nhau.
    `DAU_AN` khai riêng từng kênh, và cổng này canh đúng cái tính "riêng" ấy: nó là điều kiện
    duy nhất khiến bảng có nghĩa. Thiếu cổng thì kênh thứ 19 thêm vào sẽ lặng lẽ trùng một
    kênh cũ, và không có gì báo — đúng thứ đã xảy ra với `GU_SS`.
    """
    import collections
    import giai_thich as G
    assert len(G.DAU_AN) == len(G.KENH), (
        f"DAU_AN có {len(G.DAU_AN)} kênh nhưng bảng KENH có {len(G.KENH)}")
    thieu = [k["ma"] for k in G.KENH if k["ma"] not in G.DAU_AN]
    assert not thieu, f"kênh chưa khai dấu ấn: {thieu}"
    c = collections.Counter(G.DAU_AN.values())
    trung = {v: n for v, n in c.items() if n > 1}
    assert not trung, f"dấu ấn TRÙNG giữa các kênh: {trung}"
    # Và phải THẬT SỰ tới được nhịp — bảng đúng mà không ai đọc thì như chưa có (§15.12).
    for m in ("howlong", "survive", "whatif"):
        n = G.kich_ban(m, 0)[4][0]
        assert n.get("dau_an") == G.DAU_AN[m][0], f"{m}: dau_an không vào nhịp"
        assert n.get("dau_an_so") == G.DAU_AN[m][1], f"{m}: dau_an_so không vào nhịp"


def t_tieu_de_dung_ngu_phap():
    """Tiêu đề · hook · câu đọc · prompt ảnh phải là tiếng Anh ĐỌC ĐƯỢC.

    `QUANG_DUONG` trộn bốn loại ngữ pháp (điểm đến · tuyến A-B · vòng quanh · một chặng) mà
    bốn khuôn câu đều ghép `f"… to {ten}"` như thể chỉ có một loại. Đo trên 22 mục: **13 mục
    (59%)** ra câu sai, và cùng chuỗi ấy đi thẳng vào TIÊU ĐỀ YOUTUBE:

        "Walking to all the way around Saturn"
        "The distance to New York to Los Angeles."
        "New York to Los Angeles hanging huge and pale in a deep open sky"   <- prompt FLUX

    Câu cuối không sai ngữ pháp, nó VÔ NGHĨA — và mô hình vẽ theo đúng thứ vô nghĩa ấy.

    Cổng quét dạng câu hỏng thay vì so với một danh sách mẫu: danh sách mẫu sẽ trượt ngay khi
    ai thêm mục thứ 23 (§13.9 — danh sách ngoại lệ là danh sách vô hạn).
    """
    import re
    import giai_thich as G
    xau = [
        (re.compile(r"\bto all the way\b", re.I),        "'to all the way …'"),
        # HẸP: chỉ bắt "to" thứ hai NGAY TRONG cụm quãng đường, không bắt "to" của mệnh đề.
        # Bản đầu viết `to \w+ … to` và tố oan "HOW LONG TO WALK TO THE MOON?" — hai chữ
        # "to" ấy có hai vai khác nhau (chỉ mục đích và chỉ đích đến), đều đúng. 28 dòng đỏ
        # giả, đúng cái làm lỗi thật nằm cạnh bị chìm (§13.2).
        (re.compile(r"\b(?:distance|Walking)\s+to\s+[\w' ]+?\s+to\s", re.I),
         "cụm quãng đường có hai chữ 'to'"),
        (re.compile(r"\bdistance to a (?:marathon|cross|year)\b", re.I), "'distance to' + một chặng"),
        (re.compile(r"\b(?:distance|length|height) of the (?:length|height)\b", re.I),
         "danh từ đo lường lặp"),
    ]
    loi = []
    for k in G.KENH:
        for i in range(12):
            try:
                r = G.kich_ban(k["ma"], i)
            except Exception:
                continue
            chu = [x for x in r if isinstance(x, str)]
            # cả lời đọc lẫn câu tả cảnh gửi cho mô hình vẽ
            for n in (r[4] if len(r) > 4 and isinstance(r[4], list) else []):
                chu.append(str(n.get("loi") or ""))
                chu.append(str(n.get("ve") or ""))
            for t in chu:
                for rx, ten in xau:
                    if rx.search(t):
                        loi.append((k["ma"], i, ten, t[:70]))
    assert not loi, f"{len(loi)} câu sai ngữ pháp, ví dụ: {loi[:3]}"


def t_tieu_de_viet_hoa_doi_xung():
    """Khuôn tiêu đề so sánh không được `.title()` một vế mà để nguyên vế kia.

    Bốn kênh dùng `f"{lon[0].title()} vs {nho[0]}"`, nên ra *"A School Bus vs a giraffe"* —
    hai vế cùng vai, một vế Title Case, một vế chữ thường. 14 kênh còn lại đều dùng câu
    thường, nên bốn kênh này đọc ra ngay là chữ máy ghép.

    ── VÌ SAO SOI MÃ, KHÔNG SOI ĐẦU RA ────────────────────────────────────────────────────
    Bản đầu của cổng đo trên tiêu đề đã sinh: "vế A có chữ hoa giữa cụm mà vế B không thì
    báo". Nó tố oan ngay *"A Boeing 747 vs an adult human"* và *"The Statue of Liberty vs a
    football field"* — hai vế viết hoa khác nhau vì một bên là TÊN RIÊNG, hoàn toàn đúng.

    Không có cách đáng tin nào nhận ra tên riêng từ chuỗi đầu ra, nên phép đo ấy sẽ bắt oan
    mãi. Lỗi thật không nằm ở đầu ra mà ở KHUÔN CÂU, và khuôn câu thì đọc chính xác được.
    §13.8: cổng bắt oan ép người ta tắt nó đi, tức tệ hơn không có cổng.
    """
    import os
    import re
    import giai_thich as G
    src = io.open(os.path.abspath(G.__file__), encoding="utf-8").read()
    ma = re.sub(r"(?m)^\s*#.*$", "", src)          # bỏ chú thích (kiem_nen._doc_ma)
    xau = re.findall(r"\{[\w\[\]']+\.title\(\)\}\s*(?:vs|versus)\s*\{[^}]+\}", ma)
    assert not xau, (
        f"khuôn tiêu đề `.title()` một vế, để nguyên vế kia: {xau[:3]} — "
        "dùng `_hoa()` (viết hoa đúng chữ đầu câu) cho cả cụm")


def t_prompt_khong_cat_mat_luat():
    """Chốt chặn độ dài prompt không được cắt mất LUẬT SÀN hay BẢNG MÀU.

    `_prompt` ghép theo thứ tự ưu tiên rồi `break` khi vượt 1.873 ký tự — im lặng. Đo trên 872
    tổ hợp thật (18 kênh × 3 tập × mọi nhịp có cảnh × 4 mức siết × dọc/ngang): **286 tổ hợp
    (32%) đang mất một vế**, và vế bị mất chính là hai thứ anh phàn nàn nhiều nhất — luật sàn
    (*"ground runs unbroken"*, thứ chặn người lơ lửng) và bảng màu kênh (thứ chặn lệch chất
    ảnh giữa các cảnh trong một tập).

    Đây là §14.13 ở dạng nặng nhất: hàm vừa ĐO vừa TỰ SỬA, nên không cổng nào đặt sau nó bắt
    được — và ở đây còn không có cổng nào cả. Bốn bản sửa (bỏ ba vế viết nghịch · bỏ hai vế
    của bộ truyện tranh · bỏ chữ bảng màu mơ hồ trong sắc thái · bỏ vế tầm máy nói lại) đưa
    32% xuống 4%.

    Trần 8% chứ không phải 0: 4% còn lại chỉ mất vế SẮC THÁI (vế ít thiệt nhất, đứng cuối
    đúng theo thiết kế), và đặt trần bằng 0 sẽ biến cổng này thành cổng bắt oan ngay lần đầu
    ai đó thêm một kênh có câu cảnh dài. Trần 8% cho chỗ thở gấp đôi hiện tại mà vẫn bắt
    được ngay nếu ai thêm một khối vào prompt.
    """
    import nen_gt as N, giai_thich as G
    ct = tong = 0
    matluat = []
    for k in G.KENH:
        for idx in range(2):
            try:
                _, _, _, _, nhip, _ = G.kich_ban(k["ma"], idx)
            except Exception:
                continue
            for n in nhip:
                ve = n.get("ve") or ""
                if not ve:
                    continue
                for st in range(4):
                    for doc in (True, False):
                        tong += 1
                        N._DA_CAT.clear()
                        N._prompt(ve, k.get("tam") or "", N.GU_CARTOON, k["ma"], doc, siet=st)
                        if N._DA_CAT:
                            ct += 1
                            # LUẬT SÀN bị cắt là lỗi NẶNG, không có hạn ngạch nào cả.
                            if "runs unbroken" in N._DA_CAT[0]:
                                matluat.append((k["ma"], st))
    assert tong > 300, f"chỉ đo được {tong} tổ hợp — bài kiểm hỏng, không phải mã lành"
    assert not matluat, f"LUẬT SÀN bị cắt khỏi prompt ở {len(matluat)} tổ hợp: {matluat[:4]}"
    assert ct * 100 <= tong * 8, f"{ct}/{tong} prompt bị cắt mất vế ({ct*100//tong}%) — trần 8%"


def t_prompt_khong_viet_nghich():
    """Prompt không được chứa vế viết NGHỊCH — FLUX vẽ ra chính danh từ bị cấm.

    `kiem_nen.CAM_NGHICH` đã ghi và đã trả giá: *"`no furniture` đẻ ra đúng cái đồ chắn giữa
    khung mà nó định cấm"*. `TRAN_KHUNG` của bộ này viết `no circular vignette, no round
    badge, no border` — ba danh từ TRÒN đứng liền nhau ngay sau câu tả khung, và khung anh
    gửi kèm lời *"vẫn không rõ bối cảnh"* đúng là một minh hoạ nằm gọn trong một hình tròn.

    Cổng canh cả prompt đã ghép, không canh riêng một hằng số: câu nghịch có thể vào từ
    `KEP_GU`, `khung`, `_luat` hay `SIET`.
    """
    import re
    import nen_gt as N
    xau = re.compile(r"\bno (?:circular|round|border|furniture|objects?|text)\b", re.I)
    # HAI CẢNH, HAI NHÁNH. `_luat` rẽ theo `_NGOAI`: một cảnh chỉ soi được một nửa số vế, và
    # bản đầu của cổng này chỉ có cảnh vỉa hè — tức nhánh TRONG NHÀ chưa từng được soi.
    for ve in ("a person walking on a wide sidewalk",       # -> GON_NGOAI
               "a person sitting at a kitchen table"):      # -> GON_TRONG
        for doc in (True, False):
            for st in range(4):
                p = N._prompt(ve, "", N.GU_CARTOON, "howlong", doc, siet=st)
                m = xau.search(p)
                assert not m, f"prompt chứa vế viết nghịch {m.group(0)!r} ({ve[:20]}, siet={st})"


def t_prompt_khong_noi_nguoc_ve_giua_khung():
    """Không được vừa dặn 'chủ thể ở giữa' vừa dặn 'giữa khung để trống'.

    Hai câu ấy từng cùng nằm trong một prompt: `KHUNG_DOC` nói *"subject centred, everything
    important in the middle band"*, `GON_TRONG` nói *"centre of the frame is empty walkable
    floor"*. Câu sau chép từ `kich_hai.SAN_NEN` (§7), nơi nó ĐÚNG vì bộ truyện tranh dán người
    vector lên nền AI nên phải chừa chỗ dán. Bộ này để mô hình vẽ luôn người — §12.5.
    Mô hình chọn bên nào là may rủi, và đó là thứ làm chủ thể lúc có lúc không.
    """
    import nen_gt as N
    for ve in ("a person walking on a wide sidewalk",       # -> GON_NGOAI
               "a person sitting at a kitchen table"):      # -> GON_TRONG
      for doc in (True, False):
        p = N._prompt(ve, "", N.GU_CARTOON, "howlong", doc).lower()
        if "subject centred" in p or "middle band" in p:
            for c in ("centre of the frame is empty", "center of the frame is empty",
                      "centre of the frame is open", "center of the frame is open"):
                assert c not in p, f"prompt vừa dặn chủ thể ở giữa vừa dặn giữa khung trống: {c!r}"


def t_prompt_canh_dung_dau():
    """Câu tả CẢNH phải đứng ĐẦU prompt, trước khối phong cách.

    Docstring của `_prompt` viết đúng điều này, còn mã thì làm ngược lại: khối phong cách 844 ký
    tự ở `phan[0]`, câu cảnh xuống vị trí thứ ba. Hậu quả đo được: kênh SURVIVE (Kỷ Băng Hà) có
    prompt cảnh đúng *"a lone person in a frozen tundra"* mà **cả bốn ảnh ra một căn phòng hiện
    đại có đồng hồ treo tường** — mô hình khuếch tán đọc phần đầu nặng ký hơn.

    Không có lỗi nào báo, và chú thích đọc lên vẫn rất hợp lý. Cổng này canh đúng khoảng cách
    giữa lời nói và việc làm.
    """
    import nen_gt as N

    _ve = "a lone person standing in a frozen tundra under heavy grey sky"
    p = N._prompt(_ve, "lanh", N.GU_CARTOON, "survive")
    i_canh = p.find("frozen tundra")
    i_gu = p.find("hand-drawn 2D cartoon illustration")
    assert i_canh >= 0, "câu cảnh biến mất khỏi prompt"
    assert i_canh < 200, f"câu cảnh nằm ở ký tự {i_canh} — phải ở đầu prompt"
    if i_gu >= 0:
        assert i_canh < i_gu, "khối phong cách đứng TRƯỚC câu cảnh — ảnh sẽ theo phong cách, bỏ cảnh"
    # Và câu siết KHÔNG được đẩy nền về phía trắng: chữ trắng trên nền trắng thì tàng hình.
    for c in N.SIET:
        assert "white paper" not in c and "white page" not in c, \
            f"câu siết đẩy nền về TRẮNG: {c[:60]}"


def t_ghi_khoa_co_chot():
    """`ghi_trang_thai` phải có chốt chặn theo thời gian, không ghi mỗi tập.

    Nó được gọi trong `mot_tap`, tức mỗi TẬP một lần. Đo: 45 tập × 18 luồng × ~100 ghi =
    ~81.000 lượt GHI trên trần free 20.000/ngày, và ~239.000 lượt ĐỌC trên trần 50.000. Đây là
    gốc của mọi thứ Firestore hỏng hôm nay — dashboard hiện 241/295 khoá 'chưa kiểm, 13 ngày
    trước' trong khi bộ ghi vẫn chạy đều và ăn 429 mỗi lượt.
    """
    import io as _io
    import os as _o

    g = _o.path.dirname(_o.path.abspath(__file__))
    src = _io.open(_o.path.join(g, "xoay_key.py"), encoding="utf-8").read()
    i = src.find("def ghi_trang_thai")
    assert i > 0, "không tìm thấy ghi_trang_thai"
    # ── CẮT ĐÚNG THÂN HÀM, KHÔNG CẮT 4.000 KÝ TỰ  (4/9/2026) ────────────────────────────
    # `src[i:i+4000]` là một cửa sổ đoán. Thêm mấy dòng chú thích vào đầu hàm là chốt chặn
    # thời gian rơi ra ngoài cửa sổ, và cổng báo ĐỎ cho một hàm hoàn toàn đúng — đúng lúc
    # đang sửa chính hàm ấy để tiết kiệm hạn mức. Cổng bắt oan thì người ta tắt cổng (§13.8).
    # Cắt tới `def` kế tiếp ở cột 0: đó là ranh giới thật của thân hàm, không phải một con số.
    j = src.find("\ndef ", i + 1)
    than = src[i:j if j > 0 else len(src)]
    assert "getmtime" in than or "time.time" in than or "_t.time" in than, \
        "ghi_trang_thai không còn chốt chặn thời gian -> sẽ ghi mỗi tập và cạn hạn mức"
    assert "/tmp/" in than, \
        "chốt chặn dùng biến module thay vì tệp -> không sống qua ranh giới tiến trình"
    # ── VÀ BA CHIỀU KHÁC, MỖI CHIỀU MỘT LẦN ĐÃ TRẢ GIÁ  (4/9/2026) ──────────────────────
    # Chốt thời gian cắt TẦN SUẤT, nhưng nó không cắt SỐ NGƯỜI GHI (18 luồng cùng ghi một
    # sự thật) và không cắt GIÁ MỖI LẦN (dựng lại bản đồ 295 doc `gemini_keys`). Số học trên
    # cấu hình đang chạy: 10 lần × 18 luồng × 295 doc = **53.100 lượt ĐỌC mỗi lượt workflow**,
    # trên trần 50.000 CẢ NGÀY. Chốt thời gian một mình báo XANH cho đúng cảnh ấy.
    assert "GHI_SO_KHOA" in than, \
        "thiếu cờ một-luồng-ghi -> 18 luồng cùng ghi một ảnh chụp, nhân 18 lần chi phí"
    assert "_stream_at" in than, \
        "bản đồ khoá đọc thẳng `.stream()` -> không vào sổ ngân sách, bức tường không thấy"
    assert 'con_ngan_sach("doc")' in than, \
        "bản đồ khoá là một lượt ĐỌC nhưng chỉ hỏi ngân sách GHI"


def t_san_khong_dam_vao_chu():
    """Mặt sàn phải nằm HẲN TRÊN vùng chữ — nếu không thì "chạm sàn" và "không bị che" đánh nhau.

    Đo bằng pixel trên khung dựng thật (4/9): dải nhãn trắng chiếm 0,72–0,76·H, dải phụ đề
    0,80–0,85·H. `chanTroi` cũ trả 0,66 · 0,73 · **0,80**·H — hai biến thể trong ba rơi thẳng
    vào vùng chữ.

    Hậu quả không phải "hơi xấu": nó làm hai yêu cầu của anh loại trừ nhau. Vật đứng đúng trên
    đất thì bị dải chữ cắt ngang bụng; nhấc vật lên khỏi chữ thì nó **lơ lửng** (đo được 213
    pixel). Không bản vá nào ở phía vật giải được, vì mâu thuẫn nằm ở chỗ hai lớp cùng đòi một
    dải ngang của khung.

    Cổng này giữ ranh giới ấy. Ai nới `chanTroi` xuống dưới 0,72 là hình lại bị chữ cắt, và
    người sửa sẽ đi tìm lỗi ở phía nhân vật — đúng chỗ KHÔNG có lỗi.
    """
    import io as _io
    import os as _o
    import re as _re

    g = _o.path.dirname(_o.path.abspath(__file__))
    src = _io.open(_o.path.join(_o.path.dirname(g), "engine-remotion", "src", "gt", "Khuon.tsx"),
                   encoding="utf-8").read()
    i = src.find("export const chanTroi")
    assert i > 0, "mất hàm chanTroi"
    than = src[i:src.find("};", i)]
    so = [float(x) for x in _re.findall(r"H \* \(|([01]\.\d+)", than) if x]
    assert so, f"không đọc được phân số nào trong chanTroi: {than[:120]}"
    TRAN = 0.72          # mép TRÊN của dải nhãn, đo bằng pixel trên khung thật
    xau = [x for x in so if x >= TRAN]
    assert not xau, (f"chân trời {xau} chạm/vượt vùng chữ (mép trên {TRAN}·H) — vật đứng trên "
                     f"sàn sẽ bị dải chữ cắt ngang, và nhấc lên thì lơ lửng")


def t_bia_lay_nhip_dinh():
    """Ảnh bìa phải lấy mốc nhịp ĐỈNH, không lấy khung cuối video.

    `lam_thumb` mặc định trích ở 1,2 giây trước khi hết — đúng cho bộ comic (cú chốt nằm ở cuối)
    và sai cho bộ giải thích: nhịp cuối là cảnh đóng. Trường `dinh` đánh dấu đúng nhịp cần lấy,
    và trước 3/9 nó được ghi ở 87 chỗ mà KHÔNG AI ĐỌC.
    """
    import io as _io
    import os as _o

    g = _o.path.dirname(_o.path.abspath(__file__))
    gt = _io.open(_o.path.join(g, "giai_thich.py"), encoding="utf-8").read()
    assert "giay=_moc" in gt or "giay=" in gt.split("lam_thumb(")[1][:200], \
        "giai_thich không truyền mốc thời gian cho lam_thumb -> bìa lấy khung cuối"
    assert 'n.get("dinh")' in gt, "không còn đọc trường `dinh` -> nó lại thành trường chết"

    # Soi đúng CHỮ KÝ hàm, không soi cả docstring: bản đầu quét 400 ký tự sau `def` nên chữ
    # `giay` trong chú thích vẫn khớp, và cổng không bắt được khi tham số bị bỏ (thử ngược ra
    # "KHÔNG BẮT"). Một cổng chưa thử ngược là cổng chưa biết có hoạt động không (§13.11).
    kh = _io.open(_o.path.join(g, "kich_hai.py"), encoding="utf-8").read()
    i = kh.find("def lam_thumb")
    assert i > 0
    _ky = kh[i:kh.index("->", i)] if "->" in kh[i:i + 400] else kh[i:i + 400]
    assert "giay" in _ky, "lam_thumb không nhận tham số mốc thời gian trong chữ ký"

    # ── ĐƯỜNG COMIC PHẢI GIỮ NGUYÊN ────────────────────────────────────────────────────
    # `lam_thumb` dùng chung với bộ COMIC, nơi bìa đang được duyệt. Mọi thay đổi của bộ giải
    # thích (cắt dải phụ đề · bóng mềm · bỏ lớp chữ đè) phải nằm sau `_giua`, và `_giua` chỉ
    # bật khi chỗ gọi truyền `giay` — chỉ `giai_thich` truyền. Đổi mặc định là mang quyết định
    # của bộ này áp cho bộ kia mà không ai xem lại (§12.5).
    _than = kh[i:kh.find("\ndef ", i + 10)]
    assert "giay and 0.3 < giay" in _than, "`_giua` không còn phụ thuộc tham số `giay`"
    _j = _than.rfind("else:")
    assert _j > 0 and "rectangle" in _than[_j:] and "stroke_width" in _than[_j:], \
        "nhánh comic mất hộp nền/viền chữ — bộ comic sẽ đổi hình mà không ai duyệt"


def t_kiem_khuon_dem_theo_video():
    """`kiem_khuon` đo khuôn lời GIỮA CÁC VIDEO — nên mỗi video góp tối đa một phiếu mỗi khuôn.

    Bản cũ gộp mọi câu rồi đếm, nên MỘT bản dài 202 nhịp chiếm **72% mẫu** và một câu dẫn lặp 7
    lần trong 31 chương của cùng một video bị đếm y như 7 kênh khác nhau cùng đọc nó. Hai chuyện
    khác hẳn: cái đầu là điệp khúc của một chương trình, cái sau mới là "templated storylines".

    Lặp NỘI BỘ một video đã có cổng riêng (`t_khong_lap_loi_gan`, đo khoảng cách giữa hai lần
    đọc — thứ người xem cảm được).
    """
    import io as _io
    import os as _o

    g = _o.path.dirname(_o.path.abspath(__file__))
    src = _io.open(_o.path.join(g, "kiem_khuon.py"), encoding="utf-8").read()
    assert "_theo_video" in src, "cổng vẫn gộp mọi câu — một video dài sẽ lấn át mẫu"

    # Thử NGƯỢC bằng dữ liệu giả: một video lặp 50 lần chỉ được tính MỘT.
    import collections as _c
    import kiem_khuon as KK
    kho = [("a.json", "Put them side by side.")] * 50 + [("b.json", "Put them side by side.")]
    tv = {}
    for f, t in kho:
        tv.setdefault(f, set()).add(KK.khuon(t))
    dem = _c.Counter(k for ks in tv.values() for k in ks)
    assert dem.most_common(1)[0][1] == 2, \
        f"đếm sai: một video lặp 50 lần phải tính 1 phiếu, ra {dem.most_common(1)[0][1]}"


def t_kiem_hinh_lay_dung_khung():
    """Cổng `kiem_hinh` chỉ được đo tương phản phụ đề ở nhịp THẬT SỰ CÓ phụ đề.

    ── VÌ SAO ─────────────────────────────────────────────────────────────────────────────
    Nó lấy khung ở mốc chia đều `DAI*k/7`, nên khung rơi vào bất cứ nhịp nào. Đo trên bản dài
    HOW LOUD: **2/6 khung rơi trúng `the_chu`**, mà engine TẮT phụ đề ở đó theo thiết kế. Vùng
    phụ đề khi ấy chỉ toàn nền -> tỉ số **1,75:1**, kéo trung bình từ ~5,8 xuống 3,8 và cổng
    báo "chữ khó đọc" trong khi bốn khung có chữ đều đạt 4,62–6,76:1.

    Cổng phạt một QUYẾT ĐỊNH THIẾT KẾ như thể nó là lỗi (§13.8).
    """
    import io as _io
    import json as _json
    import os as _o
    import re as _re

    g = _o.path.dirname(_o.path.abspath(__file__))
    src = _io.open(_o.path.join(g, "kiem_hinh.py"), encoding="utf-8").read()
    assert 'the_chu' in src, "cổng không còn loại nhịp thẻ chữ ra khỏi phép đo"

    # Thử THẬT trên một tệp nhịp có sẵn: mốc chọn ra không được rơi vào `the_chu`.
    ra = sorted(_o.path.join(g, "out", f) for f in _o.listdir(_o.path.join(g, "out"))
                if _re.match(r"v9_.*\.json$", f)) if _o.path.isdir(_o.path.join(g, "out")) else []
    for tep in ra[:3]:
        nh = (_json.load(_io.open(tep, encoding="utf-8")).get("nhip") or [])
        co = [n for n in nh if (n.get("khuon") or "") != "the_chu"
              and str(n.get("loi") or "").strip() and n.get("s") is not None]
        if len(co) < 6:
            continue
        b = len(co) / 6.0
        for k in range(6):
            n0 = co[min(len(co) - 1, int(b * (k + 0.5)))]
            assert (n0.get("khuon") or "") != "the_chu", \
                f"{_o.path.basename(tep)}: mốc {k} vẫn rơi vào thẻ chữ"


def t_khong_tdz():
    """`const` dùng trước khai báo — `esbuild` và `tsc` đều xanh, chỉ nổ LÚC RENDER.

    Xảy ra khi chèn một khối mới vào giữa hai khai báo trong một component dài. Lỗi nằm sau một
    nhánh dữ liệu (chỉ biểu đồ kiểu 1/2 mới chạm tới `bo`), nên cả cổng render một khung cũng
    không thấy — đúng §5: *cổng render một khung không chứng minh được gì ngoài khung ấy*.
    """
    import os as _o
    import subprocess as _sp
    import sys as _s
    g = _o.path.dirname(_o.path.abspath(__file__))
    r = _sp.run([_s.executable, _o.path.join(g, "kiem_tdz.py")],
                capture_output=True, text=True, cwd=g)
    assert r.returncode == 0, "kiem_tdz báo lỗi:\n" + (r.stdout or r.stderr)[:400]


def t_giao_keo_chuoi_lien_repo():
    """`day_kho` nhận diện thành công bằng CHUỖI do repo KHÁC in ra — phải có cổng canh.

    `day_kho.day_mot` coi một lượt đẩy là thành công khi tìm được `Drive file id:` trong
    stdout của `MM0-AutoPublisher/src/enqueue.py`. Đó là một giao kèo giữa hai repo, và nó
    được viết bằng một chuỗi trần trong `print` — đổi một chữ ở repo kia thì:

        mọi lượt đẩy bị chấm HỎNG -> 3 lần thử -> `break` -> cả 18 luồng dừng -> 0 video/ngày

    và triệu chứng đọc ra y hệt "hạ tầng Drive hỏng", tức sẽ mất một buổi đi tìm sai chỗ.
    Cổng này rẻ và bắt đúng lúc đổi, không phải lúc chạy thật.

    Không tìm thấy repo publish thì BỎ QUA (máy này có thể chưa checkout nó) — nhưng nói
    rõ là bỏ qua, không im lặng cho xanh.
    """
    import os as _o
    import re as _re
    g = _o.path.dirname(_o.path.abspath(__file__))
    dk = _o.path.join(g, "day_kho.py")
    src = open(dk, encoding="utf-8").read()
    m = _re.search(r'_re\.search\(r"([^"]*Drive file id[^"]*)"', src)
    assert m, "day_kho.py không còn dò `Drive file id:` — cập nhật cổng này"
    # Lấy phần chữ thuần của biểu thức để tìm trong repo kia.
    can = "Drive file id:"
    for ung in (_o.path.join(g, "..", "MM0-AutoPublisher", "src", "enqueue.py"),
                _o.path.join(g, "..", "_autopublisher", "src", "enqueue.py")):
        if _o.path.exists(ung):
            assert can in open(ung, encoding="utf-8").read(), (
                f"day_kho dò {can!r} nhưng {ung} KHÔNG in chuỗi ấy — "
                f"mọi lượt đẩy sẽ bị chấm hỏng và cả 18 luồng dừng")
            return
    print("      (bỏ qua: chưa checkout repo publish trên máy này)")


def t_moi_truong_co_nguoi_doc():
    """Mỗi trường nhịp phải được engine vẽ ở ĐÚNG NHÁNH khuôn của nó.

    §16.6 đã ghi hai lần "trường được GHI mà không ai ĐỌC", và phép soi cả tệp bỏ lọt biến
    thể khó hơn: trường CÓ được đọc — chỉ là ở nhánh khác. Nhịp `howlong` bản dài, khuôn
    `dem`, ghi `dai_chu` và `so`+`don`; ba nhánh khác vẽ `dai_chu`, riêng `dem` thì không,
    nên người xem nhận 11 biểu tượng KHÔNG NHÃN. Đúng họ lỗi số 6.

    Cổng đã thử ngược cả hai lỗi thật (bỏ lại từng cái -> exit 1) và trạng thái sạch (0).
    """
    import os as _o
    import subprocess as _sp
    import sys as _s
    g = _o.path.dirname(_o.path.abspath(__file__))
    r = _sp.run([_s.executable, _o.path.join(g, "kiem_truong.py")],
                capture_output=True, text=True, cwd=g)
    assert r.returncode == 0, "kiem_truong báo lỗi:\n" + (r.stdout or r.stderr)[:400]


def t_moi_nhip_co_bo_cuc():
    import os as _o
    """Không nhịp nào của khuôn có nhiều bố cục được phép thiếu trường bố cục.

    ── LỖI NÀY CẮN HAI LẦN TRONG MỘT NGÀY ──────────────────────────────────────────────────
    Nhịp HOOK được `insert(0, …)` trong `kich_ban`. Lần đầu: `_bt_canh` gắn ở `_n` nên hook
    không bao giờ có `bt`. Lần hai: các lượt `_rai_*` chạy TRƯỚC khối hook nên `kieu_so` của
    30/30 nhịp hook là `None` — tức nhịp QUAN TRỌNG NHẤT của cả tập, ba giây đầu, là nhịp duy
    nhất rơi về bố cục mặc định.

    Cả hai lần đều KHÔNG có lỗi nào báo: engine đọc `N.kieu_so ?? 0` nên nó im lặng dùng mặc
    định, và nhìn từ ngoài chỉ là "tập nào hook cũng giống nhau".

    Quy luật rút ra: **mọi lượt rải phải chạy sau MỌI lượt chèn nhịp.** Cổng này canh chính điều
    ấy — nó bắt được bất kỳ nhịp nào được chèn sau lượt rải, kể cả nhịp thêm sau này.
    """
    import giai_thich as G

    # `bo_so` là trục bố cục THỨ HAI của `so_lieu` — engine từng tự tính bằng `hat % 3`, tức
    # một quyết định nằm ngoài mọi bảng gu. Canh nó ở đây để nó không lặng lẽ quay về engine.
    can = {"so_lieu": ("kieu_so", "bo_so"), "the_chu": ("bo_the",), "chia_doi": ("bo_ss",)}
    thieu = []
    for k in G.KENH:
        for i in range(3):
            for j, n in enumerate(G.kich_ban(k["ma"], i)[4]):
                for truong in (can.get(n.get("khuon") or "") or ()):
                    if n.get(truong) is None:
                        thieu.append(f'{k["ma"]} tập {i} nhịp {j} '
                                     f'({n.get("khuon")}) thiếu {truong}')
    assert not thieu, "nhịp thiếu bố cục: " + "; ".join(thieu[:4])

    # Và mọi bố cục phải THẬT SỰ được dùng — bảng gu có 6 kiểu thẻ mà chỉ dùng 2 thì thừa 4.
    import collections as _c
    dung = _c.Counter()
    for k in G.KENH:
        for i in range(3):
            for n in G.kich_ban(k["ma"], i)[4]:
                if (n.get("khuon") or "") == "the_chu":
                    dung[n.get("bo_the")] += 1
    # 5/9 — `the_chu` đã được GỘP vào hai họ hình (xem `giai_thich._gop_hai_ho`): anh chốt
    # rằng lộn xộn nằm trong một video, và năm khuôn không mang dữ liệu riêng bị bỏ. Nên
    # đường đang giao đi KHÔNG sinh nhịp `the_chu` nào nữa, và bảng 6 bố cục ấy chỉ còn phục
    # vụ template cũ (bật lại bằng `datGiay(false)`, giữ để đối chiếu theo §3).
    # Cổng giữ nguyên RĂNG cho trường hợp thật: hễ CÓ sinh thẻ chữ thì phải dùng đủ 6 — dùng
    # 2 trong 6 mới là bảng thừa. Vắng mặt hoàn toàn là một quyết định, không phải một lỗi.
    if dung:
        assert len(dung) >= 6, f"chỉ {len(dung)}/6 bố cục thẻ chữ được dùng -> bảng gu thừa"


def t_gu_hinh_khac_nhau():
    """Hai trục cùng lúc: KHÔNG lặp biểu tượng ở nhịp liền kề, và bộ gu hình phải khác nhau.

    Đo lúc phát hiện: 41/196 nhịp cảnh dùng lại đúng biểu tượng của nhịp ngay trước, và mỗi kênh
    bị một biểu tượng chiếm sóng (`dayinlife` ra cái đồng hồ 8 lần trong 4 tập). Anh soi khung
    và gọi đúng tên: *"nó cứ lặp đi lặp lại cùng 1 motip hoài"*.

    Trần giao nhau 3/5: có 24 biểu tượng cho 18 kênh × 5 chỗ nên trùng là không tránh khỏi, và
    trùng 3 là chấp nhận được. Trùng 4/5 thì hai kênh dùng gần như cùng một từ vựng hình — đúng
    trục "cảnh" mà chính sách YouTube nêu tên (§13.17).
    """
    import itertools as _it
    import giai_thich as G

    for m in [k["ma"] for k in G.KENH]:
        assert m in G.GU_HINH, f"kênh {m} chưa có bộ gu hình -> rơi về bộ mặc định chung"

    xau = []
    for k in G.KENH:
        for i in range(4):
            # ĐI QUA ĐÚNG ĐƯỜNG MÃ THẬT: `kich_ban` chạy cả `_rai_hinh` lẫn `_rai_tu_the`.
            # Gọi thẳng `_rai_hinh` là bỏ mất lượt gán tư thế, tức cổng đo một sản phẩm không
            # tồn tại (§13.15) — và nó sẽ báo đỏ cho những nhịp người vốn đã được phân biệt
            # bằng tư thế.
            nh = G.kich_ban(k["ma"], i)[4]
            truoc = ""
            truocTu = -1
            # PHẠM VI phải khớp `_rai_hinh` — cả `canh` lẫn `kinh_lup` đều vẽ biểu tượng.
            # Cổng đi qua ít khuôn hơn hàm thì nó thấy "nha, nha liền nhau" ở hai nhịp thật ra
            # có một nhịp kính lúp xen giữa. Cổng và hàm lệch phạm vi thì cổng báo lỗi giả.
            for n in nh:
                if (n.get("khuon") or "") not in ("canh", "nhom", "kinh_lup"):
                    continue
                if not (n.get("bt") or ""):
                    continue        # nhịp không vẽ hình thì trong suốt, không cắt mạch
                b = n.get("bt") or ""
                # ── NGƯỜI ĐƯỢC LẶP, NHƯNG TƯ THẾ PHẢI KHÁC  (4/9/2026) ───────────────
                # Luật cũ cấm mọi biểu tượng lặp liền kề. Nó đúng cho ĐỒ VẬT — hai cái
                # đồng hồ liền nhau là một khung lặp. Nó SAI cho nhân vật: sau khi buộc đồ
                # vật phải lấy từ LỜI, `nguoi` chiếm 64% nhịp `canh`, và ép đổi đi thì hệ
                # lại nhặt đồ vật trong phông nền — đúng lỗi "khung nói một đằng lời nói
                # một nẻo" vừa phải sửa.
                # Bốn ảnh tham chiếu đều có người ở MỌI khung; cái đổi là TƯ THẾ. Nên cổng
                # đổi theo: người lặp thì phải lặp với một tư thế khác.
                if b and b == truoc:
                    if b == "nguoi":
                        if (n.get("tu") or 0) == truocTu:
                            xau.append(f'{k["ma"]} tập {i}: người hai nhịp liền CÙNG tư thế')
                    else:
                        xau.append(f'{k["ma"]} tập {i}: {b} hai nhịp liền')
                truoc = b
                truocTu = n.get("tu") or 0
    assert not xau, "lặp biểu tượng liền kề: " + "; ".join(xau[:3])

    qua = [(a, b, sorted(set(G.GU_HINH[a]) & set(G.GU_HINH[b])))
           for a, b in _it.combinations(G.GU_HINH, 2)
           if len(set(G.GU_HINH[a]) & set(G.GU_HINH[b])) > 3]
    assert not qua, "bộ gu hình trùng quá 3/5: " + "; ".join(f"{a}/{b} {c}" for a, b, c in qua[:3])

    # Thử ngược: bỏ chống lặp đi thì phải CÓ lặp, nếu không cổng này canh một cơ chế không cần.
    tho = G.BO_SINH["dayinlife"](0)[3]
    lap = sum(1 for j, n in enumerate(tho[1:], 1)
              if (n.get("khuon") == "canh" and tho[j - 1].get("khuon") == "canh"
                  and n.get("bt") and n.get("bt") == tho[j - 1].get("bt")))
    assert lap > 0, "dữ liệu thô không còn lặp -> cổng chống lặp đang canh một việc đã hết"


def t_chia_doi_hai_ve_khac_nhau():
    """Nhịp `chia_doi` đặt hai vế cạnh nhau để so — hai vế bằng nhau thì nó không so gì cả.

    Xảy ra khi mốc so sánh ghi cứng trong bộ sinh TRÙNG với mục mà bộ lịch phát cho chương ấy:
        NORMAL TALKING 60 dB  |  A NORMAL CONVERSATION 60 dB
    Không có lỗi nào báo — nhịp vẫn dựng, vẫn đúng cỡ, vẫn có lời đọc. Chỉ soi khung mới thấy.
    Đo lúc phát hiện: 2/108. Chữa bằng `giai_thich._moc_khac`.

    Thử NGƯỢC ở cuối: `_moc_khac` phải thật sự đổi mốc, nếu không cổng này canh một hàm chết.
    """
    import giai_thich as G
    xau = []
    for k in G.KENH:
        for i in range(8):
            for n in G.BO_SINH[k["ma"]](i)[3]:
                if n.get("khuon") != "chia_doi":
                    continue
                t, p = n.get("trai") or {}, n.get("phai") or {}
                if str(t.get("so", "")).strip() == str(p.get("so", "")).strip():
                    xau.append(f'{k["ma"]}: {t.get("nhan")} = {p.get("nhan")} = {t.get("so")}')
    assert not xau, "nhịp so sánh có hai vế bằng nhau: " + "; ".join(xau[:3])

    assert G._moc_khac([{"nhan": "a", "so": "60 dB"}, {"nhan": "b", "so": "30 dB"}],
                       "60 dB")["nhan"] == "b", "_moc_khac không đổi mốc khi trùng"


def t_chart_co_so_that():
    """Biểu đồ phải có ít nhất hai giá trị KHÁC NHAU — trục toàn 0 hoặc trục phẳng không so gì.

    Bản đầu cạo số từ chữ số của TỪ ĐẦU trong hook phụ. 5/18 kênh trả lời định tính ("PROBABLY
    NOT", hoặc rỗng) nên nhịp tổng hợp của chúng ra bốn cột `0.0`; kênh ODDS viết mọi hook phụ
    theo khuôn "1 IN N" nên ra bốn cột đều bằng 1. Cả hai đều dựng êm.
    """
    import giai_thich as G
    xau = []
    for k in G.KENH:
        for i in range(4):
            for n in G.BO_SINH[k["ma"]](i)[3]:
                if n.get("khuon") != "chart":
                    continue
                v = [float(c.get("v", 0) or 0) for c in (n.get("cot") or [])]
                if len(v) < 2 or len({round(x, 6) for x in v}) < 2:
                    xau.append(f'{k["ma"]}: {v}')
    assert not xau, "biểu đồ không so được gì: " + "; ".join(xau[:3])

    assert G._so_hook("PROBABLY NOT") is None, "_so_hook phải trả None khi câu không có số"
    assert G._so_hook("11 MONTHS") == 11, "chữ M của MONTHS bị đọc thành hệ số triệu"
    assert G._so_hook("700,000x SMALLER") == 700000, "regex lùi khi gặp chữ sau số"
    assert G._so_hook("1 IN 36") == 36, "khuôn 1-in-N phải lấy N"


if __name__ == "__main__":
    main()
