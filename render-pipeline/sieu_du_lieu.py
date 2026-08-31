#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIÊU DỮ LIỆU ĐĂNG TẢI + ẢNH BÌA (31/8/2026)
════════════════════════════════════════════════════════════════════════════════════════════

Anh: *"xây modun tạo ảnh thumbnail cho ảnh thumbnail chuẩn hook phù hợp mỗi videos long hay
short, và file upload title, descrip, tag... sao cho chuẩn."*

Một video nằm trong kho mà thiếu ba thứ này thì chưa đăng được, và ba thứ ấy quyết định lượt
xem nhiều hơn cả chất lượng hình: người ta bấm vào ẢNH BÌA và TIÊU ĐỀ trước khi thấy được một
khung hình nào.

── TIÊU ĐỀ ───────────────────────────────────────────────────────────────────────────────
Giới hạn cứng của YouTube là 100 ký tự, nhưng trên điện thoại chỉ hiện chừng 40–50 ký tự đầu
trước khi bị cắt. Nên tiêu đề ở đây luôn dồn thông tin vào nửa đầu, và không bao giờ mở bằng
tên kênh (tên kênh đã hiện ngay dưới tiêu đề rồi — lặp lại là phí đúng chỗ đắt nhất).

KHÔNG dùng câu chốt làm tiêu đề, dù nó hay nhất: đọc tiêu đề là biết trò đùa, và người ta
không bấm vào thứ mình đã biết kết quả. Tiêu đề lấy TÌNH HUỐNG, chốt để dành cho video.

── MÔ TẢ ─────────────────────────────────────────────────────────────────────────────────
Chỉ 2–3 dòng đầu hiện ra trước khi phải bấm "thêm". Ba dòng ấy viết cho NGƯỜI; phần còn lại
(chương, thẻ, dòng loạt bài) viết cho máy tìm kiếm.

