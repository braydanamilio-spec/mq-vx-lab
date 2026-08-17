import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTES, Pal } from "./scenegen";

// THƯ VIỆN MINH HOẠ ẨN DỤ — mỗi concept = 1 hình NHIỀU LỚP kể được Ý (không phải icon phẳng).
// Tham số: W,H khung · p (0..1 reveal) · t (thời gian) · pal (màu) · wide.
const clamp = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const ease = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const D = (deg: number) => (deg * Math.PI) / 180;

type CP = { W: number; H: number; p: number; t: number; pal: Pal; cy: number };

const coin = (x: number, y: number, r: number, ink: string, s = 1) => (
  <g transform={`translate(${x} ${y}) scale(${s})`}><circle r={r} fill="#F5B301" stroke={ink} strokeWidth={4} /><circle r={r - 9} fill="none" stroke={ink} strokeWidth={3} /><text y={r * 0.55} textAnchor="middle" fontFamily="Poppins,sans-serif" fontWeight={900} fontSize={r * 1.15} fill={ink}>$</text></g>);

export const CONCEPTS: Record<string, (c: CP) => any> = {
  // TIỀN CHẢY ĐI vì subscriptions: ví mở -> coin bay -> loạt thẻ app
  subscriptions: ({ W, H, p, t, pal, cy }) => {
    const ink = pal.ink, wx = W * 0.28, cardX = W * 0.66;
    const cards = [["#E23744", "▶"], ["#1DB954", "♪"], ["#3E7BFA", "☁"], ["#7C5CFF", "▦"]];
    return (<g>
      {/* ví */}
      <g stroke={ink} strokeWidth={6}><rect x={wx - 120} y={cy - 60} width={240} height={150} rx={20} fill="#8a5a3a" /><rect x={wx - 120} y={cy - 60} width={240} height={54} rx={20} fill="#a9764e" /><rect x={wx + 30} y={cy - 4} width={70} height={44} rx={8} fill="#F5B301" /><circle cx={wx + 65} cy={cy + 18} r={9} fill={ink} /></g>
      {/* thẻ app (fan) */}
      {cards.map(([col, sym], i) => { const yy = cy - 150 + i * 100, pop = clamp((p - 0.15 - i * 0.08) * 4); return (
        <g key={i} transform={`translate(${cardX} ${yy}) scale(${lerp(0.4, 1, ease(pop))})`} opacity={pop} stroke={ink} strokeWidth={5}><rect x={-90} y={-38} width={180} height={76} rx={16} fill={col as string} /><text x={0} y={16} textAnchor="middle" fontFamily="Poppins,sans-serif" fontWeight={900} fontSize={44} fill="#fff">{sym as string}</text></g>); })}
      {/* coin bay LIÊN TỤC theo cung từ ví -> thẻ (tiền chảy đi hoài) */}
      {[0, 1, 2, 3, 4].map((i) => { const ph = ((t * 0.5 + i * 0.22) % 1); const ax = lerp(wx, cardX - 40, ease(ph)); const ay = cy - Math.sin(ph * Math.PI) * (H * 0.28) - lerp(0, 30, ph); const vis = clamp(p * 2) * (ph > 0.03 && ph < 0.97 ? 1 : 0); return <g key={i} opacity={vis}>{coin(ax, ay, 26, ink, lerp(1, 0.7, ph))}</g>; })}
    </g>);
  },

  // TRUNG GIAN ĂN CHẶN: cọc tiền qua tay -> nhỏ dần -> còn tí xíu
  middlemen: ({ W, H, p, t, pal, cy }) => {
    const ink = pal.ink; const stacks = [1, 0.72, 0.46, 0.22]; const xs = [W * 0.16, W * 0.38, W * 0.6, W * 0.82];
    return (<g>
      {stacks.map((h, i) => { const pop = clamp((p - i * 0.16) * 4); const bh = 40 + h * 200; return (
        <g key={i} opacity={pop}>
          {/* cọc tiền */}
          <g transform={`translate(${xs[i]} ${cy + 90})`} stroke={ink} strokeWidth={4}>{Array.from({ length: Math.max(1, Math.round(h * 6)) }).map((_, k) => <rect key={k} x={-52} y={-k * 22 - 30} width={104} height={22} rx={4} fill={k % 2 ? "#2FA84F" : "#37c06a"} />)}<text x={0} y={-Math.max(1, Math.round(h * 6)) * 22 - 40} textAnchor="middle" fontFamily="Poppins,sans-serif" fontWeight={900} fontSize={38} fill={ink}>${Math.round(h * 100)}</text></g>
          {/* bàn tay/mũi tên lấy cắt giữa các cọc */}
          {i < 3 && <g opacity={clamp((p - i * 0.16 - 0.1) * 4)}><path d={`M ${xs[i] + 60} ${cy} L ${xs[i + 1] - 60} ${cy}`} stroke={ink} strokeWidth={7} markerEnd="" fill="none" /><path d={`M ${xs[i + 1] - 70} ${cy - 14} L ${xs[i + 1] - 50} ${cy} L ${xs[i + 1] - 70} ${cy + 14}`} fill="none" stroke={ink} strokeWidth={7} /><text x={(xs[i] + xs[i + 1]) / 2} y={cy - 26} textAnchor="middle" fontFamily="Poppins,sans-serif" fontWeight={900} fontSize={34} fill="#E23744">-{Math.round((stacks[i] - stacks[i + 1]) * 100)}%</text><circle cx={(xs[i] + xs[i + 1]) / 2} cy={cy + 40} r={22} fill="#F5B301" stroke={ink} strokeWidth={4} /></g>}
        </g>); })}
    </g>);
  },

  // GIÁ TĂNG VỌT: mũi tên đỏ dốc lên, $ to dần, người nhỏ ngước nhìn
  pricerise: ({ W, H, p, t, pal, cy }) => {
    const ink = pal.ink; const x0 = W * 0.2, y0 = cy + 160, x1 = W * 0.8, y1 = cy - 200; const pe = ease(clamp(p * 1.1));
    const ax = lerp(x0, x1, pe), ay = lerp(y0, y1, pe);
    return (<g>
      {/* trục */}
      <line x1={x0} y1={y0} x2={x0} y2={cy - 220} stroke={ink} strokeWidth={6} opacity={0.4} /><line x1={x0} y1={y0} x2={W * 0.85} y2={y0} stroke={ink} strokeWidth={6} opacity={0.4} />
      {/* mũi tên đỏ dốc lên */}
      <path d={`M ${x0} ${y0} Q ${lerp(x0, x1, 0.5)} ${lerp(y0, y1, 0.15)} ${ax} ${ay}`} fill="none" stroke="#E23744" strokeWidth={16} strokeLinecap="round" />
      <path d={`M ${ax - 34} ${ay + 6} L ${ax + 6} ${ay - 30} L ${ax + 30} ${ay + 20} Z`} fill="#E23744" transform={`rotate(34 ${ax} ${ay})`} opacity={clamp((p - 0.7) * 5)} />
      {/* $ to dần dọc mũi tên */}
      {[0.25, 0.55, 0.85].map((f, i) => { const px = lerp(x0, x1, f), py = lerp(y0, y1, f) - 40; const pop = clamp((p - f * 0.7) * 4); return <g key={i} opacity={pop}>{coin(px, py, 22 + i * 12, ink)}</g>; })}
      {/* người nhỏ ngước nhìn */}
      <g transform={`translate(${x0 - 30} ${y0 + 30})`} stroke={ink} strokeWidth={5}><circle cy={-40} r={24} fill={pal.sw?.[1] || "#F1B784"} /><path d="M-22 40 Q0 -6 22 40 Z" fill="#39454F" /></g>
    </g>);
  },

  // ĐỘC QUYỀN: 1 toà khổng lồ đè bẹp mấy toà tí hon
  monopoly: ({ W, H, p, pal, cy }) => { const ink = pal.ink; const gh = ease(clamp(p * 1.2)) * (H * 0.44); return (<g>
    {[[W * 0.2, 0.5], [W * 0.34, 0.35], [W * 0.7, 0.42], [W * 0.84, 0.3]].map(([x, h], i) => { const pop = clamp((p - 0.3 - i * 0.05) * 4); const bh = (h as number) * H * 0.3 * pop; return <g key={i} opacity={pop}><rect x={(x as number) - 42} y={cy + 120 - bh} width={84} height={bh} fill="#9db9d8" stroke={ink} strokeWidth={4} /></g>; })}
    <g><rect x={W * 0.5 - 110} y={cy + 120 - gh} width={220} height={gh} fill="#E23744" stroke={ink} strokeWidth={6} />{Array.from({ length: 5 }).map((_, r) => [0, 1, 2].map((cN) => <rect key={`${r}${cN}`} x={W * 0.5 - 80 + cN * 58} y={cy + 120 - gh + 26 + r * (gh / 6)} width={38} height={gh / 11} fill="#ffd76b" opacity={0.9} />))}<text x={W * 0.5} y={cy + 120 - gh - 20} textAnchor="middle" fontFamily="Poppins,sans-serif" fontWeight={900} fontSize={54} fill={ink}>$</text></g>
  </g>); },

  // PHÍ ẨN: hoá đơn dài + kính lúp soi ra dòng đỏ
  hiddenfees: ({ W, H, p, pal, cy }) => { const ink = pal.ink; const rx = W * 0.42; return (<g>
    <g stroke={ink} strokeWidth={5}><rect x={rx - 130} y={cy - 200} width={260} height={420} rx={8} fill="#fff" /><rect x={rx - 100} y={cy - 170} width={200} height={20} fill={ink} opacity={0.25} />{[0, 1, 2, 3, 4, 5].map((i) => <rect key={i} x={rx - 100} y={cy - 120 + i * 44} width={200} height={12} fill={i === 3 ? "#E23744" : "#00000022"} />)}<text x={rx + 60} y={cy + 20} fontFamily="Poppins,sans-serif" fontWeight={900} fontSize={30} fill="#E23744" opacity={clamp((p - 0.4) * 4)}>-$9</text></g>
    <g transform={`translate(${rx + 40 + Math.cos(p * 6) * 6} ${cy + 40})`} stroke={ink} strokeWidth={9} opacity={clamp(p * 2)}><circle r={70} fill="#bfe3ff44" /><line x1={50} y1={50} x2={110} y2={110} strokeLinecap="round" /></g>
  </g>); },

  // NỢ: người kéo quả cầu $ khổng lồ xích chân
  debt: ({ W, H, p, pal, cy }) => { const ink = pal.ink; const px = W * 0.4; const pop = ease(clamp(p * 1.3)); return (<g>
    <g transform={`translate(${px} ${cy})`} stroke={ink} strokeWidth={6}><circle cy={-70} r={44} fill={pal.sw?.[1] || "#F1B784"} /><path d="M-40 90 Q0 -30 40 90 Z" fill="#39454F" /></g>
    {Array.from({ length: 5 }).map((_, i) => <circle key={i} cx={px + 60 + i * 34} cy={cy + 80} r={12} fill="none" stroke={ink} strokeWidth={6} opacity={pop} />)}
    <g transform={`translate(${px + 300} ${cy + 90}) scale(${lerp(0.4, 1, pop)})`} stroke={ink} strokeWidth={6}><circle r={80} fill="#3a4657" /><text y={22} textAnchor="middle" fontFamily="Poppins,sans-serif" fontWeight={900} fontSize={70} fill="#F5B301">$</text></g>
  </g>); },

  // WALL STREET THÂU TÓM NHÀ: bàn tay vest to bốc nhà nhỏ
  ownshomes: ({ W, H, p, pal, cy }) => { const ink = pal.ink; const lift = ease(clamp(p * 1.2)); return (<g>
    {[[W * 0.24, 0], [W * 0.4, 0], [W * 0.56, 1]].map(([x, grabbed], i) => { const gy = grabbed ? cy - lift * 150 : cy + 60; return (<g key={i} transform={`translate(${x} ${gy})`} stroke={ink} strokeWidth={5}><path d="M-56 0 L0 -50 L56 0 Z" fill="#E23744" /><rect x={-44} y={0} width={88} height={60} fill="#e8c477" /><rect x={-14} y={20} width={28} height={40} fill="#7a4f30" /></g>); })}
    {/* bàn tay vest chộp */}
    <g transform={`translate(${W * 0.56} ${cy - lift * 150 - 90})`} stroke={ink} strokeWidth={5}><rect x={-46} y={40} width={92} height={70} rx={14} fill="#2b2f3a" />{[-30, -10, 10, 30].map((fx, i) => <rect key={i} x={fx - 7} y={-10} width={14} height={60} rx={7} fill={pal.sw?.[1] || "#F1B784"} />)}<rect x={-52} y={30} width={104} height={20} fill="#fff" /></g>
  </g>); },

  // LẠM PHÁT: tờ đô teo nhỏ dần, giá mũi tên lên
  inflation: ({ W, H, p, pal, cy }) => { const ink = pal.ink; return (<g>
    {[1, 0.7, 0.45, 0.25].map((s, i) => { const pop = clamp((p - i * 0.14) * 4); return (<g key={i} transform={`translate(${W * 0.18 + i * W * 0.17} ${cy}) scale(${s})`} opacity={pop} stroke={ink} strokeWidth={5}><rect x={-90} y={-54} width={180} height={108} rx={10} fill="#2FA84F" /><circle r={34} fill="#37c06a" stroke={ink} strokeWidth={4} /><text y={16} textAnchor="middle" fontFamily="Poppins,sans-serif" fontWeight={900} fontSize={44} fill="#fff">$</text></g>); })}
    <path d={`M ${W * 0.16} ${cy + 150} Q ${W * 0.5} ${cy + 120} ${W * 0.86} ${cy - 60}`} fill="none" stroke="#E23744" strokeWidth={12} strokeLinecap="round" opacity={clamp((p - 0.4) * 3)} />
  </g>); },

  // BỔ PHÂN LƯƠNG: bánh tròn chia miếng, phần "bạn" tí xíu
  paycheck: ({ W, H, p, pal, cy }) => { const ink = pal.ink; const segs = [["Rent", 0.4, "#E23744"], ["Taxes", 0.25, "#3E7BFA"], ["Food", 0.18, "#F5B301"], ["Fun", 0.1, "#7C5CFF"], ["YOU", 0.07, "#2FA84F"]]; let a0 = -90; const R = Math.min(W, H) * 0.26; const cx = W * 0.42; const pe = ease(clamp(p * 1.2)); return (<g>
    {segs.map(([lab, frac, col], i) => { const sweep = (frac as number) * 360 * pe; const a1 = a0 + sweep; const large = sweep > 180 ? 1 : 0; const x1 = cx + R * Math.cos(D(a0)), y1 = cy + R * Math.sin(D(a0)); const x2 = cx + R * Math.cos(D(a1)), y2 = cy + R * Math.sin(D(a1)); const mid = (a0 + a1) / 2; a0 = a1; return (<g key={i}><path d={`M ${cx} ${cy} L ${x1} ${y1} A ${R} ${R} 0 ${large} 1 ${x2} ${y2} Z`} fill={col as string} stroke={ink} strokeWidth={4} /><text x={cx + R * 0.66 * Math.cos(D(mid))} y={cy + R * 0.66 * Math.sin(D(mid))} textAnchor="middle" fontFamily="Poppins,sans-serif" fontWeight={800} fontSize={26} fill="#fff">{lab as string}</text></g>); })}
  </g>); },

  // BẪY: bẫy chuột, mồi là tờ tiền
  trap: ({ W, H, p, pal, cy }) => { const ink = pal.ink; const snap = clamp((p - 0.6) * 6); const bar = lerp(-70, 6, ease(snap)); return (<g transform={`translate(${W * 0.42} ${cy + 40})`}>
    <rect x={-170} y={0} width={340} height={120} rx={12} fill="#c8a06a" stroke={ink} strokeWidth={6} />
    <rect x={40} y={-14} width={110} height={54} rx={8} fill="#2FA84F" stroke={ink} strokeWidth={5} /><text x={95} y={20} textAnchor="middle" fontFamily="Poppins,sans-serif" fontWeight={900} fontSize={34} fill="#fff">$</text>
    <g transform={`rotate(${bar} -120 20)`} stroke={ink} strokeWidth={12} strokeLinecap="round"><line x1={-120} y1={20} x2={90} y2={20} /></g>
    <circle cx={-120} cy={20} r={12} fill={ink} />
  </g>); },

  // BẤT BÌNH ĐẲNG: 1 người tí trên cọc tí, 1 người trên cọc khổng lồ
  gap: ({ W, H, p, pal, cy }) => { const ink = pal.ink; const g1 = ease(clamp(p * 1.2)) * 40, g2 = ease(clamp(p * 1.2)) * 300; const fig = (x: number, top: number, col: string) => (<g transform={`translate(${x} ${top})`} stroke={ink} strokeWidth={5}><circle cy={-34} r={22} fill={col} /><path d="M-20 40 Q0 -4 20 40 Z" fill="#39454F" /></g>); return (<g>
    <g transform={`translate(${W * 0.28} ${cy + 130})`}>{Array.from({ length: 1 }).map((_, k) => <rect key={k} x={-52} y={-k * 22 - 22} width={104} height={22} rx={4} fill="#2FA84F" stroke={ink} strokeWidth={4} />)}</g>{fig(W * 0.28, cy + 108 - g1, pal.sw?.[3] || "#F1B784")}
    <g transform={`translate(${W * 0.72} ${cy + 130})`}>{Array.from({ length: 12 }).map((_, k) => <rect key={k} x={-52} y={-k * 22 - 22} width={104} height={22} rx={4} fill={k % 2 ? "#2FA84F" : "#37c06a"} stroke={ink} strokeWidth={3} />)}</g>{fig(W * 0.72, cy + 108 - g2, "#F5B301")}
  </g>); },

  // THỜI GIAN = TIỀN: đồng hồ cát, coin rơi
  timemoney: ({ W, H, p, t, pal, cy }) => { const ink = pal.ink; const cx = W * 0.5; return (<g>
    <g transform={`translate(${cx} ${cy})`} stroke={ink} strokeWidth={7}><path d="M-110 -150 L110 -150 M-110 150 L110 150" strokeLinecap="round" /><path d="M-90 -150 Q-90 -20 0 0 Q90 -20 90 -150 Z" fill="#eef4ff" /><path d="M-90 150 Q-90 20 0 0 Q90 20 90 150 Z" fill="#eef4ff" />
      {/* coin trên + dưới */}
      <g clipPath="none">{Array.from({ length: 6 }).map((_, i) => <circle key={i} cx={-50 + (i % 3) * 50} cy={-60 - Math.floor(i / 3) * 30} r={16} fill="#F5B301" stroke={ink} strokeWidth={3} opacity={clamp(1 - p)} />)}</g>
      <circle cx={0} cy={30 + (Math.sin(t * 4) * 4)} r={12} fill="#F5B301" stroke={ink} strokeWidth={3} opacity={clamp(p * 2)} />
      {Array.from({ length: Math.round(p * 6) }).map((_, i) => <circle key={i} cx={-50 + (i % 3) * 50} cy={110 - Math.floor(i / 3) * 30} r={16} fill="#F5B301" stroke={ink} strokeWidth={3} />)}
    </g></g>); },

  // THUẾ: tờ đô bị cắt 1 miếng to (kéo)
  tax: ({ W, H, p, pal, cy }) => { const ink = pal.ink; const cx = W * 0.46; const cut = ease(clamp(p * 1.3)); return (<g>
    <g transform={`translate(${cx} ${cy})`} stroke={ink} strokeWidth={6}><rect x={-180} y={-110} width={360} height={220} rx={14} fill="#2FA84F" /><circle r={54} fill="#37c06a" stroke={ink} strokeWidth={5} /><text y={22} textAnchor="middle" fontFamily="Poppins,sans-serif" fontWeight={900} fontSize={64} fill="#fff">$</text>
      {/* miếng bị cắt bay ra */}
      <g transform={`translate(${lerp(0, 240, cut)} ${lerp(0, -60, cut)}) rotate(${cut * 20})`} opacity={clamp(p * 2)}><path d="M60 -110 L180 -110 L180 110 L60 110 Z" fill="#E23744" stroke={ink} strokeWidth={5} /><text x={120} y={12} textAnchor="middle" fontFamily="Poppins,sans-serif" fontWeight={900} fontSize={40} fill="#fff">TAX</text></g>
    </g></g>); },

  // CỖ MÁY LỢI NHUẬN: người vào -> máy -> tiền ra cho ông trùm
  profitmachine: ({ W, H, p, t, pal, cy }) => { const ink = pal.ink; const mx = W * 0.5; const flow = (t * 0.6) % 1; return (<g>
    {/* người vào trái */}
    {[0, 1].map((i) => <g key={i} transform={`translate(${W * 0.14 + i * 60} ${cy})`} stroke={ink} strokeWidth={5} opacity={clamp(p * 2)}><circle cy={-30} r={20} fill={pal.sw?.[3] || "#F1B784"} /><path d="M-18 40 Q0 0 18 40 Z" fill="#39454F" /></g>)}
    {/* máy */}
    <g transform={`translate(${mx} ${cy})`} stroke={ink} strokeWidth={7}><rect x={-120} y={-100} width={240} height={200} rx={16} fill="#5a6b72" /><rect x={-80} y={-60} width={160} height={120} rx={8} fill="#2b3a44" /><circle cx={0} cy={0} r={40} fill="none" stroke="#F5B301" strokeWidth={8} transform={`rotate(${t * 120})`} strokeDasharray="30 20" /><rect x={-30} y={-130} width={60} height={34} fill="#9db9d8" /></g>
    {/* tiền ra phải -> ông trùm */}
    {[0, 1, 2].map((i) => { const f = (flow + i * 0.33) % 1; return <g key={i} transform={`translate(${lerp(mx + 120, W * 0.86, f)} ${cy - 20})`} opacity={clamp(p * 2)}>{coin(0, 0, 20, ink)}</g>; })}
    <g transform={`translate(${W * 0.9} ${cy})`} stroke={ink} strokeWidth={5} opacity={clamp(p * 2)}><circle cy={-40} r={30} fill="#F5B301" /><path d="M-30 50 Q0 -6 30 50 Z" fill="#1D63C7" /><path d="M-30 -46 Q0 -60 30 -46" fill="none" strokeWidth={4} /></g>
  </g>); },
};

