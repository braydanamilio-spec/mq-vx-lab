#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NỀN 3D SINH BẰNG CLOUDFLARE FLUX (31/8/2026)
════════════════════════════════════════════════════════════════════════════════════════════

Anh: *"thấy vẽ 2.5D vẫn chưa ổn đẹp lắm, giữ lại những nâng cấp tốt và kiểu bong bóng hội
thoại, e thử thay lại bối cảnh 3D cf generate đúng ngữ cảnh kịch bản, và nhớ đừng có lỗi lơ
lửng."*

── PHẢI NÓI TRƯỚC: ĐÂY LÀ CÁCH BẢN CŨ ĐÃ HỎNG ────────────────────────────────────────────
`KichHai` từng dùng ảnh AI làm nền và hỏng theo đúng hai đường:
  1. ảnh 3D photoreal đứng cạnh người vector phẳng → mắt đọc ra hai lớp dán chồng;
  2. ảnh sinh ra thường KHÔNG CÓ SÀN trong khung (máy chụp ngang tầm bàn), nên nhân vật đặt
     vào đâu cũng lơ lửng — đúng cái anh vừa chỉ ở tấm 02.

Nên bản này không chỉ đổi nguồn nền. Nó thêm ba lớp chặn, và lớp thứ ba là lớp quyết định:

  A. PROMPT ép có sàn: máy đặt ngang tầm mắt người đứng, sàn chiếm trọn phần ba dưới, đồ đạc
     dồn về hai mép, chính giữa để trống cho nhân vật.
  B. ẢNH BỊ HẠ XUỐNG LÀM PHÔNG: làm mờ nhẹ và giảm bão hoà, để nó lùi ra sau và không tranh
     nét với nhân vật. Nền sắc nét ngang nhân vật là nền cãi nhau với nhân vật.
  C. LỚP SÀN VẼ ĐÈ — KHÔNG PHỤ THUỘC ẢNH: một dải sàn mờ cộng bóng đổ, vẽ bằng code ở đúng
     mức `SAN`. Dù mô hình trả về ảnh không có sàn thì nhân vật VẪN đứng trên một mặt phẳng
     có thật. Đây là chỗ bản cũ thiếu, và là lý do nó lơ lửng.

