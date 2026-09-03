# BÀN GIAO — 18 KÊNH GIẢI THÍCH · trạng thái cuối ngày 3/9/2026

Đọc tệp này TRƯỚC khi làm gì. Nó nói ba thứ: **đang ở đâu · làm gì tiếp · đừng làm lại cái gì.**

---

## 1. ĐANG Ở ĐÂU

| | |
|---|---|
| Video trên Drive | ~1.280 (đếm thật: 6.297 tệp ÷ 4,9 tệp/video) |
| **Nhưng dùng được** | Chỉ những video tạo **sau 07:00 UTC 3/9** — trước đó là engine chưa vá |
| Cổng chấm hình | `kiem_hinh.py` — clip mới **100/100** |
| Cổng che khuất | `kiem_chelap.py` — đạt |
| Hồ CF | **97 tài khoản, cạn sạch** ngày 3/9 · hồi 00:00 UTC |
| Dashboard | 13/13 mục sạch: 0 ảnh vỡ · 0 lỗi JS · 0 `undefined` |

**Anh chưa duyệt clip nào.** Mọi con số "đạt chuẩn" mới là điểm cổng, không phải anh gật đầu.

---

## 2. LÀM GÌ TIẾP — theo thứ tự

### ① Lớp đồ hoạ vẽ bằng code (việc lớn nhất)
Biểu đồ · chia đôi · thẻ số vẫn **nền trắng phẳng**, đứng cạnh ảnh AI thì lộ ngay là hai thế giới.
Quan trọng gấp đôi vì **CF cạn thì nó là thứ duy nhất còn lại** — bản dài 3/9 vẽ được **0/32 cảnh
AI**, toàn bộ dựa vào lớp này.

Đích: cùng ngôn ngữ với ảnh AI — nền sáng ấm, nét mực dày, có bối cảnh. Xem `GU_CARTOON` trong
`nen_gt.py` để biết ảnh AI đang được tả thế nào, rồi làm lớp code khớp vào đó.

### ② Thang chấm kịch bản 100 điểm
Đã có: `kiem_trung.py` (không lặp nội dung) · `kiem_khuon.py` (không lặp khuôn câu).
Chưa có: thang điểm cho **chất lượng viết**. Anh đặt chuẩn 90/100 cho *kịch bản · nội dung · hình
ảnh · chuyển cảnh · âm thanh*; hình và tiếng đã có thang, kịch bản thì chưa.
Tham khảo `cham100.py` của bộ Kling — thang 10 trục đã chạy thật ở bộ đó.

### ③ Xác nhận hai thứ vừa sửa CHẠY THẬT trên runner
- **Trần 120 ảnh/luồng** (`TRAN_ANH_LUONG` trong `render_giai_thich_18.yml`)
- **Sổ trạng thái khoá khớp `last4`** (`xoay_key.ghi_trang_thai`)
Cả hai chỉ chứng minh được khi lượt render có luồng đầu về. Tìm dòng `🎚 đã vẽ 120 ảnh` và
`🗺 bản đồ khoá: N doc khớp`.

---

## 3. ĐỪNG LÀM LẠI — những thứ đã đo và đã bác

| Đừng làm | Vì đã đo |
|---|---|
| Siết vòng thử lại ảnh | tỉ lệ vẽ lại chỉ **2,3%**, hệ số 1,02× — không phải thủ phạm (7eh) |
| Siết ngưỡng "chất vẽ lệch" | thước lẫn phong cách với **mật độ chi tiết**; ảnh bị chấm lệch nhìn ra vẫn cùng thế giới (7ed) |
| Làm cổng bằng phép đo **bảng màu** | đo trên 14 kênh: cùng kênh 0,46 · khác kênh 0,49 — **chồng lấn hoàn toàn** (7ed) |
| Neo cỡ phụ đề vào `min(W,H)` | làm khổ DỌC bé đi; chuẩn phụ đề đo theo **chiều cao** (7eg) |
| Đổ tại Firebase khi mất video | bốn tầng dự phòng đều là **tầng mạng**; tầng cứu thật là **đĩa runner** (7dz) |
| Dựng công cụ bấm tay để chữa hệ tự động | anh đã gạt một lần; sửa **đường tự động** (§13.9) |

---

## 4. DỌN KHO — dùng đúng công cụ

| Việc | Lệnh | Lưu ý |
|---|---|---|
| Dọn video **engine cũ**, giữ video mới | `lam_lai.yml` với ô `truoc` = mốc ISO | **Mặc định bỏ thùng rác**, 30 ngày cứu được |
| Xoá **sạch** kho | `lam_lai.yml`, để trống ô `truoc` | Chỉ khi KHÔNG có lượt render đang chạy |
| Dọn bản ghi kênh đã nghỉ | `don_kho.yml` | Đụng cả Firestore lẫn D1 |
| Dựng lại sổ từ Drive | bước trong `don_kho.yml` | Khi video có mà sổ rỗng |

**Xoá sạch trong lúc render đang chạy = giết luôn video vừa làm ra.** Đó là lý do có ô `truoc`.

---

## 5. HẠN MỨC — ba con số phải nhớ

```
CF     : 97 tài khoản × 10.000 neuron ÷ 58 = 16.724 ảnh/ngày   · hồi 00:00 UTC
Firestore: 50.000 đọc · 20.000 GHI (hai hạn mức RIÊNG)          · hồi 07:00 UTC
Worker : 100.000 lượt gọi/ngày
```

**Nhu cầu ảnh = luồng × vòng × nhịp.** Vòng lặp liên tục (3/9) đẩy nó từ 4% lên 89% sức hồ. Trần
`TRAN_ANH_LUONG=120` giữ ở ~51%. Đổi số vòng lặp thì **phải tính lại con số này**.

---

## 6. QUY TRÌNH ĐÃ CHỨNG MINH LÀ ĐÚNG

1. **Anh nói "xấu" → trích khung ra NHÌN**, đừng mở code. Hai lần trong ngày 3/9 việc này đổi hẳn
   hướng sửa: lỗi thật là bản dài dựng bằng composition dọc và thẻ chữ lặp phụ đề, không phải
   "ảnh AI xấu".
2. **Sửa xong → dựng lại → soi lưới 9 khung → mới báo cáo.**
3. **Làm cổng xong phải thử NGƯỢC**: `kiem_chelap` bắt 10/10 hai vòng đầu vì soi nhầm loại nhịp;
   chỉ đọc tay các ca nó bắt mới thấy.
4. **Con số và con mắt bất đồng → đo cái đang bị chấm**, rồi mới quyết bên nào sai.
