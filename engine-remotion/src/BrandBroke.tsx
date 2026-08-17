import React from "react";
import { AbsoluteFill } from "remotion";
import { StickFigure, StickDefs } from "./StickFigure";
import { Story } from "./Story";

// 🏷️ BRAND kênh "BROKE" (money) — stick-figure vẽ tay + ví rỗng + $ rơi. Xanh tiền + cream.
const GREEN = "#2FA84F", CREAM = "#F3E7C0", INK = "#161616", GOLD = "#D79A34";

const Wallet: React.FC = () => (
  <g filter="url(#handdrawn)">
    <path d="M-70,-30 L70,-30 L64,60 L-64,60 Z" fill="#8B5A2B" stroke={INK} strokeWidth={8} />
    <path d="M-70,-30 Q0,-64 70,-30" fill="#A56A34" stroke={INK} strokeWidth={8} />
    <rect x={20} y={0} width={40} height={28} rx={6} fill={GOLD} stroke={INK} strokeWidth={6} />
    {/* con nhậy bay ra (gag "rỗng túi") */}
    <path d="M-10,-70 q-14,-10 -26,-2 q14,4 26,2" fill="#cdbfae" stroke={INK} strokeWidth={4} />
  </g>
);
const Coin: React.FC<{ x: number; y: number; r?: number }> = ({ x, y, r = 30 }) => (
  <g filter="url(#handdrawn)" transform={`translate(${x},${y})`}>
    <circle r={r} fill={GOLD} stroke={INK} strokeWidth={7} />
    <text x={0} y={r * 0.42} textAnchor="middle" fontSize={r * 1.1} fontWeight={900} fill={INK} fontFamily="Georgia,serif">$</text>
  </g>
);

export const BrandBroke: React.FC<{ kind: "avatar" | "banner" | "thumb" }> = ({ kind }) => {
  if (kind === "thumb") {
    return (
      <AbsoluteFill style={{ background: "#FBE9A7", fontFamily: "'Poppins',Arial" }}>
        {/* tia hướng tâm tạo drama */}
        <svg width={1280} height={720} viewBox="0 0 1280 720" style={{ position: "absolute", inset: 0 }}>
          {Array.from({ length: 24 }).map((_, i) => { const a = (i / 24) * Math.PI * 2; return <path key={i} d={`M640,360 L${640 + Math.cos(a) * 1000},${360 + Math.sin(a) * 1000}`} stroke="#F6D96A" strokeWidth={40} opacity={i % 2 ? 0.5 : 0} />; })}
        </svg>
        <svg width={1280} height={720} viewBox="0 0 1280 720" style={{ position: "absolute", inset: 0 }}><StickDefs />
          <rect x={0} y={612} width={1280} height={108} fill="#9C9A93" />
          <path d="M-20,612 L1300,608" stroke={INK} strokeWidth={7} fill="none" filter="url(#handdrawn)" />
          {/* MŨI TÊN ĐỎ tăng vọt (drama) */}
          <g filter="url(#handdrawn)">
            <path d="M120,600 C300,560 360,300 560,120" stroke="#E4562B" strokeWidth={30} fill="none" strokeLinecap="round" />
            <path d="M470,150 L575,105 L540,215" fill="#E4562B" stroke="#161616" strokeWidth={6} strokeLinejoin="round" />
          </g>
          {/* NHÂN VẬT SỐC — to, 2 tay ôm đầu, mắt mở to, miệng há */}
          <g transform="translate(980,660) scale(0.92)"><Story brow={0.85} mouth="o" eyeWide={1.22} armL={158} armR={158} lookX={-0.35} lookY={-0.25} outfit="tie" shirt="#7FB0D8" tie="#1F7A3A" hair="#2A2038" hairStyle="short" /></g>
        </svg>
        {/* CHỮ tối giản, cực lớn */}
        <div style={{ position: "absolute", top: 250, left: 56, lineHeight: 0.92 }}>
          <div style={{ fontSize: 78, fontWeight: 900, color: "#161616" }}>WHY IS RENT</div>
          <div style={{ fontSize: 176, fontWeight: 900, color: "#FFD21E", WebkitTextStroke: "12px #161616" as any }}>SO HIGH?!</div>
        </div>
        {/* badge số sốc */}
        <div style={{ position: "absolute", top: 40, left: 70, background: "#E4562B", color: "#fff", fontSize: 52, fontWeight: 900, padding: "8px 22px", borderRadius: 14, border: "6px solid #161616", transform: "rotate(-6deg)", WebkitTextStroke: "1px #161616" as any }}>33% OF YOUR PAY 😱</div>
      </AbsoluteFill>
    );
  }
  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: GREEN, fontFamily: "'Poppins',Arial" }}>
        <svg width={800} height={800} viewBox="0 0 800 800"><StickDefs />
          <circle cx={400} cy={400} r={360} fill={CREAM} stroke={INK} strokeWidth={14} filter="url(#handdrawn)" />
          <g transform="translate(400,470) scale(0.62)"><StickFigure brow={-0.4} mouth="frown" armL={40} armR={70} lookY={0.4} /></g>
          <g transform="translate(560,470) scale(1.1)"><Wallet /></g>
          <Coin x={520} y={300} r={26} /><Coin x={300} y={330} r={22} />
        </svg>
        <div style={{ position: "absolute", bottom: 96, width: "100%", textAlign: "center" }}>
          <span style={{ fontSize: 150, fontWeight: 900, color: GREEN, WebkitTextStroke: "10px #161616" as any, letterSpacing: 2 }}>BROKE</span>
        </div>
      </AbsoluteFill>
    );
  }
  // banner 2560x1440 (safe zone giữa)
  return (
    <AbsoluteFill style={{ background: CREAM, fontFamily: "'Poppins',Arial" }}>
      <svg width={2560} height={1440} viewBox="0 0 2560 1440"><StickDefs />
        <rect x={0} y={1180} width={2560} height={260} fill="#9C9A93" />
        <path d="M-20,1180 L2580,1176" stroke={INK} strokeWidth={8} fill="none" filter="url(#handdrawn)" />
        <g transform="translate(720,1140) scale(0.9)"><StickFigure brow={-0.4} mouth="frown" armL={44} armR={78} lookX={0.6} lookY={0.3} /></g>
        <g transform="translate(980,980) scale(1.4)"><Wallet /></g>
        <Coin x={900} y={720} r={40} /><Coin x={1120} y={760} r={30} /><Coin x={1030} y={640} r={24} />
      </svg>
      <div style={{ position: "absolute", left: 0, right: 0, top: 470, textAlign: "center" }}>
        <div style={{ fontSize: 240, fontWeight: 900, color: GREEN, WebkitTextStroke: "12px #161616" as any, letterSpacing: 3 }}>BROKE</div>
        <div style={{ fontSize: 62, fontWeight: 700, color: INK, marginTop: 10 }}>Where your money really goes.</div>
      </div>
    </AbsoluteFill>
  );
};
