#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DỰNG PHIM HÀI HAI NHÂN VẬT — thế hệ 4, 10 kênh mới (29/8/2026).

Anh: "dạng videos hài hước phong cách usa, có đa dạng bối cảnh, và đa dạng nhân vật đối thoại
trong 1 videos… mỗi channel mang một phong cách riêng… kịch bản hay viral… short 15-45s-60s…
tận dụng hệ thống api gemini, cf để vẽ ảnh bối cảnh nền".

TÁCH HẲN khỏi 60 kênh đang có. Xem `YTUONG_V4.md` để biết vì sao chọn mười cặp nhân vật này.

    python kich_hai.py --nen          # vẽ + cache nền cho cả 10 kênh (chỉ chạy MỘT LẦN)
    python kich_hai.py --demo         # dựng 1 video cho mỗi kênh
    python kich_hai.py --kenh RENTPANIC

NỀN VẼ MỘT LẦN, DÙNG MÃI. Đo được hôm nay: "đã thử 151 key, tất cả hết hạn mức ảnh". Nếu mỗi
video vẽ nền mới thì bộ này chết đúng vào những ngày bận nhất. Nên nền cache theo KÊNH: 60 ảnh
cho cả bộ, và từ video thứ hai trở đi không tốn một lượt vẽ nào.
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
NEN = os.path.join(PUB, "v4nen")
sys.path.insert(0, GOC)

# ══════════════════════════════════════════════════════════════════════════════════════════
# MƯỜI KÊNH — mỗi kênh MỘT CẶP nhân vật, MỘT bộ nền, MỘT bảng giọng
# ------------------------------------------------------------------------------------------
# Hài Mỹ ăn khách không đến từ câu đùa mà từ KHOẢNG CÁCH giữa hai người: một bên tin vào điều
# hợp lý, một bên nói ra điều có thật. Nên mỗi kênh là một cặp cố định, và mọi tập đều là hai
# người ấy va nhau ở một chỗ khác.
#
# `nen` = ba prompt vẽ nền. CỐ Ý KHÔNG có chữ trong prompt (xem `_CAM_CHU` bên datastory_ci):
# máy vẽ thấy biển hiệu là bịa chữ, và chữ bịa trên nền thì không sửa được sau.
# ══════════════════════════════════════════════════════════════════════════════════════════
KENH = [
    {"ten": "RENT PANIC", "handle": "@rentpanicusa", "a": "nam_gay", "b": "bank",
     "mau": "#F3E3C6", "de": "rent",
     "nen": ["empty american apartment living room, bare walls, afternoon light, no furniture",
             "apartment building lobby with mailboxes seen from the side, warm lamps",
             "suburban apartment parking lot at golden hour, no cars in focus"]},
    {"ten": "GYM LIES", "handle": "@gymliesusa", "a": "khoa_hoc", "b": "hang_xom",
     "mau": "#E3EEF6", "de": "gym",
     "nen": ["american gym interior with racks of weights, cool blue light, nobody in frame",
             "gym smoothie bar counter with blenders, bright morning light",
             "locker room bench and lockers, soft light, empty"]},
    {"ten": "AIRPORT HELL", "handle": "@airporthellusa", "a": "luat_tre", "b": "y_ta",
     "mau": "#E8EDF4", "de": "airport",
     "nen": ["airport check-in hall with empty queue barriers, wide windows, overcast light",
             "airport departure gate seating area, planes outside the glass, dusk",
             "baggage claim carousel, empty, fluorescent light"]},
    {"ten": "CAR GUY", "handle": "@carguyusa", "a": "hang_xom", "b": "vien_phi",
     "mau": "#EEE6D8", "de": "car",
     "nen": ["auto repair garage bay with tool chests, one car lift, warm work light",
             "american suburban driveway with an open hood seen from the side, morning",
             "tyre shop wall of stacked tyres, no signage"]},
    {"ten": "OFFICE SMALL TALK", "handle": "@officesmalltalkusa", "a": "vien_phi", "b": "cong_to",
     "mau": "#EDF1F6", "de": "office",
     "nen": ["small office meeting room with a long table and chairs, glass wall, daylight",
             "office kitchenette with a coffee machine and mugs, warm light",
             "open plan office desks seen from a corner, empty, late afternoon"]},
    {"ten": "DIET WARS", "handle": "@dietwarsusa", "a": "bank", "b": "hang_xom",
     "mau": "#F6EDDC", "de": "diet",
     "nen": ["american home kitchen counter with a fruit bowl, bright morning light",
             "fast food restaurant booth seating, warm interior, nobody in frame",
             "grocery store produce aisle, colourful, no shoppers"]},
    {"ten": "TECH SUPPORT", "handle": "@techsupportusa", "a": "luat_tre", "b": "khoa_hoc",
     "mau": "#E9E6F4", "de": "tech",
     "nen": ["american living room with a sofa and a coffee table, evening lamp light",
             "call centre cubicle row seen from the aisle, cool light, empty chairs",
             "home desk corner with a chair, curtains, soft daylight"]},
    {"ten": "PARENT MODE", "handle": "@parentmodeusa", "a": "hang_xom", "b": "sao_dem",
     "mau": "#F4E9DC", "de": "parent",
     "nen": ["american family living room with a worn couch, afternoon light through blinds",
             "car interior front seats seen from the dashboard, suburban street outside",
             "teenager bedroom with posters on the wall, string lights, evening"]},
    {"ten": "NEIGHBOR WATCH", "handle": "@neighborwatchusa", "a": "hang_xom", "b": "cong_to",
     "mau": "#F7EFD8", "de": "neighbor",
     "nen": ["american suburban backyard with a white picket fence, bright afternoon",
             "front porch of a suburban house with a rocking chair, warm light",
             "quiet suburban street with mailboxes, morning haze"]},
    {"ten": "DATING APP", "handle": "@datingappusa", "a": "sao_dem", "b": "luat_tre",
     "mau": "#F4E6EE", "de": "dating",
     "nen": ["small apartment bedroom with an unmade bed, warm evening lamp",
             "coffee shop interior with small tables, window light, nobody in frame",
             "city sidewalk at night with shop lights out of focus"]},
]

