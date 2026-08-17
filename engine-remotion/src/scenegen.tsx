import React from "react";
// PROCEDURAL SET-DRESSING ENGINE — vẽ PROP 1 lần, sinh cảnh vô hạn bằng cấu hình (seed).
// Không vẽ lại SVG mỗi cảnh => tiết kiệm token. Deterministic (seed) => cache tốt, hiệu năng cao.

// ---- seeded RNG (LCG) — cùng seed = cùng cảnh ----
export function rng(seed: number) {
  let s = (seed >>> 0) || 1;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}
const pick = <T,>(r: () => number, a: T[]): T => a[Math.floor(r() * a.length) % a.length];
const NOFLIP = new Set(["store", "coin", "streetlight", "cart", "hmonitor", "counter", "whiteboard", "cert"]); // có chữ/định hướng -> ko lật
const jit = (r: () => number, m: number) => (r() * 2 - 1) * m;

// ---- PALETTE: đổi màu = biến thể vô hạn, 0 vẽ lại ----
export type Pal = { wall: [string, string]; floor: string; ink: string; accent: string; sky: [string, string]; sw: string[] };
export const PALETTES: Record<string, Pal[]> = {
  broke: [
    { wall: ["#e9f0f8", "#d5e3f1"], floor: "#d8c39d", ink: "#25313f", accent: "#3E7BFA", sky: ["#bfe0ff", "#eaf6ff"], sw: ["#e23744", "#3E7BFA", "#F5B301", "#2FA84F", "#7C5CFF"] },
    { wall: ["#f7ecdb", "#eddcc6"], floor: "#c9a87d", ink: "#3a2b22", accent: "#F59E0B", sky: ["#ffd9a8", "#ffeccb"], sw: ["#e07a52", "#3E7BFA", "#F5B301", "#4e9a4e", "#c0504d"] },
    { wall: ["#1a2b47", "#0f1c33"], floor: "#101d33", ink: "#0a1220", accent: "#22D3EE", sky: ["#12233f", "#0a1526"], sw: ["#ef4444", "#38bdf8", "#f5b301", "#34d399", "#a78bfa"] },
  ],
  inside: [
    { wall: ["#e9f8f5", "#d6efeb"], floor: "#cfe4e0", ink: "#2a4a52", accent: "#3FB0A0", sky: ["#bfe6ff", "#eaf9ff"], sw: ["#e23744", "#3FB0A0", "#F5B301", "#3E7BFA", "#7C5CFF"] },
    { wall: ["#f2e9f2", "#e6d8e6", ], floor: "#c9b3c4", ink: "#3a2a3a", accent: "#EC4899", sky: ["#ffd9ef", "#ffeaf6"], sw: ["#ec4899", "#3FB0A0", "#f5b301", "#7C5CFF", "#e23744"] },
  ],
  huh: [
    { wall: ["#eef1fb", "#e1e7f6"], floor: "#d6d8e6", ink: "#2c3550", accent: "#6366F1", sky: ["#c9d6ff", "#eef2ff"], sw: ["#e23744", "#3E7BFA", "#F5B301", "#2FA84F", "#7C5CFF"] },
    { wall: ["#eafaf1", "#d7f0e0"], floor: "#c7d8cc", ink: "#26402f", accent: "#10B981", sky: ["#bff0d6", "#e8fbef"], sw: ["#10b981", "#3E7BFA", "#f5b301", "#e23744", "#7C5CFF"] },
  ],
  ranked: [
    { wall: ["#eaf0f8", "#d7e2f0"], floor: "#c9bd9e", ink: "#243447", accent: "#F5B301", sky: ["#9cc3ef", "#e2eefb"], sw: ["#e23744", "#3E7BFA", "#F5B301", "#2FA84F", "#7C5CFF"] },
    { wall: ["#122038", "#0c1728"], floor: "#0e1a2e", ink: "#0a1220", accent: "#F5B301", sky: ["#0c1730", "#141f3a"], sw: ["#ef4444", "#38bdf8", "#f5b301", "#34d399", "#a78bfa"] },
  ],
};

// ---- PROP LIBRARY: mỗi prop vẽ 1 lần, tham số (x,y anchor, s scale, flip, pal, c màu, v biến thể) ----
type PP = { x: number; y: number; s?: number; flip?: boolean; pal: Pal; c?: string; v?: number; time?: number };
const G: React.FC<PP & { children: any }> = ({ x, y, s = 1, flip, children }) => (
  <g transform={`translate(${x} ${y}) scale(${(flip ? -s : s)} ${s})`}>{children}</g>);

