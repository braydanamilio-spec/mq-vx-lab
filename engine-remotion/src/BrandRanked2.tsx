import { AbsoluteFill } from "remotion";
import React from "react";

// Brand kênh #3 RANKED. Motif: cột tier S/A/B/C màu + wordmark. Palette tím #7C5CFF.
type Kind = "banner" | "avatar" | "watermark" | "thumb";
const BG = "radial-gradient(120% 100% at 50% 6%, #1a1638 0%, #0d0b1c 52%, #06060f 100%)";
const PUR = "#7C5CFF";
const TIERS: [string, string][] = [["S", "#FF3B5C"], ["A", "#FF9F1C"], ["B", "#FFD23F"], ["C", "#3DDC97"]];

const TierStack: React.FC<{ h: number; gap?: number }> = ({ h, gap = 10 }) => {
  const cell = (h - gap * (TIERS.length - 1)) / TIERS.length;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap, height: h }}>
      {TIERS.map(([t, c]) => (
        <div key={t} style={{ display: "flex", alignItems: "center", gap: cell * 0.18, height: cell }}>
          <div style={{ width: cell, height: cell, borderRadius: cell * 0.22, background: c, color: "#0a0c14", fontWeight: 900,
            fontSize: cell * 0.6, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 6px 18px ${c}55`, fontFamily: "'Poppins',Arial" }}>{t}</div>
          <div style={{ width: cell * 2.6, height: cell * 0.62, borderRadius: cell * 0.16, background: "#ffffff14", border: "1.5px solid #ffffff20" }} />
        </div>
      ))}
    </div>
  );
};

export const BrandRanked2: React.FC<{ kind?: Kind; name?: string; tagline?: string; handle?: string; topLine?: string; bigLine?: string }> =
  ({ kind = "banner", name = "RANKED", tagline = "S-tier to trash.", handle = "@rankedusa", topLine, bigLine }) => {

  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
        <div style={{ marginBottom: 24 }}><TierStack h={300} /></div>
        <div style={{ fontSize: 118, fontWeight: 900, color: "#fff", letterSpacing: -4, lineHeight: 0.85, textShadow: `0 0 40px ${PUR}66` }}>{name}</div>
        <div style={{ marginTop: 8, background: PUR, color: "#0a0c14", fontWeight: 900, fontSize: 34, padding: "6px 26px", borderRadius: 30 }}>TIER LIST</div>
      </AbsoluteFill>
    );
  }
  if (kind === "watermark") {
    return <AbsoluteFill style={{ background: "transparent", alignItems: "center", justifyContent: "center" }}><TierStack h={120} gap={6} /></AbsoluteFill>;
  }
  if (kind === "thumb") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial" }}>
        <div style={{ position: "absolute", right: 80, top: "50%", transform: "translateY(-50%)" }}><TierStack h={560} /></div>
        <div style={{ position: "absolute", left: 70, top: 110 }}>
          <div style={{ display: "inline-block", background: PUR, color: "#0a0c14", fontWeight: 900, fontSize: 44, padding: "10px 28px", borderRadius: 16, letterSpacing: 1 }}>🏆 RANKED</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 122, lineHeight: 0.98, marginTop: 24, maxWidth: 620, textShadow: "0 6px 30px #000c" }}>{bigLine || "WHAT'S\nS-TIER?"}</div>
          <div style={{ marginTop: 24, color: PUR, fontWeight: 900, fontSize: 58 }}>{topLine || "you'll rage 😤"}</div>
        </div>
      </AbsoluteFill>
    );
  }
  // BANNER
  return (
    <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
      <div style={{ position: "absolute", left: 200, top: "50%", transform: "translateY(-50%)" }}><TierStack h={640} /></div>
      <div style={{ position: "absolute", right: 200, top: "50%", transform: "translateY(-50%)", opacity: 0.5 }}><TierStack h={520} /></div>
      <div style={{ textAlign: "center", zIndex: 2 }}>
        <div style={{ fontSize: 260, fontWeight: 900, color: "#fff", letterSpacing: -8, lineHeight: 0.85, textShadow: `0 0 60px ${PUR}55` }}>{name}</div>
        <div style={{ marginTop: 24, display: "inline-block", background: PUR, color: "#0a0c14", fontWeight: 900, fontSize: 56, padding: "12px 44px", borderRadius: 40 }}>{tagline}</div>
        <div style={{ marginTop: 24, color: "#9aa4b8", fontWeight: 800, fontSize: 44 }}>{handle}</div>
      </div>
    </AbsoluteFill>
  );
};
