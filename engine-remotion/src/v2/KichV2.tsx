import React from "react";
// 31/8 — Anh chỉ vào ảnh bản đồ nước Mỹ và hỏi đã tích hợp chưa. Chưa — nên thêm, và dùng lại
// đúng bộ đã có sẵn trong bundle (MappedShort dùng chung ba thứ này), không kéo thêm gói nào.
import { geoAlbersUsa, geoPath } from "d3-geo";
import { feature as _feature } from "topojson-client";
import _statesTopo from "../../public/geo/states-10m.json";
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
  nenTheoCanh?: string[];        // một nền cho mỗi cảnh — đổi theo đoạn nội dung
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
// ══ BỐ CỤC DỌC: NHÂN VẬT GÓC TRÁI, CHART CHIẾM PHẦN CÒN LẠI ═══════════════════════════════
// Anh: *"nhân vật nên nhỏ chỉ bằng 50-60% hiện tại thôi, sát góc trái"* — nên cỡ hạ từ 2,5 xuống
// 1,42 (57%). Người hẹp lại thì khoảng trống bên phải rộng ra, và chart phải lấy đúng phần rộng
// ra ấy chứ không phải giữ nguyên rồi để thừa.
// Ba số dưới đây suy ra nhau, không phải ba số chỉnh tay độc lập — đó là lý do bản trước sai:
// mỗi lần đổi một số lại phải nhớ đi sửa hai số kia, và có lần quên.
const VB_PHAI = 500;              // mép phải viewBox dọc
const NGUOI_DAU = 470;            // đỉnh đầu nhân vật ở cỡ 1,42 — soi khung đo được
const LE = 22;                    // khe hở để chart không dính người và không dính mép khung
const CHART_RONG_GOC = 488;       // bề rộng tấm nền bốn cột trong hệ toạ độ riêng của nó
const CHART_DAY_GOC = 230;        // mép dưới tấm nền, tính từ gốc nhóm của nó
const CHART_Y = 120;
// Soi khung xong mới thấy tôi đã ràng buộc NHẦM TRỤC. Nhân vật chỉ chiếm góc DƯỚI trái — phần
// trên bên trái bỏ trống hoàn toàn — nên chiều ngang không phải thứ giới hạn biểu đồ. Thứ giới
// hạn là CHIỀU CAO: mép dưới bảng phải nằm trên đỉnh đầu nhân vật.
// Ràng theo đúng trục ấy thì bảng rộng ra được một phần tám và trải gần hết bề ngang khung,
// thay vì co lại tránh một người mà nó vốn không hề chạm tới.
const CHART_CO = Math.min((NGUOI_DAU - LE - CHART_Y) / CHART_DAY_GOC,
                          (2 * VB_PHAI - 2 * LE) / CHART_RONG_GOC);
const CHART_TAM = 26;             // nhích phải một chút: mắt người đọc từ trái, chừa lối vào

// ══ BIỂU ĐỒ PHẢI CÓ HƠN MỘT DÁNG ═══════════════════════════════════════════════════════════
// 30/8 — Anh: *"chart dữ liệu đang bị lặp đi lặp lại hơi nhàm chán"*. Đúng: sáu mươi kênh, mỗi
// kênh nhiều tập, tất cả dùng CHUNG một dáng cột dọc vàng-với-một-cột-đỏ. Xem hai video liền
// nhau là thấy cùng một hình, chỉ đổi con số.
//
// Nhưng đa dạng không phải là đổi dáng ngẫu nhiên cho vui. Mỗi dáng giải một bài toán riêng, và
// chọn đúng dáng làm số liệu DỄ ĐỌC HƠN chứ không chỉ mới mắt hơn:
//   · CỘT DỌC  — mặc định, tốt khi nhãn ngắn và các giá trị cùng bậc;
//   · CỘT NGANG — khi nhãn DÀI: chữ chạy ngang theo cột nên không phải xuống dòng hay cắt cụt,
//                 đúng chỗ đau của những nguồn có tên sản phẩm dài;
//   · CHẤM-QUE  — khi một giá trị vượt trội hẳn: cột dọc lúc ấy biến ba cột kia thành ba vạch
//                 sát đáy, còn chấm-que giữ được vị trí đọc được cho mọi mục.
// Nên luật chọn đọc DỮ LIỆU trước, và chỉ khi dữ liệu không đòi hỏi gì thì mới lấy dáng cố định
// của kênh — để mỗi kênh vẫn có một bộ mặt quen thuộc.
// 31/8 — Anh: *"vẫn nói + chart + nền mờ, lặp đi lặp lại, còn gì đa dạng hơn không"*.
// Có, và không cần bỏ nhân vật hay bỏ nền — anh đã nói rõ là muốn GIỮ hai thứ ấy. Chỗ còn đơn
// điệu là LOẠI biểu đồ: ba dáng cột/thanh/chấm đều là cùng một ý tưởng "so chiều dài".
// Thêm ba loại nói bằng ngôn ngữ hình khác hẳn:
//   khoi   — ô vuông to nhỏ theo giá trị: mắt so DIỆN TÍCH, hợp khi chênh lệch lớn
//   thehai — hai tấm thẻ lớn đối đầu, đỉnh so đáy: hợp khi câu chuyện là một khoảng cách
//   vong   — vòng tròn chia phần: hợp khi các mục cộng lại thành một tổng thể
// 31/8 — Anh gửi ảnh tham khảo phong cách motion-graphics dữ liệu và hỏi vẽ được không.
// Được, và chúng nói bằng ngôn ngữ hình KHÁC HẲN sáu dạng trên (vốn đều quy về "so chiều dài"
// hoặc "so diện tích"):
//   luoi  — lưới ô sáng/tắt: "bao nhiêu trong tổng số", đọc ngay mà không cần trục
//   thuoc — khung thước kiểu bản vẽ kỹ thuật: đo MỘT đại lượng, hợp cho một con số duy nhất
//   diem  — điểm phân tán trên nền kẻ ô: mật độ thay cho chiều dài, hợp cho số rất lớn
// Cả ba vẫn nằm trong khung có người dẫn và nền mờ — anh muốn giữ hai thứ đó.
type DangChart = "dung" | "ngang" | "cham" | "khoi" | "thehai" | "vong" | "luoi" | "thuoc" | "diem" | "bando";

const chonDang = (cot: { nhan: string; gt: number }[], kenhSo: number): DangChart => {
  const n = Math.min(4, cot.length);
  if (!n) return "dung";
  const dai = Math.max(...cot.slice(0, n).map((c) => (c.nhan || "").length));
  const gt = cot.slice(0, n).map((c) => c.gt).sort((a, b) => b - a);
  // 31/8 — CHỌN THEO DỮ LIỆU TRƯỚC, XOAY THEO KÊNH SAU.
  // Mỗi loại hình nói tốt một kiểu quan hệ; ép sai loại thì biểu đồ đúng số mà vẫn khó đọc:
  //   · đỉnh vượt xa phần còn lại  -> chấm trên thang (cột sẽ dẹp lép hết)
  //   · chỉ hai mục                -> hai thẻ đối đầu (hai cột trơ trọi không thành bảng)
  //   · các mục là phần trăm       -> vòng chia phần (chúng cộng lại thành một tổng thể)
  //   · nhãn dài                   -> thanh ngang (nhãn nằm ngang mới đủ chỗ)
  // Chỉ khi dữ liệu không đòi hỏi gì riêng thì mới xoay theo băm kênh — và xoay trong SÁU loại
  // chứ không phải ba, nên hai kênh cạnh nhau hiếm khi trùng bộ mặt.
  if (gt.length > 1 && gt[1] > 0 && gt[0] / gt[1] > 3.5) return "cham";
  // Bản đồ chỉ dùng khi nhãn ĐÚNG LÀ tên bang — vẽ bản đồ cho dữ liệu không theo bang thì
  // hình đẹp mà nói sai, tệ hơn một cái cột tẻ nhạt.
  const _BANG = ["california", "texas", "florida", "new york", "illinois", "ohio", "arizona",
                 "nevada", "oregon", "washington", "georgia", "michigan", "virginia",
                 "colorado", "delaware", "alaska", "hawaii", "utah", "maine", "iowa"];
  if (cot.length >= 3 && cot.slice(0, 3).every((c) => _BANG.includes(String(c.nhan).trim().toLowerCase())))
    return "bando";
  if (cot.length === 2) return "thehai";
  const _phan = cot.slice(0, n).every((c) => /%/.test(String(c.nhan)) || /%/.test(String((c as any).hien || "")));
  if (_phan && cot.length >= 3) return "vong";
  if (dai > 14) return "ngang";
  return (["dung", "ngang", "cham", "khoi", "thehai", "vong", "luoi", "thuoc", "diem"] as DangChart[])[kenhSo % 9];
};

