import React, { useEffect, useState } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring, staticFile, Audio, Img, delayRender, continueRender } from "remotion";

// ---------- MOTION-GRAPHICS engine (SAY THIS) : kinetic type + data + icons. KHÔNG mascot. ----------
const clamp = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const ease = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
const lerp = (a: number, b: number, t: number) => a + (b - a) * clamp(t);
const F = "Poppins, 'Arial Black', sans-serif";

type Scene = { s: number; e: number; kind: string; [k: string]: any };
type MGProps = { scenes?: Scene[]; voMp3?: string; voJson?: string; handle?: string; accent?: string };

export const calcMG = async ({ props }: { props: MGProps }) => {
  try { const j = await fetch(staticFile(props.voJson || "stickdemo/vo2.json")).then((r) => r.json()); return { durationInFrames: Math.round((j.dur + 0.6) * 30) }; }
  catch { return { durationInFrames: 900 }; }
};

// entrance helper: 0..1 progress from a start delay
const inAt = (t: number, s: number, delay: number, dur = 0.4) => clamp((t - s - delay) / dur);
const upFade = (p: number, dist = 60) => ({ opacity: p, transform: `translateY(${(1 - ease(p)) * dist}px)` });

// ---------- shared background: grid drift + accent glow pulse + noise + vignette ----------
const MGBg: React.FC<{ t: number; accent: string; tone?: string; pos?: number }> = ({ t, accent, tone = "#0b0e14", pos = 0 }) => {
  const { width: W, height: H } = useVideoConfig();
  const drift = (t * 18) % 90;
  const pulse = 0.11 + Math.sin(t * 1.4) * 0.04;
  const gx = ["50%", "24%", "76%", "40%", "62%"][pos % 5];   // đổi vị trí quầng sáng mỗi cảnh -> đỡ nhàm
  const gy = ["16%", "40%", "34%", "64%", "22%"][pos % 5];
  const nH = Math.ceil(H / 150) + 1, nV = Math.ceil(W / 154) + 1;
  return (
    <>
      <AbsoluteFill style={{ background: `radial-gradient(120% 90% at 50% 0%, #131824 0%, ${tone} 55%, #06080c 100%)` }} />
      <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        <defs>
          <radialGradient id="mgGlow" cx={gx} cy={gy} r="66%"><stop offset="0" stopColor={accent} stopOpacity={pulse} /><stop offset="1" stopColor={accent} stopOpacity="0" /></radialGradient>
          <radialGradient id="mgVig" cx="50%" cy="46%" r="72%"><stop offset="0.52" stopColor="#000" stopOpacity="0" /><stop offset="1" stopColor="#04060a" stopOpacity="0.6" /></radialGradient>
        </defs>
        <g stroke="#ffffff" strokeOpacity="0.04" strokeWidth="2">
          {Array.from({ length: nH }).map((_, i) => <line key={"h" + i} x1={0} y1={(i * 150 + drift) % H} x2={W} y2={(i * 150 + drift) % H} />)}
          {Array.from({ length: nV }).map((_, i) => <line key={"v" + i} x1={i * 154} y1={0} x2={i * 154} y2={H} />)}
        </g>
        <rect width={W} height={H} fill="url(#mgGlow)" />
        <rect width={W} height={H} fill="url(#mgVig)" />
      </svg>
    </>
  );
};

