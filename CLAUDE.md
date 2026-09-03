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

## 7. BA MỆNH LỆNH CHO MỌI PROMPT VẼ NỀN

```
wide shot, camera at standing eye level,
floor clearly visible across the lower third,
open space in the centre of the frame
```

Thiếu một trong ba là nhân vật lơ lửng. Đừng viết lại câu thứ hai — `import SAN_NEN` từ
`kich_hai.py`. Cổng `kiem_nen.py` quét mọi tệp dựng prompt nền và chặn nếu thiếu.

Bốn tầng để render không bao giờ thiếu nền: **nền riêng đã cache** → **sinh bù ở bước chuẩn bị**
(`chuan_bi_nen.py`, chạy TRƯỚC render) → **mượn nền cùng kênh** → **nền vector vẽ bằng code**.
Tầng cuối không gọi API nên không bao giờ hỏng.

## 8. NGUYÊN TẮC CỨNG

- **Không `gh workflow run` để "kiểm tra"** — kể cả một lần. Đợi cron. (Đã vi phạm 2 lần, tốn
  quota thật.)
- **Không dùng Claude Code trong đường chạy tự động.** Hệ trên GitHub chạy bằng key AI sẵn có
  (Gemini / Cloudflare). Test ở máy anh được, nhưng thứ giao đi phải chạy được A-Z trên Actions.
- **Báo cáo ngắn.** Nói cái gì đã đổi và tại sao; không kể lại quá trình.
- **Tận dụng free 100%** — nền vẽ bằng code thay ảnh AI vừa đẹp hơn vừa cắt hẳn phụ thuộc hạn
  mức ảnh.

## 9. BẢN ĐỒ TỆP

| Việc | Tệp |
|---|---|
| 60 kênh phân tích | `render-pipeline/kich_v2.py` · `engine-remotion/src/v2/KichV2.tsx` |
| **10 kênh hài — engine** | `engine-remotion/src/comic/KichComic.tsx` (dựng cảnh) · `NenComic.tsx` (nền + trần + đạo cụ) · `MoDun.tsx` (30 mảnh đồ đạc) · `NoiChon.tsx` (nơi chốn) · `ThumbComic.tsx` (ảnh bìa) |
| **10 kênh hài — pipeline** | `render-pipeline/kich_comic.py` (short 9:16) · `kich_comic_long.py` (long 16:9) · `sinh_kich_ban.py` (kịch bản) · `sieu_du_lieu.py` (bìa + chữ đăng cho 3 nền tảng) · `brand_comic.py` (avatar/banner/watermark) |
| Kho kịch bản tích luỹ | `render-pipeline/kho_comic.json` |
| **10 kênh giải thích — engine** | `engine-remotion/src/gt/KichGiaiThich.tsx` (dựng cảnh) · `Khuon.tsx` (8 khuôn: chia đôi · số liệu · trục · kính lúp · dải chữ · đếm · thẻ chữ · chart) |
| **10 kênh giải thích — pipeline** | `render-pipeline/giai_thich.py` (kịch bản + dựng) · `nen_gt.py` (CF vẽ cảnh, khoá nhân vật, cổng phong cách) · `to_mau.py` (chỉnh màu) · `kiem_nhip.py` (cổng nhịp cắt) |
| **30 kênh Kling — hồ sơ + thước** | `render-pipeline/kling_kenh.py` — hồ sơ 30 kênh (20 đời thường + 10 cỗ máy hài khác nhau, xem §14.1), bộ lịch 7 trục, `_mo_kenh()` lọc nhịp mở theo thế giới, thước `cham()`, ghép prompt theo ngân sách 2.500 ký tự |
| **30 kênh Kling — cổng** | `cham100.py` (thang 100 điểm, sàn 95) · `kiem_da_dang.py` (cổng chính sách: đo 435 cặp kênh) · `brand_kling.py` (brand kit vẽ bằng code + ba cổng: `kiem_bong()` bóng ngoài · `kiem_tron()` chữ lọt đường cắt tròn · `kiem_tuong_phan()` biểu tượng đọc được) · `selftest.py` (đề bài Python khớp web từng trường) |
| **20 kênh Kling — đưa clip về** | `kling_dong_bo.py` (gán clip tải về vào đúng tập, ép 1080×1920, viết bài đăng) |
| **12 kênh thiên nhiên** | `render-pipeline/thien_nhien.py` (10 thế giới, bộ lịch 4 trục + khuôn hình theo môi trường, 7 cổng: máu me · chữ · người · nhân hoá · trôi máy · động tác hỗn loạn · ngân sách) · `tn_dong_bo.py` (clip → video → bài → bìa 66% → đẩy kho, cổng khai báo AI) · `brand_tn.py` (brand kit, gọi thẳng ba cổng của `brand_kling`) |
| Cách dùng bộ Kling | `render-pipeline/KLING_CACH_DUNG.md` |
| Phân tích video tham chiếu | `render-pipeline/PHAN_TICH_GIAI_THICH.md` |
| Bản hài cũ (giữ để đối chiếu) | `render-pipeline/kich_hai.py` · `src/v4/KichHai.tsx` — vẫn là nơi giữ `KHO` 40 mẩu viết tay, `doc_hai_giong`, `lam_thumb` |
| Luật + buglog | `render-pipeline/PIPELINE_RULES.md` |

## 10. HAI BỘ, HAI XƯỞNG — ĐỪNG TRỘN

| Bộ | Kênh | Pipeline | Workflow | Luồng |
|---|---|---|---|---|
| **Comic (hài)** | 10 | `kich_comic.py` · `kich_comic_long.py` · `sieu_du_lieu.py` | `render_hai.yml` | 10 (mỗi kênh một luồng) |
| **Phân tích** | 56 | `kich_v2.py` · `kich_v2_long.py` | `render_phan_tich_18.yml` | 18 (chia xen kẽ) |
| **Kling (hài, AI video)** | 30 | `kling_kenh.py` · `kling_dong_bo.py` | **KHÔNG có** — anh dán prompt vào Kling web rồi tải clip về | tay |
| **Thiên nhiên (Kling, short 8–10s)** | 12 | `thien_nhien.py` · `tn_dong_bo.py` | **KHÔNG có** — anh dán prompt vào Kling web rồi tải clip về | tay |
| Thế hệ 1 (cũ) | ~50 | `datastory_ci.py` | `render_cron.yml` | cron TẮT |

Bộ Kling khác ba bộ kia ở một chỗ quyết định: **nó không dựng video trên Actions**. Python chỉ
viết kịch bản và ghép prompt; phần tốn tiền là anh dán vào Kling web. Nên mọi tối ưu ở bộ này
phải hỏi *"cái này có làm giảm số lượt gọi Kling không"* trước khi hỏi nó có đẹp hơn không.

Năm hệ này **không dùng chung engine, không dùng chung workflow**. Trộn chúng là cách chắc chắn
để một bản sửa ở bộ này làm hỏng bộ kia.

### 10.1 Chia luồng theo TRẦN THỜI GIAN THẬT, không theo cảm giác

Đo thời gian dựng thật của một đơn vị · nhân số đơn vị · **nhân hai** cho runner 2 nhân · cộng
30% dự phòng. Vượt trần thì **chia luồng, đừng nâng trần** — trần cao chỉ làm lỗi hiện ra muộn.

| | thời lượng | dựng ở máy anh | trên runner |
|---|---|---|---|
| comic ngắn | 14 giây | ~35 giây | ~1 phút |
| comic dài | 7 phút | ~19 phút | ~38 phút |
| phân tích ngắn | 20 giây | ~1 phút | ~2 phút |

Job bị huỷ vì quá giờ thì **`upload-artifact` không chạy** — mất luôn cả những video đã dựng
xong. Hỏng mà không để lại tệp nào thì trông y hệt chưa từng chạy.

### 10.2 `cron` của repo này KHÔNG đáng tin — đặt bốn mốc

Bằng chứng: `cleanup.yml` chỉ có một cron `"0 3 * * *"` nhưng nổ lúc 17:37, 09:37, 08:38, 00:36
— không lần nào đúng giờ. Có tick bị bỏ hẳn: hai tick đầu của `render_phan_tich_18.yml` (18:10
và 19:35) đều **0 lượt**, trong khi workflow khác cùng repo vẫn nổ.

Nên mỗi workflow đặt **bốn mốc cách nhau một giờ** + một job `chot` hỏi API xem 20h qua đã có
lượt thành công chưa. Bốn mốc nổ cả bốn cũng chỉ tốn bốn lượt kiểm 5 giây.

Khi cron không nổ, kiểm **ba** thứ trước khi đổ lỗi cho cấu hình: workflow `state == active` ·
`cron` có mặt trên `main` · workflow khác trong repo có nổ không. Đủ ba mà vẫn không nổ thì ghi
nhận đúng hiện trạng, đừng sửa bừa.

### 10.3 Bộ giao hàng của một tập — cổng `kiem_workflow.py` canh

**ngắn · dài · ảnh bìa · `.tai.json`**. Thiếu `.tai.json` là có video mà không đăng được. Cổng
đọc MÃ trong YAML, không đọc chú thích — bản đầu của nó bị lừa bởi một dòng comment nhắc tên tệp.

## 11. CHẠY MỘT TẬP COMIC TỪ ĐẦU ĐẾN CUỐI

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

---

## 12. LUẬT RÚT TỪ NGÀY 1/9 — BỘ PHIM GIẢI THÍCH

Một ngày làm mười kênh giải thích, và **năm lần tự làm sập đường chạy của chính mình**. Cả năm
đều cùng một dạng: *tin một điều mà chưa thử*. Ghi lại để không mất thêm buổi nào nữa.

### 12.1 Thêm tham số vào API ngoài thì THỬ MỘT LỆNH GỌI TRƯỚC

Tôi thêm `seed` rồi `width`/`height` vào lệnh gọi Cloudflare FLUX **và báo cáo như thể chúng
chạy**, trước khi thử lần nào. Endpoint trả thẳng:

```
HTTP 400  Additional or unevaluated properties '/seed' at '/' not allowed
HTTP 400  Additional or unevaluated properties '/width, /height' at '/' not allowed
HTTP 400  Length of '/prompt' must be <= 2048
```

`@cf/black-forest-labs/flux-1-schnell` **chỉ nhận `prompt` và `steps`**.

Cái giá không phải "thiếu một tính năng". `seed` làm **mọi** lệnh vẽ trả 400, nên cả đường sinh
ảnh chết — mà chết **chậm**: `goi_xoay` xoay hết 97 khoá, mỗi khoá một vòng mạng, rồi mới bỏ
cuộc. Nhìn từ ngoài y hệt "mạng chậm". Tôi đi đo thời gian nạp thư viện và đọc giọng một lúc
lâu trước khi thử đúng một lệnh gọi. Một lệnh gọi mất **nửa giây**; tin nhầm mất **cả buổi**.

Cùng dạng lần thứ ba trong ngày: nhồi prompt lên ~2800 ký tự theo yêu cầu "viết dài chi tiết
hơn" → vượt trần 2048 → mọi lệnh 400, không một ảnh nào ra.

**Nay:** mọi chỗ ghép prompt phải có **chốt chặn độ dài** ghép theo thứ tự ưu tiên và cắt từ
đuôi, thay vì để API từ chối cả câu.

### 12.2 `tsc --noEmit` xanh KHÔNG có nghĩa là build được

Chèn chú thích JSX `{/* … */}` vào **giữa các thuộc tính** của một thẻ. `npx tsc --noEmit` báo
xanh; `esbuild` — thứ Remotion thật sự dùng — báo `Expected "..." but found "}"` và render chết.

Tôi đã dùng typecheck làm cổng suốt ngày và nó cho tôi **niềm tin sai**.

```bash
npx esbuild src/gt/*.tsx --loader:.tsx=tsx --outdir=/tmp/_chk --log-level=error
```

Cổng đúng là **bộ dựng thật**, không phải bộ kiểm kiểu.

### 12.3 Thước đo phải soi ở KHOẢNG GIỮA, không chỉ ở hai đầu cực

Tôi xây thước "độ phẳng" để tách ảnh cartoon khỏi ảnh chụp. Calibrate hai đầu: ảnh chụp 0,13 ·
vector phẳng 0,91 — tách sạch, mắt nhìn khớp. Tin luôn.

Chạy thử: 6/11 ảnh "trượt sàn". **Nhìn vào sáu ảnh ấy thì cả sáu đều là cartoon đúng chất**, cùng
một nhân vật. Tấm điểm thấp nhất (0,30) là cảnh đám đông ban đêm có nhiều hình nhỏ và trời
chuyển sắc. Thước lẫn lộn **phong cách phẳng** với **bố cục đơn giản**.

Suýt nữa tôi báo "ép cartoon thất bại" trong khi nó đã thành công.

**Luật:** calibrate ở hai đầu cực chỉ chứng minh thước **có tách được hai đầu**. Trước khi lấy
nó làm cổng, phải **nhìn tận mắt vài mẫu ở khoảng giữa** — vì cổng sống ở khoảng giữa, không
sống ở hai đầu.

### 12.4 Cổng tự chuẩn hoá theo mẫu đầu tiên: nhất quán quanh một mốc SAI vẫn sai

Bản đầu của cổng lấy ảnh đầu tiên của tập làm mốc, ép mọi ảnh sau bám theo. Nghe hay. Nhưng nếu
ảnh đầu lỡ ra chất ảnh chụp thì **cả tập bị khoá vào chất sai ấy** — và cổng báo xanh, vì mọi
ảnh đều "nhất quán".

Cổng cần **một sàn tuyệt đối** trước, rồi mới tới nhất quán tương đối.

### 12.5 Một câu luật đúng trong ngữ cảnh nó sinh ra, sai ở ngữ cảnh mới

`SAN_NEN` viết cho bộ truyện tranh (mọi cảnh trong nhà): *"all furniture pushed far to the left
and right edges"*. Đem sang cảnh ngoài trời → FLUX làm đúng điều được bảo: **kê tủ kệ vào sa
mạc**. Nhịp nói "đi bộ ban đêm giữa sa mạc" ra một phòng khách có tủ.

Cùng dạng, lần thứ hai trong ngày: cắt ảnh vuông xuống 9:16 mất 44% bề ngang, mà luật lại đang
dặn *"dồn đồ đạc ra hai mép"* — tức dặn mô hình đặt đồ vào **đúng dải sắp bị cắt bỏ**.

**Nhận ra:** mỗi lần dùng lại một hằng/một câu luật ở chỗ mới, hỏi **"câu này còn đúng ở ngữ
cảnh mới không"** — dùng lại là đúng, dùng lại mà không hỏi là sai.

### 12.6 Prompt tả theo lối ẢNH CHỤP thì ra ẢNH CHỤP

Anh yêu cầu prompt dài và chi tiết hơn. Tôi ghép sáu tầng: chủ thể · hành động · biểu cảm ·
`background:` · `foreground:` · ánh sáng. Prompt lên 60 chữ, và **ảnh ngả hẳn sang ảnh thật**.

Vì `"background:"`, `"foreground:"`, `"warm light from the left, long soft shadows"` là **ngôn
ngữ mô tả một bức ảnh**. Mô hình đọc xong thì vẽ một bức ảnh. Đo được: những nhịp có câu ánh
sáng cho độ phẳng thấp nhất cả tập.

**Chi tiết hơn** và **phẳng như tranh** là hai yêu cầu đánh nhau nếu tả bằng ngôn ngữ quang học.
Tranh vẽ phẳng không có tiền cảnh/hậu cảnh theo nghĩa quang học, cũng không có đổ bóng mềm — nó
có: **cái gì ở đâu trong khung, và màu gì**.

### 12.7 Chữ trong ảnh: ngắn thì được, số dài có dấu thì không

Đo trên 8 mẫu, cùng một prompt phong cách:

| chuỗi | kết quả |
|---|---|
| `560` · `WALK` (≤ 4 ký tự, không dấu) | **5/6 đúng** |
| `238,900` (số dài có dấu phẩy) | **0/2 đúng** — ra `23 8,900` và `238.900` |

Và ngược trực giác: **câu nhấn mạnh lặp lại làm hỏng thêm** — hai mẫu duy nhất có
`"Write exactly: …"` đều sai, kể cả mẫu chuỗi ngắn.

**Luật:** nhãn ngắn để mô hình vẽ vào ảnh (hết đè, hết lệch khớp); **số dài luôn do code vẽ đè**.
Và phải có **cổng đọc chữ đối chiếu** với chuỗi đặt hàng — `_co_chu` đã có sẵn đường thị giác,
chỉ cần nâng từ "có chữ không" thành "chữ có đúng không".

### 12.8 Cổng canh đếm "lượt success" sẽ TỰ KHOÁ VĨNH VIỄN

