#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PILOT — NỘI DUNG GIẢI THÍCH DỰNG BẰNG ENGINE COMIC.  (6/9/2026)

Anh: *"nếu 18 channel giờ tận dụng CF vẽ thêm nền bối cảnh, sau đó dùng làm clip dạng 100%
generate code như dạng videos demo thì liệu ổn không — nó giống một file có chuyển động đối
thoại, anh nghĩ nó hay hơn."*

Tệp này KHÔNG sửa gì của hai bộ đang chạy. Nó chỉ ghép:

    giai_thich.kich_ban()   số liệu tính bằng Python  ← giữ nguyên, không đụng
      -> đối thoại hai vai  (Groq/CF viết lại CÁCH NÓI, không đụng CON SỐ)
      -> nền phòng vẽ bằng CF, cache vĩnh viễn        ← ~4 ảnh MỘT LẦN cho cả kênh
      -> KichComic                                     ← engine comic sẵn có, chạy được hôm nay

── VÌ SAO ĐÁNG THỬ ────────────────────────────────────────────────────────────────────────
Đo hai bộ trong cùng một ngày:

              ảnh AI mỗi tập   trần sản lượng      nhất quán nhân vật   lỗi hình
  v10 PHIM         97          1,6 mẻ/ngày         7/8 khung            cắt đầu·tay·chữ bịa
  COMIC            ~0          ~24 mẻ/ngày         tuyệt đối (vector)   không có

Comic thắng sạch ở tầng SẢN XUẤT, giải thích thắng sạch ở tầng NỘI DUNG. Pilot này thử lấy
đúng phần mạnh của mỗi bên.

── MỘT CÂU LUẬT ĐÚNG Ở ĐÂY VÀ SAI Ở KIA ───────────────────────────────────────────────────
`SAN_NEN` dặn *"giữa khung là sàn trống, đồ đạc dồn hai mép"*. Ở v10 em đã LOẠI BỎ nó, vì nó
rút ruột khung hình (xem đầu `phim_gu.py`). Ở đây nó ĐÚNG: chỗ trống ấy là chỗ nhân vật vector
đứng vào. Cùng một câu, hai ngữ cảnh, hai kết quả ngược nhau — §12.5 đọc theo chiều ngược.
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(os.path.dirname(GOC), "engine-remotion")
PUB = os.path.join(ENG, "public")
NEN = os.path.join(PUB, "comic_nen")
sys.path.insert(0, GOC)

os.environ.setdefault("GT_KHONG_CF", "1")     # `kich_ban` không được tự gọi CF của bộ cũ

import phim_anh as A                           # noqa: E402
import phim_canh as C                          # noqa: E402
import phim_gu as GU                           # noqa: E402

# ══ NỀN: VẼ MỘT LẦN, DÙNG MÃI ════════════════════════════════════════════════════════════════
# Đây là chỗ đổi hẳn kinh tế của cả hệ. v10 vẽ 97 ảnh MỖI TẬP; ở đây bốn ảnh cho CẢ KÊNH, và
# tập thứ một nghìn vẫn dùng đúng bốn ảnh ấy. Chi phí ảnh của một tập -> 0.
GU_NEN = ("Flat 2D cartoon background painting for an animated sitcom, clean vector-like "
          "shapes, soft even lighting, muted friendly palette, no hard shadows, no people, "
          "no text, no letters, no signage anywhere.")


def ve_nen(de: str, phong: list, ks=None) -> int:
    """Vẽ nền cho từng nơi chốn của kênh. Trả số ảnh CÓ trên đĩa sau khi chạy.

    Bỏ qua ảnh đã có — nên chạy lại tốn 0 lượt. Đây là điều kiện để "vẽ một lần" là thật chứ
    không phải một lời hứa."""
    from kich_hai import SAN_NEN
    os.makedirs(NEN, exist_ok=True)
    ks = ks or A.khoa()
    co = 0
    for i, p in enumerate(phong):
        dest = os.path.join(NEN, f"{de}_{i:02d}.jpg")
        if os.path.exists(dest) and os.path.getsize(dest) > 8000:
            co += 1
            continue
        # Khung NGANG cho nền comic: engine đặt hai nhân vật đứng cạnh nhau ở dải giữa, nên
        # nền phải rộng hơn cao. `A.ve` với `doc=False` cho 1344×768.
        rel = A.ve(f"{GU_NEN} {SAN_NEN}. The room is: {p}.", de, 0, i, doc=False, ks=ks)
        if rel:
            src = os.path.join(PUB, rel)
            os.replace(src, dest)
            for phu in (src + ".json",):
                if os.path.exists(phu):
                    os.remove(phu)
            co += 1
            print(f"   🖼 nền {i}: {os.path.basename(dest)}")
        else:
            print(f"   ✗ nền {i} vẽ hỏng")
    return co


# ══ ĐỔI LỜI DẪN THÀNH ĐỐI THOẠI ══════════════════════════════════════════════════════════════
# RANH GIỚI CỨNG: AI được đổi CÁCH NÓI, không được đụng CON SỐ. Mọi con số trong lời dẫn phải
# xuất hiện nguyên văn ở lời thoại — cổng `_du_so` đo đúng điều đó và bắt viết lại nếu thiếu.
LENH_THOAI = """You turn a narrated explainer script into a two-person conversation.

You are given the narration of one episode and two characters. Rewrite it as dialogue that
delivers exactly the same information, in the same order.

RULES
1. EVERY number, unit and dollar figure in the narration must appear word for word in the
   dialogue. Never round, never change, never drop one. They are computed facts.
1b. Some lines end with [ON SCREEN: ...]. That figure is about to appear on a card in that
   exact panel. The dialogue turn for that line MUST SAY THAT FIGURE OUT LOUD, with its digits
   written exactly as given and its unit in ordinary spoken words. Write "111 decibels", not
   "that loud"; write "43,107 dollars", not "that much". A viewer listening without watching
   has to get the number from the voice alone. Do not put [ON SCREEN: ...] itself in the line.
1c. Say each figure ONCE, in its own turn. Do not repeat a figure that an earlier turn already
   said, and do not repeat the unit inside one line: write "70, 212 and 3,800 degrees",
   never "70 degrees and 212 degrees and 3,800 degrees". A turn carries at most ONE figure.
   Long turns are a real defect here, not a style note: the speech balloon grows with the
   line and a four-line balloon covers the number card underneath it.
2. One line per turn, 5 to 10 words — measured, not estimated: a 13-word turn wraps to
   four balloon lines and swallows the top third of the panel. Speakers alternate; the same person never speaks twice
   in a row.
3. The first speaker is the one who is curious or complaining. The second is the one who
   knows the number.
4. Plain spoken American English. Contractions are fine. No narrator voice, no "as you can
   see", nobody explains what the audience is looking at.
5. Keep the same number of turns as there are narration lines, or at most two more.

Return ONLY a JSON array: [{"ai":"a","chu":"...","cx":"trung_tinh"}]
"ai" is "a" for the first character and "b" for the second.
"cx" is one of: trung_tinh, ngac_nhien, tuc, buon, nghi_ngo, vui.
"""

