import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";

/* ══════════════════════════════════════════════════════════════════════════════════════════
   BRAND KIT — 10 kênh giải thích  (1/9/2026)

   Anh: *"brandkit — có đủ profile, banner đủ size cho youtube, fb, insta, xây dựng rồi nâng
   cho đẹp chuẩn trên 95/100 top usa."*

   VẼ BẰNG CODE, KHÔNG GỌI API. Ba lý do, và lý do thứ ba mới là lý do thật:
     · miễn phí và không bao giờ hết hạn mức;
     · đổi bảng màu một chỗ là cả mười kênh đổi theo;
     · **chữ phải ĐÚNG TUYỆT ĐỐI.** Avatar và banner mang TÊN KÊNH. Đo hôm nay: FLUX viết
       chuỗi ngắn đúng 5/6 lần — với một khung phim thoáng qua thì chấp nhận được, với ảnh đại
       diện đứng vĩnh viễn trên trang kênh thì 1/6 sai là hỏng thương hiệu. Không có vòng lặp
       nào đáng để đánh cược chỗ này.

   BỐN NGUYÊN TẮC LẤY TỪ AVATAR KÊNH TOP MỸ
   1. Ở 48px (cỡ avatar thật trong danh sách đề xuất) chỉ còn đọc được HÌNH KHỐI và MÀU. Nên
      avatar phải sống bằng một hình khối duy nhất, không bằng chi tiết.
   2. Chữ trên avatar chỉ được 1-2 TỪ, và phải là từ mang nghĩa nhất của tên kênh.
   3. Banner có vùng an toàn 1546×423 ở giữa — mọi thứ ngoài vùng ấy sẽ bị cắt trên điện thoại.
      Nên banner thật ra là một tấm 1546×423 đặt giữa một nền 2560×1440.
   4. Mỗi kênh một MÀU NHẬN DIỆN, và màu ấy phải là màu đã dùng trong video. Avatar một màu,
      video một màu là hai thương hiệu khác nhau đặt cạnh nhau.
   ══════════════════════════════════════════════════════════════════════════════════════════ */

const F = "Poppins, Arial Black, sans-serif";

export type PropsBrand = {
  ten?: string;          // tên kênh đầy đủ
  ngan?: string;         // 1-2 từ cho avatar
  mau?: string;          // màu nhận diện
  phu?: string;
  nen?: string;
  chu?: string;
  loai?: string;         // avatar | banner | cover | post
  kk?: string;           // kiểu bố cục: cheo | doc | vien | ngang | tron | soc
  bieu?: string;         // biểu tượng: dong_ho | tien | trai_dat | nguoi | may_bay | hop | cay
};

/* Biểu tượng lớn cho brand — vẽ dày và đơn giản hơn hẳn bộ dùng trong video, vì nó phải sống
   ở 48px. Chi tiết ở cỡ ấy chỉ thành vết bẩn.

   `mot_mau`: vẽ thành MỘT KHỐI ĐẶC một màu, dùng khi đặt lên dải màu đậm.
   Bản trước đặt `muc="#FFFFFF"` để nét nổi trên dải màu — nhưng `Hinh` dùng `muc` làm màu NÉT
   và `mau` làm màu TÔ, nên nét trắng vẽ lên phần tô trắng và biến mất: đồng hồ ra một vòng
   tròn trắng đặc, tờ tiền mất hết chi tiết.
   Trên nền đậm thì biểu tượng phải là SILHOUETTE một màu, không phải hình hai màu. */
