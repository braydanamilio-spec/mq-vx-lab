import React from "react";
import { LapNoi, LopGan, Noi, SAN } from "./NoiChon";

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

/** Hệ số nét: mỗi kênh một độ dày, tính quanh mốc 5 của bản vẽ gốc. */
let HE_NET = 1;

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
    {/* 31/8 — bỏ tấm bảng DELAYED ở đây. Từ khi khung dọc có thêm lớp TRẦN, sân bay đã có một
        bảng chỉ dẫn treo ở đúng vùng ấy, và hai tấm bảng đen chồng lên nhau che mất chữ của
        nhau. Một nơi chốn chỉ cần MỘT tấm bảng — cái treo trên trần đọc ra tự nhiên hơn. */}
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

// ══ ĐẠO CỤ ĐỌC RA TỪ CHÍNH LỜI THOẠI ═══════════════════════════════════════════════════
// Anh: *"e vẽ được bối cảnh liên quan tới lời thoại để người xem dễ hình dung chứ, có cần AI
// phân tích ko?"* — vẽ được, và KHÔNG cần AI.
//
// Lời thoại đã nằm sẵn trong tay dưới dạng văn bản. Việc cần làm chỉ là dò từ khoá rồi vẽ vật
// tương ứng từ một bộ vẽ có sẵn. Gọi mô hình để làm việc ấy vừa chậm, vừa tốn hạn mức, vừa
// không hứa gì về bố cục — đúng ba lý do đã khiến đường sinh ảnh nền của bản cũ phải bỏ.
//
// Bảng dưới đây là toàn bộ "phân tích": từ khoá -> vật. Thứ tự có ý nghĩa — mục đứng trước
// thắng, nên câu vừa có "phone" vừa có "bill" thì vẽ điện thoại (thứ nhân vật đang cầm) chứ
// không vẽ hoá đơn. Vật đặt ở mép dưới-phải, chỗ mà cả bong bóng lẫn nhân vật đều không dùng.
const TU_KHOA: [RegExp, string][] = [
  [/\b(phone|scroll|text|app|call|texting)\b/i, "dien_thoai"],
  [/\b(router|wi-?fi|internet|modem|signal|reboot|reset)\b/i, "router"],
  [/\b(invoice|bill|charge|paid|dollars?|refund|fee|rent)\b/i, "giay"],
  [/\b(box|boxes|package|deliver|parcel)\b/i, "thung"],
  [/\b(tire|engine|car|brake|oil|garage)\b/i, "lop_xe"],
  [/\b(homework|school|class|teacher|book|study|essay|grade)\b/i, "sach"],
  [/\b(coffee|cup|mug|drink|latte)\b/i, "coc"],
  [/\b(laptop|computer|keyboard|monitor|screen|desktop|boot|reboot|crash)\b/i, "may_tinh"],
  [/\b(sugar|snack|calorie|diet|eat|food|fridge)\b/i, "hop_do_an"],
  [/\b(gym|weight|workout|rep|treadmill|cardio)\b/i, "ta_tay"],
  [/\b(bag|luggage|suitcase|gate|flight|boarding)\b/i, "vali"],
];

export const doDaoCu = (cau: string): string => {
  for (const [re, ten] of TU_KHOA) if (re.test(cau)) return ten;
  return "";
};

