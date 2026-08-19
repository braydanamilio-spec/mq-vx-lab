"""
seed_new_channels_wave4.py — WAVE 4: 4 kênh MOTIF hoạt hoạ RIÊNG (engine mới, không dùng chung doc/motif cũ):
SWARM (mật độ hạt bay lấp đầy), PULSE (gauge cường độ giác quan), CLOCKWORK (nén thời gian), LONGSHOT (tháp xác suất).
Đủ QC chuẩn như các kênh khác: content_brain.generate_X (MIN_SCORE + accuracy≥95 + viết lại), engine render riêng
đã render-verify (avatar + still giữa animation, không lỗi che khuất).

Idempotent — xem seed_new_channels.py để biết cơ chế đầy đủ.
Dùng: python seed_new_channels_wave4.py [--dry-run]
"""
from __future__ import annotations
import os
import sys

from google.cloud import firestore
from google.oauth2 import service_account

NEW = [
    {"name": "SWARMUSA", "format": "swarm", "accent": "#0D9488",
     "niche": "real crowd/quantity numbers — stadium capacity, population, biology counts, natural phenomena counts. Neutral contexts only (never protests/political crowds)."},
    {"name": "PULSEUSA", "format": "pulse", "accent": "#EA580C",
     "niche": "real sensory intensity — loudness (dB), brightness (lux), heat (°F), g-force, radiation. One unit per video."},
    {"name": "CLOCKWORKUSA", "format": "clockwork", "accent": "#C2410C",
     "niche": "huge real timespans compressed onto one scale — geological time, evolution, history, astronomy, construction/career timelines — landing on a shockingly tiny real fact."},
    {"name": "LONGSHOTUSA", "format": "longshot", "accent": "#4F46E5",
     "niche": "real, sourced probability/odds — everyday risks, sports, medical/actuarial stats, disasters, records. Never gambling advice, just real published odds."},
]

TARGET_KEYS = ["short_target", "long_target", "n_shorts", "make_long", "tier", "cap_gb"]


def _db() -> firestore.Client:
    key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_B") or os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    project = os.environ.get("FIREBASE_PROJECT_ID_B") or os.environ.get("FIREBASE_PROJECT_ID")
    creds = service_account.Credentials.from_service_account_file(key)
    return firestore.Client(project=project, credentials=creds)


def main():
    dry = "--dry-run" in sys.argv
    db = _db()
    existing = list(db.collection("render_channels").stream())
    if not existing:
        sys.exit("❌ render_channels rỗng.")
    tmpls = [d.to_dict() or {} for d in existing]
    owner = os.environ.get("OWNER_UID") or next((t.get("owner") for t in tmpls if t.get("owner")), "")
    if not owner:
        sys.exit("❌ Không có owner. Set OWNER_UID.")
    have = {(t.get("name") or "") for t in tmpls}
    sample = tmpls[0]
    target = {k: sample.get(k) for k in TARGET_KEYS if sample.get(k) is not None}
    print(f"owner={owner} · kênh hiện có={len(have)} · mẫu target={target}\n")

    made = skipped = 0
    for ch in NEW:
        if ch["name"] in have:
            print(f"  ⏭  {ch['name']:12s} đã tồn tại -> bỏ qua"); skipped += 1; continue
        doc = {"owner": owner, "paused": False, "type": "short", "make_long": False,
                "long_target": 0, "n_shorts": 3, **target, **ch}
        print(f"  ➕ {ch['name']:12s} [{ch['format']}] {ch['niche'][:42]}")
        made += 1
        if not dry:
            db.collection("render_channels").document(f"{owner}__{ch['name']}").set(doc, merge=True)

    print(f"\n{'(dry) sẽ tạo' if dry else '✅ đã tạo'} {made} kênh, bỏ qua {skipped}.")


if __name__ == "__main__":
    main()