export const PROPS: Record<string, React.FC<PP>> = {
  // — floor props (anchor = đáy giữa) —
  desk: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}>
    <rect x={-160} y={-70} width={320} height={22} rx={6} fill="#a9764e" /><rect x={-150} y={-48} width={22} height={48} fill="#7a4f30" /><rect x={128} y={-48} width={22} height={48} fill="#7a4f30" />
    <rect x={-90} y={-150} width={150} height={92} rx={8} fill="#1e2a38" /><rect x={-80} y={-140} width={130} height={72} rx={3} fill="#dff1ff" />
    <polyline points="-64,-84 -30,-116 4,-100 46,-132" fill="none" stroke={p.c || "#e23744"} strokeWidth={5} /><rect x={80} y={-92} width={30} height={34} rx={4} fill={p.pal.sw[0]} /></g></G>,
  sofa: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={5}>
    <rect x={-160} y={-70} width={320} height={70} rx={22} fill={p.c || "#e07a52"} /><rect x={-166} y={-130} width={54} height={130} rx={22} fill={p.c || "#e07a52"} /><rect x={112} y={-130} width={54} height={130} rx={22} fill={p.c || "#e07a52"} />
    <rect x={-110} y={-120} width={220} height={64} rx={16} fill={p.c || "#e07a52"} /><rect x={-96} y={-66} width={88} height={54} rx={12} fill="#ffffff30" /><rect x={8} y={-66} width={88} height={54} rx={12} fill="#ffffff30" /></g></G>,
  tv: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={6}><rect x={-150} y={-180} width={300} height={175} rx={10} fill="#1b2430" /><rect x={-138} y={-168} width={276} height={151} rx={4} fill={p.pal.sky[0]} /><polyline points="-110,-40 -40,-100 10,-70 100,-140" fill="none" stroke="#fff" strokeWidth={6} /><rect x={-40} y={0} width={80} height={16} rx={4} fill="#7a5a3a" /></g></G>,
  shelf: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-100} y={-200} width={200} height={200} fill={(p.v || 0) % 2 ? "#e7ddc8" : "#22303e"} />{[0, 1, 2].map((rw) => <g key={rw}><rect x={-100} y={-180 + rw * 66} width={200} height={12} fill="#c9b79a" />{[0, 1, 2, 3].map((k) => <rect key={k} x={-88 + k * 46} y={-168 + rw * 66} width={34} height={44} rx={4} fill={p.pal.sw[(k + rw) % 5]} />)}</g>)}</g></G>,
  cabinet: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-70} y={-160} width={140} height={160} rx={6} fill={p.c || "#8895a3"} />{[0, 1, 2].map((i) => <g key={i}><rect x={-62} y={-150 + i * 52} width={124} height={44} rx={4} fill="#00000010" /><rect x={-14} y={-134 + i * 52} width={28} height={8} rx={3} fill={p.pal.ink} /></g>)}</g></G>,
  plant: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><path d="M-26 0 L26 0 L18 74 L-18 74 Z" fill="#c96f3a" />{[[-16, -40, -18], [16, -40, 18], [0, -70, 0]].map(([a, b, r], i) => <ellipse key={i} cx={a * 0.6} cy={b} rx={24} ry={40} fill={i === 2 ? "#4e9a4e" : "#5cb85c"} transform={`rotate(${r})`} />)}</g></G>,
  cooler: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-34} y={-150} width={68} height={150} rx={8} fill="#eef4f7" /><rect x={-26} y={-176} width={52} height={40} rx={10} fill={p.pal.accent} opacity={0.5} /><rect x={-20} y={-90} width={40} height={10} fill={p.pal.accent} /></g></G>,
  vault: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={6}><rect x={-90} y={-180} width={180} height={180} rx={12} fill="#7f8c9c" /><circle cx={0} cy={-92} r={54} fill="#93a0b0" /><circle cx={0} cy={-92} r={26} fill="#aab6c4" />{[0, 45, 90, 135].map((a) => <rect key={a} x={-3} y={-150} width={6} height={20} fill={p.pal.ink} transform={`rotate(${a} 0 -92)`} />)}</g></G>,
  bed: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-150} y={-70} width={300} height={70} rx={10} fill="#dfeeec" /><rect x={-150} y={-110} width={90} height={44} rx={12} fill="#fff" /><rect x={-158} y={-96} width={14} height={96} fill="#b8c4cc" /><rect x={144} y={-96} width={14} height={96} fill="#b8c4cc" /></g></G>,
  car: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={5}><rect x={-115} y={-60} width={230} height={60} rx={16} fill={p.c || "#ffcf33"} /><path d="M-85 -60 Q-55 -104 15 -104 L75 -104 Q95 -80 95 -60 Z" fill={p.c || "#ffcf33"} /><rect x={-55} y={-98} width={55} height={34} fill="#bfe3ff" /><rect x={13} y={-98} width={58} height={34} fill="#bfe3ff" /><circle cx={-60} cy={0} r={26} fill="#222" /><circle cx={65} cy={0} r={26} fill="#222" /></g></G>,

  // — wall props (anchor = tâm) —
  window: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={5}><rect x={-190} y={-140} width={380} height={280} rx={10} fill="#f4f7fb" /><clipPath id={`w${Math.round(p.x)}`}><rect x={-176} y={-126} width={352} height={252} /></clipPath><g clipPath={`url(#w${Math.round(p.x)})`}><rect x={-176} y={-126} width={352} height={252} fill={p.pal.sky[0]} /><circle cx={110} cy={-70} r={30} fill="#ffe08a" />{[0, 1, 2, 3].map((i) => <rect key={i} x={-150 + i * 90} y={40 - (i % 3) * 40} width={60} height={120} fill="#9db9d8" opacity={0.8} />)}</g><rect x={-4} y={-126} width={8} height={252} fill="#f4f7fb" /><rect x={-176} y={-4} width={352} height={8} fill="#f4f7fb" /></g></G>,
  art: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-75} y={-58} width={150} height={116} rx={6} fill="#fff" /><rect x={-64} y={-47} width={128} height={94} fill={p.pal.sky[0]} /><path d="M-64 47 L-18 -6 L14 24 L64 -30 L64 47 Z" fill="#79b36b" /><circle cx={40} cy={-24} r={12} fill="#ffd36b" /></g></G>,
  clock: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={6}><circle r={42} fill="#fff" />{Array.from({ length: 12 }).map((_, i) => <rect key={i} x={-2} y={-38} width={4} height={8} fill={p.pal.ink} transform={`rotate(${i * 30})`} />)}<line x1={0} y1={0} x2={0} y2={-24} strokeWidth={4} transform={`rotate(${((p.time || 0) * 6) % 360})`} /><line x1={0} y1={0} x2={16} y2={0} strokeWidth={4} /><circle r={4} fill={p.pal.ink} /></g></G>,
  whiteboard: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={5}><rect x={-120} y={-84} width={240} height={168} rx={6} fill="#fff" /><polyline points="-90,50 -30,-10 20,20 90,-50" fill="none" stroke={p.pal.sw[0]} strokeWidth={6} /><rect x={-90} y={-64} width={90} height={12} rx={4} fill={p.pal.accent} opacity={0.6} /></g></G>,
  cert: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-50} y={-64} width={100} height={128} rx={4} fill="#fff" /><rect x={-38} y={-52} width={76} height={12} fill={p.pal.accent} opacity={0.5} />{[0, 1, 2, 3].map((i) => <rect key={i} x={-38} y={-28 + i * 16} width={76} height={6} fill="#00000018" />)}<circle cx={0} cy={44} r={12} fill={p.pal.sw[2]} /></g></G>,

  // — ceiling —
  lamp: (p) => <G {...p}><line x1={0} y1={0} x2={0} y2={58} stroke="#8a97a6" strokeWidth={6} /><path d="M-46 58 Q0 34 46 58 L32 92 Q0 78 -32 92 Z" fill="#3a4658" /><ellipse cx={0} cy={92} rx={34} ry={9} fill="#ffe9a8" /></G>,

  // — HERO prop (khớp nội dung) —
  card: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-70} y={-46} width={140} height={92} rx={10} fill={p.c || p.pal.accent} /><rect x={-58} y={-24} width={40} height={30} rx={4} fill="#ffd76b" /><rect x={-58} y={20} width={100} height={8} fill="#ffffff88" /></g></G>,
  box: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-56} y={-70} width={112} height={70} fill="#c8a06a" /><path d="M-56 -70 L0 -92 L56 -70 Z" fill="#dbb27f" /><rect x={-10} y={-70} width={20} height={70} fill="#00000015" /></g></G>,
  coin: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><circle r={44} fill={p.c || "#F5B301"} /><circle r={32} fill="none" stroke={p.pal.ink} strokeWidth={3} /><text y={16} textAnchor="middle" fontFamily="Poppins,sans-serif" fontWeight={900} fontSize={44} fill={p.pal.ink}>$</text></g></G>,
  flask: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><path d="M-14 -70 L14 -70 L30 -30 Q44 30 0 30 Q-44 30 -30 -30 Z" fill="#dff" /><path d="M-22 -6 Q0 16 22 -6 Q30 16 0 20 Q-30 16 -22 -6 Z" fill={p.c || "#2FA84F"} /></g></G>,
  // — HERO minh hoạ theo LỜI (điện thoại/app/mua/web/free/tăng/ý tưởng/khoá) —
  phone: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-38} y={-72} width={76} height={144} rx={14} fill="#1e2a38" /><rect x={-30} y={-56} width={60} height={104} rx={4} fill={p.pal.sky[0]} /><circle cx={0} cy={60} r={6} fill="#33404d" /><rect x={-18} y={-40} width={36} height={12} rx={3} fill="#33404d" /></g></G>,
  app: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-40} y={-74} width={80} height={148} rx={14} fill="#1e2a38" /><rect x={-32} y={-58} width={64} height={116} rx={4} fill="#f2f6fb" />{[0, 1, 2].map((r) => [0, 1, 2].map((c) => <rect key={`${r}${c}`} x={-26 + c * 20} y={-50 + r * 24} width={14} height={14} rx={4} fill={p.pal.sw[(r + c) % 5]} />))}</g></G>,
  bag: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><path d="M-42 -30 L42 -30 L34 60 L-34 60 Z" fill={p.c || p.pal.accent} /><path d="M-22 -30 Q-22 -60 0 -60 Q22 -60 22 -30" fill="none" stroke={p.pal.ink} strokeWidth={5} /><circle cx={0} cy={6} r={12} fill="#ffffff55" /></g></G>,
  globe: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4} fill="none"><circle r={54} fill="#5aa9e6" /><ellipse rx={54} ry={22} /><ellipse rx={26} ry={54} /><line x1={-54} y1={0} x2={54} y2={0} /><path d="M-40 -24 Q0 -10 40 -24 M-40 24 Q0 10 40 24" /></g></G>,
  gift: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-46} y={-30} width={92} height={80} rx={6} fill={p.c || "#e2483a"} /><rect x={-46} y={-30} width={92} height={22} fill="#ffffff40" /><rect x={-10} y={-30} width={20} height={80} fill="#ffffff70" /><path d="M0 -30 Q-30 -60 -40 -40 Q-20 -30 0 -30 Q30 -60 40 -40 Q20 -30 0 -30" fill="#ffd76b" /></g></G>,
  chartup: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-56} y={-56} width={112} height={100} rx={8} fill="#fff" />{[0, 1, 2, 3].map((i) => <rect key={i} x={-44 + i * 26} y={20 - i * 14} width={16} height={20 + i * 14} fill={p.pal.sw[i % 5]} />)}<path d="M-46 18 L-6 -8 L14 2 L48 -34" fill="none" stroke="#2FA84F" strokeWidth={5} /><path d="M40 -34 L48 -34 L48 -26" fill="none" stroke="#2FA84F" strokeWidth={5} /></g></G>,
  bulb: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><circle cy={-16} r={40} fill={p.c || "#ffd76b"} /><rect x={-16} y={20} width={32} height={16} rx={3} fill="#9aa" /><rect x={-12} y={36} width={24} height={12} rx={3} fill="#7a8590" /><path d="M-8 20 Q0 0 8 20" fill="none" stroke={p.pal.ink} strokeWidth={3} /></g></G>,
  lock: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-40} y={-14} width={80} height={64} rx={10} fill={p.c || "#8895a3"} /><path d="M-24 -14 L-24 -34 Q-24 -58 0 -58 Q24 -58 24 -34 L24 -14" fill="none" stroke={p.pal.ink} strokeWidth={7} /><circle cy={14} r={9} fill={p.pal.ink} /><rect x={-4} y={16} width={8} height={18} fill={p.pal.ink} /></g></G>,
  clockh: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={5}><circle r={48} fill="#fff" /><line x1={0} y1={0} x2={0} y2={-30} strokeWidth={5} transform={`rotate(${((p.time || 0) * 30) % 360})`} /><line x1={0} y1={0} x2={22} y2={0} strokeWidth={5} /><circle r={5} fill={p.pal.ink} /></g></G>,
  house: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><path d="M-56 -8 L0 -60 L56 -8 Z" fill={p.pal.sw[0]} /><rect x={-44} y={-8} width={88} height={58} fill={p.c || "#e8c477"} /><rect x={-16} y={16} width={32} height={34} fill="#7a4f30" /><rect x={20} y={2} width={20} height={20} fill={p.pal.sky[0]} /><rect x={-40} y={2} width={20} height={20} fill={p.pal.sky[0]} /></g></G>,
  bank2: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-56} y={-6} width={112} height={56} fill={p.c || "#3E7BFA"} /><path d="M-66 -6 L0 -50 L66 -6 Z" fill={p.pal.sw[2] || "#F5B301"} />{[-38, -13, 12, 37].map((x, i) => <rect key={i} x={x} y={-2} width={12} height={52} fill="#eef4ff" stroke={p.pal.ink} strokeWidth={2} />)}<rect x={-64} y={50} width={128} height={12} rx={3} fill={p.pal.ink} /><circle cx={0} cy={22} r={12} fill="#eef4ff" /><text x={0} y={28} textAnchor="middle" fontFamily="Poppins,sans-serif" fontWeight={900} fontSize={16} fill={p.pal.ink}>$</text></g></G>,

  // — outdoor / thêm —
  building: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={3}><rect x={-90} y={-360} width={180} height={360} fill={p.c || "#8fb3da"} />{(p.v || 0) % 3 === 0 && <rect x={-8} y={-400} width={16} height={40} fill={p.pal.ink} />}{Array.from({ length: 6 }).map((_, r) => Array.from({ length: 3 }).map((_, c) => <rect key={`${r}${c}`} x={-70 + c * 52} y={-340 + r * 54} width={38} height={34} fill={(r + c) % 3 === (p.v || 0) % 3 ? "#f5d76e" : "#cfe0f2"} />))}</g></G>,
  store: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-120} y={-240} width={240} height={240} fill={p.c || "#d98b6a"} /><rect x={-128} y={-250} width={256} height={40} fill={p.pal.sw[0]} />{Array.from({ length: 7 }).map((_, k) => <rect key={k} x={-128 + k * 37} y={-250} width={18} height={40} fill="#fff" opacity={0.35} />)}<rect x={-60} y={-190} width={120} height={40} rx={4} fill="#1e2a38" /><text x={0} y={-160} textAnchor="middle" fill="#ffd76b" fontFamily="Poppins,sans-serif" fontWeight={800} fontSize={28}>SHOP</text><rect x={-40} y={-90} width={80} height={90} rx={4} fill="#bfe3ff" /></g></G>,
  streetlight: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-4} y={-300} width={8} height={300} fill="#5a6b72" /><path d="M0 -300 q0 -30 34 -30" fill="none" stroke="#5a6b72" strokeWidth={8} /><ellipse cx={34} cy={-326} rx={14} ry={10} fill="#ffe08a" /></g></G>,
  tree: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-14} y={-120} width={28} height={120} fill="#7a5230" /><circle cx={0} cy={-150} r={58} fill="#4e9a4e" /><circle cx={-42} cy={-118} r={40} fill="#5cb85c" /><circle cx={42} cy={-118} r={40} fill="#5cb85c" /><circle cx={0} cy={-190} r={38} fill="#66c266" /></g></G>,
  bench: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={3}><rect x={-90} y={-30} width={180} height={16} rx={4} fill="#8a5a3a" /><rect x={-90} y={-58} width={180} height={14} rx={4} fill="#9a6a44" /><rect x={-80} y={-14} width={12} height={30} fill="#5a6b72" /><rect x={68} y={-14} width={12} height={30} fill="#5a6b72" /></g></G>,
  cart: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={5}><path d="M-70 -70 L-50 -70 L-26 0 L80 0" fill="none" /><path d="M-46 -50 L80 -50 L64 -6 L-30 -6 Z" fill="#c9d2da" />{[0, 1, 2].map((i) => <line key={i} x1={-30 + i * 30} y1={-50} x2={-36 + i * 30} y2={-6} strokeWidth={3} />)}<circle cx={-15} cy={16} r={16} fill="#333" /><circle cx={55} cy={16} r={16} fill="#333" /></g></G>,
  hmonitor: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={5}><rect x={-90} y={-150} width={180} height={130} rx={10} fill="#12303a" /><rect x={-78} y={-138} width={156} height={90} rx={4} fill="#031318" /><polyline points="-66,-92 -30,-92 -12,-124 6,-56 24,-92 66,-92" fill="none" stroke="#39ff88" strokeWidth={4} /><rect x={-66} y={-40} width={34} height={16} rx={3} fill={p.pal.sw[0]} /></g></G>,
  poster: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={4}><rect x={-58} y={-80} width={116} height={160} rx={4} fill={p.c || p.pal.accent} /><circle cx={0} cy={-30} r={30} fill="#ffffff40" /><rect x={-40} y={30} width={80} height={12} rx={4} fill="#ffffff70" /><rect x={-40} y={52} width={54} height={10} rx={4} fill="#ffffff50" /></g></G>,
  counter: (p) => <G {...p}><g stroke={p.pal.ink} strokeWidth={5}><rect x={-140} y={-30} width={280} height={30} fill={p.c || "#8a5a3a"} /><rect x={-140} y={-46} width={280} height={18} rx={4} fill="#a9764e" />{Array.from({ length: 4 }).map((_, i) => <rect key={i} x={-110 + i * 70} y={-110} width={5} height={64} fill="#9fb4cc" />)}<rect x={-120} y={-110} width={240} height={5} fill="#9fb4cc" /></g></G>,
};

