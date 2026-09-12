"""
trend_kho.py — KHO TƯ LIỆU VIDEO TRENDING (nghiên cứu) từ YouTube / TikTok / Facebook / Instagram (USA).

MỤC ĐÍCH: gom video đang hot ở Mỹ về làm kho tham khảo nghiên cứu gu/xu hướng — KHÔNG đăng lại,
KHÔNG copy nội dung. Hai tầng, cố ý tách nhau:

  · TẦNG DUYỆT  (metadata + link + thumbnail URL) — cron `--collect` lấy MỌI video trending, ghi
    Firestore. NHẸ, KHÔNG tốn Drive (thumbnail để nguyên URL gốc, dashboard hiện thẳng).
  · TẦNG FILE   (tải .mp4) — chỉ tải khi:
        (a) anh tích chọn trên dashboard  -> ghi `trending_req` -> `--serve-requests` tải,
        (b) hoặc auto tải TOP-N mỗi nền tảng theo `trending_config` (mặc định 0 = tắt).
    File tải bằng yt-dlp (free, open-source) về kho Drive pool.

Vì sao hybrid: kho đầy đủ để duyệt mà dung lượng Drive chỉ tốn cho thứ anh THẬT SỰ cần xem offline.

100% FREE trên GitHub Actions (repo PUBLIC): yt-dlp free; YouTube trending qua Data API v3 (key free
của anh, hạn mức 10k/ngày — 1 lượt collect tốn ~1 unit). KHÔNG mở account/dịch vụ trả phí nào.

Nền tảng — thực tế kỹ thuật (xem `_adapter`):
  · YouTube  : API CHÍNH THỨC `videos.list?chart=mostPopular&regionCode=US` -> sạch, ổn định.
  · TikTok/FB/IG : chưa có API trending chính thức cho bên thứ ba -> adapter để TRỐNG (pilot),
    nhân ra sau bằng cách điền đúng một hàm `*_trending()`. Khung (DB·cron·dashboard·tải) dùng chung.

Chạy:
    python trend_kho.py --collect            # cron: gom metadata + auto tải top-N
    python trend_kho.py --serve-requests     # thực thi yêu cầu tải tay từ dashboard
    python trend_kho.py --collect --serve-requests
    python trend_kho.py --collect --dry-run  # chỉ in, KHÔNG ghi Firestore/không tải

Cron: .github/workflows/trend_kho.yml
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firestore_bridge as FB

OWNER = os.environ.get("OWNER_UID") or ""
REGION = "US"
PLATFORMS = ["yt", "tiktok", "fb", "ig"]
TEN_NEN = {"yt": "YouTube", "tiktok": "TikTok", "fb": "Facebook", "ig": "Instagram"}

COL_KHO = "trending_kho"       # 1 doc / video:  id = "<plat>_<video_id>"
COL_REQ = "trending_req"       # 1 doc / yêu cầu tải tay từ dashboard
COL_CFG = "trending_config"    # 1 doc / owner: bật-tắt + auto top-N từng nền tảng

# yt-dlp: research kho -> 720p đủ, chặn file khổng lồ (bản scan/gốc) làm ngập Drive.
DL_FORMAT = "bv*[height<=720]+ba/b[height<=720]/b"
DL_MAX = "500M"
CFG_MAC_DINH = {p: {"on": (p == "yt"), "auto_dl_top_n": 0, "max_keep": 60} for p in PLATFORMS}


# ─────────────────────────── Firestore (shard B qua FB._db_meta) ───────────────────────────
def _db():
    """Project A (mm0-auto-publisher) — nơi dashboard client ĐÃ ĐĂNG NHẬP đọc + ghi được.
    KHÔNG dùng shard B: user chỉ auth trên Project A (getAuth(appFb)), không auth trên shard B,
    nên client KHÔNG ghi được trending_config/trending_req lên B (Missing permissions). Trending là
    dữ liệu nhỏ, để ở A cùng chỗ tasks/social_queue là đúng — collector ghi qua Admin (bỏ qua rules)."""
    return FB._db()


def doc_id(plat: str, vid: str) -> str:
    return f"{plat}_{re.sub(r'[^A-Za-z0-9_-]', '', str(vid))[:80]}"


def nap_config() -> dict:
    """Đọc trending_config của owner; thiếu trường nào lấp bằng mặc định (không ghi đè ý anh)."""
    cfg = {p: dict(CFG_MAC_DINH[p]) for p in PLATFORMS}
    if not OWNER:
        return cfg
    try:
        d = _db().collection(COL_CFG).document(OWNER).get(timeout=15)
        if d.exists:
            data = d.to_dict() or {}
            for p in PLATFORMS:
                if isinstance(data.get(p), dict):
                    cfg[p].update({k: v for k, v in data[p].items() if k in cfg[p]})
    except Exception as e:
        print(f"   ⚠️ đọc trending_config lỗi ({str(e)[:120]}) — dùng mặc định")
    return cfg


def upsert_meta(rows: list[dict], dry: bool) -> int:
    """Ghi metadata (merge) — GIỮ nguyên trạng thái tải (downloaded/drive_id) nếu doc đã có.

    §15.2: trả về SỐ ĐẾM thật để câu log luôn có mẫu số, không có 0 vô nghĩa."""
    if not rows:
        return 0
    if dry:
        for r in rows[:5]:
            print(f"      · [{r['platform']}] {r.get('views',0):>10,} view · {r['title'][:70]}")
        if len(rows) > 5:
            print(f"      · … +{len(rows)-5} video nữa")
        return len(rows)
    db = _db()
    n = 0
    for r in rows:
        # §13.7 ngân sách dùng chung: dừng ghi metadata (việc phụ) ở 70% trần, chừa cho render.
        if not FB.con_ngan_sach("ghi"):
            print(f"      ⚠️ hạn mức GHI đã tới ngưỡng phụ (70%) — dừng ở {n}/{len(rows)}")
            break
        rid = doc_id(r["platform"], r["video_id"])
        r2 = dict(r, owner=OWNER, collected_at=int(time.time()))
        try:
            db.collection(COL_KHO).document(rid).set(r2, merge=True)
            n += 1
        except Exception as e:
            print(f"      ⚠️ ghi {rid} lỗi: {str(e)[:100]}")
    return n


# ─────────────────────────── Adapter từng nền tảng ───────────────────────────
def _iso_giay(s: str) -> int:
    """ISO8601 PT#H#M#S -> giây (YouTube contentDetails.duration)."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    if not m:
        return 0
    h, mi, se = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + se


