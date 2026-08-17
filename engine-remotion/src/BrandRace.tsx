import { AbsoluteFill } from "remotion";
import React from "react";

// Brand cho kênh DATA RACE — banner / avatar / watermark. Motif: bars đua + cờ ca-rô.
type Kind = "banner" | "avatar" | "watermark";
const ACC = ["#22D3EE", "#7C5CFF", "#EC4899", "#F5B301", "#2FA84F"];

const Bars: React.FC<{ h: number; gap: number; heights: number[]; col?: string }> = ({ h, gap, heights, col = "#22D3EE" }) => (
  <div style={{ display: "flex", alignItems: "flex-end", gap, height: h }}>
    {heights.map((ph, i) => (
      <div key={i} style={{ width: `calc((100% - ${gap * (heights.length - 1)}px) / ${heights.length})`, height: `${ph * 100}%`,
        background: `linear-gradient(180deg,${col},${col}99)`, borderRadius: 10, boxShadow: `0 8px 26px ${col}66`, opacity: 0.72 + 0.28 * ph }} />
    ))}
  </div>
);

const Checker: React.FC<{ size: number }> = ({ size }) => (
  <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", width: size, height: size, borderRadius: 6, overflow: "hidden", transform: "rotate(8deg)", boxShadow: "0 6px 20px #0008" }}>
    {Array.from({ length: 16 }).map((_, i) => <div key={i} style={{ background: (Math.floor(i / 4) + i) % 2 ? "#EAF2FF" : "#0b1020" }} />)}
  </div>
);

export const BrandRace: React.FC<{ kind?: Kind; name?: string; tagline?: string; handle?: string; accent?: string }> =
  ({ kind = "banner", name = "DATA RACE", tagline = "Watch the numbers race.", handle = "@dataracehq", accent = "#F5B301" }) => {
  const bg = "radial-gradient(120% 100% at 50% 0%, #131a30 0%, #0b1020 45%, #070a14 100%)";
  const twoLine = name.split(" ").join("\n");        // avatar: mỗi từ 1 dòng

  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: bg, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 34 }}>
          <div style={{ width: 420 }}><Bars h={300} gap={26} heights={[0.42, 0.66, 0.9, 0.55]} col={accent} /></div>
          <div style={{ fontSize: name.length > 12 ? 96 : 118, fontWeight: 900, color: "#EAF2FF", letterSpacing: -3, lineHeight: 0.9, textAlign: "center", whiteSpace: "pre-line" }}>{twoLine}</div>
        </div>
        <div style={{ position: "absolute", top: 120, right: 150 }}><Checker size={92} /></div>
      </AbsoluteFill>
    );
  }
  if (kind === "watermark") {
    // WATERMARK SẠCH: bars dày, bo góc nhẹ, KHÔNG glow (glow lem xấu ở size nhỏ)
    const hs = [0.5, 0.72, 1, 0.62];
    return (
      <AbsoluteFill style={{ background: "transparent", alignItems: "center", justifyContent: "center" }}>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 9, height: 88 }}>
          {hs.map((h, i) => (
            <div key={i} style={{ width: 24, height: `${h * 100}%`, background: accent, borderRadius: "6px 6px 2px 2px", opacity: 0.7 + 0.3 * h }} />
          ))}
        </div>
      </AbsoluteFill>
    );
  }
  // banner 2560x1440 — nội dung trong safe area giữa
  return (
    <AbsoluteFill style={{ background: bg, fontFamily: "'Poppins',Arial" }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 508, display: "flex", flexDirection: "column", alignItems: "center", gap: 30 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 40 }}>
          <div style={{ width: 300 }}><Bars h={190} gap={18} heights={[0.4, 0.62, 0.85, 0.55]} col={accent} /></div>
          <div style={{ fontSize: name.length > 10 ? 150 : 200, fontWeight: 900, color: "#EAF2FF", letterSpacing: -6, lineHeight: 0.9, whiteSpace: "nowrap" }}>{name}</div>
          <div style={{ transform: "translateY(-10px)" }}><Checker size={120} /></div>
        </div>
        <div style={{ fontSize: 58, fontWeight: 700, color: "#7FA8D0", letterSpacing: 2 }}>{tagline}</div>
        <div style={{ fontSize: 40, fontWeight: 800, color: accent }}>{handle}</div>
      </div>
    </AbsoluteFill>
  );
};
