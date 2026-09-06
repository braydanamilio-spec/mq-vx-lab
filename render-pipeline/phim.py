#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DÂY CHUYỀN PHIM GIẢI THÍCH v10 — 18 kênh.  (6/9/2026)

    kịch bản (Python, số liệu tính ra)          giai_thich.kich_ban   — GIỮ NGUYÊN
      -> giọng đọc + mốc từng từ                kich_hai.doc_hai_giong
      -> CHIA NHỊP theo mốc từ, ép 1,5–2,5 s    chia_nhip()           — MỚI
      -> bảng phân cảnh                          phim_canh.dao_dien    — MỚI
      -> ảnh AI mỗi nhịp (CF FLUX.2 / Gemini)   phim_anh.ve           — MỚI
      -> lớp dữ liệu vẽ bằng code                LopSo.tsx             — MỚI
      -> render                                  PhimDoc / PhimNgang   — MỚI

── VÌ SAO KỊCH BẢN CŨ ĐƯỢC GIỮ, CÒN MỌI THỨ KHÁC LÀM LẠI ───────────────────────────────────
Anh chê hai thứ: ảnh xấu và template lặp. Cả hai đều nằm ở tầng HÌNH. Tầng CHỮ thì ngược lại —
nó là chỗ duy nhất của bộ này không được phép sai, vì `giai_thich.py` tính mọi con số bằng
Python từ hằng số sách giáo khoa, đúng để không có một con số nào do AI bịa ra. Viết lại tầng
ấy là tự nguyện đánh đổi thứ đang đúng để lấy thứ không ai phàn nàn.

Nên ranh giới của lần làm lại này là: **giữ nguyên `giai_thich.py`, thay toàn bộ đường đi từ
lời nói tới khung hình.** Bộ cũ vẫn chạy được y như trước — `phim.py` không import ngược vào
nó, không sửa một dòng nào của nó.

