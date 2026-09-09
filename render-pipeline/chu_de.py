#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHỦ THỂ CÓ THẬT — lấy câu sự thật kiểm chứng được từ Wikipedia.  (7/9/2026)

── VÌ SAO CÓ TỆP NÀY ──────────────────────────────────────────────────────────────────────
Anh: *"18 channel hiện tại... hơi khô khan, đọc ko ra gì, ko phải cái người ta muốn coi"*.
Anh đúng, và cái khô là do THIẾT KẾ chứ không do dựng kém: mười tám kênh ấy đều là kênh
ĐO LƯỜNG — *bao to · bao ồn · bao nặng · bao lâu*. Không có câu chuyện nào trong "một sân
bóng dài bao nhiêu", nên không có lý do để ai ở lại.

Bốn tệp tiêu đề anh gửi (14.103 tiêu đề) nói ngược lại: **17% mở bằng một CÁI TÊN CÓ THẬT**,
12% là *"How X did Y"*. Chủ thể là một thứ đã xảy ra ngoài đời — Dolly, MH370, Concorde,
Theranos. Đó vừa là chỗ có câu chuyện, vừa là chỗ ý tưởng không bao giờ cạn.

── VÌ SAO KHÔNG DÙNG WIKIDATA ─────────────────────────────────────────────────────────────
Phản xạ đầu của em là Wikidata: có cấu trúc, dễ đọc máy. Đo thật trên 8 chủ thể thì nó cho
**~2 sự kiện có số mỗi chủ thể**, Segway cho 0 — trong khi một tập cần 10–20. Wikidata giữ
những gì ĐIỀN ĐƯỢC VÀO Ô; câu chuyện thì nằm ở THÂN BÀI. Đo lại trên thân bài: Concorde 38
câu có số, MH370 31, Theranos 23, Chernobyl 19.

