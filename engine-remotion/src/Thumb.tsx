import React from "react";
import { AbsoluteFill } from "remotion";
import { StickDefs } from "./StickFigure";
import { Story } from "./Story";

// 🖼️ THUMBNAIL 1280x720 data-driven — mỗi video 1 thumb riêng, đúng persona + hook. CTR cao.
const INK = "#161616";
export type ThumbProps = {
  topLine?: string;    // dòng nhỏ trên
  bigLine?: string;    // dòng CHỮ TO (vàng viền đen)
  badge?: string;      // badge số sốc (góc trên trái)
  bg?: string;         // nền tia
  accent?: string;     // màu tia
  floor?: string;
  handle?: string;
  persona?: any;       // outfit/shirt/tie/hair/hairStyle/glasses/skin
  brow?: number; eyeWide?: number; mouth?: string;
  motif?: "arrow" | "none";
  badgeBg?: string;
};

export const calcThumb = () => ({ width: 1280, height: 720 });

export const Thumb: React.FC<ThumbProps> = ({
  topLine = "", bigLine = "", badge = "", bg = "#FBE9A7", accent = "#F6D96A",
  floor = "#9C9A93", handle = "", persona = {}, brow = 0.85, eyeWide = 1.22,
  mouth = "o", motif = "arrow", badgeBg = "#E4562B",
}) => {
  // auto-fit dòng chữ to theo độ dài
  const big = (bigLine || "").toUpperCase();
  const bigFs = big.length <= 8 ? 176 : big.length <= 13 ? 138 : big.length <= 18 ? 112 : 92;
  return (
    <AbsoluteFill style={{ background: bg, fontFamily: "'Poppins',Arial" }}>
      {/* tia hướng tâm tạo drama */}
      <svg width={1280} height={720} viewBox="0 0 1280 720" style={{ position: "absolute", inset: 0 }}>
        {Array.from({ length: 24 }).map((_, i) => { const a = (i / 24) * Math.PI * 2; return <path key={i} d={`M640,360 L${640 + Math.cos(a) * 1100},${360 + Math.sin(a) * 1100}`} stroke={accent} strokeWidth={44} opacity={i % 2 ? 0.55 : 0} />; })}
      </svg>
      <svg width={1280} height={720} viewBox="0 0 1280 720" style={{ position: "absolute", inset: 0 }}><StickDefs />
        <rect x={0} y={612} width={1280} height={108} fill={floor} />
        <path d="M-20,612 L1300,608" stroke={INK} strokeWidth={7} fill="none" filter="url(#handdrawn)" />
        {motif === "arrow" && (
          <g filter="url(#handdrawn)">
            <path d="M120,600 C300,560 360,300 560,120" stroke="#E4562B" strokeWidth={30} fill="none" strokeLinecap="round" />
            <path d="M470,150 L575,105 L540,215" fill="#E4562B" stroke="#161616" strokeWidth={6} strokeLinejoin="round" />
          </g>
        )}
        {/* NHÂN VẬT SỐC — to, 2 tay ôm đầu, mắt mở to */}
        <g transform="translate(980,660) scale(0.92)"><Story brow={brow} mouth={mouth} eyeWide={eyeWide} armL={158} armR={158} lookX={-0.35} lookY={-0.25} {...persona} /></g>
      </svg>
      {/* CHỮ cực lớn */}
      <div style={{ position: "absolute", top: 244, left: 56, lineHeight: 0.92, maxWidth: 900 }}>
        {topLine ? <div style={{ fontSize: 78, fontWeight: 900, color: INK }}>{topLine.toUpperCase()}</div> : null}
        <div style={{ fontSize: bigFs, fontWeight: 900, color: "#FFD21E", WebkitTextStroke: "12px #161616" as any }}>{big}</div>
      </div>
      {/* badge số sốc */}
      {badge ? <div style={{ position: "absolute", top: 40, left: 70, background: badgeBg, color: "#fff", fontSize: 50, fontWeight: 900, padding: "8px 22px", borderRadius: 14, border: "6px solid #161616", transform: "rotate(-6deg)", WebkitTextStroke: "1px #161616" as any }}>{badge}</div> : null}
    </AbsoluteFill>
  );
};