# `re.I` ở đây là một lỗi, không phải một tiện ích: hậu tố `K/M/B` viết HOA (xem `_tien`:
# "$295K"), còn chữ thường `m` là chữ đầu của **miles** · **minutes** · **months**. Bật `re.I`
# thì "19 miles" cắt ra thành `"19 m"`, và cổng báo thiếu một chuỗi không ai từng viết — trông
# y hệt một đơn vị MÉT lọt vào kênh Mỹ (§12.13), tức nó còn dẫn người đọc đi sai hướng.
_SO = re.compile(r"\$?\d[\d,\.]*\s*(?:%|K|M|B)?")


_DON_VI = {0:"zero",1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",7:"seven",8:"eight",
           9:"nine",10:"ten",11:"eleven",12:"twelve",13:"thirteen",14:"fourteen",15:"fifteen",
           16:"sixteen",17:"seventeen",18:"eighteen",19:"nineteen"}
_CHUC = {2:"twenty",3:"thirty",4:"forty",5:"fifty",6:"sixty",7:"seventy",8:"eighty",9:"ninety"}


def _doc_so(n: int) -> str:
    """Số thành CHỮ như người Mỹ đọc. Chỉ cần tới hàng nghìn — số lớn hơn thì mô hình gần như
    luôn viết bằng chữ số ("125,893 times"), và cổng đã bắt được dạng ấy."""
    if n < 0 or n > 9999:
        return ""
    if n < 20:
        return _DON_VI[n]
    if n < 100:
        c, d = divmod(n, 10)
        return _CHUC[c] + ("-" + _DON_VI[d] if d else "")
    if n < 1000:
        t, r = divmod(n, 100)
        return _DON_VI[t] + " hundred" + (" " + _doc_so(r) if r else "")
    t, r = divmod(n, 1000)
    return _doc_so(t) + " thousand" + (" " + _doc_so(r) if r else "")


def so_tren_man(n: dict) -> str:
    """Con số mà panel này SẼ HIỆN, viết thành lời đọc được. Rỗng = panel không có số.

    ── VÌ SAO  (anh, 6/9/2026) ─────────────────────────────────────────────────────────────
    *"có nên đọc cả số liệu quan trọng với sub khi hiện trên bảng trong videos ko vì nhiều
    người ko nhìn vào videos vẫn nghe hình dung được nội dung"* — và anh đúng. Đo tập
    `pilot_howloud_0062`: **6/6 lượt có bảng số mà lời thoại không đọc con số ấy**. Người nghe
    mà không nhìn thì mất đúng thứ kênh này bán.

    Cổng `_du_so` vẫn in "số liệu ĐỦ" suốt, vì nó so lời thoại với **lời DẪN** — mà lời dẫn của
    bộ này không chứa chữ số nào (con số nằm ở trường `so`/`trai`/`phai`/`cot` của nhịp). Tập
    hợp cần kiểm rỗng, nên cổng xanh một cách rỗng: §12.8, và tệ hơn — chú thích đầu
    `SoComic.tsx` đã ghi ĐÚNG cái bẫy này từ lượt trước, em đọc rồi vẫn để nguyên cổng.
    """
    def g(v):
        return " ".join(str(v).split()) if v not in (None, "") else ""
    if n.get("so"):
        return (g(n["so"]) + " " + g(n.get("don"))).strip()
    t, ph = n.get("trai"), n.get("phai")
    if isinstance(t, dict) and isinstance(ph, dict) and t.get("so") and ph.get("so"):
        return f"{g(t['so'])} for {g(t.get('nhan'))} against {g(ph['so'])} for {g(ph.get('nhan'))}"
    cot = n.get("cot") or []
    if cot:
        # ── ĐƠN VỊ NÓI MỘT LẦN, KHÔNG MỖI CỘT MỘT LẦN  (soi khung 6/9/2026) ─────────────
        # Bản cũ ghép `f"{v} {don}"` cho TỪNG cột, nên với ba cột nó sinh ra:
        #     "70 degrees fahrenheit and 212 degrees fahrenheit and 3800 degrees fahrenheit"
        # Chuỗi ấy đi thẳng vào `[ON SCREEN: ...]`, và mô hình chép lại gần nguyên văn:
        #     "See 70 degrees fahrenheit, 212 degrees fahrenheit, and 3,800 degrees
        #      fahrenheit together"                                        — 13 chữ.
        # Hậu quả KHÔNG dừng ở câu văn: bong bóng bốn dòng chiếm 0,17·h và CHE mất nhãn
        # `3,800` của cột SURFACE — đúng con số cả tập sinh ra để nói. Em đã đi sửa hình học
        # hai vòng (`tran` rồi `dinh`) trước khi chịu nhìn lên nguồn của chuỗi; vòng thứ hai
        # còn làm khối số teo lại nằm sau đầu nhân vật. §16.3: sửa vòng thứ ba mà vẫn cùng
        # họ lỗi thì thứ sai là CÁCH TIẾP CẬN — hình học không có chỗ để nhường, câu mới có.
        #
        # Và đây là §14.16: luật *"số trên màn phải được đọc lên"* (anh dặn, vì nhiều người
        # NGHE mà không nhìn) đang được thoả bằng cách RẺ NHẤT mà câu chữ cho phép. Chỗ hở
        # nằm ở phần em không viết ra: em nói *phải đọc số*, không nói *đọc mấy lần*.
        v = [str(c.get("v")) for c in cot[:3]]
        d = g(n.get("don"))
        ten = (", ".join(v[:-1]) + " and " + v[-1]) if len(v) > 1 else v[0]
        return (ten + (" " + d if d else "")).strip()
    return ""


