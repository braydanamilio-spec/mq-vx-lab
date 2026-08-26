#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DỌN 55 KÊNH THẾ HỆ 1 — kiểm kê trước, dọn sau, và KHÔNG xoá vĩnh viễn (26/8/2026).

MẶC ĐỊNH CHỈ ĐẾM. Không truyền cờ thì script này không thay đổi một byte nào.

Ba lớp dọn, tách riêng để làm từng bước và dừng được giữa chừng:
    --tat        tắt 55 kênh cũ (paused=True). ĐẢO NGƯỢC ĐƯỢC, làm trước tiên.
    --kho        chuyển video + thumbnail + sidecar của kênh cũ vào THÙNG RÁC Drive (giữ 30 ngày)
    --ban-ghi    xoá bản ghi Firestore của kênh cũ (render_channels + hàng chờ)

Vì sao thùng rác chứ không xoá thẳng: dọn nhầm một điều kiện lọc là mất hàng nghìn video không
có đường lùi. Thùng rác cho 30 ngày để phát hiện. Việc đổ thùng rác để người chủ tự bấm.

    python don_the_he_1.py                    # chỉ đếm
    python don_the_he_1.py --tat --that       # tắt kênh cũ
    python don_the_he_1.py --kho --that       # đưa kho vào thùng rác
"""
from __future__ import annotations

import io
import json
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))


def _db():
    """Client Firestore CÓ ĐƯỜNG LẬT B2 — dùng chung với dây chuyền chính.

    26/8 — bản đầu tự dựng client trỏ thẳng project B và chết ngay lần chạy đầu:
    `RESOURCE_EXHAUSTED: Quota exceeded.` vì B đang cạn hạn mức ngày (cờ nghỉ tới 06:59Z).
    Nghịch lý: đúng lúc hệ cạn quota là lúc cần thao tác quản trị nhất (tắt kênh, dọn kho), mà
    công cụ quản trị lại là thứ chết đầu tiên. `firestore_bridge._db_meta()` đã có sẵn failover
    sang gương B2 — dùng lại, đừng dựng client riêng."""
    import firestore_bridge as _FB
    return _FB._db_meta()


def _kenh_moi() -> set:
    p = os.path.join(GOC, "kenh_the_he_2.json")
    if not os.path.exists(p):
        return set()
    return {k["ten"].replace(" ", "") for k in json.load(io.open(p, encoding="utf-8"))}


def main() -> int:
    that = "--that" in sys.argv
    lam_tat = "--tat" in sys.argv
    lam_kho = "--kho" in sys.argv
    lam_bg = "--ban-ghi" in sys.argv
    db = _db()
    owner = os.environ.get("OWNER_UID") or ""
    q = db.collection("render_channels")
    if owner:
        q = q.where("owner", "==", owner)
    tat_ca = [{**(d.to_dict() or {}), "_id": d.id} for d in q.stream()]
    moi = _kenh_moi()
    cu = [c for c in tat_ca if str(c.get("the_he") or "") != "2" and (c.get("name") or "") not in moi]
    m2 = [c for c in tat_ca if str(c.get("the_he") or "") == "2"]

    print(f"\n{'='*70}\nKIỂM KÊ\n{'='*70}")
    print(f"  tổng kênh trong render_channels : {len(tat_ca)}")
    print(f"  kênh THẾ HỆ 1 (sẽ dọn)          : {len(cu)}")
    print(f"  kênh THẾ HỆ 2 (giữ)             : {len(m2)}")
    print(f"  đang bật trong nhóm cũ          : {sum(1 for c in cu if not c.get('paused'))}")
    if not (lam_tat or lam_kho or lam_bg):
        print("\n  (chỉ đếm. Thêm --tat / --kho / --ban-ghi và --that để làm thật)")
        return 0

    if lam_tat:
        n = 0
        for c in cu:
            if c.get("paused"):
                continue
            n += 1
            if that:
                db.collection("render_channels").document(c["_id"]).set({"paused": True}, merge=True)
        print(f"\n  ⏸  {'đã tắt' if that else '(sẽ tắt)'} {n} kênh thế hệ 1")

    if lam_kho:
        src = os.environ.get("AUTOPUBLISHER_SRC")
        if src and src not in sys.path:
            sys.path.insert(0, src)
        try:
            import storage as ST
        except Exception as e:
            print(f"  ❌ không nạp được storage: {str(e)[:60]}")
            return 2
        ten_cu = {(c.get("name") or "").upper() for c in cu}
        tong = 0
        for acc in ST.pool_accounts():
            try:
                dr = ST.account_drive(acc)
            except Exception as e:
                print(f"  ⚠️ kho {acc.get('name', '?')}: {str(e)[:50]}")
                continue
            goc = acc.get("root_id") or acc.get("root")
            if not goc:
                continue
            for f in (dr._list_videos(goc) or []):
                ten = str(f.get("name") or "")
                # CHỈ đụng tệp có tên kênh cũ ở đầu — không quét mù cả kho
                if not any(ten.upper().startswith(t) for t in ten_cu):
                    continue
                tong += 1
                if that:
                    dr.trash(f["id"])
        print(f"\n  🗑  {'đã đưa vào thùng rác' if that else '(sẽ đưa vào thùng rác)'} {tong} tệp "
              f"— Drive giữ 30 ngày, khôi phục được")

    if lam_bg:
        n = 0
        for c in cu:
            n += 1
            if that:
                db.collection("render_channels").document(c["_id"]).delete()
        print(f"\n  🧹 {'đã xoá' if that else '(sẽ xoá)'} {n} bản ghi kênh trong render_channels")
    if not that:
        print("\n  ⚠️ CHƯA LÀM GÌ CẢ — thiếu cờ --that")
    return 0


if __name__ == "__main__":
    sys.exit(main())
