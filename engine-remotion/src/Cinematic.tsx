import React from "react";
import { AbsoluteFill, Audio, Sequence, OffthreadVideo, Img, staticFile, interpolate, useCurrentFrame, useVideoConfig, spring } from "remotion";

// 🌌 CINEMATIC comp (BEYOND) — nền stock 4K (hoặc cosmic fallback) + Ken Burns + DATA-HUD chồng lên + color grade + kinetic caption.
// Schema scene: { type, clip?, audio, dur, nar, amp?, hud?, title? }
//   type: talk | chapter | payoff
//   clip: tên file video trong public/<slug>/clips/  (ko có -> nền cosmic gradient + sao)
//   hud (data-HUD, tuỳ chọn): { kind:"timeline"|"scale"|"counter"|"countdown", value?, from?, to?, unit?, label?, marks?:string[] }
type HUD = { kind: string; value?: number; from?: number; to?: number; unit?: string; label?: string; marks?: string[] };
type Sub = { t: string; s: number; d: number };
type Scene = { type: string; clip?: string; clip2?: string; clips?: string[]; fx?: string; audio: string; dur: number; nar: string; amp?: number[]; hud?: HUD; title?: string; num?: string; subs?: Sub[]; hook?: { stat?: string; label?: string; line?: string } };
export type CProps = { scenes: Scene[]; slug: string; handle?: string; accent?: string; accent2?: string; ink?: string; music?: string; mode?: "duel" | "file"; host?: string };
export const calcCinematic = ({ props }: { props: CProps }) => ({ durationInFrames: Math.max(1, props.scenes.reduce((a, s) => a + s.dur, 0)) });
const ci = (v: number, a: number, b: number, x: number, y: number) => interpolate(v, [a, b], [x, y], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
// 1 ảnh hỏng/thiếu KHÔNG được giết cả video: <Img> mặc định CHỜ VÔ HẠN ảnh không nạp được ->
// CPU 0% -> watchdog giết sau 6' (sự cố 21/8: 7/7 lệnh render của UNSOLVED chết kiểu này, cả
// lane 0 video). RaceLong đã có SafeImg từ đầu — Cinematic thiếu. onError -> đổi sang ảnh nền
// dự phòng, render đi tiếp.
const FB_IMG = staticFile("img/_fallback.jpg");
const SafeImg: React.FC<any> = ({ src, ...rest }) => {
  const [s, setS] = React.useState(src);
  React.useEffect(() => { setS(src); }, [src]);
  return <Img src={s} onError={() => { if (s !== FB_IMG) setS(FB_IMG); }} {...rest} />;
};
const WEAK = new Set(["a", "an", "the", "and", "but", "or", "to", "of", "in", "on", "for", "with", "is", "are", "was", "were", "that", "it", "its", "at", "as", "by", "so", "if"]);

const W = (s: string): number => (s.toLowerCase().match(/[aeiouy]+/g) || []).length || 1; // ước lượng âm tiết
const GW = (g: string[]): number => g.reduce((a, w) => a + W(w), 0);
const chunkWords = (ws: string[]): string[][] => {
  const ch: string[][] = []; let i = 0;
  while (i < ws.length) {
    let end = Math.min(i + 6, ws.length); // chunk dài hơn -> ít chuyển dòng -> mượt, đỡ giật
    if (end < ws.length && end - i > 1 && WEAK.has(ws[end - 1].toLowerCase().replace(/[.,!?;:]$/, ""))) end--;
    ch.push(ws.slice(i, end)); i = end;
  }
  return ch;
};
// Caption karaoke: nếu có subs (mốc CÂU từ edge-tts) -> neo đúng lúc voice nói (khớp tiếng). Không có -> chia đều cả cảnh.
const Caption: React.FC<{ nar: string; l: number; d: number; accent: string; subs?: Sub[]; mode?: "duel" | "file" }> = ({ nar, l, d, accent, subs, mode }) => {
  const lines: { words: string[]; s: number; e: number }[] = [];
  if (subs && subs.length) {
    for (const sb of subs) {
      const groups = chunkWords(sb.t.split(/\s+/).filter(Boolean));
      const totC = groups.reduce((a, g) => a + GW(g), 0) || 1; let t = sb.s;
      for (const g of groups) { const gd = sb.d * (GW(g) / totC); lines.push({ words: g, s: t, e: t + gd }); t += gd; }
    }
  } else {
    const groups = chunkWords(nar.split(/\s+/)); const aF = d - 10;
    const totC = groups.reduce((a, g) => a + GW(g), 0) || 1; let t = 0;
    for (const g of groups) { const gd = aF * (GW(g) / totC); lines.push({ words: g, s: t, e: t + gd }); t += gd; }
  }
  if (!lines.length) return null;
  let cur = lines[0];
  for (const ln of lines) { if (l >= ln.s && l < ln.e) { cur = ln; break; } if (l >= ln.e) cur = ln; }
  const cd = Math.max(1, cur.e - cur.s); const wl = cur.words.reduce((a, x) => a + W(x), 0) || 1;
  let wt = cur.s, active = 0;
  for (let j = 0; j < cur.words.length; j++) { const wd = cd * (W(cur.words[j]) / wl); if (l >= wt && l < wt + wd) { active = j; break; } wt += wd; if (l >= wt) active = j; }
  const lineOp = Math.min(1, Math.max(0, (l - cur.s) / 5)); // fade-in mỗi dòng -> mượt, hết cắt cứng
  const { width, height } = useVideoConfig(); const port = height > width; // dọc (short) vs ngang (long)
  const fs = port ? 58 : 64; const bottom = port ? 520 : 120; const pad = port ? "0 70px" : "0 140px"; // dọc: nâng caption khỏi vùng UI Shorts
  if (mode === "file") {
    // Kiểu MÁY ĐÁNH CHỮ: gõ từng ký tự tới đúng frame hiện tại (không highlight từ theo giọng — hợp gu hồ sơ/giấy tờ).
    const full = cur.words.join(" ");
    const typedFrac = Math.min(1, Math.max(0, (l - cur.s) / cd));
    const shown = full.slice(0, Math.round(full.length * typedFrac));
    return (
      <div style={{ position: "absolute", left: 0, right: 0, bottom, textAlign: "center", padding: pad, opacity: lineOp }}>
        <span style={{ fontSize: fs * 0.72, fontWeight: 700, color: "#F3EEE3", fontFamily: "'Courier New',monospace", letterSpacing: 1, textShadow: "0 3px 20px rgba(0,0,0,0.9)", background: "#00000066", padding: "10px 22px", borderRadius: 4 }}>{shown}<span style={{ opacity: Math.floor(l / 8) % 2 ? 1 : 0, color: accent }}>▌</span></span>
      </div>
    );
  }
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom, textAlign: "center", padding: pad, opacity: lineOp,
                  zIndex: 30, textShadow: "0 2px 18px rgba(0,0,0,.95)" }}>
      {cur.words.map((x, i) => { const on = i === active; return <span key={i} style={{ fontSize: fs, fontWeight: 900, color: on ? accent : "#EAF8FF", margin: "0 9px", display: "inline-block", transform: on ? "scale(1.09)" : "scale(1)", textShadow: on ? `0 3px 26px rgba(0,0,0,0.9), 0 0 22px ${accent}88` : "0 3px 26px rgba(0,0,0,0.9)" }}>{x}</span>; })}
    </div>
  );
};

