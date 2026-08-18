import { AbsoluteFill } from "remotion";
import React from "react";

// Brand kênh GUESS (đố/đoán). Motif: mảnh ghép mở dần + kính lúp + dấu "?". Palette đồng bộ video.
type Kind = "banner" | "avatar" | "watermark" | "thumb";
const BG = "radial-gradient(120% 100% at 50% 0%, #141827 0%, #0b0e17 48%, #06080e 100%)";
const YEL = "#F5B301", PINK = "#ff375f";

// lưới ô ghép: vài ô "đã mở" (viền hồng glow), phần còn che tối -> nhận diện ngay là game đố
const Mosaic: React.FC<{ size: number; cols?: number; open?: number[] }> = ({ size, cols = 5, open = [] }) => {
  const n = cols * cols; const cell = size / cols;
  return (
    <div style={{ position: "relative", width: size, height: size, borderRadius: 18, overflow: "hidden", transform: "rotate(-7deg)", boxShadow: "0 18px 60px #000a" }}>
      {Array.from({ length: n }).map((_, i) => {
        const isOpen = open.includes(i);
        const dark = (Math.floor(i / cols) + i) % 2 ? "#12162100" : "#0b0e1700";
        return <div key={i} style={{ position: "absolute", left: (i % cols) * cell, top: Math.floor(i / cols) * cell, width: cell, height: cell,
          background: isOpen ? "transparent" : `linear-gradient(135deg,#161b29,#0a0d15)`,
          border: isOpen ? `${Math.max(2, size / 220)}px solid ${PINK}` : "1px solid #ffffff0e",
          boxShadow: isOpen ? `0 0 ${size / 26}px ${PINK}cc inset, 0 0 ${size / 30}px ${PINK}88` : "none" }} />;
      })}
    </div>
  );
};

export const BrandGuess: React.FC<{ kind?: Kind; name?: string; tagline?: string; handle?: string; topLine?: string; bigLine?: string }> =
  ({ kind = "banner", name = "GUESS", tagline = "Can you get them all?", handle = "@guessdaily", topLine, bigLine }) => {

  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
        <div style={{ position: "relative", width: 300, height: 300, marginBottom: 26 }}>
          <Mosaic size={300} cols={5} open={[6, 7, 12, 18]} />
          <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 150, filter: "drop-shadow(0 8px 24px #000a)" }}>🤔</div>
        </div>
        <div style={{ fontSize: 150, fontWeight: 900, color: "#fff", letterSpacing: -4, lineHeight: 0.85, textShadow: `0 0 40px ${YEL}66` }}>{name}</div>
        <div style={{ marginTop: 10, background: YEL, color: "#0a0c14", fontWeight: 900, fontSize: 40, padding: "6px 26px", borderRadius: 30 }}>?</div>
      </AbsoluteFill>
    );
  }

  if (kind === "watermark") {
    return (
      <AbsoluteFill style={{ background: "transparent", alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: 118, height: 118 }}><Mosaic size={118} cols={4} open={[2, 5, 9]} /></div>
      </AbsoluteFill>
    );
  }

  if (kind === "thumb") {
    // THUMBNAIL video: câu hỏi to + mảnh ghép -> click ngay
    return (
      <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial" }}>
        <div style={{ position: "absolute", right: -60, top: -40, opacity: 0.9 }}><Mosaic size={760} cols={6} open={[8, 9, 14, 20, 21, 27]} /></div>
        <div style={{ position: "absolute", left: 70, top: 90 }}>
          <div style={{ display: "inline-block", background: YEL, color: "#0a0c14", fontWeight: 900, fontSize: 46, padding: "10px 30px", borderRadius: 16, letterSpacing: 1 }}>GUESS THIS?</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 118, lineHeight: 0.98, marginTop: 26, maxWidth: 760, textShadow: "0 6px 30px #000c" }}>{bigLine || "CAN YOU\nNAME IT?"}</div>
          <div style={{ marginTop: 26, color: PINK, fontWeight: 900, fontSize: 60 }}>{topLine || "99% FAIL 👀"}</div>
        </div>
      </AbsoluteFill>
    );
  }

  // BANNER (2560x1440) — vùng an toàn giữa
  return (
    <AbsoluteFill style={{ background: BG, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center" }}>
      <div style={{ position: "absolute", left: 180, top: "50%", transform: "translateY(-50%)" }}><Mosaic size={420} cols={5} open={[6, 7, 11, 12, 18]} /></div>
      <div style={{ position: "absolute", right: 180, top: "50%", transform: "translateY(-50%) rotate(7deg)" }}><Mosaic size={340} cols={4} open={[1, 5, 10]} /></div>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: 300, fontWeight: 900, color: "#fff", letterSpacing: -10, lineHeight: 0.85, textShadow: `0 0 60px ${YEL}55` }}>{name}</div>
        <div style={{ marginTop: 24, display: "inline-block", background: YEL, color: "#0a0c14", fontWeight: 900, fontSize: 60, padding: "12px 44px", borderRadius: 40 }}>{tagline}</div>
        <div style={{ marginTop: 26, color: "#9aa4b8", fontWeight: 800, fontSize: 44 }}>{handle}</div>
      </div>
    </AbsoluteFill>
  );
};
