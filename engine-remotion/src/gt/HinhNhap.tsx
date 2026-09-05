import React from "react";
import { KHO_SVG } from "./KhoSVG";

/* ══════════════════════════════════════════════════════════════════════════════════════
   HÌNH VẼ NHẬP TỪ KHO NGOÀI  (5/9/2026)

   Anh: *"tải file Vector (.SVG) về rồi import vào template của e chỉnh sửa lại cho chuẩn
   đẹp"*. Đây là phía engine; phía tải và chuẩn hoá nằm ở `render-pipeline/tai_svg.py`
   (đọc docstring ở đó cho phần giấy phép và vì sao không dùng Freepik/Vecteezy).

   Khoảng cách mà nó vá: nét vector mình tự vẽ là HÌNH QUE, và `nguoi` chiếm **54%** số
   nhịp có biểu tượng. Đó là chỗ người xem đọc ra "nghiệp dư" nhanh nhất, và cũng là chỗ
   không cách nào vẽ tay đẹp hơn bằng code trong thời gian hợp lý.

   ── BỐN QUYẾT ĐỊNH, VÀ VÌ SAO ─────────────────────────────────────────────────────────

   1. `dangerouslySetInnerHTML` chứ không dựng lại thành phần tử React.
      Ruột SVG đã được `tai_svg.py` làm sạch ở khâu TẢI: bỏ `<style>`, bỏ `<image>`, bỏ chú
      thích, chỉ giữ thẻ hình. Nội dung không đến từ người dùng và không đổi lúc chạy, nên
      không có đường tiêm nào. Dựng lại thành phần tử React thì phải viết một bộ phân tích
      SVG — thêm một chỗ để sai, đổi lấy không gì.

   2. Nét tự vẽ chạy bằng CSS, không bằng `TuVe`.
      `TuVe` đi qua cây React, mà nhánh này không có cây React để đi. Nhưng `tai_svg.py` đã
      chèn `pathLength="1"` vào MỌI thẻ hình, nên một luật CSS trên thẻ cha là đủ:
      chiều dài đường nào cũng bằng 1, nên `stroke-dashoffset` dùng chung một con số.
      Hai đường vẽ (React và CSS) cho cùng một kết quả — đó là lý do chèn `pathLength` ở
      khâu tải chứ không ở khâu dựng.

   3. Màu thay bằng màu KÊNH.
      Giữ bảng tím-xanh gốc của unDraw thì mười tám kênh dùng chung một bảng màu, tức mất
      đúng trục bản sắc vừa dựng (§14.5). `MUC` giữ nguyên tông mực tối của cả bộ để hình
      nhập và cảnh mình vẽ cùng một chất nét.

   4. Hình nhập KHÔNG có nét mực bao ngoài như hình mình vẽ.
      unDraw vẽ bằng MẢNG MÀU, không bằng viền. Ép thêm viền vào là làm hỏng chất của nó và
      cũng không khớp — nên chỗ hoà hai chất liệu nằm ở BẢNG MÀU (điểm 3) và ở hiệu ứng vẽ
      (điểm 2), không nằm ở viền.
   ══════════════════════════════════════════════════════════════════════════════════════ */

/* Làm tối một mã màu về mức "vùng tối của tranh" — không về đen. */
const _toi = (hex: string): string => {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m) return "#3A3540";
  /* 0,34 + 18 (bản đầu) cho ra #223741 với màu phụ của THE RULES — đúng là "tối" nhưng ở
     cỡ tán cây trong khung dọc thì mắt đọc ra MỘT LỖ ĐEN, không đọc ra tán cây. Vùng tối
     của tranh minh hoạ phải còn thấy được màu; 0,55 + 44 giữ đúng vai ấy. */
  const v = [0, 2, 4].map((i) => Math.round(parseInt(m[1].slice(i, i + 2), 16) * 0.55) + 44);
  return "#" + v.map((x) => Math.min(255, x).toString(16).padStart(2, "0")).join("");
};

/* Pha một mã màu về phía tối (k<0) hoặc sáng (k>0). */
const _pha = (hex: string, k: number): string => {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m) return hex;
  const v = [0, 2, 4].map((i) => {
    const x = parseInt(m[1].slice(i, i + 2), 16);
    return Math.max(0, Math.min(255, Math.round(k < 0 ? x * (1 + k) : x + (255 - x) * k)));
  });
  return "#" + v.map((x) => x.toString(16).padStart(2, "0")).join("");
};

export const co_hinh_nhap = (bt: string): boolean => !!(KHO_SVG as any)[bt]?.length;

export const HinhNhap: React.FC<{
  bt: string; s: number; bien?: number; p?: number;
  mau: string; mauPhu?: string; nen?: string;
}> = ({ bt, s, bien = 0, p = 1, mau, mauPhu = "", nen = "#F2F0EA" }) => {
  const ds = (KHO_SVG as any)[bt] as { ten: string; vb: string; ruot: string }[] | undefined;
  if (!ds || !ds.length) return null;
  const h = ds[Math.abs(bien) % ds.length];

  const [, , vw, vh] = h.vb.split(/\s+/).map(Number);
  /* Vừa hộp `s × s` theo cạnh DÀI, không theo cạnh ngang: hình unDraw có tỉ lệ rất khác
     nhau (888×677 · 840×736), và kẹp theo một cạnh thì cạnh kia tràn. Cùng bài học §17.2. */
  const k = s / Math.max(vw || 1, vh || 1);

  const q = Math.max(0, Math.min(1, p));
  const m = q <= 0.28 ? 0 : Math.min(1, (q - 0.28) / 0.72);

  /* Năm vai do `tai_svg._vai()` phân loại — xem docstring ở đó. Mỗi vai một màu của
     BẢNG MÌNH, nên hình nhập về mang màu kênh chứ không mang bảng tím-xanh của unDraw. */
  const ruot = h.ruot
    .replace(/\{CHINH\}/g, mau)
    .replace(/\{TOI\}/g, _toi(mauPhu || mau))
    .replace(/\{XAM\}/g, _pha(nen, -0.18))
    .replace(/\{NHAT\}/g, nen)
    .replace(/\{DA\}/g, "#D9A98D")
    /* Bắt mọi vai LẠ về màu nhạt thay vì để chuỗi `{X}` lọt ra thành màu không hợp lệ —
       trình duyệt bỏ qua fill hỏng và vẽ ĐEN, tức đúng lỗi vừa đi sửa. Thêm một vai ở
       `tai_svg.py` mà quên nối ở đây thì hỏng mềm, không hỏng thành mảng đen. */
    .replace(/\{[A-Z0-9_]+\}/g, nen);

  const id = `hn${bt}${Math.abs(bien) % 97}`;
  return (
    <g transform={`translate(${-vw * k / 2} ${-vh * k / 2}) scale(${k})`}>
      <style>{`#${id} *{stroke-dasharray:1;stroke-dashoffset:${(1 - q).toFixed(4)};`
             + `fill-opacity:${m.toFixed(4)};stroke:#2C2722;stroke-width:${(1.6 / k).toFixed(3)}}`}</style>
      <g id={id} dangerouslySetInnerHTML={{ __html: ruot }} />
    </g>
  );
};
