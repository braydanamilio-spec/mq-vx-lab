#!/usr/bin/env python3
"""TÌM VIDEO BỊ CHỮ CHỒNG CHÉO VÀ XẾP HÀNG RENDER LẠI (24/8/2026).

BỆNH
----
Ảnh chụp của anh (DEFENSEUSA `$750B`, CRIMEUSA `1%`): con số to của lớp HOOK bị câu phụ đề đâm
ngang qua giữa. Hai lớp vẽ ĐỘC LẬP trong `Cinematic.tsx` nên không lớp nào biết lớp kia ở đâu:
  • lớp HOOK biến thể neo đáy: `padding-bottom: 300px` -> khối chữ trải tới y≈1620
  • lớp PHỤ ĐỀ: `bottom: 520` -> băng chữ nằm ở y≈1200-1400
Bố cục hook chọn bằng **băm** `(stat + line)` rồi `% 4`, nên **đúng 1/4 số video** rơi vào biến thể
hỏng — giải thích vì sao lúc thấy lúc không, và vì sao QC không bắt được (video vẫn "sạch, đọc rõ").

Đã vá trong `Cinematic.tsx` (ép hook nằm trọn phía trên băng phụ đề) + chốt `t_bo_cuc_khong_chong`
trong selftest để không tái phát. Nhưng video ĐÃ RENDER thì phải làm lại — script này tìm ĐÚNG
những cái dính, không render lại tràn lan (render lại tất cả là đốt quota vô ích cho 3/4 số video
vốn không sao).

CÁCH TÌM
--------
Mỗi job `done` có kèm KỊCH BẢN đã lưu (`script`). Lấy `thumb_stat`/`thumb_hook` trong đó, chạy lại
ĐÚNG hàm băm của `Cinematic.tsx`, ra biến thể = 2 thì video đó đã bị chồng chữ.
Render lại dùng chính đường `new_render_request` của nút 🔄 trên dashboard: dựng lại từ kịch bản đã
lưu nên **không tốn thêm một lượt gọi AI nào**, và bản cũ được bỏ vào thùng rác sau khi bản mới xong.

    python find_overlap_videos.py                 # chỉ đếm và liệt kê (mặc định)
    python find_overlap_videos.py --xep-hang      # xếp hàng render lại thật
    python find_overlap_videos.py --xep-hang --gioi-han 30
"""
from __future__ import annotations

import argparse
import json
import os
import sys

BO_CUC_HONG = 2          # biến thể neo đáy — xem Cinematic.tsx


def bam_bo_cuc(stat: str, line: str) -> int:
    """ĐÚNG hàm băm trong Cinematic.tsx:
        let h = 0; for (...) h = (h * 31 + charCodeAt(k)) >>> 0;  const v = h % 4;
    Chép nguyên si (kể cả cắt 32 bit) — lệch một chi tiết là tìm nhầm video."""
    t = (stat or "") + (line or "")
    h = 0
    for ch in t:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h % 4


def _hook_cua(script_raw) -> tuple[str, str]:
    """Lấy (stat, line) y như build_doc_props: thumb_stat[:8] và thumb_hook[:22]."""
    try:
        d = json.loads(script_raw) if isinstance(script_raw, str) else (script_raw or {})
    except Exception:
        return "", ""
    if not isinstance(d, dict):
        return "", ""
    return str(d.get("thumb_stat") or "").strip()[:8], str(d.get("thumb_hook") or "").strip()[:22]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xep-hang", dest="xep", action="store_true",
                    help="xếp hàng render lại thật (mặc định chỉ liệt kê)")
    ap.add_argument("--gioi-han", type=int, default=60,
                    help="tối đa bao nhiêu video xếp hàng một lượt (tránh dội cả dây chuyền)")
    ap.add_argument("--owner", default=os.environ.get("RENDER_OWNER", ""))
    a = ap.parse_args()
    if not a.owner:
        print("❌ thiếu RENDER_OWNER")
        return 1

    import firestore_bridge as FB

    dinh, tong, khong_doc_duoc = [], 0, 0
    try:
        q = (FB._db_jobs().collection("render_jobs")
             .where("owner", "==", a.owner).where("status", "==", "done"))
        for d in FB._stream_at(q, 60):
            x = d.to_dict() or {}
            if not x.get("drive_id") or x.get("rerender"):
                continue                       # chưa lên kho, hoặc đã xếp hàng làm lại rồi
            tong += 1
            stat, line = _hook_cua(x.get("script"))
            if not (stat or line):
                khong_doc_duoc += 1
                continue                       # không có hook (format khác) -> không dính bệnh này
            if bam_bo_cuc(stat, line) == BO_CUC_HONG:
                dinh.append((d.id, x.get("channel", "?"), x.get("type", "?"),
                             x.get("title", "")[:48], stat, x.get("drive_id"),
                             x.get("drive_account", "")))
    except Exception as e:
        print(f"❌ đọc render_jobs lỗi: {str(e)[:90]}")
        return 1

    print(f"📊 Soi {tong} video có file trong kho · {khong_doc_duoc} cái không có lớp hook (không dính bệnh)")
    print(f"🎯 Dính chữ chồng chéo: {len(dinh)} video"
          f" ({len(dinh) * 100 // max(1, tong - khong_doc_duoc)}% số video có hook — lý thuyết ~25%)")
    for _id, ch, ty, ti, stat, _dv, _acc in dinh[:15]:
        print(f"   {ch:<14} {ty:<6} «{stat}» {ti}")
    if len(dinh) > 15:
        print(f"   … và {len(dinh) - 15} cái nữa")

    if not a.xep:
        print("\n(chạy thử — thêm --xep-hang để xếp hàng render lại thật)")
        return 0

    n = 0
    for _id, ch, ty, _ti, _stat, dv, acc in dinh[:a.gioi_han]:
        try:
            req = FB.new_render_request(a.owner, ch, ty, seed="", replace_id=dv, replace_account=acc)
            FB.mark_job_requeued(_id, req)
            n += 1
        except Exception as e:
            print(f"   ⚠️ {ch}: xếp hàng hụt ({str(e)[:60]})")
    print(f"\n✅ Đã xếp hàng render lại {n} video (dựng lại từ kịch bản đã lưu — KHÔNG tốn lượt gọi AI). "
          f"Bản cũ vào thùng rác sau khi bản mới xong.")
    if len(dinh) > a.gioi_han:
        print(f"   ℹ️ còn {len(dinh) - a.gioi_han} cái để lượt sau (giới hạn {a.gioi_han}/lượt).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