const CotNgang: React.FC<{ cot: NonNullable<Canh["cot"]>; p: number; mau: Paltte; noiBat: number;
                           pCua?: (i: number) => number }> =
({ cot, p, mau, noiBat, pCua }) => {
  const _p = pCua || (() => p);
  // Nhãn chạy NGANG theo thanh nên không phải xuống dòng hay cắt cụt — đúng chỗ đau của những
  // nguồn có tên sản phẩm dài. Đổi lại chỉ hiện được bốn mục, nên chỉ dùng khi nhãn thật sự dài.
  const N = Math.min(4, cot.length);
  // 30/8 — anh gửi khung: nhãn "Family Brands" đè lên thanh phía trên. Tính lại thì đúng: chữ
  // cỡ 19 đặt ở y = −6 kéo lên tới −25, mà thanh của mục trước kết thúc ở −20. Đè 5 điểm.
  // Lỗi tôi vừa tạo lúc thêm dáng này: đặt nhãn NGAY TRÊN thanh mà quên chữ có chiều cao.
  const DAI = 380, DAY = 52, BUOC = 92;
  const dinh = Math.max(1, ...cot.slice(0, N).map((c) => c.gt));
  const nenX = -250, nenY = -54, nenW = 500, nenH = BUOC * N + 46;
  return (
    <g transform={`translate(0 ${-nenH / 2 + 40})`}>
      <rect x={nenX} y={nenY} width={nenW} height={nenH} rx={18}
            fill="#FBF6EA" stroke={mau.muc} strokeWidth={6} />
      {cot.slice(0, N).map((c, i) => {
        const moc = muot(kep((_p(i) - i * 0.07) / 0.3));
        const w = (c.gt / dinh) * DAI * moc;
        const sang = i === noiBat;
        return (
          <g key={i} transform={`translate(${-232} ${i * BUOC})`}>
            <text x={0} y={-13} fontSize={19} fontWeight={800} fill={mau.muc}
                  opacity={0.9 * moc}>{c.nhan}</text>
            <rect x={0} y={2} width={Math.max(2, w)} height={DAY} rx={7}
                  fill={sang ? mau.nhan : "#F2C230"} stroke={mau.muc}
                  strokeWidth={sang ? 6 : 4} />
            {/* 30/8 — anh gửi khung "1262 cal" bị một đường dọc chặt đôi. Đường ấy là mép tấm
                nền: số đặt SAU thanh, mà thanh dài thì số đẩy ra ngoài khung.
                Chỗ đặt số phải phụ thuộc CÒN BAO NHIÊU CHỖ, không phải luôn đặt sau thanh.
                Thanh dài thì số vào NẰM TRONG thanh (đổi sang màu nền cho đọc được); thanh
                ngắn thì giữ nguyên bên ngoài. */}
            {(() => {
              const _w = Math.max(2, w);
              const _rongChu = String(c.hien || "").length * (sang ? 16 : 13);
              const _trong = _w + 12 + _rongChu > DAI - 6;
              return (
                <text x={_trong ? _w - 10 : _w + 12} y={DAY * 0.72}
                      textAnchor={_trong ? "end" : "start"}
                      fontSize={sang ? 30 : 25} fontWeight={900}
                      fill={_trong ? "#FBF6EA" : mau.muc} opacity={moc}>{c.hien}</text>
              );
            })()}
          </g>
        );
      })}
    </g>
  );
};

const ChamQue: React.FC<{ cot: NonNullable<Canh["cot"]>; p: number; mau: Paltte; noiBat: number;
                          pCua?: (i: number) => number }> =
({ cot, p, mau, noiBat, pCua }) => {
  const _p = pCua || (() => p);
  // Khi một giá trị vượt trội hẳn, cột dọc biến ba mục kia thành ba vạch sát đáy. Chấm-que giữ
  // được vị trí đọc được cho mọi mục vì cái mắt đọc là CHẤM, không phải diện tích cột.
  const N = Math.min(5, cot.length);
  const BUOC = 62, DAI = 400;
  const dinh = Math.max(1, ...cot.slice(0, N).map((c) => c.gt));
  const nenX = -250, nenY = -40, nenW = 500, nenH = BUOC * N + 46;
  return (
    <g transform={`translate(0 ${-nenH / 2 + 34})`}>
      <rect x={nenX} y={nenY} width={nenW} height={nenH} rx={18}
            fill="#FBF6EA" stroke={mau.muc} strokeWidth={6} />
      {cot.slice(0, N).map((c, i) => {
        const moc = muot(kep((_p(i) - i * 0.06) / 0.28));
        const x = (c.gt / dinh) * DAI * moc;
        const sang = i === noiBat;
        const y = i * BUOC + 16;
        return (
          <g key={i} transform={`translate(${-226} 0)`}>
            <text x={0} y={y - 12} fontSize={18} fontWeight={800} fill={mau.muc}
                  opacity={0.88 * moc}>{c.nhan}</text>
            <line x1={0} y1={y + 8} x2={Math.max(4, x)} y2={y + 8}
                  stroke={mau.muc} strokeWidth={sang ? 7 : 4} opacity={sang ? 0.9 : 0.42}
                  strokeLinecap="round" />
            <circle cx={Math.max(4, x)} cy={y + 8} r={sang ? 17 : 12}
                    fill={sang ? mau.nhan : "#F2C230"} stroke={mau.muc} strokeWidth={sang ? 6 : 4} />
            {/* 30/8 — anh gửi khung "2M km" bị mép phải chặt. Cùng một lỗi với dáng ngang mà
                tôi đã sửa lúc chiều: số đặt SAU chấm, chấm chạy tới cuối thanh thì số ra ngoài
                tấm nền. Tôi sửa dáng kia rồi quên dáng này.
                Nên lần này gộp phép tính chỗ đặt số thành MỘT quy tắc dùng chung: còn chỗ thì
                đặt sau, hết chỗ thì lùi vào trước — không dáng nào tự viết lại phép ấy. */}
            {(() => {
              const _x = Math.max(4, x);
              const _rong = String(c.hien || "").length * (sang ? 15 : 13);
              const _trong = _x + 26 + _rong > DAI + 10;
              return (
                // 31/8 — Anh gửi khung: "127.8K" và "105.4K" bị chính đường thang XUYÊN NGANG
                // qua giữa chữ. Con số vẽ ở đúng cao độ của đường, và khi nó lùi vào trước chấm
                // thì nằm chồng lên đoạn đường đã vẽ. Không phải lỗi vị trí — số ở đúng chỗ cần
                // ở; lỗi là hai lớp cùng cao độ mà không lớp nào nhường.
                // Cho chữ một viền dày màu nền tấm bảng và vẽ viền TRƯỚC (paintOrder): viền ấy
                // xoá một khoảng trống quanh từng chữ số, nên đường bị cắt gọn ở hai bên chữ.
                // Rẻ hơn nhiều so với đo bề rộng chữ để né, và không bao giờ lệch.
                <text x={_trong ? _x - 26 : _x + 26} y={y + 15}
                      textAnchor={_trong ? "end" : "start"}
                      fontSize={sang ? 27 : 23} fontWeight={900}
                      stroke="#FBF6EA" strokeWidth={8} paintOrder="stroke"
                      strokeLinejoin="round"
                      fill={mau.muc} opacity={moc}>{c.hien}</text>
              );
            })()}
          </g>
        );
      })}
    </g>
  );
};