def _du_so(loi: list, thoai: list, man: list = None) -> list:
    """Con số nào ĐANG HIỆN trên màn (hoặc có trong lời dẫn) mà lời thoại không đọc.

    `man` là danh sách song song với `loi`: con số panel ấy sẽ hiện. Thiếu nó thì hàm quay về
    hành vi cũ — chỉ soi lời dẫn — và đó chính là trạng thái đã cho ra "ĐỦ" trên một tập câm
    hoàn toàn về số. Nên chỗ gọi PHẢI truyền `man`; cổng dưới đây canh việc ấy."""
    goc = set()
    for t in list(loi) + list(man or []):
        ds = [x.strip() for x in _SO.findall(t) if any(c.isdigit() for c in x)]
        # ── BIỂU ĐỒ: CHỈ ĐÒI CON SỐ LỚN NHẤT  (đo 6/9/2026) ─────────────────────────────
        # Một nhịp `chart` mang 3–4 cột, và bắt đọc đủ cả bốn thì câu dài lê thê rồi vẫn trượt:
        # đo trên `howloud` thấy 3 vòng viết lại liên tiếp đều thiếu một cột. Cột lớn nhất là
        # cột chốt — nói nó ra là người nghe nắm được quy mô; ba cột kia là hình, không phải lời.
        if " and " in t and len(ds) >= 3:
            def _v(x):
                try:
                    return float(re.sub(r"[^\d.]", "", x) or 0)
                except Exception:
                    return 0.0
            ds = [max(ds, key=_v)]
        goc |= set(ds)
    co = " ".join(x.get("chu", "") for x in thoai)
    # ── SỐ ĐỌC BẰNG CHỮ CŨNG LÀ ĐỌC  (đo 6/9/2026) ─────────────────────────────────────
    # Mô hình đôi khi viết *"one hundred ten decibels"* thay vì *"110 decibels"*. Với người
    # NGHE thì đó còn tự nhiên hơn — mà cổng cũ chấm trượt và đốt ba vòng viết lại cho một
    # bản vốn đúng (§13.8: cổng bắt oan tệ hơn cổng không bắt).
    # Nên nới CHÍNH XÁC một dạng: sinh chuỗi chữ của từng con số rồi tìm nó trong lời thoại.
    # ── CHUẨN HOÁ DẤU NỐI TRƯỚC KHI SO  (soi khung 6/9/2026) ───────────────────────────
    # `_doc_so(59)` sinh `fifty-nine` với gạch nối ASCII; mô hình viết `Fifty‑nine` với U+2011
    # (gạch nối KHÔNG NGẮT DÒNG). Hai chuỗi khác nhau đúng một mã ký tự, cùng một cách đọc —
    # và cổng chấm trượt rồi ĐỐT BA VÒNG gọi AI cho một bản vốn đúng, mỗi tập, mọi kênh
    # (§13.8: cổng bắt oan tệ hơn cổng không bắt).
    # Dòng này đã chuẩn hoá U+2019 từ trước; thiếu đúng họ ký tự bên cạnh. Gom cả họ: mô hình
    # rải en dash / em dash / gạch nối kiểu chữ tuỳ câu, và mỗi cái là một lần bắt oan nữa.
    _cl = co.lower().replace("\u2019", "'")
    for _d in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"):
        _cl = _cl.replace(_d, "-")
    def _da_doc(x):
        v = re.sub(r"[^\d.]", "", x).rstrip(".")
        if not v or "." in v:
            return False
        c = _doc_so(int(v))
        return bool(c) and c in _cl
    # So theo CHỮ SỐ, bỏ dấu phẩy và ký hiệu: mô hình viết "43,107 dollars" hay "43107 dollars"
    # đều là đọc đúng con số, và phạt cách viết thứ hai là bắt oan (§13.8).
    def rut(x):
        """Chuẩn hoá về CHỮ SỐ để so. Phải bỏ cả đuôi `.0`: biểu đồ mang `30.0` (số do Python
        tính, kiểu float) trong khi người nói "30 decibels" — hai chuỗi khác nhau, một con số.
        Không chuẩn hoá thì cổng báo thiếu ở MỌI nhịp biểu đồ và ép viết lại một bản vốn đúng
        (§13.8: cổng bắt oan tệ hơn cổng không bắt)."""
        v = re.sub(r"[^\d.]", "", x).rstrip(".")
        if "." in v:
            v = v.rstrip("0").rstrip(".")
        return v
    cs = {rut(x) for x in _SO.findall(co)}
    return sorted(s for s in goc
                  if s not in co and rut(s) and rut(s) not in cs and not _da_doc(s))


def doi_thoai(loi: list, vai: list, man: list = None) -> list:
    keys = C._khoa_groq()
    man = man or [""] * len(loi)
    dong = [f"{i}. {t}" + (f"   [ON SCREEN: {m}]" if m else "")
            for i, (t, m) in enumerate(zip(loi, man))]
    u = (f"CHARACTER A: {vai[0]['vai']} — {vai[0]['ta']}\n"
         f"CHARACTER B: {vai[1]['vai']} — {vai[1]['ta']}\n\n"
         f"NARRATION ({len(loi)} lines):\n" + "\n".join(dong))
    thieu: list = []
    for vong in range(3):
        t = C._goi(LENH_THOAI, u if vong == 0 else u + (
            "\n\nYour previous answer DROPPED these figures: " + ", ".join(thieu) +
            ". Each one is on a card the viewer will see. Rewrite so every one of them is "
            "spoken out loud, digits exactly as written above, in the turn for its own line. "
            "A viewer listening without watching must hear each figure."), keys)
        ds = C._tach_json(t) or []
        ra = [{"chu": " ".join(str(x.get("chu") or "").split()),
               "ai": "b" if str(x.get("ai", "a")).lower().startswith("b") else "a",
               "cx": str(x.get("cx") or "trung_tinh")}
              for x in ds if str(x.get("chu") or "").strip()]
        if len(ra) < 4:
            continue
        thieu = _du_so(loi, ra, man)
        if not thieu:
            return ra
        print(f"   ↻ lời thoại thiếu số {thieu} — viết lại")
    print("   ⚠ không đạt cổng số sau 2 vòng — dùng bản cuối kèm cảnh báo")
    return ra if len(ra) >= 4 else []


