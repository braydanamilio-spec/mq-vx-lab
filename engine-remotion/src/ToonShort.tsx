/**
 * ToonShort — skit hoạt hình 2 nhân vật (BALD & BANDIT / HANKTOWN), format 22/8:
 * 3-5 KHUNG ẢNH TĨNH của cùng một cảnh (FLUX vẽ, đổi biểu cảm + 1 khung cận) chuyển theo
 * NHỊP THOẠI + zoom nhẹ, title card đỉnh (đè luôn vùng chữ giả FLUX hay tự chế), phụ đề
 * từng câu ở đáy theo màu nhân vật, whoosh khi đổi khung, nhạc nền nhỏ.
 *
 * Props (python make_toon dựng sẵn, mọi file nằm public/{slug}/):
 *   slug, title, color (accent kênh), name (tên kênh),
 *   frames: [{img, from, dur}]            — khung hình theo frame 30fps
 *   lines:  [{audio, text, who, from, dur}] — mỗi câu thoại 1 file mp3 + phụ đề
 *   music?: đường dẫn nhạc nền (staticFile), watermark?: logo nhỏ góc
 */
import { AbsoluteFill, Audio, Img, Sequence, staticFile, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import React from "react";

const FB_IMG = staticFile("img/_fallback.jpg");
const SafeImg: React.FC<{ src: string; style?: React.CSSProperties }> = ({ src, style }) => {
  const [s, setS] = React.useState(src);
  return <Img src={s} style={style} onError={() => setS(FB_IMG)} pauseWhenLoading />;
};

type Frame = { img: string; from: number; dur: number };
type Word = { w: string; f: number };   // f = frame bắt đầu TƯƠNG ĐỐI trong câu (karaoke)
type Line = { audio: string; text: string; who: string; from: number; dur: number; words?: Word[];
              punch?: boolean; stat?: { num: string; cap?: string } };   // stat = thẻ số liệu động (23/8)

type Chapter = { text: string; from: number; dur: number };

export const ToonShort: React.FC<{
  slug: string; title: string; color?: string; name?: string;
  frames: Frame[]; lines: Line[]; music?: string; whoColors?: Record<string, string>;
  chapters?: Chapter[];   // LONG (tuyển tập skit): title card đổi theo skit đang chiếu
}> = ({ slug, title, color = "#E4562B", name = "", frames = [], lines = [], music = "", whoColors = {}, chapters = [] }) => {
  const f = useCurrentFrame();
  const { durationInFrames: total, width: vw, height: vh } = useVideoConfig();
  const isVertical = vh > vw;
  const ci = (x: number, a: number, b: number, c: number, d: number) =>
    interpolate(x, [a, b], [c, d], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const cur = lines.find(l => f >= l.from && f < l.from + l.dur);
  // ── NẤC 2 (23/8): "CON RỐI GIẤY" — nhân vật nhún/nghiêng theo nhịp thoại thay vì đứng chết ──
  // (a) IMPACT: mỗi câu mới bật ra 1 cú nảy nhẹ tắt dần trong ~10 frame — mắt đọc là "đổi lượt nói";
  // (b) BOB: nhún dọc theo TỪNG TỪ (dùng luôn mốc karaoke) -> cảm giác đang nói, biên độ nhỏ để không nôn;
  // (c) TILT: nghiêng nhẹ, hướng ngược nhau theo nhân vật A/B -> hai bên "đối đáp" thấy rõ.
  const relLine = cur ? f - cur.from : 0;
  // 23/8 (user: "đừng rung rung, không hợp"): format PHÂN TÍCH cần điềm tĩnh, sang trọng —
  // BỎ HẲN nhún/nghiêng/nảy theo nhịp thoại (thứ hợp skit hài). Chỉ giữ 1 nhịp lướt CỰC NHẸ khi
  // đổi câu để mắt biết có chuyển ý, và toàn bộ chuyển động còn lại là ken-burns trôi đều.
  const impact = cur ? Math.max(0, 1 - relLine / 14) : 0;
  const bob = 0;
  const tilt = 0;
  // ── NẤC 3: câu CHỐT -> rung máy + zoom giật (biên độ tắt dần), đạo cụ emoji bay vào ──
  // Câu chốt: KHÔNG rung máy nữa — chỉ khép vignette + nhích zoom rất nhẹ (xem khối camera).
  const punchOn = !!(cur && cur.punch);
  const shake = punchOn ? Math.max(0, 1 - relLine / 20) : 0;   // chỉ còn dùng cho vignette + zoom
  const shX = 0;
  const shY = 0;
  // 23/8 (user: "kết thúc bị khung đen"): LỚP ĐÁY luôn giữ ảnh — khi audio còn chạy mà chuỗi
  // Sequence khung đã hết, nền trước đây tụt về đen. Giờ luôn có ảnh hiện tại/gần nhất phía sau.
  const baseImg = (frames.filter(x => f >= x.from).slice(-1)[0] || frames[0] || { img: "" }).img;
  return (
    <AbsoluteFill style={{ background: "#0e0e12", fontFamily: "Inter, Helvetica, Arial, sans-serif" }}>
      {baseImg && (
        <AbsoluteFill>
          <SafeImg src={staticFile(`${slug}/${baseImg}`)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        </AbsoluteFill>
      )}
      {frames.map((fr, i) => {
        const rel = f - fr.from;
        const p = Math.min(1, Math.max(0, rel / Math.max(1, fr.dur)));
        // CAMERA SỐNG (22/8): đảo hướng theo khung — chẵn zoom-in, lẻ zoom-out nhẹ; kèm trôi ngang
        // xen kẽ trái/phải 0.8% -> mỗi lần cắt có "hơi máy quay" khác nhau, hết cảm giác lặp.
        const zoomIn = i % 2 === 0;
        const zoom = (zoomIn ? 1.02 + 0.04 * p : 1.06 - 0.04 * p) + 0.008 * impact + 0.012 * shake;   // nhích rất nhẹ, không giật
        const drift = (i % 4 < 2 ? 1 : -1) * 0.8 * p;
        return (
          <Sequence key={i} from={fr.from} durationInFrames={fr.dur}>
            <AbsoluteFill style={{
              transform: `scale(${zoom}) translateX(${drift + shX}%) translateY(${bob + shY}%) rotate(${tilt}deg)`,
              transformOrigin: "50% 55%",
            }}>
              <SafeImg src={staticFile(`${slug}/${fr.img}`)}
                style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            </AbsoluteFill>
            {i > 0 && <Audio src={staticFile("sfx/whoosh.mp3")} volume={0.35} />}
          </Sequence>
        );
      })}
      {/* BANNER MỞ ĐẦU (23/8 — user: "text to bự như banner trên nền footage"): khối chữ CỠ LỚN
          trên dải màu thương hiệu, đè lên ảnh mở đầu, bung ra rồi tan sau ~2.8s. Long: chớp lại
          ngắn ở mỗi chương. Đây là cú hook thị giác của 2 giây đầu. */}
      {(() => {
        const ch = chapters.find(c => f >= c.from && f < c.from + 70);
        if (!(f < 84 || ch)) return null;
        const rel = ch ? f - ch.from : f;
        const inP = Math.min(1, rel / 12);
        const outP = Math.min(1, Math.max(0, (rel - 62) / 20));
        const op = inP * (1 - outP);
        const txt = ch ? ch.text : title;
        const slide = (1 - inP) * 42;
        return (
          <AbsoluteFill style={{ pointerEvents: "none", opacity: op }}>
            <AbsoluteFill style={{ background: "rgba(8,8,12,.52)" }} />
            <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "0 56px" }}>
              <div style={{ width: "100%", maxWidth: 1000, transform: `translateY(${slide}px)` }}>
                <div style={{
                  display: "inline-block", background: color, color: "#fff",
                  fontSize: 30, fontWeight: 900, letterSpacing: 3, padding: "10px 20px",
                  marginBottom: 20, transform: `scaleX(${inP})`, transformOrigin: "left center",
                }}>{(name || "").toUpperCase()}</div>
                <div style={{
                  color: "#fff", fontSize: 92, fontWeight: 900, lineHeight: 1.04, letterSpacing: -2,
                  textShadow: "0 6px 30px rgba(0,0,0,.6)", textTransform: "uppercase",
                }}>{txt}</div>
                <div style={{
                  height: 10, background: color, marginTop: 26, borderRadius: 5,
                  transform: `scaleX(${inP})`, transformOrigin: "left center",
                }} />
              </div>
            </AbsoluteFill>
          </AbsoluteFill>
        );
      })()}
      {/* PHỤ ĐỀ (bản 23/8 — user: "sub hơi dài, chưa đẹp"): CHIA CỤM ~5 TỪ theo mốc karaoke,
          mỗi lúc chỉ hiện cụm đang đọc -> mắt đọc kịp, không phải nuốt cả câu dài. Bỏ hộp bo viền
          thô, thay bằng chữ dày có viền tối + dải mờ đáy: sạch, chuẩn caption chuyên nghiệp. */}
      {cur && (() => {
        const CH = 5;
        const ws = (cur.words && cur.words.length)
          ? cur.words
          : cur.text.split(/\s+/).filter(Boolean).map((w, k, arr) => ({ w, f: Math.round((cur.dur * 0.9) * k / Math.max(1, arr.length)) }));
        const groups = [];
        for (let k = 0; k < ws.length; k += CH) groups.push(ws.slice(k, k + CH));
        const rel = f - cur.from;
        let gi = groups.findIndex((g, k) => {
          const start = g[0].f;
          const next = groups[k + 1];
          return rel >= start && (!next || rel < next[0].f);
        });
        if (gi < 0) gi = 0;
        const g = groups[gi] || [];
        const spoken = (w) => rel >= w.f;
        return (
          <AbsoluteFill style={{ pointerEvents: "none" }}>
            <AbsoluteFill style={{
              background: "linear-gradient(0deg, rgba(8,8,12,.72) 0%, rgba(8,8,12,.30) 26%, rgba(8,8,12,0) 46%)",
            }} />
            <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center",
              // 23/8: LỀ AN TOÀN — short 9:16 nâng lên 330px vì TikTok/Reels che đáy bằng caption +
              // nút chia sẻ; long 16:9 giữ 150px (không có UI che).
              paddingBottom: isVertical ? 330 : 150 }}>
              <div style={{
                maxWidth: 900, textAlign: "center", fontSize: 58, fontWeight: 900, lineHeight: 1.18,
                letterSpacing: -0.4, textShadow: "0 3px 12px rgba(0,0,0,.75), 0 0 2px rgba(0,0,0,.9)",
              }}>{g.map((w, wi) => (
                <span key={wi} style={{
                  color: spoken(w) ? "#fff" : "rgba(255,255,255,.42)",
                  marginRight: 14, display: "inline-block",
                  transform: spoken(w) ? "translateY(-1px)" : "none",
                }}>{w.w}</span>
              ))}</div>
            </AbsoluteFill>
          </AbsoluteFill>
        );
      })()}
      {/* NẤC 3 (bản 23/8 — user: "đừng rẻ tiền"): ĐẠO CỤ EMOJI BAY VÀO ĐÃ BỎ HẲN.
          Câu chốt chỉ nhấn bằng NGÔN NGỮ ĐIỆN ẢNH: cú zoom giật + rung máy tắt dần (xử lý ở khối
          camera phía trên) + tối 4 góc (vignette) khép nhẹ để mắt dồn vào giữa khung — sang, không
          làm bẩn khung hình, hợp cả kênh hài lẫn kênh sepia cổ điển. */}
      {punchOn && (
        <AbsoluteFill style={{
          pointerEvents: "none",
          background: `radial-gradient(ellipse at 50% 52%, rgba(0,0,0,0) 52%, rgba(0,0,0,${0.34 * shake}) 100%)`,
        }} />
      )}
      {/* THẺ SỐ LIỆU (23/8 — user: "kết hợp chart/biểu đồ nếu phù hợp"): CHỈ hiện khi câu đang đọc
          có con số thật. Số bung lớn + thanh chỉ báo chạy ngang, nằm góc trên phải để không đè
          phụ đề. Không có số thì không hiện — tránh nhồi hiệu ứng vô nghĩa. */}
      {cur && cur.stat && (() => {
        const rel2 = f - cur.from;
        const p = Math.min(1, rel2 / 14);
        const fade = Math.min(1, Math.max(0, (cur.dur - rel2) / 12)) * Math.min(1, rel2 / 6);
        const pop = 0.82 + 0.18 * Math.min(1, rel2 / 9) + 0.03 * Math.sin(Math.min(p, 1) * Math.PI);
        return (
          <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-end", padding: "150px 54px 0 0", pointerEvents: "none" }}>
            <div style={{
              opacity: fade, transform: `scale(${pop})`, transformOrigin: "top right", textAlign: "right",
              background: "rgba(10,10,14,.62)", padding: "18px 26px 20px", borderRadius: 14,
              borderRight: `8px solid ${color}`,
            }}>
              <div style={{ color: "#fff", fontSize: 76, fontWeight: 900, lineHeight: 1, letterSpacing: -1.5,
                            fontVariantNumeric: "tabular-nums", textShadow: "0 3px 14px rgba(0,0,0,.6)" }}>
                {cur.stat.num}
              </div>
              {cur.stat.cap && (
                <div style={{ color: "#ffffffcc", fontSize: 26, fontWeight: 700, letterSpacing: 1, marginTop: 8 }}>
                  {cur.stat.cap.toUpperCase()}
                </div>
              )}
              <div style={{ height: 7, background: color, borderRadius: 4, marginTop: 14,
                            transform: `scaleX(${Math.min(1, rel2 / 20)})`, transformOrigin: "right center" }} />
            </div>
          </AbsoluteFill>
        );
      })()}
      {/* (6) KẾT BÀI (23/8): ~2 giây cuối hiện lời mời theo dõi + tên kênh — tăng đăng ký và cho
          YouTube thấy video có cấu trúc mở-thân-kết rõ ràng (điểm cộng khi xét kiếm tiền). */}
      {(() => {
        const left = total - f;
        if (left > 62 || left < 0) return null;
        const p = Math.min(1, (62 - left) / 14);
        return (
          <AbsoluteFill style={{ pointerEvents: "none", opacity: p }}>
            <AbsoluteFill style={{ background: "rgba(8,8,12,.62)" }} />
            <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
              <div style={{ textAlign: "center", transform: `translateY(${(1 - p) * 14}px)` }}>
                <div style={{ color: "#fff", fontSize: 54, fontWeight: 900, letterSpacing: -0.5 }}>
                  More things you had wrong?
                </div>
                <div style={{ height: 8, width: 120, background: color, borderRadius: 4, margin: "22px auto" }} />
                <div style={{ color: "#fff", fontSize: 40, fontWeight: 900, letterSpacing: 4 }}>
                  {(name || "").toUpperCase()}
                </div>
              </div>
            </AbsoluteFill>
          </AbsoluteFill>
        );
      })()}
      {/* watermark kênh */}
      {name && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-end", padding: 34 }}>
          <div style={{ color: "#ffffffc9", fontSize: 30, fontWeight: 800, letterSpacing: 1 }}>{name}</div>
        </AbsoluteFill>
      )}
      {lines.map((l, i) => (
        <Sequence key={"a" + i} from={l.from} durationInFrames={l.dur}>
          <Audio src={staticFile(`${slug}/${l.audio}`)} />
        </Sequence>
      ))}
      {music && <Audio src={staticFile(music)} loop
        volume={Math.min(ci(f, 0, 24, 0, 1), ci(f, total - 30, total, 1, 0)) * 0.09} />}
    </AbsoluteFill>
  );
};

export const calcToon = ({ props }: { props: any }) => {
  const fr = (props && props.frames) || [];
  const ln = (props && props.lines) || [];
  const endF = fr.length ? Math.max(...fr.map((x: any) => (x.from || 0) + (x.dur || 0))) : 300;
  const endL = ln.length ? Math.max(...ln.map((x: any) => (x.from || 0) + (x.dur || 0))) : 0;
  return { durationInFrames: Math.max(120, Math.max(endF, endL) + 18) };
};
