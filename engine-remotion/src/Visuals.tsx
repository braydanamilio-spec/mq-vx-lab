import React, { useEffect, useState } from "react";
import { staticFile, interpolate, spring, continueRender, delayRender, Img } from "remotion";
import { geoNaturalEarth1, geoAlbersUsa, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import { scaleLinear } from "d3-scale";
import { line as d3line, area as d3area, curveMonotoneX } from "d3-shape";
import { Style, rng, hashStr } from "./Motion";

// 🎨 THƯ VIỆN VISUAL v2 — mỗi cảnh 1 hình KHỚP LỜI, đa dạng (icon/photo/map/chart/compare/metaphor).
const INK = "#161616";
const ease = (v: number, a: number, b: number, x: number, y: number) => interpolate(v, [a, b], [x, y], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
const san = (n: string) => n.replace(/[^a-z0-9]+/gi, "_");
export type Visual =
  | { kind: "bignum"; value: number; suffix?: string; label?: string; icon?: string }
  | { kind: "hero"; icon: string; label?: string; sub?: string }
  | { kind: "flow"; steps: { icon: string; label?: string }[] }
  | { kind: "timeline"; events: { year: string; label?: string }[]; title?: string }
  | { kind: "quote"; text: string }
  | { kind: "chartpro"; bars: { label: string; value: number }[]; title?: string; subtitle?: string; source?: string; unit?: string; arc?: { from: number; to: number; ratio?: string } }
  | { kind: "icons"; items: { name: string; label?: string }[]; layout?: "row" | "scatter" | "story"; accent?: string }
  | { kind: "photo"; file?: string; caption?: string; treat?: "dark" | "plain" }
  | { kind: "map"; scope?: "world" | "us"; highlight: { region: string; label?: string; value?: number; color?: string }[]; title?: string }
  | { kind: "chart"; mode?: "line" | "bar" | "area"; data: { x?: any; label?: string; y?: number; value?: number }[]; unit?: string; source?: string; title?: string }
  | { kind: "compare"; left: { icon?: string; label: string; value?: string }; right: { icon?: string; label: string; value?: string }; accent?: string }
  | { kind: "metaphor"; preset: string; value?: number; label?: string };

// ---- ICONS: danh từ khoá -> icon Iconify (đã tải về public/assets/<slug>/icons/) ----
const IconImg: React.FC<{ slug: string; name: string; size: number }> = ({ slug, name, size }) => (
  <Img src={staticFile(`assets/${slug}/icons/${san(name)}.svg`)} style={{ width: size, height: size, objectFit: "contain" }} />
);
const IconStage: React.FC<{ v: Extract<Visual, { kind: "icons" }>; l: number; slug: string; accent: string; ink: string; style?: Style }> = ({ v, l, slug, accent, ink, style }) => {
  const items = v.items.slice(0, 6); const n = items.length;
  const lay = v.layout || style?.layout || (n <= 3 ? "row" : "scatter");
  const frame = style?.frame || "badge";
  const pos = (i: number): [number, number] => {
    if (lay === "row" || lay === "story") { const x = (i - (n - 1) / 2) * 330; const y = lay === "story" ? -Math.sin((i / Math.max(1, n - 1)) * Math.PI) * 70 : 0; return [x, y]; }
    if (lay === "stack") return [(i - (n - 1) / 2) * 90, (i - (n - 1) / 2) * 150];
    if (lay === "arc") { const a = (i / Math.max(1, n - 1) - 0.5) * 1.5; return [Math.sin(a) * 460, -Math.cos(a) * 120 + 40]; }
    const ring = [[-380, -110], [380, -140], [-320, 170], [340, 175], [0, -250], [10, 210]]; return [ring[i % 6][0], ring[i % 6][1]];
  };
  const dirs = ["up", "left", "right", "zoom"];
  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
      {items.map((it, i) => {
        const r = rng(hashStr((it.name || "") + i)); const t = spring({ frame: l - i * 7, fps: 30, config: { damping: 13, mass: 0.6 } });
        const [bx, by] = pos(i); const float = Math.sin(l / 24 + i * 1.3) * 12; const wob = Math.sin(l / 40 + i) * 3;
        const dir = dirs[Math.floor(r() * dirs.length)];
        const ex = dir === "left" ? (1 - t) * -120 : dir === "right" ? (1 - t) * 120 : 0;
        const ey = dir === "up" ? (1 - t) * 80 : 0; const esc = dir === "zoom" ? 0.5 + t * 0.5 : 1;
        const sz = n <= 2 ? 220 : 190;
        // icon MÀU (2D) -> thẻ TRẮNG sạch (không đè màu accent), biến thiên hình dạng + bóng
        const box: any = frame === "badge"
          ? { background: "#fff", border: `7px solid ${ink}`, borderRadius: 40, boxShadow: `9px 11px 0 ${accent}66`, display: "inline-block" }
          : frame === "soft" ? { background: "#fff", borderRadius: "50%", boxShadow: `0 16px 38px ${ink}2e`, display: "inline-block" }
            : { background: "transparent", display: "inline-block" };
        return (
          <div key={i} style={{ position: "absolute", transform: `translate(${bx + ex}px, ${by + float + ey}px) scale(${t * esc}) rotate(${wob}deg)`, opacity: t, textAlign: "center" }}>
            {frame === "plain" && <div style={{ position: "absolute", left: "50%", top: 100, width: 260, height: 260, transform: "translate(-50%,-50%)", borderRadius: "50%", background: `radial-gradient(circle, ${accent}55, transparent 70%)` }} />}
            <div style={{ position: "relative", padding: frame === "plain" ? 8 : 26, ...box }}>
              <IconImg slug={slug} name={it.name} size={sz} />
            </div>
            {it.label && <div style={{ marginTop: 14, fontSize: 42, fontWeight: 900, color: ink }}>{it.label}</div>}
          </div>
        );
      })}
    </div>
  );
};

// ---- PHOTO: ảnh thật ĐÃ chuyển thành VẼ TAY (cartoon/ink, bake lúc tải) -> Ken Burns + vignette nhẹ ----
const PhotoStage: React.FC<{ v: Extract<Visual, { kind: "photo" }>; l: number; d: number; slug: string; dark: boolean; accent: string; ink: string; style?: Style }> = ({ v, l, d, slug, ink }) => {
  if (!v.file) return null;
  const zin = (Math.floor(v.file.charCodeAt(0) || 0) % 2) === 0;
  const z = zin ? ease(l, 0, d, 1.05, 1.18) : ease(l, 0, d, 1.18, 1.05); const px = ease(l, 0, d, -18, 18);
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
      <Img src={staticFile(`assets/${slug}/photos/${v.file}`)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", filter: "contrast(1.02) saturate(1.05)", transform: `scale(${z}) translateX(${px}px)` }} />
      <div style={{ position: "absolute", inset: 0, boxShadow: `inset 0 0 300px 70px ${ink}55`, pointerEvents: "none" }} />
      <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, rgba(10,10,16,.05), rgba(10,10,16,.5))" }} />
    </div>
  );
};