# ══════════════════════════════════════════════════════════════════════════════════════════
# KỊCH BẢN HÀI — mở · va · leo · chốt
# ------------------------------------------------------------------------------------------
# Mỗi kênh một kho tình huống. Cấu trúc giống nhau (đó là cấu trúc của mọi mẩu hài 30 giây),
# nhưng NỘI DUNG và GIỌNG khác hẳn, nên mười kênh không nghe giống nhau.
# Luật cứng, chốt bằng `cham_v4.py`: lượt thoại ≤ 14 từ · hai người nói xen kẽ · cú chốt ở cuối.
# ══════════════════════════════════════════════════════════════════════════════════════════
KHO = {
 "rent": [
   [("So the rent is going up a little?", 0, "nghi_ngo"),
    ("Just a small adjustment. Four hundred dollars.", 1, "vui"),
    ("Four hundred? For what exactly?", 0, "bat_ngo"),
    ("Market rate. Also the laundry room is closed now.", 1, "tu_tin"),
    ("The laundry room I paid for?", 0, "tuc"),
    ("That was last year's laundry room.", 1, "vui")],
   [("My lease says the rent is fixed.", 0, "tu_tin"),
    ("It says fixed for twelve months. Month thirteen is different.", 1, "vui"),
    ("It has been eleven months.", 0, "nghi_ngo"),
    ("Then you have thirty wonderful days left.", 1, "vui"),
    ("What happens on day thirty one?", 0, "so"),
    ("We celebrate. With a new number.", 1, "vui")],
 ],
 "gym": [
   [("I want to get in shape before summer.", 0, "tu_tin"),
    ("Great. Summer was four months ago.", 1, "vui"),
    ("Then I will start with next summer.", 0, "nghi_ngo"),
    ("Perfect. That gives us eight months of talking about it.", 1, "vui"),
    ("I am paying you to talk about it?", 0, "bat_ngo"),
    ("You are paying me to watch you not do it.", 1, "vui")],
   [("How long until I see results?", 0, "nghi_ngo"),
    ("Depends. Are you eating the smoothie or the fries?", 1, "tu_tin"),
    ("The smoothie. Mostly. With fries.", 0, "buon"),
    ("Then you will see results mostly.", 1, "vui"),
    ("That is not encouraging.", 0, "tuc"),
    ("Neither are the fries.", 1, "vui")],
 ],
 "airport": [
   [("Is the flight still on time?", 0, "nghi_ngo"),
    ("It is on time. It is just not here.", 1, "trung_tinh"),
    ("What does that mean?", 0, "bat_ngo"),
    ("The plane is on time somewhere else.", 1, "trung_tinh"),
    ("So when do we board?", 0, "so"),
    ("When the plane finishes being on time there.", 1, "trung_tinh")],
   [("My connection is in forty minutes.", 0, "so"),
    ("Then you have forty minutes of hope left.", 1, "trung_tinh"),
    ("Can you rebook me?", 0, "nghi_ngo"),
    ("I can. The next seat is Thursday.", 1, "trung_tinh"),
    ("Today is Monday.", 0, "tuc"),
    ("Yes. That is why the seat is available.", 1, "trung_tinh")],
 ],
 "car": [
   [("Just an oil change today, right?", 0, "tu_tin"),
    ("Started as one. Then I opened the hood.", 1, "nghi_ngo"),
    ("What did you find?", 0, "so"),
    ("Everything behind the thing you asked about.", 1, "trung_tinh"),
    ("Give me a number.", 0, "tuc"),
    ("Sit down first. Then a number.", 1, "vui")],
   [("The noise only happens on Tuesdays.", 0, "nghi_ngo"),
    ("Then bring it in on a Tuesday.", 1, "trung_tinh"),
    ("It stopped when I drove here.", 0, "buon"),
    ("Cars do that. They behave in front of me.", 1, "vui"),
    ("So what do I do?", 0, "so"),
    ("Drive home. It will start again in your driveway.", 1, "vui")],
 ],
 "office": [
   [("Quick question about the report.", 0, "trung_tinh"),
    ("Let us put it on the calendar.", 1, "vui"),
    ("It is a yes or no question.", 0, "nghi_ngo"),
    ("Then it is a short meeting.", 1, "vui"),
    ("Can I just say it now?", 0, "tuc"),
    ("You can say it now, and again at two.", 1, "vui")],
   [("This meeting could have been an email.", 0, "tuc"),
    ("I agree. Let us discuss that.", 1, "vui"),
    ("For how long?", 0, "so"),
    ("I blocked an hour to be safe.", 1, "tu_tin"),
    ("An hour to agree it should be an email?", 0, "bat_ngo"),
    ("Now it is going to be two emails.", 1, "vui")],
 ],
 "diet": [
   [("I am starting a new diet on Monday.", 0, "tu_tin"),
    ("What happened to the last one?", 1, "nghi_ngo"),
    ("It ended on a Wednesday.", 0, "buon"),
    ("That is two whole days of discipline.", 1, "vui"),
    ("It was a strong two days.", 0, "tu_tin"),
    ("They always are. Right before pizza.", 1, "vui")],
   [("This one cuts out sugar completely.", 0, "tu_tin"),
    ("Including the coffee thing you drink?", 1, "nghi_ngo"),
    ("That is not sugar. That is breakfast.", 0, "tu_tin"),
    ("It has more sugar than a birthday cake.", 1, "vui"),
    ("Then it is a very small cake.", 0, "buon"),
    ("You drink two of them.", 1, "vui")],
 ],
 "tech": [
   [("The screen is completely frozen.", 0, "so"),
    ("Have you tried turning it off and on again?", 1, "trung_tinh"),
    ("Yes. Four times.", 0, "tuc"),
    ("Let us try a fifth for the record.", 1, "trung_tinh"),
    ("Why would the fifth work?", 0, "bat_ngo"),
    ("It will not. But now it is in the notes.", 1, "vui")],
   [("It worked yesterday and now it does not.", 0, "buon"),
    ("Did anything change?", 1, "nghi_ngo"),
    ("No. Nothing at all.", 0, "tu_tin"),
    ("So the computer changed its own mind.", 1, "vui"),
    ("Okay. I updated one thing.", 0, "so"),
    ("There it is. The one thing.", 1, "vui")],
 ],
 "parent": [
   [("Can you put the phone down for dinner?", 0, "trung_tinh"),
    ("I am putting it down. Just after this.", 1, "vui"),
    ("After what exactly?", 0, "nghi_ngo"),
    ("After the part that is almost over.", 1, "vui"),
    ("That was the answer twenty minutes ago.", 0, "tuc"),
    ("And look. It is still almost over.", 1, "vui")],
   [("How was school today?", 0, "trung_tinh"),
    ("Fine.", 1, "trung_tinh"),
    ("Anything happen?", 0, "nghi_ngo"),
    ("No.", 1, "trung_tinh"),
    ("Seven hours and nothing happened?", 0, "bat_ngo"),
    ("Correct. It was a very efficient day.", 1, "vui")],
 ],
 "neighbor": [
   [("You are the one who just moved in.", 0, "nghi_ngo"),
    ("That is right. Three weeks ago.", 1, "vui"),
    ("I noticed the truck. And the boxes.", 0, "tu_tin"),
    ("You noticed a lot for three weeks.", 1, "bat_ngo"),
    ("I keep an eye on the street.", 0, "tu_tin"),
    ("Do you ever keep it on your own yard?", 1, "vui")],
   [("Your grass is getting a little tall.", 0, "nghi_ngo"),
    ("It is. I am letting it express itself.", 1, "vui"),
    ("There are rules about that here.", 0, "tu_tin"),
    ("Are there rules about watching me mow?", 1, "vui"),
    ("I am not watching. I am gardening.", 0, "so"),
    ("You have been gardening the same rose for an hour.", 1, "vui")],
 ],
 "dating": [
   [("My profile says I love hiking.", 0, "tu_tin"),
    ("When did you last go hiking?", 1, "nghi_ngo"),
    ("Two thousand nineteen.", 0, "buon"),
    ("So the profile is a historical document.", 1, "vui"),
    ("It is aspirational.", 0, "tu_tin"),
    ("So is my resume. We should date each other.", 1, "vui")],
   [("She asked what I do on weekends.", 0, "so"),
    ("What did you say?", 1, "nghi_ngo"),
    ("Rock climbing and pottery.", 0, "tu_tin"),
    ("You watch television and order noodles.", 1, "bat_ngo"),
    ("Both of those take hands.", 0, "tu_tin"),
    ("That is the weakest argument I have ever heard.", 1, "vui")],
 ],
}

