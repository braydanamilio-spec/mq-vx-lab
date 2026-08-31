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
  dungB = false, camXuc = "vui",
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
    return (
      <AbsoluteFill style={{ background: mau, overflow: "hidden" }}>
        <Halftone w={S} h={S} co={18} />
        <AbsoluteFill>
          <svg width={S} height={S} viewBox={`0 0 ${S} ${S}`}>
            <circle cx={S / 2} cy={S * 0.52} r={S * 0.43} fill={mauPhu} opacity={0.5} />
            <DienVienHai
              kieu={N} camXuc={camXuc} cuChi={"nghi" as TenCuChi} nhin={[0, 0]}
              noi={{ w: 20, h: 14, tron: 0.1 } as any} t={0.8} dangNoi={false}
              kyHieu={false} ghimNguc
              x={S / 2} y={S * 0.15 + CAO_NG * caoA * k} scale={k}
            />
          </svg>
        </AbsoluteFill>
        <AbsoluteFill style={{ border: "26px solid #14110F", borderRadius: 0 }} />
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
  const W = 2560, H = 1440;
  const AT = { w: 1546, h: 423, x: (2560 - 1546) / 2, y: (1440 - 423) / 2 };
  // 31/8 — NHÂN VẬT PHẢI NẰM TRỌN TRONG Ô AN TOÀN.
  // Bản đầu tính tỉ lệ theo đoạn đầu-tới-ngực (như ảnh bìa), nên người cao 716px trong một ô
  // chỉ cao 423px — phần chân tràn xuống dưới và sẽ bị cắt mất trên điện thoại. Banner khác
  // ảnh bìa ở đúng chỗ này: nó không được cắt ai cả, vì nó phải đọc được ở MỌI tỉ lệ màn hình.
  const kA = (AT.h * 0.92) / (CAO_NG * (A.cao ?? 1));
  const kB = (AT.h * 0.86) / (CAO_NG * (B.cao ?? 1));
  return (
    <AbsoluteFill style={{ background: mauPhu, overflow: "hidden" }}>
      <Halftone w={W} h={H} co={26} />
      {/* dải màu chính chạy ngang ô an toàn — khung ngoài chỉ là màu tràn cho màn rộng */}
      <div style={{
        position: "absolute", left: 0, top: AT.y - 60, width: W, height: AT.h + 120,
        background: mau, borderTop: "12px solid #14110F", borderBottom: "12px solid #14110F",
      }} />
      <AbsoluteFill>
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
          <DienVienHai
            kieu={A} camXuc={"bat_ngo" as TenCamXuc} cuChi={"mo_tay" as TenCuChi} nhin={[0.4, 0]}
            noi={{ w: 24, h: 18, tron: 0.1 } as any} t={1.1} dangNoi={false} kyHieu={false} ghimNguc
            x={AT.x + AT.w * 0.1} y={AT.y + AT.h * 0.97} scale={kA}
          />
          <DienVienHai
            kieu={B} camXuc={"tu_tin" as TenCamXuc} cuChi={"khoanh_tay" as TenCuChi} nhin={[-0.4, 0]}
            noi={{ w: 20, h: 12, tron: 0.1 } as any} t={1.7} dangNoi={false} kyHieu={false} ghimNguc lat
            x={AT.x + AT.w * 0.9} y={AT.y + AT.h * 0.97} scale={kB}
          />
        </svg>
      </AbsoluteFill>

      <div style={{
        position: "absolute", left: AT.x + AT.w * 0.22, top: AT.y,
        width: AT.w * 0.56, height: AT.h,
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        fontFamily: "Poppins, Arial Black, sans-serif", textAlign: "center",
      }}>
        <div style={{
          fontSize: Math.min(150, 1900 / Math.max(6, tieuDe.length)), fontWeight: 900,
          color: "#FFFFFF", letterSpacing: -1, lineHeight: 1,
          WebkitTextStroke: "12px #14110F", paintOrder: "stroke fill",
          textShadow: "10px 11px 0 #14110F",
        }}>{tieuDe}</div>
        <div style={{
          marginTop: 26, background: "#14110F", color: "#FFFFFF", padding: "10px 26px",
          fontSize: 42, fontWeight: 800, letterSpacing: 1.4,
        }}>{khau || "NEW EPISODE EVERY DAY"}</div>
        <div style={{ marginTop: 16, fontSize: 36, fontWeight: 800, color: "#14110F" }}>{handle}</div>
      </div>
    </AbsoluteFill>
  );
};
