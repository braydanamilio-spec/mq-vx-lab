# KÊNH KLING — cách dùng

Hai lệnh. Một để lấy prompt, một để đưa video anh tải về vào kho đăng.

---

## 1 · Lấy prompt

```bash
python3 kling_kenh.py --kenh "HOUSE RULES" --sl 10 --giay 8
```

| cờ | nghĩa |
|---|---|
| `--sl 10` | sinh 10 tập một lượt |
| `--giay 8` | độ dài clip — `5` `6` `8` `9` `10` đều được, nhịp tự co theo |
| `--y "..."` | ép ý tưởng cụ thể; bỏ trống thì AI tự nghĩ theo mạch kênh |
| `--kenh-liet-ke` | xem đang có kênh nào |

Mỗi tập ra một thư mục:

```
out/kling/house-rules/001-sink-surprise-showdown/
├── PROMPT.txt     ← mở ra, chép nguyên, dán vào Kling
├── tap.json       ← khâu sau đọc, anh không cần đụng
└── clips/         ← chỗ thả video tải về
```

Hệ **tự nhớ tập đã làm** và không lặp ý; số tập tự đếm tiếp.

---

## 2 · Đưa video về kho

Tải xong từ Kling, có hai đường:

**Thả tay** — kéo file vào đúng `clips/` của tập. Rõ ràng nhất.

**Hoặc để máy gán theo thứ tự tải:**

```bash
python3 kling_dong_bo.py --hop ~/Downloads
```

Lệnh này **chỉ in bảng dự kiến**, không đụng file:

```
14 video mới · 3 tập còn trống → ghép được 3
  kling_20260811_VIDEO_5946_0.mp4  →  001-sink-surprise-showdown
  kling_20260811_VIDEO_5947_0.mp4  →  002-cereal-flood-fix
```

Thấy đúng thì thêm `--lam`. Sai thì thả tay. *(Gán nhầm thì mười tập lắp nhầm mười video mà không cách nào biết ngoài mở từng cái ra xem — nên luôn xem trước.)*

Rồi dựng và đẩy kho:

```bash
python3 kling_dong_bo.py --kenh-dang HOUSERULES
```

Ép về 1080×1920@30 → AI viết bài đăng → vào Drive `_QUEUE`. Bỏ `--kenh-dang` thì dừng ở bước viết bài, chưa đẩy.

---

## 3 · Vì sao nhân vật không trôi

Prompt có **sáu khối**, bốn khối là **hằng số** — mã ghép vào, AI không đụng tới:

```
CHARACTER LOCK ....... ai, mặt, quần áo, tuổi, tính nết      HẰNG
LOCATION LOCK ........ nhà cửa, màu tường, đồ đạc            HẰNG
VISUAL / AUDIO LOCK .. nét vẽ, giọng                         HẰNG
TIMING AND STORY ..... chuyện của tập này              ← AI viết ĐÚNG chỗ này
PERFORMANCE / RENDER . cách diễn, hàng rào chống lỗi         HẰNG
```

Trước đây AI viết **cả prompt**, nên mỗi tập nó tả lại nhân vật một kiểu — tóc nâu thành hạt dẻ, áo trắng thành kem, 42 tuổi thành "trung niên". Kling vẽ đúng cái nó đọc. Nhân vật không trôi vì Kling kém, mà vì **mình đưa cho Kling mười bản mô tả khác nhau**.

Hai điểm nữa:

- **Prompt chỉ chèn người CÓ MẶT trong tập.** Kling hay kéo vào khung bất cứ ai được tả kỹ — tả Grandpa Joe ở tập không có ông là tự chuốc thêm một cụ già đứng thừa ở nền.
- **Chỉ chèn CĂN PHÒNG của tập ấy.** Tả cả năm phòng khi chỉ quay một phòng làm Kling trộn hai bối cảnh vào cùng khung.

---

## 4 · Thước tự chặn trước khi anh tốn lượt Kling

Kịch bản phải qua hết mới ra prompt:

| chặn | vì |
|---|---|
| ≤ 4 người trong khung | năm người thì Kling chia ngân sách khuôn mặt, nát cả năm |
| ≤ 4 lượt · ≤ 9 từ/lượt | dài hơn thì khớp miệng trượt |
| ≤ 13 từ thoại cho clip 8s | 2,7 từ/giây; quá là nói như đọc rap |
| hook ≥ 10 từ, ghim góc máy | không ghim thì Kling hay ra cảnh drone *(bài học 09/08)* |
| payoff phải có **cú lật** | đảo tình thế, không phải tả thêm cảm xúc |
| không đồ đạc nhà không có | 26 món lớn hay bị AI bịa — island, dishwasher, staircase… |
| không chữ / biển / logo | chỗ Kling hỏng nặng nhất |

Lỗi máy sửa được (thiếu dấu chấm, thừa khoảng trắng) thì **máy tự sửa**, không đốt lượt gọi AI.

---

## 5 · Bài đăng viết ba lần, không dùng chung

| nền tảng | thưởng cái gì | nên bài viết thế nào |
|---|---|---|
| **YouTube** | câu người ta **gõ vào ô tìm kiếm** | tiêu đề là cụm tìm kiếm; mô tả dài thật, có ngữ cảnh |
| **Facebook** | **bình luận** | câu đầu khiến người ta dừng cuộn + một câu mời trả lời; hashtag gần như vô dụng |
| **Instagram** | **hashtag** | caption hai dòng; 15–20 thẻ đúng chủ đề |

> **Chặn cứng thẻ `kids` / `children` / `nursery`.** Hoạt hình cộng mấy chữ ấy là đúng công thức để YouTube xếp video vào *made for kids*: tắt bình luận, không lưu playlist, không gửi thông báo, chặn quảng cáo cá nhân hoá. Mất gần hết doanh thu và gần hết đường phân phối — không đáng đổi lấy một cái thẻ AI thêm cho đủ số.

---

## 6 · Thêm kênh mới cho niche khác

Thêm **một mục** vào `KENH` trong [kling_kenh.py](kling_kenh.py) — không sửa mã:

```python
"TÊN KÊNH": {
    "ten": "...", "mo_ta": "...", "ty_le": "9:16",
    "nhan_vat": { "Tên": "tả cố định, nguyên văn mọi tập", ... },
    "phong":    { "kitchen": "tả 3-4 mốc lớn", ... },
    "nha": "...", "style": "...", "audio": "...{vai}...", "dien": "...",
    "mach": "loại chuyện kênh này kể — dùng làm đề bài cho AI",
}
```

Thước, hệ lệnh, bài đăng dùng chung — không phải viết lại gì.
