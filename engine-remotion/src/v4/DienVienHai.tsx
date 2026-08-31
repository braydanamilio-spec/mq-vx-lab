import React from "react";
import { CAM_XUC, CU_CHI, Kieu, TenCamXuc, TenCuChi, Tu, visemeTai } from "../v2/DienVien";

/**
 * DIỄN VIÊN HÀI — tạo hình hoạt hình Mỹ, riêng cho 10 kênh thế hệ 4 (30/8/2026).
 *
 * Anh: *"nhân vật cần chuẩn hoạt hình kiểu simpson hay phim hoạt hình mỹ ăn khách trước đó,
 * nhớ ko vi phạm bản quyền, nhưng vẫn đảm bảo được tính dễ thương hài hước đẹp, ko khô cứng
 * như hiện tại… nâng cấp sao cho mượt mà chuyển động, biểu cảm, lời nói"*.
 *
 * ── VÌ SAO LÀ TỆP MỚI, KHÔNG SỬA `v2/DienVien` ──────────────────────────────────────────
 * `v2/DienVien` đang chạy cho 10 kênh dữ liệu thế hệ 3. Sửa nó là sửa luôn mười kênh ấy trong
 * khi chúng đang đạt chuẩn — đúng thứ anh dặn tránh ("ko động vào channel đang ok"). Bộ hài
 * cần tạo hình khác hẳn, nên nó được một tệp riêng và mượn lại các bảng dữ liệu thuần
 * (cảm xúc, cử chỉ, khẩu hình) của tệp cũ.
 *
 * ── KHÁC BẢN CŨ Ở ĐÂU, VÀ VÌ SAO ────────────────────────────────────────────────────────
 * Bản cũ đọc ra "khô cứng" vì bốn thứ, không phải một:
 *
 *  1. **TỈ LỆ NGƯỜI THẬT.** Đầu bằng 1/6 thân. Hoạt hình Mỹ ăn khách để đầu 1/3,5 – 1/4: đầu
 *     to thì mắt to, mà mắt mới là chỗ khán giả đọc cảm xúc. Đây là thay đổi có tác dụng lớn
 *     nhất, và nó thuộc về TỈ LỆ — không sao chép nét vẽ của ai.
 *  2. **CHI THỂ LÀ QUE + KHỚP LÀ BI TRÔI.** Bàn tay là hình tròn rời khỏi cánh tay, nhìn ra
 *     ngay là hình ghép. Nay tay chân vẽ bằng nét dày bo tròn đầu (thành hình con nhộng liền
 *     mạch) và bàn tay là **găng bốn ngón** — ngôn ngữ tạo hình chung của hoạt hình phương
 *     Tây từ những năm 1930, không thuộc về một hãng nào.
 *  3. **KHÔNG CÓ NÉN – GIÃN.** Người thật không nén giãn, nhân vật hoạt hình thì có: mỗi nhịp
 *     thở và mỗi lần nhấn giọng, thân hơi lùn xuống rồi bật cao lên. Thiếu nó thì hình đứng
 *     yên như tượng dù mọi khớp đều động.
 *  4. **MỌI THỨ CHUYỂN ĐỘNG THEO ĐƯỜNG THẲNG.** Nay cử chỉ đi theo cung có gia tốc, và tóc,
 *     vạt áo, đuôi tóc trễ lại một nhịp so với đầu (`treo`).
 *
 * ── CHỖ CỐ Ý KHÔNG LÀM ──────────────────────────────────────────────────────────────────
 * Không da vàng, không răng vẩu, không mắt lồi có tròng đen bằng hạt đậu, không bốn ngón tay
 * vàng — đó là DẤU HIỆU NHẬN DẠNG của những bộ phim cụ thể và là chỗ bản quyền bám vào.
 * Thứ mượn được là NGUYÊN TẮC dựng hình (tỉ lệ đầu–thân, nét bao dày, găng tay, nén–giãn,
 * chuyển động thứ cấp) — những nguyên tắc ấy là kiến thức chung của ngành, không của ai cả.
 */

// ══════════════════════════════════════════════════════════════════════════════════════════
// BẢNG CỬ CHỈ RIÊNG CHO CẢNH HAI NGƯỜI ĐỨNG CẠNH NHAU
// ------------------------------------------------------------------------------------------
// 30/8 — Đo trên khung thật: cử chỉ CHỈ TAY của bảng dùng chung (`v2/DienVien.CU_CHI`) đưa cánh
// tay đi NGANG, và trong cảnh hai người đứng cạnh nhau thì bàn tay hạ đúng xuống vai người kia —
// hai hình vẽ lồng vào nhau, lỗi vật lý mắt bắt được ngay.
//
// Không sửa bảng gốc, vì bảng ấy đang chạy cho mười kênh dữ liệu thế hệ 3 — ở đó chỉ có MỘT
// người trong khung nên chỉ ngang là đúng và đẹp. Cùng một cử chỉ, hai bối cảnh, hai giá trị
// đúng khác nhau: đó chính là lý do bộ hài cần bảng riêng.
//
// Nguyên tắc của bảng này: **mọi cử chỉ đều hướng LÊN hoặc VÀO TRONG, không hướng NGANG.**
// Cánh tay duỗi ngang hết cỡ dài hơn khoảng trống giữa hai người, nên chỉ cần một cử chỉ ngang
// là chạm. Chỉ lên trời còn đúng ngôn ngữ hài hơn: nó là điệu bộ "tuyên bố", còn chỉ ngang vào
// mặt người đối diện thì vừa thô vừa che mất mặt người ấy.
// ══ BIÊN ĐỘ GẬP KHUỶU — sửa 30/8, lần cuối cùng ═══════════════════════════════════════════
// Anh: *"tay vẫn cong cong khèo khèo thế"* — nói sau khi tôi ĐÃ hoàn tác cách vẽ về bản cũ.
// Đó là dữ kiện quan trọng nhất: **cả bản cũ lẫn ba bản mới đều cong khèo như nhau.** Nghĩa là
// suốt ba lượt tôi sửa nhầm chỗ — vấn đề chưa bao giờ nằm ở cách VẼ (nét kẻ hay mảnh cắt hay
// xương), nó nằm ở BẢNG SỐ.
// Bảng có `chong_nanh: khuyuT = -86` và `suy_nghi: khuyuP = -96`: cẳng tay quay ngược gần chín
// mươi độ so với cánh tay. Ở góc ấy thì cách vẽ nào cũng ra hình móc câu — đường cong thì phình
// thành lưỡi liềm, xương thì gãy gập, mảnh cắt thì như khớp giả.
// Hạ biên độ gập còn khoảng một nửa. Giữ nguyên dấu (chiều gập) và giữ những giá trị vốn đã nhỏ.
//
// Bài học đắt nhất phiên: ba lượt liền tôi đổi KIẾN TRÚC để chữa một triệu chứng do MỘT BẢNG SỐ
// gây ra. Dấu hiệu đáng lẽ phải nhận ra ngay: nếu đổi hẳn cách làm mà triệu chứng không đổi,
// thì cái hỏng nằm ở phần KHÔNG đổi.
const CU_CHI_HAI: Record<string, { vaiT: number; khuyuT: number; vaiP: number; khuyuP: number }> = {
  // ══ VIẾT LẠI TOÀN BẢNG — 30/8, sau khi anh nhắc lần thứ tư về tay ══════════════════════
  // Anh: *"tự dưng dơ tay lên trời thấy lỗi… fix 1 lần triệt để"*. Trước nay tôi vá từng cử chỉ
  // một, và mỗi lần vá xong lại còn một cái khác vung quá tay. Lần này sửa cả bảng theo MỘT
  // luật, thay vì chỉnh từng dòng.
  //
  // QUY ƯỚC GÓC ở tệp này: **0° = thẳng lên trời · 90° = ngang vai · 180° = buông thẳng xuống.**
  // Đọc lại bảng cũ theo quy ước ấy thì ra ngay thủ phạm:
  //     chi:      vaiP = -86   → tay chỉ THẲNG LÊN TRỜI
  //     gio_len:  vaiP = -96   → còn quá thẳng đứng
  // Không ai vừa nói chuyện vừa giơ tay lên trời, trừ lúc hô khẩu hiệu.
  //
  // DẢI ĐÚNG cho người đang trò chuyện, đo từ chính phim tham khảo anh gửi:
  //     buông tự nhiên  165–175°     ·  tay ngang ngực   110–135°
  //     chỉ về phía kia  95–110°     ·  cao nhất cho phép      70°
  // Dưới 70° là vung quá vai — chỉ dành cho một khoảnh khắc kinh ngạc, và cả bảng này không có
  // khoảnh khắc nào như thế. Nên **không dòng nào dưới 70**, và đó là luật để lần sau ai đọc
  // bảng cũng biết ngưỡng ở đâu.
  // Quy ước: P() theo trục SVG (y hướng XUỐNG), nên 90°=xuôi thẳng, 180°=ngang trái,
  // 0°=ngang phải, 270°=thẳng lên. `khuyu` CỘNG vào góc vai; gập vào trong là ÂM cho tay
  // trái và DƯƠNG cho tay phải. Khuỷu người chỉ gập một chiều, tối đa ~145° — mọi giá trị
  // dưới đây nằm trong ngưỡng đó.
  //
  // Bảng cũ hỏng theo HAI cách cùng lúc, và bảng tư thế nền trơn mới lộ ra cả hai:
  //  · SAI HƯỚNG: `nghi` đặt vaiP = 168, tức tay PHẢI vắt ngang sang TRÁI trong lúc đang
  //    buông xuôi. Nhiều dòng khác cũng vậy — hai tay cùng chìa về một phía.
  //  · MẤT BIÊN ĐỘ: lượt trước tôi chia đôi mọi góc khuỷu để chữa "tay khèo", làm cả mười
  //    cử chỉ dẹt thành một tư thế duy nhất — khoanh tay không khoanh, chống hông không
  //    chống. Chữa lỗi này bằng cách phá tính năng kia.
  // Lỗi "khèo" thật ra nằm ở NÉT VẼ (một đường Q không có khớp), không nằm ở bảng số. Sửa
  // đúng chỗ rồi thì bảng được trả lại biên độ đầy đủ.
  nghi:       { vaiT: 96,  khuyuT: -14,  vaiP: 84, khuyuP: 14 },   // buông xuôi, khuỷu cong nhẹ
  chi:        { vaiT: 100, khuyuT: -16,  vaiP: 34, khuyuP: 10 },   // tay phải chỉ chếch ngang
  mo_tay:     { vaiT: 138, khuyuT: -46,  vaiP: 42, khuyuP: 46 },   // mở hai tay ra trước-ngoài
  dem:        { vaiT: 118, khuyuT: -78,  vaiP: 68, khuyuP: 74 },   // hai cẳng thu vào giữa ngực
  // Chống cằm: cánh tay đưa gần NGANG (10°) rồi cẳng hất ngược lên (-125° → hướng 245°, tức
  // lên-vào). Bản trước để vai 35°/khuỷu 138° nên bàn tay dừng ở tầm ngực, và cổng cử chỉ đo
  // ra nó chỉ cách `ngan_ngam` 50 đơn vị — hai tư thế khác tên nhưng trên màn hình là một.
  suy_nghi:   { vaiT: 98,  khuyuT: -12,  vaiP: 10, khuyuP: -125 },  // tay chống cằm, bàn TRÊN vai
  nhun_vai:   { vaiT: 128, khuyuT: -62,  vaiP: 52, khuyuP: 62 },   // khuỷu gập, hai bàn ngửa
  gio_len:    { vaiT: 100, khuyuT: -14,  vaiP: 300, khuyuP: 20 },  // giơ CHẾCH lên, không thẳng đứng
  // Khoanh tay: cánh tay phải đưa gần NGANG (155°/25°) chứ không xuôi. Đặt vai xuôi thì khuỷu
  // rơi xuống ngang hông, và hai cẳng bắt chéo ở BỤNG — đọc ra là "chắp tay trước bụng", một
  // tư thế nhũn nhặn, trái hẳn nghĩa phòng thủ/khó chịu mà khoanh tay cần truyền.
  khoanh_tay: { vaiT: 155, khuyuT: -140, vaiP: 25, khuyuP: 140 },  // hai cẳng bắt chéo ngang NGỰC
  chong_nanh: { vaiT: 132, khuyuT: -104, vaiP: 48, khuyuP: 104 },  // hai bàn về hông
  ngan_ngam:  { vaiT: 98,  khuyuT: -12,  vaiP: 56, khuyuP: 98 },   // một buông, một chống hông
};


const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const trn = (a: number, b: number, t: number) => a + (b - a) * kep(t);
// Cung có gia tốc hai đầu: rời điểm đầu chậm, giữa nhanh, vào điểm cuối chậm. Tay người thật
// không quay đều tốc độ, và mọi phép nội suy tư thế trong tệp này đều đi qua nó.
// 30/8 — khai ở TẦNG MODULE chứ không trong thân component: phép nội suy cử chỉ nằm ở đầu thân
// hàm, trước chỗ khai cũ, nên nó đọc phải một hằng chưa khởi tạo và render chết. Lần thứ tư
// dính họ lỗi này (xem luật 7ae) — thứ dùng ở nhiều chỗ thì khai ở chỗ ai cũng thấy.
const muot = (v: number) => v * v * (3 - 2 * v);
const D = (deg: number) => (deg * Math.PI) / 180;
const P = (x: number, y: number, d: number, a: number): [number, number] =>
  [x + Math.cos(D(a)) * d, y + Math.sin(D(a)) * d];

/** Trễ pha + dao động tắt dần — cho tóc, đuôi tóc, vạt áo đi sau đầu một nhịp. */
const treo = (dich: number, t: number, tre = 0.13, bien = 1) =>
  dich + Math.sin((t - tre) * 7.5) * bien * 0.35 * Math.exp(-Math.abs(Math.sin(t * 1.1)) * 0.6);

