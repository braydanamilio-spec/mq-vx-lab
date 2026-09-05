import React from "react";

/* ══ NỀN TRANG GIẤY — TEMPLATE MỚI, KHÔNG PHẢI BẢN VÁ CỦA CÁI CŨ  (5/9/2026) ══════════════
   Anh: *"sao vẫn dùng template cũ, a muốn đổi hẳn template cách làm, và nền là paper"* —
   và trước đó: *"kêu làm mới hoàn toàn sao vẫn kiểu cũ vậy"*.

   Anh đúng, và §2 của tệp luật nói thẳng điều em bỏ qua: *sửa vòng thứ ba mà vẫn cùng một
   họ lỗi thì dừng lại, đi tìm thứ cả ba cùng dùng*. Bốn vòng vừa rồi em đổi màu, đổi thẻ
   chữ, đổi tỉ lệ ảnh, bỏ icon — tất cả đều đúng và **không đổi được cái template**, vì thứ
   cả bốn cùng dùng là `NenPhong`: MỌI khung đều là một CĂN PHÒNG.

   Đo trên khung đã dựng: mỗi khung có một đường chân trời, một mặt sàn sẫm hơn tường, một
   quầng sáng hắt từ một phía, và một bóng ê-líp dưới chân mỗi vật. Đó là ngữ pháp của ẢNH
   CHỤP MỘT CĂN PHÒNG. Dán thớ giấy lên nó thì vẫn là căn phòng, chỉ là căn phòng bằng giấy
   — đúng cái anh nhìn ra ngay.

   ── TRANG GIẤY THÌ KHÔNG CÓ GÌ TRONG BỐN THỨ ẤY ─────────────────────────────────────────
   Một trang sổ tay là mặt phẳng. Không chiều sâu, nên:

       không chân trời · không sàn · không nguồn sáng · không bóng đổ dưới chân

   Vật nằm TRÊN trang, không đứng TRONG phòng. Đây là khác biệt về ngữ pháp, không phải về
   sắc độ — và người xem đọc ra BỐ CỤC chứ không đọc ra sắc độ (§15.1 của đợt template).

   ── BỐN LỚP, VÀ KHÔNG LỚP NÀO GIẢ CHIỀU SÂU ────────────────────────────────────────────
   1. nền giấy: một màu phẳng, ngả ấm
   2. thớ giấy: `feTurbulence` tần số cao, biên độ rất nhỏ, nhân `multiply` — thớ thật của
      giấy là NHIỄU, không phải gradient
   3. mép trang: một đường viền mảnh lệch tâm, hơi run — trang giấy có mép, phòng thì không
   4. lề: một vạch dọc màu kênh ở lề trái như sổ tay kẻ sẵn; đây là chỗ DUY NHẤT màu kênh
      xuất hiện trên nền, nên bản sắc vẫn còn mà tông không vỡ

   Không có lớp thứ năm. Mỗi lớp thêm vào là một cơ hội để trang giấy lại thành căn phòng. */

/** Bật/tắt nền giấy cho cả lượt dựng. Đặt MỘT LẦN ở component gốc — cùng cách `datChu` làm,
 *  vì luồn một prop qua 21 chỗ dùng `NenPhong` là 21 cơ hội để quên một chỗ. */
let _giay = false;
export const datGiay = (b: boolean): void => { _giay = b; };
export const laGiay = (): boolean => _giay;

/** Nét run nhẹ cho một đường thẳng — mép giấy và vạch lề đều do tay kẻ, không do máy. */
const _run = (x1: number, y1: number, x2: number, y2: number, bien: number, hat: number) => {
  const n = 8;
  let d = `M ${x1} ${y1}`;
  for (let i = 1; i <= n; i++) {
    const t = i / n;
    const s = Math.sin((hat + i * 37) * 1.7) * bien;
    d += ` L ${x1 + (x2 - x1) * t + (y2 - y1 ? s : 0)} ${y1 + (y2 - y1) * t + (x2 - x1 ? s : 0)}`;
  }
  return d;
};

