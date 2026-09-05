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
/* ── 5/9 (chốt) — NỀN TRẮNG ────────────────────────────────────────────────────────────
   Anh: *"videos e dùng hết nền trắng đi cho a, a thấy nền trắng đẹp"* — và năm ảnh mẫu
   anh gửi đều là NÉT ĐEN TRÊN TRẮNG, không một tấm nào có giấy.
   Nền trắng giải luôn ba thứ đã cãi nhau suốt buổi: hết chuyện giấy sáng hay tối, hết
   chuyện chữ trắng viền đen hay mực nâu (trên trắng thì mực đen là hiển nhiên), và hết
   chuyện tranh cảnh tô màu chửi nhau với nền.
   Giữ nguyên tên `TrangGiay` và công tắc `datGiay` để không phải sửa 21 chỗ gọi — thứ đổi
   là BỀ MẶT, không phải kiến trúc. Bảng kraft vẫn nằm trong lịch sử git nếu cần lấy lại. */
/* ── 5/9 (chốt lại) — GIẤY NÂU SÁNG, MÀU ĐO TỪ 20 TẤM ANH NHẤN SAO ────────────────────
   Anh: *"nền trắng hơi rẻ tiền, e làm nền brown paper"*.
   Không đoán màu nữa: em tải 20 tấm anh đã nhấn sao trên Canva rồi đo pixel —

       trung bình RGB (234, 215, 192) · độ sáng 218 · nhám (độ lệch) 6,7

   Đó là lý do bảng kraft trước anh chê TỐI: em dùng #C9A87C (sáng ~170), tối hơn gu anh
   chọn tới 48 mức. Nay lấy đúng con số đo được, và giữ nhám ở mức thấp đúng như đo. */
export const TrangGiay: React.FC<{
  W: number; H: number; nen: string; mau: string; hat?: number;
}> = ({ W, H, hat = 0 }) => {
  const id = `g${Math.abs(hat) % 89}`;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}
         style={{ position: "absolute", left: 0, top: 0 }}>
      <defs>
        <filter id={`${id}t`} x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" seed={hat % 50} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <filter id={`${id}v`} x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.007" numOctaves="3" seed={(hat + 9) % 50} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
      </defs>
      <rect x={0} y={0} width={W} height={H} fill="#EAD7C0" />
      <rect x={0} y={0} width={W} height={H} filter={`url(#${id}v)`}
            opacity={0.06} style={{ mixBlendMode: "multiply" }} />
      <rect x={0} y={0} width={W} height={H} filter={`url(#${id}t)`}
            opacity={0.13} style={{ mixBlendMode: "multiply" }} />
    </svg>
  );
};
