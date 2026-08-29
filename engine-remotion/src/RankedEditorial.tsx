import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { Karaoke } from "./Karaoke";
import { Bookend } from "./Bookend";
import { phong } from "./Phong";
import { SoChay, SO_DEU, DongNguon } from "./So";
import { nenDayDu } from "./Nen";
import React from "react";
import type { RankedProps } from "./RankedShort";

/**
 * RANKED — BẢN BIÊN TẬP (29/8/2026).
 *
 * VÌ SAO VIẾT BỐ CỤC THỨ HAI CHO CÙNG MỘT DẠNG
 * --------------------------------------------
 * Anh xem ba kênh `ranked` render cạnh nhau và nói thẳng: "vẫn còn rẻ tiền, channel nào cũng làm
 * được". Đúng. Mười tám kênh dùng chung một bảng tier S/A/B/C thẻ màu; `bien_cua` có 27 biến thể
 * nhưng chúng chỉ đổi vị trí nhãn, kiểu viền, hoạ tiết nền — bộ khung thì một. Ba kênh đặt cạnh
 * nhau đọc ra là một kênh đổi filter. Đó vừa là chuyện thẩm mỹ, vừa là rủi ro lớn nhất còn lại
 * với chính sách "nội dung sản xuất hàng loạt" của YouTube.
 *
 * Và bảng tier thẻ màu là thứ AI CŨNG LÀM ĐƯỢC bằng một template có sẵn. Thứ không sao chép được
 * của hệ này là DỮ LIỆU — hồ sơ công, API sống, số tra lại được. Nên bố cục phải để con số làm
 * nhân vật chính, không phải trang trí quanh nó.
 *
 * BA QUYẾT ĐỊNH, MỖI CÁI ĐỔI LẤY MỘT THỨ
 * --------------------------------------
 * ① MỘT MỤC MỘT MÀN HÌNH, không phải sáu dòng cùng lúc.
 *    Mất: người xem không thấy toàn bảng ngay.
 *    Được: con số được phóng tới cỡ không thể lướt qua, và mỗi lần đổi mục là một nhịp mới —
 *    thứ giữ chân trên feed dọc. Bảng đầy đủ vẫn dựng dần ở đáy, nên cuối video vẫn có toàn cảnh.
 *
 * ② SỐ THỨ HẠNG KHỔNG LỒ LÀM NỀN, chìm dưới nội dung.
 *    Đây là chữ ký của trang biểu đồ báo in: nó cho biết đang ở đâu trong danh sách mà không tốn
 *    thêm một dòng chữ nào, và nó là thứ nhận ra ngay cả khi xem không tiếng.
 *
 * ③ BẢNG MÀU CHỈ HAI TÔNG: nền tối của kênh + accent. Không thẻ màu, không viền phát sáng.
 *    Mất: khung "vui mắt" kiểu thumbnail game.
 *    Được: chữ và số nổi hẳn lên, và nó trông như đồ hoạ của một toà soạn chứ không như một
 *    template. Tương phản cũng lên theo — xem ghi chú tương phản trong `Nen.tsx`.
 */

const FPS = 30;
const idur = (it: any, s: number) => (it?.dur && it.dur > 0 ? it.dur : s);

export const calcRankedEditorial = ({ props }: any) => {
  const its = props?.items || [];
  const isec = props?.introSec ?? 1.8, isc = props?.itemSec ?? 2.2, tail = props?.outroSec ?? 1.6;
  const tong = its.reduce((a: number, it: any) => a + idur(it, isc), 0);
  return { durationInFrames: Math.round((isec + tong + tail) * FPS), fps: FPS };
};