── MỘT NHỊP MỘT ẢNH, VÀ ĐÓ LÀ RÀNG BUỘC CHÍNH ────────────────────────────────────────────
Trần 2,6 giây không phải mong muốn mà là phép chia: nhịp dài hơn thế thì cắt đôi tại mốc từ
gần giữa nhất, và nửa sau nhận một ảnh RIÊNG. Nên "1,5–2,5 giây một cảnh" là hệ quả cấu trúc
chứ không phải một con số cần ai nhớ.
"""
import argparse
import io
import json
import math
import os
import re
import subprocess
import sys
import time

GOC = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(os.path.dirname(GOC), "engine-remotion")
PUB = os.path.join(ENG, "public")
RA = os.path.join(GOC, "out")

sys.path.insert(0, GOC)
import phim_gu as GU              # noqa: E402
import phim_anh as A              # noqa: E402
import phim_canh as C             # noqa: E402
import phim_dang as D             # noqa: E402

# Nhịp: trần cứng và đích. Trần 2,6 s là chỗ §12.11 đo trên video tham chiếu ("không cảnh nào
# quá 7 s") siết lại theo đúng lời anh hôm nay ("1.5 tới 2.5s"). Đích 2,0 s dùng khi chia đôi:
# chia một nhịp 5,0 s thành 2 phần thì mỗi phần 2,5 s — vẫn trong dải.
TRAN_NHIP = 2.6
DICH_NHIP = 2.0

# Phông chữ theo kênh — cùng bảng với bộ cũ để giữ nhận diện đã dựng. Đây là thuộc tính KÊNH,
# không đổi theo tập, nên nó khai một chỗ và engine chỉ đọc.
PHONG = {
    "howlong": "poppins",  "howbig": "anton",     "realcost": "oswald",
    "howmuch": "archivo",  "whatif": "rubik",     "survive": "anton",
    "dayinlife": "rubik",  "wheregoes": "poppins", "therules": "oswald",
    "speedof": "archivo",  "odds": "oswald",      "hiddenfee": "archivo",
    "yearsof": "rubik",    "howloud": "anton",    "whatweighs": "poppins",
    "rightnow": "poppins", "howhot": "anton",     "smallest": "archivo",
}


# ══ LỚP DỮ LIỆU ══════════════════════════════════════════════════════════════════════════════
def _so(v) -> float:
    """"20.2K" -> 20200 · "$1K" -> 1000 · "1.5" -> 1.5. Không đọc được thì trả None.

    Chỉ dùng cho `moc`/`cot` — những chỗ dữ liệu CÙNG MỘT đơn vị. Không dùng cho cặp so sánh
    khác đơn vị: xem chú thích `DoiChieu` trong `LopSo.tsx`."""
    s = str(v or "").strip().replace(",", "")
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*([KMB])?", s, re.I)
    if not m:
        return None
    n = float(m.group(1))
    return n * {"k": 1e3, "m": 1e6, "b": 1e9}.get((m.group(2) or "").lower(), 1)


def lop_du_lieu(n: dict) -> dict:
    """Nhịp cũ -> lớp phủ dữ liệu, hoặc None nếu nhịp này chỉ cần ẢNH.

    Nguyên tắc: chỉ phủ khi có SỐ THẬT. Bộ cũ có khuôn `the_chu` biến lời kể thành một thẻ chữ
    giữa khung — người xem đọc cùng một câu hai lần (thẻ + phụ đề), và đó là một trong hai thứ
    anh gọi là "lặp đi lặp lại cùng một motip". Ở đây thẻ chữ KHÔNG tồn tại: câu ấy đã có phụ
    đề đọc nó, và khung hình để dành cho cảnh phim."""
    if n.get("cot"):
        cot = [{"nhan": str(c.get("nhan") or "")[:14], "v": float(c.get("v") or 0)}
               for c in n["cot"] if c.get("v") is not None]
        if len(cot) >= 2:
            return {"k": "chart", "cot": cot[:6], "don": n.get("don") or "",
                    "nhan": n.get("chu") or ""}
    if n.get("moc") and len(n["moc"]) >= 2:
        cot = []
        for m in n["moc"]:
            v = _so(m.get("phu"))
            if v is not None:
                # Cùng phép cắt với nhãn `doi` — cắt cứng `[:14]` ở đây cũng cắt giữa chữ,
                # chỉ là nhãn cột ngắn nên hiếm khi lộ. Một chỗ hiếm lộ vẫn là một chỗ hỏng.
                cot.append({"nhan": _nhan(m.get("nhan"), 16), "v": v})
        if len(cot) >= 2:
            return {"k": "chart", "cot": cot[:6], "don": n.get("don") or "", "nhan": ""}
    if n.get("so"):
        return {"k": "so", "so": str(n["so"]), "don": str(n.get("don") or ""),
                "nhan": str(n.get("chu") or "")[:44]}
    tr, ph = n.get("trai"), n.get("phai")
    if isinstance(tr, dict) and isinstance(ph, dict) and tr.get("so") and ph.get("so"):
        return {"k": "doi",
                "trai": {"nhan": _nhan(tr.get("nhan")), "so": str(tr["so"])},
                "phai": {"nhan": _nhan(ph.get("nhan")), "so": str(ph["so"])}}
    return None


def _nhan(x, tran: int = 26) -> str:
    """Nhãn cho lớp so sánh — cắt ở RANH GIỚI TỪ, không cắt giữa chữ.

    ── VÌ SAO  (đo 6/9/2026) ───────────────────────────────────────────────────────────────
    Bản cũ cắt cứng `[:16]`, và nhãn *"the rocket engine combustion chamber"* lên màn hình
    thành **"THE ROCKET ENGIN"** — cụt giữa một chữ. Người xem đọc ra "video lỗi", không đọc
    ra "nhãn dài".
    Em suýt chữa nhầm tầng: soi khung thấy chữ cụt nên đi sửa CỠ CHỮ trong engine, trong khi
    chuỗi đã bị cắt từ trước lúc rời Python — engine không bao giờ nhìn thấy phần bị mất.
    §1 CLAUDE.md: khi con số và con mắt bất đồng, ĐO cái đang bị chấm; ở đây là đọc chính
    chuỗi trong `.json`, không đoán từ khung hình.

    26 chứ không 16: lớp `doi` nay cho nhãn xuống dòng thứ hai và tự hạ cỡ chữ theo độ dài
    (xem `SoComic.tsx`), nên trần chỉ còn để chặn nhãn dài bất thường. Và cắt ở ranh giới từ —
    "the rocket engine" đọc được, "the rocket engin" thì không."""
    t = " ".join(str(x or "").split())
    if len(t) <= tran:
        return t
    cat = t[:tran].rsplit(" ", 1)[0]
    # Bỏ hư từ ở ĐUÔI: cắt xong ra "the surface of the sun at" thì chữ cuối treo lửng, đọc ra
    # là câu bị đứt chứ không phải một nhãn. Nhãn phải KẾT THÚC ở một danh từ.
    _hu = {"at", "of", "the", "a", "an", "in", "on", "from", "and", "to", "for", "with",
           "by", "per", "into", "over", "under"}
    while cat and cat.rsplit(" ", 1)[-1].lower() in _hu and " " in cat:
        cat = cat.rsplit(" ", 1)[0]
    return cat if len(cat) >= tran * 0.4 else t[:tran]


# ══ CHIA NHỊP ════════════════════════════════════════════════════════════════════════════════
def chia_nhip(nhip0: list, moc: list, tu: list, tong: float) -> list:
    """Trả danh sách nhịp MỚI: mỗi phần tử là một khung phim, không phần tử nào quá `TRAN_NHIP`.

    Chia tại MỐC TỪ, không chia bằng cách lấy nửa thời lượng: cắt giữa một từ thì phụ đề của
    hai nửa đều sai, và cắt hình giữa một từ nghe ra như video bị lỗi.

    Lớp dữ liệu chỉ gắn vào nửa ĐẦU. Nửa sau là cùng một câu nói tiếp, phủ lại con số lần nữa
    là đúng cái lỗi "một câu hai chỗ" vừa nói ở `lop_du_lieu`."""
    ra = []
    for i, n in enumerate(nhip0):
        s = float(moc[i][0])
        e = float(moc[i + 1][0]) if i + 1 < len(moc) else min(tong, float(moc[i][1]) + 0.45)
        dn = max(0.35, e - s)
        phan = max(1, math.ceil(dn / TRAN_NHIP))
        if phan > 1:
            # Mốc chia mong muốn, rồi nắn về mốc từ gần nhất nằm trong khoảng.
            cat = [s + dn * k / phan for k in range(1, phan)]
            trong = [w for w in tu if s + 0.25 < w["t"] < e - 0.25]
            diem = [s]
            for c in cat:
                if trong:
                    w = min(trong, key=lambda w: abs(w["t"] - c))
                    if w["t"] - diem[-1] > 0.45:
                        diem.append(w["t"])
                elif c - diem[-1] > 0.45:
                    diem.append(c)
            diem.append(e)
        else:
            diem = [s, e]
        for k in range(len(diem) - 1):
            a, b = diem[k], diem[k + 1]
            chu = " ".join(w["w"] for w in tu if a - 0.02 <= w["t"] < b) or n.get("loi", "")
            ra.append({"s": round(a, 3), "e": round(b, 3),
                       "loi": n.get("loi", ""), "cua": chu,
                       "goc": i, "phan": k, "tong_phan": len(diem) - 1,
                       "dinh": bool(n.get("dinh")) and k == 0,
                       "lop": lop_du_lieu(n) if k == 0 else None})
    return _gop_ngan(ra)


# Sàn 1,3 giây. Anh nói "1.5 tới 2.5s"; sàn đặt thấp hơn đích một chút vì mốc từ không rơi
# đúng chỗ mình muốn, và ép đúng 1,5 s sẽ đẩy nhịp bên cạnh vượt trần 2,6 s — hai ràng buộc
# kéo ngược nhau thì phải chừa dung sai, nếu không công thức chỉ mã hoá được một (§17.2).
#
# Vì sao phải có sàn: kịch bản có những câu ba chữ ("You make it.") đọc hết 0,6 giây. Một tấm
# ảnh hiện 0,6 giây đọc ra là một cú nháy, không phải một cảnh — và nó còn tốn đúng một lượt
# vẽ như mọi cảnh khác. Gộp vào cảnh bên cạnh thì vừa hết nháy vừa tiết kiệm hạn mức.
SAN_NHIP = 1.3


def _gop_ngan(ds: list) -> list:
    ra = []
    for n in ds:
        # Trần khi GỘP nới thêm 0,35 s so với trần khi CHIA. Hai phép ngược chiều nhau dùng
        # chung một trần thì có những nhịp không phép nào chạm tới được — đo thật: nhịp 0,97 s
        # đứng cạnh nhịp 1,9 s, gộp ra 2,87 s nên bị từ chối, và nó ở lại làm một cú nháy.
        # Một cảnh 2,87 giây tệ hơn một cảnh 0,97 giây rất nhiều lần ít hơn.
        if ra and (n["e"] - n["s"]) < SAN_NHIP and (n["e"] - ra[-1]["s"]) <= TRAN_NHIP + 0.35:
            t = ra[-1]
            t["e"] = n["e"]
            t["cua"] = (t["cua"] + " " + n["cua"]).strip()
            t["dinh"] = t.get("dinh") or n.get("dinh")
            if not t.get("lop"):
                t["lop"] = n.get("lop")
            continue
        ra.append(n)
    # Nhịp ĐẦU quá ngắn thì không có nhịp trước để gộp vào — gộp NGƯỢC vào nhịp sau.
    if len(ra) > 1 and (ra[0]["e"] - ra[0]["s"]) < SAN_NHIP \
            and (ra[1]["e"] - ra[0]["s"]) <= TRAN_NHIP:
        ra[1]["s"] = ra[0]["s"]
        ra[1]["cua"] = (ra[0]["cua"] + " " + ra[1]["cua"]).strip()
        ra[1]["lop"] = ra[0].get("lop") or ra[1].get("lop")
        ra[1]["dinh"] = ra[0].get("dinh") or ra[1].get("dinh")
        ra = ra[1:]
    return ra


# ══ PROMPT ẢNH ═══════════════════════════════════════════════════════════════════════════════
def prompt_anh(ma: str, canh: str, doc: bool, vai=None, kt: str = "") -> str:
    """PHONG CÁCH đứng đầu, rồi bố cục, rồi CẢNH, rồi câu an toàn.

    ── HAI LƯỢT ĐO, VÀ MỘT SAI LẦM VỀ PHƯƠNG PHÁP Ở GIỮA ──────────────────────────────────
    Lượt 1 (phong cách trước, `sang`/`may` còn lẫn nội dung): 8/8 khung ra CÙNG một cú cận mặt
    trong phòng khách, dù sổ cảnh viết đúng tám nơi khác nhau.
    Tôi kết luận "thứ tự sai" và đổi HAI thứ cùng lúc: dọn `sang`/`may` VÀ đảo thứ tự.
    Lượt 2 (cảnh trước): nội dung đúng hẳn nhưng ra ẢNH CHỤP, mất sạch chất hoạt hình.
    Hai lượt ấy chỉ chứng minh một điều: đổi hai biến cùng lúc thì không biết biến nào chữa
    được gì. Tách ra thì thủ phạm của lượt 1 là NỘI DUNG NẰM TRONG TRƯỜNG PHONG CÁCH, không
    phải thứ tự — nên giữ thứ tự đã chứng minh, giữ bản dọn hai trường.

    ── CHỈ GẮN NHỮNG VAI THẬT SỰ CÓ MẶT TRONG CẢNH  (6/9/2026) ──────────────────────────
    `vai` là DÀN VAI của cả tập, nhưng một khung chỉ có một hoặc hai người. Dán cả dàn vào mọi
    prompt là đặt hàng đúng cái đám đông không ai yêu cầu — và ở cỡ hình que thì bốn người
    giống nhau đọc ra là lỗi. Nên quét câu cảnh, chỉ gắn vai nào ĐƯỢC GỌI TÊN ở đó.
    """
    bo = GU.BO_CUC_DOC if doc else GU.BO_CUC_NGANG
    doo = (kt or GU.gu(ma)["kt"]) == "doo"
    ds = list(vai or [])
    # Cảnh đồ vật thì không gắn vai nào — thang cỡ cảnh cho phép ~1/3 số cảnh không có người,
    # và dán câu tả người vào một cảnh vừa nói "no person" là tự tay đặt hàng một hình thừa.
    trong = bool(re.search(r"\bno (?:person|people|one)\b|\bnobody\b", canh, re.I))
    if trong:
        ds = []
    else:
        ds = [v for v in ds if re.search(r"\b" + re.escape(v["vai"]) + r"s?\b", canh, re.I)]
        if not ds and vai:
            ds = [vai[0]]        # cảnh có người mà không gọi tên -> mặc định là vai chính
        # TRẦN HAI VAI MỖI KHUNG, và đây là lý do NỘI DUNG chứ không phải lý do ngân sách:
        # ở cỡ hình que, ba người trở lên trong một khung đọc ra là một đám giống nhau, không
        # đọc ra ba nhân vật. Hai người là đủ để có quan hệ, và là trần mà mắt còn phân biệt.
        ds = ds[:2]
    ai = GU.khoa_vai(ds)
    if trong:
        # Cảnh đồ vật mà mô hình vẫn nhét hai đứa bé vào — anh soi ra. FLUX không có negative
        # prompt, nên "no person" trong câu cảnh đọc ra như một danh từ NGƯỜI. Phải nói bằng
        # vế KHẲNG ĐỊNH về cái khung (§17.6): khung này là một tĩnh vật.
        ai = " This is a still life of the place and its objects only; the frame is completely empty."
    # Khung tĩnh vật thì KHÔNG kèm câu giải phẫu: nó tả một nhân vật không tồn tại, và mọi
    # danh từ trong prompt đều là thứ mô hình có thể vẽ ra (§17.6). Chính câu này là một lời
    # mời thêm người vào một khung vừa tuyên bố không có ai.
    gp = "" if (doo or trong) else GU.GIAI_PHAU + " "
    return f"{GU.khoi_look(ma, kt)} {bo} SCENE: {canh.strip()}{ai} {gp}{GU.AN_TOAN}"


def ca_xau_nhat() -> tuple:
    """Prompt DÀI NHẤT có thể sinh ra, đo bằng chính `prompt_anh`. Trả (số ký tự, mã kênh).

    Câu tả cảnh do AI viết nên không duyệt hết được — dùng trần 45 từ mà lệnh hệ thống đặt ra,
    quy đổi 7,2 ký tự/từ (đo trên 240 câu thật của một lượt chạy)."""
    # Ca xấu nhất: câu cảnh dài nhất lệnh dặn cho phép, CỘNG cả dàn vai bốn người cùng xuất
    # hiện — vì `prompt_anh` gắn mọi vai được gọi tên, và bốn vai là trần của `dan_vai`.
    canh = "x" * int(45 * 7.2) + " nurse patient doctor visitor"
    vai = [{"vai": v, "ta": "x" * 90} for v in ("nurse", "patient", "doctor", "visitor")]
    # `prompt_anh` tự cắt còn 2 vai, nên ca xấu nhất thật là 2 vai — nhưng vẫn đưa cả 4 vào
    # để cổng đo CHÍNH phép cắt ấy, không đo một giả định về nó.
    xau = max(((len(prompt_anh(m, canh, True, vai, k)), m + "/" + (k or "gốc"))
                for m in GU.KENH for k in ("", "doo")), key=lambda x: x[0])
    return xau


class ThieuAnh(RuntimeError):
    """Tập này chưa đủ ảnh riêng cho mọi nhịp -> HOÃN tập, không dựng.

    Khác `HoCan`: hồ vẫn còn hạn mức, chỉ tập này chưa xong (prompt bị chặn, mạng hụt, cổng
    ảnh loại). Nên chỉ bỏ MỘT tập rồi đi tiếp, không dừng cả mẻ."""


class HoCan(RuntimeError):
    """Hết hạn mức ảnh — KHÔNG phải lỗi lập trình.

    Dùng `RuntimeError` chứ không `SystemExit` (§13.3): `SystemExit` kế thừa `BaseException`
    nên `except Exception` không bắt được, và nó xuyên qua mọi vòng xoay để giết cả tiến trình
    — đúng lỗi đã làm chết 18/18 luồng một lần rồi.
    Vòng lặp ở `main` bắt riêng nó để DỪNG CẢ MẺ (dựng thêm cũng vô ích khi hồ cạn), khác với
    lỗi thường thì chỉ bỏ một tập."""


# ══ MỘT TẬP ══════════════════════════════════════════════════════════════════════════════════
def mot_tap(ma: str, idx: int, doc: bool = True, long: bool = False, so_chuong: int = 3,
            khong_anh: bool = False, luong: int = 6, kieu: str = "") -> str:
    os.environ.setdefault("GT_KHONG_CF", "1")     # `kich_ban` KHÔNG được tự gọi CF của bộ cũ
    import giai_thich as G
    from kich_hai import doc_hai_giong

    k, tieu, hook, hook_phu, nhip0, muc = G.kich_ban(ma, idx, long, so_chuong)
    if not k:
        return ""
    g = GU.gu(ma)
    slug = f"v10_{ma}_{idx:04d}" + ("_long" if long else "")
    print(f"\n▶ {g['ten']} · {tieu}", flush=True)

    # ── GIỌNG ─────────────────────────────────────────────────────────────────────────────
    gr = G.GU_RIENG.get(ma, ("en-US-GuyNeural", "music/forecast.mp3", ""))
    h = sum(ord(c) for c in ma)
    ga = (gr[0], f"{-8 + h % 9}%", f"{-4 + h % 7}Hz")
    loi = [n["loi"] for n in nhip0]
    rel_mp3 = f"{slug}.mp3"
    dur, tu, moc = doc_hai_giong([(t, 0, "trung_tinh") for t in loi], ga, ga,
                                 os.path.join(PUB, rel_mp3))
    if not tu or len(moc) < len(nhip0):
        print("   ❌ thiếu mốc giọng đọc — BỎ")
        return ""

    nhip = chia_nhip(nhip0, moc, tu, dur)
    dai = [n["e"] - n["s"] for n in nhip]
    dai_s = sorted(dai)
    print(f"   🎬 {len(nhip0)} câu -> {len(nhip)} cảnh · trung vị "
          f"{dai_s[len(dai_s)//2]:.2f}s · dài nhất {max(dai):.2f}s · {dur:.1f}s")

    # ── BẢNG PHÂN CẢNH ────────────────────────────────────────────────────────────────────
    _doo = (kieu or GU.gu(ma)["kt"]) == "doo"
    vai = C.dan_vai(ma, tieu, GU.the_gioi(ma), doo=_doo)
    if vai:
        print("   🎭 dàn vai: " + " · ".join(f"{v['vai']}={v['ta']}" for v in vai))
    nv = "\n".join(f"- {v['vai']}: {v['ta']}" for v in vai)

    # ── DÙNG LẠI SỔ CẢNH CŨ NẾU CÓ  (6/9/2026) ────────────────────────────────────────
    # Ảnh đã có cache theo VÂN TAY PROMPT, nên chạy lại một tập lẽ ra tốn 0 lượt vẽ. Nhưng nó
    # KHÔNG tốn 0: bảng phân cảnh do AI viết nên mỗi lượt ra một câu khác, prompt khác, vân
    # tay khác — cache trượt sạch và cả tập vẽ lại từ đầu.
    # Nghĩa là "chạy lại được" chỉ đúng trên giấy: job chết giữa chừng, mốc cron sau chạy lại,
    # và nó trả tiền lần thứ hai cho đúng những cảnh đã vẽ xong. Đây là chỗ đắt nhất mà không
    # ai thấy, vì nhìn từ log nó y hệt một lượt chạy bình thường.
    # Sổ cảnh ghi sẵn ra `out/<slug>.canh.json`; nay ĐỌC nó trước. Chỉ nhận khi số cảnh khớp
    # đúng số nhịp — kịch bản đổi thì sổ cũ vô nghĩa và phải viết lại.
    # TÊN BIẾN KHÔNG ĐƯỢC TRÙNG TÊN HÀM ĐANG DÙNG TRONG CÙNG PHẠM VI. Bản đầu đặt `_so`, mà
    # `mot_tap` gọi `_so(x.get("so"))` ở khối hook mấy chục dòng sau — biến chuỗi che mất hàm,
    # và lỗi ra là `TypeError: 'str' object is not callable`, không nói gì về nguyên nhân.
    # §15.8 đã ghi đúng bài này ở `storage.py`: `grep "def <tên>"` trước khi đặt tên.
    _so_canh = os.path.join(RA, f"{slug}.canh.json")
    canh = None
    if os.path.exists(_so_canh):
        try:
            _cu = json.load(io.open(_so_canh, encoding="utf-8"))
            if len(_cu) == len(nhip) and all(x.get("canh") for x in _cu):
                canh = [x["canh"] for x in _cu]
                print(f"   ♻ dùng lại sổ cảnh cũ ({len(canh)} cảnh) — không gọi AI, không vẽ lại")
        except Exception as e:
            print(f"   ⚠ sổ cảnh cũ đọc hỏng ({type(e).__name__}) — viết lại")
    if canh is None:
        canh = C.dao_dien(ma, tieu, [n["cua"] or n["loi"] for n in nhip], GU.the_gioi(ma), nv)
    for n, c in zip(nhip, canh):
        n["canh"] = c

    # ── ẢNH ───────────────────────────────────────────────────────────────────────────────
    if not khong_anh:
        # KHOÁ NẠP LẠI Ở MỖI TẬP, không nạp một lần lúc khởi động: thêm khoá mới vào secret
        # (hoặc vào `.keys.local`) là tập kế tiếp dùng được ngay, không phải khởi động lại gì.
        ks = A.khoa()
        _song, _tong = A.suc_khoe(ks)
        print(f"   🔑 CF {_song}/{_tong} tài khoản còn hạn mức · {len(ks['gem'])} khoá Gemini")
        if _song == 0:
            # HỒ CẠN SẠCH -> DỪNG HẲN, không dựng. Dựng tiếp sẽ ra một video mà mọi nhịp dùng
            # chung một tấm ảnh mượn — trông như hỏng, mà vẫn được đẩy đi như hàng hoàn chỉnh.
            # Đó đúng §12.8: hỏng mà vẫn báo xanh, dạng tệ nhất.
            raise HoCan(f"hồ CF cạn sạch ({_tong}/{_tong} tài khoản) — dừng, "
                        f"chờ hạn mức hồi rồi mốc cron sau tự chạy lại")
        t0 = time.time()
        viec = [(i, prompt_anh(ma, n["canh"], doc, vai, kieu)) for i, n in enumerate(nhip)]
        anh = A.ve_nhieu(viec, ma, idx, doc, ks, luong=luong,
                         bao=lambda a, b: print(f"      vẽ {a}/{b}", end="\r", flush=True))
        for n, p in zip(nhip, anh):
            n["anh"] = p
        co = sum(1 for n in nhip if n.get("anh"))
        print(f"   🖼 {co}/{len(nhip)} cảnh có ảnh AI · {time.time()-t0:.0f}s · "
              f"{A.tong_ket()}")
        # ── KHÔNG MƯỢN ẢNH. MỘT NHỊP MỘT ẢNH RIÊNG, HOẶC BỎ TẬP.  (6/9/2026) ──────────
        # Anh: *"ko lấy ảnh lung tung là giảm chất lượng videos rác em nha."*
        #
        # Bản trước thiếu ảnh thì mượn ảnh nhịp liền trước. Nghe như một tầng đỡ tử tế, thực
        # ra nó là cách chắc chắn nhất để giao hàng rác: hồ cạn giữa tập thì mọi nhịp còn lại
        # dùng chung một tấm ảnh, video vẫn đủ thời lượng, vẫn có tiếng, vẫn đủ bộ giao hàng —
        # nên nó đi thẳng lên kho như một tập hoàn chỉnh. Hỏng mà báo xanh (§12.8), và lần này
        # cái hỏng là thứ người xem nhìn thấy đầu tiên.
        #
        # Sàn 100%. Bỏ tập KHÔNG mất gì đáng kể, vì sổ cảnh và cache ảnh đều giữ nguyên: mốc
        # cron sau chạy lại và chỉ vẽ ĐÚNG những nhịp còn thiếu, những nhịp đã có lấy từ cache
        # với 0 lượt gọi. Tức "bỏ tập" ở đây nghĩa là "hoãn tập", không phải "mất tập".
        thieu = [i for i, n in enumerate(nhip) if not n.get("anh")]
        if thieu:
            raise ThieuAnh(f"{len(thieu)}/{len(nhip)} nhịp chưa có ảnh riêng "
                           f"(nhịp {thieu[:6]}{'…' if len(thieu) > 6 else ''}) — HOÃN tập, "
                           f"không mượn ảnh. Lượt sau chỉ vẽ phần thiếu. Lý do: {A.tong_ket()}")

    # ── HOOK: LỜI HỨA PHẢI Ở NHỊP 0  (6/9/2026) ───────────────────────────────────────
    # Đo bản short `dayinlife`: con số đầu tiên xuất hiện ở giây 8,2 — 48% thời lượng. Với
    # short thì đó là hỏng: người xem quyết định ở lại hay lướt trong ~400ms đầu, và thứ giữ
    # họ ở một kênh giải thích là LỜI HỨA — một con số đủ lớn để muốn biết nó ở đâu ra.
    #
    # `kich_ban` trả sẵn `hook_phu` ("$295K OVER 30 YEARS") mà em CHƯA ĐỌC LẦN NÀO. Kênh nào
    # `hook_phu` rỗng (dayinlife) thì nhấc con số lớn nhất của chính tập lên làm lời hứa —
    # nó vẫn là số thật của tập ấy, chỉ đổi chỗ xuất hiện.
    if not nhip[0].get("lop"):
        lo = None
        if hook_phu and hook_phu.strip():
            pp = hook_phu.strip().split(" ", 1)
            lo = {"k": "so", "so": pp[0], "don": (pp[1] if len(pp) > 1 else ""), "nhan": ""}
        else:
            ung = [n["lop"] for n in nhip if (n.get("lop") or {}).get("k") == "so"]
            if ung:
                lo = max(ung, key=lambda x: _so(x.get("so")) or 0)
        if lo:
            nhip[0]["lop"] = lo

    # ── NHÃN CHƯƠNG (bản dài) ─────────────────────────────────────────────────────────────
    if long and muc:
        for m in muc:
            j = m.get("nhip") if isinstance(m, dict) else None
            if j is None:
                continue
            for n in nhip:
                if n["goc"] == j and n["phan"] == 0:
                    n["moi"] = True
                    if not n.get("lop"):
                        n["lop"] = {"k": "nhan", "chu": str(m.get("ten") or "")[:26]}
                    break

    # ── KẾT GHÉP VÒNG PHẢI Ở NỘI DUNG, KHÔNG PHẢI Ở TỆP ẢNH  (sửa 6/9/2026) ───────────
    # Bản đầu gán thẳng `nhip[-1]["anh"] = nhip[0]["anh"]`. Anh soi ra ngay: khung cuối của
    # tập `dayinlife` là **hành lang ngập nước, đèn báo động đỏ** — trong khi lời của nhịp ấy
    # là *"For the rest of it."*, một câu đóng trầm. Và sổ cảnh cho thấy nhịp cuối ĐÃ CÓ cảnh
    # riêng của nó (*"turning away, she glances toward the medication cart"*) — em ném đi một
    # cảnh đúng để lấy một vòng lặp hình.
    #
    # Vòng lặp ấy sinh ra để người xem không thấy chỗ nối khi video tự phát lại (§13.16), mà
    # điều kiện của nó là hai khung PHẢI CÙNG MỘT NƠI — không phải cùng một tệp. Nên nay việc
    # ấy giao cho ĐẠO DIỄN: luật số 10 bắt cảnh cuối quay về đúng nơi chốn của cảnh 0, ở một
    # thời điểm khác. Vòng vẫn khép, mà nhịp cuối vẫn nói đúng lời của nó.
    #
    # ── VÀ KHÔNG CÒN ĐƯỜNG MƯỢN NÀO, KỂ CẢ Ở ĐÂY  (6/9/2026) ──────────────────────────
    # Bản trước còn một nhánh dự phòng: nhịp cuối không vẽ được thì mượn ảnh nhịp 0. Cổng
    # `t_khong_muon_anh` bắt đúng dòng ấy — và nó đúng. Từ khi sàn ảnh là 100%, nhánh này là
    # mã chết: tập thiếu một ảnh đã bị HOÃN trước khi chạy tới đây. Giữ một nhánh mượn ảnh
    # "chỉ để phòng" là giữ đúng cái cửa mà lần sau sẽ có người mở lại.

    props = {
        "ma": ma, "tieuDe": tieu, "handle": "@" + ma, "phong": PHONG.get(ma, "poppins"),
        "chinh": g["chinh"], "phu": g["phu"], "nen": g["nen"],
        "doc": doc, "dai": round(dur + 0.35, 2), "hat": h + idx,
        "voMp3": rel_mp3, "nhac": gr[1], "nhacVol": 0.17,
        "tu": tu,
        "nhip": [{"s": n["s"], "e": n["e"], "anh": n.get("anh") or "",
                  "lop": n.get("lop"), "dinh": n.get("dinh"), "moi": n.get("moi")}
                 for n in nhip],
    }
    pf = os.path.join(PUB, f"_{slug}.json")
    json.dump(props, io.open(pf, "w", encoding="utf-8"), ensure_ascii=False)
    # Sổ cảnh đi kèm: đọc được bảng phân cảnh mà không phải mở lại video. Đây là thứ duy nhất
    # cho phép soi "cảnh có khớp lời không" bằng mắt trong một phút.
    json.dump([{"loi": n["cua"], "canh": n["canh"], "anh": n.get("anh"),
                "s": n["s"], "e": n["e"]} for n in nhip],
              io.open(os.path.join(RA, f"{slug}.canh.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    os.makedirs(RA, exist_ok=True)
    out = os.path.join(RA, f"{slug}.mp4")
    comp = "PhimDoc" if doc else "PhimNgang"
    # ── DỰNG Ở 1440p, KHÔNG PHẢI 1080p  (6/9/2026) ──────────────────────────────────────
    # Anh: *"time máy dư thì render lâu hơn có làm tăng chất lượng không?"*
    #
    # Đo trước khi tin. Hai thứ KHÔNG được gì:
    #   · phóng ảnh nguồn bằng lanczos trước khi dựng -> ghép hai bản, gần như trùng khít.
    #     Trình duyệt đã nội suy tương đương; đây là công không đổi lấy gì.
    #   · nâng cỡ ẢNH NGUỒN -> tốn HẠN MỨC chứ không tốn thời gian. CF tính ~262 neuron/MP:
    #     768×1344 (1,03 MP) = 270 n -> 1,60 mẻ/ngày
    #     1080×1920 (2,07 MP) = 543 n -> 0,80 mẻ/ngày  <- thấp hơn đích 1,00, không mua nổi
    #
    # Thứ CÓ được, và nó thuần thời gian: dựng ở 1440×2560 rồi tải lên nguyên cỡ ấy. §15.16 đã
    # ghi lý do ở bộ thiên nhiên — YouTube cấp **codec và bitrate cao hơn hẳn cho tệp ≥1440p**,
    # nên cùng một khung hình, bản 1440 giữ được nhiều chi tiết hơn SAU KHI YouTube nén lại.
    # Với phim hoạt hình phẳng thì cái mất khi nén là **dải màu bệt (banding)** ở mảng lớn —
    # đúng chỗ 1440p cứu được. Ảnh nguồn vẫn 768 nên đây không phải "4K thật", mà là tránh
    # tầng nén tệ hơn; gọi đúng tên để phiên sau không tin nhầm (§15.16).
    #
    # Giá: pixel gấp 1,78 lần -> render lâu hơn ~1,8 lần. Trần thời gian đang là 24,4 mẻ/ngày
    # trong khi hạn mức chỉ cho 1,6 — thời gian là thứ duy nhất mình đang thừa.
    scale = float(os.environ.get("PHIM_SCALE") or 1.333)
    cmd = ["npx", "remotion", "render", "src/index.ts", comp, out,
           f"--props=./{os.path.relpath(pf, ENG)}", "--gl=swiftshader",
           f"--scale={scale}",
           "--jpeg-quality=100", "--crf=15", "--concurrency=2", "--log=error"]
    r = subprocess.run(cmd, cwd=ENG)
    if r.returncode or not os.path.exists(out):
        print("   ❌ render hỏng")
        return ""
    chuan_am(out)
    # BỘ GIAO HÀNG ĐỦ BỐN THỨ, không chỉ có video (§10.3). Nhịp 0 là hình hook do đạo diễn ép
    # thành khung sai trái nhất tập, nên ảnh bìa lấy ngay ở đó.
    D.giao_hang(slug, out, ma, g["ten"], tieu, hook, hook_phu, dur, long, nhip)
    print(f"   ✅ {out}")
    return out


# ══ CHUẨN ÂM ═════════════════════════════════════════════════════════════════════════════════
# Đo bản dựng đầu: short −19,9 LUFS · long −23,5 LUFS. YouTube, TikTok và Facebook đều chuẩn
# hoá về ≈ −14 LUFS, nên clip của mình phát NHỎ HƠN feed 6–9,5 dB. Người xem không phân tích
# được vì sao, họ chỉ thấy video này "yếu" hơn video trước nó — và đó là một dấu hiệu nghiệp dư
# đo được, không phải chuyện khẩu vị.
#
# Chỉ mã hoá lại TIẾNG, video `-c:v copy`: một lượt chuẩn âm mất vài giây thay vì vài phút, và
# không đụng gì tới chất lượng hình.
DICH_LUFS = -14.0


def chuan_am(mp4: str) -> bool:
    tam = mp4 + ".am.mp4"
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-c:v", "copy",
                        "-af", f"loudnorm=I={DICH_LUFS}:TP=-1.5:LRA=11",
                        "-c:a", "aac", "-b:a", "192k", tam], capture_output=True, text=True)
    if r.returncode or not os.path.exists(tam) or os.path.getsize(tam) < 10000:
        # Hỏng thì GIỮ bản gốc và NÓI RA — mất 6 dB còn hơn mất cả video, nhưng im lặng
        # thì lượt sau không ai biết mà sửa (§15.2).
        print(f"   ⚠ chuẩn âm hỏng, giữ bản gốc: {r.stderr[:90]}")
        if os.path.exists(tam):
            os.remove(tam)
        return False
    os.replace(tam, mp4)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="howlong")
    ap.add_argument("--tu", type=int, default=0)
    ap.add_argument("--so", type=int, default=1)
    ap.add_argument("--ngang", action="store_true")
    ap.add_argument("--long", action="store_true")
    ap.add_argument("--chuong", type=int, default=3)
    ap.add_argument("--khong-anh", action="store_true",
                    help="bỏ bước vẽ ảnh (chỉ để soi nhịp và lớp dữ liệu)")
    ap.add_argument("--kieu", default="",
                    help="ép kỹ thuật dựng hình cho lượt này (vd: doo) — chỉ để dựng thử")
    ap.add_argument("--luong", type=int, default=6,
                    help="số luồng VẼ ẢNH trong một tập (trần 8)")
    ap.add_argument("--tap-song-song", type=int, default=1,
                    help="số TẬP dựng cùng lúc; >2 thì các lượt render tranh CPU của nhau")
    a = ap.parse_args()
    ds = [x.strip() for x in a.kenh.split(",") if x.strip()] or list(GU.KENH)
    if a.long and not a.ngang:
        a.ngang = True
        print("   ↔ bản dài -> 16:9")
    don = [(de, a.tu + i) for de in ds for i in range(a.so)]

    dung = {"can": False}

    def chay(t):
        if dung["can"]:
            return ""
        try:
            return mot_tap(t[0], t[1], doc=not a.ngang, long=a.long, so_chuong=a.chuong,
                           khong_anh=a.khong_anh, luong=a.luong, kieu=a.kieu)
        except ThieuAnh as e:
            # Hoãn MỘT tập. Sổ cảnh + cache ảnh còn nguyên nên lượt sau vẽ nốt phần thiếu.
            print(f"   ⏭ {t[0]} tập {t[1]}: {e}")
            return ""
        except HoCan as e:
            # Hồ cạn là chuyện của CẢ MẺ, không của một tập: mọi tập sau sẽ cạn y hệt. Dựng
            # tiếp chỉ để đốt thời gian runner và sinh video hỏng.
            print(f"   ⛔ {t[0]} tập {t[1]}: {e}")
            dung["can"] = True
            return ""
        except Exception as e:                       # một tập hỏng không được giết cả mẻ
            print(f"   ❌ {t[0]} tập {t[1]}: {type(e).__name__}: {str(e)[:120]}")
            return ""

    # SONG SONG Ở MỨC TẬP: mỗi tập ghi tệp mang tên kênh + số tập nên không đè nhau, và hồ
    # khoá CF xoay theo băm của (kênh, nhịp) nên hai tập khác kênh gần như không bốc trùng
    # tài khoản. Nút thắt thật là `remotion render` — nó ăn 2 nhân mỗi tập, nên mặc định 1.
    if a.tap_song_song > 1 and len(don) > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(a.tap_song_song, len(don))) as ex:
            ra = [v for v in ex.map(chay, don) if v]
    else:
        ra = [v for v in (chay(t) for t in don) if v]
    print(f"\n✅ {len(ra)}/{len(don)} video")
    if dung["can"]:
        # Mã thoát 3 = HẾT HẠN MỨC, phân biệt với 1 = hỏng thật. Workflow đọc mã này để nghỉ
        # thay vì thử lại ngay — thử lại khi hồ cạn chỉ tốn thêm vòng mạng.
        print("   ⏸ dừng vì hết hạn mức ảnh — mốc cron sau sẽ chạy lại từ chỗ đang dở")
        return 3
    return 0 if ra else 1


if __name__ == "__main__":
    raise SystemExit(main())
