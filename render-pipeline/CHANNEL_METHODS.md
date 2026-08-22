# MM0 — Sổ tay Method & Repo (đọc lại là làm tiếp được)

> Mục tiêu: 100% FREE, máy tắt vẫn chạy 24/7, tự sản xuất video "cinematic data-story"
> cho các kênh USA → render trên GitHub Actions → đẩy Google Drive → MM0-AutoPublisher tự đăng.

## Repo (ai chứa gì)
| Repo | Loại | Chứa |
|---|---|---|
| **mq-vx-lab** | PRIVATE | `render-pipeline/` (não Gemini, QC, orchestrator) · `engine-remotion/` (engine vẽ video) · `.github/workflows/` (cron render) · brand/method docs |
| **mm0-auto-publisher** | PUBLIC | `dashboard/` (web quản lý) · `connect-worker/` (Cloudflare OAuth+Drive) · publisher (tự đăng YT/FB) |

Moat (bí mật) nằm ở GitHub Secret `GEMINI_SYSTEM_PROMPT` + local `PROMPT_SECRET.txt` (gitignore). KHÔNG đẩy public.

## 🔀 Kiến trúc 3-project Firestore (19/8 — chống 1 project cạn quota kéo cả hệ thống đứng)
| Project | Chứa | Ai đọc/ghi |
|---|---|---|
| **A** `mm0-auto-publisher` | settings/connections/channels/fb_pages/links/**gemini_keys**(nhạy cảm, cần auth)/**storage_accounts**(connect-worker chỉ biết A) | dashboard + connect-worker |
| **B** `mm0-shard-b` | render_config/render_channels/render_topics/render_requests/render_jobs | render pipeline (`_db_meta()`/`_db_jobs()`) |
| **C** `mm0-shard-c` | videos/counters/quota/yt_queue/social_queue | publisher (`self.pub`) |

Chi tiết đầy đủ: `SHARD_SETUP.md` (B) + `SHARD_C_SETUP.md` (C). **BÀI HỌC ĐAU (đọc trước khi động vào bất kỳ collection nào):**
- **storage_accounts PHẢI ở A** — connect-worker (Cloudflare Worker, external, KHÔNG biết B/C tồn tại) ghi trực tiếp vào A khi connect/sync/xoá kho Drive. Route sang B/C = dashboard đọc 1 nơi, Worker ghi nơi khác → nút "Đồng bộ dung lượng" bấm hoài không đổi (lỗi thật đã xảy ra 19/8, xem PIPELINE_RULES.md §7).
- **2 REPO CÓ THỂ CÓ WORKFLOW TRÙNG TÊN — chỉ 1 bản chạy thật.** `mq-vx-lab` (public, root `.github/workflows/`) có bản sao publish.yml/cleanup.yml/publish_social.yml/stats.yml của `mm0-auto-publisher`. **Bản ở mq-vx-lab MỚI LÀ BẢN LIVE** (cron thật); bản ở mm0-auto-publisher đã tắt cron có chủ đích (chỉ workflow_dispatch để test tay — có comment "⛔ CRON ĐÃ CHUYỂN sang repo public" ngay trong file). Sửa env/secret 1 workflow → LUÔN `gh run list` kiểm bản nào thực sự có lịch sử chạy gần đây trước khi tin "sửa xong".
- **gemini_keys tuyệt đối KHÔNG public trên B** — dù B rules mở cho render_jobs+4 collection meta khác, gemini_keys vẫn khoá vì chứa API key thật; dashboard app B không auth.

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

## 🌊 WAVE 3 — 6 kênh TÀI LIỆU thêm (19/8, cùng engine Wave 2, KHÔNG engine mới)
Cảm hứng từ 1 hệ "epistemic-grammar" channel khác (dream-motion, agent thủ công/phim — KHÔNG port nguyên quy trình vì phá vỡ tự động 24/7 của MM0). Chỉ lấy Ý TƯỞNG chủ đề + kỷ luật guardrail, giữ nguyên pipeline tự động Gemini+Cinematic.

| # | Kênh | Niche | Style | Accent | Guardrail RIÊNG (chống bịa) |
|---|---|---|---|---|---|
| F | ⚡ GRIDUSA | Hệ thống vô hình (lưới điện, data center, chuỗi cung ứng) | technical, tense | `#64748B` | chỉ dùng fact kỹ thuật đã ghi nhận |
| G | ⚖️ RULEDUSA | Phán quyết pháp lý bất ngờ (cà chua=rau, burrito≠sandwich) | dry, deadpan | `#E11D48` | **STRICT: chỉ case/quy định CÓ THẬT, nêu rõ toà/cơ quan+năm; không chắc thật → chọn case khác đã biết** — rủi ro cao nhất (Gemini dễ bịa case luật nghe như thật) |
| H | 🔍 VAULTUSA | Cách chuyên gia phát hiện hàng giả/gian lận | precise, investigative | `#B45309` | chỉ phương pháp đã ghi nhận, không gán vụ việc cụ thể trừ khi nổi tiếng công khai |
| I | 🧾 LEDGERUSA | Phí/thuế được tính ra sao | sharp, procedural | `#15803D` | **STRICT: chỉ giải thích công thức, số liệu MINH HOẠ không phải thật, không tư vấn tài chính** |
| J | 📡 SIGNALUSA | Thuật toán quyết định tin cậy ra sao (điểm tín dụng, lọc spam) | cool, technical | `#A21CAF` | không khung âm mưu, không cáo buộc công ty cụ thể chưa kiểm chứng |
| K | 📐 MARGINUSA | Sản xuất chính xác/dung sai kỹ thuật | tight, technical | `#1E40AF` | chỉ tiêu chuẩn ISO/ANSI thật + ví dụ lịch sử có thật |

**Bài học rút ra khi build Wave 3 (ghi để không quên):**
- **Kiểm màu accent TRÙNG trước khi seed** — lúc đầu chọn nhầm GRIDUSA trùng hệt màu EATSUSA (`#A3E635`); phải rà cả bảng 20 kênh cũ trước khi chốt màu mới, không chỉ đoán bằng mắt.
- **KHÔNG dùng lại format `ranked`/`scaled` cho kênh thứ 2** — schema cố định (tier S/A/B/C/D hay trục kích thước) khiến 2 kênh nhìn giống hệt nhau trên feed. Wave 3 toàn bộ dùng `doc` (đã chứng minh linh hoạt qua 5 kênh, style/accent khác nhau đủ để không nhàm).
- **`niche` field = nơi thêm guardrail** — không cần code mới, chỉ cần viết rõ ràng buộc ("STRICT: chỉ dùng case CÓ THẬT...") ngay trong text niche, Gemini đọc field này mỗi lần viết. Áp dụng khi kênh chạm chủ đề dễ bịa (luật, tài chính, y tế...).
- **Seed idempotent, dry-run trước** (`seed_new_channels_wave3.py --dry-run` rồi bỏ cờ) — script mẫu cho các wave sau, đọc owner từ kênh mẫu sẵn có, `merge:True` an toàn chạy lại.

## 🔎 TREND SCOUT — học gu viết kênh lớn, tự động hàng tuần (19/8)
`render-pipeline/trend_scout.py` + `.github/workflows/trend_scout.yml` (cron thứ 2 hàng tuần, hoặc chạy tay `workflow_dispatch`):
1. `yt-dlp --flat-playlist` lấy TITLE (KHÔNG tải video) của vài kênh lớn tham khảo trong `SOURCES` (hiện có Zack D Films, Kurzgesagt, The Infographics Show).
2. Gemini (quota chữ có sẵn, key đầu trong pool) đọc titles → tự tóm tắt 2-3 câu **GU VIẾT** (hook/twist/cách đặt câu) — **KHÔNG tóm chủ đề**, tránh copy nội dung.
3. Lưu Firestore (`FB.save_trend_scout`, ghi đè không cộng dồn) → `run_render.py` tự đọc (`FB.read_trend_scout`) và chèn vào `niche` trước khi gọi Gemini viết kịch bản thật — giống hệt cơ chế `top_titles()` (học phong cách, luôn viết chủ đề MỚI, không lặp).
- Thêm kênh tham khảo mới: thêm 1 dòng vào `SOURCES` trong `trend_scout.py`, không cần sửa code khác.
- 100% free: yt-dlp free/mã nguồn mở, Gemini dùng quota chữ dư sẵn (không mở key/account mới). Đã test thật 3 URL nguồn (yt-dlp lấy title thành công cả 3, không tải video).

## 🚀 WAVE 5 — 2 kênh SPECULATIVE, 100% ảnh AI vẽ (19/8)
Insight: quota ảnh Nano Banana (~500 ảnh/ngày/key × 40+ key ≈ 20.000 ảnh/ngày lý thuyết) **tách riêng hoàn toàn** khỏi quota viết kịch bản — đang bỏ phí 100%. 2 kênh mới nhắm đúng chỗ **không thể có ảnh thật để tìm** — nên ảnh AI không phải "chữa cháy" như GUESS/doc mà là **lựa chọn duy nhất hợp lý**.
- **FUTUREUSA** (`#3B82F6`/`#A855F7`) — tương lai suy đoán (thành phố, công nghệ, đời sống 50-200 năm tới). Narration BẮT BUỘC ngôn ngữ suy đoán ("could"/"might"/"imagine if"), không khẳng định như sự thật.
- **UNSEENUSA** (`#4C1D95`/`#A78BFA`) — vật lý thiên văn lý thuyết CÓ THẬT nhưng chưa camera nào chụp được (lỗ đen, ngoại hành tinh, vũ trụ sơ khai). Narration BẮT BUỘC bám khoa học thật; chỉ HÌNH ẢNH là suy đoán nghệ thuật, luôn khung "artist's impression" — không bao giờ nói ảnh là ảnh chụp thật.
- Dùng lại format "doc" có sẵn (Cinematic engine, KHÔNG cần engine/brand Remotion mới — parametric `BrandDoc` đã đủ, chỉ seed Firestore + dashboard).
- Thêm mới `ai_style`/`ai_only` vào `fetch_image()→build_doc_props()→make_doc()` (datastory_ci.py): `ai_style` = gu vẽ riêng nhất quán (khác ảnh báo chí mặc định); `ai_only=True` = bỏ qua tìm Openverse hẳn (chắc chắn trật, đỡ phí round-trip mạng) + bỏ qua Vision-verify (ảnh nào cũng do AI vẽ theo prompt, không có "ảnh tải về" để so khớp/sai).
- Seed: `render-pipeline/seed_new_channels_wave5.py` (giống mẫu wave3/4, idempotent).
- **🔴 Bug phát hiện + fix cùng ngày**: `DOC_SYS` (system prompt chung mọi kênh doc) có rule bắt `img_query` phải mô tả ảnh CC0 TÌM ĐƯỢC THẬT — mâu thuẫn trực tiếp với ai_only=True (ảnh 100% AI vẽ). Không sửa thì kênh vẫn CHẠY được nhưng Gemini tự bó hẹp mô tả cảnh, mất chất tưởng tượng — lỗi ĐỊNH HƯỚNG khó thấy qua log. Fix: `DOC_SYS_SPECULATIVE` riêng (content_brain.py), tự chọn qua `speculative=ai_only` (không cần field mới).
- **Nhạc nền Cinematic engine** (Cinematic.tsx, prop `music` mới, Audio loop 0.12 volume + fade mượt): đã build hạ tầng nhưng **mặc định TẮT** — 13 kênh doc-format tông rất khác nhau, ép 1 bài chung theo tên file đoán mò dễ "kỳ" (đúng lời cảnh báo user 19/8). CHỈ bật per-kênh sau khi nghe thật + chọn đúng bài (field `music` ở render_channels, file phải `git ls-files` xác nhận có trên git trước — xem PIPELINE_RULES.md bài học nhạc 404).
- Transitions/hiệu ứng hình ảnh (Ken Burns, 5 kiểu chuyển cảnh xoay vòng không-chớp-đen, kinetic caption karaoke, particle FX ash/snow/dust/embers/rain, data-HUD) đã CÓ SẴN từ trước trong Cinematic.tsx — không phải xây mới, đã khá tốt; whoosh SFX riêng theo từng transition CHƯA có, để dịp sau (cần nguồn SFX + cơ chế trigger riêng, việc lớn hơn).

## 🌊 WAVE 4 — 4 kênh ENGINE RIÊNG hoàn toàn mới (19/8, không dùng chung doc/motif cũ)
Đột phá thật (không phải doc reskin) — mỗi kênh 1 ngôn ngữ hình ảnh chưa từng có trong 26 kênh trước: thời gian/tỉ lệ, cường độ giác quan, mật độ đám đông, xác suất/may rủi. Build trực tiếp (không qua agent tự mày mò — học từ lần đầu tốn token), render-verify từng cái (avatar + still giữa animation) trước khi tích hợp.

| # | Kênh | Engine | Cơ chế hình ảnh | Accent |
|---|---|---|---|---|
| L | 🐝 SWARMUSA | `SwarmShort.tsx` + `BrandSwarm.tsx` | hàng trăm hạt bay từ mép vào, hội tụ thành silhouette (stadium/city/person/circle/grid) + số đếm lớn | `#0D9488` |
| M | 📟 PULSEUSA | `PulseShort.tsx` + `BrandPulse.tsx` | gauge bán nguyệt kim vật lý (spring), đổi màu lạnh→nóng, rung+shockwave khi extreme | `#EA580C` |
| N | ⏱️ CLOCKWORKUSA | `ClockworkShort.tsx` + `BrandClockwork.tsx` | thanh/mặt đồng hồ nén thời gian, quét nhanh→chậm, zoom dramatic vào hero reveal cuối | `#C2410C` |
| O | 🎲 LONGSHOTUSA | `LongshotShort.tsx` + `BrandLongshot.tsx` | tháp xác suất dọc (log-scale), token leo bậc, camera scroll/zoom lên khi hiếm dần | `#4F46E5` |

**Backend đầy đủ** (giống hệt cấu trúc Wave 1, KHÔNG rút gọn): `content_brain.generate_swarm/pulse/clockwork/longshot` (accuracy≥95 + MIN_SCORE + viết lại) → `key_manager.write_swarm/pulse/clockwork/longshot` (dùng chung helper `_write_wave4`) → `datastory_ci.build_X_props`+`make_X` (TTS bám giọng + thumb branded qua composition `XThumb`) → `run_render.py` dispatch (`fmt in (...,"swarm","pulse","clockwork","longshot")`, nhánh riêng truyền `accent` mặc định/kênh).

**Bài học build lần này (quan trọng, đọc trước khi build engine mới khác):**
- **KHÔNG giao 4 agent tự mày mò song song build từ đầu** — tốn token rất nhiều (mỗi agent tự code+render+soi+sửa lặp) mà không kiểm soát được. Lần đầu bị huỷ giữa chừng vì lý do này.
- **Nhưng 8 file dở dang agent để lại (chưa xoá, chưa commit) hoá ra DÙNG ĐƯỢC** — render-verify lại thấy cả 4 đều đẹp (chỉ LONGSHOT có 1 lỗi nhãn mốc đè token, sửa 1 chỗ CSS là xong). LUẬT: trước khi build lại từ đầu, LUÔN kiểm file cũ (kể cả của agent bị huỷ) — `git status` thấy file lạ (`??`) → đọc thử, render thử trước khi bỏ.
- **`npx remotion still ... --frame=N`**: mặc định frame=0 chỉ ra được khung intro (thường trống/chưa có hiệu ứng) — LUÔN test ở khung GIỮA animation (`--frame=90` trở lên) mới thấy hiệu ứng thật để đánh giá.
- **Test composition tạm trong Root.tsx**: chèn trước `</>);`(đóng React Fragment, KHÔNG phải `</Compositions>`) — nhớ backup + revert sau khi test xong, đừng để lẫn vào bản chính thức.

## 📤 AUTO-PUBLISH (đăng YouTube tự động)
- Render xong → job lưu kèm title/description/hashtags/tags (`run_render.py`).
- `MM0-AutoPublisher/src/auto_enqueue.py` (chạy trong `main.py` trước `publish_yt_queue`): tự đẩy video của kênh **đã bật `auto_publish`** vào `yt_queue`. **Mặc định TẮT**; dedup theo `drive_file_id`; trần ~6/ngày/kênh (chống spam).
- Bật/tắt: dashboard → mỗi kênh có nút **🟢/⚪ Auto-đăng** (ghi `settings/overrides__<uid>.auto_publish[TÊN kênh]`).
- Điều kiện chạy: kênh phải **đã Kết nối YouTube** (`connections/<owner>__<kênh>__youtube` có refresh_token) — bước này user tự làm (OAuth).
- `invalid_grant` khi list_queue = 1 kết nối Drive cũ ở `connections` (khác 48 kho `storage_accounts` đều sống) → đã bỏ qua tự động, vô hại.
- **Playlist tự động** (19/8, kích hoạt): mỗi video upload qua `publish_yt_queue.py` tự vào playlist **"Long Videos"** hoặc **"Shorts"** (theo `type`), tạo/tìm ngay trong ĐÚNG kênh đang upload (mỗi kênh OAuth riêng → không thể lẫn playlist chéo kênh dù trùng tên). `_ensure_playlist()` tìm theo tên trước, không tạo trùng. Lỗi playlist (nếu có) KHÔNG làm hỏng upload (try/except riêng).
- ⛔ **End Screen (subscribe + video liên quan cuối clip) — CHỦ ĐỘNG KHÔNG LÀM** (quyết định của user 19/8): cho là gây nhàm chán, dễ khiến người xem thoát. Đừng đề xuất lại trừ khi user chủ động hỏi.

## 💾 LƯU KỊCH BẢN CHI TIẾT (đề phòng sự cố, 19/8)
- Mỗi video lúc `status="done"` được ghi kèm field **`script`** (JSON, `_script_json()` trong `run_render.py`) vào **Firestore project B** (`render_jobs`) — CHỦ ĐỘNG tách khỏi Drive, vì lý do đúng: nếu 1 tài khoản Drive bị khoá TRƯỚC KHI video kịp đăng, video+sidecar trong tài khoản đó mất cùng lúc, nhưng `script` ở Firestore (hạ tầng khác) vẫn còn.
- Short (mọi format guess/mapped/ranked/scaled/thennow/doc/wave4): `script` = toàn bộ `story` (lời thoại từng vòng/scene/item, ảnh query, self_score...) trừ `_thumb` (path tạm cục bộ, vô nghĩa sau khi xong).
- Long (data-race pillar): `make_long()` nay trả thêm `stories` (dữ liệu ĐẦY ĐỦ từng race, trước đây bị bỏ) → `script` = `{pillar_title, hook, races: stories}`.
- Mục đích: có sự cố (mất file/Drive) → render lại **MIỄN PHÍ + NHANH** thẳng từ `script` (TTS + Remotion) — KHÔNG cần gọi lại Gemini (đỡ tốn quota/tiền, khỏi lo trùng/lệch nội dung).
- Chi phí: vài KB/video, cap 300KB/video phòng hờ (`_script_json` tự cắt bớt nếu quá lớn) — dư sức nằm trong 1GiB free tier của Firestore dù hàng vạn video.
- Nhân bản FILE VIDEO (khác với lưu script) — CHƯA LÀM, để sau (quyết định user 19/8): khi làm chỉ nhân bản video CHƯA ĐĂNG (đã đăng thì YouTube đã lưu bản chính rồi, nhân bản làm gì).

## 🎨 ẢNH AI DỰ PHÒNG — Nano Banana (19/8)
- `fetch_image()` trong `datastory_ci.py`: khi Openverse (CC0) KHÔNG tìm ra ảnh khớp chủ đề → trước khi bỏ cuộc (mosaic/cosmic bg), thử `_generate_image_ai()` nhờ **Gemini 2.5 Flash Image ("Nano Banana")** vẽ ảnh minh hoạ thay. Chỉ chữa cháy, KHÔNG thay thế Openverse (ảnh thật vẫn ưu tiên trước).
- Quota **tách riêng hoàn toàn** khỏi quota viết kịch bản (khác model) → dùng ngay 40+ key Gemini hiện có, không tốn gì thêm. ~500 ảnh/ngày/key free.
- SDK dùng `google-genai` (KHÁC package `google-generativeai` đang dùng viết chữ) — API: `client.models.generate_content(model="gemini-2.5-flash-image", contents=prompt)`, đọc `candidates[0].content.parts[i].inline_data.data` (đã là raw bytes, không cần base64 decode). Đã cài vào `render_cron.yml` (render job).
- Đã nối vào GUESSUSA (`build_guess_props`) và mọi kênh doc-format Wave2/3 (`build_doc_props`). DATA RACE (`_race_from_story`) CHƯA nối (đang tự lùi về "dùng lại ảnh cảnh trước" khi thiếu, ít ưu tiên hơn).
- Lỗi/hết quota/an toàn nội dung → `_generate_image_ai()` trả False, KHÔNG BAO GIỜ crash pipeline, tự lùi về fallback cũ.

## 🩺 HEALTH GUARDIAN — tự canh + tự chữa mỗi giờ (19/8)
- File mới: `render-pipeline/health_guardian.py` + `.github/workflows/health_guardian.yml` (cron mỗi giờ phút 07).
- **Tự chữa**: job render "treo" (status queued/running/writing/rendering/qc) quá `STALE_HOURS` (mặc định 6h) → tự đánh dấu `failed`. Trước đây việc này CHỈ chạy bằng JavaScript phía dashboard (JS trong `index.html`, cần MỞ trình duyệt mới chạy) → không ai mở dashboard = job treo mãi = `has_active_render()` coi cổng còn "đang chạy" **VÔ THỜI HẠN** → chặn hết mọi phiên render mới. Đây LÀ nguyên nhân sự cố thật đêm 19/8 (EATSUSA treo gần 3h, kéo theo 26 job cũ khác kẹt sẵn từ trước, video ngừng tăng nhiều giờ).
- **Cảnh báo thật**: 12h liền không có video "done" nào dù render đang bật → `sys.exit(1)` → GitHub TỰ GỬI EMAIL cho chủ repo (free có sẵn, không cần dịch vụ thông báo ngoài nào).
- **Can thiệp khẩn cấp**: `workflow_dispatch` có input `stale_hours` (đọc qua env `STALE_HOURS_OVERRIDE`) → chạy tay với ngưỡng thấp (vd 1h) để dọn NGAY, không đợi đủ 6h. Lệnh: `gh workflow run health_guardian.yml -f stale_hours=1`.
- **Bài học rút ra cùng đêm đó**: `render_cron.yml` là workflow production DUY NHẤT thiếu khoá `concurrency` (mọi workflow khác đều có) → đã thêm `concurrency: { group: mm0-render-cron, cancel-in-progress: false }`. Lượt trigger mới giờ XẾP HÀNG thay vì chạy chồng.

## ♻️ CHECKPOINT/RESUME — không render lại từ đầu khi bị huỷ/treo (19/8)
- Vấn đề: trước đây bất kỳ job nào bị huỷ (mất mạng, GitHub kill, `gh run cancel`) hay lỗi giữa chừng đều MẤT SẠCH — kể cả khi Gemini đã viết XONG kịch bản (bước tốn quota nhất), phiên sau phải viết lại từ đầu.
- Fix: MỌI hàm `make_X()` (12 hàm: video/mapped/ranked/scaled/thennow/doc/swarm/pulse/clockwork/longshot/guess/long) giờ:
  1. Ngay khi Gemini viết xong kịch bản (TRƯỚC bước render tốn thời gian nhất) → tự ghi checkpoint vào field `script` của job (qua `on_status`/`st("rendering", ..., script=_ckpt_json(story))`) — TÁI DÙNG đúng cơ chế lưu kịch bản đã có, không thêm hạ tầng mới.
  2. Nhận thêm tham số `resume_story=` (hoặc `resume_checkpoint=` cho `make_long`) — có truyền vào thì BỎ QUA gọi Gemini, dùng thẳng kịch bản cũ.
- `firestore_bridge.py` thêm `find_resumable(owner, channel, vtype)` (tìm job **status="failed"** gần nhất còn `script` — CHỈ lấy job đã chắc chắn không ai xử lý, an toàn tuyệt đối, không đụng job đang chạy thật) và `clear_resumed(job_id)` (dùng xong 1 lần thì xoá, tránh lặp lại kịch bản lỗi vô hạn).
- `run_render.py`: mỗi nhánh (short/motif/wave4, long, short-từ-subtopics) gọi `find_resumable()` 1 lần trước vòng lặp, dùng cho **video đầu tiên** rồi tiêu ngay; thử lại lần 2 trong cùng phiên (self-heal) KHÔNG dùng lại checkpoint (lỗi có thể do chính kịch bản đó).
- Kết hợp với Health Guardian: job treo → Health Guardian đánh dấu `failed` (giữ nguyên `script`) → phiên render TIẾP THEO tự động nhặt lại, không tốn quota Gemini viết lại, không lệch/trùng chủ đề.

## 🆕 THÊM 1 KÊNH MỚI — QUY TRÌNH ĐỒNG BỘ (RULE bắt buộc, làm ĐỦ các bước)
> Thêm kênh KHÔNG chỉ là thêm 1 dòng — phải đồng bộ ĐỦ để "chọn là sản xuất + brand + đăng" chạy trơn.
> Có 3 loại kênh, làm theo loại tương ứng:

### Loại A — Kênh MOTIF mới (đồ hoạ riêng, vd GUESS/MAPPED/RANKED/SCALED/THENNOW)
1. **Engine** `engine-remotion/src/<X>Short.tsx` — composition riêng (test render local: still + full, soi ảnh, sửa chồng chéo).
2. **Brand** `engine-remotion/src/Brand<X>.tsx` (avatar/banner/watermark/thumb) + đăng ký cả 2 vào `src/Root.tsx`.
3. **Não** `render-pipeline/content_brain.py`: `generate_<x>()` + `_validate_<x>()` (ép logic/accuracy ≥95, viết lại nếu trượt).
4. **Key** `key_manager.py`: `write_<x>()` (bám+xoay key, cùng khuôn write_story).
5. **Dựng** `datastory_ci.py`: `build_<x>_props()` + `make_<x>()` (edge-tts + [ảnh CC0 **Vision verify** nếu có ảnh] + SFX + timing bám giọng + thumb) — test local với story giả.
6. **Dispatch** `run_render.py`: thêm `"<x>"` vào set `fmt in (...)` + vào map `mk = {...}`.
7. **Dashboard** `MM0-AutoPublisher/dashboard/index.html`: thêm vào `RS_PRESETS` (fmt/accent/[style]/niche) + `RS_BRANDS` (d/a/t/h/ic/ht/niche) + `.cat`. (Form dropdown + brand kit + avatar TỰ nhận.)
8. **Handle** `MM0-AutoPublisher/config/brands.json`: thêm entry (display/handle/accent/tagline/category/hashtags).
9. **Deploy** dashboard (`firebase deploy --only hosting`) + **doc** (cập nhật bảng kênh + file NÀY).

### Loại B — Kênh TÀI LIỆU mới (Wave 2/3, dùng chung engine Cinematic) — NHANH
KHÔNG cần engine/brand/brain mới. Chỉ:
1. `RS_PRESETS`: `{name, fmt:"doc", accent, accent2, style, niche}`.
2. `RS_BRANDS` + `.cat` + `brands.json` (handle/accent/tagline).
3. `Root.tsx`: thêm 1 dòng vào mảng `BrandDoc` (id/name/emoji/accent). Deploy + doc.
4. **⚠️ KIỂM MÀU TRÙNG** trước khi chốt accent — rà cả bảng kênh cũ (giống bài học Wave 3 GRIDUSA).
5. **⚠️ Chủ đề dễ bịa (luật/tài chính/y tế/kỹ thuật cụ thể)?** → viết guardrail thẳng vào `niche` (vd "STRICT: chỉ dùng case/số liệu CÓ THẬT, nêu nguồn"). Xem mẫu Wave 3 RULEDUSA/LEDGERUSA.
→ Đã có `generate_doc`/`make_doc` + dispatch `format="doc"` lo hết.

### Loại C — Kênh DATA-RACE mới (engine bar-race có sẵn)
Chỉ `RS_PRESETS` (không fmt) + `RS_BRANDS` + `brands.json`. Deploy. (Pipeline race mặc định lo.)

### ✅ Kiểm nghiệm thu sau khi thêm
- Dropdown "📺 Kênh & Chủ đề Render" + panel "📋 Kế hoạch" thấy kênh mới (số thứ tự + badge format).
- Brand kit (2 dropdown) render avatar/cover/mô tả/tag đúng.
- Bấm thêm → `render_channels` có `format`+`accent`(+`style`) → mẻ render tới route đúng maker.
- (Khi có key) chạy test 1 video đầu-cuối trước khi bật rộng.

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


## 🌟 WAVE 8 — 10 kênh doc-format mới (21/8, chuẩn pipeline ĐÃ KIỂM CHỨNG)
Method: format="doc" -> tự vào luồng chuẩn: **1 long (3 phần) + 3 short bám nội dung long** ·
cảnh hook footage thật (cấm chữ-nền-đen, 2 cổng chặn) · cắt 2-3s · SFX · không intro/outro/CTA ·
thumbnail khung hook · verify ảnh theo lưới + ô mồi · 3 pool key xoay theo kênh.
Niche nhạy cảm có sẵn câu STRICT (policy_lint pass 10/10). Data: `render-pipeline/wave8_channels.json`.
Seed: workflow `seed_channels.yml` (dry-run trước). Brand: brands.json (màu/handle duy nhất toàn 50 kênh).

| Kênh | Niche 1 dòng | Giọng | Màu |
|---|---|---|---|
| MADEUSA | đồ Mỹ được sản xuất thế nào (nhà máy/quy trình) | Andrew | #E76F51 |
| BUILTUSA | siêu công trình & kỳ quan kỹ thuật Mỹ | Guy | #457B9D |
| UNDERUSA | dưới lòng nước Mỹ: hầm/hang/ống (tài liệu công khai) | Brian | #5E548E |
| RELICUSA | nước Mỹ bỏ hoang & vì sao (cấm cổ vũ trespass) | Aria | #8D6A4F |
| FIRSTUSA | những "lần đầu tiên" của nước Mỹ (mốc lịch sử thật) | Jenny | #B22234 |
| BRANDEDUSA | chuyện gốc logo/thương hiệu Mỹ (chỉ sử liệu) | Emma | #111827 |
| PRICEDUSA | giải phẫu giá: mỗi đô-la của ly latte đi đâu | Eric | #0F766E |
| HAULUSA | hàng hoá di chuyển khắp Mỹ: cảng/rail/truck | Christopher | #CA8A04 |
| FAKEUSA | hàng giả & scam bị bóc bằng data FTC/CBP (cấm how-to) | Michelle | #DC2626 |
| FARMUSA | thức ăn Mỹ đến từ đâu: nông trại quy mô (USDA) | Roger | #65A30D |

Khác biệt với 42 kênh cũ: không kênh nào trùng lãnh địa (manufacturing/engineering/underground/
abandoned/firsts/brand-origin/price-anatomy/logistics/anti-scam/agriculture đều là đất mới).

## ⚠️ CHECKLIST BỔ SUNG 22/8 — 3 BẢNG NHÚNG TRONG DASHBOARD PHẢI CẬP NHẬT KHI THÊM KÊNH
Thêm kênh mà quên 1 trong 3 bảng nhúng ở `MM0-AutoPublisher/dashboard/index.html` là kênh "tàng hình"
trên UI (đã xảy ra với Wave 8 — thiếu ở cả 3, phát hiện lắt nhắt 3 lần trong 1 ngày):
1. `RS_BRANDS` (panel Brand kit — profile/cover/desc/tag) + dòng gán `RS_BRANDS.<KÊNH>.cat="<id>"`.
2. `RS_PRESETS` (dropdown "Kênh & Chủ đề Render" — name/fmt/niche).
3. `RS_VOICES` (bảng giọng đọc theo kênh).
Sau khi sửa: chạy node --check toàn bộ inline script (LUẬT) rồi mới deploy hosting.
Nguồn dữ liệu chuẩn để copy: `wave*_channels.json` (render) + `config/brands.json` (publisher).
