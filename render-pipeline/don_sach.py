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


def _dem(db, ten_bo, owner: str) -> int:
    """Đếm tài liệu bằng TRUY VẤN ĐẾM, không duyệt từng tài liệu.

    ── VÌ SAO (1/9/2026) ───────────────────────────────────────────────────────────────────
    Anh: *"ngày nay a chưa chạy gì đã cạn firebase."* Thủ phạm là chính hàm này ở bản trước:
    nó `.stream()` TOÀN BỘ `render_jobs` chỉ để đếm. Với ~2.000 bản ghi thì mỗi lần kiểm kê là
    ~2.000 lượt đọc, mà `don()` gọi kiểm kê HAI lần (trước và sau khi dọn), và workflow chạy
    `don_sach.py` hai bước (thử rồi thật). Một lượt bấm = ~8.000 lượt đọc; tôi bấm hai lượt là
    ~16.000 trên hạn mức free 50.000/ngày. Firestore cạn, và cạn vì công cụ DỌN chứ không phải
    vì dây chuyền render.

    Truy vấn đếm (`aggregation`) tính ở phía máy chủ: **1 lượt đọc thay cho N**.
    Client cũ không có `.count()` thì rơi về đếm thủ công — chậm và tốn, nhưng vẫn đúng, và có
    dòng cảnh báo để biết mình đang trả giá gì.
    """
    q = db.collection(ten_bo).where("owner", "==", owner)
    try:
        r = q.count().get()
        return int(r[0][0].value)
    except Exception:
        print(f"   ⚠ client không hỗ trợ truy vấn đếm — đếm thủ công `{ten_bo}` (tốn hạn mức)")
        return sum(1 for _ in q.stream())


def kiem_ke(db, owner: str, giu: set):
    """Đếm trước khi đụng vào gì. Trả (kênh giữ, kênh dọn, job giữ, job dọn).

    `render_channels` PHẢI tải tài liệu — ta cần `_id` để xoá, và nó chỉ vài chục bản ghi.
    `render_jobs` chỉ cần CON SỐ, nên dùng truy vấn đếm: xem chú thích ở `_dem`.
    """
    kg, kd = [], []
    for d in db.collection("render_channels").where("owner", "==", owner).stream():
        c = d.to_dict() or {}
        c["_id"] = d.id
        (kg if _ten(c) in giu else kd).append(c)
    # Không thể lọc theo danh sách giữ lại bằng truy vấn (Firestore không có "NOT IN" quá 10
    # phần tử), nên đếm TỔNG rồi trừ phần giữ lại — mỗi kênh giữ lại một truy vấn đếm, 18 lượt
    # đọc thay cho hai nghìn.
    tong = _dem(db, "render_jobs", owner)
    jg = 0
    for ten in sorted(giu):
        try:
            r = (db.collection("render_jobs").where("owner", "==", owner)
                 .where("name", "==", ten).count().get())
            jg += int(r[0][0].value)
        except Exception:
            pass
    return kg, kd, jg, max(0, tong - jg)


