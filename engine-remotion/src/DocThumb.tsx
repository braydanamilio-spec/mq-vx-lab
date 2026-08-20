import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";

// 🖼️ THUMBNAIL cho 21 kênh format "doc".
// TRƯỚC ĐÂY: cắt đại 1 khung hình từ video -> mờ nhạt, không chữ, CTR thấp.
// GIỜ: ảnh thật của video + GRADE MÀU THEO BRAND (duotone) + nêm chéo + chữ hook viền dày phát sáng
// -> nhìn ra ngay là ảnh THIẾT KẾ, không phải ảnh chụp màn hình. Đọc rõ ở cỡ nhỏ trên feed.
export type DocThumbProps = {
  bg?: string;        // ảnh GỐC SẠCH của chính video (public/<slug>/clips/sN.jpg) — mỗi video một ảnh khác
  big: string;        // tiêu đề (dùng khi KHÔNG có số liệu)
  kicker?: string;    // dòng nhỏ phía trên (tên kênh)
  stat?: string;      // SỐ LIỆU gây sốc, ngắn: "$4.7B" / "92%" / "1 IN 6"
  statLabel?: string; // số đó là gì: "OF US TAP WATER"
  hook?: string;      // CÂU HỎI MỞ gây tò mò, KHÔNG trả lời: "IS YOURS ON THE LIST?"
  accent?: string;
  accent2?: string;
};

// AUTO-FIT: tiêu đề dài phải NHỎ lại cho vừa khung (bài học chữ tràn khung avatar brand).
// CHAR_W đo THẬT từ ảnh render (không đoán): Poppins weight 800-900 IN HOA có bề rộng trung bình
// ~0.58em/ký tự. Trước đây để 0.5 -> fitSize tưởng chữ hẹp hơn thực ~16% -> tiêu đề/nhãn/hook đều
// tính ra cỡ chữ QUÁ TO -> tràn quá lề phải và lòi ra ngoài nền pill (thấy rõ khi test chữ dài).
// Để 0.62 (dư an toàn trên mức đo 0.58) vì còn letterSpacing cộng thêm.
const CHAR_W = 0.62;
const fitSize = (lines: string[], maxW: number, base: number) => {
  const longest = lines.reduce((a, l) => Math.max(a, l.length), 1);
  const est = longest * base * CHAR_W;
  return est > maxW ? Math.floor((base * maxW) / est) : base;
};

// XUỐNG DÒNG KHÔNG BAO GIỜ MẤT CHỮ.
// TRƯỚC ĐÂY: gói cứng 13 ký tự/dòng rồi `if (lines.length === 3) break` -> tiêu đề dài bị CẮT CỤT
// GIỮA CÂU (thử thật: "The State Americans Are Fleeing The Fastest And It Is Not California"
// hiện ra thành "THE STATE / AMERICANS ARE / FLEEING THE" — cụt, mất nghĩa, phản tác dụng CTR).
// GIỜ: nới dần hạn mức ký tự/dòng cho tới khi TOÀN BỘ chữ nằm gọn trong maxLines; cỡ chữ do
// fitSize() tự thu lại. Thà chữ nhỏ hơn một chút còn hơn mất nghĩa.
const wrapAll = (words: string[], maxLines: number, startPer = 13): string[] => {
  let per = startPer;
  for (let guard = 0; guard < 10; guard++) {
    const ls: string[] = [];
    let cur = "";
    for (const w of words) {
      if (!cur) cur = w;
      else if ((cur + " " + w).length <= per) cur += " " + w;
      else { ls.push(cur); cur = w; }
    }
    if (cur) ls.push(cur);
    if (ls.length <= maxLines) return ls;
    per = Math.ceil(per * 1.25) + 1;
  }
  return [words.join(" ")];   // cực đoan: 1 dòng, fitSize lo phần thu nhỏ
};

