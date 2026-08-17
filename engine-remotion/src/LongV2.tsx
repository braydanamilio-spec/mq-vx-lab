import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, interpolate, useCurrentFrame, spring } from "remotion";
import { Story } from "./Story";
import { StickDefs } from "./StickFigure";
import { VisualStage, Visual } from "./Visuals";
import { LivingBg, sceneStyle, inOut, camera } from "./Motion";

// 🎬 ENGINE v2.1 — nền SỐNG liên tục + mỗi cảnh bay vào/ra + camera + màu xoay theo SEED. Sống động, mượt, không lặp.
const INK = "#161616";
type Scene = { type: string; audio: string; dur: number; nar: string; amp?: number[]; expr?: string; visual?: Visual; num?: string; title?: string; source?: string };
export type V2Props = { scenes: Scene[]; slug: string; persona?: any; bg?: string; floor?: string; accent?: string; accent2?: string; ink?: string; handle?: string };
export const calcV2 = ({ props }: { props: V2Props }) => ({ durationInFrames: props.scenes.reduce((a, s) => a + s.dur, 0) });
const ci = (v: number, a: number, b: number, x: number, y: number) => interpolate(v, [a, b], [x, y], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
const EM: Record<string, { b: number; e: number }> = { neutral: { b: 0, e: 1 }, angry: { b: -0.6, e: 1 }, shocked: { b: 0.85, e: 1.18 }, worried: { b: 0.6, e: 1.06 }, skeptical: { b: -0.3, e: 0.9 }, happy: { b: 0.18, e: 1 } };

const Karaoke: React.FC<{ nar: string; l: number; d: number }> = ({ nar, l, d }) => {
  const w = nar.split(/\s+/); const ch: string[][] = [];
  const WEAK = new Set(["a", "an", "the", "and", "but", "or", "to", "of", "in", "on", "for", "with", "is", "are", "was", "were", "that", "it", "its", "at", "as", "by", "so", "if", "my", "your", "his", "her", "their", "our"]);
  { let i = 0; while (i < w.length) { let end = Math.min(i + 5, w.length); if (end < w.length && end - i > 1 && WEAK.has(w[end - 1].toLowerCase().replace(/[.,!?;:]$/, ""))) end--; ch.push(w.slice(i, end)); i = end; } }
  const tot = ch.reduce((a, c) => a + c.join(" ").length, 0) || 1; const aF = d - 10; let t = 0, cur = ch[0] || [], ct = 0, cd = 1;
  for (const c of ch) { const dd = aF * c.join(" ").length / tot; if (l >= t && l < t + dd) { cur = c; ct = t; cd = dd; break; } t += dd; }
  const wl = cur.reduce((a, x) => a + x.length, 0) || 1; let wt = ct, active = 0;
  for (let j = 0; j < cur.length; j++) { const wd = cd * cur[j].length / wl; if (l >= wt && l < wt + wd) { active = j; break; } wt += wd; if (l >= wt) active = j; }
  const rise = ci(l, 0, 8, 16, 0);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 62 + rise, textAlign: "center", padding: "0 90px" }}>
      <div style={{ display: "inline-block", background: "rgba(16,15,26,0.82)", borderRadius: 22, padding: "16px 34px" }}>
        {cur.map((x, i) => { const on = i === active; return <span key={i} style={{ fontSize: 58 * (on ? 1.1 : 1), fontWeight: 900, color: on ? "#FFD21E" : "#fff", margin: "0 9px", display: "inline-block", lineHeight: 1.14 }}>{x}</span>; })}
      </div>
    </div>
  );
};

const Host: React.FC<{ s: Scene; l: number; persona: any; mode: "center" | "corner"; point?: boolean }> = ({ s, l, persona, mode, point }) => {
  const amp = s.amp ? (s.amp[Math.min(l, s.amp.length - 1)] || 0) : 0;
  let sm = 0, cnt = 0; if (s.amp) for (let k = -5; k <= 5; k++) { const i = l + k; if (i >= 0 && i < s.amp.length) { sm += s.amp[i]; cnt++; } }
  const g = cnt ? sm / cnt : 0; const em = EM[s.expr || "neutral"] || EM.neutral;
  const breathe = Math.sin(l / 34) * 5;
  const gR = (point ? 150 : 15) + g * 40 + Math.sin(l / 32) * 7, gL = 11 + g * 18 + Math.sin(l / 38 + 2) * 6;
  const pose = { brow: em.b, eyeWide: em.e, mouthOpen: amp, armL: gL, armR: gR, lookY: -0.05, lookX: mode === "corner" ? 0.35 : 0 };
  const app = spring({ frame: l, fps: 30, config: { damping: 16 } });
  if (mode === "corner")
    return <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, pointerEvents: "none" }}><g transform={`translate(210,${1086 + (1 - app) * 120 + breathe}) scale(0.62)`}><ellipse cx={0} cy={116} rx={100} ry={20} fill="#000" opacity={0.16} /><Story {...persona} {...pose} /></g></svg>;
  return <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}><g transform={`translate(960,${806 + breathe}) scale(${0.9 + app * 0.1})`} opacity={app}><ellipse cx={0} cy={116} rx={120} ry={22} fill="#000" opacity={0.16} /><Story {...persona} {...pose} /></g></svg>;
};

