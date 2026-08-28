#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KLING API — CHỖ CẮM để cả dây chuyền thành tự động A-Z (28/8/2026).

TRẠNG THÁI: VIẾT SẴN, CHƯA CHẠY THẬT.
Anh chưa mua API nên em chưa gọi được lần nào. Mọi thứ dưới đây viết theo hình dạng API mà Kling
công bố, và em đánh dấu rõ NHỮNG CHỖ PHẢI ĐỐI CHIẾU LẠI với tài liệu lúc anh mua — vì em không
kiểm chứng được, và đoán bừa rồi nói chắc là cách tệ nhất.

VỊ TRÍ: đây là hàm DUY NHẤT phải đổi để bỏ khâu thủ công.
    hôm nay : người dán prompt vào Kling, tải clip, thả vào `clips/scene-NN.mp4`
    có API  : `sinh_clip(thu_muc)` tự làm đúng việc đó, ghi vào ĐÚNG chỗ ấy
Mọi thứ từ `kling_lo` trở đi không biết và không cần biết clip từ đâu ra.

TIỀN — ĐỌC TRƯỚC KHI BẬT
------------------------
Kling API tính tiền THEO TỪNG LƯỢT SINH. Một video của anh 5-8 cảnh = 5-8 lượt. "Hàng trăm video
mỗi ngày" nhân lên là con số lớn. Nên hàm này CỐ Ý có `tran_ngay`: chạm trần thì dừng, không âm
thầm tiêu tiếp. Mặc định trần thấp — anh tự nâng khi đã nhìn thấy hoá đơn thật.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import os
import time
import urllib.request

GOC = os.path.dirname(os.path.abspath(__file__))

# ── PHẢI ĐỐI CHIẾU LẠI khi mua key (Kling đổi tên miền theo khu vực và đánh số phiên bản) ──
NEN = os.environ.get("KLING_BASE") or "https://api-singapore.klingai.com"
DUONG_TAO = "/v1/videos/text2video"          # image2video là đường khác, xem `sinh_clip`
DUONG_HOI = "/v1/videos/text2video/{id}"
MODEL = os.environ.get("KLING_MODEL") or "kling-v1-6"

TRAN_NGAY = int(os.environ.get("KLING_TRAN_NGAY") or "20")   # số lượt sinh tối đa mỗi ngày
SO_DEM = os.path.join(GOC, "out", "kling", ".dem_ngay.json")


def co_api() -> bool:
    """Có khoá chưa. Cả hệ hỏi hàm này để biết chạy A-Z hay chạy thủ công."""
    return bool(os.environ.get("KLING_ACCESS_KEY") and os.environ.get("KLING_SECRET_KEY"))


def _jwt() -> str:
    """JWT HS256 ký bằng AccessKey/SecretKey — Kling không dùng key trần trong header.

    PHẢI ĐỐI CHIẾU: thời hạn và tên trường (`iss`/`exp`/`nbf`) theo tài liệu hiện hành."""
    ak = os.environ["KLING_ACCESS_KEY"]
    sk = os.environ["KLING_SECRET_KEY"]
    now = int(time.time())
    b = lambda o: base64.urlsafe_b64encode(json.dumps(o, separators=(",", ":")).encode()).rstrip(b"=")
    head = b({"alg": "HS256", "typ": "JWT"})
    than = b({"iss": ak, "exp": now + 1800, "nbf": now - 5})
    ky = hmac.new(sk.encode(), head + b"." + than, hashlib.sha256).digest()
    return (head + b"." + than + b"." + base64.urlsafe_b64encode(ky).rstrip(b"=")).decode()


