# BẢNG KIỂM CHỨNG BẢN VÁ — "selftest xanh" KHÔNG có nghĩa là đã fix

Đêm 25-26/8 có **ba** bản vá hoá ra chưa từng chạy một lần nào:
- chụp hồ key vào D1 (`Đã chụp hồ key` in **0 lần**)
- thoát sớm khi cạn key (bắt ở chỗ `run_one` không ném lên → **0 lần**)
- chốt selftest đầu tiên cho chính bản vá đó (khớp chuỗi con → báo động giả)

Cả ba đều **selftest xanh, log sạch, không Traceback**. Chúng chỉ lộ ra khi đếm **chính con số mà
bản vá lẽ ra phải tạo ra**. Vì vậy mỗi bản vá phải khai sẵn: *đo gì thì biết nó đã chạy*.

## Cách dùng
Sau mỗi phiên, chạy các phép đếm ở cột "ĐO GÌ" trên log phiên đó. Chưa đạt = **chưa fix**,
không tính là xong dù mã đã push.

| bản vá | ĐO GÌ trên log phiên thật | đạt khi |
|---|---|---|
| 504 → thử lại | `TỔNG x video · y lỗi` | tỉ lệ lỗi < 30% ✅ đã đạt (47→24%) |
| nền trơn → khung thật | đếm `NỀN TRƠN` và `mượn ảnh sáng nhất` | NỀN TRƠN = 0 ✅ đã đạt |
| `key_order[0]` | đếm `IndexError` | = 0 ✅ đã đạt |
| cạn tài nguyên in gọn | đếm `Traceback` khi hết key | = 0 ✅ đã đạt |
| thoát sớm khi cạn key | đếm `3 kênh liên tiếp hết key` | > 0 trong phiên có cạn key |
| hồ key A ở plan | đếm `Hồ key A: dùng gói plan` | > 0 ở lane; `merge_keys_A` chỉ còn ở plan |
| cấu hình kênh gói plan | `read_channels=` trong sổ Firestore | tụt ~5.460/ngày |
| phanh số lane | đếm `🛑 PHANH` | > 0 khi quota ≥ 70% |
| sổ đo publish | `🧮 Firestore (publish)` | > 0 sau 1 ngày |
| ghi D1 nói lý do | đếm `⚠️ D1 ` | > 0 khi D1 tắt/từ chối |
| cổng an toàn nội dung | đếm `🛡️` | > 0 khi nguồn trả mục bẩn |
| nghẽn 500/AiError | đếm Traceback loại đó | = 0 |

## Luật
1. **Vá xong phải đo xem nó có chạy không.** Không đo = không biết.
2. Cách đo luôn giống nhau: **đếm chính con số mà bản vá phải tạo ra**.
3. Chốt selftest chứng minh mã ĐÚNG, không chứng minh mã CHẠY. Hai việc khác nhau.

## Chạy thử TRƯỚC KHI SEED (26/8, 06:10Z)

Seed 50 kênh chỉ có **một lần bấm**, nên chạy thử hết những gì chạy thử được mà không tốn hạn mức.

**① Seed với Firestore GIẢ** — ghi lại mọi doc mà nó định ghi, không đụng mạng:

| kiểm | kết quả |
|---|---|
| đủ 50 bản ghi | ✅ |
| `paused=False` (bật ngay) | ✅ 50/50 |
| `make_long=False` · `long_target=0` · `n_shorts=3` | ✅ 50/50 — `**dich` KHÔNG đè |
| `the_he=2` | ✅ 50/50 |
| chữ ký giọng khác nhau | ✅ **50/50**, 0 trùng |

**② Đường nội dung thật** — dựng story từ nguồn mở, 7/7 dạng:

| dạng | kênh thử | kết quả |
|---|---|---|
| ranked | WHAT IS IN IT | ✅ 6 mục · *Breakfast cereal: what is really in it* |
| ranked | RECALL PLATE | ✅ 6 mục · *Food recalls you probably missed* |
| race | PENTAGON LEDGER | ✅ 6 khung · Boeing $2.803M · BAE · Northrop |
| scaled | CALORIE SHOCK | ✅ 6 mục · *Frozen pizza, by calories* |
| mapped | SKY RIGHT NOW | ✅ 10 vùng · *Who is flying over America* |
| longshot | FAME CURVE | ✅ 5 mục · *Hayden Panettiere: the spike* |
| thennow | RENT REALITY | ✅ 6 cặp · *Same house, different decade* |
| cinematic | ONE STUDY | ✅ 6 cảnh · *Sleep and human cognitive development* |

Một lần Open Food Facts trả `503` — cơ chế lùi tự xoay sang mục khác, KHÔNG chết lượt. Đúng thiết kế.

**Vẫn chưa chứng minh được** (phải có phiên thật): phanh hạn mức · tín hiệu `CAN` · phông riêng trên
video · chuyển cảnh · thumbnail gen-2 · bản dọn kho đi hết cây.