// ---- ARCHETYPE: mỗi loại cảnh có NHIỀU biến thể layout (chọn theo seed) => đa dạng template ----
type Slot = { at: number; band: "floor" | "wall" | "ceil" | "far"; pick: string[]; s?: number; p?: number };
type Arch = { outdoor?: boolean; hero?: { at: number; band: "floor" | "wall" }; layouts: Slot[][] };
const W_ = (at: number, pick: string[], s = 1, p?: number): Slot => ({ at, band: "wall", pick, s, p });
const F_ = (at: number, pick: string[], s = 1, p?: number): Slot => ({ at, band: "floor", pick, s, p });
const C_ = (at: number, pick: string[], s = 1, p?: number): Slot => ({ at, band: "ceil", pick, s, p });
const D_ = (at: number, pick: string[], s = 1, p?: number): Slot => ({ at, band: "far", pick, s, p });
const LAMP2 = [C_(0.5, ["lamp"]), C_(0.26, ["lamp"], 0.85, 0.4)];

export const ARCH: Record<string, Arch> = {
  office: { hero: { at: 0.5, band: "floor" }, layouts: [
    [F_(0.11, ["desk"]), F_(0.9, ["plant", "cooler"]), F_(0.7, ["cabinet"], 0.85, 0.5), W_(0.76, ["window"], 1.15), W_(0.13, ["clock", "cert"]), W_(0.3, ["art", "cert"], 0.95, 0.8), W_(0.46, ["cert", "art"], 0.85, 0.5), ...LAMP2],
    [F_(0.14, ["cabinet"]), F_(0.32, ["desk"], 1, 0.9), F_(0.88, ["plant"]), W_(0.2, ["whiteboard"], 1.1), W_(0.55, ["art", "clock"], 0.9, 0.7), W_(0.8, ["cert", "art"], 0.9, 0.7), C_(0.5, ["lamp"])],
    [F_(0.1, ["cooler"]), F_(0.3, ["desk"]), F_(0.86, ["cabinet", "plant"]), W_(0.7, ["window"], 1.2), W_(0.15, ["art"]), W_(0.4, ["cert", "clock"], 0.9, 0.6), ...LAMP2] ] },
  home: { hero: { at: 0.5, band: "floor" }, layouts: [
    [F_(0.13, ["sofa"]), F_(0.86, ["tv", "shelf"]), F_(0.7, ["plant"], 0.85, 0.5), W_(0.74, ["window"], 1.05), W_(0.16, ["art", "clock"]), W_(0.34, ["art", "cert"], 0.9, 0.7), C_(0.5, ["lamp"])],
    [F_(0.16, ["tv"]), F_(0.84, ["sofa"], 1, 1), F_(0.5, ["plant"], 0.8, 0.4), W_(0.2, ["window"], 1.05), W_(0.5, ["art"], 0.9, 0.7), W_(0.8, ["clock", "art"], 0.9, 0.7), C_(0.5, ["lamp"])],
    [F_(0.12, ["shelf"]), F_(0.5, ["sofa"]), F_(0.9, ["plant", "tv"]), W_(0.76, ["window"]), W_(0.3, ["art", "cert"], 0.9, 0.8), ...LAMP2] ] },
  bank: { hero: { at: 0.5, band: "floor" }, layouts: [
    [F_(0.14, ["vault"]), F_(0.86, ["counter", "cabinet"]), W_(0.3, ["clock", "cert"]), W_(0.7, ["art"], 1, 0.8), ...LAMP2],
    [F_(0.16, ["counter"]), F_(0.85, ["vault"], 0.9), F_(0.5, ["plant"], 0.8, 0.4), W_(0.5, ["cert"], 1), W_(0.15, ["clock"]), W_(0.82, ["art"], 0.9, 0.7), C_(0.5, ["lamp"])] ] },
  lab: { hero: { at: 0.5, band: "floor" }, layouts: [
    [F_(0.14, ["cabinet"]), F_(0.86, ["flask", "cooler"]), F_(0.5, ["flask"], 0.8, 0.5), W_(0.72, ["whiteboard"], 1.05), W_(0.22, ["cert", "clock"]), W_(0.5, ["poster"], 0.9, 0.5), ...LAMP2],
    [F_(0.12, ["cooler"]), F_(0.4, ["cabinet"]), F_(0.88, ["flask"]), W_(0.7, ["window"]), W_(0.2, ["whiteboard"], 0.9), W_(0.45, ["cert"], 0.85, 0.6), C_(0.5, ["lamp"])] ] },
  store: { hero: { at: 0.5, band: "floor" }, layouts: [
    [F_(0.12, ["shelf"]), F_(0.5, ["shelf"], 1, 0.7), F_(0.88, ["shelf"]), F_(0.72, ["cart"], 0.9, 0.6), W_(0.5, ["poster", "art"], 0.9, 0.7), C_(0.3, ["lamp"]), C_(0.7, ["lamp"])],
    [F_(0.14, ["shelf"]), F_(0.86, ["cart"]), F_(0.5, ["cooler"], 0.9, 0.5), W_(0.3, ["poster"]), W_(0.7, ["poster"], 1, 0.7), ...LAMP2] ] },
  gym: { hero: { at: 0.5, band: "floor" }, layouts: [
    [F_(0.13, ["bench"]), F_(0.86, ["cooler"]), F_(0.5, ["bench"], 0.9, 0.5), W_(0.72, ["window", "poster"], 1.05), W_(0.2, ["clock"]), W_(0.5, ["poster"], 0.95, 0.7), ...LAMP2] ] },
  hospital: { hero: { at: 0.5, band: "floor" }, layouts: [
    [F_(0.14, ["bed"]), F_(0.86, ["hmonitor"]), F_(0.5, ["cooler"], 0.85, 0.5), W_(0.72, ["window"], 1.05), W_(0.2, ["cert", "clock"]), W_(0.5, ["poster"], 0.9, 0.5), ...LAMP2],
    [F_(0.16, ["hmonitor"]), F_(0.84, ["bed"]), W_(0.5, ["cert"]), W_(0.16, ["clock"]), W_(0.8, ["window"], 0.95), C_(0.5, ["lamp"])] ] },
  street: { outdoor: true, hero: { at: 0.5, band: "floor" }, layouts: [
    [D_(0.16, ["building"], 1), D_(0.44, ["building"], 0.85), D_(0.82, ["store"], 1), F_(0.12, ["tree"]), F_(0.88, ["streetlight"]), F_(0.66, ["car"], 1, 0.7)],
    [D_(0.2, ["store"], 1), D_(0.6, ["building"], 1), D_(0.86, ["building"], 0.8), F_(0.14, ["streetlight"]), F_(0.86, ["tree"]), F_(0.5, ["car"], 0.95, 0.6), F_(0.72, ["bench"], 0.9, 0.5)] ] },
  city: { outdoor: true, hero: { at: 0.5, band: "floor" }, layouts: [
    [D_(0.1, ["building"], 1.1), D_(0.3, ["building"], 0.9), D_(0.55, ["building"], 1.15), D_(0.78, ["building"], 0.85), D_(0.94, ["building"], 1), F_(0.88, ["streetlight"]), F_(0.14, ["tree"], 0.9, 0.6)] ] },
  park: { outdoor: true, hero: { at: 0.5, band: "floor" }, layouts: [
    [D_(0.7, ["building"], 0.7, 0.5), F_(0.12, ["tree"], 1.1), F_(0.88, ["tree"], 0.95), F_(0.5, ["bench"]), F_(0.7, ["streetlight"], 0.9, 0.5)],
    [F_(0.14, ["tree"]), F_(0.86, ["tree"], 1.05), F_(0.5, ["bench"], 1, 0.7), F_(0.3, ["streetlight"], 0.85, 0.5)] ] },
  cafe: { hero: { at: 0.5, band: "floor" }, layouts: [
    [F_(0.13, ["counter"]), F_(0.86, ["plant"]), F_(0.5, ["bench"], 0.85, 0.5), W_(0.72, ["window"], 1.05), W_(0.2, ["art", "poster"]), W_(0.5, ["cert", "art"], 0.9, 0.7), ...LAMP2] ] },
  studio: { hero: { at: 0.5, band: "floor" }, layouts: [
    [F_(0.12, ["cabinet"]), F_(0.88, ["plant"]), W_(0.5, ["poster"], 1.2), W_(0.2, ["poster"], 0.9, 0.7), W_(0.8, ["poster"], 0.9, 0.7), ...LAMP2] ] },
};

