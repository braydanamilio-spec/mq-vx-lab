#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ĐO HƯỚNG SÁNG CỦA NỀN — để bóng đổ cùng chiều với ảnh (31/8/2026)

Anh: *"nhân vật chưa hoà vào nền 3D — người vẽ phẳng trên nền có chiều sâu vẫn hơi như dán
lên. Chữa rẻ: bóng đổ đậm hơn và đổ theo đúng hướng sáng của ảnh nền."*

Mắt người đọc "vật này có thật ở trong ảnh không" chủ yếu qua BÓNG: bóng tiếp đất (chỗ chân
chạm sàn) nói vật đứng trên mặt phẳng, bóng đổ dài nói ánh sáng đến từ đâu. Bóng đối xứng đổ
thẳng xuống là bóng của phòng chụp studio — đặt lên một ảnh có nắng chiếu xiên thì mắt bắt
được ngay dù không gọi tên được.

Ảnh nền đã có sẵn hướng sáng của nó. Việc ở đây chỉ là ĐỌC ra rồi bảo engine đổ bóng theo.

Cách đo: cắt nửa trên ảnh (vùng tường/trần, nơi ánh sáng lộ rõ nhất — nửa dưới là sàn nên
phản xạ lẫn lộn), so độ sáng trung bình một phần ba trái với một phần ba phải. Bên nào sáng
hơn là bên có nguồn sáng; bóng đổ về phía ngược lại.

Ra `engine-remotion/public/comic_nen/huong_sang.json`:
    { "airporthell_00": {"huong": -1, "manh": 0.42}, ... }
  huong: -1 sáng từ TRÁI (bóng đổ sang phải) · +1 sáng từ PHẢI · 0 sáng đều (bóng đổ thẳng)
  manh : 0..1 — chênh lệch càng lớn thì bóng càng dài và càng đậm
"""
import io
import json
import os

from PIL import Image

GOC = os.path.dirname(os.path.abspath(__file__))
NEN = os.path.join(GOC, "..", "engine-remotion", "public", "comic_nen")
RA = os.path.join(NEN, "huong_sang.json")

# Dưới ngưỡng này coi như sáng đều: chênh vài phần trăm là nhiễu của chi tiết trong ảnh, không
# phải nguồn sáng. Đổ bóng xiên theo một chênh lệch nhiễu thì còn sai hơn đổ thẳng.
NGUONG = 0.045


def do_mot(d: str):
    im = Image.open(d).convert("L")
    w, h = im.size
    im = im.resize((90, max(1, int(90 * h / w))), Image.BILINEAR)
    w, h = im.size
    nua = im.crop((0, 0, w, int(h * 0.55)))          # nửa trên: tường + trần
    px = nua.load()
    W, H = nua.size
    ba = W // 3

    def tb(x0, x1):
        s = n = 0
        for y in range(H):
            for x in range(x0, x1):
                s += px[x, y]
                n += 1
        return s / max(1, n) / 255.0

    trai, phai = tb(0, ba), tb(W - ba, W)
    chenh = phai - trai                      # >0 : phải sáng hơn -> nguồn sáng bên PHẢI
    if abs(chenh) < NGUONG:
        return {"huong": 0, "manh": round(abs(chenh) / NGUONG * 0.3, 3)}
    huong = 1 if chenh > 0 else -1
    manh = min(1.0, abs(chenh) / 0.22)       # chênh 0.22 trở lên là nắng gắt
    return {"huong": huong, "manh": round(manh, 3)}


def main() -> int:
    if not os.path.isdir(NEN):
        print("❌ chưa có thư mục nền")
        return 1
    ra = {}
    for t in sorted(os.listdir(NEN)):
        if not t.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        try:
            ra[os.path.splitext(t)[0]] = do_mot(os.path.join(NEN, t))
        except Exception as e:
            print(f"  ⚠️ {t}: {e}")

    io.open(RA, "w", encoding="utf-8").write(json.dumps(ra, ensure_ascii=False, indent=1))
    dem = {-1: 0, 0: 0, 1: 0}
    for v in ra.values():
        dem[v["huong"]] += 1
    tb_manh = sum(v["manh"] for v in ra.values()) / max(1, len(ra))
    print(f"  ✅ đo {len(ra)} nền -> comic_nen/huong_sang.json")
    print(f"     sáng từ trái {dem[-1]} · đều {dem[0]} · sáng từ phải {dem[1]} · độ gắt tb {tb_manh:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
