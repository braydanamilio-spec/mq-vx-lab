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
# 1/9 — HIỆU CHỈNH LẠI, và vì sao con số cũ đã hết đúng.
# Bộ ba cũ (0.1875 · 0.5625 · 0.8125) lấy từ bộ 500 prompt chạy tốt, ở clip 8 GIÂY chia BỐN
# khối. Nhưng 8 giây nay đi nhánh BA khối (`nhip()` đổi số khối theo độ dài từ 30/8), nên `MOC`
# chỉ còn dùng cho clip ≥10 giây — một ngữ cảnh nó **chưa bao giờ được đo**. Hằng số vẫn ở đó,
# vẫn trông có căn cứ, và căn cứ ấy đã đi mất. Đúng họ lỗi "chép hằng sang hệ quy chiếu khác".
#
# Số mới đặt theo số đo công bố về short hài: phần DỰNG chiếm 60–70% clip, phần CHỐT cộng phản
# ứng chiếm 30–40%. Bộ cũ cho chốt đúng 18,75% — tức ở clip 15 giây, cú chốt và cả cái mặt phản
# ứng chỉ được 2,8 giây, trong khi tài liệu đo được nói cú lật nên nằm trong ba giây cuối và
# cần chỗ để người xem kịp cười.
#     hook 16% · setup 28% · escalate 24% · payoff 32%
MOC = (0.16, 0.44, 0.68)

# Kling web chỉ cho chọn vài mốc thời lượng cố định tuỳ phiên bản model. Đây là các mốc hay gặp;
# anh nhập số nào thì hệ dựng nhịp theo số ấy, vì chỉ anh mới biết giao diện mình đang có gì.
# 1/9 — ANH TRẢ TIỀN CHO KLING THEO LƯỢT, nên độ dài không phải chuyện thẩm mỹ mà là chuyện chi
# phí. Vùng ưu tiên là 5–8 giây: đủ cho một trò đùa trọn vẹn ở hai khuôn kể đầu, và rẻ nhất.
#
# Đo được vì sao 5–8 vẫn đủ viral, không phải cắt cụt:
#   · 5–6s  khuôn ONE JOKE, ONE PUNCH — một hình sai trái, một cú lật. Toàn bộ clip nằm gọn
#           trong "3 giây đầu" mà số đo giữ chân gọi là khoảnh khắc quyết định lướt hay ở lại,
#           nên tỉ lệ xem hết gần như bằng 100% nếu khung đầu giữ được mắt.
#   · 7–8s  khuôn SETUP AND TURN — có chỗ cho người xem ĐOÁN trước khi bị lật. Tỉ lệ dựng/chốt
#           của hai mốc này (67% / 33%) khớp đúng số đo công bố cho short hài.
# Từ 10 giây trở lên vẫn chạy được, nhưng mỗi giây thêm là tiền thêm mà số đo không hứa thêm
# gì: vùng tối ưu của hài short đo được là 18–28 giây — quá xa 15, nên 10–15 nằm ở khoảng
# giữa "không rẻ nữa" và "chưa đủ dài để hơn", tức khoảng tệ nhất.
GIAY_UU_TIEN = (5, 6, 7, 8)
GIAY_CHUAN = (5, 6, 7, 8, 9, 10, 12, 15)

# ── KHUÔN KỂ THEO THỜI LƯỢNG ────────────────────────────────────────────────────────────────
# 1/9 — Đo được: lệnh hệ thống cho clip 5 giây và clip 15 giây **giống nhau 99,9%**, chỉ khác
# mỗi con số. Nên AI viết đúng MỘT kiểu chuyện bốn nhịp cho mọi thời lượng, rồi engine gộp lại
# (5 giây) hoặc trải ra (15 giây). Cả hai đều hỏng theo cách riêng:
#   · gộp   -> ba nhịp nhồi vào một khối 3,3 giây: xem không kịp hiểu, cú lật mất chỗ gài
#   · trải  -> một chuyện 8 giây kéo qua 15 giây: khúc giữa không có việc gì xảy ra, người xem lướt
#
# Phim ngắn thật không co giãn một kịch bản — nó ĐỔI LOẠI CHUYỆN. Năm giây kể được một trò đùa
# một cú đấm; mười lăm giây BẮT BUỘC phải có tiếng cười thứ hai ở khúc giữa, không thì thừa
# tám giây. Ba khuôn dưới đây khớp đúng ba dạng nhịp mà `nhip()` dựng.
KHUON_KE = (
    (6.5, "ONE JOKE, ONE PUNCH", (
        "This length holds exactly ONE idea. There is no room to establish anything, so the "
        "first frame must already BE the setup — the viewer understands the situation from the "
        "image alone, before anyone speaks.",
        "Do NOT write a small version of a longer story. Write a different kind of story: a "
        "single wrong image that turns once.",
        "The reversal must be readable in under a second, so it has to be a change of SHAPE or "
        "POSITION, not a piece of information. Something falls, opens, is revealed to be facing "
        "the other way, or someone simply walks off. A reversal the viewer has to think about "
        "does not exist at this length.",
        "'escalate' here is not a story beat — it is one physical half-second between the image "
        "and the turn (a doorknob turning, a stack leaning further, someone drawing breath). "
        "Keep it to one short clause.",
        "Dialogue is ONE exchange: two lines, and the second is shorter than the first. Nobody "
        "explains, nobody names the problem. Often the funniest second line is one word.",
    )),
    (9.5, "SETUP AND TURN", (
        "This length holds a situation and its reversal — but not a second laugh. Do not try to "
        "escalate twice; a second attempt at this length steals the time the punchline needs.",
        "Use the middle to make the viewer PREDICT something specific. The turn is only funny "
        "if the prediction was clear, so the middle must commit to one obvious outcome.",
        "'escalate' folds into the middle: one small physical gag that makes the prediction "
        "stronger, not a new development.",
        "Dialogue is two or three lines: a want, a refusal or a correction, and then the image "
        "does the rest. The last line is the shortest and lands before the reversal is visible.",
    )),
    (99.0, "ESCALATION AND TWO LAUGHS", (
        "This length REQUIRES a second laugh in the middle, or the last third drags and the "
        "viewer leaves before the punchline. A ten-second short with one joke is an eight-second "
        "short with two seconds of nothing.",
        "The engine of the middle is EFFORT: the wrong solution gets bigger, more elaborate, "
        "more committed — never abandoned. The audience laughs once at how far the character "
        "will go, and again at what it turns out to be.",
        "'escalate' must genuinely RAISE something measurable, and must SAY SO in words. Write "
        "it with one of these: again, another, further, more, bigger, deeper, harder, higher, "
        "faster, a second, one more, the whole, even the, instead of, not enough. If 'escalate' "
        "could be deleted without changing the payoff, it is description, not escalation.",
        "The reversal must pay off the ESCALATION specifically, not just the opening image. The "
        "bigger the effort, the smaller and more ordinary the true answer should be.",
        "Dialogue is three or four lines spread across the beats — do not stack them all in the "
        "middle. Give the payoff beat its own short line, or no line at all.",
    )),
)


def khuon_ke(giay: float) -> tuple[str, tuple]:
    """Loại chuyện mà thời lượng này kể được. Khớp đúng ba dạng nhịp của `nhip()`."""
    for tran, ten, luat in KHUON_KE:
        if float(giay) <= tran:
            return ten, luat
    return KHUON_KE[-1][1], KHUON_KE[-1][2]


# ── GIỚI HẠN THẬT CỦA KLING, DÙNG ĐỂ CHẤM KỊCH BẢN ──────────────────────────────────────────
# Không phải để trang trí. Mỗi con số dưới đây là một lần render hỏng đã trả giá.
TU_MOI_GIAY = 2.7          # người Mỹ thoại tự nhiên ~2,7 từ/giây. Quá số này là nói như đọc rap.
TU_MOI_LUOT = 9            # một lượt dài hơn 9 từ thì Kling khớp miệng bắt đầu trượt.
LUOT_TOI_DA = 4            # quá 4 lượt trong 8 giây là cắt cảnh liên tục, mặt ai cũng kịp méo.
VAI_TOI_DA = 4             # quá 4 người trong khung thì Kling chia ngân sách khuôn mặt -> nát cả 4.
# Trần ký tự. Kling CẮT ĐUÔI prompt quá dài, mà đuôi là RENDER REQUIREMENTS — mất khối đó là mất
# hàng rào chống "thêm tay, thêm chân, chữ loằng ngoằng". Nên không bao giờ để tràn rồi phó mặc:
# `prompt()` tự CO cho vừa, và co theo thứ tự GIÁ TRỊ chứ không cắt bừa phần cuối.
#
# 1/9 — HẠ 3000 -> 2500. Tài liệu API Kling ghi trần `prompt` là 2.500 KÝ TỰ. Bản cũ đặt trần
# 3000 nên **30/30 tệp đã xuất đều vượt** (đo được 2.731–3.024) — tức mọi tập đang chạy đều bị
# Kling cắt mất đuôi, mà đuôi đúng là khối DO NOT. Hình hỏng, và không có gì báo lỗi.
#
# Con số "2.500 TỪ" từng ghi ở đây là đọc nhầm đơn vị: 2.500 từ ≈ 16.800 ký tự, gấp gần bảy lần
# trần thật. Bản `day=True` sinh ra đúng 16.834 ký tự và không bao giờ tới được Kling nguyên vẹn.
KY_TU_MIN, KY_TU_MAX = 2000, 2500
_CAM_TU_LOAT: list = []    # từ đã mòn trong loạt đang chạy; `main` nạp, `cham` đọc
# Chữ thuộc về khuôn prompt hoặc về căn nhà thì lặp là ĐÚNG — cấm chúng là cấm nhầm.
_BO_QUA = {"static", "shot", "level", "wide", "kitchen", "living", "backyard", "garage", "porch",
           "front", "table", "floor", "wooden", "camera", "counter", "couch", "coffee", "house",
           "while", "which", "their", "there", "about", "where", "holding", "standing"}
# Đây vẫn gần GẤP ĐÔI trung vị hiện tại (379 ký tự) — tức nới chỗ cho hook viết đủ ý, không
# phải siết. Chia theo giá trị: hook và setup là chỗ người xem quyết định ở lại hay lướt.
# Trần TỪNG KHỐI — nay chỉ là chốt chặn chống "một đoạn văn thay vì một câu tả một hình".
# Ngân sách thật không nằm ở đây nữa: `cham()` ghép prompt của chính tập ấy rồi đo (xem ghi
# chú trong `cham`). Trần 240 = ~40 từ, gấp rưỡi trần hook 30 từ, đủ rộng để không bắt oan.
VAN_KE_CHIA = {"hook": 240, "setup": 240, "escalate": 200, "payoff": 200}

DIEM_SAN = 90              # sàn thang 100 điểm (`cham100.py`). Dưới sàn thì bắt AI viết lại chứ
                           # không xuất. Đặt 90 vì đo được: 30 tập đã chạy nằm ở 67–87 — tức
                           # "sạch thước cũ" và "hay" là hai chuyện khác nhau, cách nhau đúng
                           # khoảng ấy.
VONG_VIET = 8              # số lần cho AI viết lại một tập. Dây chuyền để 3 — hợp cho việc trích
                           # dữ liệu, quá ít cho việc sáng tác: kịch bản hỏng nhịp thường tới lần
                           # thứ tư, thứ năm mới ra được bản dùng được.

CAU_GIU_HINH = "Hold this exact image to the final frame."
CAU_CHOT_RAO = "The last frame IS the punchline — no settling shot, no fade, exactly {g} seconds."

# Một LƯỢNG CHÍNH XÁC. `one` không tính, `half`/`twice` cũng không: chúng là từ đệm ("one more
# time", "half the room") chứ không phải thứ người xem đếm được — bản đầu nhận chúng nên cổng
# báo sạch cho đúng loại kịch bản mơ hồ mà nó sinh ra để bắt.
# Giữ ở đây làm MỘT NGUỒN: `cham100` và bản xuất web đều đọc lại, không chép.
# Những chữ mà hook phải dùng để NÓI RA cái sai — thước tìm đúng chúng, nên lệnh dặn phải
# liệt kê chúng ra (bài học: cổng đo một TỪ, lệnh dặn nói một Ý).
SAI_TRAI_TA = (r"\b(empty|open|stacked|leaning|spill\w*|smok\w*|stuck|missing|upside|backwards|"
               r"soak\w*|frozen|melting|tilt\w*|scatter\w*|cover\w*|wrong|too (high|many|small))\b")

SO_CHINH_XAC = (r"\b\d{1,4}\b|\$\d|\b(Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day\b|"
                r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
                r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|"
                r"fifty|sixty|seventy|eighty|ninety|hundred|thousand|dozen)\b")

GHIM_MAY = ("static", "eye-level", "eye level", "low angle", "high angle", "wide shot",
            "medium shot", "close shot", "over-the-shoulder", "locked-off", "top-down")

# Đồ lớn nói được bằng nhiều tên. Bản trước so chuỗi thẳng nên phòng "stairwell" (tả là "bare
# concrete steps") vẫn bị chặn khi kịch bản viết "stairs", và phòng "motel room" (tả là "a boxy
# TV") bị chặn khi viết "television". Cổng bắt oan còn tệ hơn cổng không bắt: nó ép AI viết lại
# một kịch bản vốn đúng, và ép tới khi hết vòng thì trả bản tệ hơn.
DONG_NGHIA_DO = {
    "television": ("tv", "screen"), "tv screen": ("tv",),
    "stairs": ("stairwell", "step"), "staircase": ("stairwell", "step"),
    "hallway": ("hall",), "bookcase": ("bookshelf",), "bookshelf": ("bookcase", "shelf"),
    "basement": ("cellar",), "washing machine": ("washer",), "dryer": ("dryer",),
}

DO_TO = ("island", "dishwasher", "staircase", "stairs", "fireplace", "balcony", "pool",
         "chandelier", "bookshelf", "bookcase", "television", "tv screen", "piano", "treadmill",
         "washing machine", "dryer", "pantry", "bar stool", "kitchen bar", "breakfast bar",
         "second floor", "hallway", "basement", "attic", "elevator", "escalator")

# Loạt 15 tập chia đều phòng và đều người lật, nhưng **5/15 hook mở bằng "teeters"** và 4 tập
# xoay quanh một chồng đồ chực đổ. AI tìm ra một khuôn hình ảnh hiệu quả rồi dùng lại — tầng thứ
# BA của cùng một bệnh, sau phòng và người lật.
# Cách chữa vẫn thế (luật 7bi): không dặn, mà cấp theo lịch. Tám loại tai nạn mở màn, luân phiên
# lệch pha với hai trục kia — 5 phòng × 5 người × 8 kiểu, đủ cho hai trăm tập không trùng bộ ba.
KIEU_MO = (
    "something is stacked far too high and is about to fall",
    "a liquid is spreading across a surface where it should not be",
    "smoke or steam is coming from something that should not be smoking",
    "an object is somewhere it physically cannot have got to on its own",
    "something that was there a moment ago is now missing",
    "an object is stuck fast and someone is losing a fight with it",
    "a sound keeps happening and nobody can find the source",
    "one character is dressed or equipped completely wrong for the room",
    # 1/9 — tám kiểu nữa. Mỗi kiểu là một CÁCH KHUNG ĐẦU SAI, không phải một chủ đề: đó là lý
    # do thêm chúng nhân thật sự đa dạng lên chứ không chỉ đổi danh từ.
    "far too many of one ordinary thing are in one place",
    "something has been taken apart and not put back together",
    "an object is wrapped, taped or tied in a way nobody would ever do",
    "two things that belong apart have been swapped with each other",
    "somebody has clearly been waiting in one spot far too long",
    "a thing that should be closed is open, and everything inside is now outside",
    "one small area is spotless and everything around it is wrecked",
    "an object is being used confidently as a tool it is not",
)

# ── ÁP LỰC — thứ biến một sự cố thành một CẢNH ─────────────────────────────────────────────
# 1/9 — Trục này thiếu hẳn, và nó là trục đắt nhất. Cùng một đồ vật hỏng trong cùng một căn
# phòng cho ra hai tập KHÁC HẲN nếu áp lực khác: "cái máy pha hỏng" lúc rảnh là một sự cố, lúc
# khách sắp tới là một cảnh. Luật hài Mỹ số 3 nói cần hai người muốn hai thứ đối nhau — áp lực
# chính là thứ sinh ra cái muốn, nên thiếu nó thì AI phải tự bịa và nó bịa ra cùng một thứ.
AP_LUC = (
    "somebody is arriving in a minute and the room cannot be seen like this",
    "it is already late and one more delay is the one that matters",
    "a specific amount of money has just been said out loud",
    "a rule was made about exactly this, yesterday",
    "there is only one left and more than one person wants it",
    "it was borrowed and it was not supposed to leave the house",
    "somebody is watching who should not see this",
    "the same thing went wrong last time and everybody remembers",
    "one person promised this would be handled and said so publicly",
    "it belongs to somebody who is not in the room",
    "it has to be working again before anyone notices it stopped",
    "somebody is trying to leave and cannot until this is settled",
)

# ── THOẠI KIỂU MỸ — chặn những chỗ AI hay trượt sang giọng sách vở ─────────────────────────
# Người Mỹ nói tắt, nói thiếu, và trả lời lệch câu hỏi. AI viết tiếng Anh "đúng ngữ pháp" nên
# hay ra giọng phụ đề phim tài liệu. Ba nhóm dưới đây bắt được gần hết, và bắt CHÍNH XÁC —
# không có từ nào ở đây mà một câu thoại gia đình Mỹ thật lại cần dùng.
KHONG_MY = [
    # dạng đầy đủ ở chỗ người Mỹ luôn nói tắt
    (r"\b(I am|it is|that is|you are|we are|they are|do not|does not|did not|cannot|"
     r"will not|is not|are not|have not|has not|I will|I have|I would)\b",
     "viết dạng đầy đủ — người Mỹ nói tắt: I'm · it's · that's · don't · can't · won't"),
    # giọng sân khấu / giọng dịch
    (r"\b(indeed|perhaps|quite so|very well|shall|mustn't we|oh dear|my goodness|"
     r"how wonderful|splendid|marvellous|marvelous|dreadful|terribly)\b",
     "giọng sân khấu, không phải giọng người Mỹ nói trong bếp"),
    # câu cảm thán rỗng — chiếm chỗ trong ngân sách từ mà không đưa thông tin nào
    (r"^(oh no|wow|whoa|uh oh|oh my|no way|amazing|incredible)\b",
     "câu cảm thán rỗng — ở clip ngắn mỗi từ phải đưa một thông tin hoặc một cú đùa"),
]

# ── BỐN CỔNG NGHỀ, rút từ việc ĐỌC 28 kịch bản AI đã sinh ─────────────────────────────────
# Thang 100 điểm đo được CẤU TRÚC (có cú lật không · hook đủ dài không · thoại có vừa nhịp
# không). Nó không đo được BUỒN CƯỜI. Đọc tay 28 tập thì thấy bốn lỗi nghề mà mọi cổng đều cho
# qua — và cả bốn đều đo được, chỉ là chưa ai viết ra.

# 1 · CHỮ TRONG KHUNG. Đo được: 6/28 tập bắt Kling vẽ chữ đọc được, chỗ nó hỏng nặng nhất.
#     `CAM_KY` có mục "sign reads" nhưng so bằng CHUỖI CON, nên "a sign on the shed door that
#     reads…" · "one neon note reads…" · "spelling out Dr Shah" đều lọt. Một danh sách chuỗi con
#     không bắt được ngôn ngữ — phải là biểu thức.
CHU_TRONG_KHUNG = (
    r"\b(reads?|reading|spell(s|ed|ing)?( out)?|writ(ten|ing)|says on|labell?ed|handwritten|"
    r"scrawl(ed)?|printed with|marked ['\"“]|in (blue|black|red) marker)\b"
    r"|['\"“][^'\"”]{2,40}['\"”]\s*(on|across|taped|stuck|hangs|written)"
)

# 2 · CHỮ KHÔNG VẼ ĐƯỢC. "evidence he made the mess" · "confirming they're his" — đó là người
#     viết giải thích cho người đọc, không phải thứ hoạ sĩ phân cảnh vẽ được. Kling đọc xong sẽ
#     tự bịa ra một hình cho khái niệm ấy, và mỗi tập bịa một kiểu.
KHONG_VE_DUOC = (
    r"\b(evidence|proving|confirming|indicating|suggesting|implying|symboliz\w+|representing|"
    r"showing that|revealing that|meaning|as if to say|clearly (his|hers|theirs)|obviously)\b"
)

# 3 · THOẠI TỰ THUẬT. "Kyle, your note made the fridge a sticky wall" — không ai nói thế; đó là
#     lời dẫn đội lốt lời thoại. Ba dấu hiệu đo được: gọi tên người đối diện, nói ra chính hành
#     động mình đang làm, và câu dài kiểu văn viết.
THOAI_TU_THUAT = (
    r"^\s*[A-Z][a-z]+,\s"                       # "Kyle, ..." — gọi tên giữa hai người trong phòng
    r"|\bI'?ll (tape|put|stick|write|make|hang|place) \b"   # tự tường thuật hành động sắp làm
    r"|\byour \w+ (made|turned|caused) \b"
)

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


# ── SÀN TAY NGHỀ — phần CHUNG của mười kênh, và chỉ chung đúng phần thật sự chung ───────────
# Đây là những quyết định một xưởng hoạt hình Mỹ chốt trước khi vẽ khung đầu tiên, viết dưới
# dạng Kling đọc được. Nó là SÀN, không phải phong cách: phong cách nằm ở `style` của từng kênh
# và mười cái ấy khác hẳn nhau. Để riêng thành hằng số vì hai lý do — sửa tay nghề thì sửa một
# chỗ, và khi ngân sách prompt căng thì `_bat_buoc` biết chính xác chuỗi nào cần cắt bỏ trước.
# Yêu cầu ÂM THANH mà mọi kênh phải có — tay nghề, không phải bản sắc. Tách ra để cổng đa dạng
# không tính chúng là "hai kênh giống nhau": khớp miệng chính xác thì kênh nào cũng cần.
SAN_TIENG = "Precise lip sync."

# Câu KHOÁ BỐI CẢNH mà mọi kênh phải có, vì lý do tương tự.
SAN_NHA = ("Keep the exact same layout, colors, furniture shapes and camera geography in every "
           "episode. Never redesign or recolor it.")

SAN_NGHE = ("hand-drawn 2D animation on twos, held key poses with snappy transitions between them, tapered ink line that thickens on the shadow side, appealing readable silhouettes, generous squash and stretch on the face only")