/** Ô VUÔNG TỈ LỆ — mắt so diện tích thay vì so chiều dài. */
const KhoiVuong: React.FC<{ cot: NonNullable<Canh["cot"]>; p: number; mau: Paltte;
                            noiBat: number; pCua: (i: number) => number }> =
({ cot, p, mau, noiBat, pCua }) => {
  const N = Math.min(4, cot.length);
  const ds = cot.slice(0, N);
  const dinh = Math.max(1, ...ds.map((c) => c.gt));
  // Cạnh ô theo CĂN BẬC HAI của giá trị: diện tích mới là thứ mắt đọc, nên cạnh phải là căn.
  // Lấy cạnh tỉ lệ thẳng với giá trị thì ô lớn nhất trông to gấp bội lần sự thật.
  const canh = (g: number) => 60 + 130 * Math.sqrt(Math.max(0, g) / dinh);
  let x = -230;
  return (
    <g>
      <rect x={-268} y={-150} width={536} height={330} rx={18} fill="#FBF6EA"
            stroke={mau.muc} strokeWidth={6} />
      {ds.map((c, i) => {
        const pi = muot(kep(pCua(i)));
        const k = canh(c.gt) * pi;
        const sang = i === noiBat;
        const gx = x + k / 2;
        x += canh(c.gt) + 16;
        return (
          <g key={i} transform={`translate(${gx} 40)`}>
            <rect x={-k / 2} y={-k / 2} width={k} height={k} rx={10}
                  fill={sang ? mau.nhan : "#F2C230"} stroke={mau.muc} strokeWidth={sang ? 6 : 4} />
            <text x={0} y={6} textAnchor="middle" fontSize={Math.max(15, k * 0.19)}
                  fontWeight={900} fill={mau.muc} opacity={pi}>{c.hien}</text>
            <text x={0} y={k / 2 + 26} textAnchor="middle" fontSize={17} fontWeight={800}
                  fill={mau.muc} opacity={0.9 * pi}>{c.nhan}</text>
          </g>
        );
      })}
    </g>
  );
};

/** HAI THẺ ĐỐI ĐẦU — đỉnh bảng so với đáy bảng. Câu chuyện là KHOẢNG CÁCH, không phải thứ hạng. */
/** HAI THẺ CHỒNG DỌC — đỉnh bảng trên, đáy bảng dưới. Đọc từ trên xuống là thấy khoảng cách.
 *
 * 31/8 — Anh chỉ vào ảnh "1970 $0.28 / 2024 $2.74" xếp dọc và hỏi đã tích hợp chưa. Bản trước
 * tôi xếp NGANG với chữ "vs" ở giữa — đọc ra là một trận đấu, không phải một khoảng cách. Xếp
 * dọc thì mắt đi từ trên xuống và tự thấy chênh lệch, đúng cách ảnh ấy kể.
 * Thẻ trên tô đậm và số to hơn; thẻ dưới nhạt đi. Không cần mũi tên hay chữ "vs" nào.
 */
const TheDoiDau: React.FC<{ cot: NonNullable<Canh["cot"]>; p: number; mau: Paltte;
                            noiBat: number; pCua: (i: number) => number }> =
({ cot, p, mau, noiBat, pCua }) => {
  const a = cot[0];
  const b = cot[cot.length - 1] || cot[1] || cot[0];
  if (!a) return null;
  const the = (c: NonNullable<Canh["cot"]>[number], dy: number, i: number, tren: boolean) => {
    const pi = muot(kep(pCua(i)));
    return (
      <g transform={`translate(0 ${dy})`} opacity={pi}>
        <rect x={-244} y={-62} width={488} height={124} rx={14}
              fill={tren ? mau.nhan : "#F2C230"} stroke={mau.muc} strokeWidth={6} />
        <text x={-216} y={-24} fontSize={17} fontWeight={800}
              fill={tren ? "#FFFFFF" : mau.muc} opacity={0.92} letterSpacing={1.2}>
          {String(c.nhan).toUpperCase()}
        </text>
        <text x={-216} y={34} fontSize={tren ? 52 : 44} fontWeight={900}
              fill={tren ? "#FFFFFF" : mau.muc}>{c.hien}</text>
      </g>
    );
  };
  return (
    <g>
      <rect x={-282} y={-142} width={564} height={290} rx={18} fill="#FBF6EA"
            stroke={mau.muc} strokeWidth={6} />
      {the(a, -70, 0, true)}
      {the(b, 74, Math.min(cot.length - 1, 1), false)}
    </g>
  );
};

/** VÒNG CHIA PHẦN — hợp khi các mục cộng lại thành một tổng thể. */
const VongPhan: React.FC<{ cot: NonNullable<Canh["cot"]>; p: number; mau: Paltte;
                           noiBat: number; pCua: (i: number) => number }> =
({ cot, p, mau, noiBat, pCua }) => {
  const N = Math.min(5, cot.length);
  const ds = cot.slice(0, N);
  const tong = Math.max(1, ds.reduce((t, c) => t + Math.max(0, c.gt), 0));
  const MAU = ["#F2C230", "#E4572E", "#3B8EA5", "#7B6CD9", "#4C9A6B"];
  const R = 104, r = 58;
  let goc = -Math.PI / 2;
  return (
    <g>
      <rect x={-292} y={-150} width={584} height={310} rx={18} fill="#FBF6EA"
            stroke={mau.muc} strokeWidth={6} />
      <g transform="translate(-150 10)">
        {ds.map((c, i) => {
          const pi = muot(kep(pCua(i)));
          const phan = (Math.max(0, c.gt) / tong) * Math.PI * 2 * pi;
          const g0 = goc, g1 = goc + phan;
          goc += (Math.max(0, c.gt) / tong) * Math.PI * 2;
          const lon = phan > Math.PI ? 1 : 0;
          const d = [`M ${Math.cos(g0) * R} ${Math.sin(g0) * R}`,
                     `A ${R} ${R} 0 ${lon} 1 ${Math.cos(g1) * R} ${Math.sin(g1) * R}`,
                     `L ${Math.cos(g1) * r} ${Math.sin(g1) * r}`,
                     `A ${r} ${r} 0 ${lon} 0 ${Math.cos(g0) * r} ${Math.sin(g0) * r}`, "Z"].join(" ");
          return <path key={i} d={d} fill={i === noiBat ? mau.nhan : MAU[i % MAU.length]}
                       stroke={mau.muc} strokeWidth={4} />;
        })}
      </g>
      <g transform="translate(30 -66)">
        {ds.map((c, i) => (
          <g key={i} transform={`translate(0 ${i * 42})`} opacity={muot(kep(pCua(i)))}>
            <rect x={0} y={-13} width={22} height={22} rx={5}
                  fill={i === noiBat ? mau.nhan : MAU[i % MAU.length]}
                  stroke={mau.muc} strokeWidth={3} />
            <text x={32} y={5} fontSize={18} fontWeight={800} fill={mau.muc}>{c.nhan}</text>
            <text x={232} y={5} textAnchor="end" fontSize={19} fontWeight={900}
                  fill={mau.muc}>{c.hien}</text>
          </g>
        ))}
      </g>
    </g>
  );
};