CU_CHI = ["mo_tay", "chi", "nhun_vai", "dem", "suy_nghi", "khoanh_tay"]
SFX = {1: "sfx/pop.mp3", 3: "sfx/whoosh.mp3", 5: "sfx/ding.mp3"}


def _ten_tep(k: dict) -> str:
    return k["ten"].replace(" ", "").lower()


def ve_nen(k: dict, DS, keys) -> list:
    """Vẽ + CACHE ba nền cho một kênh. Trả đường dẫn tương đối trong `public/`.

    Chỉ vẽ tệp CHƯA CÓ. Đây là lý do bộ này chạy được kể cả ngày kho key cạn: sau lượt đầu, mọi
    video đều dùng lại đúng ba ảnh ấy."""
    os.makedirs(NEN, exist_ok=True)
    ra = []
    for i, prompt in enumerate(k["nen"]):
        rel = os.path.join("v4nen", f"{_ten_tep(k)}_{i}.jpg")
        dest = os.path.join(PUB, rel)
        if os.path.exists(dest) and os.path.getsize(dest) > 20000:
            ra.append(rel)
            continue
        gu = ("flat 2D cartoon background in the style of classic American animated sitcoms, "
              "bold clean outlines, simple flat colours, no people, no text, no signage, "
              "wide establishing shot, slightly stylised perspective")
        # 29/8 — GỌI THẲNG `_generate_image_ai`, KHÔNG QUA `fetch_image`.
        # `fetch_image` chỉ vẽ khi có tham số `ai_key` truyền vào (`if ai_key and ...`), nên gọi
        # nó với `ai_only=True` mà không kèm khoá thì nó lặng lẽ trả None — đúng cảnh vừa gặp:
        # 169 khoá vẽ nằm sẵn trong pool mà cả ba nền đều "không vẽ được".
        # `_generate_image_ai` tự lấy khoá từ pool đã nạp (`set_ai_pool`) và tự xoay khoá khi một
        # khoá cạn, nên nó mới là tầng đúng cho việc chỉ-vẽ-chứ-không-tìm-ảnh-thật.
        try:
            ok = DS._generate_image_ai(f"{prompt}, {gu}", dest, None, style=gu)
        except Exception as e:
            print(f"      ⚠️ nền {i}: {str(e)[:60]}")
            ok = None
        if ok and os.path.exists(dest):
            try:
                DS.nang_sang_anh(dest)
            except Exception:
                pass
            ra.append(rel)
            print(f"      🎨 nền {i} xong")
        else:
            print(f"      ⚠️ nền {i}: không vẽ được — cảnh này dùng màu nền trơn")
            ra.append("")
    return ra


