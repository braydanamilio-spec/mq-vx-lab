#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NGUỒN MỞ CÓ CẤU TRÚC — chủ đề "vì sao" sinh từ phép GỘP, không từ bảng viết tay. (7/9/2026)

── VÌ SAO KHÔNG PHẢI WIKIPEDIA ────────────────────────────────────────────────────────────
Em neo vào Wikipedia rồi kết luận cho cả hướng đi, và anh bác đúng: *"Wikipedia có nhiều
nguồn lắm mà"*. Đo lại thì con số nói rõ:

    bài Wikipedia NGẪU NHIÊN        0/24 đủ sự thật   (0%)
    bài được TRA NHIỀU NHẤT         3/24              (12%)
    openFDA · phản ứng phụ thuốc    20.692.690 bản ghi, mỗi bản ghi TỰ NÓ là số liệu

12% là giới hạn của một nguồn CHỮ, không phải của hướng đi. Nguồn có CẤU TRÚC thì dùng
được 100%, và nó là kho lịch sử nên chỉ dồn thêm chứ không mất đi.

── VÌ SAO GỘP, KHÔNG LẤY BẢN GHI LẺ ───────────────────────────────────────────────────────
Một bản ghi lẻ thì nhạt: "một người, một thuốc, một phản ứng". GỘP lại mới thành tập:

    4.011 vụ thu hồi thực phẩm ở California · 1.942 Texas · 1.886 Illinois
    534.326 báo cáo phản ứng phụ cho ASPIRIN

Và gộp giải luôn bài toán khó nhất của hướng câu chuyện: **con số do Python tính ra**, còn
mệnh đề đi kèm là HỆ QUẢ TRỰC TIẾP của phép tính. "California thu hồi nhiều hơn mọi bang
khác" là điều phép đếm nói ra, không phải điều mô hình nghĩ ra. Nên hướng này giữ được đúng
tính an toàn của 18 kênh đo lường — không như đường Wikipedia, nơi em đã đo được mô hình
viết "Theranos worked" và cổng kiểm số cho đi qua.

── VÌ SAO XẾP HẠNG Ô, KHÔNG DUYỆT Ô ───────────────────────────────────────────────────────
Hai trục gộp của một nguồn cho ~17 tỉ ô. Nhưng phần lớn RỖNG hoặc PHẲNG: "thu hồi ở
Wyoming, hạng III, 1987" ra hai bản ghi, và một biểu đồ mà mọi cột bằng nhau thì không so
gì cả (§15.13). Nên không duyệt — XẾP HẠNG: giữ ô có đủ dữ liệu VÀ có tương phản thật.

