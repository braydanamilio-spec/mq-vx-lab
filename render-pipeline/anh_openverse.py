#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NGUỒN ẢNH THỨ TƯ — OPENVERSE  (9/9/2026)

Anh: *"ảnh thực làm nền videos footage e đang lấy ảnh ở đâu nguồn nào đảm bảo đa dạng đủ cho
việc làm videos chứ"* · *"có thể thêm vài nguồn ok cho phong phú hoặch dự phòng"*.

── VÌ SAO CẦN NGUỒN THỨ TƯ  (đo 20 chủ thể ngẫu nhiên, 9/9) ────────────────────────────────
Ba nguồn đang có cho TRUNG VỊ **5 ảnh/chủ thể**; 8/20 chủ thể có dưới 3 ảnh. Trong khi một
tập cần ~30 hình nếu footage phải đổi mỗi 1,5–2,5 giây như anh yêu cầu. Thiếu gấp sáu lần.

── VÌ SAO CHỌN OPENVERSE, VÀ HAI NGUỒN BỊ LOẠI ─────────────────────────────────────────────
Bài kiểm bắt buộc trước khi tin một kho (§19.14): gõ một truy vấn VÔ NGHĨA. Kho nào vẫn trả
hàng nghìn kết quả thì nó không phân biệt được "không có" với "có", và mọi phép lọc đặt sau
nó đều đang lọc rác.

    truy vấn `zzqx wubblefrotz`      «Kodak»
    Openverse            0             240      ✅
    Internet Archive     0              20      ✅
    Smithsonian OA       0           1.244      ✅ nhưng CẦN KHOÁ (DEMO_KEY có hạn ngặt)
    Library of Congress  403           403      ⛔ chặn ở môi trường này
    DPLA                 403           403      ⛔ như trên

Chọn Openverse trước vì nó **không cần khoá** — không đụng ràng buộc "không tạo thông tin
đăng nhập mới" — và nó GỘP nhiều bảo tàng (Flickr Commons, Science Museum, Statens Museum…),
tức nó bù đúng chỗ Wikimedia mỏng.

── SỐ ĐO, VÀ MỘT CON SỐ EM ĐÃ BÁO SAI ──────────────────────────────────────────────────────
Lượt đo đầu: 6 chủ thể EM TỰ CHỌN (Kodak, Pan Am, Thalidomide, Convair, Fine Air, Great
Fires) -> 229 thô, 64 qua lọc, **trung bình 10,7 ảnh/chủ thể**. Em báo con số ấy với anh.

Đo lại trên **20 chủ thể NGẪU NHIÊN** rút từ chính hồ đang dùng:

    trung vị      4  ->  4     (không đổi)
    có ≥ 3 ảnh   12/20 -> 12/20
    có ≥ 6 ảnh    8/20 ->  9/20
    có ≥10 ảnh    6/20 ->  6/20

Gần như KHÔNG TĂNG. Sáu chủ thể kia toàn tên lớn; hồ thật đầy «Great Lakes Jet Express»,
«Caldera UK», «CMS Enhancements» — những cái tên không có ảnh ở BẤT KỲ kho nào. Đúng §12.3,
lỗi em vừa dùng để bác một thước khác rồi lại tự mắc: calibrate trên mẫu thuận, suy ra cả hồ.

KẾT LUẬN ĐỔI THEO: thiếu ảnh KHÔNG phải bài toán NGUỒN mà là bài toán CHỌN CHỦ THỂ. Thêm
nguồn thứ năm, thứ sáu cũng không cứu được một chủ thể mà thế giới không chụp tấm nào.
Đòn bẩy thật nằm ở `vi_sao._SAN_ANH` — hiện là ƯU TIÊN, muốn hết khung trống thì phải thành
SÀN, và đó là đánh đổi sản lượng lấy chất lượng nên để anh quyết.

Vẫn GIỮ nguồn này: nó không hại gì, tốn 3 lượt gọi, và có ích thật với chủ thể tên tuổi
(Pan Am 42 ảnh) — đúng vai một tầng dự phòng (§7).

── HAI CÁI BẪY ĐÃ ĐO ───────────────────────────────────────────────────────────────────────
1. `result_count` trả **240 cho MỌI truy vấn** — nó là trần, không phải số khớp. Đừng bao giờ
   dùng con số ấy để xếp hạng hay để quyết định gì (§15.2).
2. `page_size` > 20 trả **HTTP 401** cho lượt gọi ẩn danh. Không phải sai khoá — là trần của
   truy cập ẩn danh. Nên lấy nhiều bằng cách PHÂN TRANG, không bằng cách xin trang to.

Giấy phép lọc ngay ở TRUY VẤN (`license=cc0,pdm`) chứ không lọc sau: rẻ hơn, và không bao giờ
có chuyện một ảnh có bản quyền lọt vào bộ nhớ đệm rồi mới bị loại.
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

# Cùng UA với `anh_nara`: URL repo là đủ, KHÔNG đưa email cá nhân của anh cho bên thứ ba.
UA = {"User-Agent": "MM0-pipeline/1.0 (+https://github.com/braydanamilio-spec/mq-vx-lab)"}
GOC = os.path.dirname(os.path.abspath(__file__))
KHO = os.path.join(GOC, "anh_pd")
API = "https://api.openverse.org/v1/images/"

