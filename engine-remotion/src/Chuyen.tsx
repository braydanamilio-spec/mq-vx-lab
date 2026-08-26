import { Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import React from "react";

// ─────────────────────────────────────────────────────────────────────────────
// HỆ CHUYỂN CẢNH DÙNG CHUNG (26/8/2026)
//
// VÌ SAO CÓ FILE NÀY
// Trước đây mỗi composition tự rắc âm hiệu: `RankedShort` 2 chỗ, `LongshotShort` 3 chỗ,
// `MappedShort` KHÔNG chỗ nào — và mỗi file tự đặt `volume` bằng một con số viết tay
// (0.22 · 0.32 · 0.4 · 0.45 · 0.5 · 0.55 · 0.6 · 0.7). Hậu quả đo được:
//   • hai kênh cạnh nhau nghe to nhỏ khác hẳn, không ai chỉnh nổi vì phải sửa 12 file;
//   • có kênh im lìm suốt video, có kênh âm hiệu ĐÈ CẢ LỜI DẪN;
//   • âm phát một đằng, hình đổi một nẻo — không có nhịp chung nên xem thấy rời rạc.
//
// Ở đây: MỘT nhịp -> đồng thời một tiếng và một chuyển động hình. Mức âm quyết ở một chỗ.
//
// KHÔNG LẶP MỘT MÔ-TÍP: mỗi kênh nhận một "tính cách chuyển cảnh" riêng, suy ra từ tên
// kênh nên cố định vĩnh viễn (cùng kênh -> cùng motif ở mọi video, mọi phiên), mà 4 kênh
// khác nhau thì gần như chắc chắn khác nhau. Đây là chỗ đáp yêu cầu "không lặp lại nhàm
// chán 1 motip" bằng cơ chế, không bằng lời dặn.
// ─────────────────────────────────────────────────────────────────────────────

export type Motif = "quet" | "dap" | "no" | "chuong";

/** Nhịp = một khoảnh khắc đáng đánh dấu (mục mới hiện, thứ hạng lật, cảnh đổi).
 *  `manh` 0..1 = tầm quan trọng; #1 mạnh hơn #3 nên nghe và nhìn cũng phải khác. */
export type Nhip = { at: number; manh?: number };

/** MỨC ÂM — QUYẾT Ở ĐÚNG MỘT CHỖ.
 *  Chuẩn: âm hiệu là dấu chấm câu, KHÔNG được tranh chỗ với lời dẫn. Lời dẫn đã chuẩn hoá
 *  quanh -16 LUFS; các mức dưới đây nằm đủ thấp để nghe rõ mà không nuốt giọng. Sửa mức thì
 *  sửa ở đây, không rắc số vào composition — rắc lại là quay về đúng mớ 8 con số cũ. */
export const MUC_AM: Record<string, number> = {
  whoosh: 0.30,
  pop: 0.34,
  ding: 0.36,
  impact: 0.46,
  cheer: 0.28,
};

/** Tiếng của từng motif: [tiếng thường, tiếng cho nhịp MẠNH nhất]. */
const TIENG: Record<Motif, [string, string]> = {
  quet: ["whoosh", "impact"],
  dap: ["impact", "impact"],
  no: ["pop", "impact"],
  chuong: ["ding", "cheer"],
};

/** Băm ổn định (FNV-1a rút gọn). Cùng chuỗi -> cùng số, ở mọi máy, mọi lần chạy.
 *  Không dùng random: kênh phải giữ nguyên tính cách qua các phiên, nếu không thì mỗi video
 *  một kiểu — đúng cái "nhàm chán vì lộn xộn" thay cho "nhàm chán vì lặp". */
export const bam = (s: string): number => {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  // TRỘN LẠI TRƯỚC KHI DÙNG. Bỏ bước này thì `% 4` chỉ ăn 2 bit thấp của FNV, mà 2 bit thấp lại
  // bám rất chặt vào KÝ TỰ CUỐI — trong khi 50 handle gen-2 hầu hết kết thúc bằng "usa". Đo thật
  // trên đúng 50 handle đó: chia 7/11/14/18 (lệch 11) tức có motif dùng gấp 2,5 lần motif khác.
  // Sau khi trộn, đo lại trên đúng 50 handle đó: 11/12/12/15 (lệch 4). Một hàm băm không thể chia đều
  // tuyệt đối khi chưa biết trước cả tập; muốn đều tuyệt đối phải gán motif lúc ĐĂNG KÝ kênh rồi truyền qua prop
  // `motif` (đường đó đã mở sẵn ở dưới) — ghi ra đây để sau này khỏi tưởng đã đều.
  h ^= h >>> 15;
  h = Math.imul(h, 2246822519);
  h ^= h >>> 13;
  return h >>> 0;
};

const MOTIFS: Motif[] = ["quet", "dap", "no", "chuong"];

/** Motif cố định của một kênh, suy từ tên/handle. */
export const chonMotif = (khoa: string): Motif => MOTIFS[bam(String(khoa || "")) % MOTIFS.length];

const DAI = 9;   // khung: chuyển cảnh dài ~0,3s. Dài hơn thành hiệu ứng, ngắn hơn thành giật.

/**
 * Lớp phủ chuyển cảnh + âm hiệu, ăn theo cùng một danh sách nhịp.
 *
 * Cố ý giữ NHẸ: đây là dấu chấm câu giữa các mục, không phải màn trình diễn. Một cú loé
 * chiếm hết khung hình vừa xấu vừa làm khán giả mất dấu nội dung đang đọc dở.
 * Đặt `pointerEvents:none` và không nền đục, nên không bao giờ che chữ.
 */
export const ChuyenCanh: React.FC<{
  nhip: Nhip[];
  accent: string;
  motif?: Motif;
  khoa?: string;
  im?: boolean;
}> = ({ nhip, accent, motif, khoa = "", im = false }) => {
  const f = useCurrentFrame();
  const { width: W, height: H } = useVideoConfig();
  const mo: Motif = motif || chonMotif(khoa);
  const [thuong, manhTieng] = TIENG[mo];

  // Nhịp gần nhất đã qua và còn trong tầm ảnh hưởng -> quyết định phần HÌNH.
  let gan: Nhip | null = null;
  for (const n of nhip) {
    if (f >= n.at && f < n.at + DAI && (!gan || n.at > gan.at)) gan = n;
  }
  const t = gan ? interpolate(f - gan.at, [0, DAI], [0, 1], { extrapolateRight: "clamp" }) : 1;
  const suc = (gan?.manh ?? 0.6) * (1 - t);   // tắt dần: mạnh nhất ngay khung đầu

  let hinh: React.CSSProperties | null = null;
  if (gan) {
    if (mo === "quet") {
      // Vệt sáng quét ngang, đi từ trái sang phải đúng trong 9 khung.
      const x = interpolate(t, [0, 1], [-40, 140]);
      hinh = {
        background: `linear-gradient(105deg, transparent ${x - 26}%, ${accent}${Math.round(suc * 90).toString(16).padStart(2, "0")} ${x}%, transparent ${x + 26}%)`,
      };
    } else if (mo === "dap") {
      // Rung nhẹ + tối viền: cảm giác "đóng dấu". Không đổi layout, chỉ transform lớp phủ.
      hinh = {
        boxShadow: `inset 0 0 ${Math.round(160 * suc)}px ${Math.round(60 * suc)}px #000`,
        transform: `translateX(${Math.sin((f - gan.at) * 2.1) * suc * 7}px)`,
      };
    } else if (mo === "no") {
      // Vòng sáng lan từ tâm.
      const r = interpolate(t, [0, 1], [4, 78]);
      hinh = {
        background: `radial-gradient(circle at 50% 46%, transparent ${r - 5}%, ${accent}${Math.round(suc * 70).toString(16).padStart(2, "0")} ${r}%, transparent ${r + 6}%)`,
      };
    } else {
      // "chuong": ánh sáng doi lên từ đáy, hợp với các dạng có bảng xếp hạng ở dưới.
      hinh = {
        background: `linear-gradient(to top, ${accent}${Math.round(suc * 64).toString(16).padStart(2, "0")} 0%, transparent ${Math.round(18 + t * 26)}%)`,
      };
    }
  }

  return (
    <>
      {hinh ? (
        <div style={{ position: "absolute", inset: 0, width: W, height: H, pointerEvents: "none", zIndex: 40, ...hinh }} />
      ) : null}
      {im
        ? null
        : nhip.map((n, i) => {
            const manh = n.manh ?? 0.6;
            const ten = manh >= 0.95 ? manhTieng : thuong;
            const goc = MUC_AM[ten] ?? 0.35;
            // Nhịp phụ nhẹ hơn nhịp chính: cùng một tiếng nhưng khác trọng lượng, tai nghe ra
            // thứ bậc mà không cần thêm file âm thanh nào.
            const vol = Math.max(0.12, goc * (0.62 + manh * 0.38));
            if (n.at < 0) return null;
            return (
              <Sequence key={`sfx${i}`} from={Math.round(n.at)} durationInFrames={30}>
                <Audio src={staticFile(`sfx/${ten}.mp3`)} volume={vol} />
              </Sequence>
            );
          })}
    </>
  );
};
