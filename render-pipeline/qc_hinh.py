#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QC HÌNH — cổng kiểm TRƯỚC và SAU render.  (7/9/2026)

Anh: *"tự đánh giá chất lượng chuẩn top 1 usa rồi có tiêu chuẩn qc visual trước sau render"*.

── VÌ SAO HAI TẦNG, VÀ VÌ SAO TẦNG TRƯỚC QUAN TRỌNG HƠN ──────────────────────────────────
Kiểm SAU render bắt được lỗi khi đã tiêu xong tiền: 18 luồng × 4 clip × ~28 phút runner. Kiểm
TRƯỚC render đọc danh sách nhịp và bảng props, chạy mất mili giây, và bắt được phần lớn lỗi
hình vì chúng đã nằm sẵn trong dữ liệu (§12.11 — `kiem_nhip` đo trên danh sách nhịp, TRƯỚC
khi render, vì nhịp là việc của khâu VIẾT).

Kiểm SAU vẫn cần cho đúng những thứ chỉ thấy được trên pixel: chữ tràn mép · nền trắng lòi ra
· khung tối thui · nhân vật lọt khỏi khung.

── ĐIỂM SỐ KHÔNG PHẢI "ĐẸP"  (§16.1) ────────────────────────────────────────────────────
Mọi con số ở đây chỉ nói *"không dính N lỗi đã biết"*. Nó KHÔNG nói đẹp, và không thay được
việc trích khung ra nhìn (§5). Ghi ra ngay đầu tệp vì chính em đã đọc câu này hàng chục lần
rồi vẫn báo cáo "100/100" như thể nó là chất lượng.
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))


