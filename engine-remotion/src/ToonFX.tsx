import React, { useEffect, useState } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, staticFile, delayRender, continueRender, spring, interpolate } from "remotion";
import { Lottie } from "@remotion/lottie";

/**
 * TẦNG 5 — HIỆU ỨNG CARTOON (25/8/2026).
 *
 * Bốn tầng trước (multiplane · khí quyển · diễn xuất · nhép mồm) làm nhân vật SỐNG. Tầng này làm
 * nó BUỒN CƯỜI — và đây mới là thứ phân biệt "phim hoạt hình" với "hai hình dán biết nhúc nhích":
 * giọt mồ hôi khi bí, chùm sao khi choáng, gân giận, dấu hỏi lơ lửng, cú đập punchline, bụi tung.
 * Trong nghề gọi là "smear & symbol" — Tex Avery, Looney Tunes, và mọi phim hài 2D đều sống nhờ nó.
 *
 * HAI NGUỒN, TỰ CHỌN
 *  1. LOTTIE (nếu có file trong `public/lottie/fx/<tên>.json`): chuẩn hoạt hình vector của ngành
 *     (Airbnb mở nguồn), thư viện LottieFiles hàng chục nghìn animation miễn phí — thả file vào là
 *     dùng được ngay, không phải sửa code.
 *  2. SVG DỰNG SẴN (mặc định): không có file Lottie thì vẫn chạy. Quan trọng vì hệ phải render
 *     được NGAY trên runner sạch, không phụ thuộc tải tài nguyên ngoài — bài học "tính năng đẹp
 *     mà thiếu tài nguyên thì im lặng không hiện gì".
 *
 * Chi phí: 0 quota, ~0 CPU (vài chục hình SVG/khung).
 */

export type FxKind = "sweat" | "shock" | "anger" | "question" | "impact" | "dust" | "sparkle" | "none";

const FX_LOTTIE: Record<string, string> = {
  sweat: "fx/sweat.json", shock: "fx/shock.json", anger: "fx/anger.json",
  question: "fx/question.json", impact: "fx/impact.json", dust: "fx/dust.json",
  sparkle: "fx/sparkle.json",
};

/** Nạp Lottie nếu có; không có thì trả null để rơi về bản SVG. */
const useLottieFx = (kind: FxKind) => {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    const f = FX_LOTTIE[kind];
    if (!f) return;
    const h = delayRender(`fx:${kind}`);
    fetch(staticFile(`lottie/${f}`))
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setData(d))
      .catch(() => setData(null))
      .finally(() => continueRender(h));
  }, [kind]);
  return data;
};

/** Giọt mồ hôi: rơi xuống rồi tan — dấu hiệu "bí quá" kinh điển. */
const Sweat: React.FC<{ f: number }> = ({ f }) => {
  const t = (f % 45) / 45;
  return (
    <svg viewBox="0 0 100 100" style={{ width: "100%", height: "100%", overflow: "visible" }}>
      <path d="M50 20 C42 34, 36 42, 36 52 a14 14 0 0 0 28 0 c0-10-6-18-14-32z"
        fill="#7FD4FF" stroke="#1B4F7A" strokeWidth="3"
        opacity={1 - t} transform={`translate(0 ${t * 46}) scale(${1 - t * 0.25})`} />
    </svg>
  );
};

/** Chùm sao quay quanh đầu: "choáng". */
const Shock: React.FC<{ f: number }> = ({ f }) => (
  <svg viewBox="0 0 120 120" style={{ width: "100%", height: "100%", overflow: "visible" }}>
    {[0, 1, 2, 3, 4].map((i) => {
      const a = (f / 9 + (i * Math.PI * 2) / 5);
      const x = 60 + Math.cos(a) * 40, y = 40 + Math.sin(a) * 15;
      const s = 0.8 + Math.sin(f / 6 + i) * 0.25;
      return (
        <path key={i} transform={`translate(${x} ${y}) scale(${s}) translate(-10 -10)`}
          d="M10 0 L12.6 7 L20 7.6 L14.3 12.4 L16.2 20 L10 15.6 L3.8 20 L5.7 12.4 L0 7.6 L7.4 7 Z"
          fill="#FFD43B" stroke="#8A5A00" strokeWidth="1.6" />
      );
    })}
  </svg>
);

/** Gân giận (anger vein) — dấu hiệu bực trong hoạt hình Nhật/Mỹ, ai cũng đọc được. */
const Anger: React.FC<{ f: number }> = ({ f }) => {
  const p = 1 + Math.sin(f / 4) * 0.14;
  return (
    <svg viewBox="0 0 60 60" style={{ width: "100%", height: "100%", overflow: "visible" }}>
      <g transform={`translate(30 30) scale(${p}) translate(-30 -30)`} fill="none"
         stroke="#E23B3B" strokeWidth="5" strokeLinecap="round">
        <path d="M18 16 L30 26 L18 36" /><path d="M42 16 L30 26 L42 36" />
        <path d="M30 26 L30 44" />
      </g>
    </svg>
  );
};

