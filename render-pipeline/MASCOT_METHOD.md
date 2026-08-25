# METHOD — 5 KÊNH HOẠT HÌNH 2D (slot 56-60, chốt 25/8/2026)

## 1. Vì sao concept này quay lại được
Bản 22/8 để FLUX vẽ lại nhân vật **mỗi cảnh**, ghì bằng "style lock" trong prompt. Style lock giữ
được ~80%: hai khung liền nhau của cùng cặp đại bàng + gấu mèo ra hai tỉ lệ đầu, hai độ dày nét,
hai cái kính khác nhau. Khán giả đọc ra ngay "không phải một nhân vật" → concept bị xếp lại.
Không phải lỗi fps, không phải lỗi chi phí — **lỗi ở chỗ vẽ lại**.

Nay: **vẽ MỘT LẦN cho cả kênh** (rig), sau đó chỉ diễn.

| | Bản 22/8 | Bản 25/8 |
|---|---|---|
| Ảnh AI mỗi video | 5-8 | **0** |
| Drift nhân vật | có | **0** |
| Chuyển động | ảnh tĩnh đổi theo nhịp thoại | **30fps nội suy từng khung** |

## 2. Năm tầng chuyển động (MascotStage.tsx)
1. **MULTIPLANE** — đủ 4 dấu hiệu chiều sâu của máy đa tầng Disney 1937:
   thị sai theo độ sâu · **phối cảnh không khí** (lớp xa bạc màu + sương) · độ sâu trường ảnh ·
   **nhân vật nằm GIỮA các tấm kính** (lớp `near` vẽ đè lên nhân vật).
2. **KHÍ QUYỂN** — bụi bay, tia nắng quét (SVG, 0 quota).
3. **DIỄN XUẤT** — nhún thở liên tục, nghiêng người khi nói, squash & stretch ở chữ nhấn.
4. **NHÉP MỒM** — đo RMS 12Hz từ **chính file tiếng**, đổi `talk_closed`/`talk_open`.
5. **HIỆU ỨNG CARTOON** (ToonFX) — mồ hôi/sao choáng/gân giận/dấu hỏi/cú đập punchline.
   Dùng Lottie nếu có `public/lottie/fx/<tên>.json`, không thì SVG dựng sẵn (chạy được ngay).

## 3. Quy trình chuẩn (thứ tự BẮT BUỘC)
```
seed   → ghi 5 kênh vào render_channels, enabled=false
rig    → vẽ 6 tư thế × mỗi nhân vật + 4 lớp bối cảnh, tách nền, CẤT VÀO REPO
brand  → sinh 5 cỡ nhận diện từ chính rig
pilot  → viết skit → 2 giọng → đo mồm → xếp cảnh → render 1 short + 1 long → đẩy Drive
duyệt  → user xem; ưng thì bật `enabled` trên dashboard, kênh vào matrix
```
Chạy: workflow **MM0 Mascot Pilot**, chọn `buoc` = `seed+rig+brand+pilot`.

## 4. Luật cứng (vi phạm là tái phát bệnh cũ)
- **`mascot_build` TUYỆT ĐỐI không gọi đường vẽ ảnh.** Chốt `t_mascot_khong_ve_lai_nhan_vat`.
- **`style`/`mo_ta`/`id` trong `mascot_cast.py` là KHOÁ NHẬN DIỆN** — sửa một chữ rồi dựng lại rig
  là ra nhân vật khác. Muốn đổi tạo hình thì mở kênh mới.
- **Rig phải nằm trong repo**, không phải thư mục tạm của runner (lượt 11:16Z chết vì điều này).
- **Tách nền ĐO màu từ viền**, không khoá cứng mã màu (FLUX vẽ #38b828 chứ không #00b140).
- **Lọc lớp nền theo file THẬT** trước khi vào props — khai báo là ý định, thư mục là sự thật.

## 5. Cỡ nhận diện (MascotBrand.tsx)
| Cỡ | Dùng ở đâu | Lưu ý |
|---|---|---|
| 800×800 | avatar YouTube/FB/IG | hiện ra chỉ 98px → mặt TO, **không chữ** |
| 2560×1440 | bìa YouTube | vùng an toàn di động chỉ **1546×423 GIỮA khung**; chữ ra ngoài là bị cắt |
| 1024×1024 | dấu chìm video | |
| 1640×624 | bìa trang Facebook | |
| 1280×720 | khung thumbnail mẫu | bố cục cố định cho cả kênh |

## 6. Chi phí
Rig: ~11 lượt vẽ **một lần/kênh**. Brandkit: 0 lượt AI (render từ rig).
Mỗi video sau đó: **0 lượt vẽ**, chỉ tốn viết kịch bản + TTS như mọi kênh khác.
