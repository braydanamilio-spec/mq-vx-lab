import { AbsoluteFill } from "remotion";
import React from "react";

// Brand PARAMETRIC cho Wave 2 (tài liệu điện ảnh): Cosmos/Deep/Why/Empire/Unsolved.
// 1 component -> 5 kênh, chỉ khác emoji/tên/accent. Motif: nền vũ trụ tối + emoji lớn + wordmark + tagline.
type Kind = "banner" | "avatar" | "watermark" | "thumb";
type P = { kind?: Kind; name?: string; emoji?: string; tagline?: string; handle?: string; accent?: string; accent2?: string; bg?: string; topLine?: string; bigLine?: string };

const Stars: React.FC<{ w: number; h: number; n?: number }> = ({ w, h, n = 60 }) => (
  <svg width={w} height={h} style={{ position: "absolute", inset: 0 }}>
    {Array.from({ length: n }).map((_, i) => {
      const x = ((Math.sin(i * 12.9) * 43758.5) % 1 + 1) % 1 * w;
      const y = ((Math.sin(i * 78.2) * 12543.7) % 1 + 1) % 1 * h;
      const r = ((Math.sin(i * 3.3) * 100) % 1 + 1) % 1 * 1.8 + 0.4;
      return <circle key={i} cx={x} cy={y} r={r} fill="#fff" opacity={0.25 + (i % 5) * 0.13} />;
    })}
  </svg>
);

export const BrandDoc: React.FC<P> = ({ kind = "banner", name = "COSMOS", emoji = "🌌", tagline = "The universe, explained.",
  handle = "@cosmosdaily", accent = "#7C5CFF", accent2 = "#22D3EE", bg, topLine, bigLine }) => {
  const BG = bg || `radial-gradient(120% 100% at 50% 8%, ${accent}33 0%, #0a0e1a 52%, #05060c 100%)`;

  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
        <Stars w={800} h={800} n={70} />
        <div style={{ fontSize: 300, filter: `drop-shadow(0 0 50px ${accent})`, marginBottom: 6 }}>{emoji}</div>
        <div style={{ fontSize: name.length > 7 ? 108 : 132, fontWeight: 900, color: "#EAF8FF", letterSpacing: -4, lineHeight: 0.85, textAlign: "center", textShadow: `0 0 50px ${accent}88` }}>{name}</div>
        <div style={{ marginTop: 12, background: accent, color: "#08101f", fontWeight: 900, fontSize: 34, padding: "6px 26px", borderRadius: 30 }}>EXPLAINED</div>
      </AbsoluteFill>
    );
  }
  if (kind === "watermark") {
    return <AbsoluteFill style={{ background: "transparent", alignItems: "center", justifyContent: "center" }}><div style={{ fontSize: 108, filter: `drop-shadow(0 0 14px ${accent})` }}>{emoji}</div></AbsoluteFill>;
  }
  if (kind === "thumb") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial" }}>
        <Stars w={1280} h={720} n={90} />
        <div style={{ position: "absolute", right: 60, top: "50%", transform: "translateY(-50%)", fontSize: 400, filter: `drop-shadow(0 0 60px ${accent})` }}>{emoji}</div>
        <div style={{ position: "absolute", left: 70, top: 104 }}>
          <div style={{ display: "inline-block", background: accent, color: "#08101f", fontWeight: 900, fontSize: 44, padding: "10px 28px", borderRadius: 16, letterSpacing: 1 }}>{emoji} {name}</div>
          <div style={{ color: "#EAF8FF", fontWeight: 900, fontSize: 120, lineHeight: 0.98, marginTop: 24, maxWidth: 680, textShadow: "0 6px 30px #000c" }}>{bigLine || "YOU WON'T\nBELIEVE THIS"}</div>
          <div style={{ marginTop: 22, color: accent2, fontWeight: 900, fontSize: 56 }}>{topLine || "the truth is wild"}</div>
        </div>
      </AbsoluteFill>
    );
  }
  // BANNER
  return (
    <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
      <Stars w={2560} h={1440} n={140} />
      <div style={{ position: "absolute", left: 220, top: "50%", transform: "translateY(-50%)", fontSize: 460, filter: `drop-shadow(0 0 70px ${accent})` }}>{emoji}</div>
      <div style={{ textAlign: "center", zIndex: 2 }}>
        <div style={{ fontSize: name.length > 7 ? 220 : 270, fontWeight: 900, color: "#EAF8FF", letterSpacing: -8, lineHeight: 0.85, textShadow: `0 0 60px ${accent}88` }}>{name}</div>
        <div style={{ marginTop: 24, display: "inline-block", background: accent, color: "#08101f", fontWeight: 900, fontSize: 54, padding: "12px 44px", borderRadius: 40 }}>{tagline}</div>
        <div style={{ marginTop: 24, color: "#9fb0c8", fontWeight: 800, fontSize: 44 }}>{handle}</div>
      </div>
    </AbsoluteFill>
  );
};
