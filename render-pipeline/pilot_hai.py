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
import unicodedata
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
# ── CẤM CHỮ BẰNG CÂU PHỦ ĐỊNH LÀ ĐẶT HÀNG CHỮ  (soi khung 8/9/2026) ─────────────────────────
# Đuôi cũ là `"no text, no letters, no signage anywhere"` — BA danh từ chỉ chữ đứng liền nhau.
# FLUX không có negative prompt (§17.6 đã trả giá với `no circular vignette, no round badge,
# no border` -> ra đúng một vignette tròn), nên ba chữ ấy là ba lần ĐẶT HÀNG.
# Soi bản dài `ATA Airlines`: nền hiện `"ATA a…"` và `"MILLION CASH TRANSEC…"` — chữ loằng
# ngoằng, thứ người xem đọc ra "nghiệp dư" trong nửa giây (§13.20).
# Chữa bằng câu KHẲNG ĐỊNH tả bề mặt TRỐNG, không nhắc tới chữ.
GU_NEN = ("Flat 2D cartoon background painting for an animated sitcom, clean vector-like "
          "shapes, soft even lighting, muted friendly palette, soft shadows only, "
          "surfaces painted in flat solid colour.")


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
_DUNG_CHUNG = {
    "that","this","these","those","with","from","have","been","were","they","their","there",
    "which","when","what","would","could","about","after","before","other","such","than",
    "also","into","over","under","more","most","some","many","much","very","just","only",
    "company","industry","became","being","because","while","where","then","them","will",
}

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
3. Speaker "a" ASKS: curious, sceptical, or complaining, and never supplies a figure of
   their own. Speaker "b" is the domain professional named in the cast — the surveyor, the
   accountant, the attorney, the ranger — and is the ONLY one who answers with figures.
0a. A line marked [KEEP] says the thing everyone believes is wrong. Speaker "b" — the
   expert — must be the one who says it, and the VERY NEXT turn must say what actually
   happened instead. "People think X, but that's wrong" followed by anything other than
   the real cause leaves the viewer with a hole where the answer should be, and that is
   worse than never raising it.
0. A narration line marked [KEEP] carries the whole point of the episode — usually the
   thing everyone believes that turns out to be wrong. Its turn must still say THAT claim,
   with its own nouns, not a summary of it. Compressing "the common belief that Kodak
   ignored digital cameras is wrong" down to "2013 was a hard year" throws away the only
   reason to watch. Keep the claim; cut everything around it instead.
3a. THE FIRST TURN DECIDES WHETHER ANYONE WATCHES. It must do one of three things, and
   nothing else counts: carry a figure, contradict something the viewer already believes,
   or speak to the viewer as "you"/"your". A plain "How hot is a summer day in Phoenix?"
   promises nothing and the viewer scrolls — measured on 18 real episodes, 7 opened like
   that. Write "How hot does your car get in a Phoenix summer?" instead: same question,
   now it is about them.
3b. Speaker "b" talks like a working analyst being interviewed, not like a host: states the
   figure, then one clause of what it means, and stops. No exclamation marks, no "wow", no
   "get this", no rhetorical questions back, no selling. Confidence comes from being brief
   and specific, and specificity comes from the figure they were given.
3c. THE VIEWER MUST BE IN THE EPISODE. At least two turns say "you" or "your" and tie the
   figure to the viewer's own life — their commute, their kitchen, their paycheck, their
   body. Measured on 18 real episodes: 6 of them never said "you" once. An explainer that
   never mentions the person watching is a lecture, and people do not stay for lectures.
3d. THE LAST TURN IS NOT A NUMBER. It is the one sentence the viewer repeats to someone
   else tomorrow. Measured endings that FAILED: "Three times bigger." · "Twenty five
   pounds, the actual weight." · "One is a mound, one is terrain." Each restates a figure
   already said and leaves nothing to carry. Close on what it means for them instead:
   "You have been paying for the trip, not the cup." Never end on digits.
4. Plain spoken American English. Contractions are fine. No narrator voice, no "as you can
   see", nobody explains what the audience is looking at.
5. Keep the same number of turns as there are narration lines, or at most two more.

6. Every turn MUST carry "i": the number of the narration line it delivers, copied from the
   list above. Two turns may share the same "i" (a question then its answer), and the numbers
   must never go backwards. This is how the on-screen figure card is placed next to the turn
   that actually says it — get "i" wrong and the viewer hears one number while reading another.

Return ONLY a JSON array: [{"i":0,"ai":"a","chu":"...","cx":"trung_tinh"}]
"ai" is "a" for the first character and "b" for the second.
"cx" is one of exactly these: trung_tinh, bat_ngo, tu_tin, nghi_ngo, vui, buon.
Speaker "a" may use bat_ngo when a figure surprises them. Speaker "b" uses ONLY tu_tin or
trung_tinh — a professional does not gasp at their own data. This is an explainer channel,
not a comedy: never angry, never giddy.
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


def loc_the_so(so_lieu: list, cau: list) -> tuple:
    """Bỏ thẻ số KHÔNG được đọc lên, và thẻ mang con số đã hiện rồi. Sửa TẠI CHỖ.

    ── VÌ SAO LÀ HÀM RIÊNG, KHÔNG PHẢI KHỐI INLINE  (8/9/2026) ─────────────────────────
    Bản đầu viết thẳng trong `mot_tap`, và cổng canh nó chỉ kiểm được *"tên `_duoc_noi` có
    xuất hiện trong tệp không"*. Thử ngược: đổi `if not _duoc_noi(...)` thành `if False:` —
    cổng vẫn XANH, vì `def _duoc_noi` phía trên vẫn còn đó. Một cổng đo sự có mặt của một cái
    tên không đo được gì (§13.11 · §13.10: cổng phải CHẠY chính mã ấy).

    ── HAI LUẬT ────────────────────────────────────────────────────────────────────────
    1. Số trên thẻ phải nằm trong lời thoại của CHÍNH lượt ấy — dạng chữ số hoặc dạng đọc
       thành chữ. Đo 967 thẻ: 346 (35%) mang số không hề được nói, phần lớn ở NHỊP CHỐT nơi
       §19.2 cố ý cấm số. Người xem NGHE một số và ĐỌC một số khác thì thà không có thẻ.
    2. Một con số chỉ làm thẻ MỘT lần mỗi tập. Bộ 170 hiện `1720` ba lần và `1717` ba lần —
       cơ chế không hỏng, nhưng màn hình lặp, đúng lời anh *"lặp đi lặp lại quá nhiều lần"*.
       Giữ lần ĐẦU: đó là lúc con số mang tin.

    Đo kết quả CUỐI trên 228 tập thật (§13.23): thẻ 1.070 -> 514, mà **213 tập (93%) vẫn còn
    ≥1 thẻ**; 14 tập mất hết, và chúng mất vì MỌI thẻ đều sai số hoặc trùng.
    """
    def _duoc_noi(v, noi) -> bool:
        g = str(v or "").replace(",", "").strip()
        if not g:
            return True
        if g in (noi or "").replace(",", ""):
            return True
        m = re.fullmatch(r"[$]?(\d+)", g)
        if m:
            try:
                if _chuan_so(_doc_so(int(m.group(1)))) in _chuan_so(noi):
                    return True
            except Exception:
                pass
        return False

    def _loi(c) -> str:
        """Lời thoại của một lượt, nhận CẢ HAI hình dạng đang tồn tại trong dây chuyền.

        `mot_tap` giữ `cau` là list TUPLE `(lời, ai, cảm xúc)`; props đã ghi thì giữ `luot` là
        list DICT có khoá `nar`. Bản đầu chỉ nhận dict — cổng gọi bằng dict nên XANH, còn lời
        gọi thật truyền tuple và nổ `AttributeError` ngay lượt dựng đầu tiên.
        §13.15: bài kiểm phải gọi bằng đúng đường mà mã thật gọi."""
        if isinstance(c, (tuple, list)):
            return str(c[0] if c else "")
        if isinstance(c, dict):
            return str(c.get("nar") or "")
        # ── KHÔNG CÓ ĐƯỜNG DỰ PHÒNG "STR(BẤT KỲ THỨ GÌ)"  (thử ngược 8/9/2026) ─────────
        # Bản đầu kết bằng `return str(c or "")`. Nó làm phép thử ngược MÙ: gỡ hẳn nhánh
        # tuple ra thì tuple rơi xuống đây, thành `"('It collapsed in 1720.', 0, 'trung_tinh')"`
        # — chuỗi ấy VẪN chứa `1720` nên cổng thấy mọi thứ bình thường.
        # Tệ hơn: nó khiến con số nằm ở trường CẢM XÚC hay chỉ số người nói cũng tính là
        # "đã được đọc lên". Một đường dự phòng đoán bừa trả lời sai mà không báo — thà nổ
        # (§15.2: "không biết" và "đã tìm, không có" phải là hai câu khác nhau).
        raise TypeError(f"loc_the_so: không biết đọc lời thoại từ {type(c).__name__}")

    bo_lech = 0
    for t, x in enumerate(so_lieu):
        if x and x.get("k") == "so" and t < len(cau):
            if not _duoc_noi(x.get("so"), _loi(cau[t])):
                so_lieu[t] = None
                bo_lech += 1
    da, bo_lap = set(), 0
    for t, x in enumerate(so_lieu):
        if x and x.get("k") == "so":
            k = str(x.get("so") or "").replace(",", "").strip().lower()
            if k in da:
                so_lieu[t] = None
                bo_lap += 1
            else:
                da.add(k)
    return bo_lech, bo_lap


def _chuan_so(s: str) -> str:
    """Chuẩn hoá để so dạng ĐỌC THÀNH CHỮ: bỏ dấu, hạ chữ thường, gộp mọi gạch nối.

    `_du_so` đã trả giá cho đúng chỗ này: mô hình viết `Fifty‑nine` bằng U+2011 nên phép so
    ASCII trượt và đốt ba vòng gọi AI mỗi tập (§18.11). Sáu dạng gạch nối Unicode, không phải
    một."""
    # NFKD gộp các biến thể gạch nối về dạng cơ sở, rồi phép thay MỌI ký tự không phải
    # chữ-số bằng dấu cách nuốt nốt phần còn lại — nên không cần liệt kê sáu dấu gạch nối
    # Unicode như bản đầu của em: danh sách ấy KHÔNG làm gì cả, và một dòng mã trông có việc
    # mà không có việc là chỗ phiên sau tin nhầm (§15.12).
    return re.sub(r"[^a-z0-9 ]", " ",
                  unicodedata.normalize("NFKD", str(s or "")).lower())


def _doc_so(n: int) -> str:
    """Số thành CHỮ như người Mỹ đọc.

    ── TRẦN 9999 LÀ MỘT GIẢ ĐỊNH, VÀ NÓ SAI  (đo 6/9/2026) ────────────────────────────────
    Chú thích cũ: *"chỉ cần tới hàng nghìn — số lớn hơn thì mô hình gần như luôn viết bằng chữ
    số, và cổng đã bắt được dạng ấy"*. Nghe hợp lý, và đọc bản thảo thật thì sai:

        "That gap is thirty-one thousand six hundred twenty-three times more energy"

    31.623 > 9999 nên hàm trả CHUỖI RỖNG, `bool(c)` false, cổng kết luận "chưa đọc" — rồi đốt
    **2 vòng gọi AI** để bắt viết lại một câu đã đúng, và cuối cùng vẫn in `số liệu THIẾU`.
    §13.8: cổng bắt oan tệ hơn cổng không bắt, và ở đây nó còn tiêu hạn mức.

    Cùng họ với mọi lỗi hôm nay: một chú thích đọc rất có căn cứ, viết đúng ở thời của nó, và
    không ai đi đo lại khi ngữ cảnh đổi — ở đây ngữ cảnh đổi vì chính em bắt mô hình PHẢI đọc
    con số lên, nên nó bắt đầu viết số lớn bằng chữ (§12.5).

    Nay đệ quy tới hàng tỉ. Trần 10^12 chỉ để chặn đầu ra vô nghĩa, không phải một giới hạn
    thật của tiếng Anh."""
    if n < 0 or n >= 10 ** 12:
        return ""
    if n < 20:
        return _DON_VI[n]
    if n < 100:
        c, d = divmod(n, 10)
        return _CHUC[c] + ("-" + _DON_VI[d] if d else "")
    if n < 1000:
        t, r = divmod(n, 100)
        return _DON_VI[t] + " hundred" + (" " + _doc_so(r) if r else "")
    for goc, ten in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
        if n >= goc:
            t, r = divmod(n, goc)
            return _doc_so(t) + " " + ten + (" " + _doc_so(r) if r else "")
    return ""


def _doc_gon(s: str) -> str:
    """Con số cho LỜI NÓI. Màn hình giữ số CHÍNH XÁC; miệng người thì không đọc được nó.

    ── VÌ SAO  (soi khung vòng thứ sáu, 6/9/2026) ─────────────────────────────────────────
    Cổng `_du_so` đòi mọi con số trên bảng phải được đọc lên (anh dặn — nhiều người NGHE mà
    không nhìn). Với `31,622,776,602x` thì mô hình làm đúng điều được bảo:

        "That's thirty-one billion six hundred twenty-two million seven hundred seventy-six
         thousand six hundred two times the energy."

    18 chữ, bong bóng NĂM DÒNG, che hẳn khối số phía dưới. Và không luật nào cứu được: không
    câu tiếng Anh nào chứa con số ấy trong mười chữ. Trần chữ và cổng đọc-số **đánh nhau**, và
    em đã đi sửa hình học ba vòng trước khi nhận ra hai luật của chính mình mâu thuẫn.

    Người thật nói "ba mươi mốt tỉ lần". Con số chính xác là việc của MÀN HÌNH — nó ở đó, code
    tính ra, người xem đọc được. Lời nói mang QUY MÔ.

    Rút gọn do CODE, không do mô hình: đây là con số chảy vào sản phẩm, và AI không bao giờ
    được cấp một con số.
    """
    m = re.match(r"^([^\d\-]*)(-?[\d,]+(?:\.\d+)?)(.*)$", str(s or "").strip())
    if not m:
        return str(s or "")
    dau, so, duoi = m.group(1), m.group(2), m.group(3)
    try:
        v = float(so.replace(",", ""))
    except ValueError:
        return str(s or "")
    for goc, ten in ((1e9, "billion"), (1e6, "million")):
        if abs(v) >= goc:
            r = v / goc
            # Một chữ số thập phân tới 100: "31.6 billion" khớp với `31,622,776,602` đang hiện
            # trên màn, còn làm tròn thành "32 billion" thì TAI nghe một số, MẮT thấy số khác.
            sr = f"{r:.1f}".rstrip("0").rstrip(".") if r < 100 else f"{r:.0f}"
            # `31,622,776,602x` -> hậu tố "x" phải thành chữ đọc được, không dính vào đơn vị
            # ("32 billionx" là thứ không ai đọc lên được).
            hau = " times" if duoi[:1].lower() == "x" else duoi
            return f"{dau}{sr} {ten}{hau}".strip()
    return str(s or "")


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
        return (_doc_gon(g(n["so"])) + " " + g(n.get("don"))).strip()
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


def _da_doc_trong(x: str, van: str) -> bool:
    """Con số `x` có được đọc trong đoạn `van` không — chữ số HOẶC dạng đọc bằng chữ."""
    g = van.lower().replace("\u2019", "'")
    for _d in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"):
        g = g.replace(_d, "-")
    v = re.sub(r"[^\d.]", "", x).rstrip(".")
    if not v:
        return True
    if re.sub(r"[^\d.]", "", x).rstrip(".") in re.sub(r"[^\d.]", "", g):
        return True
    if x.lower() in g:
        return True
    if "." in v:
        ng, _, le = v.partition(".")
        le = le.rstrip("0")
        if ng.isdigit() and le.isdigit() and len(le) == 1:
            c = _doc_so(int(ng))
            return bool(c) and f"{c} point {_doc_so(int(le))}" in g
        v = ng
    if not v.isdigit() or len(v) > 12:
        return False
    c = _doc_so(int(v))
    return bool(c) and c in g


_DON_CHU = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,
            "nine":9,"ten":10,"eleven":11,"twelve":12,"thirteen":13,"fourteen":14,
            "fifteen":15,"sixteen":16,"seventeen":17,"eighteen":18,"nineteen":19,
            "twenty":20,"thirty":30,"forty":40,"fifty":50,"sixty":60,"seventy":70,
            "eighty":80,"ninety":90}
_NHAN_CHU = {"hundred":100, "thousand":1000, "million":10**6, "billion":10**9,
             "trillion":10**12}


def _so_trong(van: str) -> set:
    """Mọi GIÁ TRỊ số nhắc tới trong câu — cả chữ số lẫn số viết bằng chữ.

    Ghép chữ thành giá trị thay vì gắn cờ từng từ: bản dò đầu tiên của em cho `hundred` và
    `million` là "số lạ" ở 12/18 tập, trong khi chúng là THÀNH PHẦN của những số hợp lệ
    ("one billion steps"). Một bộ dò kêu 12/18 mà hai phần ba là oan thì không dùng được
    (§13.8) — phải ghép "one hundred ninety" thành 190 rồi mới so.
    """
    ra = set()
    for x in re.findall(r"\b\d[\d,\.]*\b", van or ""):
        g = x.replace(",", "").rstrip(".")
        if g:
            ra.add(g)
    tu = re.findall(r"[a-z]+", (van or "").lower())
    cum = tong = 0
    for w in tu + ["\x00"]:
        if w in _DON_CHU:
            cum += _DON_CHU[w]
        elif w in _NHAN_CHU:
            n = _NHAN_CHU[w]
            if n >= 1000:
                tong += max(cum, 1) * n; cum = 0
            else:
                cum = max(cum, 1) * n
        else:
            v = tong + cum
            if v:
                ra.add(str(v))
            cum = tong = 0
    return ra


def _so_kich_ban(man: list, loi: list) -> set:
    """Mọi số HỢP LỆ — tức mọi số do kịch bản (Python) cấp."""
    ra = set()
    for x in list(man or []) + list(loi or []):
        ra |= _so_trong(str(x or ""))
    return ra


def _du_so(loi: list, thoai: list, man: list = None) -> list:
    """Con số nào ĐANG HIỆN trên màn (hoặc có trong lời dẫn) mà lời thoại không đọc.

    `man` là danh sách song song với `loi`: con số panel ấy sẽ hiện. Thiếu nó thì hàm quay về
    hành vi cũ — chỉ soi lời dẫn — và đó chính là trạng thái đã cho ra "ĐỦ" trên một tập câm
    hoàn toàn về số. Nên chỗ gọi PHẢI truyền `man`; cổng dưới đây canh việc ấy."""
    # ── NHỊP NÀO CÓ THẺ THÌ THẺ LÀ NGUỒN DUY NHẤT  (anh gửi ảnh, 7/9/2026) ──────────────
    # Anh soi ra một khung: thẻ hiện **`$213K`** mà bong bóng đọc *"two hundred twelve thousand
    # five hundred thirty seven dollars thirty years"* — 11 chữ, bốn dòng, che hẳn cái thẻ.
    #
    # Gợi ý ON SCREEN đưa xuống đã đúng (`$213K over 30 years`). Con số `212,537` đến từ LỜI
    # DẪN, và vòng dưới đây gom số từ **cả lời dẫn lẫn thẻ** — nên cổng đòi mô hình đọc một con
    # số mà MÀN HÌNH KHÔNG HỀ HIỆN.
    #
    # Luật anh giao là *"số TRÊN MÀN HÌNH phải được đọc lên"* (người nghe mà không nhìn). Một
    # con số chỉ nằm trong lời dẫn thì không ở trên màn hình; bắt đọc nó là làm quá luật, và
    # cái giá trả bằng đúng thứ luật ấy sinh ra để bảo vệ — cái thẻ bị che.
    # Nên: nhịp NÀO CÓ thẻ thì chỉ đòi con số của thẻ; nhịp không có thẻ mới xét lời dẫn.
    goc = set()
    _man = list(man or [])
    _nguon = [(_man[i] if i < len(_man) and _man[i] else t) for i, t in enumerate(loi)]
    _nguon += _man[len(loi):]
    for t in _nguon:
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
    # ── ĐÒI THEO TỪNG NHỊP, KHÔNG ĐÒI "Ở ĐÂU ĐÓ TRONG TẬP"  (7/9/2026) ─────────────────
    # Bản cũ gom mọi lời thoại thành MỘT chuỗi rồi hỏi "con số này có xuất hiện không". Nên
    # một tập nói `$213K` ở lượt 9 vẫn tính là ĐỦ cho cái thẻ đang hiện ở lượt 1 — người xem
    # thì thấy thẻ ở lượt 1 và nghe số ở lượt 9. Đo: sau khi đã sửa chỗ ĐẶT thẻ, vẫn còn 27%
    # thẻ rơi vào lượt không đọc nó, và toàn bộ phần còn lại là dạng này: mô hình diễn nhịp ấy
    # bằng một câu HỎI, con số để dành cho lượt sau.
    #
    # Nay mỗi lượt đã khai `i` (nhịp nó diễn), nên đòi được ĐÚNG CHỖ: con số của nhịp `i` phải
    # được đọc trong một lượt khai `i` ấy. Đây là điều luật của anh nói từ đầu — *"số trên màn
    # hình phải được đọc lên"* — chỉ khác là giờ nó kiểm được theo từng màn hình, không phải
    # theo cả tập.
    # ── LƯỢT ĐỌC ĐÚNG SỐ NHƯNG KHAI SAI NHỊP: SỬA, ĐỪNG BẮT VIẾT LẠI  (7/9/2026) ─────────
    # Dựng thật `realcost` tập 4: cổng báo thiếu `$331K` và `48,358`, mà đọc lời thoại lên thì
    # CẢ HAI đều được nói đúng — chỉ là lượt ấy khai `i` trỏ sang nhịp khác. Hậu quả đúng thứ
    # anh chê: *"nói số liệu thì không hiện, hiện thì không nói"*. Cổng bắt đúng, nhưng nó
    # tiêu HAI vòng gọi AI rồi vẫn giao bản hỏng — máy sửa được thì máy sửa (§13.12).
    #
    # BẢN ĐẦU CỦA CHÍNH BẢN VÁ NÀY LÀ MỘT CỖ MÁY ĐOÁN, và log dựng thật chỉ ra ngay: nó kéo
    # `$14` qua bốn nhịp liên tiếp (0 -> 2 -> 3 -> 10) và đẩy `3,500` đi rồi kéo về. Hai lỗi:
    #   · phép "khớp duy nhất" đếm số LƯỢT nói con số ấy, trong khi thứ cần duy nhất là số
    #     NHỊP muốn nó — `$14` là chủ đề cả tập nên nhịp nào cũng muốn;
    #   · không có sổ nên một lượt bị dời nhiều lần, mỗi vòng lặp một lần.
    # Nay: một lượt chỉ được dời ĐÚNG MỘT LẦN, và chỉ khi con số ấy có ĐÚNG MỘT nhịp đang
    # thiếu nó — hai điều kiện, và thiếu điều kiện nào thì để cổng chặn, đừng đoán.
    if man and any("i" in (x or {}) for x in thoai):
        _thieu_o = {}                       # con số -> [nhịp đang thiếu nó]
        for _i, _m in enumerate(man):
            _ds = [x.strip() for x in _SO.findall(_m or "") if any(c.isdigit() for c in x)]
            if not _ds:
                continue
            _noi = " ".join(t.get("chu", "") for t in thoai if int(t.get("i", -1)) == _i)
            if not _da_doc_trong(_ds[0], _noi):
                _thieu_o.setdefault(_ds[0], []).append(_i)
        _da_doi = set()
        for _x, _nhips in _thieu_o.items():
            if len(_nhips) != 1:
                continue                    # hai nhịp cùng thiếu -> không biết cho ai, để cổng chặn
            _dich = _nhips[0]
            _ung = [k for k, t in enumerate(thoai)
                    if k not in _da_doi and _da_doc_trong(_x, t.get("chu", ""))
                    and int(t.get("i", -1)) != _dich]
            # Chỉ dời lượt mà nhịp GỐC của nó không cần chính nó: dời đi để chữa nhịp này mà
            # làm hỏng nhịp kia thì chỉ là chuyển chỗ cái lỗi.
            _ung = [k for k in _ung
                    if not any(_da_doc_trong(y, thoai[k].get("chu", ""))
                               for y in _thieu_o if y != _x)]
            if len(_ung) == 1:
                _cu = int(thoai[_ung[0]].get("i", -1))
                thoai[_ung[0]]["i"] = _dich
                _da_doi.add(_ung[0])
                print(f"   ↔ lượt đọc «{_x}» khai nhịp {_cu} -> sửa về {_dich}")

    _co_i = any("i" in (x or {}) for x in thoai)
    if _co_i and man:
        thieu_nhip = []
        _da_doi_hoi = set()
        for _i, _m in enumerate(man):
            if not _m:
                continue
            # CHỈ con số CHÍNH của thẻ. `so_tren_man` ghép `so` + `don`, mà `don` hay chứa
            # số của đơn vị (*"$213K over 30 years"*) — đòi đọc cả `30` là bắt oan: `30 years`
            # là ngữ cảnh, không phải con số thẻ đang khoe. Bản đầu của cổng này đòi cả hai và
            # trượt ngay ca đúng đầu tiên.
            _ds = [x.strip() for x in _SO.findall(_m) if any(c.isdigit() for c in x)]
            _goc = {_ds[0]} if _ds else set()
            if " and " in _m and len(_ds) >= 3:
                _goc = set(_ds)
                def _v(x):
                    try:
                        return float(re.sub(r"[^\d.]", "", x) or 0)
                    except Exception:
                        return 0.0
                _goc = {max(_goc, key=_v)}
            _noi = " ".join(x.get("chu", "") for x in thoai if int(x.get("i", -1)) == _i)
            if not _noi:
                continue
            for _x in _goc:
                # CHỈ đòi ở nhịp ĐẦU TIÊN hiện con số ấy. Luật 1c của `LENH_THOAI` dặn mô
                # hình *"nói mỗi con số ĐÚNG MỘT LẦN, đừng lặp lại con số lượt trước đã nói"*,
                # trong khi bản cũ của cổng đòi MỌI nhịp mang thẻ `$14` đều phải có lượt đọc
                # `$14` — mà `realcost` hiện `$14` ở ba nhịp vì đó là chủ đề cả tập. Hai luật
                # trong cùng một hệ đánh nhau, và cái thua là mô hình: nó làm đúng lệnh dặn
                # rồi bị cổng đánh trượt, tiêu hai vòng gọi AI rồi vẫn giao bản kèm cảnh báo.
                # Thẻ lặp là cùng một sự thật; người xem nghe một lần và thấy ba lần là đúng.
                if _x in _da_doi_hoi:
                    continue
                _da_doi_hoi.add(_x)
                if not _da_doc_trong(_x, _noi):
                    thieu_nhip.append(_x)
        # THAY THẾ phép kiểm cả-tập, không bổ sung vào nó. Bản đầu `return` chỉ khi có thiếu
        # rồi rơi xuống phép cũ khi đạt — nên phép cũ (gom cả tập, đòi cả số trong ĐƠN VỊ) lại
        # bắt oan đúng ca vừa được xác nhận là đúng. Một phép đo chặt hơn mà để phép lỏng hơn
        # chạy sau thì kết quả là phép lỏng quyết định.
        return sorted(set(thieu_nhip))
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
        if not v:
            return False
        # ── SỐ THẬP PHÂN CŨNG ĐỌC ĐƯỢC  (đo 6/9/2026) ──────────────────────────────────
        # Bản cũ trả False cho mọi số có dấu chấm. Đúng khi mọi con số đều nguyên; sai kể từ
        # lúc `_doc_gon` bắt đầu sinh "31.6 billion" cho lời nói — mô hình viết
        # *"thirty-one point six billion"*, hoàn toàn đúng, và cổng chấm trượt.
        # Cùng họ với mọi lỗi hôm nay: một bản sửa ở tầng trên đổi ngữ cảnh của một hàm ở
        # tầng dưới, và hàm ấy giữ nguyên giả định cũ (§12.5).
        if "." in v:
            ng, _, le = v.partition(".")
            le = le.rstrip("0")
            if not ng.isdigit() or not le.isdigit() or len(le) > 1:
                return False
            c = _doc_so(int(ng))
            return bool(c) and f"{c} point {_doc_so(int(le))}" in _cl
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


# ── SÀN SỐ LƯỢT: MỘT CON SỐ, HAI CHỖ CƯỠNG CHẾ  (8/9/2026) ──────────────────────────────
# `doi_thoai` vứt mọi bản nháp dưới bốn lượt, còn `_lat_short` cắt theo sàn BA nhịp. Hai sàn
# nói về cùng một thứ mà không khớp nhau, nên mọi short ba nhịp đều bị `doi_thoai` loại sạch
# rồi trả rỗng — đo được: bộ 128 vẫn mất clip thứ tư dù lát đã dày lên đúng 3 (bản vá trước
# chữa được cái mỏng 2, không chữa được cái lệch sàn).
# Một hằng số, hai chỗ đọc. §11: đừng bao giờ tạo nguồn sự thật thứ hai cho cùng một số.
SAN_LUOT = 4
TRAN_LAT = 7        # trần nhịp mỗi short ≈ 37 giây, xem `_lat_short`

