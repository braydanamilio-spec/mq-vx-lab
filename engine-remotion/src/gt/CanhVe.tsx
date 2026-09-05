import React from "react";
import { TuVe } from "./TuVe";
import { AbsoluteFill } from "remotion";
import { chanTroi, _tron, _pha } from "./Khuon";

/* ══════════════════════════════════════════════════════════════════════════════════════
   CẢNH VẼ BẰNG CODE — lớp XEN KẼ với ảnh CF, không phải lớp dự phòng   (4/9/2026)
   ══════════════════════════════════════════════════════════════════════════════════════

   VÌ SAO CÓ TỆP NÀY
   ─────────────────
   Đo trên 18 kênh, tập 0, cả short lẫn long: **999/1.640 nhịp (60%) đặt một ảnh CF**, và
   riêng nhịp `canh` là 586/586 — một trăm phần trăm. Một tập HOW LONG tiêu **134 ảnh**.
   §16.5 đã đo hồ CF cạn sạch ở 14.900 ảnh. Nên ở mức "vài nghìn video mỗi ngày" thì đường
   ảnh CF là một bức tường, không phải một nút thắt nới ra được.

   Repo ĐÃ có một lớp vẽ bằng code (`que/NenQue`) và `KichGiaiThich` đã gọi nó — nhưng chỉ
   khi `nenAnh` VẮNG, tức nó là lưới an toàn chứ chưa bao giờ là một lựa chọn có chủ ý. Và
   mười nơi chốn của nó đều là trong nhà (bếp · phòng khách · phòng tắm): thế giới của bộ
   truyện tranh sinh ra nó, không phải thế giới bộ giải thích (kho hàng · băng giá · vũ trụ
   · nhà máy). Đúng §12.5 — một tài sản đúng ở ngữ cảnh nó sinh ra, sai ở ngữ cảnh mới.

   ĐIỀU KIỆN ĐỂ XEN KẼ KHÔNG ĐỌC RA "CHẮP VÁ"
   ──────────────────────────────────────────
   Người xem chấp nhận hai chất liệu trong một phim khi chúng chia nhau BỐN thứ. Cả bốn
   đều là ràng buộc mã, không phải lời khuyên:

     1. cùng ĐƯỜNG CHÂN TRỜI  -> `chanTroi(H, hat)`, đúng hàm mà `NenPhong` dùng
     2. cùng BẢNG MÀU         -> mọi màu pha ra từ `nen` + `mau` của kênh, không hằng số rời
     3. cùng LUẬT TIẾP ĐẤT    -> vật đứng trên sàn thì có bóng ellipse, không trừ vật nào
     4. cùng SÀN SẪM DẦN Ở ĐÁY-> để phụ đề trắng giữ tương phản ≥ 4,5:1 (WCAG AA)

   Thiếu (1) thì hai loại nhịp có hai mặt sàn; thiếu (4) thì cổng `kiem_hinh` sẽ đánh trượt
   đúng những nhịp vẽ bằng code — và đó là cách chắc chắn để kết luận nhầm rằng "vẽ code
   xấu hơn" trong khi thứ sai chỉ là một dải sáng ở đáy khung.

   VÌ SAO SILHOUETTE, KHÔNG PHẢI NÉT VIỀN
   ──────────────────────────────────────
   §15.9 đã trả giá: con hươu vẽ bằng ba đường KHÔNG TÔ, thu xuống 34% thì ra một cái móc
   câu — độ dày nét không co theo hình. Mọi hình ở đây là KHỐI ĐẶC, và chiều sâu làm bằng
   ba nấc giá trị của cùng một sắc, không làm bằng đường viền.

   VÀ VÌ SAO PROFILE PHẢI LỞM CHỞM
   ───────────────────────────────
   Thứ tách "được thiết kế" khỏi "ghép bằng hình chữ nhật" là đường bao KHÔNG ĐỀU. `_rang`
   sinh dãy lệch tất định từ hạt, nên cùng một tập luôn ra cùng một cảnh (dựng lại được),
   còn hai tập khác nhau ra hai đường bao khác nhau.
   ══════════════════════════════════════════════════════════════════════════════════════ */

/** Dãy số tất định trong [0,1) — thay cho Math.random, để dựng lại tập cũ ra đúng hình cũ. */
const _rang = (hat: number, n: number): number[] => {
  const ra: number[] = [];
  let x = (Math.abs(Math.trunc(hat)) % 100000) + 12345;
  for (let i = 0; i < n; i++) {
    x = (x * 1103515245 + 12345) & 0x7fffffff;   // LCG cổ điển, đủ cho việc lệch hình
    ra.push((x >>> 8) / 0x7fffff);
  }
  return ra;
};

/** Đường bao lởm chởm từ trái sang phải, đóng kín xuống đáy `day`. */
const _bao = (W: number, y0: number, bien: number, day: number,
              hat: number, dot: number): string => {
  const r = _rang(hat, dot + 1);
  const b = [`M 0 ${day}`, `L 0 ${y0 + (r[0] - 0.5) * bien}`];
  for (let i = 1; i <= dot; i++) {
    const x = (W * i) / dot;
    b.push(`L ${x.toFixed(1)} ${(y0 + (r[i] - 0.5) * bien).toFixed(1)}`);
  }
  b.push(`L ${W} ${day}`, "Z");
  return b.join(" ");
};

/** Đường bao răng cưa NHỌN — núi, băng, thông. Cùng hạt thì cùng hình. */
const _rang_cua = (W: number, y0: number, cao: number, day: number,
                   hat: number, dinh: number): string => {
  const r = _rang(hat + 77, dinh * 2);
  const b = [`M 0 ${day}`, `L 0 ${y0}`];
  for (let i = 0; i < dinh; i++) {
    const x0 = (W * i) / dinh, x1 = (W * (i + 0.5)) / dinh, x2 = (W * (i + 1)) / dinh;
    b.push(`L ${x1.toFixed(1)} ${(y0 - cao * (0.45 + r[i] * 0.55)).toFixed(1)}`,
           `L ${x2.toFixed(1)} ${(y0 - cao * r[dinh + i] * 0.28).toFixed(1)}`);
    void x0;
  }
  b.push(`L ${W} ${day}`, "Z");
  return b.join(" ");
};

/* ── VIỀN NÉT CHO VẬT TIỀN CẢNH  (4/9/2026, theo ảnh tham chiếu anh gửi) ────────────────
   Ảnh tham chiếu vẽ VIỀN quanh mọi vật ở tiền cảnh — bàn, chậu cây, cửa sổ, tảng đá — và
   đó là thứ tách "tranh vẽ tay" khỏi "khối màu ghép bằng code". Không có viền thì hai mảng
   màu gần nhau nhoè vào nhau và cảnh đọc ra phẳng lì.

   Nhưng CHỈ tiền cảnh. Viền cả dải xa nữa thì khung thành một bức tranh tô màu: trong
   tranh phẳng, chiều sâu làm bằng việc vật ở xa MẤT DẦN chi tiết, và viền là chi tiết.
   Đây là chỗ dễ làm quá tay — viền thêm luôn trông "kỹ hơn" ở một hình đứng một mình, và
   làm hỏng lớp lang khi nhìn cả khung.

   Mực lấy từ chính bảng màu (nấc sẫm nhất, sẫm thêm) chứ không dùng đen tuyệt đối: đen
   thuần trên một cảnh sa mạc ấm đọc ra vết cắt dán. */
