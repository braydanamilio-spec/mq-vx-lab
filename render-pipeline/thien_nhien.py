#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MƯỜI KÊNH THIÊN NHIÊN — short 8–10 giây, MỘT cú máy, không lời đọc  (2/9/2026)

VÌ SAO ĐÂY LÀ BỘ RIÊNG, KHÔNG PHẢI KÊNH KLING THỨ 31
-----------------------------------------------------
Bộ Kling hài (`kling_kenh.py`) dựng quanh: dàn vai khoá hình · phòng cố định · đồ vật gây mâu
thuẫn · thoại Mỹ · cú lật. Bộ này KHÔNG có thứ nào trong đó. Dùng chung engine thì mọi thước của
bên kia đều báo sai, và mỗi bản sửa một bên làm hỏng bên kia — đúng cảnh báo ở CLAUDE.md §10.

Nhưng nó KHÔNG viết lại từ đầu: `kling_studio.py` đã có bảng chụp + luật ghim góc máy, và
`kling_lo.py` đã có ghép clip + nhạc + chuẩn âm + QC + đẩy kho. Bộ này cắm vào đúng hai chỗ ấy.

VÌ SAO THIÊN NHIÊN LÀ THỨ HỢP KLING NHẤT TRONG CẢ NĂM BỘ
---------------------------------------------------------
`kling_studio.py` đã ghi ra, từ lần thử thật 09/08:

    mạnh : một chủ thể rõ · một hành động rõ · khí quyển, khói, ánh sáng, chuyển động chậm
           · ĐỘNG VẬT · đồ vật · vật lý siêu thực
    yếu  : chữ đọc được · mặt người cận cảnh · bàn tay · thoại/khớp miệng · đám đông nhanh

Bộ thiên nhiên không chạm vào MỘT chỗ yếu nào: không chữ, không mặt người, không bàn tay, không
thoại. Nó đứng trọn trong phần mạnh. Đây là lý do kỹ thuật để làm bộ này, không phải vì đề tài
đang hot.

BA RÀNG BUỘC CỨNG, VÀ CẢ BA ĐỀU CÓ CỔNG
----------------------------------------
1. **Không bao giờ trình bày như phim tư liệu thật.** Đây là cảnh DỰNG bằng AI. Kênh nói rõ điều
   đó ở mô tả và ở watermark. Trình bày cảnh AI như tư liệu động vật thật là khai man, và nó
   cũng chính là dạng bị gỡ nhanh nhất trong ngách này.
2. **Săn mồi được, máu me thì không.** Cho xem KHOẢNH KHẮC LAO TỚI, không cho xem hậu quả. Không
   máu, không vết thương, không xác bị xé. `CAM_MAU` chặn ở khâu viết.
3. **Một chủ thể, một hành động, máy ghim cứng.** Kling trôi thành cảnh drone khi không ghim, và
   vẽ sai giải phẫu khi con vật cử động nhanh và phức tạp. Nên ưu tiên chậm và đơn.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
KHO = os.path.join(GOC, "out", "thien_nhien")

# Trần ký tự của Kling. Cùng con số, cùng nguồn, cùng bài học đã trả giá ở bộ hài (13.1):
# "2.500" không phải một giới hạn, nó là một con số — giới hạn là "2.500 KÝ TỰ".
KY_TU_MAX = 2500
KY_TU_MIN = 900

# Độ dài. Anh chốt short 8–10 giây một cú máy: 1 lượt Kling mỗi video, cùng kinh tế với bộ hài.
GIAY_CHUAN = (8, 9, 10)
GIAY_UU_TIEN = (8, 10)

# ── SÀN TAY NGHỀ — mọi kênh dùng chung, và giống nhau ở đây là ĐÚNG ────────────────────────
# Cắt khối này ra trước khi đo trùng giữa các kênh (bài học 13.4: hỏi "phần nào giống nhau là
# đúng" rồi cắt, trước khi đo).
# ỐNG KÍNH THEO KHUÔN HÌNH, không phải một hằng số.
#
# 2/9 — Bản đầu ghép một câu tele duy nhất vào mọi prompt, và nó rơi vào cả những cảnh DƯỚI
# NƯỚC: "long telephoto lens from a great distance" đứng ngay cạnh "camera locked underwater at
# depth, level with the animal". Hai lệnh trái nhau trong cùng một prompt, và Kling sẽ chọn một
# bên. Đúng họ lỗi 12.5: một câu luật đúng ở ngữ cảnh sinh ra nó, sai ở ngữ cảnh mới.
ONG_KINH = {
    "xa": ("Long telephoto from a great distance, the way real wildlife is filmed: shallow depth of "
           "field, the animal sharp, the background dissolved into soft bands of colour."),
    "nuoc": ("Wide lens in an underwater housing, close to the subject because water eats contrast "
             "over distance: surface light only, visible particles, no artificial lamp."),
    "macro": ("Macro lens very close in: depth of field a few millimetres deep, so one detail is "
              "sharp and everything just behind it is already soft."),
}


def ong_kinh(khuon: str, moi_truong: str = "tren") -> str:
    """Ống kính theo KHUÔN HÌNH *và* MÔI TRƯỜNG.

    2/9 — Bản trước chỉ nhìn tên khuôn, nên khuôn "extreme slow motion" ở dưới băng vẫn nhận câu
    "long telephoto from a great distance" — không ai quay tele dưới nước. Đây là lần thứ ba câu
    ống kính sai vì thiếu ngữ cảnh (lần một: một hằng số cho mọi cảnh; lần hai: theo khuôn nhưng
    quên môi trường). Cứ mỗi lần thiếu một chiều là lại sai ở đúng chỗ chiều ấy quyết định.
    """
    if khuon.startswith("macro"):
        return ONG_KINH["macro"]
    if moi_truong == "duoi" or khuon.startswith("underwater") or khuon.startswith("split level"):
        return ONG_KINH["nuoc"]
    return ONG_KINH["xa"]
SAN_CHUYEN_DONG = (
    "One continuous locked shot. If the animal leaves the frame, the frame stays where it is."
)
SAN_THAT = (
    "Photoreal, documentary-grade. Anatomy exactly right for the species: limb count, joints, eye "
    "placement, and fur or feathers lying the way they lie on a live animal."
)

# ── HÀNG RÀO DO NOT — khối cuối của mọi prompt, không bao giờ được cắt ─────────────────────
RAO = (
    "DO NOT:",
    "No text, letters, numbers, captions, watermarks, logos or signage anywhere in the frame.",
    "No people, no human faces, no hands, no boats, no buildings, no vehicles unless named above.",
    "No camera movement of any kind: no pan, tilt, zoom, dolly, handheld, drone or orbit.",
    "No blood, no wounds, no torn flesh, no carcass, no visible kill. The strike may begin; it "
    "never lands on screen.",
    "No cartoon styling, no CGI sheen, no plastic fur, no glowing eyes, no invented species.",
    "No cuts. This is ONE unbroken shot of exactly {g} seconds.",
)
CAU_CHOT_RAO = "No cuts. This is ONE unbroken shot of exactly {g} seconds."

# ── CỔNG: máu me · chữ · người · nhân hoá · trôi máy ───────────────────────────────────────
# Cấm bằng BIỂU THỨC, không bằng danh sách ví dụ — bài học 13.20: một danh sách chuỗi con không
# bắt được ngôn ngữ, "sign reads" chỉ là một cách viết trong mười cách.
CAM_MAU = re.compile(
    r"\b(blood\w*|bleed\w*|bloody|gore|gory|wound\w*|injur\w*|carcass\w*|corpse\w*|"
    r"entrails?|guts?|viscera|dismember\w*|tear\w* (?:apart|into)|\brips?\b|\bripped\b|\bripping\b|"
    r"devour\w*|feast\w* on|eating (?:the|its) (?:kill|prey)|dead \w+ (?:body|animal))\b", re.I)
CAM_CHU = re.compile(
    r"\b(text|letter\w*|word\w*|caption\w*|subtitle\w*|label\w*|sign\w*|logo\w*|watermark\w*|"
    r"number\w* (?:on|across)|writing|written|spell\w* out|read\w* ['\"])\b", re.I)
CAM_NGUOI = re.compile(
    r"\b(person|people|human\w*|man|woman|child\w*|hand\w*|finger\w*|face of a|diver\w*|"
    r"photographer\w*|researcher\w*|crew|boat\w*|ship\w*|kayak\w*|drone\w*)\b", re.I)
# BA LẦN CÙNG MỘT LỖI BIỂU THỨC trong một buổi, nên ghi thẳng ở đây:
#   `rip\w* (apart|open)` nuốt "ripple Open"   ·  `grin\w*` nuốt "grinding"
#   `hand\w*` nuốt "a hand's width" / "a hand deep"
# Một GỐC TỪ NGẮN cộng `\w*` là một cái bẫy: nó nuốt những từ không cùng nghĩa mà chỉ tình cờ
# cùng bốn chữ cái đầu. Với gốc dưới năm ký tự, phải liệt kê các dạng thật (grins/grinned/
# grinning) thay vì dùng `\w*`. Cùng họ với 13.22: một chữ có hai nghĩa là chữ không làm cổng
# được — ở đây là hai chữ KHÁC NHAU tình cờ chung phần đầu.
CAM_NHAN_HOA = re.compile(
    r"\b(smil\w*|grins?|grinned|grinning|laugh\w*|wink\w*|wav\w* (?:hello|goodbye)|wearing|dressed|hat|scarf|"
    r"glasses|shoes|talk\w*|speak\w*|say\w*|sings? a|dance\w* like|hugs?|waves? at)\b", re.I)
GHIM_MAY = ("locked", "static", "fixed camera", "tripod", "telephoto", "macro", "wide shot",
            "close shot", "underwater housing", "low angle", "eye level", "high angle")
# Máy CHUYỂN ĐỘNG — thứ trôi mạnh nhất của Kling, và hàng rào đã cấm. Bắt luôn ở khâu viết để
# đừng tiêu một lượt sinh clip cho một prompt tự mâu thuẫn với hàng rào của chính nó.
CAM_TROI = re.compile(
    r"\b(pan\w*|tilt\w*|zoom\w*|dolly\w*|track\w+ shot|orbit\w*|fly\w*(?:over|ing) (?:over|across)|"
    r"drone shot|aerial|crane shot|handheld|steadicam|push\w* in|pull\w* back|camera follows?)\b", re.I)
# Giải phẫu hỏng: Kling vẽ sai khi con vật cử động NHANH và PHỨC TẠP. Đo được ở bộ hài rằng cấm
# một khái niệm phải bằng biểu thức; ở đây khái niệm là "nhiều thứ cùng động rất nhanh".
# Tạo hình KIỂU PHIM. Ngách tiền sử hỏng ở đúng chỗ này: mô hình đã học hàng triệu khung phim
# khủng long, nên không ghim thì nó vẽ ra một con quái vật gầm vào ống kính chứ không phải một
# con vật đang uống nước. Ngoài chuyện xấu, nó còn là rủi ro bản quyền — tạo hình của một hãng
# phim là tài sản của hãng ấy.
CAM_PHIM = re.compile(
    r"\b(jurassic|godzilla|king kong|cinematic|movie|film[- ]?like|blockbuster|epic shot|"
    r"roar\w*|rearing up|menacing|terrifying|monster|creature feature|dramatic lighting|"
    r"lit from below|slow[- ]motion menace)\b", re.I)
CAM_NHANH = re.compile(
    r"\b(sprint\w*|dash\w*|scrambl\w*|thrash\w*|flail\w*|writh\w*|somersault\w*|barrel roll|"
    r"frantic\w*|chaotic\w*|swarm\w* over|tumbl\w* over each other)\b", re.I)

# ── MƯỜI KHUÔN HÌNH TƯ LIỆU — trục dùng chung, tất cả đều KHOÁ CỨNG ────────────────────────
# Bài học 14.9 của bộ hài, áp ngay từ đầu ở bộ này: nếu không cấp khuôn hình theo lịch thì mọi
# tập của mọi kênh ra cùng một cú máy, và đó là thứ người xem thấy TRƯỚC cả nội dung. Ở đây nó
# còn quan trọng hơn, vì clip không lời thì HÌNH là toàn bộ sản phẩm.
KHUON = (
    ("long lens full body",
     "Locked telephoto shot from far away, the whole animal small inside a vast empty frame, "
     "background compressed into flat bands."),
    ("long lens tight",
     "Locked long-lens shot filling the frame with the animal's head and shoulders, everything "
     "behind it dissolved to soft colour."),
    ("ground level low angle",
     "Camera locked at ground level, lens almost touching the surface, the animal rising huge "
     "against the sky."),
    ("split level half under water",
     "Camera locked at the waterline in an underwater housing, the frame cut in half: air and "
     "light above, green-blue water below."),
    ("underwater looking up",
     "Camera locked underwater below the animal, looking up toward the bright surface, the animal "
     "a dark shape against the light."),
    ("underwater side on",
     "Camera locked underwater at depth, level with the animal, blue falling away to black behind "
     "it."),
    ("extreme slow motion",
     "Locked shot at very high frame rate so one single movement unfolds slowly, every droplet "
     "and every muscle readable."),
    ("backlit silhouette",
     "Locked shot into a low sun, the animal a clean black silhouette, breath and spray lit like "
     "smoke."),
    ("cliff edge looking down",
     "Camera locked on a cliff edge looking steeply down at the water below — a fixed vantage "
     "point on solid rock, and the camera never leaves that point."),
    ("macro detail",
     "Locked macro shot on one small part of the animal — an eye, a tusk, a feather, frost on "
     "fur, breath condensing — filling the whole frame."),
)

