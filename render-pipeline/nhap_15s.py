#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RÚT 10 KÊNH TỪ GÓI 15 GIÂY -> `kho_15s.json`  (1/9/2026)

Anh gửi `GROCK PROMPT VIDEOS 15S`: 10 tệp × 2.500 prompt. Khác hẳn gói 6 giây trước đó —
gói này có **dòng thời gian bốn nhịp**, mỗi nhịp một hành động kèm một câu thoại:

    0-3s:   Derek stands in the kitchen holding a smoking pan.
            Derek: "I made breakfast!"
    3-7s:   Sara walks in, waves the smoke away.
            Sara: "That's not breakfast. That's a fire drill."
    7-11s:  Max appears and takes a photo.
            Max: "This is going on the family group chat."
    11-15s: Nana Bea walks by without stopping: "I've seen worse... from him."

Bốn nhịp × 4 giây = 15 giây, đúng độ dài anh muốn. Và mỗi nhịp có HÀNH ĐỘNG riêng — đó là thứ
engine người que dùng được mà engine truyện tranh thì không: `StickAnim` có bảy tư thế cộng lớp
`live()` chạy trên chín khớp, nên "walks in", "takes a photo", "walks by" diễn được.

Rút ra: dàn vai (tên · tuổi · giới · màu áo quần) · bốn nhịp (giây · hành động · ai nói · lời).
"""
import io
import json
import os
import re

GOC = os.path.dirname(os.path.abspath(__file__))
NGUON = os.path.expanduser("~/Downloads/GROCK PROMPT VIDEOS 15S")
RA = os.path.join(GOC, "kho_15s.json")

MAU = {
    "gray": "#8C9095", "grey": "#8C9095", "blue": "#3A5C93", "light blue": "#7FA8D4",
    "navy": "#22375C", "red": "#C4453A", "green": "#3E8F5E", "light green": "#7FBF8F",
    "teal": "#2F7D8A", "yellow": "#E8B93C", "orange": "#D9793C", "purple": "#6B4A93",
    "lavender": "#9B87C4", "pink": "#D98BA6", "coral": "#E0715E", "white": "#F1EEE7",
    "black": "#2A2A2E", "brown": "#7A5638", "khaki": "#C2A778", "beige": "#D8C7A9",
    "cream": "#EDE3CE", "maroon": "#7B3B3B", "olive": "#6E7A46", "mint": "#8FC4A8",
    "blonde": "#D9B978", "gold": "#C9A24B", "silver": "#B9BDC2", "denim": "#4A6A96",
}
_TREN = r"(t-shirt|shirt|top|sweater|hoodie|cardigan|polo|blouse|jacket|vest|sweatshirt|dress)"
_DUOI = r"(jeans|pants|shorts|leggings|skirt|trousers|slacks)"


def _mau(mo: str, dau: str) -> str:
    for m in re.finditer(rf"([a-z]+(?:\s+[a-z]+)?)\s+{dau}", mo):
        for tu in reversed(m.group(1).split()):
            if tu in MAU:
                return MAU[tu]
    return ""


def _dan(than: str) -> dict:
    m = re.search(r"CHARACTER LOCK[^\n]*\n([\s\S]+?)\nKeep exact", than)
    if not m:
        return {}
    ra = {}
    for d in m.group(1).splitlines():
        mm = re.match(r"([A-Z][\w ]*?):\s*(.+)", d.strip())
        if not mm:
            continue
        ten, mo = mm.group(1).strip(), mm.group(2).lower()
        gt = re.search(r"(\d{1,2})-year-old", mo)
        so = int(gt.group(1)) if gt else 0
        tuoi = ("tre_con" if so and so <= 12 else "tre" if so and so <= 19
                else "gia" if (so >= 60 or "elderly" in mo) else "trung")
        gioi = "nam"
        if re.search(r"\b(woman|female|girl|mom|mother|grandma|nana|nani|dadi|abuela|gigi|ba noi|she|her)\b", mo):
            gioi = "nu"
        elif re.search(r"\b(blouse|dress|skirt|shawl|cardigan)\b", mo):
            gioi = "nu"
        # thú cưng: không tuổi VÀ không mặc gì
        thu = (not gt and "elderly" not in mo and not re.search(_TREN + "|" + _DUOI, mo))
        ra[ten] = {"tuoi": tuoi, "gioi": gioi, "so_tuoi": so, "thu": thu,
                   "ao": _mau(mo, _TREN) or "#8C9095", "quan": _mau(mo, _DUOI) or "#3A3D42",
                   "mo": mo[:160]}
    return ra


def main() -> int:
    if not os.path.isdir(NGUON):
        print(f"❌ không thấy {NGUON}")
        return 1
    kho = {}
    for t in sorted(os.listdir(NGUON)):
        if not t.endswith(".txt"):
            continue
        s = io.open(os.path.join(NGUON, t), encoding="utf-8", errors="ignore").read()
        m = re.search(r"NEW CHANNEL: (.+)|CHANNEL: (.+)", s)
        ten = (m.group(1) or m.group(2)).strip() if m else t[:24]
        de = re.sub(r"[^a-z0-9]", "", ten.lower())[:14] or t[:10]
        khoi = re.split(r"\n(\d{4}) — ", s)[1:]
        cap = list(zip(khoi[0::2], khoi[1::2]))
        if not cap:
            continue
        # DÀN VAI NẰM Ở ĐẦU TỆP, không nằm trong prompt. Bản đầu đọc từ `cap[0][1]` (thân
        # prompt 0001) nên `dan` rỗng, và vì lượt thoại chỉ được nhận khi `ai in dan`, cả
        # 25.000 prompt đều bị loại — ra 0 tập mà không lỗi nào báo.
        dan = _dan(s)
        vai = sorted(dan, key=len, reverse=True)
        tap = []
        for so, than in cap:
            mk = re.search(r"SCENE AND DIALOGUE[^\n]*\n([\s\S]+?)\n\s*DIRECTOR NOTE", than)
            if not mk:
                continue
            nhip = []
            for mm in re.finditer(r"(\d+)-(\d+)s:\s*([^\n]+)((?:\n(?!\d+-\d+s:|DIRECTOR)[^\n]+)*)",
                                  mk.group(1)):
                khoi_van = (mm.group(3) + "\n" + (mm.group(4) or "")).strip()
                # lời thoại: `Ten: "..."` ở bất kỳ đâu trong nhịp
                # AI NÓI = TÊN VAI CUỐI CÙNG xuất hiện TRƯỚC dấu nháy, không phải chữ ngay
                # trước dấu hai chấm. Nhịp thứ tư thường viết kiểu:
                #   "Nana Bea walks by without stopping: 'I've seen worse... from him.'"
                # -> chữ ngay trước dấu hai chấm là "stopping", nên bản đầu gán nhầm rồi loại
                # cả câu. Mất trọn nhịp CHỐT của mỗi tập — mà nhịp chốt là chỗ buồn cười nhất.
                loi = []
                for q in re.finditer(r'"([^"]+)"', khoi_van):
                    truoc = khoi_van[:q.start()]
                    ai = ""
                    vt = -1
                    for v in dan:
                        i = truoc.rfind(v)
                        if i > vt:
                            vt, ai = i, v
                    if ai:
                        loi.append([q.group(1).replace("\u2019", "'"), ai])
                hanh = re.sub(r'[A-Z][\w ]*?:\s*"[^"]+"', "", khoi_van)
                hanh = " ".join(hanh.split())[:140]
                nhip.append({"s": int(mm.group(1)), "e": int(mm.group(2)),
                             "hanh": hanh, "loi": loi})
            if len(nhip) >= 3 and sum(len(n["loi"]) for n in nhip) >= 2:
                tap.append({"so": int(so), "ten": than.split("\n")[0].strip(), "nhip": nhip})
        kho[de] = {"ten": ten, "dan": dan, "tap": tap}
        n_loi = sum(len(n["loi"]) for x in tap for n in x["nhip"])
        print(f"  {ten[:26]:28s} {len(tap):5d} tập · {n_loi} lượt thoại · "
              f"dàn {len([1 for v in dan.values() if not v['thu']])} người + "
              f"{len([1 for v in dan.values() if v['thu']])} thú")

    io.open(RA, "w", encoding="utf-8").write(json.dumps(kho, ensure_ascii=False))
    print(f"\n  ✅ {len(kho)} kênh · {sum(len(v['tap']) for v in kho.values())} tập -> kho_15s.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
