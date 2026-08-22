"""
firestore_bridge.py — Cầu nối render pipeline <-> Firestore (dùng CHUNG service account
với AutoPublisher: biến GOOGLE_APPLICATION_CREDENTIALS + FIREBASE_PROJECT_ID).

- Đọc: gemini_keys (key+Gmail), render_channels (kênh cần render), render_config (bật/tắt, qc_min, model).
- Ghi: render_jobs (trạng thái realtime -> tab 🎬 Render Studio hiển thị live).

Chạy trên GitHub Actions: workflow ghi secret GCP_SA_KEY ra /tmp/sa.json rồi set 2 biến trên.
"""
from __future__ import annotations
import os, json
from datetime import datetime, timezone


def _db():
    from google.cloud import firestore
    from google.oauth2 import service_account
    key = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    project = os.environ.get("FIREBASE_PROJECT_ID")
    creds = service_account.Credentials.from_service_account_file(key)
    return firestore.Client(project=project, credentials=creds)


_DBJ = [None]
def _db_jobs():
    """Client cho collection render_jobs -> Project B (SHARD, giảm tải A) nếu có creds B; KHÔNG thì dùng A (backward-compatible)."""
    key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_B")
    project = os.environ.get("FIREBASE_PROJECT_ID_B")
    if not (key and project and os.path.exists(key)):
        return _db()                                   # chưa cấu hình shard -> A như cũ
    if _DBJ[0] is None:
        from google.cloud import firestore
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(key)
        _DBJ[0] = firestore.Client(project=project, credentials=creds)
    return _DBJ[0]


_DBP = [None]
def _db_pub():
    """Client cho collection videos (Project C, publish) -> ĐỌC hiệu suất video đã đăng cho feedback loop chọn
    chủ đề (xem top_titles). Không có creds C -> None (feature tắt êm, không lỗi)."""
    key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_C")
    project = os.environ.get("FIREBASE_PROJECT_ID_C")
    if not (key and project and os.path.exists(key)):
        return None
    if _DBP[0] is None:
        from google.cloud import firestore
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(key)
        _DBP[0] = firestore.Client(project=project, credentials=creds)
    return _DBP[0]


def top_titles(owner: str, channel: str, n: int = 8) -> list[str]:
    """Tiêu đề N video ĐÃ ĐĂNG xem nhiều nhất của kênh -> đưa vào prompt Gemini làm gợi ý
    "phong cách/góc độ đang ăn khách" (KHÔNG lặp chủ đề, chỉ học GU khán giả thật).
    Rỗng nếu chưa có creds C / chưa có video nào đăng (điều bình thường tới khi user kết nối YouTube)."""
    _cr("top_titles", n)   # limit(n) — trước ghi 60 là ĐẾM SAI (máy đo phải đúng trước tiên)
    db = _db_pub()
    if db is None:
        return []
    try:
        col = db.collection("videos").where("owner", "==", owner).where("channel", "==", channel).where("status", "==", "posted")
        try:
            from google.cloud.firestore_v1 import Query
            docs = list(col.order_by("stats.views", direction=Query.DESCENDING).limit(n).stream())
        except Exception:
            docs = list(col.limit(60).stream())              # thiếu index -> lấy thô rồi tự sort
            docs.sort(key=lambda d: ((d.to_dict() or {}).get("stats") or {}).get("views", 0), reverse=True)
            docs = docs[:n]
        out = []
        for d in docs:
            x = d.to_dict() or {}
            t = (x.get("title") or "").strip()
            v = ((x.get("stats") or {}).get("views") or 0)
            if t and v > 0:
                out.append(f"{t} ({v} views)")
        return out
    except Exception as e:
        print(f"   ⚠️ top_titles lỗi ({e}) — bỏ qua feedback, chạy bình thường")
        return []


def _db_meta():
    """Client cho META render (config·channels·gemini_keys·storage·topics·requests).
    Bật cờ SHARD_META=1 (khi đã migrate sang Project B) -> đọc/ghi meta trên B (render CHỈ đụng B, cách ly A).
    Chưa bật (mặc định) -> A như cũ (backward-compatible)."""
    if os.environ.get("SHARD_META") == "1":
        return _db_jobs()          # B (đã cấu hình creds B); _db_jobs tự fallback A nếu thiếu creds
    return _db()


def _db_keys():
    """Project chứa gemini_keys. SHARD_KEYS=1 -> B (render hết dùng chung hạn mức với publish).

    ĐỌC VÀ GHI PHẢI CÙNG MỘT NƠI: nếu đọc key ở B mà ghi req_today/alive/cooling sang A thì bộ đếm
    bên B mãi bằng 0 -> key_order() tưởng mọi key đều chưa dùng -> chia key sai lệch, dồn tải vào
    vài key rồi lại 429. Vì vậy MỌI hàm đụng gemini_keys đều đi qua đây."""
    return _db_jobs() if os.environ.get("SHARD_KEYS") == "1" else _db()


def _now():
    return datetime.now(timezone.utc).isoformat()


# ── ĐẾM LƯỢT GHI FIRESTORE (đo thật, không ước lượng) ──────────────────────────────────────────
# Vì sao: suốt 21/8 phải ƯỚC LƯỢNG xem cái gì đốt hạn mức ghi, mỗi lần lại soi log từ đầu.
# Có bộ đếm thì cuối mỗi phiên tự in ra con số THẬT theo từng hàm -> nhìn log là biết ngay,
# khỏi đoán, khỏi phải điều tra lại lần sau.
_WRITES = {"n": 0, "by": {}}
_READS = {"n": 0, "by": {}}


def _cw(tag: str):
    _WRITES["n"] += 1
    _WRITES["by"][tag] = _WRITES["by"].get(tag, 0) + 1


def _cr(tag: str, n: int = 1):
    _READS["n"] += n
    _READS["by"][tag] = _READS["by"].get(tag, 0) + n


def flush_soft() -> int:
    """XẢ các lượt ghi quan trọng bị rơi lúc tắt-ghi (job done/new/topics). Gọi CUỐI LUỒNG —
    lúc đó cửa sổ 20' thường đã qua hoặc quota vừa hồi. Không xả được thì thôi (phiên sau
    Health Guardian/target tự cân), nhưng phần lớn trường hợp cứu được count_done khỏi đếm thiếu
    -> không LÀM DƯ video. Trả số lượt xả thành công."""
    import time as _t
    if not _PENDING:
        return 0
    if _t.time() < _WQ_DEAD["until"]:
        # thử 1 lượt thăm dò: quota có khi đã hồi trước hạn
        fn, tag = _PENDING[0]
        try:
            _retry(fn, tries=1); _PENDING.pop(0); _WQ_DEAD["until"] = 0
        except Exception:
            return 0
    ok = 0
    while _PENDING:
        fn, tag = _PENDING.pop(0)
        try:
            _retry(fn, tries=2); ok += 1; _cw(f"xả:{tag}")
        except Exception:
            _PENDING.insert(0, (fn, tag)); break
    if ok:
        print(f"   💾 Đã xả lại {ok} lượt ghi bị hoãn (job/topics) — count_done không đếm thiếu.")
    return ok