// ---- MAP: bản đồ thế giới/US, tô sáng quốc gia/bang khớp nội dung ----
const useTopo = (scope: "world" | "us") => {
  const [geo, setGeo] = useState<any>(null);
  const [handle] = useState(() => delayRender(`map-${scope}`));
  useEffect(() => {
    const file = scope === "us" ? "geo/states-10m.json" : "geo/countries-110m.json";
    fetch(staticFile(file)).then((r) => r.json()).then((topo) => {
      const key = scope === "us" ? "states" : "countries";
      setGeo(feature(topo, topo.objects[key])); continueRender(handle);
    }).catch(() => continueRender(handle));
  }, [scope, handle]);
  return geo;
};
const ALIAS: Record<string, string> = { usa: "united states of america", us: "united states of america", "united states": "united states of america", uk: "united kingdom", "u.k.": "united kingdom" };
const MapStage: React.FC<{ v: Extract<Visual, { kind: "map" }>; l: number; W: number; H: number; accent: string; ink: string }> = ({ v, l, W, H, accent, ink }) => {
  const scope = v.scope || "world"; const geo = useTopo(scope);
  if (!geo) return null;
  const proj = (scope === "us" ? geoAlbersUsa() : geoNaturalEarth1()).fitExtent([[60, 140], [W - 60, H - 90]], geo);
  const path = geoPath(proj) as any;
  const hi = new Map(v.highlight.map((h) => [(ALIAS[h.region.toLowerCase()] || h.region.toLowerCase()), h]));
  return (
    <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
      {geo.features.map((f: any, i: number) => {
        const nm = (f.properties.name || "").toLowerCase(); const h = hi.get(nm);
        const on = !!h; const app = on ? ease(l, 8, 26, 0, 1) : 1;
        return <path key={i} d={path(f)} fill={on ? (h!.color || accent) : "#DfE6EC"} fillOpacity={on ? 0.35 + 0.55 * app : 1} stroke={on ? ink : "#B9C4CC"} strokeWidth={on ? 4 : 1} />;
      })}
      {v.highlight.map((h, i) => {
        const nm = (ALIAS[h.region.toLowerCase()] || h.region.toLowerCase());
        const f = geo.features.find((x: any) => (x.properties.name || "").toLowerCase() === nm); if (!f) return null;
        const c = path.centroid(f); const app = ease(l, 14 + i * 3, 30 + i * 3, 0, 1);
        return (
          <g key={`l${i}`} transform={`translate(${c[0]},${c[1]})`} opacity={app}>
            <circle r={9} fill={ink} />
            {(h.label || h.value != null) && <g transform="translate(0,-18)">
              <rect x={-Math.max(70, ((h.label || "").length * 15) / 2)} y={-46} width={Math.max(140, (h.label || "").length * 15)} height={44} rx={10} fill={ink} />
              <text x={0} y={-16} textAnchor="middle" fontSize={26} fontWeight={900} fill="#fff">{h.label}{h.value != null ? ` ${h.value}` : ""}</text>
            </g>}
          </g>
        );
      })}
      {v.title && <text x={W / 2} y={70} textAnchor="middle" fontSize={54} fontWeight={900} fill={ink} style={{ paintOrder: "stroke" } as any} stroke="#fff" strokeWidth={7}>{v.title}</text>}
    </svg>
  );
};

