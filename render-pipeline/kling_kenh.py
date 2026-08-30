#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KLING KÊNH — sinh prompt Kling có KHOÁ NHÂN VẬT, để một kênh phim hoạt hình chạy hàng trăm
tập mà dàn diễn viên không đổi mặt. (30/8/2026)

VÌ SAO PHẢI CÓ TỆP NÀY, TRONG KHI ĐÃ CÓ kling_studio.py
--------------------------------------------------------
`kling_studio` để **AI viết trọn prompt**. Với phim ngắn một tập thì được. Với một KÊNH thì hỏng,
và hỏng theo đúng cách anh nhìn thấy: mỗi lần AI viết lại phần tả nhân vật, nó đổi một chi tiết —
tóc nâu thành tóc hạt dẻ, áo trắng thành áo kem, 42 tuổi thành "trung niên". Kling vẽ đúng cái nó
đọc được, nên mười tập ra mười người khác nhau. **Nhân vật không trôi vì Kling kém; nó trôi vì
mình đưa cho Kling mười bản mô tả khác nhau.**

NGUYÊN TẮC GỐC CỦA TỆP NÀY — MỘT CÂU
------------------------------------
    AI chỉ được viết phần CHUYỆN. Bốn khối khoá do MÃ ghép vào, nguyên văn, không qua tay AI.

Prompt gửi Kling có sáu khối. Bốn trong sáu là HẰNG SỐ, y hệt nhau ở mọi tập của cùng một kênh:

    CHARACTER LOCK ....... ai, mặt mũi, quần áo, tuổi, tính nết      (hằng)
    LOCATION LOCK ........ nhà cửa, phòng ốc, màu tường, đồ đạc      (hằng)  ← bộ 500 THIẾU khối này
    VISUAL STYLE LOCK .... nét vẽ, màu, khổ hình                     (hằng)
    AUDIO STYLE LOCK ..... giọng, tiếng động, cách thoại             (hằng)
    TIMING AND STORY ..... chuyện của TẬP NÀY                        (biến)  ← chỗ duy nhất AI viết
    PERFORMANCE + RENDER . cách diễn, điều kiện xuất                 (hằng)

LOCATION LOCK LÀ PHẦN MỚI, VÀ NÓ QUAN TRỌNG NGANG CHARACTER LOCK
----------------------------------------------------------------
Bộ 500 prompt cũ khoá người mà không khoá nhà. Kết quả xem lại thấy ngay: cùng "the kitchen" mà
tập này bếp trắng đảo giữa, tập kia bếp gỗ sát tường. Người xem không gọi tên được lỗi ấy, nhưng
họ cảm thấy **đây không phải cùng một gia đình** — và đó đúng là thứ giết một kênh sitcom hoạt
hình, nơi khán giả quay lại vì thấy quen chứ không vì thấy mới.

VÌ SAO PROMPT DÀI ~2800 KÝ TỰ, KHÔNG PHẢI 2800 TỪ
--------------------------------------------------
Bộ 500 của anh đo được 424 từ / 2970 ký tự mỗi prompt. Kling cắt phần đuôi khi prompt quá dài, mà
đuôi chính là RENDER REQUIREMENTS ("no extra limbs, no text overlays…") — mất khối đó là mất luôn
hàng rào chống lỗi. Nên trần ở đây đặt theo KÝ TỰ, và đặt đúng bằng bộ đang chạy tốt.

BỘ 500 CŨ VẪN DÙNG ĐƯỢC
------------------------
Dàn Mike / Lisa / Tommy / Grandpa Joe / Buddy giữ **nguyên văn** từ bộ 500 anh đang có. Tập mới
sinh ra khớp thẳng vào kho cũ, không phải vẽ lại ai.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KHO = os.path.join(HERE, "out", "kling")

# ── NHỊP KỂ ─────────────────────────────────────────────────────────────────────────────────
# Bốn mốc, theo TỈ LỆ chứ không theo giây, để một kịch bản dùng được cho clip 5s hay 10s mà nhịp
# không vỡ. Tỉ lệ lấy đúng từ bộ 500 đang chạy tốt: với T=8s ra 0-1.5 / 1.5-4.5 / 4.5-6.5 / 6.5-8.
MOC = (0.1875, 0.5625, 0.8125)

# Kling web chỉ cho chọn vài mốc thời lượng cố định tuỳ phiên bản model. Đây là các mốc hay gặp;
# anh nhập số nào thì hệ dựng nhịp theo số ấy, vì chỉ anh mới biết giao diện mình đang có gì.
GIAY_CHUAN = (5, 6, 8, 9, 10)