// ---------- PHOTO background (footage thật + Ken Burns + phủ tối) : hết "phẳng xấu" ----------
const PhotoBg: React.FC<{ src: string; lp: number; pos: number; src2?: string }> = ({ src, lp, pos, src2 }) => {
  const z = 1.08 + ease(lp) * 0.14;                       // Ken Burns zoom chậm
  const px = ["50%", "44%", "56%", "48%"][pos % 4];
  // cảnh dài: đổi sang ảnh 2 giữa cảnh (crossfade) -> giữ retention, đỡ chán
  const fade2 = src2 ? clamp((lp - 0.58) / 0.07) : 0;     // giữ ảnh 1 tới lp=0.58, dissolve NHANH (~0.5s) sang ảnh 2 -> sạch, đỡ rối
  const z2 = 1.16 - ease(clamp((lp - 0.5) / 0.5)) * 0.12; // ảnh 2 zoom ngược cho khác nhịp
  return (
    <>
      <AbsoluteFill style={{ overflow: "hidden" }}>
        <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: `${px} 40%`, transform: `scale(${z})` }} />
      </AbsoluteFill>
      {src2 && fade2 > 0 && (
        <AbsoluteFill style={{ overflow: "hidden", opacity: fade2 }}>
          <Img src={staticFile(src2)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: `${["52%", "48%", "45%", "55%"][pos % 4]} 42%`, transform: `scale(${z2})` }} />
        </AbsoluteFill>
      )}
      {/* phủ tối vừa phải: ảnh nổi rõ nhưng chữ vẫn đọc được */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(5,7,11,0.42) 0%, rgba(5,7,11,0.16) 32%, rgba(5,7,11,0.55) 66%, rgba(5,7,11,0.93) 100%)" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 520px rgba(0,0,0,0.7)" }} />
    </>
  );
};

// ---------- karaoke caption (windowed, kinetic) ----------
const Cap: React.FC<{ words: any[]; t: number; accent: string }> = ({ words, t, accent }) => {
  if (!words?.length) return null;
  let ci = 0; for (let i = 0; i < words.length; i++) if (t >= words[i].t) ci = i;
  const si = words[ci].si, lo = Math.max(0, ci - 2), hi = Math.min(words.length, ci + 3);
  const win = words.slice(lo, hi).filter((w) => w.si === si);
  return (
    <div style={{ position: "absolute", left: "50%", bottom: 150, transform: "translateX(-50%)", width: "88%", display: "flex", justifyContent: "center" }}>
      <div style={{ background: "#0a0e15ee", borderRadius: 16, padding: "14px 26px", border: `2px solid ${accent}66`, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "2px 10px" }}>
        {win.map((w, i) => { const on = t >= w.t && t < w.t + w.d + 0.05; const pop = on ? Math.max(0, 1 - (t - w.t) / 0.13) : 0; return <span key={lo + i} style={{ fontFamily: F, fontWeight: 900, fontSize: 46, color: on ? accent : "#fff", display: "inline-block", transform: `scale(${1 + pop * 0.3})`, textShadow: on ? `0 0 18px ${accent}88` : "none" }}>{w.w}</span>; })}
      </div>
    </div>
  );
};

// split a phrase, highlight words listed in emph[]; WRAP để không tràn khung
const Rich: React.FC<{ text: string; emph?: string[]; accent: string; size: number; color?: string; lh?: number; maxW?: number }> = ({ text, emph = [], accent, size, color = "#eef2f7", lh = 1.06, maxW = 900 }) => (
  <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", alignItems: "baseline", maxWidth: maxW, margin: "0 auto", fontFamily: F, fontWeight: 900, fontSize: size, lineHeight: lh, letterSpacing: -1, columnGap: size * 0.22, rowGap: size * 0.1 }}>
    {text.split(" ").map((w, i) => { const hit = emph.some((e) => w.toUpperCase().replace(/[^A-Z]/g, "").includes(e.toUpperCase())); return <span key={i} style={{ color: hit ? accent : color }}>{w}</span>; })}
  </div>
);