// ---- CHART: line/bar/area từ DATA thật + nhãn + nguồn, vẽ dần ----
const ChartStage: React.FC<{ v: Extract<Visual, { kind: "chart" }>; l: number; W: number; H: number; accent: string; ink: string }> = ({ v, l, W, H, accent, ink }) => {
  const data = v.data.slice(0, 24); const mode = v.mode || (data[0]?.x != null ? "line" : "bar");
  const m = { t: 150, r: 90, b: 130, l: 140 }; const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const vals = data.map((d) => (d.y ?? d.value ?? 0)); const rawMax = Math.max(...vals, 1) * 1.1;
  // tick tròn đẹp
  const pow = Math.pow(10, Math.floor(Math.log10(rawMax))); const f = rawMax / pow;
  const nf = f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10; const maxV = nf * pow;
  const y = scaleLinear().domain([0, maxV]).range([m.t + ih, m.t]);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((g) => maxV * g);
  const fmt = (n: number) => (n >= 1000 ? (n / 1000).toLocaleString() + "k" : (Number.isInteger(n) ? n : n.toFixed(1)).toString());
  const grow = ease(l, 6, 40, 0, 1); const lastV = vals[vals.length - 1];
  return (
    <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
      {v.title && <text x={W / 2} y={80} textAnchor="middle" fontSize={54} fontWeight={900} fill={ink}>{v.title}</text>}
      {ticks.map((tv, i) => { const yy = y(tv); return <g key={i}><line x1={m.l} x2={m.l + iw} y1={yy} y2={yy} stroke="#00000014" strokeWidth={2} /><text x={m.l - 18} y={yy + 8} textAnchor="end" fontSize={26} fill="#666">{fmt(tv)}{v.unit || ""}</text></g>; })}
      {(mode === "bar") && data.map((d, i) => {
        const bw = iw / data.length * 0.6; const x = m.l + (i + 0.5) * (iw / data.length) - bw / 2;
        const full = (m.t + ih) - y(d.value ?? d.y ?? 0); const h = full * grow;
        return <g key={i}><rect x={x} y={(m.t + ih) - h} width={bw} height={h} rx={8} fill={accent} stroke={ink} strokeWidth={4} /><text x={x + bw / 2} y={m.t + ih + 40} textAnchor="middle" fontSize={26} fontWeight={700} fill={ink}>{d.label ?? d.x}</text></g>;
      })}
      {(mode !== "bar") && (() => {
        const x = scaleLinear().domain([0, data.length - 1]).range([m.l, m.l + iw]);
        const pts: [number, number][] = data.map((d, i) => [x(i), y(d.y ?? d.value ?? 0)]);
        const nShow = Math.max(2, Math.round(grow * data.length));
        const shown = pts.slice(0, nShow);
        const lp = d3line().curve(curveMonotoneX)(shown) || "";
        const ap = d3area().y0(m.t + ih).curve(curveMonotoneX).x((p: any) => p[0]).y1((p: any) => p[1])(shown as any) || "";
        const end = shown[shown.length - 1];
        return <g>{mode === "area" && <path d={ap} fill={accent} fillOpacity={0.28} />}
          <path d={lp} fill="none" stroke={ink} strokeWidth={16} strokeLinecap="round" strokeLinejoin="round" />
          <path d={lp} fill="none" stroke={accent} strokeWidth={9} strokeLinecap="round" strokeLinejoin="round" />
          {end && <g><circle cx={end[0]} cy={end[1]} r={14} fill={accent} stroke={ink} strokeWidth={5} />
            {grow > 0.9 && <g transform={`translate(${Math.min(end[0], m.l + iw - 120)},${end[1] - 30})`}><rect x={-64} y={-42} width={128} height={44} rx={10} fill={ink} /><text x={0} y={-12} textAnchor="middle" fontSize={28} fontWeight={900} fill="#fff">{fmt(lastV)}{v.unit || ""}</text></g>}</g>}
          {data.map((d, i) => (i === 0 || i === data.length - 1) && <text key={`x${i}`} x={x(i)} y={m.t + ih + 44} textAnchor="middle" fontSize={26} fill={ink} fontWeight={700}>{d.label ?? d.x}</text>)}</g>;
      })()}
      {v.source && <text x={W / 2} y={H - 30} textAnchor="middle" fontSize={24} fill="#888">Source: {v.source} (approx.)</text>}
    </svg>
  );
};