# ── HỒ SƠ KÊNH ──────────────────────────────────────────────────────────────────────────────
# Mỗi kênh là một cuốn "sổ tay phim": dàn diễn viên, bối cảnh, nét vẽ, giọng, và loại chuyện kênh
# ấy kể. Thêm kênh mới = thêm một mục vào đây, không phải sửa mã.
KENH: dict[str, dict] = {
    "BREAK ROOM": {
        "ten": "BREAK ROOM",
        "mo_ta": "Hài công sở Mỹ — phòng nghỉ nhân viên, nơi mọi mâu thuẫn nhỏ của văn phòng nổ ra quanh cái tủ lạnh chung.",
        "ty_le": "9:16",
        "nhan_vat": {
            "Dave": "Dave: 38-year-old man, thinning blond hair, wrinkled blue dress shirt, loose tie, khaki pants, brown shoes; confidently wrong, takes credit, never reads emails.",
            "Priya": "Priya: 34-year-old woman, black hair in a low bun, dark green blazer, grey trousers, flat black shoes; dry, unimpressed, keeps receipts of everything.",
            "Kyle": "Kyle: 24-year-old man, short curly brown hair, oversized grey hoodie, jeans, white sneakers; fast, literal, says the quiet part out loud.",
            "Marge": "Marge: 58-year-old woman, short silver hair, red cardigan, floral blouse, navy skirt, beige shoes; deadpan veteran, has worked here longer than the building.",
        },
        "nha": (
            "The break room of a mid-size American office on the fourth floor: beige walls, one humming vending machine, a shared refrigerator covered in passive-aggressive sticky notes. Keep the exact same room layout, wall colors, furniture shapes and camera geography in every episode. Never redesign or recolor the office."
        ),
        "phong": {
            "break room": "Break Room: beige walls, a shared white refrigerator on the right covered in sticky notes, a round table with four blue chairs, a tall vending machine.",
            "copy corner": "Copy Corner: grey carpet, one large copier against the wall, a paper recycling bin, a small window with closed blinds.",
            "cubicles": "Cubicles: low grey partitions, three desks with old monitors, one dying potted plant on the corner desk.",
            "elevator lobby": "Elevator Lobby: cream walls, two brushed steel elevator doors, a bench nobody sits on, a wall clock.",
            "supply closet": (
                "Supply Closet: narrow room, metal shelves of paper reams and boxes, one flickering "
                "strip light, a mop in the corner."
            ),
            "stairwell": (
                "Stairwell: bare concrete steps, painted steel handrail, a propped fire door, one "
                "caged bulb overhead."
            ),
            "conference room": (
                "Conference Room: long laminate table, eight mismatched chairs, a whiteboard wiped "
                "grey, a speakerphone in the middle."
            ),
        },
        "style": (
            "Flat corporate fluorescent look: everything is built from rectangles — cubicle "
            "walls, the vending machine, the shoulders of people who have stopped fighting it. "
            "Thin even line of constant weight, no texture. Palette is beige, grey and one "
            "aggressive corporate teal accent that appears exactly once per shot. Light is "
            "even, shadowless and slightly green, the way overhead office light actually is.. "
            "hand-drawn 2D animation on twos, held key poses with snappy transitions between "
            "them, tapered ink line that thickens on the shadow side, appealing readable "
            "silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Flat American office voices for {vai} — nobody raises their voice, everything is "
            "said pleasantly. Hum of a vending machine and a distant printer under everything. "
            "Precise lip sync. The laugh is in what is not said, so leave the pauses long"
        ),
        "dien": "Dave is confident even when obviously wrong; Priya is dry and keeps evidence; Kyle says out loud what everyone is thinking; Marge has seen this exact thing happen twice before",
        "hai": (
            "The joke is always what nobody says out loud. These are people being extremely "
            "polite to someone they are furious with. Status is job title versus actual power — "
            "the person who controls the supply closet outranks the person who runs the "
            "meeting. Escalate through procedure: a note becomes a policy becomes a laminated "
            "sign. Never let anyone actually argue; the moment someone says the real thing, the "
            "joke is over."
        ),

        "dao_cu": (
            "the shared microwave",
            "a mug with someone's name on it",
            "the one good chair",
            "a stapler",
            "the middle fridge shelf",
            "the thermostat",
            "a group birthday card",
            "a laminated sign",
            "the last coffee filter",
            "a phone charger",
            "a reserved parking placard",
            "a dying office plant",
            "the one whiteboard marker that still works",
            "a paper jam",
            "a toner cartridge",
            "a lunch bag",
            "a sticky note",
            "a spare key on a lanyard",
            "a chair with one broken armrest",
            "the water cooler jug",
            "a conference speakerphone",
            "a box of pens",
            "a visitor badge",
            "a stuck vending machine coil",
        ),

        "mach": ("Ordinary American office friction blown one size too big: stolen lunches, thermostat wars, reply-all disasters, birthday cake politics, the one broken chair everyone avoids. One tiny workplace dispute escalates and lands on a reversal where the person with the least authority turns out to be right."),
    },

    "DINER SHIFT": {
        "ten": "DINER SHIFT",
        "mo_ta": "Hài quán ăn đêm Mỹ — bồi bàn kỳ cựu, bếp trưởng nóng tính và những vị khách lúc hai giờ sáng.",
        "ty_le": "9:16",
        "nhan_vat": {
            "Rosa": "Rosa: 46-year-old woman, dark hair in a ponytail, pale blue waitress dress, white apron, worn white shoes; deadpan veteran, unshockable, carries four plates at once.",
            "Chef Nick": "Chef Nick: 51-year-old man, heavy build, white t-shirt, stained apron, backwards cap, black clogs; confidently wrong, defends every recipe he ever invented.",
            "Toby": "Toby: 19-year-old man, messy red hair, oversized green uniform shirt, black jeans, sneakers; anxious over-preparer, new, writes everything down.",
            "Walt": "Walt: 67-year-old man, grey stubble, brown flat cap, beige jacket, dark trousers; sits in the same booth every night, dry and unimpressed.",
        },
        "nha": (
            "Ruby's Diner, a small American roadside diner open all night: red vinyl booths, a long counter with chrome stools, a pass-through window to the kitchen. Keep the exact same room layout, colors, furniture shapes and camera geography in every episode. Never redesign or recolor the diner."
        ),
        "phong": {
            "counter": "Counter: long cream counter with six chrome stools, a coffee machine, a glass pie case at the end.",
            "booth": "Booth: red vinyl booth against a window, a formica table, salt and pepper shakers, a napkin holder.",
            "kitchen pass": "Kitchen Pass: steel pass-through window, heat lamps above, order tickets clipped in a row.",
            "parking lot": "Parking Lot: cracked asphalt at night, one tall lamp post, the diner window glowing behind.",
            "walk-in": (
                "Walk-In: steel shelving stacked with crates, a heavy insulated door, cold blue "
                "light, breath visible."
            ),
            "back alley": (
                "Back Alley: brick wall, a dented dumpster, milk crates stacked as a seat, the "
                "diner's back door propped open."
            ),
            "register": (
                "Register: worn front counter with a till, a jar of mints, a rack of local flyers, a "
                "stool nobody uses."
            ),
        },
        "style": (
            "Warm tungsten interior against deep blue night outside the window — the two "
            "temperatures never mix, they meet at a hard edge. Rounded chrome and vinyl shapes, "
            "thick brushy ink line that varies in weight. Palette is amber, cherry red vinyl "
            "and cold window blue. A faint film grain over everything. Light pools on the "
            "counter and falls off fast.. hand-drawn 2D animation on twos, held key poses with "
            "snappy transitions between them, tapered ink line that thickens on the shadow "
            "side, appealing readable silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Tired, unhurried American voices for {vai} at two in the morning. Coffee machine "
            "hiss, plate clatter from off-screen, the door bell. Precise lip sync. Everyone "
            "speaks at the pace of the eleventh hour of a shift, never faster"
        ),
        "dien": "Rosa is unshockable and deadpan; Chef Nick defends every bad idea he has ever had; Toby is new and over-prepares everything; Walt comments once and is always right",
        "hai": (
            "Exhaustion comedy. The staff have seen everything; the customer has seen nothing. "
            "Status is seniority — how many years, not what rank. Play every absurd request "
            "completely straight and answer it with logistics, never with outrage. Escalate "
            "through the ticket: a simple order becomes an impossible one, one substitution at "
            "a time. The reversal is usually that the strange request was reasonable and "
            "everyone else was wrong."
        ),

        "dao_cu": (
            "a coffee pot that has been on since noon",
            "a ticket spike",
            "the last slice of pie",
            "a bottle of hot sauce",
            "a wobbly table leg",
            "a bus tub",
            "the tip jar",
            "a broken creamer lid",
            "a laminated menu",
            "the milkshake machine",
            "a stack of clean plates",
            "a ketchup bottle",
            "a receipt roll",
            "the bell at the pass",
            "a sugar caddy",
            "a paper hat",
            "the specials board",
            "a napkin dispenser",
            "a to-go box",
            "the mop bucket",
            "a coat left in a booth",
            "an order pad",
            "a butter dish",
            "the heat lamp",
        ),

        "mach": ("Late-night American diner friction blown one size too big: an order that makes no sense, a coffee pot that has been on since noon, a regular who wants something not on the menu, a health inspection rumour. One small kitchen dispute escalates and lands on a reversal where the quietest person at the counter knew the answer first."),
    },

    "GYM FLOOR": {
        "ten": "GYM FLOOR",
        "mo_ta": "Hài phòng gym Mỹ — huấn luyện viên tự tin, người mới lóng ngóng và ông chú tập ở đây từ thời máy còn mới.",
        "ty_le": "9:16",
        "nhan_vat": {
            "Brad": "Brad: 31-year-old man, muscular, short blond hair, tight grey tank top, black shorts, white trainers; confidently wrong, gives advice nobody asked for.",
            "Nia": "Nia: 28-year-old woman, dark curly hair in a headband, purple sports top, black leggings, teal trainers; dry, unimpressed, lifts more than Brad.",
            "Gary": "Gary: 44-year-old man, average build, oversized faded blue t-shirt, baggy grey shorts, old white sneakers; anxious over-preparer, reads the machine instructions twice.",
            "Coach Ed": "Coach Ed: 63-year-old man, grey buzz cut, whistle, red polo shirt, navy track pants, black shoes; deadpan veteran, has run this gym for thirty years.",
        },
        "nha": (
            "Iron Street Gym, a small American neighborhood gym: grey rubber flooring, mirrored wall, a row of treadmills, a free-weight corner. Keep the exact same room layout, colors, equipment positions and camera geography in every episode. Never redesign or recolor the gym."
        ),
        "phong": {
            "weight floor": "Weight Floor: grey rubber floor, a mirrored wall on the left, a rack of dumbbells, one flat bench.",
            "treadmill row": "Treadmill Row: three treadmills facing a wall-mounted television that is always muted.",
            "locker room": "Locker Room: narrow blue lockers, a wooden bench down the middle, one flickering light.",
            "front desk": "Front Desk: white counter with a card scanner, a jar of protein bars, a wall of membership photos.",
            "stretch mats": (
                "Stretch Mats: blue foam mats in a corner, a rack of foam rollers, a wall mirror, one "
                "lost resistance band."
            ),
            "sauna": (
                "Sauna: cedar benches in two tiers, a bucket and ladle, a small thermometer, warm "
                "amber light."
            ),
            "juice bar": (
                "Juice Bar: short counter with a blender, a shelf of tubs, a cold case of bottles, "
                "two tall stools."
            ),
        },
        "style": (
            "High-key bright and hard-edged: rubber mat charcoal, chrome, and two loud primary "
            "accents on equipment. Elastic shape language — bodies compress and rebound, "
            "weights have weight. Bold line that thickens hard under load. Flat top light that "
            "puts a crisp shadow directly under everyone. Sweat is drawn as three specific "
            "drops, never a sheen.. hand-drawn 2D animation on twos, held key poses with snappy "
            "transitions between them, tapered ink line that thickens on the shadow side, "
            "appealing readable silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Confident, slightly breathless American voices for {vai}. Plate clank, treadmill "
            "belt, somebody else's headphones leaking. Precise lip sync. Effort sounds are "
            "small and real, never cartoon strain"
        ),
        "dien": "Brad gives confident wrong advice; Nia is dry and stronger than everyone; Gary reads every instruction and still gets it wrong; Coach Ed says one sentence and ends the argument",
        "hai": (
            "Ego against physics, and physics always wins on camera. Status is what you can "
            "actually do versus what you are explaining. The loudest advice comes from the "
            "weakest person in frame, and nobody points it out. Escalate through numbers — the "
            "weight, the reps, the count — because numbers make the failure exact. The reversal "
            "belongs to whoever has said the least and lifted the most."
        ),

        "dao_cu": (
            "a towel left on a bench",
            "the last forty-five pound plate",
            "a chalk bucket",
            "a foam roller",
            "the treadmill emergency clip",
            "a shaker bottle",
            "a resistance band",
            "the squat rack pins",
            "someone's phone on the bench",
            "a jump rope",
            "the wall clock",
            "a spray bottle and rag",
            "a locker padlock",
            "the water fountain",
            "a gym bag in the walkway",
            "a weight belt",
            "the sign-in clipboard",
            "an unracked barbell",
            "a pair of headphones",
            "the fan remote",
            "a protein tub",
            "the pull-up bar chalk",
            "a mat nobody wiped",
            "a stack of step platforms",
        ),

        "mach": ("American gym friction blown one size too big: the machine somebody is sitting on scrolling their phone, the mystery towel, the guy who counts other people's reps, the mirror selfie. One small gym dispute escalates and lands on a reversal where the least athletic person is the one who was right."),
    },

    "DORM 204": {
        "ten": "DORM 204",
        "mo_ta": "Hài ký túc xá đại học Mỹ — bốn bạn cùng phòng, một cái tủ lạnh mini và không ai chịu rửa bát.",
        "ty_le": "9:16",
        "nhan_vat": {
            "Jess": "Jess: 20-year-old woman, shoulder-length brown hair, oversized university sweatshirt, joggers, fluffy slippers; dry, unimpressed, runs on four hours of sleep.",
            "Marcus": "Marcus: 19-year-old man, short black hair, red basketball jersey, grey shorts, high-top sneakers; confidently wrong, has a theory about everything.",
            "Ollie": "Ollie: 18-year-old man, floppy brown hair, striped pyjama top, jeans, one sock; fast and literal, permanently confused.",
            "Sam": "Sam: 21-year-old woman, blonde hair in a messy bun, glasses, yellow raincoat worn indoors, black boots; anxious over-preparer, colour-codes the chore chart.",
        },
        "nha": (
            "Room 204 of an American college dorm: cinderblock walls painted off-white, two bunk beds, a shared mini fridge, one window with a broken blind. Keep the exact same room layout, colors, furniture shapes and camera geography in every episode. Never redesign or recolor the dorm."
        ),
        "phong": {
            "dorm room": "Dorm Room: off-white cinderblock walls, two wooden bunk beds, a mini fridge under the window, a cluttered desk.",
            "hallway": "Hallway: narrow corridor, scuffed grey floor, a row of identical brown doors, a bulletin board.",
            "shared kitchen": "Shared Kitchen: small communal kitchen, one microwave, a sink with a permanent stack of dishes.",
            "laundry room": "Laundry Room: two washers, two dryers, a folding counter, a basket somebody left three days ago.",
            "study lounge": (
                "Study Lounge: three study carrels, a sagging couch, a vending machine, a window with "
                "the blind stuck half open."
            ),
            "bike room": (
                "Bike Room: concrete floor, a rack of chained bikes, a pile of flattened boxes, one "
                "bare bulb."
            ),
            "rooftop": (
                "Rooftop: flat gravel roof, a low parapet wall, two folding chairs, the campus "
                "skyline behind."
            ),
        },
        "style": (
            "Cluttered warm chaos lit by string lights and one laptop screen. Sketchy energetic "
            "line with visible construction strokes left in. Palette is poster-print primaries "
            "over cinderblock grey, everything slightly too saturated. Piles read as "
            "silhouettes, not as detail. Two light sources fighting: warm string lights and "
            "cold blue screen glow.. hand-drawn 2D animation on twos, held key poses with "
            "snappy transitions between them, tapered ink line that thickens on the shadow "
            "side, appealing readable silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Young American voices for {vai}, overlapping in energy but never in timing. "
            "Distant hallway noise, a microwave, someone else's music through a wall. Precise "
            "lip sync. Everything is said at the volume of people who have not slept"
        ),
        "dien": "Jess is dry and exhausted; Marcus has a confident theory about everything; Ollie takes everything literally; Sam has already made a chart about it",
        "hai": (
            "Nobody has money, nobody has slept, and nothing belongs to one person. Status is "
            "who cleaned last — an authority that expires in a day. Escalate through avoidance: "
            "the problem is not solved, it is moved, then moved again, until it is somebody's "
            "bed. Play catastrophe as a mild inconvenience and mild inconvenience as "
            "catastrophe. The reversal is usually that the disgusting solution actually worked."
        ),

        "dao_cu": (
            "one clean bowl",
            "a phone charger",
            "the shared mini fridge",
            "a laundry pod",
            "somebody's leftovers",
            "the shower caddy",
            "a stolen dining hall tray",
            "the thermostat knob",
            "an extension cord",
            "a whiteboard on the door",
            "the last roll of paper towels",
            "a fan",
            "a textbook nobody opened",
            "the microwave turntable",
            "a stack of quarters",
            "a desk lamp",
            "a wet towel on a chair",
            "the wifi router",
            "a bag of chips",
            "an alarm clock",
            "somebody's parking permit",
            "a kettle",
            "a sock behind the radiator",
            "the trash bag nobody tied",
        ),

        "mach": ("American college dorm friction blown one size too big: the dish nobody washed, the alarm going off for the fourth time, somebody's food eaten again, a group project at 2am. One small roommate dispute escalates and lands on a reversal where the most chaotic roommate turns out to have been right."),
    },

    "GARAGE HOURS": {
        "ten": "GARAGE HOURS",
        "mo_ta": "Hài gara sửa xe Mỹ — thợ già, thợ trẻ và những vị khách nghĩ mình biết xe hơn thợ.",
        "ty_le": "9:16",
        "nhan_vat": {
            "Hank": "Hank: 57-year-old man, grey moustache, navy work shirt with a name patch, dark jeans, oil-stained boots; deadpan veteran, diagnoses by sound.",
            "Rico": "Rico: 26-year-old man, black hair, red bandana, grey coveralls tied at the waist, black boots; fast and literal, learns by breaking things.",
            "Denise": "Denise: 41-year-old woman, short auburn hair, glasses, green work shirt, khaki trousers, steel-toe boots; dry, unimpressed, runs the front desk and the shop.",
            "Mr. Palmer": "Mr. Palmer: 49-year-old man, neat side part, pale polo shirt, pressed chinos, loafers; confidently wrong customer who watched a video about engines.",
        },
        "nha": (
            "Miller & Son Auto, a small American repair shop: two service bays with a car lift, a concrete floor, a wall of hanging tools. Keep the exact same layout, colors, tool positions and camera geography in every episode. Never redesign or recolor the shop."
        ),
        "phong": {
            "service bay": "Service Bay: grey concrete floor, a blue car lift with a sedan raised on it, a red tool chest on wheels.",
            "tool wall": "Tool Wall: pegboard wall covered in wrenches and sockets, a workbench with a vice.",
            "waiting area": "Waiting Area: four plastic chairs, a coffee machine nobody trusts, a window looking into the bay.",
            "shop yard": "Shop Yard: gravel yard outside the roll-up door, two parked cars, a stack of old tyres.",
            "parts counter": (
                "Parts Counter: chipped laminate counter, a wall of small drawers behind, a spinning "
                "stool, a taped-up catalogue."
            ),
            "pit": (
                "Pit: recessed service pit under a car, steel steps down, a trouble light on a hook, "
                "dark oil-stained walls."
            ),
            "lot fence": (
                "Lot Fence: chain-link fence at the edge of the yard, weeds along the base, three "
                "cars parked nose-in behind."
            ),
        },
        "style": (
            "Industrial and grounded: oil-stain browns, steel blue, one safety-orange accent. "
            "Heavy confident ink line, hard-edged mechanical shapes against soft human ones. "
            "One strong raking light from the open bay door with visible dust in the beam, and "
            "deep shadow where it does not reach. Metal reads by a single hard highlight, never "
            "by gradient.. hand-drawn 2D animation on twos, held key poses with snappy "
            "transitions between them, tapered ink line that thickens on the shadow side, "
            "appealing readable silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Unhurried working American voices for {vai}. Air tools two bays over, a radio "
            "nobody listens to, the specific sound being diagnosed. Precise lip sync. Prices "
            "are said quietly and land hard"
        ),
        "dien": "Hank diagnoses a car by listening to it; Rico is quick and learns the hard way; Denise is dry and actually runs the place; Mr. Palmer explains cars to mechanics",
        "hai": (
            "Expertise against price. One person can name a sound from across the room; the "
            "other cannot describe it and cannot afford it. Status is who can diagnose, not who "
            "owns the car. Escalate through the estimate — each new discovery adds a number, "
            "and the numbers are always said flatly. Never let the mechanic gloat. The reversal "
            "is often that the customer's ridiculous description was medically accurate."
        ),

        "dao_cu": (
            "a socket wrench",
            "the printed estimate",
            "a loaner key",
            "an air hose",
            "the coffee pot in the waiting area",
            "a torque wrench",
            "a box of shop rags",
            "the lift controls",
            "a customer's dashcam",
            "a set of hubcaps",
            "the parts catalogue",
            "a funnel",
            "the tire pressure gauge",
            "a bottle of coolant",
            "a jack stand",
            "the shop radio",
            "a work order clipboard",
            "a cracked side mirror",
            "the drain pan",
            "a battery charger",
            "a floor creeper",
            "the impact gun",
            "a spare fuse",
            "the courtesy shuttle sign",
        ),

        "mach": ("American auto shop friction blown one size too big: a noise the customer cannot describe, a quote read out loud, a part that costs more than the car, a check engine light ignored for a year. One small repair dispute escalates and lands on a reversal where the simplest explanation was the right one all along."),
    },

    "FENCE LINE": {
        "ten": "FENCE LINE",
        "mo_ta": "Hài hàng xóm Mỹ — hai nhà, một hàng rào, và một cuộc chiến lịch sự kéo dài nhiều năm.",
        "ty_le": "9:16",
        "nhan_vat": {
            "Ron": "Ron: 54-year-old man, neat grey hair, tucked-in white polo shirt, pressed beige shorts, white socks with sandals; anxious over-preparer, owns a measuring tape for the lawn.",
            "Deb": "Deb: 50-year-old woman, curly blonde hair, oversized tie-dye shirt, denim shorts, gardening clogs; dry and unimpressed, mows once a season on purpose.",
            "Chad": "Chad: 33-year-old man, backwards cap, sleeveless orange shirt, cargo shorts, flip-flops; confidently wrong, offers to help and makes it worse.",
            "Mrs. Okafor": "Mrs. Okafor: 69-year-old woman, silver braids, purple headwrap, long green dress, sensible shoes; deadpan veteran, watches everything from her porch.",
        },
        "nha": (
            "Two neighboring backyards on Cedar Lane separated by a low white picket fence: one lawn perfectly striped, the other overgrown. Keep the exact same yard layouts, fence position, colors and camera geography in every episode. Never redesign or recolor the yards."
        ),
        "phong": {
            "fence line": "Fence Line: a low white picket fence down the middle, a neat striped lawn on the left, an overgrown lawn on the right.",
            "neat yard": "Neat Yard: trimmed hedges, a garden gnome, a coiled hose on a wall bracket, a flowerbed with straight edges.",
            "messy yard": "Messy Yard: long grass, a half-built shed, a plastic chair on its side, a tarp over something unidentified.",
            "driveway": "Driveway: shared concrete driveway strip, two mailboxes on posts, a basketball hoop over one garage.",
            "shared alley": (
                "Shared Alley: strip of cracked concrete between two fences, two trash bins, a "
                "basketball hoop bolted to a garage."
            ),
            "front lawn": (
                "Front Lawn: mown grass to the sidewalk, a mailbox on a post, a young tree with a "
                "support stake."
            ),
            "toolshed": (
                "Toolshed: small wooden shed, a pegboard of hand tools, a bag of fertiliser, one "
                "dusty window."
            ),
        },
        "style": (
            "Bright suburban daylight, and the frame is deliberately symmetrical — the fence "
            "splits it, one world each side, and the two sides are drawn with the same care so "
            "the difference reads instantly. Clean medium line. Palette is lawn green, white "
            "picket, and one clashing accent per yard. Hard midday shadows with crisp edges.. "
            "hand-drawn 2D animation on twos, held key poses with snappy transitions between "
            "them, tapered ink line that thickens on the shadow side, appealing readable "
            "silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Extremely pleasant American voices for {vai} saying unpleasant things. Distant "
            "sprinkler, a leaf blower that stops at the worst moment, birds. Precise lip sync. "
            "Nobody ever sounds angry"
        ),
        "dien": "Ron measures the lawn and the fence; Deb is unbothered on purpose; Chad helps and makes it worse; Mrs. Okafor sees everything and comments once",
        "hai": (
            "Territorial war conducted entirely through politeness. Every attack is a favour "
            "and every favour is an attack. Status is whose yard is winning, judged by a "
            "standard nobody has agreed on. Escalate through escalating niceness — the "
            "friendlier the line, the worse the intent. The fence is the joke: it decides what "
            "is a problem. The reversal is usually that the neighbour was doing something "
            "completely innocent."
        ),

        "dao_cu": (
            "a branch over the fence",
            "a package on the wrong porch",
            "a leaf blower",
            "a garden gnome",
            "the shared trash bin",
            "a sprinkler head",
            "a for-sale sign",
            "a ladder borrowed last spring",
            "a bag of grass seed",
            "a security camera",
            "a wind chime",
            "a basketball in the flower bed",
            "a hose splitter",
            "a bird feeder",
            "a gate latch",
            "a stack of firewood",
            "a mower with a flat tire",
            "a string of patio lights",
            "a wheelbarrow",
            "a bag of mulch",
            "a hedge trimmer",
            "a mailbox flag",
            "a garden hose left running",
            "a pile of raked leaves",
        ),

        "mach": ("American suburban neighbor friction blown one size too big: a branch over the fence, a package delivered to the wrong porch, a leaf blower at seven in the morning, a fence painted one inch onto the wrong side. One polite dispute escalates and lands on a reversal where the neighbor everyone blamed was not responsible at all."),
    },

    "FRONT DESK": {
        "ten": "FRONT DESK",
        "mo_ta": "Hài quầy lễ tân phòng khám Mỹ — nơi mọi thủ tục vô lý gặp mọi bệnh nhân sốt ruột.",
        "ty_le": "9:16",
        "nhan_vat": {
            "Carla": "Carla: 43-year-old woman, dark hair in a clip, teal scrubs, ID badge on a lanyard, white shoes; deadpan veteran, has heard every excuse.",
            "Trent": "Trent: 27-year-old man, neat brown hair, blue scrubs, navy fleece vest, grey sneakers; anxious over-preparer, follows the form to the letter.",
            "Bev": "Bev: 61-year-old woman, short permed hair, floral blouse, beige cardigan, comfortable shoes; confidently wrong patient who diagnosed herself online.",
            "Dr. Shah": "Dr. Shah: 38-year-old woman, black hair, white coat over a navy shirt, dark trousers, flat shoes; dry, unimpressed, has forty seconds per patient.",
        },
        "nha": (
            "The front desk of a small American walk-in clinic: a laminate counter, a sliding glass window, rows of grey waiting chairs. Keep the exact same room layout, colors, furniture shapes and camera geography in every episode. Never redesign or recolor the clinic."
        ),
        "phong": {
            "front desk": "Front Desk: laminate counter with a sliding glass window, a clipboard on a chain, a bowl of hard candy.",
            "waiting room": "Waiting Room: four rows of grey chairs, a wall-mounted television playing nothing, a fake plant in the corner.",
            "hallway": "Hallway: pale green corridor, three closed exam-room doors, a wheeled blood pressure stand.",
            "exam room": "Exam Room: paper-covered exam table, a stool on wheels, a poster of a diagram on the wall.",
            "records room": (
                "Records Room: rows of beige filing cabinets, a step stool, a label printer, one high "
                "narrow window."
            ),
            "break nook": (
                "Break Nook: a small counter with a kettle, two chairs, a corkboard of curled "
                "notices, a mini fridge."
            ),
            "parking bay": (
                "Parking Bay: painted asphalt spaces outside the glass entrance, a low kerb, a sign "
                "post with no sign."
            ),
        },
        "style": (
            "Clinical and calm on the surface: sea-glass mint, clipboard white, pale wood. Thin "
            "clean line with no texture at all. Waiting-room symmetry — chairs in a row, "
            "everything aligned, which makes one thing out of place scream. Soft even light "
            "with a faint cool cast and almost no shadow.. hand-drawn 2D animation on twos, "
            "held key poses with snappy transitions between them, tapered ink line that "
            "thickens on the shadow side, appealing readable silhouettes, generous squash and "
            "stretch on the face only"
        ),
        "audio": (
            "Warm, endlessly patient American voices for {vai}. A phone that rings and is never "
            "answered, a printer, the specific squeak of a chair. Precise lip sync. The patient "
            "voice never cracks, which is the joke"
        ),
        "dien": "Carla has heard every excuse twice; Trent follows the form even when it makes no sense; Bev arrives with a diagnosis she found online; Dr. Shah is dry and running late",
        "hai": (
            "A system against a person who needs something from it. Status is who holds the "
            "form. The staff are not villains — they are the third-most-trapped people in the "
            "room. Escalate through repetition: the same question asked a fourth time, in a "
            "slightly different way. Never let the desk lose its temper. The reversal is "
            "usually that the absurd rule exists for a reason nobody in the room could have "
            "guessed."
        ),

        "dao_cu": (
            "a form asking the same question four times",
            "an expired insurance card",
            "a clipboard pen on a chain",
            "the sign-in sheet",
            "a fax machine",
            "a waiting room magazine from 2019",
            "a hand sanitizer pump",
            "the appointment book",
            "a wheelchair nobody moved",
            "a label printer",
            "a thermometer cover box",
            "a broken chair in the waiting room",
            "the water dispenser",
            "a stack of referral slips",
            "the phone on hold",
            "a parking validation stamp",
            "a box of tissues",
            "a fish tank",
            "a laminated notice on the glass",
            "a prescription pad",
            "a scale with a sticky slider",
            "a bin of toy blocks",
            "a name badge",
            "the after-hours number",
        ),

        "mach": ("American clinic front-desk friction blown one size too big: a form asking the same question four times, an insurance card that expired, a patient who is early for next week, a waiting room television nobody can turn off. One small paperwork dispute escalates and lands on a reversal where the rule everyone was arguing about does not exist."),
    },

    "ROAD TRIP": {
        "ten": "ROAD TRIP",
        "mo_ta": "Hài trong xe Mỹ — bốn người, một chuyến đi dài, và không ai chịu nhường quyền chỉnh nhạc.",
        "ty_le": "9:16",
        "nhan_vat": {
            "Ted": "Ted: 47-year-old man, receding brown hair, blue polo shirt, cargo shorts, driving sandals; confidently wrong, refuses to stop for directions or for anything.",
            "Anne": "Anne: 45-year-old woman, straight dark hair, striped red top, jeans, white sneakers; dry, unimpressed, holds the map she does not need.",
            "Ellie": "Ellie: 14-year-old girl, black hair in a high ponytail, purple hoodie, ripped jeans, headphones around her neck; fast and literal, narrates the trip.",
            "Grandma Rue": "Grandma Rue: 74-year-old woman, white curls, large sunglasses, lavender cardigan, floral skirt; deadpan veteran, packed sandwiches for a four-hour drive.",
        },
        "nha": (
            "The inside of a beige family sedan on an American highway, seen from a fixed camera on the dashboard or from the back seat. Keep the exact same interior, seat colors, mirror position and camera geography in every episode. Never redesign or recolor the car."
        ),
        "phong": {
            "front seats": "Front Seats: two grey cloth front seats, a dashboard with a cracked phone mount, a rear-view mirror with an air freshener.",
            "back seat": "Back Seat: grey bench seat, three seatbelts, a cooler on the floor, a window showing highway.",
            "gas station": "Gas Station: fuel pump island under a bright canopy, the sedan parked at pump three, a convenience store behind.",
            "rest stop": "Rest Stop: a picnic table on grass beside a parking lot, a vending machine shelter, the sedan parked nearby.",
            "motel room": (
                "Motel Room: two beds with matching bedspreads, a boxy TV on a dresser, heavy "
                "curtains half open."
            ),
            "diner booth": (
                "Diner Booth: roadside booth by a window, laminated menus upright behind the napkin "
                "holder."
            ),
            "scenic overlook": (
                "Scenic Overlook: gravel pull-off, a low guard rail, a coin-operated viewer, wide sky "
                "beyond."
            ),
        },
        "style": (
            "Car interior, horizontal composition, and the light MOVES — warm dashboard glow "
            "inside against cool sky outside, with scenery sliding past the windows at a "
            "constant speed. Medium line, soft rounded upholstery shapes. Palette is faded "
            "upholstery beige, highway grey and whatever colour the sky is doing. Everyone is "
            "framed by a headrest.. hand-drawn 2D animation on twos, held key poses with snappy "
            "transitions between them, tapered ink line that thickens on the shadow side, "
            "appealing readable silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Close, slightly boxed-in American voices for {vai} — a car interior is a small "
            "room. Constant tyre hum, indicator tick, one song nobody agreed on. Precise lip "
            "sync. Nobody can leave, so nobody can end a conversation"
        ),
        "dien": "Ted refuses to stop for anything; Anne is dry and holds the map; Ellie narrates everything out loud; Grandma Rue produces exactly what is needed from her bag",
        "hai": (
            "Confinement comedy: four people, one small room, and it is moving. Status is who "
            "holds the wheel versus who holds the map, and those are different powers. Escalate "
            "through distance — every mile makes the disagreement more expensive to fix. Nobody "
            "can walk out, so arguments do not end, they get parked and reopened. The reversal "
            "is usually visible through a window that one person has been refusing to look at."
        ),

        "dao_cu": (
            "the aux cable",
            "a paper map",
            "a gas station hot dog",
            "the last phone charger",
            "a cooler between the seats",
            "a window that only rolls halfway",
            "a bag of boiled peanuts",
            "the tire pressure light",
            "a road atlas from 1998",
            "a souvenir snow globe",
            "a coffee in the cup holder",
            "the trunk that will not shut",
            "a roll of quarters for tolls",
            "a travel pillow",
            "a bug on the windshield",
            "the spare key taped under the seat",
            "a receipt from three states ago",
            "an air freshener",
            "the cruise control button",
            "a wet swimsuit in a bag",
            "a car seat nobody can uninstall",
            "the fold-out table at a rest stop",
            "a bag of ice melting",
            "the odometer about to roll over",
        ),

        "mach": ("American road-trip friction blown one size too big: a wrong exit taken on purpose, a gas gauge argument, control of the music, somebody needing a bathroom eight minutes after the last stop. One small car dispute escalates and lands on a reversal where the person in the back seat was right about the route."),
    },

    "PET HOUSE": {
        "ten": "PET HOUSE",
        "mo_ta": "Hài nhà nhiều thú cưng Mỹ — hai con vật cạnh tranh, một con chuột lang quan sát, và hai người chủ không hiểu gì.",
        "ty_le": "9:16",
        "nhan_vat": {
            "Duke": "Duke: large brown dog, floppy ears, red collar, expressive eyebrows; confidently wrong, believes every plan will work.",
            "Cleo": "Cleo: sleek grey cat, green eyes, silver collar with a bell; dry and unimpressed, silently judges Duke.",
            "Nugget": "Nugget: small golden hamster, round body, tiny paws; silent judge, watches from the cage and misses nothing.",
            "Owen": "Owen: 35-year-old man, short beard, green flannel shirt, jeans, wool socks; anxious over-preparer, reads pet forums at midnight.",
            "Rae": "Rae: 33-year-old woman, dark bob haircut, mustard sweater, black jeans, bare feet; deadpan, knows exactly which animal did it.",
        },
        "nha": (
            "A small American home shared with three pets: a living room with a worn couch, a pet bed by the radiator, a hamster cage on a side table. Keep the exact same room layout, colors, furniture shapes and camera geography in every episode. Never redesign or recolor the home."
        ),
        "phong": {
            "living room": "Living Room: warm grey walls, a worn beige couch facing camera, a round pet bed near the radiator, a hamster cage on a side table.",
            "kitchen": "Kitchen: white cabinets, two pet bowls on a mat by the fridge, a bin with a slightly loose lid.",
            "hallway": "Hallway: narrow hall with a coat rack, a leash hanging on a hook, a mat by the front door.",
            "back garden": "Back Garden: small fenced garden, patchy grass, a half-buried tennis ball, a garden chair.",
            "utility room": (
                "Laundry Room: washer and dryer side by side, a folded pile on top, a basket on the "
                "floor, a small window."
            ),
            "front hall": (
                "Front Hall: a coat hook rail, a shoe tray, a narrow console table, the front door "
                "with a letter slot."
            ),
            "vet waiting room": (
                "Vet Waiting Room: bench seating along two walls, a scale on the floor, a rack of "
                "leaflets, sealed pet food bags."
            ),
        },
        "style": (
            "Shot from about knee height, because that is where the cast lives — humans are "
            "often just legs and a voice. Soft rounded shape language, toy-bright saturated "
            "palette, and a fine broken line that reads as fur on the animals and stays solid "
            "on the furniture. Warm low sun through a window, long shadows across the floor.. "
            "hand-drawn 2D animation on twos, held key poses with snappy transitions between "
            "them, tapered ink line that thickens on the shadow side, appealing readable "
            "silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Human American voices for {vai} heard from floor level, plus animal sounds only — "
            "no talking animals. Collar tags, claws on floorboards, a bag being investigated. "
            "Precise lip sync on the humans; the animals act with the face"
        ),
        "dien": "Duke is confident every plan will work; Cleo watches and judges silently; Nugget observes everything from the cage; Owen over-researches; Rae already knows which animal is responsible",
        "hai": (
            "Animal logic played completely straight — the pets have a plan and it is "
            "internally consistent. Status is which animal the human believes. Never "
            "anthropomorphise with speech; the whole joke is that they cannot explain "
            "themselves and do not need to. Escalate through evidence accumulating in the wrong "
            "place. The reversal is usually that the animal was right and the human has just "
            "noticed."
        ),

        "dao_cu": (
            "a food bowl",
            "the good spot on the couch",
            "a squeaky toy under the fridge",
            "a leash by the door",
            "a cardboard box",
            "the vacuum",
            "a bag of treats on a high shelf",
            "a scratching post",
            "the trash bin lid",
            "a laser pointer",
            "a chewed shoe",
            "the cat carrier",
            "a screen door with a hole",
            "a sock",
            "the sunny patch on the floor",
            "a water fountain bowl",
            "a bag of kibble",
            "the doorbell",
            "a blanket on the bed",
            "a tennis ball under the couch",
            "the litter box",
            "a package on the porch",
            "a hairbrush full of fur",
            "the pet gate",
        ),

        "mach": ("American pet-household friction blown one size too big: something knocked off a counter, a bin investigated, a vet appointment sensed in advance, one bowl eaten from twice. One small animal dispute escalates and lands on a reversal where the smallest and quietest pet caused all of it."),
    },


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
            "laundry room": (
                "Laundry Room: washer and dryer side by side, a wire shelf of detergent, a basket of "
                "unsorted clothes."
            ),
            "bathroom": (
                "Bathroom: white tile, a pedestal sink, a mirrored cabinet, a shower curtain on a "
                "rail."
            ),
            "attic stairs": (
                "Attic Stairs: a pull-down ladder from the hall ceiling, dust in the light, boxes "
                "visible above."
            ),
        },

        "style": (
            "Classic American family-sitcom warmth: cream walls, honey oak, and one saturated "
            "accent per room. Medium confident line that tapers at the ends of a stroke. "
            "Staging is theatrical — the room reads like a set, with a clear centre and clear "
            "wings. Warm key light from a practical window, gentle fill, one soft shadow per "
            "figure.. hand-drawn 2D animation on twos, held key poses with snappy transitions "
            "between them, tapered ink line that thickens on the shadow side, appealing "
            "readable silhouettes, generous squash and stretch on the face only"
        ),
        # {vai} do mã điền theo người CÓ MẶT trong tập — xem chú thích ở `_ghep`.
        "audio": (
            "Familiar, overlapping American family voices for {vai} — people who interrupt each "
            "other because they have known each other forever. House ambience: a fridge hum, a "
            "screen door, a TV in another room. Precise lip sync"
        ),
        "dien": (
            "Mike is confident even when obviously wrong; Lisa is dry and practical; Tommy is "
            "clever and playful; Grandpa Joe is deadpan; Buddy communicates mostly through facial "
            "expressions and small actions"
        ),

        # Mạch kênh: thứ quyết định tập nào HỢP kênh, tập nào lạc. Dùng làm đề bài cho AI.
        "hai": (
            "Domestic friction where the stakes are absurdly small and the commitment is "
            "absolute. Status is who is currently right, and it changes hands within the scene. "
            "The confident one is always wrong and never learns; the quiet one is always right "
            "and never says so. Escalate through effort — the wrong solution gets more "
            "elaborate, never abandoned. The reversal belongs to the family member with the "
            "least authority in the room."
        ),

        "dao_cu": (
            "the last slice of pizza",
            "the thermostat",
            "a streaming password",
            "the good scissors",
            "a phone charger",
            "the remote control",
            "a package on the porch",
            "the laundry basket",
            "a jar nobody can open",
            "the last roll of paper towels",
            "a birthday cake",
            "the smoke detector battery",
            "a grocery list",
            "the garage door opener",
            "a permission slip due yesterday",
            "the ice tray",
            "a broken drawer handle",
            "the car keys",
            "a leftover container with no lid",
            "the sprinkler timer",
            "a school project due tomorrow",
            "the wifi router",
            "a coupon that expired",
            "the good towel",
        ),

        "mach": (
            "Everyday American household friction blown one size too big: chores, groceries, "
            "thermostats, streaming passwords, school runs, weekend projects, holiday visits. "
            "One small domestic disagreement escalates for six seconds and lands on a reversal "
            "where the least likely family member turns out to be right."
        ),
    },
    "NIGHT SHIFT": {
        "ten": "NIGHT SHIFT",
        "mo_ta": (
            "Hài cửa hàng tiện lợi 24h Mỹ — hai giờ sáng, đèn huỳnh quang, và những vị khách chỉ "
            "xuất hiện lúc ấy."
        ),
        "ty_le": "9:16",
        "nhan_vat": {
            "Dez": (
                "Dez: 27-year-old man, short black twists, red store polo over a grey hoodie, black "
                "jeans, white sneakers; unshockable, has seen every version of this night."
            ),
            "Marisol": (
                "Marisol: 34-year-old woman, dark hair in a claw clip, red store polo, khaki pants, "
                "black slip-resistant shoes; runs the register like a control tower, keeps receipts "
                "on everyone."
            ),
            "Rusty": (
                "Rusty: 61-year-old man, grey buzz cut, tan work jacket, jeans, scuffed boots; comes "
                "in every night at the same hour, confidently wrong about everything."
            ),
            "Pip": (
                "Pip: 19-year-old man, floppy blond hair, oversized red polo, cargo shorts, high-top "
                "sneakers; brand new, takes every instruction literally."
            ),
        },
        "nha": (
            "The Gas-N-Go, a 24-hour convenience store off a state highway: white tile floor, "
            "humming coolers along the back wall, one register by the door under a bright "
            "fluorescent grid. Keep the exact same layout, colors, shelving and camera geography "
            "in every episode. Never redesign or recolor the store."
        ),
        "phong": {
            "register": (
                "Register: a low counter with a scanner and a tip cup, a rack of gum, a lottery "
                "ticket dispenser, a small monitor showing the pumps."
            ),
            "cooler aisle": (
                "Cooler Aisle: a long wall of glass-door coolers glowing blue, a wet spot on the "
                "tile, a yellow caution sign nobody moved."
            ),
            "snack aisle": (
                "Snack Aisle: two metal shelves of bagged snacks, one shelf sagging, a cardboard "
                "display half collapsed at the end."
            ),
            "coffee counter": (
                "Coffee Counter: three carafes on warmers, a tower of lids, a sugar caddy, a stack of "
                "napkins in a wet spot."
            ),
            "back stock": (
                "Back Stock: grey concrete floor, stacked cases of drinks to the ceiling, a hand "
                "truck, a single caged bulb."
            ),
            "forecourt": (
                "Forecourt: cracked asphalt under a bright canopy, two fuel pumps, an air hose reel, "
                "dark highway beyond."
            ),
            "walk-in fridge": (
                "Walk-In Fridge: steel racks stacked with crates, a heavy insulated door, cold blue "
                "light, breath visible."
            ),
        },
        "style": (
            "Hard fluorescent light with no shadow anywhere — the specific flatness of a store at "
            "two in the morning, where everything is equally lit and nothing looks good. Palette "
            "is white tile, cooler-glass blue, and one loud brand red on the uniforms. Clean even "
            "line of constant weight. Outside the windows is pure black, so the store reads as an "
            "island.. hand-drawn 2D animation on twos, held key poses with snappy transitions "
            "between them, tapered ink line that thickens on the shadow side, appealing readable "
            "silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Flat, unhurried American voices for {vai} — nobody at this hour has energy to raise "
            "their voice. Cooler compressors, a door chime, a radio playing to nobody. Precise "
            "lip sync. The pauses are long because there is nowhere to be"
        ),
        "dien": (
            "Dez is unshockable and has seen this exact thing before; Marisol runs the counter "
            "and keeps receipts; Rusty is confidently wrong and comes back every night; Pip is "
            "new and takes every instruction literally"
        ),
        "hai": (
            "Two in the morning comedy: the rules of daytime do not apply and everyone knows it. "
            "The staff are not surprised by anything, which makes the customer's urgency funny by "
            "contrast. Status is who has been on this shift longer. Escalate through the "
            "transaction — a simple purchase acquires one more condition at a time until it is a "
            "negotiation. Never let the staff panic; the joke dies the moment somebody treats it "
            "as an emergency."
        ),
        "dao_cu": (
            "the coffee that has been on the warmer since midnight",
            "a lottery ticket",
            "the hot dog roller",
            "a bag of ice",
            "the card reader",
            "a mop bucket",
            "the last energy drink",
            "a pump that will not authorize",
            "the bathroom key on a giant plastic paddle",
            "a phone charger on a peg hook",
            "the price gun",
            "a stack of scratch-offs",
            "the air hose",
            "a broken freezer door",
            "the security monitor",
            "a case of water on a hand truck",
            "the receipt roll",
            "a sign taped to the door",
            "the microwave by the coffee",
            "a delivery pallet in the aisle",
            "the trash can by the pumps",
            "a coupon that expired",
            "the window squeegee",
            "the shift schedule on a clipboard",
        ),
        "mach": (
            "Late-night convenience store friction blown one size too big: a card that will not "
            "read, a pump that will not start, a customer who wants something the store has never "
            "carried, a delivery arriving at the worst hour. One small transaction escalates and "
            "lands on a reversal where the person nobody was listening to turns out to have "
            "solved it already."
        ),
    },

    "OPEN HOUSE": {
        "ten": "OPEN HOUSE",
        "mo_ta": (
            "Hài môi giới nhà đất Mỹ — mở cửa xem nhà cuối tuần, nơi mọi khuyết điểm của căn nhà "
            "và của con người cùng lộ ra."
        ),
        "ty_le": "9:16",
        "nhan_vat": {
            "Brenda": (
                "Brenda: 45-year-old woman, blonde bob, teal blazer over a white blouse, cream "
                "slacks, low heels; sells everything as a feature, never says a negative word."
            ),
            "Curtis": (
                "Curtis: 38-year-old man, neat beard, grey quarter-zip, dark jeans, brown loafers; "
                "dry, reads the inspection report out loud at the worst moments."
            ),
            "Nadia": (
                "Nadia: 31-year-old woman, black hair in a high ponytail, olive jacket, wide-leg "
                "trousers, white trainers; fast and literal, opens every cupboard."
            ),
            "Mr. Ellery": (
                "Mr. Ellery: 68-year-old man, thin white hair, brown cardigan, grey trousers, "
                "orthopedic shoes; comes to every open house in the county, buys nothing, knows "
                "everything."
            ),
        },
        "nha": (
            "A 1970s split-level house on a cul-de-sac, staged for sale: beige carpet, fresh "
            "white paint over everything, borrowed furniture that is one size too small for each "
            "room. Keep the exact same layout, colors, staging furniture and camera geography in "
            "every episode. Never redesign or recolor the house."
        ),
        "phong": {
            "staged living room": (
                "Living Room: beige carpet, a rented grey sofa too small for the wall, a glass coffee "
                "table with one staged book, vertical blinds."
            ),
            "show kitchen": (
                "Kitchen: white cabinets, laminate counters, a bowl of plastic lemons, a dishwasher "
                "with the sticker still on."
            ),
            "primary bedroom": (
                "Primary Bedroom: a bed with a hotel-white duvet, two mismatched lamps, an empty "
                "closet with the door removed."
            ),
            "lower level": (
                "Basement: bare concrete floor, a sump pump in the corner, one small window at "
                "ceiling height, a dehumidifier running."
            ),
            "two-car garage": (
                "Garage: oil-stained concrete, a pegboard with no tools on it, a water heater in the "
                "corner, a single hanging bulb."
            ),
            "back lot": (
                "Backyard: patchy grass, a chain-link fence, a concrete patio slab, one shrub trimmed "
                "into a ball."
            ),
            "driveway": (
                "Driveway: cracked concrete to the street, an OPEN HOUSE sign frame with no sign in "
                "it, two cars parked at odd angles."
            ),
        },
        "style": (
            "Everything is staged, and staged reads as slightly wrong: furniture one size too "
            "small, every surface bare, a house pretending nobody lives in it. Palette is builder "
            "beige, landlord white, and one teal accent that follows Brenda around. Clean thin "
            "line, flat midday light through vertical blinds throwing hard stripes across the "
            "carpet.. hand-drawn 2D animation on twos, held key poses with snappy transitions "
            "between them, tapered ink line that thickens on the shadow side, appealing readable "
            "silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Bright, relentlessly positive American voices for {vai} describing things that are "
            "not good. A door chime, footsteps on bare floors, the specific hollow sound of an "
            "empty room. Precise lip sync. Nobody says the negative word out loud"
        ),
        "dien": (
            "Brenda sells every flaw as a feature and never says a negative word; Curtis reads "
            "the inspection report out loud at the worst moment; Nadia opens every cupboard and "
            "says what she finds; Mr. Ellery has been to every open house in the county and buys "
            "nothing"
        ),
        "hai": (
            "Comedy of the thing nobody will name. Everyone in the room can see the problem and "
            "the language forbids saying it — 'cozy' means small, 'original' means broken, "
            "'motivated seller' means run. Status is who can hold the euphemism longest. Escalate "
            "by the house itself supplying evidence at the worst moment. The reversal is usually "
            "that the flaw is exactly what one person was looking for."
        ),
        "dao_cu": (
            "a bowl of plastic lemons",
            "the inspection report",
            "a lockbox on the door",
            "an air freshener plugged in",
            "the sump pump",
            "a closet door that will not slide",
            "the water heater",
            "a stack of flyers",
            "fresh paint over a stain",
            "the thermostat",
            "a doorbell camera",
            "the sign-in sheet",
            "a tray of grocery store cookies",
            "the garage door opener",
            "a window that is painted shut",
            "the fuse box",
            "a plug-in nightlight",
            "the crawl space hatch",
            "a rented sofa",
            "the mailbox with the flag stuck up",
            "a smoke detector chirping",
            "the sprinkler control box",
            "a key that does not work",
            "the neighbor's dog barking through the fence",
        ),
        "mach": (
            "American open-house friction blown one size too big: a smell nobody will name, a "
            "noise that starts every time someone stops talking, a neighbor who wanders over, a "
            "room that is not on the floor plan. One euphemism escalates until the house "
            "contradicts it out loud, and lands on a reversal where the flaw turns out to be the "
            "selling point."
        ),
    },

    "AISLE SIX": {
        "ten": "AISLE SIX",
        "mo_ta": (
            "Hài siêu thị Mỹ — nhân viên ca tối, xe đẩy, và những yêu cầu chỉ nảy ra trong lòng "
            "một siêu thị."
        ),
        "ty_le": "9:16",
        "nhan_vat": {
            "Tay": (
                "Tay: 24-year-old man, short dreads, green store apron over a black tee, jeans, black "
                "sneakers; fast, literal, answers exactly what was asked."
            ),
            "Ginny": (
                "Ginny: 52-year-old woman, short grey-streaked hair, green apron, floral blouse, navy "
                "trousers; has worked here through four owners, deadpan."
            ),
            "Omar": (
                "Omar: 29-year-old man, close beard, green apron over a blue button-down, chinos, "
                "brown shoes; the manager, confidently wrong, loves a system."
            ),
            "Kelsey": (
                "Kelsey: 21-year-old woman, red hair in a bun, green apron, black leggings, white "
                "trainers; anxious over-preparer, carries a label maker everywhere."
            ),
        },
        "nha": (
            "A mid-size American grocery store on a weeknight: polished grey floor, long aisles "
            "under bright white light, a row of registers at the front with only two open. Keep "
            "the exact same layout, colors, fixtures and camera geography in every episode. Never "
            "redesign or recolor the store."
        ),
        "phong": {
            "aisle six": (
                "Aisle Six: two tall shelves of canned goods, a stepstool left in the middle, a price "
                "gun on a shelf edge, an endcap of sale items."
            ),
            "produce": (
                "Produce: sloped green display tables of fruit, a misting pipe overhead, a stack of "
                "paper bags, a scale on a post."
            ),
            "registers": (
                "Registers: four checkout lanes with only two lights on, conveyor belts, a candy "
                "rack, a self-checkout kiosk at the end."
            ),
            "deli counter": (
                "Deli Counter: a glass case of sliced meats, a slicer on the back bench, a number "
                "dispenser, a ticket display on the wall."
            ),
            "freezer aisle": (
                "Freezer Aisle: glass doors fogged from the inside, a stack of empty pallets, one "
                "door propped with a box."
            ),
            "stockroom": (
                "Stockroom: concrete floor, pallets shrink-wrapped to the ceiling, a baler, a time "
                "clock by the door."
            ),
            "parking lot": (
                "Parking Lot: painted asphalt at dusk, three cart corrals, a light pole with one dead "
                "lamp, carts scattered between spaces."
            ),
        },
        "style": (
            "Supermarket bright — flat white light everywhere, saturated packaging colors stacked "
            "into walls, and long straight perspective down the aisles. Palette is store-apron "
            "green, polished grey floor, and the loud multicolor of product shelves used as "
            "texture, never as detail. Clean medium line, everything perpendicular, which makes "
            "one crooked thing scream.. hand-drawn 2D animation on twos, held key poses with "
            "snappy transitions between them, tapered ink line that thickens on the shadow side, "
            "appealing readable silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Even, professionally pleasant American voices for {vai}. A PA announcement nobody "
            "listens to, cart wheels, the beep of a scanner. Precise lip sync. Everything is said "
            "at the volume of someone who has been standing for six hours"
        ),
        "dien": (
            "Tay answers exactly what was asked and nothing more; Ginny has worked here through "
            "four owners and has seen this; Omar is the manager and loves a system that does not "
            "fit; Kelsey over-prepares and labels everything"
        ),
        "hai": (
            "Comedy of the customer request that has no correct answer. The staff are "
            "professionally obligated to help with something that cannot be helped. Status is "
            "seniority, and the manager has less of it than the woman who has been here twenty "
            "years. Escalate through procedure — a simple question triggers a policy, which "
            "triggers a form, which triggers a phone call. The reversal is usually that the "
            "customer was right about something nobody checked."
        ),
        "dao_cu": (
            "a price gun",
            "the last rotisserie chicken",
            "a cart with one bad wheel",
            "the number dispenser at the deli",
            "a coupon from 2019",
            "the self-checkout kiosk",
            "a pallet in the aisle",
            "the PA microphone",
            "a stepstool left out",
            "the misting pipe over the produce",
            "a case of eggs",
            "the time clock",
            "a spill and a wet floor sign",
            "the schedule taped to the stockroom wall",
            "a broken scale",
            "the freezer door that will not seal",
            "a stack of paper bags",
            "the baler",
            "a customer's shopping list",
            "the cart corral",
            "a sale sign for the wrong item",
            "the deli slicer",
            "a box cutter",
            "the intercom handset",
        ),
        "mach": (
            "American grocery store friction blown one size too big: an item that is on sale but "
            "not in the system, a request the policy has no answer for, a cart nobody will claim, "
            "a delivery that arrives during the rush. One small question escalates through "
            "procedure and lands on a reversal where the customer turns out to have been right "
            "the whole time."
        ),
    },

    "PARENT PICKUP": {
        "ten": "PARENT PICKUP",
        "mo_ta": (
            "Hài hàng xe đón con Mỹ — ba giờ chiều, hai mươi phút, và toàn bộ chính trị của phụ "
            "huynh trong một hàng xe."
        ),
        "ty_le": "9:16",
        "nhan_vat": {
            "Todd": (
                "Todd: 41-year-old man, receding brown hair, quarter-zip fleece over a polo, cargo "
                "pants, running shoes; confidently wrong, has a theory about the line."
            ),
            "Anjali": (
                "Anjali: 37-year-old woman, black hair in a low bun, denim jacket, dark jeans, white "
                "sneakers; dry, arrives late on purpose and gets out first."
            ),
            "Coach Dane": (
                "Coach Dane: 33-year-old man, buzz cut, school windbreaker, athletic shorts, whistle "
                "on a lanyard; runs the pickup line like a drill, deadpan."
            ),
            "Mrs. Vail": (
                "Mrs. Vail: 59-year-old woman, silver bob, quilted vest over a turtleneck, pressed "
                "slacks, loafers; head of the parent committee, has a laminated map."
            ),
        },
        "nha": (
            "The front loop of Riverbend Elementary at three in the afternoon: a covered walkway "
            "along the school wall, a painted lane curving past it, orange cones marking the "
            "numbered zones. Keep the exact same layout, colors, signage and camera geography in "
            "every episode. Never redesign or recolor the school."
        ),
        "phong": {
            "pickup lane": (
                "Pickup Lane: a painted curve of asphalt beside a covered walkway, orange cones every "
                "few yards, numbered zone signs on posts."
            ),
            "front steps": (
                "Front Steps: four wide concrete steps to a glass double door, a metal handrail, a "
                "bell housing above."
            ),
            "crosswalk": (
                "Crosswalk: white stripes across the loop, a portable stop sign on a stand, a yellow "
                "curb."
            ),
            "overflow lot": (
                "Overflow Lot: gravel with faded parking lines, a chain across the far entrance, "
                "weeds along the edge."
            ),
            "front office": (
                "Front Office: a laminate counter, a sign-out clipboard, two chairs against the wall, "
                "a wall clock."
            ),
            "playground fence": (
                "Playground Fence: chain-link along the field, a gate with a spring latch, a bike "
                "rack half full."
            ),
            "bus lane": (
                "Bus Lane: a wide separate strip with a yellow curb, a shelter with two benches, a NO "
                "CARS sign on a post."
            ),
        },
        "style": (
            "Bright flat afternoon sun on asphalt — the specific glare of three o'clock, with "
            "hard short shadows directly under everything. Palette is school-bus yellow, cone "
            "orange, and the washed grey of a parking lot, with each family's car a different "
            "saturated color so the line reads as a row of blocks. Clean medium line, strong "
            "horizontal composition.. hand-drawn 2D animation on twos, held key poses with snappy "
            "transitions between them, tapered ink line that thickens on the shadow side, "
            "appealing readable silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Extremely polite American voices for {vai} through half-open car windows. Idling "
            "engines, a distant bell, a whistle. Precise lip sync. Everyone is pleasant and "
            "nobody is happy"
        ),
        "dien": (
            "Todd has a theory about why the line is slow and is wrong; Anjali arrives late on "
            "purpose and it works; Coach Dane runs the line like a drill and does not negotiate; "
            "Mrs. Vail heads the parent committee and has a laminated map"
        ),
        "hai": (
            "Comedy of the rule that everyone follows and nobody agreed to. The pickup line has a "
            "hierarchy, a folklore and an unwritten law, all invisible to outsiders and defended "
            "to the death by insiders. Status is your position in the line, which is a moral "
            "judgment. Escalate through waiting — every extra second in a stopped car doubles the "
            "stakes. Nobody can leave the vehicle, so nobody can win an argument outright."
        ),
        "dao_cu": (
            "a laminated zone map",
            "a car seat nobody can uninstall",
            "the numbered placard on the dashboard",
            "an orange cone",
            "a permission slip due yesterday",
            "the sign-out clipboard",
            "a whistle",
            "a lunchbox left in the back seat",
            "the portable stop sign",
            "a group text nobody answers",
            "a bag of soccer gear",
            "the school bell",
            "a folding chair in a trunk",
            "a magnetic honor roll sticker",
            "the crossing guard's vest",
            "a birthday invitation for the whole class",
            "an idling engine",
            "the bike rack",
            "a juice box leaking in a backpack",
            "a dented bumper",
            "the parent committee sign-up sheet",
            "a spare pair of shoes",
            "the drop-off gate latch",
            "a coffee in the cup holder going cold",
        ),
        "mach": (
            "American school pickup friction blown one size too big: a car in the wrong zone, a "
            "rule nobody was told, a parent who parks and walks up, a bell that rings two minutes "
            "late. One small breach of line etiquette escalates and lands on a reversal where the "
            "person breaking the rule turns out to have been told to."
        ),
    },

    "MOVING DAY": {
        "ten": "MOVING DAY",
        "mo_ta": (
            "Hài chuyển nhà Mỹ — hai người khuân, một cầu thang, và một cái ghế sofa không chịu "
            "qua cửa."
        ),
        "ty_le": "9:16",
        "nhan_vat": {
            "Big Ray": (
                "Big Ray: 44-year-old man, heavy build, shaved head, grey moving-company tee, work "
                "jeans, steel-toe boots; deadpan veteran, has moved this exact sofa before."
            ),
            "Jonesy": (
                "Jonesy: 26-year-old man, wiry, backwards cap, grey company tee, cargo shorts, "
                "sneakers; confidently wrong about angles, always says it will fit."
            ),
            "Tam": (
                "Tam: 30-year-old woman, black hair in a braid, grey company tee, work pants, gloves "
                "tucked in the belt; dry, does the math and is always right."
            ),
            "Mr. Diggs": (
                "Mr. Diggs: 71-year-old man, white mustache, plaid shirt, suspenders, khakis, "
                "slippers; the customer, supervises, packed nothing."
            ),
        },
        "nha": (
            "A second-floor walk-up apartment on moving day: bare walls with picture hooks still "
            "in them, a narrow stairwell with one tight turn, a truck backed up to the curb "
            "outside. Keep the exact same layout, colors, stair geometry and camera geography in "
            "every episode. Never redesign or recolor the building."
        ),
        "phong": {
            "stairwell": (
                "Stairwell: narrow painted steps with one tight landing turn, a metal handrail, a "
                "scuffed wall at shoulder height."
            ),
            "empty apartment": (
                "Empty Apartment: bare beige walls with picture hooks left in, scratched wood floor, "
                "one bare bulb, a window with no curtain."
            ),
            "truck ramp": (
                "Truck Ramp: a metal ramp down from a box truck to the curb, furniture pads stacked "
                "at the bottom, a dolly leaning on the truck."
            ),
            "curb": (
                "Curb: a strip of pavement between the truck and the door, a NO PARKING cone, a "
                "wheeled trash bin pushed aside."
            ),
            "landing": (
                "Landing: a small square between flights, a fire extinguisher case on the wall, a "
                "window painted shut."
            ),
            "storage unit": (
                "Storage Unit: a corrugated roll-up door, concrete floor, boxes stacked to the "
                "ceiling on one side, a bare bulb on a pull chain."
            ),
            "loading dock": (
                "Loading Dock: a raised concrete edge, a rubber bumper strip, a rolling cage cart, a "
                "taped-up sign about hours."
            ),
        },
        "style": (
            "Working daylight — flat overcast outside, one bare bulb inside, and everything "
            "covered in the specific grey of moving pads and cardboard. Palette is cardboard "
            "brown, blanket grey and one safety-orange accent on the equipment. Heavy confident "
            "ink line, blocky rectangular shapes everywhere, so a diagonal reads as an "
            "emergency.. hand-drawn 2D animation on twos, held key poses with snappy transitions "
            "between them, tapered ink line that thickens on the shadow side, appealing readable "
            "silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Short, breath-conscious American voices for {vai} — people carrying something heavy "
            "do not make speeches. Boots on stairs, cardboard scraping, a ramp banging. Precise "
            "lip sync. Sentences are three or four words because that is all the air anyone has"
        ),
        "dien": (
            "Big Ray has moved this exact sofa before and says so once; Jonesy is confidently "
            "wrong about angles and always says it will fit; Tam does the math and is always "
            "right; Mr. Diggs is the customer, supervises, and packed nothing"
        ),
        "hai": (
            "Comedy of physics against confidence. The object does not care what anyone believes "
            "about it. Status is who is holding the heavy end — whoever is carrying more has less "
            "say, which is exactly backwards. Escalate through commitment: the more turns the "
            "sofa has already made, the more impossible it is to admit it will not fit. The "
            "reversal is usually that the obvious easy solution was available at the start and "
            "somebody mentioned it."
        ),
        "dao_cu": (
            "a sofa that will not turn the corner",
            "a roll of packing tape with no end",
            "the dolly",
            "a box labeled MISC",
            "furniture pads",
            "the truck ramp",
            "a door taken off its hinges",
            "a mattress with no handles",
            "the elevator that is out of service",
            "a box of dishes packed wrong",
            "the parking cone somebody moved",
            "a mirror wrapped in a blanket",
            "the ratchet strap",
            "a fish tank still full",
            "the box spring",
            "a shelf with the screws missing",
            "a lamp with no shade",
            "the storage unit padlock",
            "a box that says FRAGILE on every side",
            "the door frame measurement",
            "a plant nobody wants to carry",
            "the last trip up",
            "a pizza ordered for the crew",
            "the tip envelope",
        ),
        "mach": (
            "American moving-day friction blown one size too big: an item that will not fit "
            "through a door it came in through, a customer who packed nothing, a parking spot "
            "lost to a neighbor, an elevator out of service on the day. One confident measurement "
            "escalates and lands on a reversal where the easy answer was said out loud in the "
            "first ten seconds and ignored."
        ),
    },

    "THE SALON": {
        "ten": "THE SALON",
        "mo_ta": (
            "Hài tiệm tóc Mỹ — cái ghế, tấm gương, và những chuyện người ta chỉ kể khi đang bị "
            "cắt tóc."
        ),
        "ty_le": "9:16",
        "nhan_vat": {
            "Roxie": (
                "Roxie: 48-year-old woman, platinum blonde with dark roots on purpose, black smock "
                "over a leopard blouse, black jeans, heeled boots; owns the chair by the window, "
                "deadpan, knows everyone's business."
            ),
            "Junie": (
                "Junie: 23-year-old woman, box-dyed teal bob, black smock, ripped jeans, chunky "
                "sneakers; new stylist, anxious, checks the color chart twice."
            ),
            "Dominic": (
                "Dominic: 39-year-old man, slicked dark hair, black smock over a fitted tee, black "
                "trousers, leather shoes; confidently wrong, insists every client wants a change."
            ),
            "Miss Pearl": (
                "Miss Pearl: 74-year-old woman, tight silver curls, purple cardigan, floral dress, "
                "orthopedic shoes; same appointment every Thursday for thirty years, unbothered."
            ),
        },
        "nha": (
            "Roxie's, a small storefront salon on a main street: three stations along a mirrored "
            "wall, two shampoo bowls at the back, a black-and-white checkered floor. Keep the "
            "exact same layout, colors, fixtures and camera geography in every episode. Never "
            "redesign or recolor the salon."
        ),
        "phong": {
            "styling chair": (
                "Styling Chair: a black hydraulic chair facing a wall mirror, a station counter of "
                "bottles and brushes, a hair dryer on a hook."
            ),
            "shampoo bowl": (
                "Shampoo Bowl: a reclined black chair at a white basin, a sprayer on a coiled hose, a "
                "folded towel on the edge."
            ),
            "waiting bench": (
                "Waiting Bench: a padded bench along the window, a low table of curled magazines, a "
                "coat hook rail above."
            ),
            "color station": (
                "Color Station: a narrow counter of tint bowls and brushes, a wall of numbered tubes, "
                "a timer stuck to the mirror."
            ),
            "back room": (
                "Back Room: a washer and dryer stacked, shelves of towels, a mop in a bucket, a small "
                "window high on the wall."
            ),
            "front desk": (
                "Front Desk: a wooden counter with a card reader, an appointment book, a jar of hair "
                "ties, a bell."
            ),
            "sidewalk": (
                "Sidewalk: pavement outside the glass storefront, a folding sandwich board sign, a "
                "bench, a parking meter."
            ),
        },
        "style": (
            "Warm bulb light bouncing off mirrors — every shot has a reflection in it, which "
            "doubles the cast and lets a reaction happen behind someone's back. Palette is "
            "checkered black and white floor, salon-chair black, and one hot magenta accent. "
            "Clean medium line, rounded furniture shapes, and the specific shine of a mirror "
            "drawn as two flat highlights.. hand-drawn 2D animation on twos, held key poses with "
            "snappy transitions between them, tapered ink line that thickens on the shadow side, "
            "appealing readable silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Warm, confiding American voices for {vai} pitched over a hair dryer. Scissors, a "
            "spray bottle, a dryer switching off mid-sentence. Precise lip sync. Everything "
            "important is said to a mirror, not to a face"
        ),
        "dien": (
            "Roxie owns the window chair and knows everyone's business; Junie is new and checks "
            "the color chart twice; Dominic insists every client secretly wants a change; Miss "
            "Pearl has had the same appointment for thirty years and is unbothered"
        ),
        "hai": (
            "Comedy of the captive conversation. The client cannot leave, cannot see properly, "
            "and has handed over control of their own head. Status is who is holding the scissors "
            "— total power, zero authority. Escalate through the haircut itself: every attempt to "
            "fix it removes another option. Never let anyone panic on camera; the mirror does the "
            "reacting. The reversal is usually that the client wanted the accident."
        ),
        "dao_cu": (
            "a photo on a phone of a haircut",
            "the color chart",
            "a timer stuck to the mirror",
            "the appointment book",
            "a cape with a stuck snap",
            "the spray bottle",
            "a hair dryer on a hook",
            "the tip jar",
            "a tube of the wrong number",
            "the shampoo sprayer",
            "a broken chair pump",
            "the broom",
            "a stack of towels still damp",
            "the front door bell",
            "a magazine from 2019",
            "the card reader",
            "a pair of clippers with no guard",
            "the mirror with a chip in the corner",
            "a bottle with the label worn off",
            "the folding sandwich board",
            "a coat left on the hook",
            "the parking meter",
            "a bobby pin on the floor",
            "the closing-time sign",
        ),
        "mach": (
            "American salon friction blown one size too big: a photo that does not match the head "
            "it is held next to, a color that develops wrong, a walk-in during a booked hour, a "
            "client who asks for a trim and means a transformation. One small misunderstanding "
            "escalates in the mirror and lands on a reversal where the mistake is exactly what "
            "somebody wanted."
        ),
    },

    "TAILGATE": {
        "ten": "TAILGATE",
        "mo_ta": (
            "Hài bãi xe trước trận Mỹ — bốn tiếng nướng thịt, một cái ghế gấp, và luật bất thành "
            "văn của cả bãi."
        ),
        "ty_le": "9:16",
        "nhan_vat": {
            "Bull": (
                "Bull: 50-year-old man, heavy build, team jersey over a long-sleeve tee, cargo "
                "shorts, sneakers; confidently wrong about grilling, owns the canopy."
            ),
            "Shell": (
                "Shell: 43-year-old woman, curly hair under a team cap, hoodie, jeans, boots; dry, "
                "brought everything everyone forgot."
            ),
            "Boz": (
                "Boz: 28-year-old man, face paint in team colors, sleeveless jersey, athletic shorts, "
                "high-tops; fast and literal, has a superstition for everything."
            ),
            "Pops": (
                "Pops: 66-year-old man, grey stubble, weathered team jacket, work trousers, worn "
                "boots; has had this same parking spot for twenty-two years, deadpan."
            ),
        },
        "nha": (
            "Lot C outside a stadium, four hours before kickoff: rows of painted parking lines, a "
            "low chain-link fence at the edge, the stadium rim visible above the treeline. Keep "
            "the exact same layout, colors, landmarks and camera geography in every episode. "
            "Never redesign or recolor the lot."
        ),
        "phong": {
            "the spot": (
                "The Spot: two parking spaces with a folding canopy over them, a grill on the "
                "asphalt, four folding chairs in a rough circle."
            ),
            "tailgate": (
                "Tailgate: the open back of a pickup truck, a cooler on the bed, a folded blanket, "
                "the tailgate down as a table."
            ),
            "cornhole lane": (
                "Cornhole Lane: two angled boards facing each other on the asphalt, bean bags "
                "scattered, a chalk line between them."
            ),
            "grill zone": (
                "Grill Zone: a small charcoal grill on a stand, a bag of briquettes leaning, a "
                "folding table of trays and tongs."
            ),
            "porta line": (
                "Porta Line: three portable toilets against the fence, a hand-wash station, a line of "
                "people that never gets shorter."
            ),
            "fence edge": (
                "Fence Edge: chain-link at the lot boundary, weeds along the base, the stadium "
                "visible past a row of trees."
            ),
            "shuttle stop": (
                "Shuttle Stop: a painted curb with a sign on a post, a metal barricade, a bench with "
                "one slat missing."
            ),
        },
        "style": (
            "Late-afternoon sun low across an open parking lot — long raking shadows from every "
            "canopy and chair, and hard warm light on one side of every face. Palette is asphalt "
            "grey, team colors used as the only saturation, and charcoal smoke drawn as three "
            "flat shapes, never as haze. Bold line, wide open composition with lots of sky.. "
            "hand-drawn 2D animation on twos, held key poses with snappy transitions between "
            "them, tapered ink line that thickens on the shadow side, appealing readable "
            "silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Loud, cheerful, overlapping American voices for {vai} outdoors. A distant PA, a car "
            "radio, a bean bag hitting wood. Precise lip sync. Everything is said louder than it "
            "needs to be because the lot is big and open"
        ),
        "dien": (
            "Bull is confidently wrong about grilling and owns the canopy; Shell brought "
            "everything everyone else forgot; Boz has a superstition for every situation; Pops "
            "has had this exact parking spot for twenty-two years"
        ),
        "hai": (
            "Comedy of the tradition nobody can explain. Every rule of the lot is sacred, "
            "arbitrary, and enforced with total seriousness. Status is how many seasons you have "
            "parked here. Escalate through preparation — the more elaborate the setup, the more "
            "catastrophic one missing item becomes. Nobody may admit the ritual is silly, "
            "including when it clearly is. The reversal is usually that the superstition worked."
        ),
        "dao_cu": (
            "a bag of charcoal",
            "the folding chair with the broken arm",
            "a cooler with no ice",
            "the canopy leg that will not lock",
            "a bean bag",
            "the propane tank",
            "a lucky jersey",
            "the tailgate speaker",
            "a package of buns nobody brought",
            "the tongs",
            "a folding table leg",
            "the parking pass on the dashboard",
            "a bottle opener on a keychain",
            "the trash bag",
            "a portable radio",
            "the extension cord to nowhere",
            "a foil tray",
            "the meat thermometer",
            "a chair claiming a spot",
            "the shuttle schedule",
            "a cornhole board with a warped slat",
            "the ice run",
            "a phone at four percent",
            "the ticket in somebody else's pocket",
        ),
        "mach": (
            "American tailgate friction blown one size too big: a grill that will not light, a "
            "spot somebody else parked in, an item everyone assumed somebody else brought, a "
            "ritual performed in the wrong order. One small breach of lot tradition escalates and "
            "lands on a reversal where the superstition turns out to have been load-bearing."
        ),
    },

    "BAGGAGE CLAIM": {
        "ten": "BAGGAGE CLAIM",
        "mo_ta": (
            "Hài sân bay Mỹ — cửa ra tàu bay và băng chuyền hành lý, nơi ai cũng mệt và không ai "
            "nhường."
        ),
        "ty_le": "9:16",
        "nhan_vat": {
            "Renata": (
                "Renata: 40-year-old woman, dark hair in a tight bun, navy gate-agent blazer, grey "
                "skirt, low heels; unshockable, has said every sentence before."
            ),
            "Wes": (
                "Wes: 33-year-old man, short red hair, orange high-vis vest over a grey uniform "
                "shirt, work trousers, boots; ramp crew, dry, knows where the bag actually is."
            ),
            "Bitsy": (
                "Bitsy: 62-year-old woman, silver pixie cut, quilted travel jacket, wide trousers, "
                "comfortable shoes; a passenger, confidently wrong, has flown this route since 1987."
            ),
            "Trev": (
                "Trev: 25-year-old man, headset around his neck, navy vest over a white shirt, dark "
                "trousers, sneakers; new gate agent, anxious, reads the policy aloud."
            ),
        },
        "nha": (
            "Gate 14 and the adjoining baggage hall of a mid-size American airport: grey carpet "
            "in the gate area, polished concrete at the carousel, a wall of tall windows onto the "
            "apron. Keep the exact same layout, colors, fixtures and camera geography in every "
            "episode. Never redesign or recolor the terminal."
        ),
        "phong": {
            "gate 14": (
                "Gate 14: rows of linked blue seats, a podium with a monitor, a jet bridge door, a "
                "departure board on the wall."
            ),
            "carousel": (
                "Carousel: an oval metal belt on polished concrete, a rubber curtain where bags "
                "emerge, a stack of loose luggage carts."
            ),
            "jet bridge": (
                "Jet Bridge: a narrow enclosed ramp with ribbed walls, one small window, a folded "
                "wheelchair against the side."
            ),
            "ramp": (
                "Ramp: open apron concrete under the aircraft wing, a baggage cart train, orange "
                "cones, a belt loader."
            ),
            "oversize": (
                "Oversize: a separate roller counter beside the carousel, a strollers-and-skis rack, "
                "a scuffed floor scale."
            ),
            "lost luggage": (
                "Lost Luggage: a small office counter with a monitor, shelves of unclaimed bags "
                "behind, a wall of tags."
            ),
            "moving walkway": (
                "Moving Walkway: a rubber belt between two rails down a long corridor, a repeating "
                "overhead sign, tall windows on one side."
            ),
        },
        "style": (
            "The specific flat grey light of a terminal — no shadow, no time of day, everything "
            "lit from an invisible ceiling. Palette is airline navy, high-vis orange on the ramp "
            "crew, and the washed neutral of carpet and concrete. Thin clean line, strong "
            "repeating verticals from window mullions and seat rows, so one thing out of "
            "alignment reads instantly.. hand-drawn 2D animation on twos, held key poses with "
            "snappy transitions between them, tapered ink line that thickens on the shadow side, "
            "appealing readable silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Calm, professionally level American voices for {vai}. A PA chime, rolling suitcase "
            "wheels, the rumble of a carousel starting. Precise lip sync. Nobody raises their "
            "voice, which makes the smallest sharpness enormous"
        ),
        "dien": (
            "Renata is unshockable and has said every sentence before; Wes is ramp crew and knows "
            "where the bag actually is; Bitsy is confidently wrong and has flown this route since "
            "1987; Trev is new and reads the policy aloud"
        ),
        "hai": (
            "Comedy of the system that cannot be argued with. Everyone is tired, the rules are "
            "real, and no amount of being right changes anything. Status is who has information — "
            "the ramp crew outranks the gate agent who outranks the passenger, regardless of "
            "uniform. Escalate through waiting and through announcements that contradict each "
            "other. The reversal is usually that the bag, the seat or the answer was two feet "
            "away the entire time."
        ),
        "dao_cu": (
            "a bag that looks exactly like everyone else's",
            "the boarding pass on a cracked phone screen",
            "a gate change on the monitor",
            "the sizer frame for carry-ons",
            "a stroller at the jet bridge",
            "the podium microphone",
            "a luggage tag torn half off",
            "the standby list",
            "a seat-back pocket item",
            "the belt loader",
            "a wheelchair nobody requested",
            "the departure board",
            "a suitcase with a broken wheel",
            "the oversize counter scale",
            "a boarding group number",
            "the rubber curtain on the carousel",
            "an overhead bin that is full",
            "the delay announcement",
            "a passport left at security",
            "the moving walkway",
            "a bag of duty-free",
            "the unclaimed bag shelf",
            "a connection with nineteen minutes",
            "the last carousel bag going around alone",
        ),
        "mach": (
            "American airport friction blown one size too big: a gate change announced twice, a "
            "bag that is identical to four other bags, a policy that contradicts the sign above "
            "it, a connection that is technically possible. One small procedural conflict "
            "escalates and lands on a reversal where the thing everyone was looking for was in "
            "plain view."
        ),
    },

    "THE CAMPGROUND": {
        "ten": "THE CAMPGROUND",
        "mo_ta": (
            "Hài khu cắm trại Mỹ — lều, xe RV, và một cái bãi đất mà ai cũng nghĩ là của mình."
        ),
        "ty_le": "9:16",
        "nhan_vat": {
            "Chip": (
                "Chip: 46-year-old man, sunburned, wide-brim hat, khaki fishing shirt, cargo shorts, "
                "hiking sandals with socks; confidently wrong about the outdoors, owns every gadget."
            ),
            "Marguerite": (
                "Marguerite: 52-year-old woman, grey braid, flannel over a tank top, jeans, worn "
                "hiking boots; dry, does this every year, needs almost nothing."
            ),
            "Wendell": (
                "Wendell: 20-year-old man, beanie, oversized hoodie, joggers, unlaced trainers; fast "
                "and literal, has never been outside overnight before."
            ),
            "Ranger Faye": (
                "Ranger Faye: 57-year-old woman, grey hair under a flat-brim ranger hat, olive "
                "uniform shirt, dark trousers, boots; deadpan, has told everyone this already."
            ),
        },
        "nha": (
            "Loop B of a state-park campground: gravel spurs off a one-way loop road, numbered "
            "wooden site posts, tall pines closing in on all sides. Keep the exact same layout, "
            "colors, landmarks and camera geography in every episode. Never redesign or recolor "
            "the campground."
        ),
        "phong": {
            "site 12": (
                "Site 12: a gravel pad with a fire ring, a weathered picnic table, a numbered wooden "
                "post, a tent pitched slightly crooked."
            ),
            "fire ring": (
                "Fire Ring: a blackened metal ring on dirt, a grate on one side, three folding chairs "
                "pulled close, split logs stacked nearby."
            ),
            "bathhouse": (
                "Bathhouse: a small cinderblock building with two doors, a bare bulb over each, a "
                "hose bib on the outside wall."
            ),
            "dump station": (
                "Dump Station: a concrete pad with a capped inlet, a hose reel on a post, a faded "
                "sign of instructions."
            ),
            "camp store": (
                "Camp Store: a small wooden building with a screen door, a shelf of firewood bundles, "
                "an ice chest, a bulletin board."
            ),
            "lake dock": (
                "Lake Dock: weathered planks out over still water, a cleat at the end, one aluminium "
                "boat tied up, reeds along the bank."
            ),
            "trailhead": (
                "Trailhead: a gravel opening in the treeline, a wooden map board under a shingle "
                "roof, a boot brush station."
            ),
        },
        "style": (
            "Deep pine shade with hard shafts of sun coming through in straight beams — the whole "
            "frame is dark green except where light lands, which makes any bright object a "
            "subject. Palette is forest green, tent nylon in loud primaries, and campfire orange. "
            "Medium line, organic irregular shapes for nature against perfectly rectangular human "
            "gear, which is the joke drawn into the style itself.. hand-drawn 2D animation on "
            "twos, held key poses with snappy transitions between them, tapered ink line that "
            "thickens on the shadow side, appealing readable silhouettes, generous squash and "
            "stretch on the face only"
        ),
        "audio": (
            "Outdoor American voices for {vai} that carry further than intended — nothing is "
            "private in a campground. Crickets, a zipper, a fire popping, a distant generator. "
            "Precise lip sync. Every conversation is overheard by the next site"
        ),
        "dien": (
            "Chip is confidently wrong about the outdoors and owns every gadget; Marguerite does "
            "this every year and needs almost nothing; Wendell has never been outside overnight; "
            "Ranger Faye has told everyone this already and says it once more"
        ),
        "hai": (
            "Comedy of gear against nature. The person with the most equipment is the least "
            "prepared, and the person with a pocket knife is fine. Status is how little you need. "
            "Escalate through the gear itself — each gadget deployed to fix the last gadget. "
            "Sound carries, so private arguments have an audience nobody acknowledges. The "
            "reversal is usually that the ranger already said this at check-in and nobody "
            "listened."
        ),
        "dao_cu": (
            "a tent pole that does not match",
            "the firewood bundle",
            "a cooler left open",
            "the camp stove that will not light",
            "a bear box",
            "the air mattress with a slow leak",
            "a lantern with dead batteries",
            "the site number post",
            "a bag of marshmallows",
            "the generator two sites over",
            "a folding table",
            "the hose bib at the bathhouse",
            "a map of the trails",
            "the quiet hours sign",
            "a tarp strung wrong",
            "the fire ring grate",
            "a pair of socks drying on a line",
            "the trash bag hung in a tree",
            "a camp chair in a puddle",
            "the reservation printout",
            "a raccoon-proof latch",
            "the dump station hose",
            "a phone with no signal",
            "the last dry match",
        ),
        "mach": (
            "American campground friction blown one size too big: a site somebody else is set up "
            "on, a generator running past quiet hours, gear that fails in the exact way the "
            "instructions warned about, an animal that has done this before. One small outdoor "
            "problem escalates through equipment and lands on a reversal where the simplest "
            "option was always there."
        ),
    },

    "THE LAUNDROMAT": {
        "ten": "THE LAUNDROMAT",
        "mo_ta": (
            "Hài tiệm giặt tự động Mỹ — ba mươi phút chờ, một máy hỏng, và luật ngầm về việc động "
            "vào đồ người khác."
        ),
        "ty_le": "9:16",
        "nhan_vat": {
            "Yolanda": (
                "Yolanda: 55-year-old woman, hair wrapped in a bright scarf, denim jacket over a work "
                "polo, leggings, slip-on shoes; deadpan, runs the place without owning it."
            ),
            "Deshawn": (
                "Deshawn: 31-year-old man, tall and thin, hoodie with the strings pulled uneven, "
                "sweatpants, slides with socks; confidently wrong about machine settings."
            ),
            "Winnie": (
                "Winnie: 68-year-old woman, tight grey perm, floral housecoat over slacks, "
                "comfortable shoes; has a folding system and will explain it."
            ),
            "Kade": (
                "Kade: 22-year-old man, headphones around his neck, band tee, cuffed jeans, canvas "
                "shoes; anxious, first time doing his own laundry."
            ),
        },
        "nha": (
            "Sudz-N-Suds, a storefront laundromat on a corner: two long rows of front-load "
            "washers facing dryers, a folding counter down the middle, fluorescent tubes overhead "
            "and a big window onto the street. Keep the exact same layout, colors, machines and "
            "camera geography in every episode. Never redesign or recolor the laundromat."
        ),
        "phong": {
            "washer row": (
                "Washer Row: a long bank of front-load washers with round glass doors, a wheeled cart "
                "at the end, a taped OUT OF ORDER sign on one."
            ),
            "dryer wall": (
                "Dryer Wall: a stacked wall of dryers with round doors, a bench in front, lint trays "
                "hanging open."
            ),
            "folding counter": (
                "Folding Counter: a long laminate table down the middle, a stack of empty baskets "
                "underneath, a fluorescent tube directly above."
            ),
            "change machine": (
                "Change Machine: a steel box on the wall with a coin tray, a handwritten sign taped "
                "beside it, a small trash can below."
            ),
            "back corner": (
                "Back Corner: a soap vending machine, a mop and bucket, a stack of broken carts, a "
                "door marked EMPLOYEES."
            ),
            "window seats": (
                "Window Seats: three plastic chairs against the front glass, a low table with a "
                "curled magazine, the street outside."
            ),
            "sidewalk": (
                "Sidewalk: pavement outside the corner storefront, a newspaper box, a bus stop sign, "
                "a dryer vent breathing warm air."
            ),
        },
        "style": (
            "Flat fluorescent light on white machines — the whole frame is white and chrome with "
            "the laundry itself supplying every color, so a pile of clothes is the only saturated "
            "thing in shot. Palette is machine white, coin-slot steel, and one acid yellow on the "
            "signage. Clean thin line, strict grid of circular doors, which makes a single open "
            "door a focal point.. hand-drawn 2D animation on twos, held key poses with snappy "
            "transitions between them, tapered ink line that thickens on the shadow side, "
            "appealing readable silhouettes, generous squash and stretch on the face only"
        ),
        "audio": (
            "Voices for {vai} pitched over machine noise, then suddenly too loud when a cycle "
            "ends. Tumbling dryers, coins dropping, a buzzer. Precise lip sync. Conversations "
            "happen in the gaps between cycles"
        ),
        "dien": (
            "Yolanda runs the place without owning it and says one thing per scene; Deshawn is "
            "confidently wrong about settings; Winnie has a folding system and will explain it; "
            "Kade is doing his own laundry for the first time"
        ),
        "hai": (
            "Comedy of shared property and unwritten law. Touching someone else's laundry is a "
            "moral event. Everyone is trapped for a fixed number of minutes with strangers and "
            "nothing to do. Status is who understands the machines. Escalate through the timer — "
            "the cycle is a clock nobody can stop, and every problem must be solved before it "
            "ends. The reversal is usually that the machine everyone avoided was the working one."
        ),
        "dao_cu": (
            "a machine with an OUT OF ORDER sign",
            "the change machine",
            "a single red sock",
            "the last working dryer",
            "a laundry cart with a bad wheel",
            "the soap vending machine",
            "somebody's clothes left in a washer",
            "a quarter jammed in the slot",
            "the lint tray",
            "a folded pile nobody claimed",
            "the cycle timer",
            "a bottle of detergent with no cap",
            "the bench in front of the dryers",
            "a dryer sheet stuck to a shirt",
            "the mop bucket",
            "a handwritten sign taped to the wall",
            "an empty basket",
            "the door that will not latch",
            "a bus schedule",
            "the vending snack machine",
            "a shirt on a hanger",
            "the wet floor by the door",
            "a phone charging behind the counter",
            "the last quarter",
        ),
        "mach": (
            "American laundromat friction blown one size too big: a machine that eats money, "
            "clothes left too long in the only free washer, a setting somebody changed, a cycle "
            "that ends at the worst moment. One small breach of laundromat etiquette escalates "
            "against a running timer and lands on a reversal where the avoided machine was fine "
            "all along."
        ),
    },
}


