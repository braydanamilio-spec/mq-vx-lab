import React from "react";

// ══════════════════════════════════════════════════════════════════════════════════════════
// BỘ MÔ-ĐUN ĐỒ ĐẠC — vật liệu để lắp ra hàng chục nơi chốn cho mỗi kênh
// ------------------------------------------------------------------------------------------
// Anh: *"phải đảm bảo đa dạng mỗi channel có vài chục bối cảnh phù hợp liên quan để xoay vòng
// chứ, nếu vài cái thì hơi ít và kịch bản sợ sẽ bị thu hẹp lại."*
//
// Đúng ở cả hai vế, và vế thứ hai mới là vế nặng: khi engine chỉ vẽ được một nơi chốn cho mỗi
// kênh thì bộ sinh kịch bản buộc phải viết mọi chuyện xảy ra ở đúng chỗ ấy — tức là công cụ vẽ
// đang bó tay người viết. Đó là đuôi vẫy chó.
//
// Nhưng vẽ ba mươi nền cho mười kênh là ba trăm hàm vẽ, không ai duy trì nổi. Nên đảo cách
// chia việc: KHÔNG vẽ nền, vẽ MẢNH. Hai mươi mảnh đồ đạc dưới đây, mỗi mảnh tự biết đứng trên
// sàn và tự co theo khung. Một "nơi chốn" khi ấy chỉ còn là một dòng dữ liệu — chọn ba tới năm
// mảnh, đặt vị trí, chọn bảng màu. Ba mươi nơi là ba mươi dòng.
//
// Và vì bộ mảnh là ĐÓNG, mô hình có thể sinh thêm nơi chốn mà không bao giờ ra hình bậy: nó
// chỉ được chọn trong danh sách, còn bố cục (chạm sàn, không tràn, chừa chỗ nhân vật) do code
// giữ. Đây là chỗ dùng AI đúng việc — sắp xếp, không phải vẽ.
// ══════════════════════════════════════════════════════════════════════════════════════════

const MUC = "#14110F";

export const nhat = (hex: string, t: number) => {
  const h = hex.replace("#", "");
  const n = parseInt(h.length === 3 ? h.split("").map((c) => c + c).join("") : h, 16);
  const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  const p = (v: number) => Math.round(v + (255 - v) * t);
  return `rgb(${p(r)},${p(g)},${p(b)})`;
};

/** Tham số một mảnh: x là tâm theo tỉ lệ bề ngang, co là hệ số phóng (1 = cỡ chuẩn). */
export type ThamSo = {
  x: number; co?: number; yS: number; w: number; h: number; mau: string; mauPhu: string;
};

type Ve = (p: ThamSo) => React.ReactNode;

// Mọi mảnh vẽ quanh gốc (0,0) đặt ở CHÂN của nó, rồi được `LapNoi` dịch tới chỗ cần. Nhờ vậy
// "chạm sàn" là bất biến của hệ, không phải thứ mỗi chỗ vẽ phải tự nhớ — bản trước quên nhớ
// và cho ra cái bàn treo giữa không khí.
const g = (el: React.ReactNode, sw = 4.5) => (
  <g stroke={MUC} strokeWidth={sw} strokeLinejoin="round">{el}</g>
);

