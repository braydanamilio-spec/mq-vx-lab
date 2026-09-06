#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SOI KHO NỀN BẰNG PIXEL — đo trước, làm cổng sau  (6/9/2026)

── VÌ SAO ───────────────────────────────────────────────────────────────────────────────────
Anh: *"vì dùng đi dùng lại nhiều lần thì cần phải chuẩn ko lỗi là quan trọng nhất, sai sau này
là lỗi hết và chất lượng thấp kéo cả channel xuống."* Đúng, và nó đổi hẳn mức độ cẩn thận cần
có: một cảnh phim v10 hỏng làm hỏng MỘT nhịp; một NỀN hỏng làm hỏng mọi tập từng dùng nó.

── VÌ SAO TỆP NÀY CHỈ ĐO, CHƯA CHẶN ─────────────────────────────────────────────────────────
§12.3 đã trả giá: thước "độ phẳng" calibrate ở hai đầu cực (ảnh chụp 0,13 · vector 0,91) tách
sạch, tin luôn, rồi chạy thật thì 6/11 ảnh "trượt sàn" mà **cả sáu đều là cartoon đúng chất**.
Calibrate hai đầu chỉ chứng minh thước tách được HAI ĐẦU; cổng thì sống ở KHOẢNG GIỮA.
Nên bước một là in phân bố và bày ra các ca cực trị để NHÌN, không phải đặt ngưỡng.

── NĂM THƯỚC, MỖI THƯỚC MỘT LỖI ĐÃ TỪNG XẢY RA ──────────────────────────────────────────────
  sang   quá tối     -> nhân vật vector và phụ đề chìm (§15.26 đã bắt 8 nhịp nền trắng/đen)
  phang  ngả ảnh chụp-> lệch chất giữa các nền trong cùng một tập (§12.6)
  giua   giữa khung có đồ -> nhân vật đứng đè lên đồ đạc (§17.4, ba lớp cùng chọn giữa khung)
  san    thiếu dải sàn    -> nhân vật lơ lửng (§7, ba mệnh lệnh)
  trung  hai nền giống nhau -> đổi phòng mà khung vẫn đọc ra một chỗ

