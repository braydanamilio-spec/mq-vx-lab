#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MƯỜI KÊNH 6 GIÂY TỪ GÓI GROCK — MỘT PIPELINE, KHÔNG MƯỜI BẢN SAO  (1/9/2026)

Anh: *"từ cách làm 10 channel funny trước làm cho a 10 channel mới"* và *"này là kịch bản cho
videos 6s"*.

Dùng lại nguyên khuôn ba nhịp đã duyệt ở HOUSE RULES — 0,8s giữ khung (thẻ hook) · hai panel
thoại · một panel LẬT giữ hình không lời — ra đúng 6,0 giây như gói quy định.

**Một pipeline cho mười kênh, không mười tệp.** Mỗi kênh khác nhau ở BẢNG, không ở MÃ:
dàn nhân vật (đọc từ CHARACTER LOCK), bảng màu, nét vẽ, nơi chốn. Mười tệp giống nhau 95% là
cách chắc chắn để sửa một chỗ quên chín chỗ — họ lỗi đã trả giá sáu lần trong hai ngày.

Cơ chế 6 giây và mười lối dựng dùng lại từ `kich_kling` (`_nhip_6_giay`, `LOI_DUNG`), không
chép lại: hai bản của một luật rồi sẽ lệch nhau.
"""
import argparse
import io
import json
import os
import subprocess

from kich_hai import doc_hai_giong, lam_thumb, GOC, ENG, PUB
from kich_comic import GIONG_VAI, _sang_cua, _am_nhac
from kich_kling import LOI_DUNG, LOI_DUNG_TT, MO_DAU, _nhip_6_giay, _dai
from chuan_am import chuan

KHO = os.path.join(GOC, "kho_grock.json")

# ── NÉT RIÊNG TỪNG KÊNH ───────────────────────────────────────────────────────────────────
# Anh đã dặn từ bộ comic: *"tránh họ nhìn vào biết cùng 1 người làm"*. Mười kênh này còn dễ
# giống nhau hơn bộ comic vì chúng CÙNG một thể loại (hài gia đình trong nhà). Nên phải tách
# bằng năm trục cùng lúc: hai màu thương hiệu · độ dày mực · cỡ halftone · bo bong bóng · chữ nổ.
# Không tổ hợp nào trùng nhau, và cũng không trùng mười kênh comic (net 5-10, cham 7-14).
NET = {
    "modernfam":  dict(mau="#E0533D", phu="#2F7D6B", net=8, cham=6,  bo=24, no="OOPS!"),
    "kevinlaura": dict(mau="#3F7CC9", phu="#E08A3C", net=6, cham=12, bo=16, no="WHAT?!"),
    "marcussofia":dict(mau="#C7522A", phu="#3B7A57", net=9, cham=5,  bo=30, no="HEY!"),
    "ethanmaya":  dict(mau="#7A4FA3", phu="#D9A441", net=5, cham=9,  bo=34, no="AH!"),
    "chrisangela":dict(mau="#2E8B84", phu="#D4553F", net=10,cham=15, bo=8,  no="UGH!"),
    "houserules": dict(mau="#E0533D", phu="#2F7D6B", net=8, cham=6,  bo=24, no="WAIT!"),
    "thurung":    dict(mau="#A9722E", phu="#4C7F9E", net=7, cham=13, bo=28, no="YIP!"),
    "quaivat":    dict(mau="#6B3FA0", phu="#5FA355", net=10,cham=16, bo=12, no="GRR!"),
    "robot":      dict(mau="#2F6FA8", phu="#C9A24B", net=6, cham=4,  bo=6,  no="BEEP!"),
    "alien":      dict(mau="#3E9E86", phu="#B45FA0", net=7, cham=7,  bo=32, no="ZAP!"),
}
# Nơi chốn: cùng mười loại phòng (đều là hài gia đình trong nhà), nhưng mỗi kênh một PHONG_CACH
# riêng ở `nen_cf.py` nên ra mười CĂN NHÀ khác nhau, không phải mười lần cùng một căn.
NOI = ["the kitchen", "the living room", "the front entry hall", "the dining table",
       "the garage", "the back porch", "the laundry room", "the kid's bedroom",
       "the hallway by the stairs", "the driveway"]
# LOÀI + MÀU DA — bốn kênh phi nhân. Mắt đọc loài qua MÀU DA trước, rồi mới tới tai/sừng/
# ăng-ten. Không dùng AI vẽ nhân vật: AI không giữ được nhân dạng qua 2.500 tập và không làm
# được khẩu hình khớp giọng — hai thứ gói của anh khoá chặt. AI lo BỐI CẢNH, engine lo NGƯỜI.
LOAI = {"thurung": ("thu", "#B08247"), "quaivat": ("quai", "#8E7BB8"),
        "robot": ("robot", "#B9BDC2"), "alien": ("alien", "#8FC4A8")}

NHAC = {"modernfam": "music/carefree.mp3", "kevinlaura": "music/km_undaunted.mp3",
        "marcussofia": "music/km_interloper.mp3", "ethanmaya": "music/inspired.mp3",
        "chrisangela": "music/km_ascending.mp3", "houserules": "music/carefree.mp3",
        "thurung": "music/forecast.mp3", "quaivat": "music/mind_pad32.mp3",
        "robot": "music/mindloop_pad.mp3", "alien": "music/km_reawakening.mp3"}


def _kho() -> dict:
    return json.load(io.open(KHO, encoding="utf-8"))


def _giong(v: dict, i: int) -> tuple:
    ds = GIONG_VAI.get((v["gioi"], v["tuoi"])) or GIONG_VAI[("nam", "trung")]
    return ds[i % len(ds)]


# Nét mặt: bốn trục, mỗi trục vài lựa chọn. Bốc theo BĂM CỦA TÊN VAI nên Derek luôn ra đúng
# một khuôn mặt ở mọi tập, mà Derek với Kevin thì khác nhau.
# GIÁ TRỊ PHẢI KHỚP KIỂU CỦA ENGINE (`Kieu` trong `v2/DienVien.tsx`). 1/9 — bản đầu bịa
# `cuoi`, `cong`, `boc`, `hoi_xoan`, và `dai` (đã dùng cho HOUSE RULES từ hôm qua). Engine
# không nhận thì nó IM LẶNG rơi về mặc định — tức mọi nhân vật lại chung một khuôn mặt, đúng
# thứ đang đi sửa. Kiểu TypeScript không cứu được vì props đi qua JSON.
_MUI = ["moc", "cu", "nhon", "hat", "quap"]
_MAT = ["bau", "tron", "hep", "xech"]
_MAY = ["day", "manh", "xech", "ru"]
_TOC = {"nam": ["ngan", "re_ngoi", "roi", "hoi"], "nu": ["bui", "duoi_ngua", "xoan", "bob"],
        "tre": ["ngan", "roi", "re_ngoi", "hoi"]}


def _kieu(v: dict, hat: int, ten_vai: str = "", de: str = "") -> dict:
    """Vai -> tham số vẽ của engine. Giới·tuổi·cao lấy từ CHARACTER LOCK, không bịa.

    1/9 — MẶT PHẢI KHÁC NHAU. Bản đầu chỉ đổi màu áo, nên mười kênh ra mười người đàn ông
    giống hệt nhau — đúng thứ anh cấm: *"tránh họ nhìn vào biết cùng 1 người làm"*. Màu áo là
    trục YẾU nhất: mắt đọc hình dạng khuôn mặt trước khi kịp đọc màu.
    Nay bốn trục nét mặt bốc theo BĂM CỦA TÊN VAI — nên Derek luôn là một khuôn mặt ở mọi tập
    (nhất quán, đúng CHARACTER LOCK), mà Derek với Kevin thì khác hẳn.
    Thêm hai gợi ý đọc thẳng từ mô tả gói: "dad bod / round" -> bè ngang hơn; "sleek / slim" ->
    thon hơn. Gói đã tả sẵn, không dùng thì phí.
    """
    b = sum(ord(c) * (i + 3) for i, c in enumerate(ten_vai or v.get("mo", "")[:8]))
    mo = v.get("mo", "")
    be = 1.0
    if any(x in mo for x in ("round", "dad bod", "stocky", "boxy", "compact")):
        be = 1.14
    elif any(x in mo for x in ("sleek", "slim", "slender", "lean")):
        be = 0.90
    d = {"gioi": v["gioi"], "tuoi": v["tuoi"], "cao": v["cao"],
         "ao": v["ao"], "quan": v["quan"], "loiVe": "mat_to",
         "kieuAo": v.get("kieuAo", "thun"),
         # XOÁ PHỤ KIỆN NGHỀ CỦA KIỂU GỐC. `KIEU_MAU.hang_xom`/`bank` mang sẵn
         # `phuKien: "ve_vest"` + `caVat` (chúng viết cho kênh dữ liệu: chuyên gia tài chính,
         # luật sư). Bản ghi đè trộn SAU nhưng không xoá thì hai thứ ấy vẫn còn — nên mọi nhân
         # vật gia đình đều mặc vest có ve và đeo cà vạt, che luôn cổ áo vừa thêm.
         # Đây là họ lỗi "mượn giá trị cho việc nó không sinh ra để làm": mượn kiểu gốc của
         # kênh dữ liệu cho kênh hài gia đình rồi chỉ đổi vài trường.
         "phuKien": "", "caVat": "", "aoKhoac": "",
         # Tóc theo GIỚI THẬT, không theo nhóm vẽ: bé gái 12 tuổi thuộc nhóm vẽ "tre" nên bản
         # đầu bốc tóc từ danh sách con trai — bé gái ra đầu đinh.
         "kieuToc": _TOC["nu" if v.get("gioiThat") == "nu" else "nam"][b % 4],
         "kieuMui": _MUI[(b // 4) % 5], "kieuMat": _MAT[(b // 7) % 4],
         "kieuMay": _MAY[(b // 11) % 4],
         "beNgang": be, "matTo": 0.88 + (b % 5) * 0.09, "cam": (b % 7) * 0.14,
         "tiLeDau": 0.93 + (b % 4) * 0.045,
         "kinh": (b % 5) == 0, "rau": "", "mu": "",
         # ── DÁNG ĐỨNG — trục mắt đọc TRƯỚC cả khuôn mặt ────────────────────────────────
         # 1/9, sau khi anh loại 10 kênh GROCK vì *"vẽ không ổn"*. Đo ra: mặt · màu · nhà đã
         # khác nhau, thứ giống hệt là BÓNG DÁNG — `CU_CHI` chỉ đổi cánh tay, chân thì cố định.
         # Bốc theo cùng một băm với khuôn mặt, nên Derek luôn đứng kiểu Derek qua 2.500 tập;
         # còn Derek với Kevin thì nhìn từ xa đã khác.
         # Người lớn mới đổi thế đứng; trẻ con giữ thế đều (0) vì dồn trọng tâm ở trẻ con đọc
         # ra là đứng xiêu vẹo chứ không ra tính cách.
         "dangDung": 0 if v["tuoi"] == "tre_con" else [0, 1, 2, 3, 4][(b // 17) % 5],
         "xuoiVai": [0, 0.6, -0.5, 0.3, -0.8][(b // 23) % 5],
         "nghiengRieng": [0, 0.5, -0.5, 0.8, -0.3][(b // 29) % 5]}
    if de in LOAI:
        loai, mau_da = LOAI[de]
        # Robot/alien không có tóc và không có râu — để nguyên thì ra "người đội tóc giả".
        d.update(loai=loai, da=mau_da, rau="")
        # Thú cũng bỏ tóc người: mẻ thử cho ra một người đàn ông tóc nâu có tai ẩn sau tóc —
        # tức mất luôn thứ duy nhất nói lên "đây là con gấu". Lông thì dùng chính màu da.
        if loai in ("robot", "alien", "thu"):
            d["kieuToc"] = "trocs"
    if v["tuoi"] == "tre_con":
        # Trẻ con: đầu to hơn, mắt to hơn — hai thứ đọc ra "trẻ con" nhanh hơn cả chiều cao.
        d.update(tiLeDau=0.65, matTo=1.3, beNgang=0.94, kinh=False)
    elif v["tuoi"] == "gia":
        d.update(kinh=True, rau=("ria" if v["gioiThat"] == "nam" else ""), tiLeDau=0.95)
    elif v["gioiThat"] == "nam" and (b % 3) == 0:
        d["rau"] = ["", "ria", "de"][(b // 13) % 3]
    return d


def _noi_cua_tap(t: dict, idx: int) -> int:
    """Nơi chốn suy từ chính lời thoại; không ra thì xoay theo số tập."""
    loi = (" ".join(c[0] for c in t["loi"]) + " " + t.get("hook", "")).lower()
    diem = []
    for i, n in enumerate(NOI):
        tu = [w for w in n.replace("'s", "").split() if len(w) > 3 and w != "the"]
        diem.append((sum(1 for w in tu if w in loi), -i))
    tot = max(diem)
    return -tot[1] if tot[0] > 0 else idx % len(NOI)


def mot_tap(de: str, idx: int) -> str:
    kho = _kho()
    if de not in kho:
        print(f"❌ không có kênh {de}"); return ""
    k = kho[de]
    tap = k["tap"]
    t = tap[idx % len(tap)]
    nk = NET[de]
    hat = sum(ord(c) for c in de)
    ld = LOI_DUNG[list(LOI_DUNG)[idx % len(LOI_DUNG)]]
    slug = f"{de}_{idx:04d}"
    print(f"\n▶ {k['ten']} · {t['ten'][:42]}  (prompt {t['so']:04d})", flush=True)

    loi = t["loi"][:2]
    if len(loi) < 2:
        # Một lượt thoại + hành động câm: vẫn dựng được — panel lật gánh phần còn lại. Gói viết
        # cú lật bằng HÀNH ĐỘNG nên im lặng ở đó là đúng ngôn ngữ, không phải thiếu sót.
        loi = loi + [[loi[0][0], loi[0][1]]] if not loi else loi
    # THÚ CƯNG KHÔNG ĐÓNG VAI. Engine không vẽ được chó mèo; xếp chúng vào khung là ra một
    # người lạ đứng trong bếp. Tập nào để thú cưng "nói" thì trả lời ấy cho người gần nhất.
    nguoi = [x for x, v in k["dan"].items() if not v.get("thu")]
    def _nguoi(x):
        return x if x in nguoi else (nguoi[0] if nguoi else x)
    vaiA = _nguoi(loi[0][1])
    vaiB = _nguoi(loi[1][1]) if len(loi) > 1 else ""
    if not vaiB or vaiB == vaiA:
        vaiB = next((x for x in nguoi if x != vaiA), vaiA)

    cau = [(c[0], 0 if c[1] == vaiA else 1, "nghi_ngo" if "?" in c[0] else "trung_tinh")
           for c in loi]
    ga, gb = _giong(k["dan"][vaiA], hat), _giong(k["dan"].get(vaiB, k["dan"][vaiA]), hat + 3)
    rel = f"v7_{slug}.mp3"
    try:
        dur, tu, moc = doc_hai_giong(cau, ga, gb, os.path.join(PUB, rel))
    except Exception as e:
        print(f"   ❌ giọng đọc hỏng: {str(e)[:100]}"); return ""
    if not tu:
        print("   ❌ không có mốc từ — BỎ"); return ""

    dur = _nhip_6_giay(os.path.join(PUB, rel), ld["giu"])
    moc = [(a + MO_DAU, b + MO_DAU) for a, b in moc]
    tu = [{**w, "t": w["t"] + MO_DAU} for w in tu]

    luot = [{"s": 0.0, "e": moc[0][0] - 0.02, "ai": 0, "nar": "", "camXuc": "bat_ngo",
             "camXucKia": "nghi_ngo", "cuChi": "mo_tay", "chot": False, "cam": True}]
    for i, (chu, ai, cx) in enumerate(cau):
        luot.append({"s": moc[i][0], "e": moc[i][1], "ai": ai, "nar": chu, "camXuc": cx,
                     "camXucKia": "nghi_ngo" if i == 0 else "bat_ngo",
                     "cuChi": "mo_tay" if i == 0 else "chi", "chot": False})
    luot.append({"s": moc[-1][1] + 0.04, "e": dur, "ai": ld["aiLat"], "nar": "",
                 "camXuc": "bat_ngo", "camXucKia": "nghi_ngo", "cuChi": ld["cuChi"],
                 "canh": not ld["canCanh"], "chot": ld["rung"], "cam": True})

    noi_idx = _noi_cua_tap(t, idx)
    anh = f"comic_nen/{de}_{noi_idx:02d}.jpg"
    if not os.path.exists(os.path.join(PUB, anh)):
        anh = ""
    props = {
        "luot": luot, "tu": tu, "voMp3": rel, "nhac": NHAC[de],
        "kieuA": "hang_xom", "kieuB": "bank",
        "kieuTuyA": _kieu(k["dan"][vaiA], hat, vaiA, de),
        "kieuTuyB": _kieu(k["dan"].get(vaiB, k["dan"][vaiA]), hat, vaiB, de),
        "tieuDe": k["ten"], "handle": "@" + de + "usa", "kenh": de,
        "mau": nk["mau"], "mauPhu": nk["phu"],
        "netMuc": nk["net"], "cham": nk["cham"], "boGoc": nk["bo"], "tiLe": 0.62,
        "hookGiay": 1.15, "soTap": idx, "noiIdx": noi_idx,
        "hook": (loi[0][0].rstrip("?.!").upper())[:38],
        "anhNen": anh, "sang": _sang_cua(anh), "nhacVol": _am_nhac(NHAC[de]),
        "bongDuoi": False, "boKhung": 14, "chuNo": nk["no"],
    }
    pj = os.path.join(GOC, "out", f"v7_{slug}.json")
    os.makedirs(os.path.dirname(pj), exist_ok=True)
    io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))

    out = os.path.join(GOC, "out", f"v7_{slug}.mp4")
    r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "KichComic", out,
                        f"--props={pj}", "--gl=swiftshader", "--log=error", "--crf", "21"],
                       cwd=ENG, capture_output=True, text=True, timeout=2400)
    if r.returncode or not os.path.exists(out):
        print(f"   ❌ render hỏng: {(r.stderr or r.stdout or '')[-220:]}"); return ""

    lam_thumb(out, t["ten"], k["ten"], nk["mau"], os.path.join(GOC, "out", f"v7_{slug}.jpg"))
    am = chuan(out)
    print(f"   ✅ {os.path.basename(out)} ({os.path.getsize(out)/1e6:.1f} MB · {dur:.1f}s"
          f"{' · ' + am if am else ''})")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="", help="mã kênh; bỏ trống = cả 10")
    ap.add_argument("--tu", type=int, default=0)
    ap.add_argument("--so", type=int, default=1)
    a = ap.parse_args()
    ds = [x.strip() for x in a.kenh.split(",") if x.strip()] or list(NET)
    # Lệch số tập giữa các kênh: prompt 0001 của cả mười gói đều là "Midnight Fridge", nên dựng
    # cùng chỉ số thì mười bản demo ra cùng một câu đùa — nhìn như mười bản sao.
    ra = [v for j, de in enumerate(ds) for i in range(a.so)
          if (v := mot_tap(de, a.tu + i + (j * 37 if not a.kenh else 0)))]
    print(f"\n✅ {len(ra)}/{len(ds) * a.so} video")
    return 0 if ra else 1


if __name__ == "__main__":
    raise SystemExit(main())
