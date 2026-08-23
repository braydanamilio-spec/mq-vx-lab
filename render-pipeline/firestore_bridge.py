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
_B2 = {"on": False, "client": None, "wclient": None}


def _b2_available() -> bool:
    """B2 = Firestore DỰ PHÒNG (23/8, project mm0-shard-b2): cùng service account của B (đã cấp
    datastore.owner trên B2), chỉ cần FIREBASE_PROJECT_ID_B2 trong env — KHÔNG cần secret mới."""
    return bool(os.environ.get("FIREBASE_PROJECT_ID_B2") and os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_B")
                and os.path.exists(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_B", "")))


def failover_to_b2(reason: str) -> bool:
    """CÔNG TẮC TỰ ĐỘNG: B chính cạn quota (đọc hoặc ghi) -> toàn bộ client B trỏ sang B2 cho phần
    còn lại của tiến trình. B2 được plan gương sẵn channels/config/keys mỗi phiên khi B khỏe, nên
    lật sang là chạy được ngay. Đêm 22/8 đứng máy 9 tiếng vì không có đường này."""
    if _B2["on"] or not _b2_available():
        return _B2["on"]
    try:
        from google.cloud import firestore
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(os.environ["GOOGLE_APPLICATION_CREDENTIALS_B"])
        _B2["client"] = firestore.Client(project=os.environ["FIREBASE_PROJECT_ID_B2"], credentials=creds)
        _B2["on"] = True
        _RQ_DEAD["until"] = 0          # mở lại đường đọc — giờ đọc là đọc B2
        _WQ_DEAD["until"] = 0
        age = "?"
        try:
            m = _B2["client"].collection("render_config").document("mirror_meta").get()
            if m.exists:
                at = datetime.fromisoformat((m.to_dict() or {}).get("at", ""))
                age = f"{int((datetime.now(timezone.utc) - at).total_seconds() // 60)} phút"
        except Exception:
            pass
        print(f"🔀 FAILOVER: B chính nghẽn ({reason[:60]}) -> chuyển sang B2 (gương tuổi {age}).")
        return True
    except Exception as e:
        print(f"   ⚠️ failover B2 lỗi ({str(e)[:60]}) — ở lại B, chạy chế độ đệm.")
        return False


def _db_jobs():
    """Client cho collection render_jobs -> Project B (SHARD, giảm tải A) nếu có creds B; KHÔNG thì dùng A (backward-compatible)."""
    if _B2["on"] and _B2["client"] is not None:
        return _B2["client"]
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
    ck = ("tt", owner, channel, n)
    if ck in _HOT_CACHE:
        return _HOT_CACHE[ck]           # gu khán giả không đổi trong 1 luồng -> đọc C đúng 1 lần (đo 22/8: 32 lượt/luồng -> 1)
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
        _HOT_CACHE[("tt", owner, channel, n)] = out
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


def flush_rw_ledger(owner: str):
    """SỔ TỔNG ĐỌC/GHI THEO NGÀY (23/8): đêm 22/8 quota ĐỌC B cháy ngầm từ trưa mà không ai thấy vì
    chỉ soi từng luồng, không cộng lũy kế cả ngày -> tối lộ ra thì đã muộn, dây chuyền đứng tới reset.
    Mỗi tiến trình cuối đời cộng dồn số ĐO THẬT vào doc render_stats/__rw__ theo ngày (field-Increment,
    1 lượt ghi). Plan đọc lại 1 lượt/phiên -> chuông báo 60%/85% NGAY TRONG NGÀY, không đợi chết mới biết."""
    try:
        if not (_WRITES["n"] or _READS["n"]):
            return
        from google.cloud.firestore_v1 import Increment
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        _soft(lambda: _db_jobs().collection("render_stats").document(f"__rw__{owner}").set(
            {day: {"r": Increment(_READS["n"]), "w": Increment(_WRITES["n"])}}, merge=True), "rw_ledger")
    except Exception:
        pass


def read_rw_ledger(owner: str) -> tuple:
    """(đọc, ghi) lũy kế HÔM NAY từ sổ tổng — plan gọi 1 lần/phiên để rung chuông sớm."""
    try:
        _cr("rw_ledger", 1)
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        d = _db_jobs().collection("render_stats").document(f"__rw__{owner}").get()
        x = ((d.to_dict() or {}).get(day) or {}) if d.exists else {}
        return int(x.get("r", 0)), int(x.get("w", 0))
    except Exception:
        return -1, -1


def count_pushed(owner: str, drive_id: str = "", channel: str = "", vtype: str = ""):
    """SỔ ĐẾM VIDEO ĐÃ THẬT SỰ LÊN KHO (23/8 — user: "số phải khớp nhau").

    Vì sao cần: dashboard trước đây lấy "Tổng cộng dồn" bằng cách đếm BẢN GHI JOB (status=done),
    trong đó có cả video render lại và video CHƯA đẩy được kho -> hiện 1755 trong khi kho chỉ có
    61. Hai ô đo hai thứ khác nhau nên không bao giờ khớp.

    Giờ: MỌI lượt đẩy kho THÀNH CÔNG (có drive_id) cộng đúng 1 vào doc đếm này. Dashboard đọc 1 doc
    -> "Tổng" và "Hôm nay" luôn = số video CÓ THẬT trong kho, khớp với thư viện.
    Chống đếm trùng: nhớ 400 drive_id gần nhất trong RAM tiến trình (render lại cùng video sẽ có
    drive_id MỚI nên vẫn tính 1 — đúng, vì đó là file mới trong kho)."""
    if not drive_id:
        return
    _seen = count_pushed.__dict__.setdefault("_seen", [])
    if drive_id in _seen:
        return
    _seen.append(drive_id)
    del _seen[:-400]
    try:
        from google.cloud.firestore_v1 import Increment
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        patch = {"total": Increment(1), day: Increment(1), "at": _now()}
        if channel:
            patch[f"ch_{str(channel).upper()}"] = Increment(1)
        _soft(lambda: _db_jobs().collection("render_stats").document(f"__pushed__{owner}")
              .set(patch, merge=True), "count_pushed")
    except Exception:
        pass


def quota_pulse(owner: str):
    """1 nhịp/tiến trình: đọc sổ quota ngày (1 lượt), in trạng thái, ≥90% trần thì gương tươi + LẬT
    B2 CHỦ ĐỘNG (23/8, user đề xuất — lật lúc B còn sống = dữ liệu khớp 100%, khỏi chờ chết mới lật).
    Gọi ở đầu plan VÀ đầu mỗi lane (lane là tiến trình riêng, quyết định của plan không tự lan sang)."""
    try:
        r, w = read_rw_ledger(owner)
        if r < 0:
            return
        msg = f"📟 Sổ quota hôm nay: ĐỌC {r:,}/50.000 · GHI {w:,}/20.000"
        if r > 45000 or w > 18000:
            print("   " + msg + " — 🚨 ≥90% TRẦN: gương tươi + LẬT B2 CHỦ ĐỘNG trước khi cạn.")
            try:
                mirror_b_to_b2(owner)
            except Exception:
                pass
            failover_to_b2("chủ động ≥90% trần ngày")
        elif r > 42500 or w > 17000:
            print("   " + msg + " — 🚨 SÁT TRẦN (85%): chạy tằn tiện tối đa")
        elif r > 30000 or w > 12000:
            print("   " + msg + " — ⚠️ qua 60%: để mắt, tránh mở việc đọc nặng")
        else:
            print("   " + msg)
    except Exception:
        pass


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
                # 23/8 tối: chỉ thử lại khi là BURST theo phút. Cạn hạn mức NGÀY mà vẫn thử 5 lần thì
                # mỗi lệnh mất thêm ~15s vô ích — nhân 110 lệnh là treo cả phiên.
                if _t.time() < _RQ_DEAD["until"]:
                    raise
                _t.sleep(1.5 * (i + 1)); continue
            raise


_KEYS_CACHE = {}      # (owner, include_cooling) -> (thời điểm, kết quả)
_HOT_CACHE = {}       # đệm tiến-trình cho các hàm đọc NÓNG (top_titles/resume/config/count) — 22/8:
                      # đo VAULTUSA 113 đọc/luồng thì 105 là 4 hàm này gọi lặp cho CÙNG câu trả lời
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
            # 23/8: GHI cạn cũng lật B2 (fn bám client cũ nên lượt này vào _PENDING xả lại trên B2)
            if not _B2["on"] and failover_to_b2(f"write 429 ({tag})"):
                if tag in _PENDING_TAGS and len(_PENDING) < _PENDING_CAP:
                    _PENDING.append((fn, tag))
                return None
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
        # TỐI ƯU GỐC 22/8 (thủ phạm số 1 làm B cạn 50K ĐỌC/ngày): trước đây MỖI lượt gọi là quét
        # cả bảng ~74 doc; nhân số lần làm tươi × 18 luồng × ~15 phiên là 30-40K đọc/ngày chỉ cho
        # bảng key. Giờ: đọc 1 DOC SNAPSHOT `__snap__<owner>` (sync_keys_from_a dựng lại mỗi phiên
        # plan) = 1 đọc thay vì 74. Không có snapshot (lần đầu/migrate cũ) thì mới quét bảng như xưa.
        # Snapshot nằm TRONG collection gemini_keys -> hưởng nguyên rules đã KHÓA (an toàn key).
        db = _db_keys()
        out = []; now = _now()
        rows = None
        try:
            _cr("read_keys_snap", 1)
            sd = db.collection("gemini_keys").document(f"__snap__{owner}").get()
            if sd.exists:
                rows = [(x.get("id", ""), x) for x in ((sd.to_dict() or {}).get("keys") or [])]
        except Exception:
            rows = None                                   # snapshot hỏng -> quét bảng, đừng chết
        if rows is None:
            _cr("read_keys_scan", 70)
            rows = [(d.id, d.to_dict() or {})
                    for d in db.collection("gemini_keys").where("owner", "==", owner).stream()]
        for did, x in rows:
            if did.startswith("__") or not x.get("key"):
                continue                                  # bỏ doc hệ thống (__snap__/__req__)
            cooling = x.get("cooling_until", "")
            if cooling and cooling > now and not include_cooling:
                continue                                  # đang nghỉ -> bỏ qua vòng này
            if x.get("alive") is False and not include_cooling:
                continue                                  # RENDER: bỏ key đã biết CHẾT (403/khoá) -> khỏi phí lượt.
            today = now[:10]
            req_today = int(x.get("req_today", 0) or 0) if x.get("req_date") == today else 0   # sang ngày mới -> coi như 0
            out.append({"id": did, "key": x["key"], "email": x.get("email", ""),
                        "last_checked": x.get("last_checked", ""), "alive": x.get("alive"),
                        "last_used": x.get("last_used", ""), "cooling_until": cooling,
                        "dead_since": x.get("dead_since", ""), "req_today": req_today})
        # OVERLAY sổ đếm gộp __req__ (nguồn sự thật mới của req_today; doc lẻ hết được ghi từ 22/8)
        try:
            import datetime as _ddt
            _cr("req_overlay", 1)
            rd = db.collection("gemini_keys").document(f"__req__{owner}").get()
            rx = (rd.to_dict() or {}) if rd.exists else {}
            gday = (_ddt.datetime.now(_ddt.timezone.utc) - _ddt.timedelta(hours=7)).isoformat()[:10]
            if rx.get("d") == gday:
                c = rx.get("c") or {}
                for r in out:
                    r["req_today"] = int(c.get(r["id"], 0) or 0)
        except Exception:
            pass                                          # overlay hỏng -> giữ số cũ, không chết
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
            if not _B2["on"] and failover_to_b2("read_keys 429"):   # chỉ lật+thử lại LẦN ĐẦU (chống đệ quy vô hạn)
                try:
                    return read_keys(owner, include_cooling=include_cooling)   # thử lại — giờ đọc B2
                except Exception:
                    pass
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
    _have_gsk = any(str(r.get("key", "")).startswith("gsk_") for r in rows)
    _have_cf = any(str(r.get("key", "")).startswith("cf:") for r in rows)
    if _have_gsk and _have_cf:
        return rows        # B đã đủ cả Groq lẫn CF (sync đã ăn) -> không đụng tới quota A nữa
    # 22/8 chiều: B cạn quota ĐỌC cả ngày -> sync_keys chết mọi phiên -> 20 key CF user thêm kẹt ở A.
    # Điều kiện cũ chỉ hợp nhất khi thiếu gsk_ (mà B có gsk_ rồi) -> CF vô hình. Giờ: thiếu BẤT KỲ
    # nhà nào (gsk_ / cf:) là hợp nhất từ A — 1 lượt đọc A/tiến trình, tự tắt khi sync hồi sau reset.
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
        # 22/8 tối: A nghẽn -> stream ném -> rows vẫn None -> LẦN ĐỌC KẾ THỬ LẠI -> 9 lần x 70 đếm
        # = 630 đọc A/luồng x 18 luồng, tự tay đấm A gục -> enqueue đọc danh sách kho Drive (cũng ở A)
        # trả rỗng -> 9 video EMPIREUSA QC 98 bị TỪ CHỐI đẩy kho. Lỗi thì ĐỆM RỖNG luôn: 1 phát/tiến trình.
        if _A_KEYS["rows"] is None:
            _A_KEYS["rows"] = []
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


def incr_key_requests_bulk(owner: str, counts: dict, today: str):
    """GỘP SỔ ĐẾM (22/8, user duyệt): 1 lượt GHI cho TẤT CẢ key thay vì 1 ghi/key/luồng.

    Doc `gemini_keys/__req__<owner>`: {"d": ngày-google, "c": {key_id: tổng request}} — mỗi field
    dùng Increment NGUYÊN TỬ nên 18 luồng cùng ghi không giẫm nhau. owner="__req__" để query
    where(owner==owner) của scan/sync KHÔNG quét trúng. Sang ngày mới: plan (sync_keys_from_a)
    reset; read_keys overlay số từ doc này vào rows -> key_order vẫn ưu tiên key ít dùng như cũ."""
    from google.cloud import firestore
    items = {str(k): int(v) for k, v in (counts or {}).items() if int(v or 0) > 0}
    if not items:
        return
    _cw("req_counters")
    patch = {"d": today, "owner": "__req__",
             "c": {k: firestore.Increment(v) for k, v in items.items()}}
    _soft(lambda: _db_keys().collection("gemini_keys").document(f"__req__{owner}").set(patch, merge=True),
          "req_counters")


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
        have = set(); nb = 0; snap_rows = []
        for d in db_b.collection("gemini_keys").where("owner", "==", owner).stream():
            if d.id.startswith("__snap__"):
                continue
            nb += 1
            x = d.to_dict() or {}
            if x.get("key"):
                have.add(x["key"])
                snap_rows.append({**x, "id": d.id})
        _cr("sync_keys_A", 70)
        added = 0; na = 0
        for d in db_a.collection("gemini_keys").where("owner", "==", owner).stream():
            if d.id.startswith("__snap__"):
                continue
            na += 1
            x = d.to_dict() or {}
            if not x.get("key") or x["key"] in have:
                continue
            _cw("sync_keys")
            _soft(lambda _id=d.id, _x=x: db_b.collection("gemini_keys").document(_id).set(_x, merge=True),
                  "sync_keys")
            snap_rows.append({**x, "id": d.id})   # vào snapshot NGAY cả khi lượt ghi doc lẻ bị nuốt
            added += 1
        # DỰNG SNAPSHOT 1-DOC (tối ưu gốc: read_keys 1 đọc thay vì quét 74 doc) — tái dùng chính
        # lượt quét trên, KHÔNG tốn thêm lượt đọc nào; 1 lượt ghi/phiên plan.
        _cw("keys_snapshot")
        _soft(lambda: db_b.collection("gemini_keys").document(f"__snap__{owner}").set(
            {"keys": snap_rows, "n": len(snap_rows), "updated_at": _now()}), "keys_snapshot")
        # RESET sổ đếm gộp __req__ khi sang ngày-google mới (Increment cộng dồn mù, không tự reset)
        try:
            import datetime as _ddt
            gday = (_ddt.datetime.now(_ddt.timezone.utc) - _ddt.timedelta(hours=7)).isoformat()[:10]
            _cr("req_reset", 1)
            rd = db_b.collection("gemini_keys").document(f"__req__{owner}").get()
            if rd.exists and (rd.to_dict() or {}).get("d") != gday:
                _cw("req_reset")
                _soft(lambda: db_b.collection("gemini_keys").document(f"__req__{owner}").set(
                    {"d": gday, "owner": "__req__", "c": {}}), "req_reset")
        except Exception:
            pass
        # LUÔN in số đếm — phiên 04:22Z sync im lặng nên không phân biệt được "0 key mới" với
        # "query A trả 0 dòng (owner lệch)" hay "ghi bị nuốt vì B cạn quota ghi".
        print(f"   🔑 Sync key A->B: A={na} · B={nb} · mới={added}"
              + (" (ghi qua _soft — B cạn quota ghi thì lượt ghi chờ hồi, ĐỌC đã tự hợp nhất từ A)" if added else ""))
        if added:
            _KEYS_CACHE.clear()
        return added
    except Exception as e:
        if _wq_exhausted(e) and not getattr(sync_keys_from_a, "_retried", False):
            # 429 lúc plan thường là BURST theo phút (vừa chạy loạt đếm 106 lệnh) — nghỉ 8s thử lại
            # ĐÚNG 1 lần (cờ _retried chống đệ quy vô hạn khi 429 dai dẳng): sync là đường DUY NHẤT
            # đưa key mới (Groq/CF user vừa dán) vào trận, trượt phiên này là key chờ thêm ~25'.
            sync_keys_from_a._retried = True
            try:
                import time as _t2; _t2.sleep(8)
                return sync_keys_from_a(owner)
            except Exception as e2:
                print(f"   ⚠️ sync_keys A->B lỗi cả lượt thử lại (bỏ qua): {str(e2)[:80]}")
                return 0
            finally:
                sync_keys_from_a._retried = False
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
    if minutes < 5:
        # 22/8 tối (B ghi 12K/20K lúc 14:40Z, user lo cạn trước reset): lệnh nghỉ NGẮN (per-minute
        # 1.1') chỉ cần sổ RAM _COOLED là đủ né trong tiến trình — ghi Firestore cho loại này gần
        # như vô nghĩa với luồng khác (hết nghỉ trước khi họ kịp đọc). Chỉ nghỉ DÀI (>=5', tức
        # quota ngày) mới đáng 1 lượt ghi chia sẻ liên luồng. Cắt ~60-80% lượt cool_key trong bão.
        _COOLED[key_id] = until_ts
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
    import time as _t
    _hc = _HOT_CACHE.get(("cfg", owner))
    if _hc and (_t.time() - _hc[0]) < 60:
        return dict(_hc[1])             # TTL 60s: stop/run_now trễ tối đa 1' — đổi 17 đọc/luồng còn ~3
    _cr("read_config", 1)
    if _t.time() < _RQ_DEAD["until"]:
        return dict(_CFG_LAST.get(owner) or {})   # quota đọc chết -> bản đệm/mặc định, không crash
    def _do():
        d = _db_meta().collection("render_config").document(owner).get()
        return (d.to_dict() or {}) if d.exists else {}
    try:
        out = _retry(_do)
        _CFG_LAST[owner] = out
        _HOT_CACHE[("cfg", owner)] = (_t.time(), out)
        return out
    except Exception as e:
        if _wq_exhausted(e):
            if not _B2["on"] and failover_to_b2("read_config 429"):
                try:
                    return read_config(owner)          # thử lại — giờ đọc B2 (đã gương config)
                except Exception:
                    pass
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
    # GHI SONG SONG SANG B2 (23/8, user: "phải khớp, không được trùng phải render lại") — ngân hàng
    # chủ đề là dữ liệu DUY NHẤT mà trễ 1 phiên gây hậu quả THẬT (viết trùng đề tài -> video bỏ đi).
    # Vì vậy nó KHÔNG đi theo nhịp gương mà ghi ngay tại chỗ: mỗi video chỉ tốn thêm 1 lượt ghi ở
    # B2 (kho riêng, không đụng quota B) -> lật sang B2 lúc nào cũng có bản mới nhất, hết trùng.
    if not _B2["on"] and _b2_available():
        try:
            from google.cloud import firestore as _fs2
            from google.oauth2 import service_account as _sa2
            if _B2.get("wclient") is None:
                _B2["wclient"] = _fs2.Client(
                    project=os.environ["FIREBASE_PROJECT_ID_B2"],
                    credentials=_sa2.Credentials.from_service_account_file(
                        os.environ["GOOGLE_APPLICATION_CREDENTIALS_B"]))
            _B2["wclient"].collection("render_topics").document(f"{owner}__{channel}").set(
                {"owner": owner, "channel": channel, "topics": cur}, merge=True)
        except Exception as e:
            print(f"   ⚠️ ghi chủ đề sang B2 lỗi ({str(e)[:50]}) — gương phiên sau bù.")


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
    # 23/8 TỐI — CẦU DAO CHỐNG TREO PHIÊN: phiên 15:38Z đứng 42 PHÚT ở bước điều phối. Nguyên nhân:
    # quota đọc cạn -> mỗi lệnh đếm chờ hết 60s timeout, rồi _retry thử lại 5 lần (thêm ~15s), nhân
    # với ~110 lệnh đếm cho 55 kênh = hàng giờ. Phiên treo còn kéo theo hậu quả dây chuyền: khoá
    # concurrency của GitHub huỷ luôn các phiên xếp sau (15:54 và 16:14 đều bị huỷ) -> dây chuyền
    # đứng hẳn. Nay: hễ biết đường đọc đã chết thì trả 0 NGAY, không trả giá 60s cho từng kênh.
    import time as _t
    if _t.time() < _RQ_DEAD["until"]:
        return 0
    q = (db.collection("render_jobs").where("owner", "==", owner)
         .where("channel", "==", channel).where("status", "==", "done"))
    if vtype:
        q = q.where("type", "==", vtype)
    try:
        # _retry: 429 ở đây đa số là BURST THEO PHÚT (plan bắn ~106 lệnh đếm liền tay cho 53 kênh,
        # 10:17Z 22/8), không phải cạn ngày — backoff 1.5-7.5s là qua. Không retry thì count trả 0
        # -> _ratio_plan tưởng kênh 0 long 0 short -> ép long sai + target đếm thiếu (làm DƯ video).
        def _agg():
            res = q.count().get(timeout=12)      # aggregation: ~1 read thay vì N (timeout ngắn: chết thì chết NHANH)
            row = res[0]; ar = row[0] if isinstance(row, (list, tuple)) else row
            return int(ar.value)
        return _retry(_agg)
    except Exception as e:
        # ĐỪNG lùi về đếm thủ công cả collection: khi quota cạn thì count() lỗi -> stream() đọc HÀNG
        # NGHÌN doc -> càng cạn nhanh hơn (vòng xoáy chết, đúng sự cố 20/8). Đếm có giới hạn: đủ để
        # biết "đã đạt target chưa" vì target lớn nhất chỉ 30.
        if _wq_exhausted(e):
            # Cạn hạn mức NGÀY (không phải burst): đóng cầu dao 15 phút cho CẢ tiến trình, đừng thử
            # lại kiểu nào nữa — mọi lệnh đọc sau đều sẽ chết y hệt, chỉ tốn thời gian.
            if not _B2["on"] and failover_to_b2(f"count_done 429 ({channel})"):
                try:
                    return _count_jobs(_db_jobs(), owner, channel, vtype)
                except Exception:
                    pass
            _RQ_DEAD["until"] = _t.time() + 15 * 60
            if not _RQ_DEAD["warned"]:
                _RQ_DEAD["warned"] = True
                print("   🔌 CẦU DAO: quota đọc cạn -> ngừng đếm 15', coi mọi kênh = 0 (phiên sau đếm lại)")
            return 0
        try:
            return sum(1 for _ in q.limit(200).stream(timeout=12))
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


def update_channel_stats(owner: str, channel: str):
    """SỔ THỐNG KÊ 1-DOC `render_stats/{owner}`: {kênh: {l: long, s: short}} — pipeline ghi cuối mỗi
    luồng (1 lượt ghi mềm, số lấy từ count_done ĐÃ ĐỆM nên ~0 lượt đọc thêm). Dashboard chỉ đọc đúng
    1 doc là có số THẬT của mọi kênh — hết cảnh 22/8 mỗi ô một nguồn ("1058 tổng · 74 đã tải ·
    kênh 7/9/11" đếm từ danh sách cắt) làm user rối."""
    try:
        L = count_done(owner, channel, "long")
        S = count_done(owner, channel, "short")
        _cw("channel_stats")
        _soft(lambda: _db_meta().collection("render_stats").document(owner).set(
            {channel: {"l": int(L), "s": int(S)}, "up": _now()}, merge=True), "channel_stats")
    except Exception:
        pass


def count_done(owner: str, channel: str, vtype: str = None) -> int:
    """Đếm số video ĐÃ XONG của 1 kênh (so target). Đếm CẢ Project B (job mới) + A (job CŨ trước shard) -> không sót, không làm THỪA.
    Dùng aggregation count() = ~1 read/project. TTL 90s: một mẻ video kéo dài >5' nên mỗi vòng vẫn
    số tươi; các lần gọi lặp TRONG vòng (gate/target/ratio ~4 lần) dùng đệm — 16 đọc/luồng còn ~4."""
    import time as _t
    _hc = _HOT_CACHE.get(("cnt", owner, channel, vtype))
    if _hc and (_t.time() - _hc[0]) < 90:
        return _hc[1]
    _cr("count_done", 1)
    total = 0
    if _B2["on"]:
        # 23/8: B2 KHÔNG chép lịch sử job (cố ý — nặng, ít giá trị). Nếu vẫn đếm job trên B2 thì
        # thấy ~0 -> tưởng kênh chưa làm gì -> LÀM DƯ so với chỉ tiêu. Lấy số từ SỔ THỐNG KÊ
        # render_stats/{owner} (1 doc, đã gương sang B2) — đúng con số kênh đã có tới phiên trước.
        try:
            d = _B2["client"].collection("render_stats").document(owner).get()
            ch = ((d.to_dict() or {}).get(str(channel).upper()) or {}) if d.exists else {}
            base = int(ch.get("l", 0) or 0) + int(ch.get("s", 0) or 0) if not vtype else \
                   int(ch.get("l" if vtype == "long" else "s", 0) or 0)
            live = _count_jobs(_db_jobs(), owner, channel, vtype)        # video làm TRONG phiên khẩn
            total = base + live
            _HOT_CACHE[("cnt", owner, channel, vtype)] = (_t.time(), total)
            return total
        except Exception as e:
            print(f"   ⚠️ count_done B2 dùng sổ thống kê lỗi ({str(e)[:50]}) — đếm thô.")
    try:
        total += _count_jobs(_db_jobs(), owner, channel, vtype)          # B (hoặc A nếu chưa shard)
    except Exception as e:
        # 23/8: phiên 13:29Z in 108 dòng "đếm ... 429" mà KHÔNG lật B2 — vì lỗi bị nuốt ngay tại
        # đây. Hậu quả: cả phiên chạy trên B đã cạn đọc (đếm = 0 -> lập kế hoạch sai, và mọi lượt
        # đọc sau đó đều hụt). 429 ở đây là bằng chứng B chết -> phải lật sang B2 ngay lần đầu.
        if _wq_exhausted(e) and not _B2["on"] and failover_to_b2(f"count_done 429 ({channel})"):
            try:
                total += _count_jobs(_db_jobs(), owner, channel, vtype)
            except Exception:
                pass
        else:
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
    _HOT_CACHE[("cnt", owner, channel, vtype)] = (_t.time(), total)
    return total


def mirror_b_to_b2(owner: str) -> int:
    """GƯƠNG DỮ LIỆU SỐNG CÒN B->B2 (23/8): kênh + config + snapshot key + gương kho — đủ để failover
    sang B2 là plan/lane chạy được ngay (job history KHÔNG gương: sống thiếu nó được, đếm lại dần).
    1 lần/phiên khi B khỏe; so giá trị, chỉ ghi doc đổi (B2 quota riêng, gần như không tốn của B)."""
    if _B2["on"] or not _b2_available():
        return 0
    try:
        from google.cloud import firestore as _fs
        from google.oauth2 import service_account as _sa
        creds = _sa.Credentials.from_service_account_file(os.environ["GOOGLE_APPLICATION_CREDENTIALS_B"])
        b2 = _fs.Client(project=os.environ["FIREBASE_PROJECT_ID_B2"], credentials=creds)
        n = 0
        # 0) DRAIN NGƯỢC: job sinh ra trong lúc chạy tạm B2 (phiên khẩn) -> rót về B rồi xoá ở B2,
        #    để kho/số đếm ở B đủ video, B2 sạch sẽ chờ lần khẩn sau. (Kênh/config KHÔNG cần chiều
        #    ngược — nguồn chuẩn của chúng luôn là B, B2 chỉ là bản sao.)
        drained = 0
        for d in b2.collection("render_jobs").where("owner", "==", owner).limit(300).stream():
            x = d.to_dict() or {}
            _db_jobs().collection("render_jobs").document(d.id).set(x, merge=True)
            d.reference.delete(); drained += 1
        if drained:
            print(f"   🔁 Rót ngược {drained} job từ B2 về B (video phiên khẩn không bị thất lạc).")
        # 0b) rót ngược ngân hàng chủ đề (đề tài viết trong phiên khẩn) — B2 giữ superset nên set thẳng
        for d in b2.collection("render_topics").stream():
            if not d.id.startswith(f"{owner}__"):
                continue
            x2 = d.to_dict() or {}
            t = _db_meta().collection("render_topics").document(d.id)
            cur = (t.get().to_dict() or {})
            # GỘP chứ KHÔNG ĐÈ (23/8): trong lúc B chết, B2 nhận đề tài mới; nhưng B cũng có đề tài
            # cũ mà B2 chưa kịp có. Đè một chiều = MẤT một nửa ngân hàng chống trùng -> vài ngày sau
            # AI viết lại đúng đề tài cũ. Gộp theo thứ tự, bỏ trùng, giữ 300 mục gần nhất.
            merged, seen = [], set()
            for t0 in list(cur.get("topics") or []) + list(x2.get("topics") or []):
                if t0 and t0 not in seen:
                    seen.add(t0); merged.append(t0)
            if merged != (cur.get("topics") or []):
                t.set({"owner": owner, "channel": x2.get("channel") or cur.get("channel"),
                       "topics": merged[-300:]}, merge=True)
        # 1) render_channels (toàn bộ của owner)
        cur = {d.id: (d.to_dict() or {}) for d in b2.collection("render_channels").where("owner", "==", owner).stream()}
        for d in _db_meta().collection("render_channels").where("owner", "==", owner).stream():
            x = d.to_dict() or {}
            if cur.get(d.id) != x:
                b2.collection("render_channels").document(d.id).set(x); n += 1
        # 1b) render_topics — NGÂN HÀNG CHỦ ĐỀ ĐÃ LÀM (23/8, user chỉ ra): thiếu nó thì phiên khẩn
        #     trên B2 tưởng "chưa làm gì" -> viết lại đề tài cũ = video trùng nội dung. Gương bắt buộc.
        curt = {d.id: (d.to_dict() or {}) for d in b2.collection("render_topics").stream()}
        for d in _db_meta().collection("render_topics").stream():
            if d.id.startswith(f"{owner}__"):
                x = d.to_dict() or {}
                if curt.get(d.id) != x:
                    b2.collection("render_topics").document(d.id).set(x); n += 1
        # 2) render_config + snapshot keys + __req__ + connections_mirror (mỗi thứ 1-2 doc)
        for col, docid in (("render_config", owner), ("gemini_keys", f"__snap__{owner}"),
                           ("gemini_keys", f"__req__{owner}"), ("render_stats", owner)):
            try:
                s = _db_meta().collection(col).document(docid).get() if col == "render_config" else \
                    _db_keys().collection(col).document(docid).get()
                if s.exists:
                    x = s.to_dict() or {}
                    t = b2.collection(col).document(docid)
                    if (t.get().to_dict() or {}) != x:
                        t.set(x); n += 1
            except Exception:
                pass
        try:
            for d in _db_jobs().collection("connections_mirror").stream():
                x = d.to_dict() or {}
                t = b2.collection("connections_mirror").document(d.id)
                if (t.get().to_dict() or {}) != x:
                    t.set(x); n += 1
        except Exception:
            pass
        b2.collection("render_config").document("mirror_meta").set({"at": _now()})   # dấu tuổi gương
        # sổ quota phải đếm ĐỦ chi phí của chính gương: ~60 kênh + ~60 topics + 4 doc lẻ đọc từ B
        _cr("mirror_b2", 124)
        if n:
            print(f"   🪞 Gương B→B2: cập nhật {n} doc (B2 sẵn sàng nhận failover).")
        return n
    except Exception as e:
        print(f"   ⚠️ mirror B→B2 lỗi ({str(e)[:60]}) — phiên sau thử lại.")
        return 0


def mirror_connections_to_b() -> int:
    """GƯƠNG KHO DRIVE A->B (23/8): A cạn quota đọc cả chiều -> enqueue đọc danh sách kho (ở A) trả
    rỗng -> video render xong bị TỪ CHỐI hàng loạt dù B vẫn sống. Chép connections (đủ refresh_token
    + root) sang B collection `connections_mirror` — rules B khóa kín (catch-all deny, chỉ service
    account bypass được) nên token KHÔNG lộ ra client. Publisher fallback đọc gương khi A nghẽn ->
    A hết là điểm-chết-đơn của khâu đẩy kho. Chạy 1 lần/phiên ở plan; so giá trị, chỉ ghi doc đổi."""
    try:
        if _db() is _db_jobs():
            return 0
        rows = {}
        # 23/8 tối: thêm timeout cho lượt quét A. Không có nó, hôm A cạn quota thì riêng lệnh này đã
        # ngốn 60s+ ngay đầu phiên trước khi cầu dao kịp biết đường đọc đã chết.
        for d in _db().collection("connections").stream(timeout=20):
            x = d.to_dict() or {}
            if x.get("refresh_token") and x.get("root"):
                rows[d.id] = x
        _cr("mirror_conn_A", max(1, len(rows)))
        if not rows:
            return 0
        col = _db_jobs().collection("connections_mirror")
        cur = {d.id: (d.to_dict() or {}) for d in col.stream(timeout=20)}
        _cr("mirror_conn_B", max(1, len(cur)))
        n = 0
        keys = ("refresh_token", "root", "client_id", "client_secret", "channel", "owner", "email", "cap_gb")
        for i, x in rows.items():
            if any(cur.get(i, {}).get(k) != x.get(k) for k in keys):
                _soft(lambda ref=col.document(i), v=x: ref.set(v), "mirror_conn")
                n += 1
        for i in set(cur) - set(rows):
            _soft(lambda ref=col.document(i): ref.delete(), "mirror_conn_del")
        # SNAPSHOT 1-DOC (23/8 — GỐC của 125K đọc/ngày trên A): publisher đọc danh sách kho bằng
        # cách quét CẢ COLLECTION 70 doc, đệm chỉ 10' -> mỗi lane 110' làm mới ~11 lần = 770 đọc,
        # ×18 lane = ~14.000 đọc/phiên chỉ để lấy một danh sách gần như bất biến. Gói cả danh sách
        # vào 1 doc -> publisher đọc 1 lượt thay vì 70. (Cùng chiêu đã dùng cho 142 key AI.)
        _snap = [{"id": i, **{k: v for k, v in x.items() if k in keys}} for i, x in rows.items()]
        _soft(lambda: col.document("__snap__").set({"at": _now(), "n": len(_snap), "accs": _snap}),
              "mirror_conn_snap")
        if n:
            print(f"   🪞 Gương kho Drive A→B: cập nhật {n}/{len(rows)} tài khoản + snapshot 1-doc.")
        return n
    except Exception as e:
        print(f"   ⚠️ mirror_connections lỗi ({str(e)[:60]}) — A nghẽn thì phiên sau tự thử lại.")
        return 0


def heal_unpushed(owner: str, hours: int = 48, cap: int = 120) -> int:
    """TỰ CHỮA video 'mồ côi' (22/8): Firestore A nghẽn 1 nhịp -> enqueue tưởng '0 kho Drive' ->
    9 video EMPIREUSA QC 98 render xong bị TỪ CHỐI đẩy, job ghi done «Xong (chưa đẩy Drive)» rồi
    runner chết -> file mất, chỉ còn KỊCH BẢN trong job. Hàm này chạy 1 lần/phiên (plan_mode):
    tìm job done + drive_id RỖNG + có script trong N giờ gần đây -> lật về 'failed' để
    find_resumable của kênh đó tự nhặt, render lại TỪ SCRIPT (0 quota AI) + đẩy kho tử tế.
    Rẻ: dùng index (owner,status,created_at) đã deploy; chỉ ghi khi thật sự có nạn nhân.
    CỬA SỔ 30h (23/8): quota Firestore reset THEO NGÀY nên sự cố cạn quota luôn kéo dài xuyên đêm —
    cửa sổ 8h ban đầu quét trượt sạch nạn nhân của chính sự cố mà nó sinh ra để chữa (phiên 07:06Z
    báo "quét 0 job" trong khi 9 video EMPIREUSA nằm ở mốc 14-17h trước đó)."""
    try:
        # 23/8: CHỈ chữa khi có ĐƯỜNG ĐẨY KHO — A sống HOẶC gương B có dữ liệu. A chết + gương rỗng
        # mà vẫn lật failed thì lane render lại xong LẠI bị từ chối -> vòng lặp đốt máy vô ích cả đêm.
        _path_ok = False
        try:
            next(_db().collection("connections").limit(1).stream(), None)
            _path_ok = True
        except Exception:
            try:
                _path_ok = next(_db_jobs().collection("connections_mirror").limit(1).stream(), None) is not None
            except Exception:
                pass
        if not _path_ok:
            print("   🩹 heal HOÃN: A nghẽn đọc + gương B chưa có -> đẩy kho chắc chắn từ chối."
                  " Video giữ script + artifact 3 ngày, tự chữa khi có đường.")
            return 0
        from datetime import timedelta
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        _cr("heal_unpushed", 20)
        q = (_db_jobs().collection("render_jobs").where("owner", "==", owner)
             .where("status", "==", "done").where("created_at", ">=", since).limit(400))
        healed = scanned = orphan = 0
        for d in q.stream():
            j = d.to_dict() or {}
            scanned += 1
            _is_orphan = (j.get("drive_id") or "") == "" and bool(j.get("script"))
            if _is_orphan:
                orphan += 1
            if healed >= cap:
                continue          # vẫn đếm tiếp để biết CÒN BAO NHIÊU (trước đây break -> mù số dư)
            if _is_orphan:
                _soft(lambda ref=d.reference: ref.set(
                    {"status": "failed", "note": "tự chữa: xong nhưng chưa đẩy được kho -> render lại từ script"},
                    merge=True), "heal_unpushed")
                healed += 1
        # LUÔN in 1 dòng (kể cả 0) + SỐ CÒN LẠI (23/8): 180 video mồ côi > sức chữa 1 phiên, phải
        # biết còn bao nhiêu để chắc chắn KHÔNG BỎ SÓT trước khi hết cửa sổ 48h.
        print(f"   🩹 heal_unpushed: quét {scanned} job done/{hours}h, chữa {healed} video chưa-đẩy-kho"
              + (f", CÒN LẠI ~{max(0, orphan - healed)} chờ phiên sau." if orphan > healed else "."))
        return healed
    except Exception as e:
        print(f"   ⚠️ heal_unpushed lỗi ({str(e)[:70]}) — bỏ qua, không chặn phiên.")
        return 0


def find_resumable(owner: str, channel: str, vtype: str):
    """CHECKPOINT: job THẤT BẠI gần nhất của kênh này còn giữ kịch bản (script, ghi lúc 'rendering' —
    TRƯỚC bước render tốn thời gian nhất) -> dùng lại thay vì gọi Gemini viết mới, đỡ tốn quota + tránh
    lệch nội dung/chủ đề đã ghi vào ngân hàng. CHỈ lấy job status='failed' (đã CHẮC CHẮN không ai còn xử
    lý — do lỗi thật hoặc Health Guardian tự đánh dấu job treo) -> an toàn, không đụng job đang chạy thật.
    Trả {'job_id', 'story'} hoặc None (không có gì để resume -> viết mới bình thường như cũ)."""
    ck = ("rz", owner, channel, vtype)
    if ck in _HOT_CACHE:
        lst = _HOT_CACHE[ck]
        return lst.pop(0) if lst else None   # đã nạp 1 lần -> phát dần, hết thì thôi (phần còn lại phiên sau)
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
            _HOT_CACHE[ck] = []
            return None
        cands.sort(key=lambda x: x[1].get("created_at", ""), reverse=True)   # ưu tiên bản GẦN NHẤT
        lst = []
        for job_id, job in cands:
            try:
                story = json.loads(job["script"])
                if story:
                    lst.append({"job_id": job_id, "story": story})
            except Exception:
                continue
        _HOT_CACHE[ck] = lst
        return lst.pop(0) if lst else None
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
        # 22/8: 5' -> 10' (user duyệt): mốc trung gian chỉ để dashboard nhìn; nhịp tim nền 15'
        # vẫn chứng minh "còn sống" (guardian coi chết sau 45' im lặng), video không ảnh hưởng.
        if now - _LAST_JOB_WRITE.get(job_id, 0) < 720:
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
BEAT_SEC = 1200   # 15' — health_guardian coi job chết sau STALE_BEAT_MIN=45' im lặng, tức vẫn còn 3
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

# ── BẾN PHỤ R2: sổ video đang đậu tạm (23/8) — HIỆN ĐANG NGỦ ────────────────────────────────
# 23/8 chiều: user chốt BỎ R2 ("hơi rối, tránh xung đột lỗi") -> KHÔNG chỗ nào gọi 3 hàm dưới nữa.
# Giữ lại nguyên vẹn để bật lại trong 1 phút nếu cần; chúng không tự chạy, không tốn quota.
# Video đẩy Drive hụt -> gửi lên R2 -> ghi 1 doc ở đây. Phiên sau `repush_r2()` tải về và đẩy vào
# Drive rồi xoá doc + xoá file R2. Nhờ vậy hụt quota/hụt kho KHÔNG còn làm mất công render.

def add_r2_pending(owner: str, meta: dict) -> None:
    _soft(lambda: _db_jobs().collection("r2_pending").document(str(meta.get("key"))[:400].replace("/", "__"))
          .set({**meta, "owner": owner, "at": _now()}), "add_r2_pending")


def list_r2_pending(owner: str, cap: int = 40) -> list[dict]:
    try:
        q = _db_jobs().collection("r2_pending").where("owner", "==", owner).limit(cap)
        return [{**(d.to_dict() or {}), "_doc": d.id} for d in q.stream()]
    except Exception as e:
        print(f"   ⚠️ đọc sổ R2 lỗi ({str(e)[:60]})")
        return []


def clear_r2_pending(doc_id: str) -> None:
    _soft(lambda: _db_jobs().collection("r2_pending").document(doc_id).delete(), "clear_r2_pending")


# ── SỔ ẢNH ĐÃ DÙNG THEO KÊNH (23/8) — chống trùng footage xuyên luồng & xuyên phiên ──────────
# 1 doc/kênh, giữ N id gần nhất. Đọc 1 lượt đầu video, ghi 1 lượt cuối video -> ~110 lượt/phiên cho
# 55 kênh, rẻ hơn nhiều so với cái giá phải trả: video các kênh dùng lại cùng một tấm ảnh.

def read_used_images(owner: str, channel: str) -> list:
    try:
        d = _db_jobs().collection("img_used").document(f"{owner}__{channel}").get()
        return ((d.to_dict() or {}).get("ids") or []) if d.exists else []
    except Exception:
        return []


def append_used_images(owner: str, channel: str, ids: list, cap: int = 600) -> None:
    if not ids:
        return
    def _w():
        ref = _db_jobs().collection("img_used").document(f"{owner}__{channel}")
        cur = []
        try:
            d = ref.get()
            cur = ((d.to_dict() or {}).get("ids") or []) if d.exists else []
        except Exception:
            pass
        merged = (cur + [str(i) for i in ids])[-cap:]
        ref.set({"ids": merged, "n": len(merged), "at": _now()})
    _soft(_w, "append_used_images")


# ── SỔ MẠCH KÊNH (23/8): dấu vân từ khoá + đếm trụ nội dung, 1 doc/kênh ─────────────────────
# Thay cho render_topics (chỉ nhớ 80 chuỗi): doc này nhớ tới 4000 BỘ TỪ KHOÁ nên còn tác dụng khi
# kênh đã có hàng nghìn video, mà vẫn chỉ tốn 1 lượt đọc + 1 lượt ghi mỗi lane.
_FP_CACHE = {}


def read_channel_memory(owner: str, channel: str) -> dict:
    ck = (owner, channel)
    if ck in _FP_CACHE:
        return _FP_CACHE[ck]
    out = {"fps": [], "pillars": {}}
    try:
        d = _db_jobs().collection("channel_memory").document(f"{owner}__{channel}").get()
        if d.exists:
            x = d.to_dict() or {}
            out = {"fps": [list(f) for f in (x.get("fps") or [])], "pillars": dict(x.get("pillars") or {})}
    except Exception as e:
        print(f"   ⚠️ đọc mạch kênh hụt ({str(e)[:50]}) — coi như kênh mới")
    _FP_CACHE[ck] = out
    return out


def append_channel_memory(owner: str, channel: str, fp: list, pillar: str = "", cap: int = 4000) -> None:
    """Ghi thêm 1 bài vào mạch kênh. Cập nhật luôn bộ nhớ tiến trình để video kế tiếp thấy ngay."""
    if not fp:
        return
    mem = read_channel_memory(owner, channel)
    mem["fps"] = (mem["fps"] + [list(fp)])[-cap:]
    if pillar:
        mem["pillars"][pillar] = int(mem["pillars"].get(pillar, 0)) + 1
    _FP_CACHE[(owner, channel)] = mem
    _soft(lambda: _db_jobs().collection("channel_memory").document(f"{owner}__{channel}")
          .set({"fps": mem["fps"], "pillars": mem["pillars"], "n": len(mem["fps"]), "at": _now()}),
          "channel_memory")
