import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, interpolate, useCurrentFrame, Easing } from "remotion";
import { StickFigure, StickDefs } from "./StickFigure";
import { Story } from "./Story";
import { Scenery, BgVariant } from "./Scenery";

// 🎬 LONG-FORM data-driven (BROKE). Đọc scenes[] từ props.json -> render theo type. Tái dùng cho mọi video.
const CREAM = "#F3E7C0", FLOOR = "#9C9A93", INK = "#161616", GREEN = "#2FA84F", RED = "#E4562B", GOLD = "#D79A34";
type Scene = { type: string; audio: string; dur: number; nar: string; value?: number; suffix?: string; label?: string; pct?: number; num?: string; title?: string; expr?: string; missing?: boolean; source?: string; bars?: [string, number][]; amp?: number[] };
export type LProps = { scenes: Scene[]; slug: string; persona?: any; bg?: string; floor?: string; handle?: string };
export const calcLong = ({ props }: { props: LProps }) => ({ durationInFrames: props.scenes.reduce((a, s) => a + s.dur, 0) });
const BROKE_PERSONA = { outfit: "tie", shirt: "#7FB0D8", tie: "#1F7A3A", hair: "#2A2038", hairStyle: "short" };
const ci = (v: number, a: number, b: number, x: number, y: number, e?: any) => interpolate(v, [a, b], [x, y], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: e });
const DATA_T = new Set(["stat", "pct", "crowd", "houses", "seesaw", "bars", "chart"]);
const bgOf = (type: string, idx: number): BgVariant => type === "chapter" ? "card" : type === "payoff" ? "night" : DATA_T.has(type) ? "spot" : (["room", "street", "park", "night"] as BgVariant[])[idx % 4];

const Head: React.FC<{ c: string }> = ({ c }) => <g><circle r={20} fill={c} stroke={INK} strokeWidth={5} /><circle cx={-6} cy={-2} r={3} fill={INK} /><circle cx={6} cy={-2} r={3} fill={INK} /></g>;
const House: React.FC<{ miss?: boolean }> = ({ miss }) => (<g><rect x={-30} y={-2} width={60} height={54} fill={miss ? "none" : GOLD} stroke={INK} strokeWidth={6} strokeDasharray={miss ? "9 9" : "0"} /><path d="M-40,0 L0,-42 L40,0" fill={miss ? "none" : "#B5702A"} stroke={INK} strokeWidth={6} strokeDasharray={miss ? "9 9" : "0"} strokeLinejoin="round" /></g>);
const Pie: React.FC<{ pct: number; r?: number }> = ({ pct, r = 160 }) => { const a = (pct / 100) * 2 * Math.PI, x = r * Math.sin(a), y = -r * Math.cos(a), lg = pct > 50 ? 1 : 0; return <g><circle r={r} fill="#fff" stroke={INK} strokeWidth={8} />{pct > 0.5 && <path d={`M0,0 L0,${-r} A${r},${r} 0 ${lg} 1 ${x.toFixed(1)},${y.toFixed(1)} Z`} fill={GREEN} stroke={INK} strokeWidth={6} strokeLinejoin="round" />}</g>; };

const Karaoke: React.FC<{ nar: string; l: number; d: number }> = ({ nar, l, d }) => {
  const words = nar.split(/\s+/); const chunks: string[][] = [];
  for (let i = 0; i < words.length; i += 4) chunks.push(words.slice(i, i + 4));
  const totC = chunks.reduce((a, c) => a + c.join(" ").length, 0) || 1; const audF = d - 8; let t = 0, cur = chunks[0] || [], ct = 0, cd = 1;
  for (const c of chunks) { const dd = audF * c.join(" ").length / totC; if (l >= t && l < t + dd) { cur = c; ct = t; cd = dd; break; } t += dd; }
  // karaoke: highlight TỪ đang đọc trong cụm (theo tỉ lệ độ dài từ)
  const wl = cur.reduce((a, w) => a + w.length, 0) || 1; let wt = ct, active = 0;
  for (let j = 0; j < cur.length; j++) { const wd = cd * cur[j].length / wl; if (l >= wt && l < wt + wd) { active = j; break; } wt += wd; if (l >= wt) active = j; }
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 50, textAlign: "center" }}>
      <span style={{ background: "rgba(20,20,20,0.82)", padding: "8px 22px", borderRadius: 8, lineHeight: 1.5, boxDecorationBreak: "clone" as any, WebkitBoxDecorationBreak: "clone" as any }}>
        {cur.map((w, j) => <span key={j} style={{ fontSize: 44, fontWeight: 800, color: j === active ? "#FFD21E" : "#fff", display: "inline-block", transform: j === active ? "scale(1.12)" : "scale(1)", margin: "0 6px" }}>{w}</span>)}
      </span>
    </div>
  );
};

