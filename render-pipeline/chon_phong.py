#!/usr/bin/env python3
"""Chọn phông cho 18 kênh bằng SỐ ĐO, không bằng cảm giác.

Anh: *"tự chọn cái nào cho phù hợp từng channel, phải dùng phân tích hay có công cụ nào
phân tích đánh giá rồi tự chọn"*.

Lý do phải có công cụ: hôm nay em chọn sai bằng mắt nhiều lần liên tiếp (hình nhập, icon,
bảng màu). Cảm giác của em không dùng được ở việc này. Số đo thì dùng được — và quan trọng
hơn, nó ĐO ĐƯỢC LẠI khi thêm kênh thứ 19.

── BA THỨ ĐO ĐƯỢC, VÀ VÌ SAO CHÍNH LÀ BA THỨ NÀY ────────────────────────────────────────
1. ĐỌC ĐƯỢC Ở CỠ PHỤ ĐỀ. Chữ viết tay đẹp ở cỡ lớn có thể nát ở cỡ nhỏ. Đo bằng cách dựng
   THẬT chuỗi phụ đề ở đúng cỡ pixel rồi đếm tỉ lệ mực — quá mỏng thì mất nét, quá dày thì
   các chữ dính vào nhau. §14.4 đã trả giá đúng bài này ở avatar: *kiểm bằng mắt ở CỠ THẬT,
   không ở cỡ đang xem*.
2. BỀ NGANG MỖI KÝ TỰ. Kênh có câu dài cần phông hẹp; ép phông rộng vào câu dài thì hoặc
   tràn, hoặc phải thu nhỏ chữ — và §12.12 đã ghi: thẻ tuyên bố mà bé bằng phụ đề thì nó
   không còn là tuyên bố.
3. KHOẢNG CÁCH GIỮA HAI PHÔNG. Mười tám kênh phải nhìn ra khác nhau. Đo bằng cách dựng
   cùng một chuỗi ở hai phông rồi so từng điểm ảnh — cùng nguyên tắc `kiem_da_dang.py`.

Không đo "đẹp". Không đo được, và giả vờ đo được là tự lừa mình.
"""
import json, os, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont

KHO = os.path.join(os.environ.get("TMPDIR") or "/tmp", "mm0_phong")
GH = "https://raw.githubusercontent.com/google/fonts/main"

# 20 ứng viên — nhóm viết tay (hợp nét mực trên giấy) + nhóm truyện tranh (mạnh cho số).
UNG_VIEN = [
    ("Permanent Marker", "ofl/permanentmarker/PermanentMarker-Regular.ttf", "tay"),
    ("Caveat Brush",     "ofl/caveatbrush/CaveatBrush-Regular.ttf", "tay"),
    ("Patrick Hand",     "ofl/patrickhand/PatrickHand-Regular.ttf", "tay"),
    ("Gochi Hand",       "ofl/gochihand/GochiHand-Regular.ttf", "tay"),
    ("Architects Daughter", "ofl/architectsdaughter/ArchitectsDaughter-Regular.ttf", "tay"),
    ("Kalam",            "ofl/kalam/Kalam-Bold.ttf", "tay"),
    ("Indie Flower",     "ofl/indieflower/IndieFlower-Regular.ttf", "tay"),
    ("Shadows Into Light", "ofl/shadowsintolight/ShadowsIntoLight-Regular.ttf", "tay"),
    ("Just Another Hand", "ofl/justanotherhand/JustAnotherHand-Regular.ttf", "tay"),
    ("Amatic SC",        "ofl/amaticsc/AmaticSC-Bold.ttf", "tay"),
    ("Coming Soon",      "ofl/comingsoon/ComingSoon-Regular.ttf", "tay"),
    ("Schoolbell",       "ofl/schoolbell/Schoolbell-Regular.ttf", "tay"),
    ("Bangers",          "ofl/bangers/Bangers-Regular.ttf", "truyen"),
    ("Luckiest Guy",     "ofl/luckiestguy/LuckiestGuy-Regular.ttf", "truyen"),
    ("Titan One",        "ofl/titanone/TitanOne-Regular.ttf", "truyen"),
    ("Lilita One",       "ofl/lilitaone/LilitaOne-Regular.ttf", "truyen"),
    ("Chewy",            "ofl/chewy/Chewy-Regular.ttf", "truyen"),
    ("Bowlby One",       "ofl/bowlbyone/BowlbyOne-Regular.ttf", "truyen"),
    ("Baloo 2",          "ofl/baloo2/Baloo2%5Bwght%5D.ttf", "truyen"),
    ("Fredoka",          "ofl/fredoka/Fredoka%5Bwdth,wght%5D.ttf", "truyen"),
]