export const MO_DUN: Record<string, Ve> = {
  // ── BÀN GHẾ ────────────────────────────────────────────────────────────────────────────
  ban: (p) => { const S = p.h * 0.3 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.92} y={-S * 0.44} width={S * 1.84} height={S * 0.13} rx={3}
          fill={nhat(p.mau, 0.22)} />
    <rect x={-S * 0.8} y={-S * 0.31} width={S * 0.64} height={S * 0.16}
          fill={nhat(p.mau, 0.31)} strokeWidth={3.5} />
    <rect x={-S * 0.56} y={-S * 0.25} width={S * 0.18} height={S * 0.04} rx={2} fill={MUC} />
    <rect x={-S * 0.78} y={-S * 0.31} width={S * 0.1} height={S * 0.31} fill={nhat(p.mau, 0.15)} />
    <rect x={S * 0.68} y={-S * 0.31} width={S * 0.1} height={S * 0.31} fill={nhat(p.mau, 0.15)} />
    <rect x={-S * 0.7} y={-S * 0.1} width={S * 1.4} height={S * 0.045}
          fill={nhat(p.mau, 0.12)} strokeWidth={2.5} />
  </>); },
  ban_dai: (p) => { const S = p.h * 0.3 * (p.co ?? 1); return g(<>
    <rect x={-S * 1.5} y={-S * 0.4} width={S * 3} height={S * 0.11} fill={nhat(p.mauPhu, 0.22)} />
    <rect x={-S * 1.3} y={-S * 0.29} width={S * 0.1} height={S * 0.29} fill={nhat(p.mauPhu, 0.14)} />
    <rect x={S * 1.2} y={-S * 0.29} width={S * 0.1} height={S * 0.29} fill={nhat(p.mauPhu, 0.14)} />
  </>); },
  ghe: (p) => { const S = p.h * 0.26 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.42} y={-S * 0.5} width={S * 0.84} height={S * 0.14} fill={nhat(p.mauPhu, 0.22)} />
    <rect x={-S * 0.42} y={-S} width={S * 0.16} height={S * 0.5} fill={nhat(p.mauPhu, 0.17)} />
    <rect x={-S * 0.34} y={-S * 0.36} width={S * 0.08} height={S * 0.36} fill={MUC} opacity={0.7} />
    <rect x={S * 0.26} y={-S * 0.36} width={S * 0.08} height={S * 0.36} fill={MUC} opacity={0.7} />
  </>); },
  sofa: (p) => { const S = p.h * 0.34 * (p.co ?? 1); return g(<>
    <rect x={-S} y={-S * 0.62} width={S * 2} height={S * 0.56} rx={S * 0.1} fill={nhat(p.mauPhu, 0.23)} />
    <rect x={-S} y={-S} width={S * 2} height={S * 0.42} rx={S * 0.12} fill={nhat(p.mauPhu, 0.18)} />
    {/* hai gối tựa và đường may giữa hai đệm — thiếu chúng thì sofa đọc ra là một cái bục */}
    <line x1={0} y1={-S * 0.62} x2={0} y2={-S * 0.06} strokeWidth={3.5} />
    {[-1, 1].map((d, i) => (
      <rect key={i} x={d * S * 0.52 - S * 0.19} y={-S * 0.9} width={S * 0.38} height={S * 0.34}
            rx={S * 0.06} fill={nhat(p.mauPhu, 0.12)} strokeWidth={3.5}
            transform={`rotate(${d * 8} ${d * S * 0.52} ${-S * 0.72})`} />
    ))}
    <rect x={-S * 1.08} y={-S * 0.9} width={S * 0.2} height={S * 0.84} rx={S * 0.08} fill={nhat(p.mauPhu, 0.2)} />
    <rect x={S * 0.88} y={-S * 0.9} width={S * 0.2} height={S * 0.84} rx={S * 0.08} fill={nhat(p.mauPhu, 0.2)} />
    <rect x={-S * 0.92} y={-S * 0.06} width={S * 0.09} height={S * 0.06} fill={MUC} opacity={0.75} />
    <rect x={S * 0.83} y={-S * 0.06} width={S * 0.09} height={S * 0.06} fill={MUC} opacity={0.75} />
  </>); },
  giuong: (p) => { const S = p.h * 0.3 * (p.co ?? 1); return g(<>
    <rect x={-S * 1.2} y={-S * 0.5} width={S * 2.4} height={S * 0.5} rx={6} fill={nhat(p.mauPhu, 0.28)} />
    <rect x={-S * 1.3} y={-S * 1.05} width={S * 0.16} height={S * 1.05} fill={nhat(p.mau, 0.22)} />
    <rect x={-S * 1.1} y={-S * 0.72} width={S * 0.7} height={S * 0.24} rx={6} fill="#FFFFFF" />
  </>); },

  // ── TỦ, KỆ ─────────────────────────────────────────────────────────────────────────────
  tu_ho_so: (p) => { const S = p.h * 0.46 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.34} y={-S} width={S * 0.68} height={S} fill={nhat(p.mau, 0.28)} />
    {[0, 1, 2].map((i) => (<g key={i}>
      <line x1={-S * 0.34} y1={-S + (S / 3) * (i + 1)} x2={S * 0.34} y2={-S + (S / 3) * (i + 1)} strokeWidth={3} />
      <rect x={-S * 0.1} y={-S + (S / 3) * i + S * 0.12} width={S * 0.2} height={S * 0.05} rx={3} fill={MUC} />
    </g>))}
  </>); },
  ke_sach: (p) => { const S = p.h * 0.5 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.42} y={-S} width={S * 0.84} height={S} fill={nhat(p.mau, 0.31)} />
    {[0, 1, 2].map((i) => (
      <line key={i} x1={-S * 0.42} y1={-S + (S / 3) * (i + 1)} x2={S * 0.42}
            y2={-S + (S / 3) * (i + 1)} strokeWidth={3.5} />
    ))}
    {/* sách: cao thấp khác nhau và có một cuốn ngả — hàng sách đều tăm tắp đọc ra là hoạ tiết,
        không đọc ra là sách */}
    {[0, 1, 2, 3, 4].map((i) => {
      const c = [p.mauPhu, p.mau, "#FFFFFF", p.mauPhu, p.mau][i];
      const hh = S * (0.2 + ((i * 7) % 3) * 0.035);
      return <rect key={i} x={-S * 0.37 + i * S * 0.075} y={-S * 0.97} width={S * 0.055}
                   height={hh} fill={nhat(c, 0.14)} strokeWidth={2.5} />;
    })}
    <rect x={S * 0.03} y={-S * 0.94} width={S * 0.16} height={S * 0.05}
          fill={nhat(p.mauPhu, 0.19)} strokeWidth={2.5}
          transform={`rotate(-64 ${S * 0.1} ${-S * 0.9})`} />
    {[0, 1, 2, 3].map((i) => (
      <rect key={`b${i}`} x={-S * 0.35 + i * S * 0.09} y={-S * 0.63} width={S * 0.07}
            height={S * 0.24} fill={nhat(i % 2 ? p.mau : p.mauPhu, 0.3)} strokeWidth={2.5} />
    ))}
  </>); },
  tu_lanh: (p) => { const S = p.h * 0.62 * (p.co ?? 1); return g(<>
    {/* 31/8 — vẽ kỹ lại tám mô-đun hay làm vật chủ đạo. Bản trước mỗi vật chỉ có hai ba hình
        khối, và ở cỡ một phần ba khung thì "tủ lạnh" với "tủ hồ sơ" nhìn y hệt nhau — cùng là
        một chữ nhật có một đường kẻ ngang. Thứ tách chúng ra là CHI TIẾT ĐỊNH DANH: tay nắm
        dọc dài, khe hở giữa hai cánh, mấy tờ giấy dán nam châm. */}
    <rect x={-S * 0.29} y={-S} width={S * 0.58} height={S} rx={6} fill="#FFFFFF" />
    <line x1={-S * 0.29} y1={-S * 0.6} x2={S * 0.29} y2={-S * 0.6} strokeWidth={5} />
    <rect x={-S * 0.235} y={-S * 0.55} width={S * 0.032} height={S * 0.42} rx={3} fill={MUC} />
    <rect x={-S * 0.235} y={-S * 0.94} width={S * 0.032} height={S * 0.28} rx={3} fill={MUC} />
    <rect x={-S * 0.16} y={-S * 0.9} width={S * 0.17} height={S * 0.2} fill={nhat(p.mauPhu, 0.28)}
          strokeWidth={3} transform={`rotate(-4 ${-S * 0.08} ${-S * 0.8})`} />
    <rect x={S * 0.04} y={-S * 0.86} width={S * 0.13} height={S * 0.15} fill={nhat(p.mau, 0.3)}
          strokeWidth={3} transform={`rotate(5 ${S * 0.1} ${-S * 0.78})`} />
    <rect x={-S * 0.26} y={-S * 0.04} width={S * 0.06} height={S * 0.05} fill={MUC} opacity={0.7} />
    <rect x={S * 0.2} y={-S * 0.04} width={S * 0.06} height={S * 0.05} fill={MUC} opacity={0.7} />
  </>); },
  tu_bep: (p) => { const S = p.h * 0.22 * (p.co ?? 1); return g(<>
    <rect x={-S * 1.1} y={-S} width={S * 2.2} height={S} fill={nhat(p.mau, 0.26)} />
    <rect x={-S * 1.16} y={-S * 1.12} width={S * 2.32} height={S * 0.14} rx={3}
          fill={nhat(p.mau, 0.12)} />
    {/* bồn rửa và vòi — hai thứ nói "đây là bếp" nhanh hơn bất kỳ chi tiết nào khác */}
    <rect x={-S * 0.72} y={-S * 1.06} width={S * 0.6} height={S * 0.1} rx={4}
          fill={nhat(p.mauPhu, 0.34)} strokeWidth={3} />
    <path d={`M${-S * 0.42} ${-S * 1.12} q0 ${-S * 0.22} ${S * 0.2} ${-S * 0.22}`}
          fill="none" strokeWidth={4} />
    {[0, 1, 2].map((i) => (<g key={i}>
      <line x1={-S * 1.1 + (i + 1) * S * 0.55} y1={-S} x2={-S * 1.1 + (i + 1) * S * 0.55}
            y2={0} strokeWidth={3} />
      <rect x={-S * 0.98 + i * S * 0.55} y={-S * 0.78} width={S * 0.3} height={S * 0.05}
            rx={2} fill={MUC} />
    </g>))}
  </>); },
  quay: (p) => { const S = p.h * 0.42 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.8} y={-S} width={S * 1.6} height={S} fill={nhat(p.mauPhu, 0.29)} />
    {/* mặt quầy NHÔ RA hai bên — đó là thứ tách "quầy" khỏi "một cái hộp": người ta tì tay
        lên mép nhô ấy */}
    <rect x={-S * 0.92} y={-S * 1.09} width={S * 1.84} height={S * 0.13} rx={3}
          fill={nhat(p.mauPhu, 0.15)} />
    {[0, 1, 2].map((i) => (
      <rect key={i} x={-S * 0.66 + i * S * 0.46} y={-S * 0.78} width={S * 0.36}
            height={S * 0.56} fill={nhat(p.mauPhu, 0.36)} strokeWidth={3} />
    ))}
    <rect x={S * 0.3} y={-S * 1.32} width={S * 0.34} height={S * 0.24} rx={4}
          fill={MUC} strokeWidth={4} />
    <rect x={S * 0.35} y={-S * 1.27} width={S * 0.24} height={S * 0.12}
          fill={nhat(p.mau, 0.17)} strokeWidth={0} />
  </>); },
  gia_treo: (p) => { const S = p.h * 0.5 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.04} y={-S} width={S * 0.08} height={S} fill={nhat(p.mau, 0.22)} />
    <line x1={-S * 0.4} y1={-S} x2={S * 0.4} y2={-S} />
    {[-1, 1].map((d, i) => (
      <path key={i} d={`M${d * S * 0.26} ${-S} l0 ${S * 0.1} l${d * S * 0.14} ${S * 0.34} l${-d * S * 0.28} 0 Z`}
            fill={nhat(p.mauPhu, 0.19)} />
    ))}
  </>); },

  // ── TƯỜNG, CỬA ─────────────────────────────────────────────────────────────────────────
  cua_so: (p) => { const S = p.h * 0.4 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.5} y={-S * 1.55} width={S} height={S} rx={4} fill="#FFFFFF" opacity={0.55} />
    <line x1={0} y1={-S * 1.55} x2={0} y2={-S * 0.55} />
    <line x1={-S * 0.5} y1={-S * 1.05} x2={S * 0.5} y2={-S * 1.05} />
  </>); },
  cua_ra_vao: (p) => { const S = p.h * 0.66 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.3} y={-S} width={S * 0.6} height={S} fill={nhat(p.mauPhu, 0.25)} />
    <circle cx={S * 0.2} cy={-S * 0.48} r={S * 0.035} fill={MUC} />
    <rect x={-S * 0.2} y={-S * 0.9} width={S * 0.4} height={S * 0.16} rx={2} fill="#FFFFFF" strokeWidth={3} />
  </>); },
  guong: (p) => { const S = p.h * 0.55 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.34} y={-S * 1.35} width={S * 0.68} height={S * 1.1} fill="#FFFFFF" opacity={0.5} />
    <line x1={-S * 0.3} y1={-S * 1.3} x2={S * 0.28} y2={-S * 0.75} strokeWidth={7} stroke="#FFFFFF" opacity={0.7} />
  </>); },
  bang_ghim: (p) => { const S = p.h * 0.34 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.55} y={-S * 1.5} width={S * 1.1} height={S * 0.8} fill={nhat(p.mau, 0.34)} />
    {[0, 1, 2].map((i) => (
      <rect key={i} x={-S * 0.42 + i * S * 0.34} y={-S * 1.4 + (i % 2) * S * 0.16}
            width={S * 0.24} height={S * 0.3} fill="#FFFFFF" strokeWidth={3}
            transform={`rotate(${i * 5 - 5} 0 ${-S * 1.2})`} />
    ))}
  </>); },
  hang_rao: (p) => { const S = p.h * 0.3 * (p.co ?? 1); const n = 7; return g(<>
    {Array.from({ length: n }, (_, i) => (
      <rect key={i} x={-S * 1.5 + i * (S * 3) / n} y={-S} width={(S * 3) / n - S * 0.12} height={S}
            rx={3} fill="#FFFFFF" strokeWidth={3.5} />
    ))}
    <line x1={-S * 1.5} y1={-S * 0.62} x2={S * 1.5} y2={-S * 0.62} strokeWidth={3.5} />
  </>); },
  bang_hieu: (p) => { const S = p.h * 0.3 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.7} y={-S * 1.9} width={S * 1.4} height={S * 0.5} rx={4} fill={MUC} />
    {[0, 1, 2].map((i) => (
      <rect key={i} x={-S * 0.56 + i * S * 0.42} y={-S * 1.76} width={S * 0.3} height={S * 0.22}
            fill={i === 1 ? p.mauPhu : "#FFFFFF"} opacity={0.85} strokeWidth={0} />
    ))}
  </>); },

  // ── VẬT DỤNG ───────────────────────────────────────────────────────────────────────────
  may_tinh: (p) => { const S = p.h * 0.2 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.55} y={-S} width={S * 1.1} height={S * 0.72} rx={4} fill={MUC} />
    <rect x={-S * 0.47} y={-S * 0.92} width={S * 0.94} height={S * 0.56} fill={p.mauPhu} opacity={0.8} strokeWidth={0} />
    <rect x={-S * 0.12} y={-S * 0.28} width={S * 0.24} height={S * 0.28} fill={MUC} />
  </>); },
  tv: (p) => { const S = p.h * 0.26 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.8} y={-S * 1.1} width={S * 1.6} height={S * 0.92} rx={5} fill={MUC} />
    <rect x={-S * 0.72} y={-S * 1.02} width={S * 1.44} height={S * 0.76} fill={nhat(p.mauPhu, 0.12)} strokeWidth={0} />
    <rect x={-S * 0.1} y={-S * 0.18} width={S * 0.2} height={S * 0.18} fill={MUC} />
  </>); },
  cay: (p) => { const S = p.h * 0.36 * (p.co ?? 1); return g(<>
    <path d={`M${-S * 0.22} 0 L${-S * 0.16} ${-S * 0.34} L${S * 0.16} ${-S * 0.34} L${S * 0.22} 0 Z`}
          fill={nhat(p.mau, 0.22)} />
    <circle cx={0} cy={-S * 0.66} r={S * 0.36} fill="#6FA84E" />
    <circle cx={-S * 0.26} cy={-S * 0.48} r={S * 0.24} fill="#7CB85C" />
  </>); },
  thung: (p) => { const S = p.h * 0.22 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.5} y={-S * 0.8} width={S} height={S * 0.8} fill={nhat(p.mau, 0.25)} />
    <line x1={-S * 0.5} y1={-S * 0.5} x2={S * 0.5} y2={-S * 0.5} strokeWidth={3.5} />
    <rect x={-S * 0.44} y={-S * 1.5} width={S * 0.88} height={S * 0.7} fill={nhat(p.mau, 0.32)} />
  </>); },
  gia_ta: (p) => { const S = p.h * 0.34 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.6} y={-S * 0.5} width={S * 1.2} height={S * 0.12} fill={nhat(p.mau, 0.19)} />
    <rect x={-S * 0.6} y={-S * 0.9} width={S * 1.2} height={S * 0.12} fill={nhat(p.mau, 0.19)} />
    <rect x={-S * 0.66} y={-S} width={S * 0.1} height={S} fill={nhat(p.mau, 0.12)} />
    <rect x={S * 0.56} y={-S} width={S * 0.1} height={S} fill={nhat(p.mau, 0.12)} />
    {[0, 1].map((i) => (<g key={i}>
      <circle cx={-S * 0.3 + i * S * 0.6} cy={-S * 0.76} r={S * 0.13} fill={MUC} />
    </g>))}
  </>); },
  may_ca_phe: (p) => { const S = p.h * 0.24 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.34} y={-S} width={S * 0.68} height={S} rx={4} fill={MUC} />
    <rect x={-S * 0.24} y={-S * 0.86} width={S * 0.48} height={S * 0.3} fill={nhat(p.mauPhu, 0.19)} strokeWidth={0} />
    <rect x={-S * 0.16} y={-S * 0.3} width={S * 0.32} height={S * 0.2} fill="#FFFFFF" strokeWidth={3} />
  </>); },
  xe: (p) => { const S = p.h * 0.34 * (p.co ?? 1); return g(<>
    <rect x={-S * 1.3} y={-S * 0.66} width={S * 2.6} height={S * 0.46} rx={S * 0.16}
          fill={nhat(p.mauPhu, 0.19)} />
    <rect x={-S * 0.8} y={-S * 0.96} width={S * 1.5} height={S * 0.34} rx={S * 0.12}
          fill={nhat(p.mauPhu, 0.3)} />
    {/* kính, đường cửa, đèn, tay nắm — bốn chi tiết tách "xe" khỏi "một khối bo tròn" */}
    <path d={`M${-S * 0.7} ${-S * 0.92} l${S * 0.16} ${-S * 0.0} l0 ${S * 0.28} l${-S * 0.2} 0 Z`}
          fill="#FFFFFF" opacity={0.55} strokeWidth={3} />
    <path d={`M${-S * 0.34} ${-S * 0.94} l${S * 0.5} 0 l0 ${S * 0.3} l${-S * 0.5} 0 Z`}
          fill="#FFFFFF" opacity={0.45} strokeWidth={3} />
    <line x1={-S * 0.36} y1={-S * 0.96} x2={-S * 0.36} y2={-S * 0.22} strokeWidth={3} />
    <rect x={-S * 0.5} y={-S * 0.52} width={S * 0.16} height={S * 0.04} rx={2} fill={MUC} />
    <ellipse cx={S * 1.24} cy={-S * 0.5} rx={S * 0.09} ry={S * 0.07} fill="#FFE9A8" strokeWidth={3} />
    <circle cx={-S * 0.8} cy={-S * 0.16} r={S * 0.24} fill={MUC} />
    <circle cx={-S * 0.8} cy={-S * 0.16} r={S * 0.1} fill={nhat(p.mau, 0.34)} />
    <circle cx={S * 0.8} cy={-S * 0.16} r={S * 0.24} fill={MUC} />
    <circle cx={S * 0.8} cy={-S * 0.16} r={S * 0.1} fill={nhat(p.mau, 0.34)} />
  </>); },
};

