# BÀN GIAO — LỚP ĐỒ HOẠ VẼ BẰNG CODE & THANG CHẤM KỊCH BẢN  (3/9/2026)

Phiên này làm hai việc: dựng **hệ template đa dạng có bản sắc từng kênh** cho lớp đồ hoạ vẽ
bằng code, và dựng **thang chấm kịch bản** đầu tiên cho bộ giải thích.

Đọc tệp này TRƯỚC khi sửa `Khuon.tsx` hoặc `giai_thich.py`.

---

## 1. KIẾN TRÚC TEMPLATE — MỘT NGUỒN QUYẾT ĐỊNH, MỘT NƠI VẼ

```
giai_thich.py                          Khuon.tsx
─────────────────────                  ─────────────────────
GU_KHUON[kênh] -> 3 bố cục   ──ghi──>  nhip["bo_the"]  ──đọc──>  TheChu   (6 bố cục)
GU_SS[kênh]    -> 2 bố cục   ──ghi──>  nhip["bo_ss"]   ──đọc──>  ChiaDoi  (3 bố cục)
GU_HINH[kênh]  -> 5 biểu tượng ─ghi─>  nhip["bt"]      ──đọc──>  BieuTuong
```

**Luật cứng: Python QUYẾT, engine ĐỌC.** Không bao giờ để engine tự suy ra bố cục.

Bản trước engine tính `bo = hat + round(N.s * 3)`. Nghĩa là chỗ CHỌN bố cục nằm ở engine còn
chỗ biết BẢN SẮC KÊNH nằm ở Python — hai nơi, không nơi nào thấy nơi kia. Sửa bảng gu ở Python
mà engine vẫn dựng theo công thức cũ, **không có lỗi nào báo**.

Ba hệ quả của việc ghi vào nhịp:
1. con số nằm trong `.json` của tập -> dựng lại tập cũ ra **đúng hình cũ**
2. đọc `.json` là biết tập ấy dùng bố cục nào, không phải chạy lại công thức
3. thêm một bố cục mới chỉ phải sửa hai chỗ: bảng `GU_*` và `switch` trong engine

### Ba lượt rải, gọi ở MỘT chỗ hẹp
`kich_ban()` gọi tuần tự `_rai_hinh` -> `_rai_khuon` -> `_rai_ss` **sau khi** hai nhánh
short/long đã gộp lại. Đặt trong từng nhánh là hai chỗ để lệch nhau.

### Vì sao xoay theo `idx + thứ tự xuất hiện`, không theo `hat` của tập
Chỉ theo `hat` thì **mười thẻ chương trong CÙNG một video giống hệt nhau** — đúng cái anh đã
phê. Cộng `idx` để hai TẬP của cùng kênh không mở đầu bằng cùng bố cục.

---

## 2. SÁU BỐ CỤC THẺ CHỮ — khác nhau ở BỐ CỤC, không ở màu

| # | bố cục | dùng cho kênh kiểu |
|---|---|---|
| 0 | tràn màu, chữ giữa | gây sốc — mạnh nhất, cũng là chỗ rơi về khi thẻ không có số |
| 1 | số khổng lồ mờ làm nền, tiêu đề canh trái | kênh về con số |
| 2 | dải màu giữa khung, số lớn mờ trong dải | giữ được bối cảnh, nhẹ nhàng |
| 3 | nền sáng + vạch màu dày + eyebrow `CHAPTER n` | điềm đạm — nhẹ nhất |
| 4 | nêm chéo | phá nhịp; đường chéo là thứ duy nhất không ngang không dọc |
| 5 | đĩa số bên trái, tiêu đề canh trái | "chương sách" |

**Người xem nhận ra BỐ CỤC, không nhận ra sắc độ.** Sáu biến thể màu của cùng một bố cục vẫn
đọc ra một mô-típ. Nếu thêm bố cục thứ bảy, nó phải khác ở *trọng tâm nằm đâu · nền chiếm bao
nhiêu · chữ canh bên nào*.

Bố cục 1 và 5 **cần số chương**; thẻ tuyên bố giữa phim không có số nên tự rơi về 0.

---

## 3. BA BỐ CỤC SO SÁNH

| # | bố cục | ghi chú |
|---|---|---|
| 0 | hai cột + vạch đứt + hai tấm nền mờ | mặc định |
| 1 | trên/dưới | mỗi vế được CẢ bề ngang -> nhãn dài hết phải thu nhỏ. Đây là lý do thật để có nó |
| 2 | **theo tỉ lệ** | hai hình chung một mặt sàn, cỡ ∝ √(giá trị). Chênh lệch thành thứ NHÌN THẤY |

Bố cục 2 **tự rơi về 0** khi hai vế không có số đọc được hoặc hai số bằng nhau. Cấp một bố cục
cho dữ liệu không đỡ nổi nó là cách chắc chắn ra khung vô nghĩa.

**Căn bậc hai, không tuyến tính** — mắt so DIỆN TÍCH. Sàn 0,34: dưới mức ấy biểu tượng thành
một chấm. Sàn càng cao thì chênh lệch càng bị nói dối bớt; 0,34 là mức thấp nhất còn nhận ra
được hình ở khung điện thoại.

---

## 4. RÀNG BUỘC MỚI: BIỂU TƯỢNG PHẢI LÀ **KHỐI ĐẶC**

