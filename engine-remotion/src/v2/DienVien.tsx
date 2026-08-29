import React from "react";

/**
 * DIỄN VIÊN V2 — con rối vector 2D điều khiển được từng khung (29/8/2026).
 *
 * VÌ SAO 2D VECTOR CHỨ KHÔNG PHẢI 3D THẬT
 * ---------------------------------------
 * Anh gửi sáu ảnh tham chiếu và nói "3D animation". Nhưng cả sáu ảnh ấy đều là VECTOR 2D PHẲNG:
 * nét viền dày đều, màu bệt, không có khối, không có bóng đổ theo nguồn sáng. Con cú đội mũ Uncle
 * Sam, hai ông hàng xóm bên hàng rào, bà cô trên ghế bập bênh — tất cả là 2D.
 * Đó là tin tốt, vì hai đường đi rất khác nhau về chi phí:
 *   • 3D thật cần model có rig xương, blendshape khẩu hình, texture — mình không có sẵn, mà máy
 *     vẽ ảnh thì không sinh ra được model, chỉ sinh ra được ẢNH. Đi đường đó là mua một kho asset
 *     rồi vẫn phải dựng lại toàn bộ pipeline.
 *   • 2D vector thì mình VẼ RA từng khung bằng SVG, nên điều khiển được đúng mười thứ anh liệt kê
 *     tới từng khung hình, và render bằng chính Remotion đang chạy — không thêm một phụ thuộc nào.
 * Nhìn ra màn hình thì kết quả GIỐNG ảnh tham chiếu hơn hẳn một bản 3D làm vội.
 *
 * MƯỜI THỨ ANH DẶN, NẰM Ở ĐÂU TRONG TỆP NÀY
 *   👄 khẩu hình khớp giọng  -> `Mieng` + `visemeTai` (đọc mốc thời gian từng TỪ của edge-tts)
 *   👀 mắt nhìn đúng hướng   -> `Mat` nhận `nhin` (vector -1..1), con ngươi lệch theo
 *   😮 biểu cảm theo thoại   -> `CAM_XUC` đổi chân mày + mí + khoé miệng + nghiêng đầu
 *   🗣️ giọng có cảm xúc      -> chọn ở tầng Python (kiểu giọng + tốc độ theo `cam_xuc` từng cảnh)
 *   👐 cử chỉ tay            -> `CU_CHI` đặt góc vai/khuỷu, lò xo giảm chấn đưa tay tới đích
 *   🚶 đi/chạy/ngồi/nhảy     -> `DANG` (tư thế gốc) + `buoc()` cho chu kỳ chân
 *   🎭 bộ cảm xúc            -> `CAM_XUC`: vui, buồn, sợ, tức, bất ngờ, nghi ngờ, trung tính
 *   🎥 máy quay đổi góc      -> ở `KichV2` (thành phần cha), không thuộc diễn viên
 *   👕 chuyển động phụ       -> `treo()` cho tóc/cà vạt/vạt áo đi trễ sau thân
 *   🔊 tiếng động            -> ở `KichV2`, gắn theo mốc hành động
 */

const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const trn = (a: number, b: number, t: number) => a + (b - a) * kep(t);
const D = (deg: number) => (deg * Math.PI) / 180;

/** Điểm cuối của một đoạn xương: từ (x,y) đi `d` theo góc `a` độ. */
const P = (x: number, y: number, d: number, a: number): [number, number] =>
  [x + d * Math.cos(D(a)), y + d * Math.sin(D(a))];

// ══════════════════════════════════════════════════════════════════════════════════════════
// BỘ CẢM XÚC
// ------------------------------------------------------------------------------------------
// Mỗi cảm xúc là một BỘ SỐ, không phải một hình vẽ riêng. Nhờ vậy trộn được giữa hai cảm xúc
// (chuyển từ trung tính sang bất ngờ trong 8 khung) mà không cần vẽ thêm hình trung gian nào.
//   may     : góc chân mày (dương = cụp vào giữa, giận/lo)
//   mayCao  : chân mày nâng lên bao nhiêu (bất ngờ nâng cao, buồn hạ thấp)
//   mi      : mí trên che bao nhiêu phần mắt (0 = mở to, 1 = nhắm)
//   khoe    : khoé miệng (dương = cười, âm = mếu)
//   ha      : miệng hé sẵn bao nhiêu khi KHÔNG nói
//   nghieng : độ nghiêng đầu
//   than    : độ ngả thân (dương = ngả ra sau, âm = chồm tới)
// ══════════════════════════════════════════════════════════════════════════════════════════
export type TenCamXuc =
  | "trung_tinh" | "vui" | "buon" | "so" | "tuc" | "bat_ngo" | "nghi_ngo" | "tu_tin";

