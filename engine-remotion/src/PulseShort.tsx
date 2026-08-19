import { AbsoluteFill, Sequence, Audio, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import React from "react";

// KÊNH #6 PULSE — so sánh CƯỜNG ĐỘ giác quan thật (dB/lux/°F/g/...) qua ĐỒNG HỒ ĐO kim analog.
// Motif riêng hẳn: gauge bán nguyệt (kim vật lý spring, đổi màu lạnh->nóng), redline rung+shockwave khi extreme.

type Word = { t: number; d: number; w: string };
export type PulseItem = { label: string; emoji?: string; value: number; disp?: string; extreme?: boolean; vo?: string };
export type PulseProps = {
  title?: string; handle?: string; color?: string; accent?: string;
  unit: string; maxScale: number; items: PulseItem[];
  audio?: string; music?: string; subs?: Word[]; sfx?: boolean;
};

const FPS = 30;
const W = 1080, H = 1920;

// ---- màu lạnh -> nóng (cường độ thấp -> cực đại) ----
const STOPS: [number, string][] = [
  [0, "#22D3EE"],   // cyan lạnh
  [0.35, "#34D399"], // xanh lá
  [0.6, "#FACC15"],  // vàng
  [0.82, "#F97316"], // cam
  [1, "#EF4444"],   // đỏ nóng
];
const hex2rgb = (h: string): [number, number, number] => {
  h = h.replace("#", ""); if (h.length === 3) h = h.split("").map((c) => c + c).join("");
  const n = parseInt(h, 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};
const rgb2hex = (r: number, g: number, b: number) => "#" + [r, g, b].map((v) => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, "0")).join("");
const colorAt = (t: number) => {
  t = Math.max(0, Math.min(1, t));
  for (let i = 0; i < STOPS.length - 1; i++) {
    const [t0, c0] = STOPS[i], [t1, c1] = STOPS[i + 1];
    if (t >= t0 && t <= t1) {
      const k = (t - t0) / (t1 - t0 || 1);
      const [r0, g0, b0] = hex2rgb(c0), [r1, g1, b1] = hex2rgb(c1);
      return rgb2hex(r0 + (r1 - r0) * k, g0 + (g1 - g0) * k, b0 + (b1 - b0) * k);
    }
  }
  return STOPS[STOPS.length - 1][1];
};

// ---- hình học gauge: quạt bán nguyệt hơi loe (200° sweep), kim quay -100°..+100° (CSS/SVG rotate cùng chiều) ----
const GX = 540, GY = 1230, GR = 420, SWEEP = 200;
const rotForT = (t: number) => -100 + SWEEP * Math.max(0, Math.min(1, t));
const mathAngle = (rotDeg: number) => 90 - rotDeg;
const polar = (cx: number, cy: number, r: number, deg: number) => {
  const rad = (deg * Math.PI) / 180; return { x: cx + r * Math.cos(rad), y: cy - r * Math.sin(rad) };
};
const arcPath = (t0: number, t1: number, r: number, steps = 72) => {
  const pts: string[] = [];
  for (let i = 0; i <= steps; i++) {
    const t = t0 + (t1 - t0) * (i / steps);
    const p = polar(GX, GY, r, mathAngle(rotForT(t)));
    pts.push(`${i === 0 ? "M" : "L"}${p.x.toFixed(1)} ${p.y.toFixed(1)}`);
  }
  return pts.join(" ");
};

const idur = (it: PulseItem, s: number) => s + (it.extreme ? 0.7 : 0);

export const calcPulse = ({ props }: any) => {
  const its: PulseItem[] = props.items || [];
  const isec = 1.7, isc = 2.2, tail = 1.6;
  const total = its.reduce((a, it) => a + idur(it, isc), 0);
  return { durationInFrames: Math.round((isec + total + tail) * FPS), fps: FPS, width: W, height: H };
};

// ---- kim (needle): hình thoi thon, đế rộng ở trục quay, nhọn ở đầu, có đuôi đối trọng ngắn ----
const Needle: React.FC<{ rotDeg: number; t: number; hot: boolean }> = ({ rotDeg, t, hot }) => {
  const A = mathAngle(rotDeg);
  const dir = { x: Math.cos((A * Math.PI) / 180), y: -Math.sin((A * Math.PI) / 180) };
  const perp = { x: -dir.y, y: dir.x };
  const len = GR - 44, tail = 46, hw = 12, thw = 22;
  const tip = { x: GX + dir.x * len, y: GY + dir.y * len };
  const tailP = { x: GX - dir.x * tail, y: GY - dir.y * tail };
  const baseR = { x: GX + perp.x * hw, y: GY + perp.y * hw };
  const baseL = { x: GX - perp.x * hw, y: GY - perp.y * hw };
  const tailR = { x: tailP.x + perp.x * thw, y: tailP.y + perp.y * thw };
  const tailL = { x: tailP.x - perp.x * thw, y: tailP.y - perp.y * thw };
  const col = colorAt(t);
  return (
    <g filter="url(#needleGlow)">
      <polygon points={`${tip.x},${tip.y} ${baseR.x},${baseR.y} ${tailR.x},${tailR.y} ${tailL.x},${tailL.y} ${baseL.x},${baseL.y}`} fill={col} opacity={0.97} />
      {hot ? <circle cx={tip.x} cy={tip.y} r={10} fill="#FFF7ED" opacity={0.9} /> : null}
    </g>
  );
};

const GaugeDefs: React.FC = () => (
  <defs>
    <linearGradient id="pulseGrad" x1={GX - GR} y1={GY} x2={GX + GR} y2={GY} gradientUnits="userSpaceOnUse">
      {STOPS.map(([t, c], i) => <stop key={i} offset={`${t * 100}%`} stopColor={c} />)}
    </linearGradient>
    <radialGradient id="hubGrad" cx="35%" cy="30%" r="75%">
      <stop offset="0%" stopColor="#3a4152" /><stop offset="55%" stopColor="#161b26" /><stop offset="100%" stopColor="#05070c" />
    </radialGradient>
    <filter id="arcGlow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="10" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
    </filter>
    <filter id="needleGlow" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="6" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
    </filter>
  </defs>
);

const GaugeTicks: React.FC<{ maxScale: number; unit: string }> = ({ maxScale, unit }) => {
  const n = 8;
  const items = Array.from({ length: n + 1 }, (_, i) => i / n);
  return (
    <g>
      {items.map((t, i) => {
        const major = i % 2 === 0;
        const a = mathAngle(rotForT(t));
        const p0 = polar(GX, GY, GR - (major ? 34 : 22), a);
        const p1 = polar(GX, GY, GR + 6, a);
        const lp = polar(GX, GY, GR + (major ? 58 : 44), a);
        return (
          <g key={i}>
            <line x1={p0.x} y1={p0.y} x2={p1.x} y2={p1.y} stroke={major ? "#c7cfdd" : "#5b6478"} strokeWidth={major ? 5 : 3} strokeLinecap="round" opacity={major ? 0.85 : 0.5} />
            {major ? <text x={lp.x} y={lp.y + 8} textAnchor="middle" fontSize={26} fontWeight={800} fill="#8892a6" fontFamily="'Poppins',Arial">{Math.round(t * maxScale)}</text> : null}
          </g>
        );
      })}
      <text x={GX} y={GY + 96} textAnchor="middle" fontSize={30} fontWeight={800} letterSpacing={3} fill="#5b6478" fontFamily="'Poppins',Arial">{unit.toUpperCase()}</text>
    </g>
  );
};

const GaugeItem: React.FC<{ it: PulseItem; accent: string; unit: string; maxScale: number; dur: number }> = ({ it, accent, unit, maxScale, dur }) => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const targetT = Math.max(0, Math.min(1, it.value / maxScale));

  const enter = spring({ frame: f, fps, config: { damping: 13, stiffness: 150 } });
  const swing = spring({ frame: f, fps, config: { damping: 8.5, mass: 0.85, stiffness: 95 } });
  let needleT = swing * targetT;

  const settleF = 20;
  const jitterEnd = Math.max(settleF + 4, dur - 6);
  const inJitter = !!it.extreme && f > settleF && f < jitterEnd;
  const jp = inJitter ? Math.min(1, (f - settleF) / Math.max(1, jitterEnd - settleF)) : 0;
  const jitterDeg = inJitter ? Math.sin(f * 2.35) * 7 * (1 - 0.35 * jp) + Math.sin(f * 3.9) * 3 * (1 - 0.35 * jp) : 0;

  const rotDeg = rotForT(Math.min(1.08, needleT)) + jitterDeg;
  const clampT = Math.max(0, Math.min(1, needleT));
  const col = colorAt(clampT);
  const hot = clampT > 0.86;

  const numberPop = spring({ frame: f - 10, fps, config: { damping: 14, stiffness: 170 } });
  const labelPop = spring({ frame: f - 2, fps, config: { damping: 14, stiffness: 170 } });

  // shockwave rings khi redline: 2 vòng lệch pha, lặp theo modulo
  const ringPhase = inJitter ? (f - settleF) % 30 : -1;
  const ring2Phase = inJitter ? (f - settleF + 15) % 30 : -1;
  const ring = (phase: number) => {
    if (phase < 0) return null;
    const rt = phase / 30; const r = 60 + rt * (GR + 120); const op = (1 - rt) * 0.5;
    return <circle cx={GX} cy={GY - 40} r={r} fill="none" stroke={accent} strokeWidth={6} opacity={op} />;
  };

  return (
    <>
      {/* emoji + label */}
      <div style={{ position: "absolute", top: 300, left: 0, right: 0, textAlign: "center", opacity: labelPop, transform: `translateY(${(1 - labelPop) * 26}px)` }}>
        <div style={{ fontSize: 128, lineHeight: 1, filter: `drop-shadow(0 8px 20px #0009)` }}>{it.emoji || "🔊"}</div>
        <div style={{ color: "#fff", fontWeight: 900, fontSize: 56, marginTop: 10, textShadow: "0 4px 18px #000c", padding: "0 60px", textWrap: "balance" as any }}>{it.label}</div>
      </div>

      {/* GAUGE SVG */}
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", top: 0, left: 0 }}>
        <GaugeDefs />
        {inJitter ? ring(ringPhase) : null}
        {inJitter ? ring(ring2Phase) : null}
        {/* track nền */}
        <path d={arcPath(0, 1, GR)} fill="none" stroke="#1b2230" strokeWidth={46} strokeLinecap="round" opacity={0.9} />
        {/* progress (kim đã "quét" tới đâu) */}
        <path d={arcPath(0, clampT)} fill="none" stroke="url(#pulseGrad)" strokeWidth={40} strokeLinecap="round" filter="url(#arcGlow)" opacity={0.95} />
        <GaugeTicks maxScale={maxScale} unit={unit} />
        <Needle rotDeg={rotDeg} t={clampT} hot={hot} />
        {/* trục (hub) */}
        <circle cx={GX} cy={GY} r={40} fill="url(#hubGrad)" stroke={col} strokeWidth={5} filter="url(#needleGlow)" />
        <circle cx={GX} cy={GY} r={12} fill={col} />
      </svg>

      {/* số đọc lớn */}
      <div style={{ position: "absolute", top: 1420, left: 0, right: 0, textAlign: "center", transform: `scale(${0.6 + numberPop * 0.4})`, opacity: numberPop }}>
        <div style={{ display: "inline-block", background: `${col}22`, border: `2.5px solid ${col}`, borderRadius: 24, padding: "14px 42px", boxShadow: `0 0 ${hot ? 60 : 26}px ${col}88` }}>
          <span style={{ color: "#fff", fontWeight: 900, fontSize: 92, textShadow: `0 0 30px ${col}aa`, fontFamily: "'Poppins',Arial" }}>{it.disp || `${it.value.toLocaleString()} ${unit}`}</span>
        </div>
        {it.extreme ? (
          <div style={{ marginTop: 18, color: accent, fontWeight: 900, fontSize: 34, letterSpacing: 3, opacity: inJitter ? (Math.sin(f * 1.6) > 0 ? 1 : 0.35) : 1, textShadow: `0 0 18px ${accent}` }}>⚠ REDLINE</div>
        ) : null}
      </div>
    </>
  );
};

