#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CỔNG ÂM THANH — mỗi tệp nhạc phải có hệ số riêng, và bóng phải vẽ cho MỌI cảnh (31/8/2026)

Hai lỗi ở mục 22 của PIPELINE_RULES đều vô hình với mọi cổng đang có, vì không cái nào làm
render thất bại. Cổng này bắt đúng hai thứ ấy ở tầng mã nguồn:

  1. Mọi tệp trong bảng `NHAC` phải có số đo trong `music/am_luong.json`. Thiếu thì tệp ấy rơi
     về hằng 0.16 — tức là quay lại đúng lỗi cũ, lặng lẽ.
  2. `BongNguoi` phải được gọi NGOÀI nhánh `doiNguoi`. Bóng thuộc về người, không thuộc về số
     lượng người trong khung.
"""
import io
import json
import os
import re

GOC = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(GOC, "..", "engine-remotion", "public")
ENG = os.path.join(GOC, "..", "engine-remotion", "src", "comic", "KichComic.tsx")


def main() -> int:
    loi = []

    # ── 1. nhạc ──────────────────────────────────────────────────────────────────────────
    try:
        bang = json.load(io.open(os.path.join(PUB, "music", "am_luong.json"), encoding="utf-8"))
    except Exception:
        bang = {}
    s = io.open(os.path.join(GOC, "kich_comic.py"), encoding="utf-8").read()
    m = re.search(r"^NHAC\s*=\s*\{(.*?)\}", s, re.S | re.M)
    tep = re.findall(r'"(music/[^"]+)"', m.group(1)) if m else []
    # TỆP PHẢI CÓ THẬT, VÀ PHẢI CÓ TRÊN GIT. 1/9 — kênh SELF CHECKOUT chết với "404 Not Found"
    # vì tôi khai `km_undaunted_tram.mp3`, một tệp KHÔNG TỒN TẠI (chỉ có 5 bản `_tram`, không
    # có bản ấy). Đây đúng bài học đã ghi trong `.gitignore`: thêm một `music=` mới thì phải
    # kiểm tệp có thật chưa — và "có trên máy" chưa đủ, phải "có trên git" thì CI mới thấy.
    import subprocess
    khong_co = [t for t in tep if not os.path.exists(os.path.join(PUB, t))]
    if khong_co:
        loi.append("nhạc KHÔNG TỒN TẠI: " + " · ".join(khong_co) + "  -> render 404")
    else:
        gtr = subprocess.run(["git", "ls-files"] + [os.path.join("engine-remotion/public", t) for t in tep],
                             capture_output=True, text=True, cwd=os.path.join(GOC, "..")).stdout.split()
        chua_git = [t for t in tep if f"engine-remotion/public/{t}" not in gtr]
        if chua_git:
            loi.append("nhạc chưa lên git (CI sẽ 404): " + " · ".join(chua_git))
        else:
            print(f"  ✅ {len(tep)} bản nhạc đều có thật trên đĩa và trên git")

    thieu = [t for t in tep if os.path.basename(t) not in bang]
    if thieu:
        loi.append("thiếu số đo âm lượng: " + " · ".join(thieu) + "  (chạy `python3 can_nhac.py`)")
    else:
        hs = [bang[os.path.basename(t)] for t in tep]
        print(f"  ✅ {len(tep)} tệp nhạc đều có hệ số riêng "
              f"({min(hs):.3f} .. {max(hs):.3f} — hằng cũ dùng chung 0.16 cho tất cả)")

    # ── 2. bóng ──────────────────────────────────────────────────────────────────────────
    e = io.open(ENG, encoding="utf-8").read()
    goi = re.findall(r"^\s*(\{doiNguoi \? )?<BongNguoi", e, re.M)
    if not goi:
        loi.append("engine không gọi `BongNguoi` — nhân vật sẽ không có bóng")
    elif all(g for g in goi):
        loi.append("mọi lời gọi `BongNguoi` đều nằm trong nhánh `doiNguoi` — "
                   "cảnh một người sẽ không có bóng (mục 22.1)")
    else:
        print(f"  ✅ bóng vẽ cho cả cảnh một người ({len(goi)} lời gọi, "
              f"{sum(1 for g in goi if not g)} nằm ngoài nhánh `doiNguoi`)")

    # ── 3. mốc phát của nền tảng ─────────────────────────────────────────────────────────
    # YouTube/FB/IG chuẩn hoá về −14 LUFS và chỉ HẠ chứ không nâng. Cả BA đường dựng phải gọi
    # `chuan()` — đây chính là chỗ dễ tái phạm họ lỗi "vá một nhánh, để nguyên nhánh song song",
    # vì ba tệp này không dùng chung hàm dựng nào.
    # TỰ TÌM, KHÔNG DÒ DANH SÁCH VIẾT CỨNG. 1/9 — bản trước liệt kê đúng ba tệp, nên khi
    # `kich_v2_long.py` (đường thứ tư, chưa ai chạy bao giờ) không gọi `chuan()` thì cổng vẫn
    # báo xanh. Một cổng chống lỗi "vá một nhánh, để nguyên nhánh song song" mà bản thân nó
    # cũng viết cứng danh sách nhánh thì nó chính là nhánh bị bỏ quên tiếp theo.
    # Luật thật là: TỆP NÀO DỰNG RA MP4 thì tệp ấy phải chuẩn âm. Dò theo lời gọi render.
    WF = os.path.join(GOC, "..", ".github", "workflows")
    goi = ""
    if os.path.isdir(WF):
        for w in os.listdir(WF):
            if w.endswith((".yml", ".yaml")):
                goi += io.open(os.path.join(WF, w), encoding="utf-8").read()

    duong, ngu = [], []
    for t in sorted(os.listdir(GOC)):
        if not t.endswith(".py"):
            continue
        n = io.open(os.path.join(GOC, t), encoding="utf-8").read()
        if '"remotion", "render"' not in n and "'remotion', 'render'" not in n:
            continue
        # CHỈ BẮT ĐƯỜNG ĐANG CHẠY. Có bốn tệp dựng mp4 nhưng không workflow nào gọi tới:
        # `kich_hai.py` (engine hài cũ, giữ để đối chiếu) và `receipt_pilot.py` (pilot). Bắt
        # chúng là cổng tố oan, mà cổng tố oan thì người ta tắt cổng.
        # Đạt nếu tự gọi `chuan()`, HOẶC uỷ thác qua `run_render_cmd` — hàm ấy đã chuẩn âm
        # ngay tại chỗ nghẽn chung. Bản trước chỉ dò chữ "chuan(" nên tố oan `the_he_2.py`,
        # tệp đi qua đúng đường đã vá. Cổng tố oan thì người ta tắt cổng — nguy hiểm ngang cổng
        # bỏ sót.
        ok = ("chuan(" in n) or ("run_render_cmd(" in n and t != "datastory_ci.py")
        (duong if t in goi else ngu).append((t, ok))
    thieu_chuan = [t for t, ok in duong if not ok]
    if ngu:
        print(f"  ℹ️ {len(ngu)} đường dựng KHÔNG workflow nào gọi (bỏ qua): "
              f"{' · '.join(t for t, _ in ngu)}")
    if thieu_chuan:
        loi.append("chưa chuẩn âm đầu ra: " + " · ".join(thieu_chuan) + "  (gọi `chuan(out)`)")
    else:
        print(f"  ✅ cả {len(duong)} đường dựng ra mp4 đều đưa âm lượng về −14 LUFS "
              f"({' · '.join(t for t, _ in duong)})")

    if loi:
        print("\n❌ " + "\n❌ ".join(loi))
        return 1
    print("\n✅ âm lượng và bóng đều đúng luật")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