export const CAM_XUC: Record<TenCamXuc, {
  may: number; mayCao: number; mi: number; khoe: number; ha: number; nghieng: number; than: number;
}> = {
  trung_tinh: { may: 0, mayCao: 0, mi: 0.08, khoe: 0.1, ha: 0.05, nghieng: 0, than: 0 },
  vui: { may: -4, mayCao: 2.5, mi: 0.22, khoe: 1, ha: 0.22, nghieng: -3, than: -1.5 },
  buon: { may: 12, mayCao: -3, mi: 0.34, khoe: -0.8, ha: 0.04, nghieng: 6, than: 3 },
  so: { may: 16, mayCao: 5, mi: -0.16, khoe: -0.5, ha: 0.42, nghieng: -2, than: 5 },
  tuc: { may: -18, mayCao: -4, mi: 0.02, khoe: -0.65, ha: 0.1, nghieng: 0, than: -4 },
  bat_ngo: { may: 2, mayCao: 8, mi: -0.24, khoe: 0.1, ha: 0.62, nghieng: -1, than: -2 },
  nghi_ngo: { may: -6, mayCao: 3, mi: 0.3, khoe: -0.15, ha: 0.04, nghieng: 7, than: 1 },
  tu_tin: { may: -3, mayCao: 1, mi: 0.06, khoe: 0.55, ha: 0.06, nghieng: -2, than: -2.5 },
};

// ══════════════════════════════════════════════════════════════════════════════════════════
// KHẨU HÌNH
// ------------------------------------------------------------------------------------------
// KHÔNG có phiên âm âm vị trong dữ liệu — edge-tts chỉ trả mốc thời gian từng TỪ. Nên suy khẩu
// hình TỪ CHÍNH CHỮ VIẾT: nguyên âm trong từ quyết định chuỗi hình miệng, và chuỗi ấy trải đều
// trong khoảng thời gian của từ đó.
// Đây là phép xấp xỉ, và tôi nói rõ nó là xấp xỉ. Nhưng ở 30 khung/giây, thứ mắt người bắt được
// là MIỆNG CÓ MỞ ĐÚNG LÚC CÓ TIẾNG hay không, và mở RỘNG hay HẸP — chứ không phải có đúng âm /æ/
// hay /ɛ/. Hai điều đó thì suy từ chữ viết là đủ đúng.
// Cái sai duy nhất còn lại: từ có chữ câm ("through", "knight"). Đổi lại là không cần thư viện
// phiên âm nào, không cần lượt gọi mạng nào.
// ══════════════════════════════════════════════════════════════════════════════════════════
type Viseme = { w: number; h: number; tron: number };   // bề ngang, bề cao, độ tròn môi
const VISEME: Record<string, Viseme> = {
  im: { w: 0.42, h: 0.05, tron: 0 },     // ngậm
  a: { w: 0.66, h: 0.72, tron: 0 },      // "father"
  e: { w: 0.74, h: 0.36, tron: 0 },      // "bed"
  i: { w: 0.78, h: 0.18, tron: 0 },      // "see"
  o: { w: 0.44, h: 0.6, tron: 0.85 },    // "go"
  u: { w: 0.3, h: 0.34, tron: 1 },       // "you"
  m: { w: 0.46, h: 0.03, tron: 0.15 },   // môi khép: m, b, p
  f: { w: 0.56, h: 0.14, tron: 0 },      // f, v — răng chạm môi
};

/** Chuỗi khẩu hình của một từ, suy từ nguyên âm; phụ âm môi chèn hình khép vào giữa. */
const chuoiHinh = (tu: string): string[] => {
  const t = (tu || "").toLowerCase().replace(/[^a-z]/g, "");
  if (!t) return ["im"];
  const ra: string[] = [];
  for (let i = 0; i < t.length; i++) {
    const c = t[i];
    if ("aeiouy".includes(c)) {
      // nguyên âm đôi hay gặp: "ou"/"ow" -> tròn môi, "ea"/"ee" -> hẹp
      const k = t[i + 1] || "";
      if (c === "o" && (k === "u" || k === "w")) { ra.push("o", "u"); i++; continue; }
      if (c === "e" && (k === "e" || k === "a")) { ra.push("i"); i++; continue; }
      ra.push(c === "y" ? "i" : c);
    } else if ("mbp".includes(c)) {
      ra.push("m");
    } else if ("fv".includes(c)) {
      ra.push("f");
    }
  }
  if (!ra.length) ra.push("e");
  return ra;
};

