import React from "react";
import { AbsoluteFill } from "remotion";

/* ══════════════════════════════════════════════════════════════════════════════════════
   MẶT SÀN MỚI: MỰC TRÊN GIẤY  (5/9/2026)

   Anh: *"kêu làm mới hoàn toàn sao vẫn kiểu cũ vậy, cái template cũ xấu đau đớn mà cứ để"*.
   Đúng. Suốt hôm nay em chỉnh THAM SỐ của `NenPhong` và `CanhVe` — hạ gradient, đổi màu,
   thêm vân giấy — nhưng vẫn là căn phòng cũ: cái bàn, cửa sổ, chậu cây, sàn đổ bóng. Đổi
   sơn một căn phòng thì nó vẫn là căn phòng ấy.

   Tệp này KHÔNG phải bản vá. Nó là mặt sàn khác hẳn, dựng theo đúng thứ đo được từ các kênh
   người-que trăm triệu view:

       · giấy kraft phủ TRỌN khung, có vân        (không phải mảng màu, không phải gradient)
       · MỘT đường chân trời vẽ tay, hơi lượn      (không phải hai dải sáng/tối)
       · vài vệt cỏ mảnh ở HAI MÉP                 (giữa khung để trống cho chủ thể — §7)
       · KHÔNG phòng, KHÔNG bàn, KHÔNG cửa sổ, KHÔNG chậu cây, KHÔNG bóng ellipse

   Cái cuối là phần quan trọng nhất. Mọi món đồ cũ đều từng có lý do lúc thêm, và cộng lại
   chúng thành một căn phòng chung xuất hiện sau MỌI câu — kể cả câu nói về một lá thư, một
   hàng rào, hay tốc độ ánh sáng. Một bối cảnh không liên quan thì không phải bối cảnh.

   `NenPhong` và `CanhVe` giữ nguyên trong repo: chúng còn phục vụ khuôn khác, và xoá một
   thứ đang chạy để lấy chỗ cho thứ chưa được duyệt là đổi sai chiều (§3).
   ══════════════════════════════════════════════════════════════════════════════════════ */

/* Nhiễu tất định — cùng một tập luôn cho ra cùng một tờ giấy, cùng một đường chân trời. */
const _r = (i: number) => {
  const x = Math.sin(i * 12.9898) * 43758.5453;
  return (x - Math.floor(x)) - 0.5;
};

/* Đường vẽ tay: nối các điểm bằng cung cong lệch nhẹ. Cùng cơ chế với nét nhân vật, nên
   sàn và người trông như do một cây bút vẽ ra — thiếu điều đó thì người vẽ tay đứng trên
   một đường thẳng máy kẻ, và mắt đọc ra ngay. */
const _net = (pts: number[][], hat: number, bien = 0.06): string => {
  let d = `M ${pts[0][0]} ${pts[0][1]}`;
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1], [x1, y1] = pts[i];
    const dx = x1 - x0, dy = y1 - y0;
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    const o = _r(hat * 7 + i * 3.1) * len * bien;
    d += ` Q ${(x0 + x1) / 2 - (dy / len) * o} ${(y0 + y1) / 2 + (dx / len) * o} ${x1} ${y1}`;
  }
  return d;
};

export const CanhMuc: React.FC<{
  W: number; H: number; san: number; giay: string; hat?: number; p?: number;
}> = ({ W, H, san, giay, hat = 0, p = 0 }) => {
  const id = `cm${Math.abs(hat) % 9973}`;
  const MUC = "#2C2722";
  const w = Math.max(2, W * 0.0042);

  /* Chân trời chia khung ở đâu là quyết định bố cục, không phải một hằng số tiện tay:
     đủ thấp để chủ thể có đất đứng, đủ cao để phần giấy trên không thành khoảng trống. */
  const yS = san;

  /* Cỏ ở HAI MÉP, không ở giữa. Số bụi đổi theo tập nên hai tập không ra một bờ cỏ. */
  const soCo = 5 + (Math.abs(hat) % 4);
  const co: number[][][] = [];
  for (let i = 0; i < soCo; i++) {
    const ben = i % 2 === 0 ? -1 : 1;
    const t = Math.floor(i / 2) / Math.max(1, soCo / 2);
    /* 0,06 → 0,30 tính từ mép: dải này nằm ngoài vùng chủ thể ở mọi cỡ cảnh. */
    const x = W * (0.5 + ben * (0.06 + t * 0.30 + Math.abs(_r(hat + i)) * 0.08));
    const c = H * (0.012 + Math.abs(_r(hat + i * 3)) * 0.010);
    co.push([[x, yS], [x - c * 0.5, yS - c * 1.7]]);
    co.push([[x, yS], [x + c * 0.4, yS - c * 1.4]]);
  }

  return (
    <AbsoluteFill>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute" }}>
        <defs>
          <filter id={`${id}van`} x="0" y="0" width="100%" height="100%">
            {/* 0,85 cho hạt mịn như sợi giấy; dưới 0,3 ra vệt loang như mây — đã thử. */}
            <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="4"
                          seed={Math.abs(hat) % 100} result="n" />
            <feColorMatrix in="n" type="saturate" values="0" />
          </filter>
          {/* Mép tờ giấy sẫm hơn giữa tờ. Đây là ĐẶC TÍNH CỦA GIẤY, khác hẳn dải gradient
              sáng/tối chiếm một phần ba khung mà em vừa phải đi bỏ. */}
          <radialGradient id={`${id}mep`} cx="0.5" cy="0.48" r="0.78">
            <stop offset="0.5" stopColor="#4A3520" stopOpacity="0" />
            <stop offset="1" stopColor="#4A3520" stopOpacity="0.17" />
          </radialGradient>
        </defs>

        <rect x={0} y={0} width={W} height={H} fill={giay} />
        <rect x={0} y={0} width={W} height={H} filter={`url(#${id}van)`}
              opacity={0.20} style={{ mixBlendMode: "multiply" }} />

        {/* ĐƯỜNG CHÂN TRỜI — một nét, kéo tràn qua cả hai mép. Kéo tràn là cố ý: đường
            dừng trước mép đọc ra một vật nằm trong khung, đường tràn ra đọc ra mặt đất. */}
        <path d={_net([[-W * 0.04, yS], [W * 0.3, yS], [W * 0.7, yS], [W * 1.04, yS]], hat, 0.02)}
              fill="none" stroke={MUC} strokeWidth={w} strokeLinecap="round" />

        {co.map((c, i) => (
          <path key={i} d={_net(c, hat + i * 11, 0.22)} fill="none" stroke={MUC}
                strokeWidth={w * 0.62} strokeLinecap="round" opacity={0.72} />
        ))}

        <rect x={0} y={0} width={W} height={H} fill={`url(#${id}mep)`} />
      </svg>
    </AbsoluteFill>
  );
};
