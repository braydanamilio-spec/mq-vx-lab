# MM0 — QUY TRÌNH SẢN XUẤT VIDEO A-Z (repo rule)

> File này = luật/quy trình cho nhà máy render. GIỮ LOCAL (gitignored) — không đẩy public.
> Moat thật (SYSTEM prompt Gemini) nằm trong GitHub Secret `GEMINI_SYSTEM_PROMPT`, KHÔNG ở đây.

## 🔴🔴 RULE CỨNG NHẤT — ĐỌC TRƯỚC MỌI THỨ (vi phạm 2 LẦN: 18/8 + 19/8)
**TUYỆT ĐỐI KHÔNG `gh workflow run` BẤT KỲ workflow nào (render_cron/health_guardian/seed_channels/trend_scout/publish/cleanup/stats...) để "verify"/"test" — KỂ CẢ 1 LẦN.**
- 18/8: kích render + health-check lặp tay → đốt 92K reads → Firestore cạn, đứng tới nửa đêm Pacific.
- 19/8 (LẶP LẠI dù rule đã có từ 18/8): tự bấm render_cron×2 + health_guardian×2 + seed_channels×2 + trend_scout×2 trong 1 đêm để "verify fix" — mỗi lần tự thấy "nhỏ, chắc không sao", CỘNG DỒN vẫn đúng hành vi bị cấm → quota lại cạn, user phát hiện, giận dữ, yêu cầu ghi rule bắt buộc.
- **Không có ngoại lệ "verify nhanh 1 phát".** Muốn biết code mới chạy đúng chưa → đợi CRON TỰ CHẠY theo lịch rồi đọc log của lần đó (`gh run list` xem run tự động gần nhất, KHÔNG tự tạo run mới).
- Chỉ trigger tay khi **user yêu cầu TRỰC TIẾP bằng lời trong chat** — không tự suy diễn "chắc user muốn xem ngay".
- Xem chi tiết: memory `mm0-no-quota-waste`.

## 🔴 BÀI HỌC 20/8 — 5 LỖI CÙNG MỘT KIỂU SAI (đọc trước khi sửa dây chuyền)

Cả ngày 20/8 dây chuyền "lúc treo lúc lỗi", vá 3-4 vòng mới ra gốc. Kiểu sai lặp lại:
**suy đoán trạng thái từ dữ liệu không đáng tin, thay vì dùng thứ đã được bảo đảm sẵn.**

| # | Triệu chứng | Gốc thật | Cách chữa |
|---|---|---|---|
| 1 | Dây chuyền đứng 6h rồi 5h, không lỗi nào | Cổng render hỏi `has_active_render()` — SUY ĐOÁN "có phiên đang chạy" từ bảng `render_jobs`; job ma (tiến trình chết đột ngột trên CI) làm nó sai | **Gỡ hẳn.** GitHub `concurrency` ĐÃ bảo đảm không chồng phiên ở tầng hạ tầng. Đừng làm lại việc đó bằng dữ liệu tệ hơn |
| 2 | 15 job đang render khoẻ bị đánh "mất nhịp tim" rồi giết | `update_job()` là BỘ HÃM GHI, không phải máy phát nhịp — `npx remotion render` chạy 20-40' không gọi nó lần nào | Luồng nền đóng dấu `updated_at` mỗi 2' (`firestore_bridge._beat_loop`) |
| 3 | Dashboard "đang chạy 3" dù cấp 18 slot | `plan_mode` xếp đại 18 kênh, không xét kênh nào ĐÃ ĐỦ chỉ tiêu -> job mở ra rồi thoát ngay | Đếm phần còn thiếu TRƯỚC khi xếp matrix |
| 4 | 3 phiên liên tiếp bị huỷ | 2 job treo giữ khoá `concurrency`, mà trần `timeout-minutes` để 350' (kênh chậm nhất thật chỉ 27') | Hạ trần xuống 120' |
| 5 | 313 lỗi 429 Gemini | `fix_queue_thumbnails` lấy `ks[0]` — LUÔN key thứ nhất, trong khi chạy 10 kênh song song -> 10 tiến trình dội 1 key, 9 key kia nằm không | Dùng lại `key_manager.key_order()` + xoay theo VỊ TRÍ kênh |

**Ba luật rút ra:**
1. **`py_compile` KHÔNG đủ.** Nó chỉ kiểm cú pháp. Hai lỗi `name 'p' is not defined` và `undefined name 'slug_'` lọt qua nó và chỉ lộ khi chạy thật trên 150 video. → **Luôn chạy `pyflakes` trước khi đẩy.**
2. **Đừng tự chế lại thứ dây chuyền đã có.** Lỗi 429 sinh ra chỉ vì viết lại phần chọn key thay vì gọi `key_order()` có sẵn.
3. **Ngưỡng phải calibrate trên NHIỀU mẫu.** Ngưỡng lọc khung biểu đồ đặt 45% dựa trên đúng 2 mẫu -> loại nhầm hàng loạt cảnh hook thật (thực tế nằm ở 49-61%, biểu đồ mới là 65-67%).

**Công cụ tự kiểm (chạy free, không tốn token):**
```bash
python3 render-pipeline/test_thumb_pipeline.py     # 33 phép kiểm cơ chế thumbnail
python3 render-pipeline/check_thumbs.py --stress   # dựng ảnh mẫu 19 kênh + ca chữ xấu nhất
```

## 0. Kiến trúc (2 repo + 3 project Firestore, máy TẮT, free vô hạn)
- **Render** = repo PUBLIC `braydanamilio-spec/mq-vx-lab` (Actions không giới hạn phút). Workflow `render_cron.yml`.
- **Đăng bài** = code ở repo PRIVATE `braydanamilio-spec/mm0-auto-publisher`, NHƯNG **chạy trên repo public** (publish/social/cleanup/stats.yml ở `mq-vx-lab` checkout private lúc chạy → free vô hạn, code vẫn kín). ⚠️ Bản workflow ở `mm0-auto-publisher` ĐÃ TẮT cron (chỉ dispatch tay) — **bản ở mq-vx-lab mới là bản chạy thật**, đừng sửa nhầm bản không chạy.
- **Firestore 3 project độc lập** (chống 1 project cạn quota kéo cả hệ đứng — xem CHANNEL_METHODS.md phần "Kiến trúc 3-project Firestore" để biết field nào ở đâu): **A**=`mm0-auto-publisher` (dashboard/settings/connections/gemini_keys/storage_accounts) · **B**=`mm0-shard-b` (render config/channels/keys-meta/jobs) · **C**=`mm0-shard-c` (publish videos/queues/counters).
- **Dashboard** = Firebase hosting `mm0-auto-publisher.web.app` (deploy từ `MM0-AutoPublisher/dashboard`). Router `_appFor(collection)` quyết định app Firebase nào (A/B/C) cho từng collection — sửa dashboard đụng Firestore PHẢI qua router này, không gọi thẳng `db`.
- **Worker** = `mm0-connect.adisondurham-ef1.workers.dev` (OAuth + Drive stream/thumb, chỉ biết Project A). Deploy: `cd connect-worker && npx wrangler deploy`.
- OWNER_UID chủ = `MW0vCcIkw9TNqsd8imuZZt0EdIc2` (mrquyenbk@mm0user.app).

