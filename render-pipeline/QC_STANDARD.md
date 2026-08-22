# 📏 QC_STANDARD.md — Chuẩn chất lượng & chính sách kiếm tiền (toàn hệ 40 kênh)

> Chốt ngày 20/8/2026. File này là **tiêu chuẩn bắt buộc** — thêm kênh/engine mới PHẢI đạt đủ 5 cổng dưới.
> Xem thêm: `PIPELINE_RULES.md` (rule vận hành), `CHANNEL_METHODS.md` (cách thêm kênh), `ERROR_PLAYBOOK.md`.

---

## 1. Năm cổng QC (thứ tự chạy)

| # | Cổng | Ở đâu | Chặn cái gì | Lỗi/hết quota thì |
|---|------|-------|-------------|-------------------|
| 1 | **Tự chấm điểm** | `content_brain.generate_doc()` | accuracy < 92 hoặc tổng < `MIN_SCORE` → viết lại | viết lại tối đa `MAX_TRIES` |
| 2 | **Kiểm chứng độc lập** | `content_brain.audit_doc()` | fact bịa, rủi ro quảng cáo, suy đoán nói như thật | **fail-open** (cho qua) |
| 3 | **Ảnh khớp chủ đề** | `qc_vision.verify_image()` | ảnh không đúng nội dung câu | fail-open |
| 4 | **Kỹ thuật** | `datastory_ci.qc()` | thiếu giây / mất tiếng / sai khung hình | **CHẶN** (lỗi thật) |
| 5 | **Hình ảnh tổng thể** | `qc_vision.check_visual()` | chồng chéo, chữ tràn, khung đen | fail-open |

**Vì sao cổng 2/3/5 fail-open**: chúng là *lớp tăng cường*. Nếu hết quota Gemini mà chặn cứng thì cả dây
chuyền đứng — thiệt hơn lợi. Chỉ cổng 4 (kỹ thuật) là chặn tuyệt đối vì file hỏng thì đăng cũng vô nghĩa.

### Cổng 2 quan trọng nhất — vì sao
`self_score` do **chính model vừa viết** tự chấm → một con số **bịa nhưng viết tự tin** vẫn tự cho 92+.
Đây là điểm yếu cố hữu, **không sửa được bằng siết prompt viết**. `audit_doc()` gọi 1 lệnh Gemini RIÊNG
với vai *người soi độc lập* (không dính dáng bản nháp), bắt 3 nhóm:
- (a) số liệu / mốc / kỷ lục / tên vụ án **sai hoặc không kiểm chứng được**
- (b) **rủi ro quảng cáo**: bi kịch–nạn nhân thật kể chi tiết, bạo lực/tội phạm chi tiết, chính trị đảng
  phái, tư vấn y tế–tài chính, nội dung người lớn, framing miệt thị nhóm người
- (c) chuyện **còn tranh cãi/suy đoán** nhưng nói như sự thật chắc chắn (thiếu "có thể / giới khoa học tin")

Chỉ soi bản **đã qua cổng 1**, tối đa **2 lượt/video** → tốn tối đa 1–2 lệnh Gemini/video.

---

## 2. RULE CỨNG: mọi lệnh gọi mạng PHẢI có timeout

> Bài học 20/8 — **30/40 kênh chưa từng ra nổi 1 video** chỉ vì rule này bị bỏ sót.

Lệnh gọi Gemini/HTTP **không timeout** thì khi mạng chập chờn nó **treo vĩnh viễn** — và vì *không ném lỗi*
nên **mọi `try/except`, retry, fallback bên dưới đều vô dụng**. Job đứng im ở `writing`/`qc` tới khi bị
GitHub giết sau 6h. Triệu chứng nhận biết: job chết hàng loạt với step `"⏱ Quá 6h — job treo"`.

| Nơi gọi | Timeout | Hằng số |
|---------|---------|---------|
| `content_brain` — 13 lệnh `generate_content` | 180s | `GEN_OPTS` |
| `qc_vision` — `check_visual` / `verify_image` | 30s / 45s | inline |
| `datastory_ci` — Nano Banana vẽ ảnh | 120s | `http_options` |

**Thêm bất kỳ lệnh gọi API mới → BẮT BUỘC đặt timeout ngay từ dòng đầu.** Không có ngoại lệ.

---

## 3. Chống "nội dung sản xuất hàng loạt" (rủi ro kiếm tiền LỚN NHẤT)

40 kênh **cùng một chủ** là thứ YouTube soi kỹ nhất (chính sách *inauthentic / mass-produced content*).
Từng video sạch **vẫn có thể bị đánh giá theo cả mạng lưới**. Ba lớp khác biệt hoá đang áp dụng:

