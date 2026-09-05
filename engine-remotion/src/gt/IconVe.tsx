import React from "react";
import { KHO_ICON } from "./KhoIcon";

/* ══════════════════════════════════════════════════════════════════════════════════════
   ICON LÀM CHỦ THỂ CỦA CẢNH  (5/9/2026)

   Thay `BieuTuong` (23 hình em tự vẽ) bằng icon do hoạ sĩ vẽ, chọn theo đúng chữ trong câu.
   Lý do và số đo nằm ở `render-pipeline/tai_icon.py`.

   ── VÌ SAO ICON KHÔNG LƠ LỬNG, TRONG KHI TRANH unDraw THÌ CÓ ────────────────────────────
   Bức unDraw là CẢ MỘT CẢNH: nó mang mặt đất của chính nó ở ~0,55 khung nó, nên neo đáy
   vào sàn của mình là sai — và sai một lượng KHÁC NHAU ở từng bức, nên không hằng số nào
   chữa được. Đó là thứ anh gọi là "lơ lửng", và là lý do em bỏ đường ấy.
   Icon là một VẬT PHẲNG không có đất. Mình đặt đáy nó vào mặt sàn thì nó đứng trên sàn, ở
   mọi icon, không ngoại lệ.

   ── MỘT VẬT, KHÔNG PHẢI MỘT BỘ SƯU TẬP ─────────────────────────────────────────────────
   Cám dỗ là xếp ba bốn icon cho "đầy khung". Đừng: §7 nói giữa khung phải trống cho chủ
   thể, và một khung ba icon đọc ra bảng biểu tượng chứ không đọc ra một cảnh. Một vật lớn,
   đứng trên sàn, trong một căn phòng — đó là bố cục của ảnh tham chiếu anh gửi.
   ══════════════════════════════════════════════════════════════════════════════════════ */

export const co_icon = (tu: string): boolean => !!KHO_ICON[tu];

export const IconVe: React.FC<{
  tu: string; s: number; p?: number; mau: string; mauPhu?: string;
}> = ({ tu, s, p = 1, mau, mauPhu = "" }) => {
  const ic = KHO_ICON[tu];
  if (!ic) return null;
  const [, , vw, vh] = ic.vb.split(/\s+/).map(Number);
  const k = s / Math.max(vw || 1, vh || 1);
  const q = Math.max(0, Math.min(1, p));
  /* Nét chạy trước, màu đổ sau — cùng cơ chế `TuVe`, nhưng làm bằng CSS vì ruột icon vào
     cây bằng `dangerouslySetInnerHTML` (Python đã chèn `pathLength="1"` lúc tải). */
  const m = q <= 0.3 ? 0 : Math.min(1, (q - 0.3) / 0.7);
  const id = `ic${tu.replace(/[^a-z]/g, "")}`;
  /* ── ĐỪNG ÉP NÉT VIỀN LÊN ICON  (5/9/2026, sau khi soi lưới) ──────────────────────────
     Bản đầu đặt `stroke:currentColor` cho MỌI hình con. Iconify trộn hai loại icon: loại
     vẽ bằng MẢNG ĐẶC và loại vẽ bằng NÉT. Ép viền lên loại đặc thì nó dày cộm; ép độ dày
     `1.2/k` lên loại nét thì nét gốc bị đè thành sợi chỉ — soi khung `trees` ra ba cái cây
     mờ tịt gần như không thấy.
     Icon đã được hoạ sĩ vẽ xong: việc của mình là ĐỔ MÀU, không phải vẽ lại. `currentColor`
     là cách Iconify khai chỗ nhận màu, nên chỉ cần đặt `color` ở thẻ cha. */
  const ruot = ic.ruot.replace(/\{MUC\}/g, "currentColor");
  return (
    <g transform={`translate(${-vw * k / 2} ${-vh * k}) scale(${k})`}>
      <style>{`#${id} *{stroke-dasharray:1;stroke-dashoffset:${(1 - q).toFixed(3)};`
             + `fill-opacity:${m.toFixed(3)}}`}</style>
      <g id={id} color="#2C2722"  /* MỰC, không phải màu kênh — xem chú thích ở `ruot` */ dangerouslySetInnerHTML={{ __html: ruot }} />
    </g>
  );
};
