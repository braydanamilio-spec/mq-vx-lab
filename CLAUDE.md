# MM0 — CÁCH LÀM VIỆC CHUẨN

Anh (31/8/2026): *"cách e làm trên rất hay, note methord hay claude.md để sau cứ làm chuẩn
phân tích plan thế."* Đây là quy trình đã cho ra bản comic — ghi lại để lần sau không phải
tìm lại nó bằng cách đi sai vài vòng.

---

## 1. CHẨN ĐOÁN TRƯỚC KHI SỬA — bằng bằng chứng, không bằng cảm giác

Khi anh nói "cái này chưa được", việc đầu tiên KHÔNG phải mở code, mà là **trích khung hình ra
nhìn**:

```bash
ffmpeg -y -ss 12 -i out/video.mp4 -frames:v 1 -vf scale=640:-1 khung.png
```

Rồi đọc ảnh và viết ra bảng: lỗi gì · bằng chứng ở khung nào · gốc rễ. Ba cột, không thiếu cột
nào. Cột "bằng chứng" ngăn việc sửa thứ không hỏng; cột "gốc rễ" ngăn việc sửa triệu chứng.

**Khi con số và con mắt bất đồng, đo pixel.** Hôm nay tôi nhìn một khung và kết luận "nhân vật
quá nhỏ"; đo ra 84% chiều cao ô — không nhỏ chút nào. Cái sai là BỐ CỤC (ô ngang 988px chứa
người rộng 282px). Nếu tin con mắt mà phóng to người thì người đã tràn cả trên lẫn dưới.

```python
from PIL import Image                       # đo hộp bao của nét mực
im = Image.open("khung.png").convert("RGB"); px = im.load()
```

## 2. TÌM MỘT GỐC CHUNG, ĐỪNG VÁ TỪNG TRIỆU CHỨNG

Bốn lỗi khác nhau của bản hài cũ (nền đá nhau · nền sai bối cảnh · khung trống · mất người thứ
hai) đều chảy ra từ **một** nguyên nhân: dán người vector lên ảnh AI. Sửa gốc thì cả bốn biến
mất; vá từng cái thì mỗi bản vá đẻ ra lỗi mới — hôm nay ba trong bốn lỗi bố cục là do chính
bản vá trước sinh ra.

Dấu hiệu đang vá triệu chứng: **sửa vòng thứ ba mà vẫn cùng một họ lỗi.** Dừng lại, đi tìm thứ
cả ba cùng dùng.

## 3. PLAN TRƯỚC KHI LÀM — và nói rõ xoá gì, giữ gì

Plan gồm: chẩn đoán (bảng ở mục 1) · kiến trúc mới · thứ tự làm · **thứ sẽ xoá và thứ giữ lại**.
Mặc định: chỉ xoá `.mp4`; không bao giờ xoá `.py` / `.tsx` / `.md` / brand kit / cấu hình kênh /
kịch bản đã lưu. Giữ bản cũ để đối chiếu cho tới khi bản mới được duyệt.

## 4. PILOT MỘT KÊNH — anh duyệt — rồi mới nhân ra mười

Không bao giờ dựng cả loạt bằng code chưa ai nhìn. Một kênh, gửi, chờ duyệt.

## 5. SOI KHUNG TRƯỚC KHI GỬI — bắt buộc, không thay bằng điểm số

```bash
for P in 10 35 60 90; do ... ffmpeg -ss $(dur*P/100) ... ; done   # rồi ghép lưới và NHÌN
```

Ba lỗi tràn khung của tuần trước đều đi qua cổng chấm điểm với điểm sạch. Điểm số chỉ biết thứ
nó được dạy để đo.

**Cổng render một khung không chứng minh được gì ngoài khung ấy.** Hôm nay tôi gọi hai hàm
không tồn tại mà cổng vẫn xanh, vì khung 300 không rơi vào nhánh chứa lời gọi. Sau khi sửa
engine: `grep -c "_tenHam(" File.tsx` — ra 1 (chỉ chỗ gọi, không có chỗ khai báo) là hỏng.

## 6. GHI BUGLOG NGAY — `render-pipeline/PIPELINE_RULES.md`

Mỗi lỗi ghi ba thứ: triệu chứng · gốc rễ · **họ lỗi** (để nhận ra nó ở chỗ khác). Ví dụ họ lỗi
đã trả giá nhiều lần:

- *một kích thước chịu hai ràng buộc mà công thức chỉ mã hoá một* — cỡ chữ theo ô mà không theo
  độ dài chuỗi; chỗ chừa bong bóng cố định trong khi câu dài ngắn khác nhau
- *vá một nhánh, để nguyên nhánh song song* — sửa panel rộng, quên panel cận
- *mượn giá trị cho việc nó không sinh ra để làm* — `k["mau"]` là màu nền dự phòng, không phải
  màu thương hiệu
- *chép hằng sang hệ quy chiếu khác* — `545 / −437 / 119` đúng ở `KichHai` (đã nhân zoom), sai ở
  `KichComic`. Không báo lỗi, chỉ làm hình lệch — nên dễ đi sửa thẩm mỹ suốt bảy vòng

## 7. NGUYÊN TẮC CỨNG

- **Không `gh workflow run` để "kiểm tra"** — kể cả một lần. Đợi cron. (Đã vi phạm 2 lần, tốn
  quota thật.)
- **Không dùng Claude Code trong đường chạy tự động.** Hệ trên GitHub chạy bằng key AI sẵn có
  (Gemini / Cloudflare). Test ở máy anh được, nhưng thứ giao đi phải chạy được A-Z trên Actions.
