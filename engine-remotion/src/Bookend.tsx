import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

// THẺ MỞ ĐẦU + THẺ KẾT DÙNG CHUNG CHO SHORT (24/8/2026 tối — anh: "mở đầu videos và kết thúc chưa
// hook, tẻ nhạt, hay khung đen").
//
// Đo trước khi sửa: trong `introSec` giây đầu, 7 component short chỉ hiện MỘT chip tiêu đề nhỏ trên
// nền gradient — nội dung thật (gauge/bản đồ/bậc thang) mãi tới hết intro mới bắt đầu. Còn
// `outroSec` giây cuối thì các Sequence đã hết, màn hình đứng ở khung cuối cùng. Không đen kịt,
// nhưng là hai quãng chết đúng vào hai chỗ quyết định giữ chân người xem: 1 giây đầu và nút "theo dõi".
//
// Cách làm: một lớp phủ TỰ BIẾT MÌNH Ở ĐÂU (đọc `durationInFrames`), nên mỗi component chỉ thêm một
// dòng — không phải tính lại mốc, tức không đẻ ra lỗi lệch mốc như đã dính ở PULSE.
// Màu lấy từ `accent` của chính kênh đó nên mỗi kênh vẫn giữ nhận diện riêng, không bị đồng phục.

export const Bookend: React.FC<{
  title?: string; handle?: string; accent?: string; color?: string;
  introSec?: number; outroSec?: number; cta?: string;
}> = ({ title = "", handle = "", accent = "#F5B301", color, introSec = 0, outroSec = 0,
        cta = "FOLLOW FOR MORE" }) => {
  const f = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const c2 = color || accent;
  const iF = Math.round((introSec || 0) * fps);
  const oF = Math.round((outroSec || 0) * fps);

  // ── THẺ MỞ ĐẦU ────────────────────────────────────────────────────────────────────────────
  if (iF > 6 && f < iF) {
    const p = spring({ frame: f, fps, config: { damping: 13, stiffness: 150 } });
    const ra = interpolate(f, [iF - 7, iF], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    // vệt sáng quét ngang — chuyển động ngay từ khung hình đầu, không để màn hình đứng yên
    const quet = interpolate(f, [0, iF], [-40, 140], { extrapolateRight: "clamp" });
    return (
      <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center",
                    justifyContent: "center", padding: "0 70px", zIndex: 40, opacity: ra,
                    background: `radial-gradient(90% 60% at 50% 45%, ${accent}22 0%, rgba(0,0,0,0.82) 60%, rgba(0,0,0,0.94) 100%)` }}>
        <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
          <div style={{ position: "absolute", top: 0, bottom: 0, left: `${quet}%`, width: "26%",
                        background: `linear-gradient(100deg, transparent, ${accent}30, transparent)` }} />
        </div>
        <div style={{ textAlign: "center", transform: `scale(${0.86 + 0.14 * p})` }}>
          <div style={{ display: "inline-block", background: c2, color: "#080a12", fontWeight: 900,
                        fontSize: 30, letterSpacing: 3, padding: "9px 26px", borderRadius: 999,
                        marginBottom: 34 }}>
            {handle || "MM0"}
          </div>
          <div style={{ fontSize: 88, lineHeight: 1.06, fontWeight: 900, color: "#FFFFFF",
                        textShadow: `0 6px 40px rgba(0,0,0,.95), 0 0 46px ${accent}55`,
                        letterSpacing: -1.5 }}>
            {title}
          </div>
          <div style={{ margin: "36px auto 0", width: interpolate(p, [0, 1], [40, 260]),
                        height: 9, borderRadius: 999, background: accent }} />
        </div>
      </div>
    );
  }

  // ── THẺ KẾT ───────────────────────────────────────────────────────────────────────────────
  const batDau = durationInFrames - oF;
  if (oF > 6 && f >= batDau) {
    const l = f - batDau;
    const p = spring({ frame: l, fps, config: { damping: 14, stiffness: 130 } });
    const nhip = 1 + 0.045 * Math.sin(l / 4.5);          // nút "theo dõi" đập nhẹ, kéo mắt xuống
    return (
      <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center",
                    justifyContent: "center", zIndex: 40, opacity: Math.min(1, l / 5),
                    background: `radial-gradient(85% 55% at 50% 45%, ${accent}26 0%, rgba(0,0,0,0.86) 62%, rgba(0,0,0,0.96) 100%)` }}>
        <div style={{ textAlign: "center", transform: `scale(${0.9 + 0.1 * p})`, padding: "0 70px" }}>
          <div style={{ fontSize: 54, fontWeight: 900, color: "#FFFFFF", letterSpacing: -0.5,
                        textShadow: "0 6px 30px rgba(0,0,0,.95)" }}>
            {cta}
          </div>
          <div style={{ display: "inline-block", marginTop: 30, background: c2, color: "#080a12",
                        fontWeight: 900, fontSize: 46, letterSpacing: 1.5, padding: "16px 44px",
                        borderRadius: 999, transform: `scale(${nhip})`,
                        boxShadow: `0 0 44px ${accent}66` }}>
            {handle || "MM0"}
          </div>
          {title ? (
            <div style={{ marginTop: 34, fontSize: 30, fontWeight: 700, color: "#C9D6E6",
                          opacity: 0.9 }}>
              {title}
            </div>
          ) : null}
        </div>
      </div>
    );
  }
  return null;
};

export default Bookend;