/** Vẽ một đạo cụ ở mép dưới-phải panel. Nhỏ, đứng trên sàn, không tranh chỗ với ai. */
export const DaoCu: React.FC<{ ten: string; w: number; h: number; mau: string; mauPhu: string; hai?: boolean }> =
({ ten, w, h, mau, mauPhu, hai }) => {
  if (!ten) return null;
  // 31/8 — CHỖ TRỐNG THẬT LÀ KHOẢNG GIỮA HAI NGƯỜI, KHÔNG PHẢI MÉP PHẢI.
  // Bản đầu đặt đạo cụ ở mép dưới-phải và khung ra gần như không thấy nó: mép phải là chỗ của
  // tủ, của kệ, và của chính người thứ hai. Hai nhân vật đứng ở 28% và 72% bề ngang, nên dải
  // giữa mới là khoảng duy nhất chắc chắn trống trong mọi cảnh hai người. Cận cảnh thì ngược
  // lại — người đứng giữa, nên vật lùi ra mép.
  const S = Math.min(w, h) * (hai ? 0.17 : 0.15);   // đã theo cạnh NGẮN — đúng
  const x = hai ? w * 0.5 : w * 0.86;
  const y = h * (hai ? SAN : SAN - 0.05);   // cận cảnh thì vật lùi ra mép, cao hơn chút
  const G = (el: React.ReactNode) => (
    <g transform={`translate(${x} ${y})`} stroke={MUC} strokeWidth={4.5} strokeLinejoin="round">{el}</g>
  );
  if (ten === "dien_thoai") return G(<>
    <rect x={-S * 0.28} y={-S} width={S * 0.56} height={S} rx={S * 0.1} fill={MUC} />
    <rect x={-S * 0.21} y={-S * 0.9} width={S * 0.42} height={S * 0.72} fill={nhat(mauPhu, 0.35)} strokeWidth={0} />
  </>);
  if (ten === "router") return G(<>
    <rect x={-S * 0.5} y={-S * 0.5} width={S} height={S * 0.5} rx={4} fill={nhat(mau, 0.5)} />
    <line x1={-S * 0.3} y1={-S * 0.5} x2={-S * 0.42} y2={-S} />
    <line x1={S * 0.2} y1={-S * 0.5} x2={S * 0.34} y2={-S} />
    <circle cx={-S * 0.2} cy={-S * 0.25} r={3.5} fill={mauPhu} strokeWidth={0} />
    <circle cx={0} cy={-S * 0.25} r={3.5} fill={mauPhu} strokeWidth={0} />
  </>);
  if (ten === "giay") return G(
    <path d={`M${-S * 0.38} ${-S} L${S * 0.38} ${-S * 0.92} L${S * 0.32} 0 L${-S * 0.42} ${-S * 0.06} Z`}
          fill="#FFFFFF" />);
  if (ten === "thung") return G(<>
    <rect x={-S * 0.5} y={-S * 0.78} width={S} height={S * 0.78} fill={nhat(mau, 0.45)} />
    <line x1={-S * 0.5} y1={-S * 0.5} x2={S * 0.5} y2={-S * 0.5} />
  </>);
  if (ten === "lop_xe") return G(<>
    <circle cx={0} cy={-S * 0.45} r={S * 0.45} fill={MUC} />
    <circle cx={0} cy={-S * 0.45} r={S * 0.2} fill={nhat(mau, 0.6)} />
  </>);
  if (ten === "sach") return G(<>
    <rect x={-S * 0.45} y={-S * 0.32} width={S * 0.9} height={S * 0.32} fill={nhat(mauPhu, 0.4)} />
    <rect x={-S * 0.4} y={-S * 0.6} width={S * 0.9} height={S * 0.3} fill={nhat(mau, 0.4)} />
  </>);
  if (ten === "coc") return G(<>
    <path d={`M${-S * 0.3} ${-S * 0.6} L${S * 0.3} ${-S * 0.6} L${S * 0.22} 0 L${-S * 0.22} 0 Z`}
          fill="#FFFFFF" />
    <path d={`M${S * 0.3} ${-S * 0.5} q ${S * 0.22} ${S * 0.1} 0 ${S * 0.3}`} fill="none" />
  </>);
  if (ten === "may_tinh") return G(<>
    <path d={`M${-S * 0.5} 0 L${-S * 0.4} ${-S * 0.6} L${S * 0.4} ${-S * 0.6} L${S * 0.5} 0 Z`}
          fill={nhat(mau, 0.5)} />
    <rect x={-S * 0.36} y={-S * 0.56} width={S * 0.72} height={S * 0.42} fill={MUC} strokeWidth={0} />
  </>);
  if (ten === "hop_do_an") return G(<>
    <rect x={-S * 0.45} y={-S * 0.55} width={S * 0.9} height={S * 0.55} rx={4} fill={nhat(mauPhu, 0.35)} />
    <rect x={-S * 0.5} y={-S * 0.68} width={S} height={S * 0.16} rx={3} fill={nhat(mau, 0.35)} />
  </>);
  if (ten === "ta_tay") return G(<>
    <circle cx={-S * 0.34} cy={-S * 0.3} r={S * 0.26} fill={MUC} />
    <circle cx={S * 0.34} cy={-S * 0.3} r={S * 0.26} fill={MUC} />
    <rect x={-S * 0.3} y={-S * 0.4} width={S * 0.6} height={S * 0.2} fill={nhat(mau, 0.5)} />
  </>);
  if (ten === "vali") return G(<>
    <rect x={-S * 0.44} y={-S * 0.7} width={S * 0.88} height={S * 0.7} rx={5} fill={nhat(mauPhu, 0.4)} />
    <path d={`M${-S * 0.14} ${-S * 0.7} l0 ${-S * 0.24} l${S * 0.28} 0 l0 ${S * 0.24}`} fill="none" />
  </>);
  return null;
};

