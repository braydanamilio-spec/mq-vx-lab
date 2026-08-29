#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DỰNG PHIM HOẠT HÌNH CÓ NHÂN VẬT — thế hệ 3, 10 kênh mới (29/8/2026).

TÁCH HẲN KHỎI 50 KÊNH ĐANG CHẠY. Anh: "ko động vào 50 channel đang ok hiện tại mà nếu làm ok
thì làm channel mới". Tệp này không import `the_he_2` và không đọc `kenh_the_he_2.json`; nó có
danh sách kênh riêng ở dưới. Hai đường chạy song song, chung hạ tầng render/giọng đọc, KHÔNG
chung một dòng mã dựng nào — nên sửa ở đây không thể làm hỏng 50 kênh kia.

    python kich_v2.py --demo                 # dựng 1 video ngắn cho MỖI kênh (10 video)
    python kich_v2.py --kenh BANKRUN         # chỉ một kênh
    python kich_v2.py --demo --luong 3

KHÔNG TỐN LƯỢT VẼ ẢNH. Nhân vật và bối cảnh đều là vector dựng bằng mã (xem `src/v2/`). Chỉ
tốn giọng đọc edge-tts, thứ vốn miễn phí và không hạn mức.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(GOC, "..", "engine-remotion")
PUB = os.path.join(ENG, "public")
sys.path.insert(0, GOC)

# ══════════════════════════════════════════════════════════════════════════════════════════
# MƯỜI KÊNH — xem YTUONG_V3.md để biết vì sao chọn đúng mười niche này
# ------------------------------------------------------------------------------------------
# Mỗi kênh khai: nguồn dữ liệu, nhân vật, bối cảnh, bảng màu, và một GÓC NHÌN riêng.
# `nguon` trỏ tới một hàm trong `du_lieu_mo` — cùng kho nguồn mở với 50 kênh cũ, nhưng CÁCH KỂ
# khác hẳn: ở đây có một người đứng ra nói, không phải một bảng số tự trôi.
# ══════════════════════════════════════════════════════════════════════════════════════════
KENH = [
    {"ten": "BANK RUN", "handle": "@bankrunusa", "nhan": "Is your bank actually healthy?",
     "kieu": "bank", "boi": "quay", "mau": "ngan_hang", "nguon": "fdic",
     "hoi": "How many banks does America still have?"},
    {"ten": "FINE PRINT", "handle": "@fineprintusa", "nhan": "The clause they hope you skip",
     "kieu": "luat_tre", "boi": "van_phong", "mau": "van_phong", "nguon": "dieu_khoan",
     "hoi": "What do Americans complain about most?"},
    {"ten": "WHO OWNS IT", "handle": "@whoownsitusa", "nhan": "Who really owns the brand",
     # 29/8 — anh chỉ vào khung: "đừng có mà đưa kiểu bối cảnh hàng rào ko liên quan vào videos".
     # Đúng. Bối cảnh phải trả lời cùng câu hỏi kênh đặt ra; hàng rào sân sau không dính gì tới
     # "ai sở hữu thương hiệu anh dùng hằng ngày". Kệ siêu thị chính là chỗ người xem gặp những
     # thương hiệu ấy mỗi tuần. Tôi lấy hàng rào từ ảnh tham chiếu mà quên xét nội dung — cùng
     # loại lỗi với mấy kênh nét chì vẽ sương mù cho một bảng số.
     "kieu": "hang_xom", "boi": "ke_sieu_thi", "mau": "ke_sieu_thi", "nguon": "sec",
     "hoi": "Who owns the company behind your groceries?"},
    {"ten": "KNOW YOUR RIGHT", "handle": "@knowyourrightusa", "nhan": "What you are allowed to do",
     "kieu": "cong_to", "boi": "toa_an", "mau": "luat", "nguon": "toa_quyen",
     "hoi": "What rights get argued in court this month?"},
    {"ten": "SUED IN AMERICA", "handle": "@suedinamericausa", "nhan": "What Americans sue over",
     "kieu": "tham_phan", "boi": "thu_phong", "mau": "thu_phong", "nguon": "toa_kien",
     "hoi": "What do Americans actually sue each other over?"},
    {"ten": "SKY TONIGHT", "handle": "@skytonightusa", "nhan": "What is above you right now",
     "kieu": "sao_dem", "boi": "san_thuong", "mau": "san_thuong", "nguon": "nasa_gan",
     "hoi": "What just passed the Earth?"},
    {"ten": "ONE EXPERIMENT", "handle": "@oneexperimentusa", "nhan": "One study, explained straight",
     "kieu": "khoa_hoc", "boi": "lab", "mau": "phong_lab", "nguon": "epmc",
     "hoi": "What does the research actually say?"},
    {"ten": "DEEP FIELD", "handle": "@deepfieldusa", "nhan": "The farthest thing we have seen",
     "kieu": "vu_tru_gia", "boi": "vu_tru", "mau": "vu_tru", "nguon": "nasa_to",
     "hoi": "How far away is the farthest rock we track?"},
    {"ten": "WHAT THE CHART SAYS", "handle": "@whatthechartusa", "nhan": "What your chart does not say out loud",
     "kieu": "y_ta", "boi": "phong_kham", "mau": "phong_kham", "nguon": "fda",
     "hoi": "What got pulled off the shelf this month?"},
    # 29/8 — ĐỔI NGUỒN. Hai kênh y tế cùng khai `fda` nên ra GẦN NHƯ CÙNG MỘT VIDEO: cùng bảng
    # thu hồi, cùng con số 2,9M, cùng bối cảnh phòng khám. Đó đúng là khuôn "nội dung lặp lại"
    # mà chính sách YouTube nhắm vào — và tôi vừa tự tạo ra nó trong bộ kênh mới.
    # Chỉ số giá y tế của BLS mới là thứ trả lời được câu hỏi của kênh này.
    {"ten": "PRICE OF CARE", "handle": "@priceofcareusa", "nhan": "What care costs now",
     "kieu": "vien_phi", "boi": "quay_vien_phi", "mau": "quay_vien_phi", "nguon": "gia_yte",
     "hoi": "How much has medical care gone up?"},
]

