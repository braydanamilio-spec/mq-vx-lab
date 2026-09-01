import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring, Audio, staticFile } from "remotion";
import { useAudioData, visualizeAudio } from "@remotion/media-utils";

const D = (deg: number) => (deg * Math.PI) / 180;
const PT = (x: number, y: number, len: number, ang: number): [number, number] => [x + len * Math.cos(D(ang)), y + len * Math.sin(D(ang))];
const lerp = (a: number, b: number, t: number) => a + (b - a) * Math.max(0, Math.min(1, t));
const ease = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

type Expr = "neutral" | "curious" | "shock" | "annoyed" | "happy" | "suspicious" | "sad";
const EXPR: Record<Expr, { browY: number; browTilt: number; eyeSc: number; smile: number; look: number }> = {
  neutral:    { browY: 0,  browTilt: 0,   eyeSc: 1,    smile: 3,   look: 0 },
  curious:    { browY: -6, browTilt: 10,  eyeSc: 1.12, smile: 1,   look: 0.5 },
  shock:      { browY: -11,browTilt: 0,   eyeSc: 1.6,  smile: 0,   look: 0 },
  annoyed:    { browY: 3,  browTilt: -18, eyeSc: 0.85, smile: -6,  look: -0.3 },
  happy:      { browY: -5, browTilt: 5,   eyeSc: 1,    smile: 11,  look: 0 },
  suspicious: { browY: 2,  browTilt: -12, eyeSc: 0.6,  smile: -3,  look: 0.7 },
  sad:        { browY: -4, browTilt: 14,  eyeSc: 1,    smile: -8,  look: 0 },
};

type Pose = { armL: number; foreL: number; armR: number; foreR: number; legL: number; shinL: number; legR: number; shinR: number; headTilt: number; lean: number };
export const POSES: Record<string, Pose> = {
  idle:    { armL: 100, foreL: 98,  armR: 80,  foreR: 82,  legL: 96, shinL: 92, legR: 84, shinR: 88, headTilt: 0, lean: 0 },
  present: { armL: 98,  foreL: 92,  armR: 40,  foreR: 22,  legL: 95, shinL: 91, legR: 85, shinR: 89, headTilt: 4, lean: 3 },
  point:   { armL: 104, foreL: 104, armR: 8,   foreR: -10, legL: 95, shinL: 91, legR: 85, shinR: 89, headTilt: 3, lean: 5 },
  shrug:   { armL: 52,  foreL: 15,  armR: 128, foreR: 165, legL: 96, shinL: 92, legR: 84, shinR: 88, headTilt: 6, lean: 0 },
  shock:   { armL: -55, foreL: -92, armR: 235, foreR: 272, legL: 100,shinL: 96, legR: 80, shinR: 84, headTilt: -4, lean: -5 },
  lean:    { armL: 96,  foreL: 88,  armR: 58,  foreR: 42,  legL: 98, shinL: 94, legR: 82, shinR: 86, headTilt: 9, lean: 13 },
  lookaway:{ armL: 100, foreL: 100, armR: 82,  foreR: 84,  legL: 96, shinL: 92, legR: 84, shinR: 88, headTilt: -12, lean: -7 },
};
const blend = (a: Pose, b: Pose, t: number): Pose => { const o: any = {}; (Object.keys(a) as (keyof Pose)[]).forEach((k) => (o[k] = lerp(a[k], b[k], t))); return o; };
// LỚP SỐNG ĐỘNG: micro-motion liên tục mọi khớp (khác pha) + tay/bàn tay TRỄ (follow-through) + nhún + gật khi nói → hết cứng robot
export const live = (p: Pose, t: number, mo: number): Pose => {
  const s = (f: number, ph: number, a: number) => Math.sin(t * f + ph) * a;
  const gesture = 1 + s(0.7, 0, 0.12);           // biên độ cử chỉ thở ra/vào
  return {
    ...p,
    armR: p.armR + s(1.6, 0, 4) + s(3.1, 1, 1.4),
    foreR: p.foreR + s(1.6, -0.55, 8) * gesture,   // trễ pha so upper-arm = follow-through
    armL: p.armL + s(1.8, 1.1, 4),
    foreL: p.foreL + s(1.8, 0.5, 7) * gesture,
    headTilt: p.headTilt + s(1.05, 0, 2.6) + mo * 4 + s(2.2, 0.5, 0.8),  // gật nhẹ theo lời
    lean: p.lean + s(0.85, 0.5, 3.2),
    legL: p.legL + s(0.85, 0.5, 1.4),               // dồn trọng tâm chân so le
    legR: p.legR - s(0.85, 0.5, 1.4),
    shinL: p.shinL + s(0.85, 0.5, 0.8),
    shinR: p.shinR - s(0.85, 0.5, 0.8),
  };
};