// ── MẢNH TREO TƯỜNG ────────────────────────────────────────────────────────────────────
// 31/8 — Khung dọc 9:16 với hai người vẽ cả thân thì nền chỉ còn hai dải mép, và cả nửa trên
// là tường trơn. Đồ đứng sàn không với tới đó được (chúng chỉ cao tới ngang ngực người). Nhóm
// này treo ở tầm mắt trở lên — chỗ mà nhân vật không bao giờ che, và cũng là chỗ mắt người xem
// đi qua khi đọc bong bóng thoại.
export const MO_TREO: Record<string, Ve> = {
  tranh: (p) => { const S = p.h * 0.12 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.7} y={-S * 0.55} width={S * 1.4} height={S * 1.1} fill={nhat(p.mauPhu, 0.25)} />
    <rect x={-S * 0.56} y={-S * 0.42} width={S * 1.12} height={S * 0.84} fill="#FFFFFF" strokeWidth={3} />
    <path d={`M${-S * 0.5} ${S * 0.36} L${-S * 0.16} ${-S * 0.16} L${S * 0.12} ${S * 0.12}
              L${S * 0.36} ${-S * 0.24} L${S * 0.5} ${S * 0.36} Z`}
          fill={nhat(p.mau, 0.22)} strokeWidth={3} />
  </>); },
  dong_ho: (p) => { const S = p.h * 0.1 * (p.co ?? 1); return g(<>
    <circle cx={0} cy={0} r={S} fill="#FFFFFF" />
    <line x1={0} y1={0} x2={0} y2={-S * 0.6} strokeWidth={5} />
    <line x1={0} y1={0} x2={S * 0.42} y2={S * 0.2} strokeWidth={5} />
  </>); },
  ke_treo: (p) => { const S = p.h * 0.13 * (p.co ?? 1); return g(<>
    <rect x={-S} y={0} width={S * 2} height={S * 0.16} fill={nhat(p.mau, 0.23)} />
    {[0, 1, 2].map((i) => (
      <rect key={i} x={-S * 0.8 + i * S * 0.55} y={-S * 0.5} width={S * 0.34} height={S * 0.5}
            fill={i % 2 ? nhat(p.mauPhu, 0.17) : nhat(p.mau, 0.14)} strokeWidth={3.5} />
    ))}
  </>); },
  bang_trang: (p) => { const S = p.h * 0.16 * (p.co ?? 1); return g(<>
    <rect x={-S * 1.1} y={-S * 0.7} width={S * 2.2} height={S * 1.4} fill="#FFFFFF" />
    {[0, 1].map((i) => (
      <line key={i} x1={-S * 0.85} y1={-S * 0.3 + i * S * 0.45} x2={S * (0.5 - i * 0.35)}
            y2={-S * 0.3 + i * S * 0.45} strokeWidth={4} stroke={i ? p.mauPhu : p.mau} />
    ))}
  </>); },
  cua_so_cao: (p) => { const S = p.h * 0.17 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.8} y={-S * 0.8} width={S * 1.6} height={S * 1.6} rx={4}
          fill="#FFFFFF" opacity={0.55} />
    <line x1={0} y1={-S * 0.8} x2={0} y2={S * 0.8} />
    <line x1={-S * 0.8} y1={0} x2={S * 0.8} y2={0} />
  </>); },
  bien_bao: (p) => { const S = p.h * 0.11 * (p.co ?? 1); return g(<>
    <rect x={-S} y={-S * 0.42} width={S * 2} height={S * 0.84} rx={5} fill={nhat(p.mau, 0.17)} />
    <rect x={-S * 0.78} y={-S * 0.2} width={S * 1.1} height={S * 0.16} fill="#FFFFFF" strokeWidth={0} />
  </>); },
};

