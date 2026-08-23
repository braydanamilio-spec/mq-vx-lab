# 🚑 CỨU 180 VIDEO MỒ CÔI — phiên 07:02Z ngày 23/8/2026

**Việc này TỰ ĐỘNG. Không cần ai bấm gì.** File này để đối chiếu và chốt sổ, phòng khi quên.

## Chuyện gì đã xảy ra
Sáng 23/8 đổi scope OAuth Drive `drive` → `drive.file` trong code. Refresh_token của 70 kho được
cấp theo scope CŨ nên mọi lần làm mới trả `invalid_scope` → hệ tưởng "không kho nào đủ chỗ" →
**180/180 video của phiên 07:02Z bị từ chối đẩy Drive** (đã render xong, QC đạt, có thumbnail).

Đã rollback scope lúc 08:23Z; phiên 08:42Z xác nhận **0 dòng invalid_scope**, video đẩy kho bình
thường trở lại (37 video đầu tiên có `drive_id` + `thumb_id` lúc 09:12Z).

## Tài sản còn nguyên (không mất gì)
| Thứ | Ở đâu | Hạn |
|---|---|---|
| File .mp4 gốc (18 gói, ~8GB) | GitHub Actions artifacts, run `32624497622` | **26/8/2026** |
| Kịch bản đầy đủ từng video | Firestore B, field `script` của job | không hạn |
| Trạng thái job | `status=done`, `drive_id=""` (dấu nhận biết mồ côi) | — |

## Cách hệ tự cứu
1. Mỗi phiên, `plan` chạy `heal_unpushed(owner, hours=48, cap=120)`:
   quét job `done` + `drive_id` rỗng + có `script` → lật về `failed`.
2. Lane của kênh đó gọi `find_resumable` → nhặt kịch bản → **render lại từ script (0 gọi AI viết)**
   → đẩy Drive như video mới.
3. Mỗi phiên in: `🩹 heal_unpushed: quét N job done/48h, chữa M video chưa-đẩy-kho, CÒN LẠI ~K`.

## Mốc kiểm — ĐỐI CHIẾU BẰNG SỐ, KHÔNG TIN CẢM GIÁC
- [ ] Phiên kế tiếp: log heal phải hiện `chữa >0` và `CÒN LẠI` giảm dần
- [ ] Sau ~3-5 phiên: `CÒN LẠI ~0`
- [ ] Kiểm chốt: đếm job có `drive_id` **và** `thumb_id` tăng đúng ~180 so với mốc 09:12Z
- [ ] **Hạn chót 25/8/2026**: nếu còn sót, tải artifact run `32624497622` (còn tới 26/8) và đẩy tay

## Rủi ro đã tính
- `cap=120/phiên` + cửa sổ `48h` → thừa sức phủ 180 video trong 2-3 phiên.
- Nếu quota Firestore cạn giữa chừng: heal tự hoãn (không lật oan), phiên sau làm tiếp.
- Nếu vượt 48h mà chưa xong: dùng đường artifact (mục trên) — đó là lý do ghi hạn 25/8.
