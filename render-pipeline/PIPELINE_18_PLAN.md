# PIPELINE 18 KÊNH — RÀ SOÁT & PLAN CHUẨN (9/9/2026)

Anh yêu cầu: rà lỗi tiềm ẩn · pipeline chuẩn 18 kênh · method đẩy GitHub render · QC visual
trước+sau · không cạn ý tưởng · hook viral USA · long+short (short cắt từ long) · thumbnail ·
fileupload chuẩn · 5 mẻ/ngày × 18 luồng · fix triệt để Firebase quota.

Mọi con số dưới đây là ĐO, không phải cảm giác.

---

## 1. TRẠNG THÁI TỪNG TRỤC (đo 9/9)

| trục | trạng thái | số đo |
|---|---|---|
| **Long + Short** | ✅ xong | mỗi bộ = 1 long (16:9, ~60–80s) + 3 short (9:16). `bo_1_3` |
| **Short cắt TỪ long** | ✅ xong | short đọc `v11L_*.json` của long, KHÔNG gọi CF lại (§17.11) |
| **Short hay nhất** | ⚠ một phần | short cắt theo CHƯƠNG của long; chưa chấm-chọn 3 chương HAY NHẤT |
| **Thumbnail** | ✅ xong | `v11L_*.jpg` + `v11_*.jpg`, lấy khung nhịp đỉnh |
| **Fileupload (.tai.json)** | ✅ xong | 3 nền tảng: YouTube (title+desc+tags) · FB (`noi_dung`) · IG (`chu_thich`+`the`) · `dang_duoc` |
| **QC trước (props)** | ✅ xong | `qc_hinh.truoc()` — chạy ở workflow trước khi giao |
| **QC sau (pixel)** | ✅ xong | `qc_hinh.sau()` — soi 6 khung pixel, in `::warning::` nếu lỗi |
| **Nền 100% ảnh thật** | ✅ xong | 12–14/14 nhịp ảnh tư liệu, 0 cặp liền trùng, dải ảnh 56% |
| **Hook viral USA** | ✅ xong | 24 khuôn hỏi/lời hứa, đơn vị Mỹ, số kèm đơn vị, người xem "you" |
| **5 mẻ × 18 luồng** | ✅ vừa làm | 10 mốc cron = 5 mẻ × 2 (idempotent), `max-parallel: 18` |
| **Không cạn ý tưởng** | ⚠ có trần | 2.310 chủ thể đạt × 24 khuôn = **55.440 bộ = 221.760 clip** = 205 ngày |
| **Firebase quota** | ⚠ nhiều guard, chưa 1 chốt | Python có `con_ngan_sach` (50k đọc); worker+dashboard là nguồn riêng |
| **GitHub render XANH** | ❌ chưa | 16/16 đỏ tới 9/9 (edge-tts, đã sửa); **phải đợi cron** (§8) |

---

## 2. HỒ Ý TƯỞNG — KHÔNG VÔ HẠN, NHƯNG 205+ NGÀY VÀ CÒN NỞ

```
chủ thể trong cây hạng mục : 42.344
đã sàng chuyện             : 13.070  (còn 29.274 chưa sàng — 18% đạt)
ĐẠT ngưỡng (≥8 câu nhân quả): 2.310
× 24 khuôn hỏi             : 55.440 bộ = 221.760 clip
```

5 mẻ × 18 kênh × 3 tập = 270 bộ/ngày → **205 ngày** mới cạn một vòng, và hồ CÒN NỞ mỗi lượt
sàng nền. §13.18: một chủ thể × 24 khuôn KHÔNG phải trùng lặp — mỗi khuôn là một "tập" khác
của cùng chương trình, miễn video trong CÙNG kênh không giống hệt nhau (24 khuôn lo việc đó).

**Nút thắt thật KHÔNG phải ý tưởng mà là ẢNH**: 2.310 chủ thể có ≥8 ảnh, nhưng chủ thể mỏng
ảnh (Atari 3 ảnh) vẫn phải quay vòng. Đây là giới hạn của NGUỒN (ảnh PD/CC0), không phải bộ lọc.