# KHUÔN HÌNH quay được ở MÔI TRƯỜNG nào. Bảng này là thứ ngăn "máy đặt dưới nước nhìn lên" ghép
# với "trượt xuống sống băng", và "cận cực đại" ghép với "lao lên khỏi mặt nước".
KHUON_MOI_TRUONG = {
    "long lens full body":          ("tren", "mep"),
    "long lens tight":              ("tren", "mep"),
    "ground level low angle":       ("tren", "mep"),
    "split level half under water": ("mep",),
    "underwater looking up":        ("duoi",),
    "underwater side on":           ("duoi",),
    "extreme slow motion":          ("tren", "mep", "duoi"),   # cỡ nào cũng được, chỉ đổi tốc độ
    "backlit silhouette":           ("tren", "mep"),
    "cliff edge looking down":      ("tren", "mep"),
    "macro detail":                 ("tren", "mep", "duoi"),   # thêm ràng buộc MACRO_OK bên dưới
}

# Khuôn hình nào TỰ QUY ĐỊNH ánh sáng thì khối LIGHT không được nói thêm.
#
# 2/9 — "backlit silhouette" đã ghi trong câu máy là *"locked shot into a low sun"*, rồi khối
# LIGHT nói tiếp *"hard high sun, small black shadows directly under everything"*. Hai lệnh trái
# nhau, và Kling sẽ chọn một bên. Chữa bằng cách để khuôn hình GIỮ ánh sáng của nó, thay vì thêm
# một bảng loại trừ nữa — đây đã là lần thứ sáu cùng một họ lỗi trong tệp này.
KHUON_TU_SANG = frozenset({"backlit silhouette"})

# ── TRỤC ÁNH SÁNG ─────────────────────────────────────────────────────────────────────────
ANH_SANG = (
    "low dawn sun raking across everything, long blue shadows",
    "flat white overcast, no shadows at all, the light coming from the whole sky",
    "hard high sun, small black shadows directly under everything",
    "golden hour, the light orange and almost horizontal",
    "blue hour after sunset, the world dim blue and the sky still bright",
    "polar twilight under a low moon, everything silver and nearly monochrome",
    "shafts of sunlight cutting down through the water in visible columns",
    "storm light: dark sky, one bright band on the horizon lighting the subject",
)

# ── TRỤC NƯỚC / THỜI TIẾT ─────────────────────────────────────────────────────────────────
THOI_TIET = (
    "water like glass, not one ripple",
    "heavy slow swell lifting and dropping everything",
    "driving snow moving sideways across the frame",
    "a fog bank sitting on the water, edges of things dissolving",
    "loose pack ice, plates of it knocking together",
    "rain stippling the surface into a million points",
    "still freezing air with frost smoke lifting off open water",
    "wind tearing spray off the tops of the waves",
)

# Hành vi CHẬM / TĨNH — chỉ những hành vi này mới quay được bằng khuôn cận cực đại.
# Tách riêng khỏi trục môi trường vì đây là hai thuộc tính khác nhau: môi trường quyết
# định máy đặt ở đâu, còn chậm/nhanh quyết định cỡ ảnh nào đọc được. Một cú lao lên khỏi
# mặt nước không thể quay macro, dù nó ở đúng môi trường.
MACRO_OK = frozenset({
    "blowing air into its fur so the coat lifts and fluffs around the face",
    "hovering just above the seabed with the fins moving very slowly",
    "standing at the edge of the trees with both eyes returning the light",
    "sitting still on the bank with water beading on the down",

    "changing the shape of its melon forehead while hanging still",
    "crouched motionless in a form pressed into grass with its ears flat along its back",
    "flushing dark red to translucent pale and back",
    "hanging perfectly still with tentacles spread in a wide net",
    "hanging still with a row of tiny blue lights along its underside",
    "holding still on the rock with its head turned to the sea",
    "lifting its head as spray lands on it and putting it down again",
    "lifting its head slowly and lowering it again",
    "lying on the ice with its body curved into a banana shape",
    "lying still on a boulder while water runs past on both sides",
    "raising its head and holding a scent on the wind",
    "sitting down in blowing snow and curling its tail over its feet",
    "sitting on a post and turning the white face toward the camera",
    "sleeping curled with its nose tucked under a paw while snow settles on it",
    "standing at the edge of the rock in the spray without moving",
    "standing unsteady in wind with its down lifting in patches",
    "standing upright with its feathers flattened by the wind",
    "tucking the bill under a wing while the feathers are flattened by wind",
    "turning a single huge black eye toward the camera",
    "washing its face with both forepaws",
})

