"""
seed_new_channels.py — Tạo doc render_channels cho 10 KÊNH MỚI (5 motif + 5 doc) trên Project B.

Lấy target/quota từ 1 kênh CŨ làm mẫu (short_target/long_target/n_shorts/make_long/tier/cap_gb)
-> kênh mới sản xuất cùng nhịp; chỉ override identity + format + brand.

Idempotent: doc id = {owner}__{name}; đã có thì bỏ qua (không ghi đè target anh đã chỉnh).
Dùng: python seed_new_channels.py [--dry-run]
ENV: GOOGLE_APPLICATION_CREDENTIALS_B + FIREBASE_PROJECT_ID_B (+ OWNER_UID nếu chưa suy ra được).
"""
from __future__ import annotations
import os
import sys

from google.cloud import firestore
from google.oauth2 import service_account

# 10 kênh mới — khớp engine đã xây + brand dashboard (RS_PRESETS)
NEW = [
    {"name": "GUESSUSA",   "format": "guess",   "accent": "#F5B301", "category": "24",
     "niche": "US cities, world landmarks, famous scientists & inventors, history"},
    {"name": "MAPPEDUSA",  "format": "mapped",  "accent": "#22D3EE", "category": "27",
     "niche": "US demographics, cost of living, health & economy by state"},
    {"name": "RANKEDUSA",  "format": "ranked",  "accent": "#7C5CFF", "category": "24",
     "niche": "US fast food, streaming, cars, brands, cities ranked"},
    {"name": "SCALEDUSA",  "format": "scaled",  "accent": "#2FA84F", "category": "28",
     "niche": "ocean animals, tallest buildings, planets, dinosaurs sizes"},
    {"name": "THENNOWUSA", "format": "thennow", "accent": "#EC4899", "category": "24",
     "niche": "cost of living, tech, salaries, prices — 1970 vs now"},
    {"name": "COSMOS",     "format": "doc", "accent": "#7C5CFF", "accent2": "#22D3EE", "category": "28",
     "style": "awe, cosmic wonder", "niche": "space, galaxies, black holes, planets, the universe"},
    {"name": "THEDEEP",    "format": "doc", "accent": "#0EA5E9", "accent2": "#22D3EE", "category": "28",
     "style": "eerie, mysterious, deep", "niche": "deep sea creatures, ocean mysteries & abyss"},
    {"name": "WHYUSA",     "format": "doc", "accent": "#F59E0B", "accent2": "#F5B301", "category": "28",
     "style": "curious, clear, fascinating", "niche": "why natural phenomena happen — science explained"},
    {"name": "EMPIREUSA",  "format": "doc", "accent": "#EAB308", "accent2": "#F5B301", "category": "27",
     "style": "ambitious, dramatic", "niche": "how famous entrepreneurs built their empires"},
    {"name": "UNSOLVED",   "format": "doc", "accent": "#EF4444", "accent2": "#F59E0B", "category": "27",
     "style": "suspenseful, mysterious", "niche": "unsolved mysteries, ancient enigmas, unexplained"},
]

# Field nhịp sản xuất copy từ kênh mẫu (nếu có)
TARGET_KEYS = ["short_target", "long_target", "n_shorts", "make_long", "tier", "cap_gb"]


def _db() -> firestore.Client:
    key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_B") or os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    project = os.environ.get("FIREBASE_PROJECT_ID_B") or os.environ.get("FIREBASE_PROJECT_ID")
    creds = service_account.Credentials.from_service_account_file(key)
    return firestore.Client(project=project, credentials=creds)


def main():
    dry = "--dry-run" in sys.argv
    db = _db()
    # đọc kênh hiện có -> lấy owner + mẫu target
    existing = list(db.collection("render_channels").stream())
    if not existing:
        sys.exit("❌ render_channels rỗng — không suy ra được owner/mẫu. Set OWNER_UID và chạy lại.")
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
        doc = {"owner": owner, "paused": False, **target, **ch}
        print(f"  ➕ {ch['name']:12s} [{ch['format']}] {ch['niche'][:42]}")
        made += 1
        if not dry:
            db.collection("render_channels").document(f"{owner}__{ch['name']}").set(doc, merge=True)

    print(f"\n{'(dry) sẽ tạo' if dry else '✅ đã tạo'} {made} kênh, bỏ qua {skipped}. "
          f"{'' if dry else 'Mẻ render tới sẽ tự nhận (matrix 18 luồng, dư xếp hàng).'}")


if __name__ == "__main__":
    main()