def _goi(duong: str, body: dict | None = None, cach: str = "POST", giay: int = 60) -> dict:
    req = urllib.request.Request(
        NEN + duong, method=cach,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bearer " + _jwt(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=giay) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def _dem_hom_nay(them: int = 0) -> int:
    """Sổ đếm lượt sinh TRONG NGÀY — cái phanh duy nhất giữa anh và một hoá đơn bất ngờ.

    Ghi ra tệp chứ không giữ trong bộ nhớ: mỗi lane là một tiến trình riêng, giữ trong bộ nhớ thì
    18 lane mỗi lane tự tiêu một trần."""
    hom = time.strftime("%Y-%m-%d")
    try:
        d = json.load(io.open(SO_DEM, encoding="utf-8"))
    except Exception:
        d = {}
    if d.get("ngay") != hom:
        d = {"ngay": hom, "n": 0}
    d["n"] = int(d.get("n") or 0) + them
    if them:
        os.makedirs(os.path.dirname(SO_DEM), exist_ok=True)
        io.open(SO_DEM, "w", encoding="utf-8").write(json.dumps(d))
    return int(d["n"])


def tao_task(prompt: str, giay: int = 5, ty_le: str = "9:16", anh_goc: str = "") -> str:
    """Đặt một lượt sinh. Trả task_id.

    `anh_goc` = ảnh tham chiếu (base64 hoặc URL). BÀI HỌC 09/08: prompt chữ thuần TRÔI — xin
    Pompeii ra làng Ý hiện đại. Có ảnh gốc thì bám sát hơn hẳn. Nên khi anh bật A-Z, nên vẽ ảnh
    trước (Cloudflare FLUX, gần như miễn phí) rồi mới cho Kling làm động — vừa rẻ vừa đúng ý hơn.
    """
    body = {
        "model_name": MODEL,
        "prompt": prompt[:2400],
        "duration": str(int(giay)),
        "aspect_ratio": ty_le,
        "mode": os.environ.get("KLING_MODE") or "std",   # std rẻ hơn pro; PHẢI ĐỐI CHIẾU tên
        "cfg_scale": 0.5,
    }
    duong = DUONG_TAO
    if anh_goc:
        duong = "/v1/videos/image2video"                  # PHẢI ĐỐI CHIẾU đường và tên trường
        body["image"] = anh_goc
    ra = _goi(duong, body)
    tid = ((ra.get("data") or {}).get("task_id")) or ra.get("task_id") or ""
    if not tid:
        raise RuntimeError(f"Kling không trả task_id: {str(ra)[:200]}")
    _dem_hom_nay(1)
    return str(tid)


def cho_xong(task_id: str, toi_da_giay: int = 900) -> str:
    """Chờ tới khi có video. Trả URL, hoặc "" nếu hỏng.

    Kling sinh mất vài phút. Hỏi thưa (15 giây) chứ không dồn dập — hỏi dày không làm nó nhanh hơn,
    chỉ tốn lượt gọi."""
    het = time.time() + toi_da_giay
    while time.time() < het:
        ra = _goi(DUONG_HOI.format(id=task_id), None, "GET", 30)
        d = ra.get("data") or {}
        tt = str(d.get("task_status") or "").lower()
        if tt in ("succeed", "success", "completed"):
            vs = ((d.get("task_result") or {}).get("videos") or [])
            return str((vs[0] or {}).get("url") or "") if vs else ""
        if tt in ("failed", "fail", "error"):
            print(f"   ❌ Kling task {task_id} hỏng: {str(d.get('task_status_msg'))[:120]}")
            return ""
        time.sleep(15)
    print(f"   ⏱️ Kling task {task_id} quá {toi_da_giay}s — bỏ chờ (task vẫn chạy bên Kling)")
    return ""


def tai_ve(url: str, dich: str) -> bool:
    os.makedirs(os.path.dirname(dich), exist_ok=True)
    tam = dich + ".tai"
    try:
        with urllib.request.urlopen(url, timeout=300) as r, io.open(tam, "wb") as f:
            while True:
                c = r.read(1 << 16)
                if not c:
                    break
                f.write(c)
        # Đổi tên SAU KHI tải xong: `kiem_du` bên `kling_lo` coi tệp <10KB là chưa có, nhưng tệp
        # tải dở vẫn có thể lớn hơn thế. Ghi tên tạm rồi mới đổi thì không bao giờ ghép nhầm bản dở.
        if os.path.getsize(tam) < 10000:
            os.remove(tam); return False
        os.replace(tam, dich)
        return True
    except Exception as e:
        print(f"   ⚠️ tải clip hỏng: {str(e)[:90]}")
        try: os.remove(tam)
        except OSError: pass
        return False


def sinh_clip(thu_muc: str) -> tuple[int, int]:
    """CHỖ CẮM: sinh những cảnh CÒN THIẾU của một thư mục việc. Trả (số ra, số còn thiếu).

    Cố ý chỉ làm phần THIẾU: chạy lại không sinh lại cái đã có, nên không đốt tiền hai lần —
    và anh có thể tự dán tay vài cảnh khó rồi để API làm nốt phần dễ."""
    import kling_lo as KL
    if not co_api():
        print("   ⏭️ chưa có KLING_ACCESS_KEY/SECRET — bỏ qua sinh tự động (vẫn chạy thủ công được)")
        return 0, -1
    d = json.load(io.open(os.path.join(thu_muc, "shots.json"), encoding="utf-8"))
    _, _, thieu = KL.kiem_du(thu_muc)
    if not thieu:
        return 0, 0
    can = {int(x.split("-")[1]) for x in thieu if x.startswith("scene-")}
    ra = 0
    for s in (d.get("scenes") or []):
        n = int(s.get("n") or 0)
        if n not in can:
            continue
        dem = _dem_hom_nay()
        if dem >= TRAN_NGAY:
            print(f"   🛑 chạm trần {TRAN_NGAY} lượt sinh/ngày — DỪNG để không tiêu thêm tiền. "
                  f"Nâng bằng KLING_TRAN_NGAY khi anh đã xem hoá đơn thật.")
            break
        print(f"   🎬 sinh cảnh {n:02d} ({s.get('sec')}s) — lượt {dem + 1}/{TRAN_NGAY} hôm nay")
        try:
            tid = tao_task(str(s.get("prompt") or ""), int(s.get("sec") or 5))
            url = cho_xong(tid)
        except Exception as e:
            print(f"   ❌ cảnh {n:02d}: {str(e)[:110]}")
            continue
        if url and tai_ve(url, os.path.join(thu_muc, "clips", f"scene-{n:02d}.mp4")):
            ra += 1
    _, _, con = KL.kiem_du(thu_muc)
    return ra, len(con)


if __name__ == "__main__":
    import sys
    if not co_api():
        print("Chưa có khoá. Đặt hai biến rồi chạy lại:")
        print("   KLING_ACCESS_KEY=...   KLING_SECRET_KEY=...")
        print("Lấy ở app.klingai.com/dev/api-key (gói API riêng, KHÁC gói web).")
        sys.exit(1)
    print(f"Đã có khoá · nền {NEN} · model {MODEL} · "
          f"đã dùng {_dem_hom_nay()}/{TRAN_NGAY} lượt hôm nay")
