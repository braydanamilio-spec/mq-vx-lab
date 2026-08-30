import React from "react";
import { CAM_XUC, CU_CHI, TenCamXuc, TenCuChi, Kieu } from "../v2/DienVien";

/**
 * NHÂN VẬT QUE — bộ diễn viên thứ hai của mười kênh hài. (30/8/2026)
 *
 * VÌ SAO ĐỔI, VÀ ĐỔI CÓ ĐÁNG KHÔNG
 * ---------------------------------
 * Anh xem một phim ngắn nhân vật que rồi hỏi thẳng: *"nếu làm người kiểu stick thì cử chỉ tay
 * chân có linh động dễ khớp mượt mà hơn ko"*. Có, và không phải hơn một chút — nó gỡ cùng lúc
 * bốn thứ mà bộ nhân vật có khối lượng đã phải chống đỡ suốt cả tuần:
 *
 *   · **Tay bẻ được mọi góc.** Cánh tay hình ống có đường viền phải khớp với vai và với thân;
 *     xoay quá một biên độ là lộ mối nối, nên bảng cử chỉ cũ chỉ dám dùng những góc hẹp. Tay
 *     que là một đoạn thẳng có độ dày, xoay quanh khớp — không có gì để lộ.
 *   · **Tay đi qua trước thân được.** Bộ cũ phải cấm cử chỉ hướng ngang vì tay đè lên áo thì
 *     thấy rõ chỗ chồng hình. Que thì tay qua trước ngực là chuyện thường.
 *   · **Đồ cầm trên tay hợp phong cách trở lại.** Lỗi anh chỉ hai lần — vật màu cam-nâu không
 *     đọc ra là gì — đến từ chỗ đạo cụ vẽ bằng vài hình vector đơn giản trong khi nhân vật lại
 *     có khối và có màu; hai lối vẽ cãi nhau. Với nhân vật vẽ bằng nét, một cái cốc vẽ bằng nét
 *     là *đúng* lối.
 *   · **Mười kênh hết na ná nhau.** Bộ cũ phân biệt bằng màu áo, mà màu áo là thứ mắt nhận ra
 *     sau cùng. Que phân biệt bằng BÓNG DÁNG — tóc, mũ, kính, chiều cao, độ dày nét — thứ đọc
 *     được từ xa và ở cỡ nhỏ.
 *
 * Và một thứ nữa anh nêu riêng: *"tỉ lệ người với bối cảnh nên tỉ lệ phù hợp"*. Nhân vật vẽ
 * nửa vời (có khối, có màu, nhưng đơn giản) đứng trước một ảnh nền AI nhiều chi tiết thì hai
 * bên **cạnh tranh nhau mà không bên nào thắng**. Người vẽ bằng nét đen trên nền chi tiết là
 * tương phản có chủ đích: mắt biết ngay phải nhìn đâu.
 *
 * CÁI PHẢI ĐÁNH ĐỔI, GHI RA ĐỂ SAU NÀY KHỎI TRANH LUẬN LẠI
 * ---------------------------------------------------------
 * Mất hẳn "nét USA màu sắc" kiểu sitcom hoạt hình mà chính anh đặt ra lúc đầu. Đây là lựa chọn
 * có ý thức, đổi *bảng màu* lấy *chuyển động*. Và nó chỉ áp cho MƯỜI KÊNH HÀI: mười kênh dữ
 * liệu giữ nguyên `DienVien`, vì một chuyên gia phân tích vẽ bằng hình que thì mất đúng thứ
 * mà mười kênh ấy sống bằng — vẻ đáng tin.
 *
 * BẢNG TỈ LỆ
 * ----------
 * Chân chạm y = 0, người mọc lên theo chiều âm, cùng hệ với `DienVienHai` để `KichHai` không
 * phải đổi một con số nào.
 */

const kep = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const trn = (a: number, b: number, t: number) => a + (b - a) * kep(t);
const muot = (v: number) => v * v * (3 - 2 * v);
const rad = (d: number) => (d * Math.PI) / 180;

// Người que cao 420 như bộ cũ, nhưng chia lại: đầu nhỏ hơn (que không cần đầu to để dễ thương,
// nó dễ thương nhờ nét), thân dài hơn, chân dài hơn — vì chân que dài mới bước được rộng.
const R_DAU = 46;
const Y_CO = -336;              // đáy đầu / đỉnh cổ
const Y_VAI = -300;
const Y_HONG = -150;
const DAI_CANH = 78;            // vai→khuỷu và khuỷu→cổ tay
const DAI_DUI = 82;
const DAI_ONG = 72;

