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
}


# ══════════════════════════════════════════════════════════════════════════════════════════
# TỪ KHUÔN HỎI + TƯ LIỆU THẬT -> NHỊP KỊCH BẢN
# ══════════════════════════════════════════════════════════════════════════════════════════
import re as _re


_NGAY = _re.compile(r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
                    r"September|October|November|December)\b")


def _so_dau(c: str) -> str:
    """Con số ĐÁNG hiện lên màn. Bỏ ngày-trong-tháng.

    Bản đầu lấy chữ số đầu tiên, nên "On 9 October 1975" cho ra `9` và "entered service on
    21 January 1976" cho ra `21`. Đó là NGÀY, không phải dữ kiện — thẻ số hiện "9" thì người
    xem không hiểu 9 cái gì. Bỏ cụm ngày trước rồi mới tìm số.
    """
    c = _NGAY.sub(" ", c or "")
    for m in _re.finditer(r"\b\d[\d,\.]*\b", c):
        g = m.group()
        if len(g.replace(",", "").replace(".", "")) > 1:      # bỏ số một chữ số lẻ loi
            return g
    return ""


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
    sach = []
    for c in (ho_so.get("tat_ca") or ho_so.get("cau") or []):
        r = _rut(c["cau"])
        if not r or _co_tham_chieu_treo(r):
            continue
        r = _lau_sach(r)
        if r:
            sach.append({"cau": r, "so": _so_dau(r)})
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

    dau = cau[0]
    hook = tieu.upper()[:52]
    hook_phu = dau["so"] or chu_the.upper()[:18]

    nhip = [
        # `du=True`: nhịp này TỰ MANG nội dung của nó, `_day_du_y` không được chèn câu
        # viết tay của kênh vào (§ đo được: tập về Kodak dính câu về ranh giới đất).
        # `[KEEP]` — nhịp này là CÚ LẬT của tập, khâu nén lời thoại không được bỏ mệnh đề
        # của nó. Cổng ở `pilot_hai` đọc dấu này.
        _n("so_lieu" if dau["so"] else "canh", "[KEEP]" + dau["cau"], du=True,
           **({"so": dau["so"], "don": "", "bt": "tien"} if dau["so"] else {}),
           dinh=True,
           ve=_ve("a simplified figure looking at a single object on a plain table",
                  "studying it closely", "curious",
                  "a plain pale wall", "a clean floor strip", "restrained muted palette")),
    ]
    for c in cau[1:]:
        if c["so"]:
            nhip.append(_n("so_lieu", c["cau"], so=c["so"], don="", bt="tien", dinh=True))
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
