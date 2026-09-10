#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KHUNG CÂU HỎI — một kênh là MỘT LỜI HỨA chứa VÀI CHỤC khuôn nhỏ.  (7/9/2026)

── VÌ SAO KHÔNG PHẢI MỘT KÊNH MỘT KHUÔN ───────────────────────────────────────────────────
Bản thiết kế đầu của em gán mỗi kênh đúng một kiểu câu hỏi ("STILL MISSING" chỉ hỏi về thứ
mất tích). Anh bác: *"có thể cho vài chục nhóm nhỏ vào 1 channel cho đa dạng mở rộng"*.

Anh đúng, và luật YouTube đứng về phía anh. §13.18 đã đọc kỹ nguyên văn: luật KHÔNG cấm kênh
này giống kênh kia — nghìn kênh na ná nhau vẫn sống. Thứ nó cấm là **các video trong CÙNG
một kênh giống hệt nhau**, và thiếu bàn tay biên tập. Vài chục khuôn trong một kênh chính là
thứ luật ấy gọi là *meaningful variation*.

── NHƯNG LỜI HỨA PHẢI GIỮ ─────────────────────────────────────────────────────────────────
Một kênh đăng thứ gì cũng được thì không ai đăng ký. Nên kênh không định nghĩa bằng KHUÔN,
mà bằng LỜI HỨA: "thứ từng là tương lai rồi biến mất". Trong lời hứa ấy, hàng chục cách hỏi
đều hợp lệ, và người xem vẫn biết mình sẽ được xem gì.

Ba tầng, và mỗi tầng nhân lên tầng dưới:

    18 lời hứa  ×  ~24 khuôn hỏi mỗi lời hứa  ×  hồ chủ thể vô hạn

