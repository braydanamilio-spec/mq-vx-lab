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

## 🆕 5 KÊNH MỚI — motif KHÁC HẲN data-race (đang build lần lượt)
Mục tiêu: phá thế "10 kênh cùng 1 motif bar-race". Mỗi kênh 1 cơ chế hình ảnh riêng, USA-viral, đẹp, KHÔNG lặp.

| # | Kênh | Handle | Màu | Engine (mới) | Cơ chế hình ảnh (motif) | TT |
|---|---|---|---|---|---|---|
| 1 | 🤔 GUESS | @guessdaily | #F5B301 + #ff375f | `GuessShort.tsx` + `BrandGuess.tsx` | **mảnh ghép mở dần + đồng hồ đếm giờ + đáp án bung** — ép đoán trước khi lộ | ✅ **FULL A-Z** (engine+brand+não+dispatch) |
| 2 | 🗺️ MAPPED | @mappedusa | #22D3EE | `MappedShort.tsx` + `BrandMapped.tsx` (geoAlbersUsa) | choropleth US "nóng dần" + pin số + bảng xếp hạng | ✅ **FULL A-Z** (engine+brand+não+dispatch) |
| 3 | 🏆 RANKED | @rankedusa | #7C5CFF | `RankedShort.tsx` + `BrandRanked2.tsx` | bảng tier S/A/B/C/D thẻ lật xếp hạng | ✅ **FULL A-Z** (engine+brand+não+dispatch) |
| 4 | 📏 SCALED | @scaledusa | #2FA84F | `ScaledShort.tsx` + `BrandScaled.tsx` | so sánh KÍCH THƯỚC vật lý (emoji đúng tỉ lệ trên nền) | ✅ **FULL A-Z** (engine+brand+não+dispatch) |
| 5 | ⏳ THEN×NOW | @thennowusa | #EC4899 | `ThenNowShort.tsx` + `BrandThenNow.tsx` | split XƯA(sepia)/NAY(hồng) + con số biến đổi | ✅ **FULL A-Z** (engine+brand+não+dispatch) |

> 🎉 **WAVE 1 HOÀN TẤT** — cả 5 kênh motif đã xong A-Z (engine + brand + não + dispatch + doc), test local từng bước. Bật kênh chỉ cần đặt `format`.

### ⚙️ Cách BẬT 1 kênh motif (GUESS/MAPPED) — config kênh trong dashboard/Firestore
Đặt field **`format`** cho kênh: `"guess"` · `"mapped"` · `"ranked"` · `"scaled"` · `"thennow"` · `"doc"` → `run_one` route sang maker tương ứng (short-only, theo `short_target`). `doc` (Wave 2) đọc thêm `style`/`accent`/`accent2`/`niche`.
- GUESS: thêm `category` (vd `"US cities"`, `"famous historical scientists"`, `"US landmarks"`).
- MAPPED: `niche`/`category` (vd `"US demographics"`, `"cost of living"`) → Gemini tự chọn metric có số liệu THẬT.
- RANKED: `niche`/`category` (vd `"US fast food"`, `"streaming services"`) → Gemini tự xếp tier theo tiêu chí + số liệu THẬT.
- SCALED: `niche`/`category` (vd `"ocean animals"`, `"tallest buildings"`, `"planets"`) → Gemini so sánh kích thước THẬT + emoji.
- THENNOW: `niche`/`category` (vd `"cost of living"`, `"technology"`, `"salaries"`) → Gemini so sánh giá trị XƯA/NAY THẬT + mức biến đổi.
- Không đặt `format` → kênh chạy data-race như cũ (không phá kênh cũ).

### Pipeline 2 kênh này (đã build + test local)
`content_brain.generate_guess/generate_mapped` (ép logic/accuracy ≥95, viết lại nếu trượt) → `key_manager.write_guess/write_mapped` (bám+xoay key) → `datastory_ci.make_guess/make_mapped` (edge-tts giọng + [GUESS: ảnh CC0 + **Vision verify khớp đáp án**, MAPPED: số liệu bang] + SFX + timing bám giọng + thumb brand) → render `GuessShort`/`MappedShort` → QC → enqueue Drive.

## 🌊 WAVE 2 — 5 kênh KỂ CHUYỆN/TÀI LIỆU (có footage, tái dùng engine Cinematic/BEYOND, KHÔNG cần engine motif mới)
Khác Wave 1 (motif đồ họa). Dạng: narration lôi cuốn + footage/ảnh PD + nhạc. Chọn theo viral + ảnh free + an toàn policy.

