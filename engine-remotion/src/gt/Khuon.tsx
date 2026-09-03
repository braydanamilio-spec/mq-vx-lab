import React from "react";

/* ══════════════════════════════════════════════════════════════════════════════════════════
   BẢY KHUÔN HÌNH — bộ phim giải thích  (1/9/2026)

   Đo trên hai video anh gửi: 244 và 290 nhát cắt, trung vị 2,1 giây, không cảnh nào quá 7
   giây. Một tập 9 phút cần 250 khung hình RIÊNG BIỆT.

   Điều quan trọng không phải con số 250 mà là: họ KHÔNG dựng 250 cảnh diễn xuất. Họ xoay vòng
   bảy khuôn, và bốn trong bảy khuôn chỉ gồm chữ, vạch, mũi tên, biểu tượng — tức dựng được
   100% bằng code, không gọi một lần API ảnh nào.

     1. canh      — một người trong bối cảnh                (cần nền)
     2. chia_doi  — vạch dọc giữa khung, hai nhãn hai bên   (code)  <- thiết bị tu từ TRUNG TÂM
     3. so_lieu   — con số rất to đè lên vật đang nói tới    (code)
     4. truc      — trục thời gian / trục khoảng cách        (code)
     5. kinh_lup  — phóng to một chi tiết, có đường chỉ tên  (code)
     6. nhom      — 4-5 người, dùng cho đoạn nói về xã hội  (cần nền)
     7. anh       — một ảnh thật xen vào cho đổi vị          (kho ảnh)

   `chia_doi` đáng học nhất: mọi luận điểm của họ đều được dựng thành "cái này SO VỚI cái kia".
   Không phải vì đẹp — vì bộ não người đo lường bằng so sánh, không bằng con số tuyệt đối.
   "Một người gánh 25 ký" không nói lên gì; "25 ký, bằng đứa con bảy tuổi của bạn" thì nhớ đời.
   ══════════════════════════════════════════════════════════════════════════════════════════ */

const F = "Poppins, Arial Black, sans-serif";

/* Biểu tượng vẽ bằng code. Cố ý ít và thô: mỗi cái phải đọc được ở 1/6 chiều ngang khung trên
   màn hình điện thoại, nên chi tiết nhiều chỉ thành vết bẩn. */
export const BieuTuong: React.FC<{ ten: string; s: number; mau?: string }> =
({ ten, s, mau = "#2C2722" }) => {
  const k = (v: number) => v * s;
  const n = Math.max(2, s * 0.055);
  const P = (d: string, f = "none", w = 1) => (
    <path d={d} fill={f} stroke={mau} strokeWidth={n * w} strokeLinejoin="round" strokeLinecap="round" />
  );
  switch (ten) {
    /* ── MƯỜI HÌNH THÊM 1/9 ─────────────────────────────────────────────────────────────────
       Bộ cũ có 13 hình cho tất cả bảng dữ liệu, nên hình bị gán theo CÁI GẦN NHẤT CÒN TRỐNG và
       nói sai chuyện ở phần lớn trường hợp. Đo được mức chồng lấn:
         nguoi     -> "an adult human" ĐÚNG, nhưng cũng dùng cho "a red blood cell", "a hair's width"
         cay       -> "a blue whale", "a giraffe", "a virus", "a bacterium"
         trai_dat  -> "a single atom", "the Sun", "the Moon", "Mars"
         xe        -> "a school bus", "a Boeing 747", "a motorbike"
       Cùng gốc rễ với bộ hình brand kit sáng nay: *bộ hình được chốt TRƯỚC bảng nội dung*.
       Thêm hình rẻ hơn nhiều so với việc một biểu tượng sai đứng mãi trong video. */
    case "xe_buyt": return <g>{P(`M ${-k(0.44)} ${-k(0.26)} h ${k(0.88)} v ${k(0.40)} h ${-k(0.88)} Z`, "#E8B324")}
      {P(`M ${-k(0.36)} ${-k(0.18)} h ${k(0.24)} v ${k(0.16)} h ${-k(0.24)} Z`, "#FFFFFF", 0.6)}
      {P(`M ${-k(0.06)} ${-k(0.18)} h ${k(0.24)} v ${k(0.16)} h ${-k(0.24)} Z`, "#FFFFFF", 0.6)}
      <circle cx={-k(0.24)} cy={k(0.16)} r={k(0.10)} fill="#2C2722" />
      <circle cx={k(0.26)} cy={k(0.16)} r={k(0.10)} fill="#2C2722" /></g>;
    case "ca_voi": return <g>{P(`M ${-k(0.46)} 0 q ${k(0.22)} ${-k(0.30)} ${k(0.56)} ${-k(0.20)}
      q ${k(0.20)} ${k(0.04)} ${k(0.26)} ${k(0.20)} q ${-k(0.24)} ${k(0.22)} ${-k(0.56)} ${k(0.16)}
      q ${-k(0.20)} ${-k(0.04)} ${-k(0.26)} ${-k(0.16)} Z`, "#3E6E93")}
      {P(`M ${-k(0.46)} 0 l ${-k(0.14)} ${-k(0.16)} l ${-k(0.02)} ${k(0.32)} Z`, "#3E6E93")}
      <circle cx={k(0.22)} cy={-k(0.06)} r={k(0.035)} fill="#2C2722" /></g>;
    case "huou": return <g>{P(`M ${-k(0.06)} ${k(0.42)} v ${-k(0.34)} h ${k(0.26)} v ${k(0.34)}`, "none")}
      {P(`M ${-k(0.06)} ${k(0.08)} q ${-k(0.02)} ${-k(0.34)} ${k(0.16)} ${-k(0.44)}`, "none", 1.4)}
      {P(`M ${k(0.10)} ${-k(0.36)} l ${k(0.16)} ${-k(0.06)} l ${-k(0.04)} ${k(0.16)} Z`, "#D9A441")}</g>;
    case "meo": return <g><circle cx="0" cy={k(0.06)} r={k(0.30)} fill="#C98A4B" stroke={mau} strokeWidth={n} />
      {P(`M ${-k(0.26)} ${-k(0.14)} l ${-k(0.04)} ${-k(0.22)} l ${k(0.20)} ${k(0.10)} Z`, "#C98A4B")}
      {P(`M ${k(0.26)} ${-k(0.14)} l ${k(0.04)} ${-k(0.22)} l ${-k(0.20)} ${k(0.10)} Z`, "#C98A4B")}
      <circle cx={-k(0.10)} cy={k(0.02)} r={k(0.035)} fill="#2C2722" />
      <circle cx={k(0.10)} cy={k(0.02)} r={k(0.035)} fill="#2C2722" /></g>;
    case "te_bao": return <g><circle cx="0" cy="0" r={k(0.40)} fill="#C4525C" stroke={mau} strokeWidth={n} />
      <circle cx="0" cy="0" r={k(0.17)} fill="#8E2F3A" stroke={mau} strokeWidth={n * 0.7} /></g>;
    case "vi_khuan": return <g>{P(`M ${-k(0.30)} ${-k(0.10)} q ${k(0.10)} ${-k(0.34)} ${k(0.34)} ${-k(0.16)}
      q ${k(0.26)} ${k(0.20)} ${k(0.02)} ${k(0.42)} q ${-k(0.30)} ${k(0.16)} ${-k(0.36)} ${-k(0.16)} Z`, "#6FAE5B")}
      <circle cx={-k(0.04)} cy={k(0.02)} r={k(0.08)} fill="#33632A" /></g>;
    case "nguyen_tu": return <g><circle cx="0" cy="0" r={k(0.09)} fill="#4A5CC4" stroke={mau} strokeWidth={n * 0.7} />
      <ellipse cx="0" cy="0" rx={k(0.42)} ry={k(0.16)} fill="none" stroke={mau} strokeWidth={n * 0.8} />
      <ellipse cx="0" cy="0" rx={k(0.42)} ry={k(0.16)} fill="none" stroke={mau} strokeWidth={n * 0.8}
               transform="rotate(60)" />
      <ellipse cx="0" cy="0" rx={k(0.42)} ry={k(0.16)} fill="none" stroke={mau} strokeWidth={n * 0.8}
               transform="rotate(-60)" /></g>;
    case "mat_troi": return <g><circle cx="0" cy="0" r={k(0.26)} fill="#E8A317" stroke={mau} strokeWidth={n} />
      {[0, 45, 90, 135, 180, 225, 270, 315].map((a, i) => (
        <line key={i} x1={0} y1={-k(0.34)} x2={0} y2={-k(0.46)} stroke={mau} strokeWidth={n}
              strokeLinecap="round" transform={`rotate(${a})`} />))}</g>;
    case "mat_trang": return <g>{P(`M ${k(0.12)} ${-k(0.42)} a ${k(0.42)} ${k(0.42)} 0 1 0 0 ${k(0.84)}
      a ${k(0.33)} ${k(0.33)} 0 1 1 0 ${-k(0.84)} Z`, "#D8D3C6")}</g>;
    case "giuong": return <g>{P(`M ${-k(0.44)} ${k(0.06)} h ${k(0.88)} v ${k(0.22)} h ${-k(0.88)} Z`, "#8E6B4A")}
      {P(`M ${-k(0.40)} ${k(0.06)} q 0 ${-k(0.20)} ${k(0.22)} ${-k(0.20)} h ${k(0.30)} v ${k(0.20)}`, "#EDE7DA")}
      {P(`M ${-k(0.44)} ${k(0.28)} v ${k(0.12)}`)}{P(`M ${k(0.44)} ${k(0.28)} v ${k(0.12)}`)}</g>;
    case "dan_piano": return <g>{P(`M ${-k(0.44)} ${-k(0.14)} h ${k(0.88)} v ${k(0.30)} h ${-k(0.88)} Z`, "#F4F1EA")}
      {[-0.34, -0.22, -0.10, 0.02, 0.14, 0.26].map((x, i) => (
        <rect key={i} x={k(x)} y={-k(0.14)} width={k(0.05)} height={k(0.17)} fill="#2C2722" />))}
      {P(`M ${-k(0.44)} ${-k(0.14)} v ${-k(0.22)} h ${k(0.66)} l ${k(0.22)} ${k(0.22)}`, "#3A2C22")}</g>;
    case "coc":  return <g>{P(`M ${-k(0.3)} ${-k(0.34)} h ${k(0.6)} l ${-k(0.07)} ${k(0.62)} h ${-k(0.46)} Z`, "#FFFFFF")}
      {P(`M ${k(0.3)} ${-k(0.22)} q ${k(0.2)} ${k(0.02)} ${k(0.16)} ${k(0.18)} q ${-k(0.04)} ${k(0.14)} ${-k(0.19)} ${k(0.12)}`)}
      {P(`M ${-k(0.26)} ${-k(0.2)} h ${k(0.52)} l ${-k(0.05)} ${k(0.36)} h ${-k(0.42)} Z`, "#7A4B2A", 0)}</g>;
    case "nha":  return <g>{P(`M ${-k(0.42)} 0 L 0 ${-k(0.42)} L ${k(0.42)} 0 Z`, "#C4553F")}
      {P(`M ${-k(0.3)} 0 h ${k(0.6)} v ${k(0.42)} h ${-k(0.6)} Z`, "#EDE0C8")}
      {P(`M ${-k(0.09)} ${k(0.42)} v ${-k(0.24)} h ${k(0.18)} v ${k(0.24)}`, "#7A5638")}</g>;
    case "xe":   return <g>{P(`M ${-k(0.46)} ${k(0.12)} l ${k(0.1)} ${-k(0.22)} h ${k(0.72)} l ${k(0.1)} ${k(0.22)} v ${k(0.14)} h ${-k(0.92)} Z`, "#3E7FB0")}
      <circle cx={-k(0.26)} cy={k(0.26)} r={k(0.13)} fill={mau} /><circle cx={k(0.26)} cy={k(0.26)} r={k(0.13)} fill={mau} /></g>;
    case "dong_ho": return <g><circle cx="0" cy="0" r={k(0.42)} fill="#FFFFFF" stroke={mau} strokeWidth={n} />
      {P(`M 0 0 v ${-k(0.26)}`, "none", 1.1)}{P(`M 0 0 l ${k(0.18)} ${k(0.1)}`, "none", 1.1)}</g>;
    case "tien": return <g>{P(`M ${-k(0.46)} ${-k(0.26)} h ${k(0.92)} v ${k(0.52)} h ${-k(0.92)} Z`, "#5E9C63")}
      <circle cx="0" cy="0" r={k(0.15)} fill="#EDE3CE" stroke={mau} strokeWidth={n * 0.8} /></g>;
    case "lua":  return <g>{P(`M 0 ${k(0.4)} q ${-k(0.34)} ${-k(0.12)} ${-k(0.2)} ${-k(0.42)}
      q ${k(0.04)} ${k(0.1)} ${k(0.13)} ${k(0.08)} q ${-k(0.1)} ${-k(0.24)} ${k(0.13)} ${-k(0.42)}
      q ${-k(0.02)} ${k(0.2)} ${k(0.14)} ${k(0.24)} q ${k(0.1)} ${-k(0.06)} ${k(0.06)} ${-k(0.16)}
      q ${k(0.2)} ${k(0.24)} ${-k(0.26)} ${k(0.68)} Z`, "#E8862E")}</g>;
    case "nguoi": return <g><circle cx="0" cy={-k(0.3)} r={k(0.14)} fill="#FFFFFF" stroke={mau} strokeWidth={n} />
      {P(`M 0 ${-k(0.16)} v ${k(0.3)}`, "none", 1.2)}{P(`M ${-k(0.2)} ${-k(0.06)} L 0 ${-k(0.12)} L ${k(0.2)} ${-k(0.06)}`, "none", 1.1)}
      {P(`M 0 ${k(0.14)} l ${-k(0.16)} ${k(0.28)}`, "none", 1.2)}{P(`M 0 ${k(0.14)} l ${k(0.16)} ${k(0.28)}`, "none", 1.2)}</g>;
    case "dien_thoai": return <g>{P(`M ${-k(0.22)} ${-k(0.42)} h ${k(0.44)} v ${k(0.84)} h ${-k(0.44)} Z`, "#20262E")}
      {P(`M ${-k(0.16)} ${-k(0.34)} h ${k(0.32)} v ${k(0.6)} h ${-k(0.32)} Z`, "#6FB7E8", 0)}</g>;
    case "trai_dat": return <g><circle cx="0" cy="0" r={k(0.42)} fill="#5A93C8" stroke={mau} strokeWidth={n} />
      {P(`M ${-k(0.3)} ${-k(0.16)} q ${k(0.16)} ${-k(0.1)} ${k(0.28)} ${k(0.02)} q ${k(0.1)} ${k(0.12)} ${-k(0.04)} ${k(0.2)} q ${-k(0.2)} ${k(0.04)} ${-k(0.24)} ${-k(0.22)} Z`, "#6BA45E", 0)}
      {P(`M ${k(0.06)} ${k(0.14)} q ${k(0.16)} ${-k(0.04)} ${k(0.22)} ${k(0.12)} q ${-k(0.1)} ${k(0.1)} ${-k(0.24)} ${k(0.02)} Z`, "#6BA45E", 0)}</g>;
    case "cay":  return <g>{P(`M ${-k(0.06)} ${k(0.42)} v ${-k(0.34)} h ${k(0.12)} v ${k(0.34)} Z`, "#7A5638")}
      <circle cx="0" cy={-k(0.14)} r={k(0.3)} fill="#5E8C4A" stroke={mau} strokeWidth={n} /></g>;
    case "giay": return <g>{P(`M ${-k(0.3)} ${-k(0.42)} h ${k(0.5)} l ${k(0.1)} ${k(0.12)} v ${k(0.72)} h ${-k(0.6)} Z`, "#FFFFFF")}
      {[-0.16, 0, 0.16].map((y, i) => <line key={i} x1={-k(0.18)} y1={k(y)} x2={k(0.2)} y2={k(y)} stroke={mau} strokeWidth={n * 0.7} />)}</g>;
    /* 1/9 — soi khung bắt được: kênh SPEED OF nói "a commercial jet" mà biểu tượng vẽ ra là
       Ô TÔ, vì bảng chỉ có `xe` nên tôi gán tạm. Ở khuôn `so_lieu` thì con số ĐỨNG CẠNH biểu
       tượng, nên gán tạm không phải là "gần đúng" — nó nói sai hẳn cái đang được đo.
       Đây đúng quy tắc G rút từ video tham chiếu: con số phải đứng cạnh HÌNH CỦA CHÍNH VẬT ẤY. */
    case "may_bay": return <g>{P(`M ${-k(0.46)} ${k(0.04)} l ${k(0.62)} ${-k(0.06)} l ${k(0.3)} ${k(0.02)}
      q ${k(0.12)} ${k(0.03)} 0 ${k(0.07)} l ${-k(0.3)} ${k(0.03)} l ${-k(0.62)} ${-k(0.06)} Z`, "#D8DCE0")}
      {P(`M ${-k(0.06)} ${-k(0.01)} l ${-k(0.16)} ${-k(0.3)} h ${k(0.1)} l ${k(0.24)} ${k(0.28)} Z`, "#B9BFC6")}
      {P(`M ${-k(0.06)} ${k(0.05)} l ${-k(0.16)} ${k(0.3)} h ${k(0.1)} l ${k(0.24)} ${-k(0.28)} Z`, "#B9BFC6")}
      {P(`M ${-k(0.4)} ${-k(0.02)} l ${-k(0.1)} ${-k(0.2)} h ${k(0.07)} l ${k(0.14)} ${k(0.18)} Z`, "#B9BFC6")}</g>;
    case "hop":  return <g>{P(`M ${-k(0.4)} ${-k(0.2)} h ${k(0.8)} v ${k(0.56)} h ${-k(0.8)} Z`, "#C9A06A")}
      {P(`M ${-k(0.44)} ${-k(0.34)} h ${k(0.88)} v ${k(0.14)} h ${-k(0.88)} Z`, "#B08A56")}</g>;
    default:     return <circle cx="0" cy="0" r={k(0.36)} fill={mau} opacity={0.25} />;
  }
};