/** Dấu hỏi bật lên rồi lắc — "hả?" */
const Question: React.FC<{ f: number; fps: number }> = ({ f, fps }) => {
  const s = spring({ frame: f, fps, config: { damping: 9, stiffness: 140 }, durationInFrames: 12 });
  const lac = Math.sin(f / 7) * 9;
  return (
    <svg viewBox="0 0 60 90" style={{ width: "100%", height: "100%", overflow: "visible" }}>
      <text x="30" y="66" textAnchor="middle" fontSize="72" fontWeight="900"
        fill="#FFD43B" stroke="#7A4E00" strokeWidth="4" paintOrder="stroke"
        transform={`translate(30 45) rotate(${lac}) scale(${s}) translate(-30 -45)`}>?</text>
    </svg>
  );
};

/** Vụ nổ tia (impact star) cho punchline — bung ra rồi tắt trong ~0.5s. */
const Impact: React.FC<{ f: number }> = ({ f }) => {
  const t = Math.min(1, f / 15);
  const s = interpolate(t, [0, 0.35, 1], [0.2, 1.18, 1.4]);
  const o = interpolate(t, [0, 0.3, 1], [0, 1, 0]);
  const tia = Array.from({ length: 12 }).map((_, i) => {
    const a = (i * Math.PI * 2) / 12;
    const r1 = 26, r2 = i % 2 ? 44 : 62;
    return `${50 + Math.cos(a) * r1} ${50 + Math.sin(a) * r1} L ${50 + Math.cos(a + 0.26) * r2} ${50 + Math.sin(a + 0.26) * r2} L`;
  }).join(" ");
  return (
    <svg viewBox="0 0 100 100" style={{ width: "100%", height: "100%", overflow: "visible" }}>
      <path d={`M ${tia} Z`} fill="#FFE066" stroke="#C2410C" strokeWidth="3"
        opacity={o} transform={`translate(50 50) scale(${s}) translate(-50 -50)`} />
    </svg>
  );
};

/** Bụi tung dưới chân khi nhân vật nhấn mạnh — làm nhân vật "có trọng lượng". */
const Dust: React.FC<{ f: number }> = ({ f }) => (
  <svg viewBox="0 0 140 60" style={{ width: "100%", height: "100%", overflow: "visible" }}>
    {[0, 1, 2, 3].map((i) => {
      const t = ((f + i * 7) % 32) / 32;
      const dir = i % 2 ? 1 : -1;
      return <ellipse key={i} cx={70 + dir * (14 + t * 44)} cy={44 - t * 16}
        rx={9 + t * 12} ry={7 + t * 8} fill="#D8CFC2" opacity={(1 - t) * 0.5} />;
    })}
  </svg>
);

/** Lấp lánh cho vẻ đắc chí. */
const Sparkle: React.FC<{ f: number }> = ({ f }) => (
  <svg viewBox="0 0 100 100" style={{ width: "100%", height: "100%", overflow: "visible" }}>
    {[0, 1, 2].map((i) => {
      const t = ((f + i * 11) % 30) / 30;
      const x = 22 + i * 28, y = 30 + (i % 2) * 22;
      const s = Math.sin(t * Math.PI) * 1.1;
      return <path key={i} transform={`translate(${x} ${y}) scale(${s}) translate(-8 -8)`}
        d="M8 0 L10 6 L16 8 L10 10 L8 16 L6 10 L0 8 L6 6 Z" fill="#FFFFFF" opacity={0.9} />;
    })}
  </svg>
);

/**
 * Một hiệu ứng neo vào vị trí nhân vật. `x` tính theo % bề ngang khung, `neo` = cao/thấp.
 * Có file Lottie thì dùng Lottie, không thì dùng bản SVG dựng sẵn.
 */
export const ToonFX: React.FC<{
  kind: FxKind; x: number; f: number; size?: number; neo?: "dau" | "chan";
}> = ({ kind, x, f, size = 16, neo = "dau" }) => {
  const { fps } = useVideoConfig();
  const lot = useLottieFx(kind);
  if (kind === "none") return null;
  const style: React.CSSProperties = {
    position: "absolute", left: `${x}%`,
    [neo === "dau" ? "top" : "bottom"]: neo === "dau" ? "12%" : "1%",
    width: `${size}%`, height: `${size}%`, transform: "translateX(-50%)",
    pointerEvents: "none",
  };
  if (lot) {
    return <div style={style}><Lottie animationData={lot} loop /></div>;
  }
  const body =
    kind === "sweat" ? <Sweat f={f} /> :
    kind === "shock" ? <Shock f={f} /> :
    kind === "anger" ? <Anger f={f} /> :
    kind === "question" ? <Question f={f} fps={fps} /> :
    kind === "impact" ? <Impact f={f} /> :
    kind === "dust" ? <Dust f={f} /> :
    kind === "sparkle" ? <Sparkle f={f} /> : null;
  return <div style={style}>{body}</div>;
};

/** Tư thế -> hiệu ứng hợp lý. Diễn viên đang làm gì thì hiện dấu hiệu đó, không rắc bừa. */
export const fxTheoTuThe = (pose: string, noi: boolean, punch: boolean): FxKind => {
  if (punch) return "impact";
  if (pose === "react") return "shock";
  if (pose === "smug") return "sparkle";
  if (pose === "point") return "anger";
  if (!noi && pose === "idle") return "none";
  return "none";
};

export default ToonFX;