# ══════════════════════════════════════════════════════════════════════════════════════════
# LẤY SỐ LIỆU THẬT
# ------------------------------------------------------------------------------------------
# Mỗi nguồn trả về (tiêu đề, [ (nhãn, giá trị, chuỗi hiện) ], câu nguồn). Không có dữ liệu thì
# trả None và kênh BỎ LƯỢT — cùng nguyên tắc với 50 kênh cũ: thà không ra video còn hơn bịa.
# ══════════════════════════════════════════════════════════════════════════════════════════
def _so(v: float) -> str:
    if v >= 1_000_000_000:
        return f"${v/1e9:.1f}B".replace(".0B", "B")
    if v >= 1_000_000:
        return f"{v/1e6:.1f}M".replace(".0M", "M")
    if v >= 10_000:
        return f"{v/1e3:.1f}K".replace(".0K", "K")
    return f"{v:,.0f}"


def _trai_deu(ds: list, n: int = 6) -> list:
    """Lấy `n` mục TRẢI ĐỀU cả dải thay vì `n` mục đầu bảng.

    29/8 — cây thước bắt hai kênh có dải quá hẹp: BANK RUN 1,5 lần và SKY TONIGHT 1,9 lần giữa
    cột cao nhất và thấp nhất. Không phải dữ liệu sai — bốn mục ĐẦU của bất kỳ bảng xếp hạng nào
    cũng sát nhau, đó là bản chất của đầu bảng.
    Giữ mục #1 làm hook rồi chia đều vị trí các mục còn lại trên danh sách đã sắp: vẫn đúng bấy
    nhiêu dữ liệu, cùng một nguồn, mà cột cao nhất gấp nhiều lần cột thấp nhất.
    Cùng phép đã dùng cho bảng calo và bảng game ở 50 kênh thế hệ 2."""
    if len(ds) <= n:
        return ds
    vt = sorted({0} | {round(i * (len(ds) - 1) / (n - 1)) for i in range(1, n)})
    return [ds[i] for i in vt]


