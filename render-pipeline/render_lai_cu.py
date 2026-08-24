#!/usr/bin/env python3
"""RENDER LẠI VIDEO DỰNG BẰNG ENGINE CŨ (24/8/2026).

VÌ SAO CÓ FILE NÀY (anh: "kêu dọn xoá rồi mà sao vẫn còn")
----------------------------------------------------------
Vá `.tsx` chỉ đổi CÁCH DỰNG của các phiên SAU. Video đã nằm trong kho là file .mp4 đã đóng gói —
sửa engine không đụng được tới nó. `find_junk.py` cũng không đụng, vì với nó những file đó "đủ
.mp4 + .json + .jpg" nên là video TỐT. Muốn hết bản cũ thì phải **dựng lại** rồi mới bỏ bản cũ đi.

Đó là chỗ khác nhau giữa hai loại việc, hôm nay lẫn lộn nên anh tưởng đã dọn:
  • DỌN RÁC   = file hỏng/thừa   -> bỏ thùng rác luôn, không dựng lại (`find_junk.py`)
  • LÀM MỚI   = file vẫn chạy được nhưng dựng bằng engine CŨ -> phải render lại (file này)

BẢNG MỐC VÁ ENGINE
------------------
Mỗi dòng: video của những kênh dùng motif đó, đẩy kho TRƯỚC mốc -> dựng bằng engine lỗi.
Mốc lấy đúng giờ commit vá (giờ UTC).

CHỈ ĐẾM LÀ MẶC ĐỊNH. Render lại tốn giờ máy chứ không tốn lượt gọi AI (dựng lại từ kịch bản đã
lưu), nhưng vẫn phải có trần mỗi lượt để không dội cả dây chuyền.

    python render_lai_cu.py                        # đếm theo từng bản vá
    python render_lai_cu.py --xep-hang --gioi-han 40
    python render_lai_cu.py --chi guess            # chỉ một bản vá
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict

# ma: (nhãn, tập format kênh, loại video, mốc UTC ISO, mô tả bệnh)
BAN_VA = {
    "guess": ("GUESS mở đầu/kết thúc màn hình đen", {"guess"}, {"short"},
              "2026-08-24T13:54:55+00:00",
              "mở đầu nền đen không hook, cuối video đen thui — nay có ảnh thật + thẻ kết"),
    "pulse": ("PULSE ngắn hụt + lệch tiếng-hình 4,7s", {"pulse"}, {"short"},
              "2026-08-24T15:27:36+00:00",
              "composition bỏ qua `dur` của Python -> video bị cắt ngắn và tiếng lệch khỏi hình"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xep-hang", dest="xep", action="store_true", help="xếp hàng render lại thật")
    ap.add_argument("--gioi-han", type=int, default=40, help="trần số video xếp hàng mỗi lượt")
    ap.add_argument("--chi", default="", help="chỉ chạy một bản vá (guess|pulse)")
    ap.add_argument("--owner", default=os.environ.get("RENDER_OWNER", ""))
    a = ap.parse_args()
    if not a.owner:
        print("❌ thiếu RENDER_OWNER")
        return 1
    bang = {k: v for k, v in BAN_VA.items() if not a.chi or k == a.chi}
    if not bang:
        print(f"❌ không có bản vá tên «{a.chi}» (có: {', '.join(BAN_VA)})")
        return 1

    import firestore_bridge as FB

    # kênh -> format. Đọc 1 lượt, dùng cho mọi bản vá.
    fmt_cua: dict[str, str] = {}
    try:
        for ch in FB.read_channels(a.owner) or []:
            fmt_cua[str(ch.get("name") or "").upper()] = str(ch.get("format") or "").lower()
    except Exception as e:
        print(f"❌ đọc danh sách kênh lỗi: {str(e)[:90]}")
        return 1
    if not fmt_cua:
        print("❌ không đọc được kênh nào — DỪNG (không dám đoán kênh nào dùng motif nào).")
        return 1

    can: dict[str, list] = defaultdict(list)
    tong = 0
    try:
        q = (FB._db_jobs().collection("render_jobs")
             .where("owner", "==", a.owner).where("status", "==", "done"))
        for d in FB._stream_at(q, 90):
            x = d.to_dict() or {}
            if not x.get("drive_id") or x.get("rerender"):
                continue          # chưa lên kho, hoặc đã xếp hàng làm lại rồi
            tong += 1
            ten = str(x.get("channel") or "").upper()
            f = fmt_cua.get(ten, "")
            khi = str(x.get("updated_at") or x.get("created_at") or "")
            for ma, (_nh, fs, loai, moc, _mo) in bang.items():
                if f in fs and (x.get("type") or "") in loai and khi and khi < moc:
                    can[ma].append((d.id, ten, x.get("type", "?"), x.get("drive_id"),
                                    x.get("drive_account", ""), str(x.get("title", ""))[:44]))
                    break
    except Exception as e:
        print(f"❌ đọc render_jobs lỗi: {str(e)[:90]}")
        return 1

    print(f"📊 Soi {tong:,} video đang có file trong kho\n")
    for ma, (nh, _fs, loai, moc, mo) in bang.items():
        ds = can[ma]
        print(f"🔧 {nh}")
        print(f"   bệnh : {mo}")
        print(f"   mốc  : trước {moc}  ·  loại: {'/'.join(sorted(loai))}")
        print(f"   dính : {len(ds)} video")
        for _i, t, ty, _dv, _ac, ti in ds[:5]:
            print(f"          {t:<14} {ty:<6} {ti}")
        if len(ds) > 5:
            print(f"          … và {len(ds) - 5} cái nữa")
        print()

    tat_ca = [v for ma in bang for v in can[ma]]
    if not a.xep:
        print(f"(chạy thử — tổng {len(tat_ca)} video cần làm mới. "
              f"Thêm --xep-hang để xếp hàng, mỗi lượt tối đa --gioi-han {a.gioi_han}.)")
        return 0

    n = 0
    for jid, ten, ty, dv, ac, _ti in tat_ca[: a.gioi_han]:
        try:
            req = FB.new_render_request(a.owner, ten, ty, seed="", replace_id=dv, replace_account=ac)
            FB.mark_job_requeued(jid, req)
            n += 1
        except Exception as e:
            print(f"   ⚠️ {ten}: xếp hàng hụt ({str(e)[:60]})")
    print(f"✅ Xếp hàng làm mới {n} video (dựng lại từ kịch bản đã lưu — KHÔNG tốn lượt gọi AI). "
          f"Bản cũ vào thùng rác sau khi bản mới xong.")
    if len(tat_ca) > a.gioi_han:
        print(f"   ℹ️ còn {len(tat_ca) - a.gioi_han} cái để lượt sau.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