def yt_trending(n: int = 50) -> list[dict]:
    """YouTube USA — API CHÍNH THỨC `videos.list?chart=mostPopular`. Cần YT_DATA_KEY (free).

    Thiếu key thì NÓI RÕ và trả [] (không giả vờ 0 — §15.2), không rơi về đường scrape kém tin."""
    key = os.environ.get("YT_DATA_KEY") or os.environ.get("YOUTUBE_API_KEY") or ""
    if not key:
        print("   ⏭  YouTube: CHƯA có YT_DATA_KEY (secret) — bỏ qua. "
              "Lấy key free ở console.cloud.google.com > YouTube Data API v3.")
        return []
    url = ("https://www.googleapis.com/youtube/v3/videos"
           "?part=snippet,statistics,contentDetails&chart=mostPopular"
           f"&regionCode={REGION}&maxResults={min(n,50)}&key={key}")
    try:
        with urllib.request.urlopen(url, timeout=25) as r:
            raw = r.read()
    except Exception as e:
        # 403 quotaExceeded / keyInvalid đều rơi vào đây — in nguyên do, đừng nuốt (§15.2).
        print(f"   ❌ YouTube API lỗi: {str(e)[:180]}")
        return []
    if not raw[:1] == b"{":
        print(f"   ❌ YouTube API trả không phải JSON (bị chặn?): {raw[:120]!r}")
        return []
    data = json.loads(raw)
    if "error" in data:
        print(f"   ❌ YouTube API: {json.dumps(data['error'])[:200]}")
        return []
    out = []
    for it in data.get("items", []):
        sn, st, cd = it.get("snippet", {}), it.get("statistics", {}), it.get("contentDetails", {})
        th = sn.get("thumbnails", {})
        thumb = (th.get("high") or th.get("medium") or th.get("default") or {}).get("url", "")
        out.append({
            "platform": "yt", "video_id": it["id"],
            "url": f"https://www.youtube.com/watch?v={it['id']}",
            "title": sn.get("title", ""), "channel": sn.get("channelTitle", ""),
            "thumb": thumb, "published_at": sn.get("publishedAt", ""),
            "views": int(st.get("viewCount", 0) or 0), "likes": int(st.get("likeCount", 0) or 0),
            "duration_s": _iso_giay(cd.get("duration", "")), "region": REGION,
            "downloaded": False,
        })
    return out


