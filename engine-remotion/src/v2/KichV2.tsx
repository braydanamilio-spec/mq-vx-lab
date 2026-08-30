import React from "react";
import { AbsoluteFill, Audio, Img, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { BoiCanh, BANG_MAU, TenBoiCanh, Paltte } from "./BoiCanh";
import { CAM_XUC, KIEU_MAU, visemeTai, Kieu, TenCamXuc, TenCuChi, TenDang, Tu } from "./DienVien";
// 30/8 — MƯỜI KÊNH DỮ LIỆU DÙNG CHUNG DIỄN VIÊN MỚI CỦA BỘ HÀI.
// Anh: *"ứng dụng những cải tiến ở 10 channel sau này nâng cấp vào 10 channel đầu tiên"*.
// `DienVienHai` mang toàn bộ phần đã sửa qua một đêm: khuôn mặt kiểu hoạt hình Mỹ (sọ quả lê,
// mắt bầu dục, lông mày khối, mũi nét móc, nếp cười), tóc có khối và mảng bóng, bàn tay găng bốn
// ngón liền mạch, nén–giãn giữ thể tích, các chu kỳ sống lệch tần số, giày có đế.
// Đổi được vì hai bộ dùng CHUNG giao diện: mười kênh dữ liệu chỉ có một người trong khung và
// luôn ở dáng ĐỨNG (kiểm bằng `kich_v2.py`: không kênh nào khai `dang`), tức là không dùng tới
// `dang`/`ngoi`/`di` — thứ duy nhất `DienVienHai` không có.
import { DienVienHai } from "../v4/DienVienHai";

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
  // 30/8 — DẢI ZOOM SIẾT HẲN sau khi chuyển sang bố cục người-dẫn-ở-góc.
  // Trong bố cục cũ (toàn thân, giữa khung) thì zoom 0,8–1,5 là hợp lý. Nay người dẫn đã được
  // đặt cận sẵn ở góc, nên cùng dải ấy làm cỡ RỘNG đẩy nhân vật tràn hẳn ra mép trái — đo được
  // trên khung mở của FINE PRINT: mất nửa khuôn mặt.
  // Người dẫn không cần "toàn cảnh": bối cảnh đã là ảnh nền full khung rồi, máy quay chỉ còn
  // một việc là nhấn nhá quanh khuôn mặt. Dải 0,96–1,18 đủ để thấy nhịp mà không phá bố cục.
  rong: { x: 0, y: -120, z: 0.96 },      // hơi lùi — thấy rộng bối cảnh hơn
  trung: { x: 0, y: -150, z: 1.06 },     // mặc định
  can: { x: 0, y: -230, z: 1.18 },       // siết vào mặt: mắt, chân mày, khoé miệng
};

export type Canh = {
  dich?: number;                  // xê dịch chỗ đứng của cảnh này (điểm)
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
  noiBat?: number;           // cột nào được tô sáng — đổi theo câu đang nói
  sfx?: string;              // tệp tiếng động trong public/
};

