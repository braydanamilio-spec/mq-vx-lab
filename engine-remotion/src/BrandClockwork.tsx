import { AbsoluteFill } from "remotion";
import React from "react";

// Brand kênh CLOCKWORK. Motif: mặt đồng hồ 12 vạch + kim quét dừng ở 1 lát cắt sáng (ẩn dụ nén thời gian). Đồng/nâu ấm.
type Kind = "banner" | "avatar" | "watermark" | "thumb";
const BG = "radial-gradient(120% 100% at 50% 6%, #22140a 0%, #140d07 52%, #050403 100%)";
const AC = "#C2410C";
const AC2 = "#F5A15A";

// mặt đồng hồ: vòng tròn + 12 vạch giờ + 1 vạch sáng (lát cắt hero) + kim dừng đúng đó
const ClockFace: React.FC<{ size: number }> = ({ size }) => {
  const r = size / 2;
  const heroAng = -Math.PI / 2 + (355 / 360) * Math.PI * 2; // kim gần chạm về vạch 12, dừng ở lát cắt cuối
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={r} cy={r} r={r - 8} stroke={AC} strokeWidth={Math.max(3, size / 90)} fill="#0000" opacity={0.9} />
      {Array.from({ length: 12 }).map((_, i) => {
        const ang = (i / 12) * Math.PI * 2 - Math.PI / 2;
        const isHero = i === 11;
        const r1 = r - 10, r2 = r - (size / 11);
        const x1 = r + Math.cos(ang) * r1, y1 = r + Math.sin(ang) * r1;
        const x2 = r + Math.cos(ang) * r2, y2 = r + Math.sin(ang) * r2;
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={isHero ? AC2 : AC} strokeWidth={isHero ? size / 55 : size / 110} opacity={isHero ? 1 : 0.8} />;
      })}
      {/* kim quét, dừng gần vạch 12 (lát cắt hero) */}
      <line x1={r} y1={r} x2={r + Math.cos(heroAng) * (r - 26)} y2={r + Math.sin(heroAng) * (r - 26)} stroke={AC2} strokeWidth={Math.max(4, size / 70)} strokeLinecap="round" />
      <circle cx={r} cy={r} r={size / 45} fill={AC2} />
      <circle cx={r + Math.cos(heroAng) * (r - 26)} cy={r + Math.sin(heroAng) * (r - 26)} r={size / 40} fill={AC2} opacity={0.9} />
    </svg>
  );
};

export const BrandClockwork: React.FC<{ kind?: Kind; name?: string; tagline?: string; handle?: string; topLine?: string; bigLine?: string }> =
  ({ kind = "banner", name = "CLOCKWORK", tagline = "Time, compressed.", handle = "@clockworkusa", topLine, bigLine }) => {

  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
        <div style={{ marginBottom: 22 }}><ClockFace size={340} /></div>
        <div style={{ fontSize: 92, fontWeight: 900, color: "#fff", letterSpacing: -3, lineHeight: 0.85, textShadow: `0 0 40px ${AC}66` }}>{name}</div>
        <div style={{ marginTop: 8, background: AC, color: "#0a0603", fontWeight: 900, fontSize: 30, padding: "6px 26px", borderRadius: 30 }}>TIME, COMPRESSED</div>
      </AbsoluteFill>
    );
  }
  if (kind === "watermark") {
    return <AbsoluteFill style={{ background: "transparent", alignItems: "center", justifyContent: "center" }}><ClockFace size={130} /></AbsoluteFill>;
  }
  if (kind === "thumb") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial" }}>
        <div style={{ position: "absolute", right: 60, bottom: 70, width: 560 }}><ClockFace size={560} /></div>
        <div style={{ position: "absolute", left: 70, top: 100 }}>
          <div style={{ display: "inline-block", background: AC, color: "#0a0603", fontWeight: 900, fontSize: 44, padding: "10px 28px", borderRadius: 16, letterSpacing: 1 }}>⏱ CLOCKWORK</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 112, lineHeight: 0.98, marginTop: 24, maxWidth: 620, textShadow: "0 6px 30px #000c" }}>{bigLine || "1.7 SECONDS\nOF 24 HOURS"}</div>
          <div style={{ marginTop: 24, color: AC2, fontWeight: 900, fontSize: 52 }}>{topLine || "you won't believe it"}</div>
        </div>
      </AbsoluteFill>
    );
  }
  // BANNER
  return (
    <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
      <div style={{ position: "absolute", left: 150, bottom: 280, opacity: 0.9 }}><ClockFace size={420} /></div>
      <div style={{ position: "absolute", right: 150, bottom: 300, opacity: 0.4 }}><ClockFace size={300} /></div>
      <div style={{ textAlign: "center", zIndex: 2 }}>
        <div style={{ fontSize: 240, fontWeight: 900, color: "#fff", letterSpacing: -8, lineHeight: 0.85, textShadow: `0 0 60px ${AC}55` }}>{name}</div>
        <div style={{ marginTop: 24, display: "inline-block", background: AC, color: "#0a0603", fontWeight: 900, fontSize: 56, padding: "12px 44px", borderRadius: 40 }}>{tagline}</div>
        <div style={{ marginTop: 24, color: "#c9a68c", fontWeight: 800, fontSize: 44 }}>{handle}</div>
      </div>
    </AbsoluteFill>
  );
};
