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
