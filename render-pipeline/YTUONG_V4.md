# THẾ HỆ 4 — 10 KÊNH HÀI, ĐỐI THOẠI HAI NHÂN VẬT (29/8/2026)

Anh: *"a muốn a làm cho a 10 channel nữa mà dạng videos hài hước phong cách usa, có đa dạng bối
cảnh, và đa dạng nhân vật đối thoại trong 1 videos theo kiểu phong cách simpson hay các phim hoạt
hình usa ăn khách trước đây… mỗi channel mang một phong cách riêng… kịch bản hay viral… short
ngắn 15-45s-60s… 9:16… tận dụng hệ thống api gemini, cf để vẽ ảnh bối cảnh nền"*.

**Tách hẳn khỏi 60 kênh đang có.** Thế hệ 2 (50 kênh) dùng `the_he_2.py`; thế hệ 3 (10 kênh dữ
liệu) dùng `kich_v2.py` + `src/v2/`; bộ này dùng `kich_hai.py` + `src/v4/`. Ba đường chạy song
song, chung hạ tầng giọng đọc và render, không chung mã dựng.

---

## 1. KHÁC THẾ HỆ 3 Ở ĐÂU

| | Thế hệ 3 (10 kênh dữ liệu) | Thế hệ 4 (10 kênh hài) |
|---|---|---|
| Nhân vật | **một** người kể | **hai** người đối thoại, thay nhau nói |
| Kịch bản | số liệu → giải thích → nguồn | **mở → leo thang → cú chốt** |
| Nền | vector dựng bằng mã | **ảnh AI vẽ**, cache một lần cho cả kênh |
| Độ dài | 20–36 giây | 15–60 giây |
| Mục tiêu | tin cậy, tra được | **buồn cười, chia sẻ được** |

## 2. VÌ SAO NỀN LÀ ẢNH AI CÒN NHÂN VẬT VẪN LÀ VECTOR

Anh dặn tận dụng Gemini/CF để vẽ nền. Đúng chỗ nên dùng, và có một lý do kỹ thuật rõ ràng:

* **Nhân vật phải điều khiển được từng khung** — khẩu hình, hướng mắt, cử chỉ, cảm xúc. Máy vẽ
  ảnh không cho mình điều khiển thứ gì; nó trả về một tấm ảnh và hết. Nên nhân vật giữ vector.
* **Nền thì đứng yên** trong suốt một cảnh. Đó chính là thứ ảnh AI làm tốt và vector làm dở: một
  gian bếp Mỹ lộn xộn, một bãi đỗ xe siêu thị lúc hoàng hôn, một phòng khách thảm hoa những năm
  90 — vẽ bằng hình học thì mất cả ngày mà vẫn nghèo.

**VÀ NỀN ĐƯỢC CACHE.** Đây là điểm quyết định, vì hôm nay đã đo được cảnh cạn sạch hạn mức:
*"đã thử 151 key, tất cả hết hạn mức ảnh"*. Nên mỗi kênh sinh **6 nền một lần duy nhất** rồi
dùng lại cho **mọi video sau**. Sáu mươi ảnh cho cả bộ, và từ video thứ hai trở đi **không tốn
một lượt vẽ nào**. Kênh nào cũng chạy được kể cả ngày kho key cạn.

## 3. MƯỜI KÊNH — MỖI KÊNH MỘT GIỌNG HÀI RIÊNG

Nguyên tắc: hài Mỹ ăn khách không đến từ câu đùa, mà đến từ **một người bình thường va vào một
sự thật khó chịu**. Nên mỗi kênh là một CẶP nhân vật cố định, và tiếng cười nằm ở khoảng cách
giữa hai người.

| # | Kênh | Cặp nhân vật | Kiểu hài | Bối cảnh |
|---|---|---|---|---|
| 1 | **RENT PANIC** | người thuê nhà trẻ ↔ chủ nhà tươi cười | giá thuê tăng nói bằng giọng vui vẻ | căn hộ · sảnh · bãi đỗ |
| 2 | **GYM LIES** | người mới tập ↔ huấn luyện viên quá nhiệt | quyết tâm tháng Giêng gặp thực tế | phòng gym · quầy sinh tố |
| 3 | **AIRPORT HELL** | khách bay ↔ nhân viên quầy | thông báo hoãn chuyến, giọng đều đều | quầy check-in · cổng ra |
| 4 | **CAR GUY** | chủ xe ↔ thợ sửa | báo giá leo thang từng câu | ga-ra · vỉa hè |
| 5 | **OFFICE SMALL TALK** | nhân viên ↔ sếp vui tính | họp lẽ ra là một email | phòng họp · bếp văn phòng |
| 6 | **DIET WARS** | người ăn kiêng ↔ bạn thân ăn tất | mỗi tuần một chế độ mới | bếp · quán ăn nhanh |
| 7 | **TECH SUPPORT** | người dùng ↔ tổng đài viên | "anh thử tắt bật lại chưa" | phòng khách · trung tâm gọi |
| 8 | **PARENT MODE** | bố ↔ con tuổi teen | hai thế hệ, một cái điện thoại | phòng khách · xe hơi |
| 9 | **NEIGHBOR WATCH** | hàng xóm tò mò ↔ người mới dọn đến | hàng rào là ranh giới ngoại giao | hàng rào · sân trước |
| 10 | **DATING APP** | người dùng ↔ bạn cùng phòng | hồ sơ hẹn hò và sự thật | phòng ngủ · quán cà phê |

Mỗi kênh **một cặp nhân vật riêng, một bộ nền riêng, một bảng màu riêng, một cặp giọng riêng** —
đo bằng `cham_v4.py`, cùng cách đã làm cho thế hệ 3.

## 4. CẤU TRÚC KỊCH BẢN HÀI (6–10 lượt thoại)

Rút từ chính cách phim hoạt hình Mỹ dựng một mẩu 30 giây:

1. **MỞ** — nhân vật A nói một câu bình thường (2–3 giây). Không đùa. Càng bình thường càng tốt.
2. **VA** — B trả lời bằng một sự thật lệch hẳn kỳ vọng. Đây là chỗ người xem cười lần đầu.
3. **LEO** — A cố cứu vãn; B đẩy thêm một nấc. Lặp 2–3 lần, mỗi lần nấc cao hơn.
4. **CHỐT** — một câu ngắn đảo ngược tình thế, hoặc A đầu hàng bằng một câu tự nhận.
5. **ĐUÔI** — nửa giây im lặng rồi một phản ứng không lời (nhướn mày, quay sang ống kính).

Luật cứng, chốt bằng `cham_v4.py`:
* lượt thoại **không quá 14 từ** — dài hơn thì nhịp hài chết;
* **cú chốt phải ở 3 giây cuối** — chốt sớm thì phần sau thành thừa;
* **hai nhân vật phải nói xen kẽ**, không ai nói hai lượt liền trừ ở phần leo thang.