def dung_luot(k: dict, nen: list, vong: int = 0) -> tuple:
    """Trả (danh sách lượt thoại, lời đọc ghép). Kịch bản bốc theo `vong` để mỗi tập một chuyện."""
    kho = KHO[k["de"]]
    kb = kho[vong % len(kho)]
    luot, loi = [], []
    for i, (chu, ai, cx) in enumerate(kb):
        cuoi = i == len(kb) - 1
        l = {"s": 0.0, "e": 0.0, "ai": ai, "nar": chu,
             "camXuc": cx,
             # CẢM XÚC NGƯỜI NGHE — nửa còn lại của trò đùa. Trong hài thoại, mặt người nghe
             # thường buồn cười hơn câu của người nói.
             "camXucKia": ["nghi_ngo", "bat_ngo", "trung_tinh", "tuc", "buon", "vui"][i % 6],
             "cuChi": CU_CHI[i % len(CU_CHI)],
             "co": "can" if (cuoi or i == 1) else ("rong" if i == 0 else "trung"),
             # 30/8 — NỀN ĐỔI THEO NHỊP, KHÔNG XOAY VÒNG TỪNG CÂU.
             # `i % 3` trên sáu lượt cho ra 1·2·3·1·2·3: khung 2 và khung 4 giống hệt nhau, đúng
             # cảnh vừa đo. Và đổi nền mỗi câu còn sai về kể chuyện — hai người đang nói với nhau
             # thì không dịch chuyển tức thời sang chỗ khác sau mỗi lượt. Chia theo NHỊP (mở · va ·
             # chốt) thì ba nền phủ hết sáu lượt, không lặp cái nào, và mỗi lần đổi nền trùng đúng
             # chỗ câu chuyện sang đoạn mới.
             "nen": nen[min(i * len(nen) // max(1, len(kb)), len(nen) - 1)] if nen else "",
             "chot": cuoi}
        if SFX.get(i):
            l["sfx"] = SFX[i]
        luot.append(l)
        loi.append(chu)
    return luot, " ".join(loi)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--nen", action="store_true", help="chỉ vẽ + cache nền, không render")
    ap.add_argument("--kenh", default="")
    ap.add_argument("--vong", type=int, default=0)
    a = ap.parse_args()

    import datastory_ci as DS
    import the_he_2 as T2
    import tts_karaoke as TTS

    chon = KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [x for x in KENH if x["ten"].replace(" ", "").upper() in vt]
    if not chon:
        print("❌ không khớp kênh nào")
        return 2

    keys = None
    try:
        keys = T2.keys_cuc_bo() or None
        if keys:
            DS.set_ai_pool(keys, "V4")
    except Exception:
        pass

    ra = []
    for k in chon:
        ten = k["ten"]
        print(f"\n▶ {ten}", flush=True)
        nen = ve_nen(k, DS, keys)
        if a.nen:
            continue
        luot, loi = dung_luot(k, nen, a.vong)

        # GIỌNG: hai nhân vật, hai chất giọng. Đây là thứ làm đối thoại nghe ra là hai người.
        GIONG = {"nam_gay": ("en-US-EricNeural", "+12%", "+14Hz"),
                 "bank": ("en-US-JennyNeural", "+4%", "+6Hz"),
                 "khoa_hoc": ("en-US-BrianNeural", "+10%", "+4Hz"),
                 "hang_xom": ("en-US-GuyNeural", "-6%", "-16Hz"),
                 "luat_tre": ("en-US-EricNeural", "+14%", "+16Hz"),
                 "y_ta": ("en-US-MichelleNeural", "+2%", "+4Hz"),
                 "vien_phi": ("en-US-SteffanNeural", "+0%", "-8Hz"),
                 "cong_to": ("en-US-AriaNeural", "-2%", "-8Hz"),
                 "sao_dem": ("en-US-AvaNeural", "+3%", "+10Hz")}
        # 29/8 — MỘT TỆP TIẾNG CHO CẢ ĐOẠN, KHÔNG GHÉP HAI GIỌNG.
        # Ghép hai tệp mp3 rời thì mốc thời gian từng từ của tệp sau phải dời đi, mà edge-tts trả
        # mốc tính từ 0 của CHÍNH tệp đó — cộng dồn sai một nhịp là khẩu hình lệch cả nửa video.
        # Đọc cả đoạn bằng giọng nhân vật A, rồi ĐỔI CAO ĐỘ theo lượt là việc của bản sau; ở bản
        # này ưu tiên KHỚP TUYỆT ĐỐI giữa tiếng và hình.
        v, rate, pitch = GIONG.get(k["a"], ("en-US-GuyNeural", "+4%", "+0Hz"))
        rel = f"v4_{_ten_tep(k)}.mp3"
        mp3 = os.path.join(PUB, rel)
        try:
            dur, subs, _ = TTS.synth(loi, mp3, voice=v, rate=rate, pitch=pitch)
        except Exception as e:
            print(f"   ❌ giọng đọc hỏng: {str(e)[:70]}")
            continue
        tu = [{"t": float(x.get("t", 0)), "d": float(x.get("d", 0)), "w": str(x.get("w", "")),
               "si": int(x.get("si", 0))} for x in (subs or [])]
        if not tu:
            print("   ❌ không có mốc từ — BỎ")
            continue

        # 30/8 — RANH GIỚI LƯỢT BÁM SỐ TỪ, KHÔNG BÁM CHỈ SỐ CÂU.
        # Cách cũ (dùng `si`) giả định bộ tách câu của mình và bộ tách câu bên trong edge-tts cắt
        # giống nhau. Chúng KHÔNG giống nhau: đo được lượt kết thúc giữa chừng nên phụ đề rớt đuôi
        # ("…just moved in. That") và câu sau bị gán nhầm cho người kia — trong hài hai người thì
        # gán nhầm người nói là hỏng cả trò đùa.
        # Số TỪ thì không có chỗ để hai bên hiểu khác nhau: edge-tts trả mốc theo đúng thứ tự từ
        # của văn bản mình đưa vào, nên đếm từ là phép ghép chắc chắn.
        _sotu = lambda t: len([x for x in str(t or "").split() if x.strip()])
        vt = 0
        for i2, l in enumerate(luot):
            n = _sotu(l["nar"])
            ws = tu[vt:vt + n]
            vt += n
            if ws:
                l["s"] = round(ws[0]["t"], 2)
                sau = tu[vt] if vt < len(tu) else None
                l["e"] = round(sau["t"] if sau else max(x["t"] + x["d"] for x in ws) + 0.4, 2)
            else:
                l["s"] = luot[i2 - 1]["e"] if i2 else 0.0
                l["e"] = l["s"] + 1.0
        if luot:
            luot[-1]["e"] = round(max(luot[-1]["e"], dur), 2)

        # 30/8 — ÉP HAI NGƯỜI KHÁC BÓNG DÁNG.
        # Mười kiểu gốc khác nhau ở tóc và màu áo, nhưng vài kiểu cùng đeo kính và cùng để ria:
        # khung đo được hai nhân vật đọc ra như anh em sinh đôi đổi màu áo. Trong phim hoạt hình
        # Mỹ, hai người trong một cảnh luôn tương phản ở BÓNG — một cao gầy một thấp đậm — vì
        # người xem nhận ra ai đang nói qua hình dáng trước cả khi nhìn mặt.
        tuyA = {"cao": 0.90, "beNgang": 1.22, "kinh": True, "rau": "ria", "matTo": 0.94, "cam": 0.85}
        tuyB = {"cao": 1.12, "beNgang": 0.86, "kinh": False, "rau": "", "matTo": 1.16, "cam": 0.10}
        props = {"luot": luot, "tu": tu, "voMp3": rel,
                 "kieuA": k["a"], "kieuB": k["b"], "kieuTuyA": tuyA, "kieuTuyB": tuyB,
                 "tieuDe": ten, "mucNen": k["mau"]}
        pj = os.path.join(GOC, "out", f"v4_{_ten_tep(k)}.json")
        os.makedirs(os.path.dirname(pj), exist_ok=True)
        io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))
        out = os.path.join(GOC, "out", f"v4_{_ten_tep(k)}.mp4")
        r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "KichHai", out,
                            f"--props={pj}", "--gl=swiftshader", "--log=error"],
                           cwd=ENG, capture_output=True, text=True, timeout=2400)
        if r.returncode or not os.path.exists(out):
            print(f"   ❌ render hỏng: {(r.stderr or r.stdout or '')[-190:]}")
            continue
        print(f"   ✅ {ten}: {out}  ({os.path.getsize(out)/1e6:.1f} MB · {dur:.0f}s)")
        ra.append(out)

    print(f"\n{'✅' if ra else '⚠️'} {len(ra)}/{len(chon)} video")
    return 0 if ra or a.nen else 1


if __name__ == "__main__":
    sys.exit(main())
