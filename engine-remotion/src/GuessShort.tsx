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
// dur = độ dài vòng (giây, khớp giọng); revSec = giây tới lúc REVEAL trong vòng. Có thì bám giọng chuẩn, không thì fallback roundSec*0.66.
export type Round = { q: string; clue?: string; answer: string; stat?: string; img?: string; dur?: number; revSec?: number };
export type GuessProps = {
  title?: string; handle?: string; color?: string; accent?: string;
  rounds: Round[]; roundSec?: number; introSec?: number; outroSec?: number;
  audio?: string; music?: string; subs?: Word[]; sfx?: boolean;
};

const FPS = 30;
const rdur = (r: Round, rsec: number) => (r.dur && r.dur > 0 ? r.dur : rsec);   // độ dài 1 vòng
export const calcGuess = ({ props }: any) => {
  const rs: Round[] = props.rounds || [];
  const rsec = props.roundSec || 7;
  const isec = props.introSec ?? 1.6;
  // 24/8 — đuôi 1.2s trước đây KHÔNG vẽ gì, chỉ còn trơ nền tối (#0a0c14) -> "kết thúc đen".
  // Nay có thẻ kết thật (ảnh + kêu gọi) nên cho 2.4s để người xem kịp đọc và bấm theo dõi.
  const tail = props.outroSec ?? 2.4;
  const total = rs.reduce((a, r) => a + rdur(r, rsec), 0);
  return { durationInFrames: Math.round((isec + total + tail) * FPS), fps: FPS, width: 1080, height: 1920 };
};

// hash cố định [0,1) -> thứ tự mảnh ghép biến mất KHÔNG đổi theo frame (Remotion cần deterministic, tránh flicker)
const hash01 = (n: number) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

// LƯỚI MẢNH GHÉP: ô che ảnh, biến mất dần theo p (0..1). Ép người xem đoán trước khi lộ hết.
const COLS = 6, ROWS = 10;
const MosaicTiles: React.FC<{ p: number; accent: string }> = ({ p, accent }) => {
  const tiles = [];
  for (let row = 0; row < ROWS; row++) for (let col = 0; col < COLS; col++) {
    const i = row * COLS + col;
    const ord = hash01(i + 1);                                  // mốc biến mất của ô
    const tp = Math.max(0, Math.min(1, (p - ord) / 0.08));      // 0=còn che, 1=đã mở
    if (tp >= 1) continue;                                      // ô đã mở -> bỏ (ảnh lộ)
    const dark = (row + col) % 2 === 0 ? "#11151f" : "#0b0e17";
    const edge = tp > 0.01 && tp < 1;                           // ô đang mở -> viền sáng accent
    tiles.push(
      <div key={i} style={{
        position: "absolute", left: `${(col / COLS) * 100}%`, top: `${(row / ROWS) * 100}%`,
        width: `${100 / COLS}%`, height: `${100 / ROWS}%`,
        background: `linear-gradient(135deg, ${dark}, #05070d)`,
        border: edge ? `2px solid ${accent}` : "1px solid #ffffff10",
        opacity: 1 - tp, transform: `scale(${1 - tp * 0.35}) rotate(${tp * (ord > 0.5 ? 8 : -8)}deg)`,
        boxShadow: edge ? `0 0 22px ${accent}bb` : "none",
      }} />
    );
  }
  return <AbsoluteFill>{tiles}</AbsoluteFill>;
};

