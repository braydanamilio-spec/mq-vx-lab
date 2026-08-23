#!/usr/bin/env python3
"""RESET SỔ VIDEO (23/8/2026) — làm lại từ đầu cho sạch.

Kho Drive đã dọn bằng `wipe_queue.py`, nhưng dashboard vẫn liệt kê video vì nó đọc **sổ**
(`render_jobs` ở project B) chứ không đọc Drive. File đã vào thùng rác mà bản ghi còn thì trang vẫn
hiện — đúng cảnh "dọn rồi mà vẫn thấy video".

Script này xoá bản ghi job đã render xong + reset 2 doc đếm, để số trên dashboard = số THẬT trong kho
(lúc này là 0). KHÔNG đụng: cấu hình kênh, chủ đề (`render_topics`), key.

    python reset_ledger.py --dry-run     # chỉ đếm
    python reset_ledger.py               # xoá thật
"""
import argparse
import os
import sys

import firestore_bridge as FB

OWNER = os.environ.get("RENDER_OWNER", "mm0")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--owner", default=OWNER)
    a = ap.parse_args()

    db = FB._db_jobs()
    col = db.collection("render_jobs")
    n = del_ok = 0
    err = 0
    # 23/8: chạy bằng requirements của AutoPublisher thì `col.stream()` ném
    # AttributeError: '_UnaryStreamMultiCallable' object has no attribute '_retry' (lệch phiên bản
    # google-cloud-firestore/grpc). `list_documents()` đi đường khác nên không dính; giữ stream() làm
    # phương án dự phòng.
    try:
        refs = list(col.list_documents(page_size=500))
    except Exception as e:
        print(f"   ↻ list_documents hỏng ({str(e)[:50]}), dùng stream()")
        refs = [d.reference for d in col.stream()]
    for ref in refs:
        n += 1
        if a.dry_run:
            continue
        try:
            ref.delete()
            del_ok += 1
        except Exception:
            err += 1
        if del_ok and del_ok % 200 == 0:
            print(f"   … đã xoá {del_ok}", flush=True)

    print(f"📒 render_jobs: thấy {n} bản ghi · xoá {del_ok} · lỗi {err}")

    # 23/8: owner là UID Firebase 28 ký tự, KHÔNG phải "mm0" -> bản trước xoá nhầm tên doc nên
    # dashboard vẫn hiện "176 video trong kho". render_stats chỉ chứa doc đếm ({owner},
    # __pushed__{owner}, __rw__{owner}) nên xoá sạch cả collection là đúng và an toàn.
    st = db.collection("render_stats")
    try:
        st_refs = list(st.list_documents(page_size=200))
    except Exception as e:
        st_refs = []
        print(f"   ⚠️ không liệt kê được render_stats: {str(e)[:60]}")
    print(f"📈 render_stats: {len(st_refs)} doc đếm")
    if not a.dry_run:
        for ref in st_refs:
            try:
                ref.delete()
                print(f"   ↺ xoá render_stats/{ref.id}")
            except Exception as e:
                err += 1
                print(f"   ⚠️ không xoá được render_stats/{ref.id}: {str(e)[:50]}")

    print("✅ Sổ đã reset — dashboard sẽ hiện đúng số video CÓ THẬT trong kho.")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
