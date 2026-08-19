# MM0 — BẮT ĐẦU TỪ ĐÂY (Handoff cho phiên mới)

> Đọc file này TRƯỚC. Nó nói hệ thống là gì, đọc file nào tiếp, đang làm gì, deploy sao.
> Cập nhật: 19/8/2026 (sau đợt sharding 3-project + Wave 3 + round-cap rotation).

## 1. Dự án là gì (1 dòng)
100% FREE, máy tắt vẫn chạy 24/7: **26 kênh USA** tự sản xuất video (data-race + 5 motif đồ hoạ + 11 tài liệu điện ảnh) → render trên **GitHub Actions** → đẩy **Google Drive** → **MM0-AutoPublisher** tự đăng YouTube/FB/IG.

## 2. Đọc theo thứ tự
1. **`render-pipeline/CHANNEL_METHODS.md`** — method + repo TỪNG kênh + **kiến trúc 3-project Firestore** (đọc kỹ phần này trước khi đụng bất kỳ collection nào).
2. **`render-pipeline/ERROR_PLAYBOOK.md`** — cơ chế TỰ CHỮA LỖI + quy trình diagnose lỗi mới + rule tiết kiệm quota (KHÔNG test tay bằng cách kích render/health-check lặp).
3. **`render-pipeline/PIPELINE_RULES.md`** — bug-log chi tiết + rule (mỗi bug/đổi mới ghi ở đây, đọc §7 để biết lịch sử các lỗi nghiêm trọng đã gặp).
4. **`render-pipeline/SHARD_SETUP.md`** + **`SHARD_C_SETUP.md`** — chi tiết setup Project B (render) và C (publish).
5. Claude memory (máy này): `~/.claude/projects/.../memory/MEMORY.md` — mục lục + context nhanh, đặc biệt `mm0-3project-isolation.md`.

## 3. Repo + Firestore (ai chứa gì)
- **mq-vx-lab** (PUBLIC) = repo NÀY: `render-pipeline/` (não Gemini + orchestrator) · `engine-remotion/` (engine vẽ) · `.github/workflows/` (cron render **+ bản THẬT của publish/cleanup/stats**, xem §6).
- **mm0-auto-publisher** (PUBLIC): `dashboard/index.html` (web quản lý, router `_appFor()` chọn A/B/C theo collection) · `connect-worker/src/worker.js` (Cloudflare OAuth+Drive, chỉ biết Project A) · `src/*.py` (code publish, nhưng cron của repo NÀY đã tắt — xem §6).
- **3 Firestore project độc lập** (chống 1 project cạn quota kéo cả hệ đứng — đã xảy ra thật 18-19/8):
  | Project | Chứa | Ai ghi |
  |---|---|---|
  | **A** `mm0-auto-publisher` | settings/connections/channels/fb_pages/links/gemini_keys(nhạy cảm)/storage_accounts(Worker cần) | dashboard + connect-worker |
  | **B** `mm0-shard-b` | render_config/channels/topics/requests/jobs | render pipeline |
  | **C** `mm0-shard-c` | videos/counters/quota/yt_queue/social_queue | publisher |

## 4. Luồng chạy (1 dòng)
`content_brain.py` (Gemini viết, chuẩn QC ≥90, có guardrail chống bịa nguồn cho chủ đề nhạy — luật/tài chính) → `datastory_ci.py` (data/ảnh CC0 Vision-verify khớp nội dung/edge-tts karaoke) → `engine-remotion` render MP4 1080p → `run_render.py` enqueue → Drive (kho tự cân bằng tải, xoay theo tên kênh) → AutoPublisher đăng.

## 5. Điểm vào code chính
- **`render-pipeline/run_render.py`** — orchestrator. `--gate` (kiểm nhanh có chạy không) · `--plan` (điều phối: health-check + re-render + xuất TOÀN BỘ danh sách kênh không phân trang) · `--channel NAME` (render 1 kênh, vòng lặp tới đủ **round-cap** hoặc target/quota/giờ).
- **`render-pipeline/firestore_bridge.py`** — `_db()`=A · `_db_jobs()`=B (render_jobs) · `_db_meta()`=B nếu `SHARD_META=1` else A (config/channels/topics/requests). gemini_keys LUÔN `_db()` (A, không bao giờ shard).
- **`.github/workflows/render_cron.yml`** — 2 job: `plan` + `render` (matrix max-parallel:18). Cron `*/10` + giờ mẻ 0/4/8/12/16/20 UTC.