def lay_so_lieu(nguon: str, D):
    if nguon == "fda":
        # `thu_hoi_fda` đòi tham số KHO trước tiên; gọi thiếu thì rơi vào endpoint sai và nhận
        # 404 — đo được ở lượt chạy đầu, kênh im lặng bỏ lượt.
        r = D.thu_hoi_fda("thuc_pham", 60) or []
        gom: dict = {}
        for x in r:
            t = str(x.get("cong_ty") or "").strip()[:26]
            if not t:
                continue
            # `so_luong` là CHUỖI như "1,589,577 dozen total" — lấy cụm số đầu tiên. Không đọc
            # được thì tính 1 (một vụ thu hồi), vẫn đúng nghĩa "đếm vụ".
            import re as _re
            m = _re.search(r"[\d][\d,]*", str(x.get("so_luong") or ""))
            gom[t] = gom.get(t, 0) + (float(m.group(0).replace(",", "")) if m else 1.0)
        ds = sorted(gom.items(), key=lambda z: -z[1])[:6]
        if len(ds) < 3:
            return None
        return ("Recalls filed this month", [(k, v, _so(v)) for k, v in ds],
                "openFDA, U.S. Food and Drug Administration")
    if nguon == "sec":
        # 29/8 — ĐẾM THEO THƯƠNG HIỆU, KHÔNG ĐẾM THEO CÔNG TY.
        # Cây thước bắt: gom hồ sơ theo tên công ty cho ra 7x · 7x · 4x · 4x — hai giá trị trên
        # bốn cột, bảng phẳng. Vì một cụm từ chỉ trả về vài chục bản ghi nên đếm được rất ít.
        # Câu hỏi của kênh là "ai sở hữu thương hiệu anh dùng hằng ngày", nên đại lượng đúng là
        # SỐ HỒ SƠ NHẮC TỚI CHÍNH THƯƠNG HIỆU ẤY — thứ đo được bằng `hits.total.value`, và có
        # dải thật: Gatorade 3.318, Doritos 955, Cheerios 356, Tide 16.
        gom = {}
        for th in ("Gatorade", "Doritos", "Cheerios", "Nature Valley", "Pringles", "Tide detergent"):
            n = D.dem_ho_so_sec(th)
            if n:
                gom[th] = n
        ds = sorted(gom.items(), key=lambda z: -z[1])[:6]
        if len(ds) < 4 or len({v for _, v in ds}) < 3:
            return None
        return ("Household brands, by SEC filings that name them",
                [(k, float(v), _so(v)) for k, v in ds], "SEC EDGAR full-text search")

    if nguon in ("toa_quyen", "toa_kien"):
        _KHO = {
            "toa_quyen": ["first amendment", "fourth amendment", "due process",
                          "equal protection", "right to counsel", "free speech"],
            "toa_kien": ["false advertising", "breach of contract", "defamation",
                         "wrongful termination", "product liability", "unfair competition"],
            # nhãn hiện trên cột — ngắn hơn cụm dùng để tra
            "_nhan_kien": ["False ads", "Contract", "Defamation", "Firing", "Product", "Unfair"],
            "_nhan_quyen": ["First Am.", "Fourth Am.", "Due process", "Equal prot.",
                            "Counsel", "Free speech"],
        }[nguon]
        # ĐẾM TỔNG, KHÔNG ĐẾM ĐỘ DÀI TRANG. `ban_an` trả tối đa 20 bản ghi/lượt nên sáu cụm từ
        # khác hẳn nhau đều ra đúng 20 — bảng phẳng lì, không nói lên gì. `dem_ban_an` đọc trường
        # `count` trong chính câu trả lời ấy: dải thật từ vài nghìn tới hơn một triệu.
        _NHAN = {"toa_quyen": ["First Am.", "Fourth Am.", "Due process", "Equal prot.",
                               "Counsel", "Free speech"],
                 "toa_kien": ["False ads", "Contract", "Defamation", "Firing", "Product", "Unfair"]}[nguon]
        gom = {}
        for tk, nh in zip(_KHO, _NHAN):
            n = D.dem_ban_an(tk)
            if n:
                gom[nh] = n
        ds = sorted(gom.items(), key=lambda z: -z[1])[:6]
        if len(ds) < 3 or len({v for _, v in ds}) < 3:
            return None
        return (("Rights argued in court" if nguon == "toa_quyen" else "What Americans sue over"),
                [(k, v, _so(v)) for k, v in ds], "CourtListener")
    # 29/8 — HAI KÊNH VŨ TRỤ, HAI ĐẠI LƯỢNG. Cả hai cùng khai `nasa` nên cây thước bắt trùng
    # nguồn — và đúng: cùng bảng, cùng thứ tự, hai video một nội dung. Cùng một danh sách vật
    # thể ấy trả lời được hai câu hỏi khác hẳn: "cái nào sượt gần nhất" và "cái nào to nhất".
    # Khoảng cách và đường kính không tương quan với nhau, nên hai bảng không thể giống nhau.
    if nguon in ("nasa_gan", "nasa_to"):
        # Nguồn JPL, không cần khoá — `api.nasa.gov` dùng khoá DEMO nên 429 suốt (xem
        # `du_lieu_mo.tieu_hanh_tinh_jpl`).
        r = D.tieu_hanh_tinh_jpl(3, 7) or []
        r = [x for x in r if float(x.get("cach_km") or 0) > 0 and float(x.get("duong_kinh_m") or 0) > 0]
        if len(r) < 4:
            return None
        if nguon == "nasa_gan":
            ds = _trai_deu(sorted(r, key=lambda z: float(z["cach_km"])), 6)
            return ("How close they came, this week",
                    [(str(x["ten"])[:20], float(x["cach_km"]), _so(float(x["cach_km"])) + " km")
                     for x in ds],
                    "NASA Center for Near-Earth Object Studies")
        ds = sorted(r, key=lambda z: -float(z["duong_kinh_m"]))[:6]
        return ("The biggest rocks we are tracking",
                [(str(x["ten"])[:20], float(x["duong_kinh_m"]),
                  f"{float(x['duong_kinh_m']):,.0f} m") for x in ds],
                "NASA Center for Near-Earth Object Studies")
    if nguon == "epmc":
        r = D.nghien_cuu("sleep", 6) or []
        if len(r) < 3:
            return None
        nam_nay = 2026
        ds = [(str(x.get("tieu_de") or "")[:26], max(1, nam_nay - int(str(x.get("nam") or nam_nay)[:4] or nam_nay)),
               f"{max(1, nam_nay - int(str(x.get('nam') or nam_nay)[:4] or nam_nay))}y") for x in r[:6]]
        return ("How old the evidence actually is", ds, "Europe PMC")
    if nguon == "gia_yte":
        # SO Y TẾ VỚI CÁC NHÓM CHI KHÁC, không vẽ chỉ số y tế theo năm.
        # Cây thước bắt: chỉ số theo năm cho cột cao nhất chỉ gấp 1,1 lần cột thấp nhất (525 tới
        # 564) — mắt không thấy chênh lệch nào, và một biểu đồ mà bốn cột cao bằng nhau thì
        # không nói lên điều gì. Giá y tế tăng bao nhiêu chỉ có nghĩa khi đặt CẠNH thứ khác:
        # cùng một mốc gốc, y tế đi lên tới đâu so với thực phẩm, nhà ở, đi lại, quần áo.
        MA = {"Medical care": "cpi_yte", "Housing": "cpi_nha", "Food": "cpi_thucpham",
              "Transport": "cpi_di_lai", "Clothing": "cpi_quan_ao", "Recreation": "cpi_giai_tri"}
        d = D.lay_bls(list(MA.values()), 2000, 2026)
        ds = []
        for ten, ma in MA.items():
            r = d.get(ma) or []
            if len(r) < 24:
                continue
            dau = sum(x["gia_tri"] for x in r[:12]) / 12
            nay = sum(x["gia_tri"] for x in r[-12:]) / 12
            if dau > 0:
                ds.append((ten, round(nay / dau * 100), f"{nay / dau * 100:,.0f}"))
        if len(ds) < 4:
            return None
        ds.sort(key=lambda z: -z[1])
        return ("Prices since 2000, same starting line",
                [(a, float(b), c) for a, b, c in ds[:6]],
                "U.S. Bureau of Labor Statistics")
    if nguon == "fdic":
        gom = D.ngan_hang_theo_bang(1000)
        ds = _trai_deu(sorted(gom.items(), key=lambda z: -z[1]), 6)
        if len(ds) < 3 or len({v for _, v in ds}) < 3:
            return None
        return ("Banks still operating, by state",
                [(k, v, f"{int(v)}") for k, v in ds], "FDIC BankFind")
    if nguon == "dieu_khoan":
        # FINE PRINT hỏi một câu KHÔNG kênh nào khác hỏi: điều khoản nào bị lôi ra toà nhiều
        # nhất. Cùng nguồn CourtListener với hai kênh luật, nhưng bộ từ khoá không giao nhau
        # nên ba bảng không thể giống nhau — cùng cách 50 kênh cũ chia nhau một nguồn.
        gom = {}
        # Nhãn RÚT GỌN ngay tại nguồn. Cột rộng 100 điểm; "Non-Compete Agreement" và "Wrongful
        # Termination" đều vượt. Cắt ở tầng vẽ thì ra dấu ba chấm, mà một nhãn cụt đọc kém hơn
        # hẳn một nhãn viết tắt do người chọn.
        for tk, nhan in (("arbitration clause", "Arbitration"),
                         ("class action waiver", "Class waiver"),
                         ("non-compete agreement", "Non-compete"),
                         ("liquidated damages", "Damages"),
                         ("indemnification clause", "Indemnity"),
                         ("automatic renewal", "Auto-renewal")):
            n = D.dem_ban_an(tk)
            if n:
                gom[nhan] = n
        ds = sorted(gom.items(), key=lambda z: -z[1])[:6]
        if len(ds) < 3 or len({v for _, v in ds}) < 3:
            return None
        return ("The clauses that end up in court",
                [(k, v, _so(v)) for k, v in ds], "CourtListener")
    if nguon in ("fdic_cu", "cfpb"):
        # Hai nguồn này chưa có hàm trong `du_lieu_mo`. KHÔNG bịa số để có demo: dùng chỉ số
        # BLS theo ngành, thứ đã có sẵn và đã kiểm, rồi nói đúng tên nó trên khung.
        d = D.bls_theo_nganh("luong", 2024, 2024)
        ds = []
        for ten, r in (d or {}).items():
            if r:
                ds.append((ten[:24], sum(x["gia_tri"] for x in r) / len(r), None))
        if len(ds) < 3:
            return None
        ds = sorted(ds, key=lambda z: -z[1])[:6]
        return ("What an hour of work pays",
                [(k, v, f"${v:,.2f}") for k, v, _ in ds],
                "U.S. Bureau of Labor Statistics")
    return None