# ══════════════════════════════════════════════════════════════════════════════════════════
# MƯỜI KÊNH. Mỗi kênh = MỘT THẾ GIỚI (bản sắc hình) × MỘT CƠ CHẾ HOOK (lý do không lướt qua).
#
# Bài học 14.1 áp ngay từ đầu: thêm mười con vật khác nhau KHÔNG phải là mười kênh khác nhau.
# Mười kênh dưới đây khác nhau ở chỗ VÌ SAO người ta dừng ngón tay, không chỉ ở loài nào.
# ══════════════════════════════════════════════════════════════════════════════════════════
KENH: dict[str, dict] = {

    "ICE BEAR": {
        "ten": "ICE BEAR",
        "mo_ta": "Gấu Bắc Cực trên băng trôi — cuộc săn dài trong im lặng trắng.",
        "hook": (
            "A single dark animal in an enormous white nothing, doing something with total "
            "patience. The viewer stops because they cannot tell yet what it is waiting for."
        ),
        "anh_sang_cam": ("through the water",),
        "thoi_tiet_cam": ("rain stippling",),
        "the_gioi": (
            "The pack ice off Svalbard in late spring: flat white floes split by black leads of "
            "open water, pressure ridges of blue ice, no land in sight and no sound but wind."
        ),
        "loai": {
            "polar bear": (
                "An adult polar bear: cream-yellow fur stained slightly at the neck, black nose, "
                "black eyes, black lips, huge flat paws, heavy shoulders that roll when it walks."
            ),
            "bear cub": (
                "A polar bear cub of the year, half the height of its mother, fur brighter white, "
                "clumsy on the ice, always within one body length of her."
            ),
            "ringed seal": (
                "A ringed seal: small, grey with pale rings on its back, huge dark eyes, hauled "
                "out beside a breathing hole in the ice."
            ),
            "arctic fox": (
                "An arctic fox in winter coat: pure white, very small, short muzzle, thick tail "
                "almost as long as its body, following at a distance."
            ),
        },
        "hanh_vi": {
            "polar bear": {
                "tren": (
                    "waiting motionless beside a breathing hole in the ice",
                    "shaking a whole coat of water off in one violent shudder",
                    "testing thin ice with one forepaw before putting weight on it",
                    "lying flat and pushing itself forward across the ice on its belly",
                    "walking a straight line across a floe toward something out of frame",
                    "standing up on its hind legs to see further",
                    "digging at compacted snow with both forepaws",
                    "raising its head and holding a scent on the wind",
                    "sleeping curled with its nose tucked under a paw while snow settles on it",
                ),
                "mep": (
                    "swimming between two floes with only the head above water",
                    "climbing out of black water onto a floe edge",
                ),
            },
            "bear cub": {
                "tren": (
                    "sliding down a pressure ridge on its side",
                    "following in a much larger set of tracks and stepping into each print",
                    "standing up on its hind legs and immediately overbalancing",
                    "pressing itself against a much larger body that is out of frame",
                ),
            },
            "ringed seal": {
                "tren": (
                    "hauling out beside a breathing hole and lifting its head every few seconds",
                    "lying on the ice with its body curved into a banana shape",
                ),
                "mep": (
                    "slipping into a hole in the ice in one movement and vanishing",
                ),
            },
            "arctic fox": {
                "tren": (
                    "trotting along a line of bear tracks with its tail streaming behind",
                    "digging into a snowdrift until only its hindquarters show",
                    "sitting down in blowing snow and curling its tail over its feet",
                ),
            },
        },
        "khuon_cam": ("underwater side on", "cliff edge looking down"),
        "style": (
            "Almost no colour: white, off-white, and one black shape. The only saturation in the "
            "whole frame is the blue inside a crack in the ice. Grain fine, contrast low, the "
            "highlights soft the way overexposed snow really is."
        ),
        "am": "wind over flat ice, ice creaking, water lapping in a lead, breath",
        "luat": (
            "The bear is never violent on screen and never catches anything. Whatever it is "
            "hunting stays out of frame.",
            "There is no land, no vegetation, no building and no vessel anywhere in this world.",
        ),
    },

    "THE POD": {
        "ten": "THE POD",
        "mo_ta": "Cá voi sát thủ — nhiều cái đầu cùng nghĩ một điều, thấy được bằng mắt.",
        "hook": (
            "Several animals move as if one mind is running all of them, and the coordination is "
            "visible in the first second. The viewer stops to work out who is deciding."
        ),
        "thoi_tiet_cam": ("loose pack ice",),
        "anh_sang_duoi": (
            "green water with the surface a bright ceiling above",
            "shafts of light coming down through the surface in visible columns",
            "flat green gloom with visibility only a few metres",
            "bright surface light scattered by a thin layer of plankton",
        ),
        "the_gioi": (
            "Cold coastal water off a steep dark shore: deep green-black sea, kelp on the rocks, "
            "low grey cloud sitting on the headlands, the surface breaking over hidden reefs."
        ),
        "loai": {
            "pacific white-sided dolphin": (
                "A Pacific white-sided dolphin: sharply hooked dorsal fin, dark grey back, pale grey flank "
                "stripes sweeping back like brushstrokes, white belly, short blunt beak."
            ),
            "orca bull": (
                "An adult male orca: glossy black back, sharp white eye patch, white chin and "
                "belly, grey saddle behind the fin, dorsal fin nearly two metres tall and straight."
            ),
            "orca female": (
                "An adult female orca: same black and white pattern, dorsal fin shorter and "
                "curved back like a sickle, body more slender."
            ),
            "orca calf": (
                "An orca calf: markings the same but the white areas faintly orange, small enough "
                "to swim in the pressure wave beside an adult's flank."
            ),
            "sea lion": (
                "A Steller sea lion: pale tawny fur darkening when wet, blunt heavy head, small "
                "external ears, on a rock at the edge of the water."
            ),
        },
        "hanh_vi": {
            "pacific white-sided dolphin": {
                "mep": (
                    "leaping clear in a low flat arc and re-entering without a splash",
                    "surfacing in a fast line so the fins break the water one after another",
                ),
                "duoi": (
                    "riding the pressure wave off a much larger flank",
                    "turning in unison with a dozen others so the pale flank stripes all flash at once",
                    "swimming upside down just beneath the silver of the surface",
                ),
            },
            "orca bull": {
                "tren": (
                    "surfacing so the tall dorsal fin rises first and goes under last",
                    "slapping the surface once with the tail fluke",
                ),
                "mep": (
                    "spy-hopping straight up, holding, and sliding back down without a splash",
                    "breaching clear of the water and landing on one side",
                ),
                "duoi": (
                    "hanging vertical and motionless in the water column",
                    "swimming inverted just under the surface showing the white belly",
                    "rising through a shaft of light with the rest of the pod behind it in silhouette",
                ),
            },
            "orca female": {
                "tren": (
                    "turning as one body at the same instant as the animals beside it",
                    "moving in single file along the edge of a kelp bed",
                    "breaking formation and circling wide",
                    "pushing a bow wave ahead of a calf so the calf is carried",
                    "surfacing in line abreast so the blows fire at once",
                ),
                "duoi": (
                    "passing directly beneath the camera with others following in order",
                ),
            },
            "orca calf": {
                "tren": (
                    "copying an adult spy-hop and getting the timing wrong",
                    "surfacing a half-beat after the animal beside it",
                ),
                "duoi": (
                    "swimming in the pressure wave beside a much larger flank",
                    "rolling completely over and righting itself",
                ),
            },
            "sea lion": {
                "tren": (
                    "watching from a rock as dark shapes pass offshore",
                    "holding still on the rock with its head turned to the sea",
                ),
                "mep": (
                    "slipping off a rock into the water and disappearing",
                ),
            },
        },
        "khuon_cam": ("ground level low angle", "macro detail"),
        "style": (
            "Hard black against hard white, in a world of deep green. No warm tones anywhere. "
            "Water surface reads as polished stone. The shapes are graphic — the animals look "
            "designed rather than grown, and the frame is built around that."
        ),
        "am": "blows, water sheeting off a fin, distant clicks and whistles, swell on rock",
        "luat": (
            "No hunt is ever completed on screen. Prey animals may appear, but the moment of "
            "contact is never shown.",
            "The pod is never in distress, never stranded, never entangled.",
        ),
    },

    "BLUE GIANT": {
        "ten": "BLUE GIANT",
        "mo_ta": "Cá voi lưng gù — kênh về KÍCH THƯỚC: một cơ thể lớn tới mức khó tin.",
        "hook": (
            "Something impossibly large moves slowly through the frame, and there is always a "
            "small familiar thing beside it so the size lands. The viewer stops because the scale "
            "does not compute."
        ),
        "thoi_tiet_cam": ("loose pack ice", "driving snow", "frost smoke"),
        "anh_sang_duoi": (
            "deep blue falling away to black below, the surface a distant bright plane",
            "shafts of sunlight cutting down through the water in visible columns",
            "even blue light with no direction to it at all",
            "the surface above lit and everything beneath it in shadow",
        ),
        "the_gioi": (
            "Open ocean far from any coast: deep blue water going black underneath, a horizon with "
            "nothing on it, long ocean swell, and clouds of krill hanging in the upper water."
        ),
        "loai": {
            "sperm whale": (
                "A sperm whale: a vast squared-off blunt head taking up a third of the whole "
                "body, dark wrinkled grey skin like old bark, a narrow underslung jaw, one "
                "blowhole set to the left at the very front, and a low ridge instead of a fin."
            ),
            "whale shark": (
                "A whale shark: an enormous flattened head, a wide straight mouth right across the front, "
                "dark blue-grey skin patterned with a grid of white spots and pale stripes, five long "
                "gill slits."
            ),
            "humpback": (
                "An adult humpback whale: dark grey-black back, white grooved throat pleats, very "
                "long white pectoral fins scalloped along the front edge, knobbly tubercles on the "
                "head, barnacle clusters on the chin and fluke edges."
            ),
            "blue whale": (
                "An adult blue whale: enormous slate-blue body mottled with paler grey, a very "
                "small dorsal fin set far back near the tail, a broad flat U-shaped head with one "
                "ridge down the middle, long throat grooves running the length of the belly."
            ),
            "humpback calf": (
                "A humpback calf: same shape at one third the length, skin smoother and paler, "
                "always riding just above and behind its mother's head."
            ),
            "sardine school": (
                "A dense school of sardines: thousands of small silver fish turning together, "
                "flashing from silver to dark as the whole shape rotates."
            ),
            "shearwater": (
                "A shearwater: narrow dark wings held stiff, gliding a few centimetres above the "
                "water, tiny against everything else in frame."
            ),
        },
        "hanh_vi": {
            "sperm whale": {
                "duoi": (
                    "hanging completely vertical and motionless, head up, fast asleep",
                    "turning its enormous squared head slowly toward the camera",
                    "sinking tail-first into the dark without moving a muscle",
                    "gliding past with the wrinkled skin catching the light like old bark",
                ),
                "mep": (
                    "blowing a low bushy spout angled forward and to the left",
                    "lifting the broad triangular fluke straight up before a long dive",
                ),
            },
            "whale shark": {
                "mep": (
                    "swimming just under the surface with the tip of the dorsal fin cutting the water",
                ),
                "duoi": (
                    "cruising forward with the mouth held wide open and the gill slits pulsing",
                    "turning slowly so the grid of white spots wraps around the body",
                    "rising through a shaft of light with small fish holding station under its chin",
                ),
            },
            "humpback": {
                "tren": (
                    "lifting one enormous pectoral fin clear of the surface and holding it there",
                    "exhaling a column of spray straight up in still air",
                ),
                "mep": (
                    "rolling slowly onto its side so one eye comes above the water",
                    "lifting the fluke straight up and sliding under without a ripple",
                    "cruising just below the surface with the blowhole breaking every few seconds",
                ),
                "duoi": (
                    "rising slowly from below with the mouth closed and the throat pleats flat",
                    "hanging motionless head-down in the water column",
                    "drifting through a shaft of light so the white fins glow",
                    "opening the mouth wide and letting the throat expand, water pouring out through baleen",
                    "moving past the camera so slowly that the body takes the whole shot to cross",
                ),
            },
            "blue whale": {
                "duoi": (
                    "moving through the frame so slowly that the head enters before the tail arrives",
                    "hanging almost still with the throat grooves relaxed and flat",
                    "turning very gradually so the pale mottling catches the light along its flank",
                    "rising toward the surface with the small dorsal fin appearing last",
                    "gliding past a cloud of krill without opening its mouth",
                ),
                "mep": (
                    "exhaling a single column of spray that goes far higher than seems possible",
                    "showing a long stretch of back at the surface with the blowhole closing",
                ),
            },
            "humpback calf": {
                "tren": (
                    "lifting its whole head clear of the water and dropping back",
                ),
                "mep": (
                    "resting at the surface with a much larger body directly beneath it",
                ),
                "duoi": (
                    "riding just above and behind a much larger head",
                    "rolling upside down against an adult flank",
                ),
            },
            "sardine school": {
                "duoi": (
                    "turning together so the whole shape flashes from silver to dark",
                    "opening a clean hole as something large passes through",
                    "compressing into a tight ball and holding it",
                ),
            },
            "shearwater": {
                "tren": (
                    "gliding a few centimetres above the swell on stiff wings",
                ),
                "mep": (
                    "landing on the water and sitting low among the swell",
                ),
            },
        },
        "khuon_cam": ("ground level low angle", "cliff edge looking down"),
        "style": (
            "Deep saturated blue that gets darker toward the bottom of every frame. The whale is "
            "always the darkest thing and always crosses more of the frame than feels possible. "
            "Particles and marine snow in the water give the scale away."
        ),
        "am": "low distant song, water moving over a huge body, one blow, deep pressure hum",
        "luat": (
            "There is never a boat, a diver, a net or a rope in this world.",
            "The whale is never beached, never entangled, never injured.",
        ),
    },

    "PENGUIN ROAD": {
        "ten": "PENGUIN ROAD",
        "mo_ta": "Chim cánh cụt Nam Cực — hàng nghìn cơ thể giống hệt nhau chịu cái lạnh cùng nhau.",
        "hook": (
            "A crowd of identical bodies where exactly one is doing something different. The "
            "viewer stops to find the odd one, and by then they have watched three seconds."
        ),
        "anh_sang_cam": ("through the water",),
        # Đàn ở trên BĂNG LIỀN BỜ, không có mặt nước hở trong khung: sóng lừng, bọt sóng và
        # "mặt nước phẳng như gương" đều là trạng thái của một thế giới khác.
        "thoi_tiet_cam": ("rain stippling", "heavy slow swell", "tearing spray", "like glass"),
        "the_gioi": (
            "A colony on Antarctic sea ice at the foot of a glacier front: dirty trodden snow, "
            "hard blue ice cliffs behind, a long worn path between the colony and the water's "
            "edge, and wind that never stops."
        ),
        "loai": {
            "gentoo penguin": (
                "A gentoo penguin: black back, white front, a bright orange bill and orange feet, and a "
                "clean white patch above each eye meeting across the crown."
            ),
            "emperor penguin": (
                "An adult emperor penguin: black head and back, white belly, a bright yellow-orange "
                "flash on each side of the neck fading into pale yellow on the chest, dense feather "
                "coat, standing just over a metre tall."
            ),
            "emperor chick": (
                "An emperor chick: round body in soft grey down, black head with a white face "
                "mask, standing on its own feet and unsteady in wind."
            ),
            "adelie penguin": (
                "An adelie penguin: smaller, plain black head with a white ring around the eye, "
                "sharp black-and-white edge at the throat, walks with a pronounced side-to-side roll."
            ),
            "skua": (
                "A south polar skua: heavy brown gull-like bird with pale wing flashes, standing "
                "at the edge of the colony watching."
            ),
        },
        "hanh_vi": {
            "gentoo penguin": {
                "tren": (
                    "running downhill with both flippers held out for balance",
                    "picking up a small stone and carrying it away in its bill",
                    "standing with the orange feet planted wide against the wind",
                    "stretching one flipper and one foot straight out behind at the same time",
                ),
            },
            "emperor penguin": {
                "tren": (
                    "leaning into a wind that flattens the feathers along one whole side",
                    "shuffling forward inside a tight huddle so the outside birds rotate inward",
                    "tobogganing on its belly across ice, pushing with both feet",
                    "standing at the ice edge looking down at the water without going in",
                    "walking a single-file line worn into the snow by thousands of feet",
                    "bowing and stretching the neck straight up in one slow movement",
                    "sheltering a chick on its feet under a fold of belly skin",
                    "standing completely still while blowing snow streams past it",
                ),
                "mep": (
                    "porpoising out of the water and landing on its feet on the ice",
                ),
            },
            "emperor chick": {
                "tren": (
                    "standing unsteady in wind with its down lifting in patches",
                    "pushing its head into an adult belly fold",
                    "sitting down abruptly on the ice",
                    "shivering with both flippers held out from the body",
                ),
            },
            "adelie penguin": {
                "tren": (
                    "walking with a pronounced side-to-side roll",
                    "sliding down a slope out of control and stopping against another bird",
                    "shaking snow out of its feathers in one whole-body shiver",
                    "stepping over a sleeping bird and continuing without pausing",
                ),
            },
            "skua": {
                "tren": (
                    "standing at the edge of the colony with its head turned",
                    "taking off into the wind from a standing start",
                ),
            },
        },
        "khuon_cam": ("underwater side on",),
        "style": (
            "White ground, white sky, and a crowd of black-and-white bodies with two small warm "
            "yellow marks each — the only warm colour in the world. Blowing snow softens "
            "everything at distance. The frame is often nearly abstract: pattern first, animal "
            "second."
        ),
        "am": "constant wind, thousands of calls layered into a wash, feet on hard snow",
        "luat": (
            "No chick is ever shown in distress, taken, or alone in danger. The skua watches and "
            "nothing more.",
            "Nothing dies on screen and no body is ever in frame.",
        ),
    },

    "TUSK": {
        "ten": "TUSK",
        "mo_ta": "Kỳ lân biển dưới băng Bắc Cực — con vật huyền thoại, quay như thật.",
        "hook": (
            "An animal that looks invented is moving in a real place, filmed like real footage. "
            "The viewer stops because the brain refuses it for a second."
        ),
        "anh_sang": (
            "shafts of daylight coming down through cracks in the ice ceiling in hard columns",
            "one round pool of bright light directly under a breathing hole",
            "even blue-green glow coming through thick ice, no direction to it at all",
            "the ice ceiling bright and the water below fading to black",
            "dim under-ice twilight where only the nearest surfaces are readable",
        ),
        "thoi_tiet": (
            "absolutely still water, no current, nothing moving but the animal",
            "a slow current bending the columns of light",
            "loose brash ice grinding together against the ceiling above",
            "a fine haze of ice crystals suspended in the water",
            "small silver domes of trapped air rolling along the underside of the ice",
        ),
        "the_gioi": (
            "Under the arctic sea ice in a fjord: a ceiling of white ice above, blue-green water "
            "below it, shafts of light coming down through cracks and breathing holes, and total "
            "silence."
        ),
        "loai": {
            "walrus": (
                "An adult walrus: a vast wrinkled cinnamon-brown body, thick folds at the neck, a broad "
                "muzzle of stiff whiskers, and two long ivory tusks hanging straight down."
            ),
            "narwhal bull": (
                "An adult male narwhal: mottled grey-and-cream body with no dorsal fin, small "
                "rounded head, and one long straight spiral tusk projecting forward from the upper "
                "left jaw."
            ),
            "narwhal female": (
                "An adult female narwhal: same mottled body, no dorsal fin, no tusk, blunt "
                "forehead, slightly smaller."
            ),
            "beluga": (
                "A beluga whale: pure white, no dorsal fin, a rounded melon forehead that changes "
                "shape, a visible neck crease."
            ),
            "arctic cod": (
                "Arctic cod: small slender silver fish gathered in a loose cloud directly under "
                "the ice ceiling."
            ),
        },
        "hanh_vi": {
            "walrus": {
                "mep": (
                    "hooking both tusks over the edge of the ice and hauling its weight upward",
                    "breathing out at a breathing hole so the whiskers scatter the spray",
                ),
                "duoi": (
                    "hanging vertically in the water with both tusks pointing down into the dark",
                    "sweeping the seabed with its whiskers and lifting a slow cloud of silt",
                    "rising toward a hole in the ice with the tusks leading",
                ),
            },
            "narwhal bull": {
                "mep": (
                    "surfacing into a narrow lead so only the tusk and forehead appear",
                ),
                "duoi": (
                    "rising slowly toward a breathing hole with the tusk leading",
                    "hanging vertically in the water column, tusk pointing straight up",
                    "crossing tusks slowly with another male, the two shapes making an X",
                    "swimming upside down under the ice ceiling",
                    "moving through a shaft of light so the spiral on the tusk becomes visible",
                    "turning on its side and looking directly at the camera with one eye",
                    "exhaling under water so a single silver dome of air rolls along the ice above",
                ),
            },
            "narwhal female": {
                "duoi": (
                    "gliding past below with the whole body in silhouette against the bright ice",
                    "pressing the top of its head against the underside of the ice",
                    "drifting motionless while a cloud of small fish parts around it",
                    "swimming in a tight group where all the bodies point the same way",
                ),
            },
            "beluga": {
                "tren": (
                    "changing the shape of its melon forehead while hanging still",
                    "turning its head to follow the camera",
                ),
                "duoi": (
                    "rising into a pool of light under a breathing hole",
                ),
            },
            "arctic cod": {
                "duoi": (
                    "gathered in a loose cloud directly under the ice ceiling",
                    "parting into two streams around something much larger",
                ),
            },
        },
        "khuon_cam": ("ground level low angle", "backlit silhouette", "cliff edge looking down"),
        "style": (
            "A ceiling instead of a sky: every frame has white ice above and dark water below, and "
            "the light comes down in hard columns. Palette is ice white, deep teal and the warm "
            "ivory of the tusk. Everything moves slowly because there is no hurry under there."
        ),
        "am": "muffled under-ice tone, ice groaning, a distant series of clicks, one blow at a hole",
        "luat": (
            "The tusk is a straight left-side spiral and never glows, never bends, never doubles "
            "except on the rare two-tusked bull, and never touches the camera.",
            "No hunt, no predator, no blood, no ice collapse. This world is calm.",
        ),
    },

    "SEAL ROCK": {
        "ten": "SEAL ROCK",
        "mo_ta": "Sư tử biển và hải cẩu ở mép sóng — nơi đất liền kết thúc và mọi thứ tranh nhau.",
        "hook": (
            "A crowded ledge and a wall of white water arriving, and one animal is in the wrong "
            "place. The viewer stops because the collision is obviously coming."
        ),
        "thoi_tiet_cam": ("loose pack ice", "frost smoke"),
        "anh_sang_duoi": (
            "green water full of suspended sand stirred up by the surge",
            "sunlight broken into moving nets of light on the rock below",
            "flat green light with kelp shadows moving across everything",
            "the surface churning white above and broken light beneath it",
        ),
        "the_gioi": (
            "A black volcanic rock shelf on a cold Pacific coast: kelp beds combing back and forth "
            "in the surge, white water breaking over the outer rocks, spray hanging in the air, "
            "and green swell rising against the ledge."
        ),
        "loai": {
            "sea otter": (
                "A sea otter: dense chocolate fur holding silver air bubbles, a pale grizzled face, small "
                "round ears, a thick tapered tail, floating high on its back."
            ),
            "sea lion bull": (
                "A bull Steller sea lion: massive, pale tawny, a thick muscular neck with a mane "
                "of coarser fur, blunt heavy head, small rolled external ears."
            ),
            "sea lion pup": (
                "A sea lion pup: dark chocolate fur when wet, huge eyes, thin neck, moves in "
                "awkward hops on its front flippers."
            ),
            "harbour seal": (
                "A harbour seal: small, mottled grey with dark spots, no external ears, rounded "
                "head, cannot rotate its hind flippers so it moves on land like a caterpillar."
            ),
            "kelp gull": (
                "A kelp gull: white body, black back, yellow bill with a red spot, standing at the "
                "edge of the rock in the spray."
            ),
        },
        "hanh_vi": {
            "sea otter": {
                "tren": (
                    "hauled out on a rock working the fur of its chest with both forepaws",
                    "blowing air into its fur so the coat lifts and fluffs around the face",
                ),
                "mep": (
                    "floating on its back with a stone balanced on its chest",
                    "rolling over once in the water and coming up facing the other way",
                    "wrapping itself in a strand of kelp and going completely still",
                ),
                "duoi": (
                    "diving straight down and vanishing into the kelp",
                ),
            },
            "sea lion bull": {
                "tren": (
                    "throwing the head back and holding the mouth open with no sound in frame",
                    "sliding backwards down wet rock and recovering",
                    "pushing through the crowd to a specific spot and settling exactly there",
                ),
                "mep": (
                    "bracing flat against the rock as a wave washes completely over it",
                    "launching off a ledge into a rising swell",
                    "hauling out by timing one surge and heaving up in a single movement",
                    "hanging vertically in the surge with only the nose above water",
                ),
                "duoi": (
                    "riding the steep front of a green wave just under the surface",
                ),
            },
            "sea lion pup": {
                "tren": (
                    "hopping awkwardly on its front flippers across wet rock",
                    "sleeping stacked against a dozen other bodies, all rising and falling together",
                    "shaking the whole head so water flies off the whiskers",
                    "slipping off a low ledge and climbing straight back",
                ),
            },
            "harbour seal": {
                "tren": (
                    "moving up the rock like a caterpillar in a series of humps",
                    "lying still on a boulder while water runs past on both sides",
                ),
                "mep": (
                    "floating on its back at the surface with both fore-flippers in the air",
                ),
            },
            "kelp gull": {
                "tren": (
                    "standing at the edge of the rock in the spray without moving",
                    "opening its wings once and closing them again",
                ),
            },
        },
        "khuon_cam": ("underwater looking up",),
        "style": (
            "Wet black rock, white water and one band of kelp green — a hard three-colour world. "
            "Everything is either soaked or about to be. Spray hangs in the air and softens the "
            "background while the foreground stays sharp and dripping."
        ),
        "am": "surf on rock, water draining off stone, barks layered at distance, gulls",
        "luat": (
            "No predator ever arrives. No animal is ever struck by a rock or crushed.",
            "The sea is powerful but nothing is ever in real danger on screen.",
        ),
    },

    "DEEP DARK": {
        "ten": "DEEP DARK",
        "mo_ta": "Biển sâu — những thứ trông như không thể có thật, và có thật.",
        "hook": (
            "Pure black, and then one living thing lights itself up. The viewer stops because "
            "nothing in the frame behaves like anything they have seen."
        ),
        "anh_sang": (
            "no light at all except a slow blue-green pulse from the animal itself",
            "a single steady point of blue light on the body and nothing else",
            "a wave of light running along the body and fading behind it",
            "one brief flash that lights the water for an instant and goes out",
            "a faint continuous glow just strong enough to show the outline",
        ),
        "thoi_tiet": (
            "marine snow falling steadily through the whole frame",
            "water so still that nothing drifts at all",
            "a slow current carrying particles sideways across the frame",
            "a thin cloud of tiny suspended organisms catching the light",
            "absolute stillness, the only movement is the animal",
        ),
        "the_gioi": (
            "The midwater ocean eight hundred metres down: absolute black in every direction, no "
            "surface, no floor, no horizon, marine snow drifting steadily downward through the "
            "frame, and the only light is light the animals make."
        ),
        "loai": {
            "dumbo octopus": (
                "A dumbo octopus: a soft pale-pink body the shape of a small bell, two rounded fins standing "
                "out from the head like ears, short webbed arms held together underneath."
            ),
            "siphonophore": (
                "A siphonophore: a chain of translucent bells and tendrils many metres long, "
                "pulsing along its length, faintly blue where it lights."
            ),
            "jellyfish": (
                "A deep-sea jellyfish: a clear bell with red internal organs visible through it, "
                "long trailing tentacles, rings of blue-green light running around the rim."
            ),
            "squid": (
                "A deep-sea squid: dark red skin that flushes to pale in waves, huge black eye, "
                "eight arms and two long tentacles held tight together."
            ),
            "lanternfish": (
                "A lanternfish: small, silver-black, with a row of tiny blue photophores along the "
                "underside of the body."
            ),
        },
        "hanh_vi": {
            "dumbo octopus": {
                "duoi": (
                    "flapping both ear-like fins once and drifting forward on it",
                    "spreading the webbed arms into a wide umbrella and closing them again",
                    "hovering just above the seabed with the fins moving very slowly",
                    "turning on the spot with only one fin beating",
                ),
            },
            "siphonophore": {
                "duoi": (
                    "pulsing once and gliding forward on the momentum",
                    "running a wave of blue light from one end of the body to the other",
                    "unfolding from a compact shape into a long chain",
                    "trailing a filament twice the length of its own body behind it",
                    "contracting the whole chain in one movement",
                ),
            },
            "jellyfish": {
                "duoi": (
                    "opening a bell wide and closing it in one slow contraction",
                    "rotating slowly on its own axis with no visible effort",
                    "drifting upward through falling marine snow",
                    "running rings of light around the rim of the bell",
                    "hanging perfectly still with tentacles spread in a wide net",
                ),
            },
            "squid": {
                "duoi": (
                    "retracting every arm at once into a tight point",
                    "holding two long tentacles out ahead and drawing them back",
                    "releasing a small cloud of blue light and moving away from it",
                    "flushing dark red to translucent pale and back",
                    "turning a single huge black eye toward the camera",
                ),
            },
            "lanternfish": {
                "duoi": (
                    "turning so the row of lights goes out of view one by one",
                    "drifting upward through falling marine snow",
                    "hanging still with a row of tiny blue lights along its underside",
                ),
            },
        },
        "khuon_cam": ("long lens full body", "ground level low angle", "backlit silhouette",
                      "cliff edge looking down", "split level half under water"),
        "style": (
            "Black is ninety percent of every frame. The only colours are the blue-greens the "
            "animals emit and one deep red that the water swallows. Everything is translucent — "
            "you can see through the animal to the black behind it. No fill light ever."
        ),
        "am": "deep pressure silence, one low sustained tone, a faint tick of falling particles",
        "luat": (
            "There is never a submersible, a light rig, a cable or a diver in frame — the light "
            "always comes from the animal itself.",
            "Nothing is eaten on screen. No blood, and no gore of any kind at this depth.",
        ),
    },

    "NIGHT EYES": {
        "ten": "NIGHT EYES",
        "mo_ta": "Thợ săn ban đêm — thế giới mà mắt người không nhìn thấy.",
        "hook": (
            "Near-total darkness with two points of reflected light in it, and the light is "
            "moving. The viewer stops because something is looking back."
        ),
        "anh_sang": (
            "a low full moon throwing long hard shadows across open ground",
            "no moon at all, the only light a faint glow left in the western sky",
            "moonlight coming through bare branches in broken patches",
            "the last blue minutes before full dark, shapes still readable",
            "mist lying knee-deep and lit from above by the moon",
        ),
        "thoi_tiet": (
            "completely still air, not one blade of grass moving",
            "heavy dew on everything, each stem beaded",
            "a thin ground frost turning the grass grey",
            "fine drizzle hanging rather than falling",
            "a light wind moving the tops of the grass only",
        ),
        "the_gioi": (
            "Temperate forest edge and open meadow on a clear night: bare branches against a sky "
            "that still holds a little light, wet grass, mist lying in the low ground, and a moon "
            "low enough to throw long shadows."
        ),
        "loai": {
            "roe deer": (
                "A roe deer: small and neat, grey-brown winter coat, a white patch on the rump, short "
                "upright ears, and large dark eyes that throw back a flat coin of light."
            ),
            "barn owl": (
                "A barn owl: white heart-shaped face, dark eyes, golden-buff back flecked with "
                "grey, pure white underside, long legs trailing behind in flight."
            ),
            "red fox": (
                "A red fox: rust-orange coat, white throat and belly, black stockings on the legs, "
                "black-backed ears, a thick white-tipped brush."
            ),
            "badger": (
                "A European badger: low heavy grey body, short legs, a white head with two broad "
                "black stripes running back through the eyes."
            ),
            "field mouse": (
                "A wood mouse: sandy brown above, white below, enormous dark eyes, very long thin "
                "tail, sitting up on its hind legs in grass."
            ),
        },
        "hanh_vi": {
            "roe deer": {
                "tren": (
                    "standing at the edge of the trees with both eyes returning the light",
                    "lifting its head and holding completely still",
                    "stepping into the open and stopping mid-stride",
                    "turning its ears independently while the body stays motionless",
                ),
            },
            "barn owl": {
                "tren": (
                    "flying straight toward the camera on completely silent wings and passing overhead",
                    "hovering in one place with the head absolutely still while the body works",
                    "turning its head far past its shoulder without moving its body",
                    "dropping feet-first into deep grass",
                    "landing on a fence post and folding its wings in one movement",
                    "quartering low along a field edge with the head down",
                    "sitting on a post and turning the white face toward the camera",
                ),
            },
            "red fox": {
                "tren": (
                    "standing motionless with one forepaw lifted, ears rotating independently",
                    "pouncing straight up and coming down nose first into deep grass",
                    "walking a fence line with the head down, following one line of scent",
                    "freezing mid-step as something changes in the dark",
                    "stepping out of a hedge shadow into moonlight and stopping there",
                ),
            },
            "badger": {
                "tren": (
                    "digging quickly at the base of a tussock with both forepaws",
                    "walking a well-worn path with the head low",
                    "shaking dew off in one shudder that runs from nose to tail",
                    "carrying a bundle of dry grass in its mouth across open ground",
                ),
            },
            "field mouse": {
                "tren": (
                    "sitting up on the hind legs to listen with both ears forward",
                    "freezing completely flat in short grass",
                    "running a short distance and stopping dead",
                ),
            },
        },
        "khuon_cam": ("underwater looking up", "underwater side on", "split level half under water",
                      "cliff edge looking down"),
        "style": (
            "Almost monochrome: silver, grey-blue and black, with one warm reflection in an eye. "
            "Deep shadow occupies most of the frame and detail lives only where the moon reaches. "
            "Grain is visible and honest, the way real low-light footage is."
        ),
        "am": "still night air, one distant call, grass moving, a wingbeat that makes no sound",
        "luat": (
            "The strike is never completed. The hunter may dive, pounce or freeze; the prey is "
            "never taken on screen and is often not in frame at all.",
            "No infrared green wash and no thermal false-colour — this is moonlight, filmed.",
        ),
    },

    "FIRST LIGHT": {
        "ten": "FIRST LIGHT",
        "mo_ta": "Những giờ đầu tiên của một sinh vật vừa ra đời — sự mong manh.",
        "hook": (
            "Something very new and very unsteady is trying to do one basic thing for the first "
            "time. The viewer stops because they want to see whether it manages."
        ),
        "anh_sang": (
            "the first direct sun of the day coming in almost horizontally through mist",
            "flat soft light a few minutes before sunrise, everything one gentle tone",
            "sunlight broken by leaves into moving coins of light on the ground",
            "backlight so every hair and every stem is rimmed and the body is in shade",
            "overcast morning, shadowless, colours quiet and even",
        ),
        "thoi_tiet": (
            "heavy dew turning every grass blade into a line of beads",
            "ground mist thirty centimetres deep, burning off in patches",
            "still warm air with insects hanging in the light",
            "a light shower just finished, everything wet and dripping",
            "no wind at all, the grass completely upright",
        ),
        "the_gioi": (
            "Spring in a temperate grassland at the edge of woodland: long wet grass holding dew, "
            "low early sun coming in almost horizontally, mist burning off the ground, and a still "
            "morning with no wind."
        ),
        "loai": {
            "duckling": (
                "A mallard duckling: soft yellow and dark brown down in a neat pattern, a small flat bill, "
                "oversized dark feet, riding very high on the water."
            ),
            "fawn": (
                "A newborn roe deer fawn: rust-red coat covered in rows of white spots, enormous "
                "dark eyes, ears too large for its head, legs folded under it in the grass."
            ),
            "cygnet": (
                "A mute swan cygnet: pale grey down, dark grey bill, black feet far too big for "
                "the body, riding low in shallow water."
            ),
            "leveret": (
                "A brown hare leveret: fully furred, eyes wide open, ears already long and laid "
                "flat along the back, crouched motionless in a form pressed into grass."
            ),
            "fox cub": (
                "A red fox cub of a few weeks: woolly grey-brown coat not yet turned red, blunt "
                "muzzle, blue-grey eyes, unsteady on wide-set paws."
            ),
        },
        "hanh_vi": {
            "duckling": {
                "tren": (
                    "paddling hard to keep up and falling behind anyway",
                    "climbing onto a floating leaf and sinking it",
                    "shaking its whole body and almost tipping over",
                    "sitting still on the bank with water beading on the down",
                ),
            },
            "fawn": {
                "tren": (
                    "standing for the first time and immediately folding back down",
                    "lying flat and motionless in grass while something passes nearby",
                    "taking three steps and stopping to work out what happened",
                    "stretching one back leg out behind it and holding it there",
                    "pushing its head into long grass until only the hindquarters show",
                ),
            },
            "cygnet": {
                "tren": (
                    "riding low in shallow water and paddling with feet far too big for the body",
                    "being groomed by an adult that is entirely out of frame except one bill",
                    "drinking at the very edge of shallow water and flinching at the cold",
                    "climbing onto a bank and slipping back once",
                ),
            },
            "leveret": {
                "tren": (
                    "crouched motionless in a form pressed into grass with its ears flat along its back",
                    "lifting its head slowly and lowering it again",
                    "washing its face with both forepaws",
                ),
            },
            "fox cub": {
                "tren": (
                    "falling asleep sitting upright and slowly tipping sideways",
                    "shaking its head hard enough to overbalance",
                    "trying to jump a small obstacle and clearing it by far too much",
                    "yawning enormously with its whole face",
                    "following a set of adult legs closely and losing the line",
                ),
            },
        },
        "khuon_cam": ("underwater looking up", "underwater side on", "split level half under water",
                      "cliff edge looking down"),
        "style": (
            "Warm and low-contrast: gold light through mist, backlit dew, wide-open aperture so "
            "only the eye and nose are sharp and everything else is bloom. The softest-looking "
            "channel of the ten, and it is soft on purpose."
        ),
        "am": "dawn birdsong at a distance, grass moving, one small call, insects",
        "luat": (
            "No predator, no threat, no separation, no death. Nothing bad happens in this world "
            "and nothing is implied.",
            "The adult is never fully in frame — this channel is about the young animal alone in "
            "the picture.",
        ),
    },

    # ── ĐÃ CẮT: "THE MURMUR" (hàng triệu cơ thể chuyển động như một hình khối) ────────────
    #
    # Ý tưởng mạnh nhất về mặt hình của cả mười một bản nháp — nhưng nó đâm thẳng vào một điểm
    # yếu ĐÃ ĐO của Kling, ghi trong `kling_studio.py` từ lần thử thật 09/08:
    #
    #     yếu : chữ đọc được · mặt người cận cảnh · bàn tay · thoại · ĐÁM ĐÔNG CHUYỂN ĐỘNG NHANH
    #
    # Một đàn sáo đá cuộn xoáy CHÍNH LÀ đám đông chuyển động nhanh. Chín kênh kia đứng trọn
    # trong phần mạnh của Kling; kênh này thì không, và mỗi lượt sinh hỏng là tiền thật.
    #
    # Không bỏ hẳn ý tưởng: ghi lại ở đây để nếu những clip đầu tiên cho thấy Kling dựng nổi
    # khối đông thì mở lại — lúc ấy đã có bằng chứng, thay vì đoán. (Bản thảo đầy đủ nằm trong
    # lịch sử git của tệp này, commit thêm mười kênh thiên nhiên.)

    "STORM COAST": {
        "ten": "STORM COAST",
        "mo_ta": "Động vật đối mặt thời tiết dữ — sức chịu đựng, không phải thảm hoạ.",
        "hook": (
            "Weather violent enough to flatten anything standing in it, and an animal standing in it "
            "as though nothing is happening. The viewer stops at the contrast."
        ),
        "anh_sang_cam": ("through the water", "hard high sun"),
        "thoi_tiet_cam": ("water like glass", "loose pack ice"),
        "the_gioi": (
            "A North Atlantic seabird cliff in a gale: black wet rock, white water exploding at "
            "the base, horizontal rain, low ragged cloud tearing past, and grass on the clifftop "
            "combed flat in one direction."
        ),
        "loai": {
            "gannet": (
                "A northern gannet: brilliant white body, black wingtips, a buff-yellow head, a "
                "long blue-grey dagger bill, pale eyes ringed in blue."
            ),
            "puffin": (
                "An atlantic puffin: black back, white front, a large triangular bill banded "
                "orange, yellow and blue-grey, orange feet, upright stance."
            ),
            "grey seal": (
                "A grey seal: long straight muzzle, mottled grey coat, hauled out on a boulder "
                "beach with waves running past."
            ),
            "raven": (
                "A raven: entirely glossy black, heavy bill, shaggy throat feathers, wedge-shaped "
                "tail, holding position in the wind."
            ),
        },
        "hanh_vi": {
            "gannet": {
                "tren": (
                    "holding a fixed position in a gale by adjusting the wings a few centimetres",
                    "landing on a ledge in a crosswind and stopping dead on the spot",
                    "facing directly into driving rain without closing its eyes",
                    "opening the wings once in the wind and being lifted straight up",
                    "gliding along a cliff face in perfect control while everything around it is chaos",
                    "standing on the very edge of a cliff with the wind pushing from behind",
                    "shaking a whole coat of rain off in one movement and being soaked again",
                ),
            },
            "puffin": {
                "tren": (
                    "sheltering in a rock crevice while spray blows over the top of it",
                    "walking up a wet rock slope against water running down it",
                    "gripping wet rock with its feet as a gust hits",
                    "standing upright with its feathers flattened by the wind",
                ),
            },
            "grey seal": {
                "tren": (
                    "lying on a boulder beach while waves run past on both sides",
                    "hauling further up the beach between waves",
                    "lifting its head as spray lands on it and putting it down again",
                ),
            },
            "raven": {
                "tren": (
                    "holding position in the wind above the clifftop",
                    "watching a wave break below and not reacting to it at all",
                    "tucking the bill under a wing while the feathers are flattened by wind",
                ),
            },
        },
        "khuon_cam": ("underwater side on", "macro detail"),
        "style": (
            "Grey on grey with one clean white bird in it. Rain is visible as streaks across the "
            "whole frame. Everything at distance is washed out by spray, and the only true black "
            "is wet rock. Nothing in this world is warm."
        ),
        "am": "wind over rock, rain on stone, surf detonating below, one call cutting through",
        "luat": (
            "Nothing is blown away, drowned, dashed against rocks or killed. This is endurance, "
            "not disaster.",
            "No shipwreck, no rescue, no human structure other than bare rock.",
        ),
    },

    "ICE AGE": {
        "ten": "ICE AGE",
        "mo_ta": "Voi ma mút và thảo nguyên băng hà — quay như phóng sự, về những con vật đã biến mất.",
        "hook": (
            "An animal everyone knows is gone, filmed exactly the way a wildlife crew would film "
            "one that is not. The viewer stops because the shot behaves like real footage of an "
            "impossible thing."
        ),
        "the_gioi": (
            "The mammoth steppe in late winter: dry frozen grassland running flat to the horizon, "
            "wind-packed snow lying in long ribbons between the tussocks, no trees anywhere, and "
            "a sun that never climbs far above the ground."
        ),
        "anh_sang_cam": ("through the water",),
        "thoi_tiet_cam": ("heavy slow swell", "tearing spray", "like glass", "loose pack ice",
                          "frost smoke"),
        "khuon_cam": ("underwater looking up", "underwater side on", "split level half under water",
                      "cliff edge looking down"),
        "loai": {
            "woolly mammoth": (
                "A woolly mammoth: a high domed head and a fatty hump behind it, a coat of coarse "
                "dark-ginger guard hair hanging almost to the ground over dense underwool, small "
                "furred ears, and two long tusks curving inward and crossing near the tips."
            ),
            "mammoth calf": (
                "A woolly mammoth calf: chest-high to an adult, woolly all over with a paler "
                "ginger coat, a short trunk it does not yet control, and tusks barely showing."
            ),
            "woolly rhinoceros": (
                "A woolly rhinoceros: a long low body under a thick brown coat, a broad flat front "
                "horn worn to a blade by sweeping snow, a smaller second horn behind it, and a "
                "heavy head carried close to the ground."
            ),
            "cave lion": (
                "A cave lion: larger and longer-legged than a modern lion, sandy-grey coat with "
                "faint pale stripes on the flanks, and no mane at all — only a slight ruff."
            ),
            "giant deer": (
                "A giant deer: a tall pale-brown stag carrying antlers wider than its own body, "
                "flat and palmate like two open hands, with a dark line down the spine."
            ),
        },
        "hanh_vi": {
            "woolly mammoth": {
                "tren": (
                    "sweeping snow aside with one tusk to reach the grass underneath",
                    "standing broadside with the whole coat streaming sideways in the wind",
                    "raising the trunk straight up and holding a scent on the air",
                    "walking a worn trail with the head swinging in time with each step",
                    "curling the trunk around a tussock and pulling it free",
                    "standing completely still while snow builds along the top of its back",
                    "rubbing one flank slowly against a boulder",
                    "lifting one front foot and setting it down in exactly the same place",
                ),
            },
            "mammoth calf": {
                "tren": (
                    "walking underneath an adult body and staying inside its shadow",
                    "trying to use its short trunk on a tussock and giving up",
                    "running a few steps and stopping to look back",
                ),
            },
            "woolly rhinoceros": {
                "tren": (
                    "sweeping the front horn side to side to clear snow off the grass",
                    "standing with the head lowered and steam rising from its nostrils",
                    "turning its whole body to face the wind",
                ),
            },
            "cave lion": {
                "tren": (
                    "lying flat in dry grass with only the ears above the seed heads",
                    "walking a straight line across open ground without hurrying",
                    "stopping mid-step with one forepaw still raised",
                ),
            },
            "giant deer": {
                "tren": (
                    "turning its head so the full width of the antlers crosses the frame",
                    "standing on a low rise outlined against a pale sky",
                    "lowering the antlers slowly to reach the grass",
                ),
            },
        },
        "style": (
            "Dust and low sun: everything is ochre, bone-white and cold grey, and the light comes "
            "in almost horizontally so every animal is rimmed and the ground goes dark. Air is "
            "full of blown snow and grass seed, which softens distance to nothing. Nothing in "
            "this world is green and nothing is bright."
        ),
        "am": "constant wind over dry grass, coarse hair moving, deep footfalls, distant rumble",
        "luat": (
            "Filmed as real wildlife footage, never as a museum reconstruction and never as a "
            "creature from a film. No dramatic lighting, no slow-motion roar, no monster staging.",
            "No people, no spears, no cave art, no fire, no hunt. This world has no humans in it "
            "at all.",
            "Nothing is killed, injured or eaten on screen.",
        ),
    },

    "DEEP TIME": {
        "ten": "DEEP TIME",
        "mo_ta": "Khủng long quay bằng ống kính phóng sự — không phải quái vật phim, mà là động vật.",
        "hook": (
            "A wildlife shot of an animal that has been extinct for sixty-six million years, held "
            "on a locked lens like any other. The viewer stops because it is filmed calmly, and "
            "calm is the last thing they expect."
        ),
        "the_gioi": (
            "A Late Cretaceous floodplain in the wet season: braided river channels between banks "
            "of horsetails, low broad-leaved conifers and ginkgo standing back from the water, "
            "wet sand tracked over everywhere, and mist lifting off the shallows at dawn."
        ),
        "anh_sang_cam": ("through the water", "polar twilight"),
        "thoi_tiet_cam": ("loose pack ice", "driving snow", "frost smoke", "tearing spray"),
        "khuon_cam": ("underwater looking up", "underwater side on", "split level half under water",
                      "cliff edge looking down"),
        "loai": {
            "tyrannosaur": (
                "A large tyrannosaur: a deep narrow skull with small forward-facing eyes, a "
                "muscular neck, a coat of coarse dark filaments along the neck and back fading to "
                "bare pebbled skin on the flanks, two short powerful arms held close to the chest, "
                "and a thick tail carried level with the spine."
            ),
            "sauropod": (
                "A sauropod: a very long neck held almost horizontal, a tiny blunt head, a barrel "
                "body on four columnar legs, pale grey skin with darker mottling along the back, "
                "and a tail as long as the neck held clear of the ground."
            ),
            "feathered theropod": (
                "A small feathered theropod the size of a large bird: a full covering of "
                "brown-and-cream barred feathers, long stiff tail feathers, three-fingered "
                "feathered arms held folded, and a slender toothed muzzle."
            ),
            "hadrosaur": (
                "A hadrosaur: a heavy body on four legs with a broad duck-like flattened muzzle, "
                "a hollow crest curving back from the head, olive-brown skin patterned in fine "
                "pebbled scales, and a deep tail."
            ),
            "pterosaur": (
                "A pterosaur: a long thin skull with a bony crest, a fuzzy coat of fine "
                "filaments over the body, and enormous membrane wings stretched from a single "
                "very long finger on each hand."
            ),
        },
        "hanh_vi": {
            "tyrannosaur": {
                "tren": (
                    "standing in shallow water and lowering its head to drink",
                    "walking a sandbank with the tail held perfectly level and still",
                    "turning its head to bring one eye to bear on something out of frame",
                    "shaking the filaments along its neck the way a bird shakes its feathers",
                    "resting on its haunches with the head lowered and eyes half closed",
                ),
            },
            "sauropod": {
                "tren": (
                    "sweeping the small head slowly along a bank of horsetails while feeding",
                    "walking through shallow water so the whole body reflects underneath it",
                    "lifting the neck to full height and holding it there",
                    "standing still while the long tail drifts slowly to one side",
                ),
            },
            "feathered theropod": {
                "tren": (
                    "picking its way along wet sand leaving a line of three-toed prints",
                    "fluffing every feather out at once and flattening them again",
                    "cocking its head to one side and holding it there",
                    "stretching one feathered arm and one leg out on the same side",
                ),
            },
            "hadrosaur": {
                "tren": (
                    "grazing at the water's edge with the flat muzzle skimming the surface",
                    "raising its head and holding still with the crest against the sky",
                    "moving through mist with only the crest and back showing",
                ),
            },
            "pterosaur": {
                "tren": (
                    "standing folded on all fours on a sandbank with the wings tucked away",
                    "opening both wings once to their full span and closing them",
                    "walking on its wing-knuckles and hind feet along the shallows",
                ),
            },
        },
        "style": (
            "Wet, green and quiet — the opposite of every dinosaur film ever made. Palette is "
            "river-silt grey, horsetail green and the warm sand of the banks. Light is soft "
            "morning haze coming through mist off the water, never hard, never orange, never "
            "lit from below. The animals are drawn as animals: dull, practical colours, skin "
            "that looks like it has weather on it."
        ),
        "am": "running shallow water, insects, wind in horsetails, one distant low call",
        "luat": (
            "Filmed as real wildlife footage. This is an animal, not a monster: no roaring at "
            "camera, no rearing, no film-franchise design, no dramatic under-lighting, no "
            "slow-motion menace.",
            "No people, no vehicles, no fences, no amber, no laboratory — nothing that belongs to "
            "a film about dinosaurs.",
            "No hunt, no chase, no kill, no blood. The animals are doing ordinary things.",
        ),
    },
}


