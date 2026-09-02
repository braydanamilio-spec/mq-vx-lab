#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ĐẨY VIDEO VỪA DỰNG VÀO HÀNG ĐỢI ĐĂNG — mắt xích còn thiếu để chạy A-Z (1/9/2026)

Anh: *"nó phải tự động chứ mày đẩy chi, nó chưa đồng bộ là mày xây pepline sai rồi"* và
*"còn đăng bài đồng bộ auto a-z nữa chứ"*.

Đúng. Hai workflow render mới dừng ở bước gói artifact rồi hết — không có bước nào đưa video
sang khâu đăng. Artifact hết hạn sau 14 ngày là mất trắng, và trong lúc đó không ai đăng được
gì. Dây chuyền thật của hệ cũ là:

    render  ->  enqueue.py (đẩy Drive + ghi hàng đợi)  ->  publish.yml đăng YouTube/FB/IG

Tệp này là MẮT XÍCH GIỮA, và nó cố ý mỏng: **không tự viết lối đẩy Drive**. Repo publish đã có
`src/enqueue.py` làm đúng việc ấy, đã chạy thật cho ~50 kênh. Viết bản thứ hai là tạo nguồn thứ
hai — họ lỗi đã trả giá nhiều lần. Ở đây chỉ dịch: `.tai.json` -> tham số dòng lệnh của nó.

Bỏ qua có kiểm soát, không im lặng:
  · video không có `.tai.json`  -> bỏ, in rõ (đăng mà không có tiêu đề là rác)
  · kênh chưa có trong `channels.yaml` -> bỏ, in rõ (enqueue sẽ ném KeyError)
