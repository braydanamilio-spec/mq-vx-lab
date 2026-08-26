/** BIẾN THỂ BỐ CỤC — để nhiều kênh dùng CHUNG một dạng vẫn không nhìn giống nhau.
 *
 * 26/8 — đo thật 50 kênh mới: màu chính 50/50 khác nhau, chữ ký giọng 50/50 khác nhau, phông 23
 * giá trị. Nhưng `dinh_dang` chỉ có **7 giá trị cho 50 kênh**: `ranked` dùng lại **18 lần**,
 * `cinematic` 10 lần. Màu và phông khác nhau không cứu được chuyện đó: người xem nhận ra "cùng
 * một lò" qua BỐ CỤC — vị trí nhãn, hình dáng thẻ, cách nền chuyển — chứ không qua mã màu.
 * Anh cấm rõ: "ko lặp lại 1 motip, ko lặp lại 1 template".
 *
 * Cách làm rẻ nhất mà thật sự khác: KHÔNG viết 18 bố cục, mà tách bố cục thành mấy công tắc độc
 * lập rồi cho mỗi kênh một tổ hợp riêng. 3 vị trí nhãn × 3 kiểu thẻ × 3 nền = 27 tổ hợp, thừa cho
 * 18 kênh đông nhất. Chỉ số `bien` do seed gán cố định theo kênh nên bố cục KHÔNG đổi giữa các
 * video của cùng một kênh — nhận diện kênh phải ổn định, đó là điểm của cả việc này.
 */
export type Bien = {
  nhan: 0 | 1 | 2;   // 0 = nhãn cột TRÁI · 1 = cột PHẢI · 2 = hàng TRÊN
  the: 0 | 1 | 2;    // 0 = thẻ đặc · 1 = thẻ viền rỗng · 2 = thẻ có vạch màu bên trái
  nen: 0 | 1 | 2;    // 0 = trơn · 1 = sọc chéo · 2 = lưới chấm
};

export const bienCua = (n?: number): Bien => {
  const i = Math.max(0, Math.floor(Number(n) || 0));
  return { nhan: (i % 3) as any, the: (Math.floor(i / 3) % 3) as any, nen: (Math.floor(i / 9) % 3) as any };
};

/** Lớp hoạ tiết chồng lên nền. Rất nhạt (≤5%) — đủ để mắt thấy khác, không đủ để cướp nội dung. */
export const hoaTietNen = (b: Bien, accent: string): React.CSSProperties => {
  if (b.nen === 1)
    return { backgroundImage: `repeating-linear-gradient(135deg, ${accent}0d 0 2px, transparent 2px 22px)` };
  if (b.nen === 2)
    return { backgroundImage: `radial-gradient(${accent}1a 1.5px, transparent 1.6px)`, backgroundSize: "26px 26px" };
  return {};
};

/** Kiểu thẻ nội dung. Giữ NGUYÊN kích thước và khoảng cách — chỉ đổi hình dáng, để không đụng
 *  vào các phép đo chống tràn đã chỉnh tay từng con số. */
export const kieuThe = (b: Bien, accent: string): React.CSSProperties => {
  if (b.the === 1)
    return { background: "#0e132633", border: `2.5px solid ${accent}aa`, borderRadius: 14 };
  if (b.the === 2)
    return { background: "#0e1326", border: "2px solid #ffffff14", borderLeft: `7px solid ${accent}`,
             borderRadius: "6px 16px 16px 6px" };
  return { background: "#0e1326", border: `2px solid ${accent}66`, borderRadius: 16 };
};
