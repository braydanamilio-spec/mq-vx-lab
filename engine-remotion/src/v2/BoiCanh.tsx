import React from "react";

/**
 * BỐI CẢNH V2 — nền vector phẳng, mỗi niche một thế giới (29/8/2026).
 *
 * Dựng bằng hình học thuần, KHÔNG dùng một lượt vẽ AI nào. Đây không phải chuyện tiết kiệm cho
 * vui: nhật ký phiên hôm nay ghi "đã thử 151 key, tất cả hết hạn mức ảnh" — kho vẽ ảnh là chỗ
 * nghẽn nặng nhất của cả hệ. Một bộ kênh không tiêu lượt vẽ nào thì chạy được kể cả những ngày
 * mọi kênh khác phải xếp hàng.
 *
 * Và nó giải luôn hai lỗi đã đo được trên 50 kênh cũ:
 *   • CHỮ BỊA trong ảnh AI — nền vector không có chỗ nào để máy điền chữ vào;
 *   • KHUNG TỐI — màu nền do mình đặt, đo được trước khi render, không phải cầu may.
 *
 * Mọi bối cảnh vẽ trong khung 1000×1000, gốc (0,0) ở giữa, đất ở y = +230.
 */

type P = { mau: Paltte; t: number };
export type Paltte = {
  troi: [string, string];      // gradient nền
  dat: string;                 // mặt đất / sàn
  vach: string;                // đường kẻ, khung cửa
  nhan: string;                // màu nhấn của kênh
  muc: string;                 // màu nét
};

export const BANG_MAU: Record<string, Paltte> = {
  // Ba bảng màu bổ sung, đi cùng ba bối cảnh mới.
  ke_sieu_thi: { troi: ["#F7F2E4", "#E4DCC4"], dat: "#C8BFA4", vach: "#9A8E70", nhan: "#C0392B", muc: "#241E14" },
  thu_phong: { troi: ["#F3E3C6", "#DCC49A"], dat: "#B99763", vach: "#8A6A3C", nhan: "#8A2F3C", muc: "#2A1E12" },
  san_thuong: { troi: ["#3A3468", "#1A1740"], dat: "#2C2652", vach: "#7E74C4", nhan: "#F2C230", muc: "#0D0B22" },
  quay_vien_phi: { troi: ["#EAF6F4", "#CBE8E3"], dat: "#A9D4CD", vach: "#4E9C93", nhan: "#B8474F", muc: "#17322F" },
  ngan_hang: { troi: ["#FFF3D6", "#FFE0A8"], dat: "#E9C888", vach: "#B98A3C", nhan: "#1D7A5F", muc: "#241A12" },
  luat: { troi: ["#EDE7FF", "#D6CBFA"], dat: "#C3B4EE", vach: "#6E5AB8", nhan: "#8A2F3C", muc: "#1E1830" },
  san_sau: { troi: ["#FFF6D9", "#FFE7A6"], dat: "#F2C230", vach: "#FFFFFF", nhan: "#C0392B", muc: "#241A12" },
  phong_kham: { troi: ["#E6F7F5", "#C6EAE6"], dat: "#AEDBD6", vach: "#4E9C93", nhan: "#D6353B", muc: "#17322F" },
  phong_lab: { troi: ["#E9F1FF", "#CBDDF9"], dat: "#B4CBEC", vach: "#4C74AE", nhan: "#F2A33C", muc: "#16233A" },
  vu_tru: { troi: ["#2A2350", "#120E2C"], dat: "#241D46", vach: "#5B4EA0", nhan: "#F2C230", muc: "#0A0818" },
  van_phong: { troi: ["#F0F4F8", "#D8E2EC"], dat: "#C3D0DC", vach: "#7A8DA0", nhan: "#1D63C7", muc: "#1B2430" },
};

const Troi: React.FC<P & { id: string }> = ({ mau, id }) => (
  <>
    <defs>
      <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor={mau.troi[0]} />
        <stop offset="1" stopColor={mau.troi[1]} />
      </linearGradient>
    </defs>
    <rect x={-700} y={-700} width={1400} height={1400} fill={`url(#${id})`} />
  </>
);