/** LƯỚI Ô SÁNG/TẮT — "bao nhiêu trong tổng số", không cần trục nào. */
const LuoiO: React.FC<{ cot: NonNullable<Canh["cot"]>; p: number; mau: Paltte;
                        noiBat: number; pCua: (i: number) => number }> =
({ cot, p, mau, noiBat, pCua }) => {
  const a = cot[noiBat] || cot[0];
  if (!a) return null;
  const tong = Math.max(1, cot.reduce((t, c) => t + Math.max(0, c.gt), 0));
  const CT = 10, HG = 5, N = CT * HG;
  // Số ô sáng = phần của mục đang nói trên tổng. Làm tròn LÊN từ 1: không mục nào đáng bị vẽ
  // thành số không, kể cả khi nó rất nhỏ — vẽ ra số không là nói sai.
  const sang = Math.max(1, Math.min(N, Math.round((Math.max(0, a.gt) / tong) * N)));
  const pi = muot(kep(pCua(noiBat)));
  const O = 42, KHE = 8;
  return (
    <g>
      <rect x={-282} y={-140} width={564} height={286} rx={18} fill="#FBF6EA"
            stroke={mau.muc} strokeWidth={6} />
      <text x={-250} y={-98} fontSize={20} fontWeight={800} fill={mau.muc} opacity={0.85}>
        {a.nhan}
      </text>
      <text x={250} y={-96} textAnchor="end" fontSize={30} fontWeight={900} fill={mau.muc}>
        {a.hien}
      </text>
      <g transform={`translate(${-((O + KHE) * CT - KHE) / 2} -62)`}>
        {Array.from({ length: N }).map((_, i) => {
          const c = i % CT, h = Math.floor(i / CT);
          const on = i < Math.round(sang * pi);
          return (
            <rect key={i} x={c * (O + KHE)} y={h * (O + KHE)} width={O} height={O} rx={8}
                  fill={on ? mau.nhan : "#E8E1CE"} stroke={mau.muc}
                  strokeWidth={on ? 4 : 2} opacity={on ? 1 : 0.55} />
          );
        })}
      </g>
    </g>
  );
};

/** KHUNG THƯỚC — đo MỘT đại lượng, kiểu bản vẽ kỹ thuật. */
const KhungThuoc: React.FC<{ cot: NonNullable<Canh["cot"]>; p: number; mau: Paltte;
                             noiBat: number; pCua: (i: number) => number }> =
({ cot, p, mau, noiBat, pCua }) => {
  const a = cot[noiBat] || cot[0];
  if (!a) return null;
  const dinh = Math.max(1, ...cot.map((c) => c.gt));
  const pi = muot(kep(pCua(noiBat)));
  const RONG = 470;
  const w = RONG * Math.min(1, Math.max(0.04, a.gt / dinh)) * pi;
  return (
    <g>
      <rect x={-282} y={-130} width={564} height={262} rx={18} fill="#FBF6EA"
            stroke={mau.muc} strokeWidth={6} />
      <text x={-236} y={-72} fontSize={46} fontWeight={900} fill={mau.muc} opacity={pi}>
        {a.hien}
      </text>
      <text x={-236} y={-40} fontSize={19} fontWeight={800} fill={mau.muc} opacity={0.8 * pi}>
        {a.nhan}
      </text>
      {/* Khung thước: hai chốt vuông hai đầu và các vạch chia — đọc ra là một PHÉP ĐO, không
          phải một cái cột. Đó là khác biệt về nghĩa, không chỉ khác về hình. */}
      <g transform="translate(-236 20)">
        <rect x={-10} y={-8} width={16} height={68} rx={3} fill={mau.muc} />
        <rect x={RONG - 6} y={-8} width={16} height={68} rx={3} fill={mau.muc} />
        <rect x={0} y={-2} width={RONG} height={12} fill={mau.muc} />
        <rect x={0} y={46} width={RONG} height={12} fill={mau.muc} />
        {Array.from({ length: 22 }).map((_, i) => (
          <rect key={i} x={(RONG / 22) * i + 6} y={12} width={2} height={22}
                fill={mau.muc} opacity={0.28} />
        ))}
        <rect x={4} y={10} width={Math.max(4, w)} height={38} fill={mau.nhan} />
      </g>
    </g>
  );
};

/** ĐIỂM PHÂN TÁN — mật độ thay cho chiều dài, cho những con số quá lớn để so bằng cột. */
const DiemPhanTan: React.FC<{ cot: NonNullable<Canh["cot"]>; p: number; mau: Paltte;
                              noiBat: number; pCua: (i: number) => number }> =
({ cot, p, mau, noiBat, pCua }) => {
  const a = cot[noiBat] || cot[0];
  if (!a) return null;
  const dinh = Math.max(1, ...cot.map((c) => c.gt));
  const pi = muot(kep(pCua(noiBat)));
  const N = Math.max(6, Math.round(78 * Math.min(1, a.gt / dinh)));
  // Vị trí điểm sinh từ một dãy tất định (không dùng số ngẫu nhiên): cùng một dữ liệu phải cho
  // cùng một hình ở mọi lần dựng, nếu không mỗi lần render lại ra một khung khác.
  const diem = Array.from({ length: N }).map((_, i) => {
    const t = (i * 2654435761) % 100000;
    return { x: -240 + ((t % 977) / 977) * 480, y: -96 + ((Math.floor(t / 977) % 613) / 613) * 200 };
  });
  return (
    <g>
      <rect x={-282} y={-130} width={564} height={266} rx={18} fill="#FBF6EA"
            stroke={mau.muc} strokeWidth={6} />
      {Array.from({ length: 9 }).map((_, i) => (
        <rect key={`v${i}`} x={-250 + i * 62} y={-110} width={1.5} height={200}
              fill={mau.muc} opacity={0.1} />
      ))}
      {diem.map((d, i) => (
        <circle key={i} cx={d.x} cy={d.y} r={i / N < pi ? 9 : 0}
                fill={mau.nhan} opacity={0.85} />
      ))}
      <text x={244} y={-84} textAnchor="end" fontSize={38} fontWeight={900}
            fill={mau.muc} opacity={pi}>{a.hien}</text>
      <text x={244} y={-54} textAnchor="end" fontSize={18} fontWeight={800}
            fill={mau.muc} opacity={0.8 * pi}>{a.nhan}</text>
    </g>
  );
};


/** BẢN ĐỒ NƯỚC MỸ — bang đậm nhạt theo giá trị. Chỉ dùng khi nhãn LÀ tên bang. */
const BanDoMy: React.FC<{ cot: NonNullable<Canh["cot"]>; p: number; mau: Paltte;
                          noiBat: number; pCua: (i: number) => number }> =