_TRANG = 20          # trần THẬT của lượt gọi ẩn danh; xin hơn thì 401
_NHIP = 0.6          # giãn cách giữa hai lượt gọi
_LUC = [0.0]
_DU_LON = 900        # cùng sàn với `anh_tu_do`: nhỏ hơn thì phóng lên nền là vỡ
TRAN_BYTE = 24 * 1024 * 1024
# Logo/biểu tượng KHÔNG làm nền được — cùng luật đã áp ở `pilot_hai._chen_anh_that`, và ở đây
# chặn sớm hơn một bước để khỏi tốn một lượt tải.
_DAU_LOGO = re.compile(r"\b(logo|icon|symbol|emblem|wordmark|coat of arms|seal|badge)\b", re.I)


def _goi(q: str, trang: int) -> list:
    cho = _NHIP - (time.time() - _LUC[0])
    if cho > 0:
        time.sleep(cho)
    _LUC[0] = time.time()
    u = (API + "?q=" + urllib.parse.quote(q)
         + f"&license=cc0,pdm&page_size={_TRANG}&page={trang}")
    r = urllib.request.Request(u, headers=UA)
    b = urllib.request.urlopen(r, timeout=45).read()
    if not b[:1] == b"{":
        raise RuntimeError("Openverse trả về thứ không phải JSON — nghi bị chặn")
    return json.loads(b).get("results") or []


def anh_cua(chu_the: str, toi_da: int = 8) -> list:
    """[{ten, url, giay_phep}] — CC0/PD, đủ lớn, tên MANG TÊN CHỦ THỂ.

    Luật tên là bắt buộc ở đây chứ không phải tuỳ chọn: Openverse tìm theo chữ nên «Fine Air»
    trả về cả *"Postcard: Simon Fraser Hotel"*. Đo trên 6 chủ thể: 229 thô -> 64 qua lọc.
    Một nguồn rộng mà lọc lỏng thì chỉ là đổ thêm rác vào (§19.14).
    """
    cum = " ".join(str(chu_the or "").lower().split())
    if len(cum) < 4:
        return []
    ra, thay = [], set()
    for trang in (1, 2, 3):
        if len(ra) >= toi_da:
            break
        try:
            rs = _goi(chu_the, trang)
        except Exception as e:
            # Nói RÕ lý do rồi dừng — "0 ảnh" và "không hỏi được" là hai câu khác nhau (§15.2).
            print(f"   ⚠ Openverse hụt ở trang {trang}: {type(e).__name__} {str(e)[:44]}")
            break
        if not rs:
            break
        for r in rs:
            ten = " ".join(str(r.get("title") or "").split())
            url = r.get("url") or ""
            if not url or not ten:
                continue
            if (r.get("width") or 0) < _DU_LON:
                continue
            if cum not in ten.lower():
                continue
            if _DAU_LOGO.search(ten):
                continue
            if url in thay:
                continue
            thay.add(url)
            ra.append({"ten": ten, "url": url,
                       "giay_phep": f"{r.get('license')}-{r.get('license_version')}"})
            if len(ra) >= toi_da:
                break
    return ra


def _ha_co(d: str) -> str:
    """Hạ ảnh về cỡ dùng được. Kho nền cả hệ chỉ ~100 MB, một tấm gốc có thể 27 MB."""
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
    """Tải một ảnh về kho cục bộ. Trả đường dẫn, "" khi hỏng — nói RÕ lý do, không nuốt."""
    try:
        os.makedirs(KHO, exist_ok=True)
        k = hashlib.sha1(anh["url"].encode("utf-8")).hexdigest()[:20]
        duoi = os.path.splitext(urllib.parse.urlparse(anh["url"]).path)[1].lower()
        if duoi not in (".jpg", ".jpeg", ".png", ".webp"):
            duoi = ".jpg"
        d = os.path.join(KHO, k + duoi)
        # Nhánh ĐÃ CÓ cũng phải đi qua `_ha_co` — nhánh trả về sớm là chỗ dễ quên nhất (§6).
        if os.path.exists(d) and os.path.getsize(d) > 4096:
            return _ha_co(d)
        b = urllib.request.urlopen(
            urllib.request.Request(anh["url"], headers=UA), timeout=60).read(TRAN_BYTE + 1)
        if len(b) < 4096:
            return ""
        if len(b) > TRAN_BYTE:
            print(f"   ⚠ Openverse bỏ ảnh > {TRAN_BYTE // 1048576} MB: {anh['ten'][:40]}")
            return ""
        io.open(d, "wb").write(b)
        return _ha_co(d)
    except Exception as e:
        print(f"   ⚠ Openverse tải hụt «{str(anh.get('ten'))[:34]}»: "
              f"{type(e).__name__} {str(e)[:40]}")
        return ""


if __name__ == "__main__":
    import sys
    for ct in (sys.argv[1:] or ["Kodak", "Pan Am", "Fine Air"]):
        r = anh_cua(ct, toi_da=12)
        print(f"{ct:24s} {len(r)} ảnh")
        for x in r[:3]:
            print(f"     {x['giay_phep']:10s} {x['ten'][:56]}")