/* ── KHUÔN 2: CHIA ĐÔI ────────────────────────────────────────────────────────────────────
   Vạch dọc, hai nhãn hoa ở trên, hai biểu tượng, hai con số. Nhãn viết HOA và đặt SÁT TRÊN —
   người xem đọc nhãn trước, nhìn hình sau; ngược lại thì phải đoán mình đang so cái gì. */
/* ══════════════════════════════════════════════════════════════════════════════════════════
   NỀN PHÒNG — bề mặt dùng chung cho MỌI khuôn vẽ bằng code  (3/9/2026)

   Anh: *"lớp đồ hoạ vẽ bằng code là chỗ lệch duy nhất còn lại… làm template đẹp để các kênh
   dùng cho đa dạng, không nhàm chán trùng lặp, xứng với clip top đầu thế giới."*

   ── VẤN ĐỀ ĐO ĐƯỢC ──────────────────────────────────────────────────────────────────────
   Mọi khuôn code (`ChiaDoi`, `Chart`, `Truc`, `Dem`, `SoLieu` không ảnh) đặt trên
   `<AbsoluteFill background: nenTrang />` — **một màu phẳng duy nhất**. Ảnh AI thì có tường ấm,
   sàn gỗ, cửa sổ, chậu cây, bóng đổ mềm. Hai thứ đứng cạnh nhau trong một video là lộ ngay.

   Và nó quan trọng gấp đôi: bản dài ngày 3/9 vẽ được **0/32 cảnh AI** vì CF cạn — lúc ấy lớp
   này là thứ DUY NHẤT người xem thấy.

   ── THIẾT KẾ ────────────────────────────────────────────────────────────────────────────
   Cùng ngôn ngữ với ảnh AI, dựng từ ba lớp mà ảnh mẫu nào cũng có:

     1. TƯỜNG   — chuyển màu ấm dịu, sáng ở trên
     2. QUẦNG SÁNG — một nguồn sáng lệch tâm, giả cửa sổ; đây là thứ tạo "chiều sâu" mà nền
                     phẳng không bao giờ có
     3. SÀN     — sẫm hơn tường, ngăn bằng một đường mảnh; mắt đọc ra mặt phẳng đứng được

   ── ĐA DẠNG: SÁU KIỂU PHÒNG, CHỌN THEO `hat` ───────────────────────────────────────────
   `hat` đã được tính theo (kênh, số tập) và truyền sẵn vào engine. Nên hai tập liền nhau của
   cùng một kênh ra hai phòng khác nhau, và hai kênh khác nhau cũng khác — **không tốn một lượt
   gọi API nào**.

   Đây đúng cách bộ truyện tranh đã làm và đã chứng minh (§9, `NoiChon.tsx`): đa dạng sinh ra từ
   TỔ HỢP dựng bằng code, không từ việc gọi thêm ảnh.

   ── VÌ SAO KHÔNG VẼ ĐỒ ĐẠC CHI TIẾT ────────────────────────────────────────────────────
   Vì lớp này luôn có đồ hoạ đè lên (biểu đồ, số lớn, hai cột so sánh). Nền có bàn ghế chi tiết
   sẽ đánh nhau với chúng — đúng lỗi "che khuất" đã sửa cả ngày. Nền chỉ cần **nói rằng đây là
   một không gian**, không cần kể nó là phòng gì.
   ══════════════════════════════════════════════════════════════════════════════════════════ */

