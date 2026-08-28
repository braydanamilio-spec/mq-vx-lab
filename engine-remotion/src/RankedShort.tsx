import { AbsoluteFill, Sequence, Audio, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { Karaoke } from "./Karaoke";
import { Bookend } from "./Bookend";
import { phong } from "./Phong";
import { SoChay, SO_DEU, DongNguon } from "./So";
import { nenDayDu } from "./Nen";
import { ChuyenCanh } from "./Chuyen";
import { dungKhung, dayTieuDe } from "./Khung";
import { bienCua, hoaTietNen, kieuThe } from "./Bien";
import React from "react";

// KÊNH #3 RANKED — tier list S/A/B/C/D, thẻ lật vào hạng lần lượt. Motif khác hẳn map/bar/guess.
const FB_IMG = staticFile("img/_fallback.jpg");
const SafeImg: React.FC<any> = ({ src, ...rest }) => {
  const [s, setS] = React.useState(src);
  React.useEffect(() => { setS(src); }, [src]);
  return <Img src={s} onError={() => { if (s !== FB_IMG) setS(FB_IMG); }} {...rest} />;
};

type Word = { t: number; d: number; w: string };
export type RankItem = { name: string; tier: string; img?: string; stat?: string; dur?: number };
export type RankedProps = {
  title?: string; subtitle?: string; handle?: string; source?: string; color?: string; accent?: string;
  tiers?: string[]; items: RankItem[]; introSec?: number; itemSec?: number; outroSec?: number;
  hookStat?: string; hookLabel?: string; hookLine?: string;
  bg?: string; bg2?: string;
  font?: string;
  audio?: string; music?: string; subs?: Word[]; sfx?: boolean;
};

const FPS = 30;
// 27/8 — BẢNG MÀU BẬC PHẢI LÀ MÀU CỦA KÊNH.
// Bảng cũ viết cứng đỏ/cam/vàng/lục — đúng bảng màu mà mọi video "tier list" trên Internet dùng.
// Nó làm hai việc tệ cùng lúc: nhìn như ảnh chế có sẵn (anh gọi là "rẻ tiền"), và xoá sạch nhận
// diện — 50 kênh có 50 bảng màu riêng trong `brand.palette` mà lên khung đều đỏ-cam-vàng-lục.
// Nay dựng thang 6 bậc TỪ HAI MÀU CỦA CHÍNH KÊNH: bậc cao lấy màu nhấn ở cường độ đầy, xuống
// dần thì nhạt và ngả về màu phụ. Thứ hạng vẫn đọc được ngay bằng mắt, mà mỗi kênh một tông.
const _rgb = (h: string) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
const _tron = (a: string, b: string, t: number) => {
  if (!/^#[0-9a-fA-F]{6}$/.test(a) || !/^#[0-9a-fA-F]{6}$/.test(b)) return a;
  const [x1, x2, x3] = _rgb(a), [y1, y2, y3] = _rgb(b);
  const k = (x: number, y: number) => Math.round(x + (y - x) * t).toString(16).padStart(2, "0");
  return `#${k(x1, y1)}${k(x2, y2)}${k(x3, y3)}`;
};
const THANG = "SABCDF";
const tcol = (t: string, accent: string, phu: string) => {
  const i = THANG.indexOf((t || "").toUpperCase());
  if (i < 0) return "#8A93A6";
  // Trộn thẳng accent -> phụ theo i/5 cho hai bậc đầu gần như trùng màu (S và A nhìn giống nhau
  // trên khung thật). Ép thêm một bước TỐI DẦN nữa để mỗi bậc cách bậc kế một khoảng thấy rõ.
  const c = _tron(accent, phu && /^#/.test(phu) ? phu : "#5B6479", Math.min(1, (i / 5) * 1.15));
  return _tron(c, "#0B0E17", i * 0.11);
};

/** Con số nằm trong `stat` ("154K", "9.2K", "8x", "3 cases") -> để vẽ cột theo ĐỘ LỚN. */
const _giaTri = (s?: string): number => {
  const m = String(s || "").match(/([\d][\d,\.]*)\s*([KMB])?/i);
  if (!m) return 0;
  const v = parseFloat(m[1].replace(/,/g, "")) || 0;
  const d = (m[2] || "").toUpperCase();
  return v * (d === "B" ? 1e9 : d === "M" ? 1e6 : d === "K" ? 1e3 : 1);
};
// Co chữ phải tính theo TỪ DÀI NHẤT, không theo cả chuỗi: chuỗi nhiều từ thì xuống dòng được,
// co theo tổng độ dài làm "Honeywell International" (2 từ ngắn) tụt còn 22px trong khi thẻ bên
// cạnh vẫn 40px — bảng nhìn loạn cỡ chữ mà chẳng vì lý do gì.
const _tuDai = (t?: string) => String(t || "").split(/\s+/).reduce((a, w) => Math.max(a, w.length), 1);
const idur = (it: RankItem, s: number) => (it.dur && it.dur > 0 ? it.dur : s);

export const calcRanked = ({ props }: any) => {
  const its: RankItem[] = props.items || [];
  const isec = props.introSec ?? 1.8, isc = props.itemSec ?? 1.7, tail = props.outroSec ?? 1.6;
  const total = its.reduce((a, it) => a + idur(it, isc), 0);
  return { durationInFrames: Math.round((isec + total + tail) * FPS), fps: FPS };
};

const Card: React.FC<{ it: RankItem; s: number; accent: string; the: any; tuF?: number }> = ({ it, s, accent, the, tuF = 0 }) => (
  <div style={{ transform: `scale(${0.5 + s * 0.5}) perspective(600px) rotateY(${(1 - s) * 80}deg)`, opacity: s,
    ...the, padding: it.img ? 8 : "14px 20px",
    display: "flex", flexDirection: "column", alignItems: "center", gap: 6, minWidth: it.img ? 150 : 0, boxShadow: "0 8px 22px #0007" }}>
    {it.img ? <SafeImg src={staticFile(it.img)} style={{ width: 150, height: 104, objectFit: "cover", borderRadius: 10 }} /> : null}
    {/* Tên hạng mục do Gemini sinh, KHÔNG bị giới hạn độ dài trong schema. Trước đây để nowrap +
        cỡ chữ cố định -> tên dài ("MCDONALD'S QUARTER POUNDER WITH CHEESE") TRÀN HẲN ra ngoài thẻ.
        Nay: cho xuống dòng + tự thu cỡ chữ theo độ dài (giống cách ScaledShort vốn đã làm đúng). */}
    {/* 25/8 — thẻ rộng 260 + co chữ nhẹ (1.4) khiến một từ đơn dài vẫn không vừa, và
        overflowWrap ĐƯỢC PHÉP bẻ GIỮA TỪ: "Globalfoundries" ra thành "Globalfound / ries".
        Nới bề ngang và co mạnh hơn để một từ luôn nằm trọn; chỉ bẻ giữa từ khi hết cách. */}
    <div style={{ color: "#fff", fontWeight: 900,
      fontSize: Math.max(22, (it.img ? 26 : 32) - Math.max(0, _tuDai(it.name) - 14) * 1.7),
      lineHeight: 1.05, textAlign: "center", whiteSpace: "normal", overflowWrap: "break-word",
      maxWidth: it.img ? 150 : 330 }}>{it.name}</div>
    {/* 27/8 — CON SỐ PHẢI TO HƠN TÊN. Bản cũ để tên 40px còn số 24px, tức thứ DUY NHẤT phân biệt
        các mục với nhau lại được in bé nhất thẻ. Người lướt short đọc con số trước, tên sau —
        đảo đúng thứ tự đó thì bảng tự nó có nhịp, không cần thêm hiệu ứng nào. */}
    {it.stat ? (
      <SoChay s={it.stat} tuFrame={tuF} giay={0.95}
              style={{ color: accent, fontWeight: 900, fontSize: it.img ? 34 : 52, lineHeight: 1,
                       letterSpacing: -1, marginTop: 2, display: "inline-block",
                       textShadow: `0 2px 14px ${accent}55` }} />
    ) : null}
  </div>
);

export const RankedShort: React.FC<RankedProps> = (props) => {
  const { font = "", hookStat = "", hookLabel = "", hookLine = "", bg = "", bg2 = "", title = "TIER LIST", subtitle = "", source = "", handle = "@rankedusa", color = "#7C5CFF", accent = "#7C5CFF",
    tiers = ["S", "A", "B", "C", "D"], items = [], introSec = 1.8, itemSec = 1.7, outroSec = 1.6, audio, music, sfx = true , subs = [] } = props;
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const K = dungKhung();          // bố cục theo KHỔ — dọc giữ y số cũ, ngang là bộ số riêng
  const B = bienCua((props as any).bien);   // biến thể bố cục RIÊNG của kênh (18 kênh cùng dạng)
  const introF = Math.round(introSec * fps);
  const introP = spring({ frame: f, fps, config: { damping: 12, stiffness: 140 } });

  // mốc xuất hiện của từng item (offset cộng dồn theo dur item) — bám giọng
  const starts: number[] = []; let acc = introF;
  for (const it of items) { starts.push(acc); acc += Math.round(idur(it, itemSec) * fps); }

  // Hàng tier KHÔNG có item nào thì không vẽ: trước đây bảng luôn vẽ đủ S/A/B/C/D nên một danh
  // sách 6 mục dùng S/A/B/C để lại nguyên hàng D rỗng — mất trắng 1/5 chiều cao màn hình dọc.
  const hangCoDo = tiers.filter((t) => items.some((it) => (it.tier || "").toUpperCase() === t.toUpperCase()));
  // Băng chữ karaoke neo ở bottom 200 và cao ~2 dòng; bảng tier neo bottom 130 -> chữ ĐÈ lên hàng
  // cuối. Có sub thì nhường chỗ, không sub thì dùng lại toàn bộ chiều cao.
  const dayBang = (subs && subs.length) ? K.thanDayCoSub : K.thanDayKhongSub;
  // Thân bảng lùi xuống dưới khối tiêu đề THẬT, không dùng mốc cứng — xem `dayTieuDe`.
  const thanTop = Math.max(K.thanTop, dayTieuDe(title, K, !!subtitle));

  return (
      // 26/8 — NỀN SÁNG LÊN. Đo 5 video thật: sáng trung bình chỉ **25-40/255**, trong khi
      // short trên feed thường 60-100 — nhìn tối om, và khung cuối tụt xuống 15 nên trông
      // như video kết thúc bằng màn hình đen. Nâng cả ba chặng gradient, GIỮ NGUYÊN tông màu
      // riêng của từng dạng (tông là thứ phân biệt kênh, không được gộp về một màu).
    <AbsoluteFill style={{ background: nenDayDu(bg || accent, bg2 || color), fontFamily: phong(font), ...hoaTietNen(B, accent) }}>
      {/* TIÊU ĐỀ */}
      <div style={{ position: "absolute", top: K.tieuDeTop, left: 0, right: 0, textAlign: "center", padding: `0 ${K.padX}px` }}>
        {/* 27/8 — BỎ PILL "🏆 RANKED".
            Nó in TÊN ĐỊNH DẠNG NỘI BỘ của pipeline lên mặt video. Người xem không biết "RANKED"
            là gì, nhưng nó gom mọi kênh dùng dạng này thành một cụm nhìn thấy được — đúng thứ
            dấu vân tay "cùng một chủ" mà cả bộ nhận diện V4 vừa đi xoá. Và nó chiếm mất khoảng
            trên cùng, chỗ đáng ra để tiêu đề thở. */}
        {/* Tiêu đề lúc mở đầu do Bookend vẽ. Header ẩn đi trong quãng đó, nếu không sẽ có hai bản tiêu đề chồng nhau (lỗi 25/8). */}
        <div style={{ display: f < introF ? "none" : undefined, color: "#fff", fontWeight: 900, fontSize: K.tieuDeCo, lineHeight: 1.02, marginTop: K.doc ? 18 : 10, textShadow: "0 4px 24px #000c", textWrap: "balance" as any, transform: `translateY(${(1 - introP) * 20}px)`, opacity: 0.4 + introP * 0.6 }}>{title}</div>
        {subtitle ? <div style={{ color: "#a9b0cc", fontWeight: 700, fontSize: K.doc ? 32 : 26, marginTop: 8 }}>{subtitle}</div> : null}
      </div>

      {/* BẢNG TIER */}
      <div style={{ position: "absolute", top: thanTop, bottom: dayBang, left: K.padX, right: K.padX, display: "flex", flexDirection: "column", gap: K.doc ? 16 : 12 }}>
        {hangCoDo.map((t) => {
          const rowItems = items.map((it, gi) => ({ it, gi })).filter((x) => (x.it.tier || "").toUpperCase() === t.toUpperCase());
          // 27/8 — HÀNG CHƯA CÓ MỤC THÌ CHƯA HIỆN.
          // Xem khung thật frame 300: hai hàng B và C là hai hình chữ nhật rỗng chiếm 40% khung,
          // suốt phần lớn video. Khung trống không phải "chỗ thở", nó đọc ra như video lỗi.
          // Hàng nở ra đúng lúc mục đầu của nó xuất hiện: hết chỗ chết, và tự nó thành chuyển động.
          const dauTien = rowItems.length ? Math.min(...rowItems.map((x) => starts[x.gi])) : Infinity;
          const moR = spring({ frame: f - dauTien, fps, config: { damping: 14, stiffness: 120 } });
          if (f < dauTien) return null;
          // Cột nền theo ĐỘ LỚN: 154K và 254 đang hiện hai cái chip to bằng nhau, tức con số to
          // nhất bảng không hề nổi hơn con số bé nhất. Vẽ cột chạy sau thẻ theo tỉ lệ thật thì
          // chênh lệch đọc được ngay từ xa, khỏi phải đọc chữ.
          const vMax = Math.max(1, ...items.map((it) => _giaTri(it.stat)));
          const vRow = Math.max(...rowItems.map((x) => _giaTri(x.it.stat)), 0);
          // 27/8 — THANG TUYẾN TÍNH LÀM CỘT NHỎ THÀNH VÔ DỤNG.
          // Đo trên chính bảng này: 154K / 9.2K / 837 / 254. Chia thẳng thì cột hàng A còn 6%,
          // hàng C còn 0,16% — nằm lọt sau tấm thẻ, không ai thấy. Cột nhìn không ra thì thà
          // không vẽ.
          // Dùng luỹ thừa 0,4 (họ hàng căn bậc hai): GIỮ NGUYÊN THỨ TỰ và vẫn cho thấy chênh
          // lệch là lớn, nhưng nén khoảng cách đủ để mọi hàng có một cột đọc được. Đây là cách
          // các bảng dữ liệu nghiêm túc vẫn làm khi dải giá trị trải hàng nghìn lần.
          // Kẹp bằng `Math.max(0.17, …)` thì mọi giá trị nhỏ đều bị đẩy về ĐÚNG 0,17 — 837 và
          // 254 ra hai cột dài bằng nhau, tức lại mất đúng thứ mình đang cố vẽ. Ánh xạ vào dải
          // [0,17 … 1] thay vì kẹp: cột ngắn nhất vẫn đủ thấy, mà không hai cột nào bằng nhau
          // trừ khi số bằng nhau thật.
          const tyLe = vRow > 0 ? 0.17 + 0.83 * Math.pow(vRow / vMax, 0.4) : 0;
          return (
            <div key={t} style={{ flex: 1, display: "flex", minHeight: 0,
              transformOrigin: "left center",
              transform: `scaleY(${0.7 + 0.3 * moR})`, opacity: moR,
              // biến thể `nhan`: 0 = nhãn cột TRÁI (cũ) · 1 = cột PHẢI · 2 = hàng TRÊN
              flexDirection: B.nhan === 2 ? "column" : "row",
              alignItems: B.nhan === 2 ? "stretch" : "stretch",
              gap: B.nhan === 2 ? 6 : 14 }}>
              <div style={{
                ...(B.nhan === 2
                    ? { width: "100%", height: K.doc ? 54 : 40, borderRadius: 10, letterSpacing: 4 }
                    : { width: K.doc ? 130 : 108, borderRadius: 16 }),
                order: B.nhan === 1 ? 2 : 0,
                background: tcol(t, accent, color), color: "#0a0c14", fontWeight: 900,
                fontSize: B.nhan === 2 ? (K.doc ? 34 : 26) : (K.doc ? 84 : 62),
                display: "flex", alignItems: "center", justifyContent: "center",
                boxShadow: `0 6px 20px ${tcol(t, accent, color)}55` }}>{t.toUpperCase()}</div>
              <div style={{ flex: 1, borderRadius: 16, background: "#ffffff08", border: "1.5px solid #ffffff12", display: "flex", alignItems: "center",
                gap: 14, padding: "0 18px", flexWrap: "wrap", overflow: "hidden", position: "relative" }}>
                {tyLe > 0 ? (
                  /* Alpha 0x3a nhìn ra mảng nền chứ không ra cột số liệu. Đậm lên, bo góc phải
                     và thêm vạch mép dày: mắt phải đọc được "cột này dài gấp mấy cột kia" từ xa,
                     trước cả khi đọc chữ. */
                  <div style={{ position: "absolute", left: 0, top: 0, bottom: 0,
                                width: `${tyLe * 100 * Math.min(1, moR)}%`,
                                background: `linear-gradient(90deg, ${tcol(t, accent, color)}9e 0%, ${tcol(t, accent, color)}52 70%, ${tcol(t, accent, color)}1f 100%)`,
                                borderRight: `5px solid ${tcol(t, accent, color)}`,
                                borderRadius: "16px 6px 6px 16px",
                                boxShadow: `0 0 26px ${tcol(t, accent, color)}44` }} />
                ) : null}
                {rowItems.map(({ it, gi }) => {
                  const s = spring({ frame: f - starts[gi], fps, config: { damping: 12, stiffness: 170 } });
                  if (f < starts[gi]) return null;
                  return <Card key={gi} it={it} s={s} accent={accent} the={kieuThe(B, accent)} tuF={starts[gi]} />;
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* INTRO overlay ngắn */}
      {/* 26/8 — LỚP EMOJI MỞ ĐẦU CHỈ VẼ Ở KHỔ DỌC. Khổ dọc đẩy nó lên bằng `paddingBottom: 620`
          nên nó nằm TRÊN khối hook của Bookend. Khung ngang chỉ cao 1080, không còn chỗ để đẩy —
          đo thật khung giây thứ 1 của long: emoji 🏆 nằm ĐÈ giữa số dẫn, đọc ra "Cl.I" lẫn hình
          cái cúp. Bookend đã vẽ trọn thẻ mở đầu rồi, nên ở khổ ngang lớp này là thừa. */}
      {f < introF && K.doc && !hookStat ? (
        <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 42%, #7C5CFF22, #07060f 70%)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", paddingBottom: K.doc ? 620 : 150 }}>
          <div style={{ fontSize: K.doc ? 150 : 110, transform: `scale(${introP})` }}>🏆</div>
        </AbsoluteFill>
      ) : null}

      {/* CHUYỂN CẢNH — mỗi thẻ vào là MỘT nhịp: cùng lúc một tiếng và một chuyển động hình.
          26/8 — thay cho hai dòng sfx viết cứng `volume={0.5}` / `volume={0.4}` ở đây. Mức âm nay
          do `Chuyen.MUC_AM` quyết một chỗ cho toàn hệ; tiếng thì đổi theo chữ ký của KÊNH nên 18
          kênh dùng chung dạng `ranked` không còn nghe giống hệt nhau. Thẻ vào hạng S = nhịp mạnh. */}
      {sfx ? (
        <ChuyenCanh accent={accent} khoa={handle}
                    nhip={items.map((it, gi) => ({
                      at: starts[gi],
                      manh: (it.tier || "").toUpperCase() === "S" ? 1 : 0.6,
                    }))} />
      ) : null}

      <div style={{ position: "absolute", bottom: K.handleDay, left: 0, right: 0, textAlign: "center", color: "#ffffff5c", fontWeight: 700, fontSize: K.doc ? 24 : 19, textShadow: "0 1px 6px #0009" }}>{handle}</div>
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
      <Karaoke subs={subs} accent={accent} />
      <Bookend hookStat={hookStat} hookLabel={hookLabel} hookLine={hookLine} title={title} handle={handle} accent={accent} color={color}
               introSec={introSec} outroSec={outroSec} />
          <DongNguon nguon={source} />
    </AbsoluteFill>
  );
};
