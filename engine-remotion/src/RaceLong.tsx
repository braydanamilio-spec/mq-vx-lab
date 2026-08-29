import { AbsoluteFill, Sequence, Audio, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import React from "react";
import { BarChartRace, RaceProps, calcRace } from "./BarChartRace";
import { WorldMapRace } from "./WorldMapRace";

// ẢNH AN TOÀN: nếu 1 ảnh (tải về) lỗi/hỏng -> tự đổi sang _fallback.jpg, KHÔNG làm VỠ cả render.
// Remotion: có onError thì <Img> gọi handler thay vì ném lỗi hủy render.
const FB_IMG = staticFile("img/_fallback.jpg");
const SafeImg: React.FC<any> = ({ src, ...rest }) => {
  const [s, setS] = React.useState(src);
  React.useEffect(() => { setS(src); }, [src]);
  return <Img src={s} onError={() => { if (s !== FB_IMG) setS(FB_IMG); }} {...rest} />;
};

const cfmt = (v: number) => v >= 1000 ? (v / 1000).toFixed(v >= 10000 ? 0 : 1) + "K" : v < 100 ? String(Number(v.toFixed(1))) : String(Math.round(v));
// số cho COLD-OPEN: rõ nghĩa (nghìn tỉ/tỉ) thay vì K khó hiểu
const coldNum = (v: number, unit: string) => {
  if (unit === "$") return v >= 1000 ? "$" + (v / 1000).toFixed(1) + "T" : "$" + Math.round(v) + "B";
  if (unit === "M") return v >= 1000 ? (v / 1000).toFixed(1) + "B" : Math.round(v) + "M";
  return cfmt(v) + (unit ? " " + unit : "");
};

// COLD OPEN — đập kết quả sốc ngay 3s đầu (ảnh/logo + số khổng lồ + flash + whoosh) rồi mới tiêu đề => giữ chân
type Cold = { name: string; value: number; unit?: string; photo?: string; logo?: string; color?: string; hook?: string };
const ColdOpen: React.FC<Cold> = ({ name, value, unit = "", photo, logo, color = "#F5B301", hook }) => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const zoom = interpolate(f, [0, 90], [1.12, 1.26]);
  const nP = spring({ frame: f - 4, fps, config: { damping: 11, stiffness: 150 } });
  const flash = interpolate(f, [4, 9, 24], [0, 0.42, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const hookO = interpolate(f, [42, 56], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#05070e", fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
      {photo ? <AbsoluteFill><SafeImg src={staticFile(photo)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${zoom})`, filter: "brightness(0.92) saturate(1.05)" }} /></AbsoluteFill> : null}
      {/* làm tối VỪA để chữ rõ nhưng ảnh vẫn thấy rõ, sang */}
      <AbsoluteFill style={{ background: photo ? "linear-gradient(180deg, rgba(5,7,14,0.35) 0%, rgba(5,7,14,0.18) 40%, rgba(5,7,14,0.5) 100%)" : "radial-gradient(circle at 50% 42%, rgba(5,7,14,0.15), rgba(5,7,14,0.85) 78%)" }} />
      {photo ? <AbsoluteFill style={{ background: "radial-gradient(ellipse 46% 34% at 50% 46%, rgba(5,7,14,0.55), rgba(5,7,14,0) 75%)" }} /> : null}
      <AbsoluteFill style={{ background: "#fff", opacity: flash * 0.12 }} />
      <div style={{ textAlign: "center", transform: `scale(${0.55 + Math.min(1, nP) * 0.45})`, zIndex: 2, display: "flex", flexDirection: "column", alignItems: "center" }}>
        {!photo && logo ? <div style={{ width: 260, height: 260, borderRadius: 40, background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 34, boxShadow: `0 0 70px ${color}aa, 0 20px 50px #000a` }}><Img src={staticFile(logo)} style={{ width: "72%", height: "72%", objectFit: "contain" }} /></div> : null}
        <div style={{ fontSize: 220, fontWeight: 900, color: "#fff", lineHeight: 1, letterSpacing: -5, textShadow: `0 0 90px ${color}, 0 8px 40px #000` }}>{coldNum(value, unit)}</div>
        <div style={{ fontSize: 66, fontWeight: 900, color, letterSpacing: 3, marginTop: 4, textShadow: "0 4px 24px #000" }}>{name.toUpperCase()}</div>
      </div>
      {hook ? <div style={{ position: "absolute", bottom: 104, fontSize: 46, fontWeight: 800, color: "#EAF2FF", opacity: hookO, textShadow: "0 3px 18px #000" }}>{hook}</div> : null}
      <Sequence from={3} durationInFrames={18}><Audio src={staticFile("sfx/whoosh.mp3")} volume={0.6} /></Sequence>
      <Sequence from={7} durationInFrames={18}><Audio src={staticFile("sfx/ding.mp3")} volume={0.5} /></Sequence>
    </AbsoluteFill>
  );
};

// LONG coherent 6-8' cho mid-roll ads: 1 PILLAR (nhiều race cùng chủ đề) + lời bình TTS + intro/outro + nhạc nền.
type Word = { t: number; d: number; w: string; si: number };
type Seg = { title?: string; subtitle?: string; kicker?: string; audio?: string; sec?: number; subs?: Word[]; bg?: string; bignum?: string; bigcap?: string };
export type NarratedRace = RaceProps & { narration?: string; chart?: "bars" | "map"; subs?: Word[]; bg?: string; shots?: string[] };

// ẢNH DẪN CHỨNG cắt vào ĐÚNG LÚC NÓI — shots[si] = ảnh cho câu si; pop-in khớp thời điểm câu bắt đầu.
const IllustrationInsert: React.FC<{ subs?: Word[]; shots?: string[] }> = ({ subs, shots }) => {
  const f = useCurrentFrame(); const { fps, width, height } = useVideoConfig();
  if (!subs || !subs.length || !shots || !shots.length) return null;
  const now = f / fps; const port = height > width;
  if (now < subs[0].t) return null;
  let idx = subs.findIndex((s) => now < s.t + s.d); if (idx === -1) idx = subs.length - 1;
  const si = subs[idx].si;
  const img = shots[si]; if (!img) return null;
  const first = subs.find((s) => s.si === si); const sentStart = first ? first.t : now;
  const pop = spring({ frame: Math.max(0, Math.round((now - sentStart) * fps)), fps, config: { damping: 15, stiffness: 150 } });
  const inO = interpolate(now, [sentStart - 0.05, sentStart + 0.22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const z = 1.05 + 0.08 * Math.min(1, (now - sentStart) / 3.5);   // Ken Burns nhẹ
  const box: React.CSSProperties = port
    ? { position: "absolute", left: "50%", bottom: 250, transform: `translateX(-50%) scale(${0.9 + Math.min(1, pop) * 0.1})`, width: width * 0.74, height: width * 0.74 * 0.6 }
    : { position: "absolute", right: 80, top: height * 0.5 - 150, transform: `scale(${0.9 + Math.min(1, pop) * 0.1})`, width: 470, height: 300 };
  return (
    <div style={{ ...box, borderRadius: 22, overflow: "hidden", border: "3px solid #ffffffcc", boxShadow: "0 22px 60px #000b", opacity: inO, zIndex: 5 }}>
      <SafeImg src={staticFile(img)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${z})` }} />
    </div>
  );
};

// LỚP ẢNH NỀN THỰC TẾ — full-bleed + Ken Burns (zoom chậm) + overlay tối để chữ/bars vẫn rõ.
const BgImage: React.FC<{ src?: string; dim?: number }> = ({ src, dim = 0.55 }) => {
  const f = useCurrentFrame(); const { durationInFrames } = useVideoConfig();
  if (!src) return null;
  const z = interpolate(f, [0, Math.max(1, durationInFrames)], [1.06, 1.2], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <SafeImg src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${z})`, filter: "saturate(1.05)" }} />
      <AbsoluteFill style={{ background: `linear-gradient(180deg, rgba(7,10,20,${dim}) 0%, rgba(7,10,20,${dim + 0.18}) 55%, rgba(7,10,20,0.92) 100%)` }} />
    </AbsoluteFill>
  );
};

// NỀN ĐỘNG — ĐỔI ảnh theo TỪNG CÂU đang nói (crossfade mượt) + Ken Burns + overlay tối để chart rõ.
const DynamicBg: React.FC<{ subs?: Word[]; shots?: string[]; fallback?: string }> = ({ subs, shots, fallback }) => {
  const f = useCurrentFrame(); const { fps, width, height } = useVideoConfig();
  const now = f / fps; const port = height > width;
  const raw = (shots && shots.length) ? shots : (fallback ? [fallback] : []);
  const anyImg = raw.find(Boolean) || fallback || null;
  if (!anyImg) return null;
  const imgs = raw.map((x) => x || anyImg);      // lấp null bằng ảnh gần nhất -> KHÔNG bao giờ staticFile(null)
  let si = 0;
  if (subs && subs.length) { let idx = subs.findIndex((s) => now < s.t + s.d); if (idx === -1) idx = subs.length - 1; si = subs[idx].si; }
  si = Math.min(si, imgs.length - 1);
  const cur = imgs[si] || anyImg; const prev = (si > 0 ? imgs[si - 1] : imgs[si]) || anyImg;
  const first = subs && subs.find((s) => s.si === si); const start = first ? first.t : 0;
  const fade = interpolate(now, [start, start + 0.45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const z = 1.06 + 0.1 * Math.min(1, (now - start) / 5);
  // overlay NHẸ để ẢNH RÕ: tối nhẹ tổng thể + đậm chỗ bars/chữ đứng (dọc: đậm cột giữa-trái + đáy; ngang: đậm trái + đáy)
  const readMask = port
    ? "linear-gradient(90deg, rgba(6,9,17,0.72) 0%, rgba(6,9,17,0.5) 62%, rgba(6,9,17,0.2) 100%)"
    : "linear-gradient(90deg, rgba(6,9,17,0.82) 0%, rgba(6,9,17,0.5) 55%, rgba(6,9,17,0.12) 100%)";
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#070a14" }}>
      <SafeImg src={staticFile(prev)} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", objectPosition: "center" }} />
      <SafeImg src={staticFile(cur)} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", objectPosition: "center", transform: `scale(${z})`, opacity: fade }} />
      <AbsoluteFill style={{ background: "rgba(6,9,17,0.28)" }} />
      <AbsoluteFill style={{ background: readMask }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(6,9,17,0) 55%, rgba(6,9,17,0.82) 100%)" }} />
    </AbsoluteFill>
  );
};

// KARAOKE SUB — khớp voice (sync theo câu), chữ vàng highlight đúng lúc đọc, nền mờ dưới (không đè bars quan trọng)
const KaraokeCaption: React.FC<{ subs?: Word[] }> = ({ subs }) => {
  const f = useCurrentFrame(); const { fps, width } = useVideoConfig();
  if (!subs || !subs.length) return null;
  const now = f / fps;
  if (now < subs[0].t - 0.25) return null;                 // trước khi nói -> ẩn
  let idx = subs.findIndex((s) => now < s.t + s.d);
  if (idx === -1) idx = subs.length - 1;
  const si = subs[idx].si;
  const sent = subs.filter((s) => s.si === si);
  const wi = Math.max(0, sent.findIndex((s) => s === subs[idx]));   // vị trí chữ đang đọc trong câu
  const CH = 5;                                                     // hiện ~5 chữ/lần (cụm), TO, 1 dòng
  const cs = Math.floor(wi / CH) * CH;
  const chunk = sent.slice(cs, cs + CH);
  const c0 = chunk[0].t; const app = interpolate(now, [c0 - 0.12, c0 + 0.12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", bottom: 96, left: 0, width: "100%", display: "flex", justifyContent: "center", pointerEvents: "none", opacity: app }}>
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "0 16px", padding: "16px 42px", maxWidth: "80%", background: "rgba(6,10,20,0.82)", border: "1px solid #ffffff1c", borderRadius: 22, whiteSpace: "nowrap", overflow: "hidden", boxShadow: "0 10px 34px #0008" }}>
        {chunk.map((s, i) => {
          const active = now >= s.t && now < s.t + s.d;
          return <span key={i} style={{ fontSize: 52, fontWeight: 900, color: active ? "#F5B301" : "#EAF2FF", transform: active ? "scale(1.08)" : "none", textShadow: active ? "0 0 26px #F5B301aa" : "none" }}>{s.w}</span>;
        })}
      </div>
    </div>
  );
};
export type MultiProps = {
  races: NarratedRace[];
  intro?: Seg; outro?: Seg; cold?: Cold;
  handle?: string; music?: string;
};
const secF = (s: number) => Math.round((s || 0) * 30);
const COLD = 3.0;   // giây cold-open

export const calcMulti = ({ props }: { props: MultiProps }) => {
  const coldF = props.cold ? secF(COLD) : 0;
  const introF = secF(props.intro?.sec || 0);
  const outroF = secF(props.outro?.sec || 0);
  const racesF = (props.races || []).reduce((a, r) => a + calcRace({ props: r }).durationInFrames, 0);
  return { durationInFrames: Math.max(1, coldF + introF + racesF + outroF) };
};

const ACC = ["#22D3EE", "#F5B301", "#EC4899", "#7C5CFF", "#2FA84F"];
const TitleScreen: React.FC<Seg & { kind: "intro" | "outro" }> = ({ title = "", subtitle = "", kicker = "", kind, bg, bignum, bigcap }) => {
  const f = useCurrentFrame(); const { fps, width, height } = useVideoConfig();
  const port = height > width;                                   // 9:16 -> co chữ + đổi overlay để không chồng chéo
  const p = spring({ frame: f, fps, config: { damping: 14, stiffness: 130 } });
  const pop = spring({ frame: f - 2, fps, config: { damping: 9, stiffness: 170 } });  // kicker nảy
  const numS = spring({ frame: f - 8, fps, config: { damping: 12, stiffness: 150 } }); // số dẫn nảy vào
  const capO = interpolate(f, [14, 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const tx = (1 - Math.min(1, p)) * -40;   // trượt vào từ trái
  const l = title.replace(/\n/g, "").length;
  const titleFs = port ? (l > 20 ? 96 : l > 14 ? 116 : 132) : (l > 26 ? 128 : l > 20 ? 150 : l > 14 ? 176 : 196);
  const pad = port ? "0 60px" : "0 96px";
  return (
    // HƯỚNG A · IMPACT — canh TRÁI, số dẫn (kiểu top data-channel USA)
    <AbsoluteFill style={{ background: "linear-gradient(180deg,#243468,#1e2a55)", fontFamily: "'Poppins',Arial", justifyContent: "center", alignItems: "flex-start", padding: pad, overflow: "hidden" }}>
      <BgImage src={bg} dim={0.5} />
      <AbsoluteFill style={{ background: port
        ? "linear-gradient(180deg, rgba(7,10,20,0.55) 0%, rgba(7,10,20,0.25) 45%, rgba(7,10,20,0.9) 100%)"
        : "linear-gradient(90deg, rgba(7,10,20,0.9) 0%, rgba(7,10,20,0.45) 55%, rgba(7,10,20,0.1) 100%)" }} />
      <div style={{ position: "relative", zIndex: 2, transform: `translateX(${tx}px)`, maxWidth: port ? "100%" : "78%" }}>
        {kicker ? <div style={{ fontSize: port ? 24 : 30, fontWeight: 800, letterSpacing: port ? 6 : 9, color: "#FF3B3B", textTransform: "uppercase", marginBottom: port ? 14 : 18, opacity: Math.min(1, pop) }}>{kicker}</div> : null}
        <div style={{ fontFamily: "Anton, 'Poppins'", fontSize: titleFs, fontWeight: 400, color: "#fff", lineHeight: 0.9, letterSpacing: 1, textTransform: "uppercase", textShadow: "0 10px 44px #000b", whiteSpace: "pre-line" }}>{title}</div>
        {bignum ? <div style={{ fontFamily: "Anton, 'Poppins'", fontSize: port ? 130 : 168, lineHeight: 0.92, color: "#FFC400", letterSpacing: 1, marginTop: 14, textShadow: "0 8px 34px #FFC40044", transform: `scale(${0.7 + Math.min(1, numS) * 0.3})`, transformOrigin: "left center" }}>{bignum}</div> : null}
        {(bigcap || subtitle) ? <div style={{ fontSize: port ? 32 : (bigcap ? 40 : 42), fontWeight: bigcap ? 800 : 700, color: bigcap ? "#C6D4E6" : "#9FC0E6", textTransform: bigcap ? "uppercase" : "none", letterSpacing: bigcap ? 1.5 : 0.5, marginTop: 16, opacity: capO, maxWidth: port ? "94%" : "100%" }}>{bigcap || subtitle}</div> : null}
        {!bignum ? <div style={{ width: 130, height: 7, background: "#F5B301", borderRadius: 4, marginTop: 30, transform: `scaleX(${Math.min(1, p)})`, transformOrigin: "left" }} /> : null}
      </div>
      {kind === "outro" ? <div style={{ position: "absolute", bottom: 84, left: port ? 60 : 96, fontSize: 40, fontWeight: 900, color: "#8FB6DE", opacity: capO }}>▶ @dataracehq</div> : null}
    </AbsoluteFill>
  );
};

export const RaceLong: React.FC<MultiProps> = ({ races = [], intro, outro, cold, handle = "@dataracehq", music }) => {
  const coldF = cold ? secF(COLD) : 0;
  const introF = secF(intro?.sec || 0);
  const outroF = secF(outro?.sec || 0);
  let off = coldF + introF;
  const segs = races.map((r, i) => {
    const rd = calcRace({ props: r }).durationInFrames;
    const from = off; off += rd;
    return { r, i, from, rd };
  });
  const outroFrom = off;
  return (
    <AbsoluteFill style={{ background: "#070a14" }}>
      {music ? <Audio src={staticFile(music)} volume={0.045} /> : null}
      {cold ? (
        <Sequence from={0} durationInFrames={coldF}><ColdOpen {...cold} /></Sequence>
      ) : null}
      {intro ? (
        <Sequence from={coldF} durationInFrames={introF}>
          {intro.audio ? <Audio src={staticFile(intro.audio)} volume={1} /> : null}
          <Sequence durationInFrames={18}><Audio src={staticFile("sfx/whoosh.mp3")} volume={0.55} /></Sequence>
          <TitleScreen kind="intro" {...intro} />
        </Sequence>
      ) : null}
      {segs.map(({ r, i, from, rd }) => (
        <Sequence key={i} from={from} durationInFrames={rd}>
          {r.narration ? <Audio src={staticFile(r.narration)} volume={1} /> : null}
          <Sequence durationInFrames={16}><Audio src={staticFile("sfx/whoosh.mp3")} volume={0.5} /></Sequence>
          <DynamicBg subs={r.subs} shots={r.shots} fallback={r.bg} />
          {/* 27/8 — PHỤ ĐỀ CHỒNG PHỤ ĐỀ (anh chụp ảnh AMERICALOOKEDUP): trên khung hình có HAI
              băng chữ cùng một câu, khác cỡ, khác vị trí, khác cách ngắt cụm — một cái có nền đen
              bo góc, một cái chữ trắng trần nằm lệch xuống dưới.
              Nguyên nhân ở đúng hai dòng này: `{...r}` trải CẢ `r.subs` xuống BarChartRace, mà
              BarChartRace tự vẽ `<Karaoke subs={subs}/>` bên trong nó; rồi ngay dòng sau RaceLong
              lại vẽ thêm `<KaraokeCaption>` của riêng mình. Hai bộ vẽ khác nhau, ngắt cụm khác
              nhau (5 chữ vs 8 chữ), nên không chồng khít mà thành bóng ma.
              Sửa: RaceLong LÀM CHỦ lớp phụ đề — biểu đồ chỉ vẽ biểu đồ. Cắt `subs` khỏi props
              truyền xuống thay vì gỡ Karaoke trong BarChartRace, vì BarChartRace còn được dùng
              độc lập ở chỗ khác và ở đó nó VẪN PHẢI tự vẽ phụ đề. */}
          {r.chart === "map"
            ? <WorldMapRace {...r} subs={undefined} music={undefined} handle={r.handle || handle} transparent={true} />
            : <BarChartRace {...r} subs={undefined} music={undefined} handle={r.handle || handle} transparent={true} />}
          <KaraokeCaption subs={r.subs} />
        </Sequence>
      ))}
      {outro ? (
        <Sequence from={outroFrom} durationInFrames={outroF}>
          {outro.audio ? <Audio src={staticFile(outro.audio)} volume={1} /> : null}
          <TitleScreen kind="outro" {...outro} />
        </Sequence>
      ) : null}
    </AbsoluteFill>
  );
};