// ---------- animated vector icons (premium, drawn — no emoji, no mascot) ----------
const ICONS: Record<string, (c: string) => React.ReactNode> = {
  arrowUp: (c) => <path d="M50 8 L86 50 L64 50 L64 92 L36 92 L36 50 L14 50 Z" fill={c} />,
  arrowDown: (c) => <path d="M50 92 L14 50 L36 50 L36 8 L64 8 L64 50 L86 50 Z" fill={c} />,
  speech: (c) => <><rect x="8" y="14" width="84" height="56" rx="18" fill="none" stroke={c} strokeWidth="7" /><path d="M30 68 L30 90 L52 68 Z" fill={c} /><circle cx="34" cy="42" r="5" fill={c} /><circle cx="50" cy="42" r="5" fill={c} /><circle cx="66" cy="42" r="5" fill={c} /></>,
  shield: (c) => <><path d="M50 8 L86 22 V50 C86 74 50 94 50 94 C50 94 14 74 14 50 V22 Z" fill="none" stroke={c} strokeWidth="7" /><path d="M38 50 L47 60 L66 38" fill="none" stroke={c} strokeWidth="8" strokeLinecap="round" strokeLinejoin="round" /></>,
  crown: (c) => <><path d="M14 78 L22 34 L38 58 L50 26 L62 58 L78 34 L86 78 Z" fill={c} /><rect x="14" y="78" width="72" height="12" rx="3" fill={c} /></>,
  flame: (c) => <path d="M50 8 C58 30 78 36 70 62 C66 82 52 92 42 88 C24 82 26 58 40 50 C36 62 44 66 48 60 C52 52 40 44 50 8 Z" fill={c} />,
  bolt: (c) => <path d="M56 6 L26 54 L46 54 L40 94 L74 42 L52 42 Z" fill={c} />,
  eye: (c) => <><path d="M8 50 C28 22 72 22 92 50 C72 78 28 78 8 50 Z" fill="none" stroke={c} strokeWidth="7" /><circle cx="50" cy="50" r="14" fill={c} /></>,
  coin: (c) => <><circle cx="50" cy="50" r="40" fill="none" stroke={c} strokeWidth="7" /><text x="50" y="70" fontFamily="Arial Black, sans-serif" fontWeight="900" fontSize="58" fill={c} textAnchor="middle">$</text></>,
  heart: (c) => <path d="M50 86 C6 56 16 20 42 30 C48 32 50 38 50 40 C50 38 52 32 58 30 C84 20 94 56 50 86 Z" fill={c} />,
  target: (c) => <><circle cx="50" cy="50" r="40" fill="none" stroke={c} strokeWidth="7" /><circle cx="50" cy="50" r="24" fill="none" stroke={c} strokeWidth="7" /><circle cx="50" cy="50" r="8" fill={c} /></>,
  mic: (c) => <><rect x="38" y="12" width="24" height="46" rx="12" fill={c} /><path d="M26 50 a24 24 0 0 0 48 0" fill="none" stroke={c} strokeWidth="7" /><line x1="50" y1="74" x2="50" y2="86" stroke={c} strokeWidth="7" /><line x1="34" y1="88" x2="66" y2="88" stroke={c} strokeWidth="7" strokeLinecap="round" /></>,
  clock: (c) => <><circle cx="50" cy="50" r="40" fill="none" stroke={c} strokeWidth="7" /><line x1="50" y1="50" x2="50" y2="24" stroke={c} strokeWidth="7" strokeLinecap="round" /><line x1="50" y1="50" x2="70" y2="58" stroke={c} strokeWidth="7" strokeLinecap="round" /></>,
  handshake: (c) => <><path d="M10 40 L34 34 L50 44 L66 34 L90 40 L90 62 L66 68 L50 60 L34 68 L10 62 Z" fill={c} /><rect x="44" y="42" width="12" height="20" rx="4" fill="#0b0e14" /></>,
  ban: (c) => <><circle cx="50" cy="50" r="38" fill="none" stroke={c} strokeWidth="8" /><line x1="26" y1="26" x2="74" y2="74" stroke={c} strokeWidth="8" strokeLinecap="round" /></>,
  brain: (c) => <><path d="M40 20 C22 20 18 38 24 44 C14 50 18 66 30 66 C30 80 50 82 50 70 L50 24 C50 18 46 20 40 20 Z" fill="none" stroke={c} strokeWidth="6" strokeLinejoin="round" /><path d="M60 20 C78 20 82 38 76 44 C86 50 82 66 70 66 C70 80 50 82 50 70 L50 24 C50 18 54 20 60 20 Z" fill="none" stroke={c} strokeWidth="6" strokeLinejoin="round" /></>,
  growth: (c) => <><path d="M14 82 L40 54 L56 68 L86 30" fill="none" stroke={c} strokeWidth="8" strokeLinecap="round" strokeLinejoin="round" /><path d="M66 30 L86 30 L86 50" fill="none" stroke={c} strokeWidth="8" strokeLinecap="round" strokeLinejoin="round" /></>,
  lock: (c) => <><rect x="24" y="46" width="52" height="40" rx="8" fill={c} /><path d="M34 46 V34 a16 16 0 0 1 32 0 V46" fill="none" stroke={c} strokeWidth="7" /><circle cx="50" cy="64" r="6" fill="#0b0e14" /></>,
  phone: (c) => <><rect x="32" y="10" width="36" height="80" rx="10" fill="none" stroke={c} strokeWidth="6" /><circle cx="50" cy="78" r="4" fill={c} /><rect x="40" y="22" width="20" height="4" rx="2" fill={c} /></>,
  battery: (c) => <><rect x="16" y="34" width="60" height="34" rx="7" fill="none" stroke={c} strokeWidth="6" /><rect x="78" y="44" width="8" height="14" rx="3" fill={c} /><rect x="24" y="42" width="16" height="18" rx="3" fill={c} /></>,
  hourglass: (c) => <><path d="M28 14 H72 M28 86 H72" stroke={c} strokeWidth="7" strokeLinecap="round" /><path d="M30 14 C30 40 70 40 70 14 M30 86 C30 60 70 60 70 86" fill="none" stroke={c} strokeWidth="7" strokeLinejoin="round" /><path d="M42 50 L58 50 L50 60 Z" fill={c} /></>,
  bag: (c) => <><path d="M28 34 H72 L78 86 H22 Z" fill={c} /><path d="M38 40 V30 a12 12 0 0 1 24 0 V40" fill="none" stroke="#0b0e14" strokeWidth="6" /></>,
};
const IconBig: React.FC<{ name: string; t: number; p: number; color: string; size?: number }> = ({ name, t, p, color, size = 300 }) => {
  const sc = lerp(0.4, 1, ease(clamp(p * 1.6))) * (1 + Math.sin(t * 2.2) * 0.02);
  const fy = Math.sin(t * 1.3) * 8;
  return <svg width={size} height={size} viewBox="0 0 100 100" style={{ transform: `translateY(${fy}px) scale(${sc})`, filter: `drop-shadow(0 0 30px ${color}55)` }}>{ICONS[name] ? ICONS[name](color) : null}</svg>;
};

