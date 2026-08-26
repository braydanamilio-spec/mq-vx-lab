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
            if "xac_minh_mo_dau(" in dong[j]:
                thay = True
                break
            if dong[j].startswith("def "):
                # canary là PHÁT SÚNG THỬ bằng ảnh tự tạo, không phải video sẽ đăng -> miễn trừ
                thay = "render_canary" in dong[j]
                break
        if not thay:
            xau.append(f"dòng {i+1}: render Cinematic mà không xác minh mở đầu bằng khung thật")
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
    for f in ("chay_chung", "chay_race", "chay_phim"):
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
    """50 kênh gen-2 phải có mặt ĐỦ ở ba nơi, theo `CHANNEL_METHODS §THÊM 1 KÊNH MỚI`.

    26/8 — kiểm lại thì thiếu SẠCH: `RS_PRESETS` 0/50, `RS_BRANDS` 0/50, `brands.json` 0/50, trong
    khi 55 kênh cũ đủ cả. Nghĩa là đã làm xong hết phần khó (engine · giọng riêng · phông riêng ·
    template thumbnail · chuyển cảnh) mà kênh mới vẫn **không hiện trên dashboard** và khâu ĐĂNG
    **không biết handle/hashtag** của chúng.

    Ba nơi, ba việc khác nhau — thiếu nơi nào hỏng việc nấy:
      • `RS_PRESETS`  -> dropdown chọn kênh khi render
      • `RS_BRANDS`   -> brand kit: avatar/cover/mô tả/hashtag
      • `brands.json` -> khâu đăng YouTube/FB/IG đọc handle · tagline · hashtag · category"""
    import json as _json
    ks = _json.loads(_doc("kenh_the_he_2.json"))
    ten = [k["ten"].replace(" ", "").upper() for k in ks]
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
    import json as _json, re as _re
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
        fn = mp.get(ham)
        b = _re.search(r"def " + str(fn) + r"\(.*?(?=\ndef )", src, _re.S) if fn else None
        doc = set(_re.findall(r'ky\.get\("(\w+)"', b.group(0))) if b else set()
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
    check("50 kênh không được giống nhau (≥70 điểm)", t_50_kenh_khong_duoc_giong_nhau)
    check("băm Python khớp băm TypeScript", t_bam_python_khop_typescript)
    check("prop font khai rồi phải thao ra", t_phong_khai_roi_phai_thao_ra)
    check("gen-2: cả 3 đường phải làm thumbnail", t_gen2_phai_lam_thumbnail)
    check("fitSize theo phông + theo template", t_fitsize_phai_theo_phong_va_khung)
    check("canary không được render vào composition rỗng", t_canary_khong_duoc_render_vao_composition_rong)
    check("phông chảy hết đường JSON->props->composition", t_phong_phai_chay_het_duong_toi_luc_render)
    check("dọn kho: đi hết cây + mọi loại tệp", t_don_kho_phai_di_het_cay_va_moi_loai_tep)
    check("mức âm chuyển cảnh quyết ở MỘT chỗ", t_muc_am_quyet_o_mot_cho)
    check("50 kênh đồng bộ đủ 3 nơi (dropdown/brand/đăng)", t_50_kenh_dong_bo_du_ba_noi)
    check("tên seed lưu phải tra ra được kênh gen-2", t_tra_kenh_gen2_phai_khop_ten_seed_luu)
    check("mỗi kênh gen-2 phải xoay được đề tài", t_moi_kenh_gen2_phai_xoay_duoc_de_tai)
    check("55 kênh cũ phải có bản chụp tên", t_ten_kenh_cu_phai_co_ban_chup)
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
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "firestore_bridge.py"), encoding="utf-8").read().split("\n")
    tron = []
    for i, ln in enumerate(src):
        if ".stream(" not in ln or ln.strip().startswith("#"):
            continue
        if "_stream_at" in ln:
            continue                      # đi qua lớp bọc -> hợp lệ
        vung = "\n".join(src[max(0, i - 6):i + 2])
        if "_cr(" in vung or "def _stream_at" in vung:
            continue                      # có gắn sổ ngay trên -> hợp lệ
        tron.append(f"dòng {i+1}: {ln.strip()[:78]}")
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
    than = src[i:i + 2200]
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
    than = src[i: i + 4200]
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
    than = src[i: i + 900]
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
        for n in _ast.walk(t):
            if isinstance(n, _ast.Call) and getattr(n.func, "attr", "") == "get" \
                    and getattr(getattr(n.func, "value", None), "attr", "") == "environ" \
                    and len(n.args) == 2 and isinstance(n.args[1], _ast.Constant) \
                    and isinstance(n.args[1].value, str) and n.args[1].value.strip():
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
    than = src[i: i + 2600]
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
    than = src[i: i + 3000]
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
        assert con > 20, f"cờ {con:.0f}' không dài hơn nhánh 'không rõ' (20')"
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

    assert abs(cf - _toi_moc(_utc)) <= 2, f"Cloudflare không nghỉ tới mốc 00:00 UTC: {cf}"
    assert abs(gg - _toi_moc(_utc - _d.timedelta(hours=7))) <= 2, \
        f"Google không nghỉ tới mốc 00:00 giờ Thái Bình Dương: {gg}"
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
    than = src[i:i + 6000]
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
    than = src[i:i + 9000]
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
    assert to <= 100, f"timeout {to}' quá dài — phiên sau sẽ bị huỷ trắng như 10:03/10:44 ngày 25/8"


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
    than = src[i:i + 5200]
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
    than = src[i:i + 700]
    assert "tuDaiNhat" in than, "phải tính theo TỪ DÀI NHẤT (từ đơn không xuống dòng được)"
    assert "Math.max(38" in than, "thiếu sàn cỡ chữ"
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
    than = src[i:i + 4200]
    assert "_cf_chan_prompt" in than, "CF chặn prompt vẫn giết luôn cả lượt vẽ"
    # không còn `return False` ngay sau nhánh CF
    assert "return False               # CF trả về không phải ảnh" not in than, \
        "vẫn trả False ngay khi CF chặn -> mất đường Gemini"
    # phải bỏ qua CF còn lại để khỏi đốt lượt vô ích
    assert 'if _cf_chan_prompt and str(_k).startswith("cf:")' in than, \
        "không bỏ qua key CF còn lại -> đốt lượt vào cùng một prompt bị chặn"


if __name__ == "__main__":
    main()