export type Tu = { t: number; d: number; w: string };

/**
 * Khẩu hình tại giây `giay`. Trả về hình miệng đã TRỘN giữa hai hình liền kề — chuyển mượt chứ
 * không giật từng nấc, vì miệng thật không nhảy cóc giữa các tư thế.
 */
export const visemeTai = (tu: Tu[], giay: number, haSan: number): Viseme => {
  const im = { ...VISEME.im, h: VISEME.im.h + haSan * 0.5 };
  if (!tu || !tu.length) return im;
  // từ đang phát: mốc t <= giay < t + d
  let k = -1;
  for (let i = 0; i < tu.length; i++) {
    if (giay >= tu[i].t && giay < tu[i].t + tu[i].d) { k = i; break; }
    if (tu[i].t > giay) break;
  }
  if (k < 0) return im;                       // khoảng lặng giữa hai từ -> ngậm
  const ds = chuoiHinh(tu[k].w);
  const p = kep((giay - tu[k].t) / Math.max(0.001, tu[k].d));
  const vt = p * ds.length;
  const i0 = Math.min(ds.length - 1, Math.floor(vt));
  const i1 = Math.min(ds.length - 1, i0 + 1);
  const f = vt - i0;
  const A = VISEME[ds[i0]] || VISEME.e;
  const B = VISEME[ds[i1]] || VISEME.e;
  return { w: trn(A.w, B.w, f), h: trn(A.h, B.h, f), tron: trn(A.tron, B.tron, f) };
};

// ══════════════════════════════════════════════════════════════════════════════════════════
// CỬ CHỈ TAY & TƯ THẾ
// ------------------------------------------------------------------------------------------
// Góc tính theo hệ SVG: 0° là hướng sang PHẢI, tăng theo chiều kim đồng hồ (y hướng xuống).
// `vai` = góc cánh tay trên so với thân; `khuyu` = góc cẳng tay so với cánh tay trên.
// ══════════════════════════════════════════════════════════════════════════════════════════
export type TenCuChi =
  | "nghi" | "chi" | "mo_tay" | "dem" | "suy_nghi" | "nhun_vai" | "gio_len" | "khoanh_tay";

// 29/8 — GÓC TUYỆT ĐỐI TRONG HỆ SVG, KHÔNG CỘNG THÊM 90 Ở CHỖ DÙNG.
// Khung render đầu tiên cho ra một nhân vật duỗi thẳng hai tay ngang vai như bù nhìn. Vì bảng
// này ghi góc "so với thân" rồi chỗ dùng lại cộng thêm 90 — hai quy ước chồng lên nhau, và
// "nghỉ" (78) hoá ra 168 độ, tức chỉ thẳng sang trái.
// Nay chỉ còn MỘT quy ước, ghi ngay đây: 90 = thẳng xuống đất · 0 = ngang sang phải ·
// 180 = ngang sang trái · số ÂM = chếch lên. Đọc bảng là hình dung ra tư thế.
export const CU_CHI: Record<TenCuChi, {
  vaiT: number; khuyuT: number; vaiP: number; khuyuP: number; banT?: number; banP?: number;
}> = {
  nghi: { vaiT: 100, khuyuT: -8, vaiP: 80, khuyuP: 8 },                    // buông xuôi, hơi hở nách
  chi: { vaiT: 100, khuyuT: -4, vaiP: -22, khuyuP: 14 },                   // tay phải trỏ chếch LÊN
  mo_tay: { vaiT: 128, khuyuT: -46, vaiP: 52, khuyuP: 46 },                // ngửa hai bàn tay ra
  dem: { vaiT: 112, khuyuT: -58, vaiP: 68, khuyuP: 58 },                   // hai tay lên trước ngực
  suy_nghi: { vaiT: 100, khuyuT: -6, vaiP: 74, khuyuP: -96 },              // tay phải chống cằm
  nhun_vai: { vaiT: 138, khuyuT: -54, vaiP: 42, khuyuP: 54 },
  gio_len: { vaiT: 100, khuyuT: -6, vaiP: -52, khuyuP: -18 },              // giơ tay phải lên cao
  khoanh_tay: { vaiT: 116, khuyuT: -72, vaiP: 64, khuyuP: 72 },            // khoanh trước ngực
};

export type TenDang = "dung" | "ngoi" | "di" | "chay" | "nhay";

