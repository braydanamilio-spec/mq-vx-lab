import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, interpolate, useCurrentFrame, Easing } from "remotion";
import { Story } from "./Story";
import { StickDefs } from "./StickFigure";

// 📱 SHORT 9:16 data-driven (đa kênh) — RENDER RIÊNG, hook riêng. Story persona + karaoke + lip-sync + data.
const INK = "#161616", RED = "#E4562B", GREEN = "#2FA84F", GOLD = "#D79A34";
type Scene = { type: string; audio: string; dur: number; nar: string; value?: number; suffix?: string; label?: string; missing?: boolean; source?: string; amp?: number[]; expr?: string };
export type SProps = { scenes: Scene[]; slug: string; persona?: any; bg?: string; floor?: string; handle?: string };
export const calcShortGen = ({ props }: { props: SProps }) => ({ durationInFrames: props.scenes.reduce((a, s) => a + s.dur, 0) });
const ci = (v: number, a: number, b: number, x: number, y: number, e?: any) => interpolate(v, [a, b], [x, y], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: e });
const EM: Record<string, { b: number; e: number }> = { neutral: { b: 0, e: 1 }, angry: { b: -0.6, e: 1 }, shocked: { b: 0.85, e: 1.18 }, worried: { b: 0.6, e: 1.06 }, skeptical: { b: -0.3, e: 0.9 }, happy: { b: 0.18, e: 1 } };
const House: React.FC<{ miss?: boolean }> = ({ miss }) => (<g><rect x={-34} y={-2} width={68} height={60} fill={miss ? "none" : GOLD} stroke={INK} strokeWidth={7} strokeDasharray={miss ? "10 10" : "0"} /><path d="M-44,0 L0,-46 L44,0" fill={miss ? "none" : "#B5702A"} stroke={INK} strokeWidth={7} strokeDasharray={miss ? "10 10" : "0"} strokeLinejoin="round" /></g>);

const Karaoke: React.FC<{ nar: string; l: number; d: number; top?: number }> = ({ nar, l, d, top = 250 }) => {
  const w = nar.split(/\s+/); const ch: string[][] = [];
  const WEAK = new Set(["a", "an", "the", "and", "but", "or", "to", "of", "in", "on", "for", "with", "is", "are", "was", "were", "that", "it", "its", "at", "as", "by", "so", "if", "my", "your", "his", "her", "their", "our"]);
  { let i = 0; while (i < w.length) { let end = Math.min(i + 3, w.length); if (end < w.length && end - i > 1 && WEAK.has(w[end - 1].toLowerCase().replace(/[.,!?;:]$/, ""))) end--; ch.push(w.slice(i, end)); i = end; } }
  const tot = ch.reduce((a, c) => a + c.join(" ").length, 0) || 1; const aF = d - 12; let t = 0, cur = ch[0] || [], ct = 0, cd = 1;
  for (const c of ch) { const dd = aF * c.join(" ").length / tot; if (l >= t && l < t + dd) { cur = c; ct = t; cd = dd; break; } t += dd; }
  // karaoke: highlight TỪ đang đọc (vàng + nảy); CAPS = đỏ; còn lại đậm
  const wl = cur.reduce((a, x) => a + x.length, 0) || 1; let wt = ct, active = 0;
  for (let j = 0; j < cur.length; j++) { const wd = cd * cur[j].length / wl; if (l >= wt && l < wt + wd) { active = j; break; } wt += wd; if (l >= wt) active = j; }
  return <div style={{ position: "absolute", top, left: 60, right: 60, textAlign: "center" }}>{cur.map((x, i) => { const caps = x.replace(/[^A-Z0-9]/g, "").length >= Math.max(2, x.length - 2); const on = i === active; return <span key={i} style={{ fontSize: (caps ? 112 : 86) * (on ? 1.12 : 1), fontWeight: 900, color: on ? "#FFD21E" : caps ? RED : INK, WebkitTextStroke: (on || caps) ? "6px #161616" : ("0" as any), margin: "0 10px", lineHeight: 1.12, display: "inline-block" }}>{x}</span>; })}</div>;
};

const World: React.FC<{ s: Scene; l: number; persona: any }> = ({ s, l, persona }) => {
  const amp = s.amp ? (s.amp[Math.min(l, s.amp.length - 1)] || 0) : 0;
  let sm = 0, cnt = 0; if (s.amp) for (let k = -5; k <= 5; k++) { const i = l + k; if (i >= 0 && i < s.amp.length) { sm += s.amp[i]; cnt++; } }
  const gAmp = cnt ? sm / cnt : 0; const em = EM[s.expr || (s.type === "num" ? "shocked" : "neutral")] || EM.neutral;
  const gR = 15 + gAmp * 42 + Math.sin(l / 30) * 7, gL = 11 + gAmp * 18 + Math.sin(l / 38 + 2) * 6;
  return (
    <svg width={1080} height={1920} viewBox="0 0 1080 1920" style={{ position: "absolute", inset: 0 }}>
      <StickDefs boil={Math.floor(l / 4) % 3} />
      <rect x={-200} y={1600} width={1480} height={500} fill={"#00000018"} />
      {s.type === "num" && <text x={540} y={860} textAnchor="middle" fontSize={260} fontWeight={900} fill={GREEN} stroke={INK} strokeWidth={9} style={{ paintOrder: "stroke" } as any}>{Math.round(ci(l, 16, 70, 0, s.value || 0))}{s.suffix}</text>}
      {s.type === "houses" && (() => { const N = 5, sh = Math.floor(ci(l, 10, 80, 0, N)); return <g transform="translate(200,820)">{Array.from({ length: N }).map((_, j) => j < sh ? <g key={j} transform={`translate(${(j % 3) * 260},${Math.floor(j / 3) * 240}) scale(1.5)`}><House miss={j >= 3} /></g> : null)}</g>; })()}
      <g transform="translate(540,1560) scale(1.14)"><ellipse cx={0} cy={116} rx={100} ry={20} fill="#000" opacity={0.16} /><Story {...persona} brow={em.b} eyeWide={em.e} mouthOpen={amp} armL={gL} armR={gR} lookY={-0.15} /></g>
    </svg>
  );
};

export const ShortGen: React.FC<SProps> = ({ scenes, slug, persona = {}, handle = "", bg = "#F3E7C0" }) => {
  const f = useCurrentFrame(); const st: number[] = []; scenes.reduce((a, s, i) => (st[i] = a, a + s.dur), 0);
  let i = 0; for (let k = 0; k < scenes.length; k++) if (f >= st[k]) i = k; const s = scenes[i], l = f - st[i];
  return (
    <AbsoluteFill style={{ background: bg, fontFamily: "'Poppins',Arial" }}>
      <World s={s} l={l} persona={persona} />
      <Karaoke nar={s.nar} l={l} d={s.dur} top={s.type === "talk" ? 760 : 250} />
      {s.type === "num" && s.label && <div style={{ position: "absolute", top: 958, width: "100%", textAlign: "center", fontSize: 50, fontWeight: 800, color: INK }}>{s.label}</div>}
      {/* VÙNG AN TOÀN mobile (chuẩn short chuyên nghiệp): handle đưa xuống dưới top-UI; BỎ source trên màn hình (nguồn đã ở description/meta) tránh bị UI che + đè host */}
      {scenes.map((sc, j) => <Sequence key={j} from={st[j]} durationInFrames={sc.dur}><Audio src={staticFile(`${slug}/${sc.audio}`)} /></Sequence>)}
    </AbsoluteFill>
  );
};