`render_hai.yml` và `render_phan_tich_18.yml` có job `chot` đếm *"20 giờ qua đã có lượt
`conclusion == success` chưa"* để tránh dựng trùng.

Nhưng **một lượt bị chính cổng ấy bỏ qua cũng kết thúc là `success`**: `chot` chạy xong, `dung`
chỉ `skipped`, mà `skipped` không làm hỏng lượt chạy. Nên mỗi lượt bỏ qua lại **làm mới dấu
success**, cửa sổ 20 giờ không bao giờ trôi hết.

Đo được: `01:21` dựng thật 10/10 job → 10 artifact; `08:34` cùng ngày dựng **0/1 job → 0
artifact**. Dashboard xanh suốt.

Đây là dạng **tệ nhất** của luật 24.1 (*hỏng mà không để lại tệp nào thì trông y hệt chưa từng
chạy*) — vì nó còn **báo xanh**.

**Sửa:** hỏi thẳng job `dung` của từng lượt, chỉ đếm lượt có job dựng **thật sự chạy**.

### 12.9 Số trên dashboard đếm BẢN GHI, không đếm TỆP

Ô "✅ Video trong kho: 2088" đọc từ D1, đếm **bản ghi job** `status=done AND có drive_id` — không
liệt kê tệp trong Drive. Xoá sạch kho mà không xoá bản ghi thì con số **không đổi một đơn vị**.

Chính mã đã ghi lại cái bẫy này từ 23/8 (*"đếm bản ghi job → Tổng 1755 trong khi thư viện chỉ
61"*) và vá bằng cách **đổi chỗ đếm** — nhưng nguồn mới vẫn là bản ghi. Vá đổi chỗ đếm, không
đổi **thứ được đếm**.

### 12.10 Đo trước khi kết luận — kể cả về video của người khác

Hai lần trong ngày tôi kết luận từ ấn tượng rồi số đo bác lại:

- Xem 12 khung quanh một nhát cắt, thấy con báo dịch chuyển, kết luận *"cảnh vào đã đang chuyển
  động sẵn"*. Đo `mpdecimate` ba ngưỡng: **cắt cứng tuyệt đối** (0/244 cặp điểm cắt cách nhau
  <0,09 s), trong cảnh **có trôi máy nhưng biên độ cực nhỏ**.
- Tuyên bố *"chỉnh màu về bảng màu kênh là đòn bẩy lớn nhất"*. Làm xong, ghép trước/sau: **gần
  như không thấy khác biệt**, kể cả ở cường độ 0,32. Đòn bẩy thật là **lệch phong cách giữa các
  ảnh**, và chỉnh màu không cứu được lệch phong cách.

### 12.11 Bộ giải thích — bảy quy tắc nối cảnh

Rút ra khi cắt **24 cảnh LIÊN TIẾP** (không phải khung rời rạc). Lần soi đầu lấy 25 khung rải
đều và chỉ rút được "bảy khuôn hình" — đó là **từ vựng**. Ngữ pháp nằm ở chỗ cảnh nối cảnh:

| | quy tắc |
|---|---|
| A | mỗi cảnh vẽ **đúng mệnh đề đang nói**, không minh hoạ chung chung |
| B | mệnh đề song song → **khung hình song song**, dải chữ giữ nguyên một chỗ |
| C | thời gian trôi vẽ bằng **số lượng biểu tượng** để người xem ĐẾM, không đọc "hai tuần sau" |
| D | cảnh sau **kế thừa** cảnh trước (vệt chân dài dần) |
| E | lời chuyển từ kể sang **khẳng định** → hình chuyển sang thẻ chữ, bỏ hẳn minh hoạ |
| F | nói về **cơ chế** → sơ đồ có nhãn, nhân vật bỏ màu thành nét |
| G | con số luôn đứng cạnh **hình của chính vật ấy** |

Số đo bắt buộc của bộ này: **nhịp cắt trung vị ≤ 2,6 s · không cảnh nào quá 7 s · ≥ 20 cắt/phút**
— cổng `kiem_nhip.py` đo **trên danh sách nhịp, TRƯỚC khi render**. Nhịp là việc của **khâu
viết**: muốn cảnh 2 giây thì câu phải 5–8 chữ. Viết câu hai mươi chữ rồi mong khâu dựng cắt
nhanh là bất khả.

### 12.12 Dấu hiệu "nghiệp dư" — danh sách kiểm trước khi gửi

Đây là những thứ người xem đọc ra trong nửa giây, không liên quan tới nội dung:

- hộp đen bo góc quanh phụ đề (mặc định trình tạo phụ đề điện thoại) → **chữ trắng + bóng mềm rộng**
- dải tên kênh dưới **mọi** khung → **watermark nhạt ở góc**
- viền trắng quanh chữ số (`paintOrder="stroke"`) → **bóng mềm**; không hãng phim nào viền chữ
- đổ bóng cứng lệch (`10px 11px 0`) → viền mảnh
- thẻ tiêu đề to đè lên ba giây đầu → **hook phải là NỘI DUNG của cảnh đầu**, không phải tấm biển
- thẻ chữ giữ 3 giây ở cú chốt → **đóng bằng cảnh**, câu chốt để phụ đề nói
- thiếu lớp hoàn thiện → **vignette + grain rất nhẹ phủ toàn khung**, vì nó phủ lên cả ảnh lẫn
  đồ hoạ code nên hai thứ khác bản chất mới chung một bề mặt

### 12.13 Kênh Mỹ thì ĐƠN VỊ phải Mỹ

Mười kênh giải thích chạy suốt buổi với **kilômét, km/h, mét**. Người xem Mỹ đọc "384,400
kilometres" là biết ngay không phải kênh của mình — họ không có cảm giác về kilômét, đúng như
người Việt không có cảm giác về dặm.

Kênh giải thích **sống bằng việc quy con số về thứ người xem CẢM ĐƯỢC**. Dùng sai hệ đơn vị là
phá đúng cơ chế ấy ngay ở gốc. Dặm · mph · pound · feet · Fahrenheit · đô la.


---

## 13. LUẬT RÚT TỪ NGÀY 1/9 — BỘ KLING, 20 KÊNH

Một ngày đưa bộ Kling từ 10 lên 20 kênh và nâng điểm kịch bản AI từ **85,9 lên 94,0/100**.
Chi tiết từng lỗi nằm ở `PIPELINE_RULES.md` mục 8k1–8k41. Đây là những luật **vượt ra ngoài bộ
Kling** — chúng sẽ đúng ở bộ tiếp theo, nên để ở đây.

### 13.1 Giới hạn của hệ ngoài phải có ĐƠN VỊ viết ra và NGUỒN dẫn

`KY_TU_MAX = 3000` với ghi chú *"anh dặn prompt 2.500–3.000 từ"*. Trần thật của Kling là **2.500
KÝ TỰ**. Hai đơn vị chênh nhau bảy lần, và hậu quả là **30/30 tệp đã xuất đều bị cắt mất đuôi** —
đuôi là khối `DO NOT`, tức đúng hàng rào chặn lỗi hình. Prompt vẫn gửi được, video vẫn ra, chỉ
là ra xấu hơn mức lẽ ra. Không có gì báo.

**"2.500" không phải một giới hạn — nó là một con số.** Giới hạn là "2.500 ký tự, theo tài liệu
API ngày X".

### 13.2 Cổng đo một TỪ thì lệnh dặn phải LIỆT KÊ chính những từ ấy

Ba cổng đốt **49 vòng gọi AI** trong một lượt chạy 30 tập, và cả ba là lỗi của lệnh dặn:

| cổng | thước tìm | lệnh dặn nói |
|---|---|---|
| `beat` | `beat != "hook"` | **liệt kê `hook` là nhịp hợp lệ** rồi phạt khi dùng |
| `escalate` | một từ trong `again/further/more…` | "phải leo thang thứ đo được" — một Ý |
| `payoff` | một động từ đảo tình thế | "phải là cú lật" — một Ý |

AI viết đúng ý mà sai từ, rồi bị bắt viết lại. Cái đầu tệ nhất: nó **mâu thuẫn**, không chỉ mơ hồ.

Sửa xong, cổng giữ nguyên độ chặt và điểm nhảy 85,9 → 94,0. **Cổng không liệt kê từ nó tìm thì
không phải cổng chất lượng — nó là thuế.**

### 13.3 Chấm mà không chặn thì chỉ là lời khuyên

Luật *"Not 'expensive' but 'nine hundred dollars'"* nằm trong bộ luật hài từ đầu, nhưng chỉ được
**chấm điểm**, không **chặn**. Kết quả: mất 108 điểm ở 18/28 tập, đứng thứ hai trong mọi trục.
**Một luật chỉ trừ điểm là một luật tuỳ chọn.**

### 13.4 Trước khi đo hai thứ có giống nhau không, cắt phần TAY NGHỀ chung ra

Cổng đa dạng chạy lần đầu báo **185/190 cặp kênh vượt ngưỡng**. Cổng sai, không phải dữ liệu sai:
hai phần ba lệnh hệ thống là luật hài và chuẩn hook — thứ **mọi kênh buộc phải dùng chung** vì
đó là tay nghề, không phải bản sắc.

Cùng lỗi ấy lặp **ba lần trong một buổi**, mỗi lần một trường: `style` (0,89 → 0,03 sau khi cắt
`SAN_NGHE`) · `sys` (0,82 → 0,04) · `audio`/`nha`.

**Luật:** hỏi *"phần nào giống nhau là ĐÚNG"* rồi cắt, trước khi đo.

### 13.5 Đo CHUỖI khi thứ cần đo là NỘI DUNG

Sau khi cắt phần chung, `audio` vẫn báo 22 cặp trùng. Đọc lên thì *loa siêu thị · bánh xe đẩy ·
máy quét* và *chuông sân bay · bánh vali · băng chuyền* **không hề giống nhau** — thứ giống nhau
là KHUÔN CÂU. Người xem nghe thấy âm thanh, không nghe thấy cú pháp. Đổi sang Jaccard trên tập
từ: 22 cặp → **0**.

**Họ lỗi:** *chọn phép đo theo thứ dễ tính, không theo thứ người xem cảm được.*

### 13.6 Hằng số sống lâu hơn ngữ cảnh sinh ra nó

`MOC = (0.1875, 0.5625, 0.8125)` lấy từ bộ 500 prompt ở clip **8 giây chia bốn khối**. Nhưng
`nhip()` đã đổi để 8 giây đi nhánh **ba khối** — nên `MOC` chỉ còn dùng cho clip ≥10 giây, **một
ngữ cảnh nó chưa bao giờ được đo**. Ghi chú "lấy từ bộ 500" vẫn đúng về lịch sử và đã sai về
hiện tại; vì nó đọc rất có căn cứ, nó là chỗ cuối cùng người ta nghĩ tới.

**Khi đổi một hàm, đi soát mọi hằng số mà hàm ấy từng nuôi.**

### 13.7 Sai một hằng số tới lần thứ ba thì THÔI TÌM CON SỐ — đo thẳng vật thật

`VAN_KE_MAX` em đặt nhầm **sáu lần**: 800 → 720 → 670 → 640 → 600 → 447. Lần nào cũng "đo cẩn
thận trên cả 10 kênh × 8 thời lượng". Lần nào cũng còn hàng chục trường hợp tràn.

Sáu lần sai vì mỗi lần chỉ mô hình hoá một chiều và bỏ sót chiều khác (độ dài thoại · tên phòng
vs mô tả phòng · số vai có mặt vs vai có thoại · khối bắt buộc mới · web điền cast · **thứ giao
đi là khuôn web chứ không phải đường Python**).

Chữa: `_ngan_sach_khuon()` nhận **chính khuôn sắp giao đi** và ghép bằng **chính phép ghép mà web
sẽ chạy**. Không còn chiều nào để bỏ sót, vì không còn mô hình nào — chỉ còn vật thật.

### 13.8 Cổng BẮT OAN tệ hơn cổng không bắt

Ba chỗ bắt oan tìm được, cả ba chặn kịch bản **hoàn toàn đúng**: phòng `stairwell` (tả là
*"concrete steps"*) chặn chữ `stairs`; phòng `motel room` (tả là *"a boxy TV"*) chặn `television`;
vai tên hai chữ `Chef Nick` bị phép quét một-chữ **xé đôi**, nửa sau thành "người lạ".

Cổng bắt oan không chỉ phiền: nó **ép AI viết lại một kịch bản vốn đúng**, và ép tới hết vòng thì
trả về bản tệ hơn bản đầu. **Nó làm chất lượng đi xuống trong khi trông như đang canh gác.**

### 13.9 Danh sách ngoại lệ là danh sách VÔ HẠN

Cổng chặn nhân vật lạ quét chữ viết hoa và bỏ qua một danh sách (`The · This · That…`). Câu
*"Behind Mike the freezer rattles"* làm cổng chặn một kịch bản đúng. Thêm `Behind` vào rồi mai
`Across`, `Beneath`, `Inside` lại nổ.

Chữ hoa **đầu câu là ngữ pháp, không phải tên riêng**. Bỏ chữ đầu mỗi câu trước khi quét thì chỉ
còn tên thật, và danh sách hết cần dài. **Nhận ra quy luật sinh ra ngoại lệ, đừng liệt kê chúng.**

### 13.10 Cổng cho mã chạy ở môi trường khác phải CHẠY CHÍNH MÃ ẤY

Ba lỗi chỉ hiện ra khi em trích **đúng đoạn JavaScript của dashboard** ra khỏi `index.html` và
chạy nó bằng `node` trên **đúng dữ liệu vừa xuất**. Mọi phép kiểm trước đó viết bằng Python mô
phỏng lại điều web *sẽ* làm — và bản mô phỏng thừa hưởng đúng những giả định sai đang cần bắt.

```bash
node -e 'const s=require("fs").readFileSync("index.html","utf8");
         const code=s.slice(s.indexOf("<mốc đầu>"), s.indexOf("<mốc cuối>"))+"; ({p});";
         /* nạp dữ liệu thật, rồi eval(code) */'
```

### 13.11 Mỗi cổng cần HAI phép thử: không bắt oan, VÀ bắt được

Cổng thoại kiểu Mỹ chạy trên 30 tập thật: **0 lỗi**. Con số ấy một mình có hai cách hiểu ngược
nhau — "thoại đã chuẩn" hoặc "cổng không hoạt động". Phải thử chiều ngược lại: sáu kịch bản cố
tình viết sai, mỗi cái sai một kiểu. **Cả sáu bị chặn đúng lý do** — lúc đó con số 0 mới có nghĩa.

Chỉ có phép thử thứ nhất thì **một cổng chết vẫn xanh**.

### 13.12 Lỗi MÁY SỬA ĐƯỢC thì đừng đốt một vòng gọi AI

AI viết `who: "Nick"` cho vai `"Chef Nick"` và bị thước chặn. Đúng luật, nhưng nó tiêu một vòng
viết lại — một lượt gọi AI và một chỗ trong hạn mức — cho thứ máy sửa được, y như chuyện thiếu
dấu chấm câu. Nay `don()` tự chuẩn hoá, **và chỉ khi khớp DUY NHẤT**: đoán bừa còn tệ hơn chặn.

### 13.13 Bộ lịch chia theo modulo lặp sau `lcm`, không phải sau TÍCH

Cấp cho mỗi tập một bộ N trục bằng `chỉ_số_i = số_tập % độ_dài_i` thì **mỗi trục nhìn riêng đều
trải hết**, nhưng bộ N trục lặp lại sau `lcm(các độ dài)`. Với 7 trục, tích = 7,37 triệu mà
lcm = **240**. Trần to mà lịch không với tới, và không cách nào thấy bằng cách nhìn từng trục.

Chữa: đánh số thẳng trên không gian tích, bước bằng số **nguyên tố cùng nhau với tích**.

Và: `hash()` của Python **đổi theo từng lần chạy** (`PYTHONHASHSEED`) — dùng nó để lệch pha thì
hai môi trường ra hai lịch khác nhau. Phải viết phép băm ra tường minh.

### 13.14 Kiểm bằng MẮT ở CỠ THẬT, không ở cỡ đang xem

Lưới 10 avatar nhìn ở cỡ lớn thì đẹp. Ở **48px** — cỡ avatar thật trong danh sách đăng ký
YouTube — mới thấy huy hiệu số đè lên chữ ở **10/10 kênh**, tên kênh tràn khỏi vòng tròn, và hai
biểu tượng đọc sai hẳn (cờ lê thành chìa khoá, cốc thành hình chữ nhật).

Và khi có 20 kênh thì mắt không dùng lại được: `brand_kling.kiem_bong()` vẽ riêng từng biểu
tượng, hạ xuống 48px, nhị phân hoá rồi so mặt nạ. **Màu không tham gia phép đo** — ở cỡ ấy màu
chỉ giúp phân biệt SAU KHI hình đã khác.

