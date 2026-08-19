"""
firestore_bridge.py — Cầu nối render pipeline <-> Firestore (dùng CHUNG service account
với AutoPublisher: biến GOOGLE_APPLICATION_CREDENTIALS + FIREBASE_PROJECT_ID).

- Đọc: gemini_keys (key+Gmail), render_channels (kênh cần render), render_config (bật/tắt, qc_min, model).
- Ghi: render_jobs (trạng thái realtime -> tab 🎬 Render Studio hiển thị live).

Chạy trên GitHub Actions: workflow ghi secret GCP_SA_KEY ra /tmp/sa.json rồi set 2 biến trên.
"""
from __future__ import annotations
import os
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


def _db_meta():
    """Client cho META render (config·channels·gemini_keys·storage·topics·requests).
    Bật cờ SHARD_META=1 (khi đã migrate sang Project B) -> đọc/ghi meta trên B (render CHỈ đụng B, cách ly A).
    Chưa bật (mặc định) -> A như cũ (backward-compatible)."""
    if os.environ.get("SHARD_META") == "1":
        return _db_jobs()          # B (đã cấu hình creds B); _db_jobs tự fallback A nếu thiếu creds
    return _db()


def _now():
    return datetime.now(timezone.utc).isoformat()


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


def read_keys(owner: str, include_cooling: bool = False) -> list[dict]:
    """Trả key CÒN DÙNG được (bỏ qua key đang cooldown do vừa bị rate-limit)."""
    def _do():
        db = _db(); out = []; now = _now()
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
    return _retry(_do)


def incr_key_requests(key_id: str, n: int, today: str):
    """Cộng dồn số REQUEST hôm nay của 1 key (reset khi sang ngày mới) -> tính quota còn free trước ngưỡng."""
    ref = _db().collection("gemini_keys").document(key_id)
    d = ref.get()
    x = (d.to_dict() or {}) if d.exists else {}
    if x.get("req_date") == today:
        ref.set({"req_today": int(x.get("req_today", 0) or 0) + int(n)}, merge=True)
    else:
        ref.set({"req_today": int(n), "req_date": today}, merge=True)


def mark_key_alive(key_id: str, alive: bool, reason: str = "", used: bool = False, kind: str = ""):
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
        cur = _db().collection("gemini_keys").document(key_id).get()
        if not (cur.exists and (cur.to_dict() or {}).get("dead_since")):
            patch["dead_since"] = _now()               # stamp mốc chết LẦN ĐẦU (giữ nguyên nếu đã chết từ trước)
    _db().collection("gemini_keys").document(key_id).set(patch, merge=True)


def cool_key(key_id: str, minutes: int = 90):
    """Đánh dấu key nghỉ N phút sau khi bị 429/quota (chống hammer -> chống die)."""
    from datetime import timedelta
    until = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()
    _db().collection("gemini_keys").document(key_id).set({"cooling_until": until}, merge=True)


def update_storage_used(owner: str, name: str, used: int, cap_gb=None):
    """Ghi dung lượng THẬT của 1 kho vào storage_accounts.used (render upload KHÔNG tự cập nhật số này ->
    phải sync để display + guard-kho-đầy chính xác). Doc id khớp Worker: {owner}__{name}."""
    patch = {"used": int(used or 0), "used_synced_at": _now()}
    if cap_gb:
        patch["cap_gb"] = cap_gb
    _db_meta().collection("storage_accounts").document(f"{owner}__{name}").set(patch, merge=True)


def drive_usage(owner: str):
    """Tổng dung lượng ĐÃ DÙNG / SỨC CHỨA của mọi kho Drive (bytes) -> guard 'kho gần đầy' trước khi render."""
    used = cap = 0
    try:
        for d in _db_meta().collection("storage_accounts").where("owner", "==", owner).stream():
            x = d.to_dict() or {}
            used += (x.get("used", 0) or 0)
            cap += (x.get("cap_gb", 15) or 15) * 1_000_000_000
    except Exception as e:
        print(f"   ⚠️ drive_usage lỗi ({e})")
    return used, cap


def read_channels(owner: str) -> list[dict]:
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
    def _do():
        d = _db_meta().collection("render_config").document(owner).get()
        return (d.to_dict() or {}) if d.exists else {}
    return _retry(_do)