// ---- COMPARE: A vs B ----
const Side: React.FC<{ s: any; slug: string; l: number; delay: number; accent: string; ink: string }> = ({ s, slug, l, delay, accent, ink }) => {
  const t = spring({ frame: l - delay, fps: 30, config: { damping: 13 } });
  return <div style={{ flex: 1, textAlign: "center", transform: `scale(${t})`, opacity: t }}>
    {s.icon && <div style={{ background: "#fff", border: `9px solid ${ink}`, borderRadius: 34, padding: 24, display: "inline-block", boxShadow: `8px 10px 0 ${accent}55` }}><IconImg slug={slug} name={s.icon} size={200} /></div>}
    <div style={{ marginTop: 18, fontSize: 46, fontWeight: 900, color: ink }}>{s.label}</div>
    {s.value && <div style={{ fontSize: 92, fontWeight: 900, color: accent, WebkitTextStroke: `6px ${ink}` as any }}>{s.value}</div>}
  </div>;
};
const CompareStage: React.FC<{ v: Extract<Visual, { kind: "compare" }>; l: number; slug: string; accent: string; ink: string }> = ({ v, l, slug, accent, ink }) => (
  <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", gap: 40, padding: "0 120px" }}>
    <Side s={v.left} slug={slug} l={l} delay={4} accent={ink === "#161616" ? "#2FA84F" : accent} ink={ink} />
    <div style={{ fontSize: 120, fontWeight: 900, color: ink, opacity: ease(l, 10, 22, 0, 1) }}>vs</div>
    <Side s={v.right} slug={slug} l={l} delay={12} accent={v.accent || "#E4562B"} ink={ink} />
  </div>
);

