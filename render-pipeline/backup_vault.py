#!/usr/bin/env python3
"""SAO LƯU KHO KEY + CẤU HÌNH, CÓ MÃ HOÁ (24/8/2026).

Vì sao cần: toàn bộ 211 key API, 55 kênh và cấu hình đang nằm MỘT CHỖ là Firestore. Firebase bị khoá,
xoá nhầm, hay quota chết dài ngày là mất trắng công gom key nhiều tháng. B2 chỉ là bản gương CÙNG hạ
tầng Google — cùng rủi ro tài khoản.

Lớp sao lưu này ĐỘC LẬP hạ tầng:
  • Dữ liệu: gemini_keys + render_channels + render_config  (KHÔNG lấy job/video — nặng, tái tạo được)
  • Mã hoá: Fernet (AES-128-CBC + HMAC), khoá dẫn xuất từ mật khẩu bằng PBKDF2-SHA256 480.000 vòng
  • Nơi cất: 3 tài khoản Drive KHÁC NHAU trong hồ 72 kho -> hỏng 1 kho vẫn còn 2
  • Mật khẩu: env BACKUP_PASSPHRASE (GitHub Secret) — KHÔNG bao giờ nằm cùng chỗ với file mã hoá

=> Muốn đọc được backup phải có ĐỒNG THỜI: file trên Drive + secret trên GitHub. Mất một trong hai
   thì kẻ lấy được cũng vô dụng; mất Firebase thì mình vẫn khôi phục đủ.

    python backup_vault.py              # sao lưu
    python backup_vault.py --khoi-phuc  # in ra JSON đã giải mã (để nạp lại tay)
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timezone

THU_MUC = "_BACKUP"
GIU_LAI = 7            # giữ 7 bản gần nhất mỗi kho, cũ hơn thì xoá


def _khoa(mat_khau: str, muoi: bytes) -> bytes:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=muoi, iterations=480000)
    return base64.urlsafe_b64encode(kdf.derive(mat_khau.encode("utf-8")))


def ma_hoa(du_lieu: dict, mat_khau: str) -> bytes:
    """Trả gói: [16 byte muối] + [dữ liệu đã mã hoá]. Muối ngẫu nhiên mỗi lần -> 2 bản backup khác nhau."""
    from cryptography.fernet import Fernet
    muoi = os.urandom(16)
    goi = Fernet(_khoa(mat_khau, muoi)).encrypt(json.dumps(du_lieu, ensure_ascii=False).encode("utf-8"))
    return muoi + goi


def giai_ma(raw: bytes, mat_khau: str) -> dict:
    from cryptography.fernet import Fernet
    return json.loads(Fernet(_khoa(mat_khau, raw[:16])).decrypt(raw[16:]).decode("utf-8"))


def _doc_firestore() -> dict:
    """Gom đúng 3 thứ không tái tạo được: key, kênh, cấu hình."""
    from google.cloud import firestore
    from google.oauth2 import service_account
    pid = os.environ.get("FIREBASE_PROJECT_ID_B")
    sa = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_B")
    if not (pid and sa and os.path.exists(sa)):
        raise SystemExit("❌ thiếu khoá project B")
    db = firestore.Client(project=pid,
                          credentials=service_account.Credentials.from_service_account_file(sa))
    ra = {"at": datetime.now(timezone.utc).isoformat(), "nguon": pid}
    for ten in ("gemini_keys", "render_channels", "render_config"):
        try:
            ra[ten] = [{"id": d.id, **(d.to_dict() or {})} for d in db.collection(ten).stream(timeout=60)]
        except Exception as e:
            print(f"   ⚠️ đọc {ten} lỗi: {str(e)[:60]}")
            ra[ten] = []
    return ra


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--khoi-phuc", action="store_true", help="giải mã bản mới nhất và in ra")
    a = ap.parse_args()

    mk = os.environ.get("BACKUP_PASSPHRASE", "")
    if not mk or len(mk) < 12:
        print("ℹ️ Chưa đặt BACKUP_PASSPHRASE (≥12 ký tự) — bỏ qua sao lưu.")
        return 0

    src = os.environ.get("AUTOPUBLISHER_SRC")
    if src and src not in sys.path:
        sys.path.insert(0, src)
    try:
        import storage as ST
    except ModuleNotFoundError:
        # 24/8 tối — `AUTOPUBLISHER_SRC` trỏ vào thư mục KHÔNG TỒN TẠI (job plan quên checkout repo
        # publish) nên hàm này chết mọi phiên, mà bước gọi có `|| true` nên workflow vẫn xanh: kho
        # key coi như không được sao lưu suốt thời gian đó, không ai biết. Nói thẳng ra thay vì để
        # traceback trôi trong log.
        print(f"🚨 KHÔNG SAO LƯU ĐƯỢC: không thấy module `storage` "
              f"(AUTOPUBLISHER_SRC={src or 'CHƯA ĐẶT'} — thư mục "
              f"{'không tồn tại' if src and not os.path.isdir(src) else 'thiếu storage.py'}). "
              f"Kiểm workflow đã checkout repo publish chưa.")
        return 1

    accs = ST.pool_accounts()
    if not accs:
        print("❌ không đọc được kho Drive nào — bỏ qua.")
        return 1

    if a.khoi_phuc:
        for acc in accs[:5]:
            try:
                drv = ST.account_drive(acc)
                bdir = drv.child_folder(drv.child_folder(acc["root"], "MM0-STORE"), THU_MUC)
                fs = drv.svc.files().list(q=f"'{bdir}' in parents and trashed=false",
                                          fields="files(id,name)", orderBy="name desc",
                                          pageSize=5).execute().get("files", [])
                if not fs:
                    continue
                import io as _io
                from googleapiclient.http import MediaIoBaseDownload
                buf = _io.BytesIO()
                dl = MediaIoBaseDownload(buf, drv.svc.files().get_media(fileId=fs[0]["id"]))
                while not dl.next_chunk()[1]:
                    pass
                d = giai_ma(buf.getvalue(), mk)
                print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in d.items()},
                                 ensure_ascii=False, indent=1))
                print(f"✅ Giải mã được bản {fs[0]['name']} từ kho {acc['name']}")
                return 0
            except Exception as e:
                print(f"   ⚠️ {acc.get('name')}: {str(e)[:70]}")
        print("❌ không tìm/giải mã được bản sao lưu nào.")
        return 1

    du_lieu = _doc_firestore()
    _n_key = len(du_lieu.get("gemini_keys", []) or [])
    _n_kenh = len(du_lieu.get("render_channels", []) or [])
    if _n_key == 0 and _n_kenh == 0:
        # 24/8 tối — SUÝT MẤT SẠCH KHO SAO LƯU. Log phiên 21:52Z: `📦 Gói sao lưu: 0 key · 0 kênh`.
        # Cất gói RỖNG đó lên kho thì nó thành bản MỚI NHẤT, và mấy dòng dưới đây sẽ **bỏ các bản cũ
        # vào thùng rác** để giữ đúng GIU_LAI bản. Sao lưu chạy mỗi phiên (~30-40'), nên chỉ vài giờ
        # là mọi bản sao lưu THẬT bị đẩy ra rìa rồi xoá — đúng thứ cái vault này sinh ra để chống.
        # Nguyên nhân gói rỗng: A và B đều cạn hạn mức nên `_doc_firestore()` đọc được 0 bản ghi.
        # Đọc không ra dữ liệu KHÔNG PHẢI là "dữ liệu rỗng" (luật 7.bm/7.cg) — càng không phải lý do
        # để ghi đè bản tốt.
        print("🛑 KHÔNG CẤT: gói sao lưu rỗng (0 key · 0 kênh) — gần như chắc chắn do Firestore đang "
              "cạn hạn mức, không phải do kho thật sự trống. Cất gói rỗng sẽ ĐẨY CÁC BẢN TỐT RA "
              "RÌA rồi xoá. Giữ nguyên bản cũ, thử lại phiên sau.")
        return 1
    goi = ma_hoa(du_lieu, mk)
    ten = "vault-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M") + ".enc"
    print(f"📦 Gói sao lưu: {_n_key} key · {_n_kenh} kênh · {len(goi)/1024:.1f}KB (đã mã hoá)")

    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), ten)
    with open(tmp, "wb") as f:
        f.write(goi)

    ok = 0
    for acc in accs[:6]:                      # thử 6 kho, cần 3 bản là đủ
        if ok >= 3:
            break
        try:
            drv = ST.account_drive(acc)
            store = drv.child_folder(acc["root"], "MM0-STORE")
            bdir = drv.child_folder(store, THU_MUC)
            drv.upload_file(bdir, tmp, ten)
            ok += 1
            print(f"   ✅ đã cất ở kho {acc['name']}")
            cu = drv.svc.files().list(q=f"'{bdir}' in parents and trashed=false",
                                      fields="files(id,name)", orderBy="name desc",
                                      pageSize=50).execute().get("files", [])
            for f in cu[GIU_LAI:]:
                drv.svc.files().update(fileId=f["id"], body={"trashed": True}).execute()
        except Exception as e:
            print(f"   ⚠️ kho {acc.get('name')} hụt: {str(e)[:70]}")
    try:
        os.remove(tmp)
    except Exception:
        pass
    print(f"\n{'✅' if ok >= 2 else '⚠️'} Sao lưu xong ở {ok} kho độc lập "
          f"(cần ≥2 để an toàn). Muốn đọc phải có CẢ file lẫn BACKUP_PASSPHRASE.")
    return 0 if ok >= 2 else 1


if __name__ == "__main__":
    sys.exit(main())
