import React from "react";
import { AbsoluteFill } from "remotion";

// 🏆 BRAND cho RANKED — data-viz cao cấp: nền gradient tối, cột phát sáng, mũi tên tăng trưởng, #1 vàng.
const BARS = [
  { c0: "#6D4AF0", c1: "#A78BFA" }, // violet
  { c0: "#0EA5C9", c1: "#67E8F9" }, // cyan
  { c0: "#1FB07A", c1: "#6EE7B7" }, // green
  { c0: "#E86A6A", c1: "#FCA5A5" }, // coral
  { c0: "#3B82F6", c1: "#93C5FD" }, // blue
  { c0: "#E0A008", c1: "#FCD34D" }, // gold (tallest)
];

const Defs: React.FC = () => (
  <defs>
    <radialGradient id="rkbg" cx="50%" cy="38%" r="75%">
      <stop offset="0%" stopColor="#1B2A4A" />
      <stop offset="55%" stopColor="#0E1730" />
      <stop offset="100%" stopColor="#060A14" />
    </radialGradient>
    {BARS.map((b, i) => (
      <linearGradient key={i} id={`rkbar${i}`} x1="0" y1="1" x2="0" y2="0">
        <stop offset="0%" stopColor={b.c0} />
        <stop offset="100%" stopColor={b.c1} />
      </linearGradient>
    ))}
    <linearGradient id="rkgold" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stopColor="#FDE68A" />
      <stop offset="100%" stopColor="#F59E0B" />
    </linearGradient>
    <filter id="rkglow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="14" result="b" />
      <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
    </filter>
    <filter id="rksoft" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="26" />
    </filter>
  </defs>
);

// Vẽ cụm cột + lưới mờ + mũi tên vàng + #1. cx = tâm ngang, base = đáy, sc = tỉ lệ.
const Bars: React.FC<{ cx: number; base: number; bw: number; gap: number; heights: number[]; badge?: boolean }> = ({ cx, base, bw, gap, heights, badge }) => {
  const n = heights.length;
  const total = n * bw + (n - 1) * gap;
  const x0 = cx - total / 2;
  const tops = heights.map((h) => base - h);
  const cxs = heights.map((_, i) => x0 + i * (bw + gap) + bw / 2);
  const arrow = cxs.map((x, i) => `${x},${tops[i] - 26}`).join(" ");
  const lastX = cxs[n - 1], lastTop = tops[n - 1];
  return (
    <g>
      {/* lưới mờ */}
      {[0, 1, 2, 3].map((k) => (
        <line key={k} x1={x0 - 40} y1={base - (k * (base - Math.min(...tops) + 30)) / 3} x2={x0 + total + 40} y2={base - (k * (base - Math.min(...tops) + 30)) / 3} stroke="#5B6B8C" strokeWidth={2} opacity={0.12} />
      ))}
      {/* glow nền cột */}
      <g filter="url(#rksoft)" opacity={0.5}>
        {heights.map((h, i) => (<rect key={i} x={cxs[i] - bw / 2} y={tops[i]} width={bw} height={h} rx={bw / 2.4} fill={BARS[i].c1} />))}
      </g>
      {/* cột chính */}
      {heights.map((h, i) => (
        <rect key={i} x={cxs[i] - bw / 2} y={tops[i]} width={bw} height={h} rx={Math.min(18, bw / 3)} fill={`url(#rkbar${i})`} />
      ))}
      {/* mũi tên tăng trưởng */}
      <polyline points={arrow} fill="none" stroke="url(#rkgold)" strokeWidth={Math.max(6, bw / 9)} strokeLinecap="round" strokeLinejoin="round" filter="url(#rkglow)" />
      <polygon points={`${lastX - 4},${lastTop - 26} ${lastX + bw / 1.5},${lastTop - 26 - bw / 3.2} ${lastX + bw / 1.5},${lastTop - 26 + bw / 3.2}`} fill="#FBBF24" filter="url(#rkglow)" />
      {badge && (
        <g transform={`translate(${lastX},${lastTop - bw * 1.15})`}>
          <circle r={bw * 0.55} fill="url(#rkgold)" filter="url(#rkglow)" />
          <text y={bw * 0.2} textAnchor="middle" fontSize={bw * 0.72} fontWeight={900} fill="#3A2600" fontFamily="'Poppins',Arial">1</text>
        </g>
      )}
    </g>
  );
};

export const BrandRanked: React.FC<{ kind: "avatar" | "banner" }> = ({ kind }) => {
  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ fontFamily: "'Poppins',Arial" }}>
        <svg width={800} height={800} viewBox="0 0 800 800">
          <Defs />
          <circle cx={400} cy={400} r={400} fill="url(#rkbg)" />
          <circle cx={400} cy={400} r={384} fill="none" stroke="url(#rkgold)" strokeWidth={16} opacity={0.9} />
          <Bars cx={400} base={545} bw={70} gap={26} heights={[120, 175, 235, 300, 360]} badge />
          <text x={400} y={690} textAnchor="middle" fontSize={132} fontWeight={900} fill="#EAF2FF" letterSpacing={2} fontFamily="'Poppins',Arial" style={{ filter: "drop-shadow(0 0 18px rgba(124,92,255,0.45))" }}>RANKED</text>
        </svg>
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{ fontFamily: "'Poppins',Arial" }}>
      <svg width={2560} height={1440} viewBox="0 0 2560 1440">
        <Defs />
        <rect width={2560} height={1440} fill="url(#rkbg)" />
        {/* hero: chữ ở vùng an toàn giữa, cột + mũi tên bên dưới */}
        <text x={1280} y={540} textAnchor="middle" fontSize={300} fontWeight={900} fill="#EAF2FF" letterSpacing={14} fontFamily="'Poppins',Arial" style={{ filter: "drop-shadow(0 0 30px rgba(124,92,255,0.5))" }}>RANKED</text>
        <text x={1280} y={648} textAnchor="middle" fontSize={60} fontWeight={600} fill="#9FB2D4" letterSpacing={8} fontFamily="'Poppins',Arial">WATCH THE NUMBERS RACE</text>
        <Bars cx={1280} base={1215} bw={92} gap={34} heights={[95, 130, 170, 225, 285, 340]} badge />
      </svg>
    </AbsoluteFill>
  );
};
