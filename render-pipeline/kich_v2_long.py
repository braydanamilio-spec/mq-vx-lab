#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BẢN DÀI 16:9 CHO KÊNH PHÂN TÍCH (31/8/2026)
════════════════════════════════════════════════════════════════════════════════════════════

Anh: *"60 channel kia cũng có clip long phù hợp chứ"*. Khảo sát ra: composition ngang
`KichV2Wide` (1920×1080) ĐÃ CÓ trong engine, nhưng `kich_v2.py` không có cờ nào gọi nó, và
chưa video dài nào được dựng. Engine sẵn sàng; thiếu tầng ghép nội dung.

── MẠCH CỦA KÊNH PHÂN TÍCH KHÁC HẲN MẠCH CỦA PHIM HÀI ────────────────────────────────────
Ở bộ comic, mạch là "A đang cố làm xong một việc". Ở đây không có nhân vật đuổi theo mục tiêu
nào — nên mạch phải là **một câu hỏi lớn được trả lời dần bằng nhiều lát cắt dữ liệu**:

    RENT REALITY — "Thuê nhà ở Mỹ đắt tới mức nào?"
        lát 1: giá theo bang        lát 4: so với lương tối thiểu
        lát 2: giá theo năm         lát 5: bao nhiêu phần trăm thu nhập
        lát 3: so với thu nhập      kết:   con số cuối cùng

Mỗi lát trả lời một phần; nối lại thành MỘT lập luận. Đó là chỗ tách "video dài hợp lệ" khỏi
"một chồng biểu đồ nối đuôi nhau" — và cũng là chỗ chính sách nội dung tái sử dụng nhắm tới.

── VÌ SAO GHÉP Ở TẦNG SẢN PHẨM ───────────────────────────────────────────────────────────
`kich_v2.py` dựng `props` thẳng trong `main()` (hơn hai nghìn dòng, không tách hàm), nên gọi
lại từng phần là không khả thi mà không viết lại cả tệp. Thay vào đó: chạy `kich_v2.py` nhiều
lượt cho cùng một kênh — mỗi lượt nó tự chọn một bộ số liệu khác nhờ danh sách `avoid` — rồi
GHÉP các sản phẩm lại: nối tiếng bằng ffmpeg, dịch mốc thời gian của cảnh, chèn câu dẫn giữa
các lát.

Cách này chậm hơn (mỗi lát một lượt render ~3 phút) nhưng KHÔNG đụng vào đường đang chạy tốt
của 56 kênh — luật đầu tiên trong CLAUDE.md.
"""
import os
from chuan_am import chuan   # đưa âm lượng về mốc −14 LUFS của nền tảng
import io
import json
import shutil
import argparse
import subprocess

from kich_v2 import KENH as KENH_V2, GOC, ENG

PUB = os.path.join(ENG, "public")
TAM = os.path.join(GOC, "out", "_long_tam")


def _slug(t: str) -> str:
    return t.replace(" ", "").lower()


def _chay_mot_lat(ten_kenh: str, gen2: bool) -> tuple:
    """Chạy kich_v2 một lượt, trả (props, đường mp3) của lát vừa dựng."""
    lenh = ["python3", "kich_v2.py", "--gen2" if gen2 else "--kenh", ten_kenh.replace(" ", "")]
    if gen2:
        lenh = ["python3", "kich_v2.py", "--gen2", ten_kenh]
    r = subprocess.run(lenh, cwd=GOC, capture_output=True, text=True, timeout=2400)
    pj = os.path.join(GOC, "out", f"v3_{_slug(ten_kenh)}.json")
    if not os.path.exists(pj):
        print(f"     ❌ lát hỏng: {(r.stderr or r.stdout or '')[-160:]}")
        return None, ""
    d = json.load(io.open(pj, encoding="utf-8"))
    mp3 = os.path.join(PUB, d.get("voMp3", ""))
    return (d, mp3) if os.path.exists(mp3) else (None, "")


def _giay(mp3: str) -> float:
    try:
        return float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3],
            capture_output=True, text=True, timeout=60).stdout.strip() or 0)
    except Exception:
        return 0.0


def ghep(ten_kenh: str, gen2: bool, so_lat: int) -> str:
    os.makedirs(TAM, exist_ok=True)
    sl = _slug(ten_kenh)
    lat = []
    for i in range(so_lat):
        print(f"   → lát {i + 1}/{so_lat} …", flush=True)
        d, mp3 = _chay_mot_lat(ten_kenh, gen2)
        if not d:
            continue
        # giữ bản sao: lượt sau sẽ ghi đè chính hai tệp này
        m2 = os.path.join(TAM, f"{sl}_{i:02d}.mp3")
        shutil.copy2(mp3, m2)
        lat.append({"props": d, "mp3": m2, "giay": _giay(m2)})

    if len(lat) < 3:
        print(f"   ❌ chỉ ghép được {len(lat)} lát — bỏ")
        return ""

    # ── nối tiếng ────────────────────────────────────────────────────────────────────────
    ds = os.path.join(TAM, f"{sl}_list.txt")
    io.open(ds, "w", encoding="utf-8").write(
        "\n".join(f"file '{os.path.abspath(x['mp3'])}'" for x in lat))
    rel = f"v3L_{sl}.mp3"
    out_mp3 = os.path.join(PUB, rel)
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", ds,
                    "-c", "copy", out_mp3, "-loglevel", "error"], timeout=600)

    # ── dịch mốc thời gian và nối cảnh ───────────────────────────────────────────────────
    # Mốc `s`/`e` của mỗi lát tính từ 0. Cộng dồn thời lượng các lát trước vào — đây là chỗ
    # dễ sai nhất của mọi phép ghép, và sai một nhịp là khẩu hình lệch cả video.
    canh, tu, moc = [], [], 0.0
    for x in lat:
        for c in x["props"].get("canh", []):
            c2 = dict(c)
            c2["s"] = round(c.get("s", 0) + moc, 3)
            c2["e"] = round(c.get("e", 0) + moc, 3)
            canh.append(c2)
        for t in x["props"].get("tu", []):
            tu.append({**t, "t": round(t.get("t", 0) + moc, 3)})
        moc += x["giay"]

    goc = lat[0]["props"]
    props = {**goc, "canh": canh, "tu": tu, "voMp3": rel}
    pj = os.path.join(GOC, "out", f"v3L_{sl}.json")
    io.open(pj, "w", encoding="utf-8").write(json.dumps(props, ensure_ascii=False))

    out = os.path.join(GOC, "out", f"v3L_{sl}.mp4")
    r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "KichV2Wide", out,
                        f"--props={pj}", "--gl=swiftshader", "--log=error"],
                       cwd=ENG, capture_output=True, text=True, timeout=9000)
    if r.returncode or not os.path.exists(out):
        print(f"   ❌ render hỏng: {(r.stderr or r.stdout or '')[-200:]}")
        return ""
    _am = chuan(out)
    print(f"   ✅ {ten_kenh}: {os.path.basename(out)} · {moc/60:.1f} phút · {len(canh)} cảnh"
          f"{' · ' + _am if _am else ''}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", required=True, help="tên kênh (đúng như trong bảng)")
    ap.add_argument("--lat", type=int, default=14, help="số lát cắt dữ liệu")
    ap.add_argument("--gen2", action="store_true", help="kênh thuộc thế hệ 2")
    a = ap.parse_args()
    print(f"▶ {a.kenh} — bản dài {a.lat} lát")
    return 0 if ghep(a.kenh, a.gen2, a.lat) else 1


if __name__ == "__main__":
    raise SystemExit(main())