def write_report() -> str:
    """Chuỗi 1-2 dòng tổng kết lượt ghi Firestore của tiến trình này."""
    if not _WRITES["n"]:
        return "🧮 Firestore: 0 lượt ghi."
    top = sorted(_WRITES["by"].items(), key=lambda x: -x[1])[:6]
    rtop = sorted(_READS["by"].items(), key=lambda x: -x[1])[:6]
    return ("🧮 Firestore: " + str(_WRITES["n"]) + " GHI (" + " · ".join(f"{k}={v}" for k, v in top) + ")"
            + " | " + str(_READS["n"]) + " ĐỌC (" + " · ".join(f"{k}={v}" for k, v in rtop) + ")")


def _retry(fn, tries=5):
    """Thử lại khi Firestore 429/RESOURCE_EXHAUSTED (burst đọc/ghi dồn) -> KHÔNG để burst tạm chặn gate/render."""
    import time as _t
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            s = str(e)
            if ("RESOURCE_EXHAUSTED" in s or "Quota exceeded" in s or "429" in s) and i < tries - 1:
                _t.sleep(1.5 * (i + 1)); continue
            raise


_KEYS_CACHE = {}      # (owner, include_cooling) -> (thời điểm, kết quả)
KEYS_TTL = 180        # giây



# ── GHI MỀM (best-effort) — SẢN XUẤT KHÔNG BAO GIỜ CHẾT VÌ TELEMETRY ────────────────────────────
# Nhận thức gốc (21/8, do user chỉ ra): hạn mức ĐỌC (50K/ngày) và GHI (20K/ngày) là HAI QUOTA
# RIÊNG. B cạn GHI nhưng ĐỌC vẫn còn — mà render chỉ cần ĐỌC (config/kênh/key/topics) để làm
# video và đẩy Drive; mọi lượt GHI (job, trạng thái, cờ, cooldown) chỉ là telemetry cho dashboard.
# Trước đây một lượt ghi 429 là plan_mode/lane CHẾT NGUYÊN PHIÊN -> mất cả ngày sản xuất chỉ vì
# không ghi được bảng theo dõi. Giờ: ghi hỏng vì quota -> BÁO RÕ 1 LẦN, tắt ghi 20', sản xuất
# chạy tiếp. Cái giá: dashboard mù tạm thời + mất checkpoint resume trong 20' — rẻ hơn vô hạn so
# với 0 video.
_WQ_DEAD = {"until": 0.0, "warned": False}
# ĐỌC-MỀM (22/8): hạn mức ĐỌC của B cũng cạn được (phiên 04:22Z chết 18/18 luồng vì read_keys/
# read_config ném 429 xuyên _retry). Nguyên tắc y như ghi-mềm: quota chết = dùng bản đệm cũ /
# mặc định an toàn, KHÔNG BAO GIỜ crash luồng vì một lượt đọc telemetry.
_RQ_DEAD = {"until": 0.0, "warned": False}
_CFG_LAST = {}        # owner -> bản render_config đọc được gần nhất (fallback khi quota đọc chết)
_PENDING = []   # các lượt ghi QUAN TRỌNG bị rơi trong cửa sổ tắt-ghi -> xả lại cuối luồng
_PENDING_TAGS = ("update_job", "new_job", "save_topics")   # mất done-write là count_done đếm thiếu -> LÀM DƯ video
_PENDING_CAP = 300


def _wq_exhausted(e) -> bool:
    t = str(e)
    return "RESOURCE_EXHAUSTED" in t or "Quota exceeded" in t or "429" in t


def _soft(fn, tag: str):
    """Chạy 1 lượt GHI best-effort. Trả kết quả fn() hoặc None nếu đang trong cửa sổ tắt-ghi.
    Lỗi KHÔNG-phải-quota vẫn ném lên như cũ (đó là lỗi thật cần thấy)."""
    import time as _t
    if _t.time() < _WQ_DEAD["until"]:
        _WRITES["by"]["(bỏ-vì-quota)"] = _WRITES["by"].get("(bỏ-vì-quota)", 0) + 1
        if tag in _PENDING_TAGS and len(_PENDING) < _PENDING_CAP:
            _PENDING.append((fn, tag))     # set(merge) idempotent -> xả lại sau an toàn
        return None
    try:
        return _retry(fn, tries=2)
    except Exception as e:
        if _wq_exhausted(e):
            _WQ_DEAD["until"] = _t.time() + 20 * 60
            if tag in _PENDING_TAGS and len(_PENDING) < _PENDING_CAP:
                _PENDING.append((fn, tag))
            if not _WQ_DEAD["warned"]:
                _WQ_DEAD["warned"] = True
                print(f"🩹 Firestore HẾT HẠN MỨC GHI ({tag}) -> tắt ghi telemetry 20', SẢN XUẤT CHẠY TIẾP. "
                      f"Dashboard sẽ mù tạm thời; video vẫn render + đẩy Drive bình thường.")
            return None
        raise

def read_keys(owner: str, include_cooling: bool = False) -> list[dict]:
    """Trả key CÒN DÙNG được (bỏ qua key đang cooldown do vừa bị rate-limit).

    CÓ ĐỆM 3 PHÚT trong tiến trình: bảng gemini_keys nằm ở Project A — CÙNG project với publish —
    mà mỗi lần gọi là đọc TOÀN BỘ key. 18 luồng render đọc lặp lại nhiều lần/phiên thì giành sạch
    hạn mức đọc của Project A, khiến publish/publish_social ăn "ResourceExhausted: 429" (sự cố
    20/8) dù bản thân render vẫn chạy (render_jobs ở Project B nên không bị ảnh hưởng).
    3 phút đủ ngắn để nhận key vừa được thêm/hồi quota, đủ dài để cắt phần lớn lượt đọc lặp."""
    import time as _t
    ck = (owner, include_cooling)
    hit = _KEYS_CACHE.get(ck)
    if hit and (_t.time() - hit[0]) < KEYS_TTL:
        return hit[1]
    if hit and _t.time() < _RQ_DEAD["until"]:
        return hit[1]     # quota ĐỌC đang chết -> bản đệm cũ (dù quá TTL) còn hơn crash luồng

    def _do():
        # ĐỌC TỪ PROJECT B TRƯỚC (nếu đã copy key sang B), B rỗng thì lùi về A như cũ.
        # Vì sao: gemini_keys là thứ DUY NHẤT còn lại mà render dùng chung Project A với publish
        # (SHARD_META=1 đã đưa config/channels/topics/requests sang B). 18 luồng render đọc bảng
        # này mỗi phiên -> ăn hết hạn mức đọc của A -> publish VÀ CẢ bước lập kế hoạch render đều
        # ăn "ResourceExhausted: 429" (20/8 chặn sản xuất ~13 tiếng tới lúc quota reset).
        # Lùi-về-A giữ cho thay đổi này AN TOÀN: chưa copy sang B thì chạy y như trước.
        db = _db_keys()
        out = []; now = _now()
        for d in db.collection("gemini_keys").where("owner", "==", owner).stream():
            x = d.to_dict() or {}
            if not x.get("key"):
                continue
            cooling = x.get("cooling_until", "")
            if cooling and cooling > now and not include_cooling:
                continue                                  # đang nghỉ -> bỏ qua vòng này
            if x.get("alive") is False and not include_cooling:
                continue                                  # RENDER: bỏ key đã biết CHẾT (403/khoá) -> khỏi phí lượt.
            today = now[:10]
            req_today = int(x.get("req_today", 0) or 0) if x.get("req_date") == today else 0   # sang ngày mới -> coi như 0
            out.append({"id": d.id, "key": x["key"], "email": x.get("email", ""),
                        "last_checked": x.get("last_checked", ""), "alive": x.get("alive"),
                        "last_used": x.get("last_used", ""), "cooling_until": cooling,
                        "dead_since": x.get("dead_since", ""), "req_today": req_today})
        return out
    try:
        res = _retry(_do)
        if not res and os.environ.get("SHARD_KEYS") == "1":
            # B rỗng (chưa copy key sang) -> lùi về A, KHÔNG để pipeline tưởng là hết key rồi dừng.
            def _fallbackA():
                db = _db(); out2 = []
                for d in db.collection("gemini_keys").where("owner", "==", owner).stream():
                    x = d.to_dict() or {}
                    if x.get("key"):
                        out2.append({"id": d.id, "key": x["key"], "email": x.get("email", ""),
                                     "last_checked": x.get("last_checked", ""), "alive": x.get("alive"),
                                     "last_used": x.get("last_used", ""), "cooling_until": x.get("cooling_until", ""),
                                     "dead_since": x.get("dead_since", ""), "req_today": 0})
                return out2
            print("   ℹ️ SHARD_KEYS=1 nhưng Project B chưa có key -> dùng tạm Project A")
            res = _retry(_fallbackA)
        res = _merge_a_keys(owner, res)
    except Exception as e:
        # ĐỌC-MỀM: quota đọc cạn thì trả bản đệm cũ (hoặc rỗng) — 18/18 luồng phiên 04:22Z chết
        # chỉ vì lượt đọc này ném 429 xuyên qua `or keys` của caller (raise ≠ falsy).
        if _wq_exhausted(e):
            _RQ_DEAD["until"] = _t.time() + 15 * 60
            if not _RQ_DEAD["warned"]:
                _RQ_DEAD["warned"] = True
                print("🩹 Firestore HẾT HẠN MỨC ĐỌC (read_keys) -> dùng bản đệm cũ 15', luồng chạy tiếp.")
            return hit[1] if hit else []
        raise
    _KEYS_CACHE[ck] = (__import__('time').time(), res)
    return res