# ── GIỚI HẠN THẬT CỦA KLING, DÙNG ĐỂ CHẤM KỊCH BẢN ──────────────────────────────────────────
# Không phải để trang trí. Mỗi con số dưới đây là một lần render hỏng đã trả giá.
TU_MOI_GIAY = 2.7          # người Mỹ thoại tự nhiên ~2,7 từ/giây. Quá số này là nói như đọc rap.
TU_MOI_LUOT = 9            # một lượt dài hơn 9 từ thì Kling khớp miệng bắt đầu trượt.
LUOT_TOI_DA = 4            # quá 4 lượt trong 8 giây là cắt cảnh liên tục, mặt ai cũng kịp méo.
VAI_TOI_DA = 4             # quá 4 người trong khung thì Kling chia ngân sách khuôn mặt -> nát cả 4.
# Trần ký tự. Kling CẮT ĐUÔI prompt quá dài, mà đuôi là RENDER REQUIREMENTS — mất khối đó là mất
# hàng rào chống "thêm tay, thêm chân, chữ loằng ngoằng". Nên không bao giờ để tràn rồi phó mặc:
# `prompt()` tự CO cho vừa, và co theo thứ tự GIÁ TRỊ chứ không cắt bừa phần cuối.
KY_TU_MIN, KY_TU_MAX = 2400, 3000
VONG_VIET = 8              # số lần cho AI viết lại một tập. Dây chuyền để 3 — hợp cho việc trích
                           # dữ liệu, quá ít cho việc sáng tác: kịch bản hỏng nhịp thường tới lần
                           # thứ tư, thứ năm mới ra được bản dùng được.

GHIM_MAY = ("static", "eye-level", "eye level", "low angle", "high angle", "wide shot",
            "medium shot", "close shot", "over-the-shoulder", "locked-off", "top-down")

DO_TO = ("island", "dishwasher", "staircase", "stairs", "fireplace", "balcony", "pool",
         "chandelier", "bookshelf", "bookcase", "television", "tv screen", "piano", "treadmill",
         "washing machine", "dryer", "pantry", "bar stool", "kitchen bar", "breakfast bar",
         "second floor", "hallway", "basement", "attic", "elevator", "escalator")

CAM_KY = [
    ("subtitle", "Kling vẽ chữ ra ký tự loằng ngoằng — chữ để khâu ghép làm, không nhờ Kling"),
    ("caption", "như trên: chữ trên màn hình do ffmpeg vẽ, không để Kling vẽ"),
    ("text on screen", "như trên"),
    ("sign reads", "biển có chữ đọc được là chỗ Kling hỏng nặng nhất"),
    ("logo", "logo thương hiệu — vừa hỏng hình vừa vướng bản quyền"),
    ("simpson", "không nhái phim có thật; phong cách thì được, nhân vật thì không"),
    ("family guy", "như trên"),
    ("south park", "như trên"),
    ("crowd runs", "đám đông chuyển động nhanh — Kling biến họ thành bùn"),
]


