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
const CU_CHI_HAI: Record<string, { vaiT: number; khuyuT: number; vaiP: number; khuyuP: number }> = {
  nghi:       { vaiT: 100, khuyuT: -8,  vaiP: 80,  khuyuP: 8 },
  chi:        { vaiT: 104, khuyuT: -10, vaiP: -86, khuyuP: -18 },   // chỉ LÊN, không chỉ ngang
  mo_tay:     { vaiT: 142, khuyuT: -74, vaiP: 38,  khuyuP: 74 },    // dang rộng hai tay
  dem:        { vaiT: 118, khuyuT: -88, vaiP: 62,  khuyuP: 88 },    // hai tay trước ngực
  suy_nghi:   { vaiT: 100, khuyuT: -6,  vaiP: 78,  khuyuP: -122 },  // tay chống cằm
  nhun_vai:   { vaiT: 148, khuyuT: -80, vaiP: 32,  khuyuP: 80 },
  gio_len:    { vaiT: 100, khuyuT: -6,  vaiP: -96, khuyuP: -12 },
  khoanh_tay: { vaiT: 122, khuyuT: -96, vaiP: 58,  khuyuP: 96 },
  // 30/8 — CHỐNG NẠNH: hai tay chống hông, khuỷu chĩa ra ngoài. Đây là tư thế ĐỨNG NGHE điển
  // hình nhất của hoạt hình Mỹ, và nó giải đúng bài toán "người nghe không được nhấp nhô mà cũng
  // không được thành tượng": một tư thế CÓ HÌNH, đọc ra ngay là đang chờ, mà đứng yên hoàn toàn.
  chong_nanh: { vaiT: 134, khuyuT: -104, vaiP: 46, khuyuP: 104 },
  // Nghiêng người dồn trọng tâm một chân, một tay buông một tay chống — dáng "chán rồi đấy".
  ngan_ngam: { vaiT: 108, khuyuT: -14, vaiP: 44, khuyuP: 108 },
};