_A_KEYS = {"rows": None}   # đọc bảng key ở A TỐI ĐA 1 LẦN mỗi tiến trình (A cũng Spark free!)


def _merge_a_keys(owner: str, rows: list[dict]) -> list[dict]:
    """HỢP NHẤT key A -> kết quả đọc từ B, so theo GIÁ TRỊ key (không theo doc id).

    Vì sao cần (phát hiện 22/8, phiên quyết định 04:22Z): user thêm 10+ key Groq trên dashboard
    (ghi vào A), nhưng B đang CẠN HẠN MỨC GHI cả ngày nên sync_keys_from_a ghi qua _soft bị nuốt
    -> key mới vô hình với 18 luồng suốt phiên. Hợp nhất lúc ĐỌC thì key mới dùng được NGAY cả
    khi không ghi nổi vào B.

    TIẾT CHẾ (sửa cùng ngày, soi console thật: A cũng là SPARK FREE 50K đọc/ngày, KHÔNG phải Blaze
    như tưởng): chỉ đọc A khi pool B CHƯA CÓ key gsk_ nào (sync chưa ăn) + tối đa 1 lần/tiến trình.
    Sync A->B ghi thành công là nhánh này tự tắt — chi phí chỉ tồn tại đúng cửa sổ hỏng. (Bản đầu
    đọc lại mỗi 10'/luồng ≈ 56K đọc A/ngày = tự tay giết quota A — chặn trước khi kịp xảy ra.)
    Key chỉ-có-ở-A giữ nguyên doc id của A: cool_key/incr ghi set(merge) theo id sẽ tự tạo doc
    bên B khi quota ghi hồi — tự lành, khỏi cần migrate tay."""
    if os.environ.get("SHARD_KEYS") != "1":
        return rows
    if any(str(r.get("key", "")).startswith("gsk_") for r in rows):
        return rows        # B đã có key Groq (sync đã ăn) -> không đụng tới quota A nữa
    try:
        if _db() is _db_keys():
            return rows
        if _A_KEYS["rows"] is None:
            _cr("merge_keys_A", 70)
            out = []
            for d in _db().collection("gemini_keys").where("owner", "==", owner).stream():
                x = d.to_dict() or {}
                if x.get("key"):
                    out.append({"id": d.id, "key": x["key"], "email": x.get("email", ""),
                                "last_checked": x.get("last_checked", ""), "alive": x.get("alive"),
                                "last_used": x.get("last_used", ""), "cooling_until": x.get("cooling_until", ""),
                                "dead_since": x.get("dead_since", ""), "req_today": 0})
            _A_KEYS["rows"] = out
        have = {r.get("key") for r in rows}
        extra = [r for r in (_A_KEYS["rows"] or []) if r.get("key") not in have]
        if extra:
            print(f"   🔑 Hợp nhất {len(extra)} key CHỈ CÓ Ở A (B chưa ghi được) vào pool phiên này.")
        return rows + extra
    except Exception:
        return rows   # A đọc lỗi thì thôi — B vẫn là nguồn chính


def incr_key_requests(key_id: str, n: int, today: str):
    """Cộng dồn số REQUEST hôm nay của 1 key (reset khi sang ngày mới) -> tính quota còn free trước ngưỡng.
    ~10 kênh chạy SONG SONG có thể cùng dùng chung 1 key (key_order xoay vòng qua TẤT CẢ key của owner) và
    đều gọi hàm này gần như đồng thời cuối phiên (channel_mode() flush) -> đọc-rồi-ghi (read x, set x+n) là
    RACE: worker A đọc req_today=5, worker B cũng đọc 5 (trước khi A ghi xong), A ghi 5+3=8, B ghi 5+2=7 ->
    ghi của B ĐÈ MẤT phần cộng của A -> req_today bị đếm THIẾU -> key tưởng còn nhiều quota hơn thực tế
    (làm sai lệch key_order() ưu tiên "ít request nhất"). Dùng Increment() NGUYÊN TỬ (Firestore cộng dồn
    ở server, không cần đọc trước) cho nhánh cùng ngày -> hết race ở trường hợp phổ biến nhất (trong ngày).
    (Nhánh sang-ngày-mới vẫn đọc-rồi-ghi vì cần biết req_date cũ để quyết định reset hay cộng dồn — hiếm khi
    2 luồng cùng trúng đúng khoảnh khắc sang ngày, rủi ro thấp hơn nhiều.)"""
    from google.cloud import firestore
    _cw("incr_key_requests")
    ref = _db_keys().collection("gemini_keys").document(key_id)
    # BỎ LƯỢT ĐỌC lặp: đọc-trước-ghi chỉ cần cho lần ĐẦU của key trong ngày (quyết định reset hay
    # cộng dồn). Khi tiến trình này đã ghi req_date=today rồi thì các lần sau Increment thẳng —
    # 56 key x nhiều lần flush = hàng chục lượt đọc mỗi luồng, cắt được sạch.
    if _KEY_DATE_OK.get(key_id) == today:
        _soft(lambda: ref.set({"req_today": firestore.Increment(int(n))}, merge=True), "incr_key_requests")
        return
    _cr("incr_key_requests")
    d = ref.get()
    x = (d.to_dict() or {}) if d.exists else {}
    if x.get("req_date") == today:
        _soft(lambda: ref.set({"req_today": firestore.Increment(int(n))}, merge=True), "incr_key_requests")
    else:
        _soft(lambda: ref.set({"req_today": int(n), "req_date": today}, merge=True), "incr_key_requests")
    _KEY_DATE_OK[key_id] = today


