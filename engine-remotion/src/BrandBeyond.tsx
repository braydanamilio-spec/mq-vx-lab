import React from "react";
import { AbsoluteFill } from "remotion";

// 🌌 BRAND cho BEYOND — vũ trụ điện ảnh: nền space, sao, hành tinh phát sáng + quỹ đạo, "BEYOND" glow, timeline tinh tế (moat cinematic+data).
const stars = (n: number, w: number, h: number) =>
  Array.from({ length: n }).map((_, i) => ({
    x: (i * 733 % w), y: (i * 419 % h), r: (i % 5 === 0 ? 2.6 : 1.3), o: 0.15 + (i % 7) / 12,
  }));

const Defs: React.FC = () => (
  <defs>
    <radialGradient id="bybg" cx="50%" cy="40%" r="80%">
      <stop offset="0%" stopColor="#0C1A33" />
      <stop offset="55%" stopColor="#060B18" />
      <stop offset="100%" stopColor="#02030A" />
    </radialGradient>
    <radialGradient id="byplanet" cx="38%" cy="32%" r="75%">
      <stop offset="0%" stopColor="#5EE7FF" />
      <stop offset="45%" stopColor="#2A7FD4" />
      <stop offset="100%" stopColor="#101C3A" />
    </radialGradient>
    <linearGradient id="byring" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stopColor="#F5B301" /><stop offset="100%" stopColor="#22D3EE" />
    </linearGradient>
    <filter id="byglow" x="-70%" y="-70%" width="240%" height="240%">
      <feGaussianBlur stdDeviation="16" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
    </filter>
    <filter id="bysoft"><feGaussianBlur stdDeviation="34" /></filter>
  </defs>
);

const Planet: React.FC<{ cx: number; cy: number; r: number }> = ({ cx, cy, r }) => (
  <g>
    <circle cx={cx} cy={cy} r={r * 1.25} fill="#22D3EE" opacity={0.18} filter="url(#bysoft)" />
    <ellipse cx={cx} cy={cy} rx={r * 1.7} ry={r * 0.42} fill="none" stroke="url(#byring)" strokeWidth={r * 0.05} opacity={0.85} transform={`rotate(-18 ${cx} ${cy})`} filter="url(#byglow)" />
    <circle cx={cx} cy={cy} r={r} fill="url(#byplanet)" />
    <circle cx={cx - r * 0.35} cy={cy - r * 0.38} r={r * 0.9} fill="#EAF8FF" opacity={0.12} />
  </g>
);

export const BrandBeyond: React.FC<{ kind: "avatar" | "banner" }> = ({ kind }) => {
  if (kind === "avatar") {
    const S = 800;
    return (
      <AbsoluteFill style={{ fontFamily: "'Poppins',Arial" }}>
        <svg width={S} height={S} viewBox="0 0 800 800"><Defs />
          <circle cx={400} cy={400} r={400} fill="url(#bybg)" />
          {stars(70, 800, 800).map((s, i) => <circle key={i} cx={s.x} cy={s.y} r={s.r} fill="#fff" opacity={s.o} />)}
          <circle cx={400} cy={400} r={384} fill="none" stroke="url(#byring)" strokeWidth={14} opacity={0.85} />
          <Planet cx={400} cy={330} r={150} />
          <text x={400} y={640} textAnchor="middle" fontSize={150} fontWeight={900} fill="#EAF8FF" letterSpacing={2} fontFamily="'Poppins',Arial" style={{ filter: "drop-shadow(0 0 22px rgba(34,211,238,0.6))" }}>BEYOND</text>
        </svg>
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{ fontFamily: "'Poppins',Arial" }}>
      <svg width={2560} height={1440} viewBox="0 0 2560 1440"><Defs />
        <rect width={2560} height={1440} fill="url(#bybg)" />
        {stars(150, 2560, 1440).map((s, i) => <circle key={i} cx={s.x} cy={s.y} r={s.r} fill="#fff" opacity={s.o} />)}
        <Planet cx={2230} cy={410} r={210} />
        {/* timeline tinh tế = moat data */}
        <line x1={560} y1={1020} x2={2000} y2={1020} stroke="#22D3EE" strokeWidth={3} opacity={0.35} />
        {[0, 1, 2, 3, 4].map((k) => <circle key={k} cx={560 + k * 360} cy={1020} r={k === 4 ? 12 : 6} fill={k === 4 ? "#F5B301" : "#22D3EE"} opacity={0.9} filter={k === 4 ? "url(#byglow)" : undefined} />)}
        <text x={1160} y={620} textAnchor="middle" fontSize={310} fontWeight={900} fill="#EAF8FF" letterSpacing={16} fontFamily="'Poppins',Arial" style={{ filter: "drop-shadow(0 0 34px rgba(34,211,238,0.55))" }}>BEYOND</text>
        <text x={1160} y={730} textAnchor="middle" fontSize={58} fontWeight={600} fill="#8FB6D8" letterSpacing={10} fontFamily="'Poppins',Arial">THE UNIVERSE, ON A TIMELINE</text>
      </svg>
    </AbsoluteFill>
  );
};