// ─── DATA-HUD (moat) ───
const HudView: React.FC<{ hud: HUD; l: number; d: number; accent: string; accent2: string }> = ({ hud, l, d, accent, accent2 }) => {
  // cảnh rất ngắn (d*0.6 < 8) -> khoảng [8, d*0.6] bị đảo ngược -> Remotion interpolate() throw "must be strictly increasing".
  // ép mốc sau luôn > 8 để khoảng luôn tăng dần, kể cả cảnh HUD chỉ dài vài frame.
  const p = ci(l, 8, Math.max(9, Math.min(d * 0.6, 50)), 0, 1);
  const { width, height } = useVideoConfig(); const port = height > width; // dọc (short) vs ngang (long)
  if (hud.kind === "counter" || hud.kind === "countdown") {
    // Đếm LÊN tới SỐ Ý NGHĨA rồi GIỮ (năm/giá trị). KHÔNG tụt về 0 (trước đây countdown->0 hiện "MILAN FALLS 0" vô nghĩa).
    const from = hud.from ?? 0;
    const to = hud.to ?? (hud.value || 0);
    const cur = from + (to - from) * p; const dec = Math.abs(to) < 100 && Math.round(to) !== to;
    const numStr = dec ? cur.toFixed(1) : Math.round(cur).toLocaleString();
    // AUTO-FIT (by construction, KHÔNG BAO GIỜ TRÀN): co số vừa bề ngang với lề an toàn + ước lượng bảo thủ.
    const base = port ? 128 : 236; const maxW = width - (port ? 150 : 260);
    const est = (numStr.length + (hud.unit || "").length * 0.62) * base * 0.64; // 0.64em/ký tự = bảo thủ (rộng hơn thực)
    const fs = est > maxW ? Math.floor(base * maxW / est) : base;
    const pop = spring({ frame: l, fps: 30, config: { damping: 13, stiffness: 110 } });
    const glow = 40 + 30 * Math.max(0, 1 - l / 20);
    return (
      <div style={{ position: "absolute", left: 0, right: 0, top: port ? 300 : 250, textAlign: "center", padding: "0 40px", opacity: Math.min(1, pop * 1.2), transform: `scale(${0.82 + 0.18 * pop}) translateY(${(1 - pop) * 24}px)` }}>
        <div style={{ fontSize: fs, fontWeight: 900, color: accent, textShadow: `0 0 ${glow}px ${accent}99`, lineHeight: 1, whiteSpace: "nowrap" }}>{numStr}<span style={{ fontSize: fs * 0.5 }}>{hud.unit || ""}</span></div>
        {hud.label && <div style={{ fontSize: port ? 40 : 46, fontWeight: 700, color: "#9FC4E0", marginTop: 12, letterSpacing: 2 }}>{hud.label.toUpperCase()}</div>}
      </div>
    );
  }
  if (hud.kind === "scale") { // thanh log-scale phát sáng
    return (
      <div style={{ position: "absolute", left: port ? 80 : 160, right: port ? 80 : 160, top: port ? 420 : 360 }}>
        <div style={{ height: 16, borderRadius: 10, background: "#ffffff18", overflow: "hidden" }}>
          <div style={{ width: `${p * 100}%`, height: "100%", background: `linear-gradient(90deg,${accent},${accent2})`, boxShadow: `0 0 22px ${accent}` }} />
        </div>
        {hud.label && <div style={{ fontSize: port ? 42 : 48, fontWeight: 900, color: "#EAF8FF", marginTop: 20, textAlign: "center", textShadow: "0 2px 20px #000" }}>{hud.label}</div>}
      </div>
    );
  }
  // timeline: đường ngang + node chạy + mốc
  const marks = hud.marks && hud.marks.length ? hud.marks : ["", "", "", "", ""]; const n = marks.length;
  return (
    <div style={{ position: "absolute", left: port ? 55 : 140, right: port ? 55 : 140, top: port ? 440 : 380 }}>
      <div style={{ position: "relative", height: 6, background: `${accent}55` }}>
        <div style={{ position: "absolute", left: 0, top: 0, height: 6, width: `${p * 100}%`, background: accent, boxShadow: `0 0 18px ${accent}` }} />
        {marks.map((m, i) => { const x = (i / (n - 1)) * 100; const passed = p >= i / (n - 1) - 0.02; return (
          <div key={i} style={{ position: "absolute", left: `${x}%`, top: -7, transform: "translateX(-50%)", textAlign: "center" }}>
            <div style={{ width: passed ? 22 : 14, height: passed ? 22 : 14, borderRadius: "50%", background: passed ? accent2 : `${accent}`, boxShadow: passed ? `0 0 16px ${accent2}` : "none", margin: "0 auto" }} />
            <div style={{ fontSize: port ? 22 : 30, fontWeight: 800, color: passed ? "#EAF8FF" : "#5f7590", marginTop: 14, whiteSpace: "nowrap" }}>{m}</div>
          </div>); })}
      </div>
    </div>
  );
};

