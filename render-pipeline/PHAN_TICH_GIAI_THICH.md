# PHÂN TÍCH HAI VIDEO THAM CHIẾU — dạng "giải thích người que"

Anh gửi hai video (1/9/2026) và bảo phân tích chi tiết cảnh + voice/sub để làm dạng này hoặc
hơn. Dưới đây là số ĐO ĐƯỢC, không phải cảm nhận.

Nguồn: `How Did Ancient Humans Travel the World` (A) · `What Did Ancient Humans Actually Do All
Day` (B). Cùng một kênh, cùng công thức.

---

## 1. Khung kỹ thuật

| | A | B |
|---|---|---|
| thời lượng | 9'22" (562 s) | 11'12" (672 s) |
| khung hình | 1920×1080 · 29,97 fps | 1920×1072 · 29,97 fps |
| bitrate | 401 kbps | 411 kbps |

**Đọc ra được gì.** Cả hai đều **trên 8 phút** — ngưỡng YouTube cho phép chèn quảng cáo giữa
video. Đó là lý do tồn tại của độ dài này, không phải vì nội dung cần chừng ấy. Bitrate 400 kbps
là thấp: họ không đầu tư vào chất lượng nén, vì hình vẽ phẳng nén rất tốt.

B cao 1072 chứ không phải 1080 — dấu vết cắt cúp watermark. Chi tiết nhỏ nhưng nói lên quy trình
của họ là lắp ghép, không phải dựng một mạch.

---

## 2. Nhịp cắt — thứ quan trọng nhất

| | số cắt | trung vị | 25% | 75% | dài nhất |
|---|---|---|---|---|---|
| A | 244 | **2,1 s** | 1,4 s | 3,0 s | 7,0 s |
| B | 290 | **2,1 s** | 1,4 s | 2,9 s | 10,5 s |

Phân bố A: `<1s` 22 · `1–2s` 91 · `2–4s` 113 · `4–8s` 17 · `>8s` 0

**≈ 26 cắt mỗi phút.** Đây là con số phải khắc vào đầu. Một video 9 phút cần **250 khung hình
riêng biệt**. Không có cảnh nào giữ quá 7 giây ở video A — kể cả đoạn cao trào.

So với bộ mình đang có: `kich_v2` giữ mỗi cảnh 4–8 giây. **Chậm gấp ba lần.** Đó là khoảng cách
lớn nhất giữa hai bên, lớn hơn cả khoảng cách về nét vẽ.

---

## 3. Tiếng

| | LUFS | true peak | LRA | quãng lặng > 0,25 s |
|---|---|---|---|---|
| A | **−14,1** | **+0,2 dBTP** | 3,9 LU | **0** |
| B | −14,0 | −1,8 dBTP | 2,5 LU | **0** |

Ba điều đọc ra:

1. **−14,0 LUFS đúng phóc** — họ chuẩn hoá về đúng mốc YouTube. Bộ mình đã làm việc này rồi
   (`chuan_am.py`), nên chỗ này ngang bằng.

2. **LRA 2,5–3,9 LU là NÉN RẤT MẠNH.** Dải động của giọng nói tự nhiên là 8–12 LU. Nén xuống
   còn 3 LU nghĩa là câu thầm thì và câu hét to gần bằng nhau — nghe trên điện thoại ngoài
   đường vẫn rõ từng chữ. Đây là lựa chọn có chủ đích cho nền tảng, không phải cẩu thả.

3. **Không có một quãng lặng nào dài quá 0,25 giây** trong suốt 9–11 phút, kể cả khi lọc riêng
   dải giọng 300–3400 Hz. Nhạc nền phủ kín từ đầu đến cuối, và lời kể gần như không nghỉ.

   Đây là con dao hai lưỡi và là **chỗ mình có thể làm hơn**: không nghỉ thì không có chỗ cho
   câu vừa nói ngấm vào. Mọi người kể chuyện giỏi đều dùng khoảng lặng. Họ đánh đổi nó lấy
   chỉ số giữ chân trong 30 giây đầu.

**Lỗi của họ:** true peak video A là **+0,2 dBTP — đã vượt 0**, tức có clip. Nền tảng nén lại
sẽ sinh méo. Bộ mình đặt trần −1 dBTP nên chỗ này mình đang **tốt hơn**.