/* ── MỘT THỨ MỰC CHO CẢ KHUNG  (4/9/2026) ──────────────────────────────────────────────────
   Bản trước lấy mực từ chính bảng màu (`nhan` sẫm thêm 45%), với lý do *"đen thuần trên một
   cảnh sa mạc ấm đọc ra vết cắt dán"*. Lý do ấy nghe đúng và **sai theo bằng chứng**: mấy
   ảnh tham chiếu anh gửi đều là cảnh ấm (sa mạc, chợ đất nện, phòng gỗ) và mọi vật trong đó
   đều viền bằng một thứ mực gần đen — nó không hề đọc ra cắt dán, nó đọc ra "cùng một cây bút".

   Và có một ràng buộc mà bản trước không thấy: **nhân vật đã viền `#2C2722`**. Mực của cảnh
   pha theo từng nơi chốn nghĩa là mỗi nơi một cây bút khác, còn nhân vật thì luôn một cây —
   nên nhân vật luôn lệch khỏi cảnh dù cảnh nào cũng "hợp màu của nó".

   Cùng một thứ mực cho cả khung. Không phải đen thuần (#000) mà là đen ấm, đúng thứ
   `BieuTuong` đang dùng. */
const _muc = (_c: Bang) => "#2C2722";

/** Bóng tiếp đất — MỌI vật đứng trên sàn đều phải có, không trừ vật nào (ràng buộc 3). */
const Bong: React.FC<{ x: number; y: number; r: number }> = ({ x, y, r }) => (
  /* `stroke="none"`: nhóm cha nay mang nét mực và SVG kế thừa nó xuống mọi con. Bóng đổ là
     một VÙNG MỜ, không phải một vật — viền quanh nó biến bóng thành một cái đĩa đen nằm dưới
     chân. Mọi hình "không phải vật" trong tệp này đều phải tự tắt nét. */
  <ellipse cx={x} cy={y} rx={r} ry={r * 0.17} fill="#000000" opacity={0.13} stroke="none" />
);

type Bang = { xa: string; giua: string; gan: string; troi: string; troiD: string;
              san: string; sanD: string; sanDay: string; nhan: string;
              vat2: string; vat3: string; vat4: string };

/* ── MỘT NƠI CHỐN CÓ ÁNH SÁNG CỦA RIÊNG NÓ  (4/9/2026, sau khi SOI KHUNG) ────────────────
   Bản đầu pha MỌI màu từ `nen` + `mau` của kênh — nghe đúng ("giữ bản sắc kênh"), và soi
   khung thì sa mạc của SURVIVE ra **nâu tím**, băng giá cũng ra nâu tím. Hai nơi lẽ ra
   không thể nhầm được lại trông y hệt nhau, và không nơi nào đọc ra đúng tên của nó.

   Cùng họ lỗi số 6 của CLAUDE.md: *mượn một giá trị cho việc nó không sinh ra để làm*.
   Màu thương hiệu sinh ra để nói "đây là kênh nào", không sinh ra để nói "đây là đâu".

   Nên mỗi nơi khai một SẮC NEO, và bảng màu pha kênh → sắc neo 45%: đủ để cát ra cát và
   băng ra băng, vẫn đủ để hai kênh cùng vẽ sa mạc ra hai sắc cát khác nhau. Nơi không
   khai sắc neo (phố, đồng, kho…) thì giữ nguyên màu kênh như cũ — chỉ những nơi có ánh
   sáng ĐẶC TRƯNG mới cần, và ép sắc cho mọi nơi là mất bản sắc kênh để lấy về không gì. */
const SAC_NOI: Record<string, [number, number]> = {
  // [góc sắc độ, độ bão hoà]. Không khai bằng mã hex: trộn hex là trộn cả ĐỘ SÁNG, mà độ
  // sáng ở đây chính là nấc chiều sâu — trộn vào là san phẳng nó.
  sa_mac: [38, 0.52],    // cát dưới nắng cao
  bang:   [200, 0.34],   // băng trong bóng râm — lam nhạt, KHÔNG trắng tinh
  bien:   [198, 0.40],
  troi:   [232, 0.44],   // trời đêm sâu, để sao đọc được
};

/* Kéo SẮC và ĐỘ BÃO HOÀ về phía một nơi chốn, GIỮ NGUYÊN độ sáng.

   Bản đầu trộn thẳng hai mã hex và soi khung thì không ăn: nền của SURVIVE vốn là xám
   `#E8E9E6`, nên trộn 45% về một sắc cát nhạt chỉ làm nó sáng hơn — `#c0aba5` thành
   `#c7c4c6`, vẫn xám. Đo ra ngay bằng `node`, và đó là lý do phải đo thay vì nhìn mã.

   Độ sáng phải giữ nguyên vì ba nấc `xa`/`giua`/`gan` LÀ chiều sâu của cảnh; đổi chúng là
   phá thứ làm cảnh có lớp. Nên phép đúng là chuyển sắc, không phải trộn màu. */
export const _sacHoa = (hex: string, h2: number, s2: number, t: number): string => {
  const m = /^#([0-9a-f]{6})$/i.exec((hex || "").trim());
  if (!m) return hex;
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(m[1].slice(i, i + 2), 16) / 255);
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, d = mx - mn;
  let h = 0;
  if (d) {
    h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
    h *= 60; if (h < 0) h += 360;
  }
  const sa = d ? d / (1 - Math.abs(2 * l - 1)) : 0;
  // ── SẮC LÀ MỘT ĐÍCH, KHÔNG PHẢI MỘT QUÃNG ĐƯỜNG  (sửa sau khi ĐO bằng `node`) ───────
  // Bản đầu nội suy sắc theo đường ngắn nhất với hệ số `t`. Đo ra: nền xám của SURVIVE ở
  // sắc 14°, đích băng ở 200° — hai giá trị gần ĐỐI CỰC, nên đi 72% đường ngắn nhất dừng
  // lại ở 249°: **màu tím**. Đúng thứ luật nội suy sinh ra để tránh, ở một ca nó không
  // che được. Và mắt không bắt được điều này khi đọc mã — chỉ phép đo bắt.
  //
  // Nghĩ lại thì "đi 72% quãng đường tới sắc của cát" vốn không có nghĩa gì: sa mạc thì
  // MÀU CÁT, không phải màu lưng chừng giữa cát và màu kênh. Nên sắc lấy trọn từ nơi
  // chốn, còn `t` chỉ điều tiết ĐỘ BÃO HOÀ — đó mới là chỗ giữ được sức mạnh của kênh
  // (kênh trầm thì sa mạc trầm, kênh tươi thì sa mạc tươi), và nó không bao giờ đổi sắc.
  const H = ((h2 % 360) + 360) % 360;
  const S = sa + (s2 - sa) * t;
  void h;
  const C = (1 - Math.abs(2 * l - 1)) * S, X = C * (1 - Math.abs(((H / 60) % 2) - 1));
  const mm = l - C / 2;
  const k = Math.floor(H / 60) % 6;
  const v = [[C, X, 0], [X, C, 0], [0, C, X], [0, X, C], [X, 0, C], [C, 0, X]][k];
  return "#" + v.map((x) => Math.round((x + mm) * 255).toString(16).padStart(2, "0")).join("");
};

/* ── NƠI CÓ MẶT ĐẤT TỐI THẬT SỰ ────────────────────────────────────────────────────────
   Sau khi sàn được sáng trở lại, `troi` (trời đêm) rơi vào 173 — vừa đủ để `PhuDe` chọn
   mực tối, và một cảnh đêm có mặt đất SÁNG thì sai hẳn về bản chất.

   Đây không phải ngoại lệ cần vá: mặt đất dưới trời đêm tối là ĐÚNG. Nên nó khai riêng,
   rơi xuống dưới 118 và `PhuDe` tự chọn mực trắng — cùng cơ chế, hai kết quả, không có
   nhánh đặc biệt nào trong mã phụ đề. */
