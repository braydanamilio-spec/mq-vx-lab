import { AbsoluteFill } from "remotion";
import React from "react";

// Brand v2 — MỖI KÊNH 1 MOTIF/ICON KHÁC HẲN (không chỉ đổi màu). name/tagline/handle/accent/motif/layout.
type P = { kind?: "banner" | "avatar" | "watermark"; name?: string; tagline?: string;
  handle?: string; accent?: string; motif?: string; layout?: "left" | "center" };

// ICON theo motif (SVG đơn giản, sắc, tô theo accent)
const Icon: React.FC<{ m: string; c: string; s: number }> = ({ m, c, s }) => {
  const p = { stroke: c, strokeWidth: 7, fill: "none", strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const fill = { fill: c };
  const svg = (children: React.ReactNode) => <svg width={s} height={s} viewBox="0 0 100 100">{children}</svg>;
  switch (m) {
    case "coins":   return svg(<><ellipse cx="50" cy="30" rx="30" ry="12" {...fill} /><path d="M20 30v22c0 7 13 12 30 12s30-5 30-12V30" {...p} /><path d="M20 41c0 7 13 12 30 12s30-5 30-12" {...p} /></>);
    case "field":   return svg(<><rect x="14" y="20" width="72" height="60" rx="4" {...p} /><line x1="50" y1="20" x2="50" y2="80" {...p} /><circle cx="50" cy="50" r="12" {...p} /></>);
    case "film":    return svg(<><polygon points="38,28 38,72 74,50" {...fill} /><circle cx="50" cy="50" r="34" {...p} /></>);
    case "map":     return svg(<><path d="M50 84C30 62 22 48 22 36a28 28 0 0156 0c0 12-8 26-28 48z" {...p} /><circle cx="50" cy="36" r="10" {...fill} /></>);
    case "pulse":   return svg(<polyline points="12,52 34,52 44,26 56,74 66,52 88,52" {...p} />);
    case "road":    return svg(<><path d="M34 84 46 20h8l12 64" {...p} /><line x1="50" y1="30" x2="50" y2="38" {...p} /><line x1="50" y1="48" x2="50" y2="58" {...p} /><line x1="50" y1="68" x2="50" y2="78" {...p} /></>);
    case "plate":   return svg(<><circle cx="50" cy="50" r="32" {...p} /><circle cx="50" cy="50" r="15" {...p} /></>);
    case "chip":    return svg(<><rect x="28" y="28" width="44" height="44" rx="6" {...p} />{[36, 50, 64].map(v => <React.Fragment key={v}><line x1={v} y1="14" x2={v} y2="28" {...p} /><line x1={v} y1="72" x2={v} y2="86" {...p} /><line x1="14" y1={v} x2="28" y2={v} {...p} /><line x1="72" y1={v} x2="86" y2={v} {...p} /></React.Fragment>)}</>);
    case "receipt": return svg(<><path d="M30 16h40v68l-8-6-6 6-6-6-6 6-6-6-8 6z" {...p} /><line x1="40" y1="36" x2="60" y2="36" {...p} /><line x1="40" y1="50" x2="60" y2="50" {...p} /></>);
    default:        return svg(<g>{[0, 1, 2, 3].map(i => <rect key={i} x={18 + i * 18} y={70 - [30, 46, 62, 40][i]} width="12" height={[30, 46, 62, 40][i]} rx="3" {...fill} />)}</g>); // bars (race)
  }
};

export const BrandV2: React.FC<P> = ({ kind = "banner", name = "DATA RACE", tagline = "", handle = "@ch", accent = "#F5B301", motif = "bars", layout = "center" }) => {
  const bg = "radial-gradient(120% 100% at 50% 0%, #131a30 0%, #0b1020 45%, #070a14 100%)";
  const two = name.split(" ").join("\n");
  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: bg, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 20 }}>
        <Icon m={motif} c={accent} s={300} />
        <div style={{ fontSize: name.length > 12 ? 92 : 116, fontWeight: 900, color: "#EAF2FF", lineHeight: 0.9, letterSpacing: -3, textAlign: "center", whiteSpace: "pre-line" }}>{two}</div>
      </AbsoluteFill>
    );
  }
  if (kind === "watermark") {
    return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}><Icon m={motif} c={accent} s={130} /></AbsoluteFill>;
  }
  const left = layout === "left";
  return (
    <AbsoluteFill style={{ background: bg, fontFamily: "'Poppins',Arial", justifyContent: "center", alignItems: left ? "flex-start" : "center", padding: left ? "0 160px" : 0 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 44 }}>
        <Icon m={motif} c={accent} s={190} />
        <div style={{ textAlign: left ? "left" : "center" }}>
          <div style={{ fontSize: name.length > 12 ? 150 : 190, fontWeight: 900, color: "#EAF2FF", letterSpacing: -5, lineHeight: 0.9, whiteSpace: "nowrap" }}>{name}</div>
          <div style={{ fontSize: 50, fontWeight: 700, color: "#9FC0E6", marginTop: 14 }}>{tagline}</div>
          <div style={{ fontSize: 38, fontWeight: 800, color: accent, marginTop: 6 }}>{handle}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
