import React from "react";

// ══════════════════════════════════════════════════════════════════════════════════════════
// NỀN PANEL — vẽ bằng code, không dùng ảnh
// ------------------------------------------------------------------------------------------
// Bản hài cũ sinh nền bằng prompt ảnh AI cho từng lượt thoại. Hỏng theo hai đường, và cả hai
// đều nằm ngoài tầm sửa của bất kỳ prompt nào:
//
//   1. Ảnh photoreal đứng cạnh người vẽ phẳng thì mắt đọc ra ngay là hai lớp dán chồng.
//   2. Prompt viết từ nội dung lượt thoại vẫn trả về ảnh không có sàn, hoặc có vật che ngang
//      bụng nhân vật (cái giỏ giặt trong khung anh gửi). Ảnh không hứa gì về bố cục.
//
// Nền vẽ bằng code thì cùng cây bút với nhân vật, và quan trọng hơn: TÔI BIẾT SÀN Ở ĐÂU. Mọi
// nền dưới đây đều dựng theo cùng một xương — mảng tường, đường chân tường, mặt sàn — nên nhân
// vật không bao giờ đứng lơ lửng hay đứng trên mặt bàn.
//
// Nền cũng KHÔNG được rối. Nó là phông, không phải nhân vật chính: hình khối to, ít chi tiết,
// độ tương phản thấp hơn người rõ rệt.
// ══════════════════════════════════════════════════════════════════════════════════════════

const MUC = "#14110F";

/** Pha màu về phía trắng — dùng cho tường, để nhân vật luôn đậm hơn nền. */
const nhat = (hex: string, t: number) => {
  const h = hex.replace("#", "");
  const n = parseInt(h.length === 3 ? h.split("").map((c) => c + c).join("") : h, 16);
  const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  const p = (v: number) => Math.round(v + (255 - v) * t);
  return `rgb(${p(r)},${p(g)},${p(b)})`;
};

type P = { w: number; h: number; mau: string; mauPhu: string; hat: number; rong: boolean };

/** Xương chung: tường + đường chân tường + sàn. `yS` là mức sàn theo tỉ lệ chiều cao panel. */
const Xuong: React.FC<P & { yS?: number; tuong?: string; san?: string }> =
({ w, h, mau, yS = 0.74, tuong, san }) => {
  const y = h * yS;
  return (
    <>
      <rect x={0} y={0} width={w} height={y} fill={tuong || nhat(mau, 0.82)} />
      <rect x={0} y={y} width={w} height={h - y} fill={san || nhat(mau, 0.62)} />
      <line x1={0} y1={y} x2={w} y2={y} stroke={MUC} strokeWidth={4} opacity={0.5} />
      {/* Chân tường và một vệt sáng chéo — hai thứ rẻ nhất để một mảng tường phẳng đọc ra là
          một căn phòng có chiều sâu, thay vì một hình chữ nhật tô màu. */}
      <rect x={0} y={y - h * 0.045} width={w} height={h * 0.045} fill="#00000010" />
      <path d={`M${w * 0.62} 0 L${w * 0.86} 0 L${w * 0.5} ${y} L${w * 0.3} ${y} Z`}
            fill="#FFFFFF" opacity={0.14} />
    </>
  );
};

// ── MƯỜI BỐI CẢNH ─────────────────────────────────────────────────────────────────────────
// Mỗi kênh một nơi chốn cố định, đọc ra trong một giây: cửa căn hộ, phòng tập, cổng bay, gara,
// vách ngăn văn phòng, tủ lạnh, bàn máy, phòng khách đồ chơi, hàng rào, quán cà phê.

// ══ MƯỜI BỐI CẢNH ═════════════════════════════════════════════════════════════════════════
// 31/8, viết lại lần hai. Bản đầu mỗi nền chỉ có hai ba hình khối, và khung DATING APP phơi ra
// hậu quả: một panel cao 800px với hai người to đùng đứng trước một mảng hồng trơn, phía dưới
// là cái bàn mỏng dính. Nền nghèo không lộ ra ở panel thấp, nhưng panel cao thì lộ ngay.
//
// Mỗi bối cảnh từ nay phải đủ BA TẦNG, và thiếu tầng nào cũng đọc ra là nền chưa vẽ xong:
//   · vật ĐỨNG SÀN, đáy chạm đường sàn — cho biết mặt đất ở đâu;
//   · vật TREO TƯỜNG ở tầm mắt — lấp khoảng tường trống sau đầu nhân vật;
//   · chi tiết nhỏ — thứ mắt bắt được ở lần xem thứ hai.
// Và tất cả dồn về HAI BÊN MÉP: khoảng giữa panel là chỗ của hai nhân vật.

