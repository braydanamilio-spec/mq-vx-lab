# 🟣 PROJECT C — PUBLISH (tách đăng bài độc lập)

Mục tiêu: **đăng bài chạy trên project riêng** → render (B) hay dashboard cạn quota cũng KHÔNG ảnh hưởng publish. 3 project độc lập:
- **A** `mm0-auto-publisher` = dashboard/login/settings
- **B** `mm0-shard-b` = RENDER (config·channels·keys·render_jobs)
- **C** `mm0-shard-c` = PUBLISH (yt_queue·social_queue·connections·videos·quota)

## Project C — ĐÃ DỰNG (19/8, qua firebase CLI + REST token)
- Project ID: **mm0-shard-c** (number 443486296227)
- Firestore: (default) @ **asia-southeast1** — NATIVE
- Service account (publisher): `mm0-publisher@mm0-shard-c.iam.gserviceaccount.com` (role `datastore.user`)
- GitHub secrets (repo `braydanamilio-spec/mq-vx-lab`): `GCP_SA_KEY_C` (SA JSON), `FIREBASE_PROJECT_ID_C=mm0-shard-c`
- Web config (public, cho dashboard):
```
projectId: mm0-shard-c
appId: 1:443486296227:web:e5607766466c3bf6cd8716
apiKey: AIzaSyAVEj7RUMx5jRtxN0o2eOzh4r7Pjjm-zBk
authDomain: mm0-shard-c.firebaseapp.com
messagingSenderId: 443486296227
storageBucket: mm0-shard-c.firebasestorage.app
```
- Rules: **KHÓA** (`allow read,write: if false`) — C chứa OAuth token (connections) nên KHÔNG public như B. SA pipeline bypass rules → publisher vẫn ghi/đọc bình thường. Dashboard đọc C sẽ finalize ở bước wiring (đọc load-once + rules cho collection không nhạy cảm).

## Trạng thái
- [x] Provision project + Firestore + SA + IAM + secrets + web config + rules khóa
- [x] **CODE WIRING XONG (gated, mặc định TẮT = A y cũ):**
  - Render: `firestore_bridge._db_meta()` route config/channels/keys/storage/topics/requests → B khi `SHARD_META=1`.
  - Publish: `firestore_state` tách `self.db`(A shared) vs `self.pub`(C owned) khi `SHARD_PUBLISH=1`; `auto_enqueue` đọc render_jobs từ B, ghi yt_queue vào C.
  - Secrets B+C đã nạp cả 2 repo (mq-vx-lab + mm0-auto-publisher); workflow ghi creds + cờ.
- [ ] **KHI A RESET (~14h VN) — chỉ 3 bước:**
  1. Chạy migrate: repo mq-vx-lab → workflow_dispatch `migrate_to_shards.py` (đọc A 1 lượt → B+C). Hoặc local nếu có creds A.
  2. Bật cờ: `gh variable set SHARD_META -R braydanamilio-spec/mq-vx-lab -b 1` và `gh variable set SHARD_PUBLISH -R braydanamilio-spec/mm0-auto-publisher -b 1`.
  3. Dashboard: thêm app Firebase thứ 3 (config C) đọc videos/yt_queue/counters từ C (hiện đọc A) — display, làm sau khi test.
- Shared (settings/connections/channels/storage_reservations) GIỮ ở A → Worker/dashboard ghi A không đổi.

## Nguyên tắc chống nghẽn (xem [[mm0-no-quota-waste]])
Render đọc/ghi CHỈ B, publish CHỈ C, dashboard load-once cả 3 + cache dự phòng → 1 project cạn, 2 cái kia vẫn chạy.
