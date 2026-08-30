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
     "kieu": "bank", "boi": ["quay", "ban_lam_viec", "van_phong"], "mau": "ngan_hang", "nguon": "fdic",
     "hoi": "How many banks does America still have?"},
    {"ten": "FINE PRINT", "handle": "@fineprintusa", "nhan": "The clause they hope you skip",
     "kieu": "luat_tre", "boi": ["van_phong", "ban_lam_viec", "phong_xu"], "mau": "van_phong", "nguon": "dieu_khoan",
     "hoi": "What do Americans complain about most?"},
    {"ten": "WHO OWNS IT", "handle": "@whoownsitusa", "nhan": "Who really owns the brand",
     # 29/8 — anh chỉ vào khung: "đừng có mà đưa kiểu bối cảnh hàng rào ko liên quan vào videos".
     # Đúng. Bối cảnh phải trả lời cùng câu hỏi kênh đặt ra; hàng rào sân sau không dính gì tới
     # "ai sở hữu thương hiệu anh dùng hằng ngày". Kệ siêu thị chính là chỗ người xem gặp những
     # thương hiệu ấy mỗi tuần. Tôi lấy hàng rào từ ảnh tham chiếu mà quên xét nội dung — cùng
     # loại lỗi với mấy kênh nét chì vẽ sương mù cho một bảng số.
     "kieu": "hang_xom", "boi": ["ke_sieu_thi", "san_sau", "ban_lam_viec"], "mau": "ke_sieu_thi", "nguon": "sec",
     "hoi": "Who owns the company behind your groceries?"},
    {"ten": "KNOW YOUR RIGHT", "handle": "@knowyourrightusa", "nhan": "What you are allowed to do",
     "kieu": "cong_to", "boi": ["toa_an", "phong_xu", "thu_phong"], "mau": "luat", "nguon": "toa_quyen",
     "hoi": "What rights get argued in court this month?"},
    {"ten": "SUED IN AMERICA", "handle": "@suedinamericausa", "nhan": "What Americans sue over",
     "kieu": "tham_phan", "boi": ["thu_phong", "phong_xu", "toa_an"], "mau": "thu_phong", "nguon": "toa_kien",
     "hoi": "What do Americans actually sue each other over?"},
    {"ten": "SKY TONIGHT", "handle": "@skytonightusa", "nhan": "What is above you right now",
     "kieu": "sao_dem", "boi": ["san_thuong", "tinh_van", "vu_tru"], "mau": "san_thuong", "nguon": "nasa_gan",
     "hoi": "What just passed the Earth?"},
    {"ten": "ONE EXPERIMENT", "handle": "@oneexperimentusa", "nhan": "One study, explained straight",
     "kieu": "khoa_hoc", "boi": ["lab", "ban_lam_viec", "phong_kham"], "mau": "phong_lab", "nguon": "epmc",
     "hoi": "What does the research actually say?"},
    {"ten": "DEEP FIELD", "handle": "@deepfieldusa", "nhan": "The farthest thing we have seen",
     "kieu": "vu_tru_gia", "boi": ["vu_tru", "tinh_van", "san_thuong"], "mau": "vu_tru", "nguon": "nasa_to",
     "hoi": "How far away is the farthest rock we track?"},
    {"ten": "WHAT THE CHART SAYS", "handle": "@whatthechartusa", "nhan": "What your chart does not say out loud",
     "kieu": "y_ta", "boi": ["phong_kham", "quay_vien_phi", "lab"], "mau": "phong_kham", "nguon": "fda",
     "hoi": "What got pulled off the shelf this month?"},
    # 29/8 — ĐỔI NGUỒN. Hai kênh y tế cùng khai `fda` nên ra GẦN NHƯ CÙNG MỘT VIDEO: cùng bảng
    # thu hồi, cùng con số 2,9M, cùng bối cảnh phòng khám. Đó đúng là khuôn "nội dung lặp lại"
    # mà chính sách YouTube nhắm vào — và tôi vừa tự tạo ra nó trong bộ kênh mới.
    # Chỉ số giá y tế của BLS mới là thứ trả lời được câu hỏi của kênh này.
    {"ten": "PRICE OF CARE", "handle": "@priceofcareusa", "nhan": "What care costs now",
     "kieu": "vien_phi", "boi": ["quay_vien_phi", "phong_kham", "van_phong"], "mau": "quay_vien_phi", "nguon": "gia_yte",
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
        # 30/8 — CỬA ẢI 3 → 4 MỤC. Cây thước `cham_v3` trừ điểm khi bảng có dưới BỐN mục ("bảng
        # bốn cột không đủ chỗ so sánh"), nhưng cửa ải ở đây chỉ đòi BA — nên hệ thống tự cho qua
        # đúng thứ mà chính nó chấm là hỏng, rồi SUED IN AMERICA ra 77 điểm.
        # Hai con số này phải khớp nhau: cửa ải ở tầng dữ liệu là chỗ quyết định BỎ LƯỢT, còn cây
        # thước chỉ đo cái đã lỡ ra. Thà không ra video còn hơn ra một bảng ba cột phẳng.
        if len(ds) < 4 or len({v for _, v in ds}) < 3:
            print(f"   ⚠️ {nguon}: chỉ {len(ds)} mục có số (nguồn toà đang chặn nhịp) — BỎ LƯỢT")
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
                # 30/8 — ĐO PHẦN TRĂM TĂNG, KHÔNG ĐO CHỈ SỐ.
                # Cây thước vẫn bắt "cột cao nhất chỉ gấp 1,2 lần cột thấp nhất" dù đã đổi từ
                # chỉ-số-theo-năm sang so-các-nhóm-chi. Lý do: chỉ số CPI đều bắt đầu từ 100, nên
                # một nhóm tăng 130% và một nhóm tăng 5% ra 230 và 105 — chênh nhau 2,2 lần trên
                # giấy nhưng chỉ 1,2 lần khi vài nhóm rơi rụng vì thiếu dữ liệu.
                # Bỏ đi cái gốc 100 ấy thì thành 130 và 5 — chênh HAI MƯƠI SÁU lần, và mắt thấy
                # ngay. Cùng một dữ liệu, chỉ khác chỗ đặt gốc.
                # Và nó ĐÚNG HƠN về thông tin: câu hỏi của kênh là "giá tăng bao nhiêu", không
                # phải "chỉ số hiện là bao nhiêu" — chỉ số là thứ không ai đọc ra ý nghĩa.
                _tang = nay / dau * 100 - 100
                if _tang > 0:
                    ds.append((ten, round(_tang, 1), f"+{_tang:,.0f}%"))
        if len(ds) < 4:
            return None
        ds.sort(key=lambda z: -z[1])
        return ("How much prices rose since 2000",
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
        # 30/8 — CẢNH MỞ DÙNG CỠ RỘNG, KHÔNG DÙNG CỠ CẬN.
        # Sau khi chuyển sang bố cục người-dẫn-ở-góc, cảnh mở khai "can" làm nhân vật to nhất
        # phim ngay giây đầu và tràn hẳn mép trái — đo được trên khung mở FINE PRINT: mất một
        # phần ba khuôn mặt. Và nó còn sai về kể chuyện: giây đầu là lúc người xem cần thấy MÌNH
        # ĐANG Ở ĐÂU, tức là lúc cần thấy bối cảnh nhiều nhất, chứ không phải lúc soi vào mặt.
        # Cỡ cận để dành cho câu chốt — chỗ cần nét mặt.
        (_mo, "bat_ngo", "mo_tay", "rong", [0.2, -0.12]),
        (k["hoi"], "nghi_ngo", "mo_tay", "trung", [0, 0]),
        # 29/8 — CẢNH CÓ BIỂU ĐỒ THÌ TAY PHẢI Ở TRONG NGƯỜI. Khung thật: cử chỉ "chỉ" duỗi tay
        # sang phải và cắt ngang tấm biểu đồ, nhìn ra là hai lớp chồng nhau chứ không ra là người
        # đang chỉ vào bảng. Nhân vật đứng bên trái, bảng bên phải — khoảng giữa quá hẹp để một
        # cánh tay duỗi hết cỡ nằm gọn.
        # Ba cảnh có bảng dùng cử chỉ khép: đếm trên ngón, khoanh tay, ngửa lòng bàn tay. Mắt
        # người xem đã có con số dẫn đường rồi, không cần một ngón tay chỉ nữa.
        (f"{tieu_de}. The gap is bigger than it looks.", "tu_tin", "dem", "trung", [-0.28, 0.1]),
        (f"{dan[1][0]} comes second at {dan[1][2]}. Then it drops fast.",
         "trung_tinh", "khoanh_tay", "trung", [0.3, 0]),
        (f"This is straight from {nguon.split(',')[0]}, not from me.",
         "tu_tin", "dem", "trung", [0.1, 0]),
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
        # ── BỐI CẢNH ĐỔI TRONG CÙNG MỘT VIDEO (29/8) ────────────────────────────────────
        # Anh: "10 channel mới phải đa dạng bối cảnh trong 1 videos sao cho phù hợp".
        # Trước đó cả sáu cảnh dùng đúng một nền, nên video 20 giây chỉ có một khung hình duy
        # nhất đứng yên phía sau — máy quay đổi cỡ nhưng thế giới không đổi, và mắt chán ngay từ
        # giây thứ tám.
        # Mỗi kênh nay có BỘ BA bối cảnh cùng một thế giới nghề nghiệp (ngân hàng: quầy → bàn
        # làm việc → văn phòng), xoay vòng theo cảnh. Không kênh nào trùng bộ ba với kênh khác.
        # KHÔNG tốn thêm một lượt hạn mức nào: bối cảnh là vector dựng bằng mã.
        _bo = k["boi"] if isinstance(k["boi"], list) else [k["boi"]]
        # ── CỬ CHỈ SUY TỪ CHÍNH CÂU ĐANG NÓI (30/8) ─────────────────────────────────────
        # Anh: *"tham khảo nâng cấp phần… cử động"*. Bảng `cau` gán cử chỉ theo VỊ TRÍ câu, nên
        # câu ở vị trí ba luôn cùng một cử chỉ dù nội dung câu ấy mỗi kênh một khác — tay nói một
        # đằng, miệng nói một nẻo. Bộ hài đã chữa chuyện này bằng `cu_chi_cua`, suy từ chính chữ:
        # có con số thì đếm ngón tay, câu hỏi thì ngửa tay, phủ định thì khoanh tay.
        # Dùng lại đúng hàm ấy (không chép), và chỉ ĐÈ khi bảng gốc để trống — bảng gốc có mấy
        # chỗ gán cố ý (cảnh chốt) thì phải tôn trọng.
        try:
            import kich_hai as _KH3
            _cc = cc or _KH3.cu_chi_cua(nar, i, i == len(cau) - 1)
        except Exception:
            _cc = cc
        c = {"s": round(t, 2), "e": round(t + giay_moi_cau, 2), "nar": nar,
             "camXuc": cx, "cuChi": _cc, "co": co, "nhin": nhin,
             # XÊ DỊCH CHỖ ĐỨNG theo cảnh. Người kể đứng chôn chân suốt hai mươi giây là dấu hiệu
             # rõ nhất của hình dựng máy; nhích vài chục điểm mỗi cảnh là đủ để khung "còn sống".
             "dich": [-26, 12, -8, 22, -14, 4][i % 6],
             "boi": _bo[i % len(_bo)]}
        # 29/8 — LỚP HÌNH PHẢI KHỚP CÂU ĐANG NÓI. Khi đảo thứ tự lời thoại (đưa con số lên câu
        # đầu để hook mạnh hơn) tôi quên đảo bảng gán lớp hình theo — nên con số lớn hiện ở cảnh
        # CÂU HỎI, còn cảnh đọc con số thì trống. Người xem nghe "109, đó là Illinois" mà màn
        # hình chưa có gì, rồi con số mới bật ra lúc đang hỏi một câu khác.
        if i == 0:
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
        # ── TIẾNG ĐỘNG THEO HÀNH ĐỘNG (29/8) ────────────────────────────────────────────
        # Anh: "âm thanh hiệu ứng chuyển cảnh phù hợp hay e nha". Trước đó không cảnh nào khai
        # `sfx` nên cỗ máy có sẵn đường phát tiếng mà chưa từng phát một tiếng nào.
        # Gắn theo Ý NGHĨA của cảnh, không rải đều cho có:
        #   cảnh số lớn rơi xuống -> tiếng va (impact), đúng lúc con số bật ra
        #   cảnh biểu đồ mọc      -> tiếng lướt (whoosh), đi cùng cột đang lên
        #   cảnh đổi cột tô sáng  -> tiếng tách (pop), báo mắt nhìn sang cột khác
        #   cảnh chốt             -> tiếng ding nhẹ
        # Bốn tiếng cho sáu cảnh: hai cảnh còn lại để yên. Cảnh nào cũng có tiếng thì tai mệt và
        # tiếng mất hết sức nhấn — im lặng cũng là một phần của nhịp.
        # Đường dẫn phải kể cả thư mục `sfx/` — khai thiếu thì Remotion tải 404 và CẢ LƯỢT
        # RENDER chết, chứ không phải chỉ mất tiếng. Một tệp phụ trợ thiếu mà giết cả video là
        # cái giá quá đắt, nên tên tệp phải đúng ngay từ đầu.
        c["sfx"] = {0: "sfx/impact.mp3", 2: "sfx/whoosh.mp3",
                    3: "sfx/pop.mp3", 5: "sfx/ding.mp3"}.get(i, "")
        if not c["sfx"]:
            c.pop("sfx")
        canh.append(c)
        t += giay_moi_cau
    return canh, " ".join(x[0] for x in cau)


# ══════════════════════════════════════════════════════════════════════════════════════════
# DÙNG LẠI PHẦN ĐÃ VIẾT CHO BỘ HÀI — KHÔNG CHÉP LẠI
# ------------------------------------------------------------------------------------------
# 30/8 — Anh: *"ứng dụng 10 channel funny sau vào 10 channel trước"*.
# Ba thứ dưới đây đã viết và đã đo trong `kich_hai.py`; chép lại là tạo ra hai bản sẽ trôi xa
# nhau. Nhập thẳng từ đó — sửa một chỗ thì cả hai bộ được hưởng.
#   · `_cat_lang`  — cắt đệm im lặng edge-tts chèn ở hai đầu mỗi đoạn (luật 7ak)
#   · `lam_thumb`  — thumbnail trích từ chính video ở nhịp đuôi (luật 7…)
#   · `_giay_wav`  — đo độ dài THẬT của tệp wav
# ══════════════════════════════════════════════════════════════════════════════════════════
# NỀN ẢNH AI CHO BỘ DỮ LIỆU — HAI NỀN MỖI KÊNH, VẼ MỘT LẦN DÙNG MÃI
# ------------------------------------------------------------------------------------------
# 30/8 — Anh: *"tham khảo nâng cấp phần bối cảnh"*. Bối cảnh vector của bộ này chỉ là vài mảng
# màu với mấy hình khối, trong khi bộ hài đã chạy nền ảnh AI và khung đẹp hơn hẳn — cùng một dàn
# nhân vật mà hai bộ trông như hai mức đầu tư.
#
# Câu vẽ chọn theo NGHỀ của kênh, không theo "cho đẹp": sảnh ngân hàng cho kênh ngân hàng, phòng
# lưu trữ hồ sơ cho kênh điều khoản, đài quan sát cho kênh thiên văn. Người xem phải đọc ra kênh
# này nói về gì trước cả dòng chữ đầu tiên.
#
# Mọi câu đều kèm `_SAN_V3`: ép ảnh có sàn ở một phần ba dưới khung (nếu không, ảnh chụp ngang
# tầm mặt bàn và nhân vật hoá ra đứng trên mặt bàn — lỗi đã trả giá ở bộ hài, luật 7aa) và ép
# CHỪA KHOẢNG TRỐNG BÊN PHẢI cho biểu đồ, vì bộ này luôn có một bảng số đè lên nền.
# Từ nào báo hiệu chủ đề có BỀ MẶT IN ĐƯỢC — thấy nó thì phải ép bao bì trơn (luật 7ay).
# Khai ở TẦNG MODULE vì hai hàm vẽ nền đều cần: để trong thân một hàm thì hàm kia không thấy.
# Câu cấm chữ mượn từ `kich_hai` — MỘT bản cho cả hai bộ. Xem chú thích ở đó về việc quy tắc
# này từng tồn tại ở ba bản khác nhau, và bản yếu nhất lại là bản đang chạy.
try:
    from kich_hai import CAM_CHU, CAM_BAO_BI
except Exception:
    CAM_CHU = ", no signs on walls, no lettering anywhere in the scene, blank walls"
    CAM_BAO_BI = ", all packaging completely blank and unbranded, no printed text"

_CO_BAO = ("packet", "package", "packaging", "box", "boxes", "bottle", "can ", "cans",
           "carton", "label", "product", "shelf", "shelves", "grocer", "snack", "brand")
_SAN_V3 = ("wide shot, camera at standing eye level, no single object fills more than a third of the frame, furniture at normal size for a standing adult, floor clearly visible across the lower "
           "third, large empty wall space on the right side of the frame, nothing important on "
           "the right half")
NEN_V3 = {
    "BANK RUN":            ["american bank branch lobby with teller counters along the left wall",
                            "bank vault door seen from inside a quiet corridor",
                            "bank branch back office with desks and a computer on the left",
                            "bank drive-through window seen from inside, morning light",],
    "FINE PRINT":          ["law office room with tall filing cabinets on the left, warm lamps",
                            "records archive room with rows of document boxes on shelves",
                            "law office desk with a lamp and stacked folders on the left",
                            "quiet meeting room with a long table on the left, blinds",],
    "WHO OWNS IT":         ["corporate lobby with a reception desk on the left, glass and stone",
                            "empty boardroom with a long table pushed to the left",
                            "corporate hallway with glass office doors on the left",
                            "office floor with empty desks on the left, late afternoon",],
    "KNOW YOUR RIGHT":     ["american courthouse corridor with tall columns on the left",
                            "quiet courtroom gallery seen from the side, wooden benches",
                            "courthouse steps seen from the side, stone columns on the left",
                            "clerk office counter with document trays on the left",],
    "SUED IN AMERICA":     ["courtroom bench and witness stand seen from the left side",
                            "law library with rows of legal volumes on the left wall",
                            "judge chambers with bookshelves on the left, warm lamp",
                            "empty jury box seen from the side, wooden panels",],
    "SKY TONIGHT":         ["observatory dome interior at night, telescope on the left, deep blue",
                            "open field at night under a clear starry sky, low horizon",
                            "observatory control desk with monitors on the left, night",
                            "rooftop terrace at night with a small telescope on the left",],
    "ONE EXPERIMENT":      ["university research lab bench on the left, clean bright light",
                            "quiet laboratory corridor with glass doors on the left",
                            "lab office with a microscope and notebooks on the left",
                            "clean room corridor with lab windows on the left",],
    "DEEP FIELD":          ["mission control room at night, console banks on the left, blue glow",
                            "radio telescope dish seen from the ground at dusk, wide open sky",
                            "deep space network operations room, screens on the left, night",
                            "telescope maintenance floor with cables and rigs on the left",],
    "WHAT THE CHART SAYS": ["hospital records office with folders on the left, clean daylight",
                            "empty clinic corridor with doors on the left, bright and calm",
                            "clinic nurse station with a counter on the left, bright light",
                            "hospital supply room with labelled shelves on the left",],
    "PRICE OF CARE":       ["hospital admissions desk on the left, waiting chairs, daylight",
                            "pharmacy counter seen from the side, shelves on the left",
                            "hospital billing office with a desk on the left, daylight",
                            "clinic waiting area seen from the side, chairs on the left",],
}


# Tên riêng KHÔNG được lọt vào câu vẽ. Máy vẽ thấy "Gatorade" là dựng ngay một cái chai có logo
# — mà logo thật trong khung của kênh bật kiếm tiền là rủi ro pháp lý (luật 7w). Bảng này đổi
# tên riêng thành LOẠI HÀNG: cùng thông tin cho máy vẽ, không có nhãn hiệu nào.
_LOAI = [
    (("gatorade", "pepsi", "coca", "drink", "soda", "juice"), "bottled drinks on a shelf"),
    (("pringles", "doritos", "cheerios", "snack", "chip", "cereal"), "snack boxes on a shelf"),
    (("poultry", "meat", "beef", "chicken", "food", "produce"), "packaged food on a shelf"),
    (("drug", "pill", "pharma", "medicine", "recall"), "medicine boxes on a pharmacy shelf"),
    (("bank", "deposit", "loan", "credit"), "bank counter and paperwork"),
    (("court", "lawsuit", "clause", "contract", "damages"), "legal documents on a desk"),
    (("asteroid", "orbit", "space", "km", "telescope"), "night sky through an observatory window"),
    (("study", "research", "trial", "evidence"), "lab notebooks and glassware on a bench"),
    (("price", "cost", "cpi", "inflation"), "receipts and a calculator on a counter"),
]


def _chu_de_ai(ten_kenh: str, tieu_de: str, nhan_cot: list, keys) -> str:
    """Hỏi AI: video này nói về gì, và cảnh nền nào hợp nhất? Trả cụm mô tả, rỗng nếu hỏng.

    30/8 — Anh: *"sao cho phù hợp nội dung, nhớ PHÂN TÍCH ĐÚNG ko máy móc"*.
    Bản trước dò từ khoá cứng (`_LOAI`): thấy chuỗi "poultry" thì trả "packaged food". Đó đúng là
    máy móc, và nó hỏng theo hai chiều — bỏ sót khi tiêu đề dùng từ ngoài bảng, và gán bừa khi
    một từ trùng nghĩa khác ("class action" có chữ "class", "damages" có chữ "age").
    Một câu hỏi cho mô hình ngôn ngữ thì đọc được Ý, không đọc chuỗi. Rẻ hơn nhiều so với vẽ ảnh:
    một lượt sinh văn bản ngắn, và kết quả được cache theo chủ đề nên tập sau cùng chủ đề không
    hỏi lại.
    Ba ràng buộc ép vào câu hỏi, vì cả ba đều là lỗi đã trả giá:
      · KHÔNG tên riêng, KHÔNG nhãn hiệu — máy vẽ thấy tên là dựng logo (luật 7w);
      · KHÔNG người trong khung — nhân vật đã là vector, thêm người vẽ vào nền là hai thế giới;
      · KHÔNG chữ, KHÔNG biển hiệu — máy vẽ bịa chữ sai chính tả (luật 7t).
    """
    if not keys:
        return ""
    try:
        import content_brain as CB
    except Exception:
        return ""
    cot = ", ".join(str(x) for x in (nhan_cot or [])[:5])
    hoi = (
        "You pick the background setting for one short explainer video.\n"
        f"Channel: {ten_kenh}\nVideo title: {tieu_de}\nChart labels: {cot}\n\n"
        "Reply with ONE short English phrase (max 12 words) describing the physical place or "
        "objects that best match WHAT THIS VIDEO IS ABOUT — not where a presenter would stand.\n"
        "Hard rules: no brand names, no proper nouns, no people, no text or signage in the "
        "scene. Describe objects and a place only.\n"
        "Reply with the phrase alone, nothing else."
    )
    for k in list(keys)[:3]:
        try:
            g = CB._genai(k if isinstance(k, str) else k.get("key"))
            m = g.GenerativeModel("gemini-2.5-flash")
            r = m.generate_content(hoi)
            t = " ".join(str(getattr(r, "text", "") or "").split())[:120]
            # Bỏ dấu nháy và dấu chấm cuối mà mô hình hay thêm vào.
            t = t.strip().strip('"').strip("'").rstrip(".")
            if 8 <= len(t) <= 120:
                return t
        except Exception:
            continue
    return ""


def canh_moi_cau_ai(ten_kenh: str, tieu_de: str, cau_noi: list, keys) -> list:
    """Một cảnh nền cho MỖI CÂU nói. Trả danh sách cùng độ dài `cau_noi`, hoặc [] nếu hỏng.

    30/8 — Anh: *"chuyển cảnh footage chưa đa dạng, khi nói hết 1 câu thì phải thay đổi nền
    footage đúng ai phân tích vẽ ra"*.
    Bản trước chia sáu cảnh làm ba đoạn, ba nền — nên hai câu liền nhau vẫn cùng một khung, và
    video hai mươi giây chỉ có ba lần đổi hình. Anh muốn mỗi câu một hình, và hình ấy phải nói
    đúng câu đang nói.
    Nên hỏi mô hình MỘT lần cho cả bài: đưa nguyên sáu câu, nhận về sáu cảnh. Hỏi một lần thay vì
    sáu lần vì mô hình cần thấy CẢ MẠCH mới chọn được cảnh nối nhau hợp lý — sáu câu hỏi rời sẽ
    cho sáu cảnh chẳng liên quan gì nhau.
    """
    if not keys or not cau_noi:
        return []
    try:
        import content_brain as CB
    except Exception:
        return []
    ds = "\n".join(f"{i+1}. {c}" for i, c in enumerate(cau_noi))
    hoi = (
        "You pick one background image per line for a short explainer video.\n"
        f"Channel: {ten_kenh}\nTitle: {tieu_de}\nLines:\n{ds}\n\n"
        f"Return exactly {len(cau_noi)} numbered lines. For line N, give ONE short English "
        "phrase (max 12 words) describing the place or objects that best illustrate THAT line.\n"
        "Keep all scenes inside one coherent world so cuts between them feel natural.\nEVERY scene must be a WIDE shot at standing eye level, showing a room or open space with the floor visible and the line where floor meets the far wall visible. The camera stands back far enough that no single object fills more than a third of the frame; furniture at normal size for a room a standing adult walks through. Never a close-up, never a macro shot, never a low angle looking up at an object.\n\n"
        "Hard rules: no brand names, no proper nouns, no people, no text or signage, all "
        "packaging blank. Objects and places only.\n"
        "Format strictly as: 1. phrase\n2. phrase\n... nothing else."
    )
    import re as _re
    for kk in list(keys)[:3]:
        try:
            g = CB._genai(kk if isinstance(kk, str) else kk.get("key"))
            m = g.GenerativeModel("gemini-2.5-flash")
            t = str(getattr(m.generate_content(hoi), "text", "") or "")
            ra = []
            for ln in t.splitlines():
                mm = _re.match(r"\s*(\d+)[.)]\s*(.+)", ln)
                if mm:
                    v = " ".join(mm.group(2).split()).strip().strip('"').rstrip(".")
                    if 6 <= len(v) <= 130:
                        ra.append(v)
            if len(ra) >= len(cau_noi):
                return ra[:len(cau_noi)]
        except Exception:
            continue
    return []


def _chu_de_nen(tieu_de: str, nhan_cot: list) -> str:
    """Một cụm mô tả CHỦ ĐỀ CỦA TẬP để ghép vào câu vẽ nền. Rỗng nếu không đoán được.

    30/8 — Anh: *"footage là nền lấy từ ai generate của mình cho phù hợp NỘI DUNG VIDEOS ấy"*.
    Trước bản này nền chọn theo NGHỀ CỦA KÊNH và cố định — nên tập nào của WHO OWNS IT cũng đứng
    trong đúng một cái sảnh công ty, dù tập này nói về nước ngọt còn tập kia nói về thịt gà.
    Nền phải nói về THỨ ĐANG KỂ, không chỉ về nơi người kể đang đứng.
    Đoán chủ đề từ tiêu đề + nhãn cột, rồi đổi sang LOẠI HÀNG (không giữ tên riêng).
    """
    t = (str(tieu_de or "") + " " + " ".join(str(x) for x in (nhan_cot or []))).lower()
    for tu, mo in _LOAI:
        if any(x in t for x in tu):
            return mo
    return ""


def ve_nen_moi_cau(k: dict, DS, canh_ds: list) -> list:
    """Vẽ một nền cho mỗi cảnh trong `canh_ds`. Trả danh sách đường dẫn (rỗng ở chỗ vẽ hỏng).

    Cache theo NỘI DUNG CẢNH, không theo chỉ số: hai tập khác nhau mà có một cảnh giống nhau thì
    dùng chung ảnh. Với sáu cảnh mỗi tập, cách này cắt hẳn phần lớn chi phí vẽ từ tập thứ hai.
    """
    import hashlib as _hl
    thu = os.path.join(PUB, "v3nen")
    os.makedirs(thu, exist_ok=True)
    try:
        import kich_hai as _KHG
        gu = _KHG.GU_NEN
    except Exception:
        gu = "flat 2D cartoon background, bold clean outlines, simple flat colours"
    ra = []
    for canh in canh_ds:
        if not canh:
            ra.append("")
            continue
        rel = os.path.join("v3nen", f"c{_hl.md5(canh.encode('utf-8')).hexdigest()[:10]}.jpg")
        dest = os.path.join(PUB, rel)
        if os.path.exists(dest) and os.path.getsize(dest) > 20000:
            ra.append(rel)
            continue
        _them = CAM_CHU
        if any(x in canh.lower() for x in _CO_BAO):
            _them += CAM_BAO_BI
        ok = None
        for _l in range(2):
            try:
                import datastory_ci as _DC
                _p = _DC._salt_prompt(f"{canh}{_them}, {_SAN_V3}, {gu}")
            except Exception:
                _p = f"{canh}{_them}, {_SAN_V3}, {gu}"
            try:
                ok = DS._generate_image_ai(_p, dest, None, style=gu)
            except Exception:
                ok = None
            if ok and os.path.exists(dest) and os.path.getsize(dest) > 20000:
                break
            ok = None
        if ok:
            try:
                import kich_hai as _KH
                DS.nang_sang_anh(dest); _KH._keo_sang(dest)
                if _KH._nen_hong(dest) or _KH._co_chu(dest):
                    os.remove(dest); ok = None
            except Exception:
                pass
        ra.append(rel if (ok and os.path.exists(dest)) else "")
    print(f"      🎨 {sum(1 for x in ra if x)}/{len(ra)} nền theo câu")
    return ra


def ve_nen_v3(k: dict, DS, keys, chu_de: str = "") -> list:
    """Vẽ + cache nền cho một kênh. Chỉ vẽ tệp CHƯA CÓ.

    `chu_de` rỗng  -> bốn nền CỐ ĐỊNH của kênh (nơi làm việc, dùng lại mọi tập);
    `chu_de` có    -> thêm MỘT nền riêng cho tập này, ghép chủ đề vào câu vẽ. Nền ấy cache theo
                      chính chủ đề, nên hai tập cùng chủ đề dùng chung một ảnh — không tốn lượt
                      vẽ lần thứ hai.
    """
    thu = os.path.join(PUB, "v3nen")
    os.makedirs(thu, exist_ok=True)
    ra = []
    # 30/8 — DÙNG ĐÚNG MỘT CÂU GU VỚI BỘ HÀI. Anh: *"vẽ theo kiểu như bối cảnh style dạng như
    # mấy videos trước e demo"*.
    # Bản trước tôi tự viết một câu gu riêng cho bộ dữ liệu ("clean American explainer animation,
    # calm professional mood") vì nghĩ kênh nghiêm túc thì nền phải điềm đạm hơn. Kết quả: nền
    # V3 nhạt màu, ít chi tiết, trông như bản nháp bên cạnh nền của bộ hài.
    # Sai ở chỗ lẫn hai thứ: CHẤT (nghiêm túc hay hài) nằm ở nội dung, ở nhạc, ở ký hiệu cảm xúc
    # — KHÔNG nằm ở nét vẽ nền. Cùng một nét vẽ ấm và giàu chi tiết thì kênh nào cũng đẹp hơn.
    # Nên hai bộ dùng CHUNG một câu gu, và giữ nó ở một chỗ để không bao giờ trôi xa nhau nữa.
    try:
        import kich_hai as _KHG
        gu = _KHG.GU_NEN
    except Exception:
        gu = ("flat 2D cartoon background in the style of classic American animated sitcoms, "
              "bold clean outlines, simple flat colours, no people, no text, no signage, "
              "wide establishing shot, slightly stylised perspective")
    for i, prompt in enumerate(NEN_V3.get(k["ten"], [])):
        rel = os.path.join("v3nen", f"{k['ten'].replace(' ', '').lower()}_{i}.jpg")
        dest = os.path.join(PUB, rel)
        if os.path.exists(dest) and os.path.getsize(dest) > 20000:
            ra.append(rel)
            continue
        ok = None
        for _lan in range(3):
            try:
                import datastory_ci as _DC
                _p = _DC._salt_prompt(f"{prompt}, {_SAN_V3}, {gu}")
            except Exception:
                _p = f"{prompt}, {_SAN_V3}, {gu}"
            try:
                ok = DS._generate_image_ai(_p, dest, None, style=gu)
            except Exception as e:
                print(f"      ⚠️ nền {i} lượt {_lan+1}: {str(e)[:56]}")
                ok = None
            if ok and os.path.exists(dest) and os.path.getsize(dest) > 20000:
                break
            ok = None
        if ok:
            try:
                import kich_hai as _KH
                DS.nang_sang_anh(dest)
                _KH._keo_sang(dest)
                if _KH._nen_hong(dest) or _KH._co_chu(dest):
                    os.remove(dest); ok = None
            except Exception:
                pass
        if ok and os.path.exists(dest):
            ra.append(rel)
            print(f"      🎨 nền {i} xong")
        else:
            print(f"      ⚠️ nền {i}: không vẽ được — cảnh này dùng bối cảnh vector")
            ra.append("")

    # ── NỀN RIÊNG CHO TẬP NÀY ─────────────────────────────────────────────────────────
    if chu_de:
        import hashlib as _hl
        _kh = _hl.md5(chu_de.encode("utf-8")).hexdigest()[:8]
        rel = os.path.join("v3nen", f"{k['ten'].replace(' ', '').lower()}_t{_kh}.jpg")
        dest = os.path.join(PUB, rel)
        if os.path.exists(dest) and os.path.getsize(dest) > 20000:
            ra.insert(0, rel)
            return ra
        # ══ CHỦ ĐỀ CÓ BAO BÌ THÌ PHẢI ÉP BAO BÌ TRỐNG ═══════════════════════════════
        # 30/8 — Khung WHO OWNS IT đo được: kệ hàng đầy bao gói có NHÃN HIỆU BỊA — "Sunalis",
        # "Picn", "RET IFT". Đúng thứ luật 7w cấm, và lần này nó lọt qua vì chủ đề do AI sinh ra
        # ("kitchen pantry with assorted snack packets") vốn KHÔNG có tên riêng nào — nhưng chỉ
        # cần nhắc tới BAO GÓI là máy vẽ tự bịa nhãn lên đó.
        # Nên câu cấm phải bám vào VẬT, không bám vào tên: hễ chủ đề nói tới thứ có bề mặt in
        # được thì ép "bao bì trơn, mặt trắng". Cùng nguyên tắc `_bo_mat_chu` — không xin máy
        # đừng viết, mà bỏ hẳn chỗ chữ có thể bám.
        # CẤM CHỮ ÁP CHO MỌI NỀN, KHÔNG CHỈ NỀN CÓ BAO BÌ.
        # 30/8 — Khung BANK RUN đo được một biển hiệu ghi "BAND ANK": máy vẽ thấy chủ đề nói tới
        # ngân hàng là dựng ngay một cái biển trên tường, rồi bịa chữ lên đó. Chủ đề ấy KHÔNG có
        # từ nào trong danh sách bao-bì, nên lệnh cấm cũ không chạm tới.
        # Bài học lặp lại lần thứ ba (luật 7t · 7w · 7ay): chỗ nào có MẶT PHẲNG là chỗ đó có thể
        # mọc chữ, mà mọi bối cảnh trong nhà đều có tường. Nên câu cấm chữ phải áp cho TẤT CẢ,
        # còn câu cấm bao-bì chỉ là phần cộng thêm khi chủ đề nhắc tới hàng hoá.
        _them = CAM_CHU
        if any(x in chu_de.lower() for x in _CO_BAO):
            _them += CAM_BAO_BI
        _pr = f"{chu_de}, seen in a {k['ten'].split()[0].lower()} setting{_them}"
        ok = None
        for _lan in range(2):
            try:
                import datastory_ci as _DC
                _p = _DC._salt_prompt(f"{_pr}, {_SAN_V3}, {gu}")
            except Exception:
                _p = f"{_pr}, {_SAN_V3}, {gu}"
            try:
                ok = DS._generate_image_ai(_p, dest, None, style=gu)
            except Exception:
                ok = None
            if ok and os.path.exists(dest) and os.path.getsize(dest) > 20000:
                break
            ok = None
        if ok:
            try:
                import kich_hai as _KH
                DS.nang_sang_anh(dest)
                _KH._keo_sang(dest)
                if _KH._nen_hong(dest) or _KH._co_chu(dest):
                    os.remove(dest); ok = None
            except Exception:
                pass
        if ok and os.path.exists(dest):
            print(f"      🎨 nền theo chủ đề ({chu_de[:34]}) xong")
            ra.insert(0, rel)   # ưu tiên dùng cho cảnh mở
    return ra


def _mau_kenh(ten_bang: str) -> str:
    """Mã màu nhấn của một bảng màu, đọc thẳng từ `BANG_MAU` trong `BoiCanh.tsx`.

    Đọc từ nguồn thật thay vì chép sang đây một bản: chép là tạo ra hai bảng sẽ trôi xa nhau, và
    lần sau ai đổi màu kênh trong `BoiCanh.tsx` thì thumbnail lặng lẽ mang màu cũ.
    """
    import re as _re
    try:
        src = io.open(os.path.join(ENG, "src", "v2", "BoiCanh.tsx"), encoding="utf-8").read()
        m = _re.search(r"\b" + _re.escape(str(ten_bang)) + r":\s*\{[^}]*?nhan:\s*\"(#[0-9A-Fa-f]{6})\"", src, _re.S)
        if m:
            return m.group(1)
    except Exception:
        pass
    return "#C9A24A"


def _muon_bo_hai():
    """Trả (cat_lang, lam_thumb) mượn từ bộ hài; trả (None, None) nếu chưa có."""
    try:
        import kich_hai as _KH
        return _KH._cat_lang, _KH.lam_thumb
    except Exception as e:
        print(f"   ⚠️ không mượn được hàm của bộ hài: {str(e)[:60]}")
        return None, None


# NHẠC NỀN — mỗi kênh một bản, không kênh nào chung với kênh khác (kể cả với bộ hài).
# Video không nhạc thì mọi khoảng lặng đọc ra là thiếu tiếng chứ không phải nhịp (luật 7ag).
# Chọn bản TRẦM, ĐỀU — chất tài liệu. KHÔNG dùng những bản vui nhộn đang chạy cho bộ hài
# (carefree, km_undaunted, inspired): nhạc vui trên một kênh kể số liệu ngân hàng làm người xem
# đọc ra là đùa, mà cả mười kênh này sống bằng vẻ đáng tin.
# Không kênh nào chung bản với kênh khác, và không bản nào trùng với mười kênh hài.
NHAC_V3 = {
    "BANK RUN":            "music/km_impact_andante.mp3",
    "FINE PRINT":          "music/km_long_note_four.mp3",
    "WHO OWNS IT":         "music/broke_pad.mp3",
    "KNOW YOUR RIGHT":     "music/km_ossuary_air.mp3",
    "SUED IN AMERICA":     "music/km_ossuary_rest.mp3",
    "SKY TONIGHT":         "music/broke_pad_tram.mp3",
    "ONE EXPERIMENT":      "music/forecast_tram.mp3",
    "DEEP FIELD":          "music/inspired_tram.mp3",
    "WHAT THE CHART SAYS": "music/km_ascending_tram.mp3",
    "PRICE OF CARE":       "music/carefree_tram.mp3",
}

# ĐẠO CỤ — mỗi kênh một vật, nói ngay kênh này về gì trước cả câu thoại đầu tiên (luật 7an).
# Gán theo ĐÚNG việc nhân vật làm, không gán bừa cho có. Bản nháp đầu đặt cờ-lê cho kênh "ai sở
# hữu thương hiệu" và cốc cà phê cho kênh chi phí y tế — hai thứ chẳng nói lên gì về nội dung, mà
# đạo cụ sai còn tệ hơn không có: nó nói dối về nhân vật ngay giây đầu tiên.
# Và KHÔNG kênh nào dùng chung đạo cụ với kênh khác — cùng luật chống trùng đã áp cho bộ hài.
VAT_V3 = {
    "BANK RUN":            "giay_to",     # hồ sơ FDIC
    "FINE PRINT":          "kinh_lup",    # soi điều khoản in nhỏ
    "WHO OWNS IT":         "bang_ke",     # bảng kê cổ đông
    "KNOW YOUR RIGHT":     "bua_toa",     # quyền công dân
    "SUED IN AMERICA":     "bua_toa",     # kiện tụng
    "SKY TONIGHT":         "ong_nhom",    # bầu trời đêm nay
    "ONE EXPERIMENT":      "ong_nghiem",  # một nghiên cứu
    "DEEP FIELD":          "ong_nhom",    # vũ trụ sâu
    "WHAT THE CHART SAYS": "bang_ke",     # biểu đồ
    "PRICE OF CARE":       "giay_to",     # hoá đơn viện phí
}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="dựng 1 video ngắn cho mỗi kênh")
    ap.add_argument("--kenh", default="", help="chỉ kênh này (tên viết liền)")
    ap.add_argument("--luong", type=int, default=2)
    ap.add_argument("--nen", action="store_true", help="chỉ vẽ + cache nền ảnh, không render")
    a = ap.parse_args()

    import du_lieu_mo as D
    import datastory_ci as DS

    # Nạp kho khoá vẽ ảnh — cùng đường bộ hài dùng. Không có khoá thì `ve_nen_v3` tự lui về bối
    # cảnh vector, kênh vẫn ra video.
    # Nạp kho khoá vẽ ảnh — DÙNG ĐÚNG ĐƯỜNG bộ hài đang dùng (`the_he_2.keys_cuc_bo`), không tự
    # viết một đường khác. Không có khoá thì `ve_nen_v3` tự lui về bối cảnh vector, kênh vẫn ra
    # video — không bao giờ để một kênh câm chỉ vì thiếu ảnh.
    keys = None
    try:
        import the_he_2 as T2
        keys = T2.keys_cuc_bo() or None
        if keys:
            DS.set_ai_pool(keys, "V3")
    except Exception as e:
        print(f"   ⚠️ không nạp được kho khoá vẽ: {str(e)[:60]}")

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
        if a.nen:
            ve_nen_v3(k, DS, keys)
            continue
        sl = lay_so_lieu(k["nguon"], D)
        if not sl:
            print(f"   ⚠️ {ten}: nguồn không trả đủ dữ liệu — BỎ LƯỢT (không bịa)")
            continue
        # Nền vẽ SAU khi có số liệu, vì chủ đề của tập nằm trong chính số liệu ấy.
        # HỎI AI TRƯỚC, BẢNG TỪ KHOÁ LÀ ĐƯỜNG LUI. Không có khoá hoặc mô hình chập thì vẫn ra
        # được một chủ đề thô còn hơn không có nền theo nội dung nào.
        canh, loi = dung_canh(k, sl)
        # ══ MỘT NỀN CHO MỖI CÂU ═════════════════════════════════════════════════════════
        # Anh: *"khi nói hết 1 câu thì phải thay đổi nền footage"*. Hỏi mô hình MỘT lần cho cả
        # bài (nó cần thấy cả mạch mới chọn được các cảnh nối nhau hợp lý), nhận về sáu cảnh.
        _canhDS = canh_moi_cau_ai(ten, sl[0], [c["nar"] for c in canh], keys)
        for _i2, _c2 in enumerate(_canhDS):
            print(f"   🧭 {_i2+1}. {_c2[:62]}")
        nenCau = ve_nen_moi_cau(k, DS, _canhDS) if _canhDS else []
        # Nền cố định của kênh làm ĐƯỜNG LUI cho những câu mà mô hình không trả hoặc vẽ hỏng —
        # không bao giờ để một cảnh trống nền.
        _nhan = [a2 for a2, _b2, _c2 in sl[1]]
        nen2 = ve_nen_v3(k, DS, keys, "") if (not nenCau or not all(nenCau)) else []
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
        # CẮT ĐỆM IM LẶNG edge-tts chèn ở hai đầu (luật 7ak). Bộ này đọc CẢ ĐOẠN một lần nên chỉ
        # có một cặp đệm — ít hơn bộ hài nhiều, nhưng vẫn là một hai giây chết ở đầu và cuối
        # video. Cắt xong phải DỜI mọi mốc từ đi đúng phần đã bỏ ở đầu, không thì khẩu hình chạy
        # trước tiếng.
        _cat, _thumb = _muon_bo_hai()
        _bo_dau = 0.0
        if _cat:
            import tempfile as _tf
            _tam = _tf.mkdtemp(prefix="v3lang_")
            _w0 = os.path.join(_tam, "a.wav"); _w1 = os.path.join(_tam, "b.wav")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp3, "-ar", "24000", "-ac", "1",
                            _w0], capture_output=True, timeout=300)
            if os.path.exists(_w0):
                _bo_dau = _cat(_w0, _w1)
                if _bo_dau and os.path.exists(_w1):
                    r2 = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", _w1,
                                         "-b:a", "96k", mp3], capture_output=True, timeout=300)
                    if r2.returncode:
                        _bo_dau = 0.0
                    else:
                        import kich_hai as _KH2
                        dur = _KH2._giay_wav(_w1)
                        print(f"   ✂️ cắt {_bo_dau:.2f}s im lặng đầu · còn {dur:.1f}s")
        # `subs` là [{w, t, d, si}] — đúng khuôn `Tu` mà `visemeTai` cần, không phải đổi gì.
        tu = [{"t": round(max(0.0, float(x.get("t", 0)) - _bo_dau), 3),
               "d": float(x.get("d", 0)), "w": str(x.get("w", "")),
               "si": int(x.get("si", 0))} for x in (subs or [])]
        if not tu:
            print("   ❌ giọng đọc không trả mốc từ nào — BỎ (khỏi ra video câm)")
            continue
        # ── RANH GIỚI CẢNH LẤY TỪ CHỈ SỐ CÂU, KHÔNG CHIA ĐỀU (29/8) ─────────────────────
        # Anh: "voice với sub chạy khớp trùng nhau 100%".
        # Phụ đề vốn đã khớp tuyệt đối — nó đọc thẳng mốc từng từ của edge-tts. Thứ LỆCH là
        # RANH GIỚI CẢNH: tôi chia đều thời lượng cho sáu cảnh, trong khi sáu câu dài ngắn khác
        # nhau. Đo trên BANK RUN: chia đều ra 3,7 giây mỗi cảnh, còn câu thật dài từ 2,1 tới 5,4
        # giây — nên máy quay cắt cảnh, biểu đồ mọc và cảm xúc đổi đều rơi vào GIỮA một câu.
        # Người xem thấy nhân vật đang nói dở thì cảnh nhảy; đó là thứ đọc ra ngay là "làm ẩu"
        # dù không ai chỉ được tên lỗi.
        # `subs` có sẵn `si` = câu thứ mấy, do chính edge-tts đánh dấu. Cảnh thứ i chạy từ từ
        # ĐẦU TIÊN của câu i tới ngay trước từ đầu tiên của câu i+1. Khớp tuyệt đối, không phải
        # xấp xỉ, và không tốn thêm một phép đo nào.
        # MỘT LỜI THOẠI CÓ THỂ GỒM NHIỀU CÂU. edge-tts đánh `si` theo CÂU, còn cảnh của mình
        # là theo LỜI THOẠI: "109. That is Illinois, and most people have no idea." là một lời
        # thoại nhưng hai câu. Đo trên BANK RUN: 6 cảnh mà có 9 câu — ánh xạ thẳng cảnh i ↔ câu i
        # thì ba cảnh cuối không có câu nào và cả video lệch hẳn.
        # Nên đếm số câu trong TỪNG lời thoại rồi cộng dồn để ra dải câu của mỗi cảnh.
        import re as _re3
        _dem_cau = lambda t: max(1, len([x for x in _re3.split(r"(?<=[.!?])\s+", str(t or "")) if x.strip()]))
        _dai = []
        _bd = 0
        for c2 in canh:
            _n = _dem_cau(c2["nar"])
            _dai.append((_bd, _bd + _n - 1))
            _bd += _n
        _mocs = {}
        for w in tu:
            _mocs.setdefault(w["si"], []).append(w)
        for i2, c2 in enumerate(canh):
            _a, _b = _dai[i2]
            ws = [w for si in range(_a, _b + 1) for w in (_mocs.get(si) or [])]
            if ws:
                c2["s"] = round(min(x["t"] for x in ws), 2)
                _sau = _mocs.get(_b + 1) or []
                c2["e"] = round(min(x["t"] for x in _sau) if _sau
                                else max(x["t"] + x["d"] for x in ws) + 0.35, 2)
            else:
                # câu không có từ nào (TTS nuốt) -> nối tiếp cảnh trước, đừng để lỗ thời gian
                c2["s"] = canh[i2 - 1]["e"] if i2 else 0.0
                c2["e"] = c2["s"] + 1.2
        # cảnh cuối kéo tới hết tiếng, khỏi cụt đuôi
        if canh:
            canh[-1]["e"] = round(max(canh[-1]["e"], dur), 2)
        props = {
            "canh": canh, "tu": tu, "voMp3": rel,
            # ══ NGHỀ HIỆN LÊN NGƯỜI ═══════════════════════════════════════════════════
            # Đặt hai khung cạnh nhau (khối và que của cùng một giây) thì bản que thua đúng một
            # điểm: **nhìn không ra nghề**. Bản khối có áo blouse và bảng kẹp nên đọc ngay là
            # chuyên gia; bản que là một người trung tính.
            # Đó là thứ anh dặn riêng — *"kênh luật thì là chuyên gia luật"* — nên phải trả lại.
            # Trả bằng NÉT, không bằng cách quay về lối vẽ có khối: một tà áo choàng là hai
            # đường xiên, một ống nghe là hai đường cong với ba vòng tròn.
            # Vài kênh dùng chung một phụ kiện (luật sư và thẩm phán cùng áo choàng) — đúng
            # thực tế, và chúng vẫn phân biệt được bằng tóc, kính, dáng.
            "kieu": {"phuKien": {
                "bank": "the_deo", "luat_tre": "bang_kep", "hang_xom": "bang_kep",
                "cong_to": "ao_choang", "tham_phan": "ao_choang", "sao_dem": "khan_quang",
                "khoa_hoc": "ao_blouse", "vu_tru_gia": "ao_blouse", "y_ta": "ong_nghe",
                "vien_phi": "ong_nghe",
            }.get(k["kieu"], "the_deo")},
            "kieuGoc": k["kieu"], "bangMau": k["mau"],
            "tieuDe": k["nhan"], "nguon": sl[2],
            "nhac": NHAC_V3.get(k["ten"], ""),
            "doVat": VAT_V3.get(k["ten"], ""),
            # Một nền cho cả video — cùng luật "một tập một địa điểm" đã chốt cho bộ hài
            # (luật 7x): người kể không dịch chuyển giữa câu. Nền thứ hai để dành cho tập sau.
            # 30/8 — MỘT NỀN CHO MỖI ĐOẠN NỘI DUNG, không phải một nền cho cả video.
            # Anh: *"chuyển cảnh phù hợp với nội dung lời nói"*. Sáu cảnh chia làm ba đoạn —
            # MỞ (giới thiệu) · SỐ LIỆU (đọc bảng) · CHỐT (kết luận) — và mỗi đoạn một nền.
            # Nền đầu tiên trong `nen2` là nền vẽ THEO CHỦ ĐỀ CỦA TẬP (nếu đoán được chủ đề),
            # nên nó dành cho đoạn MỞ: giây đầu người xem thấy ngay video này nói về cái gì.
            # Hai nền sau là nơi làm việc của kênh — cùng một thế giới nghề nghiệp, nên đổi cảnh
            # giữa chúng vẫn logic (người dẫn đi từ sảnh vào bàn làm việc), khác hẳn kiểu nhảy
            # từ ngân hàng sang bãi biển.
            "nenTheoCanh": [((nenCau[i] if i < len(nenCau) and nenCau[i] else
                              (nen2[i % len(nen2)] if nen2 else "")))
                            for i in range(len(canh))],
            "nenAnh": (next((x for x in (nenCau + nen2) if x), "")),
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
        # THUMBNAIL — trích từ chính video, không vẽ mới (cùng cách bộ hài, luật 7…).
        # Câu hook lấy TIÊU ĐỀ kênh chứ không lấy câu thoại đầu: bộ này là kênh dữ liệu, và thứ
        # kéo người xem là CÂU HỎI mà video trả lời ("Is your bank actually healthy?"), không
        # phải một mẩu đối đáp.
        if _thumb:
            _th = os.path.join(GOC, "out", f"v3_{sl_ten}.jpg")
            # `k["mau"]` ở bộ này là TÊN bảng màu ("ngan_hang"), không phải mã màu — khác hẳn
            # bộ hài, nơi `mau` là mã hex. Đọc mã `nhan` từ chính `BANG_MAU` trong `BoiCanh.tsx`
            # thì dải nhận diện trên thumbnail mang đúng màu kênh; đoán bừa một mã là dải ấy
            # chẳng liên quan gì tới kênh.
            _hex = _mau_kenh(k["mau"])
            if _thumb(out, k.get("nhan") or ten, ten, _hex, _th):
                print(f"   🖼  thumbnail: {os.path.basename(_th)}")
        print(f"   ✅ {ten}: {out}  ({mb:.1f} MB)")
        ra.append(out)

    print(f"\n{'✅' if ra else '⚠️'} {len(ra)}/{len(chon)} video")
    for x in ra:
        print(f"   {x}")
    return 0 if ra else 1


if __name__ == "__main__":
    sys.exit(main())