def tiktok_trending(n: int = 50) -> list[dict]:
    """TikTok USA — CHƯA làm (pilot). Nhân ra: điền hàm này trả về list cùng SCHEMA như yt_trending.
    Không có API trending chính thức cho bên thứ ba; hướng khả thi: TikTok Research API (cần duyệt)
    hoặc endpoint không chính thức. Trả [] để khung vẫn chạy, KHÔNG giả vờ có dữ liệu."""
    return []


def fb_trending(n: int = 50) -> list[dict]:
    """Facebook USA — CHƯA làm (pilot). Meta Graph API chỉ cho nội dung của chính mình; trending
    phải scrape (dễ gãy). Nhân ra sau."""
    return []


def ig_trending(n: int = 50) -> list[dict]:
    """Instagram USA — CHƯA làm (pilot). Như Facebook."""
    return []


_ADAPTER = {"yt": yt_trending, "tiktok": tiktok_trending, "fb": fb_trending, "ig": ig_trending}


# ─────────────────────────── Tải file (yt-dlp -> Drive kho) ───────────────────────────
_KHO = {"drive": None, "folders": {}}   # cache 1 lượt chạy


def _kho_drive():
    """Một Drive pool account cho kho nghiên cứu. None nếu chưa có pool (khi đó chỉ gom metadata)."""
    if _KHO["drive"] is not None:
        return _KHO["drive"], _KHO.get("root")
    try:
        _ap = os.environ.get("AUTOPUBLISHER_SRC") or "/tmp/_autopublisher/src"
        for p in (_ap, "../_autopublisher/src", "_autopublisher/src"):
            if os.path.isdir(p):
                sys.path.insert(0, p)
                break
        import storage as ST
        accs = ST.pool_accounts()
        if not accs:
            print("   ⏭  chưa có Drive pool account — chỉ gom metadata, KHÔNG tải file.")
            _KHO["drive"] = False
            return None, None
        acc = accs[0]
        _KHO["drive"] = ST.account_drive(acc)
        _KHO["root"] = acc["root"]
        return _KHO["drive"], _KHO["root"]
    except Exception as e:
        print(f"   ⏭  không mở được Drive kho ({str(e)[:120]}) — chỉ gom metadata.")
        _KHO["drive"] = False
        return None, None


def _folder_cho(plat: str):
    """Folder MM0_TRENDING/<PLAT> trên Drive kho (tạo nếu chưa có)."""
    drive, root = _kho_drive()
    if not drive:
        return None
    if plat in _KHO["folders"]:
        return _KHO["folders"][plat]
    base = drive.child_folder(root, "MM0_TRENDING", create=True)
    fid = drive.child_folder(base, TEN_NEN[plat].upper(), create=True) if base else None
    _KHO["folders"][plat] = fid
    return fid


def tai_mot(row: dict) -> dict | None:
    """yt-dlp tải 1 video (<=720p, <=500M) -> upload Drive kho. Trả {drive_id,size_mb} hoặc None."""
    plat, vid, url = row["platform"], row["video_id"], row.get("url", "")
    if not url:
        return None
    fid = _folder_cho(plat)
    if not fid:
        return None
    tmp = os.path.join(os.environ.get("TMPDIR") or "/tmp", f"trend_{doc_id(plat,vid)}")
    out_tmpl = tmp + ".%(ext)s"
    try:
        r = subprocess.run(
            ["yt-dlp", "--no-playlist", "--no-warnings", "-f", DL_FORMAT,
             "--max-filesize", DL_MAX, "--merge-output-format", "mp4",
             "-o", out_tmpl, url],
            capture_output=True, text=True, timeout=600)
    except FileNotFoundError:
        print("      ❌ chưa cài yt-dlp"); return None
    except Exception as e:
        print(f"      ⚠️ yt-dlp lỗi: {str(e)[:120]}"); return None
    got = None
    for ext in ("mp4", "mkv", "webm"):
        if os.path.exists(f"{tmp}.{ext}"):
            got = f"{tmp}.{ext}"; break
    if not got:
        print(f"      ⚠️ không tải được {plat}:{vid} ({(r.stderr or '')[:120]})"); return None
    size_mb = round(os.path.getsize(got) / 1e6, 1)
    drive, _ = _kho_drive()
    name = f"{doc_id(plat,vid)}.mp4"
    try:
        up = drive.upload_file(fid, got, name)
    except Exception as e:
        print(f"      ⚠️ upload Drive lỗi: {str(e)[:120]}"); os.remove(got); return None
    try:
        os.remove(got)
    except OSError:
        pass
    return {"drive_id": up.get("id", ""), "size_mb": size_mb}


