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


# ══ RULE PHONG CÁCH NỀN CHO TỪNG KÊNH ══════════════════════════════════════════════════
# Anh: *"thế thì e có thể vẫn đúng bối cảnh nhưng xây pepline rule chuẩn phong cách cho
# channel"*. Đúng chỗ còn thiếu: mười kênh đang dùng CHUNG một gu ("clay render, pastel"), nên
# nơi chốn khác nhau mà nền vẫn cùng một chất — xếp mười khung cạnh nhau lại ra một xưởng.
#
# Ba trục dưới đây là thứ mắt đọc được trên một tấm nền, xếp theo thứ tự nhận ra:
#   · BẢNG MÀU — bám theo `MAU_CHINH`/`MAU_PHU` của kênh, để nền và nhân vật cùng một họ màu;
#   · ÁNH SÁNG — gắt hay dịu, ấm hay lạnh, từ trên hay từ cửa sổ;
#   · CHẤT LIỆU — clay mềm, nhựa bóng, giấy mờ, kim loại nhám.
# Ba trục ấy đổi thì cùng một căn phòng cho ra hai thế giới khác hẳn.
PHONG_CACH = {
    "rent":     "warm brick red and deep navy palette, hard directional light from one side, "
                "matte painted walls, slightly worn urban feel",
    "gym":      "emerald green and bright orange palette, crisp even gym lighting, glossy "
                "rubber and chrome surfaces, energetic and clean",
    "airport":  "cool grey blue and muted teal palette, flat institutional ceiling light, "
                "polished floors with soft reflections, wide and impersonal",
    "car":      "amber orange and steel blue palette, industrial overhead lamps casting warm "
                "pools of light, brushed metal and concrete textures",
    "office":   "lavender purple and mint palette, flat fluorescent lighting with no shadows, "
                "smooth matte plastic surfaces, tidy and slightly sterile",
    "diet":     "soft teal and warm pink palette, bright kitchen daylight from a window, "
                "clean ceramic and light wood, cosy domestic feel",
    "tech":     "electric blue and orange palette, cool screen glow mixed with white ceiling "
                "light, matte plastic and cable clutter, modern workplace",
    "parent":   "warm coral and sky blue palette, soft afternoon light through curtains, "
                "plush fabrics and rounded wooden furniture, lived-in and homely",
    "neighbor": "fresh grass green and burnt sienna palette, natural outdoor daylight, "
                "painted timber and stucco textures, quiet suburban street",
    "dating":   "rose pink and violet palette, warm low-hanging pendant light, velvet and "
                "polished wood, intimate and softly lit",    # Nhà của một gia đình Mỹ ngoại ô: gỗ ấm, nắng qua rèm, đồ dùng bày bừa vừa phải. Cố ý
    # KHÁC mười kênh kia — chúng đều là nơi công cộng (phòng gym, sân bay, văn phòng), còn đây
    # là trong nhà, nên tông ấm hơn và tương phản dịu hơn.
    "houserules": "warm suburban American family home, oak and cream palette, soft afternoon "
                  "daylight through curtains, lived-in but tidy, gentle contrast",

}


# BIẾN THỂ THEO TẬP — 1/9. Anh: *"tạo cho đa dạng, ko dùng lại, mà tạo cho đúng bối cảnh
# channel, videos"* và *"key api free dư sức mà"*. Đúng: dùng lại một ảnh cho mọi tập là tự
# tay làm kênh nhàm, trong khi 97 khoá CF cho ~16.300 ảnh/ngày — sinh 10-18 ảnh mỗi lượt là
# không đáng kể.
# Mỗi tập đổi BA trục: giờ trong ngày · độ cao máy · thời tiết/ánh sáng. Ba trục này đổi hẳn
# cảm giác khung hình mà KHÔNG đụng vào bố cục ép sàn — thứ đã mất nhiều vòng mới đúng.
# 1/9, sau mẻ thử: BỎ hai biến thể "evening interior lighting" và "cool blue-hour light" —
# chúng đẩy mô hình sang tông NEON, ra ảnh photoreal rực đèn, lệch hẳn phong cách 3D cartoon
# phẳng của nhân vật. Đa dạng phải nằm trong khuôn phong cách, không phải phá khuôn.
BIEN_THE = [
    "early morning light, long soft shadows",
    "bright midday light, crisp shadows",
    "late afternoon golden light, warm tones",
    "overcast daylight, soft even shadows",
    "hazy sunlight, gentle bloom",
    "clear cool daylight, slightly desaturated",
    "soft diffused light, no harsh shadows",
    "warm indoor daylight, gentle contrast",
]
GOC_MAY = [
    "camera slightly left of centre",
    "camera straight on, centred",
    "camera slightly right of centre",
    "camera a step further back, wider view",
]


