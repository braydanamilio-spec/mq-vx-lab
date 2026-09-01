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
| Phân tích video tham chiếu | `render-pipeline/PHAN_TICH_GIAI_THICH.md` |
| Bản hài cũ (giữ để đối chiếu) | `render-pipeline/kich_hai.py` · `src/v4/KichHai.tsx` — vẫn là nơi giữ `KHO` 40 mẩu viết tay, `doc_hai_giong`, `lam_thumb` |
| Luật + buglog | `render-pipeline/PIPELINE_RULES.md` |

## 10. HAI BỘ, HAI XƯỞNG — ĐỪNG TRỘN

| Bộ | Kênh | Pipeline | Workflow | Luồng |
|---|---|---|---|---|
| **Comic (hài)** | 10 | `kich_comic.py` · `kich_comic_long.py` · `sieu_du_lieu.py` | `render_hai.yml` | 10 (mỗi kênh một luồng) |
| **Phân tích** | 56 | `kich_v2.py` · `kich_v2_long.py` | `render_phan_tich_18.yml` | 18 (chia xen kẽ) |
| Thế hệ 1 (cũ) | ~50 | `datastory_ci.py` | `render_cron.yml` | cron TẮT |

Ba hệ này **không dùng chung engine, không dùng chung workflow**. Trộn chúng là cách chắc chắn
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