const CosmicBg: React.FC<{ f: number }> = ({ f }) => (
  <AbsoluteFill style={{ background: "radial-gradient(70% 60% at 50% 38%, #0C1A33 0%, #060B18 55%, #02030A 100%)" }}>
    <svg width="100%" height="100%">{Array.from({ length: 120 }).map((_, i) => <circle key={i} cx={(i * 733) % 1920} cy={(i * 419) % 1080} r={i % 5 === 0 ? 2.4 : 1.2} fill="#fff" opacity={0.12 + (i % 7) / 16} />)}</svg>
  </AbsoluteFill>
);

// NỀN CHỦ ĐỀ — LUÔN hiển thị, KHÔNG BAO GIỜ ĐEN. Clip đặt lên bằng blend 'screen':
// chỗ clip đen -> nền lộ ra (on-brand), chỗ clip sáng -> hiện clip. => không thể ra khung đen dù clip tối/thiếu/lỗi.
// Nền chủ đề ẤM/GIÀU (KHÔNG sao — sao làm giống "không gian rỗng", xấu cho tiểu sử). Vignette điện ảnh.
const ThemedBase: React.FC<{ accent: string; accent2: string; f: number }> = ({ accent, accent2 }) => (
  <AbsoluteFill style={{ background: `radial-gradient(95% 78% at 50% 42%, ${accent}33 0%, ${accent2}16 32%, #15161e 64%, #0a0b12 100%)` }}>
    <AbsoluteFill style={{ background: `radial-gradient(55% 45% at 26% 24%, ${accent2}20 0%, transparent 55%)`, mixBlendMode: "screen" }} />
    <AbsoluteFill style={{ boxShadow: "inset 0 0 340px 100px rgba(0,0,0,0.5)" }} />
  </AbsoluteFill>
);

