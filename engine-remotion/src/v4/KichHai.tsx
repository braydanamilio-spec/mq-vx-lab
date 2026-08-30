import React from "react";
import { AbsoluteFill, Audio, Img, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { CAM_XUC, KIEU_MAU, visemeTai, Kieu, TenCamXuc, TenCuChi, Tu } from "../v2/DienVien";
// 30/8 — MƯỜI KÊNH HÀI CHUYỂN SANG NHÂN VẬT QUE (anh chọn sau khi xem một phim ngắn stick).
// `DienVienHai` GIỮ NGUYÊN trên đĩa, không xoá: mười kênh dữ liệu vẫn dùng `DienVien` cùng họ,
// và nếu hướng này không hợp thì đổi lại chỉ là một dòng import. Xoá một engine đang chạy được
// để "cho gọn" là cách chắc chắn nhất để mất đường lui.
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
/** Màu áo làm SÁNG lên để dùng cho chữ phụ đề.
 *  Màu áo nguyên bản quá tối trên nền thẻ đen — chữ phải sáng mới đọc được, mà vẫn phải giữ đúng
 *  sắc để mắt nhận ra là người nào đang nói. Kéo 55% về phía trắng là điểm cân bằng đo được:
 *  đủ sáng để đọc ở cỡ khung điện thoại, còn đủ sắc để phân biệt hai người. */
const _sangChu = (h: string) => {
  const c = (h || "#DDDDDD").replace("#", "");
  if (c.length !== 6) return "#FFFFFF";
  const v = [0, 2, 4].map((i) => {
    const x = parseInt(c.slice(i, i + 2), 16);
    return Math.min(255, Math.round(x + (255 - x) * 0.55));
  });
  return "#" + v.map((x) => x.toString(16).padStart(2, "0")).join("");
};

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
  // ══ GÓC MÁY — thêm 30/8 ═══════════════════════════════════════════════════════════════
  // Anh: *"cần đa dạng góc quay chứ ko phải là zoom hay chuyển động"*. Cả hệ trước nay chỉ có
  // MỘT góc (máy chính diện) và mọi "thay đổi" là đổi khoảng cách — nên nó ra đúng cảm giác
  // "xa quá rồi tự dưng gần".
  //   hai_nguoi — cả hai trong khung, chính diện. Mở màn, cho biết ai đứng đâu với ai.
  //   qua_vai   — qua vai người NGHE nhìn người NÓI. Góc chủ lực của mọi phim đối thoại: thấy
  //               mặt người nói VÀ lưng người nghe cùng lúc, mà vẫn là một cú cận.
  //   mot_nguoi — chỉ người nói. Dành cho câu quan trọng nhất.
  goc?: "hai_nguoi" | "qua_vai" | "mot_nguoi";
  sfx?: string;
  chot?: boolean;               // lượt này là cú chốt -> có khoảng lặng trước, rung nhẹ khi nổ
  vatA?: string;                // đạo cụ người A cầm Ở LƯỢT NÀY (rỗng = tay trống)
  vatB?: string;
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
  // ══ BỎ HẲN DÁNG ĐI VÀ XÊ DỊCH ═══════════════════════════════════════════════════════
  // 30/8 — Anh: *"lúc nói hay di chuyển cả 2 nhân vật đều di chuyển chưa phù hợp, và cử chỉ đi
  // chưa phù hợp; NẾU KO LÀM ĐƯỢC ĐI THÌ NÊN CHO NHÂN VẬT ĐỨNG YÊN, khẽ thay đổi tư thế và động
  // tác tay là được"*.
  // Anh cho phép dứt khoát, và đó là lựa chọn đúng: một dáng đi vẽ chưa tới còn tệ hơn hẳn một
  // người đứng yên. Dáng đi cần bàn chân trượt đúng tốc độ thân, trọng tâm dồn đúng chân trụ, và
  // bóng đổ đi theo — sai một trong ba thì mắt đọc ra ngay là trượt băng.
  // Hai người đứng CỐ ĐỊNH. Sinh khí dồn hết sang thứ vốn làm tốt: tư thế đổi mượt, tay đánh
  // nhịp theo lời, nét mặt, khẩu hình. Đây cũng đúng "limited animation" — cách hoạt hình truyền
  // hình Mỹ vẫn làm suốt tám mươi năm.
  const dichA = -292, dichB = 292;
  // ══ MÁY LIA TỚI NGƯỜI, NGƯỜI KHÔNG DẠT RA HAI BÊN ═══════════════════════════════════════
  // 30/8 — Anh: *"mỗi khi zoom chuyển nhân vật thì nhân vật nhảy sang vị trí khác… nên giữ
  // nguyên và zoom hay focus vào từng nhân vật chứ nhân vật ko nhảy thế"*.
  // Đúng, và bản cũ làm sai hẳn về ngôn ngữ điện ảnh: hễ vào cỡ cận là nhân khoảng cách hai
  // người lên 3,6 lần để đẩy người-không-nói ra ngoài khung. Trên màn hình nó đọc ra là **hai
  // diễn viên bị kéo dạt sang hai bên**, đúng lúc máy đang áp sát — chuyện không xảy ra ở bất
  // kỳ đoạn phim nào.
  // Máy quay áp sát thì nó LIA TỚI một người. Diễn viên đứng nguyên chỗ; thứ dịch chuyển là
  // KHUNG HÌNH. Nên nay hai người có toạ độ cố định suốt cả tập, còn ở cỡ cận thì cả nhóm được
  // dịch ngang sao cho người đang nói về giữa khung.
  // Và dịch phải NỘI SUY trong nửa giây đầu lượt, cùng nhịp với độ phóng — cắt phựt sang một
  // khung khác chính là "nhảy" mà anh nhìn thấy, dù lần này là khung nhảy chứ không phải người.
  const xA = dichA;
  const xB = dichB;
  // (khối lia máy đã dời xuống dưới `zoom` — xem chú thích ở đó)

  const buocA = 0, buocB = 0;

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
  // Cử chỉ của lượt TRƯỚC, để nội suy sang tư thế mới thay vì nhảy khung.
  const _Lt = i > 0 ? luot[i - 1] : L;
  const _noiAt = _Lt.ai === 0;
  const _ccNgheT = NGHE[(_Lt.camXucKia || "trung_tinh") as string] || "nghi";
  const ccTruocA = (_noiAt ? (_Lt.cuChi || "nghi") : _ccNgheT) as TenCuChi;
  const ccTruocB = (!_noiAt ? (_Lt.cuChi || "nghi") : _ccNgheT) as TenCuChi;
  // Nửa giây đầu mỗi lượt là quãng chuyển tư thế: ngắn hơn thì vẫn giật, dài hơn thì tay lờ đờ.
  // ══ HAI NGƯỜI KHÔNG ĐỔI TƯ THẾ CÙNG MỘT LÚC ═══════════════════════════════════════════
  // Anh nêu từ đầu: *"sao cử động cả 2 cùng cử động đồng thời 1 lúc"*. Tôi đã sửa phần DI
  // CHUYỂN (bỏ hẳn đi lại) nhưng bỏ sót phần CỬ CHỈ: cả hai vẫn dùng chung một `doiCC`, nên ở
  // đúng khung hình bắt đầu mỗi lượt, bốn cánh tay cùng khởi hành.
  // Trong đối thoại thật, người nói đổi tư thế TRƯỚC — tư thế đi cùng câu nói — còn người nghe
  // phản ứng SAU khi đã nghe được vài chữ. Lệch một phần năm giây là đủ để mắt đọc ra quan hệ
  // nhân quả giữa hai người, thay vì hai con rối chung một sợi dây.
  const doiCC = kep((giay - L.s) / 0.58);
  const doiCCnghe = kep((giay - L.s - 0.2) / 0.58);

  // CÚ GIẬT MÌNH của người NGHE, đúng vào lúc câu chốt vừa rơi.
  // Trong hài hình ảnh, thứ báo cho khán giả "chỗ này buồn cười" không phải tiếng cười lồng mà
  // là PHẢN ỨNG của người trên màn hình. Cho nó bắt đầu trễ 0,35 giây so với đầu lượt chốt —
  // đúng nhịp một người nghe xong mới kịp hiểu.
  // CÚ GIẬT MÌNH PHẢI NỔ ĐÚNG LÚC MÁY CẮT SANG. Bản trước tính từ đầu lượt chốt + 0,35 giây,
  // nên tới lúc máy quay sang người nghe thì cú giật đã tắt từ lâu — máy cắt sang một khuôn mặt
  // đứng yên. Mốc đúng là thời điểm câu chốt VỪA DỨT, tức chỗ bắt đầu nhịp đuôi.
  const _giatNghe = L.chot ? kep((giay - (L.e - 1.25)) / 1.5) : 0;

  // ══ HOOK HÌNH ẢNH 1,4 GIÂY ĐẦU ══════════════════════════════════════════════════════
  // 30/8 — Bộ 500 prompt anh gửi ghi rõ nhịp mở của mỗi tập:
  //   *"0.0–1.5s: Use a quick wide shot, then a close-up on the final facial reaction.
  //     Establish the comedic situation immediately with a clear visual hook."*
  // Bản của mình mở bằng hai người đứng yên rồi bắt đầu nói — không có hook nào cả, và khán giả
  // lướt short quyết định đúng trong quãng ấy.
  // Nên 1,4 giây đầu: máy quay TIẾN VÀO (từ rộng hơn về cỡ đã định) và người nói NHÚN người một
  // nhịp. Hai chuyển động rất nhỏ, nhưng chúng làm khung "đang xảy ra chuyện" thay vì "đang chờ".
  const _hook = kep(1 - giay / 1.4);
  const hookZoom = 1 - _hook * 0.16;
  const hookNhun = Math.sin(kep(giay / 0.55) * Math.PI) * 0.4;

  // 30/8 — ĐO ĐƯỢC: nhân vật chỉ chiếm ~30% chiều cao khung. Trên điện thoại thì mặt bé đến
  // mức không đọc được nét mặt, mà cú chốt của hài nằm ở nét mặt. Short phải đóng cận: người
  // chiếm quá nửa khung. Nâng cả độ phóng lẫn cỡ người, và hạ chân xuống thấp để phần trống
  // phía trên không thừa.
  // 30/8 — CỠ MÁY PHẢI CHÊNH ĐỦ ĐỂ MẮT THẤY.
  // Một tập chỉ còn MỘT bối cảnh (xem `dung_luot`), nên toàn bộ nhịp thị giác dồn vào máy quay.
  // Dải 1,42–1,92 quá hẹp: bốn lượt liền nhau ra bốn khung gần y hệt. Nới thành 1,25–2,25 thì
  // toàn cảnh đọc ra là "đang ở đâu" còn cận cảnh đọc ra là "nhìn mặt nó kìa".
  const _can = (L.co || "trung") === "can";
  // 30/8 — Anh: *"chỗ cuối đang bị zoom videos lên hơi thô ko hợp"*.
  // Hai lỗi trong một: cỡ cận 3,6 gấp hơn HAI LẦN cỡ trung — cú nhảy quá lớn; và độ phóng đổi
  // NGAY tại ranh giới lượt, tức nhảy trọn một nấc trong đúng một khung hình.
  // Hạ cận xuống 2,4 (vẫn đủ thấy nét mặt) và NỘI SUY độ phóng trong nửa giây đầu mỗi lượt —
  // máy quay tiến vào, không cắt phựt.
  const KH: Record<string, number> = doc
    // 30/8 — Anh: *"khi đổi góc quay vào 1 nhân vật thì tránh zoom quá gần"*, và *"nhớ phải
    // đúng theo tiêu chuẩn làm phim chuyên nghiệp"*.
    // Ở 2,4 lần, khung chỉ còn đầu và ngực — trong ngôn ngữ quay phim đó là "big close-up",
    // cỡ dành cho khoảnh khắc căng nhất của một bộ phim, không phải cho một câu thoại hài.
    // Cỡ đúng ở đây là "medium close-up": đầu, vai và một phần thân trên, đủ để thấy cả nét mặt
    // lẫn cử chỉ tay — mà cử chỉ tay chính là nửa phần diễn của nhân vật này.
    // Và một luật của nghề: **không cắt ngang khớp**. Cắt ở cổ, khuỷu hay đầu gối làm người xem
    // thấy khó chịu mà không gọi tên được; cắt ở giữa cánh tay hoặc giữa thân thì không.
    ? { rong: 1.18, trung: 1.52, can: 1.86 }
    : { rong: 0.84, trung: 1.06, can: 1.6 };
  const _zTruoc = KH[((i > 0 ? luot[i - 1].co : L.co) || "trung") as string] || 1.68;
  const _zNay = KH[(L.co || "trung") as string] || 1.68;
  // Đổi cỡ máy trong 0,5 giây là một cú giật; máy quay thật mất khoảng một giây để tiến vào
  // một cỡ khác, và có gia tốc ở hai đầu. Kéo dài lên 0,9 giây.
  const zoom = trn(_zTruoc, _zNay, muot(kep((giay - L.s) / 0.9)))
               * (1 + truocChot * 0.05) * hookZoom;
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
  const _canNay = (L.co || "trung") === "can";
  const _canTruoc = ((i > 0 ? luot[i - 1].co : L.co) || "trung") === "can";
  // 30/8, sửa lần hai — anh gửi ba khung liên tiếp: nhân vật trôi dần ra khỏi khung rồi biến
  // mất hẳn, chỉ còn nền và một mảng áo ở mép.
  // Lỗi ở đúng một hệ số thừa. Nhân vật được đặt ở `xA / zoom` bên trong một nhóm có
  // `scale(zoom)`, nên vị trí THẬT của nó trên khung là `xA` — phép chia và phép nhân đã triệt
  // tiêu nhau. Muốn kéo nó về giữa thì dịch khung đi `-xA`. Tôi lại nhân thêm `zoom` lần nữa,
  // thành dịch `-xA * zoom`: ở cỡ cận (zoom 2,4) là dịch 700 điểm thay vì 292, đẩy chính người
  // đang nói văng ra mép rồi ra hẳn ngoài.
  // Bài học: khi một toạ độ đã đi qua phép chia rồi phép nhân của cùng một hệ số, nó KHÔNG còn
  // mang hệ số ấy nữa. Đọc chuỗi biến đổi từ trong ra ngoài trước khi cộng thêm một phép nào.
  // Người đang nói nay LUÔN ở giữa nhờ bố cục theo góc, nên không cần lia bù nữa. Giữ hàm để
  // đọc lịch sử: đây từng là cách chữa lỗi "nhân vật văng khỏi khung", và nó chữa triệu chứng
  // (kéo khung theo người) chứ không chữa nguyên nhân (bố cục cố định không hợp cỡ máy).
  const _mucTieu = (_co: boolean) => 0;
  // ══ BỐ CỤC THEO GÓC ═══════════════════════════════════════════════════════════════════
  // Ba góc, ba cách đặt người — và cả ba đều đưa NGƯỜI ĐANG NÓI về giữa khung. Đó cũng là cách
  // chữa triệt để lỗi anh nêu ("nhân vật vẫn bị đứng ra mép rìa"): trước nay chỉ có một bố cục
  // cố định ±292, nên hễ máy tiến vào là ai đó rơi ra mép. Nay vị trí do GÓC quyết.
  //
  // Quy tắc 180 độ giữ nguyên ở mọi góc: người A luôn đứng bên trái, B bên phải, nên A luôn
  // nhìn sang phải và B nhìn sang trái. Không bao giờ đổi bên giữa chừng.
  const _goc = (L.goc || "hai_nguoi") as string;
  // `qua_vai`: người nghe thành TIỀN CẢNH — to hơn, tối hơn, đứng lệch hẳn ra mép và bị khung
  // cắt bớt. Đó chính là cái làm nên chiều sâu của cú qua-vai: một khối gần ống kính, mất nét,
  // đóng khung cho khuôn mặt ở xa.
  const _quaVai = _goc === "qua_vai";
  const _motNguoi = _goc === "mot_nguoi";
  // Soi bốn khung dựng thử thì ba góc ra GIỐNG HỆT NHAU: hai người luôn sát nhau, không tiền
  // cảnh nào, và ở góc "một người" vẫn thấy cả hai. Tôi khai đủ biến nhưng chỉ nối chúng vào
  // BÓNG ĐỔ, quên nối vào chính nhân vật — đúng lỗi cổng `kiem_gan` sinh ra để chặn, mắc lại
  // ngay trong ngày viết nó.
  // Ba góc phải cho ba BỐ CỤC khác hẳn, không phải ba biến thể của một bố cục:
  const _xA = _quaVai ? (noiA_ ? -40 : -430)      // qua vai: người nói lệch nhẹ khỏi tâm (quy
            : _motNguoi ? (noiA_ ? 0 : -9999)     //   tắc một-phần-ba), người nghe ra sát mép
            : -292;                               //   và bị khung cắt bớt — đó là tiền cảnh
  const _xB = _quaVai ? (noiA_ ? 430 : 40)        // một người: người kia đẩy hẳn ra ngoài
            : _motNguoi ? (noiA_ ? 9999 : 0)
            : 292;
  // Tiền cảnh gần ống kính nên TO hơn và TỐI hơn — hai dấu hiệu chiều sâu mà mắt đọc tức thì.
  const _coA = _quaVai && !noiA_ ? 1.5 : 1;
  const _coB = _quaVai && noiA_ ? 1.5 : 1;
  // Anh gửi khung: người tiền cảnh TRONG SUỐT, nhìn xuyên qua thấy cả xe phía sau — đọc ra là
  // một bóng ma chứ không phải một người đứng gần ống kính.
  // Lỗi ở chỗ tôi dùng ĐỘ MỜ để tả chiều sâu. Trong hoạt hình, vật ở tiền cảnh không mờ đi —
  // nó TỐI đi (ngược sáng) và MẤT NÉT. Cả hai đều là hiện tượng quang học thật; độ mờ thì
  // không, và mắt đọc ra ngay là sai.
  const _toiA = _quaVai && !noiA_;
  const _toiB = _quaVai && noiA_;

  const _liaTam = trn(_mucTieu(_canTruoc), _mucTieu(_canNay),
                      muot(kep((giay - L.s) / 0.9)));
  // ▲ KHỐI TRÊN PHẢI NẰM SAU `zoom`. Bản đầu tôi đặt nó cạnh `dichA`/`dichB` cho gọn ý, nhưng
  // `_mucTieu` đọc `zoom` — mà `zoom` mãi mấy chục dòng dưới mới khai. Dựng ra:
  //     ReferenceError: Cannot access 'zoom' before initialization
  // Đây là lần thứ NĂM cùng một lỗi trong kho này, và cả năm lần đều qua được `tsc` lẫn
  // `esbuild`: không cổng nào bắt được vì mã hoàn toàn hợp lệ về kiểu và cú pháp — nó chỉ sai
  // về THỨ TỰ, và thứ tự chỉ lộ ra lúc chạy.
  // Đặt mã cạnh thứ nó nói VỀ thì dễ đọc; đặt cạnh thứ nó ĐỌC TỪ thì chạy được. Khi hai điều ấy
  // xung khắc, chạy được thắng — và để lại một dòng chỉ đường như dòng ở chỗ cũ.
  // Anh: *"tránh lia zoom máy quá nhanh nhiều"*. Biên độ lia hạ từ 26 xuống 14 và chu kỳ chậm
  // lại: một chuyển động máy quay tốt là thứ người xem KHÔNG nhận ra — nó chỉ giữ cho khung
  // "còn sống". Thấy được máy đang lia nghĩa là lia quá tay.
  const liaNhe = Math.sin(giay * 0.19 + i * 1.7) * 14;

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

  // ══ CẮT CẢNH PHẢN ỨNG — máy quay bỏ người nói, quay sang NGƯỜI NGHE ═════════════════
  // 30/8 — Đo trên khung thật: ở cú chốt, máy đang cận vào người NÓI (đúng, họ đang nói câu
  // chốt) — nhưng thứ buồn cười là PHẢN ỨNG của người NGHE, mà người nghe thì đã bị đẩy hẳn ra
  // ngoài khung. Nên cú chốt nổ ở một chỗ không ai nhìn thấy.
  //
  // Bộ 500 prompt anh gửi ghi đúng cách làm, ngay ở dòng nhịp đầu tiên của mọi tập:
  //   *"a quick wide shot, then a CLOSE-UP ON THE FINAL FACIAL REACTION"*.
  // Đó là "reaction cut" — cắt sang mặt người nghe ngay sau khi câu chốt rơi. Trong hài, nó là
  // cú đánh thứ hai, và thường là cú làm người ta bật cười chứ không phải câu nói.
  //
  // Nhịp đuôi dài 1,2 giây; cắt sang người nghe khi vào quãng ấy.
  // Ở nhịp phản ứng, người NGHE mới là người diễn — `dangNoi` phải trả lại đủ biên độ cho họ,
  // không thì máy cắt sang một pho tượng. (Chú thích để ở đây, KHÔNG để giữa các thuộc tính JSX:
  // `{/* */}` xen giữa thuộc tính là lỗi cú pháp — đã dính bốn lần, xem luật 7t.)
  const _phanUng = !!L.chot && giay > L.e - 1.25;
  const _aiTrungTam = _phanUng ? !noiA_ : noiA_;
  const _tamNguoi = _aiTrungTam ? xA : xB;
  // Khi cắt sang người nghe thì lia RẤT nhanh (0,12 giây) — cắt cảnh trong hài phải dứt khoát,
  // lia chậm biến một cú cắt thành một cú trượt và mất hết sức nặng.
  const liaVao = _canhCan
    ? -_tamNguoi * muot(kep(_phanUng ? (giay - (L.e - 1.25)) / 0.12 : (giay - L.s) / 0.28))
      - (_phanUng ? 0 : 0)
    : 0;
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
          {/* 30/8 — Anh: *"người vẫn hơi lơ lửng trong 1 số trường hợp"*.
              Chân ĐÃ đặt đúng đường sàn — đo lại thấy không lệch điểm nào. Cái thiếu là BÓNG.
              Mắt người không đọc toạ độ; nó đọc bóng tiếp xúc để biết một vật đứng trên mặt
              phẳng hay treo trước nó. Thiếu bóng thì dù chân đúng chỗ, hình vẫn đọc ra là một
              nhân vật DÁN LÊN ảnh nền — và càng rõ khi ảnh nền có sàn với phối cảnh riêng, vì
              lúc ấy có hai mặt sàn đối nhau mà không mặt nào nhận lấy nhân vật.
              Đây là thứ hoạt hình vẽ tay nào cũng có và không ai để ý khi nó có mặt. */}
          <radialGradient id="bongchan">
            <stop offset="0%" stopColor="#000" stopOpacity={0.34} />
            <stop offset="55%" stopColor="#000" stopOpacity={0.17} />
            <stop offset="100%" stopColor="#000" stopOpacity={0} />
          </radialGradient>
          <linearGradient id="san" x1="0" y1="0" x2="0" y2="1">
            {/* Mờ hẳn: đây là LỚP BẢO HIỂM cho trường hợp ảnh nền không có sàn, không phải
                một tấm sàn để nhìn. Đục quá thì nó đè lên mặt đường có sẵn của ảnh và đọc ra
                là một tờ giấy dán ngang khung. */}
            <stop offset="0%" stopColor={mucNen} stopOpacity={0.0} />
            <stop offset="30%" stopColor={mucNen} stopOpacity={0.16} />
            <stop offset="100%" stopColor={mucNen} stopOpacity={0.4} />
          </linearGradient>
        </defs>
        <g transform={`translate(${rung + lia + _liaTam} ${dichY}) scale(${zoom})`} style={{ transformOrigin: "0px 0px" }}>
          <rect x={-1600} y={Y_CHAN - 34} width={3200} height={1400} fill="url(#san)" />
          <line x1={-1600} y1={Y_CHAN - 34} x2={1600} y2={Y_CHAN - 34}
                stroke="#00000014" strokeWidth={2} />
          {/* Bóng vẽ TRƯỚC nhân vật (nằm dưới trong thứ tự vẽ) và nhân theo đúng hệ số cỡ người
              đang dùng, nên khi cỡ ấy đổi thì bóng đổi cùng thay vì trôi thành một vệt rời.
              Hiện `coA` và `coB` đều bằng 1 — hiệu ứng phóng to người đang nói đã bỏ theo yêu
              cầu của anh ("nhân vật cao lên, nhân vật kia nhỏ lại rất thiếu thẩm mỹ") — nên hai
              bóng bằng nhau. Vẫn buộc bóng vào hệ số ấy để nếu sau này cỡ người lại đổi thì
              bóng không phải đi sửa lần nữa. */}
          <ellipse cx={_xA / zoom} cy={Y_CHAN - 4} rx={110 * coA * _coA} ry={16 * coA}
                   fill="url(#bongchan)" />
          <ellipse cx={_xB / zoom} cy={Y_CHAN - 4} rx={110 * coB * _coB} ry={16 * coB}
                   fill="url(#bongchan)" />
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
          <g style={_toiA ? { filter: "brightness(0.52) saturate(0.7) blur(1.4px)" } : undefined}>
          <DienVienHai kieu={A} camXuc={(noiA_ ? L.camXuc : L.camXucKia) || "trung_tinh"}
                    cuChi={noiA_ ? (L.cuChi || "nghi") : cuChiNghe}
                    nhin={noiA_ ? [0.3, 0] : [0.5, -0.06]} noi={noiA} t={giay}
                    nhan={(noiA_ ? noiA.h : 0) + (noiA_ ? hookNhun : 0)} nghieng={nghiengA} buoc={buocA}
                    giat={noiA_ ? 0 : _giatNghe}
                    cuChiTruoc={ccTruocA} doiCuChi={noiA_ ? doiCC : doiCCnghe} tuoiCanh={giay - L.s}
                    dangNoi={noiA_ || (_phanUng && !noiA_)} doVat={L.vatA ?? vatA}
                    x={_xA / zoom} y={Y_CHAN} scale={1.12 * coA * _coA} />
          </g>
          <g style={_toiB ? { filter: "brightness(0.52) saturate(0.7) blur(1.4px)" } : undefined}>
          <DienVienHai kieu={B} camXuc={(!noiA_ ? L.camXuc : L.camXucKia) || "trung_tinh"}
                    cuChi={!noiA_ ? (L.cuChi || "nghi") : cuChiNghe}
                    nhin={!noiA_ ? [-0.3, 0] : [-0.5, -0.06]} noi={noiB} t={giay + 1.7}
                    nhan={(!noiA_ ? noiB.h : 0) + (!noiA_ ? hookNhun : 0)} nghieng={nghiengB} buoc={buocB}
                    giat={!noiA_ ? 0 : _giatNghe}
                    cuChiTruoc={ccTruocB} doiCuChi={noiA_ ? doiCCnghe : doiCC} tuoiCanh={giay - L.s}
                    dangNoi={!noiA_ || (_phanUng && noiA_)} doVat={L.vatB ?? vatB}
                    x={_xB / zoom} y={Y_CHAN} scale={1.12 * coB * _coB} lat />
          </g>
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
        {/* 30/8 — Anh: *"phần sub nhân vật cần thay đổi màu riêng cho mỗi nhân vật để phân
            biệt"*. Bản trước chỉ đổi VIỀN thẻ và một chấm ở mép — chữ vẫn trắng cho cả hai
            người, mà mắt đọc CHỮ chứ không đọc viền. Nay chính chữ mang màu người nói. */}
        <PhuDe tu={tu} giay={giay} nhan="#FFE27A" day={doc ? 812 : 470} s0={L.s} e0={L.e}
               vien={noiA_ ? A.ao : B.ao} ben={noiA_ ? -1 : 1}
               chuMau={_sangChu(noiA_ ? A.ao : B.ao)} />
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
