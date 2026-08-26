import { AbsoluteFill, Sequence, Audio, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { Karaoke } from "./Karaoke";
import { Bookend } from "./Bookend";
import { phong } from "./Phong";
import { ChuyenCanh } from "./Chuyen";
import React from "react";

// KÊNH #6 LONGSHOT — real odds/probability, items HOP UP a vertical log-scale ladder to their real rung.
// Camera scrolls/zooms up as rarity increases; final item = big dramatic push-in reveal. Motif: vertical ladder, unique so far.
type Word = { t: number; d: number; w: string };
export type LongshotItem = { label: string; emoji?: string; oddsDisp: string; logValue: number; vo?: string; dur?: number };
export type LongshotProps = {
  title?: string; handle?: string; color?: string; accent?: string;
  items: LongshotItem[]; introSec?: number; itemSec?: number; outroSec?: number;
  font?: string;
  audio?: string; music?: string; subs?: Word[]; sfx?: boolean;
};

const FPS = 30;
const idur = (it: LongshotItem, s: number) => (it.dur && it.dur > 0 ? it.dur : s);

export const calcLongshot = ({ props }: any) => {
  const its: LongshotItem[] = props.items || [];
  const isec = props.introSec ?? 1.8, isc = props.itemSec ?? 2.7, tail = props.outroSec ?? 2.4;
  const total = its.reduce((a, it) => a + idur(it, isc), 0);
  return { durationInFrames: Math.round((isec + total + tail) * FPS), fps: FPS, width: 1080, height: 1920 };
};

// ---- ladder geometry (log scale: 1 log10 unit == RUNG_GAP px, so rarity gaps grow "further apart" up the tower) ----
const RUNG_GAP = 232;
const BOTTOM_PAD = 470;
const TOP_PAD = 520;
const ANCHOR_Y = 1920 * 0.66;
const RAIL_L = 1080 / 2 - 96, RAIL_R = 1080 / 2 + 96, CENTER = 1080 / 2;

const fmtRung = (n: number) => {
  const v = Math.pow(10, n);
  if (v < 1e6) return "1 in " + v.toLocaleString();
  if (v < 1e9) return "1 in " + Math.round(v / 1e6) + "M";
  return "1 in " + Math.round(v / 1e9) + "B";
};

// bouncy multi-hop climb: splits the climb into N discrete rung-hops (anticipation + landing bounce each hop)
const climbPos = (f: number, climbStart: number, climbDur: number, hops: number, fromY: number, toY: number, fps: number) => {
  const local = f - climbStart;
  if (local <= 0) return { y: fromY, hopT: 0, arc: 0, done: false, justLanded: false };
  if (local >= climbDur) return { y: toY, hopT: 1, arc: 0, done: true, justLanded: local < climbDur + 3 };
  const perHop = climbDur / hops;
  const hopIdx = Math.min(hops - 1, Math.floor(local / perHop));
  const hopLocal = local - hopIdx * perHop;
  const hopFromY = fromY + (hopIdx / hops) * (toY - fromY);
  const hopToY = fromY + ((hopIdx + 1) / hops) * (toY - fromY);
  const sp = spring({ frame: hopLocal, fps, config: { damping: 11, stiffness: 210, mass: 0.55 } });
  const y = interpolate(sp, [0, 1], [hopFromY, hopToY], { extrapolateRight: "clamp" });
  const arc = Math.sin(Math.min(1, hopLocal / Math.max(1, perHop)) * Math.PI) * 16; // small horizontal hop-arc
  return { y, hopT: sp, arc, done: false, justLanded: false, hopLocal, perHop };
};

const yForLog = (log: number, trackH: number) => trackH - BOTTOM_PAD - log * RUNG_GAP;

export const LongshotShort: React.FC<LongshotProps> = (props) => {
  const { font = "", title = "WHAT ARE THE REAL ODDS?", handle = "@longshotusa", color = "#4F46E5", accent = "#4F46E5",
    items = [], introSec = 1.8, itemSec = 2.7, outroSec = 2.4, audio, music, sfx = true , subs = [] } = props;
  const f = useCurrentFrame(); const { fps, width: W, height: H } = useVideoConfig();

  const introF = Math.round(introSec * fps);
  const starts: number[] = []; let acc = introF;
  for (const it of items) { starts.push(acc); acc += Math.round(idur(it, itemSec) * fps); }
  const introP = spring({ frame: f, fps, config: { damping: 12, stiffness: 140 } });

  const maxLogAll = Math.max(1, ...items.map((d) => d.logValue));
  const maxN = Math.ceil(maxLogAll) + 1;
  const trackH = BOTTOM_PAD + maxN * RUNG_GAP + TOP_PAD;

  // which item is currently active (climbing or holding), and its live Y
  let activeIdx = -1;
  for (let i = 0; i < items.length; i++) { if (f >= starts[i]) activeIdx = i; }

  let activeY = trackH - BOTTOM_PAD; // ground level while still in intro
  let activeLog = 0;
  const climbHops = 3;
  const climbFrac = 0.56; // portion of each item's slot spent hopping, rest = hold/reveal

  const perItemClimb: { y: number; arc: number; done: boolean; justLanded: boolean }[] = [];
  for (let i = 0; i < items.length; i++) {
    const slotFrames = Math.round(idur(items[i], itemSec) * fps);
    const climbDur = Math.max(18, Math.round(slotFrames * climbFrac));
    const prevLog = i === 0 ? 0 : items[i - 1].logValue;
    const fromY = yForLog(prevLog, trackH), toY = yForLog(items[i].logValue, trackH);
    const c = climbPos(f, starts[i], climbDur, climbHops, fromY, toY, fps);
    perItemClimb.push({ y: c.y, arc: c.arc, done: c.done, justLanded: c.justLanded });
  }
  if (activeIdx >= 0) { activeY = perItemClimb[activeIdx].y; activeLog = interpolate(activeY, [yForLog(maxLogAll, trackH), yForLog(0, trackH)], [maxLogAll, 0]); }

  const isLast = activeIdx === items.length - 1 && activeIdx >= 0;
  const lastDone = isLast && perItemClimb[activeIdx].done;
  const lastLocal = isLast ? f - starts[activeIdx] : 0;

  // zoom: creeps up with rarity reached, extra dramatic punch-in once the final item lands
  let zoom = interpolate(activeLog, [0, maxLogAll], [1, 1.26], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (lastDone) {
    const slotFrames = Math.round(idur(items[activeIdx], itemSec) * fps);
    const climbDur = Math.max(18, Math.round(slotFrames * climbFrac));
    const revealP = spring({ frame: lastLocal - climbDur, fps, config: { damping: 14, stiffness: 90 } });
    zoom = interpolate(revealP, [0, 1], [1.26, 1.46], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  }

  const camY = ANCHOR_Y - activeY;

  // Y CỦA CÁC NHÃN MỤC ĐANG HIỆN Ở NHÁNH TRÁI. Chú thích cũ ngay dưới đây khẳng định nhãn mục
  // "branches left/right so it never collides with the rung badges" — đo lại thì SAI: nhãn thang
  // trải tới RAIL_L+34, còn nhãn mục nhánh trái kết thúc ở RAIL_L-40, hai vùng chồng nhau
  // [RAIL_L-96, RAIL_L-40]. Thấy rõ ở canary: "1 in 15,300" đè lên "1 in 10,000".
  // Cách xử lý: khi hai thứ tranh chỗ thì BỎ nhãn thang, giữ nhãn mục — nhãn mục nói con số CHÍNH
  // XÁC của mục đó, còn nhãn thang chỉ là mốc tròn; giữ cái kém thông tin hơn là chọn sai.
  const yNhanTrai = items
    .map((it, i) => (i % 2 === 0 && f >= starts[i] ? perItemClimb[i].y : null))
    .filter((y): y is number => y !== null);

  return (
    <AbsoluteFill style={{ background: `radial-gradient(120% 90% at 50% 10%, #17163a 0%, #0d0b22 55%, #06050f 100%)`, fontFamily: phong(font), overflow: "hidden" }}>
      {/* TIÊU ĐỀ — fixed header, always visible */}
      <div style={{ position: "absolute", top: 74, left: 0, right: 0, textAlign: "center", padding: "0 50px", zIndex: 5 }}>
        <div style={{ display: "inline-block", background: color, color: "#0a0c14", fontWeight: 900, fontSize: 28, letterSpacing: 2, padding: "7px 20px", borderRadius: 12 }}>🎲 LONGSHOT</div>
        {/* Tiêu đề lúc mở đầu do Bookend vẽ. Header ẩn đi trong quãng đó, nếu không sẽ có hai bản tiêu đề chồng nhau (lỗi 25/8). */}
        <div style={{ display: f < introF ? "none" : undefined, color: "#fff", fontWeight: 900, fontSize: 54, lineHeight: 1.04, marginTop: 14, textShadow: "0 4px 24px #000c", textWrap: "balance" as any, opacity: 0.5 + introP * 0.5 }}>{title}</div>
      </div>

      {/* CAMERA: outer scales (zoom) around the fixed anchor point; inner translates the tall ladder track */}
      <div style={{ position: "absolute", inset: 0, transformOrigin: `50% ${ANCHOR_Y}px`, transform: `scale(${zoom})` }}>
        <div style={{ position: "absolute", left: 0, right: 0, top: 0, width: W, height: trackH, transform: `translateY(${camY}px)` }}>
          {/* rails */}
          <div style={{ position: "absolute", left: RAIL_L, top: 0, width: 6, height: trackH, background: `linear-gradient(180deg, ${accent}00, ${accent}99 12%, ${accent}66 100%)`, borderRadius: 4 }} />
          <div style={{ position: "absolute", left: RAIL_R - 6, top: 0, width: 6, height: trackH, background: `linear-gradient(180deg, ${accent}00, ${accent}99 12%, ${accent}66 100%)`, borderRadius: 4 }} />

          {/* rungs — evenly spaced in LOG space (so real rarity gaps compound going up) */}
          {Array.from({ length: maxN + 1 }, (_, n) => n).map((n) => {
            const ry = yForLog(n, trackH);
            // 26/8 — CHỒNG CHỮ Ở ĐÁY KHUNG. Thang nằm trong lớp bị dịch `camY`, nên chỗ đứng THẬT
            // của một nấc trên màn hình là `camY + ry`, không phải `ry`. Nấc thấp nhất rơi đúng
            // vào dải đáy nơi đặt @handle -> nhãn "1 in 10" in đè lên tên kênh (thấy rõ ở canary
            // sau khi có defaultProps thật). Nấc trôi ra ngoài khung thì không vẽ: nó không mang
            // thông tin gì, chỉ kịp đâm vào chữ khác.
            // Vị trí THẬT trên khung phải đi qua CẢ HAI phép biến hình, không chỉ một:
            //   translateY(camY)  rồi  scale(zoom) quanh tâm 50% ANCHOR_Y.
            // Bản vá đầu của em chỉ cộng `camY` rồi kết luận nấc nằm an toàn — nhưng zoom 1.26-1.46
            // đẩy mọi thứ DƯỚI tâm xuống thấp thêm, nên nấc "an toàn" ở 1737 thật ra rơi xuống 1859,
            // đúng chỗ @handle. Render lại thấy vẫn chồng y nguyên: dấu hiệu tính sai chứ không phải
            // vá sai chỗ.
            const yMan = ANCHOR_Y + (camY + ry - ANCHOR_Y) * zoom;
            if (yMan > H - 118 || yMan < 92) return null;
            const bidong = yNhanTrai.some((y) => Math.abs(y - ry) < 46);
            const reached = activeLog >= n - 0.15;
            return (
              <div key={n} style={{ position: "absolute", top: ry - 3, left: RAIL_L - 26, width: RAIL_R - RAIL_L + 52, height: 6,
                background: reached ? `${accent}cc` : "#ffffff1c", borderRadius: 3 }}>
                {/* nhãn mốc dời hẳn ra MÉP TRÁI ngoài vùng token leo (CENTER±arc) -> KHÔNG BAO GIỜ bị token to đè lên,
                    dù ở mốc nào cũng đọc được (khác thiết kế cũ: label giữa cột, đúng chỗ token hạ cánh -> luôn đè). */}
                <div style={{ position: "absolute", top: -13, left: -70, whiteSpace: "nowrap", textAlign: "right", width: 130,
                  color: reached ? "#fff" : "#ffffff55", fontWeight: 800, fontSize: 22, letterSpacing: 0.5, textShadow: "0 2px 8px #000a",
                  opacity: bidong ? 0 : 1 }}>{n === 0 ? "EVERYDAY" : fmtRung(n)}</div>
              </div>
            );
          })}

          {/* ITEM TOKENS — hop up the pole, land on their real rung, label branches left/right */}
          {items.map((it, i) => {
            if (f < starts[i]) return null;
            const c = perItemClimb[i];
            const side = i % 2 === 0 ? -1 : 1;
            const isFinal = i === items.length - 1;
            const landedGlow = c.done && isFinal;
            const landScale = c.justLanded ? 1.22 : 1;
            const labelP = spring({ frame: f - starts[i] - Math.round(Math.round(idur(it, itemSec) * fps) * climbFrac) + 6, fps, config: { damping: 13, stiffness: 170 } });
            return (
              <React.Fragment key={i}>
                {/* token on the pole */}
                <div style={{ position: "absolute", top: c.y, left: CENTER + c.arc, transform: `translate(-50%,-50%) scale(${landScale})`,
                  width: isFinal && c.done ? 148 : 108, height: isFinal && c.done ? 148 : 108, borderRadius: "50%",
                  background: `radial-gradient(circle at 35% 30%, #ffffff22, ${accent}33 60%, #00000000)`, border: `3px solid ${accent}`,
                  display: "flex", alignItems: "center", justifyContent: "center", fontSize: isFinal && c.done ? 74 : 54,
                  boxShadow: landedGlow ? `0 0 60px ${accent}, 0 0 120px ${accent}88` : `0 6px 18px #0009`, zIndex: 3 }}>
                  {it.emoji || "🎯"}
                </div>
                {/* dust-puff impact ring on landing */}
                {c.justLanded ? (
                  <div style={{ position: "absolute", top: c.y, left: CENTER, transform: "translate(-50%,-50%)", width: 200, height: 200,
                    borderRadius: "50%", border: `3px solid ${accent}`, opacity: 0.7, zIndex: 2 }} />
                ) : null}
                {/* label + real odds, branches left/right so it never collides with the rung badges */}
                {c.done || f - starts[i] > Math.round(Math.round(idur(it, itemSec) * fps) * climbFrac) - 4 ? (
                  <div style={{ position: "absolute", top: c.y, left: side < 0 ? RAIL_L - 40 : RAIL_R + 40, transform: `translate(${side < 0 ? "-100%" : "0"}, -50%) scale(${Math.max(0, Math.min(1, labelP))})`,
                    opacity: Math.max(0, Math.min(1, labelP)), textAlign: side < 0 ? "right" as const : "left" as const, maxWidth: 300, zIndex: 3 }}>
                    <div style={{ color: "#fff", fontWeight: 800, fontSize: 30, lineHeight: 1.08, textShadow: "0 2px 10px #000c" }}>{it.label}</div>
                    <div style={{ display: "inline-block", marginTop: 6, background: accent, color: "#fff", fontWeight: 900, fontSize: 26, padding: "5px 14px", borderRadius: 10, letterSpacing: 0.3 }}>{it.oddsDisp}</div>
                  </div>
                ) : null}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* FINAL BIG REVEAL — fixed overlay, not affected by camera transform, glows once the last item lands */}
      {lastDone && items.length ? (() => {
        const last = items[items.length - 1];
        const slotFrames = Math.round(idur(last, itemSec) * fps);
        const climbDur = Math.max(18, Math.round(slotFrames * climbFrac));
        const p = spring({ frame: lastLocal - climbDur, fps, config: { damping: 13, stiffness: 110 } });
        const pulse = 1 + Math.sin((f / fps) * 6) * 0.02;
        return (
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end", paddingBottom: 210, zIndex: 6, pointerEvents: "none" }}>
            <div style={{ opacity: Math.min(1, p), transform: `translateY(${(1 - Math.min(1, p)) * 40}px) scale(${pulse})`, textAlign: "center", padding: "0 60px" }}>
              <div style={{ color: "#ffffffcc", fontWeight: 800, fontSize: 30, letterSpacing: 2, marginBottom: 6, textTransform: "uppercase" as const }}>{last.label}</div>
              <div style={{ fontFamily: "Anton, 'Poppins'", color: "#fff", fontWeight: 400, fontSize: 100, lineHeight: 0.98, letterSpacing: 1, textShadow: `0 0 50px ${accent}, 0 8px 30px #000c` }}>{last.oddsDisp.toUpperCase()}</div>
            </div>
          </AbsoluteFill>
        );
      })() : null}

      {/* INTRO overlay */}
      {f < introF ? (
        <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 44%, ${accent}22, #06050f 70%)`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", paddingBottom: 620, zIndex: 10 }}>
          <div style={{ fontSize: 150, transform: `scale(${introP})` }}>🪜</div>
        </AbsoluteFill>
      ) : null}

      {/* SFX: hop-land per item, bigger impact + ding on the final item */}
      {/* CHUYỂN CẢNH: bắt đầu leo = nhịp nhẹ, chạm nấc = nhịp chính, mục cuối = nhịp mạnh nhất.
          26/8 — thay ba dòng sfx viết cứng (0.22 / 0.45 / 0.7). Ba mức đó chênh nhau hơn ba lần,
          nên riêng trong một video đã nghe lồi lõm; giữa các kênh còn lệch hơn nữa. */}
      {sfx ? (
        <ChuyenCanh accent={accent} khoa={handle}
                    nhip={items.flatMap((it, i) => {
                      const climbDur = Math.max(18, Math.round(Math.round(idur(it, itemSec) * fps) * climbFrac));
                      return [
                        { at: starts[i], manh: 0.35 },
                        { at: starts[i] + climbDur - 4, manh: i === items.length - 1 ? 1 : 0.65 },
                      ];
                    })} />
      ) : null}

      <div style={{ position: "absolute", bottom: 50, left: 0, right: 0, textAlign: "center", color: "#ffffffcc", fontWeight: 800, fontSize: 32, textShadow: "0 2px 10px #000", zIndex: 5 }}>{handle}</div>
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
      <Karaoke subs={subs} accent={accent} />
      <Bookend title={title} handle={handle} accent={accent} color={color}
               introSec={introSec} outroSec={outroSec} />
    </AbsoluteFill>
  );
};
