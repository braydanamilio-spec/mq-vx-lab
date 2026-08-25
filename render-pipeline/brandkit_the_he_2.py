#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BRAND-KIT 50 KÊNH THẾ HỆ 2 — sinh bằng QUY TẮC, 0 quota (25/8/2026).

VÌ SAO KHÔNG GỌI AI
-------------------
Bộ nhận diện là thứ phải ỔN ĐỊNH suốt đời kênh. Gọi AI sinh màu/tagline thì mỗi lần chạy lại ra
một bản khác, mà kênh đổi nhận diện là mất người theo dõi. Sinh bằng quy tắc: cùng đầu vào luôn
ra cùng kết quả, đổi được có chủ đích, và không tốn một đơn vị quota nào.

MÀU: mỗi NICHE một vùng màu riêng (24 niche = 24 vùng), mỗi kênh trong niche lệch sắc độ theo thứ
tự → 50 kênh không kênh nào trùng màu, mà cùng niche vẫn nhìn ra họ hàng.

    python brandkit_the_he_2.py --sinh          # ghi brand vào kenh_the_he_2.json
    python brandkit_the_he_2.py --xem "STEAM TRUTH"
"""
from __future__ import annotations

import colorsys
import io
import json
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(GOC, "kenh_the_he_2.json")

# Góc màu (độ) cho từng niche — đặt tay để các niche cạnh nhau không lẫn màu.
GOC_MAU = {
    "Đồ ăn & đồ uống": 22, "Sức khoẻ & gym": 150, "Tiền cá nhân": 45,
    "Tội phạm có thật": 355, "Bí ẩn chưa lời giải": 275, "Thể thao": 15,
    "Người nổi tiếng": 320, "Phim & truyền hình": 260, "Nhạc": 300,
    "Game": 190, "Xe": 205, "Thú cưng & động vật": 95, "Du lịch": 175,
    "Công nghệ & AI": 225, "Kinh dị & rùng rợn": 285, "Quan hệ & hẹn hò": 335,
    "Nghề nghiệp": 210, "Nhà ở": 35, "Lịch sử": 30, "Vũ trụ": 245,
    "Thời tiết & thảm hoạ": 195, "Quân sự": 85, "Luật & quyền công dân": 235,
    "Giáo dục": 165,
}

# Biểu tượng theo NICHE, không theo dạng render: người xem nhận ra kênh nói về CHỦ ĐỀ gì trước
# khi nhận ra nó trình bày kiểu gì. Mọi tên dưới đây đều có trong BrandV2.tsx.
MOTIF = {
    "Đồ ăn & đồ uống": "plate", "Sức khoẻ & gym": "flask", "Tiền cá nhân": "coins",
    "Tội phạm có thật": "scale", "Bí ẩn chưa lời giải": "lens", "Thể thao": "field",
    "Người nổi tiếng": "pulse", "Phim & truyền hình": "film", "Nhạc": "note",
    "Game": "gamepad", "Xe": "road", "Thú cưng & động vật": "paw", "Du lịch": "map",
    "Công nghệ & AI": "chip", "Kinh dị & rùng rợn": "ghost", "Quan hệ & hẹn hò": "heart",
    "Nghề nghiệp": "receipt", "Nhà ở": "house", "Lịch sử": "film", "Vũ trụ": "rocket",
    "Thời tiết & thảm hoạ": "storm", "Quân sự": "shield", "Luật & quyền công dân": "scale",
    "Giáo dục": "cap",
}

# Câu định vị — viết tay từng kênh, tiếng Anh cho khán giả Mỹ.
TAGLINE = {
 "WHAT IS IN IT": "What the label does not say",
 "RECALL PLATE": "Pulled from shelves this week",
 "CALORIE SHOCK": "One meal, real numbers",
 "ONE STUDY": "One real study, explained straight",
 "PILL FACTS": "What the FDA pulled and why",
 "PAYCHECK GAP": "Your raise versus your rent",
 "RENT REALITY": "What a roof costs now",
 "PRICE OF NOW": "What got expensive this year",
 "COURT RECORD": "Straight from the court file",
 "SUED FOR THIS": "The lawsuit they hoped you missed",
 "COLD FILE": "The case nobody closed",
 "UNSOLVED LOG": "Still no answer",
 "MISSING PIECE": "Gone, and never explained",
 "DIAMOND NUMBERS": "Baseball, by the numbers",
 "COURT KINGS": "Who actually leads the league",
 "PAID VS PLAYED": "Paid like a star, played like what",
 "AMERICA LOOKED UP": "What America read yesterday",
 "FAME CURVE": "The rise and the drop",
 "SHOW NUMBERS": "Every show has a number",
 "GONE TOO SOON": "Great shows that got cut",
 "SONG FILE": "Who really wrote it",
 "ONE HIT": "One song, then silence",
 "STEAM TRUTH": "Who is actually online",
 "GAME GRAVEYARD": "Bought by millions, empty tonight",
 "CAR RECALL": "What they recalled on your car",
 "MPG TRUTH": "What the EPA actually measured",
 "BREED FILE": "One breed, one file",
 "WILD NUMBERS": "The wild, counted",
 "COST TO GO": "What that trip really costs",
 "SKY RIGHT NOW": "Who is above you right now",
 "FILINGS SAY": "What companies admit in writing",
 "QUIET LAYOFFS": "The cuts they filed quietly",
 "REAL PLACE": "A real place, a real record",
 "NIGHT SHIFT": "What happens after midnight",
 "MARRIAGE MATH": "Love, in numbers",
 "WHAT THEY SEARCH": "What America looks up alone",
 "SALARY TRUTH": "What that job really pays",
 "JOB DYING": "The jobs going away",
 "WHERE TO MOVE": "Where your money goes further",
 "HOUSE MATH": "Years of pay for four walls",
 "ARCHIVE REEL": "Footage nobody owns",
 "THEN AND NOW": "Same street, a century apart",
 "NEAR EARTH": "What just passed us",
 "SPACE INVOICE": "Who NASA pays",
 "ALERT NOW": "What is warning right now",
 "QUAKE LOG": "The ground moved here",
 "PENTAGON LEDGER": "Where the defense money went",
 "WEAPON PRICE": "What one round costs you",
 "YOUR RIGHTS CASE": "The ruling that changed your day",
 "DEGREE WORTH": "What that degree is worth",
}


def _hex(h: float, s: float, v: float) -> str:
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360.0, s, v)
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def bang_mau(niche: str, thu_tu: int) -> dict:
    """Bảng màu của một kênh. Cùng niche = họ hàng, khác kênh = khác sắc độ."""
    goc = GOC_MAU.get(niche, 210) + thu_tu * 14      # lệch đủ để mắt phân biệt
    return {
        "bg":        _hex(goc + 200, 0.55, 0.09),     # nền tối, ngả về màu bù
        "primary":   _hex(goc,       0.82, 0.98),
        "secondary": _hex(goc + 32,  0.70, 0.92),
        "accent":    _hex(goc + 175, 0.75, 0.98),     # màu đối, dùng cho con số
        "text":      "#F2F6FF",
    }


def sinh(k: dict, thu_tu: int) -> dict:
    ten, tay = k["ten"], k["handle"]
    tag = TAGLINE.get(ten, k.get("goc_nhin", ""))
    tu_khoa = [w.lower() for w in ten.split()] + ["usa", "real data", "verified"]
    return {
        "name": ten, "handle": tay, "tagline": tag, "niche": k["niche"],
        "palette": bang_mau(k["niche"], thu_tu),
        "font": "Poppins",
        "motif": MOTIF.get(k["niche"], "bars"),
        "voice_tone": "calm, factual, a little blunt",
        "description": {
            "youtube": (f"{tag}. Every number in this channel comes from a public record you can "
                        f"look up yourself — no stock footage, no made-up statistics. "
                        f"Source shown on screen. New episode regularly."),
            "facebook": f"{tag}. Real records, real numbers.",
            "instagram": f"{tag}",
        },
        "keywords": tu_khoa[:12],
        "style_anh": k.get("style_anh", ""),
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--sinh", action="store_true")
    ap.add_argument("--xem", default="")
    a = ap.parse_args()
    ks = json.load(io.open(DS, encoding="utf-8"))
    dem = {}
    for k in ks:
        i = dem.get(k["niche"], 0)
        dem[k["niche"]] = i + 1
        k["brand"] = sinh(k, i)
    thieu = [k["ten"] for k in ks if not k["brand"]["tagline"]]
    if thieu:
        print("❌ thiếu tagline:", thieu)
        return 2
    mau = [k["brand"]["palette"]["primary"] for k in ks]
    trung = sorted({m for m in mau if mau.count(m) > 1})
    if trung:
        print("❌ màu chính trùng giữa các kênh:", trung)
        return 3
    if a.xem:
        k = next((x for x in ks if x["ten"].upper() == a.xem.upper()), None)
        print(json.dumps(k["brand"] if k else {}, ensure_ascii=False, indent=1))
        return 0
    if a.sinh:
        io.open(DS, "w", encoding="utf-8").write(json.dumps(ks, ensure_ascii=False, indent=1))
        print(f"✅ sinh brand cho {len(ks)} kênh · {len(set(mau))} màu chính, không trùng")
    return 0


if __name__ == "__main__":
    sys.exit(main())