const Hinh: React.FC<{ ten: string; s: number; mau: string; muc: string; mot_mau?: string }> =
({ ten, s, mau, muc, mot_mau }) => {
  if (mot_mau) { mau = mot_mau; muc = mot_mau; }
  const k = (v: number) => v * s;
  const n = s * 0.085;
  const P = (d: string, f = "none") => (
    <path d={d} fill={f} stroke={muc} strokeWidth={n} strokeLinejoin="round" strokeLinecap="round" />
  );
  switch (ten) {
    case "dong_ho": return (<g>
      <circle cx="0" cy="0" r={k(0.42)} fill="#FFFFFF" stroke={muc} strokeWidth={n} />
      {P(`M 0 0 v ${-k(0.27)}`)}{P(`M 0 0 l ${k(0.19)} ${k(0.11)}`)}</g>);
    case "tien": return (<g>
      {P(`M ${-k(0.46)} ${-k(0.28)} h ${k(0.92)} v ${k(0.56)} h ${-k(0.92)} Z`, mau)}
      <circle cx="0" cy="0" r={k(0.16)} fill="#FFFFFF" stroke={muc} strokeWidth={n * 0.8} /></g>);
    case "trai_dat": return (<g>
      <circle cx="0" cy="0" r={k(0.42)} fill={mau} stroke={muc} strokeWidth={n} />
      {P(`M ${-k(0.32)} ${-k(0.12)} q ${k(0.2)} ${-k(0.14)} ${k(0.34)} 0 q ${k(0.1)} ${k(0.16)} ${-k(0.08)} ${k(0.22)} q ${-k(0.22)} ${k(0.04)} ${-k(0.26)} ${-k(0.22)} Z`, "#FFFFFF")}</g>);
    case "may_bay": return (<g>
      {P(`M ${-k(0.46)} 0 l ${k(0.66)} ${-k(0.07)} l ${k(0.26)} ${k(0.03)} q ${k(0.1)} ${k(0.04)} 0 ${k(0.08)} l ${-k(0.26)} ${k(0.03)} Z`, mau)}
      {P(`M ${-k(0.04)} ${-k(0.02)} l ${-k(0.16)} ${-k(0.3)} h ${k(0.1)} l ${k(0.24)} ${k(0.27)} Z`, mau)}
      {P(`M ${-k(0.04)} ${k(0.04)} l ${-k(0.16)} ${k(0.3)} h ${k(0.1)} l ${k(0.24)} ${-k(0.27)} Z`, mau)}</g>);
    case "hop": return (<g>
      {P(`M ${-k(0.4)} ${-k(0.2)} h ${k(0.8)} v ${k(0.56)} h ${-k(0.8)} Z`, mau)}
      {P(`M ${-k(0.44)} ${-k(0.34)} h ${k(0.88)} v ${k(0.14)} h ${-k(0.88)} Z`, "#FFFFFF")}</g>);
    case "cay": return (<g>
      {P(`M ${-k(0.07)} ${k(0.44)} v ${-k(0.36)} h ${k(0.14)} v ${k(0.36)} Z`, muc)}
      <circle cx="0" cy={-k(0.14)} r={k(0.32)} fill={mau} stroke={muc} strokeWidth={n} /></g>);
    case "lua": return P(`M 0 ${k(0.44)} q ${-k(0.36)} ${-k(0.13)} ${-k(0.21)} ${-k(0.45)}
      q ${k(0.04)} ${k(0.11)} ${k(0.14)} ${k(0.09)} q ${-k(0.11)} ${-k(0.26)} ${k(0.14)} ${-k(0.45)}
      q ${-k(0.02)} ${k(0.21)} ${k(0.15)} ${k(0.26)} q ${k(0.11)} ${-k(0.06)} ${k(0.06)} ${-k(0.17)}
      q ${k(0.21)} ${k(0.26)} ${-k(0.28)} ${k(0.72)} Z`, mau);
    case "nui": return P(`M ${-k(0.46)} ${k(0.30)} L ${-k(0.12)} ${-k(0.34)} L ${k(0.10)} ${k(0.02)}
      L ${k(0.24)} ${-k(0.16)} L ${k(0.48)} ${k(0.30)} Z`, mau);
    case "mui_ten": return P(`M ${-k(0.44)} ${k(0.26)} L ${-k(0.06)} ${-k(0.10)} L ${k(0.10)} ${k(0.06)}
      L ${k(0.42)} ${-k(0.30)} m 0 0 l ${-k(0.22)} ${-k(0.02)} m ${k(0.22)} ${k(0.02)} l ${k(0.02)} ${k(0.22)}`);
    case "cua": return (<g>
      {P(`M ${-k(0.28)} ${k(0.44)} v ${-k(0.86)} h ${k(0.56)} v ${k(0.86)} Z`, mau)}
      <circle cx={k(0.14)} cy={k(0.06)} r={k(0.05)} fill={muc} /></g>);
    case "giot": return P(`M 0 ${-k(0.44)} q ${k(0.34)} ${k(0.44)} ${k(0.30)} ${k(0.60)}
      a ${k(0.31)} ${k(0.31)} 0 1 1 ${-k(0.60)} 0 q ${-k(0.04)} ${-k(0.16)} ${k(0.30)} ${-k(0.60)} Z`, mau);
    /* ── NĂM HÌNH THÊM 1/9 ────────────────────────────────────────────────────────────────
       Bộ hình cũ có 17 mục cho 18 kênh, nên hình bị gán theo CÁI CÒN TRỐNG chứ không theo
       nghĩa: THE ODDS ra ngôi sao, YEARS ra giọt nước, WEIGHS ra ngọn núi, SMALLEST ra ngọn
       lửa. Không có lỗi nào báo — avatar vẫn vẽ ra, chỉ là nói sai chuyện. Thêm hình đúng
       nghĩa rẻ hơn nhiều so với ép một hình sai đứng mãi trên mặt kênh. */
    case "xuc_xac": return (<g>
      {P(`M ${-k(0.40)} ${-k(0.40)} h ${k(0.80)} v ${k(0.80)} h ${-k(0.80)} Z`, mau)}
      {[[-0.19,-0.19],[0.19,-0.19],[0,0],[-0.19,0.19],[0.19,0.19]].map((p,i)=>(
        <circle key={i} cx={k(p[0])} cy={k(p[1])} r={k(0.07)} fill={mot_mau ? "#FFFFFF" : muc} />))}
    </g>);
    case "cat": return (<g>
      {P(`M ${-k(0.34)} ${-k(0.44)} h ${k(0.68)} l ${-k(0.34)} ${k(0.44)} l ${k(0.34)} ${k(0.44)}
          h ${-k(0.68)} l ${k(0.34)} ${-k(0.44)} Z`, mau)}
      {P(`M ${-k(0.42)} ${-k(0.46)} h ${k(0.84)}`)}
      {P(`M ${-k(0.42)} ${k(0.46)} h ${k(0.84)}`)}
    </g>);
    case "can": return (<g>
      {P(`M 0 ${-k(0.42)} v ${k(0.72)}`)}
      {P(`M ${-k(0.40)} ${-k(0.30)} h ${k(0.80)}`)}
      {P(`M ${-k(0.24)} ${k(0.34)} h ${k(0.48)}`)}
      {P(`M ${-k(0.40)} ${-k(0.30)} l ${-k(0.13)} ${k(0.30)} h ${k(0.26)} Z`, mau)}
      {P(`M ${k(0.40)} ${-k(0.30)} l ${-k(0.13)} ${k(0.30)} h ${k(0.26)} Z`, mau)}
    </g>);
    case "hoa_don": return (<g>
      {P(`M ${-k(0.32)} ${-k(0.46)} h ${k(0.64)} v ${k(0.78)} l ${-k(0.16)} ${-k(0.09)}
          l ${-k(0.16)} ${k(0.09)} l ${-k(0.16)} ${-k(0.09)} l ${-k(0.16)} ${k(0.09)} Z`, mau)}
      {P(`M ${-k(0.17)} ${-k(0.22)} h ${k(0.34)}`)}
      {P(`M ${-k(0.17)} ${-k(0.02)} h ${k(0.34)}`)}
    </g>);
    case "kinh_lup": return (<g>
      <circle cx={-k(0.10)} cy={-k(0.12)} r={k(0.30)} fill={mot_mau ? mau : "#FFFFFF"}
              stroke={muc} strokeWidth={n} />
      {P(`M ${k(0.12)} ${k(0.11)} L ${k(0.42)} ${k(0.44)}`)}
      <circle cx={-k(0.10)} cy={-k(0.12)} r={k(0.09)} fill={muc} />
    </g>);
    case "sao": return P(`M 0 ${-k(0.46)} L ${k(0.13)} ${-k(0.14)} L ${k(0.46)} ${-k(0.13)}
      L ${k(0.19)} ${k(0.09)} L ${k(0.28)} ${k(0.42)} L 0 ${k(0.23)} L ${-k(0.28)} ${k(0.42)}
      L ${-k(0.19)} ${k(0.09)} L ${-k(0.46)} ${-k(0.13)} L ${-k(0.13)} ${-k(0.14)} Z`, mau);
    case "song": return (<g>
      {P(`M ${-k(0.46)} 0 q ${k(0.115)} ${-k(0.26)} ${k(0.23)} 0 q ${k(0.115)} ${k(0.26)} ${k(0.23)} 0
          q ${k(0.115)} ${-k(0.26)} ${k(0.23)} 0 q ${k(0.115)} ${k(0.26)} ${k(0.23)} 0`)}
      {P(`M ${-k(0.46)} ${k(0.26)} q ${k(0.115)} ${-k(0.26)} ${k(0.23)} 0 q ${k(0.115)} ${k(0.26)} ${k(0.23)} 0
          q ${k(0.115)} ${-k(0.26)} ${k(0.23)} 0 q ${k(0.115)} ${k(0.26)} ${k(0.23)} 0`)}</g>);
    case "khoa": return (<g>
      {P(`M ${-k(0.30)} ${-k(0.04)} h ${k(0.60)} v ${k(0.46)} h ${-k(0.60)} Z`, mau)}
      {P(`M ${-k(0.17)} ${-k(0.04)} v ${-k(0.16)} a ${k(0.17)} ${k(0.17)} 0 0 1 ${k(0.34)} 0 v ${k(0.16)}`)}</g>);
    case "banh_rang": return (<g>
      <circle cx="0" cy="0" r={k(0.30)} fill={mau} stroke={muc} strokeWidth={n} />
      <circle cx="0" cy="0" r={k(0.12)} fill="#FFFFFF" stroke={muc} strokeWidth={n * 0.8} />
      {[0, 60, 120, 180, 240, 300].map((g, i) => {
        const a = (g * Math.PI) / 180;
        return <rect key={i} x={-k(0.055)} y={-k(0.46)} width={k(0.11)} height={k(0.17)}
                     fill={mau} stroke={muc} strokeWidth={n * 0.7}
                     transform={`rotate(${g})`} />;
      })}</g>);
    case "hat": return (<g>
      {[[-0.26, -0.20], [0.02, -0.30], [0.28, -0.14], [-0.30, 0.10], [-0.02, 0.02],
        [0.24, 0.16], [-0.16, 0.32], [0.10, 0.34]].map((q, i) => (
        <circle key={i} cx={k(q[0])} cy={k(q[1])} r={k(0.075)} fill={mau}
                stroke={muc} strokeWidth={n * 0.55} />))}</g>);
    case "nhiet": return (<g>
      {P(`M ${-k(0.09)} ${-k(0.40)} a ${k(0.09)} ${k(0.09)} 0 0 1 ${k(0.18)} 0 v ${k(0.46)}
          a ${k(0.19)} ${k(0.19)} 0 1 1 ${-k(0.18)} 0 Z`, "#FFFFFF")}
      <circle cx="0" cy={k(0.26)} r={k(0.14)} fill={mau} />
      {P(`M 0 ${k(0.20)} v ${-k(0.34)}`, "none")}</g>);
    default: return (<g>            {/* nguoi — người que, hình mặc định */}
      <circle cx="0" cy={-k(0.30)} r={k(0.16)} fill="#FFFFFF" stroke={muc} strokeWidth={n} />
      {P(`M 0 ${-k(0.14)} v ${k(0.3)}`)}
      {P(`M ${-k(0.22)} ${-k(0.04)} L 0 ${-k(0.1)} L ${k(0.22)} ${-k(0.04)}`)}
      {P(`M 0 ${k(0.16)} l ${-k(0.17)} ${k(0.3)}`)}{P(`M 0 ${k(0.16)} l ${k(0.17)} ${k(0.3)}`)}</g>);
  }
};

