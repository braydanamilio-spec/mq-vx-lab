import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { StickFigure, POSES, live } from "../StickAnim";
import { SceneBG } from "../SceneBG";

/* ══════════════════════════════════════════════════════════════════════════════════════════
   KỊCH NGƯỜI QUE — 15 giây, bốn nhịp  (1/9/2026)

   Anh: *"xưa có loại hoạt hình animation người que e làm cho a nhân vật di chuyển tay chân cử
   chỉ mượt lằm mà… làm cho a 10 channel mới này kiểu người que phong cách chuẩn usa cử chỉ
   biểu cảm mượt mà, bối cảnh đúng như kịch bản."*

   VÌ SAO DÙNG BỘ KHUNG NÀY, KHÔNG DÙNG ENGINE TRUYỆN TRANH
   Engine truyện tranh (`DienVienHai`) có tám tư thế TĨNH và chỉ đổi cánh tay; hai chân đứng
   nguyên một chỗ trừ lúc đi bộ. Đo ra hôm qua: mười kênh khác mặt, khác màu, khác nhà mà bóng
   dáng y hệt nhau.
   `StickAnim` thì khác về bản chất: bảy tư thế CỘNG lớp `live()` chạy liên tục trên chín khớp,
   mỗi khớp một pha —
     · cẳng tay trễ pha so cánh tay  -> follow-through, nguyên tắc gốc của hoạt hình
     · đầu gật theo độ mở miệng      -> nói tới đâu gật tới đó
     · hai chân dồn trọng tâm so le  -> đứng mà vẫn sống
   Đó chính là "cử chỉ mượt" anh nhớ.

   VÌ SAO GÓI 15 GIÂY HỢP HƠN GÓI 6 GIÂY
   Gói này cho MỖI NHỊP một hành động riêng ("walks in", "takes a photo", "walks by"). Engine
   truyện tranh không diễn được hành động; engine người que thì ánh xạ thẳng hành động -> tư thế.

   BỐ CỤC: bốn nhịp × ~3,75 giây. Mỗi nhịp một bối cảnh `SceneBG` chọn theo LỜI THOẠI của chính
   nhịp ấy, một hoặc hai nhân vật đứng diễn trên sàn, chữ thoại ở dưới.
   ══════════════════════════════════════════════════════════════════════════════════════════ */

const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const bat = (t: number) => 1 - Math.pow(1 - kep(t), 3);

export type VaiQue = {
  ten: string; skin: string; shirt: string; pants: string; hair: string;
  cap?: string; hoodie?: boolean; glasses?: boolean; scale: number;
};
export type NhipQue = {
  s: number; e: number; bg: string; hanh: string;
  ai: number;            // 0 = trái, 1 = phải
  nar: string;           // lời thoại
  pose: string; expr: string;
  hai?: boolean;         // hai người trong khung
};
export type PropsQue = {
  nhip?: NhipQue[]; tu?: { t: number; d: number }[]; voMp3?: string; nhac?: string;
  nhacVol?: number; vaiA?: VaiQue; vaiB?: VaiQue;
  tieuDe?: string; handle?: string; mau?: string; mauPhu?: string; hook?: string;
};

export const calcQue = async ({ props }: { props: PropsQue }) => {
  const n = props.nhip || [];
  const het = n.length ? Math.max(...n.map((x) => x.e)) : 15;
  return { durationInFrames: Math.max(90, Math.round((het + 0.5) * 30)), fps: 30 };
};

/* Chữ thoại: dải dưới, chữ to, nền đậm — đọc được trên điện thoại cầm tay. Không dùng bong
   bóng như bản truyện tranh: người que gầy, bong bóng có đuôi chỉ vào sẽ che mất tay đang diễn. */
const Loi: React.FC<{ chu: string; W: number; H: number; p: number; mau: string }> =
({ chu, W, H, p, mau }) => {
  if (!chu) return null;
  const n = Math.max(8, chu.length);
  const fs = Math.max(38, Math.min(74, Math.sqrt((W * 0.84 * H * 0.13) / 0.58 / n)));
  return (
    <div style={{
      position: "absolute", left: W * 0.06, right: W * 0.06, bottom: H * 0.13,
      transform: `translateY(${(1 - bat(p)) * 26}px)`, opacity: bat(p),
      background: "#12151Cdd", border: `5px solid ${mau}`, borderRadius: 22,
      padding: "22px 26px", textAlign: "center",
      fontFamily: "Poppins, Arial Black, sans-serif", fontWeight: 800,
      fontSize: fs, lineHeight: 1.16, color: "#FFFFFF", letterSpacing: 0.2,
    }}>{chu}</div>
  );
};