const Dat: React.FC<P> = ({ mau }) => (
  <rect x={-700} y={230} width={1400} height={520} fill={mau.dat} />
);

/** Cỏ lún phún ở chân hàng rào — chi tiết nhỏ nhưng thiếu nó thì nền đọc ra là hình dán. */
const Co: React.FC<{ mau: Paltte; n?: number }> = ({ mau, n = 14 }) => (
  <g stroke={mau.muc} strokeWidth={3.6} strokeLinecap="round" fill="none" opacity={0.55}>
    {Array.from({ length: n }).map((_, i) => {
      const x = -640 + (i * 1280) / (n - 1);
      return <path key={i} d={`M ${x} 236 l -7 -19 M ${x} 236 l 2 -25 M ${x} 236 l 9 -17`} />;
    })}
  </g>
);

// ══════════════════════════════════════════════════════════════════════════════════════════
// SÂN SAU — hàng rào cọc trắng. Ảnh tham chiếu số 3 của anh chính là cảnh này.
// ══════════════════════════════════════════════════════════════════════════════════════════
const SanSau: React.FC<P> = ({ mau, t }) => (
  <g>
    <Troi mau={mau} t={t} id="g_ss" />
    <Dat mau={mau} t={t} />
    <g>
      {Array.from({ length: 17 }).map((_, i) => {
        const x = -660 + i * 82;
        return (
          <path key={i} d={`M ${x} 250 l 0 -168 l 26 -30 l 26 30 l 0 168 Z`}
                fill={mau.vach} stroke={mau.muc} strokeWidth={5} strokeLinejoin="round" />
        );
      })}
      <rect x={-700} y={60} width={1400} height={16} fill={mau.vach} stroke={mau.muc} strokeWidth={4} />
      <rect x={-700} y={168} width={1400} height={16} fill={mau.vach} stroke={mau.muc} strokeWidth={4} />
    </g>
    <Co mau={mau} />
  </g>
);

// ══════════════════════════════════════════════════════════════════════════════════════════
// QUẦY NGÂN HÀNG — bảng tỉ giá sau lưng, KHÔNG có chữ nào (số thật do lớp dữ liệu vẽ đè lên)
// ══════════════════════════════════════════════════════════════════════════════════════════
const Quay: React.FC<P> = ({ mau, t }) => (
  <g>
    <Troi mau={mau} t={t} id="g_q" />
    <rect x={-700} y={-260} width={1400} height={500} fill={mau.troi[1]} />
    <Dat mau={mau} t={t} />
    {/* bảng điện tử: chỉ là các thanh sáng, cố ý KHÔNG vẽ chữ */}
    <rect x={-430} y={-250} width={860} height={250} rx={16}
          fill={mau.muc} stroke={mau.vach} strokeWidth={7} />
    {Array.from({ length: 5 }).map((_, i) => (
      <g key={i}>
        <rect x={-390} y={-222 + i * 46} width={330} height={16} rx={8}
              fill={mau.nhan} opacity={0.55 + Math.sin(t * 1.4 + i) * 0.2} />
        <rect x={70} y={-222 + i * 46} width={150 + ((i * 53) % 90)} height={16} rx={8}
              fill="#F2C230" opacity={0.8} />
      </g>
    ))}
    {/* mặt quầy */}
    {/* Mặt quầy ngang HÔNG, không ngang ngực: khung thử cắt nhân vật đúng giữa thân, che mất
        cả hai tay và toàn bộ cử chỉ — mà cử chỉ tay là một trong mười thứ phải thấy được. */}
    <rect x={-700} y={196} width={1400} height={90} fill={mau.vach} stroke={mau.muc} strokeWidth={6} />
    <rect x={-700} y={196} width={1400} height={18} fill="#FFFFFF" opacity={0.35} />
  </g>
);