/* Làm sáng / làm sẫm một mã màu — dùng dựng bảng màu phòng từ đúng màu nền của kênh. */
const _pha = (h: string, t: number): string => {
  const m = /^#([0-9a-f]{6})$/i.exec((h || "").trim());
  if (!m) return h;
  return "#" + [0, 2, 4].map((i) => {
    const v = parseInt(m[1].slice(i, i + 2), 16);
    const r = t >= 0 ? v + (255 - v) * t : v * (1 + t);
    return Math.max(0, Math.min(255, Math.round(r))).toString(16).padStart(2, "0");
  }).join("");
};

/* Trộn hai mã màu theo tỉ lệ — dùng cho tường/sàn của `NenPhong`, xem chú thích tại chỗ. */
const _tron = (a: string, b: string, t: number): string => {
  const ma = /^#([0-9a-f]{6})$/i.exec((a || "").trim());
  const mb = /^#([0-9a-f]{6})$/i.exec((b || "").trim());
  if (!ma || !mb) return a;
  return "#" + [0, 2, 4].map((i) => {
    const va = parseInt(ma[1].slice(i, i + 2), 16);
    const vb = parseInt(mb[1].slice(i, i + 2), 16);
    return Math.round(va + (vb - va) * t).toString(16).padStart(2, "0");
  }).join("");
};