Ảnh cache theo (kênh, nơi chốn) nên mỗi nơi chỉ sinh MỘT lần: 100 nơi = 100 ảnh, dùng lại cho
hàng nghìn tập. Hạn mức CF free ≈ 174 ảnh/ngày, nên cả bộ chạy trong một ngày.
"""
import os
import io
import json
import time
import argparse

from kich_hai import KENH, _ten_tep, GOC, ENG

THU = os.path.join(ENG, "public", "comic_nen")


def _prompt(noi: str, kenh_ten: str, ngoai: bool = False) -> str:
    """Prompt ép ba thứ: có sàn · giữa trống · không người không chữ."""
    # 31/8 — hai lỗi thấy trên mẻ đầu:
    #   · nơi NGOÀI TRỜI (sân trước, hàng rào) bị dựng thành phòng kín có hàng rào bên trong —
    #     vì prompt không nói rõ, và "interior" là mặc định của mô hình;
    #   · ảnh TECH SUPPORT có chữ "IT help" vẽ lên tường, dù đã cấm text. Một lần cấm ở cuối
    #     câu không đủ; phải cấm bằng nhiều từ và đặt gần đầu.
    khong_gian = (
        "Outdoor scene in daylight, open sky above, ground and grass visible across the bottom "
        "third of the frame. "
        if ngoai else
        "Interior scene. The floor is clearly visible across the entire bottom third. "
    )
    return (
        f"Stylized 3D cartoon render of {noi}, in the world of a comedy show about "
        f"{kenh_ten.lower()}. Absolutely no text anywhere: no letters, no words, no writing, "
        f"no labels, no signs, no logos, no posters with writing. "
        + khong_gian +
        # (A) ép bố cục chừa chỗ cho nhân vật
        "Camera at standing eye level, straight on. Furniture and props pushed to the far left "
        "and far right edges, leaving the center of the frame completely empty. "
        # phong cách: gần với nhân vật vector phẳng hơn là photoreal
        "Soft matte clay-render look, simple rounded shapes, flat even lighting, no harsh "
        "shadows, muted pastel colors, clean and uncluttered. "
        # (loại thứ hay làm hỏng khung)
        "No people, no characters, no watermark, no text of any kind."
    )


def sinh_mot(kenh: str, idx: int, noi: str, ten: str, keys, ngoai: bool = False) -> str:
    os.makedirs(THU, exist_ok=True)
    dest = os.path.join(THU, f"{kenh}_{idx:02d}.jpg")
    rel = f"comic_nen/{kenh}_{idx:02d}.jpg"
    if os.path.exists(dest) and os.path.getsize(dest) > 20000:
        return rel

    # Mọi lệnh gọi ảnh CF đi qua MỘT đường: `xoay_key.goi_xoay`. Trước đây mỗi chỗ tự viết
    # vòng lặp khoá riêng, nên mỗi chỗ lặp lại y nguyên lỗi "một khoá 429 = cả pool cạn".
    import datastory_ci as DS
    from xoay_key import goi_xoay, bao_cao, CanThat

    def _thu(kk):
        return DS._cf_flux_image(_prompt(noi, ten, ngoai), dest, kk) and \
            os.path.getsize(dest) > 20000

    try:
        ok, tk = goi_xoay(keys, _thu, hat=idx + sum(ord(c) for c in kenh))
    except CanThat as e:
        print(f"     ⛔ {e}")
        return ""
    if ok:
        return rel
    print(f"     ❌ không sinh được: {bao_cao(tk)}")
    return ""
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--so", type=int, default=4, help="số nơi chốn đầu mỗi kênh cần sinh nền")
    a = ap.parse_args()

    import the_he_2 as T2
    keys = T2.keys_cuc_bo() or []
    cf = [k for k in keys if (k if isinstance(k, str) else k.get("key", "")).startswith("cf:")]
    if not cf:
        print("❌ không có khoá Cloudflare nào — nền 3D cần CF FLUX")
        return 2
    print(f"→ {len(cf)} khoá CF")

    ds = json.load(io.open(os.path.join(GOC, "noi_chon.json"), encoding="utf-8"))
    # Nơi nào là ngoài trời — đọc thẳng từ NoiChon.tsx để không giữ bản thứ hai của sự thật.
    # 31/8: ba regex đầu đều trả 0 nơi, vì cờ `ngoai` nằm SAU khối `mo: [...]` và mọi mẫu
    # `[^}]*` đều dừng ở dấu `}` đầu tiên bên trong khối ấy. Cách chắc chắn: tách theo MỐC
    # `{ ten: "` rồi tìm cờ trong đoạn giữa hai mốc — không phụ thuộc vào dấu ngoặc lồng nhau.
    import re as _re
    _tsx = io.open(os.path.join(GOC, "..", "engine-remotion", "src", "comic", "NoiChon.tsx"),
                   encoding="utf-8").read()
    _b = _tsx[_tsx.index("export const NOI"):_tsx.index("// ══ SINH NƠI CHỐN")]
    _mocs = [m.start() for m in _re.finditer(r'\{ ten: "', _b)] + [len(_b)]
    NGOAI = set()
    for _i in range(len(_mocs) - 1):
        _kh = _b[_mocs[_i]:_mocs[_i + 1]]
        if "ngoai: true" in _kh:
            NGOAI.add(_re.search(r'\{ ten: "([^"]+)"', _kh).group(1))
    print(f"→ {len(NGOAI)}/100 nơi ngoài trời")
    if not NGOAI:
        print("   ⚠️ KHÔNG nơi nào — cách đọc cờ đang hỏng, mọi ảnh sẽ ra nội thất")
    chon = KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [x for x in KENH if x["ten"].replace(" ", "").upper() in vt]

    # 31/8 — GỘP, KHÔNG GHI ĐÈ.
    # Lần chạy thứ hai (chỉ 3 kênh) đã ghi đè bản đồ và xoá mất 7 kênh sinh ở lần đầu — 40 ảnh
    # vẫn nằm trên đĩa mà engine không biết đường nào dẫn tới chúng. Đây là họ lỗi "công cụ chỉ
    # biết phần việc của lần chạy này": mỗi lần chạy đều đúng, mà kết quả cộng lại thì sai.
    ra = {}
    if os.path.exists(os.path.join(GOC, "nen_cf.json")):
        try:
            ra = json.load(io.open(os.path.join(GOC, "nen_cf.json"), encoding="utf-8"))
        except Exception:
            ra = {}
    for k in chon:
        slug = _ten_tep(k)
        noi_ds = ds.get(k["de"], [])[:a.so]
        print(f"\n▶ {k['ten']}", flush=True)
        for i, noi in enumerate(noi_ds):
            r = sinh_mot(slug, i, noi, k["ten"], cf, noi in NGOAI)
            print(f"   {'✅' if r else '❌'} {i:02d} {noi[:46]}", flush=True)
            if r:
                ra.setdefault(slug, {})[str(i)] = r
            # ghi sau mỗi ảnh — sinh 100 ảnh mất hơn tiếng, đứt giữa chừng không mất phần đã có
            io.open(os.path.join(GOC, "nen_cf.json"), "w", encoding="utf-8").write(
                json.dumps(ra, ensure_ascii=False, indent=1))
    n = sum(len(v) for v in ra.values())
    print(f"\n{'✅' if n else '⚠️'} {n} ảnh nền → engine-remotion/public/comic_nen/")
    return 0 if n else 1


if __name__ == "__main__":
    raise SystemExit(main())
