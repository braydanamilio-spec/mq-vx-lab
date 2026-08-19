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
