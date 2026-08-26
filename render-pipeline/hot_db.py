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

_URL = (os.environ.get('HOT_URL') or 'https://mm0-connect.adisondurham-ef1.workers.dev/api/hot')
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


_DA_GHI: set = set()        # job đã có ÍT NHẤT một dòng trong D1 (xem ghi_job)
_XA_MOI = [0.0]             # mốc lần xả sớm gần nhất — giữ nhịp, xem ghi_job


def ghi_job(owner, jid, channel, vtype, status, step="", title=None, drive_id=None,
            queued=False, at="", drive_account=None, thumb_id=None, size_mb=None, qc=None) -> None:
    """25/8 — thêm 4 trường phụ (kho chứa, thumbnail, dung lượng, điểm QC): video làm trong lúc
    Firestore nghẽn trước đây mất sạch các trường này (chỉ Firestore giữ) ⇒ thư viện hiện
    "kho chưa rõ"/"thiếu thumbnail" oan. COALESCE phía Worker nên None không đè giá trị cũ."""
    if not bat_ghi():
        return
    import time as _t
    if not _BUF_AT[0]:
        _BUF_AT[0] = _t.time()
    _DEM_BUF.append({"_owner": owner, "id": jid, "channel": channel, "vtype": vtype,
                     "status": status, "step": step, "title": title, "drive_id": drive_id,
                     "queued": bool(queued), "at": at, "drive_account": drive_account,
                     "thumb_id": thumb_id, "size_mb": size_mb, "qc": qc})
    # 25/8 — VÌ SAO Ô "⚙️ ĐANG CHẠY" LUÔN BẰNG 0. Soi D1 lúc 3 luồng đang render thật: bảng chỉ có
    # done/failed/ratelimited, KHÔNG có một dòng `running` nào. Bộ đệm chỉ xả sớm ở trạng thái CUỐI;
    # dòng trung gian nằm chờ trong đệm, tới lúc xả thì thường đã đi cùng lô với dòng `done` của
    # chính job đó và bị đè. Kết quả: D1 không bao giờ thấy job nào đang chạy — nên đọc "Đang chạy"
    # từ D1 cũng vẫn ra 0, chỉ là đổi chỗ sai chứ không hết sai.
    # Xả ngay lượt ghi ĐẦU TIÊN của mỗi job: đúng 1 lời gọi Worker thêm cho mỗi video (~400/ngày
    # trên trần 100.000 lượt Worker free), đổi lại ô "Đang chạy" nói thật.
    # Xả sớm CÓ NHỊP: bước plan dựng cả trăm job liền tay, xả từng cái là phá luôn việc gộp lô
    # (25 thao tác -> 25 lời gọi Worker). Tối đa 1 lượt xả sớm mỗi 25 giây: job đang chạy hiện lên
    # trong vòng nửa phút, mà lô vẫn gộp được.
    _moi = jid not in _DA_GHI
    if _moi:
        _DA_GHI.add(jid)
        if len(_DA_GHI) > 2000:
            _DA_GHI.clear()
    _som = _moi and (_t.time() - _XA_MOI[0]) >= 25
    if _som:
        _XA_MOI[0] = _t.time()
    _xa_buf(ep=_som or status in ("done", "failed"))


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
    """Tổng số video CÒN ĐĂNG ĐƯỢC hôm nay, cộng qua mọi dự án YouTube đang bật.

    Trả -1 = KHÔNG BIẾT (chưa bật D1, hoặc bảng `yt_project` chưa có dự án nào). Trả 0 = biết chắc
    đã hết lượt đăng hôm nay.

    24/8 tối — hai chuyện đó đang hiện CÙNG một con số. Log plan in `đăng được hôm nay: 0` trong khi
    sự thật là bảng dự án còn trống: Worker cộng `con` từ danh sách dự án, danh sách rỗng thì tổng
    tự nhiên bằng 0. Người đọc log hiểu thành "hết hạn mức đăng", còn thực tế là "chưa khai báo dự
    án nào". Cùng họ với luật 7.cg (không đo được thì đừng báo 0)."""
    if not (bat_ghi() or bat_doc()):
        return -1
    import datetime as _d
    ngay = (_d.datetime.now(_d.timezone.utc) - _d.timedelta(hours=7)).date().isoformat()
    r = goi("yt_con_cho", {"ngay": ngay}) or {}
    if "con" not in r:
        return -1
    if r.get("rows"):
        return int(r.get("con", -1))
    return _suc_suy_ra(ngay)