const Actor: React.FC<{ x?: number; y?: number; scale?: number; pose: any; dark?: boolean; persona?: any }> = ({ x = 960, y = 793, scale = 1, pose, dark, persona = BROKE_PERSONA }) => (
  <g transform={`translate(${x},${y}) scale(${scale})`}>
    <ellipse cx={0} cy={114} rx={96} ry={20} fill="#000" opacity={dark ? 0.35 : 0.16} />{/* bóng tiếp đất -> tách khỏi nền */}
    <Story {...pose} dark={dark} {...persona} />{/* persona theo kênh */}
  </g>
);

const SceneView: React.FC<{ s: Scene; l: number; dark?: boolean; persona?: any }> = ({ s, l, dark, persona = BROKE_PERSONA }) => {
  const amp = s.amp ? (s.amp[Math.min(l, s.amp.length - 1)] || 0) : 0;      // biên độ audio frame này (lip-sync)
  const expr = s.expr || "neutral";
  // 😃 biểu cảm khớp nội dung: {brow, eyeWide}
  const EM: Record<string, { b: number; e: number }> = {
    neutral: { b: 0, e: 1 }, angry: { b: -0.6, e: 1 }, frown: { b: -0.5, e: 1 }, shocked: { b: 0.85, e: 1.18 },
    worried: { b: 0.6, e: 1.06 }, skeptical: { b: -0.3, e: 0.9 }, happy: { b: 0.18, e: 1 }, smile: { b: 0.18, e: 1 }, sad: { b: 0.5, e: 0.95 },
  };
  const em = EM[expr] || EM.neutral;
  // cử chỉ tay TỰ NHIÊN: biên độ đã LÀM MƯỢT (trung bình cửa sổ) -> không giật; tay lệch pha, bất đối xứng, idle sway
  let sm = 0, cnt = 0; if (s.amp) for (let k = -5; k <= 5; k++) { const i = l + k; if (i >= 0 && i < s.amp.length) { sm += s.amp[i]; cnt++; } }
  const gAmp = cnt ? sm / cnt : 0;
  const gR = 15 + gAmp * 40 + Math.sin(l / 32) * 7 + Math.sin(l / 17 + 1) * 3;  // tay phải: cử chỉ chính
  const gL = 11 + gAmp * 18 + Math.sin(l / 39 + 2) * 6;                          // tay trái: phụ, lệch pha
  const nod = -gAmp * 0.16 + Math.sin(l / 42) * 0.12;                            // gật đầu êm
  if (s.type === "chapter") {
    const p = ci(l, 4, 24, 0, 1, Easing.out(Easing.cubic));
    return (<><Actor x={290} y={860} scale={0.5} pose={{ brow: 0, mouthOpen: amp, lookX: 0.5, lookY: nod, walk: l < 30 ? 1 : 0 }} dark={dark} persona={persona} />
      <foreignObject x={0} y={190} width={1920} height={420}><div style={{ display: "flex", flexDirection: "column", alignItems: "center", opacity: p, transform: `translateY(${(1 - p) * 30}px)` }} {...{ xmlns: "http://www.w3.org/1999/xhtml" } as any}>
        {/* nền "card" sạch tô màu -> tiêu đề crisp + gạch nhấn (bắt mắt, không muddy) */}
        <div style={{ fontSize: 56, fontWeight: 900, color: GREEN, WebkitTextStroke: "6px #161616", letterSpacing: 4, fontFamily: "'Poppins',Arial" } as any}>CHAPTER {s.num}</div>
        <div style={{ fontSize: (s.title || "").length > 13 ? 108 : 148, fontWeight: 900, color: "#FFD21E", WebkitTextStroke: "9px #161616", fontFamily: "'Poppins',Arial", lineHeight: 1.02, marginTop: 6 } as any}>{s.title}</div>
        <div style={{ width: 220, height: 14, background: RED, border: "5px solid #161616", borderRadius: 10, marginTop: 22, transform: `scaleX(${p})` }} />
      </div></foreignObject></>);
  }
  if (s.type === "stat") return (<><Actor x={520} pose={{ brow: 0.6, eyeWide: 1.12, mouthOpen: amp, lookX: 0.5, lookY: nod, armL: gL, armR: gR }} persona={persona} />
    <foreignObject x={760} y={300} width={1100} height={400}><div style={{ textAlign: "center", fontFamily: "'Poppins',Arial" }} {...{ xmlns: "http://www.w3.org/1999/xhtml" } as any}><div style={{ fontSize: 200, fontWeight: 900, color: RED, WebkitTextStroke: "8px #161616" } as any}>{Math.round(ci(l, 10, 60, 0, s.value || 0))}{s.suffix}</div><div style={{ fontSize: 46, fontWeight: 800, color: INK }}>{s.label}</div></div></foreignObject></>);
  if (s.type === "pct") return (<><Actor x={520} pose={{ brow: 0.6, eyeWide: 1.12, mouthOpen: amp, lookX: 0.5, lookY: nod, armL: gL, armR: gR }} persona={persona} /><g transform="translate(1260,470)"><Pie pct={ci(l, 12, 60, 0, s.pct || 33, Easing.out(Easing.cubic))} /></g></>);
  if (s.type === "crowd") { const N = 24, sh = Math.floor(ci(l, 8, 70, 0, N)); return (<><g transform="translate(500,300)">{Array.from({ length: N }).map((_, j) => j < sh ? <g key={j} transform={`translate(${(j % 8) * 130},${Math.floor(j / 8) * 150}) scale(1.2)`}><Head c={j % 2 ? "#fff" : RED} /></g> : null)}</g><foreignObject x={0} y={760} width={1920} height={120}><div style={{ textAlign: "center", fontSize: 110, fontWeight: 900, color: RED, WebkitTextStroke: "7px #161616", fontFamily: "'Poppins',Arial", opacity: ci(l, 50, 70, 0, 1) } as any}>{s.label}</div></foreignObject></>); }
  if (s.type === "houses") { const N = 7, sh = Math.floor(ci(l, 10, 90, 0, N)); return (<><g transform="translate(360,620)">{Array.from({ length: N }).map((_, j) => j < sh ? <g key={j} transform={`translate(${j * 200},0) scale(1.15)`}><House miss={j >= 4} /></g> : null)}</g><foreignObject x={0} y={200} width={1920} height={160}><div style={{ textAlign: "center", fontSize: 120, fontWeight: 900, color: RED, WebkitTextStroke: "7px #161616", fontFamily: "'Poppins',Arial" } as any}>{s.label}</div></foreignObject></>); }
  if (s.type === "chart") { const rh = ci(l, 12, 70, 0, 360, Easing.out(Easing.cubic)), ih = ci(l, 12, 70, 0, 90, Easing.out(Easing.cubic)); return (<g transform="translate(760,760)">
      <rect x={0} y={-rh} width={160} height={rh} fill={RED} stroke={INK} strokeWidth={6} /><rect x={300} y={-ih} width={160} height={ih} fill={GREEN} stroke={INK} strokeWidth={6} />
      <foreignObject x={-40} y={20} width={240} height={70}><div style={{ textAlign: "center", fontSize: 40, fontWeight: 800, color: INK, fontFamily: "'Poppins',Arial" } as any}>RENT</div></foreignObject>
      <foreignObject x={260} y={20} width={240} height={70}><div style={{ textAlign: "center", fontSize: 40, fontWeight: 800, color: INK, fontFamily: "'Poppins',Arial" } as any}>INCOME</div></foreignObject></g>); }
  if (s.type === "bars") {
    const bars = s.bars || []; const max = Math.max(...bars.map((b) => b[1]), 1);
    return (<foreignObject x={260} y={230} width={1400} height={700}><div style={{ fontFamily: "'Poppins',Arial" }} {...{ xmlns: "http://www.w3.org/1999/xhtml" } as any}>
      {bars.map((b, j) => { const w = ci(l, 10 + j * 8, 60 + j * 8, 0, (b[1] / max) * 900, Easing.out(Easing.cubic)); const top = b[0].includes("avg"); return (
        <div key={j} style={{ display: "flex", alignItems: "center", marginBottom: 24 }}>
          <div style={{ width: 340, fontSize: 44, fontWeight: 800, color: INK, textAlign: "right", paddingRight: 24 }}>{b[0]}</div>
          <div style={{ width: w, height: 74, background: top ? GREEN : RED, border: "5px solid #161616", borderRadius: 8 }} />
          <div style={{ fontSize: 44, fontWeight: 900, color: top ? GREEN : RED, marginLeft: 16 }}>{Math.round(ci(l, 10 + j * 8, 60 + j * 8, 0, b[1]))}%</div>
        </div>); })}
      <div style={{ fontSize: 30, color: "#6b6457", marginTop: 10, marginLeft: 340 }}>{s.label}</div>
    </div></foreignObject>);
  }
  if (s.type === "climb") {
    // 🚀 DATA-REACTIVE: nhân vật LEO cầu thang tiền thuê tăng theo năm (data = thế giới, tác động lên nhân vật)
    const steps = s.bars || [["2005", 900], ["2010", 1150], ["2015", 1350], ["2020", 1600], ["2025", 1900]] as [string, number][];
    const N = steps.length, sw = 300, baseX = 340, baseY = 880, rise = 130;
    const prog = ci(l, 15, N * 26, 0, N - 1, Easing.inOut(Easing.cubic)); // vị trí leo
    const ci2 = Math.min(Math.floor(prog), N - 1); const fx = baseX + ci2 * sw + 120; const fy = baseY - ci2 * rise - 8;
    return (<>
      {steps.map((st, j) => { const x = baseX + j * sw, y = baseY - j * rise; const up = ci(l, 6 + j * 4, 24 + j * 4, 0, 1); return (
        <g key={j} opacity={up} filter="url(#handdrawn)">
          <rect x={x} y={y} width={sw + 4} height={baseY - y + 200} fill={j === N - 1 ? RED : GOLD} stroke={INK} strokeWidth={7} />
          <foreignObject x={x} y={y + 12} width={sw} height={110}><div style={{ textAlign: "center", fontFamily: "'Poppins',Arial" }} {...{ xmlns: "http://www.w3.org/1999/xhtml" } as any}><div style={{ fontSize: 40, fontWeight: 900, color: "#fff", WebkitTextStroke: "3px #161616" } as any}>${st[1]}</div><div style={{ fontSize: 30, fontWeight: 800, color: "#161616" }}>{st[0]}</div></div></foreignObject>
        </g>); })}
      <g transform={`translate(${fx},${fy}) scale(0.62)`}><Story brow={0.3} mouthOpen={amp} armL={64} armR={40} lookY={-0.3} {...persona} /></g>
      <foreignObject x={1180} y={180} width={640} height={200}><div style={{ textAlign: "center", fontFamily: "'Poppins',Arial" }} {...{ xmlns: "http://www.w3.org/1999/xhtml" } as any}><div style={{ fontSize: 110, fontWeight: 900, color: RED, WebkitTextStroke: "7px #161616" } as any}>RENT ↑↑↑</div><div style={{ fontSize: 34, fontWeight: 700, color: INK }}>every year, another step</div></div></foreignObject>
    </>);
  }
  if (s.type === "seesaw") { const tilt = ci(l, 10, 50, 0, -12, Easing.out(Easing.cubic)); return (<g transform="translate(960,640)" filter="url(#handdrawn)"><path d="M0,120 L-70,260 L70,260 Z" fill={GOLD} stroke={INK} strokeWidth={6} /><g transform={`rotate(${tilt})`}><rect x={-520} y={100} width={1040} height={26} rx={12} fill="#C98A2E" stroke={INK} strokeWidth={6} />{Array.from({ length: 6 }).map((_, j) => <g key={j} transform={`translate(${-460 + (j % 3) * 70},${70 - Math.floor(j / 3) * 44})`}><Head c="#fff" /></g>)}<g transform="translate(420,54) scale(0.9)"><House /></g></g><foreignObject x={-960} y={-300} width={1920} height={120}><div style={{ textAlign: "center", fontSize: 96, fontWeight: 900, color: RED, WebkitTextStroke: "6px #161616", fontFamily: "'Poppins',Arial", opacity: ci(l, 55, 80, 0, 1) } as any}>PRICES ↑↑↑</div></foreignObject></g>); }
  if (s.type === "payoff") return (<foreignObject x={0} y={340} width={1920} height={400}><div style={{ textAlign: "center", fontFamily: "'Poppins',Arial" }} {...{ xmlns: "http://www.w3.org/1999/xhtml" } as any}><div style={{ fontSize: 120, fontWeight: 900, color: "#3FD968", WebkitTextStroke: "6px #161616" } as any}>BROKE</div><div style={{ fontSize: 44, fontWeight: 800, color: "#F5F3FF" }}>where your money really goes</div><div style={{ fontSize: 36, color: "#C9BEE6", marginTop: 16 }}>▶ Subscribe · @brokeexplained</div></div></foreignObject>);
  // talk
  return <Actor x={960} pose={{ brow: em.b, eyeWide: em.e, mouthOpen: amp, lookX: Math.sin(l / 50) * 0.3, lookY: nod, armL: gL, armR: gR, mouth: expr === "smile" || expr === "happy" ? "smile" : "neutral" }} dark={dark} persona={persona} />;
};

