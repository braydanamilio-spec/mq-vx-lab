import React from "react";
import { AbsoluteFill, Img, useCurrentFrame, useVideoConfig, staticFile, interpolate, spring } from "remotion";
import { Karaoke } from "./Karaoke";

/**
 * SÂN KHẤU HOẠT HÌNH 2D — nhân vật rig + bối cảnh đa tầng, 30fps thật (25/8/2026).
 *
 * VÌ SAO KHÔNG DÙNG CÁCH CŨ
 * Bản thử 22/8 để FLUX vẽ lại cả nhân vật lẫn cảnh MỖI KHUNG rồi đổi ảnh theo nhịp thoại. Hai
 * hậu quả: nhân vật TRÔI (mỗi lần vẽ một tỉ lệ) và chuyển động chỉ là ảnh tĩnh nhảy. Ở đây
 * nhân vật là PNG tách nền vẽ SẴN MỘT LẦN (mascot_rig.py), còn mọi chuyển động do component này
 * tính lại từng khung — nên vừa hết trôi, vừa mượt thật.
 *
 * BỐN TẦNG CHUYỂN ĐỘNG (chồng lên nhau tạo cảm giác "phim", không phải "slideshow")
 *  1. MULTIPLANE  — nền tách 4 lớp sâu, camera pan/zoom thì lớp gần trượt nhanh hơn lớp xa
 *                   (nguyên lý camera đa tầng của Disney 1937). Đây là thứ tạo CHIỀU SÂU.
 *  2. KHÍ QUYỂN   — mây trôi, tia nắng quét, bụi bay: SVG/CSS thuần, 0 quota.
 *  3. DIỄN XUẤT   — nhân vật nhún theo nhịp thở, nghiêng người khi nói, nảy (squash & stretch)
 *                   ở chữ nhấn, đổi tư thế theo kịch bản.
 *  4. NHÉP MỒM    — đổi qua lại talk_closed/talk_open theo BIÊN ĐỘ TIẾNG THẬT (mảng `mouth`
 *                   do pipeline đo từ file audio), 12 lần/giây — mắt người đọc là "đang nói".
 *
 * Ai không nói thì `idle`/`smug` + nhún nhẹ — im mà vẫn sống, không đứng chết như ảnh dán.
 */

export type MascotShot = {
  stage: string;                 // tên sân khấu (thư mục trong public/stages/<KENH>/)
  layers: { lop: string; xa: number }[];   // lớp nền, xa: 0=đứng yên … 1=trượt nhanh nhất
  speaker?: string;              // id nhân vật đang nói (khớp thư mục public/mascots/<KENH>/<ID>)
  pose?: Record<string, string>; // id -> tư thế của người KHÔNG nói (idle/smug/react/point)
  from: number;                  // khung bắt đầu
  dur: number;                   // số khung
  cam?: "in" | "out" | "left" | "right" | "still";
  shake?: boolean;               // rung máy ở punchline
  line?: string;                 // câu thoại (phụ đề)
};

export type MascotProps = {
  channel: string;
  cast: { id: string; x: number; scale: number; flip?: boolean }[];
  shots: MascotShot[];
  mouth?: number[];              // biên độ mồm 0..1, 12 mẫu/giây (pipeline đo từ audio)
  title?: string;
  accent?: string;
  subs?: { t: number; d: number; w: string }[];   // karaoke từng chữ
};

const MOUTH_HZ = 12;             // 12 mẫu/giây: đủ để mắt đọc là "đang nói", không rung giật

/** Ảnh nhân vật: public/mascots/<KENH>/<ID>/<tư thế>.png */
const mascotSrc = (ch: string, id: string, pose: string) =>
  staticFile(`mascots/${ch.toUpperCase()}/${id.toUpperCase()}/${pose}.png`);

