import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { POSES, live } from "../StickAnim";
import { NguoiQue, ThuQue, QUE_CAO, QUE_GOT, Vai } from "./NguoiQue";
import { NenQue } from "./NenQue";

/* ══════════════════════════════════════════════════════════════════════════════════════════
   KỊCH NGƯỜI QUE — 15 giây, bốn nhịp, cả nhà trong một căn phòng  (1/9/2026)

   Anh, bốn lần liền, mỗi lần chỉ đúng một chỗ hỏng:
     "chưa thể hiện nam nữ"                -> giới/tuổi có sẵn trong gói mà không ai đọc
     "chưa có đa nhân vật"                 -> vẽ đúng một người mỗi nhịp
     "nhân vật quá to so với bối cảnh"     -> ĐO RA: đồ đạc nhỏ gấp 3,2 lần, không phải người to
     "bối cảnh phải đúng như prompt 15s"   -> kitchen/laundry/hallway/bedroom rơi hết về "home"
     "làm demo đúng clip 15s"              -> thoại nối sát nhau, hết ở giây 8
     "nhân vật ko phải giống hết… có nét đặc trưng"

   Một gốc chung cho cả sáu: **tôi dựng phim từ trí nhớ của mình về gói, không dựng từ gói.**
   Gói viết sẵn tuổi, giới, tóc, áo, kính, nơi chốn, ai có mặt ở nhịp nào, và bốn cửa sổ thời
   gian 0-3 / 3-7 / 7-11 / 11-15. Tôi đọc lấy lời thoại rồi tự bịa phần còn lại.

   Nay mọi thứ trên màn hình đều truy được về một dòng trong gói.
   ══════════════════════════════════════════════════════════════════════════════════════════ */

const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const bat = (t: number) => 1 - Math.pow(1 - kep(t), 3);

export type VaiQue = Vai & { ten: string; cao: number };
export type NhipQue = {
  s: number; e: number; hanh: string; ai: number;
  nar: string; pose: string; expr: string;
};
export type PropsQue = {
  nhip?: NhipQue[]; vai?: VaiQue[]; noi?: string; thu?: string;
  tu?: { t: number; d: number }[]; voMp3?: string; nhac?: string; nhacVol?: number;
  tieuDe?: string; handle?: string; mau?: string; mauPhu?: string; hook?: string;
};

/* ĐÚNG 15 GIÂY. Gói khoá cứng con số này ("exactly 15 seconds", "final reaction in the last 3
   seconds"), và nó cũng là con số Shorts/Reels thích. Không lấy độ dài tiếng nói làm độ dài
   phim nữa — tiếng nói ngắn hơn thì phần dôi ra là KHOẢNG LẶNG DIỄN, không phải phim bị thừa. */
export const DAI_QUE = 15.0;
export const calcQue = async () => ({ durationInFrames: Math.round(DAI_QUE * 30), fps: 30 });

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

/* CHỖ ĐỨNG theo số người. Đo trước khi chọn: ở nét que, người buông tay rộng chừng 0,33 lần
   chiều cao. Cao 0,42 khung (806px trên khung 1920) -> rộng ~265px; bốn người là 1060px, vừa
   khít khung 1080. Cao hơn nữa thì bốn người chồng lên nhau — đó là lý do bản trước phải bỏ
   bớt người chứ không phải vì gói viết mỗi nhịp một người. */
const CHO = [[0.5], [0.30, 0.70], [0.17, 0.5, 0.83]];
/* TỐI ĐA BA NGƯỜI trong khung. Gói có bốn vai, và bản trước dựng cả bốn: soi khung ra bốn
   người chen kín từ mép này sang mép kia, không ai đọc được. Ba người là ngưỡng đo được —
   mỗi người rộng ~0,33 chiều cao, ba người cao 0,38 khung chiếm 0,64 bề ngang, còn chỗ thở.
   Ai bị bỏ ra thì bỏ người KHÔNG nói ở nhịp nào — chọn theo dữ liệu, không theo thứ tự. */
const TOI_DA = 3;