def _lich(kenh: str, so: int) -> dict:
    """Cấp cho tập số `so` một bộ SÁU TRỤC phân biệt: phòng · đồ vật · áp lực · kiểu mở ·
    ai gây ra · ai lật. Giữ nguyên khoá tạo hình — chỉ tình huống đổi.

    VÌ SAO KHÔNG DÙNG MODULO TỪNG TRỤC
    ----------------------------------
    Cách hiển nhiên là `chỉ_số_trục_i = so % độ_dài_i`. Nó sai theo một kiểu rất khó thấy: bộ
    sáu trục lặp lại sau `lcm(các độ dài)` tập, chứ không phải sau `tích` các độ dài. Với
    HOUSE RULES: tích = 7.372.800 nhưng lcm(8,20,10,16,24,12) = **240**. Tức lịch chỉ đi qua
    240 trong 7,3 triệu tổ hợp rồi quay lại từ đầu — trần đa dạng to mà lịch không với tới.
    Đây đúng họ lỗi "vá một nhánh, để nguyên nhánh song song": mỗi trục nhìn riêng thì đều
    trải hết, mà bộ sáu thì không.

    Cách đúng: đánh số THẲNG trên không gian tích, rồi bước bằng một số nguyên tố cùng nhau với
    tích ấy. Bước như thế đi qua **đúng một lần** mọi tổ hợp trước khi lặp — và vì bước rất lớn,
    hai tập liền nhau rơi vào hai góc xa nhau của không gian, không phải hai ô cạnh nhau.
    """
    hs = ho_so(kenh)
    phong = list(hs["phong"])
    do = list(hs.get("dao_cu") or ["an ordinary object"])
    vai = list(hs["vai"])
    # 1/9 — THÊM TRỤC THỨ BẢY: cơ chế cú lật. Đo trên lượt sinh thật, đây là chỗ mất điểm lớn
    # nhất và lặp lại nhiều nhất: "Cú lật — cơ chế mới, không lặp kho = 5/10 (họ =
    # nhấc-lộ-vô-hại)". Đề bài cấp phòng · đồ vật · áp lực · kiểu mở · ai gây · ai lật, nhưng
    # KHÔNG cấp cách lật — nên chỗ duy nhất còn để AI tự quyết lại đúng là chỗ nó lười nhất.
    # Dặn "đừng lặp" đã thử ở phòng và người lật, không ăn thua; cấp theo lịch thì ăn thua.
    ho_ten = list(HO_LAT)
    truc = _do_truc(hs)
    P = 1
    for x in truc:
        P *= x
    # Bước lớn, lẻ, không chia hết cho 3 hay 5 -> nguyên tố cùng nhau với mọi tích ở đây (các
    # tích chỉ có thừa số 2, 3, 5 và các số nhỏ). Kiểm bằng gcd cho chắc, đừng tin lý lẽ suông.
    n = (_goc_lich(kenh) % P + so * _buoc_lich(kenh)) % P

    ra, chi = [], n
    for x in truc:
        ra.append(chi % x)
        chi //= x
    i_ph, i_do, i_ap, i_mo, i_gay, i_lat, i_co = ra
    gay = vai[i_gay]
    con = [v for v in vai if v != gay] or vai
    lat = con[i_lat % len(con)]
    return {"phong": phong[i_ph], "dao_cu": do[i_do], "ap_luc": AP_LUC[i_ap],
            "kieu_mo": KIEU_MO[i_mo], "gay": gay, "lat": lat, "co_che": ho_ten[i_co],
            "_khong_gian": P}


