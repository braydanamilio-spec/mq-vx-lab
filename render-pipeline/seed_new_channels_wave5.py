"""
seed_new_channels_wave5.py — WAVE 5: 2 kênh "doc" SPECULATIVE — tận dụng quota ảnh AI (Nano Banana,
~500 ảnh/ngày/key, TÁCH RIÊNG quota viết chữ, đang bỏ phí 100%) cho đúng chủ đề mà ảnh THẬT
không thể tồn tại — tương lai (chưa xảy ra) và hiện tượng vũ trụ chưa ai chụp được. Dùng format
"doc" có sẵn (Cinematic engine) + ai_style/ai_only mới (fetch_image bỏ qua tìm Openverse hẳn,
đi thẳng vào Nano Banana vẽ theo gu riêng — xem datastory_ci.py).

Idempotent — xem seed_new_channels.py để biết cơ chế đầy đủ.
Dùng: python seed_new_channels_wave5.py [--dry-run]
"""
from __future__ import annotations
import os
import sys

from google.cloud import firestore
from google.oauth2 import service_account

NEW = [
    {"name": "FUTUREUSA", "format": "doc", "accent": "#3B82F6", "accent2": "#A855F7",
     "style": "awe, speculative, cinematic wonder",
     "ai_style": "cinematic sci-fi concept art, dramatic volumetric lighting, hyper-detailed digital matte painting",
     "ai_only": True,
     "niche": "speculative visions of the future — future cities, technology, transportation, food, medicine, daily life 50-200 years from now. Loosely grounded in real current science/trends but presented as IMAGINATIVE SPECULATION, never as predicted fact. Narration MUST use clearly speculative language ('could', 'might', 'imagine if', 'one vision of') — never state a future event/technology as a certainty. No real named companies/people/countries making false claims."},
    {"name": "UNSEENUSA", "format": "doc", "accent": "#4C1D95", "accent2": "#A78BFA",
     "style": "awe, cosmic mystery, reverent",
     "ai_style": "cinematic space concept art, artist's impression, dramatic deep-space lighting, hyper-detailed digital painting",
     "ai_only": True,
     "niche": "real, documented theoretical astrophysics and cosmic phenomena that have NEVER been photographed by any camera — black hole interiors, exoplanet surfaces, the early universe, neutron star surfaces, theoretical multiverse concepts, wormholes. STRICT: narration must be grounded in REAL scientific consensus/theory (general relativity, event horizon, spaghettification, real named exoplanets/phenomena) — only the VISUALS are speculative because no photo can exist. Narration must explicitly frame it as 'what scientists believe it might look like' / 'artist's impression' — never claim the image is a real photo."},
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
