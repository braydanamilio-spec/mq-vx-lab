#!/usr/bin/env python3
"""QC VISUAL đo trên ẢNH ĐÃ RENDER — không đọc props, không tin điểm nội dung.

31/8 — Mọi cổng cho tới nay đều đọc DỮ LIỆU trước khi vẽ: kịch bản, props, toạ độ. Chúng bắt
được lỗi logic nhưng mù trước lỗi hình, và hôm 30/8 đã chứng minh điều đó theo cách đắt nhất:
mười video được chấm 95–100, trích một khung ra nhìn thì thấy nguyên si lỗi anh đã chê ba lần.

Cổng này đo trên chính khung hình cuối cùng — thứ người xem thấy. Bốn phép đo, đều là con số,
đều rút ra từ lời anh chê chứ không từ lý thuyết:

  1. VÙNG TRỐNG   — "khoảng trống lớn phía trên", "bố cục dồn xuống dưới".
     Chia khung thành lưới, đếm ô gần như đồng màu. Trống quá nửa khung là một khung chưa dựng
     xong, dù mọi con số trong nó đều đúng.
  2. LỆCH TRÁI/PHẢI — "chart bị lệch phải quá nhiều che khuất".
     So khối lượng chi tiết hai nửa khung. Lệch quá thì mắt không có chỗ nghỉ ở nửa kia.
  3. TƯƠNG PHẢN   — chữ đọc được ở cỡ điện thoại hay không.
     Đo độ lệch sáng trong dải phụ đề; dải phụ đề mà phẳng lì thì chữ đang chìm vào nền.

Ngưỡng đặt ở mức mắt bắt đầu khó chịu, không phải mức lý tưởng — cổng bắt oan còn tệ hơn cổng
bỏ sót, vì nó dạy người ta bỏ qua cảnh báo.
"""
import io, os, sys, glob, math

TRONG_TOI_DA = 0.62      # tỉ lệ ô đồng màu tối đa
LECH_TOI_DA = 0.34       # chênh lệch khối lượng hai nửa
MEP = 4                  # bề dày dải mép (px) để dò chạm
DAM = 46                 # mức lệch so với nền để coi là "có chi tiết"


def _xam(im):
    return im.convert("L")


def do_khung(f: str) -> dict:
    from PIL import Image, ImageStat
    im = Image.open(f).convert("RGB")
    W, H = im.size
    g = _xam(im)
    px = g.load()

    # 1 — vùng trống: lưới 8×14, ô nào độ lệch chuẩn thấp thì coi là trống
    CX, CY = 8, 14
    trong = 0
    for j in range(CY):
        for i in range(CX):
            o = g.crop((i * W // CX, j * H // CY, (i + 1) * W // CX, (j + 1) * H // CY))
            if ImageStat.Stat(o).stddev[0] < 9:
                trong += 1
    ty_trong = trong / (CX * CY)

    # 2 — lệch trái/phải: khối lượng chi tiết = tổng độ lệch chuẩn theo cột
    def khoi(x0, x1):
        return sum(ImageStat.Stat(g.crop((x0, j * H // CY, x1, (j + 1) * H // CY))).stddev[0]
                   for j in range(CY))
    t, p = khoi(0, W // 2), khoi(W // 2, W)
    lech = abs(t - p) / max(1.0, t + p)

    # 3 — tương phản dải phụ đề (20% dưới)
    sub = g.crop((0, int(H * .80), W, H))
    tp = ImageStat.Stat(sub).stddev[0]

    return {"tep": os.path.basename(f), "trong": ty_trong, "lech": lech, "tuong_phan": tp}


def cham_khung(d: dict) -> list:
    loi = []
    if d["trong"] > TRONG_TOI_DA:
        loi.append(f"khung trống {d['trong']:.0%} — bố cục rỗng, mắt không có gì để nhìn")
    if d["lech"] > LECH_TOI_DA:
        ben = "trái" if d["lech"] > 0 else "phải"
        loi.append(f"dồn lệch {d['lech']:.0%} về một bên — nửa kia bỏ không")
    if d["tuong_phan"] < 26:
        loi.append(f"dải phụ đề phẳng (lệch sáng {d['tuong_phan']:.0f}) — chữ chìm vào nền")
    return loi


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="QC visual đo trên ảnh khung đã render.")
    ap.add_argument("--thu-muc", default="out/_khung")
    ap.add_argument("--mau", default="*.png")
    a = ap.parse_args()
    fs = sorted(glob.glob(os.path.join(a.thu_muc, a.mau)))
    if not fs:
        print(f"  ⚠️ không có ảnh nào trong {a.thu_muc}"); return 0
    xau = 0
    print(f"\n  QC VISUAL trên {len(fs)} khung đã render\n")
    for f in fs:
        try:
            d = do_khung(f)
        except Exception as e:
            print(f"  ⚠️ {os.path.basename(f)}: {type(e).__name__}"); continue
        loi = cham_khung(d)
        if loi:
            xau += 1
            print(f"  ❌ {d['tep']}")
            for l in loi:
                print(f"       └ {l}")
    print(f"\n  ✅ lành {len(fs)-xau}  ·  ❌ có vấn đề {xau}   (trên {len(fs)} khung)")
    return 1 if xau else 0


if __name__ == "__main__":
    sys.exit(main())
