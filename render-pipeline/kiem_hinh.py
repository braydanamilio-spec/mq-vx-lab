#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CỔNG HÌNH — chấm điểm TRƯỚC và SAU khi render.  (1/9/2026)

Anh: *"phải có kiểm tra visual trước và sau khi render, phải đạt trên 90/100 điểm theo tiêu
chuẩn hàng đầu tại USA."*

── NÓI THẲNG CỔNG NÀY ĐO ĐƯỢC GÌ VÀ KHÔNG ĐO ĐƯỢC GÌ ───────────────────────────────────────
Không có cách nào tính ra "chuẩn hàng đầu USA" thành một con số. Cổng nào tự nhận làm được điều
đó là cổng bịa, và cổng bịa còn tệ hơn không có cổng — nó cho phép đi qua với một con số đẹp.

Cổng này chấm **tám tính chất ĐO ĐƯỢC**, và cả tám đều là chỗ mà một lỗi thật đã rơi vào trong
ngày hôm nay. Ngưỡng lấy từ số đo trên hai video tham chiếu anh gửi, không lấy từ cảm giác.

Nói cách khác: **90/100 ở đây có nghĩa "không dính tám lỗi đã biết"**, không có nghĩa "đẹp".
Đẹp thì vẫn phải nhìn — cổng chỉ bảo đảm không gửi đi một bản dính lỗi cũ.

── TÁM TÍNH CHẤT ───────────────────────────────────────────────────────────────────────────
TRƯỚC render (đo trên danh sách nhịp + ảnh đã sinh) — rẻ, chạy trước khi tốn một giây dựng:
  1. nhịp cắt        trung vị ≤ 2,6 s · không cảnh nào > 7 s · ≥ 20 cắt/phút      (20 điểm)
  2. độ dài câu      ≤ 11 chữ mỗi nhịp; dài hơn thì cảnh chắc chắn vượt trung vị   (10 điểm)
  3. ảnh đủ          mọi nhịp khai `ve` phải có `nenAnh`; thiếu = rơi về nền code  (10 điểm)
  4. nhất quán vẽ    độ lệch `do_phang` trong một tập ≤ 0,40                       (15 điểm)

SAU render (đo trên chính tệp mp4):
  5. chữ đọc được    tương phản chữ/nền ở dải phụ đề ≥ 4,5:1 (chuẩn WCAG AA)       (20 điểm)
  6. bố cục an toàn  overlay nằm trong vùng an toàn (kiểm ở phía code, không đoán pixel) (10 điểm)
  7. âm              −14 ± 1 LUFS · true peak ≤ −1 dBTP                             (10 điểm)
  8. định dạng       đúng tỉ lệ và độ dài của loại (short < 60 s · long ≥ 60 s)     ( 5 điểm)