// ── SÁU MẢNH ĐẶC MỸ ────────────────────────────────────────────────────────────────────
// Anh: *"bối cảnh cũng vẽ theo chuẩn style usa chứ e"*. Nơi chốn thì đã Mỹ từ tên gọi (HOA,
// DMV, drive-thru), nhưng ĐỒ ĐẠC thì vẫn trung tính — một cái bàn với một cái tủ thì ở nước
// nào cũng thế. Sáu mảnh dưới đây là thứ người Mỹ nhìn phát ra ngay, và người nước khác nhìn
// cũng đọc ra "đây là nước Mỹ": hộp thư trụ ngoài sân, cửa lưới chống muỗi, máy nước lạnh văn
// phòng, cửa cuốn gara, ghế booth quán ăn, lò vi sóng đặt trên bếp.
export const MO_MY: Record<string, Ve> = {
  hop_thu_tru: (p) => { const S = p.h * 0.3 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.05} y={-S} width={S * 0.1} height={S} fill={nhat(p.mau, 0.19)} />
    <path d={`M${-S * 0.3} ${-S} l0 ${-S * 0.2} a${S * 0.3} ${S * 0.22} 0 0 1 ${S * 0.6} 0 l0 ${S * 0.2} Z`}
          fill={nhat(p.mauPhu, 0.22)} />
    <rect x={-S * 0.3} y={-S * 1.06} width={S * 0.08} height={S * 0.06} fill="#C0392B" />
  </>); },
  cua_luoi: (p) => { const S = p.h * 0.62 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.3} y={-S} width={S * 0.6} height={S} fill={nhat(p.mauPhu, 0.33)} />
    {[0, 1, 2, 3].map((i) => (
      <line key={i} x1={-S * 0.3 + i * S * 0.2} y1={-S} x2={-S * 0.3 + i * S * 0.2} y2={0}
            strokeWidth={2.5} opacity={0.5} />
    ))}
    <rect x={-S * 0.26} y={-S * 0.94} width={S * 0.52} height={S * 0.4} fill="#FFFFFF" opacity={0.35} />
  </>); },
  may_nuoc: (p) => { const S = p.h * 0.4 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.22} y={-S * 0.62} width={S * 0.44} height={S * 0.62} fill={nhat(p.mau, 0.3)} />
    <path d={`M${-S * 0.2} ${-S * 0.62} l${S * 0.06} ${-S * 0.38} l${S * 0.28} 0 l${S * 0.06} ${S * 0.38} Z`}
          fill={nhat(p.mauPhu, 0.14)} />
    <rect x={-S * 0.06} y={-S * 0.36} width={S * 0.12} height={S * 0.08} fill={MUC} />
  </>); },
  cua_cuon: (p) => { const S = p.h * 0.72 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.5} y={-S} width={S} height={S} fill={nhat(p.mau, 0.28)} />
    {[0, 1, 2, 3, 4].map((i) => (
      <line key={i} x1={-S * 0.5} y1={-S + (S / 5) * (i + 1)} x2={S * 0.5}
            y2={-S + (S / 5) * (i + 1)} strokeWidth={3.5} opacity={0.7} />
    ))}
  </>); },
  booth: (p) => { const S = p.h * 0.34 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.9} y={-S * 0.46} width={S * 1.8} height={S * 0.46} rx={4}
          fill={nhat(p.mauPhu, 0.19)} />
    <rect x={-S * 0.9} y={-S * 1.12} width={S * 1.8} height={S * 0.68} rx={S * 0.1}
          fill={nhat(p.mauPhu, 0.15)} />
    {[0, 1, 2].map((i) => (
      <line key={i} x1={-S * 0.5 + i * S * 0.5} y1={-S * 1.06} x2={-S * 0.5 + i * S * 0.5}
            y2={-S * 0.5} strokeWidth={3} opacity={0.55} />
    ))}
  </>); },
  lo_vi_song: (p) => { const S = p.h * 0.16 * (p.co ?? 1); return g(<>
    <rect x={-S * 0.7} y={-S * 0.62} width={S * 1.4} height={S * 0.62} rx={4} fill={MUC} />
    <rect x={-S * 0.6} y={-S * 0.54} width={S * 0.86} height={S * 0.46} fill={nhat(p.mauPhu, 0.17)} />
    <circle cx={S * 0.48} cy={-S * 0.32} r={S * 0.07} fill="#FFFFFF" strokeWidth={2.5} />
  </>); },
};

export const TEN_MO_MY = Object.keys(MO_MY);
export const TEN_MO_TREO = Object.keys(MO_TREO);
export const TEN_MO_DUN = Object.keys(MO_DUN);
