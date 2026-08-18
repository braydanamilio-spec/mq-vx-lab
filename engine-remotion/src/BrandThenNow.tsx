import { AbsoluteFill } from "remotion";
import React from "react";

// Brand kênh #5 THEN×NOW. Motif: split đôi XƯA(sepia)/NAY(hồng) + wordmark. Hồng #EC4899.
type Kind = "banner" | "avatar" | "watermark" | "thumb";
const BG = "radial-gradient(120% 100% at 50% 6%, #1e0f1c 0%, #120a12 52%, #08060a 100%)";
const PK = "#EC4899", SEP = "#c79a3e";

// khối split đôi: nửa sepia (xưa) + nửa hồng (nay), có mũi tên
const Split: React.FC<{ w: number; h: number }> = ({ w, h }) => (
  <div style={{ position: "relative", width: w, height: h, borderRadius: w * 0.06, overflow: "hidden", boxShadow: "0 16px 50px #000a" }}>
    <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: "50%", background: `linear-gradient(160deg,#3a2c12,#1c1508)`, borderBottom: `${Math.max(3, w / 120)}px solid ${SEP}`,
      display: "flex", alignItems: "center", justifyContent: "center", color: SEP, fontWeight: 900, fontSize: h * 0.18, fontFamily: "'Poppins',Arial" }}>THEN</div>
    <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: "50%", background: `linear-gradient(200deg,#3a1230,#160a13)`,
      display: "flex", alignItems: "center", justifyContent: "center", color: PK, fontWeight: 900, fontSize: h * 0.18, fontFamily: "'Poppins',Arial" }}>NOW</div>
    <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%,-50%)", background: PK, color: "#0a0c14",
      width: h * 0.26, height: h * 0.26, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: h * 0.16, boxShadow: `0 0 ${w / 8}px ${PK}` }}>⬇</div>
  </div>
);

export const BrandThenNow: React.FC<{ kind?: Kind; name?: string; tagline?: string; handle?: string; topLine?: string; bigLine?: string }> =
  ({ kind = "banner", name = "THEN × NOW", tagline = "How much has changed?", handle = "@thennowusa", topLine, bigLine }) => {

  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
        <div style={{ marginBottom: 26 }}><Split w={300} h={300} /></div>
        <div style={{ fontSize: 92, fontWeight: 900, color: "#fff", letterSpacing: -3, lineHeight: 0.85, textAlign: "center", textShadow: `0 0 40px ${PK}66` }}>THEN<span style={{ color: PK }}>×</span>NOW</div>
      </AbsoluteFill>
    );
  }
  if (kind === "watermark") {
    return <AbsoluteFill style={{ background: "transparent", alignItems: "center", justifyContent: "center" }}><Split w={110} h={110} /></AbsoluteFill>;
  }
  if (kind === "thumb") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial" }}>
        <div style={{ position: "absolute", right: 90, top: "50%", transform: "translateY(-50%)" }}><Split w={470} h={560} /></div>
        <div style={{ position: "absolute", left: 70, top: 110 }}>
          <div style={{ display: "inline-block", background: PK, color: "#0a0c14", fontWeight: 900, fontSize: 44, padding: "10px 28px", borderRadius: 16, letterSpacing: 1 }}>⏳ THEN × NOW</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 116, lineHeight: 0.98, marginTop: 24, maxWidth: 560, textShadow: "0 6px 30px #000c" }}>{bigLine || "50 YEARS\nLATER…"}</div>
          <div style={{ marginTop: 24, color: PK, fontWeight: 900, fontSize: 56 }}>{topLine || "the change is wild"}</div>
        </div>
      </AbsoluteFill>
    );
  }
  // BANNER
  return (
    <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
      <div style={{ position: "absolute", left: 190, top: "50%", transform: "translateY(-50%)" }}><Split w={380} h={620} /></div>
      <div style={{ position: "absolute", right: 190, top: "50%", transform: "translateY(-50%)", opacity: 0.5 }}><Split w={300} h={500} /></div>
      <div style={{ textAlign: "center", zIndex: 2 }}>
        <div style={{ fontSize: 190, fontWeight: 900, color: "#fff", letterSpacing: -6, lineHeight: 0.85, textShadow: `0 0 60px ${PK}55` }}>THEN<span style={{ color: PK }}>×</span>NOW</div>
        <div style={{ marginTop: 24, display: "inline-block", background: PK, color: "#0a0c14", fontWeight: 900, fontSize: 54, padding: "12px 44px", borderRadius: 40 }}>{tagline}</div>
        <div style={{ marginTop: 24, color: "#9aa4b8", fontWeight: 800, fontSize: 44 }}>{handle}</div>
      </div>
    </AbsoluteFill>
  );
};
