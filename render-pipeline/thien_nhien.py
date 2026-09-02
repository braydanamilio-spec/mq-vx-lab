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
    "xa": ("Shot on a long telephoto lens from a great distance, the way real wildlife is filmed: "
           "shallow depth of field, the animal sharp and the background dissolved into soft bands "
           "of colour. Natural light only, no film-LUT grading, no added lens flare."),
    "nuoc": ("Shot on a wide lens in an underwater housing, close to the subject because water "
             "eats contrast over distance: natural light from the surface only, visible particles "
             "in the water, no artificial lamp, no colour correction that removes the blue."),
    "macro": ("Shot on a macro lens very close to the subject: depth of field only a few "
              "millimetres deep, so one detail is sharp and everything a centimetre behind it is "
              "already soft. Natural light only."),
}


def ong_kinh(khuon: str) -> str:
    if khuon.startswith("underwater") or khuon.startswith("split level"):
        return ONG_KINH["nuoc"]
    if khuon.startswith("macro"):
        return ONG_KINH["macro"]
    return ONG_KINH["xa"]
SAN_CHUYEN_DONG = (
    "One continuous locked shot. The camera does not pan, tilt, zoom, dolly, orbit or fly. If the "
    "animal leaves the frame, the frame stays where it is."
)
SAN_THAT = (
    "Photoreal, documentary-grade. Correct anatomy for the species: right number of limbs, right "
    "joints, right eye placement, fur or feathers lying the way they lie on a real animal. No "
    "anthropomorphism: the animal never wears anything, never stands like a person, never makes "
    "a human expression."
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
CAM_NHAN_HOA = re.compile(
    r"\b(smil\w*|grin\w*|laugh\w*|wink\w*|wav\w* (?:hello|goodbye)|wearing|dressed|hat|scarf|"
    r"glasses|shoes|talk\w*|speak\w*|say\w*|sings? a|dance\w* like|hugs?|waves? at)\b", re.I)
GHIM_MAY = ("locked", "static", "fixed camera", "tripod", "telephoto", "macro", "wide shot",
            "close shot", "underwater housing", "low angle", "eye level", "high angle")
# Máy CHUYỂN ĐỘNG — thứ trôi mạnh nhất của Kling, và hàng rào đã cấm. Bắt luôn ở khâu viết để
# đừng tiêu một lượt sinh clip cho một prompt tự mâu thuẫn với hàng rào của chính nó.
CAM_TROI = re.compile(
    r"\b(pan\w*|tilt\w*|zoom\w*|dolly\w*|track\w+ shot|orbit\w*|fly\w*(?:over|ing) (?:over|across)|"
    r"drone shot|aerial|crane shot|handheld|steadicam|push\w* in|pull\w* back|follow\w* the)\b", re.I)
# Giải phẫu hỏng: Kling vẽ sai khi con vật cử động NHANH và PHỨC TẠP. Đo được ở bộ hài rằng cấm
# một khái niệm phải bằng biểu thức; ở đây khái niệm là "nhiều thứ cùng động rất nhanh".
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
        "hanh_vi": (
            "waiting motionless beside a breathing hole in the ice",
            "swimming between two floes with only the head above water",
            "shaking a whole coat of water off in one violent shudder",
            "testing thin ice with one forepaw before putting weight on it",
            "lying flat and pushing itself forward across the ice on its belly",
            "raising its head and holding a scent on the wind",
            "climbing out of black water onto a floe edge",
            "walking a straight line across a floe toward something out of frame",
            "sliding down a pressure ridge on its side",
            "digging at compacted snow with both forepaws",
            "standing up on its hind legs to see further",
            "sleeping curled with its nose tucked under a paw while snow settles on it",
        ),
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
        "the_gioi": (
            "Cold coastal water off a steep dark shore: deep green-black sea, kelp on the rocks, "
            "low grey cloud sitting on the headlands, the surface breaking over hidden reefs."
        ),
        "loai": {
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
        "hanh_vi": (
            "surfacing in perfect line abreast, all blows firing at once",
            "spy-hopping straight up, holding, and sliding back down without a splash",
            "turning as one body when the lead animal turns",
            "swimming inverted just under the surface showing the white belly",
            "slapping the surface once with the tail fluke",
            "moving in single file along the edge of a kelp bed",
            "one animal breaking formation and circling wide",
            "rising through a shaft of light with the pod behind it in silhouette",
            "pushing a bow wave ahead of a calf so the calf is carried",
            "hanging vertical and motionless in the water column",
            "breaching clear of the water and landing on one side",
            "passing directly beneath the camera, one after another, in order",
        ),
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
        "the_gioi": (
            "Open ocean far from any coast: deep blue water going black underneath, a horizon with "
            "nothing on it, long ocean swell, and clouds of krill hanging in the upper water."
        ),
        "loai": {
            "humpback": (
                "An adult humpback whale: dark grey-black back, white grooved throat pleats, very "
                "long white pectoral fins scalloped along the front edge, knobbly tubercles on the "
                "head, barnacle clusters on the chin and fluke edges."
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
        "hanh_vi": (
            "rising slowly from below with the mouth closed and the throat pleats flat",
            "hanging motionless head-down in the water column",
            "lifting one enormous pectoral fin clear of the surface and holding it there",
            "rolling slowly onto its side so one eye comes above the water",
            "lifting the fluke straight up and sliding under without a ripple",
            "cruising just below the surface with the blowhole breaking every few seconds",
            "drifting through a shaft of light so the white fins glow",
            "opening the mouth wide and letting the throat expand, water pouring out through baleen",
            "surfacing directly beneath a small school of fish that scatters",
            "moving past the camera so slowly that the body takes the whole shot to cross",
            "exhaling a column of spray straight up in still air",
            "resting at the surface with the calf lying across its back",
        ),
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
        "thoi_tiet_cam": ("rain stippling",),
        "the_gioi": (
            "A colony on Antarctic sea ice at the foot of a glacier front: dirty trodden snow, "
            "hard blue ice cliffs behind, a long worn path between the colony and the water's "
            "edge, and wind that never stops."
        ),
        "loai": {
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
        "hanh_vi": (
            "leaning into a wind that flattens the feathers along one whole side",
            "shuffling forward inside a tight huddle so the outside birds rotate inward",
            "tobogganing on its belly across ice, pushing with both feet",
            "standing at the ice edge looking down at the water without going in",
            "porpoising out of the water and landing on its feet on the ice",
            "walking a single-file line worn into the snow by thousands of feet",
            "bowing and stretching the neck straight up in one slow movement",
            "sheltering a chick on its feet under a fold of belly skin",
            "shaking snow out of its feathers in one whole-body shiver",
            "sliding down a slope out of control and stopping against another bird",
            "standing completely still while blowing snow streams past it",
            "stepping over a sleeping bird and continuing without pausing",
        ),
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
        "hanh_vi": (
            "rising slowly toward a breathing hole with the tusk leading",
            "hanging vertically in the water column, tusk pointing straight up",
            "crossing tusks slowly with another male, the two shapes making an X",
            "swimming upside down under the ice ceiling",
            "surfacing into a narrow lead so only the tusk and forehead appear",
            "moving through a shaft of light so the spiral on the tusk becomes visible",
            "drifting motionless while a cloud of small fish parts around it",
            "pressing the top of its head against the underside of the ice",
            "turning on its side and looking directly at the camera with one eye",
            "gliding past below with the whole body in silhouette against the bright ice",
            "exhaling under water so a single silver dome of air rolls along the ice above",
            "swimming in a tight group where all the tusks point the same way",
        ),
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
        "the_gioi": (
            "A black volcanic rock shelf on a cold Pacific coast: kelp beds combing back and forth "
            "in the surge, white water breaking over the outer rocks, spray hanging in the air, "
            "and green swell rising against the ledge."
        ),
        "loai": {
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
        "hanh_vi": (
            "bracing flat against the rock as a wave washes completely over it",
            "launching off a ledge into a rising swell",
            "riding the steep front of a green wave just under the surface",
            "hauling out by timing one surge and heaving up in a single movement",
            "sleeping stacked against a dozen other bodies, all rising and falling together",
            "throwing the head back and holding the mouth open with no sound in frame",
            "sliding backwards down wet rock and recovering",
            "porpoising through a kelp bed with the fronds parting",
            "hanging vertically in the surge with only the nose above water",
            "shaking the whole head so water flies off the whiskers",
            "pushing through the crowd to a specific spot and settling exactly there",
            "floating on its back at the surface with both fore-flippers in the air",
        ),
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
        "hanh_vi": (
            "pulsing once and gliding forward on the momentum",
            "running a wave of blue light from one end of the body to the other",
            "hanging perfectly still with tentacles spread in a wide net",
            "flushing dark red to translucent pale and back",
            "retracting every arm at once into a tight point",
            "drifting upward through falling marine snow",
            "turning a single huge black eye toward the camera",
            "opening a bell wide and closing it in one slow contraction",
            "trailing a filament twice the length of its own body behind it",
            "rotating slowly on its own axis with no visible effort",
            "releasing a small cloud of blue light and moving away from it",
            "unfolding from a compact shape into a long chain",
        ),
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
        "hanh_vi": (
            "flying straight toward the camera on completely silent wings and passing overhead",
            "hovering in one place with the head absolutely still while the body works",
            "turning its head far past its shoulder without moving its body",
            "standing motionless with one forepaw lifted, ears rotating independently",
            "pouncing straight up and coming down nose first into deep grass",
            "walking a fence line with the head down, following one line of scent",
            "freezing mid-step as something changes in the dark",
            "sitting up on the hind legs to listen with both ears forward",
            "shaking dew off in one shudder that runs from nose to tail",
            "digging quickly at the base of a tussock with both forepaws",
            "carrying a bundle of dry grass in its mouth across open ground",
            "stepping out of a hedge shadow into moonlight and stopping there",
        ),
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
            "ground mist a hand deep, burning off in patches",
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
        "hanh_vi": (
            "standing for the first time and immediately folding back down",
            "taking three steps and stopping to work out what happened",
            "lying flat and motionless in grass while something passes nearby",
            "being groomed by an adult that is entirely out of frame except one muzzle",
            "shaking its head hard enough to overbalance",
            "stretching one back leg out behind it and holding it there",
            "following an adult's legs closely and losing the line",
            "drinking at the very edge of shallow water and flinching at the cold",
            "yawning enormously with its whole face",
            "pushing its head into long grass until only the hindquarters show",
            "falling asleep sitting upright and slowly tipping sideways",
            "trying to jump a small obstacle and clearing it by too much",
        ),
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
        "hanh_vi": (
            "holding a fixed position in a gale by adjusting the wings a few centimetres",
            "landing on a ledge in a crosswind and stopping dead on the spot",
            "facing directly into driving rain without closing its eyes",
            "sheltering in a rock crevice while spray blows over the top of it",
            "opening the wings once in the wind and being lifted straight up",
            "walking up a wet rock slope against water running down it",
            "shaking a whole coat of rain off in one movement and being soaked again",
            "standing on the very edge of a cliff with the wind pushing from behind",
            "tucking the bill under a wing while the feathers are flattened by wind",
            "watching a wave break below and not reacting to it at all",
            "gripping wet rock with its feet as a gust hits",
            "gliding along a cliff face in perfect control while everything around it is chaos",
        ),
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
}


# ══════════════════════════════════════════════════════════════════════════════════════════
# BỘ LỊCH — cấp cho mỗi tập một bộ trục phân biệt
# ══════════════════════════════════════════════════════════════════════════════════════════
def ho_so(kenh: str) -> dict:
    k = KENH.get(kenh.upper().strip())
    if not k:
        raise RuntimeError(f"❌ chưa có kênh {kenh!r}. Đang có: {', '.join(KENH)}")
    return k


def _bam(t: str) -> int:
    """Băm tường minh. `hash()` của Python đổi theo từng lần chạy (PYTHONHASHSEED), nên dùng nó
    để lệch pha thì hai môi trường ra hai lịch khác nhau — bài học 13.13 của bộ hài."""
    h = 2166136261
    for c in t:
        h = ((h ^ ord(c)) * 16777619) & 0xFFFFFFFF
    return h


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


def as_kenh(hs: dict) -> tuple:
    """Trạng thái ÁNH SÁNG mà thế giới này có thật.

    2/9 — Bản đầu dùng chung một danh sách cho cả mười kênh, và TUSK (dưới băng) nhận được
    "storm light: dark sky, one bright band on the horizon". Dưới trần băng thì không có bầu
    trời và không có đường chân trời. Em đã áp `khuon_cam` cho trục khuôn hình rồi quên hai
    trục còn lại — đúng họ lỗi 6: *vá một nhánh, để nguyên nhánh song song*.
    """
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


def _truc(hs: dict) -> list:
    """Độ dài từng trục. MỘT nguồn duy nhất — bài học 13.x: danh sách trục viết ở ba nơi thì sớm
    muộn lệch, và lệch một trường thì nhìn như 'gần đúng'."""
    return [len(hs["loai"]), len(hs["hanh_vi"]), len(khuon_kenh(hs)),
            len(as_kenh(hs)), len(tt_kenh(hs))]


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
    AS, TT = as_kenh(hs), tt_kenh(hs)
    truc = [len(hs["loai"]), len(hs["hanh_vi"]), len(AS), len(TT)]
    P = 1
    for x in truc:
        P *= x
    goc = _bam(hs["ten"]) % P
    buoc = 1000003                                  # lớn, lẻ, không chia hết cho 3 hay 5
    from math import gcd
    while gcd(buoc, P) != 1:
        buoc += 2
    n = (goc + so * buoc) % P
    ra, chi = [], n
    for x in truc:
        ra.append(chi % x)
        chi //= x
    i_lo, i_hv, i_as, i_tt = ra
    bk = 3
    while gcd(bk, len(kh)) != 1:
        bk += 1
    i_kh = (_bam(hs["ten"] + "khuon") + so * bk) % len(kh)
    loai = list(hs["loai"])[i_lo]
    return {
        "loai": loai, "ta_loai": hs["loai"][loai],
        "hanh_vi": hs["hanh_vi"][i_hv],
        "khuon": kh[i_kh][0], "may": kh[i_kh][1],
        "anh_sang": AS[i_as], "thoi_tiet": TT[i_tt],
        "_khong_gian": P * len(kh),
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
        "SUBJECT — exactly one animal is the subject and nothing else is:",
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
        "LIGHT AND WEATHER:",
        f"The light is {x['anh_sang']}. The conditions are {x['thoi_tiet']}.",
        "",
        "TREATMENT:",
        SAN_THAT,
    ]
    rao = [RAO[0]] + list(RAO[1:-1]) + [CAU_CHOT_RAO.format(g=g)]

    # KHO TUỲ CHỌN — chèn tới đâu ngân sách cho phép, theo thứ tự giá trị giảm dần.
    kho = [
        ["LOOK:", hs["style"]],
        ["LENS:", ong_kinh(x["khuon"])],
        ["SOUND OF THE PLACE (for reference only, not rendered):", hs["am"]],
        ["WHY THIS SHOT HOLDS A VIEWER:", hs["hook"]],
    ]

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
    return lo + "\n\n" + "".join(t + "\n\n" for t in them) + ra


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
    mo_ta = "\n · ".join([x["ta_loai"], x["hanh_vi"], hs2["the_gioi"],
                          x["may"], x["anh_sang"], x["thoi_tiet"], hs2["style"], hs2["hook"]])
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
    json.dump({"kenh": kenh, "so": so, "giay": giay, **x},
              io.open(os.path.join(tm, "tap.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return tm


def main() -> int:
    ap = argparse.ArgumentParser(description="Mười kênh thiên nhiên — prompt Kling 8–10 giây.")
    ap.add_argument("--kenh")
    ap.add_argument("--so", type=int, default=0)
    ap.add_argument("--sl", type=int, default=1, help="sinh mấy tập liên tiếp")
    ap.add_argument("--giay", type=float, default=8, choices=[float(g) for g in GIAY_CHUAN])
    ap.add_argument("--liet-ke", action="store_true")
    ap.add_argument("--kiem", action="store_true", help="chạy mọi cổng trên 10 kênh")
    a = ap.parse_args()

    if a.liet_ke:
        for i, (k, c) in enumerate(KENH.items(), 1):
            print(f"{i:02d} · {k:<14} {c['mo_ta']}")
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
    for i in range(a.sl):
        tm = luu(a.kenh, a.so + i, a.giay)
        print(f"  ✅ {a.kenh} tập {a.so + i} → {tm}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