/* ── 5/9 (đợt hai) — GIẤY CŨ THẬT, THEO ẢNH MẪU ANH GỬI ────────────────────────────────
   Anh: *"sao ko làm mấy nền giấy kiểu sáng sáng như này"*, kèm một tấm giấy da: TÂM SÁNG ngả
   kem, MÉP ngả nâu, và VỆT Ố loang không đều.

   Bản trước em cố ý làm phẳng MỘT màu, với lý do *"gradient là ánh sáng, ánh sáng là phòng"*.
   Luật ấy quá chặt và em đã áp sai chỗ. Cái dựng nên căn phòng là **chân trời + sàn + đèn hắt
   MỘT PHÍA** — thứ ánh sáng có HƯỚNG. Còn tâm sáng ĐỀU, toả từ giữa ra mép, thì không nói gì
   về hướng cả: đó đúng là cách một tờ giấy cũ bắt sáng, và mắt đọc ra "giấy", không đọc ra
   "phòng". Cấm nhầm một thứ vì nó cùng tên kỹ thuật với thứ khác (§12.5: một luật đúng ở ngữ
   cảnh nó sinh ra, sai ở ngữ cảnh mới).

   Ba tầng, theo đúng thứ tự nhìn thấy trong ảnh mẫu:
     · quầng sáng giữa trang  — radial, TÂM khung, không lệch về phía nào
     · vệt ố                  — nhiễu tần số THẤP, nhân multiply, chỗ đậm chỗ nhạt
     · thớ giấy               — nhiễu tần số CAO, biên độ nhỏ
   Tần số thấp cho ố, tần số cao cho thớ. Dùng một tần số cho cả hai thì ra vân đá. */
export const TrangGiay: React.FC<{
  W: number; H: number; nen: string; mau: string; hat?: number;
}> = ({ W, H, nen, mau, hat = 0 }) => {
  const id = `giay${Math.abs(hat) % 97}`;
  const le = W * 0.085;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}
         style={{ position: "absolute", left: 0, top: 0 }}>
      <defs>
        {/* ố: tần số THẤP -> mảng loang to bằng nắm tay, đúng như giấy ẩm lâu ngày */}
        <filter id={`${id}o`} x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.008 0.013"
                        numOctaves={4} seed={hat % 50} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        {/* thớ: tần số CAO -> hạt mịn */}
        <filter id={`${id}t`} x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.85"
                        numOctaves={3} seed={(hat + 17) % 50} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        {/* quầng sáng giữa trang — TÂM khung, bán kính lớn, chuyển rất mềm */}
        <radialGradient id={`${id}s`} cx="0.5" cy="0.47" r="0.78">
          <stop offset="0%"   stopColor="#FBF4E6" />
          <stop offset="42%"  stopColor="#F2E6CD" />
          <stop offset="78%"  stopColor="#E4CFA8" />
          <stop offset="100%" stopColor="#D8BE90" />
        </radialGradient>
      </defs>

      <rect x={0} y={0} width={W} height={H} fill={`url(#${id}s)`} />
      <rect x={0} y={0} width={W} height={H} filter={`url(#${id}o)`}
            opacity={0.20} style={{ mixBlendMode: "multiply" }} />
      <rect x={0} y={0} width={W} height={H} filter={`url(#${id}t)`}
            opacity={0.10} style={{ mixBlendMode: "multiply" }} />

      {/* mép trang: hơi run, rất nhạt */}
      <path d={_run(W * 0.035, H * 0.022, W * 0.965, H * 0.022, W * 0.0012, hat)}
            stroke="#6B5636" strokeWidth={Math.max(1, W * 0.0012)} fill="none" opacity={0.16} />
      <path d={_run(W * 0.035, H * 0.978, W * 0.965, H * 0.978, W * 0.0012, hat + 11)}
            stroke="#6B5636" strokeWidth={Math.max(1, W * 0.0012)} fill="none" opacity={0.16} />

      {/* vạch lề màu kênh — chỗ duy nhất màu kênh chạm vào nền */}
      <path d={_run(le, H * 0.022, le, H * 0.978, W * 0.0010, hat + 5)}
            stroke={mau} strokeWidth={Math.max(1.5, W * 0.0018)} fill="none" opacity={0.26} />
    </svg>
  );
};
