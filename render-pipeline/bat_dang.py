#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BẬT ĐĂNG TỰ ĐỘNG CHO 18 KÊNH — ghi cấu hình vào D1, không đụng Firestore.  (2/9/2026)

Anh: *"cứ setup tự động đầy đủ, sau gắn channel vô là nó tự động ăn khớp, chọn lịch là đăng
được"* và *"đừng có 1 phương án firebase trong khi suốt ngày cạn"*.

── VÌ SAO GHI D1 CHỨ KHÔNG GHI FIRESTORE ───────────────────────────────────────────────────
Cờ `auto_publish` quyết định cả dây chuyền đăng có chạy hay không. Trước đây nó CHỈ nằm ở
Firestore, nên hôm Firestore cạn (đã xảy ra hai ngày liền) thì `auto_enqueue` đọc rỗng, thoát
ngay, và không đăng gì mà cũng không báo gì. `auto_enqueue._cau_hinh_d1` nay đọc D1 TRƯỚC.

── VÌ SAO BẬT TRƯỚC KHI NỐI KÊNH LÀ AN TOÀN ────────────────────────────────────────────────
`auto_enqueue` có chốt cứng thứ hai: kênh phải có `connections/<owner>__<kênh>__youtube` với
`refresh_token`. Chưa nối thì nó bỏ qua kênh ấy và IN RA lý do. Nên bật cờ sẵn không làm đăng
nhầm cái gì — nó chỉ khiến kênh "sẵn sàng", và đúng lúc anh nối xong là chạy ngay, không phải
quay lại bật thêm thứ gì.

── LỊCH ────────────────────────────────────────────────────────────────────────────────────
Mỗi kênh gán một template trong `posting_templates.yaml` (mix short/long mỗi ngày + giờ vàng
US). Không gán thì `auto_enqueue` rơi về `balanced_1long_3short` — vẫn chạy, nhưng gán rõ thì
anh đổi lịch chỉ bằng cách đổi tên template ở đây.

    python bat_dang.py              # xem sẽ ghi gì
    python bat_dang.py --that       # ghi thật vào D1
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

GOC = os.path.dirname(os.path.abspath(__file__))
D1_KEY = "pub_overrides"

# Template mặc định cho bộ giải thích: 1 bản dài + 3 short mỗi ngày, giờ vàng US.
# Kênh nào muốn nhịp khác thì đổi ở đây — `auto_enqueue` đọc thẳng bảng này.
TEMPLATE_MAC_DINH = "balanced_1long_3short"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--that", action="store_true", help="ghi thật (mặc định chỉ in ra)")
    ap.add_argument("--template", default=TEMPLATE_MAC_DINH)
    a = ap.parse_args()

    sys.path.insert(0, GOC)
    import giai_thich as G
    import hot_db as H

    ma = [k["ma"].upper() for k in G.KENH]
    ov = {
        "auto_publish": {m: True for m in ma},
        "channels": {m: a.template for m in ma},
        "nguon": "bat_dang.py",
        "luc": datetime.now(timezone.utc).isoformat(),
    }
    print(f"  bật đăng tự động cho {len(ma)} kênh · template `{a.template}`")
    print(f"  {', '.join(ma[:6])} …")
    print("  ⚠ chốt an toàn giữ nguyên: kênh CHƯA nối YouTube thì `auto_enqueue` bỏ qua và in lý do.")

    if not a.that:
        print("\n  (chạy thử — thêm --that để ghi vào D1)")
        return 0
    if not H.bat_ghi():
        print("  ❌ thiếu HOT_KEY — không ghi được vào D1")
        return 1
    r = H.goi("nho_ghi", {"k": D1_KEY, "js": json.dumps(ov, ensure_ascii=False),
                          "at": ov["luc"]})
    if not r:
        print("  ❌ ghi D1 hụt")
        return 1
    # ĐỌC LẠI ĐỂ CHẮC — ghi mà không đọc lại thì không biết nó có vào thật không.
    d = H.goi("nho_doc", {"k": D1_KEY}) or {}
    n = len(json.loads(d.get("js") or "{}").get("auto_publish") or {})
    print(f"  ✅ đã ghi và đọc lại: {n}/{len(ma)} kênh bật trong D1")
    return 0 if n == len(ma) else 1


if __name__ == "__main__":
    raise SystemExit(main())
