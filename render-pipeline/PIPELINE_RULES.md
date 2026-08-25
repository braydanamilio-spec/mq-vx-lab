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
- **🔴 22/8 · Phiên ĐẦU TIÊN Groq vào trận (07:07Z) chết cả 18 luồng trong ~90s**: `_GroqShim.GenerativeModel()` không nhận `system_instruction` mà plan_pillar/generate_doc (30 chỗ) đều truyền → TypeError, xoay hết key Groq đều dính (cùng shim), lane thoát sạch. Không lộ sớm vì các phiên trước key Groq chưa từng có mặt trong pool (B thiếu key — bug sync). FIX: cả _GroqShim lẫn _CfShim nhận `system_instruction=None, **kw`, map thành message `role=system` chuẩn OpenAI. LUẬT shim: shim đội lốt SDK phải phủ ĐỦ chữ ký các call site thật — grep mọi cách gọi (`GenerativeModel(`, `generate_content(`) trước khi ship, và test shim bằng đúng đường gọi sản xuất (write_doc/plan_pillar), không chỉ gọi tay.
- **🔴 22/8 · Dashboard TREO TRẮNG ("Đang tải bảng điều khiển…") sau deploy brand kit Wave 8** — script chèn entry vào RS_BRANDS thêm dấu phẩy thừa (entry cuối đã có phẩy sẵn) → SyntaxError chết CẢ module script → trang không khởi động. Phát hiện bằng `node --check` từng <script> (script #0 lỗi dòng "    ,"). FIX: xoá phẩy + LUẬT MỚI: mọi lần sửa index.html PHẢI chạy node --check toàn bộ inline script TRƯỚC khi deploy (đã làm thành bước chuẩn); user thấy trang treo = nghĩ ngay đến deploy gần nhất, curl bản live về check cú pháp là ra trong 1 phút.
- **22/8 · Cổng mở-đầu-tối giết oan 4/6 short COSMOS (phiên Groq đầu 07:40Z)**: kênh thẩm mỹ TỐI CHỦ ĐÍCH (vũ trụ/đáy biển) có khung mở dark 75-86% nhưng 737-992 màu — là ảnh không gian thật, không phải thẻ chữ. FIX: `_dark_ok(channel)` (DARK_OK_CHANNELS=COSMOS,THEDEEP,UNSEENUSA,FUTUREUSA,UNDERUSA, đổi được qua env) -> nhóm này chỉ chặn chữ ký nền-trơn THẬT (dark>=88 & cols<450, đo 91.9/342). Video bị loại oan có script lưu -> find_resumable tự nhặt render lại phiên sau, không mất gì. LUẬT: ngưỡng QC dựa trên pixel phải phân theo THẨM MỸ KÊNH, không một ngưỡng cho cả 53 kênh.
- **22/8 · Phiên Groq đầu tiên end-to-end THÀNH CÔNG (COSMOS, 07:40Z)**: `DOC đạt vòng 1: total 98, acc 100`, 2 short vào hàng đợi, sổ ghi gộp `1 lượt ghi gộp` chạy, snapshot `read_keys_snap=6`/`req_overlay=6` đúng thiết kế. Còn lại trong log: Nano Banana 61 key cạn hạn mức ảnh (Gemini vẽ free rất bé — key CF FLUX user đang thêm sẽ gánh từ phiên sync kế), vision-skip 429/504 (fail-open đúng thiết kế, CF vision sẽ đỡ thêm).
- **22/8 · ĐÍNH CHÍNH hạn mức free Cloudflare (tự tính từ giá niêm yết, không tin trang thứ 3)**: 10K neuron/ngày/tài khoản = ~174 ảnh FLUX 1024² (4 bước, 58n/ảnh) HOẶC ~60 bài viết ngắn gpt-oss-120b (~166n/bài) — KHÔNG phải "~2.000 ảnh" như trang review viết (sai ~12 lần). Đã hạ FLUX steps 6→4 (schnell thiết kế cho ≤4 bước, +34% ảnh, chất lượng không đổi). Kế hoạch: FLUX gánh trọn ảnh AI ở 500 video/ngày cần ~10-15 tài khoản; 30-50 tài khoản = dư cho cả thumbnail đấu loại + vá footage yếu. LUẬT: hạn mức nhà cung cấp phải TỰ TÍNH từ bảng giá chính thức hoặc ĐO THẬT — cấm trích số bên thứ ba.
- **22/8 · `groq HTTP 403: error code 1010` (EMPIREUSA long)** — WAF Cloudflare TRƯỚC api.groq.com chặn chữ ký bot của urllib (UA "Python-urllib", IP GitHub runner), lẻ tẻ. FIX: gắn UA danh tính rõ (`Mozilla/5.0 (compatible; MM0-render/1.0; +url)`) cho MỌI lệnh urllib (Groq chat/models, CF shim, FLUX) + map 403-1010 thành lỗi TẠM per-minute (nghỉ 1.1', xoay key) thay vì đánh trượt video. LUẬT: mọi client REST tự viết phải có User-Agent tử tế ngay từ đầu — API nấp sau WAF là chuyện mặc định thời nay.
- **22/8 · TẦNG TỰ-LÀNH HOÀN CHỈNH (mục tiêu: hệ chạy KHÔNG CẦN AI CANH)** — bản đồ 8 lớp lỗi ↔ cơ chế tự xử:
  (1) bản push hỏng → **selftest.py** chạy đầu MỖI phiên (0 mạng/0 quota, 8 mục qua đúng đường gọi sản xuất) — fail là chặn phiên, lane không spawn;
  (2) quota Firestore chết (đọc/ghi) → đọc-mềm `_RQ_DEAD` + ghi-mềm `_WQ_DEAD` + `_PENDING` xả lại;
  (3) nhà cung cấp AI gỡ model → Groq + CF đều tự-dò model sống từ danh sách ưu tiên;
  (4) WAF/429/1010 → UA tử tế + map lỗi tạm + xoay key + cooldown RAM;
  (5) render treo/ảnh 404 → SafeImg + watchdog + canary + health_guardian dọn job ma mỗi giờ;
  (6) video hỏng QC/lane chết giữa chừng → checkpoint kịch bản + find_resumable tự render lại;
  (7) kho Drive chết token → publisher skip kho hỏng, xoay kho khỏe (GỐC của invalid_grant lặp lại: OAuth app ở chế độ Testing — token 7 ngày tự thu hồi; fix 1 lần: PUBLISH APP trong Google Cloud Console — việc của user);
  (8) dashboard deploy hỏng → luật node --check trước deploy.
  Việc DUY NHẤT hệ không tự làm được: sửa code cho LỚP LỖI CHƯA TỪNG GẶP — selftest thu hẹp còn đúng phần đó, và mỗi lớp mới xử xong PHẢI thêm 1 test vào selftest.py (luật trong docstring).
- **🔴 22/8 · 16/18 lane phiên 07:40Z bị trần matrix 150' CHÉM giữa chừng** — channel_mode tự đặt ngân sách 210'/330' (bộ số viết thời timeout workflow còn 350') nên lane "tưởng còn cả tiếng" và cứ mở mẻ mới ở phút 120+. Video đã queue trước đó VẪN CÒN (queue theo từng video), kịch bản checkpoint giữ — chỉ phí phần render đang dở. FIX: ngân sách mềm 110' + cứng 150', matrix timeout 150→165 (buffer 15') -> lane tự thoát sạch (flush đủ, không job ma) trước khi bị chém. LUẬT: MỌI hằng số thời gian trong code phải ghi rõ nó phụ thuộc timeout nào — đổi timeout ở yml thì grep các hằng bám theo (batch_budget/HARD_S/watchdog).
- **22/8 · `groq HTTP 413 Request too large` (VAULTUSA, 16 job 0 video)** — Groq free giới hạn ~8K token/request; prompt DOC (system+niche+avoid 120+ngữ cảnh) vượt cỡ → key nào cùng nhà cũng dính, video trượt sạch dù còn 60 key Gemini ngồi không. FIX: write_doc gặp 413 → BỎ CẢ NHÓM nhà đó (skip prefix) → đi thẳng Gemini. Phân vai thực tế: Groq gánh prompt NHỎ (plan_pillar, đấu loại, chấm điểm, short gọn); prompt lớn về Gemini. Việc sau (đo rồi làm): ăn kiêng prompt DOC (~12K→<8K token) để Groq gánh lại phần viết chính. LUẬT: lỗi lặp y hệt theo NHÀ cung cấp (413/cỡ context) -> skip theo nhà, đừng xoay từng key.
- **22/8 · 429 BURST THEO PHÚT lúc plan (10:17Z)** — plan bắn ~106 lệnh count liền tay (53 kênh × long+short) → Firestore chặn theo phút (KHÔNG phải cạn ngày — lane 7' sau đếm bình thường). Hậu quả kép: (a) count trả "coi như 0" → _ratio_plan tưởng 0 long 0 short → ép long sai + đếm target thiếu; (b) sync_keys trượt → 10 key CF user vừa thêm chờ phiên sau. FIX: _count_jobs bọc _retry (backoff 1.5-7.5s vượt burst) + sync_keys tự thử lại 1 lần sau 8s (cờ chống đệ quy). LUẬT: 429 có HAI loài — theo NGÀY (chờ reset) và theo PHÚT (backoff là qua); mọi đường đọc quan trọng phải phân biệt được, đừng thấy 429 là kết luận "cạn ngày".
- **22/8 · TRIỆT ĐỂ QUOTA ĐỌC B (yêu cầu user "B hơi tốn")** — đo VAULTUSA 113 đọc/luồng thì 105 lượt là 4 hàm gọi lặp cho CÙNG câu trả lời: find_resumable=40, top_titles=32, read_config=17, count_done=16. FIX: `_HOT_CACHE` tiến-trình — top_titles đệm vĩnh viễn/luồng (gu khán giả không đổi trong 1 luồng), find_resumable nạp 1 lần phát dần (pop), read_config TTL 60s (nút Dừng trễ ≤1'), count_done TTL 90s (mẻ >5' nên mỗi vòng vẫn tươi). Ước còn ~30-35 đọc/luồng (từ 113). LUẬT: hàm đọc nào bị gọi >5 lần/luồng cho cùng tham số -> phải có đệm tiến-trình, kiểm bằng dòng 🧮.
- **🔴 22/8 · MỌI RENDER LONG chết đúng giây 360 ("CPU đứng im 360s")** — watchdog đọc utime+cutime của tiến trình CHA (npx), mà Linux chỉ cộng cutime/cstime SAU khi con thoát: Chrome con cày 30' nhưng đồng hồ cha đứng im -> giết oan mọi long -> luật 1:3 chặn short theo -> sản lượng đứng hình 2h (user phát hiện "2h không tăng"). Short <360s nên không bao giờ lộ. FIX: (a) Popen start_new_session + đo CPU CẢ NHÓM SỐNG qua /proc pgrp; (b) treo thật -> killpg cả nhóm (hết chrome mồ côi); (c) trần cứng riêng cho Cinematic(long) 3600s (2 core render long 10'+ mất 30-50'). LUẬT: đo tiến trình nào PHẢI hiểu ngữ nghĩa /proc (cutime chỉ nhảy sau reap) — mọi watchdog đo CPU phải đo theo NHÓM, và test cả ca "con cày, cha im".
- **22/8 · SỐ LIỆU DASHBOARD "RỐI TÙM LUM" (1058 tổng · đã tải 74 · kênh 7/9/11)** — mỗi ô lấy MỘT nguồn khác nhau (server-count vs danh sách đã cắt). FIX kiến trúc: **sổ thống kê 1-doc** `render_stats/{owner}` — pipeline ghi {kênh:{l,s}} cuối mỗi luồng (1 ghi mềm, số từ count_done đã đệm), dashboard đọc 1 doc/5' làm nguồn sự thật cho MỌI ô. Rules B thêm render_stats CHỈ-ĐỌC (bản rules B giờ lưu tại `render-pipeline/shard_b.firestore.rules`; sửa rules B = sửa file này rồi phát hành qua firebaserules API — firebase.json của dashboard trỏ rules A, deploy nhầm là ĐÈ B bằng rules A!). LUẬT: một con số hiển thị ở nhiều nơi phải có MỘT nguồn; nguồn = doc tổng hợp do server ghi, không phải client tự đếm từ danh sách bị cắt.
- **22/8 chiều · 20 key CF kẹt ở A cả ngày** — B cạn quota ĐỌC nên sync chết mọi phiên (retry vô ích tới 07:00Z); điều kiện hợp-nhất-A cũ chỉ kích hoạt khi thiếu gsk_ → CF vô hình. FIX: hợp nhất khi thiếu BẤT KỲ nhà nào (gsk_/cf:), tự tắt khi sync hồi. Kèm 2 vá 413 đường LONG: plan_pillar 413 → lập pillar lại bằng Gemini; avoid trim còn 35 mục cho nhà 8K-token (đo thật: request 9069 > trần 8000).
- **22/8 đêm · burst 429 tái diễn ở plan (13:55Z)** — cả loạt count/sync/drive_usage bắn cùng giây → chết chùm dù từng lệnh có _retry (retry chồng retry còn làm bão to). FIX: RẢI NHỊP 0.35s/kênh trong vòng đếm plan + nghỉ 2.5s trước sync. LUẬT: vòng lặp gọi Firestore >20 lần phải có nhịp rải ngay từ đầu — backoff cứu lẻ, không cứu bão.
- **22/8 tối · van xả GHI khẩn (B 12K/20K lúc 14:40Z)** — cool_key bỏ ghi Firestore cho lệnh nghỉ NGẮN (<5', per-minute trong bão ảnh) — sổ RAM _COOLED đủ né trong tiến trình, luồng khác cũng chẳng kịp hưởng lượt ghi đó; chỉ nghỉ dài (quota ngày) mới ghi chia sẻ. Cắt ~60-80% cool_key writes. LUẬT: lượt ghi nào vòng đời NGẮN hơn thời gian để bên khác đọc được nó = ghi vô nghĩa, RAM là đủ.
- **🔴 22/8 · GỐC RỄ THẬT của 413 Groq**: "Requested 9069, Limit 8000" = INPUT + MAX_TOKENS (shim khai 8192) — tức MỌI lệnh Groq đều tự vượt trần bất kể prompt, các vá trim-avoid chỉ chữa triệu chứng. FIX: max_tokens 8192→3600 (JSON dài nhất ~2.5K tok) → input+max luôn <8K → Groq viết lại được TOÀN BỘ kể cả doc dài; các fallback 413 (skip nhà/pillar→Gemini) giữ làm lưới. LUẬT: đọc kỹ CÁCH provider đo limit (họ đếm cả max_tokens!), đừng chỉ đo prompt.
- **🔴 22/8 tối · 9 VIDEO EMPIREUSA QC 98 BỊ VỨT dù render hoàn hảo ("Chưa kết nối tài khoản kho nào")** — chuỗi tự bắn chân 3 khâu: (1) A nghẽn 1 nhịp → `_merge_a_keys` stream ném mà KHÔNG đệm kết quả → lần đọc kế thử lại → 9 lần × 70 = 630 đọc A/luồng × 18 luồng tự đấm A gục thêm; (2) `firestore_pool_accounts()` (danh sách kho Drive, cũng đọc A) gặp lỗi → trả `[]` trần → enqueue dịch "lỗi mạng" thành "0 kho" → SystemExit từ chối; (3) job vẫn ghi done «Xong (chưa đẩy Drive)» → runner chết → mất file, chỉ còn script. FIX 3 tầng: (a) merge lỗi → đệm rỗng luôn (1 phát/tiến trình); (b) pool_accounts thử lại 8s/25s rồi dùng ĐỆM CŨ quá-TTL, chỉ trả [] khi cả đời tiến trình chưa đọc được lần nào; (c) `heal_unpushed` chạy 1 lần/phiên ở plan: done + drive_id rỗng + có script trong 8h → lật failed → find_resumable render lại TỪ SCRIPT (0 quota AI) + đẩy kho. LUẬT: (i) lỗi đọc KHÔNG BAO GIỜ được dịch thành "danh sách rỗng" ở đường quyết định vứt/giữ sản phẩm; (ii) mọi nhánh đọc-1-lần/tiến-trình phải đệm CẢ THẤT BẠI, không chỉ thành công.
- **22/8 tối · plan 15:36Z: `name 'time' is not defined` GIẾT CẢ VÒNG ĐẾM chọn kênh** — vá anti-burst thêm `time.sleep(0.35)` vào vòng count nhưng run_render KHÔNG import time ở module (chỉ có `import time as _tt` cục bộ ở block khác); except nuốt lỗi → mọi kênh "thiếu 1+1" → chọn kênh vô nghĩa + anti-burst không chạy + kênh đủ chỉ tiêu vẫn chiếm slot. Kèm lỗi 2: `need.sort(-thiếu)` XÓA SẠCH ưu tiên _pri xếp trước đó (kênh cũ thiếu 30 đè kênh mới priority=1). FIX: import time module-level; sort 2 khóa (priority, -thiếu). LUẬT: (i) dùng module gì trong hàm thì import module-level, ĐỪNG dựa vào import cục bộ của block khác; (ii) mọi "xếp ưu tiên rồi sort lại sau" là mâu thuẫn tự hủy — ưu tiên phải nằm TRONG khóa sort cuối cùng.
- **22/8 đêm · FLUX IN CHỮ GIẢ lên ảnh brand (đo 6 lượt vẽ thật)** — 2 bẫy prompt: (a) từ vựng quảng cáo ("advertising" trong style HANKTOWN) -> vẽ poster kèm chữ to "Hel.ly DAD!"; (b) TÊN RIÊNG VIẾT HOA (PEARL trong style TRUETALES) -> in thẳng "PEARL"/"MOSE" lên cửa sổ/hộp thư; trong khi 2 kênh không dính bẫy (BALDBANDIT/EXPLAINUSA có "no signs, no lettering, no text") ra sạch 100%. FIX 3 lớp: (1) _toon_safe thêm advertising->animation + XÓA token VIẾT-HOA-TOÀN-BỘ >=3 ký tự (PEARL/BISON/USA/UPA đều bị FLUX vẽ thành chữ); (2) áp _toon_safe cho CẢ style-lock lẫn prompt ngay lượt đầu (trước chỉ prompt + chỉ lượt retry); (3) gột tên riêng khỏi toon_style trong wave8_channels.json. Selftest thêm assert. LUẬT PROMPT VẼ ẢNH: mô tả nhân vật bằng ĐẶC ĐIỂM (không tên riêng), cấm từ vựng poster/quảng cáo, luôn chốt đuôi "no signs, no lettering, no text"; nghi ngờ thì soi ảnh thật — 6 ảnh đo được hơn 60 phút đoán.
- **22/8 khuya · Cover brand bị "mất góc" (user bắt)** — FLUX chỉ ra ảnh VUÔNG; crop dải 16:9 từ vuông zoom-sát là toán học không thể đủ (nhân vật cao ~85% khung > dải 56%) -> đại bàng cụt đỉnh đầu, PEARL cụt bình trà. FIX chuẩn 2 bước: (1) prompt thêm "wide establishing shot, characters small in center, large empty margins, space above heads/below feet" -> FLUX tự chừa lề trong ảnh vuông; (2) dựng 16:9 bằng LETTERBOX kéo-màu-mép-theo-từng-hàng (không crop): vuông đặt giữa canvas 2560x1440, mỗi hàng lề trái/phải tô đúng màu pixel mép hàng đó -> nền phẳng/gradient/dải ngang (siding, cỏ, trời) nối liền vô hình. KHÔNG dùng SVG vẽ tay cho mascot. LUẬT: ảnh vuông -> khung chữ nhật thì hoặc chừa lề từ lúc vẽ, hoặc letterbox kéo mép — cấm crop dải qua thân nhân vật; dựng xong PHẢI mở ảnh soi lại bằng mắt trước khi deploy (lỗi này lọt vì deploy không soi).
- **🔴 23/8 rạng sáng · A cạn quota ĐỌC CẢ NGÀY -> mọi video từ ~14:00Z bị TỪ CHỐI đẩy kho** (retry 8s/25s vô ích vì không phải nghẽn nhịp — thủ phạm chính là bão merge_keys 630×18×3 phiên trưa trước khi được vá). Đau nhất: danh sách kho Drive (connections, token) chỉ sống ở A -> A chết là khâu đẩy kho chết theo dù B khỏe. FIX kiến trúc 3 mảnh: (1) `mirror_connections_to_b` — plan chép connections A→B collection `connections_mirror` mỗi phiên khi A còn thở (rules B catch-all deny nên token kín, chỉ SA đọc; so giá trị chỉ ghi doc đổi); (2) publisher `firestore_pool_accounts` fallback đọc gương B khi A chết + hết đệm; (3) `heal_unpushed` HOÃN khi (A chết && gương rỗng) — không lật failed để lane render lại rồi LẠI bị từ chối = vòng churn đốt máy cả đêm. LUẬT: dữ liệu mà một khâu SỐNG CÒN phụ thuộc (danh sách kho, key) phải có bản sao ở shard khác — "1 project chết không kéo khâu khác chết theo" (đúng tinh thần luật 3-project-độc-lập).
- **🔴 23/8 03:11 VN · GATE ĐÓNG CẢ ĐÊM vì B cạn quota đọc (mẻ 20:00Z ra mắt toon bị giam oan)** — read_config chết -> trả {} -> `enabled=False` -> gate false NGAY CẢ GIỜ MẺ; tiến trình CI mới không có đệm config nên đêm nào quota đọc chết là dây chuyền đứng máy tới reset. FIX: (a) gate FAIL-OPEN — cfg rỗng (quota chết) thì coi như enabled (hệ 24/7: mất liên lạc config thì chạy tiếp, nút Dừng chỉ trễ tới khi quota hồi); (b) plan "0 key" khi _RQ_DEAD đang bật là số ẢO -> bỏ mẻ im lặng, KHÔNG bắn email "hết key" giả mỗi 30'. LUẬT: mọi cổng an toàn phải chọn CHIỀU HỎNG có chủ đích — hệ sản xuất tự động thì mất-tín-hiệu = CHẠY (fail-open), chỉ tín hiệu Dừng tường minh mới dừng.
- **23/8 sáng · SỔ QUOTA NGÀY + CHUÔNG BÁO (từ bài học "cháy ngầm")** — hôm 22/8 chỉ soi quota GHI theo lời hứa (12K/20K lúc 14:40Z, giữ đúng) mà không CHIẾU LŨY KẾ ĐỌC cả ngày -> đọc cháy từ trưa (bão merge trước khi vá), tối lộ ra thì dây chuyền đứng 9 tiếng tới reset. FIX: mọi tiến trình cuối đời Increment số ĐO THẬT vào `render_stats/__rw__{owner}.{yyyymmdd}` (1 ghi); plan đọc 1 lượt/phiên in "📟 Sổ quota hôm nay: ĐỌC x/50K · GHI y/20K" + chuông ⚠️60% / 🚨85%. LUẬT: tài nguyên có TRẦN NGÀY thì phải theo dõi ở tầm NGÀY (lũy kế + chuông %), theo dõi từng phiên là mù cháy ngầm; và khi hứa "đủ tới X giờ" phải hứa trên CẢ các đồng hồ, không chỉ cái đang nhìn.
- **23/8 sáng · B2 DỰ PHÒNG + FAILOVER TỰ ĐỘNG (từ bài học đứng máy 9 tiếng)** — dựng project `mm0-shard-b2` (Firestore nam5, rules+index y hệt B, KHÔNG cần secret mới: cấp datastore.owner cho chính 2 SA của B). Cơ chế 3 tầng: (1) `mirror_b_to_b2` mỗi phiên khi B khỏe — gương kênh/config/snapshot key/gương kho (job history KHÔNG gương — vận hành không cần, đếm lại dần) + DRAIN NGƯỢC job sinh ra lúc chạy tạm B2 về B; (2) `failover_to_b2` — read_keys/read_config dính 429 cạn là lật TOÀN BỘ client B→B2 trong tiến trình (chống đệ quy: chỉ lật lần đầu), phiên sau tự về B; (3) dashboard bắt resource-exhausted → localStorage cờ 6h + reload sang config B2. Env chỉ thêm FIREBASE_PROJECT_ID_B2 (giá trị public, nằm thẳng trong yml). LUẬT: shard dự phòng phải (a) có dữ liệu sống trước khi nhận việc (gương xuôi), (b) trả lại dữ liệu sinh trong lúc khẩn (drain ngược), (c) lật bằng công tắc tự động chứ không đợi người.
- **23/8 trưa · CHỐNG TRÙNG NỘI DUNG + LẬT B2 CHỦ ĐỘNG (user đề xuất, đúng)** — (a) gương B→B2 thêm render_topics (ngân hàng chủ đề đã làm) + rót ngược topics phiên khẩn: thiếu nó thì phiên chạy tạm B2 tưởng "chưa làm gì" -> viết lại đề tài cũ = video trùng nội dung mà dedup vân-tay-file KHÔNG bắt được (file khác byte); (b) quota_pulse(owner) gọi đầu plan VÀ đầu MỖI lane (lane là tiến trình riêng, quyết định plan không tự lan): ≥90% trần ngày -> gương tươi + failover_to_b2 CHỦ ĐỘNG lúc B còn sống = không còn cửa sổ vênh; lật bị động khi 429 chỉ là lưới cuối; (c) failover in "gương tuổi X phút" (mirror_meta). LUẬT: failover chuẩn có 2 tầng — chủ động theo ngưỡng (dữ liệu khớp) + bị động theo lỗi (lưới cuối); và mọi bộ "tránh lặp" (topics/avoid) phải nằm trong tập dữ liệu được gương.
- **23/8 · LỖI TRÌNH TỰ ONBOARDING (user chỉ ra, đau)** — cho kết nối HÀNG LOẠT 70 kho Drive khi OAuth app còn ở Testing (token 7 ngày) thay vì bắt PUBLISH APP trước → toàn bộ 70 token là token "tử tù", giờ mỗi kho phải đồng ý lại 1 lần sau publish (chính sách Google: hạn 7 ngày GẮN VÀO TOKEN lúc cấp, publish không hồi tố). LUẬT: bước cấu hình ảnh hưởng ĐỘ BỀN của credential (publish consent, verify domain, scope) phải là CỔNG CHẶN đứng TRƯỚC mọi onboarding hàng loạt — UI kết nối phải kiểm tra và CHẶN kèm hướng dẫn khi app chưa publish; áp dụng ngay cho khâu kết nối YouTube sắp tới. Kèm luật báo cáo: mô tả fix cho user phải đủ CẢ VẾ (publish = chặn tương lai, KHÔNG cứu token cũ), cấm rút gọn "1 lần là xong" khi còn bước kèm theo.
- **🔴 23/8 · GỐC RỄ THẬT token Drive 7 ngày (user cung cấp bằng chứng lật chẩn đoán)** — app VỐN Ở "In production" (không phải Testing như em đoán 2 lần!); token vẫn rụng vì scope `auth/drive` FULL là loại **RESTRICTED**: production + restricted + chưa verify → Google phát token 7 ngày + mỗi account cấp quyền ăn 1 suất user-cap 100 (đã 84/100 — sắp trần!). Verify restricted = CASA audit nặng, KHÔNG đáng. FIX ĐÚNG: đổi DRIVE_SCOPES sang `drive.file` (non-sensitive) — token vĩnh viễn, không verify, KHÔNG ăn cap; đủ quyền vì hệ chỉ đụng file do chính app tạo (drive.file tính "file của app" theo OAuth client, file cũ upload thời full-scope vẫn thấy). Đã deploy worker + sync scope 2 file python + sửa token-check nhận drive.file. Kho/kênh reconnect từ giờ = token bất tử. CẢNH GIÁC còn lại: YT_SCOPES là loại SENSITIVE → vẫn ăn user-cap (84/100) — kênh YT mới sẽ tốn suất; khi gần 100 phải tách OAuth client sang project mới (worker đã hỗ trợ YT_CLIENTS nhiều client). LUẬT: chẩn đoán hạn token phải soi ĐỦ 3 biến (publishing status × loại scope × verify status), không được dừng ở biến đầu tiên khớp triệu chứng.
- **23/8 trưa · RÀ TRƯỚC PHIÊN 14h: selftest suýt CHẶN CẢ PHIÊN vì trạng thái global rò giữa các test** — t_soft_read giả lập 429 làm failover_to_b2 kích THẬT trong CI (creds B hợp lệ, client init không cần mạng) -> cờ _B2 dính ON -> t_b2 phía sau assert OFF fail -> selftest chặn phiên. Máy local KHÔNG lộ (thiếu creds thật) — chỉ lộ khi giả lập đúng env CI (fake SA đúng định dạng RSA). FIX: t_soft_read pop env B2 trong lúc chạy + finally reset _B2; t_b2 tự dọn cờ đầu test. LUẬT: test đụng cơ chế có TRẠNG THÁI GLOBAL (failover, cache, cờ tiến trình) phải (a) cô lập env kích hoạt, (b) reset trạng thái trong finally; và trước mốc quan trọng phải chạy selftest với ENV GIẢ LẬP CI (đủ biến, creds đúng định dạng), không tin selftest local thiếu env.
- **23/8 · NÂNG CHẤT TOON (user chốt "chất > lượng")** — 3 nấc + siết sản lượng: (1) MẬT ĐỘ ẢNH: khung nào >3.2s bị cắt 2-3 lát, mỗi lát đổi GÓC MÁY (wide/medium/cận/qua vai/low-angle/two-shot) — đo thật 5 khung/69s → 15 khung (~4.6s/khung), trần 16 khung/skit để không nổ neuron CF; (2) RỐI GIẤY: impact-nảy khi đổi câu + bob dọc theo TỪNG TỪ (dùng lại mốc karaoke) + tilt ngược chiều theo nhân vật A/B → cảm giác nhân vật đang diễn thay vì ảnh chết (0 chi phí AI, chỉ Remotion); (3) NHẤN CÂU CHỐT bằng NGÔN NGỮ ĐIỆN ẢNH: zoom giật + rung máy biên độ nhỏ + vignette khép — **đã BỎ đạo cụ emoji bay vào** (user: "đừng làm xấu trông rẻ tiền"; emoji phá tông kênh sepia cổ điển). LUẬT THẨM MỸ: hiệu ứng nhấn phải đến từ máy quay/ánh sáng/nhịp cắt, không dán sticker lên khung hình; (4) round cap kênh toon 10/30 → **2 long/6 short** mỗi phiên. LUẬT: khi tăng độ nặng mỗi video (mật độ ảnh, hiệu ứng) phải HẠ trần sản lượng tương ứng trong cùng commit — không thì lane hết giờ/nổ quota giữa chừng.
- **23/8 chiều · ĐỔI FORMAT 3 KÊNH: skit hài → ESSAY (phân tích lật-ngược-niềm-tin)** — user chấm demo skit BALD&BANDIT dựng tại máy: format đối thoại hài phụ thuộc 100% vào chất lượng câu đùa (AI viết đùa rất khó ăn) + vào giữa video không biết đang xem gì. Tham chiếu kênh triệu view: nội dung PHÂN TÍCH (list 4-6 món lật ngược niềm tin) ăn vì "bất ngờ → share/save", AI làm tốt phần này. Bổ sung mode `essay`: ESSAY_SYS (hook <9 từ, 4-6 mục, mỗi mục 1 số liệu THẬT, ẩn dụ hình ảnh thay minh hoạ suông, chốt bằng takeaway) + `_validate_essay` siết CỨNG: bắt buộc có ít nhất 1 con số + bắt buộc `sources`, 1 giọng kể. Style đổi sang editorial flat illustration (bảng màu giới hạn 3-4 tông/kênh). 3 kênh chuyển: TRUETALES→DEAD WRONG, DUMBHISTORY, EXPLAINUSA. Giữ BALD&BANDIT + HANKTOWN chạy skit làm nhánh thử. KHÔNG thêm băng chữ cố định (user chốt: giữ phụ đề karaoke như cũ). LUẬT: format nào phụ thuộc "AI phải duyên" là format rủi ro — ưu tiên format ăn bằng THÔNG TIN BẤT NGỜ + hình ẩn dụ, thứ AI làm ổn định.
- **23/8 · ĐỒNG BỘ CONFIG THEO cfg_rev (seed chỉ-thêm-nếu-thiếu là bẫy)** — đổi format 5 kênh trong wave8_channels.json nhưng seed cũ chỉ ghi kênh CHƯA CÓ -> Firestore vẫn giữ config cũ -> phiên sau render sai format, mà lúc đó quota đọc đang chết nên không patch tay qua dashboard được. FIX: mỗi entry file có `cfg_rev`; plan so rev với doc, khác thì đẩy toàn bộ field xuống (merge) + cập nhật luôn bản trong RAM để LANE CÙNG PHIÊN dùng ngay. Idempotent (rev giống nhau thì im), không đè chỉnh tay ở field khác. LUẬT: file cấu hình muốn làm nguồn sự thật thì phải có CƠ CHẾ REV — "thêm nếu thiếu" chỉ đúng cho lần khai sinh, không đúng cho vòng đời.
- **🔴 23/8 · SEED ĐẺ 5 DOC KÊNH KHÔNG TÊN (user phát hiện qua số đếm 60 vs 55)** — wave8_channels.json để TÊN Ở KHOÁ dict, seed ghi `{**cfg, owner}` mà quên `name` -> mỗi kênh mới có 2 doc: 1 doc thật (thêm từ dashboard, có name) + 1 doc vô danh (seed). Hậu quả: dashboard đếm sai, plan có thể cấp slot render cho kênh rỗng tên, mọi patch cấu hình chỉ trúng 1 trong 2 bản. FIX: seed ghi kèm `"name": _nm`; plan LỌC BỎ doc không tên trước khi chia slot; đã xoá 5 doc rác (60 → 55). LUẬT: khi nguồn dữ liệu để KHOÁ mang ý nghĩa (tên kênh là key của dict/file), lúc ghi xuống store phải VẬT CHẤT HOÁ khoá đó thành field — và mọi vòng chọn việc phải có guard bỏ bản ghi thiếu định danh.
- **23/8 · heal_unpushed cửa sổ 8h QUÉT TRƯỢT nạn nhân của chính sự cố nó sinh ra để chữa** — video mồ côi sinh lúc 14-17h hôm trước, phiên chữa đầu tiên chạy 07:06Z hôm sau (>14h) -> "quét 0 job". Quota Firestore reset THEO NGÀY nên mọi sự cố cạn quota đều kéo dài xuyên đêm; cửa sổ phải ≥ 24h + biên. FIX: 30h, cap 40. LUẬT: cửa sổ thời gian của cơ chế tự chữa phải LỚN HƠN chu kỳ của loại sự cố nó phục vụ (quota ngày → ≥30h), không được chọn theo cảm tính.
- **23/8 · QC ẢNH 2 ĐẦU cho essay (user yêu cầu "ghép 1 ảnh, kiểm trước và sau render")** — TRƯỚC: đã có verify_grid (ghép lưới, 1 lệnh Vision) nhưng 2 lỗi: (a) chủ đề chấm HARDCODE "hai nhân vật hoạt hình" -> mode essay (tranh ẩn dụ, không nhân vật) bị chấm sai hoàn toàn; (b) khi vẽ lại lấy `spec[k2]` trong khi `fr` đã dài hơn sau bước tăng mật độ -> lệch prompt/IndexError. FIX: chấm theo ĐÚNG PROMPT CỦA TỪNG Ô (khớp nội dung 100%), vẽ lại theo fr[k2], >40% ô trượt thì BỎ BÀI viết lại. SAU: thêm `_qc_after_render` — ffprobe lấy thời lượng, trích 6 khung trải đều (có khung sát cuối để bắt KHUNG ĐEN), ghép lưới, Vision chấm 1 lệnh, <70% đạt thì QC trượt (job failed, tự render lại). LUẬT: QC trước render kiểm NGUYÊN LIỆU, QC sau render kiểm THÀNH PHẨM — thiếu vế sau thì lỗi dựng (khung đen, phụ đề đè, ảnh không nạp) lọt hết ra kho.
- **23/8 · BANNER MỞ ĐẦU + THẺ SỐ LIỆU (user: "text to bự như banner trên footage", "kết hợp chart nếu phù hợp")** — (a) mở đầu: khối tên kênh trên dải màu thương hiệu + tiêu đề CHỮ HOA cỡ 92 trên nền ảnh phủ tối, bung ra rồi tan sau ~2.8s (long chớp lại ở mỗi chương) = cú hook thị giác 2 giây đầu; (b) THẺ SỐ LIỆU động: python rút con số THẬT trong lời kể (ưu tiên số có $/%/đơn vị/dấu phân cách hơn NĂM trơn — "177,000" thắng "2020"), tối đa 3 thẻ/video, chỉ mode essay; engine bung số cỡ 76 + thanh chỉ báo chạy, đặt góc trên phải để không đè phụ đề; câu không có số thì KHÔNG hiện. LUẬT: hiệu ứng dữ liệu chỉ được xuất hiện khi CÓ dữ liệu thật trong câu đang đọc — nhồi chart trang trí là phản tác dụng.
- **23/8 · 6 NÂNG CẤP CHUẨN NHÀ NGHỀ cho essay (user: "nâng tất cả")** — (1) THUMBNAIL: doc_thumb giờ nhận comp_id+props_path của chính video toon -> render THẲNG khung banner mở đầu từ composition (chữ sắc, đúng khoảnh khắc hook) thay vì trích từ video đã nén; (2) ÂM LƯỢNG: `_normalize_loudness` ffmpeg loudnorm I=-14 TP=-1.5 chạy TRƯỚC qc (qc phải đo đúng file sẽ đăng) — nền tảng tự kéo về -14 LUFS nên video không chuẩn nghe mỏng hơn đối thủ; (3) NHẠC NỀN CC-BY chọn theo kênh (_TOON_MUSIC) + set story["_music"] để enqueue ghi công đúng license; (4) LỀ AN TOÀN: phụ đề short 9:16 nâng lên 330px (UI TikTok/Reels che đáy), long 16:9 giữ 150px; (5) NHỊP THỞ 0.4s trước câu chốt; (6) KẾT BÀI 2.2s mời theo dõi + tên kênh, kèm nới end_f (+66 frame) — thiếu bước nới là outro bị cắt cụt. LUẬT: mọi phần tử mới CHIẾM THỜI LƯỢNG (outro, intro, pause) phải cộng vào end_f trong cùng commit, nếu không engine cắt mất.
- **23/8 · VÂN TAY MỸ cho toàn bộ khung hình essay (user: "bối cảnh, nhân vật, minh hoạ đều phải chuẩn USA")** — trước đó hình ẩn dụ trung tính, nhìn không biết là kênh Mỹ. Siết 2 tầng: ESSAY_SYS thêm mục 3b (bối cảnh Mỹ nhận ra ngay + đạo cụ đời thường Mỹ + người Mỹ đa sắc tộc mặc đồ đời thường) và tầng VẼ có `_usa_style` ghép tag vào style-lock (áp cả ảnh vẽ lại/fallback, idempotent). ĐO BẰNG ẢNH THẬT 2 vòng: vòng 1 vân tay vào được nhưng cảnh RỐI -> FLUX đẻ CHỮ GIẢ ("Coffe Ferricus") + LOGO NHÁI (rủi ro bản quyền); vòng 2 siết "1 đạo cụ (tối đa 2), nền tối giản 3-5 phần tử, cấm kệ hàng/biển hiệu/logo/nhãn" -> sạch chữ, sạch logo, vẫn đọc ra nước Mỹ; vòng 3 thêm "đặt tự nhiên đúng chỗ, không nhét gượng". LUẬT: mỗi lần nới yêu cầu NỘI DUNG cho ảnh AI phải siết ĐỘ PHỨC TẠP tương ứng — cảnh càng đông chi tiết thì model càng đẻ chữ giả/logo; và luôn nghiệm thu bằng ảnh thật, không tin prompt.
- **🔴 23/8 · ĐỔI SCOPE OAUTH ĐỒNG LOẠT = GIẾT SẠCH 70 KHO NGAY LẬP TỨC** — sáng đổi DRIVE_SCOPES `drive` → `drive.file` (đúng về lý thuyết: non-sensitive, token vĩnh viễn) NHƯNG refresh_token đang lưu của 70 kho được cấp theo scope CŨ; Google trả `invalid_scope` cho mọi lần refresh -> `_free_cached` rơi vào nhánh "không đọc được dung lượng" -> im lặng bỏ qua từng kho -> `ranked_accounts` rỗng -> mọi lane báo "❌ Không tài khoản kho nào đủ chỗ (~0.09 GB)" trong khi kho còn 1TB. Video vẫn render nhưng KHÔNG đẩy được kho suốt ~2 tiếng. FIX: rollback scope về `drive` ở worker + auth_setup + drive_client, deploy worker ngay; thêm nhánh nhận diện `invalid_scope` HÉT TO ("SCOPE SAI — mọi kho sẽ chết") thay vì im lặng. LUẬT: scope OAuth là HỢP ĐỒNG GẮN VỚI TỪNG TOKEN — chỉ được đổi CÙNG LÚC với reconnect từng tài khoản (kho mới dùng scope mới), TUYỆT ĐỐI không đổi đồng loạt trong code; và mọi lỗi ở khâu chọn kho phải phân biệt "kho hỏng" với "cấu hình mình sai".
- **🔴 23/8 · 125K ĐỌC/NGÀY TRÊN A — thủ phạm: danh sách 70 kho Drive quét cả collection** — `firestore_pool_accounts` quét CẢ 70 doc `connections`, đệm chỉ 10'; mỗi lane sống 110' -> làm mới ~11 lần = 770 đọc/lane, ×18 lane = **~14.000 đọc/phiên**, ×4-5 phiên/ngày = vượt xa trần 50K của A (đo thật: A 125K, B 51K). Cùng lớp lỗi với 142 key AI hồi 22/8 nhưng ở collection khác nên lọt. FIX: plan gói cả danh sách kho vào **1 doc snapshot** `connections_mirror/__snap__` (ở B, service-account-only); publisher đọc snapshot TRƯỚC (1 lượt, lại không đụng A), chỉ khi thiếu mới quét collection; POOL_TTL 10' → 30'. Ước còn ~200 đọc/phiên (giảm ~98%). LUẬT: bất kỳ danh sách >20 doc bị đọc trong VÒNG ĐỜI LANE (không phải 1 lần/phiên) đều phải gói snapshot 1-doc — đọc-cả-collection chỉ được phép ở plan, không được ở đường nóng của lane.
- **🔴 23/8 · DASHBOARD LÀ NGUỒN ĐỐT QUOTA LỚN NHẤT (không phải render)** — đo thật: mỗi lần TẢI TRANG ≈ 700 lượt đọc (200 videos + 300 render_jobs A/B + 60 kênh + 142 key + settings/connections), và listener realtime để mở còn ăn THÊM 1 lượt cho MỖI cập nhật job — 18 lane đang chạy ghi liên tục nên 1 tab mở trong 1 phiên = hàng nghìn lượt. Ngày 23/8 chính việc AI mở/tải lại dashboard hàng chục lần để soi lỗi đã góp phần đẩy A lên 125K / B lên 51K. FIX 3 lớp: (a) bọc mọi onSnapshot bằng `snapW` — nhớ hàm huỷ + đếm lượt; (b) tab ẩn quá 90s TỰ NGẮT toàn bộ listener (quay lại thì nạp mới) -> để tab mở không còn tốn gì; (c) hạ trần: render_jobs A 100→40, B 200→80, videos 200→80 (≈700 → ≈260 lượt/lần tải); (d) đồng hồ "📖 N lượt đọc phiên này" hiện góc màn hình để chi phí LUÔN NHÌN THẤY. LUẬT VẬN HÀNH: đi soi lỗi thì đọc LOG GITHUB (0 quota), không mở dashboard; dashboard chỉ để xem kết quả, không phải công cụ debug.
- **23/8 · FAILOVER B2 KHÔNG KHỚP 100% — 2 lỗ đã bịt/đã biết** — (a) ĐÃ BỊT: `count_done` đếm job trong kho, mà B2 CỐ Ý không chép lịch sử job -> lật sang B2 sẽ thấy ~0 -> tưởng kênh chưa làm gì -> LÀM DƯ video so với chỉ tiêu. Fix: khi `_B2["on"]`, count_done = số trong SỔ THỐNG KÊ `render_stats/{owner}` (đã thêm vào danh sách gương) + số job làm trong chính phiên khẩn; (b) CÒN LẠI (chấp nhận): ngân hàng chủ đề `render_topics` chỉ tươi tới lần gương gần nhất (≤1 phiên) -> ở chế độ lật BỊ ĐỘNG có rủi ro nhỏ trùng đề tài; lật CHỦ ĐỘNG (≥90%) thì gương chạy ngay trước khi lật nên khớp 100%. LUẬT: mọi con số dùng để RA QUYẾT ĐỊNH SẢN XUẤT (đếm đã làm, chỉ tiêu, chống trùng) phải có nguồn thay thế khi failover — nếu không, hệ dự phòng sẽ đẻ ra sai lệch tệ hơn cả sự cố gốc.
- **🔴 23/8 · FAILOVER PHẢI KHỚP TUYỆT ĐỐI Ở DỮ LIỆU GÂY HẬU QUẢ (user ép, đúng)** — "trễ 1 phiên" nghe vô hại nhưng với NGÂN HÀNG CHỦ ĐỀ thì hậu quả THẬT: AI viết trùng đề tài -> video vứt đi, tốn cả lượt vẽ FLUX lẫn giờ render. FIX 2 chiều: (a) `save_topics` GHI SONG SONG sang B2 ngay tại chỗ (không đợi nhịp gương) — mỗi video thêm đúng 1 lượt ghi vào kho B2 riêng, không đụng quota B; (b) lúc rót ngược B2→B thì GỘP hai danh sách (khử trùng, giữ 300 gần nhất) thay vì đè một chiều — đè sẽ xoá mất nửa ngân hàng chống trùng và vài ngày sau lặp lại đề tài cũ. LUẬT: phân loại dữ liệu theo HẬU QUẢ KHI LỆCH — loại "lệch là hỏng sản phẩm" (chống trùng, đếm chỉ tiêu) phải ghi song song/đồng bộ tức thì; loại "lệch chỉ hơi cũ" (cấu hình, thống kê) mới được đi theo nhịp gương.
- **23/8 · DIỄN TẬP THAY VÌ CHỜ SỰ CỐ (user: "đừng chạy xong mới ớ ra")** — thêm `t_failover_rehearsal` vào selftest: dựng client GIẢ (0 mạng/0 quota) mô phỏng B CHẾT GIỮA PHIÊN rồi kiểm 4 đường gây hỏng sản phẩm — chủ đề ghi song song B+B2, phiên khẩn không làm mất đề tài cũ, `count_done` ở B2 = sổ thống kê + job khẩn (nếu về 0 là LÀM DƯ video), rót ngược GỘP hai phía. Chạy đầu MỖI phiên nên bất kỳ ai (kể cả AI) đụng vào đường failover mà làm sai là plan fail trong 30 giây, lane không spawn. LUẬT: cơ chế chỉ chạy KHI CÓ SỰ CỐ thì phải có DIỄN TẬP TỰ ĐỘNG — không được để lần chạy thật đầu tiên chính là lần kiểm thử đầu tiên.
- **23/8 · SỐ KHÔNG KHỚP (user: "tổng 1755 mà kho 61")** — 2 ô đo 2 thứ khác nhau: "Tổng cộng dồn" đếm BẢN GHI JOB `status=done` (gộp cả video render lại + video CHƯA đẩy được kho), còn thư viện chỉ hiện video CÓ `drive_id`. Không bao giờ khớp được vì định nghĩa khác nhau. FIX kiến trúc: **sổ đếm 1-doc `render_stats/__pushed__{owner}`** — `enqueue_drive` (chỗ DUY NHẤT mọi đường đẩy kho đi qua) cộng 1 khi có `drive_id` thật, kèm field theo ngày + theo kênh, chống đếm trùng bằng danh sách 400 drive_id gần nhất trong RAM. Dashboard đọc 1 doc cho cả "Tổng" và "Hôm nay" -> khớp tuyệt đối với thư viện, lại rẻ hơn 2 lượt aggregation count(). LUẬT: một con số hiển thị cho user phải có ĐỊNH NGHĨA DUY NHẤT và được ghi tại ĐÚNG KHOẢNH KHẮC sự kiện xảy ra (lúc đẩy kho thành công), không được suy ra bằng cách đếm lại bản ghi trung gian.
- **🔴 23/8 · TRÙNG FOOTAGE TOÀN HỆ + PHỤ ĐỀ GIẬT (user phát hiện qua video thật)** — (1) TRÙNG ẢNH: `fetch_image` luôn xin TRANG 1, lấy theo thứ tự trả về, KHÔNG nhớ ảnh đã dùng, lại lọc chặt `license=cc0,pdm` (kho nhỏ) -> mọi video/mọi kênh cùng từ khoá nhận ĐÚNG vài tấm đầu. FIX 3 lớp: trang ngẫu nhiên 1-4 (kho ×4) + xáo kết quả + sổ nhớ `_IMG_USED` trong RAM (0 quota Firestore) bỏ ảnh đã tải; thêm QC `qc_structure` chặn khi <50% ảnh khác nhau hoặc 1 ảnh lặp quá 1/3 số cảnh. (2) PHỤ ĐỀ GIẬT: edge-tts mặc định chỉ trả `SentenceBoundary` (1 mốc/câu) nên hệ CHIA ĐỀU thời lượng theo số ký tự -> từ dài/ngắn lệch nhịp. FIX: `Communicate(..., boundary="WordBoundary")` -> mốc THẬT từng từ (đo: 13 từ, hở 0.01s), `_expand_words` nhận diện mốc-từng-từ thì dùng thẳng, chỉ fallback ước lượng khi máy đọc không hỗ trợ. LUẬT: dữ liệu THỜI GIAN và dữ liệu NGUỒN ẢNH phải lấy từ nguồn CHÍNH XÁC nếu nguồn đó tồn tại — ước lượng chỉ là phương án cuối, và mọi thứ "chọn từ danh sách" phải có bộ nhớ chống lặp.
- **23/8 · MỞ RỘNG KHO ẢNH ×5 (gốc của trùng footage)** — kho cũ hẹp vì chỉ Openverse + lọc `cc0,pdm` + luôn trang 1 = ~12 ảnh/từ khoá cho TOÀN HỆ. FIX: (a) thêm **Wikimedia Commons** làm nguồn thứ 2 (~100 triệu file, không cần key, loại bỏ giấy phép ShareAlike để tránh ràng buộc video); (b) mở license Openverse sang `cc0,pdm,by` + tự thêm dòng ghi công "Imagery: Openverse & Wikimedia Commons (CC0/PD/CC BY)" vào mô tả (đúng luật attribution); (c) trang ngẫu nhiên 1-4. ĐO THẬT: "college tuition" 12 → 60 ảnh, "american suburban house" 12 → 60 (×5). Kèm sổ nhớ RAM chống lặp + QC chặn video có <50% ảnh khác nhau. LUẬT: khi phát hiện "trùng lặp nội dung", phải đo ĐỘ RỘNG KHO NGUỒN trước — thường gốc là kho hẹp chứ không phải thuật toán chọn.
- **23/8 · KHO ẢNH 3 NGUỒN (nối tiếp bản ×5)** — thêm **NASA Image Library** (~140k ảnh, PUBLIC DOMAIN toàn bộ, không cần key) bên cạnh Openverse + Wikimedia Commons; đặc biệt mạnh cho COSMOS/FUTUREUSA/DISASTERUSA (vũ trụ, khí hậu, khoa học, thiên tai) và luôn là ảnh THẬT chất lượng cao. Đã khảo sát và LOẠI: Library of Congress (API trả 403 với user-agent thường), Met Museum (chỉ hiện vật bảo tàng, hợp kênh sử/nghệ thuật — để dành), Pexels/Unsplash/Smithsonian (cần key, chưa có trong secrets). LUẬT: mỗi nguồn mới phải KIỂM BẰNG GỌI THẬT trước khi cắm (LoC trông hứa hẹn nhưng 403), và phải trả cùng cấu trúc {id,url} để mọi lớp lọc/chống-lặp phía sau dùng chung.
- **23/8 · CHỐNG TRÙNG ẢNH — LỚP CUỐI: MUỐI PROMPT** (user: "vẫn sợ trùng") — mọi ảnh AI vẽ ra đều được thêm 1 biến thể GÓC MÁY/ÁNH SÁNG ngẫu nhiên (`_salt_prompt`, 8 biến thể) trước khi gửi FLUX: cùng chủ đề vẫn ra khung khác nhau kể cả khi máy chủ dùng seed cố định, và vì mỗi khung được VẼ MỚI nên không bốc từ kho chung nào -> không thể trùng theo cấu trúc. Xếp tầng chống trùng hiện có: (1) kho stock ×5 + 3 nguồn; (2) trang ngẫu nhiên + xáo thứ tự; (3) sổ nhớ ảnh đã dùng (RAM, 0 quota); (4) muối prompt cho ảnh AI; (5) QC chặn video <50% ảnh khác nhau. LUẬT: chống trùng phải xếp NHIỀU TẦNG rẻ tiền, không dựa vào một cơ chế duy nhất.
- **23/8 · NGUỒN ẢNH THỨ 4: PEXELS (user tự lấy key)** — kho ảnh HIỆN ĐẠI đẹp nhất nhóm free (người thật, đời sống Mỹ), key lưu ở GitHub secret `PEXELS_KEY` (KHÔNG in ra log/chat, lấy bằng clipboard → `gh secret set`). TÔN TRỌNG ĐIỀU KHOẢN: tự hạn chế 120 lượt/tiến trình (nhà cung cấp cho 200/giờ, 20k/tháng), chạm 429/403 là TẮT hẳn phiên đó nhường nguồn khác, dùng đúng mục đích minh hoạ video của mình (không dựng lại dịch vụ giống Pexels), có ghi công trong mô tả. LUẬT: mọi nguồn có key phải có VAN TỰ HẠN CHẾ trong code — không dựa vào việc "chắc không dùng hết".
- **23/8 · QUẢN LÝ NHIỀU KEY PEXELS (user: "thêm chục key xoay vòng")** — dùng CHUNG hệ quản lý key sẵn có thay vì dựng UI mới: key lưu dạng `px:<KEY>`, dashboard tự nhận diện (chuỗi 48-64 ký tự chữ+số, không phải gsk_/AIza/AQ./cf:), có nút "🖼️ Lấy key Pexels", chip lọc, health-check riêng (gọi /v1/search per_page=1), ước lượng "N key ≈ N×20.000 lượt/tháng". Pipeline: `set_pexels_pool` nạp từ cùng danh sách key, XOAY điểm bắt đầu theo kênh (18 luồng không đốt chung 1 key), mỗi key trần 150 lượt/tiến trình, gặp **401/403/429 là tắt riêng key đó** rồi nhảy key kế (đo thật: key sai trả 401 — bản đầu chỉ bắt 429/403 nên key hỏng nằm lại pool). LUẬT: thêm nhà cung cấp mới thì CẮM VÀO hệ key sẵn có (thêm/xoá/kiểm tra/xoay vòng dùng lại 100%), đừng dựng luồng quản lý riêng.
- **23/8 · NÚT "THÊM KEY" CHẾT LẶNG khi thêm nhận diện Pexels** — viết `v = "px:" + v` trong khi `v` khai báo bằng `const` -> trình duyệt ném TypeError, cả hàm thêm key ngừng chạy, bấm nút KHÔNG có phản hồi gì (không lỗi hiện ra). FIX: không đụng vào `v`, chỉ đặt cờ `isPx` rồi dựng `kv` (và cho `isPx` chặn sớm nhánh tự-dò-Account-ID của Cloudflare — nếu không key Pexels bị đem đi hỏi CF). Nghiệm thu bằng thao tác THẬT trên trình duyệt: thêm key → doc vào Firestore với provider "pexels", chip lọc "🖼️ Pexels 1", dòng quota "≈20.000 lượt/tháng", health-check ping /v1/search trả 200. LUẬT: mọi thay đổi trong hàm xử lý form phải bấm thử NÚT THẬT — lỗi gán hằng không hiện ở node --check (cú pháp vẫn hợp lệ), chỉ lộ khi chạy.
- **23/8 · DỌN KHO LÀM LẠI TỪ ĐẦU (user chốt sau khi xem video thật)** — ~1.399 video + thumbnail của pipeline CŨ (ảnh trùng, sub chưa khớp, âm chưa chuẩn) được chuyển vào THÙNG RÁC Drive (hoàn tác được 30 ngày; bước "đổ thùng rác" xoá vĩnh viễn để USER tự bấm — AI không xoá vĩnh viễn dữ liệu). Quy trình an toàn: chỉ đụng đúng `MM0-STORE/_QUEUE/{long,short}` của từng kho, KHÔNG chạm thư mục riêng của user trong cùng Drive (kho ADISONDURHAM có "Kling ai model", "MM0 YOUTUBE 2026"… nằm cạnh); duyệt cây thư mục rồi mới trash từng file, chạy NGẦM có sổ tiến độ. Kèm: tắt `heal_unpushed` (bỏ 180 video kẹt — cũng là hàng pipeline cũ), reset sổ đếm video-đã-lên-kho về 0. LUẫT: thao tác hàng loạt trên kho của user phải (a) khoanh vùng theo thư mục CỦA HỆ, (b) dùng bước hoàn tác được, (c) để bước không-hoàn-tác cho user bấm.
- **23/8 · NGUỒN ẢNH THỨ 5: PIXABAY** — ~4 triệu ảnh, giấy phép riêng cho phép dùng thương mại và KHÔNG cần ghi công, hạn mức rộng nhất nhóm (5.000 lượt/GIỜ/key). Cắm y hệt Pexels: key dạng `pb:<KEY>` trong cùng hệ quản lý key (dashboard tự nhận diện theo mẫu "<số 6-10>-<chuỗi 20-40>", có nút lấy key + chip lọc + health-check), pool xoay theo kênh, trần 400 lượt/key/tiến trình, key hỏng (400/401/403/429) tắt riêng rồi nhảy key kế. THỨ TỰ LẤY ẢNH hiện tại: Pexels → Pixabay → Wikimedia → NASA → Openverse (gộp rồi XÁO + bỏ ảnh đã dùng) → AI vẽ (FLUX, có muối prompt) khi không tìm được ảnh thật. LUẬT: nguồn nào hạn mức rộng + giấy phép thoáng thì để gần đầu, nguồn cần ghi công/hẹp để sau.
- **23/8 · GHI CÔNG ẢNH THEO ĐÚNG LUẬT TỪNG NGUỒN (user hỏi "có phải credit Pexels/Pixabay không")** — trả lời: **CC-BY (Openverse, một phần Wikimedia) BẮT BUỘC** ghi tác giả + giấy phép; **Pexels/Pixabay/NASA/Public Domain KHÔNG bắt buộc** nhưng nên ghi (minh bạch nguồn khi YouTube xét kiếm tiền). Bản trước chỉ dán 1 câu chung "Openverse & Wikimedia" -> vừa THIẾU (không nêu tác giả CC-BY) vừa SAI (kể tên nguồn không dùng). FIX: sổ `_IMG_CREDITS` ghi lại nguồn·tác giả·giấy phép của CHÍNH ảnh đã tải (Pexels trả photographer, Pixabay trả user, Openverse/Wikimedia trả creator+license), `take_credits()` gắn vào story, mô tả in tối đa 8 dòng thật; không có sổ mới lùi về câu chung. LUẬT: ghi công phải theo TÀI SẢN THẬT SỰ DÙNG, không phải câu bao đồng — sai cả hai chiều đều là rủi ro pháp lý/uy tín.

### BUG 23/8 — "Pixabay vẫn lỗi" (2 lỗi chồng nhau)
1. **Deploy bắn nhầm project**: alias Firebase đang là `c` (mm0-shard-c) nên `firebase deploy --only hosting`
   đẩy bản sửa lên `mm0-shard-c.web.app`, còn dashboard thật `mm0-auto-publisher.web.app` vẫn bản cũ.
   → **LUẬT**: mọi deploy dashboard PHẢI có `-P a`, và phải kiểm chứng bằng cách đọc mã trên trang thật
   (vd `String(window.__autoAddKeyFromUrl).includes('@auto')`), không tin dòng "Deploy complete".
2. **Thêm key im lặng**: `__rsAddKey` bắt buộc có Gmail, nhưng `pixabay.com/api/docs/` KHÔNG hiện email nào
   → bookmarklet gửi `addkey` không kèm `kmail` → hàm `return alert(...)` chặn, người dùng chỉ thấy "vẫn lỗi".
   → Fix: thiếu Gmail thì tự đặt nhãn `pixabay-<4 số cuối>@auto` / `pexels-<4 số cuối>@auto`.
   → **LUẬT**: luồng tự động không được phụ thuộc trường mà trang nguồn có thể không có; luôn có nhãn dự phòng.
3. Kiểm chứng bằng key GIẢ (`19999999-test...`) rồi xoá, không dùng key thật để thử.
4. **Dán nửa key**: bấm 2 lần vào key Pixabay chỉ bôi được phần sau dấu gạch (`9860cae...`) → không khớp mẫu
   `\d{6,10}-...` → rơi nhầm vào nhánh Cloudflare, nút "Thêm key" như chết. Fix: chặn sớm + báo rõ thiếu 8 số đầu.
   Thêm nút **📋 Dán key từ clipboard** (đọc clipboard, tự nhận nhà cung cấp, tự đặt nhãn) — bỏ được bookmarklet.
5. **Trang cũ do cache**: deploy xong mà trang vẫn bản cũ (`typeof window.__rsPasteKey === 'undefined'`) dù tệp
   trên máy chủ đã mới (fetch kèm `?cb=` thấy mã mới). → Đã thêm header no-cache cho `**` trong firebase.json.
   → **LUẬT kiểm chứng deploy**: so mã TRÊN MÁY CHỦ (`fetch('/index.html?cb='+Math.random())`) với mã ĐANG CHẠY
   (`typeof window.__ham`), khác nhau thì tải lại kèm `?v=...`, đừng kết luận "đã lên" khi chỉ thấy Deploy complete.

### BUG 23/8 — 429 bị nuốt ở count_done nên KHÔNG lật B2
Phiên 13:29Z in 108 dòng `⚠️ đếm <kênh>/<loại> lỗi (429 Quota exceeded.)` mà không có dòng `🔀 FAILOVER`.
Vì `count_done` bắt Exception rồi chỉ in cảnh báo → cả phiên tiếp tục chạy trên B đã cạn đọc: đếm = 0
(lập kế hoạch sai) và mọi lượt đọc sau đều hụt. Fix: 429 tại đây gọi `failover_to_b2()` rồi đếm lại.
→ **LUẬT**: mọi chỗ bắt lỗi Firestore phải phân biệt "lỗi thường" và "429 = shard chết". 429 luôn phải
kích failover, không được chỉ in cảnh báo rồi đi tiếp.

### LUẬT 23/8 — "không đẩy được thì đừng render"
Render 18 luồng rồi bị từ chối đẩy kho = mất trắng phút GitHub + công AI (đúng vết 180 video sáng 23/8).
Nay `--gate` kiểm `storage.pool_accounts()` trước khi mở phiên: rỗng thật -> `run=false` + in lý do;
lỗi mạng -> vẫn chạy (fail-open, vì storage.py có đệm + B2 + thử lại 8s/25s).
`firestore_pool_accounts` cũng đọc theo thứ tự B -> B2 -> A thay vì B -> A (chiều 23/8 B cạn quota đọc
nên nhánh cũ rơi thẳng xuống A đã chết).

### BUG 23/8 — key ảnh/bến R2 lọt vào HỒ KEY VIẾT
`key_order()` định nghĩa `gem = mọi key không phải gsk_/cf:` nên key Pexels (`px:`), Pixabay (`pb:`)
và bến R2 (`r2:`) bị đem đi gọi API viết chữ: mỗi lượt 1 lần lỗi + bị đánh dấu nghỉ oan. Sắp thêm 10
key R2 nên mức pha loãng còn nặng hơn. Fix: lọc `px:/pb:/r2:` ngay đầu `key_order`, có test trong selftest.
→ **LUẬT**: mỗi khi thêm LOẠI key mới vào hồ chung, phải lọc nó ra khỏi các hồ không dùng nó
(viết / vẽ / vision / ảnh thật / lưu trữ) và thêm 1 test chặn hồi quy.

### BUG 23/8 — video 13 giây CÂM vẫn được chấm QC 100
Ba short CLOCKWORKUSA ra lò 0:13 · 1.8MB · giống hệt nhau. Gốc: `TK.synth()` khi edge-tts trục trặc
trả `dur=0.0` LẶNG LẼ -> timeline cộng 0 -> video chỉ còn khung tĩnh, không lời. `qc()` lúc đó chỉ hỏi
"dur>=5 và CÓ luồng audio" — luồng audio câm vẫn tính là có -> đạt 100 -> đẩy thẳng lên kho.
Fix 2 tầng: (1) synth thử lại 3 lần rồi NÉM LỖI thay vì trả 0; (2) qc() thêm ĐỘ DÀI TỐI THIỂU theo khổ
hình (dọc ≥20s, ngang ≥45s) và ĐO MỨC ÂM bằng volumedetect, ≤ -45dB coi là câm -> trượt QC.
→ **LUẬT**: QC phải đo THỨ NGƯỜI XEM NGHE/THẤY, không chỉ đo "file có tồn tại luồng đó không".
Hàm sinh dữ liệu nền tảng (TTS/ảnh) không được phép trả giá trị rỗng trong im lặng.

### BUG 23/8 — video CLOCKWORK cắt cụt lời (13.2s trong khi giọng 27s)
Sáng nay chẩn đoán nhầm là "video câm". Đo lại kịch bản: CLOCKWORKUSA có 6 đoạn VO / 69 từ ≈ 27 giây
lời, mà video chỉ 13.2s. Gốc: `calcClockwork` trong engine tính độ dài bằng HẰNG SỐ CỨNG
(1.5 + 1.8×số mốc + 3 + 1.5) và **bỏ qua hoàn toàn** thời lượng giọng mà Python đã đo. Fix: Python gửi
kèm `introSec/heroSec/outroSec/totalSec`, engine lấy `totalSec` làm chuẩn, hằng số chỉ còn là dự phòng.
→ **LUẬT**: độ dài video PHẢI tính từ độ dài giọng đọc thật, không bao giờ từ hằng số phỏng đoán.
Mọi composition có audio phải nhận thời lượng qua props, không tự bịa.
(Ghi chú: PULSEUSA/SWARMUSA ngắn 15-17s là do kịch bản chỉ có VO cho intro+outro, phần thân không có
lời — đó là giới hạn THIẾT KẾ của format, không phải lỗi; muốn dài hơn phải thêm VO cho từng item.)

### 23/8 chiều — GỠ BẾN PHỤ R2 khỏi luồng sản xuất
User chốt bỏ ("hơi rối, tránh xung đột lỗi"). Đã ngắt: `_r2_park()` trong `enqueue_drive`, `repush_r2()`
và khối báo dung lượng trong plan, boto3 khỏi workflow, toàn bộ giao diện R2 khỏi dashboard.
GIỮ NGUYÊN (ngủ, không ai gọi): `r2_store.py`, 3 hàm sổ `*_r2_pending` trong firestore_bridge,
endpoint `/api/r2-setup` ở worker. Bật lại = khôi phục 2 chỗ gọi trong run_render.
Lưới an toàn còn 2 lớp và đủ dùng: `heal_unpushed` đẩy lại video hụt kho ở phiên sau + artifact GitHub.
Bài học: 49/49 token Cloudflare cũ (chỉ có quyền Workers AI) KHÔNG tạo được R2 — muốn R2 phải tạo
token riêng 3 quyền cho từng tài khoản, chi phí thao tác lớn hơn giá trị mang lại khi Drive đang khoẻ.

### 23/8 chiều — CHỐNG TRÙNG ẢNH XUYÊN LUỒNG & XUYÊN PHIÊN
Bản sáng nay chỉ có `_IMG_USED` trong RAM MỘT tiến trình. 18 luồng = 18 tiến trình, mỗi phiên lại khởi
động mới -> hai video khác luồng/khác phiên vẫn rút trúng cùng tấm ảnh (đúng thứ user thấy: "nhiều
kênh dùng cùng 1 footage"). Nay có sổ Firestore `img_used/{owner}__{channel}` giữ 600 id gần nhất:
`load_used_images()` móc trong `set_ai_pool` (cửa duy nhất mọi make_* đi qua), `save_used_images()`
móc trong `qc()` (chạy đúng 1 lần sau render). Chi phí ~110 lượt đọc-ghi/phiên cho 55 kênh.
→ **LUẬT**: mọi cơ chế "đã dùng rồi thì đừng dùng lại" phải sống ngoài RAM tiến trình, nếu không nó
chỉ đúng trong đúng một luồng.

### 23/8 — CHART ĐỘNG mặc định cho nhóm kể chuyện (toon/essay)
Người viết trả thêm khối `chart {label, unit, items[2-5]{name, value}}` khi bài có số so sánh được
(null nếu không có — KHÔNG bịa). `_chart_props()` chốt lại: chỉ nhận 2-5 mục, value > 0, rồi đặt vào
GIỮA video (mốc câu giữa) trong 4.5 giây. Engine ToonShort dựng cột chạy từ 0 + số đếm lên, nền tối mờ.
→ **LUẬT**: mọi hiệu ứng dựa trên dữ liệu phải có đường "không đủ dữ liệu thì tắt", không bao giờ
dựng chart từ số tự chế.

### BUG 23/8 — PHỤ ĐỀ ĐÈ LÊN THẺ SỐ LIỆU (ảnh user gửi)
Thẻ chữ giữa màn trong Cinematic dùng `inset: 0` nên tâm của nó rơi TRÚNG dải phụ đề (bottom 520 ở
khổ dọc) -> chữ chồng chữ, không đọc được. Fix: thẻ chữ chỉ được dùng vùng trên (`bottom: capZone`
= 560px dọc / 170px ngang), HUD số liệu nâng lên top 300, phụ đề thêm zIndex 30 + bóng đậm.
→ **LUẬT BỐ CỤC**: mỗi lớp chữ phải có VÙNG RIÊNG khai báo rõ; không lớp nào được `inset: 0` khi
màn hình còn lớp chữ khác. Thêm lớp chữ mới = phải khai vùng của nó trước.

### 23/8 — CỔNG CHẤT LƯỢNG CHUNG (quality_gate.py) cho kênh hàng nghìn video
Bọc ngoài toàn bộ 14 hàm write_* (một lớp áo, không sửa 12 hàm sinh):
1. Mạch kênh: đếm "trụ nội dung", ép người viết chọn trụ ít tập nhất -> kênh có series thay vì bài rời.
2. Chống trùng theo Ý: dấu vân từ khoá của (tiêu đề + hook + 2 câu đầu), so bằng OVERLAP (không phải
   Jaccard — Jaccard bỏ lọt khi 2 tiêu đề dài ngắn khác nhau), ngưỡng 0.5, nhớ 4000 bài/kênh trong 1 doc.
   Trùng -> viết lại ĐÚNG 1 lần (không lặp vô hạn, không đốt key).
3. Chuẩn kiếm tiền: ≥2 nguồn, phải có số liệu, chặn cụm từ rủi ro chính sách.
Đo thật: "Rent 2025 vs 2015…" ~ "How US rent doubled since 2015…" = 0.62 (bắt được), so với bài NASA = 0.0.

### BUG 23/8 — KHUNG ĐEN CUỐI VIDEO (quét tĩnh toàn engine, 0 quota)
Quét 11 composition đang dùng: chỉ `ThenNowShort` có gốc `<AbsoluteFill>` KHÔNG nền — hai panel chạy
theo animation, hết nội dung là lộ nền trong suốt và Remotion xuất ra ĐEN. Các engine còn lại
(Cinematic/Clockwork/Pulse/Swarm/Longshot/Guess/Toon/StickStory/RaceLong) đều có nền full-bleed nên
không dính. Fix: thêm nền thương hiệu cho ThenNowShort.
→ **LUẬT**: gốc mọi composition PHẢI có nền đục. Không bao giờ để `<AbsoluteFill>` trần làm lớp dưới cùng.

### 23/8 — ÂM CHUYỂN CẢNH hết đơn điệu
Trước: mọi cú cắt đều phát đúng 1 file `whoosh.mp3` cùng âm lượng -> nghe lặp như máy. Nay xoay vòng
4 mẫu (whoosh/pop/whoosh/impact) + đổi playbackRate (1.0 / 1.16 / 0.88 / 0.95) + đổi âm lượng theo thứ
tự cắt. Cùng một file phát ở 0.88 và 1.16 nghe như hai tiếng khác nhau -> 0 file mới, 0 quota.

### BUG 23/8 tối — PHIÊN TREO 42 PHÚT Ở BƯỚC ĐIỀU PHỐI (dây chuyền đứng)
Phiên 15:38Z đứng 42' ở `--plan`. Chuỗi nhân quả: quota đọc cạn -> mỗi lệnh đếm chờ hết 60s timeout
mặc định -> `_retry` thử lại 5 lần (+15s) -> nhân ~110 lệnh đếm cho 55 kênh = hàng giờ. Tệ hơn: phiên
treo giữ khoá `concurrency` nên GitHub HUỶ mọi phiên xếp sau (15:54, 16:14) -> dây chuyền đứng hẳn.
Fix 3 lớp: (1) cầu dao `_RQ_DEAD` chặn ngay đầu `_count_jobs` — biết đường đọc chết thì trả 0 tức thì;
(2) `timeout=12` cho aggregation + stream — chết thì chết nhanh; (3) `_retry` không thử lại khi cầu dao
đã đóng (cạn hạn mức NGÀY ≠ burst theo phút).
→ **LUẬT**: mọi lệnh gọi mạng trong vòng lặp N kênh PHẢI có timeout ngắn + cầu dao dùng chung. Một
lệnh chậm nhân với N là treo cả phiên, và phiên treo thì giết luôn các phiên sau qua khoá concurrency.

### 23/8 tối — MẮT XÍCH TREO CUỐI: mirror_b_to_b2 + MỌI lượt quét thiếu timeout
Sau khi vá cầu dao cho `_count_jobs` và `heal_unpushed`, phiên VẪN treo ~16-20'. Thủ phạm còn lại:
`mirror_b_to_b2()` quét 7 collection, không lượt nào có timeout -> riêng nó ~7 phút khi quota cạn.
Đã: (1) cầu dao bỏ qua hẳn khi `_RQ_DEAD` đóng; (2) timeout 15-20s cho toàn bộ 12 lệnh trong hàm;
(3) rà cả file, đặt `timeout=20` cho **mọi** `.stream()` còn lại (19 chỗ).
→ **LUẬT**: trong firestore_bridge KHÔNG được tồn tại lệnh gọi mạng nào không có timeout. Thêm hàm
mới mà quên timeout = thêm một chỗ có thể treo cả phiên và giết các phiên xếp sau.

### 23/8 tối — HẠ TRẦN THỜI GIAN JOB PLAN 60' → 18'
Bước điều phối khoẻ chỉ mất 2-4 phút. Khi nó treo, khoá `concurrency` giữ luôn hàng đợi và GitHub huỷ
mọi phiên xếp sau — tối nay mất 4 phiên liên tiếp vì đúng chuyện này. Trần 18' để phiên hỏng chết
nhanh, cron 10' sau mở phiên mới.
→ **LUẬT**: trần thời gian phải đặt theo THỜI GIAN CHẠY THẬT (× 4-5 lần), không đặt "cho rộng rãi".
Trần rộng biến một phiên hỏng thành một giờ đứng máy.

### BUG 23/8 tối — `NameError: name 'story' is not defined` (do chính bản vá gói-đăng)
Khi bổ sung mô tả/hashtag/tag vào MỌI lệnh ghi `done`, script chèn tự động dùng biến `story` cho cả
những khối mà biến kịch bản thật tên khác (`st_` trong `_doc_long_then_shorts` và nhánh toon-short).
Hậu quả: video render XONG rồi mới nổ ở bước ghi sổ — mất công render, job kẹt trạng thái.
Fix: dò biến thật theo dòng `title=<var>.get(...)` ngay trong khối rồi thay đúng tên; thêm bước quét
AST tìm mọi hàm dùng `story` mà không gán (đã sạch).
→ **LUẬT**: sửa hàng loạt bằng script thì PHẢI quét lại bằng AST, đừng tin `python -c "import ast"`
chỉ kiểm cú pháp — cú pháp đúng vẫn có thể sai TÊN BIẾN theo ngữ cảnh từng khối.

### BUG 24/8 — VỠ LUẬT 1 LONG : 3 SHORT khi quota đọc cạn (đo thật 1:4.5)
Đêm 23/8 cầu dao quota trả `count_done = 0` cho mọi kênh -> `_ratio_plan` tính chỗ trống từ số 0 nên
guard mất tác dụng. Đo trên phiên 21:24: **17 long / 77 short = 1:4.5**, vượt luật.
Fix: thêm sổ đếm TRONG PHIÊN (`_SESSION_MADE`, RAM, không cần Firestore), ghi nhận ngay tại
`enqueue_drive` khi đẩy kho thành công; `_ratio_plan` lấy mức CHẶT HƠN giữa số Firestore và số phiên.
Thử thật: 0 long -> ép làm long; 1 long -> cho 3 short; 1 long + 3 short -> lại ép long.
→ **LUẬT**: mọi hạn mức/tỉ lệ phải có đường tính DỰ PHÒNG không phụ thuộc Firestore. Guard chỉ đúng
khi quota khoẻ là guard hỏng đúng lúc cần nhất.

### BUG 24/8 — KEY CẠN QUOTA GIẾT CẢ LUỒNG (POWERPLAY ra 0 video)
Shim Groq/CF ném `RuntimeError("429 rate limit …")`, nhưng vòng xoay key chỉ bắt `CB.RateLimited`;
nhánh `except Exception` không nhận ra đó là lỗi quota nên `raise` -> chết cả kênh. Đêm 23/8: 16 key
Groq cạn hạn mức NGÀY (TPD 200K/key) và lane POWERPLAY trả 0 video **dù còn 40 key + CF + Gemini chưa
đụng tới**. Fix 3 lớp: (1) `RateLimited` kế thừa `RuntimeError` (mọi `except RuntimeError` cũ vẫn chạy);
(2) shim ném `RateLimited` thay vì `RuntimeError`; (3) lưới an toàn ở **6 hàm viết**: lỗi chứa
429/rate limit/quota/resource_exhausted -> cho key nghỉ + đổi key. Có test chặn hồi quy.
→ **LUẬT**: phân loại lỗi phải theo NỘI DUNG lỗi, không theo lớp ngoại lệ mà một shim tình cờ chọn.
Mọi vòng xoay tài nguyên phải có lưới "lỗi lạ mang dấu hiệu quota = đổi tài nguyên", không được `raise`.

### BUG 24/8 — "xoay vòng mà vẫn dồn vào key đã chết"
`_cool()` chỉ có 2 mức: nghẽn theo phút (1.1') và mọi thứ khác (20'). Key cạn HẠN MỨC NGÀY (Groq TPD
200K) cũng chỉ bị phạt 20' -> cứ 20 phút cả 18 luồng lại dội vào đúng những key đã chết, mỗi lượt tốn
1 vòng HTTP + 1.5s chờ. Nay 3 mức: phút → 1.1' · NGÀY → 8 giờ · mơ hồ → 20'. Áp cho cả 8 hàm viết.
→ **LUẬT**: thời gian phạt phải khớp CHU KỲ HỒI của hạn mức (phút/ngày), phạt sai chu kỳ thì vòng xoay
biến thành vòng dội.

### BUG 24/8 — PHÂN LOẠI SAI: cạn TOKEN/ngày bị gán nhãn "per minute" (POWERPLAY 0 video 3 phiên liền)
Groq có 2 loại hạn mức: SỐ LƯỢT (requests) và SỐ TOKEN (TPD). Code phân loại bằng header
`x-ratelimit-remaining-requests`: token cạn nhưng lượt vẫn còn -> `left>0` -> gán "per minute" ->
phạt 1.1' -> hết 1.1' cả 18 luồng lại dội đúng những key đã chết, không bao giờ tới CF/Gemini.
Triệu chứng: lane in `⏳ vòng 1/2/3 hết quota tạm → chờ 40s/80s/120s` rồi `TỔNG 0 video`.
Fix: đọc THẲNG nội dung lỗi ("tokens per day"/"TPD"/"per day") -> nhãn `daily` -> phạt 8h. Có test.
→ **LUẬT**: phân loại hạn mức phải dựa trên NỘI DUNG lỗi của nhà cung cấp, không dựa trên một header
đo đại lượng KHÁC. Sai một chữ ở đây là cả dây chuyền ra 0 video mà log vẫn báo "0 lỗi".

### 24/8 03:20Z — CẠN QUOTA VIẾT TRÊN CẢ 3 NHÀ CUNG CẤP (không phải lỗi code)
Sau khi vá xong chuỗi 3 lỗi phân loại/xoay key, log GRIDIRON cho thấy hệ ĐÃ lùi đúng: Groq `daily` ×3
-> nhảy sang Cloudflare ×42. Nhưng **42/49 key CF cũng báo hết quota** (10K neuron/ngày/tài khoản) và
hồ Gemini chỉ còn **1 key**. Kết quả: 0 video vì KHÔNG CÒN NHÀ CUNG CẤP NÀO CÒN ĐẠN, không phải vì bug.
→ **LUẬT VẬN HÀNH**: khi cả 3 nhà cung cấp viết đều cạn, ĐỪNG mở phiên mới — mỗi phiên đốt 18 luồng
GitHub mà chắc chắn ra 0 video. Chờ hạn mức hồi (Groq TPD + CF neuron reset theo ngày) hoặc thêm key.
Việc cần làm: bổ sung key Gemini (đang 1) — đó là nhà cung cấp DUY NHẤT chưa cạn tối nay.

### BUG 24/8 — CÔNG TẮC "DỪNG" BỊ CHÍNH PLAN XOÁ (dừng không nổi)
Dashboard bấm Dừng ghi `enabled:false, stop:true`, nhưng `plan_mode` có dòng
`FB.set_config(OWNER, {"last_safety_stop": None, "stop": None})  # xoá cờ dừng cũ` -> mỗi phiên tự
xoá cờ rồi vẫn spawn 18 luồng. Đêm 24/8 tắt máy lúc 03:50Z mà phiên 04:24Z vẫn mở đủ 18 lane.
Cách chặn chắc chắn hiện tại: `gh workflow disable render_cron.yml` (bật lại bằng `enable`).
→ **LUẬT**: cờ do NGƯỜI đặt (stop/pause) chỉ được xoá bởi hành động NGƯỜI (nút Chạy tiếp), tuyệt đối
không do tiến trình tự xoá. Cần sửa: plan chỉ xoá `last_safety_stop` (cờ do MÁY đặt), giữ nguyên `stop`.

### BUG 24/8 — THUMBNAIL TRẮNG TRÊN DASHBOARD (40 ảnh treo vô hạn)
Triệu chứng: không thấy ảnh nào, `complete=false`, `naturalWidth=0`, KHÔNG có onerror. Nhưng `fetch()`
đúng URL đó trả 200 + JPEG 28-46KB. Gốc: 40 thẻ <img> cùng gọi Worker, mà Worker phải lấy bytes từ
Drive (1-3s/ảnh); trình duyệt chỉ mở 6 kết nối/host -> tất cả xếp hàng và treo. `loading="lazy"` làm
nặng thêm (không kích hoạt trong bố cục này).
Fix: ảnh dùng `data-src`, bộ nạp `__rsLoadThumbs` rót TỪNG ĐỢT 6 ảnh, xong cái nào rót cái kế, ảnh
treo quá 12s thì nhường chỗ. Đo sau khi vá: 0/40 -> 40/40 ảnh hiện.
→ **LUẬT**: mọi danh sách ảnh đi qua proxy PHẢI có bộ nạp giới hạn số ảnh đồng thời. Trình duyệt
không báo lỗi khi hàng đợi tắc — nhìn y hệt "ảnh hỏng", rất dễ chẩn đoán nhầm.

### 24/8 — WEB TỰ F5 = ĐỐT QUOTA (đã bỏ)
Tab ẩn >90s thì ngắt listener để tiết kiệm quota (đúng), nhưng khi quay lại tab thì `location.reload()`
-> nạp lại toàn bộ kênh/key/video ≈ 200 lượt đọc MỖI LẦN chuyển tab. Nay nối lại listener tại chỗ,
dữ liệu cũ vẫn trong bộ nhớ trang nên Firestore chỉ gửi phần thay đổi.
→ **LUẬT**: không bao giờ reload cả trang để khôi phục kết nối — nối lại đúng thứ đã ngắt.

### 24/8 — DÒNG ĐẾM VIDEO TRỘN 2 NGUỒN (nhìn như số nhảy loạn)
"193 video trong kho · đang nạp 84" trộn sổ đếm LƯỢT ĐẨY cộng dồn với số bản ghi thật, nên bật/tắt bộ
lọc là con số nhảy 342 -> 79 -> 65. Nay số chính LUÔN là video đang có, cộng dồn ghi riêng có nhãn:
"81 video (đã đẩy cộng dồn 268 lượt, gồm cả bản đã thay thế)".

### 24/8 — CỜ DỪNG CỦA NGƯỜI: pipeline không được tự gỡ nữa
`plan_mode` trước đây xoá cả `last_safety_stop` (máy đặt) LẪN `stop` (người bấm) -> bấm Dừng không
dừng nổi. Nay chỉ xoá cờ của máy; thêm chốt ở `--gate`: có `stop` là đóng cổng ngay, kể cả khi còn
`run_now` cũ. Gỡ cờ chỉ bằng nút ▶️ Chạy tiếp / Render ngay.

### 24/8 — THỬ "MỘT TAB LÀM CHỦ" THẤT BẠI, ĐÃ GỠ
Ý tưởng: nhiều tab dashboard = nhiều bộ listener = nhân số lượt đọc; bầu 1 tab chủ qua localStorage,
tab phụ không mở listener. Đo thật: tab phụ VẪN 184 lượt đọc -> chặn ở `subscribe()` là chưa đủ vì
listener còn được mở rải rác (render studio, snapW rời). Đã gỡ, không để code nửa vời.
→ Muốn làm đúng: bọc TẤT CẢ điểm gọi `onSnapshot` qua một cổng duy nhất rồi mới bầu tab chủ.

### 24/8 — MỘT TAB LÀM CHỦ (bản làm ĐÚNG, đã đo)
Lần 1 thất bại vì chỉ chặn `subscribe()`. Đo lại mới thấy phần lớn lượt đọc đến từ `getDocs/getDoc`
MỘT-LẦN (nạp key/kênh/job), không phải onSnapshot. Bản đúng chặn CẢ HAI cửa:
 • `snapW` — tab phụ không mở onSnapshot, nhận dữ liệu tab chủ phát qua BroadcastChannel.
 • `gdGate/gdocGate` bọc `getDocs/getDoc` (import là HẰNG, không gán đè được — phải thay 18 điểm gọi).
   Tab chủ đọc thật rồi ghi localStorage; tab phụ đọc từ đó.
 • Tab chủ đóng >15s -> tab phụ tự lên thay.
Đo thật: tab chủ 549 lượt đọc · **tab phụ 0 lượt**, dữ liệu vẫn hiện đủ (210 key, 40/40 ảnh).
→ **LUẬT**: muốn cắt quota ở client thì phải bịt MỌI cửa đọc, không chỉ cửa realtime. Bộ đếm cũ chỉ
đếm onSnapshot nên che mất phần lớn lượt đọc — sửa đếm trước, rồi mới tối ưu.

### BUG 24/8 — Groq HTTP 400 "Failed to generate JSON" bị coi là lỗi CHẾT
Ở chế độ `json_object`, Groq thỉnh thoảng trả JSON hỏng -> HTTP 400. Trước đây ném `RuntimeError`
thường nên tầng trên coi là lỗi lạ và bỏ luôn kênh/lượt sinh. Đo phiên 07:19: **15 lần trong 14 luồng**
= 15 lượt sinh mất trắng (mỗi lượt vài nghìn token). Nay báo là lỗi TẠM (`RateLimited`) -> tầng trên
đổi key và thử lại như với nghẽn quota.
→ **LUẬT**: lỗi NGẪU NHIÊN của một lượt sinh (JSON hỏng, cắt giữa chừng) phải cho thử lại; chỉ lỗi
CẤU HÌNH (key sai, model không tồn tại, thiếu quyền) mới được coi là chết.

### 24/8 — THÊM NGUỒN VIDEO THẬT (Pexels Video + Pixabay Video)
User muốn thêm Mixkit / Coverr / Dareful / DVIDS / NARA. Kiểm khả thi trước khi làm:
 • **Pexels Video + Pixabay Video**: có API chính thức, DÙNG CHUNG key ảnh đã có (25 + 18 key) ->
   làm ngay, 0 thao tác thêm cho user. ĐÃ LÀM.
 • **Mixkit, Dareful**: KHÔNG có API công khai -> phải cào trang, dễ vỡ + sai điều khoản. KHÔNG làm.
 • **Coverr**: ĐÃ LOẠI (xem dòng dưới). **DVIDS / NARA**: có API, đã làm 24/8.
Cách hoạt động: cảnh 0 và mỗi 3 cảnh lấy 1 clip .mp4 (3-30s, ≥720p, ≤14MB, chọn bản nhỏ nhất còn đủ
nét); hỏng thì lùi về ảnh tĩnh nên không có đường nào làm video xấu đi. Engine Cinematic đã có
OffthreadVideo nên không phải sửa engine. Clip đi qua CÙNG sổ chống trùng với ảnh (id pxv:/pbv:).
Tắt khẩn cấp: đặt env `CLIPS_OFF=1`.
→ **LUẬT**: trước khi hứa thêm nguồn, kiểm API công khai có thật không — nguồn không API thì đừng cào.

### 24/8 — NGUỒN TƯ LIỆU MỸ: NARA + DVIDS (bật khi có key)
`nara:<key api.data.gov>` · `dvids:<key dvidshub>` — thêm vào hồ key như mọi key khác, hệ tự nhận,
tự xoay vòng, tự tắt key lỗi. Không có key thì hai nguồn này im lặng bỏ qua (trả rỗng), pipeline chạy
y như cũ. Đã kiểm: dán key nara giả -> vào hồ với nhãn provider "nara", KHÔNG bị nhận nhầm sang
Cloudflare (nhánh cf: bắt mọi token lạ nên phải chặn trước nó).
**Coverr: LOẠI HẲN (24/8, user chốt)** — link mp4 ký hạn 15' + đếm hạn mức tải, 18 luồng song song
chạm trần ngay. ĐỪNG thêm lại; nếu ai đó đề xuất nữa thì đọc dòng này.

### RÀ SOÁT 24/8 — LUỒNG B ↔ B2
Đã kiểm 4 điểm, 3 điểm LÀNH:
 • `mirror_b_to_b2` có guard `if _B2["on"] ... return 0` -> không bao giờ chép/drain khi ĐANG chạy B2
   (nếu không, `_db_jobs()` lúc đó trỏ B2 và sẽ tự chép vào chính nó).
 • Drain ngược render_jobs: `set(merge=True)` rồi mới xoá ở B2 -> mất mạng giữa chừng thì phiên sau
   drain tiếp, không mất job.
 • Cầu dao quota: mirror tự bỏ qua khi `_RQ_DEAD` đóng -> không góp phần treo phiên.
LỖI TÌM ĐƯỢC (đã vá): drain KHÔNG rót `render_stats`. Trong phiên khẩn, `count_pushed` cộng vào
`render_stats/__pushed__` **ở B2**; B hồi thì số đó biến mất -> dashboard đếm thiếu và `count_done`
tưởng kênh làm ít hơn thực tế -> **làm DƯ video**. Nay cộng dồn bằng Increment về B rồi xoá doc ở B2.
CÒN RỦI RO (chưa xử, cần quyết): khi chạy trên B2, `count_done` lấy số từ `render_stats/{owner}` —
sổ này vừa bị reset 23/8 nên trong phiên khẩn kế tiếp hệ sẽ đếm thấp hơn thực tế. Sổ tự dựng lại sau
vài phiên; muốn chắc thì nạp lại số đếm từ số job thật một lần.

### 24/8 — DÒNG ĐẾM NÓI SAI SỰ THẬT (user: "sao lẫn lộn thế")
Dashboard chỉ NẠP 120 bản ghi mới nhất (limit 40 ở A + 80 ở B — giới hạn đặt 23/8 để tiết kiệm quota),
nhưng dòng đếm lại in `done.length` như thể đó là kích thước kho. Kết quả: hiện "93 video" trong khi
kho thật có **414** -> user tưởng bấm xoá làm mất video. Nay in rõ hai phần:
"📤 414 video trong kho · đang hiện 14 mới nhất". Số 414 lấy từ sổ đếm (1 lượt đọc), không phải đếm
danh sách đã nạp.
→ **LUẬT**: khi danh sách bị CẮT BỚT để tiết kiệm quota, con số hiển thị PHẢI nói rõ "đang hiện N/M",
không được để người đọc tưởng phần hiện là toàn bộ. Tối ưu quota mà làm số liệu nói dối là tối ưu hỏng.

### 24/8 — THÊM 2 NGUỒN VIDEO KHÔNG CẦN KEY: Internet Archive + NASA video
Kiểm bằng lệnh gọi THẬT trước khi viết code (không tin tài liệu):
 • archive.org → **200** ✅ không cần key, chứa **PRELINGER ARCHIVES** (user từng nhắc). Lọc theo
   collection phạm vi công cộng để không dính bản quyền. Thử thật: query "city street 1950s" ra clip.
 • images-api.nasa.gov `media_type=video` → **200** ✅ không cần key. Trước mình chỉ lấy ẢNH của NASA.
 • loc.gov (Library of Congress) → **403** ❌ chặn bot bằng Cloudflare challenge. KHÔNG dùng được.
Thứ tự nguồn clip hiện tại: Pexels → Pixabay → NARA → DVIDS → Internet Archive → NASA video.

### 7.x — Key nguồn tư liệu Mỹ: DVIDS dán liền 2 khoá, và bộ kiểm key giết oan (24/8/2026)

**Đo được:**
- Trang DVIDS `accounts/<id>#tab_applications` có cột tiêu đề **"Public Key/Private Key"**, hiển thị
  HAI khoá **dính liền không dấu phân cách**: public = `key-` + 13 ký tự (17), private = 40 ký tự.
  Copy cả ô ra chuỗi 57 ký tự → API trả `403 "API key is not in a valid format"`.
  Cắt 17 ký tự đầu → **200**, 1.000 kết quả. (Đó là lý do "thêm key DVIDS mãi không được".)
- Ô thêm key ở dashboard chốt `length < 20` → public key 17 ký tự bị chặn im lặng.
- Nút "⚡ Kiểm ngay" ném key `nara:`/`dvids:` xuống nhánh cuối (Gemini) → Google 403 →
  ghi `alive:false, dead_kind:"permanent"` = **giết oan key vừa thêm**.
- NARA (`catalog.archives.gov`) không trả header CORS → trình duyệt luôn "Failed to fetch",
  không phân biệt được key sống/chết.
- Worker gọi DVIDS **không kèm User-Agent** → 403 + trang HTML. Thêm UA là 200.
  (Pipeline python đã luôn gửi `UA` nên không dính; chỉ Worker thiếu.)

**Đã sửa:**
- `dashboard/index.html`: chuỗi `key-` 57 ký tự tự **tách lấy public key**; nới chốt độ dài cho
  đúng dạng `key-…`; nhánh kiểm riêng cho `nara:`/`dvids:` đi qua Worker.
- `connect-worker/src/worker.js`: thêm route `/api/key-probe?kind=nara|dvids|pexels|pixabay&key=…`
  (gọi hộ phía server, có UA). Nhà cung cấp trả **trang HTML chặn** ⇒ báo `status 0` (chưa rõ),
  KHÔNG báo chết — nguyên tắc: không kết luận key hỏng từ một lần chặn tầng mạng.

**Luật:** thêm nguồn key mới thì phải làm ĐỦ 3 chỗ — nhận diện khi dán, nhánh kiểm sống/chết,
và pipeline đọc. Thiếu nhánh kiểm thì bộ kiểm sẽ đánh chết key tốt.

### 7.y — Vỡ trần Firestore: publish chết 11/12 lượt vì đọc lặp (24/8/2026)

**Triệu chứng đo được:** `publish` thoát ngay ở lệnh đọc ĐẦU TIÊN với `429 Quota exceeded`,
11/12 lượt cron gần nhất → **video render ra nhưng không cái nào được đăng**. Log chỉ nói
"hết hạn mức", không nói project nào.

**Ba nguồn rò, tính theo số lượt cron thật trong 24h (publish 36 · social 33 · thumbnail 37 ·
guardian 20 · stats 4 ≈ 130 lượt):**

1. **Project B — auto_enqueue quét mù.** Mỗi lượt quét 40 doc `done` mới nhất của TỪNG kênh:
   55 kênh × 40 × 48 lượt/ngày ≈ **105.000 lượt đọc** — một mình gấp đôi trần 50K. Mà 39/40 doc
   quét được đều đã xếp lịch từ lâu.
   → Vá: `update_job` đóng `queued=False` ngay khi job sang `done`; auto_enqueue truy vấn
   `status==done AND queued==False` (toàn bằng-nhau ⇒ không cần composite index), trả về đúng
   video mới. Lối quét cũ giữ làm **quét vét 6h/lần** cho doc tạo trước ngày có cờ.
   *105.000 → ~2.500 lượt/ngày.*

2. **Project A — đọc lại bảng `connections` hàng trăm lần.** `list_connections` bị gọi 2-3 lần
   mỗi lượt cron (main.py 451/452, publish_social 55/59/122, storage.py 195), mỗi lần quét lại
   cả bảng (~55 youtube / ~73 drive); `get_connection` còn gọi RIÊNG cho từng kênh trong vòng lặp
   55 kênh. ≈ 250-300 lượt đọc A cho MỘT lượt cron.
   → Vá: đệm theo tiến trình (`_CONN_CACHE`), quét 1 lần/loại; `get_connection` lấy từ đệm đó.
   Token chỉ đổi khi người dùng bấm kết nối/ngắt nên đệm không sai lệch. *~300 → ~128 lượt/lượt cron.*

3. **Không ai biết cạn ở đâu.** → `chan_doan_429()`: dính 429 thì thăm dò 1 doc ở mỗi project và
   in rõ A/B/C project nào cạn. 3 lượt đọc thêm, chỉ khi đã hỏng.

**Cơ chế chống tái phát — `src/quota_guard.py`:** sổ đọc/ghi theo NGÀY-GOOGLE (UTC-7, khớp mốc
reset) cho từng project, cộng bằng `Increment` (1 đọc + 1 ghi/tiến trình = 0,26% trần).
`du_suc(project, n)` là **PHANH**: việc PHỤ (quét vét, thống kê, dựng lại thumbnail) bị chặn từ
ngưỡng **75%**, việc THIẾT YẾU (đăng video) chạy tới sát trần.

**Luật:** mọi vòng lặp `for kênh in ...` có truy vấn Firestore bên trong đều là bom hẹn giờ —
số kênh tăng thì lượt đọc tăng theo cấp số. Thấy khuôn đó thì phải đổi sang **một truy vấn có cờ**,
và việc nào không phải "đăng video" thì phải hỏi `quota_guard.du_suc()` trước khi chạy.

**Bổ sung 7.y — `drive_usage` (guard kho đầy):** quét cả bảng `storage_accounts` (~73 doc trên
project A) và MỖI luồng render gọi một lần ở đầu `main()` → 18 luồng × 73 ≈ **1.300 lượt đọc A
mỗi phiên** để trả lời một câu hỏi mà cả 18 luồng nhận CÙNG đáp án. Nay kết quả cất ở
`render_stats/__drive_usage__` (project B, TTL 30'): plan quét thật (`moi_nhat=True`) và dựng đệm,
luồng chỉ đọc 1 doc. Quét hỏng thì **không ghi đè đệm bằng số 0** — guard đọc phải số 0 sẽ tưởng
kho rỗng và render vô tội vạ.

### 7.z — 18 luồng cùng phát hiện lại một key đã cạn (24/8/2026)

**Đo ở phiên 08:47** (dòng kế toán cuối mỗi luồng): `83-87 GHI (cool_key=44 · update_job=25 · ...)`
→ **44 lượt ghi cool_key mỗi luồng × 18 luồng ≈ 800 lượt ghi project B** trong khi số key thật sự
cạn chỉ khoảng 50.

**Gốc:** `read_keys` đọc doc ẢNH `__snap__`, mà ảnh này chỉ được dựng lại ở bước **plan** (1 lần/phiên).
Nên `cooling_until` do luồng A vừa ghi KHÔNG BAO GIỜ xuất hiện với luồng B trong cùng phiên → mỗi
luồng phải tự đâm vào key đã chết, ăn 429, rồi ghi lại đúng lệnh nghỉ mà luồng khác vừa ghi. Tốn
cả lượt ghi lẫn thời gian (mỗi lần phát hiện là một vòng HTTP + chờ).

**Vá:** thêm doc gộp `gemini_keys/__cool__{owner}` — `cool_key` ghi lệnh nghỉ DÀI vào đó
(`{key_id: until}`, merge), `read_keys` phủ nó lên danh sách bằng 1 lượt đọc. Luồng sau biết ngay
key nào đang nghỉ, không thử nữa. Cùng khuôn với overlay `__req__` đã có.
*~800 → ~100 lượt ghi/phiên, và cắt ~17 vòng HTTP-429 lặp cho mỗi key cạn.*

**Ghi nhận kèm (chưa vá, gốc nằm ở chỗ khác):** log phiên 08:47 có `🔀 FAILOVER ... (gương tuổi
948 phút)` — gương B2 cũ 16 tiếng. `mirror_b_to_b2` chỉ chạy ở plan và tự tắt khi đã lật sang B2,
nên B ốm dài ngày thì gương không bao giờ tươi lại; `count_done` lúc đó đọc số cũ → dễ **làm dư
video**. Đường chữa đúng là đừng để B cạn (mục 7.y), không phải nới điều kiện mirror.

**Luật:** trạng thái CHIA SẺ giữa 18 luồng (key nghỉ, kho đầy, chỉ tiêu) không được nằm trong doc
ảnh dựng-một-lần-mỗi-phiên. Phải có doc gộp ghi-được-trong-phiên, nếu không mỗi luồng sẽ tự trả giá
để học lại cùng một điều.

### 7.aa — Ba lỗi phiên 08:47: gương B2 chết âm thầm · PULSE quá ngắn · 10/30 hiểu sai (24/8/2026)

**1. Gương B→B2 hỏng MỌI PHIÊN, không ai biết.**
Log: `⚠️ mirror B→B2 lỗi ('_UnaryStreamMultiCallable' object has no attribute '_retry')` — lỗi
tương thích của `google-cloud-firestore` (workflow `pip install` không ghim phiên bản) ở lệnh
`.stream(timeout=…)`. Cả hàm gương nằm trong **một** `try` nên hỏng bước đầu là mất sạch: B2 đứng
im **16 tiếng**, tới lúc failover mới lòi ra `gương tuổi 948 phút`.
→ Vá: `_stream_at()/_get_at()` — gặp `AttributeError/TypeError` thì gọi lại không kèm `timeout`
(lỗi thật 429/mạng vẫn ném lên để cầu dao xử lý); mỗi bước gương có `try` RIÊNG; `mirror_meta` được
đóng dấu **kể cả khi hụt bước**, kèm danh sách bước hỏng.

**2. PULSE render ra clip 12,8s → QC loại 15 lần/phiên.**
Độ dài PulseShort = tổng độ dài giọng đọc; mỗi mục một câu ngắn nên 5 mục ≈ 12-15s, dưới sàn 20s.
Mỗi lần loại mất trắng 1 lượt viết AI + 1 lượt render (PULSEUSA cả phiên chỉ đẩy được 2 video).
→ Vá: đo trước khi dựng, thiếu bao nhiêu thì **rải đều vào thời gian giữ mỗi mục** (trần 2,5s/mục).
Không bịa thêm nội dung, không kéo giọng đọc.

**3. `10 long / 30 short` bị dùng làm TRẦN TRỌN ĐỜI.**
`RESERVE_LONG/RESERVE_SHORT` (10/30) vừa là mẻ mỗi vòng (`round_long/round_short`) vừa là chỉ tiêu
mặc định → kênh làm xong **đúng một vòng** là bị cho nghỉ vĩnh viễn, dù video đã đăng hết.
→ Vá: `_muc_tieu()` — anh tự đặt chỉ tiêu trên dashboard (>0) thì đó là trần thật; không đặt (=0)
thì **kho trôi**: mỗi vòng mở thêm đúng một mẻ, kênh luôn còn việc. Chặn phình kho là việc của
`DRIVE_SAFETY_PCT` (kho ≥90% thì ngừng), không phải của chỉ tiêu.
Kèm theo: thứ tự ưu tiên đổi từ "thiếu nhiều nhất" sang **"tổng video ít nhất đứng trước"** — với
kho trôi thì "còn thiếu" gần như bằng nhau ở mọi kênh nên khoá cũ vô nghĩa, kênh mới sẽ nằm chờ mãi.

**Luật:** hàm nào là LƯỚI AN TOÀN (gương, failover, backup) thì (a) không được để cả thân hàm trong
một `try`, (b) phải để lại dấu vết đo được mỗi lần chạy — hỏng âm thầm còn tệ hơn không có lưới.

### 7.ab — Cạn hạn mức rồi vẫn đập vào Firestore: vì sao "vừa reset đã cháy" (24/8/2026)

**Điều bị bỏ sót:** lượt đọc THẤT BẠI vì 429 **vẫn tính vào hạn mức**. Nên khi A cạn, mọi cơ chế
"thử lại cho chắc" biến thành máy đốt quota:
- `firestore_state._retry`: 5 lần/lệnh, ~22s chờ — mà cạn hạn mức NGÀY thì thử lại 5 lần cũng vô ích.
- `storage.firestore_pool_accounts`: vòng `for wait in (0, 8, 25)` × ~73 doc, lặp mỗi 30' (hết TTL)
  cho **từng luồng**: 18 luồng × 5 lần × 3 × 73 ≈ **20.000 lượt đọc hỏng mỗi phiên**, cộng 33s ngủ.

Log phiên 08:47 xác nhận: mọi luồng in `🪞 A nghẽn — dùng GƯƠNG kho ở B` **từ 09:18** — tức A đã
chết chưa đầy 90 phút sau mốc reset, rồi bị đập tiếp cả ngày. Sáng sau vừa reset là cháy lại ngay.

**Vá — "đệm âm" (nhớ rằng đã cạn):**
- `_retry`: 429 lần đầu vẫn thử lại (burst thoáng qua là có thật); hết lượt mà vẫn 429 thì ghi mốc
  **nghỉ 30 phút**, trong khoảng đó gặp 429 là ném ngay cho tầng trên chuyển sang gương/đệm.
- `firestore_pool_accounts`: A trả 429 → đặt mốc nghỉ 30' và **đi thẳng sang gương B/B2**, bỏ hẳn
  vòng thử lại. Đo thật: 33s → **0,07s**, và 0 lượt đọc A.

**Luật:** phân biệt **burst thoáng qua** với **cạn hạn mức cả ngày** — cùng mã 429 nhưng chữa ngược
nhau. Thử lại chỉ đúng cho cái đầu; với cái sau, mỗi lần thử là tự bắn vào chân.

### 7.ac — A cạn = KHÔNG ĐĂNG ĐƯỢC VIDEO NÀO (điểm chết đơn của khâu đăng bài, 24/8/2026)

Chẩn đoán mới (`chan_doan_429`) ở lượt publish 11:50Z in ra đúng thủ phạm:
`A ❌ CẠN 429 · B còn hạn mức · C còn hạn mức`.

**Vì sao nguy:** token YouTube/Facebook chỉ nằm ở **A**. Gương `connections_mirror` (dựng 23/8) có
điều kiện `refresh_token AND root` — `root` là id thư mục Drive, nên **chỉ kho Drive được chép**.
Kết quả: A cạn thì render vẫn chạy, vẫn đẩy kho được (nhờ gương Drive), nhưng **không đăng được cái
nào** — đúng cảnh "render làm gì khi không đăng được".

**Vá 3 lớp:**
1. `mirror_connections_to_b`: bỏ điều kiện `root` → chép **mọi** connection có `refresh_token`
   (drive + youtube + facebook). Rules B khoá kín nên token không lộ thêm.
2. `State.list_connections` / `get_connection`: gặp 429 ở A thì đọc **gương ở B**, không chết lượt đăng.
3. `State.get_doc`: lượt publish 11:50Z chết ngay ở dòng đầu — `settings/overrides`, một doc cấu
   hình TUỲ CHỌN. A cạn → trả `None` + báo, chạy bằng mặc định thay vì giết cả lượt đăng.

**Lưu ý vận hành:** gương chỉ tươi lại được khi plan đọc được A. A đã cạn từ 09:18 hôm nay nên gương
chưa có token YouTube — lớp bảo vệ này có hiệu lực **từ phiên plan đầu tiên sau khi A hồi** (~07:00Z).

**Luật:** mỗi dữ liệu SỐNG CÒN phải trả lời được câu "project giữ nó chết thì việc gì dừng?".
Trả lời là "khâu đăng bài" thì bắt buộc phải có gương ở project khác.

### 7.ad — VÒNG XOÁY TỰ SIẾT: A cạn khiến hệ đập vào A mạnh hơn (24/8/2026)

Đây là mắt xích **gốc** của việc "vừa reset ngày mới đã cháy sạch A". Chuỗi nhân quả đo được:

1. `mirror_connections_to_b` đọc **A ở dòng đầu tiên**. A cạn → ném → `return 0`.
2. Nên doc gói `connections_mirror/__snap__` **không được dựng**.
3. Mà `__snap__` chính là lối **1-lượt-đọc** của `pool_accounts`.
4. Không có nó, mỗi luồng rơi xuống lối cũ: thử A **3 lần × ~73 doc**, cứ 30' một vòng (hết TTL),
   suốt 165', **× 18 luồng ≈ 20.000 lượt đọc A mỗi phiên**.
5. Lượt đọc **hỏng vì 429 vẫn tính vào hạn mức** → A bị dìm sâu hơn, hôm sau vừa reset là cháy lại.

Bằng chứng: log phiên 08:47 có `🪞 A nghẽn — dùng GƯƠNG kho ở B: 73 tài khoản` ở **mọi** luồng —
dòng đó thuộc lối QUÉT 73 doc, tức lối `__snap__` đã hụt.

**Vá:** `_dung_snap_tu_B()` — A không đọc được thì **dựng lại `__snap__` từ chính gương ở B**
(B còn hạn mức). Gói luôn tươi bất kể A sống hay chết; chỉ thiếu kho MỚI kết nối trong lúc A chết,
phiên sau A hồi là đầy đủ. 18 luồng phía sau tốn **1 lượt đọc/luồng** thay vì đập vào A.

**Luật:** đường dự phòng KHÔNG được phụ thuộc vào chính thứ nó dự phòng. Gương mà chỉ dựng được khi
nguồn còn sống thì đúng lúc cần nhất nó sẽ không có.

### 7.ae — Clip thật hỏng CÂM + hồ ảnh Pexels teo còn 1 key (24/8/2026)

**Đo được ở phiên 08:47 (118 video):**
- **0 dòng `🎬 clip thật`** trong toàn bộ log. Tính năng clip video (6 nguồn, gắn 24/8) **chết 100%**
  mà nhìn log vẫn tưởng bình thường — vì `fetch_clip()` CHỈ in khi thành công, mọi đường thất bại
  đều `continue`/`return None` không một chữ nào.
- `🖼️ Pexels: 1 key` xuất hiện **87 lần** so với `25 key` chỉ **49 lần**. Hồ ảnh teo thì hết lượt
  Pexels rất nhanh → phải nhờ AI vẽ ảnh bù → đốt quota Gemini/Cloudflare, và `fetch_clip` không còn
  ứng viên nào để tải.
- Phạm vi: clip mới chỉ gắn ở nhánh dựng cảnh của `build_doc_props` (format `doc`), chưa phủ các
  format khác.

**Đã làm:** gắn mắt đo, chưa vá gốc (chưa xác định được ai truyền hồ rỗng xuống — không đoán bừa).
- `fetch_clip`: thất bại cũng phải in — phân biệt `không nguồn nào trả clip` (kèm số key mỗi hồ:
  px/pb/nara/dvids) với `N ứng viên nhưng không lấy được: X đã dùng · Y tải hỏng`.
- `set_pexels_pool`: hồ ≤1 key mà đầu vào KHÔNG có key `px:` nào → cảnh báo kèm số key nhận vào.

**Luật:** thêm tính năng mà không thêm đường log cho ca THẤT BẠI thì tính năng đó có thể chết 100%
trong nhiều ngày mà không ai biết. Mọi nhánh `return None` im lặng đều là một điểm mù.

### 7.af — GỐC của "clip thật chết + hồ ảnh teo": failover kéo theo mất kho key ảnh (24/8/2026)

Truy tới cùng, ba triệu chứng tưởng rời nhau hoá ra **một gốc**.

**Chứng cứ số:**
- `🖼️ Pexels:` in **136** lần · `🧩 Pixabay:` chỉ **49** lần → chênh đúng **87**. Tức 87 lượt nạp hồ
  KHÔNG có key `px:` LẪN `pb:` (Pexels còn "1 key" là nhờ biến môi trường `PEXELS_KEY`, Pixabay
  không có đường lùi nên im luôn). **Cả hai loại key ảnh cùng biến mất một lúc** — không phải hao mòn.
- Trong mỗi luồng, thứ tự luôn là `25 1 1 1` lặp lại: video LONG đủ 25 key, 3 SHORT sau đó còn 1.
- **18/18 luồng đều `🔀 FAILOVER` sang B2** ngay đầu phiên.

**Chuỗi nhân quả:** B cạn → failover → `read_keys` đọc kho key ở **B2** → mà `mirror_b_to_b2` **hỏng
suốt 16 tiếng** (mục 7.aa) nên bản sao key ở B2 vừa cũ vừa thiếu → **kho key ảnh rơi mất** → không
còn ảnh thật, phải nhờ AI vẽ (đốt quota Gemini/Cloudflare) → `fetch_clip` không còn ứng viên nào →
**0 clip thật trên 118 video**, mà không một dòng log nào báo (mục 7.ae).

**Vá 2 lớp (vá gương thôi là chưa đủ):**
1. Gương B→B2 đã sửa (7.aa).
2. `_giu_key_anh()`: key ảnh **không hết hạn, không bị phạt nghỉ** → thấy lần nào thì nhớ luôn trong
   tiến trình; lượt đọc sau thiếu thì **bù lại từ bộ nhớ** kèm cảnh báo. Hồ ảnh không còn phụ thuộc
   vào việc shard nào đang trả lời. Có test trong `selftest.py`.

**Luật:** dữ liệu KHÔNG BAO GIỜ THAY ĐỔI (key ảnh, key lưu trữ) thì đừng đọc lại nó theo đường có thể
hỏng. Đọc được một lần là giữ; lượt sau thiếu là bù, không phải là "hết".

### 7.ag — Hai lỗi tiềm ẩn DO CHÍNH BẢN VÁ TỐI NAY sinh ra (24/8/2026)

Rà lại code mình vừa sửa, bắt được hai chỗ hỏng-ngầm — chưa gây hậu quả nhưng chắc chắn sẽ gây:

**1. "Đệm âm" dùng chung một mốc nghỉ cho cả 3 project.**
`_CAN_QUOTA["den"]` là một biến duy nhất, trong khi `_retry` phục vụ cả A, B lẫn C. A cạn hạn mức
(chuyện đang xảy ra HẰNG NGÀY) sẽ khoá luôn đường thử-lại của **B và C** suốt 30 phút — mà B/C vẫn
còn hạn mức và cơn 429 của chúng thường chỉ là burst thoáng qua, thử lại là qua.
Hậu quả nếu để nguyên: một nhịp nghẽn ở C là **rớt luôn lượt đăng của video đó**, không thử lại.
→ Vá: sổ nghỉ tách theo project (`_CAN_QUOTA_P`), 9 lượt đọc/ghi trên C đi qua `_retry_C`.
Đo: A đang nghỉ → A chỉ thử 1 lần; C vẫn thử đủ 5 lần.

**2. Quét vét lần ĐẦU bị phanh quota chặn → video cũ không bao giờ được đăng.**
Mọi video `done` render trước hôm nay đều không có trường `queued`, chỉ quét vét mới bắt được.
Nhưng quét vét bị xếp là "việc phụ" nên phanh 75% chặn — mà bị chặn thì mốc `at` không được ghi →
lượt sau vẫn "chưa từng quét" → lại bị chặn. **Vòng lặp chết: số video cũ đó mất luôn đường lên sóng.**
→ Vá: lần quét đầu tiên (chưa có mốc `at`) tính là **việc thiết yếu**, không hoãn.

**Luật:** phanh quota chỉ được **hoãn** việc, không được **bỏ rơi** việc. Bất kỳ bước nào mà "bị hoãn"
đồng nghĩa với "không bao giờ chạy" thì phải xếp vào nhóm thiết yếu.

### 7.ah — GỐC của "42 Groq · 59 Gemini · 52 CF mà mới đầu ngày đã chạm trần" (24/8/2026)

**Số đo phiên 08:47:** `⚠️ verify_image lỗi (… You exceeded your current quota)` **108 lần**;
`429` tổng **651 lần**; `Quota exceeded` **225 lần** — trên chỉ 118 video.

**Nguyên nhân:** `set_ai_pool()` chạy **một lần mỗi video** (đo được 136 lần/phiên) và trong đó có
hai dòng:
```
_AI_POOL["dead"] = set()      # quên sạch key nào đã cạn hạn mức VẼ ẢNH
_VIS_DEAD.clear()             # quên sạch key nào đã cạn hạn mức VISION
```
Tức là cứ sang video mới, hệ **quên hết** những key vừa trả 429 ở video trước, rồi lôi đúng chúng
ra dùng lại. Mỗi ảnh còn đổi key tối đa 3 lần → **hàng nghìn lượt gọi chắc chắn thất bại mỗi phiên**.
Mà **lượt gọi hỏng vẫn bị trừ vào hạn mức** của nhà cung cấp — y hệt bài học Firestore ở mục 7.ab.
Càng nhiều key càng lâu phát hiện, vì lúc nào cũng còn key "chưa thử" để đâm vào.

**Vá:** trí nhớ key-đã-cạn **sống xuyên video**, có mốc hết nghỉ 90 phút (`_vis_chet/_vis_die`,
`_ve_chet/_ve_die`) — key dính giới hạn THEO PHÚT vẫn quay lại được, key cạn theo NGÀY không bị lôi
ra dùng liên tục nữa. Có test `t_nho_key_can` trong `selftest.py`.

**Cộng hưởng với 7.af:** khi kho key ẢNH rơi mất (failover B2), hệ phải nhờ AI VẼ thay cho ảnh thật
— nhân thêm số lượt gọi Gemini/CF. Hai lỗi này cùng nhau giải thích trọn vẹn vì sao hồ key lớn mà
vẫn cháy sớm.

**Luật (lặp lại lần thứ ba trong một đêm, nên viết to):** *bất kỳ chỗ nào biết "cái này đã cạn" mà
lại quên đi theo chu kỳ ngắn, đều là một máy đốt hạn mức.* Trí nhớ phải sống ít nhất bằng chu kỳ
hạn mức của nhà cung cấp, không phải bằng vòng đời một video.

### 7.ai — Sổ nghỉ DÙNG CHUNG cho 18 luồng (mô hình central rate-limiter, 24/8/2026)

**Lỗ hổng còn lại sau 7.ah:** trí nhớ "key này đã cạn" mới chỉ sống trong MỘT tiến trình. Mà 18 luồng
render là **18 tiến trình trên 18 máy khác nhau, không chia sẻ gì**. Luồng 3 phát hiện key X cạn thì
17 luồng kia không hề biết — mỗi luồng phải tự đâm vào để học lại **cùng một điều**, và mỗi lần đâm
là một lượt gọi hỏng bị nhà cung cấp trừ hạn mức. Nhân 18 luồng × mỗi key = phí thật.

**Chuẩn ngành:** các hãng lớn giải bài này bằng **central rate-limit service** (Envoy ratelimit,
Redis token-bucket dùng chung) — mọi worker hỏi một chỗ trước khi gọi. Mình không có server luôn bật,
nên dùng **1 doc Firestore làm chốt chung**: `gemini_keys/__cool__{owner}`.
- Phát hiện key cạn → `share_key_rest(kind, kid, until)` — 1 lượt ghi mềm.
- Đầu mỗi video → `nap_so_nghi_chung()` — 1 lượt đọc, đệm 5 phút.
- Danh tính key ghi bằng **SHA1 12 ký tự**, không bao giờ ghi key trần ra ngoài.

Chi phí ~1 đọc/5'/luồng, đổi lại cắt hàng trăm lượt gọi chắc chắn 429 sang Gemini/CF mỗi phiên.
Đo thử: luồng mới nạp sổ và biết ngay key đã cạn **mà chưa gọi API lần nào**.

**Luật:** khi N worker cùng dùng chung một hồ tài nguyên có hạn mức, tri thức "cái này đã hết" phải
nằm ở chỗ **dùng chung**, không phải trong RAM của từng worker. Không có chỗ chung thì mỗi worker sẽ
tự trả giá để học lại cùng một bài học.

### 7.aj — Nghỉ ĐÚNG MỨC theo loại hạn mức · Dashboard mù khi đang failover (24/8/2026)

**1. Gộp "chặn theo phút" với "cạn theo ngày" làm một mức 90' là sai (anh chỉ ra).**
Ba loại 429 chữa ngược nhau:
- **RPM/TPM (theo phút)** — key vẫn tốt, chỉ cần thở. Cho nghỉ 90' là **ném đi 88 phút hạn mức còn
  dùng được** của một key khoẻ. Hồ 153 key mà mỗi cơn RPM lại loại một key suốt 90' thì tới trưa
  còn vài key là đúng.
- **RPD/TPD (theo ngày)** — gọi lại trước mốc reset là chắc chắn 429, mà lượt hỏng vẫn bị trừ.
- **Không rõ** — 20' là mức thoả hiệp.
→ `_muc_nghi(err)` đọc nguyên văn lỗi và trả: **2 phút** / **tới 00:00 giờ Thái Bình Dương** / 20 phút.
Đo thật: `per minute` → 2' · `tokens per day` → 1094' · `free_tier ... per_day` → 1094' · lỗi trống → 20'.
Áp cho cả 4 đường: `_verify_image_rot`, `_verify_grid_rot`, `_check_visual_rot`, `_generate_image_ai`.

**2. `⚙️ Đang chạy: 0` trong khi 8 luồng đang chạy thật.**
Khi B nghẽn, mọi luồng lật sang **B2** và ghi trạng thái job vào đó — còn dashboard đọc **B**.
Trang web mù suốt cả phiên, và số liệu nhảy lung tung vì một phần nằm B, một phần nằm B2.
Mấu chốt: failover kích hoạt do cạn hạn mức **ĐỌC**, hạn mức **GHI** của B thường vẫn còn.
→ `ghi_nhip_song()`: đang chạy trên B2 thì vẫn ghi một dòng nhịp sống về **B**, gộp hết vào MỘT doc
`render_stats/__live__{owner}`. Dashboard đọc 1 doc đó (cùng lượt với sổ đếm, gần như không thêm chi
phí) và lấy mức LỚN HƠN giữa hai nguồn; mục nào im quá 45' thì bỏ.

**Luật:** shard dự phòng phải giữ cho hệ **chạy được**, nhưng không được làm hệ **mất tiếng nói**.
Lật shard mà quên đường báo cáo thì người vận hành mù đúng lúc cần nhìn nhất.

**Bổ sung 7.aj — doc nhịp sống phải được DỌN.** `ghi_nhip_song` ghi mỗi job thành một TRƯỜNG trong
doc `render_stats/__live__{owner}`, dùng `merge` nên **không bao giờ tự mất đi**: ~120 job/phiên,
vài ngày là chạm trần **1MB** của Firestore → mọi lượt ghi nhịp sống hỏng, mà dashboard lại phải tải
về một doc ngày càng nặng. `don_nhip_song()` giữ 2 giờ gần nhất rồi ghi đè, chạy 1 lần/phiên ở plan
(1 đọc + 1 ghi). **Luật: mọi doc gộp ghi bằng `merge` đều phải có đường dọn, nếu không nó là quả bom hẹn giờ.**

### 7.ak — Hai thứ chuẩn ngành mình còn thiếu, và đã bù (24/8/2026)

Rà lại các sự cố đêm nay, hai cái đắt nhất đều KHÔNG phải lỗi logic — mà là thiếu hai nền nếp kỹ
thuật mà ngành đã chuẩn hoá từ lâu:

**1. Không ghim phiên bản thư viện (reproducible build / lockfile).**
Workflow chạy `pip install google-cloud-firestore` **không ghim phiên bản** → mỗi phiên cài "bản mới
nhất tại thời điểm đó". Một bản phát hành mới của Google làm gãy `.stream(timeout=…)` →
`'_UnaryStreamMultiCallable' object has no attribute '_retry'` → **gương B→B2 chết âm thầm 16 tiếng**.
Mã nguồn không đổi mà hành vi đổi theo NGÀY CÀI ĐẶT thì không thể suy luận ra sự cố.
→ `render-pipeline/constraints.txt` (sàn = bản đã qua selftest, trần = chặn nhảy MAJOR) + **in phiên
bản thư viện vào log mỗi phiên**. Lần sau có sự cố kiểu này: 1 phút đối chiếu thay vì hàng giờ đoán.

**2. Không có chỉ số tỉ lệ thành công → hỏng câm không ai biết.**
Clip video chết **100% suốt 118 video** mà log vẫn sạch. Cách ngành chặn: mỗi phụ thuộc có một chỉ
số tỉ lệ thành công, và **cảnh báo riêng cho ca tụt về 0** — vì 0% là dấu hiệu HỎNG CẤU HÌNH, khác
hẳn 30% (chỉ là chất lượng kém).
→ `dem_khau()/bao_cao_khau()`: đếm thử/được từng khâu, cuối mỗi luồng in `📈 tỉ lệ dùng được: …`;
khâu nào thử ≥3 lần mà 0 lần được thì in `🚨 CHẾT CÂM`.

**Luật:** một tính năng không có chỉ số đo được là một tính năng **có thể đã chết mà không ai biết**.
Và một môi trường chạy không ghim phiên bản là một hệ **không thể lặp lại**, nên cũng không thể gỡ lỗi.

### 7.al — Chữ chồng chéo: hai lớp vẽ độc lập, đúng 1/4 số video dính (24/8/2026)

**Bằng chứng:** ảnh chụp DEFENSEUSA (`$750B`) và CRIMEUSA (`1%`) — con số to bị câu phụ đề đâm ngang
qua giữa.

**Gốc:** trong `Cinematic.tsx` có HAI lớp vẽ **hoàn toàn độc lập**, không lớp nào biết lớp kia ở đâu:
- lớp HOOK, biến thể neo đáy: `padding-bottom: 300px` → khối chữ trải tới **y≈1620**
- lớp PHỤ ĐỀ: `bottom: 520` → băng chữ nằm ở **y≈1200-1400**

Bố cục hook chọn bằng **băm `(stat + line) % 4`** → **đúng 1/4 số video** rơi vào biến thể hỏng.
Đó là lý do lúc thấy lúc không, và vì sao QC không bắt: video vẫn "sạch, chữ đọc rõ" nên Vision chấm
80+ (đúng bài học mục qc_structure). Kiểm chứng bằng chính hàm băm: cả hai mẫu anh chụp đều ra v=2.

**Vá 3 lớp:**
1. `Cinematic.tsx`: **chia băng cố định** — hằng số `CAP_TOP` ép mọi biến thể hook nằm TRỌN phía trên
   băng phụ đề (chừa 260px cho phụ đề 2-3 dòng). Vẫn giữ đủ 4 bố cục để không lặp mô-típ.
2. `selftest.py` — `t_bo_cuc_khong_chong`: đọc thẳng hai con số trong `Cinematic.tsx` và bắt buộc
   `CAP_TOP >= bottom_phụ_đề + 260`. Ai sửa lùi lại là **FAIL ngay tại selftest**, không phải chờ
   thấy video xấu rồi mới biết.
3. `find_overlap_videos.py`: chép **nguyên si** hàm băm của TSX, soi kịch bản đã lưu của từng job
   `done` để tìm ĐÚNG video dính rồi xếp hàng render lại qua `new_render_request` (dựng lại từ kịch
   bản — **không tốn một lượt gọi AI nào**). Bật bằng `wipe_queue.yml -f fix_overlap=true`.
   KHÔNG render lại tràn lan: 3/4 số video vốn không sao.

**Luật:** hai lớp đồ hoạ chồng lên nhau mà toạ độ khai báo rời rạc thì sớm muộn cũng đâm nhau.
Phải có **hằng số băng dùng chung** + một bài kiểm chốt bằng số. Mắt người soi vài video không thay
được phép tính — nhất là khi lỗi chỉ xuất hiện ở 1/4 trường hợp.

### 7.am — Chia việc TĨNH: 17 máy ngồi không chờ 1 máy (24/8/2026, anh chỉ ra)

**Đo thật phiên 11:00Z:** 18/19 job xong từ lâu, còn **đúng một** luồng `WHYUSA` chạy **1h53**.
→ 17 máy đứng im gần một tiếng, mà khoá concurrency của GitHub còn bắt **phiên kế nằm chờ** luồng
chậm nhất. Kênh dư (`50 kênh còn việc > 18 slot`) thì bị đẩy sang "phiên sau" dù máy đang rảnh.

**Gốc:** mỗi luồng nhận **CỨNG** một kênh rồi thôi — đây là *chia việc tĩnh* (static partitioning),
mà tải mỗi kênh chênh nhau tới 5-6 lần. Cách chữa chuẩn là **hàng chờ + luồng tự lấy việc kế**
(work stealing): ai xong trước thì lấy tiếp, không ai đợi ai.

**Vá:**
- `dat_hang_cho()` — plan để phần kênh dư vào **một doc** hàng chờ (thay vì vứt sang phiên sau).
- `lay_viec_ke()` — luồng xong việc thì lấy kênh kế bằng **GIAO DỊCH Firestore nguyên tử**. Không có
  giao dịch thì hai máy cùng đọc rồi cùng ghi → **render trùng kênh**, tốn đôi quota AI lẫn chỗ kho.
- Ngân sách thời gian `LANE_BUDGET_MIN` (mặc định 130') — chừa biên trước cap 165' để luồng không bị
  cắt ngang giữa một video.
- Có test `t_hang_cho_nguyen_tu` trong selftest.

**Hệ quả:** số kênh làm được trong một phiên giờ phụ thuộc **thời gian còn lại**, không còn bị chặn
cứng ở 18. Máy rảnh biến thành video thay vì thành thời gian chết.

**Luật:** chia việc tĩnh chỉ đúng khi mọi phần việc nặng như nhau. Hễ tải lệch nhau là phải chuyển
sang hàng chờ — và mọi phép lấy việc dùng chung đều phải NGUYÊN TỬ, nếu không sẽ làm trùng.

**Bổ sung 7.am — ba lớp chống chồng chéo của hàng chờ.** Máy chạy độc lập nên "ai xong trước lấy
tiếp" chỉ an toàn khi việc lấy KHÔNG thể trùng:
1. **Rời nhau từ gốc** — 18 kênh vào mẻ và phần dư vào hàng chờ là hai tập KHÔNG giao nhau.
2. **Lấy nguyên tử** — `lay_viec_ke()` dùng giao dịch Firestore; hai máy cùng gọi thì mỗi kênh chỉ
   về tay đúng một máy. Không có giao dịch: hai máy cùng đọc rồi cùng ghi → render trùng kênh.
3. **Sổ trong luồng** — mỗi luồng nhớ kênh mình đã làm, gặp lại thì bỏ qua (chống ca luồng chết giữa
   chừng rồi kênh được xếp lại).
Cộng với `LANE_BUDGET_MIN` (130'), luồng không bao giờ bị cap 165' cắt ngang giữa một video.

### 7.an — Sàn 20s không chỉ dính PULSE (24/8/2026)

Log phiên 11:00Z: QC chặn `quá ngắn` ở **ba** format — pulse (12.8s ×8, 15.1s ×3), **doc** (10.6s),
**scaled** (19.1s — hụt đúng 0,9 giây, vứt cả video đã render xong).
→ Đã thêm `keo_du_dai()` dùng chung và áp cho `build_doc_props`. Bản LONG không bị đụng tới vì luôn
dài hơn sàn (hàm tự no-op) — khỏi phải đoán long/short từ `prefix`, đoán sai là bỏ sót hoặc kéo nhầm.

**CHƯA áp cho 8 format trộn-một-track** (scaled/ranked/mapped/thennow/swarm/clockwork/longshot/guess)
và lý do phải nói rõ: các format đó ghép **một** track audio với mốc thời gian CỐ ĐỊNH
(`_mix_track(clips, total, track)`). Cộng thời lượng vào giữa sẽ **lệch tiếng khỏi hình** — lỗi nặng
hơn nhiều so với một short bị loại. Cách đúng là làm như đã làm với PULSE: đo trước → cộng vào thời
lượng → RỒI mới đặt mốc clip. Việc này phải sửa từng builder và cần nhìn video thật để nghiệm thu,
nên để lại làm ban ngày thay vì vá mù lúc 3h sáng.

### 7.ao — GUESS: mở đầu nhàm, kết thúc MÀN HÌNH ĐEN (24/8/2026, anh chỉ ra)

**Đo trong `GuessShort.tsx`:**
- **Mở đầu** (1,6s): chỉ có emoji 🤔 + tiêu đề trên nền gradient tối — **không một khung hình thật nào**.
  Giây đầu là chỗ YouTube tính giữ chân gắt nhất mà lại là chỗ nhàm nhất.
- **Kết thúc**: `calcGuess` cộng `tail = 1.2s` vào tổng thời lượng nhưng **KHÔNG có Sequence nào vẽ
  đoạn đó** → hết vòng cuối là còn trơ nền `#0a0c14`. Đúng thứ luật "cấm khung cuối đen" đã cấm, mà
  lọt vì không ai soi tới giây chót.

**Vá — tận dụng ảnh ĐÃ TẢI, 0 lượt tải/quota thêm:**
- Mở đầu mượn ảnh **vòng 1** làm nền (mờ 13px, tối 0.42, phóng nhẹ theo spring) → có chuyển động và
  hình thật ngay giây đầu. Không có ảnh thì vẫn lùi về gradient như cũ.
- Thêm **thẻ kết** thật: nền là ảnh **vòng cuối**, "HOW MANY DID YOU GET?" + "n/n ? COMMENT BELOW 👇"
  + "▶ FOLLOW @handle". Đuôi nâng 1,2s → **2,4s** cho kịp đọc và bấm theo dõi.
- Kiểm cú pháp bằng esbuild cho **cả 51 file .tsx** trước khi push.

**Luật:** thời lượng có cộng thêm đuôi thì phải có **cảnh vẽ cho đuôi đó**. Cộng giây mà không vẽ =
tặng người xem một màn hình đen đúng lúc họ quyết định có theo dõi hay không.

### 7.ap — "Đếm sai": ba phép đo, và cái sai là con số TÔI từng báo (24/8/2026)

Đo ba đường độc lập:
| Đường đo | Kết quả |
|---|---|
| Sổ đếm lượt đẩy kho `__pushed__.total` | **1.305** |
| Bản ghi job `status=done` ở B | **644** (tổng job 772) |
| Dung lượng kho 57,7 GB ÷ ~44MB/video | **~1.343** |

Đường 1 và 3 khớp nhau (lệch 3%). Đường 2 thấp vì sổ job bị reset 23/8 **và** các phiên failover ghi
job sang B2. Phân rã: `1.305 = 414 (mốc dựng lại 23/8) + 496 (23/8) + 395 (24/8)` — cộng đúng, không
có dấu hiệu cộng trùng.

**Kết luận: sổ đếm KHÔNG sai. Con số 414 tôi từng báo mới là con số sai** — nó là kết quả của
`rebuild_stats.py` đếm bản ghi job SAU khi sổ vừa bị reset, tức đếm phần sống sót chứ không phải
phần có thật trong kho.

**Cái thật sự hỏng là số NHẢY LUNG TUNG:** `count_pushed` ghi qua `_db_jobs()`, mà hàm này khi
failover trả về **B2** — cả phiên khẩn sổ cộng vào B2 trong khi dashboard đọc B → số **đứng im** suốt
phiên rồi **nhảy vọt** lúc rót ngược.
→ Vá: sổ đếm **luôn ghi thẳng vào B** (`_db_B_that()`), vì failover là do cạn hạn mức ĐỌC còn ghi vào
B vẫn được. Một nguồn duy nhất, số tăng đều theo thời gian thực, và bỏ được đường rót ngược — vốn là
chỗ dễ cộng trùng nhất vì nó cộng `Increment` từ một bản sao.

**Luật:** ba ô số trên một màn hình mà đo ba thứ khác nhau thì người xem sẽ luôn thấy "sai". Trước
khi kết luận số hỏng, phải đo ĐỘC LẬP ít nhất hai đường và nói rõ mỗi ô đang đo cái gì.

### 7.aq — Dọn rác mà KHÔNG được xoá nhầm

`wipe_queue.py` xoá SẠCH kho — đúng cho lúc làm lại từ đầu, **sai** cho yêu cầu "giữ video hoàn hảo,
chỉ dọn rác". Thêm `find_junk.py`: nhận diện rác theo **từng loại có bằng chứng**, mặc định chỉ đếm.

| Loại | Bằng chứng để gọi là rác | Xử lý |
|---|---|---|
| 1 | tên chứa `.new.` / `.tmp` / `.part` | bỏ thùng rác |
| 2 | trùng tên y hệt cùng thư mục | giữ bản mới nhất, bỏ phần còn lại |
| 3 | `.jpg`/`.json` mà không có `.mp4` cùng gốc | bỏ thùng rác |
| 4 | `.mp4` < 300KB | bỏ thùng rác |
| 5 | `.mp4` thiếu CẢ `.json` lẫn `.jpg` | **KHÔNG xoá** — chỉ liệt kê để dựng lại phần phụ |

Ba chốt an toàn: (a) mặc định `--dry-run`; (b) "xoá" = **bỏ vào thùng rác**, còn khôi phục được —
đổ thùng rác (xoá vĩnh viễn) **cố ý không nằm trong công cụ**; (c) không bao giờ đụng `.mp4` có đủ
`.json` + `.jpg`. Đọc kho qua gương ở B nên không tốn hạn mức project A.

**Bổ sung 7.aq — chạy khô bằng Drive GIẢ trước khi đụng kho thật.** `find_junk.py` bản đầu có **ba**
lỗi mà chỉ chạy khô mới lộ:
1. Đi theo đường `root/MM0-STORE/_QUEUE` trong khi `_QUEUE` là con **trực tiếp** của root → soi vào
   thư mục trống, báo "0 rác", tưởng kho sạch (đúng loại lỗi *chết câm*).
2. Gọi `child_folder()` thiếu `create=False` — hàm này **mặc định TẠO thư mục**, tức một công cụ
   chỉ-đọc lại đi tạo thư mục rỗng trong kho người dùng.
3. Một file vừa là "file tạm" vừa là "ảnh mồ côi" → **đếm hai lần** và nằm hai lần trong danh sách xoá.
→ Nay quét đệ quy thẳng từ root (chỉ đọc), và mỗi file chỉ được xếp vào **đúng một loại**.
Bài chạy khô dùng Drive giả (0 mạng) kiểm đủ 5 loại + xác nhận video hoàn hảo KHÔNG bị đụng.

**Luật:** công cụ xoá file thì bài kiểm phải chạy TRƯỚC lần chạy thật đầu tiên. Số báo cáo sai một
lần là mất niềm tin, mà với công cụ dọn kho thì niềm tin là tất cả.

### 7.ar — B và B2: giả định gốc SAI, và cách dẹp chuyện "đổ thừa cho nhau" (24/8/2026)

Anh nói: *"cứ đổ thừa B với B2 cho nhau, không đồng bộ được thì dẹp một cái đi"*. Soi lại thì đúng là
kiến trúc sai từ giả định gốc:

> Firestore có hạn mức **ĐỌC** và **GHI** tách riêng (50K đọc · 20K ghi mỗi ngày).
> Failover sang B2 gần như **luôn** kích hoạt vì cạn hạn mức **ĐỌC** — lúc đó **ghi vào B vẫn tốt**
> (đo thật: pipeline ghi ~800 lượt/phiên, còn xa trần 20K).

Nhưng `_db_jobs()` trả B2 cho **cả đọc lẫn ghi**. Hệ quả dây chuyền:
dữ liệu sống (job · số đếm · chủ đề) **chẻ làm đôi** → dashboard đọc B thấy thiếu → phải có đường
"rót ngược" B2→B → rót ngược cộng `Increment` từ một **bản sao** → lệch số.
**Mọi con số sai tối nay đều mọc ra từ đúng chỗ này.**

**Sửa gốc — không dẹp B2, mà lấy lại đúng vai của nó:**
- **B là nguồn GHI duy nhất** (`_db_ghi()` = luôn B). 10 lệnh ghi đã chuyển hết.
- **B2 chỉ để ĐỌC** khi B cạn hạn mức đọc. Không còn hai bản ghi thì không còn gì để lệch.
- **Bỏ `render_stats/{owner}` khỏi danh sách rót ngược** — chính hàm gương CHÉP doc này B→B2, rót
  ngược lại cộng bản sao đó vào B ⇒ **số đếm mỗi kênh nhân đôi sau mỗi vòng gương-rồi-rót**.
  Chép một chiều rồi cộng ngược chiều kia là sai từ ý tưởng.
- Chốt bằng bài `t_b2_chi_doc` trong selftest: còn lệnh ghi nào đi qua `_db_jobs()` là **FAIL**.

**Luật:** khi một hệ có bản chính và bản dự phòng, phải định nghĩa rõ **ai được GHI**. Cho cả hai
cùng ghi thì không phải "đồng bộ" — đó là hai sự thật, và rồi sẽ phải chọn tin cái nào.

### 7.as — Vì sao "tối ưu" mãi vẫn vỡ, và bức tường thay cho lời hứa (24/8/2026)

**Con số nói hết:** sổ `_cr()` của pipeline báo **1.302** lượt đọc, trong khi project B đã dùng
**>50.000** (vỡ trần, phải failover). **Sổ chỉ nhìn thấy ~3% sự thật** — vì `_cr()` chỉ đếm ở chỗ
*có ai đó nhớ gắn vào*. Mỗi lần thêm code là thêm một lối đọc không ai đếm.

> **Tối ưu = GIẢM mức tiêu thụ. Nó không bao giờ tạo ra một BỨC TƯỜNG.**
> Hứa "sẽ tiết kiệm" thì lần sau vẫn vỡ. Phải có trần mà code **không thể** vượt và **không thể quên gắn**.

**Bốn phần, làm xong hôm nay:**
1. `_stream_at()` **tự tính tiền** theo **số doc THẬT** trả về — mọi lời gọi qua nó tự vào sổ, không
   cần nhớ. (Trước đây các con số trong `_cr("...", 70)` là **ước lượng**, mà pool key đã lên 220.)
2. **29 câu lệnh đọc** còn lại được gắn sổ (dò bằng AST để chèn đúng đầu câu lệnh, không phá cú pháp).
3. `nap_nen_ngan_sach()` — đọc số **CẢ HỆ** đã tiêu hôm nay (18 luồng + dashboard cùng cộng vào một
   doc). Thiếu bước này thì mỗi luồng chỉ thấy phần mình (~1.300) và **tưởng còn dư 97%**, trong khi
   18 luồng cộng lại đã chạm trần. Đây chính là chỗ khiến "mỗi người tối ưu một mảnh mà tổng vẫn vỡ".
4. `con_ngan_sach()` là **bức tường**: việc **PHỤ** (gương, tự chữa, quét vét, thống kê) dừng ở **70%**
   trần; việc **THIẾT YẾU** (ghi kết quả job, sổ đếm) chạy tới cùng — *thà cạn quota còn hơn mất video
   đã render*.

**Và chốt để không tái phát:** `selftest.t_khong_tron_so` quét mọi lệnh `.stream(` trong
`firestore_bridge.py`; lệnh nào không gắn sổ và không đi qua `_stream_at` là **FAIL ngay**, chặn phiên.
Tức từ nay **không thể** thêm một lối đọc trốn sổ mà vẫn push được.

**Luật:** kỷ luật con người không giữ được hạn mức. Chỉ có hai thứ giữ được: **đếm ở tầng thấp nhất**
(để không ai quên) và **một bài kiểm chặn build** (để không ai thêm lối mới).

**Bổ sung 7.as — chèn sổ TỰ ĐỘNG phải soi lại từng chỗ.** Bản chèn bằng AST gắn đúng vị trí cú pháp
nhưng **sai con số** ở hai chỗ, và cả hai đều nguy:
- `_count_jobs` ghi **200** trong khi `count()` là truy vấn **TỔNG HỢP, tốn ~1 lượt** dù bảng bao nhiêu
  doc. Plan gọi ~110 lần ⇒ **22.000 lượt ma = 44% trần ngay ở bước plan** ⇒ tường bật nhầm, tắt hết
  việc phụ dù thực tế mới dùng 1%. (Con số 200 chỉ đúng cho **nhánh lùi** đếm thô.)
- Chèn thêm `_cr` ngay trong chính `_stream_at`, cộng đôi với phần `_tinh()` đã đếm theo số doc thật.

Đo lại sau khi sửa: một phiên plan điển hình = **831 lượt đọc (1% trần)**, việc phụ vẫn chạy.

**Luật:** công cụ sinh code tự động chỉ bảo đảm **đúng cú pháp**, không bảo đảm **đúng ngữ nghĩa**.
Sổ ghi sai còn tệ hơn không có sổ — vì nó làm bức tường bật nhầm và tắt việc thật.

### 7.at — Chuyển kho NÓNG sang Cloudflare D1 (24/8/2026, anh chốt "làm đi")

**Con số, không nói chung chung:**
| | ĐỌC/ngày | GHI/ngày | Dung lượng |
|---|---|---|---|
| Firestore free | 50.000 | 20.000 | 1 GB |
| **Cloudflare D1 free** | **5.000.000** | **100.000** | **5 GB** |
| Hơn | **100×** | **5×** | 5× |

→ **ĐỌC hết lo** (đây là chỗ đang vỡ: B chạm >50.000). **GHI chỉ hơn 5×** — đo thật ~800 ghi/phiên ×
20 phiên = 16.000/ngày, Firestore 20.000 là sát nút, D1 100.000 là thoải mái **nhưng không vô hạn**.

**Nói rõ cái D1 KHÔNG giải quyết:** nó đếm **SỐ DÒNG ĐỌC**. Truy vấn không trúng index mà quét cả
bảng vẫn tốn đúng bấy nhiêu dòng — y như Firestore đếm doc. Hết lo là nhờ 100× **cộng với** index
đúng, chứ không phải cứ đổi kho là xong. Vì thế 3 index đã đánh sẵn theo đúng 3 truy vấn nóng.

**Đã dựng xong:** DB `mm0-hot` (5 bảng) · Worker `/api/hot` · secret `HOT_KEY` · client `hot_db.py`.

**Chống lặp lại sự cố B/B2 — bốn chốt:**
1. **Một cửa duy nhất**: mọi lời gọi qua Worker với **danh sách lệnh CÓ TÊN**, KHÔNG nhận SQL tự do.
   Đã thử: gửi `DROP TABLE render_job` → *"lệnh không có trong danh sách cho phép"*.
2. **Một chủ ghi mỗi bảng**, ghi rõ ngay trong schema.
3. **Chuyển DẦN**: mặc định chế độ **`shadow`** — ghi cả hai nơi, **ĐỌC vẫn từ Firestore**. Chạy vài
   ngày, đối chiếu số hai bên rồi mới bật `HOT_MODE=on`. Không bao giờ tự nhảy sang `on`.
4. **Hỏng thì lùi êm**: D1 lỗi → `hot_db` nuốt lỗi, hụt 20 lần thì **tự tắt cả phiên**, việc chính
   chạy tiếp bằng Firestore.

Đã thử thật: sai khoá → từ chối · SQL tự do → từ chối · ghi rồi đếm → đúng · **3 máy tranh 2 việc
trong hàng chờ → A, B, rỗng — không trùng**.

**Bẫy dính ngay lần gọi đầu:** thiếu `User-Agent` thì **Cloudflare chặn ở cổng với mã 1010**, trả
**403 y hệt sai khoá** nên rất dễ chẩn nhầm. Đúng cái bẫy đã dính với DVIDS sáng nay.
→ Luật: mọi client HTTP tự viết phải gửi `User-Agent`; và 403 **không** đương nhiên là lỗi xác thực.

**Bổ sung 7.at — bản ghi bóng phải ĐỦ TRƯỜNG mới đối chiếu được.** `update_job(job_id, **patch)`
không nhận `channel` lẫn `type`, nên bản ghi sang D1 có `vtype` rỗng → lệnh `dem_xong` (đếm long/short)
luôn trả 0 và **việc đối chiếu hai bên thành vô nghĩa** — tức chạy chế độ bóng cả tuần cũng không
kết luận được gì. Nay `new_job` nhớ hộ cả kênh lẫn loại (`_JOB_CH` + `_JOB_TY`).

**Luật:** chạy song song để đối chiếu thì bản phụ phải ghi ĐỦ trường dùng cho phép so. Bản phụ thiếu
trường không phải "gần đúng" — nó là **không có dữ liệu**, mà lại trông như đang chạy tốt.

### 7.au — Chuyển số đếm sang D1 và cắt phụ thuộc B/B2 (24/8/2026)

**Anh chốt: làm dứt điểm, đừng để mai quên.** Đã làm, theo đúng thứ tự an toàn:

1. **Chép trước, bật sau.** Bật đọc từ D1 khi kho còn rỗng thì `count_done` trả 0 cho mọi kênh →
   hệ tưởng chưa làm gì → **render dư hàng loạt** và vỡ luật 1:3. Nên chép 772 job từ B sang D1 trước.
2. **Đối chiếu rồi mới tin:** 80 nhóm kênh/loại · Firestore **644** — D1 **644** · **0 nhóm lệch**.
3. Bật `HOT_MODE=on` ở cả 4 bước workflow.

**Điểm phải thiết kế lại, không chuyển 1-1 được:** đo thật mỗi lời gọi Worker ~**0,22s** (D1 vùng
APAC, runner ở Mỹ). Plan cần ~110 số đếm ⇒ gọi lẻ là **~33 giây chỉ để đếm, chậm hơn cả Firestore**.
Và **Worker free chỉ 100.000 lượt/ngày** ⇒ gọi lẻ thì 30 phiên/ngày **vỡ trần Worker (111%)** trong
khi D1 mới dùng vài phần trăm.
> **Trần thật nằm ở Worker, không phải D1.** Nên `dem_tat_ca` gộp mọi kênh vào **một** `GROUP BY`
> (đo 0,20s) + đệm 90s. 110 lời gọi → 1.

**Hai bẫy dính ngay khi làm, ghi lại kẻo quên:**
- Thiếu `User-Agent` → Cloudflare chặn **mã 1010**, trả **403 y hệt sai khoá**.
- Thiếu `x-hot-key` trong `Access-Control-Allow-Headers` → preflight chặn, trình duyệt báo
  **"Failed to fetch"** — trông như mất mạng, không hề giống lỗi quyền.
> Cả hai đều là **403/lỗi mạng giả dạng**. Luật: gặp 403 đừng vội kết luận sai khoá.

**Đã xoay khoá `HOT_KEY`** sau khi backfill, vì khoá cũ có đi qua trình duyệt. Đã kiểm: khoá mới
chạy, khoá cũ trả *"sai khoá"*.

**Còn lại để gỡ B2 (chưa làm, có lý do):** đợi 1-2 phiên chạy thật với `HOT_MODE=on` xác nhận số
đếm đúng, rồi mới xoá gương + rót ngược + B2. Xoá cùng lúc với bật là mất đường lùi.

### 7.av — Đếm ĐÚNG: bỏ cộng dồn, đếm lại từ bản ghi (24/8/2026)

**Gốc của "số nhảy tùm lum":** `__pushed__` là bộ đếm **CỘNG DỒN** bằng `Increment`. Kiểu đó sai được
theo **hai chiều** và **không bao giờ tự sửa**:
- cộng **thiếu** khi lượt ghi rơi (quota chết, `_soft` nuốt) → số thấp hơn thực tế;
- cộng **thừa** khi rót ngược từ bản sao B2 → số cao hơn thực tế;
- và một khi đã lệch thì **lệch vĩnh viễn**, vì không có gì để đối chiếu lại.

→ Nay đếm **thẳng từ bảng `render_job` trên D1**: *"video có thật" = `status='done'` VÀ có `drive_id`*.
Sai lệch **không tích luỹ được**, vì mỗi lần hỏi là một lần **đếm lại từ sự thật**.
Dashboard đọc qua cổng `/api/hot-stat` — **cổng CHỈ-ĐỌC-SỐ, không cần `HOT_KEY`**: nhét khoá ghi vào
trình duyệt là ai mở trang cũng đọc được khoá của cả kho nóng, hạ cấp bảo mật để lấy một con số thì
không đáng. Cổng này chỉ chạy phép ĐẾM, không trả về một dòng dữ liệu nào.

### 7.aw — Job MA: bản ghi nói dối "đang chạy"

**Đo được:** 75 bản ghi kẹt ở `rendering`/`writing`/`qc`/`ratelimited`, cái **mới nhất cũng đã im
11 TIẾNG**. Chúng làm ô "⚙️ Đang chạy" sai và khiến người nhìn không biết tin số nào.
→ `don_job_ma()`: quá **6 giờ** im lặng thì đổi sang `failed`. Ngưỡng 6h an toàn vì một phiên dài
nhất bị GitHub cắt ở **165 phút**. **KHÔNG xoá** — chỉ thôi nói dối, vẫn giữ để soi nguyên nhân.
Chạy tự động đầu mỗi phiên.

**Kết quả ngay:** 71 bản ghi được dọn. Sổ giờ là `done 644 · failed 124 · ratelimited 4` — và
`dangchay` về **0**, khớp với thực tế (phiên đang chạy còn ghi ở Firestore, chưa sang D1).

**Luật:** số đo bằng cách **cộng dồn** thì sai lệch tích luỹ và không sửa được. Số đo bằng cách
**đếm lại từ bản ghi** thì mỗi lần hỏi là một lần tự sửa. Chọn kiểu thứ hai bất cứ khi nào có thể.

### 7.ax — DOC ID BỊ FIRESTORE CẤM: lối tối ưu chưa từng chạy ngày nào (24/8/2026)

Lộ ra khi chạy thật `find_junk.py`: B2 ném
`400 Resource id "__snap__" is invalid because it is reserved`.

**Firestore CẤM doc id khớp mẫu `__...__`** (bọc kín hai đầu — dành riêng cho hệ thống).
`connections_mirror/__snap__` mang đúng dạng đó, nên **chưa từng ghi được ngày nào**. Lượt ghi đi qua
`_soft` nên **lỗi bị nuốt**, lượt đọc trả rỗng.

**Hậu quả — đây chính là thứ tôi đi tìm suốt đêm:** lối "1 lượt đọc" (gói danh sách kho vào 1 doc)
**không bao giờ tồn tại**, nên mọi luồng đều rơi xuống lối **quét 73 doc trên project A**, mỗi 30 phút,
× 18 luồng. Tôi đã đổ cho `mirror_connections_to_b` hỏng, cho A cạn, cho vòng xoáy tự siết — **đều là
triệu chứng**. Gốc nằm ở một cái tên.

**Hai cái tôi tự thêm tối nay cũng dính y hệt** — `render_stats/__drive_usage__` và
`counters/__enqueue_sweep__`: viết xong, tưởng chạy, thực ra chưa bao giờ ghi được. Nghĩa là đệm
`drive_usage` và mốc "quét vét 6h/lần" đều vô hiệu.

**Vá:** đổi tên → `snap_kho` · `drive_usage_cache` · `enqueue_sweep`.
**Chốt:** `selftest.t_id_khong_cam` quét mọi `.document("...")` trong 6 file, gặp dạng `__...__` là FAIL.
Lưu ý `__snap__{owner}` / `__cool__{owner}` / `__pushed__{owner}` **HỢP LỆ** (không kết thúc bằng `__`)
— bản thay hàng loạt suýt sửa nhầm hai dòng lọc đó, phải trả lại.

**Luật:** `_soft` (ghi mềm, nuốt lỗi) là con dao hai lưỡi — nó cứu pipeline khỏi chết vì quota, nhưng
cũng **giấu luôn lỗi cấu hình vĩnh viễn**. Mọi thứ đi qua `_soft` phải có bài kiểm TĨNH, vì nó sẽ
không bao giờ tự la lên.

### 7.ay — Soi & dọn rác kho khi CẢ A LẪN B đều cạn (24/8/2026)

`find_junk.py` chạy trong CI lấy danh sách kho từ Firestore → **A và B đều 429** → chết ngay bước đầu,
không quét nổi một file. Nhưng Worker có **bản sao thẻ kết nối trong KV** (dựng 23/8 để chống đúng
cảnh này), và **KV thì liệt kê được** → có đường đi trọn vẹn **không hỏi Firestore một câu nào**.

→ Thêm `/api/junk-list` (lấy 72 kho từ KV) + `/api/junk-scan` (quét đệ quy 1 kho, phân loại, tuỳ chọn dọn).

**KẾT QUẢ THẬT — 72/72 kho · 3.534 file:**
| Loại | Số | |
|---|---|---|
| 1 · file tạm | **0** | |
| 2 · trùng tên y hệt | **18** | giữ bản mới nhất |
| 3 · ảnh/sidecar mồ côi | **4** | |
| 4 · video hỏng <300KB | **0** | |
| 5 · video thiếu phần phụ | **2** | **KHÔNG xoá** — chỉ liệt kê |

**Kho sạch hơn tưởng nhiều: rác chỉ 0,6%** (22/3.534), nằm ở 6/72 kho.
Đã dọn đủ 22 file → **bỏ vào THÙNG RÁC, không xoá vĩnh viễn**. Kiểm lại 3 kho: rác về 0, số file tốt
không suy suyển. Xoá vĩnh viễn (đổ thùng rác) **cố ý không nằm trong công cụ** — đó là việc của anh.

**Luật:** trước khi kết luận "kho đầy rác", phải ĐẾM. Ở đây nỗi lo là 100% còn thực tế là 0,6% — nếu
tin cảm giác mà `wipe_queue` cả kho thì mất trắng 3.512 file tốt.

### 7.az — PULSE: composition BỎ QUA thời lượng Python đo → lệch tiếng-hình 4,7 giây (24/8/2026)

**Triệu chứng ban đầu:** phiên 13:08Z có **24 video PULSE bị QC loại "quá ngắn"** (10,6 / 12,8 / 15,1s),
tăng gấp đôi so với phiên trước, **dù bản vá kéo dài đã chạy** (log có 3 dòng `⏱ PULSE ... -> 21.0s`).

**Gốc:** `PulseShort.tsx` **không hề đọc `it.dur`** — nó dùng cứng **2,2 giây mỗi mục** và
**1,7 / 1,6** cho intro/outro. Nên mọi cố gắng kéo dài bên Python đều **vô hiệu**: độ dài luôn là
`1,7 + n×2,2 + 1,6` → 4-5 mục là 12-15 giây, dưới sàn QC 20s.

**Và đây mới là phần nặng:** track tiếng được ghép theo **mốc THẬT của giọng đọc**, còn hình chuyển
theo **2,2s cố định**. Tính trên một ví dụ 5 mục: tới mục cuối, **hình chuyển ở 10,5s trong khi
tiếng đọc tới đó ở 15,2s — lệch 4,7 GIÂY**. Lỗi này có **từ đầu**, chưa ai thấy, vì QC chỉ đo độ dài
và độ sáng chứ **không đo khớp tiếng-hình**.

**Vá:** `idur()` ưu tiên `it.dur`; `calcPulse` và component lấy `introSec`/`outroSec` từ props;
`build_pulse_props` truyền hai mốc đó sang. Cùng một ví dụ: **14,3s → 20,6s** và tiếng-hình khớp.

**Luật:** khi Python đo một đằng còn composition tính một nẻo, **im lặng là triệu chứng nguy hiểm
nhất** — video vẫn ra, vẫn đẹp, chỉ là tiếng lệch hình. Mọi thời lượng phải có **một nguồn duy nhất**,
và bên vẽ phải ĐỌC nó chứ không tự đoán.

### 7.ba — Gộp lệnh ghi D1: cứu trần WORKER, không phải trần D1 (24/8/2026, anh đề xuất)

**Phải nhìn HAI trần, không phải một:**
| | Trần free/ngày |
|---|---|
| D1 — số **DÒNG GHI** | 100.000 |
| Worker — số **LƯỢT GỌI** | 100.000 ← **chật hơn**, vì mọi đường vào D1 đều qua đây |

**Gộp KHÔNG làm giảm số DÒNG ghi vào D1** (vẫn ngần ấy dòng) — nó cứu **trần Worker**. Đo thật
122 video/phiên × ~4 lượt ghi/job × 20 phiên:

| Cách | Lượt gọi/ngày | % trần Worker |
|---|---|---|
| không gộp | 9.760 | 9% |
| **gộp 20/lượt** | **488** | **0,5%** — rẻ hơn **20 lần** |

**Quy tắc xả:** đủ **20 mục** HOẶC quá **120 giây**, cái nào tới trước → dashboard trễ nhiều nhất
2 phút, vẫn trực quan. **Trạng thái CUỐI (`done`/`failed`) xả NGAY**, không nằm đệm — đó là con số
người ta nhìn để biết có mất video không, trễ nó là mất ý nghĩa.
`xa_het()` gọi cuối luồng: **thiếu bước này là mất các lượt ghi còn trong đệm**.

Có test `t_gop_ghi_d1` chốt cả ba điều kiện: gộp có ăn · done/failed xả ngay · không sót mục nào.

**Luật:** khi thêm một lớp trung gian (Worker), trần MỚI của hệ là trần chật nhất trong chuỗi —
không phải trần của kho dữ liệu phía sau. Đo cả chuỗi trước khi ăn mừng "100× hạn mức".

### 7.bb — Đã fix được bao nhiêu, và cái gì VẪN phải đợi reset (24/8/2026)

**Đo trạng thái thật lúc 15:09Z** (log publish, nhờ `chan_doan_429` mới):
`⛔ Project A cạn hạn mức — ngừng thử lại 30 phút. Project khác KHÔNG bị ảnh hưởng.` ·
`⚠️ A cạn — bỏ qua settings/overrides, chạy bằng mặc định.` · `gương connections ở B cũng 429`.
→ **A và B đều đang cạn.** Hai bản vá đêm nay hoạt động đúng như thiết kế (đệm âm không lây sang
project khác; thiếu doc cấu hình vẫn chạy tiếp), nhưng **chúng không hoàn lại được hạn mức đã tiêu**.

**Đã thoát khỏi Firestore (chạy được ngay cả khi A/B cạn):**
đếm video · trạng thái job · sổ ngân sách · hàng chờ kênh *(D1)* · danh sách kho Drive + soi/dọn rác
*(Worker + KV)*.

**CÒN phụ thuộc — và đây là lý do publish vẫn nằm im:**
**token YouTube chỉ có ở project A.** Drive đã có bản sao trong KV từ 23/8, **YouTube thì chưa ai làm**
— nên A cạn là khâu đăng bài chết cứng cho tới lúc reset, dù render vẫn chạy và video vẫn lên kho đều.
→ Vá: `ytCtx` nay ghi/đọc bản sao KV y như `driveCtx`. **Có hiệu lực từ lần kết nối kế tiếp** (KV được
nạp khi đọc Firestore THÀNH CÔNG), tức từ sau mốc reset. Hôm nay vẫn phải đợi.

**Trả lời thẳng: CHƯA fix 100%.** Các nguồn lãng phí đã bịt (sẽ thấy hiệu quả trên hạn mức MỚI),
nhưng hạn mức HÔM NAY đã tiêu rồi — không có cách nào hoàn lại. Publish chạy lại khi A reset.

**Luật:** phân biệt "đã bịt chỗ rò" với "đã đầy lại bình". Bịt rò không hoàn lại phần đã mất; báo cáo
gộp hai thứ đó làm một là báo cáo sai.

### 7.bc — Project C: quả bom ĐÃ NỔ SẴN, chưa ai nhìn tới (24/8/2026)

`auto_enqueue` quét **TOÀN BỘ** `yt_queue` mỗi lượt, **không giới hạn**:
```
for d in q_db.collection("yt_queue").where("owner","==",owner).stream()
```
Mà `yt_queue` **chỉ phình**: xếp lịch thì nhanh, còn đăng bị **YouTube chặn ở ~6 video/ngày**.

| Ngày | Mục trong hàng đợi | Lượt đọc C/ngày | % trần |
|---|---|---|---|
| **hôm nay** | 644 | **61.824** | **123%** ← đã vỡ |
| +7 | 2.044 | 196.224 | 392% |
| +30 | 6.644 | 637.824 | 1275% |

→ Vá: chỉ lấy mục **CHƯA ĐĂNG** (`pending`/`processing`/`scheduled`) + `limit(2000)`. Số mục chưa
đăng luôn nhỏ (bị chính trần YouTube giữ lại) nên truy vấn **không phình theo kho**. Video đã đăng
vẫn không bị xếp lại nhờ cờ `queued` trên `render_job` — chốt thứ hai.
**61.824 → ~4.000 lượt (8%).**

**Dự báo ngày mai sau khi bịt hết:** A **26%** · B **22%** · C **8%** · B2 **1%**.

**Luật:** truy vấn nào quét một bảng **chỉ có tăng** thì sớm muộn cũng vỡ — không phải "nếu" mà là
"khi nào". Mọi `.stream()` không `limit` trên bảng tích luỹ đều là bom hẹn giờ; phải lọc theo trạng
thái ĐANG hoạt động, không phải theo chủ sở hữu.

### 7.bd — Tài khoản Cloudflare: bốn đồng hồ riêng, cái chật nhất là KV GHI (24/8/2026)

Anh hỏi "ngoài D1 còn xài gì, có bị khấu trừ không". **Không trừ lẫn nhau** — mỗi dịch vụ một đồng hồ
riêng. Nhưng mỗi cái có trần riêng, và **cái chật nhất không phải D1**:

| Dịch vụ | Trần free/ngày | Đang dùng | % |
|---|---|---|---|
| Workers (mm0-connect) | 100.000 lượt gọi | ~500-2.000 | 0,5-2% |
| D1 đọc | 5.000.000 dòng | ~432.000 | 8,6% |
| D1 ghi | 100.000 dòng | ~8.000 | 8% |
| KV đọc | 100.000 lượt | ~2.000 | 2% |
| **KV GHI** | **1.000 lượt** | ⚠️ | **chật nhất 100 lần** |

**KHÔNG nằm trên tài khoản này:** Workers AI vẽ ảnh FLUX — 52 key `cf:` thuộc **các tài khoản
Cloudflare khác**, mỗi cái có 10.000 neuron riêng. Việc vẽ ảnh không ăn vào hạn mức Worker/D1.

**Chỗ suýt vỡ:** `driveCtx`/`ytCtx` `put()` KV **mỗi lần** đọc Firestore thành công. Mỗi tấm
thumbnail trên dashboard là một lượt gọi → tải một trang thư viện 40 ảnh có thể tốn **40 lượt ghi KV**.
Vài lần mở trang là chạm trần 1.000, rồi bản sao thẻ kết nối **ngừng cập nhật** — đúng lúc cần nhất
(khi Firestore cạn) thì nó lại là bản cũ.
→ `kvPutKhacNhau()`: **đọc trước, giống thì thôi ghi**. Đổi 1 lượt ghi (trần 1.000) lấy 1 lượt đọc
(trần 100.000) — **rẻ hơn 100 lần**. Thẻ kết nối gần như không đổi nên hầu hết lượt sẽ không ghi.

**Luật:** trong một nhà cung cấp có nhiều dịch vụ, phải liệt kê **TỪNG đồng hồ** rồi tìm cái chật nhất.
Nhìn mỗi con số to nhất (5 triệu dòng D1) rồi yên tâm là cách chắc chắn nhất để vỡ ở chỗ khác.

### 7.be — 26 VIDEO KHÔNG ĐẨY ĐƯỢC KHO: A và B cạn cùng lúc (24/8/2026)

**Bắt được lúc đang chạy, không phải qua log:** soi D1 thấy 26 job `status=done` mà **không có
`drive_id`**, và bước đều ghi *"chưa đẩy Drive"* (13 long · 11 short · 3 khác).

**Gốc:** `pool_accounts` lấy danh sách kho theo 3 đường Firestore — A (cạn) → gương ở B (cạn) →
B2 (gương cũ, rỗng) → **trắng tay** → `enqueue` hiểu là *"không có kho nào"* → video ở lại trong
artifact, không lên kho. Phiên 13:08Z đẩy được 122 video vì lúc đó B chưa cạn; tới 14:54Z thì cả hai
đã hết.

**Vá — lớp cứu cuối không đụng Firestore:** Worker có bản sao thẻ kết nối trong **KV**, và KV liệt kê
được. Thêm `/api/drive-pool` trả đúng những trường `pool_accounts` cần. Đo thật: **72 tài khoản, đủ
`root` + `creds`**, lấy được khi ép tắt cả 3 đường Firestore.

**Vì sao đáng nhớ:** cùng một bản sao KV này đã cứu khâu **soi rác** vài giờ trước, mà tôi **không
nghĩ tới việc nó cũng cứu được khâu ĐẨY KHO** — đường sống đã có sẵn, chỉ chưa nối. Bài học: khi
dựng một đường vòng, phải hỏi ngay *"còn chỗ nào khác đang chết vì cùng lý do?"*.

**Luật:** dữ liệu SỐNG CÒN phải có ít nhất một đường đọc **không nằm cùng nhà cung cấp** với đường
chính. Ba đường mà cùng là Firestore thì đó là **một** đường, không phải ba.

### 7.bf — Ba mức ưu tiên của bức tường quota, và đệm bài tính theo NGÀY (24/8/2026)

**Lỗi tôi tự gây khi dựng bức tường:** xếp `heal_unpushed` vào nhóm "việc phụ" nên nó bị hoãn từ 70%
trần. SAI hoàn toàn — đó là hàm **cứu những video đã render xong nhưng chưa đẩy được kho** (đo hôm
nay: 36 cái). Hoãn nó vì tiếc vài trăm lượt đọc là đánh đổi ngược: mất công render cả tiếng để tiết
kiệm 0,8% hạn mức.
→ Ba mức, xếp theo **hậu quả nếu KHÔNG chạy**:
| Mức | Không chạy thì mất gì | Chạy tới |
|---|---|---|
| `thiet_yeu` | video ĐANG làm | luôn luôn |
| `cuu_du_lieu` | video ĐÃ LÀM XONG | **92%** |
| còn lại | vài con số thống kê | 70% |

**Đệm bài đo bằng NGÀY, không phải số video thô** (anh chốt: *"kênh nào sắp hết video lên lịch thì
tự động ưu tiên, và nên chia đều"*). Kênh nhịp 4 video/ngày tồn 28 cái = còn **7 ngày**; kênh nhịp
1 video/ngày tồn 28 cái = còn **28 ngày** — cùng con số nhưng mức đói khác hẳn.
→ Sắp kênh theo **số ngày còn bài, ít nhất trước**; kênh đã đủ `NGAY_DEM` (mặc định **7 ngày**, đúng
kế hoạch dựng đệm một tuần trước khi đăng) thì **ngưng làm thêm**, nhường máy cho kênh đói.

**Đường lấy kho Drive — 6 lớp, kiểm KHÔNG SÓT KHÔNG CHỒNG CHÉO:**
đệm tiến trình → gói 1-doc ở B/B2 → quét A → gương ở B → gương ở B2 → **🆘 KV của Worker**.
Mỗi lớp `return` ngay khi có kết quả nên không lớp nào chạy hai lần. Đo thật: gọi 3 lần liên tiếp khi
Firestore tắt hết → **72 kho mỗi lần · 0 tên trùng · KV chỉ bị gọi 1 lần** (2 lần sau ăn đệm).

**Tăng trần KV bằng cách DỜI KHỎI KV:** KV free chỉ **1.000 lượt ghi/ngày**, không nới được nếu không
trả tiền. D1 cho **100.000** — gấp **100 lần**, mà đã có sẵn. Nên bộ nhớ đệm thẻ kết nối nay **ghi vào
D1** (bảng `the_ket_noi`), KV chỉ còn làm lớp đọc thứ hai cho dữ liệu cũ.
**Luật:** gặp trần chật thì hỏi "có dịch vụ nào khác trong tay làm được việc này với trần rộng hơn
không" trước khi nghĩ tới việc trả tiền.

### 7.bg — TÔI HIỂU SAI: 55 kênh trên 55 TÀI KHOẢN, không phải 1 tài khoản 37 dự án (24/8/2026)

**Tôi đã cảnh báo sai.** Tôi tưởng tình huống là *một* tài khoản Google tạo 37 dự án để nhân hạn mức
cho chính mình — đó mới là lách hạn mức và đúng là rủi ro.

**Thực tế:** anh có **~72 tài khoản Google riêng** (bằng chứng ngay trong hệ: 72 kho Drive tên khác
nhau, mỗi cái 15GB riêng). Mỗi kênh YouTube nằm trên tài khoản riêng của nó. Nên **mỗi tài khoản tự
tạo dự án Cloud của MÌNH, dùng hạn mức của MÌNH, cho kênh của MÌNH** — giống hệt chuyện 72 kho Drive,
không ai gọi đó là lách.

| | Video/ngày |
|---|---|
| 6 kênh đang nối × 6 | 36 |
| 55 kênh × 6 | **330** — thừa cho nhịp 220 |

→ **Không cần xin nâng hạn mức, không cần lách gì.**

**Nhưng code chưa cho làm đúng như vậy:** `startAuth` **xoay vòng round-robin** khi có nhiều client,
nên kênh A có thể bị nối bằng dự án của tài khoản B → hai kênh ăn chung một bình 6 lượt trong khi bình
của A ngồi không. Đã thêm `?client=<id|số thứ tự>` để chỉ định đúng dự án lúc nối kênh; không chỉ
định thì vẫn xoay vòng như cũ.

**Luật:** trước khi cảnh báo về chính sách, phải xác minh **cấu trúc tài sản thật của người dùng**.
Cùng một hành động — "nhiều dự án Cloud" — là lách nếu một tài khoản nhân bản cho chính nó, và là
bình thường nếu mỗi tài khoản dùng phần của nó. Tôi đã kết luận trước khi hỏi, và làm anh lo vô cớ.

### 7.bh — Rải kho Drive: băm tên kênh CỐ ĐỊNH nên 37/72 kho không ai chạm tới (24/8/2026)

Anh hỏi *"đã rải đều các kho chưa, dồn một kho có bị chặn không"*. Có rải, nhưng rải **lệch**.

**Cách cũ:** `ranked_accounts` sắp kho theo dung lượng trống rồi **xoay danh sách theo băm TÊN KÊNH**.
Băm cố định ⇒ mỗi kênh **luôn** bắt đầu ở đúng một vị trí, đời đời không đổi.

**Đo bằng số:** 55 kênh chỉ rơi vào **35 vị trí trong 72** → **37 kho không kênh nào chạm tới**.
Số liệu thật khớp: kho nhiều nhất **119** file · kho ít nhất (khác 0) **18** · chênh **6,6 lần** ·
**3 kho còn nguyên 0 file** (token vẫn tốt, chỉ là không ai chọn tới).

**Vá:** xoay theo **băm tên kênh CỘNG bộ đếm lượt đẩy**. Vẫn giữ phần băm-theo-kênh (đó là lý do gốc
của seed: 18 luồng song song không cùng đâm vào một kho tại cùng thời điểm), nhưng mỗi lượt đẩy nhích
một bước nên cùng một kênh cũng rải ra nhiều kho.

| Mô phỏng 55 kênh × 20 video | Kho được dùng | Nhiều nhất | Ít nhất |
|---|---|---|---|
| Cũ | **35/72** | 80 | 20 |
| Mới | **72/72** | 21 | 11 |

**Về câu "đầy thì bị chặn không":** không. `ranked_accounts` lọc `free >= need_bytes` nên kho đầy bị
bỏ qua, và `DRIVE_SAFETY_PCT` dừng render khi tổng kho đạt 90%. Hiện mới **57,7/1080 GB = 5%** — còn
rất xa. Nhưng rải lệch vẫn đáng sửa: nó làm vài kho đầy sớm trong khi 37 kho ngồi không.

**Luật:** băm để "rải đều" chỉ đều khi khoá băm có **nhiều giá trị hơn số chỗ**. Băm một tập cố định
55 tên vào 72 chỗ thì mãi mãi chỉ chạm được ~35 chỗ — phải trộn thêm thứ THAY ĐỔI theo từng lượt.

### 7.bi — Đăng bài phải LIỀN MẠCH: long đi cùng short của chính nó (24/8/2026, anh chỉ ra)

**Hai thiếu sót anh phát hiện, cả hai đều có thật:**

**1. Thứ tự đăng gần như NGẪU NHIÊN.** Truy vấn `status==done AND queued==False` **không có
`order_by`** → Firestore trả theo thứ tự ID doc. Hôm nay lấy một short ở tận cuối kho, mai lấy cái ở
giữa — kênh nhìn vào không có mạch nào.
→ Vá: `order_by("created_at", ASCENDING)` = đăng theo đúng thứ tự làm ra, cũ nhất trước.

**2. Long và short trong ngày KHÔNG cùng một bài.** Luật 1 long : 3 short được ép ở khâu **RENDER**,
nhưng tới khâu **ĐĂNG** chúng là 4 bản ghi rời rạc → dễ thành *long chủ đề A + 3 short chủ đề B, C, D*.
Người xem bấm short thấy hay, đi tìm bản dài thì không có — **mất trọn ý đồ "short kéo người về long"**.
→ Vá: `new_job` ghi thêm `cha` (id của long sinh ra short) + `thu_tu`; `auto_enqueue` xếp
**LONG trước, ngay sau là các short mang `cha` = long đó** theo đúng `thu_tu`. Short mồ côi (format
chỉ-short, hoặc video cũ chưa có trường này) giữ thứ tự thời gian ở cuối.
Đã kiểm bằng ví dụ 7 bản ghi trộn lẫn → ra đúng `L1 · S1a · S1b · L2 · S2a · S1c · Sx`.

**Lỗi tôi tự tạo khi vá, bắt được bằng bài kiểm tĩnh:** bản đầu gán `cha=ljob` cho cả nhánh format
**CHỈ-SHORT** (guess/mapped/ranked…) — nơi `ljob` không tồn tại → **NameError giết cả luồng ngay video
đầu tiên**. Phát hiện nhờ quét "biến dùng mà chưa gán trong cùng hàm", không phải nhờ chạy thử.

**Trả lời câu "hết quota thì sao":** code đã đúng sẵn — không bỏ video, không báo lỗi giả.
`⏸ hết quota — dừng đăng hôm nay, phần còn lại để ngày mai` và video giữ nguyên `status=pending`,
`note=quota_wait`; lượt cron ngày hôm sau tự lấy lại. Lịch **giãn ra**, không mất bài nào.

### 7.bj — "Tổng cộng dồn 1343" là SỔ CỘNG DỒN, không phải số video trong kho (24/8/2026, anh chỉ ra)
`render_stats/__pushed__{owner}.total` cộng bằng `Increment(1)` mỗi lượt đẩy kho thành công và
**không có đường nào trừ**. Ba việc bình thường đều làm nó phồng: render lại (bản cũ vào thùng rác,
bản mới +1 ⇒ 1 video đếm 2 lần), dọn rác `find_junk --don`, xoá tay trên Drive. Nên con số đúng
nghĩa đen của nó (số lượt render thành công từ trước tới nay) nhưng SAI với thứ người vận hành muốn
biết. **LUẬT: một con số hiển thị phải SUY RA TỪ SỰ THẬT HIỆN TẠI, không cộng dồn theo sự kiện — vì
sự kiện chỉ có chiều lên, kho thì có cả chiều xuống.** Nguồn sự thật duy nhất của "video trong kho"
= danh sách `.mp4` chưa vào thùng rác trên Drive. Công cụ: `kiem_kho.py` (đi hết kho, đối chiếu
`render_jobs.drive_id`, GHI ĐÈ sổ bằng `set`, và **xoá bản ghi job trỏ vào file đã mất** — nếu không
`count_done()` tưởng kênh còn đủ video rồi ngừng làm). Kho nào đọc hụt thì TỰ TẮT chế độ ghi (đọc
thiếu mà ghi đè = tự hạ sổ xuống số sai). Chốt bằng `t_so_kho_lay_tu_drive`.

### 7.bk — Vá `.tsx` KHÔNG sửa được video đã render; "dọn rác" và "làm mới" là hai việc khác nhau (24/8/2026)
Anh: *"kêu dọn xoá rồi mà sao vẫn còn"*. Vá engine chỉ đổi cách dựng của các phiên SAU; video trong
kho là `.mp4` đã đóng gói. `find_junk.py` cũng không đụng vì với nó file đó "đủ .mp4 + .json + .jpg"
= video TỐT. Phải tách bạch:
* **DỌN RÁC** — file hỏng/thừa ⇒ bỏ thùng rác, không dựng lại (`find_junk.py`).
* **LÀM MỚI** — file vẫn chạy nhưng dựng bằng engine CŨ ⇒ phải render lại (`render_lai_cu.py`, có
  BẢNG MỐC VÁ: kênh dùng motif nào + đẩy kho trước giờ commit vá nào thì dính). Dựng lại từ kịch bản
  đã lưu nên **không tốn lượt gọi AI**; bản cũ vào thùng rác sau khi bản mới xong.

### 7.bl — Facebook có trần RIÊNG, và hết nhịp FB đang bị tính là "hỏng" ⇒ vứt video (24/8/2026)
Anh hỏi *"đăng facebook có ảnh hưởng quota ko"*. Trả lời: **không** — FB không dùng chung 10.000
đơn vị/ngày của YouTube, cũng không đụng Firestore. Nhưng nó có trần riêng (mã 4 app · 17 user ·
32 page · 613 rate limit · Reels có trần bài/ngày mỗi Page) và trước bản vá hệ KHÔNG nhận ra:
(1) `upload()` thấy Reels lỗi liền quay về đăng video thường ⇒ gọi thêm một lượt nữa vào đúng Page
đang bị chặn; (2) `publish_social` đếm 3 lần lỗi là dán `failed` ⇒ **video bị bỏ luôn**, đúng cái bẫy
đã vá cho Instagram mà FB thì chưa. Nay `_soi()` đọc header `X-App-Usage` (cảnh báo từ 80%) và ném
`HetNhip` riêng; tầng trên hoãn sang cron sau, KHÔNG cộng `attempts`. Chốt bằng
`t_fb_het_nhip_khong_giet_video`.

### 7.bm — "Kênh không còn (đã xóa)" là LỜI KHAI SAI của một lệnh đọc hỏng (24/8/2026 tối, phiên 16:06Z)
Lane HAULUSA và FAKEUSA thoát sau 60 giây với `⚠️ Kênh ... không còn (đã xóa) — bỏ`, trong khi plan
vừa xếp việc cho chính hai kênh đó vài giây trước. Hai lỗi chồng nhau, cùng họ với luật "chết câm":
1. `read_one_channel` gọi `.stream(timeout=20)` **trực tiếp**, không qua `_stream_at` — nên vẫn dính
   đúng lỗi thư viện `'_UnaryStreamMultiCallable' object has no attribute '_retry'` mà `_stream_at`
   sinh ra để đỡ. **Vá một lỗi ở một chỗ không có nghĩa là đã vá cả họ: phải quét mọi lối đọc.**
2. `except Exception: return None` — biến một lệnh đọc HỎNG thành một SỰ THẬT SAI ("kênh không tồn
   tại"). Người gọi tin lời đó rồi bỏ nguyên một lane (~2 tiếng máy); ở vòng lặp giữa phiên còn tệ
   hơn: kết liễu một lane **đang ra video**.
**LUẬT: hàm đọc phải phân biệt "không tìm thấy" với "không đọc được".** Nay `read_one_channel` ném
`FB.DocLoi` khi đọc hỏng; `None` chỉ còn đúng một nghĩa. Đầu lane: thử lại 3 lần rồi dừng với thông
báo đúng bản chất. Giữa vòng lặp: giữ cấu hình vòng trước, làm tiếp. Chốt bằng `t_doc_hong_khac_kenh_bi_xoa`.

### 7.bn — Render lại LONG đang dùng SAI ENGINE cho mọi kênh không phải DATARACE (24/8/2026 tối)
Anh hỏi *"kịch bản có dùng để render lại được ko"* — soi ra ba lỗ, hai cái nặng:
* Nhánh xử lý yêu cầu 🔄 gọi **cứng** `DS.make_long` (long biểu đồ đua cột) cho MỌI kênh. Bấm render
  lại một long doc/toon/motif là thay video đúng định dạng bằng video **sai hẳn định dạng** — mà bản
  cũ đã bị bỏ thùng rác ngay sau đó. Nay chia đường đúng như `run_one`: toon → `make_toon_long`;
  doc + mọi motif → `make_doc_long`; còn lại → `make_long`.
* Long **doc/motif** chỉ lưu `[p["topic"] for p in parts]` — mấy cái TÊN chủ đề, không phải kịch bản.
  `make_doc_long(resume=…)` cần `parts` là danh sách **story dict** và cần thêm `subs`; thiếu thì
  resume bị cắt về 0 phần ⇒ viết mới bằng Gemini, tốn quota đúng việc lẽ ra miễn phí.
* Long **toon** không lưu kịch bản **gì cả** ⇒ mất trắng, làm lại phải viết từ đầu.
Nay cả ba đường đi qua `_ks_long(plan, parts)` lưu đủ `pillar_title · hook · sources · subs · parts`
(story dict thật). Chỉ long DATARACE (`races`) và mọi SHORT là đã lưu đủ từ trước.
Chốt bằng `t_render_lai_long_dung_engine`.

### 7.bo — 9/9 định dạng SHORT không có phụ đề, dù mốc karaoke đã có sẵn (24/8/2026 tối, anh yêu cầu)
`subs` nằm trong khai báo props của mọi component short nhưng **không lớp nào vẽ**, còn phía Python
thì mọi builder viết `du, _, _ = TK.synth(...)` — vứt thẳng mốc từng từ mà edge-tts đã trả sẵn. Người
xem tắt tiếng (phần lớn lượt xem đầu trên feed) không đọc được chữ nào. Vá:
* `tts_karaoke.subs_tu_clips(clips)` — ghép mốc của cả track từ chính danh sách `[(mp3, giây_bắt_đầu)]`
  mà builder đã dựng để trộn tiếng. **Dùng lại đúng nguồn của tiếng thì không thể lệch offset**, và mỗi
  builder chỉ thêm MỘT dòng.
* `engine-remotion/src/Karaoke.tsx` — băng chữ dùng chung, `BOTTOM = 200` (nằm TRÊN mọi thứ neo đáy
  của 8 short, chỗ thấp nhất chúng dùng là 150) và tối đa 7 từ/cụm ⇒ không bao giờ cao quá 2 dòng.
  Đặt chỗ CỐ ĐỊNH chứ không tuỳ hứng từng file — đúng bài học "chữ chồng chéo".
Chốt bằng `t_short_co_phu_de_karaoke`.

### 7.bp — Chỉ 2/9 format có lưới "đủ dài"; 7 format còn lại rơi dưới sàn QC là mất trắng (24/8/2026 tối)
Độ dài mọi short = TỔNG ĐỘ DÀI GIỌNG ĐỌC. `keo_du_dai()` chỉ dùng được cho doc, PULSE thì tự lo bằng
đoạn code riêng; bảy motif còn lại không có lưới nào — log 11:00Z có ca `scaled 19.1s`, **vứt cả video
vì hụt 0,9 giây** (mất một lượt viết AI + một lượt render). Nay tất cả đi qua
`keo_du_dai_track(items, clips, introSec, outroSec)`. Hai chỗ dễ sai đã chốt bằng test:
* **Kéo dài `dur` thì phải DỰNG LẠI mốc đặt tiếng.** Quên bước này chính là lỗi PULSE lệch tiếng-hình
  4,7 giây. Hàm dựng lại toàn bộ `clips` từ độ dài mới, không chỉ sửa `dur`.
* **Làm tròn phải LÊN.** `dur` lưu 2 số lẻ; làm tròn xuống ra 20,98s — vẫn dưới sàn 21s, vẫn mất video
  vì 2 phần trăm giây.
Hình dạng `clips` không khớp (`n*moi_muc + 2`) thì **để nguyên, không đoán** — thà video ngắn còn hơn
video lệch tiếng. Chốt bằng `t_short_khong_qua_ngan`.

### 7.bq — Mở đầu và kết thúc SHORT là hai quãng chết (24/8/2026 tối, anh chỉ ra)
Đo trước khi sửa: trong `introSec` giây đầu, 7 component short chỉ hiện MỘT chip tiêu đề nhỏ trên nền
gradient — nội dung thật (gauge/bản đồ/bậc thang) mãi hết intro mới chạy. `outroSec` giây cuối thì mọi
Sequence đã hết, màn hình **đứng ở khung cuối cùng**. Không đen kịt, nhưng chết đúng hai chỗ quyết
định: giây đầu (giữ chân) và nút theo dõi (chuyển đổi). `engine-remotion/src/Bookend.tsx` = thẻ mở
(tên kênh + tiêu đề bung theo spring + vệt sáng quét) và thẻ kết (CTA + handle đập nhẹ), **tự đọc
`durationInFrames`** nên mỗi component chỉ thêm một dòng — không tính lại mốc thì không đẻ ra lỗi lệch
mốc. Màu lấy từ `accent` của chính kênh nên không bị đồng phục. GUESS giữ thẻ riêng (ảnh vòng 1 + KetCard).

### 7.br — Vá đúng bệnh nhưng SAI FILE: 3 builder vẫn lệch tiếng suốt (24/8/2026 tối)
Bản vá "truyền mốc THẬT sang composition" hôm nay ghi chú *"thiếu hai dòng này thì PulseShort dùng
cứng 1,7/1,6"* — nhưng lại nằm trong `build_ranked_props`. Kết quả: swarm, **pulse** và longshot vẫn
không truyền `introSec`/`outroSec`, composition dùng số cứng trong khi giọng dài khác hẳn ⇒ hình lệch
tiếng, đúng cái bệnh tưởng đã vá. **LUẬT: sửa xong phải ĐẾM số chỗ đã sửa trên TOÀN BỘ họ hàm, đừng
tin vào một lần sửa.** Nay 9/9 builder truyền mốc thật, chốt bằng `t_moc_intro_outro_that` (đếm ≥9).

### 7.bs — Shard cạn hạn mức bị xử như "cấu hình sai" ⇒ đổ hết sang project A (24/8/2026 tối)
`firestore_state._sa_client()` ping thử database lúc tạo client; ping hỏng thì trả `None` và **mọi
lệnh của shard đó rơi về project A**. Nhánh này đúng cho lỗi cấu hình, nhưng SAI hoàn toàn khi lỗi là
`429 Quota exceeded`: project vẫn đúng, client vẫn dùng được, chỉ là hết lượt hôm nay — vậy mà B cạn
lại kéo A cạn theo, đúng cái vòng luẩn quẩn mà kiến trúc 3-project sinh ra để chặn (log phiên 16:06Z:
14 dòng `-> fallback Project A` trong MỘT lane). Nay tách hai nhánh: 429 ⇒ **giữ client, KHÔNG rơi về
A**, để tầng trên retry / lật gương B2; lỗi khác mới fallback như cũ.
**LUẬT: "không gọi được" và "hết lượt" là hai chuyện khác nhau — đừng gộp vào một nhánh except.**
(Cùng họ với 7.bm: đọc hỏng ≠ dữ liệu không tồn tại.)

### 7.bt — Cảnh báo lặp lại mọi phiên mà KHÔNG đường nào xử: `#shorts` (24/8/2026 tối)
Mọi phiên đều in `⚠️ Short nên có #shorts để YouTube phân loại đúng` — cảnh báo đúng, nhưng
`autotitle` chỉ thêm thẻ khi nó TỰ đặt lại tiêu đề, còn video có sẵn tiêu đề từ Gemini thì đi thẳng
qua. Thiếu thẻ này YouTube có thể xếp video dọc vào luồng thường ⇒ mất hẳn kênh phân phối Shorts.
Nay thêm ngay trong `enqueue_drive` — chỗ DUY NHẤT mọi đường đẩy kho đi qua.
**LUẬT: một cảnh báo lặp lại mỗi phiên mà không ai xử thì nó không còn là cảnh báo, nó là lỗi.**

### 7.bu — Bước cứu "quá ngắn" lại đẩy video vào lỗi "nhàm" (24/8/2026 tối)
`keo_du_dai` rải đều số giây thiếu cho mọi cảnh. Nhưng QC ngay bên dưới chặn *"cảnh giữ một ảnh quá
3,5s (nhàm)"* — cảnh chỉ có 1 ảnh mà cộng thêm giây thì thành đứng hình lâu hơn. Nay rải **cân theo
SỐ ẢNH** của từng cảnh: cảnh nhiều ảnh thêm giây = thêm nhát cắt, cảnh một ảnh thêm ít thôi. Và bỏ
trần 2,5s/cảnh ở vòng hai khi ít cảnh quá — video hơi chậm còn xem được, video bị QC vứt thì mất
trắng cả lượt viết AI lẫn lượt render. Chốt bằng `t_doc_du_dai_va_khong_nham`.

### 7.bv — Ghim phiên bản mới làm ở ĐÚNG MỘT workflow, 13 cái còn lại vẫn hở (24/8/2026 tối)
`constraints.txt` sinh ra sau sự cố gương chết 16 tiếng (`'_UnaryStreamMultiCallable' object has no
attribute '_retry'` — thư viện Google ra bản mới làm gãy `.stream(timeout=…)`). Nhưng soi lại: chỉ
`render_cron.yml` dùng nó, còn **publish · publish_social · stats · health_guardian · trend_scout ·
migrate · seed_channels · thumb_requests · fix_queue_thumbnails · wipe_queue** vẫn cài "bản mới nhất
tại thời điểm chạy". Nghĩa là khâu ĐĂNG BÀI có thể vớ đúng bản hỏng vào bất kỳ ngày nào, mà mã nguồn
thì không đổi một dòng — loại sự cố không thể suy luận được. `requirements.txt` cũng chỉ có SÀN
(`>=2.16`), không có TRẦN. Nay: requirements.txt ghim cả sàn lẫn trần (mọi workflow cài `-r` đều được
che), các lệnh cài rời đi qua `-c render-pipeline/constraints.txt`. Chốt bằng
`t_moi_workflow_deu_ghim_thu_vien` — test QUÉT cả thư mục workflow, nên workflow mới thêm mà quên ghim
là selftest chặn ngay.
**LUẬT: vá một lỗi thì phải quét TOÀN BỘ chỗ có cùng hình dạng, và để lại một test biết tự quét** —
bài học lặp lại lần thứ ba trong đêm (7.bm dòng đọc, 7.br mốc intro/outro, giờ là ghim thư viện).

### 7.bw — Cạn NGÀY: mỗi nhà cung cấp reset ở một múi giờ, đang gộp làm một (24/8/2026 tối)
Log phiên 16:06Z: `429 rate limit daily (cloudflare): ... daily free allocation of 10,000 neurons`.
`_muc_nghi()` xếp đúng loại (cạn NGÀY, không phải chặn theo phút) nhưng cho nghỉ tới **00:00 giờ Thái
Bình Dương** — mốc của Google. Cloudflare Workers AI reset **00:00 UTC**, nên key cạn lúc 16:00 UTC bị
treo tới 07:00 UTC hôm sau trong khi nó đã hồi từ nửa đêm: **ném đi 7 tiếng của một key đã tốt trở
lại, mỗi ngày**. Nay nhận diện Cloudflare (`cloudflare`/`neuron`/`aierror`) → mốc UTC; Google giữ mốc
Thái Bình Dương; nhà cung cấp chưa có bằng chứng thì **không đoán**, giữ mốc cũ. Chốt bằng
`t_moc_reset_theo_nha_cung_cap` (kiểm cả khoảng lệch đúng 7 tiếng).

### 7.bx — Quét cả họ "đọc hỏng → khai rỗng": 37 chỗ, 3 chỗ gây hậu quả thật (24/8/2026 tối)
Sau 7.bm (kênh "đã xoá") em quét AST toàn bộ hai repo: **37 chỗ** `except Exception: return None/[]/{}`.
Đa số vô hại (việc phụ). Ba chỗ thì không:
* `recent_topics()` rỗng = nói với Gemini *"kênh này chưa làm gì cả"* ⇒ nó viết lại đúng đề tài tuần
  trước ⇒ **reused content** trên YouTube. Đây là sổ DUY NHẤT chặn trùng ý.
* `read_used_images()` rỗng = tắt hẳn chống trùng ảnh ⇒ nhiều video xài chung một tấm.
* `get_script_by_drive()` trả `None` khi ĐỌC HỎNG ⇒ render lại viết kịch bản MỚI, ra video **khác đề
  tài**, rồi bỏ bản cũ vào thùng rác. Người dùng bấm 🔄 mà **mất luôn video đang có**.
Hai cái đầu vẫn trả rỗng (thà làm còn hơn treo kênh) nhưng nay **HÉT LÊN** và ghi vào máy dò chết câm
(`dem_khau`) — cả phiên không đọc nổi lần nào thì đó là hỏng cấu hình, sẽ hiện 🚨 CHẾT CÂM. Cái thứ ba
ném `DocLoi`, đường render lại **hoãn yêu cầu sang lượt sau, không đụng bản cũ**.
Chốt bằng `t_so_hong_phai_het_len`.

### 7.by — Cùng một quyết định có HAI bản, bản kém hơn nằm ở đường quan trọng hơn (24/8/2026 tối)
Phạt key cạn hạn mức đang được quyết ở hai nơi khác nhau:
* đường VẼ ẢNH/VISION (`datastory_ci._muc_nghi`) — tính ĐÚNG số phút còn lại tới mốc reset;
* đường VIẾT (`key_manager`, **8 chỗ**) — con số **cứng 8 tiếng**.
8 tiếng là số đoán, và sai cả hai chiều: key Google cạn lúc 20:00 UTC (reset 07:00 UTC) hết phạt lúc
04:00 ⇒ **dội lại 3 tiếng trước khi nó hồi**, mỗi lượt hỏng vẫn bị trừ hạn mức; key Cloudflare cạn lúc
02:00 UTC (đã reset từ 00:00 UTC) bị **treo oan tới 10:00**. Nay tách `nghi_key.muc_nghi()` làm nguồn
duy nhất, cả hai đường import chung. Chốt bằng `t_mot_bang_phat_key_duy_nhat` — test so KẾT QUẢ hai
đường cho cùng 4 loại lỗi, nên bản sao mới lén mọc là fail ngay.
**LUẬT: một quyết định nghiệp vụ chỉ được có MỘT chỗ quyết. Thấy logic giống nhau ở hai file thì đó
không phải trùng lặp vô hại — sớm muộn hai bên lệch nhau, và bên lệch sẽ là bên ít ai đọc.**
(Cùng họ với `ten_chuan.py` tách ra chiều nay vì cùng lý do.)

### 7.bz — 18 lane, mỗi lane tự tông vào tường một lần mới biết B đã cạn (24/8/2026 tối)
Log phiên 16:06Z: **mỗi** lane có một dòng `🔀 FAILOVER: B chính nghẽn (read_config 429)` riêng. Nghĩa
là trạng thái "B cạn hạn mức ngày" — một sự thật CHUNG của cả phiên — đang được 18 tiến trình khám
phá lại 18 lần, mà **mỗi lượt hỏng vẫn bị trừ hạn mức**, cộng thêm vài vòng thử lại 1,5s. Nay lane đầu
tiên phát hiện thì ghi cờ `proj:B` vào **D1** (miễn phí, không đụng hạn mức Firestore) qua đúng đường
`key_nghi_ghi` đã có; `quota_pulse` ở đầu mỗi lane đọc cờ và **lật B2 thẳng**, không tốn lượt 429 nào.
Chốt bằng `t_bao_chung_b_can_han_muc`.
**LUẬT: cái gì đúng cho cả phiên thì phải phát hiện MỘT lần rồi chia sẻ, đừng để mỗi tiến trình tự
học lại bằng cách trả giá.** (D1 là chỗ chia sẻ đúng: rẻ, không nằm trong tài nguyên đang cạn.)

**Ghi chú số đo cần soi tiếp:** `📟 Sổ quota hôm nay: ĐỌC 9.631/50.000` trong khi B **đã** trả 429 —
tức sổ đang đếm THIẾU ~80% lượt đọc thật (dashboard/Worker, auto_enqueue bên repo publish, và lượt
gương B→B2 đều không vào sổ). Bức tường ngân sách vì thế không bao giờ chạm ngưỡng. Chưa vá đêm nay;
cách chắc chắn nhất là coi chính cú 429 là nguồn sự thật (đã làm ở 7.bz) thay vì tin con số ước lượng.

### 7.ca — Vá "mở đầu tẻ nhạt" suýt tạo lại đúng "chữ trên nền trơn" đang bị cấm (24/8/2026 tối)
Bản đầu của `Bookend.tsx` phủ thẻ hook lên `rgba(0,0,0,0.82→0.94)` — che kín nội dung bằng một nền
gần đen. Đó CHÍNH LÀ chữ ký mà `opening_is_flat()` chặn (đo thật: nền trơn = 91,9% tối · 342 màu;
ngưỡng `dark≥75 & colors<900`), và cũng chính là thứ anh cấm. Đặt thẻ hook lên rồi bịt hết phần hình
thì mở đầu **tệ hơn lúc chưa có thẻ**. Nay trần cứng `MAN_CHE = 0.5`: gauge/bản đồ/bậc thang bên dưới
vẫn hiện và vẫn đang chạy, chữ vẫn đọc rõ nhờ đổ bóng. Thẻ KẾT che dày hơn được (0,78) vì QC chỉ soi
khung MỞ ĐẦU và cuối video mục tiêu là đọc được CTA. Chốt bằng `t_the_mo_dau_khong_thanh_nen_tron`.
**LUẬT: mỗi lần thêm một lớp phủ toàn màn hình, phải hỏi lại nó có chạm ngưỡng QC nào không —
QC là luật đã viết ra để chặn chính mình, không phải chỉ để chặn Gemini.**

### 7.cb — GỐC THẬT của 2 lane mất trắng: gương B2 THIẾU kênh, không phải kênh bị xoá (24/8/2026 tối)
Truy tiếp 7.bm. Log phiên 16:06Z: plan liệt kê `PLAN channels=[... "HAULUSA" ... "FAKEUSA" ...]` — hai
kênh **vẫn tồn tại**. Nhưng B đã cạn hạn mức đọc từ TRƯỚC lúc plan chạy (`sync_keys A->B lỗi: 429`),
nên gương B→B2 không được làm tươi; lane lật sang gương **cũ 156 phút** và gương thiếu đúng hai kênh
đó ⇒ `read_one_channel` trả `None` ⇒ lane khai "đã xoá" rồi thoát. **Lệnh đọc KHÔNG hỏng, dữ liệu chỉ
THIẾU — nên `DocLoi` (7.bm) không đỡ được ca này.**
Vá: plan đã đọc đủ 50 kênh lúc nó còn đọc được, nên **gửi thẳng cấu hình xuống lane** (`out_channels`
nén gzip+base64 → output `cfgs` → env `CHANNEL_CFGS`; 50 kênh ≈ 3KB). `read_one_channel` không thấy
trong gương thì lấy từ gói đó và nói rõ "gương thiếu kênh này, KHÔNG phải bị xoá".
Chốt bằng `t_guong_thieu_kenh_khong_phai_bi_xoa`.
**LUẬT: dữ liệu đã đọc được ở thượng nguồn thì ĐƯA XUỐNG, đừng bắt hạ nguồn đọc lại từ một nguồn có
thể đã cũ hơn.** Ba biến thể của cùng một câu hỏi "không thấy nghĩa là gì" đã tốn 3 lần vá trong đêm:
đọc hỏng (7.bm) · dữ liệu thiếu (7.cb) · hết lượt (7.bs).

### 7.cc — Sao lưu kho key CHẾT MỌI PHIÊN, workflow vẫn xanh (24/8/2026 tối, phiên 17:56Z)
`backup_vault.py` ném `ModuleNotFoundError: No module named 'storage'` ở **mọi** phiên. Job `plan`
CÓ checkout repo publish — nhưng ở dòng 106, tức **SAU** bước "Sao lưu kho key" ở dòng 72. Bước gọi
có `|| true` nên workflow luôn xanh ⇒ **kho key coi như không được sao lưu suốt thời gian qua mà không
ai biết**. Đúng họ "chết câm", lần này ở tầng workflow chứ không phải tầng code.
Vá: checkout repo publish lên ĐẦU job (bỏ bản gated trùng ở dưới), và `backup_vault` bắt riêng
`ModuleNotFoundError` để **nói thẳng** thay vì để traceback trôi.
Chốt bằng `t_buoc_phu_that_bai_khong_duoc_im` — test kiểm **THỨ TỰ** (checkout phải đứng trước chỗ
dùng `AUTOPUBLISHER_SRC`), và đã thử ngược: đẩy checkout xuống sau thì test bắt đúng.
**LUẬT: `|| true` chỉ được dùng khi bước đó thật sự không quan trọng. Việc quan trọng mà nuốt lỗi thì
phải có người ĐẾM nó — không có ai đếm thì nó sẽ hỏng lặng lẽ hàng tháng.**

### 7.cd — Cờ "B cạn hạn mức" tự hạ hạn xuống 20 phút rồi ghi đè bản đúng (24/8/2026 tối)
Log phiên 17:56Z, ba dòng liên tiếp: `nghỉ tới 06:59Z` (đúng) → `nghỉ tới 18:33Z` → `nghỉ tới 18:35Z`.
Hai lỗi trong bản vá 7.bz vừa viết:
1. `muc_nghi()` phân loại theo NGUYÊN VĂN lỗi, mà chỗ gọi chỉ truyền mẩu tóm tắt `"read_config 429"` —
   không có chữ "per day" nên rơi vào nhánh "không rõ" = 20 phút. Failover sang B2 là hành động NẶNG,
   chỉ làm khi B đã nghẽn thật ⇒ mặc định đúng ở đây là CẠN NGÀY, trừ khi nguyên văn nói rõ theo phút.
2. Ghi sau đè ghi trước ⇒ một lần phân loại nhầm xoá sổ lần phân loại đúng. **Cờ chỉ được DÀI THÊM.**
**LUẬT: hàm phân loại theo nguyên văn lỗi thì chỗ gọi phải truyền NGUYÊN VĂN, đừng truyền mẩu tóm tắt
cho người khác đoán.** Và cờ chia sẻ giữa nhiều tiến trình phải theo quy tắc gộp một chiều (max), vì
thứ tự ghi giữa 18 tiến trình là không xác định.

### 7.ce — Bức tường ngân sách mù: sổ báo 9.631/50.000 trong khi B đã 429 (24/8/2026 tối)
Số đo tự tố cáo. `📟 Sổ quota hôm nay: ĐỌC 9.631/50.000` in ra ở hai phiên LIÊN TIẾP với **con số y
hệt**, trong khi B trả 429 (tức đã chạm 50.000). Hai lỗi cộng lại:
1. **Sổ sang trang lệch 7 tiếng.** Ngày đánh bằng `now(utc).strftime("%Y%m%d")` — lật lúc 00:00 UTC,
   trong khi hạn mức free reset 00:00 giờ Thái Bình Dương (07:00-08:00 UTC). Suốt khung 00:00→07:00
   UTC mỗi đêm, sổ báo "đã dùng 0" trong khi bình xăng vẫn gần cạn — **đúng khung giờ 18 luồng chạy
   mạnh nhất**. Nay dùng `_ngay_quota()` (UTC-7), cùng mốc với `nghi_key`.
2. **Project B có HAI cuốn sổ, hàm đọc chỉ lấy một.** Nhà máy render ghi
   `render_stats/__rw__{owner}`; khâu ĐĂNG ghi `quota/__rw__{ngày}` (`quota_guard._client("B")` trỏ
   đúng vào B). Mỗi cuốn thấy một nửa lưu lượng ⇒ tường không bao giờ chạm ngưỡng. Nay `read_rw_ledger`
   cộng cả hai (+1 lượt đọc/tiến trình, đổi lại con số nói thật).
Chốt bằng `t_so_quota_dung_ngay_va_gop_du`; đã thử ngược (lén đổi 1 chỗ về UTC → test bắt đúng).
**LUẬT: con số dùng để RA QUYẾT ĐỊNH mà đứng im hai phiên liên tiếp thì phải nghi nó hỏng, đừng nghi
hệ thống đang nhàn.** Và mốc "một ngày" phải khớp với mốc reset của nhà cung cấp, không phải UTC.

### 7.cf — Khâu ĐĂNG dội 112 lượt vào một lệnh đã biết chắc hỏng (24/8/2026 tối, publish 18:25Z)
Một lượt publish in ĐÚNG **112 dòng** `⚠️ gương connections ở B cũng lỗi: 429`. `_guong_connections()`
được gọi cho TỪNG kênh; cả A lẫn B đều cạn nên mỗi kênh lại đi hỏi B thêm một lần — 112 lượt đọc hỏng,
mà **lượt hỏng vẫn bị trừ hạn mức**, cộng mấy vòng `_retry` 1,5s mỗi lượt. Nay có `_GUONG_CHET` theo
loại: hỏng một lần là ngừng hỏi cho cả lượt chạy.
**LUẬT: cạn hạn mức là trạng thái của CẢ TIẾN TRÌNH, không phải của từng vòng lặp.** (Cùng họ 7.bz —
ở đó là chia sẻ giữa 18 lane, ở đây là trong một tiến trình.)

### 7.cg — `⛔ Project A cạn hạn mức` ×114, dòng tổng kết vẫn báo `đọc 0/50.000 (0%)` (24/8/2026 tối)
`quota_guard.da_dung()` đọc sổ hỏng thì trả 0 — "thà cho chạy còn hơn tự khoá mình". Cho chạy tiếp là
đúng, nhưng **báo 0% khi đã chạm trần là nói dối người vận hành**, và `du_suc()` còn mở cửa cho mọi
việc phụ đúng lúc project hết sạch. Đọc sổ hỏng **vì 429** chính là bằng chứng chắc nhất rằng project
đã cạn ⇒ ghi nhận `r = TRAN_DOC` + cờ `_can`, `bao_cao()` in "CẠN (429 — không đọc nổi sổ)". Lỗi khác
(mạng) vẫn giữ hành vi cũ. Chốt bằng `t_publish_khong_doi_vao_cho_da_chet`.
**LUẬT: khi không đo được, đừng báo 0 — hãy báo "không đo được", và nếu lý do KHÔNG đo được chính là
cái mình đang đo thì đó là câu trả lời.** (Lần thứ tư trong đêm: 7.bm · 7.bs · 7.ce · nay 7.cg.)

### 7.ch — PHẢN ÁP LỰC chưa từng chạy, mà log nhìn vẫn bình thường (24/8/2026 tối)
Soi log plan hai phiên liên tiếp (16:06Z, 17:56Z): **không có dòng `📦 Đệm bài`, cũng không có dòng
lỗi nào**. Vì `ton_kho()` trả `{}` êm ru nên cả khối `if _ton:` rơi thẳng qua — tính năng anh yêu cầu
("kênh nào sắp hết bài lên lịch thì tự động ưu tiên, chia đều") **chưa từng chạy một lần nào**.
Gốc: bảng `render_job` trên D1 ghi owner bằng `_OWNER_HINT[0]` — biến này khởi tạo **rỗng** và chỉ
được đặt trong `read_keys`/`new_job`. Tiến trình nào gọi `update_job` trước hai hàm đó ghi hàng loạt
bản ghi `owner=""`, trong khi `ton_kho(OWNER)` lọc theo owner THẬT ⇒ luôn rỗng. Nay có `_chu()`:
`owner truyền vào → _OWNER_HINT → env OWNER_UID`, tức luôn có giá trị, không phụ thuộc thứ tự gọi hàm.
Và tồn kho rỗng nay **in ra một dòng nói rõ phản áp lực không chạy** kèm chỗ cần soi.
Chốt bằng `t_phan_ap_luc_khong_im_lang`.
**LUẬT: `if <dữ liệu>:` bọc quanh một tính năng thì nhánh `else` PHẢI nói ra là tính năng đó không
chạy.** Một `if` không có `else` in log là một tính năng có thể chết âm thầm nhiều tháng — đây là lần
thứ hai trong đêm (lần trước: bước sao lưu kho key, 7.cc).

### 7.ci — "Lấy việc kế" viết ở `main()`, nhưng matrix chạy `channel_mode()` (24/8/2026 tối)
Đo được trong log mọi lane phiên 17:56Z: kết thúc bằng `⏱ DEBTUSA: còn 58' < ước tính 68'/mẻ → DỪNG`
rồi thoát — trong khi plan vừa xếp **32 kênh vào HÀNG CHỜ**. Dòng `♻️ Luồng rảnh -> nhận thêm kênh`
**chưa từng xuất hiện** trong bất kỳ log lane nào: vòng work-stealing được viết trong `main()`, còn
matrix chạy `run_render.py --channel X` tức vào `channel_mode()`. **Tính năng nằm ở đường vào KHÔNG
được dùng.** Giá phải trả: 18 lane × ~58 phút bỏ không mỗi phiên (~17 giờ máy), hàng chờ chỉ để đó.
Nay `channel_mode` có vòng lấy việc kế (giao dịch nguyên tử, trần theo `budget_s`/`HARD_S`, đọc danh
sách kênh CHỈ khi thật sự có việc để lấy, và ngã về gói `CHANNEL_CFGS` khi gương thiếu kênh).
Chốt bằng `t_lay_viec_ke_o_dung_duong_vao`.
**LUẬT: thêm tính năng vào một hàm thì phải kiểm nó có nằm trên ĐƯỜNG CHẠY THẬT không.** Cách kiểm rẻ
nhất: tìm dòng log đặc trưng của tính năng trong log phiên thật — không thấy dòng nào tức là chưa chạy,
đừng cho rằng "chắc nó chạy rồi". (Cùng họ 7.br: vá đúng bệnh nhưng sai file.)

### 7.cj — `❌ mở đầu NỀN TRƠN` lặp qua nhiều phiên: chữa SAU render là quá muộn (24/8/2026 tối)
7 ca ở phiên 16:06Z, 2 ca ở 17:56Z — mỗi ca mất TRẮNG một lượt viết AI + một lượt render (~2-4' CPU),
mà nguyên nhân chỉ là ĐỘ SÁNG của một tấm ảnh. `opening_is_flat()` soi video ĐÃ DỰNG nên phát hiện
đúng nhưng luôn muộn. Nay `sang_hoa_mo_dau()` chạy NGAY TRƯỚC lệnh render (cả 3 đường Cinematic:
`make_doc` · `render_short_from_props` · `make_doc_long`), dùng ĐÚNG thước đo mà QC sẽ dùng, chữa theo
bậc: ① tăng sáng + tương phản ảnh cảnh 0 → ② mượn ảnh sáng nhất của cảnh khác → ③ trả lý do để dừng
trước render.

**Bẫy bắt được lúc chạy thử, suýt biến bản vá thành gian lận:** tăng sáng ×2.1 kéo một tấm gần đen
(#0c0c10) xuống "2% tối" và **LỌT QC**, nhưng thứ ra màn hình là một mảng XÁM PHẲNG — qua mặt thước
đo chứ không làm video tốt hơn. Thước phân biệt là **ĐỘ BÃO HOÀ** (đo thật ghi ngay trong file này:
nền trơn sat 14,2 · ảnh thật chụp tối sat 31,1) ⇒ chỉ tăng sáng khi `sat ≥ 20`; dưới ngưỡng là nền
phẳng, đi thẳng sang bậc ②. Chốt bằng `t_cuu_mo_dau_khong_qua_mat_qc` (có ca kiểm file nền phẳng
KHÔNG bị ghi đè).
**LUẬT: khi tự động "chữa" một thứ mà QC đang chấm, phải chứng minh mình chữa CÁI THẬT chứ không chữa
CON SỐ. Test phải có một ca mà bản vá tham lam sẽ trượt.**

### 7.ck — Thủ phạm thật của `mở đầu NỀN TRƠN`: LỚP PHỦ CỦA CHÍNH MÌNH (24/8/2026 tối)
Bản vá 7.cj đo ảnh GỐC — **đo nhầm vật**. `Cinematic.tsx` phủ lên MỌI ảnh
`linear-gradient(rgba(3,6,16, .74 → .58 → .88))` cộng vignette `rgba(0,0,0,.55)`. Số đo trên máy:
một tấm ảnh **0,0% tối** ở dạng gốc ra khung **93,3% tối** sau lớp phủ. Vậy nên mới có ca
`❌ mở đầu NỀN TRƠN (tối 84,5% · 788 màu)` — **788 màu tức ẢNH THẬT**, chỉ bị chính lớp phủ của mình
dìm chết. Và đó cũng là lý do mở đầu trông tẻ nhạt: ta tự đắp một màn đen 74-88% lên đúng tấm hook.
Vá hai đầu:
* `_sau_man()` mô phỏng đúng lớp phủ trước khi đo ⇒ quyết định dựa trên thứ QC sẽ thấy.
* Thêm **BẬC 0 — làm mỏng lớp phủ** (`man` 0.75/0.55/0.45, gửi theo từng cảnh sang `Cinematic.tsx`).
  Rẻ nhất, đúng bệnh nhất, **không đụng tới ảnh**; chữ vẫn đọc được nhờ `textShadow` sẵn có. Chỉ khi
  bậc 0 không cứu nổi mới tới tăng sáng ảnh (bậc 1) rồi mượn ảnh cảnh khác (bậc 2).
Chốt bằng `t_cuu_mo_dau_khong_qua_mat_qc` (kiểm cả việc `Cinematic.tsx` THẬT SỰ dùng `man` — Python
tính xong mà composition không đọc thì vô nghĩa).
**LUẬT: trước khi chữa "ảnh xấu", phải kiểm xem thứ mình đo có đúng thứ người xem thấy không. Ở đây
khoảng cách giữa hai thứ đó là 93 điểm phần trăm.**

### 7.cl — Chữa mỗi khung mở đầu là chữa chỗ BỊ CHẤM, không phải chỗ NGƯỜI XEM THẤY (24/8/2026 tối)
Nối tiếp 7.ck. QC chỉ soi khung mở đầu, nên nới lớp phủ cho cảnh 0 là hết bị loại — **nhưng các cảnh
sau vẫn bị lớp phủ 74-88% dìm y hệt**, tức cả video vẫn xỉn, chỉ khác là không ai chặn. Đó đúng là
thứ anh nói "hình nhàm chán".
`can_man_moi_canh()` đo TỪNG cảnh qua lớp phủ; cảnh nào vượt 75% tối thì hạ `man` (0.75 → 0.55 → 0.45)
tới khi đạt. **Ảnh vốn sáng giữ nguyên lớp phủ dày** — phụ đề karaoke chạy suốt video nên không được
bỏ lớp phủ đại trà, chỉ nới đúng chỗ ảnh đã tối sẵn (ảnh tối + phủ mỏng thì chữ vẫn đọc rõ).
Chi phí đo: ~40ms/cảnh (đo thật), so với 2-4 phút render là không đáng kể.
Chốt bằng `t_noi_man_khong_dung_toi_anh` — kiểm **file ảnh gốc không bị sửa một byte**: nới lớp phủ là
đổi THÔNG SỐ DỰNG HÌNH, sửa file là làm hỏng nguồn mà nguồn thì không lấy lại được.
**LUẬT: sửa xong phải hỏi "mình vừa chữa chỗ bị CHẤM hay chỗ người xem THẤY?" — hai chỗ đó thường
không trùng nhau.**

### 7.cm — Đang chạy trên GƯƠNG mà vẫn đọc sổ quota Ở GƯƠNG (24/8/2026 tối)
`📟 Sổ quota hôm nay: ĐỌC 9.631/50.000` in ra **y hệt ở ba phiên liên tiếp** (16:06Z · 17:56Z · 20:12Z).
Nối tiếp 7.ce (sai ngày + thiếu một cuốn sổ), đây là tầng thứ ba: sau failover, `_db_jobs()` trả về
**B2 — bản chép ĐÔNG CỨNG từ 13:15Z** (B cạn hạn mức đọc nên gương không làm tươi được nữa). Đọc sổ ở
đó là đọc một con số đã chết, mà bức tường ngân sách thì ra quyết định trên nó.
Nay: khi `_B2["on"]`, lấy số từ **D1** (`ngan_sach_doc`) — luôn tươi, và **không nằm trong tài nguyên
đang cạn**, đúng nguyên tắc đã dùng ở 7.bz. D1 chưa có số ngày hôm nay thì trả `-1` = "không đo được",
KHÔNG bịa 0 (luật 7.cg).
**LUẬT: nguồn dự phòng chỉ đáng tin cho thứ nó được chép sang. Sổ đo THỜI GIAN THỰC thì bản chép luôn
sai — phải đọc từ nơi vẫn đang được cập nhật.**

**Ghi nhận đêm nay đã chạy đúng (đo trong log plan 20:12Z):**
`📦 Đệm bài: mục tiêu 7 ngày/kênh · đói nhất: FAKEUSA=1.5ngày, FARMUSA=2.0ngày, RELICUSA=2.0ngày…`
— PHẢN ÁP LỰC lần đầu hoạt động sau khi vá `_chu()` (7.ch); `📣 nghỉ tới 06:59Z` + `📣 B đã có cờ nghỉ
tới 06:59Z (dài hơn) — giữ nguyên` — cờ chung giữ đúng mốc cạn-ngày và không bị ghi đè (7.cd);
0 `Traceback`, 0 `KHÔNG SAO LƯU` — bước sao lưu kho key đã sống (7.cc).

### 7.cn — CỔNG KHO DRIVE chưa từng chặn được gì: nó tự ném lỗi rồi tự nuốt (24/8/2026 tối)
Chạy `pyflakes` quét cả hai repo, đúng MỘT phát hiện thật — và là phát hiện đắt:
`run_render.py: undefined name 'out_channels'`. Dòng `return out_channels([])` của cổng kho nằm trong
khối `try`, mà `out_channels` khi đó **chưa được định nghĩa** (nó ở phía dưới) ⇒ `NameError` ⇒ rơi
thẳng vào `except Exception` ngay bên dưới ⇒ in *"không kiểm được kho Drive … vẫn chạy (fail-open)"*
rồi **mở 18 luồng**. Nghĩa là cái cổng viết ra để chặn "không đọc được kho nào thì đừng render" chưa
bao giờ chặn được gì; mỗi lần kho Drive hỏng là cả phiên render ra rồi bị từ chối đẩy.
Vá: `out_channels` (và `import json` nó cần) chuyển lên TRƯỚC cổng; quyết định dừng đưa **ra ngoài
khối try** (`_cong_dong`) để không bao giờ bị nuốt. Chạy thử với `pool_accounts()` rỗng: in
`🛑 GATE ĐÓNG — DỪNG PHIÊN` và trả `PLAN channels=[]` đúng như thiết kế.
Chốt bằng `t_cong_kho_drive_dong_duoc_that` (so vị trí định nghĩa/lời gọi + kiểm quyết định nằm ngoài try).
**LUẬT: `except Exception` bọc quanh một QUYẾT ĐỊNH (không chỉ quanh I/O) là chỗ ẩn nấp hoàn hảo cho
lỗi lập trình. Việc đọc thì bọc được; việc QUYẾT ĐỊNH phải nằm ngoài.** Và: cho một linter chạy qua
repo là 30 giây, rẻ hơn nhiều so với một cổng an toàn chết âm thầm.

### 7.co — Đường dự phòng B2 bị bỏ qua IM LẶNG suốt (24/8/2026 tối)
Quét kiểu mới: lấy mọi dòng log đặc trưng trong code rồi đối chiếu với log thật — **dòng nào chưa từng
xuất hiện là ứng viên "tính năng chết"**. Cách này đã bắt 4 lỗi tối nay; lần này lòi ra
`📦 Gói sao lưu:` chưa từng in. Truy: bước sao lưu chạy được (7.cc đã vá) nhưng `pool_accounts()` trả
rỗng — và trong log chỉ có ĐÚNG MỘT dòng `đọc danh sách kho ở B hụt` rồi thẳng tới
`❌ không đọc được kho Drive nào`. Nhìn thì tưởng đã thử cả B2.
Thật ra `_b2_client()` trả `None` vì bước đó không được truyền `FIREBASE_PROJECT_ID_B2`, và vòng lặp
`continue` **không in gì**. Trớ trêu: ngay trong CÙNG FILE, khối B2 phía dưới lại mặc định
`"mm0-shard-b2"` khi thiếu env — hai chỗ cùng một việc, hai hành vi khác nhau (cùng họ 7.by).
Vá: `_b2_client()` mặc định `mm0-shard-b2` + in lý do khi vẫn phải bỏ qua; workflow truyền env B2 cho
bước sao lưu (đồng bộ với 3 bước còn lại). Chốt bằng `t_duong_du_phong_b2_khong_bi_bo_qua_im`.
**LUẬT: `continue` / `return None` trong một chuỗi dự phòng phải NÓI RA lý do. Chuỗi dự phòng im lặng
là chuỗi mà không ai biết nó có chạy hay không — và nó sẽ không chạy đúng lúc cần nhất.**

### 7.cp — `♻️ Dùng lại kịch bản đã lưu` chưa từng chạy: mỗi video đang trả tiền AI hai lần (24/8/2026 tối)
Quét dòng-log-chưa-từng-xuất-hiện (7.co) lòi tiếp ca này. Mỗi phiên đều có job `failed` còn giữ kịch
bản (QC loại mở đầu), nên `find_resumable` LẼ RA phải tìm thấy. Nhưng B cạn hạn mức cả buổi ⇒ lượt đọc
đó luôn 429 ⇒ hàm trả `None` với một câu *"bỏ qua, viết mới bình thường"* nghe như chuyện vặt.
**Không vặt:** mỗi lần bỏ qua là gọi Gemini **viết lại một kịch bản đã có sẵn** — thứ đắt nhất trong
dây chuyền — và điều đó đang xảy ra ở MỌI video. Nay hét lên + ghi vào máy dò chết câm
(`checkpoint kịch bản`), nên phiên nào không resume nổi lần nào sẽ hiện 🚨 thay vì im.
**LUẬT: câu chữ trong log định giá trị của sự việc. "Bỏ qua, bình thường" dán lên một khoản lãng phí
lặp lại ở mọi video thì không ai buồn đọc — và nó sống sót nhiều tháng.**

**Việc để lại cho sáng (cần anh quyết, em không tự làm):** kịch bản hiện chỉ nằm ở Firestore, nên hết
hạn mức là mất luôn đường resume. `hot_db.ghi_job` chưa chép `script` sang D1. Chép sang thì resume
chạy được cả khi Firestore cạn — nhưng phải đổi bảng D1 + deploy lại Worker, tức đụng hạ tầng đang
chạy, nên em dừng ở đây chờ anh.

### 7.cq — Mô hình lớp phủ đo hụt: HAULUSA vẫn bị loại dù đã "cứu" (24/8/2026 tối)
Phiên 20:12Z chạy bản vá 7.ck/7.cl. Kết quả tốt — `🪟 nới lớp phủ cho 8-13 cảnh` xuất hiện ở MỌI lane
(xác nhận lớp phủ đang dìm gần như toàn bộ cảnh, không riêng khung đầu). Nhưng HAULUSA vẫn có
`❌ mở đầu NỀN TRƠN (tối 80.0%)` **mà không có dòng cứu nào** — tức `sang_hoa_mo_dau` chấm "đạt" trong
khi khung thật 80% tối.
Hai chỗ sai, đều thuộc loại "tin mô hình quá mức":
* **Vignette mô phỏng quá nhẹ.** Thật là `inset 0 0 340px 120px rgba(0,0,0,.55)` trên khung rộng 1080:
  120px lan + 340px nhoè ⇒ vệt tối ăn vào tới ~40% nửa bề ngang, không phải chỉ mép. Bản đầu lấy mốc
  0.45 nên hụt. Sửa lại mốc 0.22 + đường cong mũ 1.4. Sau khi sửa, một ảnh **0,0% tối** ở dạng gốc đo
  ra **70-78% tối** sau lớp phủ — khớp hẳn với những con số QC vẫn báo.
* **Không có biên.** `_sau_man` là MÔ HÌNH, thiếu Ken Burns, `objectPosition: center 32%`, bóng chữ
  hook. Nay ép chặt hơn ngưỡng QC 13 điểm (`BIEN = 13`).
Chốt trong `t_cuu_mo_dau_khong_qua_mat_qc` (bắt buộc có `BIEN` ≥ 8).
**LUẬT: khi thay một phép đo thật bằng một mô hình, phải để BIÊN — và phải có ca thật đối chiếu.
Mô hình khớp "vừa đủ" nghĩa là nó sẽ trượt ở ca kế tiếp.**

### 7.cr — Bản vá "lấy việc kế" (7.ci) đúng chỗ nhưng VÔ HIỆU: nó dùng lại đúng ngưỡng vừa chặn nó
Kiểm chứng phiên 20:12Z (đã chạy 7.ci): dòng `♻️ … rảnh -> nhận thêm kênh` **vẫn 0 lần**, lane vẫn kết
thúc bằng `còn 57' < ước tính 69'/mẻ`. Vì vòng lấy-việc-kế đo bằng `min(budget_s, HARD_S)` — chính là
ngân sách MỀM 110' vừa chặn vòng trên — nên nó luôn `break` ngay lượt đầu.
Số thật (PRICEDUSA): lane tiêu **53'**, trần CỨNG là **150'** (timeout matrix 165' − 15' đệm) ⇒ còn
**97'**, thừa cho một mẻ 69'; lấy thêm một mẻ thì kết thúc ở 122', vẫn dưới trần 28'.
Ngân sách mềm sinh ra để **một KÊNH đừng ôm máy quá lâu**; phần giờ thừa phải chảy về HÀNG CHỜ chứ
không bỏ không. Nay vòng lấy việc đo theo `HARD_S`. Chốt bằng `t_lay_viec_ke_o_dung_duong_vao` (cấm
hẳn chuỗi `min(budget_s, HARD_S)` trong vòng đó); đã thử ngược: quay về ngưỡng mềm là test bắt.
**LUẬT: vá xong phải KIỂM CHỨNG BẰNG LOG PHIÊN SAU, đừng dừng ở "code đã đúng chỗ".** Đây là lần thứ
hai trong đêm một bản vá đúng ý tưởng nhưng không chạy (lần trước: 7.br vá nhầm file).

### 7.cs — `đăng được hôm nay: 0` thật ra là "bảng dự án YouTube còn trống" (24/8/2026 tối)
Dòng `📦 Đệm bài … đăng được hôm nay: 0` nghe như **hết hạn mức đăng**, nhưng Worker cộng `con` từ
danh sách dự án trong bảng `yt_project`; danh sách rỗng thì tổng tự nhiên bằng 0. Hai trạng thái hoàn
toàn khác nhau — "hết lượt" và "chưa khai báo dự án nào" — đang hiện cùng một con số, và con số đó là
thứ khâu phản áp lực sẽ dùng để quyết định nhịp sản xuất.
Nay `suc_dang_ngay()` trả **-1 = chưa biết** khi `rows` rỗng, chỉ trả 0 khi có dự án và đã hết lượt
thật; dòng log nói thẳng *"CHƯA BIẾT (bảng dự án YouTube trên D1 còn trống)"*.
Chốt bằng `t_suc_dang_phan_biet_chua_biet_voi_het_luot` (3 ca: trống / hết lượt / còn lượt).
**LUẬT (lần thứ năm trong đêm): 0 là một PHÉP ĐO, không phải chỗ đổ mọi thứ mình không biết.**
7.bm · 7.bs · 7.ce · 7.cg · nay 7.cs — cùng một sai lầm ở năm chỗ khác nhau.

**Việc để lại cho sáng:** bảng `yt_project` trên D1 chưa có dự án nào ⇒ khâu chọn dự án YouTube theo
hạn mức chưa có dữ liệu để làm việc. Cần anh khai báo (mỗi kênh 1 dự án Google riêng, 6 video/ngày).

### 7.ct — SUÝT MẤT SẠCH KHO SAO LƯU: gói rỗng được cất đè lên bản tốt (24/8/2026 tối) ⚠️
Vá xong 7.cc + 7.co thì bước sao lưu chạy được — và ngay lượt đầu tiên nó làm đúng thứ nguy hiểm nhất.
Log phiên 21:52Z:
```
📦 Gói sao lưu: 0 key · 0 kênh · 0.3KB (đã mã hoá)
✅ đã cất ở kho ADISONDURHAM / AHSHABRIAUNA / AIZAMAHIYAH
```
Gói **rỗng** đó thành bản MỚI NHẤT; ngay dưới lệnh cất, code giữ `GIU_LAI = 7` bản gần nhất và **bỏ
phần còn lại vào thùng rác**. Sao lưu chạy mỗi phiên (~30-40 phút) ⇒ **chỉ vài giờ là mọi bản sao lưu
THẬT bị đẩy ra rìa rồi xoá** — đúng thứ cái vault này sinh ra để chống. Đã cất 1 bản rỗng trước khi vá;
với GIU_LAI=7 thì chưa mất gì, nhưng đó là may.
Gói rỗng vì A và B đều cạn hạn mức ⇒ `_doc_firestore()` đọc được 0 bản ghi. **Đọc không ra dữ liệu
không phải là "dữ liệu rỗng"** (7.bm/7.cg) — càng không phải lý do để ghi đè bản tốt.
Nay: 0 key **và** 0 kênh ⇒ in `🛑 KHÔNG CẤT` rồi thoát, giữ nguyên bản cũ. Chốt bằng
`t_khong_cat_goi_sao_luu_rong` (kiểm cả việc chặn nằm TRƯỚC bước đóng gói/cất).
**LUẬT: bật một tính năng đã chết lâu ngày thì phải soi kỹ LƯỢT CHẠY ĐẦU TIÊN của nó — nó chạy trong
một thế giới khác với lúc được viết ra.**

**Cũng thấy trong log:** `⚠️ kho ADISONDURHAM hụt: invalid_grant` rồi ngay sau đó `✅ đã cất ở kho
ADISONDURHAM` — tức đang có HAI bản ghi cùng tên, một cái token chết. Đây là việc chờ anh bấm
`wipe_queue.yml -f fix_dup=true`.

### 7.cu — Quét cả HỌ "ghi bản rỗng đè bản tốt": còn 2 chỗ nữa, cả hai đều chí mạng (24/8/2026 tối)
Sau 7.ct, soi mọi chỗ có hình dạng "đọc xong rồi ghi đè snapshot". Ra thêm hai chỗ chưa có lớp chặn:
* **Snapshot KEY** `gemini_keys/__snap__{owner}` — `read_keys` đọc doc này TRƯỚC. Ghi đè bằng danh
  sách rỗng nghĩa là **cả dây chuyền tưởng mình không có key AI nào**. Xảy ra khi B quét ra 0 doc
  (owner lệch / shard trỏ nhầm / đang đọc gương không có key) mà A cũng trả 0 dòng.
* **Gói KHO** `connections_mirror/snap_kho` — gói rỗng ⇒ 18 luồng phía sau đọc ra "không có kho nào"
  rồi **từ chối đẩy video đã render xong**.
Nay cả hai in `🛑 KHÔNG ghi … danh sách rỗng — giữ nguyên bản cũ`. (Đường dựng gói kho TỪ GƯƠNG B đã
có sẵn `if not rows: return 0` từ trước — đúng mẫu, chỉ thiếu ở hai chỗ kia.)
Chốt bằng `t_khong_ghi_snapshot_rong`; đã thử ngược: gỡ một lớp chặn là test bắt.
**LUẬT: mọi lệnh GHI ĐÈ một bản sao lưu/gương/snapshot phải hỏi trước "cái tôi sắp ghi có RỖNG
không?" — vì nguồn của nó là một lượt ĐỌC, và đọc thì hỏng được. Rỗng gần như luôn là triệu chứng,
không phải sự thật.** Ba chỗ trong một đêm: vault (7.ct) · snapshot key · gói kho.

### 7.cv — Hàng chờ nằm TRONG chính tài nguyên đang cạn (24/8/2026 tối)
Vá 7.cr làm vòng lấy-việc-kế chạy được thật — và ngay lượt đầu lòi ra tầng dưới: log GRIDIRON phiên
21:52Z `⚠️ lấy việc kế hụt (429 Quota exceeded.)`. `lay_viec_ke` giành việc bằng **giao dịch trên
Firestore**, tức hàng chờ sống trong đúng thứ đang hết ⇒ **đúng lúc cần nhất thì không dùng được**.
Đường thay, không đụng Firestore và không cần deploy gì: plan gửi kèm danh sách dư (`QUEUE_LIST`) và
thứ tự mẻ (`PLAN_CHANNELS`) qua env; lane thứ *i* tự lấy các mục *i, i+N, i+2N…*. Chia TĨNH nên
**không cần điều phối và không thể trùng** (chạy thử: 18 lane chia 32 kênh dư → đúng 32, trùng 0).
Đổi lại: lane chết thì phần của nó chờ phiên sau — chấp nhận được, vì hiện tại phần dư **chẳng ai
làm cả**. Giao dịch Firestore vẫn là đường ưu tiên khi nó còn sống.
Chốt bằng `t_hang_cho_khong_phu_thuoc_firestore` (đủ/không trùng · hàng chờ rỗng · thiếu env thì im).
**LUẬT: cơ chế điều phối không được đặt trong tài nguyên mà nó điều phối việc sử dụng.** Đây là lần
thứ ba tối nay dùng đúng cách chữa đó: cờ B-cạn → D1 (7.bz), sổ quota → D1 (7.cm), nay hàng chờ → env.

### 7.cw — Đường thay của 7.cv sẽ KHÔNG BAO GIỜ tới lượt: hai lệnh Firestore chưa bọc (24/8/2026 tối)
Soi lại chính bản vá vừa viết trước khi nó kịp chạy. Vòng lấy-việc-kế có **ba** lệnh Firestore
(`read_config` kiểm cờ Dừng · `lay_viec_ke` · `read_channels`) nhưng chỉ `lay_viec_ke` được bọc. Mà
`read_config` đứng TRƯỚC — nó ném 429 là rơi thẳng xuống `except` ngoài cùng, in `lấy việc kế hụt` rồi
thoát ⇒ **đường chia-sẵn (không cần Firestore) không bao giờ tới lượt**. Đúng bẫy "bản vá không chạy"
đã dính hai lần trong đêm (7.br vá nhầm file · 7.cr tự chặn bằng ngân sách mềm).
Nay bọc RIÊNG từng lệnh, và mặc định khi hỏng là **chạy tiếp**, không phải chết: không đọc nổi cờ Dừng
thì coi như không có lệnh dừng; không đọc nổi danh sách kênh thì dùng gói `CHANNEL_CFGS` plan gửi kèm.
Chạy thử: mọi lệnh Firestore hỏng, lane vẫn lấy được việc + cấu hình từ env.
Chốt bằng `t_hang_cho_khong_phu_thuoc_firestore` (kiểm từng lệnh có `try` riêng); thử ngược: gỡ một
lớp bọc là test bắt.
**LUẬT: một chuỗi dự phòng chỉ mạnh bằng lệnh YẾU NHẤT đứng TRƯỚC nó. Viết xong đường thay thì phải
đi ngược lên xem có gì chặn đường tới đó không.**

### 7.cx — Vision kiểm ảnh: khâu hỏng thì IM HOÀN TOÀN, và hậu quả là ảnh sai vào thẳng video (24/8/2026 tối)
Soi máy dò "chết câm" xem nó đang canh những khâu nào: chỉ có `clip` (+ hai cuốn sổ vừa thêm ở 7.bx).
`verify_image` — lượt kiểm ảnh CÓ KHỚP NỘI DUNG không — nằm ngoài. Mà hàm này trả `None` khi lỗi, và
theo hợp đồng thì `None` = **"bỏ qua kiểm"**, tức người gọi NHẬN ảnh. Nghĩa là key Vision chết hoặc cạn
quota ⇒ **mọi ảnh đi thẳng vào video không qua một lượt kiểm nào**, còn log chỉ có một dòng cảnh báo lẫn
giữa hàng nghìn dòng. Đúng loại sự cố đã trả giá ở ca "clip 0/118": tính năng chết mà nhìn vẫn như đang chạy.
Nay `verify_image` ghi vào `dem_khau("vision ảnh", …)`, nên phiên nào 0/N sẽ hiện
`🚨 CHẾT CÂM: vision ảnh` ở dòng tổng kết; câu cảnh báo cũng nói thẳng *"ẢNH VÀO VIDEO KHÔNG QUA KIỂM"*.
Chốt bằng `t_vision_chet_thi_phai_hien_chet_cam` (3 lượt hỏng ⇒ phải ra CHẾT CÂM).
**LUẬT: mỗi phụ thuộc ngoài mà "hỏng thì bỏ qua" đều phải có người ĐẾM. Không đếm thì `bỏ qua` = `tắt
hẳn`, và không ai biết mình đang chạy với tính năng đã tắt.**

### 7.cy — HỒI QUY do chính bản đổi tên chuẩn: artifact phình vài GB mỗi phiên (24/8/2026 tối)
Kiểm end-to-end quy ước đặt tên (anh yêu cầu chiều nay) thì lòi ra tác dụng phụ chưa ai để ý.
Chuỗi tên vốn rất chặt và ĐÚNG: `upload_to_queue` đặt tên `.json` và thumbnail theo
`base = basename(video)`, còn sidecar ghi `thumbnail`/`captions` cũng từ chính `vbase` đó ⇒ một cái
tên video quyết định cả bốn. Vấn đề nằm chỗ khác:
* Trước: tên file đầu ra CỐ ĐỊNH theo kênh (`out/xxx_docshort0.mp4`) nên `fresh_out()` xoá đúng nó
  mỗi vòng — thư mục `out/` luôn chỉ có ~1 video.
* Sau khi đổi sang tên chuẩn (mỗi video một tên riêng), `fresh_out` không còn khớp ⇒ **video cũ nằm
  lại**. Mà workflow có `upload-artifact path: out/*.mp4` để cứu video CHƯA đẩy được kho ⇒ mỗi lane
  bắt đầu nhét TOÀN BỘ video của mình lên artifact: 18 lane × ~8 video × ~40MB ≈ **vài GB mỗi phiên**,
  cho những video ĐÃ nằm an toàn trên Drive.
Vá: đẩy kho thành công (có `drive_id`) thì xoá bản trên đĩa (video + ảnh + thumb). Bước backup giữ
đúng ý nghĩa của nó — chỉ còn cái CHƯA đẩy được. Chốt bằng `t_day_kho_xong_thi_xoa_ban_tren_dia`.
**LUẬT: đổi quy ước đặt tên là đổi một GIẢ ĐỊNH mà nhiều chỗ khác đang dựa vào — phải đi soi mọi nơi
khớp tên theo mẫu (dọn dẹp, artifact, glob), không chỉ nơi sinh ra tên.**

### 7.cz — Tên chuẩn có thể làm HAI VIDEO KHÁC NHAU đụng tên, và loại 2 sẽ xoá mất một cái (24/8/2026 tối)
Anh hỏi "đổi tên đã fix triệt để chưa" — soi lại thì còn một lỗ nữa, nặng hơn vụ artifact (7.cy).
`ten_file` cắt tiêu đề còn 46 ký tự, nên hai bài chỉ khác nhau ở đuôi ra CÙNG một tên. Ca thật dựng
được trên máy:
```
'Which state pays the most for electricity in 2026 really'
'Which state pays the most for electricity in 2026 truly'
-> GUESSUSA__20260824__S__Which-state-pays-the-most-for-electricity-in-2   (cả hai)
```
Hậu quả dây chuyền: hai file trùng tên trong một thư mục Drive ⇒ `find_junk` **loại 2 xoá cái cũ** =
mất một video thật; sidecar và thumbnail cũng lấy tên theo gốc đó nên **móc chéo sang nhau**.
Vá hai lớp:
* **Gốc:** tiêu đề BỊ CẮT thì gắn thêm 4 ký tự băm của tiêu đề ĐẦY ĐỦ. Tên đủ ngắn thì không gắn gì
  (giữ tên sạch) — lúc đó trùng tên nghĩa là trùng đúng nội dung.
* **Lưới:** `find_junk` loại 2 chỉ coi là bản sao khi **cùng tên VÀ cùng kích thước**; trùng tên mà
  khác cỡ thì in cảnh báo và **không xoá**.
Chốt bằng `t_ten_chuan_khong_dung_ten_nhau`.
**LUẬT: bất kỳ phép CẮT NGẮN nào (tên, id, khoá) đều tạo ra khả năng đụng nhau. Cắt thì phải kèm một
mẩu băm của bản đầy đủ — và chỗ nào XOÁ dựa trên "trùng" thì phải có thêm một dấu hiệu độc lập.**

### 7.da — "21 lỗi MỚI" là JOB BỎ NGỎ cộng dồn nhiều ngày, không phải lỗi của phiên đang chạy (25/8/2026)
Anh chỉ ra dashboard: `⚠️ 21 lỗi MỚI · gần nhất STATEWARS — ⏱ Quá 6h — tiến trình đã dừng (job ma)`.
Soi ra: mỗi video mở một bản ghi job (`new_job`) rồi mới đóng bằng `update_job(done/failed)`. Lane
thoát GIỮA CHỪNG — `SystemExit`, trần giờ 150', matrix timeout 165', runner hết bộ nhớ — thì bản ghi
đó **nằm mở vĩnh viễn**; 6 tiếng sau `health_guardian` thấy im tiếng nên dán `failed`. Không có lối
nào đóng chúng lúc thoát ⇒ con số **cộng dồn qua nhiều ngày**, nhìn như "lỗi mới" trong khi phiên
đang chạy sạch (kiểm 14 phiên gần nhất: phiên nào CHẠY cũng `success` 100-137'; các phiên `cancelled`
đều bị huỷ lúc còn PENDING 21-41', chưa render gì nên không mất việc).
Vá: `firestore_bridge` theo dõi `_JOB_MO` (job đã mở, chưa có kết cục) và đóng nốt lúc thoát qua
`atexit`, ghi rõ lý do. Tập rỗng thì 0 lượt ghi; có bỏ ngỏ mới ghi, trần 20 cái.
Chốt bằng `t_job_bo_ngo_duoc_dong_luc_thoat`.
**LUẬT: mở một bản ghi trạng thái thì phải có đường ĐÓNG nó ở MỌI lối thoát, kể cả lối thoát bất
thường. Không thì "số lỗi" trên bảng điều khiển đo tuổi thọ của rác, không đo sức khoẻ hệ thống.**

### 7.db — Test khẳng định thứ tự PHỤ THUỘC GIỜ, tự sai khi đồng hồ đi qua nửa đêm (25/8/2026)
`t_moc_reset_theo_nha_cung_cap` khẳng định *"Cloudflare luôn hồi sớm hơn Google"*. Chỉ đúng trong
khung 07:00→24:00Z. Qua 00:00Z, Cloudflare vừa reset nên mốc kế tiếp xa 24h, còn Google chỉ còn vài
tiếng tới 07:00Z ⇒ test đỏ lúc 00:14Z dù code không đổi một dòng. Điều BẤT BIẾN không phải thứ tự hai
con số mà là **mỗi bên nghỉ tới ĐÚNG mốc reset của mình** — nay test tính thẳng số phút tới mốc rồi so.
**LUẬT: test không được khẳng định thứ tự của hai đại lượng phụ thuộc thời gian. Hãy khẳng định
CÔNG THỨC, đừng khẳng định kết quả của một khoảnh khắc.**

### 7.dc — Kịch bản đi CÙNG video trên Drive, không chỉ nằm ở Firestore (25/8/2026, anh: "tự làm đi")
Vấn đề gốc ở 7.cp: kịch bản chỉ có trong `render_jobs` ⇒ Firestore cạn hạn mức là mất đường resume,
hệ phải gọi AI **viết lại một bài ĐÃ CÓ**. Phương án D1 cần đổi bảng + deploy lại Worker, mà máy này
KHÔNG có token Cloudflare nên em không deploy được.
Đường tốt hơn và **không cần deploy**: nhét kịch bản vào **sidecar `.json` nằm cạnh video trên Drive**.
Drive luôn đọc được (có gương ở B/B2 + lớp cứu KV), lại chính là nơi video đang nằm, nên kịch bản và
video **không thể lạc nhau** — và không tốn thêm một lượt ghi nào (sidecar vốn đã được ghi).
`get_script_by_drive` nay: Firestore trước → hỏng/không có thì đọc sidecar trên Drive → cả hai không
ra mới ném `DocLoi`. Chốt bằng `t_kich_ban_di_cung_video_tren_drive`.
**LUẬT: dữ liệu quý phải nằm CÙNG CHỖ với thứ nó mô tả. Tách ra hai hệ thống là có ngày một bên chết
mà bên kia không biết.**

### 7.dd — Token kho hỏng: mỗi tiến trình tự tông một lần vì trí nhớ không chia sẻ (25/8/2026)
Anh chỉ ra: `⚠️ kho ADISONDURHAM hụt: invalid_grant` rồi NGAY SAU đó `✅ đã cất ở kho ADISONDURHAM`
— **tài khoản vẫn sống**, chỉ là đang có HAI bản ghi cùng tên và một bản mang `refresh_token` cũ.
`_DEAD_ACCS` chỉ nhớ trong MỘT tiến trình, nên mỗi lane / mỗi lượt publish lại thử lại đúng bản chết
đó: rác log, chậm, và **mỗi lượt hỏng vẫn tính vào hạn mức Google**.
Nay ghi cờ `kho:<root>` vào **D1** qua đúng lệnh `key_nghi_ghi` đã có (không đổi bảng, không deploy),
mọi tiến trình tra trước khi thử. Cờ **tự hết hạn sau 12h** nên anh kết nối lại là kho tự sống — không
phải nhớ đi xoá cờ, và cũng không xoá bản ghi nào (không phá dữ liệu).
Chốt bằng `t_kho_token_chet_nho_chung`.
**LUẬT: cái gì đã học được bằng một lần trả giá thì phải chia sẻ cho mọi tiến trình — và phải TỰ HẾT
HẠN, vì trạng thái hỏng hôm nay có thể được sửa ngày mai.**

### 7.de — Khai báo dự án YouTube: suy ra từ kênh đã kết nối, khỏi bắt người dùng khai tay (25/8/2026)
Anh: *"a chỉ lấy api key youtube gắn vào chọn folder channel là chạy thôi"*. Bảng `yt_project` trên D1
còn trống nên `suc_dang_ngay()` trả "chưa biết" (7.cs) — đúng nhưng vô dụng. Worker **không có lệnh
thêm dòng** vào bảng đó, mà thêm lệnh thì phải deploy lại Worker; máy này không có token Cloudflare.
Đường không cần deploy: mỗi kênh YouTube nằm trên một tài khoản Google riêng ⇒ **mỗi kênh có hạn mức
riêng 6 video/ngày**. Vậy sức đăng ≈ (số kênh đã từng đăng được) × 6 − (đã dùng hôm nay), lấy từ
`yt_kenh_doi` + `yt_con_cho` — **cả hai đều là lệnh CÓ SẴN**.
Thứ tự ưu tiên: bảng có dữ liệu → dùng số thật; bảng trống → suy ra và **nói rõ là ước tính trần trên**;
chưa kênh nào từng đăng → vẫn trả -1 (chưa biết), không bịa.
**LUẬT: khi thiếu một bảng cấu hình, hãy hỏi xem dữ liệu đó có SUY RA ĐƯỢC từ thứ hệ thống đã biết
không — trước khi bắt người dùng ngồi khai báo tay.**

### 7.df — "Hôm nay: 32" là do CHÍNH bản vá 20:21 làm bên ghi và bên đọc lệch khoá ngày (25/8/2026)
Anh hỏi số hôm nay đã đúng chưa. Soi ra một hồi quy tôi tự gây tối nay: lúc 20:21 tôi đổi **cả sáu**
chỗ đánh số ngày sang `_ngay_quota()` (UTC-7) cho khớp mốc reset của Google. Đúng cho **sổ quota**,
nhưng SAI ở `count_pushed` — ô đó là **bộ đếm HIỂN THỊ**, mà dashboard đọc bằng
`new Date().toISOString().slice(0,10)` tức **ngày UTC**. Lúc 00:39Z ngày 25/8, dashboard đọc khoá
`20260825` trong khi tiến trình ghi vào `20260824` ⇒ ô "Hôm nay" hiện 32 thay vì số thật.
Nay tách bạch: **sổ quota → UTC-7** (mốc Google) · **bộ đếm hiển thị → UTC** (khớp dashboard).
Chốt bằng `t_so_quota_dung_ngay_va_gop_du`: kiểm từng hàm quota phải dùng `_ngay_quota()`, `count_pushed`
phải dùng UTC, VÀ kiểm luôn dashboard vẫn tính khoá theo cách cũ (dashboard đổi thì test đỏ).
**LUẬT: "một ngày" không phải một khái niệm duy nhất trong hệ. Ngày của NHÀ CUNG CẤP (mốc reset hạn
mức) khác ngày của NGƯỜI XEM BẢNG. Thay khoá ngày ở một bên mà không xem bên kia đọc bằng gì là con
số sai ngay lập tức — và sai một cách rất khó ngờ vì code hai bên đều "trông đúng".**

### 7.dg — Kịch bản cần bản dự phòng ở KHO KHÁC (25/8/2026, anh hỏi "nhỡ 1 driver hỏng")
Kiểm thật thì thấy: **kịch bản** có 2 bản (Firestore + sidecar cạnh video) nhưng sidecar nằm ĐÚNG cái
kho chứa video ⇒ kho đó chết là mất **cả hai** cùng lúc, chỉ còn Firestore — mà Firestore chính là thứ
hay cạn hạn mức nhất. **Video** thì chỉ có 1 bản; `storage.backup_account()` (kho lạnh) có tồn tại
nhưng **không ai gọi** — lại một tính năng chết câm.
Không thể nhân đôi mọi video (72 kho × 14GB, nhân đôi là mất một nửa sức chứa). Nhưng kịch bản chỉ vài
KB: cuối mỗi lane gom cả lane vào MỘT file rồi cất sang **2 kho khác** (~18 file/phiên thay vì ~110).
Mất một kho vẫn dựng lại được toàn bộ video của kho đó, **0 lượt gọi AI**.
Chốt bằng `t_kich_ban_co_ban_du_phong_khac_kho` (2 kho phải KHÁC NHAU · cất xong dọn danh sách · rỗng
thì không cất).

### 7.dh — MÁY DÒ CHẾT CÂM BẮT ĐƯỢC CA THẬT ĐẦU TIÊN: vision chết 0/36 (25/8/2026)
Chưa đầy một giờ sau khi gắn `dem_khau("vision ảnh")` (7.cx), nó bắt ngay:
```
📈 tỉ lệ dùng được: checkpoint kịch bản 2/2 · clip 16/16 · sổ chủ đề 6/6 · vision ảnh 0/36
🚨 CHẾT CÂM: vision ảnh
   ⚠️ verify_image lỗi: cloudflare HTTP 403: AiError: Model ...
```
Tức **36 tấm ảnh của lane FUTUREUSA vào video mà không qua một lượt kiểm khớp nội dung nào** — và
trước hôm nay chuyện này hoàn toàn vô hình.
Gốc: đường TEXT đã có `_resolve_live_model()` (dò `/ai/models/search` khi CF gỡ model) từ lâu, nhưng
đường **VISION viết cứng đúng MỘT tên model** `CF_VISION_MODEL`. CF đổi/gỡ tên là vision chết 100%.
Thêm nữa, nhánh tự chữa chỉ nhận **400/404**, còn ca thật trả **403** nên rơi thẳng xuống `raise`.
Vá: `_CF_VIS_PREF` + `_resolve_live_vision()` (dò model CF **thật sự đang có**, danh sách lỗi thời
cũng không sao) · nhận thêm 403 cho đường vision · nới thông báo lỗi 60→220 ký tự (cắt 60 làm mất
đúng chỗ chẩn đoán: log chỉ hiện `AiError: Model A`).
Chốt bằng `t_vision_co_model_du_phong`.
**LUẬT: mỗi phụ thuộc ngoài phải có (a) danh sách dự phòng, (b) đường TỰ DÒ khi nhà cung cấp đổi tên,
(c) một người ĐẾM. Thiếu (c) thì (a) và (b) hỏng lúc nào không ai biết.** Đây là lần đầu cả ba có đủ,
và nó trả kết quả ngay trong giờ đầu tiên.

### 7.di — Lane ôm nhiều kênh ⇒ dòng log không ghi tên kênh là QUY SAI LỖI (25/8/2026)
Chính tôi vừa dính. Thấy lane tên **COSMOS** có `❌ mở đầu NỀN TRƠN (tối 77,3% · 629 màu)` nên kết luận
"COSMOS lỗi" — nhưng COSMOS là kênh `dark_ok` (luật `dark≥88 & cols<450`), 77,3% lẽ ra KHÔNG bị loại.
Truy tiếp mới ra: lane đó vừa `♻️ nhận thêm kênh SIGNALUSA` từ hàng chờ, và lỗi là **của SIGNALUSA** —
kênh KHÔNG dark_ok, luật `dark≥75 & cols<900`, nên 77,3% bị loại là đúng.
Từ khi lane biết lấy thêm việc (7.ci/7.cr), **một lane xử lý nhiều kênh** mà mọi dòng QC vẫn chỉ ghi
nội dung, không ghi kênh ⇒ đọc log là quy sai lỗi, rồi vá sai chỗ.
Nay 3 dòng loại QC đều in `[TÊNKÊNH]`. Chốt bằng `t_dong_loai_qc_phai_ghi_ten_kenh` (quét mọi lệnh
`print` có "NỀN TRƠN" phải kèm `[{channel}]`, bỏ qua chú thích).
**LUẬT: khi một tiến trình bắt đầu phục vụ NHIỀU đối tượng, mọi dòng log của nó phải mang danh tính
đối tượng. Đổi mô hình chạy mà không đổi log là biến log thành thứ đánh lừa người đọc.**

**Kiểm chứng bản vá lớp phủ trên số thật (không đợi phiên sau):**
COSMOS phiên 23:33 — hàm cứu báo *"làm mỏng lớp phủ xuống 0,75 → tối 73% (đạt)"* nhưng khung render
THẬT ra **93,7%**. Với ngưỡng cũ (BIEN=13 ⇒ chấp nhận <75) thì 73% lọt. Với BIEN=20: dark_ok ⇒ ngưỡng
**<68**, nên 73% **không được chấp nhận**, hàm tiếp tục hạ `man` xuống 0,55 rồi 0,45. Ca SIGNALUSA
(không dark_ok) ngưỡng còn **<55**, ép mỏng sâu hơn nữa. Tức bản vá 23:34 đánh trúng cả hai ca đang lỗi.

### 7.dj — Tên chuẩn làm BẨN TIÊU ĐỀ YOUTUBE khi video thiếu sidecar (25/8/2026)
Quét repo ĐĂNG trước giờ project A hồi (~07:00Z) — khâu này sắp chạy lần đầu sau ~18 tiếng nằm im.
`main.py` dựng metadata bằng `sidecar.get("topic") or M.slug_to_topic(f["name"])`. Từ khi dùng tên
chuẩn `KENH__YYYYMMDD__seri__S1__tieu-de[-bam]`, nhánh dự phòng đó trả
`'DEFENSEUSA 20260825 Ab3xk9 S1 Where The Money Goes'` — và **đó là thứ được đem đặt làm TIÊU ĐỀ
YOUTUBE**: mã kênh, ngày, mã chùm, số thứ tự dán trước tiêu đề thật, hiện ra cho người xem.
Lỗi do chính bản đổi tên gây ra, và chỉ lộ ở khâu đăng nên render chạy sạch vẫn không thấy.
Vá: `slug_to_topic` bóc mọi đoạn trước ô vai trò `L`/`S<n>` và bỏ đuôi băm 4 ký tự; tên đời cũ
(`how-i-went-broke_short.mp4`) vẫn ra đúng như trước. Chốt bằng `t_ten_file_khong_lam_ban_tieu_de`.
**LUẬT: đổi quy ước đặt tên thì phải soi cả những chỗ ĐỌC NGƯỢC cái tên đó ra thông tin — không chỉ
chỗ ghép tên.** (7.cy là chỗ dọn dẹp, 7.cz là chỗ so trùng, đây là chỗ suy ngược ra tiêu đề.)

### 7.dk — Biến môi trường RỖNG phá giá trị mặc định — và tôi tự tạo ra nó trong 5 phút (25/8/2026)
Chạy `kiem_kho` để sửa con số anh nhìn thấy. Lần 1 chết vì bước đó không được truyền `HOT_KEY` ⇒ lớp
cứu KV (đường sống khi Firestore hỏng) không dùng được — **có đường sống mà không cắm điện**. Thêm
`HOT_KEY` + `HOT_URL` rồi chạy lần 2, lại chết:
```
⚠️ lớp cứu KV cũng hụt: unknown url type: ''
```
Vì `HOT_URL: ${{ secrets.HOT_URL }}` trỏ vào một secret **không tồn tại** ⇒ biến được ĐẶT nhưng RỖNG
⇒ `os.environ.get("HOT_URL", "https://…")` trả `""` (đối số mặc định chỉ dùng khi biến KHÔNG tồn tại)
⇒ URL rỗng. Tôi tự tay vô hiệu hoá giá trị mặc định, đúng lúc nó là đường sống duy nhất.
Quét cả hai repo: **21 chỗ** cùng dạng (`GEMINI_MODEL`, `CF_VISION_MODEL`, `LANE_BUDGET_MIN`,
`POSTING_TEMPLATE`, `FIREBASE_PROJECT_ID_B2`…) — mỗi chỗ là một quả mìn chờ ai đó thêm một dòng env
trỏ vào secret chưa đặt. Đã đổi hết sang `os.environ.get(K) or "mđ"`.
Chốt bằng `t_bien_moi_truong_rong_khong_pha_mac_dinh` (quét AST, cấm hẳn dạng cũ).
**LUẬT: trong CI, "biến không tồn tại" và "biến rỗng" là hai chuyện khác nhau, và cái thứ hai mới hay
xảy ra — vì workflow luôn ĐẶT biến, chỉ là secret có thể trống. Luôn dùng `or`, đừng dùng đối số mặc
định của `.get()`.**

### 7.dl — LƯỢT PING "CHO CHẮC" TỰ LOẠI CLIENT TỐT (25/8/2026)
Ba lượt `kiem_kho` liên tiếp chết vì `400 Invalid database id (default)`. Đoán hai lần đều trượt (đổi
Python 3.12→3.11, ghim thư viện giống render_cron). Nên in thẳng chẩn đoán thay vì đoán tiếp — và số
đo trả lời ngay: project id ĐÚNG (A=18 · B=11 · B2=12 ký tự), file creds có thật (2.3KB), thư viện
đúng bản (firestore 2.29 · api-core 2.35 · grpcio 1.83). **Không phải cạn hạn mức, không phải đợi là hết.**
Gốc: `firestore_state._sa_client()` sau khi dựng client còn chạy một lượt **ping** `_ping` "để lộ lỗi
sớm". Lượt ping đó trả 400 rồi hàm kết luận **client hỏng → trả None**. Trong khi
`firestore_bridge._db_jobs()` dựng client **KHÔNG ping** và đọc/ghi B bình thường suốt đêm ở
render_cron. Tức chính lượt kiểm "cho chắc" mới là thứ làm hỏng: nó gặp một lỗi mà đường dùng thật
không gặp, rồi phán quyết thay cho đường dùng thật.
Vá: ping trả 400 ⇒ **ghi nhận rồi VẪN trả client** cho tầng trên tự thử. Và `kiem_kho` không còn coi
"đọc render_jobs hỏng" là hỏng cả việc — con số quan trọng nhất (bao nhiêu video THẬT) đã đếm xong từ
Drive, kênh/loại suy được từ tên chuẩn.
**LUẬT: một phép kiểm tra sức khoẻ chỉ được phép BÁO CÁO, không được phép PHÁN QUYẾT. Nếu nó nghiêm
khắc hơn đường dùng thật, nó sẽ giết những thứ đang chạy tốt.**

### 7.dm — Đặt việc SỬA SỐ vào nơi lệnh GHI chắc chắn chạy được (25/8/2026)
`wipe_queue` chạy `kiem_kho.py` **đếm được** số thật (1.996 video, qua lớp cứu KV, 72/72 kho) nhưng
lệnh **ghi sổ luôn trả `400 Invalid database id`** — trong khi plan của `render_cron` ghi Firestore
bình thường suốt đêm với ĐÚNG những secret đó. Sửa được số mà không ghi được thì vô nghĩa.
Nên chuyển việc đối chiếu vào **plan**: `_kiem_kho_ngay()` chạy **1 lần/ngày**, đi 72 kho (~35 giây,
không tốn hạn mức Firestore vì đọc qua gương + KV), rồi `dat_so_kho_that()` **ghi đè** `total` bằng số
nguyên (KHÔNG `Increment`). Bộ đếm cộng dồn không bao giờ tự đúng lại được — chỉ đếm lại từ Drive mới
kéo nó về sự thật.
Hai chốt an toàn: đọc được **<5 kho** hoặc **có kho nào đọc hụt** ⇒ **bỏ qua lượt ghi** (đếm thiếu mà
ghi đè thì sổ càng sai hơn — đúng luật 7.cu).
Chốt bằng `t_doi_chieu_so_kho_chay_trong_plan`.
**LUẬT: đặt việc sửa dữ liệu vào tiến trình có QUYỀN GHI đã được chứng minh, đừng đặt vào một workflow
riêng rồi mới phát hiện nó không ghi nổi.**

### 7.dn — BA CON SỐ, BA SỰ THẬT KHÁC NHAU — và không cái nào đúng (25/8/2026)
Đo thẳng, không đoán:
| Nguồn | Số | Bản chất |
|---|---|---|
| `__pushed__` (Firestore) | **2.070** | bộ đếm cộng dồn, chỉ tăng: render lại +1, dọn rác vẫn +1 |
| D1 đếm lại bản ghi | **1.475** | chỉ có job TỪ LÚC bật chế độ D1, thiếu 521 video cũ |
| **Đi đếm 72 kho Drive** | **1.996** | **sự thật** |
Dashboard lại lấy số theo thứ tự tệ nhất: hỏi D1 (1.475) rồi **ghi đè bằng `__pushed__` (2.070)** ở
dòng ngay sau, vô điều kiện — số đúng bị vứt mỗi lần tải trang.
Vá trọn chuỗi: ① dashboard chỉ dùng `__pushed__` làm **đường lùi** khi D1 im · ② Worker có bảng
`kho_that` + lệnh `kho_that_ghi`, `apiHotStat` **ưu tiên số Drive** (quá 26h thì mới quay về đếm bản
ghi) · ③ plan mỗi ngày đi 72 kho rồi ghi số đó vào D1 **trước**, Firestore sau.
Đã deploy Worker + dashboard. Số hiện tại: `{"tong":1996,"tong_nguon":"drive","homnay":283,"loi":218,"dangchay":12}`.
**LUẬT: khi ba nguồn cho ba con số, đừng chọn nguồn "tiện nhất" — hãy hỏi cái nào ĐO THỨ THẬT. Ở đây
chỉ có Drive, vì video nằm ở đó.**

### 7.do — Ô "❌ Lỗi" đếm cả đời nên vô dụng (25/8/2026)
`apiHotStat` đếm `status='failed'` **không giới hạn thời gian** ⇒ mọi lần QC loại từ trước tới nay đều
cộng vào (đo: 218) và không bao giờ giảm. Con số chỉ-tăng thì người vận hành hoặc hoảng hoặc bỏ qua
hẳn — cả hai đều vô dụng. Nay giới hạn **2 ngày**: thứ cần biết là "gần đây có gì hỏng", còn lịch sử
đã nằm trong bản ghi job. (Cùng họ 7.bj: số cộng dồn không đo được sức khoẻ hiện tại.)

### 7.dp — Tối ưu mà đẻ ra lãng phí lớn hơn: chốt 1-lần/ngày đặt ở chỗ GHI HỤT (25/8/2026)
Vừa thêm `_kiem_kho_ngay()` (đi 72 kho Drive để lấy số thật) vào plan, chốt "hôm nay làm rồi" đặt ở
`render_config` trên **Firestore** — đúng thứ đang trả 400 khi ghi. Ghi hụt ⇒ chốt **không bao giờ
đóng** ⇒ plan đi 72 kho **mỗi lượt** thay vì 1 lần/ngày: ~48 lượt/ngày × 72 kho ≈ **3.500 lượt quét**,
mỗi lượt ~35 giây. Một bản "tối ưu" tự đẻ ra khoản lãng phí lớn hơn thứ nó tiết kiệm.
Vá: đóng chốt ở **D1 trước** (`key_nghi_ghi("kiem_kho", …)`, hạn 20 giờ — luôn ghi được, không nằm
trong tài nguyên đang cạn), Firestore chỉ là bản ghi phụ. Chạy thử: chốt đóng rồi thì 5 lượt plan tiếp
theo **quét 0 lần**. Chốt bằng `t_doi_chieu_so_kho_chay_trong_plan`.
**LUẬT: chốt chống-làm-lại phải nằm ở nơi GHI CHẮC CHẮN THÀNH CÔNG. Chốt ghi hụt thì không phải là
chốt — nó là một vòng lặp vô hạn chạy chậm.**

### 7.dq — Số "Tổng" neo vào sự thật rồi CỘNG TIẾP, khỏi đứng im cả ngày (25/8/2026, anh hỏi nhịp cập nhật)
Lượt đi đếm 72 kho chỉ chạy **1 lần/ngày**. Nếu ô "Tổng" chỉ hiện con số đó thì suốt ngày nó **đứng
im** dù video vẫn ra đều — người xem lại tưởng hỏng, đúng cái vòng nghi ngờ đã tốn cả đêm.
Cách đúng: lưu kèm `nen` = số bản ghi done-có-file trong D1 **ngay lúc đếm**, rồi hiển thị
```
tổng = số_thật_từ_Drive + (số_bản_ghi_hiện_tại − nen)
```
Phần chênh chính là số video làm THÊM kể từ lượt đếm ⇒ **tươi theo từng video**, mà vẫn **neo vào sự
thật** mỗi ngày. Quá 26 giờ không có lượt đếm mới thì bỏ neo, quay về đếm bản ghi (thà thiếu còn hơn
trôi xa sự thật mà không ai biết).
**LUẬT: một con số vừa cần ĐÚNG vừa cần TƯƠI thì đừng chọn một trong hai — hãy neo vào phép đo đúng
rồi cộng phần chênh đo được theo thời gian thực.**

### 7.dr — D1 sẽ CẠN sau ~30 ngày nếu không dọn (25/8/2026, anh hỏi trước khi nó xảy ra)
Đo thật bằng `rows_read` mà D1 trả về, không ước:
| Sau | Dòng `render_job` | rows_read/ngày | % trần 5 triệu |
|---|---|---|---|
| hôm nay | 1.558 | 979.200 | 19,6% |
| +15 ngày | 7.558 | 4,75 triệu | **95%** |
| +30 ngày | 13.558 | 8,52 triệu | **170% — CẠN** |
Vì `apiHotStat` chạy 4 lệnh `COUNT` trên `render_job` mỗi lượt, mà bảng **chỉ tăng**. Dashboard đã đệm
5 phút (288 lượt/ngày/tab) nên nhịp gọi không phải vấn đề — **kích thước bảng mới là vấn đề**.
Vá: D1 là kho **NÓNG**, không phải kho lưu trữ. Lệnh `don_job_cu` giữ **14 ngày** gần nhất, chạy cùng
nhịp 1 lần/ngày với lượt kiểm kho ⇒ bảng đứng ở ~5.600 dòng và mức đọc **phẳng mãi mãi**. Lịch sử
không mất: video ở Drive, kịch bản ở sidecar + 2 kho dự phòng.
Dọn xong **neo lại `nen`** = số dòng còn lại, nếu không phần chênh của ô "Tổng" hoá âm.
**LUẬT: bảng nào chỉ-tăng mà lại bị COUNT mỗi lượt đọc thì phải có hạn tuổi. Tính trước ngày nó cạn,
đừng đợi ngày đó tới.**

### 7.ds — "Báo một đằng hiển thị một nẻo": có hai nguồn số mà không dán nhãn (25/8/2026)
API trả `{"tong":1996,...}` trong khi dashboard hiện `2178` — vì có **hai nguồn** (D1 đếm thật từ
Drive · `__pushed__` cộng dồn ở Firestore) và khối D1 `catch(_){}` **nuốt im** mọi lỗi, rơi về nguồn
sai mà không dấu vết. Người xem không có cách nào biết mình đang nhìn số nào.
Vá: ① ô đổi tên thành **"Video trong kho"** (đúng thứ nó đo) · ② dán nhãn nguồn ngay cạnh số
(`✓ kho thật` / `~ bản ghi` / `⚠ D1 im — số cộng dồn`) · ③ lỗi D1 ghi `console.warn`, không nuốt.
**LUẬT: một con số có nhiều nguồn thì PHẢI hiện nguồn. Không dán nhãn thì mỗi lần lệch là một cuộc
tranh cãi vô ích.**

### 7.dt — Cắt 71% lượt ghi D1 mà không mất một con số nào (25/8/2026, gói FREE mốc NGÀY)
Anh xác nhận đang dùng **D1 Free** ⇒ mốc **theo ngày**: 5 triệu dòng đọc · **100.000 dòng ghi** · 5 GB.
Số đo thật kho `mm0-hot` (24h): đọc **665.157 (13,3%)** · ghi **19.073 (19,1%)** · dung lượng 963 kB.
**Ghi mới là ô chật nhất**, và nó tăng theo SỐ VIDEO chứ không theo số lần mở dashboard — nâng sản
lượng gấp 3 là chạm ~57%.
Truy nguồn: mọi bảng khác chỉ 0-2 dòng ⇒ `render_job` chiếm gần như toàn bộ, ~10 lượt ghi/video. Hai
chỗ thừa:
1. Mọi cập nhật mang `script` **vượt qua hãm 12 phút** (đúng — kịch bản là thứ quý, mất là trả tiền
   Gemini lần hai). Nhưng **D1 KHÔNG LƯU `script`** ⇒ với D1 những lượt đó không thêm một chữ nào.
2. Ghi từng bước `writing → rendering → qc` chỉ để làm mới mốc thời gian.
D1 thật sự chỉ cần: **trạng thái CUỐI** (để đếm) + **một mốc còn tươi** (ô "Đang chạy" dùng cửa sổ 45
phút). Nay: bỏ lượt ghi khi bộ trường D1 quan tâm KHÔNG đổi, và hãm bước trung gian 10 phút;
`done/failed/ratelimited` **luôn ghi ngay, không bao giờ hãm**.
Đo trên vòng đời một video: **7 lượt → 2 lượt (cắt 71%)** ⇒ ~19,1% xuống ~**5-6%** trần ngày.
Chốt bằng `t_cat_luot_ghi_d1_thua` (có ca kiểm `done` KHÔNG bị hãm — hãm nhầm là đếm thiếu video).
**LUẬT: trước khi tối ưu một khoản chi, hãy ĐO xem nó đi đâu. Ở đây 100% nằm ở một bảng, và 71% là
lượt ghi không mang thông tin mới cho chính kho đó.**

### 7.du — Bản vá vision TỰ CHỌN LẠI CHÍNH MODEL VỪA HỎNG (25/8/2026)
Log phiên 02:15Z (đã chạy bản vá 7.dh):
```
⛅ CF vision: '@cf/meta/llama-3.2-11b-vision-instruct' không dùng được
   -> chuyển sang '@cf/meta/llama-3.2-11b-vision-instruct'
```
Vì model đó là **mục đầu** danh sách ưu tiên và `/ai/models/search` vẫn báo nó **TỒN TẠI**. Lỗi thật
là **403 Forbidden** — chuyện **QUYỀN** (tài khoản chưa được cấp Workers AI cho model ảnh), không phải
model bị gỡ. **"Có tồn tại" và "được phép dùng" là hai chuyện khác nhau**, mà hàm dò chỉ kiểm cái đầu.
Kết quả: vision vẫn 0/36 — ảnh vẫn vào video không qua kiểm.
Vá: nhớ model đã hỏng (`_vis_hong`), lần dò sau **bỏ qua nó**; hết danh sách thì báo rõ *"tài khoản có
thể chưa được cấp quyền Workers AI cho model ảnh — hãy để Vision chạy bằng key Gemini"*. Tách
`_models_song()` ra để test được mà không gọi mạng.
**LUẬT: khi tự chữa bằng cách "chọn cái khác", phải LOẠI TRỪ cái vừa hỏng. Không loại trừ thì vòng
lặp tự chọn lại chính nó và mọi thứ trông như đã chữa.**

### 7.dv — DEPLOY NHẦM SITE SUỐT: sửa đúng nhưng đẩy vào trang không ai xem (25/8/2026)
Anh báo vẫn thấy `✅ Tổng cộng dồn: 2209` — trong khi em đã đổi nhãn đó thành `Video trong kho` và
deploy "thành công" **ba lần**. Manh mối chính là cái nhãn: **chữ cũ nghĩa là trang cũ**, không phải
đệm trình duyệt.
Truy ra: `firebase deploy` lấy project đang chọn của CLI (`mm0-shard-c`), trong khi `.firebaserc` ghi
`"default": "mm0-auto-publisher"` — và **trang anh mở là bản default**. Đo thẳng ba site:
```
mm0-auto-publisher.web.app  __d1OK=0  nhãn="Tổng cộng dồn"   <- anh đang xem
mm0-shard-c.web.app         __d1OK=8  nhãn="Video trong kho" <- em deploy vào đây
```
Ba lượt vá dashboard đêm nay đều **đúng code, sai đích**. Đã deploy lại với `--project
mm0-auto-publisher`, kiểm chứng lại bằng chính lệnh đo trên: `__d1OK=8 · nhãn="Video trong kho"`.
**LUẬT: deploy xong phải FETCH LẠI URL NGƯỜI DÙNG THẬT SỰ MỞ và tìm một dấu vết CHỈ CÓ Ở BẢN MỚI
(nhãn đổi, biến mới). "Deploy complete" chỉ chứng minh có thứ gì đó lên mạng, không chứng minh nó lên
đúng chỗ.** Và khi người dùng mô tả thứ họ thấy mà nó KHÔNG khớp code hiện tại, hãy nghi đường phân
phối trước khi nghi logic.

### 7.dw — 51 key Groq VÔ HÌNH với dây chuyền vì ảnh chụp key không được dựng lại (25/8/2026)
Anh hỏi "bữa kêu ưu tiên Groq mà sao không dùng". Kiểm: `key_order()` **đúng** — Groq → CF → Gemini,
có `t_key_order` chốt. Nhưng log 4 lane **không có một chữ `gsk_`/`groq` nào**, trong khi dashboard
báo 51 key Groq.
Gốc: lane đọc hồ key từ **ảnh chụp `__snap__` ở B**; ảnh đó chỉ được dựng lại ở CUỐI `sync_keys_from_a`
— mà lượt quét A ném `429 Quota exceeded` nên nhảy thẳng xuống `except`, ảnh **giữ nguyên bản cũ chưa
có Groq**. Dashboard thì đọc thẳng A nên vẫn thấy đủ 51 key ⇒ **nhìn hai nơi thấy hai sự thật**.
Giá phải trả: 51 key × 1.000 gọi/ngày = **51.000 lượt free nằm không**, còn Gemini bị nện tới cạn.
Vá: `snap_rows` vốn ĐÃ có đủ key của B trước khi đụng A ⇒ **dựng ảnh ngay tại đó**, có thêm key từ A
thì ghi đè lần hai. Và in rõ thành phần ảnh (`gemini=… groq=… cf=…`) để lần sau thiếu là thấy ngay.
**LUẬT: cái gì được dựng ở CUỐI một hàm hay ném lỗi thì coi như không bao giờ được dựng. Dựng phần
chắc chắn có trước, phần bổ sung sau.**

### 7.dx — Key chết hẳn không được nhận ra vì thiếu đúng chữ ký của nó (25/8/2026)
Anh hỏi "sao dashboard không báo Gemini die". Log thật:
`API key not valid. Please pass a valid API key. [reason: "API_KEY_INVALID"]`
Danh sách chữ ký "key chết vĩnh viễn" có `denied · suspended · not enabled · forbidden…` nhưng **không
có `not valid`/`API_KEY_INVALID`** ⇒ key bị xử như chỉ-nghẽn-tạm: cứ thử lại mãi mỗi phiên, và bảng
key vẫn báo xanh. Danh sách đó lại chép tay ở **8 chỗ** trong `key_manager`.
Vá: gộp thành **một hằng số `CHET_HAN`** dùng chung cho cả 8 nhánh, bổ sung `api_key_invalid`,
`api key not valid`, `invalid api key`, `api key expired`, `unregistered`, `key not found`, `revoked`.
Chốt bằng `t_key_chet_han_duoc_nhan_dien` — có cả ca NGƯỢC (429/timeout **không** được coi là chết,
kẻo mất key oan).
**LUẬT: cách kiểm key rẻ nhất là GHI LẠI thứ dây chuyền đã học trong lúc làm việc thật — 0 lượt gọi
thêm. Đi dò 166 key chỉ để biết cái nào chết là trả tiền cho thông tin mình đã có.**

- **Hồ key ảnh/Vision phải xoay theo SỐ LƯỢT ĐÃ DÙNG, không phải offset băm-tên-kênh.** (25/8)
  `_ai_candidates`/`_vision_order` trước trả thứ tự cố định suốt phiên ⇒ một lane render 20 video
  cùng kênh nện đúng `cands[0]` cả 20 lần, tới khi key ấy ăn 429 **hạn mức NGÀY** (nghỉ tới 00:00
  UTC) mới bò sang key kế — đốt cạn từng key một trong khi 51 key khác còn nguyên. Nay `_DUNG`
  đếm trong tiến trình (kể cả lượt hỏng — nhà cung cấp vẫn trừ), key ít dùng nhất lên đầu; băm tên
  kênh chỉ còn để phá hoà giữa 18 lane. Chốt: `t_xoay_key_theo_luot_dung`.

- **Ô nào lấy số từ D1 thì phải ĐỌC LẠI biến đó, đừng chỉ gán.** (25/8) `__d1DangChay`/`__d1Loi`
  được gán từ 24/8 kèm chú thích "Đang chạy và Lỗi cũng lấy từ đây" nhưng **không dòng nào đọc** ⇒
  hai ô vẫn đếm trên danh sách Firestore 200 doc: hiện "⚙️ 0" trong khi D1 thấy 13 job chạy, và
  "❌ 21 lỗi MỚI" trỏ mãi về sự cố 19/8. Kèm theo: "lỗi MỚI" phải tính trên TOÀN bảng
  (`updated_at > MAX(updated_at) của job done-có-file`), không tính theo mốc lấy từ danh sách bị cắt.
  Worker thêm `loi_moi`; đo sau khi vá: `loi=221` nhưng `loi_moi=0`.
- **Deploy hosting phải ghi rõ `--project`.** (25/8) alias đang chọn là `c` ⇒ `firebase deploy`
  trần đẩy vào `mm0-shard-c` chứ không phải `mm0-auto-publisher` như `.firebaserc` mặc định.

- **Lỗi ĐÃ LƯỜNG TRƯỚC và có đường xử lý thì in 1 dòng, đừng in stack.** (25/8) Phiên 02:15 in 39
  vệt Traceback 20 dòng, tất cả là `RateLimited: 429 rate limit daily (cloudflare)` — hệ đổi key
  rồi làm tiếp, không mất video nào. Log trông như 39 lần sập ⇒ soi log tốn công, crash THẬT lẫn
  vào đó thì không ai thấy. `print_exc_gon()` thay cả 25 chỗ; cuối phiên `bao_da_luong()` in tổng
  số lượt để "im lặng" không thành "giấu". Chốt: `t_nen_loi_da_luong_khong_de_quy` — chốt này còn
  bắt cái bẫy tự gây: lệnh thay hàng loạt ăn luôn dòng nằm TRONG hàm mới ⇒ đệ quy vô hạn.

- **Thư viện video lọc theo ngày phải đọc D1, không đọc Firestore.** (25/8) Ảnh chụp: "Tất cả kênh
  (0)" khi lọc *Hôm nay*, còn *7 ngày* ra 85. Biểu thức lọc không sai — **nguồn** sai:
  `__rsJobsData` đọc từ Firestore B, mà hôm nay B ăn 429 nên 399 video làm trong ngày không có bản
  ghi ở B (chúng ở D1 + bản sao B2) ⇒ lọc "hôm nay" trên danh sách chỉ còn video ngày trước = 0,
  còn "7 ngày" vẫn thấy 85 cái cũ. Nay `/api/hot-jobs` trả danh sách từ D1 và **chính SQL đó lọc
  ngày**, dùng đúng cột `updated_at` như ô "📅 Hôm nay" ⇒ hai chỗ không thể ra hai số khác nhau.
  Bản ghi Firestore chỉ còn dùng để bù cột D1 không giữ (ảnh nền, điểm QC, kho chứa). D1 im thì rơi
  về lọc cũ. Đo sau khi vá: 400 video / 45 kênh cho hôm nay. Đệm 5' mỗi mốc lọc (~6,9% trần D1 free).

- **Ô xổ phải TỰ CỘNG ĐÚNG: tổng và từng dòng phải cùng một nguồn.** (25/8) Ảnh chụp: "Tất cả kênh
  (2084)" nhưng từng kênh chỉ 7-15, cộng lại chưa tới 600 — vì tổng đếm ở **kho Drive** còn số mỗi
  kênh đếm trên `__chStats`/danh sách Firestore ~200 doc đã cắt. Nay cả hai lấy từ một truy vấn
  `GROUP BY channel` trên D1 (`/api/hot-chan`), cùng mốc ngày. Đo: 50 kênh, cộng lại 1597 = đúng
  tổng trả về. Chênh với kho Drive (2084 file — 487 cái làm trước khi bật sổ D1) **nói ở tooltip**,
  không giấu vào con số. Số kho Drive vẫn là ô "✅ Video trong kho", đó là câu hỏi khác.

- **Chốt viết ra phải ĐĂNG KÝ trong `main()` — và phải thử PHÁ để biết nó không đậu giả.** (25/8)
  `selftest.main()` gọi tay từng `check(...)`; 5 chốt thêm trong đêm không cái nào được đăng ký,
  lại còn nằm SAU khối `if __name__` nên chưa từng tồn tại lúc `main()` chạy ⇒ suốt đêm báo
  "SELFTEST PASS" trong khi chúng chưa chạy một lần. Nay `t_moi_chot_deu_duoc_dang_ky` soi chính
  file selftest (đối chiếu tập `t_*` với tập đã `check`). Thêm luật: mỗi chốt mới phải chạy một
  lượt **phá bản vá** để xác nhận chốt kêu — chốt `t_moi_lop_toi_deu_noi` bản đầu chỉ khớp độ mờ
  dạng SỐ nên đổi `${.66 * man}` -> `${.66}` vẫn đậu.
- **Hồ key đi qua ảnh chụp D1, không đâm vào project A.** (25/8) Sổ đọc thật phiên 02:15: mỗi luồng
  tính `merge_keys_A=70`, luồng NÀO CŨNG tính (nhánh này lẽ ra chỉ chạy khi hồ key ở B thiếu nhà
  cung cấp, nhưng B cạn hạn mức GHI nên sync A→B hỏng vĩnh viễn ⇒ "cửa sổ tạm" thành thường trực).
  70 × 18 luồng × ~30 phiên/ngày ≈ 40.000 lượt trên trần 50.000 của A — chính nó làm A cạn, kéo
  theo bảng key và danh sách kho Drive (cũng ở A) cùng chết. Nay luồng đầu đọc A rồi chụp vào D1
  (`keys_ghi`/`keys_doc`, hạn 30'), 17 luồng còn lại đọc ảnh chụp = 0 lượt A.
- **Chốt phụ thuộc đồng hồ phải đo CÔNG THỨC, không đo số tuyệt đối.** (25/8) `assert con > 120`
  fail oan trong 2 tiếng trước mốc reset của Google — lúc đó "cạn tới hết ngày" đúng nghĩa chỉ còn
  97 phút. (Cùng loại với lỗi `cf < gg` lúc nửa đêm UTC.) Lưu ý `nghi_key.muc_nghi()` trả **PHÚT**.

- **Ô "⚙️ Đang chạy" bằng 0 vì D1 KHÔNG HỀ CÓ dòng job đang chạy.** (25/8) Soi D1 lúc 3 luồng đang
  render: bảng chỉ có done/failed/ratelimited. Bộ đệm `hot_db` chỉ xả sớm ở trạng thái CUỐI, nên
  dòng trung gian nằm chờ rồi đi cùng lô với dòng `done` của chính job đó và bị đè. ⇒ Đọc số này
  từ D1 mà không sửa gốc chỉ là **đổi chỗ sai**. Nay lượt ghi ĐẦU của mỗi job xả sớm, có nhịp 25s
  (bước plan dựng cả trăm job liền tay — xả từng cái là phá gộp lô: 25 thao tác thành 25 lời gọi).
  Chốt: `t_job_dang_chay_len_d1_ngay` (đã thử phá 2 kiểu, đều bắt được).

- **Dashboard: F5 và thao tác key không được đọc lại cả bảng.** (25/8) Ba khoản lãng phí đo được:
  (a) `getFirestore()` trần chỉ đệm trong BỘ NHỚ TRANG ⇒ mỗi lần F5 nạp lại toàn bộ kênh/key/job
  (~200-500 lượt; F5 20 lần/ngày = 10.000 lượt ≈ 1/5 trần một project). Nay bật `persistentLocalCache`
  + `persistentMultipleTabManager` (IndexedDB): F5 dựng lại từ đệm, listener chỉ kéo phần THAY ĐỔI.
  Trình duyệt chặn IndexedDB thì rơi về `getFirestore` như cũ.
  (b) Thêm/xoá 1 key gọi `__loadKeys()` = `getDocs` trọn bộ `gemini_keys` (166 lượt đọc cho 1 dòng
  vừa đổi). Nay `__rsKeyThem`/`__rsKeyBo` sửa tại chỗ rồi vẽ lại: 0 lượt đọc.
  (c) Đổi tab lọc nhà cung cấp cũng gọi `__loadKeys()` — dữ liệu đã nằm trong bộ nhớ. Nay chỉ vẽ lại.
  Đã có sẵn từ trước: ẩn tab 45s → ngắt listener, tab phụ → 0 lượt đọc, đệm doc lẻ ở localStorage.

- **Hai vòi rỉ lớn nhất — đo bằng sổ, không đoán.** (25/8) Cộng dòng `🧮 Firestore` của cả 18 luồng
  phiên 02:15: **5.885 ĐỌC · 1.957 GHI** một phiên. Trong đó:
  * `nhip_song=832` (42% số ghi) — ghi theo MỌI lần `update_job`, không hãm. ×~30 phiên/ngày ≈
    **25.000 ghi/ngày trên trần 20.000 của B** ⇒ B cạn hạn mức GHI ⇒ `sync_keys A→B` hỏng vĩnh viễn
    ⇒ mỗi luồng tự đọc A (`merge_keys_A=70`) ⇒ **A cạn nốt**. Một vòi rỉ kéo sập hai project.
    Nay hãm 10'/job (dashboard dùng cửa sổ 45' nên vẫn thừa tươi); trạng thái CUỐI luôn ghi ngay.
  * `top_titles=2.842` (48% số đọc) trên project C; ×30 phiên ≈ **85.000/ngày trên trần 50.000**.
    18 luồng hỏi lại đúng một câu giống hệt nhau. Nay đi qua bộ nhớ chung D1 (`nho_ghi`/`nho_doc`,
    hạn 6h) — lượt xem chỉ nhích theo ngày.
  Chốt: `t_hai_voi_ri_da_ham` (đã thử phá 3 kiểu, đều bắt được).

- **`read_channels` phải có đệm tiến trình.** (25/8) Mỗi lane gọi 5 lần (dựng map, chia việc,
  work-steal, re-render, flush), lần nào cũng 40 lượt đọc cho CÙNG danh sách ⇒ `read_channels=440`
  một phiên. Cấu hình kênh đổi theo thao tác tay, không đổi theo giây; quyết định cần tươi
  (pause/target) vốn đi đường `read_one_channel` (1 lượt). Đệm 10' ⇒ 440 → ~90/phiên.

- **`getDocs` không tự hưởng đệm bền — phải đệm-trước ở tầng gdGate.** (25/8) Sau khi bật IndexedDB,
  F5 vẫn 538 lượt server: listener đã rẻ nhưng các `getDocs` một-phát (riêng `__loadKeys` = 220
  lượt/lần mở trang) mặc định luôn hỏi server. Nay `gdGate` trả đệm localStorage khi còn hạn (mặc
  định 30'), chỗ cần tươi truyền `tuoiGiay=0` (nút Kiểm ngay). Máy đo `snapW` cũng phải bỏ qua
  snapshot `fromCache` — không thì F5 đo ra 875 "lượt đọc" tự dọa mình. **Đo thật sau vá: F5 = 2
  lượt đọc server** (trước 559-875), dữ liệu nguyên vẹn 220 key/55 kênh/120 job.

- **Đích sản xuất = ĐỘ ĐẦY KHO (100 long + 300 short/kênh), không phải "đủ 7 ngày đệm".** (25/8,
  anh chốt) Phản áp lực đổi thước đo: sắp kênh theo độ đầy kho (vơi nhất trước = làm đều), hoà thì
  xoay theo băm tên+ngày (không thiên vị bảng chữ cái), chỉ kênh đã ĐẠT CẢ long lẫn short mới
  nhường máy. Khẩu phần round_long/round_short mỗi phiên giữ nguyên nên không kênh nào "ăn một
  phát lên đích". Đích riêng từng kênh đọc từ cấu hình `target_long`/`target_short` nếu có.
  5 kênh toon (HANKTOWN, EXPLAINUSA, TRUETALES, DUMBHISTORY, BALDBANDIT) đã mở pause 25/8 — kho
  đang 0 video nên sẽ được ưu tiên tự nhiên theo luật vơi-nhất-trước.

- **Gương B→B2 TẮT mặc định (25/8).** Mỗi phiên nó quét 7 collection ĐỌC TỪ B để chép — vài nghìn
  lượt đọc B/ngày — trong khi mọi dữ liệu failover đã có đường rẻ và luôn tươi: cấu hình kênh theo
  env `CHANNEL_CFGS`, số đếm/hồ key/danh sách job ở **D1**, kịch bản ở Drive sidecar. B2 chỉ còn là
  bến đọc khẩn (dữ liệu cũ dần); bật lại gương để nghiệm thu lần cuối: `B2_GUONG=on`. Kế hoạch: gỡ
  hẳn B2 sau 1-2 ngày D1 chạy sạch.

- **Bước nào đi mạng theo LÔ (73 kho, 55 kênh…) phải có ngân sách thời gian + chạy song song.** (25/8)
  Plan 07:05Z treo 14,5' ở "đồng bộ dung lượng kho" (73 kho tuần tự, không hạn giờ, rơi đúng chu kỳ
  20h) rồi bị chém ở timeout 18' — và vì `usage_synced_at` chưa kịp đóng dấu nên plan kế dính y hệt:
  **vòng lặp chết ăn trọn các phiên**. Nay: 8 luồng song song, ngân sách 150s, hết giờ lấy phần đã
  xong và VẪN đóng dấu; không dùng `with ThreadPoolExecutor` (shutdown mặc định đợi đủ). Chốt:
  `t_dong_bo_kho_co_ngan_sach_gio`.

- **Bản ghi D1 phải mang đủ CHUẨN UPLOAD: kho chứa + thumb_id + size + QC.** (25/8) Video làm trong
  lúc Firestore nghẽn chỉ có bản ghi D1, mà D1 thiếu 4 trường này ⇒ thư viện hiện "🔍 kho chưa rõ"
  và "🖼 thiếu thumbnail" oan (file .jpg vẫn nằm trên Drive, chỉ mất bản ghi). Nay: 4 cột mới trong
  `render_job` (ALTER TABLE đã chạy), `ghi_job`/`ghi_job_loat` COALESCE để None không đè giá trị cũ,
  `qc` lấy từ `patch.score`, hot-jobs trả kèm và dashboard ghép vào (Firestore vẫn thắng khi có).

- **Thủ phạm THẬT của hai plan chết liên tiếp (07:05Z + 07:28Z) là `_kiem_kho_ngay`.** (25/8) Lượt
  đi bộ 72 kho hằng ngày chạy TUẦN TỰ 12-15 phút, đứng ngay TRƯỚC lệnh xuất matrix ⇒ 18 luồng không
  bao giờ mở, plan chết ở timeout 18', và vì rơi đúng lượt đầu sau mốc reset (chu kỳ 20h) nên "mỗi
  ngày chết một buổi". Cùng công thức sửa với sync dung lượng: 8 luồng song song + ngân sách 240s;
  dở dang thì BỎ NGUYÊN LƯỢT (số thiếu độc hơn không có số). Đã cắm thêm `_moc` quanh mọi bước
  plan để lần treo sau tự khai tên. Chốt: `t_kiem_kho_ngay_co_ngan_sach`.

- **"Kho chưa rõ" + thumbnail "tối thui" = CÙNG MỘT GỐC: bản ghi thiếu, file không thiếu.** (25/8)
  Video làm lúc Firestore nghẽn mất `drive_account` (⇒ 🔍 kho chưa rõ) và `thumb_id` (⇒ thư viện
  rơi về khung frame-0 do Drive tự chọn — đúng lúc màn mở màn còn đen nên "tối thui", trong khi
  ảnh `.jpg` hook sáng đẹp vẫn nằm cạnh video, và lúc ĐĂNG YouTube `main.py` tự tìm `.jpg` theo tên
  từ sidecar nên không ảnh hưởng đăng). Vá: lượt đi bộ 72 kho hằng ngày nhặt kèm map file→kho và
  video→thumbnail (cùng tên gốc), đổ về D1 — **0 lượt Drive thêm**. Chốt: `t_lap_ban_ghi_tu_luot_di_bo`.

- **PLAN LÀ NGƯỜI ĐIỀU PHỐI — TUYỆT ĐỐI KHÔNG RENDER.** (25/8) Hung thủ CUỐI của 3 plan chết liên
  tiếp ở timeout 18' (07:05 · 07:28 · 08:07): `process_requests` render + đẩy kho nhiều phút MỖI
  yêu cầu, ngay trong plan, mà hàng tồn ~25 yêu cầu render-lại từ 24/8 ⇒ plan chết trước khi mở
  matrix, phiên nào cũng chỉ còn luồng sót — "video không tăng, 1 luồng thay vì 18". Kiểm-kho/sync
  chỉ là kẻ tình nghi đứng gần (vẫn đáng vá, đã vá). Nay plan chỉ ĐẾM hàng; lane nhận kênh nào thì
  `process_requests(chi_kenh=...)` xử yêu cầu kênh đó trước khi làm video mới (timeout lane 165').
  Bài học: khi một triệu chứng sống sót qua 2 bản vá, nghi phạm thật thường là kẻ ĐỨNG SAU các mốc
  đo — cắm mốc quanh TỪNG bước rồi để log tự khai. Chốt: `t_plan_khong_render`.

- **Tiến trình phải TỰ KHAI ngăn xếp khi kẹt — cấm đoán.** (25/8) 5 lane toon phiên 08:55 đứng im
  25+ phút không một bản ghi, log GitHub không đọc được khi đang chạy ⇒ chỉ còn nước đoán (và vụ
  plan đã chứng minh đoán trượt 3 lần liền). Nay `faulthandler.dump_traceback_later(600, repeat)`:
  mỗi 10' in ngăn xếp mọi thread vào log; `SIGTERM` (bị chém timeout) cũng in trước khi chết.
  0 chi phí khi không kẹt. Ghi chú cùng phiên: 7 render_request mắc kẹt ở "processing" (3 plan chết
  đánh dấu rồi bỏ) — cần lối tự hồi processing→pending khi quá 2h không nhúc nhích.

- **Khối `if __name__` phải là THỨ CUỐI CÙNG của file — mọi hàm nối thêm phải nằm TRƯỚC nó.** (25/8)
  Hung thủ 5 lane toon câm 40+ phút phiên 08:55: `_toon_long_then_shorts` được nối vào cuối file
  (23/8) SAU khối chạy ⇒ đường `--channel` của matrix gọi hàm chưa được định nghĩa ⇒ NameError bị
  vòng thử-lại nuốt êm, không bản ghi nào. Toon đi đường main()/render_datastory thì không sao nên
  bug nấp 2 ngày — tới lần ĐẦU toon vào matrix (5 kênh mới mở) mới lộ. Chốt: `t_khoi_main_cuoi_file`.

- **Tách nền rig: ĐO màu từ viền ảnh, đừng khoá cứng mã màu.** (25/8) Lượt rig 10:51Z báo "0% khung
  là nền khoá" ở gần hết tư thế. Đo trên ảnh thật: FLUX vẽ nền #38b828 trong khi code khoá cứng
  #00b140 — khoảng cách 87 so với ngưỡng 88, **lọt đúng 1 điểm** nên chỉ 1/11 ảnh sống. Nhà cung cấp
  không hứa sắc độ, chỉ hứa "nền phẳng" — mà nền phẳng thì luôn CHẠM VIỀN. Nay `_mau_vien()` lấy màu
  áp đảo ở viền + đòi viền đồng nhất ≥45% (thấp hơn = FLUX vẽ cảnh, tách sẽ ăn thủng nhân vật).
  Kèm luật chung: **ảnh/lượt hỏng phải GIỮ làm bằng chứng** (`_hong/`), xoá đi là lần sau lại đoán.
  Chốt: `t_tach_nen_khong_khoa_cung_mau`.

- **Multiplane phải đủ 4 DẤU HIỆU CHIỀU SÂU, không chỉ thị sai.** (25/8) Bản đầu chỉ cho lớp gần
  trượt nhanh hơn lớp xa — vẫn trông "ảnh nền + hình dán". Máy đa tầng Disney (1937) có bốn:
  (a) thị sai theo độ sâu; (b) **phối cảnh không khí** — lớp xa bạc màu + phủ sương, mắt đọc chiều
  sâu bằng dấu hiệu này mạnh hơn cả thị sai; (c) độ sâu trường ảnh — lấy nét ở mặt phẳng nhân vật,
  lớp lệch nét nhoè nhẹ; (d) **nhân vật NẰM GIỮA các tấm kính** — lớp `near` vẽ ĐÈ LÊN nhân vật, và
  chính nhân vật cũng chịu phép biến đổi của máy (`camScale`), nếu không thì camera đẩy vào mà nhân
  vật đứng nguyên là lộ hình dán. Chốt: `t_mascot_stage_dong_tung_khung` (kiểm cả 4).

- **Khai báo là Ý ĐỊNH, thư mục mới là SỰ THẬT — lọc asset theo file thật trước khi vào props.** (25/8)
  Pilot 11:07Z chết ở `Error loading image`: sân khấu khai 4 lớp nhưng `far` tách nền hụt nên không
  có file, code vẫn đưa `stages/.../far.png` vào props ⇒ Remotion nạp ảnh không tồn tại, giết cả lượt
  render (cả long lẫn short). Nay lọc theo `os.path.exists` + báo rõ lớp nào thiếu, còn ≥2 lớp thì
  vẫn dựng (chiều sâu vẫn đủ). Tin tốt cùng lượt: bản vá đo-màu-viền cho **12/12 tư thế nhân vật**.

- **Phiên dài giữ khoá `concurrency` làm HUỶ TRẮNG phiên sau.** (25/8) Đo trên GitHub: phiên 08:55
  giữ khoá 150 phút trong khi số lane rơi 18 → 3 → 1 (lane xong việc là THOÁT, runner được trả lại,
  nhưng khoá do lane cuối giữ). **Hai phiên 10:03 và 10:44 bị huỷ trắng** — 2,5 giờ chỉ có một mẻ
  18 lane rồi thoi thóp, 16 chỗ runner bỏ không. Đó là lý do dashboard hiện "Đang chạy: 1", KHÔNG
  phải lane đợi nhau (work-stealing vẫn chạy: xong kênh mình là lấy kênh kế từ hàng chờ nguyên tử).
  Nay ngân sách lane 110'/150' → **60'/75'**, timeout workflow 165' → **90'**: cứ ~80 phút một mẻ
  ĐỦ 18 LANE, không phiên nào bị huỷ. Chốt: `t_phien_khong_giu_khoa_qua_lau`.

- **`set -e` + gán biến từ `$( [ test ] && echo … )` = chết câm.** (25/8) Lượt pilot 11:35Z thoát
  `exit 1` NGAY SAU dòng "SELFTEST PASS", không một dòng lỗi: mã thoát của phép GÁN chính là mã
  thoát của lệnh trong ngoặc, `LAM_LAI=false` → `[ ]` trả 1 → `set -e` giết cả script. Tái hiện
  được bằng 4 dòng bash. Luật: trong bước có `set -e`, cờ tuỳ chọn phải viết bằng `if/fi`, không
  viết bằng `$(test && echo)`.

- **Giọng nhân vật cần CAO ĐỘ, không chỉ tốc độ.** (25/8) `edge_tts.Communicate` vẫn nhận `pitch`
  nhưng hệ chưa bao giờ truyền ⇒ đại bàng khoác lác, gấu mèo láu cá, bà hàng xóm nhiều chuyện đều
  nói bằng đúng một chất giọng đọc bản tin. Nay `synth(pitch=…)` + mỗi vai một cao độ, **hai vai
  bắt buộc lệch ≥12Hz** (chốt `t_giong_nhan_vat_co_cao_do`) — khán giả phân biệt nhân vật ngay
  giây đầu mà không tốn thêm lượt gọi nào. Kèm đổi sang giọng hội thoại (Multilingual/Andrew/Emma)
  thay vì giọng bản tin.
- **Kịch bản skit: 5 luật viral USA.** (25/8) một-sự-thật-chịu-lực (bỏ sự thật ra là truyện sập) ·
  cụ thể thắng chung chung ($4.87 thay vì "phí nào đó") · hai giọng đối lập có tật nói riêng ·
  **câu 4-5 phải LẬT tình huống** (không leo thang phẳng) · câu cuối trích dẫn được một mình, dưới
  9 chữ, không giải thích thêm. Chốt `t_kich_ban_co_luat_viral`.

- **Ghép tiếng vào video PHẢI có `-map`.** (25/8) Video mascot đầu tiên render ra đủ hình, đủ độ dài,
  **có luồng audio** — nhưng `-91dB`, tức câm. Gốc: Remotion xuất video kèm một track âm CÂM; lệnh
  `ffmpeg -i video -i tiếng` không có `-map` thì ffmpeg tự "chọn luồng tốt nhất" và vớ đúng track
  câm đó. Nay `-map 0:v:0 -map 1:a:0` + **đo `volumedetect` ngay sau khi ghép** (sai -map là lỗi im
  lặng: file đúng mọi mặt trừ việc không có tiếng). Chốt trong `t_mascot_khong_ve_lai_nhan_vat`.

- **Thêm tham số thì phải lần tới HÀM LÀM VIỆC THẬT, không dừng ở hàm bọc.** (25/8) Pilot 12:04Z:
  `pitch` được thêm vào `_run` nhưng thân thật nằm ở `_synth_once` — hàm đó chưa có tham số ⇒
  `name 'pitch' is not defined` ở TỪNG câu thoại. Tệ hơn: vòng thử-lại nuốt thành "TTS trả 0 giây",
  nên log nói về TTS trong khi lỗi là NameError của mình. Python không bắt lúc nạp module; nay
  `t_tts_khong_dung_bien_chua_nhan` soi bằng AST (chỉ hàm cấp cao nhất, gom tham số của cả hàm lồng
  và lambda, hiểu closure/AnnAssign — 4/5 ca đầu là báo oan nên phải siết đúng). Đã thử phá: bắt được.

- **Long ≠ short kéo dài — long là TUYỂN TẬP nhiều skit.** (25/8) Pilot: short **ĐẠT** (24,9s, đã đẩy
  Drive) nhưng long ra 22,2s, QC chặn "quá ngắn <45s" — vì dùng chung `generate_toon` vốn viết skit
  18-30 giây theo thiết kế. Nay long = **3 skit, mỗi skit một SÂN KHẤU khác** (vừa đủ dài, vừa đổi
  cảnh nên không chán, 0 lượt vẽ thêm vì sân khấu đã dựng sẵn); skit sau nhận tiêu đề skit trước vào
  danh sách tránh để không lặp ý. Chốt trong `t_mascot_khong_ve_lai_nhan_vat`.

- **Tiền cảnh ĐÓNG KHUNG cảnh, không chắn diễn viên.** (25/8) Soi khung video thật: thùng rác của
  lớp `near` che nguyên thân gấu mèo, chỉ còn cái đầu — đúng về multiplane nhưng sai về bố cục.
  Trong phim 2D tiền cảnh là cành cây góc trên, bụi cỏ mép dưới, khung cửa hai bên. Nay lớp
  `xa >= DEPTH_NV` được che bằng mặt nạ elip: rìa hiện đủ, giữa trong suốt.
- **Cấm chữ trong ảnh nền phải mô tả VẬT THỂ không có chữ, đừng chỉ cấm chung.** (25/8) Biển hiệu
  hiện chữ giả "AT D" dù prompt đã có "no text". FLUX coi lệnh cấm là gợi ý yếu khi cảnh vốn có chỗ
  để chữ. Nay thêm "all signs are completely blank and unmarked, empty storefront boards".

- **Model trả TÊN NHÂN VẬT thay vì A/B: quy ước lại, đừng loại bài.** (25/8) Pilot long: skit 1 đạt,
  skit 2 bị loại liên tiếp với `dialog[i].who phải A/B` — model thấy tên nhân vật nằm ngay trong
  niche ("BALD", "BANDIT") nên dùng luôn tên làm nhãn vai. **Nội dung kịch bản không sai gì cả**,
  chỉ khác nhãn; loại nguyên bài là vứt một kịch bản tốt + một lượt gọi AI. Nay `_chuan_hoa_who()`
  ánh xạ theo thứ tự người nói xuất hiện (đúng 2 người mới đổi, nhiều hơn để validator bắt như cũ).
- **Một skit hỏng không được giết cả bản dài.** (25/8) Cùng ca trên: skit 2 hỏng thì cả lượt long
  chết IM LẶNG, không một dòng nói vì sao. Nay báo rõ, bỏ skit hỏng, dựng bằng số skit còn lại.

- **Đường phụ phải DÙNG LẠI cơ chế xoay key của đường chính.** (25/8) Pilot 12:51Z: 3/3 skit hỏng với
  "You exceeded your current quota" — không phải lỗi kịch bản mà vì pilot truyền thẳng `keys[0]`,
  key đầu cạn là chết cả lượt, trong khi dây chuyền chính vẫn chạy ngon nhờ `key_manager.key_order`
  (ưu tiên key ÍT DÙNG NHẤT). Nay `_viet_skit()` xoay tối đa 8 key, chỉ xoay khi lỗi là **cạn hạn
  mức** (lỗi khác thì báo và dừng, đừng đốt 8 key vào một bài hỏng). Chốt trong
  `t_mascot_khong_ve_lai_nhan_vat`.

- **Giữ nhịp sau punchline — vừa đúng nghề vừa hết trượt sàn QC.** (25/8) Short pilot ra 18,5s, QC
  chặn "quá ngắn <20s": skit viết 18-30 giây nên có lượt rơi sát sàn, mất trắng lượt render vì thiếu
  1,5 giây. Chữa: `HOLD_CUOI=1.3s` sau câu chốt (mọi phim hài đều giữ 1-2 giây trên mặt nhân vật —
  cắt ngay khi dứt chữ là giết tiếng cười), hụt tiếp thì **nới nhịp cuối** tối đa 6s. Tuyệt đối
  KHÔNG kéo giãn lời thoại — kéo lời là hỏng nhịp hài. Nhịp giữa câu cũng nới 0,22→0,34s.

- **HƯỚNG MASCOT CUTOUT ĐÃ BỊ LOẠI (25/8) — lý do phải nhớ để không làm lại.** Anh xem clip demo và
  bác: *"giật giật, không phải phim tôi cần"*. Nguyên nhân kỹ thuật, không phải chỉnh tham số được:
  cách này diễn bằng **đổi ảnh** giữa các tư thế FLUX vẽ RIÊNG (talk_open ↔ talk_closed ở 12Hz).
  Hai bản vẽ không trùng khít nhau (tỉ lệ/vị trí lệch vài pixel) nên đổi qua lại ra **nhấp nháy**,
  không ra "đang nói". Đây là giới hạn cứng của mọi lối "AI vẽ nhiều tư thế rồi swap": muốn mượt
  thì bộ phận phải **BIẾN DẠNG LIÊN TỤC** (xoay khớp / morph), chứ không thể tráo ảnh.
  ⇒ Hướng còn khả thi: nhân vật là **hình vector dựng bằng mã** (SVG/Rive/Lottie) — mỗi khớp nội
  suy được nên mượt tuyệt đối, 0 drift, 0 quota. Đã gỡ toàn bộ code/asset/kênh mascot.

- **Phụ đề phải TỰ BẢO ĐẢM tương phản, đừng trông chờ vào cảnh.** (25/8) Anh mở video thật
  (BRANDEDUSA, cảnh trời xanh chói) và bác: *"sub karaoke màu mờ tịt, chạy không hợp gì cả"*. Soi ra
  `Cinematic.Caption` chỉ có bóng đổ, KHÔNG có nền — nền sáng là chữ chìm; tệ hơn, từ đang đọc tô
  bằng `accent` của kênh, kênh nào accent nhạt thì karaoke **tàng hình** hoàn toàn. Nay ba lớp:
  (1) dải nền mờ phía sau, (2) viền chữ 7px, (3) **từ đang đọc có VIÊN NỀN màu accent + chữ tối** —
  nổi bật bất kể accent sáng hay tối, bất kể cảnh sáng hay tối. Đã render ảnh so sánh cũ/mới trên
  cả hai loại nền trước khi đẩy. Khoảng cách chữ 9px → 11px (bản cũ chữ dính nhau).

- **Đổi NGUỒN danh sách thì phải soát mọi nút tra theo nguồn cũ.** (25/8) Sau khi thư viện chuyển
  sang lấy danh sách từ **D1** (để lọc "Hôm nay" không còn ra 0), phần lớn thẻ là job **chỉ có ở D1**.
  Ba nút vẫn tra bằng `__rsJobsData` (danh sách Firestore) rồi `if(!j) return;` — **thoát không một
  lời**: bấm "🖼 Tạo lại thumbnail" và "🔄 Render lại" thì không có gì xảy ra, không báo lỗi, người
  dùng tưởng nút hỏng. Nay có `window.__timJob()` tra CẢ hai nguồn, và **không đường nào được thoát
  im lặng** — mọi nhánh đều nói ra chuyện gì đang xảy ra.

- **Lọc dữ liệu theo HÌNH DẠNG, đừng xoá theo TÊN từng trường.** (25/8) Ô xổ báo "57 kênh" trong khi
  chỉ có 55: sổ `render_stats/{owner}` chứa khoá KÊNH (`{COSMOS:{l,s}, …}`) lẫn trường phụ `at`
  (dấu thời gian) và `up`. Bản cũ chỉ `delete d.up` rồi lấy nguyên `Object.keys()` làm danh sách
  kênh ⇒ **`at` thành một "kênh" 0 video** nằm cuối ô xổ. Xoá theo tên là đuổi hình bắt bóng —
  trường mới thêm sau lại lọt. Nay giữ khoá nào có giá trị là object mang `l`/`s` (đó mới là bản
  ghi đếm của một kênh). Đo sau vá: 48 khoá, 0 rác.

- **Chữ karaoke đang chạy: dùng BẢNG MÀU đã sàng, KHÔNG dùng accent của kênh.** (25/8) Anh mở video
  BRANDEDUSA (cảnh biển Coca-Cola đỏ rực): từ đang đọc tô bằng accent navy ⇒ tàng hình. Gốc sai:
  lấy **màu nhận diện** làm **màu chữ chạy** — accent phục vụ logo/khung, chữ chạy chỉ có một việc
  là ĐỌC ĐƯỢC. Bản vá 1 của tôi (hộp + viên nền + vành trắng) bị anh bác đúng: nặng nề, xấu hơn.
  Bản 2 theo cách kênh lớn Mỹ làm: **không hộp, không viên nền** — chữ trắng đậm + viền tối 5px,
  từ đang đọc đổi màu. Đa dạng giữa kênh bằng bảng 6 màu rực (mỗi kênh một màu cố định theo băm
  tên); màu tự đặt mà độ sáng < 0.52 thì BỎ, quay về bảng. Chốt `t_chu_chay_luon_doc_duoc` kiểm cả
  độ sáng từng màu trong bảng. Đã render ảnh so 3 bản trên 3 loại nền trước khi chốt.

- **Cỡ chữ phải SUY TỪ CHỮ, đừng đặt sẵn rồi cầu may.** (25/8) Anh gửi ảnh: tiêu đề
  "SEMICONDUCTORS" bị cắt cụt cả đầu lẫn đuôi. Thẻ tiêu đề đặt cỡ **cố định 100-116px** bất kể độ
  dài; một từ 14 ký tự ở 116px chiếm ~1.010px trong khi khung 1080 trừ lề chỉ còn 840px. Tiêu đề do
  AI viết nên độ dài KHÔNG đoán trước được. Nay `_coVua()` tính theo **TỪ DÀI NHẤT** (từ đơn không
  xuống dòng được), sàn 38px, và mỗi biến thể truyền **lề thật** của nó. Chữ ngắn giữ nguyên cỡ lớn
  (CHIPS vẫn 116px), chỉ từ dài mới co (SEMICONDUCTORS → 96px). Chốt `t_the_tieu_de_khong_tran_khung`
  kiểm cả hai đầu: từ dài phải co, **từ ngắn không được co oan**.

- **HÀO CẠNH TRANH: bản ghi chính phủ Mỹ THẬT trên màn hình.** (25/8, anh nhận xét 55 kênh "quá tầm
  thường") Đúng: 55 kênh dùng chung công thức của hàng vạn kênh faceless — footage Pexels + chữ động
  + giọng AI. Ai cũng lấy được cùng bộ footage nên không có gì để thuật toán ưu ái. Thứ **không copy
  được** không phải footage đẹp hơn, mà là bản ghi gốc hiện trên màn hình. `du_lieu_mo.py` nối 4
  nguồn, **đã gọi thật trước khi viết code**, không cần một key nào:
  * **USASpending** — mọi đồng tiền liên bang (thử: Humana $51.269.205.263 từ Bộ Quốc phòng)
  * **SEC EDGAR** — số liệu trong hồ sơ công ty đại chúng (thử: doanh thu Apple 11 kỳ)
  * **BLS** — CPI/xăng/nhà/thất nghiệp chính thức (25 lượt/ngày không key)
  * **Archive.org** — phim tư liệu công cộng
  (Census trả 302 — cần key free, để lại.) Luật kèm theo: **dữ liệu là gia vị, không phải xương
  sống** — mọi hàm hỏng thì trả rỗng, chốt `t_du_lieu_mo_khong_lam_gay_day_chuyen` canh bằng AST.

- **CF chặn prompt ≠ hết đường vẽ — phải nhảy sang Gemini.** (25/8) Bốn kênh toon (BALDBANDIT,
  TRUETALES, HANKTOWN, DUMBHISTORY) cùng lúc ra `chỉ vẽ được 0/16 khung`. Gốc: khi CF trả về không
  phải ảnh (bộ lọc prompt của họ chặn — mã 8007 và họ hàng), `_generate_image_ai` **`return False`
  ngay**. Chú thích cũ lập luận *"đổi key cũng vô ích vì cùng prompt"* — đúng với key CF khác nhưng
  **sai với Gemini**: nhà cung cấp khác, bộ lọc khác, thường vẽ được đúng prompt đó. Trả False sớm
  là tự cắt đường lui duy nhất ⇒ mất trắng cả video. Nay: đánh dấu `_cf_chan_prompt`, **bỏ qua mọi
  key CF còn lại** (cùng prompt thì cùng kết quả, khỏi đốt lượt) nhưng **đi tiếp tới Gemini**.
  Chốt `t_cf_chan_prompt_van_con_duong_gemini`.

### RankedShort — bảng tier (25/8)
- **Hàng tier rỗng vẫn được vẽ** → danh sách dùng S/A/B/C để lại nguyên hàng D trống, mất 1/5 màn hình dọc.
  RankedShort nay lọc `hangCoDo` = chỉ hạng có item. `build_ranked_props` cho kịch bản chỉ định `tiers`.
- **Băng chữ karaoke đè bảng**: Karaoke neo `bottom 200` cao ~2 dòng, bảng neo `bottom 130` → chữ nằm chồng
  hàng cuối. Có `subs` thì đáy bảng lùi lên 380.
- **Chữ trong thẻ bẻ giữa từ** ("Globalfound / ries"): thẻ rộng 260 + co chữ theo CẢ CHUỖI. Nay co theo
  **từ dài nhất** (nhiều từ thì xuống dòng được) + rộng 330 + sàn 26px. Cùng nguyên tắc với tiêu đề Cinematic.
- **QC báo "quá ngắn 0.0s" cho file render THÀNH CÔNG**: lệnh render chạy `cwd=engine-remotion` nên đường dẫn
  ra tương đối rơi vào `engine-remotion/out`, còn `qc()` tìm ở `render-pipeline/out`. Đường dẫn ra phải TUYỆT ĐỐI.

### BA tiêu đề chồng nhau lúc mở đầu (25/8 — anh phát hiện bằng mắt, log không hề báo)
`Bookend` (24/8) vẽ thẻ mở đầu CÓ TIÊU ĐỀ cho mọi short, nhưng lớp phủ intro cũ của từng component
vẫn còn và cũng vẽ tiêu đề, cộng header luôn bật → **3 bản tiêu đề đè nhau suốt introSec giây đầu,
ở 6/7 component short** (Longshot · Pulse · Scaled · Ranked · Swarm · ThenNow).
- **Luật**: `Bookend` là NƠI DUY NHẤT vẽ tiêu đề lúc mở đầu. Lớp phủ intro riêng chỉ giữ emoji motif
  (đẩy `paddingBottom: 620` để không nằm sau chữ); header tự ẩn bằng `display: f < introF ? "none"`.
- **Chốt**: `t_bookend_la_noi_duy_nhat_ve_tieu_de_mo_dau` — đã thử làm hỏng lại, chốt bắt đúng.
- **Bài học rộng hơn**: thêm một lớp dùng chung cho N component thì phải GỠ phần lớp cũ làm trùng ở
  cả N, không chỉ ở component đang test.
- Chú thích trong JSX phải bọc `{/* */}`. Để trần `/* ... <Tag> ... */` làm esbuild đọc thành thẻ thật
  và gãy build toàn bộ engine.

### Phiên 14:06 25/8 — hai lỗi im lặng (không lane nào fail, không ai biết nếu không soi log)

**1. `_extract_json` trả list → giết luồng (5 lần/phiên, toon long)**
Gemini thỉnh thoảng trả thẳng MẢNG dialog thay vì object. Cả 21 chỗ gọi đều `-> dict` rồi `.get()`
ngay dòng sau, mà `.get` nằm NGOÀI vùng try bọc `_extract_json` → `AttributeError: 'list' object has
no attribute 'get'` bay thẳng lên, không rơi vào nhánh "invalid JSON, thử lại".
- **Sửa tại một chỗ, chữa cả 21**: `_extract_json` luôn trả dict — mảng bọc đúng 1 object thì bóc ra
  dùng; còn lại ném `ValueError` để vòng lặp gọi lại kèm phản hồi (cơ chế đã có sẵn).
- Chốt `t_extract_json_luon_tra_dict`.

**2. Chống trùng bị vô hiệu 63 lần/phiên — thiếu ĐÚNG MỘT DÒNG cờ**
`enqueue.py` (chống trùng + đẩy kho) chạy TRONG render lane, đọc sổ `videos` qua `client_publish()`.
Hàm đó chỉ trỏ Project C khi `SHARD_PUBLISH=1`, không thì rơi về A. `render_cron.yml` truyền sẵn
creds + id của C nhưng **thiếu cờ** → A cạn hạn mức → 429 → 63 lần in "không tra được sổ chống trùng
— vẫn upload". Không Traceback, không lane fail, chỉ có nguy cơ video trùng trong kho.
- **Luật**: step nào truyền `FIREBASE_PROJECT_ID_C` thì BẮT BUỘC truyền `SHARD_PUBLISH`, trừ script
  tự dựng client C trực tiếp (migrate_to_shards.py).
- Chốt `t_workflow_dung_project_C_phai_bat_co` — miễn trừ theo NỘI DUNG script, không theo tên file.

*Không phải lỗi (đã xác minh, đừng vá lại)*: 37 dòng "B cạn hạn mức ngày — KHÔNG rơi về Project A" là
ĐÚNG thiết kế cách ly 3 project; tầng trên lật gương B2 (19 lần `🔀 FAILOVER` trong cùng phiên).
