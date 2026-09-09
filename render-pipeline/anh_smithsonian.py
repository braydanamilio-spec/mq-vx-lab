#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NGUỒN ẢNH THỨ NĂM — SMITHSONIAN OPEN ACCESS  (9/9/2026)

Anh: *"Smithsonian OA có cần nhiều khoá ko và giới hạn như nào làm phần lấy key api như mấy
key khác a nha a get xem"*.

── TRẦN, ĐO BẰNG HEADER CHỨ KHÔNG ĐOÁN ─────────────────────────────────────────────────────
Gọi thử rồi đọc `X-Ratelimit-Limit` của chính phản hồi:

    DEMO_KEY        ->  X-Ratelimit-Limit: 10      (mỗi giờ)
    khoá đăng ký    ->  api.data.gov cấp mặc định **1.000 lượt/giờ**

`X-Ratelimit-Remaining` đi kèm mỗi phản hồi, nên module này IN RA trần thật ở lượt gọi đầu:
khi anh dán khoá vào, chính nó tự khai trần chứ không phải tin vào tài liệu (§13.1).

── CẦN BAO NHIÊU KHOÁ: MỘT LÀ ĐỦ ───────────────────────────────────────────────────────────
Ước lượng nhu cầu từ nhịp chạy thật: 18 kênh × 3 bộ/ngày = 54 lượt dựng, mỗi lượt hỏi 1–3
lần cho một chủ thể => **~150 lượt/ngày**, tức ~6 lượt/giờ. Trần 1.000/giờ dư 160 lần.

Nên KHÔNG cần hồ khoá như Cloudflare (121 tài khoản) hay Groq (109 khoá) — hai bộ ấy cần
nhiều vì chúng bị tính theo NEURON và TOKEN, cạn theo ngày. Đây chỉ là truy vấn danh mục.
Vẫn viết đường XOAY nhiều khoá (nhận danh sách) vì nó rẻ: một khoá hỏng thì còn khoá sau,
và đó là bài học §18.4 — đường dự phòng phải có sẵn trước lúc cần, không phải lúc đã hỏng.

── CÁCH ĐẶT KHOÁ, GIỐNG HỆT CÁC KHOÁ KHÁC ──────────────────────────────────────────────────
    máy anh   : thêm dòng `sm:<khoá>` vào `render-pipeline/.keys.local`
    GitHub    : `grep '^sm:' render-pipeline/.keys.local | gh secret set SMITHSONIAN_KEYS`
                rồi khai `SMITHSONIAN_KEYS: ${{ secrets.SMITHSONIAN_KEYS }}` ở workflow
Đọc biến môi trường TRƯỚC, tệp SAU — đúng thứ tự mã thật chạy ở hai môi trường (§15.4).

KHÔNG có khoá thì hàm trả `[]` và IN RÕ lý do. "Chưa cấu hình" và "kho không có ảnh" là hai
câu khác nhau, và trộn chúng vào một số 0 là §15.2.

── ⛔ KẾT LUẬN: CHƯA DÙNG ĐƯỢC. GIỮ MÃ, KHÔNG NỐI VÀO DÂY CHUYỀN  (đo 9/9/2026) ─────────────
Khoá: KHÔNG cần lấy mới. Nút "Lấy key NARA" trên dashboard trỏ tới `api.data.gov/signup` —
đúng cùng cổng khoá với Smithsonian. Hai khoá `nara:` anh đã có chạy thẳng, trần đầy đủ
**1.000 lượt/giờ**, Kodak trả 1.244 bản ghi. Phần khoá KHÔNG phải chỗ hỏng.

Chỗ hỏng là API không đưa URL ảnh ra:
    search   -> chỉ có `indexedStructured.online_media_type = ['Images']` (một lá cờ)
    content  -> `descriptiveNonRepeating` KHÔNG có khối `online_media`
    quét 10 bản ghi Kodak: **0/10 có URL ảnh**

