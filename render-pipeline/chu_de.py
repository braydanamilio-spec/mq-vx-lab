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

import json
import os
import re
import tempfile
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "MM0-pipeline/1.0 (youtube explainer; contact via repo owner)"}

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
    if os.path.exists(d):
        try:
            return io.open(d, encoding="utf-8").read()
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
    v, cuoi = "", ""
    for lan in range(3):
        try:
            p = list((_goi(u).get("query") or {}).get("pages", {}).values())
            v = (p[0].get("extract") or "") if p else ""
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
_CAU_CHUYEN = re.compile(r"[^.\n]*?\b(?:because|after|when|until|failed|refused|declined|"
                         r"collapsed|bankrupt|replaced|abandoned|banned|lost|blamed|"
                         r"led to|resulted|caused|forced|never|no longer|instead)\b"
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


def ho_so(ten: str) -> dict:
    """{ten, van, cau[]} — rỗng khi không đủ sự thật, và KHÔNG đoán bù."""
    van = bai_viet(ten)
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