// ---------- premium character ----------
export const StickFigure: React.FC<{
  x: number; y: number; scale?: number; flip?: boolean; pose: Pose; mouthOpen?: number; mouthWide?: number;
  expr?: Expr; blink?: number; skin?: string; shirt?: string; pants?: string; hair?: string; ink?: string; breath?: number; cap?: string; hoodie?: boolean; outfit?: "casual" | "suit"; glasses?: boolean; tie?: string;
  // 1/9 — CHÂN DIỄN THEO TƯ THẾ. `POSES` khai bốn góc chân và `live()` cũng hoạt hoá
  // chúng ("dồn trọng tâm chân so le"), nhưng phần vẽ dưới đây BỎ QUA hết: chân là hai
  // đoạn thẳng đứng cố định y=-12 -> y=24. Nghĩa là chân chưa bao giờ được diễn — cái
  // mượt mà thấy được chỉ đến từ TAY.
  // Bật cờ này thì chân vẽ bằng đúng bốn góc ấy: đùi -> gối -> cẳng chân -> giày, cùng
  // cách đã làm cho tay. Mặc định TẮT nên bốn kênh dữ liệu đang chạy không đổi một pixel.
  chanDong?: boolean;
  // 1/9 — CHẾ ĐỘ NGƯỜI QUE THẬT. Anh: *"kiểu người que phong cách chuẩn usa"*. Bản hiện tại là
  // cartoon ĐẦY ĐẶN (thân khiên đặc, tay dày 20, chân 17) — đúng lựa chọn anh chốt hồi 14/8 cho
  // bốn kênh dữ liệu. Với hài gia đình thì anh muốn nét que.
  // Bật cờ này: tay chân mảnh, thân là một nét dọc bo tròn thay cho khối đặc, đầu vẫn to và
  // biểu cảm (đó là chất USA — Stickman viral vẫn có mặt rõ nét, không phải que trơn).
  que?: boolean;
}> = ({ x, y, scale = 1, flip = false, pose, mouthOpen = 0, mouthWide = 0.5, expr = "neutral", blink = 1, skin = "#F6C89A", shirt = "#3E7BFA", pants = "#2B3A55", hair = "#3A2A22", ink = "#1E2A38", breath = 0, cap, hoodie = false, outfit = "casual", glasses = false, tie = "#C1272D", chanDong = false, que = false }) => {
  const e = EXPR[expr];
  const shY = -86 + breath * 0.4, shX = pose.lean;
  const hc = { x: shX + pose.headTilt * 0.5, y: shY - 60 };
  const shLx = shX - 32, shRx = shX + 32, shYa = shY + 14;
  const _dt = que ? 32 : 26, _dc = que ? 30 : 24;   // que: tay dài hơn cho cân với chân
  const aL = PT(shLx, shYa, _dt, pose.armL), fL = PT(aL[0], aL[1], _dc, pose.foreL);
  const aR = PT(shRx, shYa, _dt, pose.armR), fR = PT(aR[0], aR[1], _dc, pose.foreR);
  const limb = (a: number[], b: number[], w: number, col: string) => (<><line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={ink} strokeWidth={w + 4} strokeLinecap="round" /><line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={col} strokeWidth={w} strokeLinecap="round" /></>);
  const hand = (p: number[]) => <circle cx={p[0]} cy={p[1]} r={10} fill={skin} stroke={ink} strokeWidth={4} />;
  const eyeY = hc.y - 2, lk = e.look * 3.5;
  const mo = mouthOpen, mw = 16 * (0.6 + 0.25 * mouthWide);
  const WW = 27, SW = 43;
  const bodyPath = `M ${shX - WW} -4 C ${shX - SW} ${shY + 40} ${shX - SW} ${shY + 12} ${shX - 16} ${shY} Q ${shX} ${shY - 8} ${shX + 16} ${shY} C ${shX + SW} ${shY + 12} ${shX + SW} ${shY + 40} ${shX + WW} -4 Q ${shX} 12 ${shX - WW} -4 Z`;
  return (
    <g transform={`translate(${x} ${y}) scale(${flip ? -scale : scale} ${scale})`}>
      <defs>
        {/* shading khối: sáng trên, tối dưới -> nhân vật bớt phẳng (giữ nguyên tạo hình) */}
        <linearGradient id="sfShade" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ffffff" stopOpacity="0.12" />
          <stop offset="0.45" stopColor="#ffffff" stopOpacity="0" />
          <stop offset="1" stopColor="#05070d" stopOpacity="0.30" />
        </linearGradient>
        <radialGradient id="sfHi" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0" stopColor="#ffffff" stopOpacity="0.28" />
          <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
        </radialGradient>
      </defs>
      <ellipse cx={shX} cy={10} rx={52} ry={11} fill="#00000026" />
      {/* legs + shoes */}
      {chanDong ? (() => {
        // Đùi -> gối -> cẳng chân -> giày, dựng bằng đúng bốn góc của tư thế, y hệt cách tay
        // đang làm. Nhờ đó `live()` (đã hoạt hoá bốn góc ấy từ đầu) mới thật sự hiện ra: hai
        // chân dồn trọng tâm so le, và cẳng chân trễ pha so với đùi.
        const hL = [shX - 13, -12], hR = [shX + 13, -12];
        // Chế độ que: đùi và cẳng dài hơn hẳn. Đầu của rig này to (bán kính 40) nên nếu
        // giữ chân ngắn 20 thì cả hình lùn tịt — đầu chiếm hơn một phần ba người.
        const DAI = que ? 30 : 20;
        const gL = PT(hL[0], hL[1], DAI, pose.legL), cL = PT(gL[0], gL[1], DAI, pose.shinL);
        const gR = PT(hR[0], hR[1], DAI, pose.legR), cR = PT(gR[0], gR[1], DAI, pose.shinR);
        return (<>
          {limb(hR, gR, que ? 9 : 17, pants)}{limb(gR, cR, que ? 8 : 15, pants)}
          <ellipse cx={cR[0] + 2} cy={cR[1] + 5} rx={16} ry={8.5} fill={ink} />
          {limb(hL, gL, que ? 9 : 17, pants)}{limb(gL, cL, que ? 8 : 15, pants)}
          <ellipse cx={cL[0] - 2} cy={cL[1] + 5} rx={16} ry={8.5} fill={ink} />
        </>);
      })() : (<>
        <line x1={shX - 13} y1={-12} x2={shX - 13} y2={24} stroke={ink} strokeWidth={21} strokeLinecap="round" />
        <line x1={shX - 13} y1={-12} x2={shX - 13} y2={24} stroke={pants} strokeWidth={15} strokeLinecap="round" />
        <line x1={shX + 13} y1={-12} x2={shX + 13} y2={24} stroke={ink} strokeWidth={21} strokeLinecap="round" />
        <line x1={shX + 13} y1={-12} x2={shX + 13} y2={24} stroke={pants} strokeWidth={15} strokeLinecap="round" />
        <ellipse cx={shX - 15} cy={28} rx={16} ry={8.5} fill={ink} />
        <ellipse cx={shX + 15} cy={28} rx={16} ry={8.5} fill={ink} />
      </>)}
      {/* back arm (right) */}
      {limb([shRx, shYa], aR, que ? 9 : 20, shirt)}{limb(aR, fR, que ? 8 : 18, shirt)}{hand(fR)}
      {/* THÂN — khối khiên đặc (cartoon) hoặc một nét dọc bo tròn (người que). */}
      {que ? (
        <><line x1={shX} y1={shY + 6} x2={shX} y2={-6} stroke={ink} strokeWidth={26} strokeLinecap="round" />
        <line x1={shX} y1={shY + 6} x2={shX} y2={-6} stroke={shirt} strokeWidth={19} strokeLinecap="round" />
        <line x1={shLx} y1={shYa} x2={shRx} y2={shYa} stroke={ink} strokeWidth={12} strokeLinecap="round" />
        <line x1={shLx} y1={shYa} x2={shRx} y2={shYa} stroke={shirt} strokeWidth={7} strokeLinecap="round" /></>
      ) : (
      <path d={bodyPath} fill={shirt} stroke={ink} strokeWidth={5} strokeLinejoin="round" />
      )}
      <path d={bodyPath} fill="url(#sfShade)" stroke="none" />
      {outfit === "coat" ? (
        <>
          {/* áo trong (scrub) + ve áo blouse trắng + ỐNG NGHE */}
          <path d={`M ${shX - 14} ${shY} L ${shX} ${shY + 30} L ${shX + 14} ${shY} Z`} fill={tie} stroke={ink} strokeWidth={2} />
          <path d={`M ${shX - 15} ${shY - 2} L ${shX - 3} ${shY + 28} L ${shX - 22} ${shY + 16} Z`} fill="#fff" stroke={ink} strokeWidth={2.5} strokeLinejoin="round" />
          <path d={`M ${shX + 15} ${shY - 2} L ${shX + 3} ${shY + 28} L ${shX + 22} ${shY + 16} Z`} fill="#fff" stroke={ink} strokeWidth={2.5} strokeLinejoin="round" />
          <path d={`M ${shX - 9} ${shY + 3} Q ${shX - 24} ${shY + 32} ${shX - 6} ${shY + 46}`} fill="none" stroke="#3a4a5a" strokeWidth={3.5} strokeLinecap="round" />
          <path d={`M ${shX + 9} ${shY + 3} Q ${shX + 24} ${shY + 32} ${shX + 4} ${shY + 48}`} fill="none" stroke="#3a4a5a" strokeWidth={3.5} strokeLinecap="round" />
          <circle cx={shX - 1} cy={shY + 52} r={7} fill="#c0ccd8" stroke={ink} strokeWidth={2.5} />
        </>
      ) : outfit === "suit" ? (
        <>
          <path d={`M ${shX - 13} ${shY + 2} L ${shX} ${shY + 24} L ${shX + 13} ${shY + 2} Z`} fill="#fff" stroke={ink} strokeWidth={2.5} strokeLinejoin="round" />
          <path d={`M ${shX - 6} ${shY + 8} L ${shX + 6} ${shY + 8} L ${shX + 8} ${shY + 52} L ${shX} ${shY + 60} L ${shX - 8} ${shY + 52} Z`} fill={tie} stroke={ink} strokeWidth={2} strokeLinejoin="round" />
          <path d={`M ${shX - 6} ${shY + 8} L ${shX + 6} ${shY + 8} L ${shX} ${shY + 16} Z`} fill={tie} stroke={ink} strokeWidth={2} />
        </>
      ) : (
        <path d={`M ${shX - 15} ${shY + 2} Q ${shX} ${shY + 20} ${shX + 15} ${shY + 2}`} fill="none" stroke={ink} strokeWidth={3} opacity={0.5} />
      )}
      {/* front arm (left) */}
      {limb([shLx, shYa], aL, que ? 9 : 20, shirt)}{limb(aL, fL, que ? 8 : 18, shirt)}{hand(fL)}
      {/* neck */}
      <line x1={shX} y1={shY - 4} x2={hc.x} y2={hc.y + 30} stroke={skin} strokeWidth={22} strokeLinecap="round" />
      {/* ears */}
      <circle cx={hc.x - 39} cy={hc.y + 4} r={8} fill={skin} stroke={ink} strokeWidth={4} />
      <circle cx={hc.x + 39} cy={hc.y + 4} r={8} fill={skin} stroke={ink} strokeWidth={4} />
      {/* HEAD (to tròn) */}
      <circle cx={hc.x} cy={hc.y} r={40} fill={skin} stroke={ink} strokeWidth={5} />
      <ellipse cx={hc.x - 12} cy={hc.y - 14} rx={17} ry={21} fill="url(#sfHi)" />
      <path d={`M ${hc.x + 12} ${hc.y - 30} A 40 40 0 0 1 ${hc.x + 30} ${hc.y + 20}`} fill="none" stroke="#05070d" strokeWidth={4} strokeOpacity={0.14} strokeLinecap="round" />
      {cap ? (
        <g>
          {/* side hair peeking */}
          <path d={`M ${hc.x - 27} ${hc.y - 2} Q ${hc.x - 29} ${hc.y - 18} ${hc.x - 20} ${hc.y - 20}`} fill="none" stroke={hair} strokeWidth={7} strokeLinecap="round" />
          <path d={`M ${hc.x + 27} ${hc.y - 2} Q ${hc.x + 29} ${hc.y - 18} ${hc.x + 20} ${hc.y - 20}`} fill="none" stroke={hair} strokeWidth={7} strokeLinecap="round" />
          {/* cap dome */}
          <path d={`M ${hc.x - 28} ${hc.y - 10} Q ${hc.x} ${hc.y - 44} ${hc.x + 28} ${hc.y - 10} Q ${hc.x} ${hc.y - 20} ${hc.x - 28} ${hc.y - 10} Z`} fill={cap} stroke={ink} strokeWidth={4.5} />
          {/* brim */}
          <path d={`M ${hc.x - 6} ${hc.y - 12} Q ${hc.x + 34} ${hc.y - 16} ${hc.x + 40} ${hc.y - 6} Q ${hc.x + 30} ${hc.y - 2} ${hc.x - 6} ${hc.y - 8} Z`} fill={cap} stroke={ink} strokeWidth={4.5} strokeLinejoin="round" />
          {/* button + star accent (US) */}
          <circle cx={hc.x} cy={hc.y - 32} r={3} fill={ink} />
          <text x={hc.x - 6} y={hc.y - 18} fontSize={12} fontWeight={900} fill="#fff" fontFamily="Poppins, sans-serif">★</text>
        </g>
      ) : (
        <path d={`M ${hc.x - 39} ${hc.y - 4} Q ${hc.x - 44} ${hc.y - 46} ${hc.x} ${hc.y - 44} Q ${hc.x + 44} ${hc.y - 46} ${hc.x + 39} ${hc.y - 4} Q ${hc.x + 20} ${hc.y - 28} ${hc.x} ${hc.y - 26} Q ${hc.x - 20} ${hc.y - 28} ${hc.x - 39} ${hc.y - 4} Z`} fill={hair} stroke={ink} strokeWidth={3} strokeLinejoin="round" />
      )}
      {/* cheeks */}
      <circle cx={hc.x - 22} cy={eyeY + 17} r={6.5} fill="#ff9a9a" opacity={0.32} />
      <circle cx={hc.x + 22} cy={eyeY + 17} r={6.5} fill="#ff9a9a" opacity={0.32} />
      {/* brows */}
      <line x1={hc.x - 21} y1={eyeY - 16 + e.browY} x2={hc.x - 6} y2={eyeY - 16 + e.browY + e.browTilt} stroke={ink} strokeWidth={5} strokeLinecap="round" />
      <line x1={hc.x + 6} y1={eyeY - 16 + e.browY + e.browTilt} x2={hc.x + 21} y2={eyeY - 16 + e.browY} stroke={ink} strokeWidth={5} strokeLinecap="round" />
      {/* BIG eyes */}
      <ellipse cx={hc.x - 13} cy={eyeY} rx={9.5} ry={12.5 * e.eyeSc * blink} fill="#fff" stroke={ink} strokeWidth={2.5} />
      <ellipse cx={hc.x + 13} cy={eyeY} rx={9.5} ry={12.5 * e.eyeSc * blink} fill="#fff" stroke={ink} strokeWidth={2.5} />
      <circle cx={hc.x - 13 + lk} cy={eyeY + 2} r={5} fill={ink} opacity={blink > 0.5 ? 1 : 0} />
      <circle cx={hc.x + 13 + lk} cy={eyeY + 2} r={5} fill={ink} opacity={blink > 0.5 ? 1 : 0} />
      <circle cx={hc.x - 15 + lk} cy={eyeY - 1} r={1.8} fill="#fff" opacity={blink > 0.5 ? 1 : 0} />
      <circle cx={hc.x + 11 + lk} cy={eyeY - 1} r={1.8} fill="#fff" opacity={blink > 0.5 ? 1 : 0} />
      {glasses && (
        <g fill="none" stroke={ink} strokeWidth={3}>
          <rect x={hc.x - 25} y={eyeY - 11} width={23} height={22} rx={7} />
          <rect x={hc.x + 2} y={eyeY - 11} width={23} height={22} rx={7} />
          <line x1={hc.x - 2} y1={eyeY} x2={hc.x + 2} y2={eyeY} />
        </g>
      )}
      {/* nose */}
      <path d={`M ${hc.x - 1} ${eyeY + 9} q -4 6 2 7`} fill="none" stroke={ink} strokeWidth={2.5} strokeLinecap="round" opacity={0.45} />
      {/* MOUTH */}
      {mo < 0.16 ? (
        <path d={`M ${hc.x - 14} ${eyeY + 23} Q ${hc.x} ${eyeY + 23 + e.smile} ${hc.x + 14} ${eyeY + 23}`} fill="none" stroke={ink} strokeWidth={4} strokeLinecap="round" />
      ) : (
        <g>
          <path d={`M ${hc.x - mw} ${eyeY + 23} Q ${hc.x} ${eyeY + 21} ${hc.x + mw} ${eyeY + 23} Q ${hc.x + mw * 0.7} ${eyeY + 23 + mo * 14} ${hc.x} ${eyeY + 23 + mo * 16} Q ${hc.x - mw * 0.7} ${eyeY + 23 + mo * 14} ${hc.x - mw} ${eyeY + 23} Z`} fill="#6d2b2b" stroke={ink} strokeWidth={4} strokeLinejoin="round" />
          <path d={`M ${hc.x - mw * 0.8} ${eyeY + 23} L ${hc.x + mw * 0.8} ${eyeY + 23}`} stroke="#fff" strokeWidth={Math.min(5, 1 + mo * 5)} strokeLinecap="round" />
          {mo > 0.5 && <ellipse cx={hc.x} cy={eyeY + 23 + mo * 12} rx={mw * 0.5} ry={2 + mo * 3} fill="#e07a7a" />}
        </g>
      )}
    </g>
  );
};