### 13.15 Trước khi kết luận hạ tầng của anh hỏng, kiểm lại BÀI KIỂM của mình

Em đo hồ khoá bằng `urllib` trần, thấy Groq trả `403` trên cả 5 khoá thử, và báo cáo **"83 khoá
Groq đã chết"**. Anh nói khoá vẫn dùng tốt — và anh đúng. `403 error code 1010` là mã chặn bot
của **CDN**, không phải của Groq. Thêm một dòng `User-Agent`: **5/5 khoá OK ngay**.
`content_brain` vốn đã đặt `User-Agent` ở mọi lệnh gọi — chỉ bài kiểm của em là thiếu.

**Bài kiểm phải gọi bằng đúng đường mà mã thật gọi.** Gọi bằng đường khác thì cái hỏng có thể là
bài kiểm, và lúc đó ta đi sửa thứ không hỏng. *(Mã 403/1010/1020 gần như luôn là tầng CDN; ứng
dụng từ chối khoá thì trả 401 kèm giải thích.)*

### 13.16 Chép kịch bản của người khác thì không, nhưng SỐ ĐO công bố thì có

Chép kịch bản kênh hot vừa vướng bản quyền vừa trái luật kênh mình. Thứ tham khảo được là số đo
công bố, và chúng quy được thành cổng:

| chuẩn | dùng vào đâu |
|---|---|
| giữ >80% trong 3 giây đầu (quyết định lướt ~400ms) | hook phải là hình SAI TRÁI sẵn, không dựng cảnh |
| xem hết >70% là vùng được đẩy | cú lật đặt ở cuối, clip ngắn |
| dựng 60–70% · chốt + phản ứng 30–40% | hiệu chỉnh `MOC` (xem 13.6) |
| rewatch là tín hiệu nặng nhất của TikTok | kết ghép vòng được |
| **hài ăn nhất ở 18–28 giây** | **khoảng cách thật: clip Kling dài nhất 15 giây** |
| **đổi hình mỗi 1,5–2 giây** | **khoảng cách thật: Kling cho một cú máy liền** |

Hai dòng cuối **không sửa được bằng prompt** — cần khâu dựng ghép nhiều clip. Ghi ra để lần sau
không đi tìm lời giải ở chỗ không có.

### 13.17 Luật YouTube nêu SÁU DANH TỪ, và cả sáu đều đo được

Luật *"inauthentic content"* (7/2025) nhắm vào sản xuất tự động sinh video từ **prompt · bố cục ·
kịch bản · cảnh · giọng · khuôn chuyện** gần như giống hệt nhau. Phạt: cảnh cáo → treo 90 ngày →
**loại vĩnh viễn khỏi YPP**.

Sáu danh từ ấy là sáu trường trong hồ sơ kênh, nên `kiem_da_dang.py` đo được chúng giữa mọi cặp.
**Chạy cổng này TRƯỚC khi thêm kênh mới** — mười kênh đầu từng có `audio` giống nhau 1,00 mà
không ai thấy, cho tới khi đo. Người viết nhớ được ba kênh, không nhớ hai mươi.

Nhưng phải nói thẳng: cổng chỉ chứng minh **hồ sơ kênh** khác nhau. Thứ YouTube xét là **video**.
Cổng là điều kiện cần, không phải điều kiện đủ.

### 13.18 Luật không cấm "giống kênh khác" — nó cấm "các video của CHÍNH BẠN giống hệt nhau"

Anh phản biện đúng: *"trên thị trường hàng nghìn channel na ná nhau họ vẫn hoạt động ổn"*. Đọc
lại nguyên văn phần **được phép** của luật thì rõ:

> *AI-generated animation **can** qualify when the creator adds original creative direction,
> meaningful variation, useful information, entertainment value, commentary, or a distinctive
> narrative. An animated channel **does not become ineligible simply because AI produced**
> characters, backgrounds, visual effects, rough scripts, voices, or editing elements.*

Nên trục xét **không phải** "kênh này có giống kênh kia không" — mà là **"các video trong CÙNG
một kênh có giống hệt nhau không, và có bàn tay biên tập nào không"**. Đó là lý do nghìn kênh
na ná nhau vẫn sống: mỗi kênh vẫn là một *chương trình*.

Nhận ra điều này đổi hẳn hướng giải: thôi né, chuyển sang **biến dây chuyền thành bộ phim**.

**Ba thứ đã dựng, theo đúng ba chữ mà luật dùng:**

| chữ trong luật | thứ đã dựng | đo được ở đâu |
|---|---|---|
| *meaningful variation* | lịch 7 trục, 3,87–7,37 triệu tổ hợp mỗi kênh, không lặp bộ nào trong 5.000 tập | `_lich()` · `kiem_da_dang.py` |
| *distinctive narrative* | **cú gọi lại**: cứ 4 tập thì nhắc một tập cũ bằng MỘT chi tiết | `goi_lai()` |
| *editorial work* | **sổ biên tập**: mỗi tập ghi lại đã bị từ chối mấy vòng và vì lý do gì | `bien_tap.json` |

### 13.19 Cú gọi lại — thứ duy nhất còn nâng được giữ chân mà không tốn thêm một giây Kling

Lý do thật để làm nó không phải là chính sách, mà là **giữ chân**:

- người xem **cũ** nhận ra cú gọi lại và thấy mình được thưởng → quay lại
- người xem **mới** vẫn hiểu trọn tập, vì cú gọi lại nằm ở **chi tiết**, không ở tiền đề
- không kênh tự động nào làm được, vì nó đòi **trạng thái** — nhớ mình đã kể gì

Hai ràng buộc cứng, cả hai đều có cổng:

1. **Không được là tiền đề.** Phải xem tập cũ mới hiểu tập này thì tập này hỏng với 95% người xem.
2. **Không được tự giải thích.** Câu *"remember when…"* phá cả hai phía: người cũ mất phần thưởng
   vì bị nói toạc, người mới bị nhắc rằng có một tập trước mà mình chưa xem — tức bị đẩy ra.

Và một bẫy dữ liệu: tập cũ lưu trước khi có trường `_dao_cu` thì **KHÔNG tính lại bằng `_lich`** —
bộ lịch đã đổi nên tính lại cho ra một đồ vật KHÁC thứ tập ấy thật sự kể. Dùng thứ tập cũ thật sự
có (cú lật của nó). **Sai nguồn còn tệ hơn không gọi lại.**

### 13.20 Thang điểm đo được CẤU TRÚC, không đo được BUỒN CƯỜI — nên phải đọc tay

28 kịch bản AI sinh ra, trung bình 85,9/100, tất cả đều "sạch thước". Đọc tay sáu tập (hai cao
nhất, hai giữa, hai thấp nhất) thì thấy **bốn lỗi nghề mà mọi cổng đều cho qua** — và cả bốn đều
đo được, chỉ là chưa ai viết ra:

| lỗi | đo được | vì sao lọt |
|---|---|---|
| **bắt Kling vẽ CHỮ đọc được** | **6/28 tập** | `CAM_KY` so CHUỖI CON `"sign reads"`, mà kịch bản viết *"a sign on the shed door that reads…"* · *"one neon note reads…"* · *"spelling out Dr Shah"* — không cái nào chứa đúng hai chữ ấy cạnh nhau |
| chữ **không vẽ được** (*evidence · confirming*) | 1/28 | không cổng nào tồn tại |
| **thoại tự thuật** (*"Kyle, your note made the fridge a sticky wall"*) | 3/28 | không cổng nào tồn tại |
| cú lật không trả lời cú dựng | ~4/28 | cần ngữ nghĩa, chưa đo được |

Cái đầu là cái đắt nhất: chữ trong khung là **chỗ Kling hỏng nặng nhất**, nó ra ký tự loằng
ngoằng và người xem đọc ra "nghiệp dư" trong nửa giây.

**Hai luật rút ra:**

1. **Một danh sách chuỗi con không bắt được ngôn ngữ.** `"sign reads"` là một cách viết trong
   mười cách. Cấm một khái niệm thì phải bằng biểu thức, không bằng danh sách ví dụ.
2. **Cứ vài chục tập phải ĐỌC TAY vài tập.** Thang điểm chỉ biết thứ nó được dạy để đo — và mọi
   thứ nó chưa được dạy đều vô hình, kể cả những thứ hỏng rõ ràng với mắt người. Bốn cổng này
   sinh ra từ đúng một buổi đọc sáu kịch bản.

Và một lỗi bắt oan ngay trong bản đầu của chính bốn cổng ấy: chặn mọi câu gọi tên người khác, nên
`"Grandpa, wait."` — câu gọi giật hoàn toàn tự nhiên — bị chặn. **Gọi tên không phải lỗi; gọi tên
RỒI TẢ TÌNH HÌNH cho người đã đứng trong tình hình ấy mới là lỗi.** Lời dẫn cần chữ, nên chỉ chặn
khi sau cái tên còn từ năm chữ trở lên (*"Kyle, + tám chữ"* bị chặn, *"Grandpa, wait."* thì không).

---

## 13. LUẬT RÚT TỪ NGÀY 1/9 — ĐỢT 18 KÊNH GIẢI THÍCH

Một ngày dài, và **phần lớn thời gian mất vì sửa nhầm phía**. Ghi lại theo đúng thứ tự sẽ gặp lại.

### 13.1 Cơ chế đã có sẵn — hỏi "cái gì CHẠY nó?" trước khi viết cái mới

Bảy lần trong ngày, thứ cần sửa **đã tồn tại trong repo** và chỉ thiếu một thứ gọi nó:

| cần | đã có sẵn | thiếu |
|---|---|---|
| số kho đúng | `apiHotStat` ưu tiên `kho_that`; `kiem_kho.py` đối chiếu Drive | không workflow nào chạy `kiem_kho.py` theo lịch |
| brand kit khác nhau | `BrandGT.tsx` có sáu bố cục `kk` | `brand_gt.py` không truyền `kk` |
| bố cục đổi theo tập | `hat` được tính trong dây chuyền | không bao giờ truyền sang engine |
| màu chữ đọc được | `mauChu` được tính | sáu khối chữ ghi thẳng `#FFFFFF` |
| trần hạn mức | `con_ngan_sach()` ba mức | `don_sach.py` không đi qua |
| cứu video chưa đẩy | `heal_unpushed` | chỉ `run_render.py` (thế hệ cũ) gọi |
| hồ kho không cần Firestore | `_kho_tu_kv` | tôi tưởng KV rỗng, **chưa bao giờ hỏi** |

**Luật:** trước khi viết cơ chế mới, `grep` xem repo đã có chưa. Nếu có mà triệu chứng vẫn còn,
câu hỏi đúng là *"cái gì gọi nó, bao lâu một lần?"* — không phải *"viết lại thế nào?"*

### 13.2 Cổng cầm danh sách chép tay = cổng che lỗi thật

Năm cổng trong ngày cùng một bệnh: `kiem_workflow.CAP` · `kiem_az.RENDER` · `RS_PRESETS` ·
`selftest.t_khong_tron_so` (chỉ soi một tệp) · `t_50_kenh_dong_bo` (danh sách gen-2).

Hậu quả không chỉ là bỏ sót. Ba cổng báo đỏ vĩnh viễn cho việc đã nghỉ khiến **lỗi THẬT nằm
cạnh chúng bị chìm** — `SHARD_PUBLISH` thiếu ở `don_sach.yml` (âm thầm ghi nhầm Project A) chỉ
lộ ra sau khi dọn ba dòng đỏ giả.

**Luật:** cổng phải TỰ TÌM phạm vi của nó — đọc thư mục workflow (lọc theo `cron:` để bỏ luồng
đã nghỉ), đọc `channels.yaml`, đọc `KENH`. Và mỗi cổng mới phải **thử ngược** (cố tình phá) để
chắc nó bắt thật; cổng chưa thử ngược là cổng chưa biết có hoạt động không.

### 13.3 `SystemExit` và `|| true`: hai cách làm hỏng mà vẫn báo xanh

* `content_brain._genai` ném `SystemExit` khi thiếu một thư viện **tuỳ chọn**. `SystemExit` kế
  thừa `BaseException` nên `except Exception` **không bắt được** — nó xuyên qua mọi vòng xoay
  khoá và giết cả tiến trình, dù hồ còn 180 khoá dùng được. 18/18 luồng chết vì một dòng.
* `python day_kho.py ... || true` ở mắt xích cuối: đẩy kho hỏng thì lượt vẫn XANH. Đo được:
  18/18 luồng xanh, `0/2 video vào hàng đợi`, dashboard 0, không dấu hiệu nào báo hỏng.

**Luật:** trong đường chạy tự động, dùng `RuntimeError` chứ đừng `SystemExit`. `|| true` chỉ
được dùng ở bước mà hỏng cũng không mất dữ liệu; ở mắt xích cuối thì phải **ghi cờ, để bước gói
artifact chạy, rồi cho cả lượt HỎNG** — lượt đỏ khiến mốc cron sau tự thử lại, đó là tự động thật.

### 13.4 Đo, đừng suy đoán — kể cả khi suy đoán nghe rất chắc

Bốn lần trong ngày tôi kết luận từ suy đoán rồi số đo bác lại:

* *"chất vẽ lệch 0,44 nên phải siết ngưỡng"* — lập luận toán học đúng (±X quanh mốc cho biên độ
  2X). **Nhìn ảnh** thì cả bốn cùng một thế giới, ảnh điểm thấp chỉ khác ở chỗ có **đổ bóng mềm**.
  Thước `do_phang` đo ĐỘ PHẲNG nên nó phạt cái bóng. Siết ngưỡng = ba lượt vẽ lại mỗi tập để đổi
  lấy không gì. Phải **NỚI**, không siết.
* *"KV rỗng"* — kết luận từ việc log thiếu một dòng in. Dò thẳng: **KV có 100 tài khoản.** Suy
  đoán ấy suýt làm cả hệ chờ 15 giờ vô ích.
* *"Hôm nay: 299 là sai"* — regex của tôi bắt nhầm ô *"📊 Hôm nay: N request"*. Dashboard đúng.
* *"cạn quota do dây chuyền render"* — thủ phạm là **công cụ dọn của chính tôi**, duyệt ~2.000
  tài liệu chỉ để ĐẾM (Firestore có truy vấn đếm: 1 lượt thay cho N).

**Luật:** trước khi sửa, đo cái đang bị chấm trượt. Trước khi báo "đã sửa", đo lại. Và khi con số
với con mắt bất đồng, **nhìn thứ đang bị chấm** rồi mới quyết bên nào sai.

### 13.5 Bốn nguồn sự thật cho một danh sách kênh

Danh sách kênh nằm ở `giai_thich.KENH` · `channels.yaml` · `RS_PRESETS` · `render_channels` (D1
+ Firestore) · `brands.json`. Dọn một nơi rồi báo xong là lỗi đã mắc **hai lần** trong ngày —
lần hai dù chính mã worker ghi sẵn *"hai kho dữ liệu song song thì lệnh dọn phải đụng cả hai"*.

**Luật:** thêm/bớt kênh thì SINH ra từ một nguồn (`dong_bo_dashboard.py`, `dong_bo_brand.py`),
đừng chép tay. Và cổng `kiem_kenh.py` kiểm tám bảng phủ đủ danh sách.

### 13.6 Giờ chạy phải khớp mốc hồi hạn mức

Hạn mức free Firestore hồi lúc **nửa đêm giờ Thái Bình Dương = 07:00 UTC**. Bốn mốc cron đặt
02:20–05:20 UTC đều nổ **trước** lúc hồi — nếu hôm trước có gì làm cạn thì cả bốn lượt dựng xong
rồi đẩy hỏng. Nay 08:20–11:20 UTC.

**Luật:** chọn giờ cron theo mốc hồi của tài nguyên nó cần, không chọn tuỳ tiện.

### 13.7 Ngân sách hạn mức là tài nguyên DÙNG CHUNG

Tôi tối ưu công cụ dọn như việc riêng; nó tiêu đúng cái hạn mức đường render đang cần, và
**17 lượt render xong không lên được Drive**. Mỗi công cụ đụng tài nguyên có hạn phải nối vào
`con_ngan_sach()` — việc phụ dừng ở 70%, cứu dữ liệu tới 92%, thiết yếu luôn chạy.

**Luật:** "số nhỏ" không phải bảo vệ. `~2.500/50.000 = 5%` nghe an toàn cho một lượt; hai mươi
lượt là vượt trần. Chỉ **trần cứng** mới là bảo vệ.

### 13.8 Đọc client cũ trước khi viết client mới