def mark_key_alive(key_id: str, alive: bool, reason: str = "", used: bool = False, kind: str = ""):
    """(xoá đệm read_keys khi đánh dấu key CHẾT -> vòng chọn key sau không lấy phải nó nữa)"""
    if not alive:
        _KEYS_CACHE.clear()
    """Ghi trạng thái sống/chết + LÝ DO + thời điểm check -> dashboard hiện 🟢/🔴 + tooltip vì sao.
    kind='permanent' -> CHẾT HẲN (denied/suspended/key sai), KHÔNG tự phục hồi -> health-check bỏ qua test lại.
    used=True: đánh dấu VỪA DÙNG THẬT -> stamp last_used (để lần sau ưu tiên key lâu chưa xài)."""
    patch = {"alive": alive, "dead_reason": ("" if alive else reason), "last_checked": _now(),
             "dead_kind": ("" if alive else kind)}     # "" = có thể tự hồi; "permanent" = chết hẳn
    if used:
        patch["last_used"] = _now()
    if alive:
        patch["dead_since"] = None                     # sống lại -> xoá mốc chết
    else:
        cur = _db_keys().collection("gemini_keys").document(key_id).get()
        if not (cur.exists and (cur.to_dict() or {}).get("dead_since")):
            patch["dead_since"] = _now()               # stamp mốc chết LẦN ĐẦU (giữ nguyên nếu đã chết từ trước)
    _soft(lambda: _db_keys().collection("gemini_keys").document(key_id).set(patch, merge=True), "mark_key_alive")


_COOLED = {}   # key_id -> mốc (epoch) hết nghỉ ĐÃ GHI, để khỏi ghi lại cùng một thứ
_KEY_DATE_OK = {}   # key_id -> ngày đã xác nhận req_date (bỏ lượt đọc lặp ở incr_key_requests)


def sync_keys_from_a(owner: str) -> int:
    """ĐỒNG BỘ KEY MỚI A -> B, tự động mỗi phiên (gọi 1 lần trong plan).

    Khe hở phát hiện 21/8: dashboard/Worker ghi key Gemini mới vào A (Worker chỉ biết A), nhưng
    SHARD_KEYS=1 nên render đọc key từ B. read_keys chỉ lùi về A khi B RỖNG HOÀN TOÀN — nghĩa là
    key thêm sau đợt migrate 56 key sẽ VÔ HÌNH với render vĩnh viễn, trừ khi nhớ bấm workflow
    migrate_keys tay. User thêm key để cứu quota mà hệ không hề dùng tới.

    Chi phí: 1 lượt đọc bảng A/phiên (~56 doc) + chỉ GHI key B còn thiếu (bình thường 0 ghi).
    Ghi qua _soft -> quota chết cũng không gãy plan."""
    if os.environ.get("SHARD_KEYS") != "1":
        return 0
    try:
        db_a = _db()
        db_b = _db_jobs()
        if db_a is db_b:
            return 0
        # SO THEO GIÁ TRỊ KEY, không theo doc id (22/8): id A/B có thể lệch (dashboard .add() sinh
        # id ngẫu nhiên) -> so id thì key mới thành "đã có" hoặc key cũ bị ghi trùng. Giá trị key
        # là danh tính thật.
        _cr("sync_keys_B", 70)
        have = set(); nb = 0
        for d in db_b.collection("gemini_keys").where("owner", "==", owner).stream():
            nb += 1
            v = (d.to_dict() or {}).get("key")
            if v:
                have.add(v)
        _cr("sync_keys_A", 70)
        added = 0; na = 0
        for d in db_a.collection("gemini_keys").where("owner", "==", owner).stream():
            na += 1
            x = d.to_dict() or {}
            if not x.get("key") or x["key"] in have:
                continue
            _cw("sync_keys")
            _soft(lambda _id=d.id, _x=x: db_b.collection("gemini_keys").document(_id).set(_x, merge=True),
                  "sync_keys")
            added += 1
        # LUÔN in số đếm — phiên 04:22Z sync im lặng nên không phân biệt được "0 key mới" với
        # "query A trả 0 dòng (owner lệch)" hay "ghi bị nuốt vì B cạn quota ghi".
        print(f"   🔑 Sync key A->B: A={na} · B={nb} · mới={added}"
              + (" (ghi qua _soft — B cạn quota ghi thì lượt ghi chờ hồi, ĐỌC đã tự hợp nhất từ A)" if added else ""))
        if added:
            _KEYS_CACHE.clear()
        return added
    except Exception as e:
        print(f"   ⚠️ sync_keys A->B lỗi (bỏ qua): {str(e)[:80]}")
        return 0


def cool_key(key_id: str, minutes: int = 20):
    """Đánh dấu key nghỉ N phút sau khi bị 429/quota (chống hammer -> chống die).

    KHỬ TRÙNG LẶP GHI — đây là chỗ đốt hạn mức Firestore nặng nhất và là VÒNG LẶP TỰ SÁT:
    mỗi lỗi 429 của Gemini biến thành 1 lượt GHI Firestore. Đo thật phiên 12:14Z ngày 21/8:
    1.201 lỗi 429 trong MỘT phiên -> 1.201 lượt ghi vào project B; nhân ~15 phiên/ngày là
    ~18.000, gần trọn hạn mức free 20.000/ngày. Càng nhiều 429 càng ghi nhiều -> Firestore chết
    -> cả dây chuyền đứng, dù đã tách 3 project.
    Mà các lượt ghi đó gần như VÔ NGHĨA: key đang nghỉ tới 14:05 thì ghi thêm "nghỉ tới 14:05"
    hàng trăm lần nữa cũng không đổi gì. Giờ chỉ ghi khi mốc nghỉ THỰC SỰ lùi xa thêm >60s.
    Bộ nhớ đệm này theo tiến trình -> mỗi luồng tự giữ, không cần đọc thêm."""
    import time as _t
    now = _t.time()
    until_ts = now + minutes * 60
    prev = _COOLED.get(key_id, 0)
    if prev > now and until_ts <= prev + 60:
        # KHÔNG xoá đệm ở nhánh khử-trùng-lặp: key đã có trong sổ _COOLED cục bộ, key_order tự né
        # (xem key_manager). Xoá ở đây = trong bão 429 mọi read_keys thành lượt đọc THẬT cả bảng.
        return
    from datetime import timedelta
    until = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()
    _cw("cool_key")
    _soft(lambda: _db_keys().collection("gemini_keys").document(key_id).set({"cooling_until": until}, merge=True), "cool_key")
    _COOLED[key_id] = until_ts
    # XOÁ ĐỆM read_keys NGAY: nếu không, tiến trình này còn dùng danh sách cũ tới 3 phút và tiếp tục
    # chọn đúng key vừa bị phạt -> ăn thêm 429 liên tiếp, đúng thứ cool_key sinh ra để tránh.
    _KEYS_CACHE.clear()