// ---------- RESPECT meter (chạy lên/xuống — motif trạng thái, rất động) ----------
const Meter: React.FC<{ t: number; p: number; target: number; dir: "up" | "down"; accent: string; caption: string; metric?: string }> = ({ t, p, target, dir, accent, caption, metric = "RESPECT" }) => {
  const col = dir === "up" ? accent : "#EF4444";
  const val = Math.round(target * ease(clamp(p * 1.5)));
  const trackW = 760;
  return (
    <div style={{ width: trackW, display: "flex", flexDirection: "column", alignItems: "center", gap: 30 }}>
      <div style={{ fontFamily: F, fontWeight: 900, fontSize: 40, letterSpacing: 6, color: "#8a94a3" }}>{metric}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 30, width: "100%" }}>
        <svg width={90} height={90} viewBox="0 0 100 100" style={{ flexShrink: 0, transform: `translateY(${Math.sin(t * 4) * (dir === "up" ? -6 : 6)}px)` }}>{ICONS[dir === "up" ? "arrowUp" : "arrowDown"](col)}</svg>
        <div style={{ flex: 1, height: 56, borderRadius: 28, background: "#141a22", border: "2px solid #26303d", overflow: "hidden" }}>
          <div style={{ height: "100%", width: `${val}%`, background: `linear-gradient(90deg,${col},${col}aa)`, boxShadow: `0 0 30px ${col}66`, borderRadius: 28 }} />
        </div>
      </div>
      <div style={{ fontFamily: F, fontWeight: 900, fontSize: 120, color: col, letterSpacing: -2, textShadow: `0 0 40px ${col}44` }}>{dir === "up" ? "+" : "−"}{val}</div>
      <div style={{ fontFamily: F, fontWeight: 900, fontSize: 52, color: "#eef2f7" }}>{caption}</div>
    </div>
  );
};