---

## 3. FIREBASE QUOTA — PHÂN TÍCH & PLAN "TRIỆT ĐỂ"

Đo đường ghi render: `_mo_so` + `_chot_so` = **2 ghi/bộ**. 5 mẻ × 18 × 3 = 270 bộ → **540
ghi/ngày**, dưới trần 20.000. Đường render KHÔNG phải thủ phạm.

"Cạn khi chưa làm gì" = nguồn ĐỌC nền, ba lớp:

| lớp | trạng thái | rủi ro còn lại |
|---|---|---|
| Python (render/dọn) | `con_ngan_sach` trần 50k, dừng việc phụ ở 80% | thấp |
| Worker Cloudflare | KV cache 5' + throttle quét kho 2h (đã làm) | trung bình — chưa có chốt đọc toàn cục |
| Dashboard (client SDK) | `videos` limit(80), `subCho` lọc status | onSnapshot còn tính đọc mỗi lần ghi khi tab mở |

**Plan triệt để (chưa làm, cần phiên riêng — RỦI RO cao nếu vội):**

1. Worker: thêm bộ đếm đọc/ghi toàn cục vào KV (`quota:doc:<ngày>`), mọi proxy Firestore
   +1 và TỪ CHỐI ở 90% — chốt cứng như `con_ngan_sach` phía Python.
2. Dashboard: đóng onSnapshot khi tab ẩn (`visibilitychange`), mở lại khi hiện — cắt đọc
   khi anh để tab chạy nền.
3. health_guardian: xác nhận index `owner+status+created_at DESC` đã DEPLOY (§17.14), nếu
   chưa thì mỗi giờ nó đọc 200 doc = 4.800/ngày.

---

## 4. METHOD ĐẨY GITHUB RENDER (chuẩn, không vi phạm §8)

```
1. Sửa code ở máy → python3 selftest.py (một mình, không song song — flock chung)
2. git add ĐÍCH DANH tệp (không -A, §15.18) → commit → git push
3. KHÔNG `gh workflow run` để thử (§8). Đợi cron mốc kế.
4. Sau cron: gh run list --workflow render_comic_18.yml --limit 1
   → đỏ thì gh run view <id> --log-failed, đọc GỐC, sửa, đợi mốc sau.
```

Cổng TRƯỚC render (`selftest · kiem_phim · kiem_nen · kiem_tdz`) chặn bản hỏng trước khi
đốt 5h runner (§16.7).

---

## 5. LỖI TIỀM ẨN ĐÃ SỬA HÔM NAY (9/9)

edge-tts thiếu Sec-MS-GEC (16/16 đỏ) · ảnh phụ đi vòng qua cổng · mốc trục bị che · thẻ logo
dưới bong bóng · trần bốc ứng viên so_luong=6 · đơn vị mét (cả gạch nối) · hook bịa đơn vị ·
số hiệu model (Atari/B-17) làm thẻ số · giọng đọc chậm -5% → +5% · đạo cụ vector đè ảnh ·
dải ảnh dọc 32% → 56% · nửa người góc trái · 4 gốc hạng mục hỏng · selftest gọi mạng (treo
runner) · thẻ số lấy số hiệu toà nhà/ngày.

Mỗi lỗi có cổng selftest, **mọi cổng đã thử ngược**.

---

## 6. CÒN LẠI (ưu tiên giảm dần)

1. **Đợi cron xác nhận GitHub XANH** — không bấm tay (§8).
2. **Firebase triệt để** — 3 việc mục 3, phiên riêng, không vội.
3. **Kênh survive** — 3 gốc toàn thương vong, chọn chủ thể >20 phút (đã tạo task).
4. **18 kênh chỉ 2 lời hứa** (vanished 11/unsolved 7) — thêm lời hứa cho đa dạng thật (§14.1).
5. **Short HAY NHẤT** — chấm 10 chương của long, cắt 3 chương điểm cao nhất thay vì 3 đầu.
6. **Tag #Shorts trên long 16:9** — long không phải Short, bỏ tag ấy ở bản dài.