def doi_thoai(loi: list, vai: list, man: list = None) -> list:
    # ── HỒ GROQ RỖNG KHÔNG ĐƯỢC LÀM ĐỨNG CẢ NHÀ MÁY  (đo 8/9/2026) ─────────────────────
    # 15/15 lượt render từ 6/9 tới 8/9 đều ĐỎ, cả 18 luồng cùng một dòng `⚠ Groq: 0 khoá` ->
    # `❌ không dựng được lời thoại` -> bỏ cả bộ. Và đo trên Drive: 115/125 kho có video mới
    # nhất là **4/9** — nhà máy đứng bốn ngày.
    #
    # Gốc trực tiếp là `GROQ_KEYS` chưa được nối vào workflow (đã vá). Nhưng gốc SÂU hơn là
    # chỗ này KHÔNG CÓ TẦNG DỰ PHÒNG: một secret thiếu làm chết đúng 18/18 luồng. §7 đã dựng
    # bốn tầng cho NỀN chỉ để chuyện ấy không xảy ra với hình; lời thoại thì chưa có tầng nào.
    #
    # `phim_canh._goi_cf` viết bằng `@cf/openai/gpt-oss-120b`, chạy bằng CHÍNH `CF_KEYS` —
    # thứ chắc chắn có, vì cả đường vẽ ảnh sống nhờ nó. Nó đã phục vụ bảng phân cảnh của bộ
    # v10 từ 6/9, tức đường đã chạy thật, không phải mã mới (§13.1).
    #
    # Chỉ dùng khi hồ Groq RỖNG — không phải mỗi khi Groq trả lời kém. Groq vẫn là đường
    # chính; đây là phanh tay, và một tập viết bằng model yếu hơn vẫn hơn hẳn không có tập.
    keys = C._khoa_groq()
    if not keys:
        print("   ↩ hồ Groq RỖNG — viết thoại bằng Cloudflare gpt-oss-120b (đường dự phòng)")
    man = man or [""] * len(loi)
    dong = [f"{i}. {t}" + (f"   [ON SCREEN: {m}]" if m else "")
            for i, (t, m) in enumerate(zip(loi, man))]
    u = (f"CHARACTER A: {vai[0]['vai']} — {vai[0]['ta']}\n"
         f"CHARACTER B: {vai[1]['vai']} — {vai[1]['ta']}\n\n"
         f"NARRATION ({len(loi)} lines):\n" + "\n".join(dong))
    thieu: list = []
    for vong in range(3):
        _lenh = LENH_MOT_GIONG if MOT_GIONG else LENH_THOAI
        _goi = ((lambda sp, up: C._goi(sp, up, keys)) if keys
                else (lambda sp, up: C._goi_cf(sp, up)))
        t = _goi(_lenh,
                   u if vong == 0 else u + (
            "\n\nYour previous answer DROPPED these figures: " + ", ".join(thieu) +
            ". Each one is on a card the viewer will see. Rewrite so every one of them is "
            "spoken out loud, digits exactly as written above, in the turn for its own line. "
            "A viewer listening without watching must hear each figure."))
        ds = C._tach_json(t) or []
        # Mô hình chép cả SỐ THỨ TỰ của câu dẫn vào lời ("0. The real cause…"). Nó đang làm
        # đúng thứ đề bài đánh số, và người xem thì nghe thấy "không chấm". Dọn ở đây, chỗ
        # duy nhất biết chuỗi vừa về từ mô hình.
        #
        # ── DẠNG THỨ HAI: TÊN TRƯỜNG + SỐ  (anh soi ra trên khung, 7/9/2026) ──────────────
        # Bản đầu chỉ bắt `7.` và `7)`. Đo trên bản dựng thật thì mô hình viết **`i7:`** — nó
        # chép luôn TÊN TRƯỜNG `"i"` mà đề bài đặt, rồi mới tới số. Phụ đề hiện `i1: Kodak
        # started as…` và giọng đọc lên nguyên chữ ấy.
        # Không liệt kê thêm ví dụ (§13.9): quy luật là *một tham chiếu tới chỉ số mà lượt này
        # ĐÃ mang trong trường riêng* — chữ cái liền số, rồi dấu ngăn.
        # Hai chỗ siết để khỏi bắt oan: chữ cái phải DÍNH số (nếu không thì *"A 3-year gap"*
        # bị xén mất đầu), và số tối đa hai chữ số (nếu không thì *"1888 was the year"* bị xén).
        for _x in ds:
            if isinstance(_x, dict):
                _c0 = str(_x.get("chu", ""))
                # ── DẤU NỘI BỘ `[KEEP]` KHÔNG ĐƯỢC LÊN MÀN HÌNH  (anh soi khung, 7/9/2026) ──
                # `mot_tap` đã gỡ `[KEEP]` khỏi từng NHỊP, nhưng danh sách `loi` đưa cho mô
                # hình được lấy TRƯỚC lượt gỡ ấy — và đó là bản có chủ ý: đề bài dạy mô hình
                # rằng câu mang dấu này là cú lật của tập. Cái không lường được là mô hình
                # chép luôn cái dấu vào lời thoại, nên phụ đề hiện *"[KEEP]Despite the common
                # misconception…"*. Vá ở nhịp mà để nguyên nhánh đi ra màn hình — đúng họ §6.
                # Gỡ MỌI dấu ngoặc vuông ở đầu câu, không riêng `[KEEP]`: dấu nội bộ nào cũng
                # sẽ rò cùng một đường, và liệt kê từng cái là danh sách vô hạn (§13.9).
                _c0 = re.sub(r"^\s*\[[A-Z_]{2,12}\]\s*", "", _c0)
                _x["chu"] = re.sub(r"^\s*(?:[A-Za-z]\d{1,2}|\d{1,2})\s*[.):]\s*", "", _c0)
        def _chi_so(x, mac_dinh):
            """Chỉ số câu dẫn mà lượt này diễn. Sai kiểu / ngoài khoảng -> quay về ước lượng."""
            try:
                v = int(x.get("i"))
            except Exception:
                return mac_dinh
            return v if 0 <= v < len(loi) else mac_dinh
        def _bo_stt(chu: str, i: int) -> str:
            """Bỏ tiền tố chỉ số mà mô hình chép vào lời — dùng CHÍNH chỉ số của lượt.

            ── VÌ SAO KHÔNG DÙNG MỘT REGEX RỘNG HƠN  (7/9/2026) ──────────────────────────
            Đo trên ba bản dựng thật, mô hình rò tiền tố theo BA dạng khác nhau: `0.` · `i7:`
            · và `1 Kodak` (số TRẦN, không dấu ngăn). Nới regex tới dạng thứ ba thì nó xén
            luôn *"1 in 5 Americans"* — một câu hoàn toàn đúng — và cổng bắt oan tệ hơn cổng
            không bắt (§13.8).
            Không cần đoán: lượt này ĐÃ mang chỉ số của nó trong trường `i`. Chỉ xén khi con
            số ở đầu câu ĐÚNG BẰNG chỉ số ấy. Hết mơ hồ, và không thể bắt oan trừ khi câu thật
            tình cờ mở đầu bằng đúng số thứ tự của chính nó.
            """
            # ── DẠNG THỨ TƯ: CHỈ SỐ VIẾT BẰNG CHỮ, KÈM NHÃN  (8/9/2026) ──────────────
            # Bộ 126: **8/8 khung** mở bằng `Line two:` · `Line seven:` · `Line twenty-five:`
            # — tức mô hình đọc số thứ tự thành CHỮ và dán thêm nhãn `Line`. Regex cũ chỉ
            # biết chữ số, và còn đòi chữ HOA ngay sau (`Line two: so let us...` là chữ
            # thường), nên nó trượt sạch. Không có lỗi nào báo; nó chỉ hiện trên mọi phụ đề.
            #
            # Vẫn giữ nguyên nguyên tắc §19.17 — chỉ xén khi con số ĐÚNG BẰNG chỉ số của
            # chính lượt này — nên nới rộng ở đây không mở ra chỗ bắt oan nào: một câu thật
            # phải vừa mở bằng nhãn, vừa mang đúng số thứ tự của chính nó.
            _chu_so = _doc_so(i).replace("-", "[-\u2010-\u2015]?")   # §18.11: sáu dạng gạch
            _nhan = r"(?:line|turn|beat|item|step|point|no\.?)\s+"
            # A · có nhãn -> xén bất kể chữ sau hoa hay thường, rồi viết hoa lại
            ra = re.sub(rf"^\s*{_nhan}(?:{i}|{_chu_so})\s*[.):\-\u2013\u2014]?\s+",
                        "", chu, flags=re.I)
            if ra is not chu and ra != chu:
                return ra[:1].upper() + ra[1:] if ra else chu
            # B · không nhãn -> giữ đúng độ chặt cũ: phải có dấu ngăn và chữ HOA theo sau
            return re.sub(rf"^\s*[A-Za-z]?(?:{i}|{_chu_so})\s*[.):]?\s+(?=[A-Z])", "", chu)
        ra = []
        for k, x in enumerate(ds):
            if not str(x.get("chu") or "").strip():
                continue
            _i = _chi_so(x, min(len(loi) - 1, k))
            ra.append({"chu": _bo_stt(" ".join(str(x.get("chu") or "").split()), _i),
                       "ai": "b" if str(x.get("ai", "a")).lower().startswith("b") else "a",
                       "cx": str(x.get("cx") or "trung_tinh"),
                       "i": _i})
        if len(ra) < SAN_LUOT:
            continue
        # ── TRẦN SỐ LƯỢT: MÁY CẮT, KHÔNG ĐỐT MỘT VÒNG GỌI AI  (đo 6/9/2026) ─────────────
        # Luật 5 nói "giữ đúng số lượt bằng số câu dẫn, nhiều nhất hơn hai" — và chỉ CHẤM chứ
        # không CHẶN, tức nó là lời khuyên (§13.3). Sau khi em hạ trần chữ 12 -> 10 và thêm
        # "mỗi lượt nhiều nhất MỘT con số", mô hình bắt đầu TÁCH một câu dẫn thành hai lượt:
        # đo `howloud` tập 6 ra **18 lượt / 53 giây** trong khi 9 câu dẫn -> 33 giây.
        # Bản sửa của em tạo ra hồi quy này, đúng §12.5.
        #
        # Không chặn để bắt viết lại: hại của nó là video dài gấp rưỡi, không phải hình hỏng —
        # máy sửa được thì máy sửa (§13.12 · nấc `don()` của §13.23). Cắt phần GIỮA và giữ lượt
        # CUỐI, vì lượt cuối là cú chốt: cắt từ đuôi thì mất đúng chỗ đóng bài.
        # Bỏ lượt KHÔNG mang chữ số trước: cắt bừa phần giữa có thể làm rơi một con số bắt
        # buộc, và cổng `_du_so` ngay dưới sẽ bắt viết lại — tức bản "máy tự sửa" lại đi đốt
        # đúng cái vòng gọi AI mà nó sinh ra để tiết kiệm.
        _tran_luot = len(loi) + 2
        if len(ra) > _tran_luot:
            _giu = [i for i, x in enumerate(ra) if any(c.isdigit() for c in x["chu"])]
            _giu = set(_giu) | {0, len(ra) - 1}
            # ── ĐỪNG BỎ LƯỢT ĐANG NGĂN HAI LƯỢT CÙNG NGƯỜI DÍNH NHAU  (7/9/2026) ────────
            # Lượt không mang số gần như luôn là câu HỎI của vai A, và bỏ nó đi thì hai lượt
            # của chuyên gia dính vào nhau. Bản trước chữa ở phía SAU (chèn lại một câu hỏi),
            # nhưng ngân sách chèn có hạn: `realcost` cắt xong còn SÁU cặp dính mà chỉ nhét
            # được hai câu nối, ra bốn cặp dính trong bản giao đi.
            # Chữa ở chính chỗ gây ra: xếp những lượt mà bỏ đi sẽ tạo cặp dính xuống CUỐI
            # danh sách ứng viên, chỉ dùng tới chúng khi không còn gì khác để bỏ. Rẻ hơn
            # nhiều so với chèn bù, và không tốn thêm một lượt nào.
            _ung = [i for i in range(len(ra)) if i not in _giu]
            def _pha(i):
                t, s2 = i - 1, i + 1
                while t in _giu and t >= 0 and False: t -= 1
                return (0 <= t and s2 < len(ra)
                        and ra[t].get("ai") == ra[s2].get("ai"))
            _ung.sort(key=_pha)                      # False (không phá) lên trước
            _bo = _ung[: len(ra) - _tran_luot]
            if len(ra) - len(_bo) > _tran_luot:          # vẫn dư -> cắt tiếp phần giữa
                _con = [x for i, x in enumerate(ra) if i not in set(_bo)]
                _con = _con[:_tran_luot - 1] + [_con[-1]]
                ra = _con
            else:
                ra = [x for i, x in enumerate(ra) if i not in set(_bo)]
            print(f"   ✂ {_tran_luot + len(_bo)} lượt -> {len(ra)} (bỏ lượt không mang số)")
        # ── LUÂN PHIÊN PHẢI ĐƯỢC VÁ LẠI SAU KHI CẮT  (7/9/2026) ────────────────────────
        # Luật 2 đòi hai người nói xen kẽ, và mô hình tuân thủ. Nhưng lượt cắt ngay trên bỏ
        # những lượt KHÔNG mang chữ số — mà lượt không mang số gần như luôn là câu HỎI của
        # vai A. Bỏ chúng đi thì hai lượt B dính vào nhau, và tai nghe ra một người tự nói
        # với mình. Dựng thật `v11_hiddenfee_0004` ra đúng thế: lượt 2 và 3 cùng của B.
        #
        # Bộ cắt sinh ra lỗi này, nên bộ cắt phải vá lại — §13.12: máy sửa được thì máy sửa,
        # đừng đốt một vòng gọi AI cho một chuyện máy làm được. Chỉ lượt MANG SỐ mới buộc
        # thuộc về chuyên gia; lượt không có số thì ai nói cũng đúng vai, nên đổi được.
        # Lượt "khoá cứng vào vai chuyên gia" là lượt KHẲNG ĐỊNH có số. Một CÂU HỎI có số
        # ("Is it really 48,358 dollars?") thì người hỏi nói được, và chuyên gia vẫn là người
        # xác nhận — vai không đổi. Đo `realcost`: gần như mọi lượt đều mang số nên đều bị
        # khoá vào B, và bộ vá luân phiên bó tay hoàn toàn (9 cặp dính trong bản giao đi).
        # Nới đúng một chỗ này mở lại chỗ xoay mà không đụng luật "số liệu do chuyên gia đưa".
        # ── MỘT GIỌNG THÌ TẮT HẲN BỘ LUÂN PHIÊN  (7/9/2026) ────────────────────────────
        # Bộ vá luân phiên sinh ra để chữa "hai lượt liền cùng người". Ở chế độ một giọng thì
        # MỌI cặp đều cùng người, nên nó nhét một câu nối vào GIỮA TỪNG CÂU — dựng thật ra 14
        # lượt mà bảy lượt là "What about the other?". Một cơ chế đúng ở định dạng này là một
        # cỗ máy phá ở định dạng kia (§12.5).
        if not MOT_GIONG:
            _so_cua = lambda x: (any(c.isdigit() for c in x.get("chu", ""))
                                 and not str(x.get("chu", "")).strip().endswith("?"))
            _bo2 = set()
            for _k in range(1, len(ra)):
                if _k - 1 in _bo2 or ra[_k].get("ai") != ra[_k - 1].get("ai"):
                    continue
                _doi = "b" if ra[_k].get("ai") == "a" else "a"
                if not _so_cua(ra[_k]) and (_k + 1 >= len(ra) or ra[_k + 1].get("ai") != _doi):
                    ra[_k]["ai"] = _doi
                elif (_k - 1 > 0 and not _so_cua(ra[_k - 1])
                      and ra[_k - 2].get("ai") != _doi):
                    # `_k - 1 > 0`: KHÔNG bao giờ lật lượt mở đầu. Luật 3 nói người HỎI mở màn,
                    # và một tập mở bằng lượt của chuyên gia thì không còn ai để hỏi — dựng thật
                    # ra "Tobias wonders why we pay extra?", tức chuyên gia tự thuật về người
                    # kia. Bản vá luân phiên không được phép đổi thứ nó không sinh ra để đổi.
                    ra[_k - 1]["ai"] = _doi
                elif not _so_cua(ra[_k]) and _k != len(ra) - 1:
                    # Đổi vai không an toàn ở cả hai phía (đổi xong lại dính vào lượt kế). Lúc
                    # này BỎ hẳn lượt không mang số là đúng: nó vốn là lượt bị trần cắt, và giữ
                    # nó chỉ để nghe một người nói hai lần liên tiếp thì không đáng.
                    _bo2.add(_k)
                elif not _so_cua(ra[_k - 1]) and _k - 1 != 0:
                    _bo2.add(_k - 1)
            if _bo2:
                ra = [x for _i, x in enumerate(ra) if _i not in _bo2]
            # ── TẬP PHẢI MỞ BẰNG LƯỢT HỎI  (7/9/2026) ──────────────────────────────────────
            # Luật 3 nói vai "a" ĐẶT CÂU HỎI và mở màn; đo 18 kênh thì `howlong` mở bằng lượt
            # của chuyên gia. Một tập bắt đầu bằng câu trả lời thì không có câu hỏi nào để trả
            # lời, và người xem mất đúng ba giây đầu — chỗ quyết định lướt hay ở lại (§13.16).
            #
            # Không LẬT vai lượt ấy: lật thì hoặc đụng lượt kế, hoặc biến chuyên gia thành người
            # hỏi. Bỏ hẳn nó khi nó KHÔNG mang số bắt buộc là cách rẻ nhất và không mất dữ kiện
            # nào — lượt sau vốn đã là lượt hỏi.
            while (len(ra) > 2 and ra[0].get("ai") == "b"
                   and not any(c.isdigit() for c in ra[0].get("chu", ""))
                   and ra[1].get("ai") == "a"):
                ra = ra[1:]
            _NOI = ("And the next one?", "What about the other?", "How does that compare?",
                    "So what does that mean?", "And after that?", "Which one is bigger?",
                    "Where does that leave us?", "Then what?", "And the rest?",
                    "How much of a gap is that?")
            # Lệch pha lấy từ TÊN VAI, không phải mã kênh: `doi_thoai` không nhận mã kênh, và
            # tên vai còn tốt hơn — nó đổi theo cả kênh LẪN tập (cặp vai xoay mỗi tập), nên hai
            # tập của cùng một kênh cũng không mở cùng một câu nối. Băm viết tường minh, không
            # dùng `hash()` — `PYTHONHASHSEED` ngẫu nhiên thì máy anh và runner ra hai lịch khác
            # nhau (§13.13, đã trả giá ở bộ Kling).
            _hat = "".join(str(v.get("vai") or "") for v in vai)
            _lech = sum(ord(c) * (k + 1) for k, c in enumerate(_hat)) % len(_NOI)

            # ── LƯỢT ĐẦU MANG SỐ THÌ KHÔNG BỎ ĐƯỢC — CHÈN CÂU HỎI VÀO TRƯỚC  (7/9/2026) ────
            # Vòng trên chỉ bỏ được lượt mở đầu KHÔNG mang số. Dựng thật kênh "vì sao": lượt
            # đầu là *"2013 was the year Kodak's decline became clear"* — mang số nên nó lọt,
            # và tập mở bằng một câu TRẢ LỜI khi chưa ai hỏi gì.
            # Bỏ nó là mất một con số bắt buộc; nên chèn một câu hỏi vào TRƯỚC nó. Câu hỏi
            # không mang dữ kiện nào nên máy viết được mà không vi phạm luật "AI không cấp số".
            if ra and ra[0].get("ai") == "b":
                ra.insert(0, {"i": int(ra[0].get("i", 0)), "ai": "a", "cx": "trung_tinh",
                              "chu": _NOI[_lech % len(_NOI)]})
            # ── HAI LƯỢT SỐ LIỀN NHAU: CHÈN MỘT CÂU HỎI, ĐỪNG ĐỔI VAI  (7/9/2026) ──────────
            # `howhot` tập 4 ra BỐN lượt B liên tiếp, cả bốn đều mang số — không lượt nào đổi
            # vai được (số phải do chuyên gia nói) và không lượt nào bỏ được (bỏ là mất một con
            # số bắt buộc). Hai nhánh trên bó tay đúng ở ca này.
            #
            # Chỗ thiếu là một câu HỎI, và câu hỏi thì không mang dữ kiện nào nên máy viết được
            # mà không vi phạm "AI/tay không bao giờ cấp một con số". Rút từ hồ và lệch pha theo
            # kênh, đúng cách `_loi` đã giải bài lặp câu nối (§15.17): cùng hồ, mỗi kênh bắt đầu
            # ở một chỗ, nên hai kênh dựng cùng vị trí không đọc cùng câu.
            _ket = []
            for _k, _x in enumerate(ra):
                if (_ket and _x.get("ai") == _ket[-1].get("ai") == "b"
                        and _so_cua(_x) and _so_cua(_ket[-1])
                        # ── KHÔNG ĐẶT TRẦN CHO CHÍNH BẢN SỬA  (7/9/2026) ─────────────────────
                        # Bản trước chặn ở `_tran_luot + 2`, và loạt dựng 18 kênh cho thấy trần
                        # ấy chặn đúng thứ cần: `howloud` có BẢY cặp dính mà chỉ nhét được hai
                        # câu nối, giao đi bảy chỗ một người nói hai lần liên tiếp.
                        #
                        # Câu nối chỉ được chèn khi CÓ một cặp dính thật — nó không bao giờ nổ
                        # bừa. Nên đặt trần lên nó là đặt trần lên CÁI CHỮA, không phải lên cái
                        # phí. Giá phải trả là vài giây mỗi câu nối; giá của việc không chữa là
                        # đúng lỗi anh chê từ đầu (*"nhầm vai"*). Đổi đúng chiều.
                        and len(_ket) < 40):
                    _ket.append({"i": _x.get("i", 0), "ai": "a",
                                 "chu": _NOI[(_lech + len(_ket)) % len(_NOI)], "cx": "trung_tinh"})
                _ket.append(_x)
            ra = _ket
            # ── ĐO GIỮ CHÂN NGAY TRÊN LỜI THOẠI ĐÃ DỰNG  (7/9/2026) ────────────────────────
            # Anh: *"đã giữ chân người coi chưa"*. Hai chỗ hỏng đo được trên 18 tập, và cả hai
            # chỉ nhìn thấy Ở ĐÂY — `cham_kich_ban` chấm CÂU DẪN, còn thứ người xem nghe là lời
            # thoại do mô hình viết ở bước này. Em vừa suýt gắn hai trục ấy vào thước sai nguồn
            # lần thứ ba trong ngày (§15.5); đặt phép đo cạnh thứ nó đo mới đúng chỗ.
            #
            # BÁO chứ không CHẶN: một tập ít nói "you" thì nhạt, không hỏng — chặn nó là tiêu
            # một vòng gọi AI cho thứ luật 3c/3d trong lệnh dặn đã lo (§13.23, ba nấc).
            # ── MỘT CHUYÊN GIA NÓI LIÊN TỤC  (anh đề xuất, 7/9/2026) ───────────────────────
            # Định dạng hai người đối thoại là nguồn của phần lớn lỗi hôm nay: 16 cặp nói liền
            # cùng người · câu hỏi đệm vô nghĩa · cú lật bị nén mất vì phải nhét câu 30 chữ vào
            # lượt 5–10 chữ · và "nêu điều sai mà không nói điều đúng" khi câu trả lời rơi vào
            # lượt của vai HỎI. Một giọng thì cả bốn biến mất, và hình đổi theo lời gánh phần
            # kể chuyện — đúng định dạng chuẩn của ngách giải thích.
            # Engine đã có sẵn cờ `hai`; chưa ai bật nó.
            if MOT_GIONG:
                for _x in ra:
                    _x["ai"] = "b"

        _van = " ".join(x.get("chu", "") for x in ra)
        _ban = len(re.findall(r"\byou(?:['\u2019]\w+|r)?\b", _van, re.I))
        _chot = (ra[-1].get("chu") if ra else "") or ""
        if _ban < 2:
            print(f"   ⚠ giữ chân: người xem chỉ xuất hiện {_ban} lần — tập này là bài giảng")
        if re.search(r"\d", _chot):
            print(f"   ⚠ giữ chân: câu chốt đọc lại một con số «{_chot[:34]}» — không mang đi được")
        # ── SỐ NÀO KHÔNG DO KỊCH BẢN CẤP THÌ KHÔNG ĐƯỢC LÊN HÌNH  (7/9/2026) ───────────
        # Anh: *"a người việt, a coi biết đẹp thôi chứ ko đánh giá được nó hay ko"*. Nên em
        # đọc tay lời thoại như một người xem Mỹ, và bắt được lỗi nặng nhất cả buổi:
        #
        #   howmuch tập 4  kịch bản cấp ĐÚNG HAI số: 1.000.000 và 1.000.000.000 bước
        #                  lời thoại nói thêm: "roughly one hundred ninety miles"  (đúng: 500)
        #                                      "circle the earth forty times"      (đúng: 20)
        #
        # Cả hai do MÔ HÌNH BỊA, và cả hai SAI. Nguyên tắc cứng của cả hệ — *AI không bao giờ
        # được cấp một con số* — đang bị vi phạm trong bản giao đi, và không cổng nào thấy:
        # `_du_so` chỉ hỏi "số BẮT BUỘC đã được đọc chưa", không bao giờ hỏi "có số THỪA
        # không". Một cổng đo chiều thiếu thì mù hoàn toàn với chiều thừa.
        #
        # CHẶN chứ không báo (§13.23 nấc ba): một con số bịa là lỗi SỰ THẬT, và ở kênh giải
        # thích thì sai một con số là mất lý do tồn tại. Đây đúng là loại "làm HỎNG sản phẩm",
        # nên nó đáng tiêu một vòng gọi AI.
        _hop = _so_kich_ban(man, loi)
        _la = []
        for _t in ra:
            _c = _t.get("chu", "")
            if " point " in f" {_c.lower()} ":
                continue          # số thập phân đọc bằng chữ: bộ ghép chưa xử được -> THA
            for _v in _so_trong(_c):
                if _v not in _hop and len(_v) > 1:
                    _la.append(_v)
        if _la:
            print(f"   ↻ lời thoại BỊA số {sorted(set(_la))[:4]} — không có trong kịch bản, viết lại")
            continue
        # ── CÂU CÚ LẬT KHÔNG ĐƯỢC NÉN MẤT  (7/9/2026) ────────────────────────────────
        # Dựng thật kênh "vì sao": câu dẫn số 0 là *"Despite the common misconception that
        # Kodak's refusal to invest in digital cameras led to its fall"* — cú lật của cả
        # tập, và là lý do duy nhất để xem. Mô hình nén nó thành *"2013 was the year
        # Kodak's decline became clear"*: đúng sự thật, và ném đi toàn bộ cú lật.
        #
        # Cổng đo bằng TỪ NỘI DUNG chung: lượt diễn câu ấy phải mang ít nhất hai từ riêng
        # của nó. Đếm từ chung thay vì so chuỗi, vì mô hình được phép diễn đạt lại — nó chỉ
        # không được phép bỏ mất mệnh đề.
        _giu = [i for i, x in enumerate(loi or []) if str(x or "").startswith("[KEEP]")]
        _mat = []
        for _i in _giu:
            _goc = set(re.findall(r"[a-z]{4,}", str(loi[_i]).lower())) - _DUNG_CHUNG
            _noi = " ".join(x.get("chu", "") for x in ra if int(x.get("i", -1)) == _i).lower()
            _co = set(re.findall(r"[a-z]{4,}", _noi))
            if len(_goc & _co) < 2:
                _mat.append(_i)
        if _mat:
            print(f"   ↻ nén mất cú lật ở câu dẫn {_mat} — viết lại")
            continue
        thieu = _du_so(loi, ra, man)
        if not thieu:
            return ra
        print(f"   ↻ lời thoại thiếu số {thieu} — viết lại")
    print("   ⚠ không đạt cổng số sau 2 vòng — dùng bản cuối kèm cảnh báo")
    return ra if len(ra) >= 4 else []


# ══ DỰNG MỘT TẬP ═════════════════════════════════════════════════════════════════════════════
MOT_GIONG = False        # bật: MỘT chuyên gia nói liên tục, hình đổi theo lời
DAO_CU_TAP = ""          # hình mẫu của cả tập (`chu_de.hinh_mau`) — lấp chỗ câu không gợi vật
ANH_THAT: list = []      # ảnh PD/CC0 của chính chủ thể — xem `_chen_anh_that`
# ── HỒ ẢNH ĐÃ QUA BA CỔNG NỀN  (anh soi bộ 210, 9/9/2026) ────────────────────────────
# Ba cổng (mang tên chủ thể · không quá tối · không phải logo) chạy BÊN TRONG
# `_chen_anh_that`, nên chúng chỉ lọc danh sách nền CHÍNH. Danh sách ảnh PHỤ dùng để cắt
# hình mỗi 2 giây (`nenCat`) lại dựng thẳng từ `ANH_THAT` — tức đi vòng qua cả ba.
# Đo trên bộ 210: nhịp 9 lấy đúng tấm logo vừa bị loại, phóng full-bleed ra một mảng
# đen với chữ «CA WES» bị cắt. §6 nguyên xi: vá một nhánh, để nguyên nhánh song song.
# Nay `_chen_anh_that` CÔNG BỐ hồ đã lọc, và mọi nơi cần ảnh nền đọc từ đây.
ANH_SACH: list = []      # ANH_THAT sau ba cổng — nguồn DUY NHẤT cho mọi lớp nền
# ── NÉT DỰNG RIÊNG TỪNG KÊNH  (anh: "mỗi channel có 1 chút nét riêng", 7/9/2026) ────────────
# §17.3 đã trả giá cho bài này ở bộ giải thích: **đa dạng thì CHỌN được, bản sắc thì phải KHAI**.
# Rút từ hồ chung thì hai kênh vẫn có thể rút trúng nhau, và đo được cặp tệ nhất trùng 79%.
#
# Ba trục, và cả ba đặt vào thứ ĐÃ hiện trong MỌI khung — không thêm món đồ mới, vì thêm đồ là
# thêm thứ để chồng chéo (§17.4):
#     viTri  người dẫn đứng đâu ở dải đáy      trai · giua · phai
#     ken    Ken Burns của kênh                vao (phóng vào) · ra (lùi ra) · ngang (trôi ngang)
#     nen    cách chỉnh nền                    am (ấm) · lanh (lạnh) · moc (mộc, chất tư liệu)
#
# Gán theo bước NGUYÊN TỐ CÙNG NHAU với 27 để cả ba trục cùng xoay — gán tuần tự thì chín kênh
# đầu bảng dùng chung một cách chỉnh nền, tức một trục đi thành vệt dài (§13.13 · §14.9).
# 18/18 tổ hợp khác nhau; cổng `t_gu_dung_duy_nhat` canh tính duy nhất khi thêm kênh.
GU_DUNG = {
    "howlong": ("trai", "vao", "am"),      "howbig": ("phai", "ra", "moc"),
    "realcost": ("giua", "vao", "moc"),    "howmuch": ("trai", "ngang", "lanh"),
    "whatif": ("phai", "vao", "lanh"),     "survive": ("giua", "ngang", "am"),
    "dayinlife": ("trai", "ra", "am"),     "wheregoes": ("phai", "ngang", "moc"),
    # ── NGƯỜI DẪN VỀ GÓC TRÁI  (anh, 9/9/2026) ────────────────────────────────────────────
    # Anh: *"cho vào góc trái videos… a thấy góc đó ko có hình ảnh chart nhiều ko bị che khuất"*.
    # Anh quan sát đúng: thẻ số và lớp vector đều neo về nửa PHẢI của khung (xem `lech` trong
    # `SoPanel`), nên góc trái là chỗ trống thật.
    # `guViTri = "trai"` đẩy người dẫn lệch −0,26 bề ngang, VÀ bong bóng tự đảo sang phải
    # (`benVat` ở `KichComic` dòng 478) — hai thứ đi cùng nhau, không phải hai chỗ chỉnh tay.
    "therules": ("trai", "ra", "moc"),     "speedof": ("trai", "vao", "moc"),
    "odds": ("phai", "ra", "lanh"),        "hiddenfee": ("giua", "vao", "lanh"),
    "yearsof": ("trai", "ngang", "am"),    "howloud": ("phai", "vao", "am"),
    "whatweighs": ("giua", "ngang", "moc"), "rightnow": ("trai", "ra", "moc"),
    "howhot": ("phai", "ngang", "lanh"),   "smallest": ("giua", "ra", "lanh"),
}