## 6. ⚠️ Đọc kỹ — 2 điểm dễ sập bẫy nhất
- **Workflow trùng tên giữa 2 repo, chỉ 1 bản CHẠY THẬT.** `mq-vx-lab/.github/workflows/{publish,cleanup,publish_social,stats}.yml` (public runner, checkout code private lúc chạy) mới là bản có cron LIVE. Bản y hệt ở `mm0-auto-publisher/.github/workflows/` đã TẮT cron có chủ đích (chỉ `workflow_dispatch` để test tay, có comment "⛔ CRON ĐÃ CHUYỂN sang repo public" trong file). **Sửa env/secret của publish PHẢI sửa ở `mq-vx-lab`**, và luôn `gh run list -R braydanamilio-spec/<repo> --workflow=X.yml --limit 5` kiểm bản nào thực sự chạy gần đây trước khi tin đã xong.
- **Round-cap rotation.** Mặc định mỗi kênh làm tối đa **10 long / 30 short** rồi nhường slot GitHub Actions matrix cho kênh khác (check SAU khi video hoàn tất, không cắt ngang) — target tổng (100L/300S) vẫn là đích, chỉ đạt dần qua nhiều phiên thay vì dồn 1 phiên. Đổi ở dashboard "🔁 Xoay vòng" hoặc `render_config.round_long/round_short` (0 = không giới hạn, về hành vi cũ).

## 7. Đang làm gì (26 kênh, cập nhật khi đổi)
- **10 kênh data-race gốc** (DATARACE/STATEWARS/MONEYMOVES/POWERPLAY/GRIDIRON/SCREENKINGS/PAYCHECK/BODYUSA/RIDEUSA/EATSUSA) — target 100L/300S, ổn định lâu.
- **5 kênh motif Wave 1** (GUESSUSA/MAPPEDUSA/RANKEDUSA/SCALEDUSA/THENNOWUSA) — short-only, engine riêng.
- **5+6 kênh tài liệu Wave 2+3** (COSMOS/THEDEEP/WHYUSA/EMPIREUSA/UNSOLVED + GRIDUSA/RULEDUSA/VAULTUSA/LEDGERUSA/SIGNALUSA/MARGINUSA) — short-only, engine Cinematic chung, Wave 3 có guardrail chống bịa nguồn riêng (RULEDUSA/LEDGERUSA rủi ro cao nhất).
- Cơ chế đã có: round-cap rotation công bằng · chia Drive tự cân bằng 67+ kho + reservation chống tràn · chia key round-robin + đếm quota req_today · rate-limit tự chờ+đổi key · dừng-theo-clip (không cắt ngang) · dọn job ma · 2 mức cảnh báo key chết (72h/7d, phân biệt tạm/vĩnh viễn) · target/bulk-edit · dashboard 3-app router (A/B/C) · QC ảnh Vision-verify + QC kỹ thuật ffprobe sau render.
- **Auto-publish**: có sẵn code (`auto_enqueue.py`), mặc định TẮT theo từng kênh — cần user tự Kết nối YouTube (OAuth) rồi bật nút 🟢 Auto-đăng mới chạy thật.
- **CÒN THIẾU:** chưa có video nào render xong cho 6 kênh Wave 3 (mới seed 19/8) — cần theo dõi chất lượng đầu ra khi có. Round-cap chưa xác nhận bằng dữ liệu live phiên đầy đủ đầu tiên (code đã verify kỹ, chờ dữ liệu tự nhiên).

## 8. Deploy / validate
- Dashboard: `cd MM0-AutoPublisher/dashboard && firebase deploy --only hosting --project mm0-auto-publisher`. Validate JS: trích `<script type="module">` → `node --check`.
- Worker: `cd MM0-AutoPublisher/connect-worker && npx wrangler deploy`.
- Pipeline: `git push` (chạy trên Actions). Validate: `python3 -c "import ast; ast.parse(open('f.py').read())"` + `python3 -c "import yaml; yaml.safe_load(open('f.yml'))"` cho MỌI file trước khi push (workflow production, không có cơ hội sửa nhanh nếu sai cú pháp giữa cron).
- Firestore admin (tạo project/rules/SA key): dùng token cache firebase CLI (`~/.config/configstore/firebase-tools.json`), refresh bằng `firebase projects:list` nếu 401.
- LIVE: dashboard https://mm0-auto-publisher.web.app · worker https://mm0-connect.adisondurham-ef1.workers.dev

## 9. AN TOÀN (bất di bất dịch)
- KHÔNG commit secret. Moat = GitHub Secret `GEMINI_SYSTEM_PROMPT` + local `PROMPT_SECRET.txt` (gitignore).
- Xóa CHỈ đụng VIDEO (→Trash Drive 30 ngày, có nút "Đổ thùng rác" xoá vĩnh viễn thu hồi dung lượng — luôn TAY, không tự động), KHÔNG xóa method/repo/brand/config.
- **KHÔNG test tay bằng cách kích render/health-check lặp lại** — đã từng đốt 92K reads làm cạn Firestore A 1 lần (18/8). Verify bằng đọc code + log run cũ có sẵn.
- 100% free + không spam (mỗi video 1 chủ đề, ≥90 điểm) + không vi phạm policy.
- Báo cáo NGẮN gọn, tiết kiệm token (theo ý user).