# ── HỒ SƠ KÊNH ──────────────────────────────────────────────────────────────────────────────
# Mỗi kênh là một cuốn "sổ tay phim": dàn diễn viên, bối cảnh, nét vẽ, giọng, và loại chuyện kênh
# ấy kể. Thêm kênh mới = thêm một mục vào đây, không phải sửa mã.
KENH: dict[str, dict] = {

    "HOUSE RULES": {
        "ten": "HOUSE RULES",
        "mo_ta": "Sitcom hoạt hình gia đình Mỹ ngoại ô — bố tự tin sai, mẹ tỉnh khô, con nhanh mồm.",
        "ty_le": "9:16",

        # Giữ NGUYÊN VĂN từ bộ 500 prompt anh đang có. Đổi một chữ ở đây là 500 tập cũ lệch khỏi
        # tập mới — cái giá cao hơn nhiều so với bất kỳ cải tiến câu chữ nào.
        # Giữ NGUYÊN VĂN từng dòng từ bộ 500 prompt anh đang có. Đổi một chữ ở đây là 500 tập
        # cũ lệch khỏi tập mới — cái giá cao hơn bất kỳ cải tiến câu chữ nào.
        # Tách theo TÊN vì prompt chỉ chèn người CÓ MẶT trong tập: Kling có thói quen kéo vào
        # khung bất cứ ai được tả kỹ, nên tả Grandpa Joe ở một tập không có ông là tự chuốc thêm
        # một cụ già đứng thừa ở nền. Khoá nằm ở chỗ CÙNG MỘT CHUỖI CHỮ mỗi lần người ấy xuất
        # hiện — không phải ở chỗ điểm danh đủ cả nhà.
        "nhan_vat": {
            "Mike": "Mike: 42-year-old man, slightly round body, short brown hair, white "
                    "short-sleeve shirt, blue pants, brown shoes; confident, clumsy, optimistic, "
                    "expressive eyebrows.",
            "Lisa": "Lisa: 39-year-old woman, shoulder-length reddish-brown hair, green shirt, "
                    "purple pants, white shoes; clever, practical, calm, dry sense of humor.",
            "Tommy": "Tommy: 10-year-old boy, messy brown hair, yellow hoodie, blue shorts, red "
                     "shoes; energetic, clever, playful, quick thinker.",
            "Grandpa Joe": "Grandpa Joe: 72-year-old man, white hair, large white mustache, red "
                           "cap, blue jacket, khaki pants; old-fashioned, confident, deadpan humor.",
            "Buddy": "Buddy: small orange cat, green eyes, expressive face; lazy, clever, "
                     "mischievous, silently judges the family.",
        },

        # KHỐI MỚI. Bộ 500 không có, và đó là lý do mười tập ra mười căn nhà.
        # Tách theo PHÒNG có chủ đích: prompt chỉ chèn căn phòng của tập ấy. Tả cả năm phòng
        # trong khi chỉ quay một phòng vừa làm prompt vượt trần, vừa làm Kling phân vân — nó
        # có thói quen trộn hai bối cảnh được tả gần nhau vào cùng một khung.
        "nha": (
            "The Miller house, a two-storey suburban American home with pale yellow siding and a "
            "white porch rail. Keep the exact same room layouts, wall colors, furniture shapes and "
            "camera geography in every episode. Never redesign or recolor the house."
        ),
        "phong": {
            "kitchen": "Kitchen: warm cream walls, honey-oak cabinets, a wide steel refrigerator "
                       "on the left, a round wooden table with four mismatched chairs.",
            "living room": "Living room: soft blue-grey walls, a worn brown three-seat couch "
                           "facing the camera, a low wooden coffee table, one tall standing lamp.",
            "backyard": "Backyard: mowed green lawn, a wooden fence, one old apple tree, a red "
                        "plastic cooler, the yellow siding of the house behind.",
            "garage": "Garage: grey concrete floor, a metal shelf of paint cans, one blue sedan, "
                      "a single hanging bulb.",
            "front porch": "Front porch: white rail, two wooden steps down to a short path, a "
                           "grey doormat, the pale yellow siding of the house behind.",
        },

        "style": (
            "Original 2D cartoon animation, original character designs, clean dark outlines, "
            "simple flat shapes, bright saturated colors, expressive facial animation, readable "
            "gestures, smooth limited animation, suburban American setting"
        ),
        # {vai} do mã điền theo người CÓ MẶT trong tập — xem chú thích ở `_ghep`.
        "audio": (
            "Natural American English dialogue, consistent distinct voices for {vai}, playful "
            "expressive delivery, precise lip sync, clean vocal recording, short conversational "
            "pauses, useful ambient sound effects, one clear comedic escalation and a strong "
            "final punchline"
        ),
        "dien": (
            "Mike is confident even when obviously wrong; Lisa is dry and practical; Tommy is "
            "clever and playful; Grandpa Joe is deadpan; Buddy communicates mostly through facial "
            "expressions and small actions"
        ),

        # Mạch kênh: thứ quyết định tập nào HỢP kênh, tập nào lạc. Dùng làm đề bài cho AI.
        "mach": (
            "Everyday American household friction blown one size too big: chores, groceries, "
            "thermostats, streaming passwords, school runs, weekend projects, holiday visits. "
            "One small domestic disagreement escalates for six seconds and lands on a reversal "
            "where the least likely family member turns out to be right."
        ),
    },
}


def ho_so(kenh: str) -> dict:
    k = KENH.get(kenh.upper().strip())
    if not k:
        raise SystemExit(f"❌ chưa có kênh {kenh!r}. Đang có: {', '.join(KENH)}")
    # `vai` suy từ khoá của `nhan_vat` chứ không chép tay: hai danh sách viết ở hai nơi thì sớm
    # muộn lệch nhau, và lúc lệch thì thước lại chê đúng nhân vật của kênh là "ngoài dàn".
    k.setdefault("vai", list(k["nhan_vat"]))
    return k


# ── DỰNG NHỊP THEO SỐ GIÂY ANH CHỌN ─────────────────────────────────────────────────────────
def nhip(giay: float) -> list[tuple[float, float, str]]:
    """Bốn khối thời gian cho clip dài `giay`. Trả [(bắt đầu, kết thúc, tên khối)]."""
    a, b, c = (round(giay * m, 1) for m in MOC)
    return [(0.0, a, "hook"), (a, b, "setup"), (b, c, "escalate"), (c, round(giay, 1), "payoff")]


def _giay_thoai(giay: float) -> float:
    """Thời gian thực sự có thoại = khối setup + escalate. Hook là hình, payoff giữ mặt phản ứng."""
    n = nhip(giay)
    return (n[1][1] - n[1][0]) + (n[2][1] - n[2][0])


# ── THƯỚC CHẤM KỊCH BẢN ─────────────────────────────────────────────────────────────────────
def don(d: dict) -> dict:
    """Sửa những lỗi máy sửa được, tại chỗ, trước khi đưa qua thước."""
    if not isinstance(d, dict):
        return d
    for ln in (d.get("lines") or []):
        if not isinstance(ln, dict):
            continue
        say = " ".join(str(ln.get("say") or "").split()).strip().strip('"“”')
        if say:
            if say[-1] not in ".!?":
                say += "."
            say = say[0].upper() + say[1:]
        ln["say"] = say
        ln["act"] = " ".join(str(ln.get("act") or "says").split()).strip() or "says"
    for k in ("hook", "setup", "escalate", "payoff", "title", "room"):
        if d.get(k):
            d[k] = " ".join(str(d[k]).split()).strip()
    return d