MAU_PHU = "The line is on a map you never saw."   # chuỗi phụ đề thật, lấy từ tập đã dựng
MAU_SO = "2,000"
CAO_PHU = 34          # cỡ pixel của phụ đề khi khung 1080 rộng — đo từ bản dựng thật


def _tai(duong: str) -> str:
    os.makedirs(KHO, exist_ok=True)
    ten = duong.split("/")[-1].replace("%5B", "[").replace("%5D", "]").replace("%2C", ",")
    dich = os.path.join(KHO, ten)
    if os.path.exists(dich) and os.path.getsize(dich) > 20000:
        return dich
    # Kho `google/fonts` để phông theo GIẤY PHÉP, không theo tên: phông cũ nằm ở `apache/`,
    # phông mới ở `ofl/`. Không có cách nào biết trước ngoài thử — nên thử cả hai thay vì
    # chép tay một danh sách ngoại lệ (§13.9).
    loi = None
    for goc in ("ofl", "apache"):
        d2 = "/".join([goc] + duong.split("/")[1:])
        try:
            rq = urllib.request.Request(f"{GH}/{d2}", headers={"User-Agent": "mm0/1.0"})
            b = urllib.request.urlopen(rq, timeout=40).read()
            if len(b) > 20000:
                with open(dich, "wb") as f:
                    f.write(b)
                return dich
        except Exception as e:
            loi = e
    raise loi or RuntimeError("không tải được")