// ══════════════════════════════════════════════════════════════════════════════════════════
// TOÀ ÁN — cột trụ tân cổ điển
// ══════════════════════════════════════════════════════════════════════════════════════════
const ToaAn: React.FC<P> = ({ mau, t }) => (
  <g>
    <Troi mau={mau} t={t} id="g_ta" />
    <Dat mau={mau} t={t} />
    <path d={`M -520 -190 L 0 -330 L 520 -190 Z`} fill={mau.vach} stroke={mau.muc} strokeWidth={7} strokeLinejoin="round" />
    <rect x={-520} y={-190} width={1040} height={40} fill={mau.vach} stroke={mau.muc} strokeWidth={6} />
    {Array.from({ length: 6 }).map((_, i) => {
      const x = -430 + i * 172;
      return (
        <g key={i}>
          <rect x={x} y={-150} width={62} height={300} fill="#F4F1EA" stroke={mau.muc} strokeWidth={5} />
          <rect x={x - 8} y={-160} width={78} height={18} fill={mau.vach} stroke={mau.muc} strokeWidth={4} />
          <rect x={x - 8} y={142} width={78} height={18} fill={mau.vach} stroke={mau.muc} strokeWidth={4} />
        </g>
      );
    })}
    {/* bậc thềm */}
    {[0, 1, 2].map((i) => (
      <rect key={i} x={-600 - i * 40} y={160 + i * 26} width={1200 + i * 80} height={26}
            fill={mau.vach} stroke={mau.muc} strokeWidth={4} />
    ))}
  </g>
);

// ══════════════════════════════════════════════════════════════════════════════════════════
// PHÒNG LAB — giá kệ, bình thí nghiệm, KHÔNG nhãn chữ
// ══════════════════════════════════════════════════════════════════════════════════════════
const Lab: React.FC<P> = ({ mau, t }) => (
  <g>
    <Troi mau={mau} t={t} id="g_lab" />
    <Dat mau={mau} t={t} />
    <rect x={-700} y={-40} width={1400} height={270} fill="#FFFFFF" opacity={0.35} />
    {[-1, 1].map((s) => (
      <g key={s}>
        <rect x={s * 300 - 150} y={-230} width={300} height={190} rx={10}
              fill={mau.vach} stroke={mau.muc} strokeWidth={6} opacity={0.75} />
        {[0, 1].map((r) => (
          <rect key={r} x={s * 300 - 132} y={-206 + r * 88} width={264} height={12}
                fill={mau.muc} opacity={0.5} />
        ))}
        {[0, 1, 2].map((b) => (
          <path key={b} d={`M ${s * 300 - 96 + b * 76} -152 l 0 -32 l 22 0 l 0 32 l 16 40 l -54 0 Z`}
                fill={b === 1 ? mau.nhan : "#7FD1C0"} stroke={mau.muc} strokeWidth={4}
                opacity={0.85} />
        ))}
      </g>
    ))}
    {/* mặt bàn */}
    <rect x={-700} y={130} width={1400} height={30} fill={mau.vach} stroke={mau.muc} strokeWidth={5} />
  </g>
);

// ══════════════════════════════════════════════════════════════════════════════════════════
// VŨ TRỤ — sao nhấp nháy có nhịp riêng, một hành tinh, đường chân trời đài quan sát
// ══════════════════════════════════════════════════════════════════════════════════════════
const VuTru: React.FC<P> = ({ mau, t }) => (
  <g>
    <Troi mau={mau} t={t} id="g_vt" />
    {Array.from({ length: 90 }).map((_, i) => {
      // Vị trí băm cố định (không dùng random: mỗi khung render lại phải ra ĐÚNG bầu trời ấy).
      const x = ((i * 977) % 1360) - 680;
      const y = ((i * 613) % 700) - 690;
      const nhay = 0.35 + Math.abs(Math.sin(t * (0.7 + (i % 5) * 0.23) + i)) * 0.65;
      return <circle key={i} cx={x} cy={y} r={1.6 + (i % 4) * 0.9} fill="#FFFFFF" opacity={nhay} />;
    })}
    <circle cx={330} cy={-380} r={112} fill={mau.nhan} opacity={0.9} stroke={mau.muc} strokeWidth={6} />
    <ellipse cx={330} cy={-380} rx={188} ry={30} fill="none" stroke="#F6E7B8" strokeWidth={12} opacity={0.75}
             transform="rotate(-18 330 -380)" />
    <path d={`M -700 230 L -300 120 L 60 210 L 380 90 L 700 190 L 700 750 L -700 750 Z`}
          fill={mau.dat} stroke={mau.muc} strokeWidth={6} />
  </g>
);