export type PropsKich = {
  canh?: Canh[];
  tu?: Tu[];                 // mốc thời gian từng từ (edge-tts WordBoundary)
  voMp3?: string;
  nhac?: string;
  doVat?: string;                // đạo cụ cầm tay — nói ngay kênh này về gì (xem `DoVat`)
  nenAnh?: string;               // ảnh nền AI đã cache; rỗng thì lui về bối cảnh vector
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
      {/* TẤM NỀN MỜ SAU CON SỐ. Anh cắt khung DEEP FIELD: "443 m / 221455" nằm đè lên đầu
          nhân vật ở cỡ cận. Con số không thể tránh nhân vật (nó đứng yên, nhân vật thì phóng
          theo máy quay), nên cách chắc chắn là cho nó một nền riêng để luôn đọc được. */}
      <rect x={-330} y={-84} width={660} height={nhan ? 168 : 122} rx={20}
            fill="#FBF6EA" opacity={0.86 * vao} stroke={mau.muc} strokeWidth={5} />
      <text x={0} y={0} textAnchor="middle" fontSize={124} fontWeight={900}
            fill={mau.nhan} stroke={mau.muc} strokeWidth={9} paintOrder="stroke"
            style={{ fontVariantNumeric: "tabular-nums" }}>{hien}</text>
      {/* 29/8 — CẮT THEO TỪ, KHÔNG CẮT GIỮA CHỮ. Khung demo: "MIDWEST POULTRY SE",
          "COURT OF APPEALS F", "ARTIFICIAL INTELLI" — cả ba đều đứt ngang một chữ và đọc ra như
          lỗi phần mềm. Nhãn nằm ngay dưới con số lớn nhất khung, tức chỗ mắt dừng lâu nhất.
          CHÚ THÍCH PHẢI NẰM NGOÀI biểu thức ba ngôi. Đặt một khối chú thích JSX ngay sau dấu
          hỏi của toán tử ba ngôi là cú pháp SAI: dấu ngoặc nhọn ở vị trí đó mở một object
          literal chứ không mở một chú thích.
          Và lần vá đầu tôi còn viết nguyên cái cú pháp hỏng ấy VÀO TRONG chú thích này — chuỗi
          đóng khối nằm giữa câu văn nên chú thích tự kết thúc sớm, đẻ ra một lỗi thứ hai ngay
          trong lời giải thích về lỗi thứ nhất.
          Đáng ghi vì bán kính sát thương: Remotion gói MỌI composition vào MỘT bundle, nên một
          tệp thế hệ 3 hỏng cú pháp làm CẢ 50 KÊNH thế hệ 2 không render được. */}
      {nhan ? (
        <text x={0} y={62} textAnchor="middle" fontSize={38} fontWeight={800}
              fill={mau.muc} opacity={0.86} letterSpacing={1.5}>
          {(() => {
            const t = String(nhan).toUpperCase().trim();
            if (t.length <= 20) return t;
            const tu = t.split(" ");
            const ra: string[] = [];
            for (const w of tu) {
              if ([...ra, w].join(" ").length > 20) break;
              ra.push(w);
            }
            return (ra.join(" ") || t.slice(0, 20)).replace(/[ ,;:-]+$/, "");
          })()}
        </text>
      ) : null}
    </g>
  );
};

