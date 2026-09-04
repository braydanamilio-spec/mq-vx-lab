#!/usr/bin/env python3
"""Bảo đảm các composite index đã KHAI thật sự TỒN TẠI trên Firestore.

── VÌ SAO CÓ TỆP NÀY  (4/9/2026) ───────────────────────────────────────────────────────────
`health_guardian` hỏi *"20h qua có video nào xong chưa"* bằng một truy vấn sắp theo thời gian.
Firestore trả `400 The query requires an index`, nên nó rơi xuống nhánh dự phòng và **không
kết luận được gì** — tức cái canh gác của cả hệ đã fail-open suốt, không canh gì.

Index `render_jobs: owner + status + created_at DESCENDING` **CÓ** trong
`dashboard/firestore.indexes.json`. Nhưng **khai một index không phải là có nó**: tệp ấy chỉ
là bản khai, phải `firebase deploy` mới thành index thật, và không workflow nào làm việc đó.
Đây là chỗ dễ tin nhầm nhất trong cả hệ, vì tệp đọc lên rất thuyết phục và git thì sạch.

Cùng họ lỗi §13.1: *cơ chế đã có sẵn, chỉ thiếu một thứ gọi nó.*

── VÌ SAO KHÔNG DÙNG `firebase deploy` ─────────────────────────────────────────────────────
`firebase-tools` cần Node, cần đăng nhập, và deploy CẢ tệp khai — tức nó cũng xoá những index
mà ai đó tạo tay trên console. Firestore Admin API tạo TỪNG index một, idempotent, và dùng
đúng service account đã có trong secrets. Ít quyền hơn, ít tác dụng phụ hơn.

── VÌ SAO ĐỌC PROJECT QUA `firestore_bridge` ───────────────────────────────────────────────
`render_jobs` nằm ở Project B khi shard bật, ở A khi chưa. Đọc biến môi trường ở đây là chép
lại luật ấy thành nguồn sự thật thứ hai — và nó sẽ lệch đúng vào ngày ai đó đổi shard. Hỏi
chính client mà guardian dùng thì không thể nhắm nhầm project.
"""
from __future__ import annotations
import json
import os
import sys
import urllib.error
import urllib.request

GOC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GOC)

# Chỉ khai những index mà MÃ THẬT SỰ truy vấn. Khai thừa thì tốn chỗ và tốn lượt ghi mỗi khi
# một tài liệu đổi, mà không ai dùng — index là một cái giá trả liên tục, không phải một lần.
CAN = [
    # health_guardian: .where(owner).where(status).order_by(created_at DESC).limit(20)
    ("render_jobs", [("owner", "ASCENDING"), ("status", "ASCENDING"),
                     ("created_at", "DESCENDING")]),
]


def _token(creds_file: str) -> str:
    from google.oauth2 import service_account
    import google.auth.transport.requests as _rq
    c = service_account.Credentials.from_service_account_file(
        creds_file, scopes=["https://www.googleapis.com/auth/datastore"])
    c.refresh(_rq.Request())
    return c.token


def _goi(url: str, tok: str, body=None):
    req = urllib.request.Request(
        url, data=(json.dumps(body).encode() if body is not None else None),
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json",
                 # `User-Agent` bắt buộc: §13.15 — thiếu nó thì tầng CDN trả 403 và ta đi sửa
                 # thứ không hỏng, tưởng là sai khoá.
                 "User-Agent": "Mozilla/5.0 (compatible; MM0-index/1.0)"},
        method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode() or "{}")


def bao_dam() -> int:
    """Tạo index còn thiếu. Trả số index vừa đặt hàng tạo (0 = đã đủ)."""
    # HỎNG MỀM. Đây là bước TỐI ƯU, không phải bước thiết yếu: thiếu khoá (chạy ở máy anh),
    # thiếu quyền, mạng chập — đều không được làm chết lượt guardian, vì guardian còn hai việc
    # khác quan trọng hơn. §13.3: trong đường chạy tự động, hỏng ở việc phụ phải im lặng đi
    # tiếp, chỉ việc thiết yếu mới được cho cả lượt đỏ.
    try:
        import firestore_bridge as FB
        db = FB._db_jobs()
        project = getattr(db, "project", None)
    except Exception as e:
        print(f"   ⓘ không mở được Firestore ({type(e).__name__}) — bỏ qua bước bảo đảm index")
        return 0
    if not project:
        print("   ⓘ không đọc được project từ client — bỏ qua")
        return 0
    # `render_jobs` ở Project B khi shard bật, ở A khi chưa — thử B trước, đúng thứ tự mà
    # `_db_jobs` dùng, rồi mới tới khoá mặc định.
    creds = next((c for c in (os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_B"),
                              os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
                  if c and os.path.exists(c)), "")
    if not creds:
        print("   ⓘ không có tệp service account — bỏ qua (bình thường khi chạy ở máy)")
        return 0
    tok = _token(creds)
    goc = (f"https://firestore.googleapis.com/v1/projects/{project}"
           f"/databases/(default)/collectionGroups")
    dat = 0
    for nhom, truong in CAN:
        try:
            co = _goi(f"{goc}/{nhom}/indexes", tok).get("indexes") or []
        except urllib.error.HTTPError as e:
            print(f"   ⚠ không liệt kê được index của {nhom}: HTTP {e.code} — bỏ qua")
            continue
        muon = [{"fieldPath": f, "order": o} for f, o in truong]
        def _khop(ix):
            fs = [f for f in (ix.get("fields") or []) if f.get("fieldPath") != "__name__"]
            return [(f.get("fieldPath"), f.get("order")) for f in fs] == truong
        if any(_khop(i) for i in co):
            print(f"   ✅ {nhom}: index đã có ({' · '.join(f'{f} {o}' for f, o in truong)})")
            continue
        try:
            _goi(f"{goc}/{nhom}/indexes", tok,
                 {"queryScope": "COLLECTION", "fields": muon})
            dat += 1
            print(f"   🛠 {nhom}: ĐÃ ĐẶT HÀNG tạo index — Firestore dựng mất vài phút, "
                  f"truy vấn sắp xếp sẽ tự chạy được sau đó")
        except urllib.error.HTTPError as e:
            t = ""
            try:
                t = e.read().decode()[:160]
            except Exception:
                pass
            # 409 = đã tồn tại (một lượt trước vừa đặt) -> KHÔNG phải lỗi.
            if e.code == 409:
                print(f"   ✅ {nhom}: index đang được dựng (lượt trước đã đặt)")
            else:
                print(f"   ⚠ {nhom}: tạo index hỏng HTTP {e.code} {t}")
    return dat


if __name__ == "__main__":
    print("🔎 Bảo đảm composite index cho render_jobs")
    try:
        bao_dam()
    except Exception as e:
        # Không bao giờ cho bước phụ này làm đỏ cả lượt guardian.
        print(f"   ⓘ bỏ qua bảo đảm index ({type(e).__name__}: {str(e)[:70]})")