export const RankedEditorial: React.FC<RankedProps> = (props) => {
  const {
    font = "", hookStat = "", hookLabel = "", hookLine = "", bg = "", bg2 = "",
    title = "RANKED", subtitle = "", source = "", handle = "@mm0",
    color = "#7C5CFF", accent = "#7C5CFF", items = [],
    introSec = 1.8, itemSec = 2.2, outroSec = 1.6, audio, music, subs = [],
  } = props;
  const f = useCurrentFrame();
  const { fps, width: W, height: H } = useVideoConfig();

  const introF = Math.round(introSec * fps);
  const starts: number[] = [];
  let acc = introF;
  for (const it of items) { starts.push(acc); acc += Math.round(idur(it, itemSec) * fps); }

  // Mục ĐANG nói: mục cuối cùng đã tới lượt. Trước intro thì chưa có mục nào.
  let idx = -1;
  for (let i = 0; i < items.length; i++) if (f >= starts[i]) idx = i;
  const cur = idx >= 0 ? items[idx] : null;
  const batDau = idx >= 0 ? starts[idx] : 0;
  const p = spring({ frame: f - batDau, fps, config: { damping: 15, stiffness: 120 } });

  // Băng chữ karaoke chiếm đáy; danh sách tích luỹ phải nhường chỗ, không thì chữ đè chữ —
  // đúng lỗi đã vá cho ba dạng khác.
  // Danh sách tích luỹ kéo lên sát khối chính: bản đầu neo quá thấp và để hở nguyên một
  // phần ba khung ở giữa — khung trống thì bố cục dù sạch vẫn đọc ra là "chưa xong".
  const dayDS = (subs && subs.length) ? 400 : 220;

  return (
    <AbsoluteFill style={{ background: nenDayDu(bg || accent, bg2 || color), fontFamily: phong(font) }}>
      {/* SỐ THỨ HẠNG KHỔNG LỒ — nằm dưới mọi thứ, cắt bớt ở mép trái cho có sức nặng của trang in */}
      {cur ? (
        <div style={{
          position: "absolute", left: -40, top: H * 0.13,
          fontSize: 620, lineHeight: 0.78, fontWeight: 900,
          color: `${accent}1c`, letterSpacing: -34, ...SO_DEU,
          transform: `translateY(${(1 - p) * 26}px)`,
        }}>{String(idx + 1).padStart(2, "0")}</div>
      ) : null}

      {/* NHÃN MỤC — nhỏ, giãn chữ, in hoa: đây là dòng "chuyên mục" của trang biên tập */}
      <div style={{
        position: "absolute", top: 92, left: 64, right: 64,
        display: f < introF ? "none" : "block",
      }}>
        <div style={{
          color: accent, fontWeight: 800, fontSize: 26, letterSpacing: 6,
          textTransform: "uppercase" as const, marginBottom: 14,
        }}>{subtitle || "ranked"}</div>
        <div style={{
          color: "#fff", fontWeight: 900, fontSize: 56, lineHeight: 1.04,
          textWrap: "balance" as any, textShadow: "0 4px 24px #0009",
        }}>{title}</div>
        <div style={{ height: 3, width: 132, background: accent, marginTop: 22, borderRadius: 2 }} />
      </div>

      {/* MỤC ĐANG NÓI — tên rồi tới số, số là thứ to nhất khung hình */}
      {cur ? (
        <div style={{
          position: "absolute", left: 64, right: 64, top: H * 0.345,
          opacity: Math.min(1, p * 1.4),
          transform: `translateY(${(1 - p) * 34}px)`,
        }}>
          <div style={{
            color: "#ffffffde", fontWeight: 800, fontSize: 46, lineHeight: 1.1,
            letterSpacing: -0.5, marginBottom: 10,
          }}>{cur.name}</div>
          <div style={{
            color: "#fff", fontWeight: 900, letterSpacing: -6, lineHeight: 0.94,
            // Cỡ suy TỪ ĐỘ DÀI chuỗi, không đặt sẵn: `stat` do nguồn quyết ("1.0M" hay
            // "$2,631M" hay "157,693.8"), và một cỡ cứng thì chuỗi dài sẽ tràn ra ngoài mép.
            fontSize: Math.max(88, Math.min(210, Math.round(1420 / Math.max(3, String(cur.stat || "").length)))),
            textShadow: `0 0 70px ${accent}55, 0 8px 30px #000a`, ...SO_DEU,
          }}>
            <SoChay s={String(cur.stat || "")} tuFrame={batDau} giay={0.9} />
          </div>

          {/* THANH TỈ LỆ — mục này so với mục lớn nhất bảng.
              Đây là chỗ bố cục cũ dùng một cái THẺ MÀU; thẻ màu chỉ tô nền cho con số chứ không
              nói thêm điều gì. Một vạch dài đúng tỉ lệ thì NÓI: mục này bằng bao nhiêu phần của
              mục đầu bảng — thứ mắt đọc được trong một phần giây, không cần đọc số.
              Và nó lấp đúng khoảng trống giữa khung mà bản đầu để hở. */}
          {(() => {
            const so = (x: any) => {
              const m = String(x ?? "").match(/[\d][\d,.]*/);
              return m ? parseFloat(m[0].replace(/,/g, "")) : 0;
            };
            const max = Math.max(1, ...items.map((it) => so(it.stat)));
            const ti = Math.max(0.02, Math.min(1, so(cur.stat) / max));
            const chay = interpolate(f - batDau, [0, Math.round(fps * 0.9)], [0, 1],
                                     { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            return (
              <div style={{ marginTop: 34, position: "relative", height: 10 }}>
                <div style={{ position: "absolute", inset: 0, background: "#ffffff14", borderRadius: 5 }} />
                <div style={{
                  position: "absolute", left: 0, top: 0, bottom: 0,
                  width: `${ti * chay * 100}%`, background: accent, borderRadius: 5,
                  boxShadow: `0 0 26px ${accent}77`,
                }} />
              </div>
            );
          })()}
        </div>
      ) : null}

      {/* DANH SÁCH TÍCH LUỸ — các mục ĐÃ qua, xếp mảnh ở đáy: cuối video vẫn có toàn cảnh bảng */}
      <div style={{
        position: "absolute", left: 64, right: 64, bottom: dayDS,
        display: "flex", flexDirection: "column", gap: 9,
      }}>
        {items.slice(0, Math.max(0, idx)).map((it, i) => (
          <div key={i} style={{
            display: "flex", alignItems: "baseline", gap: 16,
            borderTop: "1px solid #ffffff1f", paddingTop: 9, opacity: 0.5,
          }}>
            <div style={{ color: accent, fontWeight: 800, fontSize: 20, minWidth: 34, ...SO_DEU }}>
              {String(i + 1).padStart(2, "0")}
            </div>
            <div style={{ flex: 1, color: "#fff", fontWeight: 700, fontSize: 24,
                          overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {it.name}
            </div>
            <div style={{ color: "#ffffffcc", fontWeight: 800, fontSize: 24, ...SO_DEU }}>{it.stat}</div>
          </div>
        ))}
      </div>

      <DongNguon nguon={source} day={96} />
      <div style={{
        position: "absolute", bottom: 46, left: 0, right: 0, textAlign: "center",
        color: "#ffffff44", fontWeight: 700, fontSize: 22, letterSpacing: 1,
      }}>{handle}</div>

      {subs && subs.length ? <Karaoke subs={subs} accent={accent} /> : null}
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
      <Bookend hookStat={hookStat} hookLabel={hookLabel} hookLine={hookLine} title={title}
               handle={handle} accent={accent} color={color}
               introSec={introSec} outroSec={outroSec} />
    </AbsoluteFill>
  );
};

export default RankedEditorial;
