"""
migrate_to_shards.py — DỜI dữ liệu từ Project A sang B (render) + C (publish), MỘT LẦN.

Chạy khi Firestore A đã reset quota (đọc A tối thiểu: mỗi collection stream đúng 1 lượt).

  A -> B (render meta): render_config, render_channels, gemini_keys,
                        storage_accounts, render_topics, render_requests
  A -> C (publish owned): videos, counters, quota, yt_queue, social_queue

GIỮ NGUYÊN ở A (shared, KHÔNG dời): settings, connections, channels, storage_reservations
  -> publisher đọc trực tiếp A; Worker/dashboard vẫn ghi A như cũ.

ENV cần:
  A: GOOGLE_APPLICATION_CREDENTIALS + FIREBASE_PROJECT_ID
  B: GOOGLE_APPLICATION_CREDENTIALS_B + FIREBASE_PROJECT_ID_B
  C: GOOGLE_APPLICATION_CREDENTIALS_C + FIREBASE_PROJECT_ID_C

Dùng: python migrate_to_shards.py [--dry-run]   (dry-run: chỉ đếm, KHÔNG ghi)
An toàn: idempotent (ghi merge theo doc id) -> chạy lại không hỏng; nhưng mỗi lần chạy lại = đọc A thêm 1 lượt.
"""
from __future__ import annotations
import os
import sys

from google.cloud import firestore
from google.oauth2 import service_account

TO_B = ["render_config", "render_channels", "gemini_keys",
        "render_topics", "render_requests"]
# storage_accounts GIỮ Ở A — connect-worker (Cloudflare Worker, biết mỗi Project A) quản lý connect/sync/xoá kho Drive.
TO_C = ["videos", "counters", "quota", "yt_queue", "social_queue"]


def _client(key_env: str, proj_env: str, label: str) -> firestore.Client:
    key = os.environ.get(key_env)
    project = os.environ.get(proj_env)
    if not (key and project and os.path.exists(key)):
        sys.exit(f"❌ Thiếu creds {label}: {key_env} + {proj_env} (file phải tồn tại).")
    creds = service_account.Credentials.from_service_account_file(key)
    return firestore.Client(project=project, credentials=creds)


def _copy(src: firestore.Client, dst: firestore.Client, coll: str, dry: bool) -> int:
    """Stream 1 collection từ A -> ghi batch sang target (giữ nguyên doc id). Trả số doc."""
    n = 0
    batch = dst.batch(); pending = 0
    for d in src.collection(coll).stream():          # đọc A: 1 lượt/collection
        n += 1
        if dry:
            continue
        batch.set(dst.collection(coll).document(d.id), d.to_dict() or {}, merge=True)
        pending += 1
        if pending >= 400:                            # Firestore batch tối đa 500
            batch.commit(); batch = dst.batch(); pending = 0
    if not dry and pending:
        batch.commit()
    return n


def main():
    dry = "--dry-run" in sys.argv
    A = _client("GOOGLE_APPLICATION_CREDENTIALS", "FIREBASE_PROJECT_ID", "A")
    B = _client("GOOGLE_APPLICATION_CREDENTIALS_B", "FIREBASE_PROJECT_ID_B", "B")
    C = _client("GOOGLE_APPLICATION_CREDENTIALS_C", "FIREBASE_PROJECT_ID_C", "C")
    print(f"{'🔎 DRY-RUN' if dry else '🚚 MIGRATE'}  A -> B(render) + C(publish)\n")

    tot = 0
    for coll in TO_B:
        c = _copy(A, B, coll, dry); tot += c
        print(f"  A->B  {coll:22s} {c:5d} doc")
    for coll in TO_C:
        c = _copy(A, C, coll, dry); tot += c
        print(f"  A->C  {coll:22s} {c:5d} doc")

    print(f"\n{'(dry) sẽ dời' if dry else '✅ đã dời'} {tot} doc. "
          f"Shared (settings/connections/channels/storage_reservations) GIỮ ở A.")
    if not dry:
        print("→ Bật cờ: render workflow SHARD_META=1 · publish workflow SHARD_PUBLISH=1 rồi chạy.")


if __name__ == "__main__":
    main()