def update_storage_used(owner: str, name: str, used: int, cap_gb=None):
    """Ghi dung lượng THẬT của 1 kho vào storage_accounts.used (render upload KHÔNG tự cập nhật số này ->
    phải sync để display + guard-kho-đầy chính xác). Doc id khớp Worker: {owner}__{name}."""
    patch = {"used": int(used or 0), "used_synced_at": _now()}
    if cap_gb:
        patch["cap_gb"] = cap_gb
    _soft(lambda: _db().collection("storage_accounts").document(f"{owner}__{name}").set(patch, merge=True), "update_storage_used")


def drive_usage(owner: str):
    """Tổng dung lượng ĐÃ DÙNG / SỨC CHỨA của mọi kho Drive (bytes) -> guard 'kho gần đầy' trước khi render."""
    used = cap = 0
    try:
        for d in _db().collection("storage_accounts").where("owner", "==", owner).stream():
            x = d.to_dict() or {}
            used += (x.get("used", 0) or 0)
            cap += (x.get("cap_gb", 15) or 15) * 1_000_000_000
    except Exception as e:
        print(f"   ⚠️ drive_usage lỗi ({e})")
    return used, cap


def read_channels(owner: str) -> list[dict]:
    _cr("read_channels", 40)
    def _do():
        db = _db_meta(); out = []
        for d in db.collection("render_channels").where("owner", "==", owner).stream():
            x = d.to_dict() or {}; x["id"] = d.id; out.append(x)
        return out
    return _retry(_do)


def read_one_channel(owner: str, name: str) -> dict | None:
    """Đọc ĐÚNG 1 kênh theo tên (1 read) — dùng trong vòng lặp render để check pause/target mà KHÔNG đọc cả 15 kênh."""
    def _do():
        q = (_db_meta().collection("render_channels").where("owner", "==", owner)
             .where("name", "==", name).limit(1).stream())
        for d in q:
            x = d.to_dict() or {}; x["id"] = d.id; return x
        return None
    try:
        return _retry(_do)
    except Exception:
        return None


def read_config(owner: str) -> dict:
    _cr("read_config", 1)
    import time as _t
    if _t.time() < _RQ_DEAD["until"]:
        return dict(_CFG_LAST.get(owner) or {})   # quota đọc chết -> bản đệm/mặc định, không crash
    def _do():
        d = _db_meta().collection("render_config").document(owner).get()
        return (d.to_dict() or {}) if d.exists else {}
    try:
        out = _retry(_do)
        _CFG_LAST[owner] = out
        return out
    except Exception as e:
        if _wq_exhausted(e):
            _RQ_DEAD["until"] = _t.time() + 15 * 60
            if not _RQ_DEAD["warned"]:
                _RQ_DEAD["warned"] = True
                print("🩹 Firestore HẾT HẠN MỨC ĐỌC (read_config) -> dùng config đệm, luồng chạy tiếp.")
            return dict(_CFG_LAST.get(owner) or {})
        raise


def read_render_requests(owner: str) -> list[dict]:
    """Yêu cầu RENDER LẠI (từ nút 🔄 trên dashboard) đang chờ xử lý."""
    _cr("read_render_requests", 5)
    db = _db_meta(); out = []
    # limit 40: hàng đợi yêu cầu render lại hiếm khi dài; chặn để lỡ sai điều kiện cũng không quét cả bảng.
    for d in db.collection("render_requests").where("owner", "==", owner).where("status", "==", "pending").limit(40).stream():
        x = d.to_dict() or {}; x["id"] = d.id; out.append(x)
    return out


def find_done_before(owner: str, channel: str, vtype: str, before_iso: str, limit: int = 12) -> list[dict]:
    """Video ĐÃ XONG của 1 kênh, tạo TRƯỚC mốc `before_iso` — dùng để xếp render lại những bản ra đời
    khi pipeline còn lỗi. Truy vấn khớp ĐÚNG composite index đã deploy
    (owner+channel+type+status+created_at) nên không phải quét bảng.
    Bỏ qua bản đã xếp hàng rồi (requeued) để chạy nhiều phiên không tạo trùng."""
    try:
        q = (_db_jobs().collection("render_jobs")
             .where("owner", "==", owner).where("channel", "==", channel)
             .where("type", "==", vtype).where("status", "==", "done")
             .where("created_at", "<", before_iso)
             .order_by("created_at").limit(int(limit)))
        out = []
        for d in q.stream():
            x = d.to_dict() or {}
            if x.get("requeued"):
                continue
            x["id"] = d.id
            out.append(x)
        return out
    except Exception as e:
        print(f"   ⚠️ find_done_before {channel}: {str(e)[:90]}")
        return []


def new_render_request(owner: str, channel: str, vtype: str, seed: str,
                       replace_id: str = "", replace_account: str = "") -> str:
    """Tạo yêu cầu render lại — CÙNG schema với nút 🔄 trên dashboard, nên process_requests xử lý
    y hệt: dựng lại từ kịch bản đã lưu, đẩy Drive, rồi BỎ bản cũ vào thùng rác."""
    ref = _db_meta().collection("render_requests").document()
    _soft(lambda: ref.set({"owner": owner, "channel": channel, "type": vtype, "seed": seed or "",
             "replace_id": replace_id or "", "replace_account": replace_account or "",
             "status": "pending", "created_at": _now()}), "new_render_request")
    return ref.id


def mark_job_requeued(job_id: str, req_id: str = ""):
    """Đánh dấu job đã xếp hàng render lại -> phiên sau không tạo yêu cầu trùng cho nó nữa."""
    try:
        _soft(lambda: _db_jobs().collection("render_jobs").document(job_id).set(
            {"requeued": True, "rerender": "chờ render lại", "rerender_req": req_id}, merge=True),
            "mark_job_requeued")
    except Exception:
        pass


def delete_jobs_by_drive(owner: str, drive_id: str):
    """Xóa bản ghi job cũ theo drive_id (sau khi render lại đã thay thế + bỏ file cũ)."""
    if not drive_id:
        return
    # limit 5: một drive_id chỉ gắn với 1-2 job; không chặn thì lỡ query sai điều kiện là quét cả bảng.
    for d in (_db_jobs().collection("render_jobs").where("owner", "==", owner)
              .where("drive_id", "==", drive_id).limit(5).stream()):
        try:
            _soft(lambda: d.reference.delete(), "delete_jobs_by_drive")
        except Exception:
            pass


def get_script_by_drive(owner: str, drive_id: str):
    """Lấy KỊCH BẢN đã lưu của video cũ (theo drive_id) để RENDER LẠI đúng nội dung đó.
    Mỗi video 'done' được đóng kèm script (xem _script_json ở run_render.py) -> bấm 🔄 không cần
    gọi lại Gemini: vừa KHỎI TỐN QUOTA, vừa ra ĐÚNG video cũ (chỉ khác bản dựng), thay vì viết một
    kịch bản MỚI hoàn toàn khác như trước đây. Không có/hỏng -> None (tự viết mới như cũ)."""
    if not drive_id:
        return None
    try:
        for d in (_db_jobs().collection("render_jobs").where("owner", "==", owner)
                  .where("drive_id", "==", drive_id).limit(3).stream()):
            s = (d.to_dict() or {}).get("script")
            if s:
                try:
                    return json.loads(s)
                except Exception:
                    return None
    except Exception as e:
        print(f"   ⚠️ get_script_by_drive lỗi ({e}) — viết mới bình thường")
    return None