- **Báo cáo ngắn.** Nói cái gì đã đổi và tại sao; không kể lại quá trình.
- **Tận dụng free 100%** — nền vẽ bằng code thay ảnh AI vừa đẹp hơn vừa cắt hẳn phụ thuộc hạn
  mức ảnh.

## 8. BẢN ĐỒ TỆP

| Việc | Tệp |
|---|---|
| 60 kênh phân tích | `render-pipeline/kich_v2.py` · `engine-remotion/src/v2/KichV2.tsx` |
| **10 kênh hài — engine** | `engine-remotion/src/comic/KichComic.tsx` (dựng cảnh) · `NenComic.tsx` (nền + trần + đạo cụ) · `MoDun.tsx` (30 mảnh đồ đạc) · `NoiChon.tsx` (nơi chốn) · `ThumbComic.tsx` (ảnh bìa) |
| **10 kênh hài — pipeline** | `render-pipeline/kich_comic.py` (short 9:16) · `kich_comic_long.py` (long 16:9) · `sinh_kich_ban.py` (kịch bản) · `sieu_du_lieu.py` (bìa + chữ đăng cho 3 nền tảng) · `brand_comic.py` (avatar/banner/watermark) |
| Kho kịch bản tích luỹ | `render-pipeline/kho_comic.json` |
| Bản hài cũ (giữ để đối chiếu) | `render-pipeline/kich_hai.py` · `src/v4/KichHai.tsx` — vẫn là nơi giữ `KHO` 40 mẩu viết tay, `doc_hai_giong`, `lam_thumb` |
| Luật + buglog | `render-pipeline/PIPELINE_RULES.md` |

## 9. CHẠY MỘT TẬP TỪ ĐẦU ĐẾN CUỐI

Bốn lệnh, đúng thứ tự. Chạy được ở máy anh và trong GitHub Actions y như nhau — chỉ cần
`edge-tts` + `remotion` + bộ khoá AI sẵn có. **Không lệnh nào cần Claude Code.**

```bash
# 1. Kịch bản — chỉ chạy khi kho sắp cạn (mỗi kênh cần ≥ 25 mẩu cho một tập dài)
python3 sinh_kich_ban.py --so 18

# 2. Video ngắn 9:16 (một tình huống, ~18 giây)
python3 kich_comic.py --vong 0

# 3. Video dài 16:9 (nhiều tình huống nối theo mạch, 8–11 phút — chỗ bật quảng cáo giữa video)
python3 kich_comic_long.py --vong 0

# 4. Ảnh bìa + tiêu đề/mô tả/thẻ  ->  out/v5_<slug>.tai.json
python3 sieu_du_lieu.py --vong 0            # thêm --long cho bản dài

# 5. Brand kit — chỉ chạy khi mở kênh mới hoặc đổi tạo hình
python3 brand_comic.py
```

Sản phẩm của một tập: `v5_<slug>.mp4` · `v5_<slug>.jpg` · `v5_<slug>.tai.json` (đủ để đăng).

Tệp `.tai.json` chứa **ba bộ chữ riêng** cho YouTube / Facebook / Instagram, cộng `dang_duoc`
cho biết nền tảng nào nhận được video này — bản dài 9 phút lên YouTube và Facebook nhưng không
lên Reels Instagram (giới hạn 90 giây).

### Ba tầng đa dạng — không tầng nào thay được tầng nào

| Tầng | Cơ chế | Ở đâu |
|---|---|---|
| Nội dung | 6 khung truyện × 3 độ dài, xoay theo số mẩu đã có; cổng chống trùng khuôn câu | `sinh_kich_ban.py` |
| Bản dựng | `hạt = băm(kênh) + sốTập × 7919` → cỡ cảnh, chuyển cảnh, góc nhìn nền đổi theo TỪNG TẬP | `KichComic.tsx` |
| Nơi chốn | 10 nơi có tên/kênh + sinh tổ hợp không giới hạn từ tập thứ 11 | `NoiChon.tsx` |
| Nét vẽ | mỗi kênh riêng độ dày mực · cỡ halftone · bo góc bong bóng · tỉ lệ người | `NET_KENH` trong `kich_comic.py` |

### Nguồn sự thật — đừng tạo nguồn thứ hai

- **`VAI` trong `kich_comic.py`** giữ CẢ BA: ai là ai · cao thấp bao nhiêu · giọng nào. Giới và
  tuổi từng chỉ nằm trong chú thích tiếng Việt, và hậu quả là nữ công tố đeo râu dê, con cao
  hơn bố. Mỗi vai có hai tên: tiếng Việt để đọc code, tiếng Anh để HIỆN RA (tiêu đề YouTube).
- **`MAU_CHINH` / `MAU_PHU`** là màu thương hiệu. `k["mau"]` KHÔNG phải — nó là màu nền dự
  phòng của bản cũ (`#E9E6F4` cho TECH SUPPORT), dùng làm màu chữ thì chữ tàng hình.
- **Hằng toạ độ phải đo trong ĐÚNG ngữ cảnh dùng nó.** `CAO_NGUOI` là 460 trong khung video và
  378 trên ảnh bìa — không phải vì nhân vật khác, mà vì hai phép đo trước đó đo lúc nhân vật
  đang bị mép cắt. Chép hằng giữa hai tệp là cách chắc chắn để hình lệch mà không có lỗi nào.