| # | Kênh | Niche | Nguồn ảnh FREE | Ghi chú policy |
|---|---|---|---|---|
| A | 🌌 COSMOS | Vũ trụ, thiên hà, hố đen, "chuyện gì nếu..." | **NASA/ESA = public domain** (kho khổng lồ) | ✅ **BUILD XONG** (dùng chung) |
| B | 🌊 THE DEEP | Sinh vật biển sâu, đại dương bí ẩn | NOAA / Wikimedia PD | ✅ **BUILD XONG** |
| C | 🔬 WHY? | Hiện tượng tự nhiên/khoa học "vì sao X" | CC0/PD | ✅ **BUILD XONG** |
| D | 👑 EMPIRE | Tiểu sử doanh nhân/nổi tiếng — **FACELESS** (bối cảnh + tên chữ) | CC0 bối cảnh (cty/sản phẩm/thành phố) | ✅ **BUILD XONG** |
| E | 🌍 UNSOLVED | Bí ẩn/hiện tượng CHƯA lời giải (địa danh, cổ vật, không gian) | CC0/PD | ✅ **BUILD XONG** |

> ❌ True-crime nạn nhân thật, rừng-kỳ-bí cụ thể tên người: BỎ (rủi ro).

### Wave 2 — pipeline DÙNG CHUNG (5 kênh 1 engine)
- **Engine**: `Cinematic.tsx` / `CinematicShort` (có sẵn) — ảnh CC0 + Ken Burns + caption động + nền cosmic fallback.
- **Brand**: `BrandDoc.tsx` PARAMETRIC → 5 kênh (chỉ khác emoji/tên/accent). Compositions `BrandDoc<Tên>Avatar/Banner/Watermark` + `Doc<Tên>Thumb`.
- **Não**: `content_brain.generate_doc(niche, style)` → hook + 6-9 cảnh (nar + img_query) + outro, ép accuracy. `key_manager.write_doc`.
- **Dựng**: `datastory_ci.make_doc(channel, niche, style, accent, accent2)` → giọng edge-tts mỗi cảnh + ảnh CC0 (**Vision verify khớp + loại watermark/caption to**) + render Cinematic.
- **Bật kênh**: đặt `format="doc"` + `niche` + `style` + `accent`/`accent2` trong config kênh (dashboard). Thumb = trích khung video (ảnh NASA đẹp sẵn).

### GUESS — method chi tiết + ⚠️ POLICY (bắt buộc)
- **Thể loại**: Guess the City · Guess the Billionaire's Empire · Guess the Landmark · Guess the Brand (qua sản phẩm) · Guess the State.
- **Cơ chế**: intro 🤔 → mỗi vòng: ảnh bị lưới ô che, mở dần (viền hồng glow) + câu hỏi + clue + đồng hồ vòng 3-2-1 → REVEAL đáp án (chữ) bung + tia + stat sốc.
- **⚠️ ẢNH — TUYỆT ĐỐI SẠCH BẢN QUYỀN**: chỉ dùng ảnh **CC0/public-domain** (Openverse/Pexels/Wikimedia PD). KHÔNG scrape ảnh chân dung/paparazzi người nổi tiếng (bản quyền + quyền hình ảnh → chặn monetize).
  - Đố người nổi tiếng/doanh nhân → **ảnh là BỐI CẢNH của họ** (trụ sở, sản phẩm, thành phố) + clue ("Bỏ học Harvard · 2.9 tỷ user"); **đáp án = TÊN dạng chữ**, không cần mặt họ. Chân dung chỉ khi có bản PD/CC chính thức.
- **Props**: `{ title, handle, color, accent, roundSec, rounds:[{q, clue, answer, stat, img}], audio, subs, music }`. `calcGuess` tự tính độ dài. Deterministic (hash sin) → không flicker.

## 📤 AUTO-PUBLISH (đăng YouTube tự động)
- Render xong → job lưu kèm title/description/hashtags/tags (`run_render.py`).
- `MM0-AutoPublisher/src/auto_enqueue.py` (chạy trong `main.py` trước `publish_yt_queue`): tự đẩy video của kênh **đã bật `auto_publish`** vào `yt_queue`. **Mặc định TẮT**; dedup theo `drive_file_id`; trần ~6/ngày/kênh (chống spam).
- Bật/tắt: dashboard → mỗi kênh có nút **🟢/⚪ Auto-đăng** (ghi `settings/overrides__<uid>.auto_publish[TÊN kênh]`).
- Điều kiện chạy: kênh phải **đã Kết nối YouTube** (`connections/<owner>__<kênh>__youtube` có refresh_token) — bước này user tự làm (OAuth).
- `invalid_grant` khi list_queue = 1 kết nối Drive cũ ở `connections` (khác 48 kho `storage_accounts` đều sống) → đã bỏ qua tự động, vô hại.

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
