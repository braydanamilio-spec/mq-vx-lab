import React, { useEffect, useState } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring, Audio, staticFile, delayRender, continueRender, Img } from "remotion";
import { useAudioData, visualizeAudio } from "@remotion/media-utils";
import { StickFigure, THEMES } from "./StickAnim";
import { SceneBG } from "./SceneBG";
import { SceneGen, ARCH, PROPS as GEN_PROPS, PALETTES } from "./scenegen";
import { CONCEPTS } from "./Concepts";
import { Lottie } from "@remotion/lottie";

const clamp = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const ease = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
const lerp = (a: number, b: number, t: number) => a + (b - a) * clamp(t);
const D = (deg: number) => (deg * Math.PI) / 180;
const PT = (x: number, y: number, l: number, a: number): [number, number] => [x + l * Math.cos(D(a)), y + l * Math.sin(D(a))];

// simple continuous poses for host reactions
const POSE = {
  idle:  { armL: 100, foreL: 98, armR: 80, foreR: 82, legL: 96, shinL: 92, legR: 84, shinR: 88, headTilt: 0, lean: 0 },
  present:{ armL: 98, foreL: 92, armR: 40, foreR: 22, legL: 95, shinL: 91, legR: 85, shinR: 89, headTilt: 4, lean: 3 },
  point: { armL: 104, foreL: 104, armR: 8, foreR: -10, legL: 95, shinL: 91, legR: 85, shinR: 89, headTilt: 3, lean: 5 },
  shrug: { armL: 52, foreL: 15, armR: 128, foreR: 165, legL: 96, shinL: 92, legR: 84, shinR: 88, headTilt: 6, lean: 0 },
  shock: { armL: -55, foreL: -92, armR: 235, foreR: 272, legL: 100, shinL: 96, legR: 80, shinR: 84, headTilt: -4, lean: -5 },
  lean:  { armL: 96, foreL: 88, armR: 58, foreR: 42, legL: 98, shinL: 94, legR: 82, shinR: 86, headTilt: 9, lean: 13 },
} as any;
const live = (p: any, t: number, mo = 0) => { const s = (f: number, ph: number, a: number) => Math.sin(t * f + ph) * a; return { ...p, armR: p.armR + s(1.6, 0, 4), foreR: p.foreR + s(1.6, -0.55, 8), armL: p.armL + s(1.8, 1.1, 4), foreL: p.foreL + s(1.8, 0.5, 7), headTilt: p.headTilt + s(1.05, 0, 2.6) + mo * 4, lean: p.lean + s(0.85, 0.5, 3.2), legL: p.legL + s(0.85, .5, 1.4), legR: p.legR - s(0.85, .5, 1.4), shinL: p.shinL, shinR: p.shinR }; };

const HOST = { outfit: "suit" as const, glasses: true, tie: "#1D63C7", shirt: "#39454F", pants: "#222C3A", skin: "#F1B784", hair: "#3A2A20" };

// ---------- karaoke ----------
const Karaoke: React.FC<{ words: any[]; time: number; accent: string; bottom?: number }> = ({ words, time, accent, bottom = 250 }) => {
  if (!words?.length) return null;
  let ci = 0; for (let i = 0; i < words.length; i++) if (time >= words[i].t) ci = i;
  // CỬA SỔ ~5 từ quanh từ đang đọc (không hiện cả câu -> không tràn); không vượt ranh giới câu
  const si = words[ci].si;
  const lo = Math.max(0, ci - 2), hi = Math.min(words.length, ci + 3);
  const win = words.slice(lo, hi).filter((w) => w.si === si);
  return (
    <div style={{ position: "absolute", left: "50%", bottom, transform: "translateX(-50%)", width: "92%", maxWidth: 1200, display: "flex", justifyContent: "center" }}>
      <div style={{ background: "#0b1220f2", borderRadius: 16, padding: "12px 24px", boxShadow: "0 12px 34px #0006", border: `2px solid ${accent}66`, display: "flex", flexWrap: "wrap", justifyContent: "center", alignItems: "center", gap: "2px 8px", lineHeight: 1.25, maxWidth: "100%" }}>
        {win.map((w, i) => {
          const on = time >= w.t && time < w.t + w.d + 0.05;
          const pop = on ? Math.max(0, 1 - (time - w.t) / 0.13) : 0;   // 1->0 ngay khi từ bật lên
          const scl = 1 + pop * 0.34;                                   // nảy to rồi về (kinetic)
          return <span key={lo + i} style={{ fontFamily: "Poppins, sans-serif", fontWeight: 800, fontSize: 50, color: on ? accent : "#fff", display: "inline-block", transform: `scale(${scl}) translateY(${-pop * 5}px)`, textShadow: on ? `0 0 18px ${accent}88` : "none" }}>{w.w}</span>;
        })}
      </div>
    </div>
  );
};