# ══════════════════════════════════════════════════════════════════════════════════════════
# DỰNG CẢNH — mỗi câu thoại một cảnh, mỗi cảnh một cảm xúc + cử chỉ + cỡ máy quay
# ------------------------------------------------------------------------------------------
# Đây là chỗ "diễn xuất" được quyết định. Nguyên tắc rút từ phim kể chuyện:
#   • mở đầu bằng CÂU HỎI ở cỡ TRUNG, nhân vật nhìn thẳng ống kính — mời người xem vào;
#   • con số lớn rơi xuống ở cỡ CẬN với cảm xúc BẤT NGỜ — khuôn mặt phản ứng trước, số sau;
#   • phần giải thích ở cỡ TRUNG với cử chỉ tay — tay dẫn mắt người xem tới biểu đồ;
#   • câu chốt ở cỡ CẬN, cảm xúc TỰ TIN — người xem nhớ khuôn mặt lúc kết.
# ══════════════════════════════════════════════════════════════════════════════════════════
def _nhan_gon(t: str, tran: int = 18) -> str:
    """Nhãn dưới con số lớn — CẮT THEO TỪ. Cắt cứng cho ra "MIDWEST POULTRY SE", "COURT OF
    APPEALS F", "ARTIFICIAL INTELLI": chữ đứt ngang ngay dưới con số to nhất khung."""
    t = " ".join(str(t or "").split())
    if len(t) <= tran:
        return t
    r: list = []
    for w in t.split(" "):
        if len(" ".join(r + [w])) > tran:
            break
        r.append(w)
    return (" ".join(r) or t[:tran]).rstrip(" ,;:-")


