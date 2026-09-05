import React from "react";

/* ══════════════════════════════════════════════════════════════════════════════════════
   NÉT TỰ VẼ RA — hiệu ứng "whiteboard / doodle"  (5/9/2026)

   Anh gửi mô tả cách các kênh doodle đời đầu làm: nạp tệp `.SVG`, phần mềm đọc ĐƯỜNG ĐI
   (path) của hình rồi cho một bàn tay giả chạy theo đúng nét ấy. Ba phần mềm được nêu
   (VideoScribe · Doodly · Vyond) đều là ứng dụng desktop có giao diện — không chạy được
   trên GitHub Actions, nên chúng không dùng được cho dây chuyền này dù có bản quyền.

   Nhưng KỸ THUẬT thì hợp hệ mình hơn cả chúng, vì mình không phải đi *nạp* tệp SVG: mọi
   hình trong `CanhVe` · `BieuTuong` · `Khuon` VỐN ĐÃ là đường SVG do chính mình vẽ ra.
   Thứ duy nhất còn thiếu là bảo chúng hiện dần theo nét.

   ── Vì sao không cần đo chiều dài đường ────────────────────────────────────────────────
   Cách thường gặp là `path.getTotalLength()` rồi đặt `stroke-dasharray`. Cách ấy cần DOM
   thật, mà Remotion dựng khung bằng SSR nên nó hoặc không chạy, hoặc chạy chậm và khác
   nhau giữa hai máy — đúng loại lỗi "test ở máy anh được, Actions thì không" mà §8 cấm.

   SVG có sẵn lối ra: thuộc tính `pathLength` KHAI LẠI chiều dài của đường theo đơn vị mình
   chọn. Đặt `pathLength={1}` thì mọi đường — dài ngắn, thẳng cong — đều có chiều dài 1, nên
   `strokeDasharray={1}` + `strokeDashoffset={1-p}` cho ra đúng "vẽ được p phần trăm nét",
   không cần đo gì, không cần DOM.

   ── Nét trước, màu sau ─────────────────────────────────────────────────────────────────
   Video doodle thật luôn theo thứ tự ấy: bút đi hết nét rồi màu mới đổ vào. Nếu màu hiện
   cùng lúc với nét thì mắt không đọc ra "đang được vẽ", nó đọc ra "hình đang mờ dần vào" —
   hai cảm giác khác hẳn nhau, và cái sau là thứ mọi template rẻ tiền đều làm.
   Nên `fillOpacity` chỉ bắt đầu lên khi nét đã đi được `MOC_MAU`.

   ── Giới hạn đã biết, ghi ra để phiên sau không đi tìm lại ──────────────────────────────
   · Chỉ bảy thẻ hình học nhận `pathLength`; `<text>` · `<image>` · `<use>` thì không —
     chúng được cho hiện theo `fillOpacity` như cũ, không có nét chạy.
   · KHÔNG có bàn tay cầm bút. Đặt bàn tay đúng đầu nét cần `getPointAtLength()`, tức cần
     DOM — đúng thứ vừa tránh ở trên. Nét tự chạy đã là phần người xem đọc ra; bàn tay là
     phần trang trí, và trả giá bằng một phụ thuộc DOM thì không đáng.
   ══════════════════════════════════════════════════════════════════════════════════════ */

/* Bảy thẻ SVG chấp nhận `pathLength`. Danh sách này là của CHUẨN SVG, không phải một lựa
   chọn của mình — nên nó không nở ra theo thời gian như một danh sách ngoại lệ (§13.9). */
const NHAN_NET = new Set(["path", "line", "polyline", "polygon", "circle", "ellipse", "rect"]);

/* ── NÉT PHẢI XONG SỚM  (5/9/2026, sau khi soi lưới) ────────────────────────────────────
   Bản đầu: nét xong ở 42% nhịp, màu bắt đầu ở 55% quãng vẽ. Soi lưới ba khung thì hai khung
   gần như TRỐNG — không phải hỏng, mà là bắt đúng lúc đang vẽ dở.
   Với nhịp trung vị 2,3 giây thì "42% nhịp" là **gần một giây khung chưa hoàn chỉnh** ở MỌI
   nhịp. Người xem lướt qua một short 20 giây không có một giây nào để cho.
   Hiệu ứng vẽ tay chỉ cần đủ để mắt BẮT ĐƯỢC động tác, không cần đủ để xem nó vẽ. */
const MOC_MAU = 0.28;      // nét đi được 28% quãng thì màu bắt đầu đổ vào

export const TuVe: React.FC<{ p: number; children: React.ReactNode; tat?: boolean }> =
({ p, children, tat = false }) => {
  const q = Math.max(0, Math.min(1, p));
  /* Màu đổ vào sau nét, và đổ trong 45% còn lại. Ở `q >= 1` phải ra ĐÚNG 1 — thiếu điều
     đó thì mọi hình đứng mãi ở độ mờ 0,98 và cả tập trông như bị phủ sương. */
  const m = q <= MOC_MAU ? 0 : Math.min(1, (q - MOC_MAU) / (1 - MOC_MAU));

  const di = (n: React.ReactNode): React.ReactNode =>
    React.Children.map(n, (c) => {
      if (!React.isValidElement(c)) return c;
      const kieu = c.type;
      const props: any = c.props || {};
      const con = props.children != null ? di(props.children) : props.children;
      if (typeof kieu === "string" && NHAN_NET.has(kieu)) {
        return React.cloneElement(c as any, {
          pathLength: 1,
          strokeDasharray: 1,
          strokeDashoffset: 1 - q,
          /* `fillOpacity` NHÂN với cái đã có, không ghi đè: nhiều hình trong `CanhVe` cố ý
             để `opacity` thấp (bóng, mảng xa). Ghi đè là xoá mất chiều sâu đã dựng. */
          fillOpacity: (props.fillOpacity ?? 1) * m,
        }, con);
      }
      return React.cloneElement(c as any, {}, con);
    });

  return <>{tat ? children : di(children)}</>;
};