const RentPanic: React.FC<P> = (p) => {
  const { w, h } = p; const yS = h * 0.74;
  return (<>
    <Xuong {...p} tuong={nhat(p.mau, 0.87)} />
    {/* cửa căn hộ + số phòng + hộp thư — hành lang chung cư */}
    <rect x={w * 0.03} y={yS - h * 0.62} width={w * 0.2} height={h * 0.62}
          fill={nhat(p.mauPhu, 0.45)} stroke={MUC} strokeWidth={5} />
    <circle cx={w * 0.2} cy={yS - h * 0.3} r={6} fill={MUC} />
    <rect x={w * 0.08} y={yS - h * 0.56} width={w * 0.1} height={h * 0.07} rx={2}
          fill="#FFFFFF" stroke={MUC} strokeWidth={3} />
    {[0, 1, 2, 3].map((i) => (
      <rect key={i} x={w * (0.76 + (i % 2) * 0.1)} y={yS - h * (0.5 - Math.floor(i / 2) * 0.14)}
            width={w * 0.09} height={h * 0.12} rx={2}
            fill={nhat(p.mau, 0.5)} stroke={MUC} strokeWidth={3.5} />
    ))}
    <rect x={w * 0.3} y={yS - h * 0.05} width={w * 0.4} height={h * 0.05}
          fill={nhat(p.mau, 0.35)} opacity={0.5} />
  </>);
};

const GymLies: React.FC<P> = (p) => {
  const { w, h } = p; const yS = h * 0.74;
  return (<>
    <Xuong {...p} tuong={nhat(p.mau, 0.82)} san="#8A8A93" />
    {/* gương dài + giá tạ + tạ nằm sàn */}
    <rect x={w * 0.6} y={yS - h * 0.66} width={w * 0.36} height={h * 0.66}
          fill="#FFFFFF" stroke={MUC} strokeWidth={5} opacity={0.5} />
    <line x1={w * 0.6} y1={yS - h * 0.66} x2={w * 0.96} y2={yS - h * 0.3}
          stroke="#FFFFFF" strokeWidth={9} opacity={0.6} />
    <rect x={w * 0.02} y={yS - h * 0.5} width={w * 0.17} height={h * 0.5}
          fill={nhat(p.mauPhu, 0.4)} stroke={MUC} strokeWidth={4.5} />
    {[0, 1, 2].map((i) => (
      <line key={i} x1={w * 0.02} y1={yS - h * (0.4 - i * 0.14)} x2={w * 0.19}
            y2={yS - h * (0.4 - i * 0.14)} stroke={MUC} strokeWidth={3.5} />
    ))}
    <g stroke={MUC} strokeWidth={4.5} fill={nhat(p.mau, 0.3)}>
      <circle cx={w * 0.26} cy={yS - h * 0.05} r={h * 0.05} />
      <circle cx={w * 0.36} cy={yS - h * 0.05} r={h * 0.05} />
      <rect x={w * 0.26} y={yS - h * 0.065} width={w * 0.1} height={h * 0.025} />
    </g>
  </>);
};

const AirportHell: React.FC<P> = (p) => {
  const { w, h } = p; const yS = h * 0.78;
  return (<>
    <Xuong {...p} tuong={nhat(p.mauPhu, 0.88)} yS={0.78} />
    {/* vách kính + bảng cổng + hàng ghế chờ */}
    {[0, 1, 2, 3].map((i) => (
      <line key={i} x1={w * (0.08 + i * 0.28)} y1={0} x2={w * (0.08 + i * 0.28)} y2={yS}
            stroke={MUC} strokeWidth={4} opacity={0.3} />
    ))}
    <rect x={w * 0.28} y={h * 0.04} width={w * 0.44} height={h * 0.15} rx={4}
          fill={MUC} stroke={MUC} strokeWidth={4} />
    <text x={w * 0.5} y={h * 0.145} textAnchor="middle" fill="#FF7A4A"
          fontFamily="Poppins, sans-serif" fontWeight={900} fontSize={Math.min(h * 0.1, 40)}>
      DELAYED
    </text>
    {[0, 1, 2].map((i) => (
      <g key={i}>
        <rect x={w * (0.03 + i * 0.11)} y={yS - h * 0.16} width={w * 0.1} height={h * 0.05}
              fill={nhat(p.mau, 0.35)} stroke={MUC} strokeWidth={4} />
        <rect x={w * (0.03 + i * 0.11)} y={yS - h * 0.28} width={w * 0.1} height={h * 0.13}
              rx={3} fill={nhat(p.mau, 0.45)} stroke={MUC} strokeWidth={4} />
      </g>
    ))}
  </>);
};

