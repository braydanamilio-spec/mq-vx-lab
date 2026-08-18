# MM0 — Sổ tay Method & Repo (đọc lại là làm tiếp được)

> Mục tiêu: 100% FREE, máy tắt vẫn chạy 24/7, tự sản xuất video "cinematic data-story"
> cho các kênh USA → render trên GitHub Actions → đẩy Google Drive → MM0-AutoPublisher tự đăng.

## Repo (ai chứa gì)
| Repo | Loại | Chứa |
|---|---|---|
| **mq-vx-lab** | PRIVATE | `render-pipeline/` (não Gemini, QC, orchestrator) · `engine-remotion/` (engine vẽ video) · `.github/workflows/` (cron render) · brand/method docs |
| **mm0-auto-publisher** | PUBLIC | `dashboard/` (web quản lý) · `connect-worker/` (Cloudflare OAuth+Drive) · publisher (tự đăng YT/FB) |

Moat (bí mật) nằm ở GitHub Secret `GEMINI_SYSTEM_PROMPT` + local `PROMPT_SECRET.txt` (gitignore). KHÔNG đẩy public.

## Luồng chạy (1 dòng)
`content_brain.py` (Gemini viết kịch bản, chuẩn ≥90) → `datastory_ci.py` (dựng data + ảnh Openverse CC0 + edge-tts karaoke) → `engine-remotion` render MP4 1080p → `run_render.py` enqueue → Drive → AutoPublisher đăng.

## Method CHUNG hiện tại (mọi kênh đang xài)
- **Engine**: bar-chart-race — `engine-remotion/src/BarChartRace.tsx` (short 9:16) + `RaceLong.tsx` (long 16:9).
- **Nội dung**: 1 video = 1 chủ đề/pillar mạch lạc, KHÔNG trộn race lạ nhau.
- **Chuẩn**: long ≥10', short <3'; QC điểm ≥90 (chưa đạt thì VIẾT LẠI, không hạ chuẩn); ảnh đúng khổ (short=tall, long=wide) + không tràn/che.
- **Render free**: repo public = phút Actions không giới hạn; render swiftshader.
- **Định dạng/kênh**: mỗi kênh 1 long + 3 short (target chỉnh trong dashboard).

## Per-channel (repo = mq-vx-lab, method = data-race, trừ khi ghi khác)
| Kênh | Handle | Màu | Niche | Method riêng / kế hoạch |
|---|---|---|---|---|
| 📊 DATA RACE | @dataracehq | #F5B301 | Tiền & giàu US (tỷ phú, thuế, chênh lệch thu nhập) | data-race (gốc, ổn nhất) |
| 🗺️ STATE WARS | @statewarsusa | #E4562B | 50 bang so kè (dân số, GDP, tội phạm, nhà) | data-race → **tương lai: engine BẢN ĐỒ** |
| 💵 MONEY MOVES | @moneymovesusa | #2FA84F | Chi phí sống US (thuê nhà, xăng, giá) | data-race |
| 🏢 POWER PLAY | @powerplayhq | #22D3EE | Công ty/brand US (vốn hóa, user, EV) | data-race |
| 🏈 GRID IRON | @gridironusa | #FB923C | Tiền thể thao (lương NFL/NBA, vé, cúp) | data-race |
| 🎬 SCREEN KINGS | @screenkingshq | #EC4899 | Giải trí US (doanh thu phòng vé, stream, nhạc) | data-race |
| 💼 PAYCHECK | @paycheckusa | #2DD4BF | Việc & lương US (nghề lương cao, thất nghiệp) | data-race |
| 🫀 BODY USA | @bodyusahq | #7C5CFF | Sức khỏe/lối sống US (béo phì, tuổi thọ, chi tiêu) | data-race |
| 🚗 RIDE USA | @rideusahq | #38BDF8 | Xe US (doanh số brand, EV vs xăng, bán tải) | data-race |
| 🍔 EATS USA | @eatsusahq | #A3E635 | Đồ ăn/fast-food US (chuỗi, calo, giá) | data-race |

> Kế hoạch phân biệt hình ảnh 10 kênh (mỗi kênh 1 motif riêng, không lặp) = phase sau. STATEWARS đi trước với engine bản đồ.

## 🛠️ TỰ CHỮA LỖI
Cơ chế tự chữa lỗi + quy trình diagnose + lỗi đã gặp: **`ERROR_PLAYBOOK.md`**. Bug-log chi tiết: `PIPELINE_RULES.md`.

## ⚠️ QUY TẮC XÓA (bất di bất dịch)
**Dọn/xóa CHỈ đụng VIDEO.** KHÔNG bao giờ xóa: method (.py/.tsx/.md), repo, brand kit, config kênh, kịch bản/topic đã lưu.
→ Sau này luôn có thể quay lại làm tiếp. Video xóa = vào Trash Drive (khôi phục 30 ngày), không hard-delete.

## Quay lại làm tiếp (quickstart)
1. `git pull` cả 2 repo. Repair local nếu cần (node_modules/venv/ffmpeg) — xem `mm0-env-setup`.
2. Mở dashboard → tab Render Studio: chỉnh kênh/target → bấm chạy, hoặc để cron tự chạy.
3. Cần đổi cách làm 1 kênh: sửa engine/`datastory_ci.py`; nội dung: sửa `content_brain.py` + Secret prompt.
4. Bug/đổi mới → ghi vào `PIPELINE_RULES.md`. Đổi cấu trúc kênh/method → cập nhật file NÀY.
