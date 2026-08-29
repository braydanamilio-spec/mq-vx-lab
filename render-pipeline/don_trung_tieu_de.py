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
# 29/8 10:30Z — NÂNG MỐC CHO CẢ 50 KÊNH. Trước đó mốc chung đứng ở 28/8 17:44Z và tôi cố ý
# KHÔNG nâng nó, chỉ đặt mốc riêng cho 15 kênh đổi nội dung — vì nâng mốc chung sẽ gạt oan hàng
# nghìn video đúng chuẩn của những kênh không dính lỗi nào.
# Lý lẽ ấy hết đúng sau loạt vá hôm nay, vì bốn bản vá này chạm MỌI kênh:
#   • bỏ dấu @handle in đè trên khung (22 chỗ, mọi composition video);
#   • nâng 13 nền cứng quá tối — đo được: sáng trung bình 44 -> 82, điểm gần đen 65% -> 1,5%;
#   • hook: mọi lối ra đều đi qua bộ cắt câu, và kênh không có số thì mở bằng câu hỏi;
#   • bỏ chữ bịa trong ảnh AI (thêm 3 nhóm danh từ đo từ khung thật).
# Nên mọi video dựng trước 10:30Z hôm nay đều mang ít nhất một trong bốn. Không phải "có thể
# mang" — engine lúc ấy KHÔNG THỂ dựng khác đi.
#
# CÁI GIÁ, nói thẳng: kho đang có ~3.900 video và gần hết sẽ ra khỏi hàng đăng cùng lúc. Xưởng
# render ra ~700 video/ngày nên hàng đăng đầy lại trong khoảng một ngày. Và đây là phép đảo ngược
# được bằng đúng một lượt ghi — tệp trên Drive không bị đụng.
MOC_ENGINE = "2026-08-29T10:30:00Z"

# ── MỐC RIÊNG TỪNG KÊNH (29/8/2026) ────────────────────────────────────────────────────────
# 12 kênh vừa được sửa vì NHÃN THƯƠNG HIỆU HỨA MỘT ĐẰNG, NỘI DUNG MỘT NẺO — thứ nặng hơn xấu:
# REAL PLACE ("nơi có thật") ra phim "Muppet Treasure Island"; ONE HIT ra các ban tên "Viral";
# SALARY TRUTH ("nghề này trả bao nhiêu") vẽ tổng số việc làm. Bản vá nằm ở commit fd167c0.
#
# VÌ SAO KHÔNG NÂNG THẲNG `MOC_ENGINE` LÊN 29/8. Mốc chung áp cho CẢ 50 kênh, mà 38 kênh còn lại
# không dính lỗi nào trong số đó — nâng mốc chung là gạt hàng nghìn video ĐÚNG CHUẨN ra khỏi hàng
# đăng để dọn cho 12 kênh. Cái giá sai lệch hẳn về một phía.
# Mốc riêng thì mỗi kênh bị loại đúng vì lỗi CỦA CHÍNH NÓ.
MOC_THEO_KENH = {ten: "2026-08-29T08:53:00Z" for ten in (
    "ONE HIT", "SONG FILE", "REAL PLACE", "UNSOLVED LOG", "SALARY TRUTH", "JOB DYING",
    "GAME GRAVEYARD", "DEGREE WORTH", "HOUSE MATH", "PAID VS PLAYED", "WEAPON PRICE",
    "YOUR RIGHTS CASE", "COLD FILE", "MARRIAGE MATH", "NIGHT SHIFT")}


def _chuan(t: str) -> str:
    """Chuẩn hoá tiêu đề để so: bỏ dấu câu và khoảng trắng thừa, hạ chữ thường.

    Cùng luật với `_tieu_de_da_lam` để hai nơi không kết luận khác nhau về cùng một cặp tiêu đề —
    đúng loại lệch đã gây ra chuỗi lỗi tuần này."""
    return re.sub(r"[^a-z0-9]+", " ", str(t or "").lower()).strip()