def read_thumb_requests(owner: str, limit: int = 40) -> list[dict]:
    """Yêu cầu TẠO LẠI THUMBNAIL từ nút trên dashboard (collection thumb_requests)."""
    out = []
    try:
        q = (_db_meta().collection("thumb_requests").where("owner", "==", owner)
             .where("status", "==", "pending").limit(limit))   # chặn ngay ở TRUY VẤN, không phải sau khi đã đọc về
        for d in q.stream():
            x = d.to_dict() or {}; x["id"] = d.id; out.append(x)
            if len(out) >= limit:
                break
    except Exception as e:
        print(f"   ⚠️ read_thumb_requests lỗi: {e}")
    return out


def mark_thumb_request(req_id: str, status: str, note: str = "", attempt: int = None):
    try:
        patch = {"status": status, "note": note[:120], "done_at": _now()}
        if attempt is not None:
            patch["attempt"] = attempt
        _soft(lambda: _db_meta().collection("thumb_requests").document(req_id).set(patch, merge=True), "mark_thumb_request")
    except Exception as e:
        print(f"   ⚠️ mark_thumb_request lỗi: {e}")


def mark_request_status(req_id: str, status: str):
    """processing = đã bắt đầu render lại -> dashboard KHÓA nút hủy."""
    _soft(lambda: _db_meta().collection("render_requests").document(req_id).set({"status": status, "started_at": _now()}, merge=True), "mark_request_status")


def mark_request_done(req_id: str, note: str = "done"):
    _soft(lambda: _db_meta().collection("render_requests").document(req_id).set({"status": "done", "note": note, "done_at": _now()}, merge=True), "mark_request_done")


def where_am_i() -> str:
    """In RÕ mỗi client đang nối vào project NÀO — hết đoán mò khi dính 429.

    Vì sao cần (21/8): _db_jobs() TỰ LÙI về A khi thiếu/hỏng creds B. Nên khi thấy '429 Quota
    exceeded' lúc ghi render_config, không thể biết đang cạn hạn mức của B hay của A — mà hai
    project có gói riêng, nâng nhầm project thì không giải quyết được gì.
    Trả chuỗi 1 dòng, gọi lúc bắt đầu plan."""
    def _pid(c):
        try:
            return getattr(c, "project", None) or "?"
        except Exception:
            return "?"
    parts = []
    try: parts.append(f"A={_pid(_db())}")
    except Exception: parts.append("A=lỗi")
    try:
        jb = _db_jobs()
        tag = "B" if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_B") else "B(thiếu creds)"
        parts.append(f"{tag}={_pid(jb)}")
    except Exception: parts.append("B=lỗi")
    try:
        pb = _db_pub()
        parts.append(f"C={_pid(pb) if pb else 'tắt'}")
    except Exception: parts.append("C=lỗi")
    parts.append(f"SHARD_META={os.environ.get('SHARD_META') or '0'}")
    parts.append(f"SHARD_KEYS={os.environ.get('SHARD_KEYS') or '0'}")
    return "🗺️ Firestore: " + " · ".join(parts)


def set_config(owner: str, patch: dict):
    """Ghi/merge render_config (vd xoá cờ run_now sau khi đã nhận lệnh)."""
    _cw("set_config")
    _soft(lambda: _db_meta().collection("render_config").document(owner).set(patch, merge=True), "set_config")


_TOPICS_CACHE = {}   # (owner,channel) -> list; xoá khi save_topics (nguồn đổi duy nhất trong phiên)


def recent_topics(owner: str, channel: str, n: int = 80) -> list[str]:
    """Chủ đề ĐÃ dùng cho kênh -> đưa cho Gemini để TRÁNH trùng (chống 'reused content').

    ĐỆM THEO TIẾN TRÌNH: bị gọi ở 6 điểm trong run_render; kênh chạy nhiều vòng thì thành hàng
    chục lượt đọc cho CÙNG một doc chỉ đổi khi chính mình save_topics. Đệm + xoá lúc save_topics
    -> mỗi kênh còn ~1-2 lượt đọc thật."""
    ck = (owner, channel)
    if ck in _TOPICS_CACHE:
        return _TOPICS_CACHE[ck][-n:]
    _cr("recent_topics")
    try:
        d = _db_meta().collection("render_topics").document(f"{owner}__{channel}").get()
        out = (((d.to_dict() or {}).get("topics") or [])) if d.exists else []
    except Exception:
        return []   # đọc lỗi (quota) -> coi như chưa có; KHÔNG đệm để lượt sau thử lại thật
    _TOPICS_CACHE[ck] = out
    return out[-n:]


def save_topics(owner: str, channel: str, topics: list[str]):
    """Lưu chủ đề vừa dùng (cap 300 gần nhất)."""
    _TOPICS_CACHE.pop((owner, channel), None)   # nguồn vừa đổi -> lượt đọc sau lấy bản mới
    ref = _db_meta().collection("render_topics").document(f"{owner}__{channel}")
    d = ref.get()
    cur = (((d.to_dict() or {}).get("topics") or [])) if d.exists else []
    cur = (cur + [t for t in topics if t])[-300:]
    _cw("save_topics")
    _soft(lambda: ref.set({"owner": owner, "channel": channel, "topics": cur}, merge=True), "save_topics")


def read_trend_scout(owner: str, channel: str) -> list[str]:
    """Xu hướng/góc độ (tóm tắt bởi Gemini từ title kênh lớn tham khảo, xem trend_scout.py) -> đưa
    thêm vào niche khi viết kịch bản. Rỗng nếu chưa quét lần nào (bình thường)."""
    try:
        d = _db_meta().collection("trend_scout").document(f"{owner}__{channel}").get()
        return (d.to_dict() or {}).get("trends") or [] if d.exists else []
    except Exception as e:
        print(f"   ⚠️ read_trend_scout lỗi ({e})"); return []


def save_trend_scout(owner: str, channel: str, trends: list[str]):
    """Ghi đè (không cộng dồn vô hạn) — mỗi lần quét lại là bản MỚI thay bản cũ, tránh phình."""
    try:
        _soft(lambda: _db_meta().collection("trend_scout").document(f"{owner}__{channel}").set(
            {"owner": owner, "channel": channel, "trends": trends[:5], "updated_at": _now()}, merge=True), "save_trend_scout")
    except Exception as e:
        print(f"   ⚠️ save_trend_scout {channel} lỗi: {e}")


def _shard_on() -> bool:
    """Có bật shard render_jobs sang Project B không (creds B đầy đủ)."""
    k = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_B")
    return bool(k and os.environ.get("FIREBASE_PROJECT_ID_B") and os.path.exists(k))


def _count_jobs(db, owner: str, channel: str, vtype: str = None) -> int:
    q = (db.collection("render_jobs").where("owner", "==", owner)
         .where("channel", "==", channel).where("status", "==", "done"))
    if vtype:
        q = q.where("type", "==", vtype)
    try:
        res = q.count().get()                    # aggregation: ~1 read thay vì N
        row = res[0]; ar = row[0] if isinstance(row, (list, tuple)) else row
        return int(ar.value)
    except Exception as e:
        # ĐỪNG lùi về đếm thủ công cả collection: khi quota cạn thì count() lỗi -> stream() đọc HÀNG
        # NGHÌN doc -> càng cạn nhanh hơn (vòng xoáy chết, đúng sự cố 20/8). Đếm có giới hạn: đủ để
        # biết "đã đạt target chưa" vì target lớn nhất chỉ 30.
        try:
            return sum(1 for _ in q.limit(200).stream())
        except Exception:
            print(f"   ⚠️ đếm {channel}/{vtype} lỗi ({str(e)[:50]}) -> coi như 0, phiên sau đếm lại")
            return 0