// nội dung -> hero prop minh hoạ (cụm dài/đặc thù TRƯỚC; khớp lời để người xem dễ hình dung)
export const HERO_KW: [string[], string][] = [
  [["app store", "download", "install", "apps", "app"], "app"],
  [["phone", "mobile", "smartphone", "screen", "swipe", "device", "stream", "netflix", "video", "watch"], "phone"],
  [["free", "gift", "deal", "offer", "bonus", "discount", "coupon"], "gift"],
  [["buy", "shop", "purchase", "spend", "checkout", "cart", "grocery", "store"], "bag"],
  [["internet", "online", "web", "world", "global", "network", "cloud", "country"], "globe"],
  [["growth", "grow", "rise", "profit", "increase", "percent", "surge", "boom", "chart", "double", "triple"], "chartup"],
  [["idea", "truth", "secret", "trick", "reveal", "smart", "genius"], "bulb"],
  [["hidden", "lock", "private", "secure", "data", "password", "trap", "catch"], "lock"],
  [["hour", "minute", "clock", "wait", "time", "year", "daily"], "clockh"],
  [["card", "credit", "debit"], "card"],
  [["money", "cash", "dollar", "wage", "salary", "coin", "price", "cost", "fee", "pay", "rich", "expensive"], "coin"],
  [["box", "package", "product", "delivery", "amazon", "ship", "middlemen"], "box"],
  [["cell", "dna", "science", "milk", "liquid", "blood", "chem", "lab", "body"], "flask"],
];
export function heroFor(nar: string): string | null {
  const low = (nar || "").toLowerCase();
  for (const [kw, prop] of HERO_KW) if (kw.some((k) => low.includes(k))) return prop;
  return null;
}