def cham(d: dict, kenh: str, giay: float) -> list[str]:
    """Chấm một tập theo đúng giới hạn Kling. Trả danh sách lỗi để bắt AI viết lại."""
    e: list[str] = []
    if not isinstance(d, dict):
        return ["không phải JSON object"]
    hs = ho_so(kenh)
    vai = set(hs["vai"])

    lines = d.get("lines")
    if not isinstance(lines, list) or not lines:
        return ["thiếu mảng lines (các lượt thoại)"]

    if len(lines) > LUOT_TOI_DA:
        e.append(f"{len(lines)} lượt thoại — quá {LUOT_TOI_DA} thì cắt cảnh liên tục, mặt méo")

    tong_tu = 0
    for i, ln in enumerate(lines, 1):
        if not isinstance(ln, dict):
            e.append(f"lượt {i}: không phải object"); continue
        who = str(ln.get("who") or "").strip()
        say = str(ln.get("say") or "").strip()
        if who not in vai:
            e.append(f"lượt {i}: nhân vật {who!r} không có trong dàn khoá ({', '.join(hs['vai'])})")
        if who == "Buddy" and say:
            e.append("Buddy là mèo — không được có thoại, chỉ biểu cảm và hành động")
        n = len(say.split())
        tong_tu += n
        # "Mike toast is burnt" / "I'll fix it butter" — AI bị ép ≤9 từ nên cắt cụt thành chuỗi
        # không còn là câu. Kling đọc được, nhưng diễn viên nói ra thì nghe như máy hỏng. Ép có
        # dấu kết câu là cách rẻ nhất bắt được cả hai kiểu cắt cụt trên.
        if say and say[-1] not in ".!?":
            e.append(f"lượt {i} ({who}): {say!r} — thiếu dấu kết câu, đây là mẩu chữ chứ chưa "
                     f"phải câu thoại")
        if n > TU_MOI_LUOT:
            e.append(f"lượt {i} ({who}): {n} từ — quá {TU_MOI_LUOT} thì Kling khớp miệng trượt")

    tran = int(_giay_thoai(giay) * TU_MOI_GIAY)
    if tong_tu > tran:
        e.append(f"tổng {tong_tu} từ thoại — clip {giay:g}s chỉ chứa nổi {tran} từ "
                 f"({TU_MOI_GIAY} từ/giây), quá là nói như đọc rap")

    for khoa in ("hook", "escalate", "payoff"):
        if not str(d.get(khoa) or "").strip():
            e.append(f"thiếu khối {khoa!r}")

    hook = str(d.get("hook") or "")
    if len(hook.split()) < 10:
        e.append(f"hook {len(hook.split())} từ — 1,5 giây đầu phải tả một hình ảnh SAI TRÁI thấy "
                 f"ngay, đủ chi tiết để Kling dựng được khung")
    # Bài học 09/08 đã trả giá bên kling_studio: hai thứ Kling trôi mạnh nhất là GÓC MÁY và THỜI
    # ĐẠI. Xin "góc nhìn người đứng dưới đất" mà không ghim thì ra cảnh quay flycam. Luật ấy đã
    # có ở tệp kia; để rơi ở tệp này là học lại một bài đã trả tiền.
    if not any(k in (hook + " " + str(d.get("setup") or "")).lower() for k in GHIM_MAY):
        e.append("không ghim góc máy — thêm 'static eye-level shot' / 'wide shot' / 'low angle' "
                 "vào hook hoặc setup, không thì Kling tự chọn và hay ra cảnh drone")

    pay = str(d.get("payoff") or "").lower()
    if not any(k in pay for k in ("reveal", "turn", "revers", "cut to", "reaction", "realiz",
                                  "holds up", "opens", "points", "walks in", "drops", "lifts",
                                  "pulls", "steps in", "appears", "hands", "shows", "swaps",
                                  "behind", "underneath", "was never", "already", "the whole")):
        e.append("payoff không có cú lật — phải ĐẢO tình thế, không phải tả thêm cảm xúc")

    ca = " ".join(str(d.get(k) or "") for k in ("hook", "setup", "escalate", "payoff")).lower()
    ca += " " + " ".join(str((l or {}).get("say") or "") for l in lines if isinstance(l, dict)).lower()
    for tu, ly in CAM_KY:
        if tu in ca:
            e.append(f"có {tu!r} — {ly}")
            break

    if not str(d.get("title") or "").strip():
        e.append("thiếu title")
    # Đông người là lỗi kịch bản, không phải lỗi prompt dài. Năm nhân vật trong tám giây thì
    # Kling phải chia ngân sách khuôn mặt cho năm người và làm nát cả năm; ba là vừa, bốn là
    # trần. Chặn ở đây thay vì để prompt phình rồi đi co chữ.
    ke = " ".join(str(d.get(k) or "") for k in ("hook", "setup", "escalate", "payoff"))
    comat = [t for t in hs["vai"]
             if t in ke or any(str((l or {}).get("who") or "") == t
                               for l in lines if isinstance(l, dict))]
    if len(comat) > VAI_TOI_DA:
        e.append(f"{len(comat)} nhân vật trong {giay:g} giây ({', '.join(comat)}) — quá "
                 f"{VAI_TOI_DA} thì Kling chia ngân sách khuôn mặt và làm nát hết. Bỏ bớt người.")

    ph = str(d.get("room") or "").strip().lower()
    ta = (hs["phong"].get(ph) or "").lower()
    for do in DO_TO:
        if do in ca and do not in ta:
            e.append(f"nhắc {do!r} — căn nhà không có thứ đó. Chỉ dùng đồ đã tả trong phòng "
                     f"({ph or '?'}), hoặc một món cầm tay nhân vật mang vào.")
            break
    if ph not in hs["phong"]:
        e.append(f"phòng {ph!r} không có trong nhà — chọn một trong: {', '.join(hs['phong'])}")
    return e