DA_GHIM = False          # `bo_1_3` đã chọn chủ thể cho cả bộ — `mot_tap` không chọn lại
NEN_SAN: list = []       # nền do BẢN DÀI để lại, short dùng lại — xem `bo_1_3`
LOI_SAN: list = []       # LỜI của bản dài, cùng thứ tự với `NEN_SAN` — xem `_nen_theo_loi`

# ── TỰ CHỌN LẠI CHỦ THỂ NGHÈO ẢNH  (anh: "ảnh thật đa dạng, ko lặp 1 ảnh", 10/9/2026) ─────
# survive «2024 UK riots», realcost «Accounting scandal», dayinlife «Benoxaprofen» bốc chủ thể
# trừu tượng → sau ba cổng lọc (tên khớp · quá tối · logo) còn ≤1 ảnh DÙNG ĐƯỢC → nền lặp một
# tấm hoặc rơi về nền vẽ. Gốc: cổng chọn đếm ảnh THÔ (`so_anh_co`), không đếm ảnh DÙNG ĐƯỢC.
# Sửa TỰ ĐỘNG: đo số ảnh thật KHÁC NHAU NGAY TRƯỚC render (chưa tốn quota dựng); ít quá thì
# `mot_tap` báo `_NgheoAnh`, `bo_1_3` tự chọn chủ thể khác — không cần người can thiệp.
_NGUONG_ANH = 4          # tối thiểu ảnh thật KHÁC NHAU cho một bản dài
_CHON_LAI = [False]      # bo_1_3 bật khi đang dựng bản dài (được phép chọn lại chủ thể)


class _NgheoAnh(Exception):
    def __init__(self, n: int, chu_the: str = ""):
        self.n = n
        self.chu_the = chu_the
        super().__init__(f"chỉ {n} ảnh thật khác nhau (<{_NGUONG_ANH})")


def _nen_theo_loi(cau_short: list) -> list:
    """Gắn nền của bản dài vào short THEO CÂU, không theo vị trí.

    ── ANH SOI ĐÚNG KHUNG NÀY  (8/9/2026) ──────────────────────────────────────────────
    Anh: *"tốn credit mà render ra mấy tấm ảnh ko liên quan này thì làm gì cho tốn"*, kèm
    khung short nói «487 billion was transferred by 1MDB into two separate accounts» trên
    một hành lang kính trống.

    Và cảnh ĐÚNG đã được vẽ ra rồi: nhịp ấy khớp khái niệm «a vault door standing open with
    empty numbered deposit boxes inside», bản dài dựng nó ở nhịp 10. Tiền đã tiêu, ảnh đúng
    đã nằm trong kho — chỉ là short gắn nhầm câu:

        anh_nens = [NEN_SAN[i % len(NEN_SAN)] ...]

    Một phép chia lấy dư theo VỊ TRÍ. Short lấy nhịp từ bản dài rồi ĐẢO thứ tự (hook lên
    đầu) và VIẾT LẠI câu, nên vị trí trong short không còn là vị trí trong bản dài. Kết quả:
    câu về 487 tỉ nhận cảnh của câu «You own it, sort of, in your own mind».

    Nên ghép theo NGHĨA của câu, không theo chỗ ngồi: mỗi câu short tìm câu bản dài chồng
    nhiều từ nhất. Câu short được viết lại vẫn giữ phần lớn danh từ, nên phép chồng từ đủ
    chắc; không câu nào đủ giống (hook/chốt do short tự thêm) thì mới rơi về vị trí."""
    import re as _re
    if not NEN_SAN:
        return []
    _bo = {"the", "a", "an", "of", "to", "in", "on", "and", "or", "is", "was", "were", "it",
           "its", "for", "with", "that", "this", "by", "as", "at", "from", "be", "been",
           "you", "your", "they", "their", "we", "our", "he", "she", "his", "her", "not"}

    def _tu(t):
        return {w for w in _re.findall(r"[a-z0-9]+", str(t or "").lower())
                if len(w) > 2 and w not in _bo}

    _dai = [_tu(x) for x in (LOI_SAN or [])]
    ra, da = [], set()
    for i, c in enumerate(cau_short):
        a = _tu(c)
        tot, diem = -1, 0.0
        for j, b in enumerate(_dai):
            if not a or not b:
                continue
            # Jaccard: đo NỘI DUNG chứ không đo khuôn câu (§13.5)
            d = len(a & b) / len(a | b)
            if d > diem and (j not in da or d > 0.75):
                tot, diem = j, d
        # HAI NHỊP LIỀN NHAU KHÔNG ĐƯỢC CÙNG MỘT NỀN. Short 1640 có hai câu đầu đều mở bằng
        # «You own it, sort of…» nên cả hai khớp cùng một nhịp bản dài và nhận cùng một tấm —
        # màn hình đứng yên suốt hai nhịp, đúng chỗ người xem lướt đi (§15.6).
        _chon = NEN_SAN[tot % len(NEN_SAN)] if tot >= 0 and diem >= 0.34 else None
        if _chon is not None and ra and _chon == ra[-1]:
            _khac = [j for j in range(len(_dai)) if j != tot and j not in da]
            if _khac:
                tot = max(_khac, key=lambda j: len(a & _dai[j]) / max(1, len(a | _dai[j])))
                _chon = NEN_SAN[tot % len(NEN_SAN)]
        if _chon is not None:
            da.add(tot)
            ra.append(_chon)
        else:
            ra.append(NEN_SAN[i % len(NEN_SAN)])
    return ra
TEN_ANH: dict = {}       # đường ảnh -> tiêu đề nguồn, để ghép ảnh với câu theo NGHĨA
# ── HẠNG MỤC WIKIMEDIA: LẤY VỀ RỒI VỨT ĐI  (bộ 213, 9/9/2026) ───────────────────────
# §19.13 chốt rằng câu hỏi "ảnh này có phải CỦA chủ thể không" trả lời được bằng
# `Categories`, và `anh_tu_do` xin sẵn `Categories|ObjectName` từ hôm ấy. Nhưng chỗ duy
# nhất giữ lại là `TEN_ANH`, và nó chỉ giữ TIÊU ĐỀ — hai trường kia đi tới nơi rồi bị
# vứt trước khi cổng nhìn thấy (§15.12: lấy về mà không ai đọc).
# Đo «Savannah River Plant»: 24 ảnh, 19 bị loại, và đọc tay thì gần hết là ảnh ĐÚNG —
# kho gọi bằng tên viết tắt (SRS) hoặc tên khu ("H Canyon", "D Area Powerhouse"), còn
# hạng mục thì ghi thẳng «Savannah River Site».
META_ANH: dict = {}      # đường ảnh -> hạng mục + ObjectName, bằng chứng THỨ HAI của cổng

# ── SỔ NÀY PHẢI SỐNG LÂU HƠN TIẾN TRÌNH  (8/9/2026) ─────────────────────────────────────
# `TEN_ANH` giữ đúng thứ cần để trả lời câu anh hỏi — *"thẻ ảnh có khớp cái đang nói không,
# hay râu ông nọ cắm cằm bà kia"* — nhưng nó chỉ sống trong bộ nhớ một lượt dựng. Tên tệp là
# BĂM nội dung, nên sau khi tiến trình tắt thì `anh_pd/1b1fe821….jpg` không còn tra được về
# đâu cả: em đi đo độ khớp thẻ/mệnh đề và phải kết luận "CHƯA ĐO ĐƯỢC", trong khi dữ liệu ấy
# đã nằm trong tay ở đúng lúc tải về (§15.12: ghi ra mà không ai đọc — ở đây còn tệ hơn, ghi
# vào bộ nhớ rồi vứt). Sổ này cũng là XUẤT XỨ: biết mỗi tấm lấy từ trang Commons nào.
SO_ANH = os.path.join(GOC, "so_anh_nguon.json")


def _ghi_so_anh() -> None:
    """Gộp `TEN_ANH` vào sổ trên đĩa. Gộp chứ không ghi đè — nhiều lượt dựng chạy song song."""
    try:
        cu = {}
        if os.path.exists(SO_ANH):
            cu = json.load(io.open(SO_ANH, encoding="utf-8")) or {}
        cu.update({k: v for k, v in TEN_ANH.items() if v})
        io.open(SO_ANH, "w", encoding="utf-8").write(
            json.dumps(cu, ensure_ascii=False, indent=1))
    except Exception as e:
        print(f"   ⓘ không ghi được sổ ảnh ({type(e).__name__}) — không chặn lượt dựng")
LOGO_TAP = ""            # ảnh thật của chủ thể (logo/trụ sở) — thẻ nhỏ ở khúc mở
BEN_DUNG = "trai"        # người dẫn đứng bên nào — nền chừa dải trống ĐÚNG bên ấy
CHU_THE_TAP = ""         # chủ thể của tập — bộ vẽ nền theo tập dùng, xem `nen_theo_tap`
# Trần ảnh CF cho MỘT tập. Đặt ở đây chứ không ở biến toàn cục dùng chung: mỗi tập là một
# tiến trình riêng nên phạm vi "một tiến trình" ĐÚNG BẰNG phạm vi "một tập" — khác hẳn ca
# §17.7, nơi bộ đếm tự nhận là "mỗi lượt chạy" mà thật ra đếm mỗi tập.
# Trần ảnh CF cho MỘT tập. 20 chứ không 14: với bộ 1:3 thì bộ ảnh của bản dài nuôi CẢ BỐN
# clip, nên mỗi ảnh được chia cho bốn video — ngân sách đo được là 11,8 ảnh/bộ, tức 20 ảnh
# cho một bộ vẫn nằm trong tầm khi chủ thể có sẵn ảnh tư liệu.
TRAN_NEN_TAP = int(os.environ.get("TRAN_NEN_TAP") or 20)


def k_ma_sinh(ma: str) -> str:
    """Khoá của kênh trong `giai_thich.BO_SINH`. Bảng ấy khoá theo trường `sinh` của kênh,
    KHÔNG theo `ma` — hai thứ trùng nhau ở 18 kênh hiện tại nên nhầm cũng chạy, và sẽ hỏng
    im lặng đúng lúc thêm một kênh đặt tên khác (§16.6: trường có, kiểu đúng, sai hệ quy chiếu)."""
    import giai_thich as G
    return next((k["sinh"] for k in G.KENH if k["ma"] == ma), ma)


# Từ KHÔNG gợi được hình: đứng đầu prompt thì mô hình vẽ một cảnh chung chung.
_BO_NEN = {"the","and","for","with","from","that","this","was","were","its","been","have",
           "after","before","when","which","their","there","then","than","also","into",
           "would","could","company","service","began","ended","started","stopped","made",
           "took","came","went","said","later","first","most","more","some","many","other",
           "about","over","under","between","during","because","while","only","still"}

# Tám khuôn hình TĨNH, xoay theo nhịp. Không có cái nào tả chuyển động máy — hàng rào ấy đúng
# và giữ nguyên (§14.9). Cái đổi là CHIỀU CAO · KHOẢNG CÁCH · TIỀN CẢNH.
# Từ neo trong `NEN_CUA_HINH_MAU` là chuỗi TÌM KIẾM trong `nen_tag`, không phải câu tả cảnh —
# ghép thẳng ra `"a trading"`, `"a office"`. Bảng này đổi chúng thành cụm đọc được. Chỉ khai
# những từ CÓ THẬT trong bảng ấy (65 từ), không đoán thêm: một từ thiếu thì rơi về chính nó,
# thấy ngay trên prompt chứ không hỏng im lặng.
_CANH_NEO = {
    "aircraft": "an aircraft maintenance hangar", "airport": "an airport terminal hall",
    "aisle": "a supermarket aisle", "apron": "an airport apron with parked aircraft",
    "archive": "a records archive room", "assembly": "a factory assembly line",
    "bank": "a bank branch interior", "bookshop": "a bookshop interior",
    "broadcast": "a broadcast control room", "camera": "a camera shop interior",
    "checkout": "a store checkout area", "clinic": "a clinic waiting room",
    "control room": "a control room with consoles", "corridor": "a long office corridor",
    "counter": "a service counter", "darkroom": "a photo darkroom",
    "dock": "a loading dock", "editing": "an editing suite",
    "electronic": "an electronics workbench", "factory": "a factory floor",
    "garage": "a repair garage", "hangar": "an aircraft hangar",
    "harbor": "a working harbour", "harbour": "a working harbour",
    "highway": "a highway roadside", "home office": "a home office",
    "hospital": "a hospital corridor", "industrial": "an industrial plant floor",
    "laborator": "a laboratory bench room", "launch": "a rocket launch control room",
    "librar": "a library reading room", "lobby": "an office building lobby",
    "market": "a stock exchange trading floor", "medical": "a medical examination room",
    "newsroom": "a newspaper newsroom", "observator": "an observatory dome",
    "office": "an open-plan office", "phone": "a phone assembly workbench",
    "photo": "a photography studio", "plant": "a power plant hall",
    "port": "a container port", "power": "a power station turbine hall",
    "print": "a printing press room", "refiner": "an oil refinery walkway",
    "rental": "a video rental store", "repair": "a repair workshop",
    "retail": "a retail shop floor", "road": "an empty road",
    "rocket": "a rocket assembly building", "runway": "an airport runway edge",
    "server": "a server room", "shipyard": "a shipyard slipway",
    "shop": "a shop interior", "showroom": "a car showroom",
    "space": "a spacecraft assembly cleanroom", "store": "a store interior",
    "studio": "a photography studio", "terminal": "an airport terminal",
    "tower": "an office tower lobby", "trading": "a stock exchange trading floor",
    "turbine": "a turbine hall", "vault": "a bank vault",
    "warehouse": "a warehouse aisle", "workbench": "a workbench room",
    "workshop": "a workshop interior",
}

_KHUON_NEN = (
    "wide establishing view from across the space",
    "close view of the object filling the lower half",
    "view from a doorway looking in",
    "low angle looking slightly up",
    "view down a long corridor",
    "elevated view looking down across the floor",
    "corner view with something large at the left edge",
    "flat straight-on view of a single wall",
)


# ── LUẬT BỐ CỤC RIÊNG CHO BỘ NÀY  (anh soi prompt, 8/9/2026) ───────────────────────────
# Anh: *"cf chưa tận dụng để ép prompt tạo ra được ảnh như ý muốn, xem lại prompt"*. Đo thành
# phần prompt thật đang gửi CF:
#     tổng 643 ký tự — phần nói VẼ GÌ chỉ **19%** (cảnh 9% · khuôn hình 6% · đồ vật 4%)
#     luật bố cục 45% · phong cách 33%
# Và đọc nó NHƯ MÔ HÌNH ĐỌC (§16.2), hai câu đang đánh nhau với chính mục tiêu:
#     "anything in the scene pushed far to the left and right edges,
#      the centre of the frame is empty walkable floor"
# Tức mình RA LỆNH đẩy hết đồ ra mép và để giữa trống. Cái búa gỗ + chồng hồ sơ — thứ khiến
# người xem nhận ra — bị đẩy ra rìa, giữa khung còn sàn trống. Đó chính là "nền chung chung".
#
# Hai câu ấy đúng ở ngữ cảnh sinh ra chúng: engine cũ dán nhân vật VECTOR vào GIỮA khung, nên
# giữa phải trống (§7). Nhưng anh đã cho người dẫn đứng 1/3 và LỆCH HẲN MỘT BÊN (`GU_DUNG.viTri`,
# `_lechGu = 0,26`), nên chỗ cần chừa là MỘT DẢI BÊN — và đồ đạc không việc gì phải ra hai mép.
# §12.5: dùng lại một câu luật ở ngữ cảnh mới thì phải hỏi lại nó còn đúng không.
#
# Giữ nguyên hai mệnh lệnh THẬT SỰ chống lỗi: sàn chiếm phần ba dưới (chống người lơ lửng) và
# máy ngang tầm mắt. Bỏ hai mệnh lệnh còn lại, thay bằng một dải trống ĐÚNG BÊN người đứng.
def san_nen_ben(ben: str) -> str:
    """Chừa dải trống ĐÚNG chỗ người dẫn đứng — ba trường hợp, không phải hai.

    ── LỖI EM VỪA TỰ TẠO RA, VÀ NÓ TRÚNG MỘT PHẦN BA SỐ KÊNH  (8/9/2026) ───────────────
    Bản đầu của hàm này viết `"left" if ben.startswith("tr") else "right"` — tức mọi giá trị
    không phải `trai` đều thành `phai`. Nhưng `GU_DUNG` có BA giá trị, chia đều:
        trai 6 kênh · phai 6 kênh · **giua 6 kênh**
    Sáu kênh `giua` (có `therules`) vì thế được dặn chừa dải BÊN PHẢI trong khi người dẫn
    đứng GIỮA, và đồ đạc bị dồn vào hai phần ba TRÁI — người đè đúng lên chỗ có đồ. Soi lưới
    bộ 146 thấy khung 3 hỏng bố cục chính là ca ấy.

    Đúng họ §13.9 ở dạng nhị phân: viết `A if X else B` cho một trường có BA giá trị là im
    lặng gộp hai giá trị làm một. Cách nhận ra rẻ nhất: đếm số giá trị thật của trường trước
    khi viết nhánh.
    """
    _b = str(ben).lower()
    _san = ("wide shot, camera at standing eye level, the ground plane fills the entire "
            "bottom third of the frame as one continuous unbroken surface running from the "
            "left edge to the right edge, ")
    if _b.startswith("tr"):
        return _san + ("the left third of the frame is open walkable floor, "
                       "the objects of the scene stand together in the right two thirds")
    if _b.startswith("ph"):
        return _san + ("the right third of the frame is open walkable floor, "
                       "the objects of the scene stand together in the left two thirds")
    # GIỮA: người đứng chính giữa nên dải trống phải ở giữa, và đồ tụ về HAI bên — đây đúng
    # là luật cũ, và với sáu kênh này nó vẫn là luật đúng.
    return _san + ("the centre of the frame is empty walkable floor, "
                   "the objects of the scene stand together at the left and right edges")


def _nen_theo_tap(anh_nens: list, cau: list, chu_the: str, bo_qua: set = None) -> list:
    """Vẽ nền RIÊNG cho tập này từ chính CHỦ THỂ + câu đang nói, thay cho nền kho chung.

    ── VÌ SAO  (anh, 7/9/2026) ───────────────────────────────────────────────────────────
    Anh: *"bỏ nền sẵn và nên lấy nền liên quan videos khi làm … hơn là mấy nền ko liên quan"*.
    Kho `nen_kho.json` được soạn từ mô tả PHÒNG chung chung (*"a metal forge, hanging chains
    and glowing furnaces"*) nên nó không bao giờ khớp chủ thể, dù bộ vẽ mạnh cỡ nào. Nút thắt
    chưa bao giờ là bộ vẽ — mà là mình bảo nó vẽ GÌ.

    ── CÓ ĐỦ HẠN MỨC KHÔNG: ĐO, KHÔNG ĐOÁN ──────────────────────────────────────────────
        121 tài khoản CF × 37 ảnh/ngày (flux-2-klein-9b) = 4.477 ảnh/ngày
        một tập 12 nhịp                                  =    12 ảnh
        -> ~373 tập/ngày cho cả 18 kênh (~21 tập/kênh/ngày)
    `A.ve` đệm theo VÂN TAY PROMPT nên dựng lại một tập đã có tốn 0 lượt — điều kiện để soi
    khung nhiều vòng mà không đốt hồ.

    ── BỐN TẦNG VẪN NGUYÊN (§7) ─────────────────────────────────────────────────────────
    ảnh thật PD/CC0  ->  nền vẽ theo chủ thể (hàm này)  ->  kho nền chung  ->  nền vector.
    CF cạn hay hỏng thì nhịp ấy GIỮ NGUYÊN ảnh kho đã tính — không nhịp nào để trống.

    Chủ thể đứng ĐẦU prompt: docstring của `_prompt` bên `giai_thich` từng viết đúng điều này
    rồi mã làm ngược, và hậu quả đo được là kênh SURVIVE đặt hàng "a lone person in a frozen
    tundra" mà ra một căn phòng hiện đại (§15.25).
    """
    if not chu_the or not anh_nens:
        return anh_nens
    if os.environ.get("KHONG_NEN_TAP"):
        return anh_nens
    # ── BỎ `import SAN_NEN_VAT`: NÓ CHỈ CÒN LÀ SUẤT MIỄN CHO CỔNG  (8/9/2026) ────────
    # Đường vẽ này nay dùng luật riêng `san_nen_ben()`, không dùng hằng chung nữa. Giữ dòng
    # import lại "cho cổng soi theo" chính là giữ một SUẤT MIỄN: `kiem_nen` thấy tệp có
    # import thì tha, nên nó báo xanh kể cả khi luật trong prompt bị phá.
    # Thử ngược chứng minh: xoá mệnh lệnh chừa chỗ khỏi `san_nen_ben` -> cổng VẪN XANH.
    # Một cổng không thể đỏ thì không phải cổng (§15.19 · §13.11).
    _san = san_nen_ben(BEN_DUNG)
    viec = []
    bo_qua = bo_qua or set()
    for i, c in enumerate(cau[:len(anh_nens)]):
        if len(viec) >= TRAN_NEN_TAP:
            break
        if anh_nens[i] in bo_qua:
            continue                  # nhịp này đã có ẢNH THẬT — vẽ nữa là vẽ vào thùng rác
        # `cau` là danh sách TUPLE `(lời, ai, cảm xúc)` — không phải dict. Em đã đoán hình
        # dạng và render chết ở đúng dòng này. Đọc phần tử đầu, và vẫn nhận dict phòng khi
        # khâu trên đổi kiểu (§13.8: đọc vật thật trước khi viết lối gọi mới).
        noi = c[0] if isinstance(c, (tuple, list)) else (c.get("nar") or c.get("chu") or "")
        noi = " ".join(str(noi).split())[:150]
        if not noi:
            continue
        # ── CÂU DẪN DẮT, CHỦ THỂ CHỈ ĐỨNG SAU  (soi khung 8/9/2026) ────────────────────
        # Bản đầu ghép `"{chủ thể}. {câu}"`, và soi 20 nền vẽ cho `Air Berlin` thì **cả 20
        # gần như một cảnh**: sảnh sân bay trống, cùng một góc. Đúng thôi — chủ thể đứng đầu
        # nên mô hình vẽ "hãng hàng không", còn câu thì nói về lịch sử công ty, không tả cảnh.
        #
        # Đảo lại: DANH TỪ CỤ THỂ của chính câu ấy đứng đầu (mô hình khuếch tán đọc phần đầu
        # nặng ký hơn — §15.25), chủ thể lùi xuống làm bối cảnh. Và xoay KHUÔN HÌNH theo nhịp
        # để hai nhịp liền nhau không cùng một góc máy: đa dạng phải nằm ở thứ người xem NHÌN
        # THẤY, không ở thứ đếm được (§14.9).
        # ── NƠI CHỐN NEO BẰNG HÌNH MẪU, DANH TỪ CHỈ THÊM CHI TIẾT  (soi khung 8/9/2026) ─
        # Bản trước cho danh từ TRẦN của câu dẫn đầu, và mất ngữ cảnh: câu *"India's market
        # crashed"* ra một CHỢ ĐƯỜNG PHỐ, còn một tập về bê bối chứng khoán có cả kệ gấu
        # bông. Đa dạng thì đạt, đúng thì không — mà sai chủ đề còn tệ hơn nhàm.
        #
        # `hinh_mau` đã suy MỘT LẦN từ chủ thể (§19.10) và nói thẳng nơi chốn: `dong_xu` ->
        # ngân hàng · sàn giao dịch · két. Cho nó NEO cảnh, rồi danh từ của câu thêm chi
        # tiết vào cái neo ấy. Nơi chốn đứng đầu, chi tiết đứng sau — cùng thứ tự §15.25.
        # ── TÊN RIÊNG TRONG PROMPT = CHỮ NGUỆCH NGOẠC TRONG ẢNH  (soi khung 8/9/2026) ──
        # Lưới bộ 131: nền vẽ ra `John Paul / Pauift / Ridle / born` chạy ngang khung, và
        # `Arlit Kept INTERNATIONA` trên một tấm biển. FLUX vẽ đúng thứ được đưa: câu dẫn
        # có `John Paul Riddle`, prompt còn thêm `Setting: Airlift International`.
        # §13.20 đã đo: chữ trong khung là chỗ mô hình hỏng nặng nhất, và người xem đọc ra
        # "nghiệp dư" trong nửa giây. §12.7: chuỗi dài luôn ra sai, cấm bằng câu phủ định
        # thì lại thành ĐẶT HÀNG chữ (§17.6) — nên cách duy nhất là ĐỪNG ĐƯA TÊN VÀO.
        #
        # Nhận ra quy luật thay vì liệt kê ngoại lệ (§13.9): tên riêng VIẾT HOA giữa câu.
        # Chỉ lấy từ viết thường — chúng là danh từ chung, thứ duy nhất vẽ được thành hình.
        _cam = {w.lower() for w in re.findall(r"[A-Za-z]{3,}", chu_the or "")}
        # Và bỏ ĐỘNG TỪ: `born · died · pioneered · bought` không vẽ được thành hình, chúng
        # chỉ pha loãng prompt (§17.5 — chỉ lấy thứ vẽ được). Đuôi `-ed`/`-ing` là một QUY
        # LUẬT, không phải một danh sách ngoại lệ (§13.9).
        _dt = [w for w in re.findall(r"(?<![.!?]\s)\b[a-z]{4,}\b", noi)
               if w not in _BO_NEN and w not in _cam
               and not w.endswith(("ed", "ing"))][:4]
        _neo = ""
        try:
            import chu_de as _CD1
            _nh = _CD1.nhom_nen_cua(DAO_CU_TAP)
            if _nh:
                _k = _nh[i % len(_nh)]
                _neo = _CANH_NEO.get(_k, f"a {_k}") + ", "
        except Exception:
            pass
        _canh = _KHUON_NEN[i % len(_KHUON_NEN)]
        _chi = (", ".join(_dt) + ". ") if _dt else ""
        # `Setting: {chu_the}` đã bị BỎ: nó là nguồn tên riêng thứ hai, và nó THỪA — neo
        # cảnh đã suy từ hình mẫu của chính chủ thể (§19.10), tức đã mang đúng thế giới ấy
        # rồi. Giữ cái tên chỉ để mô hình viết nó ra thành chữ hỏng.
        # ── VÀ BỎ NỐT DANH SÁCH DANH TỪ  (soi khung bộ 132, 8/9/2026) ──────────────────
        # Bỏ tên riêng xong, nền VẪN có chữ: khung 3 hiện `known, / berlin / became,`. Cả 13
        # nền là VẼ MỚI sau bản vá (đo mtime), nên không phải đệm cũ. Nguồn là chính vế
        # `In it: known, became, major` — một DANH SÁCH TỪ đọc ra như một tấm biển cần chép,
        # và mô hình chép. Lọc theo hoa/thường chỉ chặn được tên riêng, không chặn được việc
        # đưa chữ vào.
        #
        # Có thể siết `_dt` về danh từ VẼ ĐƯỢC không? Từ vựng nơi chốn của repo chỉ 112 từ
        # và toàn tên NƠI CHỐN (`hangar`, `apron`); `cargo · carrier · aviation · ticket`
        # đều không có. Siết theo nó thì gần như mọi nhịp mất sạch chi tiết — tức bằng đúng
        # việc bỏ vế này, chỉ vòng vo hơn. §13.22: đo xong rồi QUYẾT ĐỊNH KHÔNG LÀM cũng là
        # một kết quả; ghi ra đây rằng chỗ này CHƯA ĐO ĐƯỢC cách giữ chi tiết mà không đưa
        # chữ vào khung.
        #
        # Đa dạng theo nhịp KHÔNG mất: neo cảnh xoay theo `i % len(_nh)` (nơi chốn của chính
        # hình mẫu) và khuôn hình xoay theo `i % len(_KHUON_NEN)` — hai trục người xem NHÌN
        # THẤY (§14.9), không phải một danh sách từ mà mô hình đem viết lên tường.
        # KHÁI NIỆM CỦA CHÍNH CÂU dẫn cảnh; hình mẫu chỉ còn giữ thế giới cho nhất quán.
        _tho = str(noi).lower()
        _su = next((c for r, c in _KHAI_NIEM if re.search(r, _tho)), "")
        _vat = _VAT_HINH_MAU.get(DAO_CU_TAP or "", ())
        _do = f"Further back: {_vat[i % len(_vat)]}. " if _vat else ""
        if _su:
            viec.append((i, f"{_su}. {_canh}. {_do}{_san}. {GU_NEN}"))
        else:
            _tt = _NEN_TRUNG_TINH.get(DAO_CU_TAP or "", ())
            _nen0 = f"{_tt[i % len(_tt)]}, " if _tt else _neo
            viec.append((i, f"{_nen0}{_canh}. {_do}{_san}. {GU_NEN}"))
    if not viec:
        return anh_nens
    try:
        # ── CHIỀU ẢNH PHẢI THEO KHUNG SẼ DÙNG NÓ  (anh soi bản dài, 8/9/2026) ──────────
        # Anh: *"clip 16:9 ko ổn, bị cắt ảnh khá nhiều, ko còn nhận ra gì cả"*. Đo đúng phép
        # `objectFit: cover` mà engine dùng:
        #     nền DỌC  768×1344 -> khung 1920×1080: phóng 2,50x · chỉ thấy **32% chiều cao**
        #     nền NGANG 1344×768 -> khung 1920×1080: phóng 1,43x · thấy **98%**
        # 32% chiều cao là một DẢI NGANG cắt ngang giữa cảnh — thường chỉ còn mảng tường hoặc
        # mảng sàn, nên "không nhận ra gì" là mô tả đúng, không phải cảm giác.
        #
        # §18.13 đổi kho nền sang DỌC là ĐÚNG Ở THỜI ĐIỂM ẤY: đo được `comic_nen` chỉ có MỘT
        # nơi đọc là short 9:16, và dọc cho gấp 3,1 lần điểm ảnh thật. Nhưng `bo_1_3` nay dựng
        # CẢ long 16:9 LẪN short 9:16 từ CÙNG một bộ ảnh (§17.11) — tức đã có HAI nơi đọc với
        # hai khung ngược nhau, đúng tình huống anh hỏi trước khi em đổi:
        # *"ngang dùng cho long hay sao, long short phải đồng nhất?"*
        #
        # Vì sao chọn NGANG làm chiều dùng chung: mất 68% BỀ NGANG (ngang -> short) vẫn giữ
        # trọn chiều cao, mà prompt vốn dặn chủ thể ở GIỮA nên phần mất là hai mép trống —
        # §17.11 đã đo và ghi đúng điều này. Mất 68% CHIỀU CAO (dọc -> long) thì cắt ngang
        # giữa cảnh, không cứu được bằng bố cục nào.
        _ngang = bool(os.environ.get("NEN_NGANG") or CHUONG_KHONG_LAP)
        ra = A.ve_nhieu(viec, "nentap", 0, doc=not _ngang, luong=6)
    except Exception as e:
        print(f"   ⚠ vẽ nền theo tập hỏng ({str(e)[:44]}) — giữ nền kho")
        return anh_nens
    out = list(anh_nens)
    n = 0
    for (i, _), rel in zip(viec, ra or []):
        if rel:
            out[i] = rel
            n += 1
    print(f"   🎨 nền vẽ theo chủ thể «{chu_the}»: {n}/{len(viec)} nhịp"
          f" (còn lại dùng kho chung)")
    return out