## 1. Luồng 1 video (run_render.py → datastory_ci.py)
1. Đọc Firestore: gemini_keys, render_channels, render_config.
2. **Health-check key** (đầu mỗi run): 429/quota = SỐNG (giới hạn tạm); chỉ "api key not valid/403/disabled" = CHẾT. Không chắc = giữ nguyên (không báo chết oan).
3. Mỗi kênh theo TEMPLATE (`make_long`, `n_shorts`, `long_target`, `short_target`): 1 long pillar + N short.
4. Gemini viết (bám key sticky theo kênh; 429 → nghỉ 90' + đổi key). Model 3.x (né 2.5 vì 404 user mới). Tự chấm ≥ngưỡng, trượt viết lại.
5. **Tiền-kiểm miễn phí TRƯỚC render**: cắt tên nhãn ≤16 ký tự (chống cắt mép/chồng nhãn = thủ phạm điểm visual thấp).
6. edge-tts giọng US + karaoke subs + ảnh CC0 (Openverse, validate magic-byte, ảnh hỏng bỏ; SafeImg fallback engine).
7. Render Remotion swiftshader. **out = đường dẫn TUYỆT ĐỐI** (render chạy cwd=engine-remotion, path tương đối sẽ lạc chỗ → QC/enqueue mất file).
8. **Self-heal**: long lỗi → thử lại 4→2 race; short lỗi → thử lại 1 lần.
9. QC: ffprobe (dur/audio/res, bắt buộc) + Vision NỚI (2 khung, điểm CAO NHẤT, ngưỡng 55, bỏ veto overlap; fail-open khi 429).
10. **Thumbnail**: trích khung ffmpeg ở 62% video → dùng cho YouTube + gallery (`_make_thumb`).
11. **enqueue** → Drive `_QUEUE` (chọn kho nhiều chỗ nhất, failover). Trả `{id, account}` → lưu job `drive_id`+`drive_account`.

## 2. Quyền/upload (tránh nhầm quyền)
- Upload dùng **OAuth token của CHÍNH kho** (scope full `auth/drive`). File **private của kho đó**, KHÔNG share public.
- Xem trên web = **Worker stream** (`/api/drive-stream`) dùng token kho → nhúng player, không cần share, không "request access".
- Thumbnail gallery = `/api/drive-thumb` (Drive tự tạo thumb video) — cũng qua token kho.
- Đăng YouTube/FB = AutoPublisher đọc file bằng token kho. → KHÔNG chỗ nào cần public link → không nhầm quyền.
- Nút dashboard **🩺 Kiểm token + quyền**: verify từng kho có scope full drive (upload+share+xóa). Thiếu → cảnh báo + Kết nối lại.

## 3. Điều khiển (dashboard)
- **Bảng điều khiển Agent**: gõ lệnh tự nhiên (Gemini hiểu) hoặc thẻ: Tình hình / Render ngay / Tạm dừng / Dừng ngay / Chạy tiếp / Thử lại lỗi / Dọn job cũ / Gợi ý niche.
- **Render ngay** = cờ `run_now` → nhịp cron 30' nhận (≤30'). **Dừng ngay** = cờ `stop` → pipeline ngưng kênh còn lại. **Tối đa/lần** = `max_per_run`.
- **Kế hoạch 10 kênh**: preset chip 1-chạm-thêm; phân nhóm Sẵn sàng / Đang làm / Đã có video.
- **Thư viện video**: chia kênh → long/short, thumbnail như Drive, bấm = nhúng player phát ngay.
- **Báo lỗi thông minh**: chỉ đếm lỗi SAU lần thành công gần nhất (lỗi cũ = đã khắc phục); không lỗi mới + có video = banner XANH "đang chạy mượt".

## 4. Chuẩn chất lượng
- Long 16:9 ~8-12', 4-6 race/pillar cùng chủ đề. Short 9:16 30-55s, VIẾT LẠI (không crop). Mục tiêu/kênh: 100 long + 200-300 short.
- Hook 3s: ảnh+chart+số NGAY, giọng từ frame 0, KHÔNG card chữ tĩnh, KHÔNG outro/CTA.
  → Luật này CÓ TỪ ĐẦU nhưng code trôi mất nhiều ngày (dựng 2 thẻ chapter kẹp đầu-cuối). Nay đã có cổng chặn thật — xem **mục 4d**, đừng sửa code các phần đó mà không đọc 4d.
- Ảnh CC0/PDM (khỏi ghi nguồn); nhạc Kevin MacLeod CC-BY (ghi nguồn trong description). Nội dung gốc → monetize OK.
- Xóa Drive: CHỈ khi đã đăng ≥2 nền tảng (YouTube + FB/IG). Giữ lâu (archive).
- **ẢNH khớp ĐỊNH DẠNG + NỘI DUNG**: short lấy ảnh DỌC (aspect_ratio=tall), long lấy ảnh NGANG (wide) — đã làm trong fetch_image(orient). Query ảnh phải BÁM đúng câu đang nói (Gemini visual.query = 2-5 từ cụ thể, danh từ hình ảnh được — không trừu tượng). Mục tiêu: ảnh khớp nội dung ~100%.
- **KHÔNG CHE KHUẤT + ẢNH ĐÚNG KÍCH THƯỚC (bắt buộc kiểm mỗi thay đổi layout, cả long 16:9 lẫn short 9:16)**:
  - Phụ đề karaoke maxWidth 80% canh giữa (không chạm handle @/mép); handle @ góc phải-dưới; nhãn giá trị không tràn mép; năm góc phải-trên; hero góc phải — các lớp KHÔNG đè nhau.
  - Ảnh (nền/minh hoạ/hero) **KHÔNG quá nhỏ, KHÔNG tràn khung**: nền full-bleed objectFit cover; ảnh minh hoạ short = ~74% rộng khung dọc, long = hộp cố định phải; hero long ~68% cao. Ảnh phải khớp hướng (short=dọc, long=ngang).
  - QC-vision là CỔNG KIỂM BẮT BUỘC: chấm occlusion + ảnh quá nhỏ/tràn + text tràn mép. Ngưỡng nới (chỉ loại video hỏng thật) nhưng LUÔN log điểm + issue để soi.
- **10 KÊNH PHẢI KHÁC BIỆT RÕ** (không cùng 1 motip lặp lại): mỗi kênh KHÁC về kiểu đồ hoạ + layout + màu + chuyển động, không chỉ đổi accent. Ý tưởng phân hoá: STATEWARS→BẢN ĐỒ bang (WorldMapRace + states-10m.json, đã có engine); DATARACE→bar-race vàng/tiền; MONEYMOVES→ticker giá/hoá đơn; POWERPLAY→bong bóng market-cap/logo; GRIDIRON→bảng điểm sân cỏ; SCREENKINGS→poster/box-office; PAYCHECK→cuống lương; BODYUSA→infographic cơ thể; RIDEUSA→showcase xe; EATSUSA→thẻ menu/calo. → CẦN build dần, mỗi kênh 1 template engine riêng (KHÔNG dùng chung RaceLong cho cả 10).

## 4d. 🔴 CHUẨN CẤU TRÚC VIDEO — MỖI LUẬT GẮN VỚI 1 CỔNG CHẶN (21/8)

**Bài học gốc:** luật "KHÔNG card chữ tĩnh, KHÔNG outro/CTA" đã nằm ở mục 4 TỪ TRƯỚC, nhưng code
vẫn dựng 2 thẻ chapter kẹp đầu-cuối suốt nhiều ngày. Rule viết ra mà không có cổng chặn thì code
sẽ trôi khỏi rule mà không ai biết. Từ nay MỖI luật phải kèm cột "chặn ở đâu" — không có cổng thì
coi như chưa có luật.

| # | LUẬT | Chặn ở đâu (code) | Chặn cứng? |
|---|------|-------------------|-----------|
| 1 | **1 long : 3 short**, short đi SAU long và bám nội dung long | `run_render._ratio_plan()` — short tối đa = 3 × số long ĐÃ CÓ; hết chỗ thì BUỘC làm long, kể cả `make_long=False` | ✅ cứng |
| 2 | **KHÔNG intro, KHÔNG outro** (không thẻ chữ kẹp đầu/cuối) | `build_doc_props()` chỉ dựng cảnh nội dung; lời hook gộp vào cảnh 1, lời kết vào cảnh cuối. `qc_structure()` đếm `type=="chapter"` | ⚠️ cảnh báo |
| 3 | **Mở đầu = cảnh hook có FOOTAGE THẬT** — cấm chữ trên nền trơn | 6 lớp dự phòng trong `add_scene` (query cảnh 1 → 3 cảnh sau → tiêu đề → Gemini vẽ → mượn ảnh cảnh sau) → `qc_structure()` CHẶN nếu cảnh 0 không có clip → `opening_is_flat()` soi VIDEO ĐÃ DỰNG | ✅ cứng, 2 lớp |
| 4 | **Ảnh khớp nội dung 100%** | `_verify_image_rot()` (Gemini Vision, XOAY KEY khi 429). Không khớp → `False` → bỏ ảnh, thử ảnh khác | ⚠️ fail-open khi cả pool cạn |
| 5 | **Cắt cảnh 2-3s**, không đứng yên 1 ảnh | `add_scene`: `segs = round(dur / 2.6s)`, tối đa 3 ảnh/cảnh, lấy trong CÙNG 1 lần tìm Openverse. `qc_structure()` cảnh báo nếu 1 ảnh đứng > 3.5s | ⚠️ cảnh báo |
| 6 | **Có tiếng chuyển cảnh** | `Cinematic.tsx`: whoosh 0.55 mở màn + 0.4 mỗi nhịp cắt, dùng CHUNG `public/sfx/` với 9 engine khác | — |
| 7 | **KHÔNG fade đen đầu/cuối** | `Cinematic.tsx`: `vidFade = 1` (trước là fade 14 frame hai đầu) | — |
| 8 | **Không lặp một mô-típ** | 4 bố cục hook chọn theo hash tiêu đề → mỗi video một kiểu nhưng ỔN ĐỊNH khi render lại | — |
| 9 | **Mô tả không được ghi sai** | Credit nhạc CC-BY chỉ thêm khi `story["_music"]` thật | ✅ cứng |

