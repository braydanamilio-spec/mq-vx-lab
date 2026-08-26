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
//
// ⚠️ MÀN CHE PHẢI MỎNG — suýt tự tạo lại đúng lỗi bị cấm. Bản đầu của thẻ mở đầu phủ
// `rgba(0,0,0,0.82→0.94)`, tức che kín nội dung bên dưới bằng một nền gần đen. Đó CHÍNH LÀ chữ ký
// "chữ trên nền trơn" mà `opening_is_flat()` chặn (đo thật: nền trơn = 91,9% tối · 342 màu; ngưỡng
// chặn dark≥75 & colors<900) — và cũng chính là thứ anh cấm: "mở đầu KHÔNG được là chữ trên nền
// đen". Đặt thẻ hook lên trên rồi bịt hết phần hình thì mở đầu còn tệ hơn lúc chưa có thẻ.
// Nay màn che tối đa `MAN_CHE` = 0.5: gauge/bản đồ/bậc thang bên dưới **vẫn hiện và vẫn đang chạy**,
// chữ vẫn đọc rõ nhờ viền đổ bóng. Vừa hook hơn, vừa không dính chữ ký nền trơn.

// Màn che THẺ MỞ ĐẦU: 0.5 là trần cứng. Cao hơn là dính chữ ký "nền trơn" (dark≥75) mà
// `opening_is_flat()` chặn — xem ghi chú đầu file. Thẻ KẾT thì che dày hơn được: QC chỉ soi khung
// MỞ ĐẦU, và cuối video mục tiêu là đọc được CTA chứ không phải khoe hình.
// 26/8 — HẠ MÀN CHE. Đo 5 video thật: sáng trung bình 25-40/255, khung cuối tụt xuống 15 nên
// trông như video kết bằng màn hình đen. Màn che 0.5 ở mở đầu và 0.78 ở khung kết là hai chỗ
// tối nhất. Hạ xuống: mở đầu còn thấy rõ nội dung đang chạy bên dưới, khung kết KHÔNG tối đi
// mà giữ nguyên hình cuối cùng — anh yêu cầu "kết thúc video không bằng khung đen".
const MAN_CHE = 0.16;   // đo lại: 0.28 -> khung hook 38/255, vẫn tối; 0.16 -> ~58
const MAN_CHE_KET = 0.34;

