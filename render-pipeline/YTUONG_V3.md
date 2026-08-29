# THẾ HỆ 3 — 10 KÊNH HOẠT HÌNH CÓ NHÂN VẬT (29/8/2026)

Anh: *"nâng cấp channel V2 với ideal làm thêm dạng channel mới… tài chính, ngân hàng, luật,
khoa học, vũ trụ, thiên văn, y tế… theo phong cách nội dung viral USA"* và *"ko động vào 50
channel đang ok hiện tại mà nếu làm ok thì làm channel mới"*.

**Tách hẳn.** 50 kênh thế hệ 2 không bị đụng một dòng nào: chúng dùng `the_he_2.py` +
`kenh_the_he_2.json`; bộ này dùng `kich_v2.py` + `kenh_the_he_3.json` + `src/v2/`. Hai đường
chạy song song, chung hạ tầng render/đăng, không chung mã dựng.

---

## 1. VÌ SAO 2D VECTOR, KHÔNG PHẢI 3D

Sáu ảnh anh gửi tham chiếu — con cú đội mũ Uncle Sam, hai ông hàng xóm bên hàng rào, bà cô ghế
bập bênh — **đều là vector 2D phẳng**: nét viền dày đều, màu bệt, không khối, không bóng đổ theo
nguồn sáng. Không có tấm nào là 3D.

Điều đó quyết định hướng làm, vì hai đường chênh nhau rất xa về chi phí:

| | 3D thật | 2D vector |
|---|---|---|
| Cần gì | model có rig xương + blendshape khẩu hình + texture | không cần asset ngoài |
| Lấy ở đâu | mua kho asset; máy vẽ AI **không** sinh ra model, chỉ sinh ẢNH | tự vẽ bằng SVG |
| Điều khiển | qua engine 3D, phải nhúng thêm three.js | thẳng từng khung, ngay trong Remotion |
| Giống ảnh anh gửi | **không** | **có** |

Nên: dựng con rối vector điều khiển tới từng khung. Nhìn ra màn hình thì giống ảnh tham chiếu hơn
hẳn một bản 3D làm vội — mà mười thứ anh liệt kê đều làm được thật, không phải hứa.

## 2. MƯỜI THỨ ANH DẶN — LÀM Ở ĐÂU

| Yêu cầu | Cách làm | Nằm ở |
|---|---|---|
| 👄 Lip-sync khớp voice | mốc thời gian TỪNG TỪ của edge-tts → chuỗi khẩu hình suy từ nguyên âm, trộn mượt giữa hai hình | `DienVien.visemeTai` |
| 👀 Mắt nhìn đúng hướng | con ngươi lệch theo vector `nhin`; cảnh nào nhìn ống kính, cảnh nào nhìn biểu đồ | `DienVien.Mat` |
| 😮 Biểu cảm theo câu thoại | 8 cảm xúc = 8 bộ số (mày, mí, khoé miệng, nghiêng đầu, ngả thân), trộn được giữa hai | `CAM_XUC` |
| 🗣️ Voice có cảm xúc | chọn giọng + tốc độ + cao độ theo `cam_xuc` từng cảnh khi gọi edge-tts | `kich_v2.py` |
| 👐 Cử chỉ tay | 8 cử chỉ đặt góc vai/khuỷu, lò xo giảm chấn đưa tay tới đích | `CU_CHI` |
| 🚶 Đi/chạy/ngồi/nhảy | `DANG` đổi khung xương chân + chu kỳ bước | `DienVien.dang` |
| 🎭 Emotion engine | như trên, đổi được giữa cảnh và **trong** cảnh | `CAM_XUC` |
| 🎥 Camera đổi góc | máy quay ảo = biến đổi viewBox: cắt cảnh, lia, đẩy vào, kéo ra | `KichV2.MayQuay` |
| 👕 Secondary motion | tóc/cà vạt/vạt áo đi **trễ** sau thân bằng hàm thuần theo thời gian | `DienVien.treo` |
| 🔊 SFX theo hành động | mỗi mốc hành động gắn một tiếng; trộn dưới giọng đọc | `KichV2` |

## 3. MƯỜI KÊNH — Ý TƯỞNG, NHÂN VẬT, BỐI CẢNH

Nguyên tắc chung, rút từ 50 kênh đang chạy: **mỗi kênh một câu hỏi mà người Mỹ tự hỏi về tiền
của chính mình**, trả lời bằng số liệu công khai tra được. Nhân vật không phải để trang trí — nó
là **người kể chuyện có chính kiến**, thứ mà 50 kênh kia (toàn chữ và biểu đồ) không có.

