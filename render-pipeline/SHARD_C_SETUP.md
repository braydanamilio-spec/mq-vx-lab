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
- [ ] **WIRING (làm khi A reset, 1 lượt):** publisher (`MM0-AutoPublisher/src/*`) route yt_queue/connections/videos → C; workflow publish pass creds C; dashboard init app Firebase thứ 3 (config C) đọc queue/connections từ C.
- [ ] Migrate dữ liệu publish A→C (đọc A đúng 1 lượt).

## Nguyên tắc chống nghẽn (xem [[mm0-no-quota-waste]])
Render đọc/ghi CHỈ B, publish CHỈ C, dashboard load-once cả 3 + cache dự phòng → 1 project cạn, 2 cái kia vẫn chạy.
