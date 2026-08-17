import React from "react";
import { useCurrentFrame } from "remotion";

// ✍️ STICK FIGURE vẽ tay (style "Why You?") — nét mực wobbly + mặt biểu cảm cao, mượt.
// "Vẽ tay" = bọc filter feDisplacementMap (nét sạch -> rung hữu cơ). Đổi seed theo frame = boiling line.
export type StickPose = {
  lookX?: number; lookY?: number;      // hướng con ngươi (-1..1)
  brow?: number;                        // -1 giận .. 0 thường .. 1 lo/ngạc nhiên
  mouth?: "neutral" | "smile" | "frown" | "o" | "talk";
  mouthOpen?: number;                   // 0..1 lip-sync theo biên độ audio (ưu tiên hơn `mouth`)
  armL?: number; armR?: number;         // góc tay (độ): 0 xuôi, + giơ ra
  legPhase?: number;                    // đi bộ: độ lệch chân
  ink?: string;
};
const INK = "#161616";
const HY = -300, R = 84; // tâm đầu, bán kính

export const StickDefs: React.FC<{ boil?: number }> = ({ boil = 0 }) => (
  <defs>
    <filter id="handdrawn" x="-25%" y="-25%" width="150%" height="150%">
      <feTurbulence type="fractalNoise" baseFrequency="0.016" numOctaves="2" seed={2 + Math.floor(boil)} result="n" />
      <feDisplacementMap in="SourceGraphic" in2="n" scale="5.5" xChannelSelector="R" yChannelSelector="G" />
    </filter>
  </defs>
);

export const StickFigure: React.FC<StickPose & { walk?: number; live?: boolean; dark?: boolean }> = ({
  lookX = 0, lookY = 0, brow = 0, mouth = "neutral", mouthOpen, armL = 18, armR = -18, legPhase = 0, ink, walk = 0, live = true, dark = false,
}) => {
  ink = ink || (dark ? "#F5F3FF" : INK);      // nền tối -> nét trắng
  const headFill = dark ? "#232A52" : "#FFFFFF";
  const PUP = "#161616";                       // con ngươi luôn đậm (nổi trên tròng trắng)
  const frame = useCurrentFrame();
  // ✨ SỐNG tự động: chớp mắt thưa + thở nhẹ + tay đung đưa micro (hết "tĩnh")
  const blinkPhase = (frame % 96);
  const blink = live && blinkPhase < 4 ? Math.max(0.12, Math.abs(blinkPhase - 2) / 2) : 1;
  const breathe = live ? Math.sin(frame / 20) * 2 : 0;
  const microArm = live ? Math.sin(frame / 18) * 3 : 0;
  // đi bộ: legPhase + swing tay ngược pha
  const gait = walk ? Math.sin(frame / 4) * 26 * walk : 0;
  const armSwing = walk ? Math.sin(frame / 4) * 22 * walk : 0;
  const S = { stroke: ink, strokeWidth: 8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, fill: "none" };
  const rad = (d: number) => (d * Math.PI) / 180;
  const sh = { x: 0, y: -150 + breathe }, hip = 0, armLen = 118, legLen = 150;
  legPhase = legPhase + gait; armL = armL + microArm + armSwing; armR = armR + microArm - armSwing;
  const aL = { x: sh.x - Math.sin(rad(armL)) * armLen, y: sh.y + Math.cos(rad(armL)) * armLen };
  const aR = { x: sh.x + Math.sin(rad(-armR)) * armLen, y: sh.y + Math.cos(rad(-armR)) * armLen };
  const lL = { x: -Math.sin(rad(18 + legPhase)) * legLen, y: hip + Math.cos(rad(18 + legPhase)) * legLen };
  const lR = { x: Math.sin(rad(18 - legPhase)) * legLen, y: hip + Math.cos(rad(18 - legPhase)) * legLen };

  const eyeY = HY - 10, eyeDX = 30;
  const browY = HY - 42, tilt = brow < 0 ? 11 : brow > 0 ? -9 : 0, lift = brow > 0 ? -8 : 0;
  const mY = HY + 36;
  const mouthEl = { neutral: `M-22,${mY} L22,${mY}`, smile: `M-24,${mY - 4} Q0,${mY + 20} 24,${mY - 4}`, frown: `M-24,${mY + 12} Q0,${mY - 12} 24,${mY + 12}`, talk: `M-18,${mY - 2} Q0,${mY + 14} 18,${mY - 2}` } as const;

  return (
    <g filter="url(#handdrawn)">
      {/* chân + bàn chân */}
      <path d={`M0,${hip} L${lL.x},${lL.y}`} {...S} />
      <path d={`M0,${hip} L${lR.x},${lR.y}`} {...S} />
      <path d={`M${lL.x},${lL.y} l${-24 + legPhase * 0.4},4`} {...S} />
      <path d={`M${lR.x},${lR.y} l${24 + legPhase * 0.4},4`} {...S} />
      {/* thân + tay */}
      <path d={`M0,${hip} L${sh.x},${sh.y}`} {...S} />
      <path d={`M${sh.x},${sh.y} L${aL.x},${aL.y}`} {...S} />
      <path d={`M${sh.x},${sh.y} L${aR.x},${aR.y}`} {...S} />
      {/* cổ */}
      <path d={`M0,${sh.y} L0,${HY + R - 4}`} {...S} />
      {/* đầu */}
      <circle cx={0} cy={HY} r={R} stroke={ink} strokeWidth={8} fill={headFill} />
      {/* mắt (chớp = co ry) — tròng trắng + con ngươi đậm (rõ ở cả nền sáng/tối) */}
      <ellipse cx={-eyeDX} cy={eyeY} rx={15} ry={18 * blink} fill="#fff" stroke={PUP} strokeWidth={3} />
      <ellipse cx={eyeDX} cy={eyeY} rx={15} ry={18 * blink} fill="#fff" stroke={PUP} strokeWidth={3} />
      {blink > 0.5 && <><circle cx={-eyeDX + lookX * 7} cy={eyeY + lookY * 8} r={7} fill={PUP} />
      <circle cx={eyeDX + lookX * 7} cy={eyeY + lookY * 8} r={7} fill={PUP} /></>}
      {/* chân mày */}
      <path d={`M${-eyeDX - 18},${browY + lift + tilt} L${-eyeDX + 16},${browY + lift - tilt}`} stroke={ink} strokeWidth={7} strokeLinecap="round" />
      <path d={`M${eyeDX - 16},${browY + lift - tilt} L${eyeDX + 18},${browY + lift + tilt}`} stroke={ink} strokeWidth={7} strokeLinecap="round" />
      {/* miệng — lip-sync nếu có mouthOpen, ngược lại theo biểu cảm */}
      {mouthOpen != null
        ? (mouthOpen > 0.12
            ? <ellipse cx={0} cy={mY + 2} rx={13} ry={3 + mouthOpen * 17} fill={dark ? "#0E1230" : "#3A2A2A"} stroke={ink} strokeWidth={3} />
            : <path d={mouthEl.neutral} stroke={ink} strokeWidth={6} fill="none" strokeLinecap="round" />)
        : (mouth === "o" ? <ellipse cx={0} cy={mY + 2} rx={11} ry={14} fill={ink} /> : <path d={mouthEl[mouth]} stroke={ink} strokeWidth={6} fill="none" strokeLinecap="round" />)}
    </g>
  );
};
