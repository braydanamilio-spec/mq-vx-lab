"""
seed_new_channels_wave3.py — WAVE 3: 6 kênh "doc" mới, lấy cảm hứng từ hệ epistemic-grammar
(BLACK START/BRIGHT LINE/WITNESS MARK/LINE ITEM/HALF OPEN/FIXED POINT) nhưng viết lại cho
pipeline TỰ ĐỘNG HOÀN TOÀN của MM0 (Gemini viết kịch bản + Cinematic engine render, không
cần agent thủ công mỗi video). Đều dùng format "doc" (đã chứng minh linh hoạt qua Wave 2)
để tránh trùng motif với RANKEDUSA/SCALEDUSA (schema cố định S/A/B/C hoặc trục vật lý).

Idempotent — xem seed_new_channels.py để biết cơ chế đầy đủ.
Dùng: python seed_new_channels_wave3.py [--dry-run]
"""
from __future__ import annotations
import os
import sys

from google.cloud import firestore
from google.oauth2 import service_account

NEW = [
    {"name": "GRIDUSA", "format": "doc", "accent": "#64748B", "accent2": "#94A3B8", "category": "28",
     "style": "technical, tense, systems-thinking",
     "niche": "the invisible systems that run America — power grid, data centers, supply chains, water — how they work and what happens when they fail"},
    {"name": "RULEDUSA", "format": "doc", "accent": "#E11D48", "accent2": "#FB7185", "category": "27",
     "style": "dry, deadpan, matter-of-fact",
     "niche": "real classification rulings that go the surprising way — a tomato ruled a vegetable, a burrito ruled not a sandwich, what legally counts as milk or organic"},
    {"name": "VAULTUSA", "format": "doc", "accent": "#B45309", "accent2": "#F2A93B", "category": "27",
     "style": "precise, investigative",
     "niche": "how experts really catch fakes and fraud — art authentication, forensic accounting, appraisal, verification"},
    {"name": "LEDGERUSA", "format": "doc", "accent": "#15803D", "accent2": "#86EFAC", "category": "27",
     "style": "sharp, procedural",
     "niche": "how a bill, tax, or fee is actually computed line by line — hidden charges, the real math behind the number"},
    {"name": "SIGNALUSA", "format": "doc", "accent": "#A21CAF", "accent2": "#E879F9", "category": "28",
     "style": "cool, technical, slightly ominous",
     "niche": "how algorithms decide what to trust — spam filters, credit scores, recommendation engines, fraud detection"},
    {"name": "MARGINUSA", "format": "doc", "accent": "#1E40AF", "accent2": "#60A5FA", "category": "28",
     "style": "tight, technical, meticulous",
     "niche": "precision manufacturing and measurement — why 'exact' specs always hide a tolerance, from aerospace bolts to microchips"},
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