def _do_truc(hs: dict) -> list:
    """Độ dài từng trục của bộ lịch. MỘT nguồn duy nhất.

    1/9 — Danh sách trục từng được viết ra ba nơi: `_lich()`, `_buoc_lich()`, và khối xuất web.
    Thêm trục thứ bảy, tôi sửa hai nơi đầu và quên nơi thứ ba — web tính theo sáu trục, Python
    theo bảy, và 280/280 đề bài lệch ĐÚNG MỘT TRƯỜNG. Sáu trục kia khớp hoàn hảo, nên nhìn
    thoáng qua nó giống "gần đúng" chứ không giống hỏng.
    """
    return [len(hs["phong"]), len(hs.get("dao_cu") or [1]), len(AP_LUC), len(KIEU_MO),
            len(hs["vai"]), max(1, len(hs["vai"]) - 1), len(HO_LAT)]


def _buoc_lich(kenh: str) -> int:
    """Bước đi trong không gian tổ hợp. Phải NGUYÊN TỐ CÙNG NHAU với tích, không thì lịch chỉ
    đi qua một phần không gian rồi lặp — đúng cái bẫy `lcm` đã tránh ở `_lich`."""
    hs = ho_so(kenh)
    P = 1
    for x in _do_truc(hs):
        P *= x
    b = 1_000_003
    while _gcd(b, P) != 1:
        b += 2
    return b


def _goc_lich(kenh: str) -> int:
    """Điểm xuất phát riêng của kênh. `hash()` của Python đổi theo từng lần chạy (PYTHONHASHSEED)
    nên KHÔNG dùng được: web tính ra một số, Python tính ra số khác, hai bên lệch lịch. Dùng phép
    băm cố định, viết ra để cả hai bên chạy y hệt."""
    h = 0
    for c in kenh:
        h = (h * 131 + ord(c)) % 1_000_000_007
    return h


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def ho_so(kenh: str) -> dict:
    k = KENH.get(kenh.upper().strip())
    if not k:
        raise SystemExit(f"❌ chưa có kênh {kenh!r}. Đang có: {', '.join(KENH)}")
    # `vai` suy từ khoá của `nhan_vat` chứ không chép tay: hai danh sách viết ở hai nơi thì sớm
    # muộn lệch nhau, và lúc lệch thì thước lại chê đúng nhân vật của kênh là "ngoài dàn".
    k.setdefault("vai", list(k["nhan_vat"]))
    return k


# ── KHỐI CHUYÊN SÂU: TỪ KỊCH BẢN RA HÌNH ẢNH ────────────────────────────────────────────────
# 30/8 — Anh yêu cầu prompt 2.500–3.000 từ và "từ kịch bản tới hình ảnh". Bản cũ ra 436 từ: nó
# nói ĐIỀU GÌ xảy ra (thoại, cú lật) nhưng gần như không nói TRÔNG NHƯ THẾ NÀO. Phần thiếu ấy
# chính là phần Kling tự bịa — và tự bịa là nguồn gốc của mọi tập trông khác nhau.
#
# Bảy khối dưới đây là những quyết định mà một đoàn phim thật phải chốt trước khi bấm máy: cỡ
# cảnh, hướng sáng, bảng màu, nhịp diễn, biểu cảm, tiếng động, và luật nối cảnh. Viết chúng ra
# không phải để prompt dài cho đủ chỉ tiêu — mà vì mỗi câu bỏ trống là một chỗ máy tự quyết.

def _cu_may(n: list, g: float) -> list[str]:
    """Danh sách cú máy theo từng khối thời gian — cỡ cảnh, chuyển động, lý do."""
    # Cỡ cảnh đi theo NGHĨA của khối, không theo trang trí: hook cần rộng để đọc ra bối cảnh
    # trong một nhịp; phần dựng dùng cú trung để thấy cả người lẫn tay; cú chốt vào cận vì cái
    # cười nằm trên khuôn mặt. Đây là cách phim hài truyền hình Mỹ dựng suốt sáu mươi năm.
    ban = {
        "hook":     ("wide establishing shot", "locked-off, no camera move",
                     "the viewer must read the room and the problem within one beat"),
        "setup":    ("medium two-shot", "very slow push-in, barely perceptible",
                     "both characters and their hands stay visible while the situation builds"),
        "escalate": ("medium close-up on the reacting character", "static, cut on the beat",
                     "the second laugh comes from a face, not from more words"),
        "payoff":   ("close-up on the character who loses", "locked-off, hold to the last frame",
                     "the punchline lands on an expression; a moving camera steals it"),
    }
    ra = ["CAMERA AND COVERAGE:"]
    ra.append(f"Total {g} seconds, {len(n)} shots. One cut per block, never inside a block. "
              "Cut on the accent of a line, never mid-word.")
    for a, b, ten in n:
        co, dong, vi = ban[ten]
        ra.append(f"{a:.1f}–{b:.1f}s ({ten}): {co}; {dong}; {vi}.")
    ra.append("Stay on ONE side of the line between the two characters for the whole clip "
              "(the 180-degree rule): the character on the left stays on the left in every "
              "shot. Crossing it makes the viewer lose their bearings even if they cannot say why.")
    ra.append("Never cut on a joint: no framing that slices a character exactly at the neck, "
              "elbow, wrist, waist or knee. Frame just above or just below the joint.")
    ra.append("Eye level with the characters. No drone shots, no crane moves, no orbiting, "
              "no dolly zoom, no handheld shake, no rack focus.")
    return ra


def _anh_sang(hs: dict, phong: str) -> list[str]:
    return [
        "LIGHTING:",
        f"Single dominant soft key light coming from the practical light source already inside "
        f"the {phong} (window, ceiling fixture or lamp), plus a soft ambient fill so no face "
        f"falls into black. Warm key around 4800K, cool fill.",
        "Shadows are soft-edged and flat-shaded — one shadow tone per surface, no gradients, "
        "no ambient occlusion smudges, no rim light halo.",
        "Faces stay the brightest thing in frame at all times. Never let the background out-"
        "contrast a face; the eye must go to the person, not to the furniture.",
        "Lighting direction, intensity and color stay IDENTICAL for every shot in the clip and "
        "across every episode of this channel. Do not relight between cuts.",
    ]


def _mau(hs: dict) -> list[str]:
    return [
        "COLOR:",
        "Flat cel colors with hard edges. No gradients on characters, no textured brush strokes, "
        "no painterly rendering, no photographic detail.",
        "Characters read against the background through VALUE, not through outline weight: "
        "keep the background one clear step lighter or darker than the clothing.",
        "The color of every character's clothing is locked and never shifts hue between shots, "
        "even when the lighting of the scene changes.",
        "Keep the palette limited: roughly six background colors and the locked character colors. "
        "A crowded palette reads as cheap even when every element is drawn well.",
    ]


def _dien_xuat(tap: dict, hs: dict) -> list[str]:
    ra = ["FACIAL ACTING AND BODY:",
          "Faces carry the comedy. Every line needs a visible change on the face BEFORE the "
          "words start — the thought lands first, the sentence follows.",
          "Eyebrows and mouth do most of the work; eyes stay large and readable. Blink on the "
          "beat between lines, never during a line.",
          "Anticipation before every large movement: a small opposite motion first (lean back "
          "before stepping forward). Movement without anticipation reads as a glitch.",
          "One character moves at a time. When one speaks, the other listens VISIBLY — reacting "
          "stillness, not frozen stillness.",
          "Hands are readable: fingers separated, gestures inside the chest box, never crossing "
          "the face, never leaving frame.",
          "No floating: feet stay planted on the floor with visible contact and weight. If a "
          "character shifts weight, the whole body follows, not just the legs."]
    for ln in (tap.get("lines") or [])[:6]:
        if isinstance(ln, dict) and ln.get("who"):
            ra.append(f"{ln['who']} {ln.get('act') or 'says'} the line — hold the reaction on the "
                      f"listener for a beat after it ends.")
    return ra


