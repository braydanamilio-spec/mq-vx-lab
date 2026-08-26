import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";
import { phong } from "./Phong";
import { bienCua, hoaTietNen } from "./Bien";

/**
 * BỘ NHẬN DIỆN V3 — avatar / banner / watermark cho 50 kênh thế hệ 2 (26/8/2026).
 *
 * VÌ SAO LÀM LẠI. Xem tận mắt bản V2 render ra:
 *   • banner 2560×1440 mà **90% khung là nền tối trống** — nội dung dồn vào một cụm nhỏ giữa;
 *     phần ngoài vùng an toàn (thứ hiện trên TV và desktop) bỏ phí hoàn toàn;
 *   • **một khuôn cho cả 50 kênh**: icon trái + tên + tagline + handle, căn giữa;
 *   • motif không nói lên gì — kênh thu hồi thực phẩm, motif tên `plate`, vẽ ra vòng tròn đồng
 *     tâm, nhìn như bia bắn;
 *   • avatar là CHỮ HAI DÒNG, mà YouTube cắt avatar thành hình TRÒN và hiển thị ở 48px trên điện
 *     thoại — ở cỡ đó không đọc được gì.
 *
 * NGUYÊN TẮC BẢN NÀY: nền của mỗi kênh **phản chiếu đúng thứ kênh đó sản xuất**. Kênh xếp hạng ra
 * hàng tier, kênh đua ra cột đua, kênh bản đồ ra lưới bang, kênh so kích thước ra khối lớn nhỏ…
 * Nhìn banner là biết kênh làm gì — và 7 dạng cho ra 7 hệ hình khác hẳn nhau, nhân với 50 bảng màu
 * và 27 biến thể bố cục thì không kênh nào đụng kênh nào.
 *
 * KÍCH THƯỚC (chuẩn YouTube, không đoán):
 *   banner    2560×1440, vùng an toàn mọi thiết bị **1546×423** ở chính giữa -> CHỮ CHỈ ĐẶT TRONG ĐÓ
 *   avatar     800×800, bị cắt TRÒN -> mọi thứ phải nằm trong đường tròn nội tiếp
 *   watermark  150×150, nền trong suốt
 */
export type BrandV3Props = {
  kind?: "banner" | "avatar" | "watermark";
  name?: string;
  tagline?: string;
  handle?: string;
  dang?: string;            // ranked | race | mapped | scaled | thennow | longshot | cinematic
  accent?: string;          // palette.primary
  accent2?: string;         // palette.secondary
  bg?: string;              // palette.bg
  font?: string;
  bien?: number;
};