const CarGuy: React.FC<P> = (p) => {
  const { w, h } = p; const yS = h * 0.8;
  return (<>
    <Xuong {...p} tuong={nhat(p.mau, 0.8)} san="#7C7C84" yS={0.8} />
    {/* nửa chiếc xe nâng cầu + bảng treo dụng cụ */}
    <rect x={-w * 0.06} y={yS - h * 0.4} width={w * 0.5} height={h * 0.26} rx={14}
          fill={nhat(p.mauPhu, 0.3)} stroke={MUC} strokeWidth={5} />
    <rect x={w * 0.04} y={yS - h * 0.52} width={w * 0.26} height={h * 0.14} rx={10}
          fill={nhat(p.mauPhu, 0.55)} stroke={MUC} strokeWidth={5} />
    <circle cx={w * 0.05} cy={yS - h * 0.1} r={h * 0.1} fill={MUC} />
    <circle cx={w * 0.05} cy={yS - h * 0.1} r={h * 0.045} fill={nhat(p.mau, 0.6)} />
    <circle cx={w * 0.33} cy={yS - h * 0.1} r={h * 0.1} fill={MUC} />
    <circle cx={w * 0.33} cy={yS - h * 0.1} r={h * 0.045} fill={nhat(p.mau, 0.6)} />
    <rect x={w * 0.74} y={h * 0.08} width={w * 0.22} height={h * 0.42}
          fill={nhat(p.mau, 0.55)} stroke={MUC} strokeWidth={4.5} />
    {[0, 1, 2, 3].map((i) => (
      <line key={i} x1={w * (0.77 + i * 0.05)} y1={h * 0.12} x2={w * (0.77 + i * 0.05)}
            y2={h * (0.24 + (i % 2) * 0.1)} stroke={MUC} strokeWidth={5} strokeLinecap="round" />
    ))}
  </>);
};

const OfficeSmallTalk: React.FC<P> = (p) => {
  const { w, h } = p; const yS = h * 0.8;
  return (<>
    <Xuong {...p} tuong={nhat(p.mauPhu, 0.89)} yS={0.8} />
    {/* vách ngăn cubicle + máy pha cà phê + bảng ghim giấy */}
    <rect x={w * 0.02} y={yS - h * 0.46} width={w * 0.34} height={h * 0.46}
          fill={nhat(p.mau, 0.6)} stroke={MUC} strokeWidth={5} />
    <rect x={w * 0.02} y={yS - h * 0.46} width={w * 0.34} height={h * 0.05}
          fill={nhat(p.mau, 0.4)} stroke={MUC} strokeWidth={4} />
    <rect x={w * 0.66} y={yS - h * 0.34} width={w * 0.3} height={h * 0.34}
          fill={nhat(p.mau, 0.7)} stroke={MUC} strokeWidth={5} />
    <rect x={w * 0.72} y={yS - h * 0.52} width={w * 0.12} height={h * 0.18} rx={3}
          fill={MUC} stroke={MUC} strokeWidth={4} />
    <rect x={w * 0.745} y={yS - h * 0.4} width={w * 0.07} height={h * 0.05}
          fill={nhat(p.mauPhu, 0.3)} />
    {[0, 1, 2].map((i) => (
      <rect key={i} x={w * (0.41 + i * 0.07)} y={h * (0.1 + (i % 2) * 0.06)}
            width={w * 0.055} height={h * 0.08} rx={2}
            fill="#FFFFFF" stroke={MUC} strokeWidth={3} transform={`rotate(${i * 4 - 4} ${w * 0.44} ${h * 0.14})`} />
    ))}
  </>);
};