── RANH GIỚI KHÔNG ĐƯỢC VƯỢT ──────────────────────────────────────────────────────────────
Mọi con số đi vào sản phẩm phải là chuỗi **trích nguyên văn** từ bài, và hàm `kiem()` đối
chiếu ngược lại nguồn trước khi cho qua. AI được phép DIỄN ĐẠT quanh con số; nó không bao
giờ được cấp một con số. Thiếu dữ liệu thì trả rỗng và bỏ lượt — thà mất một video còn hơn
mất uy tín cả kênh (chép đúng ranh giới của `the_he_2.py`).
"""
from __future__ import annotations

import io
import json
import os
import re
import tempfile
import time
import urllib.parse
import urllib.request

# ── USER-AGENT PHẢI CÓ LIÊN HỆ THẬT — ĐÂY LÀ GỐC CỦA MỌI 429 ĐÊM NAY  (8/9/2026) ──
# Chính sách User-Agent của Wikimedia đòi định danh công cụ KÈM một địa chỉ liên hệ.
# Chuỗi cũ ghi "contact via repo owner" — nghe như có liên hệ mà KHÔNG PHẢI liên hệ,
# nên Wikimedia coi ta là bot ẩn danh và bóp cổ ngay. Đo tách bạch bằng `curl`:
#     UA cũ ("contact via repo owner")      -> HTTP 429
#     không UA                              -> HTTP 429
#     UA có URL repo                        -> HTTP 200  (wikipedia · wikidata · commons)
#
# Đây là §13.15 ở mức đắt nhất của cả đêm: em kết luận "Wikipedia đang chặn vì mình gọi
# nhiều", rồi dựng đồng hồ dùng chung, nới nhịp tự động, rút theo thời gian, lùi 6/12/24
# — cả một bộ máy để đi vòng qua một vấn đề mà nguyên nhân là MỘT DÒNG HEADER. Hai bộ
# 142 và 144 mất trắng vì nó, và hồ đề tài đọc về 0 ký tự suốt nhiều giờ.
# (Bộ máy nhịp vẫn giữ: nó đúng và cần khi thật sự bị giới hạn — chỉ là nó không phải
#  thứ đang hỏng.)
#
# KHÔNG đưa email cá nhân của anh vào header gửi bên thứ ba: đo được URL repo là ĐỦ.
UA = {"User-Agent": "MM0-pipeline/1.0 (+https://github.com/braydanamilio-spec/mq-vx-lab)"}

# Đơn vị PHẢI có mặt thì con số mới "cảm được" — một năm trần (1996) không nói lên quy mô.
# Danh sách này cố ý HẸP: rộng ra thì nhặt cả số trang, số hiệu, số chú thích.
# ── BỘ TRÍCH ĐẦU TIÊN QUÁ HẸP, VÀ EM ĐÃ KẾT LUẬN SAI TỪ NÓ  (7/9/2026) ────────────────────
# Bản đầu đòi SỐ + ĐƠN VỊ ĐO trong cùng một câu. Đo ra `Dolly (sheep)` chỉ 1 câu, `Simulation
# hypothesis` 0 câu, và em báo với anh rằng hồ chủ thể chỉ dùng được 12% — "không vô hạn".
#
# Sai. Nội dung KỂ CHUYỆN không sống bằng đơn vị đo; nó sống bằng NĂM, TUỔI, SỐ LẦN, SỐ CA,
# SỐ NGƯỜI. Nới đúng những thứ ấy rồi đo lại chính sáu chủ đề anh nêu:
#
#     Dolly 1 -> 22 câu · MH370 40 -> 129 · Simulation hypothesis 0 -> 18
#     Benjamin Franklin 8 -> 202 · Cloning 1 -> 80 · Sleep deprivation 26 -> 40
#
# Con số 12% đo chính bộ lọc của em, không đo nguồn. Đây là §13.15 ở dạng đắt nhất trong
# ngày: em lấy kết quả của một phép đo hẹp rồi dùng nó để BÁC một hướng đi mà anh đã chọn.
_DV = (r"%|percent|million|billion|trillion|thousand|km|kilometres?|miles?|kg|kilograms?|"
       r"pounds?|tons?|tonnes?|years?|months?|days?|hours?|minutes?|seconds?|people|"
       r"passengers?|crew|deaths?|dollars?|USD|feet|foot|metres?|meters?|degrees?|"
       r"times|copies|attempts?|embryos?|cases?|patients?|studies|subjects?|"
       r"votes?|books?|letters?|inventions?|experiments?")
# `\d{4}` bắt NĂM — mốc thời gian là xương sống của mọi câu chuyện, và bản đầu bỏ hết.
_CAU = re.compile(r"[^.\n]*?\b(?:\d{4}|\d[\d,\.]*\s*(?:" + _DV + r"))\b[^.\n]*\.")
_SO = re.compile(r"\b\d[\d,\.]*\b")


_LUC = [0.0]
# Nhịp tối thiểu giữa hai lệnh gọi Wikipedia. Đêm 8/9 em chạy song song ba thứ cùng gọi API
# này — quét cây hạng mục, sàng chủ thể, và dựng tập — mỗi thứ có (hoặc không có) nhịp riêng,
# nên tổng nhịp vượt xa mức Wikipedia chịu và MỌI lượt gọi trả `HTTP 429`. Lúc ấy `bai_viet`
# trả 0 ký tự, cổng chuyện chấm 0 câu nhân quả, hồ đề tài ra rỗng — cả dây chuyền đọc ra
# "không có dữ liệu" trong khi sự thật là "tôi tự chặn mình".
# Nhịp phải là của TIẾN TRÌNH, không của từng nơi gọi: ba nơi mỗi nơi 0,9 giây vẫn ra 0,3.
NHIP = float(os.environ.get("WIKI_NHIP") or 1.1)


# ── VÀ NHỊP PHẢI LÀ CỦA MÁY, KHÔNG CỦA TIẾN TRÌNH  (8/9/2026) ──────────────────────────
# Chú thích ngay trên đã viết đúng câu luật rồi dừng sớm MỘT NẤC: `_LUC` là biến MODULE, nên
# nó chỉ ghìm được các lời gọi trong CÙNG một tiến trình. Đêm nay có HAI tiến trình cùng gọi
# Wikipedia — bộ sàng chạy nền và lượt dựng bộ 1:3 — mỗi bên giữ đồng hồ riêng, nên nhịp thật
# còn một nửa. Đo được: bộ 135 ăn `429` ở **6/6 chủ thể**, `bai_viet` trả 0 ký tự, và dây
# chuyền kết luận "chưa có chủ thể đủ chuyện" trong khi hồ có 29 cái.
#
# Đúng họ §17.7: *mọi bộ đếm/đồng hồ dùng để CHẶN phải sống ở TỆP, không ở biến* — ở đó là
# trần ảnh đếm bằng thuộc tính hàm trong khi mỗi tập là một tiến trình riêng, ở đây là đồng
# hồ nhịp. Giữ `flock` TRONG lúc ngủ thì hai tiến trình tự xếp hàng, không cần biết nhau.
#
# Hỏng mềm ở mọi nhánh: đây là bước tối ưu, hệ thống tệp khoá chặt cũng không được làm chết
# đường lấy tư liệu (§13.3). Trên Actions mỗi luồng là một RUNNER riêng nên tệp không dùng
# chung — và đúng thế: ở đó mỗi máy một IP, nhịp theo MÁY mới là đơn vị đúng.
_LUC_TEP = os.path.join(tempfile.gettempdir(), "mm0_wiki_nhip")


# ── NHỊP TỰ NỚI KHI BỊ CHẶN, VÀ NỚI CHO CẢ MÁY  (8/9/2026) ─────────────────────────────
# Đưa đồng hồ ra tệp đã cắt 429 từ **4,7 xuống 2,0 lượt mỗi vòng sàng** (đo trên chính log:
# 118/25 vòng -> 26/13 vòng). Giảm 57% nhưng chưa hết — tức 1,1 giây vẫn có lúc quá nhanh.
#
# Không đi đoán một con số mới: Wikipedia không công bố ngưỡng cho lượt gọi ẩn danh, nên mọi
# con số gõ tay ở đây đều là §13.1 lặp lại. Thay vào đó ĐỌC chính lời từ chối — gặp 429 thì
# nới nhịp, qua trót lọt thì rút dần về. Và nới trong TỆP, vì bên bị chặn không nhất thiết
# là bên gây ra: hai tiến trình dùng chung một IP thì phải cùng chậm lại.
_NHIP_TRAN = 12.0


def _doc_so_tep(f):
    try:
        f.seek(0)
        phan = (f.read() or "").split()
        return float(phan[0]), (float(phan[1]) if len(phan) > 1 else NHIP)
    except Exception:
        return 0.0, NHIP


def _cho_nhip() -> None:
    try:
        import fcntl
        with open(_LUC_TEP, "a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            truoc, nhip = _doc_so_tep(f)
            nhip = min(max(nhip, NHIP), _NHIP_TRAN)
            # ── RÚT THEO THỜI GIAN, KHÔNG CHỈ THEO SỐ LƯỢT GỌI  (8/9/2026) ─────────────
            # Bản đầu chỉ rút 3% mỗi lượt gọi TRÓT LỌT. Đo sau vài giờ chạy thật: nhịp nằm
            # đúng ở TRẦN 12,0 giây trong khi 40 dòng log gần nhất KHÔNG có lượt 429 nào —
            # tức hàng rào đã hết từ lâu mà mình vẫn tự trói. Vì bộ sàng nghỉ giữa các vòng,
            # không có lượt gọi nào để mà rút, nên giá trị cũ nằm lại vĩnh viễn.
            # Cùng họ §15.19: một cơ chế phòng thủ kẹt ở mức cao nhất thôi bảo vệ và chỉ còn
            # làm chậm — ở đó là cổng đỏ vĩnh viễn, ở đây là nhịp 12 giây cắt sản lượng 11 lần.
            # Thời gian trôi cũng là bằng chứng "đã hết bị chặn", nên nó phải được tính.
            _im = max(0.0, time.time() - truoc)
            if _im > 60:
                nhip = max(NHIP, nhip * (0.5 ** (_im / 900.0)))
            cho = nhip - (time.time() - truoc)
            if 0 < cho <= nhip:
                time.sleep(cho)
            # rút dần về nhịp nền sau mỗi lượt trót lọt — nới thì nhanh, rút thì chậm
            f.seek(0); f.truncate()
            f.write(f"{time.time()} {max(NHIP, nhip * 0.97)}"); f.flush()
        _LUC[0] = time.time()
        return
    except Exception:
        pass
    cho = NHIP - (time.time() - _LUC[0])
    if cho > 0:
        time.sleep(cho)
    _LUC[0] = time.time()


def _nong_nhip() -> None:
    """Bị 429 thì nới nhịp cho CẢ MÁY, không chỉ cho tiến trình gặp nó."""
    try:
        import fcntl
        with open(_LUC_TEP, "a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            truoc, nhip = _doc_so_tep(f)
            f.seek(0); f.truncate()
            # ── LẦN 429 ĐẦU TIÊN PHẢI NHẢY THẲNG TỚI MỨC AN TOÀN  (8/9/2026) ───────────
            # Bộ 144 mất trắng: 429 ở 7/7 chủ thể, dù sàng đã tắt và lùi đã 6/12/24. Nhưng đo
            # ngay sau đó, ở nhịp 12s, một lượt gọi đọc về **83.228 ký tự bình thường** — tức
            # Wikipedia KHÔNG chặn ta, hệ chỉ chưa tới được mức an toàn.
            #
            # Gốc: nhịp khởi từ 1,1s rồi nhân 1,8× sau TỪNG lần 429 (1,1 -> 2,0 -> 3,6 -> 6,4).
            # Trong lúc leo, mỗi chủ thể chỉ có 3 lượt thử và chúng bị đốt hết ở những nhịp còn
            # quá nhanh; sáu chủ thể ứng viên chết sạch trước khi nhịp kịp lên. Hệ "học" đúng
            # nhưng học bằng chính hàng hoá của mình.
            #
            # 429 không phải tín hiệu mờ để dò dần — nó là câu trả lời DỨT KHOÁT (§19.20).
            # Nghe một lần là nhảy thẳng tới mức đã đo được là chạy tốt, rồi mới rút dần.
            _AN_TOAN = 6.0
            f.write(f"{time.time()} {min(_NHIP_TRAN, max(nhip * 1.8, _AN_TOAN))}"); f.flush()
    except Exception:
        pass


def _goi(url: str, timeout: int = 25) -> dict:
    _cho_nhip()
    r = urllib.request.Request(url, headers=UA)          # §13.15: thiếu User-Agent -> CDN chặn 403
    try:
        return json.load(urllib.request.urlopen(r, timeout=timeout))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            _nong_nhip()                 # 429 là hàng rào có chủ ý (§19.20) — nghe nó, đừng đoán
        raise


_DEM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_dem_wiki")
LY_DO_CUOI = [""]        # vì sao lượt đọc gần nhất trả rỗng — xem chú thích trong `bai_viet`


_DEM_ANH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "so_anh_co.json")


def so_anh_co(ten: str) -> int:
    """Đếm ảnh TỰ DO dùng được của một chủ thể. -1 nếu không hỏi được.

    ── VÌ SAO ĐẾM TRƯỚC KHI DỰNG  (anh: *"tất cả videos đều có ảnh thật chứ"*, 8/9/2026) ──
    Anh chốt nền chỉ được là ảnh tư liệu thật. Nhưng đo 14 bộ đã dựng thì ảnh thật đi theo ĐỘ
    NHẬN BIẾT của chủ thể gần như tuyến tính: Kodak (87.057 lượt/90 ngày) cho 16 ảnh, South
    Sea Company (35.493) cho 7/12 nhịp, còn Charter One Airlines (53 lượt) cho ĐÚNG MỘT.

    Nên muốn mọi tập có ảnh thì phải siết ở khâu CHỌN CHỦ THỂ, không phải khâu tìm ảnh. Và
    siết bằng chính thứ mình cần — SỐ ẢNH — chứ không bằng một thứ thay thế như lượt xem:
    lượt xem chỉ tương quan, còn số ảnh là điều kiện thật.

    Đệm ra đĩa vì cùng một chủ thể sẽ được cân nhắc lại ở nhiều lượt và nhiều kênh — 18 kênh
    rút từ CÙNG hai họ hạng mục (`vanished` 11 · `unsolved` 7), nên đệm dùng chung là đáng.
    """
    import json as _j
    k = " ".join(str(ten or "").split())
    if not k:
        return -1
    try:
        d = _j.load(io.open(_DEM_ANH, encoding="utf-8")) if os.path.exists(_DEM_ANH) else {}
    except Exception:
        d = {}
    if k in d:
        return int(d[k])
    n = -1
    try:
        import anh_tu_do as _A
        n = len(_A.anh_cua(k, toi_da=12) or [])
        if n < 3:
            n += len(_A.anh_cua(k, toi_da=12, commons=True) or [])
    except Exception:
        return -1
    try:
        d[k] = n
        io.open(_DEM_ANH, "w", encoding="utf-8").write(_j.dumps(d, ensure_ascii=False))
    except Exception:
        pass
    return n


def bai_viet(ten: str) -> str:
    """Thân bài Wikipedia dạng chữ thuần. `redirects=1` là bắt buộc.

    Bản đầu của em thiếu nó và bốn trong tám chủ thể trả về CHUỖI RỖNG — em suýt kết luận
    "Wikipedia không có bài về Benjamin Franklin". Trang đổi hướng trả `pages` không có
    `extract`, và rỗng thì trông y hệt không tồn tại (§15.2).
    """
    # ── ĐỆM RA ĐĨA, VÀ NÓ KHÔNG PHẢI TỐI ƯU MÀ LÀ ĐIỀU KIỆN ĐÚNG ĐẮN  (7/9/2026) ─────────
    # Đo năng suất khuôn×chủ thể ra 10% và em suýt kết luận thiết kế hỏng. Kiểm lại: `Kodak`
    # trả 40 câu ở lượt trước và 0 câu ở lượt sau — Wikipedia CHẶN NHỊP GỌI (429), nên phép
    # đo đang đo chính cái rate-limit của em chứ không đo thiết kế (§13.15, lần thứ năm
    # trong ngày).
    #
    # Một phép đo lặp lại trên cùng dữ liệu mà cho hai kết quả khác nhau thì nó chưa đo được
    # gì. Đệm ra đĩa làm phép đo LẶP LẠI ĐƯỢC, và đó là điều kiện để tin bất kỳ con số nào
    # ở đây — chưa nói tới chuyện nó cứu hạn mức khi chạy hàng nghìn tập.
    import hashlib
    os.makedirs(_DEM, exist_ok=True)
    k = hashlib.sha1(ten.encode("utf-8")).hexdigest()[:20]
    d = os.path.join(_DEM, k + ".txt")
    # 8/9 — TỆP RỖNG LÀ "CHƯA CÓ", KHÔNG PHẢI "BÀI NÀY RỖNG".
    # Đệm này CHƯA BAO GIỜ CHẠY: `chu_de` không hề `import io`, nên cả lượt đọc lẫn lượt ghi
    # ném `NameError` và hai `except` trần nuốt sạch (§15.2). Hậu quả đo đêm 8/9: mọi lượt
    # `bai_viet` đều đi mạng, và log vòng quét ra 392/500 dòng «đọc về 0 ký tự» — tức 78% là
    # 429 của chính nhịp gọi mình. Docstring ngay trên kể rất kỹ về một cơ chế không tồn tại
    # (§15.12). Và một tệp 0 byte còn sót từ trước bản vá "không ghi khi hỏng" sẽ khoá cứng
    # đúng chủ thể ấy mãi mãi, nên rỗng phải đọc là CHƯA CÓ.
    if os.path.exists(d):
        try:
            _v = io.open(d, encoding="utf-8").read()
            if _v.strip():
                return _v
        except Exception:
            pass
    u = ("https://en.wikipedia.org/w/api.php?action=query&format=json&redirects=1"
         f"&prop=extracts&explaintext=1&titles={urllib.parse.quote(ten)}")
    # ── THỬ LẠI, VÀ NÓI RA LÝ DO  (8/9/2026) ────────────────────────────────────────────
    # `except: return ""` nuốt sạch nguyên nhân, nên một lượt 429 chập chờn đọc ra y hệt
    # "Wikipedia không có bài này" — và mọi phép đo phía sau (số câu nhân quả, cổng chuyện,
    # hồ đề tài) đều nhận một số 0 KHÔNG CÓ MẪU SỐ (§15.2). Đo đêm 8/9: `bai_viet` trả 0 ký
    # tự cho ba chủ thể trong khi lệnh gọi THÔ tới đúng URL ấy trả 39.420 ký tự vài giây sau
    # — tức lỗi chập chờn, không phải bài không tồn tại. Một lần thử là chưa đủ.
    # ── RỖNG PHẢI KHAI VÌ SAO  (8/9/2026) ───────────────────────────────────────────────
    # Log vòng quét ra 11.802 dòng «đọc về 0 ký tự» và **0 dòng "hỏng sau 3 lần"** — tức mọi
    # lượt rỗng đều là HTTP 200, không phải lỗi mạng. Nhưng cùng những tên ấy đọc lại ở tiến
    # trình khác ra 272–4.632 ký tự, nên "0" đang gộp ít nhất ba chuyện khác hẳn nhau: trang
    # không tồn tại · trang có mà không có `extract` · đọc hỏng. Ba chuyện ấy dẫn tới ba hành
    # động khác nhau, mà chúng in ra CÙNG một dòng chữ (§15.2: số 0 phải có mẫu số).
    # Ghi lý do vào `LY_DO_CUOI` để chỗ gọi in ra, thay vì đoán như em vừa đoán cả buổi.
    v, cuoi = "", ""
    for lan in range(3):
        try:
            p = list((_goi(u).get("query") or {}).get("pages", {}).values())
            v = (p[0].get("extract") or "") if p else ""
            if not v:
                LY_DO_CUOI[0] = ("trang KHÔNG tồn tại" if (p and "missing" in p[0])
                                 else "trang có nhưng KHÔNG có extract" if p
                                 else "API trả 200 mà không có pages")
            break
        except Exception as e:
            cuoi = str(e)[:60]
            # ── LÙI 6/12/24 KHI BỊ 429, KHÔNG PHẢI 5/10  (8/9/2026) ────────────────────
            # §19.20 đã đo nhịp an toàn của Wikipedia và ghi rõ: gặp 429 thì lùi 6/12/24 giây
            # *"chứ không phải 1,5/3/4,5 — 429 là hàng rào có chủ ý, không phải một gói tin
            # rớt"*. Chỗ này vẫn còn 5/10, tức luật đã viết mà một nơi gọi chưa theo.
            # Đo được hậu quả: bộ 142 mất trắng vì 5/6 chủ thể ứng viên đều ăn 429 trong cùng
            # một cửa sổ ngắn — ba lần thử tiêu hết trong 15 giây rồi bỏ cuộc.
            time.sleep((6.0 * (2 ** lan)) if "429" in cuoi else 1.5 * (lan + 1))
    if not v and cuoi:
        LY_DO_CUOI[0] = f"đọc hỏng: {cuoi}"
        print(f"   ⚠ bai_viet «{ten[:34]}» hỏng sau 3 lần: {cuoi}")
        return ""                      # hỏng thì KHÔNG ghi đệm — đệm một chuỗi rỗng là khoá
    if v:                              # cứng cái hỏng lại mãi mãi
        try:
            io.open(d, "w", encoding="utf-8").write(v)
        except Exception:
            pass
    return v


# ── CÂU KHÔNG CÓ SỐ VẪN KIỂM CHỨNG ĐƯỢC  (7/9/2026) ───────────────────────────────────────
# Đưa 22 câu CÓ SỐ của Kodak cho mô hình chọn, nó trả về RỖNG — và nó đúng: 22 câu ấy toàn
# niên đại thành lập (1880 · 1884 · 1888), không câu nào giải thích cái gì giết Kodak.
#
# Gốc là ràng buộc của chính em: chỉ giữ câu CÓ SỐ. Nhưng câu NHÂN QUẢ — thứ trả lời "vì
# sao" — thường không có số ("failed to transition to digital photography"). Em tự bỏ đói
# mô hình rồi trách nó không chọn được.
#
# Và ràng buộc ấy đặt sai chỗ: một câu TRÍCH NGUYÊN VĂN kiểm chứng được dù không có số —
# phép kiểm là "câu này có trong bài không", so chuỗi chính xác. SỐ chỉ cần cho cái THẺ trên
# màn hình, không cần cho SỰ THẬT. Nên lấy cả hai loại, đánh dấu loại nào có số, rồi khâu
# dựng cho câu có số thành nhịp `so_lieu` và câu không số thành nhịp `canh`.
# ── HAI HỌ CHỮ CÒN THIẾU  (đo 90 bài, 8/9/2026) ──────────────────────────────────────────
# Đo sổ sàng: 18,4% chủ thể qua cổng ≥8 câu, và 3.800 chủ thể đứng ở 1–3 câu — trong đó một
# nửa có bài DÀY (trung vị 3.380 ký tự). Bài dày mà chấm 1–3 là dấu hiệu bộ trích hẹp, không
# phải chủ thể nghèo chuyện (§19.5: phép đo này đo nguồn, hay đo chính bộ lọc của mình?).
#
# Đọc tay 54 câu bị loại của «LBRY» — bài 8.024 ký tự, chấm 2 câu. Phần lớn đúng là câu MÔ TẢ
# và loại đúng. Nhưng bốn câu bị bỏ sót lại là chính cái chết của chủ thể:
#   «…Securities and Exchange Commission which FOUND THAT LBRY had sold unregistered securities»
#   «It STOPPED being supported in December 2019, IN FAVOR OF LBRY, Inc.»
#   «Odysee was split… AS LBRY FACED A LAWSUIT…»
# Thiếu hẳn hai họ: ĐỘNG TỪ KẾT CỤC (kiện · phán quyết · thu hồi giấy phép · giải thể) và
# LIÊN TỪ NHÂN QUẢ (due to · as a result · prompted · amid).
#
# ── VÀ MỘT BẢN NỚI ĐÃ BỊ BÁC  (§13.21: đọc tay ca được NHẬN, không chỉ đếm) ──────────────
# Bản nới đầu thêm cả `acquired · merged · recalled · stopped · closed · ruled · found that`.
# Nó cho 1,87× — nghe hay hơn hẳn. Đọc tay thì «Republic New York» thêm 11 câu mà 6 câu đầu
# đều là *"in 1974, it ACQUIRED Kings Lafayette Bank"*: một NHẬT KÝ THÂU TÓM, đúng dạng đã
# làm hỏng tập Periscope (§19.19 — kịch bản tụt thành nhật ký cập nhật phiên bản).
# Và `recalled` trong «"The ambiance was very special there," RECALLED Bob Gibson» là NHỚ LẠI,
# không phải thu hồi — §13.22: một chữ hai nghĩa là chữ không dùng làm cổng được.
#
# Nên giữ bản 1,47×: mỗi chữ dưới đây chỉ có MỘT nghĩa, và nghĩa ấy là kết thúc hoặc nguyên
# nhân. 0,4× còn lại của bản kia mua bằng rác, và rác đi thẳng lên màn hình.
_CAU_CHUYEN = re.compile(r"[^.\n]*?\b(?:because|after|when|until|failed|refused|declined|"
                         r"collapsed|bankrupt|replaced|abandoned|banned|lost|blamed|"
                         r"led to|resulted|caused|forced|never|no longer|instead|"
                         # kết cục — không lẫn nghĩa nào khác
                         r"ceased|shut down|dissolved|liquidated|seized|sued|lawsuit|"
                         r"convicted|indicted|fined|revoked|grounded|discontinued|halted|"
                         r"expelled|stripped of|filed for bankruptcy|filed for Chapter|"
                         r"went bankrupt|"
                         # liên từ nhân quả
                         r"due to|owing to|as a result|prompted|triggered|sparked|"
                         r"in favor of|amid |over allegations)\b"
                         r"[^.\n]*\.")


def cau_nhan_qua(van: str, toi_da: int = 30) -> list[dict]:
    """Câu mang QUAN HỆ NHÂN QUẢ, kể cả khi không có số. Vẫn nguyên văn từ nguồn."""
    ra, thay = [], set()
    for c in _CAU_CHUYEN.findall(van or ""):
        c = " ".join(c.split())
        if not (34 < len(c) < 215) or c in thay:
            continue
        thay.add(c)
        ds = [x for x in _SO.findall(c) if len(x) > 1]
        ra.append({"cau": c, "so": ds[0] if ds else "", "moi_so": ds})
        if len(ra) >= toi_da:
            break
    return ra


def cau_su_that(van: str, toi_da: int = 40) -> list[dict]:
    """Câu có SỐ KÈM ĐƠN VỊ, kèm chính con số để cổng đối chiếu ngược."""
    ra, thay = [], set()
    for c in _CAU.findall(van):
        c = " ".join(c.split())
        if not (34 < len(c) < 215) or c in thay:
            continue
        ds = [x for x in _SO.findall(c) if len(x) > 1 or x != "1"]
        if not ds:
            continue
        thay.add(c)
        ra.append({"cau": c, "so": ds[0], "moi_so": ds})
        if len(ra) >= toi_da:
            break
    return ra


def kiem(so: str, nguon: str) -> bool:
    """Con số này có THẬT nằm trong nguồn không.

    Cổng cuối trước khi một con số được phép lên màn hình. So trên chuỗi đã bỏ dấu phẩy để
    `239` khớp `239` lẫn `2,39` viết khác — nhưng KHÔNG nới hơn thế: nới nữa thì `39` khớp
    `1939` và cổng thành vô dụng.
    """
    if not so:
        return False
    g = so.replace(",", "")
    return g in nguon.replace(",", "")


# ══════════════════════════════════════════════════════════════════════════════════════════
# ĐỔI ĐƠN VỊ SANG HỆ MỸ — Ở NGUỒN, TRƯỚC KHI AI NHÌN THẤY
# ══════════════════════════════════════════════════════════════════════════════════════════
# §12.13 dặn từ 1/9: *"kênh Mỹ thì ĐƠN VỊ phải Mỹ"* — người xem Mỹ đọc "384,400 kilometres"
# là biết ngay không phải kênh của mình. `cham_kich_ban.KHONG_MY` có canh, nhưng nó chỉ CHẤM
# ĐIỂM (trục `don_vi_my`, trần 10) — và §13.3 đã trả giá cho đúng chuyện này: *một luật chỉ
# trừ điểm là một luật tuỳ chọn*. Đo bộ 215: hai nhịp đọc *"10,000 metric tons"* và
# *"1,230 metric tons"*, lọt sạch. `\btonnes?\b` của bảng ấy còn không khớp "metric tons".
#
# Ba nấc của §13.23 nói rõ nấc nào: đây là lỗi MÁY SỬA ĐƯỢC (một phép nhân), nên máy sửa —
# không chặn, không trừ điểm, không tiêu một vòng gọi AI.
#
# Và sửa Ở NGUỒN chứ không ở lời thoại đã sinh, vì hai lý do:
#   · mô hình không bao giờ NHÌN THẤY con số mét, nên nó không thể chép lại
#   · cổng chặn số bịa đối chiếu lời thoại với CHÍNH văn bản này — sửa ở đây thì hai bên
#     nhất quán; sửa ở lời thoại thì con số đã đổi sẽ bị chính cổng ấy tố là bịa
#
# Không vi phạm §19.3 (*AI không bao giờ được cấp một con số*): con số ở đây do PYTHON nhân,
# từ một con số có thật trong nguồn.
_QUY_DOI = [
    # thứ tự QUAN TRỌNG: cụm dài trước, nếu không "square kilometres" bị "kilometres" ăn mất,
    # và "metric ton" bị "ton" ăn mất.
    (r"square\s+kilomet(?:re|er)s?|km(?:2|²)\b", 0.386102, "square mile", "square miles"),
    (r"metric\s+tons?|tonnes?",                   1.10231,  "ton", "tons"),
    (r"kilomet(?:re|er)s?\s+per\s+hour|km/h\b|kph\b", 0.621371, "mph", "mph"),
    (r"kilomet(?:re|er)s?|\bkm\b",               0.621371, "mile", "miles"),
    (r"centimet(?:re|er)s?|\bcm\b",              0.393701, "inch", "inches"),
    (r"millimet(?:re|er)s?|\bmm\b",              0.0393701, "inch", "inches"),
    (r"kilograms?|\bkg\b",                       2.20462,  "pound", "pounds"),
    (r"hectares?|\bha\b",                        2.47105,  "acre", "acres"),
    (r"lit(?:re|er)s?",                            0.264172, "gallon", "gallons"),
    (r"met(?:re|er)s?\b",                         3.28084,  "foot", "feet"),
]


def _lam_tron_theo_nguon(goc: str, moi: float) -> str:
    """Làm tròn kết quả về ĐÚNG độ chính xác mà nguồn ngụ ý.

    "10,000" là bội của 1.000 nên nguồn chỉ khẳng định tới hàng nghìn — trả về 11.023,1 là
    giả vờ chính xác hơn nguồn. Ngược lại "1,230" là bội của 10 nên giữ tới hàng chục.
    Đây không phải chuyện thẩm mỹ: một con số chính xác hơn nguồn là một con số BỊA.
    """
    g = goc.replace(",", "")
    if "." in g:                                   # nguồn có phần thập phân -> giữ đúng số chữ số
        n = len(g.split(".", 1)[1])
        return f"{round(moi, n):,.{n}f}"
    try:
        iv = int(g)
    except ValueError:
        return f"{moi:,.0f}"
    # Bước làm tròn = ước số 10^k LỚN NHẤT của nguồn, NHƯNG chặn trên ở `|iv|/10` để kết quả
    # còn ít nhất hai chữ số có nghĩa. Bản đầu không chặn: "10,000 metric tons" lấy bước
    # 10.000, và 11.023 làm tròn về **10.000** — tức phép đổi chạy xong mà con số không đổi
    # một đơn vị nào, đọc y hệt như chưa đổi. Một phép làm tròn nuốt trọn phép đổi thì nó
    # không phải làm tròn nữa (§15.2: kết quả bằng đầu vào có hai nghĩa ngược nhau).
    buoc, tran = 1, max(1, abs(iv) // 10)
    for b in (1000000, 100000, 10000, 1000, 100, 10):
        if iv and iv % b == 0 and b <= tran:
            buoc = b
            break
    return f"{int(round(moi / buoc)) * buoc:,}"


def sang_don_vi_my(van: str) -> str:
    """Đổi mọi lượng hệ mét trong văn bản nguồn sang đơn vị Mỹ. Không đổi thì trả nguyên."""
    if not van:
        return van
    t = van
    # Nhiệt độ trước: nó là phép AFFINE, không phải phép nhân, nên không dùng chung khuôn.
    def _do(m):
        try:
            c = float(m.group(1).replace(",", ""))
        except ValueError:
            return m.group(0)
        return f"{_lam_tron_theo_nguon(m.group(1), c * 9 / 5 + 32)}°F"   # giữ nguyên lối viết °
    t = re.sub(r"(-?[\d,]+(?:\.\d+)?)\s*(?:°\s*C\b|degrees?\s+Celsius\b)", _do, t, flags=re.I)

    for rx, he, it, nhieu in _QUY_DOI:
        def _nhan(m, he=he, it=it, nhieu=nhieu):
            try:
                v = float(m.group(1).replace(",", ""))
            except ValueError:
                return m.group(0)
            ra = _lam_tron_theo_nguon(m.group(1), v * he)
            # "1 mile" chứ không phải "1 miles". So bằng GIÁ TRỊ, không bằng chuỗi đã cắt
            # đuôi: bản đầu dùng `rstrip("0")` nên "10,000" thành "1" và cho ra "10,000 ton".
            try:
                dv = it if abs(float(ra.replace(",", ""))) == 1 else nhieu
            except ValueError:
                dv = nhieu
            return f"{ra} {dv}"
        t = re.sub(r"([\d,]+(?:\.\d+)?)\s*(?:" + rx + r")", _nhan, t, flags=re.I)
    return t


def ho_so(ten: str) -> dict:
    """{ten, van, cau[]} — rỗng khi không đủ sự thật, và KHÔNG đoán bù."""
    # Đổi đơn vị NGAY SAU khi đọc bài, trước mọi phép trích: cả `cau_su_that` lẫn
    # `cau_nhan_qua` đều đọc từ đây, nên một chỗ sửa là mọi tầng dưới sạch (§13.5).
    van = sang_don_vi_my(bai_viet(ten))
    cs = cau_su_that(van)
    nq = cau_nhan_qua(van)
    thay = {c["cau"] for c in cs}
    gop = cs + [c for c in nq if c["cau"] not in thay]
    return {"ten": ten, "van": van, "cau": cs, "nhan_qua": nq, "tat_ca": gop,
            "du": len(gop) >= 8}


# ══════════════════════════════════════════════════════════════════════════════════════════
# CỔNG KIỂM MỆNH ĐỀ — thứ chặn "Theranos worked"
# ══════════════════════════════════════════════════════════════════════════════════════════
# ── VÌ SAO KIỂM SỐ LÀ KHÔNG ĐỦ  (đo 7/9/2026) ─────────────────────────────────────────────
# Ghép hook bằng khuôn trên sự thật đã trích, ba câu đầu tiên máy sinh ra:
#
#     "They built it. 60,000 of them are left."   -> 60.000 là CHI PHÍ chương trình Concorde,
#                                                    không phải số máy bay còn lại
#     "Theranos worked. That was the problem."    -> Theranos KHÔNG hoạt động; đó là cả vụ án
#     "What Chernobyl disaster looked like in..." -> vỡ ngữ pháp
#
# Và `kiem()` cho CẢ BA đi qua, vì `60,000` có thật trong bài. Cái sai không nằm ở con số mà
# ở MỆNH ĐỀ gắn vào con số — một chuỗi chữ số đúng có thể mang một câu hoàn toàn bịa.
#
# Ở kênh đo lường, số do Python tính nên không ai gán nghĩa sai được: sai nhất là NHÀM. Ở kênh
# câu chuyện, "Theranos worked" là một khẳng định sai về một vụ án hình sự có thật — không
# phải lỗi thẩm mỹ mà là rủi ro mất kênh. Nên cổng phải đổi đại lượng: từ "con số có trong
# nguồn không" sang "CÂU NÀY có nói quá điều nguồn nói không".
#
# ── BA PHÉP, VÀ VÌ SAO ĐỦ BA ──────────────────────────────────────────────────────────────
#   1. SỐ phải nằm trong ĐÚNG CÂU NGUỒN, không phải trong cả bài. Đây là chỗ "60,000" chết:
#      nó có trong bài, không có trong câu nói về số máy bay còn lại.
#   2. TỪ NỘI DUNG phải bắt rễ ở câu nguồn. Một câu diễn đạt lại được phép đổi cách nói,
#      không được phép mang vào một khái niệm nguồn không có. "worked" chết ở đây.
#   3. PHỦ ĐỊNH phải cùng chiều. Nguồn nói "not approved" mà câu nói "approved" là lật nghĩa
#      trong khi mọi từ đều bắt rễ — phép 2 một mình không bắt được.
#
# Cổng này CHẶT CÓ CHỦ Ý: nó thà chặn một câu diễn đạt hay còn hơn cho qua một câu sai. Đó là
# đánh đổi đúng chiều ở ngách này, và ngược hẳn với ngách hài (§13.8) nơi bắt oan mới là hại.
_DUNG = {
    "the","a","an","of","in","on","at","to","for","and","or","but","is","are","was","were",
    "be","been","it","its","this","that","these","those","as","by","with","from","into",
    "than","then","so","not","no","only","just","about","over","under","more","less","most",
    "least","after","before","when","while","how","what","why","who","which","many","much",
    "one","two","first","last","new","old","still","now","even","also","all","would","could",
    "did","does","do","has","have","had","will","can","may","they","their","them","you","your",
}
_PHU_DINH = re.compile(r"\b(not|never|no|nobody|nothing|none|failed|denied|without|n['’]t)\b", re.I)


def _goc_tu(c: str) -> set:
    """Từ nội dung, đã bỏ đuôi biến hình thô để 'passengers' khớp 'passenger'."""
    ts = re.findall(r"[a-z]+", (c or "").lower())
    ra = set()
    for t in ts:
        if t in _DUNG or len(t) < 3:
            continue
        for d in ("ing", "ed", "es", "s"):
            if len(t) > 4 and t.endswith(d):
                t = t[: -len(d)]
                break
        ra.add(t)
    return ra


def kiem_menh_de(cau_ra: str, cau_nguon: str, san: float = 0.6) -> tuple[bool, str]:
    """(đạt, lý do). `cau_ra` không được khẳng định nhiều hơn `cau_nguon`."""
    if not cau_ra or not cau_nguon:
        return False, "thiếu câu nguồn — không truy ngược được"
    for s in _SO.findall(cau_ra):
        if len(s) > 1 and not kiem(s, cau_nguon):
            return False, f"số «{s}» không có trong CÂU NGUỒN (có thể có ở chỗ khác trong bài)"
    tr, ng = _goc_tu(cau_ra), _goc_tu(cau_nguon)
    if tr:
        la = tr - ng
        if len(tr - la) / len(tr) < san:
            return False, f"từ không bắt rễ ở nguồn: {', '.join(sorted(la)[:4])}"
    if bool(_PHU_DINH.search(cau_ra)) != bool(_PHU_DINH.search(cau_nguon)):
        return False, "lật chiều phủ định so với nguồn"
    return True, "đạt"


# ── NGƯỜI XEM PHẢI BIẾT ĐÓ LÀ GÌ TRƯỚC KHI NGHE CÚ LẬT  (anh soi, 7/9/2026) ────────────────
# Anh xem tập mẫu và nói *"xem ko hiểu"*. Đọc lại như người chưa biết Kodak thì rõ ngay: tập
# MỞ BẰNG CÚ LẬT — "ai cũng tưởng Kodak bỏ lỡ máy ảnh số" — mà người xem chưa biết Kodak là
# ai thì cú lật ấy lật cái gì? Rồi lao thẳng vào "chemical diversification", "inkjet markets".
#
# Gốc: em đưa CÂU BÁCH KHOA vào miệng nhân vật. Câu bách khoa viết cho người ĐỌC LẠI ĐƯỢC và
# ĐÃ ĐỌC ĐOẠN TRÊN. Người xem lướt không có cả hai.
#
# Wikipedia luôn cho sẵn câu "X là gì" ở đầu bài — chỉ cần dọn rác ngoặc đơn (phiên âm, tên
# khác, chữ Hy Lạp) là dùng được.
_NGOAC = re.compile(r"\s*\([^()]*\)")
_KEP = re.compile(r"\s*\[[^\[\]]*\]")


def cau_la_gi(van: str) -> str:
    """Một câu nói rõ chủ thể LÀ GÌ, lấy từ câu đầu bài và dọn sạch."""
    c = (van or "").split("\n")[0]
    for _ in range(3):
        c = _NGOAC.sub("", c)
        c = _KEP.sub("", c)
    c = " ".join(c.split())
    # Bỏ mệnh đề đệm của lối viết bách khoa: "referred to simply as X," · "also known as
    # X," · "stylized as X,". Chúng đúng trong bài tra cứu và làm câu nói nghe lê thê.
    c = re.sub(r",\s*(?:referred to (?:simply )?as|also known as|stylized as|"
               r"commonly known as|formerly)\b[^,]*,", ",", c, flags=re.I)
    c = re.sub(r",\s*,", ",", c)
    c = re.sub(r",\s*(is|was|are|were)\b", r" \1", c)   # "Company, is" -> "Company is"
    c = " ".join(c.split()).replace(" ,", ",")
    c = c.split(". ")[0].rstrip(".") + "."
    # ── DÀI QUÁ THÌ CẮT, ĐỪNG BỎ  (7/9/2026) ──────────────────────────────────────────
    # Bản đầu trả rỗng khi câu đầu > 190 ký tự. Đo: `Blockbuster` và `Theranos` rơi vào đó,
    # nên tập của chúng KHÔNG CÓ nhịp "đó là gì" — đúng cái lỗi anh nói *"xem ko hiểu"* —
    # và hình mẫu cũng suy sai vì phải lùi về quét cả bài.
    # Câu định nghĩa của Wikipedia luôn có mệnh đề chính ở ĐẦU; cắt ở dấu phẩy sau chỗ đủ
    # dài thì giữ được định nghĩa mà bỏ phần đuôi liệt kê.
    if len(c) >= 190:
        for k in range(170, 59, -1):
            if k < len(c) and c[k] in ",;":
                c = c[:k].rstrip(",; ") + "."
                break
    return c if 24 < len(c) < 190 else ""


# ── CÂU KHÓ HIỂU THÌ BỎ, DÙ NÓ ĐÚNG ───────────────────────────────────────────────────────
# "Under CEOs Colby Chandler and Kay Whitmore, Kodak instead attempted to diversify its
# chemical operations" — đúng sự thật, và người xem lướt không theo kịp: hai cái tên lạ, một
# thuật ngữ, một mệnh đề phụ. Tai nghe một lần thì không giữ được.
_KHO = re.compile(r"\b(pursuant|thereof|whereby|notwithstanding|aforementioned|inter alia|"
                  r"respectively|subsidiary|conglomerate|amortization|divestiture)\b", re.I)


def de_hieu(c: str) -> bool:
    """Câu này nghe MỘT LẦN có hiểu không.

    Ba thước, và mỗi thước là một cách tai người mất dấu: quá nhiều mệnh đề · quá nhiều tên
    riêng lạ · từ chuyên ngành. Không thước nào chắc chắn, nhưng cả ba cùng nghiêng về phía
    BỎ — thà mất một câu đúng còn hơn giao một câu không ai theo kịp.
    """
    c = c or ""
    if _KHO.search(c):
        return False
    if c.count(",") >= 3:
        return False
    ten = re.findall(r"\b[A-Z][a-z]{2,}\b", c[1:])       # bỏ chữ đầu câu
    if len(ten) >= 4:
        return False
    return True


# ── HÌNH MẪU CỦA CHỦ THỂ — SUY MỘT LẦN CHO CẢ TẬP  (anh soi khung, 7/9/2026) ───────────────
# Anh: *"hình ảnh chưa vẽ ra được ảnh liên quan tới nội dung khi nói"*. Khung dựng ra là quầy
# thủ tục SÂN BAY trong khi lời nói về Kodak và phim ảnh.
#
# Gốc: bộ chọn đọc DANH TỪ TRONG TỪNG CÂU. Câu "Kodak began as an American public company
# focused on film photography" không khớp danh từ nào trong bảng đạo cụ (bảng ấy chỉ có 7 mục
# của ngách hài cũ), nên không vẽ gì và nền chọn bừa.
#
# Chữa: suy hình mẫu MỘT LẦN từ CHỦ THỂ, rồi mọi nhịp dùng chung. Cả tập nói về Kodak thì mọi
# nhịp thuộc hình mẫu "máy ảnh" — kể cả câu không nhắc chữ camera.
#
# ── SỐ ĐO LÀM NỀN CHO THIẾT KẾ NÀY ─────────────────────────────────────────────────────────
# 49 chủ thể mẫu gom về 10 hình mẫu, và hình mẫu KHÔNG tăng theo số chủ thể: thêm 1.000 chủ
# thể vẫn rơi vào ~10–30 hình mẫu. Nên vẽ 30 đạo cụ là việc HỮU HẠN làm một lần, phủ được
# không gian chủ thể vô hạn. Đó là lý do nguyên tắc anh nêu — *cái nào vẽ được thì phải vẽ* —
# là hướng đúng về mặt kinh tế, không chỉ về mặt thẩm mỹ.
HINH_MAU = [
    ("may_anh",   r"\b(camera|photograph|photographic|film|imaging|lens|darkroom)\b"),
    ("bang_video", r"\b(videocassette|videotape|VHS|cassette|tape format|camcorder)\b"),
    ("may_bay",   r"\b(airliner|aircraft|airplane|aeroplane|jet|airship|aviation|flight)\b"),
    ("ten_lua",   r"\b(spacecraft|space shuttle|rocket|launch vehicle|orbiter|satellite)\b"),
    ("dien_thoai", r"\b(mobile phone|smartphone|cellular|handset|telephone|pager)\b"),
    ("xe",        r"\b(personal transporter|self-balancing|scooter|two-wheel)\b"),
    ("cua_hang",  r"\b(retailer|retail|store chain|rental (?:shop|chain|store)|"
                  r"video rental|supermarket|franchise)\b"),
    ("ong_nghiem", r"\b(health technology|blood test|biotechnology|pharmaceutical|"
                   r"medical device|diagnostics|clinical)\b"),
    ("may_tinh",  r"\b(computer|microcomputer|console|operating system|software|browser|"
                  r"video game|website|social network)\b"),
    ("cua_hang",  r"\b(retailer|retail|store chain|shop|supermarket|rental chain|franchise)\b"),
    ("xe",        r"\b(automobile|car manufacturer|motor vehicle|scooter|motorcycle|truck)\b"),
    ("lo_phan_ung", r"\b(nuclear|reactor|power plant|power station|energy company)\b"),
    ("ong_nghiem", r"\b(biotechnology|blood test|pharmaceutical|drug|medical device|clinic|"
                   r"laboratory|vaccine)\b"),
    ("tau_thuy",  r"\b(ocean liner|ship|vessel|ferry|submarine|boat)\b"),
    ("toa_nha",   r"\b(skyscraper|building|tower|bridge|stadium|hotel)\b"),
    ("dong_xu",   r"\b(bank|currency|financial|investment|insurance|exchange)\b"),
    ("sach",      r"\b(newspaper|magazine|publisher|encyclopedia|bookstore|periodical)\b"),
    ("nguoi",     r"\b(politician|scientist|inventor|founder|writer|actor|musician|"
                  r"physicist|engineer|entrepreneur)\b"),
]


def hinh_mau(ho: dict) -> str:
    """Một hình mẫu cho CẢ TẬP. "" khi không nhận ra — và không đoán bừa.

    Đọc CÂU ĐẦU BÀI trước: Wikipedia luôn mở bằng "X là một <loại>", nên loại nằm ngay đó.
    Danh mục chỉ là đường lùi, vì phần lớn danh mục là rác bảo trì ("All articles with
    unsourced statements", "CS1 maint") — đo thật trên 5 chủ thể, 4/6 danh mục đầu là rác.
    """
    van = ho.get("van") or ""
    dau = cau_la_gi(van) or van[:300]
    for ten, rx in HINH_MAU:
        if re.search(rx, dau, re.I):
            return ten
    # đường lùi: quét rộng hơn trong 1.500 ký tự đầu (phần mô tả, trước khi vào lịch sử)
    for ten, rx in HINH_MAU:
        if re.search(rx, van[:1500], re.I):
            return ten
    return ""


# ── HÌNH MẪU -> NHÓM NỀN  (7/9/2026) ──────────────────────────────────────────────────────
# Bộ phân nhóm nền cũ chấm tập theo LỜI, và tập về Kodak rơi vào nhóm "corporate boardrooms"
# — cả kho chỉ có MỘT nền nhóm ấy, nên nó lùi về chọn cả kho và ra khu an ninh sân bay.
#
# Nhưng hình mẫu thì đã suy được chắc chắn (8/8 chủ thể thử đúng), và nó nói thẳng nơi chốn:
# máy ảnh -> xưởng ảnh, nhà in, phòng tin; máy bay -> sân đỗ, nhà chứa. Đo trên kho 5.118:
#
#     may_anh 112 nền · may_bay 211 · cua_hang 424 · ong_nghiem 232 · toa_nha 246
#
# Mọi hình mẫu đều có nền đủ dùng, nên đây là đường chọn ĐÁNG TIN HƠN phép chấm theo lời.
NEN_CUA_HINH_MAU = {
    "may_anh":    ("studio", "photo", "darkroom", "camera", "newsroom", "print"),
    "bang_video": ("studio", "editing", "broadcast", "rental", "newsroom"),
    "may_bay":    ("airport", "aircraft", "hangar", "runway", "terminal", "apron"),
    "ten_lua":    ("launch", "space", "rocket", "control room", "observator"),
    "dien_thoai": ("phone", "electronic", "factory", "assembly", "workbench"),
    "may_tinh":   ("office", "workbench", "server", "electronic", "home office"),
    "cua_hang":   ("shop", "store", "retail", "aisle", "checkout", "market"),
    "xe":         ("garage", "workshop", "road", "highway", "showroom", "repair"),
    "lo_phan_ung": ("power", "turbine", "industrial", "refiner", "plant"),
    "ong_nghiem": ("laborator", "clinic", "hospital", "medical"),
    "tau_thuy":   ("dock", "harbour", "harbor", "port", "shipyard", "warehouse"),
    "toa_nha":    ("office", "corridor", "lobby", "tower"),
    "dong_xu":    ("bank", "office", "trading", "vault", "counter"),
    "sach":       ("librar", "print", "newsroom", "archive", "bookshop"),
}


def nhom_nen_cua(hm: str) -> tuple:
    return NEN_CUA_HINH_MAU.get(hm or "", ())


# ── ĐỘ NHẬN BIẾT CỦA MỘT CHỦ THỂ, ĐO BẰNG LƯỢT XEM TRANG  (anh, 8/9/2026) ───────────────
# Anh: *"kịch bản phải nói về cái người dùng dễ nhớ dễ hình dung — một sự kiện nào đó, một
# công ty lớn, một vấn đề tầm cỡ thế giới… nhìn là hình dung ra ngay"*.
#
# Hồ đề tài đang duyệt cây hạng mục (*"Defunct airlines of the United States"*) nên nó ra
# `Alaska International Air`, `Boston-Maine Airways` — không ai nhớ. Cần một thước ĐO ĐƯỢC
# cho "dễ hình dung", và Wikimedia có sẵn: lượt xem trang.
#
#     Facebook 1.784.660 · Concorde 327.667 · Toyota 221.697 · FTX 49.491
#     Boston-Maine Airways 1.277 · Alaska International Air 143
#
# Chênh **12.000 lần** giữa hai đầu — thước tách sạch, đặt ngưỡng được (§12.3: calibrate hai
# đầu chỉ chứng minh tách được hai đầu, nên ngưỡng để MỀM và chỉ dùng để XẾP HẠNG, không dùng
# để loại thẳng; hồ mỏng thì vẫn phải có tập để dựng).
#
# Đệm ra ĐĨA: lượt xem đổi rất chậm, mà mỗi lần hỏi là một lượt gọi mạng cho một chủ thể đã
# biết (§18.8 — chi phí phải tỉ lệ với PHẦN MỚI, không với kích thước hồ).
_SO_XEM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "so_luot_xem.json")


def _doc_so_xem() -> dict:
    try:
        return json.load(io.open(_SO_XEM, encoding="utf-8"))
    except Exception:
        return {}


def luot_xem(ten: str, ngay: int = 90) -> int:
    """Lượt xem trang Wikipedia của `ten` trong `ngay` ngày qua. -1 nếu không hỏi được.

    Trả -1 chứ không trả 0: "chưa hỏi được" và "không ai xem" là hai chuyện khác hẳn nhau, và
    trộn chúng thì mọi phép xếp hạng nói dối (§15.2 — con số 0 cần mẫu số).
    """
    import datetime
    so = _doc_so_xem()
    if ten in so:
        return int(so[ten])
    try:
        t = urllib.parse.quote(str(ten).replace(" ", "_"), safe="")
        h = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y%m%d")
        d = (datetime.date.today() - datetime.timedelta(days=ngay)).strftime("%Y%m%d")
        u = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
             f"en.wikipedia/all-access/user/{t}/daily/{d}/{h}")
        _cho_nhip()
        r = urllib.request.Request(u, headers=UA)
        j = json.load(urllib.request.urlopen(r, timeout=25))
        n = sum(int(x.get("views") or 0) for x in (j.get("items") or []))
    except Exception:
        return -1
    so[ten] = n
    try:
        json.dump(so, io.open(_SO_XEM, "w", encoding="utf-8"))
    except Exception:
        pass
    return n
