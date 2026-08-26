#!/usr/bin/env python3
"""ĐO ĐỘ GIỐNG NHAU GIỮA HAI KÊNH BẤT KỲ (26/8/2026).

VÌ SAO CÓ FILE NÀY
------------------
`QC_STANDARD.md §7B` liệt "không lặp một mô-típ giữa các kênh" là điều CHƯA CÓ CHỐT — nghĩa là suốt
thời gian qua không ai trả lời được câu "hai kênh này có giống nhau không" bằng một con số. Mà đây
không phải chuyện thẩm mỹ: hệ 50 kênh cùng chủ, nếu các kênh nhìn/nghe như nhau thì đó đúng là thứ
chính sách "inauthentic, mass-produced content" của YouTube nhắm tới — rủi ro lớn nhất cho việc bật
kiếm tiền, lớn hơn mọi lỗi kỹ thuật khác cộng lại.

Đo lần đầu (trước khi sửa) trên 50 kênh gen-2: **241 cặp ≥70 điểm, cặp tệ nhất 97,9** (ALERT NOW ~
QUAKE LOG gần như một kênh). Lý do lộ ra ngay khi đếm: `font` chỉ có **1** giá trị cho cả 50 kênh,
`voice_tone` cũng **1**, và chưa kênh nào có trường `voice` nên tất cả sẽ đọc bằng cùng một giọng.

CÁCH CHẤM
---------
Điểm 0..100 = "hai kênh này giống nhau bao nhiêu phần trăm dưới mắt và tai khán giả". Trọng số theo
thứ tự thứ mà người xem nhận ra TRƯỚC:

    45  cùng định dạng dựng hình  (thứ đập vào mắt trong 1 giây đầu)
    18  cùng giọng đọc            (nhận ra trong 2 giây đầu, kể cả khi không nhìn)
    12  cùng mô-típ brand kit
    10  màu chủ đạo gần nhau
     8  cùng chữ ký chuyển cảnh
     7  cùng phông chữ

Ngưỡng: **70**. Trên ngưỡng nghĩa là hai kênh đủ giống để một người lướt qua tưởng là cùng một kênh.

    python3 do_giong_nhau.py            # bảng xếp hạng cặp giống nhau nhất
    python3 do_giong_nhau.py --gat      # thoát mã 1 nếu còn cặp vượt ngưỡng (dùng cho chốt)
"""
from __future__ import annotations

import io
import itertools
import json
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
NGUONG = 70.0

TRONG_SO = {"dinh_dang": 45.0, "giong": 18.0, "motif": 12.0, "mau": 10.0, "chuyen": 8.0, "font": 7.0}


def _rgb(h: str) -> tuple:
    h = str(h or "#000000").lstrip("#")
    if len(h) < 6:
        return (0, 0, 0)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _xa(a: tuple, b: tuple) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def _bam(s: str) -> int:
    """PHẢI khớp từng bước với `bam()` trong engine-remotion/src/Chuyen.tsx.

    Nếu hai bên lệch nhau thì con số ở đây là con số của một hệ KHÁC với hệ đang render — tức là
    một phép đo nói dối, còn tệ hơn không đo. `t_bam_python_khop_typescript` giữ hai bên bằng nhau."""
    h = 2166136261
    for ch in str(s or ""):
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    h ^= h >> 15
    h = (h * 2246822519) & 0xFFFFFFFF
    h ^= h >> 13
    return h & 0xFFFFFFFF


MOTIF_CHUYEN = ["quet", "dap", "no", "chuong"]


def chu_ky_chuyen(handle: str) -> str:
    return MOTIF_CHUYEN[_bam(handle) % 4]


def _dac_diem(k: dict, giong: dict | None = None) -> dict:
    b = k.get("brand") or {}
    ten = str(k.get("ten") or "").replace(" ", "")
    g = (giong or {}).get(ten) or {}
    return {
        "ten": k.get("ten"),
        "dinh_dang": k.get("dinh_dang"),
        "motif": b.get("motif"),
        "font": b.get("font"),
        "mau": _rgb((b.get("palette") or {}).get("primary")),
        "chuyen": chu_ky_chuyen(k.get("handle") or ""),
        "giong": (g.get("voice"), g.get("voice_rate"), g.get("voice_pitch")),
    }


def cham(a: dict, b: dict) -> float:
    s = 0.0
    for k in ("dinh_dang", "motif", "font", "chuyen"):
        if a[k] is not None and a[k] == b[k]:
            s += TRONG_SO[k]
    if a["giong"] == b["giong"] and a["giong"][0] is not None:
        s += TRONG_SO["giong"]
    elif a["giong"][0] is not None and a["giong"][0] == b["giong"][0]:
        s += TRONG_SO["giong"] * 0.5      # cùng người, khác tốc/cao độ -> giống một nửa
    s += TRONG_SO["mau"] * max(0.0, 1 - _xa(a["mau"], b["mau"]) / 441.0)
    return round(s, 1)


def _giong_theo_ten() -> dict:
    """Chữ ký giọng seed sẽ ghi. Lấy từ chính `seed_the_he_2.py` để không có hai bản sự thật."""
    import ast
    src = io.open(os.path.join(GOC, "seed_the_he_2.py"), encoding="utf-8").read()
    cay = ast.parse(src)
    giu = [n for n in cay.body
           if (isinstance(n, ast.FunctionDef) and n.name == "chu_ky_giong")
           or (isinstance(n, ast.Assign) and any(getattr(t, "id", "") in ("GIONG", "TOC", "CAO")
                                                 for t in n.targets))]
    ns: dict = {}
    exec(compile(ast.Module(body=giu, type_ignores=[]), "seed", "exec"), ns)
    ks = json.load(io.open(os.path.join(GOC, "kenh_the_he_2.json"), encoding="utf-8"))
    thu_tu = {t: i for i, t in enumerate(sorted(k["ten"].replace(" ", "") for k in ks))}
    return {t: ns["chu_ky_giong"](i) for t, i in thu_tu.items()}


def do() -> list:
    ks = json.load(io.open(os.path.join(GOC, "kenh_the_he_2.json"), encoding="utf-8"))
    try:
        giong = _giong_theo_ten()
    except Exception as e:
        print(f"   ⚠️ không lấy được chữ ký giọng từ seed ({str(e)[:60]}) — chấm thiếu chiều giọng")
        giong = {}
    dd = [_dac_diem(k, giong) for k in ks]
    return sorted(((cham(a, b), a["ten"], b["ten"]) for a, b in itertools.combinations(dd, 2)),
                  reverse=True)


def main() -> int:
    ps = do()
    vuot = [p for p in ps if p[0] >= NGUONG]
    tb = sum(p[0] for p in ps) / max(1, len(ps))
    print(f"📐 {len(ps)} cặp · trung bình {tb:.1f} · cao nhất {ps[0][0]} · "
          f"vượt ngưỡng {NGUONG:.0f}: {len(vuot)}")
    for s, x, y in ps[:10]:
        print(f"   {'❌' if s >= NGUONG else '  '} {s:5.1f}  {x[:24]:26} ~ {y[:24]}")
    if "--gat" in sys.argv and vuot:
        print(f"\n❌ còn {len(vuot)} cặp kênh giống nhau ≥{NGUONG:.0f} — sửa màu/phông/giọng/định dạng")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
