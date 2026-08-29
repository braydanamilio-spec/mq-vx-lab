#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DỌN VIDEO TRÙNG TIÊU ĐỀ — giữ bản mới nhất, chặn phần còn lại khỏi được đăng (28/8/2026).

VÌ SAO
------
Đo phiên 28/8: 600 video ra lò, **334 trùng tiêu đề**. Nguyên nhân đã vá ở gốc (`hoan_tieu_de`
vứt mất hậu tố trục, xem `cham_kenh.py`), nhưng video ĐÃ RENDER thì bản vá không đụng tới — chúng
vẫn nằm trong hàng đợi và vẫn sẽ được đăng.

Và đăng mới là chỗ ĐẮT. Một bản trùng nằm trong kho chỉ tốn vài chục MB; một bản trùng lên kênh thì
trang kênh thành cột chữ lặp, và YouTube xếp đúng khuôn "nội dung lặp lại, sản xuất hàng loạt" bị
hạn chế phân phối — thiệt hại rơi vào CẢ những video tốt của kênh đó.
Nên việc gấp không phải xoá tệp, mà là CHẶN chúng khỏi hàng đăng.

CÁCH LÀM
--------
Gom job `done` theo (kênh, tiêu đề đã chuẩn hoá). Nhóm nào có hơn một bản thì giữ bản MỚI NHẤT,
các bản còn lại chuyển `status` sang `trung` và hạ cờ `queued` — hàng đăng chỉ lấy `queued == False`
và `status == done`, nên đổi hai trường đó là chúng biến khỏi đường đăng, mà TỆP VẪN CÒN NGUYÊN
trên Drive để còn xem lại hay khôi phục.

MẶC ĐỊNH CHỈ ĐẾM. `--that` mới ghi.

    python don_trung_tieu_de.py                # chỉ đếm, in ra nhóm trùng
    python don_trung_tieu_de.py --that