// ĐỒNG HỒ đếm giờ: vòng tròn vơi dần + số 3-2-1 ở giữa
const RingClock: React.FC<{ frac: number; label: number; accent: string }> = ({ frac, label, accent }) => {
  const R = 150, C = 2 * Math.PI * R;
  return (
    <div style={{ position: "relative", width: 360, height: 360, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <svg width={360} height={360} style={{ position: "absolute", transform: "rotate(-90deg)" }}>
        <circle cx={180} cy={180} r={R} fill="none" stroke="#ffffff22" strokeWidth={18} />
        <circle cx={180} cy={180} r={R} fill="none" stroke={accent} strokeWidth={18} strokeLinecap="round"
          strokeDasharray={C} strokeDashoffset={C * (1 - frac)} style={{ filter: `drop-shadow(0 0 16px ${accent})` }} />
      </svg>
      <div style={{ fontFamily: "Anton, Poppins, Arial", fontWeight: 900, fontSize: 210, color: "#fff", textShadow: `0 0 50px ${accent}, 0 8px 30px #000` }}>{label}</div>
    </div>
  );
};

// 1 VÒNG ĐOÁN: mảnh ghép mở dần + đồng hồ 3-2-1 -> REVEAL (đáp án bung + tia + stat)
const GuessRound: React.FC<{ r: Round; color: string; accent: string; sec: number; idx: number; sfx?: boolean }> = ({ r, color, accent, sec, idx, sfx }) => {
  const f = useCurrentFrame(); const dur = Math.max(1, sec * FPS);
  // ép >=7: nếu revSec rất nhỏ (bám giọng khớp 1 câu ngắn), revF-6 có thể <=0 -> khoảng [0, revF-6, revF] không tăng dần
  // -> Remotion interpolate() throw "must be strictly increasing".
  const revF = Math.max(7, r.revSec && r.revSec > 0 ? Math.round(r.revSec * FPS) : Math.round(dur * 0.66));
  const revealed = f >= revF;
  const mosaicP = interpolate(f, [0, revF], [0, 1], { extrapolateRight: "clamp" });  // % mảnh ghép đã mở
  const blur = interpolate(f, [0, revF - 6, revF], [12, 5, 0], { extrapolateRight: "clamp" });  // blur nền nhẹ, sắc dần
  const dim = interpolate(f, [revF - 8, revF], [0.5, 0.24], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const zoom = interpolate(f, [0, dur], [1.12, 1.22]);
  // đồng hồ đếm ngược 3-2-1
  const cdTotal = revF; const remain = Math.max(0, cdTotal - f);
  const frac = remain / cdTotal;                             // vòng vơi dần 1 -> 0
  const cd = Math.min(3, Math.max(1, Math.ceil((remain / cdTotal) * 3)));
  const ans = spring({ frame: f - revF, fps: FPS, config: { damping: 10, stiffness: 170 } });
  const flash = interpolate(f, [revF, revF + 4, revF + 16], [0, 0.55, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const rays = interpolate(f, [revF, revF + 20], [0.4, 1.6], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }); // tia bung
  const raysO = interpolate(f, [revF, revF + 6, revF + 30], [0, 0.5, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#0a0c14" }}>
      {/* SFX: 3 tick đếm ngược + whoosh cận reveal + impact & ding lúc bung đáp án */}
      {sfx ? [0, 1, 2].map((k) => (
        <Sequence key={"t" + k} from={Math.max(0, revF - Math.round((3 - k) * FPS * 0.55))} durationInFrames={6}>
          <Audio src={staticFile("sfx/pop.mp3")} volume={0.45} />
        </Sequence>
      )) : null}
      {sfx ? <Sequence from={Math.max(0, revF - 8)} durationInFrames={16}><Audio src={staticFile("sfx/whoosh.mp3")} volume={0.5} /></Sequence> : null}
      {sfx ? <Sequence from={revF} durationInFrames={45}><Audio src={staticFile("sfx/impact.mp3")} volume={0.7} /></Sequence> : null}
      {sfx ? <Sequence from={revF + 3} durationInFrames={45}><Audio src={staticFile("sfx/ding.mp3")} volume={0.4} /></Sequence> : null}
      {r.img ? <AbsoluteFill><SafeImg src={staticFile(r.img)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${zoom})`, filter: `blur(${blur}px) brightness(${1 - dim})` }} /></AbsoluteFill> : null}
      {/* mảnh ghép che ảnh, mở dần */}
      {!revealed ? <MosaicTiles p={mosaicP} accent={accent} /> : null}
      <AbsoluteFill style={{ background: `linear-gradient(180deg, #000d 0%, #0000 24%, #0000 60%, #000e 100%)` }} />
      {flash > 0 ? <AbsoluteFill style={{ background: accent, opacity: flash }} /> : null}
      {/* câu hỏi trên */}
      <div style={{ position: "absolute", top: 120, left: 0, right: 0, textAlign: "center", padding: "0 60px" }}>
        <div style={{ display: "inline-block", background: color, color: "#0a0c14", fontWeight: 900, fontSize: 34, letterSpacing: 1, padding: "10px 24px", borderRadius: 14, fontFamily: "Poppins, Arial" }}>ROUND {idx + 1}</div>
        <div style={{ color: "#fff", fontWeight: 900, fontSize: 62, lineHeight: 1.05, marginTop: 22, textShadow: "0 4px 24px #000c", fontFamily: "Poppins, Arial", textWrap: "balance" as any }}>{r.q}</div>
        {r.clue && !revealed ? <div style={{ color: "#e5e7eb", fontWeight: 700, fontSize: 36, marginTop: 16, textShadow: "0 2px 12px #000e" }}>🔎 {r.clue}</div> : null}
      </div>
      {/* đồng hồ đếm ngược giữa */}
      {!revealed ? (
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <RingClock frac={frac} label={cd} accent={accent} />
        </div>
      ) : null}
      {/* REVEAL: tia bung + đáp án đập vào */}
      {revealed ? (
        <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
          {raysO > 0 ? <div style={{ position: "absolute", width: 900, height: 900, borderRadius: "50%", transform: `scale(${rays})`, opacity: raysO, background: `radial-gradient(circle, ${accent}00 40%, ${accent}66 55%, ${accent}00 70%)` }} /> : null}
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", transform: `scale(${0.6 + ans * 0.4})`, opacity: ans }}>
            <div style={{ color: "#fff", fontWeight: 900, fontSize: 118, lineHeight: 1, textAlign: "center", padding: "0 40px", textShadow: `0 6px 40px #000, 0 0 40px ${accent}88`, fontFamily: "Poppins, Arial" }}>{r.answer}</div>
            {r.stat ? <div style={{ marginTop: 26, background: accent, color: "#0a0c14", fontWeight: 900, fontSize: 46, padding: "14px 34px", borderRadius: 18, fontFamily: "Poppins, Arial" }}>{r.stat}</div> : null}
          </div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};

export const GuessShort: React.FC<GuessProps> = (props) => {
  const { title = "GUESS THE USA", handle = "@guessusa", color = "#F5B301", accent = "#ff375f", rounds = [], roundSec = 7, introSec = 1.6, audio, music, subs = [], sfx = true } = props;
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const introF = Math.round(introSec * fps);
  const introP = spring({ frame: f, fps, config: { damping: 12, stiffness: 140 } });
  return (
    <AbsoluteFill style={{ background: "#0a0c14", fontFamily: "Poppins, Arial" }}>
      {/* INTRO */}
      <Sequence durationInFrames={introF}>
        <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 40%, ${color}22, #0a0c14 70%)`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          {/* 24/8 — MỞ ĐẦU KHÔNG CÒN TRƠ NỀN TỐI: mượn ảnh của vòng 1 (đã tải sẵn cho vòng đó nên
              KHÔNG tốn thêm lượt tải/quota nào), làm mờ + tối để chữ vẫn nổi, thêm phóng nhẹ cho
              khung hình có chuyển động ngay giây đầu. Giây đầu là chỗ YouTube tính giữ chân gắt nhất
              mà lại là chỗ nhàm nhất thì phí. Không có ảnh -> vẫn về nền gradient như cũ. */}
          {rounds[0]?.img ? (
            <AbsoluteFill>
              <SafeImg src={staticFile(rounds[0].img as string)}
                style={{ width: "100%", height: "100%", objectFit: "cover",
                         transform: `scale(${1.12 + introP * 0.06})`, filter: "blur(13px) brightness(0.42)" }} />
              <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 42%, ${color}33, #0a0c14cc 72%)` }} />
            </AbsoluteFill>
          ) : null}
          <div style={{ fontSize: 150, transform: `scale(${introP})` }}>🤔</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 86, marginTop: 10, textAlign: "center", padding: "0 50px", transform: `translateY(${(1 - introP) * 40}px)`, opacity: introP, textWrap: "balance" as any }}>{title}</div>
          <div style={{ color: color, fontWeight: 800, fontSize: 40, marginTop: 18, opacity: introP }}>Can you get them all? 👀</div>
        </AbsoluteFill>
      </Sequence>
      {/* CÁC VÒNG — offset cộng dồn theo độ dài từng vòng (bám giọng) */}
      {rounds.map((r, i) => {
        const sec = rdur(r, roundSec);
        const from = introF + Math.round(rounds.slice(0, i).reduce((a, rr) => a + rdur(rr, roundSec), 0) * fps);
        return (
          <Sequence key={i} from={from} durationInFrames={Math.round(sec * fps)}>
            <GuessRound r={r} color={color} accent={accent} sec={sec} idx={i} sfx={sfx} />
          </Sequence>
        );
      })}
      {/* THẺ KẾT (24/8) — trước đây hết vòng cuối là màn hình trơ nền tối, không lời kêu gọi nào.
          Dùng lại ảnh vòng CUỐI (đã có sẵn) + câu hỏi chốt để đẩy bình luận, và nhắc theo dõi. */}
      {(() => {
        const tongVong = rounds.reduce((a, rr) => a + rdur(rr, roundSec), 0);
        const ketF = introF + Math.round(tongVong * fps);
        const tailF = Math.max(1, Math.round((props.outroSec ?? 2.4) * fps));
        const anhCuoi = [...rounds].reverse().find(rr => rr.img)?.img;
        return (
          <Sequence from={ketF} durationInFrames={tailF}>
            <KetCard img={anhCuoi} color={color} accent={accent} handle={handle} n={rounds.length} />
          </Sequence>
        );
      })()}
      {/* handle góc */}
      <div style={{ position: "absolute", bottom: 54, left: 0, right: 0, textAlign: "center", color: "#ffffffcc", fontWeight: 800, fontSize: 34, textShadow: "0 2px 10px #000" }}>{handle}</div>
      {/* karaoke caption (nếu có subs) */}
      {subs.length ? <KaraokeCaption subs={subs} /> : null}
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
    </AbsoluteFill>
  );
};

// THẺ KẾT: ảnh nền (mượn vòng cuối) + số điểm + kêu gọi. Vào bằng spring, không cắt cứng.
const KetCard: React.FC<{ img?: string; color: string; accent: string; handle: string; n: number }> =
  ({ img, color, accent, handle, n }) => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const p = spring({ frame: f, fps, config: { damping: 13, stiffness: 130 } });
  return (
    <AbsoluteFill style={{ background: "#0a0c14", alignItems: "center", justifyContent: "center" }}>
      {img ? (
        <AbsoluteFill>
          <SafeImg src={staticFile(img)} style={{ width: "100%", height: "100%", objectFit: "cover",
            transform: `scale(${1.1 + p * 0.05})`, filter: "blur(15px) brightness(0.38)" }} />
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 45%, ${color}2e, #0a0c14dd 70%)` }} />
      <div style={{ position: "relative", textAlign: "center", padding: "0 60px",
                    transform: `translateY(${(1 - p) * 34}px)`, opacity: p }}>
        <div style={{ fontSize: 120 }}>🏆</div>
        <div style={{ color: "#fff", fontWeight: 900, fontSize: 92, lineHeight: 1.05,
                      textShadow: `0 6px 34px #000, 0 0 40px ${accent}66`, fontFamily: "Poppins, Arial" }}>
          HOW MANY<br />DID YOU GET?
        </div>
        <div style={{ display: "inline-block", marginTop: 26, background: color, color: "#0a0c14",
                      fontWeight: 900, fontSize: 46, padding: "14px 34px", borderRadius: 18,
                      fontFamily: "Poppins, Arial" }}>{n} / {n} ?  COMMENT BELOW 👇</div>
        <div style={{ color: "#ffffffdd", fontWeight: 800, fontSize: 40, marginTop: 26,
                      textShadow: "0 2px 12px #000" }}>▶ FOLLOW {handle}</div>
      </div>
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