// ---------- big stat (cold-open / reveal) ----------
const BigStat: React.FC<{ p: number; big: string; label: string; sub?: string; icon?: string; accent: string; ink?: string }> = ({ p, big, label, sub, icon, accent }) => {
  const s = spring({ frame: p * 30, fps: 30, config: { damping: 9, stiffness: 120, mass: 0.7 } });
  const numFont = big.length > 4 ? 190 : big.length > 2 ? 240 : 280; // fit 1080 theo độ dài
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", padding: "0 60px" }}>
      {icon && <div style={{ fontSize: 170, transform: `scale(${clamp(p * 3)})`, marginBottom: -6 }}>{icon}</div>}
      <div style={{ fontFamily: "Poppins, sans-serif", fontWeight: 900, fontSize: numFont, color: accent, lineHeight: .95, transform: `scale(${lerp(0.6, 1, s)})`, textShadow: `0 0 40px ${accent}66, 0 10px 30px #0008`, WebkitTextStroke: "6px #0b1220", whiteSpace: "nowrap", maxWidth: "100%" }}>{big}</div>
      <div style={{ fontFamily: "Poppins, sans-serif", fontWeight: 800, fontSize: 52, color: "#fff", marginTop: 16, textAlign: "center", whiteSpace: "pre-line", maxWidth: 940, lineHeight: 1.15, opacity: clamp((p - 0.15) * 4) }}>{label}</div>
      {sub && <div style={{ fontWeight: 700, fontSize: 38, color: accent, marginTop: 8, textAlign: "center", maxWidth: 940, opacity: clamp((p - 0.3) * 4) }}>{sub}</div>}
    </AbsoluteFill>
  );
};