def _lop_ve(cau: list) -> list:
    """Nhịp không có ảnh thật -> lớp VẼ BẰNG CODE khớp chính câu đang nói. None nếu không hợp.

    ── VÌ SAO VẼ THAY VÌ ĐỂ TRỐNG  (anh chốt, 8/9/2026) ───────────────────────────────────
    Anh: *"nền 100% là ảnh thật liên quan … hay nền trống"*, rồi *"dùng ảnh thực tế hay ảnh
    generate code nha"*. Tức: ảnh tư liệu khi có, còn lại VẼ BẰNG CODE — không dùng ảnh CF.

    Lý do bỏ ảnh CF đã đo: nó KHÔNG BIẾT THỜI ĐẠI. Chuyện năm 1866 ra văn phòng kính hiện đại,
    vì không prompt nào mang niên đại. Hình vẽ bằng code thì KHÔNG CÓ thời đại — một trục thời
    gian hay một thẻ số không thể sai thời, nên nó không bao giờ mắc lỗi ấy.

    Và mọi con số ở đây rút TỪ CHÍNH LỜI THOẠI, không tự nghĩ ra cái nào — luật cứng §19.3
    (*máy gác sự thật, không ai được cấp một con số*) giữ nguyên.

    Độ phủ đo trên 149 nhịp của 10 bản dài: 37% nhắc tới một NĂM (trục thời gian) · 11% có SỐ
    kèm đơn vị (thẻ số) · 52% còn lại để trống, vì bịa ra một hình cho câu không có gì đo được
    thì lại đúng cái lỗi vừa bỏ.

    Hai khuôn `Truc` và `SoLieu` đã có sẵn trong `gt/Khuon.tsx`, tự chứa và chỉ nhận W/H/p —
    không phải viết mới (§13.1).
    """
    import re as _re
    txt = " ".join(str(c or "") for c in cau)
    nam_tap = sorted({int(y) for y in _re.findall(r"\b(1[89]\d\d|20[0-2]\d)\b", txt)})
    # trục chỉ có nghĩa khi có ít nhất hai mốc; quá nhiều thì lấy đầu-giữa-cuối cho đọc được
    if len(nam_tap) > 5:
        b = len(nam_tap)
        nam_tap = [nam_tap[0], nam_tap[b // 4], nam_tap[b // 2], nam_tap[3 * b // 4], nam_tap[-1]]
    ra = []
    for c in cau:
        t = str(c or "")
        y = _re.findall(r"\b(1[89]\d\d|20[0-2]\d)\b", t)
        if y and len(nam_tap) >= 2:
            try:
                vt = nam_tap.index(int(y[0]))
            except ValueError:
                vt = 0
            ra.append({"k": "truc", "moc": [{"nhan": str(n)} for n in nam_tap], "vt": vt})
            continue
        m = _re.search(r"\b([\d][\d,.]*)\s*(billion|million|thousand|percent|%)\b", t, _re.I)
        if m:
            ra.append({"k": "so", "so": m.group(1), "don": m.group(2),
                       "chu": t[:70]})
            continue
        ra.append(None)
    return ra


def _nen_can_tron(duong: list, ngang: bool, san: float = 0.60) -> list:
    """[bool] — nền nào bị phép `cover` giấu mất quá nhiều thì phải hiện TRỌN.

    ── LUẬT ĐÚNG LÀ "GIẤU MẤT BAO NHIÊU", KHÔNG PHẢI "KHUNG DỌC"  (8/9/2026) ──────────────
    Anh gửi khung một chiếc Camry bị phóng còn CÁNH CỬA: *"zoom bự quá … ko thấy được cái
    muốn thể hiện"*. Bản sửa đầu của em chỉ xử khung DỌC, và đo lại thì chiều ngược lại hỏng
    y hệt — 4/13 ảnh thật trong bản DÀI mất quá 45% một chiều:

        564×835   -> thấy 100% ngang · chỉ  31% DỌC
        1600×349  -> thấy  47% ngang · 100% dọc

    Nên điều kiện không phải hướng khung mà là TỈ LỆ BỊ GIẤU. Đo ở Python vì đây là nơi biết
    cỡ ảnh thật; engine chỉ biết sau khi ảnh tải xong, tức quá muộn để đổi cách dán.

    Chỉ áp cho ẢNH THẬT: nền vẽ sinh ra để phủ kín khung, và §17.4 đã trả giá cho mép trắng
    lọt ra. Ảnh thật thì ngược lại — nó có mặt CHỈ vì nhận ra được ngay (§19.12), nên thà
    chừa mép còn hơn cắt mất chủ thể.
    """
    try:
        from PIL import Image
    except Exception:
        return [False] * len(duong or [])
    KW, KH = (1860, 860) if ngang else (1040, 1860)
    pub = os.path.join(GOC, "..", "engine-remotion", "public")
    ra = []
    for a in (duong or []):
        b = str(a or "")
        if "anh_pd/" not in b:
            ra.append(False)
            continue
        p = os.path.join(pub, b)
        try:
            W, H = Image.open(p).size
            k = max(KW / W, KH / H)
            thay = min((KW / k) / W, (KH / k) / H)
            ra.append(thay < san)
        except Exception:
            ra.append(False)
    return ra


def _chen_anh_that(anh_nens: list, duong: list, cau: list = None) -> list:
    """Gắn ảnh THẬT vào nhịp mà nó NÓI VỀ, không rải đều theo vị trí.

    ── VÌ SAO ĐỔI  (anh hỏi thẳng, 7/9/2026) ─────────────────────────────────────────────
    Anh: *"như thế có đúng bối cảnh khớp kịch bản videos khi nói ko"*. Bản trước rải ảnh
    CÁCH ĐỀU các nhịp, nên nó khớp CHỦ THỂ mà không khớp MỆNH ĐỀ: câu nói về 2007 vẫn có thể
    đứng cạnh tấm quảng cáo 1888. Anh đúng, và đó là lỗ em tự ghi ra mà chưa vá.

    Ghép theo chữ chung giữa TIÊU ĐỀ ảnh và CÂU đang nói. Tiêu đề nguồn rất giàu thông tin —
    *"Eastman Kodak HQ 1900"*, *"Folding Pocket Kodak Camera ad 1900"* — nên phép so chỉ cần
    đếm từ nội dung chung, không cần mô hình.

    Nhịp KHÔNG có ảnh nào khớp thì để TRỐNG cho `_nen_theo_tap` vẽ nền riêng theo chính câu
    ấy. Đó vừa là chất lượng (khung nói đúng thứ đang nói) vừa là cách tiêu đúng hạn mức CF:
    ngân sách đo được là 11,8 ảnh/bộ, mà bản cũ chỉ dùng 36% vì nó bỏ qua mọi nhịp đã có ảnh
    kể cả khi ảnh ấy không liên quan.

    Tên chủ thể bị BỎ khỏi phép so: nó có trong mọi tiêu đề lẫn gần mọi câu, nên để lại thì
    mọi cặp đều khớp bằng nhau và phép so mất hết sức phân giải (§13.4 — cắt phần giống nhau
    ĐÚNG ra trước rồi mới đo).
    """
    # Dọn TRƯỚC mọi lối ra: hàm này được gọi lại cho từng clip của bộ (long + ba short), nên
    # một lối ra sớm mà không dọn sẽ để clip sau đọc hồ của clip trước — đúng thứ một biến
    # chung luôn hỏng theo (§15.12).
    global ANH_SACH
    ANH_SACH = []
    if not duong:
        return anh_nens
    # ── LOGO KHÔNG PHẢI ẢNH NỀN  (anh soi bộ 171, 8/9/2026) ────────────────────────────
    # Anh gửi khung có "một bức tranh trừu tượng đỏ/xanh" làm nền. Tra sổ xuất xứ thì đó là
    # `File:Fine air logo.png` — chữ logo, phóng full-bleed thành mảng màu vô nghĩa. Khung
    # khác là `File:Aviacionavion.png`, biểu tượng hàng không chung của Wikipedia.
    #
    # Logo vẫn CẦN, nhưng ở đúng chỗ của nó: thẻ nhỏ góc trên (`LOGO_TAP`), nơi cùng tấm ấy
    # đọc ra ngay là logo. Cùng một tấm, hai vai — và vai "nền" là vai nó không làm được.
    #
    # Nhận bằng XUẤT XỨ, không bằng pixel. Em đã thử thước pixel trước: `top5` (tỉ lệ 5 ô màu
    # phổ biến nhất) tách sạch hai đầu — logo 0,82–0,89 vs ảnh chụp 0,13–0,46 — nhưng soi
    # khoảng GIỮA thì một chiếc máy bay trên nền trời trơn cũng cho 0,71, tức thước nhầm
    # "nền phẳng" với "logo". Ngưỡng nào cũng cắt oan ảnh thật (§12.3: calibrate hai đầu cực
    # chỉ chứng minh tách được hai đầu; cổng sống ở khoảng giữa).
    # Tiêu đề nguồn thì nói thẳng, không phải suy: `... logo.png` là logo.
    _DAU_LOGO = re.compile(r"\b(logo|icon|symbol|emblem|wordmark|coat of arms|seal|badge|"
                           r"template|stub)\b", re.I)
    # ── ẢNH NỀN PHẢI MANG TÊN CHỦ THỂ, MỌI TẦNG  (anh soi bộ 193, 9/9/2026) ───────────
    # Bộ «Meat Hope» (công ty thịt Nhật) lấy nền là ảnh lưu trữ ALASKA: *"Preparing whale
    # meat for the Point Hope Whaling Festival"*. NARA khớp "**Meat**" và "**Hope**" như hai
    # TỪ RỜI — whale *meat* + Point *Hope*. Đọc được ngay trên khung: "CREDIT: NATIONAL PARK
    # SERVICE". Đúng thứ anh gọi *"râu ông nọ cắm cằm bà kia"*.
    #
    # §19.13 đã dạy luật này và nó CHỈ được áp cho tầng Commons; tầng bài-Wikipedia và tầng
    # NARA đi thẳng. Vá một nhánh, để nguyên nhánh song song (§6) — lần thứ tư trong phiên.
    # Nay chặn ở ĐÂY, chỗ duy nhất mọi tầng đều đi qua trước khi thành nền.
    #
    # Khớp CỤM LIỀN, không khớp từ rời: «Meat Hope» phải xuất hiện nguyên cụm. Và nhận cả TÊN
    # GỌI KHÁC từ Wikidata, vì «MetLife Building» cần nhận được ảnh «Pan Am Building» — tên cũ
    # của chính toà nhà ấy.
    _cum = []
    try:
        import logo_wd as _LW3
        _cum = [" ".join(str(t).lower().split())
                for t in (_LW3.ten_khac(CHU_THE_TAP) or [CHU_THE_TAP]) if t]
    except Exception:
        _cum = [" ".join(str(CHU_THE_TAP or "").lower().split())]
    # ── TÊN CHỦ THỂ HAY CÓ TIỀN TỐ MÔ TẢ  (đo bộ 196, 9/9/2026) ──────────────────────
    # «Bankruptcy of FTX» ra 0/12 nhịp có ảnh: mọi ảnh mang tên «FTX …», mà cụm đầy đủ
    # "bankruptcy of ftx" thì không tiêu đề nào chứa. Bộ lọc cụm của em bắt oan sạch.
    # Tên bài Wikipedia rất hay có dạng «<chuyện> of <chủ thể>» — Bankruptcy of · Sinking of ·
    # Collapse of · Trial of. Lõi tên nằm SAU giới từ, và đó mới là thứ ảnh mang.
    # Nhận CẢ HAI: cụm đầy đủ và lõi tên. Không nới hơn thế — lõi phải còn ≥4 ký tự để
    # «FTX» qua được mà «of» thì không.
    _loi = []
    for c in list(_cum):
        for _tt in (" of ", " in ", " at "):
            if _tt in c:
                _loi.append(c.split(_tt, 1)[1].strip())
                break
    # ── TÊN CƠ SỞ HAY ĐỔI CHỮ CUỐI  (bộ 212, 9/9/2026) ────────────────────────────────
    # «Savannah River Plant» tìm ra 24 ảnh và cổng cụm loại 23. Đọc tay sáu tiêu đề liên
    # quan: *Aerial of P Reactor at SRS* · *Historic P and R Reactor Photos — Savannah River
    # **Site*** ×3 · *SRS at 60 — Savannah River Ecology Lab* — **5/6 là ảnh ĐÚNG chủ thể**,
    # bị loại vì kho lưu trữ gọi nơi ấy là "Site" còn bài Wikipedia gọi là "Plant".
    # Wikidata KHÔNG cứu được ca này: `ten_khac` trả về đúng một tên (đã đo) vì đây là một
    # thực thể riêng, không phải trang đổi hướng.
    #
    # Luật nới: bỏ CHỮ CUỐI của tên, và chỉ khi phần còn lại còn ≥2 từ và ≥8 ký tự. Ranh
    # giới ấy không phải để cho đẹp — nó giữ nguyên hai ca đã trả giá:
    #     «Savannah River Plant» -> "savannah river"  (2 từ, 14 ký tự) -> NHẬN, cứu 5 ảnh
    #     «Meat Hope»            -> "meat"            (1 từ)            -> KHÔNG áp dụng,
    #                               nên ảnh cá voi Alaska vẫn bị loại như cũ
    #     «Midway Express»       -> "midway"          (1 từ)            -> KHÔNG áp dụng,
    #                               nên «Midway Pony Express station» vẫn bị loại
    # Tên hai chữ là chỗ phép nới nguy hiểm nhất, và đó đúng là chỗ luật này tự tắt.
    _bo_duoi = []
    for c in list(_cum):
        _tu = c.split()
        if len(_tu) >= 3:
            _ng = " ".join(_tu[:-1])
            if len(_ng) >= 8:
                _bo_duoi.append(_ng)
    _cum = [c for c in _cum + _loi + _bo_duoi if len(c) >= 3]
    if _cum:
        # CHỈ loại khi BIẾT tiêu đề mà nó không khớp. Ảnh không có trong sổ xuất xứ (nền kho
        # `comic_nen/`, ảnh cũ tải trước khi có sổ) thì "không biết" — và không biết KHÔNG
        # phải bằng chứng sai chủ thể (§15.6). Cổng selftest bắt đúng ca này: bản đầu loại
        # sạch 2/2 ảnh chỉ vì chúng chưa có trong sổ.
        # Xét TIÊU ĐỀ *hoặc* HẠNG MỤC: hạng mục là bằng chứng mạnh hơn hẳn — nó do người
        # đóng góp xếp, còn tiêu đề chỉ là tên tệp. Đo trên chính hồ ảnh «Savannah River
        # Plant»: ảnh của khu ấy mang hạng mục «Savannah River Site» dù tiêu đề chỉ ghi
        # «SRS at 60 -- H Canyon». Và phép nới này KHÔNG mở cửa cho ảnh lạc: đo ba tấm
        # «Corps hosts wetlands field exercise at Savannah State University» — hạng mục của
        # chúng là «PD US Army», không chứa cụm nào, nên vẫn bị loại đúng.
        _lac = []
        for d in duong:
            _t = " ".join(str(TEN_ANH.get(d, "")).lower().replace("file:", "").split())
            _m = " ".join(str(META_ANH.get(d, "")).lower().replace("file:", "").split())
            if _t and not any(c in _t or (bool(_m) and c in _m) for c in _cum):
                _lac.append(d)
        if _lac:
            duong = [d for d in duong if d not in _lac]
            print(f"   🚫 {len(_lac)} ảnh KHÔNG mang tên «{str(CHU_THE_TAP)[:26]}» — không làm nền")
            if not duong:
                return anh_nens

    # ── ĐÚNG CHỦ THỂ CHƯA ĐỦ — ẢNH CÒN PHẢI NHÌN ĐƯỢC  (anh: *"quá xấu tối ko được"*) ──
    # Bộ 195 «3dfx» đạt mọi số đo em đặt ra — 12/12 nhịp có ảnh, 1,65 giây/hình, ảnh ĐÚNG chủ
    # thể — và anh nhìn một cái là chê. Soi lại thì đúng: nền toàn ảnh macro die chip, sáng ở
    # giữa và đen kịt xung quanh; `objectFit: cover` cộng Ken Burns phóng vào đúng phần đen.
    # Em thêm cổng ĐÚNG CHỦ THỂ mà quên cổng NHÌN ĐƯỢC — §16.1 nguyên văn: điểm cổng và "đẹp"
    # là hai đại lượng khác nhau, và cổng chỉ biết thứ nó được dạy để đo.
    #
    # Đo tỉ lệ điểm tối (độ sáng < 60) trên ảnh gốc:
    #     3dfx          17,9% · 28,9% · 63,7% · 77,9%
    #     tư liệu tốt    2,1% – 14,0%   (Meat Hope, Fine Air, NARA)
    # Hai đầu tách sạch, và ngưỡng 25% nằm giữa khoảng trống — không cắt vào nhóm nào.
    # Đọc ảnh bằng PIL ở cỡ 200px: vài mili giây mỗi tấm, không đáng kể so với một lượt tải.
    def _nhin_duoc(d: str) -> bool:
        try:
            from PIL import Image
            # `PUB` là hằng của module (dòng 42). Bản đầu em dùng `pub` — một biến CỤC BỘ
            # của `nap_anh_that`, không có ở đây — nên hàm ném `NameError`, rơi vào `except`
            # và trả `True`: cổng chạy mà KHÔNG loại tấm nào, im lặng. Đúng dạng "hỏng mà báo
            # xanh" (§12.8), và chỉ lộ ra vì em đo lại chính 7 tấm 3dfx sau khi thêm cổng.
            # `os` chứ KHÔNG phải `_o`: `_o` là bí danh CỤC BỘ của `nap_anh_that`, và `pub`
            # cũng vậy. Em dùng nhầm cả hai trong cùng một hàm này — mỗi lần `except` nuốt
            # `NameError` rồi trả `True`, nên cổng chạy mà không loại tấm nào, KHÔNG một dòng
            # báo. Chỉ lộ ra vì em đo lại chính 7 tấm 3dfx sau khi thêm cổng và thấy vẫn 7/7.
            # §12.8: hỏng mà báo xanh — và ở đây `except` fail-open chính là thứ giấu nó.
            p = d if os.path.isabs(d) and os.path.exists(d) else os.path.join(PUB, d)
            if not os.path.exists(p):
                return True                 # không đọc được thì KHÔNG kết luận (§15.6)
            if os.path.getsize(p) < 2048:
                return False               # tệp rỗng/cụt: Remotion cũng không đọc được
            im = Image.open(p).convert("L")
            im.thumbnail((200, 200))
            px = list(im.getdata())
            return (sum(1 for v in px if v < 60) / max(1, len(px))) <= 0.25
        except Exception:
            # ── HỎNG MỀM ĐÚNG CHIỀU  (đo bộ 198, 9/9/2026) ────────────────────────────
            # Bản đầu trả `True` ở đây: "đọc không được thì cứ dùng". Với một tệp ẢNH thì
            # đó là chiều SAI — `f57850843a0b135954bf.jpg` là tệp **0 byte**, cổng cho qua,
            # và Remotion chết cả lượt dựng:
            #     CancelledError  Error loading image with src: .../anh_pd/f578…jpg
            #     ⚠ tập 198: bản dài hỏng — bỏ cả bộ
            # Props đã rất tốt (29 ảnh thật · 13/13 nhịp · 2,04 giây/hình) và mất trắng vì
            # MỘT tệp rỗng. PIL không mở được thì trình duyệt cũng không: loại.
            # §15.6 vẫn đúng ("không biết ≠ sai") nhưng ở đây ta BIẾT — biết là không đọc được.
            return False
    _toi = [d for d in duong if not _nhin_duoc(d)]
    if _toi:
        duong = [d for d in duong if d not in _toi]
        print(f"   🌑 {len(_toi)} ảnh QUÁ TỐI (>25% điểm tối) — không làm nền")
        if not duong:
            return anh_nens

    _bo_logo = [d for d in duong
                if _DAU_LOGO.search(str(TEN_ANH.get(d, "")).replace("File:", ""))]
    if _bo_logo:
        duong = [d for d in duong if d not in _bo_logo]
        print(f"   🚫 {len(_bo_logo)} tấm là LOGO/biểu tượng — không làm nền "
              f"(vẫn dùng cho thẻ logo)")
        if not duong:
            return anh_nens
    # Chỗ DUY NHẤT cả ba cổng đều đã chạy xong. Công bố ở đây chứ không ở từng lối ra: mọi
    # `return` phía trên là ca "không còn ảnh nào dùng được", và hồ rỗng đúng là câu trả lời.
    ANH_SACH = list(duong)
    ra = list(anh_nens)
    if not cau:
        n, m = len(ra), len(duong)
        if m >= n:
            return list(duong[:n])
        for k in range(m):
            ra[round(k * (n - 1) / max(1, m - 1)) if m > 1 else n // 2] = duong[k]
        return ra

    _bo = set(re.findall(r"[a-z]+", (CHU_THE_TAP or "").lower())) | {
        "the", "and", "for", "with", "from", "that", "this", "was", "were", "its",
        "file", "jpg", "png", "svg", "logo", "photo", "image", "company", "inc"}

    # ── NĂM LÀ TÍN HIỆU MẠNH NHẤT, VÀ BẢN ĐẦU BỎ MẤT NÓ  (7/9/2026) ────────────────────
    # Bộ tách từ đầu tiên chỉ lấy `[a-z]{3,}`, nên tiêu đề *"Eastman Kodak HQ 1900"* và câu
    # *"The headquarters opened in 1900"* khớp ĐÚNG 0 từ — chữ thì `HQ` vs `headquarters`
    # không trùng, còn `1900` thì bị vứt. Đo trên bốn nhịp thử: khớp 1/4.
    # Năm bốn chữ số là thứ nối chắc nhất giữa một tấm ảnh lưu trữ và một câu nói về mốc thời
    # gian — nó hiếm, nên trùng là trùng thật, không phải trùng ngẫu nhiên như từ thường.
    # Cho nó trọng số 3: một năm trùng thắng ba từ nội dung trùng.
    def _tu(t):
        t = str(t).lower()
        ra = {w for w in re.findall(r"[a-z]{3,}", t) if w not in _bo}
        for n in re.findall(r"\b(1[6-9]\d{2}|20[0-4]\d)\b", t):
            ra |= {"nam" + n, "nam" + n + "_", "nam" + n + "__"}   # đếm ba lần = trọng số 3
        return ra

    _ct = [_tu(c[0] if isinstance(c, (tuple, list)) else c) for c in cau[:len(ra)]]
    _ca = [(d, _tu(TEN_ANH.get(d, d))) for d in duong]
    # Ghép THAM LAM theo điểm giảm dần: cặp khớp mạnh nhất được chọn trước, mỗi ảnh và mỗi
    # nhịp chỉ dùng một lần. Đủ tốt cho 10–14 nhịp và không cần thuật toán ghép cặp tối ưu.
    cham = sorted(((len(a & b), i, d) for i, a in enumerate(_ct) for d, b in _ca),
                  key=lambda x: -x[0])
    xong_i, xong_d, n = set(), set(), 0
    for diem, i, d in cham:
        if diem < 1 or i in xong_i or d in xong_d:
            continue
        ra[i] = d
        xong_i.add(i); xong_d.add(d); n += 1
    # ── MẪU SỐ PHẢI LÀ SỐ ẢNH, KHÔNG PHẢI SỐ NHỊP  (8/9/2026) ─────────────────────────
    # Dòng cũ in `1/12 nhịp` và CHÍNH EM đọc nó thành "bộ ghép hỏng", rồi đi tìm lỗi trong
    # thuật toán ghép. Trần thật không phải 12: chủ thể «Fine Air» chỉ có **4 ảnh tự do**, nên
    # nhiều nhất 4 nhịp có ảnh. `1/12` trộn hai đại lượng — tỉ lệ ghép trúng, và độ phủ ảnh —
    # rồi cho ra một con số không đo cái nào.
    # §15.2: một con số không có ĐÚNG mẫu số thì mọi kết luận dựng trên nó đều lệch, và ở đây
    # nó lệch về phía đổ lỗi cho đoạn mã lành.
    print(f"   🔗 ảnh khớp NGHĨA: {n}/{len(duong)} ảnh rơi đúng nhịp nói về nó "
          f"· phủ {len(duong)}/{len(ra)} nhịp"
          + (" — HỒ ẢNH MỎNG, không phải phép ghép kém" if len(duong) < len(ra) / 2 else ""))
    # ── LƯỢT HAI: ẢNH THẬT CÒN DƯ ĐI VÀO NHỊP SẼ NHẬN NỀN CHUNG CHUNG  (anh, 8/9/2026) ──
    # Anh: *"tốn credit mà render ra mấy tấm ảnh ko liên quan này thì làm gì cho tốn"* ·
    # *"phải render cái gì người dùng nhìn cái nhận ra ngay chứ ko thì khác gì dùng kho nền
    # sẵn đâu"* · *"ảnh thật vẫn quá ít"*. Đo trên 13 bản dài gần nhất: **11/163 nền là ảnh
    # thật — 7%**, 152 nền còn lại là ảnh CF vẽ. Bộ 154 có SÁU ảnh thật trong tay mà chỉ
    # dùng ba.
    #
    # Lượt một ở trên đúng và phải giữ: ảnh vào đúng nhịp NÓI VỀ nó là chất lượng cao nhất.
    # Nhưng nó vứt phần dư, trong khi những nhịp không khớp khái niệm nào đằng nào cũng sắp
    # nhận một CĂN PHÒNG CHUNG do CF vẽ. Ở đúng những nhịp ấy, một tấm ảnh thật của chính chủ
    # thể luôn dễ nhận ra hơn — và nó còn CẮT một lượt gọi CF.
    #
    # Nên đây không phải đánh đổi: vừa dễ nhận ra hơn, vừa rẻ hơn. Ưu tiên nhịp GIỮA bài
    # (bỏ hook và câu chốt, hai chỗ đã có bố cục riêng), và không đặt hai ảnh thật liền nhau
    # để tập không đọc ra như một album ảnh.
    _du = [d for d in duong if d not in ra]
    if _du:
        # Ô THAY ĐƯỢC = ô chưa giữ một ảnh thật. KHÔNG dò theo TIỀN TỐ đường dẫn: bản đầu
        # của em dò `phim_nen/` và `nentap_`, mà lúc hàm này chạy thì `_nen_theo_tap` CHƯA
        # vẽ — ô đang giữ đường dẫn KHO NỀN với tiền tố khác. Kết quả đo trên bộ 155: bản dài
        # 0/11 ảnh thật trong khi short được 2/7, tức điều kiện chỉ tình cờ đúng ở nhánh
        # short. Em viết điều kiện theo giá trị ĐOÁN thay vì giá trị thật (§13.15).
        _co_that = set(duong)
        _trong = [k for k in range(1, max(1, len(ra) - 1))
                  if k < len(ra) and ra[k] not in _co_that]
        _dat = []
        for k in _trong:
            if _dat and k - _dat[-1] < 2:      # đừng đặt hai ảnh thật liền nhau
                continue
            _dat.append(k)
        for k, d in zip(_dat, _du):
            ra[k] = d
    return ra



# ── HỎI ẢNH BẰNG TÊN THỰC THỂ, KHÔNG BẰNG TÊN SỰ KIỆN  (anh, 8/9/2026) ─────────────────
# Anh: *"phải ép được ảnh vẽ vào cái gì người nhìn nhận ra được ngay — nói về facebook phải
# có logo facebook hay trụ sở, không vẽ chung chung"*.
#
# Ràng buộc đã đo và KHÔNG vượt được bằng prompt: FLUX không vẽ nổi logo. §12.7 đo trên 8
# mẫu — chuỗi ≤4 ký tự đúng 5/6, chuỗi dài **0/2**; §13.20 ghi chữ trong khung là chỗ mô hình
# hỏng nặng nhất. Bảo nó "vẽ logo Facebook" là đặt hàng một mớ ký tự loằng ngoằng, đúng thứ
# lưới bộ 131 đã hiện (`John Paul / Pauift / Ridle`).
#
# Nên thứ NHẬN RA ĐƯỢC phải là ẢNH THẬT. Đường ấy đã có từ §19.12 và đang cho 0–2 ảnh mỗi
# tập. Đo thẳng thì ra lý do, và nó không nằm ở bộ tìm ảnh:
#     «Facebook»            -> 8 ảnh
#     «2021 Facebook leak»  -> 0 ảnh   <- chuỗi mà dây chuyền THẬT SỰ hỏi
#     «Eastman Kodak»       -> 7 · «Concorde» -> 8
# Hồ đề tài cấp TÊN SỰ KIỆN, còn Wikimedia xếp ảnh theo TÊN THỰC THỂ. Không hạng mục nào tên
# "2021 Facebook leak", nên tập về Facebook không lấy nổi một tấm Facebook.
#
# Rút thực thể bằng QUY LUẬT, không bằng danh sách (§13.9): bỏ năm ở đầu, bỏ ngoặc ở đuôi, bỏ
# các danh từ SỰ KIỆN. Phần còn lại viết hoa chính là thực thể đáng hỏi.
_DANH_TU_SU_KIEN = (
    "leak", "leaks", "scandal", "scandals", "recall", "recalls", "outbreak", "crisis",
    "disaster", "controversy", "affair", "case", "cases", "collapse", "bankruptcy",
    "lawsuit", "investigation", "inquiry", "incident", "shortage", "shutdown", "strike",
)


def thuc_the(chu_the: str) -> str:
    """«2021 Facebook leak» -> «Facebook». Rỗng nếu không còn tên riêng nào."""
    t = re.sub(r"\s*\([^)]*\)\s*$", " ", str(chu_the or ""))     # bỏ «(1931)» ở đuôi
    t = re.sub(r"\b(1[6-9]\d{2}|20[0-4]\d)(\s*[–-]\s*(1[6-9]\d{2}|20[0-4]\d))?\b", " ", t)
    tu = [w for w in t.split() if w.strip()]
    giu = [w for w in tu if w.lower().strip(".,") not in _DANH_TU_SU_KIEN]
    # Tên riêng = từ CÓ chữ hoa, không phải từ BẮT ĐẦU bằng chữ hoa: «1MDB» mở đầu bằng chữ
    # số nên phép cũ vứt mất nó, mà đó chính là thực thể (§13.9 — nhận ra quy luật, đừng
    # liệt kê ngoại lệ; ở đây quy luật là "có chữ hoa giữa từ" chứ không phải "chữ đầu hoa").
    hoa = [w for w in giu if any(c.isupper() for c in w)]
    ra = " ".join(hoa).strip(" -–,.")
    return ra if len(ra) >= 3 and ra.lower() != str(chu_the or "").lower() else ""


def nap_anh_that(chu_the: str, toi_da: int = 6) -> list:
    """Tải ảnh PD/CC0 của chủ thể rồi COPY vào `engine-remotion/public/anh_pd`.

    Trả về danh sách đường dẫn TƯƠNG ĐỐI với public — dạng engine đọc được.

    ── VÌ SAO HÀM NÀY Ở ĐÂY, KHÔNG Ở TỆP THỬ  (7/9/2026) ─────────────────────────────────
    Bản đầu em viết phép tải + copy thẳng trong `_thu_vanished.py`. Chạy thì đúng, nhưng
    `ANH_THAT` khi ấy là một trường CHỈ tệp thử ghi — tới lúc nối vào đường chạy thật thì
    người nối phải viết lại phép copy, và chỗ dễ quên nhất chính là câu copy (đường dẫn hợp
    lệ mà ảnh không hiện). Đúng họ §13.1: cơ chế phải nằm ở nơi đường chạy thật với tới.

    Copy chứ không trỏ thẳng: Remotion chỉ phục vụ tệp nằm dưới `public`, còn `anh_tu_do`
    tải về `render-pipeline/anh_pd`.
    """
    import os as _o, shutil as _sh
    pub = _o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))),
                       "engine-remotion", "public", "anh_pd")
    _o.makedirs(pub, exist_ok=True)

    # ── HAI NGUỒN, THEO THỨ TỰ  (anh: "ảnh khớp bối cảnh vẫn hơi ít", 7/9/2026) ────────────
    # Wikimedia trước: nó giữ những tấm ĐÃ ĐƯỢC BIÊN TẬP chọn cho chính bài viết ấy, nên tấm
    # đầu thường là tấm biểu tượng. NARA sau, để BÙ — đo được nó có tư liệu ở chỗ Wikimedia
    # cạn: Concorde 3 -> +8 · Three Mile Island 0 -> +8.
    #
    # Không thêm Pexels/Pixabay: đo truy vấn vô nghĩa `zzqx wubblefrotz` ra **4.248 ảnh**
    # (bóng bay). Kho không bao giờ trả zero là kho không phân biệt được "không có" với "có"
    # (§15.2), nên mọi phép lọc đặt sau nó chỉ đang lọc rác.
    ra, thay = [], set()
    # ── NGUỒN THỨ TƯ: OPENVERSE  (anh, 9/9/2026) ───────────────────────────────────────
    # Anh: *"có thể thêm vài nguồn ok cho phong phú hoặch dự phòng"*. Đo 20 chủ thể ngẫu
    # nhiên: ba nguồn cũ cho TRUNG VỊ 5 ảnh/chủ thể, 8/20 chủ thể có dưới 3 ảnh — trong khi
    # footage đổi mỗi 1,5–2,5 giây cần ~30 hình một tập.
    # Openverse gộp nhiều bảo tàng, KHÔNG cần khoá, và qua bài kiểm truy vấn vô nghĩa
    # (`zzqx wubblefrotz` -> 0). Đo sau bộ lọc: +10,7 ảnh/chủ thể.
    # Đứng CUỐI vì độ chính xác giảm dần: ảnh của BÀI (người viết chọn) > NARA (bản ghi có
    # tên chủ thể) > Openverse (tìm theo chữ, phải lọc cụm). Một ảnh sai đắt hơn một ảnh
    # thiếu, nên nguồn nhiễu hơn chỉ được LẤP phần còn thiếu (§19.13).
    # `anh_smithsonian` KHÔNG có trong danh sách này — xem đầu `anh_smithsonian.py`: khoá
    # chạy (dùng lại khoá NARA, trần 1.000/giờ) nhưng API KHÔNG trả URL ảnh, đo 0/10 bản ghi.
    # Nối một nguồn đóng góp 0 ảnh chỉ tốn 2 lượt gọi mỗi lượt dựng (§13.22).
    for _ten_mod in ("anh_tu_do", "anh_nara", "anh_openverse"):
        if len(ra) >= toi_da:
            break
        try:
            _M = __import__(_ten_mod)
        except Exception as e:
            print(f"   ⚠ không nạp được {_ten_mod} ({str(e)[:40]}) — bỏ qua nguồn này")
            continue
        try:
            _ds = _M.anh_cua(chu_the, toi_da=toi_da - len(ra))
        except Exception as e:
            print(f"   ⚠ {_ten_mod} hỏng ({str(e)[:40]}) — bỏ qua nguồn này")
            continue
        for a in _ds:
            d = _M.tai_ve(a)
            if not d:
                continue
            ten = _o.path.basename(d)
            # KHỬ TRÙNG THEO CẢ TIÊU ĐỀ NGUỒN — xem chú thích ở nhánh Commons phía dưới. Hai
            # vòng tải là hai nhánh song song, và bản vá đầu chỉ chạm một (§6).
            _tt = " ".join(str(a.get("ten", "")).lower().replace("file:", "").split())
            if ten in thay or (_tt and _tt in thay):
                continue
            thay.add(ten)
            if _tt:
                thay.add(_tt)
            dich = _o.path.join(pub, ten)
            if not _o.path.exists(dich):
                _sh.copyfile(d, dich)
            ra.append("anh_pd/" + ten)
            TEN_ANH["anh_pd/" + ten] = a.get("ten", "")
            META_ANH["anh_pd/" + ten] = " ".join(
                str(a.get(k) or "") for k in ("cat", "ob"))
            _ghi_so_anh()
            if len(ra) >= toi_da:
                break
    # ── TẦNG CUỐI: TÌM THẲNG TRÊN COMMONS  (anh: *"ảnh thực tế quá ít"*, 8/9/2026) ────
    # `generator=images` chỉ trả ảnh ĐƯỢC DÙNG TRONG BÀI Wikipedia — đo bốn chủ thể ra 1–10
    # ảnh qua cổng. Tìm thẳng trên Commons cho 27–30 ảnh đủ lớn mỗi chủ thể, và sau khi đi
    # qua ĐÚNG bộ lọc cũ thì thêm được thật: MetLife 1 -> 6 · Kodak 10 -> 16.
    #
    # Nhưng nó đứng CUỐI, không đứng đầu, vì nó mang rủi ro TRÙNG TÊN: «Hôtel Le Concorde
    # Québec» là một khách sạn, không phải máy bay — đúng thứ anh gọi *"râu ông nọ cắm cằm
    # bà kia"*, và §19.13 đã trả giá đúng chuyện ấy với ga tàu điện ngầm Paris. Ảnh của BÀI
    # có độ chính xác cao hơn hẳn (chúng được người viết bài chọn), nên chúng đi trước và
    # Commons chỉ LẤP phần còn thiếu. Một ảnh sai đắt hơn một ảnh thiếu.
    if len(ra) < toi_da:
        # GỌI THẲNG `anh_tu_do`, KHÔNG dùng `_M`: sau vòng lặp nguồn ở trên, `_M` đang trỏ
        # vào `anh_nara` — module ấy không có tham số `commons`, nên lời gọi ném `TypeError`
        # và `except` nuốt mất. Tầng này vì thế thêm được ĐÚNG 0 ảnh mà không báo gì (§15.2).
        try:
            import anh_tu_do as _ATD
            _cm = _ATD.anh_cua(chu_the, toi_da=(toi_da - len(ra)) * 3, commons=True)
            # ── TẦNG COMMONS PHẢI KHỚP CỤM, KHÔNG KHỚP TỪ RỜI  (anh soi bộ 159, 8/9) ────
            # Bộ «Midway Express» lấy về «Midway Pony Express station» (trạm xe ngựa ở Utah),
            # «Midway Plaisance Map» (công viên Chicago) và một bản đồ hội chợ 1893 — 4/6 ảnh
            # thật là chủ thể KHÁC. Đúng thứ anh gọi *"râu ông nọ cắm cằm bà kia"*.
            #
            # Ảnh của BÀI Wikipedia thì an toàn (người viết bài đã chọn), nên luật này chỉ áp
            # cho tầng Commons — nơi phép tìm khớp theo TÊN. «Midway Express» gồm hai từ rất
            # phổ biến, nên khớp từ RỜI sẽ trúng mọi thứ có "midway" hoặc "express" ở bất kỳ
            # đâu. Đòi CỤM LIỀN thì «Midway Pony Express» trượt vì có "Pony" chen giữa.
            # KHỚP CỤM VỚI CẢ TÊN GỌI KHÁC. Khớp cụm cứng loại oan đúng những tấm hay nhất:
            # «MetLife Building» mất hết ảnh «Pan Am Building» — TÊN CŨ của chính toà nhà ấy —
            # và «Credit Suisse» mất «Schweizerische Kreditanstalt». Wikidata giữ sẵn danh
            # sách tên gọi khác ở `aliases`, nên không phải đoán và không phải chép tay.
            try:
                import logo_wd as _LW2
                _ten_ds = _LW2.ten_khac(chu_the) or [chu_the]
            except Exception:
                _ten_ds = [chu_the]
            _cums = [" ".join(str(t).lower().split()) for t in _ten_ds if t]
            _cums = [c for c in _cums if len(c) >= 4]
            if _cums:
                _cm = [x for x in _cm
                       if any(c in " ".join(str(x.get("ten", "")).lower()
                                            .replace("file:", "").split()) for c in _cums)]
        except Exception as _e:
            print(f"   ⚠ tầng Commons hỏng ({type(_e).__name__}: {str(_e)[:44]})")
            _cm = []
        for a in (_cm or []):
            try:
                d = _M.tai_ve(a)
                if not d:
                    continue
                ten = _o.path.basename(d)
                # KHỬ TRÙNG THEO CẢ TIÊU ĐỀ NGUỒN. Tên tệp là BĂM CỦA URL, nên cùng một tấm
                # phục vụ ở hai bề ngang khác nhau ra hai tệp khác nhau và lọt cả hai — đo
                # trên «Credit Suisse»: «Schweizerische Kreditanstalt 1898» vào hai lần. Một
                # tập có hai khung y hệt thì người xem đọc ra là lỗi, không đọc ra là dụng ý.
                _tt = " ".join(str(a.get("ten", "")).lower().replace("file:", "").split())
                if ten in thay or (_tt and _tt in thay):
                    continue
                thay.add(ten)
                if _tt:
                    thay.add(_tt)
                dich = _o.path.join(pub, ten)
                if not _o.path.exists(dich):
                    _sh.copyfile(d, dich)
                ra.append("anh_pd/" + ten)
                TEN_ANH["anh_pd/" + ten] = a.get("ten", "")
                META_ANH["anh_pd/" + ten] = " ".join(
                    str(a.get(k) or "") for k in ("cat", "ob"))
                _ghi_so_anh()
                if len(ra) >= toi_da:
                    break
            except Exception:
                continue

    # ── HỎI LẠI BẰNG TÊN THỰC THỂ KHI TÊN SỰ KIỆN KHÔNG RA GÌ ────────────────────────
    # Đo: «2021 Facebook leak» -> 0 ảnh, «Facebook» -> 8. Wikimedia xếp ảnh theo THỰC THỂ,
    # hồ đề tài cấp tên SỰ KIỆN. Hỏi lần hai bằng thực thể là cách duy nhất lấy được thứ
    # người xem NHẬN RA NGAY (logo, trụ sở) mà không bắt FLUX vẽ chữ (§12.7 · §13.20).
    if len(ra) < 3:
        _tt = thuc_the(chu_the)
        if _tt:
            try:
                _them = nap_anh_that(_tt, toi_da=toi_da)
            except Exception:
                _them = []
            for _x in (_them or []):
                if _x not in ra:
                    ra.append(_x)
            if _them:
                print(f"   🔁 hỏi lại bằng thực thể «{_tt}»: +{len(_them)} ảnh thật")
    return ra

