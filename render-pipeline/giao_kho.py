#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GIAO VIDEO VÀO KHO — R2 + D1, KHÔNG ĐỤNG FIRESTORE  (1/9/2026)

Anh: *"tại sao trước đã xây sẵn rồi mà lần nào lên cũng ko tự động chạy mà toàn bị lỗi firebase
này nọ, tìm fix triệt để."*

Hai bệnh khác nhau, và vì chúng cùng biểu hiện "không ra video" nên bị tưởng là một:

  BỆNH 1 — không tự chạy. Không liên quan Firebase: GitHub nuốt tick cron · cổng chặn vì lý do
  ngoài phạm vi · 110 ảnh nền chưa bao giờ lên git. Đã chữa cả ba đêm 31/8.

  BỆNH 2 — Firestore cạn. Chính `publish.yml` đã ghi: *"100 lượt chạy/ngày của nhóm
  publish/thumbnail/health-guardian chính là ~52% trần Firestore"*. Tối ưu phía Python bao nhiêu
  vòng cũng không chạm tới, vì nguồn tiêu thụ nằm ở nhóm workflow chạy mỗi 30 phút.

CHỮA TRIỆT ĐỂ nghĩa là **bỏ hẳn Firestore khỏi đường dựng-và-lưu**, chứ không phải tiết kiệm
lượt đọc. Hai mảnh đã có sẵn trong repo mà chưa ai nối vào nhau:

  · `r2_store.upload()` — Cloudflare R2, 10 GB free MỖI tài khoản, gộp nhiều tài khoản. Viết
    xong từ lâu, **không một dòng nào gọi tới**.
  · `hot_db.ghi_job()`  — ghi bản ghi việc vào Cloudflare D1 (5.000.000 đọc/ngày, gấp 100 lần
    Firestore).

Nối hai mảnh: video rời artifact 14 ngày sang kho vĩnh viễn, và có bản ghi tra được — cả hai
đều ở Cloudflare, cùng hệ với khoá vẽ ảnh đang dùng. Firestore không còn nằm trên đường đi.

Hỏng thì NUỐT: video đã dựng xong vẫn nằm trong artifact, không mất. Một bước giao kho hỏng
không được phép làm hỏng lượt render.
"""
import os
import sys


def giao(mp4: str, kenh: str, loai: str = "short", tieu_de: str = "") -> dict:
    """Đẩy một video lên R2 rồi ghi bản ghi vào D1. Trả {'r2':..., 'd1':bool}."""
    ra = {"r2": None, "d1": False}
    if not os.path.exists(mp4):
        return ra
    ten = os.path.basename(mp4)

    try:
        import r2_store
        ra["r2"] = r2_store.upload(mp4, ten)
    except Exception as e:
        print(f"   ⚠️ R2 lỗi: {str(e)[:80]}")

    try:
        import hot_db
        owner = os.environ.get("OWNER_UID", "")
        if owner and hot_db.bat_ghi():
            # `drive_id` mang khoá R2 — cùng vai trò "video nằm ở đâu", nên bộ đăng chỉ cần đọc
            # đúng trường nó vẫn đọc, không phải đổi lược đồ.
            khoa = (ra["r2"] or {}).get("key") or ""
            hot_db.ghi_job(owner, f"r2:{ten}", kenh, loai, "done",
                           step="giao kho R2", title=tieu_de or ten, drive_id=khoa)
            hot_db.xa_het()
            ra["d1"] = True
    except Exception as e:
        print(f"   ⚠️ D1 lỗi: {str(e)[:80]}")

    if ra["r2"] or ra["d1"]:
        print(f"   📦 {ten}: R2={'✅' if ra['r2'] else '—'} · D1={'✅' if ra['d1'] else '—'}")
    return ra


def main() -> int:
    if len(sys.argv) < 2:
        print("dùng: giao_kho.py <thư_mục_out> [kenh]")
        return 2
    thu = sys.argv[1]
    n = 0
    for t in sorted(os.listdir(thu)):
        if not t.endswith(".mp4"):
            continue
        loai = "long" if ("L_" in t[:5] or t.startswith(("v3L_", "v5L_"))) else "short"
        r = giao(os.path.join(thu, t), t.split("_", 1)[-1].rsplit(".", 1)[0], loai)
        n += bool(r["r2"] or r["d1"])
    print(f"\n{'✅' if n else '⚠️'} giao {n} video vào kho R2+D1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