# ══ TẦNG 1 — TRƯỚC RENDER: đọc props, chạy mili giây ═══════════════════════════════════════
def truoc(props: dict) -> list:
    """Trả danh sách lỗi. Rỗng = qua cổng."""
    loi = []
    nh = props.get("luot") or props.get("nhip") or []
    if not nh:
        return ["không có nhịp nào"]

    # 1. MỌI NHỊP PHẢI CÓ NỀN. Nhịp thiếu nền rơi về nền vector và đọc ra là một khung khác
    #    hẳn — người xem thấy tập "nhảy chất" giữa chừng (§7, bốn tầng).
    an = props.get("anhNens") or []
    thieu = sum(1 for i in range(len(nh)) if i >= len(an) or not an[i])
    if thieu:
        loi.append(f"{thieu}/{len(nh)} nhịp KHÔNG có nền")

    # 2. NỀN KHÔNG ĐƯỢC LẶP LIỀN KỀ. Hai nhịp liền nhau cùng một tấm thì màn hình đứng yên
    #    suốt hai nhịp — đúng chỗ người xem lướt đi (§15.6).
    lap = sum(1 for i in range(1, len(an)) if an[i] and an[i] == an[i - 1])
    if lap:
        loi.append(f"{lap} cặp nhịp liền nhau DÙNG CHUNG một nền")

    # 2b. LỜI KHÔNG ĐƯỢC LẶP NGUYÊN VĂN. Soi lưới bộ 130: khung 2 và khung 7 giống nhau TỪNG
    #     CHỮ, khung 3 và khung 8 cũng vậy — bản dài 186 giây nói đi nói lại 14 câu.
    #     Gốc: `kich_ban(long=True, chuong=3)` kéo dài thời lượng bằng cách ĐỌC LẠI, không
    #     bằng cách thêm nội dung (đo: chương 1 -> 13/13 câu khác nhau · chương 3 -> 14/32).
    #     Cổng này canh SẢN PHẨM chứ không canh tham số, nên nó vẫn bắt được nếu mai có
    #     đường nào khác bơm thời lượng bằng cùng một mẹo (§15.3).
    _noi = [" ".join(str((x or {}).get("nar") or (x or {}).get("chu") or "").lower().split())
            for x in nh]
    _noi = [t for t in _noi if len(t) > 24]
    if _noi:
        # ── LẶP GẦN NHAU thì MỘT CẶP đã hỏng  (soi lưới bộ 138, 8/9/2026) ──────────────
        # Khung 1 và khung 2 của bộ 138 đọc y hệt nhau. Ngưỡng 10% cho qua vì 1 cặp trong 13
        # nhịp là 7,7%. Nhưng ngưỡng phần trăm đo TỔNG ĐỘ LẶP của cả tập, còn thứ người xem
        # cảm được là KHOẢNG CÁCH giữa hai lần đọc (§15.15 đã đo đúng điều này ở bộ giải
        # thích: 40% lặp là sàn số học, thứ dùng được là "cách nhau bao nhiêu giây").
        # Hai câu cách nhau ≤3 nhịp mà giống nhau thì luôn là lỗi — kể cả một cặp duy nhất.
        # Xa hơn thì để ngưỡng phần trăm lo, vì một chương trình được phép có điệp khúc
        # (§13.18) và chặn nó là bắt oan.
        _gan = [(i, j) for i in range(len(_noi)) for j in range(i + 1, min(i + 4, len(_noi)))
                if _noi[i] and _noi[i] == _noi[j]]
        if _gan:
            loi.append(f"{len(_gan)} cặp lượt LẶP NGUYÊN VĂN cách nhau ≤3 nhịp "
                       f"(nhịp {_gan[0][0]} và {_gan[0][1]})")
        _lap_van = len(_noi) - len(set(_noi))
        if _lap_van > max(1, len(_noi) * 0.10):
            loi.append(f"{_lap_van}/{len(_noi)} lượt LẶP NGUYÊN VĂN "
                       f"({len(set(_noi))} câu khác nhau) — tập đang kéo dài bằng cách đọc lại")

    # 3. LỜI THOẠI KHÔNG ĐƯỢC MANG DẤU NỘI BỘ hay tiền tố chỉ số. Đã rò ba dạng khác nhau
    #    trong một ngày (`0.` · `i7:` · `1 Kodak`), nên cổng phải quét ở đây chứ không tin
    #    vào phép dọn ở khâu trên (§19.17).
    for i, n in enumerate(nh):
        t = str(n.get("nar") or "")
        if re.match(r"^\s*\[[A-Z_]{2,12}\]", t):
            loi.append(f"nhịp {i}: lời thoại còn dấu nội bộ «{t[:18]}»")
        if re.match(r"^\s*[A-Za-z]?\d{1,2}\s*[.):]\s", t):
            loi.append(f"nhịp {i}: lời thoại còn tiền tố chỉ số «{t[:14]}»")

    # 4. CÂU QUÁ DÀI = BONG BÓNG CAO = ĐÈ NHÂN VẬT. Bong bóng cao theo SỐ DÒNG, và hình học
    #    không có chỗ nhường; câu thì có (§18.10).
    dai = [i for i, n in enumerate(nh) if len(str(n.get("nar") or "")) > 132]
    if dai:
        loi.append(f"{len(dai)} nhịp có lời > 132 ký tự (bong bóng sẽ đè nhân vật): {dai[:4]}")

    # 5. NHỊP CUỐI KHÔNG ĐƯỢC LÀ MỘT CON SỐ. Hết video mà chỉ còn một con số thì không có gì
    #    để kể lại cho người khác — và kể lại mới là thứ đẩy video đi xa (§19.2).
    cuoi = str(nh[-1].get("nar") or "")
    if re.fullmatch(r"[^a-zA-Z]*\d[\d.,%$ ]*[a-z]{0,12}\.?", cuoi.strip()):
        loi.append(f"nhịp CUỐI chỉ là một con số: «{cuoi[:30]}»")

    # 6. PHẢI NÓI VỚI NGƯỜI XEM. 6/18 tập từng không nhắc người xem một lần nào — một video
    #    giải thích không nói với ai là một bài giảng (§19.2).
    # ── MỆNH LỆNH CŨNG LÀ NÓI VỚI NGƯỜI XEM  (đo 8/9/2026) ──────────────────────────
    # Cổng đếm CHỮ `you`, nhưng thứ cần đo là một HÌNH: người xem có mặt trong tập không.
    # «Tell someone tomorrow that…» · «Remember, …» là mệnh lệnh nói THẲNG với người xem mà
    # không chứa đại từ nào. Đo trên toàn bộ tập đã dựng: **33 lượt** như vậy, và 33 câu đều
    # KHÁC NHAU (không phải một khuôn lặp). Đọc tay 12 câu hay gặp nhất: cả 12 đều đúng là
    # nói với người xem.
    #
    # Đây là §13.20 ở phía đo: đo một TỪ khi thứ cần đo là một hình. Không phải nới cổng cho
    # xanh — nới là khi phép đo sai, và phép đo này sai thật: nó tính 26/30 bản dài đạt,
    # trong khi tính cả mệnh lệnh thì 28/30. Hai tập còn lại vẫn trượt, nên cổng vẫn có răng.
    _MENH = re.compile(r"^\s*(Tell|Imagine|Picture|Ask|Remember|Look|Think|Consider|Notice|"
                       r"Try|Count|Watch)\b", re.I)
    _co_ban = re.compile(r"\byou(r|'?re|'?ll|'?ve)?\b", re.I)
    ban = sum(1 for n in nh
              if _co_ban.search(str(n.get("nar") or ""))
              or _MENH.match(str(n.get("nar") or "")))
    if ban < 2:
        loi.append(f"chỉ {ban} nhịp nói với người xem (cần ≥2)")
    return loi


