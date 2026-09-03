#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHẤM KỊCH BẢN GIẢI THÍCH — thang 100 điểm, TẤT ĐỊNH, chạy TRƯỚC khi dựng.  (3/9/2026)

Anh: *"template và kịch bản videos là quan trọng để có 1 đầu ra videos chất lượng cao nên em
phải nâng cấp chúng cho thật chất lượng hàng đầu thế giới đạt 100/100 điểm."*

── VÌ SAO CẦN TỆP NÀY ──────────────────────────────────────────────────────────────────────
Bộ Kling có `cham100.py` và nhờ nó mà chất lượng kịch bản đo được, so được, cải được. Bộ giải
thích thì **không có thước nào cho phần VIẾT**: `kiem_nhip` đo nhịp cắt, `kiem_khuon` đo lặp
khuôn câu, `kiem_trung` đo trùng — ba cổng ấy đều là cổng CHẶN cho ba lỗi cụ thể, không cái nào
trả lời được câu *"kịch bản này viết tốt đến đâu"*.

Hậu quả đo được: mười tám kênh chạy suốt nhiều phiên mà không ai biết kênh nào viết yếu hơn
kênh nào, nên mọi cải tiến đều là đoán.

── QUAN HỆ VỚI BA CỔNG ĐANG CÓ ─────────────────────────────────────────────────────────────
Ba nấc, đúng như §13.23 đã rút cho bộ Kling — và chọn nấc là một quyết định thật:

    máy sửa được          -> sửa im lặng ở `giai_thich` (ví dụ `_nhan`, `_danh_tu`)
    làm KÉM đi            -> TRỪ ĐIỂM ở tệp này, cạnh tranh với các trục khác
    làm HỎNG sản phẩm     -> CHẶN ở `kiem_nhip` / `kiem_khuon` / `kiem_trung`

Nên tệp này KHÔNG chặn. Nó chấm, và điểm dùng để so kênh với kênh, tập với tập.

── VÌ SAO TẤT ĐỊNH, KHÔNG HỎI AI ───────────────────────────────────────────────────────────
`cham_hinh.py` hỏi model và vì thế nó **cố vấn**: cùng một lưới, hai lần hỏi ra hai điểm. Thước
cho phần viết phải tái lập được, vì việc của nó là so sánh — mà so sánh trên một thước lung lay
thì mọi kết luận đều là nhiễu (§13.26: chênh lệch nhỏ hơn khoảng tin cậy thì không có gì để
giải thích).

── TÁM TRỤC, MỖI TRỤC MỘT LUẬT ĐÃ TRẢ GIÁ ─────────────────────────────────────────────────
    hook          16   §12.12  hook phải là NỘI DUNG cảnh đầu, không phải tấm biển
    nhịp câu      14   §12.11  muốn cảnh 2 giây thì câu phải 5–8 chữ
    cụ thể        14   §13.3   "chín trăm đô" chứ không "đắt"
    đơn vị Mỹ     10   §12.13  kênh Mỹ thì dặm, pound, Fahrenheit
    số cạnh vật   14   §12.11G con số luôn đứng cạnh hình của chính vật ấy
    đa dạng câu   12   §12.11  khuôn câu lặp là 'templated storylines'
    kết bằng cảnh  8   §12.12  đóng bằng cảnh, câu chốt để phụ đề nói
    không lặp khuôn 12  §14.9  đa dạng phải nằm ở thứ người xem NHÌN THẤY