export const DocThumb: React.FC<DocThumbProps> = ({
  bg, big, kicker = "", stat = "", statLabel = "", hook = "",
  accent = "#22D3EE", accent2 = "#F5B301",
}) => {
  // CÔNG THỨC CTR: SỐ LIỆU GÂY SỐC + CÂU HỎI MỞ (không trả lời) > tiêu đề dài.
  // Có stat -> bố cục "số to + nhãn + câu hỏi". Không có stat -> lùi về bố cục tiêu đề (bên dưới).
  const useStat = !!String(stat).trim();
  // CHỐNG THUMBNAIL TRẮNG: Gemini thi thoảng trả tiêu đề rỗng -> trước đây ra ảnh trống trơn chỉ có
  // tên kênh. Lùi về kicker để luôn có chữ.
  const bigSafe = (big || "").trim() || kicker || "";
  // Tối đa 4 dòng, ưu tiên ~13 ký tự/dòng -> chữ TO; dài quá thì wrapAll tự nới (không cắt chữ).
  const words = bigSafe.toUpperCase().trim().split(/\s+/).filter(Boolean);
  const lines = words.length ? wrapAll(words, 4, 13) : [];
  // Vùng chữ thật = 1280 - left(62) - right(300) = 918px. Trước đây fit theo 1080 -> chữ TRÀN sát mép phải.
  const fs = fitSize(lines, 900, 138);
  // HOOK: trước đây cỡ chữ CỐ ĐỊNH 44 + nowrap -> câu hỏi dài TRÀN HẲN RA NGOÀI KHUNG, bị cắt cụt
  // ("...WANTS TO TA"). Giờ auto-fit; ngắn thì 1 dòng chữ to, quá dài thì xuống dòng thay vì tràn.
  const hookFit = fitSize([String(hook)], 820, 44);
  const hookWrap = hookFit < 32;

  return (
    <AbsoluteFill style={{ background: "#07080f", fontFamily: "'Poppins',Arial", overflow: "hidden" }}>
      {/* 1. ẢNH THẬT của video — hơi phóng to + lệch phải để chừa chỗ chữ bên trái */}
      {bg ? (
        <Img src={staticFile(bg)} style={{
          width: "100%", height: "100%", objectFit: "cover",
          transform: "scale(1.12) translateX(6%)", filter: "contrast(1.15) saturate(1.25) brightness(0.92)",
        }} />
      ) : (
        // DỰ PHÒNG khi không trích được khung: KHÔNG để nền phẳng chán — dựng nền có chiều sâu bằng
        // nhiều lớp sáng brand + lưới mảnh, để vẫn ra chất "thiết kế" chứ không phải nền màu trơn.
        <AbsoluteFill>
          <AbsoluteFill style={{ background: `radial-gradient(70% 90% at 78% 28%, ${accent}88, transparent 62%)` }} />
          <AbsoluteFill style={{ background: `radial-gradient(60% 70% at 90% 88%, ${accent2}66, transparent 66%)` }} />
          <AbsoluteFill style={{ background: `conic-gradient(from 210deg at 74% 44%, ${accent}33, transparent 30%, ${accent2}2A 62%, transparent 84%)` }} />
          <AbsoluteFill style={{
            backgroundImage: `linear-gradient(${accent}14 1px, transparent 1px), linear-gradient(90deg, ${accent}14 1px, transparent 1px)`,
            backgroundSize: "64px 64px", maskImage: "radial-gradient(70% 70% at 72% 44%, #000, transparent 75%)",
          } as React.CSSProperties} />
          <AbsoluteFill style={{ background: "linear-gradient(180deg, transparent 40%, #05060cCC 100%)" }} />
        </AbsoluteFill>
      )}

      {/* 2. DUOTONE theo màu brand -> ảnh trông ĐƯỢC THIẾT KẾ, mỗi kênh 1 sắc riêng, không giống ảnh chụp */}
      {/* duotone NHẸ tay (0.26): đủ để mỗi kênh 1 sắc riêng, KHÔNG nuốt mất chi tiết/màu ảnh gốc */}
      <AbsoluteFill style={{ background: accent, mixBlendMode: "color", opacity: 0.26 }} />
      {/* tối bên TRÁI vừa đủ đọc chữ, nhả nhanh sang phải để ảnh còn "thở" (trước F2/D9 quá nặng, che hết ảnh) */}
      <AbsoluteFill style={{ background: `linear-gradient(112deg, #05060cE8 0%, #05060cA8 30%, transparent 56%)` }} />
      <AbsoluteFill style={{ background: `radial-gradient(46% 62% at 22% 62%, ${accent2}2E, transparent 70%)` }} />

      {/* 3. NÊM CHÉO phát sáng — mảng hình học tạo chiều sâu, cắt qua khung */}
      <div style={{
        position: "absolute", left: -90, bottom: -140, width: 640, height: 640,
        background: `linear-gradient(140deg, ${accent}, ${accent2})`, opacity: 0.20,
        transform: "rotate(24deg)", borderRadius: 40, filter: "blur(2px)",
      }} />
      {/* viền sáng mảnh chạy chéo -> nét "cinematic", tách nền khỏi chữ */}
      <div style={{
        position: "absolute", left: -40, bottom: 236, width: 1500, height: 4,
        background: `linear-gradient(90deg, ${accent}, ${accent2}00)`, transform: "rotate(-3deg)",
        boxShadow: `0 0 26px ${accent}`,
      }} />

      {/* 4. VIGNETTE điện ảnh */}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px 110px rgba(0,0,0,0.72)" }} />

      {/* 5. KICKER: tên kênh, có chấm sáng nhịp */}
      {kicker ? (
        <div style={{ position: "absolute", top: 50, left: 62, display: "flex", alignItems: "center", gap: 15 }}>
          <div style={{ width: 15, height: 48, background: accent, borderRadius: 4, boxShadow: `0 0 26px ${accent}` }} />
          <div style={{
            fontSize: 37, fontWeight: 900, letterSpacing: 4, color: "#EAF6FF",
            textShadow: "0 3px 20px rgba(0,0,0,0.95)",
          }}>{kicker.toUpperCase()}</div>
        </div>
      ) : null}

      {/* 6. NỘI DUNG — viền đen dày + glow accent -> nổi bật trên MỌI nền, kể cả ảnh sáng */}
      {useStat ? (
        <div style={{ position: "absolute", left: 62, right: 300, bottom: 58 }}>
          {/* SỐ LIỆU: to nhất khung, auto-fit theo độ dài để không bao giờ tràn */}
          <div style={{
            fontSize: fitSize([String(stat)], 880, 300), fontWeight: 900, lineHeight: 0.92,
            color: accent2, whiteSpace: "nowrap",
            WebkitTextStroke: "11px #05060c", paintOrder: "stroke fill",
            textShadow: `0 0 60px ${accent2}CC, 0 10px 34px rgba(0,0,0,0.95)`,
          } as React.CSSProperties}>{stat}</div>
          {statLabel ? (
            <div style={{
              // auto-fit như hook: nhãn dài ("IN UNPAID MEDICAL BILLS EVERY SINGLE YEAR") từng sát mép
              // 850 (không phải 918) vì letterSpacing 2px/ký tự còn cộng thêm bề rộng
              marginTop: 6, fontSize: fitSize([String(statLabel)], 850, 46), fontWeight: 800,
              letterSpacing: 2, color: "#EAF6FF",
              whiteSpace: "nowrap", WebkitTextStroke: "6px #05060c", paintOrder: "stroke fill",
              textShadow: "0 6px 22px rgba(0,0,0,0.95)",
            } as React.CSSProperties}>{statLabel.toUpperCase()}</div>
          ) : null}
          {hook ? (
            // CÂU HỎI MỞ trên nền accent -> mắt dừng lại, tạo khoảng trống tò mò (không trả lời trong ảnh)
            <div style={{
              marginTop: 18, display: "inline-block", maxWidth: "100%", padding: "10px 26px", borderRadius: 12,
              background: `linear-gradient(90deg, ${accent}, ${accent2})`,
              boxShadow: `0 0 34px ${accent}88`,
            }}>
              <span style={{
                // LUÔN cho xuống dòng (không nowrap): nowrap + maxWidth = chữ LÒI RA NGOÀI nền pill
                // (nền bị cắt ở maxWidth còn chữ vẫn chạy tiếp) — đúng lỗi đã thấy khi test hook dài.
                // Cho wrap thì pill tự cao lên, chữ không bao giờ ra khỏi nền.
                fontSize: hookWrap ? 36 : hookFit, fontWeight: 900, letterSpacing: 1, color: "#05060c",
                whiteSpace: "normal", lineHeight: hookWrap ? 1.15 : 1.05,
                display: "block",
              }}>{hook.toUpperCase()}</span>
            </div>
          ) : null}
        </div>
      ) : (
        <div style={{ position: "absolute", left: 62, right: 300, bottom: 64 }}>
          {lines.map((ln, i) => {
            const last = i === lines.length - 1;
            return (
              <div key={i} style={{
                fontSize: fs, fontWeight: 900, lineHeight: 1.0, whiteSpace: "nowrap",
                color: last ? accent2 : "#FFFFFF",
                WebkitTextStroke: "9px #05060c", paintOrder: "stroke fill",
                textShadow: last
                  ? `0 0 42px ${accent2}AA, 0 8px 30px rgba(0,0,0,0.95)`
                  : "0 8px 30px rgba(0,0,0,0.95)",
              } as React.CSSProperties}>{ln}</div>
            );
          })}
          <div style={{
            marginTop: 20, height: 11, width: 300, borderRadius: 6,
            background: `linear-gradient(90deg, ${accent}, ${accent2})`, boxShadow: `0 0 30px ${accent}`,
          }} />
        </div>
      )}
    </AbsoluteFill>
  );
};
