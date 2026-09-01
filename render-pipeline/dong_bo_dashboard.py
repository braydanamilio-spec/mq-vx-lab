#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐỒNG BỘ DASHBOARD — sinh ba bảng kênh của `index.html` TỪ nguồn sự thật.  (1/9/2026)

── VÌ SAO CÓ TỆP NÀY ───────────────────────────────────────────────────────────────────────
Hôm nay đo ra danh sách kênh nằm ở BỐN nơi, và chúng đã lệch nhau hai chiều:

    giai_thich.KENH            18 kênh mới        <- nguồn thật
    config/channels.yaml       18 kênh mới
    dashboard RS_PRESETS       50 kênh cũ         <- lệch
    Firestore render_channels  50 kênh cũ         <- lệch

Hậu quả đúng như chú thích viết sẵn ngay trên `RS_PRESETS`: *"Thiếu khối này thì kênh mới KHÔNG
hiện trong dropdown Render Studio"*. Tức phần khó (engine, brand kit, giọng, nhạc) xong cả rồi
mà kẹt ở phần dễ, và kẹt trong im lặng — dashboard không báo thiếu, nó chỉ hiện danh sách cũ.

Chép tay 18 dòng vào `index.html` sẽ dựng lại đúng cái bẫy này ở lần thêm kênh sau. Nên: SINH.

── BẪY ĐÃ GHI Ở `docs/CHANNEL_METHODS.md` ──────────────────────────────────────────────────
Lần gỡ 55 kênh thế hệ 1 làm **toàn bộ dashboard đơ**: ngoài ba nơi khai báo còn 60 câu gán trần
`RS_BRANDS.KHOA.cat = …` rải giữa thân script; gỡ khoá đi thì câu đầu ném lỗi và MỌI dòng sau
ngừng chạy — kể cả dòng gắn `onclick` cho thanh điều hướng. Nên tệp này QUÉT lại các câu gán ấy
trước khi ghi, và dừng nếu còn.