/** Điểm cuối của một đoạn quay `goc` độ (0 = xuống thẳng, dương = ra ngoài). */
const diem = (x: number, y: number, goc: number, dai: number): [number, number] =>
  [x + Math.sin(rad(goc)) * dai, y + Math.cos(rad(goc)) * dai];

export type PropsQue = {
  kieu: Kieu;
  camXuc: TenCamXuc;
  cuChi: TenCuChi;
  nhin: [number, number];
  noi: { w: number; h: number; tron: number };
  t: number;
  nhan?: number;
  dangNoi?: boolean;
  doVat?: string;
  kyHieu?: boolean;
  tuoiCanh?: number;
  giat?: number;
  nghieng?: number;
  buoc?: number;
  cuChiTruoc?: TenCuChi;
  doiCuChi?: number;
  x?: number; y?: number; scale?: number; lat?: boolean;
};

// ══ CỬ CHỈ CHO NGƯỜI QUE ═════════════════════════════════════════════════════════════════
// Bảng riêng, KHÔNG dùng lại bảng của bộ có khối. Bảng cũ được viết trong ràng buộc "đừng để
// tay đè lên thân, đừng vượt quá vai" — mọi con số của nó đều đã bị bóp lại vì lý do ấy. Chép
// sang đây thì người que thừa hưởng một dáng đứng gò bó mà nó không còn lý do nào để gò.
// Ở đây góc mở gấp rưỡi đến gấp đôi, và có những tư thế bộ cũ không vẽ nổi: hai tay giơ cao,
// tay chỉ thẳng sang ngang, tay ôm đầu.
const CU_CHI_QUE: Record<string, { vaiT: number; khuyuT: number; vaiP: number; khuyuP: number }> = {
  // ══ QUY ƯỚC GÓC — ĐỌC KỸ TRƯỚC KHI SỬA MỘT SỐ NÀO ═══════════════════════════════════
  // Mọi góc tính TỪ TRỤC HƯỚNG XUỐNG, và DƯƠNG là RA XA THÂN:
  //     0° = chi buông thẳng xuống · 90° = dang ngang · 160° = giơ cao quá đầu
  //
  // Bản đầu của bảng này chép quy ước từ `DienVienHai` (nơi 0° hướng lên) mà công thức `diem`
  // ở đây lại tính từ trục xuống. Kết quả dựng ra: **tay và chân mọc ngược lên trên**, thân
  // co lại còn một mẩu, nhân vật thành một cái đầu treo giữa mấy que chĩa lên.
  // Cái đáng ghi không phải phép trừ sai, mà là: một BẢNG SỐ chép sang hệ toạ độ khác thì
  // từng con số vẫn "hợp lý" khi đọc, và trình dịch không có cách nào biết. Chỉ dựng ra hình
  // rồi nhìn mới thấy. Nên quy ước phải viết ngay trên bảng, không nằm trong đầu người viết.
  // HAI ĐIỀU RÚT RA KHI SOI KHUNG DỰNG THẬT, và cả hai đổi mọi dòng bên dưới:
  //
  //  · **Hai cẳng tay gập vào cùng một góc thì bàn tay gặp nhau và khép thành một HÌNH THOI
  //    KÍN** — đo được ở "đếm" và "chống nạnh": bàn tay hai bên cùng rơi về x ≈ 0. Mắt đọc
  //    hình khép kín ấy như một vật thể, không như hai cánh tay. Nên mọi tư thế gập khuỷu đều
  //    phải để bàn tay dừng cách trục giữa ít nhất chừng hai mươi đơn vị.
  //  · **Đối xứng tuyệt đối đọc ra là máy.** Người thật không bao giờ đặt hai tay cùng một góc;
  //    luôn có một bên cao hơn, gập hơn. Bản đầu có năm tư thế đối xứng hoàn hảo, và đó là thứ
  //    làm nhân vật trông như hình vẽ trong sách hướng dẫn thể dục. Nay mọi tư thế lệch nhau
  //    ít nhất vài độ, kể cả những tư thế "về nguyên tắc" là đối xứng.
  nghi:       { vaiT: 13,  khuyuT: 7,   vaiP: 16,  khuyuP: 11 },
  chi:        { vaiT: 11,  khuyuT: 9,   vaiP: 128, khuyuP: 26 },   // một tay chỉ chếch lên
  chi_ngang:  { vaiT: 10,  khuyuT: 6,   vaiP: 96,  khuyuP: -4 },   // chỉ thẳng sang ngang
  mo_tay:     { vaiT: 71,  khuyuT: 26,  vaiP: 78,  khuyuP: 34 },   // dang rộng hai tay
  dem:        { vaiT: 34,  khuyuT: -58, vaiP: 46,  khuyuP: -46 },  // hai tay trước ngực, lệch tầng
  suy_nghi:   { vaiT: 13,  khuyuT: 5,   vaiP: 26,  khuyuP: -128 }, // một tay chống cằm
  nhun_vai:   { vaiT: 58,  khuyuT: 56,  vaiP: 65,  khuyuP: 64 },   // khuỷu gập, lòng bàn ngửa
  gio_len:    { vaiT: 148, khuyuT: 12,  vaiP: 156, khuyuP: 18 },   // HAI tay giơ quá đầu
  khoanh_tay: { vaiT: 40,  khuyuT: -66, vaiP: 34,  khuyuP: -60 },
  chong_nanh: { vaiT: 42,  khuyuT: -58, vaiP: 38,  khuyuP: -54 },  // bàn tay đặt lên hông
  ngan_ngam:  { vaiT: 9,   khuyuT: 3,   vaiP: 44,  khuyuP: -56 },  // một tay buông, một chống
  om_dau:     { vaiT: 134, khuyuT: -62, vaiP: 142, khuyuP: -68 },  // hai tay ôm đầu
};

