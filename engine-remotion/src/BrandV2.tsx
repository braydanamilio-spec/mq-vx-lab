import { AbsoluteFill } from "remotion";
import React from "react";

// Brand v2 — MỖI KÊNH 1 MOTIF/ICON KHÁC HẲN (không chỉ đổi màu). name/tagline/handle/accent/motif/layout.
type P = { kind?: "banner" | "avatar" | "watermark"; name?: string; tagline?: string;
  handle?: string; accent?: string; motif?: string; layout?: "left" | "center" };

// ICON theo motif (SVG đơn giản, sắc, tô theo accent)
export const Icon: React.FC<{ m: string; c: string; s: number }> = ({ m, c, s }) => {
  const p = { stroke: c, strokeWidth: 7, fill: "none", strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  const fill = { fill: c };
  const svg = (children: React.ReactNode) => <svg width={s} height={s} viewBox="0 0 100 100">{children}</svg>;
  switch (m) {
    case "coins":   return svg(<><ellipse cx="50" cy="30" rx="30" ry="12" {...fill} /><path d="M20 30v22c0 7 13 12 30 12s30-5 30-12V30" {...p} /><path d="M20 41c0 7 13 12 30 12s30-5 30-12" {...p} /></>);
    case "field":   return svg(<><rect x="14" y="20" width="72" height="60" rx="4" {...p} /><line x1="50" y1="20" x2="50" y2="80" {...p} /><circle cx="50" cy="50" r="12" {...p} /></>);
    case "film":    return svg(<><polygon points="38,28 38,72 74,50" {...fill} /><circle cx="50" cy="50" r="34" {...p} /></>);
    case "map":     return svg(<><path d="M50 84C30 62 22 48 22 36a28 28 0 0156 0c0 12-8 26-28 48z" {...p} /><circle cx="50" cy="36" r="10" {...fill} /></>);
    case "pulse":   return svg(<polyline points="12,52 34,52 44,26 56,74 66,52 88,52" {...p} />);
    case "road":    return svg(<><path d="M34 84 46 20h8l12 64" {...p} /><line x1="50" y1="30" x2="50" y2="38" {...p} /><line x1="50" y1="48" x2="50" y2="58" {...p} /><line x1="50" y1="68" x2="50" y2="78" {...p} /></>);
    case "plate":   return svg(<><circle cx="50" cy="50" r="32" {...p} /><circle cx="50" cy="50" r="15" {...p} /></>);
    case "chip":    return svg(<><rect x="28" y="28" width="44" height="44" rx="6" {...p} />{[36, 50, 64].map(v => <React.Fragment key={v}><line x1={v} y1="14" x2={v} y2="28" {...p} /><line x1={v} y1="72" x2={v} y2="86" {...p} /><line x1="14" y1={v} x2="28" y2={v} {...p} /><line x1="72" y1={v} x2="86" y2={v} {...p} /></React.Fragment>)}</>);
    case "receipt": return svg(<><path d="M30 16h40v68l-8-6-6 6-6-6-6 6-6-6-8 6z" {...p} /><line x1="40" y1="36" x2="60" y2="36" {...p} /><line x1="40" y1="50" x2="60" y2="50" {...p} /></>);
    // 25/8 — 14 motif thêm cho thế hệ 2: 10 motif cũ chia cho 24 niche thì thú cưng, vũ trụ,
    // toà án… phải dùng chung biểu tượng, nhìn là không ra chủ đề. Mỗi niche một dấu riêng.
    case "gamepad": return svg(<><rect x="14" y="36" width="72" height="34" rx="16" {...p} /><line x1="32" y1="46" x2="32" y2="60" {...p} /><line x1="25" y1="53" x2="39" y2="53" {...p} /><circle cx="66" cy="49" r="4" {...fill} /><circle cx="74" cy="58" r="4" {...fill} /></>);
    case "paw":     return svg(<><ellipse cx="50" cy="64" rx="20" ry="16" {...fill} /><circle cx="30" cy="42" r="8" {...fill} /><circle cx="44" cy="32" r="8" {...fill} /><circle cx="58" cy="32" r="8" {...fill} /><circle cx="70" cy="42" r="8" {...fill} /></>);
    case "rocket":  return svg(<><path d="M50 14c12 10 18 24 18 38l-8 12H40l-8-12c0-14 6-28 18-38z" {...p} /><circle cx="50" cy="42" r="7" {...p} /><path d="M40 64l-8 16 12-6M60 64l8 16-12-6" {...p} /></>);
    case "storm":   return svg(<><path d="M28 52a16 16 0 0110-28 20 20 0 0138 6 14 14 0 012 28H34" {...p} /><polygon points="52,60 42,78 50,78 46,92 62,72 54,72 60,60" {...fill} /></>);
    case "scale":   return svg(<><line x1="50" y1="18" x2="50" y2="84" {...p} /><line x1="22" y1="30" x2="78" y2="30" {...p} /><path d="M22 30l-10 22h20zM78 30l-10 22h20z" {...p} /><line x1="34" y1="84" x2="66" y2="84" {...p} /></>);
    case "note":    return svg(<><path d="M40 72V26l32-8v46" {...p} /><ellipse cx="32" cy="74" rx="10" ry="8" {...fill} /><ellipse cx="64" cy="66" rx="10" ry="8" {...fill} /></>);
    case "shield":  return svg(<><path d="M50 14l30 10v24c0 20-13 32-30 38-17-6-30-18-30-38V24z" {...p} /><path d="M38 50l9 9 17-18" {...p} /></>);
    case "cap":     return svg(<><path d="M12 40l38-16 38 16-38 16z" {...p} /><path d="M28 48v18c0 6 10 10 22 10s22-4 22-10V48" {...p} /><line x1="84" y1="43" x2="84" y2="64" {...p} /></>);
    case "house":   return svg(<><path d="M18 50L50 22l32 28" {...p} /><path d="M28 46v34h44V46" {...p} /><rect x="44" y="58" width="14" height="22" {...p} /></>);
    case "heart":   return svg(<path d="M50 82C26 64 16 52 16 40a17 17 0 0134-8 17 17 0 0134 8c0 12-10 24-34 42z" {...p} />);
    case "plane":   return svg(<path d="M10 54l80-26-16 30 8 24-16-14-22 12 4-16z" {...p} />);
    case "flask":   return svg(<><path d="M42 16v26L22 76a8 8 0 007 12h42a8 8 0 007-12L58 42V16" {...p} /><line x1="38" y1="16" x2="62" y2="16" {...p} /><line x1="32" y1="60" x2="68" y2="60" {...p} /></>);
    case "ghost":   return svg(<><path d="M24 84V46a26 26 0 0152 0v38l-10-8-8 8-8-8-8 8z" {...p} /><circle cx="40" cy="46" r="4" {...fill} /><circle cx="60" cy="46" r="4" {...fill} /></>);
    case "lens":    return svg(<><circle cx="44" cy="44" r="24" {...p} /><line x1="62" y1="62" x2="84" y2="84" {...p} /><path d="M36 38a10 10 0 018-6" {...p} /></>);
    default:        return svg(<g>{[0, 1, 2, 3].map(i => <rect key={i} x={18 + i * 18} y={70 - [30, 46, 62, 40][i]} width="12" height={[30, 46, 62, 40][i]} rx="3" {...fill} />)}</g>); // bars (race)
  }
};

export const BrandV2: React.FC<P> = ({ kind = "banner", name = "DATA RACE", tagline = "", handle = "@ch", accent = "#F5B301", motif = "bars", layout = "center" }) => {
  const bg = "radial-gradient(120% 100% at 50% 0%, #131a30 0%, #0b1020 45%, #070a14 100%)";
  const two = name.split(" ").join("\n");
  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: bg, fontFamily: "'Poppins',Arial", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 20 }}>
        <Icon m={motif} c={accent} s={300} />
        <div style={{ fontSize: name.length > 12 ? 92 : 116, fontWeight: 900, color: "#EAF2FF", lineHeight: 0.9, letterSpacing: -3, textAlign: "center", whiteSpace: "pre-line" }}>{two}</div>
      </AbsoluteFill>
    );
  }
  if (kind === "watermark") {
    return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}><Icon m={motif} c={accent} s={130} /></AbsoluteFill>;
  }
  const left = layout === "left";
  // 25/8 — VÙNG AN TOÀN. Bản cũ đẩy nội dung ra `padding: 0 160px`, tức x=160 trên canvas 2560,
  // trong khi YouTube chỉ CHẮC CHẮN hiện ô 1235x338 GIỮA banner (x 662→1897) trên TV và điện
  // thoại. Đo trên bản render thật: tên kênh bắt đầu ở x≈397 và icon ở x≈186 -> cả hai nằm ngoài,
  // người xem trên điện thoại thấy banner cụt đầu. Nay mọi thứ bó trong ô an toàn, `left` chỉ còn
  // đổi cách canh BÊN TRONG ô đó.
  const AN_TOAN: Record<string, number> = { banner: 1235, fb_cover: 640 };
  const oRong = AN_TOAN[kind] || 1235;
  const iconS = kind === "fb_cover" ? 110 : 190;
  // Tên dài phải tự co: "AMERICA LOOKED UP" ở cỡ 150 rộng ~1580px, tràn hẳn ô an toàn.
  const conLai = oRong - iconS - 44;
  const coChu = Math.max(56, Math.min(name.length > 12 ? 150 : 190,
    Math.floor(conLai / (Math.max(name.length, 1) * 0.6))));
  return (
    <AbsoluteFill style={{ background: bg, fontFamily: "'Poppins',Arial", justifyContent: "center", alignItems: "center" }}>
      <div style={{ width: oRong, display: "flex", alignItems: "center", gap: 44,
                    justifyContent: left ? "flex-start" : "center" }}>
        <Icon m={motif} c={accent} s={iconS} />
        <div style={{ textAlign: left ? "left" : "center", minWidth: 0 }}>
          <div style={{ fontSize: coChu, fontWeight: 900, color: "#EAF2FF", letterSpacing: -5, lineHeight: 0.9, whiteSpace: "nowrap" }}>{name}</div>
          <div style={{ fontSize: Math.round(coChu * 0.33), fontWeight: 700, color: "#9FC0E6", marginTop: 14 }}>{tagline}</div>
          <div style={{ fontSize: Math.round(coChu * 0.25), fontWeight: 800, color: accent, marginTop: 6 }}>{handle}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
