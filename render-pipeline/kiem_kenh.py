#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG KÊNH — mọi bảng phụ thuộc phải phủ đủ danh sách kênh, và không trùng ngoài ý muốn.

── VÌ SAO CẦN CỔNG NÀY (1/9/2026) ──────────────────────────────────────────────────────────
`KENH` trong `giai_thich.py` là nguồn sự thật về danh sách kênh. Nhưng có BẢY bảng khác phải
đi kèm nó, nằm ở BA tệp:

    giai_thich.MAU_KENH · GU_RIENG · HOOK_LOI · BO_SINH
    nen_gt.KENH_GU · KHOA_VAI
    brand_gt.NHAN · MO_TA

Thêm một kênh mà quên một bảng thì KHÔNG có lỗi nào báo — kênh ấy lặng lẽ rơi về mặc định:
màu chung, giọng chung, biểu tượng chung. Trông vẫn chạy, chỉ là kênh ấy mất bản sắc.

Hôm nay đã dính đúng thế: thêm 8 kênh, bốn bảng thiếu, và bản vá `GU_RIENG` còn không khớp vì
lệch MỘT ký tự khoảng trắng. Phát hiện được chỉ vì tình cờ viết một đoạn kiểm tay. Đoạn kiểm
tay ấy nay thành cổng.

── CỔNG CÒN ĐẾM TRÙNG ──────────────────────────────────────────────────────────────────────
Mười tám kênh mà chung một màu, một biểu tượng hay một khoá nhân vật thì người xem thấy chúng
là một xưởng — đúng điều anh dặn tránh. Nên trùng ở các trục NHẬN DIỆN là lỗi.

