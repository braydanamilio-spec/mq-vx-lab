#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BÁO TRẠNG THÁI ĐANG CHẠY — để ô "⚙️ Đang chạy" trên dashboard nói đúng.  (1/9/2026)

── VÌ SAO (anh hỏi: *"sao a thấy ⚙️ Đang chạy: 0"*) ────────────────────────────────────────
Ô ấy đếm bản ghi `render_job` trong D1 có `status` thuộc ('queued','running','writing',
'rendering','qc') và `updated_at` trong 45 phút gần nhất.

Dây chuyền giải thích **chỉ ghi bản ghi khi ĐÃ XONG** — `day_kho.py` chạy ở cuối và ghi
`status='done'`. Không có gì ghi lúc bắt đầu, nên ô "Đang chạy" bằng 0 **theo cấu trúc**, kể cả
khi 18 luồng đang dựng thật. Con số ấy không sai vì hỏng; nó sai vì không ai nói cho nó biết.

Đây cũng là ô người vận hành nhìn để biết nhà máy còn sống hay đã chết — một ô luôn bằng 0 thì
vô dụng đúng vào lúc cần nhất.

── VÌ SAO KHÔNG GHI VÀO FIRESTORE ─────────────────────────────────────────────────────────
Dashboard đọc D1 cho ô này. Ghi Firestore là ghi nhầm kho — đúng lỗi đã mắc hôm nay khi dọn.
Và D1 rẻ hơn nhiều: một lượt gọi Worker, không tốn hạn mức Firestore vốn hay cạn.

    python bao_chay.py --kenh howlong --loai short --trang_thai rendering
    python bao_chay.py --kenh howlong --loai short --trang_thai failed
"""
import argparse
import os

# Đi qua `hot_db` chứ KHÔNG tự gọi HTTP. Bản trước tôi viết đường gọi riêng và nhận 403 — không
# phải sai khoá: `hot_db.goi` ghi sẵn rằng thiếu `User-Agent` thì Cloudflare chặn ở cổng với mã
# 1010 và trả 403 y hệt sai khoá. Viết đường thứ hai là mất cả bài học lẫn cơ chế tự tắt sau
# 20 lần hỏng.


def bao(kenh: str, loai: str, trang_thai: str, buoc: str = "") -> bool:
    """Ghi/cập nhật một bản ghi job trong D1. Trả True nếu ghi được."""
    owner = os.environ.get("OWNER_UID", "")
    if not owner:
        return False
    try:
        import hot_db as H
    except Exception:
        return False
    if not H.bat_ghi():
        return False
    from datetime import datetime, timezone
    at = datetime.now(timezone.utc).isoformat()
    # ID ỔN ĐỊNH theo (kênh, loại, ngày): mỗi ngày một bản ghi cho mỗi loại, cập nhật tại chỗ.
    # `ghi_job` có ON CONFLICT DO UPDATE nên cùng id sẽ ghi đè. Không dùng id ngẫu nhiên: bảng
    # D1 chỉ tăng, và mỗi lượt render sẽ để lại ba dòng rác thay vì một.
    ma = f"gt-{kenh.lower()}-{loai}-{at[:10]}"
    # ── ĐI QUA `ghi_job()` + `xa_het()`, KHÔNG GỌI LỆNH `ghi_job` TRỰC TIẾP  (2/9/2026) ─────
    # `hot_db` KHÔNG có lệnh `ghi_job`; danh sách lệnh nó dùng chỉ có `ghi_job_loat` (một LÔ).
    # `enqueue.py` gọi thẳng tên ấy và ăn `HTTP 500`, làm mất sạch bản ghi — màn hình hiện 0 dù
    # video đã lên Drive. Tệp này gọi CÙNG một tên, nên nó mang sẵn cùng quả bom.
    #
    # Triệu chứng đo được: 2 luồng đang render thật mà ô "⚙️ Đang chạy" hiện **0**.
    #
    # `xa_het()` là thứ viết ra đúng cho tiến trình ngắn: *"Gọi cuối luồng — thiếu bước này là
    # MẤT các lượt ghi cuối."* Bộ đệm sinh ra cho tiến trình sống lâu; tệp này sống vài giây.
    H.ghi_job(owner=owner, jid=ma, channel=kenh.upper(), vtype=loai,
              status=trang_thai, step=buoc or trang_thai, queued=False, at=at)
    return bool(H.xa_het())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kenh", required=True)
    ap.add_argument("--loai", default="short", choices=["short", "long"])
    ap.add_argument("--trang_thai", default="rendering")
    ap.add_argument("--buoc", default="")
    a = ap.parse_args()
    ok = bao(a.kenh, a.loai, a.trang_thai, a.buoc)
    print(f"   {'✓' if ok else '⏭'} {a.kenh} · {a.loai} · {a.trang_thai}")
    return 0            # luôn 0: đây là báo cáo, không phải cổng


if __name__ == "__main__":
    raise SystemExit(main())