def has_active_render(owner: str) -> bool:
    """Còn job render nào ĐANG CHẠY THẬT (B) không -> gate mở phiên MỚI ngay khi phiên trước xong hẳn
    (thay vì đoán 1 khoảng thời gian cố định) -> lấp khoảng nghỉ hiệu quả, không chồng phiên, không chờ oan."""
    ACTIVE = ["queued", "running", "writing", "rendering", "qc"]
    GHOST_H = 6      # job CŨ (chưa có updated_at): > 6h = chắc chắn chết (workflow timeout 350' = 5.8h)
    STALE_MIN = 30   # job MỚI (có nhịp tim ~90s/lần): im lặng 30' ≈ lỡ 20 nhịp -> chết. Nhanh hơn 12 lần.
    try:
        db = _db_jobs()
        q = (db.collection("render_jobs").where("owner", "==", owner)
             .where("status", "in", ACTIVE))
        res = q.count().get()                     # aggregation: ~1 read (đường nhanh, ca phổ biến = 0)
        row = res[0]; ar = row[0] if isinstance(row, (list, tuple)) else row
        n = int(ar.value)
        if n == 0:
            return False
        # 20/8: TRƯỚC ĐÂY return n>0 luôn -> job MA (tiến trình đã chết nhưng status kẹt ở qc/writing)
        # bị tính là "đang chạy" -> CHẶN mọi mẻ render mới cho tới khi health_guardian dọn (chỉ dọn khi
        # job đủ 6h). Sáng 20/8: 39 job kẹt vì bug treo Gemini Vision -> gate khoá suốt, mẻ 12:00 UTC
        # sắp mất trắng dù KHÔNG có gì chạy thật. Giờ đọc thêm để BỎ QUA job quá GHOST_H giờ -> gate tự
        # lành, không phụ thuộc health_guardian chạy đúng lúc.
        from datetime import datetime as _dt, timezone as _tz, timedelta as _td
        now_ = _dt.now(_tz.utc)
        cut_created = now_ - _td(hours=GHOST_H)          # job CŨ chưa có updated_at -> đành đo theo tuổi
        cut_beat = now_ - _td(minutes=STALE_MIN)         # job MỚI có nhịp tim -> đo theo lần ghi cuối
        live = 0
        for d in q.limit(60).stream():            # chỉ chạy khi n>0; 60 = trần an toàn (matrix tối đa 18)
            x = d.to_dict() or {}
            ts, cut = x.get("updated_at"), cut_beat
            if not ts:                            # job tạo TRƯỚC bản vá nhịp tim -> lùi về đo tuổi
                ts, cut = x.get("created_at"), cut_created
            try:
                if _dt.fromisoformat(str(ts).replace("Z", "+00:00")) > cut:
                    live += 1
                    break                          # thấy 1 job CÒN SỐNG là đủ kết luận -> dừng đọc sớm
            except Exception:
                live += 1; break                   # không đọc được giờ -> coi như còn sống (an toàn, không chồng phiên)
        if live == 0:
            print(f"   🧹 {n} job 'active' đều quá {GHOST_H}h (job ma, tiến trình đã chết) -> KHÔNG chặn phiên mới.")
        return live > 0
    except Exception as e:
        print(f"   ⚠️ has_active_render lỗi ({e}) — coi như KHÔNG active (fail-open, tránh gate treo mãi)")
        return False


_LEGACY_COUNT = {}     # (owner, kênh, loại) -> số job cũ ở Project A (bất biến)


def count_done(owner: str, channel: str, vtype: str = None) -> int:
    """Đếm số video ĐÃ XONG của 1 kênh (so target). Đếm CẢ Project B (job mới) + A (job CŨ trước shard) -> không sót, không làm THỪA.
    Dùng aggregation count() = ~1 read/project."""
    _cr("count_done", 1)
    total = 0
    try:
        total += _count_jobs(_db_jobs(), owner, channel, vtype)          # B (hoặc A nếu chưa shard)
    except Exception as e:
        print(f"   ⚠️ count_done B lỗi ({e})")
    if _shard_on():
        # Job CŨ nằm ở A là dữ liệu LỊCH SỬ — từ khi bật shard (19/8) không có job mới nào ghi vào A
        # nữa, nên con số này KHÔNG BAO GIỜ ĐỔI. Trước đây đếm lại mỗi lần gọi: plan_mode gọi cho
        # 40 kênh × 2 loại = 80 lượt đọc THỪA trên Project A mỗi phiên, cộng thêm mỗi kênh gọi lại
        # trong run_one. Đệm theo tiến trình -> mỗi (kênh, loại) chỉ đọc A đúng 1 lần.
        ck = (owner, channel, vtype)
        if ck not in _LEGACY_COUNT:
            try:
                _LEGACY_COUNT[ck] = _count_jobs(_db(), owner, channel, vtype)
            except Exception as e:
                print(f"   ⚠️ count_done A lỗi ({e})")
                _LEGACY_COUNT[ck] = 0
        total += _LEGACY_COUNT[ck]
    return total


def find_resumable(owner: str, channel: str, vtype: str):
    """CHECKPOINT: job THẤT BẠI gần nhất của kênh này còn giữ kịch bản (script, ghi lúc 'rendering' —
    TRƯỚC bước render tốn thời gian nhất) -> dùng lại thay vì gọi Gemini viết mới, đỡ tốn quota + tránh
    lệch nội dung/chủ đề đã ghi vào ngân hàng. CHỈ lấy job status='failed' (đã CHẮC CHẮN không ai còn xử
    lý — do lỗi thật hoặc Health Guardian tự đánh dấu job treo) -> an toàn, không đụng job đang chạy thật.
    Trả {'job_id', 'story'} hoặc None (không có gì để resume -> viết mới bình thường như cũ)."""
    _cr("find_resumable", 5)
    try:
        db = _db_jobs()
        q = (db.collection("render_jobs").where("owner", "==", owner).where("channel", "==", channel)
             .where("type", "==", vtype).where("status", "==", "failed"))
        # limit 25: hàm này chạy 36 lần/phiên (18 kênh x 2 loại). Không giới hạn thì mỗi lần quét
        # TOÀN BỘ job failed (hàng trăm) -> vài nghìn lượt đọc/phiên, thừa sức thổi bay hạn mức free.
        # Chỉ cần vài ứng viên gần nhất là đủ chọn checkpoint.
        # ƯU TIÊN sắp theo MỚI NHẤT rồi lấy 5 — vừa đúng thứ ta cần (checkpoint gần nhất), vừa cắt
        # 80% lượt đọc: hàm này chạy 54 lần/phiên (18 kênh x 3 đường) nên 25 -> 5 là bớt ~1.100
        # lượt đọc mỗi phiên. Thiếu composite index thì lùi về quét thô 25 như cũ (giống cách
        # top_titles đã làm) -> không gãy khi index chưa tạo.
        try:
            from google.cloud.firestore_v1 import Query
            cands = [(d.id, d.to_dict() or {})
                     for d in q.order_by("created_at", direction=Query.DESCENDING).limit(5).stream()]
        except Exception:
            cands = [(d.id, d.to_dict() or {}) for d in q.limit(25).stream()]
        cands = [(i, j) for i, j in cands if j.get("script")]
        if not cands:
            return None
        cands.sort(key=lambda x: x[1].get("created_at", ""), reverse=True)   # ưu tiên bản GẦN NHẤT
        job_id, job = cands[0]
        story = json.loads(job["script"])
        if not story:
            return None
        return {"job_id": job_id, "story": story}
    except Exception as e:
        print(f"   ⚠️ find_resumable lỗi ({e}) — bỏ qua, viết mới bình thường"); return None


