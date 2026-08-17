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


def _now():
    return datetime.now(timezone.utc).isoformat()


def read_keys(owner: str, include_cooling: bool = False) -> list[dict]:
    """Trả key CÒN DÙNG được (bỏ qua key đang cooldown do vừa bị rate-limit)."""
    db = _db(); out = []; now = _now()
    for d in db.collection("gemini_keys").where("owner", "==", owner).stream():
        x = d.to_dict() or {}
        if not x.get("key"):
            continue
        cooling = x.get("cooling_until", "")
        if cooling and cooling > now and not include_cooling:
            continue                                  # đang nghỉ -> bỏ qua vòng này
        out.append({"id": d.id, "key": x["key"], "email": x.get("email", ""),
                    "last_checked": x.get("last_checked", ""), "alive": x.get("alive")})
    return out


def mark_key_alive(key_id: str, alive: bool, reason: str = ""):
    """Ghi trạng thái sống/chết + LÝ DO + thời điểm check -> dashboard hiện 🟢/🔴 + tooltip vì sao."""
    _db().collection("gemini_keys").document(key_id).set(
        {"alive": alive, "dead_reason": ("" if alive else reason), "last_checked": _now()}, merge=True)


def cool_key(key_id: str, minutes: int = 90):
    """Đánh dấu key nghỉ N phút sau khi bị 429/quota (chống hammer -> chống die)."""
    from datetime import timedelta
    until = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()
    _db().collection("gemini_keys").document(key_id).set({"cooling_until": until}, merge=True)


def read_channels(owner: str) -> list[dict]:
    db = _db(); out = []
    for d in db.collection("render_channels").where("owner", "==", owner).stream():
        x = d.to_dict() or {}; x["id"] = d.id; out.append(x)
    return out


def read_config(owner: str) -> dict:
    d = _db().collection("render_config").document(owner).get()
    return (d.to_dict() or {}) if d.exists else {}


def read_render_requests(owner: str) -> list[dict]:
    """Yêu cầu RENDER LẠI (từ nút 🔄 trên dashboard) đang chờ xử lý."""
    db = _db(); out = []
    for d in db.collection("render_requests").where("owner", "==", owner).where("status", "==", "pending").stream():
        x = d.to_dict() or {}; x["id"] = d.id; out.append(x)
    return out


def delete_jobs_by_drive(owner: str, drive_id: str):
    """Xóa bản ghi job cũ theo drive_id (sau khi render lại đã thay thế + bỏ file cũ)."""
    if not drive_id:
        return
    for d in (_db().collection("render_jobs").where("owner", "==", owner).where("drive_id", "==", drive_id).stream()):
        try:
            d.reference.delete()
        except Exception:
            pass


def mark_request_status(req_id: str, status: str):
    """processing = đã bắt đầu render lại -> dashboard KHÓA nút hủy."""
    _db().collection("render_requests").document(req_id).set({"status": status, "started_at": _now()}, merge=True)


def mark_request_done(req_id: str, note: str = "done"):
    _db().collection("render_requests").document(req_id).set({"status": "done", "note": note, "done_at": _now()}, merge=True)


def set_config(owner: str, patch: dict):
    """Ghi/merge render_config (vd xoá cờ run_now sau khi đã nhận lệnh)."""
    _db().collection("render_config").document(owner).set(patch, merge=True)


def recent_topics(owner: str, channel: str, n: int = 80) -> list[str]:
    """Chủ đề ĐÃ dùng cho kênh -> đưa cho Gemini để TRÁNH trùng (chống 'reused content')."""
    d = _db().collection("render_topics").document(f"{owner}__{channel}").get()
    return (((d.to_dict() or {}).get("topics") or [])[-n:]) if d.exists else []


def save_topics(owner: str, channel: str, topics: list[str]):
    """Lưu chủ đề vừa dùng (cap 300 gần nhất)."""
    ref = _db().collection("render_topics").document(f"{owner}__{channel}")
    d = ref.get()
    cur = (((d.to_dict() or {}).get("topics") or [])) if d.exists else []
    cur = (cur + [t for t in topics if t])[-300:]
    ref.set({"owner": owner, "channel": channel, "topics": cur}, merge=True)


def count_done(owner: str, channel: str, vtype: str = None) -> int:
    """Đếm số video ĐÃ XONG của 1 kênh (để so mục tiêu long/short target)."""
    try:
        q = (_db().collection("render_jobs").where("owner", "==", owner)
             .where("channel", "==", channel).where("status", "==", "done"))
        if vtype:
            q = q.where("type", "==", vtype)
        return sum(1 for _ in q.stream())
    except Exception as e:                       # thiếu composite index / lỗi tạm -> 0 (đừng làm sập run)
        print(f"   ⚠️ count_done lỗi ({e}) -> coi như 0"); return 0


def new_job(owner: str, channel: str, vtype: str = "short", pver: str = "") -> str:
    db = _db(); ref = db.collection("render_jobs").document()
    ref.set({"owner": owner, "channel": channel, "type": vtype, "pver": pver,   # pver = phiên bản pipeline -> dọn thông minh (chỉ xóa bản CŨ)
             "status": "queued", "step": "bắt đầu", "created_at": _now()})
    return ref.id


def update_job(job_id: str, **patch):
    _db().collection("render_jobs").document(job_id).set(patch, merge=True)
