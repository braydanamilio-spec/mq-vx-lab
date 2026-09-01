#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DỌN SẠCH THEO DANH SÁCH GIỮ LẠI — giữ đúng 10 kênh mới, dọn tất cả còn lại.  (1/9/2026)

Anh: *"dọn hết các channel cũ hiện tại trên web để làm 10 channel mới"* — và gửi ảnh chụp
dashboard còn nguyên 37 kênh "đang làm", 13 kênh "đã có video", brand kit còn 50 kênh.

── VÌ SAO KHÔNG DÙNG `don_the_he_1.py` ─────────────────────────────────────────────────────
Đọc mã nó trước khi chạy (luật: nhìn đích trước khi xoá) và thấy dòng quyết định:

    cu = [c for c in tat_ca if str(c.get("the_he") or "") != "2" and ... not in moi]

Nó chỉ dọn kênh có `the_he != "2"`. Mà đúng 50 kênh đang hiện trên dashboard là **thế hệ 2** —
chạy nó sẽ bỏ qua sạch, và log vẫn báo thành công. Chạy rồi báo "đã dọn" là báo sai.

Đây là lý do tệp này tồn tại: lọc theo **DANH SÁCH GIỮ LẠI**, không lọc theo thế hệ. Thế hệ là
thuộc tính của quá khứ; danh sách giữ lại là thứ mô tả đúng điều anh muốn — "chỉ còn mười kênh
này, mọi thứ khác đi ra".

── NGUỒN CỦA DANH SÁCH GIỮ LẠI ─────────────────────────────────────────────────────────────
Đọc thẳng `MM0-AutoPublisher/config/channels.yaml`. KHÔNG chép tay vào đây: chép tay là tạo
nguồn sự thật thứ hai, và hai nguồn thì sớm muộn lệch nhau — đúng họ lỗi đã trả giá nhiều lần
trong dự án này. Thêm kênh vào yaml là danh sách giữ lại tự có thêm.

── AN TOÀN ─────────────────────────────────────────────────────────────────────────────────
· CHẠY THỬ LÀ MẶC ĐỊNH. Phải có `--that` mới xoá thật.
· In kiểm kê ĐẦY ĐỦ trước khi đụng vào gì, và in lại sau.
· Không đụng thư mục hệ thống (`_KICHBAN`, `_BACKUP`, `_SCRIPT`, `brand`, `config`) — sidecar
  kịch bản nằm trong đó, mất là mất kho viết.
