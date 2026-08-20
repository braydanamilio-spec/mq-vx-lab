# 🏗️ ARCHITECTURE.md — Kiến trúc 3 project Firestore

> Gộp từ `SHARD_SETUP.md` + `SHARD_C_SETUP.md` (20/8) — trước đây tách 2 file, trùng nội dung, khó tra.
> **Nguyên tắc cốt lõi: 1 project cạn quota, 2 project kia VẪN CHẠY.**

---

## 1. Ba project — ai giữ cái gì

| Project | ID | Giữ | Ai ghi |
|---------|-----|-----|--------|
| **A** | `mm0-auto-publisher` | dashboard, login, settings, connections, storage_accounts, gemini_keys | Dashboard + Worker |
| **B** | `mm0-shard-b` | **RENDER**: render_config, render_channels, render_jobs, render_topics, trend_scout | Pipeline render |
| **C** | `mm0-shard-c` | **PUBLISH**: yt_queue, social_queue, videos, counters, quota | Publisher |

**Vì sao tách**: `render_jobs` đổi trạng thái liên tục khi render + dashboard nghe realtime → nặng nhất.
Trước đây dồn hết vào A → cạn quota là **chết cả hệ**. Giờ render nghẽn không ảnh hưởng đăng bài.

📍 Cả 3 đều ở **asia-southeast1**, Firestore NATIVE.

---

## 2. Thông tin kết nối

### Project B — RENDER
- Service account: `mm0-pipeline@mm0-shard-b.iam.gserviceaccount.com` (role `datastore.user`)
- GitHub secrets (repo `braydanamilio-spec/mq-vx-lab`): `GCP_SA_KEY_B`, `FIREBASE_PROJECT_ID_B=mm0-shard-b`
- Rules: `render_jobs` cho phép đọc/ghi (job = metadata **không nhạy cảm**, hệ 1 người dùng).
  KHÔNG dùng anon auth vì Identity Platform đòi bật billing.
- Web config (public, cho dashboard):
  ```
  projectId: mm0-shard-b
  appId: 1:893314701198:web:f261226c5be8e57b14f6df
  apiKey: AIzaSyDTIlSNoApulSCCozwKTCbAelu5gYaoRFs
  authDomain: mm0-shard-b.firebaseapp.com
  messagingSenderId: 893314701198
  storageBucket: mm0-shard-b.firebasestorage.app
  ```

### Project C — PUBLISH
- Project number: 443486296227
- Service account: `mm0-publisher@mm0-shard-c.iam.gserviceaccount.com` (role `datastore.user`)
- GitHub secrets: `GCP_SA_KEY_C`, `FIREBASE_PROJECT_ID_C=mm0-shard-c`
- Rules: **KHÓA HẲN** (`allow read,write: if false`) — C chứa **OAuth token** (connections), tuyệt đối
  không mở như B. Service account bypass rules nên publisher vẫn chạy bình thường.
- Web config (public, cho dashboard):
  ```
  projectId: mm0-shard-c
  appId: 1:443486296227:web:e5607766466c3bf6cd8716
  apiKey: AIzaSyAVEj7RUMx5jRtxN0o2eOzh4r7Pjjm-zBk
  authDomain: mm0-shard-c.firebaseapp.com
  messagingSenderId: 443486296227
  storageBucket: mm0-shard-c.firebasestorage.app
  ```

---

## 3. Code định tuyến ở đâu

| Nơi | Hàm/cờ | Ghi chú |
|-----|--------|---------|
| `firestore_bridge._db_jobs()` | → B | mọi thao tác `render_jobs` |
| `firestore_bridge._db_meta()` | → B khi `SHARD_META=1` | config·channels·topics·requests |
| `firestore_state.self.db` | → A | shared (settings/connections) |
| `firestore_state.self.pub` | → C khi `SHARD_PUBLISH=1` | yt_queue·social_queue·videos |
| `auto_enqueue.py` | đọc render_jobs **B** → ghi yt_queue **C** | cầu nối render→publish |

**Backward-compatible**: thiếu creds B/C thì tự về A. Muốn TẮT shard → bỏ secret tương ứng.

⚠️ **Còn tồn đọng**: `gemini_keys` và `storage_accounts` **vẫn ở A** dù docstring `_db_meta()` nói là B.
Chưa rõ cố ý hay sót. **Đừng đổi khi chưa kiểm chứng dữ liệu thật có ở B chưa** — đổi ẩu là chết
toàn bộ key Gemini, cả hệ ngừng viết.

---

## 4. Dashboard đọc cả 3

- `render_jobs`: đọc **CẢ A + B rồi gộp** → không mất video cũ, khỏi phải migrate.
- Đọc **load-once + refresh khi quay lại tab** (không realtime) cho các collection đổi chậm
  (storage_accounts, channels, fb_pages) → đây là fix quan trọng sau 2 lần cạn quota.
- Listener realtime nào cũng phải có `limit()` — xem bài học ở [`QC_STANDARD.md`](QC_STANDARD.md).

---

## 5. Quy tắc chống nghẽn quota

1. Render đọc/ghi **chỉ B**, publish **chỉ C** → không giẫm chân nhau.
2. Dashboard: load-once + cache, **mọi listener phải có `limit()`**.
3. Truy vấn trong vòng lặp phải có giới hạn (bài học `health_guardian` đọc toàn bộ lịch sử mỗi giờ).
4. **TUYỆT ĐỐI không `gh workflow run` để "test"** — đốt quota thật của hệ đang chạy.
   Đây là rule cứng, đã vi phạm 2 lần và gây sập pipeline. Đợi cron tự chạy rồi đọc log.