### Thứ tự 3 lớp QC (rẻ trước, đắt sau)
1. **`qc_structure(props)` — TRƯỚC render, miễn phí.** 0 ảnh / mở đầu không footage → CHẶN, khỏi phí 2-4 phút CPU.
2. **`opening_is_flat(mp4)` — SAU render, miễn phí.** Đo pixel khung giây 1.2. Ngưỡng đo thật: có footage 43.9% tối · 1983 màu → đạt; ảnh thật TỐI 68.0% · 401 màu → vẫn đạt (không bắt oan); nền trơn 91.9% · 342 màu → BẮT. CHỈ áp cho `make_doc` (engine data-race mở bằng đồ hoạ có chủ đích).
3. **`_check_visual_rot(mp4)` — Vision, tốn quota.** Đặt CUỐI.

### ⚠️ Vision KHÔNG thay được luật cứng
`check_visual` chấm **khuyết tật**, không chấm **chuẩn hấp dẫn** — prompt ghi rõ *"chỉ dưới 50 nếu THỰC SỰ vỡ; sạch, đọc được = 80+"*. Một thẻ chữ trên nền đen thì sạch và đọc rất rõ → luôn 80+. Nó làm đúng việc được giao; việc đó không bao gồm "video có nhàm không". **Cái gì ĐO ĐƯỢC thì phải chặn bằng code, đừng giao cho AI.**

### Mọi khâu tốn quota Gemini PHẢI xoay key
Ba khâu, ba pool riêng (hết quota ẢNH không có nghĩa key hỏng cho VIẾT CHỮ):
`_AI_POOL` (vẽ ảnh) · `_VIS_DEAD` (Vision: `check_visual` + `verify_image`) · `key_manager` (viết kịch bản).
Bám `keys[0]` = key đầu cạn là khâu đó TẮT HẲN cả phiên mà log vẫn "thành công".

## 4b. TIẾT KIỆM TOKEN GEMINI (free ít token) — VẪN GIỮ CHẤT LƯỢNG (rule bắt buộc)
- Viết kịch bản: MIN_SCORE=90 **CỨNG** — chưa đạt thì VIẾT LẠI (MAX_TRIES=3), KHÔNG hạ chuẩn/không lấy bản <90; hết lượt vẫn <90 thì BỎ chủ đề (thà bỏ còn hơn ra rác). Token tiết kiệm nhờ thường đạt ngay vòng 1 (Gemini 94-100), không phải hạ bar.
- QC-vision: **thoát sớm** — khung 1 điểm ≥ (ngưỡng+20) là đẹp rõ → khỏi soi khung 2 (giảm nửa token vision). Fail-open khi 429.
- Ưu tiên **chặn deterministic MIỄN PHÍ trước** (cắt tên/unit, hướng ảnh, validate ảnh) hơn là để AI sửa sau.
- Health-check key ≤1 lần/20h + tận dụng lúc dùng thật (không list_models thừa).
- KHÔNG gọi Gemini lặp vô ích; prompt gọn; nhiệt độ hợp lý. Chất lượng đến từ RULE + engine, không phải gọi AI nhiều lần.

## 4c. XÓA THÔNG MINH — CHỐNG XÓA NHẦM (rule bắt buộc)
- Mỗi video job có **`pver`** (phiên bản pipeline, env PIPELINE_VERSION, hiện "v2"). Bump pver KHI có fix chất lượng breaking (handle/tràn/che/layout...).
- Dashboard "🧹 Dọn bản cũ" **CHỈ xóa video pver < bản mới nhất** → GIỮ NGUYÊN bản mới nhất → KHÔNG BAO GIỜ xóa nhầm bản tốt hiện tại.
- KHÔNG auto-xóa mù theo kênh/thời gian (dễ xóa nhầm chủ đề khác tốt). Xóa hàng loạt = theo pver hoặc bấm 🗑 từng cái.
- Video mới đã fix gốc (không tràn/che/handle sai) → không tích rác; chỉ cần "Dọn bản cũ" 1 lần cho đám pver cũ.
- Drive dùng THÙNG RÁC (trash) khi xóa → còn khôi phục 30 ngày. Nút "🧹 Đổ thùng rác" xóa vĩnh viễn thu hồi dung lượng ngay (rác vẫn tính quota tới khi đổ).
- **RENDER LẠI (🔄) an toàn + có hủy**: bấm 🔄 → confirm bắt buộc (tránh click nhầm) → tạo `render_requests` (status=pending) + cấp run_now. Job hiện "🔄 chờ render lại" + nút ⏹ Hủy. CHƯA chạy (pending) → hủy được (xóa request + clear cờ). ĐÃ bắt đầu (pipeline set status=processing) → KHÓA hủy (báo "không hủy được"). Xong → thay thế đúng bản (bỏ file cũ vào rác + xóa job cũ theo drive_id). process_requests chạy TRƯỚC vòng kênh → ưu tiên, KHÔNG chèn giữa gây rối tiến trình đang chạy.
- Mục "🚩 Nghi lỗi/bản cũ" CHỈ hiện bản CŨ (pver<mới nhất / flagged / QC<90) — v2 mới ở view "📺 Nhóm theo kênh". Đừng nhầm.

## 5. Lệnh hay dùng
```
# Trigger render (không có input FORCE — FORCE là env):
gh workflow run render_cron.yml --repo braydanamilio-spec/mq-vx-lab
# Xem log run:
gh run view <id> --repo braydanamilio-spec/mq-vx-lab --log
# Deploy: dashboard (firebase deploy --only hosting) · worker (wrangler deploy)
```

## 6. Còn lại (roadmap gần)
- Bung 10 kênh chạy SONG SONG (matrix workflow, mỗi kênh 1 job < 6h).
- Verify AutoPublisher tự đăng 1 lượt end-to-end.
- (Tuỳ chọn) cổng vision "render 1 still trước full" + thumbnail có chữ tiêu đề.
- User thêm SMTP_USER/SMTP_PASS để email cảnh báo gửi thật.

## 7. BUG LOG — LUẬT: MỖI LẦN CÓ LỖI/THAY ĐỔI PHẢI GHI VÀO ĐÂY (để không sai lại)
> Rule: gặp bug → fix → **ghi 1 dòng vào đây** (triệu chứng → nguyên nhân → cách fix). Thêm tính năng mới cũng ghi. Đọc mục này TRƯỚC khi sửa pipeline.

- **Asset 404 vỡ render** (cheer.mp3/geo/states): MỌI `staticFile()`/import trong engine PHẢI whitelist trong .gitignore, nếu không CI 404. Đã whitelist cheer/impact/pop/states.
- **Video 0 giây (QC dur=0)**: render chạy `cwd=engine-remotion` + `out` tương đối → file rơi vào ENG/out, QC/enqueue/artifact tìm ở gốc → mất file. FIX: `out=os.path.abspath(out)` đầu make_video/make_long.
- **Ảnh hỏng làm sập render**: 1 ảnh tải về lỗi/HTML → `<Img>` ném lỗi hủy render. FIX: fetch_image validate magic-byte (jpg/png/gif/webp), bỏ ảnh hỏng + `SafeImg` (onError → _fallback.jpg) trong RaceLong.
- **Gemini 2.5 → 404 user mới**: `_pick_model` né 2.5/2.0/1.x, ưu tiên 3.x flash/pro.
- **Key báo CHẾT oan (429)**: message 429 chứa "consumer" (trong danh sách DEAD) → báo chết oan. FIX: check RATE (429/quota) TRƯỚC DEAD → 429 = SỐNG (giới hạn tạm). test_key trả (alive|None, reason), thử lại 3 lần.
- **QC-vision loại video ngon**: 1 khung + ngưỡng 85 + veto overlap → chart-race nhiều nhãn bị đánh 42-72đ. FIX: 2 khung lấy điểm CAO NHẤT, ngưỡng 55, bỏ veto; + tiền-kiểm cắt tên nhãn ≤16 (chống cắt mép/chồng).
- **Enqueue lỗi "Không có kênh trong channels.yaml"**: channels.yaml/brands.json sửa LOCAL nhưng CHƯA push repo private → CI dùng bản cũ. LUẬT: sửa config AutoPublisher xong PHẢI `git push` repo private (CI checkout từ đó).
- **Xem video "Access Denied"/không tìm thấy kho**: file ở kho A, user login account B → chặn chéo. Worker tự-dò 22 kho dính giới hạn 50 subrequest/lần Cloudflare. FIX: (a) lưu `drive_account` vào job lúc enqueue; (b) dashboard dò-kho phía CLIENT (song song, không dính limit) + ghi lại vào job; (c) nút "🔗 Link full quyền" (anyoneWithLink). Video KHÔNG mất — publisher server-side đọc mọi kho.
- **Handle gắn NHẦM (@dataracehq cho mọi kênh)**: build_props default hardcode. FIX: `channel_handle(channel)` đọc brands.json (handle mỗi kênh khác: @statewarsusa, @moneymovesusa…), fallback @<kênh>hq. LUẬT: thứ gì per-kênh (handle/accent/motif/folder) KHÔNG được hardcode 1 kênh.
### 📅 21/8 — MỘT NGÀY, 15 BUG. NGUYÊN NHÂN GỐC CHUNG: xem cuối mục này