/** Dao động treo: bộ phận nặng đi sau thân một nhịp. */
const treo = (pha: number, t: number, bien: number, nhanh: number) =>
  Math.sin(t * nhanh + pha) * bien;

// ══ ĐẦU: MẶT TRẮNG, VIỀN ĐEN, BA NÉT ═════════════════════════════════════════════════════
// Phim que sống bằng khuôn mặt, vì phần còn lại chỉ là mấy đoạn thẳng. Nên mặt được ba thứ và
// chỉ ba thứ: hai con mắt có mí, hai lông mày, một cái miệng. Thêm nữa là bắt đầu thành phim
// hoạt hình thường, mà thành phim hoạt hình thường thì mất luôn lý do chọn lối vẽ này.
const Mat: React.FC<{
  E: typeof CAM_XUC[TenCamXuc]; nhin: [number, number]; R: number; NET: number;
  giat: number; to: number;
}> = ({ E, nhin, R, NET, giat, to }) => {
  const dx = R * 0.42, dy = -R * 0.08;
  const rM = R * 0.158 * to * (1 + giat * 0.5);
  // Mí trên hạ xuống che con ngươi — đây là toàn bộ cách người que "nheo mắt", "buồn ngủ",
  // "nghi ngờ". Một cái mí là một đường cong; ba phần tư biểu cảm nằm ở nó.
  const mi = kep(E.mi + giat * -0.3, -0.3, 0.6);
  const nx = kep(nhin[0], -1, 1) * rM * 0.32, ny = kep(nhin[1], -1, 1) * rM * 0.3;
  return (
    <g>
      {[-1, 1].map((s) => (
        <g key={s}>
          <ellipse cx={s * dx} cy={dy} rx={rM} ry={rM * 1.12} fill="#FFFFFF"
                   stroke="#141414" strokeWidth={NET * 0.62} />
          <circle cx={s * dx + nx} cy={dy + ny} r={rM * 0.52} fill="#141414" />
          {mi > 0.02 ? (
            <path d={`M ${s * dx - rM * 1.06} ${dy - rM * 1.14}
                      L ${s * dx + rM * 1.06} ${dy - rM * 1.14}
                      L ${s * dx + rM * 1.06} ${dy - rM * 1.14 + rM * 2.3 * mi}
                      Q ${s * dx} ${dy - rM * 1.14 + rM * 2.3 * mi + rM * 0.4}
                        ${s * dx - rM * 1.06} ${dy - rM * 1.14 + rM * 2.3 * mi} Z`}
                  fill="#FFFFFF" stroke="none" />
          ) : null}
          {/* lông mày: một nét, độ nghiêng nói hết cảm xúc */}
          <line x1={s * dx - rM * 1.1} y1={dy - rM * 1.5 - E.mayCao * 1.4 + s * E.may * 0.12}
                x2={s * dx + rM * 1.1} y2={dy - rM * 1.5 - E.mayCao * 1.4 - s * E.may * 0.12}
                stroke="#141414" strokeWidth={NET * 0.78} strokeLinecap="round" />
        </g>
      ))}
    </g>
  );
};