// ══════════════════════════════════════════════════════════════════════════════════════════
// PHÒNG KHÁM — rèm, giường, màn hình theo dõi (chỉ có đường sóng, không chữ)
// ══════════════════════════════════════════════════════════════════════════════════════════
const PhongKham: React.FC<P> = ({ mau, t }) => (
  <g>
    <Troi mau={mau} t={t} id="g_pk" />
    <Dat mau={mau} t={t} />
    <rect x={-700} y={-300} width={520} height={530} fill={mau.vach} opacity={0.35} />
    {Array.from({ length: 9 }).map((_, i) => (
      <rect key={i} x={-700 + i * 58} y={-300} width={22} height={530} fill="#FFFFFF" opacity={0.4} />
    ))}
    {/* màn hình nhịp tim — đường sóng chạy theo thời gian */}
    <rect x={180} y={-260} width={420} height={220} rx={14} fill={mau.muc} stroke={mau.vach} strokeWidth={7} />
    <path d={Array.from({ length: 60 }).map((_, i) => {
      const x = 200 + i * 6.6;
      const ph = (i / 60 + t * 0.22) % 1;
      const y = -150 - (ph > 0.42 && ph < 0.5 ? Math.sin((ph - 0.42) / 0.08 * Math.PI) * 62 : 0);
      return `${i ? "L" : "M"} ${x} ${y}`;
    }).join(" ")} stroke={mau.nhan} strokeWidth={6} fill="none" strokeLinecap="round" />
    <rect x={-700} y={140} width={1400} height={26} fill={mau.vach} stroke={mau.muc} strokeWidth={5} />
  </g>
);

const VanPhong: React.FC<P> = ({ mau, t }) => (
  <g>
    <Troi mau={mau} t={t} id="g_vp" />
    <Dat mau={mau} t={t} />
    {/* cửa sổ kính lớn */}
    <rect x={-560} y={-290} width={1120} height={420} rx={12}
          fill="#CFE4F5" stroke={mau.vach} strokeWidth={9} />
    <path d="M -560 -60 L 560 -60 M 0 -290 L 0 130" stroke={mau.vach} strokeWidth={9} />
    {/* mấy khối nhà ngoài cửa sổ */}
    {[-380, -180, 130, 360].map((x, i) => (
      <rect key={i} x={x} y={-30 - (i % 3) * 60} width={110} height={160 + (i % 3) * 60}
            fill={mau.vach} opacity={0.45} />
    ))}
    <rect x={-700} y={120} width={1400} height={36} fill={mau.vach} stroke={mau.muc} strokeWidth={5} />
  </g>
);

// ══════════════════════════════════════════════════════════════════════════════════════════
// BA BỐI CẢNH BỔ SUNG — cho đủ mười, mỗi kênh một thế giới
// ------------------------------------------------------------------------------------------
// Anh: "cả template videos bối cảnh cũng thế e nha nên đa dạng phù hợp". Bảy bối cảnh cho mười
// kênh nghĩa là ba cặp kênh dùng chung một cái nền — và nền là thứ người xem nhận ra trước cả
// nhân vật, nên dùng chung nền là hai kênh trông như một ngay từ giây đầu.
// ══════════════════════════════════════════════════════════════════════════════════════════

/** THƯ PHÒNG LUẬT — tủ sách gáy dày, đèn bàn, không một chữ nào trên gáy sách. */
const ThuPhong: React.FC<P> = ({ mau, t }) => (
  <g>
    <Troi mau={mau} t={t} id="g_tp" />
    <Dat mau={mau} t={t} />
    <rect x={-700} y={-320} width={1400} height={560} fill="#6B4A2E" opacity={0.9} />
    {[0, 1, 2].map((h) => (
      <g key={h}>
        <rect x={-660} y={-300 + h * 168} width={1320} height={150} fill="#4A3220" stroke={mau.muc} strokeWidth={5} />
        {Array.from({ length: 26 }).map((_, i) => {
          const w = 34 + ((i * 37) % 22);
          const c = ["#8A2F3C", "#2C4A6E", "#3E6B4A", "#6E4A8A", "#8A6A2F"][(i + h) % 5];
          return <rect key={i} x={-648 + i * 50} y={-292 + h * 168 + ((i * 13) % 10)}
                       width={w} height={134 - ((i * 13) % 10)} fill={c}
                       stroke={mau.muc} strokeWidth={3.4} />;
        })}
      </g>
    ))}
    <ellipse cx={0} cy={-40} rx={520} ry={300} fill="#FFE9B8"
             opacity={0.18 + Math.sin(t * 0.8) * 0.03} />
  </g>
);

