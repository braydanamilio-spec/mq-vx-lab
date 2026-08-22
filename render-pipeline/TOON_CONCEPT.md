# TOON — kênh hoạt hình stickman comedy (concept chốt 22/8, chờ build)

## Tham chiếu
Format đang hot (NoLife Animation style, view 98K-20M/short): 1 bối cảnh vẽ cố định + 3-5 khung
cảm xúc của CÙNG cảnh (gồm 1 close-up punch-in) + thoại 2 nhân vật + title card trên đỉnh +
punchline · ~18-30s · watermark góc. Đã mổ video mẫu (18.7s, 720x1280, 30fps): khung đổi theo
NHỊP THOẠI chứ không animate thật — tức là stack ảnh-tĩnh + zoom nhẹ của mình làm được nguyên bản.

## BẰNG CHỨNG KHẢ THI (test thật 22/8 ~13:30Z)
FLUX schnell (key CF user, qua worker /api/cf-flux, 4 bước): vẽ ĐÚNG style — stickman đầu tròn
trắng, nét outline dày, pastel, cảnh văn phòng boss giận + nhân viên đưa cà phê. Chất lượng ngang
kênh tham chiếu. 1 ảnh ≈ 58 neuron → 5 khung/video ≈ 290n → 1 key CF free ≈ 34 video/ngày.
⚠️ Bộ lọc prompt CF (lỗi 8007 NSFW) chặn oan cụm "extreme close-up of face" — viết prompt tránh
từ nhạy cảm ("head-and-shoulders shot" thay "close-up face"), pipeline phải có bảng từ thay thế +
retry 1 lần khi 8007.

## 2 KÊNH CHỐT (22/8 tối — user yêu cầu nhân vật GỐC đậm chất Mỹ, KHÔNG nhái motip stickman; đã vẽ thử FLUX cả 2, chất lượng đạt):

### CH1 · BALD & BANDIT — cặp đôi lệch pha biểu tượng Mỹ
Nhân vật: **BALD** — đại bàng hói mặt cau có, đeo cà vạt sao-sọc, yêu nước quá đà, nói chuyện nghiêm
trang; **BANDIT** — gấu mèo bụi đời đeo kính râm đỏ, cầm ly soda, khôn lỏi, chuyên phá logic của Bald.
Niche: skit hài về nước Mỹ đời thường (fast food, thuế, freedom units, DMV, Black Friday...).
STYLE LOCK: "original cartoon duo, a grumpy proud bald eagle with stars-and-stripes necktie standing
upright, and a scruffy sly raccoon with red sunglasses holding a soda cup, modern bold flat vector
cartoon, thick outlines, saturated colors with red white blue accents, no signs, no lettering, no text".
Giọng: Bald = en-US-ChristopherNeural (trầm nghiêm), Bandit = en-US-GuyNeural +8% (lanh).

### CH2 · HANKTOWN — Americana retro thập niên 50-60
Nhân vật: **HANK** — ông bố Mỹ râu rậm, áo flannel đỏ, mũ trucker, thích BBQ/garage/xe cỏ;
hàng xóm **DALE** thò đầu qua hàng rào trắng góp chuyện. Niche: đời sống ngoại ô Mỹ hài hước
(BBQ, sửa xe, HOA, DIY hỏng, mua đồ Costco...).
STYLE LOCK: "retro 1950s American advertising cartoon, burly friendly dad with thick mustache in red
plaid flannel and trucker cap, mid-century UPA animation look, halftone print texture, mustard and
avocado retro palette, thick brush outlines, white picket fence suburb, no signs, no lettering, no text".
Giọng: Hank = en-US-RogerNeural (ấm), Dale = en-US-EricNeural.

⚠️ Bài học vẽ thử: FLUX hay TỰ VẼ CHỮ GIẢ lên biển hiệu ("AMERICNT") -> mọi prompt PHẢI có
"no signs, no lettering, no text" + title card của Remotion luôn đè vùng đỉnh; Vision kiểm khung
thêm tiêu chí "không có chữ vô nghĩa".

## Pipeline (tái dùng hạ tầng sẵn có)
1. **Kịch bản**: Groq viết skit 6-10 câu thoại + mô tả 3-5 khung (prompt NHỎ → vừa trần 8K).
   Schema: {title, scene_base, frames:[{prompt_delta, dur}], dialog:[{who:A/B, line}], punch}.
2. **Ảnh**: FLUX 3-5 khung = style-lock + scene_base + delta cảm xúc; Vision (Gemini) kiểm khung
   "đúng 2 stickman, không dị dạng, không chữ" (grid 1 lệnh); 8007 → thay từ + retry.
3. **Giọng**: edge-tts 2 giọng (A: en-US-GuyNeural, B: en-US-ChristopherNeural chậm 0.9) + SFX
   whoosh/ding + nhạc nền nhẹ.
4. **Dựng**: composition mới `ToonShort` (Remotion): khung theo nhịp thoại + zoom 2-4%/khung +
   phụ đề từng câu (đáy) + title card (đỉnh) + logo kênh góc. Thumbnail = khung biểu cảm nhất +
   title đè (đấu loại 2 nền FLUX khi sẵn).
5. **QC/đăng/1:3**: nguyên hệ hiện tại (qc_structure bỏ yêu cầu footage-thật cho format toon,
   thay bằng "đủ ≥3 khung ảnh sinh + có audio 2 giọng"); long = compilation 5-6 skit 16:9.

## Trình tự build (sau khi FLUX chạy ổn trong pipeline production)
B1 ToonShort.tsx + make_toon() + selftest mục toon → B2 render 1 video pilot cho user duyệt gu
→ B3 seed kênh BREAKROOM (đủ checklist CHANNEL_METHODS: 2 repo + 3 bảng nhúng dashboard + voices)
→ B4 vào matrix chạy 1 long : 3 short như mọi kênh.


## 3 KÊNH STORY (đổi nhân vật 22/8 đêm — user yêu cầu KHÔNG stickman, cartoon đầy đủ):
- TRUETALES · **PEARL** — bà hàng xóm tóc búi, cardigan đỏ, ly trà đá; flat cartoon kem+đỏ.
- DUMBHISTORY · **PROFESSOR BISON** — bò rừng Mỹ đội tricorn + kính tròn; khắc gỗ sepia.
- EXPLAINUSA · **THE OWL** — cú công sở cà vạt navy + clipboard; vector xanh nhạt deadpan.
Mỗi kênh 1 linh vật dẫn chuyện (narrator) + nhân vật phụ theo chuyện; art profile/cover vẽ FLUX
từ đúng style-lock video (đồng bộ nhận diện).