// ---------- channel palettes (nền/template theo tông kênh) ----------
export const THEMES: Record<string, any> = {
  broke:  { wall: ["#FFF6E6", "#FFE9C7"], floor: "#E8C79A", floorLine: "#cBA878", accent: "#1F9D6B", shirt: "#1F9D6B", prop: "#E23744" },
  inside: { wall: ["#FDEEF3", "#FBD9E6"], floor: "#F3C6D6", floorLine: "#e0a9bf", accent: "#E14B6A", shirt: "#E14B6A", prop: "#7C3AED" },
  huh:    { wall: ["#EAF3FF", "#D7E9FF"], floor: "#CFE0EF", floorLine: "#b3ccdf", accent: "#2D7DF6", shirt: "#2D7DF6", prop: "#F5A623" },
  ranked: { wall: ["#0E1726", "#152238"], floor: "#0A1220", floorLine: "#22344f", accent: "#F5B301", shirt: "#F5B301", prop: "#22D3EE" },
};

type Beat = { t: number; expr: Expr; pose: keyof typeof POSES; cap: string };
const BEATS: Beat[] = [
  { t: 0.0, expr: "curious",    pose: "present", cap: "Your rent just hit $2,100" },
  { t: 2.3, expr: "annoyed",    pose: "shrug",   cap: "…for the SAME apartment" },
  { t: 3.4, expr: "curious",    pose: "point",   cap: "So you ask your landlord" },
  { t: 5.1, expr: "suspicious", pose: "lean",    cap: "what he'll never tell you" },
];

