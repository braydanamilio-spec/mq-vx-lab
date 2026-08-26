import { AbsoluteFill, Sequence, Audio, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { Karaoke } from "./Karaoke";
import { Bookend } from "./Bookend";
import { phong } from "./Phong";
import { nenKenh } from "./Nen";
import { ChuyenCanh } from "./Chuyen";
import { dungKhung } from "./Khung";
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
  title?: string; subtitle?: string; handle?: string; color?: string; accent?: string;
  tiers?: string[]; items: RankItem[]; introSec?: number; itemSec?: number; outroSec?: number;
  hookStat?: string; hookLabel?: string; hookLine?: string;
  bg?: string; bg2?: string;
  font?: string;
  audio?: string; music?: string; subs?: Word[]; sfx?: boolean;
};

const FPS = 30;
const TIER_COL: Record<string, string> = { S: "#FF3B5C", A: "#FF9F1C", B: "#FFD23F", C: "#3DDC97", D: "#5B8CFF", F: "#8A93A6" };
const tcol = (t: string) => TIER_COL[t?.toUpperCase()] || "#8A93A6";
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

const Card: React.FC<{ it: RankItem; s: number; accent: string; the: any }> = ({ it, s, accent, the }) => (
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
      fontSize: Math.max(26, (it.img ? 30 : 40) - Math.max(0, _tuDai(it.name) - 14) * 2.0),
      lineHeight: 1.05, textAlign: "center", whiteSpace: "normal", overflowWrap: "break-word",
      maxWidth: it.img ? 150 : 330 }}>{it.name}</div>
    {it.stat ? <div style={{ color: accent, fontWeight: 800, fontSize: 24 }}>{it.stat}</div> : null}
  </div>
);

export const RankedShort: React.FC<RankedProps> = (props) => {
  const { font = "", hookStat = "", hookLabel = "", hookLine = "", bg = "", bg2 = "", title = "TIER LIST", subtitle = "", handle = "@rankedusa", color = "#7C5CFF", accent = "#7C5CFF",
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

  return (
      // 26/8 — NỀN SÁNG LÊN. Đo 5 video thật: sáng trung bình chỉ **25-40/255**, trong khi
      // short trên feed thường 60-100 — nhìn tối om, và khung cuối tụt xuống 15 nên trông
      // như video kết thúc bằng màn hình đen. Nâng cả ba chặng gradient, GIỮ NGUYÊN tông màu
      // riêng của từng dạng (tông là thứ phân biệt kênh, không được gộp về một màu).
    <AbsoluteFill style={{ background: nenKenh(bg || accent, bg2 || color), fontFamily: phong(font), ...hoaTietNen(B, accent) }}>
      {/* TIÊU ĐỀ */}
      <div style={{ position: "absolute", top: K.tieuDeTop, left: 0, right: 0, textAlign: "center", padding: `0 ${K.padX}px` }}>
        <div style={{ display: "inline-block", background: color, color: "#0a0c14", fontWeight: 900, fontSize: K.nhanCo, letterSpacing: 2, padding: "8px 22px", borderRadius: 12 }}>🏆 RANKED</div>
        {/* Tiêu đề lúc mở đầu do Bookend vẽ. Header ẩn đi trong quãng đó, nếu không sẽ có hai bản tiêu đề chồng nhau (lỗi 25/8). */}
        <div style={{ display: f < introF ? "none" : undefined, color: "#fff", fontWeight: 900, fontSize: K.tieuDeCo, lineHeight: 1.02, marginTop: K.doc ? 18 : 10, textShadow: "0 4px 24px #000c", textWrap: "balance" as any, transform: `translateY(${(1 - introP) * 20}px)`, opacity: 0.4 + introP * 0.6 }}>{title}</div>
        {subtitle ? <div style={{ color: "#a9b0cc", fontWeight: 700, fontSize: K.doc ? 32 : 26, marginTop: 8 }}>{subtitle}</div> : null}
      </div>

      {/* BẢNG TIER */}
      <div style={{ position: "absolute", top: K.thanTop, bottom: dayBang, left: K.padX, right: K.padX, display: "flex", flexDirection: "column", gap: K.doc ? 16 : 12 }}>
        {hangCoDo.map((t) => {
          const rowItems = items.map((it, gi) => ({ it, gi })).filter((x) => (x.it.tier || "").toUpperCase() === t.toUpperCase());
          return (
            <div key={t} style={{ flex: 1, display: "flex", minHeight: 0,
              // biến thể `nhan`: 0 = nhãn cột TRÁI (cũ) · 1 = cột PHẢI · 2 = hàng TRÊN
              flexDirection: B.nhan === 2 ? "column" : "row",
              alignItems: B.nhan === 2 ? "stretch" : "stretch",
              gap: B.nhan === 2 ? 6 : 14 }}>
              <div style={{
                ...(B.nhan === 2
                    ? { width: "100%", height: K.doc ? 54 : 40, borderRadius: 10, letterSpacing: 4 }
                    : { width: K.doc ? 130 : 108, borderRadius: 16 }),
                order: B.nhan === 1 ? 2 : 0,
                background: tcol(t), color: "#0a0c14", fontWeight: 900,
                fontSize: B.nhan === 2 ? (K.doc ? 34 : 26) : (K.doc ? 84 : 62),
                display: "flex", alignItems: "center", justifyContent: "center",
                boxShadow: `0 6px 20px ${tcol(t)}55` }}>{t.toUpperCase()}</div>
              <div style={{ flex: 1, borderRadius: 16, background: "#ffffff08", border: "1.5px solid #ffffff12", display: "flex", alignItems: "center",
                gap: 14, padding: "0 18px", flexWrap: "wrap", overflow: "hidden" }}>
                {rowItems.map(({ it, gi }) => {
                  const s = spring({ frame: f - starts[gi], fps, config: { damping: 12, stiffness: 170 } });
                  if (f < starts[gi]) return null;
                  return <Card key={gi} it={it} s={s} accent={accent} the={kieuThe(B, accent)} />;
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
      {f < introF && K.doc ? (
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

      <div style={{ position: "absolute", bottom: K.handleDay, left: 0, right: 0, textAlign: "center", color: "#ffffffcc", fontWeight: 800, fontSize: K.doc ? 32 : 24, textShadow: "0 2px 10px #000" }}>{handle}</div>
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
      <Karaoke subs={subs} accent={accent} />
      <Bookend hookStat={hookStat} hookLabel={hookLabel} hookLine={hookLine} title={title} handle={handle} accent={accent} color={color}
               introSec={introSec} outroSec={outroSec} />
    </AbsoluteFill>
  );
};
