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
    check("mascot: dùng rig sẵn, KHÔNG vẽ lại nhân vật", t_mascot_khong_ve_lai_nhan_vat)
    check("MascotStage động theo từng khung + parallax", t_mascot_stage_dong_tung_khung)
    check("tách nền rig: ĐO màu viền, không khoá cứng", t_tach_nen_khong_khoa_cung_mau)
    check("brandkit qua QC hình (đo pixel rồi soi Vision)", t_brandkit_co_qc_hinh)
    check("giọng nhân vật có cao độ, hai vai lệch nhau", t_giong_nhan_vat_co_cao_do)
    check("tts: không hàm nào dùng biến chưa nhận", t_tts_khong_dung_bien_chua_nhan)
    check("kịch bản skit mang đủ 5 luật viral", t_kich_ban_co_luat_viral)
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


def t_mascot_khong_ve_lai_nhan_vat():
    """Engine mascot phải dùng RIG có sẵn — tuyệt đối không gọi FLUX vẽ nhân vật khi dựng video.

    25/8 — đây là toàn bộ lý do concept mascot quay lại được: bản 22/8 vẽ lại nhân vật mỗi cảnh
    nên nhân vật TRÔI (2 khung liền nhau ra 2 tỉ lệ khác nhau) và tốn 5-8 ảnh/video. Nếu ai đó
    lỡ tay gọi lại đường vẽ trong `mascot_build`, bệnh cũ tái phát y nguyên."""
    src = _doc("mascot_build.py")
    for cam in ("_generate_image_ai", "_cf_flux_image", "fetch_image", "_pexels"):
        assert cam not in src, f"mascot_build gọi {cam} -> nhân vật sẽ trôi trở lại"
    assert "da_co_rig" in src and "da_co_san_khau" in src, \
        "phải CHẶN trước khi dựng nếu rig/sân khấu chưa có, thay vì render ra video thiếu hình"
    # 25/8 — pilot 11:07Z chết vì props trỏ tới lớp nền KHÔNG CÓ FILE (tách nền hụt).
    # Khai báo là ý định, thư mục mới là sự thật.
    assert "os.path.exists(os.path.join(_goc_stage" in src, \
        "không lọc lớp nền theo file THẬT -> Remotion nạp ảnh không tồn tại, chết cả lượt render"
    # nhép mồm phải đo từ tiếng thật, không phải ngẫu nhiên
    assert "_rms_12hz" in src and "ffmpeg" in src, "mồm không đo từ audio thật"
    # 25/8 — video pilot ra đủ hình/độ dài/luồng audio nhưng -91dB: lệnh ghép thiếu `-map` nên
    # ffmpeg vớ đúng track CÂM mà Remotion xuất kèm. Lỗi im lặng, chỉ QC cuối mới bắt được.
    assert '"-map", "0:v:0"' in src and '"-map", "1:a:0"' in src, \
        "lệnh ghép tiếng thiếu -map -> ffmpeg tự chọn nhầm track câm của Remotion"
    assert "volumedetect" in src, "không đo mức âm ngay sau khi ghép"


def t_mascot_stage_dong_tung_khung():
    """`MascotStage` phải tính chuyển động THEO KHUNG (useCurrentFrame), không phải ảnh tĩnh đổi nhịp.

    Chốt cả multiplane: mỗi lớp nền phải nhân theo độ sâu `xa` — thiếu phép nhân đó thì các lớp
    trượt bằng nhau, mất hoàn toàn chiều sâu và lại thành ảnh phẳng zoom như bản cũ."""
    src = _doc("../engine-remotion/src/MascotStage.tsx")
    assert "useCurrentFrame" in src, "không đọc khung -> không có chuyển động thật"
    # ĐỦ 4 DẤU HIỆU CHIỀU SÂU của máy đa tầng — thiếu cái nào cũng tụt về "ảnh nền + hình dán"
    assert "0.15 + xa * 0.85" in src, "lớp nền không nhân theo độ sâu -> mất thị sai"
    assert "suong" in src and "saturate(" in src, "mất phối cảnh không khí (dấu hiệu chiều sâu mạnh nhất)"
    assert "blur(" in src, "mất độ sâu trường ảnh"
    assert "L.xa < DEPTH_NV" in src and "L.xa >= DEPTH_NV" in src, \
        "lớp gần không vẽ ĐÈ LÊN nhân vật -> nhân vật dán lên cảnh chứ không ở TRONG cảnh"
    assert "camScale" in src, "nhân vật không chịu phép biến đổi của máy -> lộ là hình dán khi camera đẩy"
    assert "talk_open" in src and "talk_closed" in src, "mất cặp nhép mồm"
    assert "spring(" in src, "mất chuyển động đàn hồi (vào cảnh/nảy)"