def _tieng_dong(n: list, hs: dict, phong: str) -> list[str]:
    ra = ["SOUND DESIGN:",
          f"Room tone of a real {phong} under everything, quiet and continuous.",
          "Native spoken audio, natural American English, conversational pace, no narrator, "
          "no voice-over, no music bed under the dialogue.",
          "Diegetic sound only — every sound has a visible cause on screen."]
    for a, b, ten in n:
        if ten == "hook":
            ra.append(f"{a:.1f}–{b:.1f}s: one specific object sound that explains the situation "
                      f"before anybody speaks (a door, a fridge, a chair, a dropped item).")
        elif ten == "payoff":
            ra.append(f"{a:.1f}–{b:.1f}s: silence for a fraction of a second before the last "
                      f"line, then the single sound that seals the joke. Silence is the setup.")
    ra.append("No laugh track, no cartoon boings, no whooshes, no stingers, no rimshot.")
    return ra


def _hook(tap: dict, n: list) -> list[str]:
    a, b, _ = n[0]
    return [
        "HOOK ENGINEERING (the first seconds decide everything):",
        f"The hook occupies {a:.1f}–{b:.1f}s and must work with the SOUND OFF. A viewer scrolling "
        f"decides in under a second, and most of them decide while muted.",
        "Open ON the problem, not on the way to the problem. No establishing walk-ins, no door "
        "opening, no character arriving: the situation is already wrong when the clip starts.",
        "Something visually strange must be present in the very first frame — an object where it "
        "should not be, a face already reacting, a posture that does not fit the room.",
        "No title card, no logo, no on-screen text, no countdown, no fade in. The first frame is "
        "already the film.",
        f"Frame the hook so the strange thing sits in the upper two thirds of the vertical frame: "
        f"the bottom of a 9:16 short is covered by the interface on most phones.",
    ]


def _noi_canh(hs: dict) -> list[str]:
    return [
        "CONTINUITY AND CONSISTENCY:",
        "Same character designs, same proportions, same clothing, same colors in every shot and "
        "in every episode. A character does not change height, weight, hair or wardrobe between "
        "cuts.",
        "Same room, same furniture positions, same wall colors as previous episodes of this "
        "channel. The audience should recognise the place instantly.",
        "Screen direction is consistent: whoever looks right in the first shot keeps looking "
        "right. Eyelines must match across a cut — if A looks at B, B looks back on the opposite "
        "diagonal.",
        "Props persist: an object placed in the hook is still there, in the same place, at the "
        "payoff, unless a character visibly moves it.",
    ]


def _cam(hs: dict) -> list[str]:
    return [
        "DO NOT:",
        "No text of any kind on screen — no subtitles, captions, titles, watermarks, signatures, "
        "logos, UI, or written signs with legible words.",
        "No extra people, no background crowd, no pets that were not listed, no reflections "
        "showing anyone who is not in the cast.",
        "No photorealism, no 3D render look, no anime style, no imitation of any existing studio, "
        "series or franchise. Original designs only.",
        "No extra fingers, no melted hands, no duplicated limbs, no faces changing mid-shot, no "
        "eyes drifting apart, no mouth moving without sound.",
        "No slow motion, no speed ramps, no time lapse, no split screen, no picture-in-picture.",
        "No sudden style change halfway through the clip. The last frame must look like it came "
        "from the same production as the first.",
    ]


def _nghe_hoat_hinh() -> list[str]:
    """Nguyên lý hoạt hình cổ điển, viết ra thành lệnh — đây là phần tách 'động đậy' khỏi 'diễn'."""
    return [
        "ANIMATION CRAFT:",
        "Timing carries the joke. Fast moves for panic and surprise, slow moves for confidence "
        "and denial. A character who is wrong moves slowly and certainly; a character who has "
        "just realised something moves fast.",
        "Every action has three parts: anticipation, action, settle. Skipping the settle is what "
        "makes cheap animation look like a slideshow.",
        "Hold poses. A clear pose held for a beat reads better than constant motion — the eye "
        "needs a still frame to read an expression. Never let everything move at once.",
        "Arcs, not straight lines: hands, heads and bodies travel along curves. Straight-line "
        "motion reads as mechanical.",
        "Overlapping action: hair, loose clothing and held objects settle a fraction AFTER the "
        "body stops, never at the same instant.",
        "Squash and stretch stays subtle — this is a sitcom, not a rubber-hose cartoon. Faces "
        "may compress on a hard reaction; bodies keep their volume.",
        "Weight is visible: heavier characters take longer to start and longer to stop. Nobody "
        "glides, nobody teleports between poses.",
        "Secondary characters keep a small idle life — breathing, a slow blink, a shift of "
        "weight. Frozen background characters kill the shot instantly.",
    ]


def _dan_dung(n: list, hs: dict) -> list[str]:
    """Dàn cảnh: ai đứng đâu trong khung, ở từng khối."""
    ra = ["BLOCKING (where people stand in frame):",
          "Vertical 9:16 framing: characters occupy the middle band of the frame. Heads sit in "
          "the upper third, feet stay visible or are cropped well below the knee — never cropped "
          "at the ankle.",
          "Two characters are staged at slightly different depths, never shoulder to shoulder on "
          "a flat line. The speaking character is closer to camera or better lit.",
          "Leave clean headroom: never let a head touch the top edge, never let a raised hand "
          "leave the frame.",
          "Nobody stands dead centre for the whole clip; nobody stands against the frame edge."]
    for a, b, ten in n:
        if ten == "hook":
            ra.append(f"{a:.1f}–{b:.1f}s: stage the strange object or the wrong situation clearly "
                      f"in the upper two thirds, unobstructed by any body.")
        elif ten == "payoff":
            ra.append(f"{a:.1f}–{b:.1f}s: the losing character is the largest thing in frame. "
                      f"Everything else falls away.")
    return ra


def _thoai_nhip(tap: dict, g: float) -> list[str]:
    ra = ["DIALOGUE DELIVERY:",
          "Natural conversational American English. Contractions, not formal grammar. Nobody "
          "announces the joke; nobody explains what just happened.",
          "One clear beat of silence between lines — overlapping dialogue destroys lip sync and "
          "destroys comic timing at the same time.",
          "The last line is the shortest line. A punchline that runs long is a punchline that "
          "already died.",
          "Stress falls on the ONE word that carries the surprise; the rest of the line is flat "
          "and casual by comparison.",
          "Lip movement matches the spoken audio exactly. No mouth movement during silence, no "
          "silent mouthing, no talking while the face is turned away from camera."]
    for ln in (tap.get("lines") or [])[:6]:
        if isinstance(ln, dict) and ln.get("say"):
            ra.append(f'"{ln["say"]}" — spoken by {ln.get("who")}, on camera, mouth visible.')
    return ra


def _viral_usa(n: list, g: float) -> list[str]:
    """Chuẩn giữ chân người xem của short Mỹ — viết thành ràng buộc hình, không phải lời khuyên."""
    a, b, _ = n[0]
    return [
        "US SHORT-FORM RETENTION STANDARD:",
        f"This is a {g}-second vertical short for a US audience. The entire clip must be "
        f"understandable by someone who has never seen this channel before, with no context and "
        f"no prior episode.",
        f"Zero dead frames. Every one of the {g} seconds shows either a new piece of information "
        f"or a reaction to one. There is no room for a character walking across a room.",
        "The situation is universal and instantly legible: food, money, chores, being late, "
        "being caught, being wrong in front of someone. No niche references, no wordplay that "
        "needs explaining, no cultural in-jokes.",
        "The clip must end ON the punchline, not after it. No goodbye, no wave, no fade, no "
        "settling shot. The last frame is the funniest frame.",
        "It must loop cleanly: the final frame should sit comfortably next to the first frame if "
        "the video replays immediately, with no jarring change in framing or brightness.",
        "Emotion reads at thumbnail size. If the key expression is not legible when the frame is "
        "shrunk to the size of a fingernail, it is not strong enough.",
    ]


def _thanh_chat_luong(hs: dict, g: float) -> list[str]:
    """Thanh chất lượng — bản kiểm cuối, viết dưới dạng câu hỏi kiểm được, không phải khẩu hiệu."""
    return [
        "QUALITY BAR — the render is only acceptable if ALL of these are true:",
        "1. Every character looks identical to their locked description, in every single frame.",
        "2. Hands are correct: five fingers, no fusion, no extra limbs, no hands passing through "
        "objects or bodies.",
        "3. Faces stay stable — no drifting eyes, no shifting jawline, no changing age, no "
        "changing hair between cuts.",
        "4. Feet make contact with the floor; nobody floats, nobody sinks into the ground.",
        "5. The room is the same room in every shot: same furniture, same positions, same colors.",
        "6. No text anywhere in frame, including on props, walls, screens and packaging.",
        "7. Lip movement matches spoken words; no mouth moves in silence.",
        f"8. The clip is exactly {g} seconds, vertical {hs['ty_le']}, and ends on the punchline.",
        "9. Lighting and color grade are identical from the first frame to the last.",
        "10. A viewer with the sound off understands the situation from the first second.",
    ]


def _trang_phuc(hs: dict, comat: list) -> list[str]:
    """Nhắc lại trang phục dưới dạng RÀNG BUỘC, không phải mô tả.

    Khối CHARACTER LOCK ở đầu prompt tả nhân vật một lần. Nhưng Kling đọc prompt như một khối
    văn xuôi và trọng số giảm dần về cuối — nên thứ cần giữ nguyên suốt clip phải được nhắc
    lại gần chỗ nó bị vi phạm. Đây không phải lặp thừa: lặp có chủ đích là cách ghim.
    """
    ra = ["WARDROBE AND PROPS:",
          "Clothing is a uniform, not an outfit: each character wears the exact same garments, "
          "in the exact same colors, in every episode. Nobody changes clothes, rolls a sleeve, "
          "removes a hat, or gains an accessory that is not in their locked description.",
          "No logos, no brand marks, no printed words, no numbers on any garment or object.",
          "Props are simple, chunky, and readable in silhouette. A prop that needs a close-up to "
          "identify is the wrong prop for a vertical short.",
          "Any object a character holds stays the same size and color the whole clip, and stays "
          "in their hand until they visibly put it down."]
    for t in comat[:5]:
        mo = hs["nhan_vat"].get(t)
        if mo:
            ra.append(f"{mo.split(';')[0].strip()} — unchanged in every frame.")
    return ra


def _luat_the_gioi(hs: dict) -> list[str]:
    return [
        "WORLD RULES:",
        "This world obeys ordinary physics. Nothing floats, nothing teleports, nothing changes "
        "size. The comedy comes from people, not from magic.",
        "The absurdity lives in the SITUATION and in how people react to it, never in the "
        "rendering. Keep the drawing honest and let the behaviour be ridiculous.",
        "Animals behave like animals — expressive faces are allowed, speech and human posture "
        "are not, unless the locked character description says otherwise.",
        "No breaking the fourth wall: nobody looks into the lens, nobody addresses the viewer.",
        "Scale is consistent: doorways, furniture and props stay in believable proportion to the "
        "characters in every shot.",
    ]


def _khung_mau(tap: dict, n: list, hs: dict) -> list[str]:
    """Storyboard bằng chữ — tả thẳng ba khung hình chủ chốt như một hoạ sĩ phân cảnh sẽ vẽ.

    Đây là khối gần nhất với thứ anh gọi là "từ kịch bản tới hình ảnh". Phần TIMING nói CHUYỆN
    GÌ xảy ra; khối này nói KHUNG HÌNH TRÔNG RA SAO ở đúng ba thời điểm quyết định — khung đầu
    tiên (giữ chân), khung giữa (dựng), khung cuối (chốt). Ba khung ấy là ba thứ người xem thật
    sự nhớ, và là ba thứ Kling hay tự bịa nhất nếu không ai tả.
    """
    g = _gop(tap, n)
    dau, cuoi = n[0], n[-1]
    ra = ["KEY FRAMES (describe these exact images):",
          f"FIRST FRAME at 0.0s — {g.get('hook', '')} Wide, locked-off, whole room readable. The "
          f"odd element sits in the upper two thirds, nothing blocking it. Faces already carry an "
          f"expression; nobody is neutral, nobody is walking in.",
          ]
    giua = g.get("setup") or g.get("payoff") or ""
    ra.append(f"MIDDLE FRAME at {dau[1]:.1f}s — {giua} Medium two-shot, both characters and both "
              f"pairs of hands visible, staged at slightly different depths, eyelines meeting.")
    ra.append(f"LAST FRAME at {cuoi[1]:.1f}s — {g.get('payoff', '')} Close-up on the character "
              f"who loses; their expression fills the frame and reads at thumbnail size. Hold "
              f"this image to the final frame with no camera move and no fade.")
    ra.append("These three images define the clip. Everything between them is the shortest, "
              "clearest path from one to the next.")
    return ra


# ── DỰNG NHỊP THEO SỐ GIÂY ANH CHỌN ─────────────────────────────────────────────────────────
def nhip(giay: float) -> list[tuple[float, float, str]]:
    """Các khối thời gian cho clip dài `giay` — SỐ KHỐI THEO ĐỘ DÀI, không cố định bốn.

    30/8 — Bản cũ chia mọi độ dài thành đúng bốn khối theo tỉ lệ cố định. Ở clip 5 giây, hook
    được 0,9 giây và escalate được 1,3 giây: không đủ cho một cú máy, chứ đừng nói một nhịp
    diễn. Bốn khối trong năm giây không phải kịch bản chặt, nó là kịch bản vụn.

    Phim ngắn thật rút gọn CẤU TRÚC chứ không nén nhịp:
      ≤ 6,5s  — hai khối: một cú hook, một cú chốt. Đây là dạng "một trò đùa, một cú đấm".
      ≤ 9,5s  — ba khối: thêm chỗ dựng tình huống trước khi chốt.
      ≥ 10s   — bốn khối: có chỗ cho leo thang, tức có chỗ cho tiếng cười thứ hai.
    """
    g = float(giay)
    if g <= 6.5:
        ty = (("hook", 0.34), ("payoff", 0.66))
    elif g <= 9.5:
        ty = (("hook", 0.22), ("setup", 0.46), ("payoff", 0.32))
    else:
        ty = (("hook", MOC[0]), ("setup", MOC[1] - MOC[0]),
              ("escalate", MOC[2] - MOC[1]), ("payoff", 1 - MOC[2]))
    ra: list[tuple[float, float, str]] = []
    t = 0.0
    for ten, ph in ty:
        h = round(t + g * ph, 1)
        ra.append((round(t, 1), h, ten))
        t = h
    ra[-1] = (ra[-1][0], round(g, 1), ra[-1][2])   # khối cuối chạm đúng mép, không hụt vì làm tròn
    return ra


def _gop(tap: dict, n: list) -> dict:
    """Ghép bốn phần AI viết vào đúng số khối mà độ dài này có — KHÔNG bỏ rơi phần nào.

    AI luôn viết đủ bốn phần (hook/setup/escalate/payoff) vì đó là cách nghĩ một mẩu hài. Nhưng
    clip 5 giây chỉ có hai khối. Nếu cứ in theo chỉ số thì `escalate` biến mất khỏi prompt —
    mất luôn nhịp gài mà cú chốt dựa vào, và cú chốt hoá ra vô duyên. Nên gộp, không cắt.
    """
    ten = [x[2] for x in n]
    lay = lambda k: str(tap.get(k) or "").strip()
    if "setup" not in ten:            # hai khối: dồn cả phần dựng và leo thang vào cú chốt
        return {"hook": lay("hook"),
                "payoff": " ".join(x for x in (lay("setup"), lay("escalate"), lay("payoff")) if x)}
    if "escalate" not in ten:         # ba khối: leo thang nhập vào phần dựng
        return {"hook": lay("hook"),
                "setup": " ".join(x for x in (lay("setup"), lay("escalate")) if x),
                "payoff": lay("payoff")}
    return {k: lay(k) for k in ten}


def _giay_thoai(giay: float) -> float:
    """Thời gian thực sự có thoại = mọi khối TRỪ hook, và trừ đuôi payoff giữ mặt phản ứng.

    Hook là hình thuần — nó phải bắt mắt trong một nhịp, và một câu thoại ở đó chỉ làm chậm.
    Đuôi payoff để yên cho khuôn mặt phản ứng: cú chốt nằm ở cái mặt, không nằm ở chữ.
    """
    n = nhip(giay)
    co = sum(b - a for a, b, t in n if t != "hook")
    duoi = next((b - a for a, b, t in n if t == "payoff"), 0.0) * 0.22
    return max(1.0, co - duoi)


# ── THƯỚC CHẤM KỊCH BẢN ─────────────────────────────────────────────────────────────────────
def don(d: dict, kenh: str = "") -> dict:
    """Sửa những lỗi máy sửa được, tại chỗ, trước khi đưa qua thước."""
    if not isinstance(d, dict):
        return d

    # ── TÊN VAI VIẾT TẮT -> TÊN ĐẦY ĐỦ ─────────────────────────────────────────────────────
    # 1/9 — Đo trên lượt sinh thật: AI viết `who: "Nick"` cho vai tên "Chef Nick", và thước chặn
    # với lý do "nhân vật không có trong dàn khoá". Về mặt luật thì đúng, nhưng nó đốt một vòng
    # viết lại cho một thứ MÁY SỬA ĐƯỢC — mà mỗi vòng là một lượt gọi AI và một chỗ trong hạn
    # mức. Cùng lý lẽ với việc tự thêm dấu chấm câu: lỗi máy sửa được thì máy sửa.
    # Chỉ nhận khi khớp DUY NHẤT: "Joe" ra "Grandpa Joe" thì được, nhưng nếu kênh có hai vai
    # cùng chứa "Joe" thì để nguyên cho thước chặn — đoán bừa còn tệ hơn chặn.
    if kenh:
        try:
            vai = ho_so(kenh)["vai"]
        except Exception:
            vai = []
        for ln in (d.get("lines") or []):
            if not isinstance(ln, dict):
                continue
            w = str(ln.get("who") or "").strip()
            if w and w not in vai:
                hop = [v for v in vai if w and (w in v.split() or v.split()[-1] == w)]
                if len(hop) == 1:
                    ln["who"] = hop[0]
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
            d[k] = _mao_tu(" ".join(str(d[k]).split()).strip())
    return d


def _mao_tu(t: str) -> str:
    """`a avalanche` -> `an avalanche`. Kling không quan tâm, người xem đọc phụ đề thì có."""
    t = re.sub(r"\ba (?=[aeiouAEIOU])", "an ", t)
    return re.sub(r"\ban (?=[bcdfgjklmnpqrstvwxyz])", "a ", t)


def _tu_chinh(cum: str) -> list[str]:
    """Từ mang nghĩa trong một cụm đồ vật — bỏ mạo từ và giới từ, giữ danh từ."""
    bo = {"the", "a", "an", "of", "in", "on", "with", "that", "one", "some", "and", "for",
          "somebody", "someone", "nobody", "last", "good", "shared"}
    return [w for w in re.findall(r"[a-z]{3,}", cum.lower()) if w not in bo]


def cham(d: dict, kenh: str, giay: float, so: int = -1) -> list[str]:
    """Chấm một tập theo đúng giới hạn Kling. Trả danh sách lỗi để bắt AI viết lại."""
    e: list[str] = []
    if not isinstance(d, dict):
        return ["không phải JSON object"]
    hs = ho_so(kenh)
    vai = set(hs["vai"])

    lines = d.get("lines")
    if not isinstance(lines, list) or not lines:
        return ["thiếu mảng lines (các lượt thoại)"]

    # "Lượt thoại" = lượt CÓ LỜI. Một lượt chỉ có hành động (Buddy stares) không tốn ngân sách
    # từ, không tốn khớp miệng, không phải một lượt cắt cảnh — đếm nó vào là chặn oan.
    # 1/9 — Python đếm cả lượt câm còn web chỉ đếm lượt có lời: cùng một kịch bản, hai kết quả.
    # Hai thước lệch nhau ở một định nghĩa là cách chắc chắn để một bên cho qua thứ bên kia chặn.
    lines = [l for l in lines if isinstance(l, dict)]
    co_loi = [l for l in lines if str(l.get("say") or "").strip()]

    if len(co_loi) > LUOT_TOI_DA:
        e.append(f"{len(co_loi)} lượt thoại — quá {LUOT_TOI_DA} thì cắt cảnh liên tục, mặt méo")

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

    # ── KHUÔN KỂ PHẢI KHỚP THỜI LƯỢNG ──────────────────────────────────────────────────────
    # Không co giãn một kịch bản: năm giây và mười lăm giây là hai LOẠI chuyện khác nhau.
    _ten_kh, _ = khuon_ke(giay)
    _esc = str(d.get("escalate") or "")

    # ── `beat` PHẢI CÓ THẬT, VÀ KHÔNG ĐƯỢC LÀ `hook` ───────────────────────────────────────
    # 1/9 — Hai lỗ cùng một chỗ, cả hai đều lọt cổng mà vẫn sai:
    #   · AI bịa tên nhịp ("intro"/"climax"/"outro"). `_thoai_theo_nhip` đẩy chúng về khối mặc
    #     định nên prompt vẫn đúng — nhưng cổng "rải đều các nhịp" ĐẾM chúng là ba nhịp khác
    #     nhau và cho qua, trong khi thực tế cả ba lời dồn vào một khối.
    #   · AI đặt lời vào nhịp `hook`. `_giay_thoai()` cố ý TRỪ hook ra khỏi thời gian có thoại
    #     (hook là hình thuần, một câu ở đó chỉ làm chậm) — nên ngân sách từ được tính như thể
    #     khối ấy im lặng, còn prompt thì có lời. Clip vượt ngân sách mà thước báo sạch.
    _khoi = [x[2] for x in nhip(giay)]
    for i, ln in enumerate(lines, 1):
        if not isinstance(ln, dict):
            continue
        b = str(ln.get("beat") or "").strip()
        if not b:
            continue
        if b not in _khoi:
            e.append(f"lượt {i}: beat {b!r} không có trong clip {giay:g}s — chỉ có "
                     f"{', '.join(_khoi)}")
        elif b == "hook":
            e.append(f"lượt {i}: đặt lời vào nhịp 'hook' — khung mở là HÌNH thuần, một câu "
                     f"thoại ở đó vừa làm chậm vừa phá ngân sách từ của cả tập")
    if giay <= 6.5:
        if len(co_loi) != 2:
            e.append(f"{len(co_loi)} lượt thoại cho clip {giay:g}s — khuôn {_ten_kh} cần ĐÚNG MỘT "
                     f"lượt trao đổi: hai câu, câu sau ngắn hơn câu trước")
        if len(_esc) > 90:
            e.append(f"'escalate' dài {len(_esc)} ký tự — ở {giay:g} giây nó không phải một nhịp "
                     f"chuyện, chỉ là nửa giây vật lý giữa hình và cú lật. Một mệnh đề ngắn")
        if not re.search(r"\b(falls?|opens?|tips?|swings?|drops?|shuts?|slides?|steps?|turns?|"
                         r"collapses?|lands?|rolls?|pulls?|walks?|leaves?)\b", str(d.get("payoff") or ""), re.I):
            e.append(f"cú lật ở {giay:g} giây phải là ĐỔI HÌNH DẠNG hoặc VỊ TRÍ thấy ngay (đổ · "
                     f"mở · lật · bước ra), không phải một thông tin người xem phải nghĩ mới hiểu")
    elif giay <= 9.5:
        if not 2 <= len(co_loi) <= 3:
            e.append(f"{len(co_loi)} lượt thoại cho clip {giay:g}s — khuôn {_ten_kh} hợp với 2–3 "
                     f"lượt: một cái muốn, một cái chặn, rồi để hình chốt")
    else:
        if len(co_loi) < 3:
            e.append(f"chỉ {len(co_loi)} lượt thoại cho clip {giay:g}s — khuôn {_ten_kh} cần 3–4 "
                     f"lượt rải đều các nhịp, không dồn vào khúc giữa")
        if not re.search(r"\b(further|again|another|more|bigger|second|third|harder|deeper|"
                         r"higher|faster|whole|entire|all of|now the|even the|one more|"
                         r"instead of|not enough)\b", _esc, re.I):
            e.append(f"'escalate' không LEO THANG gì đo được — ở {giay:g} giây khúc giữa phải có "
                     f"tiếng cười riêng của nó: nỗ lực sai lầm phải TO HƠN (sâu hơn · thêm một "
                     f"lần · thêm một người · dụng cụ to hơn), không phải tả thêm")
        _b = [str(l.get("beat") or "") for l in co_loi]
        if len(set(x for x in _b if x)) < 2:
            e.append(f"tất cả lượt thoại nằm cùng một nhịp — clip {giay:g}s có "
                     f"{len(nhip(giay))} khối, rải lời ra bằng trường 'beat' "
                     f"({', '.join(x[2] for x in nhip(giay))})")

    # ── THOẠI PHẢI RA GIỌNG MỸ ─────────────────────────────────────────────────────────────
    for ln in lines:
        if not isinstance(ln, dict):
            continue
        say = str(ln.get("say") or "")
        for rx, ly in KHONG_MY:
            if re.search(rx, say, re.I):
                e.append(f"{str(ln.get('who') or '')}: {say!r} — {ly}")
                break

    for khoa in ("hook", "escalate", "payoff"):
        if not str(d.get(khoa) or "").strip():
            e.append(f"thiếu khối {khoa!r}")

    # ── PHẢI CÓ ÍT NHẤT MỘT LƯỢNG CHÍNH XÁC ────────────────────────────────────────────────
    # 1/9 — Đo trên 28 tập AI viết: trục "Cụ thể — số thật" mất 108 điểm ở 18/28 tập, đứng thứ
    # hai trong mọi trục. Luật đã có trong `LUAT_HAI_MY` ("Not 'expensive' but 'nine hundred
    # dollars'") nhưng chỉ được CHẤM, không được CHẶN — nên nó là lời khuyên, và AI bỏ qua lời
    # khuyên. Cùng thứ thuốc đã dùng cho ba cổng kia: đưa vào thước cứng, và nói ra là bị kiểm.
    # `one` KHÔNG tính, và `half`/`twice` cũng không: chúng là từ đệm ("one more time", "one of
    # them", "half the room") chứ không phải một lượng người xem đếm được. Bản đầu nhận chúng
    # nên cổng báo sạch cho đúng những kịch bản mơ hồ mà nó sinh ra để bắt.
    _SO = (SO_CHINH_XAC if True else "")  # noqa — giữ tên rõ ràng ở chỗ dùng

    _ca_so = " ".join(str(d.get(k) or "") for k in ("hook", "setup", "escalate", "payoff")) \
        + " " + " ".join(str((l or {}).get("say") or "") for l in lines)
    if not re.search(_SO, _ca_so, re.I):
        e.append("không có một lượng chính xác nào — cần ít nhất một con số, một khoản tiền, "
                 "một tên thứ trong tuần hay một phép đếm. 'chồng cốc' phải thành 'chín cái "
                 "cốc'; 'đắt' phải thành 'chín trăm đô'")

    hook = str(d.get("hook") or "")
    # Bỏ tiền tố ghim máy trước khi đếm: nó là chỉ thị máy quay, không phải bức tranh.
    _hinh = re.sub(r"^[^:]{0,40}(shot|angle)\s*:\s*", "", hook, flags=re.I)
    # 1/9 — NÂNG SÀN HOOK TỪ 10 LÊN 16 TỪ. Đo 30 tập cũ: trung vị 73 ký tự (~12 từ), tức vừa đủ
    # qua sàn cũ và vừa đủ cụt. "A bulging trash bag teeters on the counter" cho Kling một khung
    # vẽ được, nhưng không cho người xem lý do nào để ở lại giây thứ hai — không biết ai gây ra,
    # không biết sắp hỏng chuyện gì. Sàn mới đòi đủ BA VẾ, và trần 30 từ để nó vẫn là MỘT hình.
    if len(_hinh.split()) < 16:
        e.append(f"hook {len(_hinh.split())} từ (không tính lời ghim máy) — cụt. Phải 16–30 từ và đủ ba vế: vật gì sai · "
                 f"sai chỗ nào · một chi tiết cho thấy CÓ NGƯỜI gây ra. Đây là toàn bộ lý do "
                 f"người xem ở lại giây thứ hai")
    elif len(_hinh.split()) > 30:
        e.append(f"hook {len(_hinh.split())} từ — quá 30 thì không còn là MỘT hình ảnh nữa, "
                 f"Kling phải chọn vẽ cái nào và nó chọn sai")

    # Văn kể dài quá thì prompt không còn chỗ cho hàng rào DO NOT. Chặn ở khâu VIẾT, vì tới khâu
    # ghép thì chỉ còn hai lựa chọn tồi: cắt chuyện, hoặc mất hàng rào.
    for _k, _tr in VAN_KE_CHIA.items():
        if len(str(d.get(_k) or "")) > _tr:
            e.append(f"khối {_k!r} dài {len(str(d[_k]))} ký tự — trần {_tr}. Đây là MỘT câu tả "
                     f"một hình, không phải một đoạn văn")

    # ── ĐO THẲNG PROMPT THẬT, THÔI ĐO GIÁN TIẾP QUA SỐ KÝ TỰ VĂN KỂ ────────────────────────
    # 1/9 — Chỗ này từng là một trần cứng cho tổng văn kể, và em đã đặt nhầm nó bốn lần liên
    # tiếp (800 → 720 → 670 → 640 → 600), lần nào cũng đo ở một ngữ cảnh hơi lệch. Cả bốn lần
    # đều sai theo cùng một kiểu: TRẦN CỨNG là phép đo GIÁN TIẾP.
    #
    # Chỗ tốn ký tự lớn nhất không phải văn kể, mà là SỐ NHÂN VẬT — mỗi vai là ~150 ký tự khoá
    # hình. Một tập hai người có thừa chỗ cho hook 30 từ; một tập bốn người thì không, dù văn
    # kể y hệt. Một con số chung không thể đúng cho cả hai, nên đừng tìm con số ấy nữa.
    #
    # Ghép thử prompt của CHÍNH tập này rồi đo. Chính xác tuyệt đối, và câu báo lỗi nói được
    # cách sửa nào rẻ hơn: bớt một người thường rẻ hơn cắt hook.
    try:
        _p = prompt(kenh, d, giay)
        if len(_p) > KY_TU_MAX or not _p.rstrip().endswith("seconds."):
            _co = len([t for t in hs["vai"] if t in " ".join(str(d.get(k) or "") for k in
                       ("hook", "setup", "escalate", "payoff"))
                       or any(str((l or {}).get("who") or "") == t for l in lines
                              if isinstance(l, dict))])
            e.append(f"prompt ghép ra {len(_p)} ký tự, quá trần {KY_TU_MAX} của Kling — hàng rào "
                     f"DO NOT sẽ bị cắt. Tập này có {_co} nhân vật; bớt một người rẻ hơn cắt "
                     f"hook, vì mỗi vai tốn ~150 ký tự khoá hình")
    except Exception as _ex:
        # Nuốt im lặng ở đây nghĩa là: prompt hỏng -> thước báo SẠCH -> kịch bản hỏng đi tiếp.
        # Một cổng hỏng mà vẫn xanh là dạng tệ nhất (luật 12.8). Báo ra, và coi là lỗi.
        e.append(f"không ghép nổi prompt để đo ({type(_ex).__name__}: {_ex}) — coi như chưa đạt")
    # Bài học 09/08 đã trả giá bên kling_studio: hai thứ Kling trôi mạnh nhất là GÓC MÁY và THỜI
    # ĐẠI. Xin "góc nhìn người đứng dưới đất" mà không ghim thì ra cảnh quay flycam. Luật ấy đã
    # có ở tệp kia; để rơi ở tệp này là học lại một bài đã trả tiền.
    if not any(k in (hook + " " + str(d.get("setup") or "")).lower() for k in GHIM_MAY):
        e.append("không ghim góc máy — thêm 'static eye-level shot' / 'wide shot' / 'low angle' "
                 "vào hook hoặc setup, không thì Kling tự chọn và hay ra cảnh drone")

    pay = str(d.get("payoff") or "").lower()
    # 1/9 — Trước đây chỗ này giữ một danh sách 20 từ khoá riêng ("reveal", "pulls", "lifts"…).
    # Nó vừa lỏng vừa chặt sai chỗ: "Tommy pulls the chair away and the plates settle safely"
    # ĐI QUA (có chữ "pulls") trong khi không có cú lật nào, còn "Buddy walks down the row
    # knocking each tool over" BỊ CHẶN vì không từ nào trong danh sách khớp. Nay hỏi thẳng bảng
    # HO_LAT — cùng bảng mà cổng chống trùng và thang 100 điểm đang dùng.
    if ho_lat(d) == "khác" and not re.search(
            r"\b(reveal\w*|turns? out|was never|all along|instead|behind (him|her|them))\b", pay):
        e.append("payoff không có cú lật — phải ĐẢO tình thế (ai đó bước vào, vật hoá ra là thứ "
                 "khác, thủ phạm lộ diện, hậu quả đuổi kịp), không phải tả thêm cảm xúc")

    # ── NHÂN VẬT NGOÀI DÀN TRONG VĂN KỂ ────────────────────────────────────────────────────
    # 1/9 — Thước chỉ kiểm `who` của từng lượt thoại, nên một cái tên lạ nằm trong VĂN KỂ đi lọt
    # hoàn toàn. Nó nguy hơn tên lạ trong thoại: `_co_mat()` không nhận ra nên không khoá hình
    # người ấy, mà prompt vẫn nhắc tên — Kling tự nghĩ ra một người mới, mỗi tập một kiểu.
    # Quét phần CÒN LẠI sau khi bỏ mọi tên hợp lệ: vai tên hai chữ ("Chef Nick") bị phép quét
    # một-chữ xé đôi và nửa sau thành "người lạ", chặn oan kịch bản đúng.
    _con = " ".join(str(d.get(k) or "") for k in ("hook", "setup", "escalate", "payoff"))
    for _v in sorted(hs["vai"], key=len, reverse=True):
        _con = _con.replace(_v, " ")
    _la = []
    for _c in re.split(r"(?<=[.!?])\s+", _con):
        for _w in re.findall(r"([A-Z][a-z]{2,})", re.sub(r"^\s*\S+\s*", "", _c)):
            if _w not in _la and not any(_w.lower() in p for p in hs["phong"]):
                _la.append(_w)
    if _la:
        e.append(f"tên lạ trong văn kể: {', '.join(_la[:4])} — kênh này chỉ có "
                 f"{', '.join(hs['vai'])}. Kling sẽ vẽ ra người không có trong dàn")

    ca = " ".join(str(d.get(k) or "") for k in ("hook", "setup", "escalate", "payoff")).lower()
    ca += " " + " ".join(str((l or {}).get("say") or "") for l in lines if isinstance(l, dict)).lower()
    for tu, ly in CAM_KY:
        if tu in ca:
            e.append(f"có {tu!r} — {ly}")
            break

    _hinh = " ".join(str(d.get(k) or "") for k in ("hook", "setup", "escalate", "payoff"))
    _m = re.search(CHU_TRONG_KHUNG, _hinh, re.I)
    if _m:
        e.append(f"bắt Kling vẽ CHỮ ĐỌC ĐƯỢC ({_m.group(0).strip()!r}) — đây là chỗ Kling hỏng "
                 f"nặng nhất, nó ra ký tự loằng ngoằng. Thứ trên biển/giấy phải nhận ra bằng "
                 f"HÌNH DẠNG và MÀU, không bằng chữ")
    _m = re.search(KHONG_VE_DUOC, _hinh, re.I)
    if _m:
        e.append(f"dùng chữ không vẽ được ({_m.group(0)!r}) — đó là giải thích cho người đọc, "
                 f"không phải thứ hoạ sĩ phân cảnh vẽ ra được. Tả CÁI THẤY, để người xem tự suy")
    for _i, _l in enumerate(co_loi, 1):
        _s = str(_l.get("say") or "")
        _m = re.search(THOAI_TU_THUAT, _s)
        if _m:
            e.append(f"lượt {_i} ({_l.get('who')}): {_s!r} — lời dẫn đội lốt lời thoại. Người "
                     f"trong phòng không gọi tên nhau trừ khi đang giận, và không ai nói ra "
                     f"chính hành động mình đang làm")
            break

    for _t in (_CAM_TU_LOAT or ()):
        if re.search(r"\b" + re.escape(_t) + r"\w*", ca):
            e.append(f"dùng lại chữ {_t!r} — đã mòn ở các tập trước, đổi hình ảnh khác")
            break
    if "proving" in pay or "was right all along" in pay:
        e.append("payoff đóng bằng khuôn 'proving ... was right' — cú lật phải TỰ nói lên điều "
                 "đó qua hình, không cần câu giải thích ai đúng ai sai")
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

    # Đề bài chỉ là lời khuyên nếu không ai kiểm. AI hay "ghi nhận" đồ vật được cấp rồi viết
    # một chuyện khác — đúng lỗi đã đo ở phòng và người lật trước đây.
    if so >= 0:
        _x = _lich(kenh, so)
        _ca_de = " ".join(str(d.get(k) or "") for k in
                          ("hook", "setup", "escalate", "payoff", "title")).lower()
        _tu = _tu_chinh(_x["dao_cu"])
        if _tu and not any(w in _ca_de for w in _tu):
            e.append(f"không dùng đồ vật được cấp cho tập này ({_x['dao_cu']}) — cả chuyện phải "
                     f"xoay quanh nó, không phải nhắc qua")
        if _x["lat"] not in str(d.get("payoff") or ""):
            e.append(f"cú lật phải do {_x['lat']} thực hiện — payoff không nhắc tới {_x['lat']}")

    # ── CÚ GỌI LẠI KHÔNG ĐƯỢC GIẢI THÍCH MÌNH ──────────────────────────────────────────────
    # 1/9 — Cú gọi lại chỉ có giá trị khi người xem CŨ nhận ra còn người xem MỚI không thấy gì
    # lạ. Câu "remember when…" phá cả hai: người cũ mất phần thưởng vì bị nói toạc, người mới
    # bị nhắc rằng có một tập trước mà mình chưa xem — tức bị đẩy ra. Đây cũng là ranh giới
    # giữa "một chương trình có trí nhớ" và "phần hai của một video khác".
    _NHAC_LO = (r"\b(remember when|last time|as we (saw|know)|like (last|the other) (time|episode)|"
                r"in the last (one|episode)|you (may )?recall|previously|earlier this week|"
                r"same as (last|before)|again like)\b")
    if so >= 0 and goi_lai(kenh, so):
        _ca_g = " ".join(str(d.get(k) or "") for k in ("hook", "setup", "escalate", "payoff")) \
            + " " + " ".join(str((l or {}).get("say") or "") for l in lines)
        if re.search(_NHAC_LO, _ca_g, re.I):
            e.append("cú gọi lại tự giải thích ('remember when' / 'last time') — nó phải là một "
                     "CHI TIẾT bình thường: người xem cũ nhận ra, người xem mới không thấy gì lạ")

    ph = str(d.get("room") or "").strip().lower()
    ta = (hs["phong"].get(ph) or "").lower()
    _phong_ten = ph or ""
    for do in DO_TO:
        # Đồ được coi là CÓ nếu tên nó, hoặc một tên khác của nó, xuất hiện trong mô tả phòng
        # HOẶC trong chính tên phòng.
        _co = (do in ta or do in _phong_ten
               or any(x in ta or x in _phong_ten for x in DONG_NGHIA_DO.get(do, ())))
        if do in ca and not _co:
            e.append(f"nhắc {do!r} — căn nhà không có thứ đó. Chỉ dùng đồ đã tả trong phòng "
                     f"({ph or '?'}), hoặc một món cầm tay nhân vật mang vào.")
            break
    if ph not in hs["phong"]:
        e.append(f"phòng {ph!r} không có trong nhà — chọn một trong: {', '.join(hs['phong'])}")
    return e


