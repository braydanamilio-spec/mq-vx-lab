# KẾ HOẠCH BẬT 50 KÊNH THẾ HỆ 2 — ĐƯỜNG AN TOÀN NHẤT (26/8/2026)

> Anh chọn "an toàn nhất". Nguyên tắc: **không bật 50 kênh chưa từng chạy cùng một lúc**, và
> **không xoá gì cho tới khi có bản thay thế đã chứng minh được**.

## Vì sao không bật cả 50 ngay
50 kênh × 18 lane = mọi lane đều là kênh chưa từng chạy thật. Nếu có một lỗi chung (kiểu
`vang is not defined` hôm 25/8, hay `doc_kenh` tra không ra hôm nay) thì mất trọn một phiên
~2 tiếng và **không có kênh cũ nào đỡ**, vì 55 kênh cũ đã pause hết.
Bật 6 kênh trước thì lỗi chung lộ ra sau ~30 phút với 6 lane, không phải 18.

## Thứ tự (mỗi bước xong mới sang bước sau)

**B1 · 06:59Z — Tạo 50 kênh nhưng ĐỂ TẮT**
```
gh workflow run seed_the_he_2.yml -f ghi_that=1 -f bat_ngay=0
```
`bat_ngay=0` ⇒ `paused=True`. Bản ghi có mặt, nhưng chưa kênh nào vào luồng render.
Sai gì cũng chỉ là 50 dòng dữ liệu, sửa/xoá được, chưa tốn một phút render nào.

**B2 · Soi bản ghi trên dashboard** — 50 kênh hiện đủ, đúng `format` / `accent` / giọng / phông.

**B3 · Bật 6 kênh, mỗi dạng một cái**
`WHATISINIT` (ranked) · `PENTAGONLEDGER` (race) · `CALORIESHOCK` (scaled) ·
`SKYRIGHTNOW` (mapped) · `FAMECURVE` (longshot) · `RENTREALITY` (thennow) · `ONESTUDY` (cinematic)
→ mở lại cron, xem **đúng một phiên**.

**B4 · Đọc log phiên đó** — đây mới là lúc trả lời được những thứ `KIEM_CHUNG.md` còn treo:
phanh hạn mức · tín hiệu `CAN` · phông riêng trên video · chuyển cảnh · thumbnail gen-2.
Xem tận mắt 2-3 video + thumbnail.

**B5 · Sạch thì bật nốt 44 kênh còn lại.**

**B6 · SAU CÙNG mới dọn kho kênh cũ.**
Video của 55 kênh cũ hiện là **toàn bộ kho nội dung đang có**. Dọn trước khi 50 kênh mới chứng
minh được là tự tay bỏ hết trứng đang có để đổi lấy giỏ chưa biết có đáy hay không.
Khi dọn: chỉ chuyển vào **thùng rác Drive** (giữ 30 ngày). Đổ thùng rác là việc anh tự bấm.

## Đã bỏ khỏi kế hoạch
- **Xoá 55 bản ghi kênh cũ**: không cần cho việc gì cả. Pause đã đủ để chúng ra khỏi luồng render
  (đo thật: 55/55 đang dừng). Xoá chỉ để cho gọn mắt, mà lại không lùi được. Để sau, hoặc không làm.
  (Tên 55 kênh đã chụp ra `kenh_the_he_1.json` nên xoá lúc nào cũng an toàn về mặt dọn kho.)