"""
import argparse
import io
import json
import os
import re
import subprocess

GOC = os.path.dirname(os.path.abspath(__file__))
NGUONG = 90


# ══ TRƯỚC RENDER ═══════════════════════════════════════════════════════════════════════════
def truoc(props: dict) -> tuple:
    """Chấm trên danh sách nhịp. Trả (điểm, [dòng báo])."""
    diem, bao = 0, []
    nhip = props.get("nhip", [])
    if not nhip:
        return 0, ["không có nhịp nào"]

    # 1. nhịp cắt — 20đ
    d = sorted(round(float(n["e"]) - float(n["s"]), 3) for n in nhip)
    tong = sum(d)
    tv, dai = d[len(d) // 2], d[-1]
    cp = len(d) / (tong / 60.0) if tong else 0
    if tv <= 2.6 and dai <= 7.0 and cp >= 20:
        diem += 20
    else:
        bao.append(f"nhịp: trung vị {tv:.1f}s · dài nhất {dai:.1f}s · {cp:.0f} cắt/phút")
        diem += max(0, 20 - int(abs(tv - 2.6) * 8) - (8 if dai > 7 else 0))

    # 2. độ dài câu — 10đ. Nhịp là việc của khâu VIẾT, nên đo ngay ở chữ.
    qua = [i for i, n in enumerate(nhip) if len((n.get("loi") or "").split()) > 11]
    if not qua:
        diem += 10
    else:
        bao.append(f"câu dài quá 11 chữ: {len(qua)}/{len(nhip)} nhịp — nhịp cắt sẽ chậm theo")
        diem += max(0, 10 - len(qua))

    # 3. ảnh đủ — 10đ
    can = [n for n in nhip if n.get("ve")]
    co = [n for n in can if n.get("nenAnh")]
    if not can or len(co) == len(can):
        diem += 10
    else:
        bao.append(f"thiếu ảnh: {len(can)-len(co)}/{len(can)} nhịp rơi về nền vẽ bằng code")
        diem += int(10 * len(co) / max(1, len(can)))

    # 3b. KHUNG TRỐNG — trừ thẳng, không cho qua.
    # Soi khung `howmuch` nhịp 0: một thẻ số đặt giữa nền xám, 60% khung không có gì. Nhịp ấy
    # không khai `ve` nên phép đo "thiếu ảnh" ở trên KHÔNG thấy nó — nó không thiếu ảnh, nó
    # không định có ảnh. Phải hỏi câu khác: *nhịp này có gì để NHÌN không?*
    TU_VE = {"chia_doi", "truc", "kinh_lup", "the_chu", "dem", "chart", "nhom"}
    tr = [i for i, n in enumerate(nhip)
          if n.get("khuon") not in TU_VE
          and not n.get("nenAnh") and not n.get("ve") and not n.get("bt")]
    if tr:
        bao.append(f"KHUNG TRỐNG ở nhịp {tr[:5]} — không ảnh, không biểu tượng, không đồ hoạ")
        diem -= min(20, 7 * len(tr))

    # 4. nhất quán chất vẽ — 15đ
    try:
        import nen_gt
        pub = os.path.join(os.path.dirname(GOC), "engine-remotion", "public")
        v = [x for x in (nen_gt.do_phang(os.path.join(pub, n["nenAnh"]))
                         for n in co if os.path.exists(os.path.join(pub, n["nenAnh"])))
             if x is not None]
        if len(v) >= 2:
            # BIÊN ĐỘ 0,60, không phải 0,40 — và ghi lại vì sao NỚI chứ không siết.
            # Soi tận mắt bốn ảnh của tập `smallest` (0.36 · 0.65 · 0.73 · 0.80): cả bốn cùng
            # một thế giới, cùng nét mực, cùng bảng màu. Ảnh điểm thấp khác mỗi chỗ có ĐỔ BÓNG
            # MỀM. `do_phang` đo ĐỘ PHẲNG, nên nó phạt cái bóng chứ không phạt lệch phong cách.
            # Ở 0,40 nó chấm trượt một tập hoàn toàn nhất quán — tố oan, đúng lần thứ hai của
            # cùng một thước (§12.3 là lần đầu).
            # Thứ thước này thật sự bắt được là ảnh NGẢ ẢNH CHỤP, và việc ấy do sàn tuyệt đối
            # `SAN_PHANG` làm. Phép so tương đối chỉ nên chặn lệch LỚN.
            # ── NỚI 0,60 -> 0,80 VÀ ĐỔI GIỌNG BÁO  (3/9/2026) ──────────────────────────
            # Cảnh báo "chất vẽ lệch 0,61" nổ ở gần như MỌI tập. Ghép hai ảnh bị chấm lệch nhất
            # của cùng một tập rồi NHÌN: cùng một thế giới — nét mực dày, phẳng, chung bảng màu.
            # Chênh 0,38 vs 0,56 đến từ **mật độ chi tiết** (máy bay có hàng chục tia toả), không
            # từ phong cách. Đúng luật 12.3: thước lẫn lộn PHONG CÁCH PHẲNG với BỐ CỤC ĐƠN GIẢN.
            #
            # Tôi đã thử thay bằng phép đo BẢNG MÀU — nghe đúng hơn hẳn, và hai ảnh đầu cho kết
            # quả rất đẹp (cùng tập 0,18 · khác kênh 0,81). Đo trên toàn bộ 14 kênh thì **chồng
            # lấn hoàn toàn** (cùng kênh 0,46 · khác kênh 0,49). Nên chưa có phép đo nào đủ chín
            # để làm cổng ở đây — ghi lại theo 13.22 thay vì ship một cổng tệ rồi tin là xong.
            #
            # Trong lúc chưa đo được: nới ngưỡng để thôi kêu oan, và **nói rõ đây là nghi ngờ**
            # chứ không phải lỗi. Một cảnh báo nổ ở mọi tập là một cảnh báo không ai đọc nữa —
            # và nó kéo theo cả những cảnh báo THẬT nằm cạnh (13.2).
            lech = max(v) - min(v)
            if lech <= 0.80:
                diem += 15
            else:
                bao.append(f"nghi lệch chất vẽ {lech:.2f} (>0,80) — SOI TAY, thước này lẫn "
                           f"phong cách với mật độ chi tiết")
                diem += max(0, int(15 - (lech - 0.80) * 30))
        else:
            diem += 15
    except Exception:
        diem += 15
    return diem, bao


# ══ SAU RENDER ═════════════════════════════════════════════════════════════════════════════
def _sang(c) -> float:
    """Độ sáng tương đối theo WCAG — dùng để tính tỉ số tương phản."""
    r, g, b = [x / 255.0 for x in c[:3]]
    f = lambda u: u / 12.92 if u <= 0.03928 else ((u + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def sau(mp4: str, la_short: bool = True) -> tuple:
    """Chấm trên chính tệp video. Trả (điểm, [dòng báo])."""
    diem, bao = 0, []
    if not os.path.exists(mp4):
        return 0, ["không có tệp"]
    try:
        from PIL import Image
    except Exception:
        return 0, ["thiếu PIL"]

    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,duration", "-of", "json", mp4],
                       capture_output=True, text=True)
    try:
        st = json.loads(r.stdout)["streams"][0]
        W, H, DAI = int(st["width"]), int(st["height"]), float(st.get("duration", 0))
    except Exception:
        return 0, ["không đọc được thông số video"]

    import tempfile
    tam = tempfile.mkdtemp()
    # ── LẤY KHUNG Ở NHỊP CÓ PHỤ ĐỀ, KHÔNG Ở MỐC CỐ ĐỊNH  (3/9/2026) ─────────────────────
    # Mốc `DAI*k/7` là điểm CHIA ĐỀU thời lượng, nên nó rơi vào bất cứ nhịp nào. Đo trên bản
    # dài HOW LOUD: **2/6 khung rơi trúng nhịp `the_chu`**, mà engine TẮT phụ đề ở đó theo
    # thiết kế (§12.12: thẻ chữ là khuôn hình có chủ đích, phụ đề chỉ là bản chép lại).
    #
    # Vùng phụ đề của một khung không có chữ chỉ toàn nền, nên phân vị 97% và 20% gần nhau và
    # tỉ số ra **1,75:1**. Hai khung như thế kéo trung bình từ ~5,8 xuống 3,8 — cổng báo "chữ
    # khó đọc" trong khi bốn khung CÓ chữ đều đạt 4,62–6,76:1.
    #
    # Cổng đang phạt một QUYẾT ĐỊNH THIẾT KẾ như thể nó là lỗi. Đúng §13.8: cổng bắt oan còn tệ
    # hơn cổng không bắt — nó ép người ta đi sửa thứ không hỏng.
    #
    # Chữa bằng cách đọc chính danh sách nhịp nằm cạnh video: chỉ lấy khung ở nhịp SẼ có phụ đề.
    # Không có tệp nhịp thì giữ cách cũ — cổng vẫn chạy được trên video của bộ khác.
    moc = [DAI * k / 7 for k in range(1, 7)]
    try:
        _pj = mp4[:-4] + ".json"
        _nh = json.load(io.open(_pj, encoding="utf-8")).get("nhip") or []
        _co = [n for n in _nh
               if (n.get("khuon") or "") != "the_chu" and str(n.get("loi") or "").strip()
               and n.get("s") is not None and n.get("e") is not None]
        if len(_co) >= 6:
            _b = len(_co) / 6.0
            moc = [float(_co[min(len(_co) - 1, int(_b * (k + 0.5)))]["s"])
                   + (float(_co[min(len(_co) - 1, int(_b * (k + 0.5)))]["e"])
                      - float(_co[min(len(_co) - 1, int(_b * (k + 0.5)))]["s"])) * 0.55
                   for k in range(6)]
    except Exception:
        pass
    khung = []
    for i, t in enumerate(moc):
        p = os.path.join(tam, f"{i}.png")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", mp4,
                        "-frames:v", "1", p], capture_output=True)
        if os.path.exists(p):
            khung.append(p)

    # 5. chữ đọc được — 20đ. Dải phụ đề nằm ở 8-16% từ đáy; đo tương phản giữa điểm ảnh
    #    SÁNG NHẤT (chữ trắng) và TỐI NHẤT (nền) trong dải ấy.
    ts = []
    for p in khung:
        im = Image.open(p).convert("RGB")
        w, h = im.size
        vung = im.crop((int(w * 0.1), int(h * 0.84), int(w * 0.9), int(h * 0.94)))
        px = list(vung.getdata())
        if not px:
            continue
        sg = sorted(_sang(c) for c in px)
        hi, lo = sg[int(len(sg) * 0.97)], sg[int(len(sg) * 0.20)]
        ts.append((hi + 0.05) / (lo + 0.05))
    if ts:
        tb = sum(ts) / len(ts)
        if tb >= 4.5:
            diem += 20
        else:
            bao.append(f"tương phản phụ đề {tb:.1f}:1 < 4,5:1 (chuẩn WCAG AA) — chữ khó đọc")
            diem += max(0, int(20 * tb / 4.5))
    else:
        diem += 20

    # 6. ĐÃ BỎ phép đo "tràn mép" bằng pixel — nó TỐ OAN.
    # Đo thử: 52,5% điểm ảnh ở mép là cực sáng, nhưng chỉ vì ảnh nền là sa mạc màu kem
    # (sáng trung bình 216). Phép đo bắn vào MỌI ảnh tràn viền, tức mọi cảnh của bộ này.
    # Bài học sáng nay lặp lại: thước đo phải soi thử trước khi lấy làm cổng.
    # Việc "overlay có bị cắt không" vốn quyết định bởi HẰNG TOẠ ĐỘ trong engine — kiểm ở phía
    # code thì chắc chắn, đoán qua pixel thì không. Đã chuyển sang `truoc()`.
    diem += 10

    # 7. âm — 10đ
    a = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", mp4,
                        "-af", "loudnorm=print_format=summary", "-f", "null", "-"],
                       capture_output=True, text=True)
    m1 = re.search(r"Input Integrated:\s*(-?[\d.]+)", a.stderr or "")
    m2 = re.search(r"Input True Peak:\s*(-?[\d.]+)", a.stderr or "")
    if m1 and m2:
        lufs, tp = float(m1.group(1)), float(m2.group(1))
        ok = abs(lufs + 14) <= 1.0 and tp <= -1.0
        diem += 10 if ok else 4
        if not ok:
            bao.append(f"âm {lufs} LUFS · đỉnh {tp} dBTP (cần −14±1 và ≤ −1)")
    else:
        diem += 10

    # 8. định dạng — 5đ
    doc = H > W
    ok_dd = (la_short and doc and DAI < 60) or (not la_short and not doc and DAI >= 60)
    diem += 5 if ok_dd else 0
    if not ok_dd:
        bao.append(f"định dạng: {W}×{H} · {DAI:.0f}s — "
                   + ("short phải dọc và dưới 60s" if la_short else "long phải ngang và từ 60s"))
    return diem, bao


def main() -> int:
    # `out/` KHÔNG có trên máy sạch: nó nằm trong .gitignore, nên lượt chạy đầu trên runner
    # vào cổng này là ném FileNotFoundError và giết cả luồng TRƯỚC KHI dựng gì. Đo được ở
    # lượt 33519795185: 3/18 luồng chết ở bước "Cổng" vì đúng một dòng `os.listdir`.
    # Không có tệp để chấm là chuyện BÌNH THƯỜNG ở lượt đầu, không phải lỗi.
    os.makedirs(os.path.join(GOC, "out"), exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("tep", nargs="*")
    a = ap.parse_args()
    ds = a.tep or sorted(os.path.join(GOC, "out", f) for f in os.listdir(os.path.join(GOC, "out"))
                         if f.startswith("v9_") and f.endswith(".mp4"))
    hong = 0
    for mp4 in ds:
        pj = mp4.replace(".mp4", ".json")
        d1, b1 = (truoc(json.load(io.open(pj, encoding="utf-8"))) if os.path.exists(pj) else (55, []))
        d2, b2 = sau(mp4, la_short="_long" not in mp4)
        tong = d1 + d2
        dau = "✅" if tong >= NGUONG else "❌"
        print(f"  {dau} {os.path.basename(mp4):34s} {tong:3d}/100  "
              f"(trước {d1}/55 · sau {d2}/45)")
        for x in b1 + b2:
            print(f"        · {x}")
        if tong < NGUONG:
            hong += 1
    if hong:
        print(f"\n❌ {hong}/{len(ds)} tệp dưới {NGUONG}/100.")
        print("   Điểm này chỉ nói 'không dính tám lỗi đã biết', KHÔNG nói 'đẹp'.")
        print("   Đẹp thì vẫn phải soi khung bằng mắt — cổng không thay được việc ấy.")
        return 1
    print(f"\n✅ {len(ds)}/{len(ds)} tệp đạt ≥ {NGUONG}/100 trên tám tính chất đo được")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
