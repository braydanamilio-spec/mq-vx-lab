#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CỔNG ĐA DẠNG GIỮA CÁC KÊNH — đo đúng thứ luật YouTube nhắm vào  (1/9/2026)

Tháng 7/2025 YouTube đổi "repetitious content" thành **"inauthentic content"**. Câu định nghĩa
rủi ro cao, nguyên văn ý: *sản xuất tự động sinh hàng trăm video từ **prompt · bố cục · kịch bản ·
cảnh · giọng · khuôn chuyện** gần như giống hệt nhau, rất ít can thiệp biên tập.* Phạt ba nấc:
cảnh cáo → treo 90 ngày → loại vĩnh viễn khỏi YPP.

Sáu danh từ trong câu ấy là sáu thứ đo được. Tệp này đo chúng, giữa MỌI CẶP kênh:

    prompt      -> lệnh hệ thống `_sys` của hai kênh giống nhau bao nhiêu
    bố cục      -> mô tả căn nhà và tên phòng
    kịch bản    -> `mach` (loại chuyện kênh kể)
    cảnh        -> đồ vật (`dao_cu`) — thứ quyết định TÌNH HUỐNG
    giọng       -> `audio`
    khuôn chuyện-> `hai` (cơ chế hài)
                +  `style` (chỉ đạo hình ảnh — thứ người xem thấy trước cả nội dung)

Vì sao cần cổng chứ không cần lời hứa: mười kênh đầu từng có `audio` giống nhau **1,00** và
`style` giống nhau **0,89** mà không ai thấy, cho tới khi đo. Thêm mười kênh nữa bằng tay thì
xác suất lặp lại chuyện ấy là gần chắc — người viết nhớ được ba kênh, không nhớ được hai mươi.

    python3 kiem_da_dang.py            # bảng tóm tắt + cặp gần nhau nhất
    python3 kiem_da_dang.py --chi-tiet # liệt kê mọi cặp vượt ngưỡng
