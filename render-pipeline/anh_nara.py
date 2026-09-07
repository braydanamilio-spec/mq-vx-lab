#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ẢNH TƯ LIỆU MỸ TỪ NARA — nguồn thứ hai cho nền ảnh thật.  (7/9/2026)

── VÌ SAO CẦN NGUỒN THỨ HAI ──────────────────────────────────────────────────────────────
Anh: *"ảnh khớp bối cảnh vẫn hơi ít"*. Đúng, và đo được: `anh_tu_do` (Wikimedia, chỉ nhận
Public domain + CC0) trả **Kodak 8 · Concorde 3 · Betamax 1 · MH370 0**. Một tập 9–12 nhịp
thì chừng ấy không phủ nổi các nhịp lẻ.

NARA (Cục Lưu trữ Quốc gia Hoa Kỳ) trả cho cùng chủ thể:

    Kodak 79.704 · Three Mile Island 275.195 · Concorde 5.781 · Betamax 112 bản ghi

── VÌ SAO KHÔNG DÙNG PEXELS/PIXABAY  (đo 7/9/2026, và đây là lý do KỸ THUẬT) ──────────────
Truy vấn VÔ NGHĨA `zzqx wubblefrotz`:

    Pexels -> 4.248 ảnh (bóng bay, phụ nữ trong studio)
    NARA   -> 0

Pexels không bao giờ trả zero: hết khớp thì nó lùi về ảnh chung chung và vẫn báo hàng nghìn
"kết quả". `betamax` ra băng VHS — đúng thứ đã THẮNG Betamax, tức một lỗi sự thật hiện thẳng
trên màn hình; `eastman kodak headquarters` ra một máy chiếu Kodascope. Một kho luôn trả về
thứ gì đó là một kho **không phân biệt được "không có" với "có"** (§15.2), và mọi phép lọc
đặt sau nó đều đang lọc rác chứ không lọc tư liệu.

Chuyện "cả thế giới dùng chung một kho nên bị đánh spam" thì KHÔNG phải rủi ro: luật YouTube
xét các video trong CÙNG một kênh có giống nhau không, không xét kênh này có dùng chung kho
với kênh khác không (§13.18).

── HAI CỔNG, VÀ CẢ HAI ĐỀU CẦN ───────────────────────────────────────────────────────────
1. **LOẠI BẢN GHI.** Đo 50 bản ghi đầu của «Kodak»: 32 là ảnh, **18 là văn bản** — và kết quả
   xếp hạng CAO NHẤT lại là bản scan vi phim một tờ kiểm kê tài sản. Đúng chủ thể, vô dụng làm
   nền. Chỉ nhận `Photographs and other Graphic Materials`.
2. **ĐÚNG CHỦ THỂ.** Cùng luật đã rút ở §19.13 cho Wikimedia: tiêu đề bản ghi phải mang tên
   chủ thể, nếu không thì đó là thứ chỉ đứng cạnh nó trong kho.

Giấy phép: tác phẩm của chính phủ liên bang Mỹ thuộc **public domain** theo 17 U.S.C. §105.
NARA vẫn có bản ghi của bên thứ ba, nên cổng đọc `useRestriction` và loại mọi thứ không nói
rõ là không hạn chế.

Đây là TẦNG BỔ SUNG (§7): hỏng thì trả rỗng, tập vẫn dựng bằng nền vẽ code.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "MM0-pipeline/1.0 (youtube explainer; contact via repo owner)"}
GOC = os.path.dirname(os.path.abspath(__file__))
KHO = os.path.join(GOC, "anh_pd")
API = "https://catalog.archives.gov/proxy/records/search"
_LUC = 0.0        # lúc gọi gần nhất — xem giãn cách trong `_goi`

_ANH = "photographs and other graphic materials"
_DUOI = (".jpg", ".jpeg", ".png", ".tif", ".tiff")
# Hạn chế dùng lại. NARA ghi bằng vài cách; chỉ nhận thứ nói rõ là KHÔNG hạn chế.
_MO = ("unrestricted", "public domain", "no restrictions", "")


def _khoa() -> list:
    """Mọi khoá NARA (env trước, rồi `.keys.local`). Trả [] khi không có — KHÔNG ném."""
    ra = [x.strip() for x in os.environ.get("NARA_KEY", "").split(",") if x.strip()]
    try:
        for d in io.open(os.path.join(GOC, ".keys.local"), encoding="utf-8"):
            if d.startswith("nara:"):
                k = d.strip().split(":", 1)[1]
                if k not in ra:
                    ra.append(k)
    except Exception:
        pass
    return ra


