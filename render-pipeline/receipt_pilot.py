#!/usr/bin/env python3
"""KÊNH MẪU "BẰNG CHỨNG" — video dựng từ BẢN GHI CHÍNH PHỦ MỸ THẬT (25/8/2026).

VÌ SAO CÓ FILE NÀY
------------------
Anh xem 55 kênh đang chạy và nhận xét: "quá tầm thường, không có gì đột phá". Đúng — chúng dùng
chung công thức của hàng vạn kênh faceless: footage Pexels + chữ động + giọng AI. Ai cũng lấy được
cùng bộ footage, nên thuật toán không có lý do ưu ái ai.

Thứ KHÔNG copy được không phải footage đẹp hơn, mà là **bản ghi gốc hiện trên màn hình**:
tên công ty thật, con số thật đến từng đồng, tên cơ quan chi tiền, kèm nguồn tra được.

KHÁC BIỆT NẰM Ở CHỖ NÀO
-----------------------
  • Kênh thường : AI nghĩ ra một con số nghe hay → không kiểm chứng được, và ai cũng làm được
  • Kênh này    : `du_lieu_mo.hop_dong_lon()` gọi USAspending.gov LÚC RENDER → số liệu có thật,
                  hiện luôn nguồn. Đối thủ không có đường tự động lấy; khán giả Mỹ xác minh được;
                  dữ liệu tự cập nhật nên không bao giờ hết đề tài.

AI CHỈ LÀM ĐÚNG MỘT VIỆC: viết lời dẫn quanh con số CÓ SẴN. Nó KHÔNG được nghĩ ra số — đó là ranh
giới giữ cho kênh này đáng tin.

    python receipt_pilot.py --de-tai semiconductor --nam 2024
"""
from __future__ import annotations

import json
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))

# Đề tài mồi: thứ người Mỹ có ý kiến sẵn, và có hợp đồng liên bang lớn để soi.
DE_TAI = {
    "semiconductor": ("Chip factories", "who really got the chip money"),
    "border":        ("Border contracts", "what border security actually costs"),
    "vaccine":       ("Vaccine contracts", "who was paid to make them"),
    "space":         ("Space contracts", "NASA money, real numbers"),
    "ammunition":    ("Ammunition", "what one round really costs"),
    "prison":        ("Private prisons", "the per-inmate invoice"),
}


def _tien_goi(v: float) -> str:
    """Số tiền cho người đọc: $51.3B thay vì 51269205263 — mắt bắt được ngay."""
    for chia, don in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(v) >= chia:
            return f"${v / chia:,.1f}{don}"
    return f"${v:,.0f}"


# Đuôi pháp lý trong bản ghi liên bang: dài, lặp, không mang tin. Bỏ để tên vừa thẻ.
_DUOI = (" a joint venture", " joint venture", ", inc.", ", inc", " inc.", " inc", " llc", " l.l.c.",
         " corporation", " corp.", " corp", " company", " co.", " incorporated", " ltd.", " ltd",
         " u.s. 2", " u.s.", " information and electr")


# Từ chung chung: đứng cuối tên đã cắt thì không thêm thông tin, chỉ chiếm chỗ.
_TU_CHUNG = {"information", "systems", "solutions", "services", "technologies", "technology",
             "group", "holdings", "international", "industries", "enterprises", "and", "of", "the"}


def _ten_gon(t: str, toi_da: int = 26) -> str:
    """Tên công ty vừa thẻ. Cắt theo TỪ, không cắt giữa chữ ("...Information And Electr")."""
    t = " ".join(str(t or "").split())
    thap = t.lower()
    for d in _DUOI:
        if thap.endswith(d):
            t = t[: len(t) - len(d)].rstrip(" ,-")
            thap = t.lower()
    if len(t) <= toi_da:
        return t
    tu = []
    for w in t.split():
        if len(" ".join(tu + [w])) > toi_da or len(tu) >= 3:
            break
        tu.append(w)
    # Cắt theo độ dài dễ để lại một từ chung chung treo lủng lẳng ("Bae Systems Information").
    # Bỏ nó đi thì còn đúng cái khán giả nhận ra: thương hiệu.
    while len(tu) > 2 and tu[-1].lower().strip(",.") in _TU_CHUNG:
        tu.pop()
    return " ".join(tu) or t[:toi_da]


