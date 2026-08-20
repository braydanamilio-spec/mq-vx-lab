"""
migrate_keys_to_b.py — COPY bảng gemini_keys từ Project A sang Project B (chạy MỘT LẦN).

VÌ SAO CẦN
Sau khi bật SHARD_META=1, render đã đọc config/channels/topics/requests từ Project B. Nhưng
gemini_keys thì VẪN nằm ở Project A — đúng project mà publish/publish_social dùng. 18 luồng render
đọc bảng key mỗi phiên nên ăn hết hạn mức đọc free của A; hậu quả 20/8: publish, publish_social,
rồi tới cả bước LẬP KẾ HOẠCH render đều chết vì "ResourceExhausted: 429 Quota exceeded" — sản xuất
đứng cho tới khi quota reset (~08:00 UTC). Cách ly bảng key sang B thì render KHÔNG còn đụng vào
hạn mức của A nữa.

CÁCH DÙNG (an toàn, chạy lại nhiều lần cũng được)
    python3 migrate_keys_to_b.py --dry-run     # xem trước: có bao nhiêu key, sẽ copy cái nào
    python3 migrate_keys_to_b.py               # copy thật (A -> B), KHÔNG xoá bên A

Sau khi copy xong, bật biến repo SHARD_KEYS=1:
    gh variable set SHARD_KEYS --body 1 --repo braydanamilio-spec/mq-vx-lab
và thêm `SHARD_KEYS: ${{ vars.SHARD_KEYS }}` vào env của các workflow render.

KHÔNG XOÁ BÊN A: dashboard + Worker vẫn ghi key vào A. Đây là bản COPY để render đọc. Nếu sau này
muốn dứt hẳn thì phải sửa cả dashboard/Worker ghi sang B rồi mới dọn A — chưa làm ở bước này.
Vì read_keys() có đường lùi (B rỗng -> đọc A), bật SHARD_KEYS sớm cũng không gãy gì.
"""
from __future__ import annotations
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firestore_bridge as FB


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="chỉ xem, không ghi gì")
    a = ap.parse_args()

    owner = os.environ.get("OWNER_UID")
    if not owner:
        print("❌ Thiếu OWNER_UID"); sys.exit(1)

    src = FB._db()          # Project A (nguồn thật, dashboard/Worker đang ghi vào đây)
    dst = FB._db_jobs()     # Project B (render đọc)
    if src is dst:
        print("⚠️ Project A và B đang trỏ cùng một nơi (chưa cấu hình creds B) -> không cần copy.")
        return

    rows = []
    for d in src.collection("gemini_keys").where("owner", "==", owner).stream():
        x = d.to_dict() or {}
        if x.get("key"):
            rows.append((d.id, x))
    print(f"📖 Project A có {len(rows)} key của owner này.")
    if not rows:
        print("   (không có gì để copy)"); return

    if a.dry_run:
        for i, (kid, x) in enumerate(rows, 1):
            tag = x.get("email") or ("••••" + str(x.get("key", ""))[-4:])
            print(f"   {i:2}. {kid[:8]}… {tag} · alive={x.get('alive')} req_today={x.get('req_today', 0)}")
        print("\n(dry-run: chưa ghi gì sang B)")
        return

    ok = 0
    for kid, x in rows:
        try:
            dst.collection("gemini_keys").document(kid).set(x, merge=True)
            ok += 1
        except Exception as e:
            print(f"   ⚠️ copy {kid[:8]}… lỗi: {str(e)[:70]}")
    print(f"✅ Đã copy {ok}/{len(rows)} key sang Project B (KHÔNG xoá bên A).")
    print("   Bước tiếp: bật biến repo SHARD_KEYS=1 để render đọc key từ B.")


if __name__ == "__main__":
    main()