export const SayThisMG: React.FC<MGProps> = ({ scenes = [], voMp3 = "stickdemo/vo2.mp3", voJson = "stickdemo/vo2.json", handle = "@saythis", accent = "#F5B301" }) => {
  const frame = useCurrentFrame(); const { fps, durationInFrames } = useVideoConfig(); const t = frame / fps;
  const [vo, setVo] = useState<any>(null);
  useEffect(() => { const h = delayRender(); fetch(staticFile(voJson)).then((r) => r.json()).then((d) => { setVo(d); continueRender(h); }).catch(() => continueRender(h)); }, [voJson]);
  const sc = scenes.find((s) => t >= s.s && t < s.e) || scenes[scenes.length - 1] || ({ s: 0, e: 1, kind: "line", text: "" } as Scene);
  const lp = clamp((t - sc.s) / Math.max(0.1, sc.e - sc.s));
  const kill = clamp((sc.e - t) / 0.14);           // fade out cuối cảnh
  const born = clamp((t - sc.s) / 0.16);           // fade in đầu cảnh
  const trans = Math.min(born, kill);
  const red = "#EF4444";

  const Scene = () => {
    switch (sc.kind) {
      case "hook": {
        const lines: string[] = sc.lines || ["SOMEONE JUST", "DISRESPECTED", "YOU."];
        return (
          <AbsoluteFill style={{ flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 34, padding: "60px 40px" }}>
            {/* timer motif (co giãn, không absolute -> hợp cả 9:16 & 16:9) */}
            <div style={{ ...upFade(inAt(t, sc.s, 0)) }}>
              <svg width="196" height="196" viewBox="0 0 240 240"><circle cx="120" cy="120" r="104" fill="none" stroke="#1c2431" strokeWidth="16" /><circle cx="120" cy="120" r="104" fill="none" stroke={red} strokeWidth="16" strokeLinecap="round" strokeDasharray={653} strokeDashoffset={653 * (1 - ease(clamp(lp * 1.4)))} transform="rotate(-90 120 120)" /><text x="120" y="140" fontFamily={F} fontWeight="900" fontSize="86" fill="#fff" textAnchor="middle">3s</text></svg>
            </div>
            <div>
              {lines.map((ln, i) => { const p = inAt(t, sc.s, 0.15 + i * 0.16); const big = i === (sc.emph ?? 1); const bigSize = Math.min(150, Math.floor(1020 / Math.max(6, ln.length) * 1.5)); return <div key={i} style={{ ...upFade(p, 50), textAlign: "center", padding: "0 40px" }}><span style={{ fontFamily: F, fontWeight: 900, fontSize: big ? bigSize : 74, color: big ? accent : "#eef2f7", letterSpacing: -2, textShadow: big ? `0 0 40px ${accent}55` : "none", whiteSpace: "nowrap" }}>{ln}</span>{big && <div style={{ height: 12, width: `${ease(inAt(t, sc.s, 0.5)) * 62}%`, background: `linear-gradient(90deg,${accent},${accent}88)`, borderRadius: 6, margin: "6px auto 0" }} />}</div>; })}
            </div>
            {sc.pill && <div style={{ display: "flex", alignItems: "center", gap: 20, background: "#12161f", border: "2px solid #26303d", borderRadius: 60, padding: "18px 34px", ...upFade(inAt(t, sc.s, 0.8)) }}><span style={{ fontFamily: F, fontWeight: 900, fontSize: 56, color: accent }}>{sc.pill.stat}</span><span style={{ fontFamily: F, fontWeight: 700, fontSize: 34, color: "#cfd6df" }}>{sc.pill.text}</span></div>}
          </AbsoluteFill>
        );
      }
      case "line": {
        return (
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 90px" }}>
            {sc.tag && <div style={{ ...upFade(inAt(t, sc.s, 0)), marginBottom: 40, fontFamily: F, fontWeight: 800, fontSize: 36, letterSpacing: 6, color: accent }}>{sc.tag}</div>}
            <div style={upFade(inAt(t, sc.s, 0.12))}><Rich text={sc.text} emph={sc.emph} accent={accent} size={sc.size || 96} /></div>
          </AbsoluteFill>
        );
      }
      case "wrong": {
        const p = inAt(t, sc.s, 0.1);
        return (
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 100px" }}>
            <div style={{ ...upFade(inAt(t, sc.s, 0)), display: "flex", alignItems: "center", gap: 20, marginBottom: 46 }}>
              <div style={{ width: 66, height: 66, borderRadius: 16, background: red, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: F, fontWeight: 900, fontSize: 46, color: "#fff" }}>✕</div>
              <span style={{ fontFamily: F, fontWeight: 900, fontSize: 44, letterSpacing: 4, color: red }}>MOST PEOPLE SAY</span>
            </div>
            <div style={{ ...upFade(p), maxWidth: 900, padding: "34px 40px", border: `2px solid ${red}55`, borderRadius: 24, background: "#160c0f" }}>
              <Rich text={`"${sc.quote}"`} accent={red} size={60} color="#e6c9c9" lh={1.14} maxW={800} />
            </div>
          </AbsoluteFill>
        );
      }
      case "right": {
        const p = inAt(t, sc.s, 0.12);
        return (
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 90px" }}>
            <div style={{ ...upFade(inAt(t, sc.s, 0)), display: "flex", alignItems: "center", gap: 20, marginBottom: 42 }}>
              <div style={{ width: 66, height: 66, borderRadius: 16, background: accent, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: F, fontWeight: 900, fontSize: 44, color: "#0b0e14" }}>✓</div>
              <span style={{ fontFamily: F, fontWeight: 900, fontSize: 44, letterSpacing: 4, color: accent }}>{sc.label || "SAY THIS INSTEAD"}</span>
            </div>
            <div style={{ position: "relative", ...upFade(p), maxWidth: 920, padding: "44px 46px", border: `2px solid ${accent}66`, borderRadius: 26, background: "#14120a", boxShadow: `0 0 60px ${accent}22` }}>
              <div style={{ position: "absolute", top: -54, left: 26, fontFamily: F, fontWeight: 900, fontSize: 140, color: `${accent}55` }}>“</div>
              <Rich text={sc.quote} emph={sc.emph} accent={accent} size={64} color="#f4efe2" lh={1.16} maxW={810} />
            </div>
          </AbsoluteFill>
        );
      }
      case "stat": {
        const cur = Math.round((sc.value ?? 0) * ease(clamp(lp * 1.5)));
        const suf = sc.suffix || "";
        return (
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
            <div style={{ fontFamily: F, fontWeight: 900, fontSize: 300, color: accent, letterSpacing: -6, transform: `scale(${lerp(0.7, 1, ease(clamp(lp * 2)))})`, textShadow: `0 0 60px ${accent}44` }}>{cur}{suf}</div>
            <div style={{ ...upFade(inAt(t, sc.s, 0.3)), fontFamily: F, fontWeight: 800, fontSize: 56, color: "#eef2f7", textAlign: "center", maxWidth: 900, whiteSpace: "pre-line", marginTop: 6 }}>{sc.label}</div>
          </AbsoluteFill>
        );
      }
      case "bars": {
        const bars = sc.bars || []; const max = Math.max(...bars.map((b: any) => b.value), 1);
        return (
          <AbsoluteFill style={{ justifyContent: "center", padding: "0 80px" }}>
            <div style={{ ...upFade(inAt(t, sc.s, 0)), fontFamily: F, fontWeight: 900, fontSize: 66, color: "#fff", marginBottom: 56 }}>{sc.title}</div>
            {bars.map((b: any, i: number) => { const bp = clamp((lp - 0.12 - i * 0.16) * 2.2); const w = ease(bp) * (b.value / max) * 560; const cur = Math.round(b.value * ease(bp)); return (
              <div key={i} style={{ display: "flex", alignItems: "center", marginBottom: 40, opacity: clamp(bp * 3) }}>
                <div style={{ width: 250, paddingRight: 14, boxSizing: "border-box", fontFamily: F, fontWeight: 800, fontSize: 42, lineHeight: 1.05, wordBreak: "break-word", color: "#cfd9e4" }}>{b.label}</div>
                <div style={{ height: 96, width: Math.max(8, w), background: `linear-gradient(90deg,${b.color},${b.color}bb)`, borderRadius: 14, boxShadow: `0 8px 30px ${b.color}55` }} />
                <span style={{ fontFamily: F, fontWeight: 900, fontSize: 54, color: "#fff", marginLeft: 22 }}>{b.prefix || ""}{cur}{b.suffix || ""}</span>
              </div>); })}
          </AbsoluteFill>
        );
      }
      case "cta": {
        return (
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
            <div style={{ ...upFade(inAt(t, sc.s, 0.1)), fontFamily: F, fontWeight: 900, fontSize: 96, color: "#fff", textAlign: "center", maxWidth: 900, letterSpacing: -2 }}>{sc.text || "The calm one\nwins the room."}</div>
            <div style={{ marginTop: 60, ...upFade(inAt(t, sc.s, 0.4)), display: "flex", alignItems: "center", gap: 18, background: accent, color: "#0b0e14", fontFamily: F, fontWeight: 900, fontSize: 58, padding: "22px 54px", borderRadius: 999, transform: `scale(${1 + Math.sin(t * 3) * 0.02})` }}>▶ FOLLOW · SAY THIS</div>
          </AbsoluteFill>
        );
      }
      case "chapter": {
        const p = inAt(t, sc.s, 0);
        return (
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
            <div style={{ ...upFade(inAt(t, sc.s, 0)), fontFamily: F, fontWeight: 900, fontSize: 54, letterSpacing: 10, color: accent }}>{sc.tag}</div>
            <div style={{ fontFamily: F, fontWeight: 900, fontSize: 300, color: "#fff", lineHeight: 1, letterSpacing: -6, textShadow: `0 0 60px ${accent}44`, transform: `scale(${lerp(0.65, 1, ease(clamp(p * 2)))})`, opacity: clamp(p * 3) }}>{sc.num}</div>
            <div style={{ height: 10, width: `${ease(inAt(t, sc.s, 0.4)) * 44}%`, background: `linear-gradient(90deg,${accent},${accent}88)`, borderRadius: 5, margin: "18px 0 26px" }} />
            <div style={{ ...upFade(inAt(t, sc.s, 0.5)), fontFamily: F, fontWeight: 900, fontSize: 72, color: "#eef2f7", textAlign: "center", maxWidth: 920, padding: "0 60px", letterSpacing: -1, lineHeight: 1.08 }}>{sc.title}</div>
          </AbsoluteFill>
        );
      }
      case "icon": {
        const p = inAt(t, sc.s, 0.05);
        const sIdx = Math.max(0, scenes.indexOf(sc));
        const align = sc.align || ["center", "left", "center", "right"][sIdx % 4];   // xoay bố cục -> đỡ lặp
        const col = sc.color || accent;
        if (align === "center") return (
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
            <IconBig name={sc.icon} t={t} p={p} color={col} size={sc.isize || 330} />
            {sc.label && <div style={{ marginTop: 46, ...upFade(inAt(t, sc.s, 0.25)), fontFamily: F, fontWeight: 900, fontSize: sc.lsize || 92, color: "#eef2f7", textAlign: "center", maxWidth: 900, letterSpacing: -1, padding: "0 60px" }}>{sc.label}</div>}
            {sc.sub && <div style={{ marginTop: 16, ...upFade(inAt(t, sc.s, 0.45)), fontFamily: F, fontWeight: 800, fontSize: 44, color: col }}>{sc.sub}</div>}
          </AbsoluteFill>
        );
        const leftSide = align === "left";
        return (
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 70px" }}>
            <div style={{ display: "flex", flexDirection: leftSide ? "row" : "row-reverse", alignItems: "center", gap: 46 }}>
              <div style={{ flexShrink: 0 }}><IconBig name={sc.icon} t={t} p={p} color={col} size={300} /></div>
              <div style={{ maxWidth: 540, textAlign: leftSide ? "left" : "right", ...upFade(inAt(t, sc.s, 0.2)) }}>
                <div style={{ fontFamily: F, fontWeight: 900, fontSize: sc.lsize || 80, color: "#eef2f7", lineHeight: 1.06, letterSpacing: -1 }}>{sc.label}</div>
                {sc.sub && <div style={{ marginTop: 14, fontFamily: F, fontWeight: 800, fontSize: 42, color: col }}>{sc.sub}</div>}
              </div>
            </div>
          </AbsoluteFill>
        );
      }
      case "split": {
        const pl = inAt(t, sc.s, 0.12), pr = inAt(t, sc.s, 0.34);
        const Col = (icon: string, title: string, text: string, col: string, p2: number, xd: number) => (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 30, padding: "0 44px", opacity: p2, transform: `translateX(${(1 - ease(p2)) * xd * 70}px)` }}>
            <div style={{ fontFamily: F, fontWeight: 900, fontSize: 40, letterSpacing: 3, color: col }}>{title}</div>
            <IconBig name={icon} t={t} p={p2} color={col} size={190} />
            <div style={{ fontFamily: F, fontWeight: 900, fontSize: 54, color: "#eef2f7", textAlign: "center", maxWidth: 420, lineHeight: 1.08 }}>{text}</div>
          </div>
        );
        return (
          <AbsoluteFill style={{ flexDirection: "row", alignItems: "center" }}>
            {Col(sc.leftIcon || "ban", sc.leftTitle || "MOST PEOPLE", sc.left, red, pl, -1)}
            <div style={{ width: 3, height: "50%", background: "#26303d" }} />
            {Col(sc.rightIcon || "crown", sc.rightTitle || "HIGH VALUE", sc.right, accent, pr, 1)}
          </AbsoluteFill>
        );
      }
      case "meter": {
        const p = inAt(t, sc.s, 0.1);
        return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}><Meter t={t} p={p} target={sc.target ?? 80} dir={sc.dir || "up"} accent={accent} caption={sc.caption || ""} metric={sc.metric} /></AbsoluteFill>;
      }
      default:
        return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 90px" }}><Rich text={sc.text || ""} emph={sc.emph} accent={accent} size={90} /></AbsoluteFill>;
    }
  };

  const tone = sc.kind === "wrong" ? "#140b0d" : "#0b0e14";
  const scIdx = Math.max(0, scenes.indexOf(sc));
  const eb = ease(born), mode = scIdx % 3;                 // chuyển cảnh đa dạng: trượt / zoom / mờ
  const tx = mode === 0 ? (1 - eb) * 130 : 0;
  const ty = mode === 2 ? (1 - eb) * 100 : 0;
  const scl = mode === 1 ? lerp(1.10, 1, eb) : lerp(1.02, 1, eb);
  return (
    <AbsoluteFill style={{ background: "#06080c" }}>
      {sc.bg ? <PhotoBg src={sc.bg} src2={sc.bg2} lp={lp} pos={scIdx} /> : <MGBg t={t} accent={sc.kind === "wrong" ? red : accent} tone={tone} pos={scIdx} />}
      <div style={{ position: "absolute", inset: 0, opacity: trans, transform: `translate(${tx}px,${ty}px) scale(${scl})`, filter: sc.bg ? "drop-shadow(0 3px 16px rgba(0,0,0,0.85))" : "none" }}><Scene /></div>
      <div style={{ position: "absolute", top: 0, left: 0, height: 8, width: `${clamp(frame / Math.max(1, durationInFrames)) * 100}%`, background: `linear-gradient(90deg,${accent},${accent}88)`, boxShadow: `0 0 12px ${accent}aa` }} />
      {vo?.words && <Cap words={vo.words} t={t} accent={accent} />}
      {voMp3 && <Audio src={staticFile(voMp3)} />}
    </AbsoluteFill>
  );
};
