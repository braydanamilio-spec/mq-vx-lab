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
  da: string; toc: string;
  kieuToc: "bui" | "ngan" | "roi" | "hoi" | "trocs" | "duoi_ngua" | "xoan" | "bob" | "re_ngoi";
  ao: string; aoTrong: string; quan: string; net: string;
  kinh?: boolean; rau?: "" | "ria" | "quai" | "de"; caVat?: string;
  mu?: "" | "luoi_trai" | "cao_bo" | "y_ta" | "len";
  aoKhoac?: string;                 // vạt áo có chuyển động trễ (blouse, áo choàng)
  // 29/8 — PHỤ KIỆN THEO NGHỀ. Anh: "10 channel thì phong cách nhân vật 10 channel phù hợp 10
  // phong cách style khác nhau… ko chung chung 1 template". Ba kiểu gốc dùng cho mười kênh thì
  // nhìn ra ngay là một khuôn tô lại màu. Thứ tách một nhân vật khỏi nhân vật khác trong phim
  // hoạt hình không phải màu áo — mà là NGHỀ của nó hiện lên người: áo blouse, áo choàng toà,
  // ống nghe, thẻ đeo cổ. Người xem đọc ra nghề trước khi nghe câu đầu tiên.
  phuKien?: "" | "ao_blouse" | "ao_choang" | "ong_nghe" | "the_deo" | "no_buom" | "khan_quang";
  cao?: number;                     // 0.92 = thấp đậm, 1.06 = cao gầy
  beNgang?: number;                 // 0.9 = mảnh, 1.15 = đậm người
  matTo?: number;                   // 1.0 chuẩn; >1 mắt to hơn (trẻ hơn, ngơ ngác hơn)
  cam?: number;                     // độ bạnh của hàm: 0 = tròn, 1 = vuông vức
  // ══ NÉT MẶT RIÊNG — thêm 30/8/2026 ══════════════════════════════════════════════════
  // Anh đã dặn nhiều lần: *"10 channel thì phong cách nhân vật 10 channel… ko chung chung 1
  // template"*. Sau khi dựng lại khuôn mặt kiểu hoạt hình Mỹ, cả mười kênh dùng CHUNG một
  // khuôn — chỉ khác chiều cao, bề ngang, cỡ mắt và độ bạnh hàm. Bốn trục ấy đổi được DÁNG
  // NGƯỜI nhưng không đổi được KHUÔN MẶT: nhìn mười khung cạnh nhau vẫn ra một người tô lại.
  //
  // Trong hoạt hình, thứ tách hai nhân vật ra không phải màu áo mà là BA NÉT: mũi, mắt, lông
  // mày. Một cái mũi củ hành và một cái mũi nhọn cho ra hai người khác hẳn dù mọi thứ khác
  // giống nhau. Nên thêm đúng ba trục ấy, mỗi trục vài kiểu — mười kênh chọn mười tổ hợp.
  kieuMui?: "moc" | "cu" | "nhon" | "hat" | "quap";
  kieuMat?: "bau" | "tron" | "hep" | "xech";
  kieuMay?: "day" | "manh" | "xech" | "ru";
  tiLeDau?: number;                 // 0.9 = đầu nhỏ (dáng người lớn) · 1.12 = đầu to (trẻ, hài)
};