/**
 * TRẦN — phần tường phía trên sân khấu, trong khung dọc.
 *
 * 31/8, sửa ngay sau khi dựng đủ mười kênh: bản trước lấp khoảng ấy bằng ĐÚNG MỘT hình — một
 * đường trần và hai bóng đèn hình thang — cho cả mười kênh. Xếp mười khung cạnh nhau thì hai
 * cái đèn giống hệt nhau ở cùng một toạ độ là thứ đập vào mắt trước cả màu sắc, và nó phá đúng
 * cái việc mà cả buổi đang làm: cho mười kênh mười nét riêng.
 *
 * Bài học nhỏ mà đắt: **một chi tiết dùng chung cho mọi kênh thì mạnh hơn mười chi tiết riêng
 * cộng lại** — mắt bắt cái lặp trước, và cái lặp xoá cảm giác riêng của mọi thứ còn lại.
 * Trần nay đi theo nơi chốn: đèn tuýp cho văn phòng, quạt trần cho phòng khách, xà thép cho
 * gara, tủ treo cho bếp, bảng chỉ dẫn cho sân bay, trời mây cho ngoài sân.
 */
const Tran: React.FC<{ kenh: string; w: number; H: number; mau: string; mauPhu: string }> =
({ kenh, w, H, mau, mauPhu }) => {
  const y = H * 0.42;
  const D = (n: number) => H * n;

  if (kenh === "neighborwatch") {          // ngoài trời: mây
    return (<>
      {[0.24, 0.62].map((fx, i) => (
        <g key={i} opacity={0.9}>
          <circle cx={w * fx} cy={D(0.34 + i * 0.2)} r={D(0.11)} fill="#FFFFFF" stroke={MUC} strokeWidth={4} />
          <circle cx={w * fx + D(0.1)} cy={D(0.38 + i * 0.2)} r={D(0.085)} fill="#FFFFFF" stroke={MUC} strokeWidth={4} />
          <circle cx={w * fx - D(0.09)} cy={D(0.39 + i * 0.2)} r={D(0.07)} fill="#FFFFFF" stroke={MUC} strokeWidth={4} />
        </g>
      ))}
    </>);
  }

  if (kenh === "officesmalltalk" || kenh === "techsupport") {   // đèn tuýp văn phòng
    return (<>
      <line x1={0} y1={y} x2={w} y2={y} stroke={MUC} strokeWidth={4} opacity={0.25} />
      {[0.18, 0.58].map((fx, i) => (
        <rect key={i} x={w * fx} y={D(0.52 + i * 0.16)} width={w * 0.26} height={D(0.075)} rx={3}
              fill="#FFFFFF" stroke={MUC} strokeWidth={4} opacity={0.92} />
      ))}
    </>);
  }

  if (kenh === "carguy" || kenh === "gymlies") {                // xà thép + đèn chao công nghiệp
    return (<>
      <rect x={0} y={y} width={w} height={D(0.075)} fill={nhat(mau, 0.55)} stroke={MUC} strokeWidth={4} />
      {[0.28, 0.68].map((fx, i) => (
        <g key={i}>
          <line x1={w * fx} y1={y + D(0.075)} x2={w * fx} y2={D(0.66)} stroke={MUC} strokeWidth={4} />
          <path d={`M${w * fx - D(0.13)} ${D(0.78)} Q ${w * fx} ${D(0.6)} ${w * fx + D(0.13)} ${D(0.78)} Z`}
                fill={nhat(mauPhu, 0.4)} stroke={MUC} strokeWidth={4} />
        </g>
      ))}
    </>);
  }

  if (kenh === "parentmode") {                                  // quạt trần
    // Bản trước vẽ hai cánh đối xứng quanh một trục, và ở cỡ nhỏ nó đọc ra là cái NƠ BƯỚM chứ
    // không ra quạt. Quạt cần BỐN cánh lệch pha và một bầu tròn ở giữa — bốn cánh mới cho ra
    // cảm giác quay.
    return (<>
      <line x1={w * 0.5} y1={0} x2={w * 0.5} y2={D(0.4)} stroke={MUC} strokeWidth={5} />
      {[0, 1, 2, 3].map((i) => {
        const g = (i * Math.PI) / 2 + 0.4;
        const dx = Math.cos(g), dy = Math.sin(g) * 0.34;
        return <ellipse key={i} cx={w * 0.5 + dx * D(0.3)} cy={D(0.48) + dy * D(0.3)}
                        rx={D(0.22)} ry={D(0.07)} fill={nhat(mauPhu, 0.45)}
                        stroke={MUC} strokeWidth={4}
                        transform={`rotate(${(g * 180) / Math.PI * 0.25} ${w * 0.5} ${D(0.48)})`} />;
      })}
      <circle cx={w * 0.5} cy={D(0.48)} r={D(0.09)} fill={nhat(mau, 0.35)} stroke={MUC} strokeWidth={5} />
    </>);
  }

  if (kenh === "dietwars") {                                    // tủ bếp treo
    return (<>
      <rect x={w * 0.04} y={D(0.3)} width={w * 0.4} height={D(0.55)} fill={nhat(mau, 0.55)}
            stroke={MUC} strokeWidth={5} />
      <line x1={w * 0.24} y1={D(0.3)} x2={w * 0.24} y2={D(0.85)} stroke={MUC} strokeWidth={4} />
      <rect x={w * 0.6} y={D(0.36)} width={w * 0.34} height={D(0.42)} fill={nhat(mau, 0.68)}
            stroke={MUC} strokeWidth={5} />
    </>);
  }

  if (kenh === "airporthell") {                                 // bảng chỉ dẫn treo
    return (<>
      <line x1={w * 0.2} y1={0} x2={w * 0.2} y2={D(0.36)} stroke={MUC} strokeWidth={4} />
      <line x1={w * 0.8} y1={0} x2={w * 0.8} y2={D(0.36)} stroke={MUC} strokeWidth={4} />
      <rect x={w * 0.14} y={D(0.36)} width={w * 0.72} height={D(0.34)} rx={4}
            fill={MUC} stroke={MUC} strokeWidth={4} />
      {[0.2, 0.45, 0.7].map((fx, i) => (
        <rect key={i} x={w * (fx)} y={D(0.46)} width={w * 0.14} height={D(0.12)} rx={2}
              fill={i === 1 ? mauPhu : "#FFFFFF"} opacity={0.85} />
      ))}
    </>);
  }

  if (kenh === "datingapp") {                                   // đèn thả bàn + dây đèn nháy
    return (<>
      <path d={`M0 ${D(0.2)} Q ${w * 0.5} ${D(0.42)} ${w} ${D(0.2)}`} fill="none"
            stroke={MUC} strokeWidth={4} />
      {[0.16, 0.34, 0.5, 0.66, 0.84].map((fx, i) => (
        <circle key={i} cx={w * fx} cy={D(0.26 + Math.sin(fx * 3.14) * 0.12)} r={D(0.05)}
                fill={nhat(mauPhu, 0.3)} stroke={MUC} strokeWidth={3.5} />
      ))}
      {[0.3, 0.7].map((fx, i) => (
        <g key={i}>
          <line x1={w * fx} y1={D(0.5)} x2={w * fx} y2={D(0.66)} stroke={MUC} strokeWidth={3.5} />
          <path d={`M${w * fx - D(0.1)} ${D(0.8)} L${w * fx + D(0.1)} ${D(0.8)}
                    L${w * fx + D(0.06)} ${D(0.66)} L${w * fx - D(0.06)} ${D(0.66)} Z`}
                fill={nhat(mau, 0.35)} stroke={MUC} strokeWidth={4} strokeLinejoin="round" />
        </g>
      ))}
    </>);
  }

  // rentpanic và mặc định: hành lang — đèn ốp trần tròn, đều đặn như chung cư
  return (<>
    <line x1={0} y1={y} x2={w} y2={y} stroke={MUC} strokeWidth={4} opacity={0.3} />
    {[0.22, 0.5, 0.78].map((fx, i) => (
      <circle key={i} cx={w * fx} cy={D(0.62)} r={D(0.1)} fill="#FFFFFF"
              stroke={MUC} strokeWidth={4} opacity={0.9} />
    ))}
  </>);
};