`sang` và `phang` dùng lại `nen_gt.do_sang`/`do_phang` — KHÔNG viết bản thứ hai (§11).
"""
import argparse, collections, json, os, sys

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)
os.environ.setdefault("GT_KHONG_CF", "1")
NEN = os.path.join(os.path.dirname(GOC), "engine-remotion", "public", "comic_nen")


def _pil():
    from PIL import Image
    return Image


def do_giua(tep):
    """Nét ở CHỖ ĐẶT CHÂN (giữa khung, 30% DƯỚI CÙNG) so với hai mép cùng dải.

    ── VÌ SAO CHỈ ĐO DẢI DƯỚI  (sửa sau khi đọc tay, 6/9/2026) ─────────────────────────────
    Bản đầu đo cả cột giữa từ nửa khung xuống đáy, và ca "xấu nhất" nó bắt là một **trường
    bắn cung có bia treo TƯỜNG** — sàn giữa hoàn toàn trống, nhân vật đứng thoải mái. Nó chấm
    trượt một nền đúng vì tường có hình.
    Thứ thật sự gây va chạm là đồ nằm TRÊN SÀN, chỗ nhân vật đặt chân. Tranh treo tường thì
    nhân vật đứng đè lên trước, không sao. Nên chỉ đo 30% dưới cùng — và ca hỏng thật (phòng
    họp có bàn giữa khung) vẫn nằm trong dải ấy."""
    try:
        Image = _pil()
        g = Image.open(tep).convert("L").resize((192, 110))
        px = g.load()

        def net(x0, x1, y0, y1):
            s = n = 0
            for y in range(y0, y1):
                for x in range(x0, x1 - 1):
                    s += abs(px[x, y] - px[x + 1, y]); n += 1
            return s / max(1, n)

        y0, y1 = 77, 108              # 30% dưới cùng = chỗ đặt chân
        giua = net(58, 134, y0, y1)
        mep = (net(0, 52, y0, y1) + net(140, 192, y0, y1)) / 2
        return round(giua / max(0.6, mep), 3)
    except Exception:
        return None


def do_san(tep):
    """Dải sàn: đo độ ĐỒNG NHẤT của 22% dưới cùng. Sàn liền mạch thì mỗi hàng gần như một màu
    và các hàng gần nhau gần bằng nhau. Trả 0–1, càng cao càng ra một mặt sàn liền."""
    try:
        Image = _pil()
        g = Image.open(tep).convert("L").resize((160, 96))
        px = g.load()
        y0 = int(96 * 0.78)
        lech_ngang = []
        for y in range(y0, 96):
            hang = [px[x, y] for x in range(160)]
            tb = sum(hang) / 160
            lech_ngang.append(sum(abs(v - tb) for v in hang) / 160)
        d = sum(lech_ngang) / len(lech_ngang)
        return round(max(0.0, 1.0 - d / 34.0), 3)
    except Exception:
        return None


def bam(tep):
    """Vân tay của HAI MÉP, không của cả khung.

    ── VÌ SAO  (sửa sau khi đọc tay, 6/9/2026) ─────────────────────────────────────────────
    Bản đầu băm cả khung 8×8 và báo **681 cặp trùng / 1.081 nền**, trong đó có cặp *"nhà hàng
    có bàn ghế"* ≈ *"phòng khách có sofa"* và *"phòng trẻ em"* ≈ *"phòng bệnh có giường"* —
    nhìn ra là khác hẳn nhau.
    Gốc: mọi nền đều bị `SAN_NEN` ép cùng MỘT bố cục — giữa trống, sàn chiếm dải dưới, đồ dồn
    hai mép. Ở 8×8 thì bố cục ấy CHIẾM HẾT vân tay, nên thước đang đo **thứ mọi nền buộc phải
    giống nhau**, tức tay nghề chung, không đo bản sắc (§13.4).
    Bản sắc của một căn phòng nằm ở ĐỒ ĐẠC hai mép. Nên băm riêng dải trái 27% và phải 27%, ở
    độ phân giải cao hơn (12×12 mỗi mép), và bỏ hẳn dải giữa."""
    try:
        Image = _pil()
        im = Image.open(tep).convert("L").resize((192, 108))
        r = ""
        for x0, x1 in ((0, 52), (140, 192)):
            o = im.crop((x0, 0, x1, 108)).resize((12, 12))
            d = list(o.getdata())
            tb = sum(d) / 144
            r += "".join("1" if v > tb else "0" for v in d)
        return r
    except Exception:
        return None


def _cach(a, b):
    return sum(1 for x, y in zip(a, b) if x != y)


# ══ DANH SÁCH LOẠI: THƯỚC LỌC RỘNG, MẮT PHÁN, ĐƯỜNG DỰNG BỎ QUA ═════════════════════════════
# Vì sao KHÔNG xoá tệp: một nền tốn 1.369 neuron; xoá nhầm là mất thật. Và vì sao KHÔNG để
# thước tự chặn: đọc tay 4 ca `giua` cao nhất thì chỉ 2 hỏng thật (mặt nước ở chỗ đặt chân ·
# bàn họp giữa khung), 2 ca kia chỉ là hoa văn phẳng trên sàn. Một cổng đúng 50% mà tự động
# loại bỏ là cỗ máy bắt oan (§13.8/§13.22).
#
# Nên ba nấc, đúng §13.23:
#     thước  -> rút gọn 1.081 nền xuống vài chục ca đáng ngờ
#     mắt    -> phán từng ca
#     sổ loại-> đường dựng bỏ qua, tệp vẫn nằm nguyên trên đĩa để xem lại
# ── KẾT QUẢ ĐỌC TAY 24 CA ĐÁNG NGỜ NHẤT  (6/9/2026) ─────────────────────────────────────────
# Hai ca hỏng thật, cả hai ở ĐỈNH bảng:
#     howlong_079   mặt nước ngay chỗ đặt chân — nhân vật đứng trên sông
#     hiddenfee_089 bàn họp giữa khung — nhân vật đứng trong bàn
# Hai mươi hai ca còn lại đều ổn, và tất cả đều trượt vì cùng MỘT lý do: **hoa văn trên mặt
# sàn** (sàn ca-rô quán diner · huy hiệu khảm ở sảnh · thảm tròn · sàn terrazzo siêu thị).
# Thước đếm NÉT, mà một mặt sàn có hoa văn thì nhiều nét y như một cái bàn.
#
# Nên KHÔNG đặt ngưỡng chặn: mọi ngưỡng đủ thấp để bắt hai ca thật sẽ loại hàng chục nền tốt
# (§13.8 — cổng bắt oan tệ hơn cổng không bắt). Thước này chỉ được dùng để **xếp hạng**, rồi
# người đọc soi vài ca đầu bảng. Với 1.081 nền thì đó là ~2 ca — rẻ, và chính xác.
#
# Ghi ra đây để phiên sau đừng đi đặt lại ngưỡng: chuyện ấy đã đo và đã bị bác (§13.22).
BO = os.path.join(GOC, "nen_bo.json")


def doc_bo() -> set:
    try:
        return set(json.load(open(BO)))
    except Exception:
        return set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--loc", type=int, default=0,
                    help="in N nền đáng ngờ nhất theo `giua` (danh sách để soi bằng mắt)")
    ap.add_argument("--ra", default=os.path.join(GOC, "kho_nen_do.json"))
    a = ap.parse_args()
    import nen_gt as NG

    tep = sorted(f for f in os.listdir(NEN) if f.endswith(".webp"))
    if a.kenh:
        ok = set(a.kenh.split(","))
        tep = [f for f in tep if f.rsplit("_", 1)[0] in ok]
    print(f"soi {len(tep)} nền\n")

    do = {}
    for i, f in enumerate(tep):
        p = os.path.join(NEN, f)
        do[f] = dict(sang=NG.do_sang(p), phang=NG.do_phang(p),
                     giua=do_giua(p), san=do_san(p), bam=bam(p))
        if (i + 1) % 200 == 0:
            print(f"   {i+1}/{len(tep)}", flush=True)

    def phan_bo(ten, lay=lambda v: v):
        xs = sorted(lay(v[ten]) for v in do.values() if v[ten] is not None)
        if not xs:
            return
        n = len(xs)
        q = [xs[int(n * p)] for p in (0, .05, .25, .5, .75, .95)] + [xs[-1]]
        print(f"  {ten:<6} min {q[0]:>7.3g} │ p5 {q[1]:>7.3g} │ p25 {q[2]:>7.3g} │ "
              f"trung vị {q[3]:>7.3g} │ p75 {q[4]:>7.3g} │ p95 {q[5]:>7.3g} │ max {q[6]:>7.3g}")

    print("PHÂN BỐ (chưa đặt ngưỡng — xem §12.3):")
    for t in ("sang", "phang", "giua", "san"):
        phan_bo(t)
    print("""
  ĐÃ QUYẾT ĐỊNH **KHÔNG** LÀM CỔNG TRÊN `phang` VÀ `san` (§13.22)
  Đọc tay 8 ca xấu nhất: chỉ 1 hỏng thật. Bảy ca kia là thước sai, không phải nền sai —
     · `san`=0  : sàn ca-rô quán diner · dòng dung nham. Sàn CÓ, chỉ là không đồng nhất; thước
                  đo độ đồng nhất chứ không đo "có mặt sàn không".
     · `phang` thấp: sảnh đá hoa có chuyển sắc. Vẫn là tranh vẽ, không phải ảnh chụp — đúng
                  cái bẫy §12.3 đã trả giá một lần.
     · `sang` thấp: hộp đêm đèn neon, phòng lò sưởi. Tối là ĐÚNG với nơi chốn ấy.
  Hai thước ấy vẫn IN RA để người đọc soi, nhưng không được phép chặn.""")

    # ── TRÙNG: chỉ so TRONG CÙNG một kênh ─────────────────────────────────────────────────
    # So chéo kênh là vô nghĩa: hai kênh khác nhau không bao giờ hiện cùng một tập.
    theo = collections.defaultdict(list)
    for f, v in do.items():
        if v["bam"]:
            theo[f.rsplit("_", 1)[0]].append((f, v["bam"]))
    cap = []
    for ma, ds in theo.items():
        for i in range(len(ds)):
            for j in range(i + 1, len(ds)):
                d = _cach(ds[i][1], ds[j][1])
                if d <= 26:      # ~9% của 288 bit
                    cap.append((d, ds[i][0], ds[j][0]))
    cap.sort()
    print(f"\n  cặp nền GIỐNG NHAU trong cùng kênh (khoảng cách ≤6/64): {len(cap)}")
    for d, x, y in cap[:8]:
        print(f"      {d}  {x}  ≈  {y}")

    print("\nCA CỰC TRỊ ĐỂ NHÌN TẬN MẮT (§12.3 — cổng sống ở khoảng giữa):")
    for t, chieu in (("sang", 1), ("phang", 1), ("giua", -1), ("san", 1)):
        xs = sorted((v[t], f) for f, v in do.items() if v[t] is not None)
        xau = xs[:5] if chieu > 0 else xs[-5:]
        print(f"  {t:<6} xấu nhất: " + " · ".join(f"{f.replace('.webp','')}={v:g}" for v, f in xau))

    if a.loc:
        bo = doc_bo()
        xs = sorted(((v["giua"], f) for f, v in do.items() if v["giua"] is not None),
                    reverse=True)
        xs = [(g, f) for g, f in xs if f.replace(".webp", "") not in bo][:a.loc]
        print(f"\n{a.loc} NỀN ĐÁNG NGỜ NHẤT (đồ ở chỗ đặt chân) — soi rồi ghi vào nen_bo.json:")
        for g, f in xs:
            print(f"   {g:>6.3f}  {f}")
        print(f"\n   (đã loại sẵn: {len(bo)} nền)")

    json.dump(do, open(a.ra, "w"), indent=1)
    print(f"\nsố đo -> {a.ra}")


if __name__ == "__main__":
    main()
