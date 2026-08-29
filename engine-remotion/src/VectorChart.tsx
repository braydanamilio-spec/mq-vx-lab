import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { Karaoke } from "./Karaoke";
import { phong } from "./Phong";
import { SoChay, SO_DEU } from "./So";
import React from "react";
import type { RankedProps } from "./RankedShort";

/**
 * ĐỒ HOẠ VECTOR ĐỘNG (29/8/2026) — bố cục thứ ba cho dạng `ranked`, và là hướng anh chọn.
 *
 * VÌ SAO
 * ------
 * Anh xem ba kênh `ranked` cạnh nhau: "vẫn còn rẻ tiền, channel nào cũng làm được". Rồi anh gửi
 * ảnh mẫu — đồ hoạ vector phẳng kiểu Vox/Kurzgesagt: nền giấy kem, khối màu phẳng, viền dày, một
 * màu nhấn, chữ đậm cỡ lớn, hình TỰ VẼ RA theo thời gian.
 *
 * Và hướng đó không chỉ đẹp hơn, nó còn ĐÁNG TIN CẬY HƠN VỀ KỸ THUẬT so với ảnh AI:
 *   • không cần key, không hạn mức, không 429 — vẽ bằng mã, luôn ra;
 *   • không bịa chữ ("Publlic Records"), vì mọi ký tự trên khung đều do mình đặt;
 *   • không lệch gu giữa các lượt — cùng một kênh thì lượt nào cũng đúng một ngôn ngữ hình;
 *   • nhẹ hơn nhiều lần: không tải ảnh, không chờ máy vẽ.
 * Ảnh AI vẫn giữ cho dạng phim kể, nơi cần không khí. Còn dạng số liệu thì vector đúng hơn hẳn.
 *
 * NGÔN NGỮ HÌNH (đọc từ ảnh mẫu anh gửi, không tự bịa)
 * ---------------------------------------------------
 *   nền     giấy kem ấm + kẻ dòng rất mờ, hoặc xanh rất nhạt + lưới ô
 *   viền     DÀY (10-14px) màu gần đen — đây là thứ làm nó ra "đồ hoạ" chứ không ra "biểu đồ Excel"
 *   khối     màu phẳng, bão hoà, KHÔNG gradient, KHÔNG đổ bóng mềm
 *   chữ      grotesque rất đậm, gần đen, cỡ lớn; số là nhân vật chính
 *   chuyển   hình MỌC LÊN / VẼ RA, không phải hiện ra rồi đứng im
 */

const FPS = 30;
const idur = (it: any, s: number) => (it?.dur && it.dur > 0 ? it.dur : s);

// Bảng màu phẳng — lấy đúng tinh thần ảnh mẫu: một nền giấy, mực gần đen, vài màu nhấn bão hoà.
const MUC = "#171410";
const GIAY = ["#FAF0DC", "#F6EAD2"];
const NHAN_MAU = ["#E8632A", "#F2A626", "#1F9D6B", "#2E7FA8", "#B8452F", "#7A5AA8"];

export const calcVectorChart = ({ props }: any) => {
  const its = props?.items || [];
  const isec = props?.introSec ?? 1.8, isc = props?.itemSec ?? 2.2, tail = props?.outroSec ?? 1.6;
  const tong = its.reduce((a: number, it: any) => a + idur(it, isc), 0);
  return { durationInFrames: Math.round((isec + tong + tail) * FPS), fps: FPS };
};

/** Đọc con số THẬT từ chuỗi hiển thị, GIỮ NGUYÊN ĐỘ LỚN.
 *
 * 29/8 — khung thật: "1.0M" (Counter-Strike) ra cột NGẮN NHẤT bảng, còn "314.7K" ra cột dài nhất.
 * Vì bản đầu chỉ bắt phần chữ số và bỏ hậu tố: 1.0M đọc thành 1.0, 314.7K đọc thành 314.7 — nên
 * biểu đồ vẽ ngược hẳn thứ hạng. Một biểu đồ vẽ sai thứ hạng thì tệ hơn không có biểu đồ: nó nói
 * dối một cách tự tin.
 * Cùng họ lỗi với `_dinh_don_vi` (525 + "K reads" phải ra "525K", không phải "525"). */
