# METHOD — KÊNH THẾ HỆ 2 (25/8/2026)

> Đọc file này là làm tiếp được, không cần hỏi lại.
> Thế hệ 1 = 55 kênh footage Pexels. Thế hệ 2 = 50 kênh **dữ liệu thật + đồ hoạ code, 0 footage**.

---

## 1. VÌ SAO ĐỔI

55 kênh cũ dùng đúng công thức của hàng vạn kênh faceless: footage Pexels + chữ động + giọng AI.
Ai cũng lấy được **cùng bộ footage** → không có gì để thuật toán ưu ái, sản lượng lớn chỉ bị chôn nhanh hơn.

Thứ không copy được không phải footage đẹp hơn, mà là **bản ghi gốc hiện trên màn hình**:
tên công ty thật, con số thật đến từng đồng, kèm nguồn khán giả Mỹ tra được.

---

## 2. BA CHẤT LIỆU (trường `chat_lieu` trong `kenh_the_he_2.json`)

| | Chất liệu | Nội dung | Hình | Quota |
|---|---|---|---|---|
| **A** | Dữ liệu thuần | 100% từ API mở, **0 gọi AI** | đồ hoạ Remotion | **0** — chạy được cả khi cạn sạch quota |
| **B** | Ảnh AI style riêng | AI viết lời quanh sự kiện có thật | FLUX/Gemini theo `style_anh` cố định | ảnh + lời |
| **C** | Lai | số liệu làm **xương**, AI viết lời dẫn | ảnh AI làm **da** | ảnh + lời |

Hiện có: **22 kênh A · 5 kênh B · 23 kênh C**.

**RANH GIỚI KHÔNG ĐƯỢC VƯỢT**: AI chỉ viết lời DẪN quanh con số **có sẵn**. Nó không được nghĩ ra số.
Thiếu dữ liệu → `dung_story_*` trả `None` → **bỏ lượt**. Thà mất một video còn hơn mất uy tín cả kênh.

---

## 3. LUỒNG CHẠY MỘT VIDEO

```
kenh_the_he_2.json  →  the_he_2.dung_story_ranked(kenh)
                          ├── BO_CHUYEN[ham](du_lieu_mo, tham_so)   ← gọi API mở
                          └── None nếu thiếu dữ liệu → BỎ LƯỢT
                    →  DS.build_ranked_props()   (TTS + timing + track)
                    →  npx remotion render RankedShort
                    →  DS.qc()  →  đẩy Drive  →  hàng chờ đăng
```

---

## 4. THÊM MỘT KÊNH THẾ HỆ 2 — CHECKLIST

1. Thêm dòng vào `tao_danh_sach_kenh.py` (niche · tên · handle · chất liệu · nguồn · hàm · dạng · góc nhìn · style ảnh)
2. Gắn **tham số riêng** trong `gan_tham_so_kenh.py` — xem mục 5, đây là chỗ dễ sai nhất
3. Nếu nguồn mới: viết hàm trong `du_lieu_mo.py`, **gọi thử thật** trước khi tin
4. Nếu góc mới: viết bộ chuyển đổi `_bd_*` và đăng ký vào `BO_CHUYEN`
5. `python3 selftest.py` — phải xanh
6. `python3 the_he_2.py --kenh "TÊN" --thu` — xem story bằng mắt
7. `--render` một lần, **xem khung hình bằng mắt** trước khi bật hàng loạt
8. Brand-kit: xem `BRAND_KIT.md`
9. Đăng ký kênh + kho Drive: xem `CHANNEL_METHODS.md`

---

## 5. LỖI DỄ MẮC NHẤT: HAI KÊNH RA CÙNG MỘT VIDEO

Đo thật 25/8: **6 cặp kênh ra y hệt nhau** — PILL FACTS (đáng ra là thuốc) ra tin thu hồi thực phẩm;
SALARY TRUTH và DEGREE WORTH cùng ra "Gas price"; STEAM TRUTH và GAME GRAVEYARD cùng một bảng.

Gốc: tham số xoay vòng gắn theo **NGUỒN** thay vì theo **KÊNH**.

**Luật**: mỗi kênh phải có `tham_so` riêng. Hai kênh cùng `ham` thì `tham_so` **bắt buộc khác**.
Chốt `t_kenh_the_he_2_tro_dung_ham_va_dang` chặn ngay từ selftest.

