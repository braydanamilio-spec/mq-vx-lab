import { AbsoluteFill, Sequence, Audio, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate, interpolateColors } from "remotion";
import { Karaoke } from "./Karaoke";
import { Bookend } from "./Bookend";
import { phong } from "./Phong";
import { SoChay, SO_DEU, DongNguon } from "./So";
import { bienCua, hoaTietNen } from "./Bien";
import { nenKenh } from "./Nen";
import { ChuyenCanh } from "./Chuyen";
import React, { useMemo } from "react";
import { geoAlbersUsa, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import states from "../public/geo/states-10m.json";

// KÊNH #2 MAPPED — choropleth bản đồ US "nóng dần" theo số liệu + pop TOP bang. Motif khác hẳn bar-race.
type Word = { t: number; d: number; w: string };
export type MapDatum = { state: string; value: number; disp?: string };  // disp = chuỗi hiển thị (vd "$74,580")
export type MappedProps = {
  title?: string; unit?: string; handle?: string; source?: string; color?: string; accent?: string;
  data: MapDatum[]; topN?: number; introSec?: number; bloomSec?: number; popSec?: number; outroSec?: number;
  hookStat?: string; hookLabel?: string; hookLine?: string;
  bg?: string; bg2?: string;
  font?: string;
  audio?: string; music?: string; subs?: Word[];
};

const FPS = 30;
const norm = (s: string) => s.trim().toLowerCase();

export const calcMapped = ({ props }: any) => {
  const p = props || {};
  const topN = Math.min(p.topN || 3, (p.data || []).length);
  const isec = p.introSec ?? 1.8, bloom = p.bloomSec ?? 2.4, pop = p.popSec ?? 1.6, tail = p.outroSec ?? 1.6;
  return { durationInFrames: Math.round((isec + bloom + topN * pop + tail) * FPS), fps: FPS };
};

// 27/8 — MÀU LẠNH CŨ (#16223e) GẦN NHƯ TRÙNG MÀU NỀN, nên bang giá trị thấp biến mất khỏi bản đồ:
// người xem thấy một mảng đen, tưởng chỗ đó không có dữ liệu. Đầu lạnh phải TÁCH KHỎI NỀN — nó
// vẫn là một giá trị có thật, chỉ là nhỏ.
const heat = (t: number, accent: string) => interpolateColors(Math.max(0, Math.min(1, t)), [0, 1], ["#2B3C63", accent]);

export const MappedShort: React.FC<MappedProps> = (props) => {
  const { font = "", hookStat = "", hookLabel = "", hookLine = "", bg = "", bg2 = "", title = "BY STATE", unit = "", handle = "@mappedusa", color = "#22D3EE", accent = "#22D3EE",
    data = [], topN = 3, introSec = 1.8, bloomSec = 2.4, popSec = 1.6, outroSec = 1.6, audio, music , subs = [] , source = "" } = props;
  const f = useCurrentFrame(); const { fps, width: W, height: H } = useVideoConfig();

  const { geo, pathGen, valById, maxV, ranked, hang, khungBanDo } = useMemo(() => {
    const g: any = feature(states as any, (states as any).objects.states);
    const proj = geoAlbersUsa().fitExtent([[60, 360], [W - 60, H - 620]], g);
    const m: Record<string, number> = {};
    for (const d of data) m[norm(d.state)] = d.value;
    // ── THANG MÀU THEO THỨ HẠNG, KHÔNG THEO GIÁ TRỊ/LỚN NHẤT (27/8) ────────────────────────
    // Xem khung thật kênh WHERE TO MOVE: bản đồ là một bóng đen phẳng, không đọc ra bang nào
    // hơn bang nào — trong khi dữ liệu 51 bang đều đủ và tên đều khớp geo.
    // Nguyên nhân là phép chuẩn hoá: `t = v / maxV`. Giá nhà Hawaii 833K, còn phần lớn bang
    // 250-350K -> gần như mọi bang rơi vào t≈0,3-0,4, tức CÙNG MỘT MÀU. Một giá trị ngoại lai
    // ở đầu trên đã nuốt trọn dải màu, 45 bang còn lại chen nhau trong 1/10 dải.
    // Đây là lý do bản đồ dữ liệu nghiêm túc dùng thang THEO THỨ HẠNG: xếp 51 bang rồi trải đều
    // vị trí của chúng lên dải màu. Bang thứ 1 đậm nhất, thứ 51 nhạt nhất, và MỌI bước ở giữa
    // đều nhìn thấy được — kể cả khi các con số sát nhau.
    const sap = [...data].filter((d) => typeof d.value === "number").sort((a, b) => a.value - b.value);
    const hang: Record<string, number> = {};
    sap.forEach((d, i) => { hang[norm(d.state)] = sap.length > 1 ? i / (sap.length - 1) : 1; });
    const mx = Math.max(1, ...data.map((d) => d.value));
    const rk = [...data].sort((a, b) => b.value - a.value).slice(0, topN);
    const pg = geoPath(proj);
    return { geo: g, pathGen: pg, valById: m, maxV: mx, ranked: rk, proj, hang,
             khungBanDo: pg.bounds(g) };
  }, [W, H, data, topN]);

  const introF = Math.round(introSec * fps);
  const bloomF = Math.round(bloomSec * fps);
  const bloomStart = introF;
  const bloom = interpolate(f, [bloomStart, bloomStart + bloomF], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const popStart = introF + bloomF;

  // centroid cho pin top-N
  const centroids = useMemo(() => {
    const byName: Record<string, any> = {};
    for (const ft of geo.features) byName[norm(ft.properties.name)] = ft;
    return ranked.map((d) => { const ft = byName[norm(d.state)]; return ft ? pathGen.centroid(ft) : [W / 2, H / 2]; });
  }, [geo, ranked, pathGen, W, H]);

  // NHỊP CHUYỂN CẢNH — lấy đúng các mốc pop đã có sẵn ở dưới, không bịa mốc mới: hình và tiếng
  // phải rơi vào CÙNG khoảnh khắc mà bảng xếp hạng đổi, nếu lệch thì xem còn rối hơn là im.
  // `manh`: #1 = 1 (tiếng nặng nhất), các hạng dưới nhẹ dần -> tai nghe ra thứ bậc.
  const nhip = React.useMemo(() => {
    const ra = [{ at: introF, manh: 0.55 }];   // bản đồ bắt đầu "nóng lên"
    for (let i = 0; i < ranked.length; i++) {
      const order = ranked.length - 1 - i;
      ra.push({ at: popStart + order * Math.round(popSec * fps), manh: i === 0 ? 1 : 0.6 });
    }
    return ra;
  }, [introF, popStart, popSec, fps, ranked.length]);

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
      <div style={{ position: "absolute", top: 96, left: 0, right: 0, textAlign: "center", padding: "0 60px" }}>
        {/* 27/8 — BỎ PILL IN TÊN ĐỊNH DẠNG NỘI BỘ (MAPPED · USA).
            Người xem không biết chữ đó nghĩa là gì, nhưng nó GOM mọi kênh dùng dạng này thành
            một cụm nhìn thấy được — đúng dấu vân tay "cùng một chủ" mà bộ nhận diện V4 vừa đi
            xoá khỏi ảnh đại diện và ảnh bìa. Để lại trên video thì công kia thành vô nghĩa.
            Và nó chiếm mất dải trên cùng, chỗ đáng ra để tiêu đề thở. */}
        {/* Tiêu đề lúc mở đầu do Bookend vẽ. Header ẩn đi trong quãng đó, nếu không sẽ có hai bản tiêu đề chồng nhau (lỗi 25/8). */}
        <div style={{ display: f < introF ? "none" : undefined, color: "#fff", fontWeight: 900, fontSize: 74, lineHeight: 1.02, marginTop: 20, textShadow: "0 4px 24px #000c", textWrap: "balance" as any }}>{title}</div>
        {/* 27/8 — `unit` cho dạng bản đồ thường là KÝ HIỆU chứ không phải cụm từ ("$", "%").
            In riêng nó một dòng thì trên khung hiện đúng một chữ "$" lơ lửng giữa trời — nhìn như
            phần tử bị sót lại chứ không như thiết kế. Ký hiệu đơn lẻ đã nằm sẵn trong con số phía
            dưới ($833,877), nên ở đây chỉ hiện khi nó là một cụm từ thật sự nói thêm điều gì. */}
        {unit && unit.trim().length > 2
          ? <div style={{ color: "#93a4c4", fontWeight: 700, fontSize: 34, marginTop: 8 }}>{unit}</div>
          : null}
      </div>

      {/* BẢN ĐỒ */}
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <filter id="mglow"><feGaussianBlur stdDeviation="7" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>
        {geo.features.map((ft: any, i: number) => {
          const v = valById[norm(ft.properties.name)];
          const t = v == null ? 0 : (hang[norm(ft.properties.name)] ?? 0) * bloom;
          const isTop = ranked.some((r) => norm(r.state) === norm(ft.properties.name));
          const topActive = isTop && f >= popStart;
          return <path key={i} d={pathGen(ft) || ""} fill={v == null ? "#0e1832" : heat(t, accent)}
            stroke={topActive ? "#fff" : "#0a1120"} strokeWidth={topActive ? 2.6 : 0.6}
            style={topActive ? { filter: "url(#mglow)" } : undefined} />;
        })}
      </svg>

      {/* CHÚ GIẢI THANG MÀU — 28/8.
          Hai thứ hỏng cùng một chỗ. ① Bản đồ tô 9 bang theo thứ hạng, 42 bang còn lại để màu
          "không có dữ liệu" (#0e1832) — mà màu đó nằm sát đầu lạnh của thang (#2B3C63), nên người
          xem đọc cả miền Đông nước Mỹ là "ít nhất" chứ không phải "ngoài phạm vi câu hỏi". Sai
          nghĩa, và sai về phía nguy hiểm: nó biến một câu đúng thành một khẳng định bịa.
          ② Màu đậm nhạt không kèm mốc thì không đọc ra LƯỢNG: người xem thấy California sáng hơn
          Montana nhưng không biết hơn gấp đôi hay gấp tám.
          Dải chú giải trả lời cả hai, và nó nằm đúng vào khoảng trống giữa bản đồ và bảng xếp hạng
          — chỗ trước nay bỏ không vì AlbersUsa rộng hơn cao nên luôn thừa bề cao. */}
      {(() => {
        const dsp = (d: any) => (d && (d.disp || String(d.value))) || "";
        const sap = [...data].filter((d) => typeof d.value === "number").sort((a, b) => a.value - b.value);
        if (sap.length < 3) return null;
        const y = Math.min(H - 620, (khungBanDo?.[1]?.[1] ?? 1100) + 30);
        return (
          <div style={{ position: "absolute", left: 0, right: 0, top: y, display: "flex",
                        justifyContent: "center", alignItems: "center", gap: 26, opacity: bloom }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ ...SO_DEU, color: "#93a4c4", fontWeight: 800, fontSize: 24 }}>{dsp(sap[0])}</div>
              <div style={{ width: 240, height: 14, borderRadius: 7,
                            background: `linear-gradient(90deg, ${heat(0, accent)}, ${heat(1, accent)})`,
                            boxShadow: "inset 0 0 0 1px #ffffff1f" }} />
              <div style={{ ...SO_DEU, color: "#fff", fontWeight: 900, fontSize: 24 }}>{dsp(sap[sap.length - 1])}</div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
              <div style={{ width: 22, height: 14, borderRadius: 4, background: "#0e1832",
                            boxShadow: "inset 0 0 0 1px #ffffff1f" }} />
              <div style={{ color: "#7c8db0", fontWeight: 700, fontSize: 21 }}>none</div>
            </div>
          </div>
        );
      })()}

      {/* PIN SỐ nhỏ trên map (không hộp chữ -> không chồng/tràn dù bang nhỏ sát nhau) */}
      {ranked.map((d, i) => {
        // dùng ranked.length (số mục THỰC SỰ hiển thị) chứ không phải topN prop: nếu data.length < topN
        // (vd chỉ có 1-2 bang), calcMapped() đã tính durationInFrames theo topN đã CLAMP xuống data.length,
        // nhưng topN prop ở đây vẫn giữ giá trị gốc (vd 3) -> order bị tính sai -> pin/hạng mục pop SAU KHI video đã hết.
        const order = ranked.length - 1 - i;
        const at = popStart + order * Math.round(popSec * fps);
        const s = spring({ frame: f - at, fps, config: { damping: 12, stiffness: 170 } });
        if (f < at) return null;
        const [cx, cy] = centroids[i];
        return (
          <div key={"pin" + i} style={{ position: "absolute", left: cx, top: cy, transform: `translate(-50%,-50%) scale(${0.4 + s * 0.6})`, opacity: s,
            width: 52, height: 52, borderRadius: "50%", background: i === 0 ? accent : "#0b1226", border: `3px solid ${accent}`,
            display: "flex", alignItems: "center", justifyContent: "center", color: i === 0 ? "#0a0c14" : "#fff",
            fontWeight: 900, fontSize: 28, boxShadow: `0 0 20px ${accent}, 0 6px 18px #000a` }}>{i + 1}</div>
        );
      })}

      {/* BẢNG XẾP HẠNG ở DƯỚI (vùng trống, chống chồng tuyệt đối) — #3->#1 pop, #1 nổi accent */}
      {/* 26/8 — băng chữ karaoke neo bottom 200 và cao ~2 dòng; bảng xếp hạng neo bottom 150
          nên chữ ĐÈ lên thanh #1/#2/#3 (thấy rõ ở khung 16s kênh QUAKE LOG). Có sub thì
          nhường chỗ, không sub thì giữ nguyên — cùng cách đã vá cho RankedShort. */}
      <div style={{ position: "absolute", left: 70, right: 70,
                    bottom: (subs && subs.length) ? 380 : 150,
                    display: "flex", flexDirection: "column", gap: 16 }}>
        {ranked.map((d, i) => {
          // dùng ranked.length (số mục THỰC SỰ hiển thị) chứ không phải topN prop: nếu data.length < topN
          // (vd chỉ có 1-2 bang), calcMapped() đã tính durationInFrames theo topN đã CLAMP xuống data.length,
          // nhưng topN prop ở đây vẫn giữ giá trị gốc (vd 3) -> order bị tính sai -> pin/hạng mục pop SAU KHI video đã hết.
          const order = ranked.length - 1 - i;
          const at = popStart + order * Math.round(popSec * fps);
          const s = spring({ frame: f - at, fps, config: { damping: 13, stiffness: 150 } });
          const lead = i === 0;
          return (
            <div key={"row" + i} style={{ order: i, transform: `translateX(${(1 - s) * -40}px)`, opacity: s,
              display: "flex", alignItems: "center", gap: 18, background: lead ? accent : "#0e1832e6",
              border: `2px solid ${lead ? accent : "#22345e"}`, borderRadius: 18, padding: lead ? "18px 26px" : "14px 24px",
              boxShadow: lead ? `0 10px 34px ${accent}66` : "0 6px 18px #0006" }}>
              <div style={{ fontWeight: 900, fontSize: lead ? 46 : 38, color: lead ? "#0a0c14" : accent, minWidth: 62 }}>#{i + 1}</div>
              <div style={{ flex: 1, fontWeight: 900, fontSize: lead ? 46 : 38, color: lead ? "#0a0c14" : "#fff", letterSpacing: -0.5 }}>{d.state.toUpperCase()}</div>
              <div style={{ fontWeight: 900, fontSize: lead ? 46 : 40, color: lead ? "#0a0c14" : "#fff", fontVariantNumeric: "tabular-nums" }}>
                {/* 27/8 — số trong THÂN video cũng phải chạy, không chỉ số dẫn ở hook. Cùng lý do: con số đang lớn dần giữ mắt, con số hiện sẵn thì không. */}
                <SoChay s={String(d.disp || d.value.toLocaleString())} tuFrame={popStart} giay={0.8} />
              </div>
            </div>
          );
        })}
      </div>

      {/* 28/8 — DÒNG NGUỒN. `DongNguon` được NHẬP ở đầu tệp mà chưa bao giờ được VẼ, nên 4 kênh
          dạng bản đồ ra video không ghi nguồn, trong khi 5 dạng kia đều có. Người xem không có
          cách nào kiểm con số, và mình mất luôn bằng chứng "dữ liệu công khai tra được" trước
          chính sách nội dung hàng loạt của YouTube.
          Đặt trên @handle 42px để hai dòng không chạm nhau. */}
      <DongNguon nguon={source} day={96} />
      <div style={{ position: "absolute", bottom: 54, left: 0, right: 0, textAlign: "center", color: "#ffffff5c", fontWeight: 700, fontSize: 24, textShadow: "0 1px 6px #0009" }}>{handle}</div>
      {audio ? <Audio src={staticFile(audio)} /> : null}
      {music ? <Audio src={staticFile(music)} volume={0.14} /> : null}
      <ChuyenCanh nhip={nhip} accent={accent} khoa={handle} />
      <Karaoke subs={subs} accent={accent} />
      <Bookend hookStat={hookStat} hookLabel={hookLabel} hookLine={hookLine} title={title} handle={handle} accent={accent} color={color}
               introSec={introSec} outroSec={outroSec} />
    </AbsoluteFill>
  );
};
