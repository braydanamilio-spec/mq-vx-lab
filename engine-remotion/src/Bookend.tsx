import React from "react";
import { SoChay } from "./So";
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
      // 28/8 — THẺ HOOK ĐẶT Ở PHẦN TRÊN, KHÔNG ĐẶT GIỮA KHUNG.
      // Anh gửi khung MPG TRUTH: khối "19 mpg / BRONCO 4WD / IS YOUR CAR ON IT?" nằm chình ình
      // GIỮA màn hình, đè lên đúng ba hàng cột đang chạy — người xem mất chính đoạn dữ liệu mà
      // cả video dựng lên để nói, suốt 13 giây đầu (quãng hook dài theo lời đọc).
      // Chủ ý của thẻ hook là "nội dung vẫn chạy bên dưới, không phải chữ trên nền đen" (xem màn
      // che 0,16 ở trên) — nhưng đặt giữa khung thì nó phá đúng cái nó định giữ.
      // Phần trên là chỗ mắt tìm tới trước, và ở mọi dạng thì vùng đó thoáng nhất: bảng, bản đồ
      // và thang đều bắt đầu từ khoảng 1/3 khung trở xuống.
      <div style={{ position: "absolute", inset: 0, display: "flex",
                    alignItems: _ngang ? "center" : "flex-start",
                    justifyContent: "center", padding: _ngang ? "0 150px" : "210px 70px 0", zIndex: 40, opacity: ra,
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
          // 26/8 — HAI LỖI THẤY BẰNG MẮT trên khung thật của FAME CURVE, mà phép đo độ tối cho QUA:
          //  ① SỐ DẪN CÙNG MÀU VỚI NỀN. `color: c2` = `color || accent`, mà `dung_props` gán
          //     `color = palette.primary` VÀ `bg = palette.primary` — nên số dẫn xanh nằm trên nền
          //     xanh cùng hệ, gần như không tách ra. Nay để TRẮNG, giữ quầng sáng màu kênh làm
          //     nhận diện: trắng tương phản với mọi nền tối, không phụ thuộc bảng màu từng kênh.
          //  ② CẤU TRÚC NỀN XUYÊN QUA. Vạch trục thang ("1 in 10", "1 in 1,000") chạy ngang qua
          //     số dẫn và nút câu hỏi. Thêm một tấm nền mờ sau khối hook để cắt nhiễu.
          <div style={{ textAlign: "center", width: "100%", position: "relative",
                        padding: "26px 18px", borderRadius: 26,
                        background: "radial-gradient(70% 60% at 50% 46%, rgba(6,6,14,.72) 0%, rgba(6,6,14,.34) 62%, transparent 100%)" }}>
            <div style={{
              fontSize: co(Math.max(96, Math.min(210, Math.round(1180 / Math.max(3, hookStat.length))))),
              lineHeight: 0.94, fontWeight: 900, color: "#FFFFFF", whiteSpace: "nowrap",
              letterSpacing: -2, transform: `scale(${0.55 + 0.45 * p})`,
              textShadow: `0 0 60px ${accent}88, 0 10px 40px rgba(0,0,0,.95)`,
            }}>
              {/* 27/8 — SỐ DẪN Ở HOOK PHẢI CHẠY LÊN.
                  Đây là con số to nhất, ở giây đầu tiên, và là thứ quyết định người ta lướt qua
                  hay dừng lại. Hiện sẵn giá trị cuối là vứt bỏ đúng cái sức giữ mắt của nó: người
                  xem không rời mắt khi thấy một con số còn đang lớn dần, vì não muốn biết nó dừng
                  ở đâu.
                  Sửa ở `Bookend` là ăn cả SÁU dạng cùng lúc — nó là khối mở đầu dùng chung. */}
              <SoChay s={hookStat} tuFrame={0} giay={1.05} />
            </div>
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
                // 26/8 — CÙNG GỐC VỚI LỖI SỐ DẪN. Nền nút là `linear-gradient(accent, c2)` mà
                // `dung_props` gán `accent` VÀ `color` cùng bằng `palette.primary` ⇒ gradient ra một
                // màu tối, trên đó lại đặt chữ `#080a12` gần đen. Xem khung thật: dòng câu hỏi gần
                // như không đọc được — mà đây là nhịp thứ ba của hook, nhịp giữ người xem ở lại.
                // Nay nền TRẮNG ĐẶC + chữ tối: tương phản không phụ thuộc bảng màu kênh nào cả,
                // và tạo bậc thị giác với số dẫn trắng phía trên (số = trắng trên nền tối, câu hỏi
                // = tối trên nền trắng).
                background: "#F2F6FF", color: "#0A0C16",
                boxShadow: `0 6px 26px rgba(0,0,0,.45), 0 0 0 2px ${accent}66`,
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
          {/* Nhãn @handle thứ hai, ở đầu khối — cùng lý do như trên: dấu kênh đã có sẵn ở đáy
              mọi khung, in thêm một viên thuốc màu đặc ngay trên tiêu đề chỉ đẩy tiêu đề xuống
              và cướp mất sự chú ý của giây đầu. */}
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
  // 28/8 — THẺ KẾT IN LẠI TIÊU ĐỀ, ĐÈ LÊN CHÍNH NỘI DUNG.
  // Xem khung 28,5s của SKY RIGHT NOW: "159 planes are over California right now" hiện Ở GIỮA
  // BẢN ĐỒ, trong khi ĐÚNG CÂU ẤY đang nằm trên đầu khung — header của mọi dạng short in tiêu đề
  // suốt cả video. Nên phần kết cho ra hai bản tiêu đề chồng nhau, bản dưới đè lên California và
  // Arizona đúng lúc người xem đang nhìn hai bang đó.
  // Đây là lỗi 25/8 lặp lại ở đầu kia của video: hồi đó thẻ MỞ ĐẦU chồng tiêu đề, đã vá bằng cách
  // ẩn header trong quãng intro. Quãng outro thì không ai vá, vì không ai soi khung cuối.
  // Và khi `cta` rỗng — mặc định của cả 50 kênh, vì `cta` mặc định đã bị bỏ hôm 26/8 — thì thẻ kết
  // KHÔNG CÒN NỘI DUNG NÀO của riêng nó: chỉ còn một tấm màn tối phủ lên hình cuối cùng cộng một
  // tiêu đề trùng. Không vẽ gì là đúng hơn vẽ cái đó.
  const batDau = durationInFrames - oF;
  if (oF > 6 && f >= batDau && cta) {
    const l = f - batDau;
    const p = spring({ frame: l, fps, config: { damping: 14, stiffness: 130 } });
    return (
      <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center",
                    justifyContent: "center", zIndex: 40, opacity: Math.min(1, l / 5),
                    background: `radial-gradient(85% 55% at 50% 45%, ${accent}26 0%, rgba(0,0,0,${MAN_CHE_KET * 0.85}) 62%, rgba(0,0,0,${MAN_CHE_KET}) 100%)` }}>
        <div style={{ textAlign: "center", transform: `scale(${0.9 + 0.1 * p})`, padding: "0 70px" }}>
          <div style={{ fontSize: co(54), fontWeight: 900, color: "#FFFFFF", letterSpacing: -0.5,
                        textShadow: "0 6px 30px rgba(0,0,0,.95)" }}>
            {cta}
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export default Bookend;
