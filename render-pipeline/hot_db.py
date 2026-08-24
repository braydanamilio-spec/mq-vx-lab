#!/usr/bin/env python3
"""CLIENT D1 "mm0-hot" — kho NÓNG thay Firestore cho phần đọc/ghi nhiều (24/8/2026).

VÌ SAO
------
Firestore free: **50.000 đọc · 20.000 ghi** mỗi ngày. Đo thật đêm 24/8: project B chạm >50.000,
phải failover, kéo theo cả chuỗi sự cố. Cloudflare D1 free: **5.000.000 dòng đọc (100×) ·
100.000 dòng ghi (5×) · 5 GB**. Cùng tài khoản Cloudflare đã có Worker, không thêm nhà cung cấp.

Nói thẳng cái D1 **không** giải quyết: nó đếm **SỐ DÒNG ĐỌC**, nên truy vấn không trúng index mà
quét cả bảng vẫn tốn đúng bấy nhiêu dòng. Hết lo là nhờ 100× hạn mức **cộng với** index đúng, chứ
không phải cứ đổi kho là xong.

VÀO BẰNG MỘT CỬA
----------------
Mọi lời gọi đi qua `Worker /api/hot` với **danh sách lệnh có tên** — KHÔNG có SQL tự do, nên không
có đường nào để một lời gọi bịa ra câu lệnh phá bảng. Cần khoá `HOT_KEY`. Mỗi bảng có **đúng một
chủ ghi** — luật rút ra từ sự cố B/B2: nhiều nơi cùng ghi thì không phải "đồng bộ", đó là nhiều sự thật.

BA CHẾ ĐỘ (đổi bằng env `HOT_MODE`) — CHUYỂN DẦN, KHÔNG CẮT MÙ
--------------------------------------------------------------
* `off`    : không đụng D1. (mặc định khi chưa có HOT_URL/HOT_KEY)
* `shadow` : **ghi cả hai nơi, ĐỌC vẫn từ Firestore.** D1 hỏng cũng không ảnh hưởng gì.
             Đây là chế độ để chạy vài ngày và ĐỐI CHIẾU số trước khi tin.
* `on`     : đọc từ D1 cho các bảng nóng, Firestore giữ phần dashboard.

Mặc định là `shadow`. Không bao giờ tự nhảy sang `on` — phải đổi env có chủ ý.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

_URL = os.environ.get("HOT_URL", "https://mm0-connect.adisondurham-ef1.workers.dev/api/hot")
_KEY = os.environ.get("HOT_KEY", "")
_MODE = (os.environ.get("HOT_MODE") or ("shadow" if _KEY else "off")).lower()
_HONG = {"n": 0}          # đếm số lần gọi hụt -> hỏng nhiều thì tự tắt, không cản việc chính


def che_do() -> str:
    return _MODE


def bat_ghi() -> bool:
    """Có ghi sang D1 không (shadow hoặc on)."""
    return _MODE in ("shadow", "on") and bool(_KEY) and _HONG["n"] < 20


def bat_doc() -> bool:
    """Có ĐỌC từ D1 không — chỉ khi đã bật hẳn."""
    return _MODE == "on" and bool(_KEY) and _HONG["n"] < 20


def goi(lenh: str, tham: dict | None = None, timeout: int = 12) -> dict:
    """Gọi một lệnh CÓ TÊN. Lỗi thì trả {} và đếm — KHÔNG BAO GIỜ ném lên trên.

    Nguyên tắc: D1 là lớp phụ trong giai đoạn chuyển. Nó hỏng thì việc chính vẫn phải chạy bằng
    Firestore. Hỏng quá 20 lần thì tự tắt hẳn cho phiên này, khỏi trả giá timeout từng lệnh."""
    if not _KEY or _HONG["n"] >= 20:
        return {}
    try:
        req = urllib.request.Request(
            _URL, method="POST",
            data=json.dumps({"lenh": lenh, "tham": tham or {}}).encode("utf-8"),
            headers={"content-type": "application/json", "x-hot-key": _KEY,
                     # 24/8 — BẮT BUỘC: thiếu User-Agent thì Cloudflare chặn ngay ở cổng với
                     # mã 1010 ("browser signature"), trả 403 y như sai khoá nên rất dễ chẩn nhầm.
                     # Đúng cái bẫy đã dính với DVIDS sáng nay — lần này nhận ra trong 2 phút.
                     "user-agent": "MM0-Pipeline/1.0 (+github-actions)"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "ignore")) or {}
    except Exception as e:
        _HONG["n"] += 1
        if _HONG["n"] in (1, 20):
            print(f"   ⚠️ D1 hụt ({_HONG['n']} lần): {str(e)[:70]}"
                  + (" — TẮT D1 cho phiên này, chạy tiếp bằng Firestore." if _HONG["n"] >= 20 else ""))
        return {}


# ── các lệnh dùng trong pipeline (tên khớp với danh sách cho phép ở Worker) ──────────────────
# ── GỘP LỆNH GHI (24/8, anh đề xuất) ────────────────────────────────────────────────────────
# Có HAI trần khác nhau, phải nhìn cả hai:
#   • D1     : 100.000 DÒNG ghi/ngày
#   • Worker : 100.000 LƯỢT GỌI/ngày  <- chật hơn, vì mọi đường vào D1 đều qua đây
# Gộp KHÔNG làm giảm số DÒNG ghi vào D1 (vẫn ngần ấy dòng) — nó cứu trần WORKER.
# Đo thật 122 video/phiên × ~4 lượt ghi/job × 20 phiên:
#   không gộp   9.760 lượt gọi/ngày (9% trần Worker)
#   gộp 20      488 lượt gọi/ngày   (0,5%)   -> rẻ hơn 20 lần
# Xả khi ĐỦ 20 mục HOẶC quá 120 giây, cái nào tới trước — dashboard trễ nhiều nhất 2 phút,
# đủ trực quan mà không phải trả giá mỗi thao tác một vòng mạng 0,22s.
# TRẠNG THÁI CUỐI (done/failed) XẢ NGAY: đó là số người ta nhìn để biết có mất video không.
_DEM_BUF: list = []
_BUF_AT = [0.0]
BUF_MAX, BUF_GIAY = 20, 120


def _xa_buf(ep: bool = False) -> int:
    import time as _t
    if not _DEM_BUF:
        return 0
    if not ep and len(_DEM_BUF) < BUF_MAX and (_t.time() - _BUF_AT[0]) < BUF_GIAY:
        return 0
    lo = _DEM_BUF[:100]
    del _DEM_BUF[:len(lo)]
    _BUF_AT[0] = _t.time()
    owner = lo[0].pop("_owner", "")
    for x in lo:
        x.pop("_owner", None)
    goi("ghi_job_loat", {"owner": owner, "jobs": lo})
    return len(lo)


def ghi_job(owner, jid, channel, vtype, status, step="", title=None, drive_id=None,
            queued=False, at="") -> None:
    if not bat_ghi():
        return
    import time as _t
    if not _BUF_AT[0]:
        _BUF_AT[0] = _t.time()
    _DEM_BUF.append({"_owner": owner, "id": jid, "channel": channel, "vtype": vtype,
                     "status": status, "step": step, "title": title, "drive_id": drive_id,
                     "queued": bool(queued), "at": at})
    _xa_buf(ep=status in ("done", "failed"))     # kết quả cuối thì xả ngay, khỏi chờ


def xa_het() -> int:
    """Xả nốt phần còn trong bộ đệm. Gọi cuối luồng — thiếu bước này là MẤT các lượt ghi cuối."""
    n = 0
    while _DEM_BUF:
        m = _xa_buf(ep=True)
        if not m:
            break
        n += m
    return n


_DEM = {"at": 0.0, "map": None}


def nap_dem(owner: str, tuoi: int = 90) -> dict | None:
    """Lấy số video đã xong của TẤT CẢ kênh trong MỘT lời gọi, đệm 90 giây.

    Vì sao phải gộp: đo thật 24/8 — mỗi lời gọi Worker mất ~0,22s (D1 ở vùng APAC, runner GitHub ở
    Mỹ). Bước plan cần ~110 số đếm; gọi lẻ là **~33 giây chỉ để đếm**, chậm hơn cả Firestore.
    Và Worker free chỉ 100.000 lượt/ngày — gọi lẻ thì 30 phiên/ngày là vỡ trần Worker (111%) dù D1
    mới dùng vài phần trăm. **Trần thật nằm ở Worker, không phải D1.**
    Một lệnh GROUP BY: đo được 0,20s cho toàn bộ."""
    import time as _t
    if not bat_doc():
        return None
    if _DEM["map"] is not None and (_t.time() - _DEM["at"]) < tuoi:
        return _DEM["map"]
    r = goi("dem_tat_ca", {"owner": owner})
    if "rows" not in r:
        return None
    m = {}
    for x in (r.get("rows") or []):
        m[f'{x.get("channel","")}|{x.get("vtype","")}'] = int(x.get("n") or 0)
    _DEM["at"], _DEM["map"] = _t.time(), m
    return m


def dem_xong(owner, channel, vtype) -> int | None:
    """Số video đã xong CÓ FILE của 1 kênh. Trả None khi chưa bật đọc -> caller dùng Firestore."""
    m = nap_dem(owner)
    if m is None:
        return None
    ch = str(channel or "").upper()
    if vtype:
        return int(m.get(f"{ch}|{vtype}", m.get(f"{channel}|{vtype}", 0)))
    return int(sum(v for k, v in m.items() if k.split("|")[0] in (ch, channel)))


def key_nghi_ghi(kid: str, loai: str, den_iso: str) -> None:
    if not bat_ghi():
        return
    goi("key_nghi_ghi", {"kid": kid, "loai": loai, "den": den_iso})


def key_nghi_doc(gio_iso: str) -> list:
    if not bat_doc():
        return []
    return (goi("key_nghi_doc", {"gio": gio_iso}) or {}).get("rows") or []


def ton_kho(owner: str) -> dict:
    """Tồn kho CHƯA ĐĂNG theo từng kênh. {} nếu chưa bật D1."""
    if not (bat_ghi() or bat_doc()):
        return {}
    r = goi("ton_kho", {"owner": owner})
    return {str(x.get("channel") or ""): int(x.get("ton") or 0) for x in (r.get("rows") or [])}


def suc_dang_ngay() -> int:
    """Tổng số video CÒN ĐĂNG ĐƯỢC hôm nay, cộng qua mọi dự án YouTube đang bật."""
    if not (bat_ghi() or bat_doc()):
        return -1
    import datetime as _d
    ngay = (_d.datetime.now(_d.timezone.utc) - _d.timedelta(hours=7)).date().isoformat()
    r = goi("yt_con_cho", {"ngay": ngay})
    return int(r.get("con", -1)) if "con" in r else -1


def don_job_ma(owner: str, gio: int = 6) -> int:
    """Đổi job "đang chạy" đã im quá `gio` tiếng thành failed. Trả số bản ghi đã đổi.

    24/8 — đo được 75 bản ghi kẹt ở rendering/writing/qc, cái mới nhất cũng đã im 11 TIẾNG.
    Chúng NÓI DỐI về trạng thái: ô "đang chạy" trên web sai, và người nhìn không biết tin số nào.
    Ngưỡng 6 giờ an toàn vì một phiên dài nhất bị GitHub cắt ở 165 phút.
    KHÔNG xoá — chỉ thôi nói dối, vẫn giữ để soi nguyên nhân."""
    if not bat_ghi():
        return 0
    import datetime as _d
    moc = (_d.datetime.now(_d.timezone.utc) - _d.timedelta(hours=gio)).isoformat()
    r = goi("don_job_ma", {"owner": owner, "moc": moc})
    n = int(r.get("doi") or 0)
    if n:
        print(f"   🧹 dọn {n} job ma (im quá {gio}h -> đánh dấu failed, không xoá)")
    return n


def ngan_sach_cong(ngay: str, doc: int = 0, ghi: int = 0) -> None:
    if not bat_ghi():
        return
    goi("ngan_sach_cong", {"ngay": ngay, "doc": int(doc), "ghi": int(ghi)})


def ngan_sach_doc(ngay: str) -> dict:
    if not (bat_ghi() or bat_doc()):
        return {}
    return goi("ngan_sach_doc", {"ngay": ngay}) or {}


def bao_cao() -> str:
    return (f"🔥 D1 mm0-hot: chế độ {_MODE}"
            + (f" · còn {len(_DEM_BUF)} mục chờ xả" if _DEM_BUF else "")
            + (f" · {_HONG['n']} lần hụt" if _HONG["n"] else ""))
