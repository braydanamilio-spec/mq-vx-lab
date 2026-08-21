"""
seed_channels_wave8.py — Ghi 10 kênh WAVE 8 vào render_channels (Firestore B). Chạy MỘT LẦN.

Dữ liệu kênh nằm ở wave8_channels.json (cùng thư mục) — tách data khỏi code để rà soát dễ
và tái dùng khuôn này cho wave sau (đổi file json, không đổi script).

CÁCH DÙNG (an toàn, chạy lại nhiều lần cũng được — set merge=True, không đè kênh cũ):
    python3 seed_channels_wave8.py --dry-run     # xem trước 10 kênh sẽ ghi
    python3 seed_channels_wave8.py               # ghi thật

Mỗi kênh format="doc" -> tự vào luồng chuẩn hiện tại: 1 long (3 phần) + 3 short bám nội dung,
cảnh hook footage thật, không intro/outro, cắt 2-3s, SFX, thumbnail khung hook, đủ 3 cổng QC.
Niche nào nhạy cảm đều có sẵn câu STRICT -> policy_lint trong plan sẽ xác nhận ở phiên kế.
"""
from __future__ import annotations
import os
import sys
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firestore_bridge as FB


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    owner = os.environ.get("OWNER_UID")
    if not owner:
        print("❌ Thiếu OWNER_UID"); sys.exit(1)

    data = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "wave8_channels.json")))
    db = FB._db_meta()
    have = {(d.to_dict() or {}).get("name") for d in db.collection("render_channels")
            .where("owner", "==", owner).stream()}
    print(f"📖 render_channels hiện có {len(have)} kênh.")

    for name, cfg in data.items():
        tag = "ĐÃ CÓ (merge)" if name in have else "MỚI"
        print(f"  {name:<12} {tag} · voice={cfg['voice']} · accent={cfg['accent']}")
        if a.dry_run:
            continue
        doc = {**cfg, "owner": owner}
        db.collection("render_channels").document(f"{owner}__{name}").set(doc, merge=True)
    print("(dry-run: chưa ghi gì)" if a.dry_run else f"✅ Đã ghi {len(data)} kênh Wave 8 vào render_channels.")


if __name__ == "__main__":
    main()