// Hiệu ứng KHÔNG KHÍ động (free, render engine) — làm ảnh tĩnh "sống": tro/bụi/tàn lửa/tuyết/mưa.
const _R = (n: number, s: number) => { const v = Math.sin((n + 1) * s) * 43758.5453; return v - Math.floor(v); };
const FX: Record<string, { n: number; col: string; sMin: number; sMax: number; spd: number; sway: number; rise?: boolean; op: number; glow?: number; streak?: boolean }> = {
  ash:    { n: 70, col: "215,215,220", sMin: 2, sMax: 6, spd: 0.45, sway: 6, op: 0.5 },
  snow:   { n: 80, col: "255,255,255", sMin: 3, sMax: 8, spd: 0.32, sway: 8, op: 0.72 },
  dust:   { n: 55, col: "255,240,210", sMin: 1, sMax: 3, spd: 0.12, sway: 5, op: 0.35 },
  embers: { n: 45, col: "255,150,60",  sMin: 2, sMax: 5, spd: 0.5,  sway: 5, rise: true, op: 0.85, glow: 8 },
  rain:   { n: 90, col: "180,200,220", sMin: 1, sMax: 2, spd: 1.7,  sway: 1, op: 0.4, streak: true },
};
const FxLayer: React.FC<{ kind: string; l: number }> = ({ kind, l }) => {
  const c = FX[(kind || "").toLowerCase()]; if (!c) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {Array.from({ length: c.n }).map((_, i) => {
        const bx = _R(i, 12.9898) * 100;
        const sz = c.sMin + _R(i, 78.233) * (c.sMax - c.sMin);
        const sp = c.spd * (0.6 + _R(i, 4.11) * 0.9);
        const ph = _R(i, 27.61) * Math.PI * 2;
        const prog = ((i * 6.37 + l * sp) % 120) / 120;
        const y = c.rise ? (100 - prog * 120) : (prog * 120 - 10);
        const x = bx + Math.sin(l * 0.03 + ph) * c.sway;
        const op = c.op * (0.5 + _R(i, 9.7) * 0.5) * (c.rise ? 1 - prog : 1);
        return <div key={i} style={{ position: "absolute", left: `${x}%`, top: `${y}%`, width: sz, height: c.streak ? sz * 14 : sz, borderRadius: c.streak ? 1 : "50%", background: `rgba(${c.col},${op})`, filter: c.glow ? `drop-shadow(0 0 ${c.glow}px rgba(${c.col},0.9))` : "blur(0.3px)" }} />;
      })}
    </AbsoluteFill>
  );
};