Viết đường gọi HTTP thứ ba tới `/api/hot` và nhận 403. Không phải sai khoá — `hot_db.goi` ghi sẵn
rằng **thiếu `User-Agent` thì Cloudflare chặn mã 1010, trả 403 y hệt sai khoá**. Viết đường mới
là mất cả bài học đã trả giá lẫn cơ chế tự tắt sau 20 lần hỏng.

Cùng dạng: đặt `def _hot(...)` trong `storage.py` mà tệp **đã có** `def _hot()` khác ở dưới —
hàm khai sau thắng, và tầng D1 im lặng ném `TypeError`.

**Luật:** `grep "def <tên>"` trước khi đặt tên hàm. Chú thích trong client cũ là những lần đã
trả giá.

### 13.9 Không dựng công cụ BẤM TAY để chữa một hệ tự động

Khi Drive không nhận video, tôi dựng một workflow tải artifact về rồi đẩy lên. Anh gạt ngay, và
đúng: nó biến hệ tự động thành hệ cần người trực. Lỗi thật là một dòng `|| true` trong luồng tự
động — sửa ở đó thì hệ tự chữa qua bốn mốc cron.

**Luật:** khi một hệ tự động không giao được hàng, sửa **đường tự động**. Công cụ tay chỉ dùng
để CHẨN ĐOÁN, không để thay thế.

### 13.21 Nới biểu thức TRƯỚC khi làm cổng trên nó

Đề bài chỉ định cơ chế cú lật, nhưng không cổng nào kiểm nó có được dùng không — nên **6/12 tập
rơi về "nhấc lên → lộ ra"**, đúng họ đã mòn 16/30 lần trong kho. Cấp mà không kiểm thì lại thành
lời khuyên (13.3).

Nhưng đo lần đầu chỉ **5/12** khớp cơ chế được giao, và làm cổng ngay lúc ấy sẽ chặn 7/12 — trong
đó **4 ca là biểu thức của tôi quá hẹp, không phải AI viết sai**:

| AI viết | cơ chế được giao | biểu thức thiếu |
|---|---|---|
| *"turns out it was already **set** to 7"* | người-thứ-ba-đã-xong | chỉ nhận `already done/fixed/finished/handled` |
| *"already **tucked** underneath"* | người-thứ-ba-đã-xong | như trên |
| *"Deb **slides out**, already done"* | kẻ-thản-nhiên-bỏ-đi | chỉ nhận `steps out` |
| *"revealing the scissors **behind Mike**"* | thủ-phạm-lộ-diện | chỉ nhận `behind him/her/them`, không nhận tên riêng |

Nới xong: **5/12 → 10/12**, và hai ca còn lại mới là lỗi thật. Cổng nay chặn đúng hai ca ấy.

**Luật:** làm cổng trên một biểu thức hẹp là **chế tạo thêm một cổng bắt oan**. Trước khi biến
một phép so thành cổng, chạy nó trên dữ liệu thật và **đọc tay mọi ca trượt** — nếu quá một phần
tư số ca trượt là do phép so chứ không do dữ liệu, thì phép so chưa đủ chín để làm cổng.

Và một dấu hiệu để nhận ra sớm: hai bảng nói về cùng một thứ mà **không khớp nhau**. `HO_LAT` họ
đầu tiên bắt đầu bằng `lifts?`, trong khi danh sách "đổi hình dạng" của cổng 5 giây lại không có
`lifts` — một bảng gọi nó là cú lật, bảng kia bảo nó không phải đổi hình.

### 13.22 Đo xong rồi QUYẾT ĐỊNH KHÔNG LÀM CỔNG cũng là một kết quả

Ba chỗ còn dang dở, đo trên 42 kịch bản thật. Hai cái làm cổng, **một cái quyết định không làm**:

| chỗ | đo được | quyết định |
|---|---|---|
| câu ghim máy lặp / nhét vào đuôi | 3/42 · 1/42 | **làm** — cổng đơn giản, chính xác |
| nhấc một vật gắn cố định | 1/42 | **làm** — hiếm, nhưng khi xảy ra thì cả clip hỏng |
| cú lật có trả lời cú dựng không | 2/42 | **KHÔNG làm** |

Cái thứ ba: phép đo là *"payoff có chia một danh từ nào với hook/setup không"*. Nó bắt đúng 2 ca —
và **đọc lên thì cả hai đều là kịch bản tốt**: *"Deb slides out, already done."* (97/100) không
chia danh từ nào vì nó cô đọng và trỏ ngược ngầm; *"Grandpa Joe walks in holding an empty
bottle — the flood was just his water bottle"* trả lời cú dựng rất gọn nhưng bằng chữ khác.

Nếu ship, cổng ấy sẽ là một **cỗ máy bắt oan**: 2/2 ca nó bắt đều sai. Nên không ship, và ghi ra
đây rằng *chỗ này chưa đo được* — thay vì ship một cổng tệ rồi tin là đã giải quyết.

**Luật:** một cổng chỉ đáng ship khi **đọc tay các ca nó bắt** và thấy chúng thật sự hỏng. Tỉ lệ
bắt cao không phải bằng chứng cổng tốt; nó cũng có thể là bằng chứng cổng sai. Và *"chưa đo được"*
ghi vào buglog là một kết luận hợp lệ — nó ngăn phiên sau đi làm lại đúng cái cổng đã bị bác.

Chi tiết hẹp cũng có giá: `machine` và `cabinet` bị loại khỏi danh sách vật gắn cố định, vì máy
pha cà phê thì nhấc được còn máy bán hàng thì không. **Một chữ có hai nghĩa vật lý là chữ không
dùng làm cổng được.**

### 13.23 Một cổng ĐÚNG vẫn có thể làm giảm chất lượng — đo bằng ĐIỂM CUỐI, không bằng số lỗi bắt được

Thêm hai cổng nghề (cơ chế cú lật · câu ghim máy). Cả hai bắt đúng lỗi thật. Kết quả lượt đo:

| lượt | TB | ≥95 | tập cạn 8 vòng |
|---|---|---|---|
| trước khi thêm | **92,8** | 3/6 | 1/6 |
| sau khi thêm | 90,2 | **0/6** | 3/6 |
| sau khi nới biểu thức | 92,5 | 1/6 | **6/6** |

Cổng không sai. Nhưng **ngân sách vòng viết lại là hữu hạn** (tám vòng), và hai cổng ấy nuốt hết:
đo trên 24 tập của bốn lượt, chúng chiếm **13/26 lỗi tồn**. Các trục khác vì thế không còn lượt
nào để sửa, nên điểm tổng đi xuống dù mỗi cổng riêng đều đúng.

**Chữa bằng cách hạ cấp, không phải bằng cách bỏ:**

| cổng | trước | sau | vì sao |
|---|---|---|---|
| cơ chế cú lật | **chặn** | **chấm** (`cham100` trục 2, −4 điểm nếu sai) | vẫn có răng qua sàn 90, nhưng cạnh tranh với chín trục kia thay vì chặn đứng |
| câu ghim máy lặp | **chặn** | **`don()` tự cắt** | hại của nó chỉ là tốn 25 ký tự và đọc như văn mẫu — không hỏng hình. Máy sửa được thì máy sửa (13.12) |

Lỗi tồn trên 24 tập: **26 → 14**.

**Luật:** khi thêm một cổng, đo lại **điểm cuối cùng**, không đo số lỗi nó bắt được. Một cổng bắt
nhiều lỗi có thể là cổng đang làm hỏng sản phẩm. Và mỗi cổng mới phải trả lời được: *"nếu kịch
bản chỉ sai mỗi chỗ này thì có đáng tiêu một lượt gọi AI không?"* — nếu không, nó thuộc về
`don()` (máy tự sửa) hoặc `cham100` (trừ điểm), không thuộc về `cham()`.

Ba nấc, và chọn nấc là một quyết định thật:

```
don()      máy sửa được       -> sửa, không báo
cham100()  làm kém đi         -> trừ điểm, cạnh tranh với các trục khác
cham()     làm HỎNG sản phẩm  -> chặn, tiêu một vòng gọi AI
```

### 13.24 SÀN không phải mức tối thiểu — nó CHÍNH LÀ chất lượng đầu ra

Đo phân bố điểm của 30 tập AI sinh thật qua sáu lượt:

```
81:2  86:1  87:2  88:1  89:1  90:10  92:3  94:2  95:1  97:2  98:5
                              ^^^^^ đúng bằng sàn
```

**10/30 rơi CHÍNH XÁC vào 90** — sàn đang đặt. Không phải trùng hợp: `sinh_tap` dừng vòng lặp
ngay khi `cham100 >= DIEM_SAN`, nên **không có gì thưởng cho việc viết hay hơn mức đủ**. Hệ tối
ưu đúng thứ được bảo tối ưu, và dừng ở đó.

Suốt buổi tôi đi chỉnh cổng, nới biểu thức, hạ cấp cổng — tất cả đều đúng và cần, nhưng **cái
đòn bẩy trực tiếp nhất lại là một con số tôi tự đặt và không xét lại**. Muốn 95 thì đặt 95.

Hai thứ phải đi kèm khi nâng sàn:

1. **Thêm vòng viết lại** (8 → 12) — sàn cao hơn cần nhiều lượt thử hơn.
2. **Trả bản TỐT NHẤT, không phải bản CUỐI.** Đây mới là chỗ hỏng thật sự: bản cũ cạn vòng thì
   trả lần viết gần nhất, mà chất lượng **không tăng đều theo vòng** — đo được lượt thứ ba đạt
   94 rồi lượt thứ tám tụt còn 81, và hệ trả về 81. Vòng viết lại là một cuộc **tìm kiếm**,
   không phải một cuộc mài giũa; phải nhớ điểm cao nhất đã đi qua, nếu không thì tám vòng có
   thể tệ hơn ba vòng.

**Luật:** khi một hệ có ngưỡng chấp nhận, đi đo **phân bố kết quả** — nếu nó dồn cục ngay trên
ngưỡng thì ngưỡng đang là trần, không phải sàn. Và mọi vòng lặp "thử tới khi đạt" phải nhớ bản
tốt nhất, vì lần thử cuối không có lý do gì để là lần thử tốt nhất.

### 13.25 Kho rỗng không được cho điểm miễn phí — và tôi đã báo cáo con số bị thổi

Trục "cú lật có mới không" chấm theo **độ hiếm trong kho**. Kênh mới có kho rỗng, nên `lan = 0`
và trục ấy tự động được điểm tối đa. Đo được: cùng một kịch bản GYM FLOOR chấm **95** khi so với
kho của chính kênh (0 tập) và **90** khi so với kho 30 tập — chênh đúng 5 điểm của trục này.

Hậu quả: **mười kênh mới luôn cao điểm hơn mười kênh cũ cho cùng chất lượng viết**, và mọi câu
"kênh mới tốt hơn" tôi nói trong buổi đều là ảo giác của phép đo. Tôi đã báo TB 94,3 khi con số
thật là **93,2**.

Chữa: kho dưới 8 tập thì độ hiếm không có nghĩa thống kê — chấm bằng thứ đo được **không cần
kho** (cơ chế có phải họ đã mòn không). Nhờ vậy kênh mới và kênh cũ so được với nhau.

**Luật:** mọi trục chấm theo "so với lịch sử" đều có một lỗ ở **điểm bắt đầu**, nơi lịch sử rỗng.
Lỗ ấy luôn nghiêng về phía cho điểm cao, vì "chưa từng lặp" và "chưa có gì để lặp" trông giống
hệt nhau trong công thức. Hỏi thẳng: *"trục này chấm gì khi n = 0?"*

Và một luật về báo cáo: **hai phép đo cho hai con số thì phải truy ra vì sao trước khi báo con số
nào**. Tôi thấy `sinh_tap` nhận một tập 90 điểm trong khi sàn là 95, và suýt bỏ qua nó như một
chi tiết lạ — chính chi tiết ấy là sợi dây dẫn tới lỗ hổng.

### 13.26 Sáu mẫu một lượt không phân biệt được 90 với 93 — tôi đã đọc xu hướng từ nhiễu

Chấm lại 42 tập của bảy lượt bằng một phép đo nhất quán:

```
độ lệch chuẩn của một tập        : 4,7 điểm
sai số chuẩn của một lượt 6 mẫu  : ±1,9
khoảng tin cậy 95%               : ±3,7
```

Chênh lệch giữa lượt tốt nhất (93,2) và tệ nhất (89,5) là **3,7 điểm — đúng bằng khoảng tin cậy**.
Nói cách khác: **cả bảy lượt không phân biệt được với nhau**. Suốt buổi tôi kể một câu chuyện
"85,9 → 90,3 → 92,8 → 90,2 → 92,5 → 91,2 → 94,3", giải thích từng bước lên xuống bằng một
nguyên nhân — mà phần lớn các bước ấy là **nhiễu ngẫu nhiên của sáu mẫu**.

**Thứ THẬT SỰ vượt ngưỡng nhiễu là tỉ lệ CẠN VÒNG**, vì nó là biến nhị phân đếm được:

| lượt | thay đổi | cạn vòng |
|---|---|---|
| 2 | sửa 2 cổng bắt oan | **1/6** |
| 5 | hạ cấp 2 cổng | **1/6** |
| 4 | thêm 2 cổng nghề, biểu thức hẹp | **6/6** |
| 7 | sàn 95 | 5/6 |

Đây mới là tín hiệu dùng được: hai bản sửa cổng có tác dụng rõ ràng, và siết cổng có hại rõ ràng.
Điểm trung bình thì không nói được gì ở cỡ mẫu này.

**Luật:** trước khi giải thích một thay đổi giữa hai lần đo, tính **sai số chuẩn của phép đo**.
Nếu chênh lệch nhỏ hơn khoảng tin cậy thì không có gì để giải thích — và mọi câu giải thích viết
ra lúc ấy đều là chuyện bịa nghe hợp lý. Với cỡ mẫu nhỏ và chi phí mỗi mẫu cao, hãy đo bằng
**biến đếm được** (đạt/không đạt, cạn/không cạn) thay vì bằng trung bình.

### 13.27 Ảnh bìa cắt ở 62% thời lượng — với short thì đó là chỗ LỘ CÚ LẬT

`run_render._make_thumb()` trích khung ở **62% thời lượng**. Với video dài của bộ phân tích đó là
chỗ đẹp (lúc biểu đồ đã cao, số đã lớn). Với short Kling thì đó là chỗ **tệ nhất**:

| độ dài | cú lật bắt đầu | khung 62% rơi vào |
|---|---|---|
| **5s** | 34% | **cú lật — lộ** |
| **6s** | 33% | **cú lật — lộ** |
| 7–8s | 67–69% | phần dựng |

Và 5–6 giây chính là **vùng ưu tiên** vì Kling tính tiền theo lượt. Nên phần lớn ảnh bìa của bộ
này đang kể trước cái kết — mà **không có lỗi nào báo ra**: ảnh vẫn đúng cỡ, vẫn lên YouTube,
chỉ là nó làm hỏng đúng thứ nó sinh ra để bán.

`kling_dong_bo.lam_bia()` lấy khung ở **giữa nhịp hook** — đúng cái hình sai trái được thiết kế
để chặn ngón tay người xem, và là hình duy nhất trong clip không tiết lộ gì.

**Họ lỗi:** *một hàm dùng chung mang theo giả định của bộ sinh ra nó.* `_make_thumb` đúng cho
video dài, và sai cho short vì cấu trúc nhịp của hai bộ ngược nhau — video dài dồn thông tin về
cuối, short dồn cú lật về cuối. Cùng con số 62%, hai ý nghĩa trái ngược.

Và hai lỗi tự gây ra khi vẽ bìa, cả hai đều chỉ thấy khi **nhìn ảnh**, không thấy khi đọc mã:

- **biểu tượng thương hiệu tàng hình** khi khung hình tình cờ cùng tông với màu kênh. Với hai
  mươi kênh thì sớm muộn sẽ có tập rơi đúng vào tông ấy. Chữa: đĩa tối mờ đặt sau biểu tượng —
  cách mọi hãng đặt logo lên một khung hình bất kỳ.
- **bóng chữ là bóng CỨNG có bậc**: tôi vẽ ba bản chữ lệch nhau vài điểm ảnh và gọi đó là bóng
  mềm. Bóng mềm phải là một lớp riêng đem **làm mờ**, không phải bản sao dịch chỗ. Đây đúng dấu
  hiệu nghiệp dư đã liệt kê ở 12.12 — tôi viết ra luật ấy rồi vi phạm nó trong cùng một buổi.

---

## 14. LUẬT RÚT TỪ NGÀY 2/9 — MỞ RỘNG 20 → 30 KÊNH KLING

### 14.1 Thêm mười cái GIỐNG NHAU không phải là mở rộng