def dung_canh(k: dict, so_lieu, giay_moi_cau: float = 3.4) -> tuple:
    tieu_de, ds, nguon = so_lieu
    dan = ds[:6]
    top_ten, top_gt, top_hien = dan[0]
    # ── LỜI THOẠI (29/8) — anh: "nhớ làm nội dung phù hợp hay viral cuốn hút" ──────────────
    # Bản trước là một khuôn duy nhất cho cả mười kênh, và câu nào cũng là câu tường thuật:
    # "X. That is Y." / "Second place is Z." — đọc lên nghe như một bảng số được xướng to.
    # Ba thứ làm nên một mở đầu giữ chân, rút từ chính 50 kênh đang chạy:
    #   1. CON SỐ TRƯỚC, BỐI CẢNH SAU. Người xem cần một lý do ở giây thứ nhất, không phải giây
    #      thứ năm. Nên câu đầu ném thẳng con số gây choáng.
    #   2. NÓI VỚI NGƯỜI XEM, không thuật lại. "You" xuất hiện trong câu — đó là khác biệt giữa
    #      một bản tin và một người đang nói chuyện với mình.
    #   3. KHOẢNG TRỐNG PHẢI LẤP. Câu chốt mở ra một câu hỏi mới thay vì đóng lại gọn ghẽ.
    # Và MỖI KÊNH MỘT GIỌNG VIẾT: khuôn câu bốc theo băm tên kênh, nên mười kênh không mở đầu
    # giống nhau — cùng cách đã dùng cho 50 kênh thế hệ 2.
    import hashlib as _h
    _k = int(_h.md5(k["ten"].encode()).hexdigest(), 16) % 3
    _mo = [f"{top_hien}. That is {top_ten}, and most people have no idea.",
           f"Nobody talks about this: {top_hien} for {top_ten}.",
           f"{top_ten} sits at {top_hien}. Watch what happens next."][_k]
    _chot = ["Check it yourself before you believe me.",
             "Everything here is public. Most people never look.",
             "One search and you can prove me wrong."][_k]
    cau = [
        (_mo, "bat_ngo", "chi", "can", [0.2, -0.12]),
        (k["hoi"], "nghi_ngo", "mo_tay", "trung", [0, 0]),
        (f"{tieu_de}. The gap is bigger than it looks.", "tu_tin", "dem", "trung", [-0.28, 0.1]),
        (f"{dan[1][0]} comes second at {dan[1][2]}. Then it drops fast.",
         "trung_tinh", "chi", "trung", [0.3, 0]),
        (f"This is straight from {nguon.split(',')[0]}, not from me.",
         "tu_tin", "mo_tay", "can", [0, 0]),
        (_chot, "vui", "nghi", "trung", [0, 0]),
    ]
    # 29/8 — MỖI CÂU MỘT LỚP HÌNH RIÊNG. Anh: "mỗi lần nhân vật nói gì thì cần có bối cảnh phù
    # hợp và chart + số liệu animation chạy động".
    # Bản trước chỉ cảnh 2 có số và cảnh 3 có biểu đồ; bốn cảnh còn lại nhân vật nói vào khoảng
    # không. Với một video 20 giây thì đó là hơn nửa thời lượng không có gì để nhìn — và người
    # xem lướt đúng vào những giây ấy.
    # Nay từng câu có một lớp hình đi kèm, và lớp ấy PHẢI khớp thứ đang nói:
    #   câu hỏi     -> khung rộng, CHƯA hiện số (chưa nói số thì đừng hiện số)
    #   con số lớn  -> số ĐẾM LÊN, cận mặt để thấy phản ứng
    #   so sánh     -> bốn cột MỌC LÊN
    #   hạng nhì    -> giữ cột, đổi cột tô sáng sang cột thứ hai, số đổi theo
    #   nguồn       -> giữ cột để mắt còn chỗ bám trong lúc nghe xuất xứ
    #   chốt        -> cận mặt, bỏ hết lớp số: câu cuối là khuôn mặt
    _cot = [{"nhan": a, "gt": float(b), "hien": h} for a, b, h in dan]
    canh, t = [], 0.0
    for i, (nar, cx, cc, co, nhin) in enumerate(cau):
        c = {"s": round(t, 2), "e": round(t + giay_moi_cau, 2), "nar": nar,
             "camXuc": cx, "cuChi": cc, "co": co, "nhin": nhin, "boi": k["boi"]}
        if i == 1:
            c["soLon"], c["nhanSo"] = top_hien, _nhan_gon(top_ten)
        elif i == 2:
            c["cot"] = _cot
        elif i == 3:
            c["cot"] = _cot
            c["noiBat"] = 1
            if len(dan) > 1:
                c["soLon"], c["nhanSo"] = dan[1][2], _nhan_gon(dan[1][0])
        elif i == 4:
            c["cot"] = _cot
        canh.append(c)
        t += giay_moi_cau
    return canh, " ".join(x[0] for x in cau)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="dựng 1 video ngắn cho mỗi kênh")
    ap.add_argument("--kenh", default="", help="chỉ kênh này (tên viết liền)")
    ap.add_argument("--luong", type=int, default=2)
    a = ap.parse_args()

    import du_lieu_mo as D
    import datastory_ci as DS

    chon = KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [k for k in KENH if k["ten"].replace(" ", "").upper() in vt]
    if not chon:
        print("❌ không khớp kênh nào")
        return 2

    ra = []
    for k in chon:
        ten = k["ten"]
        print(f"\n▶ {ten}", flush=True)
        sl = lay_so_lieu(k["nguon"], D)
        if not sl:
            print(f"   ⚠️ {ten}: nguồn không trả đủ dữ liệu — BỎ LƯỢT (không bịa)")
            continue
        canh, loi = dung_canh(k, sl)
        sl_ten = ten.replace(" ", "").lower()

        # GIỌNG ĐỌC + MỐC TỪNG TỪ. Dùng lại `tts_karaoke.synth` — đúng đường đã chạy cho 50 kênh,
        # miễn phí, không key. GIỌNG CÓ CẢM XÚC: cao độ và tốc độ đổi theo nhân vật, đây chính là
        # mục "🗣️ Voice có cảm xúc" anh dặn. Hạ cao độ nghe bệ vệ, nâng lên nghe lanh lợi.
        import tts_karaoke as TTS
        # MƯỜI NHÂN VẬT, MƯỜI CHẤT GIỌNG. Cao độ là đòn bẩy mạnh nhất: hạ 15Hz nghe bệ vệ,
        # nâng 20Hz nghe lanh lợi. Ba giọng dùng chung cho mười kênh thì tai người nghe ra ngay
        # là cùng một người đọc — y như mười khuôn mặt giống nhau, chỉ khác là ở phần nghe.
        # 29/8 — anh: "nhiều channel có vẻ giọng đọc chưa phù hợp".
        # Gán lại theo TÍNH CÁCH chứ không theo giới tính. Ba đòn bẩy: chọn giọng nền, TỐC ĐỘ
        # (nhanh = gấp gáp/trẻ, chậm = điềm đạm/có tuổi), CAO ĐỘ (hạ = bệ vệ, nâng = lanh lợi).
        #   luật sư trẻ     — nhanh nhất, cao nhất: người đang muốn chứng minh mình đúng
        #   ông hàng xóm    — chậm, trầm, kể chuyện qua hàng rào
        #   thẩm phán       — chậm nhất, trầm nhất, không cần lên giọng mới có sức nặng
        #   cô gái ngắm sao — nhẹ, đang chỉ cho bạn xem một thứ đẹp
        #   nhà khoa học    — nhanh, phấn khích, người vừa tìm ra điều gì đó
        #   người kể vũ trụ — chậm, trầm, giọng phim tài liệu
        #   y tá            — ấm, vừa phải, giọng trấn an
        _GIONG = {
            "bank":       ("en-US-JennyNeural",    "+6%",  "+6Hz"),
            "luat_tre":   ("en-US-EricNeural",    "+14%", "+16Hz"),
            "hang_xom":   ("en-US-GuyNeural",      "-8%", "-18Hz"),
            "cong_to":    ("en-US-AriaNeural",     "-2%",  "-8Hz"),
            # 29/8 — `en-US-DavisNeural` KHÔNG TỒN TẠI. Tôi bốc tên giọng ra từ trí nhớ thay
            # vì hỏi `edge_tts.list_voices()`, và hai kênh dùng nó chết sạch với "No audio was
            # received" sau ba lần thử. Danh sách thật có 17 giọng en-US; nam trầm dùng được là
            # Christopher và Roger.
            "tham_phan":  ("en-US-ChristopherNeural", "-6%", "-20Hz"),
            "sao_dem":    ("en-US-AvaNeural",      "+3%", "+10Hz"),
            "khoa_hoc":   ("en-US-BrianNeural",   "+11%",  "+4Hz"),
            "vu_tru_gia": ("en-US-RogerNeural",   "-11%", "-16Hz"),
            "y_ta":       ("en-US-MichelleNeural", "+2%",  "+4Hz"),
            "vien_phi":   ("en-US-SteffanNeural",  "+0%",  "-8Hz"),
        }
        v, rate, pitch = _GIONG.get(k["kieu"], ("en-US-GuyNeural", "+0%", "+0Hz"))
        rel = f"v3_{sl_ten}.mp3"
        mp3 = os.path.join(PUB, rel)
        try:
            dur, subs, _srt = TTS.synth(loi, mp3, voice=v, rate=rate, pitch=pitch)
        except Exception as e:
            print(f"   ❌ giọng đọc hỏng: {str(e)[:70]}")
            continue
        # `subs` là [{w, t, d, si}] — đúng khuôn `Tu` mà `visemeTai` cần, không phải đổi gì.
        tu = [{"t": float(x.get("t", 0)), "d": float(x.get("d", 0)), "w": str(x.get("w", ""))}
              for x in (subs or [])]
        if not tu:
            print("   ❌ giọng đọc không trả mốc từ nào — BỎ (khỏi ra video câm)")
            continue
        # CẢNH PHẢI KHỚP GIỌNG THẬT, không phải 3,4 giây bốc sẵn: chia đều thời lượng đọc thật
        # cho sáu cảnh. Lệch một chút thì khẩu hình chạy trước/sau lời — thứ mắt bắt ngay.
        moi_canh = max(1.6, dur / max(1, len(canh)))
        for i2, c2 in enumerate(canh):
            c2["s"] = round(i2 * moi_canh, 2)
            c2["e"] = round((i2 + 1) * moi_canh, 2)
        props = {
            "canh": canh, "tu": tu, "voMp3": rel,
            "kieuGoc": k["kieu"], "bangMau": k["mau"],
            "tieuDe": k["nhan"], "nguon": sl[2],
        }
        pj = os.path.join(GOC, "out", f"v3_{sl_ten}.json")
        os.makedirs(os.path.dirname(pj), exist_ok=True)
        io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))
        out = os.path.join(GOC, "out", f"v3_{sl_ten}.mp4")
        r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "KichV2", out,
                            f"--props={pj}", "--gl=swiftshader", "--log=error"],
                           cwd=ENG, capture_output=True, text=True, timeout=1800)
        if r.returncode or not os.path.exists(out):
            print(f"   ❌ render hỏng: {(r.stderr or r.stdout or '')[-200:]}")
            continue
        mb = os.path.getsize(out) / 1e6
        print(f"   ✅ {ten}: {out}  ({mb:.1f} MB)")
        ra.append(out)

    print(f"\n{'✅' if ra else '⚠️'} {len(ra)}/{len(chon)} video")
    for x in ra:
        print(f"   {x}")
    return 0 if ra else 1


if __name__ == "__main__":
    sys.exit(main())