const Scene1: React.FC<{ s: Scene; l: number; slug: string; accent: string; accent2: string; idx: number; mode?: "duel" | "file" }> = ({ s, l, slug, accent, accent2, idx, mode }) => {
  const f = useCurrentFrame();
  // CẮT NHANH: cảnh có clip2 -> nửa đầu clip, nửa sau clip2 (đổi hình giữa cảnh, nhịp dồn, hết đứng hình)
  // CẮT NHANH: s.clips = nhiều ảnh cho MỘT cảnh -> chia đều thời lượng, ~2-3s đổi hình một lần.
  // (clip2 là bản cũ chỉ chia đôi; vẫn đỡ để props cũ không gãy.)
  const list: string[] = (s.clips && s.clips.length ? s.clips : (s.clip2 ? [s.clip!, s.clip2] : (s.clip ? [s.clip] : [])));
  const nSeg = Math.max(1, list.length);
  const segLen = Math.max(1, s.dur / nSeg);        // ép >=1: s.dur=0 (cảnh lỗi) -> interpolate() sẽ throw
  const segI = Math.min(nSeg - 1, Math.floor(l / segLen));
  const clip = list[segI];
  const cl = l - segI * segLen;                    // frame trong PHÂN ĐOẠN
  const cdur = Math.max(1, segLen);                // độ dài phân đoạn
  const seg = idx + segI;                          // đổi hướng Ken Burns giữa các phân đoạn
  const isImg = !!clip && /\.(jpg|jpeg|png|webp)$/i.test(clip);
  const amt = isImg ? 0.13 : 0.16; const base = isImg ? 1.06 : 1.11;
  const zoomIn = seg % 2 === 0;
  const kb = zoomIn ? base + ci(cl, 0, cdur, 0, amt) : base + amt - ci(cl, 0, cdur, 0, amt);
  const pdir = seg % 4 < 2 ? 1 : -1;
  const panX = isImg ? ci(cl, 0, cdur, -12 * pdir, 12 * pdir) : ci(cl, 0, cdur, -32 * pdir, 32 * pdir);
  const panY = isImg ? ci(cl, 0, cdur, -9 * pdir, 9 * pdir) : ci(cl, 0, cdur, -9 * pdir, 9 * pdir);
  const rot = isImg ? ci(cl, 0, cdur, -0.7 * pdir, 0.7 * pdir) : 0;
  const punch = 1 + 0.04 * (1 - ci(cl, 0, 7, 0, 1)); // "cắt punch" nhẹ đầu mỗi phân đoạn -> năng lượng
  if (s.type === "chapter") {
    const p = spring({ frame: l, fps: 30, config: { damping: 16 } });
    // NỀN: có ảnh thật -> dùng ảnh (Ken Burns nhẹ) + lớp phủ tối cho chữ nổi; không có -> CosmicBg như cũ.
    // Cảnh MỞ ĐẦU luôn là chapter, mà thumbnail lấy đúng khung mở đầu -> trước đây mọi video ra một
    // tấm CHỮ TRÊN NỀN ĐEN giống hệt nhau, không có footage nào. Đây là chỗ sửa gốc.
    return (<AbsoluteFill>
      {clip ? (<>
        <div key={clip} style={{ position: "absolute", inset: 0, transform: `scale(${kb * punch}) translate(${panX}px, ${panY}px)` }}>
          {isImg
            ? <SafeImg src={staticFile(`${slug}/clips/${clip}`)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center 32%" }} />
            : <OffthreadVideo src={staticFile(`${slug}/clips/${clip}`)} muted loop style={{ width: "100%", height: "100%", objectFit: "cover" }} />}
        </div>
        {/* Lớp phủ ĐỦ TỐI để chữ tiêu đề 120px luôn đọc được trên mọi ảnh (kể cả ảnh sáng/nhiều chi tiết) */}
        <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(3,6,16,0.74) 0%, rgba(3,6,16,0.58) 42%, rgba(3,6,16,0.88) 100%)" }} />
        <AbsoluteFill style={{ boxShadow: "inset 0 0 340px 120px rgba(0,0,0,0.55)" }} />
      </>) : <CosmicBg f={f} />}
      {(() => {
        // ĐA DẠNG BỐ CỤC: 4 kiểu mở đầu, chọn theo hash tiêu đề -> mỗi video một kiểu, nhưng ỔN ĐỊNH
        // (render lại ra y hệt). Trước đây mọi video dùng chung đúng 1 mô-típ (gạch ngang + chữ giữa)
        // nên xem liền mấy cái là thấy lặp.
        const t = (s.title || "").toUpperCase();
        let h = 0; for (let k = 0; k < t.length; k++) h = (h * 31 + t.charCodeAt(k)) >>> 0;
        const v = h % 4;
        const rule = (w: number, mx: string) => (
          <div style={{ width: w, height: 8, background: accent, borderRadius: 6, margin: mx, boxShadow: `0 0 24px ${accent}` }} />
        );
        const { width: _vw, height: _vh } = useVideoConfig();   // 23/8: thẻ chữ cần biết khổ dọc/ngang
        const title = (size: number, align: "center" | "left") => (
          <div style={{ fontSize: size, fontWeight: 900, color: "#EAF8FF", lineHeight: 1.04, textAlign: align, textShadow: `0 0 40px ${accent}66, 0 4px 24px rgba(0,0,0,.75)` }}>{t}</div>
        );
        // 23/8 (user gửi ảnh: "chữ sub đè lên thẻ số liệu"): thẻ chữ trước đây trải TOÀN khung
        // (inset 0) nên tâm của nó rơi trúng dải phụ đề. Nay chừa sẵn vùng phụ đề phía dưới:
        // dọc chừa 560px, ngang chừa 170px — hai lớp không còn cửa nào để chạm nhau.
        const capZone = _vh > _vw ? 560 : 170;      // _vw/_vh lấy ngay dưới đây, khối này không có `port`
        const wrap = (justify: string, align: string, pad: string, inner: React.ReactNode) => (
          <div style={{ position: "absolute", left: 0, right: 0, top: 0, bottom: capZone, display: "flex", alignItems: justify, justifyContent: "center", flexDirection: "column", padding: pad, opacity: p, transform: `scale(${0.94 + p * 0.06})` }}>
            <div style={{ width: "100%", textAlign: align as any }}>{inner}</div>
          </div>
        );
        if (v === 1)  // canh TRÁI, gạch dọc bên mép -> gu tin nhanh
          return wrap("center", "left", "0 110px", <>
            <div style={{ display: "flex", gap: 28 }}>
              <div style={{ width: 10, alignSelf: "stretch", background: accent, borderRadius: 6, boxShadow: `0 0 24px ${accent}` }} />
              {title(104, "left")}
            </div></>);
        if (v === 2)  // chữ dồn XUỐNG DƯỚI, gạch trên -> để lộ ảnh nền phía trên
          return wrap("flex-end", "left", "0 110px 190px", <>
            {rule(160, "0 0 34px")}
            {title(100, "left")}</>);
        if (v === 3)  // chữ dồn LÊN TRÊN, gạch dưới
          return wrap("flex-start", "left", "230px 110px 0", <>
            {title(100, "left")}
            {rule(160, "34px 0 0")}</>);
        return wrap("center", "center", "0 120px", <>   {/* v===0: kiểu giữa như cũ */}
          {rule(120, "0 auto 40px")}
          {title(116, "center")}</>);
      })()}
    </AbsoluteFill>);
  }
  return (
    <AbsoluteFill style={{ background: "#080910", isolation: "isolate" }}>
      <ThemedBase accent={accent} accent2={accent2} f={f} />
      {mode === "duel" && (
        // Nhuộm nửa trái/phải xen kẽ theo cảnh -> cảm giác 2 phe đối đầu xuyên suốt video (không cần script tách 2 số liệu/cảnh).
        <AbsoluteFill style={{ pointerEvents: "none" }}>
          <div style={{ position: "absolute", inset: 0, background: `linear-gradient(90deg, ${idx % 2 === 0 ? accent : accent2}22 0%, transparent 45%, transparent 55%, ${idx % 2 === 0 ? accent2 : accent}22 100%)` }} />
          <div style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: 3, background: `linear-gradient(180deg, transparent, ${idx % 2 === 0 ? accent : accent2}, transparent)`, boxShadow: `0 0 24px ${idx % 2 === 0 ? accent : accent2}` }} />
        </AbsoluteFill>
      )}
      {mode === "file" && (
        // Giấy ố vàng + lưới sợi giấy nhẹ -> gu "hồ sơ giải mật" thay vì nền cosmic/cinematic thường.
        <AbsoluteFill style={{ background: "radial-gradient(120% 90% at 50% 30%, #2b2620cc 0%, #14120eee 60%, #0a0906 100%)", mixBlendMode: "multiply" }} />
      )}
      {clip && (
        <div key={clip} style={{ position: "absolute", inset: 0, mixBlendMode: "screen", transform: `scale(${kb * punch}) translate(${panX}px, ${panY}px) rotate(${rot}deg)`, filter: "brightness(1.28) contrast(1.1) saturate(1.14)" }}>
          {isImg
            ? <SafeImg src={staticFile(`${slug}/clips/${clip}`)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center 28%" }} />
            : <OffthreadVideo src={staticFile(`${slug}/clips/${clip}`)} muted loop style={{ width: "100%", height: "100%", objectFit: "cover" }} />}
        </div>
      )}
      {s.hook && (() => {
        // LỚP HOOK cảnh mở đầu (giống kênh 01/02/03): SỐ LIỆU TO + nhãn + câu hỏi mở, đè lên footage
        // thật. Vào video là hook ngay — KHÔNG thẻ intro chờ sẵn. Thumbnail lấy đúng khung này nên
        // ảnh bìa cũng thành một tấm hook có số liệu, không còn chữ trơn trên nền đen.
        const hk = s.hook as { stat?: string; label?: string; line?: string };
        const t = (hk.stat || "") + (hk.line || "");
        let h = 0; for (let k = 0; k < t.length; k++) h = (h * 31 + t.charCodeAt(k)) >>> 0;
        const v = h % 4;                                    // 4 bố cục -> không lặp một mô-típ
        // hiện nhanh (12fr) -> giữ ~2.5s -> mờ đi, nhường chỗ cho footage. Không giữ suốt cảnh:
        // số liệu to che hình cả 8 giây thì lại thành "tấm bảng chữ" đúng thứ cần tránh.
        const ein2 = Math.min(ci(l, 0, 12, 0, 1), ci(l, 78, 96, 1, 0));
        const pos: any = v === 0 ? { alignItems: "center", justifyContent: "center", textAlign: "center" }
          : v === 1 ? { alignItems: "flex-start", justifyContent: "center", textAlign: "left" }
          : v === 2 ? { alignItems: "flex-start", justifyContent: "flex-end", textAlign: "left" }
          : { alignItems: "flex-start", justifyContent: "flex-start", textAlign: "left" };
        const padV = v === 2 ? "0 100px 300px" : v === 3 ? "260px 100px 0" : "0 100px";
        return (<AbsoluteFill style={{ pointerEvents: "none" }}>
          {/* phủ tối vừa đủ: chữ hook luôn đọc được mà vẫn thấy rõ ảnh nền */}
          <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(3,6,16,.66) 0%, rgba(3,6,16,.34) 45%, rgba(3,6,16,.82) 100%)" }} />
          <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", padding: padV, opacity: ein2, transform: `translateY(${(1 - ein2) * 26}px)`, ...pos }}>
            {hk.stat ? <div style={{ fontSize: 210, fontWeight: 900, color: accent2, lineHeight: .94, letterSpacing: -4, textShadow: `0 0 60px ${accent2}55, 0 6px 30px rgba(0,0,0,.8)` }}>{hk.stat}</div> : null}
            {hk.label ? <div style={{ fontSize: 46, fontWeight: 800, color: "#EAF8FF", letterSpacing: 2, marginTop: 6, textShadow: "0 3px 18px rgba(0,0,0,.85)" }}>{hk.label.toUpperCase()}</div> : null}
            <div style={{ width: 140, height: 7, background: accent, borderRadius: 6, margin: v === 0 ? "26px auto" : "26px 0", boxShadow: `0 0 22px ${accent}` }} />
            {hk.line ? <div style={{ fontSize: 62, fontWeight: 900, color: "#EAF8FF", lineHeight: 1.1, textShadow: `0 0 34px ${accent}55, 0 4px 22px rgba(0,0,0,.85)` }}>{hk.line.toUpperCase()}</div> : null}
          </div>
        </AbsoluteFill>);
      })()}
      {/* grade nhẹ ở đáy cho caption (KHÔNG làm tối toàn khung — nền chủ đề đã lo phần không-đen) */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(4,10,26,0.0) 0%, rgba(2,3,10,0.04) 46%, rgba(2,3,10,0.58) 100%)" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 380px 110px rgba(0,0,0,0.45)" }} />
      {s.fx && <FxLayer kind={s.fx} l={l} />}
      {s.hud && <HudView hud={s.hud} l={l} d={s.dur} accent={accent} accent2={accent2} />}
      {mode === "file" && l < 18 && (
        // Thanh bôi đen "giải mật" kéo ra đầu mỗi cảnh -> đúng gu case-file, khác hẳn dissolve/push-in thường.
        <AbsoluteFill style={{ background: "#0a0a0a", transform: `translateY(${ci(l, 0, 18, 0, -100)}%)` }} />
      )}
    </AbsoluteFill>
  );
};