const Mieng: React.FC<{ noi: PropsQue["noi"]; E: typeof CAM_XUC[TenCamXuc]; R: number; NET: number }> =
({ noi, E, R, NET }) => {
  const y = R * 0.42;
  const w = trn(R * 0.3, R * 0.62, kep(noi.w));
  const h = Math.max(R * 0.045, kep(noi.h) * R * 0.42);
  const cong = E.khoe * R * 0.16;
  // Miệng đóng là một đường cong (khoé lên = cười, khoé xuống = xị); miệng mở là một hình bầu
  // dục đen. Chuyển giữa hai dạng theo `noi.h` chứ không bật/tắt, nên không thấy chỗ nhảy.
  if (h < R * 0.1) {
    return <path d={`M ${-w / 2} ${y} Q 0 ${y + cong * 2} ${w / 2} ${y}`}
                 fill="none" stroke="#141414" strokeWidth={NET * 0.82} strokeLinecap="round" />;
  }
  return <ellipse cx={0} cy={y + h * 0.2} rx={w / 2} ry={h}
                  fill="#141414" stroke="#141414" strokeWidth={NET * 0.4} />;
};

// ══ DẤU NHẬN DẠNG — THỨ THAY CHO MÀU ÁO ══════════════════════════════════════════════════
// Mười kênh, hai mươi người, và tất cả đều là mấy đoạn thẳng đen. Nếu không có gì khác thì
// mười kênh ra một người — đúng lỗi anh đã nêu ở bộ cũ, chỉ nặng hơn.
// Nên mỗi người mang một tổ hợp: tóc · mũ · kính · râu · cà vạt · chiều cao · độ dày nét.
// Bảy trục nhị phân đã cho hơn trăm tổ hợp; hai mươi người thì thừa chỗ để không ai giống ai.
const Dau: React.FC<{ kieu: Kieu; R: number; NET: number; t: number }> = ({ kieu, R, NET, t }) => {
  const s = { fill: kieu.toc || "#141414", stroke: "#141414",
              strokeWidth: NET * 0.6, strokeLinejoin: "round" as const };
  const lac = treo(0, t, 0.1, 2.4);
  const k = kieu.kieuToc;
  return (
    <g transform={`rotate(${lac})`}>
      {k === "trocs" || k === "hoi" ? (
        <path d={`M ${-R} ${-R * 0.1} q 2 -${R * 0.42} ${R * 0.3} -${R * 0.5}
                  M ${R} ${-R * 0.1} q -2 -${R * 0.42} -${R * 0.3} -${R * 0.5}`}
              fill="none" stroke="#141414" strokeWidth={NET * 0.8} strokeLinecap="round" />
      ) : k === "duoi_ngua" ? (
        <>
          <path d={`M ${-R * 0.98} ${-R * 0.5} q ${R * 0.3} -${R * 0.94} ${R * 1.96} 0
                    q -${R * 0.5} -${R * 0.3} -${R * 0.98} -${R * 0.3}
                    q -${R * 0.5} 0 -${R * 0.98} ${R * 0.3} Z`} {...s} />
          <path d={`M ${R * 0.9} ${-R * 0.4} q ${R * 0.6} ${R * 0.2} ${R * 0.34} ${R * 0.96}
                    q -${R * 0.1} ${R * 0.2} -${R * 0.4} ${R * 0.08}
                    q ${R * 0.24} -${R * 0.4} ${R * 0.06} -${R * 1.04} Z`} {...s} />
        </>
      ) : k === "bui" || k === "bob" ? (
        <>
          <path d={`M ${-R * 1.02} ${-R * 0.44} q 0 -${R * 1.12} ${R * 1.02} -${R * 1.12}
                    q ${R * 1.02} 0 ${R * 1.02} ${R * 1.12}
                    q -${R * 0.4} -${R * 0.34} -${R * 1.02} -${R * 0.34}
                    q -${R * 0.62} 0 -${R * 1.02} ${R * 0.34} Z`} {...s} />
          <path d={`M ${-R * 1.02} ${-R * 0.24} q -${R * 0.1} ${R * 0.72} ${R * 0.16} ${R * 0.94}
                    q ${R * 0.1} -${R * 0.6} 0 -${R * 0.98} Z
                    M ${R * 1.02} ${-R * 0.24} q ${R * 0.1} ${R * 0.72} -${R * 0.16} ${R * 0.94}
                    q -${R * 0.1} -${R * 0.6} 0 -${R * 0.98} Z`} {...s} />
        </>
      ) : k === "xoan" || k === "roi" ? (
        <path d={`M ${-R * 1.0} ${-R * 0.5} q ${R * 0.06} -${R * 0.6} ${R * 0.36} -${R * 0.68}
                  q -${R * 0.06} -${R * 0.3} ${R * 0.22} -${R * 0.34}
                  q ${R * 0.1} -${R * 0.28} ${R * 0.44} -${R * 0.2}
                  q ${R * 0.3} -${R * 0.16} ${R * 0.5} ${R * 0.12}
                  q ${R * 0.34} -${R * 0.02} ${R * 0.34} ${R * 0.4}
                  q ${R * 0.2} ${R * 0.16} ${R * 0.12} ${R * 0.7}
                  q -${R * 0.5} -${R * 0.4} -${R * 1.0} -${R * 0.4}
                  q -${R * 0.5} 0 -${R * 0.98} ${R * 0.4} Z`} {...s} />
      ) : (
        // "ngan" và mọi kiểu còn lại: mảng tóc có ba chóp — dáng tóc nam cắt gọn
        <path d={`M ${-R * 1.0} ${-R * 0.46} q 0 -${R * 1.06} ${R * 1.0} -${R * 1.06}
                  q ${R * 1.0} 0 ${R * 1.0} ${R * 1.06}
                  l -${R * 0.24} -${R * 0.2} l -${R * 0.2} ${R * 0.16}
                  l -${R * 0.26} -${R * 0.22} l -${R * 0.24} ${R * 0.18}
                  l -${R * 0.26} -${R * 0.18} l -${R * 0.22} ${R * 0.16} Z`} {...s} />
      )}
      {kieu.mu === "luoi_trai" ? (
        <g>
          <path d={`M ${-R * 1.04} ${-R * 0.3} q 0 -${R * 0.96} ${R * 1.04} -${R * 0.96}
                    q ${R * 1.04} 0 ${R * 1.04} ${R * 0.96} Z`}
                fill={kieu.ao || "#2B2B2B"} stroke="#141414" strokeWidth={NET * 0.6} />
          <path d={`M ${R * 0.1} ${-R * 0.3} q ${R * 1.3} -${R * 0.08} ${R * 1.36} ${R * 0.26}
                    q -${R * 0.7} ${R * 0.16} -${R * 1.36} ${R * 0.02} Z`}
                fill={kieu.ao || "#2B2B2B"} stroke="#141414" strokeWidth={NET * 0.6} />
        </g>
      ) : null}
      {kieu.kinh ? (
        <g fill="none" stroke="#141414" strokeWidth={NET * 0.62}>
          <circle cx={-R * 0.42} cy={-R * 0.08} r={R * 0.3} />
          <circle cx={R * 0.42} cy={-R * 0.08} r={R * 0.3} />
          <line x1={-R * 0.12} y1={-R * 0.08} x2={R * 0.12} y2={-R * 0.08} />
        </g>
      ) : null}
      {kieu.rau === "ria" ? (
        <path d={`M ${-R * 0.3} ${R * 0.3} q ${R * 0.3} ${R * 0.14} ${R * 0.6} 0`}
              fill="none" stroke="#141414" strokeWidth={NET * 1.1} strokeLinecap="round" />
      ) : kieu.rau === "de" ? (
        <path d={`M ${-R * 0.16} ${R * 0.6} q ${R * 0.16} ${R * 0.3} ${R * 0.32} 0 Z`}
              fill="#141414" stroke="#141414" strokeWidth={NET * 0.5} />
      ) : kieu.rau === "quai" ? (
        <path d={`M ${-R * 0.78} ${R * 0.12} q ${R * 0.1} ${R * 0.82} ${R * 0.78} ${R * 0.84}
                  q ${R * 0.68} -${R * 0.02} ${R * 0.78} -${R * 0.84}
                  q -${R * 0.3} ${R * 0.42} -${R * 0.78} ${R * 0.42}
                  q -${R * 0.48} 0 -${R * 0.78} -${R * 0.42} Z`}
              fill="#141414" stroke="#141414" strokeWidth={NET * 0.5} />
      ) : null}
    </g>
  );
};

