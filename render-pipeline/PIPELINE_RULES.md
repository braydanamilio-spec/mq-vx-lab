# MM0 — QUY TRÌNH SẢN XUẤT VIDEO A-Z (repo rule)

> File này = luật/quy trình cho nhà máy render. GIỮ LOCAL (gitignored) — không đẩy public.
> Moat thật (SYSTEM prompt Gemini) nằm trong GitHub Secret `GEMINI_SYSTEM_PROMPT`, KHÔNG ở đây.

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
- Ảnh CC0/PDM (khỏi ghi nguồn); nhạc Kevin MacLeod CC-BY (ghi nguồn trong description). Nội dung gốc → monetize OK.
- Xóa Drive: CHỈ khi đã đăng ≥2 nền tảng (YouTube + FB/IG). Giữ lâu (archive).
- **ẢNH khớp ĐỊNH DẠNG + NỘI DUNG**: short lấy ảnh DỌC (aspect_ratio=tall), long lấy ảnh NGANG (wide) — đã làm trong fetch_image(orient). Query ảnh phải BÁM đúng câu đang nói (Gemini visual.query = 2-5 từ cụ thể, danh từ hình ảnh được — không trừu tượng). Mục tiêu: ảnh khớp nội dung ~100%.
- **KHÔNG CHE KHUẤT + ẢNH ĐÚNG KÍCH THƯỚC (bắt buộc kiểm mỗi thay đổi layout, cả long 16:9 lẫn short 9:16)**:
  - Phụ đề karaoke maxWidth 80% canh giữa (không chạm handle @/mép); handle @ góc phải-dưới; nhãn giá trị không tràn mép; năm góc phải-trên; hero góc phải — các lớp KHÔNG đè nhau.
  - Ảnh (nền/minh hoạ/hero) **KHÔNG quá nhỏ, KHÔNG tràn khung**: nền full-bleed objectFit cover; ảnh minh hoạ short = ~74% rộng khung dọc, long = hộp cố định phải; hero long ~68% cao. Ảnh phải khớp hướng (short=dọc, long=ngang).
  - QC-vision là CỔNG KIỂM BẮT BUỘC: chấm occlusion + ảnh quá nhỏ/tràn + text tràn mép. Ngưỡng nới (chỉ loại video hỏng thật) nhưng LUÔN log điểm + issue để soi.
- **10 KÊNH PHẢI KHÁC BIỆT RÕ** (không cùng 1 motip lặp lại): mỗi kênh KHÁC về kiểu đồ hoạ + layout + màu + chuyển động, không chỉ đổi accent. Ý tưởng phân hoá: STATEWARS→BẢN ĐỒ bang (WorldMapRace + states-10m.json, đã có engine); DATARACE→bar-race vàng/tiền; MONEYMOVES→ticker giá/hoá đơn; POWERPLAY→bong bóng market-cap/logo; GRIDIRON→bảng điểm sân cỏ; SCREENKINGS→poster/box-office; PAYCHECK→cuống lương; BODYUSA→infographic cơ thể; RIDEUSA→showcase xe; EATSUSA→thẻ menu/calo. → CẦN build dần, mỗi kênh 1 template engine riêng (KHÔNG dùng chung RaceLong cho cả 10).

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
- **1 phiên chạy tay CŨ khoá ma trận, chặn 16 kênh mới nhiều giờ liền** (19/8): kích `render_cron` tay (`force=1`) LÚC 07:31 để test B-shard — TRƯỚC KHI seed 16 kênh mới (wave1/2/3). `plan_mode` đọc `FB.read_channels()` MỘT LẦN lúc dispatch → matrix khoá cứng 10 kênh cũ, dù seed thêm kênh sau đó session ĐANG CHẠY không bao giờ thấy được (matrix cố định từ lúc plan chạy). Cộng thêm session này chạy TRƯỚC lúc push round-cap → không giới hạn, 5/10 kênh cắm cúi chạy tới đích hàng giờ liền, chiếm slot. LUẬT: **kích render tay để test → luôn kiểm sau đó có kênh MỚI thêm vào không; nếu có, đợi phiên đó tự xong (đọc `gh run list --status in_progress`) rồi mới seed/kích tiếp**, tránh 1 session cũ "khoá" danh sách kênh cả nhiều giờ. Đây cũng là lý do đổi gate sang `has_active_render` (dòng trên) — quan trọng: **cờ này chỉ mở phiên MỚI khi phiên CŨ đã xong hẳn — 1 phiên "ma" (dở dang lâu, dù đang chạy thật không lỗi) vẫn chặn phiên mới**, không phải bug, là thiết kế chống chồng phiên.