# ── GHÉP PROMPT HOÀN CHỈNH ──────────────────────────────────────────────────────────────────
# 1/9 — DỰNG LẠI THEO NGÂN SÁCH, không theo "ghép rồi co".
#
# Bản cũ ghép hết rồi hạ mức chi tiết cho tới khi lọt trần. Nghe hợp lý, nhưng nó cho phép một
# kết cục không được phép xảy ra: mức 3 vẫn tràn thì hàm TRẢ VỀ BẢN TRÀN, và Kling cắt đuôi —
# đuôi là DO NOT. Đo trên 30 tệp đã xuất: cả 30 đều rơi đúng vào kết cục ấy.
#
# Bản này chia ngân sách TRƯỚC. Ba khối không bao giờ nhường chỗ cho ai:
#     CHARACTER LOCK · TIMELINE · DO NOT
# vì chúng quyết định (1) nhân vật có trôi không, (2) chuyện có kể đúng nhịp không, (3) hình có
# thừa ngón/hiện chữ không. Phần TẢ THÊM chỉ tiêu chỗ CÒN LẠI, và tiêu theo thứ tự giá trị —
# hết ngân sách thì khối cuối bảng đơn giản là không được chèn, chứ không bị cắt nửa chừng.
def prompt(kenh: str, tap: dict, giay: float, so: int = 0, bien: int = 1,
           tran: int = KY_TU_MAX, day: bool = False) -> str:
    """Ghép prompt gửi Kling, bảo đảm ≤ `tran` ký tự với hàng rào DO NOT còn nguyên vẹn.

    `day` giữ lại cho tương thích ngược và KHÔNG còn tác dụng: bản "đầy đủ 2.500 từ" sinh ra
    16.834 ký tự, gấp gần bảy lần trần thật của Kling, nên nó không phải một lựa chọn — nó là
    một prompt bị cắt cụt. Mười sáu khối chỉ đạo hình ảnh của bản ấy không mất đi: chúng thành
    KHO TUỲ CHỌN của bộ chia ngân sách dưới đây, và được chèn tới đâu ngân sách cho phép.
    """
    # Chọn mức nén theo GIÁ TRỊ TỔNG, không theo "mức ít nén nhất mà còn lọt trần".
    # 1/9 — Quy tắc tham cũ lấy mức 0 vì nó vừa đủ lọt (2.435/2.500) rồi không còn chỗ cho khối
    # nào — đo được 0/328 khuôn có nổi một khối tả thêm. Một thân nén nhẹ CỘNG bốn khối chỉ đạo
    # đáng giá hơn hẳn một thân đầy đủ đứng trơ. Nên thử cả bốn mức và lấy mức chèn được NHIỀU
    # khối nhất; hoà thì lấy mức ít nén hơn.
    _kho = _kho_tuy_chon(kenh, tap, giay)
    tot, best = -1, None
    for muc in (0, 1, 2, 3):
        bb, rao = _bat_buoc(kenh, tap, giay, so, bien, muc)
        lo, ra = "\n".join(bb), "\n".join(rao)
        if len(lo) + len(ra) + 2 > tran:
            continue
        con, dem = tran - len(lo) - len(ra) - 2, 0
        for kh in _kho:
            t = "\n".join(kh).strip()
            if t and len(t) + 3 <= con:
                dem += 1
                con -= len(t) + 3
        if dem > tot:
            tot, best = dem, (bb, rao, lo, ra)
    if best:
        bb, rao, lo, ra = best
    else:
        bb, rao = _bat_buoc(kenh, tap, giay, so, bien, 3)
        lo, ra = "\n".join(bb), "\n".join(rao)
    # BẢO ĐẢM CỨNG. Mức 3 vẫn tràn nghĩa là kịch bản viết quá dài — `cham()` chặn chuyện đó ở
    # khâu viết. Nhưng nếu một kịch bản cũ lọt qua, KHÔNG được trả về bản tràn: Kling sẽ cắt
    # đuôi và mất hàng rào. Cắt bớt VĂN KỂ ở ranh giới câu, và nói ra là đã cắt.
    if len(lo) + len(ra) + 2 > tran:
        tap = dict(tap)
        for _ in range(40):
            k = max(("hook", "setup", "escalate", "payoff"),
                    key=lambda x: len(str(tap.get(x) or "")))
            cau = re.split(r"(?<=[.!?]) ", str(tap.get(k) or "").strip())
            if len(cau) < 2:
                break
            tap[k] = " ".join(cau[:-1])
            bb, rao = _bat_buoc(kenh, tap, giay, so, bien, 3)
            lo, ra = "\n".join(bb), "\n".join(rao)
            if len(lo) + len(ra) + 2 <= tran:
                break
        sys.stderr.write(f"⚠️  {tap.get('title')!r}: văn kể quá dài, đã cắt bớt câu để giữ hàng "
                         f"rào DO NOT. Viết ngắn lại ở khâu kịch bản.\n")
        lo = lo[:tran - len(ra) - 2]      # chốt chặn cuối cùng, không bao giờ chạm tới trong thực tế
    con = tran - len(lo) - len(ra) - 2
    them: list[str] = []
    for kh in _kho_tuy_chon(kenh, tap, giay):
        t = "\n".join(kh).strip()
        if t and len(t) + 3 <= con:
            them.append(t)
            con -= len(t) + 3
    return lo + "\n" + "".join(x + "\n\n" for x in them) + ra


def _nen_vai(mo: str) -> str:
    """Nén CHARACTER LOCK: giữ phần Kling VẼ ĐƯỢC, bỏ phần Kling không vẽ được.

    "confident, clumsy, optimistic" là TÍNH NẾT — nó thuộc khối PERFORMANCE, không thuộc khối
    khoá hình. Để ở đây tốn ~35 ký tự mỗi vai mà không ghim thêm một pixel nào."""
    return re.split(r";\s*", mo, 1)[0].rstrip(".") + "."


def _nen_phong(ta: str) -> str:
    """Nén SET: giữ ba mốc đầu — ba thứ mắt nhận ra căn phòng ngay."""
    m = ta.split(", ")
    return ", ".join(m[:3]).rstrip(".") + "."


def _co_mat(hs: dict, tap: dict) -> list:
    """Ai THỰC SỰ có mặt trong tập này. Tả người vắng mặt là mời Kling vẽ họ vào khung."""
    ke = " ".join(str(tap.get(k) or "") for k in ("hook", "setup", "escalate", "payoff"))
    ai = [str((l or {}).get("who") or "") for l in (tap.get("lines") or []) if isinstance(l, dict)]
    ra = [t for t in hs["vai"] if t in ke or t in ai]
    return ra or list(hs["nhan_vat"])


def _dien_loc(hs: dict, comat: list) -> str:
    """Chỉ giữ vế chỉ đạo diễn xuất của người CÓ MẶT.

    1/9 — `hs["dien"]` tả cả năm vai. Bản cũ chèn nguyên chuỗi, nên một tập chỉ có Tommy và
    Grandpa Joe vẫn nhắc tên Mike, Lisa và Buddy ngay giữa prompt. KLING_CACH_DUNG.md đã cảnh
    báo đúng cơ chế này cho khối CHARACTER LOCK ("tả Grandpa Joe ở tập không có ông là tự chuốc
    thêm một cụ già đứng thừa ở nền") — chỉ là chưa ai áp luật ấy cho khối PERFORMANCE.
    """
    ve = [v.strip().rstrip(".") for v in str(hs.get("dien") or "").split(";")
          if any(t in v for t in comat)]
    return "; ".join(ve) + "." if ve else ""


def _thoai_theo_nhip(tap: dict, khoi: list[str]) -> dict:
    """Xếp mỗi lượt thoại vào ĐÚNG khối thời gian của nó.

    1/9 — Bản cũ dồn TOÀN BỘ thoại vào một khối (`setup`). Ở clip 10 giây điều đó có nghĩa là
    câu chốt được nói ở giây 5,7 trong khi cú lật xảy ra ở giây 8,2: người xem nghe câu chốt
    trước khi thấy thứ nó chốt, và 4,3 giây cuối không có lời nào. Cả hai đều là lỗi nhịp mà
    không thước nào bắt được, vì thước đo SỐ TỪ chứ không đo CHỖ ĐẶT.

    Lượt nào không ghi `beat` thì về khối mặc định — giữ nguyên hành vi cũ cho kịch bản cũ.
    """
    mac = "setup" if "setup" in khoi else "payoff"
    ra: dict[str, list[str]] = {k: [] for k in khoi}
    for ln in (tap.get("lines") or []):
        if not isinstance(ln, dict):
            continue
        who, say = str(ln.get("who") or ""), str(ln.get("say") or "").strip()
        act = str(ln.get("act") or "").strip() or "says"
        b = str(ln.get("beat") or "")
        b = b if b in khoi else mac
        if say:
            ra[b].append(f'{who} {act}: “{say}”')
        elif act:
            ra[b].append(f"{who} {act}")
    return ra


def _bat_buoc(kenh: str, tap: dict, giay: float, so: int, bien: int,
              muc: int) -> tuple[list[str], list[str]]:
    """Khối KHÔNG BAO GIỜ bị bỏ. Trả (thân, hàng rào) để bộ chia ngân sách giữ hàng rào riêng."""
    hs = ho_so(kenh)
    n = nhip(giay)
    g = f"{giay:g}"
    ten = str(tap.get("title") or "Untitled")
    comat = _co_mat(hs, tap)
    phong = str(tap.get("room") or "").strip().lower()
    if phong not in hs["phong"]:
        phong = next(iter(hs["phong"]))

    r = [f'{hs["ten"]} EP{so:03d} “{ten}” — Variation {bien} — original 2D cartoon, '
         f'vertical {hs["ty_le"]}, exactly {g} seconds.', ""]

    r.append(f"CHARACTER LOCK — identical in every episode of {hs['ten']}, never redesign, "
             f"recolor, age or replace:")
    r += [(hs["nhan_vat"][t] if muc < 1 else _nen_vai(hs["nhan_vat"][t])) for t in comat]
    r.append(f"Only {', '.join(comat)} are in frame. No other people, no background extras.")
    r.append("")

    r.append("LOCATION LOCK — identical in every episode, never rearrange:")
    ta = hs["phong"][phong]
    r.append(ta if muc < 2 else _nen_phong(ta))
    if muc < 1:
        r.append(hs["nha"].split(". ")[0] + ". Never redesign or recolor it.")
    # Danh sách "no pan / no zoom / no drone" đã nằm trong hàng rào — nhắc lại ở đây là 90 ký
    # tự lặp, và 90 ký tự ấy đúng bằng nửa cái hook.
    r.append("Camera locked off at standing eye level, wide.")
    r.append("")

    # VISUAL STYLE LOCK là khối BẮT BUỘC, không phải khối tả thêm.
    # 1/9 — Ban đầu để nó ở kho tuỳ chọn và đo được: 0/328 khuôn web chèn nổi nó, vì thân ăn
    # hết ngân sách trước. Mười kênh vì thế ra cùng một thứ — đúng điều đang phải chữa. Khối
    # này ngang hàng CHARACTER LOCK: một cái giữ nhân vật khỏi trôi, cái kia giữ KÊNH khỏi trôi.
    r.append("VISUAL STYLE LOCK:")
    _st = hs["style"]
    if muc >= 2:                       # bỏ sàn tay nghề dùng chung, giữ nét riêng của kênh
        _st = _st.split(". " + SAN_NGHE)[0]
    if muc >= 3:                       # chỉ còn hai câu đầu — phần nói kênh này TRÔNG ra sao
        _st = ". ".join(_st.split(". ")[:2])
    r.append(_st.rstrip(".") + ".")
    r.append("")

    r.append("TIMING AND STORY:")
    gop = _gop(tap, n)
    tho = _thoai_theo_nhip(tap, [x[2] for x in n])
    for a, b, k in n:
        mo = gop.get(k, "")
        if tho.get(k):
            mo = f"{mo} {' '.join(tho[k])}".strip()
        if k == "payoff":
            # Ở clip hai khối (5–6s) khối này gánh cả dựng lẫn chốt, nên phải nói RÕ cú lật
            # nằm ở đâu trong nó — không thì cú lật trôi ra giữa khối và ba phần tư cuối clip
            # là phần đã hết chuyện. Số đo công bố: phần chốt + phản ứng chiếm 30–40% clip.
            if len(n) <= 2:
                mo += (f" The reversal itself must not begin before {a + (b - a) * 0.62:.1f}s — "
                       f"everything before that is still the situation.")
            mo += " " + CAU_GIU_HINH
        r.append(f"{a:.1f}–{b:.1f}s: {mo.strip()}")
    r.append("")

    # Khối DIALOGUE lặp lại lời thoại đã có trong TIMING. Lặp là CÓ CHỦ Ý — Kling đọc prompt
    # như văn xuôi và trọng số giảm dần, nên lời cần khớp miệng phải được nhắc gần cuối. Nhưng
    # nó là 270 ký tự LẶP: khi ngân sách căng, giữ CHUYỆN quan trọng hơn giữ bản lặp. Vì thế nó
    # nằm ở đầu kho tuỳ chọn, không nằm trong khối bắt buộc.

    # Hàng rào. Giữ riêng vì nó là khối DUY NHẤT mà mất đi thì hình hỏng mà không ai biết.
    rao = ["DO NOT:",
           "No text in frame at all: captions, subtitles, signs, labels, numbers, logos, brand "
           "names, packaging print.",
           "No extra limbs, fused or extra fingers, morphing faces, age drift, clothing change, "
           "floating feet, objects passing through bodies.",
           "No camera move: no pan, zoom, dolly, handheld or drone. No imitation of an existing "
           "show or character. Nobody looks into the lens.",
           CAU_CHOT_RAO.format(g=g)]
    return r, rao


def _kho_tuy_chon(kenh: str, tap: dict, giay: float) -> list[list[str]]:
    """Kho khối TẢ THÊM, xếp theo GIÁ TRỊ giảm dần — bộ chia ngân sách lấy từ trên xuống.

    Thứ tự không tuỳ tiện. Trên cùng là những khối trả lời câu hỏi "Kling sẽ tự bịa gì nếu
    không ai nói?": cách diễn (nó tự cho ai cũng cử động), khuôn hình chốt (nó tự chọn cỡ
    cảnh), nét vẽ (nó trôi về phong cách ảnh chụp). Dưới cùng là những khối dễ chịu nhưng
    không cứu được tập nào nếu thiếu.
    """
    hs = ho_so(kenh)
    n = nhip(giay)
    g = f"{giay:g}"
    comat = _co_mat(hs, tap)
    ph = str(tap.get("room") or next(iter(hs["phong"]), "room")).lower()
    if ph not in hs["phong"]:
        ph = next(iter(hs["phong"]))
    dien = _dien_loc(hs, comat)
    noi = [f'{l["who"]}: “{str(l["say"]).strip()}”' for l in (tap.get("lines") or [])
           if isinstance(l, dict) and str(l.get("say") or "").strip()]
    return [
        (["DIALOGUE — these exact words, natural American English, precise lip sync, mouth "
          "still during silence:"] + noi) if noi else [],
        ["PERFORMANCE:",
         "Play it completely straight — nobody in the scene knows this is funny, nobody performs "
         "the joke. Only one character moves at a time; the others hold a readable pose and "
         "react with the face.",
         dien],
        _khung_mau(tap, n, hs),
        _cu_may(n, g),
        _viral_usa(n, g),
        ["AUDIO STYLE LOCK:",
         hs["audio"].format(vai=", ".join([t for t in comat if t != "Buddy"] or comat))
         + ". No subtitles, no captions, no on-screen text."],
        _anh_sang(hs, ph),
        _mau(hs),
        _tieng_dong(n, hs, ph),
        _trang_phuc(hs, comat),
        _dien_xuat(tap, hs),
        _luat_the_gioi(hs),
        _nghe_hoat_hinh(),
        _noi_canh(hs),
        _thanh_chat_luong(hs, g),
    ]


# ── SINH KỊCH BẢN BẰNG AI ───────────────────────────────────────────────────────────────────
# AI chỉ viết SÁU TRƯỜNG. Nó không thấy, không sửa, không được nhắc lại phần khoá nhân vật —
# đó là toàn bộ lý do dàn diễn viên đứng yên qua hàng trăm tập.
SCHEMA = """Return ONLY a JSON object with exactly these fields:
{
  "title":    "3-5 word episode title, no punctuation",
  "room":     "ROOM_LIST",
  "hook":     "16-30 words. The WRONG-LOOKING IMAGE the viewer sees in the first moment, containing all three of: the wrong object, what is wrong with it, and one detail proving somebody caused it. Pin the camera. A picture a storyboard artist could draw, not a feeling. No dialogue here.",
  "setup":    "one sentence of physical staging: who is where, doing what, camera angle pinned (static eye-level shot / low angle / wide shot)",
  "lines":    [{"who":"Mike","say":"spoken words","act":"says|snaps|whispers|mutters|announces","beat":"which timeline beat this line is spoken in - use one of the beat names listed in THE SHAPE section"}],
  "escalate": "one sentence: the reaction grows, one small physical gag, one beat of silence",
  "payoff":   "one sentence: the REVERSAL, written as a physical action. It is checked for a reversal verb, so it must literally contain one of: reveals, turns out, walks in, steps in, opens, lifts, tips, swings, drops, shuts, slides, knocking, behind him/her/them, was never, all along, already done, instead of. Not just a bigger emotion, and not a line of dialogue explaining who was right."
}"""


# ── RULE MODEL: LUẬT VIẾT HÀI HÌNH MỸ ───────────────────────────────────────────────────────
# 30/8 — Anh dặn "rule model để ép AI viết đúng chuẩn". Chỗ này quan trọng hơn nó trông: bảo AI
# "viết cho hài" thì nó viết ra thứ NHÌN GIỐNG hài — có nhân vật, có câu chốt, có người ngạc
# nhiên — mà không buồn cười. Nó bắt chước HÌNH DẠNG của trò đùa chứ không chạy CƠ CHẾ của trò
# đùa. Muốn nó chạy đúng cơ chế thì phải viết cơ chế ra thành luật kiểm được.
#
# Mười hai luật dưới đây là nguyên lý chung của nghề viết hài tình huống Mỹ — thứ dạy trong lớp
# biên kịch và dùng ở mọi phòng viết, không thuộc về hãng nào và không sao chép của ai. Chúng
# được viết dưới dạng CẤM và PHẢI, vì "nên" thì AI bỏ qua.
LUAT_HAI_MY = [
    "A joke is a broken expectation. Set a pattern, then break it. If nothing was expected, "
    "nothing can be funny — so the first seconds must make the viewer predict something.",
    "Comedy comes from CHARACTER, not from events. The situation must be one that only THIS "
    "person would create, and the punchline must be one that only THIS person could deliver. "
    "If you could swap two characters' lines without loss, the writing has failed.",
    "Every character wants something specific and small, and two of them want incompatible "
    "things. That collision is the engine. No want, no scene.",
    "Play it straight. Nobody in the scene knows they are in a comedy. The moment a character "
    "performs the joke, or reacts as if something was funny, the joke dies.",
    "The calm one is the funny one. Panic is not a punchline; being unbothered next to panic is. "
    "Give the biggest problem to the character least willing to admit it is a problem.",
    "Specific beats general, always. Not 'expensive' but 'nine hundred dollars'. Not 'a while "
    "ago' but 'since Tuesday'. Precision is what makes a lie sound true and a joke sound real.",
    "Escalate, never repeat. Each line must raise the stakes above the previous one. Two lines "
    "at the same level read as padding, and padding is where viewers leave.",
    "Status is the hidden subject: someone is above, someone below, and the payoff flips them. "
    "The person who was certain ends up wrong; the person who was ignored turns out right.",
    "The reversal must be SHOWN, not stated. End on an image or an action, never on a line that "
    "explains who was correct. If the last line summarises, rewrite it.",
    "The last line is the shortest line, and it belongs to whoever has spoken least.",
    "Real families interrupt, understate, and answer a different question than the one asked. "
    "Nobody speaks in complete explanatory sentences. Nobody says the other person's name unless "
    "they are angry.",
    "The viewer must be able to retell the joke in one sentence. If the premise needs setup to "
    "explain, it is the wrong premise for a vertical short.",
]

# Khuôn nhân vật hài Mỹ: mỗi vai xây quanh MỘT khiếm khuyết, và dàn vai là các khiếm khuyết
# KHÁC LOẠI nhau. Đó là lý do một dàn tốt sinh ra đùa mãi không cạn — cùng một tình huống ném
# vào bốn khiếm khuyết khác nhau thì ra bốn phản ứng khác nhau, tức bốn trò đùa khác nhau.
KHUON_VAI = (
    "confidently wrong",       # tin chắc mình đúng, và sai
    "dry and unimpressed",     # tỉnh khô, không bị lay
    "fast and literal",        # nhanh mồm, hiểu theo nghĩa đen
    "anxious over-preparer",   # lo xa, chuẩn bị thừa
    "deadpan veteran",         # từng trải, mặt lạnh
    "silent judge",            # không nói, chỉ nhìn — thường là con vật
)


def _luat_viet() -> str:
    """Luật hài đưa vào lệnh hệ thống cho AI viết kịch bản."""
    return ("RULES OF THE FORM — these are not style notes, they are how the joke works. "
            "A script that breaks any of them is rejected and rewritten:\n"
            + "".join(f"  {i}. {l}\n" for i, l in enumerate(LUAT_HAI_MY, 1)))


def _ngan_sach_sys(kenh: str, giay: float) -> int:
    """Ngân sách văn kể để nói cho AI. Dựng khuôn tạm rồi hỏi `_ngan_sach_khuon` — cùng một
    phép đo với thứ web dùng, nên hai bên không thể lệch."""
    hs = ho_so(kenh)
    ph = max(hs["phong"], key=lambda p: len(hs["phong"][p]))
    mau = {"title": "@@TITLE@@", "room": ph, "hook": "@@HOOK@@", "setup": "@@SETUP@@",
           "escalate": "@@ESCALATE@@", "payoff": "@@PAYOFF@@",
           "lines": [{"who": "@@WHO@@", "act": "says", "say": "@@LINES@@"}]}
    names = ", ".join(hs["vai"])
    def o(t, muc=0):
        cast = "\n".join((hs["nhan_vat"][x] if muc < 1 else _nen_vai(hs["nhan_vat"][x]))
                         for x in hs["vai"])
        return (t.replace(cast, "@@CAST@@").replace(names, "@@CASTNAMES@@")
                 .replace(hs["phong"][ph], "@@ROOMDESC@@").replace(ph, "@@ROOM@@"))
    kh = {"than": [o("\n".join(_bat_buoc(kenh, mau, giay, 0, 1, m)[0]), m) for m in (0, 1, 2, 3)],
          "them": [o("\n".join(x).strip()) for x in _kho_tuy_chon(kenh, mau, giay) if x],
          "rao":  o("\n".join(_bat_buoc(kenh, mau, giay, 0, 1, 0)[1]))}
    return _ngan_sach_khuon(kh, hs, giay, ph)


