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
GIAY_CHUAN = (5, 6, 7, 8, 9, 10, 12, 15)

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
_CAM_TU_LOAT: list = []    # từ đã mòn trong loạt đang chạy; `main` nạp, `cham` đọc
# Chữ thuộc về khuôn prompt hoặc về căn nhà thì lặp là ĐÚNG — cấm chúng là cấm nhầm.
_BO_QUA = {"static", "shot", "level", "wide", "kitchen", "living", "backyard", "garage", "porch",
           "front", "table", "floor", "wooden", "camera", "counter", "couch", "coffee", "house",
           "while", "which", "their", "there", "about", "where", "holding", "standing"}
VONG_VIET = 8              # số lần cho AI viết lại một tập. Dây chuyền để 3 — hợp cho việc trích
                           # dữ liệu, quá ít cho việc sáng tác: kịch bản hỏng nhịp thường tới lần
                           # thứ tư, thứ năm mới ra được bản dùng được.

GHIM_MAY = ("static", "eye-level", "eye level", "low angle", "high angle", "wide shot",
            "medium shot", "close shot", "over-the-shoulder", "locked-off", "top-down")

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
        },
        "style": ("Original 2D cartoon animation, original character designs, clean dark outlines, simple flat shapes, bright saturated colors, expressive facial animation, readable gestures, smooth limited animation, American office break room setting"),
        "audio": ("Natural American English dialogue, consistent distinct voices for {{vai}}, playful expressive delivery, precise lip sync, clean vocal recording, short conversational pauses, useful ambient sound effects, one clear comedic escalation and a strong final punchline"),
        "dien": "Dave is confident even when obviously wrong; Priya is dry and keeps evidence; Kyle says out loud what everyone is thinking; Marge has seen this exact thing happen twice before",
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
        },
        "style": ("Original 2D cartoon animation, original character designs, clean dark outlines, simple flat shapes, bright saturated colors, expressive facial animation, readable gestures, smooth limited animation, American late-night diner setting"),
        "audio": ("Natural American English dialogue, consistent distinct voices for {{vai}}, playful expressive delivery, precise lip sync, clean vocal recording, short conversational pauses, useful ambient sound effects, one clear comedic escalation and a strong final punchline"),
        "dien": "Rosa is unshockable and deadpan; Chef Nick defends every bad idea he has ever had; Toby is new and over-prepares everything; Walt comments once and is always right",
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
        },
        "style": ("Original 2D cartoon animation, original character designs, clean dark outlines, simple flat shapes, bright saturated colors, expressive facial animation, readable gestures, smooth limited animation, American neighborhood gym setting"),
        "audio": ("Natural American English dialogue, consistent distinct voices for {{vai}}, playful expressive delivery, precise lip sync, clean vocal recording, short conversational pauses, useful ambient sound effects, one clear comedic escalation and a strong final punchline"),
        "dien": "Brad gives confident wrong advice; Nia is dry and stronger than everyone; Gary reads every instruction and still gets it wrong; Coach Ed says one sentence and ends the argument",
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
        },
        "style": ("Original 2D cartoon animation, original character designs, clean dark outlines, simple flat shapes, bright saturated colors, expressive facial animation, readable gestures, smooth limited animation, American college dorm room setting"),
        "audio": ("Natural American English dialogue, consistent distinct voices for {{vai}}, playful expressive delivery, precise lip sync, clean vocal recording, short conversational pauses, useful ambient sound effects, one clear comedic escalation and a strong final punchline"),
        "dien": "Jess is dry and exhausted; Marcus has a confident theory about everything; Ollie takes everything literally; Sam has already made a chart about it",
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
        },
        "style": ("Original 2D cartoon animation, original character designs, clean dark outlines, simple flat shapes, bright saturated colors, expressive facial animation, readable gestures, smooth limited animation, American auto repair shop setting"),
        "audio": ("Natural American English dialogue, consistent distinct voices for {{vai}}, playful expressive delivery, precise lip sync, clean vocal recording, short conversational pauses, useful ambient sound effects, one clear comedic escalation and a strong final punchline"),
        "dien": "Hank diagnoses a car by listening to it; Rico is quick and learns the hard way; Denise is dry and actually runs the place; Mr. Palmer explains cars to mechanics",
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
        },
        "style": ("Original 2D cartoon animation, original character designs, clean dark outlines, simple flat shapes, bright saturated colors, expressive facial animation, readable gestures, smooth limited animation, American suburban backyard setting"),
        "audio": ("Natural American English dialogue, consistent distinct voices for {{vai}}, playful expressive delivery, precise lip sync, clean vocal recording, short conversational pauses, useful ambient sound effects, one clear comedic escalation and a strong final punchline"),
        "dien": "Ron measures the lawn and the fence; Deb is unbothered on purpose; Chad helps and makes it worse; Mrs. Okafor sees everything and comments once",
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
        },
        "style": ("Original 2D cartoon animation, original character designs, clean dark outlines, simple flat shapes, bright saturated colors, expressive facial animation, readable gestures, smooth limited animation, American clinic waiting room setting"),
        "audio": ("Natural American English dialogue, consistent distinct voices for {{vai}}, playful expressive delivery, precise lip sync, clean vocal recording, short conversational pauses, useful ambient sound effects, one clear comedic escalation and a strong final punchline"),
        "dien": "Carla has heard every excuse twice; Trent follows the form even when it makes no sense; Bev arrives with a diagnosis she found online; Dr. Shah is dry and running late",
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
        },
        "style": ("Original 2D cartoon animation, original character designs, clean dark outlines, simple flat shapes, bright saturated colors, expressive facial animation, readable gestures, smooth limited animation, American car interior on a highway setting"),
        "audio": ("Natural American English dialogue, consistent distinct voices for {{vai}}, playful expressive delivery, precise lip sync, clean vocal recording, short conversational pauses, useful ambient sound effects, one clear comedic escalation and a strong final punchline"),
        "dien": "Ted refuses to stop for anything; Anne is dry and holds the map; Ellie narrates everything out loud; Grandma Rue produces exactly what is needed from her bag",
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
        },
        "style": ("Original 2D cartoon animation, original character designs, clean dark outlines, simple flat shapes, bright saturated colors, expressive facial animation, readable gestures, smooth limited animation, American home living room with pets setting"),
        "audio": ("Natural American English dialogue, consistent distinct voices for {{vai}}, playful expressive delivery, precise lip sync, clean vocal recording, short conversational pauses, useful ambient sound effects, one clear comedic escalation and a strong final punchline"),
        "dien": "Duke is confident every plan will work; Cleo watches and judges silently; Nugget observes everything from the cage; Owen over-researches; Rae already knows which animal is responsible",
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
            d[k] = _mao_tu(" ".join(str(d[k]).split()).strip())
    return d