export const KichQue: React.FC<PropsQue> = ({
  nhip = [], tu = [], voMp3 = "", nhac = "", nhacVol = 0.16,
  vaiA, vaiB, tieuDe = "", handle = "", mau = "#E0533D", mauPhu = "#2F7D6B", hook = "",
}) => {
  const frame = useCurrentFrame();
  const { fps, width: W, height: H } = useVideoConfig();
  const t = frame / fps;

  const N = nhip.find((x) => t >= x.s && t < x.e) || nhip[nhip.length - 1] ||
    ({ s: 0, e: 15, bg: "home", hanh: "", ai: 0, nar: "", pose: "idle", expr: "neutral" } as NhipQue);
  const trong = t - N.s;
  const p = kep(trong / 0.42);

  // Khẩu hình lấy từ MỐC TỪ, không lấy từ biên độ sóng: mốc từ có sẵn từ bước đọc giọng và
  // chính xác hơn — biên độ còn dính cả tiếng nhạc nền.
  const dangNoi = tu.some((w) => t >= w.t - 0.02 && t < w.t + w.d + 0.05);
  const mo = dangNoi ? 0.35 + 0.45 * Math.abs(Math.sin(t * 21)) : 0;

  const tuThe = live(POSES[N.pose] || POSES.idle, t, mo);
  const nghi = live(POSES.idle, t + 1.7, 0);
  const blink = Math.sin(t * 2.6) > 0.93 ? 0.12 : 1;
  const breath = Math.sin(t * 2.8) * 3;

  const A = vaiA || { ten: "A", skin: "#F6C89A", shirt: "#3E7BFA", pants: "#2B3A55",
                      hair: "#3A2A22", scale: 1 } as VaiQue;
  const B = vaiB || { ten: "B", skin: "#EFC49A", shirt: "#E0715E", pants: "#3A3D42",
                      hair: "#2E2018", scale: 1 } as VaiQue;

  // ── CỠ NGƯỜI: ĐO, KHÔNG ĐOÁN ──────────────────────────────────────────────────────
  // Bản đầu đặt `co = min(W,H)/1080 * 1.32`. Đo ra: bộ khung `StickFigure` cao ~190 đơn vị
  // (chân y=0 · vai y=-86 · tâm đầu y=-146), nên 1,32 cho ra người cao 250px trên khung 1920
  // — tức 13% chiều cao, và hai phần ba khung trống hoác. Trên điện thoại thì không thấy mặt.
  // Nay tính NGƯỢC từ mục tiêu: người chiếm 55% chiều cao khung -> co = H*0.55/190.
  // Đây đúng bài học đã ghi ở CLAUDE.md: hằng toạ độ phải ĐO trong ngữ cảnh dùng nó, và khi
  // con số với con mắt bất đồng thì đo pixel.
  const CAO_RIG = 215;    // chế độ que: rig cao hơn vì chân dài hơn
  const co = (H * 0.55) / CAO_RIG;
  // Sàn: chừa chỗ cho dải chữ thoại (13% từ đáy) và dải tên kênh (5,5%).
  // Gốc của rig nằm ở HÔNG, chân vẽ xuống dưới ~40 đơn vị. Đặt `y = sàn` là chân thọc xuống
  // dưới sàn và chui vào dải chữ. Trừ đi phần chân thì bàn chân mới chạm đúng mặt sàn.
  const CHAN_DUOI = 62;   // chân dài hơn ở chế độ que
  const sanY = H * 0.74 - CHAN_DUOI * co;
  // MỖI NHỊP MỘT NGƯỜI DIỄN — đọc thẳng từ gói: "Derek stands in the kitchen…", "Sara walks
  // in…", "Max appears…". Gói viết từng nhịp cho MỘT diễn viên, không phải hai người đối thoại
  // cùng khung.
  // Bản đầu vẽ cả hai: ở cỡ 55% chiều cao thì mỗi người rộng ~480px mà khoảng cách chỉ 454px
  // -> hai thân chồng lên nhau. Chọn giữa "thu nhỏ cả hai" và "mỗi nhịp một người", lấy cái
  // thứ hai: khung dọc 15 giây trên điện thoại cần MẶT TO, và gói vốn đã viết như thế.
  // Người kia đứng lùi phía sau, nhỏ và mờ — có mặt để khung không trống, không tranh chỗ.
  const hai = N.hai === true;
  const xA = W * 0.5;
  const xB = W * 0.5;
  const xPhu = N.ai === 0 ? W * 0.80 : W * 0.20;   // vai phụ đứng lùi, lệch sang mép

  return (
    <AbsoluteFill style={{ background: "#0E1116" }}>
      {/* Bối cảnh vẽ 2D có chiều sâu — đổi theo TỪNG NHỊP, chọn theo lời thoại của nhịp ấy. */}
      <SceneBG kind={N.bg} width={W} height={H} floorPct={0.80} wide={W > H}
               T={{ ink: "#1E2A38", accent: mau, accent2: mauPhu }} time={t} />

      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}
           style={{ position: "absolute", inset: 0 }}>
        {/* Bóng tiếp đất — thứ neo nhân vật xuống sàn. Thiếu nó là người lơ lửng, lỗi đã trả
            giá nhiều lần ở engine truyện tranh. */}
        {(hai || N.ai === 0) ? (
          <ellipse cx={xA} cy={sanY + 6} rx={74 * co * A.scale} ry={13 * co} fill="#0A0C10" opacity={0.34} />
        ) : null}
        {(hai || N.ai === 1) ? (
          <ellipse cx={xB} cy={sanY + 6} rx={74 * co * B.scale} ry={13 * co} fill="#0A0C10" opacity={0.34} />
        ) : null}

        {/* Vai PHỤ đứng lùi: nhỏ 0,62 lần, mờ, không có khẩu hình — cho khung có chiều sâu
            mà không tranh chỗ với người đang nói. */}
        <g opacity={0.42}>
          <ellipse cx={xPhu} cy={sanY - 22} rx={52 * co * 0.62} ry={10 * co * 0.62}
                   fill="#0A0C10" opacity={0.4} />
          <StickFigure x={xPhu} y={sanY - 28} scale={co * 0.62}
                       flip={N.ai === 0} pose={nghi} mouthOpen={0} expr="curious"
                       blink={blink} breath={breath}
                       skin={(N.ai === 0 ? B : A).skin} shirt={(N.ai === 0 ? B : A).shirt}
                       pants={(N.ai === 0 ? B : A).pants} hair={(N.ai === 0 ? B : A).hair}
                       cap={(N.ai === 0 ? B : A).cap} hoodie={(N.ai === 0 ? B : A).hoodie}
                       glasses={(N.ai === 0 ? B : A).glasses} chanDong que />
        </g>

        {/* Người ĐANG NÓI — giữa khung, to, có khẩu hình và biểu cảm của nhịp này. */}
        <ellipse cx={xA} cy={sanY + 6} rx={74 * co} ry={13 * co} fill="#0A0C10" opacity={0.34} />
        <StickFigure x={xA} y={sanY} scale={co * (N.ai === 0 ? A.scale : B.scale)}
                     pose={tuThe} mouthOpen={mo} mouthWide={0.55}
                     expr={N.expr as any} blink={blink} breath={breath}
                     skin={(N.ai === 0 ? A : B).skin} shirt={(N.ai === 0 ? A : B).shirt}
                     pants={(N.ai === 0 ? A : B).pants} hair={(N.ai === 0 ? A : B).hair}
                     cap={(N.ai === 0 ? A : B).cap} hoodie={(N.ai === 0 ? A : B).hoodie}
                     glasses={(N.ai === 0 ? A : B).glasses} chanDong que />
      </svg>

      <Loi chu={N.nar} W={W} H={H} p={p} mau={mau} />

      {/* Thẻ hook 1,4 giây đầu — nhịp 0-3s của gói là HOOK, và YouTube quyết giữ hay lướt ở
          đúng quãng ấy. */}
      {hook && t < 1.4 ? (
        <div style={{
          position: "absolute", left: 0, right: 0, top: H * 0.09,
          display: "flex", justifyContent: "center", pointerEvents: "none",
          opacity: kep((1.4 - t) / 0.3), transform: `scale(${1 + (1 - kep(t / 0.25)) * 0.08})`,
        }}>
          <div style={{
            background: mau, border: "8px solid #12151C", borderRadius: 14,
            padding: "16px 26px", maxWidth: W * 0.86, textAlign: "center",
            boxShadow: "10px 11px 0 #12151C",
            fontFamily: "Poppins, Arial Black, sans-serif", fontWeight: 900,
            fontSize: 60, lineHeight: 1.05, color: "#FFFFFF",
          }}>{hook}</div>
        </div>
      ) : null}

      {/* Dải tên kênh — mỏng, đáy khung, không chạm vùng an toàn của nút bấm trên điện thoại. */}
      <div style={{
        position: "absolute", left: 0, right: 0, bottom: 0, height: H * 0.055,
        background: "#12151C", display: "flex", alignItems: "center",
        justifyContent: "space-between", padding: "0 34px",
        fontFamily: "Poppins, Arial, sans-serif", fontWeight: 800,
        fontSize: 26, color: "#FFFFFF", letterSpacing: 1.6,
      }}>
        <span>{tieuDe}</span><span style={{ color: mau, fontSize: 22 }}>{handle}</span>
      </div>

      {voMp3 ? <Audio src={staticFile(voMp3)} /> : null}
      {nhac ? (
        <Audio src={staticFile(nhac)} loop
               volume={(f: number) => {
                 const gy = f / fps;
                 const noi = nhip.some((x) => gy >= x.s - 0.1 && gy <= x.e + 0.15 && x.nar);
                 return nhacVol * (noi ? 0.55 : 1);
               }} />
      ) : null}
    </AbsoluteFill>
  );
};
