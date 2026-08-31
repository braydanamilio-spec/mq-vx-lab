#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CỔNG WORKFLOW — gói đúng thứ vừa dựng, và chạy cổng trước khi dựng (31/8/2026)

Hai lỗi tìm ra khi đưa bộ comic vào sản xuất, cả hai đều **im lặng tuyệt đối**:

  · `render_hai.yml` gói `out/v4_*.mp4`, trong khi pipeline comic xuất ra `v5_*`. Một lượt
    chạy sẽ dựng đủ 10 video rồi gói về TAY KHÔNG — vì "không có tệp nào khớp" không phải lỗi
    trong `upload-artifact`.
  · `cham_v4.py` cũng tìm `v4_` nên trả "chưa dựng" cho cả mười kênh: cổng chất lượng vô hiệu.

Cả hai là mảnh sót của engine cũ. Chúng sống sót vì YAML và glob không kêu khi không khớp gì.
Cổng này đối chiếu tiền tố tệp mà pipeline THẬT SỰ ghi ra với tiền tố mà workflow gói lại.
"""
import io
import os
import re

GOC = os.path.dirname(os.path.abspath(__file__))
WF = os.path.join(GOC, "..", ".github", "workflows")

# workflow -> (pipeline ngắn, pipeline dài, có siêu dữ liệu đăng không)
#
# 31/8 — Anh: *"nhớ pepline methord chuẩn long short, thumbnail, fileupload chuẩn."* Đây là
# BỘ GIAO HÀNG của một tập, và trước hôm nay nó thủng ba chỗ cùng lúc: bản dài có tệp trong
# repo mà KHÔNG workflow nào gọi tới, và bản ngắn thì gói nhầm tiền tố nên gói về tay không.
# Ghi thành cổng thay vì thành lời dặn — lời dặn không chặn được lượt chạy nào.
CAP = {
    "render_hai.yml": ("kich_comic.py", "kich_comic_long.py", True),
    "render_phan_tich.yml": ("kich_v2.py", "kich_v2_long.py", False),
}


def tien_to_pipeline(tep: str):
    """Những tiền tố `vN_` mà pipeline này ghi ra tệp mp4."""
    s = io.open(os.path.join(GOC, tep), encoding="utf-8").read()
    return set(re.findall(r'f"(v\d+)_\{[a-z_]+\}\.mp4"', s)) or set(re.findall(r'"(v\d+)_', s))


def main() -> int:
    loi = []
    for wf, (py, py_dai, co_meta) in CAP.items():
        d = os.path.join(WF, wf)
        if not os.path.exists(d) or not os.path.exists(os.path.join(GOC, py)):
            continue
        y = io.open(d, encoding="utf-8").read()
        # BỎ CHÚ THÍCH TRƯỚC KHI DÒ. Bản đầu của cổng này dò chuỗi trên toàn tệp, nên một dòng
        # chú thích nhắc tên `kich_comic_long.py` là đủ để nó tin rằng workflow có gọi bản dài —
        # trong khi lời gọi thật đã bị gỡ. Cổng phải đọc thứ CHẠY được, không đọc thứ NÓI về nó.
        ma = "\n".join(l for l in y.split("\n") if not l.lstrip().startswith("#"))
        goi = set(re.findall(r"render-pipeline/out/(v\d+)_\*", ma))
        that = tien_to_pipeline(py)
        if not goi:
            loi.append(f"{wf}: không gói tệp video nào")
            continue
        thua = goi - that
        if thua:
            loi.append(f"{wf}: gói {'/'.join(sorted(thua))}_* nhưng {py} ghi ra "
                       f"{'/'.join(sorted(that))}_* — lượt chạy sẽ gói về tay không")
        else:
            print(f"  ✅ {wf:24s} gói {'/'.join(sorted(goi))}_*  (khớp {py})")

        # ── BỘ GIAO HÀNG: ngắn · DÀI · ảnh bìa · chữ đăng ────────────────────────────────
        if os.path.exists(os.path.join(GOC, py_dai)):
            if f"python {py_dai}" not in ma:
                loi.append(f"{wf}: không dựng bản dài — `{py_dai}` có trong repo mà workflow "
                           f"không gọi tới (mất chỗ bật quảng cáo giữa video)")
            if not re.search(r"out/v\d+L_\*\.mp4", ma):
                loi.append(f"{wf}: không gói bản dài (`vNL_*.mp4`)")
        if not re.search(r"out/v\d+L?_\*\.jpg", ma):
            loi.append(f"{wf}: không gói ẢNH BÌA — có video mà không có thumbnail để đăng")
        if co_meta and ".tai.json" not in ma:
            loi.append(f"{wf}: không gói `.tai.json` — có video mà không có tiêu đề/mô tả/thẻ")

        # Cổng phải chạy TRƯỚC bước dựng: chạy sau thì tốn cả lượt render mới biết hỏng.
        i_cong = ma.find("kiem_san.py")
        i_dung = min([x for x in (ma.find("python kich_"), ma.find("python duyet_lo")) if x > 0]
                     or [10 ** 9])
        if 0 < i_dung < i_cong:
            loi.append(f"{wf}: cổng chạy SAU bước dựng — hỏng thì đã tốn cả lượt")

    if loi:
        print("\n❌ " + "\n❌ ".join(loi))
        return 1
    print("\n✅ workflow gói đúng sản phẩm, cổng chạy trước khi dựng")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