# ── GHÉP PROMPT HOÀN CHỈNH ──────────────────────────────────────────────────────────────────
def prompt(kenh: str, tap: dict, giay: float, so: int = 0, bien: int = 1,
           tran: int = KY_TU_MAX) -> str:
    """Ghép sáu khối thành prompt gửi Kling, tự co cho vừa `tran` ký tự.

    Bốn khối khoá lấy từ hồ sơ, KHÔNG qua tay AI. Nếu dài quá thì hạ MỨC CHI TIẾT theo đúng thứ
    tự giá trị: phần tả bối cảnh rườm rà đi trước, rồi phần dặn cách diễn — còn dàn nhân vật,
    chuyện của tập, và hàng rào RENDER thì không bao giờ đụng tới."""
    for muc in (0, 1, 2, 3):
        r = _ghep(kenh, tap, giay, so, bien, muc)
        if len(r) <= tran or muc == 3:
            return r
    return r


def _ghep(kenh: str, tap: dict, giay: float, so: int, bien: int, muc: int) -> str:
    hs = ho_so(kenh)
    n = nhip(giay)
    g = f"{giay:g}"
    ten = str(tap.get("title") or "Untitled")

    # Thoại xếp theo thứ tự, gộp vào khối setup — đúng cách bộ 500 đang làm và Kling đọc tốt.
    tho = []
    for ln in (tap.get("lines") or []):
        if not isinstance(ln, dict):
            continue
        who, say = str(ln.get("who") or ""), str(ln.get("say") or "").strip()
        act = str(ln.get("act") or "").strip()
        if say:
            tho.append(f'{who} {act or "says"}: “{say}”')
        elif act:
            tho.append(f"{who} {act}")
    thoai = " ".join(tho)

    r = [f"VIDEO {so:03d} — {ten} — Variation {bien}", ""]

    ke = " ".join(str(tap.get(k) or "") for k in ("hook", "setup", "escalate", "payoff"))
    comat = [t for t in hs["vai"]
             if t in ke or any(str((l or {}).get("who") or "") == t for l in (tap.get("lines") or []))]
    comat = comat or list(hs["nhan_vat"])
    r.append(f"CHARACTER LOCK — KEEP IDENTICAL ACROSS EVERY EPISODE OF {hs['ten']}:")
    r.append("\n".join(hs["nhan_vat"][t] for t in comat))
    r.append(f"Only these characters appear: {', '.join(comat)}. No other people in frame.")
    r.append("Keep exact same faces, body proportions, hair, clothing, colors, ages, "
             "personalities, and voice identity in every episode. Never redesign, recolor, age, "
             "or replace the characters.")
    r.append("")

    phong = str(tap.get("room") or "kitchen").strip().lower()
    r.append("LOCATION LOCK — KEEP IDENTICAL ACROSS EVERY EPISODE:")
    ta = hs["phong"].get(phong) or next(iter(hs["phong"].values()))
    if muc >= 1:
        # Mức 1: giữ TÊN phòng và những mốc mắt nhận ra ngay (màu tường, đồ lớn nhất), bỏ phần
        # liệt kê chi tiết. Kling giữ được bối cảnh bằng ba bốn mốc; phần còn lại chỉ tốn chỗ.
        ta = ", ".join(ta.split(", ")[:3]) + "."
    r.append(hs["nha"] if muc < 1 else hs["nha"].split(". ")[0] + ". Never redesign or recolor the house.")
    r.append(ta)
    r.append("")

    r.append("VISUAL STYLE LOCK:")
    r.append(f"{hs['style'] if muc < 2 else hs['style'].split(',')[0] + ', clean dark outlines, flat bright colors, expressive faces'}, vertical {hs['ty_le']}, exactly {g} seconds. No imitation of an "
             f"existing show, no recognizable copyrighted characters, no logos, no branded products.")
    r.append("")

    r.append("AUDIO STYLE LOCK:")
    nguoi = [t for t in comat if t != "Buddy"] or comat
    au = hs["audio"].format(vai=", ".join(nguoi)) if muc < 3 else ("Natural American English dialogue, consistent distinct "
                                      "voices, precise lip sync, one clear comedic escalation "
                                      "and a strong final punchline")
    r.append(f"{au}. No subtitles, no captions, no on-screen text.")
    r.append("")

    r.append("TIMING AND STORY:")
    r.append(f"{n[0][0]:.1f}–{n[0][1]:.1f}s: {str(tap.get('hook')).strip()}")
    r.append(f"{n[1][0]:.1f}–{n[1][1]:.1f}s: {str(tap.get('setup') or '').strip()} {thoai}".strip())
    r.append(f"{n[2][0]:.1f}–{n[2][1]:.1f}s: {str(tap.get('escalate')).strip()}")
    r.append(f"{n[3][0]:.1f}–{n[3][1]:.1f}s: {str(tap.get('payoff')).strip()} "
             f"Hold the final reaction for a fraction of a second.")
    r.append("")

    r.append("PERFORMANCE:")
    if muc < 1:
        r.append(f"Keep dialogue fast but natural for a {g}-second short. {hs['dien']}. Keep all "
                 f"spoken English concise enough to fit the timing. Only one character moves at "
                 f"a time; the others hold a readable pose and react with the face.")
    else:
        r.append(f"Fast but natural for {g} seconds. Only one character moves at a time; the "
                 f"others hold a readable pose and react with the face.")
    r.append("")

    r.append("RENDER REQUIREMENTS:")
    r.append(f"Exactly {g} seconds, vertical {hs['ty_le']}, crisp clean animation, readable "
             f"silhouettes, stable character identity, no character morphing, no extra limbs, no "
             f"text overlays, no subtitles, no watermark, no logos, no branded objects, no "
             f"recognizable existing characters or settings.")
    return "\n".join(r)