Khuôn viết TAY vì nó là NỘI DUNG chứ không phải cú pháp — ghép tự động từ tên trường sẽ ra
câu đúng ngữ pháp mà rỗng nghĩa, đúng bài học của `THEM_NHIP` trong `giai_thich`.
"""

# `{x}` = chủ thể. Mỗi khuôn là một CÁCH HỎI khác nhau về cùng một lời hứa, nên hai tập cùng
# chủ thể mà khác khuôn vẫn ra hai video khác hẳn nhau.
KHUNG = {
    "vanished": {
        "hua": "Thứ từng là tương lai, giờ không ai nhắc nữa",
        # Từ khoá của LỜI HỨA: câu nguồn phải chạm vào một trong số này thì mới thuộc về kênh
        # này. Không có nó thì "What actually killed Concorde" đi kèm sáu câu về lúc nó RA ĐỜI
        # — tiêu đề hỏi một đằng, thân bài trả lời một nẻo, và không cổng nào bắt được vì mọi
        # câu đều đúng sự thật.
        "tu_khoa": ("retire", "retired", "withdraw", "ended", "final", "last flight",
                    "ceased", "cancelled", "canceled", "grounded", "closed", "shut",
                    "decline", "declined", "stopped", "abandoned", "scrapped", "museum",
                    "out of service", "no longer", "bankrupt", "loss", "losses"),
        "khuon": [
            "Why {x} stopped being the future",
            "{x} was everywhere. Then it wasn't.",
            "What actually killed {x}",
            "The year {x} peaked, and nobody noticed",
            "{x} still exists. Almost nobody uses it.",
            "They promised {x} would change everything",
            "How much money died with {x}",
            "The last place on earth still running {x}",
            "{x} did not fail. It was replaced.",
            "Who owns {x} now",
            "The patent that outlived {x}",
            "What {x} looked like at its peak",
            "The one thing {x} got right",
            "Why nobody rebuilt {x}",
            "{x} came back. You missed it.",
            "The engineers who warned about {x}",
            "What replaced {x}, and what it cost",
            "{x} in the year it was born",
            "The museum where {x} ended up",
            "How close {x} came to working",
            "The country that kept {x}",
            "What {x} would cost today",
            "{x} and the decision that ended it",
            "Everyone forgot {x}. The data did not.",
        ],
    },
    "unsolved": {
        "hua": "Công nghệ đầy đủ mà vẫn không ai trả lời được",
        "tu_khoa": ("missing", "disappear", "vanish", "search", "never found",
                    "unknown", "unexplained", "no trace", "wreckage", "debris",
                    "last contact", "investigation", "unresolved", "mystery"),
        "khuon": [
            "GPS, radar, satellites — and {x} is still missing",
            "What the last signal from {x} said",
            "{x}: everything they found, and everything they did not",
            "The search for {x}, by the numbers",
            "How much has been spent looking for {x}",
            "Why {x} was never found",
            "The theory about {x} that will not die",
            "What {x} proves about our instruments",
            "{x}: the timeline nobody agrees on",
            "The witness accounts of {x} that conflict",
            "How long {x} has been open",
            "{x} and the evidence that went missing",
            "The one clue in {x} everyone skips",
            "What would have to be true for {x}",
            "{x}: what was ruled out, and why",
            "The people still looking for {x}",
            "{x} would be solved today. Here is why it isn't.",
            "The cost of never knowing about {x}",
            "{x} and the rule it broke",
            "What {x} changed about how we search",
            "The official report on {x}, in plain words",
            "{x}: three explanations, none complete",
            "Where {x} was last certain",
            "Why {x} still gets funded",
        ],
    },
    # ── HAI LỜI HỨA MỚI  (đa dạng 18 kênh, anh 10/9/2026) ──────────────────────────────
    # §14.1: thêm mười cái GIỐNG NHAU không phải mở rộng. 18 kênh dồn vào 2 lời hứa nên
    # nhiều kênh na ná; §13.18 nói 24 khuôn lo đa dạng TRONG kênh, nhưng lời hứa khác nhau
    # làm các KÊNH khác nhau. Nay 4 lời hứa, ~4-5 kênh mỗi cái. Từ khoá lái đúng chủ thể mà
    # gốc của kênh vốn đã cung cấp (scandal/defunct -> downfall; products -> boom).
    "downfall": {
        "hua": "Đế chế khổng lồ sụp đổ chỉ từ một quyết định",
        "tu_khoa": ("collapse", "collapsed", "scandal", "fraud", "bankrupt", "bankruptcy",
                    "fined", "sued", "lawsuit", "indicted", "convicted", "cover-up",
                    "coverup", "resigned", "recall", "banned", "shut down", "settlement",
                    "penalty", "ruling", "seized", "liquidated", "dissolved", "collapse of"),
        "khuon": [
            "The one decision that ended {x}",
            "How {x} went from untouchable to gone",
            "{x} was too big to fail. Then it failed.",
            "The email that brought down {x}",
            "What {x} hid, and what it cost",
            "The day {x} ran out of excuses",
            "{x}: who knew, and when",
            "The number that exposed {x}",
            "How much {x} owed when it fell",
            "The rule {x} thought did not apply",
            "{x} and the whistleblower nobody believed",
            "What the {x} verdict actually said",
            "The warning about {x} everyone ignored",
            "{x}: the last people paid, and the first who left",
            "How fast {x} unraveled once it started",
            "The fine print that sank {x}",
            "Who got rich as {x} died",
            "{x} would be illegal today. It wasn't then.",
            "The audit that found {x}",
            "What replaced {x}, and who paid for it",
            "The promise {x} could never keep",
            "{x}: the timeline from peak to prison",
            "Why no one stopped {x} sooner",
            "What {x} teaches about trusting a giant",
        ],
    },
    "boom": {
        "hua": "Thứ bùng nổ khắp nước Mỹ rồi tắt ngấm",
        "tu_khoa": ("popular", "popularity", "craze", "fad", "boom", "peak", "peaked",
                    "sold", "millions", "everywhere", "hit", "sensation", "phenomenon",
                    "best-selling", "bestselling", "dominated", "launched", "success",
                    "rise", "decline", "discontinued", "replaced", "obsolete", "outsold"),
        "khuon": [
            "{x} was everywhere. Then it wasn't.",
            "How {x} sold millions, then zero",
            "The peak year of {x}, and what came next",
            "Why everyone owned {x}, then nobody did",
            "{x}: the fad that felt permanent",
            "What killed {x} — a rival, or itself",
            "The last store to stock {x}",
            "{x} by the numbers, top to bottom",
            "How long {x} stayed on top",
            "The upgrade that ended {x}",
            "{x}: the ad campaign that oversold it",
            "Who kept making {x} after everyone quit",
            "The knockoffs that outlived {x}",
            "What {x} promised that it could not scale",
            "{x} in the year it was born",
            "The warehouse still full of {x}",
            "Why {x} felt like the future",
            "{x}: three reasons it faded",
            "What replaced {x}, and what it cost",
            "The collectors who still hunt {x}",
            "How much {x} is worth now",
            "{x} came back. You missed it.",
            "The patent that outlived {x}",
            "What {x} got right before it lost",
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════════════════════════
# TỪ KHUÔN HỎI + TƯ LIỆU THẬT -> NHỊP KỊCH BẢN
# ══════════════════════════════════════════════════════════════════════════════════════════
import re as _re


_NGAY = _re.compile(r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
                    r"September|October|November|December)\b")


def _so_dau(c: str):
    """(số, đơn vị) ĐÁNG hiện lên màn. ("", "") khi câu không có LƯỢNG nào.

    Bản đầu lấy chữ số đầu tiên, nên "On 9 October 1975" cho ra `9`. Bỏ cụm ngày rồi mới
    tìm số — đúng hướng, nhưng vẫn chỉ hỏi *"đây có phải chữ số không"*.

    ── VÌ SAO PHẢI HỎI THÊM "CÓ PHẢI MỘT LƯỢNG KHÔNG"  (anh soi bộ 219, 9/9/2026) ───────
    Bốn thẻ số của bộ ấy, cả bốn `don=""`:
        771   <- "The accident contaminated **Building 771** and caused $818,600 damage"
        11    <- "On **September 11**, 1957 a plutonium fire erupted"
        1400  <- "the **1400 page** congressional testimony"
        1974  <- "In **1974** operator error released…"
    771 là số HIỆU TOÀ NHÀ. 11 là ngày — `_NGAY` bỏ được dạng "9 October 1975" nhưng không
    bỏ dạng tháng-đứng-trước. 1400 là lượng THẬT mà đơn vị "page" bị vứt đi. Chỉ 1974 đúng.
    Cùng họ với thẻ "17" của **B‑17** hôm nay và `so="SOUTH"` hôm qua: một con số lọt vào
    chỗ dành cho một ĐẠI LƯỢNG.

    Nên đổi câu hỏi: không hỏi *"có chữ số không"* mà hỏi *"có một LƯỢNG không"* — và
    `_CD.so_kem_don` đã trả lời đúng câu ấy cho hook từ đầu giờ, dùng lại chứ không viết mới
    (§13.1). NĂM vẫn được giữ: nó là mốc thời gian, thứ xương sống của mọi câu chuyện, và
    thẻ năm đọc ra ngay là năm.

    Trả về CẶP: đơn vị phải đi cùng con số suốt đường tới màn hình, nếu không nó lại rơi ra
    ở đúng chỗ nó đã rơi (§14.16 — chỗ hở nằm ở phần mình không viết ra).
    """
    import chu_de as _CD                 # `_CD` chỉ có trong `nhip_tu_khuon`, không ở module
    c0 = _NGAY.sub(" ", c or "")
    t = _CD.so_kem_don(c0)
    if t:
        pp = t.split(" ", 1)
        return pp[0], (pp[1] if len(pp) > 1 else "")
    m = _re.search(r"\b(1[89]\d\d|20[0-2]\d)\b", c0)      # năm: mốc thời gian, giữ
    return (m.group(1), "") if m else ("", "")


# ── THAM CHIẾU TREO: CÂU ĐÚNG TRONG BÀI, VÔ NGHĨA KHI TÁCH RA  (7/9/2026) ─────────────────
# "The combination of these two factors caused a decline in profits." — đúng nguyên văn, và
# trong bài nó trỏ về hai yếu tố ở đoạn trên. Tách ra đứng một mình thì người xem không biết
# HAI YẾU TỐ NÀO. Câu vẫn thật, mà vẫn hỏng.
#
# Đây là loại lỗi mà cổng kiểm mệnh đề KHÔNG bắt được: câu bắt rễ hoàn toàn ở nguồn, số đúng,
# phủ định cùng chiều — nó chỉ thiếu thứ nằm ở CÂU TRƯỚC. Nên phải chặn bằng một phép khác:
# nhận ra từ chỉ trỏ mà không có vật để trỏ.
_TREO = _re.compile(r"^\s*(?:the\s+)?(?:combination of\s+)?"
                    r"(?:these|those|this|that|such|it|they|he|she|his|her|their|both|"
                    r"the (?:former|latter|same|other|two|three))\b", _re.I)


def _co_tham_chieu_treo(c: str) -> bool:
    return bool(_TREO.match(c or ""))


def _lau_sach(c: str) -> str:
    """Dọn rác chữ của Wikipedia: dấu ngoặc kép lạc, khoảng trắng thừa, dấu câu treo.

    Đo được `" The Kodak name was trademarked` — một dấu nháy mở lạc từ câu trước. Nó nhỏ,
    và nó là thứ người xem đọc ra "cẩu thả" ngay trong nửa giây (§12.12).
    """
    c = " ".join(str(c or "").split())
    c = _re.sub(r'^["\u201c\u201d\'`,;:\-\u2013\u2014 ]+', "", c)
    return c


def _duoi_hong(r: str) -> bool:
    """Câu cắt xong có kết thúc lửng lơ không.

    Ba dạng đo được trong bản Kodak đầu tiên, và cả ba đều đọc lên là câu chưa hết:
      · kết bằng SỐ      — "declined from 80."      (mất vế "xuống 7%")
      · kết bằng CHỮ TẮT — "after Antonio M."       (cắt giữa tên người)
      · kết bằng GIỚI TỪ — "the company emerged from."
    Một câu cụt tệ hơn một câu dài: câu dài chỉ chậm, câu cụt thì sai nghĩa.
    """
    r = (r or "").rstrip()
    if _re.search(r"\b\d[\d,\.]*\s*%?\.$", r):
        return True
    if _re.search(r"\b[A-Z]\.$", r):
        return True
    if _re.search(r"\b(of|in|on|at|to|for|from|by|with|as|than|into|over|under|after|"
                  r"before|between|and|or|but|the|a|an)\.$", r, _re.I):
        return True
    return False


# Trần 160 chứ không phải 74. Đây là CÂU DẪN, không phải lời thoại — `pilot_hai` sẽ đưa nó
# cho mô hình nén thành lượt 5–10 chữ ở bước sau. Trần 74 làm mọi câu dài phải cắt, và cắt
# là chỗ đẻ ra câu cụt: đo được nó bỏ oan "declined from 80% in 1976 to 7% in 2010" — một
# câu hoàn chỉnh, đúng chủ đề, chỉ vì không có dấu phẩy nào để cắt.
def _rut(c: str, tran: int = 160) -> str:
    """Cắt câu nguồn xuống độ dài đọc được, KHÔNG viết lại.

    Viết lại là chỗ mô hình bịa (đo hôm nay: "Theranos worked"). Cắt thì câu vẫn là câu của
    nguồn, chỉ ngắn hơn — mọi chữ còn lại đều truy ngược được.
    """
    c = " ".join(str(c or "").split()).rstrip(".")
    if len(c) <= tran:
        r = c + "."
        return "" if _duoi_hong(r) else r
    # Cắt ở ranh giới MỆNH ĐỀ, không ở ranh giới từ. Bản đầu cắt theo từ và ra "as the." —
    # đúng ngữ pháp tới nửa câu rồi cụt, tệ hơn một câu dài.
    d = c[:tran]
    for dau in (";", ",", " and ", " but ", " as ", " with ", " which "):
        k = d.rfind(dau)
        if k > tran * 0.45:
            r = d[:k].rstrip(",;: ") + "."
            if not _duoi_hong(r):
                return r
    return ""          # không cắt sạch được thì BỎ CÂU, đừng giao một câu cụt

def nhip_tu_khuon(khuon: str, chu_the: str, ho_so: dict, _n, _ve,
                  tu_khoa=(), dung_ai: bool = True) -> tuple:
    """(tiêu đề, hook, hook phụ, nhịp) — đúng hình dạng `giai_thich.BO_SINH` trả.

    Mọi câu là câu CỦA NGUỒN đã cắt sạch; mọi số là số của chính câu ấy. Không chỗ nào để
    mô hình cấp một dữ kiện — nó chỉ được CHỌN (trả về chỉ số), nên cổng "số bịa" ở
    `pilot_hai` luôn xanh ở bộ này.
    """
    import chu_de as _CD
    sach = []
    for c in (ho_so.get("tat_ca") or ho_so.get("cau") or []):
        r = _rut(c["cau"])
        if not r or _co_tham_chieu_treo(r) or not _CD.de_hieu(r):
            continue
        r = _lau_sach(r)
        if r:
            _s, _d = _so_dau(r)
            sach.append({"cau": r, "so": _s, "don": _d})
    if len(sach) < 8:
        return None

    # Tên chủ thể giữ nguyên hoa/thường như nguồn viết. Bản dựng đầu ra "kodak" chữ thường
    # vì khuôn hook hạ chữ cả câu — tên riêng viết thường đọc ra là cẩu thả (§12.12).
    chu_the = chu_the.strip()
    tieu = khuon.format(x=chu_the)
    chon = chon_cau(tieu, sach) if dung_ai else []
    if len(chon) < 5:
        # Mô hình không chọn được -> lùi về lọc theo TỪ KHOÁ của lời hứa. Đường lùi phải
        # tồn tại: một lượt gọi AI hỏng không được làm chết cả tập (§13.3).
        tk = tuple(t.lower() for t in (tu_khoa or ()))
        hua = [k for k, x in enumerate(sach)
               if not tk or any(t in x["cau"].lower() for t in tk)]
        if len(hua) < 2:
            return None
        con = [k for k in range(len(sach)) if k not in hua]
        chon = [hua[0]] + con[:4] + [hua[1]]
    cau = [sach[k] for k in chon][:6]

    # ── [KEEP] PHẢI GẮN VÀO CÂU CÚ LẬT, KHÔNG PHẢI CÂU ĐẦU DANH SÁCH  (7/9/2026) ─────────
    # Bản trước gắn theo VỊ TRÍ (câu mô hình chọn đầu tiên). Dựng thật thì nó rơi vào "in
    # September 2012, declining sales forced Kodak to announce an exit" — một kết cục, không
    # phải cú lật. Cú lật là câu PHỦ ĐỊNH ĐIỀU NGƯỜI XEM ĐANG TIN, và nó tự khai ra bằng
    # chính từ ngữ của nó ("misconception", "despite", "contrary"). Nhận theo NGHĨA, đừng
    # nhận theo chỗ đứng (§15.8: danh sách từ không đo được khái niệm, nhưng ở đây khái niệm
    # ấy CÓ dấu hiệu ngôn ngữ riêng — đó là khác biệt).
    _LAT = _re.compile(r"\b(misconception|despite|contrary|in fact|actually|myth|"
                       r"widely believed|often assumed|not because)\b", _re.I)
    _k_lat = next((k for k, x in enumerate(cau) if _LAT.search(x["cau"])), 0)
    _con = [x for k, x in enumerate(cau) if k != _k_lat]

    # ── NÊU MỘT ĐIỀU SAI MÀ KHÔNG NÓI ĐIỀU ĐÚNG THÌ TỆ HƠN KHÔNG NÊU  (anh soi, 7/9/2026)
    # Dựng thật: "People think Kodak ignored digital cameras, but that's wrong" — rồi tập
    # nhảy sang 2012, hỏi về hoá chất, nhảy về 2007. Người xem KHÔNG BAO GIỜ biết cái gì
    # thật sự giết Kodak. Đó đúng là *"xem ko hiểu"* anh nói.
    # Ngay sau cú lật phải là NGUYÊN NHÂN THẬT — câu mang chữ chỉ nguyên nhân.
    _NGUYEN_NHAN = _re.compile(r"\b(failed|failure|instead|because|led to|caused|forced|"
                               r"abandoned|refused|lacked|without)\b", _re.I)
    _nn = [x for x in _con if _NGUYEN_NHAN.search(x["cau"])]
    _khac = [x for x in _con if x not in _nn]

    # ── THỜI GIAN PHẢI ĐI MỘT CHIỀU ─────────────────────────────────────────────────────
    # Bản trước ra 2012 -> 2007 -> phá sản. Tai người theo được một mạch thời gian, không
    # theo được ba lần nhảy. Xếp phần bối cảnh theo NĂM tăng dần; câu không có năm giữ
    # nguyên thứ tự mô hình đã chọn (nó chọn theo mạch, và mạch ấy đáng tin hơn phép sắp).
    def _nam(x):
        m = _re.search(r"\b(1[89]\d\d|20\d\d)\b", x["cau"])
        return int(m.group()) if m else 10 ** 9
    _khac = sorted(_khac, key=_nam)
    cau = [cau[_k_lat]] + _nn[:2] + _khac

    dau = cau[0]
    hook = tieu.upper()[:52]
    # ── LƯỢNG PHẢI ĐI KÈM ĐƠN VỊ CỦA CHÍNH NÓ  (bộ 214 · 216, 9/9/2026) ──────────────
    # `dau["so"]` là con số ĐÃ BỊ TÁCH khỏi đơn vị, và hai lượt liền cho cùng một bệnh:
    #     214: *"How much money died with Savannah River Plant, eighty DOLLARS?"*
    #     216: *"The patent that outlived Savannah River Plant SHOWS 80."*
    # Cả hai lấy số 80 của câu *"claim up to 80 PERCENT"* — lần đầu mô hình tự gắn đơn vị
    # sai, lần sau nó không gắn gì và câu thành vô nghĩa. §14.16: luật "hook phải có một
    # lượng chính xác" được thoả bằng cách RẺ NHẤT câu chữ cho phép, và chỗ hở nằm ở phần
    # ta không viết ra — ta nói *phải có số*, không nói *số phải mang đơn vị của nó*.
    # Không có lượng nào kèm đơn vị thì để TÊN CHỦ THỂ như cũ: `phim._la_so` thấy không phải
    # số nên bỏ hẳn thẻ, và hook vẫn tới người xem bằng chính câu chuyện.
    hook_phu = _CD.so_kem_don(dau["cau"]).upper() or chu_the.upper()[:18]

    # ── NHỊP 0 PHẢI NÓI RÕ ĐÓ LÀ GÌ  (anh: *"xem ko hiểu"*, 7/9/2026) ────────────────────
    # Bản trước mở thẳng bằng CÚ LẬT ("ai cũng tưởng Kodak bỏ lỡ máy ảnh số"). Người xem
    # chưa biết Kodak là ai thì cú lật ấy không lật được gì — nó rơi vào khoảng không.
    # Một cú lật chỉ có lực khi người xem ĐANG GIỮ điều sắp bị lật.
    _la_gi = _CD.cau_la_gi(ho_so.get("van") or "")
    nhip = []
    if _la_gi:
        nhip.append(
            _n("canh", _la_gi, du=True,
               ve=_ve(f"a simplified figure holding one everyday object",
                      "showing it to the viewer", "matter-of-fact",
                      "a plain pale wall", "a clean floor strip", "restrained muted palette")))
    nhip += [
        # `du=True`: nhịp này TỰ MANG nội dung của nó, `_day_du_y` không được chèn câu
        # viết tay của kênh vào (§ đo được: tập về Kodak dính câu về ranh giới đất).
        # `[KEEP]` — nhịp này là CÚ LẬT của tập, khâu nén lời thoại không được bỏ mệnh đề
        # của nó. Cổng ở `pilot_hai` đọc dấu này.
        _n("so_lieu" if dau["so"] else "canh", "[KEEP]" + dau["cau"], du=True,
           **({"so": dau["so"], "don": dau.get("don") or "", "bt": "tien"}
              if dau["so"] else {}),
           dinh=True,
           ve=_ve("a simplified figure looking at a single object on a plain table",
                  "studying it closely", "curious",
                  "a plain pale wall", "a clean floor strip", "restrained muted palette")),
    ]
    for c in cau[1:]:
        if c["so"]:
            nhip.append(_n("so_lieu", c["cau"], so=c["so"], don=c.get("don") or "",
                               bt="tien", dinh=True))
        else:
            nhip.append(_n("canh", c["cau"],
                           ve=_ve("a simplified figure at a desk with one folder open",
                                  "reading a single page", "absorbed",
                                  "a plain office wall", "a clean floor strip",
                                  "restrained muted palette")))
    nhip.append(
        _n("canh", f"That is the part of {chu_the} nobody repeats.", du=True,
           ve=_ve("a simplified figure closing a folder and setting it down",
                  "finished", "quiet",
                  "a plain office wall", "a clean floor strip", "restrained muted palette")))
    return tieu, hook, hook_phu, nhip


# ══════════════════════════════════════════════════════════════════════════════════════════
# AI CHỌN, KHÔNG VIẾT
# ══════════════════════════════════════════════════════════════════════════════════════════
# Bộ lọc từ khoá bắt được câu CHỨA chữ "bankruptcy"; nó không bắt được câu GIẢI THÍCH vì sao
# phá sản. Đo: "What actually killed Kodak" ra bốn nhịp giữa nói về 1880–1888, lúc công ty RA
# ĐỜI. Chọn câu theo quan hệ nhân quả là việc của ngôn ngữ, không phải của danh sách từ.
#
# Nhưng giao việc chọn cho mô hình mà để nó SINH CHỮ là mở lại đúng cửa đã đóng: hôm nay đo
# được nó bịa "one hundred ninety miles" (sai) và "Theranos worked" (sai về một vụ án hình
# sự). Nên nó trả về CHỈ SỐ — không được viết một chữ nào; mọi câu đi vào sản phẩm vẫn là câu
# nguyên văn của nguồn.
LENH_CHON = """You are given a title and a numbered list of factual sentences taken verbatim
from an encyclopedia article. Choose the sentences that actually answer the title, and put
them in the order a viewer should hear them.

