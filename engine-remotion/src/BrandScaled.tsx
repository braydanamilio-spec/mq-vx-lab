import { AbsoluteFill } from "remotion";
import React from "react";

// Brand kênh #4 SCALED. Motif: vật đứng trên nền, cao thấp khác nhau (so sánh kích thước). Xanh lá.
type Kind = "banner" | "avatar" | "watermark" | "thumb";
const BG = "radial-gradient(120% 100% at 50% 6%, #10281c 0%, #0a1510 52%, #060b08 100%)";
const GR = "#2FA84F";

// hàng emoji cao dần trên 1 đường nền
const ScaleRow: React.FC<{ w: number; base: number; items?: [string, number][] }> = ({ w, base, items }) => {
  const its = items || [["🧍", 0.28], ["🦈", 0.5], ["🚌", 0.72], ["🐋", 1]];
  return (
    <div style={{ position: "relative", width: w, height: base }}>
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: Math.max(2, base / 90), background: `linear-gradient(90deg,#0000,${GR}cc,#0000)` }} />
      <div style={{ position: "absolute", bottom: base / 90, left: 0, right: 0, display: "flex", alignItems: "flex-end", justifyContent: "space-around" }}>
        {its.map(([e, s], i) => (
          <div key={i} style={{ fontSize: base * s, lineHeight: 0.9, filter: s === 1 ? `drop-shadow(0 0 ${base / 22}px ${GR})` : "drop-shadow(0 4px 10px #0008)" }}>{e}</div>
        ))}
      </div>
    </div>
  );
};

export const BrandScaled: React.FC<{ kind?: Kind; name?: string; tagline?: string; handle?: string; topLine?: string; bigLine?: string }> =
  ({ kind = "banner", name = "SCALED", tagline = "See the real size.", handle = "@scaledusa", topLine, bigLine }) => {

  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
        <div style={{ marginBottom: 22 }}><ScaleRow w={560} base={300} /></div>
        <div style={{ fontSize: 118, fontWeight: 900, color: "#fff", letterSpacing: -4, lineHeight: 0.85, textShadow: `0 0 40px ${GR}66` }}>{name}</div>
        <div style={{ marginTop: 8, background: GR, color: "#0a0c14", fontWeight: 900, fontSize: 34, padding: "6px 26px", borderRadius: 30 }}>TO SCALE</div>
      </AbsoluteFill>
    );
  }
  if (kind === "watermark") {
    return <AbsoluteFill style={{ background: "transparent", alignItems: "center", justifyContent: "center" }}><ScaleRow w={140} base={110} /></AbsoluteFill>;
  }
  if (kind === "thumb") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial" }}>
        <div style={{ position: "absolute", right: 60, bottom: 90, width: 640 }}><ScaleRow w={640} base={520} /></div>
        <div style={{ position: "absolute", left: 70, top: 100 }}>
          <div style={{ display: "inline-block", background: GR, color: "#0a0c14", fontWeight: 900, fontSize: 44, padding: "10px 28px", borderRadius: 16, letterSpacing: 1 }}>📏 SCALED</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 118, lineHeight: 0.98, marginTop: 24, maxWidth: 640, textShadow: "0 6px 30px #000c" }}>{bigLine || "HOW BIG\nREALLY?"}</div>
          <div style={{ marginTop: 24, color: GR, fontWeight: 900, fontSize: 56 }}>{topLine || "you won't believe it"}</div>
        </div>
      </AbsoluteFill>
    );
  }
  // BANNER
  return (
    <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
      <div style={{ position: "absolute", left: 150, bottom: 320, width: 620 }}><ScaleRow w={620} base={360} /></div>
      <div style={{ position: "absolute", right: 150, bottom: 340, width: 480, opacity: 0.5 }}><ScaleRow w={480} base={300} /></div>
      <div style={{ textAlign: "center", zIndex: 2 }}>
        <div style={{ fontSize: 260, fontWeight: 900, color: "#fff", letterSpacing: -8, lineHeight: 0.85, textShadow: `0 0 60px ${GR}55` }}>{name}</div>
        <div style={{ marginTop: 24, display: "inline-block", background: GR, color: "#0a0c14", fontWeight: 900, fontSize: 56, padding: "12px 44px", borderRadius: 40 }}>{tagline}</div>
        <div style={{ marginTop: 24, color: "#9aa4b8", fontWeight: 800, fontSize: 44 }}>{handle}</div>
      </div>
    </AbsoluteFill>
  );
};