// ---- METAPHOR: vài preset hình ẩn dụ ----
const MetaphorStage: React.FC<{ v: Extract<Visual, { kind: "metaphor" }>; l: number; W: number; H: number; accent: string; ink: string }> = ({ v, l, W, H, accent, ink }) => {
  const cx = W / 2, cy = H / 2 + 60; const g = ease(l, 6, 40, 0, 1);
  if (v.preset === "coin-stack") {
    const n = Math.min(11, Math.max(3, Math.round((v.value || 8)))); const shown = Math.round(n * g);
    return <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>{Array.from({ length: shown }).map((_, i) => <g key={i} transform={`translate(${cx},${cy - i * 46})`}><ellipse rx={118} ry={30} fill="#FFCE47" stroke="#E0A21B" strokeWidth={3} /><ellipse rx={118} ry={30} cy={-6} fill="#FFDD73" stroke="#E0A21B" strokeWidth={2} /><text y={4} textAnchor="middle" fontSize={34} fontWeight={900} fill="#B67A10">$</text></g>)}{v.label && <text x={cx} y={cy + 96} textAnchor="middle" fontSize={44} fontWeight={900} fill={ink}>{v.label}</text>}</svg>;
  }
  if (v.preset === "scale") {
    const tilt = Math.sin(l / 20) * 8;
    return <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}><g transform={`translate(${cx},${cy})`}><rect x={-8} y={-220} width={16} height={220} fill={ink} /><g transform={`rotate(${tilt})`}><rect x={-320} y={-224} width={640} height={16} rx={8} fill={ink} /><circle cx={-320} cy={-180} r={80} fill={accent} stroke={ink} strokeWidth={7} /><circle cx={320} cy={-180} r={80} fill="#E4562B" stroke={ink} strokeWidth={7} /></g></g>{v.label && <text x={cx} y={cy + 120} textAnchor="middle" fontSize={44} fontWeight={900} fill={ink}>{v.label}</text>}</svg>;
  }
  // staircase (mặc định)
  const steps = Math.min(8, Math.max(3, Math.round(v.value || 5))); const shown = Math.round(steps * g);
  return <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>{Array.from({ length: shown }).map((_, i) => <rect key={i} x={cx - 340 + i * 90} y={cy - i * 60} width={90} height={60 + i * 60} fill={accent} stroke={ink} strokeWidth={5} />)}{v.label && <text x={cx} y={cy + 120} textAnchor="middle" fontSize={44} fontWeight={900} fill={ink}>{v.label}</text>}</svg>;
};

// ---- BIGNUM: một con số lớn (count-up) + nhãn + icon tuỳ chọn — cho cảnh stat ----
const BigNum: React.FC<{ v: Extract<Visual, { kind: "bignum" }>; l: number; slug: string; W: number; H: number; accent: string; ink: string }> = ({ v, l, slug, W, H, accent, ink }) => {
  const dec = Math.abs(v.value) < 10 && Math.round(v.value) !== v.value; const cur = ease(l, 8, 46, 0, v.value);
  const shown = dec ? cur.toFixed(2) : Math.round(cur).toLocaleString();
  const pop = spring({ frame: l - 4, fps: 30, config: { damping: 12 } });
  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", transform: `scale(${0.9 + pop * 0.1})` }}>
      {v.icon && <div style={{ background: "#fff", border: `9px solid ${ink}`, borderRadius: 34, padding: 22, marginBottom: 26, boxShadow: `10px 12px 0 ${accent}55` }}><IconImg slug={slug} name={v.icon} size={160} /></div>}
      <div style={{ fontSize: 290, fontWeight: 900, color: accent, WebkitTextStroke: `7px ${ink}` as any, paintOrder: "stroke", lineHeight: 0.9, textShadow: `6px 7px 0 ${ink}22` } as any}>{shown}{v.suffix || ""}</div>
      {v.label && <div style={{ fontSize: 58, fontWeight: 800, color: ink, marginTop: 18, textAlign: "center", maxWidth: 1300 }}>{v.label}</div>}
    </div>
  );
};

