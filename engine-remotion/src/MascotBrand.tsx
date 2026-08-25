import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";

/**
 * BỘ NHẬN DIỆN 5 KÊNH HOẠT HÌNH (25/8/2026).
 *
 * Nguyên tắc: ảnh đại diện và ảnh bìa phải là CHÍNH nhân vật trong video, không phải một tranh vẽ
 * riêng. Khán giả lướt thấy avatar rồi bấm vào video — hai thứ khác mặt nhau là mất niềm tin ngay
 * giây đầu. Ở đây lấy thẳng PNG rig trong `public/mascots/` nên nhận diện khớp 100%, vĩnh viễn.
 *
 * VÙNG AN TOÀN CỦA YOUTUBE (lý do bìa hay bị cắt mất chữ)
 * Ảnh bìa 2560×1440 nhưng TV hiện gần hết, máy tính hiện 2560×423, điện thoại chỉ hiện
 * **1546×423 chính giữa**. Mọi chữ phải nằm trong ô 1546×423 đó, ngoài ra chỉ để hoạ tiết.
 */

type Kind = "avatar" | "banner" | "watermark" | "thumb" | "fbcover";

export type MascotBrandProps = {
  channel: string;      // EAGLEBANDIT…
  hero: string;         // id nhân vật chính (BALD…)
  hero2?: string;       // nhân vật phụ (BANDIT…)
  display?: string;     // tên hiển thị
  tagline?: string;
  handle?: string;
  accent?: string;
  accent2?: string;
  kind?: Kind;
};

const mascotSrc = (ch: string, id: string, pose: string) =>
  staticFile(`mascots/${ch.toUpperCase()}/${id.toUpperCase()}/${pose}.png`);

/** Nền hoạ tiết: tia toả + chấm bi — đọc được ở cỡ 98px lẫn 2560px. */
const Nen: React.FC<{ a: string; b: string; tia?: boolean }> = ({ a, b, tia = true }) => (
  <AbsoluteFill style={{ background: `radial-gradient(120% 120% at 50% 30%, ${b} 0%, ${a} 70%)` }}>
    {tia ? (
      <svg viewBox="0 0 100 100" preserveAspectRatio="none"
           style={{ position: "absolute", inset: 0, width: "100%", height: "100%", opacity: 0.14 }}>
        {Array.from({ length: 18 }).map((_, i) => {
          const ang = (i * 360) / 18;
          return <rect key={i} x="49.2" y="-60" width="1.6" height="160" fill="#fff"
            transform={`rotate(${ang} 50 50)`} />;
        })}
      </svg>
    ) : null}
  </AbsoluteFill>
);

export const MascotBrand: React.FC<MascotBrandProps> = ({
  channel, hero, hero2, display = "", tagline = "", handle = "",
  accent = "#E4562B", accent2 = "#2E6FD9", kind = "banner",
}) => {
  const F = "'Poppins', Arial, sans-serif";

  // ẢNH ĐẠI DIỆN — hiển thị bé tí (98px) nên: mặt TO, viền dày, nền tương phản, KHÔNG chữ.
  if (kind === "avatar" || kind === "watermark") {
    const wm = kind === "watermark";
    return (
      <AbsoluteFill style={{ overflow: "hidden", borderRadius: "50%" }}>
        <Nen a={accent2} b={accent} />
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-end" }}>
          <Img src={mascotSrc(channel, hero, "smug")}
               style={{ height: wm ? "88%" : "94%", width: "auto",
                        filter: "drop-shadow(0 10px 24px rgba(0,0,0,.45))" }} />
        </AbsoluteFill>
        {/* vành trong: giúp avatar không lẫn vào nền trắng/đen của giao diện YouTube */}
        <AbsoluteFill style={{
          borderRadius: "50%", boxShadow: "inset 0 0 0 18px rgba(255,255,255,.92)",
        }} />
      </AbsoluteFill>
    );
  }

  // ẢNH BÌA YOUTUBE — chữ phải nằm trong ô an toàn 1546×423 giữa khung 2560×1440.
  if (kind === "banner") {
    return (
      <AbsoluteFill style={{ fontFamily: F }}>
        <Nen a={accent2} b={accent} />
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ width: 1546, height: 423, display: "flex", alignItems: "center", gap: 44 }}>
            <div style={{ display: "flex", alignItems: "flex-end", height: "100%", flexShrink: 0 }}>
              <Img src={mascotSrc(channel, hero, "point")}
                   style={{ height: "112%", width: "auto", filter: "drop-shadow(0 14px 30px rgba(0,0,0,.5))" }} />
              {hero2 ? (
                <Img src={mascotSrc(channel, hero2, "smug")}
                     style={{ height: "98%", width: "auto", marginLeft: -34,
                              filter: "drop-shadow(0 14px 30px rgba(0,0,0,.5))" }} />
              ) : null}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 116, fontWeight: 900, color: "#fff", lineHeight: 0.96,
                            letterSpacing: -3, textShadow: "0 6px 0 rgba(0,0,0,.32)" }}>
                {display.toUpperCase()}
              </div>
              <div style={{ marginTop: 16, fontSize: 40, fontWeight: 700, color: "#FFF3C4" }}>
                {tagline}
              </div>
              <div style={{ marginTop: 22, display: "inline-block", background: "#111", color: "#fff",
                            fontSize: 30, fontWeight: 800, padding: "10px 22px", borderRadius: 999 }}>
                {handle} · new every day
              </div>
            </div>
          </div>
        </AbsoluteFill>
        {/* dải mép dưới: khung 2560 hiện trên TV — để hoạ tiết, tuyệt đối không để chữ */}
        <AbsoluteFill style={{ top: "auto", height: 90, background: "rgba(0,0,0,.28)" }} />
      </AbsoluteFill>
    );
  }

  // ẢNH BÌA FACEBOOK — vùng an toàn hẹp hơn, ảnh đại diện đè góc trái dưới trên di động.
  if (kind === "fbcover") {
    return (
      <AbsoluteFill style={{ fontFamily: F }}>
        <Nen a={accent2} b={accent} />
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 90px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 30, width: "100%" }}>
            <Img src={mascotSrc(channel, hero, "smug")}
                 style={{ height: 250, width: "auto", filter: "drop-shadow(0 8px 20px rgba(0,0,0,.45))" }} />
            <div>
              <div style={{ fontSize: 74, fontWeight: 900, color: "#fff", letterSpacing: -2 }}>
                {display.toUpperCase()}
              </div>
              <div style={{ fontSize: 27, fontWeight: 700, color: "#FFF3C4", marginTop: 6 }}>{tagline}</div>
            </div>
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }

  // KHUNG THUMBNAIL MẪU — chỗ để tiêu đề, giữ bố cục cố định cho cả kênh (nhận diện đồng nhất).
  return (
    <AbsoluteFill style={{ fontFamily: F }}>
      <Nen a={accent2} b={accent} tia={false} />
      <AbsoluteFill style={{ alignItems: "flex-end", justifyContent: "flex-end" }}>
        <Img src={mascotSrc(channel, hero, "react")} style={{ height: "96%", width: "auto" }} />
      </AbsoluteFill>
      <div style={{ position: "absolute", left: 56, top: 64, width: 700, fontSize: 92, fontWeight: 900,
                    color: "#fff", lineHeight: 1.02, letterSpacing: -2,
                    textShadow: "0 5px 0 rgba(0,0,0,.35)" }}>
        {tagline || display}
      </div>
    </AbsoluteFill>
  );
};

export default MascotBrand;