── THẺ ───────────────────────────────────────────────────────────────────────────────────
Tổng độ dài mọi thẻ cộng lại không vượt 500 ký tự — đây là giới hạn dễ vượt mà không báo lỗi,
chỉ lặng lẽ cắt mất thẻ cuối. Bộ này tự cắt trước, và luôn để thẻ quan trọng nhất lên đầu.
"""
import os
import io
import re
import json
import argparse
import subprocess

from kich_hai import KENH, KHO, _ten_tep, GOC, ENG
from kich_comic import MAU_CHINH, MAU_PHU, NET_KENH, VAI, vai_va_giong, _hai_bong

# Chủ đề để gắn thẻ — mỗi kênh một nhúm từ mà người Mỹ thật sự gõ khi tìm loại nội dung này.
THE_KENH = {
    "rent":     ["rent", "landlord", "apartment", "renting", "tenant rights"],
    "gym":      ["gym", "workout", "fitness", "personal trainer", "gym humor"],
    "airport":  ["airport", "flight delay", "travel", "airline", "tsa"],
    "car":      ["car repair", "mechanic", "auto shop", "car trouble", "garage"],
    "office":   ["office", "work humor", "coworkers", "office life", "meetings"],
    "diet":     ["diet", "food", "snacks", "healthy eating", "calories"],
    "tech":     ["tech support", "it help", "computer problems", "wifi", "helpdesk"],
    "parent":   ["parenting", "kids", "family", "screen time", "mom life"],
    "neighbor": ["neighbors", "hoa", "suburbs", "neighborhood", "yard"],
    "dating":   ["dating", "dating app", "relationships", "couples", "first date"],
}

# Khuôn tiêu đề. Nhiều khuôn để một kênh chạy hàng trăm tập mà tiêu đề không thành một dãy
# giống hệt nhau — YouTube đọc dãy ấy đúng như đọc nội dung lặp khuôn.
KHUON_TIEU_DE = [
    "When {a} Meets {b}",
    "{b} Had One Job",
    "The {topic} Excuse Nobody Buys",
    "This Is Why {topic} Never Works",
    "{a} vs {b}: Nobody Wins",
    "Ask {b} One Simple Question",
    "The Most {topic} Answer Ever Given",
    "{b} Explains It. It Gets Worse.",
    "Nobody Warned {a} About This",
    "The {topic} Rule That Makes No Sense",
]


def _sach(t: str) -> str:
    return " ".join(str(t).replace("’", "'").split()).strip()


def _tieu_de(k: dict, cau: list, so_tap: int, dai: bool) -> str:
    va, vb = VAI[k["de"]]
    # Chủ đề lấy từ thẻ đầu tiên, KHÔNG lấy tên kênh. Tên kênh là một cái nhãn ("GYM LIES",
    # "NEIGHBOR WATCH"), nhét vào giữa câu thì ra "This Is Why Gym Lies Never Works" — đọc lủng
    # củng và không ai gõ cụm ấy khi đi tìm. Thẻ đầu tiên là từ người Mỹ thật sự dùng.
    chu_de = THE_KENH.get(k["de"], ["this"])[0].title()
    kh = KHUON_TIEU_DE[(so_tap + sum(ord(c) for c in k["de"])) % len(KHUON_TIEU_DE)]
    t = kh.format(a=va[5].title(), b=vb[5].title(), topic=chu_de)
    # Nhãn cuối: Shorts cần thẻ #shorts để vào đúng luồng; bản dài ghi rõ là tập đầy đủ.
    t = f"{t} | {k['ten']} Ep {so_tap + 1}" if dai else f"{t} #shorts"
    return t[:98]


def _mo_ta(k: dict, cau: list, so_tap: int, dai: bool, chuong=None) -> str:
    # (không dùng `list | None`: Python 3.9 trên máy anh chưa nhận cú pháp ấy ở annotation runtime)
    va, vb = VAI[k["de"]]
    mo = _sach(cau[0][0]) if cau else ""
    d = [
        f"{mo}",
        "",
        f"{va[5].title()} and {vb[5].title()} have very different ideas about how this works. "
        f"Neither of them is going to budge.",
        "",
    ]
    if dai and chuong:
        d.append("Chapters:")
        d += [f"{c}" for c in chuong[:16]]
        d.append("")
    d += [
        f"New episodes on {k.get('handle', '')} — short animated comedy about "
        f"{THE_KENH.get(k['de'], ['everyday life'])[0]}.",
        "",
        "#" + " #".join(x.replace(" ", "") for x in THE_KENH.get(k["de"], [])[:4])
        + (" #shorts" if not dai else " #animation #comedy"),
    ]
    return "\n".join(d).strip()[:4800]


def _the(k: dict, dai: bool) -> list:
    ra = [k["ten"].lower(), *THE_KENH.get(k["de"], []),
          "animated comedy", "cartoon comedy", "comedy sketch", "funny animation"]
    ra += ["full episode", "compilation"] if dai else ["shorts", "funny shorts"]
    # Giới hạn 500 ký tự cho TỔNG các thẻ — vượt thì YouTube lặng lẽ cắt, không báo gì.
    out, tong, da = [], 0, set()
    for t in ra:
        if t in da:            # "tech support" vừa là tên kênh vừa là thẻ chủ đề -> trùng
            continue
        da.add(t)
        if tong + len(t) + 1 > 480:
            break
        out.append(t); tong += len(t) + 1
    return out


# ══ BA NỀN TẢNG, BA LUẬT KHÁC NHAU ═════════════════════════════════════════════════════
# Anh: *"nhớ chuẩn file upload cho fb, insta nữa vì mình có youtube, fb, insta"*.
#
# Ba nơi này KHÔNG nhận cùng một bộ chữ, và chỗ khác nhau nằm ở những giới hạn mà không nơi nào
# báo lỗi khi vượt — nó chỉ lặng lẽ cắt, hoặc lặng lẽ không đăng:
#
#   YouTube   tiêu đề ≤ 100 · mô tả ≤ 5000 · TỔNG thẻ ≤ 500 ký tự · cần category + made_for_kids
#   Facebook  có tiêu đề riêng · phần chữ là NỘI DUNG BÀI ĐĂNG · hashtag ít mới hiệu quả (3–5)
#             · Reels giới hạn 90 giây, video thường thì không
#   Instagram KHÔNG có tiêu đề, chỉ caption ≤ 2200 · tối đa 30 hashtag · link trong caption
#             KHÔNG bấm được (đừng chèn) · Reels nên ≤ 90 giây
#
# Hệ quả cần nhớ: **bản dài 9 phút đăng được YouTube và Facebook, nhưng KHÔNG lên Reels của
# Instagram.** Nên mỗi bộ siêu dữ liệu tự ghi rõ nền tảng nào nhận được và nền tảng nào không,
# kèm lý do — để bộ đăng tự động không phải đoán, và không im lặng bỏ sót.
GIAY_REELS = 90


def _fb(k: dict, cau: list, tieu_de: str, dai: bool) -> dict:
    """Facebook: phần chữ là nội dung bài đăng, không phải mô tả kỹ thuật."""
    mo = _sach(cau[0][0]) if cau else ""
    the = THE_KENH.get(k["de"], [])[:3]
    return {
        "title": tieu_de.replace(" #shorts", ""),
        "description": (
            f"{mo}\n\n"
            f"New animated comedy every day on {k.get('handle', '')}.\n"
            + " ".join("#" + x.replace(" ", "") for x in the)
        ),
        # FB quyết định trong 3 giây đầu, nên câu mở của video cũng là câu mở của bài đăng.
        "call_to_action": "LIKE_PAGE",
    }


def _ig(k: dict, cau: list, dai: bool) -> dict:
    """Instagram: caption + đúng 30 hashtag, không tiêu đề, không link."""
    mo = _sach(cau[0][0]) if cau else ""
    goc = THE_KENH.get(k["de"], [])
    chung = ["animation", "cartoon", "comedy", "funny", "animatedshorts", "comedyreels",
             "cartoonshorts", "sketchcomedy", "relatable", "dailylaugh", "toon", "reels",
             "funnyvideos", "comedyanimation", "animatedseries", "2danimation", "humor",
             "lol", "viralreels", "explorepage"]
    tags = [x.replace(" ", "") for x in goc] + chung
    tags = list(dict.fromkeys(tags))[:30]        # Instagram chặn ở 30, thừa thì hỏng cả cụm
    return {
        "caption": f"{mo}\n\n" + " ".join("#" + t for t in tags),
        "share_to_feed": True,
    }


def lam_bia(k: dict, hook: str, so_tap: int, dai: bool, dest: str) -> bool:
    """Dựng ảnh bìa bằng Remotion. Trả True nếu ra tệp."""
    kieuA, kieuB, ghiA, ghiB, _ga, _gb = vai_va_giong(k)
    tuyA, tuyB = _hai_bong(k)
    tuyA.update(ghiA); tuyB.update(ghiB)
    props = {
        "hook": hook, "kieuA": kieuA, "kieuB": kieuB, "kieuTuyA": tuyA, "kieuTuyB": tuyB,
        "tieuDe": k["ten"], "handle": k.get("handle", ""),
        "mau": MAU_CHINH.get(k["de"], "#E4572E"), "mauPhu": MAU_PHU.get(k["de"], "#1F7AE0"),
        "kenh": _ten_tep(k), "soTap": so_tap, "camXuc": "bat_ngo", "ngang": dai,
    }
    pj = dest + ".props.json"
    io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))
    comp = "ThumbComicWide" if dai else "ThumbComicDoc"
    r = subprocess.run(["npx", "remotion", "still", "src/index.ts", comp, dest,
                        f"--props={pj}", "--gl=swiftshader", "--log=error"],
                       cwd=ENG, capture_output=True, text=True, timeout=900)
    try:
        os.remove(pj)
    except OSError:
        pass
    if r.returncode or not os.path.exists(dest):
        print(f"   ❌ bìa hỏng: {(r.stderr or r.stdout or '')[-160:]}")
        return False
    return True


def mot_video(k: dict, so_tap: int, dai: bool, lam_anh: bool = True) -> str:
    slug = _ten_tep(k)
    tien = "v5L_" if dai else "v5_"
    mp4 = os.path.join(GOC, "out", f"{tien}{slug}.mp4")
    if not os.path.exists(mp4):
        print(f"   ⏭ {k['ten']}: chưa có {os.path.basename(mp4)}")
        return ""

    pj = os.path.join(GOC, "out", f"{tien}{slug}.json")
    cau, chuong = [], []
    if os.path.exists(pj):
        d = json.load(io.open(pj, encoding="utf-8"))
        cau = [(l["nar"], l["ai"], l.get("camXuc", "")) for l in d.get("luot", [])]
    if not cau:
        cau = [(c[0], c[1], c[2]) for c in KHO[k["de"]][so_tap % len(KHO[k["de"]])]["loi"]]

    # Chữ bìa lấy câu NGẮN NHẤT trong ba lượt đầu, không phải câu đầu tiên. Câu đầu thường là
    # câu dựng bối cảnh nên dài; câu ngắn trong nhóm ấy gần như luôn là câu đắt — và ngắn thì
    # vừa bìa mà không phải cắt.
    dau = [_sach(c[0]) for c in cau[:3]] or [k["ten"]]
    hook = min(dau, key=lambda x: len(x.split()))
    bia = os.path.join(GOC, "out", f"{tien}{slug}.jpg")
    if lam_anh:
        lam_bia(k, hook, so_tap, dai, bia)

    try:
        giay = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
            capture_output=True, text=True, timeout=60).stdout.strip() or 0)
    except Exception:
        giay = 0.0

    td = _tieu_de(k, cau, so_tap, dai)
    # Nền tảng nào nhận được video này. Ghi rõ cả lý do KHÔNG nhận, để bộ đăng tự động không
    # phải đoán và cũng không im lặng bỏ sót.
    hop = {"youtube": True, "facebook": True,
           "instagram": giay <= GIAY_REELS and not dai}
    ly_do = {} if hop["instagram"] else {
        "instagram": f"dài {giay:.0f}s — Reels giới hạn {GIAY_REELS}s" if giay > GIAY_REELS
                     else "bản dài không hợp định dạng Reels"}

    tai = {
        "video": os.path.basename(mp4),
        "thumbnail": os.path.basename(bia) if os.path.exists(bia) else "",
        "kenh": k["ten"], "handle": k.get("handle", ""), "slug": slug,
        "loai": "long" if dai else "short", "so_tap": so_tap,
        "giay": round(giay, 1),
        "khung_hinh": "16:9" if dai else "9:16",
        "dang_duoc": hop, "khong_dang_vi": ly_do,

        "youtube": {
            "title": td,
            "description": _mo_ta(k, cau, so_tap, dai, chuong),
            "tags": _the(k, dai),
            # Ba trường dưới đây bắt buộc khi đăng qua API và hay bị bỏ quên:
            "category_id": "23",       # Comedy
            "made_for_kids": False,    # khai sai là rủi ro pháp lý, không phải lỗi kỹ thuật
            "default_language": "en",
            "privacy": "public",
        },
        "facebook": _fb(k, cau, td, dai),
        "instagram": _ig(k, cau, dai) if hop["instagram"] else None,
    }
    dest = os.path.join(GOC, "out", f"{tien}{slug}.tai.json")
    io.open(dest, "w", encoding="utf-8").write(json.dumps(tai, ensure_ascii=False, indent=1))
    _n = [x for x, v in tai['dang_duoc'].items() if v]
    print(f"   ✅ {k['ten']:19s} {tai['youtube']['title'][:44]:44s} → {'+'.join(_n)}")
    return dest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--vong", type=int, default=0)
    ap.add_argument("--long", action="store_true", help="làm cho bản dài 16:9")
    ap.add_argument("--khong-anh", action="store_true", help="chỉ sinh siêu dữ liệu, không dựng bìa")
    a = ap.parse_args()

    chon = KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [x for x in KENH if x["ten"].replace(" ", "").upper() in vt]
    ra = [v for v in (mot_video(k, a.vong, a.long, not a.khong_anh) for k in chon) if v]
    print(f"\n{'✅' if ra else '⚠️'} {len(ra)}/{len(chon)} bộ đăng tải")
    return 0 if ra else 1


if __name__ == "__main__":
    raise SystemExit(main())
