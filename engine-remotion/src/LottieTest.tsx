import React, { useEffect, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, staticFile, useCurrentFrame, interpolate } from "remotion";
import { Lottie } from "@remotion/lottie";

// PROOF: nhúng Lottie pro làm sẵn (free) vào engine — nền tối RANKED, có tiêu đề + handle.
export const LottieTest: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [handle] = useState(() => delayRender("lottie"));
  const f = useCurrentFrame();
  useEffect(() => {
    fetch(staticFile("assets/wb/growth.json"))
      .then((r) => r.json())
      .then((j) => { setData(j); continueRender(handle); })
      .catch(() => continueRender(handle));
  }, [handle]);
  const titleP = interpolate(f, [4, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ fontFamily: "'Poppins',Arial", background: "radial-gradient(60% 60% at 50% 38%, #3e61ab 0%, #273f84 55%, #1a2b57 100%)" }}>
      <div style={{ position: "absolute", top: 90, left: 0, right: 0, textAlign: "center", opacity: titleP, transform: `translateY(${(1 - titleP) * 20}px)` }}>
        <div style={{ fontSize: 92, fontWeight: 900, color: "#EAF2FF", letterSpacing: 4, textShadow: "0 0 30px rgba(124,92,255,0.5)" }}>MARKET GROWTH</div>
        <div style={{ width: 150, height: 8, background: "#8B5CF6", borderRadius: 6, margin: "18px auto 0", boxShadow: "0 0 24px #8B5CF6" }} />
      </div>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", top: 80 }}>
        {data && <Lottie animationData={data} style={{ width: 820, height: 820 }} loop />}
      </AbsoluteFill>
      <div style={{ position: "absolute", top: 30, right: 40, color: "#ffffffcc", fontSize: 30, fontWeight: 800 }}>@rankedcharts</div>
    </AbsoluteFill>
  );
};
