# MM0 — BẮT ĐẦU TỪ ĐÂY (Handoff cho phiên mới)

> Đọc file này TRƯỚC. Nó nói hệ thống là gì, đọc file nào tiếp, đang làm gì, deploy sao.

## 1. Dự án là gì (1 dòng)
100% FREE, máy tắt vẫn chạy 24/7: tự sản xuất video "cinematic data-story" (bar-chart-race) cho **10 kênh USA** → render trên **GitHub Actions** → đẩy **Google Drive** → **MM0-AutoPublisher** tự đăng YouTube/FB.

## 2. Đọc theo thứ tự
1. **`render-pipeline/CHANNEL_METHODS.md`** — method + repo TỪNG kênh + dự án.
2. **`render-pipeline/ERROR_PLAYBOOK.md`** — cơ chế TỰ CHỮA LỖI (bảng self-heal) + quy trình diagnose lỗi mới.
3. **`render-pipeline/PIPELINE_RULES.md`** — bug-log chi tiết + rule (mỗi bug/đổi mới ghi ở đây).
4. Claude memory (máy này): `~/.claude/projects/.../memory/MEMORY.md` — mục lục + context nhanh.

## 3. Repo (ai chứa gì)
- **mq-vx-lab** (PRIVATE) = repo NÀY: `render-pipeline/` (não Gemini + orchestrator) · `engine-remotion/` (engine vẽ) · `.github/workflows/` (cron render).
- **mm0-auto-publisher** (PUBLIC): `dashboard/index.html` (web quản lý) · `connect-worker/src/worker.js` (Cloudflare OAuth+Drive) · `src/*.py` (tự đăng). Chi tiết deploy: memory `mm0-repo-methods`.

## 4. Luồng chạy (1 dòng)
`content_brain.py` (Gemini viết, chuẩn QC ≥90) → `datastory_ci.py` (data + ảnh CC0 + edge-tts karaoke) → `engine-remotion` render MP4 1080p → `run_render.py` enqueue → Drive `_QUEUE/long|short` (kèm thumbnail + sidecar.json title/desc/tag) → AutoPublisher đăng.

## 5. Điểm vào code chính
- **`render-pipeline/run_render.py`** — orchestrator. Chế độ: `--gate` (kiểm nhanh có chạy không) · `--plan` (điều phối: health-check + re-render + xuất danh sách kênh) · `--channel NAME` (render 1 kênh, VÒNG LẶP tới đủ target/quota/giờ) · không cờ = tuần tự (fallback).
- **`render-pipeline/key_manager.py`** — chọn key: chia đều round-robin + ưu tiên key còn quota (req_today) + né key vừa mở chặn.
- **`.github/workflows/render_cron.yml`** — 2 job: `plan` (điều phối) + `render` (matrix 10 luồng song song). Cron `*/10` + giờ mẻ 0/4/8/12/16/20 UTC (6 phiên/ngày). Cache node_modules + Chrome.

## 6. Đang làm gì (cập nhật khi đổi)
- 10 kênh render tự động tới target (mặc định 100 long / 300 short/kênh). Vòng lặp A-Z: chưa đủ target → phiên sau tự chạy.
- Cơ chế đã có: 10 luồng song song · chia Drive đều 33 kho + reservation chống tràn · chia key đều + đếm quota req_today · rate-limit tự chờ+đổi key (không tính Lỗi) · dừng-theo-clip · dọn job ma · 2 mức cảnh báo key chết (72h/7d) · target/bulk-edit · thu gọn UI + avatar brand.
- CÒN: phân biệt hình ảnh 10 kênh (STATEWARS=engine bản đồ) — phase sau. Upload là pipeline RIÊNG (chưa nối YouTube thật).

## 7. Deploy / validate
- Dashboard: `cd MM0-AutoPublisher/dashboard && firebase deploy --only hosting --project mm0-auto-publisher`. Validate: trích `<script>` → `node --check`.
- Worker: `cd MM0-AutoPublisher/connect-worker && npx wrangler deploy`. Validate: `node --check` (.mjs).
- Pipeline: chỉ `git push` (chạy trên Actions). Validate: `python3 -m py_compile ...` + `yaml.safe_load` workflow.
- LIVE: dashboard https://mm0-auto-publisher.web.app · worker https://mm0-connect.adisondurham-ef1.workers.dev

## 8. AN TOÀN (bất di bất dịch)
- KHÔNG commit secret. Moat = GitHub Secret `GEMINI_SYSTEM_PROMPT` + local `PROMPT_SECRET.txt` (gitignore).
- Xóa CHỈ đụng VIDEO (→Trash 30 ngày), KHÔNG xóa method/repo/brand/config.
- 100% free + không spam (mỗi video 1 chủ đề, ≥90 điểm) + không vi phạm policy.
- Báo cáo NGẮN gọn, tiết kiệm token (theo ý user).