def _mao_tu(t: str) -> str:
    """`a avalanche` -> `an avalanche`. Kling không quan tâm, người xem đọc phụ đề thì có."""
    t = re.sub(r"\ba (?=[aeiouAEIOU])", "an ", t)
    return re.sub(r"\ban (?=[bcdfgjklmnpqrstvwxyz])", "a ", t)


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
           tran: int = KY_TU_MAX, day: bool = False) -> str:
    """Ghép prompt gửi Kling. `day=False` bản gọn đã chạy tốt; `day=True` bản chỉ đạo đầy đủ.

    Bốn khối khoá lấy từ hồ sơ, KHÔNG qua tay AI. Nếu dài quá thì hạ MỨC CHI TIẾT theo đúng thứ
    tự giá trị: phần tả bối cảnh rườm rà đi trước, rồi phần dặn cách diễn — còn dàn nhân vật,
    chuyện của tập, và hàng rào RENDER thì không bao giờ đụng tới.

    HAI BẢN, VÀ VÌ SAO (30/8)
    -------------------------
    Anh dặn "prompt 2500–3000 từ". Con số ấy khớp chính xác với KÝ TỰ của bộ 500 prompt anh đang
    chạy: đo được 424 từ / 2.970 ký tự. Còn 2.500 TỪ thì vào khoảng 17.000 ký tự — gấp gần sáu
    lần, và ghi chú đầu tệp này (viết từ chính bộ 500 ấy) nói rõ Kling CẮT ĐUÔI prompt quá dài.
    Đuôi là khối DO NOT và RENDER REQUIREMENTS, tức đúng hàng rào chặn "thừa ngón, thêm tay,
    chữ loằng ngoằng". Prompt dài hơn mà mất hàng rào thì hình XẤU ĐI, ngược hẳn ý anh.

    Tôi không tự quyết thay anh, cũng không đoán bừa giới hạn của Kling 3.0 (tôi không có tài
    khoản để đo). Nên làm cả hai và để anh chọn:
      · `day=False` (mặc định) — bản gọn 2.400–3.000 KÝ TỰ, đúng khuôn bộ 500 đang chạy tốt.
      · `day=True`  — bản đầy đủ 2.500–3.000 TỪ, thêm bảy khối chỉ đạo hình ảnh (máy quay, ánh
        sáng, màu, diễn xuất, tiếng động, hook, nối cảnh). Không co, không cắt.
    Nếu Kling nhận trọn bản đầy thì dùng bản đầy: nó nói rõ TRÔNG NHƯ THẾ NÀO, và mỗi câu bỏ
    trống trong prompt là một chỗ máy tự bịa — nguồn gốc của mọi tập trông khác nhau.
    """
    if day:
        return _ghep(kenh, tap, giay, so, bien, 0, day=True)
    for muc in (0, 1, 2, 3):
        r = _ghep(kenh, tap, giay, so, bien, muc)
        if len(r) <= tran or muc == 3:
            return r
    return r