TRAN_MOI_DU_AN = 6          # 10.000 đơn vị/ngày ÷ 1.600 mỗi lần đăng


def _suc_suy_ra(ngay: str) -> int:
    """Suy sức đăng từ CHÍNH CÁC KÊNH ĐÃ KẾT NỐI, khi bảng `yt_project` còn trống (25/8/2026).

    Anh: *"a chỉ lấy api key youtube gắn vào chọn folder channel là chạy thôi"* — tức không muốn phải
    khai báo dự án bằng tay. Worker hiện KHÔNG có lệnh thêm dòng vào `yt_project`, mà thêm lệnh thì
    phải deploy lại Worker (máy này không có token Cloudflare).
    Đường không cần deploy: mỗi kênh YouTube nằm trên một tài khoản Google riêng ⇒ **mỗi kênh có hạn
    mức riêng 6 video/ngày**. Vậy sức đăng = (số kênh đã từng đăng được) × 6 − (đã đăng hôm nay).
    Lấy từ `yt_kenh_doi` + `yt_con_cho` — cả hai đều là lệnh CÓ SẴN.
    Trả -1 nếu chưa có kênh nào từng đăng (chưa có gì để suy)."""
    try:
        ow = os.environ.get("OWNER_UID", "")
        if not ow:
            return -1
        rows = (goi("yt_kenh_doi", {"owner": ow}) or {}).get("rows") or []
        if not rows:
            return -1
        n_kenh = len({str(x.get("channel") or "") for x in rows if x.get("channel")})
        da = int((goi("yt_con_cho", {"ngay": ngay}) or {}).get("da_dung_ngay", 0) or 0)
        con = max(0, n_kenh * TRAN_MOI_DU_AN - da)
        print(f"   ℹ️ Sức đăng SUY RA: {n_kenh} kênh × {TRAN_MOI_DU_AN}/ngày = {con} "
              f"(bảng dự án YouTube còn trống — con số này là ước tính trần trên).")
        return con
    except Exception:
        return -1


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


def kho_that_ghi(owner: str, tong: int) -> bool:
    """Ghi SỐ VIDEO THẬT trong kho (plan đếm từ Drive) vào D1 — dashboard đọc số này (25/8/2026).

    Vì sao cần: D1 chỉ có bản ghi job TỪ LÚC bật chế độ D1 (đo: 1.475) trong khi kho Drive có 1.996
    file thật; còn `__pushed__` bên Firestore là bộ đếm cộng dồn nên còn sai hơn. Chỉ lượt đi đếm
    72 kho mới là sự thật — cất nó vào chỗ dashboard đọc được mà không cần Firestore."""
    if not bat_ghi() or tong < 0:
        _keu_mot_lan("kho_that_tat",
                     f"kho_that_ghi bỏ qua: D1 tắt hoặc tổng không hợp lệ ({tong})")
        return False
    import datetime as _d
    r = goi("kho_that_ghi", {"owner": owner, "tong": int(tong),
                             "luc": _d.datetime.now(_d.timezone.utc).isoformat()})
    if not r.get("ok"):
        _keu_mot_lan("kho_that_tuchoi", f"kho_that_ghi bị từ chối: {str(r)[:80]}")
    return bool(r.get("ok"))


