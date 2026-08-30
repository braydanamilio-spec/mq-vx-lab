import React from "react";
import { AbsoluteFill, Audio, Img, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { CAM_XUC, KIEU_MAU, visemeTai, Kieu, TenCamXuc, TenCuChi, Tu } from "../v2/DienVien";
import { DienVienHai } from "./DienVienHai";

/**
 * KỊCH HÀI V4 — hai nhân vật đối thoại, nền là ẢNH AI (29/8/2026).
 *
 * KHÁC `KichV2` Ở BA ĐIỂM, và cả ba đều là lý do phải viết thành phần riêng thay vì thêm cờ:
 *
 *   1. HAI NGƯỜI, KHÔNG PHẢI MỘT. Ai đang nói thì nhích lên trước, sáng hơn, và có khẩu hình;
 *      người kia lùi lại, tối hơn một chút, nhưng VẪN DIỄN — gật, nhướn mày, đảo mắt. Trong hài
 *      thoại, phản ứng của người NGHE thường buồn cười hơn câu của người nói.
 *   2. NỀN LÀ ẢNH. Ảnh AI vẽ một lần cho mỗi kênh rồi dùng lại mãi (xem `kich_hai.py`). Nhân vật
 *      vector đứng trước, có một lớp phủ nhẹ để tách khỏi nền — thiếu lớp ấy thì hình vector nét
 *      dày dán lên ảnh mềm sẽ đọc ra là hai thế giới khác nhau.
 *   3. NHỊP HÀI. Cắt cảnh đúng lúc đổi lượt thoại, và có một khoảng LẶNG nửa giây trước cú chốt.
 *      Khoảng lặng ấy là thứ làm cú chốt nổ; không có nó thì câu chốt trôi qua như mọi câu khác.
 */

const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const trn = (a: number, b: number, t: number) => a + (b - a) * kep(t);
/** Chân nhân vật chạm mặt sàn ở đây. Một hằng số DUY NHẤT: dải sàn, bóng đổ và chỗ đứng đều
 *  lấy từ nó, nên không bao giờ lệch nhau. */
const Y_CHAN = 0;
/** Chân nhân vật LUÔN chạm đúng dòng này TRÊN MÀN HÌNH, ở mọi cỡ máy.
 *
 * 30/8 — Bản trước khai cỡ máy bằng một cặp (dịch chuyển, độ phóng) rời nhau, nên mỗi cỡ máy
 * chân rơi vào một chỗ khác: cỡ cận đẩy chân xuống đúng mép dưới và cắt cụt bàn chân. Máy quay
 * thật thì tiến lại gần MÀ ĐƯỜNG SÀN ĐỨNG YÊN. Nên chỉ khai độ phóng, còn dịch chuyển TÍNH RA
 * từ nó — một nguồn sự thật, không có chỗ cho hai số lệch nhau. */
const CHAN_MH = 690;
const muot = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

export type Luot = {
  s: number; e: number;
  ai: 0 | 1;                    // ai đang nói
  nar: string;
  camXuc?: TenCamXuc;           // cảm xúc NGƯỜI NÓI
  camXucKia?: TenCamXuc;        // cảm xúc NGƯỜI NGHE — nửa còn lại của trò đùa
  cuChi?: TenCuChi;
  nen?: string;                 // tệp ảnh nền cho lượt này
  co?: "rong" | "trung" | "can";
  sfx?: string;
  chot?: boolean;               // lượt này là cú chốt -> có khoảng lặng trước, rung nhẹ khi nổ
};

export type PropsHai = {
  luot?: Luot[];
  tu?: Tu[];
  voMp3?: string;
  nhac?: string;
  kieuA?: keyof typeof KIEU_MAU | string;
  kieuB?: keyof typeof KIEU_MAU | string;
  kieuTuyA?: Partial<Kieu>;
  kieuTuyB?: Partial<Kieu>;
  vatA?: string;                // đạo cụ nhân vật A cầm (xem `DoVat` trong DienVienHai)
  vatB?: string;
  tieuDe?: string;
  font?: string;
  mucNen?: string;              // màu nền dự phòng khi chưa có ảnh
};

export const calcHai = async ({ props }: { props: PropsHai }) => {
  const ls = props.luot || [];
  const het = ls.length ? Math.max(...ls.map((x) => x.e)) : 20;
  return { durationInFrames: Math.max(90, Math.round((het + 0.7) * 30)), fps: 30 };
};

/** Bong bóng thoại — chỉ vẽ khi có chữ ngắn; thoại dài thì để karaoke lo. */
const BongThoai: React.FC<{ chu: string; x: number; y: number; trai: boolean; p: number; muc: string }> =
({ chu, x, y, trai, p, muc }) => {
  const v = muot(kep(p / 0.12));
  const w = Math.min(430, 42 + chu.length * 19);
  return (
    <g transform={`translate(${x} ${y}) scale(${0.86 + v * 0.14})`} opacity={v}>
      <rect x={-w / 2} y={-58} width={w} height={104} rx={26}
            fill="#FFFFFF" stroke={muc} strokeWidth={6} />
      <path d={`M ${trai ? -34 : 34} 44 l ${trai ? 26 : -26} 40 l ${trai ? 26 : -26} -40 Z`}
            fill="#FFFFFF" stroke={muc} strokeWidth={6} strokeLinejoin="round" />
      <text x={0} y={6} textAnchor="middle" fontSize={34} fontWeight={800} fill={muc}>
        {chu.slice(0, 44)}
      </text>
    </g>
  );
};

/** Phụ đề karaoke — hai dòng, tô từ đang đọc. Dùng lại đúng luật của thế hệ 3. */
const PhuDe: React.FC<{ tu: Tu[]; giay: number; nhan: string; day: number; s0: number; e0: number;
                        vien: string; ben: number }>
    = ({ tu: tuAll, giay, nhan, day, s0, e0, vien, ben }) => {
  // 30/8 — CỬA SỔ CHỮ PHẢI DỪNG Ở RANH GIỚI LƯỢT THOẠI.
  // Trước đây cửa sổ sáu-từ trượt trên TOÀN BỘ lời thoại, nên nó nhảy qua chỗ đổi người nói và
  // ghép lời hai người thành một câu: đo được "just moved in. That is right." — nửa đầu của
  // người A, nửa sau của người B, đọc ra là một người tự nói với mình. Hài hai người mà phụ đề
  // không phân biệt được ai đang nói thì mất hẳn cú va, tức là mất chỗ gây cười.
  // Cắt theo THỜI GIAN của lượt (không theo chỉ số câu) vì một lượt có thể gồm nhiều câu.
  // Một từ thuộc về lượt chứa ĐIỂM BẮT ĐẦU của nó — không phải lượt mà nó chồng lấn.
  // `e0` được đặt bằng ĐÚNG thời điểm bắt đầu của từ đầu tiên lượt sau, nên biên trên nới rộng
  // (`< e0 + 0.02`) nuốt luôn từ ấy: đo được mọi lượt đều thừa một từ lơ lửng ở cuối — "…moved
  // in. That", "…three weeks. I". Một từ thừa của người kia đủ làm câu đọc ra sai người nói.
  const tu = tuAll.filter((w) => w.t >= s0 - 0.02 && w.t < e0 - 0.02);
  if (!tu.length) return null;
  const k = tu.findIndex((w) => giay >= w.t && giay < w.t + w.d);
  if (k < 0 && !tu.some((w) => Math.abs(w.t - giay) < 1.1)) return null;

  // 30/8 — HIỆN TRỌN LƯỢT THOẠI, BỎ HẲN CỬA SỔ SÁU TỪ.
  // Cửa sổ trượt sinh ra những mẩu vô nghĩa: đo được "moved in. That" và "I noticed the truck.
  // And the" — cắt giữa câu, người đọc phải ghép lại trong đầu. Luật của bộ này (YTUONG_V4 §4)
  // đã ép mỗi lượt ≤ 14 từ, tức là trọn lượt LUÔN vừa hai dòng. Nên không cần cửa sổ: hiện cả
  // câu, tô dần từ đang đọc. Người xem đọc trước một nhịp rồi nghe câu chốt rơi đúng lúc —
  // đó mới là cách phụ đề phục vụ trò đùa.
  const doan = tu;
  // Cắt dòng theo BỀ RỘNG chứ không theo số từ: chia đôi số từ thì một câu có từ dài sẽ lệch hẳn
  // và dòng dài tràn mép khung.
  let nua = doan.length;
  if (doan.length > 3) {
    const rong = doan.map((w) => w.w.length + 1);
    const tong = rong.reduce((a, b) => a + b, 0);
    let don = 0;
    for (nua = 0; nua < doan.length - 1 && don + rong[nua] <= tong / 2; nua++) don += rong[nua];
    nua = Math.max(1, nua);
  }
  // Dòng dài nhất quyết định cỡ chữ. 0,55 là hệ số bề rộng đo được của phông đậm dùng ở đây;
  // khung rộng 1000 đơn vị, chừa mỗi bên 40 nên chữ được phép rộng tối đa 920.
  const _dai = Math.max(doan.slice(0, nua).reduce((a, w) => a + w.w.length + 1, 0),
                        doan.slice(nua).reduce((a, w) => a + w.w.length + 1, 0));
  const cs = Math.max(30, Math.min(46, Math.floor(920 / Math.max(1, _dai * 0.55))));
  const _rongThe = Math.min(940, _dai * cs * 0.55 + 62);
  return (
    <g transform={`translate(0 ${day})`}>
      {/* Thẻ nền sau chữ: chữ trắng viền đen trên ảnh nền vẫn khó đọc khi nền lắm chi tiết
          (bếp, ga-ra). Một thẻ mờ có viền màu người nói vừa chữa được chuyện đọc, vừa là chỗ
          mang màu để phân biệt hai người. */}
      <rect x={-_rongThe / 2} y={-40} width={_rongThe} height={nua < doan.length ? 118 : 62}
            rx={22} fill="#101218" fillOpacity={0.5} stroke={vien} strokeWidth={5} />
      <circle cx={(ben * _rongThe) / 2} cy={nua < doan.length ? 19 : -9} r={11} fill={vien}
              stroke="#101218" strokeWidth={4} />
      {[doan.slice(0, nua), doan.slice(nua)].map((d, j) => (
        <text key={j} x={0} y={j * (cs + 10)} textAnchor="middle" fontSize={cs} fontWeight={900}
              stroke="#12131A" strokeWidth={10} paintOrder="stroke" fill="#FFFFFF">
          {d.map((w, i) => (
            <tspan key={i} fill={k >= 0 && tu[k] === w ? nhan : "#FFFFFF"}>{(i ? " " : "") + w.w}</tspan>
          ))}
        </text>
      ))}
    </g>
  );
};

export const KichHai: React.FC<PropsHai> = ({
  luot = [], tu = [], voMp3 = "", nhac = "", kieuA = "hang_xom", kieuB = "bank",
  kieuTuyA = {}, kieuTuyB = {}, vatA = "", vatB = "", tieuDe = "", font = "", mucNen = "#F2E6CE",
}) => {
  const f = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const giay = f / fps;
  const doc = height > width;

  const A: Kieu = { ...(KIEU_MAU[kieuA as string] || KIEU_MAU.hang_xom), ...kieuTuyA };
  const B: Kieu = { ...(KIEU_MAU[kieuB as string] || KIEU_MAU.bank), ...kieuTuyB };

  // 30/8 — KHE LẶNG GIỮA HAI LƯỢT PHẢI GIỮ NGUYÊN LƯỢT VỪA KẾT THÚC.
  // `doc_hai_giong` chèn 0,16 giây im lặng giữa các lượt (và 0,55 giây trước cú chốt) để nhịp
  // thoại tự nhiên. Nhưng cách tìm lượt cũ trả -1 ở đúng những khe ấy, rồi rơi vào nhánh dự
  // phòng `luot.length - 1` — tức NHẢY THẲNG SANG LƯỢT CUỐI. Đo được trên khung thật ở giây
  // 5,85: phim đang ở trung cảnh bỗng giật sang cỡ cận của cú chốt rồi nhảy về. Sáu khe lặng
  // là sáu cú giật hình, và người xem đọc ra là lỗi dựng chứ không phải nhịp.
  //
  // Lỗi này SINH RA TỪ chính bản vá thêm khoảng lặng — trước đó các lượt sát nhau nên không có
  // khe nào để rơi vào. Đúng họ lỗi "vá một chỗ, mở ra một chỗ khác": mỗi khi đổi cấu trúc thời
  // gian, phải rà lại mọi chỗ TRA CỨU theo thời gian.
  let i = luot.findIndex((x) => giay >= x.s && giay < x.e);
  if (i < 0) {
    // trong khe: lấy lượt cuối cùng đã BẮT ĐẦU trước thời điểm này
    for (let j = luot.length - 1; j >= 0; j--) {
      if (giay >= luot[j].s) { i = j; break; }
    }
    if (i < 0) i = 0;                       // trước cả lượt đầu tiên
  }
  const L = luot[i] || ({ s: 0, e: 4, ai: 0, nar: "" } as Luot);
  const p = kep((giay - L.s) / Math.max(0.001, L.e - L.s));

  const noiA = L.ai === 0 ? visemeTai(tu, giay, CAM_XUC[L.camXuc || "trung_tinh"].ha)
                          : visemeTai([], giay, CAM_XUC[L.camXucKia || "trung_tinh"].ha);
  const noiB = L.ai === 1 ? visemeTai(tu, giay, CAM_XUC[L.camXuc || "trung_tinh"].ha)
                          : visemeTai([], giay, CAM_XUC[L.camXucKia || "trung_tinh"].ha);

  // ── AI ĐANG NÓI THÌ NHÍCH LÊN TRƯỚC ─────────────────────────────────────────────────────
  // Trong một cảnh hai người, mắt cần biết NGAY ai đang nói. Ba dấu hiệu cùng lúc, mỗi cái nhỏ:
  // người nói to hơn ~6%, sáng hơn, và nhích vào giữa khung một chút. Không dùng mũi tên, không
  // dùng khung sáng — những thứ ấy đọc ra là đồ hoạ, không đọc ra là diễn xuất.
  const noiA_ = L.ai === 0;
  const tA = muot(kep((giay - L.s) / 0.25));
  // 30/8 — BỎ HẲN PHÉP PHÓNG TO NGƯỜI NÓI.
  // Anh: "khi lời thoại tới nhân vật nào đang bị kiểu tự nhiên nhân vật cao lên nhân vật kia
  // nhỏ lại rất thiếu thẩm mỹ". Đúng, và nó còn SAI VỀ VẬT LÝ: hai người đứng cùng một mặt sàn
  // thì không ai to lên nhỏ lại giữa câu — mắt đọc ra là người kia lùi ra xa, tức là cả không
  // gian nói dối. Cỡ người từ nay CỐ ĐỊNH.
  // Ai đang nói thì đọc ra bằng bốn dấu hiệu KHÔNG đụng tới cỡ người, và cả bốn đều là thứ
  // diễn viên thật làm: khẩu hình động, thân nghiêng về phía người kia, mắt nhìn thẳng sang,
  // và phụ đề đổi sang MÀU CỦA NGƯỜI ẤY.
  const coA = 1, coB = 1;
  const nghiengA = noiA_ ? trn(0, 3.2, tA) : trn(3.2, 0, tA);
  const nghiengB = noiA_ ? trn(-3.2, 0, tA) : trn(0, -3.2, tA);

  // KHOẢNG LẶNG TRƯỚC CÚ CHỐT — nửa giây nhân vật không nói gì, máy quay nhích vào.
  // Đây là thứ làm cú chốt nổ. Bỏ nó đi thì câu chốt trôi qua như mọi câu khác.
  const truocChot = L.chot ? kep((0.5 - (giay - L.s)) / 0.5) : 0;
  const rung = L.chot && p > 0.12 ? Math.sin((giay - L.s) * 26) * 3.5 * Math.exp(-(giay - L.s) * 3) : 0;

  // 30/8 — KHUNG DỌC PHẢI PHÓNG TO HƠN KHUNG NGANG.
  // Cùng một cỡ người, khung 9:16 hẹp hơn 1,8 lần nên nhân vật đọc ra bé bằng nửa: khung đo được
  // hai người chiếm chưa tới 40% chiều cao, mặt nhỏ đến mức không thấy khẩu hình lẫn nét mặt —
  // mà nét mặt mới là chỗ hài nằm. Điện thoại xem ở khoảng cách bằng đúng khung, nên short phải
  // đóng cận hơn hẳn video ngang.
  // Đích đứng của mỗi lượt: người nói tiến lại gần khoảng 26 đơn vị, người nghe lùi nhẹ.
  // Cộng thêm một chút lệch theo chỉ số lượt để hai người không đứng đúng chỗ cũ mỗi lần.
  const _iL = Math.max(0, i);
  // 30/8 — KHOẢNG CÁCH CƠ SỞ 232 → 292: LỖI VẬT LÝ.
  // Đo trên khung thật: khi người nói dùng cử chỉ CHỈ TAY, bàn tay vươn xuyên qua VAI người kia.
  // Cánh tay duỗi hết dài chừng 216 điểm màn hình, mà khoảng trống giữa hai thân chỉ còn 304 —
  // trừ đi phần hai người nghiêng vào nhau và phần người nói tiến lên 30, khoảng trống thật
  // xuống dưới 200. Hai hình vẽ lồng vào nhau là lỗi mắt bắt được ngay, và nó phá cả cảm giác
  // "hai người đang đứng trong một không gian có thật".
  const dichA = -292 + (noiA_ ? 30 : -14) + ((_iL % 3) - 1) * 16;
  const dichB = 292 + (noiA_ ? 14 : -30) + (((_iL + 1) % 3) - 1) * 16;
  const _truocA = -292 + (i > 0 && luot[i - 1].ai === 0 ? 30 : -14) + (((_iL + 2) % 3) - 1) * 16;
  const _truocB = 292 + (i > 0 && luot[i - 1].ai === 0 ? 14 : -30) + ((_iL % 3) - 1) * 16;
  const tDi = muot(kep((giay - L.s) / 0.6));
  // Ở cỡ cận, hai người phải giãn ĐỦ XA để người không nói ra HẲN ngoài khung. Đo được ở hệ
  // số 1,5: mép phải của người kia còn nằm trong khung 18 điểm, ra một mảnh người lơ lửng ở
  // mép trái — xấu hơn cả việc chồng người. Nửa vời là tệ nhất; hoặc trong khung hẳn, hoặc ra
  // hẳn ngoài.
  // Hệ số 3,6 chứ không phải 2,4: ở hệ số cũ THÂN người kia đã ra ngoài khung nhưng BÀN TAY
  // thì chưa — tay vươn xa tâm hơn thân, và một bàn tay lơ lửng ở mép khung còn khó chịu hơn
  // cả nửa người. Tính theo điểm XA NHẤT của hình, không theo tâm.
  const _gian = (L.co || "trung") === "can" ? 3.6 : 1;
  const xA = trn(_truocA, dichA, tDi) * _gian;
  const xB = trn(_truocB, dichB, tDi) * _gian;
  // `buoc` > 0 khi đang di chuyển: bật dáng đi (chân bước so le, tay vung ngược pha).
  const dangDi = Math.abs(dichA - _truocA) > 6 && tDi > 0.02 && tDi < 0.98;
  const buocA = dangDi ? Math.sin(tDi * Math.PI) : 0;
  const buocB = Math.abs(dichB - _truocB) > 6 && tDi > 0.02 && tDi < 0.98 ? Math.sin(tDi * Math.PI) : 0;

  // CỬ CHỈ NGƯỜI NGHE PHẢI THEO CẢM XÚC CỦA CHÍNH NÓ.
  // Bản cũ ghim cứng "khoanh_tay" cho người nghe suốt cả phim: một người khoanh tay hai mươi
  // giây trong khi mặt đổi từ ngạc nhiên sang bực sang buồn — tay và mặt kể hai chuyện khác
  // nhau. Trong hài thoại thì phản ứng của người NGHE thường buồn cười hơn câu của người nói,
  // nên đây không phải chi tiết phụ.
  // 30/8 — NGƯỜI NGHE KHÔNG BAO GIỜ ĐƯỢC BUÔNG THÕNG TAY.
  // Bản trước ánh xạ hai cảm xúc về "nghi" (buông xuôi hai tay). Cộng với việc đã hạ biên độ
  // nhịp sống của người nghe xuống 22%, kết quả là người nghe đứng chôn chân, tay dán vào thân —
  // đọc ra là một pho tượng đặt cạnh diễn viên.
  // Bài toán đúng là: đứng YÊN mà vẫn CÓ HÌNH. Hoạt hình giải bằng TƯ THẾ — chống nạnh, khoanh
  // tay, chống cằm, ngán ngẩm. Đứng yên trong một tư thế rõ ràng thì đọc ra là "đang chờ nghe",
  // còn đứng yên buông thõng tay thì đọc ra là quên vẽ.
  const NGHE: Record<string, TenCuChi> = {
    bat_ngo: "mo_tay", so: "mo_tay", nghi_ngo: "suy_nghi", tuc: "khoanh_tay",
    buon: "ngan_ngam" as TenCuChi, vui: "nhun_vai",
    tu_tin: "chong_nanh" as TenCuChi, trung_tinh: "chong_nanh" as TenCuChi,
  };
  const cuChiNghe = NGHE[(L.camXucKia || "trung_tinh") as string] || "nghi";

  // CÚ GIẬT MÌNH của người NGHE, đúng vào lúc câu chốt vừa rơi.
  // Trong hài hình ảnh, thứ báo cho khán giả "chỗ này buồn cười" không phải tiếng cười lồng mà
  // là PHẢN ỨNG của người trên màn hình. Cho nó bắt đầu trễ 0,35 giây so với đầu lượt chốt —
  // đúng nhịp một người nghe xong mới kịp hiểu.
  const _giatNghe = L.chot ? kep((giay - L.s - 0.35) / 1.6) : 0;

  // 30/8 — ĐO ĐƯỢC: nhân vật chỉ chiếm ~30% chiều cao khung. Trên điện thoại thì mặt bé đến
  // mức không đọc được nét mặt, mà cú chốt của hài nằm ở nét mặt. Short phải đóng cận: người
  // chiếm quá nửa khung. Nâng cả độ phóng lẫn cỡ người, và hạ chân xuống thấp để phần trống
  // phía trên không thừa.
  // 30/8 — CỠ MÁY PHẢI CHÊNH ĐỦ ĐỂ MẮT THẤY.
  // Một tập chỉ còn MỘT bối cảnh (xem `dung_luot`), nên toàn bộ nhịp thị giác dồn vào máy quay.
  // Dải 1,42–1,92 quá hẹp: bốn lượt liền nhau ra bốn khung gần y hệt. Nới thành 1,25–2,25 thì
  // toàn cảnh đọc ra là "đang ở đâu" còn cận cảnh đọc ra là "nhìn mặt nó kìa".
  const _can = (L.co || "trung") === "can";
  const KH = doc
    ? { rong: 1.25, trung: 1.68, can: 3.6 }
    : { rong: 0.84, trung: 1.06, can: 2.2 };
  const zoom = (KH[L.co || "trung"] || 1.68) * (1 + truocChot * 0.05);
  // ══ CỠ CẬN NEO VÀO ĐẦU, HAI CỠ KIA NEO VÀO CHÂN ═════════════════════════════════════
  // Neo mọi cỡ vào chân là lý do "cận cảnh" của bản trước vẫn ra TOÀN THÂN: giữ chân đứng yên
  // thì phóng to bao nhiêu người cũng chỉ dài thêm xuống dưới, đầu bay khỏi khung trước khi mặt
  // kịp to. Mà cận cảnh theo định nghĩa là KHÔNG THẤY CHÂN.
  // Nên hai cỡ rộng neo vào đường sàn (để đường sàn đứng yên khi máy tiến vào), còn cỡ cận neo
  // vào ĐẦU — đúng cách máy quay thật lia lên khi áp sát một khuôn mặt. Cú chốt vì thế rơi vào
  // một khuôn mặt chiếm gần bốn phần mười chiều cao màn hình, đủ để đọc từng nét.
  const _yDau = -336 * 1.3;                       // tâm đầu trong hệ toạ độ nhóm
  const dichY = _can ? -60 - _yDau * zoom : CHAN_MH - Y_CHAN * zoom;
  // LIA NGANG RẤT CHẬM. Máy quay đứng chết cứng là dấu hiệu của hình dựng máy; một chuyển động
  // dưới ngưỡng chú ý vẫn làm khung "còn sống". Hướng lia đổi theo lượt nên không thành nhịp đều.
  const liaNhe = Math.sin(giay * 0.32 + i * 1.7) * 26;

  // ══ CẬN CẢNH LÀ CẬN VÀO NGƯỜI ĐANG NÓI, KHÔNG PHẢI CẬN CẢ HAI ═══════════════════════
  // Bản trước giữ khoảng cách hai người CỐ ĐỊNH TRÊN MÀN HÌNH (chia x cho độ phóng) trong khi
  // cỡ người vẫn to lên theo độ phóng. Ở cỡ cận, mỗi người rộng 428 điểm mà khoảng cách tâm chỉ
  // 464 — hai người chồng lên nhau, tay người này đè mặt người kia. Đo được đúng cảnh ấy.
  //
  // Sửa bằng cách chia lại khoảng cách thì chỉ đẩy người ra ngoài mép khung. Đường đúng là
  // NGỮ PHÁP PHIM: toàn cảnh cho thấy đang ở đâu, trung cảnh cho thấy hai người, còn cận cảnh
  // thì theo định nghĩa chỉ có MỘT người — người đang nói. Máy quay dịch ngang để đưa người ấy
  // vào giữa khung, và cú chốt vì thế rơi đúng vào một khuôn mặt chiếm gần hết màn hình.
  const _canhCan = (L.co || "trung") === "can";
  const _tamNguoi = noiA_ ? xA : xB;
  const liaVao = _canhCan ? -_tamNguoi * muot(kep((giay - L.s) / 0.28)) : 0;
  const lia = liaNhe * (_canhCan ? 0.4 : 1) + liaVao;

  const _cao = Math.round(1000 * (height / width));
  const vb = doc ? `-500 ${-Math.round(_cao * 0.47)} 1000 ${_cao}`
                 : `-820 ${-Math.round(1640 * (height / width) * 0.5)} 1640 ${Math.round(1640 * (height / width))}`;

  return (
    <AbsoluteFill style={{ background: mucNen, fontFamily: font || "Poppins, Arial, sans-serif" }}>
      {/* NỀN LÀ ẢNH AI — đứng yên, hơi phóng chậm để khung không chết cứng */}
      {L.nen ? (
        <AbsoluteFill style={{ overflow: "hidden" }}>
          {/* ══ NỀN PHẢI TIẾN THEO MÁY QUAY, NHƯNG TIẾN ÍT HƠN NGƯỜI ══════════════════
              30/8 — Đo được ở khung cận: mặt chiếm gần nửa màn hình mà hàng rào phía sau vẫn
              nhỏ y như lúc toàn cảnh. Mắt đọc ra ngay là nhân vật được DÁN lên một tấm ảnh,
              không phải đứng trong một không gian.
              Máy quay tiến lại gần thì MỌI THỨ đều to lên — chỉ là thứ ở xa to lên chậm hơn
              thứ ở gần (đó chính là phối cảnh). Nên nền phóng theo `zoom` với hệ số 0,42:
              đủ để không "dán", đủ chậm để vẫn ra chiều sâu. Đây cũng là cách các phần mềm
              dựng phim 2D làm lớp nền xa. */}
          <Img src={staticFile(L.nen)}
               style={{ width: "100%", height: "100%", objectFit: "cover",
                        transform: `translateX(${-lia * 0.3}px) scale(${1.04 + p * 0.03 + (zoom - 1.25) * 0.42})`,
                        filter: "saturate(1.05) brightness(1.02)" }} />
          {/* Lớp phủ nhẹ: tách nhân vật vector nét dày khỏi ảnh nền mềm. Thiếu nó thì hai thứ
              đọc ra là hai thế giới dán vào nhau. */}
          {/* 30/8 — LỚP PHỦ MỎNG LẠI, VÀ CHỈ ĐẬM Ở ĐÁY.
              Bản cũ phủ đều cả khung (#00000018 → #00000042) nên nền vốn tối (ga-ra, phòng gọi)
              bị đẩy quá ngưỡng: đo được 13% điểm gần như đen, `cham_v4` chặn ở 8%. Việc tách
              nhân vật khỏi nền đã do nét viền dày của `DienVien` lo; lớp phủ chỉ còn một việc là
              làm nền dưới chân phụ đề đủ trầm để chữ trắng nổi lên, nên nó dồn xuống đáy. */}
          <AbsoluteFill style={{ background:
            "linear-gradient(180deg,#0000000A 0%,#00000005 55%,#00000038 100%)" }} />
        </AbsoluteFill>
      ) : null}

      {/* 30/8 — `<svg>` PHẢI NẰM TRONG MỘT `AbsoluteFill`.
          Nền ở trên là `position:absolute`; thẻ svg trần là phần tử TĨNH. Luật vẽ của CSS xếp
          phần tử-có-định-vị vẽ SAU nội dung tĩnh, nên nền phủ kín nhân vật lẫn phụ đề — khung
          ra chỉ còn mỗi ảnh nền, đúng cảnh vừa đo. Đặt svg vào lớp định vị thì hai bên cùng
          hạng, và thứ tự viết trong JSX mới là thứ tự vẽ. */}
      <AbsoluteFill>
      <svg viewBox={vb} width="100%" height="100%" preserveAspectRatio="xMidYMid slice">
        {/* ══ MẶT SÀN ══════════════════════════════════════════════════════════════════
            Anh: "lỗi nhân vật đứng trên bếp". Gốc của nó nằm ở ẢNH NỀN, không ở nhân vật: ảnh
            "kitchen counter with a fruit bowl" chụp NGANG TẦM MẶT BÀN nên trong khung KHÔNG CÓ
            sàn nào cả. Nhân vật đặt ở đâu cũng sẽ đứng trên một mặt bàn.
            Đã sửa câu vẽ cho các nền mới, nhưng ảnh AI thì lượt nào cũng có thể trả về một
            khung không thấy sàn — nên phải có một lớp bảo hiểm KHÔNG phụ thuộc vào ảnh.
            Dải sàn này là lớp ấy: một mặt phẳng mờ ở đáy khung, lấy màu từ chính bảng màu kênh,
            có đường chân tường và bóng đổ. Nhân vật đứng lên ĐƯỜNG NÀY, nên dù ảnh nền phía
            trên là gì thì vật lý vẫn đúng: có sàn, có bóng, có chỗ chân chạm. */}
        <defs>
          <linearGradient id="san" x1="0" y1="0" x2="0" y2="1">
            {/* Mờ hẳn: đây là LỚP BẢO HIỂM cho trường hợp ảnh nền không có sàn, không phải
                một tấm sàn để nhìn. Đục quá thì nó đè lên mặt đường có sẵn của ảnh và đọc ra
                là một tờ giấy dán ngang khung. */}
            <stop offset="0%" stopColor={mucNen} stopOpacity={0.0} />
            <stop offset="30%" stopColor={mucNen} stopOpacity={0.16} />
            <stop offset="100%" stopColor={mucNen} stopOpacity={0.4} />
          </linearGradient>
        </defs>
        <g transform={`translate(${rung + lia} ${dichY}) scale(${zoom})`} style={{ transformOrigin: "0px 0px" }}>
          <rect x={-1600} y={Y_CHAN - 34} width={3200} height={1400} fill="url(#san)" />
          <line x1={-1600} y1={Y_CHAN - 34} x2={1600} y2={Y_CHAN - 34}
                stroke="#00000014" strokeWidth={2} />
          {/* 30/8 — KHOẢNG CÁCH HAI NGƯỜI CHIA CHO ĐỘ PHÓNG.
              Toàn cảnh được phóng `zoom`; nếu giữ nguyên x thì ở cỡ CẬN (zoom 1,72) hai người
              bị đẩy ra 1,72 lần và mép khung xén mất nửa người — đo được đúng cảnh ấy. Chia x
              cho zoom thì khoảng cách trên MÀN HÌNH giữ nguyên trong khi người vẫn to lên, tức
              là máy quay tiến lại gần chứ không phải kéo hai người ra xa nhau. */}
          {/* ĐI LẠI TRONG CẢNH — anh: "nhân vật có thể chuyển động đi hay tay chân cử chỉ
              thật hơn kiểu animation được ko".
              Hai người đứng chôn chân suốt hai mươi giây là thứ đọc ra ngay là hình dựng máy;
              trong hoạt hình, người nói bao giờ cũng XÊ DỊCH — bước lại gần khi gặng hỏi, lùi
              ra khi bị dồn. Nên mỗi lượt thoại có một đích đứng riêng (`diA`/`diB`) và nhân vật
              ĐI tới đó trong 0,6 giây đầu lượt, có bước chân hẳn hoi (`buoc` > 0 bật dáng đi).
              Khoảng cách hai người vì thế thay đổi theo nội dung: dồn nhau thì gần lại, đầu
              hàng thì giãn ra. */}
          <DienVienHai kieu={A} camXuc={(noiA_ ? L.camXuc : L.camXucKia) || "trung_tinh"}
                    cuChi={noiA_ ? (L.cuChi || "nghi") : cuChiNghe}
                    nhin={noiA_ ? [0.3, 0] : [0.5, -0.06]} noi={noiA} t={giay}
                    nhan={noiA_ ? noiA.h : 0} nghieng={nghiengA} buoc={buocA}
                    giat={noiA_ ? 0 : _giatNghe} dangNoi={noiA_} doVat={vatA}
                    x={xA / zoom} y={Y_CHAN} scale={1.3 * coA} />
          <DienVienHai kieu={B} camXuc={(!noiA_ ? L.camXuc : L.camXucKia) || "trung_tinh"}
                    cuChi={!noiA_ ? (L.cuChi || "nghi") : cuChiNghe}
                    nhin={!noiA_ ? [-0.3, 0] : [-0.5, -0.06]} noi={noiB} t={giay + 1.7}
                    nhan={!noiA_ ? noiB.h : 0} nghieng={nghiengB} buoc={buocB}
                    giat={!noiA_ ? 0 : _giatNghe} dangNoi={!noiA_} doVat={vatB}
                    x={xB / zoom} y={Y_CHAN} scale={1.3 * coB} lat />
        </g>

        {tieuDe && giay < 2.6 ? (
          <text x={0} y={doc ? -640 : -470} textAnchor="middle" fontSize={doc ? 56 : 48}
                fontWeight={900} fill="#FFFFFF" stroke="#12131A" strokeWidth={11}
                paintOrder="stroke" opacity={kep((2.6 - giay) / 0.4)}>
            {tieuDe.slice(0, 40)}
          </text>
        ) : null}
        {/* 30/8 — PHỤ ĐỀ MANG MÀU CỦA NGƯỜI ĐANG NÓI.
            Anh: "2 nhân vật nói thì nên có 2 lời thoại 2 nhân vật có sự khác biệt". Trong hài
            hai người, nửa trò đùa nằm ở chỗ AI nói câu nào — mà phụ đề trắng trơn thì hai lượt
            liền nhau đọc ra như một người tự nói. Viền thẻ và chữ được tô lấy đúng màu áo của
            người ấy, nên mắt gán câu về đúng người trước cả khi nghe hết câu. */}
        <PhuDe tu={tu} giay={giay} nhan="#FFE27A" day={doc ? 812 : 470} s0={L.s} e0={L.e}
               vien={noiA_ ? A.ao : B.ao} ben={noiA_ ? -1 : 1} />
      </svg>
      </AbsoluteFill>

      {voMp3 ? <Audio src={staticFile(voMp3)} /> : null}
      {/* 30/8 — MỨC 0,07 LÀ PHÍ CÔNG. Đo trên khung thật ở nhịp đuôi (chỗ không còn giọng nói):
          mean −46 dB, đỉnh −32,7 dB. Trên loa điện thoại thì đó gần như im lặng — tức là có
          nhạc trong tệp nhưng khán giả không nghe thấy, và mọi lý do thêm nhạc đều mất.
          0,18 cho đỉnh khoảng −25 dB: nghe rõ là có nền, mà vẫn thấp hơn hẳn giọng nói (đỉnh
          −8,3 dB) nên không đè lời thoại. */}
      {nhac ? <Audio src={staticFile(nhac)} volume={0.18} loop /> : null}
      {luot.filter((x) => x.sfx).map((x, k) => (
        <Sequence key={k} from={Math.round(x.s * fps)} durationInFrames={Math.round(1.4 * fps)}>
          <Audio src={staticFile(x.sfx as string)} volume={0.3} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