# ══ TẦNG 2 — SAU RENDER: đo trên PIXEL ════════════════════════════════════════════════════
def _khung(mp4: str, giay: float, ra: str) -> bool:
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(giay),
                        "-i", mp4, "-frames:v", "1", ra], capture_output=True)
    return r.returncode == 0 and os.path.exists(ra)


def sau(mp4: str, so_mau: int = 6) -> list:
    """Đo trên khung hình thật. Trả danh sách lỗi."""
    try:
        from PIL import Image
    except Exception:
        return ["thiếu Pillow — KHÔNG kết luận được (đây là dòng dự phòng, §15.12)"]
    if not os.path.exists(mp4):
        return [f"không có tệp {os.path.basename(mp4)}"]
    r = subprocess.run(["ffprobe", "-v", "0", "-show_entries", "format=duration",
                        "-of", "csv=p=0", mp4], capture_output=True, text=True)
    try:
        dai = float(r.stdout.strip())
    except Exception:
        return ["không đọc được thời lượng"]
    # `environ.get(K, "mđ")` hai tham số: biến RỖNG phá mặc định (§15.19 đã trả giá, và cổng
    # `selftest` bắt được ngay khi em viết lại nó lần này).
    tmp = os.environ.get("TMPDIR") or "/tmp"
    loi = []
    for k in range(so_mau):
        t = dai * (k + 0.5) / so_mau
        d = os.path.join(tmp, f"_qc{k}.png")
        if not _khung(mp4, t, d):
            continue
        im = Image.open(d).convert("RGB")
        W, H = im.size
        px = im.load()
        # a. KHUNG TỐI THUI hoặc TRẮNG XOÁ — nền hỏng, hoặc ảnh không nạp được.
        mau = [px[x, y] for y in range(0, H, max(1, H // 40))
               for x in range(0, W, max(1, W // 24))]
        tb = sum(sum(c) / 3 for c in mau) / max(1, len(mau))
        if tb < 26:
            loi.append(f"khung {t:.0f}s: TỐI THUI (độ sáng TB {tb:.0f})")
        elif tb > 246:
            loi.append(f"khung {t:.0f}s: TRẮNG XOÁ (độ sáng TB {tb:.0f})")
        # b. MÉP HỞ — Ken Burns trôi quá tay thì lòi nền trang ra sát mép.
        for ten, dai_mep in (("trái", [(0, y) for y in range(0, H, 12)]),
                             ("phải", [(W - 1, y) for y in range(0, H, 12)])):
            sang = sum(1 for x, y in dai_mep if min(px[x, y]) > 248)
            if sang > len(dai_mep) * 0.75:
                loi.append(f"khung {t:.0f}s: mép {ten} TRẮNG (nghi Ken Burns hở mép)")
    return loi


def _in(ten: str, loi: list) -> int:
    print(f"\n── {ten}")
    if not loi:
        print("   ✅ không dính lỗi nào đã biết")
        print("      (điểm này KHÔNG nói 'đẹp' — vẫn phải trích khung ra nhìn, §5)")
        return 0
    for x in loi:
        print(f"   ❌ {x}")
    return len(loi)


def main() -> int:
    if len(sys.argv) < 2:
        print("dùng: qc_hinh.py <đường dẫn .json props>  [<đường dẫn .mp4>]")
        return 2
    n = 0
    pj = sys.argv[1]
    n += _in(f"TRƯỚC render · {os.path.basename(pj)}",
             truoc(json.load(io.open(pj, encoding="utf-8"))))
    if len(sys.argv) > 2:
        n += _in(f"SAU render · {os.path.basename(sys.argv[2])}", sau(sys.argv[2]))
    print(f"\n{'✅ QC SẠCH' if not n else f'❌ QC: {n} lỗi'}")
    return 1 if n else 0


if __name__ == "__main__":
    raise SystemExit(main())