# ── SINH KỊCH BẢN BẰNG AI ───────────────────────────────────────────────────────────────────
# AI chỉ viết SÁU TRƯỜNG. Nó không thấy, không sửa, không được nhắc lại phần khoá nhân vật —
# đó là toàn bộ lý do dàn diễn viên đứng yên qua hàng trăm tập.
SCHEMA = """Return ONLY a JSON object with exactly these fields:
{
  "title":    "3-5 word episode title, no punctuation",
  "room":     "ROOM_LIST",
  "hook":     "one sentence describing the WRONG-LOOKING IMAGE the viewer sees in the first moment. A visual, not a feeling. No dialogue here.",
  "setup":    "one sentence of physical staging: who is where, doing what, camera angle pinned (static eye-level shot / low angle / wide shot)",
  "lines":    [{"who":"Mike","say":"spoken words","act":"says|snaps|whispers|mutters|announces"}],
  "escalate": "one sentence: the reaction grows, one small physical gag, one beat of silence",
  "payoff":   "one sentence: the REVERSAL. Something is revealed, someone walks in, an object turns out to be something else. Not just a bigger emotion."
}"""


def _sys(kenh: str, giay: float) -> str:
    hs = ho_so(kenh)
    tran = int(_giay_thoai(giay) * TU_MOI_GIAY)
    return (
        f"You write {giay:g}-second vertical cartoon shorts for an American channel called "
        f"{hs['ten']}.\n\n"
        f"THE SHOW: {hs['mo_ta']}\n"
        f"WHAT THIS CHANNEL IS ABOUT: {hs['mach']}\n\n"
        f"CAST YOU MAY USE (and only these): {', '.join(hs['vai'])}. Buddy is a cat and never "
        f"speaks.\n"
        f"ROOMS YOU MAY USE — the whole short happens in ONE room, nobody teleports in "
        f"{giay:g} seconds. These rooms exist and nothing else does:\n"
        + "".join(f"  · {k}  —  {v}\n" for k, v in hs["phong"].items())
        + "Only the furniture listed above exists. A character may carry in a small handheld "
          "prop (a mop, a bowl, a phone), but never invent fixed furniture — no island, no "
          "dishwasher, no staircase, no fireplace.\n\n"
        f"HARD LIMITS — these are physics, not preferences:\n"
        f"  · at most {VAI_TOI_DA} characters on screen in the whole short\n"
        f"  · at most {LUOT_TOI_DA} spoken lines total\n"
        f"  · at most {TU_MOI_LUOT} words per line\n"
        f"  · at most {tran} spoken words in the whole short\n"
        f"  · never write on-screen text, captions, signs or logos\n"
        f"  · never name a real brand or an existing TV show\n\n"
        f"WHAT MAKES THESE WORK IN AMERICA:\n"
        f"  · The first moment shows something ALREADY WRONG. Do not spend time establishing "
        f"normal. The viewer arrives mid-disaster.\n"
        f"  · Specific beats general. Not 'the bill is high' — 'nine hundred dollars'. Not 'he is "
        f"late' — 'it is Thursday'.\n"
        f"  · The funniest person is the one who is calm. Panic is not a joke; being unbothered "
        f"next to panic is.\n"
        f"  · The last line must REVERSE something, not summarise it. The viewer should want to "
        f"replay the first two seconds to check they missed it.\n"
        f"  · Dialogue is how real Americans actually talk to family: interrupting, understating, "
        f"answering a different question than the one asked."
    )