"""
import argparse
import difflib
import itertools
import sys
from collections import Counter

from kling_kenh import KENH, ho_so, _lich, _sys, SAN_NGHE

# Ngưỡng. Không phải con số tròn cho đẹp — mỗi con số là mức mà đọc hai chuỗi lên thì thấy rõ
# "hai kênh này đang nói cùng một thứ".
#
# `style` được nới rộng nhất (0,55) vì mọi kênh cùng dùng chung `SAN_NGHE` — sàn tay nghề. Phần
# ấy giống nhau là ĐÚNG: nó là chuẩn nghề, không phải bản sắc. Nên trước khi so, cắt nó ra.
NGUONG = {
    "style": 0.55, "audio": 0.42, "hai": 0.30, "mach": 0.45,
    "nha": 0.42, "sys_rieng": 0.45,
}
# Trùng đồ vật / tên phòng / tên vai đo bằng ĐẾM, không bằng độ giống chuỗi.
DO_CHUNG_TOI_DA = 3          # số đồ vật trùng nhau tối đa giữa hai kênh
PHONG_CHUNG_TOI_DA = 2       # số tên phòng trùng nhau tối đa
VAI_TRUNG_TOI_DA = 0         # tên nhân vật KHÔNG được trùng: người xem gặp cùng một cái tên ở
                             # hai kênh là dấu hiệu rõ nhất của một xưởng sản xuất hàng loạt


def _giong(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a or "", b or "").ratio()


def _style_rieng(hs: dict) -> str:
    """Bỏ sàn tay nghề dùng chung trước khi so — phần ấy giống nhau là đúng, không phải lỗi."""
    return (hs.get("style") or "").split(". " + SAN_NGHE)[0]


def _sys_rieng(kenh: str) -> str:
    """Phần lệnh hệ thống RIÊNG của kênh — bỏ bộ luật dùng chung.

    1/9 — Bản đầu so nguyên `_sys()` và báo **185/190 cặp vượt ngưỡng**. Nhìn vào thì thấy ngay
    cổng sai chứ không phải dữ liệu sai: hai phần ba lệnh hệ thống là luật hài, chuẩn hook, khuôn
    kể và giới hạn cứng — thứ MỌI kênh phải dùng chung vì đó là tay nghề, không phải bản sắc.
    Giống hệt chuyện `SAN_NGHE` trong `style`. Cắt phần chung ra rồi mới so.
    """
    hs = ho_so(kenh)
    return "\n".join([hs.get("mo_ta", ""), hs.get("mach", ""), hs.get("hai", ""),
                       _style_rieng(hs), hs.get("audio", ""), hs.get("dien", ""),
                       hs.get("nha", ""),
                       "\n".join(hs["nhan_vat"].values()),
                       "\n".join(hs["phong"].values())])


def do_cap(a: str, b: str) -> dict:
    ha, hb = ho_so(a), ho_so(b)
    r = {
        "style": _giong(_style_rieng(ha), _style_rieng(hb)),
        "audio": _giong(ha.get("audio"), hb.get("audio")),
        "hai": _giong(ha.get("hai"), hb.get("hai")),
        "mach": _giong(ha.get("mach"), hb.get("mach")),
        "nha": _giong(ha.get("nha"), hb.get("nha")),
        "sys_rieng": _giong(_sys_rieng(a), _sys_rieng(b)),
    }
    r["do_chung"] = sorted(set(ha.get("dao_cu") or ()) & set(hb.get("dao_cu") or ()))
    r["phong_chung"] = sorted(set(ha["phong"]) & set(hb["phong"]))
    r["vai_chung"] = sorted(set(ha["vai"]) & set(hb["vai"]))
    return r


def loi_cap(a: str, b: str, r: dict) -> list:
    e = []
    for k, tran in NGUONG.items():
        if r[k] > tran:
            e.append(f"{k} giống nhau {r[k]:.2f} (trần {tran})")
    if len(r["do_chung"]) > DO_CHUNG_TOI_DA:
        e.append(f"{len(r['do_chung'])} đồ vật trùng: {', '.join(r['do_chung'][:5])}")
    if len(r["phong_chung"]) > PHONG_CHUNG_TOI_DA:
        e.append(f"{len(r['phong_chung'])} tên phòng trùng: {', '.join(r['phong_chung'])}")
    if len(r["vai_chung"]) > VAI_TRUNG_TOI_DA:
        e.append(f"tên nhân vật trùng: {', '.join(r['vai_chung'])}")
    return e


def kiem_lich(n: int = 400) -> list:
    """Hai kênh khác nhau có bao giờ nhận CÙNG một bộ bảy trục ở cùng số tập không?

    Không phải chuyện lý thuyết: `_lich` lệch pha các kênh bằng một phép băm, và phép băm có thể
    đụng nhau. Hai kênh cùng đề bài ở cùng tập nghĩa là hai video cùng ngày cùng tình huống — đúng
    thứ "story patterns gần như giống hệt" mà luật gọi tên.
    """
    e = []
    ks = list(KENH)
    for a, b in itertools.combinations(ks, 2):
        ha, hb = ho_so(a), ho_so(b)
        if set(ha["phong"]) != set(hb["phong"]):
            continue                      # phòng đã khác thì bộ trục không thể trùng
        for so in range(n):
            xa, xb = _lich(a, so), _lich(b, so)
            if all(xa[k] == xb[k] for k in ("phong", "dao_cu", "ap_luc", "kieu_mo", "co_che")):
                e.append(f"{a} và {b} nhận cùng đề bài ở tập {so}")
                break
    return e


def main() -> int:
    ap = argparse.ArgumentParser(description="Đo đa dạng giữa các kênh — cổng chính sách")
    ap.add_argument("--chi-tiet", action="store_true")
    a = ap.parse_args()

    ks = list(KENH)
    caps = [(x, y, do_cap(x, y)) for x, y in itertools.combinations(ks, 2)]
    hong = [(x, y, loi_cap(x, y, r)) for x, y, r in caps if loi_cap(x, y, r)]

    print(f"ĐA DẠNG GIỮA {len(ks)} KÊNH · {len(caps)} cặp\n")
    print(f"  {'trục':10s} {'TB':>6s} {'cao nhất':>9s}  {'trần':>5s}  cặp vượt")
    for k, tran in NGUONG.items():
        v = [r[k] for _, _, r in caps]
        n = sum(1 for x in v if x > tran)
        print(f"  {k:10s} {sum(v)/len(v):6.2f} {max(v):9.2f}  {tran:5.2f}  "
              f"{'✅' if not n else '❌ ' + str(n)}")
    for ten, key, tran in (("đồ vật", "do_chung", DO_CHUNG_TOI_DA),
                           ("tên phòng", "phong_chung", PHONG_CHUNG_TOI_DA),
                           ("tên vai", "vai_chung", VAI_TRUNG_TOI_DA)):
        v = [len(r[key]) for _, _, r in caps]
        n = sum(1 for x in v if x > tran)
        print(f"  {ten:10s} {sum(v)/len(v):6.2f} {max(v):9d}  {tran:5d}  "
              f"{'✅' if not n else '❌ ' + str(n)}")

    lich = kiem_lich()
    print(f"\n  đề bài trùng giữa hai kênh (400 tập đầu): {'✅ không có' if not lich else '❌ ' + str(len(lich))}")
    for x in lich[:5]:
        print("     ", x)

    if hong:
        print(f"\n❌ {len(hong)}/{len(caps)} cặp vượt ngưỡng:\n")
        for x, y, e in (hong if a.chi_tiet else hong[:12]):
            print(f"  {x} ↔ {y}")
            for l in e:
                print(f"     · {l}")
        if not a.chi_tiet and len(hong) > 12:
            print(f"  … còn {len(hong)-12} cặp, xem bằng --chi-tiet")
    else:
        print("\n✅ mọi cặp kênh đều dưới ngưỡng — không cặp nào chung prompt, bố cục, kịch bản,")
        print("   cảnh, giọng hay khuôn chuyện tới mức một người xem nhận ra cùng một xưởng.")
    return 1 if (hong or lich) else 0


if __name__ == "__main__":
    raise SystemExit(main())
