import { AbsoluteFill } from "remotion";
import React from "react";

// Brand kênh #6 PULSE. Motif: gauge bán nguyệt + kim đỏ cam (cường độ giác quan). Cam-đỏ #EA580C trên nền tối.
type Kind = "banner" | "avatar" | "watermark" | "thumb";
const BG = "radial-gradient(120% 100% at 50% 6%, #241209 0%, #140b08 52%, #080504 100%)";
const AC = "#EA580C";

// icon gauge: cung bán nguyệt lạnh->nóng + kim chỉ gần vùng đỏ (tư thế "intense")
const GaugeIcon: React.FC<{ size: number }> = ({ size }) => {
  const cx = size / 2, cy = size * 0.62, r = size * 0.42;
  const a0 = 190, a1 = -10; // độ, giống PulseShort (quạt loe 200°)
  const pt = (deg: number, rr: number) => { const rad = (deg * Math.PI) / 180; return { x: cx + rr * Math.cos(rad), y: cy - rr * Math.sin(rad) }; };
  const steps = 40;
  const arc = Array.from({ length: steps + 1 }, (_, i) => pt(a0 + (a1 - a0) * (i / steps), r)).map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
  const needleDeg = 46; // kim nghiêng về phía nóng (phải)
  const nRad = (needleDeg * Math.PI) / 180;
  const tip = { x: cx + Math.sin(nRad) * r * 0.86, y: cy - Math.cos(nRad) * r * 0.86 };
  const perp = { x: Math.cos(nRad) * r * 0.06, y: Math.sin(nRad) * r * 0.06 };
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <defs>
        <linearGradient id="gIconGrad" x1={cx - r} y1={cy} x2={cx + r} y2={cy} gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#22D3EE" /><stop offset="45%" stopColor="#FACC15" /><stop offset="100%" stopColor="#EF4444" />
        </linearGradient>
        <filter id="gIconGlow" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation={size * 0.02} result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>
      <path d={arc} fill="none" stroke="#2a1c14" strokeWidth={size * 0.09} strokeLinecap="round" />
      <path d={arc} fill="none" stroke="url(#gIconGrad)" strokeWidth={size * 0.075} strokeLinecap="round" filter="url(#gIconGlow)" opacity={0.95} />
      <polygon points={`${tip.x},${tip.y} ${cx + perp.x},${cy + perp.y} ${cx - perp.x},${cy - perp.y}`} fill="#fff" filter="url(#gIconGlow)" />
      <circle cx={cx} cy={cy} r={size * 0.06} fill="#1a1310" stroke={AC} strokeWidth={size * 0.012} />
    </svg>
  );
};

export const BrandPulse: React.FC<{ kind?: Kind; name?: string; tagline?: string; handle?: string; topLine?: string; bigLine?: string }> =
  ({ kind = "banner", name = "PULSE", tagline = "Feel the intensity.", handle = "@pulseusa", topLine, bigLine }) => {

  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
        <div style={{ marginBottom: 10 }}><GaugeIcon size={360} /></div>
        <div style={{ fontSize: 118, fontWeight: 900, color: "#fff", letterSpacing: -3, lineHeight: 0.85, textShadow: `0 0 40px ${AC}77` }}>{name}</div>
        <div style={{ marginTop: 10, background: AC, color: "#150800", fontWeight: 900, fontSize: 32, padding: "6px 26px", borderRadius: 30 }}>REDLINE</div>
      </AbsoluteFill>
    );
  }
  if (kind === "watermark") {
    return <AbsoluteFill style={{ background: "transparent", alignItems: "center", justifyContent: "center" }}><GaugeIcon size={140} /></AbsoluteFill>;
  }
  if (kind === "thumb") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial" }}>
        <div style={{ position: "absolute", right: 40, bottom: 40 }}><GaugeIcon size={560} /></div>
        <div style={{ position: "absolute", left: 70, top: 100 }}>
          <div style={{ display: "inline-block", background: AC, color: "#150800", fontWeight: 900, fontSize: 44, padding: "10px 28px", borderRadius: 16, letterSpacing: 1 }}>🎚️ PULSE</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 112, lineHeight: 0.98, marginTop: 24, maxWidth: 620, textShadow: "0 6px 30px #000c" }}>{bigLine || "HOW LOUD\nCAN IT GET?"}</div>
          <div style={{ marginTop: 24, color: AC, fontWeight: 900, fontSize: 56 }}>{topLine || "loud enough to kill you"}</div>
        </div>
      </AbsoluteFill>
    );
  }
  // BANNER
  return (
    <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
      <div style={{ position: "absolute", left: 140, bottom: 260 }}><GaugeIcon size={440} /></div>
      <div style={{ position: "absolute", right: 140, bottom: 300, opacity: 0.45 }}><GaugeIcon size={320} /></div>
      <div style={{ textAlign: "center", zIndex: 2 }}>
        <div style={{ fontSize: 250, fontWeight: 900, color: "#fff", letterSpacing: -8, lineHeight: 0.85, textShadow: `0 0 60px ${AC}66` }}>{name}</div>
        <div style={{ marginTop: 24, display: "inline-block", background: AC, color: "#150800", fontWeight: 900, fontSize: 56, padding: "12px 44px", borderRadius: 40 }}>{tagline}</div>
        <div style={{ marginTop: 24, color: "#a89a90", fontWeight: 800, fontSize: 44 }}>{handle}</div>
      </div>
    </AbsoluteFill>
  );
};