def t_tach_nen_khong_khoa_cung_mau():
    """Tách nền rig phải ĐO màu từ viền ảnh, không khoá cứng một mã màu.

    25/8 — đo trên ảnh thật của lượt rig 10:51Z: FLUX vẽ nền xanh #38b828, trong khi code khoá
    cứng #00b140. Khoảng cách 87, ngưỡng cũ 88 ⇒ lọt đúng 1 điểm, nên gần như mọi tư thế đều báo
    "0% khung là nền khoá" và bị bỏ. Nhà cung cấp không hứa sắc độ nào cả — chỉ hứa "nền phẳng",
    mà nền phẳng thì luôn CHẠM VIỀN. Đo viền là dấu hiệu không phụ thuộc sắc độ."""
    src = _doc("mascot_rig.py")
    assert "def _mau_vien" in src, "không còn hàm đo màu nền từ viền"
    i = src.index("def _tach_nen")
    than = src[i:src.index("def _cat_khung")]
    assert "_mau_vien(" in than, "_tach_nen vẫn khoá cứng màu thay vì đo"
    assert "dong_nhat < 0.45" in than, "mất chốt 'viền phải đồng nhất' -> sẽ ăn thủng nhân vật"
    # hỏng thì phải GIỮ ảnh làm bằng chứng, không xoá
    assert "_hong" in src and "os.remove(dest)" not in src, \
        "ảnh tách hỏng bị xoá -> lần sau lại phải đoán FLUX vẽ gì"


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


def t_brandkit_co_qc_hinh():
    """Ảnh nhận diện phải qua QC HÌNH trước khi được dùng — đo pixel rồi mới soi Vision.

    25/8 (anh dặn "kiểm visual QC trước sau"): avatar/bìa là thứ khán giả thấy TRƯỚC cả video.
    Một ảnh nền trơn vì PNG rig nạp hụt mà lọt lên kênh thì hỏng nhận diện ngay từ ấn tượng đầu —
    và không có gì trong hệ bắt được, vì file vẫn tồn tại và vẫn đủ dung lượng."""
    src = _doc("mascot_brand.py")
    assert "def _qc_anh" in src, "brandkit không có QC hình"
    assert "flat_bg_metrics" in src, "không đo pixel (tầng rẻ) trước khi gọi Vision"
    i = src.index("def _qc_anh")
    than = src[i:src.index("def sinh")]
    assert than.index("flat_bg_metrics") < than.index("verify_image"), \
        "phải ĐO trước SOI sau — gọi Vision trước là đốt quota cho ảnh hỏng hiển nhiên"
    assert "_hong" in src, "ảnh QC trượt bị xoá -> mất bằng chứng để soi"


def t_giong_nhan_vat_co_cao_do():
    """Giọng nhân vật phải truyền được CAO ĐỘ, và hai vai phải lệch nhau đủ để không lẫn.

    25/8 — `edge_tts.Communicate` vẫn nhận `pitch` nhưng hệ chưa bao giờ truyền: đại bàng khoác
    lác, gấu mèo láu cá, bà hàng xóm nhiều chuyện đều nói bằng đúng một chất giọng đọc bản tin.
    Cao độ là đòn bẩy mạnh nhất biến giọng phát thanh viên thành giọng nhân vật, và miễn phí."""
    import json
    tk = _doc("tts_karaoke.py")
    assert "pitch=pitch" in tk, "synth không truyền pitch xuống edge-tts"
    assert 'Communicate(text, voice, rate=rate, pitch=pitch' in tk, "Communicate thiếu pitch"
    mb = _doc("mascot_build.py")
    assert "pitch=cao.get(who)" in mb, "mascot_build không truyền cao độ theo vai"
    d = json.loads(_doc("mascot_channels.json"))
    for k, v in d.items():
        assert "pitch_a" in v and "pitch_b" in v, f"{k}: thiếu cao độ"
        pa, pb = int(v["pitch_a"].replace("Hz", "")), int(v["pitch_b"].replace("Hz", ""))
        assert abs(pa - pb) >= 12, f"{k}: hai vai chỉ lệch {abs(pa-pb)}Hz — sẽ nghe như một người"


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


if __name__ == "__main__":
    main()
