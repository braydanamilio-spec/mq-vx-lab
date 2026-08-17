import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";
import { loadFont } from "@remotion/google-fonts/Cinzel";
const { fontFamily: CINZEL } = loadFont(); // serif kiểu bia đá La Mã — chất "di sản/bất tử"

// LEGACY brand: navy sâu + vàng di sản + cream. banner 2560x1440 / avatar 800x800 / watermark 150x150.
const GOLD = "#E6B84C", CREAM = "#F3ECDA", NAVY0 = "#0C0F17", NAVY1 = "#05070C", STEEL = "#6FA8C9";

export const BrandLegacy: React.FC<{ kind?: string }> = ({ kind = "banner" }) => {
  const { width, height } = useVideoConfig();
  const banner = kind === "banner"; const mark = kind === "watermark"; const av = kind === "avatar";
  const S = Math.min(width, height);
  const titleSize = 260;
  const cy = height / 2;
  return (
    <AbsoluteFill style={{ background: `radial-gradient(60% 60% at 50% 42%, ${NAVY0} 0%, ${NAVY1} 100%)`, fontFamily: CINZEL, overflow: "hidden" }}>
      {/* tia sáng vàng mờ sau chữ */}
      <div style={{ position: "absolute", left: "50%", top: `${(cy / height) * 100}%`, transform: "translate(-50%,-50%)", width: S * 1.1, height: S * 1.1, borderRadius: "50%", background: `radial-gradient(circle, ${GOLD}22 0%, transparent 62%)` }} />
      {/* khung vàng cổ điển */}
      {!mark && <div style={{ position: "absolute", inset: banner ? 60 : 34, border: `${banner ? 4 : 3}px solid ${GOLD}`, opacity: 0.55 }} />}
      {!mark && <div style={{ position: "absolute", inset: banner ? 78 : 46, border: `1px solid ${GOLD}`, opacity: 0.3 }} />}

      {mark ? (
        // watermark: monogram L trong vòng
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ width: S * 0.82, height: S * 0.82, borderRadius: "50%", border: `${S * 0.05}px solid ${GOLD}`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 0 ${S * 0.15}px ${GOLD}66` }}>
            <div style={{ fontSize: S * 0.5, fontWeight: 900, color: GOLD, lineHeight: 1 }}>L</div>
          </div>
        </AbsoluteFill>
      ) : av ? (
        // avatar (hiển thị dạng TRÒN): monogram L lớn + LEGACY nhỏ, vừa khung
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12, opacity: 0.9 }}>
            {[0, 1, 2].map((i) => (<React.Fragment key={i}>{i > 0 && <div style={{ width: 34, height: 2, background: `${GOLD}77` }} />}<div style={{ width: 10, height: 10, borderRadius: "50%", background: i === 2 ? GOLD : STEEL, boxShadow: i === 2 ? `0 0 12px ${GOLD}` : "none" }} /></React.Fragment>))}
          </div>
          <div style={{ fontSize: S * 0.46, fontWeight: 900, color: GOLD, lineHeight: 0.9, textShadow: `0 4px 40px ${GOLD}55, 0 2px 8px #000` }}>L</div>
          <div style={{ fontSize: S * 0.115, fontWeight: 700, color: CREAM, letterSpacing: 6, marginTop: 18, opacity: 0.95 }}>LEGACY</div>
        </AbsoluteFill>
      ) : (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
          {/* mốc timeline nhỏ (motif data-moat) */}
          <div style={{ display: "flex", alignItems: "center", gap: banner ? 26 : 14, marginBottom: banner ? 40 : 26, opacity: 0.9 }}>
            {[0, 1, 2, 3, 4].map((i) => (
              <React.Fragment key={i}>
                {i > 0 && <div style={{ width: banner ? 90 : 40, height: 2, background: `${GOLD}77` }} />}
                <div style={{ width: banner ? 16 : 10, height: banner ? 16 : 10, borderRadius: "50%", background: i === 4 ? GOLD : STEEL, boxShadow: i === 4 ? `0 0 16px ${GOLD}` : "none" }} />
              </React.Fragment>
            ))}
          </div>
          <div style={{ fontSize: titleSize, fontWeight: 900, color: GOLD, letterSpacing: banner ? 24 : 6, lineHeight: 1, textShadow: `0 4px 40px ${GOLD}55, 0 2px 8px #000` }}>LEGACY</div>
          {banner && <div style={{ fontSize: 52, fontWeight: 600, color: CREAM, letterSpacing: 10, marginTop: 46, opacity: 0.92 }}>HOW GREATNESS WAS MADE</div>}
          {!banner && !mark && <div style={{ fontSize: S * 0.05, fontWeight: 600, color: CREAM, letterSpacing: 4, marginTop: 24, opacity: 0.9 }}>THE GREATS</div>}
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