export type PropsHai = {
  kieu: Kieu;
  camXuc: TenCamXuc;
  cuChi: TenCuChi;
  nhin: [number, number];
  noi: { w: number; h: number; tron: number };
  t: number;
  nhan?: number;                 // 0..1 — độ nhấn của lượt thoại này (dùng cho nén–giãn)
  dangNoi?: boolean;             // người này có đang nói không — quyết định được phép diễn bao nhiêu
  doVat?: string;                // đạo cụ cầm ở tay phải — xem `DoVat`
  // 30/8 — Anh: *"10 channel trước phù hợp niche, ko phải theo kiểu funny, chỉ bắt chước nâng
  // cấp CÁCH LÀM thôi"*. Đúng, và đây là chỗ suýt gán nhầm: ký hiệu cảm xúc kiểu truyện tranh
  // (chùm gân đỏ "điên tiết", giọt mồ hôi "chột dạ") là ngôn ngữ HÀI. Dán chúng lên một kênh kể
  // số liệu ngân hàng thì kênh ấy mất hết vẻ đáng tin — mà đáng tin chính là TOÀN BỘ giá trị của
  // mười kênh dữ liệu. Bộ hài BẬT, bộ dữ liệu TẮT: cùng một con rối, hai cách diễn.
  kyHieu?: boolean;
  ghimNguc?: boolean;            // ép cử chỉ về tầm ngực — xem `_GHIM_NGUC` và chỗ dùng ở KichHai
  // 30/8 — KÝ HIỆU LÀ MỘT CHỚP, KHÔNG PHẢI PHỤ KIỆN ĐỘI ĐẦU.
  // Khung đo được: gần như MỌI nhân vật ở MỌI khung đều có chùm tia bật trên đầu. Vẽ đúng, nhưng
  // hiện suốt lượt thì nó thôi làm dấu nhấn và thành một thứ dính vào tóc.
  // Trong truyện tranh, ký hiệu bật ra đúng lúc cảm xúc ập tới rồi tan trong khoảng một giây —
  // nó đánh dấu KHOẢNH KHẮC, không mô tả trạng thái. `tuoiCanh` = số giây kể từ đầu lượt.
  tuoiCanh?: number;
  giat?: number;                 // 0..1 — cú giật mình (mắt mở to, đầu bật lùi) ở cú chốt
  nghieng?: number;              // độ ngả người về phía người đối thoại
  buoc?: number;                 // 0 = đứng yên; >0 = đang bước (biên độ sải chân)
  // 30/8 — CỬ CHỈ CŨ + TIẾN TRÌNH ĐỔI. Anh: *"cử chỉ tay cần mượt hơn"*.
  // Bản trước đổi cử chỉ NGAY tại ranh giới lượt thoại: một khung tay đang khoanh, khung sau tay
  // đã dang ra. Ở 30 khung/giây thì đó là một cú GIẬT, không phải một cử chỉ.
  // Người thật chuyển tư thế mất khoảng nửa giây, và cánh tay đi theo cung có gia tốc chứ không
  // nhảy. Nên truyền thêm cử chỉ TRƯỚC ĐÓ và tiến trình 0→1, rồi nội suy từng góc khớp.
  cuChiTruoc?: TenCuChi;
  doiCuChi?: number;             // 0 = vừa đổi, 1 = đã vào hẳn tư thế mới
  x?: number; y?: number; scale?: number; lat?: boolean;
};

// ══════════════════════════════════════════════════════════════════════════════════════════
// TỈ LỆ — đây là bảng quyết định "trông có ra hoạt hình không"
// ------------------------------------------------------------------------------------------
// Toàn thân cao 420 đơn vị, chân chạm y = 0, người mọc lên theo chiều âm.
// Đầu bán kính 58 nên đầu chiếm 116/420 ≈ 1/3,6 — đúng dải của hoạt hình truyền hình Mỹ.
// Chân CỐ Ý ngắn (150 trên tổng 420): chân ngắn + thân tròn là công thức "dễ thương", chân dài
// đọc ra là người lớn nghiêm nghị.
// ══════════════════════════════════════════════════════════════════════════════════════════
const Y_HONG = -168;
const Y_VAI = -262;
const R_DAU_GOC = 58;

