import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig, interpolate, Audio, staticFile, Img } from "remotion";
import { phong } from "./Phong";
import React from "react";
import { Karaoke } from "./Karaoke";

// ==== KIỂU DỮ LIỆU ====
type Item = { name: string; value: number };
type Keyframe = { t: number; data: Item[] };
export type RaceProps = {
  title?: string; subtitle?: string; unit?: string; source?: string; handle?: string; font?: string; transparent?: boolean;
  frames: Keyframe[]; secondsPerFrame?: number; topN?: number; durationSec?: number;
  colors?: Record<string, string>; icons?: Record<string, string>; logos?: Record<string, string>; images?: Record<string, string>; photos?: Record<string, string>; themePhotos?: Record<string, string>; coldPhoto?: string; music?: string; sfx?: boolean;
  // 25/8 — hai prop TUỲ CHỌN cho kênh thế hệ 2: đua cột dựng thẳng từ dữ liệu, không footage, nên
  // cần đường gắn giọng + băng chữ ngay tại đây. Kênh cũ không truyền thì không có gì đổi.
  audio?: string; subs?: { t: number; d: number; w: string }[]; accent?: string;
};
export const calcRace = ({ props }: { props: RaceProps }) => {
  if (props.durationSec) return { durationInFrames: Math.max(1, Math.round(props.durationSec * 30)) }; // LONG: giữ khung kết khi lời bình còn nói
  const spf = props.secondsPerFrame ?? 2.2;
  return { durationInFrames: Math.max(1, Math.round(((props.frames.length - 1) * spf + 2.4) * 30)) };
};

const PAL = ["#22D3EE", "#F5B301", "#7C5CFF", "#2FA84F", "#E4562B", "#EC4899", "#38BDF8", "#A3E635", "#FB923C", "#F43F5E", "#818CF8", "#2DD4BF"];
const colorOf = (name: string, colors?: Record<string, string>) => {
  if (colors?.[name]) return colors[name];
  let h = 0; for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) % PAL.length;
  return PAL[h];
};
const fmt = (v: number) => {
  if (v >= 1000) return (v / 1000).toFixed(v >= 10000 ? 0 : 1) + "K";
  if (v < 100) return Number(v.toFixed(1)).toLocaleString("en-US"); // GDP/phim theo đơn vị nghìn tỉ/tỉ -> giữ 1 chữ số thập phân, số nguyên vẫn gọn
  return Math.round(v).toLocaleString("en-US");
};