def don_job_cu(owner: str, ngay: int = 14) -> dict:
    """Dọn bản ghi job cũ hơn `ngay` ngày để D1 KHÔNG PHÌNH (25/8/2026).

    Đo thật: `apiHotStat` chạy 4 lệnh COUNT trên `render_job` mỗi lượt. Với 1.558 dòng là
    ~980K rows_read/ngày (19,6% trần 5 triệu). Bảng tăng ~400 dòng/ngày ⇒ **~15 ngày chạm 95%,
    ~30 ngày VƯỢT TRẦN**. Giữ 14 ngày gần nhất thì bảng đứng ở ~5.600 dòng, mức đọc phẳng mãi mãi.
    Lịch sử không mất: video ở Drive, kịch bản ở sidecar + 2 kho dự phòng."""
    if not bat_ghi():
        return {}
    return goi("don_job_cu", {"owner": owner, "ngay": int(ngay)}) or {}


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


# 26/8 — CÁC ĐƯỜNG GHI D1 TỪNG HỎNG TRONG IM LẶNG. Cả đêm qua em không hiểu vì sao dòng
# "Đã chụp hồ key" in 0 lần, vì `keys_ghi`/`nho_ghi` trả False mà không để lại một chữ nào.
# Đúng lớp lỗi với canary nuốt stderr và vẽ ảnh hỏng im lặng: BIẾT là hỏng, KHÔNG biết hỏng ở đâu.
# Nói MỘT LẦN mỗi lý do mỗi tiến trình — đủ để lần ra, không thành 588 dòng nhiễu.
_DA_KEU: set = set()


def _keu_mot_lan(ma: str, msg: str) -> None:
    if ma in _DA_KEU:
        return
    _DA_KEU.add(ma)
    print(f"   ⚠️ D1 {msg}")


def keys_ghi(owner: str, rows: list) -> bool:
    """Chụp hồ key CHỈ-CÓ-Ở-A vào D1 để 17 luồng còn lại khỏi phải đọc A (25/8/2026).

    Xem chú thích `keys_ghi` trong worker.js: `merge_keys_A=70` lượt đọc A MỖI LUỒNG là khoản
    tiêu lớn nhất trên project A và là lý do A cạn hạn mức mỗi ngày."""
    if not bat_ghi():
        _keu_mot_lan("keys_ghi_tat", "keys_ghi bỏ qua: D1 đang TẮT (thiếu HOT_KEY hoặc HOT_MODE)")
        return False
    if not rows:
        _keu_mot_lan("keys_ghi_rong", "keys_ghi bỏ qua: danh sách key RỖNG — không có gì để chụp")
        return False
    import json as _j
    from datetime import datetime as _dt, timezone as _tz
    try:
        r = goi("keys_ghi", {"owner": owner, "js": _j.dumps(rows)[:400_000],
                             "at": _dt.now(_tz.utc).isoformat()})
        if not r.get("ok"):
            _keu_mot_lan("keys_ghi_tuchoi", f"keys_ghi bị từ chối: {str(r)[:80]}")
        return bool(r.get("ok"))
    except Exception as e:
        _keu_mot_lan("keys_ghi_loi", f"keys_ghi lỗi: {str(e)[:80]}")
        return False


def keys_doc(owner: str, tuoi: int = 1800) -> list | None:
    """Ảnh chụp hồ key từ D1. None = không có / quá cũ -> caller cứ đọc A như cũ."""
    if not bat_doc():
        return None
    import json as _j
    from datetime import datetime as _dt, timezone as _tz
    try:
        r = goi("keys_doc", {"owner": owner})
        js, at = r.get("js") or "", r.get("at") or ""
        if not js or not at:
            return None
        tuoi_that = (_dt.now(_tz.utc) - _dt.fromisoformat(at)).total_seconds()
        if tuoi_that > tuoi:
            return None
        v = _j.loads(js)
        return v if isinstance(v, list) else None
    except Exception:
        return None


