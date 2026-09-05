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

export const TrangGiay: React.FC<{
  W: number; H: number; nen: string; mau: string; hat?: number;
}> = ({ W, H, nen, mau, hat = 0 }) => {
  const id = `giay${Math.abs(hat) % 97}`;
  const le = W * 0.085;                       // lề trái, tỉ lệ sổ tay thật
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}
         style={{ position: "absolute", left: 0, top: 0 }}>
      <defs>
        {/* Thớ giấy: tần số CAO + biên độ NHỎ. Tần số thấp cho ra vân đá, không phải giấy. */}
        <filter id={`${id}tho`} x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={4} seed={hat % 50} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
      </defs>

      {/* 1 — mặt giấy phẳng. MỘT màu, không gradient: gradient là ánh sáng, ánh sáng là phòng. */}
      <rect x={0} y={0} width={W} height={H} fill={nen} />

      {/* 2 — thớ. `multiply` để nó ăn vào giấy chứ không nằm đè lên như một lớp sương. */}
      <rect x={0} y={0} width={W} height={H} filter={`url(#${id}tho)`}
            opacity={0.14} style={{ mixBlendMode: "multiply" }} />

      {/* 3 — mép trang: hơi run, hơi lệch tâm, rất nhạt. Đủ để mắt biết đây là một TRANG. */}
      <path d={_run(W * 0.035, H * 0.022, W * 0.965, H * 0.022, W * 0.0012, hat)}
            stroke="#2C2722" strokeWidth={Math.max(1, W * 0.0012)} fill="none" opacity={0.13} />
      <path d={_run(W * 0.035, H * 0.978, W * 0.965, H * 0.978, W * 0.0012, hat + 11)}
            stroke="#2C2722" strokeWidth={Math.max(1, W * 0.0012)} fill="none" opacity={0.13} />

      {/* 4 — vạch lề màu kênh. Chỗ DUY NHẤT màu kênh chạm vào nền. */}
      <path d={_run(le, H * 0.022, le, H * 0.978, W * 0.0010, hat + 5)}
            stroke={mau} strokeWidth={Math.max(1.5, W * 0.0018)} fill="none" opacity={0.30} />
    </svg>
  );
};
