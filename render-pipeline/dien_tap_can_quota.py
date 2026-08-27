#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DIỄN TẬP CẠN QUOTA — ép Firestore chết sạch rồi xem hệ còn chạy được không (27/8/2026).

VÌ SAO CẦN
----------
Suốt mấy ngày qua cùng một kiểu lỗi lặp lại: một chỗ nào đó trong đường chạy chính coi Firestore
là thứ CHẮC CHẮN CÓ, tới lúc cạn hạn mức thì cả phiên đứng — mà chỉ phát hiện được SAU khi đã mất
một đêm render. Vá xong lại tưởng xong, hôm sau đứng ở chỗ khác.

Đọc mã bằng mắt không bắt được loại lỗi này: `except Exception` nhìn thì có, nhưng `SystemExit`
không phải `Exception`; `read_channels` nhìn thì có đường lui, nhưng đường lui chỉ chạy khi NÉM
LỖI, còn thực tế Firestore trả về "thành công" với dữ liệu cũ.

Nên: KHÔNG ĐOÁN. Ép mọi lối vào Firestore ném 429 (và một chế độ nữa: trả về rỗng/dữ liệu cũ mà
không ném), rồi gọi thật từng hàm trong đường chạy chính. Hàm nào ném ra ngoài = một điểm chết.

    python dien_tap_can_quota.py            # cả hai kịch bản
    python dien_tap_can_quota.py --kb nem   # chỉ kịch bản ném 429
"""
from __future__ import annotations

import io
import os
import sys
import traceback

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)

OWNER = os.environ.get("MM0_OWNER") or "THU"


class Loi429(Exception):
    """Bản sao lỗi thật của google.api_core: '429 Quota exceeded.'"""
    def __init__(self):
        super().__init__("429 Quota exceeded.")


def _cam_firestore(kieu: str, FB) -> None:
    """Bịt MỌI lối ra Firestore của `firestore_bridge`.

    Bịt ở tầng thấp nhất (`_db`, `_db_meta`, `_retry`) chứ không bịt từng hàm nghiệp vụ: hàm
    nghiệp vụ có thể thêm mới bất cứ lúc nào, còn ba lối này thì mọi đường đều phải đi qua.
    """
    def _chet(*a, **k):
        raise Loi429()

    def _rong(*a, **k):
        return []

    if kieu == "nem":
        FB._db = _chet
        FB._db_meta = _chet
        FB._retry = _chet
    else:
        # KỊCH BẢN ÁC HƠN — và là cảnh ĐÃ XẢY RA THẬT ở phiên #33028251503: gương B2 trả về
        # "thành công" nhưng thiếu hết kênh gen-2.
        #
        # 27/8 — bản đầu mô phỏng sai: nó bịt `_retry` trả `[]`. Như thế thì thân hàm KHÔNG CHẠY,
        # nên mọi xử lý "đọc được nhưng không thấy gì" bị nhảy cóc — bài kiểm xanh mà thực tế vẫn
        # chết. Cảnh thật là: truy vấn CHẠY BÌNH THƯỜNG, chỉ là không ra bản ghi nào.
        # Nên mô phỏng ở đúng chỗ đó: cho mọi luồng đọc trả về danh sách rỗng, còn hàm vẫn chạy đủ.
        class _Truy:
            def __getattr__(self, _):
                return lambda *a, **k: self

            def stream(self, *a, **k):
                return iter(())

            def get(self, *a, **k):
                class _D:
                    exists = False

                    def to_dict(self):
                        return {}
                return _D()

            def set(self, *a, **k):
                return None

            def update(self, *a, **k):
                return None

        FB._db = lambda *a, **k: _Truy()
        FB._db_meta = lambda *a, **k: _Truy()
        FB._db_jobs = lambda *a, **k: _Truy()
        FB._stream_at = lambda *a, **k: iter(())
        FB._retry = lambda fn, *a, **k: fn()


# (nhãn, hàm gọi thử, thế nào là ĐẠT)
def _bai(FB) -> list:
    return [
        ("danh sách kênh", lambda: FB.read_channels(OWNER),
         lambda r: len([x for x in (r or []) if str(x.get("the_he")) == "2"]) >= 50),
        ("kho key Gemini", lambda: FB.read_keys(OWNER), lambda r: r is not None),
        ("cấu hình chung", lambda: FB.read_config(OWNER), lambda r: r is not None),
        ("đếm long đã làm", lambda: FB.count_done(OWNER, "WHATISINIT", "long"), lambda r: r is not None),
        ("đề tài gần đây", lambda: FB.recent_topics(OWNER, "WHATISINIT", 30), lambda r: r is not None),
        ("mở job mới", lambda: FB.new_job(OWNER, "WHATISINIT", "short"), lambda r: r is not None),
        ("cập nhật job", lambda: FB.update_job("dt-test", status="done"), lambda r: True),
        ("lưu đề tài", lambda: FB.save_topics(OWNER, "WHATISINIT", ["dien tap"]), lambda r: True),
        ("việc dở dang", lambda: FB.find_resumable(OWNER, "WHATISINIT", "short"), lambda r: True),
        ("yêu cầu render", lambda: FB.read_render_requests(OWNER), lambda r: r is not None),
        ("dung lượng kho", lambda: FB.drive_usage(OWNER), lambda r: True),
        ("báo key sống", lambda: FB.mark_key_alive(OWNER, "k-test"), lambda r: True),
        ("một kênh cụ thể", lambda: FB.read_one_channel(OWNER, "WHATISINIT"), lambda r: True),
    ]


def chay(kieu: str) -> int:
    import importlib
    for m in ("firestore_bridge",):
        if m in sys.modules:
            del sys.modules[m]
    FB = importlib.import_module("firestore_bridge")
    FB._HOT_CACHE.clear()
    _cam_firestore(kieu, FB)

    ten = "NÉM 429" if kieu == "nem" else "TRẢ VỀ RỖNG (không ném — cảnh gương B2)"
    print(f"\n{'═' * 78}\n  KỊCH BẢN: Firestore {ten}\n{'═' * 78}")
    chet = []
    for nhan, goi, dat in _bai(FB):
        try:
            r = goi()
            ok = bool(dat(r))
            mo = f"{len(r)} mục" if isinstance(r, (list, tuple)) else ("có" if r is not None else "None")
            print(f"  {'✅' if ok else '🟡'} {nhan:20} -> {mo}" + ("" if ok else "  ← chạy tiếp được nhưng THIẾU dữ liệu"))
            if not ok:
                chet.append((nhan, "thiếu dữ liệu"))
        except BaseException as e:
            print(f"  ❌ {nhan:20} -> NÉM RA NGOÀI: {type(e).__name__}: {str(e)[:60]}")
            chet.append((nhan, f"{type(e).__name__}: {str(e)[:60]}"))
            if os.environ.get("DT_VET"):
                traceback.print_exc()
    return len(chet), chet


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", default="", help="nem | rong (mặc định: cả hai)")
    a = ap.parse_args()
    kbs = [a.kb] if a.kb else ["nem", "rong"]
    tong = []
    for kb in kbs:
        n, ds = chay(kb)
        tong += [(kb, x, y) for x, y in ds]
    print(f"\n{'═' * 78}")
    if not tong:
        print("  ✅ KHÔNG CÓ ĐIỂM CHẾT — Firestore cạn sạch, đường chạy chính vẫn đi tiếp.")
        return 0
    print(f"  🚨 {len(tong)} ĐIỂM CHẾT — cạn quota là hệ đứng ở đây:")
    for kb, nhan, ly in tong:
        print(f"     [{kb}] {nhan}: {ly}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