### Nhóm TIỀN

| # | Kênh | Câu hỏi | Nhân vật | Bối cảnh | Nguồn |
|---|---|---|---|---|---|
| 1 | **BANK RUN** | Ngân hàng anh gửi tiền có khoẻ không? | Nữ chuyên viên, kính gọng dày, áo cardigan đỏ | quầy giao dịch, bảng số điện tử sau lưng | FDIC BankFind + FFIEC |
| 2 | **FINE PRINT** | Điều khoản họ mong anh không đọc | Nam luật sư trẻ, sơ mi xắn tay, cà vạt lệch | phòng họp kính, chồng hồ sơ | CFPB complaint DB |
| 3 | **WHO OWNS IT** | Ai thật sự sở hữu thương hiệu anh dùng hằng ngày | Ông chú áo kẻ, mũ lưỡi trai | hàng rào trắng, sân sau | SEC EDGAR 13F |

### Nhóm LUẬT

| # | Kênh | Câu hỏi | Nhân vật | Bối cảnh | Nguồn |
|---|---|---|---|---|---|
| 4 | **KNOW YOUR RIGHT** | Cảnh này anh được phép làm gì | Nữ cựu công tố, tóc búi, áo blazer | bậc thềm toà án | CourtListener |
| 5 | **SUED IN AMERICA** | Người Mỹ kiện nhau vì chuyện gì | Ông thẩm phán về hưu, râu quai nón | thư phòng, tủ sách luật | CourtListener + PACER |

### Nhóm KHOA HỌC & VŨ TRỤ

| # | Kênh | Câu hỏi | Nhân vật | Bối cảnh | Nguồn |
|---|---|---|---|---|---|
| 6 | **SKY TONIGHT** | Đêm nay trên đầu anh có gì | Cô gái trẻ áo khoác dạ, khăn quàng | sân thượng, kính thiên văn | NASA NeoWs + JPL |
| 7 | **ONE EXPERIMENT** | Một thí nghiệm đổi cách ta hiểu thế giới | Nhà khoa học tóc rối, áo blouse | phòng thí nghiệm | Europe PMC |
| 8 | **DEEP FIELD** | Thứ xa nhất con người từng nhìn thấy | Người kể giấu mặt, bóng đổ | đài quan sát ban đêm | NASA APOD + JPL |

### Nhóm Y TẾ

| # | Kênh | Câu hỏi | Nhân vật | Bối cảnh | Nguồn |
|---|---|---|---|---|---|
| 9 | **WHAT THE CHART SAYS** | Hồ sơ bệnh án nói gì mà bác sĩ không kịp nói | Nữ y tá, áo scrubs xanh | phòng khám | openFDA + CDC |
| 10 | **PRICE OF CARE** | Cùng một ca mổ, hai bệnh viện, hai cái giá | Nam nhân viên thanh toán viện phí | quầy tiếp nhận | CMS Hospital Price Transparency |

**Chống trùng với 50 kênh cũ:** ba kênh cũ đã dùng CourtListener (COURT RECORD, COLD FILE, YOUR
RIGHTS CASE) và một dùng openFDA (PILL FACTS). Bộ mới **không lặp góc nhìn**: kênh cũ kể *một hồ
sơ có thật*, kênh mới trả lời *một câu hỏi người xem đang có*. Chốt bằng `do_giong_nhau.py` trước
khi đưa vào sản xuất, cùng phép đo đã dùng cho 50 kênh.

## 4. KHÁC 50 KÊNH CŨ Ở ĐÂU

| | Thế hệ 2 (50 kênh) | Thế hệ 3 (10 kênh) |
|---|---|---|
| Hình | bảng số, biểu đồ, ảnh AI tĩnh | **nhân vật diễn**, biểu đồ là đạo cụ trong tay |
| Giọng | thuật lại | **nói với người xem**, có cảm xúc |
| Giữ chân | con số gây choáng ở giây đầu | con số **+ một khuôn mặt phản ứng với nó** |
| Chi phí | 1 lượt vẽ ảnh/cảnh | **0 lượt vẽ** — nhân vật là SVG, không tốn hạn mức AI |

Điểm cuối đáng chú ý: bộ này **không tiêu một lượt hạn mức vẽ ảnh nào**. Nhân vật và bối cảnh
đều là vector dựng bằng mã. Đó là lối thoát cho đúng chỗ nghẽn nặng nhất hiện nay — nhật ký hôm
nay ghi *"đã thử 151 key, tất cả hết hạn mức ảnh"*.
