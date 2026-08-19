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
    {"name": "GRIDUSA", "format": "doc", "accent": "#64748B", "accent2": "#94A3B8",
     "style": "technical, tense, systems-thinking",
     "niche": "the invisible systems that run America — power grid, data centers, supply chains, water — how they work and what happens when they fail. STRICT: only real documented engineering facts (e.g. NERC reliability standards, real blackout case studies) — never present speculation as fact."},
    {"name": "RULEDUSA", "format": "doc", "accent": "#E11D48", "accent2": "#FB7185",
     "style": "dry, deadpan, matter-of-fact",
     "niche": "real classification rulings that go the surprising way — a tomato ruled a vegetable, a burrito ruled not a sandwich, what legally counts as milk or organic. STRICT: only REAL, well-documented, verifiable rulings/regulations — name the actual court/agency + year in the narration (e.g. Nix v. Hedden 1893, FDA standards of identity, USDA organic 95%/70%, FTC Made in USA). If unsure a case is real, pick a different well-known documented one. NEVER invent a ruling or case name."},
    {"name": "VAULTUSA", "format": "doc", "accent": "#B45309", "accent2": "#F2A93B",
     "style": "precise, investigative",
     "niche": "how experts really catch fakes and fraud — art authentication, forensic accounting, appraisal, verification. STRICT: describe REAL documented methods (UV pigment analysis, provenance trails, Benford's Law) — never name a specific real person/case unless it is a well-documented public case."},
    {"name": "LEDGERUSA", "format": "doc", "accent": "#15803D", "accent2": "#86EFAC",
     "style": "sharp, procedural",
     "niche": "how a bill, tax, or fee is actually computed line by line — hidden charges, the real math behind the number. STRICT: explain the general MECHANISM/FORMULA only (e.g. how fuel surcharges work, how mortgage escrow is computed, how sales-tax nexus works) — illustrative example numbers only, never real personal financial data, never advise the viewer what to do."},
    {"name": "SIGNALUSA", "format": "doc", "accent": "#A21CAF", "accent2": "#E879F9",
     "style": "cool, technical, slightly ominous",
     "niche": "how algorithms decide what to trust — spam filters, credit scores, recommendation engines, fraud detection. STRICT: explain the documented, publicly-known mechanism (FICO factors, email header analysis, collaborative filtering) — no conspiracy framing, no unverified claims about a specific company."},
    {"name": "MARGINUSA", "format": "doc", "accent": "#1E40AF", "accent2": "#60A5FA",
     "style": "tight, technical, meticulous",
     "niche": "precision manufacturing and measurement — why 'exact' specs always hide a tolerance, from aerospace bolts to microchips. STRICT: real documented engineering standards (ISO/ANSI tolerance classes, real historical examples like the Hubble mirror flaw) — cite real standards/examples, never invent numbers."},
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