def _anh(fp, chu, cao, W=1000, H=90):
    im = Image.new("L", (W, H), 255)
    ImageDraw.Draw(im).text((6, H // 2), chu, font=ImageFont.truetype(fp, cao),
                            fill=0, anchor="lm")
    return im


def do(fp):
    """Ba số đo của một phông."""
    im = _anh(fp, MAU_PHU, CAO_PHU)
    px = im.load()
    W, H = im.size
    # bề ngang thật của chuỗi
    rong = 0
    for x in range(W - 1, -1, -1):
        if any(px[x, y] < 128 for y in range(H)):
            rong = x
            break
    muc = sum(1 for x in range(rong + 1) for y in range(H) if px[x, y] < 128)
    hop = max(1, (rong + 1) * H)
    # nét mảnh quá thì mất ở cỡ nhỏ; dày quá thì các chữ dính nhau
    return {
        "rong_ky_tu": round((rong + 1) / len(MAU_PHU), 2),   # px mỗi ký tự
        "ti_le_muc": round(muc / hop, 4),                     # đậm nhạt ở cỡ phụ đề
        "anh": im.crop((0, 0, max(1, rong + 1), H)),
    }


def khac(a, b):
    """Khoảng cách hai phông: dựng cùng chuỗi, so từng điểm ảnh sau khi chuẩn hoá bề ngang."""
    A, B = a["anh"], b["anh"]
    n = (420, 60)
    A = A.resize(n).point(lambda v: 0 if v < 128 else 255)
    B = B.resize(n).point(lambda v: 0 if v < 128 else 255)
    pa, pb = A.load(), B.load()
    lech = sum(1 for x in range(n[0]) for y in range(n[1]) if pa[x, y] != pb[x, y])
    return round(lech / (n[0] * n[1]), 4)


def nhu_cau_kenh():
    """Nhu cầu chữ THẬT của từng kênh — đọc từ `kich_ban`, không chép tay (§13.2)."""
    import statistics as st
    import giai_thich as G
    ra = {}
    for k in G.KENH:
        dai, so, n = [], 0, 0
        for idx in range(2100, 2104):
            for x in G.kich_ban(k["ma"], idx)[4]:
                n += 1
                if x.get("loi"):
                    dai.append(len(x["loi"]))
                if x.get("so"):
                    so += 1
        ra[k["ma"]] = {"dai_tb": round(st.mean(dai), 1), "dai_max": max(dai),
                       "ti_le_so": round(so / max(1, n), 2)}
    return ra


def gan(dat, nc):
    """Gán phông cho 18 kênh: hợp nhu cầu TRƯỚC, khác nhau nhiều nhất SAU.

    Thứ tự ấy là một quyết định, không phải tiện tay. Đa dạng mà chữ tràn khung thì đa dạng
    ấy vô nghĩa — §12.12: một thẻ tuyên bố bé bằng phụ đề thì nó không còn là tuyên bố.
    Nên ràng buộc CỨNG (vừa khung) lọc trước, rồi mới tối ưu cái MỀM (khác nhau).
    """
    ten = sorted(dat)
    # bề ngang cho phép: 1080px khung dọc, chừa lề 8% mỗi bên, chữ xuống tối đa 2 dòng
    TRAN = (1080 * 0.84) * 2
    ra, dung = {}, []
    for ma in sorted(nc, key=lambda m: -nc[m]["dai_max"]):
        hop = [t for t in ten if dat[t]["rong_ky_tu"] * nc[ma]["dai_max"] <= TRAN]
        if not hop:
            hop = sorted(ten, key=lambda t: dat[t]["rong_ky_tu"])[:3]
        # trong số phông vừa khung, lấy cái XA NHẤT so với những phông đã dùng
        def diem(t):
            if not dung:
                return 0.0
            return min(khac(dat[t], dat[u]) for u in dung)
        tot = max(hop, key=lambda t: (diem(t), -abs(dat[t]["ti_le_muc"] - 0.10)))
        ra[ma] = tot
        dung.append(tot)
        if len(dung) > 6:
            dung.pop(0)      # cửa sổ trượt: chỉ cần khác những kênh GẦN nhau trong bảng
    return ra


def main() -> int:
    print("── TẢI VÀ ĐO ─────────────────────────────────────────────")
    bang = {}
    for ten, duong, nhom in UNG_VIEN:
        try:
            fp = _tai(duong)
            d = do(fp)
            d["nhom"] = nhom
            bang[ten] = d
            print(f"  {ten:22s} {nhom:6s} rộng {d['rong_ky_tu']:5.2f} px/ký tự · "
                  f"mực {d['ti_le_muc']:.3f}")
        except Exception as e:
            print(f"  {ten:22s} ✗ {str(e)[:52]}")
    if len(bang) < 8:
        raise RuntimeError(f"chỉ đo được {len(bang)} phông — không đủ để chọn")

    # ── LOẠI PHÔNG KHÔNG ĐỌC ĐƯỢC Ở CỠ PHỤ ĐỀ ─────────────────────────────────────────
    # Ngưỡng lấy từ chính phông đang dùng (Poppins ~0,105 ở cỡ này): dưới 0,055 là nét quá
    # mảnh, mất chữ khi YouTube nén; trên 0,20 là quá dày, các chữ dính nhau.
    dat = {k: v for k, v in bang.items() if 0.055 <= v["ti_le_muc"] <= 0.20}
    print(f"\n  đọc được ở cỡ phụ đề: {len(dat)}/{len(bang)}")
    for k in bang:
        if k not in dat:
            print(f"    ✗ loại {k}: mực {bang[k]['ti_le_muc']:.3f} ngoài khoảng an toàn")
    print("\n── NHU CẦU TỪNG KÊNH ─────────────────────────────────────")
    nc = nhu_cau_kenh()
    print("\n── GÁN ───────────────────────────────────────────────────")
    ket = gan(dat, nc)
    for ma in sorted(ket):
        print(f"  {ma:12s} câu dài nhất {nc[ma]['dai_max']:3d} · số {nc[ma]['ti_le_so']:.2f}"
              f"  ->  {ket[ma]}")
    from collections import Counter
    c = Counter(ket.values())
    print(f"\n  {len(c)} phông khác nhau cho {len(ket)} kênh · "
          f"dùng nhiều nhất {c.most_common(1)[0][1]} lần")
    json.dump(ket, open(os.path.join(KHO, "gan.json"), "w"), indent=1)
    print(f"  kết quả ghi ở {KHO}/gan.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
