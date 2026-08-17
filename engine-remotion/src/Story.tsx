import React from "react";
import { useCurrentFrame } from "remotion";

// 🎭 STORY character — chất STORYTIME (Jaiden-style GỐC tự vẽ): ĐẦU TO + MẮT TO biểu cảm + TAY NOODLE.
// Nhân vật riêng mỗi kênh qua props (tóc/outfit/kính). Cùng pose API (lip-sync + gesture + dark).
export type StoryPose = {
  lookX?: number; lookY?: number; brow?: number; mouthOpen?: number;
  mouth?: "neutral" | "smile" | "frown" | "o";
  armL?: number; armR?: number; walk?: number; live?: boolean; dark?: boolean;
  skin?: string; hair?: string; hairStyle?: "short" | "long";
  outfit?: "tie" | "labcoat" | "hoodie"; shirt?: string; tie?: string; glasses?: boolean;
  eyeWide?: number;   // 1 = thường, >1 = mắt mở to (sốc); <1 = nheo (hoài nghi)
};
const INK = "#2A2A2A";
const HY = -330, R = 120;                 // đầu TO

export const Story: React.FC<StoryPose> = ({
  lookX = 0, lookY = 0, brow = 0, mouthOpen, mouth = "neutral", armL = 12, armR = 12, walk = 0, live = true, dark = false,
  skin = "#F6C9A0", hair = "#3A2E44", hairStyle = "short", outfit = "tie", shirt = "#7FB0D8", tie = "#E4562B", glasses = false, eyeWide = 1,
}) => {
  const f = useCurrentFrame();
  const ink = dark ? "#F5F3FF" : INK;
  const bp = f % 110; const blink = live && bp < 4 ? Math.max(0.1, Math.abs(bp - 2) / 2) : 1;
  const bob = live ? Math.sin(f / 22) * 3 : 0;
  const rad = (d: number) => (d * Math.PI) / 180;
  const sh = -150 + bob;                    // vai
  // tay NOODLE: mảnh, cong, bàn tay tròn nhỏ
  const aLen = 118;
  const hL = { x: -66 - Math.sin(rad(armL)) * aLen, y: sh + 30 + Math.cos(rad(armL)) * aLen };
  const hR = { x: 66 + Math.sin(rad(armR)) * aLen, y: sh + 30 + Math.cos(rad(armR)) * aLen };
  const eyeY = HY - 6, eDX = 44, browY = HY - 52, tilt = brow < 0 ? 12 : brow > 0 ? -10 : 0, lift = brow > 0 ? -8 : 0, mY = HY + 52;
  const bodyTop = sh + 8, bodyBot = 30, bodyW = 82;
  const bodyFill = outfit === "labcoat" ? "#FFFFFF" : outfit === "hoodie" ? shirt : shirt;

  const mouthNode = mouthOpen != null
    ? (mouthOpen > 0.12 ? <ellipse cx={0} cy={mY} rx={16} ry={4 + mouthOpen * 15} fill={dark ? "#0E1230" : "#7A3B3B"} stroke={ink} strokeWidth={3} /> : <path d={`M-14,${mY} Q0,${mY + 5} 14,${mY}`} stroke={ink} strokeWidth={5} fill="none" strokeLinecap="round" />)
    : mouth === "smile" ? <path d={`M-20,${mY - 3} Q0,${mY + 16} 20,${mY - 3}`} stroke={ink} strokeWidth={5} fill="none" strokeLinecap="round" />
    : mouth === "frown" ? <path d={`M-20,${mY + 9} Q0,${mY - 9} 20,${mY + 9}`} stroke={ink} strokeWidth={5} fill="none" strokeLinecap="round" />
    : mouth === "o" ? <ellipse cx={0} cy={mY} rx={11} ry={13} fill={dark ? "#0E1230" : "#7A3B3B"} stroke={ink} strokeWidth={3} />
    : <path d={`M-16,${mY} Q0,${mY + 4} 16,${mY}`} stroke={ink} strokeWidth={5} fill="none" strokeLinecap="round" />;

  return (
    <g filter="url(#handdrawn)">
      {/* tóc dài phía sau (nữ) */}
      {hairStyle === "long" && <path d={`M${-R - 6},${HY - 10} C${-R - 30},${HY + 180} ${-R + 10},${bodyTop + 120} ${-R + 30},${bodyTop + 120} L${-R + 40},${HY} Z M${R + 6},${HY - 10} C${R + 30},${HY + 180} ${R - 10},${bodyTop + 120} ${R - 30},${bodyTop + 120} L${R - 40},${HY} Z`} fill={hair} stroke={ink} strokeWidth={5} />}
      {/* chân ngắn + giày */}
      <path d={`M-24,${bodyBot} L-26,${bodyBot + 70}`} stroke={outfit === "hoodie" ? "#3A3550" : "#3A3550"} strokeWidth={26} fill="none" strokeLinecap="round" />
      <path d={`M24,${bodyBot} L26,${bodyBot + 70}`} stroke="#3A3550" strokeWidth={26} fill="none" strokeLinecap="round" />
      <ellipse cx={-30} cy={bodyBot + 78} rx={26} ry={13} fill="#2B2B2B" stroke={ink} strokeWidth={4} />
      <ellipse cx={30} cy={bodyBot + 78} rx={26} ry={13} fill="#2B2B2B" stroke={ink} strokeWidth={4} />
      {/* tay noodle (sau thân) */}
      <path d={`M-40,${sh + 20} Q${-96},${sh + 70} ${hL.x},${hL.y}`} stroke={outfit === "labcoat" ? "#EDEDED" : bodyFill} strokeWidth={16} fill="none" strokeLinecap="round" />
      <path d={`M40,${sh + 20} Q${96},${sh + 70} ${hR.x},${hR.y}`} stroke={outfit === "labcoat" ? "#EDEDED" : bodyFill} strokeWidth={16} fill="none" strokeLinecap="round" />
      <circle cx={hL.x} cy={hL.y} r={15} fill={skin} stroke={ink} strokeWidth={4} />
      <circle cx={hR.x} cy={hR.y} r={15} fill={skin} stroke={ink} strokeWidth={4} />
      {/* thân nhỏ tròn */}
      <path d={`M${-bodyW},${bodyTop} C${-bodyW - 6},${bodyBot} ${-40},${bodyBot + 16} 0,${bodyBot + 16} C40,${bodyBot + 16} ${bodyW + 6},${bodyBot} ${bodyW},${bodyTop} C${bodyW},${bodyTop - 26} ${-bodyW},${bodyTop - 26} ${-bodyW},${bodyTop} Z`} fill={bodyFill} stroke={ink} strokeWidth={6} />
      {/* outfit chi tiết */}
      {outfit === "tie" && <g>
        <path d={`M-22,${bodyTop - 18} L0,${bodyTop + 6} L22,${bodyTop - 18}`} fill="#fff" stroke={ink} strokeWidth={4} />
        <path d={`M-8,${bodyTop} L8,${bodyTop} L5,${bodyTop + 14} L-5,${bodyTop + 14} Z`} fill={tie} stroke={ink} strokeWidth={3} />
        <path d={`M-5,${bodyTop + 14} L5,${bodyTop + 14} L11,${bodyBot - 6} L0,${bodyBot + 6} L-11,${bodyBot - 6} Z`} fill={tie} stroke={ink} strokeWidth={3} />
      </g>}
      {outfit === "labcoat" && <g>
        <path d={`M0,${bodyTop - 20} L0,${bodyBot + 14}`} stroke={ink} strokeWidth={3} />
        <path d={`M-22,${bodyTop - 18} L0,${bodyTop + 4} L22,${bodyTop - 18}`} fill="none" stroke={ink} strokeWidth={4} />
        <path d={`M0,${bodyTop + 4} L0,${bodyBot - 20}`} stroke={tie} strokeWidth={10} strokeLinecap="round" />
        <rect x={16} y={bodyTop + 30} width={16} height={22} rx={3} fill="none" stroke={ink} strokeWidth={3} />
      </g>}
      {outfit === "hoodie" && <g>
        <path d={`M-26,${bodyTop - 16} Q0,${bodyTop + 20} 26,${bodyTop - 16}`} fill="none" stroke={ink} strokeWidth={4} />
        <line x1={-10} y1={bodyTop + 6} x2={-10} y2={bodyTop + 40} stroke={ink} strokeWidth={4} />
        <line x1={10} y1={bodyTop + 6} x2={10} y2={bodyTop + 40} stroke={ink} strokeWidth={4} />
      </g>}
      {/* cổ + ĐẦU TO */}
      <rect x={-14} y={HY + R - 22} width={28} height={30} rx={10} fill={skin} stroke={ink} strokeWidth={4} />
      <circle cx={0} cy={HY} r={R} fill={skin} stroke={ink} strokeWidth={6} />
      {/* tóc trước */}
      <path d={`M${-R - 2},${HY - 4} C${-R + 4},${HY - R - 24} ${R - 4},${HY - R - 24} ${R + 2},${HY - 4} C${R - 6},${HY - R + 34} ${hairStyle === "long" ? -R + 40 : -R + 24},${HY - R + 34} ${-R - 2},${HY - 4} Z`} fill={hair} stroke={ink} strokeWidth={5} />
      {/* MẮT TO biểu cảm (mở to/nheo theo cảm xúc) */}
      <ellipse cx={-eDX} cy={eyeY} rx={30 * Math.min(eyeWide, 1.2)} ry={34 * blink * eyeWide} fill="#fff" stroke={ink} strokeWidth={5} />
      <ellipse cx={eDX} cy={eyeY} rx={30 * Math.min(eyeWide, 1.2)} ry={34 * blink * eyeWide} fill="#fff" stroke={ink} strokeWidth={5} />
      {blink > 0.5 && <>
        <circle cx={-eDX + lookX * 12} cy={eyeY + lookY * 14} r={15} fill="#2A2A2A" /><circle cx={-eDX + lookX * 12 + 5} cy={eyeY + lookY * 14 - 6} r={5} fill="#fff" />
        <circle cx={eDX + lookX * 12} cy={eyeY + lookY * 14} r={15} fill="#2A2A2A" /><circle cx={eDX + lookX * 12 + 5} cy={eyeY + lookY * 14 - 6} r={5} fill="#fff" /></>}
      {/* kính tròn to */}
      {glasses && <g stroke={ink} strokeWidth={5} fill="#BFE9F530">
        <circle cx={-eDX} cy={eyeY} r={38} /><circle cx={eDX} cy={eyeY} r={38} />
        <line x1={-eDX + 38} y1={eyeY} x2={eDX - 38} y2={eyeY} />
      </g>}
      {/* chân mày biểu cảm */}
      <path d={`M${-eDX - 22},${browY + lift + tilt} Q${-eDX},${browY + lift - 6 + tilt} ${-eDX + 22},${browY + lift - tilt}`} stroke={ink} strokeWidth={7} fill="none" strokeLinecap="round" />
      <path d={`M${eDX - 22},${browY + lift - tilt} Q${eDX},${browY + lift - 6 + tilt} ${eDX + 22},${browY + lift + tilt}`} stroke={ink} strokeWidth={7} fill="none" strokeLinecap="round" />
      {mouthNode}
    </g>
  );
};
