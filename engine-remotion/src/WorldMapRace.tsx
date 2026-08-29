import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, interpolateColors, Audio, staticFile } from "remotion";
import React, { useMemo } from "react";
import { geoNaturalEarth1, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import world from "../public/geo/countries-110m.json";
import { RaceProps, calcRace } from "./BarChartRace";

export { calcRace };

// tên của mình -> tên trong topojson world-atlas
const ALIAS: Record<string, string> = {
  "United States": "United States of America",
  "UAE": "United Arab Emirates",
  "South Korea": "South Korea",
  "Czech Republic": "Czechia",
  "Russia": "Russia",
};

// tên ngắn cho bảng xếp hạng (khỏi tràn)
const SHORT: Record<string, string> = {
  "United States": "USA", "United Kingdom": "UK", "Saudi Arabia": "Saudi Arabia",
  "South Korea": "S. Korea", "United Arab Emirates": "UAE", "UAE": "UAE",
};
const fmt = (v: number) => {
  if (v >= 1000) return (v / 1000).toFixed(v >= 10000 ? 0 : 1) + "K";
  if (v < 100) return Number(v.toFixed(1)).toLocaleString("en-US");
  return Math.round(v).toLocaleString("en-US");
};

export const WorldMapRace: React.FC<RaceProps> = (props) => {
  const { title = "", subtitle = "", unit = "", source = "", handle = "", frames, icons, music } = props;
  const spf = props.secondsPerFrame ?? 2.2; const topN = props.topN ?? 8;
  const f = useCurrentFrame(); const { width: W, height: H, fps } = useVideoConfig();

  // geojson + projection (tính 1 lần)
  const { geo, pathGen } = useMemo(() => {
    const g: any = feature(world as any, (world as any).objects.countries);
    const proj = geoNaturalEarth1().fitExtent([[50, 175], [W - 470, H - 70]], g);
    return { geo: g, pathGen: geoPath(proj) };
  }, [W, H]);

  // giá trị hiện tại theo thời gian (nội suy như bar race)
  const tf = Math.min(frames.length - 1, f / fps / spf);
  // clamp về 0: nếu chỉ có 1 keyframe (frames.length===1) thì frames.length-2 = -1 -> frames[-1] undefined -> crash
  const i0 = Math.max(0, Math.min(frames.length - 2, Math.floor(tf))); const fr = tf - i0;
  const a = frames[i0], b = frames[Math.min(frames.length - 1, i0 + 1)];
  const smooth = fr * fr * (3 - 2 * fr);
  const names = Array.from(new Set([...a.data, ...b.data].map(d => d.name)));
  const vof = (kf: typeof a, n: string) => kf.data.find(d => d.name === n)?.value ?? 0;
  const cur = names.map(n => ({ name: n, value: vof(a, n) + (vof(b, n) - vof(a, n)) * smooth }))
    .filter(d => d.value > 0).sort((x, y) => y.value - x.value);
  const maxV = Math.max(1, cur[0]?.value ?? 1);
  const year = Math.round(a.t + (b.t - a.t) * fr);
  const leader = cur[0]?.name;

  // map tên topojson -> giá trị
  const byTopo: Record<string, number> = {};
  cur.forEach(d => { byTopo[ALIAS[d.name] || d.name] = d.value; });
  const leaderTopo = leader ? (ALIAS[leader] || leader) : "";
  const intro = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const pulse = 0.5 + 0.5 * Math.sin(f / 5);

  return (
    <AbsoluteFill style={{ background: "radial-gradient(120% 100% at 50% 20%, #244085 0%, #1e2a55 100%)", fontFamily: "'Poppins',Arial", opacity: intro }}>
      {/* bản đồ */}
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="6" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        {geo.features.map((ft: any, i: number) => {
          const nm = ft.properties?.name; const v = byTopo[nm];
          const ratio = v ? Math.pow(v / maxV, 0.5) : 0;
          const fill = v ? interpolateColors(ratio, [0, 0.5, 1], ["#1c3a6e", "#F5B301", "#EF4444"]) : "#101c33";
          const isLeader = nm === leaderTopo;
          return <path key={i} d={pathGen(ft) || ""} fill={fill} stroke={isLeader ? "#fff" : "#0a1120"} strokeWidth={isLeader ? 2.2 : 0.5}
            filter={isLeader ? "url(#glow)" : undefined} opacity={v ? 1 : 0.55} />;
        })}
      </svg>

      {/* tiêu đề + năm */}
      <div style={{ position: "absolute", top: 56, left: 60, right: 60 }}>
        <div style={{ fontSize: 62, fontWeight: 900, color: "#EAF2FF", letterSpacing: -1 }}>{title}</div>
        {subtitle ? <div style={{ fontSize: 32, fontWeight: 700, color: "#7FA8D0", marginTop: 8 }}>{subtitle}</div> : null}
      </div>
      <div style={{ position: "absolute", top: 40, right: 60, fontSize: 116, fontWeight: 900, color: "#7FA8D0", opacity: 0.5 }}>{year}</div>

      {/* bảng xếp hạng bên phải */}
      <div style={{ position: "absolute", top: 190, right: 56, width: 380, display: "flex", flexDirection: "column", gap: 10 }}>
        {cur.slice(0, topN).map((d, r) => {
          const ic = icons?.[d.name] || "";
          const col = interpolateColors(Math.pow(d.value / maxV, 0.5), [0, 0.5, 1], ["#38BDF8", "#F5B301", "#EF4444"]);
          return (
            <div key={d.name} style={{ display: "flex", alignItems: "center", gap: 12, padding: "9px 14px", borderRadius: 12, background: r === 0 ? "#ffffff14" : "#ffffff08", border: r === 0 ? `1px solid ${col}` : "1px solid #ffffff10" }}>
              <span style={{ fontSize: 26, fontWeight: 900, color: "#5B7290", width: 30 }}>{r + 1}</span>
              {ic ? <span style={{ fontSize: 30 }}>{ic}</span> : null}
              <span style={{ fontSize: 25, fontWeight: 800, color: "#EAF2FF", flex: 1, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{SHORT[d.name] || d.name}</span>
              {r === 0 ? <span style={{ fontSize: 26 }}>👑</span> : null}
              <span style={{ fontSize: 26, fontWeight: 900, color: col, whiteSpace: "nowrap" }}>{unit === "$" ? "$" : ""}{fmt(d.value)}{unit && unit !== "$" ? " " + unit : ""}</span>
            </div>
          );
        })}
      </div>

      {source ? <div style={{ position: "absolute", bottom: 36, left: 60, fontSize: 26, color: "#5B7290" }}>Source: {source}</div> : null}
      {music ? <Audio src={staticFile(music)} volume={0.12} /> : null}
    </AbsoluteFill>
  );
};