export const NenPhong: React.FC<{ W: number; H: number; nen: string; mau: string; hat?: number }> =
({ W, H, nen, mau, hat = 0 }) => {
  const k = Math.abs(hat) % 6;
  const yS = H * (k === 1 ? 0.80 : k === 4 ? 0.66 : 0.73);      // đường chân trời đổi theo kiểu
  const xS = W * (k === 2 ? 0.24 : k === 5 ? 0.78 : 0.50);      // nguồn sáng lệch trái/phải/giữa
  /* 3/9 — PHA THEO MÀU THƯƠNG HIỆU, KHÔNG CHỈ THEO `nen`.
     Bản đầu dựng phòng từ `nen` của kênh. Đo bảng màu thật thì `nen` của MỌI kênh đều gần
     trắng — `#E8E9E6` · `#F2F0EA` · `#EEF1F3` · `#EDEEF2` — nên tường và sàn pha ra vẫn trắng,
     và căn phòng đọc ra y hệt nền phẳng cũ.

     Ảnh AI tham chiếu thì có màu THẬT: tường kem ấm, sàn gỗ, cát vàng. Nên pha `nen` về phía
     `mau` (màu thương hiệu) một lượng nhỏ: đủ để phòng có sắc, vẫn đủ sáng để chữ trắng và đồ
     hoạ đè lên đọc được. Sàn pha đậm hơn tường, vì trong ảnh thật sàn luôn sẫm hơn tường.

     Đây là chỗ dễ sai theo hướng ngược lại: pha mạnh thì phòng thành một khối màu và nuốt đồ
     hoạ. 0,12 / 0,26 là mức giữ được cả hai. */
  const tuong = _pha(_tron(nen, mau, 0.10), 0.18);
  const tuongD = _pha(_tron(nen, mau, 0.14), -0.02);
  const san = _pha(_tron(nen, mau, 0.22), k === 3 ? -0.26 : -0.16);
  const sanD = _pha(_tron(nen, mau, 0.26), -0.34);
  const vach = _pha(mau, -0.55);
  const id = `np${Math.round(W)}_${k}`;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <linearGradient id={`${id}t`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={tuong} /><stop offset="1" stopColor={tuongD} />
        </linearGradient>
        <linearGradient id={`${id}s`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={san} /><stop offset="1" stopColor={sanD} />
        </linearGradient>
        <radialGradient id={`${id}g`} cx="50%" cy="50%" r="50%">
          <stop offset="0" stopColor="#FFFFFF" stopOpacity={0.55} />
          <stop offset="0.55" stopColor="#FFFFFF" stopOpacity={0.16} />
          <stop offset="1" stopColor="#FFFFFF" stopOpacity={0} />
        </radialGradient>
      </defs>

      <rect x={0} y={0} width={W} height={yS} fill={`url(#${id}t)`} />
      {/* quầng sáng — thứ tạo chiều sâu mà nền phẳng không có */}
      <ellipse cx={xS} cy={yS * 0.52} rx={W * 0.62} ry={yS * 0.86} fill={`url(#${id}g)`} />

      {/* kiểu 0 và 5: khung cửa sổ gợi ý, chỉ hai nét — đủ nói "trong nhà, có ánh sáng ngoài" */}
      {(k === 0 || k === 5) ? (
        <g stroke={vach} strokeWidth={Math.max(2, H * 0.0035)} fill="none" opacity={0.30}>
          <rect x={xS - W * 0.20} y={yS * 0.13} width={W * 0.40} height={yS * 0.52} rx={H * 0.012} />
          <line x1={xS} y1={yS * 0.13} x2={xS} y2={yS * 0.65} />
        </g>
      ) : null}

      {/* kiểu 2: đường gờ tường ngang — nhịp thị giác, không phải đồ đạc */}
      {k === 2 ? (
        <rect x={0} y={yS * 0.70} width={W} height={Math.max(2, H * 0.004)} fill={vach} opacity={0.22} />
      ) : null}

      <rect x={0} y={yS} width={W} height={H - yS} fill={`url(#${id}s)`} />
      <rect x={0} y={yS} width={W} height={Math.max(2, H * 0.0035)} fill={vach} opacity={0.34} />

      {/* bóng tiếp đất mềm ngay dưới chân trời — đồ hoạ đè lên sẽ như đứng trên sàn, không lơ lửng */}
      <ellipse cx={W / 2} cy={yS + H * 0.012} rx={W * 0.40} ry={H * 0.022} fill="#000000" opacity={0.07} />
    </svg>
  );
};

export const ChiaDoi: React.FC<{
  W: number; H: number; trai: any; phai: any; mau: string; p: number;
  nen?: string; hat?: number;
}> = ({ W, H, trai, phai, mau, p, nen = "#F2F0EA", hat = 0 }) => {
  /* CỠ CHỮ PHẢI CHỊU CẢ HAI RÀNG BUỘC.
     Bản đầu tính cỡ chữ chỉ theo CHIỀU CAO khung (`H*0.105`). Trên khung ngang 16:9 thì vừa;
     trên khung dọc 9:16 mỗi cột chỉ rộng 540px mà cỡ chữ vẫn là 202px, nên "1.08 billion km/h"
     tràn qua vạch giữa và chồng lên vế bên kia.
     Đây đúng họ lỗi đã ghi ở CLAUDE.md: *một kích thước chịu hai ràng buộc mà công thức chỉ mã
     hoá một*. Chuỗi dài ngắn khác nhau và cột rộng hẹp khác nhau — cả hai đều phải vào công thức. */
  const cot = W * 0.46;                       // bề ngang thật của mỗi vế
  const _vua = (chu: string, theoH: number) => {
    const n = Math.max(1, (chu || "").length);
    return Math.min(theoH, (cot / n) * 1.55);  // 1,55 ≈ 1 / bề ngang trung bình một chữ phông đậm
  };
  /* HAI VẾ PHẢI CÙNG MỘT CỠ CHỮ — lấy cỡ NHỎ HƠN.
     Tính riêng từng vế thì "5 km/h" ra 142px còn "1.08 billion km/h" ra 50px: chênh gần ba lần.
     Không tràn khung nữa, nhưng hỏng theo cách tệ hơn — cỡ chữ khác nhau NÓI RẰNG hai vế không
     ngang hàng, trong khi cả khuôn hình này tồn tại để nói chúng ngang hàng. Người xem đọc kích
     thước trước khi đọc chữ.
     Nên mọi cặp (nhãn/số/phụ) đều lấy min của hai bên. */
  const doi = (ka: string, kb: string, theoH: number) =>
    Math.min(_vua(ka, theoH), _vua(kb, theoH));
  const cNhan = doi((trai.nhan || "").toUpperCase(), (phai.nhan || "").toUpperCase(), H * 0.055);
  const cSo = doi(trai.so || "", phai.so || "", H * 0.105);
  const cPhu = doi(trai.phu || "", phai.phu || "", H * 0.040);
  const ben = (d: any, x: number, tre: number) => {
    const q = Math.max(0, Math.min(1, (p - tre) / 0.3));
    return (
      <g opacity={q} transform={`translate(${x} 0)`}>
        {/* BÓNG TIẾP ĐẤT dưới biểu tượng.  (3/9/2026)
            Không có nó thì hai biểu tượng lơ lửng giữa khung như hai hình dán, và khuôn này
            đọc ra "slide thuyết trình" thay vì "một cảnh". Cùng thứ đã thêm cho chủ thể ở
            `KichGiaiThich` và cho cột ở `Chart` — một khung có mặt sàn thì MỌI vật đứng trên
            sàn ấy phải để lại bóng, thiếu một vật là mắt đọc ra ngay. */}
        <ellipse cx="0" cy={H * 0.60} rx={H * 0.115} ry={H * 0.020}
                 fill="#000000" opacity={0.13} />
        <text x="0" y={H * 0.20} textAnchor="middle" fontFamily={F} fontWeight={900}
              fontSize={cNhan} fill="#2C2722"
              letterSpacing={1}>{(d.nhan || "").toUpperCase()}</text>
        <g transform={`translate(0 ${H * 0.44}) scale(${1 + (1 - q) * 0.12})`}>
          <BieuTuong ten={d.bt || ""} s={H * 0.30} />
        </g>
        {d.so ? (
          <text x="0" y={H * 0.76} textAnchor="middle" fontFamily={F} fontWeight={900}
                fontSize={cSo} fill={mau}>{d.so}</text>
        ) : null}
        {d.phu ? (
          <text x="0" y={H * 0.845} textAnchor="middle" fontFamily={F} fontWeight={700}
                fontSize={cPhu} fill="#5A544C">{d.phu}</text>
        ) : null}
      </g>
    );
  };
  const kk = Math.abs(hat) % 3;
  return (
    <g>
      {/* HAI TẤM NỀN MỜ dựng cấu trúc cho khuôn so sánh.  (3/9/2026)
          Bản trước chỉ có một vạch đứt giữa khung: hai vế trôi trên cùng một mặt phẳng, và mắt
          phải TỰ gom "nhãn + hình + số" thành một nhóm. Hai tấm nền làm việc gom ấy hộ mắt —
          đây là thứ mọi bảng so sánh chuyên nghiệp đều có, và nó không tốn thêm một chữ nào.
          Vế phải đậm hơn một chút vì nó là vế bất ngờ, vế mà lời kể dẫn tới.
          `hat` đổi bo góc và độ đậm theo TẬP để hai tập liền nhau không ra một tấm ảnh. */}
      {[0, 1].map((j) => (
        <rect key={`p${j}`} x={W * (j ? 0.515 : 0.025)} y={H * 0.075}
              width={W * 0.46} height={H * 0.79}
              rx={W * (kk === 1 ? 0.004 : kk === 2 ? 0.022 : 0.013)}
              fill={_tron(nen, mau, j ? 0.13 : 0.05)}
              opacity={(kk === 2 ? 0.62 : 0.86) * Math.min(1, p / 0.35)} />
      ))}
      {ben(trai, W * 0.25, 0)}
      {/* Vạch giữa VẼ DẦN từ trên xuống: mắt bám theo nét đang chạy, nên nó dẫn người xem sang
          vế thứ hai đúng lúc lời kể nói tới vế thứ hai. */}
      <line x1={W / 2} y1={H * 0.10} x2={W / 2} y2={H * (0.10 + 0.80 * Math.min(1, p / 0.5))}
            stroke="#2C2722" strokeWidth={Math.max(3, H * 0.006)} strokeDasharray={`${H * 0.03} ${H * 0.022}`} />
      {/* Vế phải trễ 0,16 chứ không 0,35: cảnh chỉ dài ~1,8 giây, trễ 0,35 nghĩa là vế phải
          mới hiện xong lúc cảnh gần hết — soi khung kênh COULD YOU SURVIVE thấy đúng thế, nửa
          bên phải trống trơn. Trễ vẫn cần (để mắt đọc vế trái trước), nhưng phải vừa với nhịp. */}
      {ben(phai, W * 0.75, 0.16)}
    </g>
  );
};

/* ── KHUÔN 3: SỐ LIỆU ĐÈ HÌNH ─────────────────────────────────────────────────────────────
   Con số chiếm 1/5 chiều cao khung. To đến mức khó chịu là CỐ Ý: đây là khuôn dùng cho đúng
   một con số mà cả đoạn xoay quanh, và nó phải đọc được khi video chạy trong luồng cuộn. */
/* CHỌN MÀU CHỮ BẰNG ĐO TƯƠNG PHẢN, không bằng "trên ảnh hay không".
   Bản trước: `fill={tren_anh ? "#F2EFE9" : mau}`. Nhánh `mau` là màu nhận diện kênh, và với
   `howloud` màu ấy là đỏ `#C2352E` — đặt lên nền xám sáng của khung không-ảnh thì đo được ~4:1,
   dưới chuẩn WCAG AA. Cùng công thức đã cứu brand kit sáng nay: hỏi CON SỐ, đừng hỏi ngữ cảnh.
   Màu kênh vẫn giữ ở nơi khác (con số, cột chart, dải nền); chỉ nhường ở chỗ phải ĐỌC ĐƯỢC. */
const _lum = (h: string): number => {
  const m = /^#([0-9a-f]{6})$/i.exec((h || "").trim());
  if (!m) return 0;
  const v = [0, 2, 4].map((i) => parseInt(m[1].slice(i, i + 2), 16) / 255)
    .map((u) => (u <= 0.03928 ? u / 12.92 : Math.pow((u + 0.055) / 1.055, 2.4)));
  return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2];
};
const _tp = (a: number, b: number): number =>
  (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
/** Màu chữ đọc được trên nền `nen`: thử `uu` trước, rơi về đậm/nhạt nếu chưa đạt 4,5:1. */
export const chuHopNen = (uu: string, nen: string, dam = "#2C2722", nhat = "#F4F1EA"): string => {
  const n = _lum(nen);
  // NGƯỠNG 5.2, KHÔNG PHẢI 4.5 — vì `nen` là màu PHẲNG còn nền thật là DẢI CHUYỂN sáng hơn ở
  // phía trên. Đo `howloud`: đỏ #C2352E trên #EFE7D6 ra đúng 4.50, vừa đủ nên giữ màu đỏ —
  // nhưng soi khung thật thì chữ đỏ ấy nằm trên phần sáng hơn của dải và gần không đọc được.
  // Một ngưỡng tính trên màu KHÔNG PHẢI màu thật sau lưng chữ thì phải có biên; 5.2 là 4.5 cộng
  // phần dải sáng lên đo được (~0.7).
  if (_tp(_lum(uu), n) >= 5.2) return uu;
  return _tp(_lum(dam), n) >= _tp(_lum(nhat), n) ? dam : nhat;
};

export const SoLieu: React.FC<{
  W: number; H: number; so: string; don: string; chu: string; bt: string; mau: string; p: number;
  tren_anh?: boolean; nen?: string; bo?: number;
}> = ({ W, H, so, don, chu, bt, mau, p, tren_anh = false, nen = "#EFE7D6", bo = 0 }) => {
  /* ── BỐ CỤC PHẢI ĐỔI THEO HƯỚNG KHUNG ────────────────────────────────────────────────
     Anh: *"bản 16:9 đang bị che khuất."* Đúng, và gốc rễ là mọi vị trí ở đây tính theo `H`.
     Khung dọc cao 1920 nên `H*0.20` cho chữ số là vừa; khung ngang chỉ cao 1080 nên cùng công
     thức ấy cho ra dải số chiếm gần một phần ba chiều cao, và dòng chú thích ở `H*0.94` rơi
     đúng vào giữa thân người.
     Đây lại là họ lỗi "một hằng phục vụ hai thứ biến thiên độc lập": một bộ toạ độ phục vụ cả
     hai tỉ lệ khung, mà hai tỉ lệ ấy có ngân sách chiều cao khác hẳn nhau.
     Khung ngang: chữ số nhỏ hơn, dải nền mỏng hơn, chú thích nằm NGAY DƯỚI số thay vì ở đáy. */
  const ngang = W > H;
  /* BỐ CỤC ĐỔI THEO TẬP (`bo` = hạt giống % 3). Trước bản này mọi tập của một kênh dựng y hệt:
     đo 5 tập liên tiếp của cả 18 kênh ra đúng MỘT chuỗi khuôn. Nội dung đã khác mà khuôn dựng
     vẫn một, nên xem hai tập liền vẫn thấy lặp.
       bo 0  bố cục gốc
       bo 1  số lớn hơn, đặt cao hơn   — nhấn con số
       bo 2  số nhỏ hơn, đặt thấp hơn  — nhường chỗ cho hình
     Ba biến thể đổi TRỌNG TÂM khung mà không đụng khớp hình–lời (quy tắc A). */
  const cCao = (ngang ? 0.13 : 0.20) * (bo === 1 ? 1.16 : bo === 2 ? 0.84 : 1);
  const yCao = (ngang ? 0.17 : 0.26) * (bo === 1 ? 0.86 : bo === 2 ? 1.18 : 1);
  /* 0.94 là ĐÁY KHUNG — đúng chỗ dải phụ đề chiếm. Soi khung `howmuch` nhịp 0: dòng
     "A Billion Is Not A Big Million?" chồng lên vùng phụ đề, hai lớp chữ đè nhau, cả hai cùng
     khó đọc. Đưa nó lên NGAY DƯỚI con số — chỗ nó vốn thuộc về về mặt nghĩa.
     Màu chữ cũng phải theo nền: `#3A342C` đậm chỉ đúng trên nền sạch. */
  /* Trên ảnh thì chú thích phải nằm TRONG dải mờ (dải phủ tới 0,46), không nằm ở mép nó:
     soi khung hook `survive`, dòng chữ rơi đúng chỗ dải đã tan hết nên chìm vào trời sáng. */
  /* ── CHÚ THÍCH PHẢI ĐI THEO KHỐI SỐ, KHÔNG ĐỨNG Ở PHÂN SỐ CỐ ĐỊNH  (3/9/2026) ──────────
     Anh soi khung REAL COST: `30,258 / DOLLARS IN 10 YEARS` và `assuming a 7% annual return`
     **chồng lên nhau**, đọc ra một mớ.

     Đo bằng chính công thức: khối số đặt ở `yCao = 0.26 × (bo===2 ? 1.18 : 1)`, tức nó **dịch
     theo biến thể bố cục** `bo`. Còn `yChu` là **0.37 cố định**. Với `bo === 2`:

         số      y = 0.307·H = 589
         đơn vị  y = 589 + cs·0.56 = 701
         chú thích y = 0.37·H     = 710      ← cách nhau 9px

     Hai giá trị cùng mô tả MỘT chồng chữ mà chỉ một cái biết về `bo`. Đúng họ lỗi đã trả giá
     nhiều lần: *hằng số không đi theo thứ nó nuôi* (§13.6) — và nó không báo lỗi, chỉ làm chữ
     đè nhau ở đúng một trong ba biến thể, nên rất dễ lọt.

     Nay tính TỪ đáy khối số: chú thích luôn nằm dưới dòng đơn vị một khoảng bằng 0,5 cỡ số,
     dù `bo` là gì. `yChuMin` giữ sàn để trên bản ngang chữ không leo quá cao. */
  const yChuMin = ngang ? 0.33 : (tren_anh ? 0.37 : 0.44);
  const q = Math.min(1, p / 0.28);
  /* Cùng lỗi với `ChiaDoi`, và thêm một lỗi nữa: biểu tượng đặt ở `H*0.62` còn con số ở
     `H*0.30` với cỡ `H*0.20` — hai lớp cùng chọn chỗ theo H mà không biết nhau, nên số "9"
     nằm đè lên cái biểu tượng. Nay biểu tượng bám ĐÁY khung và số bám ĐỈNH, không gặp nhau. */
  const cs = Math.min(H * cCao, (W * 0.88 / Math.max(1, so.length)) * 1.65);
  // đáy dòng đơn vị = yCao·H + cs·0.56 ; chừa thêm 0,5·cs rồi mới đặt chú thích
  const yChu = Math.max(yChuMin, (H * yCao + cs * 0.56 + cs * 0.50) / H);
  /* SỐ ĐẾM LÊN — anh: *"số liệu động animation là đẹp hay."*
     Không phải hiệu ứng cho vui: con số nhảy dần làm người xem CẢM được độ lớn, còn con số
     hiện sẵn thì chỉ được đọc. Với kênh mà cả nội dung là những con số thì đây là chỗ đắt nhất.
     Chỉ đếm phần CHỮ SỐ, giữ nguyên dấu và đơn vị dính liền ($, %, x, km/h). */
  const dem = (chu: string, tien: number) => {
    if (tien >= 1) return chu;
    return chu.replace(/[\d][\d,\.]*/g, (m) => {
      const v = parseFloat(m.replace(/,/g, ""));
      if (!isFinite(v)) return m;
      const w = v * tien;
      return m.includes(",") ? Math.round(w).toLocaleString()
           : m.includes(".") ? w.toFixed(1) : `${Math.round(w)}`;
    });
  };
  const soHien = dem(so, Math.min(1, p / 0.42));
  const cd = Math.min(H * 0.055, (W * 0.80 / Math.max(1, (don || "").length)) * 1.7);
  return (
    <g>
      {/* 1/9 — DẢI NỀN KHI CHỮ ĐÈ LÊN ẢNH.
          Soi khung kênh A DAY IN THE LIFE: chữ "KILOMETRES" nằm lọt sau người trong ảnh, đọc
          không ra. Viền trắng quanh chữ không cứu được, vì nền phía sau cũng sáng.
          Chữ đặt trên ảnh thì PHẢI có nền riêng — không có cách nào khác bảo đảm đọc được, vì
          ảnh mỗi nhịp một sáng tối khác nhau và không ai biết trước. */}
      {/* 1/9 (lần 2) — BỎ THẺ BO GÓC. Bản trước vẽ một `rect` xám mờ 0,62 sau con số. Soi khung
          `howmuch` nhịp 3 và 5: nó thành một TẤM XÁM ĐÈ NGANG MẶT ĐỒNG HỒ, che mất chính vật mà
          lời kể đang nói tới — và trông đúng như thứ luật §12.12 của tôi đã cấm ("hộp đen bo góc
          → chữ trắng + bóng mềm rộng"). Viết luật rồi tự phạm.
          Dải MỜ DẦN từ đỉnh làm đúng việc cần (nâng tương phản) mà không cắt ngang qua hình. */}
      {tren_anh ? (
        <>
          <defs>
            <linearGradient id={`sl${Math.round(W)}`} x1="0" y1="0" x2="0" y2="1">
              {/* 2/9 — DẢI MỜ TẮT TRƯỚC CHỖ CÓ CHỮ.
                  Anh: *"nhớ tránh tràn hay che khuất."* Trích khung ra nhìn: dòng chú thích
                  "a jet at takeoff" đè lên mũi máy bay TRẮNG, gần như đọc không ra.

                  Đo trên chính công thức cũ: chú thích đặt ở `y = 0.37·H`, dải mờ cao `0.46·H`
                  và đã giảm từ 0.34 (ở 62%) xuống 0 — tại 0.37·H độ đậm chỉ còn **~0.17**.
                  Dải CÓ tồn tại, nhưng nó tắt TRƯỚC chỗ cần nó nhất.

                  Họ lỗi quen: hằng số 0.62 đặt cho bố cục cũ, còn chỗ đặt chữ đã đổi sang 0.37
                  mà không ai soát lại dải mờ nuôi nó (§13.6 — hằng số sống lâu hơn ngữ cảnh).

                  Nay giữ ≥0.55 qua hết vùng chữ rồi mới tan, cao 0.54·H. Vẫn là dải MỜ DẦN nên
                  không cắt ngang qua hình — chỉ là phủ đủ chỗ chữ thật sự đứng. */}
              {/* 3/9 — SIẾT LẦN HAI, SAU KHI ĐO TRÊN ẢNH SÁNG.
                  Cổng `kiem_chelap` bắt được ca thật: khung `so_lieu` của SURVIVE có nền
                  **sáng TB 177–189, 50–55% điểm ảnh sáng** — chữ trắng gần như chìm.
                  Ở mức cũ (0.62 ở 58%) thì trên nền 230 chỉ còn xám ~126, tương phản ~3:1 với
                  chữ trắng: dưới chuẩn đọc được.
                  Nay giữ ≥0.72 qua hết vùng chữ. Trên nền 230 cho ra ~64 — tương phản ~7:1. */}
              {/* 3/9 — BỎ MÀU ĐEN, DÙNG MÀU THƯƠNG HIỆU ĐẬM.
                  Anh soi bản short REAL COST: *"ko làm bóng mờ đen thế nha xấu"*. Đúng — dải
                  `#0B0E14` là một màu KHÔNG có mặt ở đâu khác trong khung, nên nó đọc ra một
                  tấm kính khói dán lên ảnh, không đọc ra một phần của bức hình.
                  Em đã bỏ dải ấy ở phụ đề hôm qua nhưng để nguyên ở đây — đúng họ lỗi *vá một
                  nhánh, để nguyên nhánh song song*, lần thứ bảy trong tuần.

                  Thay bằng chính màu kênh làm đậm. Cùng độ tối (nên tương phản giữ nguyên,
                  cổng `kiem_chelap` vẫn qua) nhưng mắt đọc nó ra "chỉnh màu điện ảnh" chứ
                  không ra "bóng đen" — vì nó nằm trong bảng màu đã có mặt ở con số, ở cột
                  biểu đồ, ở thẻ chương.

                  Và tan sớm hơn (kết thúc ở 88% thay vì 100%) để nửa dưới bức ảnh sáng nguyên
                  vẹn — chỗ có mặt người, thứ anh muốn nhìn rõ nhất. */}
              <stop offset="0%" stopColor={_pha(mau, -0.62)} stopOpacity={0.88} />
              <stop offset="62%" stopColor={_pha(mau, -0.62)} stopOpacity={0.70} />
              <stop offset="88%" stopColor={_pha(mau, -0.55)} stopOpacity={0.24} />
              <stop offset="100%" stopColor={_pha(mau, -0.55)} stopOpacity={0} />
            </linearGradient>
          </defs>
          <rect x={0} y={0} width={W} height={H * (ngang ? 0.48 : 0.54)}
                fill={`url(#sl${Math.round(W)})`} />
        </>
      ) : null}
      {bt ? <g transform={`translate(${W / 2} ${H * (ngang ? 0.62 : tren_anh ? 0.70 : 0.64)})`} opacity={tren_anh ? 0.92 : 1}>
        {/* CỠ BIỂU TƯỢNG THEO VAI TRÒ, không một cỡ cho hai vai trò khác nhau.
            Trên ảnh, biểu tượng chỉ là phụ chú -> nhỏ là đúng. KHÔNG có ảnh thì biểu tượng LÀ
            hình của cả khung, và cỡ 0,30 cho ra khung 60% trống (soi `howmuch` nhịp 0). Ảnh
            tham chiếu anh gửi đều có chủ thể chiếm quá nửa khung. */}
        <BieuTuong ten={bt} s={tren_anh ? Math.min(H * 0.26, W * 0.28)
                                        : Math.min(H * 0.40, W * 0.66)} /></g> : null}
      <g transform={`translate(${W / 2} ${H * yCao}) scale(${0.86 + q * 0.14})`} opacity={q}>
        <text x="0" y="0" textAnchor="middle" fontFamily={F} fontWeight={900}
              fontSize={cs}
              fill={tren_anh ? "#FFFFFF" : "#2C2722"}
              style={{ filter: tren_anh
                ? `drop-shadow(0 ${H * 0.004}px ${H * 0.012}px #000000cc)`
                : `drop-shadow(0 ${H * 0.003}px ${H * 0.008}px #00000033)` }}>{soHien}</text>
        {/* 2/9 — BÓNG MỀM RỘNG, KHÔNG PHẢI BÓNG MỎNG.
            Anh: *"nhớ tránh tràn hay che khuất."* Phóng to khung mở đầu: số "124" đọc tốt, còn
            dòng "a jet at takeoff" bị **các tia đen của nền cắt ngang qua chữ**. Dải mờ đã làm
            đúng việc (nền tối đi), nhưng tia đen nằm TRÊN dải mờ, nên chữ trắng vẫn bị xé.

            Bóng cũ `0 0.3% 0.9% #00000099` quá mỏng để tách chữ khỏi một nét đen đi xuyên qua
            nó. Nay hai lớp: một quầng RỘNG không lệch (tách chữ khỏi mọi thứ phía sau) cộng một
            bóng đổ nhẹ (giữ cảm giác nổi khối).

            KHÔNG dùng viền `paintOrder="stroke"` — §12.12 xếp viền quanh chữ vào danh sách dấu
            hiệu nghiệp dư: *"không hãng phim nào viền chữ"*. Quầng mềm làm đúng việc ấy mà
            không để lại đường viền cứng. */}
        {don ? <text x="0" y={cs * 0.56} textAnchor="middle" fontFamily={F} fontWeight={800}
                     fontSize={cd} fill={tren_anh ? "#F2EFE9" : chuHopNen(mau, nen)} letterSpacing={2}
                     style={{ filter: tren_anh
                       ? `drop-shadow(0 0 ${H * 0.016}px #000000ee) drop-shadow(0 ${H*0.004}px ${H*0.010}px #000000cc)`
                       : `drop-shadow(0 ${H*0.003}px ${H*0.009}px #00000099)` }}
                     >{don.toUpperCase()}</text> : null}
      </g>
      {chu ? <text x={W / 2} y={H * yChu} textAnchor="middle" fontFamily={F} fontWeight={700}
                   fontSize={Math.min(H * 0.042, (W * 0.90 / Math.max(1, chu.length)) * 1.45)}
                   fill={tren_anh ? "#EDE9E1" : chuHopNen("#3A342C", nen)}
                   style={tren_anh ? { filter: `drop-shadow(0 0 ${H * 0.015}px #000000ee) drop-shadow(0 ${H * 0.004}px ${H * 0.011}px #000000cc)` }
                                   : undefined}>{chu}</text> : null}
    </g>
  );
};

/* ── KHUÔN 4: TRỤC ────────────────────────────────────────────────────────────────────────
   Trục thời gian hoặc trục khoảng cách. Mũi tên chạy DẦN theo `p`, và cái chấm sáng dừng ở
   đúng chỗ lời kể đang nói. Không có cái chấm ấy thì trục chỉ là hình trang trí. */
export const Truc: React.FC<{
  W: number; H: number; moc: { nhan: string; phu?: string }[]; vt: number; mau: string; p: number;
}> = ({ W, H, moc, vt, mau, p }) => {
  const x0 = W * 0.10, x1 = W * 0.90, y = H * 0.52;
    /* Trục hiện xong trong 35% thời lượng cảnh, không phải 55%. Ở nhịp 1,6 giây thì 55% là
     0,9 giây — cảnh gần hết mà trục mới vẽ xong, người xem không kịp đọc mốc cuối. */
  const ch = Math.min(1, p / 0.35);
  const n = Math.max(3, H * 0.007);
  return (
    <g>
      <line x1={x0} y1={y} x2={x0 + (x1 - x0) * ch} y2={y} stroke="#2C2722" strokeWidth={n} />
      <path d={`M ${x0 + (x1 - x0) * ch} ${y} l ${-H * 0.028} ${-H * 0.018} l 0 ${H * 0.036} Z`}
            fill="#2C2722" opacity={ch > 0.96 ? 1 : 0} />
      {moc.map((m, i) => {
        const fx = moc.length === 1 ? 0.5 : i / (moc.length - 1);
        const x = x0 + (x1 - x0) * fx;
        const hien = ch >= fx - 0.02;
        return (
          <g key={i} opacity={hien ? 1 : 0}>
            <line x1={x} y1={y - H * 0.035} x2={x} y2={y + H * 0.035} stroke="#2C2722" strokeWidth={n * 0.8} />
            <text x={x} y={y - H * 0.065} textAnchor="middle" fontFamily={F} fontWeight={900}
                  fontSize={H * 0.055} fill="#2C2722">{m.nhan}</text>
            {m.phu ? <text x={x} y={y + H * 0.10} textAnchor="middle" fontFamily={F} fontWeight={700}
                           fontSize={H * 0.036} fill="#5A544C">{m.phu}</text> : null}
          </g>
        );
      })}
      {vt >= 0 ? (
        <circle cx={x0 + (x1 - x0) * vt} cy={y} r={H * 0.026 * (1 + 0.18 * Math.sin(p * 12))}
                fill={mau} stroke="#FFFFFF" strokeWidth={n} />
      ) : null}
    </g>
  );
};

/* ── KHUÔN 5: KÍNH LÚP ────────────────────────────────────────────────────────────────────
   Vòng tròn phóng to một chi tiết + đường chỉ tới tên gọi. Khuôn này làm một việc mà lời nói
   không làm được: chỉ ĐÍCH XÁC vào chỗ đang nói. */
export const KinhLup: React.FC<{
  W: number; H: number; x: number; y: number; nhan: string; mau: string; p: number;
  con: React.ReactNode;
}> = ({ W, H, x, y, nhan, mau, p, con }) => {
  /* 1/9 — KÍNH LÚP ĐANG PHÓNG TO CHỖ TRỐNG.
     Lúc bỏ nhân vật vector, tôi truyền `con={null}` vào đây rồi quên nối ảnh nền vào thay.
     Soi khung kênh THE RULES: vòng tròn trắng tinh, không phóng gì cả.
     Đúng luật 7bp vừa ghi sáng nay — *bỏ một lớp thì phải rà những chỗ lớp cũ đang được dựa
     vào* — và tôi vi phạm chính nó trong cùng một ngày. */
  const r = H * 0.20 * Math.min(1, p / 0.3);
  const cx = W * 0.72, cy = H * 0.34;
  return (
    <g>
      <defs><clipPath id="lup"><circle cx={cx} cy={cy} r={r} /></clipPath></defs>
      <circle cx={cx} cy={cy} r={r} fill="#FFFFFF" />
      <g clipPath="url(#lup)">
        <g transform={`translate(${cx - x * 2.2} ${cy - y * 2.2}) scale(2.2)`}>{con}</g>
      </g>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#2C2722" strokeWidth={Math.max(4, H * 0.010)} />
      <line x1={x} y1={y} x2={cx - r * 0.7} y2={cy + r * 0.7} stroke="#2C2722"
            strokeWidth={Math.max(3, H * 0.006)} />
      <circle cx={x} cy={y} r={H * 0.014} fill={mau} stroke="#2C2722" strokeWidth={2} />
      {nhan ? (
        <text x={cx} y={cy + r + H * 0.075} textAnchor="middle" fontFamily={F} fontWeight={800}
              fontSize={H * 0.042} fill="#2C2722">{nhan}</text>
      ) : null}
    </g>
  );
};

/* ══════════════════════════════════════════════════════════════════════════════════════════
   BA KHUÔN BỔ SUNG — rút ra khi soi CHUỖI CẢNH LIÊN TIẾP, không phải khung rời  (1/9/2026)

   Anh: *"e cắt từng cảnh trong videos họ ra soi, họ làm rất logic, hình ảnh và bối cảnh ăn khớp
   lời nói kịch bản, logic xuyên suốt đó."*

   Lần soi đầu tôi lấy 25 khung RỜI RẠC rải đều và rút ra "bảy khuôn hình". Đúng nhưng nông:
   khuôn hình là từ vựng, còn thứ làm nên phim là NGỮ PHÁP — cảnh này nối cảnh kia thế nào.
   Cắt 24 cảnh LIÊN TIẾP ra mới thấy, và ba thứ dưới đây là ba chỗ engine đang thiếu hẳn.
   ══════════════════════════════════════════════════════════════════════════════════════════ */

/* ── DẢI CHỮ DƯỚI — làm xương sống cho BỘ CẢNH SONG SONG ───────────────────────────────────
   Bằng chứng: bốn cảnh liên tiếp `LIVED · ATE · MARRIED · KNEW`. Nội dung khác hẳn nhau, mà
   bố cục y hệt và dải chữ nằm ĐÚNG một chỗ. Mắt người bám vào chỗ không đổi để nhận ra "đây
   là một danh sách", rồi mới đọc chỗ đổi.
   Nếu đổi cả bố cục lẫn nội dung thì bốn cảnh ấy thành bốn cảnh rời — mất hẳn cấu trúc liệt kê
   mà câu văn đang có. Đây là chỗ hình phải PHỤC TÙNG cú pháp của lời. */
export const DaiChu: React.FC<{ W: number; H: number; chu: string; p: number }> =
({ W, H, chu, p }) => {
  if (!chu) return null;
  const q = Math.min(1, p / 0.25);
  const fs = Math.min(H * (W > H ? 0.055 : 0.075), (W * 0.80 / Math.max(1, chu.length)) * 1.5);
  return (
    <g opacity={q}>
      <rect x="0" y={H - fs * 1.7} width={W} height={fs * 1.7} fill="#FFFFFF" opacity={0.94} />
      <text x={W / 2} y={H - fs * 0.48} textAnchor="middle" fontFamily={F} fontWeight={900}
            fontSize={fs} fill="#2C2722" letterSpacing={fs * 0.06}>{chu.toUpperCase()}</text>
    </g>
  );
};

/* ── ĐẾM BẰNG BIỂU TƯỢNG — cách họ vẽ THỜI GIAN TRÔI ──────────────────────────────────────
   Bằng chứng: một hàng 4 biểu tượng mặt trời–mặt trăng, rồi cảnh sau là hàng 12, và ở cả hai
   cảnh người vẫn đang đi, chỉ khác là vệt dấu chân dài thêm.
   Họ KHÔNG viết "hai tuần sau". Người xem ĐẾM. Đếm thì con số đi vào bằng cảm giác chứ không
   bằng chữ, và cảm giác mới là thứ ở lại sau khi video hết.
   Giới hạn 20 biểu tượng: hơn nữa thì mắt thôi đếm và chuyển sang ước lượng — mất đúng thứ
   khuôn này sinh ra để làm. */
export const Dem: React.FC<{
  W: number; H: number; n: number; ngay: boolean; chu: string; p: number; mau: string;
}> = ({ W, H, n, ngay, chu, p, mau }) => {
  const so = Math.max(1, Math.min(20, n));
  const hien = Math.max(1, Math.round(so * Math.min(1, p / 0.55)));
  const r = Math.min(H * 0.052, (W * 0.90) / so / 2.3);
  const b = W * 0.90 / so;
  const x0 = W * 0.05 + b / 2;
  return (
    <g>
      <rect x="0" y={H * 0.06} width={W} height={r * 2.9} fill="#FFFFFF" opacity={0.88} />
      {Array.from({ length: so }).map((_, i) => {
        const x = x0 + b * i, y = H * 0.06 + r * 1.45;
        const dem = ngay ? i % 2 === 1 : false;
        return (
          <g key={i} opacity={i < hien ? 1 : 0.13}>
            {dem ? (
              <path d={`M ${x + r * 0.34} ${y - r * 0.86} a ${r * 0.86} ${r * 0.86} 0 1 0 0 ${r * 1.72}
                        a ${r * 0.68} ${r * 0.68} 0 1 1 0 ${-r * 1.72} Z`} fill="#8E9BB0" />
            ) : (
              <g><circle cx={x} cy={y} r={r * 0.62} fill="#F0C13C" />
                {[0, 45, 90, 135, 180, 225, 270, 315].map((d) => {
                  const a = (d * Math.PI) / 180;
                  return <line key={d} x1={x + Math.cos(a) * r * 0.78} y1={y + Math.sin(a) * r * 0.78}
                               x2={x + Math.cos(a) * r * 1.02} y2={y + Math.sin(a) * r * 1.02}
                               stroke="#F0C13C" strokeWidth={r * 0.16} strokeLinecap="round" />;
                })}</g>
            )}
          </g>
        );
      })}
      {chu ? (
        <text x={W / 2} y={H * 0.06 + r * 3.9} textAnchor="middle" fontFamily={F} fontWeight={800}
              fontSize={Math.min(H * 0.040, (W * 0.8 / Math.max(1, chu.length)) * 1.7)}
              fill={mau}>{chu}</text>
      ) : null}
    </g>
  );
};

/* ── THẺ CHỮ — khi lời chuyển từ KỂ sang KHẲNG ĐỊNH ───────────────────────────────────────
   Bằng chứng: giữa một loạt cảnh có nhân vật, đột nhiên một tấm thẻ giấy da chỉ có hai dòng
   chữ, không hình gì cả.
   Chỗ ấy trong lời kể là chỗ NGƯỜI KỂ ĐƯA RA NHẬN ĐỊNH, không còn mô tả nữa. Cố vẽ minh hoạ
   cho một nhận định thì hình sẽ nói một điều cụ thể mà câu không nói — tức là hình đang bịa.
   Bỏ hẳn hình đi mới đúng, và cú dừng hình ấy cũng là một nhịp nghỉ cho tai. */
export const TheChu: React.FC<{
  W: number; H: number; chu: string; p: number; mau: string; nen?: string; bo?: number;
}> = ({ W, H, chu, p, mau, nen = "#F2F0EA", bo = 0 }) => {
  const q = Math.min(1, p / 0.2);
  /* ── XUỐNG DÒNG THAY VÌ THU NHỎ  (3/9/2026) ────────────────────────────────────────────
     Anh: *"long cũng chuẩn ko lỗi nha."* Soi bản dài: thẻ chương là **khối màu trơn với chữ bé
     tí** ở giữa. 11/50 nhịp của bản dài là thẻ chữ — 22% thời lượng trông như một tấm bìa rỗng.

     Đo bằng chính công thức: `fs = min(H·0,115, (W·0,74/dai)·1,62)`. Câu chương *"Could you
     survive a night in a cave"* dài **34 ký tự**, nên nhánh thứ hai thắng:

         min(1080·0,115, (1920·0,74/34)·1,62) = min(124, 67) = **67px** = 3,5% chiều cao

     Bằng đúng cỡ phụ đề. Một thẻ TUYÊN BỐ mà bé bằng phụ đề thì nó không còn là tuyên bố.

     Gốc: công thức chỉ có MỘT cách xử lý câu dài — **thu nhỏ chữ**. Nhưng câu dài thì cách đúng
     là **xuống dòng**, giữ nguyên cỡ. Đây là họ lỗi quen: *một kích thước chịu hai ràng buộc mà
     công thức chỉ mã hoá một* (§6) — ở đây là "vừa bề ngang" và "đủ to để đọc là tuyên bố".

     Nay tự ngắt dòng ở ranh giới TỪ với trần ~16 ký tự/dòng, rồi mới tính cỡ. Chữ giữ được
     tầm vóc, và câu dài chỉ tốn thêm một dòng. */
  const _ngat = (t: string, max = 16): string[] => {
    const tu = t.trim().split(/\s+/);
    const ra: string[] = [];
    let d = "";
    for (const w of tu) {
      if (!d) { d = w; continue; }
      if ((d + " " + w).length <= max) d += " " + w;
      else { ra.push(d); d = w; }
    }
    if (d) ra.push(d);
    return ra.length ? ra : [t];
  };
  const dong = chu.split("|").flatMap((d) => _ngat(d));
  const dai = Math.max(...dong.map((d) => d.length), 1);
  const fs = Math.min(H * 0.135, (W * 0.80 / dai) * 1.62, H * 0.86 / (dong.length * 1.2));
  /* 1/9 — DỰNG LẠI. Bản trước là một HỘP TRẮNG BO GÓC, chữ `Georgia, serif`, gạch chân màu ở
     đáy. Ba thứ ấy đều lạc: cả bộ phim dùng một phông sans đậm, và §12.12 xếp "hộp bo góc" cùng
     "gạch chân màu" vào danh sách dấu hiệu nghiệp dư — người xem đọc ra trong nửa giây.
     Nó cũng làm nhịp chốt trông như một tấm biển dán đè lên phim, đúng thứ luật ấy cấm.
     Nay: lời tuyên bố TRÀN KHUNG trên nền màu kênh — đúng cách các kênh Mỹ hàng đầu đóng một ý.
     Màu chữ chọn bằng đo tương phản, vì màu kênh mỗi kênh một độ sáng. */
  const nenThe = mau;
  const chuThe = chuHopNen("#FFFFFF", nenThe);

  /* ── SÁU BỐ CỤC, KHÔNG MỘT  (3/9/2026) ──────────────────────────────────────────────────
     Anh gửi hai khung và nói: *"2 loại này a thấy xấu nhàm chán mà nó cứ lặp đi lặp lại cùng
     1 motip hoài."* Đúng, và đây là lời phê nặng hơn mọi lỗi kỹ thuật hôm nay.

     Một bản dài có **10 thẻ chương**, cộng thẻ mở và thẻ chốt — tức khoảng 22% thời lượng là
     khuôn này. Trước bản này cả 12 lần đều là MỘT hình: khối màu trơn, chữ trắng, canh giữa.
     Bóng đổ với tấm nền em thêm sáng nay làm nó đẹp hơn nhưng **không đổi mô-típ** — người xem
     vẫn thấy đúng một tấm bìa lặp mười hai lần.

     Sáu bố cục dưới đây khác nhau ở thứ mắt đọc TRƯỚC chữ: **trọng tâm nằm đâu, nền chiếm bao
     nhiêu, chữ canh bên nào**. Đổi màu hay đổi phông không giải quyết được gì — người xem nhận
     ra bố cục, không nhận ra sắc độ.

     `bo` truyền vào là `hạt + chỉ số nhịp`, KHÔNG phải `hạt` của tập: chỉ theo tập thì mười
     thẻ trong CÙNG một video vẫn giống hệt nhau — đúng cái vừa bị phê. (Luật 14.9.)

     Số chương tách khỏi tiêu đề để ba bố cục dùng nó làm phần tử hình: chữ số cỡ lớn là hình
     khối mạnh nhất có sẵn mà không tốn một lượt vẽ nào. */
  const co_so = /^\s*\d+\.?\s*$/.test((chu.split("|")[0] || ""));
  const soCh = co_so ? chu.split("|")[0].trim().replace(/\.$/, "") : "";
  const dongT = co_so ? chu.split("|").slice(1).flatMap((d) => _ngat(d)) : dong;
  const daiT = Math.max(...dongT.map((d) => d.length), 1);
  const k6 = Math.abs(bo) % 6;
  const vao = 0.97 + q * 0.03;
  const chuSang = chuHopNen("#FFFFFF", mau);
  const chuToi = chuHopNen("#2C2722", nen);

  /* Cỡ chữ tính lại theo BỀ NGANG THẬT mỗi bố cục cho phép — bố cục canh trái chỉ có 0,80·W,
     bố cục có đĩa số chỉ còn 0,62·W. Dùng chung một cỡ thì bố cục hẹp sẽ tràn. */
  const coChu = (rong: number, sodong: number) =>
    Math.min(H * 0.135, (W * rong / daiT) * 1.62, (H * 0.80) / (sodong * 1.2));

  const khoi = (x: number, y: number, neo: "middle" | "start", fsz: number, mauChu: string) => (
    <g transform={`translate(${x} ${y}) scale(${vao})`}>
      {dongT.map((d, i) => (
        <text key={i} x="0" y={(i - (dongT.length - 1) / 2) * fsz * 1.16 + fsz * 0.34}
              textAnchor={neo} fontFamily={F} fontWeight={900}
              fontSize={fsz} fill={mauChu} letterSpacing={fsz * 0.005}>{d.trim()}</text>
      ))}
    </g>
  );

  if (k6 === 1 && soCh) {
    /* SỐ KHỔNG LỒ LÀM NỀN — chữ số cao gần hết khung, mờ, lệch phải; tiêu đề canh trái đè lên.
       Đây là bố cục tạp chí: một phần tử rất lớn rất nhạt giữ khung, chữ nhỏ hơn cầm nội dung. */
    const fsz = coChu(0.78, dongT.length);
    return (
      <g opacity={q}>
        <rect x={0} y={0} width={W} height={H} fill={mau} />
        <text x={W * 0.99} y={H * 0.98} textAnchor="end" fontFamily={F} fontWeight={900}
              fontSize={H * 1.28} fill={chuSang} opacity={0.13}>{soCh}</text>
        {khoi(W * 0.08, H * 0.5, "start", fsz, chuSang)}
      </g>
    );
  }
  if (k6 === 2) {
    /* DẢI MÀU GIỮA KHUNG — căn phòng vẫn thấy ở trên và dưới, nên thẻ không cắt đứt mạch phim.
       Đây là bố cục duy nhất giữ được bối cảnh, nên nó là chỗ nghỉ mắt giữa các thẻ tràn màu. */
    const cao = H * 0.46, y0 = (H - cao) / 2;
    /* SỐ NẰM TRONG DẢI, KHÔNG ĐỨNG NGOÀI.  Bản đầu đặt nó phía trên mép dải ở cỡ 0,075·H —
       soi khung ra một chữ số bé xíu lửng lơ, đọc như vết bẩn chứ không như số chương. Số
       chương là phần tử hình, nên nó phải có KHỐI LƯỢNG: đưa vào trong dải, cỡ gần nửa chiều
       cao dải, và chữ tiêu đề lùi sang phải nhường chỗ. */
    const rSo = soCh ? W * 0.155 : 0;
    const fsz = Math.min(coChu(soCh ? 0.68 : 0.84, dongT.length), (cao * 0.80) / (dongT.length * 1.2));
    return (
      <g opacity={q}>
        <rect x={0} y={y0} width={W} height={cao} fill={mau} />
        {soCh ? (
          <>
            <text x={W * 0.055} y={y0 + cao * 0.5 + cao * 0.22} fontFamily={F} fontWeight={900}
                  fontSize={cao * 0.62} fill={chuSang} opacity={0.42}>{soCh}</text>
            <line x1={rSo} y1={y0 + cao * 0.20} x2={rSo} y2={y0 + cao * 0.80}
                  stroke={chuSang} strokeWidth={Math.max(2, W * 0.0016)} opacity={0.42} />
          </>
        ) : null}
        {khoi(rSo + (W - rSo) / 2, y0 + cao / 2, "middle", fsz, chuSang)}
      </g>
    );
  }
  if (k6 === 3) {
    /* NỀN SÁNG, LUẬT MÀU DÀY — chữ mực đậm trên nền phòng, một vạch màu dày phía trên.
       Nhẹ nhất trong sáu bố cục; đặt xen giữa các thẻ tràn màu thì cả loạt bớt nặng. */
    const fsz = coChu(0.82, dongT.length);
    const yT = H * 0.52;
    return (
      <g opacity={q}>
        <rect x={0} y={0} width={W} height={H} fill={nen} />
        <rect x={W * 0.09} y={yT - fsz * (dongT.length * 0.62) - H * 0.085}
              width={W * 0.20 * Math.min(1, q * 1.6)} height={H * 0.017} fill={mau} />
        {/* EYEBROW CÓ CHỮ, KHÔNG PHẢI MỘT CHỮ SỐ TRẦN.
            Thử hai lần: cỡ 0,042·H rồi 0,072·H — cả hai lần soi khung đều ra một vết nhỏ khó
            hiểu bên trên vạch màu. Vấn đề không phải CỠ mà là NGHĨA: một chữ số đứng một mình
            không nói nó là số gì, nên mắt bỏ qua nó như một vết bẩn. Phóng to chỉ làm vết bẩn
            to hơn.
            `CHAPTER 2` giãn chữ là khuôn eyebrow của báo in — đọc ra ngay là một nhãn, và ở cỡ
            nhỏ vẫn đúng vai vì vai của nó là NHÃN, không phải tiêu đề. */}
        {soCh ? (
          <text x={W * 0.09} y={yT - fsz * (dongT.length * 0.62) - H * 0.034}
                fontFamily={F} fontWeight={900} fontSize={H * 0.040}
                fill={mau} letterSpacing={H * 0.010}>{`CHAPTER ${soCh}`}</text>
        ) : null}
        {khoi(W * 0.09, yT, "start", fsz, chuToi)}
      </g>
    );
  }
  if (k6 === 4) {
    /* NÊM CHÉO — mảng màu cắt chéo từ đáy trái. Đường chéo là thứ duy nhất trong cả bộ khuôn
       không nằm ngang hay dọc, nên nó phá nhịp mạnh nhất. Dùng thưa. */
    const fsz = coChu(0.72, dongT.length);
    return (
      <g opacity={q}>
        <rect x={0} y={0} width={W} height={H} fill={nen} />
        <path d={`M 0 ${H * 0.16} L ${W} ${H * -0.06} L ${W} ${H} L 0 ${H} Z`} fill={mau} />
        {soCh ? (
          <text x={W * 0.08} y={H * 0.40} fontFamily={F} fontWeight={900}
                fontSize={H * 0.085} fill={chuSang} opacity={0.55}>{soCh}</text>
        ) : null}
        {khoi(W * 0.08, H * 0.64, "start", fsz, chuSang)}
      </g>
    );
  }
  if (k6 === 5 && soCh) {
    /* ĐĨA SỐ BÊN TRÁI — số trong một đĩa màu lớn, tiêu đề canh trái bên phải trên nền sáng.
       Bố cục "chương sách": mắt đọc số trước, rồi mới sang chữ. */
    const r = Math.min(H * 0.26, W * 0.17);
    const cx = W * 0.20, cy = H * 0.5;
    const fsz = Math.min(coChu(0.58, dongT.length), H * 0.11);
    return (
      <g opacity={q}>
        <rect x={0} y={0} width={W} height={H} fill={nen} />
        <circle cx={cx} cy={cy} r={r * (0.9 + q * 0.1)} fill={mau} />
        <text x={cx} y={cy + r * 0.36} textAnchor="middle" fontFamily={F} fontWeight={900}
              fontSize={r * 1.05} fill={chuSang}>{soCh}</text>
        {khoi(cx + r * 1.30, cy, "start", fsz, chuToi)}
      </g>
    );
  }
  /* BỐ CỤC GỐC — tràn màu, chữ canh giữa. Vẫn là bố cục mạnh nhất, nên nó giữ chỗ mặc định
     và là chỗ rơi về khi một bố cục cần số mà thẻ ấy không có số (thẻ tuyên bố giữa phim). */
  return (
    <g opacity={q}>
      <rect x={0} y={0} width={W} height={H} fill={nenThe} />
      <g transform={`translate(${W / 2} ${H / 2}) scale(${vao})`}>
        {dong.map((d, i) => (
          <text key={i} x="0" y={(i - (dong.length - 1) / 2) * fs * 1.16 + fs * 0.34}
                textAnchor="middle" fontFamily={F} fontWeight={900}
                fontSize={fs} fill={chuThe} letterSpacing={fs * 0.005}>{d.trim()}</text>
        ))}
      </g>
    </g>
  );
};

/* ── KHUÔN 8: BIỂU ĐỒ CỘT ĐỘNG ────────────────────────────────────────────────────────────
   Anh: *"+ chart biểu đồ + số liệu động animation là đẹp hay."*

   Ba thứ làm nên một biểu đồ đọc được trong 2 giây — và cả ba đều là chuyện NHỊP, không phải
   chuyện màu:
     · cột MỌC LÊN chứ không hiện sẵn: mắt bám theo cái đang chuyển động, nên cột mọc chính là
       thứ dẫn mắt vào biểu đồ. Hiện sẵn thì người xem phải tự tìm chỗ bắt đầu.
     · con số ĐẾM LÊN theo cột: số nhảy dần thì người xem cảm được ĐỘ LỚN, không chỉ đọc chữ.
     · cột lớn nhất TÔ MÀU NHẤN, còn lại xám: ở 2 giây không ai so được năm cột cùng màu.
   Không có lưới, không có trục tung. Ở khung điện thoại thì lưới chỉ là nhiễu. */
/* BẬC ĐƠN VỊ ĐẦY ĐỦ. Bản trước chỉ có MỘT nhánh: `>= 1000 -> chia 1000 + "K"`. Nên một tỉ hiện
   ra là `1000000.0K` — vô nghĩa, và đúng ngay ở kênh HOW MUCH IS A BILLION nơi con số tỉ là cả
   nội dung. Cùng họ lỗi đã trả giá ở `_lau()` bên `giai_thich.py`: *bảng nhánh cố định luôn có
   một trần, và trên trần ấy mọi thứ hiện ra sai*. Thang phải LEO, không dừng ở một bậc. */
const _bac = (v: number): string => {
  const a = Math.abs(v);
  const B = [[1e12, "T"], [1e9, "B"], [1e6, "M"], [1e3, "K"]] as [number, string][];
  for (const [m, k] of B) {
    if (a >= m) {
      const x = v / m;
      return (Math.abs(x) >= 100 ? Math.round(x) : +x.toFixed(1)).toLocaleString() + k;
    }
  }
  return Math.round(v).toLocaleString();
};

/* ── BIỂU ĐỒ CỘT  (nâng cấp 3/9/2026) ───────────────────────────────────────────────────────
   Soi lưới HOW LOUD: trục đúng, số đúng, mà đọc ra "bảng tính", không đọc ra "một cảnh phim".
   Ba thứ thiếu, cả ba là thứ mọi kênh đầu bảng đều có:

   · **cột không nổi bật vẽ bằng xám chết `#B8B2A6`** — một màu không có mặt ở đâu khác trong
     khung. Nay pha từ chính màu thương hiệu: cùng một bảng màu, chỉ nhạt đi. Đây đúng lỗi
     "mượn một giá trị cho việc nó không sinh ra để làm" ở luật số 6, phiên bản màu sắc.
   · **không có đường lưới** — mắt không ước lượng được cột thứ ba bằng bao nhiêu phần cột đầu.
     Ba đường mảnh là đủ; nhiều hơn thì thành giấy kẻ ô.
   · **cột không chạm sàn** — không có bóng tiếp đất nên nó dán lên phòng chứ không đứng trong
     phòng. Cùng thứ đã sửa cho chủ thể ở `KichGiaiThich`.

   `hat` đổi bo góc và độ đậm lưới theo TẬP, để hai tập liền nhau không ra một tấm ảnh. */
export const Chart: React.FC<{
  W: number; H: number; cot: { nhan: string; v: number }[]; don: string;
  mau: string; mauPhu: string; p: number; nen?: string; hat?: number;
}> = ({ W, H, cot, don, mau, mauPhu, p, nen = "#F2F0EA", hat = 0 }) => {
  if (!cot.length) return null;
  const max = Math.max(...cot.map((c) => Math.abs(c.v)), 1);
  const dinh = cot.reduce((a, b) => (Math.abs(b.v) > Math.abs(a.v) ? b : a), cot[0]);
  const yDay = H * 0.80, cao = H * 0.52;
  const b = (W * 0.86) / cot.length;
  const x0 = W * 0.07;
  const q = Math.min(1, p / 0.5);
  const cn = Math.min(H * 0.038, (b * 0.92 / Math.max(...cot.map((c) => c.nhan.length), 1)) * 1.6);
  const kk = Math.abs(hat) % 3;
  const nhat = _pha(_tron(nen, mau, 0.34), -0.10);   // cột phụ: cùng bảng màu, chỉ nhạt hơn
  const bo = W * (kk === 1 ? 0.002 : kk === 2 ? 0.012 : 0.006);
  return (
    <g>
      {/* Ba đường lưới, đặt SAU cột nên không cắt ngang mặt cột. */}
      {[0.25, 0.5, 0.75].map((f, i) => (
        <line key={`l${i}`} x1={x0} y1={yDay - cao * f} x2={x0 + b * cot.length} y2={yDay - cao * f}
              stroke={_pha(nen, -0.24)} strokeWidth={Math.max(1, H * 0.0016)}
              opacity={(kk === 2 ? 0.5 : 0.8) * q} />
      ))}
      {cot.map((c, i) => {
        // Mỗi cột mọc lệch pha 0,06 -> mắt đọc được THỨ TỰ, không thấy cả rừng bật lên cùng lúc.
        const qi = Math.max(0, Math.min(1, (q - i * 0.06) / 0.55));
        /* SÀN CHIỀU CAO. Tỉ lệ 1000× làm cột nhỏ cao 0,1% — biến mất hẳn, và người xem đọc ra
           "thiếu cột" chứ không đọc ra "cột này bé đến thế". Giữ thang TUYẾN TÍNH (chính sự
           chênh lệch ấy là thông điệp) nhưng cho cột một sàn mỏng để nó còn hiện diện. */
        const h = Math.max(cao * (Math.abs(c.v) / max), H * 0.006) * qi;
        const x = x0 + b * i + b * 0.14;
        const w = b * 0.72;
        const la = c === dinh;
        const so = c.v * qi;
        const cs = Math.min(H * 0.042, (w / Math.max(2, `${Math.round(so)}`.length)) * 1.5);
        return (
          <g key={i}>
            <ellipse cx={x + w / 2} cy={yDay + H * 0.008} rx={w * 0.54} ry={H * 0.009}
                     fill="#000000" opacity={0.15 * qi} />
            <rect x={x} y={yDay - h} width={w} height={h} rx={bo}
                  fill={la ? mau : nhat} stroke="#2C2722" strokeWidth={Math.max(2, H * 0.004)} />
            <text x={x + w / 2} y={yDay - h - H * 0.018} textAnchor="middle" fontFamily={F}
                  fontWeight={900} fontSize={cs} fill={la ? mau : _pha(mau, -0.34)} opacity={qi}>
              {_bac(so)}
            </text>
            <text x={x + w / 2} y={yDay + H * 0.055} textAnchor="middle" fontFamily={F}
                  fontWeight={800} fontSize={cn} fill="#3A342C">{c.nhan}</text>
          </g>
        );
      })}
      <line x1={x0} y1={yDay} x2={x0 + b * cot.length} y2={yDay}
            stroke="#2C2722" strokeWidth={Math.max(3, H * 0.006)} />
      {don ? (
        <text x={W / 2} y={H * 0.145} textAnchor="middle" fontFamily={F} fontWeight={800}
              fontSize={Math.min(H * 0.042, (W * 0.8 / Math.max(1, don.length)) * 1.7)}
              fill={mauPhu} letterSpacing={2}>{don.toUpperCase()}</text>
      ) : null}
    </g>
  );
};