Cùng nguồn mà muốn hai kênh thì phải khác **GÓC**, không chỉ khác tham số:
- `STEAM TRUTH` = game đông nhất · `GAME GRAVEYARD` = `loc=chet_yeu` → bán triệu bản mà không ai chơi
- `SHOW NUMBERS` = phim điểm cao · `GONE TOO SOON` = `loc=da_huy` → phim hay bị cắt
- `AMERICA LOOKED UP` = bảng đọc nhiều · `WHAT THEY SEARCH` = `loc=rieng_tu` → lọc chủ đề thầm kín

Góc ngược (S = tệ nhất) **bắt buộc** trả thêm lời mở nói rõ, nếu không người xem hiểu ngược hẳn.

---

## 6. 25 NGUỒN — TẤT CẢ ĐÃ GỌI THỬ THẬT

**Không cần key**: USASpending · SEC EDGAR (XBRL + full-text) · BLS (13 chuỗi) · openFDA · NHTSA ·
CourtListener · World Bank · USGS · Archive.org · Wikimedia Commons · Wikipedia pageviews ·
MLB StatsAPI · NBA Stats · SteamSpy · TVmaze · MusicBrainz · PubMed · NWS · OpenSky · EPA fueleconomy · Dog CEO

**Key free api.data.gov** (một key dùng chung): NASA · FEC · USDA FoodData

### ĐÃ THOÁT HẲN KHỎI HẠN MỨC — không còn cần key nào

Hạn mức từng chặn 14 kênh. Cách xử lý **không phải xin key, mà đổi đường lấy dữ liệu**:

| Vấn đề | Cũ | Nay |
|---|---|---|
| BLS API 25 lượt/**NGÀY** | `chuoi_bls` | `lay_bls` → **file tĩnh** download.bls.gov, cùng dữ liệu, **0 lượt API** |
| USDA 30 lượt/giờ (DEMO_KEY) | `thanh_phan_mon` | `thanh_phan_off` → **Open Food Facts**, mở hoàn toàn |
| BLS không có số liệu theo BANG | — | **Zillow** giá nhà 51 bang × 319 tháng, file CSV mở |
| 503 ngắt quãng khi 18 lane cùng gọi | rớt kênh ngẫu nhiên | `_goi` **thử lại có giãn** ở tầng chung |

`BLS_KEY` / `DATA_GOV_KEY` vẫn đọc được từ môi trường nếu anh muốn thêm, nhưng **không còn bắt buộc**.
IMF DataMapper đã thử: chặn 403 với mọi User-Agent — đừng dò lại.

**Chưa dùng được**: Socrata (CDC · NYC · Chicago) trả 403, cần app token free — chưa xác minh.

Quy tắc: mọi hàm trong `du_lieu_mo.py` hỏng thì **trả rỗng, không ném**. Dữ liệu là gia vị, không được làm gãy dây chuyền.

---

## 7. ĐANG CÒN THIẾU

- [x] Dạng `ranked` — 17/17 kênh dựng được story thật, đã render end-to-end
- [x] Dạng `race` — 7/7 kênh dựng được, đã render end-to-end (STEAM TRUTH chuyển sang `ranked`: SteamSpy không có chuỗi thời gian, không bịa mốc)
- [x] Dạng `cinematic` — 10/10 kênh dựng được story thật
- [x] Dạng `scaled` — 6/6 kênh (4 chạy ngay, 2 kênh BLS chờ key)
- [x] Dạng `mapped` · `longshot` · `thennow` — **50/50 kênh dựng được kịch bản thật, 0 tiêu đề trùng**
      Kiểm lại bất cứ lúc nào: `python3 kiem_50_kenh.py`
- [ ] Ảnh chất liệu B/C: nối FLUX theo `style_anh` từng kênh
- [x] Brand-kit 50 kênh — sinh 0 quota, 22 motif theo niche, 7 asset/kênh, banner bó đúng vùng an toàn
- [ ] Đăng ký kênh vào Firestore + cấp kho Drive
- [ ] Tắt 55 kênh thế hệ 1 (**chỉ sau khi chúng chạy nốt kho hiện có**)
