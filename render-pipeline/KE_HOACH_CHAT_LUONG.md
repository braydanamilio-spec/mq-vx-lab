# KẾ HOẠCH NÂNG CHẤT LƯỢNG 18 KÊNH GIẢI THÍCH — 2/9/2026

Anh: *"hình render ra phải màu đẹp, hook hay, sau đó chèn chart hay số liệu lên trên sao cho phù
hợp, không che khuất… mỗi cảnh 1–2s và phải đẹp, không nhàm chán, không mở đầu kết thúc tẻ nhạt"*
· *"phân tích lên plan đàng hoàng từng bước, không làm nửa vời"*.

**Render đã TẮT** (`gh workflow disable`) để không dựng thêm video hỏng trong lúc sửa.

---

## 1. CHẨN ĐOÁN — bằng chứng ở khung nào, không đoán

Trích khung thật từ `v9_howloud_0000.mp4` (lưới 9 khung) và khung anh gửi từ DAYINLIFE.

| # | Lỗi | Bằng chứng | Gốc rễ | Trạng thái |
|---|---|---|---|---|
| 1 | Bản dài ra **9:16** | khung anh gửi, hai mép đen | `--long` và `--ngang` là hai cờ ĐỘC LẬP, `doc = not a.ngang`; workflow gọi thiếu `--ngang` | ✅ sửa ở gốc: `--long` tự ép 16:9 |
| 2 | **Cùng một câu hiện hai lần** | khung 2 & 3 của lưới | `_n("the_chu","<lời>", the="<lời>")` + `PhuDe` cùng vẽ | ✅ nhịp có thẻ chữ thì tắt phụ đề |
| 3 | Chú thích **bị hình nuốt** | khung 1: *"a jet at takeoff"* trên mũi máy bay trắng | dải mờ cao `0.46·H`, tại `y=0.37·H` chỉ còn ~0.17 — tắt trước chỗ cần | ✅ giữ ≥0.55 qua hết vùng chữ |
| 4 | **Nền trống trơn** | khung DAYINLIFE: gradient + phụ đề, không hình | CF cạn neuron ⇒ nhịp `canh` không có ảnh, mà `canh` **không có lớp vẽ bằng code** đứng dưới | ⬜ CHƯA |
| 5 | Nhịp cắt chậm | `kiem_nhip` cho phép trung vị 2,6 s; anh muốn 1–2 s | ngưỡng đặt cho bộ cũ | ⬜ CHƯA |
| 6 | Mở đầu / kết thúc nhạt | khung 1 mở bằng số liệu, không có cú móc | chưa có khuôn riêng cho hook và cho cú chốt | ⬜ CHƯA |

**Điều quan trọng nhất số đo nói ra:** khung 4–5 (so sánh), 7 (biểu đồ cột), 8–9 (nhân vật hoạt
hình có màu) **đều đẹp**. Engine vẽ đẹp được. Nên đây **không phải** việc làm lại tầng đồ hoạ —
mà là bịt bốn chỗ cụ thể. Nếu tin ấn tượng "ảnh xấu quá" thì đã đi làm lại cả engine, sai chỗ.

---

## 2. KIẾN TRÚC — thứ tự lớp của một cảnh

Anh mô tả đúng thứ tự cần có, và engine đã có ba lớp, chỉ thiếu lớp thứ hai:

```
lớp 1  NỀN      ảnh AI (màu, có chiều sâu)   ── hoặc, khi cạn hạn mức:
lớp 2  NỀN CODE  cảnh vẽ bằng code            ── ĐANG THIẾU ở khuôn `canh`
lớp 3  DẢI MỜ    nâng tương phản cho lớp 4    ── đã có, vừa sửa cho phủ đủ
lớp 4  SỐ LIỆU   số + chú thích + biểu đồ     ── đã có, đè lên trên
lớp 5  PHỤ ĐỀ    chữ chạy theo giọng          ── đã có
```

Nguyên tắc bốn tầng của dự án (§7): **tầng cuối không gọi mạng nên không bao giờ hỏng.** Khuôn
`canh` hiện thiếu đúng tầng ấy — nên khi CF cạn thì nó rơi thẳng xuống gradient rỗng.

---

## 3. THỨ TỰ LÀM

| Bước | Việc | Vì sao thứ tự này |
|---|---|---|
| **1** | Khuôn `canh` có **lớp vẽ bằng code**: bối cảnh + người que + đạo cụ theo `bt` | Bịt lỗ to nhất. Không có nó thì mọi việc sau vẫn ra nền trống khi cạn hạn mức |
| **2** | **Hook**: cảnh đầu là hình SAI TRÁI/gây tò mò, không phải thẻ tiêu đề | §12.12: *"hook phải là NỘI DUNG của cảnh đầu, không phải tấm biển"* |
| **3** | **Cú chốt**: đóng bằng cảnh + một dòng ngắn, bỏ thẻ chữ 3 giây | §12.12, cùng luật |
| **4** | Nhịp **1–2 s**: siết `kiem_nhip` xuống trung vị ≤2,0 s và ép khâu VIẾT câu 5–8 chữ | §12.11: *"muốn cảnh 2 giây thì câu phải 5–8 chữ; viết câu hai mươi chữ rồi mong khâu dựng cắt nhanh là bất khả"* |
| **5** | **Cổng che khuất**: đo pixel vùng chữ vs nền, chặn nếu tương phản dưới ngưỡng | Sửa xong phải có cổng, không thì lần sau lại lọt |
| **6** | Dựng **1 tập mẫu**, trích lưới 9 khung, **nhìn tận mắt** | §5: cổng chấm điểm không thay được mắt |
| **7** | Anh duyệt → xoá video cũ → bật render lại | §4: pilot một kênh, anh duyệt, rồi mới nhân ra |

---

## 4. XOÁ GÌ, GIỮ GÌ

- **Xoá**: chỉ `.mp4` / `.jpg` / `.tai.json` của 18 kênh — và **chỉ sau khi anh duyệt tập mẫu**.
  Xoá trước khi sửa xong là dựng lại đúng cái nền trống ấy lần nữa.
- **Giữ nguyên**: mọi `.py` · `.tsx` · `.md` · brand kit · cấu hình kênh · kịch bản đã lưu ·
  bản ghi D1 (đã dựng lại 93 bản, mất công lấy lại).

---

## 5. ĐIỀU PHẢI NÓI THẲNG

Hạn mức CF là **970.000 neuron/ngày ≈ 16.700 ảnh**. Muốn *mỗi cảnh* có ảnh AI thì trần thật là
khoảng **300–400 video/ngày**, không phải hàng nghìn. Bước 1 (lớp vẽ bằng code cho `canh`) là
thứ quyết định: có nó thì cảnh không ảnh vẫn đẹp, và lúc ấy mới nói chuyện tăng sản lượng được.

Chọn một trong hai, không có đường thứ ba:
- **Chất trước**: giữ ~300 video/ngày, gần như mọi cảnh có ảnh AI.
- **Lượng trước**: ~1.800 video/ngày, phần lớn cảnh dùng lớp vẽ bằng code (sau bước 1 thì lớp
  này đẹp, nhưng vẫn khác ảnh AI).
