import { AbsoluteFill, Sequence, Audio, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { Karaoke } from "./Karaoke";
import { Bookend } from "./Bookend";
import React from "react";

// KÊNH #6 SWARM — trực quan hoá MẬT ĐỘ/SỐ LƯỢNG: hàng trăm hạt bay từ mép màn hình vào, hội tụ thành 1 silhouette
// (stadium/city/person/circle/grid) + số đếm lớn chạy lên. Motif riêng: "particle swarm fill", KHÔNG canvas/WebGL —
// mọi hạt là <div> absolute, vị trí tính DETERMINISTIC mỗi frame (seeded hash, không Math.random -> không flicker).

type Word = { t: number; d: number; w: string };
export type SwarmShape = "stadium" | "city" | "person" | "circle" | "grid";
export type SwarmItem = { label: string; count: number; countDisp?: string; shape: SwarmShape; emoji?: string; vo?: string; dur?: number };
export type SwarmProps = {
  title?: string; handle?: string; color?: string; accent?: string;
  items: SwarmItem[]; introSec?: number; itemSec?: number; outroSec?: number;
  audio?: string; music?: string; subs?: Word[]; sfx?: boolean;
};

const FPS = 30;
const idur = (it: SwarmItem, s: number) => (it.dur && it.dur > 0 ? it.dur : s);

// ---- seeded pseudo-random (deterministic, KHÔNG Math.random -> không nhấp nháy giữa các frame) ----
const hash01 = (n: number) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const GOLDEN = 2.399963229728653; // golden angle (rad) -> phân bố hạt đều kiểu hoa hướng dương, không cần random cho target

const CONVERGE_F = 42;   // ~1.4s: hạt bay từ mép vào, có swirl/jitter rồi settle (spring)
const DISPERSE_F = 24;   // ~0.8s: hạt cũ tan ra/mờ dần, chồng lấp vào đầu item kế tiếp

export const calcSwarm = ({ props }: any) => {
  const its: SwarmItem[] = props.items || [];
  const isec = props.introSec ?? 1.6, isc = props.itemSec ?? 2.7, tail = props.outroSec ?? 1.5;
  const total = its.reduce((a, it) => a + idur(it, isc), 0);
  return { durationInFrames: Math.round((isec + total + tail) * FPS), fps: FPS, width: 1080, height: 1920 };
};

// số hạt hiển thị: KHÔNG 1-hạt-1-đơn-vị (quá chậm/nặng) -> map log(count) vào dải 150-380 hạt, đủ "đông" mà vẫn mượt
const particleCount = (count: number) => {
  const n = Math.round(180 + Math.log10(Math.max(10, count)) * 40);
  return Math.max(150, Math.min(380, n));
};

// ---- target silhouette: trả toạ độ (dx,dy) LỆCH so với tâm (cx,cy) cho hạt thứ j / tổng N ----
function targetOffset(shape: SwarmShape, j: number, N: number, seed: number): { dx: number; dy: number } {
  if (shape === "grid") {
    const cols = Math.ceil(Math.sqrt(N * 0.72));
    const rows = Math.ceil(N / cols);
    const S = 620; // cạnh vùng lưới
    const col = j % cols, row = Math.floor(j / cols);
    const jx = (hash01(seed + 4.1) - 0.5) * (S / cols) * 0.18;
    const jy = (hash01(seed + 8.3) - 0.5) * (S / rows) * 0.18;
    return { dx: -S / 2 + (col + 0.5) * (S / cols) + jx, dy: -S / 2 + (row + 0.5) * (S / rows) + jy };
  }
  if (shape === "stadium") {
    // vành oval (đường viền sân vận động) — hạt rải đều theo chu vi, dày nhẹ theo bán kính
    const t = j * GOLDEN;
    const Rx = 330, Ry = 190;
    const thick = 1 + (hash01(seed + 1.7) - 0.5) * 0.22;
    return { dx: Math.cos(t) * Rx * thick, dy: Math.sin(t) * Ry * thick };
  }
  if (shape === "person") {
    // silhouette người: 3 khối (đầu / thân / chân) — hạt chia theo tỉ lệ diện tích, mỗi khối tự lấp kiểu xoắn ốc vàng
    const pHead = 0.12, pTorso = 0.5; // phần còn lại (0.38) là chân
    const frac = j / N;
    if (frac < pHead) {
      const jj = j, nn = Math.max(1, Math.round(N * pHead));
      const t = jj * GOLDEN, r = 78 * Math.sqrt(jj / nn);
      return { dx: Math.cos(t) * r, dy: -300 + Math.sin(t) * r };
    }
    if (frac < pHead + pTorso) {
      const jj = j - Math.round(N * pHead), nn = Math.max(1, Math.round(N * pTorso));
      const t = jj * GOLDEN, r = Math.sqrt(jj / nn);
      return { dx: Math.cos(t) * 170 * r, dy: -140 + Math.sin(t) * 230 * r };
    }
    const jj = j - Math.round(N * (pHead + pTorso)), nn = Math.max(1, N - Math.round(N * (pHead + pTorso)));
    const t = jj * GOLDEN, r = Math.sqrt(jj / nn);
    const side = jj % 2 === 0 ? -1 : 1;
    return { dx: side * 60 + Math.cos(t) * 110 * r, dy: 200 + Math.sin(t) * 230 * r };
  }
  // "circle" (mặc định/fallback đáng tin cậy) — lấp đầy hình tròn kiểu hoa hướng dương, đều & đẹp mắt
  const t = j * GOLDEN;
  const R = 330 * Math.sqrt(j / N);
  return { dx: Math.cos(t) * R, dy: Math.sin(t) * R };
}

const Particle: React.FC<{
  f: number; fps: number; startF: number; itemDur: number; seed: number;
  target: { dx: number; dy: number }; cx: number; cy: number; accent: string; emoji?: string; isOrbiter: boolean;
}> = ({ f, fps, startF, itemDur, seed, target, cx, cy, accent, emoji, isOrbiter }) => {
  const lf = f - startF; // frame cục bộ so với lúc item này bắt đầu
  const endWindow = itemDur + DISPERSE_F;
  if (lf < 0 || lf > endWindow) return null;

  // điểm xuất phát: ngoài mép màn hình, góc/bán kính theo seed (deterministic)
  const ang = hash01(seed) * Math.PI * 2;
  const rad = 1250 + hash01(seed + 2.2) * 500;
  const sx = Math.cos(ang) * rad, sy = Math.sin(ang) * rad;

  const conv = spring({ frame: lf, fps, config: { damping: 13, stiffness: 90, mass: 0.7 }, durationInFrames: CONVERGE_F });
  const convC = Math.min(1.08, conv); // cho phép overshoot nhẹ (nảy vào vị trí) nhưng chặn trần

  // swirl/jitter trong lúc bay -> giảm dần về 0 khi đã settle, tạo cảm giác "vật lý" chứ không bay thẳng cứng
  const decay = Math.max(0, 1 - lf / CONVERGE_F);
  const swirlX = Math.sin(lf * 0.35 + seed * 6.28) * 60 * decay;
  const swirlY = Math.cos(lf * 0.31 + seed * 4.71) * 60 * decay;

  let dx = sx + (target.dx - sx) * convC + swirlX;
  let dy = sy + (target.dy - sy) * convC + swirlY;

  // sau khi settle: vài hạt "orbiter" tiếp tục lượn nhẹ quanh vị trí cho có sự sống
  if (lf >= CONVERGE_F && isOrbiter) {
    const op = lf - CONVERGE_F;
    dx += Math.sin(op * 0.09 + seed * 9.1) * 14;
    dy += Math.cos(op * 0.09 + seed * 7.4) * 14;
  }

  // pha tan rã: khi lf vượt itemDur (đầu item KẾ TIẾP đã bắt đầu) -> hạt cũ bay ra ngoài & mờ dần, tạo crossfade
  let opacity = interpolate(lf, [0, 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (lf > itemDur) {
    const dp = interpolate(lf, [itemDur, endWindow], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    const outAng = hash01(seed + 5.5) * Math.PI * 2;
    dx += Math.cos(outAng) * 260 * dp;
    dy += Math.sin(outAng) * 260 * dp;
    opacity = opacity * (1 - dp);
  }

  const scale = interpolate(lf, [0, 10], [0.2, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const x = cx + dx, y = cy + dy;

  if (emoji) {
    return (
      <div style={{ position: "absolute", left: x, top: y, transform: `translate(-50%,-50%) scale(${scale})`, opacity, fontSize: 30, lineHeight: 1 }}>{emoji}</div>
    );
  }
  const size = 12 + hash01(seed + 9.9) * 6;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: size, height: size, borderRadius: "50%",
      transform: `translate(-50%,-50%) scale(${scale})`, opacity, background: accent,
      boxShadow: `0 0 ${size * 1.4}px ${accent}` }} />
  );
};

export const SwarmShort: React.FC<SwarmProps> = (props) => {
  const { title = "HOW MANY, REALLY?", handle = "@swarmusa", color = "#0D9488", accent = "#0D9488",
    items = [], introSec = 1.6, itemSec = 2.7, outroSec = 1.5, audio, music, sfx = true , subs = [] } = props;
  const f = useCurrentFrame(); const { fps, width: W, height: H } = useVideoConfig();

  const introF = Math.round(introSec * fps);
  const starts: number[] = []; let acc = introF;
  const durs: number[] = [];
  for (const it of items) { const d = Math.round(idur(it, itemSec) * fps); starts.push(acc); durs.push(d); acc += d; }
  const introP = spring({ frame: f, fps, config: { damping: 12, stiffness: 140 } });

  const CX = W / 2, CY = 900; // tâm sân khấu hạt (chừa chỗ tiêu đề trên, số/label dưới)

  return (
    <AbsoluteFill style={{ background: "radial-gradient(120% 90% at 50% 8%, #0f2a26 0%, #0a1614 55%, #050908 100%)", fontFamily: "'Poppins',Arial" }}>
      {/* TIÊU ĐỀ */}
      <div style={{ position: "absolute", top: 90, left: 0, right: 0, textAlign: "center", padding: "0 50px" }}>
        <div style={{ display: "inline-block", background: color, color: "#04120f", fontWeight: 900, fontSize: 30, letterSpacing: 2, padding: "8px 22px", borderRadius: 12 }}>🐝 SWARM</div>
        {/* Tiêu đề lúc mở đầu do Bookend vẽ. Header ẩn đi trong quãng đó, nếu không sẽ có hai bản tiêu đề chồng nhau (lỗi 25/8). */}
        <div style={{ display: f < introF ? "none" : undefined, color: "#fff", fontWeight: 900, fontSize: 66, lineHeight: 1.02, marginTop: 18, textShadow: "0 4px 24px #000c", textWrap: "balance" as any }}>{title}</div>
      </div>

      {/* SÂN KHẤU HẠT — mỗi item render trong cửa sổ [start, start+dur+DISPERSE] để tan/hội tụ chồng lấp mượt */}
      {items.map((it, i) => {
        const N = particleCount(it.count);
        const startF = starts[i], dur = durs[i];
        if (f < startF - 2 || f > startF + dur + DISPERSE_F + 2) return null;
        const parts = [] as React.ReactNode[];
        for (let j = 0; j < N; j++) {
          const seed = i * 977 + j * 3.17;
          const target = targetOffset(it.shape, j, N, seed);
          const isOrbiter = j % 11 === 0; // 1/11 hạt tiếp tục lượn nhẹ sau khi settle -> có "sự sống"
          parts.push(
            <Particle key={j} f={f} fps={fps} startF={startF} itemDur={dur} seed={seed} target={target}
              cx={CX} cy={CY} accent={accent} emoji={it.emoji} isOrbiter={isOrbiter} />
          );
        }
        // NHÃN + SỐ ĐẾM LÊN — chỉ hiện trong khoảng sống của item này (không kéo dài sang pha tan)
        const lf = f - startF;
        const show = lf >= 0 && lf <= dur + 6;
        const labelP = spring({ frame: lf, fps, config: { damping: 14, stiffness: 120 } });
        const countP = interpolate(lf, [8, CONVERGE_F + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const liveCount = Math.round(it.count * countP);
        const countText = countP >= 0.999 ? (it.countDisp || it.count.toLocaleString()) : liveCount.toLocaleString();
        return (
          <React.Fragment key={i}>
            {parts}
            {show ? (
              <div style={{ position: "absolute", left: 0, right: 0, top: CY + 430, textAlign: "center", opacity: labelP,
                transform: `translateY(${(1 - labelP) * 24}px)`, padding: "0 60px" }}>
                <div style={{ color: "#cdeee6", fontWeight: 700, fontSize: 34, textWrap: "balance" as any }}>{it.label}</div>
                <div style={{ display: "inline-block", marginTop: 14, background: accent, color: "#04120f", fontWeight: 900,
                  fontSize: 64, padding: "12px 34px", borderRadius: 20, letterSpacing: 0.5, boxShadow: `0 0 40px ${accent}88` }}>{countText}</div>
              </div>
            ) : null}
          </React.Fragment>
        );
      })}

      {/* INTRO overlay */}
      {f < introF ? (
        <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 42%, #0D948833, #050908 70%)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", paddingBottom: 620 }}>
          <div style={{ fontSize: 140, transform: `scale(${introP})` }}>🐝</div>
        </AbsoluteFill>
      ) : null}

      {/* SFX: whoosh lúc bắt đầu hội tụ, ding lúc settle */}
      {sfx ? items.map((it, i) => (
        <React.Fragment key={"sfx" + i}>
          <Sequence from={starts[i]} durationInFrames={10}><Audio src={staticFile("sfx/whoosh.mp3")} volume={0.4} /></Sequence>
          <Sequence from={starts[i] + CONVERGE_F} durationInFrames={20}><Audio src={staticFile("sfx/ding.mp3")} volume={0.3} /></Sequence>
        </React.Fragment>
      )) : null}

      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
      <Karaoke subs={subs} accent={accent} />
      <Bookend title={title} handle={handle} accent={accent} color={color}
               introSec={introSec} outroSec={outroSec} />
    </AbsoluteFill>
  );
};