def _prompt(noi: str, kenh_ten: str, ngoai: bool = False, de: str = "", tap: int = -1) -> str:
    """Prompt ép ba thứ: có sàn · giữa trống · không người không chữ.

    `tap >= 0` thì thêm biến thể ánh sáng + góc máy của tập ấy — cùng một nơi chốn ra khung
    khác hẳn, mà vẫn đúng nơi chốn kịch bản nói.
    """
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
        # 1/9 — CẤM CHỮ Ở CẢ ĐẦU LẪN CUỐI, và cấm luôn thứ SINH RA chữ. Mẻ thử ra ảnh phòng máy
        # chủ có "TECL", "TechShort" viết trên biển và màn hình — chữ rác là dấu hiệu AI rõ nhất
        # và trông nghiệp dư ngay. Cấm "text" thôi không đủ: phải cấm cả BIỂN HIỆU, MÀN HÌNH CÓ
        # CHỮ, ÁP PHÍCH — tức cấm chỗ chữ hay bám vào.
        "NO TEXT, NO LETTERS, NO WORDS, NO SIGNAGE, NO SCREENS SHOWING TEXT, NO LABELS. "
        f"Stylized 3D cartoon render of {noi}, in the world of a comedy show about "
        f"{kenh_ten.lower()}. Absolutely no text anywhere: no letters, no words, no writing, "
        f"no labels, no signs, no logos, no posters with writing, no branded screens, "
        f"blank screens only. "
        + khong_gian +
        # (A) ép bố cục chừa chỗ cho nhân vật
        "Camera at standing eye level, straight on. Furniture and props pushed to the far left "
        "and far right edges, leaving the center of the frame completely empty. "
        # phong cách: gần với nhân vật vector phẳng hơn là photoreal
        # Rule phong cách của kênh — thay cho câu gu dùng chung. Giữ "stylized 3D cartoon"
        # làm nền tảng để nền vẫn hợp với nhân vật vẽ phẳng, còn màu/sáng/chất thì mỗi kênh một.
        + (PHONG_CACH.get(de, "soft matte clay-render look, muted pastel colors") + ". ")
        + "Simple rounded shapes, clean and uncluttered, no clutter in the centre. "
        + (f"{BIEN_THE[tap % len(BIEN_THE)]}, {GOC_MAY[(tap // 3) % len(GOC_MAY)]}. "
           if tap >= 0 else "")
        # (loại thứ hay làm hỏng khung)
        + "No people, no characters, no watermark, no text of any kind."
    )


def sinh_mot(kenh: str, idx: int, noi: str, ten: str, keys, ngoai: bool = False,
             de: str = "", tap: int = -1) -> str:
    os.makedirs(THU, exist_ok=True)
    # Tên tệp mang số TẬP: mỗi tập một ảnh riêng, không đè lên ảnh nền chuẩn của nơi chốn.
    # Ảnh chuẩn (`{kenh}_{idx}.jpg`) vẫn nằm trong repo làm lớp đỡ khi API hỏng.
    ma = f"{kenh}_{idx:02d}" + (f"_t{tap:03d}" if tap >= 0 else "")
    dest = os.path.join(THU, f"{ma}.jpg")
    rel = f"comic_nen/{ma}.jpg"
    if os.path.exists(dest) and os.path.getsize(dest) > 20000:
        return rel

    # Mọi lệnh gọi ảnh CF đi qua MỘT đường: `xoay_key.goi_xoay`. Trước đây mỗi chỗ tự viết
    # vòng lặp khoá riêng, nên mỗi chỗ lặp lại y nguyên lỗi "một khoá 429 = cả pool cạn".
    import datastory_ci as DS
    from xoay_key import goi_xoay, bao_cao, CanThat

    def _thu(kk):
        return DS._cf_flux_image(_prompt(noi, ten, ngoai, de, tap), dest, kk) and \
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
    # Kênh HOUSE RULES không nằm trong `KENH` (bảng ấy do `kich_comic` dùng, mà nó tra `VAI`
    # theo từng kênh — thêm vào đó là làm `kich_comic` nổ KeyError). Nhưng nó vẫn cần nền, nên
    # nối vào ĐÂY thay vì viết một bộ sinh nền thứ hai: hai bộ sinh nền rồi sẽ lệch luật ép sàn.
    try:
        from kich_kling import KENH_KLING
        chon = KENH + [KENH_KLING]
    except Exception:
        chon = KENH
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        # LỌC TỪ `chon`, KHÔNG TỪ `KENH`. Vừa nối kênh mới vào `chon` ở trên rồi lọc lại từ
        # `KENH` thì kênh mới rơi ra ngay — và rơi im lặng: lệnh chạy xong, báo "✅ 100 ảnh
        # nền" (số cũ), không ảnh nào được sinh. Lại đúng họ lỗi vá một chỗ quên chỗ song song.
        chon = [x for x in chon if x["ten"].replace(" ", "").upper() in vt]

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
            r = sinh_mot(slug, i, noi, k["ten"], cf, noi in NGOAI, k["de"])
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