def nho_ghi(k: str, v, tuoi_gi: str = "") -> bool:
    """Cất một kết quả ĐỔI CHẬM vào bộ nhớ chung D1 để 18 luồng khỏi hỏi lại 18 lần."""
    if not bat_ghi() or not k:
        _keu_mot_lan("nho_ghi_tat", "nho_ghi bỏ qua: D1 đang TẮT (thiếu HOT_KEY hoặc HOT_MODE)")
        return False
    import json as _j
    from datetime import datetime as _dt, timezone as _tz
    try:
        r = goi("nho_ghi", {"k": k, "js": _j.dumps(v)[:200_000],
                            "at": _dt.now(_tz.utc).isoformat()})
        if not r.get("ok"):
            _keu_mot_lan("nho_ghi_tuchoi", f"nho_ghi bị từ chối: {str(r)[:80]}")
        return bool(r.get("ok"))
    except Exception as e:
        _keu_mot_lan("nho_ghi_loi", f"nho_ghi lỗi: {str(e)[:80]}")
        return False


def nho_doc(k: str, tuoi: int = 21600):
    """Lấy lại thứ đã cất. None = chưa có / quá hạn -> caller cứ đi hỏi nguồn gốc như cũ."""
    if not bat_doc() or not k:
        return None
    import json as _j
    from datetime import datetime as _dt, timezone as _tz
    try:
        r = goi("nho_doc", {"k": k})
        js, at = r.get("js") or "", r.get("at") or ""
        if not js or not at:
            return None
        if (_dt.now(_tz.utc) - _dt.fromisoformat(at)).total_seconds() > tuoi:
            return None
        return _j.loads(js)
    except Exception:
        return None


def kho_can_acc(owner: str) -> dict:
    """{drive_id: job_id} các bản ghi done thiếu kho chứa (xem worker `kho_can_acc`)."""
    if not bat_doc():
        return {}
    try:
        r = goi("kho_can_acc", {"owner": owner})
        return {x["drive_id"]: x["id"] for x in (r.get("rows") or []) if x.get("drive_id")}
    except Exception:
        return {}


def kho_acc_ghi(owner: str, pairs: list) -> int:
    """Đổ map file->kho về D1 theo lô 200 (pairs = [{'did':..., 'acc':...}])."""
    if not bat_ghi() or not pairs:
        return 0
    n = 0
    try:
        for i in range(0, len(pairs), 200):
            r = goi("kho_acc_ghi", {"owner": owner, "pairs": pairs[i:i + 200]})
            n += int(r.get("n") or 0)
    except Exception:
        pass
    return n


def job_cuaso(owner: str, tu: str, den: str) -> list:
    """Video done trong khoảng giờ [tu, den) — dọn bệnh theo lô (xem worker `job_cuaso`)."""
    if not bat_doc():
        return []
    try:
        return (goi("job_cuaso", {"owner": owner, "tu": tu, "den": den}) or {}).get("rows") or []
    except Exception:
        return []


def thumb_can(owner: str) -> dict:
    """{drive_id: job_id} các bản ghi done thiếu thumb_id (xem worker `thumb_can`)."""
    if not bat_doc():
        return {}
    try:
        r = goi("thumb_can", {"owner": owner})
        return {x["drive_id"]: x["id"] for x in (r.get("rows") or []) if x.get("drive_id")}
    except Exception:
        return {}


def thumb_ghi(owner: str, pairs: list) -> int:
    """Đổ map video->thumbnail về D1 theo lô 200 (pairs = [{'did':..., 'tid':...}])."""
    if not bat_ghi() or not pairs:
        return 0
    n = 0
    try:
        for i in range(0, len(pairs), 200):
            r = goi("thumb_ghi", {"owner": owner, "pairs": pairs[i:i + 200]})
            n += int(r.get("n") or 0)
    except Exception:
        pass
    return n
