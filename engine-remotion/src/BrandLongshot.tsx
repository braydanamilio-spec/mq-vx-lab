import { AbsoluteFill } from "remotion";
import React from "react";

// Brand kênh #6 LONGSHOT. Motif: ladder/dice — vertical rungs with a die token climbing them. Deep violet-indigo.
type Kind = "banner" | "avatar" | "watermark" | "thumb";
const BG = "radial-gradient(120% 100% at 50% 6%, #1a1840 0%, #0d0b22 52%, #06050f 100%)";
const AC = "#4F46E5";

// mini ladder motif: rails + rungs (fading in significance toward the top) + a die token near the top rung
const LadderMark: React.FC<{ w: number; h: number; rungs?: number }> = ({ w, h, rungs = 5 }) => {
  const railGap = w * 0.42;
  const cx = w / 2;
  const gap = h / rungs;
  return (
    <div style={{ position: "relative", width: w, height: h }}>
      <div style={{ position: "absolute", left: cx - railGap / 2, top: 0, width: Math.max(3, w / 60), height: h, background: `linear-gradient(180deg, ${AC}00, ${AC}bb 30%, ${AC})`, borderRadius: 6 }} />
      <div style={{ position: "absolute", left: cx + railGap / 2 - Math.max(3, w / 60), top: 0, width: Math.max(3, w / 60), height: h, background: `linear-gradient(180deg, ${AC}00, ${AC}bb 30%, ${AC})`, borderRadius: 6 }} />
      {Array.from({ length: rungs }, (_, i) => i).map((i) => {
        const y = h - i * gap;
        const strong = i >= rungs - 2;
        return (
          <div key={i} style={{ position: "absolute", top: y - 2, left: cx - railGap / 2 - w * 0.06, width: railGap + w * 0.12, height: Math.max(3, w / 70),
            background: strong ? AC : `${AC}55`, borderRadius: 4 }} />
        );
      })}
      {/* die token perched on the top rung */}
      <div style={{ position: "absolute", top: -h * 0.16, left: cx, transform: "translate(-50%,0) rotate(-6deg)", width: h * 0.3, height: h * 0.3,
        borderRadius: h * 0.07, background: `radial-gradient(circle at 35% 30%, #ffffff33, ${AC}55 65%, #0000)`, border: `${Math.max(2, w / 90)}px solid ${AC}`,
        display: "flex", alignItems: "center", justifyContent: "center", fontSize: h * 0.16, boxShadow: `0 0 ${h * 0.12}px ${AC}` }}>🎲</div>
    </div>
  );
};

export const BrandLongshot: React.FC<{ kind?: Kind; name?: string; tagline?: string; handle?: string; topLine?: string; bigLine?: string }> =
  ({ kind = "banner", name = "LONGSHOT", tagline = "What are the real odds?", handle = "@longshotusa", topLine, bigLine }) => {

  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
        <div style={{ marginBottom: 30 }}><LadderMark w={280} h={340} rungs={5} /></div>
        <div style={{ fontSize: 96, fontWeight: 900, color: "#fff", letterSpacing: -3, lineHeight: 0.85, textShadow: `0 0 40px ${AC}66` }}>{name}</div>
        <div style={{ marginTop: 10, background: AC, color: "#fff", fontWeight: 900, fontSize: 30, padding: "6px 24px", borderRadius: 30 }}>REAL ODDS</div>
      </AbsoluteFill>
    );
  }
  if (kind === "watermark") {
    return <AbsoluteFill style={{ background: "transparent", alignItems: "center", justifyContent: "center" }}><LadderMark w={90} h={120} rungs={4} /></AbsoluteFill>;
  }
  if (kind === "thumb") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial" }}>
        <div style={{ position: "absolute", right: 110, bottom: 60, width: 420 }}><LadderMark w={420} h={560} rungs={6} /></div>
        <div style={{ position: "absolute", left: 70, top: 100 }}>
          <div style={{ display: "inline-block", background: AC, color: "#fff", fontWeight: 900, fontSize: 44, padding: "10px 28px", borderRadius: 16, letterSpacing: 1 }}>🎲 LONGSHOT</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 112, lineHeight: 0.98, marginTop: 24, maxWidth: 620, textShadow: "0 6px 30px #000c" }}>{bigLine || "WHAT ARE\nTHE ODDS?"}</div>
          <div style={{ marginTop: 24, color: AC, fontWeight: 900, fontSize: 52, filter: "brightness(1.5)" }}>{topLine || "you won't believe #3"}</div>
        </div>
      </AbsoluteFill>
    );
  }
  // BANNER
  return (
    <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
      <div style={{ position: "absolute", left: 180, bottom: 260, width: 260, opacity: 0.55 }}><LadderMark w={260} h={420} rungs={5} /></div>
      <div style={{ position: "absolute", right: 180, bottom: 260, width: 300 }}><LadderMark w={300} h={520} rungs={6} /></div>
      <div style={{ textAlign: "center", zIndex: 2 }}>
        <div style={{ fontSize: 240, fontWeight: 900, color: "#fff", letterSpacing: -8, lineHeight: 0.85, textShadow: `0 0 60px ${AC}66` }}>{name}</div>
        <div style={{ marginTop: 24, display: "inline-block", background: AC, color: "#fff", fontWeight: 900, fontSize: 54, padding: "12px 44px", borderRadius: 40 }}>{tagline}</div>
        <div style={{ marginTop: 24, color: "#9aa4b8", fontWeight: 800, fontSize: 44 }}>{handle}</div>
      </div>
    </AbsoluteFill>
  );
};
