import React from "react";
import { AbsoluteFill } from "remotion";
import { DienVienHai } from "../v4/DienVienHai";
import { KIEU_MAU, Kieu, TenCamXuc, TenCuChi } from "../v2/DienVien";
import { LapNoi } from "./NoiChon";
import { noiCuaTap } from "./NoiChon";

// ══════════════════════════════════════════════════════════════════════════════════════════
// ẢNH BÌA — dựng riêng, không trích khung
// ------------------------------------------------------------------------------------------
// Bản cũ làm ảnh bìa bằng cách trích một khung của video rồi đặt chữ lên. Cách ấy có hai chỗ
// hỏng không sửa được ở tầng chữ:
//
//   1. Khung trích ra là khung ĐƯỢC DỰNG CHO VIDEO, tức nhân vật đứng ở chỗ hợp với bong bóng
//      thoại, không phải chỗ hợp với một tấm bìa. Chữ đặt lên sau luôn phải né người.
//   2. Ảnh bìa cần biểu cảm MẠNH NHẤT của nhân vật; một khung bất kỳ thường là biểu cảm trung
//      tính, vì phần lớn thời lượng nhân vật đang nói chứ không đang sốc.
//
// Dựng riêng thì cả hai biến mất: bố cục chia sẵn (chữ một bên, mặt một bên), biểu cảm chọn
// đúng cái mạnh nhất, và cỡ chữ tính theo số ký tự nên không bao giờ tràn.
//
// HAI CỠ, HAI BỐ CỤC KHÁC HẲN:
//   · 1280×720 cho video dài — người xem thấy nó trong một lưới nhiều video, cạnh nhau, ở cỡ
//     nhỏ. Chữ phải đọc được ở bề ngang 210px, tức chỉ 3–5 từ.
//   · 1080×1920 cho short — thực ra YouTube lấy khung đầu làm bìa, nhưng vẫn cần một tấm cho
//     Facebook và cho kho. Bố cục dọc: mặt trên, chữ dưới.
// ══════════════════════════════════════════════════════════════════════════════════════════

const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));

/** Cỡ chữ theo CẢ hộp lẫn số ký tự — luật đã trả giá ở PIPELINE_RULES mục 8.1. */
const coChu = (chu: string, W: number, H: number, toiDa: number) => {
  const n = Math.max(6, chu.length);
  return Math.max(28, Math.min(toiDa, Math.sqrt((W * H) / 0.6 / n)));
};

export type PropsThumb = {
  hook?: string; kieuA?: string; kieuB?: string;
  kieuTuyA?: Partial<Kieu>; kieuTuyB?: Partial<Kieu>;
  tieuDe?: string; handle?: string; mau?: string; mauPhu?: string;
  kenh?: string; soTap?: number; camXuc?: TenCamXuc; ngang?: boolean;
};