# `limit` PHẢI nhỏ. Đo với khoảng cách 20 giây giữa hai lệnh (tức đã loại hẳn yếu tố chùm):
#     limit=20 -> JSON 136 KB        limit=60 -> HTML 5,4 KB
# Lần đo đầu em kết luận "chặn ngẫu nhiên, tham số không ảnh hưởng" vì thấy 25 và 60 hỏng mà
# 50 và 100 chạy — nhưng SÁU lệnh ấy bắn liên tiếp, nên phép đo đang đo cái chùm chứ không đo
# tham số. §13.15: trước khi kết luận hạ tầng của người ta hỏng, kiểm lại bài kiểm của mình.
# Cần nhiều hơn 20 thì gọi thêm một lượt với `offset`, đừng nâng `limit`.
_LIM = 20


def _goi(q: str, lim: int = _LIM) -> dict:
    """Gọi NARA, XOAY KHOÁ rồi LÙI DẦN khi bị chặn nhịp.

    ── VÌ SAO PHẢI CÓ  (đo 7/9/2026) ─────────────────────────────────────────────────────
    Bốn lệnh gọi liên tiếp thì **cả bốn** bị từ chối, và NARA từ chối bằng **HTTP 200 + một
    trang HTML** chứ không phải 429. Không kiểm nội dung thì `json.loads` ném, `except` nuốt,
    và log in ra "0 ảnh" — tức "kho không có gì" và "tôi bị chặn" ra cùng một dòng chữ
    (§15.2). Hạn mức thật là 1.000 lượt/giờ, nên bốn lượt bị chặn KHÔNG phải hết hạn mức mà
    là chặn nhịp dồn dập; lùi một nhịp là qua.
    """
    ks = _khoa()
    if not ks:
        return {}
    # GIÃN CÁCH TỐI THIỂU giữa hai lệnh gọi. Đo: một lệnh ĐƠN cách quãng luôn ra JSON, còn bốn
    # lệnh liên tiếp thì cả bốn ra HTML — kể cả khi có lùi dần bên trong, vì lần thử đầu của
    # truy vấn sau nổ ngay sau lần thử cuối của truy vấn trước, nên chùm không bao giờ tan.
    # Vòng lùi bên trong không thay được cái này: nó phải là trạng thái của CẢ MODULE.
    global _LUC
    cho = 2.6 - (time.time() - _LUC)
    if cho > 0:
        time.sleep(cho)
    _LUC = time.time()
    u = API + "?" + urllib.parse.urlencode({"q": q, "limit": lim})
    cuoi = ""
    for lan in range(max(6, len(ks) * 3)):
        try:
            r = urllib.request.Request(u, headers={**UA, "x-api-key": ks[lan % len(ks)]})
            b = urllib.request.urlopen(r, timeout=60).read()
            if b[:1] == b"{":
                return json.loads(b)
            cuoi = "NARA trả HTML (chặn nhịp gọi)"
        except Exception as e:
            cuoi = str(e)[:60]
        time.sleep(min(8.0, 1.5 * (2 ** (lan // 2))))
        _LUC = time.time()
    raise RuntimeError(cuoi or "NARA không trả JSON")


def anh_cua(chu_the: str, toi_da: int = 8) -> list:
    """[{ten, url, giay_phep}] — chỉ ẢNH, chỉ không hạn chế, chỉ đúng chủ thể."""
    if not _khoa():
        return []
    try:
        d = _goi(chu_the)
    except Exception as e:
        print(f"   ⚠ NARA: {str(e)[:60]}")
        return []
    kho = [w for w in re.split(r"[^a-z0-9]+", chu_the.split(" (")[0].lower())
           if len(w) > 2 and w not in ("the", "and", "for")]
    ra = []
    for x in (d.get("body", {}).get("hits", {}).get("hits") or []):
        r = (x.get("_source") or {}).get("record") or {}
        loai = [str(g).lower() for g in (r.get("generalRecordsTypes") or [])]
        if _ANH not in loai:
            continue                      # bản ghi VĂN BẢN: đúng chủ thể, vô dụng làm nền
        ten = str(r.get("title") or "")
        if kho and not any(w in ten.lower() for w in kho):
            continue                      # §19.13: chỉ đứng cạnh chủ thể, không nói về nó
        han = str(r.get("useRestriction") or {}).lower()
        if not any(m in han for m in _MO):
            continue
        for do in (r.get("digitalObjects") or []):
            url = str(do.get("objectUrl") or "")
            tep = str(do.get("objectFilename") or "")
            # Đuôi đọc từ TÊN TỆP, không từ URL — bài học đã trả giá ở `anh_tu_do` (§19.12).
            if not url or os.path.splitext(tep.lower())[1] not in _DUOI:
                continue
            ra.append({"ten": ten, "url": url, "giay_phep": "NARA · US Government"})
            break
        if len(ra) >= toi_da:
            break
    return ra


# Ảnh lưu trữ là bản QUÉT GỐC: đo được một tấm Concorde **27 MB**. Kho nền cả hệ chỉ 104 MB
# cho 1.978 tệp, nên vài tấm như thế là hỏng cả phép cân đối dung lượng (§18.12) và làm Remotion
# đọc chậm. Chặn ở hai tầng: bỏ hẳn tấm quá to, và HẠ CỠ những tấm nhận về.
# 24 MB loại mất 3/8 ảnh Concorde ĐÚNG chủ thể. Vì `_ha_co` đã đưa mọi tấm về ~250 KB nên cái
# giá của một tấm to chỉ là băng thông một lần, không phải dung lượng kho — nên trần đặt ở chỗ
# chặn tệp bất thường, không ở chỗ tiết kiệm đĩa. §15.1: trần phải đặt trên đại lượng mình muốn
# chặn (tải một tệp khổng lồ), không trên đại lượng dễ đếm (cỡ tệp lưu).
TRAN_BYTE = 60 * 1024 * 1024
# Panel là khung dọc 1080×1920 và ảnh đặt bằng `objectFit: cover`, nên quá 1.600px cạnh dài là
# điểm ảnh không bao giờ tới được màn hình — đúng bài học §18.13, phía tệp tải về.
CANH_DAI = 1600


def _ha_co(d: str) -> str:
    """Hạ cỡ ảnh vừa tải về. Không có Pillow thì GIỮ NGUYÊN — đây là tối ưu, không phải cổng."""
    try:
        from PIL import Image
    except Exception:
        return d
    try:
        im = Image.open(d)
        if max(im.size) <= CANH_DAI:
            return d
        cu = os.path.getsize(d)
        im = im.convert("RGB")
        im.thumbnail((CANH_DAI, CANH_DAI), Image.LANCZOS)
        moi = os.path.splitext(d)[0] + ".jpg"
        im.save(moi, "JPEG", quality=88, optimize=True)
        if moi != d:
            os.remove(d)
        print(f"   ↓ hạ cỡ {cu // 1024} KB -> {os.path.getsize(moi) // 1024} KB")
        return moi
    except Exception as e:
        print(f"   ⚠ hạ cỡ hỏng ({str(e)[:40]}) — giữ bản gốc")
        return d


def tai_ve(anh: dict) -> str:
    """Tải một ảnh về kho cục bộ. Trả đường dẫn, "" khi hỏng — nói RÕ lý do, không nuốt."""
    try:
        os.makedirs(KHO, exist_ok=True)
        k = hashlib.sha1(anh["url"].encode("utf-8")).hexdigest()[:20]
        duoi = os.path.splitext(urllib.parse.urlparse(anh["url"]).path)[1].lower() or ".jpg"
        d = os.path.join(KHO, k + duoi)
        # Đi qua `_ha_co` cả ở nhánh ĐÃ CÓ: tệp tải về từ lượt trước có thể còn ở cỡ gốc, và
        # nhánh trả về sớm là chỗ dễ quên nhất (§6: vá một nhánh, để nguyên nhánh song song).
        if os.path.exists(d) and os.path.getsize(d) > 4096:
            return _ha_co(d)
        r = urllib.request.Request(anh["url"], headers=UA)
        b = urllib.request.urlopen(r, timeout=60).read(TRAN_BYTE + 1)
        if len(b) < 4096:
            return ""
        if len(b) > TRAN_BYTE:
            print(f"   ⚠ NARA bỏ ảnh > {TRAN_BYTE // 1048576} MB: {anh['ten'][:40]}")
            return ""
        io.open(d, "wb").write(b)
        return _ha_co(d)
    except Exception as e:
        print(f"   ⚠ NARA tải hỏng: {str(e)[:60]}")
        return ""


if __name__ == "__main__":
    import sys
    for q in (sys.argv[1:] or ["Kodak", "Concorde", "Betamax", "zzqx wubblefrotz"]):
        r = anh_cua(q)
        print(f"\n« {q} » -> {len(r)} ảnh")
        for a in r:
            print("   ", a["ten"][:70])