def _danh_dau_d1(owner: str, moc: str, lo_toi_da: int = 40) -> int:
    """Đánh dấu video engine cũ TRONG D1 — nơi thật sự chứa gần hết thư viện.

    29/8 — VÌ SAO THIẾU BƯỚC NÀY LÀ CẢ LƯỢT DỌN GẦN NHƯ VÔ NGHĨA.
    Anh: "a thấy 1 đống videos cũ lỗi sao ko dọn đi". Đo trên nhật ký lượt dọn vừa chạy: công cụ
    này đọc được **561** job 'done' trong Firestore, trong khi bảng điều khiển đếm **3.901** video
    trong kho. Chênh lệch không phải sai số — Firestore chỉ còn phần đuôi, còn thân kho nằm ở D1
    (pipeline ghi thẳng vào đó, và `don_job_cu` tỉa Firestore theo ngày).
    Nên đánh dấu một bên là dọn ~14% thư viện rồi báo "xong".
    Tệ hơn: thư viện trên bảng, KHI CÓ LỌC NGÀY, đọc thẳng từ D1 và còn gán cứng `status:"done"`
    cho mọi dòng lấy về. Video đã bị gạt ở Firestore vẫn hiện nguyên vẹn ngay khi bấm "Hôm nay" —
    đúng cảnh "dọn một nơi, hai kho song song" đã được ghi trong worker.js.

    Cách làm không cần deploy Worker: `job_cuaso` trả về tối đa 400 dòng `done` trong một khoảng
    thời gian, `ghi_job` thì upsert được trạng thái. Đánh dấu xong thì dòng ấy không còn `done`
    nên lượt gọi sau không trả nó về nữa — vòng lặp tự cạn, không cần phân trang.
    """
    try:
        import hot_db as H
    except Exception as e:
        print(f"  ⚠️ không nạp được hot_db ({str(e)[:50]}) — bỏ phần D1")
        return 0
    if not (H.bat_doc() and H.bat_ghi()):
        print("  ⚠️ D1 đang TẮT (thiếu HOT_KEY/HOT_MODE) — bỏ phần D1")
        return 0
    import datetime as _dt
    luc = _dt.datetime.now(_dt.timezone.utc).isoformat()
    xong = 0
    for _ in range(lo_toi_da):
        rows = H.job_cuaso(owner, "", moc)
        if not rows:
            break
        for r in rows:
            H.ghi_job(owner, r.get("id"), r.get("channel") or "", r.get("vtype") or "",
                      "engine_cu", step="dựng bằng engine cũ — không đăng",
                      queued=True, at=luc)
        # PHẢI XẢ BỘ ĐỆM MỖI LÔ. `ghi_job` gom vào đệm rồi mới gửi; không xả thì lượt
        # `job_cuaso` kế tiếp vẫn thấy đúng 400 dòng ấy còn `done` và vòng lặp quay tại chỗ.
        H.xa_het()
        xong += len(rows)
        print(f"     … D1: {xong} bản", flush=True)
        if len(rows) < 400:
            break
    return xong


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
    # 29/8 — CHUẨN HOÁ KHOÁ KÊNH TRƯỚC KHI SO. Bản đầu của bảng này viết tên có dấu cách
    # ("GAME GRAVEYARD") còn sổ job ghi tên VIẾT LIỀN ("GAMEGRAVEYARD"), nên phép tra khớp
    # KHÔNG BAO GIỜ trúng và cả lớp mốc-riêng chạy như không có. Không một dòng lỗi nào: nó chỉ
    # lặng lẽ dọn 0 video rồi báo thành công.
    # Đúng họ lỗi "hai bên dùng khuôn khoá khác nhau" đã gây hỏng suốt tuần. Ở đây cái giá là
    # video sai nhãn vẫn nằm nguyên trong hàng đăng trong khi bảng báo đã dọn xong.
    _kk = lambda t: str(t or "").replace(" ", "").upper()
    moc_kenh = {_kk(k): _luc(v) for k, v in MOC_THEO_KENH.items()}
    cu_engine = []
    khong_ro = 0
    rieng = defaultdict(int)
    for (ch, _t), ds in nhom.items():
        # Kênh có mốc riêng thì DÙNG MỐC RIÊNG, không phải mốc muộn hơn trong hai cái: mốc riêng
        # bao giờ cũng muộn hơn mốc chung (nó vá thêm lỗi trên nền bản vá chung), nên lấy nó là
        # đã bao trọn cả hai đời lỗi.
        m = moc_kenh.get(_kk(ch)) or moc
        for u, jid, _dr, ten in ds:
            t = _luc(u)
            if t is None:
                khong_ro += 1        # không đọc được mốc -> KHÔNG đụng, thà bỏ sót còn hơn quét oan
                continue
            if m and t < m:
                cu_engine.append((jid, ch, ten))
                if _kk(ch) in moc_kenh:
                    rieng[ch] += 1

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

    # KHÔNG ĐƯỢC IM LẶNG KHI KHỚP 0. Một bảng mốc khai 15 kênh mà không chạm được kênh nào thì
    # gần như chắc chắn là sai khoá, không phải "15 kênh ấy sạch cả". Nói ra ngay tại chỗ.
    _co_kenh = {_kk(ch) for (ch, _t) in nhom}
    _hut = sorted(k for k in moc_kenh if k not in _co_kenh)
    if _hut:
        print(f"\n  ⚠️ {len(_hut)}/{len(moc_kenh)} kênh trong bảng MỐC RIÊNG không khớp tên nào "
              f"trong sổ job: {', '.join(_hut[:6])} — kiểm lại khuôn khoá tên kênh.")
    if rieng:
        print(f"\n  🏷️ {sum(rieng.values())} video thuộc {len(rieng)} kênh có MỐC RIÊNG "
              f"(nhãn hứa sai nội dung, vá ở fd167c0):")
        for ch, n in sorted(rieng.items(), key=lambda z: -z[1]):
            print(f"     {ch:22} {n:>4} bản")
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
    print(f"  ✅ {n1} bản trùng + {n2} bản engine cũ đã ra khỏi hàng đăng (sổ Firestore). "
          f"Tệp vẫn nguyên trên Drive, phục hồi chỉ là một lượt ghi ngược.")
    n3 = _danh_dau_d1(a.owner, a.moc_engine)
    print(f"  ✅ D1: {n3} bản engine cũ đã ra khỏi hàng đăng.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