const DAY_TOI: Record<string, number> = { troi: -0.62 };

/** Nơi TRONG NHÀ: phía trên không phải bầu trời mà là tường/trần. */
const TRONG_NHA = new Set(["kho", "van_phong", "nha_may"]);

/* ── NÂNG BÃO HOÀ, KHÔNG ĐỔI ĐỘ SÁNG  (4/9/2026) ────────────────────────────────────────
   Đo pixel ba khung: bão hoà **7–36%, phần lớn quanh 20%** — đó là lý do khung đọc ra
   "xỉn" dù không có màu nào sai. Nguyên do ở công thức: mọi dải pha từ `nen` (gần trắng,
   bão hoà ~5%) với `mau`, và trộn với một màu gần trắng thì KÉO BÃO HOÀ XUỐNG.

   Không chữa bằng cách trộn thêm `mau`: trộn đổi cả độ sáng, mà độ sáng ở đây là nấc
   chiều sâu — cùng lỗi đã mắc khi ép sắc cho sa mạc. Nâng thẳng thành phần S của HSL,
   giữ nguyên H và L, thì ba dải xa/giữa/gần vẫn cách nhau đúng như cũ.

   1,55× đưa 20% lên ~31%: đủ để màu "có chất" mà chưa sang vùng rực rỡ. Tranh phẳng
   chuyên nghiệp sống ở khoảng 25–45% bão hoà; trên 60% là chất poster quảng cáo, và nó
   đánh nhau với đồ hoạ số liệu đè lên trên. */
const _dam = (hex: string, k: number): string => {
  const m = /^#([0-9a-f]{6})$/i.exec((hex || "").trim());
  if (!m) return hex;
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(m[1].slice(i, i + 2), 16) / 255);
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, d = mx - mn;
  if (!d) return hex;
  let h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  h *= 60; if (h < 0) h += 360;
  const S = Math.min(0.78, (d / (1 - Math.abs(2 * l - 1))) * k);
  const C = (1 - Math.abs(2 * l - 1)) * S, X = C * (1 - Math.abs(((h / 60) % 2) - 1));
  const mm = l - C / 2, q = Math.floor(h / 60) % 6;
  const v = [[C, X, 0], [X, C, 0], [0, C, X], [0, X, C], [X, 0, C], [C, 0, X]][q];
  return "#" + v.map((x) => Math.round((x + mm) * 255).toString(16).padStart(2, "0")).join("");
};

/** Bảng màu của một cảnh — pha TỪ màu kênh, rồi kéo về sắc neo của nơi chốn. */
/* ── BÃO HOÀ: ĐO RỒI MỚI CHỈNH  (4/9/2026) ─────────────────────────────────────────────────
   Đo pixel trên hai khung vẽ code vừa dựng (bỏ dải chữ): **bão hoà 20–22%**, độ sáng 218/255.
   Mấy ảnh tham chiếu anh gửi nằm ở **28–42%** (cát ~42%, trời ~29%, tường kem ~28%).

   Chú thích ngay dưới đã ghi đúng khoảng cần tới (*"25–45%"*) và `_dam(…, 1.55)` đã có — nhưng
   nó chỉ ăn vào ba dải VẬT (`xa/giua/gan/nhan`), còn TRỜI và SÀN thì không, mà hai thứ ấy
   chiếm gần hết diện tích khung. Nên số đo tổng vẫn nằm nguyên ở 20%: bản vá đúng chỗ nhỏ,
   bỏ trống chỗ lớn — cùng họ "vá một nhánh, để nguyên nhánh song song" (§6).

   Nay dải trời và dải sàn cũng đi qua `_dam`. Hệ số nhẹ hơn dải vật (1,25–1,35 thay vì 1,55):
   chúng là NỀN, và nền rực bằng vật thì đồ hoạ số liệu đè lên trên hết đọc được. */
/* ── ĐỒ VẬT PHẢI CÓ MÀU CỦA CHÍNH NÓ  (5/9/2026) ────────────────────────────────────────
   Anh gửi ảnh tham chiếu (cậu bé + chồng báo) và nói kiểu vẽ ấy đúng hơn. Đo màu ảnh ấy:
   tường kem · tủ NÂU · áo MẬN · quần XANH · sàn CAM · đồng hồ nâu sẫm — **sáu sắc độ trong
   một khung**.

   Bảng dưới đây thì mọi mục đều là `_tron(nen, mau, x)`: một sắc duy nhất pha loãng dần.
   Nên cảnh vẽ code đọc ra một khối bóng đơn sắc chứ không đọc ra một bức tranh, và không
   độ tương phản nào cứu được — thiếu SỐ LƯỢNG SẮC, không thiếu độ đậm.

   Đúng §14.5: *`chinh` là màu của DẤU HIỆU, không phải màu của bộ phim.* Màu kênh thuộc về
   con số và chữ (chỗ nó phải nhận ra được ở 48px); đồ đạc trong cảnh cần bảng màu riêng.

   Bốn màu vật liệu tuyệt đối — gỗ · xanh rêu · đất nung · xanh đá — mỗi màu pha 18% về phía
   màu kênh để mười tám kênh vẫn khác nhau, nhưng KHÔNG pha nhiều hơn: pha nhiều là quay lại
   đúng chỗ đơn sắc vừa đi ra. Chọn bốn màu này vì chúng là bảng của tranh minh hoạ giấy ấm,
   và cả bốn đều đọc được trên nền kem lẫn nền sẫm. */
const VAT_LIEU = ["#8A6A4F", "#7E8C6A", "#B0724E", "#5E7285"];
const _vat = (i: number, nen: string, mau: string): string =>
  _pha(_tron(VAT_LIEU[i % VAT_LIEU.length], mau, 0.18), 0.00);