def read_render_requests(owner: str) -> list[dict]:
    """Yêu cầu RENDER LẠI (từ nút 🔄 trên dashboard) đang chờ xử lý."""
    db = _db_meta(); out = []
    for d in db.collection("render_requests").where("owner", "==", owner).where("status", "==", "pending").stream():
        x = d.to_dict() or {}; x["id"] = d.id; out.append(x)
    return out


def delete_jobs_by_drive(owner: str, drive_id: str):
    """Xóa bản ghi job cũ theo drive_id (sau khi render lại đã thay thế + bỏ file cũ)."""
    if not drive_id:
        return
    for d in (_db_jobs().collection("render_jobs").where("owner", "==", owner).where("drive_id", "==", drive_id).stream()):
        try:
            d.reference.delete()
        except Exception:
            pass


def mark_request_status(req_id: str, status: str):
    """processing = đã bắt đầu render lại -> dashboard KHÓA nút hủy."""
    _db_meta().collection("render_requests").document(req_id).set({"status": status, "started_at": _now()}, merge=True)


def mark_request_done(req_id: str, note: str = "done"):
    _db_meta().collection("render_requests").document(req_id).set({"status": "done", "note": note, "done_at": _now()}, merge=True)


def set_config(owner: str, patch: dict):
    """Ghi/merge render_config (vd xoá cờ run_now sau khi đã nhận lệnh)."""
    _retry(lambda: _db_meta().collection("render_config").document(owner).set(patch, merge=True))


def recent_topics(owner: str, channel: str, n: int = 80) -> list[str]:
    """Chủ đề ĐÃ dùng cho kênh -> đưa cho Gemini để TRÁNH trùng (chống 'reused content')."""
    d = _db_meta().collection("render_topics").document(f"{owner}__{channel}").get()
    return (((d.to_dict() or {}).get("topics") or [])[-n:]) if d.exists else []


def save_topics(owner: str, channel: str, topics: list[str]):
    """Lưu chủ đề vừa dùng (cap 300 gần nhất)."""
    ref = _db_meta().collection("render_topics").document(f"{owner}__{channel}")
    d = ref.get()
    cur = (((d.to_dict() or {}).get("topics") or [])) if d.exists else []
    cur = (cur + [t for t in topics if t])[-300:]
    ref.set({"owner": owner, "channel": channel, "topics": cur}, merge=True)


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
    except Exception:
        return sum(1 for _ in q.stream())


def count_done(owner: str, channel: str, vtype: str = None) -> int:
    """Đếm số video ĐÃ XONG của 1 kênh (so target). Đếm CẢ Project B (job mới) + A (job CŨ trước shard) -> không sót, không làm THỪA.
    Dùng aggregation count() = ~1 read/project."""
    total = 0
    try:
        total += _count_jobs(_db_jobs(), owner, channel, vtype)          # B (hoặc A nếu chưa shard)
    except Exception as e:
        print(f"   ⚠️ count_done B lỗi ({e})")
    if _shard_on():                                                       # có shard -> cộng thêm job cũ còn ở A
        try:
            total += _count_jobs(_db(), owner, channel, vtype)
        except Exception as e:
            print(f"   ⚠️ count_done A lỗi ({e})")
    return total


def new_job(owner: str, channel: str, vtype: str = "short", pver: str = "") -> str:
    db = _db_jobs(); ref = db.collection("render_jobs").document()
    ref.set({"owner": owner, "channel": channel, "type": vtype, "pver": pver,   # pver = phiên bản pipeline -> dọn thông minh (chỉ xóa bản CŨ)
             "status": "queued", "step": "bắt đầu", "created_at": _now()})
    return ref.id


_LAST_JOB_WRITE = {}


def update_job(job_id: str, **patch):
    # TIẾT KIỆM Firestore write (100% FREE, dưới trần 20K ghi/ngày):
    #   - status CUỐI (done/failed/ratelimited): LUÔN ghi.
    #   - status trung gian: CHỈ ghi 1 lần/~90s/job (heartbeat thưa cho dashboard biết còn sống); còn lại BỎ.
    import time as _t
    st = patch.get("status")
    if st not in ("done", "failed", "ratelimited"):
        now = _t.time()
        if now - _LAST_JOB_WRITE.get(job_id, 0) < 90:
            return
        _LAST_JOB_WRITE[job_id] = now
    _retry(lambda: _db_jobs().collection("render_jobs").document(job_id).set(patch, merge=True))
