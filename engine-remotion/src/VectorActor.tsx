import React from "react";
import { interpolate } from "remotion";

/**
 * DIỄN VIÊN VECTOR — nhân vật dựng HOÀN TOÀN BẰNG MÃ, mượt tuyệt đối (25/8/2026).
 *
 * VÌ SAO PHẢI ĐỔI CÁCH (bài học đắt của đêm nay)
 * Bản mascot trước diễn bằng cách TRÁO ẢNH giữa các tư thế do FLUX vẽ riêng (mồm mở ↔ mồm khép,
 * 12 lần/giây). Hai bản vẽ lệch nhau vài pixel về tỉ lệ và vị trí, nên tráo qua lại ra NHẤP NHÁY
 * chứ không ra "đang nói" — anh xem thử và bác ngay: "giật giật". Đó là giới hạn cứng của mọi lối
 * "AI vẽ nhiều tư thế rồi swap", không tham số nào chữa được.
 *
 * Ở đây nhân vật là HÌNH VECTOR: mỗi bộ phận một đường path, mỗi khớp một phép xoay. Muốn mồm hé
 * 37% thì hàm dưới đây vẽ ra đúng cái mồm hé 37% — không có "khung 1" và "khung 2" để mà giật.
 * Hệ quả:
 *   • mượt tuyệt đối ở 30fps (và ở bất kỳ fps nào)
 *   • KHÔNG BAO GIỜ drift — nhân vật là công thức, không phải ảnh
 *   • 0 lượt gọi AI, 0 tài nguyên tải về, render CPU rất nhẹ (vài chục path/khung)
 *
 * Phong cách: flat vector nét dày, khối tròn, màu no — dòng mà Kurzgesagt (23 triệu sub) dùng.
 * Nó đẹp KHÔNG nhờ chi tiết mà nhờ hình khối dứt khoát, nên vẽ bằng mã là đúng thế mạnh.
 */

/** Bộ thông số tạo hình một nhân vật. Đổi vài con số là ra nhân vật khác — không đụng mã diễn. */
export type ActorSpec = {
  id: string;
  da: string;            // màu thân/lông chính
  da2: string;           // màu bụng/mảng sáng
  net: string;           // màu nét viền
  mat: string;           // màu tròng mắt
  mo?: string;           // màu mỏ / mũi
  toc?: string;          // màu tóc/mào (rỗng = không có)
  ao?: string;           // màu áo (rỗng = không mặc áo)
  phuKien?: "tie" | "glasses" | "cap" | "bun" | "hat" | "none";
  phuKienMau?: string;
  tai?: "tron" | "nhon" | "khong";   // dáng tai
  beo?: number;          // 0.8 gầy … 1.25 mập
};

type Props = {
  spec: ActorSpec;
  /** 0..1 — độ mở mồm, lấy từ biên độ tiếng thật */
  mom: number;
  /** khung hiện tại (để thở/chớp mắt/đung đưa) */
  f: number;
  /** đang nói hay không */
  noi: boolean;
  /** cảm xúc điều khiển lông mày + dáng mồm */
  cx?: "thuong" | "vui" | "gian" | "soc" | "ranh";
  /** -1 nhìn trái … 1 nhìn phải */
  nhin?: number;
  /** tay: góc xoay (độ). Không truyền -> tự vung theo nhịp nói */
  tayT?: number;
  tayP?: number;
};

const R = (deg: number) => `rotate(${deg})`;