const _bang = (nen: string, mau: string, mauPhu: string, am: number): Bang => ({
  /* ── VÀ TỈ LỆ PHA, KHÔNG PHẢI HỆ SỐ NHÂN  (đo lần hai) ─────────────────────────────────
     Thêm `_dam` vào hai dải nền xong, đo lại: **22% → 23%**. Gần như không đổi, và lý do là
     số học: `_dam` nhân THÀNH PHẦN S của HSL, mà `_tron(nen, mau, 0.06)` cho ra một màu gần
     trắng có S ≈ 0,05 — nhân 1,3 thì vẫn 0,065. Nhân một số gần 0 với một hệ số nhỏ thì vẫn
     gần 0; muốn màu có chất thì phải cho nó NHIỀU MÀU hơn, tức tăng tỉ lệ pha.
     Đây đúng bài học "đo lại sau khi sửa": bản vá thứ nhất đúng hướng và sai đòn bẩy. */
  troi:   _dam(_pha(_tron(nen, mau, 0.05 + am * 0.02), 0.14), 1.30),
  troiD:  _dam(_pha(_tron(nen, mau, 0.08 + am * 0.03), 0.00), 1.45),
  /* ── ĐỒ VẬT LÀ NÉT, KHÔNG PHẢI MẢNG MÀU  (5/9/2026) ──────────────────────────────────
     Sau khi chốt chuẩn mực-trên-giấy, những mảng màu này thành chất liệu thứ hai: nhân vật
     vẽ bằng nét, đồ đạc là khối màu pastel không viền. Soi khung thấy ngay hai lớp dán lên
     nhau — §12.10 đã đo rằng lệch phong cách là đòn bẩy lớn hơn hẳn màu sắc.
     Ảnh mẫu của các kênh trăm triệu view: mọi đồ vật đều là NÉT MỰC, ruột để giấy lộ qua,
     chỉ vài chỗ nhỏ tô đặc làm điểm nhấn. Nên ruột đồ vật nay gần bằng màu giấy — nét mực
     do thẻ `<g stroke>` ở dưới lo, đã có sẵn. */
  xa:     _pha(nen, 0.03),
  giua:   _pha(nen, -0.02),
  gan:    _pha(nen, -0.06),
  vat2:   _pha(nen, 0.05),
  vat3:   _pha(nen, -0.04),
  vat4:   _pha(nen, -0.09),
  /* Điểm nhấn giữ màu kênh — đây là chỗ DUY NHẤT trong cảnh có màu, nên nó hút mắt đúng
     như cái cà vạt tô đen trong ảnh mẫu. Một khung một điểm nhấn. */
  nhan:   _pha(_tron(nen, mauPhu || mau, 0.55), -0.10),
  /* ── BA MÀU MẶT SÀN — KHÔI PHỤC  (5/9/2026) ─────────────────────────────────────────
     Lượt sửa "đồ vật thành nét" ngay trên đây thay cả khối từ `xa:` tới `nhan:`, và XOÁ
     NHẦM ba khoá này. TypeScript không kêu vì `Bang` nhận thiếu khoá qua phép ép kiểu ở
     `_sacHoa`, nên nó hỏng LÚC CHẠY: `fill={undefined}` cho ra ĐEN, và đáy khung thành
     một dải đen chiếm một phần ba.
     Đúng họ lỗi §15.2 — thay một khối lớn thì phải đếm lại khoá trước và sau. Nếu chỉ nhìn
     mã thì khối mới đọc rất gọn gàng; chỉ khung dựng ra mới nói thật.
     Ba chặng phải SẪM DẦN, không được đảo chiều: `sangDayCanh` đọc chính `sanDay` để bảo
     engine chọn mực phụ đề (§ chú thích dài ở bản trước). */
  san:    _dam(_pha(_tron(nen, mau, 0.10), -0.04), 1.35),
  sanD:   _dam(_pha(_tron(nen, mau, 0.12), -0.07), 1.35),
  sanDay: _dam(_pha(_tron(nen, mau, 0.15), -0.11), 1.35),
});

type P = { W: number; H: number; san: number; c: Bang; hat: number; r: number[] };

/* ── MƯỜI NƠI CHỐN CỦA THẾ GIỚI GIẢI THÍCH ──────────────────────────────────────────────
   Chọn mười, không chọn mười sáu: §15.9 và §14.4 đều dạy rằng một hình chỉ đúng ở cỡ nó
   được vẽ ra thì không phải hình đúng, và mười nơi vẽ kỹ hơn hẳn mười sáu nơi vẽ vội.
   Mỗi nơi nhận `hat` nên có ba biến thể theo tập -> 30 diện mạo, xen kẽ với ảnh CF.        */