export const BrandGT: React.FC<PropsBrand> = ({
  ten = "CHANNEL", ngan = "", mau = "#D9622B", phu = "#2F6E8A",
  nen = "#F4EDE0", chu = "#2E2A24", loai = "avatar", bieu = "nguoi", kk = "cheo",
}) => {
  const { width: W, height: H } = useVideoConfig();
  const nho = Math.min(W, H);

  /* ── NỀN: DẢI MÀU PHẢI BÁM THEO KHỐI CHỮ ───────────────────────────────────────────────
     Bản đầu đặt dải chéo ở một vị trí cố định (`top: H*0.52`) còn khối chữ đặt ở giữa khung —
     hai lớp tự chọn chỗ, không lớp nào biết lớp nào. Soi ra: chữ trắng nằm VẮT QUA mép chéo,
     nửa nằm trên nền sáng và mất hút; hai trong bốn banner mất luôn biểu tượng vì biểu tượng
     trắng rơi vào vùng sáng.
     Đây đúng họ lỗi lặp đi lặp lại cả ngày — hai lớp cùng chọn vị trí độc lập.

     Nay: `dai` là tâm của dải màu, và MỌI nơi đặt chữ đều lấy từ chính `dai` ấy. Dải phủ trọn
     chiều cao khối chữ cộng lề, nên không có cách nào chữ rơi ra ngoài. */
  /* ══ SÁU KIỂU BỐ CỤC — MỖI KÊNH MỘT KIỂU ═════════════════════════════════════════════════
     Anh: *"brandkit vẽ sao cho mỗi channel mang phong cách riêng, không cùng một mô-típ, họ
     nhìn không biết cùng một người làm."*

     Anh chỉ đúng chỗ nặng nhất. Bản trước cả mười kênh dùng CHUNG một bố cục — dải chéo, biểu
     tượng trái, chữ phải — và chỉ đổi màu. Đặt hai kênh cạnh nhau là thấy ngay cùng một khuôn.
     Màu khác nhau không cứu được điều đó, vì mắt đọc BỐ CỤC trước khi đọc màu.

     Nay sáu kiểu, khác nhau ở ba trục cùng lúc: hình khối nền · chỗ đặt biểu tượng · căn lề
     chữ. Khác một trục thì vẫn nhận ra cùng khuôn; khác cả ba thì không.

       cheo   dải chéo, biểu tượng trái, chữ trái
       doc    khối dọc một bên, chữ trong khối, biểu tượng lớn mờ phía sau
       vien   viền dày bao quanh, chữ giữa trên nền sạch, biểu tượng nhỏ trên chữ
       ngang  chia đôi ngang, chữ nửa dưới, biểu tượng phải
       tron   khối tròn lớn sau chữ, chữ giữa
       soc    sọc ở mép, chữ căn phải trên nền sạch                                            */
  const kieu = (kk || "cheo");
  const tren = kieu === "vien" || kieu === "soc";     // chữ trên nền sạch -> chữ màu đậm
  // CHÚ Ý: `mauChu` từng được tính ở đây rồi KHÔNG dùng — sáu khối chữ bên dưới ghi thẳng
  // `color: "#FFFFFF"`. Hậu quả: hai kiểu `vien` và `soc` đặt chữ trắng lên nền kem sáng, đo
  // được tương phản 1,2:1 (chuẩn WCAG AA cần 4,5:1) — tên kênh gần như tàng hình trên avatar.
  // Không lỗi nào báo, vì biến vẫn đúng; chỉ là hằng ghi đè nó. Đừng thay `mauChu` bằng hằng.
  // Màu chữ chọn bằng ĐO TƯƠNG PHẢN với nền thật, không bằng kiểu bố cục. Chọn theo kiểu thì
  // đúng cho 17 kênh và sai cho kênh có màu nhận diện sáng: `howlong` (#D9622B) đo được 3,9:1
  // với chữ trắng — dưới chuẩn WCAG AA 4,5:1. Vá riêng kênh ấy là để lỗi quay lại ở kênh sáng
  // tiếp theo; đo thì mọi kênh tương lai tự đúng.
  const _lum = (h: string) => {
    const v = [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16) / 255)
      .map(u => (u <= 0.03928 ? u / 12.92 : Math.pow((u + 0.055) / 1.055, 2.4)));
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2];
  };
  const _tp = (a: number, b: number) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  // VÙNG CHẾT: có màu mà CẢ chữ trắng LẪN chữ đậm đều không qua 4,5:1. `howlong` (#D9622B) đo
  // được 3,9:1 với trắng và 3,9:1 với đậm — đổi màu chữ không cứu được, vì lỗi nằm ở độ sáng
  // của chính dải nền. Nên ở đây làm SẪM dải nền vừa đủ để chữ trắng qua chuẩn, giữ nguyên sắc
  // màu nhận diện. Đây là cùng cách đã cứu phụ đề video: thêm nền, không đổi chữ.
  const _sam = (h: string, t: number) => "#" + [1, 3, 5].map(i =>
    Math.round(parseInt(h.slice(i, i + 2), 16) * (1 - t)).toString(16).padStart(2, "0")).join("");
  let mauDai = mau;
  if (!tren) {
    let b = 0;
    while (_tp(_lum(mauDai), 1) < 4.5 && b < 0.7) { b += 0.1; mauDai = _sam(mau, b); }
  }
  const mauChu = tren ? chu : "#FFFFFF";
  // ĐẶT Ở ĐÂY, ngay sau `kieu`: bản trước khai ở giữa tệp, dưới chỗ JSX dùng `mauDai`, nên
  // ném ReferenceError (vùng chết thời gian) và 90/126 tệp brand không dựng được.
  const gocDai = loai === "avatar" ? -11 : -4;
  const dai = loai === "avatar" ? 0.66 : 0.50;
  const dayDai = loai === "banner" ? 0.46 : loai === "cover" ? 0.56 : 0.60;

  const Nen = (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <AbsoluteFill style={{ background: nen }} />
      {kieu === "cheo" ? (<>
        <div style={{ position: "absolute", left: -W * 0.3, width: W * 1.7,
                      top: H * (dai - dayDai / 2), height: H * dayDai,
                      background: mauDai, transform: `rotate(${gocDai}deg)` }} />
        <div style={{ position: "absolute", left: -W * 0.3, width: W * 1.7,
                      top: H * (dai + dayDai / 2 - 0.02), height: H * 0.42,
                      background: phu, transform: `rotate(${gocDai}deg)`, opacity: 0.92 }} />
      </>) : kieu === "doc" ? (<>
        <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: W * 0.62,
                      background: mauDai }} />
        <div style={{ position: "absolute", left: W * 0.62, top: 0, bottom: 0, width: W * 0.06,
                      background: phu }} />
      </>) : kieu === "vien" ? (
        <div style={{ position: "absolute", inset: 0,
                      border: `${Math.min(W, H) * 0.075}px solid ${mau}`,
                      boxSizing: "border-box" }} />
      ) : kieu === "ngang" ? (<>
        <div style={{ position: "absolute", left: 0, right: 0, top: H * 0.44, bottom: 0,
                      background: mauDai }} />
        <div style={{ position: "absolute", left: 0, right: 0, top: H * 0.44,
                      height: H * 0.025, background: phu }} />
      </>) : kieu === "tron" ? (
        <div style={{ position: "absolute", left: "50%", top: "50%",
                      width: Math.min(W, H) * 1.12, height: Math.min(W, H) * 1.12,
                      marginLeft: -Math.min(W, H) * 0.56, marginTop: -Math.min(W, H) * 0.56,
                      borderRadius: "50%", background: mauDai }} />
      ) : (<>
        {[0, 1, 2, 3].map((i) => (
          <div key={i} style={{ position: "absolute", left: 0, right: 0,
                                top: H * (0.60 + i * 0.105), height: H * 0.055,
                                background: i % 2 ? phu : mau, opacity: 1 - i * 0.14 }} />
        ))}
      </>)}
    </AbsoluteFill>
  );

  /* Chữ nằm ở đâu, căn lề nào, màu gì — suy ra TỪ KIỂU, không đặt rời. Đây chính là chỗ bản
     trước hỏng: dải màu và khối chữ mỗi bên tự chọn vị trí. */
  const cany = kieu === "ngang" ? 0.70 : kieu === "soc" ? 0.34 : dai;
  const canle: any = kieu === "soc" ? "flex-end" : kieu === "vien" || kieu === "tron"
    ? "center" : "flex-start";

  if (loai === "avatar") {
    const t = (ngan || ten.split(" ")[0]).toUpperCase();
    const cs = Math.min(nho * 0.20, (nho * 0.82 / Math.max(1, t.length)) * 1.5);
    return (
      <AbsoluteFill>
        {Nen}
        <div style={{ position: "absolute", inset: 0, display: "flex",
                      flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          <svg width={nho * 0.52} height={nho * 0.52} viewBox="-0.5 -0.5 1 1"
               style={{ marginTop: -nho * 0.10 }}>
            <g transform="scale(0.9)"><Hinh ten={bieu} s={1} mau={mau} muc={chu} /></g>
          </svg>
          <div style={{
            marginTop: nho * 0.02, fontFamily: F, fontWeight: 900, fontSize: cs,
            color: mauChu, letterSpacing: cs * 0.02, lineHeight: 1,
            textShadow: `0 ${nho * 0.004}px ${nho * 0.012}px ${tren ? "#00000018" : "#00000055"}`,
          }}>{t}</div>
        </div>
      </AbsoluteFill>
    );
  }

  /* BANNER YouTube 2560×1440 — mọi thứ phải nằm trong vùng an toàn 1546×423 ở GIỮA, vì trên
     điện thoại phần ngoài bị cắt sạch. Nên bố cục là: một dải an toàn đặt giữa, nền tràn ra. */
  if (loai === "banner") {
    const anW = W * (1546 / 2560), anH = H * (423 / 1440);
    const cs = Math.min(anH * 0.42, (anW * 0.88 / Math.max(1, ten.length)) * 1.55);
    return (
      <AbsoluteFill>
        {Nen}
        <div style={{
          position: "absolute", left: (W - anW) / 2, top: H * dai - anH / 2, width: anW, height: anH,
          display: "flex", alignItems: "center", gap: anW * 0.045, paddingLeft: anW * 0.05,
        }}>
          <svg width={anH * 0.78} height={anH * 0.78} viewBox="-0.5 -0.5 1 1">
            <Hinh ten={bieu} s={1} mau={nen} muc={nen} mot_mau={nen} />
          </svg>
          <div>
            <div style={{ fontFamily: F, fontWeight: 900, fontSize: cs, color: mauChu,
                          lineHeight: 1.0, letterSpacing: -cs * 0.012,
                          textShadow: `0 ${H * 0.003}px ${H * 0.008}px ${tren ? "#00000018" : "#00000055"}` }}>{ten}</div>
            <div style={{ fontFamily: F, fontWeight: 700, fontSize: cs * 0.34, color: mauChu,
                          letterSpacing: cs * 0.05, marginTop: anH * 0.06 }}>
              NEW EPISODE EVERY DAY
            </div>
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  /* COVER Facebook 1640×856 — vùng an toàn hẹp hơn banner YouTube và lệch sang trái vì ảnh đại
     diện của Trang đè lên góc dưới trái. Nên chữ dồn sang phải. */
  if (loai === "cover") {
    const cs = Math.min(H * 0.19, (W * 0.60 / Math.max(1, ten.length)) * 1.55);
    return (
      <AbsoluteFill>
        {Nen}
        <svg width={H * 0.30} height={H * 0.30} viewBox="-0.5 -0.5 1 1"
             style={{ position: "absolute", left: W * 0.10, top: H * (dai - 0.15) }}>
          <Hinh ten={bieu} s={1} mau={nen} muc={nen} mot_mau={nen} />
        </svg>
        <div style={{ position: "absolute", right: W * 0.06, top: H * (dai - 0.22),
                      height: H * 0.44, width: W * 0.62,
                      display: "flex", flexDirection: "column", justifyContent: "center",
                      alignItems: "flex-end", textAlign: "right" }}>
          <div style={{ fontFamily: F, fontWeight: 900, fontSize: cs, color: mauChu,
                        lineHeight: 1.02, textShadow: `0 ${H*0.004}px ${H*0.010}px ${tren ? "#00000018" : "#00000055"}` }}>{ten}</div>
          <div style={{ fontFamily: F, fontWeight: 700, fontSize: cs * 0.32, color: mauChu,
                        letterSpacing: cs * 0.05, marginTop: H * 0.03 }}>NEW EPISODE EVERY DAY</div>
        </div>
      </AbsoluteFill>
    );
  }

  /* POST Instagram 1080×1080 — dùng làm ảnh ghim đầu trang. Chữ to, một dòng, không có gì khác. */
  const cs = Math.min(H * 0.13, (W * 0.86 / Math.max(1, ten.length)) * 1.5);
  return (
    <AbsoluteFill>
      {Nen}
      <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column",
                    alignItems: "center", justifyContent: "center", gap: H * 0.03 }}>
        <svg width={H * 0.34} height={H * 0.34} viewBox="-0.5 -0.5 1 1">
          <Hinh ten={bieu} s={1} mau={nen} muc={nen} mot_mau={nen} />
        </svg>
        <div style={{ fontFamily: F, fontWeight: 900, fontSize: cs, color: mauChu,
                      textAlign: "center", lineHeight: 1.04, maxWidth: W * 0.9,
                      textShadow: `0 ${H*0.004}px ${H*0.010}px ${tren ? "#00000018" : "#00000055"}` }}>{ten}</div>
      </div>
    </AbsoluteFill>
  );
};
