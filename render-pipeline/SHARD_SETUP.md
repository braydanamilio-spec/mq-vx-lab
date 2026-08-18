# 🔀 FIRESTORE SHARD — Project B (giảm tải quota project A)

## Mục tiêu
Chuyển collection **`render_jobs`** (nặng nhất: đổi trạng thái liên tục khi render + dashboard nghe realtime)
sang **Project B** → project A (mm0-auto-publisher) nhẹ hẳn, gấp đôi quota free đọc.

## Project B — ĐÃ DỰNG (18/8, qua firebase CLI + REST token)
- Project ID: **mm0-shard-b**
- Firestore: (default) @ asia-southeast1
- Service account (pipeline): `mm0-pipeline@mm0-shard-b.iam.gserviceaccount.com` (role datastore.user)
- GitHub secrets (repo braydanamilio-spec/mq-vx-lab): `GCP_SA_KEY_B` (SA JSON), `FIREBASE_PROJECT_ID_B=mm0-shard-b`
- Web config (public, cho dashboard):
```
projectId: mm0-shard-b
appId: 1:893314701198:web:f261226c5be8e57b14f6df
apiKey: AIzaSyDTIlSNoApulSCCozwKTCbAelu5gYaoRFs
authDomain: mm0-shard-b.firebaseapp.com
messagingSenderId: 893314701198
storageBucket: mm0-shard-b.firebasestorage.app
```

## Kiến trúc shard (backward-compatible: chưa cấu hình B thì vẫn dùng A)
- **Pipeline** (`firestore_bridge.py`): thêm `_db_jobs()` → client Project B nếu có `FIREBASE_PROJECT_ID_B`+creds, không thì `_db()` (A). Route: `new_job`, `update_job`, `count_done`, `find_by_drive` (mọi thao tác render_jobs).
- **Workflow**: ghi `GCP_SA_KEY_B` ra file + set `GOOGLE_APPLICATION_CREDENTIALS_B` + `FIREBASE_PROJECT_ID_B`.
- **Dashboard**: init app Firebase thứ 2 (web config B) + đăng nhập ẩn danh B → listener/ghi `render_jobs` trỏ B. Fallback A nếu B chưa sẵn.
- **Rules B**: render_jobs cho user đã auth đọc/ghi (single-user, job = metadata không nhạy cảm). Pipeline (SA) bypass rules.

## Trạng thái wiring
- [x] Provision Project B + creds + secrets
- [ ] Rules B + anon auth
- [ ] Pipeline route render_jobs → B
- [ ] Workflow pass creds B
- [ ] Dashboard đọc render_jobs từ B