export const ConceptIllus: React.FC<{ name: string; p: number; caption?: string }> = ({ name, p, caption }) => {
  const { width: W, height: H } = useVideoConfig();
  const t = useCurrentFrame() / 30;
  const pal = PALETTES.broke[0];
  const fn = CONCEPTS[name] || CONCEPTS.subscriptions;
  const cy = H * (W > H ? 0.42 : 0.4);
  const rv = clamp(p);
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg,${pal.wall[0]},${pal.wall[1]})` }}>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width: W, height: H }}>
        {fn({ W, H, p: rv, t, pal, cy })}
      </svg>
      {caption && <div style={{ position: "absolute", left: "50%", top: H * (W > H ? 0.74 : 0.66), transform: "translateX(-50%)", opacity: clamp((rv - 0.2) * 3), fontFamily: "Poppins, sans-serif", fontWeight: 900, fontSize: W > H ? 66 : 80, color: "#fff", background: "#0b1220f2", padding: "10px 40px", borderRadius: 18, border: `3px solid ${pal.accent}`, whiteSpace: "nowrap", boxShadow: "0 14px 40px #0006" }}>{caption}</div>}
    </AbsoluteFill>);
};

export const ConceptDemo: React.FC<{ name?: string; caption?: string }> = ({ name = "subscriptions", caption }) => {
  const f = useCurrentFrame();
  return <ConceptIllus name={name} p={clamp(f / 45)} caption={caption} />;
};
