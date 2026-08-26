// ─────────────────────────────────────────────────────────────────────────────
// NỀN RIÊNG TỪNG KÊNH (26/8/2026)
//
// Anh xem 5 video: "cùng 1 loại template, màu nền cần đa dạng cho phù hợp từng channel".
// Đúng: nền được viết CỨNG trong từng composition, nên **18 kênh dạng `ranked` dùng chung một
// nền**, 10 kênh `cinematic` chung một nền khác. Màu accent thì riêng, nhưng accent chỉ chiếm vài
// phần trăm khung hình — nền chiếm gần hết, nên mắt vẫn thấy "cùng một lò".
//
// Trong khi đó brand kit đã có sẵn cho MỖI kênh: `bg` (38 giá trị khác nhau), `primary` (50),
// `secondary` (50) — và **không dòng mã nào đọc chúng**. Đây là lần thứ NĂM cùng một bệnh trong
// hệ này (`voice_tone` · `voice_pitch` · `brand.font` · `tham_so.xoay` · giờ là `palette.bg`).
//
// Thêm một việc nữa: đo 5 video thật thì sáng trung bình chỉ **25-40/255** (short trên feed
// thường 60-100) — nhìn tối om. Nên KHÔNG dùng `bg` thô (chúng đều cỡ #0A1317, gần đen), mà
// dựng nền TỪ màu của kênh ở độ sáng kiểm soát được: giữ sắc riêng, nâng độ sáng.
// ─────────────────────────────────────────────────────────────────────────────

const _n = (h: string): [number, number, number] => {
  const t = String(h || "#222").replace("#", "");
  const s = t.length === 3 ? t.split("").map((c) => c + c).join("") : t;
  return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16) || 0) as [number, number, number];
};

const _hsl = (r: number, g: number, b: number): [number, number, number] => {
  r /= 255; g /= 255; b /= 255;
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  let h = 0;
  if (d) {
    if (mx === r) h = ((g - b) / d) % 6;
    else if (mx === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
  }
  h = (h * 60 + 360) % 360;
  const l = (mx + mn) / 2;
  const s = d ? d / (1 - Math.abs(2 * l - 1)) : 0;
  return [h, s, l];
};

/** Ba chặng gradient cho một kênh: giữ SẮC của kênh, đặt ĐỘ SÁNG ở mức đọc được.
 *  `lech` xoay nhẹ sắc giữa hai đầu gradient -> nền có chiều sâu, không phẳng như một mảng màu. */
export const nenKenh = (chinh?: string, phu?: string, lech = 18): string => {
  const [h1, s1] = _hsl(..._n(chinh || "#3a4a7a"));
  const [h2] = _hsl(..._n(phu || chinh || "#3a4a7a"));
  const bh = Math.round(h2 || h1);
  // Bão hoà vừa phải: quá đậm thì chữ trắng chói mắt, quá nhạt thì lại về xám như nhau cả loạt.
  const sat = Math.round(Math.max(24, Math.min(46, (s1 || 0.4) * 100 * 0.62)));
  // Độ sáng đo bằng khung render thật, không đoán: mức 27/18/12% cho ra khung trung bình 34/255 —
  // vẫn tối. 36/26/18% đưa khung lên khoảng 60, đúng dải short trên feed (60-100).
  return `radial-gradient(122% 96% at 50% 8%,`
    + ` hsl(${Math.round(h1)} ${sat}% 36%) 0%,`
    + ` hsl(${(bh + lech) % 360} ${sat}% 26%) 52%,`
    + ` hsl(${(bh + lech * 2) % 360} ${Math.round(sat * 0.9)}% 18%) 100%)`;
};

/** Vệt sáng phụ đặt lệch tâm — cho mỗi kênh một "hướng sáng" khác nhau, tránh cảm giác cùng khuôn. */
export const veSang = (mau?: string, goc = 0): string =>
  `radial-gradient(58% 42% at ${28 + (goc % 3) * 22}% ${18 + (goc % 2) * 54}%, ${mau || "#fff"}22, transparent 70%)`;
