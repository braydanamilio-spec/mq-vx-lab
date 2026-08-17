import React from "react";
import { AbsoluteFill } from "remotion";

// Bộ CẢNH NỀN vẽ 2D (kể chuyện qua hình). Nhân vật đứng trên sàn (floorPct) trước cảnh.
// kind: office | home | street | bank | store | cafe | city | room | clean | park
export const SceneBG: React.FC<{ kind?: string; width: number; height: number; floorPct: number; wide: boolean; T: any; dark?: boolean; time: number }>
  = ({ kind = "room", width, height, floorPct, wide, T, dark, time }) => {
  const floorY = floorPct * height;
  const S = width / (wide ? 1920 : 1080); // scale theo khung
  const px = (v: number) => v * S;
  const sway = Math.sin(time * 0.6) * 4;

  const Floor = ({ col }: { col: string }) => (<>
    <div style={{ position: "absolute", left: 0, top: floorY, width, height: height - floorY, background: col }} />
    <div style={{ position: "absolute", left: 0, top: floorY, width, height: px(6), background: "#00000022" }} />
  </>);
  const Wall = (a: string, b: string) => <AbsoluteFill style={{ background: `linear-gradient(180deg,${a},${b})` }} />;
  const light = <div style={{ position: "absolute", left: "30%", top: -px(240), width: px(760), height: px(760), borderRadius: "50%", background: T.accent, opacity: 0.08, filter: "blur(40px)" }} />;
  const win = (l: number, t: number, w: number, h: number) => (
    <div style={{ position: "absolute", left: px(l), top: px(t), width: px(w), height: px(h), background: "linear-gradient(160deg,#bfe6ff,#8fc8f5)", border: `${px(12)}px solid #fff`, borderRadius: px(10), boxShadow: "0 10px 30px #0001", overflow: "hidden" }}>
      <div style={{ position: "absolute", left: "48%", top: 0, width: px(8), height: "100%", background: "#fff" }} />
      <div style={{ position: "absolute", left: 0, top: "48%", width: "100%", height: px(8), background: "#fff" }} />
      <div style={{ position: "absolute", right: px(14), top: px(10), fontSize: px(40) }}>☀️</div>
    </div>);
  const emo = (l: number, t: number, s: number, ch: string, extra?: any) => <div style={{ position: "absolute", left: px(l), top: px(t), fontSize: px(s), ...extra }}>{ch}</div>;
  const box = (l: number, t: number, w: number, h: number, col: string, r = 8, sh = true) => <div style={{ position: "absolute", left: px(l), top: px(t), width: px(w), height: px(h), background: col, borderRadius: px(r), boxShadow: sh ? "0 8px 22px #0002" : "none" }} />;
  // POLISH: trần + đèn (lấp khoảng trống trên) · cờ Mỹ (chất USA)
  const ceiling = (col: string) => (<>
    <div style={{ position: "absolute", left: 0, top: 0, width, height: px(44), background: col }} />
    <div style={{ position: "absolute", left: 0, top: px(44), width, height: px(5), background: "#00000018" }} />
    <div style={{ position: "absolute", left: "47%", top: px(44), width: px(4), height: px(46), background: "#8895a3" }} />
    <div style={{ position: "absolute", left: "44%", top: px(86), width: px(90), height: px(30), background: "#ffe08a", borderRadius: "0 0 60px 60px", boxShadow: `0 0 ${px(60)}px #ffe08a99` }} />
  </>);
  const flag = (l: number, t: number, s = 80) => <div style={{ position: "absolute", left: px(l), top: px(t), fontSize: px(s), transform: `rotate(${-6 + Math.sin(time * 1.2) * 3}deg)`, transformOrigin: "left" }}>🇺🇸</div>;

  if (kind === "office") {
    const W = wide ? 1920 : 1080, H = wide ? 1080 : 1920, fY = floorPct * H, ink = "#25313f";
    const wallA = dark ? "#1a2b47" : "#e9f0f8", wallB = dark ? "#0f1c33" : "#d5e3f1";
    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width, height }}>
        <defs>
          <linearGradient id="ofw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={wallA} /><stop offset="1" stopColor={wallB} /></linearGradient>
          <linearGradient id="ofsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={dark ? "#12233f" : "#bfe0ff"} /><stop offset="1" stopColor={dark ? "#0a1526" : "#eaf6ff"} /></linearGradient>
          <linearGradient id="ofdesk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#b07a4a" /><stop offset="1" stopColor="#8a5c34" /></linearGradient>
        </defs>
        <rect x="0" y="0" width={W} height={fY} fill="url(#ofw)" />
        {/* trần + đèn thả */}
        <rect x="0" y="0" width={W} height="46" fill={dark ? "#152441" : "#cfdcec"} />
        <rect x={W * 0.5 - 3} y="46" width="6" height="70" fill="#8a97a6" />
        <path d={`M ${W * 0.5 - 55} 116 Q ${W * 0.5} 96 ${W * 0.5 + 55} 116 L ${W * 0.5 + 40} 150 Q ${W * 0.5} 138 ${W * 0.5 - 40} 150 Z`} fill={dark ? "#2a3a55" : "#3a4658"} />
        <ellipse cx={W * 0.5} cy="150" rx="42" ry="10" fill="#ffe9a8" opacity="0.9" />
        {/* CỬA SỔ + skyline vẽ */}
        {(() => { const wx = wide ? 1230 : 560, wy = 150, ww = 470, wh = 320; return (<g>
          <rect x={wx - 14} y={wy - 14} width={ww + 28} height={wh + 28} rx="14" fill="#f4f7fb" stroke={ink} strokeWidth="5" />
          <clipPath id="ofwin"><rect x={wx} y={wy} width={ww} height={wh} rx="6" /></clipPath>
          <g clipPath="url(#ofwin)"><rect x={wx} y={wy} width={ww} height={wh} fill="url(#ofsky)" />
            <circle cx={wx + ww - 70} cy={wy + 70} r="34" fill={dark ? "#dfe8f5" : "#ffe08a"} />
            {[0, 1, 2, 3, 4].map((i) => <rect key={i} x={wx + 10 + i * 92} y={wy + wh - (120 + (i % 3) * 60)} width="70" height={120 + (i % 3) * 60} fill={dark ? "#1c3457" : "#9db9d8"} />)}
          </g>
          <rect x={wx + ww / 2 - 4} y={wy} width="8" height={wh} fill="#f4f7fb" /><rect x={wx} y={wy + wh / 2 - 4} width={ww} height="8" fill="#f4f7fb" />
        </g>); })()}
        {/* tranh treo */}
        <g><rect x={wide ? 150 : 70} y="170" width="150" height="120" rx="6" fill="#fff" stroke={ink} strokeWidth="5" /><rect x={wide ? 160 : 80} y="180" width="130" height="100" fill="#cdeafe" /><path d={`M ${wide ? 160 : 80} 280 L ${wide ? 210 : 130} 220 L ${wide ? 250 : 170} 260 L ${wide ? 290 : 210} 210 L ${wide ? 290 : 210} 280 Z`} fill="#79b36b" /><circle cx={wide ? 270 : 190} cy="205" r="12" fill="#ffd36b" /></g>
        {/* đồng hồ tường vẽ */}
        <g transform={`translate(${wide ? 470 : 300} 220)`}><circle r="42" fill="#fff" stroke={ink} strokeWidth="6" />{Array.from({ length: 12 }).map((_, i) => <rect key={i} x="-2" y="-38" width="4" height="8" fill={ink} transform={`rotate(${i * 30})`} />)}<line x1="0" y1="0" x2="0" y2="-24" stroke={ink} strokeWidth="4" transform={`rotate(${time * 6})`} /><line x1="0" y1="0" x2="16" y2="0" stroke={ink} strokeWidth="4" transform={`rotate(${time * 0.5})`} /><circle r="4" fill={ink} /></g>
        {/* sàn */}
        <rect x="0" y={fY} width={W} height={H - fY} fill={dark ? "#101d33" : "#d8c39d"} /><rect x="0" y={fY} width={W} height="6" fill="#0003" />
        {/* BÀN + màn hình + bàn phím + cốc vẽ */}
        {(() => { const dx = wide ? 130 : 60, dy = fY - 150, dw = 420; return (<g>
          <rect x={dx} y={dy + 90} width={dw} height="70" rx="6" fill="#6f4a2a" /><rect x={dx} y={dy + 80} width={dw} height="20" rx="6" fill="url(#ofdesk)" />
          <rect x={dx + 24} y={dy + 160} width="18" height="90" fill="#5c3d22" /><rect x={dx + dw - 42} y={dy + 160} width="18" height="90" fill="#5c3d22" />
          {/* monitor */}
          <rect x={dx + dw / 2 - 90} y={dy - 40} width="180" height="118" rx="10" fill="#1e2a38" stroke={ink} strokeWidth="5" /><rect x={dx + dw / 2 - 80} y={dy - 30} width="160" height="98" rx="4" fill="#dff1ff" />
          <polyline points={`${dx + dw / 2 - 66},${dy + 52} ${dx + dw / 2 - 30},${dy + 20} ${dx + dw / 2},${dy + 34} ${dx + dw / 2 + 60},${dy - 8}`} fill="none" stroke="#e23744" strokeWidth="5" /><rect x={dx + dw / 2 - 8} y={dy + 78} width="16" height="16" fill="#1e2a38" /><rect x={dx + dw / 2 - 26} y={dy + 92} width="52" height="8" rx="4" fill="#1e2a38" />
          {/* keyboard + mug */}
          <rect x={dx + dw / 2 - 60} y={dy + 108} width="120" height="26" rx="5" fill="#c7d2de" stroke={ink} strokeWidth="3" />
          <g transform={`translate(${dx + dw - 70} ${dy + 96})`}><rect x="-22" y="-2" width="44" height="40" rx="6" fill="#e23744" stroke={ink} strokeWidth="3" /><path d="M 22 6 q 16 6 0 22" fill="none" stroke={ink} strokeWidth="3" /><ellipse cx="0" cy="0" rx="22" ry="6" fill="#fff" /></g>
        </g>); })()}
        {/* cây trong chậu vẽ */}
        {(() => { const px2 = wide ? 1620 : 860, py = fY - 30; return (<g><path d={`M ${px2 - 26} ${py} L ${px2 + 26} ${py} L ${px2 + 18} ${py + 70} L ${px2 - 18} ${py + 70} Z`} fill="#c96f3a" stroke={ink} strokeWidth="4" />{[[-30, -70, -18], [30, -70, 18], [0, -96, 0]].map(([dxL, dyL, r], i) => <ellipse key={i} cx={px2 + (dxL as number) * 0.6} cy={py + (dyL as number)} rx="26" ry="40" fill={i === 2 ? "#4e9a4e" : "#5cb85c"} stroke={ink} strokeWidth="4" transform={`rotate(${r} ${px2} ${py})`} />)}</g>); })()}
      </svg>);
  }
  if (kind === "office_old") return (
    <AbsoluteFill>
      {Wall(dark ? "#12203a" : "#eaf1f8", dark ? "#0e1830" : "#dbe7f3")}
      {ceiling(dark ? "#1a2a44" : "#d3e0ee")}
      {win(wide ? 1180 : 560, 160, 420, 300)}
      <Floor col={dark ? "#0f1a30" : "#d9c3a0"} />
      {/* desk + PC */}
      {box(wide ? 150 : 60, floorPct * (wide ? 1080 : 1920) - 150, 360, 150, dark ? "#243a5e" : "#a9764e", 10)}
      {emo(wide ? 210 : 110, floorPct * (wide ? 1080 : 1920) - 250, 100, "🖥️")}
      {emo(wide ? 360 : 250, floorPct * (wide ? 1080 : 1920) - 130, 44, "☕")}
      {emo(wide ? 1560 : 820, floorPct * (wide ? 1080 : 1920) - 150, 110, "🪴")}
    </AbsoluteFill>);

  if (kind === "home") {
    const W = wide ? 1920 : 1080, H = wide ? 1080 : 1920, fY = floorPct * H, ink = "#3a2b22";
    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width, height }}>
        <defs>
          <linearGradient id="hmw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={dark ? "#2a2030" : "#f7ecdb"} /><stop offset="1" stopColor={dark ? "#1c1422" : "#eddcc6"} /></linearGradient>
          <linearGradient id="hmsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={dark ? "#22314f" : "#bfe0ff"} /><stop offset="1" stopColor={dark ? "#0e1a2e" : "#eaf6ff"} /></linearGradient>
        </defs>
        <rect x="0" y="0" width={W} height={fY} fill="url(#hmw)" />
        {(() => { const wx = wide ? 1270 : 610, wy = 150, ww = 380, wh = 280; return (<g>
          <rect x={wx - 12} y={wy - 12} width={ww + 24} height={wh + 24} rx="10" fill="#fff" stroke={ink} strokeWidth="5" />
          <clipPath id="hmwin"><rect x={wx} y={wy} width={ww} height={wh} /></clipPath>
          <g clipPath="url(#hmwin)"><rect x={wx} y={wy} width={ww} height={wh} fill="url(#hmsky)" /><circle cx={wx + 60} cy={wy + 60} r="30" fill={dark ? "#e6eef8" : "#ffe08a"} /><ellipse cx={wx + ww - 90} cy={wy + 80} rx="60" ry="24" fill="#fff" opacity=".85" /></g>
          <rect x={wx - 20} y={wy - 16} width="46" height={wh + 30} rx="16" fill="#c0504d" /><rect x={wx + ww - 26} y={wy - 16} width="46" height={wh + 30} rx="16" fill="#c0504d" />
        </g>); })()}
        <g><rect x={wide ? 210 : 100} y="160" width="150" height="120" rx="6" fill="#fff" stroke={ink} strokeWidth="5" /><rect x={wide ? 220 : 110} y="170" width="130" height="100" fill="#ffe1c4" /><circle cx={wide ? 285 : 175} cy="205" r="20" fill="#ff9f68" /><path d={`M ${wide ? 220 : 110} 270 q 65 -34 130 0 Z`} fill="#8fbf7a" /></g>
        <line x1={W * 0.5} y1="0" x2={W * 0.5} y2="70" stroke="#8a7a6a" strokeWidth="4" /><path d={`M ${W * 0.5 - 44} 118 Q ${W * 0.5} 66 ${W * 0.5 + 44} 118 Z`} fill="#e8c477" stroke={ink} strokeWidth="4" /><ellipse cx={W * 0.5} cy="120" rx="30" ry="8" fill="#ffe9a8" />
        <rect x="0" y={fY} width={W} height={H - fY} fill={dark ? "#1b1320" : "#c9a87d"} /><rect x="0" y={fY} width={W} height="6" fill="#0003" />
        <ellipse cx={W * 0.5} cy={fY + (H - fY) * 0.55} rx={W * 0.34} ry={(H - fY) * 0.34} fill={dark ? "#2a2036" : "#d98f6a"} opacity=".8" />
        {(() => { const sx = wide ? 150 : 60, sy = fY - 150, sofa = dark ? "#5a4a63" : "#e07a52"; return (<g>
          <rect x={sx} y={sy + 60} width="330" height="110" rx="26" fill={sofa} stroke={ink} strokeWidth="5" />
          <rect x={sx - 6} y={sy} width="60" height="150" rx="24" fill={sofa} stroke={ink} strokeWidth="5" /><rect x={sx + 276} y={sy} width="60" height="150" rx="24" fill={sofa} stroke={ink} strokeWidth="5" />
          <rect x={sx + 54} y={sy + 10} width="222" height="80" rx="18" fill={sofa} stroke={ink} strokeWidth="4" />
          <rect x={sx + 66} y={sy + 66} width="90" height="60" rx="14" fill="#ffffff33" stroke={ink} strokeWidth="3" /><rect x={sx + 176} y={sy + 66} width="90" height="60" rx="14" fill="#ffffff33" stroke={ink} strokeWidth="3" />
        </g>); })()}
        {(() => { const tx = wide ? 1470 : 780, ty = fY - 210; return (<g>
          <rect x={tx} y={ty} width="300" height="180" rx="10" fill="#1b2430" stroke={ink} strokeWidth="6" /><rect x={tx + 12} y={ty + 12} width="276" height="156" rx="4" fill="#63b3e6" /><path d={`M ${tx + 40} ${ty + 130} L ${tx + 110} ${ty + 70} L ${tx + 160} ${ty + 100} L ${tx + 250} ${ty + 40}`} fill="none" stroke="#fff" strokeWidth="5" />
          <rect x={tx + 40} y={ty + 180} width="220" height="26" rx="6" fill="#7a5a3a" /><rect x={tx + 60} y={ty + 206} width="16" height="30" fill="#7a5a3a" /><rect x={tx + 224} y={ty + 206} width="16" height="30" fill="#7a5a3a" />
        </g>); })()}
      </svg>);
  }

  if (kind === "street") {
    const W = wide ? 1920 : 1080, H = wide ? 1080 : 1920, fY = floorPct * H, ink = "#2a2f38";
    const cloud = (cx: number, cy: number, s: number) => <g transform={`translate(${cx + sway * 3} ${cy})`}><ellipse cx="0" cy="0" rx={s} ry={s * 0.6} fill="#fff" /><ellipse cx={s * 0.8} cy={s * 0.1} rx={s * 0.7} ry={s * 0.5} fill="#fff" /><ellipse cx={-s * 0.8} cy={s * 0.1} rx={s * 0.6} ry={s * 0.45} fill="#fff" /></g>;
    const SIGN = ["DINER", "BANK", "SHOP", "CAFE"];
    const shopW = W / (wide ? 4 : 2.6);
    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width, height }}>
        <defs><linearGradient id="stsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#8fc8f5" /><stop offset="1" stopColor="#dff1ff" /></linearGradient></defs>
        <rect x="0" y="0" width={W} height={fY} fill="url(#stsky)" />
        <circle cx={W - 140} cy="110" r="52" fill="#ffe08a" />
        {cloud(W * 0.2, 130, 46)}{cloud(W * 0.55, 90, 40)}
        {/* dãy cửa hàng vẽ */}
        {Array.from({ length: wide ? 4 : 3 }).map((_, i) => { const l = i * shopW + 10, bcol = ["#d98b6a", "#7fa8cf", "#8cc07e", "#d8b46a"][i % 4], top = fY - (wide ? 380 : 520); return (<g key={i}>
          <rect x={l} y={top} width={shopW - 20} height={fY - top} fill={bcol} stroke={ink} strokeWidth="4" />
          {[0, 1].map((r) => [0, 1, 2].map((c) => <rect key={`${r}${c}`} x={l + 30 + c * (shopW / 3.4)} y={top + 40 + r * 120} width={shopW / 5} height="80" fill="#cfeaff" stroke={ink} strokeWidth="3" />))}
          <rect x={l - 6} y={top - 8} width={shopW - 8} height="40" fill={i % 2 ? "#e23744" : "#2f7d4f"} />
          {Array.from({ length: 6 }).map((_, k) => <rect key={k} x={l - 6 + k * (shopW / 6)} y={top - 8} width={shopW / 12} height="40" fill="#fff" opacity=".35" />)}
          <rect x={l + shopW / 2 - 70} y={top + 40} width="140" height="44" rx="6" fill="#1e2a38" /><text x={l + shopW / 2} y={top + 71} textAnchor="middle" fill="#ffd76b" fontFamily="Poppins, sans-serif" fontWeight="800" fontSize="30">{SIGN[i % 4]}</text>
          <rect x={l + shopW / 2 - 34} y={fY - 120} width="68" height="120" rx="6" fill={ink} opacity=".8" />
        </g>); })}
        {/* cờ Mỹ trên cột */}
        <line x1={wide ? 70 : 40} y1={fY - 300} x2={wide ? 70 : 40} y2={fY - 40} stroke={ink} strokeWidth="6" /><rect x={wide ? 70 : 40} y={fY - 300} width={70 + Math.sin(time * 2) * 6} height="46" fill="#b22234" /><rect x={wide ? 70 : 40} y={fY - 300} width={30} height="24" fill="#3c3b6e" />
        {/* vỉa hè + đường */}
        <rect x="0" y={fY} width={W} height={H - fY} fill="#8a96a2" /><rect x="0" y={fY} width={W} height="14" fill="#b9c2cc" /><rect x="0" y={fY + (H - fY) * 0.4} width={W} height={(H - fY) * 0.6} fill="#3c434c" />
        {Array.from({ length: 8 }).map((_, i) => <rect key={i} x={i * (W / 7)} y={fY + (H - fY) * 0.68} width={W / 14} height="14" fill="#ffd76b" />)}
        {/* taxi vàng Mỹ vẽ */}
        {(() => { const cx = wide ? 1360 : 700, cy = fY + (H - fY) * 0.42; return (<g><rect x={cx} y={cy} width="230" height="70" rx="18" fill="#ffcf33" stroke={ink} strokeWidth="5" /><path d={`M ${cx + 30} ${cy} Q ${cx + 60} ${cy - 46} ${cx + 130} ${cy - 46} L ${cx + 190} ${cy - 46} Q ${cx + 210} ${cy - 20} ${cx + 210} ${cy} Z`} fill="#ffcf33" stroke={ink} strokeWidth="5" /><rect x={cx + 60} y={cy - 40} width="55" height="36" fill="#bfe3ff" stroke={ink} strokeWidth="3" /><rect x={cx + 128} y={cy - 40} width="60" height="36" fill="#bfe3ff" stroke={ink} strokeWidth="3" /><rect x={cx + 95} y={cy - 58} width="42" height="16" rx="3" fill="#111" /><circle cx={cx + 55} cy={cy + 70} r="26" fill="#222" stroke={ink} strokeWidth="4" /><circle cx={cx + 180} cy={cy + 70} r="26" fill="#222" stroke={ink} strokeWidth="4" /></g>); })()}
        {/* cây vẽ */}
        {(() => { const tx = wide ? 250 : 130, ty = fY; return (<g><rect x={tx - 12} y={ty - 90} width="24" height="90" fill="#7a5230" /><circle cx={tx} cy={ty - 120} r="56" fill="#4e9a4e" stroke={ink} strokeWidth="4" /><circle cx={tx - 40} cy={ty - 96} r="40" fill="#5cb85c" stroke={ink} strokeWidth="4" /><circle cx={tx + 40} cy={ty - 96} r="40" fill="#5cb85c" stroke={ink} strokeWidth="4" /></g>); })()}
      </svg>);
  }

  if (kind === "bank") {
    const W = wide ? 1920 : 1080, H = wide ? 1080 : 1920, fY = floorPct * H, ink = "#243447";
    const colc = dark ? "#2a3d5a" : "#d7e1ee", colc2 = dark ? "#1c2c44" : "#c2cfe0";
    const column = (cx: number) => (<g><rect x={cx - 44} y="90" width="88" height="30" rx="4" fill={colc2} stroke={ink} strokeWidth="4" /><rect x={cx - 36} y="120" width="72" height={fY - 200} fill={colc} stroke={ink} strokeWidth="4" />{[-18, 0, 18].map((o, i) => <rect key={i} x={cx + o - 2} y="126" width="4" height={fY - 210} fill="#00000018" />)}<rect x={cx - 48} y={fY - 80} width="96" height="34" rx="4" fill={colc2} stroke={ink} strokeWidth="4" /></g>);
    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width, height }}>
        <defs><linearGradient id="bkw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={dark ? "#122038" : "#eaf0f8"} /><stop offset="1" stopColor={dark ? "#0c1728" : "#d7e2f0"} /></linearGradient></defs>
        <rect x="0" y="0" width={W} height={fY} fill="url(#bkw)" />
        <rect x="0" y="0" width={W} height="44" fill={dark ? "#152743" : "#c9d6e6"} />
        {column(wide ? 130 : 70)}{column(wide ? 320 : 220)}{column(wide ? W - 320 : W - 220)}{column(wide ? W - 130 : W - 70)}
        {/* biển BANK + huy hiệu $ */}
        <rect x={W * 0.5 - 200} y="70" width="400" height="80" rx="10" fill={dark ? "#1c2c44" : "#31507a"} stroke={ink} strokeWidth="5" /><text x={W * 0.5} y="128" textAnchor="middle" fill="#ffd76b" fontFamily="Poppins, sans-serif" fontWeight="900" fontSize="52">BANK</text>
        <g transform={`translate(${wide ? 470 : 300} 260)`}><circle r="46" fill="#2f7d4f" stroke={ink} strokeWidth="5" /><text x="0" y="18" textAnchor="middle" fill="#fff" fontFamily="Poppins, sans-serif" fontWeight="900" fontSize="54">$</text></g>
        {/* đồng hồ */}
        <g transform={`translate(${wide ? W - 470 : W - 300} 250)`}><circle r="40" fill="#fff" stroke={ink} strokeWidth="6" /><line x1="0" y1="0" x2="0" y2="-22" stroke={ink} strokeWidth="4" transform={`rotate(${time * 6})`} /><line x1="0" y1="0" x2="15" y2="0" stroke={ink} strokeWidth="4" /><circle r="4" fill={ink} /></g>
        {/* sàn đá */}
        <rect x="0" y={fY} width={W} height={H - fY} fill={dark ? "#0e1a2e" : "#c9bd9e"} /><rect x="0" y={fY} width={W} height="6" fill="#0003" />
        {/* KÉT SẮT vẽ */}
        {(() => { const vx = wide ? 250 : 130, vy = fY - 40; return (<g><rect x={vx - 90} y={vy - 190} width="180" height="190" rx="12" fill={dark ? "#33465e" : "#7f8c9c"} stroke={ink} strokeWidth="6" /><circle cx={vx} cy={vy - 95} r="60" fill={dark ? "#26374d" : "#93a0b0"} stroke={ink} strokeWidth="6" /><circle cx={vx} cy={vy - 95} r="30" fill={dark ? "#1c2b3e" : "#aab6c4"} stroke={ink} strokeWidth="4" />{[0, 45, 90, 135].map((a) => <rect key={a} x={vx - 3} y={vy - 155} width="6" height="20" fill={ink} transform={`rotate(${a} ${vx} ${vy - 95})`} />)}</g>); })()}
        {/* QUẦY giao dịch vẽ */}
        {(() => { const cx = wide ? 560 : 240, cw = wide ? 800 : 620, cy = fY - 130; return (<g><rect x={cx} y={cy + 40} width={cw} height="90" fill={dark ? "#243a5e" : "#8a5a3a"} stroke={ink} strokeWidth="5" /><rect x={cx} y={cy + 24} width={cw} height="22" rx="4" fill={dark ? "#2f4a72" : "#a9764e"} />{Array.from({ length: 4 }).map((_, i) => <rect key={i} x={cx + 30 + i * (cw / 4)} y={cy - 40} width="6" height="70" fill="#9fb4cc" />)}<rect x={cx + 20} y={cy - 40} width={cw - 40} height="6" fill="#9fb4cc" /></g>); })()}
      </svg>);
  }

  if (kind === "store") {
    const W = wide ? 1920 : 1080, H = wide ? 1080 : 1920, fY = floorPct * H, ink = "#33414a";
    const shelf = (sx: number, sw: number) => (<g><rect x={sx} y={fY - 320} width={sw} height="320" fill={dark ? "#22303e" : "#e7ddc8"} stroke={ink} strokeWidth="4" />{[0, 1, 2].map((r) => (<g key={r}><rect x={sx} y={fY - 320 + 20 + r * 100} width={sw} height="14" fill={dark ? "#2e4150" : "#c9b79a"} />{Array.from({ length: Math.floor(sw / 46) }).map((_, k) => <rect key={k} x={sx + 12 + k * 46} y={fY - 320 + 34 + r * 100} width="34" height="56" rx="4" fill={["#e23744", "#3E7BFA", "#F5B301", "#2FA84F", "#7C5CFF", "#FB923C"][(k + r) % 6]} stroke={ink} strokeWidth="2" />)}</g>))}</g>);
    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width, height }}>
        <rect x="0" y="0" width={W} height={fY} fill={dark ? "#12202e" : "#eef4ea"} />
        <rect x="0" y="0" width={W} height="44" fill={dark ? "#183042" : "#dbe8dc"} />{[0, 1, 2, 3].map((i) => <rect key={i} x={W * 0.2 + i * (W * 0.16)} y="0" width="80" height="70" rx="0 0 40 40" fill="#ffe08a" opacity=".8" />)}
        {/* biển SALE */}
        <g transform={`translate(${W * 0.5} 150)`}><rect x="-120" y="-40" width="240" height="80" rx="12" fill="#e23744" stroke={ink} strokeWidth="5" /><text x="0" y="18" textAnchor="middle" fill="#fff" fontFamily="Poppins,sans-serif" fontWeight="900" fontSize="50">SALE 50%</text></g>
        {shelf(wide ? 90 : 40, wide ? 520 : 360)}
        {shelf(wide ? W - 610 : W - 400, wide ? 520 : 360)}
        <rect x="0" y={fY} width={W} height={H - fY} fill={dark ? "#0f1a2e" : "#d3d8cf"} /><rect x="0" y={fY} width={W} height="6" fill="#0003" />
        {/* XE ĐẨY vẽ */}
        {(() => { const cx = wide ? 1330 : 700, cy = fY + 20; return (<g><path d={`M ${cx} ${cy - 70} L ${cx + 20} ${cy - 70} L ${cx + 44} ${cy} L ${cx + 150} ${cy}`} fill="none" stroke={ink} strokeWidth="6" /><path d={`M ${cx + 24} ${cy - 50} L ${cx + 150} ${cy - 50} L ${cx + 134} ${cy - 6} L ${cx + 40} ${cy - 6} Z`} fill="#c9d2da" stroke={ink} strokeWidth="5" />{[0, 1, 2].map((i) => <line key={i} x1={cx + 40 + i * 30} y1={cy - 50} x2={cx + 34 + i * 30} y2={cy - 6} stroke={ink} strokeWidth="3" />)}<circle cx={cx + 55} cy={cy + 16} r="16" fill="#333" stroke={ink} strokeWidth="4" /><circle cx={cx + 125} cy={cy + 16} r="16" fill="#333" stroke={ink} strokeWidth="4" /></g>); })()}
      </svg>);
  }

  if (kind === "city") {
    const W = wide ? 1920 : 1080, H = wide ? 1080 : 1920, fY = floorPct * H, ink = "#1a2740";
    const cols = wide ? [30, 250, 470, 700, 930, 1180, 1440, 1700] : [20, 220, 430, 650, 880];
    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width, height }}>
        <defs><linearGradient id="ctsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={dark ? "#0c1730" : "#9cc3ef"} /><stop offset="1" stopColor={dark ? "#141f3a" : "#e2eefb"} /></linearGradient></defs>
        <rect x="0" y="0" width={W} height={fY} fill="url(#ctsky)" />
        <circle cx={W - 160} cy="120" r="48" fill={dark ? "#d7e0ee" : "#ffe08a"} />
        {cols.map((l, i) => { const bw = 190, h = 420 - (i % 4) * 70, top = fY - h, bcol = dark ? ["#152744", "#122038"][i % 2] : ["#8fb3da", "#a7c6e8"][i % 2]; return (<g key={i}>
          <rect x={l} y={top} width={bw} height={h} fill={bcol} stroke={ink} strokeWidth="3" />
          {(i % 3 === 0) && <rect x={l + bw / 2 - 6} y={top - 40} width="12" height="40" fill={ink} />}
          {(i % 3 === 1) && <rect x={l + 20} y={top - 30} width={bw - 40} height="30" rx="6" fill={dark ? "#0e1c34" : "#7ba0cc"} />}
          {Array.from({ length: 5 }).map((_, r) => Array.from({ length: 3 }).map((_, c) => <rect key={`${r}${c}`} x={l + 22 + c * (bw / 3.2)} y={top + 24 + r * (h / 6)} width={bw / 5} height={h / 11} fill={dark ? ((r + c) % 3 === i % 3 ? "#f5d76e" : "#0a1526") : "#d6e8fb"} />))}
        </g>); })}
        <rect x="0" y={fY} width={W} height={H - fY} fill={dark ? "#0a1424" : "#9fb3c9"} /><rect x="0" y={fY} width={W} height="6" fill="#0004" />
        {Array.from({ length: 7 }).map((_, i) => <rect key={i} x={i * (W / 6)} y={fY + (H - fY) * 0.5} width={W / 12} height="12" fill="#ffd76b" />)}
      </svg>);
  }

  if (kind === "park") {
    const W = wide ? 1920 : 1080, H = wide ? 1080 : 1920, fY = floorPct * H, ink = "#2f4a2a";
    const tree = (tx: number, s: number) => (<g><rect x={tx - 14 * s} y={fY - 130 * s} width={28 * s} height={130 * s} rx={8} fill="#7a5230" stroke="#3a2b22" strokeWidth="4" /><circle cx={tx} cy={fY - 150 * s} r={62 * s} fill="#4e9a4e" stroke={ink} strokeWidth="4" /><circle cx={tx - 46 * s} cy={fY - 120 * s} r={44 * s} fill="#5cb85c" stroke={ink} strokeWidth="4" /><circle cx={tx + 46 * s} cy={fY - 120 * s} r={44 * s} fill="#5cb85c" stroke={ink} strokeWidth="4" /><circle cx={tx} cy={fY - 190 * s} r={40 * s} fill="#66c266" stroke={ink} strokeWidth="4" /></g>);
    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width, height }}>
        <defs><linearGradient id="pks" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#7fbfe8" /><stop offset="1" stopColor="#dff1ff" /></linearGradient></defs>
        <rect x="0" y="0" width={W} height={fY} fill="url(#pks)" />
        <circle cx={wide ? 170 : 90} cy="120" r="54" fill="#ffe08a" />
        <g transform={`translate(${W * 0.55 + sway * 3} 130)`}><ellipse rx="60" ry="34" fill="#fff" /><ellipse cx="60" cy="8" rx="46" ry="28" fill="#fff" /><ellipse cx="-56" cy="8" rx="40" ry="24" fill="#fff" /></g>
        <rect x="0" y={fY} width={W} height={H - fY} fill="#86c962" /><rect x="0" y={fY} width={W} height="6" fill="#0002" />
        {/* lối đi */}
        <path d={`M ${W * 0.5 - 140} ${H} L ${W * 0.5 - 40} ${fY + 20} L ${W * 0.5 + 40} ${fY + 20} L ${W * 0.5 + 220} ${H} Z`} fill="#d8c79a" />
        {/* hồ */}
        <ellipse cx={wide ? 1560 : 850} cy={fY + (H - fY) * 0.55} rx={wide ? 220 : 150} ry={(H - fY) * 0.22} fill="#7ec8e8" stroke="#5aa8c8" strokeWidth="5" />
        {tree(wide ? 260 : 140, 1.1)}{tree(wide ? 1650 : 900, 0.9)}
        {/* ghế công viên vẽ */}
        {(() => { const gx = wide ? 780 : 420, gy = fY - 20; return (<g><rect x={gx} y={gy - 30} width="180" height="16" rx="4" fill="#8a5a3a" stroke={ink} strokeWidth="3" /><rect x={gx} y={gy} width="180" height="16" rx="4" fill="#9a6a44" stroke={ink} strokeWidth="3" /><rect x={gx + 8} y={gy + 16} width="14" height="40" fill="#5a6b72" /><rect x={gx + 158} y={gy + 16} width="14" height="40" fill="#5a6b72" /><rect x={gx + 8} y={gy - 60} width="14" height="46" fill="#5a6b72" /><rect x={gx + 158} y={gy - 60} width="14" height="46" fill="#5a6b72" /></g>); })()}
      </svg>);
  }

  if (kind === "hospital") {
    const W = wide ? 1920 : 1080, H = wide ? 1080 : 1920, fY = floorPct * H, ink = "#2a4a52";
    const beat = Math.abs(Math.sin(time * 3));
    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width, height }}>
        <defs><linearGradient id="hpw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={dark ? "#123240" : "#e9f8f5"} /><stop offset="1" stopColor={dark ? "#0b2028" : "#d6efeb"} /></linearGradient></defs>
        <rect x="0" y="0" width={W} height={fY} fill="url(#hpw)" />
        <rect x="0" y="0" width={W} height="44" fill={dark ? "#123842" : "#cfeee9"} /><rect x={W * 0.5 - 3} y="44" width="6" height="60" fill="#9ab" /><ellipse cx={W * 0.5} cy="108" rx="34" ry="9" fill="#ffe9a8" />
        {/* chữ thập */}
        <g transform={`translate(${wide ? 150 : 80} 210)`}><circle r="52" fill="#fff" stroke={ink} strokeWidth="5" /><rect x="-12" y="-30" width="24" height="60" fill="#e23744" /><rect x="-30" y="-12" width="60" height="24" fill="#e23744" /></g>
        {/* cửa sổ */}
        {(() => { const wx = wide ? 1260 : 600, wy = 150, ww = 360, wh = 250; return (<g><rect x={wx - 12} y={wy - 12} width={ww + 24} height={wh + 24} rx="10" fill="#fff" stroke={ink} strokeWidth="5" /><rect x={wx} y={wy} width={ww} height={wh} fill="#bfe6ff" /><rect x={wx + ww / 2 - 4} y={wy} width="8" height={wh} fill="#fff" /><rect x={wx} y={wy + wh / 2 - 4} width={ww} height="8" fill="#fff" /></g>); })()}
        <rect x="0" y={fY} width={W} height={H - fY} fill={dark ? "#0b2028" : "#cfe4e0"} /><rect x="0" y={fY} width={W} height="6" fill="#0003" />
        {/* GIƯỜNG bệnh vẽ */}
        {(() => { const bx = wide ? 130 : 50, by = fY - 80, bw = 440; return (<g><rect x={bx} y={by - 60} width="16" height="80" fill="#b8c4cc" /><rect x={bx} y={by - 90} width={bw * 0.5} height="40" rx="8" fill="#eef4f3" stroke={ink} strokeWidth="4" /><rect x={bx} y={by - 50} width={bw} height="60" rx="10" fill="#dfeeec" stroke={ink} strokeWidth="4" /><rect x={bx + bw - 16} y={by - 60} width="16" height="80" fill="#b8c4cc" /><rect x={bx + 20} y={by - 84} width="120" height="34" rx="12" fill="#fff" stroke={ink} strokeWidth="3" /><rect x={bx} y={by + 10} width={bw} height="14" fill="#9fb3b0" /></g>); })()}
        {/* IV stand */}
        {(() => { const ix = wide ? 640 : 480, iy = fY; return (<g><line x1={ix} y1={iy - 300} x2={ix} y2={iy} stroke="#9aa" strokeWidth="6" /><path d={`M ${ix} ${iy - 300} l -18 0 m 18 0 l 18 0`} stroke="#9aa" strokeWidth="6" /><rect x={ix - 20} y={iy - 290} width="40" height="60" rx="8" fill="#bfe6ff" stroke={ink} strokeWidth="4" /></g>); })()}
        {/* MÁY ĐO TIM vẽ (nhịp đập) */}
        {(() => { const mx = wide ? 1500 : 800, my = fY - 220; return (<g><rect x={mx} y={my} width="220" height="150" rx="12" fill="#12303a" stroke={ink} strokeWidth="6" /><rect x={mx + 12} y={my + 12} width="196" height="100" rx="4" fill="#031318" /><polyline points={`${mx + 20},${my + 62} ${mx + 70},${my + 62} ${mx + 90},${my + 30 - beat * 20} ${mx + 110},${my + 95} ${mx + 130},${my + 62} ${mx + 200},${my + 62}`} fill="none" stroke="#39ff88" strokeWidth="4" /><rect x={mx + 20} y={my + 120} width="40" height="20" rx="4" fill="#e23744" /><text x={mx + 130} y={my + 138} fill="#39ff88" fontFamily="Poppins,sans-serif" fontSize="20" fontWeight="800">72 BPM</text></g>); })()}
      </svg>);
  }

  if (kind === "lab") {
    const W = wide ? 1920 : 1080, H = wide ? 1080 : 1920, fY = floorPct * H, ink = "#2c3550";
    const bub = Math.sin(time * 4) * 4;
    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width, height }}>
        <defs><linearGradient id="lbw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={dark ? "#18233e" : "#eef1fb"} /><stop offset="1" stopColor={dark ? "#101830" : "#e1e7f6"} /></linearGradient></defs>
        <rect x="0" y="0" width={W} height={fY} fill="url(#lbw)" />
        <rect x="0" y="0" width={W} height="44" fill={dark ? "#1c2846" : "#d6ddf3"} /><rect x={W * 0.5 - 3} y="44" width="6" height="60" fill="#9ab" /><ellipse cx={W * 0.5} cy="108" rx="34" ry="9" fill="#dfe8ff" />
        {/* kệ hoá chất */}
        <g><rect x={wide ? 130 : 60} y="170" width="300" height="18" fill={dark ? "#2a3a5a" : "#b7c0d8"} />{[0, 1, 2, 3, 4].map((i) => <g key={i} transform={`translate(${(wide ? 150 : 80) + i * 54} 130)`}><rect x="-12" y="0" width="24" height="40" rx="6" fill={["#e23744", "#3E7BFA", "#2FA84F", "#F5B301", "#7C5CFF"][i]} stroke={ink} strokeWidth="3" opacity=".85" /><rect x="-6" y="-8" width="12" height="10" fill="#9aa" /></g>)}</g>
        {/* bảng DNA/chart tường */}
        <g transform={`translate(${wide ? 1420 : 760} 160)`}><rect x="0" y="0" width="150" height="110" rx="6" fill="#fff" stroke={ink} strokeWidth="5" />{[0, 1, 2, 3].map((i) => <line key={i} x1={20 + i * 30} y1="20" x2={20 + i * 30} y2="90" stroke={i % 2 ? "#3E7BFA" : "#e23744"} strokeWidth="4" />)}{[0, 1, 2].map((i) => <path key={i} d={`M 20 ${34 + i * 22} Q 75 ${24 + i * 22} 110 ${34 + i * 22}`} fill="none" stroke="#7C5CFF" strokeWidth="3" />)}</g>
        <rect x="0" y={fY} width={W} height={H - fY} fill={dark ? "#101830" : "#d6d8e6"} /><rect x="0" y={fY} width={W} height="6" fill="#0003" />
        {/* BÀN thí nghiệm + dụng cụ vẽ */}
        {(() => { const bx = wide ? 120 : 50, bw = 460, by = fY - 110; return (<g><rect x={bx} y={by} width={bw} height="26" fill={dark ? "#2f3d5e" : "#c7cee0"} stroke={ink} strokeWidth="4" /><rect x={bx + 20} y={by + 26} width="18" height="84" fill="#8a93aa" /><rect x={bx + bw - 38} y={by + 26} width="18" height="84" fill="#8a93aa" />
          {/* bình cầu (flask) có dung dịch */}
          <g transform={`translate(${bx + 90} ${by})`}><path d="M -14 -8 L 14 -8 L 30 0 Q 44 40 0 44 Q -44 40 -30 0 Z" fill="#dff" stroke={ink} strokeWidth="4" /><path d="M -22 18 Q 0 40 22 18 Q 30 40 0 44 Q -30 40 -22 18 Z" fill="#2FA84F" opacity=".8" /><circle cx={bub} cy="24" r="4" fill="#fff" opacity=".7" /></g>
          {/* ống nghiệm rack */}
          <g transform={`translate(${bx + 210} ${by - 40})`}>{[0, 1, 2].map((i) => <g key={i} transform={`translate(${i * 26} 0)`}><rect x="-8" y="0" width="16" height="60" rx="8" fill="#e6f0ff" stroke={ink} strokeWidth="3" /><rect x="-8" y="30" width="16" height="30" rx="0" fill={["#e23744", "#3E7BFA", "#F5B301"][i]} opacity=".8" /></g>)}<rect x="-14" y="56" width="82" height="12" rx="4" fill="#8a93aa" /></g>
          {/* kính hiển vi */}
          <g transform={`translate(${bx + bw - 90} ${by - 10})`}><rect x="-30" y="30" width="60" height="16" rx="6" fill="#556" /><rect x="-6" y="-40" width="12" height="70" fill="#66788f" /><circle cx="0" cy="-46" r="12" fill="#8a93aa" stroke={ink} strokeWidth="3" /><rect x="-4" y="-34" width="8" height="30" fill="#445" /></g>
        </g>); })()}
      </svg>);
  }

  if (kind === "gym") {
    const W = wide ? 1920 : 1080, H = wide ? 1080 : 1920, fY = floorPct * H, ink = "#2b3340";
    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width, height }}>
        <defs><linearGradient id="gyw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={dark ? "#1c2534" : "#e7edf4"} /><stop offset="1" stopColor={dark ? "#141b28" : "#d5dfea"} /></linearGradient></defs>
        <rect x="0" y="0" width={W} height={fY} fill="url(#gyw)" />
        <rect x="0" y="0" width={W} height="44" fill={dark ? "#182234" : "#cdd8e6"} />
        {/* sọc tường thể thao */}
        <rect x="0" y={fY * 0.42} width={W} height="26" fill={T.accent} opacity=".5" /><rect x="0" y={fY * 0.42 + 34} width={W} height="10" fill="#e2483a" opacity=".7" />
        {/* gương lớn phản chiếu */}
        {(() => { const gx = wide ? 1360 : 700, gy = 150, gw = wide ? 440 : 320, gh = fY - 260; return (<g><rect x={gx - 10} y={gy - 10} width={gw + 20} height={gh + 20} rx="8" fill="#8895a3" /><rect x={gx} y={gy} width={gw} height={gh} fill="#cfe0ef" opacity=".7" /><path d={`M ${gx} ${gy} L ${gx + gw * 0.5} ${gy} L ${gx} ${gy + gh * 0.6} Z`} fill="#fff" opacity=".25" /></g>); })()}
        {/* đồng hồ */}
        <g transform={`translate(${wide ? 470 : 300} 210)`}><circle r="40" fill="#fff" stroke={ink} strokeWidth="6" /><line x1="0" y1="0" x2="0" y2="-22" stroke={ink} strokeWidth="4" transform={`rotate(${time * 6})`} /><line x1="0" y1="0" x2="15" y2="0" stroke={ink} strokeWidth="4" /><circle r="4" fill={ink} /></g>
        {/* sàn cao su */}
        <rect x="0" y={fY} width={W} height={H - fY} fill={dark ? "#121a26" : "#39424f"} /><rect x="0" y={fY} width={W} height="6" fill="#0004" />
        {Array.from({ length: 8 }).map((_, i) => <line key={i} x1={i * (W / 7)} y1={fY} x2={i * (W / 7)} y2={H} stroke="#0000001a" strokeWidth="3" />)}
        {/* giá tạ + đôi tạ tay */}
        {(() => { const rx = wide ? 120 : 50, ry = fY - 150; return (<g><rect x={rx} y={ry} width="260" height="18" rx="6" fill={dark ? "#2a3648" : "#9aa6b4"} stroke={ink} strokeWidth="4" /><rect x={rx} y={ry + 150} width="260" height="16" rx="6" fill={dark ? "#2a3648" : "#9aa6b4"} /><rect x={rx + 8} y={ry} width="14" height="166" fill="#8895a3" /><rect x={rx + 238} y={ry} width="14" height="166" fill="#8895a3" />
          {[0, 1, 2].map((i) => { const dy = ry + 30 + i * 44, col = ["#e2483a", "#3E7BFA", "#F5B301"][i]; return (<g key={i} transform={`translate(${rx + 40} ${dy})`}><rect x="0" y="-6" width="180" height="12" rx="6" fill="#555d68" /><rect x="-14" y="-22" width="26" height="44" rx="6" fill={col} stroke={ink} strokeWidth="3" /><rect x="168" y="-22" width="26" height="44" rx="6" fill={col} stroke={ink} strokeWidth="3" /></g>); })}</g>); })()}
        {/* ghế tập tạ */}
        {(() => { const bx = wide ? 560 : 300, by = fY - 60; return (<g><rect x={bx} y={by} width="220" height="26" rx="10" fill="#e2483a" stroke={ink} strokeWidth="4" /><rect x={bx + 20} y={by + 26} width="16" height="60" fill="#556" /><rect x={bx + 184} y={by + 26} width="16" height="60" fill="#556" /><rect x={bx - 30} y={by - 30} width="60" height="24" rx="8" fill="#c23" stroke={ink} strokeWidth="4" transform={`rotate(-24 ${bx} ${by})`} /></g>); })()}
        {/* cờ Mỹ */}
        <g transform={`translate(${wide ? 70 : 40} ${fY - 320}) rotate(${-6 + Math.sin(time * 1.2) * 3})`}><rect x="0" y="0" width="90" height="60" fill="#b22234" /><rect x="0" y="0" width="40" height="32" fill="#3c3b6e" /></g>
      </svg>);
  }

  // room / clean / unknown -> phòng VẼ đầy đủ (không bao giờ trống)
  {
    const W = wide ? 1920 : 1080, H = wide ? 1080 : 1920, fY = floorPct * H, ink = "#2b3340";
    const wa = T.wall?.[0] || "#eef2f8", wb = T.wall?.[1] || "#dde5ef", ac = T.accent || "#3E7BFA";
    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, width, height }}>
        <defs><linearGradient id="rmw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={wa} /><stop offset="1" stopColor={wb} /></linearGradient>
          <linearGradient id="rmsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={dark ? "#22314f" : "#bfe0ff"} /><stop offset="1" stopColor={dark ? "#0e1a2e" : "#eaf6ff"} /></linearGradient></defs>
        <rect x="0" y="0" width={W} height={fY} fill="url(#rmw)" />
        <rect x="0" y="0" width={W} height="44" fill={dark ? "#1a2438" : "#00000010"} />
        {/* đèn thả trần */}
        <rect x={W * 0.5 - 3} y="44" width="6" height="56" fill="#8a97a6" /><path d={`M ${W * 0.5 - 46} 112 Q ${W * 0.5} 90 ${W * 0.5 + 46} 112 L ${W * 0.5 + 32} 146 Q ${W * 0.5} 132 ${W * 0.5 - 32} 146 Z`} fill="#3a4658" /><ellipse cx={W * 0.5} cy="146" rx="36" ry="9" fill="#ffe9a8" />
        {/* cửa sổ + trời */}
        {(() => { const wx = wide ? 1280 : 620, wy = 170, ww = 380, wh = 280; return (<g><rect x={wx - 14} y={wy - 14} width={ww + 28} height={wh + 28} rx="12" fill="#f4f7fb" stroke={ink} strokeWidth="5" /><clipPath id="rmwin"><rect x={wx} y={wy} width={ww} height={wh} /></clipPath><g clipPath="url(#rmwin)"><rect x={wx} y={wy} width={ww} height={wh} fill="url(#rmsky)" /><circle cx={wx + 70} cy={wy + 70} r="30" fill={dark ? "#e6eef8" : "#ffe08a"} /><ellipse cx={wx + ww - 90} cy={wy + 90} rx="60" ry="24" fill="#fff" opacity=".85" /></g><rect x={wx + ww / 2 - 4} y={wy} width="8" height={wh} fill="#f4f7fb" /><rect x={wx} y={wy + wh / 2 - 4} width={ww} height="8" fill="#f4f7fb" /></g>); })()}
        {/* bộ 3 khung tranh */}
        {[0, 1, 2].map((i) => { const px3 = (wide ? 150 : 80) + i * 120, py = 180 + (i % 2) * 24; return (<g key={i}><rect x={px3} y={py} width="96" height="76" rx="6" fill="#fff" stroke={ink} strokeWidth="4" /><rect x={px3 + 10} y={py + 10} width="76" height="56" fill={["#cdeafe", "#ffe1c4", "#d8f0d0"][i]} /><circle cx={px3 + 30} cy={py + 30} r="10" fill={ac} /><path d={`M ${px3 + 10} ${py + 66} L ${px3 + 40} ${py + 34} L ${px3 + 62} ${py + 50} L ${px3 + 86} ${py + 24} L ${px3 + 86} ${py + 66} Z`} fill="#79b36b" /></g>); })}
        {/* kệ sách */}
        {(() => { const sx = wide ? 470 : 300, sy = 300; return (<g><rect x={sx} y={sy + 90} width="200" height="14" fill="#9a7a5a" />{[0, 1, 2, 3, 4, 5].map((i) => <rect key={i} x={sx + 10 + i * 30} y={sy + 40 + (i % 2) * 8} width="22" height={50 - (i % 2) * 8} fill={["#e2483a", "#3E7BFA", "#F5B301", "#2FA84F", "#7C5CFF", "#e07a52"][i]} stroke={ink} strokeWidth="2" />)}</g>); })()}
        {/* sàn + thảm */}
        <rect x="0" y={fY} width={W} height={H - fY} fill={T.floor || (dark ? "#141d2e" : "#c9b593")} /><rect x="0" y={fY} width={W} height="6" fill="#0003" />
        <ellipse cx={W * 0.5} cy={fY + (H - fY) * 0.55} rx={W * 0.32} ry={(H - fY) * 0.32} fill={ac} opacity=".18" />
        {/* cây trong chậu */}
        {(() => { const px2 = wide ? 1660 : 900, py = fY - 20; return (<g><path d={`M ${px2 - 26} ${py} L ${px2 + 26} ${py} L ${px2 + 18} ${py + 74} L ${px2 - 18} ${py + 74} Z`} fill="#c96f3a" stroke={ink} strokeWidth="4" />{[[-28, -66, -18], [28, -66, 18], [0, -96, 0]].map(([dxL, dyL, r], i) => <ellipse key={i} cx={px2 + (dxL as number) * 0.6} cy={py + (dyL as number)} rx="26" ry="42" fill={i === 2 ? "#4e9a4e" : "#5cb85c"} stroke={ink} strokeWidth="4" transform={`rotate(${r} ${px2} ${py})`} />)}</g>); })()}
        {/* bàn thấp */}
        {(() => { const tx = wide ? 150 : 70, ty = fY - 70; return (<g><rect x={tx} y={ty} width="240" height="18" rx="6" fill="#8a5a3a" stroke={ink} strokeWidth="4" /><rect x={tx + 16} y={ty + 18} width="14" height="56" fill="#7a4f30" /><rect x={tx + 210} y={ty + 18} width="14" height="56" fill="#7a4f30" /><rect x={tx + 40} y={ty - 30} width="40" height="30" rx="4" fill={ac} /></g>); })()}
      </svg>);
  }
};