Hai mươi kênh Kling đầu đều là **một** thể loại: nơi chốn Mỹ đời thường có thật · dàn người ·
đồ vật gây mâu thuẫn · thoại hiện đại. `kiem_da_dang.py` đo chữ giữa từng cặp và xanh — nhưng
nó **không đo hạng mục**. Cổng xanh với hai mươi bản của cùng một cỗ máy hài, và sẽ xanh y hệt
với năm mươi bản.

Nên mười kênh mới là **mười CỖ MÁY HÀI khác nhau**, không phải mười căn phòng khác nhau:

| | kênh | cỗ máy |
|---|---|---|
| 21 | QUEST BOARD | thế giới sử thi vận hành bằng thủ tục hành chính |
| 22 | ORBIT SHIFT | không gian khổng lồ, bất bình tí hon, không vứt được gì đi |
| 23 | THE HAUNTING | ba người chết cố gửi tin, một người sống hiểu thành hỏng ống nước |
| 24 | DOG PARK | chuyện người lớn nghe lỏm qua tai chó, ráp lại bằng logic chó |
| 25 | SALOON 1884 | huyền thoại biên giới thua cuốn sổ nợ (không ai rút súng) |
| 26 | DISPATCH | bình tĩnh tuyệt đối trả lời hoảng loạn tuyệt đối, việc luôn vô hại |
| 27 | ENGINE 12 | kỷ luật cứu hoả đem áp cho cái tủ lạnh chung, chuông không bao giờ reo |
| 28 | SMALL CLAIMS | toàn bộ nghi thức tư pháp xử vụ sáu mươi đô, tang vật nói ngược chủ |
| 29 | COUNTY FAIR | năm mươi năm thứ bậc làng nén vào một cuối tuần tranh ruy băng |
| 30 | THE CRUISE | niềm vui bắt buộc trên con tàu không ai rời được |

Đo sau khi thêm: 435 cặp, trục `hai` cao nhất **0,15** trên trần 0,30 — tức mười cỗ máy mới kéo
mức trùng xuống chứ không đẩy lên.

### 14.2 Bộ lịch phát cho một kênh nhịp mà thế giới ấy KHÔNG DIỄN ĐƯỢC

DOG PARK nhận đề *"khói hoặc hơi bốc lên từ thứ lẽ ra không được bốc khói"*. Công viên chó
ngoài trời không có gì bốc khói được. Đề bài nói rõ bảy trục là **cố định**, nên AI làm đúng
thứ được bảo: một cái ghế nhựa cháy âm ỉ giữa bãi cỏ. Vô nghĩa hoàn toàn — và:

- `cham()` **không bắt** (nó đo tay nghề, không đo vật lý của thế giới)
- `cham100` chấm **91/100**

Đúng luật 12.5: `KIEU_MO` viết cho hai mươi thế giới trong nhà. Chữa không phải bằng cách dặn
AI "đừng vô lý" — đề bài đã nói bảy trục cố định, dặn thêm chỉ tạo mâu thuẫn. Chữa bằng cách
**đừng phát nhịp ấy cho kênh ấy**: `mo_cam` trong hồ sơ kênh, lọc ở đúng một chỗ `_mo_kenh()`.

Và trong lúc sửa, mắc thêm một lỗi kinh điển: `("smoke or steam")` **là chuỗi**, không phải
tuple. Rồi câu dự phòng `... or KIEU_MO` **che mất** — lọc sạch trơn thì lặng lẽ trả về đủ 16 và
cổng báo "16/16, không sao". Nay lọc sạch trơn thì **nổ**, vì nó luôn luôn là lỗi viết sai.

### 14.3 Dàn vai phải chứa được XUNG ĐỘT của chính kênh ấy

SMALL CLAIMS bản đầu có bốn vai: thẩm phán · chấp hành viên · lục sự · một ông hưu trí ngồi
xem. Cả bốn đều là **người của toà**. Kênh nói về tranh chấp giữa hai người — mà không có hai
người ấy trong dàn. Bộ lịch cấp "Fern gây ra chuyện", AI làm đúng: **lục sự kiện chấp hành
viên đòi sáu mươi đô**. Điểm: 91/100.

Câu hỏi phải hỏi khi viết một kênh mới: *"đọc `hai` lên, dàn vai này có đủ người để diễn cái
xung đột ấy không?"* Toà cần **nguyên đơn và bị đơn**. Nay là: thẩm phán · chấp hành viên ·
**Dot và Vern** — hai nhà hàng xóm bốn mươi năm, tuần nào cũng ra toà vì chuyện mới.

### 14.4 Avatar bị cắt TRÒN — và bản vá lần trước chỉ bỏ vòng tròn TÔI vẽ

Chú thích trong `avatar()` ghi rõ đã sửa lỗi "vòng tròn cắt ngang chữ" bằng cách **bỏ vòng
tròn**. Nhưng YouTube, Facebook và Instagram đều **tự cắt avatar thành hình tròn** — bỏ vòng
tròn của mình không làm vòng tròn của họ biến mất. Ghép lưới rồi vẽ đè đường cắt tròn lên:

- dải tên bị cắt ngang **giữa dòng chữ** — đo được **20/20** kênh dựng bằng bố cục cũ
- huy hiệu số ở góc khung vuông cách tâm 0,57·W, ngoài bán kính 0,5·W → **không nền tảng nào
  từng hiển thị nó**

Khung an toàn không phải hình vuông W×W mà là **đường tròn nội tiếp**, và bề ngang cho phép
**đổi theo độ cao**: nửa dây cung = √(R² − d²). Khối chữ phải neo theo **đáy** của nó, vì chỗ
hẹp nhất là dòng dưới cùng.

Cổng `kiem_tron()` đo trên **ảnh thật**, không đọc mã: đếm pixel màu nền nằm ngoài đường tròn
trong vùng dải màu. Calibrate ngược trên bố cục cũ → bắt 20/20; bố cục mới → 0/30.

### 14.5 `chinh` là màu của DẤU HIỆU, không phải màu của bộ phim

Mười kênh mới lần đầu lấy màu **không khí** làm màu thương hiệu: đỏ huy hiệu cho sảnh hội mạo
hiểm, đỏ tiết cho phòng xử. Đúng cho một khung phim. Sai cho một hình tròn 48 điểm ảnh trong
danh sách đăng ký:

| | tương phản biểu tượng/nền |
|---|---|
| SMALL CLAIMS `#7B2233` | **1,74** |
| QUEST BOARD `#8C2F39` | **2,06** |
| hai mươi kênh đang có | 2,61 – 10,98 |

Thấp hơn **mọi** kênh đang có, và nhìn lưới avatar thì hai biểu tượng ấy gần như biến mất. Cùng
họ lỗi với `k["mau"]` ở luật số 6 và với biểu tượng tàng hình trên ảnh bìa (13.27): *mượn một
giá trị cho việc nó không sinh ra để làm*. Bảng màu phim để ở `phu`; `chinh` phải đọc được.
Cổng `kiem_tuong_phan()` sàn 3,0.

### 14.6 Điểm 91 và bản thảo vô nghĩa cùng tồn tại được

Ba lỗi ở 14.2 · 14.3 và một cú chốt không có cú lật đều **đi qua** thang 100 điểm với 91–94.
Không phải thang điểm hỏng — nó đo tay nghề viết, và tay nghề viết ở cả ba bản thảo ấy đều
đúng. Cái sai nằm ở tầng **thế giới có diễn được không**, tầng mà chưa thước nào đo.

Nên khi mở một kênh mới: **đọc tận mắt ít nhất ba bản thảo**, không nhìn điểm. Điểm chỉ đủ để
so kênh mới với kênh cũ, không đủ để duyệt một kênh mới.

### 14.7 `cham100` tra thẳng `tap["payoff"]` — thước sập theo kịch bản hỏng

Bốn chỗ trong `cham100` dùng `tap["payoff"]` trong khi mọi chỗ khác dùng `.get`. Một tập thiếu
khối chốt làm cả thước nổ `KeyError`, mà thước nổ thì `sinh_tap` **mất luôn bản đang giữ** —
hỏng mà không để lại gì, đúng họ lỗi 10.1. Thước phải **chấm điểm thấp** cho một tập thiếu
khối, không được chết theo nó.

### 14.8 Hai ngân sách khác bản chất gộp vào MỘT bộ đếm — vòng viết lại chết mà log vẫn đẹp

Lỗi lớn nhất của ngày, và nó ẩn sau một con số trông rất bình thường.

`sinh_tap` đếm vòng bằng `for lan in range(1, VONG_VIET + len(ho) + 1)`. Một biến `lan` phục vụ
**hai** việc: đếm lần viết lại (ngân sách 12) và đếm lần duyệt hồ khoá (ngân sách 295). Mỗi khoá
trả 429 làm `continue` — **tiêu một `lan` mà không viết được chữ nào**. Hồ có ~100 khoá
Cloudflare cạn hạn mức mỗi ngày, nên tới lúc AI viết được bản nháp ĐẦU TIÊN thì `lan` đã là 99,
và câu `if lan >= VONG_VIET: break` bắn ngay lập tức.

```
   🔑 đổi key (76/295): 429 rate limit daily
   ↻ vòng 99: không có một lượng chính xác nào…
   ⚠️ 12 vòng chưa sạch — trả bản cuối kèm 2 điểm sửa tay
```

Mười hai vòng viết lại chỉ còn **trên giấy**. Thực tế: một bản nháp, lấy hay bỏ. Đo được
10/16 tập "sạch ở vòng 1" và 6/16 trả về kèm lỗi — trông như "AI viết khá, thỉnh thoảng hụt",
mà thật ra là **không có vòng sửa nào tồn tại**.

Đây là lý do gốc của mọi thứ đã đi chữa ở tầng trên: sàn 95 điểm, mười hai vòng, thang một trăm
điểm, cổng nới rộng — tất cả đều giả định có một vòng lặp sửa bài. Không có nó thì chúng chỉ là
bộ lọc một lần.

**Họ lỗi:** *gộp hai ngân sách khác bản chất vào một bộ đếm.* Và bản vá sinh ra nó cũng đúng ở
thời của nó — trước đó dừng ở `MAX_TRIES` nên năm khoá hỏng liên tiếp là bỏ cuộc. Chữa một đầu,
mở ra đầu kia. Chỗ nhận ra: **câu log tự mâu thuẫn** — "vòng 99" đứng cạnh "12 vòng chưa sạch".
Hai con số nói về hai thứ khác nhau mà mang cùng một tên.

**Luật:** một biến đếm chỉ được đại diện cho MỘT thứ. Khi thấy `A + B` trong một cận vòng lặp,
hỏi ngay: hai thứ ấy có tiêu cùng một tài nguyên không? Ở đây là không — đổi khoá không tốn
lượt viết, và lượt viết không tốn khoá.

### 14.9 Khuôn hình: đa dạng phải nằm ở thứ người xem NHÌN THẤY

Bộ lịch bảy trục đổi rất giỏi *chuyện*, nhưng `_bat_buoc` **ghi cứng** `"Camera locked off at
standing eye level, wide."` vào mọi prompt của mọi kênh, còn đề bài thì liệt kê ba lựa chọn và
AI luôn lấy cái đầu. Đo: **6/6 bản thảo mở bằng cùng một câu**. Ba mươi kênh, mọi tập, một khuôn
hình — đúng chữ *"cảnh"* trong câu luật YouTube về nội dung hàng loạt.

`KHUON_HINH`: tám khuôn **tĩnh**. Biến thể ở CHIỀU CAO · KHOẢNG CÁCH · TIỀN CẢNH, không ở chuyển
động — hàng rào cấm pan/zoom/dolly/drone và cấm thế là đúng.

Ba lỗi tự gây ra trong lúc làm, cả ba chỉ đo mới thấy:

| lỗi | số đo | vì sao |
|---|---|---|
| nhét thành trục thứ tám của bộ lịch | **144/199** tập liền nhau trùng khuôn | trục thêm sau cùng là **chữ số cao nhất**, đi thành vệt dài — dù tổng thể vẫn dùng đều 28 lượt/khuôn |
| ghi cứng bước 3 | kênh còn 6 khuôn chỉ dùng **2** | `gcd(3,6)=3`. Luật 13.6: hằng số sống lâu hơn ngữ cảnh |
| khuôn web dựng một lần cho cả kênh | mọi tập từ web mang khuôn của tập 0 | câu máy bị nướng cứng vào khuôn — đúng cái lặp vừa chữa, ở phía web |

Cái đầu quan trọng nhất về mặt phương pháp: **"cả tám khuôn có được dùng đều không" không phải
thứ người xem cảm được**; thứ họ cảm được là "hai tập liền nhau có trông khác nhau không". Chọn
sai đại lượng thì số đo đẹp mà sản phẩm vẫn lặp.

Và một quyết định **bỏ bớt**: khuôn `top-down` bị loại khỏi bảng, vì trong khung dọc 9:16 nhìn
thẳng từ trên xuống thì không còn mặt người — mà cả bộ chạy bằng thoại có lip sync. Một khuôn
hình đẹp mà phá cơ chế chính của sản phẩm thì không phải đa dạng.