"""
import argparse
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)

# Giọng đọc Mỹ ở nhịp bình thường ~2,8 chữ/giây — cùng con số `kiem_nhip` dùng, và nó đến từ
# đo tiếng đọc thật của `edge-tts`, không phải từ sách.
CHU_GIAY = 2.8

# Chữ chỉ ĐỘ LỚN mà không cho con số. Luật *"Not 'expensive' but 'nine hundred dollars'"* nằm
# trong bộ luật từ đầu nhưng chỉ được CHẤM, chưa bao giờ được đo trên bộ này (§13.3: một luật
# chỉ trừ điểm là một luật tuỳ chọn — nên ít nhất phải trừ điểm thật).
MO_HO = ("expensive", "cheap", "huge", "tiny", "a lot", "lots of", "massive", "enormous",
         "so much", "so many", "very big", "very small", "loads of", "tons of", "a ton of",
         "incredibly", "unbelievably", "insanely", "crazy", "way more", "way less")

# Đơn vị không phải Mỹ. `kg` và `km` bắt bằng biên từ vì `km` nằm trong "km/h" mà cũng nằm
# trong nhiều chuỗi khác; `metre/meter` bắt cả hai lối viết.
KHONG_MY = (r"\bkm\b", r"\bkm/h\b", r"\bkg\b", r"\bkilograms?\b", r"\bkilometres?\b",
            r"\bkilometers?\b", r"\bmetres?\b", r"\bmeters?\b", r"\bcelsius\b", r"°C\b",
            r"\blitres?\b", r"\bliters?\b", r"\btonnes?\b", r"\bcentimetres?\b")

TRUC = ("hook", "nhip_cau", "cu_the", "don_vi_my", "so_canh_vat",
        "da_dang_cau", "ket_bang_canh", "khong_lap_khuon")
TRAN = {"hook": 16, "nhip_cau": 14, "cu_the": 14, "don_vi_my": 10,
        "so_canh_vat": 14, "da_dang_cau": 12, "ket_bang_canh": 8, "khong_lap_khuon": 12}


def _loi(n) -> str:
    return str(n.get("loi") or n.get("nar") or "")


def _khuon_cau(t: str) -> str:
    """Rút KHUÔN của một câu: bỏ danh từ riêng và con số, giữ bộ khung.

    Hai câu *"A blue whale is 98 ft"* và *"A redwood tree is 350 ft"* khác nhau về nội dung mà
    giống hệt nhau về khuôn — và người xem nghe ra cái giống, không nghe ra cái khác. Đây đúng
    phép đo mà §13.5 đã rút: đo NỘI DUNG khi cần nội dung, đo KHUÔN khi cần khuôn.
    """
    t = re.sub(r"[\d][\d,\.]*", "«số»", t.lower())
    t = re.sub(r"\b[a-z]+ (?:ft|mph|lb|lbs|hours?|minutes?|days?|years?|dollars?)\b", "«đv»", t)
    t = re.sub(r"[^a-z«»\s]", " ", t)
    return " ".join(t.split())


def cham(nhip: list) -> dict:
    """Trả {"diem": 0-100, "truc": {...}, "loi": [...]}. Không ném lỗi với nhịp thiếu trường.

    KHÔNG dùng `n["x"]` ở bất cứ đâu: §14.7 đã trả giá cho đúng chuyện này — một tập thiếu một
    khối làm cả thước nổ `KeyError`, và thước nổ thì vòng lặp sinh mất luôn bản đang giữ. Thước
    phải CHẤM THẤP cho tập thiếu khối, không được chết theo nó.
    """
    d = {t: 0.0 for t in TRUC}
    bao = []
    if not nhip:
        return {"diem": 0, "truc": d, "loi": ["không có nhịp nào"]}

    cau = [_loi(n) for n in nhip]
    het = " ".join(cau).lower()

    # ── 1. HOOK ────────────────────────────────────────────────────────────────────────────
    # Ba điều kiện, mỗi điều một phần điểm — vì một hook hỏng theo ba cách khác nhau.
    h = cau[0] if cau else ""
    hw = len(h.split())
    if 1 <= hw <= 8:
        d["hook"] += 7
    elif hw <= 11:
        d["hook"] += 4
        bao.append(f"hook {hw} chữ — trên 8 là quá dài cho 3 giây đầu")
    else:
        bao.append(f"hook {hw} chữ — người xem quyết định lướt trong ~400ms")
    # Con số của hook nằm ở `so` (hiện TO giữa khung), không nằm trong lời đọc — bản đầu chỉ
    # soi lời và vì thế báo "hook không có số" cho 10/18 kênh trong khi hook thật luôn có số
    # chiếm một phần năm chiều cao khung. Thước phải nhìn đúng thứ người xem nhìn.
    h_all = f"{h} {nhip[0].get('so') or ''} {nhip[0].get('don') or ''}"
    # ── PHÉP ĐO MÂU THUẪN: NGUYÊN TẮC, KHÔNG DANH SÁCH  (3/9/2026) ─────────────────────────
    # Bản đầu liệt kê tám từ. Đọc tay 18 hook thật thì nó chấm trượt *"You would quit by noon."*
    # và *"You think it gets reused."* — hai hook MẠNH NHẤT trong cả bộ. Danh sách ngoại lệ là
    # danh sách vô hạn (§13.9): thêm "quit" rồi mai "regret", "lose", "owe".
    #
    # Nguyên tắc thật: một hook giữ chân khi nó **phủ định một điều người xem đang tin** HOẶC
    # **nói thẳng về chính người xem**. Hai thứ ấy viết được thành biểu thức:
    #     phủ định  : not · never · no · nobody · nothing · n't
    #     đảo chiều : actually · really · but · instead · turns out · wrong
    #     ngôi thứ hai + khẳng định : "you would/will/are/think/own/have/spend..."
    # Quét trên `h_all` (gồm cả chữ hiện trên khung) chứ không chỉ lời đọc: `survive` để
    # "PROBABLY NOT" ở trường `so`, và người xem ĐỌC được nó.
    if re.search(r"[\d]", h_all) or re.search(
            r"\b(not|never|no|nobody|nothing|n't|actually|really|but|instead|wrong|turns out)\b",
            h_all, re.I) or re.search(r"\byou(?:'\w+)?\s+\w+", h_all, re.I):
        d["hook"] += 5      # có số HOẶC có mâu thuẫn — hai cách duy nhất giữ chân ở giây đầu
    else:
        bao.append("hook không có số cũng không có mâu thuẫn — không có gì để ở lại")
    if (nhip[0].get("khuon") or "") != "the_chu":
        d["hook"] += 4      # §12.12: thẻ tiêu đề đè lên ba giây đầu là dấu hiệu nghiệp dư
    else:
        bao.append("nhịp đầu là THẺ CHỮ — hook phải là nội dung của cảnh, không phải tấm biển")

    # ── 2. NHỊP CÂU ────────────────────────────────────────────────────────────────────────
    # Nhịp cắt là việc của khâu VIẾT, không của khâu dựng (§12.11). Đo trực tiếp trên số chữ.
    dai = [len(c.split()) for c in cau if c]
    qua = [x for x in dai if x > 11]
    if dai:
        ti = len(qua) / len(dai)
        d["nhip_cau"] = round(14 * max(0.0, 1 - ti * 4), 1)
        if ti > 0.08:
            bao.append(f"{len(qua)}/{len(dai)} câu quá 11 chữ (~4s) — cảnh không cắt nhanh được")

    # ── 3. CỤ THỂ ──────────────────────────────────────────────────────────────────────────
    mh = [w for w in MO_HO if w in het]
    d["cu_the"] = max(0.0, 14 - len(mh) * 3.5)
    if mh:
        bao.append(f"chữ chỉ độ lớn mà không có số: {', '.join(mh[:4])}")

    # ── 4. ĐƠN VỊ MỸ ───────────────────────────────────────────────────────────────────────
    kmy = [p for p in KHONG_MY if re.search(p, het, re.I)]
    d["don_vi_my"] = max(0.0, 10 - len(kmy) * 5)
    if kmy:
        bao.append(f"đơn vị không phải Mỹ: {len(kmy)} loại — kênh Mỹ phải dặm/pound/°F")

    # ── 5. SỐ ĐỨNG CẠNH VẬT  (quy tắc G) ───────────────────────────────────────────────────
    sl = [n for n in nhip if (n.get("khuon") or "") == "so_lieu"]
    if sl:
        tron = sum(1 for n in sl if n.get("bt") or n.get("nenAnh") or n.get("ve"))
        d["so_canh_vat"] = round(14 * tron / len(sl), 1)
        if tron < len(sl):
            bao.append(f"{len(sl)-tron}/{len(sl)} khối số KHÔNG có hình của vật — "
                       f"con số trần không cho ai cảm giác gì")
    else:
        d["so_canh_vat"] = 14      # không có khối số thì không có lỗi này

    # ── 6. ĐA DẠNG KHUÔN CÂU ───────────────────────────────────────────────────────────────
    import collections
    kh = collections.Counter(_khuon_cau(c) for c in cau if len(c.split()) >= 3)
    nang = [(k, v) for k, v in kh.items() if v >= 3]
    d["da_dang_cau"] = max(0.0, 12 - sum(v - 2 for _, v in nang) * 3)
    if nang:
        bao.append(f"khuôn câu lặp {nang[0][1]} lần: «{nang[0][0][:40]}»")

    # ── 7. KẾT BẰNG CẢNH ───────────────────────────────────────────────────────────────────
    if (nhip[-1].get("khuon") or "") != "the_chu":
        d["ket_bang_canh"] = 8
    else:
        bao.append("kết bằng THẺ CHỮ — §12.12: đóng bằng cảnh, câu chốt để phụ đề nói")

    # ── 8. KHÔNG LẶP KHUÔN DỰNG ────────────────────────────────────────────────────────────
    # Bản đầu phạt mọi chuỗi BA nhịp cùng khuôn. Đọc tay các ca nó bắt (§13.22) thì hai phần ba
    # là BẮT OAN, và oan theo hai kiểu khác nhau:
    #
    #   · ba nhịp `canh` liền nhau  — ba CẢNH khác nhau, mỗi cảnh một hình. Khuôn giống nhau
    #     nhưng người xem thấy ba bức hình khác nhau, không thấy lặp.
    #   · `howlong` nhịp 10-12: `so_lieu` ×3 cho đi bộ · ô tô · máy bay — đây đúng **quy tắc B**
    #     của chính bộ này (§12.11): *mệnh đề song song thì khung hình song song*. Phạt nó là
    #     phạt đúng thứ bộ luật yêu cầu.
    #
    # Ca hỏng THẬT nằm ngay cạnh: nhịp 9 và 10 cùng hiện **8.8** — hai khối số liền nhau nói
    # đúng một con số. Đó mới là chỗ người xem thấy màn hình đứng yên.
    #
    # Nên đo hai thứ, không đo "ba nhịp cùng khuôn":
    #   a) hai nhịp liền nhau hiện CÙNG MỘT SỐ  -> lặp thật, phạt nặng
    #   b) từ BỐN nhịp cùng khuôn trở lên       -> quá dài cho một chuỗi song song
    trung_so = 0
    for j in range(1, len(nhip)):
        s1 = str(nhip[j - 1].get("so") or "").strip()
        s2 = str(nhip[j].get("so") or "").strip()
        if s1 and s1 == s2:
            trung_so += 1
    bon = 0
    run, pre = 1, None
    for n in nhip:
        kh = n.get("khuon")
        if kh and kh == pre and kh != "canh":
            run += 1
            if run == 4:
                bon += 1
        else:
            run = 1
        pre = kh
    d["khong_lap_khuon"] = max(0.0, 12 - trung_so * 6 - bon * 3)
    if trung_so:
        bao.append(f"{trung_so} cặp nhịp liền nhau hiện CÙNG MỘT SỐ — màn hình đứng yên")
    if bon:
        bao.append(f"{bon} chuỗi từ 4 nhịp cùng khuôn trở lên (song song 3 thì được, 4 là dài)")

    return {"diem": round(sum(d.values())), "truc": {k: round(v, 1) for k, v in d.items()},
            "loi": bao}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--tap", type=int, default=3)
    ap.add_argument("--tep", nargs="*", default=[])
    ap.add_argument("--long", action="store_true")
    a = ap.parse_args()

    if a.tep:
        for t in a.tep:
            try:
                nh = json.load(open(t, encoding="utf-8")).get("nhip") or []
            except Exception as e:
                print(f"  ⚠ {os.path.basename(t)}: {e}")
                continue
            r = cham(nh)
            print(f"  {os.path.basename(t):38s} {r['diem']:3d}/100")
            for x in r["loi"][:3]:
                print(f"        · {x}")
        return 0

    import giai_thich as G
    ds = [k["ma"] for k in G.KENH] if not a.kenh else [a.kenh]
    tong, n = 0, 0
    xau = []
    for m in ds:
        ds_diem = []
        for i in range(a.tap):
            try:
                # `kich_ban` — CÙNG nguồn mà `mot_tap` dựng. Bản đầu gọi `BO_SINH[m](i)[3]`
                # cho tiện và chấm sai: nhịp hook chèn ở `mot_tap`, nên thước thấy 17/18 kênh
                # "hook không có số" trong khi hook thật luôn có số. Một phép đo đọc từ nguồn
                # khác nguồn sản phẩm dùng thì nó đo một sản phẩm không tồn tại (§13.15).
                nh = G.kich_ban(m, i, long=a.long)[4]
            except Exception as e:
                xau.append(f"{m} tập {i}: {type(e).__name__}")
                continue
            r = cham(nh)
            ds_diem.append(r["diem"])
            tong += r["diem"]
            n += 1
            if i == 0 and r["loi"]:
                xau.append(f"{m}: " + " · ".join(r["loi"][:2]))
        if ds_diem:
            tb = sum(ds_diem) / len(ds_diem)
            dau = "✅" if tb >= 90 else ("⚠" if tb >= 80 else "❌")
            print(f"  {dau} {m:11s} {tb:5.1f}/100   {ds_diem}")
    if n:
        print(f"\n  TRUNG BÌNH {tong/n:.1f}/100 trên {n} tập")
    for x in xau[:12]:
        print(f"    · {x}")
    # KHÔNG chặn — xem đầu tệp, nấc ba. Trả 0 luôn.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