---

## 4. Chữ trên màn hình — KHÔNG có phụ đề

Soi 25 khung rải đều: **không có phụ đề cháy vào hình**. Chữ chỉ xuất hiện làm **nhãn**:

| kiểu nhãn | ví dụ đo được |
|---|---|
| tên vật thể | `Log` · `Reeds` đặt dưới hai vật đem so |
| số liệu to | `40-60 lbs.` · `HEAVY.` đè lên chính vật đang nói tới |
| mốc thời gian | `65,000 years ago` ← mũi tên → `10,000 years ago` |
| đầu đề so sánh | `YOU` \| `HIM` · `ANCIENT USE` \| `POST-EUROPEAN CONTACT USE` |
| chú giải kỹ thuật | `nuchal ligament` với đường chỉ vào vị trí trên hình |
| câu hỏi tiêu đề | `CAVEMAN?` cạnh bộ xương |

Phông: sans đậm, chữ hoa cho đầu đề, đen trên nền sáng. Không viền, không đổ bóng.

**Chỗ mình làm hơn được ngay:** thêm phụ đề. Facebook và Instagram đa số xem KHÔNG TIẾNG. Video
này lên Facebook là mất trắng. Bộ `tts_karaoke` của mình vốn đã có mốc từ nên làm phụ đề chạy
theo lời gần như không tốn gì.

---

## 5. Bảy loại khung hình — công thức thật sự

Đây là phần đáng học nhất. Họ **không** dựng 250 cảnh diễn xuất; họ xoay vòng bảy khuôn:

1. **Cảnh diễn** — một người trong phong cảnh. Chiếm nhiều nhất, ước 45%.
2. **So sánh chia đôi** — vạch dọc giữa khung, hai nhãn hai bên (`YOU`\|`HIM`). Đây là thiết bị
   tu từ TRUNG TÂM: mọi luận điểm đều dựng thành "cái này so với cái kia".
3. **Số liệu đè lên hình** — chữ số rất to đặt ngay trên vật đang nói tới.
4. **Trục thời gian / đồ thị** — mũi tên, mốc năm, trục `distance`, hàng biểu tượng mặt trời
   đếm số ngày.
5. **Kính lúp chú giải** — phóng to một chi tiết cơ thể/công cụ, có đường chỉ và tên gọi.
6. **Ảnh thật xen vào** — ảnh vệ tinh sông ngòi giữa loạt hình vẽ. Một nhát là đủ đổi vị.
7. **Cảnh nhóm** — 4–5 người quanh đống lửa, dùng cho các đoạn nói về xã hội.

**Vì sao công thức này thắng:** mỗi khuôn có chi phí dựng rất thấp và **khuôn 2/3/4 dựng được
100% bằng code** — chúng là chữ, vạch, mũi tên, biểu tượng. Đúng thứ `BarChartRace.tsx` và
`NenQue.tsx` của mình đang làm.

---

## 6. Tạo hình nhân vật

- Đầu: vòng tròn **trắng, viền đen dày**, không có cổ.
- Mắt: hai chấm đen. Mày cong là nơi chở gần hết cảm xúc.
- Miệng: một nét cong; há thành ô van khi gắng sức.
- Tóc: **MẢNG bù xù màu nâu**, không phải các sợi rời. Đây là chỗ bản `NguoiQue` của mình đang
  vẽ bằng sợi và thua rõ.
- Áo: mảng lông thú có vân, phủ thân — cùng ý tưởng với `AoTren` của mình.
- Chi: nét đen mảnh, độ dày đều, không vẽ khớp.
- Giọt mồ hôi, vạch tốc độ đỏ khi gắng sức — hiệu ứng truyện tranh, rất rẻ mà rất hiệu quả.

## 7. Nền

Tranh vẽ **có chiều sâu**, không phải tường phẳng:
- trời chuyển sắc → núi xa nhạt → cây trung cảnh → mặt đất có đá và cụm cỏ ở tiền cảnh
- đường chân trời ở 40–55% chiều cao
- **màu đổi theo tâm trạng đoạn**: xám lạnh cho đoạn khổ, vàng ấm cho ngày thường, xanh đêm
  cho cảnh quanh lửa

