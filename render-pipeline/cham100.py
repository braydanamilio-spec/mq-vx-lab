#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THƯỚC 100 ĐIỂM cho một tập Kling — mười trục, mỗi trục 10 điểm.

Vì sao cần thước MỚI khi đã có `cham()`: `cham()` trả DANH SÁCH LỖI, tức chỉ biết ĐẠT/HỎNG.
Một tập không lỗi vẫn có thể nhạt — và 18/30 tập đang chạy đều "không lỗi" trong khi dùng
CÙNG MỘT cú lật. Thước cũ đo thứ nó được dạy để đo (luật 5, CLAUDE.md).

Bảy trục dưới đây đo được bằng máy. Ba trục có dấu (*) là chỗ máy chỉ đo được cái vỏ — điểm
cuối cùng ở đó vẫn phải do người đọc chấm.
"""
import re, json, collections

from kling_kenh import (HO_LAT, ho_lat as ho_cua, _giay_thoai as _gt,
                        CAU_GIU_HINH, CAU_CHOT_RAO)

# Đảo ngôi thứ: người chắc chắn hoá ra sai, hoặc người bị bỏ qua hoá ra đúng. Đây là CƠ CHẾ của
# trò đùa, không phải trang trí — thiếu nó thì cú lật chỉ là một sự việc nữa xảy ra.
DAO_NGOI = (r"\b(does not look|without looking|keeps smiling|does not move|exactly|"
            r"never looks?|holds? (his|her)|still (smiling|holding|kneeling))\b")

SAI_TRAI = r"\b(empty|open|stacked|leaning|spill\w*|smok\w*|stuck|missing|upside|backwards|" \
           r"soak\w*|frozen|melting|tilt\w*|scatter\w*|cover\w*|wrong|too (high|many|small))\b" \
           r"|\b(every|all of the|not one) \w+ (is|are|laid|stacked|lined|piled)"
GHIM = r"\b(static|locked[- ]off|eye[- ]level|wide shot|low angle|high angle|medium shot)\b"
SO_CHU = ("one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|"
          "fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|"
          "seventy|eighty|ninety|hundred|thousand|dozen")
CU_THE = r"(\b\d{1,4}\b|\b(" + SO_CHU + r")\b|\b(Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day\b|\$\d)"
NGUY = r"\b(sign|label|logo|brand|neon|screen reads|caption|subtitle|crowd|text)\b"
# Chỉ liệt kê ĐỒ CỐ ĐỊNH có thể vắng mặt ở một phòng. Sàn · tường · cửa · trần có ở MỌI phòng
# nên bắt lỗi chúng là bắt nhầm — đúng lỗi thước đã mắc ở vòng chấm đầu tiên.
CAM_DO = ("island","dishwasher","staircase","stairs","fireplace","balcony","pool","chandelier",
          "bookshelf","television","piano","treadmill","washing machine","dryer","pantry",
          "bar stool","basement","attic","microwave","oven","stove","sink","counter","cabinet",
          "refrigerator","couch","lamp","fence","tree","cooler","shelf","bulb","sedan","rail",
          "doormat","table","chair")
DONG_NGHIA = {"fridge": "refrigerator", "sofa": "couch", "icebox": "refrigerator"}


def cham100(tap, giay, hs, prompt_txt, kho=()):
    """kho = danh sách tap đã có, để đo trùng CƠ CHẾ chứ không trùng danh từ."""
    d, ghi = {}, {}
    lines = tap.get("lines") or []
    tu = [len(l["say"].split()) for l in lines]
    ke = " ".join(str(tap.get(k) or "") for k in ("hook","setup","escalate","payoff"))
    thoai = " ".join(l["say"] for l in lines)
    ca = (ke + " " + thoai)

    # 1 · HOOK — khung đầu phải SAI TRÁI, ghim máy, không lời
    h = tap["hook"]; p1 = 0
    p1 += 4 if len(h.split()) >= 12 else (2 if len(h.split()) >= 10 else 0)
    p1 += 3 if re.search(SAI_TRAI, h, re.I) else 0
    p1 += 2 if re.search(GHIM, h + " " + str(tap.get("setup") or ""), re.I) else 0
    p1 += 1 if '"' not in h else 0
    d["1. Hook — khung đầu sai trái, ghim máy"] = p1

    # 2 · CÚ LẬT — cơ chế, và cơ chế ấy có mới so với kho không (*)
    ho = ho_cua(tap)
    da = collections.Counter(ho_cua(t) for t in kho)
    p2 = 0
    # ĐỘ HIẾM trong kho — "khác" là chưa từng có, tức hiếm nhất, chứ không phải hỏng.
    lan = len(kho) if ho == "khác" else da.get(ho, 0)
    lan = 0 if ho == "khác" else lan
    p2 += 5 if lan <= max(2, len(kho) // 8) else (2 if lan <= len(kho) // 3 else 0)
    p2 += 3 if ho != "nhấc-lộ-vô-hại" else 0          # họ đã mòn 18/30 lần
    p2 += 2 if re.search(DAO_NGOI, tap["payoff"], re.I) else 0
    d["2. Cú lật — cơ chế mới, không lặp kho"] = p2
    ghi["2"] = f"họ = {ho} · kho đã dùng {da.get(ho,0)}/{len(kho)} lần"

    # 3 · RIÊNG NHÂN VẬT (*) — lời ai nấy nói: mỗi vai nói đúng một lần trở lên, không ai độc thoại
    ai = collections.Counter(l["who"] for l in lines)
    p3 = 0
    p3 += 4 if len(ai) >= 2 else 0
    p3 += 3 if max(ai.values(), default=9) <= max(2, len(lines) - 1) else 0
    p3 += 3 if len(set(tu)) > 1 else 0               # độ dài lời khác nhau = giọng khác nhau
    d["3. Lời ai nấy nói, không hoán đổi được"] = p3

    # 4 · CỤ THỂ — một con số / một ngày có tên
    d["4. Cụ thể — số thật, không nói chung chung"] = 10 if re.search(CU_THE, ca) else 4

    # 5 · NGÂN SÁCH THOẠI theo đúng độ dài
    tran = int(_gt(giay) * 2.7); p5 = 0
    p5 += 3 if sum(tu) <= tran else 0
    p5 += 2 if all(x <= 9 for x in tu) else 0
    p5 += 2 if len(lines) <= 4 else 0
    p5 += 2 if tu and tu[-1] == min(tu) else 0        # câu chốt là câu ngắn nhất
    p5 += 1 if tu and sum(tu) >= tran * 0.5 else 0    # không im lặng quá nửa
    d["5. Ngân sách thoại khớp thời lượng"] = p5
    ghi["5"] = f"{sum(tu)}/{tran} từ · dòng cuối {tu[-1] if tu else 0} từ (ngắn nhất {min(tu) if tu else 0})"

    # 6 · DÀN & MÁY
    comat = [t for t in hs["vai"] if t in ke or any(l["who"] == t for l in lines)]
    p6 = 0
    p6 += 5 if len(comat) <= 4 else 0
    p6 += 3 if re.search(GHIM, ke, re.I) else 0
    p6 += 2 if not re.search(r"\b(everyone|all of them|the family) (runs?|rushes?|scrambl)", ca, re.I) else 0
    d["6. Dàn ≤4 mặt, góc máy ghim"] = p6

    # 7 · PHÒNG — mọi đồ cố định phải có trong khoá phòng
    ta = hs["phong"].get(tap["room"], "").lower()
    _ca = ca.lower()
    for _a, _b in DONG_NGHIA.items():
        _ca = re.sub(r"\b" + _a + r"\b", _b, _ca)
    la = [x for x in CAM_DO if re.search(r"\b"+x+r"\b", _ca) and x not in ta]
    d["7. Chỉ dùng đồ căn phòng thật có"] = 10 if not la else max(0, 10 - 4*len(la))
    if la: ghi["7"] = "đồ không có trong phòng: " + ", ".join(la)

    # 8 · CHỐT & VÒNG LẶP
    p8 = 0
    p8 += 4 if CAU_GIU_HINH.lower() in prompt_txt.lower() else 0
    p8 += 3 if not re.search(r"\b(walks? away|fade|smiles? at each other|everyone laughs)\b", tap["payoff"], re.I) else 0
    p8 += 3 if '"' not in tap["payoff"] else 0        # cú chốt bằng HÌNH, không bằng lời giải thích
    d["8. Kết đúng trên cú chốt, ghép vòng được"] = p8

    # 9 · AN TOÀN RENDER
    x = re.findall(NGUY, ca, re.I)
    d["9. Không kích hoạt lỗi Kling"] = 10 if not x else max(0, 10 - 5*len(set(x)))
    if x: ghi["9"] = "từ nguy hiểm: " + ", ".join(sorted(set(x)))

    # 10 · PROMPT VỪA TRẦN & HÀNG RÀO CÒN NGUYÊN
    n = len(prompt_txt); p10 = 0
    p10 += 6 if n <= 2500 else 0
    p10 += 2 if n >= 1800 else 0
    # Hàng rào còn nguyên = prompt kết thúc ĐÚNG câu chốt của khối DO NOT, dựng từ
    # cùng một hằng số mà engine dùng. So chuỗi chép tay là cách chắc chắn để thước
    # và engine lệch nhau sau lần sửa câu chữ đầu tiên.
    _chot = CAU_CHOT_RAO.format(g=f"{giay:g}")
    p10 += 2 if "DO NOT:" in prompt_txt and prompt_txt.rstrip().endswith(_chot) else 0
    d["10. Prompt ≤2500 ký tự, hàng rào nguyên"] = p10
    ghi["10"] = f"{n} ký tự"
    return d, ghi