export const LongBroke: React.FC<LProps> = ({ scenes, slug, persona = BROKE_PERSONA, bg = CREAM, floor = FLOOR, handle = "@brokeexplained" }) => {
  const f = useCurrentFrame();
  const starts: number[] = []; scenes.reduce((a, s, i) => (starts[i] = a, a + s.dur), 0);
  let idx = 0; for (let k = 0; k < scenes.length; k++) if (f >= starts[k]) idx = k;
  const s = scenes[idx], l = f - starts[idx];
  const TOTAL = scenes.reduce((a, x) => a + x.dur, 0);
  return (
    <AbsoluteFill style={{ background: bg, fontFamily: "'Poppins',Arial" }}>
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>
        <StickDefs boil={Math.floor(f / 4) % 3} />
        <Scenery v={bgOf(s.type, idx)} frame={f} bg={bg} floor={floor} accent={GOLD} />
        <SceneView s={s} l={l} dark={bgOf(s.type, idx) === "night"} persona={persona} />
      </svg>
      {s.type !== "chapter" && s.type !== "payoff" && <Karaoke nar={s.nar} l={l} d={s.dur} />}
      {s.source && <div style={{ position: "absolute", right: 28, bottom: 18, fontSize: 22, color: "#6b6457" }}>Source: {s.source} (approx.)</div>}
      {(s.type === "pct" || s.type === "crowd" || s.type === "houses" || s.type === "stat") && <div style={{ position: "absolute", right: 28, bottom: 18, fontSize: 22, color: "#6b6457" }}>Source: Harvard JCHS / U.S. Census / NLIHC (approx.)</div>}
      {/* nhạc nền fade in/out: video ngắn (TOTAL<=90 frame, vd bản QC render ít cảnh) làm TOTAL-50 < 40
          -> mốc [0,40,TOTAL-50,TOTAL] không tăng dần -> Remotion interpolate() throw NGAY TRONG callback volume (crash cả render).
          Tách thành 2 khoảng riêng (fade-in / fade-out) rồi lấy min, giống pattern an toàn trong Cinematic.tsx. */}
      <Audio src={staticFile("music/broke_pad.mp3")} loop volume={(fr) => Math.min(
        interpolate(fr, [0, 40], [0, 0.16], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        interpolate(fr, [Math.max(41, TOTAL - 50), Math.max(42, TOTAL)], [0.16, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
      )} />
      {scenes.map((sc, j) => <Sequence key={j} from={starts[j]} durationInFrames={sc.dur}><Audio src={staticFile(`${slug}/${sc.audio}`)} /></Sequence>)}
    </AbsoluteFill>
  );
};
