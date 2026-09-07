#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HỒ CHỦ THỂ — nguồn đề tài không cạn cho 18 kênh.  (7/9/2026)

Anh: *"làm xây pepline chuẩn cho 18 channel và số lượng lớn videos ko phải 1 videos"*.

── VÌ SAO TỆP NÀY LÀ THỨ THIẾU LỚN NHẤT ──────────────────────────────────────────────────
`khung_hoi.nhip_tu_khuon(khuon, chu_the, ...)` nhận chủ thể làm THAM SỐ, và chỗ duy nhất
truyền tham số ấy là `_thu_vanished.py` — một tệp THỬ đọc từ dòng lệnh. Nghĩa là toàn bộ
đường "vì sao" chạy được đúng một tập mỗi lần có người gõ tên chủ thể vào.

Không có hồ chủ thể thì mọi thứ phía trên (18 lời hứa · 24 khuôn hỏi · cổng sự thật) đều là
một cỗ máy không có nguyên liệu.

── VÌ SAO HẠNG MỤC WIKIPEDIA, KHÔNG PHẢI DANH SÁCH VIẾT TAY ──────────────────────────────
Danh sách viết tay cạn sau vài trăm tập và phải viết lại bằng tay — tức nó là một hằng số
đội lốt một nguồn (§13.6). Hạng mục Wikipedia là một CÂY do hàng nghìn người duy trì: mỗi
lần thế giới có thêm một công ty phá sản, một sản phẩm bị khai tử, một vụ mất tích, thì cây
tự dài thêm mà không ai ở đây phải làm gì.

Và phải duyệt CẢ CÂY, không chỉ tầng đầu: "Defunct companies of the United States" có đúng
**14** trang thành viên trực tiếp, còn hàng nghìn trang nằm trong các hạng mục con (theo
bang · theo ngành · theo thập kỷ). Đếm một tầng rồi kết luận "hạng mục này nhỏ" là lỗi đã
mắc một lần trong repo này.

── HAI CỔNG ─────────────────────────────────────────────────────────────────────────────
1. **Bỏ trang KHÔNG phải chủ thể**: `List of …`, `Timeline of …`, trang định hướng, và mọi
   trang có ngoặc đơn phân loại kiểu `(disambiguation)`. Chúng đọc lên như chủ thể nhưng
   không có câu chuyện nào để kể.
2. **Đủ tư liệu**: `chu_de.ho_so` phải rút được đủ câu sự thật. Đây là cổng ĐẮT (một lượt
   mạng mỗi chủ thể) nên nó chạy LƯỜI — chỉ khi chủ thể sắp được dùng, không phải lúc quét
   hạng mục. Quét 2.000 chủ thể mà kiểm tư liệu cả 2.000 là trả tiền cho 1.990 tập chưa làm.

