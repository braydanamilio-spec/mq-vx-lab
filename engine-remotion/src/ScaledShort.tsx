import { AbsoluteFill, Sequence, Audio, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { Karaoke } from "./Karaoke";
import { Bookend } from "./Bookend";
import { phong } from "./Phong";
import { ChuyenCanh } from "./Chuyen";
import React from "react";

// KÊNH #4 SCALED — so sánh KÍCH THƯỚC vật lý thật, vẽ ĐÚNG TỈ LỆ cạnh nhau. Motif riêng.
type Word = { t: number; d: number; w: string };
export type ScaleItem = { name: string; emoji?: string; value: number; disp?: string; dur?: number };
export type ScaledProps = {
  title?: string; subtitle?: string; handle?: string; color?: string; accent?: string;
  items: ScaleItem[]; introSec?: number; itemSec?: number; outroSec?: number;
  font?: string;
  audio?: string; music?: string; subs?: Word[]; sfx?: boolean;
};

const FPS = 30;
const idur = (it: ScaleItem, s: number) => (it.dur && it.dur > 0 ? it.dur : s);

export const calcScaled = ({ props }: any) => {
  const its: ScaleItem[] = props.items || [];
  const isec = props.introSec ?? 1.8, isc = props.itemSec ?? 2.0, tail = props.outroSec ?? 1.6;
  const total = its.reduce((a, it) => a + idur(it, isc), 0);
  return { durationInFrames: Math.round((isec + total + tail) * FPS), fps: FPS, width: 1080, height: 1920 };
};

export const ScaledShort: React.FC<ScaledProps> = (props) => {
  const { font = "", title = "SIZE COMPARISON", subtitle = "", handle = "@scaledusa", color = "#2FA84F", accent = "#2FA84F",
    items = [], introSec = 1.8, itemSec = 2.0, outroSec = 1.6, audio, music, sfx = true , subs = [] } = props;
  const f = useCurrentFrame(); const { fps, width: W, height: H } = useVideoConfig();

  // LAYOUT tính sẵn: cao emoji ∝ giá trị thật; cột ≥ LABEL_MIN (nhãn luôn đủ chỗ) — chỉ co PHẦN kích thước khi tràn.
  const GROUND = H - 430, TOPLIMIT = 470, PAD = 30, USABLE = W - 100, LABEL_MIN = 178;
  const maxH = Math.min(GROUND - TOPLIMIT, 600), floor = 46;   // cạp cao emoji lớn nhất -> hệ số co không giết cột nhãn
  const maxV = Math.max(1, ...items.map((d) => d.value));
  let hs = items.map((d) => floor + (d.value / maxV) * (maxH - floor));
  let cols = hs.map((h) => Math.max(LABEL_MIN, h + PAD * 2));
  let totalW = cols.reduce((a, b) => a + b, 0);
  if (totalW > USABLE) {
    const fixed = LABEL_MIN * items.length;
    if (fixed >= USABLE) { const k = USABLE / totalW; cols = cols.map((c) => c * k); }     // quá nhiều item -> co đều
    else { const k2 = (USABLE - fixed) / (totalW - fixed); cols = cols.map((c) => LABEL_MIN + (c - LABEL_MIN) * k2); }
    totalW = cols.reduce((a, b) => a + b, 0);
  }
  hs = hs.map((h, i) => Math.max(floor, Math.min(h, cols[i] - 20)));    // emoji vừa trong cột của nó
  const startX = (W - totalW) / 2;
  const xs: number[] = []; let cur = startX;
  for (const c of cols) { xs.push(cur + c / 2); cur += c; }                 // tâm mỗi cột

  const introF = Math.round(introSec * fps);
  const starts: number[] = []; let acc = introF;
  for (const it of items) { starts.push(acc); acc += Math.round(idur(it, itemSec) * fps); }
  const introP = spring({ frame: f, fps, config: { damping: 12, stiffness: 140 } });

  return (
    <AbsoluteFill style={{ background: "radial-gradient(120% 90% at 50% 8%, #10251a 0%, #0a1510 55%, #060b08 100%)", fontFamily: phong(font) }}>
      {/* TIÊU ĐỀ */}
      <div style={{ position: "absolute", top: 96, left: 0, right: 0, textAlign: "center", padding: "0 50px" }}>
        <div style={{ display: "inline-block", background: color, color: "#0a0c14", fontWeight: 900, fontSize: 30, letterSpacing: 2, padding: "8px 22px", borderRadius: 12 }}>📏 SCALED</div>
        {/* Tiêu đề lúc mở đầu do Bookend vẽ. Header ẩn đi trong quãng đó, nếu không sẽ có hai bản tiêu đề chồng nhau (lỗi 25/8). */}
        <div style={{ display: f < introF ? "none" : undefined, color: "#fff", fontWeight: 900, fontSize: 70, lineHeight: 1.02, marginTop: 18, textShadow: "0 4px 24px #000c", textWrap: "balance" as any }}>{title}</div>
        {subtitle ? <div style={{ color: "#9fc4ac", fontWeight: 700, fontSize: 32, marginTop: 8 }}>{subtitle}</div> : null}
      </div>

      {/* ĐƯỜNG NỀN (mặt đất) */}
      <div style={{ position: "absolute", top: GROUND, left: 40, right: 40, height: 4, background: `linear-gradient(90deg, #0000, ${accent}88, #0000)` }} />

      {/* CÁC VẬT — emoji scale đúng tỉ lệ, đứng trên nền, hiện lần lượt */}
      {items.map((it, i) => {
        const s = spring({ frame: f - starts[i], fps, config: { damping: 13, stiffness: 150 } });
        if (f < starts[i]) return null;
        const h = hs[i]; const biggest = it.value === maxV;
        return (
          <div key={i} style={{ position: "absolute", left: xs[i], top: GROUND, transform: "translateX(-50%)", textAlign: "center" }}>
            {/* emoji cao = h, mọc từ nền lên */}
            <div style={{ position: "absolute", left: "50%", bottom: 0, transform: `translateX(-50%) scaleY(${s}) `, transformOrigin: "bottom",
              fontSize: h, lineHeight: 0.9, height: h, display: "flex", alignItems: "flex-end", justifyContent: "center",
              filter: biggest ? `drop-shadow(0 0 24px ${accent})` : "drop-shadow(0 6px 14px #0008)" }}>{it.emoji || "❓"}</div>
            {/* nhãn dưới nền — bó trong bề rộng cột, tự xuống dòng -> không chồng */}
            <div style={{ position: "absolute", top: 18, left: "50%", transform: "translateX(-50%)", opacity: s, width: cols[i] - 12 }}>
              <div style={{ color: "#fff", fontWeight: 900, fontSize: 32, lineHeight: 1.05, overflowWrap: "break-word", whiteSpace: "normal" }}>{it.name}</div>
              <div style={{ display: "inline-block", marginTop: 6, background: biggest ? accent : "#132a1e", color: biggest ? "#0a0c14" : "#eafff2",
                border: `1.5px solid ${accent}`, fontWeight: 900, fontSize: 28, padding: "4px 14px", borderRadius: 12, whiteSpace: "nowrap" }}>{it.disp || it.value.toLocaleString()}</div>
            </div>
          </div>
        );
      })}

      {/* INTRO overlay */}
      {f < introF ? (
        <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 42%, #2FA84F22, #060b08 70%)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", paddingBottom: 620 }}>
          <div style={{ fontSize: 150, transform: `scale(${introP})` }}>📏</div>
        </AbsoluteFill>
      ) : null}

      {/* CHUYỂN CẢNH — mục lớn nhất là nhịp mạnh. Mức âm do Chuyen.MUC_AM quyết, không viết cứng. */}
      {sfx ? (
        <ChuyenCanh accent={accent} khoa={handle}
                    nhip={items.map((it, i) => ({ at: starts[i], manh: it.value === maxV ? 1 : 0.6 }))} />
      ) : null}

      <div style={{ position: "absolute", bottom: 50, left: 0, right: 0, textAlign: "center", color: "#ffffffcc", fontWeight: 800, fontSize: 32, textShadow: "0 2px 10px #000" }}>{handle}</div>
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
      <Karaoke subs={subs} accent={accent} />
      <Bookend title={title} handle={handle} accent={accent} color={color}
               introSec={introSec} outroSec={outroSec} />
    </AbsoluteFill>
  );
};