1. **Giọng đọc riêng từng kênh** — `render_channels.voice` + `voice_rate`, map ở `RS_VOICES`
   (dashboard). Đã verify **40/40 cặp (giọng, tốc độ) khác nhau**, 21 kênh `doc` trải đủ **16 giọng Mỹ
   người lớn CÓ THẬT**.
   ⚠️ **Bắt buộc đối chiếu `edge_tts.list_voices()` thật trước khi thêm giọng** — 9 tên giọng "hợp lý"
   từng chọn hụt đều **không tồn tại**, dùng vào là hỏng TTS cả kênh.
2. **Khác biệt hình ảnh** — `mode` trên engine Cinematic: `duel` (đối đầu 2 phe), `file` (hồ sơ giải mật,
   chữ máy đánh chữ) và `host_prompt` (nhân vật dẫn nhất quán, Nano Banana). Thêm kênh doc mới → nên
   cấp một `mode`/motif riêng, **đừng để trùng khuôn kênh cũ**.
3. **Khác biệt màu/brand** — `RS_BRANDS[].a` phải **không trùng** kênh nào khác (đã dọn 7 cặp trùng).

**Kiểm nhanh trước khi thêm kênh** (chạy trong console dashboard):
```js
const A=(window.__rsChannelsData||[]);
new Set(A.map(c=>c.voice+"|"+c.voice_rate)).size === A.length   // phải là true
```

---

## 4. Chuẩn "niche sạch" khi thêm kênh mới

Trường `niche` không chỉ là chủ đề — nó là **hàng rào chống bịa** đưa thẳng vào prompt. Bắt buộc có
mệnh đề `STRICT:` nêu rõ **nguồn thật phải bám** và **cái gì cấm**. Ví dụ đang dùng:

- `DEFENSEUSA` → "cite the real program/unit cost/source (DoD budget documents, GAO reports, CBO) —
  never invent a cost figure; factual and neutral, **never political commentary**"
- `CRIMEUSA` → "cite the real source and year (FBI UCR, DOJ, BJS) — … **never sensationalize or target
  a specific real neighborhood/address**"
- `RULEDUSA` → "name the actual court/agency + year … **NEVER invent a ruling or case name**"

**Ba nhóm chủ đề cần câu STRICT mạnh nhất**: tội phạm/an toàn, thiên tai, quân sự/ngân sách — vì bản thân
chủ đề đã sát ranh giới quảng cáo. Cách an toàn đang dùng: **luôn ở tầng thống kê tổng hợp**
(tỷ lệ, chi phí, so sánh theo bang) — **không kể chuyện nạn nhân cụ thể**.

---

## 5. Checklist bắt buộc khi thêm kênh mới

- [ ] `niche` có mệnh đề `STRICT:` + nêu nguồn thật cụ thể
- [ ] `voice` + `voice_rate` **không trùng** kênh nào (đối chiếu `RS_VOICES`, verify giọng có thật)
- [ ] `accent` **không trùng** màu kênh khác trong `RS_BRANDS`
- [ ] Nếu là `format:"doc"` → cân nhắc cấp `mode` hoặc motif riêng, tránh trùng khuôn
- [ ] `make_long`/`long_target` đúng quy ước (doc = long + short; motif riêng = short-only)
- [ ] Đồng bộ **cả 2 nơi**: `RS_PRESETS` + `RS_BRANDS` (dashboard) **và** doc Firestore `render_channels`
- [ ] Category YouTube (`RS_BRANDS[].cat`) khớp nhóm kênh anh em cùng format
- [ ] Mọi lệnh gọi API mới trong engine → **có timeout**

---

## 6. Việc còn treo (chưa xử, cần quyết định)

- `gemini_keys` / `storage_accounts` vẫn nằm ở **Project A** thay vì B theo kiến trúc shard — chưa rõ cố
  ý hay sót. Đổi mà không kiểm chứng dữ liệu thật ở B có thể làm **chết toàn bộ key** → cần xác nhận trước.
- `auto_enqueue.py` đọc `yt_queue` **không giới hạn** — cần biết queue có tự dọn sau khi đăng không thì
  mới quyết được có nên chặn giới hạn (chặn ẩu sẽ **làm yếu khả năng chống đăng trùng**).
- `publish_social._post_one()` chưa có khoá nguyên tử đầy đủ như `run_queue()` — cửa sổ đăng trùng hẹp
  hơn nhưng chưa đóng hẳn.

## §TOON (22/8) — chuẩn nghiệm thu format hoạt hình skit
1. Mở đầu ≤1s phải thấy khung vẽ + title hook (không thẻ trơn, không im lặng >1.2s).
2. Thoại nghe rõ 2 giọng phân biệt; phụ đề khớp câu; punchline nằm CUỐI.
3. Khung vẽ: đúng 2 nhân vật thương hiệu, không dị dạng tay/mặt nặng, không chữ vô nghĩa lộ ngoài
   vùng title card. >40% khung hỏng = video bị loại từ pipeline (đã enforce trong _toon_build).
4. Long: mỗi skit có title card riêng, chuyển skit có nghỉ ~1s; tổng 3 skit.
5. Số đo chuẩn: short 18-35s · long 60-110s · QC score ≥90.