Riêng GIỌNG ĐỌC được phép trùng, và đây là lựa chọn có chủ đích: edge-tts chỉ có 17 giọng en-US
(đã hỏi API), nhưng lý do chính là gán theo ĐỘ HỢP niche đắt hơn gán để không trùng — giọng
nhẹ vui cho kênh sinh tồn tệ hơn hai kênh cùng giọng.
"""
import sys

# Trục nhận diện: trùng là lỗi.
NHAN_DIEN = ("màu", "nhạc", "sắc thái vẽ", "biểu tượng", "từ avatar", "khoá nhân vật")


def kiem() -> tuple:
    """Trả (số lỗi, [dòng báo])."""
    bao, loi = [], 0
    try:
        import giai_thich as G
        import nen_gt as N
        import brand_gt as B
    except Exception as e:
        return 1, [f"không nạp được module: {str(e)[:120]}"]

    ma = [k["ma"] for k in G.KENH]
    bao.append(f"  {len(ma)} kênh trong KENH")

    bang = {
        "giai_thich.MAU_KENH": G.MAU_KENH,
        "giai_thich.GU_RIENG": G.GU_RIENG,
        "giai_thich.HOOK_LOI": G.HOOK_LOI,
        "giai_thich.BO_SINH":  G.BO_SINH,
        "nen_gt.KENH_GU":      N.KENH_GU,
        "nen_gt.KHOA_VAI":     N.KHOA_VAI,
        "brand_gt.NHAN":       B.NHAN,
        "brand_gt.MO_TA":      B.MO_TA,
        "brand_gt.BO_CUC":     B.BO_CUC,
    }
    for ten, b in bang.items():
        thieu = [m for m in ma if m not in b]
        thua = [m for m in b if m not in ma]
        if thieu:
            loi += 1
            bao.append(f"  ❌ {ten:22s} THIẾU {len(thieu)}: {', '.join(thieu[:6])}")
        elif thua:
            # Thừa không phải lỗi chặn — kênh cũ để lại không gây hại — nhưng vẫn báo, vì nó
            # thường là dấu hiệu ai đó đổi tên mã kênh mà quên một chỗ.
            bao.append(f"  ⚠ {ten:22s} thừa {len(thua)}: {', '.join(thua[:4])}")
        else:
            bao.append(f"  ✅ {ten:22s} đủ {len(ma)}")

    import collections
    truc = [
        ("màu",            lambda m: G.MAU_KENH[m]["mau"]),
        ("nhạc",           lambda m: G.GU_RIENG[m][1]),
        ("sắc thái vẽ",    lambda m: G.GU_RIENG[m][2]),
        ("biểu tượng",     lambda m: B.NHAN[m][0]),
        ("từ avatar",      lambda m: B.NHAN[m][1]),
        ("khẩu hiệu",      lambda m: B.MO_TA[m][0]),
        ("bộ thẻ",         lambda m: B.MO_TA[m][1]),
        ("khoá nhân vật",  lambda m: N.KHOA_VAI[m]),
    ]
    for ten, lay in truc:
        try:
            c = collections.Counter(lay(m) for m in ma)
        except Exception:
            continue
        tr = {k: v for k, v in c.items() if v > 1}
        if tr:
            loi += 1
            bao.append(f"  ❌ {ten:14s} TRÙNG {len(tr)} giá trị — 18 kênh sẽ đọc ra là một xưởng")
        else:
            bao.append(f"  ✅ {ten:14s} {len(c)}/{len(ma)} khác nhau")

    # Bố cục: 6 khuôn cho 18 kênh nên PHẢI trùng, nhưng phải dùng ĐỦ CẢ SÁU. Trước 1/9 cả 18
    # kênh cùng khuôn "cheo" vì `brand_gt` không truyền `kk` — engine im lặng rơi về mặc định,
    # và hậu quả là 18 avatar nhìn ra một xưởng. Cổng đếm số khuôn thật sự được dùng.
    try:
        bc = collections.Counter(B.BO_CUC[m] for m in ma)
        if len(bc) < 6:
            loi += 1
            bao.append(f"  ❌ bố cục chỉ dùng {len(bc)}/6 khuôn — brand kit sẽ đọc ra một mô-típ")
        else:
            bao.append(f"  ✅ bố cục       dùng đủ 6/6 khuôn ({dict(bc)})")
    except Exception:
        pass

    # Giọng: trùng được, chỉ báo cho biết.
    try:
        gi = collections.Counter(G.GU_RIENG[m][0] for m in ma)
        bao.append(f"  ℹ giọng đọc     {len(gi)}/{len(ma)} khác nhau (trùng có chủ đích: "
                   f"gán theo độ hợp niche)")
    except Exception:
        pass

    # Mọi bộ sinh phải CHẠY ĐƯỢC — bảng có tên mà hàm ném lỗi thì cũng như thiếu.
    hong = []
    for m in ma:
        try:
            t, h, hp, n = G.BO_SINH[m](0)
            if not n or not t:
                hong.append(m)
        except Exception as e:
            hong.append(f"{m}({str(e)[:30]})")
    if hong:
        loi += 1
        bao.append(f"  ❌ bộ sinh hỏng: {', '.join(hong[:6])}")
    else:
        bao.append(f"  ✅ {len(ma)} bộ sinh đều chạy")

    # Nhạc của mọi kênh phải TỒN TẠI trên đĩa — khai một tệp không có là video câm, và câm thì
    # không có lỗi nào báo. Đúng bài học `km_undaunted_tram.mp3` của bộ hài.
    import os
    pub = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "engine-remotion", "public")
    mat = [m for m in ma if not os.path.exists(os.path.join(pub, G.GU_RIENG[m][1]))]
    if mat:
        loi += 1
        bao.append(f"  ❌ nhạc không tồn tại: {', '.join(mat[:5])}")
    else:
        bao.append(f"  ✅ nhạc của {len(ma)} kênh đều có trên đĩa")

    # Bản DÀI không được dùng nhạc ngắn — lặp hơn mười vòng là dấu hiệu rẻ tiền rõ nhất.
    ngan = [m for m in ma if G._nhac(m, True) in getattr(G, "NHAC_NGAN", set())]
    if ngan:
        loi += 1
        bao.append(f"  ❌ bản dài dùng nhạc ngắn: {', '.join(ngan)}")
    else:
        bao.append("  ✅ không kênh nào dùng nhạc ngắn cho bản dài")

    return loi, bao


def main() -> int:
    loi, bao = kiem()
    for d in bao:
        print(d)
    if loi:
        print(f"\n❌ {loi} lỗi. Thêm kênh thì phải thêm vào ĐỦ TÁM BẢNG — thiếu một bảng là kênh")
        print("   ấy lặng lẽ mất bản sắc, và không có lỗi nào báo.")
        return 1
    print("\n✅ mọi bảng phủ đủ danh sách kênh · không trùng ở trục nhận diện")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
