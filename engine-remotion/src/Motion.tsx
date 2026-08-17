import React from "react";
import { spring, interpolate } from "remotion";

// 🎞️ TẦNG CHUYỂN ĐỘNG + BIẾN THIÊN theo SEED (nội dung) — sống động, mượt, KHÔNG lặp dù triệu clip.
export const hashStr = (s: string) => { let h = 2166136261; for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619); return h >>> 0; };
export const rng = (seed: number) => { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; };
export const pick = <T,>(r: () => number, arr: T[]): T => arr[Math.floor(r() * arr.length)];
export const rnd = (r: () => number, a: number, b: number) => a + r() * (b - a);

export type Style = { accent: string; layout: string; entrance: string; frame: string; camera: string; phase: number; rr: () => number };
export const sceneStyle = (slug: string, idx: number, palette: string[]): Style => {
  const r = rng(hashStr(slug + ":" + idx));
  return {
    accent: pick(r, palette),
    layout: pick(r, ["row", "arc", "scatter", "stack"]),
    entrance: pick(r, ["up", "left", "right", "zoom", "drop", "fade"]),
    frame: pick(r, ["badge", "soft", "plain", "badge"]),
    camera: pick(r, ["pushIn", "pushOut", "panL", "panR", "still", "pushIn"]),
    phase: rnd(r, 0, 6.28), rr: r,
  };
};

// entrance (đầu cảnh) + exit (cuối cảnh) -> {opacity, transform}
export const inOut = (type: string, l: number, dur: number, fps = 30) => {
  const pin = spring({ frame: l, fps, config: { damping: 14, mass: 0.7 } });
  const exN = 9; const pout = interpolate(l, [dur - exN, dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  let tx = 0, ty = 0, sc = 1, o = pin;
  if (type === "up") ty = (1 - pin) * 90;
  else if (type === "left") tx = (1 - pin) * -160;
  else if (type === "right") tx = (1 - pin) * 160;
  else if (type === "zoom") sc = 0.62 + pin * 0.38;
  else if (type === "drop") ty = (1 - pin) * -120;
  else sc = 0.93 + pin * 0.07; // fade
  // exit: trôi lên + mờ + thu nhỏ nhẹ
  ty += pout * -70; sc *= 1 - pout * 0.12; o *= 1 - pout;
  return { opacity: o, transform: `translate(${tx}px, ${ty}px) scale(${sc})` };
};

// camera nhẹ toàn cảnh (parallax/push) -> transform cho lớp nền/tiền cảnh
export const camera = (type: string, l: number, dur: number, depth = 1) => {
  const p = interpolate(l, [0, dur], [0, 1], { extrapolateRight: "clamp" });
  let sc = 1, tx = 0, ty = 0;
  if (type === "pushIn") sc = 1 + 0.06 * p * depth;
  else if (type === "pushOut") sc = 1.06 - 0.06 * p * depth;
  else if (type === "panL") tx = (0.5 - p) * 60 * depth;
  else if (type === "panR") tx = (p - 0.5) * 60 * depth;
  else sc = 1 + 0.02 * Math.sin(p * Math.PI) * depth;
  return `translate(${tx}px, ${ty}px) scale(${sc})`;
};

// 🌈 NỀN SỐNG liên tục (theo global frame) — gradient trôi + blob + hạt. Mượt xuyên suốt video.
export const LivingBg: React.FC<{ f: number; bg: string; accent: string; accent2?: string; W: number; H: number }> = ({ f, bg, accent, accent2 = accent, W, H }) => {
  const blobs = Array.from({ length: 6 }).map((_, i) => {
    const s = i * 1.7; const x = W / 2 + Math.sin(f / (90 + i * 18) + s) * (W * 0.32);
    const y = H / 2 + Math.cos(f / (110 + i * 14) + s * 1.3) * (H * 0.34);
    const r = 240 + Math.sin(f / 60 + s) * 60 + i * 40; const col = i % 2 ? accent : accent2;
    return { x, y, r, col, o: 0.10 + 0.05 * Math.sin(f / 50 + s) };
  });
  const shift = Math.sin(f / 140) * 8;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
      <defs><radialGradient id="lbg" cx={`${50 + shift}%`} cy={`${38 + shift * 0.5}%`} r="85%">
        <stop offset="0%" stopColor={tint(bg, 6)} /><stop offset="100%" stopColor={tint(bg, -6)} />
      </radialGradient>
        <filter id="soft"><feGaussianBlur stdDeviation="60" /></filter></defs>
      <rect x={0} y={0} width={W} height={H} fill="url(#lbg)" />
      <g filter="url(#soft)">{blobs.map((b, i) => <circle key={i} cx={b.x} cy={b.y} r={b.r} fill={b.col} opacity={b.o} />)}</g>
      {Array.from({ length: 26 }).map((_, i) => { const x = ((i * 197) % W); const y = ((i * 131 + f * (0.4 + (i % 3) * 0.3)) % (H + 40)) - 20; return <circle key={`p${i}`} cx={x} cy={y} r={3 + (i % 3) * 2} fill={accent} opacity={0.12 + 0.08 * Math.sin(f / 30 + i)} />; })}
    </svg>
  );
};
function tint(hex: string, amt: number) {
  const c = hex.replace("#", ""); const n = parseInt(c.length === 3 ? c.split("").map((x) => x + x).join("") : c, 16);
  const cl = (v: number) => Math.max(0, Math.min(255, v));
  const r = cl(((n >> 16) & 255) + amt * 2.2), g = cl(((n >> 8) & 255) + amt * 2.2), b = cl((n & 255) + amt * 2.2);
  return `rgb(${r|0},${g|0},${b|0})`;
}
