import React from "react";
import { staticFile } from "remotion";
import { KHO_CANVA } from "./KhoCanva";

/* ══════════════════════════════════════════════════════════════════════════════════════
   HÌNH HOẠ SĨ VẼ — kho Canva  (5/9/2026)

   117 hình gom từ Canva Elements (tác giả `zdeneksasek`, tài khoản Canva Pro của anh),
   toàn bộ NÉT MỰC trên nền trong suốt. Đây là lớp thay cho `BieuTuong` — hình que em tự
   vẽ bằng code, thứ anh đã chê suốt và đúng.

   ── VÌ SAO KHÔNG CẦN HOÀ MÀU  ─────────────────────────────────────────────────────────
   Đo được: 117/117 ảnh có tỉ lệ điểm-có-màu ≤ 0,12. Ảnh nét mực KHÔNG mang màu riêng, nên
   18 kênh dùng chung một kho mà mỗi kênh vẫn ra một tông — màu do bảng màu kênh cấp lúc
   dựng. Không kênh nào lệch tông được, vì không có tông nào để lệch.

   Đó là lý do chọn họ nét mực làm nền tảng thay vì họ tô màu: **màu là thứ mình CẤP,
   không phải thứ mình phải HOÀ.**

   ── VÌ SAO KHÔNG NEO ĐÁY VÀO SÀN ──────────────────────────────────────────────────────
   Bài học đắt nhất hôm nay: tranh unDraw mang mặt đất của CHÍNH NÓ ở một độ cao khác nhau
   ở từng bức, nên neo đáy vào sàn của mình là lơ lửng — và lơ lửng một lượng khác nhau ở
   từng bức, nên không hằng số nào chữa được.
   Hình Canva cũng là tranh hoàn chỉnh (người + đạo cụ + đôi khi cả mặt đất). Nên nó chiếm
   một Ô CỐ ĐỊNH trong khung, không neo sàn: một mặt đất duy nhất, của chính nó.
   ══════════════════════════════════════════════════════════════════════════════════════ */

export const co_canva = (tep: string): boolean => !!KHO_CANVA[tep];

/* ── PHẢI LÀ SVG-NATIVE, KHÔNG PHẢI <Img> CỦA REMOTION  (5/9/2026) ─────────────────────
   Bản đầu trả về `<div><Img/></div>` và render CHẾT ngay:

       TypeError  current.decode is not a function     ->  0/1 video

   Gốc: lớp chủ thể nằm TRONG thẻ `<svg>`. Một `<img>` HTML đặt trong cây SVG không tạo ra
   `HTMLImageElement`, nên `<Img>` của Remotion gọi `.decode()` trên một đối tượng không có
   hàm ấy. `esbuild` xanh, `tsc` xanh — chỉ lúc dựng mới nổ, đúng họ §15.18 (*build được
   không có nghĩa là chạy được*).

   Nay dùng `<image>` của SVG: nó là phần tử SVG thật, nằm đúng chỗ trong cây, và Remotion
   vẫn chờ ảnh tải xong vì `staticFile` trả về đường dẫn thường. */
export const CanvaVe: React.FC<{
  tep: string; W: number; H: number; san: number; p?: number; mau: string;
  dx?: number; dy?: number;
}> = ({ tep, W, H, san, p = 1, mau, dx = 0, dy = 0 }) => {
  const h = KHO_CANVA[tep];
  if (!h) return null;

  /* Ô cho hình: từ đỉnh vùng nội dung xuống mặt sàn, chừa lề hai bên. Vừa theo TỈ LỆ THẬT
     của ảnh, không kẹp hộp vuông — §17.2 đã trả giá cho `min(trần_cao, trần_ngang)` trên
     một hình không vuông. */
  const oCao = Math.max(1, san - H * 0.06);
  const oRong = W * 0.86;
  const k = Math.min(oRong / h.rong, oCao / h.cao);
  const w = h.rong * k, hh = h.cao * k;
  const x = (W - w) / 2, y = (san - hh) / 2 + H * 0.02;

  const q = Math.max(0, Math.min(1, p));
  const vao = Math.min(1, q / 0.22);
  return (
    /* ── HUỶ PHÉP DỊCH CỦA THẺ CHA  (5/9/2026) ──────────────────────────────────────
       Lớp chủ thể nằm trong `<g transform="translate(cx, sanY − sz·DAY_HINH)">` — phép
       dịch ấy sinh ra để neo ĐÁY hình que vào sàn. Hình Canva thì tự định vị trong khung,
       nên nó bị dịch thêm một lần và rơi xuống dưới-phải, đè lên phụ đề.
       Cùng họ §6 *chép hằng số sang hệ quy chiếu khác*: không báo lỗi, chỉ làm hình sai. */
    <g transform={`translate(${-dx} ${-dy})`} opacity={0.35 + 0.65 * vao}>
      <image href={staticFile("canva/" + tep)} x={x} y={y} width={w} height={hh}
             preserveAspectRatio="xMidYMid meet" />
    </g>
  );
};

/* KHÔNG tô lại màu ảnh.
   Bản đầu dùng `feColorMatrix` đảo độ đậm để nhuộm nét theo màu kênh. Render ra thì vùng
   TRONG SUỐT (RGB = 0) sau khi đảo thành màu đặc — mỗi hình thành một HỘP ĐEN che nửa
   khung. Bộ lọc SVG làm việc trên RGBA đã nhân alpha, nên phép đảo không giữ được nền
   trong suốt.
   Và nghĩ lại thì không cần nhuộm: nét mực đen trên giấy kraft CHÍNH LÀ chất của các kênh
   trăm triệu view. Màu kênh đã có ở chữ, con số và nền — thêm một chỗ nữa là thừa. */