const DietWars: React.FC<P> = (p) => {
  const { w, h } = p; const yS = h * 0.74;
  return (<>
    <Xuong {...p} tuong={nhat(p.mauPhu, 0.9)} />
    {/* tủ lạnh hai cánh + kệ bếp + tủ treo */}
    <rect x={w * 0.72} y={yS - h * 0.72} width={w * 0.25} height={h * 0.72}
          fill="#FFFFFF" stroke={MUC} strokeWidth={5} />
    <line x1={w * 0.72} y1={yS - h * 0.44} x2={w * 0.97} y2={yS - h * 0.44}
          stroke={MUC} strokeWidth={4} />
    <rect x={w * 0.735} y={yS - h * 0.4} width={w * 0.012} height={h * 0.12} rx={3} fill={MUC} />
    <rect x={w * 0.735} y={yS - h * 0.62} width={w * 0.012} height={h * 0.12} rx={3} fill={MUC} />
    <rect x={w * 0.02} y={yS - h * 0.2} width={w * 0.36} height={h * 0.2}
          fill={nhat(p.mau, 0.45)} stroke={MUC} strokeWidth={5} />
    <rect x={w * 0.02} y={yS - h * 0.22} width={w * 0.36} height={h * 0.035}
          fill={nhat(p.mau, 0.25)} stroke={MUC} strokeWidth={4} />
    <rect x={w * 0.05} y={h * 0.06} width={w * 0.3} height={h * 0.22}
          fill={nhat(p.mau, 0.6)} stroke={MUC} strokeWidth={5} />
    <circle cx={w * 0.12} cy={yS - h * 0.27} r={h * 0.04} fill={nhat(p.mauPhu, 0.3)}
            stroke={MUC} strokeWidth={4} />
  </>);
};

const TechSupport: React.FC<P> = (p) => {
  const { w, h } = p; const yS = h * 0.76;
  return (<>
    <Xuong {...p} tuong={nhat(p.mauPhu, 0.87)} yS={0.76} />
    {/* MỌI VẬT PHẢI CHẠM MỘT MẶT NÀO ĐÓ: màn hình đứng trên bàn, bàn có chân, tủ có tay nắm. */}
    <rect x={w * 0.02} y={yS - h * 0.16} width={w * 0.34} height={h * 0.035}
          fill={nhat(p.mau, 0.5)} stroke={MUC} strokeWidth={4} />
    <rect x={w * 0.06} y={yS - h * 0.125} width={h * 0.02} height={h * 0.125} fill={MUC} opacity={0.7} />
    <rect x={w * 0.3} y={yS - h * 0.125} width={h * 0.02} height={h * 0.125} fill={MUC} opacity={0.7} />
    <rect x={w * 0.07} y={yS - h * 0.4} width={w * 0.24} height={h * 0.2} rx={5}
          fill={MUC} stroke={MUC} strokeWidth={4} />
    <rect x={w * 0.085} y={yS - h * 0.385} width={w * 0.21} height={h * 0.17}
          fill={p.mauPhu} opacity={0.8} />
    <rect x={w * 0.175} y={yS - h * 0.2} width={w * 0.03} height={h * 0.04} fill={MUC} />
    <rect x={w * 0.79} y={yS - h * 0.46} width={w * 0.15} height={h * 0.46}
          fill={nhat(p.mau, 0.5)} stroke={MUC} strokeWidth={4} />
    {[0, 1, 2].map((i) => (
      <g key={i}>
        <line x1={w * 0.79} y1={yS - h * (0.46 - 0.153 * (i + 1))} x2={w * 0.94}
              y2={yS - h * (0.46 - 0.153 * (i + 1))} stroke={MUC} strokeWidth={3} />
        <rect x={w * 0.845} y={yS - h * (0.42 - 0.153 * i)} width={w * 0.04} height={h * 0.018}
              rx={3} fill={MUC} />
      </g>
    ))}
  </>);
};