const _n = (s?: string, d = "#22D3EE") => (s && /^#/.test(s) ? s : d);

/** Chữ cái đầu của tối đa 2 từ — dấu hiệu đọc được ở 48px, khác hẳn wordmark hai dòng. */
const monogram = (ten: string) => {
  const w = String(ten || "").trim().split(/\s+/).filter(Boolean);
  if (!w.length) return "MM";
  if (w.length === 1) return w[0].slice(0, 2).toUpperCase();
  return (w[0][0] + w[1][0]).toUpperCase();
};

/** NỀN THEO DẠNG — mỗi dạng một hệ hình, vẽ bằng SVG nên sắc ở mọi kích thước. */
const NenDang: React.FC<{ dang: string; a: string; b: string; W: number; H: number; bien: number }> =
({ dang, a, b, W, H, bien }) => {
  const k = (i: number) => (i * 9301 + bien * 49297) % 233280 / 233280;   // nhiễu tất định
  if (dang === "ranked") {
    const hang = 5;
    return (
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
        {Array.from({ length: hang }).map((_, i) => (
          <g key={i} opacity={0.26 + i * 0.06}>
            <rect x={0} y={(H / hang) * i + 8} width={W * (0.55 + k(i) * 0.43)} height={H / hang - 16}
                  rx={H / hang / 5} fill={i % 2 ? b : a} />
            <rect x={W * (0.55 + k(i) * 0.43) + 18} y={(H / hang) * i + 8}
                  width={W * 0.05} height={H / hang - 16} rx={12} fill={a} opacity={0.6} />
          </g>
        ))}
      </svg>
    );
  }
  if (dang === "race") {
    const n = 7;
    return (
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
        {Array.from({ length: n }).map((_, i) => (
          <rect key={i} x={0} y={(H / n) * i + 6} width={W * (0.18 + k(i * 3) * 0.78)}
                height={H / n - 12} rx={H / n / 6} fill={i % 3 === 0 ? a : b}
                opacity={0.13 + (n - i) * 0.028} />
        ))}
      </svg>
    );
  }
  if (dang === "mapped") {
    const c = 14, r = 8;
    return (
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
        {Array.from({ length: c * r }).map((_, i) => {
          const x = i % c, y = Math.floor(i / c), v = k(i);
          if (v < 0.28) return null;
          return <rect key={i} x={(W / c) * x + 10} y={(H / r) * y + 10}
                       width={W / c - 20} height={H / r - 20} rx={10}
                       fill={v > 0.72 ? a : b} opacity={0.10 + v * 0.26} />;
        })}
      </svg>
    );
  }
  if (dang === "scaled") {
    const n = 6;
    return (
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
        {Array.from({ length: n }).map((_, i) => {
          const s = 0.16 + (i / n) * 0.84, w = (W / n) * 0.72 * s, h = H * 0.82 * s;
          return <rect key={i} x={(W / n) * i + ((W / n) - w) / 2} y={H - h - H * 0.06}
                       width={w} height={h} rx={16} fill={i % 2 ? a : b}
                       opacity={0.13 + i * 0.05} />;
        })}
      </svg>
    );
  }
  if (dang === "thennow") {
    return (
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
        <rect x={0} y={0} width={W / 2 - 6} height={H} fill={b} opacity={0.16} />
        <rect x={W / 2 + 6} y={0} width={W / 2 - 6} height={H} fill={a} opacity={0.22} />
        {Array.from({ length: 9 }).map((_, i) => (
          <rect key={i} x={W / 2 - 3} y={(H / 9) * i + 10} width={6} height={H / 9 - 20}
                rx={3} fill="#fff" opacity={0.20} />
        ))}
      </svg>
    );
  }
  if (dang === "longshot") {
    const n = 8;
    return (
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
        {Array.from({ length: n }).map((_, i) => (
          <rect key={i} x={W * 0.10} y={(H / n) * i + H / n / 2 - 5}
                width={W * (0.80 - i * 0.085)} height={10} rx={5}
                fill={i < 2 ? a : b} opacity={0.14 + (n - i) * 0.035} />
        ))}
      </svg>
    );
  }
  // cinematic — khung phim
  const n = 9;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
      {Array.from({ length: n }).map((_, i) => (
        <g key={i} opacity={0.13 + k(i) * 0.22}>
          <rect x={(W / n) * i + 12} y={H * 0.14} width={W / n - 24} height={H * 0.72}
                rx={14} fill={i % 2 ? a : b} />
          <rect x={(W / n) * i + 12} y={H * 0.03} width={W / n - 24} height={H * 0.06}
                rx={6} fill="#fff" opacity={0.35} />
          <rect x={(W / n) * i + 12} y={H * 0.91} width={W / n - 24} height={H * 0.06}
                rx={6} fill="#fff" opacity={0.35} />
        </g>
      ))}
    </svg>
  );
};