# Cứ mấy tập thì gọi lại một tập cũ. Bốn: đủ thưa để người xem mới không thấy khó hiểu, đủ dày
# để người xem cũ nhận ra kênh này CÓ TRÍ NHỚ.
NHIP_GOI_LAI = 4


def _tom_lat(payoff: str) -> str:
    """Rút cú lật của một tập cũ thành một mệnh đề ngắn để nhắc lại.

    Nhắc nguyên câu payoff dài 150 ký tự thì cú gọi lại chiếm mất chỗ của chính tập đang viết —
    và ngân sách văn kể chỉ có 640 ký tự."""
    t = " ".join(str(payoff or "").split())
    t = re.split(r"(?<=[.!?]) ", t)[0]
    return (t[:96].rsplit(" ", 1)[0] + "…") if len(t) > 100 else t


def goi_lai(kenh: str, so: int, da: list | None = None) -> dict:
    """Tập này có gọi lại tập cũ nào không, và tập nào.

    VÌ SAO ĐÂY LÀ THỨ ĐÁNG LÀM NHẤT CÒN LẠI
    ---------------------------------------
    Hai lý do, và lý do thứ hai mới là lý do thật.

    1. Luật `inauthentic content` của YouTube không cấm AI và không cấm "trông giống kênh khác" —
       nó nhắm vào *các video của CHÍNH bạn giống hệt nhau, không có bàn tay biên tập*. Một tập
       nhắc tới tập trước là bằng chứng khó cãi nhất rằng đây là **một chương trình**, không phải
       một lô hàng: nó đòi TRẠNG THÁI, mà một dây chuyền sinh hàng loạt thì không có trạng thái.

    2. Quan trọng hơn: nó là thứ duy nhất còn lại có thể nâng **giữ chân** mà không tốn thêm một
       giây Kling nào. Người xem đã xem tập cũ nhận ra cú gọi lại và thấy mình được thưởng; người
       chưa xem vẫn hiểu trọn tập vì cú gọi lại nằm ở CHI TIẾT, không nằm ở tiền đề. Đó chính là
       cơ chế biến người lướt qua thành người đăng ký — và không kênh tự động nào làm được, vì
       nó đòi nhớ mình đã kể gì.

    Ràng buộc cứng: cú gọi lại **không được là tiền đề**. Nếu phải xem tập cũ mới hiểu tập này
    thì tập này hỏng với 95% người xem — đúng luật "hiểu được mà không cần ngữ cảnh".
    """
    if so % NHIP_GOI_LAI or so < NHIP_GOI_LAI:
        return {}
    da = _da_lam(kenh) if da is None else da
    # Tập cũ lưu trước khi có trường `_dao_cu` thì KHÔNG tính lại bằng `_lich`: bộ lịch đã đổi
    # (thêm trục thứ bảy), nên tính lại cho ra một đồ vật KHÁC thứ tập ấy thật sự kể. Dùng thứ
    # tập cũ thật sự có — cú lật của nó. Sai nguồn còn tệ hơn không gọi lại.
    cu = [x for x in da if x.get("title") and (x.get("dao_cu") or x.get("payoff"))]
    if not cu:
        return {}
    # Chọn tập cách đây một khoảng, không phải tập ngay trước: gọi lại tập vừa xong thì giống
    # phần hai hơn là giống trí nhớ. Bước lẻ để không rơi vào cùng một tập mãi.
    return cu[-(1 + (so // NHIP_GOI_LAI * 3) % max(1, len(cu)))]


def de_bai(kenh: str, so: int) -> str:
    """Đề bài của MỘT tập, viết thành câu cho AI. Sáu trục do `_lich` cấp.

    1/9 — Trước đây AI chỉ được cấp phòng và (đôi khi) người lật; đồ vật, áp lực và kiểu mở đều
    để nó tự nghĩ. Nó nghĩ ra cùng một thứ — đo được 16/30 tập cùng một cơ chế cú lật và 22/30
    hook mở bằng chữ "A". Cách chữa không phải dặn "đừng lặp" (đã dặn, không ăn thua) mà là
    CẤP THEO LỊCH: mỗi tập nhận sẵn một bộ sáu trục chưa dùng.
    """
    x = _lich(kenh, so)
    hs = ho_so(kenh)
    # Liệt kê ĐỒ ĐẠC của đúng căn phòng được cấp, ngay trong đề bài.
    # 1/9 — Đo trên 28 tập AI viết: trục "chỉ dùng đồ căn phòng thật có" mất 40 điểm ở 10/28
    # tập, và sau khi ba trục kia được sửa thì nó là thứ DUY NHẤT còn chặn đường tới 95. Lệnh
    # hệ thống có liệt kê cả bảy căn phòng ở phần đầu — nhưng đó là một danh sách dài, đọc từ
    # xa, trong khi đề bài chốt MỘT phòng. AI nhớ căn phòng, quên nội thất của nó.
    _ta = hs["phong"].get(x["phong"], "")
    _do = ", ".join(t.strip() for t in _ta.split(":", 1)[-1].split(",") if t.strip())
    return (
        f"THIS EPISODE'S ASSIGNMENT — build the story around exactly these, do not swap them:\n"
        f"  · ROOM: {x['phong']}. The ONLY fixed objects in it are: {_do}. This is "
        f"machine-checked: naming any other furniture (an island, a staircase, a TV, a sink "
        f"that is not listed) fails the script. A character may CARRY IN a small handheld prop.\n"
        f"  · THE OBJECT this episode is about: {x['dao_cu']}\n"
        f"  · THE PRESSURE that makes it a scene and not just an incident: {x['ap_luc']}\n"
        f"  · THE OPENING IMAGE must be this kind of wrong: {x['kieu_mo']}\n"
        f"  · {x['gay']} caused it (and does not admit it)\n"
        f"  · {x['lat']} delivers the reversal, and delivers it THIS way — not the way that "
        f"comes to mind first: {HO_LAT_TA.get(x['co_che'], x['co_che'])}\n"
        + (lambda g: (
            f"  · CALLBACK — this channel remembers. Somewhere in this episode, refer to what "
            f"happened in the earlier episode \"{g['title']}\" — "
            f"{g['dao_cu'] or _tom_lat(g.get('payoff'))} — in ONE short detail: a "
            f"repaired thing, a rule someone now follows, an object still where it ended up. "
            f"Rules: it must be a DETAIL, never the premise — a first-time viewer must understand "
            f"this episode completely without it. Nobody explains the reference or says 'remember "
            f"when'. A returning viewer notices; a new viewer sees an ordinary detail.\n"
        ) if g else "")(goi_lai(kenh, so))
        + f"These seven are fixed. Everything else — what is wanted, what is said, how it turns — is "
        f"yours to invent, and must be invented fresh: this exact combination has not been used "
        f"before on this channel.\n\n"
    )


def _sys(kenh: str, giay: float, so: int = -1) -> str:
    hs = ho_so(kenh)
    tran = int(_giay_thoai(giay) * TU_MOI_GIAY)
    return (
        f"You write {giay:g}-second vertical cartoon shorts for an American channel called "
        f"{hs['ten']}.\n\n"
        f"THE SHOW: {hs['mo_ta']}\n"
        f"WHAT THIS CHANNEL IS ABOUT: {hs['mach']}\n\n"
        # 1/9 — CƠ CHẾ HÀI RIÊNG CỦA NICHE. Trước đây mười kênh dùng chung một bộ luật hài, nên
        # mười kênh cười theo cùng một kiểu — chỉ đổi bối cảnh. Hài công sở sống bằng thứ KHÔNG
        # ai nói ra; hài quán đêm sống bằng sự mệt mỏi; hài phòng gym sống bằng cái tôi va vào
        # vật lý. Đưa chung một luật cho cả ba là cách chắc chắn để cả ba đều nhạt.
        f"HOW COMEDY WORKS ON THIS CHANNEL — this is the engine, not a mood:\n{hs['hai']}\n\n"
        + (de_bai(kenh, so) if so >= 0 else "")
        # Khuôn kể riêng cho thời lượng này. Đặt NGAY SAU cơ chế hài và TRƯỚC mọi giới hạn con
        # số, vì nó quyết định LOẠI chuyện — còn các con số chỉ quyết định kích thước.
        + f"THE SHAPE OF A {giay:g}-SECOND SHORT — {khuon_ke(giay)[0]}:\n"
        + "".join(f"  · {x}\n" for x in khuon_ke(giay)[1])
        + f"  · The timeline you are writing for has {len(nhip(giay))} beats: "
        + ", ".join(f"{a:.1f}-{b:.1f}s {t}" for a, b, t in nhip(giay)) + ".\n"
        # 1/9 — Bản trước liệt kê cả `hook` là một nhịp hợp lệ rồi để cổng CHẶN mọi lời đặt ở
        # đó. AI làm đúng thứ được bảo và bị phạt: đo được 14 vòng viết lại đốt vào riêng chỗ
        # này. Cổng không sai — lệnh dặn sai, vì nó không nói ra điều cổng đang đòi.
        + f"  · `beat` on a line must be one of: "
        + ", ".join(f"\"{t}\"" for _, _, t in nhip(giay) if t != "hook")
        + ". NEVER \"hook\" — the opening beat is a pure image with no dialogue in it, and a "
        f"line there both slows the open and breaks the word budget for the whole short.\n"
        + f"  · Total spoken words across the whole short: {int(_giay_thoai(giay) * TU_MOI_GIAY)}. "
        f"That is the real constraint on this length — write to it, do not write long and trust "
        f"someone to cut.\n\n"
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
        f"  · never name a real brand or an existing TV show\n"
        + (f"  · 'escalate' MUST contain one of these words, literally: again, another, "
           f"further, more, bigger, deeper, harder, higher, a second, one more, the whole, "
           f"even the, instead of. This is checked; an escalation the reader has to infer "
           f"does not count at this length\n" if giay > 9.5 else "")
        + f"  · the four story fields together must stay under {_ngan_sach_sys(kenh, giay)} characters "
        f"— longer and the render-safety block gets cut off by the model's prompt limit\n\n"
        # 1/9 — CHUẨN HOOK VIẾT RÕ RA. Đo 30 tập cũ: hook trung vị 73 ký tự — "A bulging trash
        # bag teeters on the counter." Đủ để Kling dựng một khung, KHÔNG đủ để người xem hiểu
        # chuyện gì đang xảy ra và vì sao nên xem tiếp. Hook cụt là hook mất người ở giây thứ hai.
        + (f"THIS IS A {giay:g}-SECOND CLIP AND THAT IS A CHOICE, NOT A LIMIT. Every second is "
           f"paid for, so there is no establishing, no walking in, no reaction shot after the "
           f"reaction. The situation must be legible from the first frame and the reversal must "
           f"land while the viewer is still deciding whether to keep watching. Write it as if "
           f"the clip were the last three seconds of a longer joke that the viewer never sees "
           f"the front of — and still understands completely.\n\n" if giay <= 9.5 else "")
        + f"THE HOOK IS THE WHOLE VIDEO — write it to this standard:\n"
        f"  · 16 to 30 words. Shorter than 16 and the viewer cannot tell what they are looking "
        f"at; longer than 30 and it stops being one image.\n"
        f"  · It must contain THREE things: the wrong object, what is wrong with it, and one "
        f"detail that proves somebody caused it. 'A trash bag teeters' has one of the three.\n"
        f"  · It is a PICTURE, not a feeling and not a summary. Write what a storyboard artist "
        f"would draw. No adjectives about mood, no 'chaos', no 'disaster'.\n"
        f"  · Name the wrongness with a concrete word, not by implication. The check looks for "
        f"one of: empty · open · stacked · leaning · spilling · smoking · stuck · missing · "
        f"upside down · backwards · soaked · frozen · melting · tilted · scattered · covered · "
        f"too high · too many. 'A tower of mugs teeters' passes; 'Brad sits on a foam roller' "
        f"does not, because nothing in it is stated as wrong.\n"
        f"  · It must make the viewer ask one specific question that the payoff answers.\n"
        f"  · Pin the camera in it: static eye-level wide shot, or low angle, or medium shot.\n\n"
        f"WHAT MAKES THESE WORK IN AMERICA:\n"
        f"  · The first moment shows something ALREADY WRONG. Do not spend time establishing "
        f"normal. The viewer arrives mid-disaster.\n"
        f"  · American units only, always: miles, mph, pounds, feet, Fahrenheit, dollars. Never "
        f"kilometres, kilos or Celsius — a US viewer stops trusting the channel instantly.\n"
        f"  · Specific beats general, and this is MACHINE-CHECKED: the script must contain at "
        f"least one exact quantity — a number, an amount of money, a day name, or a count. Not "
        f"'the bill is high' but 'nine hundred dollars'. Not 'he is late' but 'since Thursday'. "
        f"Not 'a stack of cups' but 'nine cups'. Precision is what makes a lie sound true and a "
        f"joke sound real, and a short with no number in it reads as a sketch of a joke.\n"
        f"  · The funniest person is the one who is calm. Panic is not a joke; being unbothered "
        f"next to panic is.\n"
        f"  · Vary WHO delivers the reversal across episodes — the cat solving everything twice "
        f"in a row is a formula the viewer spots before the joke.\n"
        f"  · Never end on a line that explains who was right. Show it and stop.\n"
        # 1/9 — Ba cổng nổ nhiều nhất trên lượt sinh thật đều cùng một bệnh: thước tìm một TỪ
        # cụ thể, còn lệnh dặn chỉ nói Ý NGHĨA. AI viết đúng ý mà sai từ, rồi bị bắt viết lại —
        # đo được 49 vòng đốt vào ba cổng ấy. Nói thẳng ra từ mà thước đang tìm thì AI thoả được
        # ngay lượt đầu, và cổng vẫn giữ nguyên độ chặt.
        f"  · 'payoff' is machine-checked for a reversal verb. Write the reversal as a physical "
        f"action containing one of: reveals · turns out · walks in · steps in · opens · lifts · "
        f"tips · swings · drops · slides · knocking · behind him/her/them · was never · all "
        f"along · already done.\n"
        f"  · The last line must REVERSE something, not summarise it. The viewer should want to "
        f"replay the first two seconds to check they missed it.\n"
        f"  · Dialogue is how real Americans actually talk to family: interrupting, understating, "
        f"answering a different question than the one asked.\n\n"
        + _luat_viet()
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


# Khoá đã hỏng CỨNG trong lượt chạy này. `API_KEY_INVALID` thì lần sau vẫn invalid — thử lại
# là ném đi một vòng mạng và một chỗ trong ngân sách vòng lặp.
_KEY_CHET: set = set()


def _sap_ho(ks: list) -> list:
    """Xếp hồ khoá theo thứ tự ĐÁNG THỬ TRƯỚC, bỏ khoá đã hỏng cứng.

    1/9 — Đo trên hồ thật (295 khoá): Cloudflare gọi được ngay (2,5 giây/lượt) · Groq gọi được ·
    Gemini thì 17/40 khoá `API_KEY_INVALID`, 13/40 model đã bị Google gỡ, 10/40 cạn hạn mức.
    `sinh_tap` duyệt hồ theo ĐÚNG thứ tự trong `.keys.local` — Gemini nằm đầu — nên nó đi qua
    hàng trăm khoá chết trước khi chạm khoá sống. Nhìn từ ngoài y hệt "mạng chậm": đúng cái bẫy
    mục 12.1, **chết chậm khó nhận ra hơn chết hẳn**.

    Đường web đã xếp đúng thứ tự này từ trước ("Thử Cloudflare và Groq TRƯỚC"); chỉ đường Python
    là chưa — vá một nhánh, để nguyên nhánh song song.
    """
    ks = [k for k in ks if k and k not in _KEY_CHET]
    cf = [k for k in ks if str(k).startswith("cf:")]
    gq = [k for k in ks if str(k).startswith("gsk_")]
    gm = [k for k in ks if not str(k).startswith(("cf:", "gsk_"))]
    return cf + gq + gm


def sinh_tap(kenh: str, y_tuong: str, giay: float = 8, api_key: str = None,
             tranh: list | None = None, keys: list | None = None, phong: str = "",
             lat: str = "", kieu: str = "", cam_tu: list | None = None,
             so: int = -1) -> dict:
    """Viết một tập. Viết lại tới khi qua hết thước. Trả dict sáu trường.

    Key cạn thì ĐỔI KEY chứ không bỏ cuộc — cùng bài học đã trả giá ở sáu hàm viết bên kia."""
    import content_brain as CB
    _kho_cu = _da_lam(kenh)      # đọc MỘT lần: vòng viết lại có thể chạy tới tám lượt
    ho = ([api_key] if api_key else []) or _sap_ho(_ho_key(keys)) or [None]
    _n = {"i": 0}

    def _model():
        return CB._genai(ho[_n["i"] % len(ho)]).GenerativeModel(
            CB.MODEL, system_instruction=_sys(kenh, giay, so))

    model = _model()
    ne = ("\nDo not repeat these episodes already made: " + " | ".join(list(tranh)[-40:])) if tranh else ""
    if phong:
        ne += (f"\nThis episode MUST take place in the {phong} — not the kitchen, not anywhere "
               f"else. Build the joke out of what is actually in that room.")
    if lat:
        ne += (f"\nThe reversal in the payoff MUST be delivered by {lat} — nobody else. Build "
               f"the ending around what {lat} does.")
    global _CAM_TU_LOAT
    _CAM_TU_LOAT = list(cam_tu or [])
    if kieu:
        ne += (f"\nThe opening image MUST be of this kind: {kieu}. Not a stack about to fall "
               f"unless that is the kind named here.")
    if cam_tu:
        ne += ("\nThese words are worn out from earlier episodes — do not use any of them: "
               + ", ".join(sorted(set(cam_tu))[:24]))
    sch = SCHEMA.replace("ROOM_LIST", phong or " | ".join(ho_so(kenh)["phong"]))
    goc = f'Episode idea: "{y_tuong}".\n\n{sch}{ne}'
    fb, cuoi, _so_biet = "", None, []
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
            # 1/9 — Khoá `API_KEY_INVALID` bị loại HẲN khỏi lượt chạy: nó sẽ invalid ở mọi vòng
            # sau, nên thử lại là ném đi một vòng mạng VÀ một chỗ trong ngân sách vòng lặp. Đo
            # được 17/40 khoá Gemini rơi vào loại này — tức gần một nửa ngân sách vòng lặp bị
            # tiêu cho những khoá không bao giờ chạy được.
            if "api key not valid" in low or "api_key_invalid" in low:
                _KEY_CHET.add(ho[_n["i"] % len(ho)])
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
        d = don(d, kenh)
        if phong:
            d["room"] = phong           # ép cứng: phòng do lịch luân phiên quyết, không do AI
        if lat:
            d["lat"] = lat
        loi = cham(d, kenh, giay, so)
        if lat and lat.split()[0] not in str(d.get("payoff") or ""):
            loi.append(f"cú lật phải do {lat} thực hiện — payoff không nhắc tới {lat}")
        # Trùng NỘI DUNG với bất kỳ tập nào trong TOÀN kho, không chỉ 40 tập gần nhất và không
        # chỉ so tên. Đặt sau `cham` để một tập vừa sai luật vừa trùng thì báo cả hai một lượt.
        _x, _d = trung_voi(d, _kho_cu)
        if _x:
            loi.append(f"trùng {_d:.0%} với tập đã làm {_x!r} — đổi CÚ LẬT, không đổi mỗi cái tên")
        _kt = trung_khuon_ten(d, _kho_cu)
        if _kt:
            loi.append(f"tên theo khuôn đã dùng ({_kt}) — đặt tên theo cách khác hẳn")
        _cc = trung_co_che(d, _kho_cu)
        if _cc:
            loi.append(_cc)
        # THANG 100 ĐIỂM. `cham()` chỉ biết ĐẠT/HỎNG, nên một tập nhạt vẫn "sạch" — đo được:
        # cả 30 tập đã xuất đều sạch thước cũ, và cả 30 đều dưới 90 điểm. Thang này bắt phần
        # `cham()` không được dạy để nhìn: cú lật có mới không, hook có đủ ý không, câu chốt có
        # phải câu ngắn nhất không. Chỉ chạy được khi ghép nổi prompt, nên đặt sau mọi thước kia.
        if not loi:
            try:
                import cham100 as C100
                _diem, _ghi = C100.cham100(d, giay, ho_so(kenh),
                                           prompt(kenh, d, giay, 0), _kho_cu)
                _yeu = [f"{k} = {v}/10" + (f" ({_ghi[k[0]]})" if k[0] in _ghi else "")
                        for k, v in _diem.items() if v < 8]
                if sum(_diem.values()) < DIEM_SAN:
                    loi.append(f"đạt {sum(_diem.values())}/100, dưới sàn {DIEM_SAN} — yếu ở: "
                               + "; ".join(_yeu))
            except Exception:
                pass                      # thước phụ hỏng thì không được chặn dây chuyền chính
        cuoi = d
        if loi:
            _so_biet.append({"vong": lan, "loi": loi[:8]})
            fb = "; ".join(loi[:6])
            print(f"   ↻ vòng {lan}: {fb[:110]}")
            if lan >= VONG_VIET:
                break          # AI viết mãi không đạt thì đổi key không cứu được — dừng, trả bản cuối
            continue
        print(f"   ✅ đạt vòng {lan}: {d.get('title')!r} · "
              f"{sum(len(str((l or {}).get('say') or '').split()) for l in d.get('lines') or [])} từ thoại")
        d["_bien_tap"] = {"nhan_o_vong": lan, "so_vong_tu_choi": len(_so_biet),
                          "da_tu_choi": _so_biet}
        return d
    if cuoi is not None:
        cuoi["_con_loi"] = cham(cuoi, kenh, giay, so)
        cuoi["_bien_tap"] = {"nhan_o_vong": None, "so_vong_tu_choi": len(_so_biet),
                             "da_tu_choi": _so_biet}
        print(f"   ⚠️ {VONG_VIET} vòng chưa sạch — trả bản cuối kèm {len(cuoi['_con_loi'])} điểm sửa tay")
        return cuoi
    raise SystemExit("không sinh được tập nào")


# ── LƯU RA ĐĨA ──────────────────────────────────────────────────────────────────────────────
def _slug(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (t or "tap").lower()).strip("-")[:48] or "tap"


# ── CHỐNG TRÙNG THEO NỘI DUNG ───────────────────────────────────────────────────────────────
# 30/8 — Anh hỏi đúng chỗ yếu: "sợ kịch bản trùng lặp hay không nhớ". Có nhớ, nhưng nhớ nông.
# Cơ chế cũ đưa cho AI danh sách TÊN của 40 tập gần nhất kèm câu "đừng lặp lại". Hai chỗ hở:
#   · Chỉ 40 tập. Kênh chạy tới tập 500 thì 460 tập đầu không ai kiểm, và AI có xu hướng quay
#     lại đúng những trò đùa dễ nghĩ nhất — tức những trò nó đã nghĩ ra ở các tập đầu.
#   · Chỉ so TÊN. "The Last Slice" và "One Piece Left" là hai cái tên khác nhau và CÙNG MỘT
#     trò đùa. Tên là nhãn, không phải nội dung.
# Cổng này so CÚ LẬT và TÌNH HUỐNG với TOÀN BỘ kho, bằng phép đo chứ không bằng AI — nên nó
# không tốn lượt gọi, và không cạn hạn mức khi kho lớn dần.
_TU_RONG = {
    "the","a","an","and","or","but","of","to","in","on","at","for","with","is","are","was","were",
    "be","been","it","its","he","she","they","them","his","her","their","that","this","these",
    "those","as","by","from","up","down","out","into","then","than","so","just","one","two","who",
    "what","when","while","already","still","not","no","never","all","both","each","him","you",
    "your","my","me","we","us","have","has","had","do","does","did","will","would","can","could",
}


def _van_tay(tap: dict) -> set:
    """Dấu vân tay của một tập: tập từ có nghĩa trong cú lật và tình huống.

    Lấy `payoff` + `hook` chứ không lấy cả tập: cú lật LÀ trò đùa, và tình huống mở là thứ quyết
    định người xem có thấy quen hay không. Phần thoại giữa bỏ qua — hai tập có thể nói khác nhau
    hoàn toàn mà vẫn là cùng một trò.
    """
    import re as _re
    chu = " ".join(str(tap.get(k) or "") for k in ("payoff", "hook", "title")).lower()
    tu = {t for t in _re.findall(r"[a-z]{3,}", chu) if t not in _TU_RONG}
    return tu


def trung_voi(tap: dict, da: list, nguong: float = 0.45) -> tuple:
    """So tập mới với TOÀN BỘ kho. Trả (tên tập trùng, độ giống) hoặc ("", 0.0).

    Dùng Jaccard trên tập từ có nghĩa: giống nhau bao nhiêu phần trong tổng số từ hai bên cộng
    lại. Ngưỡng 0.45 là mức mà đọc hai tập lên thấy rõ "cái này kể rồi" — dưới nữa thì bắt oan
    những tập chỉ tình cờ dùng chung vài danh từ của cùng một căn phòng.
    """
    moi = _van_tay(tap)
    if len(moi) < 3:
        return "", 0.0
    xau, diem = "", 0.0
    for cu in da:
        c = _van_tay(cu)
        if not c:
            continue
        g = len(moi & c) / max(1, len(moi | c))
        if g > diem:
            xau, diem = str(cu.get("title") or "?"), g
    return (xau, diem) if diem >= nguong else ("", diem)


# ── VÂN TAY CƠ CHẾ — tầng chống trùng mà vân tay danh từ không với tới ──────────────────────
# 1/9 — Đo 30 tập đã xuất: 23/30 payoff là "nhấc/kéo một vật", 20/30 có "lộ ra", **18/30 dùng
# ĐÚNG CHUỖI ẤY**. Cổng `trung_voi` cho cả 30 tập đi qua, và nó không sai: nó so DANH TỪ, mà
# danh từ thì khác thật — tote, pizza box, grill, paint can. Cùng một trò đùa mặc mười bộ đồ.
#
# Đây là tầng thứ tư của cùng một bệnh, sau tên tập → nội dung → phòng/người lật. Lần này chốt
# ở chỗ sâu nhất: CƠ CHẾ của cú lật. Một kênh sống được lâu không phải vì đổi đồ vật, mà vì đổi
# cách tình thế bị đảo.
# Mô tả tiếng Anh của từng họ cú lật, để CẤP cho AI như một đề bài. Tên tiếng Việt ở khoá chỉ
# để đọc code và để thước phân loại — đưa nguyên tên ấy vào lệnh hệ thống thì AI không dùng được.
HO_LAT_TA = {
    "nhấc-lộ-vô-hại": "someone lifts or moves the object and what was underneath makes the whole "
                      "panic pointless",
    "người-bước-vào": "a character walks in at the worst possible moment and the situation flips "
                      "without anyone explaining it",
    "vật-hoá-ra-là-khác": "the object turns out to be something completely different from what "
                          "everyone has been treating it as",
    "thủ-phạm-lộ-diện": "the real cause becomes visible behind or beside the character who has "
                        "been blaming something else",
    "đảo-vai": "the two characters swap positions — whoever was in control hands it over, or has "
               "it taken",
    "hậu-quả-đuổi-kịp": "the consequence quietly catches up to the person who caused it, while "
                        "they are still congratulating themselves",
    "kẻ-thản-nhiên-bỏ-đi": "one character causes or ignores the disaster and simply leaves, "
                           "without looking back",
    "đúng-mà-vẫn-thua": "the person who was right about everything still ends up worse off "
                        "because of it",
    "sai-mà-vẫn-thắng": "the obviously wrong approach works anyway, and nobody can explain why",
    "người-thứ-ba-đã-xong": "a third character had already quietly solved it before the argument "
                            "even started",
}

HO_LAT = {
    "nhấc-lộ-vô-hại":        r"\b(lifts?|pulls?|tips?|flips?|slides?|paws?)\b.{0,60}\b(reveal|expos|show)",
    "người-bước-vào":        r"\b(walks? in|steps? in|appears? in the doorway|comes? in)\b",
    "vật-hoá-ra-là-khác":    r"\b(turns? out|it was (never|actually)|all along)\b",
    "thủ-phạm-lộ-diện":      r"\b(behind (him|her|them)|caught|knocking|one by one|down the row)\b",
    "đảo-vai":               r"\b(hands? (it|him|her)|takes? over|swaps?|trades?)\b",
    "hậu-quả-đuổi-kịp":      r"\b(runs? (out|down)|spreads? to|reaches? (his|her|their)|creeps?)\b",
    "kẻ-thản-nhiên-bỏ-đi":   r"\b(without looking|does not look|pulls? the door shut|steps? (out|past))\b",
    # 1/9 — ba họ nữa. Chọn ba họ này vì chúng ĐẢO NGÔI THỨ theo ba cách chưa có: người sai
    # thắng vì lý do khác, người đúng thua vì đúng, và cả hai cùng sai với một người thứ ba.
    "đúng-mà-vẫn-thua":      r"\b(was right|had been right|correct all along)\b.{0,40}\b(but|and still|anyway)\b",
    "sai-mà-vẫn-thắng":      r"\b(works? anyway|holds? anyway|somehow (works?|holds?)|by accident)\b",
    "người-thứ-ba-đã-xong":  r"\b(already (done|fixed|finished|handled)|had (done|fixed) it)\b",
}


def ho_lat(tap: dict) -> str:
    """Cú lật của tập này thuộc HỌ nào. `khác` = chưa có trong bảng, tức mới — đó là điều tốt."""
    p = str(tap.get("payoff") or "")
    for ten, rx in HO_LAT.items():
        if re.search(rx, p, re.I):
            return ten
    return "khác"


def trung_co_che(tap: dict, da: list, tran: float = 0.25) -> str:
    """Chặn khi họ cú lật này đã chiếm quá `tran` phần kho. Trả câu giải thích, hoặc ''.

    Ngưỡng 0,25: một kênh có bảy họ cú lật, chia đều là 0,14 mỗi họ. Cho tới 0,25 là còn chỗ
    cho họ nào hợp kênh hơn được dùng nhiều hơn; quá đó thì kênh bắt đầu có MỘT trò đùa.
    """
    ho = ho_lat(tap)
    if ho == "khác" or len(da) < 8:
        return ""
    n = sum(1 for x in da if ho_lat(x) == ho)
    if n / len(da) > tran:
        return (f"cú lật thuộc họ {ho!r} — kho đã dùng họ này {n}/{len(da)} lần. Đảo tình thế "
                f"bằng cách KHÁC: {', '.join(k for k in HO_LAT if k != ho)}")
    return ""


def trung_khuon_ten(tap: dict, da: list) -> str:
    """Bắt KHUÔN TÊN lặp lại, kể cả khi nội dung khác nhau.

    Chạy trên 15 tập HOUSE RULES có sẵn thì lộ ngay: "Pizza Box Panic" / "Paint Can Panic",
    "Trash Tower Tumble" / "Plate Tower Tumble". Nội dung có thể khác, nhưng người xem lướt qua
    danh sách tập chỉ đọc TÊN — và một trang toàn "X Panic" trông như một kênh tự lặp lại, dù
    từng tập đều mới. Tên là mặt tiền của kênh.
    """
    import re as _re
    lay = lambda t: tuple(_re.findall(r"[A-Za-z]+", str(t or "").lower())[-2:])
    duoi = lay(tap.get("title"))
    if len(duoi) < 2:
        return ""
    for cu in da:
        if lay(cu.get("title")) == duoi:
            return str(cu.get("title") or "")
    # một từ cuối trùng ở từ ba tập trở lên thì đó đã thành công thức, không còn là trùng hợp
    if duoi:
        dem = sum(1 for cu in da if lay(cu.get("title"))[-1:] == duoi[-1:])
        if dem >= 2:
            return f"{dem} tập đã kết thúc bằng {duoi[-1]!r}"
    return ""


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
                r.append({"title": str(x.get("title") or d), "room": str(x.get("room") or ""),
                          "lat": str(x.get("lat") or ""), "so": int(x.get("_so") or 0),
                          "dao_cu": str(x.get("_dao_cu") or ""),
                          "payoff": str(x.get("payoff") or "")})
            except Exception:
                pass
    return r


# ⚠️ BA HÀM DƯỚI ĐÂY ĐÃ NGHỈ VIỆC (1/9). Việc cấp phòng · người lật · kiểu mở nay do `_lich()`
# làm gọn trong một chỗ, vì ba bộ đếm rời rạc mỗi cái nhìn kho một kiểu và không cái nào biết
# cái kia — nên ba trục có thể cùng quay về một chỗ mà không ai thấy.
# Giữ lại vì `--so` và các đường gọi cũ có thể còn dùng, NHƯNG: sửa cách cấp trục thì sửa ở
# `_lich()`, đừng sửa ở đây. Hai nơi cấp cùng một thứ là cách chắc chắn để chúng lệch nhau.
def nguoi_lat_ke(kenh: str, da: list[dict]) -> str:
    """Ai lật ván cờ ở tập tới — luân phiên, cùng lý lẽ với `phong_ke`.

    Buddy lật ván cờ là cú lật hợp lý nhất, nên để AI tự chọn thì nó chọn con mèo mãi mãi. Mà
    khuôn lặp bị nhận ra trước cả nội dung (luật 7bk): xem tập ba là đoán được tập bốn."""
    # Lệch pha với `phong_ke` có chủ đích. Nếu cả hai cùng xoay theo `len(da)` thì chu kỳ trùng
    # nhau: tập 6 lại đúng cặp bếp+Mike của tập 1, và kênh lặp sau đúng năm tập. Cho người lật
    # xoay MỘT NẤC MỖI VÒNG PHÒNG thì năm phòng nhân năm người ra 25 cặp khác nhau — hai mươi
    # lăm tập không tập nào trùng cặp bối cảnh-người lật.
    # Hai yêu cầu phải thoả CÙNG LÚC, và bản trước chỉ thoả một:
    #   · hai tập LIỀN NHAU không được cùng người lật — xem liền năm tập thấy Mike lật cả năm
    #     thì vẫn là lặp, chỉ đổi dạng;
    #   · cặp (phòng, người lật) không được trùng trong cả vòng lớn.
    # `i//ps` thoả điều thứ hai, hỏng điều thứ nhất. Cộng thêm `i` thì mỗi tập nhích một người,
    # mà sau đúng ps×len(vs) tập mới quay lại cặp cũ — thoả cả hai.
    vs = list(ho_so(kenh)["vai"])
    ps = len(ho_so(kenh)["phong"]) or 1
    return vs[(len(da) // ps + len(da)) % len(vs)]


def kieu_ke(da: list[dict], ps: int) -> str:
    """Loại tai nạn mở màn cho tập tới. Lệch pha với cả hai trục kia."""
    return KIEU_MO[(len(da) // (ps * 2) + len(da)) % len(KIEU_MO)]


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


def luu(kenh: str, tap: dict, giay: float, so: int,
        day: bool = False, bo: tuple = ()) -> str:
    """Ghi tập ra đĩa: prompt để dán, JSON để khâu sau đọc, thư mục clips để anh thả video về.

    BỘ SHORT NHIỀU ĐỘ DÀI (30/8, anh dặn "các short cho 1 video độ dài phù hợp")
    ---------------------------------------------------------------------------
    Cùng MỘT ý tưởng xuất ra nhiều độ dài — nhưng CHỈ những độ dài mà kịch bản này thật sự vừa.
    Mỗi bản phụ đều đi qua `cham()` với đúng khuôn kể của độ dài ấy; không đạt thì không xuất,
    và in ra lý do. Bản cũ xuất hết mọi độ dài được yêu cầu, nên một kịch bản 8 giây có thể ra
    một tệp "15 giây" thiếu hẳn khúc leo thang — đúng lỗi kéo dài mà khuôn kể sinh ra để chặn.
    Vì sao vẫn đáng làm: 5s và 6s chung một khuôn, 7/8/9 chung một khuôn, 10/12/15 chung một
    khuôn — nên một kịch bản tốt vẫn phủ được hai ba độ dài trong cùng nhóm mà không mất gì.
    """
    tm = os.path.join(KHO, _slug(kenh), f"{so:03d}-{_slug(tap.get('title'))}")
    os.makedirs(os.path.join(tm, "clips"), exist_ok=True)
    pr = prompt(kenh, tap, giay, so=so, day=day)
    # Ghi kèm ĐỒ VẬT của tập: tập sau muốn gọi lại tập này thì phải biết tập này nói về cái gì.
    # Không suy ngược từ văn kể được — một tập nhắc năm danh từ, chỉ một trong đó là chủ đề.
    tap = dict(tap, _kenh=kenh, _giay=giay, _so=so, _dao_cu=_lich(kenh, so)["dao_cu"])
    io.open(os.path.join(tm, "tap.json"), "w", encoding="utf-8").write(
        json.dumps(tap, ensure_ascii=False, indent=2))
    io.open(os.path.join(tm, "PROMPT.txt"), "w", encoding="utf-8").write(pr)

    # ── SỔ BIÊN TẬP ────────────────────────────────────────────────────────────────────────
    # Luật `inauthentic content` cho phép AI làm gần hết, với điều kiện có **bàn tay biên tập**.
    # Ở đây bàn tay ấy có thật và đo được: mỗi tập bị từ chối nhiều vòng với lý do cụ thể trước
    # khi được nhận. Nhưng nó chỉ tồn tại trong bộ nhớ rồi biến mất — nên nhìn từ ngoài, một tập
    # qua tám vòng sửa và một tập viết một lần trông y hệt nhau.
    # Ghi ra đĩa. Không phải để trưng ra, mà vì: (1) đọc lại sổ này là cách nhanh nhất thấy cổng
    # nào đang đốt vòng vô ích — chính nó chỉ ra ba cổng "đo TỪ mà dặn Ý"; (2) nếu có ngày phải
    # chứng minh, thứ chứng minh được là bản ghi, không phải lời kể.
    if tap.get("_bien_tap"):
        io.open(os.path.join(tm, "bien_tap.json"), "w", encoding="utf-8").write(
            json.dumps(tap["_bien_tap"], ensure_ascii=False, indent=2))
    # ── ĐỘ DÀI PHỤ: CHỈ XUẤT KHI KỊCH BẢN THẬT SỰ VỪA ─────────────────────────────────────
    # 1/9 — Ghi chú trên HỨA "không phải cắt ngắn bản dài — mà dựng lại nhịp cho đúng độ dài
    # ấy". Mã thì chỉ đổi DÒNG THỜI GIAN rồi in lại y nguyên kịch bản. Lúc viết ghi chú ấy điều
    # đó là đủ, vì chưa có khuôn kể. Nay có rồi, và ba khuôn đòi ba thứ khác nhau:
    #     5–6s   đúng 2 lượt thoại, cú lật phải đổi HÌNH
    #     7–9s   2–3 lượt
    #     10–15s 3–4 lượt, escalate phải LEO THANG đo được
    # Nên một kịch bản 8 giây đem in ra bản 15 giây là bản thiếu hẳn tiếng cười giữa, và bản
    # 5 giây là bản vượt ngân sách từ. Đúng hai lỗi "kéo dài" và "cắt cụt".
    #
    # Không tự sửa kịch bản cho vừa — sửa tự động là đoán hộ người viết. Chấm, và chỉ xuất bản
    # nào ĐẠT; bản không đạt thì nói rõ vì sao để viết riêng một kịch bản cho độ dài ấy.
    for _g in bo:
        _g = float(_g)
        if abs(_g - float(giay)) < 0.01:
            continue
        _l = cham(tap, kenh, _g, so)
        if _l:
            # Phân biệt hai lý do khác hẳn nhau: SAI KHUÔN (viết cho độ dài khác, phải viết
            # riêng) và KỊCH BẢN VỐN CÒN LỖI (bản chính cũng chưa sạch). Gộp chung một câu thì
            # câu báo đổ sai phía, và đổ sai phía tốn thời gian hơn không báo gì.
            _khac = khuon_ke(_g)[0] != khuon_ke(giay)[0]
            print(f"   ⏭  bỏ bản {_g:g}s — "
                  + (f"khuôn {khuon_ke(_g)[0]} khác khuôn {khuon_ke(giay)[0]} của bản chính, "
                     f"phải viết riêng: " if _khac
                     else "kịch bản gốc vốn còn lỗi này: ") + _l[0][:76])
            continue
        io.open(os.path.join(tm, f"PROMPT-{_g:g}s.txt"), "w", encoding="utf-8").write(
            prompt(kenh, tap, _g, so=so, day=day))
    return tm


# ── XUẤT CHO GIAO DIỆN WEB ──────────────────────────────────────────────────────────────────
def _ngan_sach_khuon(khuon: dict, hs: dict, giay: float, ph: str) -> int:
    """Bao nhiêu KÝ TỰ văn kể mà CHÍNH KHUÔN NÀY còn chứa được. Đo thứ sẽ giao đi, không đo
    một đường song song.

    1/9 — Bản trước đo trên đường Python (`_bat_buoc`) rồi giao khuôn cho web. Hai đường lệch
    nhau ở ba chỗ nhỏ, cộng lại 213 ký tự, và **0/328 khuôn** lọt trần dù con số ngân sách trông
    rất hợp lý. Đây là lần thứ sáu trong buổi em đo ở một ngữ cảnh rồi dùng cho ngữ cảnh khác.
    Cách chữa duy nhất còn lại: **đo đúng vật sẽ giao**, bằng chính phép ghép mà web sẽ chạy.
    """
    vai = sorted(hs["vai"], key=len, reverse=True)[:VAI_TOI_DA]
    tu = int(_giay_thoai(giay) * TU_MOI_GIAY)
    sl = max(1, min(LUOT_TOI_DA, tu // 3))
    # Cast phải điền ĐÚNG MỨC NÉN của từng bản thân. Bản trước điền một dạng cho cả bốn mức,
    # nên thang nén thành vô nghĩa: `than[3]` (đã nén) vẫn nhận mô tả đầy đủ 607 ký tự.
    cast_m = ["\n".join(hs["nhan_vat"][x] for x in vai)] + \
             ["\n".join(_nen_vai(hs["nhan_vat"][x]) for x in vai)] * 3
    ten = ", ".join(vai)
    thoai = " ".join('%s says: “%s”' % (vai[i % len(vai)],
                                        " ".join(["wordword"] * max(1, tu // sl)))
                     for i in range(sl))
    ty = sum(VAN_KE_CHIA.values())

    def ghep(tong: int) -> int:
        def dien(t: str, muc: int = 0) -> str:
            t = (t.replace("@@CAST@@", cast_m[muc]).replace("@@CASTNAMES@@", ten)
                  .replace("@@ROOMDESC@@", hs["phong"][ph]).replace("@@ROOM@@", ph)
                  .replace("@@TITLE@@", "An Episode Title Here"))
            for k, v in VAN_KE_CHIA.items():
                t = t.replace("@@%s@@" % k.upper(), "w" * (tong * v // ty))
            return (t.replace('@@WHO@@ says: “@@LINES@@”', thoai)
                     .replace("@@LINES@@", thoai).replace("@@WHO@@", vai[0]))
        rao = dien(khuon["rao"])
        them = [dien(x) for x in khuon["them"]]
        tot, dai = -1, 10 ** 9
        for th in (dien(x, m) for m, x in enumerate(khuon["than"])):
            if len(th) + len(rao) + 2 > KY_TU_MAX:
                continue
            con, dem, n = KY_TU_MAX - len(th) - len(rao) - 2, 0, len(th)
            for t in them:
                if len(t) + 3 <= con:
                    con -= len(t) + 3; dem += 1; n += len(t) + 3
            if dem > tot:
                tot, dai = dem, n + len(rao) + 1
        return dai

    lo, hi = 100, 900
    if ghep(lo) > KY_TU_MAX:
        return 0                       # kênh này không chứa nổi cả văn kể tối thiểu — báo thẳng
    while lo < hi:
        m = (lo + hi + 1) // 2
        if ghep(m) <= KY_TU_MAX:
            lo = m
        else:
            hi = m - 1
    return lo


def luat_web(kenh: str) -> dict:
    """Xuất THƯỚC dưới dạng DỮ LIỆU để web thi hành.

    1/9 — Web gọi AI viết kịch bản rồi dùng thẳng, không qua cổng nào: cổng nằm bên Python.
    Nên mọi luật đã trả giá để có (khuôn kể theo thời lượng · chống trùng cơ chế · thoại kiểu
    Mỹ · hook ba vế) đều KHÔNG áp cho đường web — đúng chỗ anh bấm nút hàng ngày.
    
    Cách chữa KHÔNG phải viết lại thước bằng JavaScript: hai bản thước thì sớm muộn lệch nhau,
    và bài học ấy đã trả giá ở câu cấm chữ (ba bản) và câu góc máy (bốn mươi bản). Cách chữa là
    Python vẫn GIỮ luật, chỉ đổi dạng: từ mã thành dữ liệu. Web không biết luật gì, nó chỉ chạy
    danh sách nó được đưa. Sửa luật ở đây thì web đổi theo ngay lượt xuất sau.
    """
    hs = ho_so(kenh)
    theo_giay = {}
    for g in GIAY_CHUAN:
        ten, _ = khuon_ke(g)
        n = nhip(g)
        if g <= 6.5:
            luot = [2, 2]
        elif g <= 9.5:
            luot = [2, 3]
        else:
            luot = [3, LUOT_TOI_DA]
        theo_giay[str(g)] = {
            "khuon": ten,
            "nhip": [x[2] for x in n],
            "luot": luot,
            "tu_toi_da": int(_giay_thoai(g) * TU_MOI_GIAY),
            "esc_toi_da": 90 if g <= 6.5 else 0,          # 0 = không chặn
            "can_rai_nhip": g > 9.5,
            "lat_phai_doi_hinh": g <= 6.5,
            "esc_phai_leo": g > 9.5,
        }
    return {
        "hook_tu": [16, 30],
        "tu_moi_luot": TU_MOI_LUOT,
        "vai_toi_da": VAI_TOI_DA,
        "van_ke_chia": VAN_KE_CHIA,
        "ghim_may": list(GHIM_MAY),
        "cam_ky": [[t, ly] for t, ly in CAM_KY],
        "khong_my": [[rx, ly] for rx, ly in KHONG_MY],
        "do_to": [x for x in DO_TO],
        "dong_nghia_do": {k: list(v) for k, v in DONG_NGHIA_DO.items()},
        "bo_tu": ["the","a","an","of","in","on","with","that","one","some","and","for",
                  "somebody","someone","nobody","last","good","shared"],
        "ho_lat": {k: v for k, v in HO_LAT.items()},
        "lat_doi_hinh": r"\b(falls?|opens?|tips?|swings?|drops?|shuts?|slides?|steps?|turns?|"
                        r"collapses?|lands?|rolls?|pulls?|walks?|leaves?)\b",
        "esc_leo": r"\b(further|again|another|more|bigger|second|third|harder|deeper|higher|"
                   r"faster|whole|entire|all of|now the|even the|one more|instead of|not enough)\b",
        "lat_bat_ky": r"\b(reveal\w*|turns? out|was never|all along|instead|behind (him|her|them))\b",
        "bo_ghim_may": r"^[^:]{0,40}(shot|angle)\s*:\s*",
        "so_chinh_xac": SO_CHINH_XAC,
        "sai_trai": SAI_TRAI_TA,
        "theo_giay": theo_giay,
        "vong_viet": 4,      # web thử lại tối đa 4 lượt — quá nữa là đốt hạn mức cho một tập
        "nhip_goi_lai": NHIP_GOI_LAI,
        "nhac_lo": r"\b(remember when|last time|as we (saw|know)|like (last|the other) (time|"
                   r"episode)|in the last (one|episode)|you (may )?recall|previously|"
                   r"same as (last|before))\b",
    }


def xuat_web(thu_muc: str) -> list[str]:
    """Xuất hồ sơ + KHUÔN prompt cho dashboard, mỗi kênh một tệp.

    31/8 — Anh muốn bấm chọn kênh và thời lượng ngay trên web, có nút chép và nút tạo. Cách dễ
    nhất là viết lại phép ghép prompt bằng JavaScript — và đó sẽ là **bản thứ hai của sự thật**,
    đúng cái bẫy đã trả giá nhiều lần trong dự án này (câu cấm chữ ba bản, câu góc máy bốn mươi
    bản). Sửa một luật hài ở Python mà quên sửa bản JS thì web lặng lẽ sinh prompt theo luật cũ,
    và không ai biết cho tới khi xem lại vài chục video.
    Nên web KHÔNG ghép prompt. Python ghép sẵn toàn bộ phần cố định — mọi khối khoá, luật hình
    ảnh, hàng rào chống lỗi — và chừa đúng bốn chỗ trống cho phần AI viết. Việc của web chỉ là
    điền vào chỗ trống. Luật vẫn nằm ở một nơi duy nhất.
    """
    os.makedirs(thu_muc, exist_ok=True)
    ra = []
    # ── VÌ SAO XUẤT BA PHẦN RỜI, KHÔNG XUẤT MỘT CHUỖI ─────────────────────────────────────
    # 1/9 — Bản trước xuất một chuỗi đã ghép sẵn, và Python phải ĐOÁN TRƯỚC văn kể sẽ dài bao
    # nhiêu để chừa chỗ. Đoán ba lần, ba lần sai (774 → 710 → 762 ký tự), và lần nào cũng còn
    # vài chục khuôn tràn — vì chỗ phình xảy ra ở trình duyệt, nơi Python không đo được.
    #
    # Không đoán nữa. Xuất ba phần rời: THÂN (có ô trống) · KHỐI TẢ THÊM (rời từng khối) ·
    # HÀNG RÀO. Web điền ô trống xong thì ĐO chuỗi thật, rồi chèn từng khối tả thêm chừng nào
    # còn chỗ, rồi mới nối hàng rào vào cuối. Luật vẫn một nơi — luật là "hàng rào không bao
    # giờ nhường chỗ", và nó đúng ở cả hai bên vì cả hai bên thi hành cùng một câu ấy.
    MAU = {"title": "@@TITLE@@", "room": "", "hook": "@@HOOK@@", "setup": "@@SETUP@@",
           "escalate": "@@ESCALATE@@", "payoff": "@@PAYOFF@@",
           "lines": [{"who": "@@WHO@@", "act": "says", "say": "@@LINES@@"}]}
    for ten, k in KENH.items():
        hs = ho_so(ten)
        # ── PHÒNG DÙNG Ô TRỐNG GỐC, KHÔNG THAY CHUỖI SAU ─────────────────────────────────
        # 1/9 — Bản trước dựng khuôn với phòng thật rồi `replace(ten_phong, "@@ROOM@@")`. Với
        # DINER SHIFT phòng tên "counter", và chữ ấy CÒN NẰM trong câu tả căn nhà ("a long
        # counter with chrome stools") lẫn trong câu tả nét vẽ. Nên web điền "booth" vào sẽ ra
        # "Ruby's Diner ... a long booth with chrome stools" — Kling đọc và vẽ đúng thứ vô nghĩa
        # ấy. Không lỗi nào báo, vì về mặt chuỗi phép thay hoàn toàn thành công.
        #
        # Không có cách nào chữa bằng phép thay: tên phòng là danh từ thường, nó SẼ trùng. Nên
        # dựng thẳng bằng ô trống — đặt một khoá phòng giả có mô tả là ô trống, rồi ghép như
        # bình thường. Không còn phép thay nào để trượt.
        _KP, _KD = "@@room@@", "@@ROOMDESC@@"
        hs["phong"][_KP] = _KD
        ph0, mo0 = _KP, _KD
        # ── DÀN NHÂN VẬT CŨNG PHẢI LÀ Ô TRỐNG ─────────────────────────────────────────────
        # 1/9 — Khuôn dựng bằng chỗ trống `@@HOOK@@`, nên `_co_mat()` không thấy tên ai và
        # rơi về "lấy cả dàn". Khuôn HOUSE RULES vì thế khoá cứng CẢ NĂM nhân vật, ở mọi tập.
        # Hai cái giá: tốn ~750 ký tự thay vì ~300 (đủ để bóp hook xuống còn 20 từ), và tệ hơn
        # — prompt bảo Kling vẽ năm người trong một tập chỉ có hai. Đúng lỗi mà
        # KLING_CACH_DUNG.md đã cảnh báo, tái sinh ở khâu xuất web.
        # Mỗi mức nén dựng dàn vai một kiểu (mức ≥1 dùng `_nen_vai`), nên phải thay ô trống
        # THEO ĐÚNG MỨC. Bản đầu chỉ khớp dạng chưa nén, nên mức 1–3 khoá cứng cả năm nhân vật
        # — vừa tốn ~450 ký tự vừa bảo Kling vẽ ba người không có trong tập.
        _names = ", ".join(hs["vai"])
        def _o(t, muc=0):
            cast = "\n".join((hs["nhan_vat"][x] if muc < 1 else _nen_vai(hs["nhan_vat"][x]))
                             for x in hs["vai"])
            # Chỉ còn phải thay dàn vai — chuỗi dài, duy nhất, không thể trùng nhầm. Phòng đã
            # là ô trống từ lúc dựng nên không có phép thay nào cho nó.
            return (t.replace(cast, "@@CAST@@").replace(_names, "@@CASTNAMES@@")
                     .replace(_KP, "@@ROOM@@"))
        khuon = {}
        for g in GIAY_CHUAN:
            tap = dict(MAU, room=ph0)
            # Bốn mức nén của THÂN, xuất cả bốn. Web chọn mức ÍT NÉN NHẤT mà còn lọt trần —
            # đúng thang mà `prompt()` đi ở phía Python. Xuất một mức thôi thì web hoặc luôn
            # thừa chỗ (mức 3, mất chi tiết vô cớ) hoặc luôn tràn (mức 0).
            rao = _bat_buoc(ten, tap, g, 0, 1, 0)[1]
            kh = {
                "than": [_o("\n".join(_bat_buoc(ten, tap, g, 0, 1, m)[0]), m) for m in (0, 1, 2, 3)],
                "them": [_o("\n".join(x).strip()) for x in _kho_tuy_chon(ten, tap, g) if x],
                "rao":  _o("\n".join(rao)),
            }
            # Ngân sách đo trên CHÍNH khuôn vừa dựng, ở ca xấu nhất của kênh: dàn đông nhất,
            # tên dài nhất, phòng có mô tả dài nhất, thoại kịch trần.
            kh["van_ke_max"] = _ngan_sach_khuon(
                kh, hs, g, max((p for p in hs["phong"] if p != _KP),
                               key=lambda p: len(hs["phong"][p])))
            khuon[str(g)] = kh
        hs["phong"].pop(_KP, None)      # khoá giả chỉ sống trong lúc dựng khuôn của kênh này
        ra_kenh = {
            "ten": ten, "mo_ta": hs["mo_ta"], "ty_le": hs["ty_le"],
            "vai": {t: hs["nhan_vat"][t] for t in hs["vai"]},
            # Dạng NÉN của khoá nhân vật — bỏ phần tính nết (thuộc khối PERFORMANCE, Kling
            # không vẽ được tính nết). Web dùng dạng này cho các mức nén ≥1; điền dạng đầy đủ
            # vào mức đã nén thì thang nén mất tác dụng và prompt tràn 200 ký tự.
            "vai_gon": {t: _nen_vai(hs["nhan_vat"][t]) for t in hs["vai"]},
            "phong": hs["phong"],
            "mach": hs["mach"],
            "giay": list(GIAY_CHUAN),
            "giay_uu_tien": list(GIAY_UU_TIEN),
            "nhip": {str(g): nhip(g) for g in GIAY_CHUAN},
            "sys": {str(g): _sys(ten, g) for g in GIAY_CHUAN},
            "tu_toi_da": {str(g): int(_giay_thoai(g) * TU_MOI_GIAY) for g in GIAY_CHUAN},
            "hai": hs["hai"],
            "luat": luat_web(ten),
            # Tham số bộ lịch. Web tính ra cùng một bộ trục bằng cùng công thức — tham số do
            # Python cấp nên hai bên không thể lệch. Không xuất sẵn danh sách tập vì kho tính
            # được từ sáu con số này, còn xuất 500 tập/kênh thì tệp phồng thêm 750 KB.
            "lich": {
                # Bảy trục — phải khớp ĐÚNG danh sách trong `_lich()`. 1/9: thêm trục cơ chế
                # lật vào `_lich` và `_buoc_lich` mà quên chỗ này, nên web tính theo sáu trục
                # còn Python theo bảy: 280/280 đề bài lệch, và lệch ĐÚNG MỘT TRƯỜNG nên sáu
                # trục kia vẫn khớp hoàn hảo — kiểu lệch dễ tin là "gần đúng" nhất.
                "truc": _do_truc(hs),
                "buoc": _buoc_lich(ten), "goc": _goc_lich(ten),
                "phong": list(hs["phong"]), "dao_cu": list(hs.get("dao_cu") or []),
                "ap_luc": list(AP_LUC), "kieu_mo": list(KIEU_MO), "vai": list(hs["vai"]),
                # Thứ tự họ cú lật phải lấy TỪ CHÍNH `HO_LAT` — bảng mà `_lich()` dùng — chứ
                # không từ `HO_LAT_TA`. Hai từ điển có cùng mười khoá nhưng khác thứ tự chèn,
                # và Python giữ thứ tự chèn: đọc nhầm bảng thì hai bên lệch trục thứ bảy trong
                # khi sáu trục kia vẫn khớp. Đo được: 280/280 đề bài sai đúng một trường.
                "ho_lat_ten": list(HO_LAT),
                "ho_lat_ta": dict(HO_LAT_TA),
            },
            "gioi_han": {"vai": VAI_TOI_DA, "luot": LUOT_TOI_DA, "tu_moi_luot": TU_MOI_LUOT,
                         "ky_tu_max": KY_TU_MAX, "hook_tu": [16, 30], "diem_san": DIEM_SAN},
            "khuon": khuon,
        }
        f = os.path.join(thu_muc, _slug(ten) + ".json")
        io.open(f, "w", encoding="utf-8").write(json.dumps(ra_kenh, ensure_ascii=False))
        ra.append(f)
    # mục lục nhẹ để web nạp danh sách kênh mà không phải tải hết
    io.open(os.path.join(thu_muc, "index.json"), "w", encoding="utf-8").write(json.dumps(
        {"kenh": [{"ten": t, "slug": _slug(t), "mo_ta": k["mo_ta"],
                   "vai": list(ho_so(t)["vai"]), "phong": list(ho_so(t)["phong"])}
                  for t, k in KENH.items()],
         "giay": list(GIAY_CHUAN),
         "luat": LUAT_HAI_MY}, ensure_ascii=False))
    return ra


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
    ap.add_argument("--xuat-web", default="", help="xuất hồ sơ + khuôn prompt cho dashboard")
    ap.add_argument("--day", action="store_true",
                    help="prompt ĐẦY ĐỦ ~2700 từ (13 khối chỉ đạo hình ảnh) thay vì bản gọn "
                         "~2700 ký tự. Dùng khi giao diện Kling nhận trọn prompt dài.")
    ap.add_argument("--bo-short", default="",
                    help="một ý tưởng ra NHIỀU độ dài, ví dụ 5,8,15 — cùng dàn vai, cùng phòng, "
                         "cùng cú lật, chỉ khác cách nén nhịp")
    a = ap.parse_args()

    if a.xuat_web:
        fs = xuat_web(a.xuat_web)
        tong = sum(os.path.getsize(f) for f in fs)
        print(f"  ✅ xuất {len(fs)} kênh · {tong/1024:.0f} KB → {a.xuat_web}")
        return 0

    if a.kenh_liet_ke:
        for k, v in KENH.items():
            print(f"  · {k:<14} {v['mo_ta']}")
        return 0

    for _g in (a.giay, *(float(x) for x in a.bo_short.replace(" ", "").split(",") if x)):
        if _g not in GIAY_CHUAN:
            print(f"  ⚠️ {_g:g}s không nằm trong mốc Kling hay dùng {GIAY_CHUAN} — vẫn dựng nhịp "
                  f"theo số này, nhưng giao diện Kling có thể không cho chọn.")

    hs = ho_so(a.kenh)
    da = _da_lam(a.kenh)
    so = a.so or (len(da) + 1)
    for i in range(a.sl):
        # 1/9 — Ba cách cấp rời rạc (phòng · người lật · kiểu mở) mỗi cái đếm kho một kiểu, và
        # không cái nào biết cái kia — nên ba trục có thể cùng quay về một chỗ. Nay MỘT bộ lịch
        # cấp cả sáu trục từ một chỉ số duy nhất, đi hết không gian tích rồi mới lặp.
        _x = _lich(a.kenh, so)
        ph = a.phong or _x["phong"]
        lt = _x["lat"]
        ki = _x["kieu_mo"]
        # Sổ từ mòn: chữ nào đã dùng ở BA tập trở lên thì cấm hẳn. Ngưỡng ba vì hai lần còn có
        # thể là trùng hợp; ba lần là AI đã bám vào một khuôn.
        dem: dict[str, int] = {}
        for x in da:
            for w in set(re.findall(r"[a-z]{5,}", (x.get("hook", "") + " " + x["title"]).lower())):
                dem[w] = dem.get(w, 0) + 1
        cam = [w for w, n in dem.items() if n >= 3 and w not in _BO_QUA]
        y = a.y or f"a fresh everyday moment in the {ph}"
        print(f"\n▶ {hs['ten']} tập {so:03d} · {a.giay:g}s · {ph} · {_x['dao_cu'][:26]} · "
              f"{lt} lật · {ki[:30]}…")
        tap = sinh_tap(a.kenh, y, a.giay, tranh=[x["title"] for x in da], phong=ph, lat=lt,
                       kieu=ki, cam_tu=cam, so=so)
        _bo = tuple(float(x) for x in a.bo_short.replace(" ", "").split(",") if x)
        tm = luu(a.kenh, tap, a.giay, so, day=a.day, bo=_bo)
        n = len(io.open(os.path.join(tm, "PROMPT.txt"), encoding="utf-8").read())
        canh = "✓" if KY_TU_MIN <= n <= KY_TU_MAX else "⚠️ ngoài khoảng"
        print(f"   📄 {os.path.join(tm, 'PROMPT.txt')}  ({n} ký tự {canh})")
        da.append({"title": str(tap.get("title") or ""), "room": ph, "lat": lt,
                   "hook": str(tap.get("hook") or "")})
        so += 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