// ---- HERO: 1 minh hoạ LỚN + nhãn (nhịp khác hẳn icon-trio) ----
const HeroStage: React.FC<{ v: Extract<Visual, { kind: "hero" }>; l: number; slug: string; accent: string; ink: string }> = ({ v, l, slug, accent, ink }) => {
  const pop = spring({ frame: l, fps: 30, config: { damping: 11, mass: 0.7 } }); const float = Math.sin(l / 26) * 16; const rot = Math.sin(l / 44) * 3;
  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
      <div style={{ transform: `translateY(${float}px) scale(${pop}) rotate(${rot}deg)`, filter: `drop-shadow(0 20px 34px ${ink}30)` }}><IconImg slug={slug} name={v.icon} size={440} /></div>
      {v.label && <div style={{ marginTop: 24, fontSize: 76, fontWeight: 900, color: ink, textAlign: "center", maxWidth: 1500, lineHeight: 1.05 }}>{v.label}</div>}
      {v.sub && <div style={{ marginTop: 10, fontSize: 44, fontWeight: 800, color: accent }}>{v.sub}</div>}
    </div>
  );
};
// ---- FLOW: quy trình icon nối bằng mũi tên ----
const FlowStage: React.FC<{ v: Extract<Visual, { kind: "flow" }>; l: number; slug: string; accent: string; ink: string }> = ({ v, l, slug, ink, accent }) => {
  const steps = v.steps.slice(0, 4); const n = steps.length;
  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", gap: 8, padding: "0 60px" }}>
      {steps.map((s, i) => { const t = spring({ frame: l - i * 11, fps: 30, config: { damping: 13 } }); const fl = Math.sin(l / 24 + i) * 8; return (
        <React.Fragment key={i}>
          <div style={{ textAlign: "center", transform: `translateY(${fl}px) scale(${t})`, opacity: t }}>
            <div style={{ background: "#fff", border: `7px solid ${ink}`, borderRadius: 32, padding: 22, display: "inline-block", boxShadow: `0 12px 26px ${ink}22` }}><IconImg slug={slug} name={s.icon} size={150} /></div>
            {s.label && <div style={{ marginTop: 12, fontSize: 34, fontWeight: 800, color: ink, maxWidth: 280 }}>{s.label}</div>}
          </div>
          {i < n - 1 && <div style={{ fontSize: 86, fontWeight: 900, color: accent, opacity: ease(l, i * 11 + 6, i * 11 + 16, 0, 1), marginBottom: 40 }}>→</div>}
        </React.Fragment>); })}
    </div>
  );
};
// ---- TIMELINE: mốc thời gian ngang ----
const TimelineStage: React.FC<{ v: Extract<Visual, { kind: "timeline" }>; l: number; W: number; H: number; accent: string; ink: string }> = ({ v, l, W, H, accent, ink }) => {
  const ev = v.events.slice(0, 6); const n = ev.length; const y = H * 0.52; const x0 = 200, x1 = W - 200; const grow = ease(l, 6, 42, 0, 1);
  return (
    <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
      {v.title && <text x={W / 2} y={110} textAnchor="middle" fontSize={54} fontWeight={900} fill={ink}>{v.title}</text>}
      <line x1={x0} y1={y} x2={x0 + (x1 - x0) * grow} y2={y} stroke={ink} strokeWidth={9} strokeLinecap="round" />
      {ev.map((e, i) => { const px = x0 + (x1 - x0) * (i / Math.max(1, n - 1)); const app = ease(l, 12 + i * 4, 24 + i * 4, 0, 1); const up = i % 2 === 0; return (
        <g key={i} opacity={app} transform={`translate(${px},${y})`}>
          <line x1={0} y1={0} x2={0} y2={up ? -78 : 78} stroke={ink} strokeWidth={4} />
          <circle r={15} fill={accent} stroke={ink} strokeWidth={5} />
          <text textAnchor="middle" y={up ? -92 : 118} fontSize={40} fontWeight={900} fill={accent}>{e.year}</text>
          {e.label && <text textAnchor="middle" y={up ? -56 : 152} fontSize={27} fontWeight={700} fill={ink}>{e.label}</text>}
        </g>); })}
    </svg>
  );
};
// ---- QUOTE: câu nhấn lớn (đổi nhịp thị giác) ----
const QuoteStage: React.FC<{ v: Extract<Visual, { kind: "quote" }>; l: number; accent: string; ink: string; dark?: boolean }> = ({ v, l, accent, ink, dark = false }) => {
  const p = spring({ frame: l, fps: 30, config: { damping: 14 } });
  if (dark) {
    // Callout chữ động cho kênh nền tối (data-viz): chữ sáng + gạch accent, không dấu nháy serif.
    return (
      <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", padding: "0 220px" }}>
        <div style={{ transform: `translateY(${(1 - p) * 26}px)`, opacity: p, textAlign: "center", maxWidth: 1650 }}>
          <div style={{ width: 120, height: 10, background: accent, borderRadius: 6, margin: "0 auto 40px", boxShadow: `0 0 26px ${accent}` }} />
          <div style={{ fontSize: 92, fontWeight: 900, color: "#EAF2FF", lineHeight: 1.16, textShadow: "0 3px 24px rgba(0,0,0,0.5)" }}>{v.text}</div>
        </div>
      </div>
    );
  }
  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", padding: "0 170px" }}>
      <div style={{ transform: `scale(${0.92 + p * 0.08})`, opacity: p, textAlign: "center" }}>
        <div style={{ fontSize: 150, color: accent, lineHeight: 0.4, fontWeight: 900, fontFamily: "Georgia,serif" }}>&ldquo;</div>
        <div style={{ fontSize: 78, fontWeight: 900, color: ink, lineHeight: 1.14, maxWidth: 1450 }}>{v.text}</div>
      </div>
    </div>
  );
};