const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const trn = (a: number, b: number, t: number) => a + (b - a) * kep(t);
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
  doVat?: string;                // đạo cụ cầm ở tay phải — xem `DAO_CU`
  giat?: number;                 // 0..1 — cú giật mình (mắt mở to, đầu bật lùi) ở cú chốt
  nghieng?: number;              // độ ngả người về phía người đối thoại
  buoc?: number;                 // 0 = đứng yên; >0 = đang bước (biên độ sải chân)
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
  doVat = "",
  x = 0, y = 0, scale = 1, lat = false,
}) => {
  const E = CAM_XUC[camXuc] || CAM_XUC.trung_tinh;
  const G = CU_CHI_HAI[cuChi as string] || CU_CHI[cuChi] || CU_CHI.nghi;
  const cao = kieu.cao ?? 1;
  const ngang = kieu.beNgang ?? 1;
  const matTo = kieu.matTo ?? 1;
  const camV = kieu.cam ?? 0.4;
  // Đầu to/nhỏ là trục đổi TUỔI mạnh nhất: đầu to đọc ra là trẻ con và hài, đầu nhỏ đọc ra là
  // người lớn nghiêm. Rẻ hơn nhiều so với vẽ lại toàn bộ nét mặt.
  const R_DAU = R_DAU_GOC * (kieu.tiLeDau ?? 1);
  const kMui = kieu.kieuMui || "moc";
  const kMat = kieu.kieuMat || "bau";
  const kMay = kieu.kieuMay || "day";

  // Nét bao dày là thứ đầu tiên mắt đọc ra "đây là phim hoạt hình". Giữ bề dày TRÊN MÀN HÌNH
  // không đổi bằng cách chia cho `scale` — không chia thì nhân vật càng xa nét càng mảnh và
  // hai người trong cùng khung trông như vẽ bằng hai cây bút khác nhau.
  const NG = 7.2 / scale;        // nét bao ngoài
  const NT = 3.4 / scale;        // nét chi tiết bên trong

  // ══ CÚ GIẬT MÌNH ("take") — ngôn ngữ hài hình ảnh cổ điển nhất của hoạt hình Mỹ ═══════
  // Khi câu chốt rơi, người NGHE phải phản ứng: mắt bật to, đầu giật lùi rồi nảy về. Đây là
  // thứ báo cho khán giả "chỗ này buồn cười" mà không cần một tiếng cười lồng nào. Không có nó
  // thì câu chốt trôi qua đúng như mọi câu khác — đó chính là chỗ anh nói "chưa thấy funny".
  // Đường cong: bật rất nhanh (0,12 giây) rồi tắt dần có nảy, giống hệt cách hoạt hình vẽ một
  // phản ứng — nhanh vào, chậm ra, có dư chấn.
  const gt = kep(giat);
  const bat = gt > 0 ? Math.exp(-gt * 3.2) * Math.sin(gt * 13) : 0;
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
  const dau: [number, number] = [co[0] + dao * 0.9 - bat * 14, co[1] - 60 * cao + gat - bat * 7];

  // Điểm gắn tay phải nằm NGOÀI mép thân, không thì cánh tay chạy chìm trong thân và bàn tay
  // đọc ra là dính vào hông. Và tay phải đủ DÀI: tay ngắn làm nhân vật đọc ra là mập lùn kể cả
  // khi thân đúng tỉ lệ — đây là chỗ bản đầu sai.
  const rongVai = 50 * ngang;
  const vaiT: [number, number] = [vai[0] - rongVai - 4, vai[1] + 8];
  const vaiP: [number, number] = [vai[0] + rongVai + 4, vai[1] + 8];
  const dtay = 86 * cao, dcang = 80 * cao;

  // Cử chỉ đi theo CUNG CÓ GIA TỐC, không đi thẳng: `muot` làm góc rời khỏi tư thế nghỉ chậm,
  // giữa nhanh, rồi dừng chậm. Tay người thật không quay đều tốc độ.
  const muot = (v: number) => v * v * (3 - 2 * v);
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

  const rongHong = 30 * ngang;
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
  const mx = kep(nhin[0], -1, 1) * 7;
  const my = kep(nhin[1], -1, 1) * 5;
  // 30/8 — MẮT NHỎ LẠI. Bản trước mắt + gọng kính chiếm 83% bề ngang đầu; mắt to là đúng
  // hướng nhưng quá tay thì đọc ra là mắt lồi ra khỏi mặt chứ không phải dễ thương. Dải đẹp
  // của hoạt hình truyền hình là hai mắt chiếm chừng 60–65% bề ngang đầu.
  // Mắt bầu dục ĐỨNG nên bề ngang hẹp hơn bản mắt-tròn cũ, và hai mắt gần nhau hơn để hợp với
  // sọ quả lê (chỗ rộng nhất nằm ngang tầm mắt, không ở giữa mặt).
  const rMat = 11.5 * matTo * (1 + gt * 0.5 * Math.exp(-gt * 2.4));
  const rTrong = 6.4 * matTo;
  const mm = 1 - chop;
  const cachMat = 17 * matTo;
  const yMat = -8;
  const yMay = yMat - 20 - E.mayCao;

  // Miệng: bề ngang và bề cao lấy thẳng từ khẩu hình, cộng độ cong khoé môi theo cảm xúc.
  const mW = trn(26, 46, noi.w) * (1 + camV * 0.05);
  const mH = trn(2.5, 34, noi.h);
  const khoe = E.khoe * 9;
  const yMieng = 26;

  return (
    <g transform={`translate(${x} ${y}) rotate(${lat ? -nghieng * 0.4 : nghieng * 0.4} 0 0) scale(${(lat ? -scale : scale) * sx} ${scale * sy})`}>
      {/* BÓNG TIẾP ĐẤT — thiếu nó thì nhân vật lơ lửng dù đứng đúng chỗ. Bóng co giãn ngược
          chiều nén–giãn: người nhún xuống thì bóng loe ra. */}
      <ellipse cx={0} cy={2} rx={62 * ngang * (1 + nen * 2)} ry={11} fill="#00000026" />

      {/* CHÂN — vẽ trước thân để thân che chỗ nối ở hông */}
      {chi(`M ${hong[0] - rongHong} ${hong[1]} Q ${goiT[0] - 4} ${goiT[1]} ${chanT[0]} ${chanT[1]}`, quan, 27 * ngang, "cT")}
      {chi(`M ${hong[0] + rongHong} ${hong[1]} Q ${goiP[0] + 4} ${goiP[1]} ${chanP[0]} ${chanP[1]}`, quan, 27 * ngang, "cP")}
      {/* Giày tô màu RIÊNG, không dùng màu nét. Khung đo được: quần sẫm + giày màu nét = một
          khối tối liền từ hông xuống sàn, không đọc ra là có bàn chân. */}
      {giay(chanT, -1, "gT")}
      {giay(chanP, 1, "gP")}

      {/* TAY SAU (bên trái) — vẽ trước thân, nên nó nằm sau lưng: ra chiều sâu mà không cần đổ bóng */}
      {chi(`M ${vaiT[0]} ${vaiT[1]} Q ${khuyuT[0]} ${khuyuT[1]} ${tayT[0]} ${tayT[1]}`, aoSau, 23 * ngang, "tT")}
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
      {kieu.phuKien === "the_deo" ? (
        <g>
          <path d={`M ${vai[0] - 16} ${vai[1] + 6} Q ${vai[0]} ${vai[1] + 52} ${vai[0] + 16} ${vai[1] + 6}`}
                stroke={V} strokeWidth={NT * 1.3} fill="none" />
          <rect x={vai[0] - 11} y={vai[1] + 46} width={22} height={28} rx={4}
                fill="#F4F7FC" stroke={V} strokeWidth={NT} />
        </g>
      ) : null}

      {/* TAY TRƯỚC (bên phải) — vẽ sau thân nên nằm trước ngực */}
      {chi(`M ${vaiP[0]} ${vaiP[1]} Q ${khuyuP[0]} ${khuyuP[1]} ${tayP[0]} ${tayP[1]}`, aoTruoc, 23 * ngang, "tP")}
      {ban(tayP, gocVP + gocKP, "bP")}
      {doVat ? <DoVat ten={doVat} p={tayP} goc={gocVP + gocKP} V={V} NT={NT} /> : null}

      {/* CỔ — bản đầu vẽ quá ngắn nên đầu dính thẳng vào vai, đọc ra là một khối. Cổ phải
          THẤY ĐƯỢC thì đầu mới quay được một cách có nghĩa. */}
      {chi(`M ${co[0]} ${co[1] + 24} L ${dau[0]} ${dau[1] + R_DAU * 0.54}`, da, 38, "co")}

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
                     ry={rMat * (kMat === "tron" ? 1.0 : kMat === "hep" ? 0.62 : 1.24)
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

        {/* TÓC — đặt CUỐI cùng để nó phủ lên mép sọ, đúng như tóc thật phủ lên trán. */}
        <Toc kieu={kieu} dau={dau} R={R_DAU} V={V} NG={NG} t={t} />
      </g>
    </g>
  );
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