/** Biểu đồ cột làm ĐẠO CỤ trong cảnh — mọc lên từ đáy, so được bằng mắt. */
const CotDaoCu: React.FC<{ cot: NonNullable<Canh["cot"]>; p: number; mau: Paltte; noiBat?: number }> = ({ cot, p, mau, noiBat = 0 }) => {
  // ══════════════════════════════════════════════════════════════════════════════════════
  // BIỂU ĐỒ PHẢI CÓ TẤM NỀN RIÊNG
  // --------------------------------------------------------------------------------------
  // 29/8 — anh cắt năm chỗ trong khung và ba trong số đó là cùng một bệnh: chữ của biểu đồ
  // nằm THẲNG TRÊN bối cảnh. Trên kệ sách thư phòng, nhãn "Breach Of Contract" đè lên gáy sách
  // nhiều màu; trên kệ siêu thị, "EQUIFAX INC" đè lên hộp hàng. Chữ đen trên nền lộn xộn thì
  // không đọc được, và người xem đọc ra là LỖI chứ không đọc ra là dữ liệu.
  // Cách chữa đúng không phải đổi màu chữ mà là DỰNG MỘT TẤM NỀN: mọi biểu đồ trong đời thật
  // đều nằm trên một mặt phẳng của riêng nó — tờ giấy, tấm bảng, màn hình. Thiếu tấm nền ấy thì
  // biểu đồ trông như bị dán đè lên cảnh.
  //
  // NHÃN CHÂN CỘT CŨNG PHẢI VỪA CHỖ. Bản cũ cắt 10 ký tự rồi xếp hai dòng, nhưng bề rộng chữ
  // không tính bằng số ký tự: "MIDWEST C/O" và "Bazzini LLC" cùng 11 ký tự mà rộng khác nhau
  // hẳn, nên bốn nhãn dính thành một vệt. Nay tính theo BỀ RỘNG THẬT (ước lượng 0,55 lần cỡ
  // chữ mỗi ký tự) và cắt cho vừa đúng bề ngang một cột.
  const N = Math.min(4, cot.length);
  const BUOC = 112, RONG = 84, CAO = 300;
  const dinh = Math.max(1, ...cot.slice(0, N).map((c) => c.gt));
  const nenX = -26, nenY = -CAO - 96, nenW = BUOC * N + 40, nenH = CAO + 176;

  /** Cắt chuỗi cho vừa `px` điểm ở cỡ chữ `cs`, cắt theo TỪ, tối đa 2 dòng. */
  const chiaDong = (t: string, px: number, cs: number): string[] => {
    const rong = (x: string) => x.length * cs * 0.55;
    // MỘT TỪ DÀI HƠN CẢ CỘT thì xuống dòng không cứu được — phải cắt chính từ đó.
    // Cây thước bắt ba ca thật: "Non-Compete Agreement" (109 điểm), "Wrongful Termination"
    // (109), "Artificial Intelligenc" (119), trong khi cột chỉ rộng 100. Xuống dòng chỉ đẩy
    // từ ấy sang dòng dưới rồi nó vẫn tràn y nguyên.
    const catTu = (w: string) => {
      if (rong(w) <= px) return w;
      const n = Math.max(3, Math.floor(px / (cs * 0.55)) - 1);
      return w.slice(0, n) + "…";
    };
    const tu = String(t || "").split(" ").filter(Boolean).map(catTu);
    const d: string[] = ["", ""];
    let k = 0;
    for (const w of tu) {
      const thu = d[k] ? d[k] + " " + w : w;
      if (rong(thu) <= px) { d[k] = thu; continue; }
      if (k === 0) { k = 1; d[1] = w; continue; }
      break;
    }
    if (!d[0]) d[0] = catTu(String(t || ""));
    return d.filter(Boolean);
  };

  return (
    <g transform="translate(30 150)">
      {/* TẤM NỀN — giấy kem mờ, viền dày, bo góc. Đây là thứ tách biểu đồ khỏi bối cảnh. */}
      <rect x={nenX} y={nenY} width={nenW} height={nenH} rx={18}
            fill="#FBF6EA" stroke={mau.muc} strokeWidth={6} />
      {/* đường chân cột, để cột có chỗ đứng thay vì lơ lửng */}
      <line x1={nenX + 12} y1={2} x2={nenX + nenW - 12} y2={2}
            stroke={mau.muc} strokeWidth={5} opacity={0.55} />
      {cot.slice(0, N).map((c, i) => {
        const moc = muot(kep((p - i * 0.07) / 0.3));
        const h = (c.gt / dinh) * CAO * moc;
        const sang = i === noiBat;
        return (
          <g key={i} transform={`translate(${i * BUOC} 0)`}>
            <rect x={0} y={-h - (sang ? 10 : 0)} width={RONG} height={h + (sang ? 10 : 0)}
                  rx={8} fill={sang ? mau.nhan : "#F2C230"}
                  stroke={mau.muc} strokeWidth={sang ? 7 : 5} />
            <text x={RONG / 2} y={-h - 24 - (sang ? 10 : 0)} textAnchor="middle"
                  fontSize={sang ? 34 : 28} fontWeight={900}
                  fill={mau.muc} opacity={moc}>{c.hien}</text>
            {chiaDong(c.nhan, BUOC - 12, 18).map((d, j) => (
              <text key={j} x={RONG / 2} y={30 + j * 21} textAnchor="middle" fontSize={18}
                    fontWeight={700} fill={mau.muc} opacity={0.85 * moc}>{d}</text>
            ))}
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
  const dau = Math.max(0, (tam < 0 ? tu.length : tam) - 2);
  // 29/8 — SÁU TỪ, XUỐNG HAI DÒNG. Bản đầu đổ chín từ lên MỘT dòng và nó chạy tràn cả hai mép
  // khung. SVG `<text>` KHÔNG tự xuống dòng — không có thuộc tính nào bảo nó làm thế — nên phải
  // tự cắt dòng. Sáu từ là vừa đủ để mắt bắt kịp ở tốc độ đọc 2,5 từ/giây mà không phải liếc.
  const doan = tu.slice(dau, dau + 6);
  const nua = Math.ceil(doan.length / 2);
  const dong = [doan.slice(0, nua), doan.slice(nua)];
  return (
    <g transform={`translate(0 ${day})`}>
      {dong.map((d, j) => (
        <text key={j} x={0} y={j * 56} textAnchor="middle" fontSize={44} fontWeight={900}
              stroke={mau.muc} strokeWidth={9} paintOrder="stroke" fill="#FFFFFF">
          {/* 29/8 — SVG NUỐT KHOẢNG TRẮNG CUỐI. Anh cắt khung: "numberherecomes", "NASA Center
              for" dính liền. Viết `{w.w} ` thì dấu cách nằm ở CUỐI nội dung tspan, và trình
              duyệt gộp khoảng trắng ở mép phần tử theo mặc định — nên nó biến mất sạch.
              Đẩy dấu cách vào GIỮA hai từ (tiền tố từ thứ hai trở đi) thì nó nằm trong lòng nội
              dung và không bị gộp. */}
          {d.map((w, i) => (
            <tspan key={i} fill={k >= 0 && tu[k] === w ? mau.nhan : "#FFFFFF"}>
              {(i ? " " : "") + w.w}
            </tspan>
          ))}
        </text>
      ))}
    </g>
  );
};

export const KichV2: React.FC<PropsKich> = ({
  canh = [], tu = [], voMp3 = "", nhac = "", doVat = "", nenAnh = "", kieu = {}, kieuGoc = "nam_dam",
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

  // Nền tối hay sáng — suy từ chính bảng màu, không khai tay ở mười chỗ.
  const _lum = (hx: string) => {
    const h = hx.replace("#", "");
    const r = parseInt(h.slice(0, 2), 16) / 255, g = parseInt(h.slice(2, 4), 16) / 255,
          b = parseInt(h.slice(4, 6), 16) / 255;
    const f = (c: number) => (c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const _nenToi = _lum(mau.troi[1]) < 0.16;

  const noi = visemeTai(tu, giay, CAM_XUC[C.camXuc || "trung_tinh"].ha);
  const nhin = C.nhin || [0, 0];

  // 29/8 — VIEWBOX PHẢI CÙNG TỈ LỆ VỚI KHUNG XUẤT.
  // Khung demo: tiêu đề và phụ đề đều bị cắt cụt hai mép ("...your bank actually healthy",
  // "...he clause they hope you ski"). Không phải chữ dài quá — mà `preserveAspectRatio="slice"`
  // PHÓNG ĐỂ LẤP ĐẦY rồi cắt phần thừa. Khung dọc 1080×1920 có tỉ lệ 0,5625 còn viewBox
  // 1000×1500 có tỉ lệ 0,667, nên nó cắt mất hai bên — đúng chỗ chữ nằm.
  // Cho viewBox đúng tỉ lệ khung thì không còn gì để cắt: dọc 1000×1778, ngang 1640×922.
  const _cao = Math.round(1000 * (height / width));
  const vb = doc ? `-500 ${-Math.round(_cao * 0.47)} 1000 ${_cao}`
                 : `-820 ${-Math.round(1640 * (height / width) * 0.5)} 1640 ${Math.round(1640 * (height / width))}`;

  return (
    <AbsoluteFill style={{ background: mau.troi[1], fontFamily: font || "Poppins, Arial, sans-serif" }}>
      {/* LỚP ẢNH NỀN — nằm dưới cùng, và PHẢI trong `AbsoluteFill` riêng: thẻ `<svg>` bên dưới là
          phần tử TĨNH, mà luật vẽ của CSS cho phần tử-có-định-vị vẽ SAU nội dung tĩnh. Đặt ảnh
          trong một lớp định vị rồi đặt svg trong một lớp khác thì thứ tự viết trong JSX mới là
          thứ tự vẽ (đã trả giá một lần ở bộ hài — luật 7t mục 1). */}
      {nenAnh ? (
        <AbsoluteFill style={{ overflow: "hidden" }}>
          <Img src={staticFile(nenAnh)}
               style={{ width: "100%", height: "100%", objectFit: "cover",
                        transform: `scale(${1.04 + (giay / Math.max(1, canh.length ? Math.max(...canh.map((c) => c.e)) : 20)) * 0.05})`,
                        filter: "saturate(1.02) brightness(1.03)" }} />
          {/* Lớp phủ ĐẬM HƠN bộ hài. Bộ này có BIỂU ĐỒ và SỐ LIỆU đè lên nền; nền ảnh nhiều chi
              tiết làm chữ số khó đọc, mà đọc được số mới là toàn bộ giá trị của mười kênh này. */}
          <AbsoluteFill style={{ background:
            `linear-gradient(180deg,${mau.troi[1]}66 0%,${mau.troi[1]}33 45%,${mau.dat}88 100%)` }} />
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill>
      <svg viewBox={vb} width="100%" height="100%" preserveAspectRatio="xMidYMid slice">
        <g transform={`translate(${-cam.x + rung} ${-cam.y}) scale(${cam.z})`}
           style={{ transformOrigin: "0px 0px" }}>
          {/* ══ NỀN: ẢNH AI TRƯỚC, VECTOR LÀ LỚP LUI ═══════════════════════════════════
              30/8 — Anh: *"tham khảo nâng cấp phần bối cảnh"*. Đúng chỗ yếu nhất: bối cảnh vector
              của bộ này chỉ là vài mảng màu và mấy hình khối, trong khi bộ hài đã chạy nền ảnh AI
              cache và khung đẹp hơn hẳn. Cùng một dàn nhân vật mà hai bộ trông như hai mức đầu tư.
              Ảnh vẽ MỘT LẦN rồi cache vĩnh viễn (`kich_v2.py --nen`), nên từ video thứ hai trở đi
              không tốn một lượt vẽ nào — cùng cách đã đo được ở bộ hài.
              Giữ `BoiCanh` vector làm lớp lui: ngày kho khoá vẽ cạn thì kênh vẫn ra video, chỉ là
              nền đơn giản hơn. Không bao giờ để một kênh câm chỉ vì thiếu ảnh. */}
          {nenAnh ? null : <BoiCanh ten={C.boi || "san_sau"} mau={mau} t={giay} />}

          {/* ══ NGƯỜI DẪN ĐỨNG MỘT GÓC, CẮT NGANG HÔNG — dựng lại 30/8/2026 ═════════════
              Anh gửi ba khung và chỉ ra ba lỗi, cả ba đều do một nguyên nhân: cho nhân vật đứng
              TOÀN THÂN giữa khung rồi bắt nó xê dịch và giơ tay.
                · chân đứng lơ lửng trên nóc tủ hồ sơ — nền là ẢNH, mà ảnh thì sàn nằm ở đâu là
                  tuỳ tấm; đặt chân theo một con số cố định thì sớm muộn cũng trúng mặt bàn;
                · tay giơ cao che mất thẻ số ở đỉnh khung;
                · càng cho xê dịch nhiều thì càng nhiều chỗ sai.
              Anh chỉ luôn cách chữa, và nó gọn hơn hẳn mọi bản vá tôi định làm: *"làm kiểu nhân
              vật ở 1 góc màn hình nói phân tích, chỉ cử động tay và miệng mắt, biểu cảm khuôn
              mặt thôi, còn ảnh bối cảnh làm như ảnh nền videos"*.
              Đặt người dẫn ở góc trái và ĐẨY XUỐNG cho mép khung cắt ngang hông thì:
                · KHÔNG CÒN CHÂN trong khung, nên không còn bài toán chân-chạm-sàn — lỗi lơ lửng
                  biến mất hoàn toàn thay vì được vá;
                · mặt to gần gấp rưỡi, nên khẩu hình và biểu cảm đọc rõ — đó mới là thứ đáng xem
                  ở một kênh phân tích;
                · nửa phải khung trống hẳn cho biểu đồ và số liệu.
              Đây là bố cục của mọi video giải thích có người dẫn, và nó đúng vì lý do vật lý chứ
              không phải vì thẩm mỹ: thứ gì không nằm trong khung thì không thể sai. */}
          <DienVienHai
            kieu={nv}
            camXuc={C.camXuc || "trung_tinh"}
            cuChi={C.cuChi || "nghi"}
            nhin={nhin}
            noi={noi}
            t={giay}
            doVat={doVat}
            /* TẮT KÝ HIỆU CẢM XÚC KIỂU TRUYỆN TRANH. Chùm gân đỏ "điên tiết", giọt mồ hôi
               "chột dạ" là ngôn ngữ HÀI; dán lên một kênh kể số liệu ngân hàng thì kênh ấy mất
               vẻ đáng tin — mà đáng tin là toàn bộ giá trị của mười kênh này.
               Anh dặn rõ: mượn CÁCH LÀM của bộ hài, không mượn chất hài. */
            kyHieu={false}
            // 29/8 — CỠ NHÂN VẬT TÍNH THEO KHUNG, KHÔNG BỐC MỘT SỐ.
            // Con rối vẽ trong hệ cao ~420 đơn vị (từ đỉnh đầu tới gót). Khung dọc cao 1500 đơn
            // vị, nên tỉ lệ 1.12 cho ra một người cao 470/1500 — lọt thỏm, đúng như khung render
            // thử. Muốn nhân vật chiếm khoảng 3/5 chiều cao (tỉ lệ quen thuộc của phim hoạt hình
            // kể chuyện) thì cần ~2.1 cho khung dọc và ~1.6 cho khung ngang.
            x={doc ? -158 : -330}
            y={doc ? 1240 : 820}
            // 29/8 lần hai — lần trước tôi tăng cỡ nhân vật 1.12->2.1 NHƯNG cùng lúc hạ zoom
            // máy quay 1.5->1.0. Tích hai số không đổi (1.68), nên khung render ra y hệt và tôi
            // suýt kết luận "sửa không ăn". Bài học: đổi hai hệ số nhân với nhau trong cùng một
            // lượt thì không đo được cái nào có tác dụng.
            scale={doc ? 4.0 : 2.6}
          />
        </g>

        {/* 29/8 — SỐ TO PHẢI NẰM NGOÀI NHÓM MÁY QUAY.
            Khung render đầu: "3,797" phóng to theo cỡ cận và đè thẳng lên mặt nhân vật — đúng
            lỗi chồng chữ anh dặn tránh. Con số là lớp THÔNG TIN, không phải vật trong cảnh; nó
            phải đứng yên ở một chỗ cố định trên màn hình bất kể máy quay đi đâu. */}
        {/* 29/8 — BIỂU ĐỒ CŨNG PHẢI RA KHỎI NHÓM MÁY QUAY.
            Anh cắt ba khung: cột thứ ba và thứ tư cùng nhãn của chúng bị cắt cụt ở mép phải.
            Vì biểu đồ nằm TRONG nhóm máy quay nên nó phóng to theo cỡ cận (×1,5) rồi tràn ra
            ngoài khung. Cùng đúng cái lỗi đã sửa cho con số lớn hôm qua mà tôi không nghĩ tới
            biểu đồ: cả hai đều là LỚP THÔNG TIN, không phải vật trong cảnh, nên phải đứng yên
            một chỗ bất kể máy quay đi đâu. */}
        {/* Vị trí biểu đồ chỉnh bằng PHÉP ĐO trên khung đã render, không bằng phép tính: chuỗi
            biến đổi lồng ba tầng (nhóm bọc → nhóm trong → viewBox) làm tôi tính lệch ba lần.

            VÀ CHÚ THÍCH PHẢI Ở ĐÂY, TRƯỚC dấu `{`. Đây là lần THỨ BA trong ngày tôi đặt một khối
            chú thích JSX ngay sau dấu hỏi của toán tử ba ngôi, và cả ba lần esbuild đều ném
            "Expected ) but found transform" — vì ở vị trí đó nó là CON THỨ HAI bên cạnh thẻ <g>,
            mà một nhánh ba ngôi chỉ nhận một biểu thức. Hai lần trước tôi đã ghi lại bài học rồi
            vẫn tái phạm, nên lần này ghi ngay tại chỗ dễ sai nhất. */}
        {C.cot ? (
          <g transform={`translate(${doc ? 96 : 170} ${doc ? 150 : 96}) scale(${doc ? 0.86 : 0.78})`}>
            <CotDaoCu cot={C.cot} p={p} mau={mau} noiBat={C.noiBat ?? 0} />
          </g>
        ) : null}
        {C.soLon ? (
          <g transform={`translate(${doc ? 150 : 190} ${doc ? -430 : -330})`}>
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
        {/* 29/8 — DÒNG NGUỒN PHẢI ĐỔI MÀU THEO NỀN. Trên hai kênh vũ trụ (nền tím than) dòng
            "Source: NASA/JPL…" vẽ bằng màu mực sẫm nên chìm hẳn, gần như không nhìn thấy.
            Uy tín của cả bộ kênh nằm ở chỗ số liệu tra được — mà dòng chỉ ra nơi tra thì lại là
            thứ duy nhất người xem không đọc nổi.
            Chọn màu theo ĐỘ SÁNG của nền: nền tối thì chữ sáng, nền sáng thì chữ mực. */}
        {nguon ? (
          <text x={0} y={doc ? 790 : 500} textAnchor="middle" fontSize={22} fontWeight={700}
                fill={_nenToi ? "#FFFFFF" : mau.muc} opacity={_nenToi ? 0.72 : 0.5}>
            Source: {nguon}
          </text>
        ) : null}
      </svg>
      </AbsoluteFill>

      {voMp3 ? <Audio src={staticFile(voMp3)} /> : null}
      {/* 30/8 — mức 0,1 quá nhỏ để nghe trên loa điện thoại; cùng phép đo đã làm cho bộ hài
          (mức 0,07 cho đỉnh −32 dB, gần như im lặng). 0,18 nghe rõ là có nền mà vẫn thấp hơn
          hẳn giọng đọc. `loop` vì nhạc nền ngắn hơn video. */}
      {nhac ? <Audio src={staticFile(nhac)} volume={0.18} loop /> : null}
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