export const Bookend: React.FC<{
  title?: string; handle?: string; accent?: string; color?: string;
  introSec?: number; outroSec?: number; cta?: string;
  hookStat?: string; hookLabel?: string; hookLine?: string;
}> = ({ title = "", handle = "", accent = "#F5B301", color, introSec = 0, outroSec = 0,
        cta = "", hookStat = "", hookLabel = "", hookLine = "" }) => {
  // 26/8 — BỎ MẶC ĐỊNH "FOLLOW FOR MORE" (anh yêu cầu). Thẻ kêu gọi chiếm trọn khung cuối, che
  // mất chính nội dung vừa kể, và là thứ ai cũng làm — không giúp kênh khác biệt. Khung kết nay
  // giữ nguyên nội dung cuối cùng của video. Kênh nào muốn thì truyền `cta` tường minh.
  const f = useCurrentFrame();
  const { fps, durationInFrames, width: _W, height: _H } = useVideoConfig();
  // 26/8 — thẻ mở đầu/kết thúc đo theo khung DỌC cao 1920. Trên long 16:9 (cao 1080) thì số dẫn
  // 210px + nhãn 40 + dòng hook 34 + tiêu đề chồng lên nhau cao hơn cả khung ⇒ tràn, đúng thứ anh
  // dặn "tránh tràn che khuất chữ". Khổ ngang co chữ lại và nới lề ngang (thừa bề ngang, thiếu
  // bề cao — ngược hẳn khổ dọc).
  const _ngang = _W > _H;
  const co = (n: number) => (_ngang ? Math.round(n * 0.66) : n);
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
                    justifyContent: "center", padding: _ngang ? "0 150px" : "0 70px", zIndex: 40, opacity: ra,
                    background: `radial-gradient(95% 65% at 50% 45%, ${accent}1f 0%, rgba(0,0,0,${MAN_CHE * 0.62}) 55%, rgba(0,0,0,${MAN_CHE}) 100%)` }}>
        <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
          <div style={{ position: "absolute", top: 0, bottom: 0, left: `${quet}%`, width: "26%",
                        background: `linear-gradient(100deg, transparent, ${accent}30, transparent)` }} />
        </div>
        {hookStat ? (
          // ── HOOK 0-3 GIÂY ───────────────────────────────────────────────────────────────
          // 26/8 — bản cũ đưa @handle lên TRƯỚC TIÊN rồi mới tới tiêu đề. Giây 0 không ai quan
          // tâm handle; thứ giữ được người xem là MỘT CON SỐ khó tin + MỘT CÂU HỎI chưa trả lời.
          // Ba nhịp trong 3 giây: số đập vào (0-0,4s) -> nhãn của số (0,4s) -> câu hỏi (0,9s).
          // Tiêu đề lùi xuống nhỏ, handle bỏ hẳn khỏi mở đầu — nó đã nằm sẵn ở đáy mọi khung.
          <div style={{ textAlign: "center", width: "100%" }}>
            <div style={{
              fontSize: co(Math.max(96, Math.min(210, Math.round(1180 / Math.max(3, hookStat.length))))),
              lineHeight: 0.94, fontWeight: 900, color: c2, whiteSpace: "nowrap",
              letterSpacing: -2, transform: `scale(${0.55 + 0.45 * p})`,
              textShadow: `0 0 60px ${accent}88, 0 10px 40px rgba(0,0,0,.95)`,
            }}>{hookStat}</div>
            {hookLabel ? (
              <div style={{
                marginTop: 14, fontSize: co(40), fontWeight: 800, letterSpacing: 2, color: "#EAF6FF",
                opacity: interpolate(f, [Math.round(fps * 0.35), Math.round(fps * 0.7)], [0, 1],
                                     { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
                textShadow: "0 4px 20px rgba(0,0,0,.95)",
              }}>{hookLabel.toUpperCase()}</div>
            ) : null}
            {hookLine ? (
              <div style={{
                marginTop: co(34), display: "inline-block", padding: "12px 30px", borderRadius: 14,
                background: `linear-gradient(90deg, ${accent}, ${c2})`, color: "#080a12",
                fontWeight: 900, fontSize: co(38), letterSpacing: 0.5,
                opacity: interpolate(f, [Math.round(fps * 0.85), Math.round(fps * 1.25)], [0, 1],
                                     { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
                transform: `translateY(${interpolate(f, [Math.round(fps * 0.85), Math.round(fps * 1.25)], [18, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}px)`,
              }}>{hookLine.toUpperCase()}</div>
            ) : null}
            <div style={{
              marginTop: co(30), fontSize: co(34), fontWeight: 700, color: "#ffffffb0", padding: "0 40px",
              opacity: interpolate(f, [Math.round(fps * 1.3), Math.round(fps * 1.7)], [0, 1],
                                   { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
            }}>{title}</div>
          </div>
        ) : (
        <div style={{ textAlign: "center", transform: `scale(${0.86 + 0.14 * p})` }}>
          <div style={{ display: "inline-block", background: c2, color: "#080a12", fontWeight: 900,
                        fontSize: co(30), letterSpacing: 3, padding: "9px 26px", borderRadius: 999,
                        marginBottom: co(34) }}>
            {handle || "MM0"}
          </div>
          <div style={{ fontSize: co(88), lineHeight: 1.06, fontWeight: 900, color: "#FFFFFF",
                        textShadow: `0 6px 40px rgba(0,0,0,.95), 0 0 46px ${accent}55`,
                        letterSpacing: -1.5 }}>
            {title}
          </div>
          <div style={{ margin: "36px auto 0", width: interpolate(p, [0, 1], [40, 260]),
                        height: 9, borderRadius: 999, background: accent }} />
        </div>
        )}
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
                    background: `radial-gradient(85% 55% at 50% 45%, ${accent}26 0%, rgba(0,0,0,${MAN_CHE_KET * 0.85}) 62%, rgba(0,0,0,${MAN_CHE_KET}) 100%)` }}>
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