Nên nguồn này đóng góp ĐÚNG 0 ảnh trong khi tốn 2 lượt gọi mỗi lượt dựng. Không nối.
Giữ mã lại vì phần khoá và phần lọc đều đúng và đã thử: nếu sau này tìm được đường lấy media
(có thể qua `unit_code` khác NMAH, hoặc qua IDS bằng `record_ID`) thì chỉ cần sửa `_anh_trong`.
Ghi ra đây để phiên sau không đi làm lại từ đầu rồi dừng ở đúng chỗ này.

── (phần dưới là lập luận lúc chưa đo được, giữ để đối chiếu) ──────────────────────────────
Openverse thêm vào gần như KHÔNG tăng trung vị (4 -> 4 trên 20 chủ thể ngẫu nhiên) vì hồ đầy
chủ thể vô danh. Smithsonian khác ở chỗ nó là kho HIỆN VẬT: máy ảnh Kodak, máy bay, thiết bị
— tức nó mạnh đúng ở loại chủ thể "công ty/sản phẩm biến mất" mà 18 kênh đang kể. Kodak cho
294 bản ghi có ảnh. Nhưng ĐỪNG tin trước: sau khi có khoá, đo lại trên 20 chủ thể NGẪU NHIÊN
của hồ thật, không phải trên vài cái tên lớn — đúng lỗi em vừa mắc với Openverse (§12.3).
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

UA = {"User-Agent": "MM0-pipeline/1.0 (+https://github.com/braydanamilio-spec/mq-vx-lab)"}
GOC = os.path.dirname(os.path.abspath(__file__))
KHO = os.path.join(GOC, "anh_pd")
API = "https://api.si.edu/openaccess/api/v1.0/search"
IDS = "https://ids.si.edu/ids/deliveryService"

_DU_LON = 900
TRAN_BYTE = 24 * 1024 * 1024
_NHIP = 0.5
_LUC = [0.0]
_DA_KHAI = [False]        # đã in trần thật chưa
_CAN = [False]            # đã chạm 429 trong lượt này -> dừng, đừng nện tiếp
_DAU_LOGO = re.compile(r"\b(logo|icon|symbol|emblem|wordmark|coat of arms|seal|badge)\b", re.I)


def _khoa() -> list:
    """Khoá Smithsonian — VÀ KHOÁ NARA DÙNG ĐƯỢC LUÔN.

    ── ĐO RA, KHÔNG PHẢI ĐOÁN  (9/9/2026) ──────────────────────────────────────────────
    Em đã định bảo anh đi đăng ký một khoá mới. Nhìn kỹ nút "Lấy key NARA" trên dashboard
    thì nó trỏ tới `api.data.gov/signup` — ĐÚNG cùng cổng khoá với Smithsonian, vì cả hai
    API đều nằm sau api.data.gov. Thử hai khoá `nara:` anh đã có:

        HTTP 200 · X-Ratelimit-Limit 1000/giờ · Kodak 1.244 bản ghi

    Chạy thẳng, trần đầy đủ. Không cần khoá mới, không cần anh làm gì.

    §13.1 ở dạng đắt nhất nếu bỏ sót: cơ chế đã có sẵn trong repo, và em suýt bắt anh đi
    lấy lại thứ đang nằm trong tay. Luôn hỏi *"cái gì đang chạy nó?"* trước khi xin thêm.

    Thứ tự đọc: biến môi trường trước, tệp sau (§15.4). Trong tệp thì nhận cả `sm:` (nếu
    sau này anh có khoá riêng) lẫn `nara:` — cùng một loại khoá, hai cái nhãn."""
    ra = []
    for ten in ("SMITHSONIAN_KEYS", "NARA_KEYS"):
        for d in (os.environ.get(ten, "") or "").replace(",", "\n").splitlines():
            d = d.strip()
            if not d or d.startswith("#"):
                continue
            for tien in ("sm:", "nara:"):
                if d.startswith(tien):
                    d = d[len(tien):]
                    break
            ra.append(d)
    if not ra:
        p = os.path.join(GOC, ".keys.local")
        if os.path.exists(p):
            for l in io.open(p, encoding="utf-8"):
                l = l.strip()
                for tien in ("sm:", "nara:"):
                    if l.startswith(tien) and len(l) > len(tien):
                        ra.append(l[len(tien):])
                        break
    return [k for k in dict.fromkeys(ra) if k]