# ══════════════════════════════════════════════════════════════════════════════════════════
# BỘ LỊCH — cấp cho mỗi tập một bộ trục phân biệt
# ══════════════════════════════════════════════════════════════════════════════════════════
def ho_so(kenh: str) -> dict:
    k = KENH.get(kenh.upper().strip())
    if not k:
        raise RuntimeError(f"❌ chưa có kênh {kenh!r}. Đang có: {', '.join(KENH)}")
    return k


def _nho(f):
    """Nhớ kết quả theo tham số — `_buoc_toi_uu` duyệt vài trăm bước, chỉ nên chạy một lần/kênh."""
    kho = {}

    def g(*a):
        if a not in kho:
            kho[a] = f(*a)
        return kho[a]
    return g


def _bam(t: str) -> int:
    """Băm tường minh. `hash()` của Python đổi theo từng lần chạy (PYTHONHASHSEED), nên dùng nó
    để lệch pha thì hai môi trường ra hai lịch khác nhau — bài học 13.13 của bộ hài."""
    h = 2166136261
    for c in t:
        h = ((h ^ ord(c)) * 16777619) & 0xFFFFFFFF
    return h



@_nho
def _buoc_toi_uu(P: int, truc: tuple) -> int:
    """Bước đi trên không gian tích, CHỌN BẰNG CÁCH ĐO chứ không bằng công thức.

    2/9 — Đã thử hai công thức và cả hai đều hỏng ở một chỗ khác nhau:

      · bước lớn cố định (1.000.003)  -> chữ số CAO đổi quá chậm: khuôn hình lặp liền kề
      · bước ≈ P/φ (tỉ lệ vàng)       -> chữ số GIỮA đổi kém: ánh sáng lặp 107/199 tập

    Không có một công thức nào đúng cho mọi hình dạng `truc`, vì "đổi đều" ở đây là một tính
    chất của TỪNG chữ số, không phải của dãy. Nên thôi tìm công thức: duyệt vài chục bước
    nguyên tố cùng nhau với P, ĐẾM số lần lặp liền kề trên cả bốn trục, lấy bước ít nhất.

    P ở đây chỉ vài nghìn nên phép duyệt này tốn vài mili giây, và nó chạy đúng một lần mỗi
    kênh nhờ `_nho`. Đo trực tiếp thứ mình cần rẻ hơn nhiều so với bảy vòng đoán công thức.
    """
    from math import gcd
    N = min(200, P)
    ung = [b for b in range(max(2, P // 12), P) if gcd(b, P) == 1][:400]
    tot, diem_tot = ung[0] if ung else 1, 10 ** 9
    for b in ung[::max(1, len(ung) // 60)]:
        truoc, diem = None, 0
        for i in range(N):
            n, ra = (i * b) % P, []
            for x in truc:
                ra.append(n % x)
                n //= x
            if truoc:
                diem += sum(1 for u, v in zip(truoc, ra) if u == v)
            truoc = ra
        if diem < diem_tot:
            tot, diem_tot = b, diem
    return tot

def khuon_kenh(hs: dict) -> tuple:
    """Khuôn hình mà thế giới này DIỄN ĐƯỢC.

    Cùng cơ chế `mo_cam` của bộ hài (14.2), áp ngay từ đầu ở đây vì ràng buộc còn cứng hơn: gấu
    Bắc Cực không có cảnh "dưới nước nhìn ngang ở độ sâu", và biển sâu tám trăm mét không có
    "mép vách nhìn xuống". Cấp một khuôn thế giới không diễn được là bảo Kling vẽ một cảnh vô
    nghĩa, và nó sẽ vẽ đúng thứ được bảo.
    """
    cam = hs.get("khuon_cam") or ()
    con = tuple(k for k in KHUON if k[0] not in cam)
    if len(con) < 4:
        raise RuntimeError(f"❌ khuon_cam của {hs['ten']} chỉ còn {len(con)} khuôn")
    return con


def as_kenh(hs: dict, moi_truong: str = "tren") -> tuple:
    """Trạng thái ÁNH SÁNG mà thế giới này có thật.

    2/9 — Bản đầu dùng chung một danh sách cho cả mười kênh, và TUSK (dưới băng) nhận được
    "storm light: dark sky, one bright band on the horizon". Dưới trần băng thì không có bầu
    trời và không có đường chân trời. Em đã áp `khuon_cam` cho trục khuôn hình rồi quên hai
    trục còn lại — đúng họ lỗi 6: *vá một nhánh, để nguyên nhánh song song*.
    """
    # Ánh sáng mặt nước KHÔNG dùng được cho cảnh chìm: "nắng gắt trên đỉnh, bóng đen nhỏ ngay
    # dưới mọi vật" là câu của một thế giới có mặt đất. Ba kênh dùng bảng chung mà vẫn có cảnh
    # dưới nước phải khai riêng bảng chìm.
    if moi_truong == "duoi" and hs.get("anh_sang_duoi"):
        return tuple(hs["anh_sang_duoi"])
    if hs.get("anh_sang"):
        return tuple(hs["anh_sang"])
    cam = hs.get("anh_sang_cam") or ()
    con = tuple(a for a in ANH_SANG if not any(c in a for c in cam))
    if len(con) < 3:
        raise RuntimeError(f"❌ anh_sang_cam của {hs['ten']} chỉ còn {len(con)}")
    return con


def tt_kenh(hs: dict) -> tuple:
    """Trạng thái NƯỚC / THỜI TIẾT mà thế giới này có thật."""
    if hs.get("thoi_tiet"):
        return tuple(hs["thoi_tiet"])
    cam = hs.get("thoi_tiet_cam") or ()
    con = tuple(t for t in THOI_TIET if not any(c in t for c in cam))
    if len(con) < 3:
        raise RuntimeError(f"❌ thoi_tiet_cam của {hs['ten']} chỉ còn {len(con)}")
    return con


def cap_loai(hs: dict) -> tuple:
    """Mọi cặp (loài, hành vi) HỢP LỆ của kênh này.

    2/9 — Bản đầu để LOÀI và HÀNH VI là hai trục độc lập của bộ lịch. Chạy thật rồi đọc tay 30
    cặp: khoảng một phần ba là vô nghĩa — chim hải âu *"cho con nằm trên lưng"*, đàn cá mòi
    *"dựng đuôi cá voi lên"*, cá tuyết *"giao ngà với con đực khác"*, chuột đồng *"bay tới bằng
    đôi cánh không tiếng"*. Không cổng nào bắt: `cham()` đo chữ, không đo sinh học.

    Đây là lần thứ BA cùng một họ lỗi trong bộ này (khuôn hình, rồi ánh sáng/thời tiết, giờ là
    hành vi): *bộ lịch cấp cho một ngữ cảnh thứ ngữ cảnh ấy không diễn được*. Hai lần trước em
    chữa bằng DANH SÁCH LOẠI TRỪ. Lần này danh sách loại trừ là sai công cụ — cái hợp lệ ở đây
    là một QUAN HỆ giữa hai trục, không phải một bộ lọc trên một trục.

    Nên hành vi được gắn thẳng vào loài, và hai trục nhập làm một. Cặp sai không còn tồn tại để
    mà lọc — đúng luật 14.12: ràng buộc tuyệt đối thì làm cho nó KHÔNG THỂ vi phạm, đừng viết
    thành lời dặn rồi đi canh.

    Loài chủ của kênh có nhiều hành vi nhất, nên nó tự chiếm phần lớn số tập mà không cần thêm
    một cơ chế cân trọng số nào.
    """
    return tuple((lo, hv, m)
                 for lo, bo in hs["hanh_vi"].items()
                 for m, ds in bo.items() for hv in ds)


def _truc(hs: dict) -> list:
    """Độ dài từng trục. MỘT nguồn duy nhất — bài học 13.x: danh sách trục viết ở ba nơi thì sớm
    muộn lệch, và lệch một trường thì nhìn như 'gần đúng'."""
    return [len(cap_loai(hs)), len(khuon_kenh(hs)), len(as_kenh(hs)), len(tt_kenh(hs))]


def lich(kenh: str, so: int) -> dict:
    """Bộ NĂM trục cho tập `so`: loài · hành vi · khuôn hình · ánh sáng · thời tiết.

    Đánh số thẳng trên không gian TÍCH rồi bước bằng một số nguyên tố cùng nhau với tích — chứ
    không modulo từng trục. Modulo từng trục thì bộ năm lặp lại sau `lcm(các độ dài)`, và với các
    độ dài ở đây lcm nhỏ hơn tích hàng nghìn lần (bài học 13.13).

    Khuôn hình lấy vòng quay RIÊNG, không nằm trong tích: trong phép phân rã cơ số, trục nào đứng
    sau là chữ số cao và đổi chậm nhất — đo được ở bộ hài là 144/199 tập liền nhau trùng khuôn
    (14.9). Mà với clip KHÔNG LỜI thì khuôn hình chính là toàn bộ sản phẩm, nên nó phải đổi mỗi
    tập, không được đi thành vệt.
    """
    hs = ho_so(kenh)
    kh = khuon_kenh(hs)
    TT, CAP = tt_kenh(hs), cap_loai(hs)
    AS = as_kenh(hs)
    from math import gcd
    # KHÔNG gán mỗi trục một vòng quay riêng. Đã thử và đó là bẫy `lcm` của luật 13.13 mặc áo
    # khác: mỗi trục nhìn riêng thì trải đều và không lặp liền kề, nhưng BỘ BỐN lặp lại sau
    # `lcm(các độ dài)` — đo được ICE BEAR chỉ có 84 bộ khác nhau trong 200 tập.
    #
    # Vẫn đánh số thẳng trên không gian TÍCH, và chữa lỗi "chữ số cao đổi chậm" bằng BƯỚC, không
    # bằng cách tách trục: bước ≈ P/φ (tỉ lệ vàng) là bước rải đều nhất trên một vòng tròn — định
    # lý ba khoảng cách — nên mọi chữ số đều đổi, kể cả chữ số cao nhất.
    truc = [len(CAP), len(kh), len(AS), len(TT)]
    P = 1
    for x in truc:
        P *= x
    buoc = _buoc_toi_uu(P, tuple(truc))
    n = (_bam(hs["ten"]) % P + so * buoc) % P
    ra, chi = [], n
    for x in truc:
        ra.append(chi % x)
        chi //= x
    i_cap, i_kh, i_as, i_tt = ra
    loai, hv, mt = CAP[i_cap]
    # Khuôn hình phải quay được MÔI TRƯỜNG của hành vi này, và khuôn cận cực đại chỉ dùng cho
    # hành vi chậm. Lọc rồi ánh xạ chỉ số vào danh sách còn lại — giữ nguyên chu kỳ P.
    hop = tuple(k for k in kh
                if mt in KHUON_MOI_TRUONG.get(k[0], ("tren",))
                and (k[0] != "macro detail" or hv in MACRO_OK))
    if not hop:
        hop = tuple(k for k in kh if mt in KHUON_MOI_TRUONG.get(k[0], ("tren",))) or kh
    kh, i_kh = hop, i_kh % len(hop)
    AS = as_kenh(hs, mt)                       # bảng ánh sáng phụ thuộc MÔI TRƯỜNG của hành vi
    i_as %= len(AS)
    return {
        "loai": loai, "ta_loai": hs["loai"][loai],
        "hanh_vi": hv,
        "khuon": kh[i_kh][0], "may": kh[i_kh][1], "moi_truong": mt,
        "anh_sang": "" if kh[i_kh][0] in KHUON_TU_SANG else AS[i_as],
        "thoi_tiet": TT[i_tt],
        "_khong_gian": P,
    }


# ══════════════════════════════════════════════════════════════════════════════════════════
# GHÉP PROMPT — có CHỐT CHẶN ĐỘ DÀI, cắt từ đuôi kho tuỳ chọn, hàng rào không bao giờ mất
# ══════════════════════════════════════════════════════════════════════════════════════════
def prompt(kenh: str, so: int, giay: float = 8) -> str:
    """Prompt gửi Kling cho tập `so`. Bảo đảm ≤ KY_TU_MAX với hàng rào DO NOT còn NGUYÊN.

    Bài học 12.1 của bộ giải thích, trả giá bằng cả một buổi: nhồi prompt vượt trần thì API trả
    400 cho MỌI lệnh, và nó chết chậm — nhìn từ ngoài y hệt "mạng chậm". Nên mọi chỗ ghép prompt
    phải có chốt chặn ghép theo thứ tự ưu tiên và cắt từ ĐUÔI, thay vì để bên kia từ chối cả câu.
    """
    hs = ho_so(kenh)
    x = lich(kenh, so)
    g = f"{float(giay):g}"

    # BẮT BUỘC — không khối nào ở đây được cắt.
    bb = [
        f"{hs['ten']} — photoreal wildlife shot, vertical 9:16, exactly {g} seconds, one "
        f"continuous take.",
        "",
        # Tiêu đề cũ là "exactly one animal is the subject" — nhưng một số hành vi có sẵn con
        # thứ hai CÙNG LOÀI ("crossing tusks with another male"), nên tiêu đề ấy mâu thuẫn với
        # chính dòng ngay dưới nó. Điều thật sự cần khoá là KHÔNG CÓ LOÀI THỨ HAI.
        "SUBJECT — this is the only kind of animal in the frame:",
        f"{x['ta_loai']}",
        f"It is {x['hanh_vi']}.",
        "",
        "PLACE — identical in every episode of this channel, never redesign:",
        f"{hs['the_gioi']}",
        "",
        "CAMERA:",
        f"{x['may']}",
        SAN_CHUYEN_DONG,
        "",
        ("LIGHT AND WEATHER:" if x["anh_sang"] else "CONDITIONS:"),
        (f"The light is {x['anh_sang']}. The conditions are {x['thoi_tiet']}."
         if x["anh_sang"] else f"The conditions are {x['thoi_tiet']}."),
        "",
        "TREATMENT:",
        SAN_THAT,
        "",
        # LENS là khối BẮT BUỘC, không phải khối tả thêm. Đo được nó bị rớt khỏi kho tuỳ chọn
        # vì `LOOK` xếp trước và ăn hết chỗ — mà câu ống kính mới là thứ quyết định clip có
        # "trông như phim quay thật" hay không. Cùng bài học 12.x của bộ giải thích: khối giữ
        # BẢN CHẤT phải ngang hàng khối khoá nhân vật, không nằm trong phần chèn được thì chèn.
        "LENS:",
        ong_kinh(x["khuon"], x["moi_truong"]),
        "",
        f"OVER THE {g} SECONDS:",
        # 2/9 — Bản đầu nói con vật ĐANG LÀM GÌ nhưng không nói tám giây ấy DIỄN RA THẾ NÀO, và
        # Kling xử lý chỗ trống ấy theo cách rẻ nhất: một clip gần như tĩnh. Với short không lời
        # thì tĩnh là chết — không có giọng nào giữ người xem qua giây thứ ba.
        #
        # Khối này cũng là chỗ đặt HOOK. Bài học đã có sẵn trong `kling_studio.py`: "Shot 1 IS
        # the hook — no setup shot, no establishing shot." Khung ĐẦU TIÊN phải đã ở giữa hành
        # động; không có nhịp dựng cảnh nào cả, vì clip chỉ dài tám giây.
        "The first frame is already mid-action — no establishing beat, no lead-in. The movement builds "
        "through the middle, resolves about two thirds through, and the last seconds are the "
        "stillness after it. Nothing else enters the frame.",
    ]
    rao = [RAO[0]] + list(RAO[1:-1]) + [CAU_CHOT_RAO.format(g=g)]

    # KHO TUỲ CHỌN — chèn tới đâu ngân sách cho phép, theo thứ tự giá trị giảm dần.
    # KHO TUỲ CHỌN chỉ chứa thứ Kling VẼ ĐƯỢC.
    #
    # Bản đầu nhét cả `am` (thiết kế âm thanh) và `hook` (lý do giữ chân người xem) vào đây. Cả
    # hai đều sai chỗ: Kling không dựng tiếng, và "vì sao cảnh này giữ chân" là lý lẽ đạo diễn,
    # không phải thứ vẽ ra được. Chúng chiếm ~300 ký tự ngân sách để nói với mô hình những điều
    # nó không làm gì được — và tệ hơn, một câu tả âm thanh có thể khiến nó vẽ nguồn phát ra
    # tiếng ấy. `am` và `hook` vẫn được ghi vào `tap.json` cho khâu dựng và khâu viết bài đăng.
    kho = [["LOOK:", hs["style"]]]

    lo, ra = "\n".join(bb), "\n".join(rao)
    con = KY_TU_MAX - len(lo) - len(ra) - 2
    them = []
    for kh in kho:
        t = "\n".join(kh).strip()
        if t and len(t) + 3 <= con:
            them.append(t)
            con -= len(t) + 3
    if len(lo) + len(ra) + 2 > KY_TU_MAX:
        raise RuntimeError(f"khối bắt buộc của {kenh} đã {len(lo) + len(ra) + 2} ký tự — "
                           f"viết ngắn `the_gioi` hoặc mô tả loài lại")
    return lo + "\n\n" + "".join(t + "\n\n" for t in them) + ra + "\n"


# ══════════════════════════════════════════════════════════════════════════════════════════
# CỔNG — chấm CHÍNH prompt sắp giao đi, không chấm một đường song song
# ══════════════════════════════════════════════════════════════════════════════════════════
def cham(kenh: str, so: int, giay: float = 8) -> list[str]:
    """Mọi lỗi tìm được trong prompt của tập này. Rỗng = giao đi được.

    Chấm trên CHÍNH chuỗi sẽ dán vào Kling (bài học 13.7): mọi phép đo gián tiếp ở bộ hài đều
    sai ít nhất một lần, và lần nào cũng sai theo kiểu 'nghe rất có căn cứ'.
    """
    e: list[str] = []
    x = lich(kenh, so)
    try:
        p = prompt(kenh, so, giay)
    except Exception as ex:
        return [f"không ghép nổi prompt ({type(ex).__name__}: {ex}) — coi như chưa đạt"]

    if len(p) > KY_TU_MAX:
        e.append(f"prompt {len(p)} ký tự, quá trần {KY_TU_MAX} của Kling — hàng rào sẽ bị cắt")
    if len(p) < KY_TU_MIN:
        e.append(f"prompt chỉ {len(p)} ký tự — quá mỏng, Kling sẽ tự bịa phần còn thiếu")
    if not p.rstrip().endswith(CAU_CHOT_RAO.format(g=f"{float(giay):g}")):
        e.append("prompt không kết đúng câu chốt của hàng rào — hàng rào đã bị cắt hoặc xô lệch")

    # QUÉT CÁI GÌ. Bản đầu quét cả phần mô tả của prompt và bắt oan 1800/1800 — vì chính câu
    # tay nghề của mình chứa từ bị cấm: `SAN_THAT` viết "never makes a human expression", và
    # cổng "không có người" bắt chữ `human` trong câu ĐANG CẤM có người. Đúng luật 13.8: cổng
    # bắt oan tệ hơn cổng không bắt, vì nó chặn thứ hoàn toàn đúng.
    #
    # Thứ cần soi là DỮ LIỆU KÊNH — những chuỗi do người viết tay, nơi lỗi thật sự sống. Các
    # hằng số tay nghề (`SAN_THAT`, `SAN_CHUYEN_DONG`, `SAN_ONG_KINH`, `RAO`) là văn bản cố định
    # đã duyệt; soi chúng mỗi lượt là soi lại thứ không đổi.
    hs2 = ho_so(kenh)
    # Nối bằng "\n · " chứ KHÔNG bằng dấu cách. Bản đầu nối bằng dấu cách và cổng máu me bắt
    # `'ripple Open'` — cụm ấy không tồn tại ở trường nào cả, nó sinh ra từ ĐUÔI trường "not one
    # ripple" dính vào ĐẦU trường "Open the mouth wide". Đo một phép nối là đo một văn bản không
    # ai viết ra; mọi biểu thức nhiều từ đều có thể nổ ở đúng chỗ ghép.
    # SOI ĐÚNG THỨ SẼ GIAO ĐI, không hơn.
    #
    # 2/9 — Bản trước soi cả `hook`. Nhưng `hook` đã bị bỏ khỏi prompt (nó là lý lẽ đạo diễn,
    # Kling không vẽ được), nên soi nó là soi văn bản không bao giờ tới tay mô hình — và nó bắt
    # oan ngay: câu hook của ICE AGE có chữ *"a wildlife crew"*, cổng "không có người trong
    # khung" nổ 246 lần cho một câu không ai gửi đi.
    #
    # Luật: khi bỏ một khối khỏi prompt, đi bỏ nó khỏi phạm vi cổng luôn. Cổng soi rộng hơn thứ
    # giao đi là một cỗ máy bắt oan đang chờ dữ liệu đúng để chặn.
    mo_ta = "\n · ".join([x["ta_loai"], x["hanh_vi"], hs2["the_gioi"],
                          x["may"], x["anh_sang"], x["thoi_tiet"], hs2["style"]])
    for rx, ly in ((CAM_MAU, "máu me / xác / vết thương — YouTube phạt mạnh ngách này, và cú vồ "
                             "chỉ được BẮT ĐẦU, không được kết thúc trên hình"),
                   (CAM_CHU, "chữ trong khung — Kling vẽ chữ ra ký tự loằng ngoằng, đây là chỗ "
                             "nó hỏng nặng nhất"),
                   (CAM_NGUOI, "người / tàu thuyền / drone trong khung — mặt người và bàn tay là "
                               "hai thứ Kling vẽ hỏng chắc chắn"),
                   (CAM_NHAN_HOA, "nhân hoá — con vật mặc đồ, cười, nói. Kênh này sống bằng việc "
                                  "trông như phim tư liệu thật"),
                   (CAM_TROI, "máy chuyển động — chính hàng rào của prompt này đã cấm nó, nên "
                              "viết vào là tự mâu thuẫn và Kling sẽ chọn một bên"),
                   (CAM_PHIM, "tạo hình kiểu PHIM — mô hình đã học hàng triệu khung phim quái "
                              "vật, nên chữ này kéo nó về đúng chỗ ấy. Đây là động vật đang "
                              "sống, không phải quái vật; và tạo hình hãng phim là tài sản của "
                              "hãng ấy"),
                   (CAM_NHANH, "chuyển động nhanh và hỗn loạn — đây là chỗ Kling vẽ sai giải "
                               "phẫu (thừa chi, cơ thể biến dạng)")):
        m = rx.search(mo_ta)
        if m:
            e.append(f"{ly}. Chữ vướng: {m.group(0)!r}")

    if not any(k in p.lower() for k in GHIM_MAY):
        e.append("không ghim góc máy — Kling trôi thành cảnh drone khi không ghim")

    if x["hanh_vi"].split()[0].lower() not in p.lower():
        e.append(f"prompt không mang hành vi được cấp cho tập này ({x['hanh_vi']!r})")
    # Khoá loài là một NHÃN ("orca bull"), còn mô tả là văn xuôi ("An adult male orca"). Đòi
    # nguyên cụm là bắt oan — đủ khi một từ đặc trưng của nhãn có mặt.
    tu = [t for t in re.findall(r"[a-z]+", x["loai"].lower()) if len(t) >= 4]
    if tu and not any(t in p.lower() for t in tu):
        e.append(f"prompt không nêu đúng loài được cấp ({x['loai']!r})")
    return e


# ══════════════════════════════════════════════════════════════════════════════════════════
# ĐA DẠNG GIỮA MƯỜI KÊNH — cùng câu luật YouTube mà `kiem_da_dang.py` đo cho bộ hài
# ══════════════════════════════════════════════════════════════════════════════════════════
def _tu(t: str) -> set:
    """Tập TỪ NỘI DUNG. Đo bằng từ chứ không bằng độ giống chuỗi: bài học 13.5 — hai mô tả âm
    thanh khác hẳn nhau vẫn 'giống' nhau nếu chúng chung KHUÔN CÂU, mà người xem nghe thấy âm
    thanh chứ không nghe thấy cú pháp."""
    bo = {"the", "a", "an", "and", "of", "in", "on", "at", "to", "with", "is", "are", "it",
          "its", "that", "this", "one", "no", "not", "into", "from", "for", "as", "by", "so",
          "up", "down", "out", "over", "under", "across", "through", "never", "always"}
    return {w for w in re.findall(r"[a-z]+", t.lower()) if len(w) > 2 and w not in bo}


def kiem_da_dang(nguong: float = 0.34) -> list:
    """Cặp kênh nào chung quá nhiều CHỮ ở các trường bản sắc.

    Ngưỡng 0,34 trên Jaccard tập từ. Không phải con số tròn cho đẹp: mười kênh này buộc phải
    chung một vốn từ hẹp (water, ice, light, frame, animal), nên trần phải cao hơn bộ hài — và
    phải đo SAU KHI cắt các câu tay nghề dùng chung, thứ giống nhau là ĐÚNG (13.4).
    """
    import itertools
    truong = ("the_gioi", "style", "hook", "am")
    ra = []
    for a, b in itertools.combinations(KENH, 2):
        for f in truong:
            ta, tb = _tu(KENH[a][f]), _tu(KENH[b][f])
            g = len(ta & tb) / max(1, len(ta | tb))
            if g > nguong:
                ra.append((round(g, 2), f, a, b))
        la = set(KENH[a]["loai"]); lb = set(KENH[b]["loai"])
        if la & lb:
            ra.append((1.0, "loài trùng", a, b))
        ha = set(KENH[a]["hanh_vi"]); hb = set(KENH[b]["hanh_vi"])
        if ha & hb:
            ra.append((1.0, "hành vi trùng", a, b))
    return sorted(ra, reverse=True)


def luu(kenh: str, so: int, giay: float = 8) -> str:
    """Ghi prompt của một tập ra đĩa để anh dán vào Kling, kèm thẻ chú giải."""
    e = cham(kenh, so, giay)
    if e:
        raise RuntimeError("prompt chưa đạt:\n  - " + "\n  - ".join(e))
    slug = re.sub(r"[^a-z0-9]+", "-", kenh.lower()).strip("-")
    tm = os.path.join(KHO, slug, f"{so:03d}")
    os.makedirs(os.path.join(tm, "clips"), exist_ok=True)
    x = lich(kenh, so)
    io.open(os.path.join(tm, "PROMPT.txt"), "w", encoding="utf-8").write(prompt(kenh, so, giay))
    json.dump({"kenh": kenh, "so": so, "giay": giay, **x,
               "am": ho_so(kenh)["am"], "hook": ho_so(kenh)["hook"]},
              io.open(os.path.join(tm, "tap.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return tm


def tap_ke(kenh: str) -> int:
    """Số tập kế tiếp CHƯA sinh của kênh này.

    2/9 — `--so` là tham số tay, và vì bộ lịch tất định nên sinh lại cùng một `--so` cho ra
    ĐÚNG cùng một prompt, ghi đè lặng lẽ lên thư mục cũ. Anh dán nó vào Kling và trả tiền cho
    một lượt sinh ra đúng cái clip đã có. Không có gì báo, vì về mặt kỹ thuật không có gì hỏng.

    Đây là dạng lỗi tốn tiền thật mà mọi cổng đều xanh — cùng họ với 12.8. Chữa bằng cách để
    máy đếm, thay vì để người nhớ.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", kenh.lower()).strip("-")
    d = os.path.join(KHO, slug)
    if not os.path.isdir(d):
        return 0
    da = [int(x) for x in os.listdir(d) if x.isdigit()]
    return max(da) + 1 if da else 0


def xuat_web(dich: str, so_tap: int = 60) -> tuple:
    """Xuất cho dashboard: prompt DỰNG SẴN, không xuất khuôn để trình duyệt tự ghép.

    2/9 — Bộ Kling hài xuất KHUÔN rồi để JS ghép, và cái giá của lựa chọn ấy là ba lỗi lệch
    Python↔JS phải đi truy: trục thứ bảy, trục khuôn hình, và trần số vai. Mỗi lần lệch đều sai
    ĐÚNG MỘT TRƯỜNG nên trông như "gần đúng" chứ không như hỏng.

    Bộ này không cần chịu giá ấy. Prompt ở đây tất định hoàn toàn — không có AI, không có ô
    trống nào phụ thuộc thứ người dùng gõ — nên xuất thẳng chuỗi cuối cùng. Trình duyệt chỉ còn
    việc HIỆN, và không còn chỗ nào để hai bên lệch nhau.

    Giá phải trả là dung lượng: 10 kênh × 60 tập × 3 độ dài ≈ 4 MB. Nằm trên Hosting (không phải
    Firestore), và trình duyệt chỉ tải tệp của kênh đang xem.
    """
    os.makedirs(dich, exist_ok=True)
    muc, tong = [], 0
    for i, (ten, c) in enumerate(KENH.items(), 1):
        slug = re.sub(r"[^a-z0-9]+", "-", ten.lower()).strip("-")
        tap = []
        for so in range(so_tap):
            x = lich(ten, so)
            tap.append({
                "so": so, "loai": x["loai"], "hanh_vi": x["hanh_vi"], "khuon": x["khuon"],
                "anh_sang": x["anh_sang"], "thoi_tiet": x["thoi_tiet"],
                "prompt": {str(g): prompt(ten, so, g) for g in GIAY_CHUAN},
            })
        d = {"ten": ten, "slug": slug, "so_tt": i, "mo_ta": c["mo_ta"], "hook": c["hook"],
             "the_gioi": c["the_gioi"], "loai": list(c["loai"]), "giay": list(GIAY_CHUAN),
             "khong_gian": lich(ten, 0)["_khong_gian"], "tap": tap}
        b = json.dumps(d, ensure_ascii=False)
        io.open(os.path.join(dich, slug + ".json"), "w", encoding="utf-8").write(b)
        tong += len(b.encode())
        muc.append({"ten": ten, "slug": slug, "so_tt": i, "mo_ta": c["mo_ta"],
                    "loai": list(c["loai"]), "so_tap": so_tap})
    io.open(os.path.join(dich, "index.json"), "w", encoding="utf-8").write(
        json.dumps({"kenh": muc, "giay": list(GIAY_CHUAN), "giay_uu_tien": list(GIAY_UU_TIEN),
                    "ky_tu_max": KY_TU_MAX}, ensure_ascii=False))
    return len(muc), tong


def main() -> int:
    ap = argparse.ArgumentParser(description="Mười kênh thiên nhiên — prompt Kling 8–10 giây.")
    ap.add_argument("--kenh")
    ap.add_argument("--so", type=int, default=None,
                    help="số tập; bỏ trống = tự lấy tập kế tiếp chưa sinh")
    ap.add_argument("--sl", type=int, default=1, help="sinh mấy tập liên tiếp")
    ap.add_argument("--giay", type=float, default=8, choices=[float(g) for g in GIAY_CHUAN])
    ap.add_argument("--liet-ke", action="store_true")
    ap.add_argument("--kiem", action="store_true", help="chạy mọi cổng trên 10 kênh")
    ap.add_argument("--xuat-web", help="xuất prompt dựng sẵn cho dashboard")
    ap.add_argument("--so-tap", type=int, default=60, help="số tập xuất mỗi kênh")
    a = ap.parse_args()

    if a.liet_ke:
        for i, (k, c) in enumerate(KENH.items(), 1):
            print(f"{i:02d} · {k:<14} {c['mo_ta']}")
        return 0

    if a.xuat_web:
        n, b = xuat_web(a.xuat_web, a.so_tap)
        print(f"  ✅ xuất {n} kênh × {a.so_tap} tập · {b / 1048576:.1f} MB → {a.xuat_web}")
        return 0

    if a.kiem:
        n = loi = 0
        for k in KENH:
            for so in range(60):
                for g in GIAY_CHUAN:
                    n += 1
                    loi += len(cham(k, so, g))
        print(f"  {n} prompt · {loi} lỗi")
        xau = kiem_da_dang()
        print(f"  đa dạng: {len(xau)} cặp vượt ngưỡng" if xau else "  đa dạng: ✅ không cặp nào")
        for x in xau[:6]:
            print("   ", x)
        return 1 if (loi or xau) else 0

    if not a.kenh:
        ap.error("cần --kenh (hoặc --liet-ke / --kiem)")
    so = a.so if a.so is not None else tap_ke(a.kenh)
    for i in range(a.sl):
        d = os.path.join(KHO, re.sub(r"[^a-z0-9]+", "-", a.kenh.lower()).strip("-"),
                         f"{so + i:03d}")
        if a.so is not None and os.path.isdir(d):
            print(f"  ⚠️ {a.kenh} tập {so + i} ĐÃ SINH RỒI ({d}) — prompt sẽ y hệt bản cũ. "
                  f"Bỏ --so để lấy tập kế tiếp.")
        tm = luu(a.kenh, so + i, a.giay)
        print(f"  ✅ {a.kenh} tập {so + i} → {tm}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