({ cot, p, mau, noiBat, pCua }) => {
  const { duong, giaTri, dinh } = React.useMemo(() => {
    const g: any = _feature(_statesTopo as any, (_statesTopo as any).objects.states);
    // Khung bảng rộng 560 cao 250 — vừa đúng chỗ tấm nền, nên bản đồ nằm gọn như mọi dạng khác.
    const proj = geoAlbersUsa().fitExtent([[-250, -108], [250, 112]], g);
    const pg = geoPath(proj);
    const m = new Map<string, number>();
    for (const c of cot) m.set(String(c.nhan).trim().toLowerCase(), Math.max(0, c.gt));
    return { duong: pg, giaTri: m, dinh: Math.max(1, ...cot.map((c) => c.gt)), geo: g };
  }, [cot]);
  const g: any = _feature(_statesTopo as any, (_statesTopo as any).objects.states);
  const pi = muot(kep(p));
  const a = cot[noiBat] || cot[0];
  return (
    <g>
      <rect x={-282} y={-130} width={564} height={266} rx={18} fill="#FBF6EA"
            stroke={mau.muc} strokeWidth={6} />
      {g.features.map((f: any, i: number) => {
        const v = giaTri.get(String(f.properties?.name || "").trim().toLowerCase());
        // Bang KHÔNG có số thì tô xám nhạt, không tô màu nhạt của thang giá trị: tô theo thang
        // sẽ đọc ra là "bang này giá trị thấp", trong khi sự thật là "không có số liệu". Hai
        // chuyện khác hẳn nhau, và vẽ nhầm là nói sai.
        const co = v === undefined ? "#E4DED0" : undefined;
        const t = v === undefined ? 0 : Math.min(1, v / dinh) * pi;
        return (
          <path key={i} d={duong(f) || ""} fill={co || (t > 0.66 ? mau.nhan : t > 0.33 ? "#F2C230" : "#F7E9B8")}
                stroke={mau.muc} strokeWidth={1.1} opacity={v === undefined ? 0.75 : 1} />
        );
      })}
      {a ? (
        <>
          <text x={-250} y={-96} fontSize={19} fontWeight={800} fill={mau.muc} opacity={0.85}>
            {a.nhan}
          </text>
          <text x={250} y={-92} textAnchor="end" fontSize={34} fontWeight={900} fill={mau.muc}>
            {a.hien}
          </text>
        </>
      ) : null}
    </g>
  );
};


const CotDaoCu: React.FC<{ cot: NonNullable<Canh["cot"]>; p: number; mau: Paltte; noiBat?: number;
                           dang?: DangChart; hien?: number; pMoi?: number }> =
