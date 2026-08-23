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

import firestore_bridge as FB  # noqa: F401  (giữ để dùng chung cấu hình creds)

OWNER = os.environ.get("RENDER_OWNER", "mm0")


def _clients():
    """Trả [(tên, client)] cho CẢ B và B2.

    23/8 — vì sao phải làm rõ: `FB._db_jobs()` tự chuyển sang B2 khi B nghẽn quota. Lần reset trước
    nó xoá 546 bản ghi ở B2 còn B vẫn nguyên 40 bản ghi -> dashboard vẫn hiện video cũ. Sổ nằm ở 2
    nơi thì phải dọn cả 2 nơi, không thể tin "đã xoá xong" từ một client động.
    """
    from google.cloud import firestore as _fs
    out = []
    for label, env_pid in (("B", "FIREBASE_PROJECT_ID_B"), ("B2", "FIREBASE_PROJECT_ID_B2")):
        pid = os.environ.get(env_pid)
        if not pid:
            continue
        try:
            out.append((f"{label}/{pid}", _fs.Client(project=pid)))
        except Exception as e:
            print(f"⚠️ không mở được {label} ({pid}): {str(e)[:60]}")
    return out


def _wipe_collection(db, name, dry) -> tuple[int, int, int]:
    col = db.collection(name)
    try:
        refs = list(col.list_documents(page_size=500))
    except Exception as e:
        print(f"   ⚠️ không liệt kê được {name}: {str(e)[:60]}")
        return 0, 0, 1
    n = len(refs)
    ok = err = 0
    if dry:
        return n, 0, 0
    for ref in refs:
        try:
            ref.delete()
            ok += 1
        except Exception:
            err += 1
    return n, ok, err


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--owner", default=OWNER)
    a = ap.parse_args()

    err = 0
    for label, db in _clients():
        print(f"\n🗂  {label}")
        for coll in ("render_jobs", "render_stats"):
            n, ok, e = _wipe_collection(db, coll, a.dry_run)
            err += e
            print(f"   {coll:<13} thấy {n:>4} · xoá {ok:>4}" + (f" · lỗi {e}" if e else ""))
    print("\n✅ Sổ đã reset ở CẢ B và B2 — dashboard hiện đúng số video CÓ THẬT trong kho.")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
