import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { BoiCanh, BANG_MAU, TenBoiCanh, Paltte } from "./BoiCanh";
import { DienVien, CAM_XUC, KIEU_MAU, visemeTai, Kieu, TenCamXuc, TenCuChi, TenDang, Tu } from "./DienVien";

/**
 * KỊCH V2 — phim hoạt hình có nhân vật, dựng hoàn toàn bằng vector (29/8/2026).
 *
 * Thành phần này ghép ba thứ lại: BỐI CẢNH (nền theo niche) + DIỄN VIÊN (con rối điều khiển được)
 * + MÁY QUAY (đổi góc theo diễn biến). Lời đọc và mốc thời gian từng từ đến từ edge-tts, đã có
 * sẵn trong dây chuyền; ở đây chỉ đọc ra và dùng.
 *
 * KHÔNG tiêu một lượt hạn mức vẽ ảnh nào. Xem `BoiCanh.tsx` để biết vì sao điều đó quan trọng.
 */

const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const trn = (a: number, b: number, t: number) => a + (b - a) * kep(t);
const muot = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

// ══════════════════════════════════════════════════════════════════════════════════════════
// MÁY QUAY ẢO
// ------------------------------------------------------------------------------------------
// Một cảnh 2D không có máy quay thật, nhưng có thứ tương đương: đổi khung nhìn. Ba cỡ cảnh, đúng
// như ngôn ngữ điện ảnh vẫn dùng, và mỗi cỡ nói một điều khác nhau:
//   rong  — cho thấy nhân vật ở ĐÂU (mở đầu, chuyển bối cảnh)
//   trung — cho thấy nhân vật LÀM GÌ (cử chỉ, đạo cụ)
//   can   — cho thấy nhân vật CẢM THẤY GÌ (mắt, chân mày, khoé miệng)
// Câu chốt của một cảnh bao giờ cũng ở cỡ CẬN: người xem cần thấy khuôn mặt lúc con số rơi xuống.
//
// Chuyển giữa hai cỡ: LIA MƯỢT trong cùng một câu, CẮT THẲNG khi sang câu mới. Lia liên tục thì
// đọc ra là trôi vô định; cắt liên tục thì chóng mặt. Trộn hai thứ mới ra nhịp phim.
// ══════════════════════════════════════════════════════════════════════════════════════════
type CoCanh = "rong" | "trung" | "can";
// 29/8 — hệ số phóng hạ xuống sau khi nhân vật được vẽ đúng cỡ. Bộ số cũ (1.0/1.5/2.45) tính
// cho một con rối nhỏ; giữ nguyên thì cỡ cận phóng tới mức chỉ còn thấy cái cằm.
const KHUNG: Record<CoCanh, { x: number; y: number; z: number }> = {
  // Con rối cao ~420 đơn vị × 1.75 = 735; nó trải từ y=236 (gót) tới y=-499 (đỉnh đầu), tâm ở
  // khoảng -130. Đặt máy quay đúng tâm ấy thì nhân vật nằm giữa khung, không bị cụt đầu cũng
  // không lọt thỏm — hai lỗi đã lần lượt xảy ra ở hai lượt render trước.
  rong: { x: 0, y: -100, z: 0.8 },       // thấy cả bối cảnh
  trung: { x: 0, y: -130, z: 1.0 },      // thấy nửa người + cử chỉ tay
  can: { x: 0, y: -330, z: 1.5 },        // thấy mặt: mắt, chân mày, khoé miệng
};

export type Canh = {
  s: number;                 // giây bắt đầu
  e: number;                 // giây kết thúc
  nar: string;               // lời đọc (để dựng phụ đề, TTS đã render sẵn)
  camXuc?: TenCamXuc;
  cuChi?: TenCuChi;
  dang?: TenDang;
  co?: CoCanh;
  nhin?: [number, number];
  boi?: TenBoiCanh;
  soLon?: string;            // con số to hiện lên giữa cảnh
  nhanSo?: string;
  cot?: { nhan: string; gt: number; hien: string }[];   // biểu đồ cột làm đạo cụ
  sfx?: string;              // tệp tiếng động trong public/
};