- **429 Firestore triền miên dù đã tách 3 project** ⭐ GỐC RỄ THẬT: mỗi lỗi 429 của **Gemini** gọi `cool_key()` → **1 lượt GHI Firestore**. Đo thật: 1.201 lỗi 429 trong MỘT phiên → 1.201 lượt ghi vào B; ×15 phiên/ngày ≈ 18.000, gần trọn hạn mức free 20.000. Càng nhiều 429 càng ghi nhiều → Firestore chết → cả dây chuyền đứng. **Tách project KHÔNG cứu được** vì lỗi Gemini đang BIẾN THÀNH lượt ghi Firestore. FIX: `cool_key` khử trùng lặp (chỉ ghi khi mốc nghỉ lùi xa thêm >60s) → giảm 95%.
- **`accuracy=10 < 92` ép viết lại 2-3 vòng MỌI video**: schema khai `"self_score": {"accuracy": int}` KHÔNG ghi thang điểm → model hiểu là điểm THÀNH PHẦN cộng vào total 100 (giống rubric ngay trên nó) nên trả ~10; code so với 92 → gần như luôn trượt. Đo: chỉ 28/186 video đạt vòng 1 → 378 lần gọi Gemini cho 186 video. FIX: ghi rõ `0-100` cho cả 10 schema. Sau fix: `đạt vòng 1` ở mọi luồng.
- **Video toàn CHỮ TRÊN NỀN ĐEN**: nhánh `type==="chapter"` trong Cinematic.tsx chỉ vẽ CosmicBg + chữ, KHÔNG nhận ảnh; mà cảnh mở đầu LUÔN là chapter, còn thumbnail lấy đúng khung mở đầu. FIX: bỏ hẳn intro/outro, cảnh 1 thành CẢNH HOOK có footage thật + số liệu to.
- **0 ảnh AI vẽ được / 209 lỗi**: `_generate_image_ai` nhận `api_key=keys[0]["key"]` → cả phiên dùng ĐÚNG 1 KEY. FIX: `_AI_POOL` xoay vòng.
- **Vision QC tắt hẳn cả phiên**: `check_visual(api_key=keys[0])` — cùng lỗi. FIX: `_check_visual_rot`.
- **Ảnh không khớp nội dung**: `verify_image(api_key=keys[0])` — CÙNG LỖI, sót lại sau 2 lần trên. FIX: `_verify_image_rot`.
- **Nhịp cắt 2-3s chết khi Vision 429**: `fallback` chỉ giữ MỘT ảnh → Vision hỏng thì cả cảnh 1 hình. FIX: `fallback` thành danh sách.
- **"quota cạn thật" khi mới thử 5/56 key**: mỗi 429 cắt key khỏi vòng xoay **90 phút** → pool teo ngay trong phiên. FIX: `AMBIG_COOL_MIN=20` + in `🔑 Pool key: N/56`.
- **Đồng bộ dung lượng kho chưa từng chạy**: `plan_mode` thiếu `sys.path` cho `storage` → `No module named 'storage'`, bị try/except nuốt nhiều ngày. FIX: nạp `AUTOPUBLISHER_SRC`.
- **Bước dọn video cũ trả rỗng**: `find_done_before` dùng `order_by` TĂNG DẦN + bất đẳng thức, mà index chỉ deploy bản DESCENDING. FIX: thêm index ASCENDING.
- **Short ra thumbnail 1280x2276** (YouTube từ chối âm thầm): `_make_thumb` dùng `scale=1280:-1`. FIX: ép 1280x720, nền mờ lấp hai bên.
- **Kênh ra "0 long · 3 short"**: 10 format đặc biệt rẽ vào nhánh CHỈ-SHORT, không có đường dựng long. FIX: `make_doc_long` (1 long + 3 short dùng chung giọng/ảnh) + `_ratio_plan` chốt tỉ lệ bằng SỐ ĐẾM THẬT.
- **Mô tả ghi công nhạc SAI**: credit Kevin MacLeod thêm vô điều kiện trong khi nhạc mặc định TẮT. FIX: chỉ ghi khi `story["_music"]`.
- **FB không có ảnh bìa**: chỉ YouTube đặt thumbnail. FIX: `set_thumbnail()` (Reels) + tham số `thumb` (video thường).
- **Dashboard báo kho Drive "đã kết nối" dù token chết**: chỉ biết khi bấm nút 🩺. FIX: publisher tự ghi health mỗi phiên (0 lệnh gọi API thêm).
- **Nhìn 481 tưởng mất 700 video**: dashboard đọc `limit(300)` từ A + 300 từ B = trần 600, không nói ra. FIX: hiện cảnh báo khi chạm trần.

- **2 listener dashboard KHÔNG GIỚI HẠN trên render_jobs** (đốt hạn mức ĐỌC âm thầm): đường lùi khi thiếu index mở realtime listener trên TOÀN BỘ bảng và giữ mở suốt. FIX: đường lùi cũng `limit(300)`.
- **Đọc lặp vô ích**: `recent_topics` 6 điểm gọi/kênh cho cùng 1 doc; `incr_key_requests` đọc-trước-ghi mỗi lần flush. FIX: đệm theo tiến trình (xoá khi save_topics) + chỉ đọc lần đầu/key/ngày.
- **PVER v2→v3 (21/8)**: chuẩn mới = cảnh hook footage thật · không intro/outro · cắt 2-3s · SFX · thumbnail khung hook. Video v2 = chuẩn cũ, dọn bằng nút "Dọn bản cũ".
- **Máy đo hoàn chỉnh**: mỗi luồng in `🧮 Firestore: N GHI (...) | M ĐỌC (...)` + `🔑 Pool key: N/56` + `🗺️ Firestore: A/B/C`. ĐỌC 3 DÒNG NÀY TRƯỚC khi điều tra bất kỳ nghi vấn quota nào.

- **Chấm ảnh HÀNG LOẠT (ý tưởng user)**: ghép các ứng viên của 1 cảnh vào 1 ảnh lưới (`qc_vision.verify_grid`) -> 1 lệnh Vision/cảnh thay vì 1 lệnh/ảnh. Video doc: ~8-14 gọi verify -> 3-4. Mù cả lưới -> fail-open; chấm hết False -> bỏ (thà không ảnh còn hơn ảnh sai). Muốn cắt nữa: gom CẢ VIDEO vào 1 lưới (verify_grid đã hỗ trợ subject riêng từng ô) = 1 gọi/video.

- **Giám khảo Vision phải TỰ CHỨNG MINH đáng tin**: verify_grid chèn Ô MỒI (ảnh nhiễu + chủ đề cụ thể) cuối mỗi lưới — model chấm ô mồi = true tức đang gật bừa (yes-bias) -> loại cả kết quả, fail-open. Kèm: tối đa 6 ô/lưới (đông hơn model lẫn thứ tự), "không chắc = false". Đếm tần suất dòng 🧪 trong log = tỉ lệ giám khảo bị loại — số đo độ tin thật.

- **6/10 giọng Wave 8 không tồn tại trên edge-tts** (Davis/Tony/Jason/Nancy/Brandon/Amber là Azure trả phí): bắt được nhờ kiểm `edge_tts.list_voices()` TRƯỚC khi seed — 6 kênh suýt chết ngay video đầu. LUẬT: config tham chiếu dịch vụ ngoài (tên giọng/model/API) PHẢI kiểm với danh sách SỐNG, không tin tên 'nghe quen'.

- **⭐ Render treo 'CPU đứng im 360s' hàng loạt (đêm 21/8, lane UNSOLVED 7/7 lệnh render chết, 0 video)**: Remotion `<Img>` CHỜ VÔ HẠN ảnh 404/hỏng (`Error loading image ... s5_1.jpg`) -> 0% CPU -> watchdog giết sau 6'/lần -> cháy cả lane. RaceLong có SafeImg từ đầu, Cinematic THIẾU. FIX 2 tầng: SafeImg (onError -> _fallback.jpg, render đi tiếp) cho mọi <Img> của Cinematic + `prune_ghost_clips()` lọc ảnh <1KB/không tồn tại khỏi props trước khi ghi. KIỂM CHỨNG: tái hiện đúng ca (props có ảnh ma) — trước treo, sau hoàn tất 5.9s. LUẬT: mọi component nhận ảnh động PHẢI dùng SafeImg, không bao giờ <Img> trần.

