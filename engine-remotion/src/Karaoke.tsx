import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";

// PHỤ ĐỀ KARAOKE DÙNG CHUNG CHO MỌI SHORT (24/8/2026 tối — anh: "short cũng nên có sub karaoke").
//
// Trước bản này, 9 định dạng short KHÔNG có phụ đề nào: `subs` nằm trong khai báo props nhưng
// không lớp nào vẽ, còn Python thì `du, _, _ = TK.synth(...)` — vứt thẳng mốc từng từ mà edge-tts
// đã trả sẵn. Người xem tắt tiếng (phần lớn lượt xem đầu tiên trên feed) không đọc được gì.
//
// Hai điều bắt buộc, rút từ đúng cái lỗi "chữ chồng chéo" hôm nay:
//  • BĂNG CHỮ CÓ CHỖ CỐ ĐỊNH. `BOTTOM = 200` nằm TRÊN mọi thứ đang neo đáy của 8 component short
//    (chỗ thấp nhất chúng dùng là bottom 150). Không đặt tuỳ hứng theo từng file.
//  • TỐI ĐA 2 DÒNG. Cắt cụm theo dấu câu / khoảng lặng ≥0,35s, mỗi cụm ≤ 7 từ — dài hơn là băng
//    chữ tự cao lên và đâm vào nội dung phía trên, đúng cái bẫy vừa vá ở Cinematic.

export type Word = { t: number; d: number; w: string };

const BOTTOM = 200;          // đáy băng chữ khổ DỌC — TRÊN mọi thứ neo đáy của các short (≤150)
// 26/8 — khổ NGANG (long 16:9) chỉ cao 1080 so với 1920: giữ nguyên `bottom 200` là băng chữ ngồi
// giữa màn hình, đè thẳng vào bảng/biểu đồ. Và cỡ chữ 56 trên khung cao 1080 chiếm gần 1/8 chiều
// cao. Nên khổ ngang có bộ số riêng, y như bố cục — không phải bản dọc kéo giãn.
const BOTTOM_NGANG = 88;
const TOI_DA_TU = 7;         // mỗi cụm tối đa 7 từ (2 dòng ở cỡ chữ 44)
const NGHI = 0.35;           // khoảng lặng ≥ mức này là sang cụm mới

type Cum = { tu: Word[]; s: number; e: number };

const chia = (subs: Word[]): Cum[] => {
  const ra: Cum[] = [];
  let cur: Word[] = [];
  const dong = () => {
    if (!cur.length) return;
    ra.push({ tu: cur, s: cur[0].t, e: cur[cur.length - 1].t + cur[cur.length - 1].d });
    cur = [];
  };
  for (let i = 0; i < subs.length; i++) {
    const w = subs[i];
    const truoc = subs[i - 1];
    if (cur.length && truoc && w.t - (truoc.t + truoc.d) >= NGHI) dong();
    cur.push(w);
    if (cur.length >= TOI_DA_TU || /[.!?]$/.test(w.w)) dong();
  }
  dong();
  return ra;
};

export const Karaoke: React.FC<{ subs?: Word[]; accent?: string; bottom?: number;
                                 kieu?: "doc" | "toon" }> = ({
  subs = [], accent = "#F5B301", bottom = BOTTOM, kieu = "doc",
}) => {
  const f = useCurrentFrame();
  const { fps, width: _W, height: _H } = useVideoConfig();
  const ngang = _W > _H;
  const day = bottom !== BOTTOM ? bottom : (ngang ? BOTTOM_NGANG : BOTTOM);
  const co = (n: number) => (ngang ? Math.round(n * 0.72) : n);
  const now = f / fps;
  const cums = React.useMemo(() => chia(subs || []), [subs]);
  if (!cums.length) return null;
  // Cụm đang đọc; giữa hai cụm thì bám cụm vừa xong ≤0,4s để chữ không nhấp nháy.
  let cum = cums.find((c) => now >= c.s - 0.08 && now <= c.e + 0.12);
  if (!cum) {
    const xong = cums.filter((c) => c.e < now);
    const cuoi = xong[xong.length - 1];
    if (cuoi && now - cuoi.e <= 0.4) cum = cuoi;
  }
  if (!cum) return null;
  // KIỂU CHỮ THEO THỂ LOẠI (25/8). Khung đen bo góc là ngôn ngữ của phim tài liệu — dán nó lên
  // phim hoạt hình là lạc tông ngay. Phim hài Mỹ dùng chữ VIỀN DÀY không nền, chữ đang đọc thì
  // NẢY lên và đổi màu: đọc rõ trên mọi nền mà vẫn giữ chất truyện tranh.
  const toon = kieu === "toon";
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: day, padding: ngang ? "0 140px" : "0 64px", textAlign: "center" }}>
      <div style={{ display: "inline-block", maxWidth: "100%",
                    background: toon ? "transparent" : "rgba(0,0,0,0.62)",
                    borderRadius: 18, padding: toon ? "6px 10px" : "10px 22px", lineHeight: 1.32 }}>
        {cum.tu.map((w, i) => {
          const on = now >= w.t - 0.05 && now < w.t + w.d + 0.05;
          if (toon) {
            return (
              <span key={i} style={{
                fontSize: on ? co(56) : co(50), fontWeight: 900, margin: "0 8px",
                display: "inline-block", color: on ? accent : "#FFFFFF",
                WebkitTextStroke: "9px #14161C", paintOrder: "stroke fill",
                letterSpacing: -1,
                transform: on ? "translateY(-6px) rotate(-1.5deg)" : "none",
                filter: on ? `drop-shadow(0 0 16px ${accent}88)` : "drop-shadow(0 4px 0 rgba(0,0,0,.4))",
              } as React.CSSProperties}>{w.w}</span>
            );
          }
          return (
            <span key={i} style={{ fontSize: co(44), fontWeight: 900, margin: "0 7px",
                                   display: "inline-block", color: on ? accent : "#F2F7FF",
                                   transform: on ? "scale(1.07)" : "scale(1)",
                                   textShadow: on ? `0 3px 18px rgba(0,0,0,.95), 0 0 18px ${accent}77`
                                                  : "0 3px 18px rgba(0,0,0,.95)" }}>
              {w.w}
            </span>
          );
        })}
      </div>
    </div>
  );
};

export default Karaoke;