export const VectorActor: React.FC<Props> = ({
  spec, mom, f, noi, cx = "thuong", nhin = 0, tayT, tayP,
}) => {
  const S = spec;
  const beo = S.beo ?? 1;

  // ── SỰ SỐNG NỀN: thở + chớp mắt. Không có hai thứ này thì nhân vật thành hình dán, kể cả khi
  //    mồm đang chạy. Mọi phim hoạt hình đều giữ nhân vật "động khẽ" suốt thời gian đứng im.
  const tho = Math.sin(f / 26) * 1.6;                  // lồng ngực phập phồng
  const nhun = Math.sin(f / 26) * 2.2;                 // cả người nhún theo
  const chuKyChop = 96;                                // ~3,2 giây/lần chớp
  const pha = f % chuKyChop;
  const nhamMat = pha < 4 ? 1 - Math.abs(pha - 2) / 2 : 0;   // 0..1, khép trong ~4 khung

  // ── MỒM: hình dạng do CÔNG THỨC, không phải ảnh. `mom` 0..1 mở dần, cảm xúc đổi độ cong.
  const moToiDa = cx === "soc" ? 26 : cx === "gian" ? 20 : 18;
  const hMom = 2 + mom * moToiDa;                      // chiều cao khoang mồm
  const wMom = 20 + mom * 8 + (cx === "vui" ? 6 : 0);  // bề ngang
  const congMom = cx === "vui" ? 7 : cx === "gian" ? -6 : cx === "ranh" ? 4 : 0;

  // ── LÔNG MÀY: hai thanh xoay — thứ chở gần hết biểu cảm trong hoạt hình phẳng
  const mayGoc = cx === "gian" ? 22 : cx === "soc" ? -16 : cx === "ranh" ? 10 : cx === "vui" ? -8 : 0;
  const mayCao = cx === "soc" ? -6 : cx === "gian" ? 3 : 0;

  // ── TAY: nếu không chỉ định thì tự vung theo nhịp nói (nói mới khoa tay — im thì buông)
  const vung = noi ? Math.sin(f / 7) * 16 * (0.4 + mom) : Math.sin(f / 48) * 3;
  const gTayT = tayT ?? (-18 - vung);
  const gTayP = tayP ?? (18 + vung);

  const netW = 5;
  const line = { stroke: S.net, strokeWidth: netW, strokeLinecap: "round" as const,
                 strokeLinejoin: "round" as const };

  return (
    <svg viewBox="0 0 200 320" style={{ width: "100%", height: "100%", overflow: "visible" }}>
      <g transform={`translate(0 ${nhun})`}>
        {/* ── CHÂN ── */}
        <g {...line} fill="none">
          <path d={`M${88} 268 L${86} 300`} />
          <path d={`M${112} 268 L${114} 300`} />
        </g>
        <g fill={S.mo || S.da2} {...line}>
          <ellipse cx="82" cy="303" rx="15" ry="7" />
          <ellipse cx="118" cy="303" rx="15" ry="7" />
        </g>

        {/* ── TAY SAU (vẽ trước thân để có lớp) ── */}
        <g transform={`translate(138 168) ${R(gTayP)}`} {...line} fill={S.da}>
          <path d="M0 0 q14 26 4 52" fill="none" />
          <circle cx="6" cy="56" r="11" />
        </g>

        {/* ── THÂN ── */}
        <g {...line} fill={S.da}>
          <path d={`M100 150
                    c ${-42 * beo} 0 ${-52 * beo} 40 ${-46 * beo} ${78 + tho}
                    c ${4 * beo} 26 ${30 * beo} 42 ${46 * beo} 42
                    c ${16 * beo} 0 ${42 * beo} -16 ${46 * beo} -42
                    c ${6 * beo} ${-38 - tho} ${-4 * beo} -78 ${-46 * beo} -78 z`} />
          {/* mảng bụng sáng — tạo khối mà không cần đổ bóng */}
          <ellipse cx="100" cy="222" rx={26 * beo} ry={38} fill={S.da2} stroke="none" opacity={0.95} />
        </g>

        {/* ── ÁO (nếu có) ── */}
        {S.ao ? (
          <path d={`M100 152 c ${-40 * beo} 0 ${-48 * beo} 30 ${-44 * beo} 52
                    l ${88 * beo} 0 c ${4 * beo} -22 ${-4 * beo} -52 ${-44 * beo} -52 z`}
                fill={S.ao} {...line} />
        ) : null}

        {/* ── PHỤ KIỆN THÂN: cà vạt ── */}
        {S.phuKien === "tie" ? (
          <g {...line} fill={S.phuKienMau || "#C62828"}>
            <path d="M100 158 l-9 10 l9 12 l9 -12 z" />
            <path d="M100 180 l-11 46 l11 12 l11 -12 z" />
          </g>
        ) : null}

        {/* ── TAY TRƯỚC ── */}
        <g transform={`translate(62 168) ${R(gTayT)}`} {...line} fill={S.da}>
          <path d="M0 0 q-14 26 -4 52" fill="none" />
          <circle cx="-6" cy="56" r="11" />
        </g>

        {/* ── ĐẦU ── */}
        <g transform={`translate(0 ${-tho * 0.5})`}>
          {/* tai */}
          {S.tai === "nhon" ? (
            <g {...line} fill={S.da}>
              <path d="M66 84 l-10 -30 l26 12 z" />
              <path d="M134 84 l10 -30 l-26 12 z" />
            </g>
          ) : S.tai === "tron" ? (
            <g {...line} fill={S.da}>
              <circle cx="62" cy="86" r="15" />
              <circle cx="138" cy="86" r="15" />
            </g>
          ) : null}

          {/* sọ */}
          <ellipse cx="100" cy="104" rx="52" ry="48" fill={S.da} {...line} />
          {/* mảng mặt sáng */}
          <ellipse cx="100" cy="112" rx="38" ry="33" fill={S.da2} stroke="none" opacity={0.9} />

          {/* tóc / mào */}
          {S.toc ? (
            <path d="M56 84 q16 -34 44 -34 q28 0 44 34 q-20 -16 -44 -16 q-24 0 -44 16 z"
                  fill={S.toc} {...line} />
          ) : null}

          {/* lông mày — hai thanh xoay, chở phần lớn biểu cảm */}
          <g {...line} fill="none" strokeWidth={netW + 1}>
            <path d={`M74 ${86 + mayCao} l22 0`} transform={`rotate(${-mayGoc} 85 ${86 + mayCao})`} />
            <path d={`M104 ${86 + mayCao} l22 0`} transform={`rotate(${mayGoc} 115 ${86 + mayCao})`} />
          </g>

          {/* mắt — tròng dịch theo hướng nhìn, mí khép khi chớp */}
          {[80, 120].map((cxx, i) => (
            <g key={i}>
              <ellipse cx={cxx} cy="106" rx="13" ry={13 * (1 - nhamMat)} fill="#FFFFFF" {...line} />
              {nhamMat < 0.6 ? (
                <circle cx={cxx + nhin * 5} cy="108" r={5.5} fill={S.mat} />
              ) : null}
              {nhamMat >= 0.6 ? (
                <path d={`M${cxx - 13} 106 l26 0`} {...line} fill="none" />
              ) : null}
            </g>
          ))}

          {/* kính (nếu có) */}
          {S.phuKien === "glasses" ? (
            <g fill="none" stroke={S.phuKienMau || "#D32F2F"} strokeWidth={netW}>
              <rect x="64" y="92" width="32" height="26" rx="7" />
              <rect x="104" y="92" width="32" height="26" rx="7" />
              <path d="M96 104 l8 0" />
            </g>
          ) : null}

          {/* mỏ / mũi */}
          {S.mo ? (
            <path d="M100 118 l-16 10 l16 12 l16 -12 z" fill={S.mo} {...line} />
          ) : null}

          {/* MỒM — công thức, không phải ảnh. mom=0 là một nét; mom=1 là khoang mở tròn. */}
          <path
            d={`M${100 - wMom / 2} ${140 - congMom}
                q ${wMom / 2} ${congMom * 2 + hMom * 1.15} ${wMom} 0
                q ${-wMom / 2} ${-congMom * 2 + hMom * 0.55} ${-wMom} 0 z`}
            fill={mom > 0.06 ? "#5A1E22" : "none"} {...line} />
          {/* lưỡi — chỉ ló ra khi mồm mở đủ, cho cảm giác có chiều sâu */}
          {mom > 0.42 ? (
            <ellipse cx="100" cy={140 + hMom * 0.45} rx={wMom * 0.32} ry={hMom * 0.24}
                     fill="#E4707A" stroke="none" />
          ) : null}

          {/* mũ / búi tóc */}
          {S.phuKien === "cap" ? (
            <g {...line} fill={S.phuKienMau || "#2E7D32"}>
              <path d="M58 78 q42 -34 84 0 z" />
              <path d="M142 78 q22 2 26 12 l-30 2 z" />
            </g>
          ) : S.phuKien === "bun" ? (
            <circle cx="100" cy="52" r="20" fill={S.toc || "#9E9E9E"} {...line} />
          ) : S.phuKien === "hat" ? (
            <g {...line} fill={S.phuKienMau || "#37474F"}>
              <rect x="72" y="34" width="56" height="34" rx="4" />
              <rect x="52" y="66" width="96" height="10" rx="5" />
            </g>
          ) : null}
        </g>
      </g>
    </svg>
  );
};

export default VectorActor;
