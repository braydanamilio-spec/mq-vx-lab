import { AbsoluteFill, Sequence, Audio, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { Karaoke } from "./Karaoke";
import { Bookend } from "./Bookend";
import { phong } from "./Phong";
import { SoChay, SO_DEU, DongNguon } from "./So";
import { bienCua, hoaTietNen } from "./Bien";
import { nenKenh } from "./Nen";
import { ChuyenCanh } from "./Chuyen";
import React from "react";

// KÊNH #5 THEN×NOW — split XƯA (trên) / NAY (dưới) + con số biến đổi. Motif riêng (nostalgia + shock).
const FB_IMG = staticFile("img/_fallback.jpg");
const SafeImg: React.FC<any> = ({ src, ...rest }) => {
  const [s, setS] = React.useState(src);
  React.useEffect(() => { setS(src); }, [src]);
  return <Img src={s} onError={() => { if (s !== FB_IMG) setS(FB_IMG); }} {...rest} />;
};

type Word = { t: number; d: number; w: string };
export type TNPair = { label: string; thenYear: string; thenVal: string; nowYear: string; nowVal: string;
  change?: string; thenImg?: string; nowImg?: string; dur?: number };
export type ThenNowProps = {
  title?: string; handle?: string; source?: string; color?: string; accent?: string;
  pairs: TNPair[]; introSec?: number; pairSec?: number; outroSec?: number;
  hookStat?: string; hookLabel?: string; hookLine?: string;
  bg?: string; bg2?: string;
  font?: string;
  audio?: string; music?: string; subs?: Word[]; sfx?: boolean;
};

const FPS = 30;
const pdur = (p: TNPair, s: number) => (p.dur && p.dur > 0 ? p.dur : s);
const SEPIA = "#c79a3e";

export const calcThenNow = ({ props }: any) => {
  const ps: TNPair[] = props.pairs || [];
  const isec = props.introSec ?? 1.6, psc = props.pairSec ?? 4.5, tail = props.outroSec ?? 1.6;
  const total = ps.reduce((a, p) => a + pdur(p, psc), 0);
  return { durationInFrames: Math.round((isec + total + tail) * FPS), fps: FPS };
};

// 1 cặp: XƯA trượt từ trên, NAY trượt từ dưới, chip biến đổi bung giữa
const TNPairView: React.FC<{ p: TNPair; accent: string; sec: number; font?: string; cosub?: boolean }> = ({ p, accent, sec, font = "", cosub = false }) => {
  const f = useCurrentFrame(); const dur = sec * FPS;
  const thenIn = spring({ frame: f, fps: FPS, config: { damping: 14, stiffness: 120 } });
  const nowIn = spring({ frame: f - 10, fps: FPS, config: { damping: 14, stiffness: 120 } });
  const chgAt = Math.round(dur * 0.42);
  const chg = spring({ frame: f - chgAt, fps: FPS, config: { damping: 9, stiffness: 180 } });
  const zoomT = interpolate(f, [0, dur], [1.06, 1.14]);
  const zoomN = interpolate(f, [0, dur], [1.14, 1.06]);
  // 26/8 — CHỪA CHỖ CHO BĂNG PHỤ ĐỀ. Hai thẻ cao 810 bắt đầu ở top 150 ⇒ thẻ dưới kết thúc ở
  // y≈1790, trong khi băng chữ karaoke neo `bottom 200` có mép trên ≈1608 ⇒ phụ đề nằm ĐÈ vào
  // trong thẻ "NOW" (thấy rõ ở RENT REALITY: dòng "From 127,046 to 481,825 dollars" nằm trong thẻ).
  // Có sub thì thu mỗi thẻ lại để đáy thẻ dưới dừng trên băng chữ.
  const HALF = cosub ? 705 : 810;   // (1920 - 140 top - 160 bottom)/2 ~ vùng mỗi panel
  return (
    // 23/8 (user: "khung đen kết thúc cuối video"): gốc AbsoluteFill này TRƯỚC ĐÂY KHÔNG CÓ NỀN.
    // Hai panel bên trong chạy theo animation, hết nội dung (hoặc lúc video còn dài hơn phần hình)
    // là lộ nền trong suốt -> Remotion xuất ra ĐEN. Nay luôn có nền thương hiệu phía dưới cùng.
    <AbsoluteFill style={{ background: "radial-gradient(120% 90% at 50% 12%, #241a0c 0%, #140f07 55%, #080604 100%)" }}>
      {/* PANEL XƯA (trên) */}
      <div style={{ position: "absolute", top: 150, left: 40, right: 40, height: HALF, borderRadius: 26, overflow: "hidden",
        transform: `translateY(${(1 - thenIn) * -60}px)`, opacity: thenIn, border: `3px solid ${SEPIA}` }}>
        {p.thenImg ? <SafeImg src={staticFile(p.thenImg)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", transform: `scale(${zoomT})`, filter: "sepia(0.75) contrast(1.05) brightness(0.72)" }} /> : null}
        <AbsoluteFill style={{ background: p.thenImg ? "linear-gradient(180deg,#1a1206aa,#0d0a04dd)" : "linear-gradient(160deg,#2a2110,#140f06)" }} />
        <div style={{ position: "absolute", top: 26, left: 30, background: SEPIA, color: "#1a1206", fontWeight: 900, fontSize: 40, padding: "8px 22px", borderRadius: 12, fontFamily: phong(font), zIndex: 2 }}>{p.thenYear}</div>
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "0 30px", fontFamily: phong(font) }}>
          <div style={{ color: "#e8d3a0", fontWeight: 800, fontSize: 42, letterSpacing: 1, textTransform: "uppercase", textAlign: "center" }}>{p.label}</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 150, lineHeight: 1, marginTop: 6, textShadow: `0 4px 30px #000` }}>{p.thenVal}</div>
        </div>
      </div>

      {/* CHIP BIẾN ĐỔI giữa */}
      <div style={{ position: "absolute", top: 150 + HALF, left: 0, right: 0, display: "flex", justifyContent: "center", zIndex: 5,
        transform: `translateY(-50%) scale(${0.4 + chg * 0.6})`, opacity: chg }}>
        <div style={{ background: accent, color: "#0a0c14", fontWeight: 900, fontSize: 58, padding: "12px 40px", borderRadius: 40,
          boxShadow: `0 10px 40px ${accent}88`, fontFamily: phong(font), display: "flex", alignItems: "center", gap: 12 }}>
          {/* 26/8 — mũi tên phải theo CHIỀU CỦA SỐ, không phải theo chiều bố cục. Bản cũ luôn
              vẽ ⬇ nên "+242%" hiện kèm mũi tên đi xuống: người xem đọc ra "giảm". */}
          <span style={{ fontSize: 48 }}>{/^\s*-/.test(String(p.change || "")) ? "⬇" : "⬆"}</span>{p.change || "NOW"}
        </div>
      </div>

      {/* PANEL NAY (dưới) */}
      <div style={{ position: "absolute", top: 150 + HALF + 20, left: 40, right: 40, height: HALF, borderRadius: 26, overflow: "hidden",
        transform: `translateY(${(1 - nowIn) * 60}px)`, opacity: nowIn, border: `3px solid ${accent}` }}>
        {p.nowImg ? <SafeImg src={staticFile(p.nowImg)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", transform: `scale(${zoomN})`, filter: "saturate(1.15) brightness(0.82)" }} /> : null}
        <AbsoluteFill style={{ background: p.nowImg ? "linear-gradient(0deg,#0a0c14aa,#0a0c14dd)" : `linear-gradient(200deg,#1a0f18,#0a0c14)` }} />
        <div style={{ position: "absolute", top: 26, right: 30, background: accent, color: "#0a0c14", fontWeight: 900, fontSize: 40, padding: "8px 22px", borderRadius: 12, fontFamily: phong(font), zIndex: 2 }}>{p.nowYear}</div>
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "0 30px", fontFamily: phong(font) }}>
          <div style={{ color: "#f6b7d8", fontWeight: 800, fontSize: 42, letterSpacing: 1, textTransform: "uppercase", textAlign: "center" }}>{p.label}</div>
          <div style={{ color: "#fff", fontWeight: 900, fontSize: 150, lineHeight: 1, marginTop: 6, textShadow: `0 4px 30px #000, 0 0 40px ${accent}66` }}>{p.nowVal}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const ThenNowShort: React.FC<ThenNowProps> = (props) => {
  const { font = "", hookStat = "", hookLabel = "", hookLine = "", bg = "", bg2 = "", title = "THEN vs NOW", source = "", handle = "@thennowusa", color = "#EC4899", accent = "#EC4899",
    pairs = [], introSec = 1.6, pairSec = 4.5, outroSec = 1.6, audio, music, sfx = true , subs = [] } = props;
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const introF = Math.round(introSec * fps);
  const introP = spring({ frame: f, fps, config: { damping: 12, stiffness: 140 } });
  const starts: number[] = []; let acc = introF;
  for (const p of pairs) { starts.push(acc); acc += Math.round(pdur(p, pairSec) * fps); }

  return (
      // 26/8 — NỀN SÁNG LÊN. Đo 5 video thật: sáng trung bình chỉ **25-40/255**, trong khi
      // short trên feed thường 60-100 — nhìn tối om, và khung cuối tụt xuống 15 nên trông
      // như video kết thúc bằng màn hình đen. Nâng cả ba chặng gradient, GIỮ NGUYÊN tông màu
      // riêng của từng dạng (tông là thứ phân biệt kênh, không được gộp về một màu).
    <AbsoluteFill style={{ background: nenKenh(bg || accent, bg2 || color), fontFamily: phong(font),
      // 26/8 — hoạ tiết nền RIÊNG theo kênh: 7 dạng cho 50 kênh nên nhiều kênh dùng chung
      // một bố cục; màu khác nhau không cứu được, người xem nhận ra qua bố cục và nền.
      ...hoaTietNen(bienCua((props as any).bien), accent) }}>
      {/* TIÊU ĐỀ */}
      <div style={{ position: "absolute", top: 40, left: 0, right: 0, textAlign: "center", zIndex: 6 }}>
        {/* 27/8 — BỎ PILL IN TÊN ĐỊNH DẠNG NỘI BỘ (THEN × NOW).
            Người xem không biết chữ đó nghĩa là gì, nhưng nó GOM mọi kênh dùng dạng này thành
            một cụm nhìn thấy được — đúng dấu vân tay "cùng một chủ" mà bộ nhận diện V4 vừa đi
            xoá khỏi ảnh đại diện và ảnh bìa. Để lại trên video thì công kia thành vô nghĩa.
            Và nó chiếm mất dải trên cùng, chỗ đáng ra để tiêu đề thở. */}
      </div>

      {/* CÁC CẶP */}
      {pairs.map((p, i) => (
        <Sequence key={i} from={starts[i]} durationInFrames={Math.round(pdur(p, pairSec) * fps)}>
          <TNPairView cosub={!!(subs && subs.length)} font={font} p={p} accent={accent} sec={pdur(p, pairSec)} />
        </Sequence>
      ))}

      {/* CHUYỂN CẢNH: panel vào = nhịp thường, chip biến đổi bung = nhịp mạnh. */}
      {sfx ? (
        <ChuyenCanh accent={accent} khoa={handle}
                    nhip={pairs.flatMap((p, i) => [
                      { at: starts[i], manh: 0.55 },
                      { at: starts[i] + Math.round(pdur(p, pairSec) * fps * 0.42), manh: 1 },
                    ])} />
      ) : null}

      {/* INTRO */}
      {f < introF && !hookStat ? (
        <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 42%, #EC489922, #08060a 70%)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", paddingBottom: 620 }}>
          <div style={{ fontSize: 140, transform: `scale(${introP})` }}>⏳</div>
        </AbsoluteFill>
      ) : null}

      <div style={{ position: "absolute", bottom: 46, left: 0, right: 0, textAlign: "center", color: "#ffffff5c", fontWeight: 700, fontSize: 24, textShadow: "0 1px 6px #0009", zIndex: 6 }}>{handle}</div>
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
      <Karaoke subs={subs} accent={accent} />
      <Bookend hookStat={hookStat} hookLabel={hookLabel} hookLine={hookLine} title={title} handle={handle} accent={accent} color={color}
               introSec={introSec} outroSec={outroSec} />
          <DongNguon nguon={source} />
    </AbsoluteFill>
  );
};
