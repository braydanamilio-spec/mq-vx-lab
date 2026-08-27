import { AbsoluteFill, Sequence, Audio, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { Karaoke } from "./Karaoke";
import { Bookend } from "./Bookend";
import { phong } from "./Phong";
import { SoChay, SO_DEU, DongNguon } from "./So";
import { bienCua, hoaTietNen } from "./Bien";
import { nenKenh } from "./Nen";
import { ChuyenCanh } from "./Chuyen";

/** Ảnh KHÔNG được phép giết cả bản render.
 *  Hình do AI vẽ có thể hụt (CF chặn prompt, hết hạn mức, tệp ghi dở). `<Img>` của Remotion mà
 *  tải hụt là ném lỗi và mất trắng video — trong khi thứ mất đi chỉ là một cái chóp trang trí.
 *  Hụt thì ẩn đi, cột số liệu vẫn nguyên vẹn. */
const AnhAnToan: React.FC<{ src: string; style?: React.CSSProperties }> = ({ src, style }) => {
  const [hong, setHong] = React.useState(false);
  if (hong) return null;
  return <Img src={src} style={style} onError={() => setHong(true)} />;
};
import React from "react";

// KÊNH #4 SCALED — so sánh KÍCH THƯỚC vật lý thật, vẽ ĐÚNG TỈ LỆ cạnh nhau. Motif riêng.
type Word = { t: number; d: number; w: string };
export type ScaleItem = { name: string; emoji?: string; value: number; disp?: string; dur?: number };
export type ScaledProps = {
  title?: string; subtitle?: string; handle?: string; source?: string; color?: string; accent?: string;
  items: ScaleItem[]; introSec?: number; itemSec?: number; outroSec?: number;
  hookStat?: string; hookLabel?: string; hookLine?: string;
  bg?: string; bg2?: string;
  font?: string;
  audio?: string; music?: string; subs?: Word[]; sfx?: boolean;
};

const FPS = 30;
const idur = (it: ScaleItem, s: number) => (it.dur && it.dur > 0 ? it.dur : s);

export const calcScaled = ({ props }: any) => {
  const its: ScaleItem[] = props.items || [];
  const isec = props.introSec ?? 1.8, isc = props.itemSec ?? 2.0, tail = props.outroSec ?? 1.6;
  const total = its.reduce((a, it) => a + idur(it, isc), 0);
  return { durationInFrames: Math.round((isec + total + tail) * FPS), fps: FPS };
};

export const ScaledShort: React.FC<ScaledProps> = (props) => {
  const { font = "", hookStat = "", hookLabel = "", hookLine = "", bg = "", bg2 = "", title = "SIZE COMPARISON", subtitle = "", source = "", handle = "@scaledusa", color = "#2FA84F", accent = "#2FA84F",
    items = [], introSec = 1.8, itemSec = 2.0, outroSec = 1.6, audio, music, sfx = true , subs = [] } = props;
  const f = useCurrentFrame(); const { fps, width: W, height: H } = useVideoConfig();

  // LAYOUT tính sẵn: cao emoji ∝ giá trị thật; cột ≥ LABEL_MIN (nhãn luôn đủ chỗ) — chỉ co PHẦN kích thước khi tràn.
  // 26/8 — NHƯỜNG CHỖ CHO BĂNG PHỤ ĐỀ. Đo trên khung thật: nhãn các mục bắt đầu ở GROUND
  // (H-430 = 1490) và dài 2-3 dòng nên chạm tới ~1640, trong khi băng chữ karaoke nằm ở
  // bottom 200 tức mép trên ~1608 ⇒ chữ đè chữ, cả hai đều không đọc được (thấy rõ ở
  // CALORIE SHOCK: sub "Sabatasso'S Pepperoni" đè lên đúng cụm nhãn).
  // Có sub thì hạ trần: nhãn kết thúc trên băng chữ, không tràn vào.
  const COSUB = !!(subs && subs.length);
  const GROUND = H - (COSUB ? 560 : 430), TOPLIMIT = 470, PAD = 30, USABLE = W - 100, LABEL_MIN = 178;
  const maxH = Math.min(GROUND - TOPLIMIT, 600), floor = 46;   // cạp cao emoji lớn nhất -> hệ số co không giết cột nhãn
  const maxV = Math.max(1, ...items.map((d) => d.value));
  let hs = items.map((d) => floor + (d.value / maxV) * (maxH - floor));
  let cols = hs.map((h) => Math.max(LABEL_MIN, h + PAD * 2));
  let totalW = cols.reduce((a, b) => a + b, 0);
  if (totalW > USABLE) {
    const fixed = LABEL_MIN * items.length;
    if (fixed >= USABLE) { const k = USABLE / totalW; cols = cols.map((c) => c * k); }     // quá nhiều item -> co đều
    else { const k2 = (USABLE - fixed) / (totalW - fixed); cols = cols.map((c) => LABEL_MIN + (c - LABEL_MIN) * k2); }
    totalW = cols.reduce((a, b) => a + b, 0);
  }
  // 27/8 — DÒNG NÀY LÀ THỨ XOÁ SẠCH TỈ LỆ.
  // Emoji gần vuông nên `fontSize = h` cũng là bề ngang; kẹp `min(h, cols[i]-20)` để nó vừa cột
  // đồng nghĩa với việc CHIỀU CAO BỊ BỀ NGANG QUYẾT ĐỊNH. Đo trên khung thật CALORIE SHOCK:
  // 704 cal và 375 cal ra hai miếng pizza gần bằng nhau — dạng tên là "SCALED" mà không scale gì.
  // Nay vẽ CỘT TỈ LỆ: chiều cao chỉ bị giới hạn bởi chiều cao khung, còn bề ngang là chuyện
  // riêng của cột. Emoji tụt xuống làm CHÓP nhỏ trên đầu cột — vẫn giữ được chất chủ đề của
  // kênh, nhưng thứ mang dữ liệu là hình khối vẽ ra, không phải một ký tự phông chữ.
  hs = hs.map((h) => Math.max(floor, Math.min(h, maxH)));
  const wCot = cols.map((c) => Math.max(52, Math.min(c - 46, 132)));
  const startX = (W - totalW) / 2;
  const xs: number[] = []; let cur = startX;
  for (const c of cols) { xs.push(cur + c / 2); cur += c; }                 // tâm mỗi cột

  const introF = Math.round(introSec * fps);
  const starts: number[] = []; let acc = introF;
  for (const it of items) { starts.push(acc); acc += Math.round(idur(it, itemSec) * fps); }
  const introP = spring({ frame: f, fps, config: { damping: 12, stiffness: 140 } });

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
      <div style={{ position: "absolute", top: 96, left: 0, right: 0, textAlign: "center", padding: "0 50px" }}>
        {/* 27/8 — BỎ PILL IN TÊN ĐỊNH DẠNG NỘI BỘ (SCALED).
            Người xem không biết chữ đó nghĩa là gì, nhưng nó GOM mọi kênh dùng dạng này thành
            một cụm nhìn thấy được — đúng dấu vân tay "cùng một chủ" mà bộ nhận diện V4 vừa đi
            xoá khỏi ảnh đại diện và ảnh bìa. Để lại trên video thì công kia thành vô nghĩa.
            Và nó chiếm mất dải trên cùng, chỗ đáng ra để tiêu đề thở. */}
        {/* Tiêu đề lúc mở đầu do Bookend vẽ. Header ẩn đi trong quãng đó, nếu không sẽ có hai bản tiêu đề chồng nhau (lỗi 25/8). */}
        <div style={{ display: f < introF ? "none" : undefined, color: "#fff", fontWeight: 900, fontSize: 70, lineHeight: 1.02, marginTop: 18, textShadow: "0 4px 24px #000c", textWrap: "balance" as any }}>{title}</div>
        {subtitle ? <div style={{ color: "#9fc4ac", fontWeight: 700, fontSize: 32, marginTop: 8 }}>{subtitle}</div> : null}
      </div>

      {/* ĐƯỜNG NỀN (mặt đất) */}
      <div style={{ position: "absolute", top: GROUND, left: 40, right: 40, height: 4, background: `linear-gradient(90deg, #0000, ${accent}88, #0000)` }} />

      {/* CÁC VẬT — emoji scale đúng tỉ lệ, đứng trên nền, hiện lần lượt */}
      {items.map((it, i) => {
        const s = spring({ frame: f - starts[i], fps, config: { damping: 13, stiffness: 150 } });
        if (f < starts[i]) return null;
        const h = hs[i]; const biggest = it.value === maxV;
        return (
          <div key={i} style={{ position: "absolute", left: xs[i], top: GROUND, transform: "translateX(-50%)", textAlign: "center" }}>
            {/* CỘT TỈ LỆ mọc từ nền lên — chiều cao ∝ giá trị thật, không bị bề ngang kẹp */}
            <div style={{ position: "absolute", left: "50%", bottom: 0,
              transform: `translateX(-50%) scaleY(${s})`, transformOrigin: "bottom",
              width: wCot[i], height: h, borderRadius: "14px 14px 6px 6px",
              background: biggest
                ? `linear-gradient(180deg, ${accent} 0%, ${accent}c4 55%, ${accent}5c 100%)`
                : `linear-gradient(180deg, ${accent}9e 0%, ${accent}66 55%, ${accent}2e 100%)`,
              border: `2px solid ${accent}${biggest ? "" : "77"}`,
              boxShadow: biggest ? `0 0 34px ${accent}77` : "0 6px 16px #0007" }}>
              {/* GIÁ TRỊ nằm trên chính cột của nó — người xem không phải đưa mắt đi tìm */}
              {it.disp ? (
                <div style={{ position: "absolute", left: "50%", top: 12, transform: `translateX(-50%) scaleY(${1 / Math.max(0.01, s)})`,
                  color: biggest ? "#08111e" : "#fff", fontWeight: 900,
                  fontSize: Math.max(20, Math.min(34, wCot[i] / 3.4)), whiteSpace: "nowrap",
                  textShadow: biggest ? "none" : "0 2px 10px #000a" }}>
                  {/* 27/8 — số trong THÂN video cũng phải chạy, không chỉ số dẫn ở hook. Cùng lý do: con số đang lớn dần giữ mắt, con số hiện sẵn thì không. */}
                  <SoChay s={String(it.disp || "")} tuFrame={starts[i]} giay={0.85} />
                </div>
              ) : null}
            </div>
            {/* CHÓP TRÊN ĐỈNH CỘT — ưu tiên HÌNH THẬT do Cloudflare FLUX vẽ theo gu riêng của kênh
                (xem `the_he_2._ve_vat`). Emoji chỉ còn là đường lui khi vẽ hụt: nó hiện khác nhau
                tuỳ nền tảng và nhìn rẻ, nên không nên là lựa chọn đầu. */}
            {it.img ? (
              <div style={{ position: "absolute", left: "50%", bottom: h * s + 10, transform: "translateX(-50%)",
                opacity: s, width: Math.min(wCot[i] + 26, 150), height: Math.min(wCot[i] + 26, 150),
                borderRadius: 18, overflow: "hidden",
                border: `3px solid ${biggest ? accent : accent + "88"}`,
                boxShadow: biggest ? `0 0 26px ${accent}88` : "0 6px 16px #0009" }}>
                <AnhAnToan src={staticFile(it.img)}
                           style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              </div>
            ) : it.emoji ? (
              <div style={{ position: "absolute", left: "50%", bottom: h * s + 8, transform: "translateX(-50%)",
                fontSize: 52, opacity: s, lineHeight: 1,
                filter: biggest ? `drop-shadow(0 0 18px ${accent})` : "drop-shadow(0 4px 10px #0008)" }}>{it.emoji}</div>
            ) : null}
            {/* nhãn dưới nền — bó trong bề rộng cột, tự xuống dòng -> không chồng */}
            <div style={{ position: "absolute", top: 18, left: "50%", transform: "translateX(-50%)", opacity: s, width: cols[i] - 12 }}>
              {/* TỐI ĐA 2 DÒNG. Trước đây để xuống dòng tự do: tên dài ("Vicolo Roasted Mushroom
                  Pizza") thành 3-4 dòng, đâm thẳng vào nhãn cột bên cạnh và vào băng phụ đề.
                  Cỡ chữ co theo bề rộng cột thật, không để một cỡ cứng cho mọi số lượng mục. */}
              <div style={{ color: "#fff", fontWeight: 900, lineHeight: 1.05,
                fontSize: Math.max(19, Math.min(32, Math.round((cols[i] - 12) / 5.6))),
                overflowWrap: "break-word", whiteSpace: "normal",
                display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical",
                overflow: "hidden" } as React.CSSProperties}>{it.name}</div>
              {/* 27/8 — GIÁ TRỊ ĐÃ NẰM TRÊN CHÍNH CỘT. In lại ở đây thì mỗi mục hiện "704 cal"
                  hai lần cách nhau vài chục pixel — mắt phải xử lý hai lần cùng một thông tin,
                  và khung vốn đã chật lại chật thêm. Chỉ giữ khi cột quá thấp để chứa chữ. */}
              {h < 92 ? (
                <div style={{ display: "inline-block", marginTop: 6, background: biggest ? accent : "#132a1e", color: biggest ? "#0a0c14" : "#eafff2",
                  border: `1.5px solid ${accent}`, fontWeight: 900, fontSize: 26, padding: "4px 14px", borderRadius: 12, whiteSpace: "nowrap" }}>{it.disp || it.value.toLocaleString()}</div>
              ) : null}
            </div>
          </div>
        );
      })}

      {/* INTRO overlay */}
      {f < introF && !hookStat ? (
        <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 42%, #2FA84F22, #060b08 70%)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", paddingBottom: 620 }}>
          <div style={{ fontSize: 150, transform: `scale(${introP})` }}>📏</div>
        </AbsoluteFill>
      ) : null}

      {/* CHUYỂN CẢNH — mục lớn nhất là nhịp mạnh. Mức âm do Chuyen.MUC_AM quyết, không viết cứng. */}
      {sfx ? (
        <ChuyenCanh accent={accent} khoa={handle}
                    nhip={items.map((it, i) => ({ at: starts[i], manh: it.value === maxV ? 1 : 0.6 }))} />
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
