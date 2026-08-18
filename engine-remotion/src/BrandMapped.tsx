import { AbsoluteFill } from "remotion";
import React, { useMemo } from "react";
import { geoAlbersUsa, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import states from "../public/geo/states-10m.json";

// Brand kênh #2 MAPPED. Motif: BẢN ĐỒ US thật (vài bang sáng accent) + pin. Palette cyan.
type Kind = "banner" | "avatar" | "watermark" | "thumb";
const BG = "radial-gradient(120% 100% at 50% 6%, #101a33 0%, #0a1020 52%, #06080e 100%)";
const CY = "#22D3EE";
const LIT = new Set(["California", "Texas", "New York", "Florida", "Maryland", "Washington", "Colorado", "Illinois"]);

const USMap: React.FC<{ w: number; h: number; pad?: number; pins?: [number, number][] }> = ({ w, h, pad = 0.08, pins }) => {
  const { feats, path } = useMemo(() => {
    const g: any = feature(states as any, (states as any).objects.states);
    const proj = geoAlbersUsa().fitExtent([[w * pad, h * pad], [w * (1 - pad), h * (1 - pad)]], g);
    return { feats: g.features, path: geoPath(proj) };
  }, [w, h, pad]);
  return (
    <svg width={w} height={h}>
      <defs><filter id="bmglow"><feGaussianBlur stdDeviation={Math.max(2, w / 260)} result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter></defs>
      {feats.map((ft: any, i: number) => {
        const lit = LIT.has(ft.properties.name);
        return <path key={i} d={path(ft) || ""} fill={lit ? CY : "#12203c"} opacity={lit ? 0.95 : 0.55}
          stroke="#0a1428" strokeWidth={Math.max(0.5, w / 900)} style={lit ? { filter: "url(#bmglow)" } : undefined} />;
      })}
    </svg>
  );
};

export const BrandMapped: React.FC<{ kind?: Kind; name?: string; tagline?: string; handle?: string; topLine?: string; bigLine?: string }> =
  ({ kind = "banner", name = "MAPPED", tagline = "The US, one map at a time.", handle = "@mappedusa", topLine, bigLine }) => {

  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
        <div style={{ marginTop: -30 }}><USMap w={620} h={400} pad={0.06} /></div>
        <div style={{ fontSize: 132, fontWeight: 900, color: "#fff", letterSpacing: -5, lineHeight: 0.85, marginTop: -20, textShadow: `0 0 40px ${CY}55` }}>{name}</div>
        <div style={{ marginTop: 8, background: CY, color: "#0a0c14", fontWeight: 900, fontSize: 34, padding: "6px 26px", borderRadius: 30 }}>USA</div>
      </AbsoluteFill>
    );
  }
  if (kind === "watermark") {
    return <AbsoluteFill style={{ background: "transparent", alignItems: "center", justifyContent: "center" }}><USMap w={140} h={100} pad={0.04} /></AbsoluteFill>;
  }
  if (kind === "thumb") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial" }}>
        <div style={{ position: "absolute", right: -30, top: 40, opacity: 0.95 }}><USMap w={760} h={640} pad={0.05} /></div>
        <div style={{ position: "absolute", left: 70, top: 96 }}>
          <div style={{ display: "inline-block", background: CY, color: "#0a0c14", fontWeight: 900, fontSize: 44, padding: "10px 28px", borderRadius: 16, letterSpacing: 1 }}>🗺️ MAPPED</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 122, lineHeight: 0.98, marginTop: 24, maxWidth: 720, textShadow: "0 6px 30px #000c" }}>{bigLine || "WHICH STATE\nWINS?"}</div>
          <div style={{ marginTop: 24, color: CY, fontWeight: 900, fontSize: 58 }}>{topLine || "#1 will shock you"}</div>
        </div>
      </AbsoluteFill>
    );
  }
  // BANNER
  return (
    <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
      <div style={{ position: "absolute", left: 120, top: "50%", transform: "translateY(-50%)", opacity: 0.9 }}><USMap w={760} h={620} pad={0.04} /></div>
      <div style={{ position: "absolute", right: 120, top: "50%", transform: "translateY(-50%)", opacity: 0.5 }}><USMap w={520} h={430} pad={0.04} /></div>
      <div style={{ textAlign: "center", zIndex: 2 }}>
        <div style={{ fontSize: 280, fontWeight: 900, color: "#fff", letterSpacing: -10, lineHeight: 0.85, textShadow: `0 0 60px ${CY}55` }}>{name}</div>
        <div style={{ marginTop: 24, display: "inline-block", background: CY, color: "#0a0c14", fontWeight: 900, fontSize: 56, padding: "12px 44px", borderRadius: 40 }}>{tagline}</div>
        <div style={{ marginTop: 24, color: "#9aa4b8", fontWeight: 800, fontSize: 44 }}>{handle}</div>
      </div>
    </AbsoluteFill>
  );
};