Đây là khoảng cách thật giữa nền của họ và `NenQue` của mình: mình đang vẽ **phòng phẳng nhìn
chính diện**, họ vẽ **cảnh có ba lớp xa gần**.

---

## 8. Lỗi của họ — chỗ mình vượt được

1. **Chữ chỉ dẫn dựng phim lọt vào ảnh.** Một khung hiện nguyên chữ `SPLIT FRAME` ở giữa trên.
   Đó là lời dặn cho hoạ sĩ/máy vẽ, không phải nội dung. Cùng đúng họ lỗi `NO TEXT` khiến FLUX
   viết chữ "NO Text." lên sàn bếp của mình hôm 30/8 — chứng tỏ họ sinh ảnh bằng AI và **không
   có cổng kiểm chữ**. Bộ mình đã có `_co_chu()`.
2. **True peak vượt 0 dBTP** (video A).
3. **Không phụ đề** → mất sạch lượt xem tắt tiếng trên Facebook/Instagram.
4. **Không có chương** — video 11 phút không mốc thời gian, người xem không nhảy được.
5. **Một tạo hình duy nhất** lặp lại suốt loạt.
6. **Không có khoảng lặng** — không đoạn nào để câu vừa nói ngấm.

---

## 9. Bản đặc tả nếu dựng bộ này

```
thời lượng     8'30" – 11'00"   (qua ngưỡng quảng cáo giữa video)
khung          1920×1080 · 30 fps
nhịp cắt       trung vị 2,1 s · không cảnh nào quá 7 s · ≈ 26 cắt/phút
               -> video 9 phút = 250 khung hình
tiếng          −14 LUFS · true peak ≤ −1 dBTP · LRA nén về 4–5 LU
               (nén mạnh như họ, nhưng CHỪA 2–3 khoảng lặng 0,8 s ở các cú chốt)
phụ đề         CÓ — chạy theo mốc từ, dải dưới, nền đậm      <- điểm vượt
chương         CÓ — 5–7 mốc trong mô tả                       <- điểm vượt
chữ trên hình  chỉ nhãn: tên vật · số liệu to · mốc năm · đầu đề so sánh
```

**Tỉ lệ bảy khuôn cho một video 9 phút (250 khung):**

| khuôn | số khung | dựng bằng |
|---|---|---|
| cảnh diễn | ~112 | `NguoiQue` + nền ba lớp |
| so sánh chia đôi | ~38 | code thuần |
| số liệu đè hình | ~30 | code thuần |
| trục thời gian / đồ thị | ~25 | code thuần |
| kính lúp chú giải | ~18 | code + một hình |
| cảnh nhóm | ~20 | `NguoiQue` × 4–5 |
| ảnh thật xen vào | ~7 | kho ảnh miễn phí |

**Hơn một nửa số khung dựng được 100% bằng code, không gọi API ảnh.** Đúng hướng anh đặt: tận
dụng free tối đa.

---

## 10. Việc phải làm nếu chạy hướng này

1. `NenQue` hiện là phòng phẳng nhìn chính diện — cần thêm **ba lớp xa gần** và **bảng màu theo
   tâm trạng đoạn**.
2. `NguoiQue` cần **tóc dạng mảng** thay cho sợi, và **hiệu ứng truyện tranh** (giọt mồ hôi,
   vạch tốc độ, dấu chấm than).
3. Dựng bốn khuôn mới hoàn toàn bằng code: so sánh chia đôi · số liệu đè hình · trục thời gian ·
   kính lúp chú giải.
4. Bộ sinh kịch bản phải viết ra **250 nhịp có mốc thời gian**, mỗi nhịp ghi rõ dùng khuôn nào —
   chứ không phải một bài văn rồi cắt.
5. Phụ đề chạy theo mốc từ (đã có sẵn trong `tts_karaoke`).
6. Cổng mới: **đếm số cắt / phút**, đỏ nếu dưới 20. Cổng chấm điểm hiện tại không đo nhịp, mà
   nhịp mới là thứ quyết định người xem ở lại hay lướt.
