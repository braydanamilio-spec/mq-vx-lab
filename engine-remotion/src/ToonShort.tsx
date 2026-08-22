/**
 * ToonShort — skit hoạt hình 2 nhân vật (BALD & BANDIT / HANKTOWN), format 22/8:
 * 3-5 KHUNG ẢNH TĨNH của cùng một cảnh (FLUX vẽ, đổi biểu cảm + 1 khung cận) chuyển theo
 * NHỊP THOẠI + zoom nhẹ, title card đỉnh (đè luôn vùng chữ giả FLUX hay tự chế), phụ đề
 * từng câu ở đáy theo màu nhân vật, whoosh khi đổi khung, nhạc nền nhỏ.
 *
 * Props (python make_toon dựng sẵn, mọi file nằm public/{slug}/):
 *   slug, title, color (accent kênh), name (tên kênh),
 *   frames: [{img, from, dur}]            — khung hình theo frame 30fps
 *   lines:  [{audio, text, who, from, dur}] — mỗi câu thoại 1 file mp3 + phụ đề
 *   music?: đường dẫn nhạc nền (staticFile), watermark?: logo nhỏ góc
 */
import { AbsoluteFill, Audio, Img, Sequence, staticFile, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import React from "react";

const FB_IMG = staticFile("img/_fallback.jpg");
const SafeImg: React.FC<{ src: string; style?: React.CSSProperties }> = ({ src, style }) => {
  const [s, setS] = React.useState(src);
  return <Img src={s} style={style} onError={() => setS(FB_IMG)} pauseWhenLoading />;
};

type Frame = { img: string; from: number; dur: number };
type Line = { audio: string; text: string; who: string; from: number; dur: number };

export const ToonShort: React.FC<{
  slug: string; title: string; color?: string; name?: string;
  frames: Frame[]; lines: Line[]; music?: string; whoColors?: Record<string, string>;
}> = ({ slug, title, color = "#E4562B", name = "", frames = [], lines = [], music = "", whoColors = {} }) => {
  const f = useCurrentFrame();
  const { durationInFrames: total } = useVideoConfig();
  const ci = (x: number, a: number, b: number, c: number, d: number) =>
    interpolate(x, [a, b], [c, d], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const cur = lines.find(l => f >= l.from && f < l.from + l.dur);
  return (
    <AbsoluteFill style={{ background: "#0e0e12", fontFamily: "Arial, sans-serif" }}>
      {frames.map((fr, i) => {
        const rel = f - fr.from;
        const zoom = 1.02 + 0.035 * Math.min(1, Math.max(0, rel / Math.max(1, fr.dur)));
        return (
          <Sequence key={i} from={fr.from} durationInFrames={fr.dur}>
            <AbsoluteFill style={{ transform: `scale(${zoom})` }}>
              <SafeImg src={staticFile(`${slug}/${fr.img}`)}
                style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            </AbsoluteFill>
            {i > 0 && <Audio src={staticFile("sfx/whoosh.mp3")} volume={0.35} />}
          </Sequence>
        );
      })}
      {/* TITLE CARD đỉnh — nền mờ đè vùng biển hiệu (chữ giả FLUX nếu lọt cũng bị che) */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 64 }}>
        <div style={{
          maxWidth: 940, padding: "18px 34px", borderRadius: 22, background: "rgba(10,10,14,0.72)",
          border: `3px solid ${color}`, color: "#fff", fontSize: 56, fontWeight: 900,
          textAlign: "center", lineHeight: 1.15, textShadow: "0 3px 14px rgba(0,0,0,.6)",
          opacity: ci(f, 0, 12, 0, 1),
        }}>{title}</div>
      </AbsoluteFill>
      {/* PHỤ ĐỀ theo câu — màu theo nhân vật */}
      {cur && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 170 }}>
          <div style={{
            maxWidth: 920, padding: "16px 30px", borderRadius: 18,
            background: "rgba(10,10,14,0.78)", color: whoColors[cur.who] || "#fff",
            fontSize: 47, fontWeight: 800, textAlign: "center", lineHeight: 1.22,
            border: `2px solid ${whoColors[cur.who] || color}55`,
          }}>{cur.text}</div>
        </AbsoluteFill>
      )}
      {/* watermark kênh */}
      {name && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-end", padding: 34 }}>
          <div style={{ color: "#ffffffc9", fontSize: 30, fontWeight: 800, letterSpacing: 1 }}>{name}</div>
        </AbsoluteFill>
      )}
      {lines.map((l, i) => (
        <Sequence key={"a" + i} from={l.from} durationInFrames={l.dur}>
          <Audio src={staticFile(`${slug}/${l.audio}`)} />
        </Sequence>
      ))}
      {music && <Audio src={staticFile(music)} loop
        volume={Math.min(ci(f, 0, 24, 0, 1), ci(f, total - 30, total, 1, 0)) * 0.09} />}
    </AbsoluteFill>
  );
};

export const calcToon = ({ props }: { props: any }) => {
  const fr = (props && props.frames) || [];
  const ln = (props && props.lines) || [];
  const endF = fr.length ? Math.max(...fr.map((x: any) => (x.from || 0) + (x.dur || 0))) : 300;
  const endL = ln.length ? Math.max(...ln.map((x: any) => (x.from || 0) + (x.dur || 0))) : 0;
  return { durationInFrames: Math.max(120, Math.max(endF, endL) + 18) };
};