# ── LỆNH DẶN RIÊNG CHO MỘT GIỌNG  (anh đề xuất, 7/9/2026) ─────────────────────────────────
# Bật `MOT_GIONG` mà vẫn dùng `LENH_THOAI` thì mô hình viết ĐỐI THOẠI: nó hỏi rồi tự đáp, và
# ra những lượt trống rỗng — "2012" đứng một mình. Đúng thôi: lệnh dặn ấy nói "hai nhân vật".
# Một giọng là một ĐỊNH DẠNG KHÁC, không phải một tuỳ chọn của định dạng cũ.
LENH_MOT_GIONG = """You turn a narrated explainer script into what ONE expert says to camera.

There is no second person. No questions asked to anyone. No interviewer. One voice, start to
finish, explaining something to the viewer.

RULES
1. EVERY number, unit and dollar figure in the narration must appear word for word. Never
   round, never change, never drop one. They are computed facts.
1b. A number never stands alone as a line. "2012" is not a sentence; "By 2012 the printers
   were gone" is. A figure must arrive attached to what it measures.
2. One sentence per line, 7 to 14 words. Longer than that and the viewer loses the thread;
   shorter and the figure has nowhere to land.
3. A line marked [KEEP] says the thing everyone believes is wrong. Keep that claim with its
   own nouns, and make the VERY NEXT line say what actually happened instead.
4. Say "you" or "your" at least twice: tie it to the viewer's own life. The last line is not
   a number — it is the sentence they repeat to someone tomorrow.
5. Plain spoken American English. No "as you can see", no "let's dive in", no narrator
   throat-clearing. Explain like someone who knows it, talking to one person.
6. Every line MUST carry "i": the number of the narration line it delivers. Keep the same
   order as the narration; never go backwards. That number belongs in the "i" FIELD ONLY —
   "chu" is what the expert says out loud, and nobody says a line number out loud. Do not
   open "chu" with it in any shape: not "7.", not "i7:", not "Line seven:", not "Turn 7 -".
   Start "chu" with the first real word of the sentence.

Return ONLY a JSON array: [{"i":0,"ai":"b","chu":"...","cx":"tu_tin"}]
"ai" is always "b". "cx" is one of: trung_tinh, tu_tin, nghi_ngo. Never excited, never angry.
"""