const ChapterCard: React.FC<{ s: Scene; l: number; ink: string; accent: string }> = ({ s, l, ink, accent }) => {
  const p = ci(l, 6, 24, 0, 1); const big = (s.title || "").length > 15 ? 108 : 148;
  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", transform: `translateY(${ci(l, 0, 20, 60, 0)}px) scale(${0.92 + p * 0.08})`, opacity: p }}>
      <div style={{ fontSize: 56, fontWeight: 900, color: "#2FA84F", letterSpacing: 6, WebkitTextStroke: `6px ${ink}` as any }}>CHAPTER {s.num}</div>
      <div style={{ fontSize: big, fontWeight: 900, color: "#FFD21E", WebkitTextStroke: `9px ${ink}` as any, lineHeight: 1 }}>{(s.title || "").toUpperCase()}</div>
      <div style={{ width: 240 * p, height: 14, background: "#E4562B", border: `4px solid ${ink}`, borderRadius: 8, marginTop: 24 }} />
    </div>
  );
};

export const LongV2: React.FC<V2Props> = ({ scenes, slug, persona = {}, bg = "#F3E7C0", floor = "#9C9A93", accent = "#2FA84F", accent2 = "#E4562B", ink = INK, handle = "" }) => {
  const f = useCurrentFrame(); const st: number[] = []; scenes.reduce((a, s, i) => (st[i] = a, a + s.dur), 0);
  let idx = 0; for (let k = 0; k < scenes.length; k++) if (f >= st[k]) idx = k; const s = scenes[idx], l = f - st[idx];
  const palette = [accent, accent2, "#2D9CDB", "#D79A34", "#7B61FF", "#2FA84F"];
  const style = sceneStyle(slug, idx, palette); const acc = style.accent;
  const vk = s.visual?.kind; const fullBleed = vk === "photo" || vk === "map" || vk === "chartpro";
  const _lum = (hex: string) => { try { const h = hex.replace("#", ""); const r = parseInt(h.slice(0, 2), 16), g = parseInt(h.slice(2, 4), 16), b = parseInt(h.slice(4, 6), 16); return (0.299 * r + 0.587 * g + 0.114 * b) / 255; } catch { return 1; } };
  const darkBg = _lum(bg) < 0.4; // kênh nền tối (RANKED) -> chữ visual sáng
  const dark = darkBg || vk === "photo" || vk === "chartpro";
  const isChapter = s.type === "chapter"; const isPayoff = s.type === "payoff";
  const hasVisual = !!s.visual && !isChapter;
  const hideHost = vk === "chartpro"; // data break sang chảnh -> ẩn host, tập trung vào chart
  const io = inOut(style.entrance, l, s.dur); const cam = camera(style.camera, l, s.dur, fullBleed ? 0.5 : 1);

  return (
    <AbsoluteFill style={{ background: bg, fontFamily: "'Poppins',Arial" }}>
      <StickDefs boil={Math.floor(l / 4) % 3} />
      {!fullBleed && <LivingBg f={f} bg={bg} accent={acc} accent2={accent2} W={1920} H={1080} />}
      {!fullBleed && <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 175, background: floor, opacity: 0.9 }} />}

      {isChapter ? <ChapterCard s={s} l={l} ink={ink} accent={acc} />
        : <>
          {s.visual && <div style={{ position: "absolute", inset: 0, transform: cam }}>
            <div style={{ position: "absolute", left: 0, right: 0, top: 0, bottom: fullBleed ? 0 : 175, ...io }}>
              <VisualStage v={s.visual} l={l} d={s.dur} slug={slug} W={1920} H={fullBleed ? 1080 : 905} accent={acc} ink={ink} dark={dark} style={style} />
            </div>
          </div>}
          {!hideHost && <Host s={s} l={l} persona={persona} mode={hasVisual ? "corner" : "center"} point={hasVisual && (vk === "icons" || vk === "compare" || vk === "bignum" || vk === "hero" || vk === "flow")} />}
        </>}

      {handle && <div style={{ position: "absolute", top: 30, right: 40, color: dark ? "#ffffffcc" : "#6b6457", fontSize: 30, fontWeight: 800 }}>{handle}</div>}
      {!isChapter && <Karaoke nar={s.nar} l={l} d={s.dur} />}

      {scenes.map((sc, j) => <Sequence key={j} from={st[j]} durationInFrames={sc.dur}><Audio src={staticFile(`${slug}/${sc.audio}`)} /></Sequence>)}
    </AbsoluteFill>
  );
};