- **⭐⭐ HẠN MỨC GEMINI FREE THẬT = 20 request/NGÀY/KEY** (Google in thẳng trong lỗi 429 đêm 21/8: `generate_content_free_tier_requests, limit: 20, model: gemini-3.5-flash`). 56 key = **1.120 gọi/ngày TỔNG** — không phải ~14K như mọi ước tính trước. Chi phí ~4.5-6 gọi/video → trần thực tế **~150-250 video/ngày**. Muốn 1.000 video/ngày: cần ~250+ key HOẶC trả phí Gemini. MỌI kế hoạch quota phải tính từ con số 20 này.
- **SafeImg fix ĐÃ ĂN trên CI** (DEBTUSA đêm 21/8): 6 render hoàn tất thật (QC 96-98, 51-75MB), watchdog 0 lần giết — hết bệnh treo chờ ảnh. Cổng opening bắt được nền trơn thật; điều-kiện-2 (ít màu) giết oan 2/6 video màu trầm → đã hạ thành cảnh báo, giữ chặn cứng dark>=75.
- **3 kênh SÓT khỏi channels.yaml từ đầu (DEBTUSA/FILEUSA/VOXUSA)**: video QC đạt bị enqueue từ chối. Đợt vá "27 kênh" ngày 20/8 không phủ đủ. FIX: thêm 3 kênh (53 tổng) + LINT SO TẬP HỢP render_channels↔channels.yaml chạy mỗi plan — không bao giờ đếm tay nữa.

- **🐤 CANARY 0-quota trước mỗi luồng** (22/8): render 12 frame bằng asset tự tạo TRƯỚC khi tiêu gọi Gemini nào — engine hỏng thì luồng dừng ngay, quota nguyên vẹn (bài học 21/8: não viết 15 gọi/luồng xong render mới chết → đốt 1.120 gọi/ngày, 0 video). Đã chạy thật local: OK ~40s, cache theo tiến trình.
- **Groq tích hợp CHUNG KHO với Gemini** (22/8): key `gsk_` bỏ chung collection gemini_keys → thừa hưởng nguyên đồng bộ A→B, xoay vòng, cooldown, đếm request, health-check. Transport qua `_GroqShim` trong `_genai()` — mọi luồng VIẾT chạy Groq không sửa logic; 429 Groq map y 429 Gemini. Groq KHÔNG có vision/vẽ → mọi pool ảnh/Vision lọc bỏ `gsk_`. Dashboard: dán key gsk_ vào đúng ô key cũ, tự nhận diện; trần quota tính theo loại (Gemini 20 · Groq ~1K — kiểm console.groq.com/settings/limits).

> **🔴 NGUYÊN NHÂN GỐC CHUNG của 15 bug trên — đọc kỹ, đừng lặp lại:**
> 1. **Bám `keys[0]`** — 3 khâu riêng biệt (vẽ ảnh · Vision QC · kiểm khớp ảnh) đều mắc CÙNG lỗi này, và em fix từng cái một qua 3 lần thay vì rà cả lớp ngay lần đầu. **Hễ sửa một chỗ bám `keys[0]`, PHẢI `grep -n "keys\[0\]" *.py` rà hết.**
> 2. **Lỗi bị try/except nuốt** — sync kho hỏng nhiều ngày, key rotation là code chết, vision fail-open âm thầm. **Mọi `except` bọc bước QUAN TRỌNG phải in ra, và phải có phép đo (đếm/log số) chứ không chỉ "không thấy lỗi".**
> 3. **Rule có mà không có cổng chặn** — luật "KHÔNG card chữ tĩnh" nằm ở mục 4 từ lâu mà code vẫn dựng thẻ chapter. **Xem mục 4d: không có cổng chặn thì coi như chưa có luật.**
> 4. **Sửa ở tầng triệu chứng** — thấy 429 thì xoay key, rút cooldown… mà mãi mới hỏi "cái gì BIẾN 429 thành lượt ghi Firestore". **Khi một triệu chứng lặp lại lần thứ 3, DỪNG vá và đi ngược chuỗi nhân quả.**