export const DienVienHai: React.FC<PropsHai> = ({
  kieu, camXuc, cuChi, nhin, noi, t, nhan = 0, nghieng = 0, buoc = 0, giat = 0, dangNoi = true,
  cuChiTruoc, doiCuChi = 1, doVat = "", kyHieu = true, tuoiCanh = 0,
  x = 0, y = 0, scale = 1, lat = false, ghimNguc = false,
}) => {
  const E = CAM_XUC[camXuc] || CAM_XUC.trung_tinh;
  // ══ CỬ CHỈ GIỚI HẠN TRONG VÙNG NGỰC KHI LÀM NGƯỜI DẪN ═══════════════════════════════
  // 30/8 — Anh gửi khung có tay giơ cao che mất thẻ số ở đỉnh video. Trong bố cục người-dẫn-ở-góc,
  // mọi thứ phía trên đầu là CHỖ CỦA CHỮ (tiêu đề, thẻ số), nên tay tuyệt đối không được vào đó.
  // Chặn ngay tại bảng thay vì đi vá từng chỗ dùng: đổi mọi cử chỉ hướng-lên thành cử chỉ ngang
  // tầm ngực. Nhân vật vẫn "nói bằng tay", chỉ là nói trong vùng của mình.
  const _GHIM_NGUC: Record<string, TenCuChi> = {
    chi: "dem", gio_len: "dem", mo_tay: "mo_tay", nhun_vai: "mo_tay",
  };
  // 31/8 — ghim cũng bật theo BỐ CỤC, không chỉ theo chế độ kênh. Tính ra thì hai người cùng
  // khung với cử chỉ dang ngang (`chi` vươn 181 đơn vị) là BẤT KHẢ ở cỡ trung và cận: chỗ cần
  // để hai người không chồng nhau (≥288) lớn hơn chỗ có để không ai tràn khung (≤225). Không
  // có giá trị nào của khoảng cách thoả mãn cả hai — nên mọi lần chỉnh tay đều thất bại, và
  // tôi đã chỉnh bốn lần. Ghim tay về tầm ngực hạ bề ngang xuống 119 và mở lại khoảng khả thi
  // ở cả ba cỡ. Cỡ rộng vẫn để cử chỉ tự do vì ở đó vẫn vừa, và tay dang rộng là thứ làm nhân
  // vật sống động — chỉ ghim đúng chỗ nó gây tràn.
  const _ghim = ghimNguc || !kyHieu;
  const _cc = (_ghim ? (_GHIM_NGUC[cuChi as string] || cuChi) : cuChi) as string;
  const _ccT = (_ghim ? (_GHIM_NGUC[(cuChiTruoc || cuChi) as string] || cuChiTruoc || cuChi)
                      : (cuChiTruoc || cuChi)) as string;
  const _G1 = CU_CHI_HAI[_cc] || CU_CHI[_cc as TenCuChi] || CU_CHI.nghi;
  const _G0 = CU_CHI_HAI[_ccT] || CU_CHI[_ccT as TenCuChi] || _G1;
  // NỘI SUY GIỮA HAI TƯ THẾ, có gia tốc hai đầu (`muot`): rời tư thế cũ chậm, giữa nhanh, vào tư
  // thế mới chậm. Đó là cách một cánh tay thật chuyển động, và là thứ tách "cử chỉ" khỏi "nhảy
  // khung".
  // ══ TAY PHẢI CÓ ĐÀ, KHÔNG PHANH GẤP ═══════════════════════════════════════════════════
  // Anh nhắc lần thứ ba: *"tay cử động mượt hơn"*. Hai lần trước tôi chữa bằng cách NỘI SUY
  // (thay vì nhảy phựt) rồi KÉO DÀI thời gian nội suy. Cả hai đều đúng mà đều chưa tới, vì cái
  // còn thiếu không phải tốc độ — là **đà**.
  // Một cánh tay thật không dừng đúng tại đích: nó vượt qua một chút rồi lùi về, và tay càng đi
  // nhanh thì vượt càng nhiều. Trong hoạt hình đây là nguyên tắc "follow through", và nó là
  // ranh giới giữa "hình chạy từ tư thế A sang tư thế B" với "một người vừa vung tay".
  // `muot` (mượt hai đầu) cho ra chuyển động sạch nhưng CHẾT: tới đích là đứng phắt.
  // Hàm dưới đây vượt đích khoảng 5% quanh mốc 0,7 rồi lắng về đúng 1.
  const _daVuot = (t: number) => {
    const u = kep(t) - 1;
    return 1 + 2.2 * u * u * u + 1.2 * u * u;
  };
  const _q = _daVuot(kep(doiCuChi));
  // Và tay không bao giờ đứng tuyệt đối yên kể cả khi đã vào tư thế: một dao động rất nhỏ ở
  // khuỷu, lệch pha hai bên. Biên độ dưới ngưỡng chú ý — thấy thì không thấy, nhưng bỏ nó đi
  // thì hình đọc ra là ảnh chụp có mấy khớp xoay.
  const _tho = (pha: number) => Math.sin(t * 1.15 + pha) * 1.9 * (dangNoi ? 1 : 0.45);
  const G = {
    vaiT: trn(_G0.vaiT, _G1.vaiT, _q) + _tho(0),
    khuyuT: trn(_G0.khuyuT, _G1.khuyuT, _q) + _tho(1.7),
    vaiP: trn(_G0.vaiP, _G1.vaiP, _q) + _tho(3.1),
    khuyuP: trn(_G0.khuyuP, _G1.khuyuP, _q) + _tho(4.6),
  };
  // ══ NHÌN MỘT GIÂY PHẢI BIẾT NAM · NỮ · TRẺ CON ═══════════════════════════════════════
  // Anh: *"nhân vật nam và nữ hay con nít nhìn là phân biệt được rõ, ko phải na ná"*.
  // Trong ba phim ngắn anh gửi, việc này được giải bằng đúng hai thứ — và cả hai đọc được ở
  // cỡ nhỏ: **mái tóc** (nữ tóc dài phủ vai, nam tóc ngắn dựng) và **DÁNG NGƯỜI** (nữ vai hẹp
  // hông rộng, nam vai rộng thân thẳng).
  // Bộ của mình trước nay phân biệt bằng màu áo, kính và râu — cả ba đều là chi tiết NHỎ, và
  // ở khổ dọc trên điện thoại thì chúng biến mất trước tiên. Đó là lý do mười kênh "na ná".
  //
  // Trẻ con thì có một dấu hiệu mạnh hơn mọi thứ khác: **tỉ lệ đầu trên thân**. Người lớn
  // khoảng 1:7, trẻ con 1:4 — mắt người đọc tỉ lệ ấy trước cả khi kịp nhìn mặt. Bảng cũ có
  // `tiLeDau` nhưng chỉ dùng trong dải 0,92–1,1: đủ để tách hai người lớn, không đủ để nói
  // "đây là một đứa trẻ".
  // ── LỐI VẼ: ba bộ hệ số, áp lên nét · mắt · tỉ lệ đầu ─────────────────────────────────
  // Không viết lại hình — chỉ nhân hệ số vào những hằng đã có. Viết lại hình là viết lại 1200
  // dòng và mất hết những gì đã sửa; nhân hệ số thì ba lối dùng chung mọi bản vá về sau.
  const _lv = kieu.loiVe || "mat_to";
  const _hsNet = _lv === "net_manh" ? 0.58 : _lv === "goc_canh" ? 1.16 : 1;
  const _hsMat = _lv === "net_manh" ? 0.58 : _lv === "goc_canh" ? 0.86 : 1;
  // 0,46 cho ra con mắt bé tới mức mất biểu cảm — mà biểu cảm mới là thứ gánh trò đùa. 0,58
  // vẫn đọc ra là "mắt chấm kiểu webcomic" nhưng còn đủ chỗ cho tròng mắt đảo và mí nhướn.
  const _hsDau = _lv === "net_manh" ? 0.84 : _lv === "goc_canh" ? 0.94 : 1;
  const _detMat = _lv === "goc_canh" ? 0.58 : 1;      // mắt dẹt theo chiều dọc
  const NG = (7.2 * _hsNet) / scale;        // nét bao ngoài
  const NT = (3.4 * _hsNet) / scale;        // nét chi tiết bên trong

  const _gioi = kieu.gioi || "nam";
  const _nu = _gioi === "nu";
  const _tre = _gioi === "tre";
  const cao = (kieu.cao ?? 1) * (_tre ? 0.74 : 1);
  // Nữ: vai hẹp lại, thân thon. Trẻ con: người ngắn và tròn hơn.
  const ngang = (kieu.beNgang ?? 1) * (_nu ? 0.9 : 1) * (_tre ? 1.06 : 1);
  const _vaiHep = _nu ? 0.82 : 1;                 // bề ngang vai — dấu hiệu giới đọc từ xa
  const _hongRong = _nu ? 1.16 : 1;
  const matTo = kieu.matTo ?? 1;
  const camV = kieu.cam ?? 0.4;
  // Đầu to/nhỏ là trục đổi TUỔI mạnh nhất: đầu to đọc ra là trẻ con và hài, đầu nhỏ đọc ra là
  // người lớn nghiêm. Rẻ hơn nhiều so với vẽ lại toàn bộ nét mặt.
  const R_DAU = R_DAU_GOC * (kieu.tiLeDau ?? 1) * _hsDau * (_tre ? 1.34 : 1);
  const kMui = kieu.kieuMui || "moc";
  const kMat = kieu.kieuMat || "bau";
  const kMay = kieu.kieuMay || "day";

  // Nét bao dày là thứ đầu tiên mắt đọc ra "đây là phim hoạt hình". Giữ bề dày TRÊN MÀN HÌNH
  // không đổi bằng cách chia cho `scale` — không chia thì nhân vật càng xa nét càng mảnh và
  // hai người trong cùng khung trông như vẽ bằng hai cây bút khác nhau.

  // ══ CÚ GIẬT MÌNH ("take") — ngôn ngữ hài hình ảnh cổ điển nhất của hoạt hình Mỹ ═══════
  // Khi câu chốt rơi, người NGHE phải phản ứng: mắt bật to, đầu giật lùi rồi nảy về. Đây là
  // thứ báo cho khán giả "chỗ này buồn cười" mà không cần một tiếng cười lồng nào. Không có nó
  // thì câu chốt trôi qua đúng như mọi câu khác — đó chính là chỗ anh nói "chưa thấy funny".
  // Đường cong: bật rất nhanh (0,12 giây) rồi tắt dần có nảy, giống hệt cách hoạt hình vẽ một
  // phản ứng — nhanh vào, chậm ra, có dư chấn.
  const gt = kep(giat);
  const bat = gt > 0 ? Math.exp(-gt * 3.2) * Math.sin(gt * 13) : 0;
  // 30/8, sửa lần hai. Anh: *"a xem clip e làm a chưa thấy sự hài hước"*.
  // Bản trước cú giật mình chỉ làm mắt to thêm 50% và đầu lùi 14 điểm — quá nhẹ để mắt bắt được
  // ở cỡ khung điện thoại. Trong hoạt hình Mỹ, phản ứng ở cú chốt là thứ TO NHẤT của cả phim:
  // mắt lồi gấp đôi, HÀM RƠI, người bật ngửa, và đồ vật đang cầm thì tuột khỏi tay.
  // Đây là chỗ khán giả BIẾT là phải cười. Không có nó thì câu chốt trôi qua như mọi câu khác,
  // dù lời hay đến đâu: trò đùa bằng chữ phải ĐỌC mới hiểu, phản ứng bằng hình thì thấy ngay.
  // `noNo` là đường bao của cả cú giật: bật rất nhanh (0,11 giây) rồi tắt trong khoảng 1,5 giây.
  const noNo = gt > 0 ? Math.exp(-gt * 2.0) * Math.min(1, gt * 9) : 0;
  // ══════════════════════════════════════════════════════════════════════════════════════
  // AI ĐANG NÓI THÌ NGƯỜI ẤY DIỄN — NGƯỜI KIA GIỮ TƯ THẾ
  // --------------------------------------------------------------------------------------
  // 30/8 — Anh xem bản demo và chỉ ra: *"sao cử động cả 2 cùng cử động đồng thời 1 lúc"*.
  // Đúng, và đó là lỗi tôi tự viết vào: cả hai nhân vật cùng chạy đủ bộ nhịp sống (thở, đảo
  // người, dồn trọng tâm, vung tay, nén–giãn), chỉ khác pha một chút. Hai hình cùng nhấp nhô
  // theo một công thức đọc ra ngay là HAI CON RỐI CÙNG MỘT DÂY.
  //
  // Soi clip tham chiếu thì thấy rõ luật thật của hoạt hình: trong một cảnh, **chỉ MỘT người
  // diễn**. Người kia GIỮ TƯ THẾ — đứng yên, chỉ chớp mắt, và bật ra một phản ứng NGẮN ở đúng
  // một thời điểm rồi lại yên. Đó là cách mắt khán giả biết phải nhìn ai, và cũng là cách nghề
  // này tiết kiệm công vẽ suốt tám mươi năm nay ("limited animation").
  //
  // Nên mọi biên độ sống đều nhân với `dien`: người nói 1,0 · người nghe 0,22. Người nghe vẫn
  // "còn sống" (thở rất nhẹ, chớp mắt) nhưng không cạnh tranh sự chú ý với người đang nói.
  const dien = dangNoi ? 1 : 0.22;

  // ── NHỊP SỐNG ──────────────────────────────────────────────────────────────────────────
  const tho = Math.sin(t * 2.0) * dien;
  const dao = Math.sin(t * 0.6) * 1.6 * dien;
  // Dồn trọng tâm: người đứng lâu thì đổi chân trụ. Chu kỳ dài và lệch pha với nhịp thở nên
  // hai chuyển động không bao giờ trùng nhịp — trùng nhịp là dấu hiệu rõ nhất của hình máy.
  const trong = Math.sin(t * 0.41 + 1.2) * 3.2 * dien;

  // NÉN – GIÃN. Thân lùn xuống thì phình ngang ra, và ngược lại: giữ nguyên thể tích, nếu
  // không thì nhân vật đọc ra là bị kéo méo chứ không phải đang nhún.
  const nen = (Math.sin(t * 2.0) * 0.012 + nhan * 0.03) * dien;
  const sy = 1 + nen;
  const sx = 1 - nen * 0.85;

  // Chớp mắt không đều nhịp — nhịp đều đọc ra ngay là máy.
  const cky = 3.3 + Math.sin(t * 0.37) * 1.5;
  const pc = (t % cky) / cky;
  const chop = pc > 0.962 ? Math.sin(((pc - 0.962) / 0.038) * Math.PI) : 0;

  // Đầu gật theo lời nói: miệng mở to thì đầu chúi xuống một chút. Đây là thứ làm lời thoại
  // "có người nói" thay vì "có cái miệng động".
  const gat = noi.h * 3.4;
  const nghiengDau = E.nghieng + dao * 0.6 + treo(0, t, 0.1, 0.6) + bat * 9;

  // ── DÁNG ĐI ────────────────────────────────────────────────────────────────────────────
  // Bước chân là chuyển động tuần hoàn: hai chân LỆCH PHA NỬA CHU KỲ, và bàn chân nhấc lên
  // theo nửa trên của hình sin (nửa dưới là lúc chân chạm đất nên phải giữ y = 0, không thì
  // chân lún xuống dưới sàn — lỗi vật lý mắt bắt được ngay).
  // `nhun` là nhịp thân nhấp nhô hai lần mỗi chu kỳ bước: người đi thì trọng tâm lên xuống,
  // đứng yên mà tay chân vung là thứ đọc ra là hình máy.
  const bPha = t * 7.4;
  const sai = buoc * 30;
  const dapT = Math.sin(bPha), dapP = Math.sin(bPha + Math.PI);
  const nhacT = buoc > 0 ? Math.max(0, dapT) * 20 : 0;
  const nhacP = buoc > 0 ? Math.max(0, dapP) * 20 : 0;
  const nhun = buoc > 0 ? Math.abs(Math.cos(bPha)) * 5 : 0;

  // ── KHUNG XƯƠNG ────────────────────────────────────────────────────────────────────────
  const hong: [number, number] = [trong * 0.3, Y_HONG * cao + nhun];
  const vai: [number, number] = [trong * 0.6 + nghieng * 1.6, Y_VAI * cao + tho * 1.2 + nhun];
  const co: [number, number] = [vai[0] + dao * 0.4, vai[1] - 14 * cao];
  // Đầu nhấc CAO hơn vai đủ để thấy cổ. Bản trước chỉ hở 9 đơn vị nên đầu dính thẳng vào vai
  // và cả khối đọc ra là một hình duy nhất — đầu có quay cũng không ai thấy.
  //
  // 31/8 — KHOẢNG HỞ PHẢI THEO BÁN KÍNH ĐẦU, KHÔNG PHẢI MỘT HẰNG SỐ.
  // Anh nhìn banner rồi hỏi *"hình như cổ, đầu nó bị đè xuống, không có cổ phải không"*. Đúng:
  // khoảng cách này là 60 cố định, trong khi `R_DAU` đổi theo `tiLeDau` của từng nhân vật
  // (0,91 tới 1,12, và trẻ con còn nhân thêm 1,34). Đầu càng to thì mép dưới của nó càng trùm
  // xuống — với `tiLeDau` ≥ 1,0 thì cằm chạm ngay điểm cổ và cả đoạn cổ nằm khuất sau thân.
  // Nên hở phải tính TỪ bán kính đầu: mọi nhân vật đều lộ đúng một đoạn cổ như nhau, dù đầu to
  // hay nhỏ. Đây là họ lỗi "một hằng số phục vụ hai thứ đổi độc lập" — cùng họ với cỡ chữ ở
  // mục 8.1 và chỗ chừa bong bóng ở mục 9.3.
  // 31/8, sửa lần ba — anh: *"nãy e nâng cấp phần cổ đầu nhân vật lại lỡ nâng cả phần videos
  // làm cho cổ dài quá; a nói là phần profile và brandkit e làm lỗi chứ ko nói trong phần
  // videos"*. Đúng, và đây là lỗi của cách tôi sửa chứ không phải của con số:
  //
  //   · lỗi THẬT anh chỉ ra: ở ảnh tĩnh cỡ lớn, nhân vật ĐẦU TO bị đầu trùm che mất cổ;
  //   · tôi chữa bằng cách nâng hằng lên 1,08·R + 22 = 85 đơn vị — hơn bản gốc 41%;
  //   · và vì đây là tầng vẽ dùng chung, cả video cũng dài cổ theo, dù video vốn không sao.
  //
  // Cái sai là chỉnh cho MỘT nơi rồi để nó ăn sang mọi nơi mà không soi lại nơi kia. Con số
  // dưới đây bằng đúng bản gốc ở đầu cỡ trung bình (63 ≈ 60) và chỉ TỰ TĂNG khi đầu to thật
  // (R = 65 -> 69) — chữa được lỗi cũ mà không đẻ ra lỗi mới.
  const _hoCo = R_DAU * 0.78 + 18 * cao;
  const dau: [number, number] = [co[0] + dao * 0.9 - bat * 14, co[1] - _hoCo + gat - bat * 7];

  // Điểm gắn tay phải nằm NGOÀI mép thân, không thì cánh tay chạy chìm trong thân và bàn tay
  // đọc ra là dính vào hông. Và tay phải đủ DÀI: tay ngắn làm nhân vật đọc ra là mập lùn kể cả
  // khi thân đúng tỉ lệ — đây là chỗ bản đầu sai.
  const rongVai = 50 * ngang * _vaiHep;
  const vaiT: [number, number] = [vai[0] - rongVai - 4, vai[1] + 8];
  const vaiP: [number, number] = [vai[0] + rongVai + 4, vai[1] + 8];
  const dtay = 86 * cao, dcang = 80 * cao;

  // `mo` chỉ còn lo lượt ĐẦU TIÊN của video (từ tư thế nghỉ vào tư thế đầu); các lượt sau đã
  // được `doiCuChi` lo, và nhân hai lần làm cử chỉ ì ra ở đầu mỗi lượt.
  const mo = muot(kep(t / 0.45));
  // TAY ĐÁNH NHỊP THEO LỜI. Người nói thật không giữ nguyên một tư thế suốt câu — tay nhấn theo
  // trọng âm. `noi.h` (độ mở miệng) là thứ gần nhất với trọng âm mà mình có sẵn mốc: miệng mở to
  // là đang nhấn. Nhân 7 độ — đủ thấy mà chưa thành múa.
  // Khi ĐI, tay vung NGƯỢC PHA với chân cùng bên — đó là cách người thật giữ thăng bằng, và
  // là chi tiết làm dáng đi đọc ra là đi chứ không phải trượt ngang.
  const vungT = buoc > 0 ? Math.sin(t * 7.4 + Math.PI) * buoc * 26 : 0;
  const vungP = buoc > 0 ? Math.sin(t * 7.4) * buoc * 26 : 0;
  const nhipTay = noi.h * 7 * dien;
  const gocVT = trn(100, G.vaiT, mo) + Math.sin(t * 1.7) * 2.2 + vungT - nhipTay;
  const gocKT = trn(-8, G.khuyuT, mo);
  const gocVP = trn(80, G.vaiP, mo) + Math.sin(t * 1.7 + 1) * 2.2 + vungP + nhipTay;
  const gocKP = trn(8, G.khuyuP, mo);

  const khuyuT = P(vaiT[0], vaiT[1], dtay, gocVT);
  const tayT = P(khuyuT[0], khuyuT[1], dcang, gocVT + gocKT);
  const khuyuP = P(vaiP[0], vaiP[1], dtay, gocVP);
  const tayP = P(khuyuP[0], khuyuP[1], dcang, gocVP + gocKP);

  const rongHong = 30 * ngang * _hongRong;
  const goiT: [number, number] = [hong[0] - rongHong + dapT * sai * 0.5, hong[1] + 82 * cao - nhacT * 0.5];
  const goiP: [number, number] = [hong[0] + rongHong + dapP * sai * 0.5, hong[1] + 82 * cao - nhacP * 0.5];
  const chanT: [number, number] = [hong[0] - rongHong - 2 + dapT * sai, -4 - nhacT];
  const chanP: [number, number] = [hong[0] + rongHong + 2 + dapP * sai, -4 - nhacP];

  // ── MÀU ────────────────────────────────────────────────────────────────────────────────
  const V = kieu.net || "#20222B";
  const da = kieu.da, ao = kieu.ao, quan = kieu.quan;

  // 30/8 — TAY TRƯỚC PHẢI SÁNG HƠN THÂN.
  // Cánh tay bên phải vẽ SAU thân nên nó nằm đè lên ngực. Cùng một màu áo thì hai khối hoà vào
  // nhau và chỉ còn cái viền — khung đo được cho ra một dải màu cắt chéo người, đọc ra là tay
  // gãy chứ không phải tay khoanh trước ngực.
  // Hoạt hình tách lớp bằng SẮC ĐỘ, không bằng viền: thứ ở gần ống kính sáng hơn thứ ở xa, vì
  // ánh sáng tới nó trước. Chỉ cần chênh chừng một phần mười là mắt tách được ngay, mà vẫn đọc
  // ra là cùng một cái áo.
  const _sang = (h: string, k: number) => {
    const c = (h || "#888888").replace("#", "");
    if (c.length !== 6) return h;
    const v = [0, 2, 4].map((i) => Math.min(255, Math.round(parseInt(c.slice(i, i + 2), 16) * k)));
    return "#" + v.map((x) => x.toString(16).padStart(2, "0")).join("");
  };
  // Chênh 13% chưa đủ khi tay ôm sát thân: khung đo được cánh tay đọc ra như một vạt áo choàng
  // chứ không phải một cánh tay. Nới lên 22% / 82% thì hai khối tách hẳn mà vẫn cùng một cái áo.
  const aoTruoc = _sang(ao, 1.22);
  const aoSau = _sang(ao, 0.82);

  /** Chi thể: một nét bao dày rồi một nét màu mỏng hơn đè lên — ra hình con nhộng có viền. */
  const chi = (d: string, mau: string, day: number, key: string) => (
    <g key={key}>
      <path d={d} stroke={V} strokeWidth={day + NG} fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <path d={d} stroke={mau} strokeWidth={day} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </g>
  );

  /**
   * CHI HAI ĐOẠN — vai→khuỷu→bàn, gập THẬT tại khớp.
   *
   * Bản cũ vẽ cả cánh tay bằng MỘT đường `Q` với khuỷu làm điểm điều khiển. Nhưng Bezier bậc
   * hai KHÔNG ĐI QUA điểm điều khiển — nó chỉ bị kéo về phía đó. Nên dù bảng cử chỉ đặt góc
   * khuỷu bằng bao nhiêu, nét vẽ vẫn luôn ra một cung tròn trơn KHÔNG CÓ KHỚP. Đó chính là
   * "tay cong cong khèo khèo": không phải sai số, mà sai loại hình. Bốn lượt trước tôi chỉnh
   * số góc, đổi cách tính góc, rồi revert — nhưng cả bốn lượt đường vẽ vẫn là một `Q`, nên
   * đầu vào nào cũng ra cung tròn. Sửa cái mình chưa từng đụng mới hết.
   *
   * Kèm hai chuyện nữa cùng gốc, tự hết khi gập đúng:
   *  · ĐOẠN THON — bắp dày hơn cẳng. Ống dày đều đọc ra là cọng bún, không phải chi thể.
   *  · BÀN TAY hết trôi — nó vốn đã đặt tại `tay`, hướng `gocVai+gocKhuyu`; chỉ có nét vẽ là
   *    bỏ qua khuỷu, nên bàn tay khớp với một cẳng tay KHÔNG được vẽ ra. Vẽ đúng thì khớp lại.
   *
   * Viền cả hai đoạn vẽ TRƯỚC, màu vẽ SAU: nếu vẽ xong đoạn một rồi mới đoạn hai, viền đoạn
   * hai sẽ cắt một vạch đen ngang giữa khuỷu.
   */
  const chi2 = (
    a: [number, number], b: [number, number], c: [number, number],
    mau: string, dayTren: number, dayDuoi: number, key: string,
  ) => {
    const d1 = `M ${a[0]} ${a[1]} L ${b[0]} ${b[1]}`;
    const d2 = `M ${b[0]} ${b[1]} L ${c[0]} ${c[1]}`;
    const nut = { fill: "none", strokeLinecap: "round", strokeLinejoin: "round" } as const;
    return (
      <g key={key}>
        <path d={d1} stroke={V} strokeWidth={dayTren + NG} {...nut} />
        <path d={d2} stroke={V} strokeWidth={dayDuoi + NG} {...nut} />
        <path d={d1} stroke={mau} strokeWidth={dayTren} {...nut} />
        <path d={d2} stroke={mau} strokeWidth={dayDuoi} {...nut} />
      </g>
    );
  };

  /**
   * BÀN TAY GĂNG BỐN NGÓN — ngôn ngữ tạo hình chung của hoạt hình phương Tây từ thập niên 1930
   * (bốn ngón vẽ nhanh hơn năm, và đọc rõ hơn ở cỡ nhỏ). Không thuộc về hãng nào.
   * `goc` = hướng cẳng tay, để bàn tay nối liền chứ không trôi lơ lửng như bản cũ.
   */
  const ban = (p: [number, number], goc: number, key: string) => {
    // 30/8 — MỘT ĐƯỜNG BAO DUY NHẤT, ngón vẽ bằng NÉT KHẮC bên trong.
    // Bản đầu ghép bốn hình tròn có viền riêng chồng lên nhau; các viền cắt nhau nên bàn tay
    // đọc ra là một CHÙM NHO chứ không phải một bàn tay. Hoạt hình vẽ găng bằng đúng một hình
    // bao tròn trịa rồi khắc hai ba đường chia ngón vào TRONG — bao giờ cũng sạch ở mọi cỡ.
    // 30/8 — BÀN TAY NHỎ LẠI VÀ BỎ VẠCH NGÓN.
    // Ba vạch khắc ngón ở cỡ này đọc ra là VẾT CÀO chứ không phải ngón, và bàn tay to bằng
    // nửa cái đầu thì đọc ra là cái vợt. Hoạt hình vẽ tay nghỉ bằng một khối tròn có duy nhất
    // một khía ngón cái — ngón chỉ hiện ra khi tay LÀM GÌ ĐÓ, không phải khi buông xuôi.
    const r = 16;
    return (
      <g key={key} transform={`rotate(${goc - 90} ${p[0]} ${p[1]})`}>
        <path
          d={`M ${p[0] - r * 0.86} ${p[1] + r * 0.5}
              q -${r * 0.34} -${r * 0.9} ${r * 0.2} -${r * 1.24}
              q ${r * 0.5} -${r * 0.3} ${r * 0.86} ${r * 0.02}
              q ${r * 0.42} -${r * 0.24} ${r * 0.72} ${r * 0.2}
              q ${r * 0.4} ${r * 0.34} ${r * 0.16} ${r * 1.02}
              q -${r * 0.24} ${r * 0.62} -${r} ${r * 0.6}
              q -${r * 0.62} 0 -${r * 0.94} -${r * 0.6} Z`}
          fill={da} stroke={V} strokeWidth={NG * 0.86} strokeLinejoin="round"
        />
        <path d={`M ${p[0] - r * 0.74} ${p[1] + r * 0.1} q ${r * 0.3} -${r * 0.34} ${r * 0.56} -${r * 0.06}`}
              stroke={V} strokeWidth={NT} fill="none" strokeLinecap="round" opacity={0.85} />
      </g>
    );
  };

  /** Giày: khối bo tròn có gót — chân trần hình que là thứ làm bản cũ đọc ra là hình que. */
  const giay = (p: [number, number], huong: number, key: string) => (
    <g key={key}>
      <path d={`M ${p[0] - 15} ${p[1]} q -12 0 -12 -11 q 0 -12 13 -12 l 30 0 q 13 0 13 12 q 0 11 -13 11 z`}
            transform={`translate(${huong > 0 ? 6 : -20} 6)`}
            fill={_sang(quan, 0.55)} stroke={V} strokeWidth={NG * 0.7} strokeLinejoin="round" />
      {/* Đế giày — một dải sáng ở đáy. Không có nó thì giày dính xuống sàn thành một vệt. */}
      <path d={`M ${p[0] - 25} ${p[1] + 15} l 56 0`}
            transform={`translate(${huong > 0 ? 6 : -20} 0)`}
            stroke="#F2EDE4" strokeWidth={NG * 0.9} strokeLinecap="round" opacity={0.85} />
    </g>
  );

  // ── MẶT ────────────────────────────────────────────────────────────────────────────────
  // 30/8 — Anh: *"khi đối thoại nhân vật quay mặt vào nhau chứ ko phải quay đơ ra trước màn
  // hình"*. Đo ra thì hướng nhìn ĐÃ được truyền đúng ý ở `KichHai` — nhưng nhân vật bên phải
  // được vẽ bằng phép LẬT NGANG (`scale(-x)`), và phép lật đảo luôn dấu của con ngươi.
  // Nên `nhin[0] = -0.3` (ý là "nhìn sang trái, về phía bạn diễn") sau khi lật hiện ra thành
  // nhìn sang PHẢI — tức nhìn ra khỏi khung, quay lưng lại với người đang nói chuyện với mình.
  // Hai người cùng nhìn ra hai phía ngược nhau thì không đọc ra là đối thoại; nó đọc ra là hai
  // người đứng cạnh nhau nói với ai đó ngoài màn hình.
  // Bù dấu ngay tại đây — nơi biết mình có bị lật hay không — thay vì bắt mọi chỗ gọi phải nhớ.
  const _huong = lat ? -1 : 1;
  const mx = kep(nhin[0], -1, 1) * 7 * _huong;
  const my = kep(nhin[1], -1, 1) * 5;
  // 30/8 — MẮT NHỎ LẠI. Bản trước mắt + gọng kính chiếm 83% bề ngang đầu; mắt to là đúng
  // hướng nhưng quá tay thì đọc ra là mắt lồi ra khỏi mặt chứ không phải dễ thương. Dải đẹp
  // của hoạt hình truyền hình là hai mắt chiếm chừng 60–65% bề ngang đầu.
  // Mắt bầu dục ĐỨNG nên bề ngang hẹp hơn bản mắt-tròn cũ, và hai mắt gần nhau hơn để hợp với
  // sọ quả lê (chỗ rộng nhất nằm ngang tầm mắt, không ở giữa mặt).
  const rMat = 11.5 * matTo * _hsMat * (1 + noNo * 0.82);
  const rTrong = 6.4 * matTo;
  const mm = 1 - chop;
  const cachMat = 17 * matTo;
  const yMat = -8;
  const yMay = yMat - 20 - E.mayCao - noNo * 10;

  // Miệng: bề ngang và bề cao lấy thẳng từ khẩu hình, cộng độ cong khoé môi theo cảm xúc.
  const mW = trn(26, 46, noi.w) * (1 + camV * 0.05);
  // HÀM RƠI — miệng mở to bất kể khẩu hình đang là gì. Cưỡng bức như vậy là đúng: ở khoảnh khắc
  // sững người, cái miệng không còn phát âm nữa, nó chỉ há ra.
  const mH = Math.max(trn(2.5, 34, noi.h), noNo * 40);
  const khoe = E.khoe * 9;
  const yMieng = 26;

  return (
    <g transform={`translate(${x} ${y}) rotate(${(lat ? -1 : 1) * (nghieng * 0.4 - noNo * 7)} 0 0) scale(${(lat ? -scale : scale) * sx} ${scale * sy})`}>
      {/* BÓNG TIẾP ĐẤT — thiếu nó thì nhân vật lơ lửng dù đứng đúng chỗ. Bóng co giãn ngược
          chiều nén–giãn: người nhún xuống thì bóng loe ra. */}
      <ellipse cx={0} cy={2} rx={62 * ngang * (1 + nen * 2)} ry={11} fill="#00000026" />

      {/* CHÂN — vẽ trước thân để thân che chỗ nối ở hông */}
      {chi2([hong[0] - rongHong, hong[1]], goiT, chanT, quan, 28 * ngang, 23 * ngang, "cT")}
      {chi2([hong[0] + rongHong, hong[1]], goiP, chanP, quan, 28 * ngang, 23 * ngang, "cP")}
      {/* Giày tô màu RIÊNG, không dùng màu nét. Khung đo được: quần sẫm + giày màu nét = một
          khối tối liền từ hông xuống sàn, không đọc ra là có bàn chân. */}
      {giay(chanT, -1, "gT")}
      {giay(chanP, 1, "gP")}

      {/* TAY SAU (bên trái) — vẽ trước thân, nên nó nằm sau lưng: ra chiều sâu mà không cần đổ bóng */}
      {chi2(vaiT, khuyuT, tayT, aoSau, 24 * ngang, 19 * ngang, "tT")}
      {ban(tayT, gocVT + gocKT, "bT")}

      {/* THÂN — hình hạt đậu, KHÔNG phải hình chữ nhật. Vai tròn và eo hơi thóp là thứ làm
          nhân vật đọc ra là dễ thương thay vì cứng đờ. */}
      <path
        d={`M ${vai[0] - rongVai - 6} ${vai[1] + 6}
            C ${vai[0] - rongVai - 16} ${vai[1] + 40}, ${hong[0] - rongHong - 20} ${hong[1] - 34}, ${hong[0] - rongHong - 12} ${hong[1] + 8}
            Q ${hong[0]} ${hong[1] + 26} ${hong[0] + rongHong + 12} ${hong[1] + 8}
            C ${hong[0] + rongHong + 20} ${hong[1] - 34}, ${vai[0] + rongVai + 16} ${vai[1] + 40}, ${vai[0] + rongVai + 6} ${vai[1] + 6}
            Q ${vai[0]} ${vai[1] - 10} ${vai[0] - rongVai - 6} ${vai[1] + 6} Z`}
        fill={ao} stroke={V} strokeWidth={NG} strokeLinejoin="round"
      />
      {/* Cổ áo chữ V + áo trong: một mảng sáng giữa ngực để thân không phẳng lì */}
      <path d={`M ${vai[0] - 20} ${vai[1] + 2} L ${vai[0]} ${vai[1] + 36} L ${vai[0] + 20} ${vai[1] + 2} Z`}
            fill={kieu.aoTrong} stroke={V} strokeWidth={NT} strokeLinejoin="round" />
      {kieu.caVat ? (
        <path d={`M ${vai[0] - 8} ${vai[1] + 26} L ${vai[0] + 8} ${vai[1] + 26} L ${vai[0] + 5} ${vai[1] + 78} L ${vai[0]} ${vai[1] + 86} L ${vai[0] - 5} ${vai[1] + 78} Z`}
              fill={kieu.caVat} stroke={V} strokeWidth={NT} strokeLinejoin="round" />
      ) : null}
      {/* ══ TRANG PHỤC NGHỀ ═══════════════════════════════════════════════════════════
          30/8 — Anh: *"nhân vật chuẩn usa, chuẩn phong cách của niche đó — kênh tài chính thì
          là chuyên gia tài chính, kênh luật thì là chuyên gia luật"*.
          Trước bản này con rối chỉ vẽ được cà vạt và thẻ đeo; mọi nghề khác mặc đúng một cái áo
          cổ chữ V trơn. Và sau khi chuyển sang bố cục người-dẫn-ở-góc (cắt ngang hông), phần
          thấy được chỉ còn ĐẦU · VAI · NGỰC — nghĩa là trang phục phần trên là thứ DUY NHẤT nói
          lên nghề. Áo trơn ở đó thì mười kênh thành mười người vô danh mặc mười màu áo.
          Năm bộ dưới đây phủ hết mười kênh dữ liệu, và mỗi bộ đọc ra nghề trong một phần mười
          giây — trước cả dòng chữ đầu tiên. */}
      {kieu.phuKien === "ve_vest" ? (
        <g>
          {/* ve áo vest — hai mảng chếch từ vai xuống ngực, màu sẫm hơn áo */}
          <path d={`M ${vai[0] - 22} ${vai[1] + 2} L ${vai[0] - 2} ${vai[1] + 40}
                    L ${vai[0] - 4} ${vai[1] + 96} L ${vai[0] - 42} ${vai[1] + 40} Z`}
                fill={_sang(ao, 0.72)} stroke={V} strokeWidth={NT * 1.2} strokeLinejoin="round" />
          <path d={`M ${vai[0] + 22} ${vai[1] + 2} L ${vai[0] + 2} ${vai[1] + 40}
                    L ${vai[0] + 4} ${vai[1] + 96} L ${vai[0] + 42} ${vai[1] + 40} Z`}
                fill={_sang(ao, 0.72)} stroke={V} strokeWidth={NT * 1.2} strokeLinejoin="round" />
        </g>
      ) : null}
      {kieu.phuKien === "ao_blouse" ? (
        <g>
          {/* áo blouse — vạt trắng hai bên, có túi ngực. Nghề y và nghề nghiên cứu. */}
          <path d={`M ${vai[0] - 26} ${vai[1] + 4} L ${vai[0] - 6} ${vai[1] + 42}
                    L ${vai[0] - 8} ${vai[1] + 108} L ${vai[0] - 48} ${vai[1] + 100} Z`}
                fill="#F7F9FC" stroke={V} strokeWidth={NT * 1.2} strokeLinejoin="round" />
          <path d={`M ${vai[0] + 26} ${vai[1] + 4} L ${vai[0] + 6} ${vai[1] + 42}
                    L ${vai[0] + 8} ${vai[1] + 108} L ${vai[0] + 48} ${vai[1] + 100} Z`}
                fill="#F7F9FC" stroke={V} strokeWidth={NT * 1.2} strokeLinejoin="round" />
          <rect x={vai[0] + 16} y={vai[1] + 52} width={22} height={18} rx={2}
                fill="none" stroke={V} strokeWidth={NT} opacity={0.6} />
        </g>
      ) : null}
      {kieu.phuKien === "ong_nghe" ? (
        <g fill="none" stroke="#3B4250" strokeWidth={NT * 2.2} strokeLinecap="round">
          {/* ống nghe quàng cổ */}
          <path d={`M ${vai[0] - 20} ${vai[1] + 2} Q ${vai[0] - 30} ${vai[1] + 62} ${vai[0] - 12} ${vai[1] + 78}`} />
          <path d={`M ${vai[0] + 20} ${vai[1] + 2} Q ${vai[0] + 30} ${vai[1] + 58} ${vai[0] + 16} ${vai[1] + 70}`} />
          <circle cx={vai[0] - 12} cy={vai[1] + 84} r={9} fill="#9AA3AD" stroke={V} strokeWidth={NT} />
        </g>
      ) : null}
      {kieu.phuKien === "no_buom" ? (
        <g>
          {/* nơ bướm — luật sư trẻ, kiến trúc sư, người dẫn chương trình */}
          <path d={`M ${vai[0] - 22} ${vai[1] + 20} l 16 -9 l 0 22 Z`}
                fill={kieu.caVat || "#8A2F3C"} stroke={V} strokeWidth={NT} strokeLinejoin="round" />
          <path d={`M ${vai[0] + 22} ${vai[1] + 20} l -16 -9 l 0 22 Z`}
                fill={kieu.caVat || "#8A2F3C"} stroke={V} strokeWidth={NT} strokeLinejoin="round" />
          <rect x={vai[0] - 5} y={vai[1] + 15} width={10} height={12} rx={3}
                fill={_sang(kieu.caVat || "#8A2F3C", 0.75)} stroke={V} strokeWidth={NT} />
        </g>
      ) : null}
      {kieu.phuKien === "ao_choang" ? (
        <g>
          {/* áo choàng toà — vạt đen rộng, cổ trắng. Thẩm phán, công tố viên. */}
          <path d={`M ${vai[0] - 30} ${vai[1] + 2} L ${vai[0] - 8} ${vai[1] + 44}
                    L ${vai[0] - 10} ${vai[1] + 116} L ${vai[0] - 54} ${vai[1] + 108} Z`}
                fill="#1E2028" stroke={V} strokeWidth={NT * 1.2} strokeLinejoin="round" />
          <path d={`M ${vai[0] + 30} ${vai[1] + 2} L ${vai[0] + 8} ${vai[1] + 44}
                    L ${vai[0] + 10} ${vai[1] + 116} L ${vai[0] + 54} ${vai[1] + 108} Z`}
                fill="#1E2028" stroke={V} strokeWidth={NT * 1.2} strokeLinejoin="round" />
          <path d={`M ${vai[0] - 11} ${vai[1] + 22} l 22 0 l -3 34 l -16 0 Z`}
                fill="#FFFFFF" stroke={V} strokeWidth={NT} strokeLinejoin="round" />
        </g>
      ) : null}
      {kieu.phuKien === "khan_quang" ? (
        <path d={`M ${-26} ${Y_VAI + 16} q 26 20 52 0 q -6 30 -26 30 q -20 0 -26 -30 Z`}
              fill={kieu.aoTrong || "#D8D2C4"} stroke={V} strokeWidth={NG * 0.7}
              strokeLinejoin="round" />
      ) : null}
      {/* BẢNG KẸP — dấu hiệu "người đi đo đếm": nhà báo điều tra, người soi hợp đồng, người
          rà số liệu. Cây kiểm `kiem_gan` bắt được ngay lần chạy đầu rằng tôi đã gán phụ kiện
          này cho hai kênh dữ liệu mà chỉ vẽ nó ở engine QUE, quên vẽ ở engine KHỐI — đúng loại
          lỗi mà cổng ấy sinh ra để chặn, và nó chặn ngay hôm được viết. */}
      {kieu.phuKien === "bang_kep" ? (
        <g transform={`translate(${vai[0] - 46} ${vai[1] + 74}) rotate(-11)`}>
          <rect x={-17} y={-23} width={34} height={46} rx={3}
                fill="#E8E2D4" stroke={V} strokeWidth={NT} />
          <rect x={-8} y={-28} width={16} height={9} rx={3} fill={V} />
          <path d="M -9 -8 H 9 M -9 1 H 9 M -9 10 H 3" stroke={V} strokeWidth={NT * 0.7}
                fill="none" strokeLinecap="round" />
        </g>
      ) : null}
      {kieu.phuKien === "the_deo" ? (
        <g>
          <path d={`M ${vai[0] - 16} ${vai[1] + 6} Q ${vai[0]} ${vai[1] + 52} ${vai[0] + 16} ${vai[1] + 6}`}
                stroke={V} strokeWidth={NT * 1.3} fill="none" />
          <rect x={vai[0] - 11} y={vai[1] + 46} width={22} height={28} rx={4}
                fill="#F4F7FC" stroke={V} strokeWidth={NT} />
        </g>
      ) : null}

      {/* TAY TRƯỚC (bên phải) — vẽ sau thân nên nằm trước ngực */}
      {chi2(vaiP, khuyuP, tayP, aoTruoc, 24 * ngang, 19 * ngang, "tP")}
      {ban(tayP, gocVP + gocKP, "bP")}
      {/* ĐỒ VẬT TUỘT KHỎI TAY ở cú chốt — trò đùa hình thể cổ điển nhất, và nó nói đúng thứ mà
          lời thoại vừa nói: "tôi không tin nổi". Rơi theo gia tốc (bình phương thời gian) và xoay
          chậm, đúng như một vật rơi thật. */}
      {doVat ? (
        <g transform={`translate(0 ${noNo > 0.06 ? Math.pow(gt, 2) * 190 : 0}) rotate(${noNo > 0.06 ? gt * 130 : 0} ${tayP[0]} ${tayP[1]})`}
           opacity={gt > 0.85 ? 0 : 1}>
          <DoVat ten={doVat} p={tayP} goc={gocVP + gocKP} V={V} NT={NT} />
        </g>
      ) : null}

      {/* CỔ — bản đầu vẽ quá ngắn nên đầu dính thẳng vào vai, đọc ra là một khối. Cổ phải
          THẤY ĐƯỢC thì đầu mới quay được một cách có nghĩa. */}
      {chi(`M ${co[0]} ${co[1] + 24} L ${dau[0]} ${dau[1] + R_DAU * 0.58}`, da, 40, "co")}

      {/* ── ĐẦU ───────────────────────────────────────────────────────────────────────── */}
      <g transform={`rotate(${nghiengDau} ${dau[0]} ${dau[1] + R_DAU})`}>
        {/* ══════════════════════════════════════════════════════════════════════════════
            KHUÔN MẶT KIỂU HOẠT HÌNH MỸ — dựng lại hoàn toàn 30/8/2026
            ------------------------------------------------------------------------------
            Anh: *"nhân vật vẫn xấu, nhìn vào chưa có nét usa và nhận ra được luôn"*, kèm một
            clip tham chiếu. Soi clip ấy khung-đối-khung thì khoảng cách nằm ở CHÍN chi tiết
            hình hoạ, không phải ở "vẽ đẹp hơn":

              1. SỌ hình QUẢ LÊ NGƯỢC — trán rộng nhất ở khoảng một phần ba trên, hai má phình,
                 cằm THU LẠI. Bản cũ là hình tròn, và hình tròn thì đọc ra là nhân vật thiếu nhi
                 châu Á/châu Âu chứ không ra hoạt hình truyền hình Mỹ.
              2. MẮT là hai BẦU DỤC ĐỨNG (cao hơn rộng), tròng trắng lớn, con ngươi chỉ là một
                 CHẤM nhỏ. Bản cũ vẽ hai vòng tròn với con ngươi to — đó là mắt búp bê.
              3. LÔNG MÀY là KHỐI ĐẶC dày, nằm SÁT ngay trên mắt. Bản cũ là nét cong mảnh đặt
                 cao, đọc ra là nét trang trí chứ không phải một bộ phận của mặt.
              4. MŨI là một KHỐI NHÔ có sống mũi và cánh mũi — đây là nét chính của khuôn mặt
                 trong dòng phim này, và bản cũ chỉ có một nét cong bằng đầu ngón tay.
              5. NẾP CƯỜI (hai đường từ cánh mũi vòng xuống quá khoé miệng). Chi tiết rẻ nhất mà
                 đổi hẳn quốc tịch của khuôn mặt.
              6. NẾP NHĂN TRÁN — hai ba đường ngang rất mảnh. Không có nó thì trán phẳng như nhựa.
              7. MIỆNG cười RỘNG, khoé kéo lên tận má, có dải RĂNG và LƯỠI.
              8. CẰM có ngấn (một nét cong dưới môi dưới).
              9. TAI có VÀNH TRONG, không phải một hình bầu dục trơn.

            Chín thứ này đều là NGUYÊN TẮC TẠO HÌNH của cả một dòng phim, không phải thiết kế
            riêng của phim nào — nên mượn được, và mượn xong vẫn là nhân vật của mình. Thứ
            KHÔNG mượn: gương mặt cụ thể, tỉ lệ đặc trưng, màu da đặc trưng của một nhân vật có
            bản quyền.
            ══════════════════════════════════════════════════════════════════════════════ */}

        {/* TAI — có vành trong. Vẽ TRƯỚC sọ để sọ đè lên chỗ nối, ra tai mọc từ đầu chứ không
            phải dán vào đầu. */}
        {[-1, 1].map((sg) => (
          <g key={sg}>
            <path d={`M ${dau[0] + sg * R_DAU * 0.9} ${dau[1] - 4}
                      q ${sg * 17} -2 ${sg * 15} 14 q ${-sg * 2} 16 ${-sg * 15} 14 Z`}
                  fill={da} stroke={V} strokeWidth={NT * 1.4} strokeLinejoin="round" />
            <path d={`M ${dau[0] + sg * R_DAU * 0.98} ${dau[1] + 1}
                      q ${sg * 8} 0 ${sg * 7} 8`}
                  stroke={V} strokeWidth={NT} fill="none" strokeLinecap="round" opacity={0.75} />
          </g>
        ))}

        {/* SỌ QUẢ LÊ NGƯỢC. `camV` điều khiển bề rộng hàm: 0 = cằm nhỏ (trẻ con), 1 = hàm bạnh
            (đàn ông đứng tuổi). Điểm rộng nhất nằm ở NGANG TẦM MẮT, không ở giữa mặt. */}
        <path
          d={`M ${dau[0] - R_DAU * 0.86} ${dau[1] - R_DAU * 0.22}
              C ${dau[0] - R_DAU * 0.98} ${dau[1] - R_DAU * 0.95}, ${dau[0] - R_DAU * 0.42} ${dau[1] - R_DAU * 1.2}, ${dau[0]} ${dau[1] - R_DAU * 1.2}
              C ${dau[0] + R_DAU * 0.42} ${dau[1] - R_DAU * 1.2}, ${dau[0] + R_DAU * 0.98} ${dau[1] - R_DAU * 0.95}, ${dau[0] + R_DAU * 0.86} ${dau[1] - R_DAU * 0.22}
              C ${dau[0] + R_DAU * 0.94} ${dau[1] + R_DAU * 0.42}, ${dau[0] + R_DAU * (0.6 + camV * 0.24)} ${dau[1] + R_DAU * 0.98}, ${dau[0] + R_DAU * 0.08} ${dau[1] + R_DAU * 1.0}
              C ${dau[0] - R_DAU * (0.56 + camV * 0.24)} ${dau[1] + R_DAU * 1.0}, ${dau[0] - R_DAU * 0.94} ${dau[1] + R_DAU * 0.42}, ${dau[0] - R_DAU * 0.86} ${dau[1] - R_DAU * 0.22} Z`}
          fill={da} stroke={V} strokeWidth={NG} strokeLinejoin="round"
        />

        {/* NẾP NHĂN TRÁN — mảnh, mờ, hai đường. Chỉ vẽ cho người có hàm bạnh (camV cao = đứng
            tuổi); trẻ con trán phẳng. */}
        {camV > 0.45 ? (
          <g stroke={V} strokeWidth={NT * 0.75} fill="none" opacity={0.42} strokeLinecap="round">
            <path d={`M ${dau[0] - 22} ${dau[1] - R_DAU * 0.66} q 22 -6 44 0`} />
            <path d={`M ${dau[0] - 18} ${dau[1] - R_DAU * 0.52} q 18 -5 36 0`} />
          </g>
        ) : null}

        {/* MẮT — BẦU DỤC ĐỨNG, tròng trắng lớn, con ngươi là một CHẤM. Mí trên là một nét dày
            đè lên mép trên tròng trắng: đó là thứ làm mắt có "mí" thay vì là hai quả trứng. */}
        {[-1, 1].map((sg) => (
          <g key={sg}>
            {/* BỐN KIỂU MẮT — bầu dục đứng (mặc định) · tròn (ngơ ngác) · hẹp (ranh mãnh) ·
                xếch (đanh đá). Tỉ lệ cao/rộng là thứ đổi tính cách nhanh nhất. */}
            <ellipse cx={dau[0] + sg * cachMat} cy={dau[1] + yMat}
                     rx={rMat * (kMat === "hep" ? 1.16 : 1)}
                     ry={rMat * _detMat * (kMat === "tron" ? 1.0 : kMat === "hep" ? 0.62 : 1.24)
                         * (0.2 + 0.8 * mm)}
                     fill="#FFFFFF" stroke={V} strokeWidth={NT * 1.5}
                     transform={kMat === "xech" ? `rotate(${sg * 9} ${dau[0] + sg * cachMat} ${dau[1] + yMat})` : undefined} />
            {mm > 0.22 ? (
              <>
                <circle cx={dau[0] + sg * cachMat + mx} cy={dau[1] + yMat + my + rMat * 0.16} r={rTrong * 0.62}
                        fill="#1B1D25" />
                <circle cx={dau[0] + sg * cachMat + mx - rTrong * 0.24} cy={dau[1] + yMat + my - rTrong * 0.1}
                        r={rTrong * 0.22} fill="#FFFFFF" />
              </>
            ) : null}
            {/* MÍ TRÊN — một CUNG ôm đúng MÉP TRÊN tròng trắng, không phải nét cong nằm bên
                trong. Bản trước vẽ nét ấy chạy ngang giữa mắt nên đọc ra là lông mi rối và mắt
                thành mắt hí. Mí thật chỉ làm dày mép trên và hơi trùm xuống hai bên. */}
            <path d={`M ${dau[0] + sg * cachMat - rMat} ${dau[1] + yMat}
                      A ${rMat} ${rMat * 1.24} 0 0 1 ${dau[0] + sg * cachMat + rMat} ${dau[1] + yMat}`}
                  stroke={V} strokeWidth={NT * 2.2} fill="none" strokeLinecap="round"
                  transform={`rotate(${sg * -6} ${dau[0] + sg * cachMat} ${dau[1] + yMat})`} />
          </g>
        ))}

        {/* 31/8 — LÔNG MI: dấu hiệu giới đọc được ở cỡ nhỏ nhất.
            Anh đã dặn *"nhân vật nam và nữ hay con nít nhìn là phân biệt được rõ"*, và engine
            đã có vai hẹp 0,82 + hông rộng 1,16 cho nữ. Nhưng soi mười khung thật thì vẫn không
            đọc ra: ở cỡ một phần năm màn hình, bề ngang vai chênh 18% là thứ mắt không bắt kịp.
            Hoạt hình Mỹ giải việc này bằng đúng hai chi tiết ở KHUÔN MẶT — lông mi và tóc buông
            — vì mắt người luôn nhìn mặt trước, và mặt thì luôn to hơn vai trong mọi cỡ cảnh. */}
        {_nu ? [-1, 1].map((sg) => (
          <g key={`mi${sg}`}>
            {[0, 1, 2].map((i) => {
              const g0 = -0.42 + i * 0.30;
              const x0 = dau[0] + sg * cachMat + sg * Math.cos(g0) * rMat * 0.98;
              const y0 = dau[1] + yMat - Math.sin(g0 + 0.5) * rMat * 0.72;
              return <line key={i} x1={x0} y1={y0}
                           x2={x0 + sg * rMat * 0.34} y2={y0 - rMat * 0.30}
                           stroke={V} strokeWidth={NT * 1.5} strokeLinecap="round" />;
            })}
          </g>
        )) : null}

        {/* LÔNG MÀY — KHỐI ĐẶC, dày, sát ngay trên mắt. Đây là bộ phận biểu cảm mạnh nhất của
            khuôn mặt: khán giả đọc "đang bực / đang ngơ" từ lông mày trước cả từ miệng. */}
        {[-1, 1].map((sg) => {
          const bx = dau[0] + sg * cachMat;
          const by = dau[1] + yMay;
          const ng = E.may * sg * -1;
          return (
            <path key={sg}
              d={kMay === "manh"
                 // mảnh — nét cong một đường, nữ tính hoặc trẻ
                 ? `M ${bx - rMat * 1.1} ${by + ng * 0.42 + 6}
                    Q ${bx} ${by - 5 - ng * 0.24} ${bx + rMat * 1.1} ${by - ng * 0.42 + 6}
                    Q ${bx} ${by - 1 - ng * 0.24} ${bx - rMat * 1.1} ${by + ng * 0.42 + 6} Z`
                 : kMay === "xech"
                 // xếch — đầu trong thấp, đuôi ngoài cao: mặt đanh, hay phán xét
                 ? `M ${bx - sg * rMat * 1.14} ${by + ng * 0.42 + 9}
                    Q ${bx} ${by - 9 - ng * 0.24} ${bx + sg * rMat * 1.14} ${by - ng * 0.42 - 2}
                    Q ${bx} ${by - ng * 0.24} ${bx - sg * rMat * 1.14} ${by + ng * 0.42 + 9} Z`
                 : kMay === "ru"
                 // rủ — hai đầu chúi xuống: mặt lo lắng, cam chịu
                 ? `M ${bx - rMat * 1.14} ${by + ng * 0.42 - 1}
                    Q ${bx} ${by + 9 - ng * 0.24} ${bx + rMat * 1.14} ${by - ng * 0.42 - 1}
                    Q ${bx} ${by + 3 - ng * 0.24} ${bx - rMat * 1.14} ${by + ng * 0.42 - 1} Z`
                 // dày — khối đặc, mặc định
                 : `M ${bx - rMat * 1.16} ${by + ng * 0.42 + 5}
                    Q ${bx} ${by - 8 - ng * 0.24} ${bx + rMat * 1.16} ${by - ng * 0.42 + 5}
                    Q ${bx} ${by - ng * 0.24} ${bx - rMat * 1.16} ${by + ng * 0.42 + 5} Z`}
              fill={kieu.toc} stroke={V} strokeWidth={NT * 0.9} strokeLinejoin="round" />
          );
        })}

        {/* MŨI — KHỐI NHÔ có sống và cánh. Nét chính của khuôn mặt trong dòng phim này. Lệch nhẹ
            theo hướng nhìn nên khi nhân vật quay sang, mũi quay theo — thứ làm mặt có chiều. */}
        {/* MŨI — MỘT NÉT MÓC, không phải hình khép kín. Bản trước vẽ mũi thành khối có viền, và
            ở cỡ này nó đọc ra là một dấu hỏi giữa mặt. Trong dòng phim tham chiếu, mũi chỉ là một
            nét: xuống từ giữa hai mắt, móc sang một bên, hết. Ít nét thì mặt sạch mà vẫn có mũi. */}
        {(() => {
          const nx = dau[0] + mx * 0.45, ny = dau[1] + 1;
          const net = { stroke: V, strokeWidth: NT * 1.6, fill: "none" as const,
                        strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
          // NĂM KIỂU MŨI. Đây là nét tách hai nhân vật mạnh nhất trên khuôn mặt: đổi mũi là đổi
          // người, dù mọi thứ khác giữ nguyên.
          if (kMui === "cu")                        // củ hành — ông chú, thợ thuyền
            return <ellipse cx={nx + 4} cy={ny + 11} rx={11} ry={9} fill={_sang(da, 0.94)}
                            stroke={V} strokeWidth={NT * 1.5} />;
          if (kMui === "nhon")                      // nhọn — người sắc sảo, hay soi
            return <path d={`M ${nx} ${ny - 2} l 13 17 l -12 2 Z`} fill={_sang(da, 0.96)}
                         stroke={V} strokeWidth={NT * 1.4} strokeLinejoin="round" />;
          if (kMui === "hat")                       // hạt đậu — trẻ con, dễ thương
            return <ellipse cx={nx + 2} cy={ny + 9} rx={6} ry={5} fill={_sang(da, 0.92)}
                            stroke={V} strokeWidth={NT * 1.3} />;
          if (kMui === "quap")                      // quặp xuống — người khó tính
            return <path d={`M ${nx} ${ny - 1} q 2 12 9 15 q 6 2 5 -5`} {...net} />;
          return <path d={`M ${nx} ${ny} q -2 11 4 15 q 7 4 11 -3`} {...net} />;   // móc — mặc định
        })()}

        {/* MÁ HỒNG — hai chấm mờ, đặt THẤP và RỘNG hơn bản cũ để hợp với sọ quả lê. */}
        <ellipse cx={dau[0] - cachMat - 10} cy={dau[1] + 22} rx={13} ry={7} fill="#E8836F" opacity={0.28} />
        <ellipse cx={dau[0] + cachMat + 10} cy={dau[1] + 22} rx={13} ry={7} fill="#E8836F" opacity={0.28} />

        {/* MIỆNG — mở theo khẩu hình, khoé kéo CAO lên má. Có dải răng và lưỡi khi mở to: một
            cái lỗ đen thui đọc ra là thủng mặt chứ không phải đang nói. */}
        <g>
          <path
            d={`M ${dau[0] - mW / 2} ${dau[1] + yMieng - khoe * 0.8}
                Q ${dau[0]} ${dau[1] + yMieng - khoe * 1.1} ${dau[0] + mW / 2} ${dau[1] + yMieng - khoe * 0.8}
                Q ${dau[0] + mW * (0.26 + noi.tron * 0.16)} ${dau[1] + yMieng + mH}
                  ${dau[0]} ${dau[1] + yMieng + mH}
                Q ${dau[0] - mW * (0.26 + noi.tron * 0.16)} ${dau[1] + yMieng + mH}
                  ${dau[0] - mW / 2} ${dau[1] + yMieng - khoe * 0.8} Z`}
            fill="#6E2A2E" stroke={V} strokeWidth={NT * 1.5} strokeLinejoin="round"
          />
          {mH > 11 ? (
            <>
              <path d={`M ${dau[0] - mW / 2 + 3} ${dau[1] + yMieng - khoe * 0.8 + 1}
                        L ${dau[0] + mW / 2 - 3} ${dau[1] + yMieng - khoe * 0.8 + 1}
                        L ${dau[0] + mW / 2 - 7} ${dau[1] + yMieng - khoe * 0.8 + 8}
                        L ${dau[0] - mW / 2 + 7} ${dau[1] + yMieng - khoe * 0.8 + 8} Z`}
                    fill="#FFFFFF" />
              <ellipse cx={dau[0]} cy={dau[1] + yMieng + mH * 0.66} rx={mW * 0.28} ry={mH * 0.3} fill="#C4636B" />
            </>
          ) : null}
        </g>

        {/* NẾP CƯỜI — hai đường từ cánh mũi vòng xuống quá khoé miệng. Đậm dần theo độ cười.
            Chi tiết rẻ nhất trong cả khuôn mặt mà đổi hẳn "quốc tịch" của nó. */}
        {[-1, 1].map((sg) => (
          <path key={sg}
            d={`M ${dau[0] + sg * 11} ${dau[1] + 15}
                Q ${dau[0] + sg * (mW / 2 + 5)} ${dau[1] + yMieng - 5}
                  ${dau[0] + sg * (mW / 2 - 1)} ${dau[1] + yMieng + 6}`}
            stroke={V} strokeWidth={NT * 1.05} fill="none" strokeLinecap="round"
            opacity={0.3 + Math.max(0, E.khoe) * 0.42} />
        ))}

        {/* CẰM có ngấn — một nét cong ngắn dưới môi dưới. */}
        {camV > 0.3 ? (
          <path d={`M ${dau[0] - 11} ${dau[1] + yMieng + mH + 11} q 11 6 22 0`}
                stroke={V} strokeWidth={NT * 0.95} fill="none" strokeLinecap="round" opacity={0.4} />
        ) : null}

        {/* RÂU — vẽ SAU miệng thì nó phủ mất miệng; vẽ trước thì miệng nằm trên. Đây là bẫy đã
            gặp một lần ở bản cũ. */}
        {kieu.rau === "ria" ? (
          <path d={`M ${dau[0] - 21} ${dau[1] + yMieng - 15} q 21 -10 42 0 q -9 8 -21 8 q -12 0 -21 -8 Z`}
                fill={kieu.toc} stroke={V} strokeWidth={NT} strokeLinejoin="round" />
        ) : null}
        {kieu.rau === "de" ? (
          <path d={`M ${dau[0] - 13} ${dau[1] + yMieng + mH + 3} q 13 16 26 0 q -4 20 -13 20 q -9 0 -13 -20 Z`}
                fill={kieu.toc} stroke={V} strokeWidth={NT} strokeLinejoin="round" />
        ) : null}
        {/* RÂU QUAI NÓN — CHỈ LÀ MỘT VIỀN QUANH HÀM, không phải một mảng phủ nửa mặt.
            30/8 — bản đầu vẽ râu như một khối đặc từ tai này sang tai kia: nó nuốt sạch mũi,
            nếp cười, miệng và cằm — tức là nuốt đúng những chi tiết vừa dựng ra để mặt có nét
            Mỹ. Râu thật chỉ bám VIỀN xương hàm và chừa hẳn vùng quanh miệng.
            Vẽ bằng một dải có bề dày: đường ngoài bám mép mặt, đường trong lùi vào 20 điểm. */}
        {kieu.rau === "quai" ? (
          <path d={`M ${dau[0] - R_DAU * 0.88} ${dau[1] + 6}
                    C ${dau[0] - R_DAU * 0.9} ${dau[1] + R_DAU * 0.55}, ${dau[0] - R_DAU * 0.4} ${dau[1] + R_DAU * 1.0}, ${dau[0] + R_DAU * 0.05} ${dau[1] + R_DAU * 1.02}
                    C ${dau[0] + R_DAU * 0.5} ${dau[1] + R_DAU * 1.0}, ${dau[0] + R_DAU * 0.9} ${dau[1] + R_DAU * 0.55}, ${dau[0] + R_DAU * 0.88} ${dau[1] + 6}
                    l -13 2
                    C ${dau[0] + R_DAU * 0.66} ${dau[1] + R_DAU * 0.52}, ${dau[0] + R_DAU * 0.38} ${dau[1] + R_DAU * 0.82}, ${dau[0] + R_DAU * 0.05} ${dau[1] + R_DAU * 0.84}
                    C ${dau[0] - R_DAU * 0.3} ${dau[1] + R_DAU * 0.82}, ${dau[0] - R_DAU * 0.66} ${dau[1] + R_DAU * 0.52}, ${dau[0] - R_DAU * 0.75} ${dau[1] + 8} Z`}
                fill={kieu.toc} stroke={V} strokeWidth={NT * 0.9} strokeLinejoin="round" />
        ) : null}

        {kieu.kinh ? (
          <g stroke={V} strokeWidth={NT * 1.5} fill="none">
            <circle cx={dau[0] - cachMat} cy={dau[1] + yMat} r={rMat + 4} fill="#FFFFFF" fillOpacity={0.1} />
            <circle cx={dau[0] + cachMat} cy={dau[1] + yMat} r={rMat + 4} fill="#FFFFFF" fillOpacity={0.1} />
            <line x1={dau[0] - cachMat + rMat + 4} y1={dau[1] + yMat} x2={dau[0] + cachMat - rMat - 4} y2={dau[1] + yMat} />
            <line x1={dau[0] - cachMat - rMat - 4} y1={dau[1] + yMat} x2={dau[0] - R_DAU * 0.92} y2={dau[1] + yMat - 2} />
            <line x1={dau[0] + cachMat + rMat + 4} y1={dau[1] + yMat} x2={dau[0] + R_DAU * 0.92} y2={dau[1] + yMat - 2} />
          </g>
        ) : null}

        {/* 31/8 — TÓC BUÔNG HAI BÊN MÁ cho nhân vật nữ. Dấu hiệu thứ hai (cùng lông mi) để
            giới đọc được ngay ở khuôn mặt. Vẽ TRƯỚC khối tóc chính nên nó nằm dưới, ôm hai bên
            sọ và buông quá cằm — đúng cách một mái tóc dài đổ xuống khi nhìn chính diện. */}
        {_nu ? [-1, 1].map((sg) => (
          <path key={`tocb${sg}`}
                d={`M ${dau[0] + sg * R_DAU * 0.92} ${dau[1] - R_DAU * 0.35}
                    q ${sg * R_DAU * 0.34} ${R_DAU * 0.85} ${sg * R_DAU * 0.16} ${R_DAU * 1.5}
                    q ${-sg * R_DAU * 0.3} ${R_DAU * 0.12} ${-sg * R_DAU * 0.42} ${-R_DAU * 0.22}
                    q ${sg * R_DAU * 0.1} ${-R_DAU * 0.7} ${-sg * R_DAU * 0.04} ${-R_DAU * 1.2} Z`}
                fill={kieu.toc} stroke={V} strokeWidth={NT * 1.5} strokeLinejoin="round" />
        )) : null}

        {/* TÓC — đặt CUỐI cùng để nó phủ lên mép sọ, đúng như tóc thật phủ lên trán. */}
        {/* Con ngươi liếc sang là chưa đủ: người thật QUAY ĐẦU về phía người mình đang nói
            chuyện. Một góc nhỏ thôi — quay nhiều thành nhìn nghiêng, mất mặt. */}
        <Toc kieu={kieu} dau={dau} R={R_DAU} V={V} NG={NG} t={t} />
        {/* 30/8 — MŨ. Kiểu `Kieu` khai trường `mu` từ lâu, bảng nhân vật gán nó, JSON mang nó
            sang tận đây — mà ENGINE CHƯA BAO GIỜ VẼ. Dữ liệu đúng, hình thiếu, không một lời
            cảnh báo nào ở giữa: đây là dạng lỗi tốn nhất, vì soi JSON thấy đủ nên không ai ngờ.
            Mũ là dấu nhận dạng mạnh nhất trong bộ — đọc được ở cỡ nhỏ hơn cả tóc. */}
        <Mu kieu={kieu} dau={dau} R={R_DAU} V={V} NG={NG} />

        {/* ══ KÝ HIỆU CẢM XÚC ("emanata") — dấu hỏi, gân giận, giọt mồ hôi, tia bật ═══════
            30/8 — Anh xem clip và nói *"ko hình dung được sự hài hước"*. Một phần vì lời thoại
            là tiếng Anh: hài đối đáp kiểu Mỹ phải NGHE HIỂU mới buồn cười, còn khán giả lướt
            short thì phần lớn xem KHÔNG TIẾNG.
            Hoạt hình phương Tây giải bài này từ thời truyện tranh báo: vẽ thẳng cảm xúc thành
            KÝ HIỆU nổi quanh đầu — dấu hỏi là "không hiểu", chùm gân là "điên tiết", giọt mồ hôi
            là "chột dạ", tia bật là "sững người". Ai cũng đọc được, không cần một chữ nào.
            Đây là cách rẻ nhất để một cảnh hài đọc được khi TẮT TIẾNG — mà tắt tiếng mới là
            cách phần lớn người ta xem short. */}
        {kyHieu && (tuoiCanh < 1.35 || noNo > 0.05) ? (
          <g opacity={noNo > 0.05 ? 1 : kep((1.35 - tuoiCanh) / 0.35)}>
            <KyHieu camXuc={camXuc} dau={dau} R={R_DAU} V={V} NT={NT} t={t} manh={noNo} />
          </g>
        ) : null}
      </g>
    </g>
  );
};

/** Ký hiệu cảm xúc nổi quanh đầu. `manh` > 0 là đang ở cú giật mình — ký hiệu bật to hơn. */
const KyHieu: React.FC<{ camXuc: string; dau: [number, number]; R: number; V: string;
                         NT: number; t: number; manh: number }> =
({ camXuc, dau, R, V, NT, t, manh }) => {
  const [x, y] = dau;
  // Nhấp nhô rất nhẹ để ký hiệu "sống" chứ không dán chết vào đầu.
  const bay = Math.sin(t * 3.1) * 3;
  // Phóng 1,7 lần: ở cỡ trung cảnh trên khung dọc, ký hiệu vẽ đúng cỡ "thật" thì bé bằng đầu
  // ngón tay và không ai đọc ra. Cùng lý do phải phóng đại cử chỉ và đạo cụ.
  const co = 1.7 * (1 + manh * 0.5);
  const g = (n: React.ReactNode) => (
    <g transform={`translate(0 ${bay}) translate(${x + R * 0.86} ${y - R * 0.98}) scale(${co}) translate(${-(x + R * 0.86)} ${-(y - R * 0.98)})`}>{n}</g>
  );
  const X = x + R * 0.86, Y = y - R * 0.98;

  if (camXuc === "nghi_ngo")            // DẤU HỎI — "không hiểu nổi"
    return g(<>
      <path d={`M ${X - 8} ${Y - 8} q 0 -13 10 -13 q 11 0 11 10 q 0 8 -9 11 q -5 2 -5 8`}
            stroke={V} strokeWidth={NT * 2.4} fill="none" strokeLinecap="round" />
      <circle cx={X + 7} cy={Y + 15} r={NT * 1.5} fill={V} />
    </>);
  if (camXuc === "bat_ngo" || camXuc === "so")   // TIA BẬT — "sững người"
    return g(<>{[0, 1, 2, 3, 4].map((i) => {
      const a2 = -118 + i * 26;
      const r1 = 13, r2 = 26;
      const c = Math.cos(D(a2)), s2 = Math.sin(D(a2));
      return <line key={i} x1={X + c * r1} y1={Y + s2 * r1} x2={X + c * r2} y2={Y + s2 * r2}
                   stroke={V} strokeWidth={NT * 1.9} strokeLinecap="round" />;
    })}</>);
  if (camXuc === "tuc")                 // CHÙM GÂN — "điên tiết"
    return g(<g stroke="#D2453A" strokeWidth={NT * 2.1} fill="none" strokeLinecap="round">
      <path d={`M ${X - 11} ${Y - 9} l 9 9 l -9 9`} />
      <path d={`M ${X + 3} ${Y - 9} l 9 9 l -9 9`} />
    </g>);
  if (camXuc === "buon")                // GIỌT MỒ HÔI — "chột dạ"
    return g(<path d={`M ${X} ${Y - 13} q 10 15 4 21 q -7 5 -11 -2 q -3 -7 7 -19 Z`}
                   fill="#8FC7E8" stroke={V} strokeWidth={NT * 1.2} strokeLinejoin="round" />);
  return null;
};

// ══════════════════════════════════════════════════════════════════════════════════════════
// ĐẠO CỤ CẦM TAY
// ------------------------------------------------------------------------------------------
// 30/8 — Soi clip tham chiếu: trò đùa không nằm ở LỜI mà nằm ở HÀNH ĐỘNG — người bố lục tung ghế
// sofa, rồi giơ cái điều khiển lên. Cả đoạn ấy không cần một câu thoại nào cũng đọc ra được.
// Bộ hài của mình thì hai người đứng nói suông: mọi trò đùa dồn hết vào chữ, và chữ thì phải ĐỌC
// mới hiểu — trong khi khán giả lướt short quyết định ở lành hai giây đầu, bằng MẮT.
//
// Đạo cụ là cách rẻ nhất để có hành động: một cái cờ-lê trên tay thợ máy, một cái điện thoại
// trên tay đứa teen, một cốc cà phê ở văn phòng. Nó làm ba việc cùng lúc:
//   · nói ngay nhân vật này là AI, trước cả câu đầu tiên;
//   · cho tay một việc để làm, nên tay không còn buông thõng;
//   · và ở cú chốt, nó là thứ để CHÌA RA — cú chốt có hình chứ không chỉ có lời.
//
// Vẽ ở toạ độ bàn tay và XOAY theo hướng cẳng tay, nên nó luôn nằm đúng trong tay.
const DoVat: React.FC<{ ten: string; p: [number, number]; goc: number; V: string; NT: number }> =
({ ten, p, goc, V, NT }) => {
  const [x, y] = p;
  // PHÓNG TO 1,5 LẦN. Đo trên khung thật: ở cỡ trung cảnh, đạo cụ vẽ đúng tỉ lệ đời thật thì
  // nhỏ bằng bàn tay và bị chính bàn tay che mất. Hoạt hình luôn vẽ đạo cụ TO HƠN thật — cùng
  // lý do phải phóng đại cử chỉ (luật 7ah): khán giả đọc khung trong một phần mười giây.
  const g = (n: React.ReactNode) => (
    <g transform={`rotate(${goc - 90} ${x} ${y}) translate(${x} ${y}) scale(1.5) translate(${-x} ${-y})`}>{n}</g>
  );
  const net = { stroke: V, strokeWidth: NT * 1.3, strokeLinejoin: "round" as const };
  switch (ten) {
    case "co_le":      // cờ-lê — CAR GUY
      return g(<>
        <rect x={x - 5} y={y - 4} width={10} height={50} rx={4} fill="#9AA3AD" {...net} />
        <path d={`M ${x - 11} ${y - 4} q 0 -13 11 -13 q 11 0 11 13 l -7 0 q 0 -5 -4 -5 q -4 0 -4 5 Z`}
              fill="#9AA3AD" {...net} />
      </>);
    case "dien_thoai": // điện thoại — PARENT MODE, DATING APP
      return g(<>
        <rect x={x - 12} y={y - 2} width={24} height={42} rx={5} fill="#2A2E38" {...net} />
        <rect x={x - 8} y={y + 3} width={16} height={30} rx={2} fill="#7FC8E8" />
      </>);
    case "coc":        // cốc cà phê — OFFICE SMALL TALK, TECH SUPPORT
      return g(<>
        <path d={`M ${x - 12} ${y} l 3 32 q 1 6 9 6 q 8 0 9 -6 l 3 -32 Z`} fill="#F2EDE4" {...net} />
        <path d={`M ${x + 12} ${y + 8} q 11 2 9 12 q -2 8 -11 7`} fill="none" {...net} />
      </>);
    case "chai_nuoc":  // chai nước — GYM LIES
      return g(<>
        <rect x={x - 9} y={y + 2} width={18} height={44} rx={7} fill="#8FD3B0" {...net} />
        <rect x={x - 5} y={y - 6} width={10} height={10} rx={2} fill="#2E5A4A" {...net} />
      </>);
    case "ve_may_bay": // thẻ lên máy bay — AIRPORT HELL
      return g(<>
        <rect x={x - 16} y={y + 2} width={32} height={44} rx={3} fill="#FBF6E8" {...net} />
        <path d={`M ${x - 10} ${y + 12} l 20 0 M ${x - 10} ${y + 20} l 20 0 M ${x - 10} ${y + 28} l 12 0`}
              stroke={V} strokeWidth={NT * 0.9} opacity={0.55} />
      </>);
    case "giay_to":    // xấp giấy — RENT PANIC
      return g(<>
        <rect x={x - 15} y={y + 4} width={30} height={40} rx={2} fill="#FBF6E8" {...net}
              transform={`rotate(-7 ${x} ${y + 24})`} />
        <rect x={x - 15} y={y + 1} width={30} height={40} rx={2} fill="#FFFFFF" {...net} />
        <path d={`M ${x - 9} ${y + 11} l 18 0 M ${x - 9} ${y + 19} l 18 0 M ${x - 9} ${y + 27} l 11 0`}
              stroke={V} strokeWidth={NT * 0.9} opacity={0.5} />
      </>);
    case "banh":       // cái bánh — DIET WARS
      return g(<>
        <path d={`M ${x - 15} ${y + 14} q 15 -16 30 0 q -3 16 -15 16 q -12 0 -15 -16 Z`}
              fill="#E8A64C" {...net} />
        <path d={`M ${x - 13} ${y + 15} q 13 -12 26 0`} stroke="#C4636B" strokeWidth={NT * 1.6} fill="none" />
      </>);
    // ── BỐN ĐẠO CỤ CHO BỘ DỮ LIỆU (30/8) ─────────────────────────────────────────────
    // Cùng vai trò như đạo cụ bộ hài — nói ngay nhân vật này làm nghề gì trước cả câu thoại đầu
    // — nhưng chọn theo NGHỀ NGHIÊM TÚC, không theo trò đùa. Anh dặn: mười kênh trước phải hợp
    // niche, chỉ mượn CÁCH LÀM chứ không mượn chất hài.
    case "kinh_lup":   // kính lúp — soi điều khoản, soi hồ sơ sở hữu
      return g(<>
        <circle cx={x} cy={y + 4} r={15} fill="#CFE8F5" fillOpacity={0.55} stroke={V} strokeWidth={NT * 1.6} />
        <rect x={x - 4} y={y + 18} width={8} height={26} rx={3} fill="#6B4A2F" stroke={V} strokeWidth={NT * 1.3} />
      </>);
    case "ong_nghiem": // ống nghiệm — kênh nghiên cứu
      return g(<>
        <path d={`M ${x - 8} ${y - 4} l 0 34 q 0 10 8 10 q 8 0 8 -10 l 0 -34 Z`}
              fill="#BFE8D6" fillOpacity={0.7} stroke={V} strokeWidth={NT * 1.5} strokeLinejoin="round" />
        <path d={`M ${x - 8} ${y + 16} l 16 0 l 0 14 q 0 10 -8 10 q -8 0 -8 -10 Z`} fill="#4FA882" />
        <rect x={x - 11} y={y - 8} width={22} height={6} rx={2} fill="#9AA3AD" stroke={V} strokeWidth={NT} />
      </>);
    case "bang_ke":    // bảng kẹp hồ sơ — kênh biểu đồ, kênh chi phí
      return g(<>
        <rect x={x - 16} y={y + 2} width={32} height={42} rx={3} fill="#C9A87C" stroke={V} strokeWidth={NT * 1.4} />
        <rect x={x - 13} y={y + 7} width={26} height={33} rx={1} fill="#FBF6E8" stroke={V} strokeWidth={NT} />
        <rect x={x - 7} y={y - 2} width={14} height={8} rx={2} fill="#9AA3AD" stroke={V} strokeWidth={NT} />
        <path d={`M ${x - 8} ${y + 16} l 16 0 M ${x - 8} ${y + 24} l 16 0 M ${x - 8} ${y + 32} l 10 0`}
              stroke={V} strokeWidth={NT * 0.9} opacity={0.55} />
      </>);
    case "bua_toa":    // búa toà — kênh luật, kênh kiện tụng
      return g(<>
        <rect x={x - 4} y={y + 6} width={8} height={38} rx={3} fill="#8A5A32" stroke={V} strokeWidth={NT * 1.3} />
        <rect x={x - 17} y={y - 8} width={34} height={16} rx={5} fill="#8A5A32" stroke={V} strokeWidth={NT * 1.5} />
        <rect x={x - 12} y={y - 5} width={9} height={10} rx={2} fill="#6B4A2F" />
      </>);
    case "ong_nhom":   // ống nhòm — NEIGHBOR WATCH
      return g(<>
        <rect x={x - 16} y={y + 2} width={13} height={34} rx={5} fill="#3B4250" {...net} />
        <rect x={x + 3} y={y + 2} width={13} height={34} rx={5} fill="#3B4250" {...net} />
        <path d={`M ${x - 3} ${y + 12} l 6 0`} {...net} />
      </>);
    default:
      return null;
  }
};

/** Tóc — khối có CHÓP và có MẢNG BÓNG, không phải một vòm trơn.
 *
 * 30/8 — Soi clip tham chiếu: tóc trong dòng phim này là một KHỐI có hình, chân tóc uốn lượn
 * chứ không cắt ngang, có vài chóp nhọn nhô lên, và có một mảng đậm hơn ở chỗ khuất sáng. Bản
 * cũ vẽ một vòm tròn trơn úp lên đầu — đọc ra là cái mũ bảo hiểm chứ không phải tóc.
 *
 * Ba lớp: khối chính (có chóp) · mảng bóng (cùng màu, đậm hơn) · vài sợi rời ở mép.
 */
const Mu: React.FC<{ kieu: Kieu; dau: [number, number]; R: number; V: string; NG: number }> =
({ kieu, dau, R, V, NG }) => {
  const [x, y] = dau;
  const m = kieu.mu;
  if (!m) return null;
  const mau = kieu.ao || "#3A4B6C";
  const s = { fill: mau, stroke: V, strokeWidth: NG * 0.85, strokeLinejoin: "round" as const };
  if (m === "luoi_trai") {
    return (
      <g>
        <path d={`M ${x - R * 1.02} ${y - R * 0.34} a ${R * 1.02} ${R * 1.02} 0 0 1 ${R * 2.04} 0 Z`} {...s} />
        <path d={`M ${x + R * 0.1} ${y - R * 0.34} q ${R * 1.24} -6 ${R * 1.34} ${R * 0.24}
                  q -${R * 0.68} ${R * 0.16} -${R * 1.34} ${R * 0.02} Z`} {...s} />
      </g>
    );
  }
  if (m === "cao_bo") {
    return (
      <g>
        <path d={`M ${x - R * 0.72} ${y - R * 0.42} q 0 -${R * 0.98} ${R * 0.72} -${R * 0.98}
                  q ${R * 0.72} 0 ${R * 0.72} ${R * 0.98} Z`} {...s} />
        <path d={`M ${x - R * 1.42} ${y - R * 0.38} q ${R * 1.42} -${R * 0.3} ${R * 2.84} 0
                  q -${R * 1.42} ${R * 0.26} -${R * 2.84} 0 Z`} {...s} />
      </g>
    );
  }
  if (m === "y_ta") {
    return <path d={`M ${x - R * 0.86} ${y - R * 0.5} q ${R * 0.86} -${R * 0.44} ${R * 1.72} 0
                     l -${R * 0.16} ${R * 0.24} q -${R * 0.7} -${R * 0.3} -${R * 1.4} 0 Z`}
                 fill="#FFFFFF" stroke={V} strokeWidth={NG * 0.85} strokeLinejoin="round" />;
  }
  // "len" — mũ len trùm, có vành gấp
  return (
    <g>
      <path d={`M ${x - R * 1.0} ${y - R * 0.3} q 0 -${R * 1.1} ${R * 1.0} -${R * 1.1}
                q ${R * 1.0} 0 ${R * 1.0} ${R * 1.1} Z`} {...s} />
      <path d={`M ${x - R * 1.06} ${y - R * 0.34} h ${R * 2.12} v ${R * 0.2} h -${R * 2.12} Z`} {...s} />
    </g>
  );
};

const Toc: React.FC<{ kieu: Kieu; dau: [number, number]; R: number; V: string; NG: number; t: number }> =
({ kieu, dau, R, V, NG, t }) => {
  const c = kieu.toc, k = kieu.kieuToc;
  const [x, y] = dau;
  const dam = (h: string) => {
    const q = (h || "#4A3626").replace("#", "");
    if (q.length !== 6) return h;
    const v = [0, 2, 4].map((i) => Math.round(parseInt(q.slice(i, i + 2), 16) * 0.72));
    return "#" + v.map((n) => n.toString(16).padStart(2, "0")).join("");
  };
  const s = { fill: c, stroke: V, strokeWidth: NG * 0.85, strokeLinejoin: "round" as const };
  const tre = treo(0, t, 0.16, 2.2);
  if (k === "trocs") {
    // hói: chỉ còn một vành tóc hai bên
    return (
      <path d={`M ${x - R * 0.9} ${y - R * 0.2} q 4 -${R * 0.5} ${R * 0.34} -${R * 0.56}
                q -${R * 0.16} ${R * 0.3} -${R * 0.1} ${R * 0.56} Z
                M ${x + R * 0.9} ${y - R * 0.2} q -4 -${R * 0.5} -${R * 0.34} -${R * 0.56}
                q ${R * 0.16} ${R * 0.3} ${R * 0.1} ${R * 0.56} Z`} {...s} />
    );
  }
  // KHỐI CHÍNH — chân tóc uốn lượn (không cắt ngang), đỉnh có ba chóp nhô lên.
  const chinh = `M ${x - R * 0.92} ${y - R * 0.14}
      C ${x - R * 1.0} ${y - R * 0.84}, ${x - R * 0.5} ${y - R * 1.3}, ${x - R * 0.06} ${y - R * 1.26}
      l ${R * 0.16} -${R * 0.26} l ${R * 0.1} ${R * 0.24}
      l ${R * 0.22} -${R * 0.2} l ${R * 0.06} ${R * 0.22}
      C ${x + R * 0.68} ${y - R * 1.14}, ${x + R * 1.02} ${y - R * 0.8}, ${x + R * 0.92} ${y - R * 0.14}
      C ${x + R * 0.78} ${y - R * 0.5}, ${x + R * 0.5} ${y - R * 0.62}, ${x + R * 0.16} ${y - R * 0.56}
      C ${x - R * 0.2} ${y - R * 0.5}, ${x - R * 0.6} ${y - R * 0.44}, ${x - R * 0.92} ${y - R * 0.14} Z`;
  return (
    <g>
      <path d={chinh} {...s} />
      {/* MẢNG BÓNG — cùng màu tóc nhưng đậm hơn, nằm ở nửa khuất. Không có nó thì tóc phẳng lì. */}
      <path d={`M ${x + R * 0.2} ${y - R * 1.2}
                C ${x + R * 0.72} ${y - R * 1.06}, ${x + R * 1.0} ${y - R * 0.78}, ${x + R * 0.92} ${y - R * 0.14}
                C ${x + R * 0.8} ${y - R * 0.48}, ${x + R * 0.54} ${y - R * 0.6}, ${x + R * 0.3} ${y - R * 0.58} Z`}
            fill={dam(c)} opacity={0.85} />
      {k === "bui" ? <ellipse cx={x + tre * 0.5} cy={y - R * 1.34} rx={23} ry={20} {...s} /> : null}
      {k === "duoi_ngua" ? (
        <path d={`M ${x + R * 0.82} ${y - R * 0.62} q ${28 + tre} ${20} ${17 + tre} ${62}
                  q -13 -24 -28 -37 Z`} {...s} />
      ) : null}
      {k === "bob" ? (
        <path d={`M ${x - R * 0.92} ${y - R * 0.2} q -6 ${R * 0.92} 5 ${R * 1.08} l 13 -7
                  q -9 -${R * 0.64} -7 -${R * 0.94} Z
                  M ${x + R * 0.92} ${y - R * 0.2} q 6 ${R * 0.92} -5 ${R * 1.08} l -13 -7
                  q 9 -${R * 0.64} 7 -${R * 0.94} Z`} {...s} />
      ) : null}
      {/* 30/8 — HÓI VÀ RỐI: hai kiểu tóc bảng nhân vật vẫn gán, mà engine chưa từng vẽ riêng —
          cả hai rơi vào nhánh mặc định nên ra ĐÚNG một dáng với "ngắn". Ba tên khác nhau cho
          một mái tóc: bảng tưởng đã tách ba người, khung hình cho ra ba người giống nhau.
          Đây chính là "na ná nhau" mà anh nêu, và nó không nằm ở chỗ tôi tìm suốt mấy hôm. */}
      {k === "hoi" ? (
        <path d={`M ${x - R * 0.94} ${y - R * 0.24} q ${R * 0.1} -${R * 0.66} ${R * 0.46} -${R * 0.72}
                  q -${R * 0.16} ${R * 0.36} -${R * 0.12} ${R * 0.7} Z
                  M ${x + R * 0.94} ${y - R * 0.24} q -${R * 0.1} -${R * 0.66} -${R * 0.46} -${R * 0.72}
                  q ${R * 0.16} ${R * 0.36} ${R * 0.12} ${R * 0.7} Z
                  M ${x - R * 0.5} ${y - R * 0.96} q ${R * 0.5} -${R * 0.2} ${R * 1.0} 0
                  q -${R * 0.5} -${R * 0.06} -${R * 1.0} 0 Z`} {...s} />
      ) : null}
      {k === "roi" ? (
        <g>{[-0.74, -0.26, 0.22, 0.68].map((pp, i) => (
          <path key={i}
                d={`M ${x + pp * R * 0.9} ${y - R * 0.92}
                    l ${8 + i * 3} -${26 + (i % 2) * 14 + tre}
                    l ${9 - i * 2} ${24 + (i % 2) * 12} Z`} {...s} />
        ))}</g>
      ) : null}
      {k === "xoan" ? (
        <g>{[-0.9, -0.32, 0.32, 0.9].map((pp, i) => (
          <circle key={i} cx={x + pp * R * 0.82} cy={y - R * (0.92 + Math.abs(pp) * 0.16)} r={20} {...s} />
        ))}</g>
      ) : null}
      {/* SỢI RỜI Ở MÉP — hai ba nét mảnh nhô ra ngoài khối. Tóc không bao giờ có mép sạch. */}
      <g stroke={V} strokeWidth={NG * 0.6} fill="none" strokeLinecap="round">
        <path d={`M ${x - R * 0.86} ${y - R * 0.5} l -10 -8`} />
        <path d={`M ${x + R * 0.88} ${y - R * 0.44} l 11 -6`} />
      </g>
      {k === "re_ngoi" ? (
        <path d={`M ${x - R * 0.18} ${y - R * 1.2} q 6 ${R * 0.4} 2 ${R * 0.62}`}
              stroke={V} strokeWidth={NG * 0.55} fill="none" opacity={0.5} />
      ) : null}
    </g>
  );
};

export { visemeTai };
export type { Tu };
