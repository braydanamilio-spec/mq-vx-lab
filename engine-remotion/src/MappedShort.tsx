import { AbsoluteFill, Sequence, Audio, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate, interpolateColors } from "remotion";
import { Karaoke } from "./Karaoke";
import { Bookend } from "./Bookend";
import React, { useMemo } from "react";
import { geoAlbersUsa, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import states from "../public/geo/states-10m.json";

// KÊNH #2 MAPPED — choropleth bản đồ US "nóng dần" theo số liệu + pop TOP bang. Motif khác hẳn bar-race.
type Word = { t: number; d: number; w: string };
export type MapDatum = { state: string; value: number; disp?: string };  // disp = chuỗi hiển thị (vd "$74,580")
export type MappedProps = {
  title?: string; unit?: string; handle?: string; color?: string; accent?: string;
  data: MapDatum[]; topN?: number; introSec?: number; bloomSec?: number; popSec?: number; outroSec?: number;
  audio?: string; music?: string; subs?: Word[];
};

const FPS = 30;
const norm = (s: string) => s.trim().toLowerCase();

export const calcMapped = ({ props }: any) => {
  const p = props || {};
  const topN = Math.min(p.topN || 3, (p.data || []).length);
  const isec = p.introSec ?? 1.8, bloom = p.bloomSec ?? 2.4, pop = p.popSec ?? 1.6, tail = p.outroSec ?? 1.6;
  return { durationInFrames: Math.round((isec + bloom + topN * pop + tail) * FPS), fps: FPS, width: 1080, height: 1920 };
};

// màu nhiệt: lạnh (#16223e) -> nóng (accent) theo giá trị chuẩn hoá (gamma nhấn tương phản)
const heat = (t: number, accent: string) => interpolateColors(Math.pow(Math.max(0, Math.min(1, t)), 0.7), [0, 1], ["#16223e", accent]);

export const MappedShort: React.FC<MappedProps> = (props) => {
  const { title = "BY STATE", unit = "", handle = "@mappedusa", color = "#22D3EE", accent = "#22D3EE",
    data = [], topN = 3, introSec = 1.8, bloomSec = 2.4, popSec = 1.6, outroSec = 1.6, audio, music , subs = [] } = props;
  const f = useCurrentFrame(); const { fps, width: W, height: H } = useVideoConfig();

  const { geo, pathGen, valById, maxV, ranked } = useMemo(() => {
    const g: any = feature(states as any, (states as any).objects.states);
    const proj = geoAlbersUsa().fitExtent([[60, 360], [W - 60, H - 620]], g);
    const m: Record<string, number> = {};
    for (const d of data) m[norm(d.state)] = d.value;
    const mx = Math.max(1, ...data.map((d) => d.value));
    const rk = [...data].sort((a, b) => b.value - a.value).slice(0, topN);
    return { geo: g, pathGen: geoPath(proj), valById: m, maxV: mx, ranked: rk, proj };
  }, [W, H, data, topN]);

  const introF = Math.round(introSec * fps);
  const bloomF = Math.round(bloomSec * fps);
  const bloomStart = introF;
  const bloom = interpolate(f, [bloomStart, bloomStart + bloomF], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const popStart = introF + bloomF;

  // centroid cho pin top-N
  const centroids = useMemo(() => {
    const byName: Record<string, any> = {};
    for (const ft of geo.features) byName[norm(ft.properties.name)] = ft;
    return ranked.map((d) => { const ft = byName[norm(d.state)]; return ft ? pathGen.centroid(ft) : [W / 2, H / 2]; });
  }, [geo, ranked, pathGen, W, H]);

  return (
    <AbsoluteFill style={{ background: "radial-gradient(120% 90% at 50% 12%, #0f1730 0%, #0a1020 55%, #070a14 100%)", fontFamily: "'Poppins',Arial" }}>
      {/* TIÊU ĐỀ */}
      <div style={{ position: "absolute", top: 96, left: 0, right: 0, textAlign: "center", padding: "0 60px" }}>
        <div style={{ display: "inline-block", background: color, color: "#0a0c14", fontWeight: 900, fontSize: 30, letterSpacing: 2, padding: "8px 22px", borderRadius: 12 }}>🗺️ MAPPED · USA</div>
        <div style={{ color: "#fff", fontWeight: 900, fontSize: 74, lineHeight: 1.02, marginTop: 20, textShadow: "0 4px 24px #000c", textWrap: "balance" as any }}>{title}</div>
        {unit ? <div style={{ color: "#93a4c4", fontWeight: 700, fontSize: 34, marginTop: 8 }}>{unit}</div> : null}
      </div>

      {/* BẢN ĐỒ */}
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <filter id="mglow"><feGaussianBlur stdDeviation="7" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>
        {geo.features.map((ft: any, i: number) => {
          const v = valById[norm(ft.properties.name)];
          const t = v == null ? 0 : (v / maxV) * bloom;
          const isTop = ranked.some((r) => norm(r.state) === norm(ft.properties.name));
          const topActive = isTop && f >= popStart;
          return <path key={i} d={pathGen(ft) || ""} fill={v == null ? "#0e1832" : heat(t, accent)}
            stroke={topActive ? "#fff" : "#0a1120"} strokeWidth={topActive ? 2.6 : 0.6}
            style={topActive ? { filter: "url(#mglow)" } : undefined} />;
        })}
      </svg>

      {/* PIN SỐ nhỏ trên map (không hộp chữ -> không chồng/tràn dù bang nhỏ sát nhau) */}
      {ranked.map((d, i) => {
        // dùng ranked.length (số mục THỰC SỰ hiển thị) chứ không phải topN prop: nếu data.length < topN
        // (vd chỉ có 1-2 bang), calcMapped() đã tính durationInFrames theo topN đã CLAMP xuống data.length,
        // nhưng topN prop ở đây vẫn giữ giá trị gốc (vd 3) -> order bị tính sai -> pin/hạng mục pop SAU KHI video đã hết.
        const order = ranked.length - 1 - i;
        const at = popStart + order * Math.round(popSec * fps);
        const s = spring({ frame: f - at, fps, config: { damping: 12, stiffness: 170 } });
        if (f < at) return null;
        const [cx, cy] = centroids[i];
        return (
          <div key={"pin" + i} style={{ position: "absolute", left: cx, top: cy, transform: `translate(-50%,-50%) scale(${0.4 + s * 0.6})`, opacity: s,
            width: 52, height: 52, borderRadius: "50%", background: i === 0 ? accent : "#0b1226", border: `3px solid ${accent}`,
            display: "flex", alignItems: "center", justifyContent: "center", color: i === 0 ? "#0a0c14" : "#fff",
            fontWeight: 900, fontSize: 28, boxShadow: `0 0 20px ${accent}, 0 6px 18px #000a` }}>{i + 1}</div>
        );
      })}

      {/* BẢNG XẾP HẠNG ở DƯỚI (vùng trống, chống chồng tuyệt đối) — #3->#1 pop, #1 nổi accent */}
      <div style={{ position: "absolute", left: 70, right: 70, bottom: 150, display: "flex", flexDirection: "column", gap: 16 }}>
        {ranked.map((d, i) => {
          // dùng ranked.length (số mục THỰC SỰ hiển thị) chứ không phải topN prop: nếu data.length < topN
          // (vd chỉ có 1-2 bang), calcMapped() đã tính durationInFrames theo topN đã CLAMP xuống data.length,
          // nhưng topN prop ở đây vẫn giữ giá trị gốc (vd 3) -> order bị tính sai -> pin/hạng mục pop SAU KHI video đã hết.
          const order = ranked.length - 1 - i;
          const at = popStart + order * Math.round(popSec * fps);
          const s = spring({ frame: f - at, fps, config: { damping: 13, stiffness: 150 } });
          const lead = i === 0;
          return (
            <div key={"row" + i} style={{ order: i, transform: `translateX(${(1 - s) * -40}px)`, opacity: s,
              display: "flex", alignItems: "center", gap: 18, background: lead ? accent : "#0e1832e6",
              border: `2px solid ${lead ? accent : "#22345e"}`, borderRadius: 18, padding: lead ? "18px 26px" : "14px 24px",
              boxShadow: lead ? `0 10px 34px ${accent}66` : "0 6px 18px #0006" }}>
              <div style={{ fontWeight: 900, fontSize: lead ? 46 : 38, color: lead ? "#0a0c14" : accent, minWidth: 62 }}>#{i + 1}</div>
              <div style={{ flex: 1, fontWeight: 900, fontSize: lead ? 46 : 38, color: lead ? "#0a0c14" : "#fff", letterSpacing: -0.5 }}>{d.state.toUpperCase()}</div>
              <div style={{ fontWeight: 900, fontSize: lead ? 46 : 40, color: lead ? "#0a0c14" : "#fff", fontVariantNumeric: "tabular-nums" }}>{d.disp || d.value.toLocaleString()}</div>
            </div>
          );
        })}
      </div>

      <div style={{ position: "absolute", bottom: 54, left: 0, right: 0, textAlign: "center", color: "#ffffffcc", fontWeight: 800, fontSize: 32, textShadow: "0 2px 10px #000" }}>{handle}</div>
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
      <Karaoke subs={subs} accent={accent} />
      <Bookend title={title} handle={handle} accent={accent} color={color}
               introSec={introSec} outroSec={outroSec} />
    </AbsoluteFill>
  );
};