// ══ ĐỒ CẦM TAY — VẼ BẰNG NÉT, ĐÚNG LỐI CỦA NHÂN VẬT ══════════════════════════════════════
// Bộ cũ phải bỏ hẳn đạo cụ: vật vẽ bằng vài hình vector đặc, cầm trong bàn tay có khối, ở cỡ
// cận phóng to thành cục màu không đọc ra được là gì (anh chỉ hai lần).
// Ở đây vật cũng vẽ bằng nét đen như người, nên nó KHÔNG cãi nhau với nhân vật — cùng một
// ngôn ngữ hình. Đó là lý do đạo cụ quay lại được, chứ không phải vì tôi đổi ý.
const DoVatQue: React.FC<{ ten: string; NET: number }> = ({ ten, NET }) => {
  const s = { fill: "none", stroke: "#141414", strokeWidth: NET * 0.72,
              strokeLinejoin: "round" as const, strokeLinecap: "round" as const };
  switch (ten) {
    case "dien_thoai":
      return <g {...s}><rect x={-9} y={-17} width={18} height={34} rx={3} />
                       <line x1={-5} y1={13} x2={5} y2={13} /></g>;
    case "coc":
      return <g {...s}><path d="M -10 -12 L -8 14 L 8 14 L 10 -12 Z" />
                       <path d="M 10 -6 q 8 0 8 8 q 0 6 -7 6" /></g>;
    case "giay_to":
      return <g {...s}><rect x={-12} y={-16} width={24} height={32} rx={2} />
                       <line x1={-7} y1={-8} x2={7} y2={-8} />
                       <line x1={-7} y1={0} x2={7} y2={0} />
                       <line x1={-7} y1={8} x2={2} y2={8} /></g>;
    case "co_le":
      return <g {...s}><path d="M -3 16 L -3 -8 M 3 16 L 3 -8" />
                       <path d="M -7 -8 q -3 -9 7 -9 q 10 0 7 9 l -5 3 l -4 0 Z" /></g>;
    case "chai_nuoc":
      return <g {...s}><path d="M -7 -8 L -7 16 q 0 3 3 3 L 4 19 q 3 0 3 -3 L 7 -8 Z" />
                       <rect x={-4} y={-16} width={8} height={8} rx={2} /></g>;
    case "ve_may_bay":
      return <g {...s}><rect x={-14} y={-9} width={28} height={18} rx={2} />
                       <line x1={4} y1={-9} x2={4} y2={9} strokeDasharray="3 3" /></g>;
    case "banh":
      return <g {...s}><circle cx={0} cy={0} r={12} />
                       <path d="M -12 -2 q 12 -7 24 0" /></g>;
    case "ong_nhom":
      return <g {...s}><rect x={-15} y={-8} width={13} height={16} rx={3} />
                       <rect x={2} y={-8} width={13} height={16} rx={3} />
                       <line x1={-2} y1={0} x2={2} y2={0} /></g>;
    default:
      return null;
  }
};