── SỔ ĐÃ DÙNG ───────────────────────────────────────────────────────────────────────────
Mỗi kênh giữ danh sách `(chủ thể, khuôn hỏi)` đã dựng. Một chủ thể được phép quay lại với
khuôn hỏi KHÁC — đó chính là phép nhân ở §19.6 — nhưng cùng một cặp thì không bao giờ hai
lần. Sổ để ở tệp JSON cạnh kho, không ở Firestore: nó chỉ cần đúng, không cần chia sẻ, và
hạn mức Firestore là tài nguyên dùng chung (§13.7).
"""
from __future__ import annotations

import io
import json
import os
import re
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "MM0-pipeline/1.0 (youtube explainer; contact via repo owner)"}
GOC = os.path.dirname(os.path.abspath(__file__))
DEM = os.path.join(GOC, "ho_chu_de.json")      # đệm cây hạng mục
SO = os.path.join(GOC, "so_chu_de.json")       # sổ (kênh -> các cặp đã dựng)

# Trang đọc lên như chủ thể mà không có chuyện để kể.
_BO = re.compile(r"^(list|lists|timeline|index|outline|glossary|history) of |"
                 r"\((disambiguation|surname|given name)\)$", re.I)


_LUC = 0.0        # lúc gọi Wikipedia gần nhất — xem `_NHIP`
_NHIP = 0.9       # giây tối thiểu giữa hai lệnh. Chạy thật ở 0,35 s trả `HTTP 429 Too Many
                  # Requests` cho 24/114 hạng mục — đây là số đo, không phải phòng xa.


def _goi(u: str) -> dict:
    """Trả JSON, hoặc NÉM khi không đọc được. Không trả `{}` — xem `duyet`."""
    global _LUC
    cuoi = ""
    for lan in range(4):
        # Nhịp DÙNG CHUNG với `chu_de._goi`: ba nơi mỗi nơi giữ nhịp riêng thì tổng nhịp
        # vẫn vượt trần (§13.7 — hạn mức là tài nguyên dùng chung, "số nhỏ" không phải bảo vệ).
        import chu_de as _CD
        cho = _CD.NHIP - (time.time() - _CD._LUC[0])
        if cho > 0:
            time.sleep(cho)
        _CD._LUC[0] = time.time()
        try:
            r = urllib.request.Request(u, headers=UA)
            return json.load(urllib.request.urlopen(r, timeout=40))
        except Exception as e:
            cuoi = str(e)[:60]
            # 429 cần nghỉ LÂU hơn hẳn lỗi mạng thường: nó là hàng rào có chủ ý, không phải
            # một gói tin rớt. Lùi 6/12/24 giây thay vì 1,5/3/4,5.
            time.sleep((6.0 if "429" in cuoi else 1.5) * (lan + 1))
    raise RuntimeError(cuoi or "không đọc được Wikipedia")


def _thanh_vien(cat: str, kind: str) -> list:
    u = ("https://en.wikipedia.org/w/api.php?action=query&format=json&list=categorymembers"
         f"&cmtitle=Category:{urllib.parse.quote(cat)}&cmlimit=500&cmtype={kind}")
    return [x["title"] for x in _goi(u).get("query", {}).get("categorymembers", [])]


def duyet(goc: str, sau: int = 2, tran_cat: int = 120) -> list:
    """Duyệt CÂY hạng mục, trả danh sách chủ thể đã lọc. Có đệm đĩa.

    `tran_cat` chặn trên số hạng mục duyệt, không trên số chủ thể: thứ tốn mạng là lượt hỏi
    hạng mục, nên trần phải đặt trên chính đại lượng ấy (§15.1).
    """
    dem = {}
    if os.path.exists(DEM):
        try:
            dem = json.load(io.open(DEM, encoding="utf-8"))
        except Exception:
            dem = {}
    khoa = f"{goc}|{sau}"
    # ── ĐỆM RỖNG = COI NHƯ CHƯA CÓ  (bắt được trong sản xuất, 7/9/2026) ──────────────────
    # Chốt chặn thêm lúc trước chỉ canh đường GHI ("hỏng thì đừng đệm"), và để hở đường ĐỌC:
    # một mục 0 đã lỡ nằm trong đệm từ lượt chạy cũ thì `duyet` trả thẳng cái 0 ấy MÃI MÃI,
    # không bao giờ quét lại. Đo thật: "Defunct companies of the United States" ra 0 chủ thể
    # trong khi cùng hạng mục ấy quét tay ra **2.080**. Vá một nhánh, để nguyên nhánh song
    # song (§6) — và nhánh còn hở là nhánh sống lâu hơn, vì đệm nằm trên đĩa.
    if dem.get(khoa):
        return dem[khoa]
    if khoa in dem:
        print(f"   ↻ đệm «{goc[:44]}» đang rỗng — quét lại thay vì tin nó")
    ra, hang, da, n, hong = set(), [(goc, 0)], set(), 0, 0
    while hang and n < tran_cat:
        c, d = hang.pop(0)
        if c in da:
            continue
        da.add(c)
        n += 1
        try:
            for t in _thanh_vien(c, "page"):
                if not _BO.search(t):
                    ra.add(t)
            if d < sau:
                for x in _thanh_vien(c, "subcat"):
                    hang.append((x.replace("Category:", ""), d + 1))
        except Exception as e:
            hong += 1
            print(f"   ⚠ không đọc được «{c[:44]}»: {str(e)[:44]}")
    # ── LƯỢT ĐỌC HỎNG THÌ KHÔNG ĐƯỢC GHI ĐỆM  (bắt được ngay lần đo đầu, 7/9/2026) ───────
    # Đo thật: "Discontinued products" ra **0 chủ thể** trong khi hỏi trực tiếp cùng hạng mục
    # ấy ra 20 trang. Không phải hạng mục rỗng — là lượt đọc hỏng, và bản đầu của hàm này ghi
    # thẳng cái 0 ấy vào `ho_chu_de.json`, tức **một trục trặc mạng vài giây khoá vĩnh viễn
    # một kênh không còn đề tài**, và không có gì báo.
    # `0` một mình luôn có hai nghĩa ngược nhau (§15.2). Hỏng thì trả về thứ đọc được, nói ra,
    # và KHÔNG đệm — lượt sau tự thử lại.
    # ── "KHÔNG ĐỆM KHI HỎNG" PHẢI CÓ NGƯỠNG, KHÔNG PHẢI TUYỆT ĐỐI  (đo 7/9/2026) ────────
    # Bản đầu: hỏng MỘT hạng mục là không đệm. Chạy thật ra 27/104 hỏng vì nhịp gọi 0,12 s bị
    # Wikipedia chặn — tức lượt nào cũng có lỗi, tức KHÔNG BAO GIỜ đệm được, tức mỗi lần dựng
    # lại quét 208 vòng mạng. Một chốt chặn tuyệt đối ở chỗ lỗi là chuyện BÌNH THƯỜNG thì nó
    # không bảo vệ gì, nó chỉ khoá tính năng lại (§13.8, phía hạ tầng).
    # Nới nhịp gọi lên 0,35 s để tỉ lệ hỏng về gần 0, VÀ cho phép đệm khi hỏng dưới 8% — kèm
    # ghi lại tỉ lệ ấy để lượt sau còn biết bản đệm này là bản đầy đủ hay bản thiếu.
    # Sàn `max(2, ...)` để lượt hỏng 100% ĐI QUA khi n nhỏ: quét 1 hạng mục hỏng 1 thì
    # `1 > max(2, 0.08)` là False -> vẫn đệm một danh sách rỗng. Đo thật, in ra đúng câu tự
    # mâu thuẫn: *"1/1 hạng mục đọc hỏng (100% — dưới ngưỡng), vẫn đệm"*. Một ngưỡng TỈ LỆ
    # phải đi kèm điều kiện tuyệt đối cho mẫu nhỏ, nếu không nó chỉ đúng ở mẫu lớn.
    if hong and (hong > n * 0.08 or n <= 4):
        print(f"   ⚠ {hong}/{n} hạng mục đọc hỏng ({hong/n*100:.0f}%) — KHÔNG ghi đệm, "
              f"lượt sau thử lại (tạm có {len(ra)} chủ thể)")
        return sorted(ra)
    if hong:
        print(f"   ⓘ {hong}/{n} hạng mục đọc hỏng ({hong/n*100:.0f}% — dưới ngưỡng), vẫn đệm")
    # Chốt thứ hai: KHÔNG đệm một danh sách RỖNG kể cả khi mọi lượt đọc đều "thành công".
    # Một hạng mục gốc rỗng gần như luôn là tên viết sai hoặc một dạng hỏng chưa nhận ra —
    # và đệm nó lại thì kênh ấy cạn đề tài vĩnh viễn mà không có gì báo. Rẻ hơn nhiều so với
    # việc đi tìm nguyên nhân sáu tháng sau.
    if not ra:
        print(f"   ⚠ «{goc[:48]}» ra 0 chủ thể — KHÔNG đệm (nghi tên hạng mục sai)")
        return []
    dem[khoa] = sorted(ra)
    io.open(DEM, "w", encoding="utf-8").write(json.dumps(dem, ensure_ascii=False))
    return dem[khoa]


_LUC_BAI = [0.0]     # nhịp gọi riêng cho bước đọc BÀI VIẾT, xem `co_chuyen`
SANG = os.path.join(GOC, "so_sang.json")      # chủ thể -> số câu nhân quả đã đo


def _doc_sang() -> dict:
    if os.path.exists(SANG):
        try:
            return json.load(io.open(SANG, encoding="utf-8"))
        except Exception:
            pass
    return {}


def co_chuyen(gocs: list, san: int = 8, them: int = 6, sau: int = 2) -> list:
    """Chủ thể ĐÃ QUA cổng chuyện, và sàng thêm `them` chủ thể mới mỗi lượt gọi.

    ── VÌ SAO SÀNG DẦN, KHÔNG SÀNG MỘT LƯỢT  (7/9/2026) ──────────────────────────────────
    Cổng chuyện phải đọc bài viết -> một lượt gọi mạng cho MỖI chủ thể. Hồ có 2.175 chủ thể
    thì sàng hết một lượt là 2.175 vòng mạng cho một tập sắp dựng — trả tiền cho 2.000 tập
    chưa làm (§18.8: chi phí tỉ lệ với KÍCH THƯỚC kho trong khi việc thật tỉ lệ với PHẦN MỚI).

    Và không sàng gì thì mỗi lần dựng lại phải thử 10 chủ thể qua mạng rồi loại 7 — đo thật
    ở lượt chạy tối nay. Nên: đệm kết quả đã đo, mỗi lượt dựng chỉ sàng thêm vài chủ thể, và
    hồ đủ dùng lớn dần lên. Sàng rồi thì không bao giờ sàng lại.

    Tỉ lệ qua cổng đo được ~25% (2/8 mẫu hãng bay), nên sàng 6 chủ thể/lượt thì mỗi lượt hồ
    dày thêm ~1,5 chủ thể — nhanh hơn tốc độ tiêu thụ (1 chủ thể × 24 khuôn hỏi mỗi tập).
    """
    import chu_de as C
    da = _doc_sang()
    # ── CHI PHÍ MỖI LƯỢT GỌI PHẢI CÓ TRẦN  (đo 7/9/2026) ────────────────────────────────
    # Bản đầu duyệt CẢ BA gốc mỗi lần gọi. Đo thật: chỉ 1/3 gốc của `therules` có đệm, hai
    # gốc kia phải đi hết cây (~100 hạng mục × 0,9 s × 2 lượt hỏi ≈ 3 phút MỖI GỐC), nên sau
    # 5 phút chưa sàng nổi một chủ thể — và nếu lượt duyệt ấy lại đọc hỏng quá ngưỡng thì
    # không đệm, tức lượt sau trả đúng chừng ấy tiền.
    # Nay: dùng NGAY mọi gốc đã có đệm, và mỗi lượt chỉ mở THÊM MỘT gốc mới. Hồ dùng được
    # ngay từ lượt đầu, và vẫn dày lên đều. §18.8 — chi phí phải tỉ lệ với PHẦN MỚI.
    dem_dia = {}
    if os.path.exists(DEM):
        try:
            dem_dia = json.load(io.open(DEM, encoding="utf-8"))
        except Exception:
            dem_dia = {}
    het, chua_mo = [], []
    for g in gocs:
        if dem_dia.get(f"{g}|{sau}"):
            het.extend(x for x in dem_dia[f"{g}|{sau}"] if x not in het)
        else:
            chua_mo.append(g)
    # Mở gốc mới CHỈ KHI hồ hiện có đã cạn. Bản trước mở thêm một gốc ở MỌI lượt gọi, và một
    # lượt duyệt cây mất vài phút không in gì — nên bước sàng bị chặn đứng và sau 4 phút vẫn
    # đúng 6 chủ thể được đo. Đo lại thì thấy tiến trình sống mà log rỗng: dấu hiệu của một
    # lượt chờ dài, không phải của một tiến trình chết.
    # Với "Defunct airlines" đã đệm 757 chủ thể thì không bao giờ cần mở thêm — hồ dư sức nuôi
    # hàng nghìn tập trước khi phải đi tìm gốc mới.
    if chua_mo and len(het) < 200:
        g = chua_mo[0]
        print(f"   🌳 hồ chỉ còn {len(het)} — mở thêm gốc «{g[:40]}»")
        het.extend(x for x in duyet(g, sau) if x not in het)
    if not het:
        return []
    dat = [x for x in het if da.get(x, -1) >= san]
    chua = [x for x in het if x not in da]
    moi = 0
    for ct in chua[:max(0, them)]:
        # `bai_viet` đi qua CÙNG một API với `_goi` nhưng KHÔNG chia sẻ nhịp gọi của nó, nên
        # bước sàng bắn liên tiếp và ăn 429: đo lượt đầu 4/6 bài đọc về 0 ký tự. Giãn cách ở
        # đây vì `chu_de` còn phục vụ nhiều chỗ khác, không nên đổi nhịp toàn cục của nó.
        cho = _NHIP - (time.time() - _LUC_BAI[0])
        if cho > 0:
            time.sleep(cho)
        _LUC_BAI[0] = time.time()
        try:
            van = C.bai_viet(ct) or ""
        except Exception:
            continue                      # mạng hỏng: KHÔNG ghi, để lượt sau đo lại
        # ── BÀI VIẾT RỖNG KHÔNG PHẢI "0 CÂU NHÂN QUẢ"  (đo 7/9/2026) ────────────────────
        # `bai_viet` trả "" khi đọc hỏng và KHÔNG ném, nên `except` ở trên không đỡ được.
        # Chạy thật với Wikipedia đang trả 429: **0/40 chủ thể đạt**, và cả 40 bị ghi sổ là
        # "0 câu nhân quả" VĨNH VIỄN — tức một lượt mạng xấu loại vĩnh viễn 40 chủ thể tốt.
        # Lần thứ ba trong ngày cùng một họ: đệm một phép đo HỎNG như thể nó là kết quả.
        if len(van) < 400:
            print(f"   ⚠ «{ct[:36]}»: bài viết đọc về {len(van)} ký tự — KHÔNG ghi sổ")
            continue
        n = len(C.cau_nhan_qua(van))
        da[ct] = n
        moi += 1
        if n >= san:
            dat.append(ct)
    if moi:
        io.open(SANG, "w", encoding="utf-8").write(json.dumps(da, ensure_ascii=False))
        print(f"   🔎 sàng thêm {moi} chủ thể · hồ ĐỦ CHUYỆN: {len(dat)}/{len(da)} đã đo "
              f"({len(het)} trong hồ)")
    return dat


def _so() -> dict:
    if os.path.exists(SO):
        try:
            return json.load(io.open(SO, encoding="utf-8"))
        except Exception:
            pass
    return {}


def da_dung(kenh: str) -> set:
    return set(tuple(x) for x in _so().get(kenh, []))


def ghi(kenh: str, chu_the: str, khuon: str) -> None:
    s = _so()
    s.setdefault(kenh, []).append([chu_the, khuon])
    io.open(SO, "w", encoding="utf-8").write(json.dumps(s, ensure_ascii=False))


def con_lai(kenh: str, gocs: list, khuons: list, sau: int = 2) -> int:
    """Số CẶP (chủ thể × khuôn) còn chưa dựng — trần lý thuyết của kênh này.

    Trả một con số có MẪU SỐ: `0` một mình có hai nghĩa ngược nhau (§15.2).
    """
    ct = set()
    for g in gocs:
        ct.update(duyet(g, sau))
    return len(ct) * len(khuons) - len(da_dung(kenh))


def tiep_tu(kenh: str, ct: list, khuons: list, so_luong: int = 1) -> list:
    """Như `tiep`, nhưng bốc từ MỘT danh sách chủ thể cho sẵn.

    ── VÌ SAO CẦN  (bắt được khi dựng bộ 1:3 đầu tiên, 8/9/2026) ─────────────────────────
    `tiep` bốc cặp trên CẢ hồ (757 chủ thể), trong khi chỉ những chủ thể ĐÃ QUA cổng chuyện
    mới dùng được — lúc ấy là 4. Xác suất 40 cặp đầu trúng một trong 4 chủ thể giữa 757 là
    gần bằng không, nên `vi_sao` báo *"không chủ thể nào đủ chuyện"* và rơi về bộ sinh cũ,
    dù hồ đã sàng ra chủ thể tốt. Cổng lọc đúng, phép BỐC sai nguồn.
    Cùng họ §15.1: cắt trước lọc sau. Ở đây là bốc trước lọc sau, và tập cần giữ chỉ chiếm
    0,5% hồ nên phép bốc gần như không bao giờ chạm tới nó.
    """
    if not ct or not khuons:
        return []
    P = len(ct) * len(khuons)
    buoc = next((b for b in (10007, 7919, 4001, 1009, 997, 101, 97, 31, 7, 3, 1) if P % b), 1)
    xong = da_dung(kenh)
    bam = 0
    for c in kenh:
        bam = (bam * 131 + ord(c)) % 1000003
    ra, i = [], 0
    while len(ra) < so_luong and i < P:
        k = (bam + i * buoc) % P
        cap = (ct[k % len(ct)], khuons[k // len(ct)])
        if cap not in xong and cap not in ra:
            ra.append(cap)
        i += 1
    return ra


def tiep(kenh: str, gocs: list, khuons: list, so_luong: int = 1, sau: int = 2) -> list:
    """`so_luong` cặp (chủ thể, khuôn) chưa dựng cho kênh này.

    Đi theo BƯỚC NGUYÊN TỐ CÙNG NHAU trên không gian tích thay vì lấy tuần tự: lấy tuần tự
    thì mười tập liền nhau đều là chủ thể vần A và cùng một khuôn hỏi — mỗi trục nhìn riêng
    đều trải hết mà bộ đôi thì đi thành vệt (§13.13 · §14.9).
    """
    ct = []
    for g in gocs:
        ct.extend(x for x in duyet(g, sau) if x not in ct)
    if not ct or not khuons:
        return []
    P = len(ct) * len(khuons)
    buoc = next((b for b in (10007, 7919, 4001, 1009, 997, 101, 97, 31, 7, 3, 1) if P % b), 1)
    xong = da_dung(kenh)
    ra, i = [], 0
    # Mốc xuất phát riêng cho từng kênh, viết TƯỜNG MINH — `hash()` của Python đổi theo mỗi
    # lần chạy nên máy anh và runner sẽ ra hai lịch khác nhau (§13.13, đã trả giá).
    bam = 0
    for c in kenh:
        bam = (bam * 131 + ord(c)) % 1000003
    while len(ra) < so_luong and i < P:
        k = (bam + i * buoc) % P
        cap = (ct[k % len(ct)], khuons[k // len(ct)])
        if cap not in xong and cap not in ra:
            ra.append(cap)
        i += 1
    return ra


if __name__ == "__main__":
    import sys
    gocs = sys.argv[1:] or ["Defunct companies of the United States", "Discontinued products"]
    tong = set()
    for g in gocs:
        r = duyet(g)
        print(f"{len(r):6}  {g}")
        tong.update(r)
    print(f"\nhợp lại, khử trùng: {len(tong)} chủ thể")
    print("vd:", ", ".join(sorted(tong)[:6]))