# ══ DỰNG MỘT TẬP ═════════════════════════════════════════════════════════════════════════════
def mot_tap(ma: str, idx: int, ve_nen_moi: bool = True) -> str:
    import giai_thich as G
    import kich_comic as KC
    from kich_hai import doc_hai_giong
    from chuan_am import chuan

    g = GU.gu(ma)
    # ── CẶP NÓI CHUYỆN XOAY THEO TẬP  (6/9/2026) ─────────────────────────────────────────
    # Bản cũ lấy `[:2]` — hai người đầu, mọi tập, mọi kênh. Ba vai khai sẵn thì vai thứ ba
    # không bao giờ lên hình (§15.12), và người xem thấy đúng một cuộc trò chuyện lặp lại.
    # Dàn ba vai cho **6 cặp có thứ tự**; ai hỏi và ai trả lời là hai vai khác nhau, nên thứ
    # tự có nghĩa. Dùng đúng phép của `giai_thich._cap`: bước nhảy TĂNG DẦN theo vòng, phủ hết
    # n·(n−1) cặp mà không cần nhớ gì giữa các lần chạy — quan trọng vì trên Actions không có
    # trạng thái nào sống qua hai lượt.
    _dan = GU.dan_vai_khai(ma)
    _n = max(1, len(_dan))
    if _n >= 2:
        _b = (idx // _n) % (_n - 1) + 1
        _i, _j = idx % _n, (idx % _n + _b) % _n
    else:
        _i = _j = 0
    vai = [_dan[_i], _dan[_j]]
    if len(vai) < 2:
        print("   ❌ kênh này chưa khai đủ hai vai"); return ""

    k, tieu, hook, hook_phu, nhip, muc = G.kich_ban(ma, idx, False, 3)
    loi = [n["loi"] for n in nhip]
    print(f"\n▶ {g['ten']} · {tieu}")
    print(f"   📜 {len(loi)} câu dẫn -> đối thoại {vai[0]['vai']} ↔ {vai[1]['vai']}")

    # ── NỀN ──────────────────────────────────────────────────────────────────────────────
    phong = phong_cua(ma)
    if ve_nen_moi:
        n = ve_nen(ma, phong)
        print(f"   🏠 {n}/{len(phong)} nền có trên đĩa")

    # ── ĐỐI THOẠI ────────────────────────────────────────────────────────────────────────
    man = [so_tren_man(n) for n in nhip]
    thoai = doi_thoai(loi, vai, man)
    if not thoai:
        print("   ❌ không dựng được lời thoại"); return ""
    thieu = _du_so(loi, thoai, man)
    print(f"   💬 {len(thoai)} lượt · số liệu {'ĐỦ' if not thieu else 'THIẾU ' + str(thieu)}")

    # ── ĐĂNG KÝ KÊNH VÀO CÁC BẢNG CỦA COMIC ──────────────────────────────────────────────
    # Không sửa `kich_comic.py`; chỉ thêm khoá lúc chạy. Bộ hài 20 kênh không đổi một dòng.
    de = ma
    KC.VAI[de] = [["luat_tre", "nu", "trung", 0.97, vai[0]["vai"], vai[0]["vai"]],
                  ["khoa_hoc", "nam", "trung", 1.00, vai[1]["vai"], vai[1]["vai"]]]
    KC.NHAC[de] = G.GU_RIENG.get(ma, ("", "music/forecast.mp3", ""))[1]
    KC.MAU_CHINH[de] = g["chinh"]
    KC.MAU_PHU[de] = g["phu"]
    KC.NET_KENH.setdefault(de, dict(net=7, cham=9, bo=26, tile=0.60))
    KC.BO_CUC_KENH.setdefault(de, dict(duoi=False, bo=0, no="HUH?"))
    kk = {"ten": g["ten"], "handle": "@" + ma, "a": "nam_gay", "b": "bank",
          "mau": g["nen"], "de": de, "nen": phong}

    cau = [(x["chu"], 0 if x["ai"] == "a" else 1, x["cx"]) for x in thoai]
    kieuA, kieuB, ghiA, ghiB, ga, gb = KC.vai_va_giong(kk)
    # ── TIỀN TỐ `v11_`, KHÔNG PHẢI `pilot_`  (6/9/2026) ──────────────────────────────────
    # `day_kho.py --mau` mặc định quét `v3_* · v3L_* · v5_* · v5L_* · v9_*`. Tệp tên `pilot_*`
    # KHÔNG nằm trong danh sách ấy, nên bước đẩy sẽ quét, không thấy gì, in "0 video vào hàng
    # đợi" và **thoát 0** — dựng xong 18 kênh rồi mất trắng, mà lượt vẫn xanh.
    # Cổng `kiem_workflow` bắt được triệu chứng ("không gói tệp video nào") vì nó đòi tiền tố
    # `v<số>_`; đi nới cổng là chữa cái báo động thay vì chữa cái hỏng.
    # `v11_` = thế hệ COMIC GIẢI THÍCH, đứng sau `v9_` (giải thích) và `v10_` (phim).
    slug = f"v11_{ma}_{idx:04d}"
    rel = f"{slug}.mp3"
    try:
        dur, tu, moc = doc_hai_giong(cau, ga, gb, os.path.join(PUB, rel))
    except Exception as e:
        print(f"   ❌ giọng đọc hỏng: {str(e)[:100]}"); return ""
    if not tu or len(moc) < len(cau):
        print("   ❌ thiếu mốc giọng đọc"); return ""

    luot = []
    for i, (chu, ai, cx) in enumerate(cau):
        cuoi = i == len(cau) - 1
        luot.append({"s": moc[i][0], "e": moc[i][1], "ai": ai, "nar": chu, "camXuc": cx,
                     "camXucKia": ("bat_ngo" if cuoi else
                                   ["nghi_ngo", "bat_ngo", "trung_tinh", "tuc",
                                    "buon", "nghi_ngo"][i % 6]),
                     "cuChi": KC.cu_chi_cua(chu, i, cuoi), "chot": cuoi})
    for i, l in enumerate(luot):
        l["s"], l["e"] = moc[i]

    tuyA, tuyB = KC._hai_bong(kk)
    tuyA.update(ghiA); tuyB.update(ghiB)
    # Dàn vai nói lời CUỐI: nó đứng sau `_hai_bong` và sau `vai_va_giong` nên nó ghi đè cả hai.
    dA, dB = do_vai(ma, (_i, _j))
    tuyA.update(dA); tuyB.update(dB)
    noi_idx = idx % max(1, len(phong))

    # Sổ loại: nền bị mắt phán là hỏng thì đường dựng bỏ qua, tệp vẫn nằm trên đĩa.
    # Đọc mỗi lần dựng chứ không nhớ trong biến: sổ có thể được cập nhật giữa hai lượt.
    try:
        _bo = set(json.load(io.open(os.path.join(GOC, "nen_bo.json"), encoding="utf-8")))
    except Exception:
        _bo = set()

    def _co(i):
        """Đường dẫn ảnh nền thứ i nếu có trên đĩa. WebP trước — kho mới nén WebP (−93% dung
        lượng), kho cũ còn JPEG hai chữ số, và cả hai phải cùng dùng được."""
        if f"{de}_{i:03d}" in _bo:
            return ""
        for ten in (f"comic_nen/{de}_{i:03d}.webp", f"comic_nen/{de}_{i:03d}.jpg",
                    f"comic_nen/{de}_{i:02d}.jpg"):
            if os.path.exists(os.path.join(PUB, ten)):
                return ten
        return ""

    anh_nen = _co(noi_idx)
    # ĐỔI PHÒNG THEO PANEL, không theo tập. Engine đã có sẵn `anhNens[]` cho bản dài — em chỉ
    # chưa truyền. Một phòng cho cả 18 panel đọc ra là đứng yên; bốn phòng xoay vòng thì mỗi
    # ba panel đổi cảnh một lần, đúng nhịp một cuộc trò chuyện đi qua vài chỗ trong ca trực.
    co = [j for j in range(len(phong)) if _co(j)]

    # ── CHỌN NỀN THEO NỘI DUNG TẬP  (anh yêu cầu, 6/9/2026) ──────────────────────────────
    # Anh: *"chia theo từng group tag key phù hợp mỗi channel để khi lấy ảnh nó tự động với
    # nội dung kịch bản"*. Trước đó bộ chọn chỉ là một bước nhảy tất định — nó lo đúng một
    # việc (đừng lặp phòng) và MÙ với nội dung. Đo được:
    #     HOW LOUD «crowd chant at a music festival» -> xưởng bảo trì · làn rải nhựa đường
    #     REAL COST «a $12 lunch every workday»      -> trạm bơm dầu diesel
    # Đa dạng mà không liên quan vẫn là khung nói một đằng lời nói một nẻo (§17.5).
    #
    # `nen_tag.json` gắn mỗi nền vào một trong mười NHÓM CHỦ ĐỀ của kênh; tập cũng được chấm
    # vào đúng mười nhóm ấy. Khớp theo NHÓM chứ không theo từ, vì nền viết "a bleacher tier,
    # steel railings" còn tập nói "stadium" — không một từ nào trùng (§13.5).
    #
    # Ba tầng, tầng dưới không bao giờ gọi mạng:
    #     nền CÙNG NHÓM với tập  ->  nếu đủ ≥3 nền thì dùng riêng nhóm ấy
    #     không đủ                ->  dùng cả kho (hành vi cũ, vẫn đúng)
    #     chưa có thẻ             ->  dùng cả kho
    try:
        import nen_tag as NT
        _the = json.load(io.open(os.path.join(GOC, "nen_tag.json"), encoding="utf-8"))
        _nh = NT.nhom_tap(ma, tieu + ". " + " ".join(loi))
        _hop = [j for j in co if _the.get(f"{de}_{j:03d}") and
                _the.get(f"{de}_{j:03d}") == _nh] if _nh else []
        if len(_hop) >= 3:
            print(f"   🎯 nhóm nền «{_nh}» — {len(_hop)}/{len(co)} nền hợp nội dung")
            co = _hop
        elif _nh:
            print(f"   🎯 nhóm «{_nh}» chỉ có {len(_hop)} nền — dùng cả kho")
    except Exception as e:
        print(f"   ⚠ không đọc được nen_tag.json ({str(e)[:40]}) — dùng cả kho")
    # ── CHỌN PHÒNG: BƯỚC NGUYÊN TỐ CÙNG NHAU, KHÔNG PHẢI LIỀN KỀ  (6/9/2026) ──────────────
    # Bản cũ lấy `(i//3 + noi_idx) % len(co_nen)` — ba panel một phòng, rồi phòng KẾ TIẾP trong
    # danh sách. Với kho 100 chỗ soạn theo NHÓM CHỦ ĐỀ, ba phòng liền nhau trong danh sách là
    # ba phòng cùng nhóm (ba xưởng gỗ), nên đổi phòng mà khung vẫn đọc ra một chỗ.
    # Bước nhảy nguyên tố cùng nhau với cỡ kho thì đi hết kho mà mỗi lần nhảy sang một vùng
    # khác hẳn — cùng cơ chế `_cap` dùng cho cặp dữ liệu, ở đây dùng cho nơi chốn.
    if co:
        buoc = next((b for b in (37, 31, 29, 23, 19, 17, 13, 11, 7, 5, 3, 1)
                     if len(co) % b), 1)
        anh_nens = [_co(co[(noi_idx + (i // 3) * buoc) % len(co)]) for i in range(len(cau))]
    else:
        anh_nens = []

    # ── LỚP SỐ LIỆU: GẮN THEO VỊ TRÍ, KHÔNG GẮN THEO TỪ KHOÁ  (sửa 6/9/2026) ─────────
    # Bản đầu dò con số trong lời thoại rồi gắn lớp vào lượt nào có nó. Đo trên tập
    # `realcost`: **khớp 3, lệch 6**. Panel 5 hiện `43,107` trong khi câu nói là *"Now let it
    # sit, imagine the total"* — không có con số nào để mà dò.
    #
    # Gốc: lời thoại phần lớn ĐẶT CÂU HỎI về con số chứ không đọc nó ra. Phép dò từ khoá vì
    # thế trượt gần hết, rồi rơi vào nhánh dự phòng "đặt vào panel trống gần đầu nhất" — và
    # nhánh ấy chạy 6/9 lần, tức nó mới là cơ chế thật, không phải cơ chế dự phòng.
    #
    # Nhưng có một ánh xạ CHẮC CHẮN mà em bỏ qua: lời thoại được sinh RA TỪ lời dẫn, gần như
    # một-đổi-một (12 câu -> 12 lượt). Nên nhịp thứ i ứng với lượt thứ i. Ánh xạ theo VỊ TRÍ
    # đúng theo cấu trúc, không phụ thuộc vào việc câu thoại có tình cờ chứa con số hay không.
    # Từ khoá chỉ còn là bản tinh chỉnh: nếu lượt lân cận có đúng con số thì dịch sang lượt đó.
    so_lieu = [None] * len(cau)
    import phim as P
    co_lop = [(i, P.lop_du_lieu(n)) for i, n in enumerate(nhip)]
    co_lop = [(i, l) for i, l in co_lop if l]
    for i, lop in co_lop:
        # vị trí tương ứng trong dòng lời thoại
        j = min(len(cau) - 1, round(i * (len(cau) - 1) / max(1, len(nhip) - 1)))
        kim = re.sub(r"[^0-9A-Za-z]", "", str(lop.get("so") or ""))[:6].lower()
        # tinh chỉnh: trong cửa sổ ±2 lượt, ưu tiên lượt THẬT SỰ đọc con số ấy
        if kim:
            for d in (0, 1, -1, 2, -2):
                t = j + d
                if 0 <= t < len(cau) and not so_lieu[t] \
                        and kim in re.sub(r"[^0-9A-Za-z]", "", cau[t][0]).lower():
                    j = t
                    break
        while j < len(cau) and so_lieu[j]:
            j += 1
        if j < len(cau):
            so_lieu[j] = lop
    _ns = sum(1 for x in so_lieu if x)
    print(f"   🔢 {_ns} lượt có lớp số liệu")
    props = {
        "luot": luot, "tu": tu, "voMp3": rel, "nhac": KC.NHAC[de],
        "kieuA": kieuA, "kieuB": kieuB, "kieuTuyA": tuyA, "kieuTuyB": tuyB,
        "tieuDe": g["ten"], "handle": "@" + ma, "kenh": slug,
        "mau": g["chinh"], "mauPhu": g["phu"],
        "netMuc": 7, "cham": 9, "boGoc": 26, "tiLe": 0.60, "soTap": idx,
        "bongDuoi": False, "boKhung": 0, "chuNo": "HUH?",
        "anhNens": anh_nens, "soLieu": so_lieu,
        # Kênh GIẢI THÍCH tắt đồ nghề hài: thẻ hook thành dải sát đáy (không đè mặt), và bỏ
        # chữ nổ + cú rung ở câu chốt — engine bắn hiệu ứng punchline vào một câu kết trầm thì
        # khán giả đọc ra là hệ thống không hiểu nó đang kể gì.
        "hookDuoi": True, "haiHuoc": False,
        "noiIdx": noi_idx, "hook": (hook_phu or hook or tieu).upper()[:44],
        "anhNen": anh_nen, "sang": KC._sang_cua(anh_nen),
        "nhacVol": KC._am_nhac(KC.NHAC[de]),
    }
    pj = os.path.join(GOC, "out", f"{slug}.json")
    os.makedirs(os.path.dirname(pj), exist_ok=True)
    io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))

    out = os.path.join(GOC, "out", f"{slug}.mp4")
    r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "KichComic", out,
                        f"--props={pj}", "--gl=swiftshader", "--log=error"],
                       cwd=ENG, capture_output=True, text=True, timeout=2400)
    if r.returncode or not os.path.exists(out):
        print(f"   ❌ render hỏng: {(r.stderr or r.stdout or '')[-260:]}"); return ""
    # ── KHÔNG DÙNG `lam_thumb` Ở BỘ NÀY  (đo 6/9/2026) ───────────────────────────────────
    # `lam_thumb` viết cho bộ `kich_hai`, nơi khung phim KHÔNG có bong bóng và không có bảng số
    # — nên nó tự vẽ một lớp chữ hook đè lên. Ở bộ comic giải thích thì khung ĐÃ mang sẵn cả
    # hai, và kết quả là **ba tầng chữ chồng nhau**, cộng thêm nhãn dưới in ra `v11_howhot_0040`
    # (slug) thay vì con số. §12.5 đúng dạng: câu luật đúng ở ngữ cảnh nó sinh ra, sai ở đây.
    #
    # Và nó vốn đã bị vứt: `giao_hang` -> `lam_bia` ghi đè CÙNG một tệp ngay sau đó. Đo bằng
    # cách so pixel: ảnh bìa đang lưu KHỚP HOÀN TOÀN khung thô — tức mọi công dựng template
    # xưa nay đều đi thẳng vào thùng rác, im lặng.
    # §16.3 đã trả giá ba vòng cho đúng câu hỏi này và kết luận: khung hook của bộ này đã mang
    # thông điệp bằng chính đồ hoạ của nó, **không cần lớp chữ thứ hai**.
    am = chuan(out)

    # ── BỘ GIAO HÀNG PHẢI ĐỦ BỐN THỨ  (6/9/2026) ─────────────────────────────────────────
    # §10.3: bộ giao hàng của một tập là **ngắn · dài · ảnh bìa · `.tai.json`**. Pilot tới giờ
    # chỉ ra `.mp4` + `.jpg` + tệp props — tức **có video mà không đăng được**, và một lượt
    # render 18 kênh sẽ chạy xanh trọn vẹn rồi cho ra số 0 ở khâu đăng.
    # Đây đúng dạng đã trả giá ở §15.10: một dây chuyền dừng nửa đường trông y hệt một dây
    # chuyền hoàn chỉnh. Nối trước khi dựng workflow, không phải sau.
    try:
        import phim_dang as PD
        co = PD.giao_hang(slug, out, ma, g["ten"], tieu, hook, hook_phu,
                          dur, False, nhip)
        _t = "✅" if all(co.values()) else "❌"
        print(f"   {_t} giao hàng: " + " · ".join(f"{k}{'✓' if v else '✗'}"
                                                  for k, v in co.items()))
        if not all(co.values()):
            return ""          # thiếu một mảnh thì KHÔNG tính là tập xong (§15.3)
    except Exception as e:
        print(f"   ❌ giao hàng hỏng: {str(e)[:140]}")
        return ""

    print(f"   ✅ {out}  ({os.path.getsize(out)/1e6:.1f} MB · {dur:.0f}s · "
          f"{len(luot)} panel{' · ' + am if am else ''})")
    return out


# ══ TRANG PHỤC — DÀN VAI NÓI LỜI CUỐI ════════════════════════════════════════════════════════
# Pilot lượt đầu ra một phụ nữ áo cam và một người đàn ông vest xanh, trong khi dàn vai khai
# *Nurse Tara — teal scrubs* và *Dr Vance — white coat*. Không phải engine hỏng: `kieuTuyA/B`
# là `Partial<Kieu>` và nó nhận đủ `ao · quan · toc · kinh · mu` — em chỉ chưa truyền gì cả,
# nên engine dùng bộ mặc định của kênh hài.
# Bảng này dịch dàn vai thành đúng những trường `Kieu` mà engine đã biết vẽ. `mu: "y_ta"` có
# sẵn trong engine từ trước — không phải thêm mã, chỉ phải BIẾT nó có.
# ── MƯỜI TÁM KÊNH, MƯỜI TÁM BỘ ĐỒ  (6/9/2026) ────────────────────────────────────────────────
# Anh hỏi: *"trang phục có cần đa dạng hơn không, và xuyên suốt mỗi channel à?"*
#
# Trả lời tách làm hai, vì hai vế kéo ngược nhau:
#
#   XUYÊN SUỐT MỘT KÊNH  -> BẮT BUỘC. Người xem theo dõi một KÊNH, không theo dõi một tập.
#     Nurse Tara phải mặc đúng bộ scrubs xanh ở tập 1 và ở tập 500. Đây chính là thứ em đánh
#     vật cả ngày với v10 mà không bao giờ khoá chặt được — vector thì khoá được tuyệt đối.
#
#   ĐA DẠNG GIỮA CÁC KÊNH -> BẮT BUỘC, và đây là chỗ đang thiếu. Mười tám kênh mà mười lăm
#     kênh dùng bộ mặc định của kênh hài thì mười lăm kênh ấy mặc GIỐNG HỆT nhau — đúng chữ
#     ký sản xuất hàng loạt mà chính sách 7/2025 nhắm vào (§13.17).
#
#   ĐA DẠNG GIỮA CÁC TẬP CỦA CÙNG MỘT KÊNH -> KHÔNG. Đổi áo mỗi tập là phá nhận diện. Chỗ để
#     đa dạng là NƠI CHỐN và ĐẠO CỤ, không phải quần áo nhân vật chính.
#
# Sáu trục phân biệt: màu áo · kiểu áo · màu quần · kiểu tóc · kính/râu · mũ. Mỗi kênh khác ít
# nhất BA trục so với mọi kênh khác — cổng `kiem_do_vai()` đo điều đó.
DO_VAI = {
 # y tế
 "dayinlife": [dict(ao="#2E8B8B", aoTrong="#FFFFFF", quan="#2E8B8B", toc="#4A3728", kieuToc="bui", mu="y_ta", kieuAo="thun"),
               dict(ao="#F2F2F2", aoTrong="#BFD7EA", quan="#2C3E50", toc="#3A3A3A", kieuToc="ngan", rau="ria", kieuAo="somi", caVat="#3E6E8C")],
 # tiền bạc
 "realcost":  [dict(ao="#3FB87E", aoTrong="#FFFFFF", quan="#37474F", toc="#6B4A2F", kieuToc="duoi_ngua", kieuAo="somi"),
               dict(ao="#E0644A", aoTrong="#FFFFFF", quan="#4E4033", toc="#2F2F2F", kieuToc="ngan", kieuAo="polo")],
 "hiddenfee": [dict(ao="#3EA877", aoTrong="#FFFFFF", quan="#2F3A34", toc="#1F1F1F", kieuToc="bob", kinh=True, kieuAo="cardigan"),
               dict(ao="#DC6A44", aoTrong="#F0F0F0", quan="#3A3A3A", toc="#5A4030", kieuToc="ngan", kieuAo="somi", caVat="#8A2E2E")],
 "howmuch":   [dict(ao="#9B72D9", aoTrong="#FFFFFF", quan="#3A3050", toc="#E0C060", kieuToc="xoan", kieuAo="hoodie"),
               dict(ao="#F0B63C", aoTrong="#FFFFFF", quan="#4A4030", toc="#4A4A4A", kieuToc="trocs", kinh=True, kieuAo="polo")],
 # quy mô · vật lý
 "howbig":    [dict(ao="#31B0C9", aoTrong="#FFFFFF", quan="#2B4A55", toc="#2A2A2A", kieuToc="ngan", mu="luoi_trai", kieuAo="thun"),
               dict(ao="#F08A3C", aoTrong="#FFFFFF", quan="#4A4034", toc="#6B4A2F", kieuToc="re_ngoi", kieuAo="polo")],
 "whatweighs":[dict(ao="#8FA84A", aoTrong="#E8E2D6", quan="#3E3A2E", toc="#8A5A2A", kieuToc="bui", kieuAo="thun"),
               dict(ao="#DC8055", aoTrong="#FFFFFF", quan="#4A4034", toc="#B03A2E", kieuToc="roi", rau="de", kieuAo="somi")],
 "smallest":  [dict(ao="#5C74D6", aoTrong="#FFFFFF", quan="#2E3350", toc="#1A1A1A", kieuToc="bob", kinh=True, kieuAo="cardigan"),
               dict(ao="#B4CE4C", aoTrong="#FFFFFF", quan="#3A4030", toc="#6B4A2F", kieuToc="hoi", kinh=True, kieuAo="somi")],
 # thời gian · hành trình
 "howlong":   [dict(ao="#E0642B", aoTrong="#F0E6D2", quan="#4A4034", toc="#C09050", kieuToc="roi", mu="luoi_trai", kieuAo="hoodie"),
               dict(ao="#4FB3C7", aoTrong="#FFFFFF", quan="#2E4450", toc="#3A2A1A", kieuToc="duoi_ngua", kieuAo="thun")],
 "yearsof":   [dict(ao="#D5813F", aoTrong="#F2EAD8", quan="#4A3E30", toc="#9A9A9A", kieuToc="ngan", kieuAo="cardigan"),
               dict(ao="#5B94A3", aoTrong="#FFFFFF", quan="#3A4450", toc="#C0B0A0", kieuToc="bui", kinh=True, kieuAo="somi")],
 "speedof":   [dict(ao="#43A0D1", aoTrong="#FFFFFF", quan="#232838", toc="#1A1A1A", kieuToc="trocs", kieuAo="thun"),
               dict(ao="#F5762F", aoTrong="#FFFFFF", quan="#3A3A3A", toc="#7A5A3A", kieuToc="xoan", rau="de", kieuAo="hoodie")],
 # đời thường
 "whatif":    [dict(ao="#EE6352", aoTrong="#FFFFFF", quan="#2E4450", toc="#6B4A2F", kieuToc="xoan", kieuAo="hoodie"),
               dict(ao="#3FA9C4", aoTrong="#FFFFFF", quan="#4A4034", toc="#1F1F1F", kieuToc="duoi_ngua", kieuAo="thun")],
 "therules":  [dict(ao="#E76A44", aoTrong="#FFFFFF", quan="#7A6A50", toc="#8A7A5A", kieuToc="hoi", kieuAo="polo"),
               dict(ao="#6FA86A", aoTrong="#FFFFFF", quan="#E8E2D6", toc="#D0C080", kieuToc="bob", kinh=True, kieuAo="cardigan")],
 "wheregoes": [dict(ao="#4FA3D9", aoTrong="#E8E2D6", quan="#3A4450", toc="#C0A060", kieuToc="ngan", mu="luoi_trai", kieuAo="thun"),
               dict(ao="#EB9440", aoTrong="#FFFFFF", quan="#3E3A30", toc="#5A5A5A", kieuToc="bui", kinh=True, kieuAo="somi")],
 "rightnow":  [dict(ao="#2FAEC9", aoTrong="#FFFFFF", quan="#232838", toc="#2A2A2A", kieuToc="xoan", kieuAo="thun"),
               dict(ao="#F09443", aoTrong="#FFFFFF", quan="#3A3A3A", toc="#9A8A7A", kieuToc="bui", kieuAo="cardigan")],
 # cực đoan
 "survive":   [dict(ao="#D9713F", aoTrong="#E8E2D6", quan="#4A4034", toc="#7A5A3A", kieuToc="roi", mu="len", kieuAo="hoodie"),
               dict(ao="#6FA86A", aoTrong="#FFFFFF", quan="#3E3A30", toc="#8A8A8A", kieuToc="ngan", rau="quai", kieuAo="somi")],
 "howhot":    [dict(ao="#EE6B29", aoTrong="#E8E2D6", quan="#3A3A3A", toc="#1A1A1A", kieuToc="trocs", kieuAo="thun"),
               dict(ao="#5A87AC", aoTrong="#FFFFFF", quan="#4A4034", toc="#B03A2E", kieuToc="duoi_ngua", mu="luoi_trai", kieuAo="polo")],
 "howloud":   [dict(ao="#E8493B", aoTrong="#FFFFFF", quan="#232838", toc="#3A2A1A", kieuToc="re_ngoi", kieuAo="thun"),
               dict(ao="#4A82BE", aoTrong="#E8E2D6", quan="#3E3A30", toc="#C0A060", kieuToc="bui", kieuAo="hoodie")],
 "odds":      [dict(ao="#9366CE", aoTrong="#FFFFFF", quan="#332A50", toc="#5A5A5A", kieuToc="hoi", rau="ria", kieuAo="somi"),
               dict(ao="#E3B33A", aoTrong="#FFFFFF", quan="#3A3A3A", toc="#B03A2E", kieuToc="bob", kieuAo="cardigan")],
}


def kiem_do_vai() -> list:
    """Mỗi kênh phải khác MỌI kênh khác ít nhất BA trục. Hai kênh khác nhau một màu áo thì ở
    cỡ điện thoại đọc ra là cùng một cặp nhân vật."""
    TRUC = ("ao", "quan", "toc", "kieuToc", "kieuAo", "mu", "kinh", "rau")
    loi, ds = [], list(DO_VAI.items())
    for i, (m1, v1) in enumerate(ds):
        for m2, v2 in ds[i + 1:]:
            khac = sum(1 for t in TRUC for a, b in zip(v1, v2)
                       if a.get(t) != b.get(t))
            if khac < 3:
                loi.append(f"{m1} và {m2} chỉ khác {khac} trục")
    thieu = [m for m in GU.KENH if m not in DO_VAI]
    if thieu:
        loi.append(f"chưa khai trang phục: {thieu}")
    return loi




# ══ VAI THỨ BA — TRANG PHỤC  (6/9/2026) ══════════════════════════════════════════════════════
# `phim_gu.VAI` khai **ba** vai cho MỖI kênh, tả rất kỹ (tuổi, tóc, áo, màu). Đường dựng thì
# lấy `[:2]` — nên 18/18 vai thứ ba được viết ra rồi **không ai đọc**, đúng §15.12: một trường
# chỉ được ghi mà không được đọc là một trường chưa tồn tại.
# Hậu quả nhìn thấy được: tập *"a day in the life of a subway train operator"* vẫn do Nurse
# Tara ↔ Dr Vance nói, vì cặp không bao giờ xoay.
#
# Màu và kiểu ở đây SUY TỪ CHÍNH câu tả trong `VAI` ('white crew cut, grey university
# sweatshirt' -> tóc trắng, áo hoodie xám), không bịa thêm: hai chỗ tả cùng một người mà nói
# khác nhau thì ảnh AI và người vector sẽ là hai người (§11 — đừng tạo nguồn thứ hai).
# Mọi giá trị đã qua `kiem_gan.py` — engine có nhánh vẽ cho từng cái.
DO_VAI_3 = {
 "howlong": dict(ao='#8A8F94', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#F2F2F2', kieuToc='ngan', kieuAo='hoodie'),   # Coach Pete
 "howbig": dict(ao='#8B6BB8', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#3A2E28', kieuToc='duoi_ngua', kieuAo='hoodie'),   # Dot
 "realcost": dict(ao='#3E6E8C', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#F2F2F2', kieuToc='ngan', kieuAo='somi', rau='ria', mu='luoi_trai'),   # Uncle Walt
 "howmuch": dict(ao='#8A8F94', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#4A3728', kieuToc='ngan', kieuAo='somi'),   # Mr Okoye
 "whatif": dict(ao='#3E6E8C', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#4A3728', kieuToc='trocs', kieuAo='somi', rau='quai'),   # Gus
 "survive": dict(ao='#6B7A45', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#8A8F94', kieuToc='ngan', kieuAo='somi', rau='ria'),   # Ranger Ellis
 "dayinlife": dict(ao='#3FA46A', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#F2F2F2', kieuToc='ngan', kieuAo='thun'),   # Mr Hollis
 "wheregoes": dict(ao='#3E6E8C', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#3A2E28', kieuToc='xoan', kieuAo='thun'),   # Otis
 "therules": dict(ao='#C8A97E', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#2A2A2A', kieuToc='bui', kieuAo='somi'),   # Officer Mel
 "speedof": dict(ao='#6B4A2F', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#F2F2F2', kieuToc='ngan', kieuAo='somi', rau='de', mu='cao_bo'),   # Pop Harlan
 "odds": dict(ao='#D9A0B0', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#F2F2F2', kieuToc='xoan', kieuAo='cardigan'),   # Grandma Pearl
 "hiddenfee": dict(ao='#3E6E8C', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#C4642A', kieuToc='ngan', kieuAo='polo'),   # Chet
 "yearsof": dict(ao='#F2F2F2', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#6B4A2F', kieuToc='ngan', kieuAo='thun'),   # Young Hal
 "howloud": dict(ao='#D9503F', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#E0C060', kieuToc='duoi_ngua', kieuAo='somi'),   # Little Ann
 "whatweighs": dict(ao='#3FA46A', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#6B4A2F', kieuToc='ngan', kieuAo='thun'),   # Chip
 "rightnow": dict(ao='#8B6BB8', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#8A8F94', kieuToc='bui', kieuAo='cardigan'),   # Mrs Reyes
 "howhot": dict(ao='#F2F2F2', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#E0C060', kieuToc='xoan', kieuAo='thun'),   # Skip
 "smallest": dict(ao='#E08A3C', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#2A2A2A', kieuToc='ngan', kieuAo='thun'),   # Ravi
}




# Trang phục VAI THỨ TƯ — cùng phép suy từ câu tả như `DO_VAI_3`.
# Bốn vai cho **12 cặp có thứ tự** thay vì 6: gấp đôi số cuộc trò chuyện khác nhau,
# và không tốn một ảnh nào.
DO_VAI_4 = {
 "howlong": dict(ao='#3FA46A', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#4A3728', kieuToc='duoi_ngua', kieuAo='somi'),   # Eli
 "howbig": dict(ao='#E39BB4', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#4A3728', kieuToc='ngan', kieuAo='somi'),   # Lena
 "realcost": dict(ao='#EDE3CE', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#B9BFC4', kieuToc='ngan', kieuAo='somi'),   # Graham
 "howmuch": dict(ao='#2A2A2A', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#D9503F', kieuToc='xoan', kieuAo='thun'),   # Mira
 "whatif": dict(ao='#E08A3C', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#4A3728', kieuToc='ngan', kieuAo='somi'),   # Jace
 "survive": dict(ao='#E8C24A', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#4A3728', kieuToc='duoi_ngua', kieuAo='somi'),   # Tara
 "dayinlife": dict(ao='#B9BFC4', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#B9BFC4', kieuToc='ngan', kieuAo='thun'),   # Eli
 "wheregoes": dict(ao='#E08A3C', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#6B4A2F', kieuToc='duoi_ngua', kieuAo='thun'),   # Mara
 "therules": dict(ao='#F2F2F2', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#4A3728', kieuToc='trocs', kieuAo='thun'),   # Sam
 "speedof": dict(ao='#2A2A2A', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#2E8B8B', kieuToc='duoi_ngua', kieuAo='thun'),   # Rita
 "odds": dict(ao='#7B2233', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#4A3728', kieuToc='ngan', kieuAo='somi'),   # Milo
 "hiddenfee": dict(ao='#2E8B8B', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#4A3728', kieuToc='bob', kieuAo='thun'),   # Nina
 "yearsof": dict(ao='#3A3A3A', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#4A3728', kieuToc='ngan', kieuAo='thun', rau='quai'),   # Milo
 "howloud": dict(ao='#2A2A2A', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#4A3728', kieuToc='ngan', kieuAo='thun'),   # Jax
 "whatweighs": dict(ao='#F2F2F2', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#4A3728', kieuToc='xoan', kieuAo='polo'),   # Nora
 "rightnow": dict(ao='#4E6E8E', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#D8D8D8', kieuToc='bob', kieuAo='thun'),   # Lena
 "howhot": dict(ao='#2B5FA8', aoTrong='#FFFFFF', quan='#3A3A3A', toc='#4A3728', kieuToc='duoi_ngua', kieuAo='somi'),   # Cass
}

_DO_ALL: dict = {}


def do_vai(ma: str, cap=(0, 1)) -> tuple:
    """Trang phục cho CẶP vai đang nói. `cap` là hai chỉ số trong dàn vai.

    ── VÌ SAO CÓ `do_vai_all.json`  (6/9/2026) ─────────────────────────────────────────────
    Dàn vai đi từ 2 lên 6 người/kênh, mà trang phục thì viết tay ở `DO_VAI` (2 bộ) rồi vá thêm
    `DO_VAI_3`, `DO_VAI_4`. Vá tới bộ thứ năm là lúc phải dừng: bốn bảng song song cho cùng một
    thứ là bốn chỗ để quên một chỗ.
    `do_vai_all.json` sinh từ CHÍNH câu tả trong `phim_gu.VAI` cho MỌI vai — một nguồn, đủ dài
    bằng dàn vai, và tự đúng khi dàn vai dài thêm. Ba bảng cũ giữ làm tầng dưới cho kênh chưa
    có tệp."""
    if not _DO_ALL:
        try:
            _DO_ALL.update(json.load(io.open(os.path.join(GOC, "do_vai_all.json"),
                                             encoding="utf-8")))
        except Exception:
            _DO_ALL["_"] = []
    _all = _DO_ALL.get(ma)
    if _all:
        return dict(_all[cap[0] % len(_all)]), dict(_all[cap[1] % len(_all)])
    ds = list(DO_VAI.get(ma) or [])
    for _b in (DO_VAI_3.get(ma), DO_VAI_4.get(ma)):
        if _b:
            ds = ds + [_b]
    if not ds:
        return {}, {}
    return dict(ds[cap[0] % len(ds)]), dict(ds[cap[1] % len(ds)])


# Bốn phòng cho mỗi kênh — vẽ một lần. Chỉ khai kênh pilot; kênh khác dùng bản mặc định.
_KHO_NEN: dict = {}


def phong_cua(ma: str) -> list:
    """Nơi chốn của một kênh, lấy từ `nen_kho.json` (100 chỗ/kênh, soạn bằng `nen_kho.py`).

    ── VÌ SAO ĐỔI NGUỒN  (6/9/2026) ────────────────────────────────────────────────────────
    `PHONG_KENH` chép tay và chỉ khai cho ĐÚNG MỘT kênh; 17 kênh còn lại rơi về `_mac_dinh` =
    **hai** căn phòng. Soi lưới 4 khung HOW LOUD thì 3/4 khung cùng một cái bàn làm việc —
    không phải lỗi dựng, mà là kênh chỉ có hai cái nền để mà chọn.

    Bảng chép tay vẫn giữ làm tầng dưới: kho chưa soạn cho một kênh mới thì nó vẫn dựng được,
    và tầng cuối không gọi mạng nên không bao giờ hỏng (§7, bốn tầng nền).
    """
    if not _KHO_NEN:
        p = os.path.join(GOC, "nen_kho.json")
        if os.path.exists(p):
            try:
                _KHO_NEN.update(json.load(io.open(p, encoding="utf-8")))
            except Exception as e:
                print(f"   ⚠ không đọc được nen_kho.json: {str(e)[:60]}")
    return _KHO_NEN.get(ma) or PHONG_KENH.get(ma) or PHONG_KENH["_mac_dinh"]


PHONG_KENH = {
    "dayinlife": [
        "a hospital ward corridor at night, doors along both sides, ceiling lights on",
        "a hospital nurses station with monitors and a counter along the back wall",
        "a small hospital staff break room with lockers and a coffee machine",
        "a quiet patient room at dawn, one empty bed, window with early light",
    ],
    "_mac_dinh": [
        "a plain american office room, desks along the back wall, daylight",
        "a plain american kitchen, counter along the back wall, window light",
    ],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="dayinlife")
    ap.add_argument("--tu", type=int, default=4)
    ap.add_argument("--khong-ve-nen", action="store_true")
    a = ap.parse_args()
    return 0 if mot_tap(a.kenh, a.tu, not a.khong_ve_nen) else 1


if __name__ == "__main__":
    raise SystemExit(main())