const _so = (x: any) => {
  const t = String(x ?? "");
  const m = t.match(/[\d][\d,.]*/);
  if (!m) return 0;
  const v = parseFloat(m[0].replace(/,/g, "")) || 0;
  const sau = t.slice(t.indexOf(m[0]) + m[0].length).trim().toUpperCase();
  if (sau.startsWith("K")) return v * 1e3;
  if (sau.startsWith("M")) return v * 1e6;
  if (sau.startsWith("B")) return v * 1e9;
  if (sau.startsWith("T")) return v * 1e12;
  return v;
};

export const VectorChart: React.FC<RankedProps> = (props) => {
  const {
    font = "", title = "RANKED", subtitle = "", source = "", handle = "@mm0",
    accent = "#E8632A", items = [],
    introSec = 1.8, itemSec = 2.2, audio, music, subs = [],
  } = props;
  const f = useCurrentFrame();
  const { fps, width: W, height: H } = useVideoConfig();

  const introF = Math.round(introSec * fps);
  const starts: number[] = [];
  let acc = introF;
  for (const it of items) { starts.push(acc); acc += Math.round(idur(it, itemSec) * fps); }

  let idx = -1;
  for (let i = 0; i < items.length; i++) if (f >= starts[i]) idx = i;

  const max = Math.max(1, ...items.map((it) => _so(it.stat)));
  const dayKhung = (subs && subs.length) ? 430 : 250;   // chừa chỗ băng phụ đề, không để chữ đè chữ
  const topKhung = 330;
  const caoKhung = H - topKhung - dayKhung;

  // Cột nằm NGANG, mọc từ trái sang: khổ dọc 9:16 thì chiều ngang là chiều dư dả nhất, và mắt
  // người so độ dài ngang chính xác hơn so độ cao (đây là lý do biểu đồ báo hay dùng cột ngang).
  const nCot = Math.max(1, items.length);
  // Cột chiếm HẾT chiều cao dùng được, không ghim trần 96px: bản đầu để trần cứng nên
  // bảng 4-6 mục chỉ lấp một phần ba khung, hai phần ba dưới bỏ trắng.
  const khe = 22;
  const caoCot = Math.max(64, Math.floor((caoKhung - (nCot - 1) * khe) / nCot));
  // Cột nhãn rộng theo TÊN DÀI NHẤT, không ghim cứng: bản đầu để 250px và "Grand Theft Auto V
  // Legacy" vỡ thành bốn dòng chữ li ti trong một ô hẹp — đọc không ra, mà lại chiếm chỗ.
  // Trần 380px để cột số liệu không bị bóp; dài hơn nữa thì cắt bằng dấu ba chấm, vì một cái tên
  // dài quá KHÔNG đáng để nuốt mất phần biểu đồ.
  const tenDai = Math.max(6, ...items.map((it) => String(it.name || "").length));
  const traiCot = Math.max(230, Math.min(380, 118 + tenDai * 9));
  const rongToiDa = W - traiCot - 210;   // chừa sẵn chỗ cho con số đứng sau đầu cột

  return (
    <AbsoluteFill style={{
      background: `linear-gradient(160deg, ${GIAY[0]} 0%, ${GIAY[1]} 100%)`,
      fontFamily: phong(font),
    }}>
      {/* KẺ DÒNG rất mờ — cho nền có chất giấy, không phải một mảng màu trơn */}
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {Array.from({ length: Math.ceil(H / 54) }, (_, i) => (
          <line key={i} x1={0} x2={W} y1={i * 54} y2={i * 54} stroke={MUC} strokeOpacity={0.055} strokeWidth={2} />
        ))}
        <line x1={104} x2={104} y1={0} y2={H} stroke="#D6483A" strokeOpacity={0.22} strokeWidth={3} />
      </svg>

      {/* TIÊU ĐỀ — chữ gần đen trên giấy, đây là bố cục DUY NHẤT trong hệ không dùng chữ trắng */}
      <div style={{ position: "absolute", top: 96, left: 104, right: 64 }}>
        <div style={{ color: accent, fontWeight: 900, fontSize: 24, letterSpacing: 5,
                      textTransform: "uppercase" as const, marginBottom: 12 }}>
          {subtitle || "the numbers"}
        </div>
        <div style={{ color: MUC, fontWeight: 900, fontSize: 58, lineHeight: 1.02,
                      letterSpacing: -1, textWrap: "balance" as any }}>{title}</div>
      </div>

      {/* CỘT NGANG — mỗi cột là một khối phẳng có VIỀN DÀY, mọc ra theo lượt của nó */}
      {items.map((it, i) => {
        if (f < starts[i]) return null;
        const p = spring({ frame: f - starts[i], fps, config: { damping: 16, stiffness: 110 } });
        const ti = Math.max(0.03, _so(it.stat) / max);
        const rong = rongToiDa * ti * p;
        const y = topKhung + i * (caoCot + khe);
        const mau = NHAN_MAU[i % NHAN_MAU.length];
        const dang = i === idx;
        return (
          <div key={i}>
            {/* TÊN MỤC — canh phải, sát mép cột: mắt đọc tên rồi trượt thẳng vào cột */}
            <div style={{
              position: "absolute", left: 104, top: y, width: traiCot - 124, height: caoCot,
              display: "flex", alignItems: "center", justifyContent: "flex-end",
              color: MUC, fontWeight: 800, fontSize: dang ? 27 : 24, textAlign: "right",
              lineHeight: 1.14, opacity: dang ? 1 : 0.62, paddingRight: 4,
              // Tối đa hai dòng rồi cắt: ba dòng trở lên là chữ nhỏ tới mức không đọc được trên
              // điện thoại, mà tên mục vốn chỉ cần đủ nhận ra.
              display: "-webkit-box" as any, WebkitLineClamp: 2 as any,
              WebkitBoxOrient: "vertical" as any, overflow: "hidden",
            }}>{it.name}</div>

            {/* KHỐI CỘT — viền dày là thứ làm nó ra "đồ hoạ" chứ không ra "biểu đồ bảng tính" */}
            <div style={{
              position: "absolute", left: traiCot, top: y, height: caoCot, width: Math.max(10, rong),
              background: mau, border: `7px solid ${MUC}`, borderRadius: 4,
              boxSizing: "border-box" as const,
            }} />

            {/* SỐ — đứng ngay sau đầu cột, cỡ lớn hẳn cho mục đang nói */}
            {/* Số đặt NGOÀI đầu cột; cột dài quá thì lùi vào TRONG cột — bản đầu để cố định bên
                ngoài và con số bị mép phải khung cắt mất ("314." thay vì "314.7K"). */}
            <div style={{
              position: "absolute",
              // Bề rộng con số ước TỪ ĐỘ DÀI CHUỖI, không dùng hằng số: bản đầu để 150/110px và
              // "157,693.8" (9 ký tự, cỡ 46) chiếm ~250px nên vẫn bị mép phải cắt cụt. Một hằng
              // số đo cho chuỗi ngắn thì âm thầm sai với mọi chuỗi dài hơn — cùng cái bẫy đã gặp
              // ở cỡ chữ thẻ tiêu đề cinematic.
              left: (() => {
                const co = dang ? 46 : 30;
                const rongSo = String(it.stat || "").length * co * 0.58 + 24;
                const ngoai = traiCot + Math.max(10, rong) + 18;
                return (ngoai + rongSo > W - 40)
                  ? Math.max(traiCot + 14, traiCot + Math.max(10, rong) - rongSo)
                  : ngoai;
              })(),
              top: y, height: caoCot, display: "flex", alignItems: "center",
              color: MUC, fontWeight: 900, fontSize: dang ? 46 : 30, ...SO_DEU,
              opacity: Math.min(1, p * 1.6),
            }}>
              {dang ? <SoChay s={String(it.stat || "")} tuFrame={starts[i]} giay={0.8} /> : String(it.stat || "")}
            </div>
          </div>
        );
      })}

      {/* NGUỒN + TÊN KÊNH — mực nhạt trên giấy, cùng hệ với phần còn lại */}
      <div style={{ position: "absolute", bottom: 96, left: 104, right: 64,
                    display: "flex", justifyContent: "space-between",
                    color: MUC, opacity: 0.44, fontWeight: 700, fontSize: 21 }}>
        <span>{source ? `Source: ${source}` : ""}</span>
        <span>{handle}</span>
      </div>

      {/* Băng phụ đề: NỀN CỦA NÓ TỐI, dù nền trang là giấy sáng.
          Bản trước tôi đưa màu MỰC (gần đen) vào đây để hợp tông giấy — và chữ đang đọc thành đen
          trên đen, mất hẳn. Sửa một chỗ chói bằng cách tạo một chỗ tàng hình thì không phải sửa.
          Màu vàng hổ phách thuộc đúng bảng giấy này mà vẫn nổi trên nền tối của băng chữ. */}
      {subs && subs.length ? <Karaoke subs={subs} accent="#F2A626" /> : null}
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
    </AbsoluteFill>
  );
};

export default VectorChart;