export const PulseShort: React.FC<PulseProps> = (props) => {
  const { title = "HOW INTENSE?", handle = "@pulseusa", color = "#EA580C", accent = "#EA580C",
    unit, maxScale, items = [], audio, music, sfx = true } = props;
  const f = useCurrentFrame(); const { fps } = useVideoConfig();

  const introSec = 1.7, itemSec = 2.2;
  const introF = Math.round(introSec * fps);
  const durs = items.map((it) => Math.round(idur(it, itemSec) * fps));
  const starts: number[] = []; let acc = introF;
  for (const d of durs) { starts.push(acc); acc += d; }
  const introP = spring({ frame: f, fps, config: { damping: 12, stiffness: 140 } });

  // shake toàn màn hình khi item hiện tại đang ở pha redline
  let activeIdx = -1;
  for (let i = 0; i < items.length; i++) { if (f >= starts[i] && f < starts[i] + durs[i]) { activeIdx = i; break; } }
  let shakeX = 0, shakeY = 0;
  if (activeIdx >= 0 && items[activeIdx].extreme) {
    const lf = f - starts[activeIdx]; const settleF = 20; const jitterEnd = Math.max(settleF + 4, durs[activeIdx] - 6);
    if (lf > settleF && lf < jitterEnd) {
      const jp = Math.min(1, (lf - settleF) / Math.max(1, jitterEnd - settleF));
      shakeX = Math.sin(lf * 2.9) * 7 * (1 - 0.3 * jp); shakeY = Math.cos(lf * 3.6) * 5 * (1 - 0.3 * jp);
    }
  }

  return (
    <AbsoluteFill style={{ background: "radial-gradient(120% 90% at 50% 8%, #1a1210 0%, #0e0908 55%, #07050a 100%)", fontFamily: "'Poppins',Arial", overflow: "hidden" }}>
      <AbsoluteFill style={{ transform: `translate(${shakeX}px, ${shakeY}px)` }}>
        {/* TIÊU ĐỀ */}
        <div style={{ position: "absolute", top: 76, left: 0, right: 0, textAlign: "center", padding: "0 50px", zIndex: 3 }}>
          <div style={{ display: "inline-block", background: color, color: "#0a0c14", fontWeight: 900, fontSize: 28, letterSpacing: 2, padding: "8px 22px", borderRadius: 12 }}>🎚️ PULSE</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 62, lineHeight: 1.02, marginTop: 16, textShadow: "0 4px 24px #000c", textWrap: "balance" as any }}>{title}</div>
        </div>

        {/* ITEMS — mỗi item 1 Sequence riêng, gauge reset & kim quét lại từ đầu */}
        {items.map((it, i) => (
          <Sequence key={i} from={starts[i]} durationInFrames={durs[i] + (i === items.length - 1 ? Math.round(1.6 * fps) : 0)}>
            <GaugeItem it={it} accent={accent} unit={unit} maxScale={maxScale} dur={durs[i]} />
          </Sequence>
        ))}

        {/* INTRO overlay */}
        {f < introF ? (
          <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 42%, ${accent}22, #07050a 70%)`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", zIndex: 4 }}>
            <div style={{ fontSize: 150, transform: `scale(${introP})` }}>🎚️</div>
            <div style={{ color: "#fff", fontWeight: 900, fontSize: 76, marginTop: 8, textAlign: "center", padding: "0 60px", opacity: introP, textWrap: "balance" as any }}>{title}</div>
          </AbsoluteFill>
        ) : null}

        {/* SFX: whoosh khi kim bắt đầu quét, impact/alarm khi redline */}
        {sfx ? items.map((it, i) => (
          <React.Fragment key={"sfx" + i}>
            <Sequence from={starts[i]} durationInFrames={10}><Audio src={staticFile("sfx/whoosh.mp3")} volume={0.45} /></Sequence>
            {it.extreme ? <Sequence from={starts[i] + 18} durationInFrames={40}><Audio src={staticFile("sfx/impact.mp3")} volume={0.6} /></Sequence> : null}
          </React.Fragment>
        )) : null}

        <div style={{ position: "absolute", bottom: 50, left: 0, right: 0, textAlign: "center", color: "#ffffffcc", fontWeight: 800, fontSize: 32, textShadow: "0 2px 10px #000", zIndex: 3 }}>{handle}</div>
      </AbsoluteFill>
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
    </AbsoluteFill>
  );
};
