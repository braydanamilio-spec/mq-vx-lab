import React from "react";
import { AbsoluteFill, Sequence, Audio, staticFile, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { RankedShort, calcRanked } from "./RankedShort";
import { ScaledShort, calcScaled } from "./ScaledShort";
import { MappedShort, calcMapped } from "./MappedShort";
import { LongshotShort, calcLongshot } from "./LongshotShort";
import { ThenNowShort, calcThenNow } from "./ThenNowShort";
import { BarChartRace, calcRace } from "./BarChartRace";
import { Cinematic, calcCinematic } from "./Cinematic";
import { phong } from "./Phong";

// LONG KHỔ NGANG CHO 5 DẠNG GEN-2 (26/8/2026)
//
// Vì sao có tệp này. Đo thật một bộ vừa render: `chay_bo` dựng từng chương bằng composition khổ
// DỌC rồi `ffmpeg -c copy` nối lại và gọi đó là "long":
//     th2long_recallplate.mp4 : 1080×1920 , 103,98s
// YouTube xếp video dọc ≤3 phút vào Shorts ⇒ bộ "1 long + 3 short" thực chất là BỐN SHORT. Sổ sách
// vẫn ghi `type: "long"`, luật 1:3 vẫn đếm đủ, khâu đăng vẫn xếp số đúng thứ tự — mọi con số đều
// xanh mà sản phẩm sai. Đây là dạng lỗi đắt nhất: không có gì đỏ để mà thấy.
//
// Anh chốt: long phải 16:9 thật; còn short KHÔNG phải cắt từ long ra mà viết + dựng lại riêng cho
// 9:16 có hook. Nên chỗ này chỉ lo LONG. Short vẫn đi đường `*Short` cũ, không đụng tới.
//
// Cách ghép theo đúng tiền lệ `RaceLong` đã dùng: mỗi chương là một `<Sequence>` mang tiếng nói của
// chính nó, cộng dồn mốc bắt đầu. GIỮ NGUYÊN intro/outro của từng chương thay vì ép về 0 — thời
// lượng chương do `calc*` tính từ introSec/itemSec/outroSec, mà tiếng nói đã thu theo đúng nhịp đó;
// cắt intro đi là lệch tiếng khỏi hình, đổi lấy một chút gọn gàng bằng một lỗi nặng hơn nhiều.

export type ChuongLong = { dang: string; props: any };
export type Gen2LongProps = {
  chuong?: ChuongLong[];
  handle?: string; accent?: string; color?: string; font?: string; music?: string;
};

const BO: Record<string, { comp: React.FC<any>; calc: (a: any) => { durationInFrames: number } }> = {
  ranked:   { comp: RankedShort as any,    calc: calcRanked },
  scaled:   { comp: ScaledShort as any,    calc: calcScaled },
  mapped:   { comp: MappedShort as any,    calc: calcMapped },
  longshot: { comp: LongshotShort as any,  calc: calcLongshot },
  thennow:  { comp: ThenNowShort as any,   calc: calcThenNow },
  // `race` và `cinematic` KHÔNG cần bố cục ngang mới: `BarChartRace` và `Cinematic` vốn đã được
  // dùng ở CẢ hai khổ trong Root.tsx (`Race` 1920×1080 và `RaceShort` 1080×1920 cùng một
  // component), tức chúng tự co theo khung từ trước. Ở đây chỉ là đấu dây.
  race:      { comp: BarChartRace as any,  calc: calcRace },
  cinematic: { comp: Cinematic as any,     calc: calcCinematic },
};

const daiChuong = (c: ChuongLong): number => {
  const b = BO[c?.dang];
  if (!b) return 0;
  try { return Math.max(1, b.calc({ props: c.props || {} }).durationInFrames); } catch { return 0; }
};

export const calcGen2Long = ({ props }: { props: Gen2LongProps }) => {
  const tong = (props.chuong || []).reduce((a, c) => a + daiChuong(c), 0);
  return { durationInFrames: Math.max(1, tong), fps: 30 };
};

/** Thanh tiến độ chương — thứ duy nhất vẽ ĐÈ lên toàn bộ long.
 *  Neo sát mép trên, cao 6px: không đụng vùng tiêu đề (mốc trên của khổ ngang là 44) và không
 *  đụng băng phụ đề (neo đáy). Có nó thì người xem biết video còn dài bao nhiêu — thiếu nó, long
 *  nhiều chương trông như một chuỗi short dán liền. */
const ThanhChuong: React.FC<{ moc: number[]; tong: number; accent: string }> = ({ moc, tong, accent }) => {
  const f = useCurrentFrame();
  const { width } = useVideoConfig();
  const p = interpolate(f, [0, Math.max(1, tong)], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 6, zIndex: 50, background: "#ffffff14" }}>
      <div style={{ height: "100%", width: `${p * 100}%`, background: accent, boxShadow: `0 0 14px ${accent}88` }} />
      {moc.slice(1).map((m, i) => (
        <div key={i} style={{ position: "absolute", top: 0, bottom: 0, left: (m / Math.max(1, tong)) * width, width: 2, background: "#0a0c14" }} />
      ))}
    </div>
  );
};

export const Gen2Long: React.FC<Gen2LongProps> = (props) => {
  const { chuong = [], handle = "", accent = "#7C5CFF", font = "", music } = props;
  const dung = chuong.filter((c) => BO[c?.dang]);
  const moc: number[] = []; let off = 0;
  const seg = dung.map((c, i) => {
    const d = daiChuong(c);
    moc.push(off);
    const from = off; off += d;
    return { c, i, from, d };
  });
  return (
    <AbsoluteFill style={{ background: "#07060f", fontFamily: phong(font) }}>
      {music ? <Audio src={staticFile(music)} volume={0.05} /> : null}
      {seg.map(({ c, i, from, d }) => {
        const C = BO[c.dang].comp;
        return (
          <Sequence key={i} from={from} durationInFrames={d}>
            <C {...c.props} handle={c.props?.handle || handle} music={undefined} />
          </Sequence>
        );
      })}
      <ThanhChuong moc={moc} tong={off} accent={accent} />
    </AbsoluteFill>
  );
};