/** SÂN THƯỢNG ĐÊM — lan can, đường chân trời thành phố, kính thiên văn. */
const SanThuong: React.FC<P> = ({ mau, t }) => (
  <g>
    <Troi mau={mau} t={t} id="g_st" />
    {Array.from({ length: 60 }).map((_, i) => {
      const x = ((i * 811) % 1360) - 680;
      const y = ((i * 457) % 520) - 640;
      return <circle key={i} cx={x} cy={y} r={1.5 + (i % 3) * 0.8} fill="#FFFFFF"
                     opacity={0.3 + Math.abs(Math.sin(t * (0.6 + (i % 4) * 0.2) + i)) * 0.6} />;
    })}
    {/* đường chân trời thành phố — khối nhà, cửa sổ sáng nhấp nháy chậm */}
    {[-620, -430, -250, -60, 140, 330, 520].map((x, i) => {
      const h = 150 + ((i * 71) % 190);
      return (
        <g key={i}>
          <rect x={x} y={230 - h} width={150} height={h} fill={mau.dat} stroke={mau.muc} strokeWidth={5} />
          {Array.from({ length: 6 }).map((_, k) => (
            <rect key={k} x={x + 18 + (k % 3) * 44} y={244 - h + Math.floor(k / 3) * 52}
                  width={26} height={32} fill="#F2C230"
                  opacity={0.25 + Math.abs(Math.sin(t * 0.5 + i * 2 + k)) * 0.55} />
          ))}
        </g>
      );
    })}
    <rect x={-700} y={230} width={1400} height={520} fill={mau.dat} />
    {/* lan can */}
    <rect x={-700} y={196} width={1400} height={12} fill={mau.vach} stroke={mau.muc} strokeWidth={4} />
    {Array.from({ length: 20 }).map((_, i) => (
      <rect key={i} x={-680 + i * 71} y={206} width={9} height={44} fill={mau.vach}
            stroke={mau.muc} strokeWidth={3} />
    ))}
  </g>
);

/** QUẦY VIỆN PHÍ — ô kính, bảng số thứ tự (chỉ ô sáng, KHÔNG chữ), ghế chờ. */
const QuayVienPhi: React.FC<P> = ({ mau, t }) => (
  <g>
    <Troi mau={mau} t={t} id="g_vp2" />
    <rect x={-700} y={-300} width={1400} height={540} fill="#FFFFFF" opacity={0.28} />
    <Dat mau={mau} t={t} />
    {/* ô kính giao dịch */}
    <rect x={-560} y={-250} width={1120} height={330} rx={14}
          fill="#D8ECEA" stroke={mau.vach} strokeWidth={8} opacity={0.75} />
    <path d={`M -180 -250 L -180 80 M 180 -250 L 180 80`} stroke={mau.vach} strokeWidth={8} />
    {/* bảng số thứ tự — bốn ô sáng, đổi luân phiên, cố ý không có chữ số bịa */}
    {[0, 1, 2, 3].map((i) => (
      <rect key={i} x={-330 + i * 172} y={-320} width={140} height={54} rx={9}
            fill={Math.floor(t * 0.6) % 4 === i ? mau.nhan : mau.vach}
            stroke={mau.muc} strokeWidth={5} opacity={0.92} />
    ))}
    {/* mặt quầy ngang hông */}
    <rect x={-700} y={196} width={1400} height={90} fill={mau.vach} stroke={mau.muc} strokeWidth={6} />
    <rect x={-700} y={196} width={1400} height={16} fill="#FFFFFF" opacity={0.4} />
  </g>
);