export const BarChartRace: React.FC<RaceProps> = (props) => {
  const { title = "", subtitle = "", unit = "", source = "", handle = "", frames, colors, icons, logos, images, photos, themePhotos, coldPhoto, music, sfx = true, audio, subs, accent = "#F5B301", font = "" } = props;
  const spf = props.secondsPerFrame ?? 2.2; const topN = props.topN ?? 10;
  const f = useCurrentFrame(); const { width: W, height: H, fps } = useVideoConfig();
  const port = H > W;
  // vị trí trong chuỗi keyframe
  const tf = Math.min((frames.length - 1), f / fps / spf);
  // clamp về 0: nếu chỉ có 1 keyframe (frames.length===1) thì frames.length-2 = -1 -> frames[-1] undefined -> crash
  const i0 = Math.max(0, Math.min(frames.length - 2, Math.floor(tf))); const fr = tf - i0;
  const a = frames[i0], b = frames[Math.min(frames.length - 1, i0 + 1)];
  const names = Array.from(new Set([...a.data, ...b.data].map(d => d.name)));
  const val = (kf: Keyframe, n: string) => (kf.data.find(d => d.name === n)?.value ?? 0);
  const cur = names.map(n => ({ name: n, value: val(a, n) + (val(b, n) - val(a, n)) * (fr * fr * (3 - 2 * fr)) }))
    .filter(d => d.value > 0).sort((x, y) => y.value - x.value);
  const shown = cur.slice(0, topN);   // xếp hạng rời rạc -> hàng PHÂN BIỆT, không chồng (2 nước sát nút vẫn 2 hàng riêng)
  const maxV = Math.max(1, shown[0]?.value ?? 1);
  const maxNameLen = Math.max(1, ...shown.map((d) => d.name.length));           // co chữ nhãn nếu tên dài -> không cắt mép
  const lblFs = (port ? 34 : 32) - (maxNameLen > 15 ? 10 : maxNameLen > 12 ? 5 : 0);
  const year = Math.round(a.t + (b.t - a.t) * fr);

  // ── SOÁN NGÔI: tìm các mốc đổi #1 để bật callout "🏆 X overtakes" (kịch tính, chống nhàm)
  const leaderAt = (kf: Keyframe) => kf.data.slice().sort((x, y) => y.value - x.value)[0]?.name;
  let callout: { name: string; prev: string } | null = null; let calloutP = 0;
  const overtakeT: number[] = [];    // thời điểm (giây) đổi #1 -> whoosh + ding
  for (let i = 1; i < frames.length; i++) {
    const ln = leaderAt(frames[i]), lp = leaderAt(frames[i - 1]);
    if (ln && lp && ln !== lp) {
      const kt = i * spf, now = f / fps;
      overtakeT.push(kt);
      if (now >= kt - 0.15 && now <= kt + 2.1) { callout = { name: ln, prev: lp }; calloutP = interpolate(now, [kt - 0.15, kt + 0.2, kt + 1.7, kt + 2.1], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }); }
    }
  }
  const finalT = (frames.length - 1) * spf;   // kết -> cheer

  const bandTop = (port && (props as any).bandTop) ? (props as any).bandTop : 0;   // vùng ảnh băng trên (short) -> chart đẩy xuống
  const M = port ? 56 : 110; const topPad = (port ? 360 : 200) + bandTop; const bottomM = port ? 150 : 90;
  const rowH = (H - topPad - bottomM) / topN; const barH = rowH * 0.66;
  const labelW = port ? 300 : 330;                          // cột TÊN (canh phải) — KHÔNG chồng thanh
  const hero = (!port && (photos || images || logos || themePhotos || coldPhoto)) ? shown[0] : null;   // #1 hiện LỚN bên phải (ảnh thực thể / ảnh chủ đề theo leader)
  const heroW = hero ? 380 : 0;
  const chartW = W - (M + labelW) - M - (port ? 300 : 230) - heroW; // chừa chỗ số cuối thanh + hero (RỘNG hơn để nhãn "215K USD" không tràn mép)
  const intro = interpolate(f, [0, 12], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: props.transparent ? "transparent" : "linear-gradient(160deg,#0b1020 0%,#070a14 100%)", fontFamily: phong(font), opacity: intro }}>
      {/* tiêu đề */}
      <div style={{ position: "absolute", top: port ? 96 : 60, left: M, right: M }}>
        <div style={{ fontSize: port ? 62 : 66, fontWeight: 900, color: "#EAF2FF", letterSpacing: -1, lineHeight: 1.04 }}>{title}</div>
        {subtitle ? <div style={{ fontSize: port ? 36 : 34, fontWeight: 700, color: "#7FA8D0", marginTop: 10 }}>{subtitle}</div> : null}
      </div>
      {/* năm: dọc -> hàng riêng dưới subtitle (không đè tiêu đề); ngang -> ghost góc phải */}
      {port
        ? <div style={{ position: "absolute", top: 232, right: M, fontFamily: "Anton", fontSize: 150, fontWeight: 400, letterSpacing: 2, color: "#7FA8D0", opacity: 0.55, lineHeight: 1 }}>{year}</div>
        : <div style={{ position: "absolute", top: 30, right: M, fontFamily: "Anton", fontSize: 150, fontWeight: 400, letterSpacing: 2, color: "#7FA8D0", opacity: 0.5, lineHeight: 1 }}>{year}</div>}
      {/* các thanh */}
      {shown.map((d, rank) => {
        const y = topPad + rank * rowH;
        const w = Math.max(8, (d.value / maxV) * chartW);
        const col = colorOf(d.name, colors); const ic = icons?.[d.name] || ""; const logo = logos?.[d.name]; const bimg = images?.[d.name];
        const chip = port ? 48 : 44;
        return (
          <div key={d.name} style={{ position: "absolute", left: M, top: y, height: barH, width: W - 2 * M }}>
            {/* TÊN — cột trái, canh phải, không chồng thanh */}
            <div style={{ position: "absolute", left: 0, width: labelW - 16, height: barH, display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 12, fontSize: lblFs, fontWeight: 800, color: "#EAF2FF", overflow: "hidden" }}>
              {bimg
                ? <Img src={staticFile(bimg)} style={{ height: barH * 1.15, width: port ? 56 : 50, objectFit: "contain", objectPosition: "bottom", flexShrink: 0 }} />
                : logo
                ? <div style={{ width: chip, height: chip, borderRadius: 10, background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden", flexShrink: 0, boxShadow: "0 2px 8px #0006" }}><Img src={staticFile(logo)} style={{ width: "82%", height: "82%", objectFit: "contain" }} /></div>
                : (ic ? <span style={{ fontSize: port ? 42 : 40 }}>{ic}</span> : null)}
              <span style={{ whiteSpace: "nowrap" }}>{d.name}</span>
            </div>
            {/* THANH */}
            <div style={{ position: "absolute", left: labelW, top: 0, height: barH, width: w, background: `linear-gradient(90deg,${col},${col}CC)`, borderRadius: 12, boxShadow: `0 6px 22px ${col}44` }} />
            {/* SỐ — cuối thanh (+ 👑 cho #1) */}
            <div style={{ position: "absolute", left: labelW + w + 14, top: 0, height: barH, display: "flex", alignItems: "center", gap: 10, fontSize: port ? 38 : 34, fontWeight: 900, color: col, whiteSpace: "nowrap" }}>
              <span>{unit === "$" ? "$" : ""}{fmt(d.value)}{unit && unit !== "$" ? " " + unit : ""}</span>
              {rank === 0 ? <span style={{ fontSize: port ? 40 : 36 }}>👑</span> : null}
            </div>
          </div>
        );
      })}
      {/* CALLOUT SOÁN NGÔI — pop-up kịch tính giữa trên */}
      {callout ? (
        <div style={{ position: "absolute", top: port ? 300 : 168, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: calloutP, transform: `scale(${0.9 + calloutP * 0.1})` }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14, padding: port ? "16px 30px" : "13px 26px", background: "linear-gradient(90deg,#F5B301,#EC4899)", borderRadius: 999, boxShadow: "0 10px 30px #0008", fontSize: port ? 36 : 30, fontWeight: 900, color: "#0b1020", whiteSpace: "nowrap" }}>
            🏆 {callout.name} takes the lead!
          </div>
        </div>
      ) : null}
      {/* HERO — toà #1 hiện lớn bên phải, đổi theo leader (dễ hình dung) */}
      {hero ? (
        <div key={hero.name} style={{ position: "absolute", right: M, top: topPad, width: heroW - 30, height: H - topPad - bottomM, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", opacity: interpolate(f, [0, 14], [0, 1], { extrapolateRight: "clamp" }) }}>
          {photos?.[hero.name]
            ? <div style={{ height: "68%", aspectRatio: "0.66", borderRadius: 22, overflow: "hidden", border: `3px solid ${colorOf(hero.name, colors)}`, boxShadow: `0 0 46px ${colorOf(hero.name, colors)}77, 0 16px 40px #0009` }}><Img src={staticFile(photos[hero.name])} style={{ width: "100%", height: "100%", objectFit: "cover" }} /></div>
            : images?.[hero.name]
            ? <Img src={staticFile(images[hero.name])} style={{ height: "66%", width: "auto", maxWidth: "80%", objectFit: "contain", objectPosition: "bottom", filter: `drop-shadow(0 0 34px ${colorOf(hero.name, colors)}aa)` }} />
            : logos?.[hero.name]
            ? <div style={{ width: "62%", aspectRatio: "1", borderRadius: 30, background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 0 46px ${colorOf(hero.name, colors)}88, 0 16px 40px #0009` }}><Img src={staticFile(logos[hero.name])} style={{ width: "74%", height: "74%", objectFit: "contain" }} /></div>
            : themePhotos?.[hero.name]
            ? <div key={themePhotos[hero.name]} style={{ height: "62%", aspectRatio: "1.1", borderRadius: 22, overflow: "hidden", border: `3px solid ${colorOf(hero.name, colors)}`, boxShadow: `0 0 46px ${colorOf(hero.name, colors)}77, 0 16px 40px #0009` }}><Img src={staticFile(themePhotos[hero.name])} style={{ width: "100%", height: "100%", objectFit: "cover" }} /></div>
            : coldPhoto
            ? <div style={{ height: "62%", aspectRatio: "1.1", borderRadius: 22, overflow: "hidden", border: `3px solid ${colorOf(hero.name, colors)}`, boxShadow: `0 0 46px ${colorOf(hero.name, colors)}77, 0 16px 40px #0009` }}><Img src={staticFile(coldPhoto)} style={{ width: "100%", height: "100%", objectFit: "cover" }} /></div>
            : null}
          <div style={{ marginTop: 18, fontSize: 34, fontWeight: 900, color: "#EAF2FF", textAlign: "center", lineHeight: 1.1 }}>{hero.name}</div>
          <div style={{ fontSize: 50, fontWeight: 900, color: colorOf(hero.name, colors) }}>{unit === "$" ? "$" : ""}{fmt(hero.value)}{unit && unit !== "$" ? " " + unit : ""}</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: "#5B7290", letterSpacing: 3, marginTop: 2 }}>#1 NOW</div>
        </div>
      ) : null}
      {/* chân: nguồn + handle */}
      {source ? <div style={{ position: "absolute", bottom: port ? 70 : 40, left: M, fontSize: port ? 30 : 26, color: "#5B7290" }}>Source: {source}</div> : null}
      {handle ? <div style={{ position: "absolute", bottom: port ? 70 : 40, right: M, fontSize: port ? 32 : 28, fontWeight: 800, color: "#7FA8D0" }}>{handle}</div> : null}
      {music ? <Audio src={staticFile(music)} volume={0.12} /> : null}
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {/* SFX khớp dữ liệu: whoosh+ding mỗi lần soán ngôi, cheer lúc kết */}
      {sfx ? overtakeT.map((t, i) => (
        <React.Fragment key={"sfx" + i}>
          <Sequence from={Math.max(0, Math.round((t - 0.12) * fps))} durationInFrames={18}><Audio src={staticFile("sfx/whoosh.mp3")} volume={0.5} /></Sequence>
          <Sequence from={Math.round(t * fps)} durationInFrames={18}><Audio src={staticFile("sfx/ding.mp3")} volume={0.55} /></Sequence>
        </React.Fragment>
      )) : null}
      {sfx ? <Sequence from={Math.round(finalT * fps)} durationInFrames={60}><Audio src={staticFile("sfx/cheer.mp3")} volume={0.32} /></Sequence> : null}
          {subs && subs.length ? <Karaoke subs={subs} accent={accent} /> : null}
    </AbsoluteFill>
  );
};
