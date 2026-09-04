#!/usr/bin/env python3
"""Cổng: mỗi TRƯỜNG nhịp phải có người ĐỌC — và đọc ở ĐÚNG NHÁNH khuôn của nó.

Vì sao có cổng này (4/9/2026)
─────────────────────────────
§16.6 đã ghi hai lần "trường được GHI mà không ai ĐỌC" (`dinh` 87 chỗ ghi / 0 chỗ đọc;
`the` xoay không theo `loi`), và cách nhận ra được ghi là "liệt kê trường nhịp, liệt kê
`N.<x>` engine đọc, lấy hiệu". Nhưng phép ấy soi CẢ TỆP, nên nó bỏ lọt biến thể khó hơn
— thứ vừa bắt được hôm nay:

    nhịp `howlong` bản dài, khuôn `dem`, ghi `dai_chu: "CAR — 11 months"`.
    Engine CÓ đọc `N.dai_chu` — ở `so_lieu`, `nhom` và `default`. Riêng `case "dem"`
    thì không. Người xem nhận 11 biểu tượng KHÔNG NHÃN, và không lỗi nào báo.

Đúng họ lỗi số 6 của CLAUDE.md: *vá một nhánh, để nguyên nhánh song song*. Phép soi cả
tệp báo XANH cho nó, vì trường ấy có được đọc — chỉ là không phải ở đây.

Nên cổng này đo THEO NHÁNH: với mỗi khuôn, tập trường mà Python thật sự ghi ra phải nằm
trong tập trường đọc được ở nhánh ấy ∪ phần dùng chung ∪ phần Python đọc lại.

Phạm vi — và một đường tha đã bị BÁC BỎ
──────────────────────────────────────
Bản đầu tha mọi trường mà Python đọc lại (`n.get("x")` ở bất kỳ tệp .py nào). Nghe hợp
lý, và nó làm cổng CHẾT: phép ấy tha **946 tên trường**, trong đó có `dai_chu` — tức
tha đúng cái lỗi cổng sinh ra để bắt. Thử ngược chiều "bỏ lại lỗi cũ" trả về XANH.

Chỉ chạy phép thử "không bắt oan" thì bản chết ấy đã đi qua (§13.11: một con số 0 có
hai cách hiểu, phải thử cả chiều ngược lại).

Tín hiệu đúng không phải "Python có đọc lại không" — mà là **engine có coi đây là
trường của mình không**:

    trường KHÔNG xuất hiện ở đâu trong tsx  -> sổ sách nội bộ của Python, ngoài phạm vi
    trường CÓ ở nhánh khác / phần dùng chung -> đúng là trường của engine
        -> mà nhánh này không đọc  -> ❌ vá một nhánh, để nguyên nhánh song song

Không cần danh sách chép tay nào, nên nó không mòn theo thời gian (§13.2).

Chống bắt oan (§13.8):
  1. `N.<x>` nằm NGOÀI switch  -> mọi khuôn đều đọc được  (phần dùng chung)
  2. trường engine chưa từng nhắc -> ngoài phạm vi, KHÔNG phán
  3. không định vị được switch -> DỪNG và nói ra, không báo xanh
"""
import ast
import os
import re
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
TSX = os.path.join(GOC, "..", "engine-remotion", "src", "gt", "KichGiaiThich.tsx")


def _than_switch(s: str) -> tuple[str, dict[str, str]]:
    """Trả (phần NGOÀI switch, {tên_case: thân_case}).

    Cắt bằng cách đếm ngoặc nhọn từ `switch (N.khuon) {` — không dùng regex vượt dòng,
    vì thân case chứa JSX có ngoặc lồng nhiều tầng.
    """
    i = s.find("switch (N.khuon) {")
    if i < 0:
        raise RuntimeError("không tìm thấy `switch (N.khuon) {` — cổng DỪNG, không báo xanh")
    j = s.index("{", i)
    sau, muc = j + 1, 1
    while sau < len(s) and muc:
        muc += (s[sau] == "{") - (s[sau] == "}")
        sau += 1
    if muc:
        raise RuntimeError("ngoặc nhọn của switch không đóng — cổng DỪNG")
    than, ngoai = s[j + 1:sau - 1], s[:i] + s[sau:]

    # Cắt thân theo từng `case "x":` / `default:` ở mức ngoặc 0 của thân switch.
    moc, muc = [], 0
    for m in re.finditer(r'case\s+"([a-z_]+)"\s*:|default\s*:', than):
        muc = (than.count("{", 0, m.start()) - than.count("}", 0, m.start()))
        if muc == 0:
            moc.append((m.start(), m.group(1) or "default"))
    ra = {}
    for k, (vt, ten) in enumerate(moc):
        het = moc[k + 1][0] if k + 1 < len(moc) else len(than)
        ra[ten] = than[vt:het]
    return ngoai, ra