/** KỆ SIÊU THỊ — hàng hoá xếp lớp, nhãn giá là ô trống (KHÔNG chữ bịa).
 *
 * 29/8 — anh chỉ vào khung WHO OWNS IT: "đừng có mà đưa kiểu bối cảnh hàng rào ko liên quan vào
 * videos như này nha". Đúng. Kênh ấy hỏi "ai thật sự sở hữu thương hiệu anh dùng hằng ngày" và
 * trả lời bằng hồ sơ SEC — một cái hàng rào sân sau chẳng dính gì tới câu hỏi lẫn câu trả lời.
 * Tôi lấy hàng rào từ ảnh tham chiếu anh gửi mà không xét xem nó có ăn nhập với NỘI DUNG kênh
 * không; đó là lỗi cùng loại với mấy kênh nét chì vẽ sương mù cho một bảng số.
 * Kệ siêu thị thì chính là chỗ người xem gặp những thương hiệu ấy mỗi tuần.
 */
const KeSieuThi: React.FC<P> = ({ mau, t }) => (
  <g>
    <Troi mau={mau} t={t} id="g_kst" />
    <Dat mau={mau} t={t} />
    <rect x={-700} y={-330} width={1400} height={570} fill="#FFFFFF" opacity={0.3} />
    {[0, 1, 2].map((h) => {
      const y = -300 + h * 180;
      return (
        <g key={h}>
          {/* mặt kệ */}
          <rect x={-680} y={y + 128} width={1360} height={20} fill={mau.vach}
                stroke={mau.muc} strokeWidth={5} />
          {/* hàng hoá: hộp, chai, lon — hình khối thuần, không nhãn chữ */}
          {Array.from({ length: 11 }).map((_, i) => {
            const x = -660 + i * 122;
            const loai = (i + h) % 3;
            const c = ["#C0392B", "#1D7A5F", "#2E4E86", "#F2A33C", "#8A2F3C"][(i * 3 + h) % 5];
            if (loai === 0) {
              return <rect key={i} x={x} y={y + 40} width={84} height={88} rx={6}
                           fill={c} stroke={mau.muc} strokeWidth={4.5} />;
            }
            if (loai === 1) {
              return (
                <g key={i}>
                  <rect x={x + 18} y={y + 18} width={26} height={30} rx={5}
                        fill={c} stroke={mau.muc} strokeWidth={4} />
                  <path d={`M ${x + 6} ${y + 128} l 0 -52 q 0 -22 24 -28 l 8 0 q 24 6 24 28 l 0 52 Z`}
                        fill={c} stroke={mau.muc} strokeWidth={4.5} strokeLinejoin="round" />
                </g>
              );
            }
            return (
              <g key={i}>
                <rect x={x + 8} y={y + 56} width={70} height={72} rx={9}
                      fill={c} stroke={mau.muc} strokeWidth={4.5} />
                <ellipse cx={x + 43} cy={y + 56} rx={35} ry={9}
                         fill="#E8E4DA" stroke={mau.muc} strokeWidth={4} />
              </g>
            );
          })}
          {/* nhãn giá: ô trắng trống, CỐ Ý không có số — số thật do lớp dữ liệu vẽ đè lên */}
          {Array.from({ length: 6 }).map((_, i) => (
            <rect key={i} x={-640 + i * 232} y={y + 132} width={62} height={22} rx={4}
                  fill="#FFFFFF" stroke={mau.muc} strokeWidth={3.5} />
          ))}
        </g>
      );
    })}
    {/* ánh đèn trần quét chậm — cho khung có nhịp sống thay vì đứng chết */}
    <ellipse cx={Math.sin(t * 0.35) * 260} cy={-220} rx={420} ry={150}
             fill="#FFFFFF" opacity={0.14} />
  </g>
);

export const BOI_CANH = {
  ke_sieu_thi: KeSieuThi,
  thu_phong: ThuPhong, san_thuong: SanThuong, quay_vien_phi: QuayVienPhi,
  san_sau: SanSau, quay: Quay, toa_an: ToaAn, lab: Lab, vu_tru: VuTru,
  phong_kham: PhongKham, van_phong: VanPhong,
} as const;

export type TenBoiCanh = keyof typeof BOI_CANH;

export const BoiCanh: React.FC<{ ten: TenBoiCanh; mau: Paltte; t: number }> = ({ ten, mau, t }) => {
  const C = BOI_CANH[ten] || SanSau;
  return <C mau={mau} t={t} />;
};