export type PropsKich = {
  canh?: Canh[];
  tu?: Tu[];                 // mốc thời gian từng từ (edge-tts WordBoundary)
  voMp3?: string;
  nhac?: string;
  kieu?: Partial<Kieu>;
  kieuGoc?: keyof typeof KIEU_MAU;
  bangMau?: keyof typeof BANG_MAU;
  tieuDe?: string;
  nguon?: string;
  font?: string;
};

export const calcKich = async ({ props }: { props: PropsKich }) => {
  const cs = props.canh || [];
  const het = cs.length ? Math.max(...cs.map((c) => c.e)) : 20;
  return { durationInFrames: Math.max(90, Math.round((het + 0.6) * 30)), fps: 30 };
};

/** Con số to — thứ giữ chân người xem, nên nó phải ĐẾM LÊN chứ không hiện sẵn. */
const SoTo: React.FC<{ so: string; nhan?: string; p: number; mau: Paltte }> = ({ so, nhan, p, mau }) => {
  const vao = muot(kep(p / 0.18));
  const m = String(so).match(/^(\D*)([\d][\d,.]*)(.*)$/s);
  let hien = so;
  if (m) {
    const goc = parseFloat(m[2].replace(/,/g, ""));
    const le = (m[2].split(".")[1] || "").length;
    const e = 1 - Math.pow(1 - kep(p / 0.45), 3);
    hien = p >= 0.45 ? m[2]
      : (goc * e).toLocaleString("en-US", { minimumFractionDigits: le, maximumFractionDigits: le });
    hien = m[1] + hien + m[3];
  }
  return (
    <g opacity={vao} transform={`translate(0 ${(1 - vao) * 26})`}>
      {/* 29/8 — VẼ TẠI GỐC 0, KHÔNG TỰ DỜI LÊN -330. Bản trước tự cộng một khoảng lệch của
          riêng nó, rồi nơi gọi cộng thêm một khoảng nữa — hai lần dời chồng lên nhau và con số
          "3,920" bị cắt cụt ở mép trên khung. Một thành phần chỉ nên biết VẼ GÌ; ĐẶT Ở ĐÂU là
          việc của nơi gọi, nơi duy nhất biết khung hình dọc hay ngang. */}
      <text x={0} y={0} textAnchor="middle" fontSize={124} fontWeight={900}
            fill={mau.nhan} stroke={mau.muc} strokeWidth={9} paintOrder="stroke"
            style={{ fontVariantNumeric: "tabular-nums" }}>{hien}</text>
      {nhan ? (
        <text x={0} y={62} textAnchor="middle" fontSize={38} fontWeight={800}
              fill={mau.muc} opacity={0.86} letterSpacing={1.5}>{nhan.toUpperCase()}</text>
      ) : null}
    </g>
  );
};

/** Biểu đồ cột làm ĐẠO CỤ trong cảnh — mọc lên từ đáy, so được bằng mắt. */
const CotDaoCu: React.FC<{ cot: NonNullable<Canh["cot"]>; p: number; mau: Paltte }> = ({ cot, p, mau }) => {
  const dinh = Math.max(1, ...cot.map((c) => c.gt));
  return (
    <g transform="translate(150 120)">
      {cot.map((c, i) => {
        const moc = muot(kep((p - i * 0.06) / 0.3));
        const h = (c.gt / dinh) * 300 * moc;
        return (
          <g key={i} transform={`translate(${i * 104} 0)`}>
            <rect x={0} y={-h} width={78} height={h} rx={7}
                  fill={i === 0 ? mau.nhan : "#F2C230"} stroke={mau.muc} strokeWidth={5} />
            <text x={39} y={-h - 16} textAnchor="middle" fontSize={30} fontWeight={900}
                  fill={mau.muc} opacity={moc}>{c.hien}</text>
            <text x={39} y={28} textAnchor="middle" fontSize={22} fontWeight={700}
                  fill={mau.muc} opacity={0.75 * moc}>{c.nhan.slice(0, 11)}</text>
          </g>
        );
      })}
    </g>
  );
};