def clear_resumed(job_id: str):
    """Đã DÙNG XONG checkpoint (resume thành công hoặc thất bại lại) -> xoá script khỏi job CŨ,
    tránh 2 lần resume cùng 1 kịch bản (lẫn lộn/trùng)."""
    try:
        _soft(lambda: _db_jobs().collection("render_jobs").document(job_id).set(
            {"script": "", "step": "♻️ đã dùng để resume phiên sau"}, merge=True), "clear_resumed")
    except Exception as e:
        print(f"   ⚠️ clear_resumed {job_id} lỗi: {e}")


def new_job(owner: str, channel: str, vtype: str = "short", pver: str = "") -> str:
    _cw("new_job")
    db = _db_jobs(); ref = db.collection("render_jobs").document()   # id sinh OFFLINE -> quota chết vẫn có id
    _soft(lambda: ref.set({"owner": owner, "channel": channel, "type": vtype, "pver": pver,   # pver = phiên bản pipeline -> dọn thông minh (chỉ xóa bản CŨ)
             "status": "queued", "step": "bắt đầu", "created_at": _now()}), "new_job")
    return ref.id


_LAST_JOB_WRITE = {}


def update_job(job_id: str, **patch):
    # TIẾT KIỆM Firestore write (100% FREE, dưới trần 20K ghi/ngày):
    #   - status CUỐI (done/failed/ratelimited): LUÔN ghi.
    #   - status trung gian: CHỈ ghi 1 lần/~90s/job (heartbeat thưa cho dashboard biết còn sống); còn lại BỎ.
    import time as _t
    st = patch.get("status")
    if st not in ("done", "failed", "ratelimited") and "script" not in patch:
        # patch mang 'script' = CHECKPOINT kịch bản (từng-phần) — quý, thưa, và mất là trả Gemini
        # lần 2 -> MIỄN hãm 300s. Chỉ hãm các mốc trạng thái trang trí (writing/rendering/qc).
        now = _t.time()
        # HÃM 5 PHÚT (trước 90s). Tính thật: ở đỉnh 172 video/giờ, mỗi video ~7 lượt ghi -> 28.896
        # lượt/ngày trong khi gói FREE chỉ cho 20.000 -> cạn sau ~16 tiếng, đúng sự cố 20/8. Phần
        # lớn số đó là các mốc trạng thái trung gian (writing/rendering/qc) chỉ để dashboard nhìn
        # cho đẹp. Hãm 5' cắt gần hết chúng mà KHÔNG mất gì: nhịp tim (cũng 5') vẫn báo job còn
        # sống, còn done/failed thì LUÔN ghi ngay không qua hãm.
        if now - _LAST_JOB_WRITE.get(job_id, 0) < 300:
            return
        _LAST_JOB_WRITE[job_id] = now
    # ĐÓNG DẤU THỜI GIAN mỗi lần ghi = NHỊP TIM có mốc. Trước đây job có nhịp tim (ghi lại mỗi ~90s)
    # nhưng KHÔNG lưu mốc -> muốn biết job còn sống hay đã chết chỉ còn cách đo TUỔI (created_at), phải
    # chờ tới 6h mới dám kết luận "chết" -> job ma khoá gate has_active_render() suốt 6 TIẾNG dù tiến
    # trình đã chết từ lâu (20/8: 39 job ma chặn mọi mẻ render mới). Có mốc này -> chỉ cần ~30' im lặng
    # (≈20 nhịp tim lỡ) là kết luận chết được, gate thoát nhanh hơn 12 lần.
    _cw("update_job")
    patch = dict(patch); patch["updated_at"] = _now()
    _soft(lambda: _db_jobs().collection("render_jobs").document(job_id).set(patch, merge=True), "update_job")
    # NHỊP TIM THẬT: bật/tắt theo trạng thái vừa ghi (xem _beat_loop bên dưới).
    _beat_set(None if st in ("done", "failed", "ratelimited") else job_id)


# ── NHỊP TIM NỀN ────────────────────────────────────────────────────────────────────────────────
# update_job() CHỈ ghi khi CÓ NGƯỜI GỌI — nó là bộ hãm ghi, không phải máy phát nhịp. Mà bước nặng
# nhất (`npx remotion render`) chạy liền 20-40 phút KHÔNG gọi update_job lần nào -> job im lặng suốt,
# rồi health_guardian thấy "im lặng quá 30'" và GIẾT NHẦM job đang render khoẻ mạnh (20/8: 15 job bị
# giết oan ngay giữa phiên). Luồng nền này đóng dấu updated_at mỗi 2 phút chừng nào tiến trình còn
# sống -> "im lặng" mới thực sự đồng nghĩa với "đã chết".
_BEAT = {"job": None, "th": None}


# NHỊP 5 PHÚT (không phải 2'): 18 kênh chạy song song mà ghi mỗi 2' = ~13K lượt ghi/ngày, ngốn gần
# trọn hạn mức FREE 20K/ngày của Firestore -> 20/8 publish_social ăn "ResourceExhausted: 429 Quota
# exceeded". Mốc coi-là-chết là 45' nên 5'/nhịp vẫn còn 9 nhịp dự phòng, thừa an toàn, mà lượng ghi
# giảm 2.5 lần (~5K/ngày).
BEAT_SEC = 900   # 15' — health_guardian coi job chết sau STALE_BEAT_MIN=45' im lặng, tức vẫn còn 3
                 # nhịp dự phòng. Trước để 5' -> 18 luồng x 12 nhịp/giờ x ~1.5h = ~320 lượt GHI mỗi
                 # phiên chỉ để chứng minh "còn sống". Project B free chỉ 20K ghi/ngày mà render đã
                 # ăn gần hết (sự cố 21/8: B cạn ghi lúc 10:21Z) -> cắt 3 lần phần này.


def _beat_loop():
    import time as _t
    while True:
        _t.sleep(BEAT_SEC)
        jid = _BEAT.get("job")
        if not jid:
            continue
        try:
            _cw("nhip_tim")
            _db_jobs().collection("render_jobs").document(jid).set({"updated_at": _now()}, merge=True)
        except Exception:
            pass          # mạng chập chờn -> bỏ nhịp này, nhịp sau ghi bù


def _beat_set(job_id):
    import threading
    _BEAT["job"] = job_id
    if job_id and _BEAT.get("th") is None:
        th = threading.Thread(target=_beat_loop, daemon=True)   # daemon -> không giữ tiến trình khi xong
        _BEAT["th"] = th
        th.start()