const ParentMode: React.FC<P> = (p) => {
  const { w, h } = p; const yS = h * 0.74;
  return (<>
    <Xuong {...p} tuong={nhat(p.mau, 0.88)} />
    {/* ghế sofa + kệ đồ chơi + đồ chơi vương sàn */}
    <rect x={w * 0.6} y={yS - h * 0.34} width={w * 0.38} height={h * 0.34} rx={10}
          fill={nhat(p.mauPhu, 0.45)} stroke={MUC} strokeWidth={5} />
    <rect x={w * 0.6} y={yS - h * 0.46} width={w * 0.38} height={h * 0.14} rx={10}
          fill={nhat(p.mauPhu, 0.35)} stroke={MUC} strokeWidth={5} />
    <rect x={w * 0.03} y={yS - h * 0.44} width={w * 0.2} height={h * 0.44}
          fill={nhat(p.mau, 0.5)} stroke={MUC} strokeWidth={5} />
    {[0, 1].map((i) => (
      <line key={i} x1={w * 0.03} y1={yS - h * (0.3 - i * 0.15)} x2={w * 0.23}
            y2={yS - h * (0.3 - i * 0.15)} stroke={MUC} strokeWidth={4} />
    ))}
    {[0, 1, 2, 3].map((i) => (
      <circle key={i} cx={w * (0.28 + i * 0.11)} cy={yS - h * (0.035 + (i % 2) * 0.03)}
              r={h * 0.038} fill={i % 2 ? p.mau : p.mauPhu} stroke={MUC} strokeWidth={3.5} />
    ))}
  </>);
};

const NeighborWatch: React.FC<P> = (p) => {
  const { w, h } = p; const yS = h * 0.72;
  const n = Math.max(6, Math.round(w / 70));
  return (<>
    <Xuong {...p} tuong={nhat(p.mauPhu, 0.9)} san="#8FBF6A" yS={0.72} />
    {/* hàng rào cọc trắng + hòm thư + bụi cây — sân trước nhà kiểu ngoại ô Mỹ */}
    {Array.from({ length: n }, (_, i) => (
      <rect key={i} x={(w / n) * i + 6} y={yS - h * 0.3} width={w / n - 12} height={h * 0.3} rx={3}
            fill="#FFFFFF" stroke={MUC} strokeWidth={3.5} opacity={0.95} />
    ))}
    <line x1={0} y1={yS - h * 0.22} x2={w} y2={yS - h * 0.22} stroke={MUC} strokeWidth={4} opacity={0.8} />
    <rect x={w * 0.05} y={yS - h * 0.52} width={w * 0.02} height={h * 0.3} fill={MUC} opacity={0.75} />
    <rect x={w * 0.005} y={yS - h * 0.62} width={w * 0.11} height={h * 0.1} rx={5}
          fill={nhat(p.mau, 0.4)} stroke={MUC} strokeWidth={4} />
    <circle cx={w * 0.9} cy={yS - h * 0.36} r={h * 0.11} fill="#6FA84E" stroke={MUC} strokeWidth={4} />
    <circle cx={w * 0.82} cy={yS - h * 0.29} r={h * 0.07} fill="#7CB85C" stroke={MUC} strokeWidth={4} />
  </>);
};

const DatingApp: React.FC<P> = (p) => {
  const { w, h } = p; const yS = h * 0.78;
  return (<>
    <Xuong {...p} tuong={nhat(p.mau, 0.86)} yS={0.78} />
    {/* 31/8 — nền này là nền hỏng nặng nhất của bản đầu: một cái bàn mỏng ở đáy và hai vật tròn
        lơ lửng, còn lại là mảng hồng trơn. Quán cà phê phải có quầy, đèn treo, cửa sổ và bàn có
        chân — bốn thứ, chia đều hai bên mép. */}
    <rect x={w * 0.66} y={yS - h * 0.44} width={w * 0.32} height={h * 0.44}
          fill={nhat(p.mauPhu, 0.55)} stroke={MUC} strokeWidth={5} />
    <rect x={w * 0.66} y={yS - h * 0.48} width={w * 0.32} height={h * 0.055} rx={3}
          fill={nhat(p.mauPhu, 0.3)} stroke={MUC} strokeWidth={4.5} />
    <rect x={w * 0.72} y={yS - h * 0.42} width={w * 0.09} height={h * 0.12} rx={3}
          fill={MUC} opacity={0.75} />
    <rect x={w * 0.02} y={h * 0.06} width={w * 0.3} height={h * 0.34} rx={6}
          fill="#FFFFFF" opacity={0.5} stroke={MUC} strokeWidth={5} />
    <line x1={w * 0.17} y1={h * 0.06} x2={w * 0.17} y2={h * 0.4} stroke={MUC} strokeWidth={4} />
    {[0, 1].map((i) => (
      <g key={i}>
        <line x1={w * (0.42 + i * 0.16)} y1={0} x2={w * (0.42 + i * 0.16)} y2={h * 0.13}
              stroke={MUC} strokeWidth={3.5} />
        <path d={`M${w * (0.39 + i * 0.16)} ${h * 0.13} L${w * (0.45 + i * 0.16)} ${h * 0.13}
                  L${w * (0.44 + i * 0.16)} ${h * 0.2} L${w * (0.4 + i * 0.16)} ${h * 0.2} Z`}
              fill={nhat(p.mauPhu, 0.35)} stroke={MUC} strokeWidth={4} strokeLinejoin="round" />
      </g>
    ))}
    <rect x={w * 0.24} y={yS - h * 0.16} width={w * 0.32} height={h * 0.035} rx={4}
          fill={nhat(p.mauPhu, 0.4)} stroke={MUC} strokeWidth={4.5} />
    <rect x={w * 0.385} y={yS - h * 0.125} width={w * 0.03} height={h * 0.125} fill={MUC} opacity={0.8} />
    <ellipse cx={w * 0.4} cy={yS} rx={w * 0.09} ry={h * 0.02} fill={MUC} opacity={0.15} />
  </>);
};