const NOI_VE: Record<string, (p: P) => React.ReactNode> = {

  /* KHO HÀNG — giá cao, thùng, vì kèo mái. Thế giới của DAY IN LIFE · WHAT WEIGHS · HOW MUCH */
  kho: ({ W, H, san, c, hat, r }) => {
    const cao = san - H * 0.30, k = 3 + Math.abs(hat) % 2;
    return (<g>
      {/* vì kèo mái — nét chéo lặp, thứ nói "nhà xưởng" chỉ bằng một hình */}
      {Array.from({ length: 7 }, (_, i) => (
        <path key={`k${i}`} d={`M ${(W * i) / 6} ${H * 0.06} L ${(W * (i + 0.5)) / 6} ${H * 0.16}
                                L ${(W * (i + 1)) / 6} ${H * 0.06}`}
              stroke={c.xa} strokeWidth={W * 0.006} fill="none" opacity={0.5} />
      ))}
      {Array.from({ length: k }, (_, i) => {
        const bw = W / (k + 0.4), x = bw * (i + 0.2);
        const h = (san - cao) * (0.74 + r[i] * 0.26);
        return (<g key={i}>
          <rect x={x} y={san - h} width={bw * 0.8} height={h} fill={c.giua} />
          {[0.30, 0.62].map((t, j) => (
            <rect key={j} x={x} y={san - h + h * t} width={bw * 0.8} height={H * 0.012}
                  fill={c.gan} opacity={0.8} />
          ))}
          {/* thùng trên kệ — kích cỡ lệch nhau, đều nhau thì đọc ra hình nền lặp */}
          {[0, 1].map((j) => (
            <rect key={`t${j}`} x={x + bw * (0.06 + j * 0.40)} y={san - h + h * 0.30 - H * 0.05}
                  width={bw * 0.30} height={H * (0.038 + r[(i + j) % r.length] * 0.016)}
                  fill={c.nhan} opacity={0.9} />
          ))}
        </g>);
      })}
    </g>);
  },

  /* NHÀ MÁY — ống khói, bồn, cầu trục. HOW HOT · WHERE GOES · REAL COST */
  nha_may: ({ W, H, san, c, r }) => (
    <g>
      <path d={_bao(W, san - H * 0.20, H * 0.09, san, 991, 8)} fill={c.xa} />
      {[0.10, 0.30, 0.72].map((x, i) => (
        <rect key={i} x={W * x} y={san - H * (0.26 + r[i] * 0.14)} width={W * 0.055}
              height={H * (0.26 + r[i] * 0.14)} fill={c.giua} />
      ))}
      {[0.46, 0.60].map((x, i) => (
        <g key={`b${i}`}>
          <rect x={W * x} y={san - H * 0.17} width={W * 0.11} height={H * 0.17}
                rx={W * 0.05} fill={c.gan} stroke={_muc(c)} strokeWidth={W * 0.005} />
          <Bong x={W * (x + 0.055)} y={san} r={W * 0.075} />
        </g>
      ))}
      {/* đường ống nối hai bồn — chi tiết nhỏ nhưng nó là thứ nói "đây là nhà máy" */}
      <rect x={W * 0.46} y={san - H * 0.13} width={W * 0.25} height={H * 0.016} fill={c.nhan} />
    </g>
  ),

  /* PHỐ — đường bao nhà, cột đèn, lòng đường. HOW LOUD · WHAT IF · RIGHT NOW · ODDS */
  pho: ({ W, H, san, c, hat, r }) => {
    const n = 7 + Math.abs(hat) % 3;
    return (<g>
      {Array.from({ length: n }, (_, i) => {
        const bw = W / n, h = H * (0.14 + r[i] * 0.26);
        return (<g key={i}>
          <rect x={bw * i} y={san - h} width={bw * 0.94} height={h}
                fill={i % 2 ? c.giua : c.xa} />
          {/* ── Ô CỬA SỔ LÀ LỖ TỐI, KHÔNG PHẢI DẢI SÁNG  (4/9/2026) ────────────────────
              Bản trước vẽ mỗi tầng một DẢI ngang sáng màu trời. Ở ảnh mẫu (khu chợ đất
              nện) cửa sổ và cửa ra vào đều là **lỗ tối** — và đó là lý do dãy nhà ở đó
              đọc ra "nhà", còn dãy của mình đọc ra "biểu đồ cột có kẻ sọc".
              Một dải ngang chạy hết bề ngang nhà không giống cửa sổ ở bất kỳ đâu; hai ô
              vuông nhỏ cạnh nhau thì giống ngay. */}
          {Array.from({ length: Math.max(2, Math.floor(h / (H * 0.062))) }, (_, j) =>
            [0, 1].map((k2) => (
              <rect key={`${j}-${k2}`}
                    x={bw * i + bw * (0.20 + k2 * 0.38)} y={san - h + H * 0.026 + j * H * 0.062}
                    width={bw * 0.22} height={H * 0.028} rx={W * 0.002}
                    fill={_muc(c)} opacity={r[(i + j + k2) % r.length] > 0.38 ? 0.60 : 0.24} />
            )))}
          {/* CỬA RA VÀO ở chân nhà: thứ nói "người đi vào được", và nó neo toà nhà xuống
              mặt đất — thiếu nó thì khối nhà nào cũng có thể là một cái hộp bất kỳ. */}
          <rect x={bw * i + bw * 0.36} y={san - H * 0.055} width={bw * 0.24} height={H * 0.055}
                rx={W * 0.003} fill={_muc(c)} opacity={0.55} />
        </g>);
      })}
      <g>
        <rect x={W * 0.80} y={san - H * 0.30} width={W * 0.012} height={H * 0.30} fill={c.gan} />
        <circle cx={W * 0.806} cy={san - H * 0.30} r={W * 0.026} fill={c.nhan} />
        <Bong x={W * 0.806} y={san} r={W * 0.030} />
      </g>
    </g>);
  },

  /* ĐƯỜNG DÀI — dải đường thu về điểm tụ, cột mốc, đồi xa. HOW LONG · SPEED OF */
  duong: ({ W, H, san, c, r }) => (
    <g>
      <path d={_bao(W, san - H * 0.13, H * 0.07, san, 313, 9)} fill={c.xa} />
      {/* ── CHIỀU CỦA CON ĐƯỜNG  (sửa 4/9/2026 sau khi SOI KHUNG) ────────────────────────
          Bản đầu vẽ rộng ở chân trời và hẹp dần xuống đáy khung. Soi khung thì nó đọc ra
          một CÁI PHỄU khoét xuống sàn, không đọc ra con đường — vì phối cảnh thật thì
          chỗ GẦN mắt là chỗ RỘNG, và chân trời là chỗ hẹp.
          Không lỗi nào báo: hình vẫn dựng, màu vẫn đúng, cổng vẫn xanh. Chỉ có mắt thấy.
          Đúng §5 — cổng chấm điểm chỉ biết thứ nó được dạy để đo. */}
      {/* Lề đường sáng hơn mặt đường một nấc: không có nó thì hình nêm đọc ra một VỆT
          SÁNG chiếu xuống sàn chứ không ra con đường. Hai vệt lề là thứ rẻ nhất nói
          "đây là mặt đường", rẻ hơn nhiều so với vẽ thêm vật hai bên. */}
      {/* Miệng đường ở chân trời phải RỘNG, không thu về một điểm: thu về điểm thì hai
          cạnh gặp nhau và hình đọc ra KIM TỰ THÁP. Đường thật ở xa vẫn còn bề ngang —
          nó biến mất vì bị vật che, không vì hẹp bằng không. */}
      <path d={`M ${W * 0.415} ${san} L ${W * 0.585} ${san}
                L ${W * 0.98} ${H * 1.02} L ${W * 0.02} ${H * 1.02} Z`}
            fill={c.xa} opacity={0.85} />
      <path d={`M ${W * 0.435} ${san} L ${W * 0.565} ${san}
                L ${W * 0.93} ${H * 1.02} L ${W * 0.07} ${H * 1.02} Z`}
            fill={c.giua} />
      {/* Vạch tim đường: về phía chân trời thì NGẮN LẠI, HẸP LẠI và GẦN NHAU — ba thứ cùng
          co mới ra chiều sâu; co một thứ thì nó chỉ ra một dãy gạch nhỏ dần. */}
      {[0.015, 0.055, 0.115, 0.200, 0.315].map((t, i) => (
        /* Vạch tim đường là SƠN trên mặt đường, không phải vật đứng trên đường — không viền. */
        <rect key={i} x={W * 0.5 - W * (0.004 + t * 0.030)} y={san + H * t}
              width={W * (0.008 + t * 0.060)} height={H * (0.008 + t * 0.045)}
              fill={c.troi} stroke="none" opacity={0.55 + t} />
      ))}
      {/* Cột điện: khoảng cách và chiều cao đều LỆCH theo hạt. Hàng cột cách đều tăm tắp
          là dấu hiệu số một của "ghép bằng vòng lặp" — mắt bắt được nhịp đều ngay cả khi
          không nhìn thẳng vào nó. Hai cột gần mép ngoài thấp hơn: gợi chiều sâu. */}
      {[0.09, 0.27, 0.71, 0.93].map((x0, i) => {
        const x = x0 + (r[i] - 0.5) * 0.05;
        const h = 0.09 + r[(i + 3) % r.length] * 0.08;
        return (<g key={`c${i}`}>
          <rect x={W * x} y={san - H * h} width={W * 0.009} height={H * h} fill={c.gan} />
          <rect x={W * (x - 0.016)} y={san - H * h} width={W * 0.041} height={H * 0.008}
                fill={c.gan} />
          <Bong x={W * (x + 0.005)} y={san} r={W * 0.022} />
        </g>);
      })}
    </g>
  ),

  /* ĐỒNG — đồi thoải, hàng cây, hàng rào. WHAT IF · YEARS OF · SURVIVE */
  dong: ({ W, H, san, c, hat, r }) => (
    <g>
      <path d={_bao(W, san - H * 0.15, H * 0.10, san, hat + 5, 6)} fill={c.xa} />
      <path d={_bao(W, san - H * 0.07, H * 0.05, san, hat + 31, 8)} fill={c.giua} />
      {[0.12, 0.26, 0.66, 0.86].map((x, i) => {
        const s = H * (0.10 + r[i] * 0.07);
        return (<g key={i}>
          <rect x={W * x - W * 0.008} y={san - s * 0.55} width={W * 0.016} height={s * 0.55}
                fill={c.nhan} />
          <ellipse cx={W * x} cy={san - s * 0.72} rx={s * 0.42} ry={s * 0.38} fill={c.gan}
                   stroke={_muc(c)} strokeWidth={W * 0.005} />
          <Bong x={W * x} y={san} r={s * 0.40} />
        </g>);
      })}
    </g>
  ),

  /* BIỂN — dải nước, con sóng, mỏm đá. HOW BIG · WHERE GOES · SMALLEST */
  bien: ({ W, H, san, c, r }) => (
    <g>
      <rect x={0} y={san - H * 0.20} width={W} height={H * 0.20} fill={c.giua} />
      {[0.04, 0.09, 0.15].map((t, i) => (
        <path key={i} d={_bao(W, san - H * (0.20 - t), H * 0.012, san, 700 + i * 13, 12)}
              fill={c.xa} opacity={0.55 - i * 0.12} />
      ))}
      {[0.16, 0.82].map((x, i) => (
        <g key={`d${i}`}>
          <path d={`M ${W * (x - 0.07)} ${san} L ${W * (x - 0.02)} ${san - H * (0.07 + r[i] * 0.05)}
                    L ${W * (x + 0.03)} ${san - H * 0.03} L ${W * (x + 0.08)} ${san} Z`}
                fill={c.gan} stroke={_muc(c)} strokeWidth={W * 0.005} strokeLinejoin="round" />
          <Bong x={W * x} y={san} r={W * 0.075} />
        </g>
      ))}
    </g>
  ),

  /* BĂNG — sống băng răng cưa, tảng trôi, trời lạnh. SURVIVE · HOW HOT (cực lạnh) */
  bang: ({ W, H, san, c, hat, r }) => (
    <g>
      <path d={_rang_cua(W, san - H * 0.06, H * 0.22, san, hat + 9, 5)} fill={c.xa} />
      <path d={_rang_cua(W, san - H * 0.01, H * 0.11, san, hat + 61, 7)} fill={c.giua} />
      {/* Tảng băng nổi: DẸT và SÁNG hơn mặt băng, có một mặt vát bắt sáng. Bản đầu vẽ hình
          thang TỐI hơn nền nên nó đọc ra ba cái lều. Băng nhận ra được nhờ nó sáng hơn thứ
          quanh nó — đó là toàn bộ lý do băng trông như băng. */}
      {[0.20, 0.57, 0.87].map((x, i) => {
        const w = 0.10 + r[i] * 0.05, h = 0.020 + r[(i + 1) % r.length] * 0.022;
        return (<g key={i}>
          <path d={`M ${W * (x - w)} ${san + H * 0.022}
                    L ${W * (x - w * 0.55)} ${san - H * h}
                    L ${W * (x + w * 0.40)} ${san - H * h * 0.72}
                    L ${W * (x + w)} ${san + H * 0.022} Z`}
                fill={_pha(c.troi, 0.10)} />
          <path d={`M ${W * (x - w * 0.55)} ${san - H * h}
                    L ${W * (x + w * 0.40)} ${san - H * h * 0.72}
                    L ${W * (x + w * 0.20)} ${san + H * 0.022}
                    L ${W * (x - w * 0.20)} ${san + H * 0.022} Z`}
                fill={c.xa} opacity={0.45} />
        </g>);
      })}
    </g>
  ),

  /* SA MẠC — cồn cát chồng lớp, khối đá, mặt trời thấp. HOW HOT · SURVIVE */
  sa_mac: ({ W, H, san, c, hat, r }) => (
    <g>
      {/* Mặt trời phải SÁNG HƠN trời. Bản đầu tô bằng `c.gan` — nấc SẪM NHẤT của bảng —
          nên nó ra một vệt tối, và một vệt tối trên trời đọc ra vết bẩn chứ không ra mặt
          trời. Cùng họ §6: mượn một giá trị cho việc nó không sinh ra để làm. */}
      <circle cx={W * (0.22 + r[0] * 0.56)} cy={san - H * 0.21} r={W * 0.075}
              fill={_pha(c.troi, 0.42)} />
      <path d={_bao(W, san - H * 0.12, H * 0.07, san, hat + 17, 5)} fill={c.xa} />
      <path d={_bao(W, san - H * 0.05, H * 0.05, san, hat + 43, 4)} fill={c.giua} />
      {/* Khối đá: đa giác lệch, KHÔNG phải chữ nhật bo góc. Soi khung bản đầu thì hai hình
          chữ nhật đọc ra hai cục xám vô nghĩa — đá nhận ra được nhờ mặt vát và đỉnh lệch,
          không nhờ nó đứng trên mặt đất. Cùng bài học §15.5 (vây cá voi nhận ra nhờ mép
          sau cong, không nhờ nó nhọn). */}
      {[0.66, 0.81].map((x, i) => {
        // Bề ngang 9–15% W, không phải 5–8,5%: soi khung bản đầu thì hai khối ra hai cái
        // gai mảnh. Khối đá đọc được là nhờ nó BỆ VỆ — cao mà hẹp thì thành cột, không
        // thành đá. Cùng bài học §15.9: hình phải giữ được bóng dáng, không giữ được nét.
        const w = 0.09 + r[i] * 0.06, h = 0.05 + r[(i + 2) % r.length] * 0.05;
        return (<g key={i}>
          <path d={`M ${W * x} ${san}
                    L ${W * (x + w * 0.30)} ${san - H * h}
                    L ${W * (x + w * 0.64)} ${san - H * h * 0.82}
                    L ${W * (x + w)} ${san} Z`} fill={c.nhan}
                stroke={_muc(c)} strokeWidth={W * 0.005} strokeLinejoin="round" />
          <path d={`M ${W * (x + w * 0.30)} ${san - H * h}
                    L ${W * (x + w * 0.64)} ${san - H * h * 0.82}
                    L ${W * (x + w * 0.58)} ${san} L ${W * (x + w * 0.36)} ${san} Z`}
                fill={c.gan} opacity={0.45} />
          <Bong x={W * (x + w * 0.5)} y={san} r={W * w * 0.72} />
        </g>);
      })}
    </g>
  ),

  /* VĂN PHÒNG — bàn, màn hình, rèm lá dọc. THE RULES · HIDDEN FEE · REAL COST */
  van_phong: ({ W, H, san, c, r }) => (
    <g>
      {/* ── ĐỒ VẬT GỌI TÊN ĐƯỢC, KHÔNG PHẢI HOA VĂN  (4/9/2026) ─────────────────────────
          Bản trước dựng tường bằng chín vạch dọc. Có nét mực rồi thì chín vạch ấy đọc ra
          một hàng rào, và không có nét thì đọc ra hoa văn giấy dán — cả hai đều không phải
          "văn phòng". Soi ảnh anh gửi: căn phòng ở đó nhận ra được nhờ **ba vật gọi tên
          được** — cửa sổ có trời, đồng hồ treo tường, chậu cây — chứ không nhờ bề mặt.
          Nguyên tắc chung cho mọi nơi chốn: một nơi chốn = vài vật ai cũng gọi tên được,
          không phải một lớp vân bề mặt. */}
      {/* CỬA SỔ: khung + trời + hai đám mây + song chữ thập */}
      <g>
        <rect x={W * 0.06} y={san - H * 0.42} width={W * 0.30} height={H * 0.26}
              fill={c.troi} />
        <ellipse cx={W * 0.14} cy={san - H * 0.34} rx={W * 0.045} ry={H * 0.022}
                 fill="#FFFFFF" opacity={0.75} stroke="none" />
        <ellipse cx={W * 0.26} cy={san - H * 0.28} rx={W * 0.035} ry={H * 0.017}
                 fill="#FFFFFF" opacity={0.6} stroke="none" />
        <line x1={W * 0.21} y1={san - H * 0.42} x2={W * 0.21} y2={san - H * 0.16} />
        <line x1={W * 0.06} y1={san - H * 0.29} x2={W * 0.36} y2={san - H * 0.29} />
      </g>
      {/* ── VÙNG CẤM CỦA CHỦ THỂ: 0,30–0,80·W  (4/9/2026) ─────────────────────────────
          Chủ thể đứng ở cx = 0,38…0,62·W (lệch theo hạt) với bề ngang tới 0,31·W, nên nó
          quét hết dải **0,30–0,78·W**. Đồng hồ đặt ở 0,70 rơi thẳng vào đó và nằm sau đầu
          nhân vật — đúng lỗi che khuất anh vừa nhắc, chỉ khác chỗ.
          Đồ trang trí treo tường phải nằm NGOÀI dải ấy: trái < 0,30 hoặc phải > 0,80. */}
      {/* ĐỒNG HỒ TREO TƯỜNG: mặt tròn + hai kim. Kim lệch theo hạt -> mỗi tập một giờ khác. */}
      <g>
        <circle cx={W * 0.87} cy={san - H * 0.40} r={W * 0.058} fill={c.troi} />
        <line x1={W * 0.87} y1={san - H * 0.40} x2={W * 0.87} y2={san - H * 0.434} />
        <line x1={W * 0.87} y1={san - H * 0.40}
              x2={W * (0.87 + 0.032 * Math.cos(r[2] * 6.28))}
              y2={san - H * 0.40 + H * 0.019 * Math.sin(r[2] * 6.28)} />
      </g>
      {/* CHẬU CÂY: chậu hình thang + ba tán lá. Vật sống duy nhất trong phòng, và là thứ
          làm căn phòng đọc ra "có người dùng" thay vì "sơ đồ nội thất". */}
      {/* Lùi vào 0,86–0,95 và to lên: bản đầu đặt ở 0,90–0,965 nên tán lá chạm mép phải,
          và ở cỡ cũ nó đọc ra một vệt xanh chứ không ra cái cây. Vật ở mép khung phải lùi
          vào bằng ÍT NHẤT bán kính của chính nó. */}
      <g>
        <path d={`M ${W * 0.865} ${san} L ${W * 0.945} ${san}
                  L ${W * 0.932} ${san - H * 0.058} L ${W * 0.878} ${san - H * 0.058} Z`}
              fill={c.gan} />
        <ellipse cx={W * 0.905} cy={san - H * 0.098} rx={W * 0.036} ry={H * 0.042} fill={c.nhan} />
        <ellipse cx={W * 0.872} cy={san - H * 0.074} rx={W * 0.026} ry={H * 0.030} fill={c.nhan} />
        <ellipse cx={W * 0.938} cy={san - H * 0.076} rx={W * 0.026} ry={H * 0.030} fill={c.nhan} />
      </g>
      {/* ── CHỪA KHOẢNG TRỐNG CHO CHỦ THỂ  (4/9/2026) ───────────────────────────────────
          Anh: *"tránh lỗi che khuất chồng chéo."* Hai cái bàn ở 0,14 và 0,56 (mỗi cái rộng
          0,30) phủ 0,14–0,44 và 0,56–0,86; chủ thể đứng quanh 0,38–0,62 với bề ngang ~0,30
          nên nó luôn cắt qua ít nhất một mặt bàn — và vì chủ thể vẽ SAU nên chân nó nằm ĐÈ
          lên mặt bàn, đọc ra "đứng xuyên qua bàn".

          Không sửa bằng thứ tự vẽ: cho chủ thể ra sau bàn thì nửa dưới bị che, mà nhịp này
          chủ thể mới là thứ cần nhìn. Sửa bằng BỐ CỤC — một cái bàn, dồn hẳn sang trái, đúng
          cách ảnh mẫu dựng căn phòng: đồ đạc một bên, người đứng ở khoảng trống bên kia.
          Dải 0,46–0,98 để trống hẳn cho chủ thể.

          Đây là ràng buộc mà mọi nơi chốn phải theo, không riêng văn phòng: cảnh là SÂN
          KHẤU, và sân khấu phải có chỗ cho diễn viên đứng. */}
      {[0.06].map((x, i) => (
        <g key={`b${i}`}>
          <rect x={W * x} y={san - H * 0.115} width={W * 0.30} height={H * 0.020} fill={c.gan}
                stroke={_muc(c)} strokeWidth={W * 0.004} />
          <rect x={W * (x + 0.02)} y={san - H * 0.095} width={W * 0.016} height={H * 0.095}
                fill={c.giua} />
          <rect x={W * (x + 0.26)} y={san - H * 0.095} width={W * 0.016} height={H * 0.095}
                fill={c.giua} />
          <rect x={W * (x + 0.09)} y={san - H * (0.20 + r[i] * 0.02)} width={W * 0.13}
                height={H * 0.085} rx={W * 0.006} fill={c.nhan}
                stroke={_muc(c)} strokeWidth={W * 0.004} />
          <Bong x={W * (x + 0.15)} y={san} r={W * 0.16} />
        </g>
      ))}
    </g>
  ),

  /* TRỜI — sao, vành hành tinh, đường cong mặt đất. HOW BIG · SPEED OF · SMALLEST */
  troi: ({ W, H, san, c, hat, r }) => (
    <g>
      {Array.from({ length: 26 }, (_, i) => {
        const q = _rang(hat + i * 7, 2);
        /* Sao KHÔNG viền: nét mực dày bằng cả ngôi sao thì nó thành một chấm đen. Cùng luật
           với `Bong` — vật thì có nét, hiệu ứng thì không. */
        return (<circle key={i} cx={W * q[0]} cy={H * 0.04 + q[1] * (san - H * 0.16)}
                        r={W * (0.0035 + q[1] * 0.004)} fill={c.troiD} stroke="none"
                        opacity={0.35 + q[0] * 0.5} />);
      })}
      <circle cx={W * (0.24 + r[0] * 0.5)} cy={H * 0.15} r={W * 0.10} fill={c.giua} />
      <circle cx={W * (0.24 + r[0] * 0.5) - W * 0.03} cy={H * 0.13} r={W * 0.075}
              fill={c.xa} opacity={0.55} />
      <path d={`M ${-W * 0.2} ${san + H * 0.16} Q ${W * 0.5} ${san - H * 0.10} ${W * 1.2} ${san + H * 0.16} Z`}
            fill={c.gan} />
    </g>
  ),
};