`khuon_cam` cho ba kênh khoá chiều cao máy ngay trong bản sắc (DOG PARK *"camera sits at dog
height"*, PET HOUSE *"knee height"*, ROAD TRIP *"fixed camera on the dashboard"*). **Không nới
câu `style` của chúng** — nới thì mất bản sắc để lấy một khuôn hình, đổi sai chiều.

### 14.10 "Trả bản tốt nhất" đã sửa ở nhánh điểm, còn nguyên ở nhánh LỖI

Luật 13.24 dạy trả bản tốt nhất thay vì bản cuối, và `_tot` làm đúng thế. Nhưng `_tot` chỉ nhận
những bản **đã qua `cham()`** (vì `cham100` chỉ chạy khi `not loi`). Nên nhánh "không bản nào
sạch" — 4/6 tập của lượt đo — vẫn trả bản viết **sau cùng**, trong khi số lỗi không giảm đều
theo vòng. Nay giữ thêm `_it` = bản ít lỗi nhất.

Đúng họ lỗi số 6: *vá một nhánh, để nguyên nhánh song song*.

### 14.11 Luật vật lý của thế giới phải đứng thành LUẬT, không nằm trong câu tả cơ chế hài

Đọc một bản thảo THE HAUNTING đã **sạch mọi cổng** và đạt 90/100:

> Trish: *It's stuck again, can't move!* · Ivy: *Just unplug.*

Trish là người sống và **không nhìn thấy ma**; Ivy là ma. Tiền đề của kênh bị phá ngay ở dòng
thoại đầu tiên. Không thước nào bắt: `cham()` đo tay nghề, `cham100` đo cấu trúc, và cả hai đều
không biết thế giới này vận hành ra sao.

Điều ấy CÓ nằm trong `hai` — nhưng nằm như một câu *tả cơ chế hài*, giữa những câu về status và
leo thang. Mô hình đọc nó như gợi ý phong cách, vì nó được đặt ở chỗ dành cho gợi ý phong cách.

`luat_the_gioi`: khối riêng, đặt ngay sau cơ chế hài và **trước** đề bài, mở đầu bằng *"these
are not style notes"*. Mười kênh mới đều có: ORBIT SHIFT *"nothing falls"* · DOG PARK *"dogs
have no hands"* · SALOON 1884 *"no electricity, no telephone"* · ENGINE 12 *"the alarm never
sounds"* · DISPATCH *"the caller is never seen"*.

**Luật:** một ràng buộc chỉ được tuân thủ ở mức tương ứng với **chỗ nó được đặt**. Cùng một câu,
để trong đoạn tả phong cách thì thành gợi ý, để trong khối luật thì thành luật. Trước khi kết
luận "AI không nghe lời", đi xem câu ấy đang nằm ở đâu trong lệnh hệ thống.

Và làm theo đúng thứ tự: **cấp luật bằng đề bài trước, đo, rồi mới tính chuyện làm cổng** — thêm
cổng là tiêu ngân sách vòng viết lại, và ngân sách ấy vừa mới được cứu sống ở 14.8.

### 14.12 Luật bằng lời không cưỡng chế được điều tuyệt đối — đo rồi mới biết

Sau 14.11 em cấp luật thế giới bằng một khối riêng trong lệnh hệ thống, mở đầu bằng *"these are
not style notes"*. Đo lại: **2/2 bản thảo vẫn cho Trish nói và vẫn cho ma nhấc tủ lạnh.**

Đây là kết quả đáng giá, vì nó bác đúng giả thuyết em vừa đặt ở 14.11. Câu luật ở đúng chỗ vẫn
chưa đủ khi ràng buộc là **tuyệt đối** (không bao giờ, không ngoại lệ) — mô hình đọc "không bao
giờ" như "hiếm khi".

Chữa ở **gốc thiết kế**, không ở lời dặn: Trish **không có thoại**, giống hệt cách DOG PARK xử
lý con người (họ là thời tiết). Ràng buộc tuyệt đối biến thành một im lặng cưỡng chế được bằng
một phép `in`, không mơ hồ, không thể bắt oan.

Và cơ chế ấy **đã tồn tại trong repo** — chép cứng: `if who == "Buddy"` (con mèo của HOUSE
RULES). Đúng luật 13.1: trước khi viết cơ chế mới, đi tìm cái đang có. Nay là `khong_thoai`, một
trường khai báo, hai kênh dùng chung.

**Luật:** khi một ràng buộc là *tuyệt đối*, đừng viết nó thành câu — hãy làm cho nó **không thể
vi phạm**. Nếu không làm được thế thì nó không phải ràng buộc tuyệt đối, và đừng viết "never".

Thứ tự đã đi, và là thứ tự đúng: đọc bản thảo → thấy lỗi → **cấp luật bằng lời** → đo → luật
không ăn → **chữa ở thiết kế + một cổng rẻ nhất có thể**. Ba bước đầu không bỏ được: nhảy thẳng
vào cổng thì không biết cổng có cần thiết không.

---

## 15. LUẬT RÚT TỪ NGÀY 2/9 — MỘT HỌ LỖI, SÁU LẦN, TRONG MỘT NGÀY

Ngày này không có sáu lỗi khác nhau. Nó có **một** lỗi, mặc sáu bộ quần áo. Ghi ra để lần sau
nhận mặt nó ở bộ thứ bảy.

### 15.1 Phép CẮT đặt trước phép LỌC

Ba chỗ, ba tệp, cùng một hình dạng:

```python
.where("owner","==",owner).limit(400)        # lấy 400 bản ghi đầu
    if _ten(j) in giu: continue              # rồi MỚI lọc kênh cũ
```
```js
const ds = s.docs.sort(theo_thoi_gian).slice(0,20);   // cắt 20 dòng nhật ký
        ... rồi mới lọc kênh đang dùng
```

400 bản ghi đầu toàn kênh đang dùng thì lượt dọn xoá đúng **0** — và lượt sau lấy lại đúng 400
bản ghi ấy, mãi mãi. 20 job mới nhất toàn kênh đã nghỉ thì nhật ký ra **rỗng**, trong khi job
của 18 kênh nằm ngay dưới lằn cắt.

Ở chỗ dọn, cái trần còn đặt **sai đại lượng**: trần trên số ĐỌC, trong khi thứ cần chặn là số
XOÁ. Hai đại lượng ấy chỉ bằng nhau khi mọi bản ghi đọc lên đều là rác — đúng cái điều kiện thôi
đúng kể từ lúc kênh mới bắt đầu sinh bản ghi.

**Luật.** Mỗi khi viết `limit` / `slice` / `[:n]`, hỏi: *cái mình muốn giữ có chắc nằm trong n
phần tử đầu không?* Không chắc thì **lọc trước, cắt sau**. Và trần phải đặt trên **đại lượng
mình muốn chặn**, không phải đại lượng dễ đếm.

### 15.2 Bằng chứng luôn tồn tại — ta ném nó đi trước khi ai kịp đọc

Bốn chỗ trong ngày, cùng một hành vi:

| chỗ | cách ném bằng chứng đi | hậu quả đo được |
|---|---|---|
| `kiem_kho.py` | chết `ModuleNotFoundError` sau `\|\| true` | bước DUY NHẤT đếm tệp thật trên Drive chưa từng chạy, nhiều ngày |
| `day_kho.day_mot` | `capture_output=True` rồi vứt `stdout` | 18/18 luồng báo ✅ mà không kho nào có bản ghi |
| `_kho_tu_kv` | `except: pass` nuốt `NameError` | đường cứu hồ kho chết câm từ 31/8, mà vẫn in ra dòng "đã lấy 100 tài khoản" |
| `don_drive_kenh` (của chính tôi) | in `0 file` không kèm mẫu số | "kho sạch" và "chưa soi được gì" ra cùng một dòng chữ |

Cái cuối đắt nhất về mặt bài học: tôi vừa sửa ba cái trên xong thì viết lại đúng nó vào script
mới của mình, trong cùng một buổi.

**Luật.** Mọi con số 0 phải đi kèm **mẫu số**. `0` một mình luôn có hai nghĩa ngược nhau —
"đã tìm, không có" và "chưa tìm được" — và hai nghĩa ấy dẫn tới hai hành động khác hẳn nhau.
`soi 12.480 file trong 100/100 kho · xoá 0` là một câu; `soi 0 file trong 0/100 kho · xoá 0`
là một câu hoàn toàn khác.

### 15.3 Mã thoát trả lời "có nổ không", không trả lời "có làm được việc không"

`day_kho` tính `ok = (returncode == 0)`. Một lượt đẩy **không sinh ra tệp nào trên Drive** vẫn
thoát 0, và cả 18 luồng in `✅ 2/2 video vào hàng đợi đăng` trong khi D1 có 0 bản ghi.

Ở mắt xích **giao hàng**, câu hỏi đúng không phải "tiến trình có chết không" mà "có tệp nào ra
đời không". Nay: thoát 0 mà không có dòng `Drive file id:` thì tính là HỎNG — lượt đỏ khiến bốn
mốc cron tự thử lại, đó mới là tự động thật.

**Luật.** Bước nào có sản phẩm đầu ra thì cổng của nó phải kiểm **sản phẩm**, không kiểm mã thoát.

### 15.4 Tệp phụ thuộc phải tìm bằng ĐƯỜNG MẶC ĐỊNH, biến môi trường chỉ để ghi đè

`kiem_kho.py` nạp `storage` chỉ qua `AUTOPUBLISHER_SRC`. Không workflow nào đặt biến ấy. Biến
thiếu thì **im**; đường mặc định sai thì **báo**. `day_kho.py` ngay cạnh làm đúng (`../_autopublisher`)
và chạy tốt suốt.

Cùng dạng: `/tmp/sa.json` được ghi bên trong bước "Đẩy video", trong khi hai bước khác trỏ vào
chính tệp ấy — tức phụ thuộc vào tác dụng phụ của một bước không liên quan. **Thứ từ ba bước
trở lên cùng cần thì nó là bước riêng.**

### 15.5 Đọc client cũ trước khi viết client mới — lần thứ ba

`Drive(acc)` trông hoàn toàn hợp lý. `Drive.__init__(self, service=None)` — nó sẽ coi cái dict
hồ sơ kho là `service` và chết ở lệnh gọi ĐẦU TIÊN, tức sau khi đã quét xong cả kho. `wipe_queue.py`
ngay cạnh đã dùng `storage.account_drive(acc)` từ 23/8.

**Luật.** Trước khi viết một lối gọi mới tới hệ đã có lối gọi, `grep` xem lối cũ làm thế nào.
Chú thích trong client cũ là những lần đã trả giá.

### 15.6 Cổng an toàn cho lệnh XOÁ: chỉ xoá khi CHỨNG MINH được

`don_drive_kenh.py` xoá file Drive của kênh đã nghỉ. Bằng chứng duy nhất được chấp nhận là
trường `channel` trong sidecar `.json` của chính video ấy:

```
sidecar đọc được · channel không có trong channels.yaml   -> xoá
sidecar đọc được · channel có trong channels.yaml         -> giữ
không có sidecar / đọc hỏng / thiếu trường                -> GIỮ, và báo ra
```

Dòng thứ ba là dòng quan trọng nhất: **không biết ≠ đã nghỉ**. Đoán theo tiền tố tên tệp
(`v3_`/`v5_`/`v9_`) nghe rất hợp lý và sẽ sai đúng một lần — lần ấy là xoá vĩnh viễn một video
đang chạy. Và như mọi lệnh dọn: **danh sách giữ lại rỗng thì DỪNG**, vì "không kênh nào được
giữ" đọc ra y hệt "xoá sạch".

### 14.13 Cổng đo một giá trị mà chính thứ bị đo đã lặng lẽ sửa xong

`cham()` đo `len(prompt(...)) > KY_TU_MAX`. Nó **không bao giờ nổ** — vì tới lúc nó đo thì
`prompt()` đã tự cắt bớt câu và trả về một chuỗi vừa khít trần. Đo được **3–4 tập mỗi lượt chạy**
in cảnh báo ra `stderr` trong khi thước báo SẠCH.

Cái mất là thật: cắt câu ở khâu ghép nghĩa là **một mệnh đề của kịch bản biến mất khỏi bản giao
đi**, và không ai duyệt việc bỏ mệnh đề nào.

**Họ lỗi:** 12.8 — *hỏng mà vẫn báo xanh*. Nhưng biến thể khó thấy hơn: không phải cổng hỏng, mà
là **cổng đo sau khi thứ cần bắt đã được tự sửa**. Dấu hiệu nhận ra giống hệt 14.8: **hai kênh
thông tin nói ngược nhau** — `stderr` kêu, thước im.

**Chữa:** `prompt()` ghi lại rằng nó đã phải cắt (`_DA_CAT`), `cham()` đọc cờ ấy.

**Luật:** khi một hàm vừa ĐO vừa TỰ SỬA, cổng đặt sau nó luôn xanh. Hoặc tách sửa ra khỏi đo,
hoặc bắt hàm ấy **khai báo** là nó đã sửa gì.

### 14.14 Đo hiệu quả của một bản sửa: chọn đại lượng trước, đừng đọc trung bình

Thêm dòng cấm họ cú lật đã mòn, đo lại đúng 12 tập ấy:

| | trước | sau | kết luận |
|---|---|---|---|
| TB điểm | 94,2 | 96,3 | chênh 2,2 · **KTC95 của chênh ±2,8** → nằm trong nhiễu |
| ≥95 điểm | 7/12 | 10/12 | gợi ý, chưa đủ mẫu |
| **lượt trừ điểm trục cú lật** | **48** | **29** | giảm 19 · sai số Poisson ±7 → **vượt nhiễu** |

Đúng luật 13.26: với n = 12 và sd ≈ 4, trung bình **không** phân biệt được hai lượt. Thứ dùng
được là **đếm sự kiện** — và ở đây đếm được nhiều sự kiện (48) nên nó có sức phân giải, trong khi
đếm tập (12) thì không.

**Luật:** trước khi sửa, chọn sẵn **đại lượng sẽ dùng để phán quyết**, và chọn đại lượng có
NHIỀU sự kiện nhất mà bản sửa nhắm vào. Đọc trung bình của một mẫu nhỏ là cách chắc chắn để kể
một câu chuyện nghe hợp lý về nhiễu.

### 14.15 Lệnh dặn tự mâu thuẫn theo chiều NGƯỢC với 13.2 — cấm một TỪ mà việc hợp lệ cũng dùng

Luật 13.2 dạy: cổng đo một TỪ thì lệnh dặn phải liệt kê chính từ ấy. Em áp nó vào dòng cấm họ cú
lật đã mòn, và liệt kê `lifts · moves aside · reveals`.

Sai ở chữ cuối. `reveals` là chữ của **ba cơ chế hợp lệ** — `thủ-phạm-lộ-diện`,
`vật-hoá-ra-là-khác`, `người-thứ-ba-đã-xong`. Đọc bản thảo thì thấy AI đổi đúng **hình** nhưng
vẫn giữ chữ ấy, nên nó vừa làm đúng vừa "vi phạm" một điều em vừa cấm.

**Luật:** 13.2 chỉ đúng khi cái bị cấm là một **từ**. Khi cái bị cấm là một **hình**, hãy tả cái
hình ấy và **đừng liệt kê từ nào** — vì bất kỳ từ nào đủ phổ biến để nhận diện cái hình cũng đủ
phổ biến để xuất hiện trong việc hợp lệ. Cùng họ với 13.22 (*một chữ có hai nghĩa vật lý là chữ
không dùng làm cổng được*), chỉ khác là ở lệnh dặn thay vì ở cổng.

### 14.16 Một luật đúng bị thực thi bằng cách rẻ nhất

Luật *"phải có ít nhất một lượng chính xác"* (13.3) là luật tốt: con số làm người xem **cảm
được** quy mô. Đọc bản thảo thì thấy nó đang được thoả thế này:

> *"Pickle's **nine** chewed rubber paw prints stain the grass"*
> *"Mercy's smudged boot prints, **three** dark spots, on the margins"*

Con số gắn vào **vết**, **đốm**, **dấu** — những thứ không đếm được bằng mắt trong một khung
hình. Luật được thoả về mặt chữ và **mất hoàn toàn tác dụng** về mặt người xem, lại còn làm câu
văn kỳ quặc.

**Luật:** khi viết một ràng buộc, đừng chỉ nói *phải có gì* — nói luôn **nó được phép đếm cái
gì**. Mọi ràng buộc đều sẽ được thoả bằng cách rẻ nhất mà câu chữ cho phép; chỗ hở nằm ở phần
mình không viết ra, không ở phần mình viết.

### 14.17 Từng bước nằm trong nhiễu, cộng dồn thì vượt — và đó không phải mâu thuẫn

Bốn lượt đo, mỗi lượt 12 tập, cùng bộ việc:

| | TB | sd | ≥95 | nhận sạch | vòng/tập |
|---|---|---|---|---|---|
| A · vòng lặp sống | 94,2 | 4,3 | 7/12 | 3/12 | 10,4 |
| B · + cấm họ mòn | 96,3 | 2,3 | 10/12 | 4/12 | 9,0 |
| C · + cổng cắt câu | 96,8 | 2,2 | 11/12 | 5/12 | 8,3 |
| D · + vá 2 chỗ hở lệnh dặn | **97,5** | **1,2** | **12/12** | **7/12** | **7,4** |

A→B chênh 2,2 (KTC95 ±2,8) và A→C chênh 2,6 (±2,7) — **cả hai nằm trong nhiễu**. Dừng ở đó mà
tuyên bố "đã cải thiện" là kể chuyện về nhiễu, đúng lỗi 13.26.

A→D chênh 3,3 (±2,5) — **vượt**. Và biến đếm rõ hơn nhiều: **≥95 điểm 7/12 → 12/12, Fisher hai
phía p = 0,037**.

Không mâu thuẫn: mỗi bản sửa nhỏ hơn ngưỡng phân giải của một mẫu 12, nhưng chúng cộng lại. Điều
kiện để câu này hợp lệ: **phép so đầu–cuối phải được định trước**, không phải chọn ra cặp đẹp
nhất trong sáu cặp — chọn hậu nghiệm thì `p` mất nghĩa.

Và hai con số đáng giá hơn cả trung bình:

- **sd 4,3 → 1,2** — đầu ra ổn định. Ở dây chuyền chạy hàng nghìn tập, phương sai mới là thứ
  quyết định, không phải trung bình.
- **vòng/tập 10,4 → 7,4** — giảm 29% lượt gọi AI cho mỗi tập. Bản sửa vừa làm chất lượng lên vừa
  làm chi phí xuống, và đó là dấu hiệu đáng tin nhất rằng ta sửa đúng gốc chứ không siết thêm
  cổng: siết cổng luôn làm số vòng TĂNG.

---

## 15. BỘ THỨ NĂM — MƯỜI KÊNH THIÊN NHIÊN (2/9/2026)

Short 8–10 giây, **một cú máy**, **không lời đọc**. Một lượt Kling mỗi video — cùng kinh tế với
bộ hài, và anh chốt như vậy sau khi em nêu ba mức chi phí (1 lượt · 7 lượt · 60–120 lượt).

### 15.1 Vì sao thiên nhiên là thứ HỢP KLING NHẤT trong cả năm bộ

`kling_studio.py` đã ghi ra từ lần thử thật 09/08, và nó là lý do kỹ thuật để làm bộ này:

```
mạnh : một chủ thể rõ · một hành động rõ · khí quyển, ánh sáng, chuyển động chậm · ĐỘNG VẬT
yếu  : chữ đọc được · mặt người cận cảnh · bàn tay · thoại/khớp miệng · đám đông nhanh
```

Bộ thiên nhiên **không chạm vào một chỗ yếu nào**. Bộ hài thì phải sống chung với "thoại" và
"mặt người" suốt. Đây là lập luận từ số đo đã có, không phải từ đề tài đang hot.

Và vì cùng lý do ấy, ý tưởng **THE MURMUR** (đàn sáo đá cuộn xoáy) bị **cắt** dù nó mạnh nhất về
hình: một đàn chim cuộn xoáy CHÍNH LÀ "đám đông chuyển động nhanh". Ghi lại để nếu clip đầu tiên
cho thấy Kling dựng nổi khối đông thì mở lại — lúc ấy đã có bằng chứng thay vì đoán.

### 15.2 Trong prompt text-to-video, một PHÉP SO SÁNH là một yêu cầu vẽ

Cổng "không có người trong khung" bắt bốn chỗ, và cả bốn là văn của chính em:

| câu | chữ vướng |
|---|---|
| *"Weather that would knock **a person** down"* | person |
| *"upright stance as tall as **a child**"* | child |
| *"riding the **face of a** green wave"* | face of a |
| *"drinking … and **pulling back** at the cold"* | pull back (cú máy) |

Phản xạ đầu tiên là nới cổng. Sai. **Mô hình đọc theo nghĩa đen**: "cao bằng một đứa trẻ" là một
cơ hội thật để nó vẽ ra một đứa trẻ đứng cạnh con chim cánh cụt. Cổng đúng, văn em sai.

**Luật:** trong prompt gửi mô hình sinh ảnh/video, **đừng ví von**. Mọi danh từ viết ra đều có
thể xuất hiện trong khung. Tả kích thước bằng số đo, đừng bằng vật so sánh.

### 15.3 Gốc từ ngắn cộng `\w*` là một cái bẫy — ba lần trong một buổi

| biểu thức | nuốt nhầm |
|---|---|
| `rip\w* (apart\|open)` | *"not one **ripple**. **Open** the mouth…"* |
| `grin\w*` | *"brash ice **grinding** together"* |
| `hand\w*` | *"a **hand's** width above the water"* |

Với gốc dưới năm ký tự phải **liệt kê các dạng thật** (`grins/grinned/grinning`) thay vì `\w*`.
Cùng họ 13.22, chỉ khác: ở đó là một chữ hai nghĩa, ở đây là hai chữ khác nhau tình cờ chung
phần đầu.

Và cái đầu tiên còn dạy thêm một điều riêng: nó khớp **qua chỗ nối giữa hai trường**. Em nối các
trường bằng dấu cách để quét, nên đuôi trường này dính đầu trường kia sinh ra một cụm **không
tồn tại ở trường nào cả**. **Đo một phép nối là đo một văn bản không ai viết ra** — nối bằng dấu
xuống dòng, đừng bằng dấu cách.

### 15.4 Áp `mo_cam` cho một trục rồi quên hai trục song song

Em áp cơ chế "thế giới này diễn được gì" (14.2) cho trục **khuôn hình** ngay từ đầu, rồi để
nguyên trục **ánh sáng** và **thời tiết**. Kết quả, prompt của TUSK (dưới trần băng) ra:

> *"The light is storm light: dark sky, one bright band on **the horizon**. The conditions are
> heavy slow **swell**."*

Dưới băng không có bầu trời, không có chân trời, không có sóng lừng. Đúng họ lỗi số 6: **vá một
nhánh, để nguyên nhánh song song**.

Và một chỗ thứ ba cùng dạng: câu ống kính là một **hằng số** tele, nên nó đứng ngay cạnh
*"camera locked underwater at depth"* — hai lệnh trái nhau trong cùng một prompt. Ống kính phải
**theo khuôn hình**, không phải một hằng số.

**Luật:** khi thêm cơ chế "ngữ cảnh này cho phép gì", đi soát **mọi trục** cùng lúc. Sửa một
trục rồi dừng là cách chắc chắn để cùng một lỗi quay lại ở trục bên cạnh, và lần sau nó khó thấy
hơn vì "chỗ đó đã sửa rồi".

### 15.5 Cổng bóng ngoài chứng minh mười cái KHÁC NHAU, không chứng minh cái nào ĐỌC ĐƯỢC

`kiem_bong` xanh cả mười. Nhìn ở 48px thì **năm cái hỏng**: vây cá voi sát thủ thành ngọn núi,
đuôi cá voi thành chữ Y rồi thành con bướm, chim cánh cụt thành ổ khoá, sóng thành mặt trời mọc,
dấu móng thành hai chiếc lá.

Cổng đo **khoảng cách giữa các bóng**, và mười hình vô nghĩa khác nhau vẫn cách xa nhau. Không
có thước nào đo được "hình này gợi ra đúng con vật ấy" — chỗ đó vẫn phải nhìn.

Ba lần vẽ lại mới xong, và mỗi lần đều học một điều cụ thể: vây nhận ra nhờ **mép sau cong**,
không nhờ nó nhọn · đuôi cá voi nhận ra nhờ **bề ngang**, thêm cuống là thành con bướm · dấu móng
nhận ra nhờ **mép trong thẳng, mép ngoài cong**, hai mép cùng cong thì thành lá.

### 15.6 Ba ràng buộc cứng của ngách này, và cả ba đều có cổng

1. **Không bao giờ trình bày như tư liệu thật.** Đây là cảnh dựng bằng AI, và kênh nói rõ ở mô
   tả. Trình bày cảnh AI như tư liệu động vật thật là khai man, và cũng là dạng bị gỡ nhanh nhất
   trong ngách này.
2. **Săn mồi được, máu me thì không.** Cho xem khoảnh khắc lao tới, không cho xem hậu quả —
   `CAM_MAU` chặn ở khâu viết, và mọi `luat` của mười kênh đều nói lại điều đó.
3. **Một chủ thể, một hành động, máy ghim cứng.** `CAM_TROI` chặn mọi từ chỉ chuyển động máy,
   `CAM_NHANH` chặn động tác nhanh–hỗn loạn (chỗ Kling vẽ sai giải phẫu).

### 15.7 SÁU LẦN cùng một họ lỗi trong một tệp — và lần thứ sáu mới nhận ra quy luật

Chạy thật rồi **đọc tay** 30 tập, phát hiện bộ lịch ghép sai ở **sáu chỗ khác nhau**, tất cả là
một câu hỏi duy nhất chưa hỏi: *"trục A có được phép ghép với trục B không?"*

| # | ghép sai | ví dụ đọc ra |
|---|---|---|
| 1 | khuôn hình × thế giới | biển sâu nhận "mép vách nhìn xuống" |
| 2 | ánh sáng × thế giới | dưới trần băng nhận "bầu trời bão, một dải sáng ở **chân trời**" |
| 3 | thời tiết × thế giới | đàn cánh cụt trên băng liền bờ nhận "**sóng lừng**" |
| 4 | **loài × hành vi** | chim hải âu *"cho con nằm trên lưng"* · cá tuyết *"giao ngà với con đực khác"* · chuột đồng *"bay tới bằng đôi cánh không tiếng"* |
| 5 | khuôn hình × hành vi | "dưới nước nhìn lên" + "trượt xuống sống băng"; "cận cực đại" + "lao lên khỏi mặt nước" |
| 6 | khuôn hình × ánh sáng | "ngược sáng vào mặt trời thấp" + "nắng gắt trên đỉnh" |

Cái thứ **4** là nặng nhất: đo tay khoảng **một phần ba** số tập vô nghĩa về mặt sinh học. Và
không cổng nào bắt được — `cham()` đo chữ, không đo sinh học.

**Ba cách chữa, và chọn đúng cách mới quan trọng:**

- 1·2·3 chữa bằng **danh sách loại trừ** (`khuon_cam`, `anh_sang_cam`, `thoi_tiet_cam`) — đúng,
  vì cái bị cấm là một tập con của MỘT trục.
- 4 thì danh sách loại trừ là **sai công cụ**: cái hợp lệ ở đây là một **quan hệ** giữa hai
  trục, không phải bộ lọc trên một trục. Nên hành vi gắn thẳng vào loài và hai trục nhập làm
  một — cặp sai **không còn tồn tại để mà lọc**.
- 6 chữa bằng cách **để khuôn hình GIỮ ánh sáng của nó** và bỏ hẳn câu ánh sáng, thay vì thêm
  bảng loại trừ thứ tư.

**Luật:** khi bộ lịch có N trục, số cặp cần hỏi là N(N−1)/2 — với 5 trục là 10 câu hỏi. Hỏi hết
MỘT LẦN lúc thiết kế rẻ hơn nhiều so với sáu lần vá. Và khi phát hiện cặp sai, hỏi tiếp: *cái
hợp lệ ở đây là một TẬP CON hay một QUAN HỆ?* Tập con thì lọc; quan hệ thì **hợp nhất hai trục**.

### 15.8 Hai công thức bước đi đều hỏng — thôi tìm công thức, đi đo

Bộ lịch cần hai thứ cùng lúc: **chu kỳ dài** (bộ trục không lặp lại sớm) và **không lặp liền
kề** (hai tập cạnh nhau trông khác nhau). Ba lần thử:

| cách | chu kỳ | lặp liền kề |
|---|---|---|
| bước lớn cố định (1.000.003) | dài ✅ | khuôn hình lặp **21/199** ❌ |
| mỗi trục một vòng quay riêng | **84/200 bộ** ❌ (bẫy `lcm`, luật 13.13) | 0 ✅ |
| bước ≈ P/φ (tỉ lệ vàng) | dài ✅ | ánh sáng lặp **107/199** ❌ |
| **duyệt vài chục bước, ĐẾM, lấy ít nhất** | dài ✅ | **0 trên mọi trục** ✅ |

Không có công thức nào đúng cho mọi hình dạng `truc`, vì "đổi đều" là tính chất của **từng chữ
số**, không phải của dãy. P ở đây chỉ vài nghìn nên duyệt 60 ứng viên tốn vài mili giây.

**Luật:** khi một tham số có thể **đo trực tiếp thứ mình cần**, đừng đi tìm công thức cho nó.
Bảy vòng đoán công thức đắt hơn nhiều so với một vòng lặp `for` chấm điểm.

### 15.9 Bài kiểm ngược hỏng vì con trỏ, và nó báo "cổng chết"

Bộ thử ngược bảy cổng báo **7/7 KHÔNG BẮT** sau khi em đổi cấu trúc dữ liệu. Suýt đi sửa bảy
cổng đang lành. Thật ra bài kiểm hỏng hai chỗ:

- `K = T.KENH["ICE BEAR"]` lấy trước vòng lặp, còn hàm khôi phục `clear()/update()` thay **object
  mới** vào — từ lượt thứ hai, mọi phép phá đi vào một object đã rời khỏi bảng.
- Chỉ soi tập 0. Sau khi đổi cấu trúc, tập 0 có thể chọn một loài khác, nên hành vi bị phá không
  được chọn.

Đúng luật 13.15: **trước khi kết luận hạ tầng hỏng, kiểm lại bài kiểm của mình** — và ở đây "hạ
tầng" là chính bảy cổng vừa viết xong.

### 15.10 Một dây chuyền kết thúc ở nửa đường trông y hệt một dây chuyền hoàn chỉnh

Bộ thiên nhiên dừng ở **prompt**. Sau khi anh dán vào Kling và tải clip về thì **không có gì đưa
nó đi tiếp** — `kling_dong_bo.py` import cứng `kling_kenh` nên nổ ngay ở dòng đầu:

```
KK.ho_so("ICE BEAR")  ->  RuntimeError: chưa có kênh 'ICE BEAR'
```

Em đã nói "cắm vào `kling_lo`" trong bản giao đầu — và nó **không hề cắm**. Câu ấy đúng về ý
định, sai về sự thật, và loại sai ấy chỉ lộ ra khi có clip thật trong tay.

**Luật:** khi giao một dây chuyền, chạy **đầu tới cuối bằng dữ liệu giả** trước khi nói nó xong.
Ở đây chỉ cần một clip màu 8 giây dựng bằng `ffmpeg lavfi` — mất một phút, và nó là khác biệt
giữa "đã cắm" và "tưởng là đã cắm".

`tn_dong_bo.py` khác `kling_dong_bo.py` ở đúng ba chỗ, và cả ba là lý do không dùng chung tệp:

| | bộ hài | bộ thiên nhiên |
|---|---|---|
| ảnh bìa | giữa nhịp **hook** (62% rơi trúng cú lật, lộ kết) | **66%** — prompt đặt hàng *"resolves about two thirds through"*, nên đó là ĐỈNH, không phải thứ phải giấu |
| bài đăng | gọi AI (tiêu đề phải bắt cú đùa) | **viết bằng code** — loài + hành vi + nơi chốn đã nằm sẵn trong `tap.json`, gọi AI là tiêu một lượt để lấy về thứ đang cầm |
| khai báo | không cần | **bắt buộc ở cả ba nền tảng**, có cổng, đã thử ngược |

### 15.11 Tất định + tham số tay = sinh trùng mà không có gì báo

`--so` là tham số tay và bộ lịch tất định, nên chạy lại cùng một `--so` cho ra **đúng cùng một
prompt**, ghi đè lặng lẽ. Anh dán nó vào Kling và **trả tiền cho một lượt sinh ra cái đã có**.

Không cổng nào kêu, vì về mặt kỹ thuật không có gì hỏng. Cùng họ 12.8: hỏng mà vẫn báo xanh —
chỉ khác là ở đây cái mất là **tiền thật**, không phải một tệp.

**Chữa:** `tap_ke()` để MÁY đếm tập kế tiếp, `--so` thành tuỳ chọn, và ép `--so` vào một thư mục
đã có thì in cảnh báo. **Luật:** hễ một hệ vừa tất định vừa nhận số thứ tự bằng tay thì nó sẽ
sinh trùng — hãy để máy đếm.

### 15.12 Viết ra một trường rồi không bao giờ đọc nó — im lặng cả hai phía

Trường `luat` (luật vật lý của thế giới) được soạn cho **cả mười hai kênh** và **đọc 0 lần**:
`grep 'hs\["luat"\]'` không ra dòng nào. Bộ hài đưa luật thế giới vào lệnh hệ thống cho AI
(14.11); bộ này **không có AI**, nên chỗ duy nhất nó tồn tại được là chính prompt — và em quên
nối.

Bỏ quên một trường dữ liệu trông **y hệt** như chưa từng viết nó. Không có lỗi, không có cảnh
báo, và bản thân dữ liệu đọc lên vẫn rất thuyết phục.

**Cách nhận ra rẻ nhất:** với mỗi trường trong hồ sơ, `grep` xem có chỗ nào ĐỌC nó không. Trường
chỉ được ghi mà không được đọc là trường chưa tồn tại.

Và khi nối vào thì lộ tiếp một điều: `luat` của hai kênh tiền sử **nói lại** thứ hàng rào DO NOT
đã cấm ("no people", "no blood"). Nói hai lần tốn ngân sách và không thêm gì. **Mỗi ràng buộc
chỉ được sống ở đúng một chỗ.**

### 15.13 Ước lượng ca xấu nhất bằng công thức — lệch 140 ký tự, cắt mò ba lượt

Sau khi thêm khối `RULES OF THIS WORLD`, prompt tràn trần. Em ước lượng ca xấu nhất bằng "dài
nhất của từng trục cộng lại + một hằng số dự phòng", ra 2.385 với 115 dư — trong khi bản dựng
thật báo **2.527**. Lệch 140, và em đi cắt mò ba lượt liền, lượt nào cũng thấy con số mới vì
mỗi lần một tổ hợp KHÁC trở thành xấu nhất.

Đúng lỗi 13.7 lần nữa: **đo mô hình thay vì đo vật thật**.

Chữa bằng `ca_xau_nhat(kenh)` — **duyệt hết** mọi tổ hợp (loài × hành vi × khuôn × sáng × tiết ×
độ dài) và trả về số dài nhất cùng tổ hợp gây ra nó. Không gian một kênh chỉ vài nghìn nên duyệt
hết mất mili giây.

Và nó thành **cổng design-time** trong selftest: thêm một kênh viết quá dài thì hỏng NGAY LÚC
THÊM, không phải ở tập số 47 sáu tháng sau.

Một chi tiết đắt: tổ hợp xấu nhất hoá ra là hành vi *"shaking the filaments along its neck **the
way a bird shakes its feathers**"* — vừa dài nhất vừa chứa một **phép ví von**, thứ luật 15.2 đã
cấm. Cắt nó sửa cả hai lỗi bằng một nhát. Chỗ dài nhất thường cũng là chỗ viết lỏng nhất.

### 15.14 Hai kênh tiền sử — vì sao là KÊNH RIÊNG, không phải loài thêm vào

Anh nêu ý voi ma mút và khủng long. Nhét chúng vào ICE BEAR hay BLUE GIANT là hỏng: khác thế
giới, khác ánh sáng, khác cả lời hứa với người xem. Nên **41 · ICE AGE** và **42 · DEEP TIME**.

Ba điều làm ngách này khác hẳn mười kênh kia:

1. **Căng thẳng "khai báo cảnh AI" biến mất, và thành điểm cộng.** Với gấu Bắc Cực, cảnh AI phải
   nói rõ là AI để khỏi khai man. Với voi ma mút thì AI là cách **duy nhất** có hình — không ai
   hiểu nhầm, và người xem tới vì đúng điều đó.
2. **Không có "giải phẫu đúng loài" để mà neo vào.** Câu `SAN_THAT` chung nói *"anatomy exactly
   right for the species"* — với con vật tuyệt chủng thì câu ấy rỗng, và chỗ rỗng ấy mô hình lấp
   bằng thứ nó thuộc nhất: **thiết kế phim**. Nên hai kênh này khai `treatment` riêng, neo vào
   **phục dựng cổ sinh học**.
3. **Cổng mới `CAM_PHIM`.** Mô hình đã học hàng triệu khung phim khủng long, nên không ghim thì
   nó vẽ một con quái vật gầm vào ống kính. Ngoài chuyện xấu, tạo hình của một hãng phim là tài
   sản của hãng ấy. Cổng chặn `jurassic · cinematic · roar · rearing · menacing · lit from below`
   — đã thử ngược cả bốn.

Và `style` của DEEP TIME cố ý đi ngược mọi phim khủng long: **ướt, xanh, yên tĩnh**, ánh sáng
sương buổi sáng từ trên xuống. Đó chính là hook — người xem dừng lại vì nó được quay **bình
tĩnh**, thứ cuối cùng họ chờ đợi ở một con khủng long.

### 15.15 Tra CỨU thật thay vì suy đoán — bốn thứ tầng tay nghề đang thiếu

Anh nhắc là em mở browser tra được, và đúng. Ba nguồn đọc được (CineD về Planet Earth II · BBC
Earth về quay tốc độ cao · các bài về bố cục ảnh động vật), rút ra bốn thứ **không có** trong hệ:

| thiếu | vì sao nó quan trọng | đã thêm vào đâu |
|---|---|---|
| **catchlight trong mắt** | mắt không có chấm sáng đọc ra là mắt CHẾT — và đó đúng là chỗ ảnh AI lộ ra ngay | `SAN_THAT` |
| **độ phân giải CẢM ĐƯỢC** | thứ người ta thấy khi nói "4K" không phải số pixel mà là *sợi lông tách khỏi sợi lông* | `SAN_THAT` |
| **lead room** — chừa chỗ TRƯỚC mặt con vật | nguyên tắc "frame for where the story is going"; đây là thứ tách khung ĐƯỢC BỐ CỤC khỏi khung có con vật ở giữa | khuôn `long lens tight` |
| **khuôn CHÂN DUNG** | nghề tách "character shot" (con vật LÀ AI) khỏi "action shot" (nó ĐANG LÀM GÌ). Mười khuôn cũ đều là action | khuôn mới `eye-level portrait` |

Và một con số được **sửa cho có nguồn**: slow motion em viết "khoảng một nghìn hình/giây" —
tự đoán. BBC Earth công bố **500 hình/giây** là *"the perfect speed"*. Đúng luật 13.1: giới hạn
phải có đơn vị và nguồn, không phải một con số nghe hợp lý.

Cũng nhờ tra mà biết luật của NIGHT EYES đang **đúng**: BBC dùng ba cách quay đêm (hồng ngoại ·
nhiệt · cảm biến siêu nhạy), và cách thứ ba cho hình màu tự nhiên — đúng thứ kênh này đang khoá.
Nay viết thành câu KHẲNG ĐỊNH thay vì câu cấm.

**Luật:** khi có thể tra, đừng suy. Bốn thứ trên đều là quy ước nghề công khai, và không cái nào
em nghĩ ra được bằng cách ngồi suy từ nguyên tắc chung.

### 15.16 "4K" trong prompt không làm ra 4K — đòn bẩy thật nằm ở khâu upload

Anh dặn chất lượng 4K. Viết chữ "4K" vào prompt **không làm gì cả**: độ phân giải là thiết lập
sinh của Kling, không phải một từ trong câu. Nói với mô hình một con số nó không điều khiển được
là tốn ký tự để lấy về không gì.

Hai đòn bẩy THẬT, và đã làm cả hai:

1. **Tả cái mà 4K TRÔNG NHƯ THẾ** — sợi lông tách rời, giọt nước tách rời, dải tương phản không
   cháy. Mô hình vẽ được những thứ ấy; nó không vẽ được "2160 pixel".
2. **Nâng cỡ lên 2160×3840 TRƯỚC KHI UPLOAD.** YouTube cấp codec và bitrate cao hơn hẳn cho tệp
   ≥1440p, nên cùng một khung hình, bản nâng cỡ giữ được nhiều chi tiết hơn **sau khi YouTube
   nén lại** — mà chi tiết chính là thứ ngách này bán. Dùng `lanczos` chứ không phải bicubic
   mặc định: ở tỉ lệ 2× nó giữ nét lông và bọt nước.

Và gọi đúng tên trong mã: đây là **nâng cỡ**, không phải 4K gốc. Ghi sai tên một thứ trong mã là
cách chắc chắn để phiên sau tin nhầm.

### 15.17 Khoá dict trùng — Python nuốt im lặng, và thước vẫn xanh

Chèn thêm hành vi cho hai loài, bộ chèn tạo khoá `"mep"` THỨ HAI trong khi loài ấy đã có `"mep"`
ở dưới. **Python lấy khoá sau, vứt khoá trước, không báo một chữ nào.** Hai hành vi mới biến mất
trong khi tệp nguồn đọc lên vẫn thấy chúng nằm nguyên đó.

Dạng tệ nhất: mã đúng cú pháp · tệp trông đúng · mọi cổng xanh · dữ liệu thì mất. Em chỉ phát
hiện vì **đếm số hành vi trước và sau** rồi thấy con số KHÔNG TĂNG.

Cổng mới quét bằng `ast`, không bằng cách nạp module — nạp module thì khoá trùng đã bị nuốt mất,
tức **đúng thứ cần bắt không còn ở đó để mà bắt**. Quét cả bốn tệp hồ sơ: sạch.

### 15.18 `git add -A` trên thư mục dùng chung — em commit bản đang sửa dở của cửa sổ kia

Anh dặn từ đầu: *"nhớ ko xung đột với phần khác e nha, a cũng đang làm việc dự án trên cửa sổ
khác"*. Em vẫn dùng `git add -A render-pipeline` và **quét luôn `nen_gt.py` đang sửa dở của cửa
sổ kia** vào commit của mình. Đây là lỗi của em, không phải của cửa sổ kia.

Hậu quả cụ thể: `selftest` báo đỏ ở `nen_gt.py:563` giữa lúc em đang giao việc, và nhìn từ ngoài
thì nó **trông như em vừa làm hỏng cái gì đó**.

**Luật:** ở repo có nhiều cửa sổ cùng làm, **`git add` phải nêu ĐÍCH DANH tệp**, không bao giờ
`-A` trên cả thư mục. Trước khi commit, `git status --short` và đọc từng dòng: dòng nào không
phải việc mình vừa làm thì để nguyên đó.

### 15.19 Và dòng đỏ ấy là một cổng BẮT OAN — đúng họ lỗi mình vừa viết ba lần

Dòng bị chặn:

```python
_tran = int(os.environ.get("TRAN_ANH_LUONG", "120") or 120)
```

Cổng quét AST tìm `environ.get(K, "mđ")` hai tham số — và dạng trên **đã an toàn**: biến rỗng làm
`.get` trả `""` (falsy), `or 120` đỡ lấy. Cổng chỉ nhìn lời gọi mà **không nhìn ra ngoài nó**.

Chữa bằng cách thu thập trước mọi nhánh không-phải-cuối của một `BoolOp Or` rồi bỏ qua chúng.
Thử ngược đủ hai chiều: dạng có `or` → tha; dạng trần → vẫn bắt.

**Vì sao phải chữa chứ không bỏ qua:** luật 13.2 đã trả giá cho đúng chuyện này — ba dòng đỏ giả
khiến một lỗi THẬT nằm cạnh chúng bị chìm. Một cổng đỏ vĩnh viễn không phiền, nó **che**.

### 15.20 Cổng kiểm hằng số bằng CHÍNH hằng số ấy — luôn xanh

`kiem_bai` so bài đăng với `_KHAI_BAO` (câu khai báo cảnh AI). Thử ngược: đổi `_KHAI_BAO` thành
`"x"` thì `viet_bai` ghi `"x"` và `kiem_bai` tìm `"x"` — **xanh**. Cổng bắt được việc BỎ câu ở
một nền tảng, nhưng không bắt được việc **làm rỗng chính câu ấy**.

Đây là ràng buộc cứng số một của ngách (§15.6), nên phải canh ở **cả hai tầng**: bài đăng có
mang câu không, VÀ câu ấy có còn nói đúng điều nó sinh ra để nói không.

**Luật:** khi một cổng so A với B mà A và B cùng đọc **một nguồn**, cổng ấy chỉ chứng minh A và
B nhất quán — không chứng minh gì về nội dung. Cùng họ với 12.4 (*cổng tự chuẩn hoá theo mẫu đầu
tiên: nhất quán quanh một mốc SAI vẫn sai*).

Và cổng vừa viết **bắt oan ngay lần chạy đầu**: `_t.split()` cho ra `"ai."` **kèm dấu chấm**, nên
`"ai" in split()` trượt chính câu thật. Dấu câu dính vào từ là chỗ mọi phép so theo `split()`
gãy — dùng ranh giới từ `\bai\b`, đừng dùng phép tách theo dấu cách.

### 15.21 Tám phép kiểm chạy tay một lần không phải tám cổng

Quét lỗi tiềm ẩn xong, tám phép đều sạch. Nhưng phép kiểm chạy một lần chỉ chứng minh **hiện tại
lành**, không ngăn được lần sửa sau — và **hai trong tám cái ấy đã từng bắt lỗi thật trong lúc
dựng** (`seabird` không có trong mô tả *"A shearwater"*; `blue sheep` không có trong *"A
bharal"*), mà cả hai lần em đều sửa tay rồi đi tiếp, tức để nguyên cái bẫy cho lần thêm loài sau.

Nay là một chốt `selftest`, và thử ngược đủ tám. Một phép trong đó lộ ra hệ có **bảo vệ hai
tầng**: `khuon_kenh` ném `RuntimeError` khi lọc còn dưới bốn khuôn, trước cả khi chốt kịp so.
Bài kiểm của em ban đầu chỉ bắt `AssertionError` nên báo "cổng chết" — lần thứ hai trong phiên
bài kiểm sai chứ không phải cổng sai (13.15).

---

## 16. LUẬT RÚT TỪ NGÀY 3/9 — BỘ GIẢI THÍCH, VÒNG NÂNG CHẤT LƯỢNG

Ngày này anh chê "vẫn xấu" bốn lần liên tiếp trong khi cổng chấm cho **100/100**. Cả bốn lần anh
đều đúng. Đó là bài học lớn nhất của ngày.

### 16.1 Điểm cổng và "đẹp" là hai đại lượng khác nhau

`kiem_hinh` in ra đúng câu này ở mỗi lượt: *"Điểm này chỉ nói 'không dính tám lỗi đã biết', KHÔNG
nói 'đẹp'."* Tôi đọc câu ấy hàng chục lần rồi vẫn báo cáo "100/100" như thể nó là chất lượng.

Khi anh nói xấu mà cổng nói đẹp, **cổng đang đo thiếu**, không phải anh khó tính. Việc cần làm là
**trích khung ra nhìn** rồi thêm thứ chưa đo, không phải giải thích rằng điểm đã cao.

### 16.2 Prompt cấm đúng thứ mình muốn

Ảnh ra tối và phẳng. Đọc lại prompt thì thấy hai câu **chống lại** chính ảnh tham chiếu anh gửi:

- `"no gradients, no texture"` — trong khi ảnh mẫu **có** đổ bóng mềm, trời chuyển màu, lông thú
  có nét. Cấm gradient là ép mô hình vẽ clipart phẳng.
- `"bright saturated palette"` — nói về **độ rực của màu**, không nói **nền phải sáng**. Mô hình
  vì thế tự do chọn nền tối, và nó chọn tối.

Và prompt **không có câu nào về bối cảnh** nên ra khung rỗng. Chữa bằng cách **liệt kê tên đồ
vật** (*cửa sổ có trời, đồng hồ tường, chậu cây, sạp chợ*) — "chi tiết" là chữ trừu tượng, tên đồ
vật thì mô hình vẽ được.

**Luật.** Khi ảnh ra không giống thứ mình muốn, **đọc lại prompt như thể mình là mô hình**: nó
đang được BẢO làm gì, chứ không phải mình MUỐN gì.

### 16.3 Cổng chặn độ dài phải đo chuỗi SẮP GỬI, không đo bản nháp

Viết prompt mới xong, CF trả `HTTP 400 Length of '/prompt' must be <= 2048`. Chốt chặn cắt ở 2048
— nhưng `_cf_flux_image` còn bọc thêm `"Absolutely no text… A <style> of: … Textless image."` =
**159 ký tự**. Chốt trên bản nháp, gửi bản đã bọc.

Cùng luật 13.7 (`_ngan_sach_khuon` phải nhận chính khuôn sắp giao đi).

### 16.4 Hai hiệu ứng ngược chiều: phần đẹp triệt tiêu, phần thiệt cộng dồn

Thêm lớp chỉnh màu "sáng ấm / tối lạnh": ấm 6% + lạnh 5%. Đo khung thật: **R=130 G=130 B=129** —
không ấm lên chút nào, nhưng vẫn hạ độ sáng và độ trong. Bỏ lớp lạnh, một lớp ấm: **+1,0 → +2,6**.

### 16.5 Cạn tài nguyên: hỏi "nhu cầu tăng mấy lần", không hỏi "sao ít thế"

97 tài khoản CF cạn sạch. Nguồn cung không đổi suốt — **nhu cầu nhân 17 lần**:

```
trước vòng lặp liên tục : 18 luồng × 1 vòng × 46 nhịp =    828 ảnh =  4% sức hồ
sau                     : 18 luồng × 14 vòng × 58 nhịp = 14.900 ảnh = 89%
```

Và tôi **đoán sai một lần ngay giữa việc này**: nói vòng thử lại "tối đa 4 lượt/cảnh" đẩy lên
349%. Đếm log thật: tỉ lệ vẽ lại **2,3%**, hệ số 1,02×. Nếu tin con số 349% thì đã đi sửa thứ
chiếm 2% trong khi thứ chiếm 89% đứng yên.

**Chặn ở chỗ trả giá rẻ nhất**: trần ảnh mỗi luồng, không giảm số video. Tập đầu có ảnh AI đầy
đủ, tập sau dùng lớp vẽ code — **đánh đổi có kiểm soát** thay vì để hồ cạn giữa chừng rồi mọi tập
sau mất ảnh ngẫu nhiên.

### 16.6 Trường tồn tại, kiểu đúng, sai HỆ QUY CHIẾU

Sổ trạng thái khoá ghi theo `k["id"]` — trường CÓ, kiểu chuỗi, nhìn qua thì đúng. Nhưng giá trị
là `local3`: id tự sinh khi đọc tệp khoá, **không phải doc id Firestore**. Nó ghi vào
`gemini_keys/local3` suốt, dashboard đọc doc thật nên không bao giờ thấy — **không một ngoại lệ
nào được ném**.

**Luật.** Khi hai hệ trao đổi định danh, hỏi *"id này do AI cấp, và bên kia có dùng cùng loại id
không?"* Sự tồn tại của trường `id` không chứng minh hai bên nói cùng một thứ.

### 16.7 Mở hết công suất TRƯỚC khi chốt chất lượng

Ngày 2/9 tôi dựng vòng lặp liên tục theo yêu cầu "hàng nghìn video/ngày". Kết quả: hệ tiêu **hết
sạch 97 tài khoản CF** để làm ra **~1.280 video mà anh không dùng được** — vì chúng mang engine
chưa vá.

§4 của chính tệp này đã viết: *pilot một kênh, anh duyệt, rồi mới nhân ra mười.* Tôi làm ngược,
và cái giá là một ngày hạn mức cộng một ngày runner.

**Luật.** Trước khi nhân sản lượng lên, hỏi: *"đã có MỘT sản phẩm được duyệt chưa?"* Nếu chưa thì
nhân lên chỉ là nhân bản thứ chưa ai gật đầu.

### 16.8 Xoá sạch khi dây chuyền đang chạy = giết thứ vừa làm ra

Anh bảo "dọn kho cũ rồi render lại". Nhưng lượt render đang chạy **đã đẩy video mới lên cùng kho**.
Không có cờ nào trong tệp nói nó dựng bằng engine nào — thứ phân biệt được là **giờ tạo**.

`don_video_cu.py --truoc <ISO>` dọn theo mốc, mặc định **bỏ thùng rác** chứ không xoá hẳn: mốc
thời gian là bằng chứng gián tiếp, nên phải để đường lùi.
