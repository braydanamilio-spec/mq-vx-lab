#!/usr/bin/env python3
"""KIỂM KHO — LẤY SỐ THẬT TỪ DRIVE, KHÔNG TIN SỔ CỘNG DỒN (24/8/2026).

BỆNH (anh chỉ ra: "1343 video lận có nhầm ko")
----------------------------------------------
`render_stats/__pushed__{owner}.total` là sổ **CỘNG DỒN** bằng `Increment(1)`: mỗi lượt đẩy kho
thành công cộng 1, và **không có đường nào trừ đi**. Ba việc bình thường đều làm nó phồng lên:
  • render lại 1 video  -> bản cũ vào thùng rác, bản mới cộng thêm 1  => 1 video đếm 2 lần
  • dọn rác (`find_junk --don`) -> file vào thùng rác, sổ giữ nguyên
  • xoá tay trên Drive         -> sổ giữ nguyên
Nên "Tổng cộng dồn" đúng NGHĨA ĐEN của nó (số lượt render thành công từ trước tới nay) nhưng SAI
với thứ anh muốn biết (**số video đang thật sự nằm trong kho**). Càng render lại nhiều thì càng lệch.

LUẬT (bổ sung mục 7 PIPELINE_RULES)
-----------------------------------
Một con số hiển thị cho người vận hành phải **suy ra từ sự thật hiện tại**, không được cộng dồn
theo sự kiện — vì sự kiện chỉ có chiều lên, mà kho thì có cả chiều xuống.
NGUỒN SỰ THẬT DUY NHẤT của "video trong kho" = **danh sách file .mp4 trên Drive (chưa vào thùng rác)**.

CÁCH LÀM
--------
1. Đi hết mọi kho Drive, lấy id + tên + ngày tạo của mọi `.mp4` còn sống (đọc Drive, KHÔNG tốn
   hạn mức Firestore).
2. Đọc `render_jobs` (status=done, có drive_id) để biết mỗi file thuộc kênh nào, long hay short.
3. Đối chiếu:
     • job có drive_id KHÔNG còn trên Drive  -> file đã bị xoá/thay -> **xoá bản ghi job** (nếu --ghi),
       nếu không `count_done()` sẽ tưởng kênh đó còn đủ video và ngừng làm tiếp.
     • file trên Drive KHÔNG có job          -> đếm theo tên file (`KENH__ngày__seri__L/S__tiêu-đề`).
4. GHI ĐÈ (set, không Increment) `render_stats/{owner}` và `render_stats/__pushed__{owner}` bằng số
   vừa đếm, kèm `kho_at`. Từ giờ dashboard hiện số khớp với thư viện.

    python kiem_kho.py            # chỉ đếm + in lệch
    python kiem_kho.py --ghi      # ghi đè sổ + dọn job trỏ vào file đã mất
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

# Tên chuẩn mới: KENH__YYYYMMDD__seri__L__tieu-de  (xem run_render.ten_file)
TEN = re.compile(r"^([A-Za-z0-9]+)__")


def _vai(ten: str) -> str:
    """long/short suy từ tên file. Tên chuẩn mới có ô vai trò `L`/`S1..`; tên cũ thì đoán theo
    chữ 'long' trong tên, còn lại coi là short (short chiếm đa số nên đoán sai ít hơn)."""
    p = ten.split("__")
    if len(p) >= 4:
        v = p[3].upper()
        if v == "L":
            return "l"
        if v.startswith("S"):
            return "s"
    return "l" if "long" in ten.lower() else "s"


def _quet(drv, folder_id, sau=0, ra=None):
    """Đi đệ quy mọi thư mục con — chép từ find_junk.py (đã kiểm chứng: quét THẲNG từ root,
    child_folder(create=False) để công cụ chỉ-đọc không tự tạo thư mục)."""
    ra = [] if ra is None else ra
    if sau > 4:
        return ra
    tok = None
    while True:
        r = drv.svc.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id,name,mimeType,createdTime)",
            pageSize=1000, pageToken=tok,
            supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        for f in r.get("files", []):
            if f.get("mimeType") == "application/vnd.google-apps.folder":
                _quet(drv, f["id"], sau + 1, ra)
            else:
                ra.append(f)
        tok = r.get("nextPageToken")
        if not tok:
            break
    return ra


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ghi", action="store_true", help="ghi đè sổ thật + dọn job trỏ vào file đã mất")
    ap.add_argument("--owner", default=os.environ.get("RENDER_OWNER", ""))
    a = ap.parse_args()
    if not a.owner:
        print("❌ thiếu RENDER_OWNER")
        return 1

    src = os.environ.get("AUTOPUBLISHER_SRC")
    if src and src not in sys.path:
        sys.path.insert(0, src)
    import storage as ST
    import firestore_bridge as FB

    accs = ST.pool_accounts()
    if not accs:
        print("❌ không đọc được kho nào — DỪNG (không dám kết luận 'kho rỗng' rồi ghi đè sổ về 0).")
        return 1

    song: dict[str, dict] = {}          # drive_id -> {name, created}
    hong_kho = 0
    for acc in accs:
        try:
            drv = ST.account_drive(acc)
            fs = _quet(drv, acc.get("root"))
        except Exception as e:
            hong_kho += 1
            print(f"   ⚠️ {acc.get('name')}: đọc hụt ({str(e)[:60]})")
            continue
        for f in fs:
            if f["name"].lower().endswith(".mp4"):
                song[f["id"]] = {"name": f["name"], "created": str(f.get("createdTime") or "")}

    if hong_kho:
        # Kho đọc hụt = file của kho đó biến mất khỏi danh sách -> ghi đè sổ sẽ đếm THIẾU và xoá
        # nhầm job. Thà không ghi còn hơn ghi sai (bài học "chết câm": số sai nguy hơn không có số).
        print(f"\n🛑 {hong_kho}/{len(accs)} kho đọc hụt — KHÔNG ghi đè sổ lần này (sẽ đếm thiếu).")
        a.ghi = False

    print(f"📦 Kho Drive có THẬT: {len(song):,} file .mp4 (trên {len(accs) - hong_kho} kho đọc được)")

    theo_kenh: dict = defaultdict(lambda: {"l": 0, "s": 0})
    theo_ngay: dict = defaultdict(int)
    mat_job = []          # job trỏ vào file không còn -> cần xoá bản ghi
    da_khop = set()
    try:
        q = (FB._db_jobs().collection("render_jobs")
             .where("owner", "==", a.owner).where("status", "==", "done"))
        for d in FB._stream_at(q, 90):
            x = d.to_dict() or {}
            dv = x.get("drive_id") or ""
            if not dv:
                continue
            if dv not in song:
                mat_job.append((d.id, x.get("channel", "?"), x.get("type", "?")))
                continue
            da_khop.add(dv)
            ten = str(x.get("channel") or "").upper()
            if ten:
                theo_kenh[ten]["l" if x.get("type") == "long" else "s"] += 1
            theo_ngay[song[dv]["created"][:10].replace("-", "")] += 1
    except Exception as e:
        print(f"❌ đọc render_jobs lỗi: {str(e)[:90]} — chỉ đếm được theo tên file.")

    mo_coi = [v for k, v in song.items() if k not in da_khop]
    for v in mo_coi:
        m = TEN.match(v["name"])
        if m:
            theo_kenh[m.group(1).upper()][_vai(v["name"])] += 1
            theo_ngay[v["created"][:10].replace("-", "")] += 1

    tong = len(song)
    try:
        d = FB._db_jobs().collection("render_stats").document(f"__pushed__{a.owner}").get()
        so_cu = int((d.to_dict() or {}).get("total", 0) or 0) if d.exists else 0
    except Exception:
        so_cu = -1

    print(f"📒 Sổ cộng dồn đang hiện: {so_cu:,}" if so_cu >= 0 else "📒 Không đọc được sổ cũ")
    if so_cu >= 0:
        print(f"📉 LỆCH: {so_cu - tong:+,} — phần dôi ra là video đã render lại / đã bỏ thùng rác.")
    print(f"🔗 Khớp job: {len(da_khop):,} · mồ côi (có file, không job): {len(mo_coi):,} "
          f"· job trỏ vào file đã mất: {len(mat_job):,}")
    print("\n📊 Theo kênh (top 10)")
    for ten, o in sorted(theo_kenh.items(), key=lambda kv: -(kv[1]["l"] + kv[1]["s"]))[:10]:
        print(f"   {ten:<16} long {o['l']:>3} · short {o['s']:>3}")

    if not a.ghi:
        print("\n(chạy thử — thêm --ghi để ghi đè sổ bằng SỐ THẬT + dọn job trỏ vào file đã mất)")
        return 0

    now = datetime.now(timezone.utc).isoformat()
    db = FB._db_B_that() or FB._db_jobs()          # sổ LUÔN ghi vào B (xem count_pushed)
    db.collection("render_stats").document(a.owner).set({**{k: dict(v) for k, v in theo_kenh.items()},
                                                         "at": now})
    db.collection("render_stats").document(f"__pushed__{a.owner}").set(
        {"total": tong, "at": now, "kho_at": now,
         **{f"ch_{k}": v["l"] + v["s"] for k, v in theo_kenh.items()},
         **{k: v for k, v in theo_ngay.items() if k}})
    n = 0
    for jid, _ch, _ty in mat_job:
        try:
            db.collection("render_jobs").document(jid).delete()
            n += 1
        except Exception:
            pass
    print(f"\n✅ Sổ = {tong:,} video THẬT trong kho (trước ghi: {so_cu:,}). "
          f"Đã dọn {n} bản ghi job trỏ vào file không còn tồn tại.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