def _ghep(kenh: str, tap: dict, giay: float, so: int, bien: int, muc: int,
          day: bool = False) -> str:
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
        # Mức 1: giữ TÊN phòng, những mốc mắt nhận ra ngay, VÀ mọi mốc kịch bản đang nhắc tới.
        # Bỏ mốc đang được dùng là co vào đúng chỗ không được đụng: Kling đọc chuyện có cái đèn
        # mà bối cảnh không có cái đèn nào thì nó tự đặt một cái, mỗi tập một chỗ.
        _ke = (ke + " " + " ".join(str((l or {}).get("say") or "")
                                   for l in (tap.get("lines") or []))).lower()
        _m = ta.split(", ")
        giu = _m[:3] + [x for x in _m[3:]
                        if any(w in _ke for w in re.findall(r"[a-z]{4,}", x.lower()))]
        ta = ", ".join(dict.fromkeys(giu)).rstrip(".") + "."
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
    _g = _gop(tap, n)
    _co_setup = any(x[2] == "setup" for x in n)
    for _a, _b, _ten in n:
        _mo = _g.get(_ten, "")
        # Thoại đặt ở khối dựng; clip ngắn không có khối dựng thì thoại về cú chốt.
        if _ten == ("setup" if _co_setup else "payoff"):
            _mo = f"{_mo} {thoai}".strip()
        if _ten == "payoff":
            _mo += " Hold the final reaction for a fraction of a second."
        r.append(f"{_a:.1f}–{_b:.1f}s: {_mo.strip()}")
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

    # Bảy khối chỉ đạo hình ảnh — chỉ ở bản đầy. Chúng đứng TRƯỚC hàng rào RENDER, để nếu Kling
    # có cắt đuôi thì phần bị mất là phần tả thêm, không phải phần chặn lỗi.
    if day:
        _ph = str(tap.get("room") or next(iter(hs["phong"]), "room"))
        for _kh in (_hook(tap, n), _cu_may(n, g), _dan_dung(n, hs), _anh_sang(hs, _ph),
                    _mau(hs), _nghe_hoat_hinh(), _dien_xuat(tap, hs), _thoai_nhip(tap, g),
                    _tieng_dong(n, hs, _ph), _khung_mau(tap, n, hs), _trang_phuc(hs, comat),
                    _luat_the_gioi(hs), _noi_canh(hs), _viral_usa(n, g),
                    _thanh_chat_luong(hs, g), _cam(hs)):
            r.extend(_kh)
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
        f"  · Vary WHO delivers the reversal across episodes — the cat solving everything twice "
        f"in a row is a formula the viewer spots before the joke.\n"
        f"  · Never end on a line that explains who was right. Show it and stop.\n"
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


