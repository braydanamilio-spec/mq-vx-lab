import React from "react";
import { AbsoluteFill, useVideoConfig, useCurrentFrame } from "remotion";
import { SceneGen, heroFor } from "./scenegen";
import { StickFigure, POSES, live } from "./StickAnim";

// Test dàn cảnh tự sinh: đổi seed => phòng khác hẳn, KHÔNG vẽ SVG mới.
export const GenDemo: React.FC<{ arch?: string; seed?: number; channel?: string; nar?: string; paletteIndex?: number }>
  = ({ arch = "office", seed = 1, channel = "broke", nar = "", paletteIndex }) => {
  const { width, height } = useVideoConfig();
  const frame = useCurrentFrame();
  const time = frame / 30;
  const wide = width > height;
  const floorPct = wide ? 0.84 : 0.73;
  const hostScale = wide ? 2.35 : 3.4;
  const HOST = { outfit: "suit" as const, glasses: true, tie: "#1D63C7", shirt: "#39454F", pants: "#222C3A", skin: "#F1B784", hair: "#3A2A20" };
  return (
    <AbsoluteFill style={{ background: "#dfe6ef" }}>
      <SceneGen arch={arch} seed={seed} channel={channel} hero={heroFor(nar)} width={width} height={height} floorPct={floorPct} wide={wide} time={time} paletteIndex={paletteIndex} />
      <svg viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute", inset: 0, width, height }}>
        <StickFigure x={width * 0.5} y={height * floorPct} scale={hostScale} pose={live(POSES.present, time, 0.3)} mouthOpen={0.3} expr="curious" blink={1} {...HOST} />
      </svg>
    </AbsoluteFill>);
};
