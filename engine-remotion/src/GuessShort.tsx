import { AbsoluteFill, Sequence, Audio, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import React from "react";

// ẢNH AN TOÀN (giống RaceLong): ảnh lỗi -> _fallback, không vỡ render.
const FB_IMG = staticFile("img/_fallback.jpg");
const SafeImg: React.FC<any> = ({ src, ...rest }) => {
  const [s, setS] = React.useState(src);
  React.useEffect(() => { setS(src); }, [src]);
  return <Img src={s} onError={() => { if (s !== FB_IMG) setS(FB_IMG); }} {...rest} />;
};

type Word = { t: number; d: number; w: string };
export type Round = { q: string; clue?: string; answer: string; stat?: string; img?: string };
export type GuessProps = {
  title?: string; handle?: string; color?: string; accent?: string;
  rounds: Round[]; roundSec?: number; introSec?: number;
  audio?: string; music?: string; subs?: Word[];
};

const FPS = 30;
export const calcGuess = ({ props }: any) => {
  const rs: Round[] = props.rounds || [];
  const rsec = props.roundSec || 7;
  const isec = props.introSec ?? 1.6;
  return { durationInFrames: Math.round((isec + rs.length * rsec + 1.2) * FPS), fps: FPS, width: 1080, height: 1920 };
};

// 1 VÒNG ĐOÁN: ảnh mờ dần + câu hỏi + đếm ngược 3-2-1 -> REVEAL (rõ + đáp án đập vào + stat)
const GuessRound: React.FC<{ r: Round; color: string; accent: string; sec: number; idx: number }> = ({ r, color, accent, sec, idx }) => {
  const f = useCurrentFrame(); const dur = sec * FPS;
  const revF = Math.round(dur * 0.66);                       // mốc reveal (66% vòng)
  const revealed = f >= revF;
  const blur = interpolate(f, [0, revF - 6, revF], [26, 14, 0], { extrapolateRight: "clamp" });   // mờ -> rõ khi reveal
  const dim = interpolate(f, [revF - 8, revF], [0.62, 0.28], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const zoom = interpolate(f, [0, dur], [1.14, 1.24]);
  // đếm ngược 3-2-1 trước reveal
  const cdTotal = revF; const remain = Math.max(0, cdTotal - f);
  const cd = Math.min(3, Math.ceil((remain / cdTotal) * 3));
  const cdPulse = 1 + 0.14 * Math.sin((f % 30) / 30 * Math.PI);
  const ans = spring({ frame: f - revF, fps: FPS, config: { damping: 10, stiffness: 170 } });
  const flash = interpolate(f, [revF, revF + 4, revF + 16], [0, 0.5, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#0a0c14" }}>
      {r.img ? <AbsoluteFill><SafeImg src={staticFile(r.img)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${zoom})`, filter: `blur(${blur}px) brightness(${1 - dim})` }} /></AbsoluteFill> : null}
      <AbsoluteFill style={{ background: `linear-gradient(180deg, #000c 0%, #0000 26%, #0000 62%, #000d 100%)` }} />
      {flash > 0 ? <AbsoluteFill style={{ background: accent, opacity: flash }} /> : null}
      {/* câu hỏi trên */}
      <div style={{ position: "absolute", top: 120, left: 0, right: 0, textAlign: "center", padding: "0 60px" }}>
        <div style={{ display: "inline-block", background: color, color: "#0a0c14", fontWeight: 900, fontSize: 34, letterSpacing: 1, padding: "10px 24px", borderRadius: 14, fontFamily: "Poppins, Arial" }}>ROUND {idx + 1}</div>
        <div style={{ color: "#fff", fontWeight: 900, fontSize: 62, lineHeight: 1.05, marginTop: 22, textShadow: "0 4px 24px #000c", fontFamily: "Poppins, Arial", textWrap: "balance" as any }}>{r.q}</div>
        {r.clue && !revealed ? <div style={{ color: "#cbd5e1", fontWeight: 600, fontSize: 36, marginTop: 16, textShadow: "0 2px 12px #000c" }}>🔎 {r.clue}</div> : null}
      </div>
      {/* đếm ngược giữa */}
      {!revealed ? (
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div style={{ fontFamily: "Poppins, Arial", fontWeight: 900, fontSize: 320, color: accent, transform: `scale(${cdPulse})`, textShadow: `0 0 60px ${accent}, 0 10px 40px #000` }}>{cd}</div>
        </div>
      ) : null}
      {/* REVEAL: đáp án đập vào */}
      {revealed ? (
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", transform: `scale(${0.6 + ans * 0.4})`, opacity: ans }}>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 118, lineHeight: 1, textAlign: "center", padding: "0 40px", textShadow: `0 6px 40px #000, 0 0 40px ${accent}88`, fontFamily: "Poppins, Arial" }}>{r.answer}</div>
          {r.stat ? <div style={{ marginTop: 26, background: accent, color: "#0a0c14", fontWeight: 900, fontSize: 46, padding: "14px 34px", borderRadius: 18, fontFamily: "Poppins, Arial" }}>{r.stat}</div> : null}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

export const GuessShort: React.FC<GuessProps> = (props) => {
  const { title = "GUESS THE USA", handle = "@guessusa", color = "#F5B301", accent = "#ff375f", rounds = [], roundSec = 7, introSec = 1.6, audio, music, subs = [] } = props;
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const introF = Math.round(introSec * fps);
  const introP = spring({ frame: f, fps, config: { damping: 12, stiffness: 140 } });
  return (
    <AbsoluteFill style={{ background: "#0a0c14", fontFamily: "Poppins, Arial" }}>
      {/* INTRO */}
      <Sequence durationInFrames={introF}>
        <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 40%, ${color}22, #0a0c14 70%)`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          <div style={{ fontSize: 150, transform: `scale(${introP})` }}>🤔</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 86, marginTop: 10, textAlign: "center", padding: "0 50px", transform: `translateY(${(1 - introP) * 40}px)`, opacity: introP, textWrap: "balance" as any }}>{title}</div>
          <div style={{ color: color, fontWeight: 800, fontSize: 40, marginTop: 18, opacity: introP }}>Can you get them all? 👀</div>
        </AbsoluteFill>
      </Sequence>
      {/* CÁC VÒNG */}
      {rounds.map((r, i) => (
        <Sequence key={i} from={introF + i * roundSec * fps} durationInFrames={roundSec * fps}>
          <GuessRound r={r} color={color} accent={accent} sec={roundSec} idx={i} />
        </Sequence>
      ))}
      {/* handle góc */}
      <div style={{ position: "absolute", bottom: 54, left: 0, right: 0, textAlign: "center", color: "#ffffffcc", fontWeight: 800, fontSize: 34, textShadow: "0 2px 10px #000" }}>{handle}</div>
      {/* karaoke caption (nếu có subs) */}
      {subs.length ? <KaraokeCaption subs={subs} /> : null}
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
    </AbsoluteFill>
  );
};

// caption karaoke bám giọng (giống RaceLong): từ đang đọc sáng lên
const KaraokeCaption: React.FC<{ subs: Word[] }> = ({ subs }) => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig(); const now = f / fps;
  const cur = subs.filter(w => now >= w.t - 0.05 && now < w.t + w.d + 0.05);
  if (!cur.length) return null;
  // gom câu quanh từ hiện tại (đơn giản: hiện cụm 5 từ quanh)
  const idx = subs.indexOf(cur[0]); const from = Math.max(0, idx - 2); const win = subs.slice(from, from + 6);
  return (
    <div style={{ position: "absolute", bottom: 150, left: 0, right: 0, textAlign: "center", padding: "0 60px" }}>
      <div style={{ display: "inline", background: "#000000aa", borderRadius: 12, padding: "6px 14px", lineHeight: 1.5 }}>
        {win.map((w, i) => { const on = now >= w.t - 0.05 && now < w.t + w.d + 0.05;
          return <span key={i} style={{ color: on ? "#F5B301" : "#fff", fontWeight: 800, fontSize: 40, textShadow: "0 2px 10px #000" }}>{w.w} </span>; })}
      </div>
    </div>
  );
};
