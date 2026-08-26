#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ĐĂNG KÝ 50 KÊNH THẾ HỆ 2 vào render_channels (26/8/2026).

MẶC ĐỊNH LÀ DRY-RUN. Phải `--that` mới ghi thật — đăng ký kênh là thứ 18 lane sẽ đọc và bắt đầu
render ngay phiên sau, nên không để lỡ tay.

Kênh mới vào ở trạng thái TẮT (`paused: True`) trừ khi `--bat`: bật 50 kênh trong khi 55 kênh cũ
còn đang chạy là 105 kênh chen nhau trên 18 lane, không kênh nào ra hồn.

    python seed_the_he_2.py                 # xem sẽ tạo gì
    python seed_the_he_2.py --that          # tạo, để TẮT
    python seed_the_he_2.py --that --bat    # tạo và bật
"""
from __future__ import annotations

import io
import json
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(GOC, "kenh_the_he_2.json")
# Khoá THỪA HƯỞNG từ một kênh mẫu đang chạy (hạn mức kho, bậc chất lượng...).
# 26/8 — BẢN ĐẦU CÓ CẢ "long_target", "n_shorts", "make_long" TRONG DANH SÁCH NÀY, mà ba khoá đó
# lại được đặt TƯỜNG MINH ngay phía trên `**dich` trong `doc`. Python lấy giá trị SAU, nên `**dich`
# âm thầm đè cả ba: 50 kênh gen-2 (thiết kế là SHORT, 3 clip, không làm long) sẽ ra đời với chỉ tiêu
# long của kênh cũ. Không lỗi, không log — chỉ vài tiếng sau ra một loạt video sai định dạng.
# Nay: khoá nào seed cố ý quyết thì KHÔNG thừa hưởng, và phần cố ý được đặt SAU `**dich`.
TARGET = ["short_target", "tier", "cap_gb"]


# ── CHỮ KÝ GIỌNG RIÊNG TỪNG KÊNH (26/8/2026) ──────────────────────────────────────────────────
# Đo trước khi seed: 50 kênh gen-2 KHÔNG có trường `voice`, mà `run_one` gọi
# `set_voice(ch.get("voice"), ...)` -> None -> rơi về `DEFAULT_VOICE`. Tức cả 50 kênh sẽ đọc bằng
# ĐÚNG MỘT giọng. Chính chú thích trong `tts_karaoke.set_voice` đã cảnh báo chuyện này cho đời 1:
# "40 kênh chung 1 giọng + 21 kênh chung 1 engine -> đúng thứ chính sách inauthentic/mass-produced
# của YouTube nhắm tới". Để nguyên là lặp lại y nguyên cái bẫy đó ở quy mô 50.
#
# 12 giọng en-US khác NGƯỜI (bỏ bản Multilingual vì trùng nhân vật, bỏ Ana vì giọng trẻ em không
# hợp các chủ đề toà án/quốc phòng/tài chính), nhân với tốc độ và cao độ -> 108 chữ ký. 50 kênh
# lấy 50 chữ ký khác nhau, không cặp nào trùng.
GIONG = ["en-US-AndrewNeural", "en-US-BrianNeural", "en-US-ChristopherNeural", "en-US-EricNeural",
         "en-US-GuyNeural", "en-US-RogerNeural", "en-US-SteffanNeural",
         "en-US-AriaNeural", "en-US-AvaNeural", "en-US-EmmaNeural", "en-US-JennyNeural",
         "en-US-MichelleNeural"]
# 26/8 — NỚI RỘNG THÊM. Anh: "khán giả xem không được biết 50 kênh cùng một người làm".
# 12 giọng cho 50 kênh nghĩa là ~4 kênh chung một NGƯỜI đọc; chỉ khác tốc/cao độ ở 3 mức thì hai
# kênh chung giọng vẫn nghe ra là một. Nới lên 5 mức mỗi chiều (12x5x5 = 300 chữ ký) và xếp sao
# cho các kênh chung giọng rơi vào tốc + cao độ CÁCH XA nhau nhất.
TOC = ["+0%", "+8%", "-6%", "+15%", "+4%"]          # kể nhanh/chậm đổi hẳn cảm giác kênh
CAO = ["+0Hz", "-14Hz", "+12Hz", "-7Hz", "+20Hz"]   # cao độ: đòn bẩy mạnh nhất để tách chất giọng


def chu_ky_giong(i: int) -> dict:
    """Chữ ký giọng thứ `i`. Xếp sao cho hai kênh LIỀN NHAU luôn khác GIỌNG (không chỉ khác tốc độ)
    — người xem lướt hai kênh cạnh nhau phải nghe ra ngay là hai kênh khác nhau."""
    g = GIONG[i % len(GIONG)]
    k = i // len(GIONG)                       # lần thứ mấy giọng này được dùng lại
    # Bước 2 và 3 là số NGUYÊN TỐ CÙNG NHAU với 5, nên mỗi lần dùng lại một giọng thì cả tốc lẫn
    # cao độ đều nhảy sang mức xa, không chỉ nhích một nấc.
    return {"voice": g, "voice_rate": TOC[(k * 2) % len(TOC)], "voice_pitch": CAO[(k * 3) % len(CAO)]}


def _db():
    """Client Firestore CÓ ĐƯỜNG LẬT B2 — dùng chung với dây chuyền chính.

    26/8 — bản đầu tự dựng client trỏ thẳng project B và chết ngay lần chạy đầu:
    `RESOURCE_EXHAUSTED: Quota exceeded.` vì B đang cạn hạn mức ngày (cờ nghỉ tới 06:59Z).
    Nghịch lý: đúng lúc hệ cạn quota là lúc cần thao tác quản trị nhất (tắt kênh, dọn kho), mà
    công cụ quản trị lại là thứ chết đầu tiên. `firestore_bridge._db_meta()` đã có sẵn failover
    sang gương B2 — dùng lại, đừng dựng client riêng."""
    import firestore_bridge as _FB
    return _FB._db_meta()


def main() -> int:
    that = "--that" in sys.argv
    bat = "--bat" in sys.argv
    # 26/8 — CHẾ ĐỘ CẬP NHẬT. Seed bỏ qua kênh đã có (đúng, để chạy lại không đè mất chỉnh tay).
    # Nhưng khi bảng giọng/phông/nền được nới thêm SAU lúc seed, 50 kênh vẫn giữ chữ ký cũ mà
    # không có đường nào sửa — đúng ca vừa gặp: seed chạy trước commit nới bảng giọng.
    # `--capnhat` ghi lại ĐÚNG các trường sinh ra từ bảng, KHÔNG đụng `paused` (trạng thái bật/tắt
    # là quyết định của người, không phải của bảng).
    capnhat = "--capnhat" in sys.argv
    ks = json.load(io.open(DS, encoding="utf-8"))
    if not that:
        print(f"🔍 DRY-RUN — sẽ đăng ký {len(ks)} kênh, trạng thái "
              f"{'BẬT' if bat else 'TẮT (chờ bật tay)'}\n")
        for k in ks:
            b = k.get("brand") or {}
            print(f"  ➕ {k['ten']:18} {k['handle']:20} {k['dinh_dang']:9} "
                  f"{(b.get('palette') or {}).get('primary', '-'):8} {k['niche'][:22]}")
        print(f"\n(chưa ghi gì cả. Thêm --that để ghi thật)")
        return 0
    db = _db()
    hien = list(db.collection("render_channels").stream())
    if not hien:
        sys.exit("❌ render_channels rỗng — không lấy được mẫu cấu hình.")
    mau = [d.to_dict() or {} for d in hien]
    owner = os.environ.get("OWNER_UID") or next((t.get("owner") for t in mau if t.get("owner")), "")
    if not owner:
        sys.exit("❌ Không có owner. Đặt OWNER_UID.")
    co = {(t.get("name") or "") for t in mau}
    # Chỉ số theo TÊN ĐÃ SẮP, không theo thứ tự trong file: thêm kênh mới vào JSON sau này cũng
    # không làm xáo giọng của các kênh đã chạy (kênh đổi giọng giữa chừng là hỏng nhận diện).
    thu_tu = {t: i for i, t in enumerate(sorted(k["ten"].replace(" ", "") for k in ks))}
    dich = {k: mau[0].get(k) for k in TARGET if mau[0].get(k) is not None}
    tao = bo = 0
    for k in ks:
        ten = k["ten"].replace(" ", "")
        if ten in co and not capnhat:
            print(f"  ⏭  {ten:18} đã có -> bỏ qua"); bo += 1; continue
        b = k.get("brand") or {}
        pal = b.get("palette") or {}
        doc = {"owner": owner, "name": ten,
               **dich,          # thừa hưởng trước...
               # ...rồi phần CỐ Ý của gen-2 ghi đè lên. Thứ tự này là điều kiện đúng, không phải
               # thẩm mỹ: đảo lại là 50 kênh nhận nhầm chỉ tiêu long của kênh mẫu.
               "the_he": 2, "paused": not bat,
               # 26/8 — TỈ LỆ 1 LONG : 3 SHORT (luật anh nêu nhiều lần).
               # Bản đầu đặt `make_long: False · long_target: 0` = short-only, ngược hẳn yêu cầu:
               # `run_one` thấy long_target 0 nên không bao giờ vào nhánh long, và 3 short ra đời
               # RỜI RẠC — không short nào có `cha`, khâu đăng không biết chúng thuộc bài nào.
               # Nay bật long: mỗi bộ = 1 long (nối từ 3 chương) + 3 short là chính 3 chương đó.
               "type": "short", "make_long": True, "long_target": 40, "n_shorts": 3,
               "format": k["dinh_dang"], "accent": pal.get("primary", "#22D3EE"),
               "accent2": pal.get("accent", "#F5B301"),
               "handle": k["handle"], "niche": k["goc_nhin"], "brand": b,
               **chu_ky_giong(thu_tu[ten])}
        if ten in co and capnhat:
            # chỉ các trường DO BẢNG SINH RA; giữ nguyên paused và mọi chỉnh tay khác
            doc = {k: v for k, v in doc.items()
                   if k in ("voice", "voice_rate", "voice_pitch", "accent", "accent2",
                            "format", "handle", "niche", "brand", "the_he")}
        db.collection("render_channels").document(f"{owner}__{ten}").set(doc, merge=True)
        _g = chu_ky_giong(thu_tu[ten])
        print(f"  {'🔄' if (ten in co) else '➕'} {ten:18} [{k['dinh_dang']}] "
              f"{'(giữ nguyên bật/tắt)' if ten in co else ('BẬT' if bat else 'tắt')} "
              f"· {_g['voice'].replace('en-US-', '').replace('Neural', '')} {_g['voice_rate']} {_g['voice_pitch']}")
        tao += 1
    print(f"\n✅ tạo {tao} kênh, bỏ qua {bo}. Trạng thái: {'ĐANG CHẠY' if bat else 'TẮT — bật ở dashboard'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