// Nơi nào có trần, nơi nào có trời. Dùng để lấp khoảng tường phía trên trong khung dọc.
const NGOAI_TROI: Record<string, boolean> = { neighborwatch: true };

const BOI_CANH: Record<string, React.FC<P>> = {
  rentpanic: RentPanic, gymlies: GymLies, airporthell: AirportHell, carguy: CarGuy,
  officesmalltalk: OfficeSmallTalk, dietwars: DietWars, techsupport: TechSupport,
  parentmode: ParentMode, neighborwatch: NeighborWatch, datingapp: DatingApp,
};

/**
 * Nền của một panel.
 *
 * Panel CẬN (rong=false) chỉ vẽ mảng màu + halftone: ở cỡ cận, khung chỉ còn đầu và vai, nên
 * mọi đồ đạc đều rơi ra ngoài mép. Vẽ chúng vào chỉ tạo ra những mẩu hình khó hiểu sau lưng
 * nhân vật — đúng lỗi "cái giỏ giặt chắn ngang bụng" của bản cũ, chỉ khác nguồn.
 */
export const NenPanel: React.FC<{
  kenh: string; w: number; h: number; mau: string; mauPhu: string; hat: number;
  rong: boolean; bien?: number;
}> = ({ kenh, w, h, mau, mauPhu, hat, rong, bien = 0 }) => {
  const Ve = BOI_CANH[kenh];
  // 31/8 — MỖI PANEL MỘT GÓC NHÌN KHÁC. Khung thử cho ra sáu panel với cùng cái màn hình ở
  // cùng một chỗ, và sáu lần lặp lại một hình trong hai mươi giây thì mắt đọc ra là ảnh dán,
  // không phải là sáu ô truyện tranh. Cùng một căn phòng nhìn từ ba chỗ đứng vẫn là một căn
  // phòng — chỉ là máy đã dịch đi, đúng như một hoạ sĩ truyện tranh vẽ trang của mình.
  const DICH = [-0.20, 0.02, 0.16], PHONG = [1.18, 1.0, 1.10];
  const b = ((bien % 3) + 3) % 3;
  const hSK = Math.min(h, Math.max(w * 0.62, Math.min(h * 0.74, w * 1.2)));   // chiều cao sân khấu
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}
         style={{ position: "absolute", inset: 0, zIndex: 1 }}>
      <defs>
        <pattern id={`hp${hat | 0}`} width="9" height="9" patternUnits="userSpaceOnUse">
          <circle cx="2.5" cy="2.5" r="1.5" fill={`${mau}1F`} />
        </pattern>
      </defs>
      {rong && Ve
        ? <>
            {/* 31/8 — SÂN KHẤU CAO CỐ ĐỊNH THEO CHIỀU RỘNG, KHÔNG THEO CHIỀU CAO PANEL.
                Khung DATING APP cho ra một cái bàn tím treo giữa không khí và hai vật tròn lơ
                lửng; NEIGHBOR WATCH thì hàng rào cao tới cổ người. Cả hai cùng một gốc: mọi
                kích thước trong các hàm nền viết theo `h`, nên panel cao 800px thì cái bàn cao
                bằng cái bàn của panel 500px NHÂN 1,6 — đồ đạc phình theo khung.
                Đồ đạc trong một căn phòng không đổi kích thước khi máy quay lùi ra. Nên chiều
                cao "sân khấu" chốt theo chiều RỘNG panel (thứ tương ứng với bề ngang căn phòng),
                phần thừa phía trên là tường trơn — đúng như một khung hình cao chụp một căn
                phòng bình thường. */}
            <rect width={w} height={h} fill={nhat(mau, 0.84)} />
            {/* 31/8, khung dọc — SÂN KHẤU PHẢI CAO HƠN.
                Từ khi mỗi lượt chiếm trọn một khung 1080×1786, sân khấu cũ (cao bằng 62% bề
                ngang) chỉ với tới hai phần năm khung, và phần còn lại là một mảng tường trơn
                cao hơn nghìn pixel. Sân khấu nay lấy theo cả hai chiều, và phần tường phía trên
                được một đường trần cùng hai bóng đèn — đủ để mắt đọc ra "trên đầu vẫn là căn
                phòng ấy" thay vì đọc ra khoảng trống chưa vẽ. */}
            <g transform={`translate(${w * DICH[b]} ${h - hSK}) scale(${PHONG[b]})`}>
              <Ve w={w} h={hSK} mau={mau} mauPhu={mauPhu} hat={hat} rong={rong} />
            </g>
            {h - hSK > 120 && NGOAI_TROI[kenh] ? (
              // Ngoài trời thì phần trên là TRỜI, không phải trần. Khung NEIGHBOR WATCH vừa
              // rồi có hai bóng đèn treo lơ lửng giữa sân cỏ — một chi tiết vô lý đủ để người
              // xem mất tin vào cả cảnh. Cùng một khoảng trống, hai nơi chốn, hai cách lấp.
              <>
                {[0.24, 0.62].map((fx, i) => (
                  <g key={i} opacity={0.9}>
                    <circle cx={w * fx} cy={(h - hSK) * (0.34 + i * 0.2)} r={(h - hSK) * 0.11}
                            fill="#FFFFFF" stroke={MUC} strokeWidth={4} />
                    <circle cx={w * fx + (h - hSK) * 0.1} cy={(h - hSK) * (0.38 + i * 0.2)}
                            r={(h - hSK) * 0.085} fill="#FFFFFF" stroke={MUC} strokeWidth={4} />
                    <circle cx={w * fx - (h - hSK) * 0.09} cy={(h - hSK) * (0.39 + i * 0.2)}
                            r={(h - hSK) * 0.07} fill="#FFFFFF" stroke={MUC} strokeWidth={4} />
                  </g>
                ))}
              </>
            ) : h - hSK > 120 ? (
              <>
                <line x1={0} y1={(h - hSK) * 0.42} x2={w} y2={(h - hSK) * 0.42}
                      stroke={MUC} strokeWidth={4} opacity={0.28} />
                {[0.3, 0.7].map((fx, i) => (
                  <g key={i}>
                    <line x1={w * fx} y1={(h - hSK) * 0.42} x2={w * fx} y2={(h - hSK) * 0.62}
                          stroke={MUC} strokeWidth={3.5} opacity={0.5} />
                    <path d={`M${w * fx - 34} ${(h - hSK) * 0.62} L${w * fx + 34} ${(h - hSK) * 0.62}
                              L${w * fx + 22} ${(h - hSK) * 0.75} L${w * fx - 22} ${(h - hSK) * 0.75} Z`}
                          fill={nhat(mauPhu, 0.4)} stroke={MUC} strokeWidth={4} strokeLinejoin="round" />
                  </g>
                ))}
              </>
            ) : null}
          </>
        : <>
            {/* cận cảnh: chỉ mảng màu và vệt sáng chéo, giữ mắt ở khuôn mặt */}
            <rect width={w} height={h} fill={nhat(mau, 0.8)} />
            <path d={`M0 ${h} L${w * 0.55} 0 L${w} 0 L${w} ${h} Z`} fill={nhat(mauPhu, 0.72)} />
          </>}
      <rect width={w} height={h} fill={`url(#hp${hat | 0})`} />
    </svg>
  );
};