export const StickDemo: React.FC<{ theme?: string }> = ({ theme = "broke" }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const time = frame / fps;
  const T = THEMES[theme] || THEMES.broke;
  const audioData = useAudioData(staticFile("stickdemo/vo.mp3"));
  // smoothed lip-sync (avg amplitude over window) + fake vowel width
  let mouthOpen = 0, mouthWide = 0.5;
  if (audioData) {
    let s = 0; const N = 4;
    for (let k = 0; k < N; k++) {
      const v = visualizeAudio({ fps, frame: Math.max(0, frame - k), audioData, numberOfSamples: 16 });
      s += (v[1] + v[2] + v[3] + v[4]) ;
    }
    mouthOpen = Math.min(1, (s / N) * 9);
    mouthOpen = mouthOpen < 0.14 ? 0 : mouthOpen; // silence -> closed
    mouthWide = 0.5 + 0.5 * Math.sin(time * 17);
  }
  let bi = 0; for (let i = 0; i < BEATS.length; i++) if (time >= BEATS[i].t) bi = i;
  const b = BEATS[bi], nb = BEATS[bi + 1] || { t: 7.6 };
  // spring => chuyển thế có anticipation + overshoot + settle (mượt, không tuyến tính robot)
  const bt = spring({ frame: frame - Math.round(b.t * fps), fps, config: { damping: 11, stiffness: 85, mass: 0.9 } });
  const prev = bi > 0 ? BEATS[bi - 1] : b;
  const pose = live(blend(POSES[prev.pose], POSES[b.pose], bt), time, mouthOpen);
  const breath = Math.sin(time * 2.8) * 3;
  const weight = Math.sin(time * 1.3) * 4 + Math.sin(time * 0.6) * 3; // dồn trọng tâm 2 tầng
  const blink = (Math.sin(time * 2.6) > 0.93 || Math.sin(time * 2.6 + 2) > 0.97) ? 0.12 : 1;

  const llShow = interpolate(time, [3.2, 3.9], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const llX = lerp(width + 220, width * 0.74, ease(llShow));
  const llExpr: Expr = time > 5.0 ? "suspicious" : "neutral";
  const rent = Math.round(interpolate(time, [0.4, 2.1], [1350, 2100], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const signPop = interpolate(time, [0.2, 0.65], [0, 1], { extrapolateRight: "clamp" });
  const dark = theme === "ranked";

  return (
    <AbsoluteFill style={{ background: T.wall[0] }}>
      {/* wall gradient + soft light */}
      <AbsoluteFill style={{ background: `linear-gradient(180deg,${T.wall[0]},${T.wall[1]})` }} />
      <div style={{ position: "absolute", left: "18%", top: -200, width: 700, height: 700, borderRadius: "50%", background: T.accent, opacity: 0.08, filter: "blur(30px)" }} />
      {/* floor */}
      <div style={{ position: "absolute", left: 0, top: height * 0.71, width, height: height * 0.29, background: T.floor }} />
      <div style={{ position: "absolute", left: 0, top: height * 0.71, width, height: 5, background: T.floorLine }} />
      {/* furniture (depth) */}
      <div style={{ position: "absolute", left: 78, top: 270, width: 250, height: 190, background: dark ? "#0c1a2e" : "#bfe3ff", border: `10px solid ${dark ? "#22344f" : "#fff"}`, borderRadius: 12, boxShadow: "0 10px 26px #0001" }} />
      <div style={{ position: "absolute", left: 197, top: 270, width: 8, height: 190, background: dark ? "#22344f" : "#fff" }} />
      <div style={{ position: "absolute", left: 120, top: 210, fontSize: 46 }}>🖼️</div>
      <div style={{ position: "absolute", left: 46, top: height * 0.71 - 96, fontSize: 96 }}>🪴</div>
      <div style={{ position: "absolute", right: 120, top: height * 0.71 - 60, width: 220, height: 60, background: dark ? "#0c1a2e" : "#d9b98f", borderRadius: 8, opacity: 0.9 }} />

      {/* rent sign */}
      <div style={{ position: "absolute", right: 70, top: 320, transform: `scale(${signPop})`, transformOrigin: "center", background: "#fff", border: `8px solid ${T.ink || "#22303C"}`, borderRadius: 22, padding: "16px 32px", textAlign: "center", boxShadow: "0 16px 40px #0002" }}>
        <div style={{ fontFamily: "Poppins, sans-serif", fontWeight: 800, fontSize: 82, color: T.prop, lineHeight: 1 }}>${rent.toLocaleString()}</div>
        <div style={{ fontWeight: 700, fontSize: 24, color: "#456", letterSpacing: 2 }}>RENT / MONTH</div>
      </div>

      {/* characters */}
      <svg viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute", inset: 0, width, height }}>
        {llShow > 0 && <StickFigure x={llX} y={height * 0.71} scale={1.75} flip pose={time > 5 ? POSES.lookaway : POSES.idle} expr={llExpr} blink={blink} skin="#E8B07A" shirt="#C1502E" pants="#3a2f2a" hair="#20140f" breath={breath} />}
        <StickFigure x={width * 0.35 + weight} y={height * 0.71} scale={1.95} pose={pose} mouthOpen={mouthOpen} mouthWide={mouthWide} expr={b.expr} blink={blink} outfit="suit" glasses tie="#1D63C7" shirt="#39454F" pants="#222C3A" skin="#F1B784" hair="#3A2A20" breath={breath} />
      </svg>

      {/* caption */}
      <div style={{ position: "absolute", left: "50%", bottom: 210, transform: "translateX(-50%)", background: "#151b24ee", color: "#fff", fontFamily: "Poppins, sans-serif", fontWeight: 800, fontSize: 46, padding: "14px 34px", borderRadius: 18, whiteSpace: "nowrap", boxShadow: "0 12px 34px #0005", border: `2px solid ${T.accent}55` }}>{b.cap}</div>

      <Audio src={staticFile("stickdemo/vo.mp3")} />
    </AbsoluteFill>
  );
};
