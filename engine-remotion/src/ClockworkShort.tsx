import { AbsoluteFill, Sequence, Audio, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import React from "react";

// KÊNH CLOCKWORK — nén 1 khoảng thời gian khổng lồ vào 1 thanh timeline quét NHANH->CHẬM, dừng lại (zoom) đúng
// vào lát cắt "hero" gây sốc cuối cùng. Motif: thanh tiến trình ngang + mặt đồng hồ mờ trang trí phía sau.
type Word = { t: number; d: number; w: string };
export type Waypoint = { label: string; atPercent: number; vo?: string };
export type Hero = { label: string; atPercent: number; realValue: string; vo?: string };
export type ClockworkProps = {
  title?: string; handle?: string; color?: string; accent?: string;
  scaleLabel: string;
  waypoints: Waypoint[];
  hero: Hero;
  audio?: string; music?: string; subs?: Word[]; sfx?: boolean;
};

const FPS = 30;
// nhịp cố định (không expose props) — đủ để calc & component luôn khớp nhau
const INTRO_SEC = 1.5, WAYPOINT_SEC = 1.8, HERO_SEC = 3.0, OUTRO_SEC = 1.5;
const K = 4.5; // độ "khựng" của easing quét — càng lớn càng nhanh-đầu/chậm-cuối

export const calcClockwork = ({ props }: any) => {
  const wps: Waypoint[] = props.waypoints || [];
  const sweepSec = Math.max(2.5, wps.length * WAYPOINT_SEC);
  const total = INTRO_SEC + sweepSec + HERO_SEC + OUTRO_SEC;
  return { durationInFrames: Math.round(total * FPS), fps: FPS, width: 1080, height: 1920 };
};

// làm sáng màu hex (trộn với trắng theo tỉ lệ amt 0-1) — dùng cho gradient/glow phụ
const lighten = (hex: string, amt: number) => {
  const h = hex.replace("#", "");
  const n = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  const r = parseInt(n.slice(0, 2), 16), g = parseInt(n.slice(2, 4), 16), b = parseInt(n.slice(4, 6), 16);
  const mix = (c: number) => Math.round(c + (255 - c) * amt);
  return `rgb(${mix(r)},${mix(g)},${mix(b)})`;
};

const KaraokeCaption: React.FC<{ subs?: Word[] }> = ({ subs }) => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig(); const now = f / fps;
  if (!subs || !subs.length) return null;
  const cur = subs.filter((w) => now >= w.t - 0.05 && now < w.t + w.d + 0.05);
  if (!cur.length) return null;
  const idx = subs.indexOf(cur[0]); const from = Math.max(0, idx - 2); const win = subs.slice(from, from + 6);
  return (
    <div style={{ position: "absolute", bottom: 148, left: 0, right: 0, textAlign: "center", padding: "0 60px" }}>
      <div style={{ display: "inline", background: "#000000aa", borderRadius: 12, padding: "6px 14px", lineHeight: 1.5 }}>
        {win.map((w, i) => { const on = now >= w.t - 0.05 && now < w.t + w.d + 0.05;
          return <span key={i} style={{ color: on ? "#F5B301" : "#fff", fontWeight: 800, fontSize: 36, textShadow: "0 2px 10px #000" }}>{w.w} </span>; })}
      </div>
    </div>
  );
};