def _ho_key(keys=None) -> list:
    """Hồ key dùng chung với cả dây chuyền: `.keys.local` khi chạy tay, biến môi trường trên CI.

    Không tự đi tìm key riêng — một hồ key thứ hai là một chỗ nữa để hết hạn mức mà không ai
    biết, và là một chỗ nữa để key lọt ra ngoài."""
    if keys:
        return [k if isinstance(k, str) else k.get("key") for k in keys]
    try:
        import the_he_2 as T2
        return [k.get("key") for k in (T2.keys_cuc_bo() or []) if k.get("key")]
    except Exception:
        return []


def sinh_tap(kenh: str, y_tuong: str, giay: float = 8, api_key: str = None,
             tranh: list | None = None, keys: list | None = None, phong: str = "") -> dict:
    """Viết một tập. Viết lại tới khi qua hết thước. Trả dict sáu trường.

    Key cạn thì ĐỔI KEY chứ không bỏ cuộc — cùng bài học đã trả giá ở sáu hàm viết bên kia."""
    import content_brain as CB
    ho = ([api_key] if api_key else []) or _ho_key(keys) or [None]
    _n = {"i": 0}

    def _model():
        return CB._genai(ho[_n["i"] % len(ho)]).GenerativeModel(
            CB.MODEL, system_instruction=_sys(kenh, giay))

    model = _model()
    ne = ("\nDo not repeat these episodes already made: " + " | ".join(list(tranh)[-40:])) if tranh else ""
    if phong:
        ne += (f"\nThis episode MUST take place in the {phong} — not the kitchen, not anywhere "
               f"else. Build the joke out of what is actually in that room.")
    sch = SCHEMA.replace("ROOM_LIST", phong or " | ".join(ho_so(kenh)["phong"]))
    goc = f'Episode idea: "{y_tuong}".\n\n{sch}{ne}'
    fb, cuoi = "", None
    # Số vòng phải đủ để vừa viết lại kịch bản vừa duyệt hồ key. Trước đây dừng ở MAX_TRIES nên
    # gặp năm key hỏng liên tiếp là bỏ cuộc trong khi hồ còn 290 key chưa thử.
    for lan in range(1, VONG_VIET + len(ho) + 1):
        p = goc + (f"\n\nYour previous attempt was rejected for: {fb}\nFix every point." if fb else "")
        try:
            resp = model.generate_content(
                p, generation_config={"temperature": 0.95,
                                      "response_mime_type": "application/json"},
                request_options=CB.GEN_OPTS)
        except Exception as ex:
            low = str(ex).lower()
            # Hồ có gần ba trăm key ba nhà cung cấp. Một key cạn hạn mức, một key bị thu hồi, một
            # key gõ sai — cả ba đều KHÔNG phải lý do để bỏ cả tập. Bài học đã trả giá ở sáu hàm
            # viết bên kia: key hỏng thì ĐỔI KEY, đừng giết luồng. Lỗi 429 lẫn lỗi "API key not
            # valid" đều rơi vào đây, nên không lọc theo mã lỗi nữa — cứ đổi tới khi hết hồ.
            if _n["i"] + 1 < len(ho):
                _n["i"] += 1
                if _n["i"] % 25 == 0 or _n["i"] < 3:
                    print(f"   🔑 đổi key ({_n['i'] + 1}/{len(ho)}): {low[:60]}")
                model = _model()
                fb = ""
                continue
            if CB._loi_tam_thoi(low) and lan < VONG_VIET:
                CB._tam_nghi(lan); fb = ""; continue
            raise
        try:
            d = CB._extract_json(resp.text)
        except Exception as ex:
            fb = f"JSON lỗi ({ex})."; continue
        d = don(d)
        if phong:
            d["room"] = phong           # ép cứng: phòng do lịch luân phiên quyết, không do AI
        loi = cham(d, kenh, giay)
        cuoi = d
        if loi:
            fb = "; ".join(loi[:6])
            print(f"   ↻ vòng {lan}: {fb[:110]}")
            if lan >= VONG_VIET:
                break          # AI viết mãi không đạt thì đổi key không cứu được — dừng, trả bản cuối
            continue
        print(f"   ✅ đạt vòng {lan}: {d.get('title')!r} · "
              f"{sum(len(str((l or {}).get('say') or '').split()) for l in d.get('lines') or [])} từ thoại")
        return d
    if cuoi is not None:
        cuoi["_con_loi"] = cham(cuoi, kenh, giay)
        print(f"   ⚠️ {VONG_VIET} vòng chưa sạch — trả bản cuối kèm {len(cuoi['_con_loi'])} điểm sửa tay")
        return cuoi
    raise SystemExit("không sinh được tập nào")


