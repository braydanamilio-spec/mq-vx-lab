/* ══ PHÔNG CHỮ RIÊNG TỪNG KÊNH  (4/9/2026) ═════════════════════════════════════════════════
   Anh: *"nâng cấp template mỗi channel cho đa dạng, không trùng lặp"*.

   Đo trước: cả 18 kênh dùng chung MỘT phông (`Poppins`). Kiểu chữ là dấu hiệu nhận diện mạnh
   nhất của một kênh giải thích — người xem nhớ nét chữ trước khi nhớ tên kênh — và nó hiện ở
   ~90% số nhịp, tức đổi nó là đổi gần như mọi khung.

   ── VÌ SAO MỘT BIẾN MÔ-ĐUN, KHÔNG PHẢI PROP ─────────────────────────────────────────────
   `fontFamily={F}` nằm ở 31 chỗ trong `Khuon.tsx`, mỗi chỗ một component khác nhau. Luồn một
   prop qua 31 chỗ là 31 cơ hội để quên một chỗ — và chỗ quên sẽ im lặng dùng phông cũ, tức
   một khung lẫn hai phông mà không có lỗi nào báo.

   React dựng cây từ trên xuống trong CÙNG một lượt đồng bộ, và Remotion dựng một composition
   mỗi tiến trình. Nên đặt phông MỘT LẦN ở đầu component gốc rồi để mọi nơi đọc là an toàn và
   không có chỗ nào để quên.

   ── PHÔNG CHỌN THEO CHẤT KÊNH, KHÔNG XOAY VÒNG ───────────────────────────────────────────
   Năm phông, mỗi phông một tính cách rõ, và mọi phông đều có nét đậm 900 (chữ số của bộ này
   rất to nên phông thiếu nét đậm sẽ đọc ra yếu):

     Poppins  hình học, tròn, trung tính   -> kênh đời thường
     Anton    hẹp, rất nặng, dứt khoát     -> kênh cực đoan / gây choáng
     Oswald   hẹp vừa, nghiêm              -> kênh số liệu, quy tắc
     Archivo  vuông vức, kỹ thuật          -> kênh cơ chế, tốc độ
     Rubik    bo góc, thân thiện           -> kênh nhẹ nhàng, đời người

   Python KHÔNG quyết cái này (khác `DAU_AN`): phông là thuộc tính của KÊNH, không đổi theo
   tập, nên để nó cạnh engine thì chỉ có một chỗ khai. Nhưng vẫn phải khai TƯỜNG MINH từng
   kênh — gán vòng tròn thì hai kênh cạnh nhau trong bảng lại trùng phông (§17.3). */

const HO: Record<string, string> = {
  poppins: "Poppins, Arial Black, sans-serif",
  anton:   "Anton, Arial Black, sans-serif",
  oswald:  "Oswald, Arial Narrow, sans-serif",
  archivo: "Archivo, Arial Black, sans-serif",
  rubik:   "Rubik, Arial Black, sans-serif",
};

/* Gán tường minh. 18 kênh trên 5 phông nên trùng là KHÔNG tránh được — khác `DAU_AN` (20 tổ
   hợp cho 18 kênh, duy nhất được). Nên ở đây mục tiêu không phải "không kênh nào trùng" mà là
   "hai kênh CÙNG CHẤT không trùng nhau", và phông đi CÙNG dấu ấn: hai kênh chung phông thì
   chắc chắn khác kiểu chân trời và khác nét quanh con số. */
const CHU_KENH: Record<string, string> = {
  howlong: "poppins",  howbig: "anton",    realcost: "oswald",  howmuch: "archivo",
  whatif: "rubik",     survive: "anton",   dayinlife: "rubik",  wheregoes: "poppins",
  therules: "oswald",  speedof: "archivo", odds: "oswald",      hiddenfee: "archivo",
  yearsof: "rubik",    howloud: "anton",   whatweighs: "poppins", rightnow: "poppins",
  howhot: "anton",     smallest: "archivo",
};

let _hienTai = HO.poppins;

/** Đặt phông cho cả lượt dựng. Gọi MỘT LẦN ở đầu component gốc, trước khi dựng con. */
export const datChu = (ma: string): void => {
  _hienTai = HO[CHU_KENH[ma] || "poppins"] || HO.poppins;
};

/** Phông đang dùng. Gọi tại chỗ vẽ chữ, không cache vào biến ngoài component. */
export const chu = (): string => _hienTai;