({ cot, p, mau, noiBat = 0, dang = "dung", hien, pMoi }) => {
  // ══ NÓI TỚI MỤC NÀO THÌ MỤC ẤY MỚI MỌC ═══════════════════════════════════════════════
  // Anh: *"chart vẫn đang bị chạy lặp đi lặp lại… hoặc nói tới dữ liệu nào dữ liệu đó chạy,
  // tránh chạy lặp lại"*.
  // Trước nay cả bảng mọc lên MỘT LẦN ở cảnh đầu rồi đứng đó tới hết; những cảnh sau chỉ đổi
  // cột nào được tô đỏ. Nên xem hai cảnh liền nhau thấy đúng một hình, và cái "chuyển động"
  // duy nhất là màu nhảy từ cột này sang cột kia — lặp, và không nói thêm điều gì.
  // Cách anh chỉ đúng hơn hẳn: biểu đồ **dựng dần theo lời**. Câu nói tới mục thứ nhất thì chỉ
  // mục thứ nhất có mặt; câu sau mục thứ hai mọc thêm; tới cuối bài bảng mới đủ. Mỗi cảnh vì
  // thế có một chuyển động THẬT và mang thông tin, thay vì một hình tĩnh đổi màu.
  const _soHien = typeof hien === "number" ? Math.max(1, hien) : cot.length;
  cot = cot.slice(0, _soHien);
  // 30/8 — Anh: *"chart số liệu cột cuối a thấy nó ra luôn ko thấy nó chạy"*.
  // Đúng, và là lỗi tôi vừa tạo khi cho bảng dựng dần: cảnh nào MƯỢN bảng của cảnh trước thì
  // được truyền `p = 1` — nghĩa là "bảng này đã mọc xong từ lâu rồi, đừng mọc lại". Đúng với
  // những cột đã có mặt từ trước, nhưng SAI với cột vừa mới thêm vào ở chính cảnh này: nó cũng
  // nhận `p = 1` nên bật ra ở trạng thái hoàn tất, không có một khung hình nào cho nó lớn lên.
  // Nên cột CUỐI CÙNG — cột mới — phải dùng tiến độ của cảnh HIỆN TẠI, còn các cột cũ giữ
  // nguyên `p = 1`. Một bảng có hai loại cột thì cần hai đồng hồ, không phải một.
  const _pCua = (i: number) =>
    (typeof pMoi === "number" && i === _soHien - 1 && _soHien > 1) ? pMoi : p;
  if (dang === "ngang") return <CotNgang cot={cot} p={p} mau={mau} noiBat={noiBat} pCua={_pCua} />;
  if (dang === "cham") return <ChamQue cot={cot} p={p} mau={mau} noiBat={noiBat} pCua={_pCua} />;
  if (dang === "khoi") return <KhoiVuong cot={cot} p={p} mau={mau} noiBat={noiBat} pCua={_pCua} />;
  if (dang === "thehai") return <TheDoiDau cot={cot} p={p} mau={mau} noiBat={noiBat} pCua={_pCua} />;
  if (dang === "vong") return <VongPhan cot={cot} p={p} mau={mau} noiBat={noiBat} pCua={_pCua} />;
  if (dang === "luoi") return <LuoiO cot={cot} p={p} mau={mau} noiBat={noiBat} pCua={_pCua} />;
  if (dang === "thuoc") return <KhungThuoc cot={cot} p={p} mau={mau} noiBat={noiBat} pCua={_pCua} />;
  if (dang === "diem") return <DiemPhanTan cot={cot} p={p} mau={mau} noiBat={noiBat} pCua={_pCua} />;
  if (dang === "bando") return <BanDoMy cot={cot} p={p} mau={mau} noiBat={noiBat} pCua={_pCua} />;
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
    <g transform={`translate(${-(nenX + nenW / 2)} 150)`}>
      {/* TẤM NỀN — giấy kem mờ, viền dày, bo góc. Đây là thứ tách biểu đồ khỏi bối cảnh. */}
      <rect x={nenX} y={nenY} width={nenW} height={nenH} rx={18}
            fill="#FBF6EA" stroke={mau.muc} strokeWidth={6} />
      {/* đường chân cột, để cột có chỗ đứng thay vì lơ lửng */}
      <line x1={nenX + 12} y1={2} x2={nenX + nenW - 12} y2={2}
            stroke={mau.muc} strokeWidth={5} opacity={0.55} />
      {cot.slice(0, N).map((c, i) => {
        const moc = muot(kep((_pCua(i) - i * 0.07) / 0.3));
        const h = (c.gt / dinh) * CAO * moc;
        const sang = i === noiBat;
        // ══ BIỂU ĐỒ PHẢI DIỄN THEO LỜI NÓI ═══════════════════════════════════════════════
        // Anh: *"cần có chart + số liệu animation chuyển động phù hợp nội dung phân tích và
        // nói cho hợp lý bắt mắt hơn"*.
        // Bản cũ chỉ có một chuyển động: bốn cột cùng mọc lên một lần ở đầu cảnh, rồi đứng
        // yên tới hết. Cột "đang được nói" có đổi màu, nhưng đổi PHỰT — không có gì dẫn mắt
        // tới đó, nên người xem vẫn phải tự dò xem lời đang nói ứng với cột nào.
        // Ba chuyển động thêm, mỗi cái làm một việc rõ:
        //   · `nhan` — cột được nhắc nảy lên trong 0,45 giây đầu khi tới lượt nó: mắt bắt
        //     chuyển động trước khi kịp đọc chữ, nên đây là thứ dẫn mắt thật sự;
        //   · `mo`   — ba cột còn lại lùi lại một nấc, để cột được nói nổi lên bằng TƯƠNG PHẢN
        //     chứ không phải bằng cách tự to thêm mãi;
        //   · số ĐẾM LÊN thay vì hiện sẵn — con số đang chạy là thứ người ta chờ xem dừng ở
        //     đâu, và nó khớp đúng nhịp người đọc đang đọc con số ấy.
        const nhip = muot(kep((p - 0.02) / 0.45));          // nhịp nhấn trong cảnh
        const nhan = sang ? Math.sin(nhip * Math.PI) * 16 : 0;
        const mo = sang ? 1 : 1 - 0.34 * nhip;
        // Đếm lên CHỈ khi nhãn là số thuần — "127.8K" hay "3 in 5" thì đếm sẽ ra chuỗi vô
        // nghĩa, nên những nhãn ấy giữ nguyên và chỉ hiện dần.
        const soThuan = /^-?[\d,]+$/.test(String(c.hien || ""));
        const hienSo = soThuan
          ? Math.round(Number(String(c.hien).replace(/,/g, "")) * moc).toLocaleString("en-US")
          : c.hien;
        return (
          <g key={i} transform={`translate(${i * BUOC} ${-nhan})`} opacity={mo}>
            <rect x={0} y={-h - (sang ? 10 : 0)} width={RONG} height={h + (sang ? 10 : 0)}
                  rx={8} fill={sang ? mau.nhan : "#F2C230"}
                  stroke={mau.muc} strokeWidth={sang ? 7 : 5} />
            {/* 30/8 — khung đo được: "351 cal" và "336 cal" dính thành "351 cal336 cal".
                Khi hai giá trị gần bằng nhau thì hai cột cao xấp xỉ nhau, mà nhãn số nằm ở
                cùng một độ cao so với đỉnh cột — thế là hai chuỗi chữ nằm ngang hàng và chạm
                nhau, vì bề rộng chữ ("351 cal") lớn hơn bề rộng một cột.
                Hai việc: nâng nhãn của cột LẺ lên một nấc để hai hàng chữ so le, và thu cỡ chữ
                lại vừa đủ khi nhãn dài. So le rẻ hơn thu nhỏ — thu nhỏ mãi thì số hết đọc
                được, mà đọc được số mới là toàn bộ giá trị của những kênh này. */}
            <text x={RONG / 2} y={-h - 24 - (sang ? 10 : 0) - (i % 2 ? 30 : 0)}
                  textAnchor="middle"
                  fontSize={(sang ? 34 : 28) * (String(hienSo).length > 6 ? 0.82 : 1)}
                  fontWeight={900}
                  fill={mau.muc} opacity={moc}>{hienSo}</text>
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
const PhuDe: React.FC<{ tu: Tu[]; giay: number; mau: Paltte; day: number; lech?: number }> = ({ tu, giay, mau, day, lech = 130 }) => {
  const k = tu.findIndex((w) => giay >= w.t && giay < w.t + w.d);
  if (k < 0 && !tu.some((w) => Math.abs(w.t - giay) < 1.2)) return null;
  const tam = k >= 0 ? k : tu.findIndex((w) => w.t > giay);
  const dau = Math.max(0, (tam < 0 ? tu.length : tam) - 2);
  // 29/8 — SÁU TỪ, XUỐNG HAI DÒNG. Bản đầu đổ chín từ lên MỘT dòng và nó chạy tràn cả hai mép
  // khung. SVG `<text>` KHÔNG tự xuống dòng — không có thuộc tính nào bảo nó làm thế — nên phải
  // tự cắt dòng. Sáu từ là vừa đủ để mắt bắt kịp ở tốc độ đọc 2,5 từ/giây mà không phải liếc.
  // 31/8 — CẮT THEO CÂU, KHÔNG CẮT GIỮA CHỪNG.
  // Lưới khung lô 1 đọc ra toàn những mẩu vỡ: "it looks. Arizona comes second at", "than it
  // looks. 6 comes second". Cửa sổ sáu từ trượt đều đặn nên nó rơi vào giữa câu, và người xem
  // đọc được một mảnh không có đầu không có đuôi — tệ hơn không có phụ đề, vì mắt vẫn dừng lại
  // để đọc rồi mới nhận ra không hiểu gì.
  // Lùi về đầu câu gần nhất (sau dấu chấm/hỏi/than) rồi mới lấy sáu từ.
  // 31/8 — LÙI VỀ ĐẦU CÂU, KHÔNG GIỚI HẠN SỐ TỪ.
  // Bản trước chỉ lùi tối đa bảy từ rồi bỏ cuộc, nên với câu dài — mà câu nào có số cũng dài,
  // vì "109" đọc thành "one hundred nine" chiếm ba từ — nó dừng giữa chừng và khung phụ đề bắt
  // đầu bằng một mẩu: "hundred nine This is straight from". Hai câu dán vào nhau, đọc không ra
  // nghĩa nào.
  // Giới hạn ấy tôi đặt vì sợ lùi quá xa; nhưng câu dài nhất trong bài cũng chỉ hơn chục từ,
  // nên không có gì để sợ. Lùi tới khi gặp dấu chấm hoặc về đầu bài.
  let _dau = dau;
  while (_dau > 0 && !/[.!?]$/.test(tu[_dau - 1]?.w || "")) _dau--;
  // 31/8 — DỪNG Ở CUỐI CÂU, đừng tràn sang câu sau.
  // Lùi về đầu câu đã đúng, nhưng cửa sổ vẫn lấy đủ sáu từ nên nó vắt qua dấu chấm và dán đuôi
  // câu này vào đầu câu kia: "Illinois at one hundred nine This", "six million The file closes
  // with". Đọc lên là hai mẩu của hai chuyện khác nhau.
  // Lỗi nặng thêm sau khi tách số thành từ đọc — "109" thành "one hundred nine" chiếm ba từ,
  // nên cửa sổ sáu từ gần như luôn chạm sang câu kế.
  // Nay cắt tại từ đầu tiên KẾT THÚC bằng dấu câu: một khung phụ đề chỉ chứa một câu.
  let _het = Math.min(tu.length, _dau + 6);
  for (let i = _dau; i < _het; i++) {
    if (/[.!?]$/.test(tu[i]?.w || "")) { _het = i + 1; break; }
  }
  const doan = tu.slice(_dau, _het);
  const nua = Math.ceil(doan.length / 2);
  const dong = [doan.slice(0, nua), doan.slice(nua)];
  return (
    // 31/8 — PHỤ ĐỀ DỊCH SANG PHẢI, RA KHỎI CHỖ NHÂN VẬT ĐỨNG.
    // Đo trên lưới: nhân vật chiếm dải x từ −504 đến −146 (đứng góc trái, scale 1,42), còn phụ
    // đề canh giữa khung nên nó trải từ −400 đến +400 — chồng thẳng lên mặt nhân vật ở CẢ MƯỜI
    // HAI kênh. Không cổng nào báo, vì cổng đọc chữ và đo nhịp chứ không nhìn hai lớp có đè
    // nhau không; chỉ xếp mười hai khung cạnh nhau mới thấy đó là lỗi hệ thống.
    // Dời tâm chữ sang +130 và thu cỡ chữ một nấc: dải chữ thành −70…+330, nằm gọn trong khoảng
    // trống bên phải nhân vật. Không hạ xuống đáy khung vì đáy là chỗ giao diện điện thoại che.
    <g transform={`translate(${lech} ${day})`}>
      {dong.map((d, j) => (
        <text key={j} x={0} y={j * 52} textAnchor="middle" fontSize={40} fontWeight={900}
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
  canh = [], tu = [], voMp3 = "", nhac = "", doVat = "", nenAnh = "", nenTheoCanh = [],
  kieu = {}, kieuGoc = "nam_dam",
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

  // ══ BIỂU ĐỒ PHẢI Ở LẠI, KHÔNG BIẾN MẤT NỬA VIDEO ══════════════════════════════════════
  // Đếm ra: đúng BA TRÊN SÁU cảnh mỗi tập có dữ liệu. Nửa còn lại là ảnh nền, một nhân vật nhỏ
  // ở góc, và một dòng phụ đề — bảy phần mười màn hình bỏ trống.
  // Với mười kênh mà toàn bộ lý do người xem ở lại là CON SỐ, để nửa thời lượng không có con số
  // nào là bỏ đi nửa giá trị. Và nó cũng chính là thứ anh gọi là "nhìn bị tĩnh chán": không có
  // gì đổi vì không có gì ở đó cả.
  // Các kênh dữ liệu thật làm ngược lại: BIỂU ĐỒ Ở LẠI, lời dẫn đi qua từng phần của nó. Nên
  // cảnh nào không có bảng riêng thì mượn bảng của cảnh gần nhất có — và cột nổi bật vẫn đổi
  // theo câu, nên bảng không đứng chết mà được "đọc" dần.
  let _cot = C.cot, _iCot = i, _pCot = p;
  if (!_cot) {
    for (let k = i - 1; k >= 0; k--) {
      if (canh[k]?.cot) { _cot = canh[k].cot; _iCot = k; break; }
    }
    // Bảng mượn đã mọc xong từ cảnh trước rồi — cho `p` = 1 để nó không mọc lại từ đầu mỗi lần
    // chuyển cảnh, thứ sẽ đọc ra là biểu đồ nhấp nháy.
    _pCot = 1;
  }
  // Cột nổi bật khi cảnh không tự khai: xoay theo thứ tự cảnh, để mỗi câu dẫn mắt sang một cột
  // khác thay vì soi mãi một chỗ.
  const _noiBatKe = _cot ? (i - _iCot) % Math.min(4, _cot.length) : 0;
  // Số mục đã được nhắc tới tính tới cảnh này. Cảnh đầu tiên có bảng thì hiện hai mục (một mục
  // đơn độc không phải một phép so sánh), rồi mỗi cảnh thêm một.
  // 31/8 — KHỞI ĐIỂM BA CỘT, KHÔNG PHẢI HAI.
  // Lưới khung lô 1: gần như mọi kênh ở giữa video mới có ĐÚNG HAI cột. Hai cột không phải một
  // biểu đồ — nó là một phép so sánh đôi, và mắt đọc xong trong nửa giây rồi không còn gì để
  // nhìn suốt phần còn lại của cảnh. Chính anh đã chỉ ra ở bản trước: "chỉ 3 mục — bảng bốn
  // cột không đủ chỗ so sánh".
  // Vẫn giữ nguyên tinh thần dựng-dần (nói tới mục nào mục ấy mọc), chỉ nâng điểm xuất phát để
  // khung đầu tiên đã có đủ ba mục cho mắt bắt được một xu hướng.
  const _hienDen = _cot ? Math.min(_cot.length, 3 + Math.max(0, i - _iCot)) : 0;

  // Băm tên kênh để mỗi kênh có một dáng biểu đồ MẶC ĐỊNH cố định — người xem quen kênh nhận ra
  // ngay bộ mặt của nó, mà sáu mươi kênh vẫn không cùng một hình.
  // 31/8 — Cộng dồn mã ký tự thì phân bố rất lệch: sáu kênh thử ra năm kênh cùng một bên, vì
  // tên tiếng Anh dài ngắn khác nhau nhưng tổng mã lại rơi vào cùng một lớp chẵn/lẻ. Nhân dồn
  // với một số nguyên tố trộn đều các bit thấp, nên hai kênh tên gần giống nhau vẫn ra hai bố
  // cục khác nhau.
  const _soKenh = Array.from(String(tieuDe || "")).reduce(
    (a, c) => (a * 31 + c.charCodeAt(0)) % 100003, 7);

  // ══ MỖI KÊNH MỘT BỐ CỤC ═══════════════════════════════════════════════════════════════
  // 31/8 — Anh: *"nếu các channel hay các videos nào cũng lặp lại y chang này thì rất là nhàm
  // chán"*. Đúng, và nặng hơn tôi tưởng: bản trước có ba dáng biểu đồ và vài bảng màu, nhưng
  // KHUNG THÌ chỉ một — thẻ số ở đỉnh, bảng ở giữa, nhân vật góc trái dưới, ở cả sáu mươi kênh.
  // Đổi dáng cột bên trong một cái khung bất biến thì người xem vẫn thấy "vẫn video ấy".
  //
  // Hai trục đảo, băm từ tên kênh nên CỐ ĐỊNH với mỗi kênh: người xem quen kênh vẫn nhận ra bộ
  // mặt của nó, còn lướt qua sáu mươi kênh thì thấy sáu mươi kênh khác nhau.
  //   · lật ngang  — nhân vật sang phải, bảng và phụ đề sang trái;
  //   · thẻ số     — ở đỉnh khung, hoặc tụt xuống ngay trên bảng.
  // Hai trục này nhân với ba dáng biểu đồ và bảng màu riêng thành mười hai bộ mặt, đủ để không
  // hai kênh cạnh nhau nào trông giống nhau.
  const _lat = _soKenh % 2 === 1;
  const _theDuoi = Math.floor(_soKenh / 2) % 2 === 1;
  const _dau = _lat ? -1 : 1;

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
      {(nenTheoCanh[i] || nenAnh) ? (
        <AbsoluteFill style={{ overflow: "hidden" }}>
          {/* 30/8 — Anh: *"nhiều channel bối cảnh ảnh chưa thay đổi sau mỗi câu thoại nhìn bị
              tĩnh chán"*.
              Đếm lại thì nền CÓ đổi: chín trên mười kênh có đủ sáu ảnh khác nhau cho sáu câu.
              Nên lời anh nói không phải "ảnh không đổi" mà là "nhìn không thấy đổi" — và đó là
              hai chuyện khác nhau, chữa bằng hai cách khác nhau.
              Hai lý do mắt không bắt được:
                · ĐỔI PHỰT. Ảnh cũ biến mất và ảnh mới xuất hiện trong đúng một khung hình. Mắt
                  người bắt CHUYỂN ĐỘNG, không bắt trạng thái; một cú thay tức thời giữa hai ảnh
                  tĩnh trôi qua mà không để lại cảm giác gì. Nay ảnh mới chồng lên ảnh cũ trong
                  0,4 giây — thấy được chính động tác đổi.
                · PHÓNG QUÁ CHẬM. Bản cũ phóng 5% trải đều hai mươi giây, tức 0,25% mỗi giây —
                  dưới ngưỡng nhận biết. Nay mỗi CẢNH có nhịp phóng riêng khoảng 4% trong ba
                  giây, và hướng đổi luân phiên (cảnh chẵn tiến vào, cảnh lẻ lùi ra) để sáu cảnh
                  không thành một nhịp đều ru ngủ. */}
          {[i - 1, i].filter((k) => k >= 0 && (nenTheoCanh[k] || nenAnh)).map((k) => {
            const _s = canh[k]?.s ?? 0;
            const _e = canh[k]?.e ?? _s + 3;
            const _t = kep((giay - _s) / Math.max(0.6, _e - _s));
            const _huong = k % 2 === 0 ? 1 : -1;
            const _phong = 1.05 + _huong * (_t - 0.5) * 0.045;
            // Ảnh của cảnh TRƯỚC chỉ còn nhiệm vụ đỡ phía dưới trong lúc ảnh mới chồng lên.
            const _hien = k === i ? muot(kep((giay - (canh[i]?.s ?? 0)) / 0.4)) : 1;
            return (
              <AbsoluteFill key={k} style={{ opacity: _hien }}>
                {/* 30/8 — Anh: *"phần nội dung footage nên đẩy lên phía trên để không bị che
                    khuất, và làm mờ nền để đỡ phân tâm"*.
                    Ảnh nền do máy vẽ luôn đặt chủ thể ở GIỮA khung — mà giữa khung cũng đúng
                    là chỗ tấm biểu đồ ngồi. Hai thứ quan trọng nhất của hai lớp chồng lên
                    nhau, và lớp dưới thua.
                    `objectPosition` kéo ảnh lên để phần chủ thể lộ ra ở dải TRÊN, nơi không có
                    gì đè. Không phải cắt bớt ảnh — chỉ là chọn phần nào của ảnh được thấy.
                    Kèm một chút làm mờ: nền không cần sắc nét, nó cần GỢI ra bối cảnh. Nét quá
                    thì mắt đọc chi tiết ở nền thay vì đọc con số ở trên. */}
                <Img src={staticFile(nenTheoCanh[k] || nenAnh)}
                     style={{ width: "100%", height: "100%", objectFit: "cover",
                              objectPosition: "center 24%",
                              transform: `scale(${_phong})`,
                              filter: "saturate(0.94) brightness(1.06) blur(1.6px)" }} />
              </AbsoluteFill>
            );
          })}
          {/* Lớp phủ ĐẬM HƠN bộ hài. Bộ này có BIỂU ĐỒ và SỐ LIỆU đè lên nền; nền ảnh nhiều chi
              tiết làm chữ số khó đọc, mà đọc được số mới là toàn bộ giá trị của mười kênh này. */}
          {/* 30/8 — Anh: *"background nền nên làm lớp mờ hơn"* và *"nền bối cảnh chọn sao cho
              không ảnh hưởng tới chart, gây đè che lấp"*.
              Hai lớp, mỗi lớp một việc:
                · lớp một phủ đều cả khung, đục hơn bản cũ một nửa — ảnh nền lùi hẳn về sau và
                  thôi tranh chỗ với chữ số;
                · lớp hai chỉ phủ DẢI GIỮA, nơi tấm biểu đồ nằm. Ảnh nền nhiều chi tiết ở đúng
                  dải ấy là thứ làm con số khó đọc, mà đọc được con số mới là toàn bộ giá trị
                  của những kênh này. Phủ có trọng điểm giữ được không khí của ảnh ở trên và
                  dưới, chỗ không có gì phải đọc. */}
          <AbsoluteFill style={{ background:
            `linear-gradient(180deg,${mau.troi[1]}99 0%,${mau.troi[1]}77 45%,${mau.dat}AA 100%)` }} />
          <AbsoluteFill style={{ background:
            `linear-gradient(180deg,transparent 6%,${mau.troi[1]}88 20%,${mau.troi[1]}88 64%,transparent 78%)` }} />
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
            // 30/8 — ĐO, không ướm. Cử chỉ rộng nhất thực sự xảy ra ở kênh phân tích là
            // `mo_tay`: bàn tay cách tâm người 118,7 đơn vị. Nhân với scale 1,42 thành 169, nên
            // ở x=-362 mép người rơi vào -531 trong khung chỉ rộng tới -500 — tràn 31.
            // (`chi` còn rộng hơn, 181, nhưng ở chế độ người-dẫn nó bị đổi thành `dem` trước khi
            // vẽ, nên tính theo nó là tính dư. Đo trên tập cử chỉ THỰC SỰ hiện ra.)
            // -325 chừa thêm 6 đơn vị cho nhịp thở và độ nghiêng người.
            x={doc ? -325 * _dau : -430 * _dau}
            y={doc ? 800 : 560}
            // 29/8 lần hai — lần trước tôi tăng cỡ nhân vật 1.12->2.1 NHƯNG cùng lúc hạ zoom
            // máy quay 1.5->1.0. Tích hai số không đổi (1.68), nên khung render ra y hệt và tôi
            // suýt kết luận "sửa không ăn". Bài học: đổi hai hệ số nhân với nhau trong cùng một
            // lượt thì không đo được cái nào có tác dụng.
            scale={doc ? 1.42 : 1.7}
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
        {/* 30/8 — Anh: *"chart vẫn bị lệch phải quá nhiều che khuất"*, kèm ảnh chụp mất hẳn
            cột cuối. Đo ra ngay: viewBox dọc chạy từ -500 đến 500, mà tấm nền bốn cột sau
            `translate(78) scale(1.24)` chạy tới x = 688 — tràn 188 điểm, đúng gần hai cột.
            Đây là lỗi tôi tự tạo ở lần trước, khi anh bảo làm chart to hơn: tôi phóng 1,24 và
            đẩy sang phải 78 mà KHÔNG kiểm mép phải. Phóng to một thứ đã sát mép thì phần lớn
            phần phóng thêm rơi ra ngoài khung — thấy to hơn ở chỗ còn nhìn được, và mất hẳn
            phần bị đẩy ra.
            Nay hai con số cùng suy từ một chỗ: nhân vật đứng ở TRAI_MEP, chart lấy trọn phần
            còn lại và căn giữa phần ấy. Đổi cỡ nhân vật thì chart tự dịch theo. */}
        {_cot ? (
          <g transform={`translate(${doc ? CHART_TAM * _dau : 150} ${doc ? CHART_Y : 84}) scale(${doc ? CHART_CO : 1.02})`}>
            <CotDaoCu cot={_cot} p={_pCot} mau={mau} noiBat={C.noiBat ?? _noiBatKe}
                      dang={chonDang(_cot, _soKenh)} hien={_hienDen} pMoi={p} />
          </g>
        ) : null}
        {C.soLon ? (
          <g transform={`translate(${doc ? 96 * _dau : 150} ${doc ? (_theDuoi ? -300 : -440) : -340}) scale(${doc ? 1.12 : 1})`}>
            <SoTo so={C.soLon} nhan={C.nhanSo} p={p} mau={mau} />
          </g>
        ) : null}

        {/* Lớp chữ KHÔNG đi theo máy quay — phụ đề mà lia theo thì không đọc nổi. */}
        {/* TIÊU ĐỀ PHẢI CÓ THẺ NỀN, KHÔNG CHỈ CÓ VIỀN.
            30/8 — Từ khi nền là ẢNH AI thay cho mảng màu phẳng, chữ trắng viền đen không còn đủ:
            trên một kệ hàng sáng màu, đo được tiêu đề "Who really owns the brand" chìm gần hết.
            Viền chỉ tách chữ khỏi nền ĐỒNG MÀU; nó không cứu được nền NHIỀU CHI TIẾT, vì mắt
            phải tách chữ khỏi hàng chục cạnh nhỏ chứ không phải khỏi một mảng.
            Một thẻ tối mờ phía sau giải đúng việc ấy — cùng cách đã làm cho phụ đề. */}
        {tieuDe && giay < 3.2 ? (
          <g opacity={kep((3.2 - giay) / 0.4)}>
            <rect x={-Math.min(470, tieuDe.slice(0, 42).length * (doc ? 17 : 15) + 34)}
                  y={(doc ? -648 : -498) - (doc ? 46 : 42)}
                  width={2 * Math.min(470, tieuDe.slice(0, 42).length * (doc ? 17 : 15) + 34)}
                  height={doc ? 78 : 70} rx={18}
                  fill="#101218" fillOpacity={0.52} />
            <text x={0} y={doc ? -648 : -498} textAnchor="middle" fontSize={doc ? 58 : 52}
                  fontWeight={900} fill="#FFFFFF" stroke={mau.muc} strokeWidth={9}
                  paintOrder="stroke">
              {tieuDe.slice(0, 42)}
            </text>
          </g>
        ) : null}
        <PhuDe tu={tu} giay={giay} mau={mau} day={doc ? 610 : 430} lech={doc ? 130 * _dau : 0} />
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