/** Lớp nền: public/stages/<KENH>/<sân khấu>/<lớp>.png */
const stageSrc = (ch: string, stage: string, lop: string) =>
  staticFile(`stages/${ch.toUpperCase()}/${stage}/${lop}.png`);

/** Camera của một cảnh: trả độ dịch (px) + phóng. Easing mượt, không tuyến tính thô. */
const camAt = (kind: string, t: number) => {
  const e = interpolate(t, [0, 1], [0, 1], { easing: (x) => 1 - Math.pow(1 - x, 3) });
  switch (kind) {
    case "in":    return { dx: 0, zoom: 1 + 0.10 * e };
    case "out":   return { dx: 0, zoom: 1.10 - 0.10 * e };
    case "left":  return { dx: -70 * e, zoom: 1.04 };
    case "right": return { dx: 70 * e, zoom: 1.04 };
    default:      return { dx: 0, zoom: 1.02 + 0.01 * e };   // "still" vẫn thở nhẹ — đứng im tuyệt đối là chết hình
  }
};

/** Bối cảnh đa tầng: mỗi lớp dịch theo `xa` -> chiều sâu thật khi camera động. */
const Multiplane: React.FC<{ ch: string; shot: MascotShot; t: number; f: number }> = ({ ch, shot, t, f }) => {
  const cam = camAt(shot.cam || "still", t);
  return (
    <AbsoluteFill>
      {shot.layers.map((L) => {
        // lớp càng GẦN (xa lớn) trượt càng nhiều và phóng càng mạnh — đó là parallax
        const dx = cam.dx * L.xa;
        const zoom = 1 + (cam.zoom - 1) * (0.55 + L.xa * 0.75);
        // lớp xa lay rất khẽ theo thời gian (gió/không khí), lớp gần đứng yên hơn
        const sway = L.xa < 0.2 ? Math.sin(f / 90) * 3 : 0;
        return (
          <AbsoluteFill key={L.lop} style={{ transform: `translateX(${dx + sway}px) scale(${zoom})` }}>
            <Img src={stageSrc(ch, shot.stage, L.lop)}
                 style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};

/** Khí quyển: bụi sáng bay + tia nắng quét. Thuần CSS/SVG — 0 quota, gần 0 CPU. */
const Khiquyen: React.FC<{ f: number; accent: string }> = ({ f, accent }) => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <AbsoluteFill style={{
      background: `linear-gradient(${75 + Math.sin(f / 180) * 6}deg, transparent 35%, ${accent}0D 50%, transparent 65%)`,
    }} />
    {Array.from({ length: 14 }).map((_, i) => {
      const sp = 0.25 + (i % 5) * 0.09;
      const x = ((i * 137 + f * sp) % 120) - 10;
      const y = 12 + ((i * 61) % 76) + Math.sin((f + i * 30) / 55) * 3;
      return <div key={i} style={{
        position: "absolute", left: `${x}%`, top: `${y}%`,
        width: 4 + (i % 3) * 2, height: 4 + (i % 3) * 2, borderRadius: "50%",
        background: "#FFFFFF", opacity: 0.10 + (i % 4) * 0.03, filter: "blur(1px)",
      }} />;
    })}
  </AbsoluteFill>
);

/** Một nhân vật: chọn tư thế + diễn xuất từng khung. */
const Actor: React.FC<{
  ch: string; id: string; x: number; scale: number; flip?: boolean;
  noi: boolean; pose: string; f: number; t: number; mo: number; fps: number;
}> = ({ ch, id, x, scale, flip, noi, pose, f, t, mo, fps }) => {
  // vào cảnh: nảy lên nhẹ (spring) thay vì hiện đột ngột
  const vao = spring({ frame: f, fps, config: { damping: 14, stiffness: 90 }, durationInFrames: 14 });
  // thở: cả người nhún rất khẽ, luôn luôn — kể cả lúc im
  const tho = Math.sin(f / 26) * 0.9;
  // đang nói thì nhún theo âm + nghiêng người nhẹ về phía trước
  const nhun = noi ? mo * 7 : 0;
  const nghieng = noi ? Math.sin(f / 9) * 1.6 : Math.sin(f / 70) * 0.5;
  // squash & stretch: mồm mở to = nhấn chữ -> người hơi bè ra rồi bật lại
  const sq = noi ? 1 + mo * 0.035 : 1;
  const st = noi ? 1 - mo * 0.025 : 1;
  const tuThe = noi ? (mo > 0.45 ? "talk_open" : "talk_closed") : pose;
  return (
    <div style={{
      position: "absolute", left: `${x}%`, bottom: `${2 + tho * 0.4}%`,
      transform: `translateX(-50%) translateY(${-nhun}px) rotate(${nghieng}deg) `
               + `scale(${scale * vao * sq}, ${scale * vao * st}) ${flip ? "scaleX(-1)" : ""}`,
      transformOrigin: "bottom center",
      height: `${72 * scale}%`,
      filter: noi ? "none" : "saturate(0.94) brightness(0.97)",   // người im lùi nhẹ về sau
    }}>
      <Img src={mascotSrc(ch, id, tuThe)} style={{ height: "100%", width: "auto" }} />
    </div>
  );
};

export const MascotStage: React.FC<MascotProps> = ({
  channel, cast, shots, mouth = [], title = "", accent = "#F5B301", subs = [],
}) => {
  const f = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const port = width < 1000;

  const shot = shots.find((s) => f >= s.from && f < s.from + s.dur) || shots[shots.length - 1];
  const fShot = Math.max(0, f - (shot?.from ?? 0));
  const t = Math.min(1, fShot / Math.max(1, shot?.dur ?? 1));

  // biên độ mồm tại khung hiện tại (mảng đo 12 mẫu/giây)
  const mi = Math.floor((f / fps) * MOUTH_HZ);
  const mo = Math.max(0, Math.min(1, mouth[mi] ?? 0));

  // rung máy ở punchline — biên độ tắt dần, không rung đều (rung đều trông giả)
  const rung = shot?.shake ? Math.sin(fShot / 1.6) * 7 * Math.max(0, 1 - fShot / 20) : 0;

  return (
    <AbsoluteFill style={{ background: "#0B0D12", fontFamily: "'Poppins',Arial", overflow: "hidden" }}>
      <AbsoluteFill style={{ transform: `translate(${rung}px, ${rung * 0.5}px)` }}>
        {shot && <Multiplane ch={channel} shot={shot} t={t} f={f} />}
        <Khiquyen f={f} accent={accent} />

        {cast.map((c) => (
          <Actor key={c.id} ch={channel} id={c.id} x={c.x} scale={c.scale} flip={c.flip}
                 noi={(shot?.speaker || "").toUpperCase() === c.id.toUpperCase()}
                 pose={(shot?.pose || {})[c.id.toUpperCase()] || "idle"}
                 f={f} t={t} mo={mo} fps={fps} />
        ))}

        {/* nền tối rất mỏng ở đáy để phụ đề luôn đọc được, KHÔNG dìm cả khung */}
        <AbsoluteFill style={{
          background: "linear-gradient(180deg, rgba(0,0,0,0) 62%, rgba(0,0,0,0.34) 100%)",
          pointerEvents: "none",
        }} />
      </AbsoluteFill>

      {title ? (
        <div style={{
          position: "absolute", top: port ? 64 : 40, left: 0, right: 0, textAlign: "center",
          fontSize: port ? 52 : 44, fontWeight: 900, color: "#fff", letterSpacing: -1,
          textShadow: `0 3px 0 rgba(0,0,0,.55), 0 0 26px ${accent}66`, padding: "0 60px",
        }}>{title}</div>
      ) : null}

      <Karaoke subs={subs} accent={accent} />
    </AbsoluteFill>
  );
};

export default MascotStage;