// ---------- animated bars (chart) ----------
const MiniBars: React.FC<{ p: number; title: string; bars: { label: string; value: number; prefix?: string; color: string }[]; accent: string; wide?: boolean }> = ({ p, title, bars, accent, wide = true }) => {
  const max = Math.max(...bars.map((b) => b.value));
  const bh = wide ? 78 : 108, bw = wide ? 440 : 480, tf = wide ? 66 : 78, lf = wide ? 40 : 44, mb = wide ? 34 : 46;
  return (
    <AbsoluteFill style={{ padding: wide ? "220px 90px" : "0 70px", paddingTop: wide ? 220 : 430, flexDirection: "column", justifyContent: "flex-start" }}>
      <div style={{ fontFamily: "Poppins, sans-serif", fontWeight: 900, fontSize: tf, color: "#fff", marginBottom: wide ? 40 : 56, opacity: clamp(p * 3) }}>{title}</div>
      {bars.map((b, i) => {
        const lp = clamp((p - 0.1 - i * 0.14) * 2.2);
        const w = ease(lp) * (b.value / max) * bw; // chừa chỗ số bên phải (fit khung)
        const cur = Math.round(b.value * ease(lp));
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", marginBottom: mb }}>
            <div style={{ width: wide ? 240 : 270, paddingRight: 14, boxSizing: "border-box", fontFamily: "Poppins, sans-serif", fontWeight: 800, fontSize: lf * (b.label.length > 8 ? 0.7 : b.label.length > 6 ? 0.85 : 1), lineHeight: 1.05, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", color: "#cfe0f0", flexShrink: 0 }}>{b.label}</div>
            <div style={{ height: bh, width: Math.max(6, w), background: `linear-gradient(90deg,${b.color},${b.color}cc)`, borderRadius: 14, boxShadow: `0 8px 24px ${b.color}66`, flexShrink: 0 }} />
            {/* số LUÔN ở NGOÀI thanh -> không đè */}
            <span style={{ fontFamily: "Poppins, sans-serif", fontWeight: 900, fontSize: 52, color: "#fff", marginLeft: 20, whiteSpace: "nowrap", opacity: clamp(lp * 3) }}>{b.prefix || ""}{cur.toLocaleString()}</span>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// ---------- cinematic grade (key light + vignette + depth) : nâng chất "phim" USA, giữ nhân vật ----------
const CinematicGrade: React.FC<{ w: number; h: number; wide: boolean; warm?: string }> = ({ w, h, wide, warm = "#ffd9a0" }) => (
  <svg viewBox={`0 0 ${w} ${h}`} style={{ position: "absolute", inset: 0, width: w, height: h, pointerEvents: "none", mixBlendMode: "normal" }}>
    <defs>
      <radialGradient id="cgKey" cx="33%" cy="22%" r="78%">
        <stop offset="0" stopColor={warm} stopOpacity="0.18" />
        <stop offset="0.5" stopColor={warm} stopOpacity="0.05" />
        <stop offset="1" stopColor={warm} stopOpacity="0" />
      </radialGradient>
      <radialGradient id="cgVign" cx="50%" cy={wide ? "44%" : "46%"} r={wide ? "70%" : "66%"}>
        <stop offset="0.5" stopColor="#000" stopOpacity="0" />
        <stop offset="1" stopColor="#05070d" stopOpacity="0.52" />
      </radialGradient>
    </defs>
    {/* cool fill from shadow side -> tách chủ thể khỏi nền, cảm giác khối */}
    <rect width={w} height={h} fill="#0a1a33" opacity="0.07" />
    {/* warm key light */}
    <rect width={w} height={h} fill="url(#cgKey)" />
    {/* vignette ôm rìa -> mắt dồn vào giữa, chất điện ảnh */}
    <rect width={w} height={h} fill="url(#cgVign)" />
  </svg>
);

// ---------- room scene bg ----------
const RoomBG: React.FC<{ T: any; dark?: boolean; kind?: string; floor?: number; wide?: boolean }> = ({ T, dark, kind = "room", floor = 0.71, wide = false }) => {
  const fy = `${floor * 100}%`;
  const cityY = floor * (wide ? 1080 : 1920) - (wide ? 520 : 620);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: `linear-gradient(180deg,${T.wall[0]},${T.wall[1]})` }} />
      <div style={{ position: "absolute", left: "20%", top: -220, width: 760, height: 760, borderRadius: "50%", background: T.accent, opacity: 0.09, filter: "blur(30px)" }} />
      <div style={{ position: "absolute", left: 0, top: fy, width: "100%", height: "40%", background: T.floor }} />
      <div style={{ position: "absolute", left: 0, top: fy, width: "100%", height: 6, background: T.floorLine }} />
      {kind === "room" && <><div style={{ position: "absolute", left: wide ? 160 : 80, top: wide ? 150 : 300, width: 250, height: 180, background: dark ? "#0c1a2e" : "#bfe3ff", border: `10px solid ${dark ? "#22344f" : "#fff"}`, borderRadius: 12 }} /><div style={{ position: "absolute", left: wide ? 90 : 46, top: fy, marginTop: -96, fontSize: 96 }}>🪴</div></>}
      {kind === "city" && <>{(wide ? [40, 330, 620, 910, 1200, 1490] : [40, 260, 480, 700, 900]).map((x, i) => {
        const h = 340 - (i % 3) * 55, top = Math.max(110, cityY) + (i % 3) * 40, w = 170;
        const col = dark ? ["#12213a", "#0e1b30"][i % 2] : ["#b9d0e8", "#a7c3e0"][i % 2];
        return (<div key={i} style={{ position: "absolute", left: x, top, width: w, height: h, background: `linear-gradient(180deg,${col},${dark ? "#0a1526" : "#93b4d6"})`, borderRadius: "6px 6px 0 0", boxShadow: "0 6px 20px #0001", display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14, padding: "20px 18px", alignContent: "start" }}>
          {Array.from({ length: 12 }).map((_, k) => <div key={k} style={{ width: "100%", height: 22, background: dark ? (k % 4 === (i % 4) ? "#f5d76e" : "#1c3050") : "#cfe2f5", borderRadius: 3, opacity: dark ? 0.9 : 0.8 }} />)}
        </div>);
      })}</>}
    </AbsoluteFill>
  );
};

// ---------- scene definitions (anchored to vo2 timings) ----------
type Scene = { s: number; e: number; kind: string; [k: string]: any };
const SCENES: Scene[] = [
  { s: 0, e: 5.1, kind: "cold", big: "50%", label: "of your paycheck\ngoes to RENT", icon: "🏠", dark: true },
  { s: 5.1, e: 7.03, kind: "char", pose: "shrug", expr: "annoyed", bg: "room" },
  { s: 7.03, e: 13.62, kind: "chart", title: "Average U.S. rent / month", bars: [{ label: "2000", value: 600, prefix: "$", color: "#38BDF8" }, { label: "2012", value: 1100, prefix: "$", color: "#F5B301" }, { label: "Today", value: 2100, prefix: "$", color: "#EF4444" }], dark: true },
  { s: 13.62, e: 16.02, kind: "compare", title: "Since 2000", left: { label: "Wages", value: 60, color: "#38BDF8" }, right: { label: "Rent", value: 250, color: "#EF4444" }, unit: "%", dark: true },
  { s: 16.02, e: 19.71, kind: "char", pose: "lean", expr: "suspicious", bg: "city" },
  { s: 19.71, e: 23.0, kind: "cold", big: "1 in 4", label: "homes bought by\nWALL STREET", icon: "🏦", dark: true },
  { s: 23.0, e: 25.56, kind: "duo", pose: "point", expr: "annoyed", bg: "city" },
  { s: 25.56, e: 29.1, kind: "cta", pose: "present", expr: "happy", bg: "clean" },
];

type StoryProps = { theme?: string; scenes?: Scene[]; voMp3?: string; voJson?: string; handle?: string; hostStyle?: any };
export const calcStory = async ({ props }: { props: StoryProps }) => {
  try {
    const j = await fetch(staticFile(props.voJson || "stickdemo/vo2.json")).then((r) => r.json());
    return { durationInFrames: Math.round((j.dur + 0.6) * 30) };
  } catch { return { durationInFrames: 880 }; }
};

export const StickStory: React.FC<StoryProps> = ({ theme = "broke", scenes, voMp3 = "stickdemo/vo2.mp3", voJson = "stickdemo/vo2.json", handle = "@brokeexplained", hostStyle }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const time = frame / fps;
  const T = THEMES[theme] || THEMES.broke;
  const HOSTX = hostStyle || HOST;
  const wide = width > height;                 // 16:9 long vs 9:16 short
  const floorPct = wide ? 0.84 : 0.73;
  const hostScale = wide ? 2.35 : 3.4;         // host to đầy khung (9:16 nhân vật to chiếm dải giữa)
  const kBottom = wide ? 70 : 250;
  const audioData = useAudioData(staticFile(voMp3));
  const [vo, setVo] = useState<any>(null);
  useEffect(() => { const h = delayRender(); fetch(staticFile(voJson)).then((r) => r.json()).then((d) => { setVo(d); continueRender(h); }).catch(() => continueRender(h)); }, [voJson]);
  const SC = (scenes && scenes.length) ? scenes : SCENES;
  // preload Lottie PRO (free) cho các cảnh có sc.lottie
  const [lotMap, setLotMap] = useState<any>({});
  useEffect(() => {
    const files: string[] = Array.from(new Set((SC || []).filter((s: any) => s.lottie).map((s: any) => s.lottie)));
    if (!files.length) return;
    const h = delayRender("lottie");
    Promise.all(files.map((f) => fetch(staticFile(`lottie/${f}`)).then((r) => r.json()).then((d) => [f, d]).catch(() => [f, null])))
      .then((es) => { setLotMap(Object.fromEntries(es)); continueRender(h); }).catch(() => continueRender(h));
  }, []);

  // lip-sync + viseme (jaw từ dải thấp, độ rộng miệng từ dải cao) + KHÉP giữa từ
  let mo = 0, mouthWide = 0.5;
  if (audioData) {
    let lo = 0, hi = 0;
    for (let k = 0; k < 3; k++) { const v = visualizeAudio({ fps, frame: Math.max(0, frame - k), audioData, numberOfSamples: 32 }); lo += v[1] + v[2] + v[3]; hi += v[6] + v[7] + v[8] + v[9]; }
    mo = clamp((lo / 3) * 11);
    mouthWide = clamp((hi / 3) * 16);
    if (mo < 0.14) mo = 0;
  }
  if (vo) { const inW = vo.words.some((w: any) => time >= w.t - 0.02 && time < w.t + w.d + 0.04); if (!inW) mo = 0; } // viseme: khép miệng khi ngắt từ
  const blink = Math.sin(time * 2.6) > 0.93 ? 0.12 : 1;
  const breath = Math.sin(time * 2.8) * 3;

  const sc = SC.find((x) => time >= x.s && time < x.e) || SC[SC.length - 1];
  const lp = clamp((time - sc.s) / (sc.e - sc.s));
  const enter = clamp((time - sc.s) / 0.14), exit = clamp((sc.e - time) / 0.12);
  const cross = 0.72 + 0.28 * enter * exit; // chuyển cảnh: dip RẤT nhẹ, ko bạc màu (trước fade sâu -> "mờ")
  const slideX = (1 - ease(clamp((time - sc.s) / 0.32))) * 90 - (1 - ease(clamp((sc.e - time) / 0.3))) * 90; // trượt ngang chuyển cảnh
  const isReveal = sc.kind === "cold" && String(sc.big).includes("4");
  const shake = isReveal ? Math.sin(time * 42) * (1 - clamp((time - sc.s) / 0.55)) * 9 : 0; // rung lúc reveal
  const dark = !!sc.dark;
  const bgTheme = dark ? THEMES.ranked : T;
  const scIdx = SC.indexOf(sc);
  const closeup = sc.kind === "char" && wide && scIdx % 4 === 2;
  const camBase = closeup ? 1.16 : 1.02;
  const noZoom = sc.kind === "chart" || sc.kind === "compare" || sc.kind === "photo"; // canh trái / tự có Ken Burns -> KHÔNG zoom ngoài (né cắt mép)
  const cam = noZoom ? 1 : lerp(camBase, camBase + (closeup ? 0.07 : 0.10), ease(lp));   // push-in điện ảnh
  const punch = noZoom ? 0 : (1 - ease(clamp((time - sc.s) / 0.34))) * ((sc.kind === "cold" || sc.kind === "illus") ? 0.1 : 0.045); // ZOOM-PUNCH vào cảnh
  const panX = wide ? Math.sin(scIdx * 1.7) * 24 * ease(lp) : 0;             // pan nhẹ đổi chiều mỗi cảnh
  const panY = Math.sin(time * 0.42 + scIdx) * (wide ? 7 : 11) * ease(lp);   // trôi dọc mềm -> floating camera
  const host = (extra = 0) => live(POSE[sc.pose || "present"], time, mo);

  return (
    <AbsoluteFill style={{ background: (dark || sc.kind === "cold" || sc.kind === "chart" || sc.kind === "compare" || sc.kind === "photo") ? "#0b1322" : T.wall[0] }}>
      <div style={{ position: "absolute", inset: 0, transform: `translateX(${slideX + shake + panX}px) translateY(${panY}px) scale(${cam + punch})`, opacity: cross }}>
        {sc.kind === "photo" && sc.photo ? (() => {   // ẢNH THẬT + Ken Burns (zoom/pan mượt) + scrim + nhãn
          const pal = (PALETTES[theme] || PALETTES.broke)[0];
          const kb = lerp(1.06, 1.2, ease(lp));
          const ppx = wide ? Math.sin(scIdx * 1.3) * 34 * ease(lp) : 0;
          const rvp = ease(clamp((time - sc.s) / 0.5));
          return (<>
            <AbsoluteFill style={{ overflow: "hidden", background: "#0b1320" }}>
              <Img src={staticFile(sc.photo)} style={{ position: "absolute", width: "116%", height: "116%", left: "-8%", top: "-8%", objectFit: "cover", transform: `scale(${kb}) translateX(${ppx}px)` }} />
            </AbsoluteFill>
            <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(11,18,32,0.55) 0%, rgba(11,18,32,0.05) 22%, rgba(11,18,32,0.05) 50%, rgba(11,18,32,0.88) 100%)" }} />
            {sc.label && <div style={{ position: "absolute", left: "50%", top: height * (wide ? 0.08 : 0.1), transform: `translateX(-50%) translateY(${(1 - rvp) * -16}px)`, opacity: rvp, fontFamily: "Poppins, sans-serif", fontWeight: 900, fontSize: wide ? 64 : 76, color: "#fff", letterSpacing: -1, whiteSpace: "nowrap", background: `${pal.accent}f2`, padding: "10px 40px", borderRadius: 16, boxShadow: "0 14px 40px #0007", textShadow: "0 2px 12px #0008" }}>{sc.label}</div>}
          </>);
        })() : sc.kind === "illus" ? (() => {   // SHOT MINH HOẠ: minh hoạ ẨN DỤ (kể ý) hoặc vật + chữ nhãn
          const pal = (PALETTES[theme] || PALETTES.broke)[0];
          const cx = width * 0.5, cy = height * (wide ? 0.42 : 0.4);
          if (sc.lottie && lotMap[sc.lottie]) {   // MINH HOẠ LOTTIE PRO (free) — đẹp nhất
            const cp2 = ease(clamp((time - sc.s) / 0.5));
            return (<>
              <AbsoluteFill style={{ background: `linear-gradient(180deg,${pal.wall[0]},${pal.wall[1]})` }} />
              <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", top: wide ? -40 : -120 }}><div style={{ opacity: cp2, transform: `scale(${0.9 + cp2 * 0.1})` }}><Lottie animationData={lotMap[sc.lottie]} style={{ width: wide ? width * 0.6 : width * 0.94, height: wide ? height * 0.7 : height * 0.56 }} loop /></div></AbsoluteFill>
              {sc.label && <div style={{ position: "absolute", left: "50%", top: height * (wide ? 0.06 : 0.08), transform: `translateX(-50%) translateY(${(1 - cp2) * -16}px)`, opacity: cp2, fontFamily: "Poppins, sans-serif", fontWeight: 900, fontSize: wide ? 60 : 74, color: "#fff", letterSpacing: -1, whiteSpace: "nowrap", background: "#0b1220f2", padding: "10px 40px", borderRadius: 18, border: `3px solid ${pal.accent}`, boxShadow: "0 14px 40px #0006" }}>{sc.label}</div>}
            </>);
          }
          if (sc.concept && CONCEPTS[sc.concept]) {   // MINH HOẠ ẨN DỤ nhiều lớp (ưu tiên)
            const cp = clamp((time - sc.s) / 0.6);
            return (<>
              <AbsoluteFill style={{ background: `linear-gradient(180deg,${pal.wall[0]},${pal.wall[1]})` }} />
              <svg viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute", inset: 0, width, height }}>{CONCEPTS[sc.concept]({ W: width, H: height, p: cp, t: time, pal, cy })}</svg>
              {sc.label && <div style={{ position: "absolute", left: "50%", top: height * (wide ? 0.73 : 0.64), transform: `translateX(-50%) translateY(${(1 - ease(cp)) * 22}px)`, opacity: ease(cp), fontFamily: "Poppins, sans-serif", fontWeight: 900, fontSize: wide ? 66 : 80, color: "#fff", letterSpacing: -1, whiteSpace: "nowrap", background: "#0b1220f2", padding: "10px 40px", borderRadius: 18, border: `3px solid ${pal.accent}`, boxShadow: "0 14px 40px #0006" }}>{sc.label}</div>}
            </>);
          }
          const P: any = GEN_PROPS[sc.prop];
          const rv = ease(clamp((time - sc.s) / 0.4));
          const S2 = width / 1920;
          const bounce = Math.sin(rv * Math.PI) * 0.14;                  // overshoot nảy giữa lúc hiện
          const bigS = S2 * (wide ? 4.6 : 5.4) * (0.55 + 0.45 * rv + bounce) * (1 + Math.sin(time * 2.2) * 0.025);
          return (
            <>
              <AbsoluteFill style={{ background: `linear-gradient(180deg,${pal.wall[0]},${pal.wall[1]})` }} />
              <svg viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute", inset: 0, width, height }}>
                <circle cx={cx} cy={cy} r={width * (wide ? 0.19 : 0.32)} fill={pal.accent} opacity={0.13} />
                <circle cx={cx} cy={cy} r={width * (wide ? 0.19 : 0.32)} fill="none" stroke={pal.accent} strokeWidth={4} opacity={0.3 * rv} />
                {P && <g opacity={rv} transform={`rotate(${Math.sin(time * 1.3) * 2.5} ${cx} ${cy})`}><P x={cx} y={cy} s={bigS} pal={pal} time={time} /></g>}
              </svg>
              {sc.label && <div style={{ position: "absolute", left: "50%", top: height * (wide ? 0.71 : 0.63), transform: `translateX(-50%) translateY(${(1 - rv) * 22}px)`, opacity: rv, fontFamily: "Poppins, sans-serif", fontWeight: 900, fontSize: wide ? 76 : 92, color: "#fff", letterSpacing: -1, whiteSpace: "nowrap", background: "#0b1220f2", padding: wide ? "8px 34px" : "10px 40px", borderRadius: 18, border: `3px solid ${pal.accent}`, boxShadow: "0 14px 40px #0006" }}>{sc.label}</div>}
            </>
          );
        })() : (sc.kind === "char" || sc.kind === "cta" || sc.kind === "duo") ? (
          <>
            {sc.kind === "cta" ? (() => {   // END-CARD PREMIUM (bỏ cartoon)
              const rv = ease(clamp((time - sc.s) / 0.5)), pulse = 1 + Math.sin(time * 3) * 0.05;
              return (<>
                <AbsoluteFill style={{ background: "radial-gradient(80% 72% at 50% 40%, #17253f 0%, #0c1526 52%, #060a12 100%)" }} />
                <svg viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute", inset: 0, width, height, pointerEvents: "none" }}>
                  <defs><radialGradient id="ctaGlow" cx="50%" cy="40%" r="45%"><stop offset="0" stopColor={T.accent} stopOpacity="0.2" /><stop offset="1" stopColor={T.accent} stopOpacity="0" /></radialGradient></defs>
                  <ellipse cx={width * 0.5} cy={height * 0.4} rx={width * 0.42} ry={height * 0.4} fill="url(#ctaGlow)" />
                  {Array.from({ length: 8 }).map((_, i) => { const bx = ((i * 137) % 100) / 100 * width, by = (((i * 71) % 100) / 100) * height; const s2 = 16 + (i % 4) * 18; return <rect key={i} x={bx + Math.sin(time * 0.4 + i) * 22} y={by + Math.cos(time * 0.3 + i) * 16} width={s2} height={s2} rx={s2 * 0.3} fill={T.accent} opacity={0.08} transform={`rotate(${time * 8 + i * 40} ${bx} ${by})`} />; })}
                </svg>
                <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column" }}>
                  <div style={{ opacity: rv, transform: `scale(${pulse})`, width: wide ? 128 : 150, height: wide ? 128 : 150, borderRadius: "50%", background: `linear-gradient(145deg, ${T.accent}, ${T.accent}bb)`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "Poppins, sans-serif", fontWeight: 900, fontSize: wide ? 72 : 86, color: "#fff", marginBottom: wide ? 36 : 46, boxShadow: `0 0 60px ${T.accent}66, 0 16px 40px #0009` }}>＋</div>
                  <div style={{ opacity: rv, transform: `translateY(${(1 - rv) * 24}px)`, fontFamily: "Poppins, sans-serif", fontWeight: 900, fontSize: wide ? 112 : 128, color: "#fff", letterSpacing: -3, textShadow: "0 8px 34px #000a", lineHeight: 1 }}>FOLLOW</div>
                  <div style={{ opacity: rv, marginTop: wide ? 18 : 24, fontFamily: "Poppins, sans-serif", fontWeight: 800, fontSize: wide ? 56 : 66, color: T.accent, letterSpacing: -1, textShadow: `0 0 26px ${T.accent}55` }}>{handle}</div>
                  <div style={{ opacity: clamp((rv - 0.3) * 3), marginTop: wide ? 30 : 40, fontFamily: "Poppins, sans-serif", fontWeight: 700, fontSize: wide ? 34 : 42, color: "#9fb0c4", letterSpacing: 2 }}>FOR MORE LIKE THIS</div>
                </AbsoluteFill>
              </>);
            })() : (   // char/duo -> NỀN ĐỘNG SẠCH (bỏ cartoon), karaoke tải chữ
              <>
                <AbsoluteFill style={{ background: `linear-gradient(150deg, ${T.wall[0]}, ${T.wall[1]})` }} />
                <svg viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute", inset: 0, width, height, pointerEvents: "none" }}>
                  <defs><radialGradient id="cg" cx="50%" cy="42%" r="55%"><stop offset="0" stopColor={T.accent} stopOpacity="0.16" /><stop offset="1" stopColor={T.accent} stopOpacity="0" /></radialGradient></defs>
                  <ellipse cx={width * 0.5} cy={height * 0.42} rx={width * 0.42} ry={height * 0.42} fill="url(#cg)" />
                  {Array.from({ length: 9 }).map((_, i) => { const bx = ((i * 137) % 100) / 100 * width, by = (((i * 71) % 100) / 100) * height; const r = 16 + (i % 4) * 20; return <rect key={i} x={bx + Math.sin(time * 0.4 + i) * 22} y={by + Math.cos(time * 0.35 + i) * 16} width={r} height={r} rx={r * 0.3} fill={T.accent} opacity={0.05 + (i % 3) * 0.02} transform={`rotate(${time * 8 + i * 40} ${bx} ${by})`} />; })}
                </svg>
              </>
            )}
            {sc.stat && (() => {   // OVERLAY SỐ LIỆU ĐỘNG ghép trên nền cảnh (số + mini-bar mọc) — chất explainer/film
              const sp = ease(clamp((time - sc.s) / 0.5)), gw = ease(clamp((time - sc.s - 0.2) / 0.7));
              const cw = wide ? 360 : 560, cx = wide ? width * 0.75 : width * 0.5;
              return (
                <div style={{ position: "absolute", left: cx - cw / 2, top: wide ? height * 0.12 : height * 0.14, width: cw, transform: `translateY(${(1 - sp) * -28}px)`, opacity: sp }}>
                  <div style={{ background: "rgba(11,19,34,0.92)", borderRadius: 22, padding: wide ? "16px 22px" : "22px 30px", boxShadow: "0 16px 44px #0007", border: `3px solid ${T.accent}` }}>
                    <div style={{ fontFamily: "Poppins, sans-serif", fontWeight: 900, fontSize: wide ? 92 : 150, color: "#fff", textAlign: "center", letterSpacing: -2, lineHeight: 1 }}>{sc.stat}</div>
                    <div style={{ display: "flex", gap: wide ? 8 : 12, alignItems: "flex-end", height: wide ? 54 : 84, marginTop: 12, justifyContent: "center" }}>
                      {[0.45, 0.72, 1, 0.62].map((h, i) => <div key={i} style={{ width: wide ? 44 : 68, height: `${h * gw * 100}%`, background: i === 2 ? T.accent : "#3a4658", borderRadius: 6 }} />)}
                    </div>
                  </div>
                </div>);
            })()}
            <CinematicGrade w={width} h={height} wide={wide} />
          </>
        ) : sc.kind === "cold" ? (
          <>
            {sc.photo ? (() => {
              const kb = lerp(1.08, 1.2, ease(lp));
              return (<>
                <Img src={staticFile(sc.photo)} style={{ position: "absolute", width: "118%", height: "118%", left: "-9%", top: "-9%", objectFit: "cover", transform: `scale(${kb})`, filter: "brightness(0.4) saturate(1.06)" }} />
                <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(9,14,26,0.5) 0%, rgba(9,14,26,0.72) 60%, rgba(9,14,26,0.9) 100%)" }} />
              </>);
            })() : <AbsoluteFill style={{ background: "linear-gradient(180deg,#0b1322,#132038)" }} />}
            <BigStat p={lp} big={sc.big} label={sc.label} icon={sc.icon} accent={sc.big.includes("4") ? "#22D3EE" : "#EF4444"} />
          </>
        ) : sc.kind === "chart" ? (
          <><AbsoluteFill style={{ background: "linear-gradient(180deg,#0b1322,#152238)" }} /><MiniBars p={lp} title={sc.title} bars={sc.bars} accent={T.accent} wide={wide} /></>
        ) : (
          <><AbsoluteFill style={{ background: "linear-gradient(180deg,#0b1322,#152238)" }} /><MiniBars p={lp} title={sc.title} bars={[{ label: sc.left.label, value: sc.left.value, color: sc.left.color }, { label: sc.right.label, value: sc.right.value, color: sc.right.color }]} accent={T.accent} wide={wide} /></>
        )}
      </div>

      <div style={{ position: "absolute", inset: 0, pointerEvents: "none", boxShadow: "inset 0 0 220px rgba(0,0,0,0.30)" }} />
      {vo && <Karaoke words={vo.words} time={time} accent={T.accent} bottom={kBottom} />}
      <div style={{ position: "absolute", top: 60, left: 60, fontFamily: "Poppins, sans-serif", fontWeight: 900, fontSize: 34, color: dark ? "#fff" : "#0b1220", opacity: .5 }}>{handle}</div>
      <Audio src={staticFile(voMp3)} />
    </AbsoluteFill>
  );
};