- **Cron đăng ăn quota private (2000'/tháng)**: chuyển publish/social/cleanup/stats sang chạy trên repo PUBLIC (checkout private lúc chạy) → free vô hạn; TẮT cron repo private.
- **Nhãn giá trị TRÀN MÉP** (vd "215K USD (chained 2017)"): unit dài + thanh dài nhất đẩy nhãn ra ngoài khung. FIX: (a) cắt unit bỏ ngoặc + ≤6 ký tự trong _race_from_story; (b) BarChartRace chừa rộng hơn cho nhãn (landscape 180→230). LUẬT: mọi text trong video phải cap độ dài + test khung.
- **SystemExit giết CẢ MẺ** (audit): content_brain.generate/make_long raise SystemExit (không phải Exception) → `except Exception` không bắt → 1 kênh trượt QC là abort toàn bộ overnight. FIX: đổi sang Exception + bọc run_one trong `except BaseException` ở main. LUẬT: KHÔNG raise SystemExit trong pipeline, dùng Exception.
- **count_done cần composite index**: query 3 field equality → thiếu index thì FAILED_PRECONDITION làm sập run. FIX: try/except trả 0.
- **Worker dò kho vỡ giới hạn 50 subrequest** (audit): auto-discover 22 kho server-side ~90 subrequest → 404 oan cho video ở kho xếp sau. FIX: cache SA token 55' + CLIENT dò kho (drive-has song song) rồi ghi drive_account vào job → sau đó pass account trực tiếp, không fan-out. Bấm "🔍 Tìm kho cho video chưa rõ" 1 lần.
- **Dropdown avatar theme** (audit UI): custom dropdown hard-code màu tối → theme sáng thì chữ đen/nền đen mất chữ. FIX: dùng `var(--surface/--text/--border/--surface2)` (đúng cả sáng/tối); bỏ emoji thừa (avatar đã thay); refresh nút sau khi chọn; **memo `_avCache`** khỏi sinh lại SVG (RAM, KHÔNG ghi Drive/Firestore). LUẬT: mọi UI mới BẮT BUỘC dùng CSS var theme, không hard-code màu.
- **Listener permission-denied "Uncaught"** (audit): 4 onSnapshot (render_config/gemini_keys/render_channels/jobs-fallback) THIẾU error-callback → lúc auth khởi tạo văng permission-denied ra console (data vẫn về sau retry). FIX: thêm `,()=>{}` cho cả 4. LUẬT: MỌI onSnapshot phải có error-callback (im hoặc setLive(false)).
- **TỐI ƯU FREE 100% + KHÔNG SPAM** (luật đứng): (a) tính năng mới KHÔNG được phình dữ liệu — ưu tiên tính client-side (SVG/canvas in-memo), không tạo collection/ghi Firestore/Drive thừa; ảnh/thumbnail sinh runtime, không lưu. (b) Không đăng hàng loạt video na ná nhau / spam → tránh YouTube-FB gắn cờ; mỗi video 1 chủ đề riêng, chuẩn ≥90. (c) Đọc giới hạn (limit 300 job, read-cap gallery) giữ Firestore free dù data lớn.
- **10 LUỒNG SONG SONG (matrix)** (nâng cấp lớn): render_cron.yml = 2 job. **plan**: `run_render.py --gate` (nhẹ, nhịp 30' idle bỏ qua setup nặng) → nếu chạy: health-check + re-render + `--plan` xuất JSON danh sách kênh. **render**: matrix `channel` từ plan, `max-parallel:10`, `fail-fast:false`, mỗi kênh `--channel NAME` = 1 luồng riêng. Gating/health/re-render CHỈ ở plan (không lặp ×10). Fallback: `run_render.py` không cờ = tuần tự (chạy tay).
- **CHIA DRIVE ĐỀU + KHÔNG TRÀN KHI SONG SONG** (nâng cấp): (a) `ranked_accounts(seed=channel)` xoay điểm bắt đầu theo kênh (md5%N) → mỗi kênh nhắm kho khác → 10 luồng không dồn 1 kho. (b) **Reservation CHIA SẺ qua Firestore** `storage_reservations/{root}` (Increment bytes + at): `reserve()` GIỮ CHỖ (size thật + đệm 60MB) TRƯỚC upload → luồng khác trừ ngay khi tính free (`ranked_accounts` trừ `max(local, shared)`); lỗi/đầy → `release()` trả chỗ, nhảy kho kế; thành công → giữ (TTL 30' tự dọn khi usage() cập nhật / job crash). → 10 luồng cùng ghi KHÔNG làm tràn kho gần đầy.
- **RENDER TUẦN TỰ, KHÔNG SONG SONG** (kiến trúc cũ, đã thay bằng matrix ở trên): `render_cron.yml` = 1 job, `run_render.py` lặp `for ch in channels` TUẦN TỰ (mỗi kênh 1 long + 3 short lần lượt). KHÔNG phải 10 luồng song song. "Đang chạy: N" = số job đang [queued/running/rendering/qc] (có thể gồm job cũ kẹt). render_datarace/datastory.yml = chỉ manual (workflow_dispatch), không cron. Muốn 10 luồng → thêm matrix (1 job/kênh, free ≤20 concurrent) NHƯNG ×10 tốc độ đầy Drive + ×10 API → cân nhắc.
- **DRIVE TỰ CHIA 33 KHO** (xác nhận): enqueue.py → `ST.ranked_accounts(need)` = kho ĐỦ CHỖ, xếp free giảm dần; upload kho nhiều chỗ nhất, đầy/lỗi → nhảy kho kế; `ST.reserve` trừ tạm. 33 kho ≈ 495GB. Guard 90% tính TỔNG mọi kho.
- **DEFAULT KÊNH MỚI = long 100 / short 300** (user chốt): quick-add + form đặt sẵn 100/300 (tùy chỉnh sau tránh phình). Form: trống=100/300, gõ 0=mức dự trữ (10/30). Dashboard có **checkbox chọn nhiều + Chọn tất cả** → 🎯 Đặt target hàng loạt / 🗑 Xoá hàng loạt (`__rsBulkTarget/__rsBulkDelete`, state `__rsSelCh`).
- **GIỚI HẠN PHÚT vs QUOTA NGÀY — COOLDOWN THÍCH ỨNG** (audit mẻ đêm 18/8): 10 luồng song song dội Gemini → chạm "429 Request limit PER MINUTE per region". BUG: cool_key mặc định 90' cho MỌI 429 → key dính giới-hạn-phút (reset sau 60s) bị treo 90' → cả loạt key nghỉ → kênh HẾT KEY → fail hẳn (PAYCHECK: 0 video). FIX: (a) `key_manager._cool` xét message "per minute/region" → nghỉ NGẮN 2' (còn quota ngày → 90'); (b) write_story 2 VÒNG — cả loạt key dính ở vòng 1 → chờ 50s cho giới-hạn-phút reset → thử lại. Kết quả trước fix: 85 lỗi quota + 58 lỗi 403 nhưng key-rotation cứu 9/10 kênh (0 fail), chỉ PAYCHECK xui gặp lúc mọi key đang cool. LUẬT: phân biệt giới-hạn-phút (nghỉ ngắn) vs quota-ngày/403 (nghỉ dài); cả loạt dính → chờ reset, đừng fail ngay.
- **RENDER = LÀM DỰ TRỮ, UPLOAD = PIPELINE RIÊNG** (kiến trúc): render chỉ đắp kho video dự trữ trên Drive, KHÔNG upload. Upload theo template/logic thông minh riêng (sau). → "an toàn" cho render = chống phình Drive, KHÔNG phải chống spam (spam lo ở upload).
- **2 LỚP AN TOÀN RENDER** (nâng cấp): (1) **Guard kho gần đầy**: `FB.drive_usage` tổng used/cap mọi kho; ≥`drive_safety_pct` (mặc định 90%) → NGỪNG mẻ + ghi `last_safety_stop` (dashboard hiện banner đỏ 🛡️) + email. (2) **Mức dự trữ/kênh**: run_one target=0 → dùng `RESERVE_LONG/SHORT` (mặc định 10/30, chỉnh ở render_config.reserve_long/short) thay vì ∞ → không render vô hạn. Dashboard hiện `long X/10 🛡️` (🛡️=đang dùng mức dự trữ, chưa đặt target) và `⏸ đủ dự trữ, tạm ngừng` khi đạt. LƯU Ý: count_done tính TỔNG done; khi có upload+dọn sẽ đổi sang đếm bản CHƯA upload.
- **DỪNG THEO TỪNG CLIP** (nâng cấp): trước chỉ dừng ở ranh giới KÊNH (làm nốt cả 4 clip). Giờ `run_one._stopped()` kiểm cờ `stop` GIỮA từng short → clip đang render xong mới ngừng, KHÔNG bắt đầu clip/kênh mới (tiết kiệm, không dở dang/hư). Long luôn xong (không cắt giữa render). Nút ⛔ báo "làm nốt clip hiện tại rồi ngừng". Chạy lại: ▶️ Chạy tiếp / Render ngay.
- **TARGET SỬA ĐƯỢC + ĐẾM LIVE** (nâng cấp): dashboard `__rsRenderChList` hiện mỗi kênh "long X/∞ · short Y/∞" (đếm từ render_jobs done), nút 🎯 Target (`__rsSetTarget`) hiện đã-làm-bao-nhiêu để điền khớp → lưu long_target/short_target vào render_channels. Pipeline (run_one) đủ target thì bỏ qua loại đó (đã có sẵn), UI đánh dấu ✅ "đủ target, đã dừng". target 0 = ∞.
- **XÓA/BACK KÊNH AN TOÀN**: nút Xoá confirm rõ (chỉ xóa CONFIG kênh, VIDEO không đụng; mẻ sau ngừng làm; clip đang render vẫn xong). Xóa giữa run KHÔNG crash vì pipeline đọc danh sách kênh 1 lần lúc bắt đầu run (`FB.read_channels`). Cancel confirm/back trình duyệt = vô hại (state ở Firestore). Chưa có undo mềm — confirm đủ chống click nhầm.
- **XÓA CHỈ ĐỤNG VIDEO** (bất di bất dịch): mọi thao tác dọn/xóa (rsDeleteVideo/rsDeleteGroup/rsCleanOldExec/_trash_old/empty-trash) chỉ trash FILE VIDEO trên Drive + xóa bản ghi render_jobs. TUYỆT ĐỐI không xóa: method (.py/.tsx/.md), repo, brand kit, config kênh, topic/kịch bản đã lưu → luôn quay lại làm tiếp được. Video → Trash (khôi phục 30 ngày), không hard-delete. Chi tiết method+repo từng kênh: `CHANNEL_METHODS.md` (cập nhật khi đổi method/kênh).

- **3-PROJECT FIRESTORE SHARDING** (19/8, nâng cấp lớn chống nghẽn quota): A cạn 50K đọc/ngày do dashboard realtime + test tay → tách render (B) + publish (C) khỏi A. `firestore_bridge._db_meta()`/`_db_jobs()` route theo cờ `SHARD_META`; `firestore_state.py` tách `self.db`(A shared)/`self.pub`(C owned); dashboard `_appFor(collection)` router. Chi tiết: `SHARD_SETUP.md`/`SHARD_C_SETUP.md`.
- **storage_accounts ĐÃ shard nhầm sang B rồi phải REVERT về A** (19/8): connect-worker (Cloudflare Worker, ngoài hệ Firestore-sharding, KHÔNG có logic route) hardcode ghi Project A. Route collection này sang B → dashboard đọc B trong khi Worker ghi A → nút "🔄 Đồng bộ dung lượng" bấm vô tác dụng (số không đổi). FIX: revert cả dashboard (`_appFor`) lẫn pipeline (`firestore_bridge.py`) về A. LUẬT: collection nào có 1 SERVICE NGOÀI (Worker/3rd-party) ghi trực tiếp không qua code sharding-aware → giữ nguyên project của service đó, không tự ý shard.
- **2 REPO CÓ WORKFLOW TRÙNG TÊN — sửa nhầm bản không chạy** (19/8, lỗi nghiêm trọng nhất phiên): set `SHARD_PUBLISH=1` + thêm creds B/C vào publish.yml/cleanup.yml/publish_social.yml/stats.yml ở repo `mm0-auto-publisher` — nhưng bản THẬT đang chạy cron là bản Ở REPO `mq-vx-lab` (checkout code private lúc chạy, chạy trên public = free vô hạn). Sửa nhầm bản im lặng KHÔNG có tác dụng gì (không lỗi, không cảnh báo — chỉ đơn giản là code đó không bao giờ được thực thi). Hậu quả: publish auto-enqueue vẫn đọc render_jobs ở A (đông cứng từ lúc migrate) thay vì B, video mới không được xếp hàng đăng — âm thầm, không báo lỗi. FIX: vá đúng 4 file ở `mq-vx-lab/.github/workflows/`. LUẬT: sửa xong 1 workflow LUÔN `gh run list --workflow=X.yml --limit 5` kiểm bản đó có lịch sử chạy gần đây thật không, đừng tin "sửa xong là xong".
- **Round-cap rotation — kênh không được nhường slot cho nhau công bằng** (19/8): với target 100 long/300 short, `channel_mode()` không có trần → 1 kênh chiếm slot matrix tới hết ngân sách phiên (~3.5h) mới nhường; 20+ kênh > 18 luồng free → kênh dư xếp hàng cả phiên. FIX: thêm `round_long`/`round_short` (mặc định 10/30, `render_config`, đổi được ở dashboard "🔁 Xoay vòng") — check SAU khi `run_one()` hoàn tất trọn video (không cắt ngang) rồi break, nhường slot cho GitHub Actions matrix tự lấp bằng kênh đang chờ. `report["done_long"]`/`report["done_short"]` tách riêng từ `report["done"]` gộp cũ (3 chỗ trong `run_one` cần cập nhật cả 2 counter).
- **Dashboard realtime listener dư thừa đốt quota A** (19/8): `storage_accounts` (67 doc) + `channels` (stats/health) dùng `onSnapshot` trong khi đã có nút refresh tay ("Đồng bộ dung lượng") làm y hệt việc đó → mỗi lần đổi dữ liệu, mọi tab dashboard đang mở đọc lại toàn bộ. FIX: đổi sang `getDocs` load-once + tự refresh khi `window.addEventListener("focus",...)` (đúng lúc quay lại tab sau khi kết nối/đồng bộ ở tab khác) — giữ nguyên UX tự nhận thay đổi, giảm đọc thừa liên tục. LUẬT: collection đổi CHẬM (>vài phút/lần) + đã có nút refresh tay tương đương → không cần realtime, chuyển load-once.
- **🔴 2 file NHẠC chưa từng lên GitHub, gây 404 hàng loạt (19/8, không liên quan Wave 4)**: `.gitignore` chặn cả `engine-remotion/public/**`, chỉ 4/6 file nhạc thật đang dùng được whitelist thủ công trước đây (`carefree/broke_pad/mind_pad32/mindloop_pad`). `km_ascending.mp3` (mặc định SCALED + Wave 4) và `km_ossuary_air.mp3` tồn tại TRÊN MÁY nhưng KHÔNG track git → CI không có file → render fail hàng loạt (SCALED/GUESS/MAPPED, không phải do sửa Wave 4). Triệu chứng: dashboard báo lỗi mới dồn dập, "Command 'npx remotion render...' returned non-zero exit status 1", KHÔNG rõ nguyên nhân trong 110 ký tự đầu lưu ở Firestore. FIX: whitelist 2 file trong `.gitignore` + `git add -f` + push. LUẬT: mỗi lần THÊM 1 param `music=`/`staticFile()` mới trong code, PHẢI kiểm `git ls-files <path>` xem file đã lên git chưa — KHÔNG tin file "có trên máy" nghĩa là "có trên CI". Diagnose lỗi render bí ẩn: LUÔN kéo log CI đầy đủ (`gh api repos/.../actions/jobs/<id>/logs`) — trường `step` ở Firestore chỉ lưu 110 ký tự đầu, không đủ thấy nguyên nhân thật.
- **🔴 `category` field bị tái dùng nhầm, Gemini nhận mã số làm niche cho 16 kênh** (19/8): `run_one()` có `cat = ch.get("category") or niche` — field `category` này THIẾT KẾ GỐC (Wave 1) là gợi ý chủ đề con dạng text (vd "US cities"), nhưng seed script Wave 1-3 (phiên 19/8) tái dùng CHÍNH TÊN FIELD đó để lưu **mã YouTube category ID dạng số** ("24"/"27"/"28", dùng cho brand kit dashboard) → Gemini nhận "24" làm niche thay vì nội dung thật, cho CẢ 16 kênh (5 motif + 11 doc). Chưa gây video lỗi vì chưa tới lượt chạy thật (bị chặn bởi phiên cũ khoá ma trận, xem dòng dưới) — phát hiện TRƯỚC khi kịp gây hại. FIX: `cat = niche` (bỏ fallback nguy hiểm), dọn field `category` sai khỏi 16 doc Firestore B, xoá khỏi 2 seed script (tránh tái sinh khi seed lại). LUẬT: **KHÔNG tái dùng tên field đã có Ý NGHĨA KHÁC trong pipeline** — trước khi đặt tên field mới vào `render_channels`, `grep` xem `run_render.py`/`content_brain.py` có đọc field đó cho mục đích khác không.
- **🔴 Job treo (EATSUSA ~3h) khoá cổng render, video ngừng tăng nhiều giờ** (19/8, sự cố thật đêm 19/8): 1 job kênh treo (không rõ nguyên nhân gốc, có thể Remotion render kẹt) → `has_active_render()` coi cổng còn "đang chạy" VÔ THỜI HẠN → mọi phiên `render_cron` sau đó (mỗi 10') bị gate chặn, thoát trong 20-45s không làm gì. Cơ chế tự dọn job treo DUY NHẤT trước đó là JavaScript phía dashboard (`index.html`, cần MỞ trình duyệt mới chạy) — không ai mở dashboard = không bao giờ tự chữa. Kiểm thêm phát hiện **26 job cũ khác** cũng kẹt sẵn từ trước (chưa từng được dọn). FIX: (a) `health_guardian.py` mới + `health_guardian.yml` (cron mỗi giờ) tự đánh dấu `failed` cho job treo >6h, chạy SERVER-SIDE không cần dashboard mở; (b) thêm input `stale_hours` để can thiệp khẩn cấp bằng tay (`gh workflow run health_guardian.yml -f stale_hours=1`); (c) `render_cron.yml` là workflow production DUY NHẤT thiếu khoá `concurrency` (mọi workflow khác đều có) — thêm `concurrency: {group: mm0-render-cron, cancel-in-progress: false}` chống 2 phiên chạy chồng khi trigger tay rơi sát tick lịch tự động. LUẬT: mọi cơ chế tự-dọn/tự-chữa PHẢI chạy server-side (cron/workflow), KHÔNG được phụ thuộc ai đó mở dashboard — dashboard JS chỉ nên là lớp UI phụ, không phải nguồn duy nhất của logic an toàn.
- **♻️ Checkpoint/resume — không mất kịch bản khi job bị huỷ/treo/lỗi** (19/8, nâng cấp sau sự cố trên): trước đây job bị huỷ giữa chừng MẤT SẠCH kể cả khi Gemini đã viết xong kịch bản (bước tốn quota nhất) — phiên sau phải viết lại từ đầu. FIX: cả 12 hàm `make_X()` giờ tự ghi checkpoint (field `script`, tái dùng cơ chế lưu kịch bản có sẵn) NGAY sau khi Gemini viết xong, TRƯỚC bước render; nhận thêm `resume_story=`/`resume_checkpoint=` — có thì bỏ qua gọi Gemini, dùng thẳng. `firestore_bridge.find_resumable()` chỉ lấy job **status="failed"** (chắc chắn không ai đang xử lý — an toàn tuyệt đối) còn `script`; `run_render.py` dùng 1 lần cho video đầu mỗi vòng rồi `clear_resumed()`. Kết hợp Health Guardian: job treo → tự đánh dấu failed (giữ nguyên script) → phiên sau tự nhặt lại, không tốn quota Gemini.
- **1 phiên chạy tay CŨ khoá ma trận, chặn 16 kênh mới nhiều giờ liền** (19/8): kích `render_cron` tay (`force=1`) LÚC 07:31 để test B-shard — TRƯỚC KHI seed 16 kênh mới (wave1/2/3). `plan_mode` đọc `FB.read_channels()` MỘT LẦN lúc dispatch → matrix khoá cứng 10 kênh cũ, dù seed thêm kênh sau đó session ĐANG CHẠY không bao giờ thấy được (matrix cố định từ lúc plan chạy). Cộng thêm session này chạy TRƯỚC lúc push round-cap → không giới hạn, 5/10 kênh cắm cúi chạy tới đích hàng giờ liền, chiếm slot. LUẬT: **kích render tay để test → luôn kiểm sau đó có kênh MỚI thêm vào không; nếu có, đợi phiên đó tự xong (đọc `gh run list --status in_progress`) rồi mới seed/kích tiếp**, tránh 1 session cũ "khoá" danh sách kênh cả nhiều giờ. Đây cũng là lý do đổi gate sang `has_active_render` (dòng trên) — quan trọng: **cờ này chỉ mở phiên MỚI khi phiên CŨ đã xong hẳn — 1 phiên "ma" (dở dang lâu, dù đang chạy thật không lỗi) vẫn chặn phiên mới**, không phải bug, là thiết kế chống chồng phiên.
- **🔴 22/8 · 18/18 luồng phiên quyết định 04:22Z CRASH ~30'** — quota ĐỌC của B cũng cạn (không chỉ ghi); `read_keys`/`read_config` ném 429 xuyên `_retry`, caller viết `keys = FB.read_keys(...) or keys` (raise ≠ falsy nên `or` vô dụng). FIX: tầng **ĐỌC-MỀM** (`_RQ_DEAD` 15') — read_keys trả bản đệm cũ, read_config trả `_CFG_LAST`, recent_topics trả []. LUẬT (đối xứng ghi-mềm): *quota chết = mất telemetry, KHÔNG BAO GIỜ chết sản xuất* — mọi hàm ĐỌC mới thêm vào bridge phải có fallback đệm/mặc định, cấm để 429 ném lên caller.
- **🔴 22/8 · 10+ key Groq user thêm KHÔNG tới tay luồng render** — chuỗi 2 lỗi: (1) `sync_keys_from_a` ghi qua `_soft` đúng lúc B cạn quota GHI → lượt ghi bị nuốt im lặng, không dấu vết; (2) sync so A/B theo **doc id** trong khi dashboard `.add()` sinh id ngẫu nhiên. FIX: so theo **GIÁ TRỊ key** + LUÔN in `🔑 Sync key A->B: A=x · B=y · mới=z` (hết im lặng mù) + `_merge_a_keys()` hợp nhất key chỉ-có-ở-A vào pool ngay lúc ĐỌC (A gói Blaze, 1 lượt đọc bảng/10'/tiến trình) → key mới dùng được NGAY cả khi B không ghi nổi; giữ nguyên doc id A nên cool_key `set(merge)` tự tạo doc bên B khi quota hồi (tự lành). LUẬT: đường đồng bộ dữ liệu nào cũng phải IN SỐ ĐẾM mỗi lần chạy — "im lặng" không phân biệt được *0 việc* với *hỏng*.
- **🔴 22/8 · Groq GỠ model `llama-3.3-70b-versatile`** (test thật 14 key qua dashboard: /models 200 cả 14, nhưng chat/completions 404 "does not exist") — đúng model mặc định của `_GroqShim`, tức toàn bộ lượt viết Groq sẽ chết 404 ngay phiên đầu. FIX: mặc định mới `openai/gpt-oss-120b` (test 200, JSON chuẩn) + shim **tự-dò model sống**: gặp 404 model-đã-gỡ → hỏi `/models` → chọn theo danh sách ưu tiên `_GROQ_PREF` → thử lại, cache toàn tiến trình. LUẬT (lần 2 của bài học voice-ảo): tên model/voice/dịch vụ ngoài PHẢI được kiểm bằng LIVE list, và mọi tích hợp ngoài phải có đường tự-dò khi nhà cung cấp gỡ tài nguyên.
- **22/8 · Soi console THẬT: Project A đang gói SPARK (free 50K đọc/ngày), KHÔNG phải Blaze như vẫn tưởng** — và trưa 22/8 A cũng "Quota exceeded" khi đọc (dashboard mù, storage_accounts không đọc được). Hệ quả: bản đầu của `_merge_a_keys` (đọc lại A mỗi 10'/luồng ≈ 56K đọc/ngày) sẽ tự tay giết quota A → TIẾT CHẾ ngay trong ngày: chỉ đọc A khi pool B chưa có key gsk_ nào + tối đa 1 lần/tiến trình; sync ăn rồi thì nhánh tự tắt. LUẬT: trước khi viết code "đọc thêm cho chắc" phải NHÂN với 18 luồng × ~15 phiên/ngày rồi so với 50K — và gói billing của từng project phải KIỂM TRÊN CONSOLE, không tin trí nhớ.
- **22/8 · TỐI ƯU GỐC QUOTA ĐỌC (theo yêu cầu "tối ưu thực tế trước đã")** — đo lại: thủ phạm #1 là `read_keys` QUÉT CẢ BẢNG ~74 doc mỗi lượt × nhiều lượt làm tươi × 18 luồng × ~15 phiên ≈ 30-40K đọc B/ngày (mình tự đốt 60-80% hạn mức chỉ để đọc key). FIX: **snapshot 1-doc** `gemini_keys/__snap__<owner>` — sync_keys_from_a dựng lại mỗi phiên plan (tái dùng lượt quét sẵn có + 1 ghi), read_keys giờ = 1 đọc; không có snapshot thì fallback quét bảng như cũ; nằm trong collection gemini_keys nên hưởng nguyên rules KHÓA. Ước sau fix: toàn bộ key-logic ~3-4K đọc/ngày. Thủ phạm #2: dashboard mỗi lần mở đọc 300 job A (bảng ĐÔNG CỨNG từ 19/8!) + 300 job B + 300 videos → hạ 100/200/200, đỡ ~400 đọc/lần mở. LUẬT: bảng nào bị đọc lặp bởi NHIỀU tiến trình -> cân nhắc snapshot 1-doc do 1 chỗ duy nhất dựng; số đo (🧮) là căn cứ, không đoán.
- **22/8 · 2 nấc tối ưu GHI (user duyệt làm luôn)**: (1) hãm mốc trạng thái trung gian của update_job 5'→10' — nhịp tim nền 15' vẫn lo phần "còn sống" (guardian 45'), video không ảnh hưởng; (2) **sổ đếm request gộp 1-doc** `gemini_keys/__req__<owner>` (field-level `Increment` nguyên tử, owner="__req__" để scan không quét trúng) — 1 lượt ghi/luồng thay vì 1 ghi/key (3-8), plan reset đầu ngày-google, read_keys overlay số vào rows nên key_order vẫn ưu tiên key ít dùng. LUẬT: counter nhiều-đối-tượng ghi bởi nhiều tiến trình -> 1 doc + Increment theo field, đừng rải mỗi đối tượng 1 lượt ghi.
- **22/8 · TÍCH HỢP CLOUDFLARE WORKERS AI (nhà cung cấp #3, user yêu cầu)** — free 10K neuron/ngày/tài khoản (reset 00:00Z) ≈ ~1.3K lượt LLM HOẶC ~2K ảnh FLUX 512². Key dạng `cf:<account_id>:<api_token>` (dashboard tự bọc từ input `ACCOUNT_ID:TOKEN`), chung collection gemini_keys -> thừa hưởng sync/snapshot/xoay vòng/cooldown y Groq. PHÂN VAI THEO THẾ MẠNH: VẼ ẢNH = CF FLUX schnell TRƯỚC Gemini (`_cf_flux_image`, pool `set_ai_pool` xếp cf đầu) · VISION = Gemini trước, CF fallback (`_vision_order`; `_CfShim.generate_content` nhận [text, ảnh] nên qc_vision chạy nguyên bản, ô mồi tự loại giám khảo ẩu) · VIẾT = chót bảng sau Groq+Gemini (để dành neuron cho ảnh). 4006 "neuron limit" map thành chuỗi 429 -> cool_key/xoay vòng xử như cũ. Tag log ⛅. CHƯA có key thật để test sống — phiên đầu tiên sau khi user thêm key phải soi log ⛅ (model vision/text có thể cần đổi qua env CF_VISION_MODEL/CF_TEXT_MODEL nếu CF đã gỡ — có tự-dò 404 cho text qua danh sách _GROQ_PREF-style chưa? KHÔNG, chỉ Groq có; nếu 404 thì sửa env, ghi chú lại đây).
- **22/8 · Thứ tự viết đổi thành Groq→CF→Gemini** (user hỏi trúng): Groq trục trặc thì CF gánh chữ, KHÔNG đốt đạn Gemini — vì đạn Gemini là thứ duy nhất không thay được (Vision). Groq/CF cùng chạy gpt-oss-120b nên chất lượng chữ y hệt.
- **22/8 · ĐẤU LOẠI CHỦ ĐỀ (nâng chất lượng đề tài)**: plan_pillar với key Groq/CF sinh 3 phương án pillar (1 lệnh) + giám khảo temperature-0 chấm curiosity gap/stakes/độ mới rồi chọn (1 lệnh) — thay vì lấy ý tưởng đầu tiên. Key Gemini giữ 1 lệnh cũ (đạn hiếm). Giám khảo lỗi -> phương án 1, không chặn sản xuất. Log: `🏆 Đấu loại chủ đề: chọn phương án N/3 — <lý do>`.
