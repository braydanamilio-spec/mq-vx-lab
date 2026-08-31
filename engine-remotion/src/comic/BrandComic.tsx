import React from "react";
import { AbsoluteFill } from "remotion";
import { DienVienHai } from "../v4/DienVienHai";
import { KIEU_MAU, Kieu, TenCamXuc, TenCuChi } from "../v2/DienVien";

// ══════════════════════════════════════════════════════════════════════════════════════════
// BRAND KIT — ảnh đại diện, ảnh bìa kênh, hình chìm
// ------------------------------------------------------------------------------------------
// Anh: *"e nhớ design lại brandkit cho a nha"*. Bộ cũ dựng theo phong cách `KichHai` (nhân vật
// đứng trên ảnh nền AI), giờ không còn đúng thứ gì trên kênh nữa.
//
// Ba cỡ, ba việc khác hẳn nhau — và đây là chỗ dễ làm sai nhất, vì chúng trông giống nhau khi
// nhìn trên màn hình lớn nhưng người xem gặp chúng ở ba nơi hoàn toàn khác:
//
//   AVATAR 800×800   — hiển thị THẬT ở 48px cạnh mỗi bình luận, và 88px trên trang kênh. Ở cỡ
//                      ấy chỉ còn đọc được MỘT thứ. Nên avatar chỉ có khuôn mặt, cắt sát, không
//                      chữ. Chữ trong avatar ở 48px là một vệt xám.
//   BANNER 2560×1440 — nhưng vùng LUÔN hiện trên mọi thiết bị chỉ là 1546×423 ở chính giữa.
//                      Mọi thứ quan trọng phải nằm trong ô ấy; phần ngoài chỉ là màu tràn.
//   WATERMARK 150×150 — hiện đè lên video, góc phải dưới, nền trong suốt. Phải đọc được trên
//                      cả nền sáng lẫn nền tối, nên có viền mực dày và không dùng màu nhạt.
// ══════════════════════════════════════════════════════════════════════════════════════════

export type PropsBrand = {
  kind?: "avatar" | "banner" | "watermark";
  kieuA?: string; kieuB?: string; kieuTuyA?: Partial<Kieu>; kieuTuyB?: Partial<Kieu>;
  tieuDe?: string; handle?: string; khau?: string;
  mau?: string; mauPhu?: string;
  // 31/8 — Xếp mười avatar cạnh nhau mới thấy: tám cái là nữ tóc dài, cùng một kiểu cười há
  // miệng. Vì avatar luôn lấy nhân vật A và luôn dùng cảm xúc "vui". Mười kênh phải nhìn ra
  // mười người khác nhau ở ô 48px — mà ở cỡ ấy chỉ còn ba thứ đọc được: tóc, biểu cảm, màu.
  dungB?: boolean;            // lấy nhân vật B thay vì A
  camXuc?: TenCamXuc;
  // 31/8 — Anh: *"brandkit mỗi channel nên tạo 1 kiểu khác nhau, tránh họ nhìn vào biết cùng
  // 1 người làm"*. Đây là chỗ mà đổi màu không cứu được: mười avatar cùng một BỐ CỤC (mặt
  // giữa, vòng tròn sau, viền dày) thì xếp cạnh nhau vẫn đọc ra một xưởng, dù mười màu khác
  // nhau. Người ta nhận ra khuôn trước khi nhận ra màu.
  boCuc?: number;             // 0..9 — mỗi kênh một khuôn dựng khác hẳn
};

const Halftone: React.FC<{ w: number; h: number; co: number }> = ({ w, h, co }) => (
  <svg width={w} height={h} style={{ position: "absolute", inset: 0 }}>
    <defs>
      <pattern id="bht" width={co} height={co} patternUnits="userSpaceOnUse">
        <circle cx={co * 0.3} cy={co * 0.3} r={co * 0.17} fill="#00000018" />
      </pattern>
    </defs>
    <rect width={w} height={h} fill="url(#bht)" />
  </svg>
);