/**
 * Nền của một panel.
 *
 * Panel CẬN (rong=false) chỉ vẽ mảng màu + halftone: ở cỡ cận, khung chỉ còn đầu và vai, nên
 * mọi đồ đạc đều rơi ra ngoài mép. Vẽ chúng vào chỉ tạo ra những mẩu hình khó hiểu sau lưng
 * nhân vật — đúng lỗi "cái giỏ giặt chắn ngang bụng" của bản cũ, chỉ khác nguồn.
 */
/** Lớp GẦN — dùng riêng, vẽ SAU nhân vật. Xem ghi chú ở `LopGan`. */
export const NenGan: React.FC<{
  noi: Noi; w: number; h: number; mau: string; mauPhu: string; rong: boolean;
}> = ({ noi, w, h, mau, mauPhu, rong }) => (
  rong ? (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}
         style={{ position: "absolute", inset: 0, zIndex: 4, pointerEvents: "none" }}>
      <LopGan noi={noi} w={w} h={h} mau={mau} mauPhu={mauPhu} />
    </svg>
  ) : null
);

export const NenPanel: React.FC<{
  kenh: string; noi: Noi; w: number; h: number; mau: string; mauPhu: string; hat: number;
  rong: boolean; bien?: number; net?: number; cham?: number;
}> = ({ kenh, noi, w, h, mau, mauPhu, hat, rong, bien = 0, net = 5, cham = 9 }) => {
  // 31/8 — MỖI PANEL MỘT GÓC NHÌN KHÁC. Khung thử cho ra sáu panel với cùng cái màn hình ở
  // cùng một chỗ, và sáu lần lặp lại một hình trong hai mươi giây thì mắt đọc ra là ảnh dán,
  // không phải là sáu ô truyện tranh. Cùng một căn phòng nhìn từ ba chỗ đứng vẫn là một căn
  // phòng — chỉ là máy đã dịch đi, đúng như một hoạ sĩ truyện tranh vẽ trang của mình.
  const DICH = [-0.20, 0.02, 0.16], PHONG = [1.18, 1.0, 1.10];
  const b = ((bien % 3) + 3) % 3;
  HE_NET = Math.max(0.7, Math.min(1.5, net / 6));
  const hSK = Math.min(h, Math.max(w * 0.62, Math.min(h * 0.74, w * 1.2)));   // chiều cao sân khấu
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}
         style={{ position: "absolute", inset: 0, zIndex: 1 }}>
      <defs>
        {/* Cỡ chấm halftone là một trong bốn trục tạo nét riêng của kênh: chấm mịn cho ra cảm
            giác in đẹp, chấm thô cho ra cảm giác báo giấy rẻ tiền. Cùng một bức vẽ, hai chất. */}
        <pattern id={`hp${hat | 0}`} width={cham} height={cham} patternUnits="userSpaceOnUse">
          <circle cx={cham * 0.28} cy={cham * 0.28} r={cham * 0.17} fill={`${mau}1F`} />
        </pattern>
      </defs>
      {/* 31/8 — CẬN CẢNH CŨNG VẼ BỐI CẢNH ĐẦY ĐỦ.
          Đo trên khung dọc 992px: cảnh HAI người để hở đúng 64px ở giữa, nên vật lớn đặt đâu
          cũng bị che 85% — không cách nào đọc ra chỗ nào. Nhưng cảnh CẬN chỉ có một người ở
          giữa, hở 286px mỗi bên: thừa chỗ cho một vật lớn.
          Vậy mà bản trước vẽ nền PHẲNG ở đúng cảnh cận — bỏ phí chỗ duy nhất còn chỗ, rồi cố
          nhồi vật lớn vào chỗ không còn chỗ. Đảo lại: cận cảnh mới là nơi khoe bối cảnh. */}
      {true ? (
        <>
          {/* 31/8 — BỐI CẢNH NAY LẮP TỪ MÔ-ĐUN, KHÔNG CÒN MỖI KÊNH MỘT HÀM VẼ.
              Mười kênh × một nơi chốn là thứ bó tay cả người viết kịch bản lẫn mắt người xem:
              ba mươi tập ở cùng một góc phòng thì dù thoại khác nhau, mắt vẫn đọc ra là một.
              Nay mỗi kênh có mười nơi có tên cộng với số nơi sinh tổ hợp không giới hạn — xem
              `NoiChon.tsx`. Cả hệ nặng 30 KB, so với 104 GB ảnh nền của bản cũ. */}
          {/* 31/8 — NỀN VÀ NGƯỜI PHẢI ĐỨNG CHUNG MỘT MẶT SÀN.
              Khung thử đầu cho ra đồ đạc bé và chìm: sân khấu cũ cao bằng 62–74% khung nên
              đường sàn của NỀN nằm ở 1500px trong khi chân nhân vật ở 1697px — đồ đạc lơ lửng
              trên lưng chừng, và vì sân khấu ngắn nên mọi mảnh cũng bị co lại theo.
              Nay nền vẽ trên TOÀN khung với đường sàn ngay dưới chân người. Trần vẫn vẽ đè lên
              phần tường phía trên, nên khoảng trống ở đỉnh vẫn được lấp. */}
          <g transform={`translate(${w * DICH[b]} 0) scale(${PHONG[b]})`}>
            <LapNoi noi={noi} w={w} h={h} mau={mau} mauPhu={mauPhu} net={net} />
          </g>
          <Tran kenh={noi.ngoai ? "neighborwatch" : kenh} w={w} H={h * 0.3}
                mau={mau} mauPhu={mauPhu} />
        </>
      ) : (
        <>
          {/* cận cảnh: chỉ mảng màu và vệt sáng chéo, giữ mắt ở khuôn mặt */}
          <rect width={w} height={h} fill={nhat(mau, 0.8)} />
          <path d={`M0 ${h} L${w * 0.55} 0 L${w} 0 L${w} ${h} Z`} fill={nhat(mauPhu, 0.72)} />
        </>
      )}
      <rect width={w} height={h} fill={`url(#hp${hat | 0})`} />
    </svg>
  );
};