def _goi(q: str, rows: int, khoa: str) -> dict:
    cho = _NHIP - (time.time() - _LUC[0])
    if cho > 0:
        time.sleep(cho)
    _LUC[0] = time.time()
    u = (API + "?q=" + urllib.parse.quote(q) + f"&api_key={urllib.parse.quote(khoa)}"
         + f"&rows={rows}")
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=45)
    if not _DA_KHAI[0]:
        _DA_KHAI[0] = True
        tr = r.headers.get("X-Ratelimit-Limit")
        con = r.headers.get("X-Ratelimit-Remaining")
        if tr:
            print(f"   ⓘ Smithsonian: trần {tr} lượt/giờ · còn {con}")
    return json.loads(r.read())


def _anh_trong(row: dict, khoa: str) -> list:
    """Mọi ảnh CC0 của một bản ghi — CẦN MỘT LƯỢT GỌI THỨ HAI.

    ── ĐO RA MỚI BIẾT  (9/9/2026) ──────────────────────────────────────────────────────
    Bản đầu của em đọc `descriptiveNonRepeating.online_media.media` thẳng từ kết quả tìm
    kiếm, và ra 0 ảnh cho MỌI chủ thể. Dump trọn một bản ghi thì thấy endpoint `search`
    KHÔNG trả media — nó chỉ báo bản ghi CÓ ảnh:

        content.indexedStructured.online_media_type = ['Images']
        content.descriptiveNonRepeating.metadata_usage.access = 'CC0'

    URL ảnh nằm ở endpoint `content/{id}`, tức mỗi bản ghi tốn thêm MỘT lượt gọi. Đây là
    ràng buộc của API, không phải thứ nới bằng tham số — và nó đổi phép tính hạn mức:
    một chủ thể = 1 lượt tìm + N lượt đọc bản ghi. Lấy 8 ảnh là 9 lượt.
    Với trần 1.000/giờ của khoá đăng ký: 54 lượt dựng/ngày × 9 ≈ 490 lượt/ngày — vẫn dư.

    Nếu em cứ ship bản đầu thì nguồn này đóng góp ĐÚNG 0 ảnh mà không một dòng lỗi nào,
    và nhìn từ ngoài y hệt "Smithsonian không có ảnh chủ thể này" (§15.2 · §18.4)."""
    ra = []
    c = row.get("content") or {}
    dnr = c.get("descriptiveNonRepeating") or {}
    if str((dnr.get("metadata_usage") or {}).get("access") or "").upper() != "CC0":
        return ra
    rid = row.get("id") or ""
    if not rid:
        return ra
    try:
        cho = _NHIP - (time.time() - _LUC[0])
        if cho > 0:
            time.sleep(cho)
        _LUC[0] = time.time()
        u = (f"https://api.si.edu/openaccess/api/v1.0/content/{urllib.parse.quote(rid)}"
             f"?api_key={urllib.parse.quote(khoa)}")
        d = json.loads(urllib.request.urlopen(
            urllib.request.Request(u, headers=UA), timeout=45).read())
    except Exception as e:
        # 429 = hết hạn mức giờ này. Nó là hàng rào CÓ CHỦ Ý, không phải một gói tin rớt —
        # thử bản ghi tiếp theo chỉ tốn thêm một lượt bị từ chối. Đo thật với DEMO_KEY: sau
        # lượt 429 đầu tiên em còn nện thêm 14 lượt nữa, tất cả đều 429 (§18.9 · §19.20).
        # Cắm cờ để `anh_cua` dừng hẳn chủ thể này, không phải chỉ bỏ một bản ghi.
        if "429" in str(e):
            _CAN[0] = True
            print("   ⓘ Smithsonian: hết hạn mức giờ này — DỪNG, lượt sau đo lại")
        else:
            print(f"   ⚠ Smithsonian đọc bản ghi hụt: {type(e).__name__} {str(e)[:36]}")
        return ra
    dnr2 = ((d.get("response") or {}).get("content") or {}).get(
        "descriptiveNonRepeating") or {}
    for m in ((dnr2.get("online_media") or {}).get("media") or []):
        if str(m.get("type") or "").lower() != "images":
            continue
        if str((m.get("usage") or {}).get("access") or "CC0").upper() not in ("CC0", ""):
            continue
        ids = m.get("idsId") or ""
        url = (f"{IDS}?id={urllib.parse.quote(ids)}&max={_DU_LON * 2}") if ids else (
            m.get("content") or "")
        if url:
            ra.append(url)
    return ra