def _bien_do(mp3: str, fps: int = 30, so_khung: int = 0) -> list:
    """Envelope RMS của audio, MỘT giá trị 0..1 mỗi khung hình — để nhép miệng theo BIÊN ĐỘ
    THẬT thay vì đoán khẩu hình từ chính tả (anh: *"nhép miệng chưa đúng và khớp"*, 10/9).

    Cách chuẩn cho hoạt hình: miệng mở tỉ lệ độ TO của tiếng ở đúng khung ấy — to (nguyên âm)
    thì mở, nhỏ/lặng (phụ âm/khoảng nghỉ) thì ngậm. Khớp CHÍNH XÁC vì lấy từ chính tiếng nói,
    không phụ thuộc chính tả tiếng Anh (vốn ≠ phát âm).
    """
    import subprocess as _sp, struct as _st
    try:
        raw = _sp.run(["ffmpeg", "-v", "error", "-i", mp3, "-ac", "1", "-ar", "8000",
                       "-f", "s16le", "-"], capture_output=True).stdout
    except Exception:
        return []
    if not raw:
        return []
    n = len(raw) // 2
    mau = _st.unpack("<%dh" % n, raw[:n * 2])
    b_khung = max(1, 8000 // fps)                       # mẫu mỗi khung hình
    tong = so_khung or (n // b_khung + 1)
    ra = []
    for k in range(tong):
        a = k * b_khung; b = min(n, a + b_khung)
        if b <= a:
            ra.append(0.0); continue
        seg = mau[a:b]
        rms = (sum(x * x for x in seg) / len(seg)) ** 0.5
        ra.append(rms)
    if not ra:
        return []
    # chuẩn hoá theo phân vị 95 (tránh một đỉnh làm cả chuỗi bé lại), kẹp 0..1, cong nhẹ
    _s = sorted(ra); dinh = _s[int(len(_s) * 0.95)] or max(_s) or 1.0
    return [round(min(1.0, (v / dinh) ** 0.6), 3) for v in ra]


def mot_tap(ma: str, idx: int, ve_nen_moi: bool = True, chuong: int = 0) -> str:
    """`chuong > 0` -> BẢN DÀI 16:9 (`KichComicWide`), tên `v11L_`.

    ── VÌ SAO BẢN DÀI DÙNG CHUNG ĐÚNG HÀM NÀY  (anh giao, 7/9/2026) ───────────────────────
    Anh xin một clip dài 2–3 phút khung ngang. Cả hai thứ cần đã có sẵn và chưa ai nối:
    `giai_thich.kich_ban(ma, idx, long=True, so_chuong=N)` sinh 32/59/95 nhịp cho 3/6/10
    chương, và `Root.tsx` đã khai composition `KichComicWide` 1920×1080 dùng CHÍNH component
    `KichComic`. Viết một hàm dựng thứ hai là tạo nguồn sự thật thứ hai cho mọi thứ vừa sửa
    hôm nay — vai chuyên gia, ngữ điệu, luân phiên, trang phục — và bản sao ấy sẽ mòn dần
    khỏi bản gốc mà không ai thấy (§13.1 · §15.25).

    Nên bản dài chỉ khác bản ngắn ĐÚNG BA THAM SỐ: số chương, tên composition, tiền tố tệp.
    Mọi bộ vá của hôm nay tự động áp cho nó.
    """
    global MOT_GIONG, DAO_CU_TAP, CHU_THE_TAP, ANH_THAT
    # Khối này phải chạy TRƯỚC phép chọn vai: nhánh "một kênh một người" đọc `MOT_GIONG`,
    # và bản đầu đặt khối ở dưới 53 dòng nên cờ vẫn là False lúc chọn — tức cơ chế vừa dựng
    # không bao giờ chạy trong đường sản xuất, chỉ chạy khi tệp THỬ bật cờ từ ngoài.
    # Đúng họ §15.19: mọi lượt RẢI phải chạy sau MỌI lượt CHÈN, ở đây là mọi lượt ĐỌC một cờ
    # phải chạy sau lượt ĐẶT cờ ấy. Không lỗi nào báo — chỉ là nhân vật vẫn xoay như cũ.
    # ── ĐƯỜNG "VÌ SAO" ĐI TRƯỚC, BỘ SINH CŨ LÀ TẦNG DƯỚI  (nối 7/9/2026) ────────────────
    # Trước lượt nối này, mọi thứ dựng cả ngày (chủ thể có thật · khuôn hỏi · một giọng ·
    # ảnh thật · nền theo chủ thể) chỉ với tới được qua `_thu_vanished.py` — một tệp THỬ.
    # Đường sản xuất vẫn chạy bộ sinh ĐO LƯỜNG cũ, tức toàn bộ công việc không tới người xem.
    #
    # Hỏng thì rơi về bộ sinh cũ chứ KHÔNG mất một tập: hết chủ thể, chủ thể thiếu tư liệu,
    # hay mạng hỏng đều là chuyện bình thường ở tầng này (§7 — tầng dưới cùng không gọi mạng).
    _vs = None
    try:
        import vi_sao as _VS
        # `bo_1_3` đã CHỌN chủ thể cho cả bộ và ghim vào `BO_SINH`. Không có cờ này thì
        # `mot_tap` chọn lại ở từng clip và GHI ĐÈ cái ghim — đo lượt thật: bản dài về
        # `Air California` còn ba short về `Air New England`, `ATA Airlines`, `Air Berlin`,
        # mà cả ba vẫn chạy nền vẽ cho Air California. Bản vá trước đưa quyết định về
        # `bo_1_3` nhưng KHÔNG chặn nơi cũ, nên hai nơi cùng quyết và nơi sau thắng (§15.3).
        if DA_GHIM:
            _vs = None
        elif _VS.co_vi_sao(ma):
            _vs = _VS.sinh(ma, idx)
    except Exception as e:
        print(f"   ⚠ đường 'vì sao' hỏng ({str(e)[:50]}) — dùng bộ sinh cũ")
    if _vs:
        _ch = _VS.DA_CHON.get((ma, idx), {})
        MOT_GIONG = True
        CHU_THE_TAP = _ch.get("chu_the", "")
        DAO_CU_TAP = _ch.get("hinh_mau", "")
        # ── XIN 32 ẢNH, KHÔNG PHẢI 14  (anh: footage đổi mỗi 1,5–2,5s, 9/9/2026) ──────────────────
        # Trần cũ 14 đặt khi ảnh chỉ dùng làm NỀN NHỊP — 12 nhịp thì 14 là dư. Nay hình còn
        # đổi TRONG nhịp (xem `nenCat`), nên một tập 71 giây cần ~35 hình để đạt 2 giây/hình.
        # Đo trên 20 chủ thể: chủ thể giàu có tới 33 ảnh, mà mình chỉ xin 14 — tự bỏ hơn nửa.
        # Trần là trần XIN, không phải trần bắt buộc: chủ thể nghèo vẫn trả về ít, không hỏng.
        ANH_THAT = nap_anh_that(CHU_THE_TAP, toi_da=32) if CHU_THE_TAP else []
        print(f"   🎨 hình mẫu: {DAO_CU_TAP or '(không nhận ra)'} · "
              f"🖼 ảnh thật: {len(ANH_THAT)}")
        # `import giai_thich as G` nằm ở DƯỚI trong chính hàm này, nên `G` là biến CỤC BỘ và
        # dùng nó ở trên là `UnboundLocalError` — không phải lỗi nạp module, mà lỗi phạm vi.
        # Nhập riêng ở đây thay vì dời lệnh import kia lên: dời lên là đụng vào một khối đang
        # chạy đúng, và §12.5 dặn hỏi lại trước khi đổi thứ đang hoạt động.
        import giai_thich as _G0
        _G0.BO_SINH[k_ma_sinh(ma)] = lambda _i, _r=_vs: _r
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
    # ── NGƯỜI BIẾT CON SỐ PHẢI RA CHẤT CHUYÊN GIA  (anh giao, 7/9/2026) ──────────────────
    # Anh: *"nếu là channel phân tích thì phong cách nhân vật đúng chất chuyên gia mỗi channel"*.
    # `LENH_THOAI` đã quy định vai B là *"người BIẾT con số"*, nhưng cặp vai xoay theo `_cap`
    # nên ai vào vai B là ngẫu nhiên. Đo 216 lượt xếp vai: **158 lượt (73%) vai B không ra chất
    # chuyên gia** — có cả một bé gái 16 tuổi đi giải thích số liệu cho người lớn.
    #
    # Không khoá cứng một người vào vai B (mất hẳn đa dạng: 30 cặp còn 5). Giữ nguyên CẶP, chỉ
    # đổi THỨ TỰ trong cặp: người có nghề hơn nhận vai trả lời. Đa dạng giữ nguyên vì cặp
    # (X,Y) và (Y,X) vẫn là hai cặp khác nhau về hình; cái đổi là ai cầm con số.
    def _chat_nghe(v) -> int:
        t = (str(v.get("vai") or "") + " " + str(v.get("ta") or "")).lower()
        d = 0
        if re.match(r"^(dr|doctor|professor|prof|chef|nurse|officer|ranger|coach|foreman|"
                    r"chief|marshal|deputy|lieutenant|warden|capt(?:ain)?|sgt|sergeant|"
                    r"attorney|counsel|inspector)\b", t):
            d += 4
        d += 3 * len(re.findall(r"\b(engineer|scientist|analyst|technician|inspector|auditor|"
                                r"surveyor|physiologist|specialist|bookkeeper|operator|"
                                r"actuary|navigator|demographer|researcher|instructor|"
                                # Ngành TÀI CHÍNH và LUẬT thiếu hẳn khỏi bảng, nên chính hai
                                # chuyên gia anh nêu tên làm ví dụ lại không vào nổi top hai.
                                r"accountant|attorney|lawyer|paralegal|appraiser|adjuster|"
                                r"economist|statistician|underwriter|pathologist|"
                                r"epidemiologist|acoustician|hydrologist|geologist)\b", t))
        # ĐỒ NGHỀ và ĐỒNG PHỤC, không chỉ chức danh  (anh giao, 7/9/2026)
        # Đọc tay 84 vai cận ngưỡng: `Ranger Ellis` (áo kiểm lâm + phù hiệu), `Gus/howbig`
        # (thước đo laser), `Gus/howloud` (máy đo decibel), `Cass` (bộ chống cháy phản quang)
        # đều là người có nghề thật mà thước cũ cho 1–2 điểm, vì nó chỉ đếm CHỨC DANH.
        # Thứ người xem đọc ra "người này biết việc" trong nửa giây là ĐỒ NGHỀ trên tay và
        # BỘ ĐỒ trên người, không phải hai chữ đứng trước tên. Đếm chức danh là danh sách vô
        # hạn (§13.9); đếm đồ nghề thì bảng đóng lại được vì số dụng cụ đo là hữu hạn.
        # `notebook` và `ledger` TRẦN bị bỏ khỏi bảng: `Mira/whatif` ("lavender dress,
        # notebook, naive") và `Eli/realcost` ("ledger book, frugal") vượt ngưỡng chỉ nhờ một
        # cuốn sổ, trong khi tính cách khai ra là NGÂY THƠ và TIẾT KIỆM — trái hẳn chất chuyên
        # gia. Một cuốn sổ ai cũng cầm được; thứ chỉ người có nghề mới cầm là DỤNG CỤ ĐO.
        d += 2 * len(re.findall(r"\b(lab coat|safety|apron|clipboard|microscope|scanner|"
                                r"lab notebook|tally|pocket ledger|goggles|"
                                r"measuring rod|decibel meter|chronometer|calipers|stopwatch|"
                                r"weight scale|weight bar|abacus|multi-tool|dividers|"
                                r"route chart|gauge|thermometer|calculator|legal pad|"
                                r"statutes|fee-?schedule|cost-?sheet|ten-?key|"
                                r"hard hat|hi-?vis|high-?visibility|coveralls|jumpsuit|badge|"
                                r"fire-?res|fire-?ret|heat-?proof|stethoscope|scrub coat)\b", t))
        d += len(re.findall(r"\b(analytical|methodical|meticulous|precise|patient|probing|"
                            r"unhurried|reads every line|delighted by detail)\b", t))
        # Tính cách khai ra NGƯỢC với chất chuyên gia thì trừ thẳng — một người được tả là
        # "naive" không thể là người mà cả tập đi hỏi con số.
        d -= 4 * len(re.findall(r"\b(naive|gullible|clueless|frugal|thrifty|mischievous|"
                                r"complaining|grumbling|impatient|hopeful|daring)\b", t))
        m = re.search(r"(\d{1,2})\s*-?\s*year", t)
        n = int(m.group(1)) if m else 38
        if n < 18:
            d -= 6                    # trẻ con hỏi thì hợp, trả lời số liệu thì không
        elif 30 <= n <= 65:
            d += 1
        return d
    # ── MỘT NGƯỜI HỎI, MỘT CHUYÊN GIA TRẢ LỜI — CHIA HAI HỒ  (anh giao, 7/9/2026) ───────
    # Chỉ đổi THỨ TỰ trong cặp thì vẫn còn 50% lượt vai B không ra chất chuyên gia, vì vòng
    # xoay `_cap` chỉ đưa chuyên gia vào ~29% số cặp — có cặp không có ai là chuyên gia cả.
    #
    # Format của một kênh giải thích không phải "hai người bất kỳ nói chuyện" mà là **người
    # tò mò hỏi, người có nghề trả lời**. Nên chia dàn vai làm hai hồ và bắt cặp CHÉO: một
    # người từ hồ hỏi, một chuyên gia từ hồ trả lời. Đa dạng không mất — `k` người hỏi × `m`
    # chuyên gia vẫn cho `k·m` cặp, và mỗi tập vẫn đổi cả hai phía.
    #
    # Kênh chưa có chuyên gia nào thì quay về cách cũ (đổi thứ tự trong cặp) thay vì bịa ra
    # một vai không có trong dàn — thà nhận là chưa đủ còn hơn giả vờ là đủ.
    _gioi = sorted(_dan, key=_chat_nghe, reverse=True)
    # Hồ HỎI lấy CẢ DÀN trừ đúng người đang trả lời — một chuyên gia hỏi một chuyên gia khác
    # là chuyện bình thường ở kênh giải thích, và chặn họ ra khỏi vai hỏi làm số cặp tụt từ 30
    # xuống 5–9. Đa dạng là thứ người xem CẢM ĐƯỢC (§14.9), không đánh đổi lấy một quy tắc.
    _ho_cg = [v for v in _dan if _chat_nghe(v) >= 3]
    if _ho_cg and MOT_GIONG:
        # ── MỘT KÊNH = MỘT NGƯỜI, CỐ ĐỊNH  (anh, 7/9/2026) ─────────────────────────────
        # Anh: *"mỗi channel giờ 1 nhân vật phải ko … nhìn ra 1 người"*. Dòng dưới xoay
        # chuyên gia theo SỐ TẬP, nên cùng một kênh mỗi tập một mặt — đúng thứ phá tan việc
        # người xem nhận ra kênh. Xoay là đúng cho định dạng HAI NGƯỜI (đa dạng cặp thoại);
        # với một người dẫn thì nó là lỗi. §12.5 lần nữa.
        #
        # Chọn TẤT ĐỊNH: người có nghề nhất, hoà thì so tên — không dùng `hash()` của Python
        # (`PYTHONHASHSEED` ngẫu nhiên nên máy anh và runner ra hai người khác nhau, §13.13).
        # Đo 18 kênh: mỗi kênh ra một người rõ rệt và khác nghề nhau — Attorney Brooks ·
        # Dr Quintero · Inspector Nadia · Nurse Tara · Sergeant Boone…
        _c = sorted(_ho_cg, key=lambda v: (-_chat_nghe(v), str(v.get("vai") or "")))[0]
        # Phần gán `vai` nằm lại ở nhánh dưới khi em tách nhánh này ra — `UnboundLocalError`
        # ở dòng `if len(vai) < 2`. Tách một nhánh thì phải mang theo cả phần ĐUÔI dùng chung,
        # không chỉ phần đầu khác nhau (§6: vá một nhánh, để nguyên nhánh song song).
        # Một giọng thì người HỎI cũng là chính người ấy: `LENH_MOT_GIONG` chỉ dựng lời cho
        # vai A, còn vai B không có thoại nào — nhưng cấu trúc vẫn cần hai chỗ.
        vai = [_c, _c]
    elif _ho_cg:
        _c = _ho_cg[(idx // max(1, len(_dan) - 1)) % len(_ho_cg)]
        _khac = [v for v in _dan if v is not _c]
        _h = _khac[idx % len(_khac)]
        vai = [_h, _c]
    else:
        _a, _b = _dan[_i], _dan[_j]
        vai = [_a, _b] if _chat_nghe(_b) >= _chat_nghe(_a) else [_b, _a]
    if len(vai) < 2:
        print("   ❌ kênh này chưa khai đủ hai vai"); return ""
    # ── CHỈ SỐ TRANG PHỤC PHẢI THEO CẶP VAI ĐÃ CHỌN  (7/9/2026) ─────────────────────────
    # Anh soi khung `hiddenfee`: *"sao giọng nữ mà ông lão hói đầu"*. Đúng, và nặng hơn —
    # nhân vật khai `gioi: nu` mà đội trang phục có RÂU DÊ, đúng lỗi §11 đã ghi từ đầu
    # (*"nữ công tố đeo râu dê"*) quay lại.
    #
    # Bảng trang phục KHÔNG sai: Tobias (nam) hói + râu dê, Gwen (nữ) tóc ngắn — đo tận nơi.
    # Sai là chỗ ghép: hôm nay em đổi cách chọn cặp vai (hồ hỏi × hồ chuyên gia) và gán vào
    # `vai`, nhưng `do_vai(ma, (_i, _j))` ở dưới vẫn dùng cặp chỉ số CŨ. Nên giọng và giới
    # lấy từ cặp MỚI còn quần áo lấy từ cặp CŨ — hai nguồn sự thật cho một nhân vật, đúng
    # thứ §11 dặn đừng bao giờ tạo ra. Hồi quy do chính bản sửa sáng nay đẻ ra.
    #
    # Suy chỉ số TỪ `vai` thay vì giữ một cặp song song: còn hai biến thì còn cách để lệch.
    _i = next((_k for _k, _v in enumerate(_dan) if _v is vai[0]), _i)
    _j = next((_k for _k, _v in enumerate(_dan) if _v is vai[1]), _j)

    global BEN_DUNG
    BEN_DUNG = GU_DUNG.get(ma, ("giua", "vao", "moc"))[0]
    k, tieu, hook, hook_phu, nhip, muc = G.kich_ban(ma, idx, chuong > 0, chuong or 3)
    # `[KEEP]` là dấu dành cho MÔ HÌNH và cho cổng giữ cú lật — nó không được lên màn hình
    # cũng không được vào phụ đề. Gỡ khỏi chính nhịp NGAY SAU khi đã đọc ra `loi`, để mọi
    # nhánh phía sau (thẻ chữ, ảnh bìa, `.tai.json`) đều thấy câu sạch.
    loi = [n["loi"] for n in nhip]
    for _n0 in nhip:
        if str(_n0.get("loi", "")).startswith("[KEEP]"):
            _n0["loi"] = _n0["loi"][6:]
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
    # ── GIỌNG PHẢI ĐỌC TỪ DÀN VAI THẬT  (anh nghe ra, 7/9/2026) ──────────────────────────
    # Anh: *"nhiều clip nhân vật đọc lời thoại nhầm ... nhầm vai"*. Bản cũ ghi CỨNG
    # `["luat_tre","nu","trung",...]` và `["khoa_hoc","nam","trung",...]`, tức vai A LUÔN giọng
    # nữ trung niên và vai B LUÔN giọng nam trung niên — bất kể cặp xoay ra ai.
    #
    # `vai_va_giong` lấy đúng hai trường ấy để tra `GIONG_VAI[(gioi, tuoi)]`, nên hình vẽ là
    # Gus/Tank/Nia của kênh (do `do_vai` ghi đè sau) còn GIỌNG thì của hai vai bộ hài đời cũ.
    # Đo trên 18 kênh × 12 tập × 2 vai = 432 lượt gán: **218 lượt sai giới — đúng 50%.**
    # Nửa số nhân vật nói bằng giọng khác giới của mình, và không cổng nào đo giọng.
    #
    # `tuoi` cũng ghi cứng `"trung"`, nên vai 12 tuổi (Ravi của `smallest`) và vai 62 tuổi đều
    # nói giọng trung niên — bảng `GIONG_VAI` có sẵn `tre`, `gia` và một giọng `tre_con` chưa
    # bao giờ được dùng (§15.12: thứ có sẵn mà không ai gọi).
    #
    # Nay suy từ chính câu mô tả vai — nguồn sự thật duy nhất, đúng luật "đừng tạo nguồn thứ
    # hai" ở §11: mô tả đã ghi "36-year-old woman, ..." nên giới và tuổi đọc thẳng ra được.
    def _gioi_tuoi(ta: str, thu_tu: int):
        t = " " + str(ta or "").lower()
        g = ("nu" if re.search(r"\b(woman|girl|she|her)\b", t) else
             "nam" if re.search(r"\b(man|boy|he|his)\b", t) else
             ("nu", "nam")[thu_tu % 2])          # mô tả không nói giới -> xen kẽ, đừng đoán
        m = re.search(r"(\d{1,2})\s*-?\s*year", t)
        n = int(m.group(1)) if m else 38
        if n < 16:
            return "tre", "tre_con", 0.82        # giọng trẻ con, và người thấp hẳn
        return g, ("tre" if n < 32 else "trung" if n < 56 else "gia"), (0.97 if g == "nu" else 1.00)
    _gA, _tA, _cA = _gioi_tuoi(vai[0].get("ta"), 0)
    _gB, _tB, _cB = _gioi_tuoi(vai[1].get("ta"), 1)
    KC.VAI[de] = [["luat_tre", _gA, _tA, _cA, vai[0]["vai"], vai[0]["vai"]],
                  ["khoa_hoc", _gB, _tB, _cB, vai[1]["vai"], vai[1]["vai"]]]
    KC.NHAC[de] = G.GU_RIENG.get(ma, ("", "music/forecast.mp3", ""))[1]
    KC.MAU_CHINH[de] = g["chinh"]
    KC.MAU_PHU[de] = g["phu"]
    KC.NET_KENH.setdefault(de, dict(net=7, cham=9, bo=26, tile=0.60))
    KC.BO_CUC_KENH.setdefault(de, dict(duoi=False, bo=0, no="HUH?"))
    kk = {"ten": g["ten"], "handle": "@" + ma, "a": "nam_gay", "b": "bank",
          "mau": g["nen"], "de": de, "nen": phong}

    cau = [(x["chu"], 0 if x["ai"] == "a" else 1, x["cx"]) for x in thoai]
    # Chỉ số câu dẫn mà mỗi lượt thoại diễn — mô hình tự khai (xem luật 6 của `LENH_THOAI`).
    # Đây là thứ biến phép đặt thẻ từ ƯỚC LƯỢNG thành TRA CỨU.
    chi_dan = [int(x.get("i", k)) for k, x in enumerate(thoai)]
    kieuA, kieuB, ghiA, ghiB, ga, gb = KC.vai_va_giong(kk)
    # ── NGỮ ĐIỆU CHUYÊN GIA CHO VAI TRẢ LỜI  (anh giao, 7/9/2026) ────────────────────────
    # Anh: *"giọng điệu ngữ điệu phân tích chuyên gia chuyên nghiệp"*. Vai đã đúng người có
    # nghề, nhưng GIỌNG thì vẫn tra `GIONG_VAI[(gioi, tuoi)]` — tức một nhà thống kê 49 tuổi
    # đọc y hệt một người qua đường 49 tuổi. Người xem Mỹ nhận ra chất chuyên gia bằng CÁCH
    # NÓI trước khi kịp nghe nội dung: chậm hơn, trầm hơn, và đều — vì người biết chắc thì
    # không cần nói nhanh để giữ lượt.
    #
    # Đặt ở đây chứ không ở `GIONG_VAI`: bảng ấy khai theo GIỚI và TUỔI, không biết ai là
    # chuyên gia (§15.3 — nơi CHỌN và nơi biết BẢN SẮC phải là một). Và cộng vào nền chứ
    # không ghi đè, để `_dieu` vẫn nhấn nhá được theo câu hỏi / câu chốt bên trên nền ấy.
    def _uy(g, dr, dp):
        try:
            r = int(str(g[1]).replace("%", "").replace("+", "") or 0)
            h = int(str(g[2]).replace("Hz", "").replace("+", "") or 0)
        except Exception:
            return g
        r = max(-24, min(20, r + dr)); h = max(-26, min(26, h + dp))
        return (g[0], f"{r:+d}%", f"{h:+d}Hz")

    def _tran_uy(g):
        """Trần TUYỆT ĐỐI cho vai trả lời, đặt SAU phép trừ.

        Chỉ trừ đi một lượng thì nền cao vẫn ra cao: chuyên gia 31 tuổi tra vào giọng
        `("nu","tre")` nền `+12%/+14Hz`, trừ xong còn `+3%/+7Hz` — vẫn là giọng tươi, tức
        đúng chỗ hỏng vẫn nguyên (§12.4: nhất quán quanh một mốc SAI vẫn sai). Trần tuyệt
        đối thì mọi nền đều rơi xuống dưới ngưỡng nghe-ra-là-chuyên-gia.
        """
        try:
            r = int(str(g[1]).replace("%", "").replace("+", "") or 0)
            h = int(str(g[2]).replace("Hz", "").replace("+", "") or 0)
        except Exception:
            return g
        return (g[0], f"{min(r, 0):+d}%", f"{min(h, 0):+d}Hz")

    # ── ĐẢO NGƯỢC: CHUYÊN GIA NÓI NHANH RÕ, KHÔNG "ỒM ỒM SLOMOTION"  (anh, 10/9/2026) ────
    # Anh soi demo howbig HAI lần: *"giọng ồm ồm còn bị trễ như slomotion"*. Đo F0 audio
    # render = **119Hz** (giọng nam trầm), trong khi Aria thật = 198Hz — tức bản 7/9 dưới
    # đây đã HẠ giọng + CHẬM lại quá tay: `_uy(gb, -9, -7)` trừ 9% tốc độ + 7Hz, rồi
    # `_tran_uy` cắt cả rate lẫn pitch xuống ≤0. "Uy quyền" hoá ra "ồm ồm + rề rà".
    # Chuyên gia phân tích VIRAL kiểu Mỹ nói NHANH, RÕ, NĂNG LƯỢNG — không rề rà hạ giọng.
    # Nay CỘNG vào nền: nhanh hơn +8%, sáng nhẹ +2Hz, và BỎ `_tran_uy` (đừng cắt xuống ≤0).
    # `_uy` vẫn kẹp trần [-24,+20]% và [-26,+26]Hz nên không vọt quá.
    gb = _uy(gb, +8, +2)             # chuyên gia: nhanh rõ, sáng — KHÔNG hạ giọng nữa
    ga = _uy(ga, +5, +2)             # người hỏi (nếu có): cũng nhanh rõ
    # ── TIỀN TỐ `v11_`, KHÔNG PHẢI `pilot_`  (6/9/2026) ──────────────────────────────────
    # `day_kho.py --mau` mặc định quét `v3_* · v3L_* · v5_* · v5L_* · v9_*`. Tệp tên `pilot_*`
    # KHÔNG nằm trong danh sách ấy, nên bước đẩy sẽ quét, không thấy gì, in "0 video vào hàng
    # đợi" và **thoát 0** — dựng xong 18 kênh rồi mất trắng, mà lượt vẫn xanh.
    # Cổng `kiem_workflow` bắt được triệu chứng ("không gói tệp video nào") vì nó đòi tiền tố
    # `v<số>_`; đi nới cổng là chữa cái báo động thay vì chữa cái hỏng.
    # `v11_` = thế hệ COMIC GIẢI THÍCH, đứng sau `v9_` (giải thích) và `v10_` (phim).
    slug = f"v11L_{ma}_{idx:04d}" if chuong else f"v11_{ma}_{idx:04d}"
    rel = f"{slug}.mp3"
    try:
        dur, tu, moc = doc_hai_giong(cau, ga, gb, os.path.join(PUB, rel))
    except Exception as e:
        # KHÔNG bắt `_DungChon` ở đây: nó là control-flow của khâu CHỌN NỀN ở dưới, khai
        # tận dòng ~2460 nên tham chiếu nó ở đây ném `UnboundLocalError` CHE mất lỗi thật.
        # Đo lượt 34416264217: ffmpeg thiếu -> `FileNotFoundError`, nhưng log chỉ hiện
        # `UnboundLocalError: _DungChon` vì except sai bắt trước (§6 — copy nhầm từ khối dưới).
        print(f"   ❌ giọng đọc hỏng: {str(e)[:100]}"); return ""
    if not tu or len(moc) < len(cau):
        print("   ❌ thiếu mốc giọng đọc"); return ""

    luot = []
    for i, (chu, ai, cx) in enumerate(cau):
        cuoi = i == len(cau) - 1
        # ── NÉT MẶT PHẢI HỢP MỘT KÊNH GIẢI THÍCH, VÀ PHẢI LÀ TÊN ENGINE VẼ ĐƯỢC ─────────
        # Anh hỏi bộ này nghe/nhìn ra kênh phân tích hay kênh hài. Đo 18 tập thì ra kênh HÀI,
        # ở đúng hai chỗ:
        #
        #  · người NGHE lấy cảm xúc từ một vòng xoay CỐ ĐỊNH `i % 6` — mù nội dung — nên nó
        #    **tức giận 13% và buồn 10%** số ô. Nghe "một tiếng súng là 165 decibel" mà mặt
        #    người kia giận dữ thì khung nói một đằng lời nói một nẻo. Đó là máy phản ứng của
        #    bộ hài (ở đó cãi nhau là chất liệu); kênh giải thích thì phản ứng đúng là TÒ MÒ,
        #    CHÚ Ý, và BẤT NGỜ khi con số lớn.
        #
        #  · mô hình gửi xuống `ngac_nhien` (30%) và `ngoc_nhien` (5%) — cả hai KHÔNG nằm
        #    trong 8 tên `TenCamXuc` mà engine vẽ được, cũng không có trong bảng ngữ điệu.
        #    Nét mặt rơi về mặc định, giọng đọc phẳng lì. Chuẩn hoá tại NGUỒN thay vì vá ở hai
        #    nơi tiêu thụ (§11: một nguồn sự thật).
        _HOP = {"trung_tinh","vui","buon","so","tuc","bat_ngo","nghi_ngo","tu_tin"}
        _DOI = {"ngac_nhien": "bat_ngo", "ngoc_nhien": "bat_ngo", "to_mo": "tu_tin",
                "quan_tam": "tu_tin", "hoai_nghi": "nghi_ngo", "ngac nhien": "bat_ngo"}
        _cx = str(cx or "trung_tinh").strip().lower()
        _cx = _cx if _cx in _HOP else _DOI.get(_cx, "trung_tinh")
        # Chuyên gia KHÔNG kinh ngạc trước con số của chính mình. `bat_ngo` (+16Hz) và `vui`
        # (+10Hz) đọc lên thành giọng người dẫn game show, đúng thứ anh chê là "giống channel
        # funny". Cảm xúc cao trào là của người HỎI; người trả lời có hai nốt: chắc chắn và
        # trung tính. Chặn ở đây — nơi cảm xúc được chuẩn hoá — thay vì dặn thêm trong lệnh
        # dặn, vì một ràng buộc tuyệt đối phải làm cho KHÔNG THỂ vi phạm (§14.12).
        if ai == 1 and _cx in ("bat_ngo", "vui", "so", "tuc"):
            _cx = "tu_tin"
        # Người nghe phản ứng theo THỨ ĐANG NGHE, không theo số thứ tự lượt:
        _co_so = any(ch.isdigit() for ch in chu)
        _hoi = chu.strip().endswith("?")
        _kia = ("bat_ngo" if cuoi else            # cú chốt: sững ra
                "bat_ngo" if _co_so else          # vừa nghe một con số -> bất ngờ
                "tu_tin" if _hoi else             # vừa được hỏi -> sẵn sàng trả lời
                ["trung_tinh", "nghi_ngo", "tu_tin"][i % 3])
        luot.append({"s": moc[i][0], "e": moc[i][1], "ai": ai, "nar": chu, "camXuc": _cx,
                     "camXucKia": _kia,
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
        """Đường dẫn ảnh nền thứ i nếu có trên đĩa.

        Nhận CẢ số (nền của kênh này) lẫn chuỗi `"<kênh>_<số>"` (nền MƯỢN của kênh khác) —
        xem tầng mượn ở dưới. Kho nền là NƠI CHỐN, không phải tài sản riêng của kênh. WebP trước — kho mới nén WebP (−93% dung
        lượng), kho cũ còn JPEG hai chữ số, và cả hai phải cùng dùng được."""
        if isinstance(i, str):                       # nền mượn: "<kênh>_<số>"
            if i in _bo:
                return ""
            for _e in (".webp", ".jpg"):
                _t = f"comic_nen/{i}{_e}"
                if os.path.exists(os.path.join(PUB, _t)):
                    return _t
            return ""
        if f"{de}_{i:03d}" in _bo:
            return ""
        # `_{i:02d}.webp` thêm 6/9/2026: kho hai-chữ-số đời cũ vốn còn là JPEG 1024×1024 và
        # chiếm 67 MB cho 169 tệp — 43% dung lượng thư mục cho 10% số tệp. Nén sang WebP thì
        # phải nhận CẢ tên mới ở đây, nếu không thì 161 nền đang được dùng làm dự phòng biến
        # mất im lặng và tập rơi về nền vector (§15.12: đổi tên tệp mà quên chỗ ĐỌC).
        for ten in (f"comic_nen/{de}_{i:03d}.webp", f"comic_nen/{de}_{i:03d}.jpg",
                    f"comic_nen/{de}_{i:02d}.webp", f"comic_nen/{de}_{i:02d}.jpg"):
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
    class _DungChon(Exception):
        pass

    try:
        import nen_tag as NT
        _the = json.load(io.open(os.path.join(GOC, "nen_tag.json"), encoding="utf-8"))
        # ── HÌNH MẪU CHỌN NỀN, KHÔNG PHẢI PHÉP CHẤM THEO LỜI  (7/9/2026) ─────────────
        # Phép chấm theo lời xếp tập Kodak vào "corporate boardrooms" — cả kho có ĐÚNG MỘT
        # nền nhóm ấy, nên nó lùi về chọn cả kho và ra khu an ninh sân bay (anh soi ra).
        # Hình mẫu thì suy chắc chắn (8/8 đúng) và nói thẳng nơi chốn. Khi có hình mẫu, dùng
        # nó — và tìm trong CẢ KHO, vì nơi chốn không phải tài sản riêng của kênh.
        _tu_hm = ()
        try:
            import chu_de as _CD0
            _tu_hm = _CD0.nhom_nen_cua(DAO_CU_TAP)
        except Exception:
            pass
        if _tu_hm:
            _nhom_hop = [n for n in set(_the.values())
                         if any(t in str(n).lower() for t in _tu_hm)]
            _muon_hm = [k for k, v in _the.items() if v in _nhom_hop]
            _muon_hm = [k for k in _muon_hm if _co(k)]
            if len(_muon_hm) >= 3:
                print(f"   🎯 hình mẫu «{DAO_CU_TAP}» -> {len(_muon_hm)} nền "
                      f"({len(_nhom_hop)} nhóm) trong cả kho")
                co = _muon_hm[:80]
                raise _DungChon
        _nh = NT.nhom_tap(ma, tieu + ". " + " ".join(loi))
        _hop = [j for j in co if _the.get(f"{de}_{j:03d}") and
                _the.get(f"{de}_{j:03d}") == _nh] if _nh else []
        if len(_hop) >= 3:
            print(f"   🎯 nhóm nền «{_nh}» — {len(_hop)}/{len(co)} nền hợp nội dung")
            co = _hop
        elif _nh:
            # ── MƯỢN NỀN CỦA KÊNH KHÁC  (7/9/2026) ───────────────────────────────────
            # Bộ chọn cũ chỉ tìm trong nền của RIÊNG kênh. Đo: `therules` có 277 nền nhưng
            # dồn vào vài nhóm (phòng chờ 50 · hành lang cơ quan 47) và KHÔNG có nhóm nào về
            # nhiếp ảnh — nên tập về Kodak rơi về khu an ninh sân bay, đúng cái anh soi ra.
            # Cả kho có 5.118 nền / 176 nhóm.
            #
            # Kho nền là NƠI CHỐN, không phải tài sản riêng của kênh: một xưởng ảnh vẽ cho
            # kênh này thì kênh kia dùng cũng đúng. Mượn xong vẫn giữ luật chống trùng liền
            # kề vì lượt rải ở dưới không biết nền đến từ đâu.
            _muon = [k for k, v in _the.items() if v == _nh and not k.startswith(de + "_")]
            _muon = [k for k in _muon if _co(k)]
            if len(_muon) >= 3:
                print(f"   🎯 nhóm «{_nh}»: kênh này {len(_hop)} nền — MƯỢN {len(_muon)} nền cả kho")
                co = (_hop + _muon)[:60]
            else:
                print(f"   🎯 nhóm «{_nh}» chỉ có {len(_hop)}+{len(_muon)} nền — dùng cả kho")
    except _DungChon:
        # ĐƯỜNG THÀNH CÔNG, KHÔNG PHẢI LỖI (8/9/2026). `_DungChon` được NÉM CÓ CHỦ Ý ngay
        # sau khi hình mẫu đã chọn xong `co` — nó là câu `break` của khối try này. Nhưng
        # `except Exception` ở dưới bắt luôn, và một Exception không tham số cho `str(e)`
        # rỗng, nên log in ra `⚠ không đọc được nen_tag.json ()` ở 4/4 clip của bộ 125
        # trong khi việc chọn nền đã chạy ĐÚNG. Đúng §18.11: một dòng cảnh báo nói sai
        # nguyên nhân dẫn người đọc đi sửa thứ không hỏng — và em suýt đi sửa nó thật.
        pass
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
        # ── MỖI Ô MỘT PHÒNG KHI KHO ĐỦ  (anh soi ra, 7/9/2026) ─────────────────────────
        # Anh: *"nhiều clip ở nhiều channel sao trùng bối cảnh"*. Đo 18 tập: **189 ô nhưng chỉ
        # 69 nền khác nhau — 36%**, vì `i // 3` giữ nguyên một phòng cho ba ô liền.
        #
        # Con số 3 đúng ở thời của nó: kho mới có 2 nền/kênh nên đổi mỗi ô là quay vòng ngay
        # trên hai tấm. Nay mỗi kênh có 42–142 nền và lọc theo chủ đề còn 8–29 tấm — thừa cho
        # 9–16 ô. Hằng số sống lâu hơn ngữ cảnh sinh ra nó (§13.6).
        #
        # Chia theo thứ CÓ THẬT thay vì một hằng số: đủ nền thì mỗi ô một phòng, thiếu thì mới
        # gộp — và gộp đúng mức tối thiểu để không tấm nào phải dùng quá hai lần.
        # Bản đầu của bản sửa này chia `len(cau)/len(co)` rồi gộp theo trần — và nó cho ra
        # KÉM HƠN mức tối đa: 9 ô trên kho 8 nền ra 5 phòng thay vì 8. Với `buoc` nguyên tố
        # cùng nhau, dãy `(noi_idx + i*buoc) % len(co)` đi qua các phòng KHÁC NHAU cho tới khi
        # quay vòng, nên số phòng riêng = min(số ô, cỡ kho) — tức mỗi ô một phòng đã là tối ưu
        # và không phép gộp nào cải thiện được. Bỏ hẳn phép gộp.
        anh_nens = ([""] * len(cau) if NEN_CHI_ANH_THAT
                    else [_co(co[(noi_idx + i * buoc) % len(co)]) for i in range(len(cau))])
        # THỨ TỰ: ảnh THẬT trước, rồi mới vẽ bù chỗ còn trống. Bản đầu làm ngược và log tự
        # tố cáo: *"nền vẽ theo chủ thể: 8/8 nhịp"* đứng cạnh *"ảnh thật: 11"* — 11 ảnh thật
        # phủ hết 8 nhịp nên **cả 8 nền vừa vẽ bị thay ngay**, tức tiêu 8 ảnh hạn mức cho thứ
        # không ai nhìn thấy. Ở sản lượng 900 tập/ngày thì đó là 7.200 ảnh vứt đi mỗi ngày.
        # Hai dòng log nói ngược nhau là dấu hiệu quen (§14.8) — đọc kỹ thay vì mừng vì 8/8.
        # ── SHORT DÙNG LẠI NỀN CỦA BẢN DÀI  (§17.11) ────────────────────────────────
        # Không có khối này thì `bo_1_3` chỉ là "dựng bốn tập rồi bỏ CF ở ba tập sau" — ba
        # short rơi hẳn về kho nền chung, tức mất đúng thứ bộ 1:3 sinh ra để làm. Đo lượt
        # đầu: long vẽ 14 nhịp theo chủ thể, ba short vẽ 0 và dùng phòng ăn với phòng gym.
        if NEN_SAN:
            anh_nens = _nen_theo_loi(cau) or [NEN_SAN[i % len(NEN_SAN)] for i in range(len(cau))]
            _khop = sum(1 for i, x in enumerate(anh_nens)
                        if x != NEN_SAN[i % len(NEN_SAN)])
            print(f"   ♻️ dùng lại {len(NEN_SAN)} nền của bản dài (short không gọi CF)"
                  f" · {_khop}/{len(anh_nens)} nhịp ghép lại THEO CÂU")
        # ── SHORT ĐỪNG RẢI LẠI ẢNH THẬT  (anh: *"footage lặp đi lặp lại quá nhiều"*, 8/9) ──
        # Đo bộ 160: 15/28 khung nền của cả bộ là DÙNG LẠI (54%), và ba tấm ảnh thật xuất hiện
        # ở CẢ BỐN clip. Gốc không phải kho ảnh mỏng: `ANH_THAT` là biến chung, và MỌI clip —
        # cả long lẫn ba short — đều gọi `_chen_anh_that` với cùng danh sách ấy.
        #
        # Nhưng short vốn ĐÃ thừa hưởng nền của bản dài qua `_nen_theo_loi`, kể cả những tấm
        # ảnh thật bản dài đã đặt. Chạy lại lượt rải chỉ dán thêm đúng ba tấm ấy lần nữa —
        # tức nhân bản, không phải làm giàu. Bỏ lượt rải ở nhánh short là hết lặp mà không
        # mất tấm nào: cái gì bản dài đặt đúng chỗ thì short đã mang theo.
        # 9/9 — em từng đổi điều kiện này thành `if not NEN_SAN or NEN_CHI_ANH_THAT` vì tưởng
        # nó chặn lượt chèn ảnh thật. Chẩn đoán SAI: `NEN_SAN` vốn rỗng nên điều kiện cũ luôn
        # đúng. Và cổng `ảnh thật hiện trọn · không lặp cả bộ` bắt ngay: đổi thế làm short rải
        # LẠI ảnh thật, nên cùng ba tấm hiện ở cả bốn clip của một bộ. Giữ nguyên bản gốc.
        if not NEN_SAN:
            anh_nens = _chen_anh_that(anh_nens, ANH_THAT, cau)
        if not NEN_CHI_ANH_THAT:
            anh_nens = _nen_theo_tap(anh_nens, cau, CHU_THE_TAP, bo_qua=set(ANH_THAT))
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
    # ── GÁN THẺ SỐ: DUYỆT THEO LƯỢT, KHÔNG DUYỆT THEO THẺ  (vòng ba, 7/9/2026) ─────────
    # Ba vòng trước đều cùng một hình dạng: cầm một cái THẺ rồi đi TÌM lượt hợp với nó — bằng
    # vị trí tỉ lệ, rồi so chữ số, rồi so dạng đọc bằng chữ, rồi tra chỉ số mô hình khai. Mỗi
    # vòng nới thêm một ít và vẫn lệch, vì phép tìm luôn có thể chọn nhầm khi hai nhịp mang hai
    # con số gần nhau (`212,537` và `$213K` là CÙNG một số tiền, và mô hình đọc cả hai thành
    # "two hundred thirteen thousand").
    #
    # §16.3: sửa vòng thứ ba mà vẫn cùng họ lỗi thì thứ sai là CÁCH TIẾP CẬN. Lật ngược vòng
    # lặp — duyệt theo LƯỢT THOẠI, và mỗi lượt lấy thẻ của chính câu dẫn mà nó KHAI là đang
    # diễn. Không còn phép tìm nào để chọn nhầm: quan hệ lượt->câu dẫn do mô hình khai, quan hệ
    # câu dẫn->thẻ do `giai_thich` sinh. Hai quan hệ đã có, chỉ cần nối.
    #
    # Nhiều lượt cùng một câu dẫn (hỏi rồi đáp) thì thẻ về lượt CUỐI — thẻ thuộc câu trả lời,
    # không thuộc câu hỏi. Đó cũng là chỗ khung đứng lâu nhất.
    so_lieu = [None] * len(cau)
    import phim as P
    lop_cua = {}
    for _i, _n in enumerate(nhip):
        _l = P.lop_du_lieu(_n)
        if _l:
            lop_cua[_i] = _l
    # lượt CUỐI trong nhóm cùng khai một câu dẫn
    cuoi_cua = {}
    for t, c in enumerate(chi_dan):
        cuoi_cua[c] = t
    for t, c in enumerate(chi_dan):
        if cuoi_cua.get(c) == t and c in lop_cua:
            so_lieu[t] = lop_cua[c]
    # Câu dẫn có thẻ mà KHÔNG lượt nào khai (mô hình bỏ qua câu ấy): rải vào ô trống gần nhất
    # theo tỉ lệ, để không mất hẳn một con số khỏi hình.
    _da = {c for t, c in enumerate(chi_dan) if so_lieu[t]}
    for _i in sorted(set(lop_cua) - _da):
        j2 = min(len(cau) - 1, round(_i * (len(cau) - 1) / max(1, len(nhip) - 1)))
        while j2 < len(cau) and so_lieu[j2]:
            j2 += 1
        if j2 < len(cau):
            so_lieu[j2] = lop_cua[_i]
    # ── KHÔNG ĐỂ NHỊP NÀO NỀN TRẮNG  (anh, 9/9/2026) ──────────────────────────────────
    # Anh: *"gặn nhiều ảnh nền trắng trơn ko được phải là ảnh nền thực ko dùng nền trắng
    # trơn"*. Trước đó anh cho phép nền trống khi không có ảnh — nay chốt lại là KHÔNG.
    # Đo bộ 183: **10/13 nhịp trắng trơn**, vì chủ thể chỉ có 3 ảnh.
    #
    # Ba lối, và hai lối bị chính anh loại: sinh ảnh CF (*"ko ưu tiên dựng ảnh cf mới"*) và
    # để trống (*"ko dùng nền trắng trơn"*). Còn lại: DÙNG LẠI ảnh đã có.
    #
    # Lặp là thứ anh đã chê, nên luật chặt: không bao giờ đặt cùng một ảnh ở HAI NHỊP LIỀN
    # NHAU, và rải đều để mỗi ảnh cách lần xuất hiện trước càng xa càng tốt. Với 3 ảnh cho 13
    # nhịp thì mỗi ảnh hiện ~4 lần, cách nhau 3 nhịp — mắt đọc ra một bộ tư liệu quay vòng,
    # không đọc ra một khung đứng hình.
    # Đây là ĐÁNH ĐỔI CÓ Ý THỨC, không phải giải pháp đẹp: lời giải thật vẫn là chọn chủ thể
    # giàu ảnh, và nó nằm ở khâu mở hồ chứ không ở đây.
    # Dưới HAI ảnh khác nhau thì KHÔNG lấp: bộ 194 «Lehman Brothers» chỉ có một tấm, lấp đủ
    # 12 nhịp ra **11 cặp liền nhau trùng** — cả tập là một bức ảnh đứng yên, tệ hơn nền trống
    # mà anh muốn tránh. Lấp chỉ có nghĩa khi còn thứ để luân phiên.
    # ── LẤP TỪ CẢ HỒ ĐÃ LỌC, KHÔNG TỪ MẤY TẤM ĐÃ ĐẶT  (anh soi bộ 213, 9/9/2026) ──────
    # Anh: *"ảnh nền đâu"* · *"ko dùng đi dùng lại 1 footage"*. Cả hai là MỘT lỗi ở đây:
    # `_co` dựng từ `anh_nens` — tức chỉ những tấm mà phép ghép THEO NGHĨA đã đặt được.
    # Đo «Savannah River Plant»: hồ có **16 ảnh qua cổng**, phép ghép nghĩa đặt được 2, nên
    # khối này quay vòng đúng 2 tấm ấy cho 13 nhịp và bỏ phí 14 tấm còn lại.
    # Nay lấp từ `ANH_SACH` (hồ đã qua ba cổng), ưu tiên tấm CHƯA dùng: 16 ảnh cho 13 nhịp
    # thì mỗi nhịp một ảnh khác nhau, không một cặp nào lặp.
    # ── KHÔNG LẶP FOOTAGE: ẢNH RIÊNG > NỀN VẼ > (cuối cùng) LẶP  (anh nhắc 2 lần, 10/9) ──
    # Anh: *"tránh footage trùng dùng đi dùng lại"*. Trước đây beat hết ảnh riêng thì QUAY
    # VÒNG lặp ảnh. Nay: beat hết ảnh riêng mà CÓ nền vẽ (trục năm / thẻ số — có nghĩa, không
    # trắng trơn) thì ĐỂ TRỐNG cho engine vẽ code (`nenVe` chỉ vẽ khi ô ảnh trống). Chỉ lặp
    # ảnh khi beat vừa hết ảnh riêng VỪA không có nền vẽ — trường hợp bất khả, tối thiểu hoá.
    _ve_beat = _lop_ve(cau)                              # beat nào có nền vẽ được
    _da = [x for x in (anh_nens or []) if x]
    _con = [a for a in (ANH_SACH or []) if a not in _da]     # ảnh CHƯA dùng
    _co = list(dict.fromkeys(_da + _con))
    if _co:
        _j = 0
        for _i in range(len(anh_nens)):
            if anh_nens[_i]:
                continue
            _truoc = anh_nens[_i - 1] if _i > 0 else ""
            _uu = [a for a in _co if a not in anh_nens]      # CHỈ ảnh chưa dùng
            if not _uu:
                # hết ảnh riêng: có nền vẽ thì để trống cho code; không thì mới đành lặp
                if _ve_beat[_i] if _i < len(_ve_beat) else None:
                    continue
                _uu = _co                                     # bất khả -> lặp (last resort)
            _chon = ""
            for _k in range(len(_uu)):
                _x = _uu[(_j + _k) % len(_uu)]
                if _x != _truoc:
                    _chon = _x
                    break
            anh_nens[_i] = _chon or _uu[0]
            _j += 1
        # ── GỠ CẶP LIỀN TRÙNG TRÊN CẢ DÃY  (bộ 217, 9/9/2026) ────────────────────────
        # Anh: *"ko dùng đi dùng lại 1 footage"*. Vòng lấp phía trên tránh trùng liền kề,
        # nhưng nó BỎ QUA nhịp đã có nền — nên hai nhịp mà phép ghép-theo-nghĩa đặt CÙNG
        # một ảnh vẫn dính nhau. Đo bộ 217: 5 ảnh cho 13 nhịp, cặp 0-1 và 2-3 trùng.
        # Vá đúng một nhánh, để nguyên nhánh song song (§6) — lần thứ sáu trong phiên.
        # Đổi chỗ với một nhịp KHÔNG kề nó và mang ảnh khác; không tìm được thì để nguyên
        # (hồ chỉ có một ảnh thì mọi hoán vị đều trùng, và đoán bừa còn tệ hơn).
        for _i in range(1, len(anh_nens)):
            if not anh_nens[_i] or anh_nens[_i] != anh_nens[_i - 1]:
                continue
            for _j in range(len(anh_nens)):
                if abs(_j - _i) <= 1 or not anh_nens[_j] or anh_nens[_j] == anh_nens[_i]:
                    continue
                _t = anh_nens[_j]
                if _t == anh_nens[_i - 1]:
                    continue                                   # đổi vào lại thành trùng
                if _i + 1 < len(anh_nens) and _t == anh_nens[_i + 1]:
                    continue
                if _j > 0 and anh_nens[_i] == anh_nens[_j - 1]:
                    continue                                   # đẩy cái trùng sang chỗ khác
                if _j + 1 < len(anh_nens) and anh_nens[_i] == anh_nens[_j + 1]:
                    continue
                anh_nens[_i], anh_nens[_j] = anh_nens[_j], anh_nens[_i]
                break
        _lap = sum(1 for _i in range(1, len(anh_nens)) if anh_nens[_i] == anh_nens[_i - 1])
        _rieng = len(set(x for x in anh_nens if x))
        print(f"   🖼 lấp nền: {sum(1 for x in anh_nens if x)}/{len(anh_nens)} nhịp có ảnh "
              f"thật · {_rieng} ảnh KHÁC NHAU · {_lap} cặp liền nhau trùng")

    # ── CỔNG ẢNH NGHÈO — TRƯỚC RENDER, để `bo_1_3` tự chọn chủ thể khác  (10/9/2026) ────────
    # Đo LẠI `_rieng` ở đây (không dùng biến trong khối `if _co` phía trên): chủ thể 0 ảnh
    # dùng được (dayinlife «Benoxaprofen») không vào khối ấy, nên phải đếm độc lập ra 0.
    # Chỉ báo khi `bo_1_3` cho phép chọn lại (bản dài); short (dùng nền bản dài) và chạy lẻ
    # thì bỏ qua cổng này để không tự chặn mình.
    _rieng_that = len(set(x for x in anh_nens if x))
    if _CHON_LAI[0] and _rieng_that < _NGUONG_ANH:
        raise _NgheoAnh(_rieng_that, str(CHU_THE_TAP))

    _bo_lech, _bo_lap = loc_the_so(so_lieu, cau)

    # ── CẮT HÌNH THEO ĐỒNG HỒ, KHÔNG THEO CÂU  (anh, 9/9/2026) ────────────────────────
    # Anh: *"đảm bảo đa dạng chuyển footage sau 1,5–2,5s"*. Đo 23 nhịp: trung vị 5,21 giây,
    # 1/23 nhịp trong dải, dài nhất 11,8 giây.
    # Engine nay nhận `nenCat[i]` = danh sách ảnh PHỤ của nhịp i và đổi hình mỗi 2 giây
    # (xem `anhLuc` trong KichComic). Việc ở đây chỉ là RẢI ảnh dư vào đúng nhịp DÀI.
    #
    # Chỉ dùng ảnh THẬT đã có trong tay — không sinh thêm gì (*"ko ưu tiên dựng ảnh cf mới"*).
    # Ưu tiên nhịp dài nhất trước: một nhịp 11 giây cần 5 hình, một nhịp 2 giây cần 0.
    # Và KHÔNG cho một ảnh xuất hiện ở hai nhịp liền nhau — màn hình lặp là thứ anh đã chỉ ra.
    nen_cat = [[] for _ in cau]
    # `ANH_SACH` chứ KHÔNG phải `ANH_THAT`: ảnh phụ hiện full-bleed y như nền chính, nên
    # nó phải qua đúng ba cổng ấy. Dùng `ANH_THAT` là cách tấm logo lọt vào bộ 210.
    _du_anh = [a for a in (ANH_SACH or []) if a and a not in (anh_nens or [])]
    if _du_anh:
        def _dai_nhip(i: int) -> float:
            return (luot[i]["e"] - luot[i]["s"]) if i < len(luot) else 0.0
        _thu_tu = sorted(range(len(cau)), key=lambda i: -_dai_nhip(i))
        _k = 0
        for _i in _thu_tu:
            if _k >= len(_du_anh):
                break
            _dai = _dai_nhip(_i)
            _can = int(_dai // 2.0)                       # 2 giây một hình
            if _can <= 0:
                continue
            _lay = []
            for _ in range(min(_can, len(_du_anh) - _k)):
                _lay.append(_du_anh[_k]); _k += 1
            nen_cat[_i] = _lay
        _n_cat = sum(len(x) for x in nen_cat)
        if _n_cat:
            print(f"   ✂️ rải {_n_cat} ảnh phụ vào {sum(1 for x in nen_cat if x)} nhịp dài "
                  f"— hình đổi mỗi 2,0 giây")
    _ns = sum(1 for x in so_lieu if x)
    _ghi = f"   🔢 {_ns} lượt có lớp số liệu"
    if _bo_lech or _bo_lap:
        _ghi += f" (bỏ {_bo_lech} thẻ số KHÔNG được đọc lên · {_bo_lap} thẻ trùng số)"
    print(_ghi)
    # nhép miệng theo BIÊN ĐỘ: 30fps, đủ khung cho cả video (dùng dur).
    _bd = _bien_do(os.path.join(PUB, rel), 30, int(dur * 30) + 2)
    props = {
        "luot": luot, "tu": tu, "voMp3": rel, "nhac": KC.NHAC[de],
        "bienDo": _bd,
        "kieuA": kieuA, "kieuB": kieuB, "kieuTuyA": tuyA, "kieuTuyB": tuyB,
        "tieuDe": g["ten"], "handle": "@" + ma, "kenh": slug,
        "mau": g["chinh"], "mauPhu": g["phu"],
        "netMuc": 7, "cham": 9, "boGoc": 26, "tiLe": 0.60, "soTap": idx,
        "bongDuoi": False, "boKhung": 0, "chuNo": "HUH?",
        # Thẻ ảnh thật chỉ hiện ở BA NHỊP ĐẦU — chỗ người xem cần nhận ra ngay. Không
        # hiện suốt tập: một thẻ đứng nguyên từ đầu tới cuối đúng là thứ anh đã chê ở
        # biểu tượng máy ảnh ("sao nó gắn trên videos từ đầu tới cuối vậy").
        "anhChens": chon_the_anh(loi, CHU_THE_TAP, LOGO_TAP, ANH_THAT),
        "anhNens": anh_nens, "nenCat": nen_cat, "soLieu": so_lieu,
        # Tấm nào bị `cover` giấu mất quá 40% một chiều thì engine hiện TRỌN — xem
        # `_nen_can_tron`. Đo ở đây vì Python biết cỡ ảnh, engine thì không.
        "nenTron": _nen_can_tron(anh_nens, ngang=bool(chuong)),
        # Nhịp KHÔNG có ảnh thật -> lớp VẼ BẰNG CODE khớp chính câu ấy (xem `_lop_ve`).
        # Chỉ gán cho nhịp trống: có ảnh tư liệu thì ảnh luôn thắng.
        "nenVe": [None if (anh_nens[i] if i < len(anh_nens) else "") else v
                  for i, v in enumerate(_lop_ve(cau))],
        # Kênh GIẢI THÍCH tắt đồ nghề hài: thẻ hook thành dải sát đáy (không đè mặt), và bỏ
        # chữ nổ + cú rung ở câu chốt — engine bắn hiệu ứng punchline vào một câu kết trầm thì
        # khán giả đọc ra là hệ thống không hiểu nó đang kể gì.
        "hookDuoi": True, "haiHuoc": False,
        "noiIdx": noi_idx, "hook": (hook_phu or hook or tieu).upper()[:44],
        "anhNen": anh_nen, "sang": KC._sang_cua(anh_nen),
        "nhacVol": KC._am_nhac(KC.NHAC[de]),
        **({"motNguoi": True} if MOT_GIONG else {}),
        **({"daoCuTap": DAO_CU_TAP} if DAO_CU_TAP else {}),
        # Nét dựng riêng của kênh. Python QUYẾT rồi truyền KẾT QUẢ sang; engine chỉ đọc —
        # §15.3: nơi chọn và nơi biết bản sắc phải là một, đừng tính lại ở đầu kia.
        # ── NGƯỜI DẪN LUÔN GÓC TRÁI  (anh soi howbig, 10/9/2026) ────────────────────────
        # Anh: *"để nhân vật nhỏ góc trái, số liệu chart góc phải trên, không đè che nhau"*
        # (nhắc lại từ 9/9: *"góc trái ko có chart nhiều"*). GU_DUNG cũ để vài kênh "phai"/
        # "giua" như một trục đa dạng (§17.3), nhưng anh muốn NHẤT QUÁN trái để chart luôn
        # được ở phải không bị che. Ép "trai" cho vị trí; guKen/guNen vẫn giữ đa dạng.
        **(lambda g: {"guViTri": "trai", "guKen": g[1], "guNen": g[2]})(
            GU_DUNG.get(ma, ("trai", "vao", "moc"))),
    }
    pj = os.path.join(GOC, "out", f"{slug}.json")
    os.makedirs(os.path.dirname(pj), exist_ok=True)
    io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))

    out = os.path.join(GOC, "out", f"{slug}.mp4")
    r = subprocess.run(["npx", "remotion", "render", "src/index.ts",
                        "KichComicWide" if chuong else "KichComic", out,
                        # ── CHẤT LƯỢNG ĐẶT TƯỜNG MINH  (anh: "ko được HD sắc nét lắm") ──
                        # Remotion mặc định CRF 18 và đã cho 10,4 Mbps ở 1080×1920 — không tệ,
                        # nhưng đây là tệp NGUỒN đem lên YouTube, nơi nó còn bị nén LẦN NỮA.
                        # Nén hai lần thì mất mát cộng dồn, nên bản nguồn phải dư chất lượng:
                        # CRF 16 và ảnh khung 100% (mặc định 80 — mỗi khung đã mất một lần
                        # trước cả khi vào bộ mã hoá).
                        f"--props={pj}", "--gl=swiftshader", "--log=error",
                        "--crf=16", "--jpeg-quality=100"],
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
        # `long=bool(chuong)`, KHÔNG ghi cứng False (anh soi .tai.json bộ 220, 9/9/2026).
        # `chuong > 0` là bản dài `v11L_` (16:9), mà tham số `long` ghi cứng False làm
        # `viet_bai` gắn `#Shorts` + `loai:short` cho video DÀI — nó sẽ lên kệ Shorts sai
        # (§10.3: mỗi mảnh giao hàng phải đúng loại của nó). Cùng slug đã phân biệt bằng
        # `chuong`; tham số này phải theo cùng nguồn, không đặt tay một hằng.
        co = PD.giao_hang(slug, out, ma, g["ten"], tieu, hook, hook_phu,
                          dur, bool(chuong), nhip, CHU_THE_TAP)
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


def _lat_short(nhip: list, san: int = SAN_LUOT) -> list:
    """Cắt bộ nhịp của bản dài thành các đoạn cho short — mỗi đoạn ĐỦ DÀY.

    ── VÌ SAO KHÔNG PHẢI `nhip[c*b:(c+1)*b]`  (đo 8/9/2026) ─────────────────────────────
    Bản cũ tính `_b = max(3, len(nhip) // 3)` rồi cắt ba lát liền nhau. `max(3, …)` đọc lên
    như một SÀN, nhưng nó chỉ áp cho hai lát đầu: lát cuối nhận phần CÒN LẠI, và phần còn
    lại có thể mỏng hơn chính cái sàn ấy.

    Đo trên bộ thật: `len(nhip) = 8` -> `_b = 3` -> ba lát **3 · 3 · 2**. Hai nhịp không đủ
    cho cổng số, nên short thứ ba chết với `❌ không dựng được lời thoại` — **3/3 bộ liên
    tiếp (123 · 126 · 127) mất đúng clip thứ tư**, tức 25% sản lượng, đều đặn và im lặng.
    (Bản dài không dính vì `kich_ban(long=True)` nở 8 nhịp thành 32 bằng khối chương.)

    Nay ba cửa sổ đều dày `k = max(san, ceil(n/3))` và cửa sổ cuối NEO VÀO ĐUÔI, nên khi
    `n` không chia hết cho ba thì phần chồng nhau rơi vào GIỮA hai short chứ không rơi vào
    độ dày. Chồng một nhịp giữa hai chương liền nhau là chuyện thường của phép cắt chương;
    một short cụt thì không cứu được.

    Ít nhịp quá thì trả ÍT short hơn, không trả short trùng nhau: `n = 5` mà ép ba cửa sổ
    dày 3 sẽ cho hai lát y hệt — và hai video giống hệt nhau đúng là thứ luật YouTube nêu
    tên (§13.17). Thà ba clip thật còn hơn bốn clip có hai cái trùng.
    """
    n = len(nhip or [])
    if n < san:
        return []
    so = 3 if n >= san * 2 + 1 else (2 if n >= san + 2 else 1)
    # ── VÀ MỘT CÁI TRẦN, KHÔNG CHỈ MỘT CÁI SÀN  (8/9/2026) ──────────────────────────────
    # Sau khi cắt từ bộ nhịp ĐÃ NỞ của bản dài (32 nhịp), `ceil(n/3)` cho lát 11 nhịp và
    # short ra **58–68 giây**. Đúng luật, nhưng sai thể loại: một short là MỘT chương có cú
    # đấm, không phải một phần ba bộ phim. Đo: ~5,3 giây/panel -> trần 7 nhịp ≈ 37 giây.
    # Ba cửa sổ vì thế TRẢI ĐỀU khắp bản dài (đầu · giữa · cuối) thay vì phủ kín nó —
    # ba chương rời nhau đọc ra ba video, ba phần ba liền nhau đọc ra một video bị chia ba.
    k = min(TRAN_LAT, max(san, -(-n // 3)))
    dau = []
    for c in range(so):
        d = 0 if so == 1 else round(c * (n - k) / (so - 1))
        dau.append(max(0, min(d, n - k)))
    ra, da = [], set()
    for d in dau:
        khoa = (d, d + k)
        if khoa in da:
            continue
        da.add(khoa)
        ra.append(nhip[d:d + k])
    return ra


# ── SỐ CHƯƠNG CỦA BẢN DÀI: THÊM CHƯƠNG KHÔNG THÊM NỘI DUNG  (8/9/2026) ──────────────────
# Soi lưới bộ 130: khung 2 và khung 7 giống nhau TỪNG CHỮ, khung 3 và khung 8 cũng vậy, và
# hai khung còn tự khai ra bằng chữ *"repeats"* / *"again"*. Đo thẳng `kich_ban(long=True)`:
#
#     gốc  8 nhịp · chương 1 -> 13 nhịp · 13 câu KHÁC NHAU · lặp  0
#                  · chương 3 -> 32 nhịp · 14 câu KHÁC NHAU · lặp 18
#     gốc 20 nhịp · chương 1 -> 25 nhịp · 25 câu KHÁC NHAU · lặp  0
#                  · chương 3 -> 68 nhịp · 26 câu KHÁC NHAU · lặp 42
#
# Số câu KHÁC NHAU gần như KHÔNG ĐỔI theo số chương (13->14, 25->26): thêm chương chỉ kéo
# dài thời lượng bằng cách đọc lại. Bản 186 giây đang giao đi có **56% số lượt là câu lặp
# nguyên văn** — đúng lỗi "bốn cảnh lặp vòng" §15.15 đã ghi cho ODDS, quay lại ở đường mới.
#
# Nên số chương = 1. Bản dài ngắn đi (≈75 giây) và đó là SỰ THẬT về lượng tư liệu đang có;
# muốn dài hơn thì phải lấy thêm câu nhân quả cho mỗi chủ thể, không phải đọc lại câu cũ.
# §19.4: khi lời thoại rỗng, đi xem kịch bản có đủ sự thật không — đừng bơm cho dài.
# ── NỀN: CHỈ ẢNH THẬT LIÊN QUAN, KHÔNG THÌ ĐỂ TRỐNG  (anh chốt, 8/9/2026) ──────────────
# Anh: *"nền 100% là ảnh thật liên quan, ko dùng ảnh ko có nghĩa, hay nền trống"*.
#
# Lý do đo được, không phải sở thích: nền CF **không biết thời đại của câu chuyện**. Lưới bộ
# 162 («Hoosac Tunnel», chuyện năm 1866) có hai khung là VĂN PHÒNG KÍNH HIỆN ĐẠI — prompt
# không mang một thông tin niên đại nào, nên mô hình luôn vẽ hiện đại. Ảnh tư liệu thì đúng
# thời tự nhiên, vì nó chính là tư liệu của thời ấy.
#
# Một khung trống sạch không nói sai điều gì; một căn phòng vô can thì nói sai. Và bỏ hẳn
# đường vẽ nền CF cắt gần trọn hạn mức ảnh của mỗi tập — thứ anh đã dặn tiết kiệm.
NEN_CHI_ANH_THAT = True

CHUONG_KHONG_LAP = 1

# ── ĐỒ VẬT THEO HÌNH MẪU, KHÔNG THEO CÂU  (8/9/2026) ────────────────────────────────────
# Bỏ danh sách danh từ lấy từ câu dẫn thì nền hết chữ nguệch ngoạc (bộ 133 · 134 sạch 8/8 và
# 6/6 khung), nhưng nghèo hẳn đi: đo lưới bộ 133 có **6/8 khung là hành lang hoặc tường
# trơn**. Anh dặn "nền liên quan videos", nên trống là hỏng đúng trục anh quan tâm.
#
# Chỗ hở của bản trước nằm ở NGUỒN chữ, không ở việc có chi tiết: chữ lấy từ CÂU thì mang
# theo tên riêng và động từ, và mô hình đem viết lên tường. Đồ vật do MÌNH soạn thì không
# bao giờ là tên riêng, và toàn là vật THẤY ĐƯỢC — thứ mô hình khuếch tán vẽ giỏi nhất thay
# vì viết ra (§12.7: nó hỏng ở CHUỖI, không hỏng ở đồ vật).
#
# Mười bốn hình mẫu, mỗi cái sáu vật, xoay hai vật một nhịp theo `i` — nên hai nhịp liền
# nhau khác nhau ở thứ người xem NHÌN THẤY (§14.9), mà không nhịp nào mang chữ của câu.
# ── ĐỒ VẬT KHÔNG ĐƯỢC MANG CHỮ  (8/9/2026) ─────────────────────────────────────────────
# Soi lưới bộ 152 («Credit Suisse»): 2/6 khung có BIỂN CHỮ nguệch ngoạc treo trên tường —
# đúng thứ người xem đọc ra "nghiệp dư" trong nửa giây (§12.12), và đúng chỗ FLUX hỏng nặng
# nhất (§12.7: chuỗi dài đúng 0/2 · §13.20: chữ trong khung là chỗ mô hình hỏng nhất).
#
# Gốc KHÔNG phải mô hình tự bịa — bảng này ĐẶT HÀNG chữ. Bốn mục, và phải đọc tay cả bảng
# mới thấy: `signage rails` (biển chỉ dẫn) · `quote boards` (bảng yết giá) · `price rails`
# (nhãn giá) · `card catalogues` (phiếu mục lục). Regex đầu của em chỉ bắt `signage` rồi bỏ
# sót ba cái kia, vì không cái nào chứa một từ nghĩa là "chữ" — đúng §13.20: *một danh sách
# chuỗi con không bắt được ngôn ngữ*. Nên cổng canh liệt kê VẬT, không liệt kê từ "chữ".
#
# THAY chứ không xoá (§17.6): xoá đồ vật thì nền trống, mà trống là lỗi ở đúng trục anh quan
# tâm. Vật thay giữ nguyên vai bố cục — một dải ngang, một mặt phẳng đứng, một khối tủ.
_VAT_HINH_MAU = {
    "may_anh":     ("enlargers", "developing trays", "film reels", "tripods",
                    "print racks", "light boxes",
                    "contact sheets pegged on a line"),
    "bang_video":  ("tape decks", "monitor walls", "cable spools", "mixing desks",
                    "rack units", "cue lights",
                    "a patch bay with looped leads"),
    "may_bay":     ("jet bridges", "baggage carts", "boarding gates", "tow tractors",
                    "wing sections", "trolley bins",
                    "a stack of chocked wheel blocks"),
    "ten_lua":     ("launch gantries", "fuel lines", "console rows", "test stands",
                    "cable trays", "blast shields",
                    "a coiled umbilical hose"),
    "dien_thoai":  ("assembly benches", "component trays", "solder stations",
                    "conveyor belts", "test jigs", "parts bins",
                    "a tray of screened panels"),
    "may_tinh":    ("server racks", "patch panels", "desk terminals", "cable bundles",
                    "cooling ducts", "tape drives",
                    "a coiled floor cable ramp"),
    "cua_hang":    ("shelf rows", "checkout counters", "stock trolleys", "shelf edge rails",
                    "basket stacks", "window displays",
                    "a folded stack of flat cartons"),
    "xe":          ("lifts and ramps", "tool chests", "tyre stacks", "engine hoists",
                    "parts shelves", "oil drums",
                    "a rolling creeper under a bench"),
    "lo_phan_ung": ("turbine halls", "pipe runs", "control desks", "valve banks",
                    "gauge panels", "walkway rails",
                    "a wheeled inspection ladder"),
    "ong_nghiem":  ("fume hoods", "sample racks", "centrifuges", "glass cabinets",
                    "bench sinks", "sterile trays",
                    "a drying rack of glassware"),
    "tau_thuy":    ("gantry cranes", "container stacks", "mooring bollards", "loading ramps",
                    "cargo nets", "dock ladders",
                    "a coil of thick mooring rope"),
    "toa_nha":     ("reception desks", "lift banks", "glass partitions", "planter rows",
                    "seating clusters", "handrail posts",
                    "a floor polisher parked by a column"),
    "dong_xu":     ("teller counters", "frosted partition screens", "desk terminals", "vault doors",
                    "queue rails", "document trays",
                    "a wheeled cash cart with its lid up"),
    "sach":        ("shelf stacks", "reading tables", "wooden drawer banks", "print presses",
                    "paper reams", "desk lamps",
                    "a book trolley left mid-aisle"),
}

# ── NỀN PHẢI KỂ ĐÚNG CHUYỆN ĐANG NÓI  (anh, 8/9/2026) ───────────────────────────────────
# Anh: *"sao 1 nền duy nhất thế này đâu phải nền hợp bối cảnh"* rồi *"ảnh nền phải thể hiện
# được vấn đề được nói tới trong clip, nhìn cái nhận ra ngay, ko chung chung"*.
#
# Anh đúng, và đo được: bản trước cho 13 nhịp ra 13 TỆP khác nhau — phép đo cũ nói "không
# lặp" — nhưng khác biệt trung bình chỉ **20,7/255**, cặp khác nhất **36,0/255**. Mười ba
# tấm nằm trong một dải rất hẹp, mắt đọc ra MỘT căn phòng. Đếm tệp là đo sai đại lượng
# (§13.5): thứ người xem cảm được là "hai khung liền nhau có khác nhau không".
#
# Gốc: sau khi bỏ danh từ lấy từ câu (để chặn chữ nguệch ngoạc), thứ duy nhất còn đổi theo
# nhịp là 3 chữ nơi chốn của hình mẫu — `dong_xu` -> bank/office/trading, cùng một thế giới.
# Nền đi theo CHỦ THỂ, không đi theo CÂU.
#
# Cách chữa giữ được cả hai ràng buộc: câu chỉ dùng để CHỌN khái niệm; chữ đi vào prompt là
# chữ EM soạn. Nên không tên riêng nào lọt vào khung (§13.20), mà cảnh vẫn bám nội dung.
#
# Và tả SỰ VIỆC, không tả CĂN PHÒNG. "a courtroom" vẫn là chung chung; "a judge's gavel
# resting on a stack of bound case files" thì nhìn phát biết đang nói chuyện kiện tụng. Mô
# hình khuếch tán vẽ vật thể và tình huống giỏi hơn hẳn vẽ một danh từ nơi chốn.
_KHAI_NIEM = (
    (r"\b(court|lawsuit|sued?|suing|litigat|judge|verdict|trial|settlement|"
     r"proceedings?|recovery|restitution|asset\s+recovery)\w*",
     "a wooden gavel resting on a tall stack of bound case files"),
    (r"\b(bankrupt|insolven|liquidat|chapter\s*11|receivership|wound\s+up)\w*",
     "a cleared office with cardboard archive boxes stacked by an empty desk"),
    (r"\b(merger|merged|acquisition|acquired|takeover|buyout)\w*",
     "two long boardroom tables pushed together, one chair left between them"),
    (r"\b(election|minister|parliament|government|regulator|ministry|senate|"
     r"congress|lawmaker|legislat|hearing|testimon)\w*",
     "a row of microphones on an empty podium under bright lights"),
    (r"\b(shares?|stock|market|trading|listed|ipo|shareholder)\w*",
     "a wall of green and red indicator lights above an empty trading desk"),
    (r"\b(audit|investigat|inquiry|probe|forensic|whistleblow)\w*",
     "an open ledger under a desk lamp beside a magnifier and paper clips"),
    (r"\b(loan|debt|bond|borrow|repaid|interest|creditor|default)\w*",
     "banded bundles of banknotes on a counter beside a locked cash drawer"),
    (r"\b(transfer|wired?|account|deposit|offshore|laundering|funds?)\w*",
     "a vault door standing open with empty numbered deposit boxes inside"),
    (r"\b(fraud|scam|scandal|bribe|corrupt|embezzl|kickback)\w*",
     "a briefcase open on a desk with unmarked envelopes spilling out"),
    (r"\b(fine|penalt|sanction|banned|revoked|licen[cs]e|complian)\w*",
     "a rubber stamp pressed onto a thick bound folder on a bare desk"),
    (r"\b(layoff|redundan|fired|staff|employee|workers?|union)\w*",
     "rows of emptied desks with chairs pushed in and cables coiled on top"),
    (r"\b(factory|factories|manufactur\w*|production|assembly|plant|plants|machinery)\b",
     "a stopped assembly line with half-built units still clamped in place"),
    (r"\b(recall|defect|faulty|malfunction|safety|inspect)\w*",
     "a workbench with a dismantled part laid out beside measuring tools"),
    (r"\b(airline|airlines|flight|flights|aircraft|airport|airports|fleet|fleets|boeing|airbus|terminal|"
     r"leased?|ordered|seats?|flew|jets?|planes?)\w*",
     "an empty boarding gate with a closed shutter and idle jet bridge"),
    (r"\b(ship|ships|shipping|shipment|shipments|vessel|port|ports|seaport|harbour|harbor|cargo|freight|container|containers)\b",
     "stacked shipping containers beside a still gantry crane at dusk"),
    (r"\b(rail|rails|railway|railways|railroad|train|trains|locomotive|track|tracks|station|stations|metro)\b",
     "an empty platform with a signal light and rails curving into the dark"),
    (r"\b(store|retail|shop|customers?|sales|chain|outlet)\w*",
     "long shelf rows stripped bare with empty baskets stacked at the end"),
    (r"\b(film|camera|photo|print|studio|broadcast|television|tape)\w*",
     "a cutting bench with film reels, a loupe and strips of negatives"),
    (r"\b(phone|mobile|handset|device|electronic|circuit|chip)\w*",
     "a repair bench with an opened handset, tweezers and tiny screws"),
    (r"\b(software|internet|website|websites|server|servers|data|computer|computers|online|app|apps)\b",
     "a server aisle with one rack door open and patch cables hanging"),
    (r"\b(drug|medicine|patient|clinical|hospital|vaccine|trial\s+result)\w*",
     "a laboratory bench with sample vials in a rack and gloves laid beside"),
    (r"\b(oil|gas|refiner|pipeline|drilling|energy|reactor|turbine)\w*",
     "a pipe run and valve wheels along a walkway inside a turbine hall"),
    (r"\b(build|construct|property|estate|tower|developer|site)\w*",
     "an unfinished concrete floor with scaffolding and a stalled hoist"),
    (r"\b(bank|banks|banking|banker|bankers|deposit|deposits|branch|branches|teller|tellers|central\s+bank|reserve|reserves)\b",
     "a row of closed teller windows with queue posts and no rope between"),
    (r"\b(founder|founders|chairman|executive|executives|chief|board|boards|boardroom|resign|resigned|stepped\s+down)\b",
     "one empty chair at the head of a long polished table"),
    (r"\b(protest|riot|strike|boycott|public\s+anger|outrage)\w*",
     "a barricade rail on an empty street with scattered paper on the ground"),
    (r"\b(ceased|closed|shut|shutdown|halted|grounded|final|last\s+day|wound\s+down)\b",
     "a rolled-down metal shutter with a chain and padlock at floor level"),
    (r"\b(profit|loss|losses|revenue|earnings|unprofitable|margin|cash\s+flow)\w*",
     "a desk calculator beside long columns of figures on ruled paper"),
    (r"\b(billion|million|thousand|dollars?|us\$|amount|total)\w*",
     "a counting tray of banded notes beside a closed ledger on a wide desk"),
    (r"\b(route|expansion|expanded|network|service\s+to|opened|launch)\w*",
     "a wall map with coloured pins and taut threads stretched between them"),
    (r"\b(price|prices|pricing|fare|fares|ticket|tickets|fee|fees|charge|charges|charged|discount|discounts|cheap|cheaper)\b",
     "a stack of blank cardboard tags and a punch tool on a bare counter"),
    (r"\b(contract|agreement|signed|deal|clause|terms)\w*",
     "a fountain pen laid across a thick unsigned document on a desk"),
    # ── BỐN KHÁI NIỆM THÊM SAU KHI ĐỌC TAY 17 CÂU TRƯỢT (§13.21) ─────────────────────
    # 11/17 câu trượt là câu DẪN (*"let us work it out together"*) — không có gì cụ thể để
    # vẽ, và ép một cảnh cụ thể vào đó là đúng lỗi §17.5. Nền trung tính ở đấy là ĐÚNG.
    # Sáu câu còn lại mới là lỗ thật, và đây là chúng.
    (r"\b(rebrand|renamed?|identity|new\s+name|became\s+known)\w*",
     "a painted wall panel half stripped back, showing an older coat beneath"),
    (r"\b(vanish|disappear|demise|gone|no\s+longer|wiped\s+out|collapse)\w*",
     "a bare hook and a clean unfaded rectangle on a wall where something hung"),
    (r"\b(sec|faa|ftc|fda|doj|commission|commissions|authority|authorities|watchdog|watchdogs|oversight)\b",
     "a counter window with a bell, a date stamp and a wire tray of forms"),
    (r"\b(founded|origin|origins|original|began|early\s+years|decades?|history|era|eras)\b",
     "a wooden drawer of index cards pulled open under a desk lamp"),
    (r"\b(research|report|analyst|publish|rating|coverage|review)\w*",
     "a bound report open flat beside a pencil and a stack of loose pages"),
    (r"\b(exit|withdrew|withdraw|pulled\s+out|sold\s+its|stake|divest|left\s+the)\w*",
     "a coat missing from a rack of empty hangers by a door"),
    # ── BA KHÁI NIỆM RÚT TỪ CHÍNH CÂU TRƯỢT CỦA BỘ 143 (§13.21 — đọc tay trước khi nới) ──
    (r"\b(leak|leaks|leaked|internal\s+document|memo|memos|whistle|disclos\w*)\b",
     "a manila folder half open with loose pages sliding out onto a desk"),
    (r"\b(feature|product|rollout|launch\w*\s+of|version|update|platform|app\b)\w*",
     "a pinboard of paper wireframe sketches with one card pulled aside"),
    (r"\b(moderat|harmful|radicali|misinformation|content|amplif|algorithm)\w*",
     "a queue of identical sealed envelopes on a conveyor with one tipped over"),
    (r"\b(sold|selling|holdings|stake\s+in|divested|liquidated\s+its)\w*",
     "an auction paddle resting on a cleared table beside numbered lot tags"),
    (r"\b(value|worth|plunged|collapsed\s+to|lost\s+\d|percent|fell\s+by)\w*",
     "a wall chart with one line dropping steeply to the floor line"),
    (r"\b(operated|service\s+from|carrier|routes?\s+between|flew\s+between)\w*",
     "a departure board frame with empty slats and a clock above it"),
)

# ── CÂU DẪN KHÔNG CÓ GÌ CỤ THỂ ĐỂ VẼ — NHƯNG VẪN PHẢI TRÔNG KHÁC NHAU  (8/9/2026) ──────
# Đo bộ 137 (bản đầu của bảng khái niệm): khác biệt TB 25,6 — qua sàn 24 nhưng còn xa mức
# đường cũ (33,3). Truy ra: 13 nhịp chỉ khớp 5 khái niệm, **6 nhịp rơi về nền chung**, và
# sáu nhịp ấy dùng đúng MỘT cảnh xoay qua 5 chữ nơi chốn — chúng kéo cả chỉ số xuống.
#
# Ép một cảnh cụ thể vào câu dẫn là sai (§17.5, khung nói một đằng lời nói một nẻo). Nhưng
# "không cụ thể" KHÔNG có nghĩa là "giống nhau": bảy BỐ CỤC trung tính của cùng thế giới —
# cầu thang, hành lang kính, sảnh thang máy, ô cửa sổ, đảo bàn, lan can lửng, lối ra — nhìn
# ra bảy khung khác hẳn nhau mà không cãi bất kỳ câu nào. Bảy để `lcm(8,7) = 56 > 32` (§13.13).
_NEN_TRUNG_TINH = {
    "dong_xu":     ("a stairwell landing with a metal handrail", "a glass-walled corridor",
                    "a lift lobby with brushed doors", "a tall window bay with blinds half open",
                    "an island of desks seen from one end", "a mezzanine rail over an open floor",
                    "a doorway onto a bare vestibule"),
    "may_bay":     ("a jetway corridor curving away", "a window wall onto an empty apron",
                    "a stair truck parked beside a fence", "a baggage belt bend",
                    "a covered walkway between piers", "a rooftop rail over a taxiway",
                    "a service door onto the ramp"),
    "may_tinh":    ("a cable riser between two floors", "a glass partition beside a hot aisle",
                    "a lift lobby with brushed doors", "a window bay above a raised floor",
                    "an island of workbenches", "a mezzanine rail over a machine room",
                    "a doorway onto a cable vault"),
    "cua_hang":    ("a stockroom stair with a rail", "a glass shopfront from inside",
                    "a service corridor behind the tills", "a window bay over the street",
                    "an island display seen end on", "a mezzanine rail above the floor",
                    "a loading door onto a bare yard"),
    "may_anh":     ("a darkroom stair with a red rail", "a glazed studio partition",
                    "a corridor of numbered doors", "a north-facing window bay",
                    "an island bench seen end on", "a gallery rail above a set",
                    "a doorway onto a props store"),
    "bang_video":  ("a stair to a control gallery", "a glazed booth partition",
                    "a corridor of cable ports", "a window bay above a studio floor",
                    "an island of editing benches", "a rail over a scenery dock",
                    "a doorway onto a tape store"),
    "ten_lua":     ("a gantry stair with open treads", "a blast-glass observation panel",
                    "a service corridor of conduit", "a window bay onto a bare pad",
                    "an island of consoles", "a rail above an assembly bay",
                    "a doorway onto a clean corridor"),
    "dien_thoai":  ("a stair between production floors", "a glazed line partition",
                    "a corridor of parts lockers", "a window bay above the line",
                    "an island of test benches", "a rail over a packing floor",
                    "a doorway onto a component store"),
    "xe":          ("a stair to a parts mezzanine", "a glazed workshop office",
                    "a corridor of roller doors", "a window bay above the bays",
                    "an island bench between two lifts", "a rail over a service pit",
                    "a doorway onto an empty forecourt"),
    "lo_phan_ung": ("a steel stair between decks", "a glazed control-room panel",
                    "a corridor of pipe runs", "a window bay over a turbine floor",
                    "an island of gauge panels", "a walkway rail above the hall",
                    "a doorway onto a plant corridor"),
    "ong_nghiem":  ("a stair with a wipe-clean rail", "a glazed laboratory partition",
                    "a corridor of numbered doors", "a window bay above a bench run",
                    "an island bench with services", "a rail over a preparation room",
                    "a doorway onto a sterile lobby"),
    "tau_thuy":    ("a quayside stair with a rail", "a glazed harbour office",
                    "a corridor between warehouse bays", "a window bay onto still water",
                    "an island of mooring bollards", "a rail along a loading deck",
                    "a doorway onto an empty wharf"),
    "toa_nha":     ("a stairwell landing with a handrail", "a glass-walled corridor",
                    "a lift lobby with brushed doors", "a tall window bay",
                    "an island of seating", "a mezzanine rail over an atrium",
                    "a doorway onto a bare vestibule"),
    "sach":        ("a stair between shelf decks", "a glazed reading-room partition",
                    "a corridor of closed stacks", "a window bay above long tables",
                    "an island of reading desks", "a gallery rail over the floor",
                    "a doorway onto a binding room"),
}

_DA_TIEU: set = set()


def _tieu_short(tieu_dai: str, lat: list, c: int) -> str:
    """Tiêu đề của MỘT short = mệnh đề của CHÍNH đoạn ấy, không phải tiêu đề bản dài.

    Đo trên bộ 125: ba short mang tiêu đề YouTube GIỐNG NHAU TỪNG KÝ TỰ —
    *"1973 Rome airport attacks and hijacking came back. You missed it."* ×3. Hai cái hại,
    và cái thứ hai nặng hơn:
      · ba video của cùng một kênh cạnh tranh nhau trong tìm kiếm, không cái nào thắng;
      · đó đúng trục *"kịch bản/khuôn chuyện giống hệt nhau"* mà luật YouTube nêu tên
        (§13.17) — và nó giống hệt nhau ở chỗ người xem NHÌN THẤY ĐẦU TIÊN.
    §17.11 đã viết sẵn câu trả lời: *"Tiêu đề = chính TÊN CHƯƠNG"*. Ở đây không có tên
    chương, nhưng mỗi short LÀ một chương, nên tên nó là mệnh đề mở của chính nó.

    Rơi về tiêu đề bản dài kèm số thứ tự khi đoạn không có câu nào đọc được — thà một hậu
    tố xấu còn hơn ba tiêu đề trùng nhau (§15.6: không biết thì nói ra, đừng đoán).
    """
    for n in (lat or []):
        cau = str((n or {}).get("loi") or "").strip()
        cau = re.split(r"(?<=[.!?])\s", cau)[0].strip(" .!?")
        # bỏ câu dẫn quá ngắn (một con số, một tiếng đệm) và câu quá dài để làm tiêu đề
        if 18 <= len(cau) <= 92 and len(cau.split()) >= 4:
            cau = cau[0].upper() + cau[1:]
            # ── KHÁC NHAU KHÔNG PHÂN BIỆT HOA THƯỜNG  (8/9/2026) ────────────────────────
            # Bộ 129 ra hai tiêu đề `1992 INDIAN STOCK MARKET SCAM CAME BACK` và
            # `1992 Indian stock market scam came back` — với người xem là MỘT tiêu đề,
            # với `set()` là hai. Phép so phải đo thứ người xem cảm được (§18.11).
            if cau.lower() not in _DA_TIEU:
                _DA_TIEU.add(cau.lower())
                return cau
    return f"{tieu_dai} — {c + 1}"


# ── SỔ JOB: HAI ĐƯỜNG DỰNG NÀY CHƯA BAO GIỜ GHI  (8/9/2026) ────────────────────────────
# Anh soi dashboard: `Hôm nay 0 · Video trong kho 0 · Đang chạy 0 · Lỗi 0` và hỏi *"sao trên
# site ko ghi nhận 1 cái gì"*. Đi tìm thì `pilot_hai` và `phim` KHÔNG gọi `new_job` /
# `update_job` một lần nào — chúng dựng video, đẩy Drive, mà không để lại bản ghi.
#
# Nên dashboard không mù vì lỗi hiển thị: nó KHÔNG CÓ GÌ ĐỂ ĐỌC. Và tệ hơn, ô ❌ đếm bản ghi
# `failed`, nên một lượt chết trước khi kịp tạo bản ghi thì không có mặt ở cả ba ô — đúng
# §10.1 (*"hỏng mà không để lại tệp nào thì trông y hệt chưa từng chạy"*), cộng một tầng nữa:
# nó còn không báo lỗi.
#
# NGÂN SÁCH GHI: một bản ghi cho MỘT BỘ (không phải mỗi clip) — mở lúc bắt đầu, chốt lúc kết
# thúc. 18 kênh × 4 mốc cron = 72 bộ/ngày ≈ 144 lượt ghi, so với trần free 20.000 (§13.7 —
# "số nhỏ" không phải bảo vệ, nên tính ra thay vì cảm giác).
#
# HỎNG MỀM Ở MỌI NHÁNH (§13.3): sổ hỏng thì video vẫn phải ra. Không bao giờ để một lượt ghi
# Firestore giết một bộ đã tốn ảnh để dựng.
def _mo_so(ma: str, idx: int) -> str:
    try:
        import firestore_bridge as FB
        owner = os.environ.get("OWNER_UID") or ""
        if not owner:
            return ""
        return FB.new_job(owner, ma, vtype="bo", pver=f"v11:{idx}") or ""
    except Exception as e:
        print(f"   ⚠ không mở được bản ghi job ({str(e)[:44]}) — vẫn dựng bình thường")
        return ""


def _chot_so(job: str, trang_thai: str, **them) -> None:
    if not job:
        return
    try:
        import firestore_bridge as FB
        FB.update_job(job, status=trang_thai, **them)
    except Exception as e:
        print(f"   ⚠ không chốt được bản ghi job ({str(e)[:44]})")


# ── THẺ ẢNH THẬT CHỌN THEO TỪNG NHỊP  (anh, 8/9/2026) ──────────────────────────────────
# Anh: *"nhớ phù hợp đúng kịch bản nội dung; nào không có thì dùng ảnh liên quan thực tế nếu
# không có logo; dùng vừa logo vừa ảnh thực tế sao cho phù hợp"*.
#
# Bản trước gắn MỘT ảnh cố định cho ba nhịp đầu — sai đúng điều anh vừa dặn: nhịp 3 có thể
# đang nói về một chiếc máy bay mà thẻ vẫn là logo, hoặc ngược lại.
#
# Ba luật, theo đúng thứ tự ưu tiên:
#   1. Nhịp GỌI TÊN chủ thể  -> LOGO. Đó là lúc người xem cần buộc cái tên vào một hình.
#   2. Nhịp nói về vật cụ thể -> ẢNH THẬT (trụ sở, máy bay, sản phẩm), xoay vòng để không lặp.
#   3. Không hợp cái nào      -> ĐỂ TRỐNG. Thà không có thẻ còn hơn dán một thẻ nói chuyện khác
#      — đúng lỗi §17.5 mà em đã trả giá: khung nói một đằng, lời nói một nẻo.
#
# Và TRẦN 40% số nhịp: thẻ hiện suốt tập thì mắt thôi nhìn nó, lại che nền vừa vẽ. Anh đã chê
# đúng chuyện này ở biểu tượng máy ảnh ("sao nó gắn trên videos từ đầu tới cuối vậy").
def chon_the_anh(loi: list, chu_the: str, logo: str, anh_that: list) -> list:
    ten = [w.lower() for w in re.findall(r"[A-Za-z0-9][\w&.-]{2,}", thuc_the(chu_the) or chu_the)]
    ten = [w for w in ten if w not in _BO_NEN]
    ra = [""] * len(loi)
    if not (logo or anh_that):
        return ra
    tran = max(1, int(len(loi) * 0.40))
    kho = list(anh_that or [])
    dung = 0
    for i, l in enumerate(loi):
        if dung >= tran:
            break
        t = str(l or "").lower()
        goi_ten = any(w in t for w in ten) if ten else False
        co_vat = bool(next((1 for r, _ in _KHAI_NIEM if re.search(r, t)), 0))
        if goi_ten and logo:
            ra[i] = logo
        elif co_vat and kho:
            ra[i] = kho.pop(0)
        else:
            continue
        dung += 1
    # Nhịp mở phải có thứ nhận ra ngay: nếu chưa nhịp nào được gắn thì ép nhịp 0.
    if logo and not any(ra):
        ra[0] = logo
    return ra


def bo_1_3(ma: str, idx: int, chuong: int = CHUONG_KHONG_LAP) -> int:
    """MỘT BỘ = 1 bản dài + 3 short, DÙNG CHUNG một bộ ảnh VÀ một chủ thể. Trả số clip.

    ── VÌ SAO ĐÂY LÀ MẶC ĐỊNH  (anh dặn ghi nhớ, 7/9/2026) ───────────────────────────────
    Thời gian render dư ~8 lần, hạn mức ảnh CF là nút thắt. Dùng lại một bộ ảnh cho bốn clip
    là ×4 sản lượng trên cùng ngân sách — đòn bẩy lớn nhất trong nhóm "tốn CPU, không tốn ảnh".

    ── QUYẾT ĐỊNH CHỦ THỂ PHẢI Ở ĐÂY, KHÔNG Ở TỪNG LƯỢT  (sửa 8/9/2026) ─────────────────
    Hai lượt dựng liên tiếp hỏng vì hàm này phó mặc chọn chủ thể cho từng `mot_tap`:
      · lượt 1: ba short mỗi cái chọn một chủ thể MỚI rồi dùng nền vẽ cho chủ thể của long
        — đúng "râu ông nọ cắm cằm bà kia".
      · lượt 2: long rơi về bộ sinh cũ nên không để lại bộ nhịp nào, ba short lại tự đi.
    Một BỘ theo định nghĩa là bốn clip về CÙNG một chuyện. Nên nơi quyết định chuyện ấy phải
    là nơi biết mình đang dựng một bộ — §15.3: đưa quyết định về nơi biết thứ khó truyền đi
    hơn, rồi TRUYỀN KẾT QUẢ.
    """
    global NEN_SAN, LOI_SAN
    import giai_thich as _G1
    try:
        import vi_sao as _VS
    except Exception as e:
        print(f"   ⚠ không nạp được vi_sao ({str(e)[:40]})")
        _VS = None

    _ma_sinh = k_ma_sinh(ma)
    _job = _mo_so(ma, idx)

    def _ghim(bo_nhip):
        _G1.BO_SINH[_ma_sinh] = lambda _i, _x=bo_nhip: _x

    global DA_GHIM, MOT_GIONG, CHU_THE_TAP, DAO_CU_TAP, ANH_THAT
    n = 0
    _ok_long = None
    # ── VÒNG TỰ CHỌN LẠI CHỦ THỂ NGHÈO ẢNH  (anh 10/9: "tự làm tự động a-z") ────────────────
    # Chủ thể mà ba cổng lọc còn <4 ảnh thật KHÁC NHAU thì `mot_tap` báo `_NgheoAnh` NGAY TRƯỚC
    # render (chưa tốn quota dựng); ở đây THỬ chủ thể khác, tối đa 4 lần. `sinh` đã `H.ghi` chủ
    # thể vừa chọn nên lần sau nó tránh; ta chỉ xoá `DA_CHON` để nó chọn lại. Hết 4 lần vẫn
    # nghèo thì BỎ bộ — thà không có video còn hơn ship video lặp một ảnh (anh chê nhiều lần).
    for _lan in range(4):
        _r = _VS.sinh(ma, idx) if (_VS and _VS.co_vi_sao(ma)) else None
        if not _r:
            # Không có chuyện thì KHÔNG dựng bộ (§16.7): bộ sinh cũ ra bốn clip của đường đang thay.
            print(f"   ⏭ {ma} tập {idx}: chưa có chủ thể đủ chuyện — BỎ bộ này, không dựng bừa")
            _chot_so(_job, "failed", error="không có chủ thể")
            return 0
        _ch = _VS.DA_CHON.get((ma, idx), {})
        MOT_GIONG = True
        CHU_THE_TAP = _ch.get("chu_the", "")
        DAO_CU_TAP = _ch.get("hinh_mau", "")
        ANH_THAT = nap_anh_that(CHU_THE_TAP, toi_da=32) if CHU_THE_TAP else []
        # ── LOGO/TRỤ SỞ TRA THẲNG TỪ WIKIDATA  (anh, 8/9/2026) ──────────────────────────
        # `logo_wd` tra THUỘC TÍNH thực thể (`P154` logo, `P18` ảnh chính) nên ra ĐÚNG tệp
        # của đúng công ty, có cổng chống nhận nhầm thực thể.
        globals()["LOGO_TAP"] = ""
        try:
            import logo_wd as _LW
            _tt = thuc_the(CHU_THE_TAP) or CHU_THE_TAP
            _ds = _LW.logo_va_anh(_tt)
            if _ds:
                globals()["LOGO_TAP"] = _ds[0]
                for _d in _ds:
                    TEN_ANH[_d] = _tt
                _ghi_so_anh()
                print(f"   🏷 ảnh thật của «{_tt}»: {_ds[0]}")
        except Exception as e:
            print(f"   ⚠ không lấy được logo ({str(e)[:40]}) — vẫn dựng bình thường")
        print(f"   🎨 hình mẫu: {DAO_CU_TAP or '(không nhận ra)'} · 🖼 ảnh thật: {len(ANH_THAT)}")
        DA_GHIM = True
        _ghim(_r)
        _CHON_LAI[0] = True
        try:
            _ok_long = mot_tap(ma, idx, False, chuong)
            break
        except _NgheoAnh as _na:
            print(f"   ⏭ «{_na.chu_the}» chỉ {_na.n} ảnh thật khác nhau (<{_NGUONG_ANH}) — "
                  f"chọn chủ thể khác (lần {_lan + 1}/4)")
            _VS.DA_CHON.pop((ma, idx), None)     # buộc `sinh` chọn ứng viên kế
            continue
        finally:
            _CHON_LAI[0] = False
    else:
        print(f"   ⚠ {ma} tập {idx}: thử 4 chủ thể đều nghèo ảnh thật — BỎ bộ "
              f"(không ship video lặp một ảnh)")
        _chot_so(_job, "failed", error="nghèo ảnh")
        return 0

    if _ok_long:
        n += 1
    else:
        print(f"   ⚠ {ma} tập {idx}: bản dài hỏng — bỏ cả bộ, không dựng short lẻ")
        # Không tệp nào ra đời -> trả cặp (chủ thể × khuôn) về hồ, đừng đốt nó. Bộ 198 đốt
        # «Atchison, Topeka and Santa Fe Railway» vì một tệp ảnh 0 byte và em phải gỡ tay.
        try:
            import ho_chu_de as _H9
            _dc = _VS.DA_CHON.get((ma, idx)) or {}
            if _dc.get("chu_the") and _H9.tra_lai(ma, _dc["chu_the"], _dc.get("khuon", "")):
                print(f"   ↩︎ trả «{_dc['chu_the']}» về hồ — lượt sau dựng lại được")
        except Exception as _e9:
            print(f"   ⓘ không trả lại được cặp ({type(_e9).__name__}) — không chặn lượt")
        _chot_so(_job, "failed", error="bản dài hỏng")
        return 0

    # Bộ ảnh của bản dài, đọc từ chính tệp props nó vừa ghi.
    _pj = os.path.join(GOC, "out", f"v11L_{ma}_{idx:04d}.json")
    try:
        _pd = json.load(io.open(_pj, encoding="utf-8"))
        # Giữ NỀN và LỜI CÙNG MỘT THỨ TỰ, và không lọc rỗng riêng một bên — lọc lệch thì hai
        # danh sách trượt chỉ số so với nhau, tức tái tạo đúng cái lỗi vừa sửa ở một chỗ khác.
        _cap = [(a, (l.get("nar") or ""))
                for a, l in zip(_pd.get("anhNens") or [], _pd.get("luot") or []) if a]
        NEN_SAN = [a for a, _ in _cap]
        LOI_SAN = [l for _, l in _cap]
        print(f"   ♻️ bản dài để lại {len(NEN_SAN)} nền cho ba short")
    except Exception as e:
        NEN_SAN = []
        LOI_SAN = []
        print(f"   ⚠ không đọc được nền bản dài ({str(e)[:40]}) — short dùng kho chung")

    # Short = CHƯƠNG của chính bản dài: cùng chủ thể, cùng ảnh, chỉ khác đoạn nhịp.
    _cu = os.environ.get("KHONG_NEN_TAP")
    os.environ["KHONG_NEN_TAP"] = "1"
    try:
        _tieu, _hook, _hp, _nhip = _r
        # ── CẮT TỪ BỘ NHỊP ĐÃ NỞ CỦA BẢN DÀI, KHÔNG TỪ BẢN THÔ  (8/9/2026) ───────────────
        # `vi_sao.sinh` trả bộ nhịp THÔ — đo bộ 128: **8 nhịp**. Bản dài không dùng thẳng nó:
        # `kich_ban(long=True)` nở ra **29 nhịp** bằng khối chương. Nhưng `bo_1_3` lại cắt
        # short từ bản THÔ, nên mỗi short chỉ được 2–3 nhịp — dưới sàn bốn lượt của
        # `doi_thoai`, và clip thứ tư chết đều đặn ở 4/4 bộ liên tiếp.
        # §17.11 vốn đã nói short phải cắt từ BẢN DÀI. `kich_ban` tất định và không gọi mạng
        # (bộ sinh vẫn đang ghim), nên hỏi lại nó là rẻ và cho đúng thứ bản dài đã kể.
        try:
            _nhip_dai = _G1.kich_ban(ma, idx, True, chuong or CHUONG_KHONG_LAP)[4] or _nhip
        except Exception as e:
            print(f"   ⚠ không lấy được nhịp bản dài ({str(e)[:40]}) — cắt từ bản thô")
            _nhip_dai = _nhip
        print(f"   ✂️ cắt short từ {len(_nhip_dai)} nhịp của bản dài "
              f"(bản thô {len(_nhip)} nhịp)")
        _DA_TIEU.clear()
        _lats = _lat_short(_nhip_dai)
        if len(_lats) < 3:
            print(f"   ⚠ chỉ {len(_nhip)} nhịp — dựng {len(_lats)} short thay vì 3 "
                  f"(short mỏng hơn {SAN_LUOT} nhịp không qua nổi sàn lượt)")
        for c, _lat in enumerate(_lats):
            _ghim((_tieu_short(_tieu, _lat, c), _hook, _hp, _lat))
            if mot_tap(ma, idx * 10 + c, False, 0):
                n += 1
    finally:
        NEN_SAN = []
        LOI_SAN = []
        DA_GHIM = False
        if _cu is None:
            os.environ.pop("KHONG_NEN_TAP", None)
        else:
            os.environ["KHONG_NEN_TAP"] = _cu
    print(f"   📦 bộ {ma}/{idx}: {n}/{1 + len(_lats)} clip · chủ thể «{CHU_THE_TAP}»")
    _chot_so(_job, "done" if n >= 1 else "failed",
             clips=n, subject=CHU_THE_TAP[:80])
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="dayinlife")
    ap.add_argument("--tu", type=int, default=4)
    ap.add_argument("--khong-ve-nen", action="store_true")
    ap.add_argument("--chuong", type=int, default=0,
                    help="＞0 = bản DÀI 16:9; 6 chương ≈ 2,5 phút")
    ap.add_argument("--bo", action="store_true",
                    help="dựng MỘT BỘ 1 long + 3 short dùng chung bộ ảnh (mặc định nên dùng)")
    a = ap.parse_args()
    if a.bo:
        return 0 if bo_1_3(a.kenh, a.tu, a.chuong or CHUONG_KHONG_LAP) >= 1 else 1
    return 0 if mot_tap(a.kenh, a.tu, not a.khong_ve_nen, a.chuong) else 1


if __name__ == "__main__":
    raise SystemExit(main())
