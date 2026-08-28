import { useVideoConfig } from "remotion";

/** Hằng số bố cục theo KHỔ, một chỗ cho toàn hệ.
 *
 * 26/8 — năm dạng gen-2 (`ranked/scaled/mapped/longshot/thennow`) chỉ có bản DỌC: `calculateMetadata`
 * của chúng ép cứng `width: 1080, height: 1920`, và mọi toạ độ trong thân hàm (top 90, top 340,
 * bottom 130, cỡ chữ 68…) đều đo theo khung dọc. Hệ quả đo thật: `chay_bo` render chương bằng
 * composition dọc rồi NỐI lại gọi là "long" ⇒ long là video dọc 1'44" ⇒ YouTube xếp vào Shorts ⇒
 * bộ 1 long + 3 short thực chất là 4 short, dù mọi con số trong sổ đều đúng.
 *
 * Anh chốt hướng: long phải là 16:9 thật, còn short KHÔNG phải cắt từ long ra mà viết + dựng lại
 * riêng cho 9:16 có hook. Nên khung ngang không được là bản dọc kéo giãn — nó là bố cục khác.
 *
 * Cách làm theo đúng tiền lệ sẵn có trong repo (`RaceLong.TitleScreen` đã tự đổi theo `port`):
 * hỏi khổ thật qua `useVideoConfig()` rồi trả về bộ hằng số tương ứng. Bản dọc giữ nguyên số cũ
 * từng con một, nên thêm khổ ngang KHÔNG đụng tới 3 short đang chạy đúng. */
export type Khung = {
  doc: boolean;          // true = 9:16
  W: number; H: number;
  padX: number;          // lề trái/phải
  tieuDeTop: number;     // mốc trên của khối tiêu đề
  tieuDeCo: number;      // cỡ chữ tiêu đề
  nhanCo: number;        // cỡ chữ nhãn/kicker
  thanTop: number;       // mốc trên của phần thân (bảng/biểu đồ)
  thanDayCoSub: number;  // mốc dưới khi CÓ phụ đề
  thanDayKhongSub: number;
  cot: boolean;          // thân xếp theo CỘT (dọc) hay HÀNG (ngang)
  handleDay: number;
};

export const dungKhung = (): Khung => {
  const { width: W, height: H } = useVideoConfig();
  const doc = H >= W;
  return doc
    ? { doc, W, H, padX: 50, tieuDeTop: 90, tieuDeCo: 68, nhanCo: 30,
        thanTop: 340, thanDayCoSub: 380, thanDayKhongSub: 130, cot: true, handleDay: 50 }
    : { doc, W, H, padX: 64, tieuDeTop: 44, tieuDeCo: 56, nhanCo: 26,
        thanTop: 190, thanDayCoSub: 170, thanDayKhongSub: 70, cot: false, handleDay: 28 };
};

/** Số dòng mà tiêu đề THẬT SỰ chiếm, ước theo bề ngang khung và cỡ chữ.
 *
 * 28/8 — soi khung thật kênh STEAM TRUTH: tiêu đề "Free games beating the ones people paid for —
 * Counter-Strike: Global, 1.0M" dài 3 dòng, đè xuống phụ đề "by players online", và phụ đề rơi
 * hẳn vào trong ô tier S. Vì `thanTop` là SỐ CỨNG 340, đo cho một tiêu đề hai dòng.
 * Tiêu đề gen-2 nay dài hơn hẳn hồi đặt con số đó: từ khi `_tieu_de_tu_du_lieu` chèn chủ thể +
 * con số lên trước khuôn, ba dòng là chuyện thường. Một hằng số đo cho hình dạng dữ liệu CŨ sẽ
 * âm thầm sai với mọi dữ liệu mới — và chỉ thấy được bằng mắt, sau khi đã render.
 *
 * Không đo được chữ trong Remotion mà không dựng thêm một lượt, nên ước: bề ngang khả dụng chia
 * cho bề ngang trung bình một ký tự (~0,52 lần cỡ chữ với phông đậm hẹp của bộ này). Ước thừa
 * một dòng chỉ tốn khoảng trắng; ước thiếu là chữ đè chữ — nên làm tròn LÊN. */
export const soDongTieuDe = (title: string, K: Khung): number => {
  const rong = Math.max(120, K.W - 2 * K.padX);
  const moiDong = Math.max(8, Math.floor(rong / (K.tieuDeCo * 0.52)));
  return Math.max(1, Math.min(4, Math.ceil((String(title || "").length || 1) / moiDong)));
};

/** Mốc y mà phần thân được phép bắt đầu, để không bao giờ chạm khối tiêu đề. */
export const dayTieuDe = (title: string, K: Khung, coSub: boolean): number =>
  K.tieuDeTop + (K.doc ? 18 : 10)
  + soDongTieuDe(title, K) * K.tieuDeCo * 1.02
  + (coSub ? (K.doc ? 32 : 26) + 8 : 0)
  + (K.doc ? 26 : 18);
