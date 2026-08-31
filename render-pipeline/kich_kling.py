#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HOUSE RULES — kênh dựng từ gói 1.500 prompt của anh  (1/9/2026)

Anh gửi `Kling_1500_Funny_USA_Hook_6s_100100.txt` và bảo dựng thành một kênh. Gói viết cho
Kling (sinh video bằng AI), nhưng ta KHÔNG dùng Kling: hệ trên GitHub chạy bằng khoá sẵn có,
và một kênh Kling trước đây đã phải tạm dừng đúng vì lý do ấy. Thứ đáng giá trong gói không
nằm ở chỗ nó gọi Kling — mà ở **kịch bản**: dàn nhân vật khoá cứng, nhịp 6 giây tính sẵn, một
cú lật mỗi tập. Engine truyện tranh của mình vẽ đúng thứ prompt mô tả: 2D, viền mực đậm, màu
tươi, 9:16, thoại có khẩu hình.

CẤU TRÚC MỘT TẬP — đọc thẳng từ dòng thời gian của gói:

    0.0–0.8  HOOK             -> thẻ hook đầu video
    0.8–2.5  SETUP            -> panel 1: câu hỏi
                                 panel 2: câu đáp
    2.5–4.9  PUNCHLINE/REVEAL -> panel 3, GIỮ HÌNH KHÔNG LỜI (gói viết cú lật bằng hành động:
                                 "Mike freezes and looks at his hand")
    4.9–6.0  REACTION/BUTTON  -> mười biến thể, mỗi biến thể một LỐI DỰNG khác

Mười lối dựng ấy là lý do 1.500 prompt không phải 150 video nhân mười bản sao. Chúng đổi cách
CHỐT, và engine dựng mỗi cách một kiểu — xem `LOI_DUNG` bên dưới.

