import React from "react";

// 🎨 Thư viện BỐI CẢNH vẽ tay đa dạng (đổi cảnh cho đỡ đơn điệu, đẹp & cuốn). Cùng tông hand-drawn.
const INK = "#161616";
export type BgVariant = "room" | "street" | "park" | "spot" | "night" | "card";

export const Scenery: React.FC<{ v: BgVariant; frame: number; bg: string; floor: string; accent: string }> = ({ v, frame, bg, floor, accent }) => {
  const sway = Math.sin(frame / 40) * 3;
  if (v === "street") return (
    <g>
      <rect x={-200} y={-300} width={2320} height={1210} fill="#BFE3F2" />
      <rect x={-200} y={905} width={2320} height={400} fill="#8C8C8C" />
      <g filter="url(#handdrawn)">
        {[[120, 420, 260, "#C98A6B"], [420, 300, 240, "#8FA9B8"], [1360, 340, 300, "#B58AA0"], [1680, 260, 320, "#7FA0A8"]].map((b, i) => (
          <g key={i}><rect x={b[0] as number} y={b[1] as number} width={b[2] as number} height={905 - (b[1] as number)} fill={b[3] as string} stroke={INK} strokeWidth={7} />
            {[0, 1, 2, 3].map((r) => [0, 1, 2].map((c) => <rect key={`${r}${c}`} x={(b[0] as number) + 24 + c * ((b[2] as number - 48) / 3)} y={(b[1] as number) + 30 + r * 90} width={30} height={44} fill="#F6E7B0" stroke={INK} strokeWidth={3} />))}
          </g>))}
        <path d="M-200,905 L2120,902" stroke={INK} strokeWidth={6} fill="none" />
        <path d="M700,940 L1220,940" stroke="#EEE" strokeWidth={6} strokeDasharray="40 40" />
      </g>
    </g>
  );
  if (v === "park") return (
    <g>
      <rect x={-200} y={-300} width={2320} height={1210} fill="#CFEBF5" />
      <rect x={-200} y={860} width={2320} height={450} fill="#9CC77A" />
      <g filter="url(#handdrawn)">
        <circle cx={300} cy={230} r={90} fill="#FCD34D" stroke={INK} strokeWidth={7} />
        <path d="M-200,860 Q500,790 1100,860 T2120,850" fill="#8FBF6A" stroke={INK} strokeWidth={6} />
        <g transform="translate(1520,860)"><rect x={-22} y={-180} width={44} height={180} fill="#8B5A2B" stroke={INK} strokeWidth={7} /><circle cx={0} cy={-230} r={130} fill="#79B85C" stroke={INK} strokeWidth={8} /></g>
      </g>
    </g>
  );
  if (v === "night") return (
    <g>
      <rect x={-200} y={-300} width={2320} height={1210} fill="#1C2140" />
      <rect x={-200} y={905} width={2320} height={400} fill="#12162E" />
      {Array.from({ length: 40 }).map((_, i) => <circle key={i} cx={(i * 137) % 2000 - 40} cy={(i * 91) % 800} r={2 + (i % 3)} fill="#FDE68A" opacity={0.4 + 0.4 * Math.sin(frame / 20 + i)} />)}
      <circle cx={1800} cy={120} r={56} fill="#F3ECFF" filter="url(#handdrawn)" />
      <path d="M-200,905 L2120,902" stroke="#3A4374" strokeWidth={6} fill="none" filter="url(#handdrawn)" />
    </g>
  );
  if (v === "card") return (
    <g>
      <rect x={-200} y={-300} width={2320} height={1210} fill={bg} />
      {/* quầng màu thương hiệu + tia nhẹ -> sạch, bắt mắt cho tiêu đề chương */}
      <ellipse cx={960} cy={340} rx={1200} ry={780} fill={accent} opacity={0.16} />
      {Array.from({ length: 22 }).map((_, i) => { const x = ((i * 173) % 1920); const y = ((i * 97) % 1000) + (Math.sin(frame / 20 + i) * 6); return <circle key={i} cx={x} cy={y} r={4 + (i % 3) * 2} fill={accent} opacity={0.18 + 0.12 * Math.sin(frame / 18 + i)} />; })}
      <rect x={-200} y={905} width={2320} height={400} fill={floor} />
      <path d="M-200,905 L2120,902" stroke={INK} strokeWidth={6} fill="none" filter="url(#handdrawn)" />
    </g>
  );
  if (v === "spot") return (
    <g>
      <rect x={-200} y={-300} width={2320} height={1210} fill={bg} />
      <ellipse cx={960} cy={620} rx={720} ry={520} fill="#fff" opacity={0.45} filter="url(#handdrawn)" />
      <rect x={-200} y={905} width={2320} height={400} fill={floor} />
      <path d="M-200,905 L2120,902" stroke={INK} strokeWidth={6} fill="none" filter="url(#handdrawn)" />
    </g>
  );
  // room (mặc định) — ấm cúng: cửa sổ + đèn + cây
  return (
    <g>
      <rect x={-200} y={-300} width={2320} height={1205} fill={bg} />
      <rect x={-200} y={905} width={2320} height={400} fill={floor} />
      <path d="M-200,905 L2120,902" stroke={INK} strokeWidth={6} fill="none" filter="url(#handdrawn)" />
      <g filter="url(#handdrawn)">
        <rect x={250} y={230} width={300} height={300} rx={8} fill="#BFE3F2" stroke={INK} strokeWidth={9} />
        <path d="M400,230 L400,530 M250,380 L550,380" stroke={INK} strokeWidth={6} />
        <g transform="translate(1560,905)"><path d="M0,0 L0,-360" stroke={INK} strokeWidth={7} /><path d="M-52,-360 L52,-360 L34,-440 L-34,-440 Z" fill={accent} stroke={INK} strokeWidth={7} /><ellipse cx={0} cy={-440} rx={40} ry={9} fill="#FDE68A" opacity={0.8} /></g>
        <g transform={`translate(1400,905) rotate(${sway * 0.3})`}><rect x={-40} y={-70} width={80} height={70} rx={10} fill="#C98A2E" stroke={INK} strokeWidth={7} /><path d="M0,-70 C-40,-180 -20,-220 0,-210 C20,-220 40,-180 0,-70" fill="#79B85C" stroke={INK} strokeWidth={6} /></g>
      </g>
    </g>
  );
};
