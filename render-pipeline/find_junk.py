#!/usr/bin/env python3
"""SOI FILE RÁC TRONG KHO — MẶC ĐỊNH CHỈ ĐẾM, KHÔNG XOÁ (24/8/2026).

VÌ SAO KHÔNG DÙNG `wipe_queue.py`
---------------------------------
`wipe_queue.py` xoá SẠCH mọi thứ trong kho — đúng cho lúc làm lại từ đầu, SAI cho lúc này vì yêu cầu
là "giữ lại video hoàn hảo, chỉ dọn rác". Công cụ này nhận diện rác theo TỪNG LOẠI có bằng chứng rõ,
và mặc định **không đụng vào gì cả**.

NĂM LOẠI RÁC, và bằng chứng để gọi là rác
-----------------------------------------
1. **File tạm** — tên chứa `.new.` hoặc kết thúc `.tmp` / `.part`. Sinh ra khi thay thumbnail hỏng
   giữa chừng. Không có đường nào dùng tới.
2. **Trùng tên y hệt** trong CÙNG thư mục — Drive cho phép; lúc đăng, `find_file` lấy đại một cái nên
   có thể lấy nhầm bản cũ. Giữ bản MỚI NHẤT, phần còn lại là rác.
3. **Ảnh/sidecar mồ côi** — `.jpg` / `.json` mà KHÔNG có `.mp4` cùng tên gốc. Video đã bị xoá/thay,
   phần phụ còn sót lại.
4. **Video 0 byte hoặc quá nhỏ** (< 300KB) — render hỏng giữa chừng, chắc chắn không xem được.
5. **Video thiếu phần phụ** — có `.mp4` nhưng THIẾU cả `.json` lẫn `.jpg`: không đăng được (không có
   tiêu đề/mô tả/ảnh bìa). ĐÂY LÀ LOẠI **KHÔNG XOÁ** — chỉ liệt kê để dựng lại phần phụ, vì bản thân
   video có thể vẫn tốt.

AN TOÀN
-------
* Mặc định `--dry-run`: chỉ đếm và in ví dụ.
* Xoá là **BỎ VÀO THÙNG RÁC** (`trashed=True`), KHÔNG xoá vĩnh viễn — sai thì còn khôi phục được.
  Việc đổ thùng rác (xoá vĩnh viễn) cố ý KHÔNG nằm trong công cụ này.
* Không bao giờ đụng tới `.mp4` có đủ `.json` + `.jpg` — đó là video hoàn hảo.
* Đọc danh sách kho qua `pool_accounts()` (đi gương ở B) nên **không tốn hạn mức đọc của project A**.

    python find_junk.py                 # soi, in báo cáo
    python find_junk.py --don           # bỏ rác vào thùng rác (loại 1-4, KHÔNG đụng loại 5)
    python find_junk.py --don --loai 1,2
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict

NHO_NHAT = 300 * 1024          # video dưới mức này chắc chắn hỏng
TAM = re.compile(r"\.new\.|\.tmp$|\.part$", re.I)


def _goc(ten: str) -> str:
    """Tên gốc bỏ phần mở rộng: 'KENH__tieu-de.mp4' -> 'KENH__tieu-de'."""
    for x in (".mp4", ".jpg", ".jpeg", ".png", ".json", ".txt"):
        if ten.lower().endswith(x):
            return ten[: -len(x)]
    return ten


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--don", action="store_true", help="bỏ rác vào THÙNG RÁC (không xoá vĩnh viễn)")
    ap.add_argument("--loai", default="1,2,3,4", help="loại rác cần dọn (mặc định 1,2,3,4 — loại 5 không bao giờ xoá)")
    ap.add_argument("--gioi-han-kho", type=int, default=0, help="chỉ soi N kho đầu (0 = tất cả)")
    a = ap.parse_args()
    lam = {x.strip() for x in a.loai.split(",") if x.strip()} & {"1", "2", "3", "4"}

    src = os.environ.get("AUTOPUBLISHER_SRC")
    if src and src not in sys.path:
        sys.path.insert(0, src)
    import storage as ST

    accs = ST.pool_accounts()
    if not accs:
        print("❌ không đọc được kho nào — dừng (KHÔNG dám kết luận 'kho rỗng').")
        return 1
    if a.gioi_han_kho:
        accs = accs[: a.gioi_han_kho]
    print(f"🔎 Soi {len(accs)} kho Drive · chế độ: {'DỌN (vào thùng rác)' if a.don else 'CHỈ ĐẾM'}")

    dem = defaultdict(int)
    vi_du = defaultdict(list)
    can_xoa = []          # (drv, file_id, loại, tên)
    thieu_phu = []
    # 24/8 — chạy khô bắt được: một file vừa là "file tạm" vừa là "ảnh mồ côi" -> bị đếm HAI lần và
    # nằm hai lần trong danh sách xoá. Số báo cáo sai thì người dùng mất niềm tin vào công cụ, mà
    # công cụ dọn file thì niềm tin là tất cả. Mỗi file chỉ được xếp vào ĐÚNG MỘT loại (loại nhỏ
    # nhất thắng), và danh sách xoá lọc trùng theo id.
    da_xep = set()

    def _xep(drv, f, loai, nhan=None):
        if f["id"] in da_xep:
            return False
        da_xep.add(f["id"])
        dem[loai] += 1
        can_xoa.append((drv, f["id"], loai, nhan or f["name"]))
        if len(vi_du[loai]) < 3:
            vi_du[loai].append(nhan or f["name"])
        return True

    def _quet(drv, folder_id, sau=0, ra=None):
        """Đi ĐỆ QUY mọi thư mục con, giữ lại thư mục cha của từng file.

        24/8 — bản đầu của hàm này SAI hai chỗ, suýt thành đúng cái lỗi "chết câm" vừa ghi luật:
          • đi theo đường `root/MM0-STORE/_QUEUE`, trong khi `_QUEUE` là con TRỰC TIẾP của root
            (xem `wipe_queue.py`) -> soi vào thư mục trống, báo "0 rác" mà tưởng kho sạch;
          • gọi `child_folder()` thiếu `create=False` — hàm này MẶC ĐỊNH TẠO thư mục, tức công cụ
            chỉ-đọc lại đi tạo thư mục rỗng trong kho người dùng.
        Nay quét thẳng từ root và chỉ đọc."""
        ra = [] if ra is None else ra
        if sau > 4:
            return ra
        tok = None
        while True:
            r = drv.svc.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id,name,size,mimeType,createdTime)",
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

    for acc in accs:
        try:
            drv = ST.account_drive(acc)
        except Exception as e:
            print(f"   ⚠️ {acc.get('name')}: mở kho hụt ({str(e)[:60]})")
            continue
        try:
            fs = _quet(drv, acc.get("root"))
        except Exception as e:
            print(f"   ⚠️ {acc.get('name')}: quét hụt ({str(e)[:60]})")
            continue

        theo_goc = defaultdict(dict)      # (thư mục, gốc) -> {đuôi: file}
        theo_ten = defaultdict(list)      # (thư mục, tên) -> [file]  — trùng tên CÙNG thư mục
        for f in fs:
            ten = f["name"]; tm = f["_thumuc"]
            theo_ten[(tm, ten)].append(f)
            theo_goc[(tm, _goc(ten))][os.path.splitext(ten)[1].lower()] = f

        # loại 1: file tạm
        for f in fs:
            if TAM.search(f["name"]):
                _xep(drv, f, "1")
        # loại 2: trùng tên y hệt trong CÙNG thư mục -> giữ bản mới nhất
        for (_tm, ten), ds in theo_ten.items():
            if len(ds) < 2:
                continue
            ds.sort(key=lambda x: str(x.get("createdTime") or ""), reverse=True)
            for f in ds[1:]:
                _xep(drv, f, "2", f"{ten} (bỏ {len(ds)-1} bản cũ)")
        # loại 3/4/5
        for (_tm, goc), m in theo_goc.items():
            mp4 = m.get(".mp4")
            phu = [m[k] for k in (".jpg", ".jpeg", ".png", ".json", ".txt") if k in m]
            if not mp4:
                for f in phu:
                    _xep(drv, f, "3")
                continue
            try:
                co = int(mp4.get("size") or 0)
            except Exception:
                co = 0
            if co and co < NHO_NHAT:
                _xep(drv, mp4, "4", f"{mp4['name']} ({co/1024:.0f}KB)")
                continue
            if mp4["id"] not in da_xep and not (".json" in m or any(k in m for k in (".jpg", ".jpeg", ".png"))):
                dem["5"] += 1; thieu_phu.append((acc.get("name"), mp4["name"]))
                if len(vi_du["5"]) < 3: vi_du["5"].append(f"{acc.get('name')}/{mp4['name']}")

    ten_loai = {"1": "file tạm (.new./.tmp/.part)", "2": "trùng tên y hệt (giữ bản mới nhất)",
                "3": "ảnh/sidecar mồ côi (không có .mp4)", "4": "video hỏng (<300KB)",
                "5": "video THIẾU phần phụ — KHÔNG xoá, chỉ dựng lại phần phụ"}
    print("\n📊 KẾT QUẢ")
    for k in ("1", "2", "3", "4", "5"):
        print(f"   loại {k}: {dem[k]:>5}  — {ten_loai[k]}")
        for v in vi_du[k]:
            print(f"            vd: {v}")
    tong_xoa = sum(dem[k] for k in lam)
    print(f"\n🗑  Có thể bỏ vào thùng rác: {tong_xoa} file (loại {','.join(sorted(lam))})")
    print(f"🛟 KHÔNG đụng tới: mọi .mp4 có đủ .json + .jpg, và {dem['5']} video loại 5.")

    if not a.don:
        print("\n(chạy thử — thêm --don để bỏ vào thùng rác; xoá vĩnh viễn KHÔNG nằm trong công cụ này)")
        return 0

    n = 0
    for drv, fid, loai, ten in can_xoa:
        if loai not in lam:
            continue
        try:
            drv.svc.files().update(fileId=fid, body={"trashed": True}).execute()
            n += 1
        except Exception as e:
            print(f"   ⚠️ bỏ rác hụt {ten}: {str(e)[:60]}")
    print(f"\n✅ Đã bỏ {n} file vào THÙNG RÁC (còn khôi phục được). "
          f"Muốn thu hồi dung lượng thì đổ thùng rác trên dashboard.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