RULES
1. Return ONLY indices from the list. Never write a sentence of your own, never edit one.
2. Pick exactly 6. The FIRST must state the outcome the title asks about; the LAST must land
   the consequence. The four in between give the cause, in the order it happened.
3. A sentence about when something was founded does not answer "what killed it". Skip
   sentences that are merely chronology unless they explain the outcome.
4. If fewer than 6 sentences genuinely bear on the title, return fewer. Returning a weak
   sentence is worse than returning a short list.

Return ONLY a JSON array of integers, e.g. [12,3,7,19,2,25]"""


def chon_cau(tieu: str, cau: list, keys=None) -> list:
    """Chỉ số các câu được chọn. Rỗng khi không gọi được -> bên gọi dùng đường lùi từ khoá."""
    import phim_canh as _C
    # `_goi` đòi danh sách khoá và nổ `TypeError` khi nhận None — lấy đúng đường mà
    # `pilot_hai` lấy (§13.15), đừng tự dựng đường thứ hai.
    keys = keys or _C._khoa_groq()
    ds = "\n".join(f"{i}. {c['cau']}" for i, c in enumerate(cau))
    u = f"TITLE: {tieu}\n\nSENTENCES:\n{ds}"
    try:
        ra = _C._tach_json(_C._goi(LENH_CHON, u, keys)) or []
    except Exception:
        return []
    tot, thay = [], set()
    for x in ra:
        try:
            i = int(x)
        except Exception:
            continue
        if 0 <= i < len(cau) and i not in thay:
            thay.add(i)
            tot.append(i)
    return tot[:6]


# ══════════════════════════════════════════════════════════════════════════════════════════
# KHUÔN ĐÒI MỘT CON SỐ TIỀN — ĐỪNG PHÁT CHO CHỦ THỂ KHÔNG CÓ
# ══════════════════════════════════════════════════════════════════════════════════════════
# ── VÌ SAO  (anh soi bộ 214, 9/9/2026) ────────────────────────────────────────────────────
# Hook bản dài đọc *"How much money died with Savannah River Plant, **eighty dollars**?"* —
# kịch bản không có một con số tiền nào. Mô hình lấy chữ "eighty" từ câu *"owner could claim
# up to eighty **percent**"* rồi gắn sang đơn vị **dollars**.
#
# Cổng chặn số bịa CÓ chạy, và nó đúng theo định nghĩa của nó: nó hỏi *"con số này có trong
# kịch bản không"* — 80 CÓ. Cái nó không hỏi là *"ĐƠN VỊ có đúng không"*. Đúng số, sai nghĩa
# là chiều thứ ba, và §19.3 mới canh hai chiều (thiếu / thừa).
#
# KHÔNG chữa bằng một cổng ngữ nghĩa: đo đơn vị khớp nghĩa là việc của ngôn ngữ, và một cổng
# mờ như thế sẽ bắt oan nhiều hơn bắt đúng (§13.22). Chữa ở GỐC, đúng cách §19.4 đã chỉ:
# *mô hình bịa vì KHÔNG CÒN GÌ THẬT ĐỂ NÓI* — đề bài đòi một con số tiền mà kịch bản không
# có, nên nó lấp chỗ trống bằng đồ tự nghĩ.
#
# Cùng cơ chế `mo_cam` của §14.2 (đừng phát cho một kênh nhịp mà thế giới ấy không diễn được),
# chỉ khác trục: đừng phát khuôn hỏi TIỀN cho chủ thể không có con số tiền nào.
DOI_TIEN = (
    "How much money died with {x}",
    "What {x} would cost today",
    "What replaced {x}, and what it cost",
)

# Con số TIỀN trong văn nguồn: ký hiệu tiền tệ, hoặc số kèm đơn vị tiền viết chữ.
# Không nhận "eighty percent" — đó chính là con số đã bị mượn sai đơn vị.
import re as _re
_CO_TIEN = _re.compile(
    r"(?:[$£€]\s?[\d,]+(?:\.\d+)?)"
    r"|(?:[\d,]+(?:\.\d+)?\s*(?:million|billion|trillion)?\s*"
    r"(?:dollars?|pounds\s+sterling|euros?|USD|GBP|EUR)\b)",
    _re.I)


def khuon_doi_tien(khuon: str) -> bool:
    """Khuôn hỏi này có BẮT BUỘC phải nêu một con số tiền không."""
    return str(khuon or "") in DOI_TIEN


def co_so_tien(van: str) -> bool:
    """Văn bản nguồn có ít nhất một con số TIỀN thật không."""
    return bool(_CO_TIEN.search(str(van or "")))