export const Cinematic: React.FC<CProps> = ({ scenes, slug, handle = "", accent = "#22D3EE", accent2 = "#F5B301", ink = "#EAF8FF", music, mode, host }) => {
  const f = useCurrentFrame(); const st: number[] = []; scenes.reduce((a, s, i) => (st[i] = a, a + s.dur), 0);
  let idx = 0; for (let k = 0; k < scenes.length; k++) if (f >= st[k]) idx = k; const s = scenes[idx], l = f - st[idx];
  // KHÔNG fade-về-đen giữa cảnh (comp render 1 cảnh/lúc -> fade sẽ chớp ĐEN mỗi chuyển cảnh).
  // Chuyển cảnh = push-in (scale) + flash trắng nhẹ. Chỉ fade tổng ở đầu/cuối CẢ video.
  const einRaw = ci(l, 0, 15, 0, 1); const ein = 1 - Math.pow(1 - einRaw, 3); // easeOutCubic
  const entryScale = 1 + 0.05 * (1 - ein);
  const total = st[scenes.length - 1] + scenes[scenes.length - 1].dur;
  // KHÔNG fade đen mở/đóng video (rule user): trước đây 14 frame đầu và 14 frame cuối fade từ/về ĐEN
  // -> mở video là nửa giây đen (mất hook ngay giây đầu, YouTube tính giữ chân rất gắt ở đoạn này) và
  // kết thúc cũng chìm vào đen. Giờ vào thẳng hình, kết thúc vẫn còn hình.
  const vidFade = 1;
  // CROSS-DISSOLVE chuyên nghiệp KHÔNG-ĐEN: đầu mỗi cảnh, cảnh TRƯỚC còn hiện phía dưới, cảnh MỚI mờ chồng lên.
  // 2 lớp đều có hình -> không bao giờ về đen. (cảnh trước chạy quá dur ~13fr, clip loop/ảnh tĩnh vẫn có nội dung)
  const X = 13; const inCross = idx > 0 && l < X; const prevIdx = idx - 1;
  const prevL = inCross ? f - st[prevIdx] : 0;
  // ĐA DẠNG chuyển cảnh (an toàn KHÔNG-ĐEN vì cảnh trước LUÔN full ở dưới lấp mọi khoảng hở):
  // xoay vòng 5 kiểu theo cảnh — dissolve / trượt phải / trượt trái / zoom-in / đẩy lên. Đều kèm mờ dần.
  const cp = inCross ? l / X : 1; const ecp = 1 - Math.pow(1 - cp, 3);   // easeOutCubic của tiến trình chuyển
  const tt = idx % 5; const curOpacity = inCross ? Math.min(1, cp * 1.15) : 1;
  let curTransform = `scale(${entryScale})`;
  if (inCross) {
    if (tt === 1) curTransform = `translateX(${(1 - ecp) * 10}%) scale(${entryScale})`;        // trượt từ phải
    else if (tt === 2) curTransform = `translateX(${-(1 - ecp) * 10}%) scale(${entryScale})`;   // trượt từ trái
    else if (tt === 3) curTransform = `scale(${(1.12 - 0.12 * ecp)})`;                          // zoom-in
    else if (tt === 4) curTransform = `translateY(${(1 - ecp) * 7}%) scale(${entryScale})`;     // đẩy lên
    // tt===0: dissolve thuần (scale push-in)
  }
  return (
    <AbsoluteFill style={{ background: "#02030A", fontFamily: "'Poppins',Arial", opacity: vidFade }}>
      {inCross && <AbsoluteFill><Scene1 s={scenes[prevIdx]} l={prevL} slug={slug} accent={accent} accent2={accent2} idx={prevIdx} mode={mode} /></AbsoluteFill>}
      <AbsoluteFill style={{ opacity: curOpacity, transform: curTransform }}><Scene1 s={s} l={l} slug={slug} accent={accent} accent2={accent2} idx={idx} mode={mode} /></AbsoluteFill>
      {/* LUÔN hiện caption (kể cả chapter -> voice đọc nar đều có sub); dùng subs (mốc câu) để khớp tiếng */}
      <Caption nar={s.nar} l={l} d={s.dur} accent={accent} subs={s.subs} mode={mode} />
      {host && (() => {
        // HOST nhất quán (Nano Banana, ảnh tham chiếu giữ nguyên nhân vật) — đứng góc dưới, hơi thở/lắc nhẹ theo spring, xuyên suốt video.
        const { width, height } = useVideoConfig(); const port = height > width;
        const bob = spring({ frame: f % 90, fps: 30, config: { damping: 100, stiffness: 40 } });
        const w = port ? 340 : 300;
        return (
          <div style={{ position: "absolute", left: port ? 20 : 40, bottom: port ? 560 : 40, width: w, transform: `translateY(${Math.sin(f / 22) * 6}px) scale(${0.98 + bob * 0.02})`, filter: "drop-shadow(0 14px 30px rgba(0,0,0,0.55))" }}>
            <SafeImg src={staticFile(host)} style={{ width: "100%", height: "auto" }} />
          </div>
        );
      })()}
      {/* (bỏ film grain feTurbulence — vẽ lại mỗi frame quá nặng, làm render chậm 3-4x; không đáng) */}
      {handle && <div style={{ position: "absolute", top: 40, right: 48, color: "#ffffffbb", fontSize: 30, fontWeight: 800 }}>{handle}</div>}
      {scenes.map((sc, j) => <Sequence key={j} from={st[j]} durationInFrames={sc.dur}><Audio src={staticFile(`${slug}/${sc.audio}`)} /></Sequence>)}
      {/* TIẾNG CHUYỂN CẢNH: whoosh ngắn 0.42s ở MỌI điểm cắt — cả chuyển cảnh lẫn đổi ảnh trong cảnh.
          Dùng CHUNG kho sfx với BarChartRace/RaceLong/SwarmShort (9 engine khác) -> nghe đồng bộ cả
          hệ. Âm lượng 0.4 đúng mức SwarmShort đặt cho whoosh mỗi nhịp (0.55-0.6 để dành cho cú mở
          màn), đủ nghe mà không lấn lời thoại. */}
      {(() => {
        const cuts: number[] = [];
        scenes.forEach((sc, j) => {
          const n = Math.max(1, (sc.clips && sc.clips.length) ? sc.clips.length : (sc.clip2 ? 2 : 1));
          const segLen = Math.max(1, sc.dur / n);
          for (let q = 0; q < n; q++) {
            const at = Math.round(st[j] + q * segLen);
            if (at > 0) cuts.push(at);
          }
        });
        return (<>
          {/* CÚ MỞ MÀN: whoosh mạnh hơn ngay giây đầu, giống cold-open của RaceLong -> vào là có lực */}
          <Sequence from={2} durationInFrames={18}><Audio src={staticFile("sfx/whoosh.mp3")} volume={0.55} /></Sequence>
          {cuts.map((at, q) => (
            <Sequence key={`sfx${q}`} from={at} durationInFrames={12}>
              <Audio src={staticFile("sfx/whoosh.mp3")} volume={0.4} />
            </Sequence>
          ))}
        </>);
      })()}
      {/* NHẠC NỀN (mới) — cực nhẹ (0.12 đỉnh) để KHÔNG đè lời thoại, fade-in/out mượt đầu-cuối, loop suốt video. */}
      {music && <Audio src={staticFile(music)} loop volume={Math.min(ci(f, 0, 30, 0, 1), ci(f, total - 40, total, 1, 0)) * 0.12} />}
    </AbsoluteFill>
  );
};