export const TEN_NOI_VE = Object.keys(NOI_VE);

/** Độ sáng 0–255 của dải đáy một cảnh vẽ code — để `PhuDe` chọn mực như nó vẫn làm với ảnh.
 *  Tính từ CHÍNH bảng màu sẽ được vẽ, không tính lại bằng công thức thứ hai: hai chỗ tính
 *  cùng một thứ là hai chỗ để lệch nhau, và lệch kiểu ấy không báo lỗi (§15.3). */
export const sangDayCanh = (noi: string, nen: string, mau: string, mauPhu = ""): number => {
  const sac = SAC_NOI[noi];
  let h = _bang(nen, mau, mauPhu, 0).sanDay;
  if (sac) h = _sacHoa(h, sac[0], sac[1], 0.20);
  if (DAY_TOI[noi]) h = _pha(h, DAY_TOI[noi]);
  const m = /^#([0-9a-f]{6})$/i.exec(h);
  if (!m) return -1;
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(m[1].slice(i, i + 2), 16));
  return Math.round(0.299 * r + 0.587 * g + 0.114 * b);
};

/* ══════════════════════════════════════════════════════════════════════════════════════ */
export const CanhVe: React.FC<{
  W: number; H: number; noi: string; nen: string; mau: string; mauPhu?: string;
  hat?: number; p?: number; am?: number; hatSan?: number;
}> = ({ W, H, noi, nen, mau, mauPhu = "", hat = 0, p = 0, am = 0, hatSan }) => {
  /* ── HAI HẠT, HAI VIỆC  (4/9/2026) ─────────────────────────────────────────────────────
     `hat` ở đây làm HAI việc cùng lúc: sinh đường bao lởm chởm của cảnh (phải đổi theo TỪNG
     nhịp, nếu không thì ba cảnh `duong` trong một tập ra đúng một con đường) và đặt ĐƯỜNG
     CHÂN TRỜI (phải giống mọi lớp khác của tập, nếu không thì nhịp vẽ code có một mặt sàn
     còn nhịp đồ hoạ có mặt sàn khác).

     Hai ràng buộc ngược nhau, và bản trước chỉ mã hoá được một: `KichGiaiThich` truyền
     `canh_hat` (hạt RIÊNG của nhịp) nên chân trời đổi theo. Đo trên 18 tập đã dựng:
     **13/17 nhịp vẽ code có sàn lệch khỏi phần còn lại của tập**. Chính điều kiện số 1 ở
     đầu tệp này (*"cùng ĐƯỜNG CHÂN TRỜI"*) bị phá bởi bản vá cho điều kiện đa dạng.

     Đúng họ lỗi §6 — một biến chịu hai ràng buộc mà công thức chỉ mã hoá một. Tách ra:
     `hat` lo hình dáng, `hatSan` lo mặt sàn. */
  const san = chanTroi(H, hatSan ?? hat);
  const sac = SAC_NOI[noi];
  const c0 = _bang(nen, mau, mauPhu, am);
  // 0,72 cho các dải cảnh: đủ để cát ra cát và băng ra băng. `sanDay` chỉ 0,20 — đó là dải
  // phụ đề, và mọi phép đổi màu ở đó phải nhường cho ràng buộc tương phản 4,5:1.
  const c: Bang = sac
    ? (Object.fromEntries(Object.entries(c0).map(
        /* Vật liệu (`gan` · `vat2-4` · `nhan`) chỉ nhận 0,28 ánh sáng của nơi chốn, không
           0,72: ở 0,72 thì sa mạc nhuộm cái tủ thành cát và cả khung lại về đơn sắc — đúng
           chỗ bảng `VAT_LIEU` vừa đi ra. Ánh sáng của nơi chốn phải CHẠM vào đồ vật, không
           được THAY màu của chúng. */
        ([k, v]) => [k, _sacHoa(v as string, sac[0], sac[1],
                                k === "sanDay" ? 0.20
                                : /^(gan|vat[234]|nhan)$/.test(k) ? 0.28 : 0.72)])) as Bang)
    : c0;
  if (DAY_TOI[noi]) { c.sanDay = _pha(c.sanDay, DAY_TOI[noi]); c.sanD = _pha(c.sanD, DAY_TOI[noi] * 0.5); }
  const trong = TRONG_NHA.has(noi);
  const r = _rang(hat + 101, 8);
  const ve = NOI_VE[noi] || NOI_VE.dong;
  const k = Math.abs(hat) % 6;
  const xS = W * (k === 2 ? 0.24 : k === 5 ? 0.78 : 0.50);   // cùng quy tắc nguồn sáng với NenPhong
  const id = `cv${Math.abs(hat) % 9973}`;

  return (
    <AbsoluteFill>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute" }}>
        <defs>
          <linearGradient id={`${id}t`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={c.troi} />
            <stop offset="100%" stopColor={c.troiD} />
          </linearGradient>
          {/* Sàn sẫm dần: ba chặng, chặng cuối chỉ ở 18% đáy — cùng cách `NenPhong` đạt
              4,5:1 cho chữ trắng mà không tối cả căn cảnh (§ràng buộc 4). */}
          <linearGradient id={`${id}s`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={c.san} />
            <stop offset="55%" stopColor={c.sanD} />
            <stop offset="100%" stopColor={c.sanDay} />
          </linearGradient>
          <radialGradient id={`${id}q`} cx={xS / W} cy={(san - H * 0.22) / H} r="0.62">
            <stop offset="0%" stopColor="#FFFFFF" stopOpacity={0.16} />
            <stop offset="100%" stopColor="#FFFFFF" stopOpacity={0} />
          </radialGradient>
        </defs>

        {/* Nơi TRONG NHÀ không có bầu trời. Bản đầu vẽ dải chuyển sáng-tối cho mọi nơi, nên
            vì kèo mái của kho và rèm của văn phòng treo lơ lửng giữa một khoảng trời —
            §12.5 lần nữa: một luật đúng ở ngoài trời, sai ở trong nhà.
            Tường: phẳng, hơi sẫm ở SÁT TRẦN (bóng đọng ở góc trên là thứ mắt đọc ra "có
            trần"), cộng một đường chỉ trần mảnh. */}
        {trong ? (
          <>
            <rect x={0} y={0} width={W} height={san} fill={c.troiD} />
            <rect x={0} y={0} width={W} height={H * 0.10} fill={c.xa} opacity={0.34} />
            <rect x={0} y={H * 0.10} width={W} height={H * 0.006} fill={c.xa} opacity={0.5} />
          </>
        ) : (
          <rect x={0} y={0} width={W} height={san} fill={`url(#${id}t)`} />
        )}
        <rect x={0} y={san} width={W} height={H - san} fill={`url(#${id}s)`} />
        {/* Nhích rất nhẹ theo tiến độ nhịp: cảnh đứng chết thì đọc ra ảnh tĩnh dán vào phim. */}
        {/* ── NÉT MỰC PHỦ CẢ CẢNH, KẾ THỪA CHỨ KHÔNG VẼ TAY TỪNG HÌNH  (4/9/2026) ────────
            Anh chọn giữ xen kẽ ảnh AI với cảnh vẽ code, và kéo lớp code lại gần chất tranh.
            Soi hai lớp cạnh nhau thì thứ tách chúng ra KHÔNG phải màu — mà là **nét**:

                ảnh AI      : mọi vật có viền mực đen dày, nhân vật cũng vậy
                cảnh code   : gần như không hình nào có viền, chỉ là mảng màu phẳng

            Nên nhân vật (có viền) đứng trong một thế giới không viền — hai chất liệu, và
            người xem đọc ra "dán vào" trong nửa giây (§12.10: lệch phong cách là đòn bẩy
            lớn nhất, và chỉnh màu không cứu được nó).

            SVG kế thừa `stroke`/`stroke-width` xuống con, nên đặt MỘT lần ở nhóm cha thì
            mọi hình chỉ-có-`fill` tự có viền — không phải sửa tay hàng chục hình trong mười
            nơi chốn, và nơi chốn thêm sau này cũng tự có nét. Hình nào cần khác thì tự khai
            `stroke` của nó và nó thắng (mấy hình đã khai sẵn giữ nguyên).

            `vectorEffect="non-scaling-stroke"` KHÔNG dùng ở đây: khung dựng đúng cỡ thật nên
            nét đã đúng tỉ lệ, còn thuộc tính ấy sẽ làm nét dày như nhau ở mọi cỡ hình. */}
        {/* ── NÉT TỰ VẼ RA  (5/9/2026) ─────────────────────────────────────────────
            Xem `TuVe.tsx` cho cơ chế và vì sao không cần đo chiều dài đường.

            `p` là tiến độ của cả nhịp (0 -> 1). Nét phải vẽ xong SỚM hơn nhiều, nếu không
            thì người xem đọc chữ phụ đề xong mà hình vẫn đang mọc — chữ và hình phải nói
            cùng một câu tại cùng một lúc. Chia cho 0,42 nghĩa là nét xong ở 42% nhịp, tức
            khoảng 0,45 giây với nhịp trung vị 2,3 giây: đủ để mắt bắt được động tác vẽ, và
            80% nhịp còn lại là một khung TĨNH hoàn chỉnh — xem chú thích `MOC_MAU`. */}
        <g transform={`translate(0 ${-p * H * 0.008})`}
           stroke={_muc(c)} strokeWidth={W * 0.005} strokeLinejoin="round" strokeLinecap="round">
          <TuVe p={p / 0.20}>
            {ve({ W, H, san, c, hat, r })}
          </TuVe>
        </g>
        <rect x={0} y={0} width={W} height={H} fill={`url(#${id}q)`} />
      </svg>
    </AbsoluteFill>
  );
};