Bố cục tỉ lệ thu biểu tượng xuống 34%. **Nét rỗng mất chữ tín khi thu nhỏ** vì độ dày nét không
co theo hình — con hươu vẽ bằng ba đường không tô ra một cái móc câu. Khối đặc thì co bao nhiêu
vẫn giữ bóng dáng.

Thêm biểu tượng mới thì phải có mảng tô, không chỉ `stroke`. Kiểm bằng cách render ở 34% và NHÌN
— không có cổng tự động cho việc này.

---

## 5. MẶT SÀN DÙNG CHUNG — mọi vật phải có bóng tiếp đất

`NenPhong` dựng tường + sàn + quầng sáng, 6 biến thể theo `hat`. **Pha theo `mau` (màu thương
hiệu), không chỉ theo `nen`**: đo bảng màu thật thì `nen` của cả 18 kênh đều gần trắng
(`#E8E9E6` · `#F2F0EA` · `#EEF1F3`), nên phòng dựng từ nó vẫn trắng.

Một khung có mặt sàn thì **MỌI vật đứng trên sàn ấy phải để lại bóng** — thiếu một vật là mắt
đọc ra ngay. Đã có bóng: chủ thể `canh` · biểu tượng `ChiaDoi` · cột `Chart`.

**Dải mờ trên ảnh dùng màu kênh làm đậm, KHÔNG dùng đen.** Anh: *"ko làm bóng mờ đen thế nha
xấu"*. Cùng độ tối nên `kiem_chelap` vẫn qua, nhưng mắt đọc ra chỉnh màu điện ảnh chứ không ra
tấm kính khói.

---

## 6. THANG CHẤM KỊCH BẢN — `cham_kich_ban.py`

Tám trục, tất định, **không chặn** (nấc 2 trong ba nấc). Đã gắn vào
`render_phan_tich_18.yml`. Hiện: **99,4/100** trung bình 18 kênh × 3 tập.

```
don()            máy sửa được       -> sửa im lặng
cham_kich_ban()  làm kém đi         -> trừ điểm, cạnh tranh giữa các trục
kiem_*()         làm HỎNG sản phẩm  -> chặn
```

**99,4 chỉ đo TÁM TRỤC được dạy** — nó không chứng minh video hay. Nó là mốc so sánh và hàng
rào chống hồi quy. Vẫn phải soi khung bằng mắt.

`kich_ban(ma, idx, long, so_chuong)` là **nguồn duy nhất** cho danh sách nhịp — dùng cho cả
`mot_tap` lẫn thước. Đừng gọi thẳng `BO_SINH`: bản đầu của thước làm thế và chấm sai 17/18 kênh
vì không thấy nhịp hook.

---

## 7. ĐỪNG LÀM LẠI — đã đo và đã bác

| ý tưởng | đã đo | vì sao bác |
|---|---|---|
| **cổng sàn ĐỘ SÁNG cho ảnh CF** | 186 ảnh: trung vị 215, p10 ≤90 | nhìn tận mắt cả dải: ảnh tối nhất là **cảnh vũ trụ** (TB 35) và **hải đăng ban đêm** (TB 48) — tối đúng nội dung và đẹp. Cổng sẽ bắt oan |
| **cổng bảng màu theo kênh** | cùng kênh 0,46 · khác kênh 0,49 | hai phân bố chồng nhau hoàn toàn, không tách được |
| **siết ngưỡng lệch chất vẽ** | 20 tập: 1/20 vượt 2× ngưỡng | cổng hiện tại đã đủ; siết thêm chỉ tốn lượt vẽ lại |
| **sửa hook yếu trong `_cau_hook`** | điểm TỤT 96,9 -> 94,7 | hàm ấy không thấy trường `so` nên nối thêm chữ vào cả kênh vốn đã có số. Sửa ở nhánh `elif` của `mot_tap` mới đúng phạm vi |
| **phạt "ba nhịp cùng khuôn"** | bắt oan 2/3 số ca | ba `canh` liền = ba cảnh khác nhau; `so_lieu` ×3 song song là đúng **quy tắc B** (§12.11). Đo LẶP SỐ mới đúng |
| **bỏ sidecar, đọc kênh từ tên tệp** | nhanh tuyệt đối | mất TIÊU ĐỀ -> 1.300 bản ghi mang tên tệp. Tải song song 8 luồng mới đúng |

---

## 8. VIỆC CÒN LẠI

1. **Deploy index Firestore** (cần anh, repo không có token):
   `cd MM0-AutoPublisher/dashboard && firebase deploy --only firestore:indexes`
   Thiếu nó thì `health_guardian` mỗi giờ quét 200 tài liệu không sắp xếp = 4.800 lượt/ngày.
2. **Nối kênh YouTube/Facebook/Instagram** — hạ tầng đăng đã sẵn, chờ tài khoản.
3. **Ba khuôn chưa nâng cấp**: `Truc` · `KinhLup` · `Dem` — mỗi khuôn hiện chỉ có một bố cục.
   Làm theo đúng khuôn mẫu ở mục 1: thêm bảng `GU_*`, ghi vào nhịp, engine đọc.
4. **Cổng biểu tượng khối đặc** — mục 4 hiện chỉ kiểm bằng mắt.
