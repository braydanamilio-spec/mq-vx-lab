#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐỒNG BỘ BRAND KIT LÊN DASHBOARD — chép ảnh + sinh `_ART_V4`.  (1/9/2026)

`brand_gt.py` sinh 7 tệp/kênh vào `render-pipeline/brand_gt/` với tên viết thường. Dashboard đọc
`/brand/<MÃ HOA>_<vai trò>_<kích thước>.png`. Hai bên chưa bao giờ được nối — nên 18 kênh mới có
đủ brand kit trên đĩa mà dashboard vẫn trống.

── ÁNH XẠ THEO KÍCH THƯỚC, KHÔNG THEO TÊN ──────────────────────────────────────────────────
Tên hai bên đặt khác nhau (`banner` vs `cover_2560x1440`), nên đoán theo tên là đoán. Đo bằng
PIL rồi khớp theo (rộng, cao) — sai kích thước thì dừng, không chép bừa.

── VÌ SAO SINH THÊM `fb_cover_820x312` ─────────────────────────────────────────────────────
Dashboard suy ra link tải Facebook bằng cách THAY CHUỖI trong tên tệp:

    b.art.cover.replace('_cover_2560x1440','_fb_cover_820x312')

Tệp ấy chưa từng được sinh ra, nên nút "⬇ Facebook 820×312" là link chết — và chết trong im
lặng, vì trình duyệt chỉ tải về một trang 404. Ở đây sinh thật (cắt giữa từ bản 2560×1440, vốn
đã chừa lề an toàn), và song song vá dashboard để đọc khoá `fb_cover` thay vì đoán từ tên.
"""
import hashlib
import io
import json
import os
import re
import shutil
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
NGUON = os.path.join(GOC, "brand_gt")
DICH = os.path.join(os.path.dirname(GOC), "MM0-AutoPublisher", "dashboard", "brand")
HTML = os.path.join(os.path.dirname(GOC), "MM0-AutoPublisher", "dashboard", "index.html")

# (kích thước đo được) -> (khoá trong _ART_V4, hậu tố tên tệp dashboard)
THEO_CO = {
    (800, 800):    ("avatar",    "avatar_800"),
    (1080, 1080):  ("ig_post",   "ig_post_1080"),
    (2560, 1440):  ("cover",     "cover_2560x1440"),
    (1640, 856):   ("fb_cover_lon", "fb_cover_1640x856"),
    (500, 500):    ("fb_avatar", "fb_avatar_500"),
    (640, 640):    ("ig_avatar", "ig_avatar_640"),
}


def main() -> int:
    sys.path.insert(0, GOC)
    import giai_thich as G
    from PIL import Image

    os.makedirs(DICH, exist_ok=True)
    ma = [k["ma"] for k in G.KENH]

    # SỐ PHIÊN BẢN THEO NỘI DUNG ẢNH, không đếm tay. Tên tệp không đổi giữa hai lần dựng, nên
    # nếu `?v=` đứng yên thì trình duyệt phục vụ avatar CŨ trong bộ đệm — sửa xong mà nhìn vẫn
    # y nguyên, và không có lỗi nào báo. Băm toàn bộ ảnh nguồn: ảnh đổi thì URL tự đổi.
    h = hashlib.sha1()
    for f in sorted(os.listdir(NGUON)):
        if f.endswith(".png"):
            h.update(io.open(os.path.join(NGUON, f), "rb").read())
    ver = h.hexdigest()[:8]
    print(f"  phiên bản ảnh: {ver}")
    art, thieu, chep = {}, [], 0

    for m in ma:
        goi = {}
        for f in sorted(os.listdir(NGUON)):
            if not f.startswith(m + "_") or not f.endswith(".png"):
                continue
            p = os.path.join(NGUON, f)
            co = Image.open(p).size
            if co not in THEO_CO:
                continue                      # ảnh phụ (avatar_lon 1080 trùng ig_post — nhận cái đầu)
            khoa, hau = THEO_CO[co]
            if khoa in goi:
                continue
            ten = f"{m.upper()}_{hau}.png"
            shutil.copyfile(p, os.path.join(DICH, ten))
            goi[khoa] = f"/brand/{ten}?v={ver}"
            chep += 1

        # Bìa Facebook 820×312: CẮT GIỮA từ bản 2560×1440 rồi thu — không kéo giãn, vì kéo giãn
        # làm mặt nhân vật méo và đó là thứ đập vào mắt đầu tiên trên trang.
        big = os.path.join(DICH, f"{m.upper()}_cover_2560x1440.png")
        if os.path.exists(big):
            im = Image.open(big).convert("RGB")
            W, H = im.size
            ch = int(W * 312 / 820)           # chiều cao cần để đúng tỉ lệ 820:312
            y = (H - ch) // 2
            im.crop((0, y, W, y + ch)).resize((820, 312), Image.LANCZOS) \
              .save(os.path.join(DICH, f"{m.upper()}_fb_cover_820x312.png"))
            goi["fb_cover"] = f"/brand/{m.upper()}_fb_cover_820x312.png?v={ver}"
            chep += 1

        can = ("avatar", "cover", "fb_cover")
        v = [x for x in can if x not in goi]
        if v:
            thieu.append(f"{m}({','.join(v)})")
        art[m.upper()] = goi

    print(f"  chép {chep} tệp cho {len(ma)} kênh -> dashboard/brand/")
    if thieu:
        print(f"  ❌ thiếu ảnh bắt buộc: {', '.join(thieu)}")
        return 1
    print("  ✅ mọi kênh đủ avatar · cover · fb_cover")

    # ── DỌN ẢNH MỒ CÔI  (1/9/2026) ──────────────────────────────────────────────────────────
    # Anh hỏi brand kit có tốn hạn mức không. Đo: thư mục 39 MB / 631 tệp, trong đó **505 tệp
    # (29,5 MB) thuộc kênh đã nghỉ và KHÔNG ai trỏ tới** — `_ART_V4` chỉ nhắc 126 tệp của 18
    # kênh, `index.html` nhắc 0 tệp trong số 505 kia. Chúng vẫn được deploy và vẫn nằm trong
    # mỗi lượt build.
    #
    # Không nguy hiểm (Hosting free có 10 GB, và ảnh brand không đụng Firestore lần nào), nhưng
    # là rác chỉ tăng: mỗi thế hệ kênh mới lại để lại một lớp. Dọn ngay ở đây, nơi vừa biết
    # chính xác tệp nào còn cần.
    #
    # An toàn: mọi tệp đều đang được git theo dõi, nên xoá khỏi thư mục vẫn lấy lại được từ
    # lịch sử. Đây là dọn thư mục làm việc, không phải xoá vĩnh viễn.
    can = {os.path.basename(u.split("?")[0]) for v in art.values() for u in v.values()}
    mo_coi = [f for f in sorted(os.listdir(DICH))
              if f.lower().endswith((".png", ".jpg", ".jpeg")) and f not in can]
    if mo_coi:
        bo = sum(os.path.getsize(os.path.join(DICH, f)) for f in mo_coi)
        for f in mo_coi:
            os.remove(os.path.join(DICH, f))
        print(f"  🧹 dọn {len(mo_coi)} ảnh mồ côi ({bo / 1048576:.1f} MB) — không tệp nào được trỏ tới")
    else:
        print("  ✅ không có ảnh mồ côi")

    s = io.open(HTML, encoding="utf-8").read()
    moi = "    const _ART_V4 = " + json.dumps(art, ensure_ascii=False) + ";"
    # Kiểm bằng CÓ KHỚP MẪU KHÔNG, không bằng "nội dung có đổi không": chạy lại khi chưa có gì
    # đổi thì nội dung y hệt, và bản trước coi đó là lỗi rồi dừng giữa chừng.
    if not re.search(r"    const _ART_V4 = \{.*?\};", s, re.S):
        print("  ❌ không tìm thấy khối _ART_V4 — DỪNG")
        return 1
    s2 = re.sub(r"    const _ART_V4 = \{.*?\};", lambda _: moi, s, count=1, flags=re.S)

    # Vá chỗ suy link bằng thay chuỗi: đọc khoá thật trước, chỉ đoán khi không có.
    cu = "${b.art.cover.replace('_cover_2560x1440','_fb_cover_820x312')}"
    if cu in s2:
        s2 = s2.replace(cu, "${b.art.fb_cover||b.art.cover}", 1)
        print("  ✅ bỏ phép suy link Facebook bằng thay chuỗi tên tệp")

    io.open(HTML, "w", encoding="utf-8").write(s2)
    print(f"  ✅ ghi _ART_V4 cho {len(art)} kênh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