// ---- CHARTPRO: biểu đồ phân tích CAO CẤP (nền tối, cột texture mép gồ ghề, cung so sánh, nguồn) — "data break" sang chảnh ----
const ChartPro: React.FC<{ v: Extract<Visual, { kind: "chartpro" }>; l: number; W: number; H: number; accent: string }> = ({ v, l, W, H, accent }) => {
  const bars = v.bars.slice(0, 5); const n = bars.length || 1; const maxV = Math.max(...bars.map((b) => b.value), 1);
  const base = H * 0.80, top = H * 0.26, x0 = W * 0.06, area = W * 0.9, slot = area / n, bw = slot * 0.5; // base cao hơn -> nhãn cột ko bị phụ đề che
  const grow = ease(l, 8, 46, 0, 1); const xOf = (i: number) => x0 + slot * i + (slot - bw) / 2; const hOf = (val: number) => (base - top) * (val / maxV);
  const jag = (x: number, w: number, yTop: number) => { let p = `M ${x} ${base} L ${x} ${yTop + 6}`; const seg = 9; for (let k = 0; k <= seg; k++) { const xx = x + w * k / seg; const off = Math.sin(k * 2.1 + x * 0.3) * 7 - (k % 2 ? 7 : 0); p += ` L ${xx.toFixed(1)} ${(yTop + off).toFixed(1)}`; } p += ` L ${x + w} ${base} Z`; return p; };
  return (
    <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <filter id="cpglow"><feGaussianBlur stdDeviation="7" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        <radialGradient id="cpbg" cx="50%" cy="26%" r="85%"><stop offset="0%" stopColor="#171a20" /><stop offset="100%" stopColor="#090a0d" /></radialGradient>
      </defs>
      <rect x={0} y={0} width={W} height={H} fill="url(#cpbg)" />
      {Array.from({ length: 90 }).map((_, i) => <circle key={i} cx={(i * 173) % W} cy={(i * 97) % H} r={1.2} fill="#fff" opacity={0.045} />)}
      <path d={`M0 ${base + 2} ${Array.from({ length: 22 }).map((_, i) => `L ${(i * W / 21).toFixed(0)} ${(base + 2 + Math.sin(i + l / 12) * 4).toFixed(1)}`).join(" ")}`} stroke="#2D9CDB" strokeWidth={3} fill="none" opacity={0.55} />
      {v.title && <text x={44} y={82} fontSize={62} fontWeight={900} fill="#fff" fontFamily="'Poppins',Arial">{v.title.toUpperCase()}</text>}
      {v.subtitle && <text x={46} y={122} fontSize={27} fontWeight={700} fill="#8a94a0" letterSpacing={4} fontFamily="'Poppins',Arial">{v.subtitle.toUpperCase()}</text>}
      {bars.map((b, i) => { const x = xOf(i); const gi = ease(l, 8 + i * 6, 44 + i * 6, 0, 1); const h = hOf(b.value) * gi; const yTop = base - h; const dec = Math.abs(b.value) < 10 && Math.round(b.value) !== b.value; const shown = dec ? (b.value * gi).toFixed(1) : Math.round(b.value * gi).toLocaleString(); return (
        <g key={i}>
          <path d={jag(x, bw, yTop)} fill={accent} filter="url(#cpglow)" opacity={0.82 + 0.12 * Math.sin(l / 15 + i)} />
          {Array.from({ length: 6 }).map((_, k) => <line key={k} x1={x + bw * (k + 0.5) / 6} y1={yTop + 8} x2={x + bw * (k + 0.5) / 6} y2={base} stroke="#090a0d" strokeWidth={2} opacity={0.32} />)}
          {gi > 0.04 && <text x={x + bw / 2} y={yTop - 20} textAnchor="middle" fontSize={44} fontWeight={900} fill={accent} letterSpacing={2} fontFamily="'Poppins',Arial" opacity={Math.min(1, gi * 3)}>{v.unit && v.unit.trim().startsWith("$") ? "$" + shown + v.unit.trim().slice(1) : shown + (v.unit || "")}</text>}
          <text x={x + bw / 2} y={base + 40} textAnchor="middle" fontSize={26} fontWeight={800} fill="#aeb6c2" letterSpacing={2} fontFamily="'Poppins',Arial">{(b.label || "").toUpperCase()}</text>
        </g>); })}
      {v.arc && bars[v.arc.from] && bars[v.arc.to] && (() => { const a = v.arc!; const xa = xOf(a.from) + bw / 2, ya = base - hOf(bars[a.from].value); const xb = xOf(a.to) + bw / 2, yb = base - hOf(bars[a.to].value); const mx = (xa + xb) / 2, my = Math.min(ya, yb) - 130; const prog = ease(l, 24, 54, 0, 1); const t = prog; const dx = (1 - t) * (1 - t) * xa + 2 * (1 - t) * t * mx + t * t * xb; const dy = (1 - t) * (1 - t) * ya + 2 * (1 - t) * t * my + t * t * yb; return (
        <g><path d={`M ${xa} ${ya} Q ${mx} ${my} ${xb} ${yb}`} stroke="#E4562B" strokeWidth={7} fill="none" strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - prog} />
          {prog > 0.02 && prog < 0.99 && <circle cx={dx} cy={dy} r={11} fill="#E4562B" filter="url(#cpglow)" />}
          {a.ratio && ease(l, 46, 56, 0, 1) > 0.3 && <text x={mx} y={my + 34} textAnchor="middle" fontSize={48} fontWeight={900} fill={accent} opacity={ease(l, 46, 56, 0, 1)}>{a.ratio}</text>}</g>); })()}
      {v.source && <text x={W / 2} y={H - 22} textAnchor="middle" fontSize={22} fill="#5a626c" letterSpacing={2} fontFamily="'Poppins',Arial">{v.source} (approx.)</text>}
    </svg>
  );
};