def _danh_dau_tai(rows: list[dict], dry: bool) -> int:
    """Tải + cập nhật doc (downloaded/drive_id/size_mb). Bỏ qua doc đã tải rồi."""
    db = _db()
    n = 0
    for r in rows:
        if r.get("downloaded") and r.get("drive_id"):
            continue
        if dry:
            print(f"      · (dry) sẽ tải {r['platform']}:{r['video_id']} — {r['title'][:60]}")
            n += 1; continue
        res = tai_mot(r)
        if not res:
            continue
        try:
            db.collection(COL_KHO).document(doc_id(r["platform"], r["video_id"])).set(
                {"downloaded": True, **res, "downloaded_at": int(time.time())}, merge=True)
        except Exception as e:
            print(f"      ⚠️ ghi trạng thái tải lỗi: {str(e)[:100]}")
        print(f"      ⬇️  {r['platform']}:{r['video_id']} — {res['size_mb']}MB — {r['title'][:50]}")
        n += 1
    return n


# ─────────────────────────── Việc chính ───────────────────────────
def collect(dry: bool) -> None:
    cfg = nap_config()
    for plat in PLATFORMS:
        pc = cfg[plat]
        if not pc.get("on"):
            print(f"⏸  {TEN_NEN[plat]}: tắt trong config — bỏ qua.")
            continue
        print(f"🔎 {TEN_NEN[plat]} (USA) …")
        rows = _ADAPTER[plat](50)
        if not rows:
            print(f"   · 0 video (adapter chưa làm hoặc không lấy được).")
            continue
        n = upsert_meta(rows, dry)
        print(f"   ✅ {n}/{len(rows)} video vào kho (metadata).")
        top = int(pc.get("auto_dl_top_n", 0) or 0)
        if top > 0:
            print(f"   ⬇️  auto tải TOP {top} …")
            got = _danh_dau_tai(sorted(rows, key=lambda x: -x.get("views", 0))[:top], dry)
            print(f"   ✅ tải {got} file.")


def serve_requests(dry: bool) -> None:
    """Đọc yêu cầu tải TAY từ dashboard (trending_req pending) -> tải -> đánh dấu done."""
    if not OWNER:
        print("⚠️ thiếu OWNER_UID — bỏ qua serve-requests."); return
    db = _db()
    try:
        reqs = list(db.collection(COL_REQ)
                    .where("owner", "==", OWNER).where("status", "==", "pending")
                    .limit(50).stream(timeout=25))
    except Exception as e:
        print(f"⚠️ đọc trending_req lỗi: {str(e)[:140]}"); return
    if not reqs:
        print("· không có yêu cầu tải nào đang chờ."); return
    print(f"📥 {len(reqs)} yêu cầu tải …")
    for rq in reqs:
        rd = rq.to_dict() or {}
        ids = rd.get("video_ids") or []
        rows = []
        for full in ids:                       # full id = "<plat>_<vid>"
            d = db.collection(COL_KHO).document(full).get(timeout=15)
            if d.exists:
                rows.append(d.to_dict())
        got = _danh_dau_tai(rows, dry)
        if not dry:
            db.collection(COL_REQ).document(rq.id).set(
                {"status": "done", "done_at": int(time.time()), "tai_duoc": got}, merge=True)
        print(f"   ✅ yêu cầu {rq.id}: tải {got}/{len(ids)}.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--serve-requests", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not (a.collect or a.serve_requests):
        a.collect = True    # mặc định: gom
    print(f"=== trend_kho · owner={OWNER[:8] or '∅'} · {'DRY' if a.dry_run else 'THẬT'} ===")
    if a.collect:
        collect(a.dry_run)
    if a.serve_requests:
        serve_requests(a.dry_run)
    if not a.dry_run:
        print(FB.bao_ngan_sach())


if __name__ == "__main__":
    main()