// ---- SceneGen: dàn cảnh từ (archetype, seed) — KHÔNG vẽ SVG mới ----
export const SceneGen: React.FC<{ arch: string; seed: number; channel: string; hero?: string | null; width: number; height: number; floorPct: number; wide: boolean; time: number; paletteIndex?: number; heroReveal?: number }>
  = ({ arch, seed, channel, hero, width, height, floorPct, wide, time, paletteIndex, heroReveal = 1 }) => {
  const r = rng(seed);
  const pals = PALETTES[channel] || PALETTES.broke;
  const pal = pals[(paletteIndex ?? Math.floor(r() * pals.length)) % pals.length];
  const A = ARCH[arch] || ARCH.office;
  const W = width, H = height, fY = floorPct * H, S = W / 1920;
  const out = !!A.outdoor;
  const bandY = (b: string) => (b === "floor" || b === "far") ? fY : b === "ceil" ? 46 * S : fY * 0.42;
  const layout = pick(r, A.layouts);
  const ord: Record<string, number> = { far: 0, ceil: 1, wall: 2, floor: 3 };
  const sorted = [...layout].sort((a, b) => ord[a.band] - ord[b.band]);
  const items: any[] = [];
  // SẠCH & GỢI bối cảnh: indoor chỉ 1 vật sàn + 1 vật tường đặt LỆCH BIÊN; outdoor = skyline + vài cây/đèn.
  // Chừa khoảng thở cho nhân vật -> chủ thể nổi bật, ko rối.
  let nFloor = 0, nWall = 0;
  const maxFloor = out ? 2 : 1, maxWall = out ? 0 : 1;
  sorted.forEach((sl, i) => {
    const name = pick(r, sl.pick);
    if (sl.band === "ceil") return;                          // bỏ đèn trần (bớt rối)
    if (sl.band === "floor") { if (nFloor >= maxFloor) return; }
    else if (sl.band === "wall") { if (nWall >= maxWall) return; }
    // giữ far (skyline) cho outdoor
    const Comp = PROPS[name]; if (!Comp) return;
    let at = sl.at;
    if (sl.band === "floor" && !out) at = nFloor === 0 ? 0.12 : 0.88;   // dồn ra biên trái/phải
    if (sl.band === "wall" && !out) at = 0.83;                          // vật tường sang phải
    const x = at * W + jit(r, 10) * S;
    const y = bandY(sl.band) + (sl.band === "far" ? 0 : jit(r, 4)) * S;
    const s = (sl.s || 1) * S * (0.98 + r() * 0.08);
    const c = r() > 0.5 ? pal.sw[Math.floor(r() * pal.sw.length)] : undefined;
    const fl = r() > 0.7;
    items.push(<Comp key={i} x={x} y={y} s={s} flip={fl && !NOFLIP.has(name)} pal={pal} c={c} v={Math.floor(r() * 4)} time={time} />);
    if (sl.band === "floor") nFloor++; else if (sl.band === "wall") nWall++;
  });
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width, height }}>
      <defs>
        <linearGradient id={`wg${seed}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={out ? pal.sky[0] : pal.wall[0]} /><stop offset="1" stopColor={out ? pal.sky[1] : pal.wall[1]} /></linearGradient>
        {/* spotlight mềm trên tường sau chủ thể */}
        <radialGradient id={`ws${seed}`} cx="50%" cy="24%" r="62%"><stop offset="0" stopColor="#ffffff" stopOpacity="0.11" /><stop offset="1" stopColor="#ffffff" stopOpacity="0" /></radialGradient>
        {/* bóng 2 góc phòng -> chiều sâu */}
        <linearGradient id={`cl${seed}`} x1="0" y1="0" x2="1" y2="0"><stop offset="0" stopColor="#04070e" stopOpacity="0.30" /><stop offset="0.2" stopColor="#04070e" stopOpacity="0" /><stop offset="0.8" stopColor="#04070e" stopOpacity="0" /><stop offset="1" stopColor="#04070e" stopOpacity="0.30" /></linearGradient>
        {/* sàn: sâu dần về đáy */}
        <linearGradient id={`fd${seed}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#04070e" stopOpacity="0" /><stop offset="1" stopColor="#04070e" stopOpacity="0.42" /></linearGradient>
      </defs>
      <rect x={0} y={0} width={W} height={fY} fill={`url(#wg${seed})`} />
      {out ? (<>
        {/* NGOÀI TRỜI: mặt trời + mây + vỉa hè + đường (chất phố Mỹ) */}
        <circle cx={W * (0.16 + (seed % 5) * 0.14)} cy={fY * 0.2} r={46 * S} fill="#ffe08a" />
        <g transform={`translate(${W * 0.6} ${fY * 0.22})`}><ellipse rx={60 * S} ry={30 * S} fill="#fff" opacity={0.9} /><ellipse cx={54 * S} cy={8 * S} rx={44 * S} ry={24 * S} fill="#fff" opacity={0.9} /></g>
        {items}
        <rect x={0} y={fY} width={W} height={H - fY} fill="#8a96a2" /><rect x={0} y={fY} width={W} height={14 * S} fill="#b9c2cc" />
        <rect x={0} y={fY + (H - fY) * 0.42} width={W} height={(H - fY) * 0.58} fill="#3c434c" />
        {Array.from({ length: 9 }).map((_, i) => <rect key={i} x={i * (W / 8)} y={fY + (H - fY) * 0.68} width={W / 16} height={12 * S} fill="#ffd76b" />)}
      </>) : (<>
        <rect x={0} y={0} width={W} height={fY} fill={`url(#ws${seed})`} />
        <rect x={0} y={0} width={W} height={fY} fill={`url(#cl${seed})`} />
        <rect x={0} y={0} width={W} height={46 * S} fill="#00000012" />
        <rect x={0} y={fY - 30 * S} width={W} height={30 * S} fill="#00000010" /><rect x={0} y={fY - 34 * S} width={W} height={5 * S} fill={pal.accent} opacity={0.22} />
        <rect x={0} y={fY} width={W} height={H - fY} fill={pal.floor} />
        <rect x={0} y={fY} width={W} height={H - fY} fill={`url(#fd${seed})`} />
        <rect x={0} y={fY} width={W} height={6} fill="#0003" /><rect x={0} y={fY} width={W} height={3 * S} fill="#ffffff" opacity={0.06} />
        <ellipse cx={W * 0.5} cy={fY + (H - fY) * 0.5} rx={W * 0.32} ry={(H - fY) * 0.3} fill={pal.accent} opacity={0.13} />
        {items}
      </>)}
    </svg>);
};
