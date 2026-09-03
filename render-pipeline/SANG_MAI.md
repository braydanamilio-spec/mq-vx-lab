# SÁNG MAI ĐỌC CÁI NÀY — phiên đêm 3/9/2026

## Đã đo tận nơi, không suy đoán

| trục | kết quả |
|---|---|
| 18 video dựng lại bằng mã cuối | **18/18** hình 1080×1920 · tiếng aac · không tệp hỏng |
| cổng chấm hình | **18/18 ≥90/100**, phần lớn 100 |
| khuôn lời giữa các video | **95% đa dạng**, khuôn nặng nhất ×3 (trần 3) |
| âm lượng | **−14,0 … −14,9 LUFS**, đỉnh −1,2 … −1,5 dBTP (chuẩn YouTube −14, đỉnh ≤0) |
| khớp lời–tiếng (phụ đề karaoke) | lệch **0,06–0,24 giây** |
| tương phản phụ đề | **5,2–12,4:1** (chuẩn WCAG 4,5) |
| Firestore hôm nay | **ĐỌC 0/50.000 · GHI 0/20.000** |
| 18 ảnh bìa | soi bằng mắt: số lớn đọc được, không hộp đen, không phụ đề sót |
| bìa bộ COMIC | **giữ nguyên byte** — mọi thay đổi nằm sau `_giua`, có cổng khẳng định |

## Trạng thái lúc bàn giao

| | |
|---|---|
| cổng trong repo | **25/27 xanh** (2 cái còn lại chỉ thiếu tham số dòng lệnh và khoá của runner) |
| cổng chấm hình | **15/15 tệp ≥90/100**, phần lớn 100/100 |
| thang chấm kịch bản | **99,5/100** trên 36 tập |
| Firestore hôm nay | **ĐỌC 0/50.000 · GHI 0/20.000 (0%)** — hôm qua cạn sạch cả hai |
| bản dài | trung bình **8,3 phút**, 10/18 kênh vượt mốc 8 phút bật quảng cáo giữa video |
| selftest | 220 bài, mọi bài mới đều có **thử ngược** |

## Việc anh cần làm (một lệnh)

Bản sửa dashboard chưa có hiệu lực cho tới khi deploy:

```bash
cd "/Users/mrquyenbk/Documents/MM0 YOUTUBE 2026/MM0-AutoPublisher/dashboard" && firebase deploy --only hosting
```

Sau khi deploy, ô "✅ Đã có video" sẽ nói thẳng `⚠ KHÔNG ĐẾM ĐƯỢC (lý do)` khi nó không đọc được
sổ, thay vì hiện `0` như thể chưa có video nào.

## Ba thứ em KHÔNG tự kiểm được

1. **Số liệu trên dashboard sau đăng nhập.** Trình duyệt của em không đăng nhập được và em không
   nhập mật khẩu hộ anh. Em kiểm được: trang trước đăng nhập sạch (0 lỗi console, mọi request
   200), 36/36 tệp brand kit của 18 kênh đều sống, và đọc thẳng mã để tìm gốc chỗ anh chụp.
2. **Video trên Drive có mở xem được không.** Log nói `✅ 5/5 video vào hàng đợi đăng` và
   `mọi video đã lên Drive`, một luồng rải 45 video qua 9 kho khác nhau — nhưng em không mở
   được tệp trên Drive để xem.
3. **Chất lượng cảm nhận.** Cổng chỉ nói "không dính tám lỗi đã biết", không nói "đẹp". Anh soi
   khung vẫn là phép kiểm cuối cùng.

## Luồng render

- Lượt 33766919199 (14:27 UTC) đang chạy: 16 luồng chạy, **2 luồng hỏng ở bước cài `edge-tts`**
  (`ResolutionImpossible` — lỗi mạng, đã ghim phiên bản + thử lại 3 lần cho lượt sau).
- Mốc cron kế: **20:20 UTC = 03:20 giờ anh**, lượt ấy mang đủ mã hôm nay.
- Đã huỷ lượt 14:37 vì nó chồng lên lượt đang chạy.