"""
import argparse
import glob
import io
import json
import os
import subprocess
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(GOC, "out")


def _kenh_biet(thu_publish: str) -> set:
    """Danh sách kênh repo publish biết. Không đọc được thì trả rỗng -> không chặn ai."""
    p = os.path.join(thu_publish, "config", "channels.yaml")
    try:
        import yaml
        d = yaml.safe_load(io.open(p, encoding="utf-8"))
        return {k.upper() for k in (d.get("channels") or {})}
    except Exception as e:
        print(f"   ⚠️ không đọc được channels.yaml ({str(e)[:60]}) — bỏ qua bước kiểm kênh")
        return set()


def day_mot(mp4: str, thu_publish: str, biet: set, that: bool) -> bool:
    tai = mp4[:-4] + ".tai.json"
    if not os.path.exists(tai):
        print(f"   ⏭ {os.path.basename(mp4)}: chưa có .tai.json -> bỏ")
        return False
    d = json.load(io.open(tai, encoding="utf-8"))
    # Ưu tiên `ma` — mã kênh do bộ sinh siêu dữ liệu ghi thẳng. Chỉ khi không có mới suy từ tên
    # hiển thị (bộ v3/v5 cũ chưa ghi `ma`, và cách suy ấy vẫn đúng với chúng).
    kenh = (d.get("ma") or (d.get("kenh") or "").replace(" ", "")).upper()
    if biet and kenh not in biet:
        print(f"   ⏭ {os.path.basename(mp4)}: kênh {kenh} chưa có trong channels.yaml -> bỏ")
        return False

    yt = d.get("youtube") or {}
    nen = [k for k, v in (d.get("dang_duoc") or {}).items() if v]
    cmd = [sys.executable, os.path.join(thu_publish, "src", "enqueue.py"),
           "--channel", kenh,
           "--video", os.path.abspath(mp4),
           "--type", "long" if d.get("loai") == "long" else "short",
           "--topic", (yt.get("title") or d.get("kenh") or "")[:80],
           "--title", yt.get("title") or "",
           "--desc", yt.get("description") or "",
           "--tags", ",".join(yt.get("tags") or [])[:300],
           "--platforms", ",".join(nen) or "youtube"]
    if not that:
        print(f"   (thử) {kenh:18s} {os.path.basename(mp4)} -> {'+'.join(nen)}")
        return True
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    ok = r.returncode == 0
    # NÓI RA VIDEO VÀO KHO NÀO — nếu không thì không ai kiểm được việc CHIA ĐỀU.
    # `enqueue.py` in `[kho:TÊN]` và `Drive file id: …`, nhưng ta bắt toàn bộ đầu ra của nó nên
    # hai dòng ấy biến mất. Anh hỏi "chia đều các kho chưa" và log không trả lời được — một
    # cơ chế không quan sát được thì cũng như không có: không ai biết nó lệch cho tới khi một
    # kho đầy và cả mẻ hỏng.
    import re as _re
    _kho = ""
    if ok:
        _m = _re.search(r"\[kho:([^\]]+)\]", r.stdout or "")
        _id = _re.search(r"Drive file id:\s*(\S+)", r.stdout or "")
        _kho = (f"  → kho {_m.group(1)}" if _m else "")
        if _id:
            _kho += f" · {_id.group(1)[:16]}"
    print(f"   {'✅' if ok else '❌'} {kenh:18s} {os.path.basename(mp4)}{_kho}"
          f"{'' if ok else ' — ' + (r.stderr or r.stdout or '')[-160:]}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", default=os.path.join(GOC, "..", "_autopublisher"),
                    help="thư mục repo MM0-AutoPublisher đã checkout")
    # `v9_` = 18 kênh GIẢI THÍCH (1/9). Thiếu tiền tố ở đây là video dựng xong mà không bao giờ
    # lên Drive — và bước này báo "⚠️ không có video nào để đẩy" rồi trả 0, tức lượt chạy vẫn
    # XANH. Mỗi thế hệ mới phải thêm tiền tố vào đây; cổng `kiem_az.py` canh đúng chỗ này.
    ap.add_argument("--mau", default="v3_*.mp4,v3L_*.mp4,v5_*.mp4,v5L_*.mp4,v9_*.mp4",
                    help="mẫu tên video cần đẩy, cách nhau bằng dấu phẩy")
    ap.add_argument("--that", action="store_true", help="đẩy thật (mặc định chỉ in ra để xem)")
    a = ap.parse_args()

    if not os.path.exists(os.path.join(a.publish, "src", "enqueue.py")):
        print(f"⚠️ không thấy repo publish ở {a.publish} — bỏ bước đẩy kho, video vẫn nằm ở artifact")
        return 0

    biet = _kenh_biet(a.publish)
    ds = []
    for m in a.mau.split(","):
        ds += sorted(glob.glob(os.path.join(OUT, m.strip())))
    if not ds:
        print("⚠️ không có video nào để đẩy")
        return 0

    n = sum(day_mot(f, a.publish, biet, a.that) for f in ds)
    _tong = len(ds)
    print(f"\n{'✅' if n else '⚠️'} {n}/{len(ds)} video vào hàng đợi đăng"
          f"{'' if a.that else '  (chạy thử — thêm --that để đẩy thật)'}")
    # THOÁT MÃ THEO KẾT QUẢ, KHÔNG THEO VIỆC ĐÃ CHẠY  (2/9/2026)
    # Bản trước luôn `return 0`. Nên khi đẩy được 0/2 video, lệnh vẫn báo thành công, bước
    # workflow xanh, cổng "Chốt — video đã lên kho chưa" của tôi cũng xanh — vì nó kiểm MÃ THOÁT
    # chứ không kiểm KẾT QUẢ. Đo thật: lượt 33533150981 xanh 18/18, log ghi "0/2 video vào hàng
    # đợi đăng", dashboard 0. Cổng tôi vừa xây để chặn đúng chuyện này lại bị chính chuyện ấy
    # lách qua.
    # Có tệp để đẩy mà đẩy được 0 -> HỎNG. Không có tệp nào thì không phải lỗi.
    if a.that and _tong and n == 0:
        print(f"❌ có {_tong} tệp nhưng KHÔNG đẩy được tệp nào — coi là hỏng để lượt chạy đỏ,")
        print("   nhờ đó mốc cron sau tự thử lại thay vì im lặng bỏ qua.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