export const KichQue: React.FC<PropsQue> = ({
  nhip = [], vai = [], noi = "phong_khach", thu = "", tu = [], voMp3 = "", nhac = "",
  nhacVol = 0.16, tieuDe = "", handle = "", mau = "#E0533D", mauPhu = "#2F7D6B", hook = "",
}) => {
  const frame = useCurrentFrame();
  const { fps, width: W, height: H } = useVideoConfig();
  const t = frame / fps;

  const N = nhip.find((x) => t >= x.s && t < x.e) || nhip[nhip.length - 1] ||
    ({ s: 0, e: 15, hanh: "", ai: 0, nar: "", pose: "idle", expr: "neutral" } as NhipQue);
  const p = kep((t - N.s) / 0.42);

  const dangNoi = tu.some((w) => t >= w.t - 0.02 && t < w.t + w.d + 0.05);
  const mo = dangNoi ? 0.35 + 0.45 * Math.abs(Math.sin(t * 21)) : 0;
  const blink = Math.sin(t * 2.6) > 0.93 ? 0.12 : 1;
  const breath = Math.sin(t * 2.8) * 3;

  /* ── MẶT ĐẤT VÀ CỠ NGƯỜI: MỘT NGUỒN DUY NHẤT ─────────────────────────────────────────
     Bản đầu có HAI hằng cùng trả lời "mặt đất ở đâu" (`floorPct=0.80` cho nền, `H*0.74` cho
     bàn chân) và lệch 116px — người treo lửng giữa không.
     Nay `SAN` và `NGUOI` là hai con số duy nhất; nền lẫn người đều đọc từ đây, và `NenQue`
     nhận `nguoi` để suy ra kích thước từng món đồ. Không còn chỗ nào cho hai số nói khác nhau. */
  const SAN = 0.66;                       // sàn chiếm trọn phần ba dưới
  const sanY = H * SAN;
  const NGUOI = H * 0.38;                 // chiều cao NGƯỜI LỚN, đơn vị của cả căn phòng

  const dan = vai.length ? vai : [{ ten: "", gioi: "nam", tuoi: "trung", toc: "ngan",
    mauToc: "#3B2A20", ao: "#3E7BFA", quan: "#2B3A55", pk: [], cao: 1 } as VaiQue];
  /* Chọn ai được lên hình: ưu tiên người CÓ NÓI trong tập (đọc từ `nhip`), rồi mới tới người
     chỉ đứng. `N.ai` trỏ vào danh sách gốc nên phải ánh xạ lại sau khi lọc — quên bước này là
     nhân vật A mấp máy môi trong khi nhân vật B đang nói, lỗi im lặng kinh điển. */
  const coNoi: number[] = [];
  nhip.forEach((x) => { if (!coNoi.includes(x.ai)) coNoi.push(x.ai); });
  const chon = [...coNoi, ...dan.map((_v, i) => i).filter((i) => !coNoi.includes(i))]
    .slice(0, TOI_DA).sort((a, b) => a - b);
  const hien = chon.map((i) => dan[i]);
  const cho = CHO[Math.min(hien.length, TOI_DA) - 1];

  return (
    <AbsoluteFill style={{ background: "#0E1116" }}>
      <NenQue noi={noi} W={W} H={H} san={sanY} nguoi={NGUOI} t={t} />

      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
        {hien.map((v, i) => {
          const noiVai = chon[i] === N.ai;
          const co = (NGUOI * v.cao) / QUE_CAO;
          const x = W * cho[i];
          /* Người ĐANG NÓI diễn tư thế của nhịp; người đứng nghe thì `idle` lệch pha để hai
             người không thở cùng nhịp — thở đồng bộ nhìn ra ngay là hình sao chép.
             KHÔNG làm mờ người đứng nghe: bản trước hạ xuống 0,42 và ở nét que thì một đường
             mảnh làm mờ chỉ còn là vệt xám, thêm nhiễu chứ không thêm chiều sâu. */
          const tuThe = live(POSES[noiVai ? (N.pose as string) : "idle"] || POSES.idle,
                             t + (noiVai ? 0 : 1.3 + i * 0.7), noiVai ? mo : 0);
          return (
            <g key={i}>
              <ellipse cx={x} cy={sanY + 4} rx={NGUOI * 0.15 * v.cao} ry={NGUOI * 0.026}
                       fill="#0A0C10" opacity={0.15} />
              <ellipse cx={x} cy={sanY + 2} rx={NGUOI * 0.07 * v.cao} ry={NGUOI * 0.013}
                       fill="#0A0C10" opacity={0.3} />
              <NguoiQue x={x} y={sanY - QUE_GOT * co} scale={co}
                        flip={i > (hien.length - 1) / 2}
                        pose={tuThe} vai={v}
                        mouthOpen={noiVai ? mo : 0}
                        /* Người đứng nghe: `neutral`, KHÔNG phải `deadpan`. Bản trước cho cả ba nửa
                           nhắm mắt nên khung nào cũng như cả nhà vừa ngủ dậy. Vẻ chán đời chỉ đắt
                           khi một người có, cả ba cùng có thì nó thành trạng thái nền. */
                        expr={noiVai ? N.expr : "neutral"}
                        blink={blink} breath={breath} />
            </g>
          );
        })}
        {thu ? (
          <ThuQue x={W * 0.90} y={sanY} scale={(NGUOI / QUE_CAO) * 0.62} mau={thu} t={t} />
        ) : null}
      </svg>

      <Loi chu={N.nar} W={W} H={H} p={p} mau={mau} />

      {hook && t < 1.4 ? (
        <div style={{
          position: "absolute", left: 0, right: 0, top: H * 0.055,
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
                 const noiGi = nhip.some((x) => gy >= x.s - 0.1 && gy <= x.e + 0.15 && x.nar);
                 return nhacVol * (noiGi ? 0.55 : 1);
               }} />
      ) : null}
    </AbsoluteFill>
  );
};