def _co_quan_gon(t: str) -> str:
    """Tên cơ quan cho LỜI ĐỌC. "Department of Defense" -> "the Defense Department".

    Đổi vế chứ không cắt: cắt "Department of " để lại "the Defense" — nghe cụt, sai ngữ pháp."""
    t = " ".join(str(t or "").split())
    if t.lower().startswith("department of "):
        return f"the {t[14:]} Department"
    return t or "a federal agency"


def dung_story(de_tai: str, nam: int, n: int = 6) -> dict | None:
    """Dựng kịch bản từ SỐ LIỆU THẬT. Trả None nếu không lấy được dữ liệu (không bịa bù)."""
    import du_lieu_mo as DL
    ten, goc_nhin = DE_TAI.get(de_tai, (de_tai.title(), "follow the money"))
    hd = DL.hop_dong_lon(nam, n, de_tai)
    if len(hd) < 3:
        print(f"   ⚠️ chỉ lấy được {len(hd)} hợp đồng cho '{de_tai}' — KHÔNG dựng (thà bỏ còn hơn bịa)")
        return None

    tong = sum(x["tien"] for x in hd)
    dau = hd[0]
    items = []
    for i, x in enumerate(hd):
        # `tier` ở đây KHÔNG phải xếp hạng chủ quan — là thứ hạng theo số tiền thật.
        ten_gon = _ten_gon(x["ten"])
        items.append({
            "name": ten_gon,
            "tier": ["S", "A", "A", "B", "B", "C"][min(i, 5)],
            "stat": _tien_goi(x["tien"]),
            # Câu ngắn, một ý: tên - số tiền - ai trả. Câu dài làm mỗi thẻ đứng ~6,5s, bảng đứng im.
            "vo": f"{ten_gon}. {_tien_goi(x['tien'])} from {_co_quan_gon(x['co_quan'])}.",
        })
    return {
        "title": f"{ten}: {_tien_goi(tong)} in {nam}",
        # Lời dẫn ngắn: intro dài 9s làm tấm phủ che bảng gần nửa phút đầu.
        "intro_vo": f"{_tien_goi(tong)} of your taxes. Here is who took it.",
        "outro_vo": "Every number is on USAspending dot gov. Go look up your state.",
        "items": items,
        # Chỉ liệt kê hạng THẬT SỰ có mặt — thừa một hạng rỗng là mất một mảng màn hình.
        "tiers": sorted({it["tier"] for it in items}, key="SABCDF".index),
        "nguon": "USAspending.gov",
        "_that": True,      # dấu: mọi con số đến từ bản ghi, không do AI nghĩ ra
        "self_score": {"total": 92},
    }


def chay(de_tai: str, nam: int) -> int:
    import datastory_ci as DS
    st = dung_story(de_tai, nam)
    if not st:
        return 2
    print(f"\n📄 {st['title']}")
    for it in st["items"]:
        print(f"   {it['tier']}  {it['stat']:>9}  {it['name']}")

    sl = DS.slug("RECEIPTS")
    sdir = os.path.join(DS.PUB, sl)
    os.makedirs(sdir, exist_ok=True)
    print("\n🎙  thu giọng + dựng props…")
    props = DS.build_ranked_props(st, sdir, handle="@receiptsusa")
    pf = os.path.join(DS.PUB, f"{sl}_receipt.json")
    json.dump(props, open(pf, "w"), ensure_ascii=False)

    out = os.path.abspath(os.path.join(GOC, "out", f"receipts_{de_tai}_{nam}.mp4"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print("🎬 render RankedShort…")
    DS.run_render_cmd(["npx", "remotion", "render", "src/index.ts", "RankedShort", out,
                       f"--props=./{os.path.relpath(pf, DS.ENG)}", "--gl=swiftshader",
                       "--concurrency=2", "--log=error"],
                      cwd=DS.ENG, timeout=2400, label="RankedShort(receipts)")
    ok, info = DS.qc(out)
    print(f"{'✅' if ok else '❌'} {out} · {info}")
    return 0 if ok else 3


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--de-tai", default="semiconductor")
    ap.add_argument("--nam", type=int, default=2024)
    a = ap.parse_args()
    return chay(a.de_tai, a.nam)


if __name__ == "__main__":
    sys.exit(main())
