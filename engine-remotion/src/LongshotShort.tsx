import { AbsoluteFill, Sequence, Audio, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { Karaoke } from "./Karaoke";
import { Bookend } from "./Bookend";
import { phong } from "./Phong";
import { SoChay, SO_DEU, DongNguon } from "./So";
import { bienCua, hoaTietNen } from "./Bien";
import { nenDayDu } from "./Nen";
import { ChuyenCanh } from "./Chuyen";
import React from "react";

// KÊNH #6 LONGSHOT — real odds/probability, items HOP UP a vertical log-scale ladder to their real rung.
// Camera scrolls/zooms up as rarity increases; final item = big dramatic push-in reveal. Motif: vertical ladder, unique so far.
type Word = { t: number; d: number; w: string };
export type LongshotItem = { label: string; emoji?: string; oddsDisp: string; logValue: number; vo?: string; dur?: number };
export type LongshotProps = {
  title?: string; handle?: string; source?: string; color?: string; accent?: string;
  items: LongshotItem[]; introSec?: number; itemSec?: number; outroSec?: number;
  hookStat?: string; hookLabel?: string; hookLine?: string;
  bg?: string; bg2?: string;
  font?: string;
  audio?: string; music?: string; rungKieu?: string; rungDonVi?: string; subs?: Word[]; sfx?: boolean;
};

const FPS = 30;
const idur = (it: LongshotItem, s: number) => (it.dur && it.dur > 0 ? it.dur : s);

export const calcLongshot = ({ props }: any) => {
  const its: LongshotItem[] = props.items || [];
  const isec = props.introSec ?? 1.8, isc = props.itemSec ?? 2.7, tail = props.outroSec ?? 2.4;
  const total = its.reduce((a, it) => a + idur(it, isc), 0);
  return { durationInFrames: Math.round((isec + total + tail) * FPS), fps: FPS };
};

// ---- ladder geometry (log scale: 1 log10 unit == RUNG_GAP px, so rarity gaps grow "further apart" up the tower) ----
const RUNG_GAP = 232;
// 26/8 — chừa chỗ cho băng phụ đề. Karaoke neo `bottom 200` và cao ~2 dòng (mép trên ~1608);
// nấc thấp nhất của thang cùng nhãn của nó rơi đúng vào dải đó ⇒ chữ đè chữ.
// Có sub thì đẩy đáy thang lên, thang ngắn lại một chút nhưng không ai phải đọc chữ chồng chữ.
const BOTTOM_PAD_GOC = 470;
const TOP_PAD = 520;
const ANCHOR_Y = 1920 * 0.66;
const RAIL_L = 1080 / 2 - 96, RAIL_R = 1080 / 2 + 96, CENTER = 1080 / 2;

// 28/8 — NHÃN THANG PHẢI NÓI ĐÚNG LOẠI DỮ LIỆU ĐANG VẼ.
// Ảnh thật kênh FAME CURVE: cột ghi "1 in 10,000" ngay cạnh con số "63.4K" — mà đây là LƯỢT ĐỌC
// Wikipedia, không phải xác suất. Khuôn này vốn là thang xác suất ("1 phần triệu"); đổ dữ liệu
// ĐẾM vào thì mọi nhãn thang đều vô nghĩa, và người xem không có cách nào hiểu.
// Nguồn nào đếm thì khai `rungKieu:"dem"` + đơn vị; thang tự đổi cách ghi. Nguồn xác suất không
// khai gì -> giữ nguyên "1 in N" như cũ, 2 kênh longshot kia không đổi một pixel.
const _gonSo = (v: number) => v >= 1e9 ? Math.round(v / 1e9) + "B"
  : v >= 1e6 ? Math.round(v / 1e6) + "M"
  : v >= 1e3 ? Math.round(v / 1e3) + "K" : String(Math.round(v));

const fmtRung = (n: number, kieu = "odds", donVi = "") => {
  const v = Math.pow(10, n);
  if (kieu === "dem") return _gonSo(v) + (donVi ? " " + donVi : "");
  if (v < 1e6) return "1 in " + v.toLocaleString();
  if (v < 1e9) return "1 in " + Math.round(v / 1e6) + "M";
  return "1 in " + Math.round(v / 1e9) + "B";
};

// bouncy multi-hop climb: splits the climb into N discrete rung-hops (anticipation + landing bounce each hop)
const climbPos = (f: number, climbStart: number, climbDur: number, hops: number, fromY: number, toY: number, fps: number) => {
  const local = f - climbStart;
  if (local <= 0) return { y: fromY, hopT: 0, arc: 0, done: false, justLanded: false };
  if (local >= climbDur) return { y: toY, hopT: 1, arc: 0, done: true, justLanded: local < climbDur + 3 };
  const perHop = climbDur / hops;
  const hopIdx = Math.min(hops - 1, Math.floor(local / perHop));
  const hopLocal = local - hopIdx * perHop;
  const hopFromY = fromY + (hopIdx / hops) * (toY - fromY);
  const hopToY = fromY + ((hopIdx + 1) / hops) * (toY - fromY);
  const sp = spring({ frame: hopLocal, fps, config: { damping: 11, stiffness: 210, mass: 0.55 } });
  const y = interpolate(sp, [0, 1], [hopFromY, hopToY], { extrapolateRight: "clamp" });
  const arc = Math.sin(Math.min(1, hopLocal / Math.max(1, perHop)) * Math.PI) * 16; // small horizontal hop-arc
  return { y, hopT: sp, arc, done: false, justLanded: false, hopLocal, perHop };
};

// `pad` truyền vào chứ không đọc hằng mô-đun: đáy thang đổi theo việc có phụ đề hay không, mà
// hàm này lại nằm ngoài component. Đọc hằng ở đây là ReferenceError (đã dính đúng lỗi đó).
// 27/8 — BƯỚC THANG PHẢI VỪA DỮ LIỆU, GIỐNG MỘT TRỤC BIỂU ĐỒ ĐÚNG NGHĨA.
// `RUNG_GAP` cố định 232px/bậc log hợp với dữ liệu trải nhiều bậc (trúng số: 1 trên 300 triệu).
// Nhưng kênh JOB DYING nạp thất nghiệp theo năm: quy ra tỉ lệ thì cả sáu năm nằm trong khoảng
// log 1,09-1,44 — tức 0,35 bậc = 81px. Sáu mốc chen nhau trong 81px thì nhìn ra một cụm số
// lộn xộn quanh một vòng tròn, đúng như khung thật cho thấy.
// Trục nào cũng phải co giãn theo dải dữ liệu của nó. Bước thang tính từ mốc cao nhất để dải
// thật trải hết chiều cao dùng được, và vẫn kẹp hai đầu để dữ liệu trải rộng không bị kéo dãn
// quá đà.
const buocThang = (maxLog: number, usable: number) =>
  Math.max(150, Math.min(560, usable / Math.max(1.15, maxLog + 0.45)));
const yForLog = (log: number, trackH: number, pad: number = BOTTOM_PAD_GOC, gap: number = RUNG_GAP) =>
  trackH - pad - log * gap;

export const LongshotShort: React.FC<LongshotProps> = (props) => {
  const { font = "", hookStat = "", hookLabel = "", hookLine = "", bg = "", bg2 = "", title = "WHAT ARE THE REAL ODDS?", source = "", handle = "@longshotusa", color = "#4F46E5", accent = "#4F46E5",
    items = [], introSec = 1.8, itemSec = 2.7, outroSec = 2.4, audio, music, sfx = true , subs = [], rungKieu = "odds", rungDonVi = "" } = props;
  const f = useCurrentFrame(); const { fps, width: W, height: H } = useVideoConfig();

  const introF = Math.round(introSec * fps);
  const starts: number[] = []; let acc = introF;
  for (const it of items) { starts.push(acc); acc += Math.round(idur(it, itemSec) * fps); }
  const introP = spring({ frame: f, fps, config: { damping: 12, stiffness: 140 } });

  // 28/8 — THANG PHẢI VỪA DỮ LIỆU, KHÔNG PHẢI LÚC NÀO CŨNG BẮT ĐẦU TỪ 1.
  // Khung thật FAME CURVE: sáu mốc đọc nằm trong khoảng 5,1K-8,3K, mà thang chạy từ "1" lên tới
  // "1M" — hai phần ba khung trên là khoảng trống, và cả sáu mục chen nhau trong một dải hẹp ở
  // dưới đáy. Người xem không đọc ra chênh lệch giữa chúng, mà chỗ trống thì chiếm mất màn hình.
  // Nguyên nhân: gốc thang ghim cứng ở 0 (tức "1"), và `maxN` còn cộng thêm MỘT bậc thừa nữa.
  // Nay gốc thang tụt xuống ngay dưới mục nhỏ nhất, trần lên ngay trên mục lớn nhất — vẫn là
  // thang log thật, vẫn ghi mốc thật, chỉ là nhìn vào đúng chỗ có dữ liệu.
  const maxLogAll = Math.max(1, ...items.map((d) => d.logValue));
  const minLogAll = Math.min(...items.map((d) => d.logValue), maxLogAll);
  // BƯỚC THANG PHẢI HỢP VỚI DẢI DỮ LIỆU.
  // Thang này sinh ra cho kiểu "1 phần triệu" — dải trải nhiều bậc mười, nên mỗi nấc một bậc là
  // đúng. Nhưng với dữ liệu ĐẾM (lượt đọc theo ngày) thì cả sáu mục nằm gọn trong 0,2 bậc: dù có
  // cắt trần xuống sát dữ liệu, sáu mục vẫn chen nhau trong một dải hẹp và nửa khung vẫn trống,
  // vì bước nấc lớn hơn cả dải dữ liệu.
  // Dải hẹp thì nấc phải nhỏ lại: 5,6K · 7,5K · 10K thay vì 1K · 10K · 100K. Vẫn là thang log
  // thật, vẫn là mốc thật — chỉ là nhìn ở đúng độ phóng mà dữ liệu cần.
  const daiLog = maxLogAll - minLogAll;
  const buocN = daiLog >= 1.2 ? 1 : daiLog >= 0.5 ? 0.25 : 0.1;
  // Chừa một nấc dưới mục thấp nhất để cột không mọc từ sát mép; không xuống dưới 0.
  const gocN = Math.max(0, Math.floor(minLogAll / buocN) * buocN - buocN);
  // Ít nhất bốn nấc để thang còn ra hình một cái thang.
  const maxN = Math.max(gocN + 4 * buocN, Math.ceil(maxLogAll / buocN) * buocN);
  const BOTTOM_PAD = BOTTOM_PAD_GOC + ((subs && subs.length) ? 150 : 0);
  // Chiều cao dùng được của cột thang trong khung 1920 (trừ hai đầu chừa chữ), rồi từ đó suy ra
  // bước thang vừa với dải dữ liệu THẬT của video này.
  const GAP = buocThang((maxN - gocN) / buocN, Math.max(320, 1920 - BOTTOM_PAD - TOP_PAD)) / buocN;
  const trackH = BOTTOM_PAD + (maxN - gocN) * GAP + TOP_PAD;

  // which item is currently active (climbing or holding), and its live Y
  let activeIdx = -1;
  for (let i = 0; i < items.length; i++) { if (f >= starts[i]) activeIdx = i; }

  let activeY = trackH - BOTTOM_PAD; // ground level while still in intro
  let activeLog = 0;
  const climbHops = 3;
  const climbFrac = 0.56; // portion of each item's slot spent hopping, rest = hold/reveal

  const perItemClimb: { y: number; arc: number; done: boolean; justLanded: boolean }[] = [];
  for (let i = 0; i < items.length; i++) {
    const slotFrames = Math.round(idur(items[i], itemSec) * fps);
    const climbDur = Math.max(18, Math.round(slotFrames * climbFrac));
    const prevLog = i === 0 ? gocN : items[i - 1].logValue;   // mục đầu mọc từ GỐC THANG, không từ 1
    const fromY = yForLog(prevLog - gocN, trackH, BOTTOM_PAD, GAP), toY = yForLog(items[i].logValue - gocN, trackH, BOTTOM_PAD, GAP);
    const c = climbPos(f, starts[i], climbDur, climbHops, fromY, toY, fps);
    perItemClimb.push({ y: c.y, arc: c.arc, done: c.done, justLanded: c.justLanded });
  }
  // ── GIÃN NHÃN THEO CHIỀU DỌC (28/8) ────────────────────────────────────────────────────
  // Ảnh thật kênh FAME CURVE: "63.4K" in ĐÈ lên "32.6K", và còn một nhãn thứ ba nấp bên dưới.
  // Gốc: nhãn neo đúng vào `c.y` của mục, mà thang là LOGARIT — hai ngày có lượt đọc gần nhau
  // (63K và 33K chỉ cách nhau 0,28 đơn vị log) rơi xuống gần như cùng một điểm.
  // Chia trái/phải theo chỉ số chẵn/lẻ KHÔNG cứu được: mục 0 và mục 2 đều là chẵn nên cùng bên.
  // Nên phải giãn THẬT: xếp các nhãn cùng bên theo y, cái nào sát nhau quá thì đẩy xuống cho đủ
  // khoảng cách. Nhãn lệch vài chục pixel so với mốc vẫn đọc được và vẫn hiểu là của mục nào;
  // hai nhãn chồng lên nhau thì không đọc được cái nào.
  const CACH_NHAN = 96;                       // cao thật của một nhãn: tên + viên số
  const nhanY: number[] = perItemClimb.map((c) => c.y);
  for (const ben of [0, 1]) {
    const idx = perItemClimb.map((_, i) => i).filter((i) => i % 2 === ben)
      .sort((a, b) => nhanY[a] - nhanY[b]);
    for (let k = 1; k < idx.length; k++) {
      const tr = idx[k - 1], nay = idx[k];
      if (nhanY[nay] - nhanY[tr] < CACH_NHAN) nhanY[nay] = nhanY[tr] + CACH_NHAN;
    }
  }
  if (activeIdx >= 0) { activeY = perItemClimb[activeIdx].y; activeLog = interpolate(activeY, [yForLog(maxLogAll - gocN, trackH, BOTTOM_PAD, GAP), yForLog(0, trackH, BOTTOM_PAD, GAP)], [maxLogAll, gocN]); }

  const isLast = activeIdx === items.length - 1 && activeIdx >= 0;
  const lastDone = isLast && perItemClimb[activeIdx].done;
  const lastLocal = isLast ? f - starts[activeIdx] : 0;

  // zoom: creeps up with rarity reached, extra dramatic punch-in once the final item lands
  let zoom = interpolate(activeLog, [0, maxLogAll], [1, 1.26], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (lastDone) {
    const slotFrames = Math.round(idur(items[activeIdx], itemSec) * fps);
    const climbDur = Math.max(18, Math.round(slotFrames * climbFrac));
    const revealP = spring({ frame: lastLocal - climbDur, fps, config: { damping: 14, stiffness: 90 } });
    zoom = interpolate(revealP, [0, 1], [1.26, 1.46], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  }

  const camY = ANCHOR_Y - activeY;

  // Y CỦA CÁC NHÃN MỤC ĐANG HIỆN Ở NHÁNH TRÁI. Chú thích cũ ngay dưới đây khẳng định nhãn mục
  // "branches left/right so it never collides with the rung badges" — đo lại thì SAI: nhãn thang
  // trải tới RAIL_L+34, còn nhãn mục nhánh trái kết thúc ở RAIL_L-40, hai vùng chồng nhau
  // [RAIL_L-96, RAIL_L-40]. Thấy rõ ở canary: "1 in 15,300" đè lên "1 in 10,000".
  // Cách xử lý: khi hai thứ tranh chỗ thì BỎ nhãn thang, giữ nhãn mục — nhãn mục nói con số CHÍNH
  // XÁC của mục đó, còn nhãn thang chỉ là mốc tròn; giữ cái kém thông tin hơn là chọn sai.
  // 28/8 — PHÉP NÉ NÀY TÍNH SAI CHỖ. Nó đọc `perItemClimb[i].y` — vị trí THÔ của nhãn, trước khi
  // vòng chống chồng ở trên đẩy các nhãn sát nhau ra xa (`nhanY`). Nên nó né một chỗ mà nhãn
  // không còn đứng ở đó nữa. Thấy rõ trên khung anh gửi: "Aug 4" nằm đè lên "10K reads".
  // Và ngưỡng 46 cũng nhỏ hơn thực tế: một nhãn mục cao `CACH_NHAN`=96 (tên + viên số), tức nửa
  // trên/dưới đã là 48, cộng nửa chiều cao chữ của nhãn thang nữa mới đủ khoảng hở.
  // Nhãn mục hai bên đều tranh chỗ với nhãn thang (nhãn thang trải từ mép trái sang tận RAIL_L+34),
  // nên xét cả hai phía chứ không chỉ phía trái.
  const yNhanTrai = items
    .map((it, i) => (f >= starts[i] ? nhanY[i] : null))
    .filter((y): y is number => y !== null);

  return (
      // 26/8 — NỀN SÁNG LÊN. Đo 5 video thật: sáng trung bình chỉ **25-40/255**, trong khi
      // short trên feed thường 60-100 — nhìn tối om, và khung cuối tụt xuống 15 nên trông
      // như video kết thúc bằng màn hình đen. Nâng cả ba chặng gradient, GIỮ NGUYÊN tông màu
      // riêng của từng dạng (tông là thứ phân biệt kênh, không được gộp về một màu).
    <AbsoluteFill style={{ background: nenDayDu(bg || accent, bg2 || color), fontFamily: phong(font), overflow: "hidden",
      // 26/8 — hoạ tiết nền RIÊNG theo kênh: 7 dạng cho 50 kênh nên nhiều kênh dùng chung
      // một bố cục; màu khác nhau không cứu được, người xem nhận ra qua bố cục và nền.
      ...hoaTietNen(bienCua((props as any).bien), accent) }}>
      {/* TIÊU ĐỀ — fixed header, always visible */}
      <div style={{ position: "absolute", top: 74, left: 0, right: 0, textAlign: "center", padding: "0 50px", zIndex: 5 }}>
        {/* 27/8 — BỎ PILL IN TÊN ĐỊNH DẠNG NỘI BỘ (LONGSHOT).
            Người xem không biết chữ đó nghĩa là gì, nhưng nó GOM mọi kênh dùng dạng này thành
            một cụm nhìn thấy được — đúng dấu vân tay "cùng một chủ" mà bộ nhận diện V4 vừa đi
            xoá khỏi ảnh đại diện và ảnh bìa. Để lại trên video thì công kia thành vô nghĩa.
            Và nó chiếm mất dải trên cùng, chỗ đáng ra để tiêu đề thở. */}
        {/* Tiêu đề lúc mở đầu do Bookend vẽ. Header ẩn đi trong quãng đó, nếu không sẽ có hai bản tiêu đề chồng nhau (lỗi 25/8). */}
        <div style={{ display: f < introF ? "none" : undefined, color: "#fff", fontWeight: 900, fontSize: 54, lineHeight: 1.04, marginTop: 14, textShadow: "0 4px 24px #000c", textWrap: "balance" as any, opacity: 0.5 + introP * 0.5 }}>{title}</div>
      </div>

      {/* CAMERA: outer scales (zoom) around the fixed anchor point; inner translates the tall ladder track */}
      <div style={{ position: "absolute", inset: 0, transformOrigin: `50% ${ANCHOR_Y}px`, transform: `scale(${zoom})` }}>
        <div style={{ position: "absolute", left: 0, right: 0, top: 0, width: W, height: trackH, transform: `translateY(${camY}px)` }}>
          {/* rails */}
          <div style={{ position: "absolute", left: RAIL_L, top: 0, width: 6, height: trackH, background: `linear-gradient(180deg, ${accent}00, ${accent}99 12%, ${accent}66 100%)`, borderRadius: 4 }} />
          <div style={{ position: "absolute", left: RAIL_R - 6, top: 0, width: 6, height: trackH, background: `linear-gradient(180deg, ${accent}00, ${accent}99 12%, ${accent}66 100%)`, borderRadius: 4 }} />

          {/* rungs — evenly spaced in LOG space (so real rarity gaps compound going up) */}
          {Array.from({ length: Math.round((maxN - gocN) / buocN) + 1 }, (_, k) => +(gocN + k * buocN).toFixed(4)).map((n) => {
            const ry = yForLog(n - gocN, trackH, BOTTOM_PAD, GAP);
            // 26/8 — CHỒNG CHỮ Ở ĐÁY KHUNG. Thang nằm trong lớp bị dịch `camY`, nên chỗ đứng THẬT
            // của một nấc trên màn hình là `camY + ry`, không phải `ry`. Nấc thấp nhất rơi đúng
            // vào dải đáy nơi đặt @handle -> nhãn "1 in 10" in đè lên tên kênh (thấy rõ ở canary
            // sau khi có defaultProps thật). Nấc trôi ra ngoài khung thì không vẽ: nó không mang
            // thông tin gì, chỉ kịp đâm vào chữ khác.
            // Vị trí THẬT trên khung phải đi qua CẢ HAI phép biến hình, không chỉ một:
            //   translateY(camY)  rồi  scale(zoom) quanh tâm 50% ANCHOR_Y.
            // Bản vá đầu của em chỉ cộng `camY` rồi kết luận nấc nằm an toàn — nhưng zoom 1.26-1.46
            // đẩy mọi thứ DƯỚI tâm xuống thấp thêm, nên nấc "an toàn" ở 1737 thật ra rơi xuống 1859,
            // đúng chỗ @handle. Render lại thấy vẫn chồng y nguyên: dấu hiệu tính sai chứ không phải
            // vá sai chỗ.
            const yMan = ANCHOR_Y + (camY + ry - ANCHOR_Y) * zoom;
            if (yMan > H - 118 || yMan < 92) return null;
            const bidong = yNhanTrai.some((y) => Math.abs(y - ry) < 58);
            const reached = activeLog >= n - 0.15;
            return (
              <div key={n} style={{ position: "absolute", top: ry - 3, left: RAIL_L - 26, width: RAIL_R - RAIL_L + 52, height: 6,
                background: reached ? `${accent}cc` : "#ffffff1c", borderRadius: 3 }}>
                {/* nhãn mốc dời hẳn ra MÉP TRÁI ngoài vùng token leo (CENTER±arc) -> KHÔNG BAO GIỜ bị token to đè lên,
                    dù ở mốc nào cũng đọc được (khác thiết kế cũ: label giữa cột, đúng chỗ token hạ cánh -> luôn đè). */}
                <div style={{ position: "absolute", top: -13, left: -70, whiteSpace: "nowrap", textAlign: "right", width: 130,
                  color: reached ? "#fff" : "#ffffff55", fontWeight: 800, fontSize: 22, letterSpacing: 0.5, textShadow: "0 2px 8px #000a",
                  // 26/8 — ẨN TRONG QUÃNG MỞ ĐẦU. Xem khung thật: "1 in 10" chạy ngang sau nút câu
                  // hỏi, "1 in 100," bị badge cắt cụt. Quãng hook là lúc khối hook làm chủ màn hình;
                  // nhãn trục thuộc về phần thân, hiện sớm chỉ tạo nhiễu chứ không cho thêm thông tin.
                  opacity: (bidong || f < introF) ? 0 : 1 }}>{(n === 0 && buocN === 1 && rungKieu !== "dem") ? "EVERYDAY" : fmtRung(n, rungKieu, rungDonVi)}</div>
              </div>
            );
          })}

          {/* ITEM TOKENS — hop up the pole, land on their real rung, label branches left/right */}
          {items.map((it, i) => {
            if (f < starts[i]) return null;
            const c = perItemClimb[i];
            const side = i % 2 === 0 ? -1 : 1;
            const isFinal = i === items.length - 1;
            const landedGlow = c.done && isFinal;
            const landScale = c.justLanded ? 1.22 : 1;
            const labelP = spring({ frame: f - starts[i] - Math.round(Math.round(idur(it, itemSec) * fps) * climbFrac) + 6, fps, config: { damping: 13, stiffness: 170 } });
            return (
              <React.Fragment key={i}>
                {/* token on the pole */}
                {/* 28/8 — mục ĐÃ QUA thì nhỏ lại và mờ đi. Ảnh thật cho thấy hai biểu tượng 📈
                    chồng nhau thành một cục không đọc được; chúng cùng nằm trên trục nên khi hai
                    mốc gần nhau là dính. Mục đang leo mới là thứ người xem cần nhìn — mục cũ chỉ
                    cần còn dấu vết đường đi. */}
                {/* 28/8 — MỤC ĐÃ QUA THU THÀNH CHẤM, KHÔNG PHẢI VÒNG NHỎ LẠI.
                    Thử trước đó: đẩy vòng sang ngang cho khỏi dính nhau -> vòng lao thẳng vào làn
                    của nhãn, XẤU HƠN bản gốc. Sai hướng: cả nhãn lẫn vòng đều tranh cùng một dải
                    ngang, nên dời ngang chỉ đổi chỗ va chạm chứ không bớt va chạm.
                    Đúng hướng là BỚT THỨ TRANH CHỖ: chỉ mục đang leo mới cần là vòng lớn có biểu
                    tượng; mục đã qua chỉ cần một chấm để thấy đường đi. Chấm 26px thì hai mốc sát
                    nhau vẫn nằm cạnh nhau được, không thành cục. */}
                <div style={{ position: "absolute", top: c.y, left: CENTER + c.arc,
                  transform: `translate(-50%,-50%) scale(${landScale})`,
                  opacity: i < activeIdx ? 0.5 : 1,
                  width: i < activeIdx ? 26 : (isFinal && c.done ? 148 : 108),
                  height: i < activeIdx ? 26 : (isFinal && c.done ? 148 : 108), borderRadius: "50%",
                  background: `radial-gradient(circle at 35% 30%, #ffffff22, ${accent}33 60%, #00000000)`, border: `3px solid ${accent}`,
                  display: "flex", alignItems: "center", justifyContent: "center", fontSize: isFinal && c.done ? 74 : 54,
                  boxShadow: landedGlow ? `0 0 60px ${accent}, 0 0 120px ${accent}88` : `0 6px 18px #0009`, zIndex: 3 }}>
                  {i < activeIdx ? null : (it.emoji || "🎯")}
                </div>
                {/* dust-puff impact ring on landing */}
                {c.justLanded ? (
                  <div style={{ position: "absolute", top: c.y, left: CENTER, transform: "translate(-50%,-50%)", width: 200, height: 200,
                    borderRadius: "50%", border: `3px solid ${accent}`, opacity: 0.7, zIndex: 2 }} />
                ) : null}
                {/* label + real odds, branches left/right so it never collides with the rung badges */}
                {/* 28/8 — CẮT NHÃN RƠI VÀO DẢI ĐÁY, y như đã làm cho nấc thang.
                    Ảnh thật kênh FAME CURVE: số "32,621 reads" in ĐÈ lên "Source: Wikimedia
                    pageviews" và @famecurveusa. Nấc thang đã có luật cắt này từ 26/8, nhưng nhãn
                    và số của MỤC thì chưa — cùng một lỗi, hai loại phần tử, chỉ vá một.
                    Bài học: vá một lỗi chồng chữ thì phải quét MỌI phần tử trôi qua vùng đó, chứ
                    không chỉ cái mình đang nhìn.
                    Dải đáy rộng hơn của nấc (150 vs 118) vì nhãn cao hai dòng: tên + viên số.
                    Mục trôi khỏi khung thì bỏ vẽ — nó đã có phần thời gian của nó rồi, hiện tiếp
                    chỉ kịp đâm vào chữ khác. */}
                {(() => {
                  const yThat = ANCHOR_Y + (camY + nhanY[i] - ANCHOR_Y) * zoom;
                  return yThat > H - 150 || yThat < 80;
                })() ? null :
                c.done || f - starts[i] > Math.round(Math.round(idur(it, itemSec) * fps) * climbFrac) - 4 ? (
                  <div style={{ position: "absolute", top: nhanY[i], left: side < 0 ? RAIL_L - 40 : RAIL_R + 40, transform: `translate(${side < 0 ? "-100%" : "0"}, -50%) scale(${Math.max(0, Math.min(1, labelP))})`,
                    opacity: Math.max(0, Math.min(1, labelP)), textAlign: side < 0 ? "right" as const : "left" as const, maxWidth: 300, zIndex: 3 }}>
                    <div style={{ color: "#fff", fontWeight: 800, fontSize: 30, lineHeight: 1.08, textShadow: "0 2px 10px #000c" }}>{it.label}</div>
                    <div style={{ display: "inline-block", marginTop: 6, background: accent, color: "#fff", fontWeight: 900, fontSize: 26, padding: "5px 14px", borderRadius: 10, letterSpacing: 0.3 }}>
                    {/* 27/8 — số trong THÂN video cũng phải chạy, không chỉ số dẫn ở hook. Cùng lý do: con số đang lớn dần giữ mắt, con số hiện sẵn thì không. */}
                    <SoChay s={String(it.oddsDisp || "")} tuFrame={starts[i]} giay={0.8} />
                  </div>
                  </div>
                ) : null}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* FINAL BIG REVEAL — fixed overlay, not affected by camera transform, glows once the last item lands */}
      {lastDone && items.length ? (() => {
        const last = items[items.length - 1];
        const slotFrames = Math.round(idur(last, itemSec) * fps);
        const climbDur = Math.max(18, Math.round(slotFrames * climbFrac));
        const p = spring({ frame: lastLocal - climbDur, fps, config: { damping: 13, stiffness: 110 } });
        const pulse = 1 + Math.sin((f / fps) * 6) * 0.02;
        return (
          // 29/8 — KHỐI TỔNG KẾT DỜI LÊN NỬA TRÊN.
          // Khung thật: "11.5K" cỡ chữ 100 neo ở đáy (paddingBottom 210) đè thẳng lên nhãn
          // "AUG 16" và viên số của nó — hai khối chữ chồng nhau ngay ở giây quyết định, lúc
          // người xem đang đọc con số cuối.
          // Đáy là vùng ĐÔNG nhất của dạng này: nhãn mục hai bên, viên số, băng phụ đề, dòng
          // nguồn và tên kênh đều ở đó. Nửa trên thì trống — thang log bao giờ cũng để trống phần
          // trên vì mục cao nhất mới chạm tới đó. Dời lên là hết đè, và lấp luôn chỗ chết.
          <AbsoluteFill style={{ alignItems: "center", justifyContent: "flex-start", paddingTop: 250, zIndex: 6, pointerEvents: "none" }}>
            <div style={{ opacity: Math.min(1, p), transform: `translateY(${(1 - Math.min(1, p)) * -40}px) scale(${pulse})`, textAlign: "center", padding: "18px 40px", borderRadius: 22,
                          background: "radial-gradient(70% 120% at 50% 50%, rgba(8,10,20,.72) 0%, rgba(8,10,20,.28) 70%, transparent 100%)" }}>
              <div style={{ color: "#ffffffcc", fontWeight: 800, fontSize: 30, letterSpacing: 2, marginBottom: 6, textTransform: "uppercase" as const }}>{last.label}</div>
              <div style={{ fontFamily: "Anton, 'Poppins'", color: "#fff", fontWeight: 400, fontSize: 100, lineHeight: 0.98, letterSpacing: 1, textShadow: `0 0 50px ${accent}, 0 8px 30px #000c` }}>{last.oddsDisp.toUpperCase()}</div>
            </div>
          </AbsoluteFill>
        );
      })() : null}

      {/* INTRO overlay */}
      {f < introF && !hookStat ? (
        // 26/8 — LỚP PHỦ MỞ ĐẦU TỪNG LÀ MÀN ĐEN. Nền cũ tiến về `#06050f` (gần đen tuyền) và phủ
        // KÍN khung ở `zIndex: 10`, trên đó chỉ có một emoji. Đo trên khung THẬT: **75,6% điểm tối ·
        // 332 màu** — QC trước render chặn đúng, và chặn đúng lý do: người xem mở video ra thấy màn
        // hình gần như đen trong 1,8 giây đầu, đúng quãng quyết định họ có ở lại không.
        // Gán `bg/bg2` cho props chỉ kéo được 82,3% -> 75,6%, vẫn dính ngưỡng, vì thủ phạm là lớp
        // phủ này chứ không phải nền kênh. Nay để nó MỜ: thang leo phía sau hiện xuyên qua, vừa
        // sáng lên vừa tăng số màu, mà vẫn còn vệt tối để chữ hook nổi.
        <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 44%, ${accent}33 0%, ${(bg || accent)}55 45%, #0b0a1acc 78%)`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", paddingBottom: 620, zIndex: 10 }}>
          <div style={{ fontSize: 150, transform: `scale(${introP})` }}>🪜</div>
        </AbsoluteFill>
      ) : null}

      {/* SFX: hop-land per item, bigger impact + ding on the final item */}
      {/* CHUYỂN CẢNH: bắt đầu leo = nhịp nhẹ, chạm nấc = nhịp chính, mục cuối = nhịp mạnh nhất.
          26/8 — thay ba dòng sfx viết cứng (0.22 / 0.45 / 0.7). Ba mức đó chênh nhau hơn ba lần,
          nên riêng trong một video đã nghe lồi lõm; giữa các kênh còn lệch hơn nữa. */}
      {sfx ? (
        <ChuyenCanh accent={accent} khoa={handle}
                    nhip={items.flatMap((it, i) => {
                      const climbDur = Math.max(18, Math.round(Math.round(idur(it, itemSec) * fps) * climbFrac));
                      return [
                        { at: starts[i], manh: 0.35 },
                        { at: starts[i] + climbDur - 4, manh: i === items.length - 1 ? 1 : 0.65 },
                      ];
                    })} />
      ) : null}

      <div style={{ position: "absolute", bottom: 44, left: 0, right: 0, textAlign: "center", color: "#ffffff5c", fontWeight: 700, fontSize: 24, letterSpacing: 0.5, textShadow: "0 1px 6px #0009" }}>{handle}</div>
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
      <Karaoke subs={subs} accent={accent} />
      <Bookend hookStat={hookStat} hookLabel={hookLabel} hookLine={hookLine} title={title} handle={handle} accent={accent} color={color}
               introSec={introSec} outroSec={outroSec} />
          <DongNguon nguon={source} />
    </AbsoluteFill>
  );
};
