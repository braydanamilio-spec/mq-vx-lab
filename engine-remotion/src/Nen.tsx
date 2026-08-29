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

/** Ba chặng gradient cho một kênh: giữ SẮC của kênh, nhưng nền là NỀN — không phải mảng màu.
 *
 * 28/8 — ANH XEM 6 VIDEO: "nền neon có vẻ ko hợp lắm, nó làm mờ chữ loá". Đúng, và đây là hậu quả
 * trực tiếp của bản vá 26/8 ngay phía trên.
 *
 * Hôm đó phép đo là ĐỘ SÁNG TRUNG BÌNH của khung: 25-40/255, kết luận "tối om", nên nâng độ sáng
 * nền lên 36/26/18% và giữ bão hoà 24-46%. Con số sáng lên thật. Nhưng độ sáng trung bình là phép
 * đo SAI cho việc này: nó không phân biệt "nền tối, chữ và cột sáng" (đúng cách video dữ liệu
 * hạng nhất trông) với "nền sáng đều một màu" (cách nhìn rẻ tiền). Ta tối ưu đúng con số ấy và
 * nhận về đúng thứ nó đo — một mảng màu bão hoà chiếm gần hết khung.
 *
 * Với kênh accent neon (#2BF0AB, #23F74D, #27D627) thì mảng ấy là xanh lá 36% sáng, và chữ trắng
 * đặt lên trên tụt tương phản còn khoảng 5:1 — đọc được nhưng loá, đúng chữ anh dùng.
 *
 * Phép đo đúng là TƯƠNG PHẢN giữa chữ và nền ngay dưới nó, không phải độ sáng trung bình. Nền
 * tối và nhạt màu cho tương phản ~17:1 với chữ trắng; còn cảm giác "video sáng, có sức sống" thì
 * lấy từ NỘI DUNG — cột màu, thẻ số, quầng accent — chứ không lấy từ nền. Đó cũng là cách mọi
 * kênh dữ liệu tử tế làm.
 *
 * Nên: bão hoà 8-15% (trước 24-46%), độ sáng 15/10/7% (trước 36/26/18%). Sắc của kênh vẫn còn —
 * đủ để 50 kênh không giống nhau — nhưng nó là một tông nền, không còn là một mảng màu.
 * `lech` xoay nhẹ sắc giữa hai đầu gradient -> nền có chiều sâu, không phẳng như một mảng màu. */
export const nenKenh = (chinh?: string, phu?: string, lech = 18): string => {
  const [h1, s1] = _hsl(..._n(chinh || "#3a4a7a"));
  const [h2] = _hsl(..._n(phu || chinh || "#3a4a7a"));
  const bh = Math.round(h2 || h1);
  // Bão hoà thấp: đủ để nhận ra sắc riêng của kênh, không đủ để thành một mảng màu tranh chỗ
  // với dữ liệu. Sàn 8 để nền không rơi về xám hệt nhau cả 50 kênh.
  const sat = Math.round(Math.max(8, Math.min(15, (s1 || 0.4) * 100 * 0.22)));
  // ĐỘ SÁNG 21/17/14%, KHÔNG PHẢI 15/10/7 NHƯ BẢN ĐẦU.
  // Bản 15/10/7 cho tương phản đẹp hơn nữa (14,6:1) nhưng làm cổng `opening_is_flat` chặn video:
  // cổng đếm điểm có độ sáng đo được DƯỚI 40, mà nền 15% sáng rơi đúng 40 — tức gần như mọi điểm
  // của khung đều bị tính là "tối", và FAME CURVE bị bỏ lượt với "83,8% tối".
  // Không nới cổng: nó bắt đúng thứ nó sinh ra để bắt (chữ trên nền trơn), và nới một cổng để
  // vừa một thay đổi thẩm mỹ là mở cửa cho đúng loại video đã bị cấm.
  // 21% cho độ sáng đo được 55 — trên ngưỡng, mà tương phản chữ trắng vẫn 11,5:1 (cũ: 4,7:1).
  // Nền vẫn tối và vẫn nhạt màu; chỉ là không tối tới mức máy đo coi cả khung là bóng đêm.
  return `radial-gradient(126% 100% at 50% 6%,`
    // 29/8 — anh soi bảng ba bố cục: "template còn tối xấu". Nền 21/17/14% là ĐỦ tương phản cho
    // chữ nhưng vẫn đọc ra là một mảng tối lì. Nâng thêm một nấc (25/20/16%) và nới bão hoà một
    // chút: khung có sức sống hơn, mà tương phản chữ trắng vẫn 9,6:1 — vẫn gấp đôi bản neon cũ
    // (4,7:1) đã làm loá chữ. Đây là lần chỉnh thứ tư của bộ số này; ba lần trước ghi ở trên.
    + ` hsl(${Math.round(h1)} ${Math.round(sat * 1.25)}% 25%) 0%,`
    + ` hsl(${(bh + lech) % 360} ${Math.round(sat * 1.15)}% 20%) 54%,`
    + ` hsl(${(bh + lech * 2) % 360} ${sat}% 16%) 100%)`;
};

