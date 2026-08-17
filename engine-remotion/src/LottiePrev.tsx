import React, { useEffect, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, staticFile, useCurrentFrame } from "remotion";
import { Lottie } from "@remotion/lottie";

// Preview 1 Lottie theo prop `file` (trong public/lottie/) — để xem animation vẽ gì.
export const LottiePrev: React.FC<{ file?: string }> = ({ file = "a.json" }) => {
  const [data, setData] = useState<any>(null);
  const [h] = useState(() => delayRender());
  useEffect(() => {
    fetch(staticFile(`lottie/${file}`)).then((r) => r.json()).then((j) => { setData(j); continueRender(h); }).catch(() => continueRender(h));
  }, [h, file]);
  return (
    <AbsoluteFill style={{ background: "linear-gradient(180deg,#eef2f8,#dce6f2)", justifyContent: "center", alignItems: "center" }}>
      {data && <Lottie animationData={data} style={{ width: 900, height: 900 }} loop />}
    </AbsoluteFill>);
};