def sinh_tap(kenh: str, y_tuong: str, giay: float = 8, api_key: str = None,
             tranh: list | None = None, keys: list | None = None, phong: str = "",
             lat: str = "", kieu: str = "", cam_tu: list | None = None) -> dict:
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
        if lat:
            d["lat"] = lat
        loi = cham(d, kenh, giay)
        if lat and lat.split()[0] not in str(d.get("payoff") or ""):
            loi.append(f"cú lật phải do {lat} thực hiện — payoff không nhắc tới {lat}")
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
                r.append({"title": str(x.get("title") or d), "room": str(x.get("room") or ""),
                          "lat": str(x.get("lat") or "")})
            except Exception:
                pass
    return r


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
    Cùng MỘT ý tưởng xuất ra nhiều độ dài. Không phải cắt ngắn bản dài — mà dựng lại nhịp cho
    đúng độ dài ấy: 5 giây có hai khối (một trò đùa, một cú đấm), 8 giây có ba, 15 giây có bốn.
    Dàn vai, căn phòng và cú lật giữ nguyên, nên các bản là ANH EM của nhau chứ không phải bản
    cắt xén — người xem gặp bản nào cũng thấy trọn một mẩu chuyện.
    Vì sao đáng làm: mỗi nền tảng ăn một độ dài khác nhau, và cùng một ý tưởng tốt thì nên được
    dùng hết ở cả ba chỗ thay vì phải nghĩ ba ý tưởng.
    """
    tm = os.path.join(KHO, _slug(kenh), f"{so:03d}-{_slug(tap.get('title'))}")
    os.makedirs(os.path.join(tm, "clips"), exist_ok=True)
    pr = prompt(kenh, tap, giay, so=so, day=day)
    tap = dict(tap, _kenh=kenh, _giay=giay, _so=so)
    io.open(os.path.join(tm, "tap.json"), "w", encoding="utf-8").write(
        json.dumps(tap, ensure_ascii=False, indent=2))
    io.open(os.path.join(tm, "PROMPT.txt"), "w", encoding="utf-8").write(pr)
    for _g in bo:
        if abs(float(_g) - float(giay)) < 0.01:
            continue
        io.open(os.path.join(tm, f"PROMPT-{float(_g):g}s.txt"), "w", encoding="utf-8").write(
            prompt(kenh, tap, float(_g), so=so, day=day))
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
    ap.add_argument("--day", action="store_true",
                    help="prompt ĐẦY ĐỦ ~2700 từ (13 khối chỉ đạo hình ảnh) thay vì bản gọn "
                         "~2700 ký tự. Dùng khi giao diện Kling nhận trọn prompt dài.")
    ap.add_argument("--bo-short", default="",
                    help="một ý tưởng ra NHIỀU độ dài, ví dụ 5,8,15 — cùng dàn vai, cùng phòng, "
                         "cùng cú lật, chỉ khác cách nén nhịp")
    a = ap.parse_args()

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
        ph = a.phong or phong_ke(a.kenh, da)
        lt = nguoi_lat_ke(a.kenh, da)
        ki = kieu_ke(da, len(hs["phong"]) or 1)
        # Sổ từ mòn: chữ nào đã dùng ở BA tập trở lên thì cấm hẳn. Ngưỡng ba vì hai lần còn có
        # thể là trùng hợp; ba lần là AI đã bám vào một khuôn.
        dem: dict[str, int] = {}
        for x in da:
            for w in set(re.findall(r"[a-z]{5,}", (x.get("hook", "") + " " + x["title"]).lower())):
                dem[w] = dem.get(w, 0) + 1
        cam = [w for w, n in dem.items() if n >= 3 and w not in _BO_QUA]
        y = a.y or f"a fresh everyday moment in the {ph}"
        print(f"\n▶ {hs['ten']} tập {so:03d} · {a.giay:g}s · {ph} · {lt} lật · {ki[:34]}…")
        tap = sinh_tap(a.kenh, y, a.giay, tranh=[x["title"] for x in da], phong=ph, lat=lt,
                       kieu=ki, cam_tu=cam)
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