// ══════════════════════════════════════════════════════════════════════════════════════════
// KIỂU NHÂN VẬT — mỗi niche một dáng người, một bộ đồ, một bảng màu
// ------------------------------------------------------------------------------------------
// Giữ trong DỮ LIỆU chứ không phải trong mã vẽ: thêm một kênh mới là thêm một dòng, không phải
// viết thêm một thành phần React. Đây là chỗ 50 kênh không giẫm chân nhau về mặt hình.
// ══════════════════════════════════════════════════════════════════════════════════════════
export type Kieu = {
  da: string; toc: string; kieuToc: "bui" | "ngan" | "roi" | "hoi" | "trocs";
  ao: string; aoTrong: string; quan: string; net: string;
  kinh?: boolean; rau?: "" | "ria" | "quai"; caVat?: string;
  mu?: "" | "luoi_trai" | "cao_bo" | "y_ta";
  aoKhoac?: string;                 // vạt áo có chuyển động trễ (blouse, áo choàng)
  cao?: number;                     // 0.92 = thấp đậm, 1.06 = cao gầy
  beNgang?: number;                 // 0.9 = mảnh, 1.15 = đậm người
};

export const KIEU_MAU: Record<string, Kieu> = {
  // Ba kiểu gốc — các kênh dẫn xuất từ đây rồi đổi màu, xem `kich_v2.py`.
  nam_dam: { da: "#F2C08A", toc: "#4A3220", kieuToc: "ngan", ao: "#C0392B", aoTrong: "#FFFFFF",
             quan: "#2C6E8F", net: "#241A12", rau: "ria", mu: "luoi_trai", cao: 0.96, beNgang: 1.16 },
  nu_kinh: { da: "#F6CBA0", toc: "#5A3A24", kieuToc: "bui", ao: "#D6353B", aoTrong: "#F6E5D8",
             quan: "#8E2C31", net: "#2A1C14", kinh: true, aoKhoac: "#D6353B", cao: 1.02, beNgang: 0.94 },
  nam_gay: { da: "#EFC49A", toc: "#6B4426", kieuToc: "roi", ao: "#F2C230", aoTrong: "#F2C230",
             quan: "#3E7CA6", net: "#26190F", cao: 1.06, beNgang: 0.88 },
};

// ══════════════════════════════════════════════════════════════════════════════════════════
// CHUYỂN ĐỘNG PHỤ — tóc, cà vạt, vạt áo đi TRỄ sau thân
// ------------------------------------------------------------------------------------------
// Đây là thứ tách một con rối "có hồn" khỏi một hình cắt dán biết trượt. Mắt người không đọc ra
// "tóc đang trễ 4 khung", nhưng đọc ngay ra "cái này không sống" khi mọi thứ cứng đơ cùng nhau.
// Làm bằng lò xo giảm chấn một chiều: giá trị đuổi theo mục tiêu, có quán tính, có ma sát.
// ══════════════════════════════════════════════════════════════════════════════════════════
const treo = (dich: number, t: number, tre = 0.13, bien = 1) => {
  // Không giữ trạng thái giữa các khung (Remotion render song song từng khung, không có state
  // liên tục) — nên mô phỏng bằng hàm của thời gian: lấy giá trị đích ở thời điểm TRỄ hơn, cộng
  // một dao động tắt dần. Cùng kết quả thị giác, mà thuần hàm nên khung nào render cũng như nhau.
  return dich + Math.sin((t - tre) * 7.5) * bien * 0.35 * Math.exp(-Math.abs(Math.sin(t * 1.1)) * 0.6);
};

export type PropsDien = {
  kieu: Kieu;
  camXuc: TenCamXuc;
  cuChi: TenCuChi;
  dang: TenDang;
  nhin: [number, number];        // -1..1 theo trục ngang/dọc; [0,0] = nhìn thẳng ống kính
  noi: Viseme;                   // khẩu hình khung này
  t: number;                     // giây trong cảnh (cho thở, chớp mắt, trễ)
  x?: number; y?: number; scale?: number; lat?: boolean;
};