· Danh sách giữ lại RỖNG thì DỪNG. Đọc yaml hỏng mà vẫn chạy là xoá sạch mọi thứ.
"""
import argparse
import io
import os
import sys

GOC = os.path.dirname(os.path.abspath(__file__))
# Đường dẫn tới channels.yaml khác nhau giữa MÁY và ACTIONS: ở máy repo publisher nằm cạnh
# repo render (`../MM0-AutoPublisher`), trên runner nó được checkout vào `_autopublisher`.
# Không liệt kê cả hai thì trên Actions danh sách giữ lại RỖNG -> bộ dọn tự dừng, và log chỉ
# nói "đọc yaml hỏng" chứ không nói vì sao. Đúng cái bẫy `cp -r MM0-AutoPublisher/src` đã ghi
# trong `don_the_he_1.yml`: repo riêng không có sẵn trong checkout của repo render.
_UNG_VIEN = [
    os.path.join(os.path.dirname(GOC), "MM0-AutoPublisher", "config", "channels.yaml"),
    os.path.join(os.path.dirname(GOC), "_autopublisher", "config", "channels.yaml"),
    os.path.join(GOC, "..", "_autopublisher", "config", "channels.yaml"),
    os.environ.get("CHANNELS_YAML", ""),
]
YAML = next((p for p in _UNG_VIEN if p and os.path.exists(p)), _UNG_VIEN[0])

# Thư mục/bản ghi hệ thống — không bao giờ đụng, dù có nằm ngoài danh sách giữ lại.
CAM_DUNG = ("_KICHBAN", "_BACKUP", "_SCRIPT", "_QUEUE", "brand", "config")


def _db():
    """Client Firestore CÓ ĐƯỜNG LẬT B2 — dùng chung với dây chuyền chính, không dựng riêng.

    Lý do đã ghi ở `don_the_he_1.py`: đúng lúc hệ cạn hạn mức là lúc cần công cụ quản trị nhất,
    mà client tự dựng lại là thứ chết đầu tiên."""
    import firestore_bridge as _FB
    return _FB._db_meta()


def giu_lai() -> set:
    """Danh sách kênh GIỮ LẠI, đọc thẳng từ channels.yaml. Rỗng = dừng, không xoá gì."""
    if not os.path.exists(YAML):
        return set()
    try:
        import yaml
        d = yaml.safe_load(io.open(YAML, encoding="utf-8")) or {}
        return {str(k).upper() for k in (d.get("channels") or {})}
    except Exception:
        # Không có pyyaml thì đọc thô — thà thô còn hơn trả rỗng, vì rỗng nghĩa là "xoá sạch".
        import re
        s = io.open(YAML, encoding="utf-8").read()
        return {m.upper() for m in re.findall(r"^\s{2}([A-Z0-9_]+):", s, re.M)}


def _ten(c) -> str:
    return str(c.get("name") or c.get("kenh") or c.get("channel") or "").upper().replace(" ", "")


def kiem_ke(db, owner: str, giu: set):
    """Đếm trước khi đụng vào gì. Trả (kênh giữ, kênh dọn, job giữ, job dọn)."""
    kg, kd, jg, jd = [], [], 0, 0
    for d in db.collection("render_channels").where("owner", "==", owner).stream():
        c = d.to_dict() or {}
        c["_id"] = d.id
        (kg if _ten(c) in giu else kd).append(c)
    for d in db.collection("render_jobs").where("owner", "==", owner).stream():
        j = d.to_dict() or {}
        if _ten(j) in giu:
            jg += 1
        else:
            jd += 1
    return kg, kd, jg, jd


WORKER = "https://mm0-connect.adisondurham-ef1.workers.dev/api/hot"


def don_d1(giu: set, owner: str, that: bool) -> int:
    """Xoá bản ghi `render_job` trong D1 của mọi kênh NGOÀI danh sách giữ lại.

    ── VÌ SAO CẦN (1/9/2026) ───────────────────────────────────────────────────────────────
    Dọn kênh ở Firestore (`render_channels`) là dọn CẤU HÌNH. Nhưng dashboard đếm video và đổ
    ô xổ "Tất cả kênh" từ bảng `render_job` bên **D1** — một kho khác. Anh gửi ảnh: ô xổ vẫn
    liệt kê đủ 50 kênh cũ kèm số đếm (ALERTNOW 55 · AMERICALOOKEDUP 57 · …), tổng 2088, dù
    `render_channels` chỉ còn 18 kênh mới.
    Chính mã worker đã ghi sẵn bài học này ở `don_job_kenh`: *"Hai kho dữ liệu song song thì
    lệnh dọn phải đụng cả hai."* Tôi dọn một kho rồi báo đã xong — đó là lỗi của tôi.

    Nguồn danh sách kênh cần dọn vẫn là `channels.yaml` (qua `giu`), không chép tay: thêm kênh
    vào yaml là nó tự được giữ, không cần sửa thêm chỗ nào.
    """
    khoa = os.environ.get("HOT_KEY", "")
    if not khoa:
        print("   ⏭ không có HOT_KEY -> bỏ bước dọn D1 (chạy trong workflow thì có)")
        return 0
    import json
    import urllib.request

    def goi(lenh, tham):
        r = urllib.request.Request(
            WORKER, method="POST",
            data=json.dumps({"lenh": lenh, "tham": tham}).encode(),
            headers={"content-type": "application/json", "x-hot-key": khoa})
        with urllib.request.urlopen(r, timeout=60) as f:
            return json.loads(f.read().decode())

    try:
        ds = goi("dem_tat_ca", {"owner": owner})
    except Exception as e:
        print(f"   ⚠ không hỏi được D1: {str(e)[:90]}")
        return 0
    # `dem_tat_ca` trả `{rows: [{channel, vtype, n}]}` — đọc đúng khoá `rows`, không đoán.
    co = sorted({str(x.get("channel") or "").upper()
                 for x in (ds.get("rows") or []) if x.get("channel")})
    cu = [c for c in co if c and c not in giu]
    print(f"   D1: {len(co)} kênh có bản ghi · {len(cu)} kênh ngoài danh sách giữ lại")
    if not cu:
        print("   ✅ D1 đã sạch")
        return 0
    print(f"   sẽ dọn: {', '.join(cu[:10])}" + (" …" if len(cu) > 10 else ""))
    if not that:
        return 0
    try:
        r = goi("don_job_kenh", {"owner": owner, "kenh": cu})
        print(f"   ✓ D1 xoá {r.get('xoa', 0)} bản ghi · còn lại {r.get('con_lai', '?')}")
        return int(r.get("xoa", 0))
    except Exception as e:
        print(f"   ⚠ dọn D1 hỏng: {str(e)[:90]}")
        return 0


def don(that: bool = False, owner: str = "") -> int:
    giu = giu_lai()
    if not giu:
        print("❌ DỪNG: danh sách giữ lại RỖNG (đọc channels.yaml hỏng).")
        print("   Chạy tiếp là xoá sạch mọi kênh. Không đánh cược chỗ này.")
        return 2
    print(f"→ giữ lại {len(giu)} kênh: {', '.join(sorted(giu))}")

    owner = owner or os.environ.get("OWNER_UID", "")
    if not owner:
        print("❌ thiếu OWNER_UID")
        return 2
    db = _db()
    if db is None:
        print("❌ không mở được Firestore")
        return 2

    kg, kd, jg, jd = kiem_ke(db, owner, giu)
    print(f"\n📊 KIỂM KÊ TRƯỚC KHI DỌN")
    print(f"   render_channels : giữ {len(kg)} · dọn {len(kd)}")
    print(f"   render_jobs     : giữ {jg} · dọn {jd}")
    if kd:
        ten = sorted(_ten(c) for c in kd)
        print(f"   kênh sẽ dọn: {', '.join(ten[:12])}" + (" …" if len(ten) > 12 else ""))

    if not that:
        print("\n⚠ CHẠY THỬ — chưa xoá gì. Thêm `--that` để dọn thật.")
        return 0

    n_k = n_j = 0
    for c in kd:
        if any(x in _ten(c) for x in CAM_DUNG):
            continue
        db.collection("render_channels").document(c["_id"]).delete()
        n_k += 1
    for d in db.collection("render_jobs").where("owner", "==", owner).stream():
        j = d.to_dict() or {}
        if _ten(j) in giu or any(x in _ten(j) for x in CAM_DUNG):
            continue
        d.reference.delete()
        n_j += 1

    # Sổ đếm: đặt lại theo số THẬT còn lại, không để nguyên con số cũ.
    # Đây chính là chỗ đã sinh ra con số "2088" đứng lì trên dashboard sau khi anh dọn kho —
    # ô ấy đọc bộ đếm, không đếm tệp. Dọn mà không đặt lại sổ thì màn hình vẫn nói con số cũ.
    try:
        db.collection("render_stats").document(owner).set(
            {"__pushed__": jg, "don_sach_at": __import__("datetime").datetime.utcnow().isoformat()},
            merge=True)
        print("   ✓ đặt lại sổ đếm theo số thật còn lại")
    except Exception as e:
        print(f"   ⚠ không đặt lại được sổ đếm: {str(e)[:90]}")

    # DỌN CẢ D1 — không chỉ Firestore. Xem chú thích ở `don_d1`.
    don_d1(giu, owner, that)

    kg2, kd2, jg2, jd2 = kiem_ke(db, owner, giu)
    print(f"\n🧹 ĐÃ DỌN {n_k} kênh · {n_j} job")
    print(f"📊 KIỂM KÊ SAU KHI DỌN")
    print(f"   render_channels : giữ {len(kg2)} · còn sót {len(kd2)}")
    print(f"   render_jobs     : giữ {jg2} · còn sót {jd2}")
    if kd2 or jd2:
        print("⚠ CÒN SÓT — chạy lại, hoặc phần sót nằm ngoài quyền xoá.")
        return 1
    print("✅ SẠCH: chỉ còn các kênh trong danh sách giữ lại.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--that", action="store_true", help="dọn THẬT (mặc định chỉ chạy thử)")
    ap.add_argument("--owner", default="")
    a = ap.parse_args()
    return don(a.that, a.owner)


if __name__ == "__main__":
    raise SystemExit(main())