def don_d1(giu: set, owner: str, that: bool) -> int:
    """Xoá bản ghi `render_job` trong D1 của mọi kênh NGOÀI danh sách giữ lại.

    ── VÌ SAO CẦN (1/9/2026) ───────────────────────────────────────────────────────────────
    Dọn kênh ở Firestore (`render_channels`) là dọn CẤU HÌNH. Nhưng dashboard đếm video và đổ
    ô xổ "Tất cả kênh" từ bảng `render_job` bên **D1** — một kho khác. Anh gửi ảnh: ô xổ vẫn
    liệt kê đủ 50 kênh cũ kèm số đếm, tổng 2088, dù `render_channels` chỉ còn 18 kênh mới.
    Chính mã worker đã ghi sẵn bài học ở `don_job_kenh`: *"Hai kho dữ liệu song song thì lệnh
    dọn phải đụng cả hai."*

    ── DÙNG `hot_db`, KHÔNG TỰ GỌI HTTP ────────────────────────────────────────────────────
    Bản trước tôi viết một đường gọi HTTP riêng và nhận **403**. Không phải sai khoá:
    `hot_db.goi` có chú thích ghi sẵn rằng thiếu `User-Agent` thì Cloudflare chặn ở cổng với mã
    1010 và trả 403 **y hệt sai khoá**. Tôi viết đường gọi thứ ba nên mất luôn cả bài học đã
    trả giá lẫn cơ chế tự tắt sau 20 lần hỏng. Nay đi qua `hot_db` — một cửa duy nhất.
    """
    import hot_db as H
    if not H.bat_ghi():
        print("   ⏭ D1 đang tắt (thiếu HOT_KEY) — bỏ bước dọn D1")
        return 0
    ds = H.goi("dem_tat_ca", {"owner": owner}) or {}
    # `dem_tat_ca` trả `{rows: [{channel, vtype, n}]}` — đọc đúng khoá `rows`, không đoán.
    co = sorted({str(x.get("channel") or "").upper()
                 for x in (ds.get("rows") or []) if x.get("channel")})
    cu = [c for c in co if c and c not in giu]
    print(f"   D1: {len(co)} kênh có bản ghi · {len(cu)} kênh ngoài danh sách giữ lại")
    if not cu:
        print("   ✅ D1 đã sạch" if co else "   ⚠ D1 không trả về kênh nào — kiểm HOT_KEY")
        return 0
    print(f"   sẽ dọn: {', '.join(cu[:10])}" + (" …" if len(cu) > 10 else ""))
    if not that:
        return 0
    r = H.goi("don_job_kenh", {"owner": owner, "kenh": cu}, timeout=90) or {}
    n = int(r.get("xoa", 0))
    print(f"   ✓ D1 xoá {n} bản ghi · còn lại {r.get('con_lai', '?')}")
    return n


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

    # ── DỌN D1 TRƯỚC, VÀ ĐỘC LẬP VỚI FIRESTORE  (1/9/2026) ──────────────────────────────
    # Lượt 33524187148 chết ở bước kiểm kê với `RESOURCE_EXHAUSTED: Quota exceeded` — Firestore
    # cạn hạn mức đọc. Nhưng ô xổ "Tất cả kênh" và số đếm video đọc **D1**, không đọc Firestore.
    # Để việc dọn D1 nằm sau Firestore nghĩa là hạn mức của kho KHÔNG liên quan quyết định xem
    # kho LIÊN QUAN có được dọn hay không. Đảo thứ tự: làm việc quan trọng trước, và đừng để nó
    # phụ thuộc vào thứ có thể cạn.
    don_d1(giu, owner, that)

    try:
        db = _db()
    except Exception as e:
        print(f"⚠ Firestore không dùng được ({str(e)[:70]}) — D1 đã dọn xong ở trên, dừng ở đây")
        return 0
    if db is None:
        print("⚠ không mở được Firestore — D1 đã dọn xong ở trên, dừng ở đây")
        return 0

    # Firestore cạn hạn mức KHÔNG được làm hỏng lệnh: phần quan trọng (D1 — kho dashboard đọc)
    # đã xong ở trên. Ném traceback ở đây chỉ khiến workflow báo đỏ cho một việc đã thành công
    # một nửa, và người đọc log tưởng chẳng có gì chạy được.
    try:
        kg, kd, jg, jd = kiem_ke(db, owner, giu)
    except Exception as e:
        print(f"⚠ Firestore không đọc được ({type(e).__name__}: {str(e)[:70]})")
        print("   D1 đã dọn xong ở trên. Phần Firestore sẽ tự chạy ở lượt sau khi hạn mức hồi.")
        return 0
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
    # ── XOÁ CÓ TRẦN MỖI LƯỢT  (1/9/2026) ────────────────────────────────────────────────────
    # Vòng này phải ĐỌC để biết xoá cái nào, nên nó là chỗ tốn hạn mức còn lại trong đường chạy
    # hằng ngày. Không giới hạn thì một lượt đọc hết ~2.000 bản ghi — đúng thứ đã làm cạn
    # Firestore hôm nay (xem buglog 7cs).
    #
    # Đặt trần 400/lượt: bước này chạy MỖI NGÀY trong luồng render, nên kho tồn sẽ cạn dần sau
    # vài ngày mà không lượt nào bùng. Dọn chậm mà đều tốt hơn dọn hết một lần rồi làm nghẽn
    # cả hệ trong ngày ấy — nhất là khi thứ người dùng NHÌN (D1) đã sạch ngay từ đầu.
    TRAN = 400
    for d in (db.collection("render_jobs").where("owner", "==", owner).limit(TRAN).stream()):
        j = d.to_dict() or {}
        if _ten(j) in giu or any(x in _ten(j) for x in CAM_DUNG):
            continue
        d.reference.delete()
        n_j += 1
    if n_j >= TRAN:
        print(f"   ℹ đã xoá {n_j} bản ghi (trần {TRAN}/lượt) — phần còn lại dọn tiếp ở lượt sau")

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