/** Một diễn viên hoàn chỉnh. Vẽ trong hệ toạ độ cao 420, gốc ở giữa chân. */
export const DienVien: React.FC<PropsDien> = ({
  kieu, camXuc, cuChi, dang, nhin, noi, t, x = 0, y = 0, scale = 1, lat = false,
}) => {
  const E = CAM_XUC[camXuc] || CAM_XUC.trung_tinh;
  const G = CU_CHI[cuChi] || CU_CHI.nghi;
  const cao = kieu.cao ?? 1;
  const ngang = kieu.beNgang ?? 1;
  const net = kieu.net;
  const NET = Math.max(2.6, 4.2 * scale) / scale;      // nét viền dày đều như ảnh tham chiếu

  // ── NHỊP SỐNG: thở, đảo người, chớp mắt ────────────────────────────────────────────────
  const tho = Math.sin(t * 1.9) * 0.9;                  // vai nhô lên xuống
  const dao = Math.sin(t * 0.62) * 1.7;                 // thân đảo rất nhẹ
  // Chớp mắt: không đều nhịp. Nhịp đều đọc ra ngay là máy.
  const chuKy = 3.1 + Math.sin(t * 0.37) * 1.4;
  const pChop = (t % chuKy) / chuKy;
  const chop = pChop > 0.965 ? Math.sin((pChop - 0.965) / 0.035 * Math.PI) : 0;

  const nghiengDau = E.nghieng + dao * 0.5 + treo(0, t, 0.1, 0.5);
  const nganThan = E.than + dao;

  // ── KHUNG XƯƠNG ────────────────────────────────────────────────────────────────────────
  const hong: [number, number] = [0, dang === "ngoi" ? -96 * cao : -168 * cao];
  const vai: [number, number] = [0, hong[1] - 108 * cao + tho];
  const co: [number, number] = [vai[0] + nganThan * 0.5, vai[1] - 20 * cao];
  const dauR = 62 * cao;
  const dauC: [number, number] = [co[0] + nghiengDau * 0.55, co[1] - dauR * 0.78];

  const rongVai = 52 * ngang;
  const vaiT: [number, number] = [vai[0] - rongVai, vai[1]];
  const vaiP: [number, number] = [vai[0] + rongVai, vai[1]];
  const daiTren = 74 * cao, daiDuoi = 70 * cao;

  // Lò xo đưa tay tới đích cử chỉ: không nhảy cóc, có một nhịp nhún nhẹ khi tới nơi.
  const nhun = (g: number) => g + Math.sin(t * 2.3) * 2.4;
  const khuyuT = P(vaiT[0], vaiT[1], daiTren, nhun(G.vaiT));
  const tayT = P(khuyuT[0], khuyuT[1], daiDuoi, nhun(G.vaiT) + G.khuyuT);
  const khuyuP = P(vaiP[0], vaiP[1], daiTren, nhun(G.vaiP));
  const tayP = P(khuyuP[0], khuyuP[1], daiDuoi, nhun(G.vaiP) + G.khuyuP);

  // ── CHÂN: đứng / ngồi / bước ───────────────────────────────────────────────────────────
  const buoc = dang === "di" ? Math.sin(t * 5.4) : dang === "chay" ? Math.sin(t * 9.2) : 0;
  const bienBuoc = dang === "chay" ? 34 : 20;
  const nhayY = dang === "nhay" ? -Math.abs(Math.sin(t * 3.4)) * 46 : 0;
  const goiT = dang === "ngoi"
    ? P(hong[0] - 16, hong[1], 78 * cao, 8)
    : P(hong[0] - 15, hong[1], 84 * cao, 90 + buoc * bienBuoc * 0.36);
  const chanT = dang === "ngoi"
    ? P(goiT[0], goiT[1], 80 * cao, 88)
    : P(goiT[0], goiT[1], 82 * cao, 90 - buoc * bienBuoc * 0.2);
  const goiP = dang === "ngoi"
    ? P(hong[0] + 16, hong[1], 78 * cao, 6)
    : P(hong[0] + 15, hong[1], 84 * cao, 90 - buoc * bienBuoc * 0.36);
  const chanP = dang === "ngoi"
    ? P(goiP[0], goiP[1], 80 * cao, 88)
    : P(goiP[0], goiP[1], 82 * cao, 90 + buoc * bienBuoc * 0.2);

  // ── MẶT ────────────────────────────────────────────────────────────────────────────────
  const matY = dauC[1] - dauR * 0.06;
  const matX = dauR * 0.34;
  const matR = dauR * 0.235;
  const nhinX = kep(nhin[0], -1, 1) * matR * 0.42;
  const nhinY = kep(nhin[1], -1, 1) * matR * 0.34;
  const mo = kep(1 - E.mi - chop * 1.35, 0, 1);          // độ mở mắt 0..1

  const mieng = { x: dauC[0] + nghiengDau * 0.2, y: dauC[1] + dauR * 0.44 };
  const mW = dauR * (0.2 + noi.w * 0.3);
  const mH = dauR * (0.02 + Math.max(noi.h, E.ha * 0.5) * 0.26);
  const cong = E.khoe * dauR * 0.1;                       // khoé miệng nhếch/mếu

  // 29/8 — DÙNG THUỘC TÍNH `transform` CỦA SVG, KHÔNG DÙNG `style`.
  // Ba lần liền tôi đổi hệ số cỡ (1.12 -> 2.1 -> 3.0) mà khung render ra GIỐNG HỆT NHAU, và tôi
  // suýt đi đổ lỗi cho máy quay. Gốc là chỗ này: đặt qua `style` thì trình duyệt đọc chuỗi ấy
  // bằng luật CSS, mà CSS đòi đơn vị và dấu phẩy — `translate(0 236) scale(3 3)` là cú pháp SVG,
  // CSS không phân tích được nên VỨT CẢ CHUỖI. Không lỗi, không cảnh báo, chỉ là không có gì xảy
  // ra. Thuộc tính `transform` của SVG thì nhận đúng cú pháp này.
  const bien = `translate(${x} ${y}) scale(${(lat ? -scale : scale)} ${scale})`;
  const vien = { stroke: net, strokeWidth: NET, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, fill: "none" };

  return (
    <g transform={bien}>
      <g transform={`translate(0 ${nhayY})`}>
        {/* ── CHÂN ───────────────────────────────────────────────────────────── */}
        {([[goiT, chanT], [goiP, chanP]] as [number[], number[]][]).map((v, i) => (
          <g key={i}>
            <path d={`M ${hong[0] + (i ? 15 : -15)} ${hong[1]} L ${v[0][0]} ${v[0][1]} L ${v[1][0]} ${v[1][1]}`}
                  {...vien} strokeWidth={NET * 5.4} stroke={kieu.quan} />
            <path d={`M ${hong[0] + (i ? 15 : -15)} ${hong[1]} L ${v[0][0]} ${v[0][1]} L ${v[1][0]} ${v[1][1]}`}
                  {...vien} strokeWidth={NET * 6.4} stroke={net} opacity={0.001} />
            <ellipse cx={v[1][0] + (i ? 9 : -9)} cy={v[1][1] + 5} rx={20} ry={9} fill={net} />
          </g>
        ))}

        {/* ── THÂN ───────────────────────────────────────────────────────────── */}
        <path d={`M ${vaiT[0]} ${vaiT[1]} Q ${vai[0]} ${vai[1] - 12} ${vaiP[0]} ${vaiP[1]}
                  L ${hong[0] + 40 * ngang} ${hong[1]} Q ${hong[0]} ${hong[1] + 12} ${hong[0] - 40 * ngang} ${hong[1]} Z`}
              fill={kieu.ao} stroke={net} strokeWidth={NET} strokeLinejoin="round" />
        {/* cổ áo + áo trong */}
        <path d={`M ${vai[0] - 20} ${vai[1] - 4} L ${vai[0]} ${vai[1] + 30} L ${vai[0] + 20} ${vai[1] - 4} Z`}
              fill={kieu.aoTrong} stroke={net} strokeWidth={NET * 0.8} />
        {kieu.caVat ? (
          <path d={`M ${vai[0]} ${vai[1] + 6} l 9 12 l -6 ${52 * cao} l -6 0 l -6 ${-52 * cao} Z`}
                fill={kieu.caVat} stroke={net} strokeWidth={NET * 0.7}
                transform={`rotate(${treo(0, t, 0.16, 2.4)} ${vai[0]} ${vai[1] + 6})`} />
        ) : null}
        {/* vạt áo khoác — CHUYỂN ĐỘNG PHỤ: đi trễ sau thân */}
        {kieu.aoKhoac ? (
          <path d={`M ${vaiT[0] - 4} ${vaiT[1] + 6} Q ${vaiT[0] - 16} ${hong[1] - 40} ${vaiT[0] - 6} ${hong[1] + 6}
                    l 22 0 L ${vaiT[0] + 16} ${vaiT[1] + 10} Z`}
                fill={kieu.aoKhoac} stroke={net} strokeWidth={NET * 0.85}
                transform={`rotate(${treo(0, t, 0.2, 3.1)} ${vaiT[0]} ${vaiT[1]})`} />
        ) : null}

        {/* ── TAY ────────────────────────────────────────────────────────────── */}
        {([[vaiT, khuyuT, tayT], [vaiP, khuyuP, tayP]] as [number[], number[], number[]][]).map((v, i) => (
          <g key={i}>
            <path d={`M ${v[0][0]} ${v[0][1]} L ${v[1][0]} ${v[1][1]} L ${v[2][0]} ${v[2][1]}`}
                  {...vien} strokeWidth={NET * 4.4} stroke={kieu.ao} />
            <circle cx={v[2][0]} cy={v[2][1]} r={13} fill={kieu.da} stroke={net} strokeWidth={NET} />
          </g>
        ))}

        {/* ── ĐẦU ────────────────────────────────────────────────────────────── */}
        <g transform={`rotate(${nghiengDau} ${dauC[0]} ${dauC[1] + dauR * 0.8})`}>
          <path d={`M ${co[0] - 15} ${co[1] + 4} l 30 0 l 0 -22 l -30 0 Z`} fill={kieu.da} stroke={net} strokeWidth={NET} />
          <ellipse cx={dauC[0]} cy={dauC[1]} rx={dauR * 0.86} ry={dauR} fill={kieu.da} stroke={net} strokeWidth={NET} />

          {/* tai */}
          <ellipse cx={dauC[0] - dauR * 0.86} cy={dauC[1] + 4} rx={9} ry={13} fill={kieu.da} stroke={net} strokeWidth={NET} />
          <ellipse cx={dauC[0] + dauR * 0.86} cy={dauC[1] + 4} rx={9} ry={13} fill={kieu.da} stroke={net} strokeWidth={NET} />

          {/* TÓC — trễ sau đầu (chuyển động phụ) */}
          <g transform={`rotate(${treo(0, t, 0.14, 1.8)} ${dauC[0]} ${dauC[1]})`}>
            {kieu.kieuToc === "bui" ? (
              <>
                <path d={`M ${dauC[0] - dauR * 0.9} ${dauC[1] - dauR * 0.2}
                          Q ${dauC[0]} ${dauC[1] - dauR * 1.5} ${dauC[0] + dauR * 0.9} ${dauC[1] - dauR * 0.2}
                          Q ${dauC[0]} ${dauC[1] - dauR * 0.72} ${dauC[0] - dauR * 0.9} ${dauC[1] - dauR * 0.2} Z`}
                      fill={kieu.toc} stroke={net} strokeWidth={NET} />
                <ellipse cx={dauC[0]} cy={dauC[1] - dauR * 1.34} rx={dauR * 0.46} ry={dauR * 0.4}
                         fill={kieu.toc} stroke={net} strokeWidth={NET} />
              </>
            ) : kieu.kieuToc === "roi" ? (
              <path d={`M ${dauC[0] - dauR * 0.88} ${dauC[1] - dauR * 0.25}
                        q ${dauR * 0.2} ${-dauR * 0.9} ${dauR * 0.5} ${-dauR * 0.55}
                        q ${dauR * 0.12} ${-dauR * 0.5} ${dauR * 0.36} ${-dauR * 0.2}
                        q ${dauR * 0.2} ${-dauR * 0.42} ${dauR * 0.44} ${-dauR * 0.02}
                        q ${dauR * 0.3} ${dauR * 0.1} ${dauR * 0.28} ${dauR * 0.72} Z`}
                    fill={kieu.toc} stroke={net} strokeWidth={NET} />
            ) : kieu.kieuToc === "trocs" ? null : (
              <path d={`M ${dauC[0] - dauR * 0.9} ${dauC[1] - dauR * 0.12}
                        Q ${dauC[0]} ${dauC[1] - dauR * 1.42} ${dauC[0] + dauR * 0.9} ${dauC[1] - dauR * 0.12}
                        Q ${dauC[0] + dauR * 0.4} ${dauC[1] - dauR * 0.66} ${dauC[0]} ${dauC[1] - dauR * 0.6}
                        Q ${dauC[0] - dauR * 0.4} ${dauC[1] - dauR * 0.54} ${dauC[0] - dauR * 0.9} ${dauC[1] - dauR * 0.12} Z`}
                    fill={kieu.toc} stroke={net} strokeWidth={NET} />
            )}
          </g>

          {/* MŨ */}
          {kieu.mu === "luoi_trai" ? (
            <g transform={`rotate(${treo(0, t, 0.12, 1.2)} ${dauC[0]} ${dauC[1]})`}>
              <path d={`M ${dauC[0] - dauR * 0.92} ${dauC[1] - dauR * 0.3}
                        Q ${dauC[0]} ${dauC[1] - dauR * 1.5} ${dauC[0] + dauR * 0.92} ${dauC[1] - dauR * 0.3} Z`}
                    fill="#E8DCC0" stroke={net} strokeWidth={NET} />
              <path d={`M ${dauC[0] + dauR * 0.2} ${dauC[1] - dauR * 0.3}
                        q ${dauR * 1.1} ${-dauR * 0.06} ${dauR * 1.05} ${dauR * 0.2}
                        q ${-dauR * 0.5} ${dauR * 0.16} ${-dauR * 1.05} ${dauR * 0.02} Z`}
                    fill="#C9B98F" stroke={net} strokeWidth={NET} />
            </g>
          ) : null}

          {/* CHÂN MÀY — cảm xúc đọc ra ở đây trước cả miệng */}
          {[-1, 1].map((s) => (
            <path key={s}
                  d={`M ${dauC[0] + s * matX - 20} ${matY - dauR * 0.36 - E.mayCao * 1.7 + s * E.may * 0.28}
                      q 20 ${-7 - E.mayCao * 0.5} 40 ${s * E.may * 0.34}`}
                  stroke={kieu.toc} strokeWidth={NET * 2.1} fill="none" strokeLinecap="round" />
          ))}

          {/* MẮT */}
          {[-1, 1].map((s) => (
            <g key={s}>
              <ellipse cx={dauC[0] + s * matX} cy={matY} rx={matR} ry={matR * (0.36 + mo * 0.72)}
                       fill="#FFFFFF" stroke={net} strokeWidth={NET * 0.9} />
              {mo > 0.08 ? (
                <>
                  <circle cx={dauC[0] + s * matX + nhinX} cy={matY + nhinY}
                          r={matR * 0.5} fill="#2B2118" />
                  <circle cx={dauC[0] + s * matX + nhinX + matR * 0.17}
                          cy={matY + nhinY - matR * 0.19} r={matR * 0.15} fill="#FFFFFF" />
                </>
              ) : null}
            </g>
          ))}
          {kieu.kinh ? (
            <g stroke={net} strokeWidth={NET * 1.15} fill="none">
              <rect x={dauC[0] - matX - matR * 1.5} y={matY - matR * 1.25}
                    width={matR * 3} height={matR * 2.5} rx={matR * 0.5} />
              <rect x={dauC[0] + matX - matR * 1.5} y={matY - matR * 1.25}
                    width={matR * 3} height={matR * 2.5} rx={matR * 0.5} />
              <path d={`M ${dauC[0] - matX + matR * 1.5} ${matY} L ${dauC[0] + matX - matR * 1.5} ${matY}`} />
            </g>
          ) : null}

          {/* MŨI */}
          <path d={`M ${dauC[0] - 5} ${dauC[1] + dauR * 0.2} q 6 9 12 0`}
                stroke={net} strokeWidth={NET * 0.95} fill="none" strokeLinecap="round" />

          {/* MIỆNG — bề ngang/cao lấy từ khẩu hình, khoé lấy từ cảm xúc */}
          <path d={`M ${mieng.x - mW} ${mieng.y - cong}
                    Q ${mieng.x} ${mieng.y + mH * 1.5 + cong * 0.6} ${mieng.x + mW} ${mieng.y - cong}
                    Q ${mieng.x} ${mieng.y - mH * 0.4 + cong * 0.6} ${mieng.x - mW} ${mieng.y - cong} Z`}
                fill={mH > dauR * 0.05 ? "#8C2F2F" : net} stroke={net} strokeWidth={NET * 0.95}
                strokeLinejoin="round" />
          {mH > dauR * 0.12 ? (
            <path d={`M ${mieng.x - mW * 0.72} ${mieng.y - cong * 0.6}
                      q ${mW * 0.72} ${mH * 0.42} ${mW * 1.44} 0 Z`} fill="#FFFFFF" opacity={0.92} />
          ) : null}

          {/* RÂU */}
          {kieu.rau === "ria" ? (
            <path d={`M ${dauC[0] - 30} ${dauC[1] + dauR * 0.34}
                      q 30 ${-14} 60 0 q ${-16} 16 ${-30} 16 q ${-14} 0 ${-30} ${-16} Z`}
                  fill={kieu.toc} stroke={net} strokeWidth={NET * 0.8} />
          ) : null}

          {/* má hồng — chi tiết nhỏ mà tách hẳn khỏi cảm giác "hình cắt dán" */}
          {[-1, 1].map((s) => (
            <ellipse key={s} cx={dauC[0] + s * dauR * 0.58} cy={dauC[1] + dauR * 0.3}
                     rx={dauR * 0.17} ry={dauR * 0.1} fill="#E9836F" opacity={camXuc === "vui" ? 0.5 : 0.28} />
          ))}
        </g>
      </g>
    </g>
  );
};