// ══ KÝ HIỆU TRUYỆN TRANH ═════════════════════════════════════════════════════════════════
// Giữ nguyên luật đã trả giá ở bộ cũ: ký hiệu là một CHỚP đánh dấu khoảnh khắc, không phải phụ
// kiện đội đầu. Hiện 1,35 giây kể từ đầu lượt rồi tan.
const KyHieuQue: React.FC<{ camXuc: TenCamXuc; R: number; NET: number; tuoi: number }> =
({ camXuc, R, NET, tuoi }) => {
  const song = kep(tuoi / 0.18) * (1 - kep((tuoi - 1.0) / 0.35));
  if (song <= 0.02) return null;
  const s = { stroke: "#141414", strokeWidth: NET * 0.7, fill: "none",
              strokeLinecap: "round" as const, opacity: song };
  const yy = -R * 1.9;
  if (camXuc === "tuc") {
    return <g {...s} transform={`translate(${R * 0.9} ${yy})`}>
             <path d="M -8 -6 L 8 6 M 8 -6 L -8 6" /><path d="M -12 0 L 12 0" /></g>;
  }
  if (camXuc === "bat_ngo" || camXuc === "so") {
    return <text x={R * 0.95} y={yy + 6} fontSize={R * 0.86} fontWeight={900} fill="#141414"
                 opacity={song} textAnchor="middle">!</text>;
  }
  if (camXuc === "nghi_ngo") {
    return <text x={R * 0.95} y={yy + 6} fontSize={R * 0.86} fontWeight={900} fill="#141414"
                 opacity={song} textAnchor="middle">?</text>;
  }
  if (camXuc === "vui") {
    return <g {...s} transform={`translate(${R * 0.95} ${yy})`}>
             <path d="M 0 -9 L 0 9 M -9 0 L 9 0 M -6 -6 L 6 6 M 6 -6 L -6 6" /></g>;
  }
  return null;
};