/** Vệt sáng phụ đặt lệch tâm — cho mỗi kênh một "hướng sáng" khác nhau, tránh cảm giác cùng khuôn. */
export const veSang = (mau?: string, goc = 0): string =>
  `radial-gradient(58% 42% at ${28 + (goc % 3) * 22}% ${18 + (goc % 2) * 54}%, ${mau || "#fff"}22, transparent 70%)`;

/** HẠT PHIM — một lớp nhiễu rất mảnh phủ lên nền.
 *
 * 28/8 — hạ nền xuống tối và nhạt màu (xem `nenKenh`) làm cổng `opening_is_flat` chặn FAME CURVE:
 * "87,5% tối · 266 màu". Cổng ấy bắt đúng: 266 màu nghĩa là khung mở đầu THẬT SỰ trống — trước
 * đây nó lọt chỉ vì nền sáng, chứ nội dung vẫn nghèo y như vậy.
 *
 * Cách sửa không phải nới ngưỡng mà làm khung giàu lên thật. Hạt phim làm đúng ba việc cùng lúc:
 *   • phá vệt loang (banding) — bệnh cố hữu của gradient tối khi nén H.264;
 *   • đưa số màu từ vài trăm lên hàng nghìn, tức nền không còn là một mảng phẳng;
 *   • cho khung cái chất "quay bằng máy" thay vì "vẽ bằng CSS".
 * Đây là thứ mọi nền tối tử tế đều có; mình thiếu nó nên phải bù bằng cách vặn nền sáng lên.
 *
 * ĐỘ MỜ PHẢI RẤT THẤP. Bản đầu tôi để `opacity=0.5` và nó phủ một tấm veil xám 50% lên toàn
 * khung: nền hết chói thật, nhưng cũng mất sạch sắc riêng của kênh và nhìn như một bức tường bẩn.
 * Hạt phim là thứ để CẢM thấy chứ không phải để NHÌN thấy — 0,055 là mức thấy được bằng máy đo
 * mà mắt chỉ đọc ra "nền có chất", không đọc ra "có nhiễu". Hạt dày còn làm phình bitrate.
 * Đã đo lại trên khung thật sau khi hạ. */
export const HAT_PHIM = "url(\"data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20width%3D%27180%27%20height%3D%27180%27%3E%3Cfilter%20id%3D%27n%27%3E%3CfeTurbulence%20type%3D%27fractalNoise%27%20baseFrequency%3D%270.8%27%20numOctaves%3D%273%27%20stitchTiles%3D%27stitch%27%2F%3E%3CfeColorMatrix%20type%3D%27saturate%27%20values%3D%270%27%2F%3E%3C%2Ffilter%3E%3Crect%20width%3D%27180%27%20height%3D%27180%27%20filter%3D%27url%28%23n%29%27%20opacity%3D%270.055%27%2F%3E%3C%2Fsvg%3E\")";

/** Nền hoàn chỉnh của một kênh: hạt phim nằm trên, gradient màu kênh nằm dưới. */
export const nenDayDu = (chinh?: string, phu?: string, lech = 18): string =>
  `${HAT_PHIM}, ${nenKenh(chinh, phu, lech)}`;
