import React from "react";
import { AbsoluteFill } from "remotion";
import { StickFigure, StickDefs } from "./StickFigure";

// 🏷️ BRAND chung cho INSIDE YOU (body) + HUH? (curiosity). Mỗi kênh palette + mascot riêng.
const CFG: Record<string, any> = {
  inside: { name: "INSIDE YOU", tagline: "The science of being you.", bg: "#F6E7DF", accent: "#E4562B", floor: "#B79E96" },
  huh: { name: "HUH?", tagline: "Ever wonder why?", bg: "#E9EFF5", accent: "#2D9CDB", floor: "#9AA6B0" },
};
const INK = "#161616";

const Heart: React.FC<{ beat?: number }> = ({ beat = 1 }) => (
  <g filter="url(#handdrawn)" transform={`scale(${beat})`}>
    <path d="M0,40 C-60,-20 -50,-70 -18,-70 C-4,-70 0,-56 0,-50 C0,-56 4,-70 18,-70 C50,-70 60,-20 0,40 Z" fill="#E4562B" stroke={INK} strokeWidth={7} />
    <path d="M-70,-30 L-40,-30 L-28,-52 L-14,-6 L0,-34 L70,-34" fill="none" stroke="#fff" strokeWidth={6} strokeLinecap="round" strokeLinejoin="round" />
  </g>
);
const Q: React.FC = () => (<g filter="url(#handdrawn)"><text x={0} y={44} textAnchor="middle" fontSize={170} fontWeight={900} fill="#2D9CDB" stroke={INK} strokeWidth={7} fontFamily="'Poppins',Arial" style={{ paintOrder: "stroke" } as any}>?</text></g>);

export const Brand: React.FC<{ ch: "inside" | "huh"; kind: "avatar" | "banner" }> = ({ ch, kind }) => {
  const c = CFG[ch];
  const Mascot = ch === "inside" ? <g transform="translate(150,470)"><Heart /></g> : <g transform="translate(150,430)"><Q /></g>;
  const figPose = ch === "inside" ? { brow: 0.6, mouth: "o", armR: 60, lookX: 0.5 } : { brow: 0.8, mouth: "neutral", armL: 70, armR: 10, lookX: 0.4, lookY: -0.3 };
  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: c.accent, fontFamily: "'Poppins',Arial" }}>
        <svg width={800} height={800} viewBox="0 0 800 800"><StickDefs />
          <circle cx={400} cy={400} r={360} fill={c.bg} stroke={INK} strokeWidth={14} filter="url(#handdrawn)" />
          <g transform="translate(330,470) scale(0.6)"><StickFigure {...figPose as any} live={false} /></g>
          <g transform="translate(360,360) scale(0.9)">{Mascot}</g>
        </svg>
        <div style={{ position: "absolute", bottom: 92, width: "100%", textAlign: "center" }}>
          <span style={{ fontSize: ch === "huh" ? 190 : 120, fontWeight: 900, color: c.accent, WebkitTextStroke: "10px #161616" as any }}>{c.name}</span>
        </div>
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{ background: c.bg, fontFamily: "'Poppins',Arial" }}>
      <svg width={2560} height={1440} viewBox="0 0 2560 1440"><StickDefs />
        <rect x={0} y={1180} width={2560} height={260} fill={c.floor} />
        <path d="M-20,1180 L2580,1176" stroke={INK} strokeWidth={8} fill="none" filter="url(#handdrawn)" />
        <g transform="translate(760,1140) scale(0.9)"><StickFigure {...figPose as any} live={false} /></g>
        <g transform="translate(1020,900) scale(1.5)">{Mascot}</g>
      </svg>
      <div style={{ position: "absolute", left: 0, right: 0, top: 470, textAlign: "center" }}>
        <div style={{ fontSize: ch === "huh" ? 300 : 200, fontWeight: 900, color: c.accent, WebkitTextStroke: "12px #161616" as any }}>{c.name}</div>
        <div style={{ fontSize: 62, fontWeight: 700, color: INK, marginTop: 10 }}>{c.tagline}</div>
      </div>
    </AbsoluteFill>
  );
};