/** Phụ đề karaoke — tô sáng đúng từ đang được đọc, lấy từ chính mốc thời gian của giọng. */
const PhuDe: React.FC<{ tu: Tu[]; giay: number; mau: Paltte; day: number }> = ({ tu, giay, mau, day }) => {
  const k = tu.findIndex((w) => giay >= w.t && giay < w.t + w.d);
  if (k < 0 && !tu.some((w) => Math.abs(w.t - giay) < 1.2)) return null;
  const tam = k >= 0 ? k : tu.findIndex((w) => w.t > giay);
  const dau = Math.max(0, (tam < 0 ? tu.length : tam) - 4);
  const doan = tu.slice(dau, dau + 9);
  return (
    <g transform={`translate(0 ${day})`}>
      <text x={0} y={0} textAnchor="middle" fontSize={46} fontWeight={900}
            stroke={mau.muc} strokeWidth={9} paintOrder="stroke" fill="#FFFFFF">
        {doan.map((w, i) => (
          <tspan key={i} fill={k >= 0 && tu[k] === w ? mau.nhan : "#FFFFFF"}>{w.w} </tspan>
        ))}
      </text>
    </g>
  );
};

export const KichV2: React.FC<PropsKich> = ({
  canh = [], tu = [], voMp3 = "", nhac = "", kieu = {}, kieuGoc = "nam_dam",
  bangMau = "san_sau", tieuDe = "", nguon = "", font = "",
}) => {
  const f = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const giay = f / fps;
  const doc = height > width;
  const mau = BANG_MAU[bangMau] || BANG_MAU.san_sau;
  const nv: Kieu = { ...(KIEU_MAU[kieuGoc] || KIEU_MAU.nam_dam), ...kieu };

  // cảnh hiện tại
  let i = canh.findIndex((c) => giay >= c.s && giay < c.e);
  if (i < 0) i = giay < (canh[0]?.s ?? 0) ? 0 : canh.length - 1;
  const C = canh[i] || ({ s: 0, e: 6, nar: "" } as Canh);
  const p = kep((giay - C.s) / Math.max(0.001, C.e - C.s));

  // ── MÁY QUAY: lia mượt trong cảnh, cắt thẳng khi sang cảnh ─────────────────────────────
  // Cỡ cảnh của cảnh này và cảnh trước; nếu KHÁC nhau thì lia trong 0,5 giây đầu, còn giống
  // nhau thì đứng yên. Nhờ vậy máy quay chỉ động khi có LÝ DO, không trôi vô cớ.
  const coNay: CoCanh = C.co || "trung";
  const coTruoc: CoCanh = (canh[i - 1]?.co as CoCanh) || coNay;
  const tLia = kep((giay - C.s) / 0.5);
  const K0 = KHUNG[coTruoc], K1 = KHUNG[coNay];
  const cam = {
    x: trn(K0.x, K1.x, muot(tLia)),
    y: trn(K0.y, K1.y, muot(tLia)),
    z: trn(K0.z, K1.z, muot(tLia)),
  };
  // rung máy rất nhẹ — thiếu nó thì khung đứng chết như ảnh chụp
  const rung = Math.sin(giay * 1.3) * 3.2;

  const noi = visemeTai(tu, giay, CAM_XUC[C.camXuc || "trung_tinh"].ha);
  const nhin = C.nhin || [0, 0];

  const vb = doc ? "-500 -700 1000 1500" : "-820 -560 1640 1120";

  return (
    <AbsoluteFill style={{ background: mau.troi[1], fontFamily: font || "Poppins, Arial, sans-serif" }}>
      <svg viewBox={vb} width="100%" height="100%" preserveAspectRatio="xMidYMid slice">
        <g transform={`translate(${-cam.x + rung} ${-cam.y}) scale(${cam.z})`}
           style={{ transformOrigin: "0px 0px" }}>
          <BoiCanh ten={C.boi || "san_sau"} mau={mau} t={giay} />
          {C.cot ? <CotDaoCu cot={C.cot} p={p} mau={mau} /> : null}
          <DienVien
            kieu={nv}
            camXuc={C.camXuc || "trung_tinh"}
            cuChi={C.cuChi || "nghi"}
            dang={C.dang || "dung"}
            nhin={nhin}
            noi={noi}
            t={giay}
            // 29/8 — CỠ NHÂN VẬT TÍNH THEO KHUNG, KHÔNG BỐC MỘT SỐ.
            // Con rối vẽ trong hệ cao ~420 đơn vị (từ đỉnh đầu tới gót). Khung dọc cao 1500 đơn
            // vị, nên tỉ lệ 1.12 cho ra một người cao 470/1500 — lọt thỏm, đúng như khung render
            // thử. Muốn nhân vật chiếm khoảng 3/5 chiều cao (tỉ lệ quen thuộc của phim hoạt hình
            // kể chuyện) thì cần ~2.1 cho khung dọc và ~1.6 cho khung ngang.
            x={C.cot ? -250 : 0}
            y={236}
            // 29/8 lần hai — lần trước tôi tăng cỡ nhân vật 1.12->2.1 NHƯNG cùng lúc hạ zoom
            // máy quay 1.5->1.0. Tích hai số không đổi (1.68), nên khung render ra y hệt và tôi
            // suýt kết luận "sửa không ăn". Bài học: đổi hai hệ số nhân với nhau trong cùng một
            // lượt thì không đo được cái nào có tác dụng.
            scale={doc ? 1.75 : 1.35}
          />
        </g>

        {/* 29/8 — SỐ TO PHẢI NẰM NGOÀI NHÓM MÁY QUAY.
            Khung render đầu: "3,797" phóng to theo cỡ cận và đè thẳng lên mặt nhân vật — đúng
            lỗi chồng chữ anh dặn tránh. Con số là lớp THÔNG TIN, không phải vật trong cảnh; nó
            phải đứng yên ở một chỗ cố định trên màn hình bất kể máy quay đi đâu. */}
        {C.soLon ? (
          <g transform={`translate(0 ${doc ? -530 : -390})`}>
            <SoTo so={C.soLon} nhan={C.nhanSo} p={p} mau={mau} />
          </g>
        ) : null}

        {/* Lớp chữ KHÔNG đi theo máy quay — phụ đề mà lia theo thì không đọc nổi. */}
        {tieuDe && giay < 3.2 ? (
          <text x={0} y={doc ? -648 : -498} textAnchor="middle" fontSize={doc ? 58 : 52}
                fontWeight={900} fill="#FFFFFF" stroke={mau.muc} strokeWidth={10}
                paintOrder="stroke" opacity={kep((3.2 - giay) / 0.4)}>
            {tieuDe.slice(0, 42)}
          </text>
        ) : null}
        <PhuDe tu={tu} giay={giay} mau={mau} day={doc ? 610 : 430} />
        {nguon ? (
          <text x={0} y={doc ? 700 : 500} textAnchor="middle" fontSize={22} fontWeight={700}
                fill={mau.muc} opacity={0.45}>Source: {nguon}</text>
        ) : null}
      </svg>

      {voMp3 ? <Audio src={staticFile(voMp3)} /> : null}
      {nhac ? <Audio src={staticFile(nhac)} volume={0.1} /> : null}
      {/* TIẾNG ĐỘNG phải nổ ĐÚNG lúc cảnh bắt đầu. `Audio` một mình luôn phát từ khung 0 của
          composition; muốn hẹn giờ thì phải bọc trong `Sequence` — đó mới là thứ dời mốc. */}
      {canh.filter((c) => c.sfx).map((c, k) => (
        <Sequence key={k} from={Math.round(c.s * fps)} durationInFrames={Math.round(1.6 * fps)}>
          <Audio src={staticFile(c.sfx as string)} volume={0.34} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
