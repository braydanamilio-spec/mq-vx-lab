import { AbsoluteFill } from "remotion";
import React from "react";

// Brand kênh #6 SWARM. Motif: cụm chấm nhỏ hội tụ thành 1 hình tròn/khối (đông đúc -> có trật tự). Teal-emerald.
type Kind = "banner" | "avatar" | "watermark" | "thumb";
const BG = "radial-gradient(120% 100% at 50% 6%, #0f2a26 0%, #0a1614 52%, #050908 100%)";
const TEAL = "#0D9488";

const hash01 = (n: number) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const GOLDEN = 2.399963229728653;

// cụm chấm hội tụ kiểu "hoa hướng dương" -> gợi swarm đã settle thành hình tròn đông đặc
const DotCluster: React.FC<{ size: number; n?: number }> = ({ size, n = 90 }) => {
  const R = size / 2;
  return (
    <div style={{ position: "relative", width: size, height: size }}>
      {Array.from({ length: n }).map((_, j) => {
        const t = j * GOLDEN;
        const r = R * Math.sqrt(j / n);
        const x = R + Math.cos(t) * r, y = R + Math.sin(t) * r;
        const s = 6 + hash01(j + 1) * 10;
        const edge = j / n > 0.86; // vòng ngoài -> vài chấm sáng nổi bật như hạt vừa "bay tới"
        return (
          <div key={j} style={{ position: "absolute", left: x, top: y, width: s, height: s, borderRadius: "50%",
            transform: "translate(-50%,-50%)", background: edge ? "#fff" : TEAL,
            boxShadow: `0 0 ${s * (edge ? 2.2 : 1.3)}px ${TEAL}` }} />
        );
      })}
    </div>
  );
};

export const BrandSwarm: React.FC<{ kind?: Kind; name?: string; tagline?: string; handle?: string; topLine?: string; bigLine?: string }> =
  ({ kind = "banner", name = "SWARM", tagline = "See the real number.", handle = "@swarmusa", topLine, bigLine }) => {

  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
        <div style={{ marginBottom: 22 }}><DotCluster size={340} n={110} /></div>
        <div style={{ fontSize: 108, fontWeight: 900, color: "#fff", letterSpacing: -3, lineHeight: 0.85, textShadow: `0 0 40px ${TEAL}66` }}>{name}</div>
      </AbsoluteFill>
    );
  }
  if (kind === "watermark") {
    return <AbsoluteFill style={{ background: "transparent", alignItems: "center", justifyContent: "center" }}><DotCluster size={120} n={60} /></AbsoluteFill>;
  }
  if (kind === "thumb") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial" }}>
        <div style={{ position: "absolute", right: 60, bottom: 60, width: 560 }}><DotCluster size={560} n={160} /></div>
        <div style={{ position: "absolute", left: 70, top: 100 }}>
          <div style={{ display: "inline-block", background: TEAL, color: "#04120f", fontWeight: 900, fontSize: 44, padding: "10px 28px", borderRadius: 16, letterSpacing: 1 }}>🐝 SWARM</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 112, lineHeight: 0.98, marginTop: 24, maxWidth: 620, textShadow: "0 6px 30px #000c" }}>{bigLine || "HOW MANY,\nREALLY?"}</div>
          <div style={{ marginTop: 24, color: TEAL, fontWeight: 900, fontSize: 52 }}>{topLine || "the real number, visualized"}</div>
        </div>
      </AbsoluteFill>
    );
  }
  // BANNER
  return (
    <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
      <div style={{ position: "absolute", left: 170, top: "50%", transform: "translateY(-50%)", opacity: 0.55 }}><DotCluster size={420} n={130} /></div>
      <div style={{ position: "absolute", right: 170, top: "50%", transform: "translateY(-50%)", opacity: 0.35 }}><DotCluster size={300} n={90} /></div>
      <div style={{ textAlign: "center", zIndex: 2 }}>
        <div style={{ fontSize: 250, fontWeight: 900, color: "#fff", letterSpacing: -8, lineHeight: 0.85, textShadow: `0 0 60px ${TEAL}55` }}>{name}</div>
        <div style={{ marginTop: 24, display: "inline-block", background: TEAL, color: "#04120f", fontWeight: 900, fontSize: 56, padding: "12px 44px", borderRadius: 40 }}>{tagline}</div>
        <div style={{ marginTop: 24, color: "#9aa4b8", fontWeight: 800, fontSize: 44 }}>{handle}</div>
      </div>
    </AbsoluteFill>
  );
};
