#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHUẨN BỊ NỀN — BỐN TẦNG BẢO VỆ, CHẠY TRƯỚC KHI RENDER (31/8/2026)
════════════════════════════════════════════════════════════════════════════════════════════

Anh: *"thế thì phải có 2 tầng bảo vệ hoặc tìm hướng xử lý"* — sau khi tôi nêu rằng sinh nền lúc
render thì API lỗi là video không có nền.

Hướng xử lý không phải thêm một lớp thử-lại, mà là TÁCH HẲN HAI VIỆC:

    chuẩn bị tài nguyên   →  gọi API, được phép chậm, được phép hỏng và thử lại
    render                →  chỉ đọc từ đĩa, KHÔNG gọi API, không bao giờ hỏng vì mạng

Trên GitHub Actions đây là hai bước riêng. Bước chuẩn bị hỏng thì bước render vẫn chạy với
những gì đã có — và nó luôn có gì đó, nhờ bốn tầng dưới đây.

── BỐN TẦNG, XẾP TỪ TỐT NHẤT XUỐNG CHẮC CHẮN NHẤT ────────────────────────────────────────
  1. NỀN RIÊNG của nơi chốn (hoặc chủ đề) — đã cache sẵn. Khớp nhất, nhanh nhất.
  2. SINH BÙ ngay tại bước chuẩn bị nếu tầng 1 thiếu. Có 94 tài khoản CF nên gần như luôn xong;
     và nếu hỏng thì hỏng ở ĐÂY, trước khi tốn một phút render nào.
  3. MƯỢN nền của một nơi khác trong CÙNG kênh. Mười nơi của một kênh cùng một thế giới, nên
     nền mượn vẫn khớp ngữ cảnh — hơn hẳn việc không có gì.
  4. NỀN VECTOR vẽ bằng code. Không gọi API, không tệp nào cần tải, không bao giờ hỏng. Xấu hơn
     ba tầng trên nhưng luôn có, và luôn có sàn — nên nhân vật không bao giờ lơ lửng.

