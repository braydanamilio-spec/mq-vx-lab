# MM0 — Cơ chế TỰ CHỮA LỖI (Error Playbook)

> Triết lý: **mọi lỗi → thử tự chữa (retry/đổi key/nhảy kho)** → không chữa được thì **cô lập** (1 kênh/1 video lỗi KHÔNG giết cả mẻ) + **cảnh báo** (email/dashboard). Máy tắt vẫn chạy 24/7, ít cần người can thiệp.

## 1. Các LỚP tự chữa (đang chạy)
| Lỗi | Tự chữa thế nào | Chỗ code |
|---|---|---|
| **Render 1 video lỗi** | make_long thử lại `4 race → 2 race`; make_video thử 2 lần | `run_render.run_one` |
| **QC < 90 điểm** | viết lại tối đa `MAX_TRIES=3`, phải ≥ `MIN_SCORE=90` (không hạ chuẩn) | `content_brain.generate` |
| **Key 429 / quota / 403 / denied / permission** | → `RateLimited` → **đổi key kế** (ưu tiên key lâu chưa xài, né key vừa mở chặn) | `key_manager.write_story`, `content_brain.generate` |
| **Giới hạn PHÚT vs quota NGÀY** | phút → nghỉ **90s**; ngày/403 → nghỉ **90 phút** (cooldown thích ứng) | `key_manager._cool` |
| **Cả loạt key dính giới hạn phút** | chờ **65s** (>60s reset) rồi thử lại 1 vòng, thay vì fail ngay | `key_manager.write_story` (2 vòng) |
| **Key chết thật** | render bỏ qua; health-check re-test mỗi ~20h → **tự mở lại** nếu Google bỏ chặn | `firestore_bridge.read_keys` + health-check |
| **Key chết quá lâu** | 2 mức: ⚠️ >72h (theo dõi) · 🔴 >7 ngày (email THAY) | `run_render.plan_mode` |
| **Kho Drive đầy/lỗi upload** | nhảy kho kế (ranked theo free); reservation chia sẻ chống tràn khi 10 luồng | `enqueue.py`, `storage.ranked_accounts` |
| **Kho tổng gần đầy (>90%)** | NGỪNG mẻ + email (tránh phình/lỗi ghi) | `run_render.plan_mode` guard |
| **1 kênh lỗi (kể cả SystemExit)** | `except BaseException` → cô lập, kênh khác vẫn chạy; matrix `fail-fast:false` | `run_render`, `render_cron.yml` |
| **Job MA (kẹt "đang chạy" >6h)** | tự đánh dấu failed → dọn | `dashboard __staleClean` |
| **404 model** | tự dò/hạ model khả dụng cho key | `content_brain._pick_model` |
| **Xóa Drive sai kho/thiếu quyền** | dò đúng kho chủ file rồi thử lại; báo email kho cần kết nối lại | `worker.apiFileAction` |

## 2. Quy trình DIAGNOSE lỗi MỚI (khi tự chữa chưa cover)
1. **Dashboard** #render → banner "⚠️ N lỗi MỚI" + message gần nhất (hoặc email cảnh báo).
2. **Đọc log CI**: `gh run view <RID> -R braydanamilio-spec/mq-vx-lab --log | grep -iE "lỗi|error|Traceback|429|403|Tự thử lại vẫn lỗi"`.
3. **Phân loại gốc**: (a) MÔI TRƯỜNG (thiếu binary/setup) · (b) API (key/quota/model) · (c) LOGIC (bug code) · (d) SONG SONG (burst/tràn/đua).
4. **Fix tại GỐC + thêm self-heal** để lần sau tự phục hồi (đừng chỉ vá triệu chứng).
5. **Ghi** vào `PIPELINE_RULES.md` (bug-log) + cập nhật bảng trên nếu thêm lớp mới.

## 3. Lỗi ĐÃ GẶP + gốc (tra nhanh; chi tiết ở PIPELINE_RULES.md)
- `ffprobe not found` → bug `--gate` chạy render trước khi cài ffmpeg. Fix dispatch `--gate`.
- `PAYCHECK 0 video` → giới-hạn-PHÚT + cooldown 90' quá dài → đói key. Fix cooldown thích ứng + chờ-thử-lại.
- `403 denied access` → project bị chặn; không rotate. Fix coi như key hỏng → đổi key.
- `Đang chạy: 3` ma → job crash không cập nhật. Fix tự dọn >6h.
- `xóa thiếu quyền` → token kho sai/scope thiếu. Fix dò chủ file + báo kho/email.

## 4. Thêm 1 self-heal mới (method)
1. Bắt lỗi ở tầng gần nhất, phân loại (tạm thời → retry/đổi tài nguyên; vĩnh viễn → cô lập + cảnh báo).
2. KHÔNG raise `SystemExit` trong pipeline (dùng `Exception`) — kẻo giết cả mẻ.
3. Mọi vòng lặp tài nguyên (key/kho) phải có **failover** + **cooldown đúng độ dài** (phút vs ngày).
4. Thêm dòng vào bảng §1 + ghi bug-log.

## 5. 🛡️ CHỐNG KHOÁ KEY GEMINI (avoid ban — an toàn tương lai)
**Vì sao free Gemini project bị khoá ("403 denied access — contact support"):** burst request quá nhanh, tạo bulk key/project cùng lúc/1 IP, hoặc Google quét vùng/ToS. Nội dung mình an toàn (data/tài liệu, không NSFW/spam) nên rủi ro chính là PATTERN request + cách tạo key.

**Pipeline ĐÃ có (tự động):**
- Chia đều tải: `key_order` ưu tiên key ÍT dùng (req_today nhỏ) + round-robin → không dội 1 key.
- Cooldown khi chạm limit: per-minute → nghỉ 90s; quota ngày → 90'. Retry có giãn (65s) trước khi coi là fail.
- Cách 1.5s giữa mỗi key trong 1 lần viết → không bắn dồn.
- Theo dõi `req_today`, ước hạn ngạch còn lại (~250/key/ngày), ưu tiên key còn quota.
- **Key denied/suspended → đánh dấu CHẾT ngay + loại khỏi vòng** (không thử lại vô ích, không dội key hỏng).
- Health-check mỗi mẻ (`plan_mode` → `test_key` → `mark_key_alive`) → tự loại key chết, tự hồi key sống lại.

**RULE tạo/dùng key (user — quan trọng nhất để tránh khoá tiếp):**
1. Tạo key từ **tài khoản Google THẬT, khác nhau**, KHÔNG tạo hàng loạt cùng lúc/cùng 1 IP (Google quét bulk-creation).
2. Mỗi account chỉ vài key; giãn thời gian tạo (đừng tạo 20 key/10 phút).
3. Giữ **dưới ~250 req/key/ngày** (pipeline tự chia — đừng chỉnh trần lên quá cao).
4. KHÔNG dùng lại project đã bị khoá; thay bằng project/account mới.
5. Giữ số kênh/target hợp lý so với số key sống (dashboard hiện "ước còn ~X request").
→ Cứ để pipeline tự chia + cooldown; đừng ép burst. Thấy `🔴 Thay ngay` tăng thì bổ sung key mới (account khác).
