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
import json
import os
import urllib.request

WORKER = "https://mm0-connect.adisondurham-ef1.workers.dev/api/hot"


def bao(kenh: str, loai: str, trang_thai: str, buoc: str = "") -> bool:
    """Ghi/cập nhật một bản ghi job trong D1. Trả True nếu ghi được."""
    khoa = os.environ.get("HOT_KEY", "")
    owner = os.environ.get("OWNER_UID", "")
    if not khoa or not owner:
        return False
    from datetime import datetime, timezone
    at = datetime.now(timezone.utc).isoformat()
    # ID ỔN ĐỊNH theo (kênh, loại, ngày): mỗi ngày một bản ghi cho mỗi loại, cập nhật tại chỗ
    # thay vì đẻ thêm dòng mỗi lần đổi trạng thái. `ghi_job` có ON CONFLICT DO UPDATE nên cùng
    # id sẽ ghi đè. Không dùng id ngẫu nhiên: bảng D1 chỉ tăng, và mỗi lượt render sẽ để lại
    # bốn dòng rác thay vì một.
    ma = f"gt-{kenh.lower()}-{loai}-{at[:10]}"
    goi = {"lenh": "ghi_job", "tham": {
        "id": ma, "owner": owner, "channel": kenh.upper(), "vtype": loai,
        "status": trang_thai, "step": buoc or trang_thai, "queued": False, "at": at}}
    try:
        r = urllib.request.Request(
            WORKER, method="POST", data=json.dumps(goi).encode(),
            headers={"content-type": "application/json", "x-hot-key": khoa})
        with urllib.request.urlopen(r, timeout=30) as f:
            json.loads(f.read().decode())
        return True
    except Exception as e:
        # KHÔNG để việc báo cáo làm hỏng lượt render. Ô trạng thái sai thì khó chịu; mất một
        # lượt dựng vì không gọi được Worker thì tốn thật.
        print(f"   ⚠ không báo được trạng thái: {str(e)[:80]}")
        return False


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