export const ClockworkShort: React.FC<ClockworkProps> = (props) => {
  const {
    title = "TIME, COMPRESSED", handle = "@clockworkusa", color = "#C2410C", accent = "#C2410C",
    scaleLabel, waypoints = [], hero, audio, music, subs, sfx = true,
  } = props;
  const f = useCurrentFrame(); const { fps, width: W, height: H } = useVideoConfig();
  const accent2 = lighten(accent, 0.55);

  const introF = Math.round(INTRO_SEC * fps);
  const sweepSec = Math.max(2.5, waypoints.length * WAYPOINT_SEC);
  const sweepF = Math.round(sweepSec * fps);
  const heroF = Math.round(HERO_SEC * fps);
  const heroStartF = introF + sweepF;

  const heroPercent = Math.min(100, Math.max(0.001, hero?.atPercent ?? 100));
  // easing: percent(t) = heroPercent*(1-(1-t)^K) -> quét nhanh lúc t nhỏ, khựng lại khi t->1 (đúng lúc chạm hero)
  const percentAt = (t: number) => heroPercent * (1 - Math.pow(1 - Math.min(1, Math.max(0, t)), K));
  const tAtPercent = (p: number) => {
    const pc = Math.min(heroPercent - 0.0001, Math.max(0, p));
    return 1 - Math.pow(Math.max(0, 1 - pc / heroPercent), 1 / K);
  };

  const sweepLocalF = Math.min(sweepF, Math.max(0, f - introF));
  const sweepT = sweepF > 0 ? sweepLocalF / sweepF : 1;
  const curPercent = percentAt(sweepT);
  const prevT = Math.max(0, (sweepLocalF - 1) / Math.max(1, sweepF));
  const speed = curPercent - percentAt(prevT); // %/frame tức thời -> để vẽ vệt sao chổi

  // hình học thanh tiến trình
  const BAR_X0 = 110, BAR_X1 = 970, BAR_Y = 1180, BAR_H = 16;
  const xForPercent = (p: number) => BAR_X0 + (p / 100) * (BAR_X1 - BAR_X0);
  const markerX = xForPercent(curPercent);

  const introP = spring({ frame: f, fps, config: { damping: 13, stiffness: 130 } });
  const headerP = spring({ frame: f, fps, config: { damping: 14, stiffness: 120 } });

  // mốc bắt đầu của từng waypoint = đúng lúc hand quét tới vị trí đó trên timeline
  const wpStarts = waypoints.map((wp) => introF + Math.round(tAtPercent(wp.atPercent) * sweepF));
  const HOLD_F = Math.round(1.35 * fps);

  const heroLocalF = f - heroStartF;
  const inHero = f >= heroStartF;
  const heroPop = spring({ frame: heroLocalF, fps, config: { damping: 13, stiffness: 110 } });
  const flashOp = interpolate(heroLocalF, [0, 3, 16], [0, 0.55, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const pulse = 0.5 + 0.5 * Math.sin(Math.max(0, heroLocalF) / 7);
  const sceneScale = 1 + Math.min(0.035, Math.max(0, heroLocalF) / 900);
  const barDim = interpolate(heroLocalF, [0, 22], [1, 0.28], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const barBlur = interpolate(heroLocalF, [0, 22], [0, 3], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const clampX = (x: number, halfW: number) => Math.min(Math.max(x, halfW + 16), W - halfW - 16);

  return (
    <AbsoluteFill style={{ background: "radial-gradient(120% 90% at 50% 10%, #1a0f08 0%, #0e0906 50%, #050403 100%)", fontFamily: "'Poppins',Arial", overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, transform: `scale(${sceneScale})`, transformOrigin: "50% 55%" }}>
        {/* mặt đồng hồ mờ trang trí phía sau — gắn thương hiệu CLOCKWORK mà không cản mạch chính (thanh tiến trình) */}
        <svg width={W} height={H} style={{ position: "absolute", inset: 0, opacity: 0.10 }}>
          <circle cx={W / 2} cy={BAR_Y} r={430} stroke={accent} strokeWidth={2} fill="none" />
          {Array.from({ length: 12 }).map((_, i) => {
            const ang = (i / 12) * Math.PI * 2 - Math.PI / 2;
            const r1 = 430, r2 = 400;
            const x1 = W / 2 + Math.cos(ang) * r1, y1 = BAR_Y + Math.sin(ang) * r1;
            const x2 = W / 2 + Math.cos(ang) * r2, y2 = BAR_Y + Math.sin(ang) * r2;
            return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={accent} strokeWidth={4} />;
          })}
        </svg>

        {/* HEADER */}
        <div style={{ position: "absolute", top: 92, left: 0, right: 0, textAlign: "center", padding: "0 56px", opacity: 0.35 + headerP * 0.65, transform: `translateY(${(1 - headerP) * -16}px)` }}>
          <div style={{ display: "inline-block", background: accent, color: "#0a0603", fontWeight: 900, fontSize: 28, letterSpacing: 2, padding: "8px 22px", borderRadius: 12 }}>⏱ CLOCKWORK</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 64, lineHeight: 1.04, marginTop: 18, textShadow: "0 4px 24px #000c", textWrap: "balance" as any }}>{title}</div>
          <div style={{ display: "inline-block", marginTop: 16, background: "#00000055", border: `1.5px solid ${accent}99`, color: accent2, fontWeight: 800, fontSize: 26, letterSpacing: 1, padding: "8px 20px", borderRadius: 30 }}>{scaleLabel}</div>
        </div>

        {/* THANH TIẾN TRÌNH (mờ dần khi vào pha hero để nhường chỗ cho panel zoom) */}
        <div style={{ position: "absolute", inset: 0, opacity: barDim, filter: `blur(${barBlur}px)` }}>
          {/* track nền */}
          <div style={{ position: "absolute", left: BAR_X0, top: BAR_Y - BAR_H / 2, width: BAR_X1 - BAR_X0, height: BAR_H, borderRadius: BAR_H, background: "#ffffff14", border: "1px solid #ffffff1f" }} />
          {/* phần đã quét qua */}
          <div style={{ position: "absolute", left: BAR_X0, top: BAR_Y - BAR_H / 2, width: Math.max(0, markerX - BAR_X0), height: BAR_H, borderRadius: BAR_H,
            background: `linear-gradient(90deg, ${accent}55, ${accent})`, boxShadow: `0 0 22px ${accent}88` }} />
          {/* nhãn 2 đầu thanh */}
          <div style={{ position: "absolute", left: BAR_X0, top: BAR_Y + 26, color: "#ffffff77", fontWeight: 800, fontSize: 22, letterSpacing: 1 }}>START</div>
          <div style={{ position: "absolute", left: BAR_X1 - 60, top: BAR_Y + 26, color: "#ffffff77", fontWeight: 800, fontSize: 22, letterSpacing: 1 }}>NOW</div>

          {/* WAYPOINTS: tick + nhãn thoáng hiện đúng lúc hand quét ngang qua */}
          {waypoints.map((wp, i) => {
            const st = wpStarts[i]; const lf = f - st; if (lf < 0) return null;
            const pop = spring({ frame: lf, fps, config: { damping: 12, stiffness: 180 } });
            const labelOp = interpolate(lf, [0, 8, HOLD_F - 12, HOLD_F], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            const x = xForPercent(wp.atPercent);
            const up = i % 2 === 0; const labelY = up ? BAR_Y - 96 : BAR_Y - 150;
            const halfW = 150; const lx = clampX(x, halfW);
            return (
              <React.Fragment key={i}>
                <div style={{ position: "absolute", left: x - 2, top: BAR_Y - 20, width: 4, height: 40, borderRadius: 2,
                  background: accent2, boxShadow: lf < 18 ? `0 0 ${20 * (1 - lf / 18)}px ${accent}` : `0 0 8px ${accent}aa`,
                  transform: `scaleY(${Math.min(1, pop)})`, transformOrigin: "center" }} />
                <div style={{ position: "absolute", left: lx, top: labelY, transform: `translateX(-50%) scale(${0.85 + pop * 0.15})`, opacity: labelOp,
                  background: "#0c0806e6", border: `1.5px solid ${accent}bb`, borderRadius: 12, padding: "8px 16px", maxWidth: halfW * 2, textAlign: "center" }}>
                  <div style={{ color: "#fff", fontWeight: 800, fontSize: 26, lineHeight: 1.15 }}>{wp.label}</div>
                </div>
              </React.Fragment>
            );
          })}

          {/* MARKER — đầu quét, có vệt sao chổi dài/ngắn theo tốc độ tức thời (nhanh=vệt dài, chậm=vệt ngắn) */}
          <div style={{ position: "absolute", left: BAR_X0, top: BAR_Y - BAR_H / 2, width: Math.max(0, markerX - BAR_X0), height: BAR_H,
            background: `linear-gradient(90deg, transparent ${Math.max(0, 100 - Math.min(260, speed * 46) / (markerX - BAR_X0 || 1) * 100)}%, ${accent2}cc 100%)`, borderRadius: BAR_H }} />
          <div style={{ position: "absolute", left: markerX - 15, top: BAR_Y - 15, width: 30, height: 30, borderRadius: 30, background: accent2,
            boxShadow: `0 0 ${18 + speed * 3}px 6px ${accent}, 0 0 44px ${accent}77` }} />
        </div>
      </div>

      {/* FLASH va chạm lúc hand tới đích */}
      <AbsoluteFill style={{ background: accent2, opacity: flashOp, pointerEvents: "none" }} />

      {/* HERO REVEAL — panel phóng to đúng lát cắt cuối cùng gây sốc */}
      {inHero ? (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", pointerEvents: "none" }}>
          <div style={{ width: 880, transform: `scale(${Math.min(1, heroPop)})`, opacity: Math.min(1, heroPop * 1.4),
            background: "linear-gradient(180deg, #140b06f2, #0a0603f5)", border: `2.5px solid ${accent}`, borderRadius: 32,
            boxShadow: `0 0 ${50 + pulse * 30}px ${accent}66, 0 20px 60px #000a`, padding: "44px 40px", textAlign: "center" }}>
            <div style={{ display: "inline-block", background: `${accent}22`, border: `1.5px solid ${accent}`, color: accent2,
              fontWeight: 900, fontSize: 26, letterSpacing: 2, padding: "7px 20px", borderRadius: 30 }}>{(hero?.label || "").toUpperCase()}</div>

            {/* mini-timeline zoom: chỉ vẽ lát cắt cuối cùng, marker nằm sát mép phải, phóng to */}
            <div style={{ position: "relative", height: 46, margin: "34px 10px 10px" }}>
              <div style={{ position: "absolute", left: 0, right: 0, top: 20, height: 8, borderRadius: 8, background: `linear-gradient(90deg, ${accent}33, ${accent})` }} />
              <div style={{ position: "absolute", right: 4, top: 8, width: 32, height: 32, borderRadius: 32, background: accent2,
                boxShadow: `0 0 ${26 + pulse * 22}px 8px ${accent}` }} />
            </div>

            <div style={{ color: "#fff", fontWeight: 900, fontSize: 108, lineHeight: 1.0, marginTop: 18, letterSpacing: -1,
              textShadow: `0 0 ${30 + pulse * 20}px ${accent}aa`, textWrap: "balance" as any }}>{hero?.realValue}</div>
            <div style={{ marginTop: 18, color: "#ffffffaa", fontWeight: 700, fontSize: 26 }}>on this scale</div>
          </div>
        </AbsoluteFill>
      ) : null}

      {/* INTRO overlay */}
      {f < introF ? (
        <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 42%, ${accent}22, #050403 70%)`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          <div style={{ fontSize: 140, transform: `scale(${introP})` }}>⏱️</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 74, marginTop: 8, textAlign: "center", padding: "0 60px", opacity: introP, textWrap: "balance" as any }}>{title}</div>
        </AbsoluteFill>
      ) : null}

      {/* SFX */}
      {sfx ? (
        <>
          {waypoints.map((_, i) => (
            <Sequence key={"wpsfx" + i} from={Math.max(0, wpStarts[i])} durationInFrames={12}><Audio src={staticFile("sfx/pop.mp3")} volume={0.45} /></Sequence>
          ))}
          <Sequence from={Math.max(0, heroStartF)} durationInFrames={36}><Audio src={staticFile("sfx/impact.mp3")} volume={0.7} /></Sequence>
          <Sequence from={Math.max(0, heroStartF + 6)} durationInFrames={40}><Audio src={staticFile("sfx/ding.mp3")} volume={0.5} /></Sequence>
        </>
      ) : null}

      <KaraokeCaption subs={subs} />
      <div style={{ position: "absolute", bottom: 50, left: 0, right: 0, textAlign: "center", color: "#ffffffcc", fontWeight: 800, fontSize: 32, textShadow: "0 2px 10px #000" }}>{handle}</div>
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
    </AbsoluteFill>
  );
};
