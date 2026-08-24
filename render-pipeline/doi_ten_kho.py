#!/usr/bin/env python3
"""ĐỔI TÊN VIDEO CŨ TRÊN DRIVE VỀ QUY ƯỚC CHUẨN — TỰ ĐỘNG A-Z (24/8/2026).

Anh: *"e làm tự động a-z cho a nha, a biết gì đâu mà duyệt"*. Nên công cụ này tự quyết mọi thứ,
KHÔNG bắt người dùng đọc bảng tên. Đổi lại nó phải tự lo được ba chỗ dễ hỏng dưới đây.

BA CHỖ DỄ HỎNG (và cách xử)
---------------------------
1. **Đổi tên video là đứt liên kết với ảnh bìa / phụ đề.** Khâu đăng tìm ảnh bìa **theo TÊN**
   (`drv.find_file(parent_id, sidecar["thumbnail"])`). Nên mỗi video phải đổi tên CẢ CHÙM
   `.mp4 + .jpg + .json (+ .vtt/.srt)` và **sửa luôn nội dung** `thumbnail`/`captions` bên trong
   sidecar. Thứ tự dưới đây chọn để lúc nào hỏng giữa chừng cũng còn cứu được, không mất video.
2. **Video đã xếp hàng đăng giữ BẢN SAO của tên cũ.** `yt_queue`/`videos` chép sẵn `drive_name`,
   `thumbnail`, `captions` lúc quét kho. Sửa file mà quên sửa hàng chờ thì tới lượt đăng nó tìm
   ảnh bìa theo tên cũ -> không thấy -> đăng thiếu ảnh. Nên bước cuối cập nhật cả hàng chờ.
   Item đang `processing` (đang đăng ngay lúc này) thì **BỎ QUA** — không đụng vào việc đang chạy.
3. **Ô SERI của video cũ không dựng lại được.** `cha`/`thu_tu` (short thuộc long nào) mới có từ
   24/8; job cũ không có. Bịa một mã cho đủ ô là tệ hơn bỏ trống, vì mã bịa trông y như mã thật mà
   lại nhóm sai. Video nào không truy ra chùm thì **bỏ hẳn ô SERI** (tên 4 đoạn) — `ten_chuan.doc_vai`
   dò ô vai trò chứ không lấy theo vị trí nên đọc được cả hai dạng.

    python doi_ten_kho.py            # chạy thử: in ra từng cặp tên cũ -> mới
    python doi_ten_kho.py --that     # đổi thật
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict

from ten_chuan import da_chuan, ten_file

PHU = (".jpg", ".jpeg", ".png", ".json", ".vtt", ".srt", ".txt")


def _goc(ten: str) -> tuple[str, str]:
    for x in (".mp4",) + PHU:
        if ten.lower().endswith(x):
            return ten[: -len(x)], ten[-len(x):]
    return ten, ""


def _quet(drv, folder_id, sau=0, ra=None):
    ra = [] if ra is None else ra
    if sau > 4:
        return ra
    tok = None
    while True:
        r = drv.svc.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id,name,mimeType,createdTime,parents)",
            pageSize=1000, pageToken=tok,
            supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        for f in r.get("files", []):
            if f.get("mimeType") == "application/vnd.google-apps.folder":
                _quet(drv, f["id"], sau + 1, ra)
            else:
                f["_thumuc"] = folder_id
                ra.append(f)
        tok = r.get("nextPageToken")
        if not tok:
            break
    return ra


def _sua_sidecar(drv, fid: str, goc_moi: str) -> None:
    """Sửa `thumbnail`/`captions` bên trong sidecar cho trỏ đúng tên mới.

    `DriveClient` chỉ có `download(file_id, dest_path)` và `upload_file(folder, path)` — không có
    lối đọc/ghi thẳng theo bytes. Nên đi qua file tạm rồi `files().update(media_body=…)`, tức GHI ĐÈ
    đúng file cũ (giữ nguyên id) chứ không tạo file mới; tạo file mới là kho có 2 sidecar, khâu đăng
    bốc nhầm cái nào cũng được."""
    import tempfile
    from googleapiclient.http import MediaFileUpload
    tam = os.path.join(tempfile.gettempdir(), f"sc_{fid}.json")
    try:
        drv.download(fid, tam)
        with open(tam, encoding="utf-8") as fh:
            sc = json.load(fh)
        for k in ("thumbnail", "captions"):
            v = sc.get(k)
            if isinstance(v, str) and v:
                sc[k] = goc_moi + _goc(v)[1]
            elif isinstance(v, dict) and v.get("file"):
                v["file"] = goc_moi + _goc(v["file"])[1]
        with open(tam, "w", encoding="utf-8") as fh:
            json.dump(sc, fh, ensure_ascii=False)
        drv.svc.files().update(fileId=fid,
                               media_body=MediaFileUpload(tam, mimetype="application/json"),
                               supportsAllDrives=True).execute()
    finally:
        try:
            os.remove(tam)
        except OSError:
            pass


def _doi(drv, fid, ten_moi):
    drv.svc.files().update(fileId=fid, body={"name": ten_moi}, supportsAllDrives=True).execute()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--that", action="store_true", help="đổi tên THẬT (mặc định chỉ in ra)")
    ap.add_argument("--gioi-han", type=int, default=0, help="chỉ xử lý N video (0 = tất cả)")
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

    # ── job: drive_id -> kênh/loại/chùm ──────────────────────────────────────────────────────
    job_cua: dict[str, dict] = {}
    try:
        q = (FB._db_jobs().collection("render_jobs")
             .where("owner", "==", a.owner).where("status", "==", "done"))
        for d in FB._stream_at(q, 90):
            x = d.to_dict() or {}
            if x.get("drive_id"):
                job_cua[x["drive_id"]] = {"id": d.id, "channel": str(x.get("channel") or ""),
                                          "type": x.get("type") or "", "cha": x.get("cha") or "",
                                          "thu_tu": int(x.get("thu_tu") or 0),
                                          "title": x.get("title") or ""}
    except Exception as e:
        print(f"⚠️ không đọc được render_jobs ({str(e)[:70]}) — vẫn đổi tên được, nhưng suy kênh/loại "
              f"từ tên file nên kém chính xác hơn.")

    _co_con = {v["cha"] for v in job_cua.values() if v.get("cha")}   # long nào có short trỏ về

    accs = ST.pool_accounts()
    if not accs:
        print("❌ không đọc được kho nào — dừng.")
        return 1

    ke = []          # (drv, nhóm file, tên gốc mới)
    bo_qua = {"đã chuẩn": 0, "không có mp4": 0}
    for acc in accs:
        try:
            drv = ST.account_drive(acc)
            fs = _quet(drv, acc.get("root"))
        except Exception as e:
            print(f"   ⚠️ {acc.get('name')}: đọc hụt ({str(e)[:60]}) — bỏ kho này, KHÔNG đổi bừa.")
            continue
        nhom: dict = defaultdict(dict)
        for f in fs:
            g, d = _goc(f["name"])
            nhom[(f["_thumuc"], g)][d.lower()] = f
        for (_tm, g), m in nhom.items():
            mp4 = m.get(".mp4")
            if not mp4:
                bo_qua["không có mp4"] += 1
                continue
            if da_chuan(mp4["name"]):
                bo_qua["đã chuẩn"] += 1
                continue
            j = job_cua.get(mp4["id"]) or {}
            kenh = (j.get("channel") or g.split("__")[0] or acc.get("name") or "MM0").upper()
            loai = j.get("type") or ("long" if "long" in g.lower() else "short")
            # SERI: chùm long+short. `cha` = job của long; long thì lấy chính id của nó.
            # SHORT: `cha` chính là mã chùm. LONG: dùng id của chính nó, NHƯNG chỉ khi có short
            # thật sự trỏ về — long lẻ mà gắn mã chùm thì mã đó chẳng nhóm với ai, chỉ tổ rối.
            seri = j.get("cha") or ""
            if not seri and loai == "long" and j.get("id") and j["id"] in _co_con:
                seri = j["id"]
            bo = "L" if loai == "long" else (f"S{j['thu_tu']}" if j.get("thu_tu") else "S")
            tieu_de = j.get("title") or g.split("__")[-1]
            ngay = str(mp4.get("createdTime") or "")[:10].replace("-", "") or None
            moi = ten_file(kenh, {"title": tieu_de}, loai, seri=seri, bo=bo, ngay=ngay)
            if moi == g:
                bo_qua["đã chuẩn"] += 1
                continue
            ke.append((drv, m, g, moi, mp4["id"]))

    print(f"📦 {len(ke)} video cần đổi tên · bỏ qua: "
          + " · ".join(f"{k} {v}" for k, v in bo_qua.items()))
    for _d, _m, cu, moi, _i in ke[:8]:
        print(f"   {cu[:58]}\n     -> {moi}")
    if len(ke) > 8:
        print(f"   … và {len(ke) - 8} cái nữa")
    if a.gioi_han:
        ke = ke[: a.gioi_han]

    if not a.that:
        print("\n(chạy thử — thêm --that để đổi tên thật)")
        return 0

    # ── đang đăng dở thì không đụng ──────────────────────────────────────────────────────────
    dang_chay: set[str] = set()
    hang_cho: dict[str, list[str]] = defaultdict(list)   # drive_file_id -> [doc id trong yt_queue]
    stt = None
    try:
        import firestore_state as FS
        stt = FS.State()
        for it in (stt.list_yt_queue() or []):
            fid_ = it.get("drive_file_id") or ""
            if not fid_:
                continue
            if it.get("status") == "processing":
                dang_chay.add(fid_)
            else:
                hang_cho[fid_].append(it["id"])
    except Exception as e:
        print(f"   ⚠️ không đọc được hàng chờ ({str(e)[:60]}) — DỪNG, vì đổi tên mà không sửa được "
              f"hàng chờ thì video tới lượt đăng sẽ mất ảnh bìa.")
        return 1

    xong, hong = 0, 0
    for drv, m, cu, moi, vid in ke:
        if vid in dang_chay:
            print(f"   ⏭ {cu[:44]}: ĐANG ĐĂNG — để lượt sau.")
            continue
        try:
            # Thứ tự có chủ ý: ảnh/phụ đề trước, rồi sửa RUỘT sidecar, rồi video, sidecar cuối.
            # Hỏng ở bất cứ đâu thì video vẫn còn nguyên và lần chạy sau sửa nốt được.
            for d in (".jpg", ".jpeg", ".png", ".vtt", ".srt", ".txt"):
                if d in m:
                    _doi(drv, m[d]["id"], moi + d)
            js = m.get(".json")
            if js:
                _sua_sidecar(drv, js["id"], moi)
            _doi(drv, m[".mp4"]["id"], moi + ".mp4")
            if js:
                _doi(drv, js["id"], moi + ".json")
            # Hàng chờ giữ BẢN SAO của tên cũ (chép lúc quét kho) -> không sửa thì tới lượt đăng nó
            # tìm ảnh bìa theo tên cũ, không thấy, đăng thiếu ảnh.
            if stt is not None:
                _da = next((d for d in (".jpg", ".jpeg", ".png") if d in m), "")
                _va = {"drive_name": moi + ".mp4"}
                if _da:
                    _va["thumbnail"] = moi + _da        # đuôi ảnh THẬT, đừng cứng .jpg
                if any(d in m for d in (".vtt", ".srt")):
                    _va["captions"] = moi + (".vtt" if ".vtt" in m else ".srt")
                try:
                    stt.upsert_video(vid, _va)
                    for _q in hang_cho.get(vid, []):
                        stt.update_yt_queue(_q, _va)
                except Exception as e:
                    print(f"   ⚠️ {moi[:40]}: file đã đổi tên nhưng CẬP NHẬT HÀNG CHỜ hụt "
                          f"({str(e)[:60]}) — chạy lại lượt sau để sửa nốt.")
            xong += 1
        except Exception as e:
            hong += 1
            print(f"   ⚠️ {cu[:44]}: đổi hụt ({str(e)[:70]})")

    print(f"\n✅ Đổi tên {xong} video (mỗi cái đủ chùm mp4+ảnh+sidecar) · hụt {hong}")
    return 0 if not hong else 1


if __name__ == "__main__":
    sys.exit(main())