Nghiệm thu (luật 3 của tài liệu ấy): mở trang thật, đọc console, đi qua từng tab.
"""
import io
import os
import re
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(os.path.dirname(GOC), "MM0-AutoPublisher", "dashboard", "index.html")


def _js(x: str) -> str:
    """Chuỗi JS an toàn — dấu nháy và gạch chéo phải thoát, nếu không cả tệp hỏng cú pháp."""
    return '"' + str(x).replace("\\", "\\\\").replace('"', '\\"') + '"'


def sinh_khoi():
    """Trả (js_voices, js_presets, js_brands) sinh từ nguồn thật."""
    sys.path.insert(0, GOC)
    import giai_thich as G
    import brand_gt as B

    ma = [k["ma"] for k in G.KENH]
    ten = {k["ma"]: k for k in G.KENH}

    # ── RS_VOICES: giọng + tốc độ. Nguồn: GU_RIENG (cùng bảng engine dùng để dựng tiếng), nên
    #    dashboard nghe thử ra ĐÚNG giọng video sẽ có. Trước đây hai bên khai riêng.
    v = ",".join(f'{_js(m.upper())}:[{_js(G.GU_RIENG[m][0])},"+0%"]' for m in ma)
    js_v = f"    const RS_VOICES={{{v}}};"

    # ── RS_PRESETS: KHÔNG khai `fmt`. Đọc `rsQuickAddAll`: có `fmt` thì kênh thành short-only
    #    (trừ "doc"); không có `fmt` thì nhận mix "1long_3short" + make_long — đúng bộ 18 kênh
    #    này, vốn làm CẢ long lẫn short. Một trường thừa ở đây là mất hẳn bản dài.
    p = [f'      {{name:{_js(m.upper())},the_he:3,accent:{_js(ten[m]["mau"])},'
         f'accent2:{_js(ten[m]["phu"])},niche:{_js(B.MO_TA[m][0])}}},' for m in ma]
    js_p = ("    const RS_PRESETS=[\n"
            "      // ── 18 KÊNH GIẢI THÍCH (1/9) — SINH RA bởi `render-pipeline/dong_bo_dashboard.py`.\n"
            "      // ĐỪNG SỬA TAY: nguồn là `giai_thich.KENH` + `brand_gt.MO_TA`. Sửa nguồn rồi chạy lại.\n"
            "      // Không khai `fmt` là cố ý — có `fmt` thì kênh thành short-only, mất hẳn bản dài.\n"
            + "\n".join(p) + "\n    ];")

    # ── RS_BRANDS: bộ nhận diện hiện trên dashboard.
    b = [f'      {m.upper()}:{{d:{_js(B.NHAN[m][1])},a:{_js(ten[m]["mau"])},'
         f't:{_js(B.MO_TA[m][0])},h:{_js("@" + m + "usa")},ic:{_js(_ic(B.NHAN[m][0]))},'
         f'ht:{_js(B.MO_TA[m][1])},niche:{_js(ten[m]["ten"])}}},' for m in ma]
    js_b = ("    const RS_BRANDS={\n"
            "      // ── 18 KÊNH GIẢI THÍCH (1/9) — SINH RA, đừng sửa tay. Xem chú thích RS_PRESETS.\n"
            + "\n".join(b) + "\n    };")
    return js_v, js_p, js_b


# Biểu tượng trong `NHAN` là tên hình VẼ BẰNG CODE (`dong_ho`, `tien`…), không phải emoji.
# Dashboard cần emoji. Ánh xạ ở đây, và có mặc định — thêm hình mới mà quên ánh xạ thì ra 📊
# chứ không nổ.
_EMOJI = {"dong_ho": "⏱", "trai_dat": "🌍", "tien": "💵", "hat": "🔢", "cau_hoi": "❓",
          "lua": "🔥", "lich": "📅", "mui_ten": "➡", "giay": "📄", "toc_do": "⚡",
          "xuc_xac": "🎲", "nhan": "🏷", "cat": "⏳", "loa": "🔊", "can": "⚖",
          "dong_ho_kim": "🕐", "nhiet": "🌡", "kinh_lup": "🔬"}


def _ic(ten_hinh: str) -> str:
    return _EMOJI.get(ten_hinh, "📊")


def quet_gan_tran(s: str) -> list:
    """Câu gán trần vào bảng dùng chung — thứ đã làm đơ cả dashboard hôm 26/8."""
    return re.findall(r"(?:RS_BRANDS|RS_PRESETS|RS_VOICES)\.[A-Z0-9_]+\.[a-z_]+\s*=", s)


def thay(s: str, dau: str, cuoi_re: str, moi: str, ten: str) -> str:
    i = s.find(dau)
    if i < 0:
        raise SystemExit(f"❌ không tìm thấy đầu khối {ten} — DỪNG, không vá mù")
    m = re.compile(cuoi_re, re.M).search(s, i)
    if not m:
        raise SystemExit(f"❌ không tìm thấy cuối khối {ten} — DỪNG")
    print(f"  {ten:12s} thay {s[i:m.end()].count(chr(10)) + 1:3d} dòng -> {moi.count(chr(10)) + 1:3d} dòng")
    return s[:i] + moi + s[m.end():]


def main() -> int:
    s = io.open(HTML, encoding="utf-8").read()
    tran = quet_gan_tran(s)
    if tran:
        print(f"❌ còn {len(tran)} câu gán trần vào bảng kênh — sửa thành vòng lặp CÓ KIỂM trước.")
        print("   (bẫy 26/8: câu đầu ném lỗi -> mọi dòng sau ngừng chạy -> tab không bấm được)")
        return 1
    print("  ✅ không còn câu gán trần vào bảng kênh")

    jv, jp, jb = sinh_khoi()
    s = thay(s, "    const RS_VOICES=", r"^.*$",                 jv, "RS_VOICES")
    s = thay(s, "    const RS_PRESETS=[", r"^\s*\];\s*$",        jp, "RS_PRESETS")
    s = thay(s, "    const RS_BRANDS={", r"^\s*\};\s*$",         jb, "RS_BRANDS")

    io.open(HTML, "w", encoding="utf-8").write(s)
    print(f"  ✅ ghi {HTML}")
    print("  → còn phải: deploy hosting, rồi mở trình duyệt đọc console + đi qua TỪNG tab.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