Tầng 4 là thứ khiến cả hệ không có điểm chết. Bản `KichHai` cũ chỉ có tầng 2, nên ngày nào API
trục trặc là ngày ấy video ra không nền.
"""
import os
import io
import json
import argparse

from kich_hai import KENH as KENH_HAI, _ten_tep, GOC, ENG

THU = os.path.join(ENG, "public", "comic_nen")
BAN_DO = os.path.join(GOC, "nen_cf.json")


def quet_dia() -> dict:
    """Tầng 1 — dựng bản đồ TỪ ĐĨA, không tin tệp chỉ mục.

    Tệp chỉ mục từng bị một lần chạy sau ghi đè mất bảy kênh (xem PIPELINE_RULES 19.3). Đĩa mới
    là sự thật; chỉ mục chỉ là bộ nhớ đệm dựng lại được bất cứ lúc nào.
    """
    import re
    ra = {}
    if not os.path.isdir(THU):
        return ra
    for f in sorted(os.listdir(THU)):
        m = re.match(r"(.+)_(\d{2})\.jpg$", f)
        if m and os.path.getsize(os.path.join(THU, f)) > 20000:
            ra.setdefault(m.group(1), {})[str(int(m.group(2)))] = f"comic_nen/{f}"
    return ra


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", default="")
    ap.add_argument("--so", type=int, default=10, help="số nơi chốn mỗi kênh cần có nền")
    ap.add_argument("--sinh", action="store_true", help="sinh bù nếu thiếu (gọi API)")
    ap.add_argument("--vong", type=int, default=-1,
                    help="sinh NỀN RIÊNG cho tập này (mỗi tập một ảnh, không dùng lại)")
    a = ap.parse_args()

    # ── NỀN RIÊNG CHO TỪNG TẬP ────────────────────────────────────────────────────────────
    # 1/9 — anh: *"tạo cho đa dạng, ko dùng lại, mà tạo cho đúng bối cảnh channel, videos"* và
    # *"key api free dư sức mà"*. Đúng cả hai: dùng lại một ảnh cho mọi tập là tự tay làm kênh
    # nhàm, còn 97 khoá CF cho ~16.300 ảnh/ngày nên 10 ảnh mỗi lượt là không đáng kể.
    #
    # Sinh Ở ĐÂY, không sinh lúc render: bước chuẩn bị được phép gọi API và được phép hỏng;
    # bước render chỉ đọc đĩa. Hỏng ở đây thì `noi_va_nen` rơi xuống kho 110 ảnh chuẩn — video
    # vẫn có nền, chỉ là nền dùng chung.
    if a.vong >= 0:
        import kich_comic as KC
        from nen_cf import sinh_mot as _sinh
        import the_he_2 as T2
        keys = [x for x in (T2.keys_cuc_bo() or [])
                if (x if isinstance(x, str) else x.get("key", "")).startswith("cf:")]
        if not keys:
            print("⚠️ không có khoá CF — bỏ bước sinh nền riêng, dùng kho ảnh chuẩn")
            return 0
        n_ok = 0
        chon0 = KENH_HAI
        if a.kenh:
            vt0 = {x.strip().upper() for x in a.kenh.split(",")}
            chon0 = [x for x in KENH_HAI if x["ten"].replace(" ", "").upper() in vt0]
        ds0 = json.load(io.open(os.path.join(GOC, "noi_chon.json"), encoding="utf-8"))
        for k in chon0:
            # Nơi chốn của ĐÚNG tập này — hỏi chính hàm mà bước dựng sẽ hỏi, để hai bên không
            # bao giờ lệch nhau về nơi chốn.
            kb, cau = KC.mau_cua_tap(k, a.vong)
            idx, _cu = KC.noi_va_nen(k, kb, cau, a.vong)
            if idx < 0:
                print(f"   ⏭ {k['ten']:19s} tập {a.vong}: không rõ nơi chốn -> dùng kho chuẩn")
                continue
            ten_noi = (ds0.get(k["de"]) or [""] * (idx + 1))[idx]
            r = _sinh(_ten_tep(k), idx, ten_noi, k["ten"], keys, False, k["de"], a.vong)
            print(f"   {'✅' if r else '❌'} {k['ten']:19s} tập {a.vong} · {ten_noi[:34]}",
                  flush=True)
            n_ok += bool(r)
        print(f"\n✅ {n_ok}/{len(chon0)} nền riêng cho tập {a.vong}")
        return 0

    ds = {}
    try:
        ds = json.load(io.open(os.path.join(GOC, "noi_chon.json"), encoding="utf-8"))
    except Exception as e:
        print(f"❌ không đọc được noi_chon.json: {e}")
        return 2

    co = quet_dia()
    chon = KENH_HAI
    if a.kenh:
        vt = {x.strip().upper() for x in a.kenh.split(",")}
        chon = [x for x in KENH_HAI if x["ten"].replace(" ", "").upper() in vt]

    thieu, tong = [], 0
    print(f"{'kênh':19s} {'cần':>4s} {'có':>4s}  tầng dùng")
    for k in chon:
        slug = _ten_tep(k)
        can = min(a.so, len(ds.get(k["de"], [])))
        cok = co.get(slug, {})
        tong += can
        for i in range(can):
            if str(i) not in cok:
                thieu.append((k, i, ds[k["de"]][i]))
        # tầng nào đang gánh: riêng · mượn cùng kênh · vector
        tang = ("1 riêng" if len(cok) >= can
                else f"3 mượn ({len(cok)}/{can})" if cok else "4 vector")
        print(f"{k['ten']:19s} {can:4d} {len(cok):4d}  {tang}")

    print(f"\n  tổng {tong - len(thieu)}/{tong} nơi chốn có nền riêng · thiếu {len(thieu)}")

    if not thieu:
        print("✅ đủ nền — bước render sẽ không gọi API lần nào")
        return 0

    if not a.sinh:
        print("   (thêm --sinh để sinh bù; không sinh thì tầng 3 và 4 gánh, video vẫn ra)")
        return 0

    # ── TẦNG 2: sinh bù, và hỏng ở ĐÂY chứ không hỏng lúc render ──────────────────────────
    import the_he_2 as T2
    from nen_cf import sinh_mot
    import xoay_key
    keys = T2.keys_cuc_bo() or []
    if not xoay_key.loc_cf(keys):
        print("⚠️ không có khoá CF — bỏ qua sinh bù, tầng 3/4 sẽ gánh")
        return 0

    xong = 0
    ngoai = set()
    try:
        import re
        tsx = io.open(os.path.join(ENG, "src", "comic", "NoiChon.tsx"), encoding="utf-8").read()
        b = tsx[tsx.index("export const NOI"):tsx.index("// ══ SINH NƠI CHỐN")]
        mocs = [m.start() for m in re.finditer(r'\{ ten: "', b)] + [len(b)]
        for i in range(len(mocs) - 1):
            kh = b[mocs[i]:mocs[i + 1]]
            if "ngoai: true" in kh:
                ngoai.add(re.search(r'\{ ten: "([^"]+)"', kh).group(1))
    except Exception:
        pass

    for k, i, noi in thieu:
        r = sinh_mot(_ten_tep(k), i, noi, k["ten"], keys, noi in ngoai)
        print(f"   {'✅' if r else '❌'} {k['ten']:19s} {i:02d} {noi[:40]}", flush=True)
        xong += bool(r)

    io.open(BAN_DO, "w", encoding="utf-8").write(
        json.dumps(quet_dia(), ensure_ascii=False, indent=1))
    print(f"\n✅ sinh bù {xong}/{len(thieu)} nền · bản đồ dựng lại từ đĩa")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