export const VisualStage: React.FC<{ v: Visual; l: number; d: number; slug: string; W: number; H: number; accent: string; ink?: string; dark?: boolean; style?: Style }> = ({ v, l, d, slug, W, H, accent, ink = INK, dark = false, style }) => {
  switch (v.kind) {
    case "bignum": return <BigNum v={v} l={l} slug={slug} W={W} H={H} accent={accent} ink={ink} />;
    case "chartpro": return <ChartPro v={v} l={l} W={W} H={H} accent={accent} />;
    case "hero": return <HeroStage v={v} l={l} slug={slug} accent={accent} ink={ink} />;
    case "flow": return <FlowStage v={v} l={l} slug={slug} accent={accent} ink={ink} />;
    case "timeline": return <TimelineStage v={v} l={l} W={W} H={H} accent={accent} ink={ink} />;
    case "quote": return <QuoteStage v={v} l={l} accent={accent} ink={ink} dark={dark} />;
    case "icons": return <IconStage v={v} l={l} slug={slug} accent={v.accent || accent} ink={ink} style={style} />;
    case "photo": return <PhotoStage v={v} l={l} d={d} slug={slug} dark={dark} accent={accent} ink={ink} style={style} />;
    case "map": return <MapStage v={v} l={l} W={W} H={H} accent={accent} ink={ink} />;
    case "chart": return <ChartStage v={v} l={l} W={W} H={H} accent={accent} ink={ink} />;
    case "compare": return <CompareStage v={v} l={l} slug={slug} accent={accent} ink={ink} />;
    case "metaphor": return <MetaphorStage v={v} l={l} W={W} H={H} accent={accent} ink={ink} />;
    default: return null;
  }
};