def _truong(txt: str) -> set[str]:
    return set(re.findall(r"\bN\.(\w+)", txt)) | set(re.findall(r'\(N as any\)\?\.\["?(\w+)', txt))


def _nhip_theo_khuon() -> dict[str, set[str]]:
    sys.path.insert(0, GOC)
    import giai_thich as G
    ra: dict[str, set[str]] = {}
    for k in G.KENH:
        for long in (False, True):
            for n in G.kich_ban(k["ma"], 0, long=long)[4]:
                ra.setdefault(n.get("khuon") or "default", set()).update(
                    t for t, v in n.items() if v is not None and v != "")
    return ra


def chay(im: bool = False) -> int:
    tsx = open(TSX, encoding="utf-8").read()
    ngoai, cases = _than_switch(tsx)
    chung = _truong(ngoai)
    # ── VÌ SAO "≥ 2 NHÁNH", KHÔNG PHẢI "CÓ Ở ĐÂU ĐÓ" ────────────────────────────────────
    # Bản trước lấy mọi `N.<x>` trong tsx làm "trường của engine". Chạy thử: 20 dòng đỏ, và
    # đọc tay thì **18/20 là lỗi của phép so** — vượt xa ngưỡng một phần tư mà §13.22 đặt ra
    # để nói một phép so chưa đủ chín làm cổng:
    #   `khuon` là biến PHÂN NHÁNH (`switch (N.khuon)`), rơi ra ngoài mọi thân case
    #   `loi`   là LỜI ĐỌC — engine phát bằng âm thanh qua `tu`, `the_chu` chỉ mượn làm dự phòng
    # Cả hai đều được ghi ở gần như mọi khuôn, nên chúng sinh ra một hàng đỏ vĩnh viễn che
    # mất hai dòng thật nằm cạnh (§15.19: cổng đỏ giả không phiền, nó CHE).
    #
    # Thứ phân biệt `dai_chu` (lỗi thật) với `loi` (không phải lỗi) là số nhánh vẽ nó:
    # `dai_chu` được VẼ ở ba nhánh, tức nó là trường HÌNH dùng chung, và nhánh nào ghi mà
    # không vẽ thì đúng là nhánh bị bỏ quên. Trường chỉ một nhánh đụng tới thì nó là của
    # riêng nhánh ấy, không suy ra được gì cho nhánh khác.
    dem_nhanh: dict[str, int] = {}
    for _v in cases.values():
        for _t in _truong(_v):
            dem_nhanh[_t] = dem_nhanh.get(_t, 0) + 1
    cua_engine = {t for t, n in dem_nhanh.items() if n >= 2}
    viet = _nhip_theo_khuon()
    loi = []
    for khuon, tr in sorted(viet.items()):
        nhanh = cases.get(khuon, cases.get("default", ""))
        doc = _truong(nhanh) | chung
        for t in sorted((tr & cua_engine) - doc):
            noi = sorted(k for k, v in cases.items() if t in _truong(v))
            loi.append(f"khuôn `{khuon}` ghi `{t}` mà nhánh ấy KHÔNG đọc "
                       f"(nhánh có vẽ: {', '.join(noi)})")
    if not im:
        _n = sum(len(v & cua_engine) for v in viet.values())
        print(f"🔎 kiem_truong: {len(cases)} nhánh · {len(viet)} khuôn có nhịp thật · "
              f"soi {_n} cặp (khuôn, trường-của-engine)")
        for e in loi:
            print(f"   ❌ {e}")
        print("   ✅ mọi trường đều có người đọc ở đúng nhánh" if not loi
              else f"   {len(loi)} trường rơi")
    return 1 if loi else 0


if __name__ == "__main__":
    raise SystemExit(chay())