DÀN NHÂN VẬT khoá theo đúng CHARACTER LOCK của gói. Chiều cao đặt theo quan hệ thật trong nhà:
bố cao nhất, mẹ thấp hơn một chút, ông đã còng nên thấp hơn bố, thằng bé thấp hẳn. Anh đã dặn
riêng chuyện này (*"con đứng với mẹ thì con phải thấp hơn mẹ"*).
"""
import argparse
import io
import json
import os
import subprocess

from kich_hai import doc_hai_giong, _ten_tep, lam_thumb, GOC, ENG, PUB
from kich_comic import GIONG_VAI, noi_va_nen, _sang_cua, _am_nhac
from chuan_am import chuan

KENH_KLING = {
    "de": "houserules",
    "ten": "HOUSE RULES",
    "handle": "@houserulesusa",
    "mau": "#EDE7DA",
    "nen": "",
}
MAU_CHINH = "#E0533D"        # đỏ gạch ấm — bếp núc, nhà cửa
MAU_PHU = "#2F7D6B"          # xanh lá trầm, đối màu với áo Lisa nên chữ nổi trên mọi nền

# ── DÀN NHÂN VẬT — CHARACTER LOCK của gói, dịch sang tham số engine ────────────────────────
# Màu áo/quần lấy đúng mô tả: Mike áo trắng quần xanh · Lisa áo xanh lá quần tím · Tommy áo
# vàng quần xanh · Joe áo khoác xanh quần kaki, mũ đỏ, ria trắng lớn.
DAN = {
    "mike": dict(ten="Mike", gioi="nam", tuoi="trung", cao=1.00,
                 ao="#F4F1EA", quan="#3A5C93", beNgang=1.14, matTo=0.96, cam=0.55,
                 kieuMui="hat", kieuMat="tron", kieuMay="manh", tiLeDau=0.98,
                 kinh=False, rau="", mu=""),
    "lisa": dict(ten="Lisa", gioi="nu", tuoi="trung", cao=0.94,
                 ao="#3E8F5E", quan="#6B4A93", beNgang=0.92, matTo=1.06, cam=0.10,
                 kieuMui="quap", kieuMat="hep", kieuMay="ru", tiLeDau=1.02,
                 kinh=False, rau="", mu=""),
    "tommy": dict(ten="Tommy", gioi="tre", tuoi="tre_con", cao=0.74,
                  ao="#F2C230", quan="#3A5C93", beNgang=0.94, matTo=1.30, cam=0.05,
                  kieuMui="hat", kieuMat="tron", kieuMay="manh", tiLeDau=0.65,
                  kinh=False, rau="", mu=""),
    "joe": dict(ten="Grandpa Joe", gioi="nam", tuoi="gia", cao=0.96,
                ao="#2F5D8A", quan="#C2A778", beNgang=1.06, matTo=0.90, cam=0.85,
                kieuMui="quap", kieuMat="hep", kieuMay="ru", tiLeDau=0.95,
                kinh=True, rau="ria", mu="luoi_trai"),
}

# ── MƯỜI LỐI DỰNG ─────────────────────────────────────────────────────────────────────────
# Mỗi biến thể trong gói đổi nhịp chốt. Nếu engine dựng cả mười y hệt nhau thì 1.500 video
# thành 150 video nhân mười bản sao — cách nhanh nhất để một kênh bị coi là rác. Nên mỗi lối
# dựng đổi ba thứ có thật trên màn hình: chữ nổ, thời lượng giữ cú lật, và cỡ cảnh của panel
# chốt.
# `canCanh=True` -> panel lật là cỡ CẬN (một mặt chiếm khung); False -> cỡ RỘNG (thấy cả hai).
# `aiLat` -> ai đứng trong khung lật: 0 người nói câu đầu, 1 người đáp. Đây là chỗ "REACTION
# CUT" khác "FAST REVEAL": cùng một cú lật, nhưng máy nhìn vào mặt khác nhau.
# `cuChi` -> tư thế ở nhịp chốt. Ba trục này cộng lại làm mười biến thể ra mười video khác
# nhau thật, thay vì một video nhân mười bản sao.
LOI_DUNG = {
    "fast_reveal":      dict(no="WAIT!",   giu=1.10, canCanh=True,  aiLat=0, cuChi="gio_len",    rung=True),
    "deadpan":          dict(no="",        giu=1.70, canCanh=True,  aiLat=1, cuChi="khoanh_tay", rung=False),
    "push_in":          dict(no="",        giu=1.55, canCanh=True,  aiLat=0, cuChi="suy_nghi",   rung=False),
    "reaction_cut":     dict(no="",        giu=1.35, canCanh=True,  aiLat=1, cuChi="nhun_vai",   rung=False),
    "prop_reveal":      dict(no="AH!",     giu=1.45, canCanh=False, aiLat=0, cuChi="gio_len",    rung=False),
    "micro_escalation": dict(no="UH-OH!",  giu=1.60, canCanh=False, aiLat=0, cuChi="mo_tay",     rung=True),
    "freeze_button":    dict(no="",        giu=1.90, canCanh=True,  aiLat=0, cuChi="nghi",       rung=False),
    "physical_button":  dict(no="THUMP!",  giu=1.30, canCanh=False, aiLat=0, cuChi="dem",        rung=True),
    "muted":            dict(no="",        giu=1.50, canCanh=True,  aiLat=1, cuChi="nghi",       rung=False),
    "clean_timing":     dict(no="",        giu=1.25, canCanh=False, aiLat=1, cuChi="chi",        rung=False),
}
NHAC = "music/carefree.mp3"


def _kho() -> list:
    d = json.load(io.open(os.path.join(GOC, "kho_kling.json"), encoding="utf-8"))
    return d["tap"]


def _giong(vai: str, i: int) -> tuple:
    v = DAN[vai]
    ds = GIONG_VAI[(v["gioi"], v["tuoi"])]
    return ds[i % len(ds)]


MO_DAU = 0.8      # 0.0–0.8s HOOK, theo đúng dòng thời gian của gói
DAI_CHUAN = 6.0   # gói ghi "EXACTLY 6 SECONDS"


def _nhip_6_giay(mp3: str, giu: float) -> float:
    """Đưa tệp tiếng về đúng nhịp 6 giây của gói: 0,8s lặng mở đầu + thoại + giữ cú lật.

    Gói viết rõ "EXACTLY 6 SECONDS" và chia sẵn bốn nhịp. Bản đầu của tôi bỏ qua nhịp mở đầu và
    chỉ nối thêm `giu` giây ở cuối, ra 3,7 giây — ngắn hơn quy cách gần một nửa, và mất hẳn
    khoảng lặng 0,8s để người xem kịp đọc khung hình trước khi có ai nói.

    `adelay` đẩy toàn bộ tiếng lùi 0,8s; `apad` kéo phần đuôi cho tổng chạm 6,0s. Nếu thoại dài
    hơn khung 6 giây thì KHÔNG cắt — giữ nguyên và chỉ cộng thời gian giữ cú lật; thà một tập
    dài 7 giây còn hơn một câu chốt bị chặt mất vế sau.
    """
    tam = mp3 + ".tam.mp3"
    r = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", mp3,
         "-af", f"adelay={int(MO_DAU * 1000)}|{int(MO_DAU * 1000)},apad=pad_dur={giu:.2f}",
         "-c:a", "libmp3lame", "-q:a", "4", tam], capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(tam):
        os.replace(tam, mp3)
    d = _dai(mp3)
    if d < DAI_CHUAN:                      # còn thiếu -> kéo cho chạm đúng 6,0s
        tam2 = mp3 + ".tam2.mp3"
        r = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", mp3,
             "-af", f"apad=pad_dur={DAI_CHUAN - d:.2f}", "-c:a", "libmp3lame", "-q:a", "4", tam2],
            capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(tam2):
            os.replace(tam2, mp3)
        d = _dai(mp3)
    return d


def _dai(mp3: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                          "-of", "csv=p=0", mp3], capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def _im_lang(mp3: str, them: float) -> float:
    """(cũ — giữ để không gãy lời gọi nào khác) Nối `them` giây im lặng vào cuối.

    Nhịp lật của gói KHÔNG có lời — nó là hành động ("Mike freezes and looks at his hand").
    Muốn panel lật tồn tại trên dòng thời gian thì phải có bấy nhiêu giây tiếng, dù là tiếng
    im. Không có bước này thì video kết thúc ngay khi câu cuối dứt, mất luôn cú lật — tức mất
    đúng phần buồn cười.
    """
    tam = mp3 + ".tam.mp3"
    r = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", mp3,
         "-af", f"apad=pad_dur={them:.2f}", "-c:a", "libmp3lame", "-q:a", "4", tam],
        capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(tam):
        os.replace(tam, mp3)
    out = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                          "-of", "csv=p=0", mp3], capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def mot_tap(idx: int) -> str:
    kho = _kho()
    t = kho[idx % len(kho)]
    k = KENH_KLING
    slug = f"{_ten_tep(k)}_{idx:04d}"
    ld = LOI_DUNG.get(t["loiDung"], LOI_DUNG["clean_timing"])
    print(f"\n▶ {t['ten']} / {t['loiDung']}  (prompt {idx + 1:04d})", flush=True)

    loi = t["loi"]
    vaiA = loi[0][1]
    vaiB = loi[1][1] if len(loi) > 1 else ("lisa" if vaiA != "lisa" else "mike")

    # Engine vẽ đúng hai người, nên A/B lấy từ chính hai người nói của tập này. Đây là điểm
    # khác bản comic (mỗi kênh một cặp cố định): ở đây dàn có bốn người và mỗi tập một cặp.
    cau = [(c, 0 if ai == vaiA else 1, cx) for c, ai, cx in loi]
    ga, gb = _giong(vaiA, 0), _giong(vaiB, 1)
    rel = f"v6_{slug}.mp3"
    try:
        dur, tu, moc = doc_hai_giong(cau, ga, gb, os.path.join(PUB, rel))
    except Exception as e:
        print(f"   ❌ giọng đọc hỏng: {str(e)[:110]}")
        return ""
    if not tu:
        print("   ❌ không có mốc từ — BỎ")
        return ""

    dur = _nhip_6_giay(os.path.join(PUB, rel), ld["giu"])
    # Tiếng đã lùi 0,8s thì MỌI mốc thời gian phải lùi theo — cả mốc lượt lẫn mốc TỪNG TỪ.
    # Quên `tu` là bong bóng tô chữ lệch khỏi giọng đúng 0,8 giây, và đó là thứ anh bắt được
    # ngay ("voice nhớ khớp với sub 100%").
    moc = [(a + MO_DAU, b + MO_DAU) for a, b in moc]
    tu = [{**w, "t": w["t"] + MO_DAU} for w in tu]

    luot = []
    # Nhịp 0.0–0.8s: giữ khung, chưa ai nói — chỗ cho thẻ hook và cho mắt đọc bối cảnh.
    luot.append({"s": 0.0, "e": moc[0][0] - 0.02, "ai": 0, "nar": "",
                 "camXuc": "bat_ngo", "camXucKia": "nghi_ngo", "cuChi": "mo_tay",
                 "chot": False, "cam": True})
    for i, (chu, ai, cx) in enumerate(cau):
        luot.append({"s": moc[i][0], "e": moc[i][1], "ai": ai, "nar": chu, "camXuc": cx,
                     "camXucKia": "nghi_ngo" if i == 0 else "bat_ngo",
                     "cuChi": "mo_tay" if i == 0 else "chi", "chot": False})
    # Panel LẬT: giữ hình, không lời. `chot` bật cú rung và vạch tốc độ của engine.
    luot.append({"s": moc[-1][1] + 0.04, "e": dur, "ai": ld["aiLat"], "nar": "",
                 "camXuc": "bat_ngo", "camXucKia": "nghi_ngo", "cuChi": ld["cuChi"],
                 "canh": not ld["canCanh"],   # `canh` là cờ "khung RỘNG" của engine
                 "chot": ld["rung"], "cam": True})

    A = dict(DAN[vaiA]); B = dict(DAN[vaiB])
    for d in (A, B):
        d["loiVe"] = "mat_to"
        d["kieuToc"] = "ngan" if d["gioi"] != "nu" else "dai"
    idx_noi, anh = noi_va_nen(k, {"noi": ""}, cau, idx)
    props = {
        "luot": luot, "tu": tu, "voMp3": rel, "nhac": NHAC,
        "kieuA": "hang_xom", "kieuB": "bank", "kieuTuyA": A, "kieuTuyB": B,
        "tieuDe": KENH_KLING["ten"], "handle": KENH_KLING["handle"], "kenh": _ten_tep(k),
        "mau": MAU_CHINH, "mauPhu": MAU_PHU,
        "netMuc": 7, "cham": 9, "boGoc": 22, "tiLe": 0.62, "hookGiay": 1.15,
        # HOOK LÀ CÂU CHO NGƯỜI XEM, KHÔNG PHẢI CHỈ DẪN ĐẠO DIỄN. Bản đầu in thẳng dòng HOOK
        # của gói — "MIKE FRANTICALLY SEARCHES WHILE HIS KEYS ARE VISIBLY IN HIS" — vừa là văn
        # phòng dựng vừa bị cắt giữa chữ. Đúng cái lỗi đã ghi ngay trong bảng `VAI`: chú thích
        # cho người dựng và nhãn cho người xem là hai thứ khác nhau, trộn chung thì sớm muộn
        # cũng rò ra mặt trước. Câu mở của chính nhân vật MỚI là hook — nó ngắn, có thật trong
        # video, và người xem nghe lại đúng câu ấy sau một giây.
        "soTap": idx, "hook": loi[0][0].rstrip("?.!").upper()[:38],
        "anhNen": anh, "sang": _sang_cua(anh), "nhacVol": _am_nhac(NHAC),
        "bongDuoi": False, "boKhung": 0, "chuNo": ld["no"] or "…",
        "noiIdx": idx_noi,
    }
    pj = os.path.join(GOC, "out", f"v6_{slug}.json")
    os.makedirs(os.path.dirname(pj), exist_ok=True)
    io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))

    out = os.path.join(GOC, "out", f"v6_{slug}.mp4")
    r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "KichComic", out,
                        f"--props={pj}", "--gl=swiftshader", "--log=error", "--crf", "21"],
                       cwd=ENG, capture_output=True, text=True, timeout=2400)
    if r.returncode or not os.path.exists(out):
        print(f"   ❌ render hỏng: {(r.stderr or r.stdout or '')[-220:]}")
        return ""

    th = os.path.join(GOC, "out", f"v6_{slug}.jpg")
    lam_thumb(out, t["hook"] or t["ten"], KENH_KLING["ten"], MAU_CHINH, th)
    am = chuan(out)
    print(f"   ✅ {os.path.basename(out)} ({os.path.getsize(out)/1e6:.1f} MB · {dur:.1f}s"
          f"{' · ' + am if am else ''})")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tu", type=int, default=0, help="bắt đầu từ prompt thứ mấy (0 = 0001)")
    ap.add_argument("--so", type=int, default=1, help="dựng bao nhiêu tập")
    a = ap.parse_args()
    ra = [v for v in (mot_tap(a.tu + i) for i in range(a.so)) if v]
    print(f"\n✅ {len(ra)}/{a.so} video")
    return 0 if ra else 1


if __name__ == "__main__":
    raise SystemExit(main())