export const ThumbComic: React.FC<PropsThumb> = ({
  hook = "", kieuA = "hang_xom", kieuB = "bank", kieuTuyA = {}, kieuTuyB = {},
  tieuDe = "", handle = "", mau = "#E4572E", mauPhu = "#1F7AE0",
  kenh = "", soTap = 0, camXuc = "bat_ngo", ngang = true,
}) => {
  const W = ngang ? 1280 : 1080;
  const H = ngang ? 720 : 1920;
  const A: Kieu = { ...(KIEU_MAU[kieuA] || KIEU_MAU.hang_xom), ...kieuTuyA };
  const B: Kieu = { ...(KIEU_MAU[kieuB] || KIEU_MAU.bank), ...kieuTuyB };
  const noi = noiCuaTap(kenh, soTap);

  // Chữ bìa: rút gọn còn tối đa 5 từ. Một tấm bìa đọc trong nửa giây — câu dài là câu không ai
  // đọc. Cắt ở ranh giới từ, không cắt giữa từ.
  // 31/8 — CẮT Ở RANH GIỚI CỤM, KHÔNG CẮT Ở TỪ THỨ N.
  // Bìa thử đầu ra dòng chữ "MY PROFILE SAYS I LOVE" — cụt giữa câu, đọc xong không hiểu gì.
  // Cắt cứng ở từ thứ năm là đúng cái lỗi đã sửa cho phụ đề hồi tuần trước, chỉ đổi chỗ.
  const tu = hook.replace(/[."']/g, "").split(/\s+/).filter(Boolean);
  const toiDaTu = ngang ? 5 : 6;
  let lay = tu.slice(0, toiDaTu);
  if (tu.length > toiDaTu) {
    // lùi về trước giới từ / liên từ gần nhất — chỗ ấy là ranh giới cụm tự nhiên
    const NOI_TU = ["i", "a", "the", "to", "of", "and", "but", "in", "on", "for", "with", "my", "your"];
    while (lay.length > 2 && NOI_TU.includes(lay[lay.length - 1].toLowerCase())) lay.pop();
  }
  const chu = lay.join(" ").toUpperCase() + (tu.length > lay.length ? "..." : "");

  const vungChu = ngang
    ? { x: 40, y: 40, w: W * 0.52, h: H - 80 }
    : { x: 40, y: H * 0.62, w: W - 80, h: H * 0.3 };
  const fs = coChu(chu, vungChu.w, vungChu.h * 0.86, ngang ? 132 : 150);

  // Nhân vật: cận mặt, biểu cảm mạnh. Đặt ở nửa còn lại của khung.
  // Nhân vật phải to và ở ĐÚNG chỗ: bìa thử đầu cho ra một cái đầu ló lên từ mép dưới, vì tỉ
  // lệ tính theo cả người trong khi bìa chỉ cần từ đầu tới ngực. Giải ngược lại: chốt đỉnh đầu
  // ở gần mép trên và ngực ở mép dưới vùng ảnh, rồi suy ra tỉ lệ.
  // Hai hằng này ĐO TỪ CHÍNH BÌA đã render, không chép từ chỗ khác: với tỉ lệ k = 2,71 và gót
  // đặt ở 1368, đỉnh đầu rơi vào 343 — tức chiều cao đầu-tới-gót là (1368−343)/2,71/1,04 ≈ 378,
  // không phải 460 như con số tôi đo được ở khung dọc (lúc đó nhân vật đang bị mép panel cắt
  // nên phép đo ấy đo thiếu). Cùng một bài học với mục 9.7: hằng toạ độ phải đo trong ĐÚNG
  // ngữ cảnh dùng nó.
  const CAO_NG = 378, NGUC = 150;
  const caoA = A.cao ?? 1;
  const cx = ngang ? W * 0.74 : W * 0.5;
  const dinh = ngang ? 0.1 : 0.12;          // đỉnh đầu, theo tỉ lệ chiều cao khung
  const day = ngang ? 1.0 : 0.62;           // ngực rơi vào đâu
  const k = (H * (day - dinh)) / ((CAO_NG - NGUC) * caoA);
  const yChan = H * dinh + CAO_NG * caoA * k;

  return (
    <AbsoluteFill style={{ background: mau, fontFamily: "Poppins, Arial Black, sans-serif" }}>
      {/* nền: cùng nơi chốn với tập, để bìa và video là một thế giới */}
      <AbsoluteFill style={{ opacity: 0.9 }}>
        <svg width={W} height={H}>
          <defs>
            <pattern id="thp" width="12" height="12" patternUnits="userSpaceOnUse">
              <circle cx="3" cy="3" r="2" fill="#00000014" />
            </pattern>
          </defs>
          <LapNoi noi={noi} w={W} h={H} mau={mau} mauPhu={mauPhu} net={6} />
          <rect width={W} height={H} fill="url(#thp)" />
        </svg>
      </AbsoluteFill>

      {/* mảng màu sau chữ — chữ trắng trên nền lộn xộn thì không đọc được ở cỡ nhỏ */}
      <div style={{
        position: "absolute", left: 0, top: ngang ? 0 : H * 0.58,
        width: ngang ? W * 0.58 : W, height: ngang ? H : H * 0.42,
        background: ngang
          ? `linear-gradient(90deg, ${mauPhu}F2 0%, ${mauPhu}E6 68%, ${mauPhu}00 100%)`
          : `linear-gradient(0deg, ${mauPhu}F2 0%, ${mauPhu}E0 70%, ${mauPhu}00 100%)`,
      }} />

      <AbsoluteFill>
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
          <DienVienHai
            kieu={A} camXuc={camXuc} cuChi={"mo_tay" as TenCuChi} nhin={[0, 0]}
            noi={{ w: 26, h: 22, tron: 0.1 } as any} t={1.4} dangNoi kyHieu={false} ghimNguc
            x={cx} y={yChan} scale={k}
          />
        </svg>
      </AbsoluteFill>

      {/* CHỮ HOOK — viền mực dày, đổ bóng cứng. Hai thứ này là lý do chữ bìa đọc được ở 210px. */}
      <div style={{
        position: "absolute", left: vungChu.x, top: vungChu.y,
        width: vungChu.w, height: vungChu.h,
        display: "flex", alignItems: ngang ? "center" : "flex-end",
        justifyContent: ngang ? "flex-start" : "center",
      }}>
        <div style={{
          fontSize: fs, fontWeight: 900, lineHeight: 1.02, color: "#FFFFFF",
          letterSpacing: -1, textAlign: ngang ? "left" : "center",
          WebkitTextStroke: `${Math.round(fs * 0.1)}px #14110F`, paintOrder: "stroke fill",
          textShadow: "8px 9px 0 #14110F",
        }}>{chu}</div>
      </div>

      {/* dải kênh — nhỏ, không tranh chỗ với hook */}
      <div style={{
        position: "absolute", left: 0, bottom: 0, padding: "14px 26px",
        background: "#14110F", color: "#FFFFFF", fontWeight: 900,
        fontSize: ngang ? 30 : 40, letterSpacing: 1.6,
      }}>{tieuDe}<span style={{ color: mau, marginLeft: 14 }}>{handle}</span></div>

      <AbsoluteFill style={{ border: `${ngang ? 12 : 16}px solid #14110F`, pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