"""
from __future__ import annotations

import os
import re
import sys
from collections import defaultdict

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)

# Sàn an toàn: đọc được ít hơn bấy nhiêu job thì gần như chắc chắn là đọc HỤT, không phải kho vắng.
# Một lượt đọc hụt mà vẫn chạy tiếp thì mọi bản đều trông như "duy nhất" hoặc "trùng" tuỳ hướng —
# và ở đây hướng sai sẽ đánh dấu nhầm hàng loạt video tốt.
SAN_AN_TOAN = 30

# ── MỐC ENGINE ĐẠT CHUẨN (29/8/2026) ───────────────────────────────────────────────────────
# Anh: "loại videos chuẩn chất lượng mới nha, ko template videos nhàm chán nền neon nha".
# Nền neon chỉ được sửa ở commit f875fba (28/8 16:42Z), và ba lỗi nặng còn lại — .XXX lọt cổng an
# toàn, đồng hồ in mã ngày thô "20260741", nhãn tĩnh nói sai nội dung ("Breakfast cereal" mà dữ
# liệu là kem) — sửa xong ở 8e28c96 (28/8 17:44Z).
# Nên MỌI video dựng trước 17:44Z ngày 28/8 đều mang ít nhất một trong số đó. Không phải "có thể
# mang": engine lúc ấy KHÔNG THỂ dựng khác đi.
#
# KHÔNG XOÁ TỆP. Chỉ đổi trạng thái để chúng ra khỏi hàng đăng — kho Drive giữ nguyên, và muốn
# phục hồi thì chỉ là một lượt ghi ngược lại. Xoá tệp là việc một chiều; ở đây không cần một chiều.
MOC_ENGINE = "2026-08-28T17:44:00Z"


def _chuan(t: str) -> str:
    """Chuẩn hoá tiêu đề để so: bỏ dấu câu và khoảng trắng thừa, hạ chữ thường.

    Cùng luật với `_tieu_de_da_lam` để hai nơi không kết luận khác nhau về cùng một cặp tiêu đề —
    đúng loại lệch đã gây ra chuỗi lỗi tuần này."""
    return re.sub(r"[^a-z0-9]+", " ", str(t or "").lower()).strip()


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--that", action="store_true", help="ghi thật (mặc định chỉ đếm)")
    ap.add_argument("--owner", default=os.environ.get("OWNER_UID") or os.environ.get("RENDER_OWNER") or "")
    ap.add_argument("--tran", type=int, default=800, help="trần số bản đánh dấu mỗi lượt")
    ap.add_argument("--moc-engine", default=MOC_ENGINE,
                    help="video dựng TRƯỚC mốc này là engine cũ (ISO-8601 UTC)")
    a = ap.parse_args()
    if not a.owner:
        print("❌ thiếu OWNER_UID")
        return 2

    import firestore_bridge as FB
    # `_db_jobs()` NÉM KeyError khi thiếu biến môi trường creds, không trả None. Bắt cả hai đường:
    # đo thật ở máy không có creds thì nó ném ra một vệt traceback dài, và người đọc log sẽ tưởng
    # công cụ hỏng chứ không phải môi trường thiếu khoá.
    try:
        db = FB._db_jobs()
    except Exception as e:
        db = None
        print(f"   (không mở được project B: {type(e).__name__} {str(e)[:50]})")
    if db is None:
        print("❌ không có creds project B — công cụ này phải chạy trên CI, nơi có khoá")
        return 3

    nhom = defaultdict(list)
    tong = 0
    for d in FB._stream_at(db.collection("render_jobs").where("owner", "==", a.owner), 180):
        x = d.to_dict() or {}
        if str(x.get("status") or "") != "done":
            continue
        tong += 1
        t = _chuan(x.get("title"))
        if not t:
            continue
        nhom[(str(x.get("channel") or "").upper(), t)].append(
            (str(x.get("updated_at") or ""), d.id, x.get("drive_id"), str(x.get("title") or "")))

    if tong < SAN_AN_TOAN:
        print(f"   🛑 chỉ đọc được {tong} job 'done' — dưới sàn an toàn {SAN_AN_TOAN}. "
              f"Nhiều khả năng đọc hụt chứ không phải kho vắng; TỪ CHỐI đánh dấu.")
        return 4

    # ── LƯỢT 2: VIDEO DỰNG BẰNG ENGINE CŨ ──────────────────────────────────────────────────
    # SO THỜI GIAN THẬT, KHÔNG SO CHUỖI. `update_job` ghi `updated_at` bằng
    # `datetime.now(timezone.utc).isoformat()` -> "2026-08-28T17:44:00.123456+00:00", còn mốc
    # viết tay kết thúc bằng "Z". So chuỗi thì tại vị trí đó gặp "." với "Z", mà "." < "Z" nên
    # MỌI video đều bị coi là cũ — và lượt dọn sẽ quét sạch cả những bản vừa render đúng chuẩn.
    # Đúng họ lỗi "hai bên dùng khuôn khác nhau" đã gây ra chuỗi hỏng cả tuần; ở đây cái giá là
    # cả thư viện ra khỏi hàng đăng.
    import datetime as _dt

    import re as _re2

    def _luc(x):
        """Đọc mốc thời gian ISO, chịu được mọi biến thể mà nguồn thật sinh ra.

        Bỏ PHẦN LẺ GIÂY trước khi đọc: `fromisoformat` của Python 3.9 chỉ nhận đúng 3 hoặc 6 chữ
        số lẻ, mà `datetime.isoformat()` cắt số 0 ở cuối nên "…:00.9+00:00" là chuyện thường. Đo
        thật: bản 1 chữ số bị ném lỗi rồi rơi vào nhánh "không đọc được" — tức im lặng bỏ sót đúng
        những video mới nhất. Lẻ giây không có nghĩa gì với một cái mốc tính theo ngày."""
        t = str(x or "").strip().replace("Z", "+00:00")
        t = _re2.sub(r"\.\d+", "", t)
        try:
            d = _dt.datetime.fromisoformat(t)
        except Exception:
            return None
        return d if d.tzinfo else d.replace(tzinfo=_dt.timezone.utc)

    moc = _luc(a.moc_engine)
    cu_engine = []
    khong_ro = 0
    for (ch, _t), ds in nhom.items():
        for u, jid, _dr, ten in ds:
            t = _luc(u)
            if t is None:
                khong_ro += 1        # không đọc được mốc -> KHÔNG đụng, thà bỏ sót còn hơn quét oan
                continue
            if moc and t < moc:
                cu_engine.append((jid, ch, ten))

    thua = []
    theo_kenh = defaultdict(int)
    for (ch, _t), ds in nhom.items():
        if len(ds) < 2:
            continue
        ds.sort(reverse=True)                 # mới nhất lên đầu -> giữ ds[0]
        for _u, jid, _dr, ten in ds[1:]:
            thua.append((jid, ch, ten))
            theo_kenh[ch] += 1

    print(f"\n  📊 {tong} job 'done' · {len(nhom)} tiêu đề khác nhau · "
          f"{len(thua)} bản TRÙNG (giữ bản mới nhất mỗi nhóm)")
    for ch, n in sorted(theo_kenh.items(), key=lambda z: -z[1])[:14]:
        print(f"     {ch:22} {n:>4} bản trùng")
    for jid, ch, ten in thua[:8]:
        print(f"     └ {ch}: {ten[:60]}")

    print(f"\n  🎬 {len(cu_engine)} video dựng bằng ENGINE CŨ (trước {a.moc_engine}) — "
          f"nền neon, chưa có các bản vá nội dung. Đưa ra khỏi hàng đăng."
          + (f"  ({khong_ro} bản không đọc được mốc thời gian — KHÔNG đụng)" if khong_ro else ""))

    if not a.that:
        print("\n  ℹ️ CHỈ ĐẾM. Thêm `--that` để đánh dấu. Tệp trên Drive KHÔNG bị đụng trong cả hai chế độ.")
        return 0
    if not (thua or cu_engine):
        return 0

    def _danh_dau(ds, nhan, tran):
        xong = 0
        ds = ds[:tran]
        for i in range(0, len(ds), 400):
            b = db.batch()
            for jid, _ch, _ten in ds[i:i + 400]:
                b.update(db.collection("render_jobs").document(jid),
                         {"status": nhan, "queued": True})
            b.commit()
            xong += len(ds[i:i + 400])
            print(f"     … {nhan}: {xong}/{len(ds)}", flush=True)
        return xong

    n1 = _danh_dau(thua, "trung", a.tran)
    # Trần riêng và rộng hơn cho lượt engine cũ: đây là một đợt dọn MỘT LẦN cho cả thư viện,
    # không phải việc lặp hằng ngày như dọn trùng.
    n2 = _danh_dau([x for x in cu_engine if x[0] not in {y[0] for y in thua[:a.tran]}],
                   "engine_cu", 4000)
    print(f"  ✅ {n1} bản trùng + {n2} bản engine cũ đã ra khỏi hàng đăng. "
          f"Tệp vẫn nguyên trên Drive, phục hồi chỉ là một lượt ghi ngược.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