# ── LƯU RA ĐĨA ──────────────────────────────────────────────────────────────────────────────
def _slug(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (t or "tap").lower()).strip("-")[:48] or "tap"


def _da_lam(kenh: str) -> list[dict]:
    """Các tập đã làm — tên VÀ phòng.

    Bản đầu chỉ trả tên tập, và cái giá hiện ra ngay ở loạt 15 tập đầu tiên: **13 tập diễn trong
    bếp**, bốn tập xoay quanh ngũ cốc/sữa/bột. AI thấy "kitchen" đứng đầu danh sách phòng thì cứ
    chọn nó, và không có gì bảo nó đừng. Một kênh 15 tập mà xem như một tập.

    Đây đúng dạng lỗi đã ghi ở luật 7bb: THƯỚC IM LẶNG Ở ĐÂU THÌ CHỖ ĐÓ KHÔNG ĐƯỢC BẢO VỆ. Trục
    "đa dạng bối cảnh" đã thêm cho bộ hài bên kia mà quên thêm ở đây."""
    tm = os.path.join(KHO, _slug(kenh))
    if not os.path.isdir(tm):
        return []
    r = []
    for d in sorted(os.listdir(tm)):
        j = os.path.join(tm, d, "tap.json")
        if os.path.isfile(j):
            try:
                x = json.load(io.open(j, encoding="utf-8"))
                r.append({"title": str(x.get("title") or d), "room": str(x.get("room") or "")})
            except Exception:
                pass
    return r


def phong_ke(kenh: str, da: list[dict]) -> str:
    """Phòng nên dùng cho tập tới: phòng LÂU NHẤT chưa quay.

    Không để AI tự chọn nữa. Tự chọn thì nó chọn bếp, mãi mãi — và ép luân phiên cũng đúng với
    cách một sitcom thật vận hành: mỗi tập một phòng, cả nhà được dùng hết."""
    ps = list(ho_so(kenh)["phong"])
    gan = [x.get("room") for x in da[-len(ps):]]
    for k in ps:
        if k not in gan:
            return k
    return ps[len(da) % len(ps)]


def luu(kenh: str, tap: dict, giay: float, so: int) -> str:
    """Ghi tập ra đĩa: prompt để dán, JSON để khâu sau đọc, thư mục clips để anh thả video về."""
    tm = os.path.join(KHO, _slug(kenh), f"{so:03d}-{_slug(tap.get('title'))}")
    os.makedirs(os.path.join(tm, "clips"), exist_ok=True)
    pr = prompt(kenh, tap, giay, so=so)
    tap = dict(tap, _kenh=kenh, _giay=giay, _so=so)
    io.open(os.path.join(tm, "tap.json"), "w", encoding="utf-8").write(
        json.dumps(tap, ensure_ascii=False, indent=2))
    io.open(os.path.join(tm, "PROMPT.txt"), "w", encoding="utf-8").write(pr)
    return tm


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Sinh prompt Kling có khoá nhân vật.")
    ap.add_argument("--kenh", default="HOUSE RULES")
    ap.add_argument("--y", default="", help="ý tưởng tập; bỏ trống thì AI tự nghĩ theo mạch kênh")
    ap.add_argument("--giay", type=float, default=8, help=f"độ dài clip {GIAY_CHUAN}")
    ap.add_argument("--so", type=int, default=0, help="số tập; 0 = tự đếm tiếp")
    ap.add_argument("--sl", type=int, default=1, help="sinh mấy tập một lượt")
    ap.add_argument("--phong", default="", help="ép một phòng cụ thể; bỏ trống = luân phiên")
    ap.add_argument("--kenh-liet-ke", action="store_true")
    a = ap.parse_args()

    if a.kenh_liet_ke:
        for k, v in KENH.items():
            print(f"  · {k:<14} {v['mo_ta']}")
        return 0

    hs = ho_so(a.kenh)
    da = _da_lam(a.kenh)
    so = a.so or (len(da) + 1)
    for i in range(a.sl):
        ph = a.phong or phong_ke(a.kenh, da)
        y = a.y or f"a fresh everyday moment in the {ph}"
        print(f"\n▶ {hs['ten']} tập {so:03d} · {a.giay:g}s · {ph}")
        tap = sinh_tap(a.kenh, y, a.giay, tranh=[x["title"] for x in da], phong=ph)
        tm = luu(a.kenh, tap, a.giay, so)
        n = len(io.open(os.path.join(tm, "PROMPT.txt"), encoding="utf-8").read())
        canh = "✓" if KY_TU_MIN <= n <= KY_TU_MAX else "⚠️ ngoài khoảng"
        print(f"   📄 {os.path.join(tm, 'PROMPT.txt')}  ({n} ký tự {canh})")
        da.append({"title": str(tap.get("title") or ""), "room": ph})
        so += 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