// MƯỜI NHÂN VẬT, MỖI KÊNH MỘT NGƯỜI. Khác nhau ở SÁU trục cùng lúc — dáng người, kiểu tóc,
// râu, kính, phụ kiện nghề, bảng màu — nên không hai người nào đọc ra là cùng một hình tô lại.
export const KIEU_MAU: Record<string, Kieu> = {
  // 1. BANK RUN — nữ giao dịch viên, gọn gàng, thẻ đeo cổ
  bank: { da: "#F6CBA0", toc: "#4A3626", kieuToc: "bui", ao: "#1D7A5F", aoTrong: "#FFFFFF",
          quan: "#1B4B3A", net: "#20180F", kinh: true, phuKien: "the_deo", caVat: "#0E5C46",
          cao: 1.02, beNgang: 0.94, matTo: 1.0, cam: 0.25 ,
            // nét mặt riêng (30/8): mũi/mắt/lông mày là ba thứ tách hai nhân vật ra.
            // Không tổ hợp nào trùng hai mươi nhân vật bộ hài — `cham_v4` chốt việc đó.
            kieuMui: "moc", kieuMat: "bau", kieuMay: "day", tiLeDau: 0.97 },
  // 2. FINE PRINT — luật sư trẻ, tóc rẽ ngôi, nơ bướm, cao gầy
  luat_tre: { da: "#EFC49A", toc: "#2E2018", kieuToc: "re_ngoi", ao: "#2B4C7E", aoTrong: "#FFFFFF",
              quan: "#1B2E4B", net: "#191F2B", phuKien: "no_buom", cao: 1.08, beNgang: 0.86,
              matTo: 1.05, cam: 0.5 ,
            // nét mặt riêng (30/8): mũi/mắt/lông mày là ba thứ tách hai nhân vật ra.
            // Không tổ hợp nào trùng hai mươi nhân vật bộ hài — `cham_v4` chốt việc đó.
            kieuMui: "nhon", kieuMat: "xech", kieuMay: "manh", tiLeDau: 1.03 },
  // 3. WHO OWNS IT — ông chú sân sau, ria rậm, mũ lưỡi trai, đậm người
  hang_xom: { da: "#F2C08A", toc: "#5A3A1E", kieuToc: "ngan", ao: "#C0392B", aoTrong: "#FFFFFF",
              quan: "#2C6E8F", net: "#241A12", rau: "ria", mu: "luoi_trai",
              cao: 0.95, beNgang: 1.2, matTo: 0.95, cam: 0.7 ,
            // nét mặt riêng (30/8): mũi/mắt/lông mày là ba thứ tách hai nhân vật ra.
            // Không tổ hợp nào trùng hai mươi nhân vật bộ hài — `cham_v4` chốt việc đó.
            kieuMui: "cu", kieuMat: "tron", kieuMay: "day", tiLeDau: 0.98 },
  // 4. KNOW YOUR RIGHT — nữ cựu công tố, tóc bob, áo choàng sẫm
  cong_to: { da: "#E8B489", toc: "#241A14", kieuToc: "bob", ao: "#3B2E5A", aoTrong: "#F2EDE4",
             quan: "#241C38", net: "#1B1526", phuKien: "ao_choang", aoKhoac: "#3B2E5A",
             cao: 1.03, beNgang: 0.96, matTo: 1.0, cam: 0.35 ,
            // nét mặt riêng (30/8): mũi/mắt/lông mày là ba thứ tách hai nhân vật ra.
            // Không tổ hợp nào trùng hai mươi nhân vật bộ hài — `cham_v4` chốt việc đó.
            kieuMui: "moc", kieuMat: "hep", kieuMay: "xech", tiLeDau: 0.99 },
  // 5. SUED IN AMERICA — thẩm phán về hưu, hói, râu quai nón, bệ vệ
  tham_phan: { da: "#E5B085", toc: "#8A8A86", kieuToc: "trocs", ao: "#2C2438", aoTrong: "#FFFFFF",
               quan: "#221C2E", net: "#1A1522", rau: "quai", caVat: "#8A2F3C",
               phuKien: "ao_choang", aoKhoac: "#2C2438", cao: 0.98, beNgang: 1.22,
               matTo: 0.92, cam: 0.8 ,
            // nét mặt riêng (30/8): mũi/mắt/lông mày là ba thứ tách hai nhân vật ra.
            // Không tổ hợp nào trùng hai mươi nhân vật bộ hài — `cham_v4` chốt việc đó.
            kieuMui: "quap", kieuMat: "hep", kieuMay: "day", tiLeDau: 0.9 },
  // 6. SKY TONIGHT — cô gái trẻ, đuôi ngựa, khăn quàng, áo khoác dạ
  sao_dem: { da: "#F4C6A0", toc: "#3A2A44", kieuToc: "duoi_ngua", ao: "#2E4E86", aoTrong: "#DCE6F5",
             quan: "#22355C", net: "#161B2E", phuKien: "khan_quang", aoKhoac: "#2E4E86",
             cao: 1.0, beNgang: 0.9, matTo: 1.12, cam: 0.15 ,
            // nét mặt riêng (30/8): mũi/mắt/lông mày là ba thứ tách hai nhân vật ra.
            // Không tổ hợp nào trùng hai mươi nhân vật bộ hài — `cham_v4` chốt việc đó.
            kieuMui: "hat", kieuMat: "xech", kieuMay: "manh", tiLeDau: 1.08 },
  // 7. ONE EXPERIMENT — nhà khoa học tóc xoăn rối, áo blouse trắng
  khoa_hoc: { da: "#E9B98A", toc: "#3E2A1C", kieuToc: "xoan", ao: "#F2A33C", aoTrong: "#FFFFFF",
              quan: "#4C74AE", net: "#1E1A14", kinh: true, phuKien: "ao_blouse",
              cao: 1.04, beNgang: 0.95, matTo: 1.08, cam: 0.3 ,
            // nét mặt riêng (30/8): mũi/mắt/lông mày là ba thứ tách hai nhân vật ra.
            // Không tổ hợp nào trùng hai mươi nhân vật bộ hài — `cham_v4` chốt việc đó.
            kieuMui: "nhon", kieuMat: "tron", kieuMay: "day", tiLeDau: 1.01 },
  // 8. DEEP FIELD — người kể lớn tuổi, tóc bạc rẽ, râu dê, trầm
  vu_tru_gia: { da: "#DFAF84", toc: "#B9B6AE", kieuToc: "hoi", ao: "#33305C", aoTrong: "#C9CBE0",
                quan: "#232244", net: "#12112A", rau: "de", cao: 1.0, beNgang: 1.02,
                matTo: 0.96, cam: 0.55 ,
            // nét mặt riêng (30/8): mũi/mắt/lông mày là ba thứ tách hai nhân vật ra.
            // Không tổ hợp nào trùng hai mươi nhân vật bộ hài — `cham_v4` chốt việc đó.
            kieuMui: "quap", kieuMat: "bau", kieuMay: "ru", tiLeDau: 0.92 },
  // 9. WHAT THE CHART SAYS — y tá, áo scrubs xanh, ống nghe, mũ y tá
  y_ta: { da: "#F3C49C", toc: "#2E2018", kieuToc: "bui", ao: "#4E9C93", aoTrong: "#DFF1EE",
          quan: "#2F6E68", net: "#17322F", phuKien: "ong_nghe", mu: "y_ta",
          cao: 1.0, beNgang: 0.98, matTo: 1.05, cam: 0.3 ,
            // nét mặt riêng (30/8): mũi/mắt/lông mày là ba thứ tách hai nhân vật ra.
            // Không tổ hợp nào trùng hai mươi nhân vật bộ hài — `cham_v4` chốt việc đó.
            kieuMui: "hat", kieuMat: "bau", kieuMay: "ru", tiLeDau: 1.07 },
  // 10. PRICE OF CARE — nhân viên viện phí, tóc ngắn, kính, cà vạt, dáng vuông
  vien_phi: { da: "#EDBE93", toc: "#4A3220", kieuToc: "ngan", ao: "#B8474F", aoTrong: "#FFFFFF",
              quan: "#3A3F52", net: "#20222E", kinh: true, caVat: "#7A2E38", phuKien: "the_deo",
              cao: 0.99, beNgang: 1.1, matTo: 0.98, cam: 0.65 ,
            // nét mặt riêng (30/8): mũi/mắt/lông mày là ba thứ tách hai nhân vật ra.
            // Không tổ hợp nào trùng hai mươi nhân vật bộ hài — `cham_v4` chốt việc đó.
            kieuMui: "cu", kieuMat: "xech", kieuMay: "manh", tiLeDau: 0.96 },
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
  // 29/8 — NÉT KHÔNG ĐƯỢC DÀY ĐỀU. Anh: "nhân vật xấu chưa có style phong cách, chưa chuẩn usa".
  // Thứ tách một hình vẽ nghiệp dư khỏi một nhân vật hoạt hình chuyên nghiệp, trước cả tạo hình,
  // là ĐỘ DÀY NÉT BIẾN THIÊN: đường bao ngoài dày, chi tiết bên trong mảnh hơn hẳn. Phim hoạt
  // hình Mỹ nào cũng làm thế — nó tạo chiều sâu mà không cần đổ bóng, và làm nhân vật bật ra
  // khỏi nền. Vẽ mọi thứ bằng MỘT độ dày thì hình đọc ra là hình cắt giấy.
  const NET = Math.max(2.6, 4.2 * scale) / scale;      // nét CHI TIẾT (bên trong hình)
  const NGOAI = NET * 1.75;                            // nét ĐƯỜNG BAO (ngoài cùng)

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
  const _cam = kep(kieu.cam ?? 0.35, 0, 1);
  const matR = dauR * 0.235 * (kieu.matTo ?? 1);
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
        {/* BÓNG ĐỔ DƯỚI CHÂN — thiếu bóng thì nhân vật trông như dán lơ lửng trước nền chứ
            không như đứng trên mặt đất. Một hình bầu dục mờ là đủ, mắt tự hiểu phần còn lại. */}
        <ellipse cx={0} cy={6} rx={92 * ngang} ry={15} fill={net} opacity={0.16} />
        {([[goiT, chanT], [goiP, chanP]] as [number[], number[]][]).map((v, i) => (
          <g key={i}>
            {/* ỐNG QUẦN CÓ DÁNG: rộng ở đùi, thu ở gối. Vẽ bằng đường bao thay vì một nét thẳng
                dày — nét thẳng cho ra hai cái que, mà que thì không có dáng người. */}
            <path d={`M ${hong[0] + (i ? 4 : -34)} ${hong[1] - 6}
                      L ${v[0][0] - 15} ${v[0][1]} L ${v[1][0] - 14} ${v[1][1]}
                      L ${v[1][0] + 14} ${v[1][1]} L ${v[0][0] + 15} ${v[0][1]}
                      L ${hong[0] + (i ? 34 : -4)} ${hong[1] - 6} Z`}
                  fill={kieu.quan} stroke={net} strokeWidth={NGOAI} strokeLinejoin="round" />
            {/* GIÀY: mũi hếch, gót vuông. Hình bầu dục đọc ra là một cục, không ra giày. */}
            <path d={`M ${v[1][0] - 15} ${v[1][1] - 2}
                      L ${v[1][0] - 16} ${v[1][1] + 12}
                      Q ${v[1][0] - 12} ${v[1][1] + 18} ${v[1][0] + (i ? 30 : -30)} ${v[1][1] + 17}
                      Q ${v[1][0] + (i ? 38 : -38)} ${v[1][1] + 10} ${v[1][0] + (i ? 26 : -26)} ${v[1][1] - 2} Z`}
                  fill={net} stroke={net} strokeWidth={NGOAI} strokeLinejoin="round" />
          </g>
        ))}

        {/* ── THÂN ───────────────────────────────────────────────────────────── */}
        <path d={`M ${vaiT[0]} ${vaiT[1]} Q ${vai[0]} ${vai[1] - 12} ${vaiP[0]} ${vaiP[1]}
                  L ${hong[0] + 40 * ngang} ${hong[1]} Q ${hong[0]} ${hong[1] + 12} ${hong[0] - 40 * ngang} ${hong[1]} Z`}
              fill={kieu.ao} stroke={net} strokeWidth={NGOAI} strokeLinejoin="round" />
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

        {/* ── PHỤ KIỆN NGHỀ ──────────────────────────────────────────────────────
            Vẽ SAU thân và TRƯỚC tay: nó nằm đè lên áo nhưng bị bàn tay che khi tay đưa ngang
            ngực — đúng thứ tự lớp của đời thật. Đây là thứ cho người xem đọc ra NGHỀ của nhân
            vật trước khi nghe câu đầu tiên. */}
        {kieu.phuKien === "ao_blouse" || kieu.phuKien === "ao_choang" ? (
          <g transform={`rotate(${treo(0, t, 0.19, 2.6)} ${vai[0]} ${vai[1]})`}>
            {/* 29/8 — VẠT ÁO PHẢI BÁM THEO DÁNG THÂN. Anh cắt khung nhà khoa học: hai tấm
                trắng dựng đứng hai bên, không ăn nhập gì với người bên trong, đọc ra như hai
                mảnh giấy dán lên. Vì bản cũ dựng vạt áo từ toạ độ VAI và HÔNG rời nhau, không
                theo đường bao của thân.
                Nay vạt đi đúng đường bao ấy: hẹp ở vai, phình ở hông, có ve áo gập ra ngoài —
                ba nét làm nên một cái áo khoác thay vì một tấm bảng. */}
            {[-1, 1].map((sd) => (
              <path key={sd}
                    d={`M ${vai[0] + sd * (rongVai * 0.86)} ${vai[1] + 2}
                        Q ${vai[0] + sd * (rongVai + 10)} ${vai[1] + 70}
                          ${vai[0] + sd * (rongVai * 0.92 + 12)} ${hong[1] + 34}
                        L ${vai[0] + sd * (rongVai * 0.3)} ${hong[1] + 34}
                        Q ${vai[0] + sd * (rongVai * 0.34)} ${vai[1] + 96}
                          ${vai[0] + sd * 16} ${vai[1] + 26} Z`}
                    fill={kieu.phuKien === "ao_blouse" ? "#FFFFFF" : (kieu.aoKhoac || kieu.ao)}
                    stroke={net} strokeWidth={NET} strokeLinejoin="round" />
            ))}
            {/* ve áo — nếp gập nhỏ ở ngực, thứ khiến mắt đọc ra "áo khoác" ngay lập tức */}
            {[-1, 1].map((sd) => (
              <path key={"ve" + sd}
                    d={`M ${vai[0] + sd * 16} ${vai[1] + 26}
                        L ${vai[0] + sd * (rongVai * 0.78)} ${vai[1] + 4}
                        L ${vai[0] + sd * (rongVai * 0.5)} ${vai[1] + 62} Z`}
                    fill={kieu.phuKien === "ao_blouse" ? "#EDEAE2" : (kieu.aoTrong || "#EDEAE2")}
                    stroke={net} strokeWidth={NET * 0.85} strokeLinejoin="round" />
            ))}
          </g>
        ) : null}
        {kieu.phuKien === "ong_nghe" ? (
          <g stroke={net} strokeWidth={NET * 1.5} fill="none" strokeLinecap="round">
            <path d={`M ${vai[0] - 22} ${vai[1] + 14}
                      Q ${vai[0] - 30} ${vai[1] + 74} ${vai[0] + 4} ${vai[1] + 92}
                      Q ${vai[0] + 38} ${vai[1] + 74} ${vai[0] + 26} ${vai[1] + 14}`} />
            <circle cx={vai[0] + 4} cy={vai[1] + 100} r={13} fill="#C9CDD4" stroke={net} strokeWidth={NET} />
          </g>
        ) : null}
        {kieu.phuKien === "the_deo" ? (
          <g transform={`rotate(${treo(0, t, 0.17, 3.2)} ${vai[0]} ${vai[1] + 8})`}>
            <path d={`M ${vai[0] - 20} ${vai[1] + 6} L ${vai[0] + 2} ${vai[1] + 72}
                      L ${vai[0] + 22} ${vai[1] + 6}`} stroke={net} strokeWidth={NET * 1.2} fill="none" />
            <rect x={vai[0] - 14} y={vai[1] + 70} width={32} height={42} rx={5}
                  fill="#F2F4F7" stroke={net} strokeWidth={NET} />
            <rect x={vai[0] - 8} y={vai[1] + 78} width={20} height={7} rx={3} fill={kieu.ao} />
          </g>
        ) : null}
        {kieu.phuKien === "no_buom" ? (
          <g transform={`translate(${vai[0]} ${vai[1] + 18})`}>
            <path d={`M -26 -12 L -6 0 L -26 12 Z`} fill={kieu.caVat || "#8A2F3C"} stroke={net} strokeWidth={NET} />
            <path d={`M 26 -12 L 6 0 L 26 12 Z`} fill={kieu.caVat || "#8A2F3C"} stroke={net} strokeWidth={NET} />
            <circle cx={0} cy={0} r={7} fill={kieu.caVat || "#8A2F3C"} stroke={net} strokeWidth={NET} />
          </g>
        ) : null}
        {kieu.phuKien === "khan_quang" ? (
          <g transform={`rotate(${treo(0, t, 0.2, 4)} ${vai[0]} ${vai[1]})`}>
            <path d={`M ${vai[0] - 40} ${vai[1] - 2} q 40 26 80 0 q 4 22 -6 30 q -36 16 -70 0 q -8 -10 -4 -30 Z`}
                  fill={kieu.aoKhoac || "#B8474F"} stroke={net} strokeWidth={NET} />
            <path d={`M ${vai[0] + 26} ${vai[1] + 26} q 16 34 4 68 l -22 -6 q 10 -30 0 -58 Z`}
                  fill={kieu.aoKhoac || "#B8474F"} stroke={net} strokeWidth={NET} />
          </g>
        ) : null}

        {/* ── TAY ────────────────────────────────────────────────────────────── */}
        {([[vaiT, khuyuT, tayT], [vaiP, khuyuP, tayP]] as [number[], number[], number[]][]).map((v, i) => (
          <g key={i}>
            <path d={`M ${v[0][0]} ${v[0][1]} L ${v[1][0]} ${v[1][1]} L ${v[2][0]} ${v[2][1]}`}
                  {...vien} strokeWidth={NET * 4.4} stroke={kieu.ao} />
            {/* KHỚP VAI: một chỏm tròn cùng màu áo, che chỗ tay cắm vào thân. Thiếu nó thì cánh
                tay đọc ra là một cái ống gắn rời — đúng thứ anh chỉ trong khung cắt. */}
            <circle cx={v[0][0]} cy={v[0][1]} r={NET * 2.4} fill={kieu.ao}
                    stroke={net} strokeWidth={NET} />
            {/* BÀN TAY hình găng, hơi bầu về phía trước, KHÔNG phải một quả bóng. */}
            <ellipse cx={v[2][0]} cy={v[2][1]} rx={15} ry={12.5} fill={kieu.da}
                     stroke={net} strokeWidth={NET}
                     transform={`rotate(${Math.atan2(v[2][1] - v[1][1], v[2][0] - v[1][0]) * 57.3} ${v[2][0]} ${v[2][1]})`} />
          </g>
        ))}

        {/* ── ĐẦU ────────────────────────────────────────────────────────────── */}
        <g transform={`rotate(${nghiengDau} ${dauC[0]} ${dauC[1] + dauR * 0.8})`}>
          <path d={`M ${co[0] - 15} ${co[1] + 4} l 30 0 l 0 -22 l -30 0 Z`} fill={kieu.da} stroke={net} strokeWidth={NET} />
          {/* 29/8 — HÀM BẠNH THEO NHÂN VẬT. Mười khuôn mặt bầu dục y hệt nhau thì đổi màu áo
              bao nhiêu cũng vẫn đọc ra là một người. Trong phim hoạt hình Mỹ, thứ phân biệt nhân
              vật mạnh nhất là ĐƯỜNG HÀM: tròn = trẻ/hiền, vuông = già/cứng. `cam` 0 tới 1 kéo
              cằm từ bầu dục sang bạnh, và một đường cong nối lên gò má giữ cho nó vẫn mềm. */}
          <path d={`M ${dauC[0] - dauR * 0.86} ${dauC[1] - dauR * 0.1}
                    Q ${dauC[0] - dauR * 0.86} ${dauC[1] - dauR} ${dauC[0]} ${dauC[1] - dauR}
                    Q ${dauC[0] + dauR * 0.86} ${dauC[1] - dauR} ${dauC[0] + dauR * 0.86} ${dauC[1] - dauR * 0.1}
                    L ${dauC[0] + dauR * (0.7 + 0.16 * (1 - _cam))} ${dauC[1] + dauR * (0.62 + 0.1 * _cam)}
                    Q ${dauC[0] + dauR * 0.4 * (1 - _cam * 0.5)} ${dauC[1] + dauR * (1 - _cam * 0.14)}
                      ${dauC[0]} ${dauC[1] + dauR * (1 - _cam * 0.16)}
                    Q ${dauC[0] - dauR * 0.4 * (1 - _cam * 0.5)} ${dauC[1] + dauR * (1 - _cam * 0.14)}
                      ${dauC[0] - dauR * (0.7 + 0.16 * (1 - _cam))} ${dauC[1] + dauR * (0.62 + 0.1 * _cam)} Z`}
                fill={kieu.da} stroke={net} strokeWidth={NGOAI} strokeLinejoin="round" />

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
            ) : kieu.kieuToc === "duoi_ngua" ? (
              <>
                <path d={`M ${dauC[0] - dauR * 0.9} ${dauC[1] - dauR * 0.18}
                          Q ${dauC[0]} ${dauC[1] - dauR * 1.44} ${dauC[0] + dauR * 0.9} ${dauC[1] - dauR * 0.18}
                          Q ${dauC[0]} ${dauC[1] - dauR * 0.66} ${dauC[0] - dauR * 0.9} ${dauC[1] - dauR * 0.18} Z`}
                      fill={kieu.toc} stroke={net} strokeWidth={NET} />
                {/* đuôi tóc — đi trễ nhiều nhất trong mọi bộ phận, nên biên độ lớn hơn */}
                <path d={`M ${dauC[0] + dauR * 0.82} ${dauC[1] - dauR * 0.2}
                          q ${dauR * 0.6} ${dauR * 0.3} ${dauR * 0.34} ${dauR * 1.16}
                          q ${-dauR * 0.3} ${dauR * 0.1} ${-dauR * 0.42} ${-dauR * 0.16}
                          q ${dauR * 0.16} ${-dauR * 0.5} ${-dauR * 0.2} ${-dauR * 0.82} Z`}
                      fill={kieu.toc} stroke={net} strokeWidth={NET}
                      transform={`rotate(${treo(0, t, 0.22, 4.6)} ${dauC[0] + dauR * 0.8} ${dauC[1] - dauR * 0.2})`} />
              </>
            ) : kieu.kieuToc === "xoan" ? (
              <g fill={kieu.toc} stroke={net} strokeWidth={NET}>
                {[[-0.72, -0.5, 0.42], [-0.3, -0.86, 0.46], [0.22, -0.9, 0.44],
                  [0.68, -0.52, 0.4], [-0.02, -0.62, 0.4]].map((c, i) => (
                  <circle key={i} cx={dauC[0] + dauR * c[0]} cy={dauC[1] + dauR * c[1]} r={dauR * c[2]} />
                ))}
              </g>
            ) : kieu.kieuToc === "bob" ? (
              <path d={`M ${dauC[0] - dauR * 0.96} ${dauC[1] + dauR * 0.34}
                        L ${dauC[0] - dauR * 0.96} ${dauC[1] - dauR * 0.24}
                        Q ${dauC[0]} ${dauC[1] - dauR * 1.42} ${dauC[0] + dauR * 0.96} ${dauC[1] - dauR * 0.24}
                        L ${dauC[0] + dauR * 0.96} ${dauC[1] + dauR * 0.34}
                        L ${dauC[0] + dauR * 0.66} ${dauC[1] + dauR * 0.34}
                        Q ${dauC[0] + dauR * 0.72} ${dauC[1] - dauR * 0.5} ${dauC[0]} ${dauC[1] - dauR * 0.56}
                        Q ${dauC[0] - dauR * 0.72} ${dauC[1] - dauR * 0.5} ${dauC[0] - dauR * 0.66} ${dauC[1] + dauR * 0.34} Z`}
                    fill={kieu.toc} stroke={net} strokeWidth={NET} />
            ) : kieu.kieuToc === "re_ngoi" ? (
              <path d={`M ${dauC[0] - dauR * 0.9} ${dauC[1] - dauR * 0.14}
                        Q ${dauC[0] - dauR * 0.5} ${dauC[1] - dauR * 1.3} ${dauC[0] + dauR * 0.16} ${dauC[1] - dauR * 1.06}
                        Q ${dauC[0] + dauR * 0.8} ${dauC[1] - dauR * 0.9} ${dauC[0] + dauR * 0.9} ${dauC[1] - dauR * 0.1}
                        Q ${dauC[0] + dauR * 0.5} ${dauC[1] - dauR * 0.62} ${dauC[0] - dauR * 0.06} ${dauC[1] - dauR * 0.72}
                        Q ${dauC[0] - dauR * 0.5} ${dauC[1] - dauR * 0.78} ${dauC[0] - dauR * 0.9} ${dauC[1] - dauR * 0.14} Z`}
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
                  {/* MÍ TRÊN — nét cong đè lên mép trên tròng. Thiếu nó thì mắt là hai cái đĩa
                      dán lên mặt; có nó thì mắt nằm TRONG hốc mắt. */}
                  <path d={`M ${dauC[0] + s * matX - matR} ${matY - matR * (0.1 + mo * 0.5)}
                            q ${matR} ${-matR * 0.62} ${matR * 2} 0`}
                        stroke={net} strokeWidth={NET * 1.1} fill="none" strokeLinecap="round" />
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

          {/* 29/8 — RÂU VẼ TRƯỚC MIỆNG, KHÔNG VẼ SAU.
              Anh cắt khung thẩm phán: cả vùng miệng bị một mảng xám bịt kín. Không phải hình
              râu vẽ sai — mà là THỨ TỰ LỚP sai. Râu đang vẽ SAU miệng nên nó nằm đè lên trên,
              và một bộ râu che mất miệng thì nhân vật vừa xấu vừa mất hẳn khẩu hình — tức mất
              luôn thứ công phu nhất của cả cỗ máy này.
              Trong đời thật râu mọc quanh miệng chứ không phủ lên miệng. Đổi thứ tự là xong,
              không cần vẽ lại một nét nào. */}
          {kieu.rau === "de" ? (
            <path d={`M ${dauC[0] - 16} ${dauC[1] + dauR * 0.52}
                      q 16 -8 32 0 q -2 ${dauR * 0.36} -16 ${dauR * 0.4}
                      q -14 ${-dauR * 0.04} -16 ${-dauR * 0.4} Z`}
                  fill={kieu.toc} stroke={net} strokeWidth={NET * 0.8} />
          ) : kieu.rau === "quai" ? (
            // 29/8 — RÂU QUAI NÓN LÀ MỘT CÁI VIỀN, KHÔNG PHẢI MỘT MẢNG ĐẶC.
            // Anh cắt khung thẩm phán: cả nửa dưới khuôn mặt là một khối xám bịt kín, miệng
            // biến mất, đọc ra như lỗi hiển thị chứ không ra một bộ râu. Bản cũ vẽ một mảng
            // liền từ má trái sang má phải rồi phủ luôn xuống cằm.
            // Râu thật ôm THEO ĐƯỜNG HÀM và chừa hẳn vùng miệng: một dải cong bám mép mặt,
            // dày ở quai hàm, mỏng dần lên má. Vẽ bằng hai đường cong đồng tâm rồi tô phần
            // giữa — nên nó luôn là một cái viền, không bao giờ thành mảng đặc.
            <path d={`M ${dauC[0] - dauR * 0.84} ${dauC[1] - dauR * 0.02}
                      Q ${dauC[0] - dauR * 0.8} ${dauC[1] + dauR * 0.86} ${dauC[0]} ${dauC[1] + dauR * 0.94}
                      Q ${dauC[0] + dauR * 0.8} ${dauC[1] + dauR * 0.86} ${dauC[0] + dauR * 0.84} ${dauC[1] - dauR * 0.02}
                      L ${dauC[0] + dauR * 0.6} ${dauC[1] + dauR * 0.04}
                      Q ${dauC[0] + dauR * 0.56} ${dauC[1] + dauR * 0.62} ${dauC[0]} ${dauC[1] + dauR * 0.68}
                      Q ${dauC[0] - dauR * 0.56} ${dauC[1] + dauR * 0.62} ${dauC[0] - dauR * 0.6} ${dauC[1] + dauR * 0.04} Z`}
                  fill={kieu.toc} stroke={net} strokeWidth={NET * 0.8} strokeLinejoin="round" />
          ) : kieu.rau === "ria" ? (
            <path d={`M ${dauC[0] - 30} ${dauC[1] + dauR * 0.34}
                      q 30 ${-14} 60 0 q ${-16} 16 ${-30} 16 q ${-14} 0 ${-30} ${-16} Z`}
                  fill={kieu.toc} stroke={net} strokeWidth={NET * 0.8} />
          ) : null}


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