export const DienVienQue: React.FC<PropsQue> = ({
  kieu, camXuc, cuChi, nhin, noi, t, nhan = 0, nghieng = 0, buoc = 0, giat = 0, dangNoi = true,
  cuChiTruoc, doiCuChi = 1, doVat = "", kyHieu = true, tuoiCanh = 0,
  x = 0, y = 0, scale = 1, lat = false,
}) => {
  const E = CAM_XUC[camXuc] || CAM_XUC.trung_tinh;
  const G1 = CU_CHI_QUE[cuChi as string] || CU_CHI_QUE.nghi;
  const G0 = CU_CHI_QUE[(cuChiTruoc || cuChi) as string] || G1;
  const q = muot(kep(doiCuChi));
  const G = {
    vaiT: trn(G0.vaiT, G1.vaiT, q), khuyuT: trn(G0.khuyuT, G1.khuyuT, q),
    vaiP: trn(G0.vaiP, G1.vaiP, q), khuyuP: trn(G0.khuyuP, G1.khuyuP, q),
  };

  const cao = kieu.cao ?? 1;
  const ngang = kieu.beNgang ?? 1;
  // ĐỘ DÀY NÉT LÀ MỘT TRỤC NHẬN DẠNG, không phải một hằng số trang trí. Người "đậm" trong bảng
  // cũ được vẽ bè ra; người que không bè được, nên nó được nét dày hơn — mắt đọc ra "chắc
  // chắn, nặng nề" y hệt, mà không phải bóp méo hình.
  const NET = 7.2 * (0.86 + ngang * 0.3);
  const R = R_DAU * (kieu.tiLeDau ?? 1) * (0.94 + ngang * 0.08);

  // Nhịp thở + nhún nhẹ. Người đang nghe vẫn phải sống, chỉ là sống ít hơn — `dien` là toàn bộ
  // ngân sách chuyển động của người này trong lượt hiện tại.
  const dien = dangNoi ? 1 : 0.24;
  const tho = Math.sin(t * 1.65) * 2.6 * dien;
  const nhun = Math.sin(t * 1.65 + 0.5) * 1.8 * dien;

  // Bước chân: hai chân đá lệch pha. Người que bước được vì chân là hai đoạn thẳng — không có
  // ống quần nào phải gấp cho khớp.
  const nhipB = buoc > 0 ? Math.sin(t * 7.4) : 0;
  // Đứng yên: hai chân hơi dạng ra (không song song — chân song song đọc ra là tượng gỗ).
  // Đang bước: hai chân đá lệch pha quanh tư thế đứng ấy.
  const dui = { T: (buoc > 0 ? nhipB * 26 : 0) - 7 - tho * 0.3,
                P: (buoc > 0 ? -nhipB * 26 : 0) + 7 + tho * 0.3 };

  const yCo = (Y_CO + tho) * cao;
  const yVai = (Y_VAI + tho) * cao;
  const yHong = (Y_HONG + nhun) * cao;
  const nga = nghieng * 0.5 + E.than * 0.4 + giat * -5;

  const vaiX = 2 + ngang * 3;
  // Tay trái mang góc ÂM (ra xa thân về bên trái), tay phải mang góc dương. Góc cẳng tay cộng
  // dồn lên góc cánh tay — khuỷu là một khớp nối tiếp, không phải một hướng độc lập.
  const [khuyuTx, khuyuTy] = diem(-vaiX, yVai, -G.vaiT, DAI_CANH * cao);
  const [tayTx, tayTy] = diem(khuyuTx, khuyuTy, -(G.vaiT + G.khuyuT), DAI_CANH * cao);
  const [khuyuPx, khuyuPy] = diem(vaiX, yVai, G.vaiP, DAI_CANH * cao);
  const [tayPx, tayPy] = diem(khuyuPx, khuyuPy, G.vaiP + G.khuyuP, DAI_CANH * cao);

  const [goiTx, goiTy] = diem(-vaiX * 0.7, yHong, dui.T, DAI_DUI * cao);
  const [chanTx, chanTy] = diem(goiTx, goiTy, dui.T * 0.35, DAI_ONG * cao);
  const [goiPx, goiPy] = diem(vaiX * 0.7, yHong, dui.P, DAI_DUI * cao);
  const [chanPx, chanPy] = diem(goiPx, goiPy, dui.P * 0.35, DAI_ONG * cao);

  const net = { stroke: "#141414", strokeWidth: NET, strokeLinecap: "round" as const,
                strokeLinejoin: "round" as const, fill: "none" };

  return (
    <g transform={`translate(${x} ${y}) scale(${(lat ? -scale : scale)} ${scale})`}>
      <g transform={`rotate(${nga} 0 ${yHong})`}>
        {/* CHÂN — vẽ trước để thân đè lên khớp hông, giấu chỗ nối */}
        <path d={`M ${-vaiX * 0.7} ${yHong} L ${goiTx} ${goiTy} L ${chanTx} ${chanTy}`} {...net} />
        <path d={`M ${vaiX * 0.7} ${yHong} L ${goiPx} ${goiPy} L ${chanPx} ${chanPy}`} {...net} />
        <path d={`M ${chanTx - 15} ${chanTy} L ${chanTx + 9} ${chanTy}`} {...net} />
        <path d={`M ${chanPx - 9} ${chanPy} L ${chanPx + 15} ${chanPy}`} {...net} />

        {/* THÂN — một đường, hơi cong theo độ ngả. Cong chứ không thẳng đơ: một đường thẳng
            tuyệt đối đọc ra là cái que cắm, còn hơi cong thì đọc ra là cột sống. */}
        <path d={`M 0 ${yCo} Q ${nga * 0.7} ${(yCo + yHong) / 2} 0 ${yHong}`} {...net} />

        {/* TAY */}
        <path d={`M ${-vaiX} ${yVai} L ${khuyuTx} ${khuyuTy} L ${tayTx} ${tayTy}`} {...net} />
        <path d={`M ${vaiX} ${yVai} L ${khuyuPx} ${khuyuPy} L ${tayPx} ${tayPy}`} {...net} />
        <circle cx={tayTx} cy={tayTy} r={NET * 0.62} fill="#141414" />
        <circle cx={tayPx} cy={tayPy} r={NET * 0.62} fill="#141414" />
        {doVat ? (
          <g transform={`translate(${tayPx} ${tayPy}) scale(${lat ? -1 : 1} 1)`}>
            <DoVatQue ten={doVat} NET={NET} />
          </g>
        ) : null}

        {/* CÀ VẠT — một dấu nhận dạng rẻ mà đọc được ngay ở cỡ nhỏ */}
        {kieu.caVat ? (
          <path d={`M -6 ${yCo + 6} L 6 ${yCo + 6} L 3 ${yCo + 20} L 0 ${yCo + 46}
                    L -3 ${yCo + 20} Z`}
                fill={kieu.caVat} stroke="#141414" strokeWidth={NET * 0.5} strokeLinejoin="round" />
        ) : null}

        {/* ĐẦU */}
        <g transform={`translate(0 ${yCo - R}) rotate(${E.nghieng * 0.5 + giat * -4})`}>
          <circle cx={0} cy={0} r={R} fill="#FFFFFF" stroke="#141414" strokeWidth={NET * 0.9} />
          <Dau kieu={kieu} R={R} NET={NET} t={t} />
          <Mat E={E} nhin={nhin} R={R} NET={NET} giat={giat}
               to={(kieu.matTo ?? 1) * (1 + nhan * 0.08)} />
          <Mieng noi={noi} E={E} R={R} NET={NET} />
          {kyHieu ? <KyHieuQue camXuc={camXuc} R={R} NET={NET} tuoi={tuoiCanh} /> : null}
        </g>
      </g>
    </g>
  );
};