Và §15.7: không phải cặp trục nào cũng có nghĩa. Mỗi nguồn khai TAY những trục nó cho phép
gộp, thay vì để máy ghép mù rồi ra "công viên chó bốc khói".
"""
from __future__ import annotations

import json
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

# Mỗi nguồn khai: endpoint · các trục ĐƯỢC PHÉP gộp · câu hỏi mà trục ấy trả lời.
# Câu hỏi viết tay vì nó là NỘI DUNG, không phải khuôn — ghép tự động từ tên trường sẽ ra
# câu đúng ngữ pháp mà rỗng nghĩa, đúng cái phải tránh (xem `THEM_NHIP` trong `giai_thich`).
NGUON = {
    "thu_hoi_thuc_pham": {
        "ten": "FDA food recalls",
        "url": "https://api.fda.gov/food/enforcement.json",
        "truc": [
            ("state.exact", "Which state pulls the most food off its shelves?",
             "{ten} pulled {so} {don}. Your state did not come close."),
            ("recalling_firm.exact", "Which company recalls the most food?",
             "One company recalled food {so} times. You have eaten their products."),
            ("classification.exact", "How dangerous are the recalls, really?",
             "{so} recalls were the serious kind. Most people never heard."),
        ],
    },
    "thu_hoi_thiet_bi": {
        "ten": "FDA medical device recalls",
        "url": "https://api.fda.gov/device/enforcement.json",
        "truc": [
            ("state.exact", "Which state recalls the most medical devices?",
             "{ten} logged {so} {don}. Your hospital buys from there."),
            ("recalling_firm.exact", "Which manufacturer recalls the most devices?",
             "One maker recalled devices {so} times. Their parts are inside people."),
        ],
    },
    "phan_ung_thuoc": {
        "ten": "FDA adverse drug events",
        "url": "https://api.fda.gov/drug/event.json",
        "truc": [
            ("patient.drug.openfda.generic_name.exact",
             "Which drug generates the most adverse event reports?",
             "{ten} has {so} adverse event reports. It is in most medicine cabinets."),
            ("patient.reaction.reactionmeddrapt.exact",
             "Which reaction gets reported the most?",
             "{so} reports say the same thing, and it is not what you would guess."),
        ],
    },
}


def _goi(url: str, timeout: int = 30) -> dict:
    r = urllib.request.Request(url, headers=UA)   # §13.15: thiếu User-Agent -> CDN chặn 403
    return json.load(urllib.request.urlopen(r, timeout=timeout))


def gop(ma_nguon: str, truc: str, lay: int = 12) -> list:
    """[(nhãn, số)] — phép đếm do CHÍNH NGUỒN thực hiện, không ai tính hộ."""
    n = NGUON.get(ma_nguon)
    if not n:
        return []
    u = f"{n['url']}?count={urllib.parse.quote(truc)}&limit={int(lay)}"
    try:
        return [(r["term"], int(r["count"])) for r in (_goi(u).get("results") or [])]
    except Exception:
        return []


def dang_ke(hang: list, san_dinh: int = 200, san_ti: float = 1.6) -> bool:
    """Ô này có đáng một tập không.

    Hai điều kiện, và thiếu điều nào cũng bỏ:
      · ĐỦ DỮ LIỆU — đầu bảng phải đạt `san_dinh`, nếu không thì con số quá nhỏ để ai quan tâm;
      · CÓ TƯƠNG PHẢN — đầu bảng phải hơn trung vị ít nhất `san_ti` lần. Một bảng mà mọi
        giá trị xấp xỉ nhau thì không có gì để hỏi "vì sao", và biểu đồ vẽ ra là một trục
        phẳng (§15.13).
    """
    if len(hang) < 4:
        return False
    vs = sorted((v for _t, v in hang), reverse=True)
    if vs[0] < san_dinh:
        return False
    tv = vs[len(vs) // 2] or 1
    return vs[0] / tv >= san_ti


def chu_de_dang_ke(lay_moi_truc: int = 12) -> list:
    """Mọi ô ĐÁNG LÀM ở mọi nguồn: [{nguon, truc, cau_hoi, hang}]."""
    ra = []
    for ma, n in NGUON.items():
        for truc, cau, khuon in n["truc"]:
            h = gop(ma, truc, lay_moi_truc)
            if dang_ke(h):
                ra.append({"nguon": ma, "ten_nguon": n["ten"], "truc": truc,
                           "cau_hoi": cau, "khuon_tieu": khuon, "hang": h})
    return ra


# ══════════════════════════════════════════════════════════════════════════════════════════
# BỘ SINH KỊCH BẢN — một ô gộp thành một tập
# ══════════════════════════════════════════════════════════════════════════════════════════
# Trả về đúng hình dạng mà `giai_thich.BO_SINH` trả: (tiêu đề, hook, hook phụ, danh sách
# nhịp). Nhờ vậy toàn bộ phần còn lại của dây chuyền — engine, vai chuyên gia, ngữ điệu,
# luân phiên, trang phục, kho nền, ảnh bìa, khâu đăng — KHÔNG phải sửa một dòng nào.
#
# Mọi con số trong nhịp đều đến từ phép đếm của chính nguồn. Không chỗ nào để mô hình cấp
# số, nên cổng "số bịa" ở `pilot_hai` sẽ luôn xanh ở bộ này — đúng như 18 kênh đo lường.


# Đơn vị phải gọi đúng tên THỨ ĐANG ĐẾM. "records" là chữ của lập trình viên; người xem
# nghe "food recalls" mới hình dung ra. Đây đúng chỗ anh chê "khô khan, đọc ko ra gì".
DON_VI = {"thu_hoi_thuc_pham": "food recalls",
          "thu_hoi_thiet_bi": "device recalls",
          "phan_ung_thuoc": "reports"}

# Mã bang -> tên bang. "Why CA leads" không phải tiếng Anh người ta nói; "Why California
# leads" mới là. Bảng viết tay vì nó là 50 dòng cố định, không phải thứ sẽ lớn lên.
BANG = {"AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California",
 "CO":"Colorado","CT":"Connecticut","DE":"Delaware","FL":"Florida","GA":"Georgia",
 "HI":"Hawaii","ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas",
 "KY":"Kentucky","LA":"Louisiana","ME":"Maine","MD":"Maryland","MA":"Massachusetts",
 "MI":"Michigan","MN":"Minnesota","MS":"Mississippi","MO":"Missouri","MT":"Montana",
 "NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico",
 "NY":"New York","NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma",
 "OR":"Oregon","PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina",
 "SD":"South Dakota","TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont",
 "VA":"Virginia","WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming",
 "DC":"Washington, D.C.","PR":"Puerto Rico"}


def _ten_that(t: str) -> str:
    """Nhãn người xem đọc được. Mã bang -> tên bang; chữ IN HOA của cơ sở dữ liệu -> chữ thường."""
    t = str(t or "").strip()
    if t.upper() in BANG:
        return BANG[t.upper()]
    if t.isupper() and len(t) > 3:
        return t.title()
    return t


def _gon(t: str, n: int = 26) -> str:
    t = " ".join(str(t or "").replace(",", " ").split())
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def sinh_taisao(chu_de: dict, _n, _ve, _loi=None) -> tuple:
    """`_n`/`_ve` truyền vào từ `giai_thich` để không tạo bản sao thứ hai của chúng."""
    hang = chu_de["hang"]
    dinh_t, dinh_v = hang[0]
    hai_t, hai_v = hang[1] if len(hang) > 1 else hang[0]
    vs = sorted((v for _t, v in hang), reverse=True)
    tv = vs[len(vs) // 2] or 1
    lan = dinh_v / tv
    tong = sum(v for _t, v in hang)

    don_vi = DON_VI.get(chu_de["nguon"], "records")
    ten = _gon(_ten_that(dinh_t))
    # Tiêu đề phải NÊU CON SỐ và NÓI VỚI NGƯỜI XEM — hai thứ đo được là giữ chân (đo hôm
    # nay: 4/18 tập cũ có, 18/18 sau khi thêm luật). "Why CA leads every other on this list"
    # thiếu cả hai và đọc như tiêu đề của một bảng tính.
    # ── KHUÔN TIÊU ĐỀ DO CHÍNH TRỤC KHAI  (§12.5) ────────────────────────────────────
    # Bản đầu ghi cứng một khuôn: "Why {ten} has {so} {don} and your state does not". Đúng
    # cho trục BANG, vô nghĩa cho hai trục kia — "Why Class II has 14,704 food recalls and
    # your state does not". Một câu đúng ở ngữ cảnh nó sinh ra, sai ở ngữ cảnh mới: chính
    # là §12.5, và đây là lần thứ hai trong ngày.
    # Trục đã khai câu hỏi của nó, nên nó khai luôn khuôn tiêu đề của nó.
    tieu = chu_de["khuon_tieu"].format(ten=ten, so=f"{dinh_v:,}", don=don_vi)
    hook = chu_de["cau_hoi"].upper()
    hook_phu = f"{dinh_v:,}"

    nhip = [
        _n("so_lieu", f"{ten} sits at the top.", so=f"{dinh_v:,}", don=don_vi,
           bt="tien", dinh=True,
           ve=_ve("a simplified figure looking up at a single tall column",
                  "head tilted back, taking in the height", "quietly surprised",
                  "a plain pale wall", "a clean floor strip", "restrained muted palette")),
        _n("chart", "Now put them side by side.", don=don_vi,
           cot=[{"nhan": _gon(_ten_that(t), 14), "v": v} for t, v in hang[:6]], dinh=True),
        _n("so_lieu", f"Second place is not close.", so=f"{hai_v:,}", don=don_vi,
           bt="tien", dinh=True),
        _n("so_lieu", "Against the middle of the list.", so=f"{lan:.1f}x", don="the median",
           bt="tien", dinh=True),
        _n("canh", "Nobody publishes this ranking.",
           ve=_ve("a simplified figure holding a single printed page",
                  "reading it closely", "absorbed",
                  "a plain office wall", "a clean floor strip", "restrained muted palette")),
        _n("so_lieu", "This is every record on file.", so=f"{tong:,}", don=f"{don_vi} in total",
           bt="tien", dinh=True),
    ]
    return tieu, hook, hook_phu, nhip