export const BrandV3: React.FC<BrandV3Props> = (props) => {
  const { kind = "banner", name = "MM0", tagline = "", handle = "", dang = "ranked",
          font = "", bien = 0 } = props;
  const a = _n(props.accent), b = _n(props.accent2, a), nen = _n(props.bg, "#0A0C16");
  const { width: W, height: H } = useVideoConfig();
  const B = bienCua(bien);
  const chu = phong(font);

  // ── WATERMARK: chỉ dấu hiệu, nền trong suốt ────────────────────────────────────────────────
  if (kind === "watermark") {
    return (
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: chu }}>
        <div style={{ width: W * 0.82, height: W * 0.82, borderRadius: "50%",
                      background: `linear-gradient(140deg, ${a}, ${b})`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      color: "#0A0C16", fontWeight: 900, fontSize: W * 0.40, letterSpacing: -2 }}>
          {monogram(name)}
        </div>
      </AbsoluteFill>
    );
  }

  // ── AVATAR: MỌI THỨ NẰM TRONG ĐƯỜNG TRÒN NỘI TIẾP ──────────────────────────────────────────
  // YouTube cắt tròn và hiển thị 48px trên điện thoại. Nên dùng MONOGRAM đậm choán khung, không
  // dùng wordmark hai dòng như bản cũ — ở 48px thì chữ hai dòng thành vệt xám.
  if (kind === "avatar") {
    return (
      <AbsoluteFill style={{ background: nen, fontFamily: chu, alignItems: "center",
                             justifyContent: "center", overflow: "hidden" }}>
        <AbsoluteFill style={{ ...hoaTietNen(B, a) }} />
        <div style={{ position: "absolute", inset: W * 0.07, borderRadius: "50%",
                      background: `radial-gradient(120% 120% at 30% 18%, ${a}2e, transparent 62%),
                                   linear-gradient(150deg, ${a}22, ${b}12)`,
                      border: `${Math.round(W * 0.018)}px solid ${a}`, boxSizing: "border-box" }} />
        <div style={{ position: "relative", color: "#FFFFFF", fontWeight: 900,
                      fontSize: W * (monogram(name).length > 2 ? 0.36 : 0.44),
                      letterSpacing: -W * 0.012, lineHeight: 1,
                      textShadow: `0 ${W * 0.012}px ${W * 0.05}px rgba(0,0,0,.6), 0 0 ${W * 0.06}px ${a}66` }}>
          {monogram(name)}
        </div>
        <div style={{ position: "absolute", bottom: W * 0.155, color: a, fontWeight: 800,
                      fontSize: W * 0.052, letterSpacing: W * 0.006, opacity: 0.95 }}>
          {String(dang || "").toUpperCase()}
        </div>
      </AbsoluteFill>
    );
  }

  // ── BANNER 2560×1440 ───────────────────────────────────────────────────────────────────────
  // Vùng an toàn 1546×423 chính giữa: CHỮ chỉ nằm trong đó. Nền tràn viền, và nền là HỆ HÌNH CỦA
  // CHÍNH DẠNG KÊNH — thứ bản cũ bỏ trống 90% khung.
  const AN_W = 1546, AN_H = 423;
  const sx = W / 2560;                         // co giãn nếu render ở khổ khác
  const tenDai = String(name).length;
  return (
    <AbsoluteFill style={{ background: nen, fontFamily: chu, overflow: "hidden" }}>
      <AbsoluteFill style={{ ...hoaTietNen(B, a) }} />
      <AbsoluteFill style={{ opacity: 0.9 }}>
        <NenDang dang={dang} a={a} b={b} W={W} H={H} bien={bien} />
      </AbsoluteFill>
      {/* làm tối vùng giữa để chữ luôn đọc được, bất kể nền dạng nào */}
      <AbsoluteFill style={{
        background: `radial-gradient(52% 44% at 50% 50%, ${nen}fa 0%, ${nen}e6 55%, ${nen}33 100%)` }} />
      <div style={{ position: "absolute", left: (W - AN_W * sx) / 2, top: (H - AN_H * sx) / 2,
                    width: AN_W * sx, height: AN_H * sx, display: "flex", flexDirection: "column",
                    // 27/8 — CHỮ LUÔN CĂN GIỮA. Bản đầu để biến thể `nhan` đẩy khối chữ sang mép
                    // trái/phải vùng an toàn. Nhìn khung thật thì lệch hẳn một bên, mất cân với nền,
                    // và nguy hơn: YouTube cắt rất mạnh trên điện thoại — chỉ vùng giữa 1546×423 là
                    // CHẮC CHẮN hiện, đẩy chữ ra mép là tự chuốc rủi ro bị cắt mất.
                    // Biến thể phải đổi PHONG CÁCH (màu, hoạ tiết, vị trí nhãn nhỏ), không được đổi
                    // thứ quyết định chữ có đọc được hay không.
                    alignItems: "center", justifyContent: "center", textAlign: "center" }}>
        <div style={{ display: "inline-block", background: a, color: "#0A0C16", fontWeight: 900,
                      fontSize: 30 * sx, letterSpacing: 3 * sx, padding: `${8 * sx}px ${20 * sx}px`,
                      borderRadius: 999, marginBottom: 18 * sx }}>
          {String(dang || "").toUpperCase()}
        </div>
        <div style={{ color: "#FFFFFF", fontWeight: 900, lineHeight: 0.95,
                      fontSize: (tenDai > 16 ? 128 : tenDai > 11 ? 156 : 184) * sx,
                      letterSpacing: -2 * sx,
                      textShadow: `0 ${10 * sx}px ${44 * sx}px rgba(0,0,0,.9), 0 0 ${70 * sx}px ${a}55` }}>
          {name}
        </div>
        {tagline ? (
          <div style={{ color: "#DCE7F5", fontWeight: 700, fontSize: 42 * sx, marginTop: 14 * sx,
                        textShadow: `0 ${4 * sx}px ${18 * sx}px rgba(0,0,0,.9)` }}>{tagline}</div>
        ) : null}
        {handle ? (
          <div style={{ color: a, fontWeight: 800, fontSize: 34 * sx, marginTop: 10 * sx }}>{handle}</div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