def anh_cua(chu_the: str, toi_da: int = 8) -> list:
    """[{ten, url, giay_phep}] — CC0, tên MANG TÊN CHỦ THỂ, không logo."""
    cum = " ".join(str(chu_the or "").lower().split())
    if len(cum) < 4:
        return []
    ks = _khoa()
    if not ks:
        print("   ⓘ Smithsonian: chưa có khoá (đặt `sm:<khoá>` trong .keys.local hoặc "
              "SMITHSONIAN_KEYS) — bỏ qua nguồn này")
        return []
    q = f'{chu_the} AND online_media_type:"Images"'
    d = None
    for k in ks:
        try:
            d = _goi(q, min(50, toi_da * 6), k)
            break
        except Exception as e:
            print(f"   ⚠ Smithsonian khoá hụt ({type(e).__name__} {str(e)[:36]}) — đổi khoá")
    if not d:
        return []
    ra, thay = [], set()
    _CAN[0] = False
    # Trần số bản ghi được MỞ, không chỉ trần số ảnh nhận: một chủ thể mà mọi bản ghi đều
    # không phải CC0 sẽ đốt hết hạn mức giờ mà không thu được ảnh nào.
    _mo = 0
    for row in ((d.get("response") or {}).get("rows") or []):
        if _CAN[0] or _mo >= toi_da + 4:
            break
        _mo += 1
        ten = " ".join(str(row.get("title") or "").split())
        if not ten or cum not in ten.lower() or _DAU_LOGO.search(ten):
            continue
        for url in _anh_trong(row, ks[0]):
            if url in thay:
                continue
            thay.add(url)
            ra.append({"ten": ten, "url": url, "giay_phep": "CC0"})
            if len(ra) >= toi_da:
                return ra
    return ra


def _ha_co(d: str) -> str:
    try:
        from PIL import Image
        im = Image.open(d)
        if max(im.size) <= 1600:
            return d
        im = im.convert("RGB")
        im.thumbnail((1600, 1600))
        im.save(d, "JPEG", quality=86)
    except Exception:
        pass
    return d


def tai_ve(anh: dict) -> str:
    try:
        os.makedirs(KHO, exist_ok=True)
        k = hashlib.sha1(anh["url"].encode("utf-8")).hexdigest()[:20]
        d = os.path.join(KHO, k + ".jpg")
        # Nhánh ĐÃ CÓ cũng qua `_ha_co` — nhánh trả về sớm là chỗ dễ quên nhất (§6).
        if os.path.exists(d) and os.path.getsize(d) > 4096:
            return _ha_co(d)
        b = urllib.request.urlopen(
            urllib.request.Request(anh["url"], headers=UA), timeout=60).read(TRAN_BYTE + 1)
        if len(b) < 4096 or len(b) > TRAN_BYTE:
            return ""
        io.open(d, "wb").write(b)
        return _ha_co(d)
    except Exception as e:
        print(f"   ⚠ Smithsonian tải hụt «{str(anh.get('ten'))[:32]}»: {str(e)[:40]}")
        return ""


if __name__ == "__main__":
    import sys
    for ct in (sys.argv[1:] or ["Kodak", "Pan Am"]):
        r = anh_cua(ct, toi_da=10)
        print(f"{ct:22s} {len(r)} ảnh CC0")
        for x in r[:3]:
            print(f"     {x['ten'][:60]}")
