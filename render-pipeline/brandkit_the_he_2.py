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

# BẢNG MÀU 50 KÊNH — chọn bằng ĐO, không đặt tay (26/8)
#
# Hai lần thử trước đều hỏng vì cùng một lý do: ép cấu trúc lên vòng màu rồi hy vọng nó vừa.
#   • đặt tay 24 góc + lệch 14°/kênh -> 73 cặp cách nhau < 40/255, có cặp cách 3 (mắt thấy y hệt)
#   • góc vàng cho niche + 3 bậc sáng -> còn 15 cặp, tất cả là hai kênh KHÁC niche
# Ràng buộc "cùng niche phải cùng hue" chính là thứ gây kẹt: 24 hue không đủ chỗ cho 50 kênh cách
# nhau rộng rãi. Bỏ ràng buộc đó — họ hàng theo niche đã được MOTIF gánh (mỗi niche một biểu
# tượng riêng), màu thì để làm việc của nó: phân biệt 50 kênh.
#
# Cách chọn: rải một lưới HSV rồi lần lượt lấy màu XA NHẤT so với mọi màu đã lấy (farthest-point).
# Thứ tự cố định nên chạy lại luôn ra đúng bộ màu cũ — nhận diện không đổi giữa các lần sinh.
def _luoi_mau() -> list:
    """Lưới ứng viên GIỚI HẠN trong vùng màu dễ nhìn.

    Để lưới trải hết không gian thì thuật toán farthest-point luôn nhặt các GÓC CỰC trước và ra
    #0FF7F7 · #0CCC0C · #F70FF7 — màu nguyên chất, chói, nhìn như bảng màu máy tính cũ chứ không
    như một bộ nhận diện được chọn. Thu bão hoà về 0,55-0,82 và độ sáng 0,72-0,94 thì màu vẫn
    tách nhau rõ mà mắt chịu được, và chữ trắng vẫn đọc được trên đó."""
    ra = []
    for h in range(0, 360, 3):
        for sa in (0.55, 0.68, 0.82):
            for va in (0.72, 0.84, 0.94):
                ra.append((h, sa, va))
    return ra


def _khoang_cach(a: tuple, b: tuple) -> float:
    import colorsys
    ra, ga, ba = colorsys.hsv_to_rgb(a[0] / 360.0, a[1], a[2])
    rb, gb, bb = colorsys.hsv_to_rgb(b[0] / 360.0, b[1], b[2])
    return (((ra - rb) * 255) ** 2 + ((ga - gb) * 255) ** 2 + ((ba - bb) * 255) ** 2) ** 0.5


def chon_mau(n: int) -> list:
    """n màu xa nhau nhất có thể, thứ tự cố định."""
    luoi = _luoi_mau()
    chon = [luoi[0]]
    while len(chon) < n:
        xa, tot = -1.0, None
        for c in luoi:
            d = min(_khoang_cach(c, x) for x in chon)
            if d > xa:
                xa, tot = d, c
        chon.append(tot)
    return chon


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


def bang_mau(hsv: tuple, thu_tu: int = 0) -> dict:
    """Bảng màu một kênh từ một điểm HSV đã chọn."""
    goc, sat, val = hsv
    return {
        "bg":        _hex(goc + 200, 0.55, 0.09),      # nền tối, ngả về màu bù
        "primary":   _hex(goc,       sat, val),
        "secondary": _hex(goc + 28,  max(0.5, sat - 0.14), min(0.99, val + 0.04)),
        "accent":    _hex(goc + 172, 0.78, 0.98),      # màu đối, dùng cho con số
        "text":      "#F2F6FF",
    }


def sinh(k: dict, thu_tu: int, hsv: tuple) -> dict:
    ten, tay = k["ten"], k["handle"]
    tag = TAGLINE.get(ten, k.get("goc_nhin", ""))
    tu_khoa = [w.lower() for w in ten.split()] + ["usa", "real data", "verified"]
    return {
        "name": ten, "handle": tay, "tagline": tag, "niche": k["niche"],
        "palette": bang_mau(hsv),
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
    mau = chon_mau(len(ks))
    dem = {}
    for idx, k in enumerate(ks):
        i = dem.get(k["niche"], 0)
        dem[k["niche"]] = i + 1
        k["brand"] = sinh(k, i, mau[idx])
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