## Đã sửa đêm nay (theo thứ tự phát hiện)

1. **Phụ đề tương phản 2,0–3,7:1** (chuẩn WCAG 4,5). Hai nguyên nhân, hai cách chữa: sàn phòng
   sẫm dần về mép dưới (không phải tấm che đen), và **đổi mực theo nền** — độ sáng dải đáy do
   `nen_gt.sang_day` đo lúc sinh ảnh rồi ghi vào nhịp. Sau: **5,2–12,4:1**.
2. **Cổng `kiem_hinh` lấy khung ở mốc cố định** nên 2/6 khung rơi trúng nhịp `the_chu` — nơi
   engine TẮT phụ đề theo thiết kế. Cổng phạt một quyết định thiết kế. Nay đọc danh sách nhịp.
3. **Cổng `kiem_khuon` gộp mẫu** nên một bản dài 202 nhịp chiếm 72%. Nay đếm theo VIDEO:
   49% → **95%** đa dạng.
4. **Kính lúp phóng vào chỗ trống** — ba lần sửa điểm soi đều ra đĩa trắng. Đảo ưu tiên: vẽ vật.
5. **2/18 luồng chết ở bước cài** — `edge-tts` không được ghim nên pip lùi qua 30 phiên bản.
   `constraints.txt` sinh ra chính để chống chuyện này mà bỏ sót thư viện cài nhiều nhất.
6. **Bốn cổng mới**, tất cả có thử ngược: prompt cảnh đứng đầu · sổ khoá có chốt thời gian ·
   ảnh bìa lấy nhịp đỉnh · mỗi kênh một bộ gu riêng (18/18 khác nhau hoàn toàn).

## Đã đo và quyết định KHÔNG làm cổng — đừng làm lại

**Thang chấm kịch bản đã thành TRẦN.** Đo phân bố trên 72 tập: `96:1 · 97:14 · 100:57`, độ lệch
chuẩn 1,25. **57/72 tập đạt đúng 100** — tám trục không còn phân biệt được chất lượng nữa. Nó
vẫn có ích như hàng rào chống hồi quy, nhưng đừng đọc con số 99,5 như một thước chất lượng
(§13.24: khi kết quả dồn cục ngay trên ngưỡng thì ngưỡng đang là trần, không phải sàn).

**Đã thử thêm một trục: "đa dạng từ mở đầu câu".** Đo được 11% từ mở đầu khác nhau, một từ mở
tới 45 câu — nghe rất tệ. Nhưng **đọc tay** thì 45 câu "Now" của WHAT IF đi thành BỘ BA:

    Now ten people. → Now a hundred. → Now everyone.

Đó là chuỗi leo thang có chủ đích, đúng **quy tắc B** (§12.11: mệnh đề song song thì khung hình
song song) — và chính từ mở đầu lặp mới làm nó đọc ra một sự leo thang. Làm cổng ở đây là phạt
đúng thứ bộ luật yêu cầu, y như trục "ba nhịp cùng khuôn" đã bị bác hôm nay.

Muốn làm trục này thì phải tách được **leo thang có chủ đích** khỏi **lặp vô ý** — em chưa đo
được cách tách, nên không ship.

## Một điều CHƯA đo được — đừng sửa mù

Ống kính của THE RULES hiện cái **đồng hồ** cho câu *"It is written right here"* — đáng lẽ là tờ
giấy. Vì `_rai_hinh` chống lặp liền kề đã đổi `giay` sang biểu tượng kế trong bộ gu.

Đây là đánh đổi thật giữa **đúng nghĩa** và **không lặp**, và em chưa đo được cái nào hại hơn.
Sửa mù theo hướng "ưu tiên đúng nghĩa" sẽ lại thành cái đồng hồ lặp 8 lần của DAY IN LIFE — đúng
thứ vừa chữa xong. Muốn giải thì phải đo trước: soi tay ~20 ca `_rai_hinh` đã đổi, đếm bao nhiêu
ca đổi làm hình SAI NGHĨA và bao nhiêu ca chỉ đổi cho khác đi.