export const BrandComic: React.FC<PropsBrand> = ({
  kind = "avatar", kieuA = "hang_xom", kieuB = "bank", kieuTuyA = {}, kieuTuyB = {},
  tieuDe = "", handle = "", khau = "", mau = "#E4572E", mauPhu = "#1F7AE0",
  dungB = false, camXuc = "vui", boCuc = 0,
}) => {
  const A: Kieu = { ...(KIEU_MAU[kieuA] || KIEU_MAU.hang_xom), ...kieuTuyA };
  const B: Kieu = { ...(KIEU_MAU[kieuB] || KIEU_MAU.bank), ...kieuTuyB };
  const CAO_NG = 378, NGUC = 150;              // đo trên ảnh bìa, xem PIPELINE_RULES 12.2

  // ── AVATAR: một khuôn mặt, cắt sát, không chữ ────────────────────────────────────────
  if (kind === "avatar") {
    const S = 800;
    const N = dungB ? B : A;
    const caoA = N.cao ?? 1;
    // Cắt từ đỉnh đầu tới ngang cằm-cổ: ở 48px thì phần thân chỉ làm mặt nhỏ đi.
    // Chừa 14% phía trên cho tóc và mũ — bản đầu cắt mất đỉnh mũ của TECH SUPPORT, và một cái
    // mũ cụt ở 48px đọc ra là hình lỗi chứ không đọc ra là kiểu tóc.
    // Trẻ con có đầu to hơn hẳn (`tiLeDau` 1,22 và engine còn nhân thêm 1,34 cho giới "tre"),
    // nên cùng một công thức cho ra một cái đầu tràn khỏi khung — avatar PARENT MODE mất cả
    // nửa mặt dưới. Chia lại theo đúng hệ số đầu thì mọi nhân vật về cùng một cỡ mặt.
    const heDau = (N.tiLeDau ?? 1) * (N.gioi === "tre" ? 1.34 : 1);
    const k = (S * 0.72) / ((CAO_NG - 205) * caoA * heDau);
    const bc = ((boCuc % 10) + 10) % 10;
    const V = "#14110F";
    // Mười khuôn. Chúng khác nhau ở NỀN và ở KHUNG — hai thứ chiếm phần lớn diện tích ô 48px,
    // nên đổi chúng là đổi thứ mắt bắt trước tiên. Khuôn mặt vẫn vẽ bằng cùng bộ nét (đó là
    // thứ giữ chất lượng), nhưng không khuôn nào trình bày nó giống khuôn nào.
    const Nen = () => {
      if (bc === 0) return <circle cx={S / 2} cy={S * 0.52} r={S * 0.43} fill={mauPhu} opacity={0.55} />;
      if (bc === 1) return <>
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <rect key={i} x={-S} y={S * (i / 6)} width={S * 3} height={S / 12} fill={mauPhu}
                opacity={0.5} transform={`rotate(-18 ${S / 2} ${S / 2})`} />
        ))}
      </>;
      if (bc === 2) return <>
        <path d={`M0 0 L${S} 0 L0 ${S} Z`} fill={mauPhu} opacity={0.65} />
      </>;
      if (bc === 3) return <>
        {Array.from({ length: 22 }, (_, i) => {
          const g = (i / 22) * Math.PI * 2;
          return <line key={i} x1={S / 2} y1={S / 2} x2={S / 2 + Math.cos(g) * S}
                       y2={S / 2 + Math.sin(g) * S} stroke={mauPhu} strokeWidth={i % 2 ? 20 : 34}
                       opacity={0.45} />;
        })}
      </>;
      if (bc === 4) return <>
        <rect x={S * 0.08} y={S * 0.08} width={S * 0.84} height={S * 0.84} rx={S * 0.42}
              fill={mauPhu} opacity={0.5} stroke={V} strokeWidth={14} />
      </>;
      if (bc === 5) return <>
        <rect x={0} y={S * 0.5} width={S} height={S * 0.5} fill={mauPhu} opacity={0.6} />
        <line x1={0} y1={S * 0.5} x2={S} y2={S * 0.5} stroke={V} strokeWidth={16} />
      </>;
      if (bc === 6) return <>
        {[0, 1, 2].map((i) => (
          <circle key={i} cx={S / 2} cy={S * 0.52} r={S * (0.2 + i * 0.12)} fill="none"
                  stroke={mauPhu} strokeWidth={26} opacity={0.55} />
        ))}
      </>;
      if (bc === 7) return <>
        <path d={`M${S / 2} ${S * 0.02} L${S * 0.62} ${S * 0.36} L${S * 0.98} ${S * 0.4}
                  L${S * 0.7} ${S * 0.64} L${S * 0.8} ${S * 0.98} L${S / 2} ${S * 0.78}
                  L${S * 0.2} ${S * 0.98} L${S * 0.3} ${S * 0.64} L${S * 0.02} ${S * 0.4}
                  L${S * 0.38} ${S * 0.36} Z`} fill={mauPhu} opacity={0.55} />
      </>;
      if (bc === 8) return <>
        {[0, 1, 2, 3].map((i) => (
          <rect key={i} x={S * (i / 4)} y={0} width={S / 8} height={S} fill={mauPhu} opacity={0.5} />
        ))}
      </>;
      return <>
        <rect x={S * 0.06} y={S * 0.06} width={S * 0.88} height={S * 0.88}
              fill="none" stroke={mauPhu} strokeWidth={30} opacity={0.7} />
        <rect x={S * 0.16} y={S * 0.16} width={S * 0.68} height={S * 0.68}
              fill={mauPhu} opacity={0.35} />
      </>;
    };
    // Khung ngoài cũng đổi theo khuôn: vuông đặc · bo góc · không viền (dùng vòng tròn thay).
    const khung = bc % 3 === 0 ? { border: `26px solid ${V}` }
      : bc % 3 === 1 ? { border: `20px solid ${V}`, borderRadius: 96 }
      : { border: `14px solid ${V}`, borderRadius: 400 };
    return (
      <AbsoluteFill style={{ background: mau, overflow: "hidden" }}>
        <Halftone w={S} h={S} co={12 + (bc % 4) * 6} />
        <AbsoluteFill>
          <svg width={S} height={S} viewBox={`0 0 ${S} ${S}`}><Nen /></svg>
        </AbsoluteFill>
        <AbsoluteFill>
          <svg width={S} height={S} viewBox={`0 0 ${S} ${S}`}>
            <DienVienHai
              kieu={N} camXuc={camXuc} cuChi={"nghi" as TenCuChi} nhin={[0, 0]}
              noi={{ w: 20, h: 14, tron: 0.1 } as any} t={0.8} dangNoi={false}
              kyHieu={false} ghimNguc
              x={S / 2} y={S * 0.15 + CAO_NG * caoA * k} scale={k}
            />
          </svg>
        </AbsoluteFill>
        <AbsoluteFill style={khung as React.CSSProperties} />
      </AbsoluteFill>
    );
  }

  // ── WATERMARK: nền trong suốt, đọc được trên mọi nền ─────────────────────────────────
  if (kind === "watermark") {
    const S = 150;
    const chu = (tieuDe || "M").split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();
    return (
      <AbsoluteFill style={{ background: "transparent" }}>
        <svg width={S} height={S} viewBox={`0 0 ${S} ${S}`}>
          <rect x={10} y={10} width={S - 20} height={S - 20} rx={16}
                fill={mau} stroke="#14110F" strokeWidth={9} />
          <text x={S / 2} y={S * 0.66} textAnchor="middle" fill="#FFFFFF"
                fontFamily="Poppins, Arial Black, sans-serif" fontWeight={900} fontSize={S * 0.46}
                stroke="#14110F" strokeWidth={7} paintOrder="stroke">{chu}</text>
        </svg>
      </AbsoluteFill>
    );
  }

  // ── BANNER: mọi thứ quan trọng nằm trong ô an toàn 1546×423 ở giữa ───────────────────
  // Sáu khuôn. Khác nhau ở BA trục cùng lúc — nền, chỗ đứng của nhân vật, cách đặt tên — vì
  // đổi một trục thì mắt vẫn nhận ra cùng một khuôn tô lại. Ô an toàn thì khuôn nào cũng phải
  // tôn trọng: nhân vật và chữ nằm trọn trong 1546×423, phần ngoài chỉ là màu tràn.
  const W = 2560, H = 1440;
  const AT = { w: 1546, h: 423, x: (2560 - 1546) / 2, y: (1440 - 423) / 2 };
  const bcB = ((boCuc % 6) + 6) % 6;
  const V = "#14110F";
  const kA = (AT.h * 0.92) / (CAO_NG * (A.cao ?? 1));
  const kB = (AT.h * 0.86) / (CAO_NG * (B.cao ?? 1));

  // chỗ đứng của hai nhân vật theo khuôn (tỉ lệ trong ô an toàn); null = không vẽ người ấy
  const CHO: ([number, number | null])[] = [
    [0.10, 0.90],    // 0 — hai bên, tên ở giữa
    [0.16, null],    // 1 — một người bên trái, tên chiếm phải
    [0.82, 0.94],    // 2 — hai người dồn về phải, tên chiếm trái
    [0.08, 0.50],    // 3 — trái và giữa, tên lệch phải
    [null as any, 0.86], // 4 — chỉ người B bên phải
    [0.5, null],     // 5 — một người chính giữa, tên hai bên
  ];
  const [xa, xb] = CHO[bcB];
  const chuTrai = bcB === 2 ? 0.04 : bcB === 1 ? 0.4 : bcB === 3 ? 0.56 : bcB === 4 ? 0.06 : 0.22;
  const chuRong = bcB === 5 ? 0.9 : bcB === 0 ? 0.56 : 0.5;

  const NenB = () => {
    if (bcB === 0) return null;                       // dải màu trơn
    if (bcB === 1) return <rect x={0} y={0} width={W * 0.5} height={H} fill={mauPhu} opacity={0.55} />;
    if (bcB === 2) return <>
      {Array.from({ length: 14 }, (_, i) => (
        <rect key={i} x={i * (W / 14)} y={0} width={W / 28} height={H} fill={mauPhu} opacity={0.4} />
      ))}
    </>;
    if (bcB === 3) return <>
      <path d={`M0 0 L${W * 0.44} 0 L${W * 0.3} ${H} L0 ${H} Z`} fill={mauPhu} opacity={0.5} />
      <path d={`M${W * 0.72} 0 L${W} 0 L${W} ${H} L${W * 0.58} ${H} Z`} fill={mauPhu} opacity={0.35} />
    </>;
    if (bcB === 4) return <>
      {Array.from({ length: 30 }, (_, i) => {
        const g = (i / 30) * Math.PI * 2;
        return <line key={i} x1={W * 0.78} y1={H / 2} x2={W * 0.78 + Math.cos(g) * W}
                     y2={H / 2 + Math.sin(g) * W} stroke={mauPhu} strokeWidth={i % 2 ? 14 : 26}
                     opacity={0.4} />;
      })}
    </>;
    return <>
      <circle cx={W / 2} cy={H / 2} r={H * 0.46} fill={mauPhu} opacity={0.5} />
      <circle cx={W / 2} cy={H / 2} r={H * 0.6} fill="none" stroke={mauPhu} strokeWidth={26} opacity={0.4} />
    </>;
  };

  return (
    <AbsoluteFill style={{ background: bcB === 5 ? mau : mauPhu, overflow: "hidden" }}>
      <Halftone w={W} h={H} co={20 + bcB * 5} />
      <AbsoluteFill><svg width={W} height={H}><NenB /></svg></AbsoluteFill>

      {/* dải màu chính — khuôn 3 và 5 bỏ dải này, dùng nền hình học thay */}
      {bcB !== 3 && bcB !== 5 ? (
        <div style={{
          position: "absolute", left: 0, top: AT.y - 60, width: W, height: AT.h + 120,
          background: mau, borderTop: `12px solid ${V}`, borderBottom: `12px solid ${V}`,
        }} />
      ) : null}

      <AbsoluteFill>
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
          {xa != null ? (
            <DienVienHai
              kieu={A} camXuc={"bat_ngo" as TenCamXuc} cuChi={"mo_tay" as TenCuChi} nhin={[0.4, 0]}
              noi={{ w: 24, h: 18, tron: 0.1 } as any} t={1.1} dangNoi={false} kyHieu={false} ghimNguc
              x={AT.x + AT.w * xa} y={AT.y + AT.h * 0.97} scale={kA}
            />
          ) : null}
          {xb != null ? (
            <DienVienHai
              kieu={B} camXuc={"tu_tin" as TenCamXuc} cuChi={"khoanh_tay" as TenCuChi} nhin={[-0.4, 0]}
              noi={{ w: 20, h: 12, tron: 0.1 } as any} t={1.7} dangNoi={false} kyHieu={false} ghimNguc lat
              x={AT.x + AT.w * xb} y={AT.y + AT.h * 0.97} scale={kB}
            />
          ) : null}
        </svg>
      </AbsoluteFill>

      <div style={{
        position: "absolute", left: AT.x + AT.w * chuTrai, top: AT.y,
        width: AT.w * chuRong, height: AT.h,
        display: "flex", flexDirection: "column",
        alignItems: bcB === 1 || bcB === 3 ? "flex-start" : bcB === 2 || bcB === 4 ? "flex-end" : "center",
        justifyContent: "center", textAlign: bcB === 1 || bcB === 3 ? "left" : bcB === 2 || bcB === 4 ? "right" : "center",
        fontFamily: "Poppins, Arial Black, sans-serif",
        transform: bcB === 4 ? "rotate(-3deg)" : "none",
      }}>
        <div style={{
          fontSize: Math.min(bcB === 5 ? 190 : 150, (bcB === 5 ? 2600 : 1900) / Math.max(6, tieuDe.length)),
          fontWeight: 900, color: "#FFFFFF", letterSpacing: -1, lineHeight: 1,
          WebkitTextStroke: "12px #14110F", paintOrder: "stroke fill",
          textShadow: bcB % 2 ? "0 0 0 #14110F" : "10px 11px 0 #14110F",
        }}>{tieuDe}</div>
        <div style={{
          marginTop: 26, background: bcB === 4 ? mau : V, color: "#FFFFFF", padding: "10px 26px",
          fontSize: 42, fontWeight: 800, letterSpacing: 1.4,
          border: bcB === 4 ? `6px solid ${V}` : "none",
        }}>{khau || "NEW EPISODE EVERY DAY"}</div>
        <div style={{ marginTop: 16, fontSize: 36, fontWeight: 800, color: V }}>{handle}</div>
      </div>
    </AbsoluteFill>
  );
};
